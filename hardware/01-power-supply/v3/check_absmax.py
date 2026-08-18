"""Puerta: que sobrevive a un fallo de regulador, contra los maximos absolutos reales.

    python hardware/01-power-supply/v3/check_absmax.py

Por que existe. `design-notes.md` §16.8 decide donde va el crowbar y donde no, y
razona contra el AS3340 -- un chip que salio del instrumento el 2026-08-17 con el
respin del modulo 3. La razon textual para NO poner crowbar en -12 V era que el
3340 protege su VEE con un zener interno; el SSI2130 que lo reemplazo no lo hace,
tiene -18 V de maximo absoluto y punto (issue #114).

El problema de fondo no es ese parrafo: es que era un parrafo. Un analisis de
proteccion escrito en prosa no se entera de que un chip cambio. Este script si.

Modela DOS cosas y las cruza:

  * el BOM, via absmax.csv -- que chips cuelgan de los rieles y cual es su limite,
    cada uno con la cita de su datasheet primario;
  * la PROTECCION, via CROWBAR -- hasta donde deja subir cada riel un fallo.

Y responde una sola pregunta: en un fallo creible, ¿se sale alguien de rango?

Los tres fallos que se evaluan salen de §16.8 y de la topologia real:

  * `U1` (LM2941) en corto  -> el riel positivo ve VRAW+, salvo que el crowbar
    del riel positivo dispare antes;
  * `U2` (LM2990) en corto  -> lo mismo por abajo con VRAW-;
  * los dos a la vez        -> improbable pero barato de comprobar, y es el que
    dice si los limites TOTALES (no los de riel) aguantan.

Un crowbar no clava el riel en su umbral: dispara ahi y lo cortocircuita. Lo que
los chips llegan a ver es, como mucho, el umbral peor caso -- por eso el modelo
usa el 16.40 V de §16.8 y no el 14.6 del mejor caso.

Sale en ROJO (exit 2) si alguien se pasa. HOY SALE EN ROJO A PROPOSITO: es el
estado real del diseno, no un fallo del script.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Tension cruda tras puente y bulk, sin carga: es lo que ve el bus si el
# regulador de ese lado se pone en corto. Simulado en design-notes §16.5.
VRAW_POS = 20.54
VRAW_NEG = -20.54

# Riel sano.
NOM_POS = 12.00
NOM_NEG = -12.00

# Hasta donde deja subir cada riel la proteccion que EXISTE.
# None = sin crowbar en ese riel: el riel llega a VRAW y nadie lo para.
# El 16.40 es el umbral PEOR CASO del crowbar de §16.8 (rango 14.6-16.4).
CROWBAR: dict[str, float | None] = {
    "positivo": 16.40,   # D7 + Q1, heredado de la v1
    "negativo": None,    # <-- el hueco del #114
}


def leer_absmax() -> list[dict]:
    with open(HERE / "absmax.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        raise SystemExit("ROJO: absmax.csv vacio")
    return filas


def tension_de_riel(fallo: bool, signo: str) -> float:
    """Lo que el bus llega a ver en ese riel: nominal si no hay fallo, y si lo
    hay, VRAW recortado por el crowbar cuando ese riel tiene uno."""
    if not fallo:
        return NOM_POS if signo == "positivo" else NOM_NEG
    tope = CROWBAR[signo]
    if signo == "positivo":
        return VRAW_POS if tope is None else min(VRAW_POS, tope)
    return VRAW_NEG if tope is None else max(VRAW_NEG, -abs(tope))


def evaluar(chip: dict, v_pos: float, v_neg: float) -> list[str]:
    """Devuelve los motivos por los que este chip se sale. Lista vacia = sobrevive."""
    motivos = []
    solo_neg = chip["rieles"] == "solo_negativo"

    v_riel = chip["vmax_riel"].strip()
    if v_riel:
        lim = float(v_riel)
        if not solo_neg and v_pos > lim:
            motivos.append(f"+{v_pos:.2f} V sobre su limite de riel de {lim:g} V")
        if abs(v_neg) > lim:
            motivos.append(f"{v_neg:.2f} V sobre su limite de riel de {lim:g} V")

    v_tot = chip["vmax_total"].strip()
    if v_tot and not solo_neg:
        lim = float(v_tot)
        total = v_pos - v_neg
        if total > lim:
            motivos.append(f"{total:.2f} V totales sobre su limite de {lim:g} V")
    return motivos


ESCENARIOS = [
    # (nombre, falla el positivo, falla el negativo)
    ("riel sano", False, False),
    ("U1 (LM2941) en corto", True, False),
    ("U2 (LM2990) en corto", False, True),
    ("los dos en corto", True, True),
]


def pasada(chips: list[dict], titulo: str) -> list[str]:
    """Corre los cuatro escenarios con la proteccion que haya en CROWBAR.
    Devuelve los nombres de los chips que se salen en alguno."""
    print(f"=== {titulo} ===")
    print(f"    crowbar positivo={CROWBAR['positivo']}  negativo={CROWBAR['negativo']}\n")
    culpables: list[str] = []
    for nombre, f_pos, f_neg in ESCENARIOS:
        v_pos = tension_de_riel(f_pos, "positivo")
        v_neg = tension_de_riel(f_neg, "negativo")
        victimas = [(c, m) for c in chips if (m := evaluar(c, v_pos, v_neg))]

        marca = "ROJO " if victimas else "verde"
        print(f"[{marca}] {nombre:24s}  bus = {v_pos:+.2f} / {v_neg:+.2f} V")
        for c, motivos in victimas:
            pend = "  (modulo sin respinar)" if c["estado"] == "pendiente" else ""
            print(f"          {c['chip']:8s} modulos {c['modulos']:12s}{pend}")
            for m in motivos:
                print(f"            - {m}")
            if c["chip"] not in culpables:
                culpables.append(c["chip"])
        print()
    return culpables


def main() -> int:
    chips = leer_absmax()
    hoy = pasada(chips, "PROTECCION DE HOY (v1/v2: crowbar solo en el riel positivo)")

    # Segunda pasada con el crowbar de -12 V que propone el #114, para que la
    # puerta diga no solo donde estamos sino que compra el arreglo. Cuando la v3
    # lo lleve montado, esta constante sube arriba y esta pasada desaparece.
    CROWBAR["negativo"] = -16.40
    con_v3 = pasada(chips, "CON EL CROWBAR DE -12 V DE LA V3 (#114)")

    arreglados = [c for c in hoy if c not in con_v3]
    if arreglados:
        print(f"El crowbar de -12 V salva a: {', '.join(arreglados)}")
    if con_v3:
        print(f"NO basta para: {', '.join(con_v3)}")
        print()
        print("      El LM358 se pasa por los DOS lados, y por el positivo se")
        print("      pasa contra el crowbar que YA EXISTE: su limite de riel son")
        print("      +-16 V y el umbral peor caso del crowbar es 16.40 V. §16.8")
        print("      dimensiono ese umbral contra los 18 V del AS3340 y nadie")
        print("      miro el LM358. No se arregla con mas proteccion: se arregla")
        print("      en el modulo 6, que todavia no esta dibujado.")

    if hoy or con_v3:
        print()
        print("ROJO: hay chips fuera de maximo absoluto en un fallo creible.")
        print("      No es un fallo del script: es el estado del diseno (#114).")
        return 2
    print("verde: ningun chip se sale en ningun escenario.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
