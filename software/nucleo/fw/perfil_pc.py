#!/usr/bin/env python3
"""Donde se va la CPU de un giro del J2: lee el histograma del muestreo y lo
cruza con los simbolos del ELF.

    cargo build --release --features muestreo --bin perfil_pc
    python perfil_pc.py target/thumbv8m.main-none-eabihf/release/perfil_pc

Lanza el binario con `probe-rs run` (termina solo en un `bkpt`), toma de su linea
`perfil_pc:` donde esta el histograma, lo lee de la RAM con `probe-rs read` y
lo mapea a funciones con `rust-nm`. Hace falta la placa libre: no puede haber
otro `probe-rs` agarrando la sonda.

    --autotest ELF   comprueba el mapeo contra los simbolos reales de ese ELF,
                     sin placa.

El perfilador esta en `src/muestreo.rs`. Da **como se reparten** los ciclos, no
cuantos son: perturba (~5 % de la CPU) y los ciclos por giro salen de `carga_j2`.
Lo que imprime como ciclos por giro es el reparto aplicado al ciclo total
(`f_cpu x segundos / giros`), con la CPU ociosa del hilo incluida.
"""
from __future__ import annotations

import bisect
import re
import subprocess
import sys

CHIP = "STM32N657"
# Los simbolos que son la CPU ociosa o el medidor del hilo: lo que NO es J2.
HILO = re.compile(r"Executor::run|vueltas_del_hilo|yield_now|embassy_main")


def simbolos(elf: str) -> tuple[list[int], list[tuple[int, int, str]]]:
    """(direcciones, [(direccion, tamano, nombre)]) ordenados, de `rust-nm`."""
    out = subprocess.run(["rust-nm", "-C", "-S", "-n", elf],
                         capture_output=True, text=True, check=True).stdout
    sims = []
    for linea in out.splitlines():
        m = re.match(r"^([0-9a-f]{8}) ([0-9a-f]{8}) [Tt] (.+)$", linea)
        if not m:
            continue
        nombre = re.sub(r"::h[0-9a-f]{16}$", "", m.group(3))
        sims.append((int(m.group(1), 16), int(m.group(2), 16), nombre))
    sims.sort()
    return [s[0] for s in sims], sims


def busca(pc: int, dirs: list[int], sims: list[tuple[int, int, str]]) -> str:
    i = bisect.bisect_right(dirs, pc) - 1
    if i >= 0:
        d, t, nombre = sims[i]
        if d <= pc < d + max(t, 1):
            return nombre
    return "?"


def reparte(hist: list[int], base: int, cubo: int, dirs, sims) -> dict[str, int]:
    """Muestras por simbolo."""
    por = {}
    for i, n in enumerate(hist):
        if n:
            nombre = busca(base + i * cubo, dirs, sims)
            por[nombre] = por.get(nombre, 0) + n
    return por


def histograma_de(texto: str, cubos: int) -> list[int]:
    """Los cubos de 16 bits de la salida de `probe-rs read b32`: filas `dir: w w w`,
    con la palabra baja primero (el formato de las lecturas de la placa)."""
    palabras = []
    for linea in texto.splitlines():
        if ":" in linea:
            palabras += [int(t, 16) for t in re.findall(r"\b[0-9a-f]{8}\b", linea.split(":", 1)[1])]
    if len(palabras) != cubos // 2:
        raise SystemExit(f"se esperaban {cubos // 2} palabras y probe-rs devolvio {len(palabras)}: "
                         "el formato de `probe-rs read b32` no es el que este guion parsea")
    hist = []
    for w in palabras:
        hist += [w & 0xFFFF, w >> 16]
    return hist


def lee_histograma(direccion: int, cubos: int) -> list[int]:
    out = subprocess.run(
        ["probe-rs", "read", "--chip", CHIP, "b32", hex(direccion), str(cubos // 2)],
        capture_output=True, text=True, check=True).stdout
    return histograma_de(out, cubos)


def campo(linea: str, clave: str) -> int:
    m = re.search(rf"\b{clave} (0x[0-9a-f]+|\d+)", linea)
    if not m:
        raise SystemExit(f"la linea de `perfil_pc:` no trae `{clave}`: {linea}")
    return int(m.group(1), 0)


def imprime(por: dict[str, int], giros: int, f_cpu: int, segundos: int, limite: int = 30) -> None:
    total = sum(por.values())
    ciclo = f_cpu * segundos / max(giros, 1)
    hilo = sum(n for k, n in por.items() if HILO.search(k))
    print(f"\n{total} muestras, {giros} giros en {segundos} s, "
          f"{ciclo:,.0f} ciclos de reloj por giro (con la CPU ociosa incluida)\n")
    print(f"  {'muestras':>9} {'%':>6} {'ciclos/giro':>11}  funcion")
    for nombre, n in sorted(por.items(), key=lambda kv: -kv[1])[:limite]:
        print(f"  {n:9d} {100*n/total:6.1f} {ciclo*n/total:11,.0f}  {nombre}")
    print(f"\n  hilo (CPU ociosa y medidor):   {100*hilo/total:5.1f} %  {ciclo*hilo/total:8,.0f} ciclos/giro")
    print(f"  J2 y sistema (todo lo demas):  {100*(total-hilo)/total:5.1f} %  "
          f"{ciclo*(total-hilo)/total:8,.0f} ciclos/giro")


def autotest(elf: str) -> None:
    """El mapeo contra los simbolos reales: sin placa."""
    dirs, sims = simbolos(elf)
    assert len(sims) > 100, f"solo {len(sims)} simbolos: rust-nm no devolvio lo esperado"
    # Una direccion dentro de cada uno de tres simbolos conocidos cae en ellos.
    for parte in ("muestreo::muestrear", "gpdma::on_irq", "Executor::run"):
        elegido = next((s for s in sims if parte in s[2] and s[1] >= 4), None)
        assert elegido, f"no hay simbolo con {parte!r}"
        d, t, nombre = elegido
        assert busca(d, dirs, sims) == nombre
        assert busca(d + t - 1, dirs, sims) == nombre, "el ultimo byte tiene que ser suyo"
    # Fuera de todo simbolo: `?`, no el vecino.
    assert busca(sims[0][0] - 1, dirs, sims) == "?"
    # Un histograma sintetico: 100 muestras en `muestrear`, 50 en un hueco.
    d, t, nombre = next(s for s in sims if "muestreo::muestrear" in s[2])
    base = 0x341A0000
    hist = [0] * 16384
    hist[(d - base) // 2] = 100
    hist[(sims[-1][0] + sims[-1][1] + 64 - base) // 2] = 50
    por = reparte(hist, base, 2, dirs, sims)
    assert por == {nombre: 100, "?": 50}, por
    # El formato de `probe-rs read b32`: dos palabras por fila, la baja primero.
    fila = "341a0000: 00010002 00000003\n341a0008: ffff0000 00000000\n"
    assert histograma_de(fila, 8) == [2, 1, 3, 0, 0, 0xFFFF, 0, 0]
    print("autotest ok:", len(sims), "simbolos")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--autotest":
        return autotest(sys.argv[2])
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    elf = sys.argv[1]
    run = subprocess.run(["probe-rs", "run", "--chip", CHIP, elf],
                         capture_output=True, text=True, timeout=180)
    linea = next((ln for ln in run.stdout.splitlines() if "perfil_pc: firmware" in ln), None)
    if linea is None:
        raise SystemExit("el binario no imprimio su linea `perfil_pc:`. Salida:\n"
                         + run.stdout[-1500:] + run.stderr[-800:])
    print(linea.strip())
    base, cubo, cubos = campo(linea, "base"), campo(linea, "cubo"), campo(linea, "cubos")
    hist = lee_histograma(campo(linea, "histograma"), cubos)
    dirs, sims = simbolos(elf)
    por = reparte(hist, base, cubo, dirs, sims)
    imprime(por, campo(linea, "giros"), campo(linea, "f_cpu"), campo(linea, "segundos"))
    print(f"\n  muestras fuera del codigo: {campo(linea, 'fuera')}, "
          f"hilo libre medido por carga: {campo(linea, 'hilo_libre_permil')/10:.1f} %")


if __name__ == "__main__":
    main()
