"""Genera el BOM de montaje de JLCPCB: las piezas SMD que monta la maquina.

    python bom_jlc.py        # lee ../bom.csv y ../fab/sam17-power-v5-pos.csv

Que monta JLC lo decide la PLACA, no la BOM: entra cada pieza que esta en el
fichero de posiciones (kicad-cli --smd-only: las huellas con atributo SMD) y
que se compra en LCSC. Las THT (conectores, modulos, SCR, trimmers) se sueldan
a mano aunque tengan codigo LCSC, y una SMD que no esta en LCSC (el K78, PS3)
va a mano y se lista como tal. Una SMD de la placa que no esta en bom.csv es
un error: JLC dejaria sus pads vacios sin avisar.
"""
from __future__ import annotations

import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, "..", "bom.csv")
POS = os.path.join(DIR, "..", "fab", "sam17-power-v5-pos.csv")
DST = os.path.join(DIR, "..", "fab", "sam17-power-v5-bom-jlc.csv")


def smd_de_la_placa() -> set[str]:
    with open(POS, newline="", encoding="utf-8") as fh:
        return {fila["Ref"].strip() for fila in csv.DictReader(fh)}


def main() -> int:
    if not os.path.exists(POS):
        print(f"FALLO: falta {os.path.basename(POS)} -- corre build_fab.py")
        return 1
    smd = smd_de_la_placa()
    filas, a_mano, vistos = [], [], set()
    with open(SRC, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            refs = [r.strip() for r in fila["refs"].split(",") if r.strip()]
            vistos.update(refs)
            maquina = [r for r in refs if r in smd]
            if not maquina:
                continue
            if fila.get("supplier", "").strip() != "LCSC" or not fila.get("lcsc", "").strip():
                a_mano += maquina
                continue
            filas.append({"Comment": fila["value"], "Designator": ",".join(maquina),
                          "Footprint": fila["footprint"].split(":")[-1],
                          "LCSC Part #": fila["lcsc"].strip()})
    if huerfanas := sorted(smd - vistos):
        print(f"FALLO: huellas SMD de la placa que bom.csv no tiene: {huerfanas}")
        return 1
    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Comment", "Designator", "Footprint", "LCSC Part #"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    n = sum(len(f["Designator"].split(",")) for f in filas)
    print(f"{len(filas)} lineas, {n} piezas para la maquina -> {os.path.basename(DST)}")
    if a_mano:
        print(f"  SMD que NO monta JLC (no estan en LCSC, van a mano): {' '.join(sorted(a_mano))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
