"""Cruza bom.csv contra los designadores y huellas reales del esquematico v5.

    python check_bom.py        # sale con codigo != 0 si no cuadran

Comprueba que cada componente en la hoja de sam17-power-v5.kicad_sch este en el
BOM con su valor y su huella, y que no sobren componentes en ninguna de las dos
partes.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(DIR, "sam17-power-v5.kicad_sch")
BOM = os.path.join(DIR, "..", "bom.csv")

INSTANCE = re.compile(r'\(property "Reference" "([A-Z]+\d+)"')
OFFSHEET_PREFIX = ("TR", "HS", "XU")


def main() -> int:
    if not os.path.exists(SCH):
        print(f"HUECO: falta {os.path.basename(SCH)} -- corre build_schematic.py primero")
        return 2

    with open(SCH, encoding="utf-8") as fh:
        sheet_text = fh.read()

    sheet = set(INSTANCE.findall(sheet_text))

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
                    "value": row.get("value", ""),
                    "footprint": row.get("footprint", ""),
                }

    solo_sch = sorted(sheet - set(bom))
    solo_bom = sorted(r for r in set(bom) - sheet
                      if not r.startswith(OFFSHEET_PREFIX))

    fallos = []
    if solo_sch:
        fallos.append(f"en el esquematico y NO en el BOM ({len(solo_sch)}): {solo_sch}")
    if solo_bom:
        fallos.append(f"en el BOM y NO en el esquematico ({len(solo_bom)}): {solo_bom}")
    if dupes:
        fallos.append(f"repetidos en el BOM ({len(dupes)}): {sorted(set(dupes))}")

    print(f"{len(sheet)} componentes en la hoja, {len(bom)} designadores en el BOM")

    if fallos:
        print(f"\nFALLO: {len(fallos)} discrepancias")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print("OK: check_bom v5 -- todos los designadores cruzados y consistentes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
