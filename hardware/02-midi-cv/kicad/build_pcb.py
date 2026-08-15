"""Genera sam17-midicv.kicad_pcb: 160 x 100 mm, 2 capas, DOS masas separadas.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Va con pcbnew directo, igual que el modulo 1 y el bus board.

LA REGLA DE ESTA PLACA: **GNDA y GNDD no se tocan en ningun punto del cobre.**

  Se unen en el punto de estrella del modulo 1 y en ningun otro sitio. Si se
  juntaran aqui, la corriente del backlight del LCD tendria dos caminos de
  vuelta y parte se iria por la masa analogica: 100 mA sobre unos 50 mohm son
  5 mV, que amplificados por 2.8 son 14 mV, o sea **17 cents de desafinacion
  que aparecen y desaparecen segun el brillo de la pantalla**.

  La placa se parte por una frontera VERTICAL en x = X_FRONTERA. A la izquierda
  vive el dominio digital (Pi, LCD, botones, MOSFET del gate) con su vertido de
  GNDD; a la derecha el analogico (DAC, amplificadores, jacks) con el de GNDA.
  Entre los dos queda una franja de HUECO sin cobre en B.Cu, y
  revisar_frontera() la mide.

  Lo que SI cruza la frontera son senales por F.Cu: SPI, gate, y los rieles.
  Eso no une las masas — cruza por la capa de arriba, por encima del hueco.

ASIMETRIA DELIBERADA EN EL RUTEO: por B.Cu solo se admiten pistas en el lado
DIGITAL. Alli el plano no mide nada y partirlo no cuesta; en el analogico el
plano es lo que sostiene el presupuesto de afinacion y no se toca. Es la misma
logica que en el bus board, aplicada a media placa.

El DAC vive justo en la frontera a proposito: su VDD y su VLOGIC son digitales,
su GND y sus salidas son analogicas. Es la pieza que cose los dos mundos y por
eso es la que menos cable tiene que cruzar.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-midicv.kicad_pcb")
NET = os.path.join(DIR, "sam17-midicv.net")
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
STOCK = os.environ.get("KICAD_FOOTPRINTS",
                       r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

W, H = 160.0, 100.0
MARGEN = 3.0
X_FRONTERA = 78.0          # eje del hueco entre los dos vertidos
HUECO = 4.0                # ancho del hueco, mm
ANCHO = 0.25               # pista de senal. Fina a proposito: el TSSOP-16 del
                           # DAC tiene 0.65 mm de paso y con 0.4 no hay por
                           # donde sacar las patillas del medio.
ANCHO_POT = 0.8            # solo +-12 V, que van a un DIP de paso 2.54
ANCHO_MED = 0.4            # +5 V y +3V3: llegan al TSSOP y 0.8 no cabe
VIA_D = 0.8                # diametro exterior de via
MOUNT = [(5.0, 5.0), (155.0, 5.0), (5.0, 95.0), (155.0, 95.0)]
MOUNT_D = 3.2

# huella -> (libreria, nombre)
HUELLA = {
    "conn2": ("Connector_Molex", "Molex_KK-254_AE-6410-02A_1x02_P2.54mm_Vertical"),
    "conn4": ("Connector_Molex", "Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical"),
    "conn16": ("Connector_PinHeader_2.54mm", "PinHeader_1x16_P2.54mm_Vertical"),
    "pi": ("Connector_PinHeader_2.54mm", "PinHeader_2x20_P2.54mm_Vertical"),
    "dac": ("Package_SO", "TSSOP-16_4.4x5mm_P0.65mm"),
    "opamp": ("Package_DIP", "DIP-14_W7.62mm_Socket"),
    "r": ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"),
    "c": ("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm"),
    "pot": ("Potentiometer_THT", "Potentiometer_Bourns_3296W_Vertical"),
    "q": ("Package_TO_SOT_SMD", "SOT-23"),
    "sw": ("Button_Switch_THT", "SW_PUSH_6mm"),
    "jack": ("Connector_Audio",
             "Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"),
}

# ref -> (clave de huella, x, y, rotacion)
COLOCACION = {
    # ---------------- lado DIGITAL (x < frontera) ----------------------
    "J3": ("pi", 12.0, 10.0, 90),        # cabecera del Pi, tumbada arriba
    "J2": ("conn2", 66.0, 8.0, 0),       # +5 V con su retorno dedicado
    "C3": ("c", 66.0, 14.0, 0),          # bulk del +5 V, contra GNDD
    "C4": ("c", 66.0, 20.0, 0),          # +3V3 del Pi, contra GNDD
    # El LCD en VERTICAL contra el borde izquierdo, no tumbado debajo del Pi.
    # Tumbado, sus 16 patillas quedaban paralelas a las 40 del Pi con 14 mm
    # entre medias, y por esa franja tenian que pasar ademas los botones y el
    # SPI. Seis senales de LCD se quedaban sin ruta. En vertical cada una sale
    # por su propia altura.
    "J8": ("conn16", 6.0, 30.0, 0),
    "RV1": ("pot", 22.0, 60.0, 0),
    "R16": ("r", 16.0, 70.0, 0),
    # gate: dos etapas en fila, de izquierda a derecha como en el esquematico
    "R10": ("r", 16.0, 34.0, 0),
    "Q1": ("q", 32.0, 34.0, 0),
    "R14": ("r", 16.0, 42.0, 0),
    "R11": ("r", 38.0, 28.0, 0),
    "Q2": ("q", 52.0, 34.0, 0),
    "R12": ("r", 58.0, 28.0, 0),
    "R13": ("r", 58.0, 42.0, 0),
    # botones con su pull-up encima, en una fila abajo
    "SW1": ("sw", 24.0, 86.0, 0), "R17": ("r", 24.0, 78.0, 0),
    "SW2": ("sw", 38.0, 86.0, 0), "R18": ("r", 38.0, 78.0, 0),
    "SW3": ("sw", 52.0, 86.0, 0), "R19": ("r", 52.0, 78.0, 0),
    "SW4": ("sw", 66.0, 86.0, 0), "R20": ("r", 66.0, 78.0, 0),

    # ---------------- lado ANALOGICO (x > frontera) --------------------
    "J1": ("conn4", 86.0, 8.0, 0),       # bus de +-12 V
    "C1": ("c", 100.0, 8.0, 0),
    "C2": ("c", 112.0, 8.0, 0),
    # El DAC GIRADO 180: sus patillas 9-16 (SPI, VLOGIC) quedan mirando a la
    # izquierda, hacia el Pi, y las 1-8 (salidas analogicas, VREF, GND) a la
    # derecha, hacia el amplificador. Sin girarlo esta justo al reves y el SPI
    # tiene que dar la vuelta al chip entero.
    "U1": ("dac", 88.0, 26.0, 180),
    # los tres del DAC, lo mas cerca que caben de el
    "C5": ("c", 94.0, 16.0, 0),
    "C6": ("c", 94.0, 22.0, 0),
    "C7": ("c", 82.0, 34.0, 0),
    "U2": ("opamp", 100.0, 46.0, 0),     # TL074H en zocalo
    # redes de ganancia: la de 18k arriba, la de 10k abajo, por canal
    "R1": ("r", 116.0, 44.0, 0), "R2": ("r", 116.0, 52.0, 0),
    "R3": ("r", 116.0, 60.0, 0), "R4": ("r", 116.0, 68.0, 0),
    "R5": ("r", 116.0, 76.0, 0), "R6": ("r", 116.0, 84.0, 0),
    # series de salida
    "R7": ("r", 132.0, 44.0, 0), "R8": ("r", 132.0, 60.0, 0),
    "R9": ("r", 132.0, 76.0, 0), "R15": ("r", 132.0, 90.0, 0),
    # jacks en el borde derecho
    "J4": ("jack", 150.0, 16.0, 0), "J5": ("jack", 150.0, 36.0, 0),
    "J6": ("jack", 150.0, 56.0, 0), "J7": ("jack", 150.0, 76.0, 0),
}

# El pad TN del jack (el contacto de normalizado) no existe en el simbolo
# AudioJack2, que solo tiene S y T. Queda sin red a proposito: es un muelle
# mecanico que en este modulo no se usa.
PADS_SIN_RED = {f"J{i}-TN" for i in (4, 5, 6, 7)}


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def leer_netlist() -> dict[str, str]:
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
    rotos = [f"{k}: {lib}:{n}" for k, (lib, n) in HUELLA.items()
             if not os.path.isfile(os.path.join(STOCK, lib + ".pretty",
                                                n + ".kicad_mod"))]
    assert not rotos, f"huellas que no estan en disco: {rotos}"


def es_digital(net: str) -> bool:
    return net in ("GNDD", "+3V3") or net.startswith(
        ("LCD_", "BTN_", "SPI_", "SCLK", "SDIN", "DAC_RESET", "GATE_IO", "GATE_G"))


def main() -> None:
    check_huellas()
    nets = leer_netlist()
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)
    for n in sorted(set(nets.values())):
        board.Add(pcbnew.NETINFO_ITEM(board, n))

    pads: dict[str, tuple[float, float]] = {}
    for ref, (clave, x, y, rot) in COLOCACION.items():
        lib, nombre = HUELLA[clave]
        fp = pcbnew.FootprintLoad(os.path.join(STOCK, lib + ".pretty"), nombre)
        assert fp, f"no se cargo {lib}:{nombre}"
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        if rot:
            fp.SetOrientationDegrees(rot)
        board.Add(fp)
        for pad in fp.Pads():
            k = f"{ref}-{pad.GetNumber()}"
            red = nets.get(k)
            if red:
                pad.SetNet(board.FindNet(red))
            if k not in pads:      # SW_PUSH y el jack repiten numero de pad
                pads[k] = (round(pad.GetX() / 1e6, 3), round(pad.GetY() / 1e6, 3))

    # ---------------------------------------------------------- contorno
    for a, b in [((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)),
                 ((0, H), (0, 0))]:
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)
    for i, (x, y) in enumerate(MOUNT):
        fp = pcbnew.FootprintLoad(os.path.join(STOCK, "MountingHole.pretty"),
                                  f"MountingHole_{MOUNT_D}mm_M3")
        fp.SetReference(f"H{i+1}")
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        board.Add(fp)

    # ------------------------------------------------------------- zonas
    def zona(red: str, capa, x0, y0, x1, y1):
        z = pcbnew.ZONE(board)
        z.SetLayer(capa)
        z.SetNet(board.FindNet(red))
        z.SetLocalClearance(mm(0.4))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIsFilled(False)
        v = pcbnew.VECTOR_VECTOR2I()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            v.append(pcbnew.VECTOR2I(mm(x), mm(y)))
        z.AddPolygon(v)
        board.Add(z)
        return z

    zona("GNDD", pcbnew.B_Cu, MARGEN, MARGEN,
         X_FRONTERA - HUECO / 2, H - MARGEN)
    zona("GNDA", pcbnew.B_Cu, X_FRONTERA + HUECO / 2, MARGEN,
         W - MARGEN, H - MARGEN)

    reglas = board.GetDesignSettings()
    reglas.m_TrackMinWidth = mm(0.25)
    reglas.m_MinClearance = mm(0.2)

    # ------------------------------------------------------------ ruteo
    n_seg, n_via, sin_rutear = rutear_todo(board)
    print(f"ruteadas {n_seg} segmentos y {n_via} vias")
    if sin_rutear:
        print(f"SIN RUTEAR ({len(sin_rutear)}):")
        for s in sin_rutear:
            print("   ", s)

    pcbnew.SaveBoard(PCB, board)

    # el relleno hay que hacerlo sobre la placa RECARGADA: sobre la de memoria
    # ZONE_FILLER.Fill() se lleva el proceso por delante con un access
    # violation, sin excepcion que capturar (misma trampa que en el bus board)
    board = pcbnew.LoadBoard(PCB)
    board.BuildListOfNets()
    board.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(board).Fill(board.Zones(), False, None), \
        "no se rellenaron las zonas"
    pcbnew.SaveBoard(PCB, board)

    fallos = revisar(board)
    for f in fallos:
        print("FALLO:", f)
    zonas = {z.GetNetname(): z for z in board.Zones()}
    print(f"{len(COLOCACION)} huellas colocadas, "
          f"{len(board.GetTracks())} segmentos, "
          f"zonas: {sorted(zonas)} en "
          f"{['F.Cu','?','B.Cu'][zonas['GNDA'].GetLayer()]}")
    if fallos:
        sys.exit(1)

    drc = subprocess.run([KICAD_CLI, "pcb", "drc", "--severity-error",
                          "--exit-code-violations", PCB],
                         capture_output=True, text=True)
    print(drc.stdout.strip()[-600:] or drc.stderr.strip()[-300:])

    # Sale con error mientras queden redes sin rutear. La placa NO es
    # fabricable en ese estado, y un script que termina en verde con 17 redes
    # al aire es justo la clase de trampa que este repo intenta no dejar.
    if sin_rutear:
        print(f"\nLA PLACA NO ESTA TERMINADA: quedan {len(sin_rutear)} redes "
              f"sin rutear. Colocacion y masas si estan cerradas.")
        sys.exit(2)


CLEARANCE = 0.2           # mm entre cobre de redes distintas
# Barrido denso en vez de una lista corta de corredores a mano: la lista corta
# dejaba 30 redes sin rutear porque el hueco bueno casi nunca caia justo en uno
# de los ocho valores elegidos a ojo.
CORREDORES_X = [4.0 + 1.5 * i for i in range(102)]     # 4 .. 155.5
CORREDORES_Y = [4.0 + 1.5 * i for i in range(62)]      # 4 .. 95.5
# Varias distancias de escape, no una: si todas las patillas de una fila salen
# el mismo trecho, sus giros caen en la misma vertical y se estorban entre si.
ESCAPES = [(0.0, 0.0)] + [(d * s, 0.0) for d in (1.6, 2.8, 4.2, 5.8, 7.4)
                          for s in (1, -1)]                        + [(0.0, d * s) for d in (1.6, 2.8, 4.2, 5.8, 7.4)
                          for s in (1, -1)]


def _dist_punto_seg(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    tt = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / L))
    return ((p[0] - (a[0]+tt*dx))**2 + (p[1] - (a[1]+tt*dy))**2) ** 0.5


def _seg_seg(a, b, c, d) -> float:
    def o(p, q, r):
        v = (q[1]-p[1])*(r[0]-q[0]) - (q[0]-p[0])*(r[1]-q[1])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else 2)
    if o(a, b, c) != o(a, b, d) and o(c, d, a) != o(c, d, b):
        return 0.0
    return min(_dist_punto_seg(a, c, d), _dist_punto_seg(b, c, d),
               _dist_punto_seg(c, a, b), _dist_punto_seg(d, a, b))


def _dist_seg_rect(a, b, x0, y0, x1, y1) -> float:
    """Distancia minima entre el segmento ab y un rectangulo alineado."""
    for p in (a, b):
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            return 0.0
    lados = (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
             ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))
    return min(_seg_seg(a, b, c, d) for c, d in lados)


def rutear_todo(board):
    """Ruteador minimo: para cada red prueba caminos en L y en Z y se queda con
    el primero que no roce nada.

    No es un autorouter de verdad y no lo pretende. Es lo justo para una placa
    donde la COLOCACION ya deja cada senal cerca de su destino: si un camino
    simple no cabe, el sitio donde hay que trabajar es la colocacion, no el
    ruteador. Por eso, cuando falla, lo dice en vez de retorcerse.

    Sale a mano lo de calcular 40 redes de coordenadas de cabeza, que es donde
    esto se estaba atascando y donde se cuelan los cortos.
    """
    # Los pads se modelan como RECTANGULOS, no como circulos.
    #
    # Antes se usaba max(ancho,alto)/2 como radio, y para un pad alargado eso es
    # grotesco: el del TSSOP mide 1.5 x 0.4 y salia un circulo de radio 0.75 que
    # se comia a sus dos vecinos, con lo que NINGUNA pista podia acercarse al
    # DAC. Veinte redes sin rutear que parecian culpa del ruteador y eran del
    # modelo de obstaculos.
    obst_pads = [(p.GetNetname(),
                  p.GetX()/1e6 - p.GetSize().x/2e6,
                  p.GetY()/1e6 - p.GetSize().y/2e6,
                  p.GetX()/1e6 + p.GetSize().x/2e6,
                  p.GetY()/1e6 + p.GetSize().y/2e6)
                 for fp in board.GetFootprints() for p in fp.Pads()]
    puestos: list = []          # (net, capa, a, b, ancho)
    vias: list = []             # (net, x, y, radio)

    def ancho_de(net: str) -> float:
        if net in ("+12V", "-12V"):
            return ANCHO_POT
        return ANCHO_MED if net in ("+5V", "+3V3") else ANCHO

    def libre(net, capa, a, b, w) -> bool:
        """El ancho REAL de la pista entra en la cuenta.

        Antes se usaba siempre ANCHO, y una pista de riel de 0.8 mm salia a
        0.05 mm de un pad del DAC: el ruteador la daba por buena y el DRC la
        cazaba despues. Tampoco se miraban las vias ya puestas.
        """
        for n, x0, y0, x1, y1 in obst_pads:
            if n == net:
                continue
            if _dist_seg_rect(a, b, x0, y0, x1, y1) < CLEARANCE + w / 2:
                return False
        for n, c, p, q, wo in puestos:
            if n == net or c != capa:
                continue
            if _seg_seg(a, b, p, q) < CLEARANCE + w / 2 + wo / 2:
                return False
        for n, vx, vy, vr in vias:
            if n == net:
                continue
            if _dist_punto_seg((vx, vy), a, b) < CLEARANCE + w / 2 + vr:
                return False
        return True

    def caminos(a, b):
        """De lo simple a lo enrevesado, para que la primera que cuele sea la
        mas corta. Los "escapes" son un saltito perpendicular al salir del pad:
        sin ellos, una patilla en medio de una fila (la cabecera del Pi, el
        LCD) no tiene por donde salir sin rozar a sus vecinas."""
        yield [a, (b[0], a[1]), b]
        yield [a, (a[0], b[1]), b]
        orden_x = sorted(CORREDORES_X, key=lambda v: min(abs(v-a[0]), abs(v-b[0])))
        orden_y = sorted(CORREDORES_Y, key=lambda v: min(abs(v-a[1]), abs(v-b[1])))
        for mx in orden_x:
            yield [a, (mx, a[1]), (mx, b[1]), b]
        for my in orden_y:
            yield [a, (a[0], my), (b[0], my), b]
        # Escapes de UN lado cada vez, no el producto cruzado. Con las dos
        # puntas a la vez salian ~22.000 candidatos por tramo y el ruteador
        # dejaba de terminar; de uno en uno son ~2.000 y cubren igual, porque
        # el que estorba casi siempre es un solo extremo.
        for lado in (0, 1):
            for esc in ESCAPES[1:]:
                pa = (a[0] + esc[0], a[1] + esc[1]) if lado == 0 else a
                pb = b if lado == 0 else (b[0] + esc[0], b[1] + esc[1])
                for mx in orden_x[:24]:
                    yield [a, pa, (mx, pa[1]), (mx, pb[1]), pb, b]
                for my in orden_y[:24]:
                    yield [a, pa, (pa[0], my), (pb[0], my), pb, b]

    # redes a rutear: todas menos las masas, que las hacen los vertidos
    por_red: dict = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if not n or n in ("GNDA", "GNDD") or n.startswith("unconnected-"):
                continue
            por_red.setdefault(n, []).append((p.GetX()/1e6, p.GetY()/1e6))

    def via_cabe(net, punto) -> bool:
        """Que quepa una via de VIA_D en ese punto.

        Sin esto el ruteador bajaba a B.Cu poniendo la via encima de un pad del
        TSSOP, donde hay 0.65 mm de paso y una via de 0.8 no entra ni de lejos.
        Seis infracciones de DRC, todas la misma causa.
        """
        r = VIA_D / 2 + CLEARANCE
        for n, x0, y0, x1, y1 in obst_pads:
            if n != net and _dist_seg_rect(punto, punto, x0, y0, x1, y1) < r:
                return False
        for n, _c, q1, q2, wo in puestos:
            if n != net and _dist_punto_seg(punto, q1, q2) < r + wo / 2:
                return False
        for n, vx, vy, vr in vias:
            if n != net and ((punto[0]-vx)**2 + (punto[1]-vy)**2) ** 0.5 < r + vr:
                return False
        return True

    n_seg = n_via = 0
    sin_rutear = []
    # Primero las redes LARGAS, mientras la placa esta vacia y hay sitio. Por
    # orden alfabetico, las cortas y faciles se colocaban antes y dejaban a las
    # largas sin pasillo: es la heuristica clasica y aqui cuesta una linea.
    def envergadura(par):
        pts = par[1]
        return -(max(x for x, _ in pts) - min(x for x, _ in pts)
                 + max(y for _, y in pts) - min(y for _, y in pts))

    for net, pts in sorted(por_red.items(), key=envergadura):
        pts = sorted(set(pts))
        hechos, pend = [pts[0]], pts[1:]
        while pend:
            b = min(pend, key=lambda q: min(abs(q[0]-h[0]) + abs(q[1]-h[1])
                                            for h in hechos))
            a = min(hechos, key=lambda h: abs(b[0]-h[0]) + abs(b[1]-h[1]))
            pend.remove(b)
            elegido = None
            for capa in (pcbnew.F_Cu, pcbnew.B_Cu):
                if capa == pcbnew.B_Cu and not (via_cabe(net, a) and via_cabe(net, b)):
                    continue
                for cam in caminos(a, b):
                    tramos = [(cam[i], cam[i+1]) for i in range(len(cam)-1)
                              if cam[i] != cam[i+1]]
                    if all(libre(net, capa, p, q, ancho_de(net))
                           for p, q in tramos):
                        elegido = (capa, tramos)
                        break
                if elegido:
                    break
            if not elegido:
                sin_rutear.append(f"{net}: {a} -> {b}")
                hechos.append(b)
                continue
            capa, tramos = elegido
            for p, q in tramos:
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(mm(p[0]), mm(p[1])))
                tr.SetEnd(pcbnew.VECTOR2I(mm(q[0]), mm(q[1])))
                tr.SetWidth(mm(ancho_de(net)))
                tr.SetLayer(capa)
                tr.SetNet(board.FindNet(net))
                board.Add(tr)
                puestos.append((net, capa, p, q, ancho_de(net)))
                n_seg += 1
            if capa == pcbnew.B_Cu:
                for punto in (a, b):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I(mm(punto[0]), mm(punto[1])))
                    v.SetDrill(mm(0.4))
                    v.SetWidth(mm(0.8))
                    v.SetNet(board.FindNet(net))
                    board.Add(v)
                    vias.append((net, punto[0], punto[1], 0.4))
                    n_via += 1
            hechos.append(b)
    return n_seg, n_via, sin_rutear


def revisar(board) -> list[str]:
    fallos: list[str] = []
    zonas = {z.GetNetname(): z for z in board.Zones()}

    # 1. las dos masas, cada una en su sitio y en B.Cu
    for n in ("GNDA", "GNDD"):
        if n not in zonas:
            fallos.append(f"falta el vertido de {n}")
        elif zonas[n].GetLayer() != pcbnew.B_Cu:
            fallos.append(f"el vertido de {n} no esta en B.Cu")
    if not fallos:
        fallos += revisar_frontera(board, zonas)

    # 2. cada plano de masa tiene que seguir siendo UNA SOLA isla.
    #
    # La primera version de esta regla prohibia toda pista por B.Cu en el lado
    # analogico. Era un proxy, y de los malos: lo que hace dano no es que haya
    # cobre en la capa de abajo, es que el plano quede PARTIDO y la corriente de
    # retorno tenga que rodear. Un vertido troceado se ve aqui como varias
    # islas, asi que se cuenta directamente lo que importa.
    # Solo se exige del ANALOGICO. El digital puede fragmentarse todo lo que
    # haga falta: alli el plano no mide nada, solo devuelve corriente logica.
    # Es la misma asimetria de la cabecera, dicha en forma de comprobacion.
    if "GNDA" in zonas:
        islas = zonas["GNDA"].GetFilledPolysList(pcbnew.B_Cu).OutlineCount()
        if islas != 1:
            fallos.append(f"el plano ANALOGICO quedo partido en {islas} islas: "
                          f"alguna pista de B.Cu lo corta y la corriente de "
                          f"retorno tiene que rodear")

    # 3. cada pieza en el lado que le toca
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("H"):
            continue
        for pad in fp.Pads():
            k, red = f"{ref}-{pad.GetNumber()}", pad.GetNetname()
            px = pad.GetX() / 1e6
            if red == "GNDD" and px > X_FRONTERA:
                fallos.append(f"{k} es GNDD pero cae en el lado analogico")
            if red == "GNDA" and px < X_FRONTERA:
                fallos.append(f"{k} es GNDA pero cae en el lado digital")

    # 4. pads sin red
    huerfanos = [f"{fp.GetReference()}-{p.GetNumber()}"
                 for fp in board.GetFootprints() for p in fp.Pads()
                 if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                 and p.GetNetname() == ""
                 and f"{fp.GetReference()}-{p.GetNumber()}" not in PADS_SIN_RED
                 and not fp.GetReference().startswith("H")]
    if huerfanos:
        fallos.append(f"pads sin red: {sorted(set(huerfanos))[:8]}")

    # 5. nada fuera de la placa
    for fp in board.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        m = min(bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                W - bb.GetRight() / 1e6, H - bb.GetBottom() / 1e6)
        if m < 0:
            fallos.append(f"{fp.GetReference()} se sale de la placa ({m:.2f} mm)")
    return fallos


def revisar_frontera(board, zonas) -> list[str]:
    """Que los dos vertidos NO se toquen, medido sobre el cobre relleno.

    No basta con haber dibujado dos rectangulos separados: el relleno se mete
    por donde puede y una isla de GNDD puede aparecer al otro lado si algun pad
    de esa red esta mal colocado. Se mide poligono contra poligono.
    """
    def xs(z) -> list[float]:
        """Coordenadas x de TODOS los vertices del cobre realmente vertido.

        No se usan operaciones booleanas de poligonos porque el binding de
        Python de pcbnew no las expone; recorrer los vertices mide lo mismo y
        ademas dice DONDE se acerca cada vertido, que es lo que hace falta para
        corregirlo.
        """
        poly = z.GetFilledPolysList(pcbnew.B_Cu)
        out = []
        for i in range(poly.OutlineCount()):
            linea = poly.Outline(i)
            for j in range(linea.PointCount()):
                out.append(linea.CPoint(j).x / 1e6)
        return out

    xa, xd = xs(zonas["GNDA"]), xs(zonas["GNDD"])
    if not xa or not xd:
        return ["algun vertido de masa quedo vacio"]
    hueco = min(xa) - max(xd)
    if hueco <= 0:
        return [f"GNDA y GNDD SE PISAN: el analogico llega a x={min(xa):.2f} y "
                f"el digital a x={max(xd):.2f}. Las dos masas quedan unidas."]
    if hueco < HUECO * 0.5:
        return [f"el hueco entre masas quedo en {hueco:.2f} mm, muy justo"]
    print(f"hueco medido entre los dos vertidos de masa: {hueco:.2f} mm "
          f"(digital hasta x={max(xd):.2f}, analogico desde x={min(xa):.2f})")
    return []


if __name__ == "__main__":
    main()
