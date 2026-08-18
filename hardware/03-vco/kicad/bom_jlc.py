"""Genera el BOM de ensamblaje JLCPCB desde pcb/sam17-vco-bom.csv.

Hermano del de la fuente v2 (`hardware/01-power-supply/v2/kicad/bom_jlc.py`),
con una diferencia de fuente: alli el origen es el bom.csv maestro y aqui es
el BOM de ensamblaje, que ya viene filtrado a lo que la maquina coloca (las
111 huellas SMD) y lleva la columna `LCSC Part#`.

Lo importante que se hereda: UNA FILA POR CODIGO LCSC, no por fila del CSV.
El BOM de origen parte la misma pieza en varias filas cuando la nota difiere
-- los 10uF salen en dos (bulk de riel y acoplos de seno) y los 49.9k en dos
(R_CVIN y R_MIX) -- y JLCPCB espera un renglon por part number con los
designadores juntos: codigos repetidos en renglones distintos los marca como
duplicados al subir. Se conserva el orden de primera aparicion.
"""
import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, "..", "pcb", "sam17-vco-bom.csv")
DST = os.path.join(DIR, "..", "pcb", "sam17-vco-bom-jlc.csv")


def main() -> int:
    por_codigo: dict[str, dict] = {}
    sin_codigo = []
    with open(SRC, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            code = row.get("LCSC Part#", "").strip()
            if not code.startswith("C") or not code[1:].isdigit():
                sin_codigo.append(f'{row["Designator"].split(",")[0]} '
                                  f'({row["Value"]}) -> {code or "vacio"}')
                continue
            if code in por_codigo:
                por_codigo[code]["Designator"] += "," + row["Designator"]
            else:
                por_codigo[code] = {"Comment": row["Value"],
                                    "Designator": row["Designator"],
                                    "Footprint": row["Footprint"],
                                    "LCSC Part #": code}

    if sin_codigo:
        print("ERROR: filas sin codigo LCSC valido, el BOM no esta cerrado:")
        for s in sin_codigo:
            print("  -", s)
        return 1

    filas = list(por_codigo.values())
    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Comment", "Designator",
                                           "Footprint", "LCSC Part #"])
        w.writeheader()
        w.writerows(filas)

    refs = sum(len(f["Designator"].split(",")) for f in filas)
    print(f"{len(filas)} lineas / {refs} designadores -> "
          f"{os.path.normpath(DST)}")
    fusionadas = [(c, f["Comment"]) for c, f in por_codigo.items()
                  if f["Designator"].count(",") + 1 > 0
                  and sum(1 for r in csv.DictReader(
                      open(SRC, newline="", encoding="utf-8"))
                      if r["LCSC Part#"].strip() == c) > 1]
    print(f"codigos que venian en mas de una fila y se fusionaron: "
          f"{fusionadas or 'ninguno'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
