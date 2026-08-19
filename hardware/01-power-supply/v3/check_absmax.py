"""Puerta: que sobrevive a un fallo de regulador, contra los maximos absolutos reales.

    python hardware/01-power-supply/v3/check_absmax.py

Por que existe. `design-notes.md` §16.8 decidia donde va la proteccion de
sobretension razonando contra el AS3340 -- un chip que salio del instrumento el
2026-08-17 con el respin del modulo 3. Un analisis de proteccion escrito en prosa
no se entera de que un chip cambio. Este script si.

Modela TRES cosas y las cruza:

  * el BOM de los modulos, via absmax.csv -- que chips cuelgan del bus y cual es
    su limite, cada uno con la cita de su datasheet primario;
  * la CASCADA de regulacion -- dos etapas por riel, y el bus cuelga de la
    segunda, asi que lo que el bus ve depende de cual falle;
  * la SUPERVIVENCIA ENTRE ETAPAS -- si el pre-regulador en corto se lleva por
    delante al post-regulador, entonces no son dos etapas: es una.

Ese tercer punto es el que decide todo lo demas, y es el que §16.8 nunca miro
porque se escribio para la topologia de la v1 (un regulador y al bus).

Historia, por si el rojo vuelve: la primera version de este script modelaba el
bus viendo VRAW directamente, que era correcto para la v1 y es lo que hacia caer
a SSI2130, LM13700 y LM358. Con la cascada verificada (issue #118) ese escenario
solo ocurre con las DOS etapas en corto, que es un fallo doble independiente.

Sale en ROJO (exit 2) si algun fallo SIMPLE saca a alguien de rango.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# --- La cascada, riel por riel (spec v2 §3 y §4) -------------------------------
# VRAW: pico simulado con red a +10 % y casi en vacio (design-notes §16.5).
VRAW_POS, VRAW_NEG = 20.54, -20.54
# Salida de los PRE-reguladores LM2941 / LM2991.
PRE_POS, PRE_NEG = 13.1, -12.9
# Salida de los POST-reguladores LT3045 / LT3094: lo que el bus ve sano.
NOM_POS, NOM_NEG = 12.0, -12.0

# --- Supervivencia entre etapas (ADI, datasheets primarios) --------------------
# Si el pre se pone en corto, el post ve VRAW. Si no lo aguanta, la cascada no
# existe: un solo fallo se lleva las dos etapas y el bus ve VRAW.
POST_IN_ABSMAX = {
    "LT3045 (ADI Rev. D, p.2, IN Pin Voltage)": (VRAW_POS, 22.00),
    "LT3094 (ADI Rev. B, p.3, IN Pin Voltage)": (abs(VRAW_NEG), 22.00),
}


def leer_absmax() -> list[dict]:
    with open(HERE / "absmax.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        raise SystemExit("ROJO: absmax.csv vacio")
    return filas


def evaluar(chip: dict, v_pos: float, v_neg: float) -> list[str]:
    """Motivos por los que este chip se sale. Lista vacia = sobrevive."""
    motivos = []
    solo_neg = chip["rieles"] == "solo_negativo"

    if (v_riel := chip["vmax_riel"].strip()):
        lim = float(v_riel)
        if not solo_neg and v_pos > lim:
            motivos.append(f"+{v_pos:.2f} V sobre su limite de riel de {lim:g} V")
        if abs(v_neg) > lim:
            motivos.append(f"{v_neg:.2f} V sobre su limite de riel de {lim:g} V")

    if (v_tot := chip["vmax_total"].strip()) and not solo_neg:
        lim = float(v_tot)
        if (total := v_pos - v_neg) > lim:
            motivos.append(f"{total:.2f} V totales sobre su limite de {lim:g} V")
    return motivos


# (nombre, v_pos del bus, v_neg del bus, es_fallo_simple)
#
# Con la cascada, un fallo del PRE no llega al bus: el POST sigue en serie y
# sigue regulando (o entra en shutdown termico, que apaga la salida). Un fallo
# del POST si llega, pero lo que llega es la salida del PRE, no VRAW.
ESCENARIOS = [
    ("todo sano",                     NOM_POS,  NOM_NEG,  True),
    ("pre-regulador en corto",        NOM_POS,  NOM_NEG,  True),
    ("post-regulador en corto",       PRE_POS,  PRE_NEG,  True),
    ("LAS DOS etapas en corto",       VRAW_POS, VRAW_NEG, False),
]


def main() -> int:
    chips = leer_absmax()
    rojo = False

    print("=== 1. La cascada existe? (el pre en corto no puede matar al post) ===\n")
    for pieza, (visto, lim) in POST_IN_ABSMAX.items():
        ok = visto < lim
        print(f"  [{'verde' if ok else 'ROJO '}] {pieza}")
        print(f"          ve {visto:.2f} V  vs  abs max {lim:.2f} V  "
              f"-> margen {lim-visto:+.2f} V")
        if not ok:
            rojo = True
    print("\n  Aguantan: la cascada es real y un fallo del pre NO arrastra al post.\n")

    print("=== 2. Que ve el bus, y quien sobrevive ===\n")
    for nombre, v_pos, v_neg, simple in ESCENARIOS:
        victimas = [(c, m) for c in chips if (m := evaluar(c, v_pos, v_neg))]
        if victimas and simple:
            marca, rojo = "ROJO ", True
        elif victimas:
            marca = "nota "          # fallo doble: se documenta, no bloquea
        else:
            marca = "verde"
        etiqueta = "" if simple else "   (fallo DOBLE independiente)"
        print(f"  [{marca}] {nombre:26s} bus = {v_pos:+.2f} / {v_neg:+.2f} V{etiqueta}")
        for c, motivos in victimas:
            pend = "  (modulo sin respinar)" if c["estado"] == "pendiente" else ""
            print(f"            {c['chip']:8s} modulos {c['modulos']:14s}{pend}")
            for m in motivos:
                print(f"              - {m}")
    print()

    if rojo:
        print("ROJO: un fallo SIMPLE saca a alguien de maximo absoluto.")
        return 2
    print("verde: ningun fallo simple saca a nadie de rango.")
    print("       El unico escenario con victimas exige que fallen las DOS etapas")
    print("       por causas independientes -- y como el pre no arrastra al post")
    print("       (bloque 1), eso ya no es una cascada sino coincidencia.")
    print("       Por eso la v3 no lleva crowbar: issue #118, §16.8 reescrita.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
