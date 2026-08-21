"""Puerta: las huellas hechas a mano dicen la verdad sobre la pieza que llevan.

    python check_huellas.py

## El fallo que esto persigue

Una huella equivocada es el fallo que no perdona: pasa el ERC, pasa el DRC,
pasa la netlist, se fabrica, se monta, y aparece cuando la pieza no entra o
entra girada. Ninguna puerta de las que hay lo ve, porque todas comprueban
CONECTIVIDAD y esto es geometria.

Esta placa tiene tres huellas propias, en `../kicad/sam17.pretty`, y existen
porque KiCad 10 no las trae (design-notes sec.14.3). Una huella de libreria la
ha revisado mucha gente; una propia, solo quien la dibujo.

## Lo que comprueba, y lo que NO puede comprobar

Comprueba la **coherencia interna**: que el paso que anuncia el nombre sea el
paso real de los pads, que el cuerpo que anuncia quepa en su courtyard, y que
el BOM y la huella hablen de la misma pieza.

Lo que NO puede comprobar es lo unico que cierra el asunto de verdad: que esas
cotas sean las de la pieza REAL, que eso solo sale del datasheet del
fabricante. Eso queda como hueco declarado abajo, con nombre y apellido.

Un nombre de huella es un contrato: `P10.0mm` promete 10 mm entre pads, y si
la geometria dice otra cosa, quien elija la pieza por el nombre se equivoca.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.join(DIR, "..", "kicad", "sam17.pretty")
BOM = os.path.join(DIR, "bom.csv")

# Lo que falta por confirmar contra la hoja del fabricante, con QUE habria que
# medir. No se disimula: se lista, se cuenta y se imprime (Principio V).
SIN_CONFIRMAR = [
    ("RV1", "S20K275 / V275LA20A",
     "diametro del disco CON recubrimiento contra el courtyard de 23.00 mm",
     "decidio bajar la barrera de red de y=128 a y=121 (README v3)"),
    ("NT1", "NTC 5R/2A",
     "diametro del disco y paso real de patas",
     "va en serie con el primario: si no entra, no hay limitador de inrush"),
    ("J5", "Faston 6.3x0.8",
     "ancho de la lengueta y separacion de sus dos patas",
     "es el UNICO puente chasis-masa de todo el instrumento (sec.13)"),
]


def lee_huella(ruta: str) -> dict:
    s = open(ruta, encoding="utf-8").read()
    pads = [(n, float(x), float(y)) for n, x, y in re.findall(
        r'\(pad "([^"]*)"\s+\w+\s+\w+\s*\(at ([-\d.]+) ([-\d.]+)', s)]
    drills = [float(d) for d in re.findall(r"\(drill ([\d.]+)\)", s)]
    crt = re.findall(
        r'\(fp_(?:line|rect)\s*\(start ([-\d.]+) ([-\d.]+)\)\s*'
        r'\(end ([-\d.]+) ([-\d.]+)\).*?"F\.CrtYd"', s, re.S)
    xs = [float(v) for t in crt for v in (t[0], t[2])]
    ys = [float(v) for t in crt for v in (t[1], t[3])]
    return {"pads": pads, "drills": drills,
            "crt": (max(xs) - min(xs), max(ys) - min(ys)) if xs else None}


def main() -> int:
    fallos: list[str] = []
    usadas = {}
    with open(BOM, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            hu = fila.get("footprint", "")
            if hu.startswith("sam17:"):
                usadas.setdefault(hu.split(":", 1)[1], []).append(fila["refs"])

    ficheros = sorted(f for f in os.listdir(PRETTY) if f.endswith(".kicad_mod"))
    print(f"{len(ficheros)} huellas propias en sam17.pretty\n")

    for fn in ficheros:
        nom = fn[:-len(".kicad_mod")]
        h = lee_huella(os.path.join(PRETTY, fn))
        quien = ", ".join(usadas.get(nom, [])) or "NADIE"
        print(f"  {nom}")
        print(f"    la usa: {quien}")

        # 1) el paso que promete el nombre contra el paso real
        mp = re.search(r"_P([\d.]+)mm", nom)
        if mp and len(h["pads"]) >= 2:
            declarado = float(mp.group(1))
            xs = sorted(p[1] for p in h["pads"])
            real = max(xs) - min(xs)
            marca = "OK" if abs(real - declarado) < 0.01 else "NO CUADRA"
            print(f"    paso: nombre dice {declarado} mm, los pads dan "
                  f"{real:.2f} mm  -> {marca}")
            if marca != "OK":
                fallos.append(f"{nom}: el nombre promete {declarado} mm de paso "
                              f"y los pads estan a {real:.2f}. Quien elija la "
                              f"pieza por el nombre se equivoca")

        # 2) el cuerpo que anuncia el nombre tiene que caber en el courtyard
        md = re.search(r"_D([\d.]+)mm", nom)
        if md and h["crt"]:
            cuerpo, (cx, cy) = float(md.group(1)), h["crt"]
            holgura = min(cx, cy) - cuerpo
            print(f"    cuerpo: nombre dice D{cuerpo} mm, courtyard "
                  f"{cx:.2f} x {cy:.2f} -> {holgura:+.2f} mm de holgura")
            if holgura < 0:
                fallos.append(f"{nom}: el courtyard ({min(cx,cy):.2f} mm) es "
                              f"MENOR que el cuerpo que anuncia el nombre "
                              f"(D{cuerpo}): la pieza no cabe en su propia caja")

        # 3) una huella propia que no usa nadie es una huella que sobra, y una
        #    que usa alguien sin estar aqui la habria cazado ya check_bom.py
        if quien == "NADIE":
            fallos.append(f"{nom}: no la usa ningun componente del BOM")
        print(f"    taladros: {sorted(set(h['drills']))}")
        print()

    print(f"lo NO confirmado contra la hoja del fabricante: "
          f"{len(SIN_CONFIRMAR)}")
    for ref, pieza, que, porque in SIN_CONFIRMAR:
        print(f"  - {ref} ({pieza}): falta {que}")
        print(f"    importa porque {porque}")

    if fallos:
        print(f"\nFALLO: {len(fallos)}")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\nOK: las tres huellas propias son coherentes con su nombre y las "
          "usa\n    alguien. Las cotas contra datasheet siguen sin confirmar "
          "(arriba).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
