"""Puerta: cada codigo LCSC de bom.csv es la pieza que la BOM dice que es.

    python check_lcsc.py        # 0 verde, 1 rojo; sin red

Compara bom.csv con lcsc_snapshot.csv, que es lo que el catalogo de LCSC
devolvio para cada codigo (lo escribe lcsc_snapshot.py). Rojo si:

  * una linea que se compra en LCSC no tiene codigo;
  * un codigo no esta en la instantanea (nadie lo ha consultado);
  * el MPN del catalogo no es el MPN de la BOM.

Es lo que habria parado la BOM de #474, donde ~45 de 55 codigos eran de otra
pieza. La instantanea lleva fecha: el stock que guarda es el de ese dia.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(DIR, "bom.csv")
FOTO = os.path.join(DIR, "lcsc_snapshot.csv")


def norm(mpn: str) -> str:
    """El catalogo y la BOM escriben el mismo MPN con y sin guiones, '#' o ','."""
    return re.sub(r"[^A-Z0-9]", "", mpn.upper())


def main() -> int:
    if not os.path.exists(FOTO):
        print("FALLO: falta lcsc_snapshot.csv -- corre lcsc_snapshot.py (necesita red)")
        return 1
    with open(FOTO, encoding="utf-8", newline="") as fh:
        foto = {f["lcsc"]: f for f in csv.DictReader(fh)}
    fallos = []
    lineas = 0
    with open(BOM, encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            codigo = fila.get("lcsc", "").strip()
            if fila.get("supplier", "").strip() == "LCSC" and not codigo:
                fallos.append(f"{fila['refs']}: se compra en LCSC y no tiene codigo")
                continue
            if not codigo:
                continue
            lineas += 1
            if codigo not in foto:
                fallos.append(f"{fila['refs']}: {codigo} no esta en lcsc_snapshot.csv")
                continue
            cat = foto[codigo]
            if norm(cat["mpn"]) != norm(fila["mpn"]):
                fallos.append(f"{fila['refs']}: {codigo} es '{cat['mpn']}' ({cat['fabricante']}) "
                              f"y la BOM dice '{fila['mpn']}'")
    fechas = sorted({f["fecha"] for f in foto.values()})
    print(f"{lineas} lineas con codigo LCSC contra la instantanea del {', '.join(fechas)}")
    if fallos:
        print(f"\nFALLO: {len(fallos)}")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("OK: check_lcsc v5 -- cada codigo es la pieza que dice la BOM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
