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
# Anchos nuevos de la Tarea 8 (spec sec.6, brief):
ANCHO_ISLA = 0.5     # +13V1/-12V9 locales, ILIM, OUT->ballast, fugas de GND
ANCHO_SET = 0.25     # red SET: "pista corta y fina" (brief, sec.6.1)
ANCHO_KELVIN = 1.5   # OUTS->J2 y ballast->J2 de +12V/-12V (brief, >=1.5mm)

# ============================================================================
# TAREA 8 — ruteo completo. Estrategia general:
#
# - Potencia THT (roja 230V, VRAW+/-, GND troncal) sigue el patron de v1:
#   mismos anchos, misma logica de corredores para no cruzar entre si.
# - +13V1/-12V9 cruzan la placa entera desde U1/U2 hasta la isla ultra por
#   un corredor "alto" (y=165, por encima de toda la rejilla de la isla,
#   que esta empaquetada fila a fila sin huecos utiles) y bajan en vertical
#   SOLO en la x exacta de cada pad, para no rozar los pines vecinos de los
#   DFN (paso de 0.5 mm entre pines).
# - Kelvin fisico de OUTS (+12V/-12V): sale del pin OUTS por una vía
#   INMEDIATA a B.Cu (la rejilla de F.Cu no deja hueco limpio) y viaja
#   entera por B.Cu, sin tocar la pista de potencia del ballast, hasta
#   soldarse SOLO en el pad de J2 (que es pasante, tiene cobre en B.Cu).
# - GND seria un arbol en F.Cu integramente en v1; en v2 la isla esta tan
#   empaquetada que ninguna fila deja paso limpio de columna a columna, asi
#   que el tronco GND entero (heredado + isla) vive en B.Cu, igual que v1
#   ya hacia con su "arbol, todo en B" — la isla simplemente extiende esa
#   misma capa. Los pads SMD de la isla escapan a B.Cu con una via corta
#   nada mas salir del pad (mismo patron que el Kelvin), evitando cruzar
#   las filas de +13V1/-12V9/SET/ILIM/OUT que si quedan en F.Cu.
# - SET, ILIM, OUT->ballast: saltos cortos directos entre pads vecinos
#   dentro de la isla, en F.Cu, con jog explicito donde una fila
#   intermedia (SET/GNDREF) se interpone.
# - GNDREF: SIN pistas propias. Toda su conectividad (R9.2, C15.2, R10.2,
#   C16.2, R6.2, R8.1, JP1.1) la resuelve la zona de cobre limitada a
#   ISLA_REF que dibuja crear_zonas() — es literalmente la isla de la spec
#   sec.6.3, no una red punto a punto.
# ============================================================================
TRACKS: list[tuple[str, str, list[tuple[float, float]], float]] = [
    # ===================== lado de red 230 V, todo en F salvo /N ===========
    # /L y /L_TR en F a y=7 (por encima de la fila); /L_F en F a y=20 (deja
    # pasar x=90/108, que son de /N, porque /N esta en OTRA CAPA); /N migra
    # a B: con J7 nuevo, /L_F y /N tienen que cruzar la placa entera y sus
    # puntos de bajada (NT1, RV1, J4, J7) se entrelazan en x — en v1 nunca
    # se cruzaban porque /L_F paraba en x=80. Todos los conectores de esta
    # franja son pasantes (pad en F y B), asi que /N en B no necesita vias.
    ("/L",    F, [(18, 15), (18, 7), (38, 7), (38, 12)], ANCHO_RED),
    ("/L",    F, [(38, 12), (38, 17.08)], ANCHO_RED),
    ("/L_TR", F, [(65.5, 15), (65.5, 7), (113, 7), (113, 15)], ANCHO_RED),
    ("/L_F",  F, [(45.62, 12), (45.62, 17.08)], ANCHO_RED),
    ("/L_F",  F, [(45.62, 17.08), (45.62, 20), (128, 20), (128, 15)], ANCHO_RED),
    ("/L_F",  F, [(58, 20), (58, 15)], ANCHO_RED),
    ("/L_F",  F, [(80, 20), (80, 15)], ANCHO_RED),
    ("/N",    B, [(23, 15), (23, 27), (133, 27), (133, 15)], ANCHO_RED),
    ("/N",    B, [(90, 27), (90, 15)], ANCHO_RED),
    ("/N",    B, [(108, 27), (108, 15)], ANCHO_RED),

    # ===================== secundario, en B (igual patron v1) ==============
    ("/SEC_A", B, [(10, 42), (10, 50), (43, 50), (43, 44.08), (39.62, 44.08)], ANCHO_POT),
    ("/SEC_B", B, [(20, 42), (20, 36), (39.62, 36), (39.62, 39)], ANCHO_POT),

    # ===================== VRAW+ (F) =========================================
    ("/VRAW+", F, [(32, 39), (32, 34), (5, 34), (5, 58), (10, 58), (10, 62)], ANCHO_POT),
    ("/VRAW+", F, [(10, 58), (28, 58), (28, 62)], ANCHO_POT),
    ("/VRAW+", F, [(10, 62), (10, 72), (12, 72), (12, 82)], ANCHO_POT),
    ("/VRAW+", F, [(28, 62), (28, 68), (44, 68), (44, 77)], ANCHO_POT),   # TP1
    ("/VRAW+", F, [(44, 68), (59, 68), (59, 82)], ANCHO_POT),
    ("/VRAW+", F, [(12, 82), (12, 90), (18, 90), (18, 94)], ANCHO_POT),
    ("/VRAW+", F, [(59, 82), (59, 90), (65, 90), (65, 94)], ANCHO_POT),
    # baja a U1.4 (pre-reg +13V1) por el margen izquierdo, por ENCIMA de
    # y=143 (evita cruzar los pads 1-3 de U1, que son ADJ/GND)
    # y=135 (no 140): a 140 cruzaba la bajada de Net-(U1-ADJ) a U1.1 (28,
    # 137.5..143) y su tronco vertical en x=25.
    ("/VRAW+", F, [(18, 90), (5, 90), (5, 135), (33.1, 135), (33.1, 143)], ANCHO_POT),
    # baja a U3.1 (+5V, sin cambios). x=79 (no 50/53/76): esquiva el
    # highway de +12V, Net-(D3-A) Y el ramal de +5V a D5.2 (75.16,90..94).
    # U3.1 esta encajonado entre la bajada de +12V a TP3 (x=74) y el
    # tronco/ramal de +5V (80.08 / 75.16) -- no hay corredor F.Cu limpio.
    # Salta a B.Cu justo al salir de la columna de C9 y llega derecho
    # (U3 es pasante).
    ("/VRAW+", F, [(65, 90), (70, 90)], ANCHO_POT),
    # la diagonal por B.Cu cruza dos horizontales de GND (y=105, U2 col.;
    # y=137, U3 col.) y el salto de -12V en x=70..78,y=99..104.5 -- saltos
    # cortos a F.Cu en cada cruce.
    # el hueco de F.Cu (96..106) cruzaba los highways de +12V/-12V (102 y
    # 104.5), que TAMBIEN son F.Cu -- se queda en B.Cu ahi y solo salta a
    # F.Cu justo en el cruce con la horizontal de GND a y=105.
    ("/VRAW+", B, [(70, 90), (70, 103)], ANCHO_POT),
    ("/VRAW+", F, [(70, 103), (71, 107)], ANCHO_POT),
    ("/VRAW+", B, [(71, 107), (74, 135)], ANCHO_POT),
    ("/VRAW+", F, [(74, 135), (74, 139)], ANCHO_POT),
    ("/VRAW+", B, [(74, 139), (75, 143)], ANCHO_POT),

    # ===================== VRAW- (F) =========================================
    ("/VRAW-", F, [(32, 44.08), (32, 52), (73.5, 52), (73.5, 62)], ANCHO_POT),
    ("/VRAW-", F, [(55.5, 52), (55.5, 62)], ANCHO_POT),
    ("/VRAW-", F, [(73.5, 62), (73.5, 68), (100, 68), (100, 77)], ANCHO_POT),   # TP2
    ("/VRAW-", F, [(100, 68), (111, 68), (111, 82)], ANCHO_POT),
    ("/VRAW-", F, [(111, 82), (111, 90), (122.16, 90), (122.16, 94)], ANCHO_POT),
    # baja a U2.3 por el margen derecho, mismo criterio (evita pads 1/2 de U2)
    # y=135 (no 140): a 140 cruzaba la bajada de Net-(U2-ADJ) a U2.1. La
    # bajada final a x=125.4 SIGUE cruzando esa red en y=137.5 -- salto
    # corto a B.Cu.
    ("/VRAW-", F, [(111, 90), (99, 90), (99, 135), (125.4, 135), (125.4, 136)], ANCHO_POT),
    ("/VRAW-", B, [(125.4, 136), (125.4, 139)], ANCHO_POT),
    ("/VRAW-", F, [(125.4, 139), (125.4, 143)], ANCHO_POT),

    # ===================== +5V (F, sin cambios de v1: U3/C9/C10/C11/D5/D6/R3) =
    ("+5V", F, [(80.08, 143), (80.08, 137), (97, 137), (97, 86)], ANCHO_POT),
    ("+5V", F, [(97, 86), (89, 86), (89, 82)], ANCHO_POT),
    ("+5V", F, [(97, 86), (84, 86), (84, 81), (84, 77)], ANCHO_POT),   # TP5
    ("+5V", F, [(84, 86), (75, 86), (75, 82)], ANCHO_POT),
    ("+5V", F, [(84, 86), (85, 90), (85, 94)], ANCHO_POT),
    ("+5V", F, [(75, 86), (75.16, 90), (75.16, 94)], ANCHO_SEN),
    # a J6.1: por y=150 hasta x=40, pero el corredor de +13V1 (y=165, hasta
    # x=110.55) sigue de por medio bajando a 172 -- salto corto a B.Cu.
    ("+5V", F, [(80.08, 143), (80.08, 150), (40, 150), (40, 163)], ANCHO_POT),
    ("+5V", B, [(40, 163), (40, 167)], ANCHO_POT),
    ("+5V", F, [(40, 167), (40, 172)], ANCHO_POT),

    # ===================== /+13V1 (F): U1.5 -> isla ==========================
    # tronco vertical junto a U1: TP7 arriba, C17/D12 en su columna, U1.5
    # en medio, R5 (divisor, acercado a la isla) y el corredor alto y=165
    # hacia la isla, todo en la MISMA x=34.8..35 para no cruzar nada propio.
    ("/+13V1", F, [(32, 74), (34.8, 74), (34.8, 96)], ANCHO_POT),   # TP7 -> U1.5
    # salto a B.Cu: a x=34.8 el highway de +12V (10..45, y=102) cruzaria
    # el tronco de lleno; el tramo B.Cu ensanchado (96..110) tambien
    # esquiva las DOS horizontales de GND a y=105 y 108 (columna U1, 20..42).
    ("/+13V1", B, [(34.8, 96), (34.8, 110)], ANCHO_POT),
    ("/+13V1", F, [(34.8, 110), (34.8, 143)], ANCHO_POT),
    ("/+13V1", F, [(28, 82), (28, 74.5), (34.8, 74.5)], ANCHO_POT),  # C17.1
    ("/+13V1", F, [(28.16, 94), (28.16, 100), (34.8, 100)], ANCHO_POT),  # D12.2
    ("/+13V1", F, [(34.8, 143), (34.8, 165)], ANCHO_POT),
    # R5.1: cruza el hub de Net-(U1-ADJ) en y=176 -- salto corto a B.Cu.
    ("/+13V1", F, [(34.8, 165), (35, 174)], ANCHO_POT),
    ("/+13V1", B, [(35, 174), (35, 178)], ANCHO_POT),
    ("/+13V1", F, [(35, 178), (35, 182)], ANCHO_POT),   # R5.1
    ("/+13V1", F, [(34.8, 165), (110.55, 165)], ANCHO_ISLA),   # corredor alto
    ("/+13V1", F, [(90.55, 165), (90.55, 168)], ANCHO_ISLA),   # U4 pines 1-3
    ("/+13V1", F, [(100, 165), (100, 168)], ANCHO_ISLA),       # D8.1
    ("/+13V1", F, [(110.55, 165), (110.55, 168)], ANCHO_ISLA),  # U5 pines 1-3
    # C19.1/C20.1: NO en linea recta por la columna (pisaria ILIM/OUT/GNDREF
    # en las filas intermedias) -- bajan por el hueco libre x=95 (entre la
    # columna de U4/C23/R15 y la de D8/D10/C15/R9, ningun pad de otra red
    # llega hasta ahi en ninguna fila) y entran a cada cap por abajo, en la
    # fila y=192 donde no hay nada mas entre 90.5 y 110.5.
    # el tramo largo salta a B.Cu: en F.Cu, x=95 cruza el puente de +12V
    # (y=183), el hub de -12V (y=178) y la fuga de SET (y=168.6) uno tras
    # otro. x=90 (no 95): fuera del rango de Kelvin +12V (94.5..114.5) Y
    # del tramo de GND a y=186 (92..112) -- el unico hueco limpio de B.Cu
    # en esta franja.
    ("/+13V1", F, [(90, 165), (90, 167)], ANCHO_ISLA),
    # x=90 cae dentro del hub de GND hacia el EP de U4 (62.54..92, y=186)
    # -- salto a F.Cu solo en ese cruce, en x=89.2 (lejos del ultimo tramo
    # de Net-(U4-OUT) a R15.1, que llega a 90.525/90.537).
    ("/+13V1", B, [(90, 167), (90, 184), (89.2, 184)], ANCHO_ISLA),
    ("/+13V1", F, [(89.2, 184), (89.2, 188)], ANCHO_ISLA),
    ("/+13V1", B, [(89.2, 188), (90, 188), (90, 190)], ANCHO_ISLA),
    ("/+13V1", F, [(90, 190), (90.525, 190), (90.525, 192)], ANCHO_ISLA),   # C19.1
    ("/+13V1", F, [(90, 190), (110.525, 190), (110.525, 192)], ANCHO_ISLA),  # C20.1

    # ===================== /-12V9 (F): U2.5 -> isla ==========================
    ("/-12V9", F, [(126, 74), (128.8, 74), (128.8, 100)], ANCHO_POT),  # TP8 -> U2.5
    # salto a B.Cu: a x=128.8 la bajada de Net-(U2-ADJ) (122..145.2, y=137.5)
    # cruzaria el tronco de lleno.
    ("/-12V9", B, [(128.8, 100), (128.8, 104)], ANCHO_POT),
    ("/-12V9", F, [(128.8, 104), (128.8, 136)], ANCHO_POT),
    # segundo salto: Net-(U2-ADJ) tambien pasa por aqui, en y=137.5.
    ("/-12V9", B, [(128.8, 136), (128.8, 139)], ANCHO_POT),
    ("/-12V9", F, [(128.8, 139), (128.8, 143)], ANCHO_POT),
    ("/-12V9", F, [(112, 94), (112, 100), (128.8, 100)], ANCHO_POT),  # D13.1
    ("/-12V9", F, [(128.8, 143), (128.8, 165)], ANCHO_POT),
    ("/-12V9", F, [(128.8, 165), (118.55, 165), (118.55, 166.875)], ANCHO_ISLA),  # U6 1-3
    ("/-12V9", F, [(130, 165), (130, 168)], ANCHO_ISLA),   # D9.2
    ("/-12V9", F, [(134.55, 165), (134.55, 166.875)], ANCHO_ISLA),  # U7 1-3
    ("/-12V9", F, [(118.55, 165), (134.55, 165)], ANCHO_ISLA),
    # C21.1/C22.1: bajar recto por la columna de pines (118.55/134.55)
    # pisaria los pines 4/5/6 (NC/NC/ILIM), que comparten esa misma x mas
    # abajo. Salen por FUERA de todo el chip (122.6, a la derecha de sus
    # pines reales hasta 121.45, y a la izquierda de D9 en 124.45) y bajan
    # rectas en F.Cu; entran a cada cap por ARRIBA para no cruzar el pad
    # vecino de GND (121.475/137.475) que esta al lado.
    # tramos largos por B.Cu: en F.Cu cruzarian el puente de -12V (y=183),
    # SET y GND de U6/U7 (y=168.1/168.8) uno tras otro. x=120 (no 122.6):
    # el unico hueco limpio de B.Cu entre JP1 (hasta 116.5) y la horizontal
    # Kelvin -12V (desde 122.5); entra a B por debajo de la diagonal
    # Kelvin (que en x=120 no baja de y=167.4).
    ("/-12V9", F, [(128.8, 165), (120, 165), (120, 169)], ANCHO_ISLA),
    ("/-12V9", B, [(120, 169), (120, 190)], ANCHO_ISLA),
    ("/-12V9", F, [(120, 190), (118.525, 190), (118.525, 192)], ANCHO_ISLA),  # C21.1
    ("/-12V9", F, [(120, 190), (134.525, 190), (134.525, 192)], ANCHO_ISLA),  # C22.1
    # R7.2 (vuelto al hueco de R6): rama propia desde el tronco vertical de
    # U2.5. x=55 esta fuera del corredor F.Cu de +13V1 (34.8..110.55 SI lo
    # cubre, asi que igual hay que tunelizar) y fuera de la diagonal Kelvin
    # de -12V (que no baja de x=60) -- un tunel corto por B.Cu en x=55 lo
    # cruza limpio, y desde ahi mismo baja por B.Cu hasta R7.2 sin pisar
    # R6 (que esta a x=76..88, fuera de esta columna).
    ("/-12V9", F, [(128.8, 150), (128.8, 160), (55, 160), (55, 163)], ANCHO_POT),
    # saltos a F.Cu: cruza el ramal de -12V a J2.1 (56.5, y=172..178), el
    # de GND a J5/J2.2/J2.3 (12..62.54, y=186) y pasa cerca de R7.1(77,192).
    ("/-12V9", B, [(55, 163), (55, 170)], ANCHO_POT),
    ("/-12V9", F, [(55, 170), (53, 172)], ANCHO_POT),
    ("/-12V9", B, [(53, 172), (53, 184)], ANCHO_POT),
    ("/-12V9", F, [(53, 184), (53, 188)], ANCHO_POT),
    ("/-12V9", B, [(53, 188), (53, 196), (87.16, 196), (87.16, 192)], ANCHO_POT),

    # ===================== ADJ (F): U1/U2, ADJ no es sub-uV (sec.6.3) ========
    # y=176: por encima de RV2/R6 (courtyard desde 179.29/180.46), no pisa
    # su fila; baja en vertical SOLO en el pin exacto de cada destino. El
    # hub de +12V vive en y=177 y el de -12V en y=178, mismo hueco de 4 mm,
    # cada red en su propio nivel.
    ("Net-(U1-ADJ)", F, [(28, 143), (28, 137.5), (25, 137.5), (25, 176)], ANCHO_SEN),
    # RV2.3 (pasante): salta a B.Cu, Net-(R5-Pad2) cruza justo ahi (45.16
    # a 57, y=180) camino de RV2.1/2 -- por B.Cu no se tocan.
    ("Net-(U1-ADJ)", F, [(25, 176), (51.92, 176)], ANCHO_SEN),
    ("Net-(U1-ADJ)", B, [(51.92, 176), (51.92, 182)], ANCHO_SEN),   # RV2.3
    # R6.1 (pasante): tambien salta a B.Cu -- a 77 cruzaria los hubs de
    # +12V (y=177) y -12V (y=178) de lleno.
    ("Net-(U1-ADJ)", F, [(25, 176), (77, 176)], ANCHO_SEN),
    ("Net-(U1-ADJ)", B, [(77, 176), (77, 182)], ANCHO_SEN),   # R6.1
    ("Net-(U2-ADJ)", F, [(122, 143), (122, 137.5), (145.2, 137.5), (145.2, 159.84)], ANCHO_SEN),
    # RV3.1: rodea el cuerpo de R8 (pad1/GNDREF en 145.2,170, cuadrado
    # 1.6x1.6) por la derecha en vez de cruzarlo en diagonal.
    ("Net-(U2-ADJ)", F, [(145.2, 159.84), (146.5, 159.84), (146.5, 175), (144, 175)], ANCHO_SEN),
    # esquiva RV2.3 (51.92,182 -- Net-U1-ADJ, entre R5.2 y RV2.1/2) subiendo
    # a y=180, por encima del pad de RV2.3 (1.44x1.44, hasta y=182.72...
    # arriba: y=181.28 es su borde superior, 180 queda claro).
    ("Net-(R5-Pad2)", F, [(45.16, 182), (45.16, 180), (54.46, 180), (54.46, 182)], ANCHO_SEN),
    ("Net-(R5-Pad2)", F, [(54.46, 182), (57, 182)], ANCHO_SEN),
    # R7.1: la diagonal directa cruzaba TODA la isla (R11, C23, R15, SET,
    # ILIM...). Escapa a B.Cu junto a RV3 y viaja entera por B.Cu hasta
    # R7.1 (pasante, cobre en B.Cu), sin tocar la rejilla de F.Cu.
    ("Net-(R7-Pad1)", F, [(144, 177.54), (144, 180.08)], ANCHO_SEN),
    ("Net-(R7-Pad1)", F, [(144, 178.8), (146.8, 178.8)], ANCHO_SEN),
    # el tramo -12V9 va por y=196 entre x 53-87.16; el ultimo tramo vertical
    # (x=77) lo cruzaria en B.Cu, asi que salta a F.Cu solo para ese tramo
    # (R7 es pasante THT, ambas caras validas en el pad).
    ("Net-(R7-Pad1)", B, [(146.8, 178.8), (146.8, 197), (77, 197)], ANCHO_SEN),
    ("Net-(R7-Pad1)", F, [(77, 197), (77, 192)], ANCHO_SEN),

    # ===================== LED/gate del crowbar (F, sin cambios de forma) ===
    ("Net-(D3-A)", F, [(39.46, 111), (39.46, 115), (52.16, 115), (52.16, 119)], ANCHO_SEN),
    ("Net-(D4-A)", F, [(55.46, 111), (55.46, 115), (68.16, 115), (68.16, 119)], ANCHO_SEN),
    ("Net-(D6-A)", F, [(86.46, 105), (86.46, 99), (95.16, 99), (95.16, 94)], ANCHO_SEN),
    ("Net-(D7-A)", F, [(33.62, 111), (33.62, 115), (26, 115), (26, 119)], ANCHO_SEN),
    ("Net-(D7-A)", F, [(26, 115), (10, 115), (10, 119)], ANCHO_SEN),

    # ===================== +12V final: bus/crowbar + Kelvin =================
    # El puente del ballast (F, entre las filas y=180/186 para no pisar
    # SET/GNDREF) sale de la isla por x=93.463 hacia y=177 -- fila libre
    # entre el bloque R9-R14 (bottom ~174.78) y el bloque C23-C26
    # (top ~178.81). Desde ahi, J2.4 (potencia) queda DEBAJO de y=165 y no
    # necesita cruzar el corredor de +13V1; el resto (Q1/D7/R1/TP3, banda
    # y=111/119) si esta por encima, asi que hace un tunel por B.Cu en
    # x=45 (fuera del rango de las dos diagonales Kelvin, que van de
    # x=60/67.62 a 114.5/122.5) para saltar el corredor de +13V1 (F, y=165)
    # sin tocarlo.
    # el puente queda RECTO (no hay margen limpio para una muesca: R15/R16
    # empiezan a 184.82 y C23/D10/C25 terminan a 181.19, solo 1.6 mm libres
    # a cada lado de y=183). En cambio, SET y Net-(U5-OUT) -- mas finas y
    # con mas libertad -- saltan a B.Cu justo donde cruzan el puente.
    ("+12V", F, [(93.463, 186), (93.463, 183), (113.463, 183), (113.463, 186)], ANCHO_KELVIN),
    ("+12V", F, [(104, 183), (104, 180)], ANCHO_ISLA),   # D10.2
    ("+12V", F, [(93.463, 183), (93.463, 177)], ANCHO_ISLA),
    ("+12V", F, [(93.463, 177), (45, 177)], ANCHO_ISLA),
    ("+12V", B, [(45, 177), (45, 102)], ANCHO_ISLA),   # tunel bajo el corredor +13V1 (y=165)
    ("+12V", F, [(45, 102), (10, 102)], ANCHO_KELVIN),
    ("+12V", F, [(10, 102), (10, 111)], ANCHO_KELVIN),    # Q1.1
    ("+12V", F, [(26, 102), (26, 111)], ANCHO_KELVIN),    # D7.1
    # R1.1: x=36 (no 45) -- a 45 la bajada cruzaba Net-(D3-A) de lleno
    # (39.46..52.16, y=115).
    ("+12V", F, [(45, 102), (38, 102), (38, 119), (42, 119)], ANCHO_KELVIN),   # R1.1
    ("+12V", F, [(45, 102), (74, 102), (74, 111)], ANCHO_KELVIN),   # TP3.1
    # J2.4 (potencia): via propia junto al puente (95,183, NO en el hub
    # y=177 que comparten -12V y Net-U1-ADJ) y viaje entero por B.Cu.
    # J2.4 (potencia): rama del hub F.Cu de +12V (93.463..45, y=177, ya
    # pasa por x=67.62) -- ir por B.Cu desde el puente cruzaba la rama de
    # GND al EP de U4 (x=92, B.Cu) de lleno. Bajar de 177 a 172 SI cruza a
    # Net-U1-ADJ (176): salto corto a B.Cu, libre en 67.62 (GND vive en
    # 92/105/112/116.5, Kelvin -12V no baja de 158 ahi).
    ("+12V", B, [(67.62, 177), (67.62, 172)], ANCHO_KELVIN),
    # Kelvin fisico: OUTS de U4/U5 (pines 9, 93.45/113.45,167.5) escapan a
    # B.Cu por una via propia a x=95.5/115.5 (no 94.5/114.5: mas lejos del
    # via de escape de Net-(U4/5-OUT), que vive junto al pin de al lado en
    # 93.45/113.45,167) -- el tramo F.Cu que las une al pad, que faltaba.
    # ancho fino (SET, 0.25mm) SOLO en este tramo de 2 mm: paso de pines
    # del DFN de 0.5 mm, ni ANCHO_KELVIN ni ANCHO_ISLA caben sin tocar a
    # GND (167.9..168.1) o a Net-(U4/5-SET) (168.5) al lado.
    ("+12V", F, [(93.45, 167.5), (95.5, 167.5)], ANCHO_SET),
    ("+12V", F, [(113.45, 167.5), (115.5, 167.5)], ANCHO_SET),
    # viajan SOLO por B.Cu hasta el pad de J2.4 — no tocan la pista de
    # arriba. El tramo horizontal sube a y=166.3 (no 167.5): a 167.5
    # pasaba a 0.75 mm de donde la rama de GND del EP de U5 baja a
    # x=112,y=168.
    ("+12V", B, [(95.5, 167.5), (95.5, 166.3)], ANCHO_KELVIN),
    # ancho fino (misma razon que la horizontal de -12V): a 166.3 pasa a
    # 0.7 mm de la fuga de Net-(U5-OUT) en x=113.45,y=167.
    ("+12V", B, [(95.5, 166.3), (115.5, 166.3)], ANCHO_ISLA),
    ("+12V", B, [(115.5, 166.3), (115.5, 167.5)], ANCHO_KELVIN),
    # diagonal fina (misma razon): pasa cerca de la fuga de Net-(U4-OUT)
    # en x=88..93.45,y=167.
    ("+12V", B, [(95.5, 167.5), (67.62, 155)], ANCHO_ISLA),
    ("+12V", B, [(67.62, 155), (67.62, 172)], ANCHO_KELVIN),

    # ===================== -12V final: bus/crowbar + Kelvin =================
    # Mismo criterio; hub a y=178 (Net-U1-ADJ en 176, +12V en 177, -12V en
    # 178 -- tres pistas en los 4 mm libres entre R9-R14 y C23-C26, cada
    # una en su propio nivel). D4/R2 (x=58) y TP4 (x=90) quedan en F.Cu tras
    # el tunel (NO en B.Cu: el arbol de GND ya usa B.Cu por ahi, x=20/57/
    # 123.7 hasta y=137). El highway de -12V a y=101 pasaria por x=74
    # justo donde +12V baja a TP3: un salto de 1 mm a B.Cu en x=70..78 lo
    # evita.
    # puente RECTO, igual criterio que +12V: SET y Net-(C26-Pad1) saltan a
    # B.Cu donde cruzan.
    ("-12V", F, [(121.463, 186), (121.463, 183), (137.463, 183), (137.463, 186)], ANCHO_KELVIN),
    ("-12V", F, [(126, 183), (126, 180)], ANCHO_ISLA),   # D11.1
    ("-12V", F, [(121.463, 183), (121.463, 178)], ANCHO_ISLA),
    # muesca en x=93..94: ahi sube la bajada F.Cu de +12V del puente
    # (y=183) a su propio hub (y=177), y cruzaria el hub de -12V de lleno.
    # la muesca anterior (179.5) seguia DENTRO del rango y=177..183 de la
    # bajada de +12V -- se necesita salir de ese rango, no solo desviarse
    # en x. y=183.5 esta justo debajo (+12V para en 183) y libre de R6
    # (que empieza en x=75.91, lejos de este tramo en x=91..96).
    # la bajada de +12V al puente (93.463) ocupa TODO y=177..186 (su tramo
    # 177..183 mas el 183..186 del propio puente) -- no hay hueco en Y
    # posible ahi. Salto a B.Cu solo para cruzar ese punto.
    ("-12V", F, [(121.463, 178), (94, 178)], ANCHO_ISLA),
    ("-12V", B, [(94, 178), (93, 178)], ANCHO_ISLA),
    ("-12V", F, [(93, 178), (48, 178)], ANCHO_ISLA),
    ("-12V", B, [(48, 178), (48, 104.5)], ANCHO_ISLA),      # tunel bajo el corredor +13V1
    # y=104.5 (no 101): a 101 el highway quedaba a solo 1 mm del de +12V
    # (y=102), y los dos son de 1.5 mm -- hacian falta 1.5 mm de hueco.
    ("-12V", F, [(48, 104.5), (70, 104.5)], ANCHO_KELVIN),
    ("-12V", B, [(70, 104.5), (70, 99), (78, 99), (78, 104.5)], ANCHO_KELVIN),  # salto a B, esquiva TP3.1 de +12V
    # huecos deliberados: Net-(D6-A) cruza x=86.46 a y=104.5, y Net-(D4-A)
    # cruza x=58 a y=115 -- las dos vías de -12V se parten para dejarlas
    # pasar sin tocarlas.
    # rodeo por y=103 en x=84..89 (no un hueco a la misma altura): el pad
    # de D6.2 usa radio real (max dimension/2 = 0.9 mm) desde su centro en
    # 86.46,105 -- el hueco anterior (85..88 a la misma y) quedaba a solo
    # 0.06 mm del radio del pad.
    ("-12V", F, [(78, 104.5), (84, 104.5), (84, 103), (89, 103), (89, 104.5), (90, 104.5)], ANCHO_KELVIN),
    ("-12V", F, [(58, 104.5), (58, 113)], ANCHO_KELVIN),    # D4.1
    ("-12V", F, [(58, 117), (58, 119)], ANCHO_KELVIN),    # R2.1
    ("-12V", F, [(90, 104.5), (90, 111)], ANCHO_KELVIN),    # TP4.1
    # J2.1 (potencia): rama del MISMO hub F.Cu de arriba (que ya pasa por
    # x=56.5 camino de 48), pero bajar en F.Cu de 178 a 172 cruzaria los
    # hubs de +12V (177) y Net-U1-ADJ (176) de lleno -- salto corto a B.Cu
    # (libre en x=56.5: las columnas del arbol de GND estan en 92/105/112).
    ("-12V", B, [(56.5, 178), (56.5, 172)], ANCHO_KELVIN),
    ("-12V", F, [(56.5, 172), (60, 172)], ANCHO_KELVIN),
    # Kelvin de U6.10/U7.10 (pines 10, 121.45/137.45,167.775): el tramo
    # F.Cu que las une a su via de escape, que faltaba.
    # y=167.65 (borde SUPERIOR del pad, lejos del vecino GND en 168.225) y
    # ancho fino: paso de 0.45 mm del DFN-12, sin margen para ANCHO_KELVIN.
    ("-12V", F, [(121.45, 167.65), (122.5, 167.65)], ANCHO_SET),
    ("-12V", F, [(137.45, 167.65), (138.5, 167.65)], ANCHO_SET),
    # y=166.7 (no 167.65) y ancho fino: pasa entre el corredor +13V1 (165)
    # y las vias de escape de GND en 124/125/139.8 (168.1..168.225), solo
    # 3.1 mm de hueco real -- no cabe ANCHO_KELVIN ahi.
    ("-12V", B, [(122.5, 167.65), (122.5, 166.7)], ANCHO_ISLA),
    ("-12V", B, [(122.5, 166.7), (138.5, 166.7)], ANCHO_ISLA),
    ("-12V", B, [(138.5, 166.7), (138.5, 167.65)], ANCHO_ISLA),
    # la diagonal directa cruzaba la horizontal Kelvin de +12V (166.3) y su
    # propia diagonal (155). Baja recta a y=153 (por debajo de las dos)
    # ANTES de cruzar hacia la izquierda, y solo entonces gira hacia J2.1.
    ("-12V", B, [(122.5, 167.65), (122.5, 153), (60, 153), (60, 172)], ANCHO_KELVIN),

    # ===================== SET compartida (0.25 mm, sec.6.1) ================
    # C15/C16 pegados al pin SET (brief): R9.1/R10.1 son el nodo compartido,
    # a un salto directo de cada capacitor. Cada SET_n de cada chip esta
    # flanqueado a 0.45-0.5 mm por dos pines de OTRA red (paso del DFN) --
    # sale por el UNICO lado libre (pegado a y=168.5/168.675 exclusivamente,
    # nunca cruzando la fila) hasta despejar el cuerpo del chip.
    # arranca en 168.6 (borde inferior del pad de SET, no el centro 168.5):
    # a 0.5 mm justos del pad de GND vecino (168) sobraban solo 0.125 mm de
    # los 0.3 que pide revisar_pistas; con los dos arrancando del borde de
    # su propio pad (GND en 167.9, mas abajo) el hueco real sube a 0.7 mm.
    ("Net-(U4-SET)", F, [(93.45, 168.6), (96, 168.6), (96, 174), (101.088, 174)], ANCHO_SET),  # U4.7 -> R9.1
    # R9.1 -> C15.1: cruza el puente de +12V en y=183 -- salto corto a B.Cu.
    ("Net-(U4-SET)", F, [(101.088, 174), (100.7, 181.5)], ANCHO_SET),
    ("Net-(U4-SET)", B, [(100.7, 181.5), (100.6, 184.5)], ANCHO_SET),
    ("Net-(U4-SET)", F, [(100.6, 184.5), (100.525, 186)], ANCHO_SET),
    # -> U5.7: R9.1 esquiva la fila de R12/JP1 (174) por B.Cu (y=176) y
    # entra a U5.7 por la derecha del chip (114.6, fuera de JP1 y del
    # cuerpo de U5).
    ("Net-(U4-SET)", F, [(101.088, 174), (103, 174), (103, 176)], ANCHO_SET),
    ("Net-(U4-SET)", B, [(103, 176), (114.6, 176)], ANCHO_SET),
    ("Net-(U4-SET)", F, [(114.6, 176), (114.6, 168.6), (113.45, 168.6)], ANCHO_SET),  # U5.7 (168.6, no 168.5: idem U4.7)
    # 168.8 (borde inferior del pad, no el centro 168.675): mismo motivo
    # que U4.7 pero con el paso de 0.45 mm del DFN-12.
    ("Net-(U6-SET)", F, [(121.45, 168.8), (124, 168.8), (124, 174), (127.088, 174)], ANCHO_SET),  # U6.8 -> R10.1
    # R10.1 -> C16.1: cruza el puente de -12V en y=183 -- salto a B.Cu.
    ("Net-(U6-SET)", F, [(127.088, 174), (126.7, 181.5)], ANCHO_SET),
    ("Net-(U6-SET)", B, [(126.7, 181.5), (126.6, 184.5)], ANCHO_SET),
    ("Net-(U6-SET)", F, [(126.6, 184.5), (126.525, 186)], ANCHO_SET),
    # -> U7.8: mismo criterio, esquiva R14 (174) por B.Cu a y=176 y entra
    # a U7.8 por la derecha (140.2, fuera de la via de escape GND de U7.9
    # en 139,168.225 y del cuerpo de U7).
    ("Net-(U6-SET)", F, [(127.088, 174), (127.088, 176)], ANCHO_SET),
    ("Net-(U6-SET)", B, [(127.088, 176), (140.2, 176)], ANCHO_SET),
    ("Net-(U6-SET)", F, [(140.2, 176), (140.2, 168.8), (137.45, 168.8)], ANCHO_SET),  # U7.8

    # ===================== ILIM, uno por chip (F) ============================
    # La diagonal directa del pin ILIM a su resistencia pasaba a 0.18 mm de
    # la diagonal OUT->C->ballast del mismo chip (ambas cruzan la misma
    # esquina). Sale por la izquierda de cada chip (fuera del cuerpo, fuera
    # del camino de OUT que se queda del lado derecho/centro) y entra a su
    # resistencia por y=174 desde el otro lado.
    ("Net-(U4-ILIM)", F, [(90.55, 169), (89, 169), (89, 174), (91.175, 174)], ANCHO_ISLA),
    ("Net-(U5-ILIM)", F, [(110.55, 169), (109, 169), (109, 174), (111.175, 174)], ANCHO_ISLA),
    # U6/U7: el hueco a la izquierda del chip es mas angosto (JP1 a un
    # lado, la fuga de Net-C25/26-Pad1 al otro) -- el ultimo tramo (169 a
    # 174) salta a B.Cu para no competir por ese milimetro.
    ("Net-(U6-ILIM)", F, [(118.55, 169.125), (117.3, 169.125)], ANCHO_ISLA),
    ("Net-(U6-ILIM)", B, [(117.3, 169.125), (119.175, 173)], ANCHO_ISLA),
    ("Net-(U6-ILIM)", F, [(119.175, 173), (119.175, 174)], ANCHO_ISLA),
    ("Net-(U7-ILIM)", F, [(134.55, 169.125), (133, 169.125)], ANCHO_ISLA),
    ("Net-(U7-ILIM)", B, [(133, 169.125), (135.175, 173)], ANCHO_ISLA),
    ("Net-(U7-ILIM)", F, [(135.175, 173), (135.175, 174)], ANCHO_ISLA),

    # ===================== OUT (antes del ballast), un tramo por chip =======
    # OUT/C25/C26-Pad1 salen por ARRIBA (y=166.2, por encima de toda la fila
    # y por debajo del corredor +13V1 en 165) y rodean el chip por fuera
    # antes de bajar -- si bajaran en diagonal directa desde su pin (fila
    # superior del chip) pisarian el pin GND vecino (0.5 mm de paso); asi
    # dejan el lado corto/directo libre para GND, que sale derecho hacia
    # el EP o su via propia.
    # Todos los SMD de la isla son de una sola cara (F.Cu, brief Tarea 7):
    # B.Cu esta VACIO ahi salvo el arbol de GND y las pistas Kelvin. En vez
    # de esquivar cada pin vecino en F.Cu (0.5 mm de paso, imposible de
    # verdad), OUT/C25/C26-Pad1 saltan a B.Cu justo en su propio pin y
    # viajan libres hasta el via de vuelta junto a su destino, con solo
    # cuidado del arbol de GND y de Kelvin (que si viven en B.Cu).
    ("Net-(U4-OUT)", B, [(93.45, 167), (88, 167), (88, 180), (90.525, 180)], ANCHO_ISLA),
    ("Net-(U4-OUT)", F, [(90.525, 180), (90.537, 186)], ANCHO_ISLA),
    # el tramo vertical en x=107 cruza Net-(U4-SET) en y=176 (dentro de su
    # rango 103..114.6) -- salto corto a F.Cu solo ahi.
    ("Net-(U5-OUT)", B, [(113.45, 167), (113.45, 169.5), (107, 169.5), (107, 175)], ANCHO_ISLA),
    ("Net-(U5-OUT)", F, [(107, 175), (107, 177)], ANCHO_ISLA),
    ("Net-(U5-OUT)", B, [(107, 177), (107, 180), (110.525, 180)], ANCHO_ISLA),
    # cruza el mismo puente en y=183 -- salto corto a B.Cu.
    ("Net-(U5-OUT)", F, [(110.525, 180), (110.53, 181.5)], ANCHO_ISLA),
    ("Net-(U5-OUT)", B, [(110.53, 181.5), (110.53, 184.5)], ANCHO_ISLA),
    ("Net-(U5-OUT)", F, [(110.53, 184.5), (110.537, 186)], ANCHO_ISLA),
    # x=117 (no 115, muy cerca de Net-(U4-SET) en 114.6) y horizontal a
    # y=174.5 (no 169.5, que cruzaba Net-(U6-ILIM)); el tramo final baja
    # cruzando Net-(U6-SET) en y=176 -- salto a F.Cu solo ahi.
    # x=119 (no 117, muy cerca del via de JP1.2 en 116.5).
    ("Net-(C25-Pad1)", B, [(121.45, 167.325), (121.45, 174.5), (119, 174.5), (119, 175)], ANCHO_ISLA),
    ("Net-(C25-Pad1)", F, [(119, 175), (119, 177)], ANCHO_ISLA),
    ("Net-(C25-Pad1)", B, [(119, 177), (119, 180), (118.525, 180)], ANCHO_ISLA),
    ("Net-(C25-Pad1)", F, [(118.525, 180), (118.537, 186)], ANCHO_ISLA),
    # C26.1 (134.525) queda a la IZQUIERDA de su vecino C26.2/GND (137.475,
    # misma fila) -- se aproxima por la izquierda (x=132), igual que las
    # otras tres, para no cruzar el pad de GND.
    # horizontal a y=174.5 (no 169.5, que cruzaba Net-(U7-ILIM)); el tramo
    # final en x=132 baja cruzando Net-(U6-SET) en y=176 -- salto a F.Cu.
    ("Net-(C26-Pad1)", B, [(137.45, 167.325), (137.45, 174.5), (132, 174.5), (132, 175)], ANCHO_ISLA),
    ("Net-(C26-Pad1)", F, [(132, 175), (132, 177)], ANCHO_ISLA),
    ("Net-(C26-Pad1)", B, [(132, 177), (132, 180), (134.525, 180)], ANCHO_ISLA),
    # cruza el mismo puente -- salto a B.Cu.
    ("Net-(C26-Pad1)", F, [(134.525, 180), (134.53, 181.5)], ANCHO_ISLA),
    ("Net-(C26-Pad1)", B, [(134.53, 181.5), (134.53, 184.5)], ANCHO_ISLA),
    ("Net-(C26-Pad1)", F, [(134.53, 184.5), (134.537, 186)], ANCHO_ISLA),

    # ===================== GND: pines 8 de U4/U5 -> su propio EP =============
    # U4.8/U5.8 son SMD de solo F.Cu; con OUT desviada por arriba, el lado
    # IZQUIERDO queda libre y GND llega derecho al EP vecino (1.45 mm), en
    # F.Cu -- el EP ya trae su propia granja de vias, no hace falta otra.
    # borde inferior del pad (168.125, lejos de Kelvin en 167.5) y ancho
    # fino: el pad de U4.8 mide 0.25 mm de alto, no hay margen para
    # ANCHO_ISLA sin tocar la fuga Kelvin vecina.
    ("GND", F, [(93.45, 168.125), (92.825, 168.125)], ANCHO_SET),   # U4.8 -> borde del EP
    ("GND", F, [(113.45, 168.125), (112.825, 168.125)], ANCHO_SET),  # U5.8 -> borde del EP
    # U6.9/U7.9 -> sus vias de escape propias (124/139.8, 168.225 -- NO en
    # 122.5/138.5, que es donde arranca la via Kelvin de -12V, o se tocan).
    # centro del pad (168.225, no un borde): equidistante de Kelvin arriba
    # (167.65) y de Net-(U6/7-SET) abajo (168.8) -- el mejor reparto
    # posible en un paso de 0.45 mm. Ancho fino, mismo motivo de siempre.
    ("GND", F, [(121.45, 168.225), (124, 168.225)], ANCHO_SET),
    ("GND", F, [(137.45, 168.225), (139.8, 168.225)], ANCHO_SET),

    # ===================== GND: el arbol, TODO en B (sec.7, incl. isla) =====
    # Tronco heredado de v1 hasta la estrella (C1.2) y sus ramas de v1
    # (columnas A/B/C con las U/C/D/R que sobreviven en v2 y sus posiciones
    # de v1), reescrito con las coordenadas reales de v2 (muralla en
    # y=143, no y=154).
    ("GND", B, [(15, 42), (15, 36), (6, 36), (6, 66), (14, 66), (14, 62), (17.5, 62)], ANCHO_POT),
    ("GND", B, [(17.5, 62), (17.5, 74), (35.5, 74), (35.5, 62)], ANCHO_POT),   # C12.2
    ("GND", B, [(35.5, 74), (48, 74), (48, 62)], ANCHO_POT),   # C2.1
    ("GND", B, [(48, 74), (68, 74), (68, 77)], ANCHO_POT),     # TP6
    ("GND", B, [(48, 74), (66, 74), (66, 62)], ANCHO_POT),     # C13.1
    # --- rama columna U1 (+13V1 pre-reg): C17.2 ---
    ("GND", B, [(17.5, 74), (20, 74), (20, 82), (30.5, 82)], ANCHO_POT),   # C17.2
    ("GND", B, [(20, 82), (20, 137), (29.7, 137), (29.7, 143)], ANCHO_POT),  # U1.2
    ("GND", B, [(29.7, 137), (31.4, 137), (31.4, 143)], ANCHO_POT),         # U1.3
    # --- rama columna U3 (+5V, igual v1) ---
    ("GND", B, [(48, 74), (48, 84), (57, 84), (57, 137)], ANCHO_POT),
    ("GND", B, [(57, 84), (64, 84), (64, 82)], ANCHO_POT),    # C9.2
    ("GND", B, [(64, 84), (77.5, 84), (77.5, 82)], ANCHO_POT),  # C10.2
    ("GND", B, [(77.5, 84), (94, 84), (94, 82)], ANCHO_POT),   # C11.2
    ("GND", B, [(57, 84), (89, 84), (89, 105)], ANCHO_POT),    # D6.1
    ("GND", B, [(57, 137), (77.54, 137), (77.54, 143)], ANCHO_POT),  # U3.2
    # --- rama columna U2 (-12V9 pre-reg): C28.1 ---
    ("GND", B, [(66, 74), (106, 74), (106, 82)], ANCHO_POT),   # C28.1
    # bifurcacion a y=95 (no 137): a 137 el tunel B.Cu de /VRAW- (que salta
    # el hub de Net-(U2-ADJ) en 137.5) cruzaba esta horizontal de lleno.
    # rodeo por x=126 en y=90..98: el pad de D13.2 (/VRAW-, radio real
    # 1.1 mm) esta en (122.16,94), a solo 1.54 mm del tramo recto en 123.7.
    ("GND", B, [(106, 74), (123.7, 74), (123.7, 90), (126, 90), (126, 98), (123.7, 98), (123.7, 143)], ANCHO_POT),  # U2.2
    ("GND", B, [(123.7, 95), (127.1, 95), (127.1, 143)], ANCHO_POT),           # U2.4
    # --- rama del crowbar/indicador +12V (banda libre, y=111/119) ---
    ("GND", B, [(20, 82), (20, 105), (15.08, 105), (15.08, 111)], ANCHO_POT),  # Q1.3
    ("GND", B, [(20, 105), (42, 105), (42, 111)], ANCHO_POT),                 # D3.1
    ("GND", B, [(42, 105), (42, 108), (20.16, 108), (20.16, 119)], ANCHO_POT),  # R4.2
    # --- rama del crowbar/indicador -12V ---
    ("GND", B, [(106, 82), (106, 105), (58, 105), (58, 108), (58, 119)], ANCHO_POT),  # R2.1
    # --- rama de salidas: bus y faston de chasis (igual criterio v1) ---
    ("GND", B, [(20, 82), (12, 82), (12, 186), (19.5, 186), (19.5, 190)], ANCHO_POT),  # J5
    ("GND", B, [(19.5, 186), (24.5, 186), (24.5, 190)], ANCHO_POT),
    ("GND", B, [(12, 186), (62.54, 186), (62.54, 172)], ANCHO_POT),   # J2.2
    ("GND", B, [(62.54, 186), (65.08, 186), (65.08, 172)], ANCHO_POT),  # J2.3
    ("GND", B, [(12, 186), (42.54, 186), (42.54, 172)], ANCHO_POT),   # J6.2 (retorno +5V dedicado)
    # --- rama de la isla ultra: entra a B por debajo de J2, alimenta las
    # cuatro columnas de la isla (U4/U5 via EP, U6/U7 via escape propio) y
    # JP1.2 (el unico puente admitido a GNDREF, sec.6.3). ---
    # UNA sola vertical larga (x=92, hasta la granja termica de U4) en vez
    # de tres (92/105/112): una horizontal corta a y=168 (la altura de las
    # granjas) llega a D8.2 y a la granja de U5 sin dejar columnas largas
    # bloqueando toda la franja y=168..186, que SET/OUT necesitan cruzar.
    # entra a la granja por la fila de abajo (168.7, no 168): mas lejos de
    # donde Net-(U4-OUT) sale por y=167.
    ("GND", B, [(62.54, 186), (92, 186), (92, 168.7)], ANCHO_POT),   # -> EP U4 (via farm)
    # D8.2, D9.1 y JP1.2 son SMD de solo F.Cu (D_SMA, NetTie) -- el tronco
    # en B.Cu llega hasta al lado del pad y una via propia (no la granja
    # del EP, que es de otro chip) cruza el ultimo tramo en F.Cu.
    # y=171 (no 168 ni 169.5): 168 esta a 0.5 mm de la via Kelvin en x=95.5;
    # 169.5 se pisa con la fuga de Net-(U5-OUT), que ya usa esa altura.
    ("GND", B, [(92, 168), (92, 171), (112, 171), (112, 168)], ANCHO_POT),  # -> EP U5 (via farm)
    ("GND", B, [(105, 171), (105, 168)], ANCHO_ISLA),
    ("GND", F, [(105, 168), (104, 168)], ANCHO_ISLA),  # via D8.2
    ("GND", B, [(92, 186), (92, 195), (122.5, 195), (124, 195), (124, 168.225)], ANCHO_POT),  # -> escape U6.9
    ("GND", B, [(122.5, 195), (125, 195), (125, 168)], ANCHO_POT),  # -> via D9.1 (esquiva R10.1)
    ("GND", F, [(125, 168), (126, 168)], ANCHO_ISLA),
    # rodeo por x=140.75 en y=174..179: ahi cruza Net-(U6-SET) camino de
    # U7.8 (y=176, hasta x=140.2) -- fuera de su rango y del courtyard de
    # RV3 (que empieza en 141.29).
    ("GND", B, [(122.5, 195), (139.8, 195), (139.8, 179), (140.75, 179),
                (140.75, 174), (139.8, 174), (139.8, 168.225)], ANCHO_POT),  # -> escape U7.9
    ("GND", B, [(122.5, 195), (116.5, 195), (116.5, 175)], ANCHO_POT),  # -> via JP1.2
    ("GND", F, [(116.5, 175), (116.5, 174)], ANCHO_ISLA),
]

# Vias con tamano propio: (x, y, net, ancho_mm, taladro_mm). La granja
# termica del EP de U4/U5 (brief Tarea 8, 3x3, 0.3 mm) vive aqui: el
# footprint DFN-10-1EP (sin "_ThermalVias") no trae vias, a diferencia del
# DFN-12-1EP..._ThermalVias de U6/U7, que YA las trae en el propio pad del
# EP (numero 13) y hereda su red del pad (verificado: 8 sub-pads mas el pad
# grande, todos en /-12V9 — el EP de U6/U7 es -IN, no GND, por diseno del
# LT3094; nada que corregir ahi). Las demas vias son "escapes" cortos de la
# rejilla de F.Cu de la isla hacia el arbol de GND en B.Cu (Kelvin de OUTS
# y GND de los pads SMD que no tienen EP que los lleve gratis).
VIAS: list[tuple[float, float, str, float, float]] = [
    # --- granja termica EP de U4 (3x3, centrada en 92,168, dentro de la
    # huella EP 1.65x2.38 mm) ---
    (91.5, 167.3, "GND", 0.6, 0.3), (92.0, 167.3, "GND", 0.6, 0.3), (92.5, 167.3, "GND", 0.6, 0.3),
    (91.5, 168.0, "GND", 0.6, 0.3), (92.0, 168.0, "GND", 0.6, 0.3), (92.5, 168.0, "GND", 0.6, 0.3),
    (91.5, 168.7, "GND", 0.6, 0.3), (92.0, 168.7, "GND", 0.6, 0.3), (92.5, 168.7, "GND", 0.6, 0.3),
    # --- granja termica EP de U5 (3x3, centrada en 112,168) ---
    (111.5, 167.3, "GND", 0.6, 0.3), (112.0, 167.3, "GND", 0.6, 0.3), (112.5, 167.3, "GND", 0.6, 0.3),
    (111.5, 168.0, "GND", 0.6, 0.3), (112.0, 168.0, "GND", 0.6, 0.3), (112.5, 168.0, "GND", 0.6, 0.3),
    (111.5, 168.7, "GND", 0.6, 0.3), (112.0, 168.7, "GND", 0.6, 0.3), (112.5, 168.7, "GND", 0.6, 0.3),
    # --- escapes GND de U6.9 / U7.9 (sin EP en GND que los lleve gratis) ---
    (124.0, 168.225, "GND", 1.2, 0.6),
    (139.8, 168.225, "GND", 1.2, 0.6),
    # --- escapes GND de D8.2 / D9.1 / JP1.2 (SMD de solo F.Cu) ---
    (105.0, 168.0, "GND", 0.6, 0.3),
    (125.0, 168.0, "GND", 0.6, 0.3),
    (116.5, 175.0, "GND", 0.6, 0.3),
    # --- escape Kelvin de OUTS: U4.9/U5.9 (+12V) y U6.10/U7.10 (-12V) a B ---
    (95.5, 167.5, "+12V", 1.2, 0.6),
    (115.5, 167.5, "+12V", 1.2, 0.6),
    (122.5, 167.65, "-12V", 1.2, 0.6),
    (138.5, 167.65, "-12V", 1.2, 0.6),
    # --- tuneles de +12V/-12V bajo el corredor de +13V1 (y=165, F.Cu) ---
    (45.0, 177.0, "+12V", 1.0, 0.5),
    (45.0, 102.0, "+12V", 1.0, 0.5),
    (48.0, 178.0, "-12V", 1.0, 0.5),
    (48.0, 104.5, "-12V", 1.0, 0.5),
    (70.0, 104.5, "-12V", 1.0, 0.5),
    (78.0, 104.5, "-12V", 1.0, 0.5),
    # --- J2.4/J2.1 (potencia): vias propias junto a cada puente ---
    (67.62, 177.0, "+12V", 1.0, 0.5),
    (56.5, 178.0, "-12V", 1.0, 0.5),
    (56.5, 172.0, "-12V", 1.0, 0.5),
    # --- tunel de /+13V1 (TP7->U1.5) bajo el highway de +12V (y=102) ---
    (34.8, 96.0, "/+13V1", 1.0, 0.5),
    (34.8, 110.0, "/+13V1", 1.0, 0.5),
    (35.0, 174.0, "/+13V1", 1.0, 0.5),
    (35.0, 178.0, "/+13V1", 1.0, 0.5),
    (128.8, 100.0, "/-12V9", 1.0, 0.5),
    (128.8, 104.0, "/-12V9", 1.0, 0.5),
    (128.8, 136.0, "/-12V9", 1.0, 0.5),
    (128.8, 139.0, "/-12V9", 1.0, 0.5),
    (70.0, 103.0, "/VRAW+", 1.0, 0.5),
    (71.0, 107.0, "/VRAW+", 1.0, 0.5),
    (74.0, 135.0, "/VRAW+", 1.0, 0.5),
    (74.0, 139.0, "/VRAW+", 1.0, 0.5),
    (107.0, 175.0, "Net-(U5-OUT)", 0.6, 0.3),
    (107.0, 177.0, "Net-(U5-OUT)", 0.6, 0.3),
    (119.0, 175.0, "Net-(C25-Pad1)", 0.6, 0.3),
    (119.0, 177.0, "Net-(C25-Pad1)", 0.6, 0.3),
    (132.0, 175.0, "Net-(C26-Pad1)", 0.6, 0.3),
    (94.0, 178.0, "-12V", 1.0, 0.5),
    (93.0, 178.0, "-12V", 1.0, 0.5),
    (132.0, 177.0, "Net-(C26-Pad1)", 0.6, 0.3),
    # --- saltos sobre los puentes de ballast (y=183) ---
    (100.7, 181.5, "Net-(U4-SET)", 0.6, 0.3),
    (100.6, 184.5, "Net-(U4-SET)", 0.6, 0.3),
    (110.53, 181.5, "Net-(U5-OUT)", 0.6, 0.3),
    (110.53, 184.5, "Net-(U5-OUT)", 0.6, 0.3),
    (126.7, 181.5, "Net-(U6-SET)", 0.6, 0.3),
    (126.6, 184.5, "Net-(U6-SET)", 0.6, 0.3),
    (134.53, 181.5, "Net-(C26-Pad1)", 0.6, 0.3),
    (134.53, 184.5, "Net-(C26-Pad1)", 0.6, 0.3),
    (125.4, 136.0, "/VRAW-", 1.0, 0.5),
    (125.4, 139.0, "/VRAW-", 1.0, 0.5),
    (51.92, 176.0, "Net-(U1-ADJ)", 0.6, 0.3),
    (77.0, 176.0, "Net-(U1-ADJ)", 0.6, 0.3),
    # --- C19/C20/C21/C22: tramos largos por B.Cu, tuneles cortos en cada punta ---
    (90.0, 167.0, "/+13V1", 1.0, 0.5),
    (90.0, 190.0, "/+13V1", 1.0, 0.5),
    (89.2, 184.0, "/+13V1", 1.0, 0.5),
    (89.2, 188.0, "/+13V1", 1.0, 0.5),
    (120.0, 169.0, "/-12V9", 1.0, 0.5),
    (120.0, 190.0, "/-12V9", 1.0, 0.5),
    # --- tunel de +5V bajo el corredor de +13V1 (y=165) ---
    (40.0, 163.0, "+5V", 1.0, 0.5),
    (40.0, 167.0, "+5V", 1.0, 0.5),
    # --- escape de -12V9 hacia R7.2, por encima de toda la isla (y=150) ---
    (55.0, 163.0, "/-12V9", 1.0, 0.5),
    (55.0, 170.0, "/-12V9", 1.0, 0.5),
    (53.0, 172.0, "/-12V9", 1.0, 0.5),
    (53.0, 184.0, "/-12V9", 1.0, 0.5),
    (53.0, 188.0, "/-12V9", 1.0, 0.5),
    # --- escape de Net-(R7-Pad1) junto a RV3, hacia R7.1 por B.Cu ---
    (146.8, 178.8, "Net-(R7-Pad1)", 1.0, 0.5),
    # --- Net-(R7-Pad1): vuelve a F.Cu para el ultimo tramo (evita el
    # tronco -12V9 que corre por B.Cu en y=196) ---
    (77.0, 197.0, "Net-(R7-Pad1)", 1.0, 0.5),
    # --- OUT/C25/C26-Pad1: directo a B.Cu en el pin y de vuelta en el destino ---
    (93.45, 167.0, "Net-(U4-OUT)", 0.6, 0.3),
    (90.525, 180.0, "Net-(U4-OUT)", 0.6, 0.3),
    (113.45, 167.0, "Net-(U5-OUT)", 0.6, 0.3),
    (110.525, 180.0, "Net-(U5-OUT)", 0.6, 0.3),
    (121.45, 167.325, "Net-(C25-Pad1)", 0.6, 0.3),
    (118.525, 180.0, "Net-(C25-Pad1)", 0.6, 0.3),
    (137.45, 167.325, "Net-(C26-Pad1)", 0.6, 0.3),
    (134.525, 180.0, "Net-(C26-Pad1)", 0.6, 0.3),
    # --- U6/U7 ILIM: salto corto a B.Cu junto a JP1 ---
    (117.3, 169.125, "Net-(U6-ILIM)", 0.6, 0.3),
    (119.175, 173.0, "Net-(U6-ILIM)", 0.6, 0.3),
    (133.0, 169.125, "Net-(U7-ILIM)", 0.6, 0.3),
    (135.175, 173.0, "Net-(U7-ILIM)", 0.6, 0.3),
    # --- escapes SET (U4-SET a U5.7, U6-SET a U7.8), tunel bajo R12/JP1/R14 ---
    (103.0, 176.0, "Net-(U4-SET)", 0.6, 0.3),
    (114.6, 176.0, "Net-(U4-SET)", 0.6, 0.3),
    (127.088, 176.0, "Net-(U6-SET)", 0.6, 0.3),
    (140.2, 176.0, "Net-(U6-SET)", 0.6, 0.3),
]

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
    for x, y, net, ancho, taladro in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetWidth(mm(ancho))
        v.SetDrill(mm(taladro))
        v.SetNet(netinfo[net])
        board.Add(v)
    print(f"pistas: {n_seg} segmentos en {len(TRACKS)} tramos, {len(VIAS)} vias")

    # --- zona GNDREF: la isla de referencia, limitada a ISLA_REF (F.Cu) ---
    # Ningun TRACKS conecta R9.2/C15.2/R10.2/C16.2/R6.2/R8.1/JP1.1: su
    # conectividad la resuelve esta zona (spec sec.6.3), que toca cada pad
    # directamente por estar dentro del rectangulo.
    zona = pcbnew.ZONE(board)
    zona.SetLayer(pcbnew.F_Cu)
    zona.SetNet(netinfo["/GNDREF"])
    x1, y1, x2, y2 = ISLA_REF
    outline = zona.Outline()
    outline.NewOutline()
    for x, y in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
        outline.Append(pcbnew.VECTOR2I(mm(x), mm(y)))
    zona.SetIsFilled(False)
    board.Add(zona)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    print("zona GNDREF creada sobre ISLA_REF y rellenada")

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
