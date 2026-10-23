"""Cruza bom.csv contra los designadores, valores y huellas reales del esquematico v5.

    python check_bom.py        # sale con codigo != 0 si no cuadran

Por cada componente de la hoja sam17-power-v5.kicad_sch comprueba que este en
bom.csv y que su valor y su huella sean EXACTAMENTE los de la fila del BOM, y
que no sobren designadores en ninguna de las dos partes. Un valor o una huella
distintos en la hoja y en el BOM sale con codigo 1: la hoja es lo que KiCad
rutea y el BOM lo que se compra, y si no dicen lo mismo se fabrica una cosa y
se monta otra.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(DIR, "sam17-power-v5.kicad_sch")
BOM = os.path.join(DIR, "..", "bom.csv")

PROPIEDAD = re.compile(r'\(property "([^"]+)" "((?:[^"\\]|\\.)*)"')
DESIGNADOR = re.compile(r"[A-Z]+\d+")
OFFSHEET_PREFIX = ("TR", "HS", "XU")


def leer_hoja(texto: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """{designador: {value, footprint}} de las instancias de la hoja.

    Las instancias son los `(symbol` con una tabulacion; los de lib_symbols van
    con dos, y los simbolos de alimentacion (#PWR) no son componentes.
    """
    hoja: dict[str, dict[str, str]] = {}
    choques: list[str] = []
    for bloque in re.split(r"\n\t\(symbol\n", texto)[1:]:
        prop: dict[str, str] = {}
        for clave, valor in PROPIEDAD.findall(bloque):
            prop.setdefault(clave, valor.replace('\\"', '"').strip())
        ref = prop.get("Reference", "")
        if not DESIGNADOR.fullmatch(ref):
            continue
        datos = {"value": prop.get("Value", ""), "footprint": prop.get("Footprint", "")}
        if ref in hoja and hoja[ref] != datos:
            choques.append(f"{ref} aparece dos veces en la hoja con valor/huella distintos")
        hoja[ref] = datos
    return hoja, choques


def main() -> int:
    if not os.path.exists(SCH):
        print(f"HUECO: falta {os.path.basename(SCH)} -- corre build_schematic.py primero")
        return 2

    with open(SCH, encoding="utf-8") as fh:
        hoja, fallos = leer_hoja(fh.read())

    bom: dict[str, dict] = {}
    dupes = []
    with open(BOM, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            for ref in (r.strip() for r in row["refs"].split(",")):
                if not ref or ref == "—":
                    continue
                if ref in bom:
                    dupes.append(ref)
                bom[ref] = {
                    "value": row.get("value", "").strip(),
                    "footprint": row.get("footprint", "").strip(),
                }

    solo_sch = sorted(set(hoja) - set(bom))
    solo_bom = sorted(r for r in set(bom) - set(hoja)
                      if not r.startswith(OFFSHEET_PREFIX))

    if solo_sch:
        fallos.append(f"en el esquematico y NO en el BOM ({len(solo_sch)}): {solo_sch}")
    if solo_bom:
        fallos.append(f"en el BOM y NO en el esquematico ({len(solo_bom)}): {solo_bom}")
    if dupes:
        fallos.append(f"repetidos en el BOM ({len(dupes)}): {sorted(set(dupes))}")

    for ref in sorted(set(hoja) & set(bom), key=lambda r: (r.rstrip("0123456789"), int(r.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))):
        for campo in ("value", "footprint"):
            if hoja[ref][campo] != bom[ref][campo]:
                fallos.append(f"{ref}: {campo} en la hoja {hoja[ref][campo]!r} y en bom.csv {bom[ref][campo]!r}")

    print(f"{len(hoja)} componentes en la hoja, {len(bom)} designadores en el BOM, "
          f"{len(set(hoja) & set(bom))} cruzados por valor y huella")

    if fallos:
        print(f"\nFALLO: {len(fallos)} discrepancias")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print("OK: check_bom v5 -- designadores, valores y huellas iguales en la hoja y en el BOM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
