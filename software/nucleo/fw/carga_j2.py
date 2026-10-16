#!/usr/bin/env python3
"""Corre `carga_j2` en la placa y saca la fila de `carga_j2.csv`, ya calculada.

    python carga_j2.py            # compila, corre las pasadas y muestra la fila
    python carga_j2.py --hub      # lo mismo con el nucleo a 800 MHz (feature reloj-hub)
    python carga_j2.py --ranuras 3   # con tres ranuras girando (2 o 3; pines en j2_banco)
    python carga_j2.py --isr      # el transporte por ISR de j2_isr, la cota sin ejecutor
    python carga_j2.py --anota    # ademas la anade a carga_j2.csv
    python carga_j2.py --autotest # el parseo y la cuenta, sin placa

**La cifra que se compara con el limite firmado (D5.1, 16-10) es el J2 entero**
-- ISR del SPI, DMA, reloj de embassy y despacho del ejecutor --, no solo el
manejador del ejecutor. Sale del medidor del hilo: lo que no es CPU libre para el
hilo, durante un ciclo. `ejecutor` y los tramos son el desglose, no el total.

    ciclos_por_giro = (1000 - hilo_libre_permil) / 1000 * ciclo_us * f_cpu / 1e6 / ranuras

`ciclo_us` es el ciclo de una ranura, en el que cada una da un giro: el J2 gasta lo
que el hilo no usa, repartido entre los giros de todas.

`--anota` se niega si el firmware sale `-sucio` (una fila con la revision de un
commit que no es el codigo que corrio no se puede repetir) y se niega con las
pasadas `-sin-mpu`, que son de exploracion: la D-cache sin la region MPU de los
buferes del DMA incumple R-MJ7 y esa fila no sirve para la puerta. Tampoco anota
las de `--isr`: es una cota de coste, no el transporte del instrumento.

La cuenta usa el reloj que **pidio** la configuracion (`f_cpu`); se niega si el
que **midio** el firmware (`f_cpu_medido`) se aparta mas de un 2 %: seria la
cuenta de un reloj que no es el que corre.
"""
from __future__ import annotations

import datetime
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, "carga_j2.csv")
PLACA = "NUCLEO-N657X0-Q"
# Debe coincidir con `recuperacion_j2_budget.py`, que lo deriva del reparto firmado;
# aqui solo se usa para decir cuantas veces lo pasa, no para decidir nada.
LIMITE_INFORMATIVO = 2500

CABECERA = re.compile(
    r"carga_j2: firmware (\S+), f_cpu (\d+) Hz(?:, f_cpu_medido (\d+) Hz)?"
    r"(?:.*?transporte (\w+))?")
TOLERANCIA_RELOJ = 0.02
# `ranuras` y `periodo_us` no estan en las lineas anteriores al 17-10: una ranura a 125 us.
PASADA = re.compile(
    r"carga_j2,cache=(?P<cache>[\w+-]+),(?:ranuras=(?P<ranuras>\d+),periodo_us=(?P<periodo>\d+),)?"
    r"ciclo_us=(?P<ciclo>\d+),giros_en_5s=(?P<giros>\d+),hilo_libre_permil=(?P<libre>\d+),"
    r"atrasos=(?P<atrasos>\d+),plazos_vencidos=(?P<plazos>\d+)")
TRAMOS = re.compile(
    r"carga_j2,cache=([\w+-]+),previo=(\d+),armado=(\d+),espera=(\d+),cierre=(\d+),"
    r"posterior=(\d+),isr_spi=(\d+),ejecutor=(\d+)")


def ciclos_del_j2(libre_permil: int, ciclo_us: int, f_cpu_hz: int, ranuras: int = 1) -> int:
    """La CPU que gasta el J2 en un giro: la parte del ciclo que no es libre,
    repartida entre los giros que caben en el (uno por ranura)."""
    return round((1000 - libre_permil) * ciclo_us * f_cpu_hz / 1e9 / ranuras)


def parsea(texto: str) -> dict:
    """Del texto crudo de `probe-rs run`: el firmware, el reloj y las pasadas."""
    cab = CABECERA.search(texto)
    if not cab:
        raise SystemExit("no hay linea `carga_j2: firmware ...`: la placa no corrio el binario")
    firmware, f_cpu = cab.group(1), int(cab.group(2))
    medido = int(cab.group(3)) if cab.group(3) else 0
    if medido and abs(medido - f_cpu) > TOLERANCIA_RELOJ * f_cpu:
        raise SystemExit(f"el reloj pedido es {f_cpu} Hz y el medido {medido} Hz: "
                         "la cuenta de ciclos saldria con un reloj que no corre")
    pasadas = {}
    for m in PASADA.finditer(texto):
        pasadas[m.group("cache")] = {
            "ranuras": int(m.group("ranuras") or 1), "periodo": int(m.group("periodo") or 125),
            "ciclo_us": int(m.group("ciclo")), "giros": int(m.group("giros")),
            "libre": int(m.group("libre")), "atrasos": int(m.group("atrasos")),
            "plazos": int(m.group("plazos"))}
    for m in TRAMOS.finditer(texto):
        t = dict(zip(("previo", "armado", "espera", "cierre", "posterior", "isr_spi", "ejecutor"),
                     map(int, m.groups()[1:])))
        if m.group(1) in pasadas:
            pasadas[m.group(1)].update(t)
    if not pasadas:
        raise SystemExit("no hay ninguna linea `carga_j2,cache=...`: el binario no llego a medir")
    for cache, p in pasadas.items():
        if p["plazos"]:
            raise SystemExit(f"cache={cache}: {p['plazos']} plazos vencidos; la medida no vale")
        p["ciclos_por_giro"] = ciclos_del_j2(p["libre"], p["ciclo_us"], f_cpu, p["ranuras"])
    return {"firmware": firmware, "f_cpu": f_cpu, "medido": medido,
            "transporte": cab.group(4) or "ejecutor", "pasadas": pasadas}


def filas(medida: dict, fecha: str) -> list[str]:
    return [f"{fecha},{medida['firmware']},{PLACA},{medida['f_cpu']},{cache},"
            f"{p['ciclos_por_giro']},{p['libre']},{p['ranuras']},{p['periodo']}"
            for cache, p in medida["pasadas"].items()]


def muestra(medida: dict) -> None:
    print(f"\nfirmware {medida['firmware']}, {medida['f_cpu']/1e6:.0f} MHz "
          f"(medido {medida['medido']/1e6:.1f} MHz), transporte {medida['transporte']}\n")
    print(f"  {'cache':8} {'ranuras':>7} {'ciclo_us':>8} {'libre':>7} {'J2 ciclos/giro':>15} "
          f"{'x limite':>9}   desglose del ejecutor")
    for cache, p in medida["pasadas"].items():
        desglose = ""
        if "ejecutor" in p:
            tarea = p["previo"] + p["armado"] + p["cierre"] + p["posterior"]
            desglose = (f"ejecutor {p['ejecutor']} = tarea {tarea} "
                        f"(previo {p['previo']}, armado {p['armado']}, cierre {p['cierre']}, "
                        f"posterior {p['posterior']}) + resto {p['ejecutor'] - tarea}; "
                        f"isr_spi {p['isr_spi']}")
        print(f"  {cache:8} {p['ranuras']:7d} {p['ciclo_us']:8d} {p['libre']:7d} {p['ciclos_por_giro']:15,d} "
              f"{p['ciclos_por_giro'] / LIMITE_INFORMATIVO:8.1f}x   {desglose}")


def anota(lineas: list[str], firmware: str, transporte: str = "ejecutor") -> None:
    if transporte != "ejecutor":
        raise SystemExit(f"transporte `{transporte}`: es una cota de coste y no se anota")
    if "sucio" in firmware or firmware == "sin-git":
        raise SystemExit(f"firmware `{firmware}`: commitea antes de anotar la fila")
    if any("sin-mpu" in ln for ln in lineas):
        raise SystemExit("hay una pasada `-sin-mpu`: es de exploracion y no se anota")
    with open(CSV, "a", encoding="utf-8", newline="") as f:
        for ln in lineas:
            f.write(ln + "\n")
    print(f"\nanotadas {len(lineas)} filas en {os.path.basename(CSV)}")


def autotest() -> None:
    """La medida del 2026-10-16 (b9f6d7d, 64 MHz) como texto de probe-rs."""
    crudo = (
        "[INFO ] carga_j2: firmware b9f6d7d, f_cpu 64000000 Hz, periodo 125 us, base 1 vueltas/s (x)\n"
        "[INFO ] carga_j2,cache=no,ciclo_us=420,giros_en_5s=11904,hilo_libre_permil=198,atrasos=11904,plazos_vencidos=0 (x)\n"
        "[INFO ] carga_j2,cache=no,previo=2424,armado=3020,espera=7879,cierre=1130,posterior=1564,isr_spi=505,ejecutor=18738 (x)\n"
        "[INFO ] carga_j2,cache=icache,ciclo_us=343,giros_en_5s=14577,hilo_libre_permil=328,atrasos=14577,plazos_vencidos=0 (x)\n"
        "[INFO ] carga_j2,cache=icache,previo=866,armado=2457,espera=6770,cierre=775,posterior=1167,isr_spi=428,ejecutor=13366 (x)\n"
    )
    m = parsea(crudo)
    assert m["firmware"] == "b9f6d7d" and m["f_cpu"] == 64_000_000
    # El total es mayor que el ejecutor: lleva la ISR del SPI, el DMA y el reloj.
    assert m["pasadas"]["no"]["ciclos_por_giro"] == 21558, m["pasadas"]["no"]
    assert m["pasadas"]["icache"]["ciclos_por_giro"] == 14752, m["pasadas"]["icache"]
    assert m["pasadas"]["no"]["ciclos_por_giro"] > m["pasadas"]["no"]["ejecutor"]
    assert filas(m, "2026-10-16")[0] == "2026-10-16,b9f6d7d,NUCLEO-N657X0-Q,64000000,no,21558,198,1,125"
    # Tres ranuras: el ciclo es de una ranura y el coste se reparte entre los tres giros.
    tres = (
        "[INFO ] carga_j2: firmware abc1234, f_cpu 64000000 Hz, f_cpu_medido 64000000 Hz, periodo 2000 us (x)\n"
        "[INFO ] carga_j2,cache=no,ranuras=3,periodo_us=2000,ciclo_us=2000,giros_en_5s=7500,hilo_libre_permil=400,atrasos=0,plazos_vencidos=0 (x)\n"
    )
    p3 = parsea(tres)["pasadas"]["no"]
    assert p3["ranuras"] == 3 and p3["periodo"] == 2000
    assert p3["ciclos_por_giro"] == round(600 * 2000 * 64e6 / 1e9 / 3) == 25600, p3
    # Un plazo vencido invalida la pasada, y un firmware sucio no se anota.
    for malo in (crudo.replace("plazos_vencidos=0", "plazos_vencidos=3", 1), "nada"):
        try:
            parsea(malo)
        except SystemExit:
            pass
        else:
            raise AssertionError("tenia que negarse")
    try:
        anota(["x"], "b9f6d7d-sucio")
    except SystemExit:
        pass
    else:
        raise AssertionError("anoto un firmware sucio")
    # El reloj de diseno: la cabecera trae el medido y las pasadas el D-cache sin MPU.
    hub = (
        "carga_j2: firmware abc1234, f_cpu 800000000 Hz, f_cpu_medido 799800000 Hz, periodo 125 us (x)\n"
        "carga_j2,cache=icache+dcache-sin-mpu,ciclo_us=200,giros_en_5s=25000,hilo_libre_permil=500,atrasos=0,plazos_vencidos=0 (x)\n"
    )
    mh = parsea(hub)
    p = mh["pasadas"]["icache+dcache-sin-mpu"]
    assert p["ciclos_por_giro"] == round(500 * 200 * 800_000_000 / 1e9) == 80000, p
    try:
        anota(filas(mh, "2026-10-17"), mh["firmware"])
    except SystemExit:
        pass
    else:
        raise AssertionError("anoto una pasada sin MPU")
    isr = parsea(hub.replace("periodo 125 us (x)", "periodo 125 us, base 1 vueltas/s, transporte isr (x)"))
    assert isr["transporte"] == "isr" and mh["transporte"] == "ejecutor"
    try:
        anota(["x"], "abc1234", "isr")
    except SystemExit:
        pass
    else:
        raise AssertionError("anoto una cota")
    try:
        parsea(hub.replace("f_cpu_medido 799800000", "f_cpu_medido 640000000"))
    except SystemExit:
        pass
    else:
        raise AssertionError("acepto un reloj medido que no es el pedido")
    print("autotest ok")


def main() -> None:
    if "--autotest" in sys.argv:
        return autotest()
    features = ["perfil"] + (["reloj-hub"] if "--hub" in sys.argv else [])
    if "--isr" in sys.argv:
        features.append("transporte-isr")
    if "--ranuras" in sys.argv:
        n = sys.argv[sys.argv.index("--ranuras") + 1]
        if n not in ("2", "3"):
            raise SystemExit("--ranuras admite 2 o 3 (la 1 es la de siempre)")
        features.append(f"ranuras-{n}")
    run = subprocess.run(
        ["cargo", "run", "--release", "--features", ",".join(features), "--bin", "carga_j2"],
        cwd=AQUI, capture_output=True, text=True, timeout=600)
    medida = parsea(run.stdout + run.stderr)
    muestra(medida)
    lineas = filas(medida, datetime.date.today().isoformat())
    print("\nfilas de carga_j2.csv:\n  " + "\n  ".join(lineas))
    if "--anota" in sys.argv:
        anota(lineas, medida["firmware"], medida["transporte"])


if __name__ == "__main__":
    main()
