"""Completa la emision de OpenSCAD 2021.01: reescribe INSUNITS=6 (metros) a 4 (mm).

    python case/fix_dxf_units.py

OpenSCAD 2021.01 estampa $INSUNITS=6 (metros en DXF spec) aunque el contenido
esta en mm. Un consumer que honra el header los escala x1000, rompiendo el corte.
Este script reescribe todos los DXF a INSUNITS=4 (mm), completando la emision
del CAD. Corre ENTRE los exports y check_dxf, ANTES de mandar a cortar.
"""
from __future__ import annotations

import sys
from pathlib import Path

import ezdxf

PLANS = Path(__file__).parent / "plans"


def main() -> int:
    fallos: list[str] = []
    for dxf_path in sorted(PLANS.glob("*.dxf")):
        try:
            doc = ezdxf.readfile(str(dxf_path))
            ins_antes = doc.header.get("$INSUNITS", 0)
            # Reescribe a 4 (mm) si es 6 (metros, OpenSCAD quirk) o si esta ausente
            if ins_antes != 4:
                doc.header["$INSUNITS"] = 4
                doc.save()
                print(f"  {dxf_path.name}: INSUNITS {ins_antes} -> 4")
            else:
                print(f"  {dxf_path.name}: ya 4")
        except Exception as e:
            fallos.append(f"{dxf_path.name}: {e}")
            print(f"ROJO: {dxf_path.name}: {e}")
    if fallos:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
