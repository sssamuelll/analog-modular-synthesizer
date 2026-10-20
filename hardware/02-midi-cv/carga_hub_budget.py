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
  la puerta `recuperacion_j2_budget.py` (papel v3, 5.2a): de las filas del tic
  con las cachés del hub, a 800 MHz y 8 kHz, las de mas ranuras; de cada regimen
  de cache, la ultima; y la peor de las dos, por 6 ranuras x 8 kHz giros por
  segundo. La cifra de cada fila es la que fijo la ficha J del acta del
  2026-10-19 (tercera firma): el DWT mas la entrada, la cadena y la salida de la
  excepcion. Medida con menos de seis ranuras es ESTIMADO, porque la columna de
  seis es aritmetica; sin las filas de los dos regimenes es HUECO. Las cifras de
  exploracion de EN-PLACA (sin region MPU) no son filas.

LAS OBLIGACIONES DE TIEMPO (R-H6, la segunda tabla)

  El papel v3 del transporte del J2 (R-H6) pide dos tablas: la de ciclos de
  arriba y una de obligaciones de tiempo que el J2 le pone al hub -- niveles,
  ventanas de inanicion, maximo enmascarado, huella en TCM y ocupacion
  sostenida del nivel 2 --, que son la moneda de R-H1 a R-H4. Una obligacion es
  HUECO hasta que el hub muestre que la cumple; una cifra del banco del J2 es
  evidencia, no prueba del hub. La de la ocupacion sostenida la pide el acta
  del 2026-10-19 (tercera firma, nota de la ficha C): con el nivel 2 ocupado
  ~94 % durante ~100 ms un bloqueo del GPDMA1 encadena incidentes, las ranuras
  sobreviven y los modulos pasan de 60 a 85 ms sin trama (S, Halberg N13), y el
  aserto del modulo, que vale por incidente, no lo ve.

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

# El USB del instrumento (`atender` y el OTG) con 1 000 mensajes MIDI/s, medido en el banco del J2
# con las dos caches encendidas: el hilo libre de `carga_j2` baja de 931 a 921 por mil
# (fw/EN-PLACA.md, «El USB con trafico, medido»). Ningun papel fija ese ritmo: con 5 000/s son 21.
USB_POR_MIL = 10


@dataclass(frozen=True)
class Fila:
    nombre: str
    duenio: str
    estado: str
    ciclos_por_s: float | None
    nota: str = ""


@dataclass(frozen=True)
class Obligacion:
    nombre: str
    limite: str
    fuente: str
    estado: str
    evidencia: str = ""


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


def fila_j2(carga: list[dict] | None = None) -> Fila:
    """La fila de `carga_j2.csv` que cuenta (papel v3, 5.2a), por los giros por segundo del lazo."""
    u = rj.del_rust()
    giros_s = u["ranuras_spi"] * rj.tb.F_LAZO_HZ
    nombre, duenio = "J2: el trabajo propio del enlace", "acta del 2026-10-19, tercera firma, ficha J"
    peor, faltan = rj.peor_regimen(rj.lee_filas(rj._CSV_CARGA) if carga is None else carga, cm.F_CPU,
                                   round(1e6 / rj.tb.F_LAZO_HZ))
    if not peor:
        return Fila(nombre, duenio, HUECO, None,
                    f"carga_j2.csv no tiene fila del hub con el regimen {', '.join(faltan)} (papel v3, 5.2a)")
    ciclos, n = int(peor["ciclos_por_giro"]), int(peor["ranuras"])
    # Con menos ranuras que el hub, la columna de seis es aritmetica sobre la medida.
    estado = MEDIDO if n >= u["ranuras_spi"] else ESTIMADO
    return Fila(nombre, duenio, estado, ciclos * giros_s,
                f"{ciclos} ciclos por giro x {giros_s:.0f} giros/s, el peor regimen del hub "
                f"({peor['regimen_cache']}, {peor['fecha']}, carga_j2.csv, medido con {n} ranuras); "
                f"limite provisional: {rj.FRACCION_CPU_J2*100:.0f} %")


def censo() -> list[Fila]:
    return [
        fila_j2(),
        Fila("J2: componer las tramas", "cabecera J2, planificador (#267)", HUECO, None,
             "la trama sale de notas, CV y pantalla; no cuenta contra el J2 (acta del 17-10)"),
        Fila("Pantalla: LTDC, GPU y la interfaz", "hub 3.1 (D2) y pantalla-motor", HUECO, None,
             "el framebuffer sale de AXISRAM o PSRAM: tambien pesa en el bus"),
        Fila("Mandos alrededor de la pantalla", "hub 3.3", HUECO, None, ""),
        Fila("USB (dispositivo) y MIDI", "fw/src/usb.rs; sin papel de CPU", MEDIDO,
             USB_POR_MIL / 1000 * cm.F_CPU,
             f"{USB_POR_MIL} por mil con 1 000 mensajes MIDI/s y las caches encendidas (EN-PLACA); "
             "21 con 5 000"),
        Fila("Radios: satelites y BLE", "hub 4.2 (D4)", HUECO, None,
             "coprocesador de radio por SPI o UART, con TDMA propio"),
        Fila("Escritor de CV", "#367", HUECO, None, "si comparte el GPDMA1 con el J2, ademas pesa en R-H3"),
        Fila("Descubrimiento I2C", "spec del maestro J2 (D2)", HUECO, None, ""),
        Fila("Supervisor de vitalidad y el IWDG", "#291", HUECO, None, ""),
        Fila("Runtime: embassy-time y el ejecutor de hilo", "fw", HUECO, None, ""),
        Fila("Margen reservado", "acta del 2026-09-09 (hub 0)", HUECO, None,
             "\"suficiente headroom\" sin numero"),
    ]


def veredicto_obligaciones(obligaciones: list[Obligacion]) -> int:
    """0 si el hub probo todas, 2 si queda alguna sin prueba."""
    return 2 if any(o.estado == HUECO for o in obligaciones) else 0


def obligaciones() -> list[Obligacion]:
    v3 = "papel v3 del transporte del J2"
    acta = "acta del 2026-10-19, tercera firma"
    return [
        Obligacion("R-H1: ninguna ISR por encima del tic", "el tic en el nivel 1, nada en el 0",
                   f"{v3}, R-H1", HUECO,
                   "fw: usb::iniciar baja a P2 el USB, TIM12 y los DMA, y j2_tic::lanzar no arranca "
                   "con una por encima; el instrumento todavia no lanza el tic (EN-PLACA)"),
        Obligacion("R-H1: inanicion del planificador (P3)",
                   "<= 12 ms de pendiente a terminado", f"{v3}, R-H1; {acta}, fichas B y C", HUECO,
                   "testigo latencia_plan_max_us de fw, de pendiente a terminado; "
                   "banco: 34 us con el USB a 5 000 mensajes MIDI/s (EN-PLACA)"),
        Obligacion("R-H1: inanicion de la recuperacion (P4)",
                   "<= 12 ms de pendiente a terminado", f"{v3}, R-H1; {acta}, fichas B y C", HUECO,
                   "testigo latencia_rec_max_us de fw, de pendiente a terminada; solo en el banco"),
        Obligacion("R-H2: maximo enmascarado", "<= 5 us por seccion critica", f"{v3}, R-H2", HUECO,
                   "banco, con las dos caches: 0,77 us, y 3,4 us frias (el temporizador de embassy-time, "
                   "TIM12); 9,9 us con las caches apagadas; desde la RAM, no desde XSPI (EN-PLACA)"),
        Obligacion("R-H2: entrada del tic", "<= 60 us desde su instante", f"{v3}, R-H2 y 2.8", HUECO,
                   "banco: 6 us con el USB a 1 000 mensajes MIDI/s y 4 us a 5 000 (EN-PLACA)"),
        Obligacion("R-H4: el enlace del J2 en TCM", "ITCM 8 224 B y DTCM 5 128 B (referencia)",
                   f"{acta}, ficha H", HUECO, "reservarlas y las dos obligaciones de arranque (#231)"),
        Obligacion("R-H6: ocupacion sostenida del nivel 2", "excluir ~94 % durante ~100 ms",
                   f"{acta}, nota de la ficha C (Halberg N13)", HUECO),
        Obligacion("R-H9: el contador de ciclos corre siempre", "DWT_CYCCNT encendido y sin parar",
                   f"{v3}, R-H9", HUECO, "y si el nucleo duerme con el J2 girando"),
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
    # La tabla de obligaciones: sin pruebas del hub es HUECO, y una sola sin prueba basta.
    cumple = Obligacion("a", "x", "y", MEDIDO)
    sin_prueba = Obligacion("b", "x", "y", HUECO)
    assert veredicto_obligaciones([cumple]) == 0
    assert veredicto_obligaciones([cumple, sin_prueba]) == 2
    assert all(o.estado == HUECO for o in obligaciones()), "el hub aun no ha probado ninguna"
    # La fila del J2 es la del peor regimen del hub en carga_j2.csv, y sin ella es HUECO, no cero.
    def f(ciclos, regimen):
        return {"ciclos_por_giro": str(ciclos), "regimen_cache": regimen, "transporte": "tic",
                "cache": "icache+dcache-mpu", "f_cpu_hz": "800000000", "ranuras": "3",
                "periodo_us": "125", "fecha": "x"}
    giros_s = rj.del_rust()["ranuras_spi"] * rj.tb.F_LAZO_HZ
    tres = fila_j2([f(2300, "caliente"), f(2450, "fria")])
    assert tres.ciclos_por_s == 2450 * giros_s and tres.estado == ESTIMADO, tres
    assert fila_j2([f(2300, "caliente")]).estado == HUECO
    assert fila_j2([f(2300, "caliente")]).ciclos_por_s is None


def main() -> int:
    _autocomprobacion()
    filas = censo()
    print(__doc__.split("\n")[0])
    print(f"\n  reloj de diseno: {cm.F_CPU/1e6:.0f} MHz = {cm.F_CPU/1e6:.0f} Mciclos/s de UN nucleo\n")
    print(f"  {'fila':46} {'estado':9} {'Mciclos/s':>10} {'% nucleo':>9}   fuente")
    for f in filas:
        cifra = f"{f.ciclos_por_s/1e6:10.1f} {fraccion(f.ciclos_por_s)*100:8.1f}%" if f.ciclos_por_s else f"{'-':>10} {'-':>9}"
        print(f"  {f.nombre:46} {f.estado:9} {cifra}   {f.duenio}" + (f" ({f.nota})" if f.nota else ""))
    obls = obligaciones()
    print("\n  las obligaciones de tiempo que el J2 le pone al hub (R-H6):\n")
    for o in obls:
        print(f"  {o.nombre:46} {o.estado:9} {o.limite}   {o.fuente}"
              + (f" ({o.evidencia})" if o.evidencia else ""))
    codigo = max(veredicto(filas), veredicto_obligaciones(obls))
    sin = [f for f in filas if f.ciclos_por_s is None]
    print(f"\n  con cifra: {len(filas) - len(sin)} de {len(filas)} filas, "
          f"{fraccion(suma_conocida(filas))*100:.1f} % de un nucleo")
    if codigo:
        sin_prueba = sum(o.estado == HUECO for o in obls)
        print("\n  Esto todavia no es un censo, y el 15 % del J2 sigue siendo provisional hasta que lo")
        print("  sea (acta del 2026-10-17, ficha 2).")
        print(f"HUECO: {len(sin)} filas sin cifra y {sin_prueba} obligaciones sin prueba del hub")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
