"""Genera sam17-power-v3.kicad_pcb: contorno, barrera de red y colocacion.

Fase C, Task 6 del plan v3 (docs/superpowers/plans/2026-08-18-fuente-v3-goat.md).
Igual que la v1 y la v2, va con pcbnew directo (nada de KiCAD-MCP-Server), asi
que hay que llamarlo con el Python de KiCad:

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Se hereda de la v2 (hardware/01-power-supply/v2/kicad/build_pcb.py) todo lo que
no depende de la geometria: contorno(), reglas(), revisar_estrella(),
revisar_pista_pad(), revisar_vias(), revisar_pistas(), revisar_smd_cara(),
revisar_isla_referencia(), revisar_diagonal(), revisar_borde_ceramicos(),
leer_netlist(), leer_bom(), dist_seg(), mm() y distancia_bbox().

QUE CAMBIA DE VERDAD, y las tres cosas salen del chasis, no de una preferencia:

  1. LA PLACA GIRA. 200 x 150 en vez de 150 x 200. El eje largo de la PCB va a
     lo ANCHO del case: 200 mm de los 528 disponibles, contra solo 150 de los
     223 de fondo (spec 2026-08-18 §3.3). Al reves no cabe.

  2. DESAPARECE LA RESERVA DE DISIPADOR. La v1 y la v2 guardaban 42 x 38.1 mm
     por cada TO-220 para su Fischer individual. Aqui el disipador es la PARED
     DEL CHASIS: los tres tabs se atornillan contra ella y la Tj de U2 baja de
     101 a 61 C (spec §3.1). Son 3 x 1600 mm2 que vuelven al layout.

  3. LA FILA DE TO-220 NO SE ELIGE AQUI. Su X la declara el chasis
     (chasis_to220_x / chasis_to220_paso en case/cad/params.scad) y esta placa
     la LEE de ese fichero. El canto de la placa y la pared son la misma cota
     vista desde dos lados; copiar el numero seria crear dos verdades que se
     separan en silencio.

Y una puerta nueva, revisar_to220_coplanares(): los tres tabs tienen que poder
tocar la misma pared plana. No es estetica de layout -- es si los tres
tornillos entran, y la mitad de los 8.5 K/W de la union termica se apoya en
eso.

Se van del BOM y de aqui: Q1, D7, R4, C14 (el crowbar, #118 -- se retiro
entero, no se sustituyo). Entran 33 refs nuevas: la isla de telemetria
(U8-U12, R21-R30, C29-C35, D14/D15, J8, TP9-TP11), los dos shunts (R19/R20) y
el filtro de modo comun de la SMPS (L1 poblado, CY1/CY2 sin poblar).

TRACKS y VIAS quedan VACIOS a proposito: el ruteo es la Task 7, sobre este
mismo fichero. revisar_pistas(), revisar_pista_pad() y revisar_estrella()
devuelven "sin problemas" de forma trivial mientras tanto, que es lo correcto
para esta fase -- y es exactamente lo que hizo la v2 entre sus Tareas 7 y 8.
"""
from __future__ import annotations

import csv
import math
import os
import re
import sys

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power-v3.kicad_pcb")
NET = os.path.join(DIR, "sam17-power-v3.net")
BOM = os.path.join(DIR, "..", "bom.csv")
STOCK = os.environ.get("KICAD_FOOTPRINTS",
                       r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
# sam17.pretty es de la v1: se comparte por fp-lib-table (ver ese fichero en
# esta misma carpeta), no se duplica.
LOCAL = os.path.join(DIR, "..", "..", "kicad", "sam17.pretty")

# ============================================================================
# GEOMETRIA. La v3 no la elige: la hereda del chasis.
# ============================================================================
# El canto de la placa y la pared del chasis son la misma cota vista desde dos
# lados, asi que los numeros se LEEN de case/cad/params.scad en vez de
# copiarse. Copiarlos seria crear dos verdades que se separan en silencio el
# dia que una de las dos se mueva -- y aqui separarse significa tres TO-220
# atornillados a una pared que ya no esta donde dice la placa.
PARAMS_CASE = os.path.join(DIR, "..", "..", "..", "..", "case", "cad",
                           "params.scad")


def leer_params_case() -> dict[str, float]:
    """Los parametros del chasis, del mismo fichero que dibuja el chasis."""
    with open(PARAMS_CASE, encoding="utf-8") as fh:
        txt = fh.read()
    p = {k: float(v) for k, v in
         re.findall(r"^\s*(\w+)\s*=\s*(-?[0-9.]+)\s*;", txt, re.M)}
    faltan = {"chasis_pcb_x", "chasis_pcb_y", "chasis_pcb_ancho",
              "chasis_pcb_fondo", "chasis_to220_x", "chasis_to220_paso",
              "chasis_to220_n"} - set(p)
    assert not faltan, f"params.scad no trae {sorted(faltan)}"
    return p


_CASE = leer_params_case()

# La placa ES el hueco que el chasis le reserva. Ni un milimetro elegido aqui.
W, H = _CASE["chasis_pcb_ancho"], _CASE["chasis_pcb_fondo"]      # 200 x 150

# La fila de TO-220, trasladada del marco del chasis al de la placa. El origen
# de la placa es la esquina (chasis_pcb_x, chasis_pcb_y) del interior.
TO220_X = [_CASE["chasis_to220_x"] - _CASE["chasis_pcb_x"]
           + _CASE["chasis_to220_paso"] * (i - (_CASE["chasis_to220_n"] - 1) / 2)
           for i in range(int(_CASE["chasis_to220_n"]))]
# Y de los pads. El cuerpo cuelga hacia -Y (rot 180), fuera de la placa, hacia
# la pared: los 10 mm entre canto y pared (chasis_pcb_y) son el sitio del
# conformado de patas. 4.0 deja MARGEN(3) y algo mas.
TO220_Y = 4.0

MARGEN = 3.0                    # de cualquier pieza al borde
# La barrera baja: en la v1 y la v2 la franja de red iba ARRIBA (y<30) porque
# la placa era alta y estrecha. Aqui la placa es ancha y baja, y arriba manda
# la pared del chasis, asi que la red se va al canto opuesto.
Y_BARRERA = 121.0
RANURA_ANCHO = 2.0
RANURA_X0, RANURA_X1 = 10.0, 190.0
FUGA_MIN = 6.0                  # cobre de red <-> cobre SELV (heredado v1)

# NO hay HS_ANCHO / HS_ALTO. La v1 y la v2 reservaban 42 x 38.1 mm por cada
# TO-220 para su disipador Fischer individual; en la v3 el disipador es la
# pared del chasis y esa reserva no existe. Son 3 x 1600 mm2 que vuelven al
# layout, y es la razon por la que una placa mas corta en un eje sigue
# sobrandole sitio. Lo que SI queda es una franja libre entre el canto y la
# fila de pads, que es por donde pasan las patas conformadas.

# Redes del lado de red. Las DOS ULTIMAS son nuevas de la v3 y no son un
# detalle: L_SMPS y N_SMPS son la salida del choke de modo comun hacia J7, o
# sea 230 V igual que antes de entrar. Sin ellas aqui es_red() las daba por
# SELV, y la puerta de fuga las medía contra el cobre de red -- que es su
# propio cobre. Lo cazó ella sola al colocar: 5.50 mm de fuga entre los dos
# pines de CY2, que son justamente los que un condensador de clase Y2 existe
# para puentear.
NETS_RED = {"L", "L_F", "L_TR", "N", "PE", "L_SMPS", "N_SMPS"}


def es_red(net: str) -> bool:
    return net.lstrip("/") in NETS_RED


# ref -> (x, y, rotacion). La v3 GIRA LA PLACA: 200 x 150 en vez de los
# 150 x 200 de la v1 y la v2. No es preferencia -- lo manda el chasis (spec
# §3.3): el eje largo de la PCB va a lo ANCHO del case, 200 mm de los 528
# disponibles contra solo 150 de los 223 de fondo. Al reves no cabe.
#
# Y desaparece la reserva de disipador. La v1 y la v2 guardaban 42 x 38.1 mm
# por cada TO-220 para su Fischer individual; en la v3 el disipador es la
# PARED DEL CHASIS, asi que esos 3 x 1600 mm2 vuelven al layout. Es la razon
# por la que una placa 25 % mas corta en un eje sigue teniendo sitio de sobra.
#
# Mapa de zonas (y crece hacia abajo):
#   y 0..10            MURALLA TO-220 contra la pared: U1 - U3 - U2. Su X NO
#                      se elige aqui: la declara el chasis (chasis_to220_x y
#                      chasis_to220_paso en case/cad/params.scad), y esta
#                      placa se pliega a ella. Es la unica cota del layout
#                      que viene de fuera.
#   y 14..40  x 76..172  columnas de soporte de cada pre-reg (in/out/proteccion)
#   y 36..60  x 76..140  puntos de prueba e indicadores
#   y 14..85  x 10..38   ISLA ULTRA (+ isla GNDREF)
#   y 14..85  x 44..66   divisores de ajuste de U1/U2 (R6/R8 en GNDREF)
#   y 88..124 x 130..196 LAZO DE RECTIFICACION + BULK -- el peor radiador
#   y 88..124 x 10..118  bus de salida, shunts e ISLA DE TELEMETRIA
#   y 128              ranura de la barrera de red
#   y 132..147         franja de red 230 V
#
# La diagonal de la spec §6.4 se mantiene: lazo abajo-derecha, isla ultra
# arriba-izquierda, con la muralla de TO-220 y las columnas de soporte de por
# medio. revisar_diagonal() lo mide.
PLACEMENT = {
    # --- MURALLA TO-220: los tabs contra la pared del chasis ---------------
    # rot 180 = el cuerpo cuelga hacia -Y, FUERA de la placa, hacia la pared.
    # Los 10 mm entre el canto de la placa (chasis y=10) y la cara interior de
    # la pared (chasis y=0) son el sitio del conformado de patas.
    "U1":  (TO220_X[0],  TO220_Y, 180),   # LM2941, pre-reg +13.1 V
    "U3":  (TO220_X[1],  TO220_Y, 180),   # LM7805, +5 V final
    "U2":  (TO220_X[2],  TO220_Y, 180),   # LM2991, pre-reg -12.9 V

    # --- columnas de soporte, cada una bajo su TO-220 ----------------------
    "C27": ( 76.0,  16.0,   0),   # 0.47uF, entrada de U1
    "C17": ( 90.0,  16.0,   0),   # salida ESR-controlada (ventana sec.1.1)
    "D12": ( 83.0,  27.0,   0),   # out->in, protege contra el bulk aguas abajo

    "C9":  (104.0,  16.0,   0),
    "C11": (130.0,  16.0,   0),
    "C10": (117.0,  16.0,   0),
    "D5":  (110.0,  27.0,   0),
    "R3":  (123.0,  27.0,   0),
    "D6":  ( 140.0,   27.0, 180),

    "C28": (150.0,  16.0,   0),   # entrada de U2
    "C18": (164.0,  16.0,   0),   # salida ESR-controlada (ventana sec.1.2)
    "D13": (157.0,  27.0,   0),   # out->in

    # --- fila de puntos de prueba ------------------------------------------
    "TP7": ( 78.0,  38.0,   0),   # +13V1 (salida de U1, entrada de U4/U5)
    "TP1": ( 94.0,  38.0,   0),   # VRAW+
    "TP6": (110.0,  38.0,   0),   # GND
    "TP5": (126.0,  38.0,   0),   # +5V
    "TP2": (142.0,  38.0,   0),   # VRAW-
    "TP8": (158.0,  38.0,   0),   # -12V9 (salida de U2, entrada de U6/U7)

    # --- indicadores de los rieles finales ---------------------------------
    # El crowbar de la v2 (Q1/D7/R4/C14) NO esta: se retiro entero, no se
    # sustituyo (#118, design-notes §16.8). Quedan solo los indicadores.
    "D3":  ( 78.0,  50.0, 180),   # LED +12V
    "R1":  ( 78.0,  60.0,   0),
    "D4":  ( 94.0,  50.0, 180),   # LED -12V
    "R2":  ( 94.0,  60.0,   0),
    "TP3": (112.0,  50.0,   0),   # +12V final (nace en la isla ultra)
    "TP4": (128.0,  50.0,   0),   # -12V final

    # --- ISLA ULTRA: pareja +12.000V (U4/U5, LT3045) -----------------------
    # Misma rejilla logica que la v2: columna izquierda = regulador 1,
    # columna derecha = regulador 2, columna central = lo COMPARTIDO (TVS,
    # SET, schottky, cap de SET). Cambian las coordenadas, no la topologia.
    "U4":  (  14.0,   14.0,   0),
    "D8":  (  25.0,   14.0,   0),   # TVS +13V1->GND
    "U5":  (  36.0,   14.0,   0),
    "R11": (  14.0,   20.5,   0),   # ILIM de U4 (Kelvin a su propio GND)
    "R9":  (  25.0,   20.5,   0),   # SET, compartida por U4 y U5
    "R12": (  36.0,   20.5,   0),   # ILIM de U5
    "C23": (  14.0,   27.0,   0),   # OUT de U4 (antes del ballast)
    "D10": (  25.0,   27.0,   0),   # schottky +12V->+13V1
    "C24": (  36.0,   27.0,   0),   # OUT de U5
    "R15": (  14.0,   33.5,   0),   # ballast de U4 -> +12V
    "C15": (  25.0,   33.5,   0),   # SET cap (compartida, baja fuga)
    "R16": (  36.0,   33.5,   0),   # ballast de U5 -> +12V
    "C19": (  14.0,   40.0,   0),   # entrada de U4 (+13V1)
    "C20": (  36.0,   40.0,   0),   # entrada de U5

    # --- puente unico GNDREF<->GND, entre las dos parejas -------------------
    "JP1": (  25.0,   46.5,   0),

    # --- ISLA ULTRA: pareja -12.000V (U6/U7, LT3094) -----------------------
    "U6":  (  14.0,   53.0,   0),
    "D9":  (  25.0,   53.0,   0),   # TVS GND->-12V9
    "U7":  (  36.0,   53.0,   0),
    "R13": (  14.0,   59.5,   0),   # ILIM de U6
    "R10": (  25.0,   59.5,   0),   # SET, compartida por U6 y U7
    "R14": (  36.0,   59.5,   0),   # ILIM de U7
    "C25": (  14.0,   66.0,   0),   # OUT de U6 (antes del ballast)
    "D11": (  25.0,   66.0,   0),   # schottky -12V->-12V9
    "C26": (  36.0,   66.0,   0),   # OUT de U7
    "R17": (  14.0,   72.5,   0),   # ballast de U6 -> -12V
    "C16": (  25.0,   72.5,   0),   # SET cap (compartida, baja fuga)
    "R18": (  36.0,   72.5,   0),   # ballast de U7 -> -12V

    # --- divisores de ajuste de U1/U2, al lado de la isla ------------------
    # Mismo criterio que la v2: R6 y R8 son el retorno de estos divisores y
    # viven en GNDREF, asi que se ACERCAN a la isla en vez de quedarse pegados
    # a U1/U2. La referencia del ADJ de un LM2941/LM2991 no es sub-uV -- eso lo
    # exige el SET del LT3045/LT3094 -- asi que un tramo de pista mas largo
    # hasta el ADJ no cuesta ruido real, y a cambio ISLA_REF sigue siendo una
    # isla y no una mancha que cruza la placa.
    "R6":  (  47.0,   20.5,   0),   # pin GNDREF, dentro de ISLA_REF
    "R5":  (  61.0,   20.5,   0),
    "RV2": (  63.0,   33.5,   0),
    "R8":  (  47.0,   59.5,   0),   # pin GNDREF, dentro de ISLA_REF
    "R7":  (  61.0,   59.5,   0),
    "RV3": (  63.0,   72.5,   0),

    # --- entradas de la isla, en su borde inferior --------------------------
    "C21": (  14.0,   79.0,   0),   # entrada de U6 (-12V9)
    "C22": (  36.0,   79.0,   0),   # entrada de U7

    # --- LAZO DE RECTIFICACION + BULK: esquina x alta / y alta -------------
    # El peor radiador de la placa (spec §6.4). Compacto y en la diagonal
    # OPUESTA a la isla ultra, con la muralla de por medio -- igual que la v2,
    # solo que ahora la diagonal va de arriba-izquierda a abajo-derecha.
    # J1 pega al canto derecho: el toroide vive justo ahi, a 15 mm de la placa.
    "J1":  ( 182.0,   74.0,   0),   # entrada del secundario (toma central)
    "BR1": ( 182.0,   96.0,   0),
    "C1":  ( 136.0,   92.0,   0),
    "C12": ( 158.0,   92.0,   0),
    "C2":  ( 136.0,  110.0,   0),
    "C13": ( 158.0,  110.0,   0),

    # --- bus de salida y shunts --------------------------------------------
    # J2/J6 pegados al canto izquierdo: la ranura de salida de cables del
    # chasis cae justo debajo de esta esquina (chasis_salida_* en
    # case/cad/params.scad), asi que el mazo baja sin cruzar la placa.
    #
    # Los shunts van AGUAS ABAJO, entre el riel y el conector: miden lo que
    # sale hacia los modulos, no lo que consumen el indicador ni la propia
    # telemetria. Y su INA226 va pegado a ellos -- las dos lineas de sensado
    # son la unica parte de la isla que no tolera un viaje largo.
    "J2":  (  15.0,   90.0,   0),   # bus +12/GND/GND/-12
    "R19": (  30.0,   88.0,   0),   # shunt del +12V
    "U8":  (  42.0,   88.0,   0),   # INA226 del +12V, 0x40
    "C29": (  52.0,   88.0,   0),
    "J6":  (  15.0,  104.0,   0),   # feed +5V al modulo 2
    "R20": (  30.0,  102.0,   0),   # shunt del +5V
    "U9":  (  42.0,  102.0,   0),   # INA226 del +5V, 0x41
    "C30": (  52.0,  102.0,   0),
    "J5":  (  16.0,  114.0,   0),   # faston GND->chasis

    # --- ISLA DE TELEMETRIA -------------------------------------------------
    # Lejos del lazo de rectificacion (el otro extremo de la placa) y lejos de
    # la muralla de TO-220 (la banda de arriba). Los divisores van pegados al
    # ADC y no al riel: el nodo de alta impedancia es el TAP, asi que el tramo
    # que hay que acortar es tap->ADC, no riel->divisor.
    "R21": (  56.0,   88.0,   0),   # 100k, riel -12V
    "R24": (  56.0,   95.0,   0),   # 20k, a +5V (la referencia)
    "R22": (  66.0,   88.0,   0),   # 100k, VRAW+
    "R25": (  66.0,   95.0,   0),   # 20k, a GNDA
    "R23": (  76.0,   88.0,   0),   # 100k, VRAW-
    "R26": (  76.0,   95.0,   0),   # 20k, a +5V
    "D14": (  56.0,  104.0,   0),   # clamp del tap de -12V
    "D15": (  66.0,  104.0,   0),   # clamp del tap de VRAW-
    "U10": (  88.0,   88.0,   0),   # ADS1115, 0x49
    "C31": (  88.0,   97.0,   0),
    "U11": (  78.0,  108.0,   0),   # TMP1075, 0x48 (aire del recinto)
    "C32": (  88.0,  108.0,   0),
    "R27": (  56.0,  110.0,   0),   # pull-up SDA_A
    "R28": (  66.0,  110.0,   0),   # pull-up SCL_A
    "U12": ( 104.0,   88.0,   0),   # ISO1541, la barrera GNDA/GNDD
    "C33": ( 104.0,   97.0,   0),   # desacoplo lado analogico
    "C34": ( 104.0,  106.0,   0),   # desacoplo lado digital
    "C35": (  96.0,   97.0,   0),
    "R29": (  96.0,  106.0,   0),   # pull-up SDA_D
    "R30": (  96.0,  114.0,   0),   # pull-up SCL_D
    "J8":  ( 106.0,  114.0,   0),   # 2.00 mm JST-PH: incompatible con J2/J6 a proposito
    "TP9": (  30.0,  114.0,   0),
    "TP10":(  42.0,  114.0,   0),
    "TP11":(  54.0,  114.0,   0),

    # --- FRANJA DE RED 230 V, bajo la barrera -------------------------------
    # Orden electrico de izquierda a derecha: entrada, fusible, y ahi el nodo
    # L_F se parte en dos -- al limitador de inrush y al toroide por un lado,
    # al filtro de modo comun y la SMPS por el otro. Que L1 pinche en L_F y no
    # en L_TR es la regla de la spec v2 §7: la SMPS comparte fusible con el
    # toroide pero NO comparte el limitador, que esta dimensionado para TR1.
    "J3":  (  17.0,  132.0,   0),   # entrada de red: L / N / PE
    "F1":  (  38.0,  134.0,   0),   # portafusible cerrado, 1.6 A T
    "NT1": (  88.0,  135.0,   0),   # limitador de inrush
    "RV1": (  63.0,  135.0,   0),   # MOV
    "L1":  ( 126.0,  131.0,   0),   # choke de modo comun (poblado: va en SERIE)
    "CY1": ( 172.0,  129.0,   0),   # clase Y2 a PE -- SIN POBLAR (va en PARALELO)
    "CY2": ( 172.0,  143.0,   0),   # idem
    "J7":  ( 158.0,  135.0,   0),   # deriva a la SMPS digital IRM-15-5
    "J4":  ( 110.0,  135.0,   0),   # salida al primario de TR1
}

# Rectangulo de colocacion de la isla GNDREF (x1, y1, x2, y2), en mm. Envuelve
# los pads que tocan la red GNDREF -- R9.2, C15.2, R10.2, C16.2, R6.2, R8.1 --
# mas JP1, el unico puente admitido a GND. Mismo criterio que la v2: la isla
# tiene que alcanzar cada uno de esos pads o se quedan sin cobre, y no mas que
# eso o deja de ser una isla y pasa a ser una mancha.
ISLA_REF = (10.0, 12.0, 54.0, 86.0)

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
# TASK 7 — ruteo. Vacio en esta fase A PROPOSITO: la Task 6 es colocacion, y
# mezclar las dos es como se pierde la trazabilidad de por que una pieza esta
# donde esta. La estrategia de la v2 (corredor alto para +13V1/-12V9, Kelvin de
# OUTS por B.Cu hasta el pad de J2, tronco de GND entero en B.Cu, SET y ILIM en
# saltos cortos dentro de la isla, GNDREF sin pistas propias porque lo resuelve
# la zona) se hereda tal cual y se reescribe contra estas coordenadas.
# ============================================================================
# ============================================================================
# TASK 7 — ruteo.
# ============================================================================
# LA DIFERENCIA CON LA v2, y no es de estilo: alli TRACKS era una lista de
# ~1000 coordenadas literales escritas a mano. Funciona, y tiene un modo de
# fallo desagradable -- mover una pieza un milimetro no rompe nada VISIBLE:
# las pistas se quedan donde estaban, apuntando a donde el pad ESTABA. El DRC
# lo veria, pero solo si alguien lo corre, y la relacion entre el numero
# "92.0" de una pista y el pad al que pretendia llegar no esta escrita en
# ningun sitio.
#
# Aqui las pistas se CALCULAN de las posiciones reales de los pads, ya
# colocados, leyendolas de la placa. Una ruta dice "de U4 pin 1 a C19 pin 1",
# no "de (92.0, 168.0) a (92.0, 192.0)". Si la pieza se mueve, la pista se
# mueve con ella; si el pin no existe, revienta al generar y no al fabricar.
#
# Lo que NO cambia respecto de la v2, porque es diseno y no herramienta:
#
#   * GND es un ARBOL, no una malla ni un plano. Un plano de masa es la
#     respuesta correcta en casi cualquier placa digital y la equivocada aqui:
#     crea lazos, y un lazo alrededor del puente rectificador es una espira de
#     100 Hz acoplada a todo lo demas. revisar_estrella() lo comprueba.
#   * El tronco de GND vive entero en B.Cu, y los pads escapan con una via
#     corta nada mas salir. F.Cu se reserva para las señales y la potencia.
#   * El Kelvin de OUTS (+12V/-12V) sale del pin por una via inmediata y viaja
#     por B.Cu sin tocar la pista de potencia del ballast, hasta soldarse solo
#     en el pad de J2.
#   * SET va corta y fina. ILIM tambien.
#   * El cobre de red va ancho y con 2.5 mm de aire a cualquier otra cosa.


def pad_xy(board, ref: str, pin: str) -> tuple[float, float]:
    """Centro de un pad, en mm, leido de la placa ya colocada."""
    fp = board.FindFootprintByReference(ref)
    assert fp, f"no existe {ref} en la placa"
    for p in fp.Pads():
        if p.GetNumber() == pin:
            c = p.GetPosition()
            return (c.x / 1e6, c.y / 1e6)
    raise AssertionError(f"{ref} no tiene pin {pin}")


def pad_red(board, ref: str, pin: str) -> str:
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == pin:
            return p.GetNetname()
    raise AssertionError(f"{ref}.{pin} no existe")


class Ruteo:
    """Acumula tramos y vias, y se asegura de que cada tramo diga su red.

    La red NO se pasa a mano: se lee del primer pad del tramo. Asi una pista
    no puede declarar una red y salir de otra, que es el error que ni el DRC
    ni revisar_pistas() cazan bien -- los dos comprueban geometria, no
    intencion.
    """

    def __init__(self, board):
        self.board = board
        self.tracks: list = []
        self.vias: list = []

    def _pt(self, p):
        """(ref, pin) -> (x, y); (x, y) se deja tal cual."""
        return pad_xy(self.board, *p) if isinstance(p[0], str) else p

    def pista(self, capa, puntos, ancho, red=None):
        """Un tramo. `puntos` mezcla (ref, pin) y (x, y) libremente."""
        pts = [self._pt(p) for p in puntos]
        # La red se declara como (ref, pin), NUNCA como cadena: el nombre que
        # usa KiCad depende de si la red nace de una etiqueta local ("/L_F") o
        # de un simbolo de alimentacion ("PE"), y escribirlo a mano es apostar
        # a cual de las dos. Un pad no se equivoca.
        if isinstance(red, tuple):
            red = pad_red(self.board, *red)
        if red is None:
            anc = next((p for p in puntos if isinstance(p[0], str)), None)
            assert anc, "una pista sin ningun pad tiene que declarar su red"
            red = pad_red(self.board, *anc)
        self.tracks.append((red, capa, pts, ancho))
        return self

    def via(self, p, red=None, ancho=0.6, taladro=0.3):
        x, y = self._pt(p)
        if isinstance(red, tuple):
            red = pad_red(self.board, *red)
        if red is None:
            assert isinstance(p[0], str), "una via suelta tiene que decir su red"
            red = pad_red(self.board, *p)
        self.vias.append((x, y, red, ancho, taladro))
        return self

    def salto(self, capa, a, b, ancho, eje="x", red=None):
        """Ruta en L entre dos puntos. `eje` = el tramo que va primero."""
        xa, ya = self._pt(a)
        xb, yb = self._pt(b)
        codo = (xb, ya) if eje == "x" else (xa, yb)
        return self.pista(capa, [a, codo, b], ancho, red)

    def cadena(self, capa, puntos, ancho, red=None):
        """Une una lista de pads en cadena, cada uno con el siguiente."""
        for a, b in zip(puntos, puntos[1:]):
            self.pista(capa, [a, b], ancho, red)
        return self

    def bajar(self, p, ancho_via=0.6):
        """Saca un pad de F.Cu a B.Cu con una via en el sitio."""
        return self.via(p, ancho=ancho_via)


# --- el arbol de GND, entero en B.Cu ---------------------------------------
# LA DECISION DE CAPA (issue #134, opcion B). GND son 68 de los 306 pads: mas
# de la quinta parte de la placa. Sacarla entera de F.Cu es lo que deja sitio
# a todo lo demas, y es lo que hizo la v2.
#
# Y va como ARBOL, no como plano. Un plano de masa es la respuesta correcta en
# casi cualquier placa digital y la equivocada aqui: un plano crea lazos, y un
# lazo alrededor del puente rectificador es una espira de 100 Hz acoplada a
# todo. revisar_estrella() lo comprueba con union-find sobre los extremos de
# los tramos, asi que las costillas se parten en cada punto de enganche -- si
# fueran un solo tramo de punta a punta, el union-find solo veria sus dos
# extremos y un lazo de verdad pasaria sin que nadie lo viera.
#
# Forma: un PEINE. Tronco vertical en x=11 (el canal libre del canto
# izquierdo), y siete costillas horizontales en las bandas donde no hay ningun
# pad pasante. Cada pad baja a su costilla por su propia x. Raiz electrica en
# J1.2, la toma central del secundario -- que es por donde vuelve la corriente
# de rectificacion, la mas grande de la placa.
GND_TRONCO_X = 11.0
GND_COSTILLAS = (11.0, 23.0, 44.0, 66.0, 84.0, 99.0, 117.0)
ANCHO_GND = 1.0


# Cuanto se separa la via del pad SMD al que sirve. Una via de 0.6 mm EN el
# pad de un chip de 0.5 mm de paso deja 0.03 mm al pin vecino -- lo midio
# revisar_vias() en 20 sitios. Se saca con un rabito corto en F.Cu, hacia
# fuera del cuerpo del chip, y la via va al final. Los pads grandes (el EP
# termico de un DFN) son la excepcion: ahi la via va dentro, que es para lo
# que existe el EP.
GND_FANOUT = 1.7
GND_PAD_GRANDE = 1.5


def _hay_sitio(board, punto, ref_propia: str, pin_propio: str,
               radio: float = 0.75) -> bool:
    """Si una via de 0.6 mm en `punto` deja aire a todo pad que no sea EL SUYO.

    El radio de 0.75 no es holgura de gusto: es el radio de la via (0.3) mas
    0.45 de aire, sobre un minimo de fabricacion de 0.127. Se probo con 1.3 y
    la via de U9.7 no cabia por ningun lado -- en un MSOP de 0.5 mm de paso,
    pedir 1.3 mm a los pines vecinos es pedir que el chip no exista.

    "El suyo" es el pad exacto, no la huella entera. Saltarse la huella
    completa fue el primer intento y salio mal en el sitio obvio: el rabito de
    C29 esquivo a R21 yendose al oeste y aterrizo encima del OTRO pad de C29.
    """
    px, py = punto
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if fp.GetReference() == ref_propia and p.GetNumber() == pin_propio:
                continue
            bb = p.GetBoundingBox()
            dx = max(bb.GetLeft() / 1e6 - px, 0, px - bb.GetRight() / 1e6)
            dy = max(bb.GetTop() / 1e6 - py, 0, py - bb.GetBottom() / 1e6)
            if (dx * dx + dy * dy) ** 0.5 < radio:
                return False
    return True


def rutear_gnd(r: Ruteo) -> None:
    board = r.board
    pads = []
    for fp in board.GetFootprints():
        centro = fp.GetPosition()
        for p in fp.Pads():
            if p.GetNetname() != "GND":
                continue
            c, tam = p.GetPosition(), p.GetSize()
            pads.append((c.x / 1e6, c.y / 1e6, fp.GetReference(), p.GetNumber(),
                         p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD,
                         (centro.x / 1e6, centro.y / 1e6),
                         min(tam.x, tam.y) / 1e6))
    assert pads, "la placa no tiene pads de GND"

    enganches: dict[float, set] = {y: set() for y in GND_COSTILLAS}
    for x, y, ref, pin, smd, (cx, cy_fp), lado in pads:
        xv, yv = x, y
        if smd and lado < GND_PAD_GRANDE:
            # Hacia fuera del cuerpo, por el eje en que el pad esta mas lejos
            # del centro. Pero "fuera del chip" no siempre es "libre": el
            # rabito de C29 salia al este y aterrizaba encima de R21. Asi que
            # se prueban las cuatro direcciones en orden de preferencia y se
            # coge la primera que deje sitio -- si ninguna lo deja, revienta
            # aqui en vez de dejarlo pasar al DRC.
            dx, dy = x - cx, y - cy_fp
            eje_x = abs(dx) >= abs(dy)
            orden = ([(GND_FANOUT if dx >= 0 else -GND_FANOUT, 0),
                      (-GND_FANOUT if dx >= 0 else GND_FANOUT, 0),
                      (0, GND_FANOUT), (0, -GND_FANOUT)] if eje_x else
                     [(0, GND_FANOUT if dy >= 0 else -GND_FANOUT),
                      (0, -GND_FANOUT if dy >= 0 else GND_FANOUT),
                      (GND_FANOUT, 0), (-GND_FANOUT, 0)])
            for ddx, ddy in orden:
                cand = (x + ddx, y + ddy)
                if _hay_sitio(board, cand, ref, pin):
                    xv, yv = cand
                    break
            else:
                raise AssertionError(
                    f"la via de GND de {ref}.{pin} no cabe por ningun lado")
            r.pista(F, [(x, y), (xv, yv)], 0.3, red=(ref, pin))
        if smd:
            r.via((xv, yv), red=(ref, pin))
        cost = min(GND_COSTILLAS, key=lambda c: abs(c - yv))
        enganches[cost].add(round(xv, 3))
        if abs(yv - cost) > 0.01:
            r.pista(B, [(xv, yv), (xv, cost)], ANCHO_GND, red=(ref, pin))

    ref_gnd = (pads[0][2], pads[0][3])
    for cy in GND_COSTILLAS:
        xs = sorted(enganches[cy] | {GND_TRONCO_X})
        for a, b in zip(xs, xs[1:]):
            r.pista(B, [(a, cy), (b, cy)], ANCHO_GND, red=ref_gnd)

    for a, b in zip(GND_COSTILLAS, GND_COSTILLAS[1:]):
        r.pista(B, [(GND_TRONCO_X, a), (GND_TRONCO_X, b)], ANCHO_GND, red=ref_gnd)


# --- la red, bajo la barrera -----------------------------------------------
# Aqui el reparto de capas NO es el de la placa (F.Cu potencia / B.Cu masa):
# bajo la barrera no hay masa, asi que las dos capas estan libres y se usan las
# dos. La cadena caliente -- entrada, fusible, limitador, primario -- se queda
# entera en F.Cu y de una pieza; el neutro, la tierra y la derivacion a la
# SMPS bajan a B.Cu. No es simetria: es que L_F tiene que cruzar la franja
# entera y todo lo demas se le pone delante.
#
# CARRILES. Cada red tiene su y reservada, y estan elegidas donde NO hay ningun
# pad: 124.5 y 129 en F.Cu, 123.5 / 127 / 136-137 / 145.5 en B.Cu. La
# separacion entre carriles de redes distintas es >= 2.5 mm, que es lo que
# revisar_pistas() exige en cuanto una de las dos es de red.
def rutear_red(r: Ruteo) -> None:
    """La franja de red. Cinco carriles, y cada uno esta donde no hay pads.

    EL PINOUT DEL CHOKE FUERZA UN CRUCE Y NO HAY FORMA DE COLOCARLO PARA
    EVITARLO. En el 8104-RC la entrada de L y la de N estan en esquinas
    OPUESTAS (pin 1 arriba-izquierda, pin 3 abajo-derecha), asi que sus dos
    salidas tambien: L_SMPS sale por abajo-izquierda y N_SMPS por
    arriba-derecha, y las dos tienen que llegar al mismo sitio a la derecha.
    Se cruzan si van por la misma capa, se coloque el choke donde se coloque.

    Se resuelve con capas, no con geometria: L_SMPS por B.Cu en el carril de
    arriba, N_SMPS por F.Cu en el de abajo. Es la unica pareja de la placa que
    necesita las dos capas para NO tocarse.

    Los carriles, y el hueco donde vive cada uno:

        F.Cu  123.0  L_F      (entre la ranura y la fila de pads de 129-135)
        F.Cu  127.5  L        (solo x=17..38, delante del fusible)
        F.Cu  129.0  L_TR     (entre NT1 y J4, por encima de sus pads)
        F.Cu  143.0  N_SMPS
        B.Cu  123.0  PE       (cruza la franja entera: es el carril mas largo)
        B.Cu  126.5  L_SMPS

    Los dos ultimos van a 2.50 y 2.50 mm exactos de su vecino mas cercano, que
    es el minimo que revisar_pistas() exige en cuanto una de las dos redes es
    de red. No sobra ni una decima: entre la ranura (122) y la fila de pads
    del choke (131) hay 9 mm y ahi caben exactamente dos carriles de 230 V.
        B.Cu  146.0  N

    Ninguna de estas pistas lleva via: los 23 pads de red son todos pasantes,
    asi que el cobre de las dos capas ya los toca. En una franja de 230 V eso
    no es comodidad -- una via es un agujero metalizado de 0.3 mm en medio del
    aislamiento, y no ponerlos es una decision.
    """
    # --- F.Cu ---------------------------------------------------------------
    r.pista(F, [("J3", "1"), (17.0, 127.5), (38.0, 127.5), ("F1", "1")],
            ANCHO_RED)
    r.pista(F, [("F1", "2"), (45.62, 123.0), (126.0, 123.0)], ANCHO_RED,
            red=("NT1", "1"))
    for ref, pin in (("RV1", "1"), ("NT1", "1"), ("L1", "1")):
        x, _ = pad_xy(r.board, ref, pin)
        r.pista(F, [(x, 123.0), (ref, pin)], ANCHO_RED)
    r.pista(F, [("NT1", "2"), (95.5, 129.0), (115.0, 129.0), ("J4", "2")],
            ANCHO_RED)
    r.pista(F, [("L1", "4"), (153.0, 131.0), (153.0, 143.0), ("CY2", "1")],
            ANCHO_RED)
    r.pista(F, [(163.0, 143.0), ("J7", "2")], ANCHO_RED, red=("J7", "2"))
    r.pista(F, [("CY1", "2"), ("CY2", "2")], ANCHO_RED)

    # --- B.Cu ---------------------------------------------------------------
    r.pista(B, [("J3", "2"), (22.0, 146.0), (146.32, 146.0)], ANCHO_RED,
            red=("J3", "2"))
    for ref, pin in (("RV1", "2"), ("J4", "1"), ("L1", "3")):
        x, _ = pad_xy(r.board, ref, pin)
        r.pista(B, [(x, 146.0), (ref, pin)], ANCHO_RED)
    r.pista(B, [("J3", "3"), (27.0, 123.0), (179.5, 123.0), ("CY1", "2")],
            ANCHO_RED)
    r.pista(B, [("L1", "2"), (120.0, 141.16), (120.0, 126.5), (172.0, 126.5),
                ("CY1", "1")], ANCHO_RED)
    r.pista(B, [(158.0, 126.5), ("J7", "1")], ANCHO_RED, red=("J7", "1"))


def rutear(board) -> Ruteo:
    """Todas las pistas de la placa. VACIA todavia -- ver la nota de arriba.

    El primer intento esta medido y descartado, y el numero es el argumento:
    ruteando en L sobre F.Cu, con corredores elegidos a ojo, TRES de los diez
    grupos (red, lazo de rectificacion y los dos rieles del pre-regulador,
    77 tramos) dieron **54 cruces y 28 pistas sobre pads ajenos**. No es que
    estuviera mal escrito: es que en dos capas no cabe una topologia plana.

    Lo que hace falta antes de escribir una sola pista mas es una DISCIPLINA
    DE CAPA declarada, y es una decision de diseno, no de herramienta:

      * F.Cu horizontal / B.Cu vertical, con via en cada codo. Los cruces se
        vuelven imposibles por construccion y el precio son cientos de vias.
      * o el reparto de la v2 -- potencia en F.Cu, arbol de GND entero en
        B.Cu -- que funciona porque GND es la mitad de la placa (68 de 306
        pads) y quitarla de F.Cu deja sitio al resto.

    La segunda es la que la v2 uso y la que este diseno pide, pero necesita
    ademas un reparto de CORREDORES: una coordenada horizontal reservada por
    riel, para que dos pistas de F.Cu no compartan la misma y. Eso es lo que
    hay que escribir, y es un trabajo con su propia ronda, no un apendice de
    la colocacion.

    Mientras tanto esta funcion devuelve vacio, y eso es HONESTO en el sentido
    del Principio V: revisar_pistas(), revisar_estrella() y revisar_pista_pad()
    dan [] trivialmente y lo dicen, la placa no tiene rutas, y nadie puede
    confundir el verde de las puertas de colocacion con una placa terminada.
    La v2 hizo exactamente esto entre sus Tareas 7 y 8.
    """
    r = Ruteo(board)
    rutear_gnd(r)
    rutear_red(r)
    return r


TRACKS: list[tuple[str, str, list[tuple[float, float]], float]] = []

# Vias con tamano propio: (x, y, net, ancho_mm, taladro_mm). La granja
# termica del EP de U4/U5 (brief Tarea 8, 3x3, 0.3 mm) vive aqui -- y
# TAMBIEN la de U6/U7 (F6, review fase C: correccion de este comentario, que
# decia lo contrario). Los CUATRO chips usan la variante SIN vias de la
# huella DFN de la libreria stock de KiCad: U4/U5 son
# "DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm" y U6/U7 son
# "DFN-12-1EP_3x3mm_P0.45mm_EP1.65x2.38mm" (netlist real, sam17-power-v3.net)
# -- ninguna trae el sufijo "_ThermalVias". La huella con vias de fabrica en
# el propio pad del EP nunca se uso en v2; el nombre quedo en una version
# vieja de este comentario, sin que nadie lo corrigiera contra el netlist
# real. Por eso el EP de U6/U7 TAMBIEN necesita su propia granja manual,
# igual que U4/U5 -- son las entradas "ronda 3, F3" mas abajo en este mismo
# VIAS (net /-12V9) y en TRACKS (los spokes B.Cu que las conectan al tronco).
# Las demas vias son "escapes" cortos de la rejilla de F.Cu de la isla hacia
# el arbol de GND en B.Cu (Kelvin de OUTS y GND de los pads SMD que no
# tienen EP que los lleve gratis).
VIAS: list[tuple[float, float, str, float, float]] = []

MOUNTING = [("H1", 7.0, 7.0), ("H2", 193.0, 7.0),
            ("H3", 7.0, 143.0), ("H4", 193.0, 143.0)]
MOUNT_D = 3.2                   # M3, SIN pad de cobre (igual que v1)

# ============================================================================
# F1/F2 (review fase C, fixwave) -- textos libres en F.SilkS. La placa no
# tenia NI UNO. Formato: (texto, x, y, tamano_mm, rotacion_deg). Todos
# centrados (horiz. y vert.) en (x,y) -- mas facil de razonar en mm que con
# justificacion left/top. Posiciones verificadas contra pads/vias/zonas de
# cobre y contra la demas serigrafia con el mismo criterio que usa kicad-cli
# (silk_overlap/silk_over_copper, ver fab-fixwave-report.md): 0 violaciones.
# ============================================================================
TEXTOS_SILK: list[tuple[str, float, float, float, float]] = [
    # Marca del + de BR1: la huella (Diode_Bridge_DIP-4, stock KiCad) es
    # simetrica a 180 grados, asi que no hay forma de saber por donde va sin
    # esto. Junto al pad 1, que es la esquina + real.
    ("+", 178.0, 96.0, 1.2, 0),

    ("SAM17 PSU v3", 168.0, 62.0, 1.4, 0),
    ("rev A - 2026-08-19", 168.0, 67.0, 1.0, 0),

    # Rotulos de los puntos de prueba. Van DEBAJO de cada TP.
    ("+13V1", 78.0, 42.5, 1.0, 0),
    ("VRAW+", 94.0, 42.5, 1.0, 0),
    ("GND", 110.0, 42.5, 1.0, 0),
    ("+5V", 126.0, 42.5, 1.0, 0),
    ("VRAW-", 142.0, 42.5, 1.0, 0),
    ("-12V9", 158.0, 42.5, 1.0, 0),
    ("+12V", 112.0, 54.5, 1.0, 0),
    ("-12V", 128.0, 54.5, 1.0, 0),

    # EL AVISO DE LOS TABS. En la v1 y la v2 cada TO-220 llevaba su disipador
    # suelto y solo U2 necesitaba mica. Aqui los TRES se atornillan a la MISMA
    # pared, que ademas es la referencia de PE: dos de los tres tabs estan a
    # VRAW+ y VRAW-, o sea que sin aislante el primer tornillo pone el
    # secundario rectificado contra tierra. Va en mayusculas y en el sitio
    # donde el que atornilla esta mirando.
    ("TABS AISLADOS: MICA + PASADOR", 150.0, 33.0, 1.1, 0),

    # EL INVARIANTE DE LOS DIVISORES. El README de la v3 lo dejo escrito como
    # hueco declarado: mal DIBUJADO lo caza check_netlist.py, mal POBLADO (un
    # 20k soldado donde va el 100k, las dos son 0805 identicas) no lo caza
    # nadie. Esta linea es ese "nadie". Va entre las dos filas del divisor,
    # que es donde mira quien las suelda.
    ("R21 R22 R23 = 100k (AL RIEL)", 66.0, 84.5, 0.9, 0),
    ("R24 R25 R26 = 20k (A LA REFERENCIA)", 66.0, 99.8, 0.9, 0),

    # Rotulo de J2. Es el bug del #121 puesto en cobre: el pin 1 es -12V, no
    # +12V. Quien monte el mazo lee ESTO, no el esquematico.
    ("-12V", 15.00, 82.0, 0.85, 90),
    ("GND", 17.54, 82.0, 0.85, 90),
    ("GND", 20.08, 82.0, 0.85, 90),
    ("+12V", 22.62, 82.0, 0.85, 90),
]


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


def texto_silk(board, texto: str, x: float, y: float, tam: float, rot: float):
    """Un PCB_TEXT libre en F.SilkS, centrado en (x,y) (F1/F2, ver TEXTOS_SILK)."""
    t = pcbnew.PCB_TEXT(board)
    t.SetText(texto)
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(tam), mm(tam)))
    t.SetTextThickness(mm(tam * 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    if rot:
        t.SetTextAngleDegrees(rot)
    board.Add(t)
    return t


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


def leer_bom() -> dict[str, str]:
    """ref -> Value recortado, desde bom.csv (F7, review fase C).

    Mismo criterio de columna `refs` (separada por coma, "—" son piezas
    mecanicas fuera de hoja) que check_bom.py. El recorte toma el texto
    antes de la primera coma O el primer parentesis, lo que aparezca antes
    -- una fila del BOM es "valor, nota tecnica larga..." o "valor (detalle
    tecnico); nota", y solo el primer trozo es un Value legible de
    serigrafia/pos.csv. Antes de F7, fp.Value() se dejaba con el nombre de
    la huella (ver comentario junto a fp.Value().SetVisible(False) en
    main()) y eso es lo que terminaba en la columna Val del pos.csv.
    """
    valores: dict[str, str] = {}
    with open(BOM, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            valor = row["value"].split(",", 1)[0].split("(", 1)[0].strip()
            for ref in (r.strip() for r in row["refs"].split(",")):
                if ref and ref != "—":
                    valores[ref] = valor
    return valores


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


def franja_to220(board: pcbnew.BOARD) -> None:
    """Marca en F.Fab la franja entre el canto y la fila de pads de los TO-220.

    Reemplaza a reserva_disipadores() de la v1/v2, que dibujaba el cuadrado de
    42 x 38.1 del Fischer de cada uno. Aqui no hay Fischer: hay pared. Lo que
    si hay que reservar -- y no se ve en ningun sitio si no se dibuja -- es la
    franja por la que pasan las PATAS CONFORMADAS, del canto de la placa hasta
    la fila de pads. Nada puede vivir ahi, ni cobre de otra red ni serigrafia,
    o el conformado apoya encima.
    """
    for x in TO220_X:
        for x1, y1, x2, y2 in [(x - 8, 0.0, x + 8, 0.0),
                               (x + 8, 0.0, x + 8, TO220_Y + 2),
                               (x + 8, TO220_Y + 2, x - 8, TO220_Y + 2),
                               (x - 8, TO220_Y + 2, x - 8, 0.0)]:
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
    # No hace falta subir m_MinAnnularWidth (default de placa, 0.1mm): ya NO
    # hay pads por debajo de ese minimo. F3 (review fase C) RESOLVIO -- no
    # bendijo -- las 10 violaciones annular_width de los pads THT de U1/U2
    # (footprint TO-220-5 stock, taladro 1.1mm): antes daban un anillo real
    # de 0.0875mm (por debajo de la capability JLC de 2 capas, 0.13mm), y en
    # vez de documentarlas como excepcion aceptada se ensancho el eje corto
    # del pad a 1.4mm (ver main(), justo despues de colocar U1/U2) -> anillo
    # (1.4-1.1)/2=0.15mm, ya por encima del minimo real. DRC completo real:
    # 0 violaciones de cualquier tipo, no 10 bendecidas.


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


def revisar_margen(board) -> list[str]:
    """Nada se sale del contorno ni se pega al canto mas de MARGEN.

    Los tres TO-220 son la excepcion DECLARADA: su cuerpo sale de la placa por
    el canto de arriba, que es como llega a la pared del chasis. Lo que tiene
    que respetar el margen son sus pads.
    """
    fuera = []
    for fp in board.GetFootprints():
        bb = _caja_util(fp)
        if (bb.GetLeft() < mm(MARGEN) or bb.GetRight() > mm(W - MARGEN)
                or bb.GetTop() < mm(MARGEN) or bb.GetBottom() > mm(H - MARGEN)):
            fuera.append(fp.GetReference())
    return fuera


def _caja_util(fp):
    """La caja que la pieza ocupa EN la placa."""
    if fp.GetReference() in ("U1", "U2", "U3"):
        bb = None
        for pad in fp.Pads():
            bb = pad.GetBoundingBox() if bb is None else bb
            bb.Merge(pad.GetBoundingBox())
        return bb
    return fp.GetBoundingBox(False, False)


def _caja_patio(fp):
    """El patio IPC si la huella lo trae; si no, su caja."""
    if fp.GetReference() in ("U1", "U2", "U3"):
        return _caja_util(fp)
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return bb if bb.GetWidth() else fp.GetBoundingBox(False, False)


def revisar_solapes(board) -> list[str]:
    """Ninguna huella pisa a otra, medido por patio IPC."""
    cajas = [(fp.GetReference(), _caja_patio(fp)) for fp in board.GetFootprints()]
    return [f"{a}~{b}" for i, (a, ba) in enumerate(cajas)
            for b, bb in cajas[i + 1:] if distancia_bbox(ba, bb) == 0.0]


def revisar_sobre_ranura(board) -> list[str]:
    """Nada montado encima de la ranura de la barrera."""
    ranura = pcbnew.BOX2I(
        pcbnew.VECTOR2I(mm(RANURA_X0), mm(Y_BARRERA - RANURA_ANCHO / 2)),
        pcbnew.VECTOR2I(mm(RANURA_X1 - RANURA_X0), mm(RANURA_ANCHO)))
    return [fp.GetReference() for fp in board.GetFootprints()
            if distancia_bbox(_caja_patio(fp), ranura) == 0.0]


def revisar_fuga(board) -> tuple[float, tuple, list, list]:
    """Separacion real entre cobre de red y cobre SELV, pad contra pad.

    LA comprobacion heredada de la v1: no se da por buena porque la ranura este
    dibujada -- la ranura es un hueco en el sustrato y la fuga es por aire y
    por superficie. Se mide el cobre.
    """
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
    return peor, par, pads_red, pads_selv


def revisar_to220_coplanares(board) -> list[str]:
    """Los tres tabs tienen que poder tocar la MISMA pared plana.

    Esta es la puerta de la Fase C, y lo que comprueba no es estetica de
    layout: es si los tres tornillos entran. Un TO-220 atornillado a una pared
    con 1 mm de desnivel respecto de sus vecinos no apoya -- apoya en un canto
    del tab, y la resistencia termica del contacto, que es la mitad de los
    8.5 K/W de la union, se va al doble o al triple. La cuenta de la spec §3.1
    (Tj de U2 en 61 C contra los 101 del disipador individual) se apoya
    entera en que los tres tabs sean coplanares.

    Tres condiciones, y las tres tienen que darse a la vez:

      1. MISMA Y. Si uno esta mas adentro que otro, sus tabs quedan en planos
         distintos y no hay pared que los toque a los tres.
      2. MISMA ROTACION. Uno girado 180 mira su tab al otro lado: se
         atornillaria contra el aire.
      3. LA X QUE DICE EL CHASIS. Los tres agujeros de la pared ya estan
         taladrados en case/cad/params.scad; la placa se pliega a ellos.

    La tolerancia de 0.2 mm no sale de un catalogo: es el orden del propio
    conformado de patas de un TO-220 a mano. Pedir menos seria mentir sobre
    lo que un montaje THT puede repetir.
    """
    males = []
    fps = {r: board.FindFootprintByReference(r) for r in ("U1", "U3", "U2")}
    if any(f is None for f in fps.values()):
        return ["falta alguno de U1/U3/U2 en la placa"]
    ys = {r: f.GetPosition().y / 1e6 for r, f in fps.items()}
    rots = {r: round(f.GetOrientationDegrees()) % 360 for r, f in fps.items()}
    xs = {r: f.GetPosition().x / 1e6 for r, f in fps.items()}

    desnivel = max(ys.values()) - min(ys.values())
    if desnivel > 0.2:
        males.append(f"los tabs de U1/U3/U2 no son coplanares: {desnivel:.2f} mm "
                     f"de desnivel entre {ys} (tolerancia 0.20)")
    if len(set(rots.values())) != 1:
        males.append(f"los TO-220 no comparten orientacion: {rots} -- alguno "
                     f"mira su tab al lado contrario de la pared")
    esperadas = sorted(TO220_X)
    reales = sorted(xs.values())
    for e, r in zip(esperadas, reales):
        if abs(e - r) > 0.2:
            males.append(f"un TO-220 esta en x={r:.2f} y la pared del chasis "
                         f"tiene su agujero en x={e:.2f}: el tornillo no entra")
    # Y ademas: el cuerpo tiene que colgar HACIA FUERA de la placa, o el tab
    # queda dentro y no hay pared que tocar.
    for r, f in fps.items():
        caja = f.GetBoundingBox(False, False)
        if caja.GetTop() / 1e6 > TO220_Y:
            males.append(f"{r} tiene todo su cuerpo dentro de la placa: con "
                         f"rot {rots[r]} el tab no llega a la pared")
    return males


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
    males = ([] if d >= 80
             else [f"lazo rectificador a {d:.0f} mm de la isla ultra (< 80)"])
    # Y la telemetria, que la spec no menciona porque en la v2 no existia.
    # Su umbral es MAS BAJO a proposito, y el motivo hay que decirlo o el
    # numero parece arbitrario: la isla ultra defiende 0.8 uVrms y no puede
    # acercarse; la telemetria mide con un ADC de 16 bits sobre un fondo de
    # escala de 4 V, o sea ~60 uV por cuenta. Tres ordenes de magnitud de
    # diferencia en lo que hay que proteger, tres veces menos distancia.
    #
    # Lo que si comparte con la isla ultra es la razon de estar lejos: sus
    # divisores son de 100k, y un nodo de alta impedancia junto al lazo de
    # rectificacion recoge por capacidad lo que no recogeria uno de baja.
    tele = bbox_de(board, ["U10", "R21", "R22", "R23", "R24", "R25", "R26"])
    dt = distancia_bbox(lazo, tele)
    if dt < 30:
        males.append(f"isla de telemetria a {dt:.0f} mm del lazo rectificador "
                     f"(< 30): sus divisores son de 100k")
    print(f"    lazo->ultra {d:.0f} mm (>=80), lazo->telemetria {dt:.0f} mm (>=30)")
    return males


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
    bom_valores = leer_bom()

    board = pcbnew.NewBoard(PCB)
    contorno(board)
    franja_to220(board)
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
        # F7 (review fase C): el campo Value SI se usa (aunque quede oculto
        # en silk) como fuente de la columna "Val" del pos.csv que exporta
        # kicad-cli -- sin esto quedaba con el nombre de la huella (ver
        # comentario de arriba), no con el valor real del BOM.
        valor = bom_valores.get(ref)
        if valor:
            fp.SetValue(valor)
        board.Add(fp)
        if ref in ("U1", "U2"):
            # F3 (review fase C): pad THT del TO-220-5 stock, 1.275x1.8mm con
            # taladro 1.1mm -> anillo real (1.275-1.1)/2=0.0875mm, por debajo
            # de la capability JLC de 2 capas (0.13mm) -- las 10 violaciones
            # annular_width que fab/README.md y reglas() venian "bendiciendo".
            # Se ensancha el eje CORTO (X) a 1.4mm -> anillo (1.4-1.1)/2=
            # 0.15mm, ya por encima del minimo. El eje largo (Y=1.8) no
            # cambia. El paso entre pads es 1.7mm en X: con pad 1.4mm el
            # hueco pad-a-pad baja de 0.425 a 0.3mm, todavia >> CLEARANCE_MM
            # (0.127) -- no crea clearance nueva contra el pad vecino (son
            # ademas de la misma huella/distinta red, ya se separaban por
            # mucho mas que el minimo).
            for pad in fp.Pads():
                pad.SetSize(pcbnew.VECTOR2I(mm(1.4), mm(1.8)))
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

    # --- F1/F2: textos libres de serigrafia (review fase C, ver TEXTOS_SILK) ---
    for texto, x, y, tam, rot in TEXTOS_SILK:
        texto_silk(board, texto, x, y, tam, rot)
    print(f"textos de serigrafia libres añadidos: {len(TEXTOS_SILK)}")

    # --- ruteo: se CALCULA de los pads ya colocados (ver rutear()) ---
    global TRACKS, VIAS
    _r = rutear(board)
    TRACKS, VIAS = _r.tracks, _r.vias

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

    fuera = revisar_margen(board)
    print(f"piezas que se salen del margen de {MARGEN} mm: {len(fuera)} {fuera}")
    solapes = revisar_solapes(board)
    print(f"piezas que se solapan: {len(solapes)} {solapes[:8]}")
    sobre_ranura = revisar_sobre_ranura(board)
    print(f"piezas montadas sobre la ranura: {len(sobre_ranura)} {sobre_ranura}")
    peor, par, pads_red, pads_selv = revisar_fuga(board)
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
    tabs_mal = revisar_to220_coplanares(board)
    print(f"TO-220 contra la pared del chasis: {len(tabs_mal)} {tabs_mal}")

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
    assert not tabs_mal, f"los TO-220 no casan con la pared del chasis: {tabs_mal}"


if __name__ == "__main__":
    sys.exit(main())
