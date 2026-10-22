"""Genera las huellas propias de los modulos Mornsun de la fuente v5.

    python build_huellas.py

Las que habia (#474) eran una sola huella generica de 6 pines repetida para el
URB y los dos TRACO -- que no se parecen entre si -- y un K78 de 3 pads en
linea cuando la pieza es un SMD de 8 pines en dos filas. Aqui las cotas salen
del plano de cada hoja, escritas en una tabla con su pagina; check_huellas.py
las vuelve a leer del .kicad_mod y las compara con la misma hoja.

Los TRACO THN 20WI/30WI no estan aqui: son el 1x1 pulgada estandar de TRACO y
KiCad ya trae esa huella (Converter_DCDC_TRACO_THL30-xxxxWI_THT, mismos seis
pines en las mismas cotas que la p. 4/5 de sus hojas).
"""
from __future__ import annotations

import os
import uuid

DIR = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.join(DIR, "sam17.pretty")
DS = "docs/reference/datasheets"

# Mornsun URB_YMD-20WR3, encapsulado horizontal sin disipador.
# mornsun_urb_ymd20wr3.pdf p. 6, "Top View (PCB Layout)": rejilla de 2.54 mm,
# taladro recomendado 1.50 mm, patilla de 1.00 mm. Origen en el pin 1.
URB = {
    "nombre": "Converter_DCDC_Mornsun_URB_YMD-20WR3_Horizontal_THT",
    "hoja": f"{DS}/mornsun_urb_ymd20wr3.pdf p. 6",
    "taladro": 1.5, "pad": 2.6,
    "pines": {"1": (0.0, 0.0), "2": (0.0, 7.62), "3": (0.0, 12.70),
              "6": (20.32, 0.0), "5": (20.32, 10.16), "4": (20.32, 20.32)},
    # Caja de 25.40 x 25.40 con los pines a 2.54 del borde.
    "cuerpo": (-2.54, -2.54, 22.86, 22.86),
}

# Mornsun K78_T-1000R3, SMD. mornsun_k78_t1000r3.pdf p. 5, "PCB Layout":
# pads de 1.00 x 2.10 mm a paso 2.54; 12.20 mm entre los bordes exteriores de
# las dos filas -> 10.10 mm entre centros. Fila de abajo 1..5, fila de arriba
# 10 (sobre el 1), 7 (sobre el 4) y 6 (sobre el 5). Origen en el centro.
K78 = {
    "nombre": "Converter_DCDC_Mornsun_K78_T-1000R3_SMD",
    "hoja": f"{DS}/mornsun_k78_t1000r3.pdf p. 5",
    "pad_smd": (1.0, 2.1),
    "pines": {"1": (-5.08, 5.05), "2": (-2.54, 5.05), "3": (0.0, 5.05),
              "4": (2.54, 5.05), "5": (5.08, 5.05),
              "10": (-5.08, -5.05), "7": (2.54, -5.05), "6": (5.08, -5.05)},
    # Cuerpo 15.24 x 8.50 (sin patillas), centrado.
    "cuerpo": (-7.62, -4.25, 7.62, 4.25),
}


def _u() -> str:
    return str(uuid.uuid4())


def _rect(x0: float, y0: float, x1: float, y1: float, capa: str, ancho: float) -> str:
    return (f'  (fp_rect (start {x0:g} {y0:g}) (end {x1:g} {y1:g}) '
            f'(stroke (width {ancho:g}) (type default)) (fill none) '
            f'(layer "{capa}") (uuid "{_u()}"))')


def _cabecera(nombre: str, descr: str, tags: str, ref_y: float, val_y: float) -> list[str]:
    return [f'(footprint "{nombre}"', "  (version 20241229)",
            '  (generator "sam17-build_huellas")', '  (generator_version "10.0")',
            '  (layer "F.Cu")', f'  (descr "{descr}")', f'  (tags "{tags}")',
            f'  (property "Reference" "REF**" (at 0 {ref_y:g} 0) (layer "F.SilkS") '
            f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))',
            f'  (property "Value" "{nombre}" (at 0 {val_y:g} 0) (layer "F.Fab") '
            f'(uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))']


def urb() -> str:
    d = URB
    x0, y0, x1, y1 = d["cuerpo"]
    out = _cabecera(d["nombre"],
                    f"Mornsun URB_YMD-20WR3 horizontal, 1x1 pulgada, {d['hoja']}",
                    "DC-DC Mornsun URB isolated THT", y0 - 1.5, y1 + 1.5)
    out.append('  (attr through_hole)')
    out.append(_rect(x0, y0, x1, y1, "F.Fab", 0.1))
    out.append(_rect(x0 - 0.12, y0 - 0.12, x1 + 0.12, y1 + 0.12, "F.SilkS", 0.12))
    out.append(_rect(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5, "F.CrtYd", 0.05))
    for num, (x, y) in d["pines"].items():
        forma = "rect" if num == "1" else "circle"
        out.append(f'  (pad "{num}" thru_hole {forma} (at {x:g} {y:g}) '
                   f'(size {d["pad"]:g} {d["pad"]:g}) (drill {d["taladro"]:g}) '
                   f'(layers "*.Cu" "*.Mask") (uuid "{_u()}"))')
    out.append(")")
    return "\n".join(out) + "\n"


def k78() -> str:
    d = K78
    x0, y0, x1, y1 = d["cuerpo"]
    w, h = d["pad_smd"]
    out = _cabecera(d["nombre"],
                    f"Mornsun K78_T-1000R3 SMD, 8 pads en dos filas, {d['hoja']}",
                    "DC-DC Mornsun K78 SMD buck", -7.6, 7.6)
    out.append('  (attr smd)')
    out.append(_rect(x0, y0, x1, y1, "F.Fab", 0.1))
    out.append(_rect(x0 - 0.12, y0 - 0.12, x1 + 0.12, y1 + 0.12, "F.SilkS", 0.12))
    out.append(_rect(x0 - 0.5, -6.6, x1 + 0.5, 6.6, "F.CrtYd", 0.05))
    # Marca del pin 1 en serigrafia, fuera del pad.
    out.append(f'  (fp_circle (center -7.0 6.3) (end -6.8 6.3) (stroke (width 0.2) '
               f'(type default)) (fill solid) (layer "F.SilkS") (uuid "{_u()}"))')
    for num, (x, y) in d["pines"].items():
        out.append(f'  (pad "{num}" smd rect (at {x:g} {y:g}) (size {w:g} {h:g}) '
                   f'(layers "F.Cu" "F.Paste" "F.Mask") (uuid "{_u()}"))')
    out.append(")")
    return "\n".join(out) + "\n"


def main() -> int:
    for d, texto in ((URB, urb()), (K78, k78())):
        ruta = os.path.join(PRETTY, d["nombre"] + ".kicad_mod")
        with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)
        print(f"escrita {os.path.basename(ruta)} ({len(d['pines'])} pads)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
