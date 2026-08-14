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
    # J3 a rot 0 y no 180: girado, el orden de pines salia PE-N-L de izquierda a
    # derecha y el neutro tenia que CRUZAR la linea para llegar al MOV. Sin
    # girar sale L-N-PE, y cada uno tira recto hacia donde va.
    "J3":  (10.0,  24.0,   0),   # entrada de red 230 V
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
    "D3":  (62.0,  70.0, 180),
    # --- carril +5 V (el del medio, sec.10.1) ---
    "C9":  (37.0,  88.0,   0),
    "D5":  (52.0,  80.0,   0),
    "U3":  (84.0,  88.0,   0),
    "C10": (48.0,  94.0,   0),
    "C11": (58.0,  88.0,   0),
    "R3":  (44.0, 102.0,   0),
    "D6":  (62.0, 102.0, 180),
    # --- carril -12 V ---
    "C4":  (37.0, 120.0,   0),
    "D2":  (52.0, 112.0,   0),
    "U2":  (84.0, 120.0,   0),
    "C6":  (48.0, 126.0,   0),
    "C8":  (58.0, 120.0,   0),
    "R2":  (44.0, 134.0,   0),
    "D4":  (62.0, 134.0, 180),
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
# ---------------------------------------------------------------- pistas ----
# (red, capa, puntos, ancho). F = cara de componentes, B = cara de soldadura.
#
# Reparto de capas: GND va entero por B, y todo lo demas por F. No es capricho
# — GND tiene 23 pads repartidos por toda la placa y si comparte cara con los
# rieles no hay forma de cerrar la estrella sin cruces por todos lados.
#
# NO HAY PLANO DE MASA, y es a proposito. Un pour une todo con todo por el
# camino mas corto, que es justo lo contrario de la estrella que pide sec.7 y
# del retorno dedicado de +5 V que exige sec.10.1. Aqui GND es un arbol: sale
# del punto de estrella (C1.2, en el bulk del riel positivo) y cada rama muere
# en su grupo funcional, sin bucles.
F, B = "F.Cu", "B.Cu"
ANCHO_POT, ANCHO_SEN, ANCHO_RED = 1.0, 0.4, 1.0

ESTRELLA = (52.5, 33.0)          # = C1.2, el bulk del riel positivo (sec.7)

TRACKS = [
    # --- lado de red, todo en F y confinado a la franja. Ninguna cruza la
    # barrera y ninguna puede: al otro lado no hay ni un pad de red. ---
    ("/L",    F, [(10, 24), (10, 40), (15, 40), (15, 45), (15, 50.1)], ANCHO_RED),
    ("/L_F",  F, [(22.6, 45), (22.6, 50.1)], ANCHO_RED),
    ("/L_F",  F, [(22.6, 50.1), (22.6, 56), (10, 56), (10, 72)], ANCHO_RED),
    ("/L_F",  F, [(10, 72), (10, 90), (12, 90), (12, 98)], ANCHO_RED),
    # El neutro baja por el canto derecho de la franja (x=26.5) para esquivar
    # el fusible y el cuerpo del MOV. Ese 26.5 es el cobre de red mas cercano
    # a la barrera y aun deja 9 mm al primer pad SELV.
    ("/N",    F, [(15, 24), (15, 30), (27, 30), (27, 66), (20, 66), (20, 72)], ANCHO_RED),
    ("/N",    F, [(20, 72), (20, 76), (27, 76), (27, 110), (16, 110), (16, 118)], ANCHO_RED),
    ("/L_TR", F, [(19.5, 98), (19.5, 106), (11, 106), (11, 118)], ANCHO_RED),

    # --- secundario del transformador, en B para dejar F a VRAW+ ---
    ("/SEC_A", B, [(42, 10), (42, 19), (77, 19), (77, 16.1), (75.6, 16.1)], ANCHO_POT),
    ("/SEC_B", B, [(52, 10), (52, 4), (79, 4), (79, 11), (75.6, 11)], ANCHO_POT),

    # --- VRAW+. Baja por x=62 (el hueco entre los cuerpos de C1 y C2) y llega
    # a C1.1 por debajo. A los reguladores entra por pasillos POR ENCIMA de su
    # carril (y=44 e y=76): a la altura del carril no cabe, porque los pads de
    # C7/C11 y el de GND del propio regulador estan en medio. ---
    ("/VRAW+", F, [(68, 11), (68, 6), (62, 6), (62, 44), (45, 44), (45, 33)], ANCHO_POT),
    ("/VRAW+", F, [(45, 44), (37, 44), (37, 56)], ANCHO_POT),
    ("/VRAW+", F, [(37, 56), (37, 88)], ANCHO_POT),
    ("/VRAW+", F, [(45, 44), (52, 44), (52, 48)], ANCHO_POT),
    ("/VRAW+", F, [(52, 44), (78, 44), (78, 52), (84, 52), (84, 56)], ANCHO_POT),
    ("/VRAW+", F, [(37, 76), (52, 76), (52, 80)], ANCHO_POT),
    ("/VRAW+", F, [(52, 76), (78, 76), (78, 84), (84, 84), (84, 88)], ANCHO_POT),

    # --- VRAW-: baja por el canto derecho en F, x=96 ---
    ("/VRAW-", F, [(68, 16.1), (68, 22), (74.5, 22), (74.5, 33)], ANCHO_POT),
    ("/VRAW-", F, [(74.5, 33), (74.5, 37), (96, 37), (96, 112)], ANCHO_POT),
    ("/VRAW-", F, [(96, 112), (86.5, 112), (86.5, 120)], ANCHO_POT),
    ("/VRAW-", F, [(96, 112), (66, 112), (62.2, 112)], ANCHO_POT),
    ("/VRAW-", F, [(66, 112), (66, 108), (42, 108), (42, 120)], ANCHO_POT),

    # --- GND: el arbol. Ramas en B, salvo el enlace de J1.2 (en F, porque en B
    # lo cruzaria SEC_A) y el retorno dedicado. Sale de ESTRELLA y no vuelve. ---
    ("GND", F, [(47, 10), (47, 26), (52.5, 26), (52.5, 33)], ANCHO_POT),
    ("GND", B, [(52.5, 33), (67, 33)], ANCHO_POT),
    # Espina en x=56 y no en 52.5: en 52.5 pasaba justo por encima de D5.1 y
    # D2.1, que viven en x=52. El pasillo entre los pads de las resistencias
    # (54.2) y los de los ceramicos (58) deja 2.1 mm libres; una pista de 1 mm
    # centrada en 56 queda a 0.45 de un lado y 0.65 del otro.
    ("GND", B, [(52.5, 33), (52.5, 40), (56, 40), (56, 122)], ANCHO_POT),
    # rama del carril +12 V
    ("GND", B, [(56, 50), (42, 50), (42, 56)], ANCHO_POT),
    ("GND", B, [(42, 56), (42, 60), (50.5, 60), (50.5, 62)], ANCHO_POT),
    ("GND", B, [(56, 50), (63, 50), (63, 56)], ANCHO_POT),
    ("GND", B, [(63, 50), (86.5, 50), (86.5, 56)], ANCHO_POT),
    ("GND", B, [(63, 56), (63, 60), (66, 60), (66, 70), (62, 70)], ANCHO_POT),
    # rama del carril +5 V
    ("GND", B, [(56, 82), (42, 82), (42, 88)], ANCHO_POT),
    ("GND", B, [(42, 88), (42, 92), (50.5, 92), (50.5, 94)], ANCHO_POT),
    ("GND", B, [(56, 82), (63, 82), (63, 88)], ANCHO_POT),
    ("GND", B, [(63, 82), (86.5, 82), (86.5, 88)], ANCHO_POT),
    ("GND", B, [(63, 88), (63, 94), (66, 94), (66, 102), (62, 102)], ANCHO_POT),
    # rama del carril -12 V
    ("GND", B, [(56, 122), (37, 122), (37, 120)], ANCHO_POT),
    ("GND", B, [(56, 122), (48, 122), (48, 126)], ANCHO_POT),
    ("GND", B, [(56, 122), (58, 122), (58, 120)], ANCHO_POT),
    ("GND", B, [(58, 122), (84, 122), (84, 120)], ANCHO_POT),
    ("GND", B, [(56, 122), (44, 122), (44, 134)], ANCHO_POT),
    # rama de salidas: rodea POR DEBAJO de los conectores (y=146)
    ("GND", B, [(56, 122), (56, 146), (62.5, 146), (62.5, 143)], ANCHO_POT),
    ("GND", B, [(62.5, 146), (65.1, 146), (65.1, 143)], ANCHO_POT),
    ("GND", B, [(56, 139), (42.5, 139), (42.5, 141)], ANCHO_POT),
    ("GND", B, [(42.5, 139), (37.5, 139), (37.5, 141)], ANCHO_POT),
    # RETORNO DEDICADO del +5 V (J6.2) -> estrella, sin tocar ninguna otra rama.
    # sec.10.1 lo exige: el backlight del LCD va conmutado y su corriente no
    # puede compartir camino con la referencia analogica. Sube por el canto
    # derecho (x=98), la unica columna libre de ramas, y cambia a B con una via.
    ("GND", F, [(78.5, 143), (78.5, 138), (98, 138), (98, 45)], ANCHO_POT),
    ("GND", B, [(98, 45), (98, 30), (52.5, 30), (52.5, 33)], ANCHO_POT),

    # --- rieles de salida. El tramo del carril va en F; el bajante hasta los
    # conectores va en B, y cada uno por su columna (90/93/96) elegida para que
    # el que termina mas a la izquierda gire primero y no corte a los otros. ---
    ("+12V", F, [(89.1, 56), (89.1, 66), (48, 66), (48, 62)], ANCHO_POT),
    ("+12V", F, [(58, 66), (58, 56)], ANCHO_POT),
    ("+12V", F, [(58, 56), (58, 52), (62.2, 52), (62.2, 48)], ANCHO_POT),
    ("+12V", F, [(48, 66), (44, 66), (44, 70)], ANCHO_POT),
    ("+12V", B, [(89.1, 56), (97, 60), (97, 146), (67.6, 146), (67.6, 143)], ANCHO_POT),
    ("+5V",  F, [(89.1, 88), (89.1, 98), (48, 98), (48, 94)], ANCHO_POT),
    ("+5V",  F, [(58, 98), (58, 88)], ANCHO_POT),
    ("+5V",  F, [(58, 88), (58, 84), (62.2, 84), (62.2, 80)], ANCHO_POT),
    ("+5V",  F, [(48, 98), (44, 98), (44, 102)], ANCHO_POT),
    ("+5V",  B, [(89.1, 88), (93, 92), (93, 137), (76, 137), (76, 143)], ANCHO_POT),
    ("-12V", F, [(89.1, 120), (89.1, 130), (50.5, 130), (50.5, 126)], ANCHO_POT),
    ("-12V", F, [(63, 130), (63, 120)], ANCHO_POT),
    ("-12V", F, [(63, 130), (63, 126), (52, 126), (52, 112)], ANCHO_POT),
    ("-12V", F, [(63, 130), (62, 130), (62, 134)], ANCHO_POT),
    ("-12V", B, [(89.1, 120), (90, 124), (90, 133), (70, 133), (70, 141), (60, 141), (60, 143)], ANCHO_POT),

    # --- anodos de los LED (girados 180, asi el anodo mira a su resistencia) ---
    ("Net-(D3-A)", F, [(54.2, 70), (59.5, 70)], ANCHO_SEN),
    ("Net-(D6-A)", F, [(54.2, 102), (59.5, 102)], ANCHO_SEN),
    ("Net-(D4-A)", F, [(54.2, 134), (59.5, 134)], ANCHO_SEN),
]

# Cambios de capa a media pista. Solo hace falta uno: el retorno dedicado.
VIAS = [(98.0, 45.0, "GND")]

MOUNTING = [("H1", 11.0, 7.0), ("H2", 93.5, 7.0),
            ("H3", 11.0, 143.5), ("H4", 93.5, 143.5)]
MOUNT_D = 3.2                   # M3, SIN pad de cobre (ver abajo)


def dist_seg(a, b, c, d) -> float:
    """Distancia minima entre el segmento ab y el cd, en mm. 0 si se cortan."""
    def sub(p, q): return (p[0] - q[0], p[1] - q[1])
    def cross(p, q): return p[0] * q[1] - p[1] * q[0]
    def punto_seg(p, u, v):
        vu = sub(v, u)
        L2 = vu[0] ** 2 + vu[1] ** 2
        if L2 == 0:
            return ((p[0] - u[0]) ** 2 + (p[1] - u[1]) ** 2) ** 0.5
        t = max(0.0, min(1.0, ((p[0] - u[0]) * vu[0] + (p[1] - u[1]) * vu[1]) / L2))
        pr = (u[0] + t * vu[0], u[1] + t * vu[1])
        return ((p[0] - pr[0]) ** 2 + (p[1] - pr[1]) ** 2) ** 0.5
    r, s_ = sub(b, a), sub(d, c)
    den = cross(r, s_)
    if den != 0:
        t = cross(sub(c, a), s_) / den
        u = cross(sub(c, a), r) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(punto_seg(a, c, d), punto_seg(b, c, d),
               punto_seg(c, a, b), punto_seg(d, a, b))


def revisar_estrella() -> list[str]:
    """Que GND sea un ARBOL y no una malla.

    Es la afirmacion central de sec.7 y la unica que no se puede comprobar
    mirando el dibujo: un bucle en la masa se ve exactamente igual que una
    rama. Union-find sobre los extremos de los tramos de GND — si un tramo une
    dos nodos que ya estaban conectados, ahi hay un bucle, y por ese bucle la
    corriente de retorno de un carril se cuela en el de otro.

    Ojo: los pads pasantes unen las dos caras, asi que el nodo es la coordenada
    y no (coordenada, capa).
    """
    padre: dict = {}

    def raiz(n):
        while padre[n] != n:
            padre[n] = padre[padre[n]]
            n = padre[n]
        return n

    bucles = []
    for net, _capa, pts, _a in TRACKS:
        if net != "GND":
            continue
        for i in range(len(pts) - 1):
            a = (round(pts[i][0], 2), round(pts[i][1], 2))
            b = (round(pts[i + 1][0], 2), round(pts[i + 1][1], 2))
            for n in (a, b):
                padre.setdefault(n, n)
            ra, rb = raiz(a), raiz(b)
            if ra == rb:
                bucles.append(f"bucle de GND al unir {a} con {b}")
            else:
                padre[ra] = rb
    return bucles


def revisar_pista_pad(board) -> list[str]:
    """Pistas que pasan por encima del pad de OTRA red.

    Esta es la que faltaba. revisar_pistas() solo compara pista contra pista, y
    con eso el trazado salia "limpio" mientras el DRC de KiCad encontraba cinco
    cortocircuitos: la espina de GND cruzando D5.1 y D2.1, el bajante de -12V
    rozando el anodo de D4, y un LED que se habia quedado sin girar. Un pad es
    cobre igual que una pista; no mirarlo era mirar media placa.
    """
    capas = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            c = pad.GetPosition()
            r = max(pad.GetSize().x, pad.GetSize().y) / 2e6
            pads.append((f"{fp.GetReference()}.{pad.GetNumber()}",
                         pad.GetNetname(), c.x / 1e6, c.y / 1e6, r,
                         pad.GetLayerSet().Contains(capas["F.Cu"]),
                         pad.GetLayerSet().Contains(capas["B.Cu"])))
    malos = []
    for net, capa, pts, ancho in TRACKS:
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            for nom, pnet, px, py, r, enF, enB in pads:
                if pnet == net:
                    continue
                if not (enF if capa == "F.Cu" else enB):
                    continue
                d = dist_seg(a, b, (px, py), (px, py)) - r - ancho / 2
                minimo = 2.5 if (es_red(net) or es_red(pnet)) else 0.3
                if d < minimo:
                    malos.append(f"{net} en {capa} a {d:.2f}mm del pad "
                                 f"{nom}[{pnet}] ({a}-{b})")
    return malos


def revisar_pistas() -> list[str]:
    """Cruces y roces entre pistas de redes distintas en la MISMA capa.

    Esto existe porque trazar 16 redes a mano en dos caras es exactamente el
    tipo de geometria que uno cree tener en la cabeza y no tiene. El DRC de
    KiCad lo pillaria igual, pero solo despues de guardar y con un informe que
    hay que leer; aqui sale con el nombre de las dos redes y las coordenadas.
    """
    segs = []
    for net, capa, pts, ancho in TRACKS:
        for i in range(len(pts) - 1):
            segs.append((net, capa, pts[i], pts[i + 1], ancho))
    malos = []
    for i, (n1, c1, a, b, w1) in enumerate(segs):
        for n2, c2, c, d, w2 in segs[i + 1:]:
            if c1 != c2 or n1 == n2:
                continue
            hueco = dist_seg(a, b, c, d) - (w1 + w2) / 2
            minimo = 2.5 if (es_red(n1) or es_red(n2)) else 0.3
            if hueco < minimo:
                malos.append(f"{n1}~{n2} en {c1} a {hueco:.2f}mm "
                             f"({a}-{b} vs {c}-{d})")
    return malos


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
            f"MountingHole_{MOUNT_D}mm_M3")
        assert fp, "no carga la huella del taladro de fijacion"
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        board.Add(fp)

    # --- pistas ---
    capas = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    n_seg = 0
    for net, capa, pts, ancho in TRACKS:
        assert net in netinfo, f"pista de una red que no existe: {net}"
        for i in range(len(pts) - 1):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(pts[i][0]), mm(pts[i][1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(pts[i + 1][0]), mm(pts[i + 1][1])))
            t.SetWidth(mm(ancho))
            t.SetLayer(capas[capa])
            t.SetNet(netinfo[net])
            board.Add(t)
            n_seg += 1
    for x, y, net in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetWidth(mm(1.2))
        v.SetDrill(mm(0.6))
        v.SetNet(netinfo[net])
        board.Add(v)
    print(f"pistas: {n_seg} segmentos en {len(TRACKS)} tramos, {len(VIAS)} vias")

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

    cruces = revisar_pistas()
    print(f"cruces o roces entre pistas: {len(cruces)}")
    for c in cruces[:8]:
        print(f"    {c}")
    bucles = revisar_estrella()
    print(f"bucles en la masa (tiene que ser 0, sec.7): {len(bucles)} {bucles}")
    contra_pad = revisar_pista_pad(board)
    print(f"pistas encima de un pad ajeno: {len(contra_pad)}")
    for c in contra_pad[:8]:
        print(f"    {c}")

    # Los taladros ya no llevan cobre (sec.13: el puente chasis-GND es UNO, el
    # de J5), asi que salen de la medida de barrera de arriba. Pero un separador
    # metalico ahi sigue estando a potencial de chasis, y hay dos en plena
    # franja de red. Se comprueba aparte.
    cerca = []
    for ref, x, y in MOUNTING:
        for nombre, bb in pads_red:
            centro = pcbnew.BOX2I(pcbnew.VECTOR2I(mm(x - MOUNT_D / 2),
                                                  mm(y - MOUNT_D / 2)),
                                  pcbnew.VECTOR2I(mm(MOUNT_D), mm(MOUNT_D)))
            d = distancia_bbox(centro, bb)
            if d < FUGA_MIN:
                cerca.append(f"{ref}~{nombre} a {d:.2f}mm")
    print(f"taladros a menos de {FUGA_MIN} mm de la red: {len(cerca)} {cerca}")

    pcbnew.SaveBoard(PCB, board)
    print(f"guardado {PCB}")

    assert not sin_red, f"pads sin red: {sin_red}"
    assert not fuera, f"piezas fuera del margen: {fuera}"
    assert not solapes, f"piezas montadas una encima de otra: {solapes}"
    assert not sobre_ranura, f"piezas sobre la ranura: {sobre_ranura}"
    assert peor >= FUGA_MIN, (
        f"la barrera de red mide {peor:.2f} mm y hacen falta {FUGA_MIN}: {par}")
    assert not cruces, f"pistas que se cruzan o se rozan: {cruces}"
    assert not contra_pad, f"pistas sobre pads ajenos: {contra_pad}"
    assert not bucles, f"la masa tiene bucles, no es una estrella: {bucles}"
    assert not cerca, f"taladros demasiado cerca de la red: {cerca}"


if __name__ == "__main__":
    sys.exit(main())
