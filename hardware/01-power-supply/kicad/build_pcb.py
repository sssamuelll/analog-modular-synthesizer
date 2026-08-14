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

W, H = 150.0, 200.0             # crece desde 100x150: los disipadores pasan de
                                # 25x25 a 42x38 (SK 129/38,1) y tres en fila
                                # piden 136 mm de ancho. Con la franja de red
                                # VERTICAL harian falta 175; puesta en
                                # HORIZONTAL arriba, caben en 150.
MARGEN = 3.0                    # de cualquier pieza al borde
# La barrera pasa a ser HORIZONTAL: la franja de red va ahora en una fila
# arriba, no en una columna a la izquierda.
Y_BARRERA = 31.0                # eje de la ranura
RANURA_ANCHO = 2.0
RANURA_X0, RANURA_X1 = 10.0, 140.0   # los puentes que quedan sostienen la placa
FUGA_MIN = 6.0                  # cobre de red <-> cobre SELV (sec.14.2)
# Fischer SK 129/38,1 220 (6.5 K/W, 7.7 acostado). La huella TO-220-3_Vertical
# mide 10.6 x 5.0 y no sabe NADA del disipador atornillado: sin esta reserva se
# montan unos encima de otros.
HS_ANCHO, HS_ALTO = 42.0, 38.1

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
    # --- franja de red 230 V, fila HORIZONTAL arriba (y ~ 15) --------------
    # En fila y no en columna: asi la barrera es horizontal y deja los 150 mm
    # de ancho enteros para la fila de disipadores de abajo.
    "J3":  ( 18.0,  15.0,   0),   # entrada de red: L / N / PE
    "F1":  ( 38.0,  12.0,   0),   # portafusible cerrado
    "NT1": ( 58.0,  15.0,   0),   # limitador de inrush
    "RV1": ( 80.0,  15.0,   0),   # el mas grande de la placa: 23 mm de cuerpo
    "J4":  (110.0,  15.0,   0),   # salida al primario de TR1

    # --- entrada del secundario y rectificacion ---------------------------
    "J1":  ( 10.0,  42.0,   0),
    "BR1": ( 32.0,  39.0,   0),
    "TP3": ( 34.0,  77.0,   0),   # +12V, en la columna A
    "TP5": ( 84.0,  77.0,   0),   # +5V, en la columna B

    # --- bulk: DOS por riel (9400 uF). Van los cuatro juntos y pegados al
    # puente para que el lazo de carga sea corto; el punto de estrella vive
    # entre ellos (sec.7). ---------------------------------------------------
    "C1":  ( 10.0,  62.0,   0),
    "C12": ( 28.0,  62.0,   0),
    "C2":  ( 48.0,  62.0,   0),
    "C13": ( 66.0,  62.0,   0),

    # --- los tres carriles van en COLUMNAS, cada uno justo encima de su
    # regulador. En filas horizontales el carril de -12 V tenia que cruzar la
    # placa entera para llegar a su 7912, cortando los otros dos. ------------
    # columna A: +12 V, sobre U1
    "C3":  ( 12.0,  82.0,   0),   # 0.47 uF, entrada del LM2940
    "C5":  ( 28.0,  82.0,   0),   # 100 uF de ESR controlada: ESTABILIDAD
    "C7":  ( 42.0,  82.0,   0),   # 0.1 uF -> se monta junto al conector
    "D1":  ( 18.0,  94.0,   0),
    "R1":  ( 38.0,  94.0,   0),
    "D3":  ( 42.0, 105.0, 180),
    # crowbar del riel de +12 V: en su propia columna, no perdido por ahi
    "Q1":  ( 32.0, 105.0,   0),
    "D7":  ( 14.0, 116.0,   0),
    "R4":  ( 36.0, 116.0,   0),
    "C14": ( 14.0, 126.0,   0),

    # columna B: +5 V, sobre U3
    "C9":  ( 59.0,  82.0,   0),
    "C10": ( 75.0,  82.0,   0),
    "C11": ( 89.0,  82.0,   0),
    "D5":  ( 65.0,  94.0,   0),
    "R3":  ( 85.0,  94.0,   0),
    "D6":  ( 89.0, 105.0, 180),

    # columna C: -12 V, sobre U2
    "C4":  (106.0,  82.0,   0),
    "C6":  (122.0,  82.0,   0),
    "C8":  (136.0,  82.0,   0),   # DNP, pero la huella va puesta
    "D2":  (112.0,  94.0,   0),
    "R2":  (132.0,  94.0,   0),
    "D4":  (136.0, 105.0, 180),

    # --- reguladores en fila, cada uno con sus 42 x 38 mm de disipador ----
    # U2 lleva mica obligatoria: su tab esta a VRAW- (hasta -20 V), no a masa,
    # y desnudo contra el mismo disipador que U1 seria un corto franco.
    "U1":  ( 28.0, 154.0,   0),
    "U3":  ( 75.0, 154.0,   0),
    "U2":  (122.0, 154.0,   0),

    # --- salidas y puntos de prueba, fila de abajo ------------------------
    "J5":  ( 18.0, 182.0,   0),   # faston GND -> chasis (sec.13)
    "J2":  ( 36.0, 182.0,   0),   # bus +12/GND/GND/-12
    "J6":  ( 54.0, 182.0,   0),   # feed de +5 V
    "TP1": ( 44.0,  77.0,   0),   # VRAW+
    "TP4": (128.0,  77.0,   0),   # -12V, en la columna C
    "TP2": (100.0,  77.0,   0),   # VRAW-
    "TP6": ( 68.0,  77.0,   0),   # GND
}

F, B = "F.Cu", "B.Cu"
ANCHO_POT, ANCHO_SEN, ANCHO_RED = 1.0, 0.4, 1.0
ESTRELLA = (17.5, 62.0)        # = C1.2, el bulk del riel positivo (sec.7)
TRACKS = [
    # ===================== lado de red 230 V, todo en F =====================
    # Tres corredores: L y L_TR por ENCIMA de la fila (y=7), L_F y N por debajo
    # (y=20 y y=27). Ninguno cruza a otro y ninguno baja de y=27, lo que deja
    # 12 mm hasta el primer pad SELV.
    ("/L",    F, [(18, 15), (18, 7), (38, 7), (38, 12)], ANCHO_RED),
    ("/L",    F, [(38, 12), (38, 17.1)], ANCHO_RED),
    ("/L_F",  F, [(45.6, 12), (45.6, 17.1)], ANCHO_RED),
    ("/L_F",  F, [(45.6, 17.1), (45.6, 20), (80, 20), (80, 15)], ANCHO_RED),
    ("/L_F",  F, [(58, 20), (58, 15)], ANCHO_RED),
    ("/N",    F, [(23, 15), (23, 27), (110, 27), (110, 15)], ANCHO_RED),
    ("/N",    F, [(90, 27), (90, 15)], ANCHO_RED),
    ("/L_TR", F, [(65.5, 15), (65.5, 7), (115, 7), (115, 15)], ANCHO_RED),

    # ===================== secundario, en B ================================
    # Los dos en B para dejar F entera al abanico de VRAW+/VRAW-, que es donde
    # de verdad aprieta: los cuatro pads de BR1 estan en dos columnas de dos.
    ("/SEC_A", B, [(10, 42), (10, 50), (43, 50), (43, 44.1), (39.6, 44.1)], ANCHO_POT),
    ("/SEC_B", B, [(20, 42), (20, 36), (39.6, 36), (39.6, 39)], ANCHO_POT),

    # ===================== VRAW+ ============================================
    # Sube de BR1.1 y rodea por arriba: bajar recto por x=32 lo llevaria encima
    # de BR1.2, que es VRAW-.
    ("/VRAW+", F, [(32, 39), (32, 34), (5, 34), (5, 58), (10, 58), (10, 62)], ANCHO_POT),
    ("/VRAW+", F, [(10, 58), (28, 58), (28, 62)], ANCHO_POT),
    ("/VRAW+", F, [(10, 62), (10, 72), (12, 72), (12, 82)], ANCHO_POT),
    ("/VRAW+", F, [(28, 62), (28, 68), (44, 68), (44, 77)], ANCHO_POT),   # TP1
    ("/VRAW+", F, [(44, 68), (59, 68), (59, 82)], ANCHO_POT),
    ("/VRAW+", F, [(12, 82), (12, 90), (18, 90), (18, 94)], ANCHO_POT),
    ("/VRAW+", F, [(59, 82), (59, 90), (65, 90), (65, 94)], ANCHO_POT),
    # bajada a los reguladores por los pasillos entre reservas de disipador
    ("/VRAW+", F, [(18, 90), (5, 90), (5, 148), (28, 148), (28, 154)], ANCHO_POT),
    ("/VRAW+", F, [(65, 90), (53, 90), (53, 148), (75, 148), (75, 154)], ANCHO_POT),

    # ===================== VRAW- ============================================
    ("/VRAW-", F, [(32, 44.1), (32, 52), (73.5, 52), (73.5, 62)], ANCHO_POT),
    ("/VRAW-", F, [(55.5, 52), (55.5, 62)], ANCHO_POT),
    ("/VRAW-", F, [(73.5, 62), (73.5, 68), (100, 68), (100, 77)], ANCHO_POT),   # TP2
    ("/VRAW-", F, [(100, 68), (108.5, 68), (108.5, 82)], ANCHO_POT),
    ("/VRAW-", F, [(108.5, 82), (108.5, 88), (122.2, 88), (122.2, 94)], ANCHO_POT),
    ("/VRAW-", F, [(108.5, 88), (101, 88), (101, 148), (124.5, 148), (124.5, 154)], ANCHO_POT),

    # ===================== carril +12 V =====================================
    # Sube del regulador por el pasillo derecho de su reserva y reparte por
    # arriba: asi no corta el anodo del LED, que vive en y=99.
    ("+12V", F, [(33.1, 154), (33.1, 144), (50, 144), (50, 86)], ANCHO_POT),
    ("+12V", F, [(50, 86), (42, 86), (42, 82)], ANCHO_POT),
    ("+12V", F, [(50, 86), (36, 86), (36, 77), (34, 77)], ANCHO_POT),  # TP3
    ("+12V", F, [(36, 86), (28, 86), (28, 82)], ANCHO_POT),
    ("+12V", F, [(36, 86), (38, 90), (38, 94)], ANCHO_POT),
    ("+12V", F, [(28, 86), (28.2, 90), (28.2, 94)], ANCHO_SEN),
    # al crowbar: pista fina, que las patas del TO-92 estan a 1.27 mm
    ("+12V", F, [(28, 86), (24, 86), (24, 100), (32, 100), (32, 105)], ANCHO_SEN),
    ("+12V", F, [(24, 100), (10, 100), (10, 116), (14, 116)], ANCHO_SEN),
    ("+12V", B, [(33.1, 154), (33.1, 170), (43.6, 170), (43.6, 182)], ANCHO_POT),

    # ===================== carril +5 V ======================================
    ("+5V", F, [(80.1, 154), (80.1, 144), (97, 144), (97, 86)], ANCHO_POT),
    ("+5V", F, [(97, 86), (89, 86), (89, 82)], ANCHO_POT),
    ("+5V", F, [(97, 86), (83, 86), (83, 81), (84, 81), (84, 77)], ANCHO_POT),  # TP5
    ("+5V", F, [(83, 86), (75, 86), (75, 82)], ANCHO_POT),
    ("+5V", F, [(83, 86), (85, 90), (85, 94)], ANCHO_POT),
    ("+5V", F, [(75, 86), (75.2, 90), (75.2, 94)], ANCHO_SEN),
    ("+5V", B, [(80.1, 154), (80.1, 170), (54, 170), (54, 182)], ANCHO_POT),

    # ===================== carril -12 V =====================================
    ("-12V", F, [(127.1, 154), (127.1, 144), (146, 144), (146, 86)], ANCHO_POT),
    ("-12V", F, [(146, 86), (141, 86), (141, 82)], ANCHO_POT),
    ("-12V", F, [(146, 86), (130, 86), (130, 81), (128, 81), (128, 77)], ANCHO_POT),  # TP4
    ("-12V", F, [(146, 112), (136, 112), (136, 105)], ANCHO_POT),
    ("-12V", F, [(130, 86), (124.5, 86), (124.5, 82)], ANCHO_SEN),
    ("-12V", F, [(146, 86), (146, 112), (112, 112), (112, 94)], ANCHO_POT),
    # el unico que va en F abajo: cruza toda la placa y en B chocaria con los
    # otros dos abanicos
    ("-12V", F, [(127.1, 154), (127.1, 176), (36, 176), (36, 182)], ANCHO_POT),

    # ===================== anodos de LED y gate del SCR =====================
    ("Net-(D3-A)", F, [(48.16, 94), (48.16, 99), (39.46, 99), (39.46, 105)], ANCHO_SEN),
    ("Net-(D6-A)", F, [(95.16, 94), (95.16, 99), (86.46, 99), (86.46, 105)], ANCHO_SEN),
    ("Net-(D4-A)", F, [(142.16, 94), (142.16, 99), (133.46, 99), (133.46, 105)], ANCHO_SEN),
    ("Net-(D7-A)", F, [(34.54, 105), (34.54, 111), (36, 111), (36, 116)], ANCHO_SEN),
    ("Net-(D7-A)", F, [(36, 111), (21.6, 111), (21.6, 116)], ANCHO_SEN),
    ("Net-(D7-A)", F, [(21.6, 116), (21.6, 122), (14, 122), (14, 126)], ANCHO_SEN),

    # ===================== GND: el arbol, todo en B =========================
    # Estrella en C1.2 (sec.7). Cada rama muere en su grupo y no vuelve.
    ("GND", B, [(15, 42), (15, 36), (6, 36), (6, 66), (14, 66), (14, 62), (17.5, 62)], ANCHO_POT),
    ("GND", B, [(17.5, 62), (17.5, 74), (35.5, 74), (35.5, 62)], ANCHO_POT),
    ("GND", B, [(35.5, 74), (48, 74), (48, 62)], ANCHO_POT),
    ("GND", B, [(48, 74), (68, 74), (68, 77)], ANCHO_POT),          # TP6
    ("GND", B, [(48, 74), (66, 74), (66, 62)], ANCHO_POT),
    # --- rama de la columna A (+12 V) y el crowbar ---
    ("GND", B, [(17.5, 74), (20, 74), (20, 130)], ANCHO_POT),
    ("GND", B, [(20, 82), (17, 82)], ANCHO_POT),
    ("GND", B, [(20, 88), (30.5, 88), (30.5, 82)], ANCHO_POT),
    ("GND", B, [(30.5, 88), (47, 88), (47, 82)], ANCHO_POT),
    ("GND", B, [(20, 110), (37.08, 110), (37.08, 105)], ANCHO_SEN),
    ("GND", B, [(37.08, 110), (42, 110), (42, 105)], ANCHO_POT),
    ("GND", B, [(42, 110), (46.16, 110), (46.16, 116)], ANCHO_POT),
    ("GND", B, [(20, 126), (19, 126)], ANCHO_POT),
    ("GND", B, [(20, 130), (20, 160), (30.5, 160), (30.5, 154)], ANCHO_POT),
    # --- rama de la columna B (+5 V). El bajante va por x=57, no por x=64:
    # en 64 pasaba a 1 mm del pad de D5.1, que es VRAW+.
    ("GND", B, [(48, 74), (48, 84), (57, 84), (57, 130)], ANCHO_POT),
    ("GND", B, [(57, 84), (64, 84), (64, 82)], ANCHO_POT),
    ("GND", B, [(64, 84), (77.5, 84), (77.5, 82)], ANCHO_POT),
    ("GND", B, [(77.5, 84), (94, 84), (94, 82)], ANCHO_POT),
    ("GND", B, [(57, 110), (89, 110), (89, 105)], ANCHO_POT),
    ("GND", B, [(57, 130), (57, 160), (77.5, 160), (77.5, 154)], ANCHO_POT),
    # --- rama de la columna C (-12 V) ---
    ("GND", B, [(66, 74), (114, 74), (114, 78), (106, 78), (106, 82)], ANCHO_POT),
    ("GND", B, [(114, 78), (118, 78), (118, 84), (122, 84), (122, 82)], ANCHO_POT),
    ("GND", B, [(118, 84), (136, 84), (136, 82)], ANCHO_POT),
    ("GND", B, [(118, 84), (118, 92), (132, 92), (132, 94)], ANCHO_POT),
    ("GND", B, [(118, 92), (118, 160), (122, 160), (122, 154)], ANCHO_POT),
    # --- rama de salidas: bus y faston de chasis. NO incluye J6.2, que va por
    # su cuenta (retorno dedicado del +5 V, sec.10.1).
    ("GND", B, [(20, 130), (12, 130), (12, 186), (15.5, 186), (15.5, 182)], ANCHO_POT),
    ("GND", B, [(15.5, 186), (20.5, 186), (20.5, 182)], ANCHO_POT),
    ("GND", B, [(20.5, 186), (38.5, 186), (38.5, 182)], ANCHO_POT),
    ("GND", B, [(38.5, 186), (41.1, 186), (41.1, 182)], ANCHO_POT),
    # --- RETORNO DEDICADO del +5 V (J6.2) -> estrella. Sube por el canto
    # derecho en F, la unica columna sin ramas de masa, y entra a la estrella
    # por su propia via sin haber tocado ninguna otra rama (sec.10.1).
    ("GND", F, [(56.5, 182), (56.5, 188), (148, 188), (148, 58)], ANCHO_POT),
    ("GND", B, [(148, 58), (148, 54), (20, 54), (20, 58), (17.5, 58), (17.5, 62)], ANCHO_POT),
]

VIAS = [(148.0, 58.0, "GND")]

MOUNTING = [("H1", 7.0, 7.0), ("H2", 143.0, 7.0),
            ("H3", 7.0, 193.0), ("H4", 143.0, 193.0)]
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

    a, b = Y_BARRERA - RANURA_ANCHO / 2, Y_BARRERA + RANURA_ANCHO / 2
    for x1, y1, x2, y2 in [(RANURA_X0, a, RANURA_X1, a),
                           (RANURA_X1, a, RANURA_X1, b),
                           (RANURA_X1, b, RANURA_X0, b),
                           (RANURA_X0, b, RANURA_X0, a)]:
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
        a, h = HS_ANCHO / 2, HS_ALTO / 2
        for x1, y1, x2, y2 in [(x - a, y - h, x + a, y - h),
                               (x + a, y - h, x + a, y + h),
                               (x + a, y + h, x - a, y + h),
                               (x - a, y + h, x - a, y - h)]:
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
            bb = pcbnew.BOX2I(pcbnew.VECTOR2I(p.x - mm(HS_ANCHO / 2),
                                              p.y - mm(HS_ALTO / 2)),
                              pcbnew.VECTOR2I(mm(HS_ANCHO), mm(HS_ALTO)))
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
        pcbnew.VECTOR2I(mm(RANURA_X0), mm(Y_BARRERA - RANURA_ANCHO / 2)),
        pcbnew.VECTOR2I(mm(RANURA_X1 - RANURA_X0), mm(RANURA_ANCHO)))
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
