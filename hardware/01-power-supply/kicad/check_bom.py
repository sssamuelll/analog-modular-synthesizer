"""Cruza bom.csv contra los designadores reales del esquematico.

    python check_bom.py        # sale con codigo != 0 si no cuadran

Existe porque este cruce ya se pudrio una vez sin que nadie se enterase: el BOM
pedia un bornero de 2 posiciones para la entrada del transformador cuando el
esquematico lleva uno de 3 (el secundario es de toma central, son tres hilos), y
pedia tres resistencias de 2.2k cuando la del riel de +5V es de 680R. Los dos se
descubrieron a mano, leyendo. Esto lo hace solo.

No necesita el KiCAD-MCP-Server: lee el .kicad_sch en crudo. La columna `refs`
del BOM lleva los designadores separados por coma; un "—" marca las lineas que
son mecanicas o van fuera de la hoja (disipadores, zocalos, herrajes de tierra)
y esas se ignoran a proposito.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(DIR, "sam17-power.kicad_sch")
BOM = os.path.join(DIR, "..", "bom.csv")

# Solo instancias: el prefijo pelado ("J", "C", "U") es el de lib_symbols, y los
# simbolos virtuales de potencia empiezan por "#".
INSTANCE = re.compile(r'\(property "Reference" "([A-Z]+\d+)"')

# Prefijos reservados a piezas que son del modulo pero no del circuito, asi que
# nunca tienen simbolo en la hoja: TR transformador (externo, entra por J4 y
# vuelve por J1), HS disipadores, XU zocalos de TO-220.
OFFSHEET_PREFIX = ("TR", "HS", "XU")


def main() -> int:
    with open(SCH, encoding="utf-8") as fh:
        sheet = set(INSTANCE.findall(fh.read()))

    bom: dict[str, str] = {}
    dupes = []
    with open(BOM, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            for ref in (r.strip() for r in row["refs"].split(",")):
                if not ref or ref == "—":
                    continue
                if ref in bom:
                    dupes.append(ref)
                bom[ref] = row["value"]

    solo_sch = sorted(sheet - set(bom))
    solo_bom = sorted(r for r in set(bom) - sheet
                      if not r.startswith(OFFSHEET_PREFIX))

    for label, items in [("en el esquematico y NO en el BOM", solo_sch),
                         ("en el BOM y NO en el esquematico", solo_bom),
                         ("repetidos en el BOM", sorted(set(dupes)))]:
        print(f"{label}: {len(items)} {items}")

    ok = not (solo_sch or solo_bom or dupes)
    print(f"{len(sheet)} componentes en la hoja, {len(bom)} designadores en el BOM"
          f" -> {'OK' if ok else 'NO CUADRA'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
