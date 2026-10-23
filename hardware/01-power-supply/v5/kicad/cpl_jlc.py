"""Genera el CPL (pick & place) de JLCPCB desde el pos.csv que exporta kicad-cli.

    python cpl_jlc.py        # despues de bom_jlc.py

Una linea por designador del BOM de JLC, con la posicion y el giro que da
KiCad. El giro de algunas huellas (SOT-23, electroliticos, DFN) no coincide
con el de la biblioteca de JLC: se revisa en su visor de colocacion antes de
pagar, ver fab/README.md. No se "corrige" aqui con una tabla de memoria.
"""
from __future__ import annotations

import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
POS = os.path.join(DIR, "..", "fab", "sam17-power-v5-pos.csv")
BOM = os.path.join(DIR, "..", "fab", "sam17-power-v5-bom-jlc.csv")
DST = os.path.join(DIR, "..", "fab", "sam17-power-v5-cpl-jlc.csv")


def num(v: str) -> str:
    return f"{float(v):.2f}".rstrip("0").rstrip(".") or "0"


def main() -> int:
    for ruta in (POS, BOM):
        if not os.path.exists(ruta):
            print(f"FALLO: falta {os.path.basename(ruta)} -- corre build_fab.py")
            return 1
    montados = []
    with open(BOM, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            montados += [d.strip() for d in fila["Designator"].split(",") if d.strip()]
    with open(POS, newline="", encoding="utf-8") as fh:
        por_ref = {fila["Ref"].strip(): fila for fila in csv.DictReader(fh)}
    if faltan := [d for d in montados if d not in por_ref]:
        print(f"FALLO: en el BOM de JLC pero sin posicion en el pos.csv: {faltan}")
        return 1
    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for ref in montados:
            r = por_ref[ref]
            w.writerow([ref, num(r["PosX"]), num(r["PosY"]), r["Side"].strip().capitalize(), num(r["Rot"])])
    print(f"{len(montados)} designadores -> {os.path.basename(DST)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
