"""Puerta: las huellas de los modulos de la v5 casan con el plano de su hoja.

    python check_huellas.py        # 0 verde, 1 rojo, 2 sin libreria de KiCad

La version de #474 tenia una tabla CONFIRMADO con cotas que no se usaba para
comprobar nada: solo miraba que existiera un courtyard. Y las tres huellas de
modulo eran la misma huella generica de 6 pines -- que el URB, el THN 20WI y el
THN 30WI no comparten --.

Aqui cada huella se lee del .kicad_mod (la propia de sam17.pretty o la de
KiCad) y se mide contra las cotas del plano, escritas de nuevo desde la hoja
--no copiadas de build_huellas.py--:

  * distancias entre pads (no dependen del origen ni de la orientacion);
  * el SENTIDO de la numeracion: las hojas de TRACO dibujan la vista INFERIOR
    y la huella es la SUPERIOR, asi que la secuencia 1 -> 2 -> 3 tiene que
    girar al reves que en el dibujo. Una huella con las distancias bien y la
    vista mal monta el modulo en espejo;
  * taladro >= patilla + 0,2 mm.
"""
from __future__ import annotations

import csv
import math
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.join(DIR, "kicad", "sam17.pretty")
BOM = os.path.join(DIR, "bom.csv")
KICAD_FP = os.environ.get(
    "KICAD_FOOTPRINTS", r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
    if os.name == "nt" else "/usr/share/kicad/footprints")
DS = "docs/reference/datasheets"
TOL = 0.05

# ref: (hoja, {(pad_a, pad_b): distancia}, (pad1, pad2, pad3, signo), patilla, sentido)
# signo del producto vectorial (p2 - p1) x (p3 - p1) en la huella, con Y hacia
# abajo como la escribe KiCad. +1 = antihorario visto desde arriba.
PLANOS = {
    "PS1": {
        "hoja": f"{DS}/traco_thn30wi.pdf p. 5 (bottom view)",
        "dist": {("1", "2"): 5.08, ("2", "6"): 7.62, ("6", "5"): 20.32,
                 ("5", "4"): 10.16, ("4", "3"): 10.16, ("1", "3"): math.hypot(7.62, 20.32)},
        # Vista inferior de la hoja: 6-2-1 arriba de izquierda a derecha y 5-4-3
        # abajo. Vista superior: espejo -> 1-2-6 de izquierda a derecha.
        "giro": ("1", "2", "3", +1),
        "patilla": 1.0,
    },
    "PS2": {
        "hoja": f"{DS}/mornsun_urb_ymd20wr3.pdf p. 6 (Top View, PCB Layout)",
        "dist": {("1", "2"): 7.62, ("2", "3"): 5.08, ("1", "6"): 20.32,
                 ("6", "5"): 10.16, ("5", "4"): 10.16, ("1", "4"): math.hypot(20.32, 20.32)},
        "giro": ("1", "6", "2", +1),
        "patilla": 1.0,
    },
    "PS3": {
        "hoja": f"{DS}/mornsun_k78_t1000r3.pdf p. 5 (PCB Layout, top view)",
        "dist": {("1", "2"): 2.54, ("2", "3"): 2.54, ("3", "4"): 2.54, ("4", "5"): 2.54,
                 ("1", "10"): 10.10, ("4", "7"): 10.10, ("5", "6"): 10.10},
        "giro": ("1", "5", "10", -1),
        "patilla": 0.0,
    },
    "J5": {
        "hoja": "Vogt AG, Steckzungen fuer gedruckte Schaltungen, 3866A.68: A 5 = 5.0 mm",
        "dist": {},
        "faston": 5.0,
        "patilla": 0.8,
    },
}
PS_IGUALES = {"PS4": "PS1", "PS5": "PS1"}   # THN 20WI = THN 30WI, mismo 1x1 pulgada


def ruta_huella(fp: str) -> str:
    lib, _, nombre = fp.partition(":")
    base = PRETTY if lib == "sam17" else os.path.join(KICAD_FP, f"{lib}.pretty")
    return os.path.join(base, f"{nombre}.kicad_mod")


def pads(ruta: str) -> list[tuple[str, float, float, float]]:
    with open(ruta, encoding="utf-8") as fh:
        s = fh.read()
    out = []
    for m in re.finditer(r'\(pad\s+"([^"]*)"\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)', s):
        cola = s[m.end():m.end() + 400]
        d = re.search(r"\(drill\s+([-\d.]+)", cola)
        out.append((m.group(1), float(m.group(2)), float(m.group(3)),
                    float(d.group(1)) if d else 0.0))
    return out


def main() -> int:
    huellas: dict[str, str] = {}
    with open(BOM, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            for r in (x.strip() for x in fila["refs"].split(",")):
                huellas[r] = fila["footprint"]

    fallos: list[str] = []
    huecos: list[str] = []
    for ref in list(PLANOS) + list(PS_IGUALES):
        plano = PLANOS[PS_IGUALES.get(ref, ref)]
        ruta = ruta_huella(huellas[ref])
        if not os.path.exists(ruta):
            huecos.append(f"{ref}: no encuentro {huellas[ref]} (KICAD_FOOTPRINTS)")
            continue
        p = {n: (x, y, d) for n, x, y, d in pads(ruta)}
        print(f"  {ref:<4} {huellas[ref]}\n       contra {plano['hoja']}")
        if "faston" in plano:
            unos = [(x, y, d) for n, x, y, d in pads(ruta) if n == "1"]
            if len(unos) != 2 or abs(math.dist(unos[0][:2], unos[1][:2]) - plano["faston"]) > TOL:
                fallos.append(f"{ref}: el Faston necesita dos pads '1' a {plano['faston']} mm")
            p = {"1": unos[0]} if unos else {}
        for (a, b), dist in plano["dist"].items():
            if a not in p or b not in p:
                fallos.append(f"{ref}: falta el pad {a if a not in p else b}")
                continue
            real = math.dist(p[a][:2], p[b][:2])
            if abs(real - dist) > TOL:
                fallos.append(f"{ref}: pads {a}-{b} a {real:.2f} mm y la hoja dice {dist:.2f}")
        if "giro" in plano:
            a, b, c, signo = plano["giro"]
            (x1, y1, _), (x2, y2, _), (x3, y3, _) = p[a], p[b], p[c]
            cruz = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
            if cruz * signo <= 0:
                fallos.append(f"{ref}: numeracion en ESPEJO ({a}->{b}->{c} gira al reves "
                              f"que en la hoja): el modulo se montaria dado la vuelta")
        for n, (_x, _y, d) in p.items():
            if plano["patilla"] and d < plano["patilla"] + 0.2 - 1e-9:
                fallos.append(f"{ref}: taladro de {d} mm para una patilla de {plano['patilla']} mm")

    for h in huecos:
        print(f"HUECO: {h}")
    if fallos:
        print(f"\nFALLO: {len(fallos)}")
        for f in fallos:
            print(f"  - {f}")
        return 1
    if huecos:
        return 2
    print(f"\nOK: check_huellas v5 -- {len(PLANOS) + len(PS_IGUALES)} huellas de modulo "
          "casan con su plano (distancias, vista y taladro)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
