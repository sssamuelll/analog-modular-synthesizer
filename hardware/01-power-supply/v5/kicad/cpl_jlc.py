"""Genera el CPL (pick&place) de JLCPCB desde el pos.csv que exporta kicad-cli."""
import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
POS = os.path.join(DIR, "..", "fab", "sam17-power-v5-pos.csv")
BOM = os.path.join(DIR, "..", "fab", "sam17-power-v5-bom-jlc.csv")
DST = os.path.join(DIR, "..", "fab", "sam17-power-v5-cpl-jlc.csv")


def main() -> int:
    if not os.path.exists(POS):
        print(f"HUECO: falta {os.path.basename(POS)} -- exportar con kicad-cli")
        return 2

    montados = []
    with open(BOM, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            montados += [d.strip() for d in row["Designator"].split(",") if d.strip()]

    por_ref = {}
    with open(POS, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            por_ref[row["Ref"].strip()] = row

    faltan = [d for d in montados if d not in por_ref]
    if faltan:
        print(f"ERROR: en el BOM pero sin posicion en el pos.csv: {faltan}")
        return 1

    def num(v: str) -> str:
        return f"{float(v):.2f}".rstrip("0").rstrip(".") or "0"

    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for ref in montados:
            r = por_ref[ref]
            w.writerow([
                ref,
                num(r["PosX"]),
                num(r["PosY"]),
                r["Side"].strip().capitalize(),
                num(r["Rot"])
            ])

    print(f"{len(montados)} designadores -> {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
