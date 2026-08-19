"""Puerta: la placa COMMITEADA cumple las reglas de colocacion.

    python check_pcb.py        # sale != 0 si el .kicad_pcb no cumple

Por que existe, y por que no basta con build_pcb.py. Aquel GENERA la placa y
comprueba lo que acaba de generar: si sus asserts pasan, es porque el
PLACEMENT del propio fichero es coherente consigo mismo. Esta lee el
`.kicad_pcb` que esta en git, que es otra cosa distinta -- y la diferencia
importa por tres motivos:

  * KiCad se abre a mano. Mover una pieza en la GUI y guardar no toca
    build_pcb.py, y a partir de ahi el fichero que se manda a fabricar y el
    script que dice como se coloco no son el mismo diseno.
  * build_pcb.py necesita el Python de KiCad y nadie lo corre por gusto. Antes
    de esta puerta, TODAS sus comprobaciones -- barrera de red incluida --
    solo se ejecutaban cuando alguien se acordaba. `gates.py` ya sabia buscar
    el Python de KiCad (necesita_kicad / PY_KICAD, ahi desde hace versiones) y
    no habia un solo fichero que lo usara: ni la v1 ni la v2 tuvieron nunca la
    placa dentro de la suite.
  * Si KiCad no esta, dice HUECO con el motivo y no calla. Un skip silencioso
    consigue no correr Y que no te enteres (constitucion, Principio V).

Se importan las funciones de build_pcb.py en vez de reescribirlas: el criterio
tiene que ser UNO. Si esta puerta tuviera su propia copia de la regla de fuga,
el dia que cambie FUGA_MIN habria dos verdades y la que manda seria la que
nadie recuerda.
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power-v3.kicad_pcb")

try:
    import pcbnew
except ImportError:                                   # pragma: no cover
    print("HUECO: no hay pcbnew -- correr con el Python de KiCad")
    sys.exit(0)

sys.path.insert(0, DIR)
import build_pcb as bp                                # noqa: E402


def main() -> int:
    if not os.path.exists(PCB):
        print("HUECO: falta sam17-power-v3.kicad_pcb -- correr build_pcb.py")
        return 0
    board = pcbnew.LoadBoard(PCB)
    fallos: list[str] = []

    refs = {fp.GetReference() for fp in board.GetFootprints()}
    esperados = set(bp.PLACEMENT) | {r for r, _, _ in bp.MOUNTING}
    if faltan := esperados - refs:
        fallos.append(f"la placa no trae {sorted(faltan)}")
    if sobran := refs - esperados:
        fallos.append(f"la placa trae piezas que PLACEMENT no conoce: "
                      f"{sorted(sobran)} -- alguien las puso a mano")

    # La colocacion real contra la que declara el script. Es lo que caza una
    # pieza movida en la GUI: 0.05 mm de tolerancia, o sea nada -- son el mismo
    # numero pasado por KiCad, igual criterio que DESVIO_DXF_MAX en el case.
    for ref, (x, y, rot) in bp.PLACEMENT.items():
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            continue
        p = fp.GetPosition()
        d = max(abs(p.x / 1e6 - x), abs(p.y / 1e6 - y))
        if d > 0.05:
            fallos.append(f"{ref} esta en ({p.x/1e6:.2f}, {p.y/1e6:.2f}) y "
                          f"PLACEMENT dice ({x}, {y}): movida a mano")
        if round(fp.GetOrientationDegrees()) % 360 != rot % 360:
            fallos.append(f"{ref} esta girada {fp.GetOrientationDegrees():.0f} "
                          f"y PLACEMENT dice {rot}")

    fallos += [f"margen: {r}" for r in bp.revisar_margen(board)]
    fallos += [f"solape: {r}" for r in bp.revisar_solapes(board)]
    fallos += [f"sobre la ranura: {r}" for r in bp.revisar_sobre_ranura(board)]
    fallos += bp.revisar_smd_cara(board)
    fallos += bp.revisar_isla_referencia(board)
    fallos += bp.revisar_diagonal(board)
    fallos += bp.revisar_borde_ceramicos(board)
    fallos += bp.revisar_to220_coplanares(board)

    peor, par, pads_red, pads_selv = bp.revisar_fuga(board)
    if peor < bp.FUGA_MIN:
        fallos.append(f"la barrera de red mide {peor:.2f} mm y hacen falta "
                      f"{bp.FUGA_MIN}: entre {par[0]} y {par[1]}")

    # La tolerancia es 0.2 y no 0.05 como la de las piezas por una razon
    # tonta y real: GetBoardEdgesBoundingBox() mide el CONTORNO DIBUJADO, y esa
    # polilinea tiene grosor (0.1 mm), asi que la caja sale 0.05 mm mas grande
    # por cada lado. La placa mide 200.00; el gate leeria 200.10 para siempre.
    caja = board.GetBoardEdgesBoundingBox()
    w, h = caja.GetWidth() / 1e6, caja.GetHeight() / 1e6
    if abs(w - bp.W) > 0.2 or abs(h - bp.H) > 0.2:
        fallos.append(f"la placa mide {w:.2f} x {h:.2f} y el chasis le reserva "
                      f"{bp.W:.0f} x {bp.H:.0f}")

    print(f"{len(refs)} huellas, placa {w:.1f} x {h:.1f} mm "
          f"(hueco del chasis: {bp.W:.0f} x {bp.H:.0f})")
    print(f"  fuga red<->SELV: {peor:.2f} mm sobre {len(pads_red)} pads de red "
          f"y {len(pads_selv)} SELV (minimo {bp.FUGA_MIN})")
    print(f"  los tres TO-220 en x={[round(v, 1) for v in bp.TO220_X]}, "
          f"leidos de case/cad/params.scad")

    if fallos:
        print(f"\nFALLO: {len(fallos)} en la placa")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\nOK: colocacion, barrera de red, isla de referencia, diagonal del "
          "lazo\n    y los tres tabs contra la pared del chasis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
