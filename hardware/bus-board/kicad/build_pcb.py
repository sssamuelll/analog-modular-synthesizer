"""Genera sam17-bus.kicad_pcb: 320 x 60 mm, 2 capas, masa en PLANO.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Va con pcbnew directo, igual que el modulo 1 y por el mismo motivo (el
sync del MCP-Server solo resuelve redes de etiquetas locales y aqui GND,
+12V y -12V vienen de simbolos de potencia). Es destructivo por diseno:
reconstruye el .kicad_pcb entero.

LA DECISION DE ESTA PLACA, en una linea: **masa es una ZONA sólida en B.Cu**.

  Con plano, el bus aporta 0.2 cents de desafinacion entre modulos. Con una
  pista de 5 mm haciendo lo mismo son 7.1 cents y el instrumento no afina
  (ground_budget.py mide las dos). No es una preferencia de estilo.

  Corolario que manda en TODO el ruteo: **nada que no sea masa baja a B.Cu**.
  Cero vias de senal. Una via de +12 V atravesando el plano le abre una
  ranura, la corriente de retorno tiene que rodearla y el plano deja de ser
  plano justo donde mas se nota. Por eso los tres rieles y los nodos locales
  van enteros por F.Cu, y revisar_capa_inferior() lo exige.

Y ojo con la contradiccion aparente contra el modulo 1, que RECHAZO el plano
(sec.7, masa en estrella): alli GND es un ARBOL con muchas ramas y un vertido
las cortocircuitaria entre si. Aqui el bus es UNA rama de esa estrella y cada
modulo cuelga de ella por un unico conector, asi que no hay bucle que crear.
Plano y estrella no se pelean: el plano vive dentro de una rama.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-bus.kicad_pcb")
NET = os.path.join(DIR, "sam17-bus.net")
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
STOCK = os.environ.get("KICAD_FOOTPRINTS",
                       r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
LOCAL = os.path.join(DIR, "sam17.pretty")

W, H = 320.0, 60.0
SLOTS_X = [26.0, 74.0, 122.0, 198.0, 246.0, 294.0]   # = ground_budget.SLOTS_X
X_FEED = 152.0
MARGEN = 2.0
ANCHO_PISTA = 0.6           # nodos locales; los rieles van por zona
Y_Z12, Y_Z12B = 2.0, 8.0    # franja de +12 V, arriba
Y_ZN, Y_ZNB = 52.0, 58.0    # franja de -12 V, abajo
# Los taladros van TODOS en la banda central (y=30) y en los huecos entre
# slots. Arriba y abajo no caben: ahi viven las dos franjas de riel, y un
# esparrago metalico en medio del vertido de +12 V seria un corto al chasis.
# Aun asi la sujecion pide **separadores de NYLON**, no metalicos: siete puntos
# de contacto entre el plano de masa y el chasis meterian corriente de chasis
# por el plano, que es justo lo que el presupuesto de masa da por supuesto que
# no pasa (notes/design-notes.md).
MOUNT = [(5.0, 30.0), (45.0, 30.0), (93.0, 30.0), (170.0, 30.0),
         (217.0, 30.0), (265.0, 30.0), (315.0, 30.0)]
MOUNT_D = 3.2

# Colocacion RELATIVA al eje del slot. El orden manda: el peine Eurorack tiene
# -12 V y +12 V a los DOS lados del bloque de masa (es el estandar Doepfer y no
# se toca), asi que se monta girado 180 para que -12 quede abajo y +12 arriba,
# alineado con las dos franjas. Puesto del otro lado, cada slot obligaria a
# cruzar +12S por encima de -12S y, sin poder bajar a B.Cu, no hay por donde.
REL = {
    # F- va GIRADO 180 respecto a F+: sus pines son (modulo, riel) mientras que
    # los de F+ son (riel, modulo), asi que sin girarlo el lado de riel de -12 V
    # cae hacia DENTRO del slot y la pista de -12S tendria que pasar por debajo
    # de su propio pad de riel. Girado, en las dos franjas el riel queda hacia
    # el borde y el modulo hacia el centro.
    "F+": (-22.0, 14.0, 0),      "F-": (-16.92, 46.0, 180),
    "D+": (-5.46, 14.0, 180),    "D-": (-5.46, 46.0, 180),
    "R+": (2.0, 14.0, 0),        "R-": (2.0, 46.0, 0),
    "P":  (-14.0, 28.0, 270),    # KK-254: pin1 (+12S) arriba, pin4 (-12S) abajo
    "J":  (2.0, 38.16, 180),     # Eurorack: par 1 (franja roja, -12 V) abajo
}
HUELLA = {
    "F": ("sam17", "PTC_Radial_P5.08mm_Dual"),
    "D": ("LED_THT", "LED_D3.0mm"),
    "R": ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"),
    "P": ("Connector_Molex", "Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical"),
    "J": ("Connector_PinHeader_2.54mm", "PinHeader_2x08_P2.54mm_Vertical"),
    "J7": ("TerminalBlock", "TerminalBlock_MaiXu_MX126-5.0-04P_1x04_P5.00mm"),
}


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def leer_netlist() -> dict[str, str]:
    """{'F1-2': 'red'} — de que red es cada pad, segun kicad-cli."""
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()
    cab = list(re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)', txt))
    assert cab, "netlist ilegible: corre build_schematic.py primero"
    out = {}
    for i, m in enumerate(cab):
        fin = cab[i + 1].start() if i + 1 < len(cab) else len(txt)
        for a, b in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',
                               txt[m.end():fin]):
            out[f"{a}-{b}"] = m.group(1).lstrip("/")
    return out


def check_huellas() -> None:
    """Antes de tocar el fichero, a proposito (misma leccion que el modulo 1)."""
    rotos = [f"{k}: {lib}:{n}" for k, (lib, n) in HUELLA.items()
             if not os.path.isfile(os.path.join(
                 LOCAL if lib == "sam17" else os.path.join(STOCK, lib + ".pretty"),
                 n + ".kicad_mod"))]
    assert not rotos, f"huellas que no estan en disco: {rotos}"


# ---------------------------------------------------------------- geometria
def seg_seg(a, b, c, d) -> float:
    """Distancia minima entre los segmentos ab y cd."""
    def punto_seg(p, q, r):
        qx, qy = r[0] - q[0], r[1] - q[1]
        L = qx * qx + qy * qy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0]-q[0])*qx + (p[1]-q[1])*qy) / L))
        return ((p[0] - (q[0] + t*qx))**2 + (p[1] - (q[1] + t*qy))**2) ** 0.5
    def cruzan():
        def o(p, q, r):
            v = (q[1]-p[1])*(r[0]-q[0]) - (q[0]-p[0])*(r[1]-q[1])
            return 0 if abs(v) < 1e-12 else (1 if v > 0 else 2)
        o1, o2, o3, o4 = o(a, b, c), o(a, b, d), o(c, d, a), o(c, d, b)
        return o1 != o2 and o3 != o4
    if cruzan():
        return 0.0
    return min(punto_seg(a, c, d), punto_seg(b, c, d),
               punto_seg(c, a, b), punto_seg(d, a, b))


def revisar_capa_inferior(board) -> list[str]:
    """B.Cu solo puede llevar la zona de GND. Ni una pista, ni una via.

    Es LA regla de esta placa. Cualquier cobre ajeno en B.Cu parte el plano y
    obliga a la corriente de retorno a rodearlo, que es exactamente lo que el
    presupuesto de masa da por descontado que no pasa.
    """
    malos = []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            malos.append(f"via en {t.GetPosition()}")
        elif t.GetLayer() == pcbnew.B_Cu:
            malos.append(f"pista de '{t.GetNetname()}' en B.Cu")
    return malos


def revisar_pistas(board) -> list[str]:
    """Pista contra pista y pista contra pad, en F.Cu, de redes distintas.

    El DRC de KiCad ya lo hace, pero llega tarde: si el ruteo esta mal, main()
    no debe llegar a escribir gerbers. En el modulo 1 el ruteo parecia limpio
    y el DRC saco 5 cortos justamente por no mirar pista-contra-PAD.
    """
    lim = 0.25
    segs = [(t.GetNetname(),
             (t.GetStart().x/1e6, t.GetStart().y/1e6),
             (t.GetEnd().x/1e6, t.GetEnd().y/1e6))
            for t in board.GetTracks() if t.GetLayer() == pcbnew.F_Cu]
    malos = []
    for i, (n1, a, b) in enumerate(segs):
        for n2, c, d in segs[i+1:]:
            if n1 != n2 and seg_seg(a, b, c, d) < lim:
                malos.append(f"'{n1}' roza '{n2}' cerca de {a}")
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == n1:
                    continue
                c = (pad.GetX()/1e6, pad.GetY()/1e6)
                r = max(pad.GetSize().x, pad.GetSize().y) / 2e6
                if seg_seg(a, b, c, c) < r + lim:
                    malos.append(f"'{n1}' pisa {fp.GetReference()}."
                                 f"{pad.GetNumber()} ('{pad.GetNetname()}')")
    return sorted(set(malos))


# ------------------------------------------------------------------ montaje
def main() -> None:
    check_huellas()
    nets = leer_netlist()
    board = pcbnew.CreateEmptyBoard()

    for n in sorted(set(nets.values())):
        board.Add(pcbnew.NETINFO_ITEM(board, n))

    def add(ref: str, clave: str, x: float, y: float, rot: int):
        lib, nombre = HUELLA[clave]
        fp = pcbnew.FootprintLoad(
            LOCAL if lib == "sam17" else os.path.join(STOCK, lib + ".pretty"), nombre)
        assert fp, f"no se cargo {lib}:{nombre}"
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        if rot:
            fp.SetOrientationDegrees(rot)
        board.Add(fp)
        for pad in fp.Pads():
            red = nets.get(f"{ref}-{pad.GetNumber()}")
            if red:
                pad.SetNet(board.FindNet(red))
        return fp

    pads: dict[str, tuple[float, float]] = {}

    def registrar(fp) -> None:
        for pad in fp.Pads():
            k = f"{fp.GetReference()}-{pad.GetNumber()}"
            if k not in pads:      # el PTC tiene el pad 2 duplicado a proposito
                pads[k] = (round(pad.GetX()/1e6, 3), round(pad.GetY()/1e6, 3))

    registrar(add("J7", "J7", X_FEED, 20.0, 270))
    for k, xs in enumerate(SLOTS_X):
        n = k + 1
        for clave, ref in (("F+", f"F{2*k+1}"), ("F-", f"F{2*k+2}"),
                           ("D+", f"D{2*k+1}"), ("D-", f"D{2*k+2}"),
                           ("R+", f"R{2*k+1}"), ("R-", f"R{2*k+2}"),
                           ("P", f"P{n}"), ("J", f"J{n}")):
            dx, dy, rot = REL[clave]
            registrar(add(ref, clave[0], xs + dx, dy, rot))

    # la colocacion depende de como gire pcbnew cada huella; en vez de fiarse,
    # se comprueba contra lo que el ruteo da por hecho
    for k, xs in enumerate(SLOTS_X):
        n = k + 1
        assert pads[f"P{n}-1"] == (xs - 14.0, 28.0), \
            f"P{n} girado al reves: pin 1 (+12S) tiene que quedar ARRIBA"
        assert pads[f"P{n}-4"] == (xs - 14.0, 35.62), f"P{n}: pin 4 abajo"
        assert pads[f"J{n}-1"] == (xs + 2.0, 38.16), \
            f"J{n} girado al reves: el par 1 (franja roja, -12 V) va ABAJO"
        assert pads[f"J{n}-9"] == (xs + 2.0, 28.0), f"J{n}: par 5 (+12 V) arriba"
        assert pads[f"J{n}-16"][1] < pads[f"J{n}-9"][1], "los NC van arriba del todo"
    assert pads["J7-1"] == (X_FEED, 20.0) and pads["J7-4"] == (X_FEED, 35.0)

    # ---------------------------------------------------------------- pistas
    def pista(red: str, puntos: list) -> None:
        pts = [pads[p] if isinstance(p, str) else p for p in puntos]
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
            t.SetWidth(mm(ANCHO_PISTA))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(board.FindNet(red))
            board.Add(t)

    pista("+12V", ["J7-1", (X_FEED, 5.0)])
    pista("-12V", ["J7-4", (X_FEED, 55.0)])
    for k, xs in enumerate(SLOTS_X):
        n, fp_, fn_ = k + 1, f"F{2*k+1}", f"F{2*k+2}"
        dp, dn, rp, rn = f"D{2*k+1}", f"D{2*k+2}", f"R{2*k+1}", f"R{2*k+2}"
        # riel de +12 V hacia el PTC y hacia el anodo del LED
        # riel de +12 V: al PTC por un lado y al anodo del LED por el otro
        pista("+12V", [f"{fp_}-1", (xs - 22.0, 5.0)])
        pista("+12V", [f"{dp}-2", (xs - 8.0, 5.0)])
        # el nudo catodo-resistencia NO es +12S: es la red interna del
        # indicador, la que KiCad bautiza Net-(Dn-K). Etiquetarla +12S
        # cortocircuitaba el LED y lo dejaba apagado para siempre.
        pista(f"Net-({dp}-K)", [f"{dp}-1", f"{rp}-1"])
        # nodo +12S: PTC -> KK -> peine, y el retorno de la rama del indicador
        pista(f"+12S{n}", [f"{fp_}-2", (xs - 16.92, 28.0), f"P{n}-1",
                           f"J{n}-10", f"J{n}-9"])
        pista(f"+12S{n}", [f"{rp}-2", (xs + 12.16, 28.0), f"J{n}-9"])
        # espejo en -12 V (con F- girado, ver REL)
        pista("-12V", [f"{fn_}-2", (xs - 22.0, 55.0)])
        pista("-12V", [f"{rn}-2", (xs + 12.16, 55.0)])
        pista(f"Net-({dn}-K)", [f"{dn}-1", f"{rn}-1"])
        pista(f"-12S{n}", [f"{fn_}-1", (xs - 16.92, 38.16), f"J{n}-1"])
        pista(f"-12S{n}", [f"{fn_}-1", f"{dn}-2"])
        pista(f"-12S{n}", [f"P{n}-4", (xs - 14.0, 38.16)])
        pista(f"-12S{n}", [f"J{n}-2", f"J{n}-1"])

    # ----------------------------------------------------------- contorno
    for a, b in [((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))]:
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)
    # taladro de la libreria, no fabricado a mano: construir un PAD suelto y
    # pedirle su UnplatedHoleMask antes de estar dentro de una huella revienta
    # pcbnew con un segfault, sin traza ni mensaje.
    for i, (x, y) in enumerate(MOUNT):
        fp = pcbnew.FootprintLoad(os.path.join(STOCK, "MountingHole.pretty"),
                                  f"MountingHole_{MOUNT_D}mm_M3")
        assert fp, "no carga la huella del taladro de fijacion"
        fp.SetReference(f"H{i+1}")
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        board.Add(fp)

    # -------------------------------------------------------------- zonas
    def zona(red: str, capa, x0: float, y0: float, x1: float, y1: float):
        z = pcbnew.ZONE(board)
        z.SetLayer(capa)
        z.SetNet(board.FindNet(red))
        z.SetLocalClearance(mm(0.4))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # sin termicas: es masa
        z.SetIsFilled(False)
        v = pcbnew.VECTOR_VECTOR2I()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            v.append(pcbnew.VECTOR2I(mm(x), mm(y)))
        z.AddPolygon(v)
        board.Add(z)
        return z

    zona("GND", pcbnew.B_Cu, MARGEN, MARGEN, W - MARGEN, H - MARGEN)
    zona("+12V", pcbnew.F_Cu, MARGEN, Y_Z12, W - MARGEN, Y_Z12B)
    zona("-12V", pcbnew.F_Cu, MARGEN, Y_ZN, W - MARGEN, Y_ZNB)

    reglas = board.GetDesignSettings()
    reglas.m_TrackMinWidth = mm(0.3)
    reglas.m_MinClearance = mm(0.25)
    # BuildConnectivity ANTES de rellenar: sin el, ZONE_FILLER.Fill peta con
    # un access violation del proceso entero — ni excepcion ni traza, solo un
    # segfault mudo.
    board.BuildListOfNets()
    board.BuildConnectivity()

    # --------------------------------------------------------- comprobar
    fallos = revisar_capa_inferior(board) + revisar_pistas(board)
    huerfanos = [f"{fp.GetReference()}.{p.GetNumber()}"
                 for fp in board.GetFootprints() for p in fp.Pads()
                 if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                 and p.GetNetname() == ""]
    if huerfanos:
        fallos.append(f"pads sin red: {huerfanos[:6]}")
    assert not fallos, "\n  ".join(["ruteo mal:"] + fallos)

    pcbnew.SaveBoard(PCB, board)

    # Rellenar hay que rellenar sobre la placa RECARGADA. Sobre la que se acaba
    # de construir en memoria, ZONE_FILLER.Fill() se lleva el proceso por
    # delante con un access violation — ni excepcion ni traza, solo un segfault
    # mudo. Ida y vuelta por disco y funciona.
    board = pcbnew.LoadBoard(PCB)
    board.BuildListOfNets()
    board.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(board).Fill(board.Zones(), False, None),         "no se rellenaron las zonas"

    # Y AQUI la comprobacion que justifica la placa entera. GetLayerName() no
    # sirve: sobre la placa en memoria devuelve "F.Cu" para la zona de masa aun
    # estando bien puesta, porque la tabla de nombres todavia no existe. Se
    # compara el id de capa, que si es de fiar.
    zonas = {z.GetNetname(): z for z in board.Zones()}
    assert zonas["GND"].GetLayer() == pcbnew.B_Cu,         "la masa NO esta en B.Cu: sin plano entero, el presupuesto de masa no vale"
    for n, z in zonas.items():
        assert z.IsFilled(), f"la zona de {n} quedo sin rellenar"
    assert zonas["+12V"].GetLayer() == pcbnew.F_Cu
    assert zonas["-12V"].GetLayer() == pcbnew.F_Cu
    pcbnew.SaveBoard(PCB, board)

    print(f"{len(board.GetFootprints()) - len(MOUNT)} huellas, "
          f"{len(board.GetTracks())} segmentos, {len(zonas)} zonas rellenas, "
          f"masa en {['F.Cu','?','B.Cu'][zonas['GND'].GetLayer()]}, 0 vias")

    drc = subprocess.run([KICAD_CLI, "pcb", "drc", "--severity-error",
                          "--exit-code-violations", PCB],
                         capture_output=True, text=True)
    print(drc.stdout.strip()[-500:] or drc.stderr.strip()[-300:])
    sys.exit(drc.returncode)


if __name__ == "__main__":
    main()
