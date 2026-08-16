"""Genera sam17-power-v2.kicad_pcb: contorno, barrera de red, redes y colocacion.

Fuente: docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md (sec.6, layout
y ruido) y el netlist que exporta kicad-cli desde sam17-power-v2.kicad_sch.

Uso — igual que la v1, este script va con pcbnew directo (nada de
KiCAD-MCP-Server), asi que hay que llamarlo con el Python de KiCad:

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Herencia de la v1 (hardware/01-power-supply/kicad/build_pcb.py): contorno()
con la ranura de barrera, reserva_disipadores(), reglas(),
revisar_estrella(), revisar_pista_pad(), revisar_pistas(), dist_seg(), mm(),
leer_netlist() y distancia_bbox() se traen SIN CAMBIOS. Placa, taladros de
fijacion y ranura de barrera son literalmente los mismos que en v1 (150x200,
misma ranura x=10..140 / y=30..32).

Esta es la Tarea 7 del plan v2: PLACEMENT completo por islas, TODAVIA SIN
RUTAS (eso es la Tarea 8, sobre este mismo fichero). TRACKS y VIAS quedan
vacios a proposito: revisar_pistas(), revisar_pista_pad() y
revisar_estrella() devuelven "sin problemas" de forma trivial, que es lo
correcto para esta fase.

Lo que cambia de verdad respecto a v1 (topologia de la GOAT, ver spec sec.3 y
6):
  - Pre-reguladores U1 (LM2941, +13.1V) y U2 (LM2991, -12.9V) en vez de los
    reguladores finales de v1: alimentan una PAREJA de LT3045/LT3094 cada uno
    (U4+U5 para +12V, U6+U7 para -12V), que son los que de verdad regulan el
    riel final. +12V/-12V "finales" nacen en esa pareja, no en U1/U2.
  - Cuatro checks nuevos (Tarea 7, Paso 3): revisar_smd_cara (ensamblaje a
    una cara), revisar_isla_referencia (GNDREF solo se toca con GND en
    JP1), revisar_diagonal (el lazo de rectificacion lejos de la isla
    ultra) y revisar_borde_ceramicos (ceramicos de precision lejos del
    borde que mas flexa).
  - Isla GNDREF: la masa de referencia analogica (SET/OUTS/divisores de los
    LT) se une a GND de potencia en UN SOLO punto, JP1 (spec sec.6.3). Su
    rectangulo de colocacion es ISLA_REF (mas abajo, con la decision de
    diseno documentada donde se define).
"""
from __future__ import annotations

import os
import re
import sys

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power-v2.kicad_pcb")
NET = os.path.join(DIR, "sam17-power-v2.net")
STOCK = os.environ.get("KICAD_FOOTPRINTS",
                       r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
# sam17.pretty es de la v1: se comparte por fp-lib-table (ver ese fichero en
# esta misma carpeta), no se duplica.
LOCAL = os.path.join(DIR, "..", "..", "kicad", "sam17.pretty")

W, H = 150.0, 200.0             # misma placa que v1: los disipadores TO-220
                                # (U1/U2/U3, ahora pre-reguladores) siguen
                                # pidiendo 42x38.1 mm cada uno.
MARGEN = 3.0                    # de cualquier pieza al borde
Y_BARRERA = 31.0                # eje de la ranura, identico a v1
RANURA_ANCHO = 2.0
RANURA_X0, RANURA_X1 = 10.0, 140.0
FUGA_MIN = 6.0                  # cobre de red <-> cobre SELV (heredado v1)
# Fischer SK 129/38,1 220, igual que v1. U1/U2 ahora son pre-reguladores
# (LM2941/LM2991) pero sobre el MISMO footprint TO-220-5 que llevaban en v1
# (donde eran los reguladores finales), asi que la reserva no cambia.
HS_ANCHO, HS_ALTO = 42.0, 38.1

# Redes del lado de red (identico a v1). J7 (nuevo: deriva a la SMPS digital
# externa, spec sec.7) cuelga de /L_F y /N, asi que ya cae en NETS_RED sin
# tocar el set.
NETS_RED = {"L", "L_F", "L_TR", "N", "PE"}


def es_red(net: str) -> bool:
    return net.lstrip("/") in NETS_RED


# ref -> (x, y, rotacion). Medido contra los footprints reales del netlist
# v2 (ver commit que introduce este fichero para el detalle mm a mm).
#
# Mapa de zonas (y crece hacia abajo, igual que v1):
#   y < 30            franja de red 230 V: J3 F1 NT1 RV1 J4 J7
#   y 30..32           ranura de la barrera (RANURA_X0..RANURA_X1)
#   y 35..80  x<80      lazo de rectificacion + bulk: J1, BR1, C1/C12/C2/C13
#                       — el PEOR RADIADOR de la placa (spec sec.6.4)
#   y 72..85            fila de puntos de prueba: VRAW+/-, +13V1/-12V9, GND
#   y 82..107            columnas de soporte de cada pre-reg/regulador THT
#                       (entrada/salida/proteccion de U1, U3, U2)
#   y 111..119          banda libre ancho completo: indicador+crowbar del
#                       riel +12V final (D3/R1, D4/R2, Q1/D7/R4/C14) y sus
#                       puntos de prueba TP3/TP4 (nacen en la isla ultra,
#                       no en U1/U2 como en v1)
#   y 143 (+-19.05)      muralla TO-220: U1 - U3 - U2, cada uno con su
#                       reserva de disipador 42x38.1 (igual criterio v1)
#   y 163..198           ISLA ULTRA + isla GNDREF, en la diagonal OPUESTA
#                       al lazo de rectificacion (spec sec.6.4), con la
#                       muralla de TO-220 de por medio. Aqui viven U4-U7,
#                       el ballast, C_SET, los C in/out, D8-D11, JP1, los
#                       divisores de ajuste de U1/U2 (acercados, ver
#                       comentario junto a R5) y el bus de salida J2/J6/J5.
PLACEMENT = {
    # --- franja de red 230 V, fila horizontal arriba (identica a v1 + J7) --
    "J3":  ( 18.0,  15.0,   0),   # entrada de red: L / N / PE
    "F1":  ( 38.0,  12.0,   0),   # portafusible cerrado, 1.6A T en v2
    "NT1": ( 58.0,  15.0,   0),   # limitador de inrush
    "RV1": ( 80.0,  15.0,   0),   # MOV, el mas grande de la placa
    "J4":  (108.0,  15.0,   0),   # salida al primario de TR1
    "J7":  (128.0,  15.0,   0),   # NUEVO: deriva a la SMPS digital IRM-15-5

    # --- lazo de rectificacion + bulk, esquina x baja / y baja (SELV) -----
    # Identico a v1: es el peor radiador de la placa (spec sec.6.4), se
    # mantiene compacto y lo mas lejos posible de la isla ultra.
    "J1":  ( 10.0,  42.0,   0),   # entrada del secundario (toma central)
    "BR1": ( 32.0,  39.0,   0),
    "C1":  ( 10.0,  62.0,   0),
    "C12": ( 28.0,  62.0,   0),
    "C2":  ( 48.0,  62.0,   0),
    "C13": ( 66.0,  62.0,   0),

    # --- fila de puntos de prueba ------------------------------------------
    # TP1/TP2/TP6 igual que v1 (VRAW+/VRAW-/GND, antes del pre-reg). TP7/TP8
    # son nuevos: salida de los pre-reg (+13V1/-12V9), donde v1 tenia
    # TP3/TP4 porque ahi SI eran los rieles finales. TP3/TP4/TP5 se mueven
    # mas abajo: en v2 +12V/-12V "final" nacen en la pareja LT3045/LT3094
    # (isla ultra), no en el pre-reg.
    "TP7": ( 32.0,  74.0,   0),   # +13V1 (salida de U1, entrada de U4/U5)
    "TP1": ( 44.0,  77.0,   0),   # VRAW+
    "TP6": ( 68.0,  77.0,   0),   # GND
    "TP2": (100.0,  77.0,   0),   # VRAW-
    "TP8": (126.0,  74.0,   0),   # -12V9 (salida de U2, entrada de U6/U7)

    # --- columna de soporte de U1 (pre-reg +13.1V) -------------------------
    "C27": ( 12.0,  82.0,   0),   # 0.47uF, entrada de U1
    "C17": ( 28.0,  82.0,   0),   # salida ESR-controlada (ventana sec.1.1)
    "D12": ( 18.0,  94.0,   0),   # out->in, protege contra el bulk aguas abajo

    # --- columna de soporte de U3 (LM7805, +5V FINAL — sin cambios v1) ----
    "C9":  ( 59.0,  82.0,   0),
    "C10": ( 75.0,  82.0,   0),
    "C11": ( 89.0,  82.0,   0),
    "D5":  ( 65.0,  94.0,   0),
    "R3":  ( 85.0,  94.0,   0),
    "D6":  ( 89.0, 105.0, 180),
    "TP5": ( 84.0,  77.0,   0),   # +5V, un solo paso, no se mueve (v1)

    # --- columna de soporte de U2 (pre-reg -12.9V) -------------------------
    "C28": (106.0,  82.0,   0),   # entrada de U2
    "C18": (122.0,  82.0,   0),   # salida ESR-controlada (ventana sec.1.2)
    "D13": (112.0,  94.0,   0),   # out->in

    # --- muralla TO-220: cada uno con su reserva de disipador de 42x38.1 --
    # Subida a y=143 (v1 la tenia en 154) para dejar sitio de sobra a la
    # isla ultra por debajo sin invadir su reserva de disipador (que llega
    # hasta y=162.05).
    "U1":  ( 28.0, 143.0,   0),
    "U3":  ( 75.0, 143.0,   0),
    "U2":  (122.0, 143.0,   0),

    # --- banda intermedia, ancho completo (y 111-119) ----------------------
    # Entre las columnas de soporte (terminan en y~107) y la muralla TO-220
    # (reserva de disipador desde y=123.95) queda una franja de la placa
    # entera sin usar. Ahi caben, con pista de sobra, el indicador+crowbar
    # del riel +12V FINAL (D3/R1, D4/R2, Q1/D7/R4/C14 — protege el mismo
    # riel, abs max +-18V de los CEM3340/AS3340) y sus puntos de prueba
    # (TP3/TP4, que en v2 nacen en la isla ultra y no en U1/U2 como en v1).
    "Q1":  ( 10.0, 111.0,   0),
    "D7":  ( 26.0, 111.0,   0),
    "D3":  ( 42.0, 111.0, 180),
    "D4":  ( 58.0, 111.0, 180),
    "TP3": ( 74.0, 111.0,   0),   # +12V (final, nace en la isla ultra)
    "TP4": ( 90.0, 111.0,   0),   # -12V (final, nace en la isla ultra)
    "R4":  ( 10.0, 119.0,   0),
    "C14": ( 26.0, 119.0,   0),
    "R1":  ( 42.0, 119.0,   0),
    "R2":  ( 58.0, 119.0,   0),
    # TP5 (+5V) no se mueve: +5V sigue siendo de un solo paso, U3 (arriba).

    # --- bus de salida + divisores, junto a la isla ultra ------------------
    # spec: "junto a J2/J6". J2/J6 en la franja libre delante de la isla
    # ultra (x baja de esa esquina), J5 en la esquina x baja / y alta.
    #
    # DECISION DE DISENO — R5/RV2/R6 y R7/RV3/R8 (spec sec.6.3, brief Tarea 7
    # Paso 2): R6 y R8 son el retorno de estos divisores y viven en GNDREF,
    # no en GND de potencia. Si se dejan "naturalmente" pegados a U1/U2 en
    # la muralla (x=28 y x=122, en extremos opuestos de la fila), ISLA_REF
    # tendria que estirarse casi todo el ancho de la placa para envolver a
    # los dos, y dejaria de ser una isla. Se ACERCAN los divisores enteros
    # (R5+RV2+R6 y R7+RV3+R8) a la isla ultra en su lugar: la referencia de
    # U1/U2 no es sub-uV (eso lo exige el SET del LT3045/LT3094, no el ADJ
    # del LM2941/LM2991), asi que un tramo de pista mas largo hasta el ADJ
    # no cuesta nada de ruido real, y R6/R8 quedan dentro de ISLA_REF (mas
    # abajo, junto a R9/R10/C15/C16/JP1).
    "J6":  ( 40.0, 172.0,   0),   # feed +5V
    "J2":  ( 60.0, 172.0,   0),   # bus +12/GND/GND/-12
    "J5":  ( 22.0, 190.0,   0),   # faston GND->chasis, esquina x baja
    "R5":  ( 35.0, 182.0,   0),
    "RV2": ( 57.0, 182.0,   0),
    "R6":  ( 77.0, 182.0,   0),
    # AJUSTE DE PLACEMENT (orquestador, review Tarea 7): la fila R7/RV3/R8
    # quedaba a ~87 mm del pin ADJ de U2 -- la traza de alta impedancia de
    # verdad no es la de R7 (R7 solo toca -12V9, un riel de baja
    # impedancia), es Net-(U2-ADJ): RV3.1 + R8.2 + U2.1(ADJ), sec.6.3/6.1
    # del netlist Tarea 6. R8/RV3 (el nodo de ajuste) se reespejan al canal
    # vertical virgen entre el disipador de U2 (borde derecho x=143) y el
    # margen de placa (x=147) -- NO es un hueco dentro de la rejilla ya
    # empaquetada de la isla ultra (esa rejilla llena x=89..138 fila a fila
    # sin huecos, verificado contra el .kicad_pcb real). Giradas 90 grados
    # (eje largo en Y) para caber en los 4 mm libres a la derecha del
    # disipador. R8 ancla (pin1=GNDREF) DENTRO de ISLA_REF (x2 ensanchado a
    # 147 mas abajo); su pin2 (ADJ) sale girado hacia ARRIBA del ancla y
    # queda a ~29 mm de U2.ADJ sin necesitar que el cuerpo entero de R8 este
    # dentro de la isla (solo el pad de GNDREF importa para la zona).
    # R7 (la pata de -12V9, no sensible) vuelve al hueco que R8 dejo libre
    # junto a R6: mismo canal x=74..89 de la isla, sin espejar de verdad
    # porque no hace falta -- no es la traza que preocupaba al review.
    "R8":  (145.2, 170.0,  90),   # pin1 GNDREF (ancla) abajo, pin2 ADJ arriba
    "RV3": (144.0, 175.0,  90),
    "R7":  ( 77.0, 192.0,   0),   # hueco que deja R8 al moverse; -12V9, no critico

    # --- ISLA ULTRA: pareja +12.000V (U4/U5, LT3045) -----------------------
    "U4":  ( 92.0, 168.0,   0),
    "D8":  (102.0, 168.0,   0),   # TVS +13V1->GND
    "U5":  (112.0, 168.0,   0),
    "R11": ( 92.0, 174.0,   0),   # ILIM de U4 (Kelvin a su propio GND)
    "R9":  (102.0, 174.0,   0),   # SET, compartida por U4 y U5
    "R12": (112.0, 174.0,   0),   # ILIM de U5
    "C23": ( 92.0, 180.0,   0),   # OUT de U4 (antes del ballast)
    "D10": (102.0, 180.0,   0),   # schottky +12V->+13V1
    "C24": (112.0, 180.0,   0),   # OUT de U5
    "R15": ( 92.0, 186.0,   0),   # ballast de U4 -> +12V
    "C15": (102.0, 186.0,   0),   # SET cap (compartida, baja fuga)
    "R16": (112.0, 186.0,   0),   # ballast de U5 -> +12V
    "C19": ( 92.0, 192.0,   0),   # entrada de U4 (+13V1)
    "C20": (112.0, 192.0,   0),   # entrada de U5

    # --- ISLA ULTRA: pareja -12.000V (U6/U7, LT3094) -----------------------
    "U6":  (120.0, 168.0,   0),
    "D9":  (128.0, 168.0,   0),   # TVS GND->-12V9
    "U7":  (136.0, 168.0,   0),
    "R13": (120.0, 174.0,   0),   # ILIM de U6
    "R10": (128.0, 174.0,   0),   # SET, compartida por U6 y U7
    "R14": (136.0, 174.0,   0),   # ILIM de U7
    "C25": (120.0, 180.0,   0),   # OUT de U6 (antes del ballast)
    "D11": (128.0, 180.0,   0),   # schottky -12V->-12V9
    "C26": (136.0, 180.0,   0),   # OUT de U7
    "R17": (120.0, 186.0,   0),   # ballast de U6 -> -12V
    "C16": (128.0, 186.0,   0),   # SET cap (compartida, baja fuga)
    "R18": (136.0, 186.0,   0),   # ballast de U7 -> -12V
    "C21": (120.0, 192.0,   0),   # entrada de U6 (-12V9)
    "C22": (136.0, 192.0,   0),   # entrada de U7

    # --- puente unico GNDREF<->GND, entre las dos parejas ------------------
    "JP1": (116.0, 174.0,   0),
}

# Rectangulo de colocacion de la isla GNDREF (x1, y1, x2, y2), en mm. Envuelve
# con margen los 5 refs cuyos pads tocan la red GNDREF (R9.2, C15.2, R10.2,
# C16.2, R6.2, R8.1 — netlist Tarea 6) mas JP1, el unico puente admitido a
# GND (revisar_isla_referencia). x1=74 deja a R6/R8 (anclados en x=77,
# cuerpo desde x=75.9) justo dentro; x2 cubre R10/C16 (anclados en x=128,
# cuerpo hasta x=130.3). El cobre de esta isla se dibuja en la Tarea 8 como
# zona sobre este mismo rectangulo.
#
# x2 ENSANCHADO de 139.0 a 147.0 en la Tarea 8 (ajuste de placement pedido
# por el orquestador): R8 se reespejo al canal libre x=143..147, pegado al
# canto derecho de la placa (ver comentario junto a su PLACEMENT), para
# acercar el nodo de ajuste de U2 en vez de dejarlo a 87 mm cruzando la
# placa. R8.1 (GNDREF) vive ahora en ese canal, asi que la isla tiene que
# alcanzarlo o su pad se queda fuera de la zona de cobre GNDREF (sin
# conexion). 147.0 = W - MARGEN: la zona llega hasta el mismo limite que ya
# respetan los componentes, no mas alla.
ISLA_REF = (74.0, 163.0, 147.0, 198.0)

F, B = "F.Cu", "B.Cu"
ANCHO_POT, ANCHO_SEN, ANCHO_RED = 1.0, 0.4, 1.0
# Sin rutas todavia (Tarea 8 rutea sobre este placement): TRACKS y VIAS
# vacios hacen que revisar_pistas(), revisar_pista_pad() y
# revisar_estrella() devuelvan "sin problemas" de forma trivial — correcto
# para esta fase (brief Tarea 7, Paso 4).
TRACKS: list[tuple[str, str, list[tuple[float, float]], float]] = []
VIAS: list[tuple[float, float, str]] = []

MOUNTING = [("H1", 7.0, 7.0), ("H2", 143.0, 7.0),
            ("H3", 7.0, 193.0), ("H4", 143.0, 193.0)]
MOUNT_D = 3.2                   # M3, SIN pad de cobre (igual que v1)


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
    """Que GND sea un ARBOL y no una malla (heredado v1, sec.7).

    Union-find sobre los extremos de los tramos de GND. Con TRACKS vacio (no
    hay rutas todavia) esto es un no-op que devuelve [] — correcto: la
    Tarea 8 es quien rutea y quien de verdad ejercita este check.
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
    """Pistas que pasan por encima del pad de OTRA red (heredado v1).

    Con TRACKS vacio no hay nada que revisar todavia: [] trivial, correcto.
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

    Heredado v1. Con TRACKS vacio, [] trivial — correcto para esta fase.
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
    """Del .net saca ref -> huella y (ref, pad) -> red. Heredado v1 sin cambios."""
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
    """Borde exterior + la ranura de la barrera, los dos en Edge.Cuts.

    Heredado v1 sin cambios: misma placa, misma ranura.
    """
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
    """Marca en F.Fab el cuadrado que ocupa cada disipador (heredado v1).

    U1/U2/U3 son ahora los pre-reguladores (LM2941/LM2991/LM7805) pero sobre
    el mismo footprint TO-220 que llevaban en v1, asi que la reserva de
    disipador no cambia de criterio.
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
    """Separacion entre dos cajas, 0 si se tocan. En mm. Heredado v1."""
    dx = max(0, max(a.GetLeft() - b.GetRight(), b.GetLeft() - a.GetRight()))
    dy = max(0, max(a.GetTop() - b.GetBottom(), b.GetTop() - a.GetBottom()))
    return (dx * dx + dy * dy) ** 0.5 / 1e6


def bbox_de(board, refs: list[str]) -> pcbnew.BOX2I:
    """Caja que envuelve la huella de cada ref en refs (brief Tarea 7)."""
    caja = pcbnew.BOX2I()
    for ref in refs:
        caja.Merge(board.FindFootprintByReference(ref).GetBoundingBox())
    return caja


def revisar_smd_cara(board) -> list[str]:
    """Todo SMD montado en F.Cu: ensamblaje a una sola cara (brief Tarea 7)."""
    males = []
    for fp in board.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_SMD and fp.GetLayer() != pcbnew.F_Cu:
            males.append(f"{fp.GetReference()} es SMD y no esta en F.Cu (ensamblaje una cara)")
    return males


def revisar_isla_referencia(board) -> list[str]:
    """GNDREF y GND solo se tocan dentro de JP1, y todo GNDREF vive en su isla.

    La parte de puentes es topologica (viene del netlist, no del placement):
    JP1 es, por diseno, el UNICO footprint cuyos pads pisan a la vez GNDREF y
    GND (spec sec.6.3). La parte de pistas es sobre ISLA_REF; con TRACKS
    vacio (Tarea 7, sin rutas todavia) no hay nada que revisar ahi — la
    Tarea 8 es quien la ejercita de verdad al rutear GNDREF dentro de este
    rectangulo.
    """
    # Los nombres locales del netlist llevan la barra de KiCad ("/GNDREF");
    # los power symbols no ("GND"). Mismo criterio que es_red() mas arriba:
    # se normaliza quitando la barra antes de comparar.
    males, puentes = [], []
    for fp in board.GetFootprints():
        nets = {p.GetNetname().lstrip("/") for p in fp.Pads()}
        if {"GNDREF", "GND"} <= nets:
            puentes.append(fp.GetReference())
    if puentes != ["JP1"]:
        males.append(f"puentes GNDREF-GND: {puentes} (debe ser exactamente ['JP1'])")
    x1, y1, x2, y2 = ISLA_REF
    for tr in board.GetTracks():
        if tr.GetNetname().lstrip("/") == "GNDREF":
            for p in (tr.GetStart(), tr.GetEnd()):
                if not (mm(x1) <= p.x <= mm(x2) and mm(y1) <= p.y <= mm(y2)):
                    males.append(f"pista GNDREF fuera de la isla en ({p.x/1e6:.1f}, {p.y/1e6:.1f})")
    return males


def revisar_diagonal(board) -> list[str]:
    """El peor radiador (lazo de rectificacion) lejos de la isla ultra (spec sec.6.4)."""
    lazo = bbox_de(board, ["BR1", "C1", "C2", "C12", "C13"])
    ultra = bbox_de(board, ["U4", "U5", "U6", "U7", "R9", "R10", "C15", "C16"])
    # distancia_bbox() ya devuelve mm (heredada de v1: divide por 1e6 antes
    # de devolver). El umbral y el mensaje comparan/imprimen en mm
    # directamente, sin volver a pasar por mm()/1e6.
    d = distancia_bbox(lazo, ultra)
    return [] if d >= 80 else [f"lazo rectificador a {d:.0f} mm de la isla ultra (< 80)"]


def revisar_borde_ceramicos(board) -> list[str]:
    """Un ceramico es un microfono piezoelectrico en un cajon que vibra (spec sec.6.5)."""
    males = []
    borde = board.GetBoardEdgesBoundingBox()
    for ref in ["C15", "C16", "C23", "C24", "C25", "C26"]:
        fp = board.FindFootprintByReference(ref)
        b = fp.GetBoundingBox()
        margen = min(b.GetLeft() - borde.GetLeft(), borde.GetRight() - b.GetRight(),
                     b.GetTop() - borde.GetTop(), borde.GetBottom() - b.GetBottom())
        if margen < mm(10):
            males.append(f"{ref} a {margen/1e6:.1f} mm del borde (< 10)")
    return males


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
        # El campo Value hereda de la libreria el nombre COMPLETO de la
        # huella (p.ej. "DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm"), visible y
        # sin reposicionar: GetBoundingBox() SIN argumentos (el que usan
        # bbox_de() y revisar_borde_ceramicos) lo cuenta, e infla la caja de
        # piezas SMD chicas hasta decenas de mm. No es placement real, es
        # texto de serigrafia que ademas nadie quiere impreso en la placa
        # (BOM ya trae el valor de cada ref). Se oculta aqui, para todas las
        # huellas, no solo las nuevas de v2.
        fp.Value().SetVisible(False)
        board.Add(fp)
        for pad in fp.Pads():
            # Huellas DFN con EP: el generador estandar de KiCad parte la
            # pasta del EP en varios sub-pads SOLO DE PASTA (F.Paste, sin
            # cobre) para no imprimir un bloque grande de estano — llevan
            # numero de pad vacio y no representan un pin del netlist. Si no
            # estan en una capa de cobre no necesitan red.
            si_cobre = (pad.GetLayerSet().Contains(pcbnew.F_Cu)
                        or pad.GetLayerSet().Contains(pcbnew.B_Cu))
            if not si_cobre:
                continue
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

    # --- pistas (vacio en esta fase, ver TRACKS mas arriba) ---
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

    # Que dos piezas no se monten una encima de otra. Los TO-220 (ahora
    # pre-reguladores) se comparan con HS_LADO, no con su patio, porque la
    # huella no sabe nada del disipador que llevan atornillado.
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

    # Y que ninguna se monte sobre la RANURA.
    ranura = pcbnew.BOX2I(
        pcbnew.VECTOR2I(mm(RANURA_X0), mm(Y_BARRERA - RANURA_ANCHO / 2)),
        pcbnew.VECTOR2I(mm(RANURA_X1 - RANURA_X0), mm(RANURA_ANCHO)))
    sobre_ranura = [ref for ref, bb in cajas
                    if distancia_bbox(bb, ranura) == 0.0]
    print(f"piezas montadas sobre la ranura: {len(sobre_ranura)} {sobre_ranura}")

    # LA comprobacion heredada de v1: separacion real entre cobre de red y
    # cobre SELV. Se mide pad contra pad, no se da por buena porque la
    # ranura este dibujada.
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

    # Taladros de fijacion a distancia segura de la red.
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

    # --- los 4 checks nuevos de la v2 (Tarea 7, Paso 3) ---
    smd_mal = revisar_smd_cara(board)
    print(f"SMD fuera de F.Cu (ensamblaje una cara): {len(smd_mal)} {smd_mal}")
    isla_mal = revisar_isla_referencia(board)
    print(f"isla GNDREF (puentes + pistas fuera de ISLA_REF): {len(isla_mal)} {isla_mal}")
    diagonal_mal = revisar_diagonal(board)
    print(f"lazo rectificador vs isla ultra (>=80mm, sec.6.4): {len(diagonal_mal)} {diagonal_mal}")
    borde_mal = revisar_borde_ceramicos(board)
    print(f"ceramicos de precision cerca del borde (<10mm, sec.6.5): {len(borde_mal)} {borde_mal}")

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
    assert not smd_mal, f"SMD fuera de F.Cu: {smd_mal}"
    assert not isla_mal, f"isla GNDREF mal: {isla_mal}"
    assert not diagonal_mal, f"lazo rectificador demasiado cerca de la isla ultra: {diagonal_mal}"
    assert not borde_mal, f"ceramicos demasiado cerca del borde: {borde_mal}"


if __name__ == "__main__":
    sys.exit(main())
