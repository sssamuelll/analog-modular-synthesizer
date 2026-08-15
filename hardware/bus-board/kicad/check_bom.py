"""Cruza bom.csv contra los designadores reales del esquematico, en los dos
sentidos: ninguna pieza sin linea de compra, ninguna linea apuntando a algo
que no existe.

    python check_bom.py
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(DIR, "sam17-bus.kicad_sch")
BOM = os.path.join(DIR, "..", "bom.csv")
# H1..H7 son taladros: van en el BOM (hay que comprar separadores) y no en el
# esquematico, que es lo correcto en los dos sitios.
SOLO_BOM = {f"H{i}" for i in range(1, 8)} | {"—"}


def del_esquematico() -> set[str]:
    with open(SCH, encoding="utf-8") as fh:
        txt = fh.read()
    # Se leen los bloques (instances ...), no las propiedades "Reference": esas
    # tambien existen dentro de lib_symbols con el prefijo pelado de la
    # libreria ("D", "R", "F", "J"), y colarlas daba cuatro componentes
    # fantasma que ningun BOM podria cubrir jamas.
    # (reference "X") solo aparece dentro de (instances ...); las propiedades
    # se escriben como (property "Reference" "X"), asi que no colisionan.
    refs = set(re.findall(r'\(reference "([^"]+)"', txt))
    return {r for r in refs if not r.startswith("#")}


def main() -> None:
    hoja = del_esquematico()
    bom: set[str] = set()
    with open(BOM, encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            bom |= set(fila["refs"].split())

    sin_comprar = sorted(hoja - bom, key=lambda r: (r[0], int(r[1:] or 0)))
    inventadas = sorted(bom - hoja - SOLO_BOM)
    for m, lista in (("en la hoja pero sin linea de compra", sin_comprar),
                     ("en el BOM pero no en la hoja", inventadas)):
        if lista:
            print(f"FALLO: {m}: {lista}")
    if sin_comprar or inventadas:
        sys.exit(1)
    print(f"OK: {len(hoja)} componentes en la hoja, "
          f"{len(bom & hoja)} cruzados, {len(SOLO_BOM) - 1} taladros solo-BOM")


if __name__ == "__main__":
    main()
