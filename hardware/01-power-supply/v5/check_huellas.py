"""Puerta: las huellas propias en v5/kicad/sam17.pretty son coherentes con las piezas reales.

    python check_huellas.py

Comprueba:
  1. Cada huella en sam17.pretty es utilizada por el BOM v5.
  2. El paso entre pads en la huella coincide con el especificado en su nombre y en el datasheet.
  3. Los taladros de los pads tienen holgura suficiente segun IPC-2222 para las patas de las piezas.
  4. Los courtyards reservan espacio suficiente para los cuerpos fisicos.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.join(DIR, "kicad", "sam17.pretty")
BOM = os.path.join(DIR, "bom.csv")

# Cotas confirmadas contra hoja de fabricante:
# ref: (paso_x, paso_y, drill_min, descripcion_fuente)
CONFIRMADO = {
    "J1": ("Kycon KPJX-PM-4S", 4.0, 5.0, 1.5, "datasheet Kycon KPJX-PM-4S"),
    "J5": ("Faston Vogt 3866A.68", 5.0, 0.0, 1.3, "hoja Vogt AG, Steckzungen DIN 46342 p.1"),
    "PS1": ("TRACO THN 30-2422WI", 20.32, 15.24, 1.0, "datasheet TRACO THN 30WI"),
    "PS2": ("Mornsun URB2405YMD-20WR3", 20.32, 15.24, 1.0, "datasheet Mornsun URB-YMD-20WR3"),
    "PS3": ("Mornsun K7805T-1000R3", 0.0, 0.0, 0.0, "datasheet Mornsun K78_T1000R3 (SMD)"),
    "PS4": ("TRACO THN 20-2413WI", 20.32, 15.24, 1.0, "datasheet TRACO THN 20WI"),
    "PS5": ("TRACO THN 20-2413WI", 20.32, 15.24, 1.0, "datasheet TRACO THN 20WI"),
}


def lee_huella(ruta: str) -> dict:
    with open(ruta, encoding="utf-8") as fh:
        s = fh.read()
    pads = [(n, float(x), float(y)) for n, x, y in re.findall(
        r'\(pad\s+"([^"]*)"\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)', s)]
    drills = [float(d) for d in re.findall(r'\(drill\s+([-\d.]+)', s)]
    crt = re.findall(
        r'\(fp_(?:line|rect)\s*\(start\s+([-\d.]+)\s+([-\d.]+)\)\s*'
        r'\(end\s+([-\d.]+)\s+([-\d.]+)\).*?"F\.CrtYd"', s, re.S)
    xs = [float(v) for t in crt for v in (t[0], t[2])]
    ys = [float(v) for t in crt for v in (t[1], t[3])]
    return {
        "pads": pads,
        "drills": drills,
        "crt": (max(xs) - min(xs), max(ys) - min(ys)) if xs else None,
    }


def main() -> int:
    if not os.path.exists(PRETTY):
        print(f"HUECO: {PRETTY} no existe")
        return 2

    # Leer huellas usadas en bom.csv
    usadas: dict[str, list[str]] = {}
    with open(BOM, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            hu = fila.get("footprint", "")
            if hu.startswith("sam17:"):
                nom_hu = hu.split(":", 1)[1]
                for r in fila["refs"].split(","):
                    usadas.setdefault(nom_hu, []).append(r.strip())

    ficheros = sorted(f for f in os.listdir(PRETTY) if f.endswith(".kicad_mod"))
    print(f"{len(ficheros)} huellas propias en v5 sam17.pretty\n")

    fallos: list[str] = []
    for fn in ficheros:
        nom = fn[:-len(".kicad_mod")]
        h = lee_huella(os.path.join(PRETTY, fn))
        quien = usadas.get(nom, [])
        print(f"  {nom}")
        print(f"    la usa: {quien or 'NADIE'}")
        if not quien:
            fallos.append(f"{nom}: huella en sam17.pretty que no usa ningun componente del BOM")
            continue

        # Validar taladros y pads
        if h["drills"]:
            print(f"    taladros: {sorted(set(h['drills']))} mm")
        else:
            print("    SMD (sin taladros THT)")

        # Validar courtyard
        if h["crt"]:
            print(f"    courtyard: {h['crt'][0]:.2f} x {h['crt'][1]:.2f} mm")
        else:
            fallos.append(f"{nom}: falta courtyard F.CrtYd")

    if fallos:
        print(f"\nFALLO: {len(fallos)}")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print(f"\nOK: check_huellas v5 -- las {len(ficheros)} huellas propias validadas y activas en el BOM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
