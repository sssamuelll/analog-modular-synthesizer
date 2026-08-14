"""Genera sam17-power.kicad_pcb: contorno, barrera de red, redes y colocacion.

Fuente: ../notes/design-notes.md sec.14 (dos placas, aislamiento reforzado) y
el netlist que exporta kicad-cli desde sam17-power.kicad_sch.

Uso — OJO, este script NO usa el KiCAD-MCP-Server, va con pcbnew directo, asi
que hay que llamarlo con el Python de KiCad:

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Por que sin el server, al reves que build_schematic.py: su sync_schematic_to_board
solo resuelve redes de ETIQUETAS LOCALES. De las 20 redes de esta hoja sacaba 9
y dejaba sin asignar GND, +12V, -12V, +5V y PE, que son las que vienen de
simbolos de potencia. Una placa sin GND no hay por donde rutearla. El netlist de
kicad-cli si sale completo, asi que se parsea de ahi.

Es destructivo por diseno, igual que build_schematic.py: reconstruye el .kicad_pcb
entero. El ruteo va en su propio paso (fase 3) y sobre este fichero.

Convenciones del dibujo:
  - Origen arriba-izquierda, Y crece hacia ABAJO (convenio de KiCad).
  - La placa se parte en dos zonas y la frontera es vertical:
      x < X_BARRERA   franja de red 230 V (J3 F1 RV1 NT1 J4)
      x > X_BARRERA   todo lo demas, que es SELV
    Entre las dos no cruza ningun cobre y no puede cruzarlo nunca: TR1 es
    externo (sale por J4, vuelve por J1), asi que son dos islas de verdad.
  - La ranura NO llega a los bordes: si llegara, la placa se partiria en dos.
    Quedan puentes de material arriba y abajo. La ranura es un extra; la
    garantia es la distancia de cobre a cobre, que main() MIDE y exige.
  - Los tres reguladores van en columna con el tab hacia el borde derecho, para
    que los disipadores queden todos en el mismo canto. U2 no puede compartir
    disipador con los otros dos: su tab es -Vin, no GND (sec.4 de las notas).
  - Alrededor de cada TO-220 se reserva HS_LADO x HS_LADO para el disipador. La
    huella TO-220-3_Vertical mide 10.6 x 5.0 y no incluye NADA del disipador,
    asi que si te fias del patio te los montas unos encima de otros.
"""
from __future__ import annotations

import os
import re
import sys

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power.kicad_pcb")
NET = os.path.join(DIR, "sam17-power.net")
STOCK = os.environ.get("KICAD_FOOTPRINTS",
                       r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
LOCAL = os.path.join(DIR, "sam17.pretty")

W, H = 100.0, 150.0             # placa: cabe en el tier barato de 100 mm de ancho
MARGEN = 3.0                    # de cualquier pieza al borde
X_BARRERA = 30.0                # eje de la ranura. 30 y no 25: el CUERPO de
                                # RV1 mide 22 mm y en una franja de 21 mm se
                                # montaba encima de la ranura. Los pads si
                                # cumplian — esto no lo ve la medida de cobre,
                                # lo vio el render.
RANURA_ANCHO = 2.0
RANURA_Y0, RANURA_Y1 = 12.0, 138.0   # los puentes que quedan sostienen la placa
FUGA_MIN = 6.0                  # cobre de red <-> cobre SELV (sec.14.2)
HS_LADO = 25.0                  # reserva cuadrada del disipador TO-220

# Redes del lado de red. Todo lo que no este aqui es SELV y tiene que quedar al
# otro lado de la barrera. PE entra en la lista aunque no lleve pista: su unico
# pad (J3.3) esta en la franja de red y es 230 V hasta el esparrago.
#
# Los nombres van SIN la barra que les pone el netlist a las etiquetas locales
# ("/N", "/L_F"): se normaliza al comparar. La primera version de esto compraba
# la barra sin darse cuenta, colaba L y N como SELV, y la medida de la barrera
# salia midiendo PE contra N — dos pines del MISMO bornero de red.
NETS_RED = {"L", "L_F", "L_TR", "N", "PE"}


def es_red(net: str) -> bool:
    return net.lstrip("/") in NETS_RED

# ref -> (x, y, rotacion). Medido, no estimado: ver la tabla de patios en el
# commit que introduce este fichero.
PLACEMENT = {
    # --- franja de red, columna izquierda, de arriba abajo siguiendo el
    # recorrido de la corriente: entra por J3, fusible, MOV, NTC, y sale por
    # J4 hacia el primario de TR1. Repartidos por los 150 mm en vez de
    # apelotonados arriba: asi caben los taladros de fijacion de la franja en
    # los puentes de material, con sus 6 mm de separacion al cobre de red.
    # J3 y J4 van a 180 y un Conn de bornera girada CRECE HACIA LA IZQUIERDA
    # desde su origen (que es el pin 1, no el centro): a x=14 el borde caia en
    # 0.97 mm, fuera de la placa.
    "J3":  (17.5,  24.0, 180),   # entrada de red; los bornes miran al borde
    "F1":  (15.0,  45.0,   0),
    "RV1": (10.0,  72.0,   0),   # el mas ancho de la placa: 23 mm de cuerpo
    "NT1": (12.0,  98.0,   0),
    "J4":  (16.0, 118.0, 180),   # salida al primario de TR1
    # --- entrada del secundario y rectificacion ---
    "J1":  (42.0,  10.0,   0),   # 12 VAC CT desde TR1
    "BR1": (68.0,  11.0,   0),
    # --- bulk. El punto de estrella de GND vive entre estos dos. ---
    "C1":  (45.0,  33.0,   0),
    "C2":  (67.0,  33.0,   0),
    # --- carril +12 V ---
    "C3":  (37.0,  56.0,   0),
    "D1":  (52.0,  48.0,   0),
    "U1":  (84.0,  56.0,   0),
    "C5":  (48.0,  62.0,   0),
    "C7":  (58.0,  56.0,   0),
    "R1":  (44.0,  70.0,   0),
    "D3":  (62.0,  70.0,   0),
    # --- carril +5 V (el del medio, sec.10.1) ---
    "C9":  (37.0,  88.0,   0),
    "D5":  (52.0,  80.0,   0),
    "U3":  (84.0,  88.0,   0),
    "C10": (48.0,  94.0,   0),
    "C11": (58.0,  88.0,   0),
    "R3":  (44.0, 102.0,   0),
    "D6":  (62.0, 102.0,   0),
    # --- carril -12 V ---
    "C4":  (37.0, 120.0,   0),
    "D2":  (52.0, 112.0,   0),
    "U2":  (84.0, 120.0,   0),
    "C6":  (48.0, 126.0,   0),
    "C8":  (58.0, 120.0,   0),
    "R2":  (44.0, 134.0,   0),
    "D4":  (62.0, 134.0,   0),
    # --- salidas y puente de chasis, fila de abajo ---
    "J2":  (60.0, 143.0,   0),   # bus +12/GND/GND/-12
    "J6":  (76.0, 143.0,   0),   # feed de +5 V (sec.10.4)
    "J5":  (40.0, 141.0,   0),   # faston GND -> chasis (sec.13)
}

# Los dos de la izquierda caen en los puentes de material que deja la ranura
# (fuera del tramo RANURA_Y0..RANURA_Y1), que es lo unico que sujeta la franja
# de red: sin ellos son 126 mm de tira colgando de dos puentes. Cuentan como
# SELV en la medida de la barrera — un separador metalico esta a potencial de
# chasis — asi que el propio script comprueba que no se acerquen a la red.
MOUNTING = [("H1", 11.0, 7.0), ("H2", 93.5, 7.0),
            ("H3", 11.0, 143.5), ("H4", 93.5, 143.5)]
MOUNT_D, MOUNT_PAD = 3.2, 6.0   # M3


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def leer_netlist() -> tuple[dict, dict]:
    """Del .net saca ref -> huella y (ref, pad) -> red."""
    txt = open(NET, encoding="utf-8").read()
    huellas = dict(re.findall(
        r'\(comp\s*\(ref "([^"]+)"\)[\s\S]*?\(footprint "([^"]*)"', txt))
    redes: dict[tuple[str, str], str] = {}
    for chunk in re.split(r"\(net\s*\n", txt)[1:]:
        m = re.search(r'\(name "([^"]+)"\)', chunk)
        if not m:
            continue
        for ref, pad in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', chunk):
            redes[(ref, pad)] = m.group(1)
    return huellas, redes


def contorno(board: pcbnew.BOARD) -> None:
    """Borde exterior + la ranura de la barrera, los dos en Edge.Cuts."""
    def linea(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)

    for x1, y1, x2, y2 in [(0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]:
        linea(x1, y1, x2, y2)

    a, b = X_BARRERA - RANURA_ANCHO / 2, X_BARRERA + RANURA_ANCHO / 2
    for x1, y1, x2, y2 in [(a, RANURA_Y0, b, RANURA_Y0),
                           (b, RANURA_Y0, b, RANURA_Y1),
                           (b, RANURA_Y1, a, RANURA_Y1),
                           (a, RANURA_Y1, a, RANURA_Y0)]:
        linea(x1, y1, x2, y2)


def reserva_disipadores(board: pcbnew.BOARD) -> None:
    """Marca en F.Fab el cuadrado que ocupa cada disipador.

    La huella TO-220-3_Vertical mide 10.6 x 5.0 y no dice nada del disipador,
    asi que sin esto quien monte la placa no tiene forma de saber que ese hueco
    esta pedido. Va en F.Fab y no en serigrafia porque es documentacion de
    montaje, no algo que deba salir serigrafiado sobre la pieza.
    """
    for ref in ("U1", "U2", "U3"):
        x, y, _ = PLACEMENT[ref]
        h = HS_LADO / 2
        for x1, y1, x2, y2 in [(x - h, y - h, x + h, y - h),
                               (x + h, y - h, x + h, y + h),
                               (x + h, y + h, x - h, y + h),
                               (x - h, y + h, x - h, y - h)]:
            sh = pcbnew.PCB_SHAPE(board)
            sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
            sh.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
            sh.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
            sh.SetLayer(pcbnew.F_Fab)
            sh.SetWidth(mm(0.1))
            board.Add(sh)


def reglas(board: pcbnew.BOARD) -> None:
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.25)
    ds.m_MinClearance = mm(0.25)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)


def distancia_bbox(a: pcbnew.BOX2I, b: pcbnew.BOX2I) -> float:
    """Separacion entre dos cajas, 0 si se tocan. En mm."""
    dx = max(0, max(a.GetLeft() - b.GetRight(), b.GetLeft() - a.GetRight()))
    dy = max(0, max(a.GetTop() - b.GetBottom(), b.GetTop() - a.GetBottom()))
    return (dx * dx + dy * dy) ** 0.5 / 1e6


def main() -> None:
    huellas, redes = leer_netlist()
    faltan = sorted(set(huellas) - set(PLACEMENT))
    assert not faltan, f"componentes del netlist sin sitio en PLACEMENT: {faltan}"

    board = pcbnew.NewBoard(PCB)
    contorno(board)
    reserva_disipadores(board)
    reglas(board)

    netinfo = {}
    for nombre in sorted(set(redes.values())):
        n = pcbnew.NETINFO_ITEM(board, nombre)
        board.Add(n)
        netinfo[nombre] = n

    sin_red = []
    for ref, fpid in sorted(huellas.items()):
        lib, _, name = fpid.partition(":")
        base = LOCAL if lib == "sam17" else os.path.join(STOCK, f"{lib}.pretty")
        fp = pcbnew.FootprintLoad(base, name)
        assert fp, f"no carga la huella de {ref}: {fpid}"
        x, y, rot = PLACEMENT[ref]
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        if rot:
            fp.SetOrientationDegrees(rot)
        board.Add(fp)
        for pad in fp.Pads():
            red = redes.get((ref, pad.GetNumber()))
            if red:
                pad.SetNet(netinfo[red])
            else:
                sin_red.append(f"{ref}.{pad.GetNumber()}")

    for ref, x, y in MOUNTING:
        fp = pcbnew.FootprintLoad(
            os.path.join(STOCK, "MountingHole.pretty"),
            f"MountingHole_{MOUNT_D}mm_M3_Pad")
        assert fp, "no carga la huella del taladro de fijacion"
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        for pad in fp.Pads():          # el separador va a chasis, o sea GND
            pad.SetNet(netinfo["GND"])
        board.Add(fp)

    # --- comprobaciones antes de guardar ---
    print(f"colocados {len(huellas)} componentes, {len(netinfo)} redes")
    print(f"pads sin red: {len(sin_red)} {sin_red[:8]}")

    # Que nada se salga de la placa.
    fuera = []
    for fp in board.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        if (bb.GetLeft() < mm(MARGEN) or bb.GetRight() > mm(W - MARGEN)
                or bb.GetTop() < mm(MARGEN) or bb.GetBottom() > mm(H - MARGEN)):
            fuera.append(fp.GetReference())
    print(f"piezas que se salen del margen de {MARGEN} mm: {len(fuera)} {fuera}")

    # Que dos piezas no se monten una encima de otra. A ojo no se ve: en el
    # render dos huellas solapadas parecen una sola pieza con mucha serigrafia.
    # Los TO-220 se comparan con HS_LADO, no con su patio, porque la huella no
    # sabe nada del disipador que lleva atornillado.
    cajas = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in ("U1", "U2", "U3"):
            p = fp.GetPosition()
            bb = pcbnew.BOX2I(pcbnew.VECTOR2I(p.x - mm(HS_LADO / 2),
                                              p.y - mm(HS_LADO / 2)),
                              pcbnew.VECTOR2I(mm(HS_LADO), mm(HS_LADO)))
        else:
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            if bb.GetWidth() == 0:
                bb = fp.GetBoundingBox(False, False)
        cajas.append((ref, bb))
    solapes = [f"{a}~{b}" for i, (a, ba) in enumerate(cajas)
               for b, bb in cajas[i + 1:] if distancia_bbox(ba, bb) == 0.0]
    print(f"piezas que se solapan: {len(solapes)} {solapes[:8]}")

    # Y que ninguna se monte sobre la RANURA, que no es una huella y por tanto
    # no sale en la comprobacion de arriba. J5 se colo asi: su patio pisaba el
    # extremo inferior de la ranura, o sea el faston medio en el aire.
    ranura = pcbnew.BOX2I(
        pcbnew.VECTOR2I(mm(X_BARRERA - RANURA_ANCHO / 2), mm(RANURA_Y0)),
        pcbnew.VECTOR2I(mm(RANURA_ANCHO), mm(RANURA_Y1 - RANURA_Y0)))
    sobre_ranura = [ref for ref, bb in cajas
                    if distancia_bbox(bb, ranura) == 0.0]
    print(f"piezas montadas sobre la ranura: {len(sobre_ranura)} {sobre_ranura}")

    # LA comprobacion: separacion real entre cobre de red y cobre SELV. Se mide
    # pad contra pad, no se da por buena porque la ranura este dibujada.
    pads_red, pads_selv = [], []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            n = pad.GetNetname()
            destino = pads_red if es_red(n) else pads_selv
            destino.append((f"{fp.GetReference()}.{pad.GetNumber()}[{n}]",
                            pad.GetBoundingBox()))
    peor, par = 1e9, None
    for na, ba in pads_red:
        for nb, bb in pads_selv:
            d = distancia_bbox(ba, bb)
            if d < peor:
                peor, par = d, (na, nb)
    print(f"pads de red: {len(pads_red)}, pads SELV: {len(pads_selv)}")
    print(f"separacion red<->SELV medida: {peor:.2f} mm (minimo {FUGA_MIN}) "
          f"entre {par[0]} y {par[1]}")

    pcbnew.SaveBoard(PCB, board)
    print(f"guardado {PCB}")

    assert not sin_red, f"pads sin red: {sin_red}"
    assert not fuera, f"piezas fuera del margen: {fuera}"
    assert not solapes, f"piezas montadas una encima de otra: {solapes}"
    assert not sobre_ranura, f"piezas sobre la ranura: {sobre_ranura}"
    assert peor >= FUGA_MIN, (
        f"la barrera de red mide {peor:.2f} mm y hacen falta {FUGA_MIN}: {par}")


if __name__ == "__main__":
    sys.exit(main())
