"""Genera el BOM de ensamblaje JLCPCB desde bom.csv (filas con codigo LCSC)."""
import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, "..", "bom.csv")
DST = os.path.join(DIR, "..", "fab", "sam17-power-v5-bom-jlc.csv")


def main() -> int:
    por_codigo: dict[str, dict] = {}
    with open(SRC, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            code = row.get("lcsc", "").strip()
            if not code or code == "—":
                continue
            if code in por_codigo:
                por_codigo[code]["Designator"] += "," + row["refs"]
            else:
                por_codigo[code] = {
                    "Comment": row["value"],
                    "Designator": row["refs"],
                    "Footprint": row["footprint"],
                    "LCSC Part #": code
                }
    filas = list(por_codigo.values())
    if not filas:
        print("ninguna fila con codigo LCSC")
        return 1
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Comment", "Designator", "Footprint", "LCSC Part #"])
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} lineas -> {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
