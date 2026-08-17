"""Genera el BOM de ensamblaje JLCPCB desde bom.csv (filas con codigo LCSC)."""
import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, "..", "bom.csv")
DST = os.path.join(DIR, "..", "fab", "sam17-power-v2-bom-jlc.csv")


def main() -> int:
    filas = []
    with open(SRC, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("lcsc", "").strip():
                filas.append({"Comment": row["value"], "Designator": row["refs"],
                              "Footprint": row["footprint"], "LCSC Part #": row["lcsc"]})
    if not filas:
        print("ninguna fila con codigo LCSC")
        return 1
    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Comment", "Designator", "Footprint", "LCSC Part #"])
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} lineas -> {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
