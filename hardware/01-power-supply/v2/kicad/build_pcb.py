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

import math
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
# margen minimo real de fabricacion (JLCPCB 2 capas, 5 mil) -- ver reglas().
# revisar_pistas()/revisar_pista_pad() usaban 0.3mm fijo heredado de v1
# (placa THT); con eso alineado a reglas() el chequeo propio y el DRC real
# dejan de discrepar.
CLEARANCE_MM = 0.127
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
    # x=70 en B.Cu quedaba dentro del tronco -12V (highway F.Cu y=104.5,
    # x48..70) Y de su salto de esquive (B.Cu, x70..78) A LA VEZ que del
    # highway +12V (F.Cu y=102, x45..74) y la horizontal de GND (B.Cu
    # y=105, x58..106) -- las cuatro redes conviven en ese mismo corredor.
    # Rodea todo por el ESTE en B.Cu y regresa a x=74/75 mas abajo, en la
    # banda libre y>111. x=97/99 estan ocupados por los troncos F.Cu de
    # +5V y /VRAW- (verticales largos, y=86..137) -- el cruce de GND (B.Cu,
    # y=105) por F.Cu no cabe entre ellos; se hace en x=102, ya al este de
    # /VRAW-.
    # (72,96): D5.2 (+5V) vive en (75.16,94), pad 2.2x2.2mm -- la diagonal
    # directa pasaba a solo 0.19mm de su borde.
    ("/VRAW+", B, [(70, 90), (72, 96), (87, 98)], ANCHO_POT),
    # D6.1 (GND) es un vertical largo en x=89, y=84..105 -- salto corto a
    # F.Cu solo para cruzarlo.
    ("/VRAW+", F, [(87, 98), (91, 98)], ANCHO_POT),
    ("/VRAW+", B, [(91, 98), (102, 98)], ANCHO_POT),
    ("/VRAW+", B, [(102, 98), (102, 103)], ANCHO_POT),
    ("/VRAW+", F, [(102, 103), (102, 108)], ANCHO_POT),
    ("/VRAW+", B, [(102, 108), (74, 135)], ANCHO_POT),
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
    # salto a B.Cu: a x=34.8 el highway de +12V (10..45, y=102) cruzaria el
    # tronco de lleno (capa distinta, sin roce). Las DOS horizontales de GND
    # (y=105 y 108, columna U1) son TAMBIEN B.Cu -- quedarse recto en
    # x=34.8 SI las cruza de lleno (bug real, quedaba sin corregir). Se
    # rodea por el este (x=43.7, fuera del 20..42 de GND) y se vuelve a
    # x=34.8 ya pasado y=108. x=43.7 (no 44): esa columna tambien tenia
    # que librar la via de +12V en (45,102) -- 44 quedaba a solo 1mm
    # (hacen falta 1.127) y D3.1 (GND, en 42,111) a la vez (hace falta
    # x>=43.527) -- 43.7 cae en la ventana valida entre ambos.
    # D12.2 (linea 428 mas abajo) termina en (34.8,100) -- punto distinto
    # de la via de transicion F/B en (34.8,96); no se tocaban.
    ("/+13V1", F, [(34.8, 96), (34.8, 100)], ANCHO_POT),
    ("/+13V1", B, [(34.8, 96), (43.7, 100)], ANCHO_POT),
    ("/+13V1", B, [(43.7, 100), (43.7, 113)], ANCHO_POT),
    ("/+13V1", B, [(43.7, 113), (34.8, 116)], ANCHO_POT),
    ("/+13V1", F, [(34.8, 116), (34.8, 143)], ANCHO_POT),
    ("/+13V1", F, [(28, 82), (28, 74.5), (34.8, 74.5)], ANCHO_POT),  # C17.1
    ("/+13V1", F, [(28.16, 94), (28.16, 100), (34.8, 100)], ANCHO_POT),  # D12.2
    ("/+13V1", F, [(34.8, 143), (34.8, 165)], ANCHO_POT),
    # R5.1: cruza el hub de Net-(U1-ADJ) en y=176 -- salto corto a B.Cu.
    ("/+13V1", F, [(34.8, 165), (35, 174)], ANCHO_POT),
    ("/+13V1", B, [(35, 174), (35, 178)], ANCHO_POT),
    ("/+13V1", F, [(35, 178), (35, 182)], ANCHO_POT),   # R5.1
    ("/+13V1", F, [(34.8, 165), (110.55, 165)], ANCHO_ISLA),   # corredor alto
    ("/+13V1", F, [(90.55, 165), (90.55, 167.95)], ANCHO_ISLA),   # U4 pines 1-3 (167.95: PG a 168.5 pisa 168)
    ("/+13V1", F, [(100, 165), (100, 168)], ANCHO_ISLA),       # D8.1
    # D10.1 (/+13V1, en 100,180, schottky +12V->+13V1) se habia quedado sin
    # pista propia. Bajar recto por x=100 cruza DOS obstaculos: el tronco
    # GND en B.Cu (y=171, x=92..112) y la horizontal de Net-(U4-SET) en
    # F.Cu (y=174, x=96..101.088) -- se libran por capa cruzando cada una
    # en la capa contraria (F hasta pasar 171, B hasta pasar 174), y el
    # ultimo tramo vuelve a F.Cu tarde (179.5, no antes) para no rozar la
    # diagonal B.Cu de Net-(U4-SET) que baja por ahi (100.6..100.92).
    ("/+13V1", F, [(100, 168), (100, 172.5)], ANCHO_ISLA),
    ("/+13V1", B, [(100, 172.5), (100, 179.5)], ANCHO_ISLA),
    ("/+13V1", F, [(100, 179.5), (100, 180)], ANCHO_ISLA),  # D10.1
    ("/+13V1", F, [(110.55, 165), (110.55, 167.95)], ANCHO_ISLA),  # U5 pines 1-3 (idem U4)
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
    # x=90 cae dentro del hub de GND hacia el EP de U4 (62.54..92, y=186)
    # -- salto a F.Cu solo en ese cruce, en x=89.2 (lejos del ultimo tramo
    # de Net-(U4-OUT) a R15.1, que llega a 90.525/90.537).
    # Net-(U4-OUT) (OUT antes del ballast) cruza esta misma columna DOS
    # veces (su escape en y=167 y su entrada a R15.1 en y=180). El primer
    # cruce se resuelve quedandose en F.Cu (el propio corredor) hasta
    # 168.3, sin bajar a B.Cu todavia -- Net-(U4-OUT) es B.Cu justo ahi.
    # y=167.7 (no 168.3): mas cerca del pad NC de U4.4/PG (90.55,168.5,
    # 0.85x0.25mm) de lo que parecia -- 168.3 quedaba a solo 0.146mm de su
    # esquina (hacen falta 0.377mm en F.Cu, o 0.627 si el propio tramo B.Cu
    # de mas abajo tambien se acercara).
    # la VIA (radio real 0.5, no solo la pista) en (90,167.7) quedaba
    # apretada entre PG (esquina a 90.125,168.375) y Net-(U4-OUT) (y=167)
    # -- ventana negativa en x=90. Jog a x=89.5 solo para la via: se aleja
    # de la esquina de PG (el limitante real) sin acercarse a Net-(U4-OUT)
    # (que no depende de x, es una horizontal).
    ("/+13V1", F, [(90, 165), (89.5, 168.1)], ANCHO_ISLA),
    ("/+13V1", B, [(89.5, 168.1), (90, 179.3)], ANCHO_ISLA),
    # segundo cruce (R15.1, y=180): Net-(U4-OUT) tiene AMBAS cosas ahi, su
    # horizontal B.Cu (88..90.525) Y su vertical F.Cu (90.525..90.537,
    # y=180..186) -- el salto se hace en x=89.3 (lejos del vertical) y con
    # margen de 0.627mm en Y (179.373..180.627) para librar la horizontal.
    # las vias (radio real 0.5) necesitan mas margen que la pista sola --
    # 179.3/180.7 quedaban a 0.7mm de Net-(U4-OUT) en y=180 (hacen falta
    # 0.877). Ensanchado a 179.0/181.0.
    # y=179.1 (no 179.0): ronda 3, F2 -- la rama de potencia de -12V sube
    # de ANCHO_SET a ANCHO_ISLA justo en este tramo (piso duro 0.5mm) y la
    # ventana contra el hub de +12V (177) y esta via quedaba en 0.004mm
    # negativos con la via en 179.0. Subir mas de 179.1 (se probo 179.15)
    # choca por el otro lado con Net-(U4-OUT) (B.Cu, y=180, hace falta
    # 0.877): la ventana real es [179.077,179.123], muy angosta -- 179.1
    # cae justo en medio, con margen de 0.023mm de cada lado.
    ("/+13V1", B, [(90, 179.3), (89.3, 179.1)], ANCHO_ISLA),
    ("/+13V1", F, [(89.3, 179.1), (89.3, 181.0)], ANCHO_ISLA),
    ("/+13V1", B, [(89.3, 181.0), (89.3, 184), (89.2, 184)], ANCHO_ISLA),
    ("/+13V1", F, [(89.2, 184), (89.2, 188)], ANCHO_ISLA),
    ("/+13V1", B, [(89.2, 188), (90, 188), (90, 190)], ANCHO_ISLA),
    ("/+13V1", F, [(90, 190), (90.525, 190), (90.525, 192)], ANCHO_ISLA),   # C19.1
    ("/+13V1", F, [(90, 190), (110.525, 190), (110.525, 192)], ANCHO_ISLA),  # C20.1

    # ===================== /-12V9 (F): U2.5 -> isla ==========================
    ("/-12V9", F, [(126, 74), (128.8, 74), (128.8, 100)], ANCHO_POT),  # TP8 -> U2.5
    ("/-12V9", F, [(124.5, 82), (124.5, 74), (126, 74)], ANCHO_ISLA),  # C18.2
    # salto a B.Cu: a x=128.8 la bajada de Net-(U2-ADJ) (122..145.2, y=137.5)
    # cruzaria el tronco de lleno.
    ("/-12V9", B, [(128.8, 100), (128.8, 104)], ANCHO_POT),
    ("/-12V9", F, [(128.8, 104), (128.8, 136)], ANCHO_POT),
    # segundo salto: Net-(U2-ADJ) tambien pasa por aqui, en y=137.5.
    ("/-12V9", B, [(128.8, 136), (128.8, 139)], ANCHO_POT),
    ("/-12V9", F, [(128.8, 139), (128.8, 143)], ANCHO_POT),
    ("/-12V9", F, [(112, 94), (112, 100), (128.8, 100)], ANCHO_POT),  # D13.1
    # partido en dos tramos en (128.8,150), no uno solo: la linea de abajo
    # (128.8,150)-(...)-(55,163)) arrancaba justo en medio de este, sin
    # vertice compartido -- "dangling" en DRC real pese a tocarse por
    # ancho (ronda 2, limpieza).
    ("/-12V9", F, [(128.8, 143), (128.8, 150)], ANCHO_POT),
    ("/-12V9", F, [(128.8, 150), (128.8, 165)], ANCHO_POT),
    ("/-12V9", F, [(128.8, 165), (118.55, 165), (118.55, 166.875)], ANCHO_ISLA),  # U6 1-3
    ("/-12V9", F, [(130, 165), (130, 168)], ANCHO_ISLA),   # D9.2
    # D11.2 (/-12V9, en 130,180) comparte exactamente la misma x que D9.2
    # (130,168) -- recto entre los dos, sin cruzar nada (R10/C16 no llegan
    # a x=130 en este rango de Y).
    ("/-12V9", F, [(130, 168), (130, 180)], ANCHO_ISLA),  # D9.2 -> D11.2
    ("/-12V9", F, [(134.55, 165), (134.55, 166.875)], ANCHO_ISLA),  # U7 1-3
    ("/-12V9", F, [(118.55, 165), (134.55, 165)], ANCHO_ISLA),
    # el track de arriba solo toca el pin 1 de cada chip (166.875); los
    # pines 2 y 3 (167.325/167.775, mismo net, 0.45mm de paso) son pads
    # separados y quedaban sin puente fisico propio -- DRC real los
    # marcaba "unconnected" aunque logicamente compartan red.
    ("/-12V9", F, [(118.55, 166.875), (118.55, 167.775)], ANCHO_SET),  # U6 pines 1-2-3
    ("/-12V9", F, [(134.55, 166.875), (134.55, 167.775)], ANCHO_SET),  # U7 pines 1-2-3
    # el EP de U6 (120,168, caja 119.175..120.825/166.81..169.19) ya lo
    # toca el tramo de mas abajo (120,165)-(120,169); el de U7 (136,168,
    # caja 135.175..136.825/166.81..169.19) no tiene equivalente -- se
    # conecta aqui, corto, desde el pin 3.
    ("/-12V9", F, [(134.55, 167.775), (135.3, 167.775)], ANCHO_SET),  # U7 pin3 -> EP
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
    # Net-(C25-Pad1) cruza esta columna en y=174.5 -- salto corto a F.Cu.
    # las vias del salto (radio real) tambien tienen que librar a R13
    # (ILIM, sus dos pines a 119.175/120.825 dejan solo 0.85mm de hueco
    # en x=120 -- ni centrada cabe una via de 0.6mm con margen) ADEMAS de
    # Net-(C25-Pad1) en y=174.5. 173.8/175.2 caian dentro del propio pad
    # de R13 (173.525..174.475). Ensanchado a 173.0/175.3.
    ("/-12V9", B, [(120, 169), (120, 172.8)], ANCHO_ISLA),
    ("/-12V9", F, [(120, 172.8), (120, 175.5)], ANCHO_ISLA),
    ("/-12V9", B, [(120, 175.5), (120, 190)], ANCHO_ISLA),
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
    # x=58.5 (ni 53 ni 54): la fila entera de RV2 (tres pines, 51.92..
    # 57.72 con caja) bloquea cualquier columna entre RV2.3 y RV2.1 -- no
    # hay hueco limpio ahi para pasar entre pines. Rodea la fila entera
    # por el este. Se queda en B.Cu de punta a punta: la diagonal cruzaba
    # el ramal F.Cu de -12V a J2.1 (56.5..60,y=172) de lleno.
    # sigue recto en x=55 (oeste de 56.5, donde vive el vertical B.Cu de
    # -12V a J2.1, que para en 178) hasta y=180 -- justo en el hueco entre
    # ese vertical (hace falta y>=179.377) y la fila de RV2 (hace falta
    # y<=180.653) -- antes de girar al este.
    ("/-12V9", B, [(55, 163), (55, 180), (58.5, 180), (58.5, 184)], ANCHO_POT),
    ("/-12V9", F, [(58.5, 184), (58.5, 188)], ANCHO_POT),
    ("/-12V9", B, [(58.5, 188), (58.5, 196), (74, 196)], ANCHO_POT),
    # ancho fino (ISLA, no POT) SOLO en el tramo que pasa junto a la via
    # de Net-(R7-Pad1) (77,197, radio real 0.5) -- con ANCHO_POT completo
    # el hueco de 1mm no alcanzaba (hacen falta 1.127); con ISLA si (0.877).
    ("/-12V9", B, [(74, 196), (80, 196)], ANCHO_ISLA),
    ("/-12V9", B, [(80, 196), (87.16, 196), (87.16, 192)], ANCHO_POT),

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
    # R6.1 (pasante): salta a B.Cu en x=66.4 (no en 67.62 ni en 77): el
    # hub F.Cu de +12V (ronda 2, ANCHO_KELVIN) SOLO existe al ESTE de
    # 67.62 (al oeste, hacia el tunel, sigue fino) -- cruzando en B.Cu
    # ANTES de 67.62 se evita el hub por completo (capa distinta donde
    # exista) y solo hace falta separacion en X de la propia bajada
    # vertical de +12V (B.Cu, en 67.62,177..172): 67.62-66.4=1.22mm,
    # mayor que el minimo real (0.75+0.2+0.127=1.077).
    # x=67.62 es un CRUCE real, no una simple cercania: la bajada B.Cu de
    # +12V (172..177) pasa justo por y=176 en ese x -- cualquier pista de
    # -12V/ADJ que tambien pise B.Cu ahi se cruza de lleno (no es cuestion
    # de margen, se tocan). Salta a B.Cu en x=66.2 (fuera del rango del
    # vertical Y de las dos vias de GND de J2.2/J2.3 en 62.54/65.08), pero
    # en vez de seguir a y=176 (que cruza igual la bajada de +12V), baja
    # primero a y=178.6 -- fuera del rango Y de esa bajada (172..177) Y
    # del hub F.Cu de +12V (177) -- y solo entonces gira hacia R6.1.
    # 178.6 (no menos) tambien libra por 0.048mm el tramo oeste de -12V,
    # que corre por y=178.1 en esta misma franja de X.
    ("Net-(U1-ADJ)", F, [(25, 176), (66.2, 176)], ANCHO_SEN),
    ("Net-(U1-ADJ)", B, [(66.2, 176), (66.2, 178.6), (77, 178.6), (77, 182)], ANCHO_SEN),   # R6.1
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
    # el "hueco deliberado" que -12V dice dejarle (comentario junto a su
    # zigzag, mas abajo) en realidad no existe: su dip a y=103 ocupa TODO
    # x=84..89 sin corte. Salto corto a B.Cu para cruzarlo.
    # salta a B.Cu de una vez (la muesca de GND en x=68..88,y=108 deja el
    # hueco): cruza TODO el tramo -12V (F.Cu, y=103) sin tocarlo por ser
    # otra capa, y sale a F.Cu ya en y=100, fuera de esa franja.
    ("Net-(D6-A)", F, [(86.46, 105), (86.46, 103.9)], ANCHO_SEN),
    ("Net-(D6-A)", B, [(86.46, 103.9), (86.46, 100)], ANCHO_SEN),
    ("Net-(D6-A)", F, [(86.46, 100), (86.46, 99), (95.16, 99), (95.16, 94)], ANCHO_SEN),
    ("Net-(D7-A)", F, [(33.62, 111), (33.62, 115), (26, 115), (26, 119)], ANCHO_SEN),
    ("Net-(D7-A)", F, [(26, 115), (10, 115), (10, 119)], ANCHO_SEN),
    # Q1.2 (Net-(D7-A), en 12.54,111) se habia quedado sin pista propia --
    # rodeo por y=113.5 (no recto a 111) para no rozar Q1.3 (GND, en
    # 15.08,111, pad vecino del mismo transistor).
    ("Net-(D7-A)", F, [(12.54, 111), (12.54, 113.5), (33.62, 113.5), (33.62, 111)], ANCHO_POT),  # Q1.2

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
    # C23.2 (GND, en 93.475,180) vive justo en esta columna -- salto a
    # B.Cu solo para cruzar su caja (179.1..180.9).
    # margen real: la caja de C23.2 es 179.1..180.9, hace falta 0.377mm
    # mas alla del borde -- 181/179 se quedaban a solo 0.1mm.
    # ronda 2, Important 1: R15/R16->J2.4 tiene que ser >=1.5mm TODO el
    # recorrido (brief sec.6.1) -- de 183 a 67.62 (el tap de J2.4, mas
    # abajo) sube de ANCHO_ISLA a ANCHO_KELVIN. Mas alla de 67.62 (67.62 a
    # 45 y el tunel) ya no es "ballast->J2", es la rama de crowbar/
    # indicador (Q1/D7/R1/TP3) -- se queda en ANCHO_ISLA, no lo pide el brief.
    # 183..181.5 tambien se queda en ANCHO_ISLA: a KELVIN pisa el pad
    # C23.2[GND] (179.1..180.9, a solo 0.6mm del endpoint en 181.5).
    ("+12V", F, [(93.463, 183), (93.463, 181.5)], ANCHO_ISLA),
    # y=178.6 (no 178.5): el propio -12V cruza aqui en B.Cu, ancho fino,
    # a y=178 (linea 92.8..94.5) -- 178.5 quedaba a solo 0.5mm.
    # y=178.7 (no 178.6): el tramo B.Cu de -12V que cruza esta columna
    # camino de GND (94.5..92.6,y=178) pasaba justo por (93.463,178),
    # a solo 0.6mm del final de este B.Cu (hacen falta 0.627).
    # 181.5..177 SE QUEDA en ANCHO_ISLA (no sube a KELVIN): es el mismo
    # pinch de -12V documentado mas abajo (GND@92 y este mismo vertical de
    # +12V, solo 1.463mm entre los dos) -- ahora que -12V tambien tiene
    # que cruzarlo (su cruce SET en y=178, camino del tap de J2.1), un
    # +12V de 1.5mm ahi no deja margen ni para el cruce fino de -12V ni
    # para el propio tramo de -12V en y=178/178.2. Mismo tipo de
    # excepcion fisica ya documentada, no descuido.
    ("+12V", B, [(93.463, 181.5), (93.463, 178.6)], ANCHO_ISLA),
    ("+12V", F, [(93.463, 178.6), (93.463, 177)], ANCHO_ISLA),
    ("+12V", F, [(93.463, 177), (67.62, 177)], ANCHO_KELVIN),
    ("+12V", F, [(67.62, 177), (45, 177)], ANCHO_ISLA),
    ("+12V", B, [(45, 177), (45, 102)], ANCHO_ISLA),   # tunel bajo el corredor +13V1 (y=165)
    ("+12V", F, [(45, 102), (10, 102)], ANCHO_KELVIN),
    ("+12V", F, [(10, 102), (10, 111)], ANCHO_KELVIN),    # Q1.1
    ("+12V", F, [(26, 102), (26, 111)], ANCHO_KELVIN),    # D7.1
    # R1.1: x=36 (no 45) -- a 45 la bajada cruzaba Net-(D3-A) de lleno
    # (39.46..52.16, y=115).
    # x=37 (no 38): D3.2 (Net-D3-A, en 39.46,111) quedaba a solo 0.56mm de
    # su borde (hacen falta 0.877 con ANCHO_KELVIN).
    ("+12V", F, [(45, 102), (37, 102), (37, 119), (42, 119)], ANCHO_KELVIN),   # R1.1
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
    ("+12V", B, [(95.5, 166.3), (112, 166.3)], ANCHO_ISLA),
    # ancho fino (SET) SOLO junto a x=113.45: la via de escape de
    # Net-(U5-OUT) tiene que librar A LA VEZ a U5.9 (167.375, arriba) y a
    # este bus (166.3, abajo) -- con ANCHO_ISLA la ventana es negativa.
    ("+12V", B, [(112, 166.3), (115.5, 166.3)], ANCHO_SET),
    ("+12V", B, [(115.5, 166.3), (115.5, 167.5)], ANCHO_KELVIN),
    # baja recto a y=158 (todavia en x=95.5, al este de Net-(U4-OUT) que
    # vive en 88..93.45) ANTES de girar hacia J2 -- la diagonal directa
    # desde 167.5 pasaba a solo 0.42mm de la fuga de esa red en y=167.
    ("+12V", B, [(95.5, 167.5), (95.5, 158)], ANCHO_ISLA),
    ("+12V", B, [(95.5, 158), (67.62, 155)], ANCHO_ISLA),
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
    # C25.2 (GND, en 121.475,180) vive justo en esta columna -- salto a
    # B.Cu solo para cruzar su caja (179.1..180.9).
    # margen real: la caja de C25.2 es 179.1..180.9, hace falta 0.377mm
    # mas alla del borde -- 181/179 se quedaban a solo 0.1mm.
    # ronda 2, Important 1: R17/R18->J2.1 tambien >=1.5mm todo el recorrido,
    # espejo de +12V. De 183 a 92.73 sube a ANCHO_KELVIN (excepto el
    # cruce de 94.5..92.73, que se queda en SET -- ver el comentario de
    # la ventana valida de 0.6mm arriba, fisicamente no cabe 1.5mm ahi
    # sin tocar a la vez la via de +12V y al tronco de GND del EP de U4).
    # 183..178 se queda en ANCHO_ISLA (no KELVIN), espejo exacto del
    # mismo fix en +12V: a KELVIN pisa el pad C25.2[GND] (179.1..180.9,
    # a 0.6mm de 181.5 y 0.5mm de 178.6 -- ninguno de los dos alcanza con
    # 0.75mm de semi-ancho).
    ("-12V", F, [(121.463, 183), (121.463, 181.5)], ANCHO_ISLA),
    ("-12V", B, [(121.463, 181.5), (121.463, 178.6)], ANCHO_KELVIN),
    ("-12V", F, [(121.463, 178.6), (121.463, 178)], ANCHO_ISLA),
    # muesca en x=93..94: ahi sube la bajada F.Cu de +12V del puente
    # (y=183) a su propio hub (y=177), y cruzaria el hub de -12V de lleno.
    # la muesca anterior (179.5) seguia DENTRO del rango y=177..183 de la
    # bajada de +12V -- se necesita salir de ese rango, no solo desviarse
    # en x. y=183.5 esta justo debajo (+12V para en 183) y libre de R6
    # (que empieza en x=75.91, lejos de este tramo en x=91..96).
    # la bajada de +12V al puente (93.463) ocupa TODO y=177..186 (su tramo
    # 177..183 mas el 183..186 del propio puente) -- no hay hueco en Y
    # posible ahi. Salto a B.Cu solo para cruzar ese punto.
    # el vertical de +12V (93.463, F.Cu, y=177..183) y el de GND hacia el EP
    # de U4 (92, B.Cu, y=168.7..195) estan a solo 1.463mm. La via de
    # transicion en si (no solo la pista) tiene que librar a los DOS: con
    # el radio MINIMO real (0.6mm de ancho, 0.3 de radio) la ventana valida
    # es x<=93.463-0.3-0.127=93.036 (para +12V, F.Cu) Y x>=92+0.3+0.127=
    # 92.427 (para GND, B.Cu) -- ES decir [92.427,93.036], casi 0.6mm de
    # ancho. (Los intentos anteriores con anchos de pista de sobra --
    # ANCHO_ISLA/KELVIN en vez del radio real de la via -- daban una
    # ventana negativa; el error estaba ahi, no en la geometria.)
    # ronda 2: este tramo (94.5..121.463) tampoco puede subir a
    # ANCHO_KELVIN. No es el paralelismo con +12V (ese hub no llega hasta
    # aqui) sino tres cruces perpendiculares que, entre las dos capas,
    # cubren TODO el hueco vertical disponible sin dejar Y libre para
    # 1.5mm: Net-(U4-SET) (F, y=174..177.2, en x~101), Net-(U5-OUT) (F
    # y=175..177 + B y=177..180, en x=107) y Net-(C25-Pad1) (idem, x=119)
    # -- y ademas C24/C25 (los propios capacitores SET/OUT, pad 0.575x1.35)
    # tapan y=178.65..181.35 justo ahi por debajo, sin hueco para rodear.
    # Probado con muescas locales (F/B y en Y): cada intento choca con el
    # pad del propio capacitor o con la fuga que se queria esquivar --
    # fisicamente no cabe 1.5mm en este tramo tampoco. Se queda en
    # ANCHO_ISLA (el ancho original), igual criterio que el tramo de abajo.
    # ronda 3, F2: medido con el propio build_pcb.py (KELVIN de punta a
    # punta SI falla, con numeros reales: -0.07/-0.25/0.00/0.00/0.04/-0.06mm
    # contra Net-(U4-SET)/Net-(U5-OUT)/Net-(C25-Pad1)/+12V) -- pero los
    # choques son puntuales (tres cruces perpendiculares en x~101/107/119
    # mas la cercania a +12V en x~93.463), no un paralelismo sostenido.
    # Entre cada cruce SI cabe 1.5mm: muescas cortas a 0.5mm solo en cada
    # punto conflictivo, KELVIN en el resto (unos 21mm de los 27mm totales).
    # las vias de escape (0.6/0.3mm, radio 0.3) piden mas margen que la
    # sola pista (via_radio + semi-KELVIN 0.75 + 0.127 = 1.177mm, no
    # 1.002/1.127) -- primer intento se quedaba corto por 0.02-0.09mm en
    # las tres, medido con el propio build_pcb.py.
    ("-12V", F, [(121.463, 178), (119.7, 178)], ANCHO_KELVIN),
    ("-12V", F, [(119.7, 178), (118.3, 178)], ANCHO_ISLA),      # Net-(C25-Pad1) en x=119
    ("-12V", F, [(118.3, 178), (107.7, 178)], ANCHO_KELVIN),
    ("-12V", F, [(107.7, 178), (106.3, 178)], ANCHO_ISLA),      # Net-(U5-OUT) en x=107
    ("-12V", F, [(106.3, 178), (101.9, 178)], ANCHO_KELVIN),
    ("-12V", F, [(101.9, 178), (99.95, 178)], ANCHO_ISLA),      # Net-(U4-SET) en x=100.922
    ("-12V", F, [(99.95, 178), (95, 178)], ANCHO_KELVIN),
    ("-12V", F, [(95, 178), (94.5, 178)], ANCHO_ISLA),          # cercania al vertical/hub de +12V (93.463)
    # ronda 3, F2: piso duro 0.5mm en TODA la rama de potencia (ya no hay
    # excepcion a 0.25mm). Sube de ANCHO_SET a ANCHO_ISLA. El waypoint
    # intermedio baja a y=177.8 (no 178) para ganar el margen que
    # ANCHO_ISLA (semi-ancho 0.25, contra 0.125 de SET) necesita de mas
    # contra la VIA de transicion de +12V en (93.463,178.6) (no solo la
    # pista): con el waypoint en (93.0,178) la via quedaba a 0.12mm
    # (hacen falta 0.677 = radio via 0.3 + semi-ancho 0.25 + 0.127); a
    # (93.0,177.8) abre el margen necesario.
    ("-12V", B, [(94.5, 178), (93.0, 177.8), (92.73, 178.2)], ANCHO_ISLA),
    # ronda 3, F2: sube de ANCHO_SET a ANCHO_ISLA (piso duro 0.5mm). NO
    # sube a ANCHO_KELVIN -- la cuenta del corredor de 3 hubs en 4.03mm de
    # alto sigue siendo la misma (ver ronda 2 mas arriba: con -12V a
    # KELVIN hacen falta 1.627mm de hueco donde solo hay margen para uno
    # de los dos, no los dos). Con ANCHO_ISLA la via de /+13V1 (radio
    # 0.5mm) se movio de y=179.0 a 179.15 para abrir una ventana real
    # (antes 0.004mm negativos, ahora 0.146mm) -- ver esa via mas arriba.
    # 92.73..67.62 se queda en ANCHO_ISLA: corre en PARALELO sostenido al
    # hub GORDO de +12V (ANCHO_KELVIN, y=177) en todo ese tramo -- ahi si
    # es un paralelismo real, no cruces puntuales, y la cuenta de la
    # ronda 2 (1.627mm de separacion necesaria contra ~1.2mm reales)
    # sigue sin cambiar. Pasado 67.62 (donde el propio hub de +12V se
    # adelgaza a ANCHO_ISLA para la rama de crowbar) el paralelismo deja
    # de exigir tanto margen -- KELVIN si cabe ahi.
    # el corte real no es en 67.62 (ahi termina el tramo GORDO del hub,
    # y su propio endpoint/via todavia exige el margen completo de dos
    # KELVIN, 1.627mm) sino mas al oeste: medido, hace falta x<=66.52.
    ("-12V", F, [(92.73, 178.2), (66.5, 178.2)], ANCHO_ISLA),
    ("-12V", F, [(66.5, 178.2), (60, 178.2)], ANCHO_KELVIN),
    ("-12V", B, [(60, 178.2), (60, 172)], ANCHO_KELVIN),  # -> J2.1
    ("-12V", F, [(60, 178.2), (48, 178.2)], ANCHO_ISLA),
    ("-12V", B, [(48, 178.2), (48, 104.5)], ANCHO_ISLA),      # tunel bajo el corredor +13V1
    # y=104.5 (no 101): a 101 el highway quedaba a solo 1 mm del de +12V
    # (y=102), y los dos son de 1.5 mm -- hacian falta 1.5 mm de hueco.
    ("-12V", F, [(48, 104.5), (70, 104.5)], ANCHO_KELVIN),
    # salto a B para esquivar TP3.1 de +12V (vertical F.Cu en x=74, y=102..
    # 111): sube a y=100 (fuera de esa franja) y cruza; el regreso a F.Cu
    # se hace en x=78 (ya al este de x=74), NO en x=70/78,y=104.5 -- ahi
    # rozaba la horizontal de GND (B.Cu, y=105) por solo 0.5mm.
    ("-12V", B, [(70, 104.5), (70, 100), (78, 100)], ANCHO_KELVIN),
    ("-12V", F, [(78, 100), (78, 104.5)], ANCHO_KELVIN),
    # huecos deliberados: Net-(D6-A) cruza x=86.46 a y=104.5, y Net-(D4-A)
    # cruza x=58 a y=115 -- las dos vías de -12V se parten para dejarlas
    # pasar sin tocarlas.
    # rodeo por y=103 en x=84..89 (no un hueco a la misma altura): el pad
    # de D6.2 usa radio real (max dimension/2 = 0.9 mm) desde su centro en
    # 86.46,105 -- el hueco anterior (85..88 a la misma y) quedaba a solo
    # 0.06 mm del radio del pad.
    # D6.1 (GND, en 89,105) es un vecino ancho (1.8x1.8mm) justo donde el
    # rodeo volvia a y=104.5 -- el regreso real se hace en x=91 (fuera de
    # su caja) y solo se acerca a TP4 (x=90) ya pasado su borde inferior
    # (y=107, la caja para en 105.9).
    # ANCHO_ISLA (no KELVIN) SOLO en este rodeo: la via de escape de D6.2
    # (Net-(D6-A), en 86.46,103.9) cae dentro de este tramo (x=84..91) y
    # con 1.5mm de ancho la ventana entre el taladro de D6.2 y esta pista
    # era negativa. Rama de crowbar/indicador, no "ballast->J2" (ver
    # ronda 2 Important 1) -- adelgazar aqui no toca ningun requisito.
    ("-12V", F, [(78, 104.5), (84, 104.5), (84, 103), (91, 103), (91, 107), (90, 107)], ANCHO_ISLA),
    # D4.1: DRC real seguia marcando "dangling" el empalme en T con la
    # horizontal (dos tramos colineales + este vertical perpendicular),
    # aun partiendo la horizontal y con via propia -- pcbnew lo ve 100%
    # conectado (GetConnectivity confirma), pero el checker de KiCad no
    # reconoce una T sin cambio de capa real como junta valida. Patron
    # que SI funciona en el resto del fichero (granjas EP, stubs de
    # retorno GND): una via que cambia de capa de verdad, tocando el
    # tronco SIN partirlo, en un punto lejos de x=58 (columna de GND,
    # y=105..108). Rodeo por x=50 (libre de GND: su horizontal solo
    # llega a x=58) para la transicion F/B.
    # el rodeo a y=110 pisaba el pad D4.2[Net-(D4-A)] (borde real en
    # 110.1, no hay margen con ANCHO_KELVIN) -- entre GND (borde en 108)
    # y D4.2 (borde en 110.1) solo quedan 2.1mm, y KELVIN necesita 2.254
    # (1.377 de un lado + 0.877 del otro). Con ANCHO_ISLA en el tramo
    # horizontal (el vertical de bajada, en x=58, no cruza a D4.2 -- su
    # caja para en x=56.36) SI cabe: 108.877..109.723.
    # y=111 (no 113): el pad real de D4.1 esta centrado en (58,111), no
    # en 113 -- el endpoint viejo caia 1.1mm mas alla del borde del pad
    # (111.9). Conectaba igual por solape de cobre (KELVIN de sobra) pero
    # el checker de "dangling" lo marcaba por no coincidir con el pad.
    ("-12V", F, [(58, 111), (58, 109.3)], ANCHO_KELVIN),
    ("-12V", F, [(58, 109.3), (50, 109.3)], ANCHO_ISLA),
    ("-12V", B, [(50, 109.3), (50, 104.5)], ANCHO_ISLA),
    # el tramo "R2.1" que seguia hasta (58,119) era un bug: R2.1 es GND
    # (retorno del indicador D4/R2), no -12V -- terminaba encima de un
    # pad ajeno de verdad. D4.1 (arriba) ya cierra la conexion real de
    # -12V en esta columna; se borra el resto.
    ("-12V", F, [(90, 107), (90, 111)], ANCHO_KELVIN),    # TP4.1
    # J2.1 (potencia): FIX critico (ronda 2) -- el puente que unia el tunel
    # de potencia (48,153) con el bus Kelvin de sense (127.3,153..60,172)
    # fusionaba las dos ramas de -12V ANTES de J2.1, exactamente lo que el
    # Kelvin prohibe (brief sec.6.1: solo se tocan en el pad). Se borra ese
    # puente; la rama de potencia ahora entra a J2.1 por su cuenta, con un
    # tap propio a x=60 (la x del propio pad) sobre el hub F.Cu de y=178
    # -- espejo exacto de como +12V entra a J2.4 (tap a x=67.62 sobre su
    # hub de y=177, ver mas abajo esa seccion).
    # Kelvin de U6.10/U7.10 (pines 10, 121.45/137.45,167.775): el tramo
    # F.Cu que las une a su via de escape, que faltaba.
    # y=167.75 (no 167.65, borde SUPERIOR del pad): a 167.65 quedaba a
    # solo 0.2mm de U6.11/U7.11 (Net-C25/26-Pad1, en 167.325) -- 167.75
    # sigue dentro del pad real de -12V (167.65..167.9) y gana margen de
    # los DOS vecinos (Net-C25/26-Pad1 arriba, GND en 168.225 abajo).
    # x=128.0/133.5 (no 122.6/138.5) para la via de transicion: la via
    # (radio 0.6) caia dentro del rango x=121.45..125.5/137.45..141.0 de
    # la fuga fina de GND (U6.9/U7.9) en y=168.225, 0.475mm mas abajo --
    # ni con la via al minimo (0.6mm) alcanzaba el margen (hace falta
    # 0.552). Se alarga el tramo F.Cu de partida hasta salir del rango.
    # sigue en F.Cu (no B.Cu -- ahi choca con Net-(C25/26-Pad1) y las vias
    # de escape de GND en 125/125.5) pero esquiva D9.1 (GND, en 126,168,
    # pad 2.5x1.8mm, y=167.1..168.9) con una muesca a y=166.5 (al norte,
    # fuera de su caja) en vez de seguir recto en y=167.75.
    # x=122.3 (no 122): U6.11/U6.12 (Net-C25-Pad1, columna en 121.45)
    # quedaban a solo 0.125mm de su borde.
    ("-12V", F, [(121.45, 167.75), (122.3, 167.75), (122.3, 166.5),
                 (127.3, 166.5), (127.3, 166.55)], ANCHO_SET),
    # lado U7: NO se puede subir en x=137.3 -- esa columna entera (U7.7..
    # U7.12) esta al mismo x=137.45, con caja hasta 137.875. Hay que salir
    # al ESTE de toda la columna antes de subir.
    ("-12V", F, [(137.45, 167.75), (138.7, 167.75), (138.7, 166.55)], ANCHO_SET),
    # y=166.7 (no 167.75) y ancho fino: pasa entre el corredor +13V1 (165)
    # y las vias de escape de GND en 124/125/139.8 (168.1..168.225), solo
    # 3.1 mm de hueco real -- no cabe ANCHO_KELVIN ahi.
    # y=166.6 (no 166.7) y x=123 (no 122.5): quedaban a 0.12/0.05mm de
    # Net-(C25/C26-Pad1) (hace falta 0.127mm).
    ("-12V", B, [(127.3, 166.55), (135, 166.55)], ANCHO_ISLA),
    # ancho fino junto a x=137.45: la via de escape de Net-(C26-Pad1)
    # tiene que librar A LA VEZ a este detour (166.55) y a su propia
    # salida de -12V mas abajo (167.75) -- con ANCHO_ISLA la ventana es
    # negativa.
    ("-12V", B, [(135, 166.55), (138.7, 166.55)], ANCHO_SET),
    # la diagonal directa cruzaba la horizontal Kelvin de +12V (166.3) y su
    # propia diagonal (155). Baja recta a y=153 (por debajo de las dos)
    # ANTES de cruzar hacia la izquierda, y solo entonces gira hacia J2.1.
    # arranca en (127.3,166.6), no (127.3,167.75): ese punto ya no existe
    # en el camino nuevo (ver la muesca de arriba, que llega derecho a
    # 166.6).
    ("-12V", B, [(127.3, 166.55), (127.3, 153), (60, 153), (60, 172)], ANCHO_KELVIN),

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
    # cruza el hub F.Cu de -12V (y=178) de lleno -- salto corto a B.Cu.
    ("Net-(U4-SET)", F, [(101.088, 174), (100.922, 177.2)], ANCHO_SET),
    # D10.1 (/+13V1, en 100,180, pad 2.5x1.8mm) vive justo en el tramo
    # siguiente -- se queda en B.Cu (inmune, capa distinta) en vez de
    # volver a F.Cu solo para ese cruce.
    ("Net-(U4-SET)", B, [(100.922, 177.2), (100.84, 178.8), (100.7, 181.5), (100.6, 184.5)], ANCHO_SET),
    ("Net-(U4-SET)", F, [(100.6, 184.5), (100.525, 186)], ANCHO_SET),
    # -> U5.7: R9.1 esquiva la fila de R12/JP1 (174) por B.Cu (y=176) y
    # entra a U5.7 por la derecha del chip (114.6, fuera de JP1 y del
    # cuerpo de U5).
    # R9.2 (/GNDREF, en 102.912,174) es el OTRO pin del mismo 0805 --
    # pasar recto por y=174 hacia x=103 lo rozaba de lleno. Rodeo por
    # y=175.5 (debajo de su caja, que para en 174.7).
    ("Net-(U4-SET)", F, [(101.088, 174), (101.088, 175.5), (104, 175.5), (104, 176)], ANCHO_SET),
    ("Net-(U4-SET)", B, [(104, 176), (114.6, 176)], ANCHO_SET),
    ("Net-(U4-SET)", F, [(114.6, 176), (114.6, 168.6), (113.45, 168.6)], ANCHO_SET),  # U5.7 (168.6, no 168.5: idem U4.7)
    # y=168.7 (no 168.8): a 168.8 quedaba a solo 0.2mm de VIOC (pin7,
    # 169.0..169.25) -- 168.7 sigue dentro del pad real de SET (168.55..
    # 168.8) y gana margen de los DOS vecinos (VIOC abajo, GND arriba).
    ("Net-(U6-SET)", F, [(121.45, 168.7), (124, 168.7), (124, 174), (127.088, 174)], ANCHO_SET),  # U6.8 -> R10.1
    # R10.1 -> C16.1: cruza el puente de -12V en y=183 -- salto a B.Cu.
    # D11.1 (-12V, en 126,180, pad 2.5x1.8mm) vive en el mismo tramo --
    # se queda en B.Cu desde antes (inmune) en vez de cruzarlo en F.Cu.
    ("Net-(U6-SET)", B, [(127.088, 174), (126.7, 181.5), (126.6, 184.5)], ANCHO_SET),
    # ronda 2, limpieza: el endpoint real de C16.1 es (126.525,186), no
    # (128.025,186) -- bug de coordenada (offset de pad mal copiado; C15.1,
    # el espejo de U4, usa correctamente 100.525 = centro 102 - 1.475).
    # El tramo viejo solo tocaba a C16.1 de refilon (cruzaba su caja a
    # mitad de camino, no en el propio endpoint) -- "dangling" en DRC real.
    ("Net-(U6-SET)", F, [(126.6, 184.5), (126.525, 186)], ANCHO_SET),
    # -> U7.8: mismo criterio, esquiva R14 (174) por B.Cu a y=176 y entra
    # a U7.8 por la derecha (140.2, fuera de la via de escape GND de U7.9
    # en 139,168.225 y del cuerpo de U7).
    ("Net-(U6-SET)", F, [(127.088, 174), (127.088, 176)], ANCHO_SET),
    # x=139.7 (no 140.2): quedaba a solo 0.55mm del vertical de GND en
    # 140.75 (hacen falta 0.625mm).
    ("Net-(U6-SET)", B, [(127.088, 176), (139.7, 176)], ANCHO_SET),
    ("Net-(U6-SET)", F, [(139.7, 176), (139.7, 168.7), (137.45, 168.7)], ANCHO_SET),  # U7.8 (idem U6.8)

    # ===================== ILIM, uno por chip (F) ============================
    # La diagonal directa del pin ILIM a su resistencia pasaba a 0.18 mm de
    # la diagonal OUT->C->ballast del mismo chip (ambas cruzan la misma
    # esquina). Sale por la izquierda de cada chip (fuera del cuerpo, fuera
    # del camino de OUT que se queda del lado derecho/centro) y entra a su
    # resistencia por y=174 desde el otro lado.
    # y=169.05 (no 169, el centro exacto del pin): PG (pin4, NC) esta a
    # solo 0.5mm en Y -- desplazado al borde real del pad de ILIM (que
    # sigue llegando hasta 169.125) gana el margen que faltaba.
    ("Net-(U4-ILIM)", F, [(90.55, 169.05), (89, 169.05), (89, 174), (91.175, 174)], ANCHO_ISLA),
    ("Net-(U5-ILIM)", F, [(110.55, 169.05), (109, 169.05), (109, 174), (111.175, 174)], ANCHO_ISLA),
    # U6/U7: el hueco a la izquierda del chip es mas angosto (JP1 a un
    # lado, la fuga de Net-C25/26-Pad1 al otro) -- el ultimo tramo (169 a
    # 174) salta a B.Cu para no competir por ese milimetro. y=169.2 (no
    # 169.125): PGFB (pin5, NC) esta justo encima, el mismo desplazamiento
    # al borde del pad de ILIM (real hasta 169.25).
    ("Net-(U6-ILIM)", F, [(118.55, 169.2), (117.3, 169.2)], ANCHO_ISLA),
    ("Net-(U6-ILIM)", B, [(117.3, 169.2), (119.175, 173)], ANCHO_ISLA),
    ("Net-(U6-ILIM)", F, [(119.175, 173), (119.175, 174)], ANCHO_ISLA),
    ("Net-(U7-ILIM)", F, [(134.55, 169.2), (133, 169.2)], ANCHO_ISLA),
    ("Net-(U7-ILIM)", B, [(133, 169.2), (135.175, 173)], ANCHO_ISLA),
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
    # via desplazada al borde norte del propio pad (166.9, no 167): U4.9
    # (+12V) esta a solo 0.5mm (paso del DFN) y con la via centrada en el
    # pin (radio 0.3) el hueco real quedaba en 0.075mm (hacen falta 0.127).
    ("Net-(U4-OUT)", F, [(93.45, 167), (93.45, 166.94)], ANCHO_SET),
    ("Net-(U4-OUT)", B, [(93.45, 166.94), (88, 167), (88, 180), (90.525, 180)], ANCHO_ISLA),
    ("Net-(U4-OUT)", F, [(90.525, 180), (90.537, 186)], ANCHO_ISLA),
    # el tramo vertical en x=107 cruza Net-(U4-SET) en y=176 (dentro de su
    # rango 103..114.6) -- salto corto a F.Cu solo ahi.
    # el rectangulo de GND hacia el EP de U5 (92..112,168..171) ocupaba
    # justo x=107..113.45,y=169.5-171 -- baja recto hasta y=172 (ya debajo
    # del rectangulo, que termina en 171) ANTES de girar hacia el oeste.
    # via desplazada al borde norte del pad (166.9, no 167): mismo motivo
    # que U4-OUT (U5.9/+12V a 0.5mm).
    ("Net-(U5-OUT)", F, [(113.45, 167), (113.45, 166.9)], ANCHO_SET),
    ("Net-(U5-OUT)", B, [(113.45, 166.9), (113.45, 172)], ANCHO_ISLA),
    ("Net-(U5-OUT)", B, [(113.45, 172), (107, 172), (107, 175)], ANCHO_ISLA),
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
    # via desplazada al borde norte del pad (167.2, no 167.325): U6.10
    # (-12V) esta a 0.45mm (paso del DFN-12) y con la via centrada el
    # hueco real era de 0.325mm (hacen falta 0.427).
    # ANCHO_SET (no ISLA) en este tramo de 0.125mm: la salida de -12V
    # (U6.10, y=167.75) queda a solo 0.425mm -- con ISLA+ISLA no alcanzaba
    # (hacia falta 0.502), con SET+SET si (0.377).
    ("Net-(C25-Pad1)", F, [(121.45, 167.325), (121.45, 167.15)], ANCHO_SET),
    ("Net-(C25-Pad1)", B, [(121.45, 167.2), (121.45, 174.5), (119, 174.5), (119, 175)], ANCHO_ISLA),
    ("Net-(C25-Pad1)", F, [(119, 175), (119, 177)], ANCHO_ISLA),
    ("Net-(C25-Pad1)", B, [(119, 177), (119, 180), (118.525, 180)], ANCHO_ISLA),
    ("Net-(C25-Pad1)", F, [(118.525, 180), (118.537, 186)], ANCHO_ISLA),
    # C26.1 (134.525) queda a la IZQUIERDA de su vecino C26.2/GND (137.475,
    # misma fila) -- se aproxima por la izquierda (x=132), igual que las
    # otras tres, para no cruzar el pad de GND.
    # horizontal a y=174.5 (no 169.5, que cruzaba Net-(U7-ILIM)); el tramo
    # final en x=132 baja cruzando Net-(U6-SET) en y=176 -- salto a F.Cu.
    # via desplazada al borde norte del pad (167.2, no 167.325): mismo
    # motivo que Net-(C25-Pad1) (U7.10/-12V a 0.45mm).
    ("Net-(C26-Pad1)", F, [(137.45, 167.325), (137.45, 167.15)], ANCHO_SET),
    ("Net-(C26-Pad1)", B, [(137.45, 167.15), (137.45, 174.5), (132, 174.5), (132, 175)], ANCHO_ISLA),
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
    # y=168.0 (el centro real del pin GND, no 168.125): a 168.125 quedaba
    # a solo 0.25mm de SET (168.5), hacen falta 0.252.
    ("GND", F, [(93.45, 168.0), (92.825, 168.0)], ANCHO_SET),   # U4.8 -> borde del EP
    ("GND", F, [(113.45, 168.0), (112.825, 168.0)], ANCHO_SET),  # U5.8 -> borde del EP
    # U6.9/U7.9 -> sus vias de escape propias (124/139.8, 168.225 -- NO en
    # 122.5/138.5, que es donde arranca la via Kelvin de -12V, o se tocan).
    # centro del pad (168.225, no un borde): equidistante de Kelvin arriba
    # (167.65) y de Net-(U6/7-SET) abajo (168.8) -- el mejor reparto
    # posible en un paso de 0.45 mm. Ancho fino, mismo motivo de siempre.
    # x=125.5/141.0 para la via (no 124/139.8): Net-(U6-SET) usa esa misma
    # x=124/139.7 para su propio vertical hacia 174 -- la via (radio 0.6)
    # quedaba a solo 0.1-0.3mm. Al este de su rango real (121.45..124 /
    # 137.45..139.7) no hay conflicto.
    ("GND", F, [(121.45, 168.225), (125.5, 168.225)], ANCHO_SET),
    ("GND", F, [(137.45, 168.225), (141.0, 168.225)], ANCHO_SET),

    # ===================== GND: el arbol, TODO en B (sec.7, incl. isla) =====
    # Tronco heredado de v1 hasta la estrella (C1.2) y sus ramas de v1
    # (columnas A/B/C con las U/C/D/R que sobreviven en v2 y sus posiciones
    # de v1), reescrito con las coordenadas reales de v2 (muralla en
    # y=143, no y=154).
    ("GND", B, [(15, 42), (15, 36), (6, 36), (6, 66), (14, 66), (14, 62), (17.5, 62)], ANCHO_POT),
    # muesca en x=29..35,y=72.3: TP7 (/+13V1, en 32,74, pad 2mm) esta
    # justo en el borde recto (17.5..35.5,74).
    ("GND", B, [(17.5, 62), (17.5, 74), (29, 74), (29, 72.3), (35, 72.3), (35, 74), (35.5, 74), (35.5, 62)], ANCHO_POT),   # C12.2
    ("GND", B, [(35.5, 74), (48, 74), (48, 62)], ANCHO_POT),   # C2.1
    ("GND", B, [(48, 74), (68, 74), (68, 77)], ANCHO_POT),     # TP6
    ("GND", B, [(48, 74), (66, 74), (66, 62)], ANCHO_POT),     # C13.1
    # --- rama columna U1 (+13V1 pre-reg): C17.2 ---
    # entra por arriba (y=80, no recto a 82): la linea recta hacia C17.2
    # (30.5,82) pasaba primero por encima de C17.1 (/+13V1, en 28,82).
    ("GND", B, [(17.5, 74), (20, 74), (20, 80), (30.5, 80), (30.5, 82)], ANCHO_POT),   # C17.2
    ("GND", B, [(20, 80), (20, 82)], ANCHO_POT),  # cierre: U1.2/Q1.3/J5 arrancan en (20,82), sin tocar lo de arriba
    ("GND", B, [(20, 82), (20, 137), (29.7, 137), (29.7, 143)], ANCHO_POT),  # U1.2
    ("GND", B, [(29.7, 137), (31.4, 137), (31.4, 143)], ANCHO_POT),         # U1.3
    # --- rama columna U3 (+5V, igual v1) ---
    # x=59.6 (no 57): el vertical largo (84..137) pasaba a solo 0.1mm del
    # borde de D4.1 (-12V, en 58,111, caja 57.1..58.9).
    ("GND", B, [(48, 74), (48, 84), (59.6, 84), (59.6, 137)], ANCHO_POT),
    ("GND", B, [(59.6, 84), (64, 84), (64, 82)], ANCHO_POT),    # C9.2
    ("GND", B, [(64, 84), (77.5, 84), (77.5, 82)], ANCHO_POT),  # C10.2
    ("GND", B, [(77.5, 84), (94, 84), (94, 82)], ANCHO_POT),   # C11.2
    ("GND", B, [(59.6, 84), (89, 84), (89, 105)], ANCHO_POT),    # D6.1
    ("GND", B, [(59.6, 137), (77.54, 137), (77.54, 143)], ANCHO_POT),  # U3.2
    # --- rama columna U2 (-12V9 pre-reg): C28.1 ---
    ("GND", B, [(66, 74), (106, 74), (106, 82)], ANCHO_POT),   # C28.1
    # bifurcacion a y=95 (no 137): a 137 el tunel B.Cu de /VRAW- (que salta
    # el hub de Net-(U2-ADJ) en 137.5) cruzaba esta horizontal de lleno.
    # rodeo por x=126 en y=90..98: el pad de D13.2 (/VRAW-, radio real
    # 1.1 mm) esta en (122.16,94), a solo 1.54 mm del tramo recto en 123.7.
    # x=122.8 (no 123.7) para el primer tramo: C18.2 (/-12V9, en 124.5,82)
    # tenia el borde justo ahi. A esa altura (y=74..90) D13.2 (94) todavia
    # no importa -- el rodeo real contra D13.2 sigue siendo el de x=126.
    ("GND", B, [(106, 74), (122.8, 74), (122.8, 90), (126, 90), (126, 98), (123.7, 98), (123.7, 143)], ANCHO_POT),  # U2.2
    # arranca en (126,96), no (124.3,96): asi cae exacto sobre el propio
    # vertical de la linea de arriba (126,90..98), que ya pasa por ahi --
    # el punto viejo (124.3,96) no tocaba nada, "dangling" en DRC real
    # (ronda 2, limpieza). x=126 sigue lejos de D13.2 (122.16,94, radio
    # real 1.1mm) de sobra.
    ("GND", B, [(126, 96), (127.1, 96), (127.1, 143)], ANCHO_POT),           # U2.4
    # --- rama del crowbar/indicador +12V (banda libre, y=111/119) ---
    ("GND", B, [(20, 82), (20, 105), (15.08, 105), (15.08, 111)], ANCHO_POT),  # Q1.3
    ("GND", B, [(20, 105), (42, 105), (42, 111)], ANCHO_POT),                 # D3.1
    ("GND", B, [(42, 105), (42, 108), (20.16, 108), (20.16, 119)], ANCHO_POT),  # R4.2
    # C14.2 (GND, en 31,119) no tenia pista propia. Rodeo por y=121 (no
    # recto a 119) para no rozar C14.1 (Net-(D7-A), en 26,119 -- mismo
    # punto donde termina la pista de esa red, linea de arriba).
    ("GND", B, [(20.16, 119), (20.16, 121), (31, 121), (31, 119)], ANCHO_POT),  # C14.2
    # --- rama del crowbar/indicador -12V ---
    # muesca en x=68..88,y=108 (no recta a 105): cubre DOS cruces --
    # el tramo B.Cu de -12V que esquiva TP3.1 (x=70..78, arranca en
    # (70,104.5), a solo 0.5mm de esta horizontal) y el salto de
    # Net-(D6-A) en x=86.46 (que no tenia hueco ni en F.Cu, bloqueado por
    # el propio -12V a y=103, ni en B.Cu, bloqueado por esta linea).
    # rodeo final x=60 en y=108..116: el ultimo tramo recto (58,108..119)
    # pasaba directo por encima del cuerpo de D4.1 (-12V, en 58,111).
    ("GND", B, [(106, 82), (106, 105), (88, 105), (88, 108), (68, 108), (68, 105), (58, 105), (58, 108), (60, 108), (60, 116), (58, 116), (58, 119)], ANCHO_POT),  # R2.1
    # --- rama de salidas: bus y faston de chasis (igual criterio v1) ---
    # x=14.5 (no 12): justo la posicion de C27.1 (/VRAW+, en 12,82) --
    # 14.5 cae en el hueco limpio entre sus dos pads (12 y 17).
    ("GND", B, [(20, 82), (14.5, 82), (14.5, 186), (19.5, 186), (19.5, 190)], ANCHO_POT),  # J5
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
    ("GND", B, [(62.54, 186), (92, 186), (92, 180)], ANCHO_POT),   # -> EP U4 (via farm)
    # tramo local mas fino (176..180, no todo ANCHO_POT): la via de -12V
    # que cruza a F.Cu junto a +12V (93.463) esta a solo 1.463mm de esta
    # columna -- con los DOS anchos completos (POT+ISLA+radio de via) la
    # ventana valida es negativa, sin solucion. Con GND mas fino aqui
    # (ANCHO_ISLA, corriente de retorno de un EP, no de potencia real) si
    # cabe.
    ("GND", B, [(92, 180), (92, 176)], ANCHO_ISLA),
    ("GND", B, [(92, 176), (92, 168.7)], ANCHO_POT),
    # D8.2, D9.1 y JP1.2 son SMD de solo F.Cu (D_SMA, NetTie) -- el tronco
    # en B.Cu llega hasta al lado del pad y una via propia (no la granja
    # del EP, que es de otro chip) cruza el ultimo tramo en F.Cu.
    # y=171 (no 168 ni 169.5): 168 esta a 0.5 mm de la via Kelvin en x=95.5;
    # 169.5 se pisa con la fuga de Net-(U5-OUT), que ya usa esa altura.
    ("GND", B, [(92, 168), (92, 171), (112, 171), (112, 168)], ANCHO_POT),  # -> EP U5 (via farm)
    ("GND", B, [(105, 171), (105, 168)], ANCHO_ISLA),
    ("GND", F, [(105, 168), (104, 168)], ANCHO_ISLA),  # via D8.2
    ("GND", B, [(92, 186), (92, 195), (122.5, 195), (125.5, 195), (125.5, 168.225)], ANCHO_POT),  # -> escape U6.9
    # y=168.4 (no 168) en el ultimo tramo: la fuga F.Cu de -12V hacia
    # U6.10/U7.10 pasa por y=167.75 justo por ahi -- 168 quedaba a solo
    # 0.25mm (hacen falta 0.502).
    # y=167.6 (no 168.4): hole-to-hole real contra la via de escape U6.9
    # (1.2/0.6mm, en 125.5,168.225) -- a 168.4 quedaban a 0.55mm (hacen
    # falta 0.7 = mitad de la suma de taladros + 0.25mm). 167.6 sigue
    # dentro de la caja real de D9.1 (167.55..168.45) (ronda 2, Important 2).
    ("GND", B, [(122.5, 195), (125, 195), (125, 167.6)], ANCHO_POT),  # -> via D9.1 (esquiva R10.1; misma red que la via de escape U6.9 en 125.5, sin conflicto)
    ("GND", F, [(125, 167.6), (126, 167.6)], ANCHO_ISLA),
    # rodeo por x=140.75 en y=174..179: ahi cruza Net-(U6-SET) camino de
    # U7.8 (y=176, hasta x=140.2) -- fuera de su rango y del courtyard de
    # RV3 (que empieza en 141.29). Ajustado a 141.0 (via movida, ver
    # comentario junto a los escapes GND de U6.9/U7.9). x=140.5 (no 141.0)
    # SOLO en el tramo y=179..195: ahi vive H4 (taladro de fijacion, en
    # 143,193, radio 1.6mm) y 141.0 quedaba a solo 0.4mm de su borde.
    ("GND", B, [(122.5, 195), (140.5, 195), (140.5, 179), (141.6, 179),
                (141.6, 174), (141.0, 174), (141.0, 168.225)], ANCHO_POT),  # -> escape U7.9
    ("GND", B, [(122.5, 195), (116.5, 195), (116.5, 175)], ANCHO_POT),  # -> via JP1.2
    ("GND", F, [(116.5, 175), (116.5, 174)], ANCHO_ISLA),

    # --- retorno GND de R11/R12/R13/R14 (ILIM) y C19-C26 (in/out caps):
    # el pad 2 de cada uno (GND) se quedaba sin ninguna pista propia --
    # la zona GNDREF no los cubre (son GND de potencia, no GNDREF) y no
    # habia stub explicito. Cada uno se conecta al tronco B.Cu mas cercano
    # ya existente arriba, con una via propia (o directo en F.Cu cuando el
    # punto de destino ya es F.Cu, como en R13.2).
    # via a (92, 173.2), no (92, 174): a y=174 la via quedaba a solo
    # 0.125mm del pad R11.1[Net-(U4-ILIM)] (necesita 0.127) -- subiendo
    # 0.8mm en Y (el tronco B.Cu en x=92 sigue continuo, 168.7..176) la
    # distancia pasa a ser diagonal a la esquina del pad, con margen.
    ("GND", F, [(92.825, 174), (92, 173.2)], ANCHO_ISLA),   # R11.2 -> tronco EP-U4 (92, 168.7..176)
    # R12.2: todo en F.Cu hasta y=171 (no via a 174 y bajada en B.Cu) --
    # en B.Cu esa bajada cruzaba Net-(U5-OUT) en (112,172); en F.Cu esa
    # zona esta libre, y y=171 ya cae justo sobre el tronco B.Cu de la
    # via farm EP-U5 (92..112,171), asi que la via de transicion va ahi.
    ("GND", F, [(112.825, 174), (112, 174), (112, 171)], ANCHO_ISLA),  # R12.2 -> tronco EP-U5
    # R13.2: al OESTE (hacia JP1.2) el hueco entre x=117..121 y y=173..177
    # esta minado -- ILIM, /-12V9 y Net-(C25-Pad1) tienen tramos F y B
    # entrelazados justo ahi (probado: cualquier Y entre 173 y 177 choca
    # con alguno). Mas facil al ESTE: baja en F.Cu junto al propio pad
    # hasta y=176 (fuera del alcance de Net-(U6-SET) en y=174 y de D11 en
    # y=179.1) y entra directo al tronco de escape U6.9 (x=125.5, B.Cu
    # continuo 168.225..195) en vez de cruzar hacia JP1.2.
    ("GND", F, [(120.825, 174), (120.825, 176), (125.5, 176)], ANCHO_ISLA),  # R13.2 -> escape U6.9
    # R14.2: idem del otro lado -- F.Cu junto al pad hasta x=138.2 (fuera
    # del rango de Net-(C26-Pad1) en B.Cu, que termina en x=137.45), salto
    # a B.Cu, sube a y=175.3 (libra a la vez Net-(C26-Pad1) en y=174.5 y
    # Net-(U6-SET) en y=176) y entra al propio tronco de escape U7.9 en
    # (141.6,174).
    ("GND", F, [(136.825, 174), (138.2, 174)], ANCHO_ISLA),
    ("GND", B, [(138.2, 174), (138.2, 175.3), (141.6, 175.3), (141.6, 174)], ANCHO_ISLA),  # R14.2 -> escape U7.9
    ("GND", F, [(93.475, 192), (92, 192)], ANCHO_ISLA),   # C19.2 -> tronco EP-U4 (92, 186..195)
    ("GND", F, [(113.475, 192), (116.5, 192)], ANCHO_ISLA),  # C20.2 -> via JP1.2 (116.5, 175..195)
    ("GND", F, [(121.475, 192), (125.5, 192)], ANCHO_ISLA),  # C21.2 -> escape U6.9 (125.5, 168.225..195)
    # x=140.5 (no 141.0): el tronco de escape U7.9 en esta franja de Y
    # (179..195) esta en x=140.5, no en 141.0 (ese solo aparece mas abajo,
    # y=174..168.225, tras el codo en 141.6) -- 141.0 aqui no tocaba nada.
    # Ademas 141.0 quedaba a 0.10mm del taladro de fijacion H4 (143,193,
    # radio 1.6); 140.5 lo libra por 0.9mm.
    ("GND", F, [(137.475, 192), (140.5, 192)], ANCHO_ISLA),  # C22.2 -> escape U7.9
    ("GND", F, [(93.475, 180), (92, 180)], ANCHO_ISLA),   # C23.2 -> tronco EP-U4
    ("GND", F, [(113.475, 180), (116.5, 180)], ANCHO_ISLA),  # C24.2 -> via JP1.2
    # C25.2: primero al ESTE por y=180 (la propia altura del pad) hasta
    # x=123.0 -- ahi ya esta fuera del rango de D11 (pad1 -12V en
    # x=124.75..127.25) Y lejos del corredor vertical de -12V que baja
    # casi por el mismo x que este pad (121.463, entre y=178 y 186 en
    # varios tramos F/B). Bajar en Y directamente en x=121.475 (primer
    # intento) corria ese corredor en paralelo, a 0.012mm; subir hasta
    # y=181.5 (segundo intento) quedaba a 0.5mm de la propia pista -12V
    # que alimenta a D11.1 (x=126, y=180..183). Subiendo a y=178.5 en vez
    # de bajar se libra todo: por encima del pad D11 (borde en 179.1),
    # por encima de la pista -12V de D11 (que no sube de 180) y del bus
    # -12V que corre por y=178 pero solo hasta x=121.463 (aqui x>=123).
    ("GND", F, [(121.475, 180), (123.0, 180)], ANCHO_ISLA),
    ("GND", F, [(123.0, 180), (123.0, 178.5)], ANCHO_ISLA),
    ("GND", F, [(123.0, 178.5), (125.5, 178.5)], ANCHO_ISLA),  # C25.2 -> escape U6.9
    ("GND", F, [(137.475, 180), (140.5, 180)], ANCHO_ISLA),  # C26.2 -> escape U7.9 (x=140.5, ver nota en C22.2)

    # --- ronda 2, Important 2: granjas termicas EP de U4/U5 rediseñadas.
    # El paso original (0.375/0.5mm, taladro 0.3mm) daba web hole-to-hole
    # de 0.075/0.2mm, por debajo del minimo del proyecto (0.25mm). Los
    # nuevos pasos (>=0.55mm) ya no dejan que las vias se toquen entre si
    # (antes se conectaban por simple solape de cobre) -- cada via necesita
    # su propio spoke de B.Cu hasta el tronco real (el vertice donde el
    # tronco GND toca cada EP), o quedan "dangling" (conectadas solo en
    # F.Cu, al pad). Spokes cortos, mismo net, sin problema de clearance.
    ("GND", B, [(92, 168), (91.7, 167.85)], ANCHO_SET),
    ("GND", B, [(92, 168), (92.3, 167.85)], ANCHO_SET),
    ("GND", B, [(92, 168), (91.7, 168.5)], ANCHO_SET),
    ("GND", B, [(92, 168), (92.3, 168.5)], ANCHO_SET),
    ("GND", B, [(112, 168), (111.7, 167.3)], ANCHO_SET),
    ("GND", B, [(112, 168), (112.3, 167.3)], ANCHO_SET),
    ("GND", B, [(112, 168), (111.7, 168.0)], ANCHO_SET),
    ("GND", B, [(112, 168), (112.3, 168.0)], ANCHO_SET),
    ("GND", B, [(112, 168), (111.7, 168.7)], ANCHO_SET),
    ("GND", B, [(112, 168), (112.3, 168.7)], ANCHO_SET),

    # --- ronda 3, F3: spokes B.Cu de las granjas EP de U6/U7 (/-12V9) ---
    # U6: el ancla es la via de transicion F/B ya existente del propio
    # tronco /-12V9 en (120,169) -- no hace falta una nueva.
    ("/-12V9", B, [(120, 169), (119.7, 167.4)], ANCHO_SET),
    ("/-12V9", B, [(120, 169), (120.3, 167.4)], ANCHO_SET),
    ("/-12V9", B, [(120, 169), (119.7, 168.0)], ANCHO_SET),
    ("/-12V9", B, [(120, 169), (120.3, 168.0)], ANCHO_SET),
    # U7: no habia NADA de cobre /-12V9 bajo el chip (F3: "U7 CERO"). Se
    # alarga el stub F.Cu de pin3->EP (que ya llega al pad, linea de
    # "U7 pin3 -> EP") 0.5mm mas, hasta aterrizar EXACTO en una de las
    # vias de la granja -- esa via hace de ancla F/B, igual que el
    # (120,169) de U6, sin necesitar una via extra.
    ("/-12V9", F, [(135.3, 167.775), (135.7, 167.4)], ANCHO_SET),
    ("/-12V9", B, [(135.7, 167.4), (136.3, 167.4)], ANCHO_SET),
    ("/-12V9", B, [(135.7, 167.4), (135.7, 168.0)], ANCHO_SET),
    ("/-12V9", B, [(135.7, 167.4), (136.3, 168.0)], ANCHO_SET),
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
    # --- granja termica EP de U4 (2x2, centrada en 92,168, dentro de la
    # huella EP 1.65x2.38 mm) --- ronda 2, Important 2: rediseñada, paso
    # 0.6mm (>=0.55 minimo real) en vez de 0.375/0.5 -- el 3x3 original no
    # cabe con hole-to-hole legal en una huella de 1.65mm de ancho (el
    # rango util de centros, descontando el radio de via, es de solo
    # ~1.05mm -- 3 columnas exigirian 0.525mm de paso, por debajo del
    # minimo). Fila en y=167.85 (no 167.3): la fuga de Net-(U4-OUT) en
    # y=167 sigue exigiendo ese margen (comentario original).
    (91.7, 167.85, "GND", 0.6, 0.3), (92.3, 167.85, "GND", 0.6, 0.3),
    (91.7, 168.5, "GND", 0.6, 0.3), (92.3, 168.5, "GND", 0.6, 0.3),
    # --- granja termica EP de U5 (2x3, centrada en 112,168) --- paso X a
    # 0.6mm (2 columnas, mismo motivo que U4); paso Y se queda en 0.7mm
    # (ya era legal) con 3 filas, que si caben en la altura de 2.38mm.
    (111.7, 167.3, "GND", 0.6, 0.3), (112.3, 167.3, "GND", 0.6, 0.3),
    (111.7, 168.0, "GND", 0.6, 0.3), (112.3, 168.0, "GND", 0.6, 0.3),
    (111.7, 168.7, "GND", 0.6, 0.3), (112.3, 168.7, "GND", 0.6, 0.3),
    # --- ronda 3, F3: granjas termicas EP de U6/U7 (net /-12V9), reales
    # esta vez. U6 tenia 1 sola via (la propia transicion F/B del tronco,
    # no una granja) y U7 CERO -- el EP es el camino termico de ~0.33W
    # por chip. Mismo patron que U4/U5: 2x2, paso 0.6mm (huella EP
    # identica, 1.65x2.38mm), drill 0.3mm. Filas en 167.4/168.0 (dentro
    # de la caja real del EP, 166.81..169.19, con margen de sobra a los
    # pines vecinos por X, no por Y).
    (119.7, 167.4, "/-12V9", 0.6, 0.3), (120.3, 167.4, "/-12V9", 0.6, 0.3),
    (119.7, 168.0, "/-12V9", 0.6, 0.3), (120.3, 168.0, "/-12V9", 0.6, 0.3),
    (135.7, 167.4, "/-12V9", 0.6, 0.3), (136.3, 167.4, "/-12V9", 0.6, 0.3),
    (135.7, 168.0, "/-12V9", 0.6, 0.3), (136.3, 168.0, "/-12V9", 0.6, 0.3),
    # --- escapes GND de U6.9 / U7.9 (sin EP en GND que los lleve gratis) ---
    (125.5, 168.225, "GND", 1.2, 0.6),
    (141.0, 168.225, "GND", 1.2, 0.6),
    # --- escapes GND de D8.2 / D9.1 / JP1.2 (SMD de solo F.Cu) ---
    (105.0, 168.0, "GND", 0.6, 0.3),
    (125.0, 167.6, "GND", 0.6, 0.3),  # D9.1, ver TRACKS
    (116.5, 175.0, "GND", 0.6, 0.3),
    # --- transiciones F->B para los retornos GND de R11/R12/R13/R14/C19-C26 ---
    (92.0, 173.2, "GND", 0.6, 0.3),  # R11.2 (ver TRACKS)
    (112.0, 171.0, "GND", 0.6, 0.3),  # R12.2, ya en el tronco EP-U5 (no 112,174: ver TRACKS)
    (125.5, 176.0, "GND", 0.6, 0.3),  # R13.2, salto a B.Cu (ver TRACKS)
    (138.2, 174.0, "GND", 0.6, 0.3),  # R14.2, salto a B.Cu (ver TRACKS)
    (92.0, 192.0, "GND", 0.6, 0.3),
    (116.5, 192.0, "GND", 0.6, 0.3),
    (125.5, 192.0, "GND", 0.6, 0.3),
    (140.5, 192.0, "GND", 0.6, 0.3),
    (92.0, 180.0, "GND", 0.6, 0.3),
    (116.5, 180.0, "GND", 0.6, 0.3),
    (125.5, 178.5, "GND", 0.6, 0.3),  # C25.2, rodeo bajo D11 (ver TRACKS)
    (140.5, 180.0, "GND", 0.6, 0.3),
    # --- escape Kelvin de OUTS: U4.9/U5.9 (+12V) y U6.10/U7.10 (-12V) a B ---
    (95.5, 167.5, "+12V", 1.2, 0.6),
    (115.5, 167.5, "+12V", 1.2, 0.6),
    (127.3, 166.55, "-12V", 0.6, 0.3),
    (138.7, 166.55, "-12V", 0.6, 0.3),
    # --- tuneles de +12V/-12V bajo el corredor de +13V1 (y=165, F.Cu) ---
    (45.0, 177.0, "+12V", 1.0, 0.5),
    (45.0, 102.0, "+12V", 1.0, 0.5),
    (48.0, 178.2, "-12V", 1.0, 0.5),
    (50.0, 109.3, "-12V", 0.6, 0.3),  # D4.1, transicion F/B (ver TRACKS)
    (50.0, 104.5, "-12V", 0.6, 0.3),  # D4.1, transicion B/F sobre el tronco (mid-span, sin partirlo)
    (48.0, 104.5, "-12V", 1.0, 0.5),
    (70.0, 104.5, "-12V", 1.0, 0.5),
    (78.0, 100.0, "-12V", 1.0, 0.5),
    # y=103.9 (no 104.5): hole-to-hole real contra D6.2 (drill 0.9mm, en
    # 86.46,105) -- a 104.5 quedaban a 0.5mm (hacen falta 0.85 = mitad de
    # la suma de taladros + 0.25mm minimo del proyecto). El rodeo F.Cu de
    # -12V (linea "esquiva D6.1/TP4", abajo) tambien se adelgaza a
    # ANCHO_ISLA justo en ese cruce para dejar sitio (era ANCHO_KELVIN).
    (86.46, 103.9, "Net-(D6-A)", 0.6, 0.3),
    (86.46, 100.0, "Net-(D6-A)", 0.6, 0.3),
    # --- J2.4/J2.1 (potencia): via propia junto a cada puente ---
    (67.62, 177.0, "+12V", 1.0, 0.5),
    (60.0, 178.2, "-12V", 1.0, 0.5),  # tap J2.1 (potencia), ver TRACKS
    # --- tunel de /+13V1 (TP7->U1.5) bajo el highway de +12V (y=102) ---
    (34.8, 96.0, "/+13V1", 1.0, 0.5),
    (100.0, 172.5, "/+13V1", 0.6, 0.3),  # D10.1, ver TRACKS
    (100.0, 179.5, "/+13V1", 0.6, 0.3),  # D10.1, ver TRACKS
    (34.8, 116.0, "/+13V1", 1.0, 0.5),
    (35.0, 174.0, "/+13V1", 1.0, 0.5),
    (35.0, 178.0, "/+13V1", 1.0, 0.5),
    (128.8, 100.0, "/-12V9", 1.0, 0.5),
    (128.8, 104.0, "/-12V9", 1.0, 0.5),
    (128.8, 136.0, "/-12V9", 1.0, 0.5),
    (128.8, 139.0, "/-12V9", 1.0, 0.5),
    # (70,90) faltaba: la transicion F->B ahi no tenia via (bug real,
    # separado del reruteo del corredor U3 -- se corrige de paso).
    (70.0, 90.0, "/VRAW+", 1.0, 0.5),
    (87.0, 98.0, "/VRAW+", 1.0, 0.5),
    (91.0, 98.0, "/VRAW+", 1.0, 0.5),
    (102.0, 103.0, "/VRAW+", 1.0, 0.5),
    (102.0, 108.0, "/VRAW+", 1.0, 0.5),
    (74.0, 135.0, "/VRAW+", 1.0, 0.5),
    (74.0, 139.0, "/VRAW+", 1.0, 0.5),
    (107.0, 175.0, "Net-(U5-OUT)", 0.6, 0.3),
    (107.0, 177.0, "Net-(U5-OUT)", 0.6, 0.3),
    (119.0, 175.0, "Net-(C25-Pad1)", 0.6, 0.3),
    (119.0, 177.0, "Net-(C25-Pad1)", 0.6, 0.3),
    (132.0, 175.0, "Net-(C26-Pad1)", 0.6, 0.3),
    (93.463, 181.5, "+12V", 0.6, 0.3),
    (93.463, 178.6, "+12V", 0.6, 0.3),
    (121.463, 181.5, "-12V", 0.6, 0.3),
    (121.463, 178.6, "-12V", 0.6, 0.3),
    (94.5, 178.0, "-12V", 0.6, 0.3),
    (92.73, 178.2, "-12V", 0.6, 0.3),
    (132.0, 177.0, "Net-(C26-Pad1)", 0.6, 0.3),
    # --- saltos sobre los puentes de ballast (y=183) ---
    (100.922, 177.2, "Net-(U4-SET)", 0.6, 0.3),
    # (100.7,181.5) borrada: via redundante a mitad de un tramo B.Cu
    # continuo (177.2..184.5, sin cambio de capa ahi) -- "conectada solo
    # en una capa" en DRC real (ronda 2, limpieza).
    (100.6, 184.5, "Net-(U4-SET)", 0.6, 0.3),
    (110.53, 181.5, "Net-(U5-OUT)", 0.6, 0.3),
    (110.53, 184.5, "Net-(U5-OUT)", 0.6, 0.3),
    (127.088, 174.0, "Net-(U6-SET)", 0.6, 0.3),
    (126.6, 184.5, "Net-(U6-SET)", 0.6, 0.3),
    (134.53, 181.5, "Net-(C26-Pad1)", 0.6, 0.3),
    (134.53, 184.5, "Net-(C26-Pad1)", 0.6, 0.3),
    (125.4, 136.0, "/VRAW-", 1.0, 0.5),
    (125.4, 139.0, "/VRAW-", 1.0, 0.5),
    (51.92, 176.0, "Net-(U1-ADJ)", 0.6, 0.3),
    (66.2, 176.0, "Net-(U1-ADJ)", 0.6, 0.3),
    # (77,176) borrada: los dos tramos que se tocaban ahi ya son B.Cu (sin
    # cambio de capa) -- via redundante, quedaba a 0.05mm del hub de +12V
    # sin servir para nada (ronda 2, limpieza).
    # --- C19/C20/C21/C22: tramos largos por B.Cu, tuneles cortos en cada punta ---
    (89.5, 168.1, "/+13V1", 1.0, 0.5),
    (89.3, 179.1, "/+13V1", 1.0, 0.5),
    (89.3, 181.0, "/+13V1", 1.0, 0.5),
    (90.0, 190.0, "/+13V1", 1.0, 0.5),
    (89.2, 184.0, "/+13V1", 1.0, 0.5),
    (89.2, 188.0, "/+13V1", 1.0, 0.5),
    (120.0, 169.0, "/-12V9", 1.0, 0.5),
    # radio minimo (0.6mm, no 1.0mm): entre R13, Net-(C25-Pad1) y la via de
    # Net-(U6-ILIM), esta esquina no tiene sitio para una via mas grande.
    (120.0, 172.8, "/-12V9", 0.6, 0.3),
    (120.0, 175.5, "/-12V9", 0.6, 0.3),
    (120.0, 190.0, "/-12V9", 1.0, 0.5),
    # --- tunel de +5V bajo el corredor de +13V1 (y=165) ---
    (40.0, 163.0, "+5V", 1.0, 0.5),
    (40.0, 167.0, "+5V", 1.0, 0.5),
    # --- escape de -12V9 hacia R7.2, por encima de toda la isla (y=150) ---
    # (55,170)/(53,172)/(53,184)/(53,188) NO estaban: eran vias huerfanas,
    # de un trazado anterior, sin ninguna pista que las tocara (DRC real
    # las marcaba "unconnected"). El camino real es el de la linea 537
    # (55,163)->(55,180)->(58.5,180)->(58.5,184) en B.Cu, que solo
    # necesita las dos vias de transicion F/B de abajo.
    (55.0, 163.0, "/-12V9", 1.0, 0.5),
    (58.5, 184.0, "/-12V9", 1.0, 0.5),  # B->F, ver TRACKS linea 537/538
    (58.5, 188.0, "/-12V9", 1.0, 0.5),  # F->B, ver TRACKS linea 538/539
    # --- escape de Net-(R7-Pad1) junto a RV3, hacia R7.1 por B.Cu ---
    (146.8, 178.8, "Net-(R7-Pad1)", 1.0, 0.5),
    # --- Net-(R7-Pad1): vuelve a F.Cu para el ultimo tramo (evita el
    # tronco -12V9 que corre por B.Cu en y=196) ---
    (77.0, 197.0, "Net-(R7-Pad1)", 1.0, 0.5),
    # --- OUT/C25/C26-Pad1: directo a B.Cu en el pin y de vuelta en el destino ---
    (93.45, 166.94, "Net-(U4-OUT)", 0.6, 0.3),
    (90.525, 180.0, "Net-(U4-OUT)", 0.6, 0.3),
    (113.45, 166.9, "Net-(U5-OUT)", 0.6, 0.3),
    (110.525, 180.0, "Net-(U5-OUT)", 0.6, 0.3),
    (121.45, 167.15, "Net-(C25-Pad1)", 0.6, 0.3),
    (118.525, 180.0, "Net-(C25-Pad1)", 0.6, 0.3),
    (137.45, 167.15, "Net-(C26-Pad1)", 0.6, 0.3),
    (134.525, 180.0, "Net-(C26-Pad1)", 0.6, 0.3),
    # --- U6/U7 ILIM: salto corto a B.Cu junto a JP1 ---
    (117.3, 169.2, "Net-(U6-ILIM)", 0.6, 0.3),
    (119.175, 173.0, "Net-(U6-ILIM)", 0.6, 0.3),
    (133.0, 169.2, "Net-(U7-ILIM)", 0.6, 0.3),
    (135.175, 173.0, "Net-(U7-ILIM)", 0.6, 0.3),
    # --- escapes SET (U4-SET a U5.7, U6-SET a U7.8), tunel bajo R12/JP1/R14 ---
    (104.0, 176.0, "Net-(U4-SET)", 0.6, 0.3),
    (114.6, 176.0, "Net-(U4-SET)", 0.6, 0.3),
    (127.088, 176.0, "Net-(U6-SET)", 0.6, 0.3),
    (139.7, 176.0, "Net-(U6-SET)", 0.6, 0.3),
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


def dist_seg_rect(a, b, cx, cy, hw, hh) -> float:
    """Distancia minima entre el segmento ab y un rectangulo AABB
    centrado en (cx,cy) de semi-ancho hw y semi-alto hh. 0 si se tocan.

    Reemplaza la aproximacion circular (radio = dimension mayor/2) que
    revisar_pista_pad() usaba antes: para un pad DFN tipico (p.ej.
    0.85x0.25mm, panza larga y perfil fino) esa aproximacion infla el
    "bulto" del pad en la direccion CORTA hasta la LARGA -- sobre 0.425mm
    de radio en vez de 0.125mm real de semi-alto. Contra un pad asi, un
    tramo que pasa limpio en la realidad (y que kicad-cli, que si conoce
    la forma real, no marca) salia marcado igual por este script. Mismo
    espiritu que el recalibrado de reglas() (Tarea 8 ronda 1): la
    aproximacion heredada ahogaba el escape de los DFN sin motivo real.
    """
    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def dist_punto_rect(p):
        qx = clamp(p[0], cx - hw, cx + hw)
        qy = clamp(p[1], cy - hh, cy + hh)
        return ((p[0] - qx) ** 2 + (p[1] - qy) ** 2) ** 0.5

    # Muestreo denso a lo largo del segmento (incluye los dos extremos) --
    # suficiente para segmentos cortos como los de TRACKS; 0 en cuanto
    # algun punto cae dentro del rectangulo.
    n = 20
    mejor = float("inf")
    for i in range(n + 1):
        t = i / n
        p = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        if cx - hw <= p[0] <= cx + hw and cy - hh <= p[1] <= cy + hh:
            return 0.0
        mejor = min(mejor, dist_punto_rect(p))
    return mejor


def revisar_pista_pad(board) -> list[str]:
    """Pistas que pasan por encima del pad de OTRA red (heredado v1).

    Con TRACKS vacio no hay nada que revisar todavia: [] trivial, correcto.
    """
    capas = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()  # ya en coordenadas de placa, rotado
            cx = (bb.GetLeft() + bb.GetRight()) / 2e6
            cy = (bb.GetTop() + bb.GetBottom()) / 2e6
            hw = bb.GetWidth() / 2e6
            hh = bb.GetHeight() / 2e6
            pads.append((f"{fp.GetReference()}.{pad.GetNumber()}",
                         pad.GetNetname(), cx, cy, hw, hh,
                         pad.GetLayerSet().Contains(capas["F.Cu"]),
                         pad.GetLayerSet().Contains(capas["B.Cu"])))
    malos = []
    for net, capa, pts, ancho in TRACKS:
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            for nom, pnet, px, py, hw, hh, enF, enB in pads:
                if pnet == net:
                    continue
                if not (enF if capa == "F.Cu" else enB):
                    continue
                d = dist_seg_rect(a, b, px, py, hw, hh) - ancho / 2
                minimo = 2.5 if (es_red(net) or es_red(pnet)) else CLEARANCE_MM
                if d < minimo:
                    malos.append(f"{net} en {capa} a {d:.2f}mm del pad "
                                 f"{nom}[{pnet}] ({a}-{b})")
    return malos


def revisar_vias(board) -> list[str]:
    """Vias contra pads, pistas y otras vias de OTRA red.

    Ausente en v1 (que no tenia vias -- una sola cara de cobre real hasta
    esta placa) y por eso ausente aqui hasta ahora: revisar_pistas() solo
    mira TRACKS y revisar_pista_pad() solo mira pads, ninguna de las dos
    revisa las VIAS del propio script. El DRC real de kicad-cli si las
    revisa -- de ahi que "pistas encima de un pad ajeno" e "cruces" dieran
    0 mientras el DRC seguia encontrando `shorting_items` centrados en
    vias (transiciones F<->B junto a un pad o pista de otra red). Una via
    pasante toca AMBAS caras siempre, asi que aqui no se filtra por capa.
    """
    malos = []
    pads = []
    capasFB = pcbnew.F_Cu, pcbnew.B_Cu
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            # igual criterio que main(): sub-pads de SOLO pasta (EP de
            # DFN partido en varios trozos para no imprimir un bloque de
            # estano) no tienen cobre ni red -- no son un conflicto real.
            if not (pad.GetLayerSet().Contains(capasFB[0])
                    or pad.GetLayerSet().Contains(capasFB[1])):
                continue
            bb = pad.GetBoundingBox()
            cx = (bb.GetLeft() + bb.GetRight()) / 2e6
            cy = (bb.GetTop() + bb.GetBottom()) / 2e6
            hw = bb.GetWidth() / 2e6
            hh = bb.GetHeight() / 2e6
            pads.append((f"{fp.GetReference()}.{pad.GetNumber()}",
                         pad.GetNetname(), cx, cy, hw, hh))
    for vx, vy, vnet, vancho, _ in VIAS:
        vr = vancho / 2
        for nom, pnet, px, py, hw, hh in pads:
            if pnet == vnet:
                continue
            d = dist_seg_rect((vx, vy), (vx, vy), px, py, hw, hh) - vr
            minimo = 2.5 if (es_red(vnet) or es_red(pnet)) else CLEARANCE_MM
            if d < minimo:
                malos.append(f"via {vnet} en ({vx},{vy}) a {d:.2f}mm "
                             f"del pad {nom}[{pnet}]")
        for net, _capa, pts, ancho in TRACKS:
            if net == vnet:
                continue
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                d = dist_seg(a, b, (vx, vy), (vx, vy)) - vr - ancho / 2
                minimo = 2.5 if (es_red(net) or es_red(vnet)) else CLEARANCE_MM
                if d < minimo:
                    malos.append(f"via {vnet} en ({vx},{vy}) a {d:.2f}mm "
                                 f"de pista {net} ({a}-{b})")
    for i, (x1, y1, n1, a1, _t1) in enumerate(VIAS):
        for x2, y2, n2, a2, _t2 in VIAS[i + 1:]:
            if n1 == n2:
                continue
            d = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 - a1 / 2 - a2 / 2
            minimo = 2.5 if (es_red(n1) or es_red(n2)) else CLEARANCE_MM
            if d < minimo:
                malos.append(f"via {n1}({x1},{y1}) a {d:.2f}mm "
                             f"de via {n2}({x2},{y2})")
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
            minimo = 2.5 if (es_red(n1) or es_red(n2)) else CLEARANCE_MM
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
    # Recalibrado Tarea 8 ronda 1 (orquestador): los minimos de 0.25/0.3mm
    # eran herencia de la v1 (placa 100% THT) y ahogaban el escape de los
    # DFN de 0.45-0.5mm de paso sin motivo real. La capability estandar de
    # JLCPCB en 2 capas es clearance/track 0.127mm (5 mil) y taladro de via
    # 0.3mm (ver JLCPCB "PCB Capabilities", 2-Layer Prototype: min. trazado/
    # espaciado 3.4mil pero 5mil es la opcion "estandar" sin recargo; min.
    # taladro de via mecanico 0.3mm/12mil). m_ViasMinSize (diametro del pad
    # de la via, no el taladro) se deja en 0.6mm: JLC permite bajarlo, pero
    # no hace falta -- no es el cuello de botella de esta placa.
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_MinClearance = mm(0.127)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)
    # No se sube m_MinAnnularWidth (default de placa, 0.1mm): los 10
    # pads THT de U1/U2 (footprint TO-220/TO-247 heredado de Tarea 6/7,
    # taladro 1.1mm) dan un anillo real de 0.0875mm -- por debajo del
    # minimo de placa pero perfectamente fabricable en JLC (min. anillo
    # anular real ~0.05-0.075mm segun el proveedor, este caso esta por
    # encima). Bendecido explicitamente por el orquestador (ronda 2): se
    # documenta como excepcion aceptada, no se toca el footprint/BOM de
    # U1/U2 para "arreglarlo" (fuera del alcance de ruteo de esta tarea).
    # Ver DRC real: 10x [annular_width], unicas infracciones que quedan.


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
    # ronda 2, Important 3: H4 (taladro de fijacion NPTH) cae DENTRO de
    # ISLA_REF (ensanchada esta ronda para de-densificar la isla ultra) --
    # sin recorte, la zona pouraba cobre encima (DRC real: hole_clearance
    # 0mm, hace falta 0.25mm). Patron v1 para taladros de fijacion: sin
    # cobre alrededor. Recorte circular con margen comodo sobre el minimo.
    h4x, h4y = next((x, y) for ref, x, y in MOUNTING if ref == "H4")
    r_keepout = MOUNT_D / 2 + 0.4  # 1.6 + 0.4 = 2.0mm
    hole_idx = outline.NewHole(0)
    for i in range(16):
        ang = 2 * math.pi * i / 16
        outline.Append(mm(h4x + r_keepout * math.cos(ang)),
                        mm(h4y + r_keepout * math.sin(ang)), 0, hole_idx)
    # los defaults de fabrica de pcbnew para una ZONE nueva son 0.5mm de
    # clearance propio y conexion termica con spoke de 0.5mm -- muy por
    # encima del resto de la placa (CLEARANCE_MM=0.127, recalibrado a
    # capacidad JLC) y, sobre todo, mas ancho que el propio pad de JP1.1
    # (0.5x0.5mm): el spoke termico no cabia y JP1.1 se quedaba sin
    # conexion al cobre de la zona (DRC real: "unconnected", zona partida
    # en dos islas). Conexion solida (sin spoke) y clearance igual al
    # resto de la placa.
    zona.SetLocalClearance(mm(CLEARANCE_MM))
    zona.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
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
    contra_via = revisar_vias(board)
    print(f"vias contra pad/pista/via ajena: {len(contra_via)}")
    for c in contra_via[:8]:
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
    assert not contra_via, f"vias contra pad/pista/via ajena: {contra_via}"
    assert not bucles, f"la masa tiene bucles, no es una estrella: {bucles}"
    assert not cerca, f"taladros demasiado cerca de la red: {cerca}"
    assert not smd_mal, f"SMD fuera de F.Cu: {smd_mal}"
    assert not isla_mal, f"isla GNDREF mal: {isla_mal}"
    assert not diagonal_mal, f"lazo rectificador demasiado cerca de la isla ultra: {diagonal_mal}"
    assert not borde_mal, f"ceramicos demasiado cerca del borde: {borde_mal}"


if __name__ == "__main__":
    sys.exit(main())
