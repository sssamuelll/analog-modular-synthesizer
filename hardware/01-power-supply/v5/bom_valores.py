"""Lee de bom.csv el valor de un designador, en unidades SI.

    from bom_valores import valor
    valor("L2")   # 2.2e-05
    valor("R36")  # 3900.0

Existe para que los presupuestos y las puertas de la v5 calculen con LAS PIEZAS
DE LA PLACA y no con una copia de sus valores. En #474 el modelo RK4 de #334
simulaba un LC de 22 uH / 47 uF / 220 uF + 0,68 ohm y la BOM montaba
10 uH / 22 uF / 47 uF + 0,5 ohm: el modelo daba 18,05 V en U1 y las piezas
reales 21,0 V, por encima de su maximo absoluto. Nadie lo vio porque los dos
numeros vivian en sitios distintos.
"""
from __future__ import annotations

import csv
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(DIR, "bom.csv")

_SUFIJO = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3,
           "k": 1e3, "K": 1e3, "M": 1e6, "": 1.0}


def filas() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with open(BOM, encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            for ref in (r.strip() for r in fila["refs"].split(",")):
                if ref:
                    out[ref] = fila
    return out


def a_si(texto: str) -> float:
    """'120k 0.1%' -> 120000.0; '22uH SRR1260-220M' -> 2.2e-05; '0.68' -> 0.68."""
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*([pnuµmkKM]?)", texto)
    if not m:
        raise ValueError(f"no se puede leer un valor de {texto!r}")
    return float(m.group(1)) * _SUFIJO[m.group(2)]


def valor(ref: str) -> float:
    f = filas()
    if ref not in f:
        raise KeyError(f"{ref} no esta en bom.csv")
    return a_si(f[ref]["value"])


def paralelo(*refs: str) -> float:
    return 1.0 / sum(1.0 / valor(r) for r in refs)
