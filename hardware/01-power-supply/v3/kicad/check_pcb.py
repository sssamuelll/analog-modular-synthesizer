"""Puerta: la placa COMMITEADA cumple las reglas de colocacion y ruteo.

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


def leer_ruteo(board) -> tuple[list[tuple], list[tuple]]:
    '''Traduce el cobre guardado al contrato TRACKS/VIAS de los revisores.

    Cada segmento se conserva por separado. Un arco no se aproxima por su
    cuerda: si aparece, la puerta se detiene hasta que exista una lectura que
    preserve su geometria real.
    '''
    if board.GetCopperLayerCount() != 2:
        raise AssertionError('leer_ruteo solo admite placas de dos capas')
    for zona in board.Zones():
        if not zona.GetIsRuleArea() and zona.GetNetname() == 'GND':
            raise AssertionError('zona GND no soportada por la regla de tramos')
    for dibujo in board.GetDrawings():
        if dibujo.GetLayer() in {pcbnew.F_Cu, pcbnew.B_Cu}:
            raise AssertionError('shape grafico en cobre no soportado')

    tracks, vias = [], []
    for cobre in board.GetTracks():
        if isinstance(cobre, pcbnew.PCB_VIA):
            if cobre.GetViaType() != pcbnew.VIATYPE_THROUGH:
                raise AssertionError('via no pasante no soportada')
            if (cobre.TopLayer() != pcbnew.F_Cu
                    or cobre.BottomLayer() != pcbnew.B_Cu):
                raise AssertionError('via fuera del par F.Cu-B.Cu')
            if not cobre.HasValidLayerPair(board.GetCopperLayerCount()):
                raise AssertionError('via con par de capas invalido')

            padstack = cobre.Padstack()
            capas = (pcbnew.F_Cu, pcbnew.B_Cu)
            tamanos = [padstack.Size(capa) for capa in capas]
            if any(
                padstack.Shape(capa) != pcbnew.PAD_SHAPE_CIRCLE
                or tamano.x != tamano.y
                for capa, tamano in zip(capas, tamanos)
            ):
                raise AssertionError('via no circular no soportada')
            if tamanos[0].x != tamanos[1].x:
                raise AssertionError('via con diametro distinto por cara')

            p = cobre.GetPosition()
            vias.append((
                p.x / 1e6,
                p.y / 1e6,
                cobre.GetNetname(),
                tamanos[0].x / 1e6,
                cobre.GetDrillValue() / 1e6,
            ))
            continue
        if isinstance(cobre, pcbnew.PCB_ARC):
            raise AssertionError(
                'la placa trae un arco de cobre que leer_ruteo no aproxima'
            )
        capa = board.GetLayerName(cobre.GetLayer())
        if capa not in {'F.Cu', 'B.Cu'}:
            raise AssertionError(f'pista en capa de cobre no soportada: {capa}')
        a, b = cobre.GetStart(), cobre.GetEnd()
        tracks.append((
            cobre.GetNetname(),
            capa,
            [(a.x / 1e6, a.y / 1e6), (b.x / 1e6, b.y / 1e6)],
            cobre.GetWidth() / 1e6,
        ))
    return tracks, vias


def revisar_ruteo(board) -> list[str]:
    '''Las cuatro reglas de ruteo sobre el cobre que trae board.'''
    bp.TRACKS, bp.VIAS = leer_ruteo(board)
    fallos = [f'cruce: {x}' for x in bp.revisar_pistas()]
    fallos += [f'masa: {x}' for x in bp.revisar_estrella()]
    fallos += [f'pista sobre pad: {x}' for x in bp.revisar_pista_pad(board)]
    fallos += [f'via: {x}' for x in bp.revisar_vias(board)]
    fallos += [f'munon: {x}' for x in bp.revisar_cobre_muerto(board)]
    return fallos


def conexiones_sin_rutear(board) -> int:
    '''Ratsnest real que queda en el PCB guardado.'''
    conectividad = board.GetConnectivity()
    conectividad.RecalculateRatsnest()
    return conectividad.GetUnconnectedCount(False)


def main() -> int:
    if not os.path.exists(PCB):
        print("HUECO: falta sam17-power-v3.kicad_pcb -- correr build_pcb.py")
        # Codigo 2, no 0: gates.py lee el codigo de salida, no la prosa.
        return 2
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

    # Las cinco puertas de RUTEO miden el cobre que se fabrica: el guardado
    # en la placa commiteada. Regenerarlo aqui tardaba 228,8 s medidos (#139)
    # y, peor, juzgaba una intencion nueva en vez del artefacto que esta
    # puerta dice vigilar: una pista arrastrada a mano en la GUI no la veia
    # NADIE, porque el ruteo que se comprobaba era el que el script acababa
    # de calcular.
    #
    # El generador conserva su propia certificacion en build_pcb.py, que
    # asevera lo mismo sobre lo que acaba de trazar. Pero build_pcb.py no lo
    # corre ninguna puerta: si rutear() se rompe, no hay rojo hasta que
    # alguien regenere. Queda escrito porque es el precio de este cambio.
    # leer_ruteo() se planta cuando el cobre trae algo que no sabe
    # representar (un arco, una zona de GND, una via no pasante). Eso NO es un
    # fallo de la placa: es la puerta diciendo que no puede medir. Sale como
    # HUECO -- codigo 2, con el motivo escrito, la convencion de gates.py --
    # en vez de reventar con un traceback que el resumen no sabe clasificar.
    try:
        fallos += revisar_ruteo(board)
    except AssertionError as exc:
        print(f"HUECO: la puerta no sabe leer este cobre -- {exc}")
        return 2

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
    sin_rutear = conexiones_sin_rutear(board)
    print(f"  ruteo: {sum(len(t[2]) - 1 for t in bp.TRACKS)} segmentos y "
          f"{len(bp.VIAS)} vias; quedan {sin_rutear} "
          f"conexiones sin rutear")
    if sin_rutear:
        fallos.append(f"ruteo: quedan {sin_rutear} conexiones sin rutear")

    if fallos:
        print(f"\nFALLO: {len(fallos)} en la placa")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\nOK: colocacion, ruteo guardado, barrera de red, isla de "
          "referencia,\n    diagonal del lazo y los tres tabs contra la pared "
          "del chasis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
