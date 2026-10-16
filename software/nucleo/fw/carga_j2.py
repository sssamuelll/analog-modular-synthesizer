#!/usr/bin/env python3
"""Corre `carga_j2` en la placa y saca la fila de `carga_j2.csv`, ya calculada.

    python carga_j2.py            # compila, corre las pasadas y muestra la fila
    python carga_j2.py --hub      # lo mismo con el nucleo a 800 MHz (feature reloj-hub)
    python carga_j2.py --anota    # ademas la anade a carga_j2.csv
    python carga_j2.py --autotest # el parseo y la cuenta, sin placa

**La cifra que se compara con el limite firmado (D5.1, 16-10) es el J2 entero**
-- ISR del SPI, DMA, reloj de embassy y despacho del ejecutor --, no solo el
manejador del ejecutor. Sale del medidor del hilo: lo que no es CPU libre para el
hilo, durante un ciclo. `ejecutor` y los tramos son el desglose, no el total.

    ciclos_por_giro = (1000 - hilo_libre_permil) / 1000 * ciclo_us * f_cpu / 1e6

`--anota` se niega si el firmware sale `-sucio` (una fila con la revision de un
commit que no es el codigo que corrio no se puede repetir) y se niega con las
pasadas `-sin-mpu`, que son de exploracion: la D-cache sin la region MPU de los
buferes del DMA incumple R-MJ7 y esa fila no sirve para la puerta.

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

CABECERA = re.compile(r"carga_j2: firmware (\S+), f_cpu (\d+) Hz(?:, f_cpu_medido (\d+) Hz)?")
TOLERANCIA_RELOJ = 0.02
PASADA = re.compile(
    r"carga_j2,cache=([\w+-]+),ciclo_us=(\d+),giros_en_5s=(\d+),hilo_libre_permil=(\d+),"
    r"atrasos=(\d+),plazos_vencidos=(\d+)")
TRAMOS = re.compile(
    r"carga_j2,cache=([\w+-]+),previo=(\d+),armado=(\d+),espera=(\d+),cierre=(\d+),"
    r"posterior=(\d+),isr_spi=(\d+),ejecutor=(\d+)")


def ciclos_del_j2(libre_permil: int, ciclo_us: int, f_cpu_hz: int) -> int:
    """La CPU que gasta el J2 en un giro: la parte del ciclo que no es libre."""
    return round((1000 - libre_permil) * ciclo_us * f_cpu_hz / 1e9)


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
        cache, ciclo_us, giros, libre, atrasos, plazos = m.group(1), *map(int, m.groups()[1:])
        pasadas[cache] = {"ciclo_us": ciclo_us, "giros": giros, "libre": libre,
                          "atrasos": atrasos, "plazos": plazos}
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
        p["ciclos_por_giro"] = ciclos_del_j2(p["libre"], p["ciclo_us"], f_cpu)
    return {"firmware": firmware, "f_cpu": f_cpu, "medido": medido, "pasadas": pasadas}


def filas(medida: dict, fecha: str) -> list[str]:
    return [f"{fecha},{medida['firmware']},{PLACA},{medida['f_cpu']},{cache},"
            f"{p['ciclos_por_giro']},{p['libre']}"
            for cache, p in medida["pasadas"].items()]


def muestra(medida: dict) -> None:
    print(f"\nfirmware {medida['firmware']}, {medida['f_cpu']/1e6:.0f} MHz "
          f"(medido {medida['medido']/1e6:.1f} MHz)\n")
    print(f"  {'cache':8} {'ciclo_us':>8} {'libre':>7} {'J2 ciclos/giro':>15} "
          f"{'x limite':>9}   desglose del ejecutor")
    for cache, p in medida["pasadas"].items():
        desglose = ""
        if "ejecutor" in p:
            tarea = p["previo"] + p["armado"] + p["cierre"] + p["posterior"]
            desglose = (f"ejecutor {p['ejecutor']} = tarea {tarea} "
                        f"(previo {p['previo']}, armado {p['armado']}, cierre {p['cierre']}, "
                        f"posterior {p['posterior']}) + resto {p['ejecutor'] - tarea}; "
                        f"isr_spi {p['isr_spi']}")
        print(f"  {cache:8} {p['ciclo_us']:8d} {p['libre']:7d} {p['ciclos_por_giro']:15,d} "
              f"{p['ciclos_por_giro'] / LIMITE_INFORMATIVO:8.1f}x   {desglose}")


def anota(lineas: list[str], firmware: str) -> None:
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
    assert filas(m, "2026-10-16")[0] == "2026-10-16,b9f6d7d,NUCLEO-N657X0-Q,64000000,no,21558,198"
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
    features = "perfil,reloj-hub" if "--hub" in sys.argv else "perfil"
    run = subprocess.run(
        ["cargo", "run", "--release", "--features", features, "--bin", "carga_j2"],
        cwd=AQUI, capture_output=True, text=True, timeout=600)
    medida = parsea(run.stdout + run.stderr)
    muestra(medida)
    lineas = filas(medida, datetime.date.today().isoformat())
    print("\nfilas de carga_j2.csv:\n  " + "\n  ".join(lineas))
    if "--anota" in sys.argv:
        anota(lineas, medida["firmware"])


if __name__ == "__main__":
    main()
