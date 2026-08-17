"""Genera el CPL (pick&place) de JLCPCB desde el pos.csv que exporta kicad-cli.

Mismo problema y misma solucion que en la fuente v2
(`hardware/01-power-supply/v2/kicad/cpl_jlc.py`, de donde sale este): subir el
pos.csv crudo falla con "Failed processing the CPL file" porque `kicad-cli pcb
export pos` escribe las cabeceras de KiCad (`Ref,Val,Package,PosX,PosY,Rot,
Side`) y JLCPCB espera las suyas (`Designator,Mid X,Mid Y,Layer,Rotation`),
con Layer capitalizado, coordenadas de 2 decimales y rotacion sin decimales.
Comprobado contra un pedido real el 2026-08-17.

Diferencia con el de la fuente: aqui el pos.csv YA se exporto con --smd-only,
asi que no trae los through-hole. El filtro contra el BOM se mantiene igual
porque sigue siendo la comprobacion util -- cruza las dos listas y grita si
una pieza del BOM no tiene posicion, que es el fallo que la fabrica descubre
tarde y caro.
"""
import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
POS = os.path.join(DIR, "..", "pcb", "sam17-vco-pos.csv")
BOM = os.path.join(DIR, "..", "pcb", "sam17-vco-bom.csv")
DST = os.path.join(DIR, "..", "pcb", "sam17-vco-cpl-jlc.csv")


def main() -> int:
    montados = []
    with open(BOM, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            montados += [d.strip() for d in row["Designator"].split(",")]

    por_ref = {}
    with open(POS, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            por_ref[row["Ref"].strip()] = row

    faltan = [d for d in montados if d not in por_ref]
    if faltan:
        print(f"ERROR: en el BOM pero sin posicion en el pos.csv: {faltan}")
        return 1

    # Al reves tambien importa: una huella SMD colocada que nadie declaro en
    # el BOM es un pad que la maquina deja vacio sin avisar.
    sobran = [r for r in por_ref if r not in set(montados)]
    if sobran:
        print(f"ERROR: en el pos.csv pero sin linea de BOM: {sobran}")
        return 1

    def num(v: str) -> str:
        return f"{float(v):.2f}".rstrip("0").rstrip(".") or "0"

    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for ref in montados:
            r = por_ref[ref]
            w.writerow([ref, num(r["PosX"]), num(r["PosY"]),
                        r["Side"].strip().capitalize(), num(r["Rot"])])

    print(f"{len(montados)} designadores -> {os.path.normpath(DST)}")
    girados = sorted({por_ref[d]["Rot"] for d in montados}
                     - {"0.000000", "0.0", "0"})
    print(f"rotaciones presentes ademas de 0: {girados or 'ninguna'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
