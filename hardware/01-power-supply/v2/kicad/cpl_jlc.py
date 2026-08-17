"""Genera el CPL (pick&place) de JLCPCB desde el pos.csv que exporta kicad-cli.

Por que hace falta un paso extra: `kicad-cli pcb export pos` escribe las
cabeceras de KiCad (`Ref,Val,Package,PosX,PosY,Rot,Side`) y JLCPCB espera las
suyas (`Designator,Mid X,Mid Y,Layer,Rotation`). Subir el pos.csv crudo falla
con "Failed processing the CPL file" -- comprobado en el pedido del
2026-08-17, con el BOM aceptado en la misma pantalla.

Ademas se filtra a los designadores que estan en el BOM de ensamblaje: el CPL
solo tiene sentido para lo que monta la maquina. Los 44 THT del pos.csv no
pintan nada ahi.
"""
import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
POS = os.path.join(DIR, "..", "fab", "sam17-power-v2-pos.csv")
BOM = os.path.join(DIR, "..", "fab", "sam17-power-v2-bom-jlc.csv")
DST = os.path.join(DIR, "..", "fab", "sam17-power-v2-cpl-jlc.csv")


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

    # Formato exacto del sample de JLC: Layer capitalizado ("Top"/"Bottom"),
    # coordenadas en mm con 2 decimales y sin sufijo, rotacion en grados sin
    # decimales. El pos.csv de KiCad trae "top" y 6 decimales, y con eso el
    # parser de JLC devuelve "File processing failed" sin mas detalle.
    def num(v: str) -> str:
        return f"{float(v):.2f}".rstrip("0").rstrip(".") or "0"

    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for ref in montados:
            r = por_ref[ref]
            w.writerow([ref, num(r["PosX"]), num(r["PosY"]),
                        r["Side"].strip().capitalize(), num(r["Rot"])])

    print(f"{len(montados)} designadores -> {DST}")
    girados = [(d, por_ref[d]["Rot"]) for d in montados
               if float(por_ref[d]["Rot"]) != 0.0]
    print(f"con rotacion != 0: {girados if girados else 'ninguno'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
