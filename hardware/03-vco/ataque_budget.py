"""El camino de la nota al VCA, contra los 3 ms de voz-total S3.3.

    python ataque_budget.py

Lo manda el papel del evento (S5: "no existe") y lo llena el del generador de
envolvente (S9). Asevera lo CONOCIDO y declara HUECO lo que no se puede derivar
de ningun papel ni hoja (R-F1/R-J6): un presupuesto que rellenara los huecos con
supuestos daria un total y no diria nada.

--- Codigos de salida (convencion del repo, gates.py) ------------------------

  0  VERDE: no queda ningun hueco y la suma cabe.
  2  HUECO: lo conocido cabe con margen, pero faltan terminos por medir.
  1  ROJO: lo conocido ya no cabe.
"""
from __future__ import annotations

import sys

OBJETIVO_US = 3_000.0          # voz-total S3.3: <= 3 ms de nota a VCA
T_TICK_US = 100.0              # generador S1: F_RENDER = 10 kHz
T_ATAQUE_MIN_MS = 1.0          # generador S7: el ataque mas corto del rango
RC_MAX_US = T_ATAQUE_MIN_MS * 1000.0 / 10.0   # generador S9: un decimo del ataque minimo

# (termino, microsegundos o None si es HUECO, fuente)
FILAS = [
    ("reaccion del cerebro", None,
     "evento S5: depende de en que nucleo viva el host USB (C2)"),
    ("turno del J2", 100.0,
     "R-E1: ningun mensaje dura mas de 100 us (la cota viva; la cifra vieja del bus compartido no)"),
    ("parse del evento y encolado en el N657", None,
     "bring-up: ISR del esclavo SPI bajo carga plena (motor-digital S7)"),
    ("latencia de la ISR del tick", None,
     "bring-up: el tick en el escalon del DMA de audio/CV, debajo de capturas y J2"),
    ("primer tick del generador", T_TICK_US,
     "generador S3.5: el evento se drena al principio del tick siguiente"),
    ("latencia de bloque del DMA de CV lento", None,
     "motor-digital S5 no declara el tamano de bloque"),
    ("escritura y asentamiento del DAC", None,
     "hoja del DAC que R-M3 nombre"),
    ("RC de reconstruccion", RC_MAX_US,
     "generador S9: RC <= un decimo del ataque minimo"),
]


def main() -> int:
    conocido = sum(v for _, v, _ in FILAS if v is not None)
    huecos = [n for n, v, _ in FILAS if v is None]
    print(f"nota -> VCA contra {OBJETIVO_US:.0f} us (voz-total S3.3)\n")
    for nombre, valor, fuente in FILAS:
        cifra = f"{valor:7.1f} us" if valor is not None else "   HUECO  "
        print(f"  {nombre:42s} {cifra}   {fuente}")
    print(f"\n  conocido: {conocido:.0f} us de {OBJETIVO_US:.0f} "
          f"({conocido / OBJETIVO_US:.0%}); {len(huecos)} huecos se reparten "
          f"{OBJETIVO_US - conocido:.0f} us")
    assert conocido < OBJETIVO_US, (
        f"lo conocido ({conocido:.0f} us) ya no cabe en {OBJETIVO_US:.0f}")
    # la RC y el tick son cotas de diseno, no medidas: si alguien las mueve, aqui grita
    assert RC_MAX_US <= T_TICK_US, "la RC no puede ser mas lenta que un tick"
    if huecos:
        print("\nHUECO: faltan " + ", ".join(huecos) + ". Se miden en bring-up.")
        return 2
    print("\nOK: presupuesto cerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
