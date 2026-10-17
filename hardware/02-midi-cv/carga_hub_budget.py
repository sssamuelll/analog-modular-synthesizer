#!/usr/bin/env python3
"""El censo de CPU del hub: una fila por quien le pide ciclos, y de donde sale cada cifra.

    python carga_hub_budget.py

Nace del acta del 2026-10-17 del J2 (ficha 2): el 15 % del J2 se firmo el 16-10
como la primera fila de un libro que no existia, y desde el acta es PROVISIONAL
hasta que este libro exista. `carga_motor_budget.py` es el libro del motor (la
Voz) y dice que sus filas heredadas no son un censo del hub; esto es el del hub.

QUE ES UNA FILA

  Un consumidor de ciclos del N657 del hub (spec del hub, D1: "interfaz grafica
  y controladores"), con su duenio, su estado y, si lo tiene, su cifra en ciclos
  por segundo de UN nucleo a 800 MHz. Los estados son los del repo:

    MEDIDO     sale de una fila de CSV o de un banco con reloj y cachés del hub
    ESTIMADO   sale de un papel, con su fuente escrita
    HUECO      no hay cifra. NO es cero: una fila sin cifra no suma, y el libro
               no es un censo hasta que ninguna lo sea.

  La lista de filas sale de las secciones 2 a 6 del papel del hub. Un consumidor
  que falte es un HUECO del censo, no una fila de cero.

LA FILA DEL J2

  Lo que cuenta es lo que firmo Samuel el 17-10 (ficha 1): el trabajo propio del
  enlace -- armar y cerrar cada transferencia, el tic o las interrupciones, el
  DMA, el CRC de la subida y los contadores de salud --, y NO componer la
  trama, que es la fila de abajo. Sale de `carga_j2.csv` por el mismo camino que
  la puerta `recuperacion_j2_budget.py`: la mejor fila a 800 MHz con las
  cachés del hub, por 6 ranuras x 8 kHz giros por segundo. Mientras no haya una,
  es HUECO, y las cifras de exploracion de EN-PLACA (sin region MPU) no son filas.

LO QUE ESTE GUION DECIDE Y LO QUE NO

  Decide si lo que ya tiene cifra cabe en un nucleo y si el censo esta completo.
  No decide el reparto: ni cuanto margen se reserva (el acta del 2026-09-09
  pide "suficiente headroom" y no le pone numero) ni si el J2 se queda en el 15 %.
  Sale con 2 (HUECO) mientras alguna fila no tenga cifra, con 1 si lo conocido
  ya pasa del nucleo, con 0 cuando no queda ninguna.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

sys.stdout.reconfigure(errors="replace")

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _AQUI)
import carga_motor_budget as cm  # noqa: E402
import recuperacion_j2_budget as rj  # noqa: E402

MEDIDO, ESTIMADO, HUECO = "MEDIDO", "ESTIMADO", "HUECO"


@dataclass(frozen=True)
class Fila:
    nombre: str
    duenio: str
    estado: str
    ciclos_por_s: float | None
    nota: str = ""


def fraccion(ciclos_por_s: float) -> float:
    """La parte de UN nucleo a F_CPU que son `ciclos_por_s`."""
    return ciclos_por_s / cm.F_CPU


def suma_conocida(filas: list[Fila]) -> float:
    """Ciclos por segundo de las filas que tienen cifra. Un HUECO no suma."""
    return sum(f.ciclos_por_s for f in filas if f.ciclos_por_s is not None)


def veredicto(filas: list[Fila]) -> int:
    """0 completo y cabe, 2 con HUECOS, y falla (AssertionError) si lo conocido pasa del nucleo."""
    conocido = fraccion(suma_conocida(filas))
    assert conocido <= 1.0, (
        f"las filas con cifra ya piden {conocido*100:.0f} % de un nucleo: el hub no cabe")
    return 2 if any(f.estado == HUECO or f.ciclos_por_s is None for f in filas) else 0


def fila_j2() -> Fila:
    """La mejor fila de `carga_j2.csv` a >= F_CPU, por los giros por segundo del lazo."""
    u = rj.del_rust()
    giros_s = u["ranuras_spi"] * rj.tb.F_LAZO_HZ
    a_diseno = [int(f["ciclos_por_giro"]) for f in rj.lee_carga()
                if float(f["f_cpu_hz"]) >= cm.F_CPU]
    if not a_diseno:
        return Fila("J2: el trabajo propio del enlace", "spec del maestro J2 (D5.1)", HUECO, None,
                    "carga_j2.csv no tiene fila a 800 MHz con las caches del hub; "
                    f"limite provisional: {rj.FRACCION_CPU_J2*100:.0f} %")
    mejor = min(a_diseno)
    return Fila("J2: el trabajo propio del enlace", "spec del maestro J2 (D5.1)", MEDIDO,
                mejor * giros_s, f"{mejor} ciclos por giro x {giros_s:.0f} giros/s")


def censo() -> list[Fila]:
    return [
        fila_j2(),
        Fila("J2: componer las tramas", "cabecera J2, planificador (#267)", HUECO, None,
             "la trama sale de notas, CV y pantalla; no cuenta contra el J2 (acta del 17-10)"),
        Fila("Pantalla: LTDC, GPU y la interfaz", "hub 3.1 (D2) y pantalla-motor", HUECO, None,
             "el framebuffer sale de AXISRAM o PSRAM: tambien pesa en el bus"),
        Fila("Mandos alrededor de la pantalla", "hub 3.3", HUECO, None, ""),
        Fila("USB (dispositivo) y MIDI", "fw/src/usb.rs; sin papel de CPU", HUECO, None, ""),
        Fila("Radios: satelites y BLE", "hub 4.2 (D4)", HUECO, None,
             "coprocesador de radio por SPI o UART, con TDMA propio"),
        Fila("Escritor de CV", "#367", HUECO, None, "si comparte el GPDMA1 con el J2, ademas pesa en R-H3"),
        Fila("Descubrimiento I2C", "spec del maestro J2 (D2)", HUECO, None, ""),
        Fila("Supervisor de vitalidad y el IWDG", "#291", HUECO, None, ""),
        Fila("Runtime: embassy-time y el ejecutor de hilo", "fw", HUECO, None, ""),
        Fila("Margen reservado", "acta del 2026-09-09 (hub 0)", HUECO, None,
             "\"suficiente headroom\" sin numero"),
    ]


def _autocomprobacion() -> None:
    """Las dos puertas, contra filas sinteticas: lo que pasa del nucleo falla, y un HUECO no suma."""
    una = Fila("a", "x", MEDIDO, 400e6)
    hueco = Fila("b", "y", HUECO, None)
    assert fraccion(400e6) == 0.5 and suma_conocida([una, hueco]) == 400e6
    assert veredicto([una]) == 0 and veredicto([una, hueco]) == 2
    try:
        veredicto([Fila("a", "x", MEDIDO, 600e6), Fila("b", "y", ESTIMADO, 300e6),
                   Fila("c", "z", ESTIMADO, 200e6)])
    except AssertionError:
        pass
    else:
        raise AssertionError("1,375 nucleos tenian que fallar")


def main() -> int:
    _autocomprobacion()
    filas = censo()
    print(__doc__.split("\n")[0])
    print(f"\n  reloj de diseno: {cm.F_CPU/1e6:.0f} MHz = {cm.F_CPU/1e6:.0f} Mciclos/s de UN nucleo\n")
    print(f"  {'fila':46} {'estado':9} {'Mciclos/s':>10} {'% nucleo':>9}   fuente")
    for f in filas:
        cifra = f"{f.ciclos_por_s/1e6:10.1f} {fraccion(f.ciclos_por_s)*100:8.1f}%" if f.ciclos_por_s else f"{'-':>10} {'-':>9}"
        print(f"  {f.nombre:46} {f.estado:9} {cifra}   {f.duenio}" + (f" ({f.nota})" if f.nota else ""))
    codigo = veredicto(filas)
    sin = [f for f in filas if f.ciclos_por_s is None]
    print(f"\n  con cifra: {len(filas) - len(sin)} de {len(filas)} filas, "
          f"{fraccion(suma_conocida(filas))*100:.1f} % de un nucleo")
    if codigo:
        print(f"\nHUECO: {len(sin)} filas sin cifra. Esto todavia no es un censo, y el 15 % del J2")
        print("  sigue siendo provisional hasta que lo sea (acta del 2026-10-17, ficha 2).")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
