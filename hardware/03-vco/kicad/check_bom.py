"""Cruza bom.csv contra los designadores reales de sam17-vco.net, en los dos
sentidos: ninguna pieza sin linea de compra, ninguna linea apuntando a algo
que no existe, y las cantidades declaradas cuadran con lo que se resuelve.

    python check_bom.py

A diferencia del modulo 2 (que lee el .kicad_sch), esta hoja tiene 136
componentes y el BOM los agrupa en rangos ("U1-U4"), numeros sueltos
("C_TCAP1-4") y comodines de prefijo ("R_MIX*", "TP*") en vez de listarlos
uno a uno: hace falta un resolvedor de esos tres formatos antes de poder
cruzar nada. Se lee el .net (no la hoja) porque es lo que ya cita el netlist:
si un ref esta en el esquematico pero el exportador no lo saco (simbolo sin
pines, por ejemplo), tambien es una alarma que vale la pena que suene aqui.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(DIR, "sam17-vco.net")
BOM = os.path.join(DIR, "..", "bom.csv")

# "U1-U4" (rango con prefijo repetido), "C_TCAP1-4" (rango corto, el prefijo
# solo va en el primer lado) o "R_I2C1-2" (el prefijo lleva un digito propio,
# "I2C": por eso el prefijo se captura de forma perezosa hasta el ULTIMO
# tramo de digitos antes del guion, no con una clase de caracteres que
# excluya numeros).
RANGO = re.compile(r'^(.+?)(\d+)-[A-Za-z_]*(\d+)$')


def resolver(token: str, universo: set[str]) -> list[str]:
    """Expande un token del BOM a la lista de refs que nombra."""
    token = token.strip()
    if token.endswith("*"):
        return sorted(r for r in universo if r.startswith(token[:-1]))
    m = RANGO.match(token)
    if m:
        prefijo, ini, fin = m.groups()
        return [f"{prefijo}{i}" for i in range(int(ini), int(fin) + 1)]
    return [token]


def del_netlist() -> set[str]:
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()
    # (ref "X") aparece tanto en (components (comp (ref ...))) como colgando
    # de cada (node (ref ...) (pin ...)) de las redes; el set() ya deduplica.
    # Los simbolos de potencia (#PWR*, #FLG*) no entran al netlist con ref
    # propia -- eso ya lo resuelve kicad-cli, no hace falta filtrarlos aqui.
    return set(re.findall(r'\(ref "([^"]+)"\)', txt))


def main() -> None:
    hoja = del_netlist()

    bom: dict[str, int] = {}
    dupes: list[str] = []
    filas_qty_mal: list[str] = []
    with open(BOM, encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            resueltos: list[str] = []
            for token in fila["ref"].split():
                resueltos += resolver(token, hoja)
            for r in resueltos:
                if r in bom:
                    dupes.append(r)
                bom[r] = bom.get(r, 0) + 1
            qty = fila["quantity"].strip()
            if qty.lstrip("~").isdigit() and int(qty.lstrip("~")) != len(resueltos):
                filas_qty_mal.append(
                    f"{fila['ref']}: declara {qty}, resuelve a {len(resueltos)}")

    bom_set = set(bom)
    sin_comprar = sorted(hoja - bom_set, key=lambda r: (r[0], re.sub(r"\D", "", r) or "0"))
    inventadas = sorted(bom_set - hoja)

    for msg, lista in (
        ("en la hoja pero sin linea de compra", sin_comprar),
        ("en el BOM pero no en la hoja", inventadas),
        ("designador repetido en el BOM", sorted(set(dupes))),
        ("cantidad declarada no cuadra con los refs resueltos", filas_qty_mal),
    ):
        if lista:
            print(f"FALLO: {msg}: {lista}")

    if sin_comprar or inventadas or dupes or filas_qty_mal:
        sys.exit(1)
    print(f"OK: {len(hoja)} componentes en la hoja, {len(bom_set)} refs "
          f"resueltos del BOM, cantidades declaradas cuadran fila por fila.")


if __name__ == "__main__":
    main()
