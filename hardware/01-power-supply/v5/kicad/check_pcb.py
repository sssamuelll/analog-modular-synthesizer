"""Puerta de calidad: la placa sam17-power-v5.kicad_pcb cumple colocacion, margenes y dimensiones.

    python check_pcb.py        # sale != 0 si el .kicad_pcb no cumple
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power-v5.kicad_pcb")

try:
    import pcbnew
except ImportError:
    print("HUECO: no hay pcbnew -- correr con el Python de KiCad")
    sys.exit(2)

sys.path.insert(0, DIR)
import build_pcb as bp  # noqa: E402


def main() -> int:
    if not os.path.exists(PCB):
        print(f"HUECO: falta {os.path.basename(PCB)} -- correr build_pcb.py")
        return 2

    board = pcbnew.LoadBoard(PCB)
    fallos: list[str] = []

    # 1. Comprobar presencia de todas las huellas
    refs = {fp.GetReference() for fp in board.GetFootprints()}
    esperados = set(bp.PLACEMENT) | {r for r, _, _ in bp.MOUNTING}
    if faltan := esperados - refs:
        fallos.append(f"la placa no contiene {sorted(faltan)}")
    if sobran := refs - esperados:
        fallos.append(f"la placa contiene piezas que PLACEMENT no conoce: {sorted(sobran)}")

    # 2. Comprobar coordenadas y rotacion contra PLACEMENT
    for ref, (x, y, rot) in bp.PLACEMENT.items():
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            continue
        p = fp.GetPosition()
        d = max(abs(p.x / 1e6 - x), abs(p.y / 1e6 - y))
        if d > 0.05:
            fallos.append(f"{ref} en ({p.x/1e6:.2f}, {p.y/1e6:.2f}) y PLACEMENT dice ({x}, {y})")
        if round(fp.GetOrientationDegrees()) % 360 != rot % 360:
            fallos.append(f"{ref} rotado {fp.GetOrientationDegrees():.0f} deg y PLACEMENT dice {rot}")

    # 3. Comprobar taladros mecanicos de fijacion H1..H4
    for ref, x, y in bp.MOUNTING:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            continue
        p = fp.GetPosition()
        d = max(abs(p.x / 1e6 - x), abs(p.y / 1e6 - y))
        if d > 0.05:
            fallos.append(f"taladro {ref} en ({p.x/1e6:.2f}, {p.y/1e6:.2f}) y MOUNTING dice ({x}, {y})")

    # 4. Comprobar dimensiones de la placa contra Eurocard 200 x 150 mm
    caja = board.GetBoardEdgesBoundingBox()
    w, h = caja.GetWidth() / 1e6, caja.GetHeight() / 1e6
    if abs(w - bp.W) > 0.25 or abs(h - bp.H) > 0.25:
        fallos.append(f"la placa mide {w:.2f} x {h:.2f} mm y deberia medir {bp.W:.0f} x {bp.H:.0f} mm")

    # 5. Comprobar margenes al borde
    fuera = []
    for fp in board.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        if (bb.GetLeft() < bp.mm(bp.MARGEN) or bb.GetRight() > bp.mm(bp.W - bp.MARGEN)
                or bb.GetTop() < bp.mm(bp.MARGEN) or bb.GetBottom() > bp.mm(bp.H - bp.MARGEN)):
            fuera.append(fp.GetReference())
    if fuera:
        fallos.append(f"componentes fuera del margen de {bp.MARGEN} mm: {sorted(fuera)}")

    # 6. Comprobar solapes de bounding boxes entre componentes electricos
    solapes = []
    fps = [board.FindFootprintByReference(r) for r in bp.PLACEMENT]
    for i in range(len(fps)):
        for j in range(i + 1, len(fps)):
            fa, fb = fps[i], fps[j]
            if fa is None or fb is None:
                continue
            ba = fa.GetBoundingBox(False, False)
            bb = fb.GetBoundingBox(False, False)
            if ba.Intersects(bb):
                solapes.append(f"{fa.GetReference()} <-> {fb.GetReference()}")
    if solapes:
        fallos.append(f"solapes de bounding box ({len(solapes)}): {solapes[:5]}")

    # 7. Comprobar zonas de masa
    zonas = {z.GetNetname() for z in board.Zones()}
    for z_esp in ("GNDA", "GNDD"):
        if z_esp not in zonas:
            fallos.append(f"falta zona de masa {z_esp} en la placa")

    print(f"{len(refs)} huellas en placa {w:.1f} x {h:.1f} mm (margen {bp.MARGEN} mm)")
    print(f"  Zonas detectadas: {sorted(zonas)}")

    if fallos:
        print(f"\nFALLO: {len(fallos)} discrepancias en la placa")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print("\nOK: check_pcb v5 -- colocacion, margenes, taladros y contorno en verde")
    return 0


if __name__ == "__main__":
    sys.exit(main())
