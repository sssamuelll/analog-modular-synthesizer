"""Consulta en el catalogo de LCSC cada codigo de bom.csv y guarda lo que dice.

    python lcsc_snapshot.py        # necesita red; reescribe lcsc_snapshot.csv

La BOM de #474 traia 55 codigos LCSC y unos 45 eran de otra pieza: el
"SMBJ26A" era un comparador LM2903, los "fusibles" y los "SCR" amplificadores
operacionales, los "shunts de 20 mohm" electroliticos de 100 uF. JLCPCB habria
montado exactamente eso.

Este guion no decide nada: copia del catalogo (detalle de producto de LCSC) el
modelo, el fabricante, el encapsulado y el stock de cada codigo, con la fecha.
La puerta es check_lcsc.py, que compara la BOM contra este fichero sin red.
"""
from __future__ import annotations

import csv
import datetime
import json
import os
import subprocess
import sys
import time

DIR = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(DIR, "bom.csv")
SALIDA = os.path.join(DIR, "lcsc_snapshot.csv")
URL = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={}"


def consulta(codigo: str) -> dict:
    # curl y no urllib: el servidor de LCSC rechaza el User-Agent de Python.
    out = subprocess.run(["curl", "-sS", "-m", "30", "-A", "curl/8.5.0", URL.format(codigo)],
                         capture_output=True, text=True, check=True).stdout
    r = (json.loads(out).get("result") or {})
    return {"lcsc": codigo, "mpn": r.get("productModel") or "",
            "fabricante": r.get("brandNameEn") or "", "encapsulado": r.get("encapStandard") or "",
            "stock": r.get("stockNumber") if r.get("stockNumber") is not None else ""}


def main() -> int:
    codigos = []
    with open(BOM, encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            c = fila.get("lcsc", "").strip()
            if c and c not in codigos:
                codigos.append(c)
    hoy = datetime.date.today().isoformat()
    filas = []
    for c in codigos:
        d = consulta(c)
        d["fecha"] = hoy
        filas.append(d)
        print(f"  {c:<10} {d['mpn']:<28} {d['fabricante']:<22} {d['encapsulado']:<18} stock {d['stock']}")
        time.sleep(0.25)
    with open(SALIDA, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["lcsc", "mpn", "fabricante", "encapsulado", "stock", "fecha"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} codigos guardados en {os.path.basename(SALIDA)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
