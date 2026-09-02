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
from functools import cache
from itertools import pairwise
import json
import math
import os
import re
import sys

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power-v3.kicad_pcb")
PRO = os.path.join(DIR, "sam17-power-v3.kicad_pro")
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
NETS_RED = {"L", "L_TR", "N", "PE", "L_SMPS", "N_SMPS"}


@cache
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
    # Orden electrico de izquierda a derecha: entrada y, nada mas entrar, el
    # nodo L se parte en dos -- al limitador de inrush y al toroide por un
    # lado, al filtro de modo comun y la SMPS por el otro. Que L1 pinche en L
    # y no en L_TR es la regla de la spec v2 §7: la SMPS comparte el fusible
    # con el toroide pero NO comparte el limitador, que esta dimensionado
    # para TR1. El fusible es el del IEC C14 de la pared; en esta placa ya no
    # hay ninguno (#130).
    "J3":  (  17.0,  132.0,   0),   # entrada de red: L / N / PE
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
# La via estandar de la placa. Estaban repartidos por el fichero como valores
# por defecto de Ruteo.via() y como literales dentro de reglas(); ahora los
# escribe tambien reglas_proyecto() en la netclass, y tres sitios con el mismo
# numero suelto es como nacio la discrepancia del clearance.
VIA_D, VIA_TALADRO = 0.6, 0.3
# Dos vias no pueden acercarse mas que su cobre: diametro + clearance. El
# taladro pide menos (0.3 + 0.25 de min_hole_clearance = 0.55), asi que manda
# el cobre. _hay_sitio() no lo miraba -- solo esquivaba PADS -- y el fanout de
# GND puso dos vias a 0.5 mm: 1 hole_to_hole en el DRC real.
VIA_A_VIA = VIA_D + CLEARANCE_MM
# Y dos TALADROS tampoco, aunque sean de la misma red: eso ya no es electrico
# sino de taladrado, y por eso revisar_vias() -- que salta el par cuando las
# dos vias comparten red -- no lo veia. El limite se calcula con los dos
# diametros reales mas min_hole_clearance del proyecto.
HOLE_CLEARANCE = 0.25
ANCHO_POT, ANCHO_SEN, ANCHO_RED = 1.0, 0.4, 1.0
# Anchos nuevos de la Tarea 8 (spec sec.6, brief):
ANCHO_ISLA = 0.5     # +13V1/-12V9 locales, ILIM, OUT->ballast, fugas de GND
ANCHO_SET = 0.25     # red SET: "pista corta y fina" (brief, sec.6.1)
ANCHO_KELVIN = 1.5
# Escapar un pin de un DFN de 0.5 mm de paso: 0.2 es lo unico que deja aire al
# pin de arriba Y al de abajo. La pista se ensancha en cuanto sale del chip.
ANCHO_ESCAPE = 0.2   # OUTS->J2 y ballast->J2 de +12V/-12V (brief, >=1.5mm)

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
        """Un tramo. `puntos` mezcla (ref, pin) y (x, y) libremente.

        Los puntos repetidos se caen aqui, y no es cosmetica. Rematar una ruta
        al centro de su pad genera un punto duplicado siempre que el camino ya
        terminara ahi, y un segmento de longitud CERO hace SEGFAULT al
        ZONE_FILLER de KiCad 10 -- sin traceback, sin mensaje, con el proceso
        muerto justo despues de dibujar las pistas (medido 2026-08-21: exit
        139 con 1050 segmentos, de los cuales dos de longitud 0.0000 mm que el
        DRC ya venia listando como `track_dangling`).
        """
        pts = []
        for p in [self._pt(q) for q in puntos]:
            if not pts or abs(p[0] - pts[-1][0]) > 1e-6                     or abs(p[1] - pts[-1][1]) > 1e-6:
                pts.append(p)
        if len(pts) < 2:
            return self
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

    def via(self, p, red=None, ancho=VIA_D, taladro=VIA_TALADRO):
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

    def bajar(self, p, ancho_via=VIA_D):
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
# todo. revisar_estrella() parte tambien los enganches interiores antes de su
# union-find. Las costillas se emiten partidas igualmente: TRACKS conserva la
# topologia explicita y el generador sigue siendo legible sin reconstruirla.
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
# Y cuanto MAS lejos por cada vecino que tenga que escapar por el mismo lado.
# La via a GND_FANOUT pelado le tapaba el pasillo a los suyos: 11 conexiones
# sin camino, y las once eran un pin del MEDIO de una fila de DFN o de MSOP
# (U6.8 SET, U8.9, U9.6/8, U10.1/8...). Un pasillo de escape mide el ancho de
# la pista mas su aire por los dos lados; 1.0 mm cabe de sobra y es redondo.
GND_ESCAPE_PASO = 1.0


def _hay_sitio(board, punto, ref_propia: str, pin_propio: str,
               radio: float = 0.75, vias=()) -> bool:
    """Si una via de 0.6 mm en `punto` deja aire a todo pad que no sea EL SUYO.

    El radio de 0.75 no es holgura de gusto: es el radio de la via (0.3) mas
    0.45 de aire, sobre un minimo de fabricacion de 0.127. Se probo con 1.3 y
    la via de U9.7 no cabia por ningun lado -- en un MSOP de 0.5 mm de paso,
    pedir 1.3 mm a los pines vecinos es pedir que el chip no exista.

    "El suyo" es el pad exacto, no la huella entera. Saltarse la huella
    completa fue el primer intento y salio mal en el sitio obvio: el rabito de
    C29 esquivo a R21 yendose al oeste y aterrizo encima del OTRO pad de C29.

    `vias` son las que ya se han colocado en esta misma pasada. Van aparte de
    los pads porque no estan en la placa todavia -- se estan calculando -- y
    porque su criterio es otro: VIA_A_VIA de centro a centro, no `radio`.
    """
    px, py = punto
    # Las vias ya puestas cuentan igual que un pad. No estaban aqui, y el
    # fanout de GND llego a poner dos a 0.5 mm cuando su cobre pide
    # VIA_A_VIA: una hole_to_hole en el DRC real con esta funcion en verde.
    for vx, vy, *_ in vias:
        if ((vx - px) ** 2 + (vy - py) ** 2) ** 0.5 < VIA_A_VIA:
            return False
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


def _indice_en_fila(fp, pad) -> int:
    """Cuantos pines quedan entre este y el extremo mas cercano de su fila.

    De un pin de ESQUINA se sale a donde sea. De uno del MEDIO no: sus dos
    vecinos tienen que salir por el mismo lado, y lo que se ponga cerca les
    tapa el pasillo. Esto es lo que cuenta cuantos pasillos hay que respetar.

    Devuelve 0 para todo lo que no viva en una fila de tres o mas (un 0805, un
    SOT, un pad pasante): ahi no hay pasillo que respetar y el fanout corto es
    el correcto.
    """
    x, y = pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6
    for clave, propia, otra in ((lambda p: p.GetPosition().y, x,
                                 lambda p: p.GetPosition().x / 1e6),
                                (lambda p: p.GetPosition().x, y,
                                 lambda p: p.GetPosition().y / 1e6)):
        fila = [p for p in fp.Pads()
                if p.GetNumber() and abs(otra(p) - propia) < 0.05]
        if len(fila) < 3:
            continue
        orden = sorted(fila, key=clave)
        i = next(k for k, p in enumerate(orden)
                 if p.GetNumber() == pad.GetNumber())
        return min(i, len(orden) - 1 - i)
    return 0


def _libre_de_pistas(r: Ruteo, a, b, ancho: float, red: str, capa: str) -> bool:
    """Si el tramo `ab` deja aire a todo lo YA trazado en su misma capa.

    `_hay_sitio()` mira pads y vias. Le faltaba esto, y se noto donde tenia que
    notarse: el fan-out de GND aterrizaba encima de una escapada de pin fino
    -- siete vias a 0.05 y 0.10 mm de una pista de otra red -- y su bajante en
    B.Cu cruzaba el buceo de -12V9 por y=46. Ninguna de las dos cosas la ve un
    chequeo que solo conoce pads.
    """
    for net, cp, pts, anc in r.tracks:
        if net == red or cp != capa:
            continue
        minimo = 2.5 if (es_red(net) or es_red(red)) else CLEARANCE_MM
        for i in range(len(pts) - 1):
            if dist_seg(a, b, pts[i], pts[i + 1]) - ancho / 2 - anc / 2 < minimo:
                return False
    return True


def _libre_de_pads(board, a, b, ancho: float, red: str, capa: str) -> bool:
    """Si el tramo `ab` deja aire a todo PAD de otra red en su capa.

    Mismo criterio que revisar_pista_pad(), que es la puerta que lo mide
    despues: dist_seg_rect contra la caja del pad, no contra su centro.

    Va aparte de _hay_sitio() porque la pregunta es otra. _hay_sitio() mira un
    PUNTO -- donde cae una via -- y con eso basta mientras el rabito sea
    corto. Cuando el rabito de GND empezo a girar y a medir milimetros, dejo
    de bastar: el de U10.7 bajaba 2.7 mm por x=90.1 y le pasaba por encima al
    pad de U10.6, que esta en esa misma columna 0.5 mm mas abajo. Los dos
    extremos del tramo estaban libres; el tramo no.
    """
    capas = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pnet = pad.GetNetname()
            if pnet == red or not pad.GetLayerSet().Contains(capas[capa]):
                continue
            bb = pad.GetBoundingBox()
            cx = (bb.GetLeft() + bb.GetRight()) / 2e6
            cy = (bb.GetTop() + bb.GetBottom()) / 2e6
            d = dist_seg_rect(a, b, cx, cy,
                              bb.GetWidth() / 2e6, bb.GetHeight() / 2e6)
            minimo = 2.5 if (es_red(pnet) or es_red(red)) else CLEARANCE_MM
            if d - ancho / 2 < minimo:
                return False
    return True


def _via_gnd_cabe(r: Ruteo, board, tramos, punto, ref: str, pin: str) -> bool:
    """Las TRES cosas que ocupa un fan-out: el rabito, la via y el bajante."""
    if not _hay_sitio(board, punto, ref, pin, vias=r.vias):
        return False
    # La VIA contra las pistas, en las dos capas y con su propio diametro. El
    # rabito de 0.3 mm pasa a 0.45 mm de una escapada vecina -- legal -- y la
    # via de 0.6 mm en el mismo punto no: pide 0.527. Comprobar solo el rabito
    # dejaba cinco vias de GND a 0.05 y 0.10 mm de una pista de otra red.
    for capa in (F, B):
        if not _libre_de_pistas(r, punto, punto, VIA_D, "GND", capa):
            return False
    for a, b, ancho in tramos:
        if not _libre_de_pistas(r, a, b, ancho, "GND", F):
            return False
        if not _libre_de_pads(board, a, b, ancho, "GND", F):
            return False
    cost = min(GND_COSTILLAS, key=lambda c: abs(c - punto[1]))
    return _libre_de_pistas(r, punto, (punto[0], cost), ANCHO_GND, "GND", B)


def _fanout_en_L(r: Ruteo, board, x, y, cx, cy_fp, fo, ref, pin, alto):
    """Sale por el eje del pad, GIRA, y pone la via fuera de la fila.

    El fan-out recto no tiene solucion en U7.9 y la razon es geometrica, no de
    busqueda: con 0.45 mm de paso y una via de 0.6 mm, una via en la banda de
    un pin invade los carriles de sus dos vecinos -- pide 0.527 mm de aire y
    solo hay 0.45. Da igual lo lejos que se vaya: mientras siga en su propia
    y, sigue dentro de las bandas de al lado. Y alargar el rabito recto solo
    empeora, porque cruza mas cosas: a 7.7 mm ya se lleva por delante el canal
    de -12V9 y el tronco de +12V.

    Lo que hace un layouter es girar. Sale al este lo justo para pasar de
    largo las escapadas de sus vecinos, gira perpendicular, y baja de capa ya
    fuera de la fila -- donde una via de 0.6 mm no le quita el sitio a nadie.
    En U7.9 solo cruza la escapada de U7.8, y por eso el recto tiene que
    llegar mas alla de donde ESA termina antes de girar.
    """
    dx, dy = x - cx, y - cy_fp
    eje_x = abs(dx) >= abs(dy)
    for extra in range(6):
        largo = fo + extra * GND_ESCAPE_PASO
        for sgn in ((1, -1) if (dx >= 0 if eje_x else dy >= 0) else (-1, 1)):
            codo = ((x + sgn * largo, y) if eje_x else (x, y + sgn * largo))
            for lado in (1, -1):
                salida = alto / 2 + GND_FANOUT
                fin = ((codo[0], y + lado * salida) if eje_x
                       else (x + lado * salida, codo[1]))
                tramos = [((x, y), codo, 0.3), (codo, fin, 0.3)]
                if _via_gnd_cabe(r, board, tramos, fin, ref, pin):
                    return codo, fin
    return None


def rutear_gnd(r: Ruteo) -> None:
    """El arbol de masa. VA EL ULTIMO de los cuatro bloques escritos a mano.

    No por importancia sino por grados de libertad, que es el criterio que
    ordena a los cuatro: la FORMA del arbol esta fijada por constantes
    (GND_TRONCO_X, GND_COSTILLAS) y lo unico que se adapta es donde cae la via
    de cada pad -- que es justo lo que tiene que adaptarse. Los carriles de
    230 V, los cuatro rieles y las escapadas de los pines finos no pueden
    moverse: los suyos los decide el aislamiento, el Kelvin y el paso del
    encapsulado.

    Cuando iba primero, sus vias se posaban en el pasillo por el que despues
    tenia que salir un pin de MSOP -- siete conflictos medidos, todos del
    mismo tipo. Ahora ve todo lo demas y se aparta.
    """
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
                         min(tam.x, tam.y) / 1e6, _indice_en_fila(fp, p),
                         fp.GetBoundingBox(False, False).GetHeight() / 1e6,
                         fp.GetBoundingBox(False, False).GetWidth() / 1e6))
    assert pads, "la placa no tiene pads de GND"

    enganches: dict[float, set] = {y: set() for y in GND_COSTILLAS}
    for x, y, ref, pin, smd, (cx, cy_fp), lado, idx, alto, ancho_fp in pads:
        xv, yv = x, y
        if smd and lado < GND_PAD_GRANDE:
            # Hacia fuera del cuerpo, por el eje en que el pad esta mas lejos
            # del centro. Pero "fuera del chip" no siempre es "libre": el
            # rabito de C29 salia al este y aterrizaba encima de R21. Se
            # prueban las cuatro direcciones en orden de preferencia y se coge
            # la primera que deje sitio -- y "sitio" significa las TRES cosas
            # que la pieza ocupa: el rabito en F.Cu, la via, y el bajante en
            # B.Cu hasta su costilla. Si ninguna lo deja, revienta aqui en vez
            # de dejarlo pasar al DRC.
            dx, dy = x - cx, y - cy_fp
            eje_x = abs(dx) >= abs(dy)
            # CUATRO DIRECCIONES POR CADA ESCALON, y los escalones crecen.
            # Un escalon fijo no basta: `min(i, n-1-i)` le da el MISMO a dos
            # pines simetricos de la fila, y los dos acaban en la misma x. A
            # dos pistas eso les da igual -- van a distinta y -- pero una via
            # no es una pista: es un circulo de 0.6 mm que pide VIA_A_VIA a
            # todo lo que pase cerca, y a 0.45 mm de paso el vecino no cabe.
            # U7.9 se quedo sin las cuatro direcciones por eso, encajonado
            # entre las escapadas de U7.8 y U7.10 y el canal de -12V9.
            #
            # Se alarga en vez de aflojar. Cada vuelta se va un pasillo mas
            # lejos, con las mismas separaciones -- ninguna regla se toca --
            # y si a los cuatro escalones sigue sin caber, revienta aqui con
            # nombre y apellido en vez de dejarlo pasar al DRC.
            base = GND_FANOUT + idx * GND_ESCAPE_PASO
            camino = None
            for extra in range(5):
                fo = base + extra * GND_ESCAPE_PASO
                orden = ([(fo if dx >= 0 else -fo, 0),
                          (-fo if dx >= 0 else fo, 0),
                          (0, fo), (0, -fo)] if eje_x else
                         [(0, fo if dy >= 0 else -fo),
                          (0, -fo if dy >= 0 else fo),
                          (fo, 0), (-fo, 0)])
                for ddx, ddy in orden:
                    cand = (x + ddx, y + ddy)
                    if _via_gnd_cabe(r, board, [((x, y), cand, 0.3)],
                                     cand, ref, pin):
                        camino = [cand]
                        break
                if camino:
                    break
            if camino is None:
                # el recto no tiene solucion: se prueba en L (ver _fanout_en_L)
                largo_fila = alto if eje_x else ancho_fp
                en_l = _fanout_en_L(r, board, x, y, cx, cy_fp, base,
                                    ref, pin, largo_fila)
                if en_l:
                    camino = list(en_l)
            if camino is None:
                raise AssertionError(
                    f"la via de GND de {ref}.{pin} no cabe: ni recta hasta "
                    f"{base + 4 * GND_ESCAPE_PASO:.1f} mm ni girando")
            xv, yv = camino[-1]
            r.pista(F, [(x, y)] + camino, 0.3, red=(ref, pin))
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

    _podar_vias_redundantes(r)


def _podar_vias_redundantes(r: Ruteo) -> None:
    """Quita las vias de GND que cierran un lazo. sec.14.5: «ni un bucle».

    La FORMA del arbol la fijan las constantes, pero el fanout no. Cuando dos
    pads vecinos escapan hacia el mismo pasillo, sus rabitos de F.Cu se
    tocan; si despues cada uno baja con su propia via a la misma costilla, la
    segunda bajada cierra una espira. Son tres pads de U11 los que lo hacian,
    y ninguna regla lo veia porque el union-find no miraba las vias.

    Quitar una arista que cierra un ciclo NUNCA desconecta: por definicion
    sus dos extremos ya estaban unidos por otro camino. Por eso esto es poda
    y no reruteo, y por eso el ratsnest sigue en cero despues.

    Si el lazo lo cierra una PISTA no hay via que quitar -- eso es el arbol
    mal trazado, no un fanout de mas -- y revienta aqui con los dos puntos.
    """
    _, cierres, _ = grafo_gnd(r.tracks, r.vias)
    if not cierres:
        return
    fuera = []
    for tipo, a, b in cierres:
        if tipo != "via":
            raise AssertionError(
                f"el arbol de masa cierra un lazo por PISTA entre {a} y {b}: "
                "no lo arregla quitar una via, esta mal trazado")
        fuera.append((a[0], a[1]))
    quedan, quitadas = [], 0
    for v in r.vias:
        if v[2].lstrip("/") == "GND" and any(
                abs(v[0] - x) <= 0.001 and abs(v[1] - y) <= 0.001
                for x, y in fuera):
            quitadas += 1
            continue
        quedan.append(v)
    assert quitadas == len(fuera), (
        f"se iban a quitar {len(fuera)} vias de GND y casaron {quitadas}")
    r.vias[:] = quedan
    muertos = _recortar_cobre_muerto(r)
    print(f"  poda del arbol de masa: {quitadas} vias de GND que cerraban "
          f"lazo, y {muertos} tramos de cobre que se quedaron sin servir")


def _malla_gnd(board, tracks, vias, red: str = "GND"):
    """La malla de `red` con sus grados y sus anclajes.

    Un nodo esta ANCLADO si hay un pad de la red encima o si hay una via.
    Lo usan los dos que necesitan saber que cobre lleva a alguna parte: la
    poda del generador, que recorta, y revisar_cobre_muerto(), que asevera.
    """
    _, _, tramos = grafo_gnd(tracks, vias, red)

    anclas = [
        (p.GetPosition().x / 1e6, p.GetPosition().y / 1e6)
        for fp in board.GetFootprints() for p in fp.Pads()
        if p.GetNetname().lstrip("/") == red
    ] + [
        (vx, vy) for vx, vy, vnet, _a, _t in vias
        if vnet.lstrip("/") == red
    ]

    def anclado(nodo):
        return any(abs(nodo[0] - a[0]) <= 0.001 and abs(nodo[1] - a[1]) <= 0.001
                   for a in anclas)

    aristas: dict = {}
    grado: dict = {}
    for idx, capa, nodos, ancho in tramos:
        for p, q in pairwise(nodos):
            clave = (min(p, q), max(p, q), capa)
            if clave in aristas:
                continue
            aristas[clave] = (idx, ancho)
            for n in ((*p, capa), (*q, capa)):
                grado[n] = grado.get(n, 0) + 1
    return tramos, aristas, grado, anclado


def revisar_cobre_muerto(board, red: str = "GND") -> list[str]:
    """Ni un munon: cobre de masa con una punta que no lleva a ningun sitio.

    Electricamente no rompe nada -- el ratsnest sigue en cero -- y por eso
    ninguna otra puerta lo ve. Pero es una antena colgada del arbol de masa,
    y el DRC de KiCad lo llama `track_dangling`. La v3 declara CERO
    infracciones de DRC, y ese DRC es un paso MANUAL del pipeline de fab: si
    la unica puerta que corre sola no lo mira, el dia que alguien no lo corra
    el munon se fabrica.

    Salio de la poda del arbol (sec.14.5): quitar una via redundante deja
    colgando su bajante y su rabito, y hubo que recortarlos. Esta regla es lo
    que asevera que el recorte se hizo.
    """
    _tramos, _aristas, grado, anclado = _malla_gnd(board, TRACKS, VIAS, red)
    return [
        f"cobre de {red} sin servir: punta suelta en "
        f"({n[0]:.4f}, {n[1]:.4f}) de {n[2]}"
        for n, g in sorted(grado.items())
        if g == 1 and not anclado(n[:2])
    ]


def _recortar_cobre_muerto(r: Ruteo, red: str = "GND") -> int:
    """Quita el cobre de `red` que ya no lleva a ninguna parte.

    Al quitar una via se quedan colgando su bajante de B.Cu y el rabito de
    F.Cu que iba a buscarla. No es un fallo electrico -- el ratsnest sigue en
    cero -- pero es una antena, y el DRC de KiCad lo canta como
    `track_dangling`. La v3 declara cero infracciones: un munon de 8 mm en el
    arbol de masa no entra por la puerta de atras.

    Un nodo esta ANCLADO si hay un pad de la red encima o si hay una via que
    sobrevivio. Lo demas se recorta: mientras haya un nodo de grado 1 sin
    anclar, su arista se va. Es iterativo porque quitar un tramo puede dejar
    colgando al de al lado, y lo hace por TRAMOS, no por pistas enteras: el
    rabito vertical de U11 sujeta a tres pads en su primera mitad y solo
    sobra la segunda.
    """
    board = r.board
    tramos, aristas, grado, anclado = _malla_gnd(board, r.tracks, r.vias, red)
    if not tramos:
        return 0
    quitadas: set = set()
    while True:
        hoja = None
        for (a, b, capa), _ in aristas.items():
            if (a, b, capa) in quitadas:
                continue
            for extremo, otro in (((*a, capa), (*b, capa)),
                                  ((*b, capa), (*a, capa))):
                if grado.get(extremo, 0) == 1 and not anclado(extremo[:2]):
                    hoja = (a, b, capa, extremo, otro)
                    break
            if hoja:
                break
        if not hoja:
            break
        a, b, capa, extremo, otro = hoja
        quitadas.add((a, b, capa))
        del aristas[(a, b, capa)]
        grado[extremo] -= 1
        grado[otro] -= 1

    if not quitadas:
        return 0

    # se reescriben SOLO las pistas de la red tocadas, uniendo los tramos que
    # sobreviven en tiradas seguidas para no partir el cobre sin motivo
    vivas: dict = {}
    for idx, capa, nodos, ancho in tramos:
        tirada = []
        for p, q in pairwise(nodos):
            if (min(p, q), max(p, q), capa) in quitadas:
                if len(tirada) > 1:
                    vivas.setdefault(idx, []).append((capa, tirada, ancho))
                tirada = []
            else:
                tirada = (tirada or [p]) + [q]
        if len(tirada) > 1:
            vivas.setdefault(idx, []).append((capa, tirada, ancho))

    nuevas = []
    for idx, (net, capa, pts, ancho) in enumerate(r.tracks):
        if net.lstrip("/") != red:
            nuevas.append((net, capa, pts, ancho))
            continue
        for capa_v, tirada, ancho_v in vivas.get(idx, []):
            nuevas.append((net, capa_v, list(tirada), ancho_v))
    r.tracks[:] = nuevas
    return len(quitadas)


# --- la red, bajo la barrera -----------------------------------------------
# Aqui el reparto de capas NO es el de la placa (F.Cu potencia / B.Cu masa):
# bajo la barrera no hay masa, asi que las dos capas estan libres y se usan las
# dos. La cadena caliente -- entrada, fusible, limitador, primario -- se queda
# entera en F.Cu y de una pieza; el neutro, la tierra y la derivacion a la
# SMPS bajan a B.Cu. No es simetria: es que L tiene que cruzar la franja
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

        F.Cu  123.0  L        (entre la ranura y la fila de pads de 129-135)
        F.Cu  127.5  L        (solo x=17..38, la bajada desde J3)
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
    # De J3 al carril de 123 sin escala: los 7.6 mm de F1 y sus cuatro clips
    # ya no estan en medio.
    r.pista(F, [("J3", "1"), (17.0, 127.5), (38.0, 127.5), (38.0, 123.0),
                (126.0, 123.0)], ANCHO_RED)
    for ref, pin in (("RV1", "1"), ("NT1", "1"), ("L1", "1")):
        x, _ = pad_xy(r.board, ref, pin)
        r.pista(F, [(x, 123.0), (ref, pin)], ANCHO_RED)
    # El 95.5 estaba escrito a mano y era la x del pad 2 CON LA HUELLA VIEJA
    # (paso 7.5). Al corregir NT1 a su paso real de 5.1 el pad se movio a 93.1
    # y la subida arrancaba en el aire. Se pide la x que tenga, como sus dos
    # vecinos de arriba.
    x_nt2, _ = pad_xy(r.board, "NT1", "2")
    r.pista(F, [("NT1", "2"), (x_nt2, 129.0), (115.0, 129.0), ("J4", "2")],
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


def rutear_rieles(r: Ruteo) -> None:
    """Los cuatro rieles: +13V1, -12V9 y las salidas +12V / -12V.

    CARRILES. La isla ultra es una rejilla SMD de 0.5 mm de paso y no se puede
    cruzar: las pistas entran por los dos canales verticales que quedan libres
    entre sus columnas -- x=9.5 (al oeste de la columna 1) y x=30.5 (entre la
    2 y la 3) -- y solo se meten en horizontal en la y exacta de cada pad.
    Los dos canales sirven a las dos mitades de la isla, la de +12 arriba
    (y 13..43) y la de -12 abajo (y 52..85), sin tocarse: entre las dos hay
    8.4 mm de aire.

    Los tramos largos usan las bandas donde no hay pads: y=9 (entre la fila de
    TO-220 y las columnas de soporte), y=21, y=43.5, y=57, y=68, y=79 y y=84.
    """
    # ================= +13V1: de U1 a la mitad de arriba ==================
    r.pista(F, [("U1", "5"), (73.2, 9.0), (90.0, 9.0), ("C17", "1")], ANCHO_POT)
    r.pista(F, [("C17", "1"), (90.0, 21.0), (93.16, 21.0), ("D12", "2")], ANCHO_POT)
    r.pista(F, [(90.0, 21.0), (78.0, 21.0), ("TP7", "1")], ANCHO_SEN,
            red=("TP7", "1"))
    # rama al divisor de ajuste de U1 y a la isla
    r.pista(F, [(73.2, 9.0), (44.0, 9.0)], ANCHO_ISLA, red=("TP7", "1"))
    r.pista(F, [(61.0, 9.0), ("R5", "1")], ANCHO_ISLA, red=("R5", "1"))
    r.pista(F, [(44.0, 9.0), (44.0, 11.0), (9.5, 11.0)], ANCHO_ISLA,
            red=("TP7", "1"))
    r.pista(F, [(30.5, 11.0), (30.5, 40.0)], ANCHO_ISLA, red=("TP7", "1"))
    r.pista(F, [(9.5, 11.0), (9.5, 40.0)], ANCHO_ISLA, red=("TP7", "1"))
    r.pista(F, [(9.5, 40.0), ("C19", "1")], ANCHO_ISLA)
    r.pista(F, [(30.5, 40.0), ("C20", "1")], ANCHO_ISLA)
    for pin in ("1", "2", "3"):
        r.pista(F, [(9.5, pad_xy(r.board, "U4", pin)[1]), ("U4", pin)], ANCHO_ESCAPE)
        r.pista(F, [(30.5, pad_xy(r.board, "U5", pin)[1]), ("U5", pin)], ANCHO_ESCAPE)
    # D8 y D10 cuelgan del canal del medio por su pad oeste
    r.pista(F, [(20.5, 14.0), ("D8", "1")], ANCHO_ISLA)
    r.pista(F, [(20.5, 27.0), ("D10", "1")], ANCHO_ISLA)
    r.pista(F, [(20.5, 14.0), (20.5, 27.0)], ANCHO_ISLA, red=("D8", "1"))
    r.pista(F, [(20.5, 14.0), (20.5, 11.0)], ANCHO_ISLA, red=("D8", "1"))

    # ================= -12V9: de U2 a la mitad de abajo ===================
    r.pista(F, [("U2", "5"), (113.2, 9.0), (166.5, 9.0), ("C18", "2")], ANCHO_POT)
    r.pista(F, [("C18", "2"), (166.5, 21.0), (157.0, 21.0), ("D13", "1")], ANCHO_POT)
    r.pista(F, [(157.0, 21.0), (157.0, 33.0), (158.0, 33.0), ("TP8", "1")],
            ANCHO_SEN, red=("TP8", "1"))
    r.pista(F, [(158.0, 33.0), (158.0, 46.0), (46.0, 46.0)], ANCHO_ISLA,
            red=("TP8", "1"))
    # cruza el tronco de +12V por debajo: dos vias y 6 mm de B.Cu, en el hueco
    # que dejan las costillas 44 y 66 del peine de masa.
    r.via((46.0, 46.0), red=("TP8", "1"))
    r.pista(B, [(46.0, 46.0), (41.5, 46.0)], ANCHO_ISLA, red=("TP8", "1"))
    r.via((41.5, 46.0), red=("TP8", "1"))
    r.pista(F, [(41.5, 46.0), (41.5, 49.0), (9.5, 49.0)], ANCHO_ISLA,
            red=("TP8", "1"))
    r.pista(F, [(30.5, 49.0), (30.5, 79.0)], ANCHO_ISLA, red=("TP8", "1"))
    r.pista(F, [(9.5, 49.0), (9.5, 79.0)], ANCHO_ISLA, red=("TP8", "1"))
    r.pista(F, [(9.5, 79.0), ("C21", "1")], ANCHO_ISLA)
    r.pista(F, [(30.5, 79.0), ("C22", "1")], ANCHO_ISLA)
    # R7 vive al otro lado del tronco de +12V: otro buceo de 13 mm por B.Cu.
    r.pista(F, [(70.0, 46.0), (70.0, 47.0)], ANCHO_ISLA, red=("TP8", "1"))
    r.via((70.0, 47.0), red=("TP8", "1"))
    r.pista(B, [(70.0, 47.0), (70.0, 59.5)], ANCHO_ISLA, red=("TP8", "1"))
    r.via((70.0, 59.5), red=("TP8", "1"))
    r.pista(F, [(70.0, 59.5), ("R7", "2")], ANCHO_ISLA)
    for pin in ("1", "2", "3"):
        r.pista(F, [(9.5, pad_xy(r.board, "U6", pin)[1]), ("U6", pin)], ANCHO_ESCAPE)
        r.pista(F, [(30.5, pad_xy(r.board, "U7", pin)[1]), ("U7", pin)], ANCHO_ESCAPE)
    # El EP de U6/U7 tambien es -12V9, y hasta ahora salia 2.5 mm hacia el sur
    # y se quedaba ahi: un munon que no llegaba a ningun sitio, con la entrada
    # del chip conectada solo por los pines 1-3. El DRC real lo cantaba
    # ("missing connection" entre la pista de -12V9 y el pad 13); las puertas
    # propias no, porque miden separacion y no continuidad. Ahora baja hasta
    # y=55.5 -- por debajo de la fila de pines, que acaba en 54.25, y muy por
    # encima de R13/R14 en 59.5 -- y de ahi va al canal vertical del que
    # cuelga esa mitad de la isla.
    for u, canal in (("U6", 9.5), ("U7", 30.5)):
        x, y = pad_xy(r.board, u, "13")
        r.pista(F, [(x, y), (x, 55.5), (canal, 55.5)], 0.4, red=(u, "13"))
    # D9 y D11 cuelgan del canal del medio por su pad ESTE
    r.pista(F, [(30.5, 53.0), ("D9", "2")], ANCHO_ISLA)
    r.pista(F, [(30.5, 66.0), ("D11", "2")], ANCHO_ISLA)

    # ================= +12V: de los ballast al shunt ======================
    # LAS CUATRO ESCAPADAS DE OUTS NO ESTAN, y no por descuido. El pin OUTS de
    # un LT3045 es la realimentacion Kelvin: sale de un DFN de 0.5 mm de paso y
    # su vecino inmediato es el pin de GND, que ademas necesita su propia via.
    # Una via de 0.6 mm y una escapada de 0.2 a 0.5 mm de distancia no dejan
    # los 0.127 de aire que exige la fabricacion, se pongan como se pongan --
    # medido en las cuatro. Se resuelven con la rejilla de la isla en la mano y
    # es lo primero de la tanda que viene, no un remate.
    r.pista(F, [(19.5, 20.0), (19.5, 33.5), ("R15", "2")], ANCHO_ISLA,
            red=("R15", "2"))
    r.pista(F, [(41.5, 20.0), (41.5, 33.5), ("R16", "2")], ANCHO_ISLA,
            red=("R16", "2"))
    r.pista(F, [("D10", "2"), (27.0, 30.0), (19.5, 30.0)], ANCHO_ISLA)
    r.pista(F, [("R16", "2"), (43.5, 33.5), (43.5, 85.0), (28.54, 85.0),
                ("R19", "1")], ANCHO_KELVIN)
    r.pista(F, [(43.5, 85.0), (45.5, 85.0), (45.5, 87.0), ("U8", "10")],
            ANCHO_ESCAPE, red=("U8", "10"))
    r.pista(F, [(43.5, 57.0), (112.0, 57.0), (112.0, 50.0), ("TP3", "1")],
            ANCHO_SEN, red=("TP3", "1"))
    r.pista(F, [(78.0, 57.0), ("R1", "1")], ANCHO_ISLA)

    # ================= -12V: de los ballast a J2 ==========================
    r.pista(F, [(19.5, 58.0), (19.5, 72.5), ("R17", "2")], ANCHO_ISLA,
            red=("R17", "2"))
    r.pista(F, [(41.5, 58.0), (41.5, 72.5), ("R18", "2")], ANCHO_ISLA,
            red=("R18", "2"))
    r.pista(F, [(19.5, 72.5), (19.5, 86.0), (15.0, 86.0), ("J2", "1")],
            ANCHO_KELVIN, red=("J2", "1"))
    r.pista(F, [("R18", "2"), (41.5, 72.5), (41.5, 76.0)], ANCHO_ISLA)
    r.via((41.5, 76.0), red=("R18", "2"))
    r.pista(B, [(41.5, 76.0), (25.0, 76.0)], ANCHO_ISLA, red=("R18", "2"))
    r.via((25.0, 76.0), red=("R18", "2"))
    r.pista(F, [(25.0, 76.0), (19.5, 76.0)], ANCHO_ISLA, red=("R18", "2"))
    r.pista(F, [("D11", "1"), (21.5, 66.0), (21.5, 76.0)], ANCHO_ISLA)
    r.pista(F, [(47.0, 68.0), (47.0, 84.0), (56.91, 84.0), ("R21", "2")],
            ANCHO_ISLA, red=("R21", "2"))
    r.pista(F, [(41.5, 68.0), (41.5, 72.5)], ANCHO_ISLA, red=("D4", "1"))
    r.via((41.5, 68.0), red=("D4", "1"))
    r.pista(B, [(41.5, 68.0), (47.0, 68.0)], ANCHO_ISLA, red=("D4", "1"))
    r.via((47.0, 68.0), red=("D4", "1"))
    r.pista(F, [(47.0, 68.0), (98.0, 68.0), (98.0, 60.0)], ANCHO_ISLA,
            red=("D4", "1"))
    # ultimo cruce de la tanda: el carril de +12V hacia TP3 va por y=57 y hay
    # que pasarle por debajo. Seis milimetros de B.Cu entre las costillas 44 y
    # 66 del peine, dos vias, y a seguir.
    r.via((98.0, 60.0), red=("D4", "1"))
    r.pista(B, [(98.0, 60.0), (98.0, 54.0)], ANCHO_ISLA, red=("D4", "1"))
    r.via((98.0, 54.0), red=("D4", "1"))
    r.pista(F, [(98.0, 54.0), (98.0, 50.0), ("D4", "1")], ANCHO_ISLA)
    r.pista(F, [(120.0, 68.0), (120.0, 50.0), ("TP4", "1")], ANCHO_SEN,
            red=("TP4", "1"))
    r.pista(F, [(98.0, 68.0), (120.0, 68.0)], ANCHO_ISLA, red=("TP4", "1"))


# ============================================================================
# Lo que queda: el laberinto de hardware/tools/maze.py
# ============================================================================
# HASTA AQUI TODO SE HA ESCRITO A MANO, y eso NO es una etapa que el laberinto
# venga a sustituir. Las cuatro cosas de arriba -- el arbol de GND, la franja
# de red, los cuatro rieles y el Kelvin de OUTS -- se rutean a mano porque su
# forma ES el diseno: un plano de masa en vez de un arbol mete una espira de
# 100 Hz, y el punto exacto donde se suelda el sense de un LT3045 decide que
# tension queda regulada. "El camino mas corto" es la respuesta equivocada a
# las dos preguntas.
#
# Lo que queda despues son 126 conexiones de otra naturaleza: I2C, los tres
# divisores de telemetria, +3V3, GNDD, las SET/ILIM/OUT locales de la isla, el
# lazo de rectificacion y el riel de +5V. Ahi lo que hace falta es no cruzarse
# con nada, y eso es exactamente lo que un BFS de Lee hace mejor que yo.
#
# El ruteador ya estaba EN EL REPO. `hardware/tools/maze.py` se escribio para
# el modulo 2 ("se quedaron 17 redes al aire"), esta probado con su propia
# demo, y ni la v1 ni la v2 ni esta version lo habian importado nunca.
#
# Dos numeros decidieron como se usa, los dos medidos y no supuestos:
#
#   * PASO 0.1 mm, no 0.25. Con 0.25 el riel de +5V dejo 5 pines al aire, y
#     los cinco eran el pin del MEDIO de un MSOP: para escapar de un pad de
#     0.5 mm de paso hay que salir recto hasta pasar a los vecinos, y una
#     rejilla de 0.25 no tiene ninguna celda en ese pasillo. Con 0.1 salieron
#     las 25 conexiones de +5V en 25 s.
#   * `via_ok` en O(1). La primera version preguntaba a _hay_sitio(), que
#     recorre los 310 pads de la placa -- y el BFS la llama una vez por cada
#     nodo que se plantea cambiar de capa. No termino en diez minutos. La
#     rejilla ya sabia responder eso: una clase de ancho mas, "via", pintada
#     con VIA_D, y su mapa ES el mapa de donde cabe una via.
sys.path.insert(0, os.path.join(DIR, "..", "..", "..", "tools"))
import maze                                                       # noqa: E402

PASO_REJILLA = 0.1

# Las clases de ancho de la rejilla. No son los anchos de dibujo (esos siguen
# siendo ANCHO_*): son los CALIBRES que el laberinto sabe reservar, y cada red
# pendiente se pide en uno de ellos. Un mapa por calibre es lo que permite que
# el escape de un DFN se mida con 0.2 mm y el lazo de rectificacion con 1.0,
# en vez de bloquear el TSSOP entero con el margen del riel mas gordo.
CALIBRES = {"fina": ANCHO_ESCAPE, "media": ANCHO_SEN, "pot": ANCHO_POT,
            "ancha": ANCHO_KELVIN, "via": VIA_D}

# El sur es de la red. Ningun pad SELV baja de y=114 (J8, J5 y los tres test
# points de telemetria son los ultimos), y el carril de 230 V mas al norte va
# por y=123: FUGA_MIN por debajo de el son 117. El laberinto no sabe de
# aislamiento -- veria una autopista libre y la usaria de atajo -- asi que la
# franja se le pinta como pared. revisar_fuga() mide pads, no pistas; esto es
# lo que hace que no le haga falta.
Y_SELV_MAX = 117.0

# Que calibre pide cada red, y en que ORDEN se rutean. El orden importa: quien
# va primero coge el camino recto. Primero la potencia (el lazo de
# rectificacion, que ademas quiere area minima), luego los rieles, y al final
# las senales, que son las que mejor toleran dar un rodeo.
PENDIENTES = [
    # el lazo de rectificacion: J1 -> BR1 -> los cuatro bulk. Mismo calibre
    # que le dio la v2 a estas cuatro redes.
    ("/SEC_A", "pot"), ("/SEC_B", "pot"),
    ("/VRAW+", "pot"), ("/VRAW-", "pot"),
    # la salida de +12 V pasada por el shunt del INA226 hacia J2
    ("/+12V_BUS", "ancha"),
    # Y EL KELVIN DE OUTS. De estas dos redes solo falta eso: el tronco
    # de potencia (ballast -> shunt -> J2) ya esta escrito a mano en
    # rutear_rieles(), con sus munones esperando en (19.5,20) y
    # (41.5,20) para +12V y (19.5,58) y (41.5,58) para -12V. El pin
    # OUTS de un LT3045 no lleva corriente -- es realimentacion -- asi
    # que va con calibre de escape, que ademas es el unico que sale de
    # un DFN de 0.5 mm de paso.
    ("+12V", "fina"), ("-12V", "fina"),
    # el riel de la telemetria y del modulo 2
    ("+5V", "media"), ("/+5V_M2", "media"),
    # las salidas locales de los cuatro reguladores y su ballast
    ("Net-(U4-OUT)", "fina"), ("Net-(U5-OUT)", "fina"),
    ("Net-(C25-Pad1)", "fina"), ("Net-(C26-Pad1)", "fina"),
    # la realimentacion: SET va corta y fina (brief sec.6.1), ILIM tambien
    ("Net-(U4-SET)", "fina"), ("Net-(U6-SET)", "fina"),
    ("Net-(U4-ILIM)", "fina"), ("Net-(U5-ILIM)", "fina"),
    ("Net-(U6-ILIM)", "fina"), ("Net-(U7-ILIM)", "fina"),
    # el ajuste de los dos pre-reguladores
    ("Net-(U1-ADJ)", "fina"), ("Net-(R5-Pad2)", "fina"),
    ("Net-(U2-ADJ)", "fina"), ("Net-(R7-Pad1)", "fina"),
    # los ballast de la carga minima
    ("Net-(D3-A)", "fina"), ("Net-(D4-A)", "fina"), ("Net-(D6-A)", "fina"),
    # La isla de referencia. La zona de ISLA_REF la resolvia sola mientras la
    # placa no tenia pistas; con la isla ultra ruteada encima, la zona queda
    # partida en trozos y sus siete pads en cinco grupos sin unir -- seis
    # "missing connection" y un isolated_copper en el DRC real. La zona se
    # queda (es el cobre que da la referencia), pero la CONTINUIDAD se cablea:
    # una zona partida por una pista es invisible para todas las puertas de
    # separacion, que es justamente lo que este repo dice que no vale.
    ("/GNDREF", "fina"),
    # los tres divisores de telemetria
    ("/TAP_VRAW+", "fina"), ("/TAP_VRAW-", "fina"), ("/TAP_-12V", "fina"),
    # el lado aislado de la barrera I2C, y el I2C de los dos dominios
    ("+3V3", "fina"), ("GNDD", "fina"),
    ("/SDA_A", "fina"), ("/SCL_A", "fina"),
    ("/SDA_D", "fina"), ("/SCL_D", "fina"),
]

CAPA_N = {F: 0, B: 1}
CAPA_NOM = {0: F, 1: B}


def _calibre_util(pad, pedido: str) -> str:
    """El calibre que de verdad cabe: el de la red, o el que admita el pad.

    Una pista no puede salir mas ancha que el pad del que sale. Suena obvio y
    no lo era: `/+12V_BUS` pide "ancha" (1.5 mm) porque lleva la corriente del
    bus, y dos de sus cuatro pads son pines IN- de un INA226 en MSOP, de
    0.3 mm de lado. La red entera se quedaba sin rutear.

    Y los dos pines son SENSE: no llevan corriente. Lo que hacia falta no era
    una excepcion escrita a mano para ellos sino esta regla, que es geometria
    y no preferencia -- el tramo que si lleva la corriente (R19 -> J2, pads
    grandes los dos) conserva su 1.5 mm sin que nadie lo declare.
    """
    lado = min(pad[3] - pad[1], pad[4] - pad[2])
    tope = min(CALIBRES[pedido], lado)
    cabe = [c for c in CALIBRES if c != "via" and CALIBRES[c] <= tope]
    assert cabe, f"ni el calibre mas fino cabe en {pad[0]} ({lado:.2f} mm)"
    return max(cabe, key=lambda c: CALIBRES[c])


def escapar_pines_finos(r: Ruteo) -> dict:
    """Saca de la fila, ANTES de rutear nada, cada pin que este atrapado.

    Es el fan-out de `rutear_gnd` aplicado al resto de las redes, y esta aqui
    por lo mismo: en una fila de pines de 0.45 o 0.5 mm de paso, el que sale
    primero coge el pasillo recto y deja a los de dentro sin salida. GND ya lo
    resolvia escalonando su via -- cuantos mas vecinos tenga que dejar pasar,
    mas lejos se va antes de bajar de capa -- y las demas redes no, porque las
    ruteaba el laberinto una a una, cada una buscando su camino mas corto sin
    saber que le tapaba el paso a la siguiente.

    Se veia como siete redes "sin camino" que no compartian nada excepto el
    sitio donde se atascaban: U8.4, U9.9, U10.4. Los tres son el pin del medio
    de una fila cuyos vecinos ya estaban ruteados.

    La escapada es recta, perpendicular a la fila, hacia fuera del cuerpo del
    chip, y su longitud es la misma formula que la del fan-out de GND: cada
    indice, un pasillo mas. Asi dos pines de la misma fila no giran nunca a la
    misma x, y el laberinto se encuentra los extremos ya en campo abierto.

    Los pines de EXTREMO no la necesitan (indice 0): a esos no hay nadie que
    dejar pasar. Y las redes que no rutea el laberinto tampoco -- +13V1 y
    -12V9 entran a la isla por sus dos canales verticales, escritos a mano.
    """
    board = r.board
    pendientes = {red for red, _ in PENDIENTES}
    escapes: dict = {}
    for fp in board.GetFootprints():
        cx = fp.GetPosition().x / 1e6
        cy = fp.GetPosition().y / 1e6
        for p in fp.Pads():
            if p.GetNetname() not in pendientes:
                continue
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            idx = _indice_en_fila(fp, p)
            if not idx:
                continue
            x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            largo = GND_FANOUT + idx * GND_ESCAPE_PASO
            dx, dy = x - cx, y - cy
            if abs(dx) >= abs(dy):
                destino = (x + (largo if dx >= 0 else -largo), y)
            else:
                destino = (x, y + (largo if dy >= 0 else -largo))
            r.pista(F, [(x, y), destino], ANCHO_ESCAPE,
                    red=(fp.GetReference(), p.GetNumber()))
            escapes[f"{fp.GetReference()}.{p.GetNumber()}"] = destino
    return escapes


def _pads_por_red(board) -> dict:
    """(red) -> [(nombre, x0, y0, x1, y1, capas, cx, cy)], en mm.

    Las `unconnected-*` que KiCad inventa para un pin sin conectar quedan
    fuera a proposito: no son una red, son la ausencia de una.
    """
    porred: dict = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            red = p.GetNetname()
            if not red or red.startswith("unconnected-"):
                continue
            ls = p.GetLayerSet()
            capas = [c for c, cu in ((0, pcbnew.F_Cu), (1, pcbnew.B_Cu))
                     if ls.Contains(cu)]
            if not capas:            # sub-pad de solo pasta: no es cobre
                continue
            bb = p.GetBoundingBox()
            porred.setdefault(red, []).append(
                (f"{fp.GetReference()}.{p.GetNumber()}",
                 bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                 bb.GetRight() / 1e6, bb.GetBottom() / 1e6, capas,
                 (bb.GetLeft() + bb.GetRight()) / 2e6,
                 (bb.GetTop() + bb.GetBottom()) / 2e6))
    return porred


def _sembrar_pista(rej, red_id: int, a, b, ancho: float, capa: int) -> None:
    """Como rej.pista(), pero con el ancho REAL y no con el calibre mas cercano.

    rej.pista() pide una CLASE, y la clase mas cercana por arriba a un rabito
    de GND de 0.3 mm es "media", de 0.4. Esos 0.05 mm de radio inventado
    tapaban la unica celda por la que sale el pin OUTS de un LT3045: el
    pasillo entre dos pines de 0.5 mm de paso mide una celda de alto y no
    admite margen de cortesia. El aire de una pista se mide con su ancho, que
    aqui se conoce, no con el del calibre en el que cabria.
    """
    x0, x1 = min(a[0], b[0]), max(a[0], b[0])
    y0, y1 = min(a[1], b[1]), max(a[1], b[1])
    for clase, w in rej.anchos.items():
        rej._pintar(red_id, x0, y0, x1, y1,
                    rej.cl + w / 2 + ancho / 2, clase, capa)


def _sembrar(rej, board, r: Ruteo, dar_id) -> None:
    """Pinta en la rejilla todo lo que ya ocupa cobre: pads, pistas y vias."""
    for fp in board.GetFootprints():
        for p in fp.Pads():
            ls = p.GetLayerSet()
            capas = [c for c, cu in ((0, pcbnew.F_Cu), (1, pcbnew.B_Cu))
                     if ls.Contains(cu)]
            if not capas:
                continue
            bb = p.GetBoundingBox()
            # Un pin sin red no comparte cobre con nadie: cada uno es su
            # propio obstaculo, no todos el mismo.
            red = p.GetNetname() or f"__{fp.GetReference()}.{p.GetNumber()}"
            rej.pad(dar_id(red), bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                    bb.GetRight() / 1e6, bb.GetBottom() / 1e6, capas=capas)
    for red, capa, pts, ancho in r.tracks:
        for i in range(len(pts) - 1):
            _sembrar_pista(rej, dar_id(red), pts[i], pts[i + 1],
                           ancho, CAPA_N[capa])
    for x, y, red, ancho, _t in r.vias:
        rej.via(dar_id(red), x, y, ancho)
    # la franja de red, como pared: un id que no es de nadie
    pared = dar_id("__FRANJA_DE_RED")
    for capa in (0, 1):
        for cal in CALIBRES:
            rej._pintar(pared, 0.0, Y_SELV_MAX, W, H, 0.0, cal, capa)


def _celdas_de_pista(rej, a, b, capa) -> set:
    """Las celdas del EJE de un tramo -- lo que ya esta conectado de una red.

    `rej.pista()` pinta el tramo ENGORDADO, que es lo que hay que esquivar;
    para arrancar un BFS hace falta lo contrario, el cobre en si. Muestreo
    denso en vez de Bresenham: los tramos son de milimetros y el paso es
    0.1 mm, asi que sobran puntos y sobra sencillez.
    """
    (ax, ay), (bx, by) = a, b
    largo = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    n = max(2, int(largo / (rej.paso / 2)) + 1)
    out = set()
    for i in range(n):
        t = i / (n - 1)
        ix, iy = rej.a_celda(ax + (bx - ax) * t, ay + (by - ay) * t)
        if 0 <= ix < rej.nx and 0 <= iy < rej.ny:
            out.add(capa * rej.n + iy * rej.nx + ix)
    return out


def _trazar(r: Ruteo, rej, camino, ancho: float, pad, fin,
            inicio=None, capas_ini=(0,)) -> None:
    """Del camino en celdas a tramos y vias de verdad.

    Un cambio de capa nunca sobrevive a comprimir() -- exige que los tres
    puntos compartan capa -- asi que las transiciones estan todas, y cada una
    es una via en el punto que las dos capas comparten.
    """
    ref, _, pin = pad[0].partition(".")
    puntos = [(rej.a_mm(ix, iy), capa)
              for ix, iy, capa in maze.comprimir(camino)]
    tramos: list = []
    for pt, capa in puntos:
        if tramos and tramos[-1][0] == capa:
            tramos[-1][1].append(pt)
        else:
            tramos.append((capa, [pt]))
    # El ultimo punto cae DENTRO del pad de destino, no en su centro
    # (celdas_rect es estricta a proposito, y por un motivo escrito: redondear
    # hacia fuera dejaba las pistas naciendo a un paso de rejilla del cobre y
    # KiCad las daba por desconectadas). Se remata al centro, que es cobre
    # propio y por tanto siempre legal.
    if tramos[-1][1][-1] != fin:
        tramos[-1][1].append(fin)
    # Y EL PRIMERO, cuando nace en un pad. celdas_rect trabaja sobre el
    # bounding box, y la esquina del bounding box de un pad REDONDO no es
    # cobre: la pista de Net-(R7-Pad1) nacia en (60.2, 60.2), que es
    # exactamente la esquina del pad de R7, y KiCad la daba por desconectada
    # con toda la razon. Rematar al centro es siempre legal -- de la esquina
    # al centro se va por dentro del propio pad.
    # ...pero solo si ese tramo esta en una capa donde el pad TIENE cobre. El
    # primer punto del camino puede caer en B.Cu -- el cobre ya trazado de la
    # red esta en las dos caras -- y si ademas cae dentro del bounding box de
    # un pad SMD, rematar al centro creaba un tramo de B.Cu que nacia en un
    # pad que solo existe en F.Cu: tres rabitos de 0.5 mm colgando, uno por
    # cada vez que paso.
    if (inicio is not None and tramos[0][1][0] != inicio
            and tramos[0][0] in capas_ini):
        tramos[0][1].insert(0, inicio)
    for i, (capa, pts) in enumerate(tramos):
        if len(pts) > 1:
            r.pista(CAPA_NOM[capa], pts, ancho, red=(ref, pin))
        if i + 1 < len(tramos):
            r.via(pts[-1], red=(ref, pin))


def _islas_de(r: Ruteo, red: str, saltar: set) -> list:
    """Los trozos de cobre INDEPENDIENTES que una red ya tiene trazados.

    Una red a medio rutear a mano puede ser varias islas, y `+12V` lo era: el
    canal de x=19.5 con R15.2 y D10.2 por un lado, y el de x=41.5 con R16.2,
    el shunt y TP3 por otro, sin nada que los una. Tratar todo su cobre como
    un solo "ya conectado" hacia que el laberinto no viera nada que hacer --
    cada pad tocaba ALGUN cobre de su red -- y las dos islas se quedaban
    separadas con las puertas propias en verde y el DRC diciendo "missing
    connection between items" entre dos pistas de +12V.

    Union-find sobre los extremos, mas los puntos que caen SOBRE otro tramo:
    en el ruteo escrito a mano una derivacion nace a mitad de camino y no en
    un extremo, y sin esa segunda parte cada derivacion seria su propia isla.

    `saltar` son las escapadas de pin fino, que no son cobre util todavia:
    llevan del pad a un munon de 2.7 mm que aun no va a ningun sitio.
    """
    tramos = [(pts, capa) for rd, capa, pts, _a in r.tracks
              if rd == red and not (len(pts) == 2 and tuple(pts[1]) in saltar)]
    padre: dict = {}

    def raiz(n):
        padre.setdefault(n, n)
        while padre[n] != n:
            padre[n] = padre[padre[n]]
            n = padre[n]
        return n

    def unir(a, b):
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[ra] = rb

    for i, (pts, _c) in enumerate(tramos):
        for a, b in zip(pts, pts[1:]):
            unir((i, round(a[0], 3), round(a[1], 3)),
                 (i, round(b[0], 3), round(b[1], 3)))
    # y ahora entre tramos: un punto de uno que toque a otro
    for i, (pts, _ci) in enumerate(tramos):
        for p in pts:
            for j, (qts, _cj) in enumerate(tramos):
                if i == j:
                    continue
                for a, b in zip(qts, qts[1:]):
                    if dist_seg(a, b, p, p) < 0.01:
                        unir((i, round(p[0], 3), round(p[1], 3)),
                             (j, round(a[0], 3), round(a[1], 3)))
                        break
    grupos: dict = {}
    for i, (pts, capa) in enumerate(tramos):
        k = raiz((i, round(pts[0][0], 3), round(pts[0][1], 3)))
        grupos.setdefault(k, []).append((pts, capa))
    return list(grupos.values())


def rutear_resto(r: Ruteo, escapes: dict) -> list[str]:
    """Las redes de PENDIENTES, con el laberinto. Devuelve las que no cerraron.

    Una red no empieza de cero: arranca de TODO lo que ya tiene trazado a
    mano, y de ahi cuelga los pads que le falten. Es lo que hace que las
    cuatro escapadas de OUTS acaben en el munon que rutear_rieles() dejo
    esperando en (19.5, 20) y sus tres simetricos -- el camino mas corto desde
    el pin hasta el cobre de su propia red es justo ese, y el punto de sensado
    sigue decidido a mano y no por un BFS.
    """
    board = r.board
    ids: dict = {}

    def dar_id(nombre: str) -> int:
        return ids.setdefault(nombre, len(ids) + 1)

    rej = maze.Rejilla(W, H, PASO_REJILLA, CLEARANCE_MM, CALIBRES)
    _sembrar(rej, board, r, dar_id)
    porred = _pads_por_red(board)

    mv = [rej.mapa["via"][0], rej.mapa["via"][1]]
    dv = [rej.red_de["via"][0], rej.red_de["via"][1]]
    actual = [0]

    def via_ok(punto) -> bool:
        ix, iy = rej.a_celda(*punto)
        k = iy * rej.nx + ix
        return all(not m[k] or d.get(k) == actual[0] for m, d in zip(mv, dv))

    def punta(p):
        # Si el pin tiene escapada preparada, el laberinto empieza y acaba en
        # SU EXTREMO, no en el pad: hasta ahi ya esta cableado.
        return escapes.get(p[0]) or (p[6], p[7])

    def celdas(p) -> set:
        if p[0] in escapes:
            return {rej.nodo(*escapes[p[0]], 0)}
        s: set = set()
        for c in p[5]:
            s |= rej.celdas_rect(p[1], p[2], p[3], p[4], c)
        return s

    sin_cerrar = []
    for red, calibre in PENDIENTES:
        pads = porred.get(red)
        assert pads, f"PENDIENTES nombra una red que no existe: {red}"
        rid = dar_id(red)
        actual[0] = rid

        puntas = {tuple(v) for v in escapes.values()}
        islas = _islas_de(r, red, puntas)

        def celdas_isla(isla) -> set:
            out: set = set()
            for pts, capa in isla:
                for i in range(len(pts) - 1):
                    out |= _celdas_de_pista(rej, pts[i], pts[i + 1],
                                            CAPA_N[capa])
            return out

        # La isla mas grande es el tronco; las demas son trozos que hay que
        # engancharle. Los pads de un trozo NO cuentan como resueltos: si
        # contaran, el laberinto no tendria nada que hacer y los trozos se
        # quedarian separados (ver _islas_de).
        celdas_por_isla = [celdas_isla(i) for i in islas]
        troncal = max(range(len(islas)), key=lambda k: len(celdas_por_isla[k]),
                      default=None)
        conectado: set = set(celdas_por_isla[troncal]) if islas else set()
        sueltas = [c for k, c in enumerate(celdas_por_isla) if k != troncal]
        for x, y, rd, _an, _t in r.vias:
            if rd != red:
                continue
            ix, iy = rej.a_celda(x, y)
            nodos = {c * rej.n + iy * rej.nx + ix for c in (0, 1)}
            if nodos & conectado:
                conectado |= nodos

        faltan = list(pads)
        hechos = []
        # los pads que YA toca el cobre trazado a mano no se rutean otra vez
        for p in list(faltan):
            if celdas(p) & conectado:
                faltan.remove(p)
                hechos.append(p)
        if not hechos and faltan:
            # Red virgen: se ancla en el pad MAS GRANDE, no en el primero de
            # la lista. Anclar en el primero salio caro: a `/TAP_VRAW+` le
            # tocaba un pin de MSOP, y de un pin de MSOP no siempre se sale --
            # con lo que fallaba el BFS del ancla y con el la red entera, tres
            # pads que no tenian ningun problema. Un 0805 o un test point
            # tienen sitio alrededor por construccion.
            sueltos = [p for p in faltan if p[0] not in escapes] or faltan
            p0 = max(sueltos, key=lambda p: (p[3] - p[1]) * (p[4] - p[2]))
            faltan.remove(p0)
            conectado |= celdas(p0)
            hechos.append(p0)

        # Dos vueltas. Un pad al que no se llega con la red a medio tender
        # puede tener camino cuando ya esta entera: el BFS busca hasta CUALQUIER
        # punto del cobre de su red, y ese cobre crece en cada iteracion. La
        # segunda vuelta es la unica que ve el arbol completo.
        fallidos: list = []
        segunda: set = set()
        while faltan or fallidos:
            if not faltan:
                if not hechos or len(fallidos) == len(pads):
                    break
                faltan, fallidos = fallidos, []
                if not faltan:
                    break
            # el mas cercano a lo ya conectado. Greedy, no optimo: el arbol de
            # Steiner minimo es NP-duro y esto es una PCB, no un teorema.
            obj = min(faltan, key=lambda p: min((p[6] - h[6]) ** 2
                                                + (p[7] - h[7]) ** 2
                                                for h in hechos))
            faltan.remove(obj)
            cal = _calibre_util(obj, calibre)
            camino = rej.buscar(rid, cal, conectado, celdas(obj),
                                via_ok, capas=(0, 1))
            if camino is None:
                if obj[0] in segunda:
                    sin_cerrar.append(f"{red}: sin camino hasta {obj[0]} "
                                      f"(calibre {cal})")
                else:
                    segunda.add(obj[0])
                    fallidos.append(obj)
                continue
            n_antes = len(r.tracks)
            # de que pad nace el camino: el que contenga su primer punto
            x0, y0 = rej.a_mm(camino[0][0], camino[0][1])
            nace_en = next((h for h in hechos
                            if h[1] - 0.01 <= x0 <= h[3] + 0.01
                            and h[2] - 0.01 <= y0 <= h[4] + 0.01), None)
            _trazar(r, rej, camino, CALIBRES[cal], obj, punta(obj),
                    punta(nace_en) if nace_en else None,
                    tuple(nace_en[5]) if nace_en else ())
            # lo recien trazado pasa a ser obstaculo para el resto de redes,
            # y origen para el resto de pads de esta
            for rd, capa, pts, anc in r.tracks[n_antes:]:
                for i in range(len(pts) - 1):
                    _sembrar_pista(rej, rid, pts[i], pts[i + 1], anc,
                                   CAPA_N[capa])
            for x, y, rd, anc, _t in r.vias:
                if rd == red:
                    rej.via(rid, x, y, anc)
            conectado |= {c * rej.n + iy * rej.nx + ix
                          for ix, iy, c in camino}
            for k, cel in enumerate(sueltas):
                if cel & conectado:
                    conectado |= cel
                    sueltas[k] = set()
            hechos.append(obj)
    return sin_cerrar


def rutear(board) -> Ruteo:
    """Todas las pistas de la placa, en dos mitades y por ese orden.

    EL PRIMER INTENTO ESTA MEDIDO Y DESCARTADO, y el numero fue el argumento:
    ruteando en L sobre F.Cu, con corredores elegidos a ojo, TRES de los diez
    grupos (red, lazo de rectificacion y los dos rieles del pre-regulador,
    77 tramos) dieron **54 cruces y 28 pistas sobre pads ajenos**. No estaba
    mal escrito: es que en dos capas no cabe una topologia plana, y hacia
    falta una DISCIPLINA DE CAPA declarada antes de escribir una pista mas.

    La disciplina es la de la v2 -- potencia en F.Cu, arbol de GND entero en
    B.Cu -- y funciona porque GND es 68 de los 306 pads: sacarla de F.Cu es lo
    que deja sitio al resto. La alternativa (F.Cu horizontal / B.Cu vertical,
    via en cada codo) hace los cruces imposibles por construccion y cuesta
    cientos de vias, y cada via en un retorno es inductancia que esta fuente
    no quiere pagar.

    A MANO va lo que se define por su FORMA, no por su longitud:

      * `rutear_gnd`     el arbol de masa. Un plano crearia lazos, y un lazo
                         alrededor del puente es una espira de 100 Hz.
      * `rutear_red`     los 230 V, en carriles con 2.5 mm de aire entre
                         redes distintas.
      * `rutear_rieles`  los cuatro rieles y el Kelvin de OUTS, cuyo punto de
                         sensado decide que tension queda regulada.

    CON EL LABERINTO va el resto (`rutear_resto`), que son 126 conexiones
    donde lo unico que se pide es no cruzarse con nada.
    """
    r = Ruteo(board)
    rutear_red(r)
    rutear_rieles(r)
    escapes = escapar_pines_finos(r)
    rutear_gnd(r)
    abiertas = rutear_resto(r, escapes)
    assert not abiertas, "el laberinto no cerro: " + "; ".join(abiertas)
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

# Referencias de serigrafia que hay que apartar a mano. KiCad las pone por
# defecto justo encima del cuerpo, y ahi chocan cuando dos piezas grandes
# quedan proximas: la seda de C1 acaba en y=100.3 y la referencia de C2
# empezaba en 100.75, 0.45 mm de separacion sobre un minimo de 0.5. Los
# cuatro casos salieron del DRC real, no de mirar el dibujo.
SILK_REF = {
    # AL LADO y no debajo: debajo de estos dos no hay 1.2 mm libres. El
    # cuerpo acaba en y=118.3 y la RANURA de la barrera de red empieza en
    # 120, asi que la referencia caia justo en medio (silk_edge_clearance
    # contra Edge.Cuts). El hueco de 5 mm que queda entre los dos bulk si
    # tiene sitio.
    "C2":  (124.0, 110.0),
    "C13": (172.0, 110.0),
    "C30": (52.0, 104.2),     # debajo del 0805, fuera del rotulo del divisor
    "RV1": (63.0, 147.5),     # estaba a 122.3, encima de la ranura de la red
}

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
    # x=71 y no 66 como su gemelo de arriba: centrado en 66 el rotulo
    # llega por la izquierda hasta x=53.5 y se come el "C30" de la
    # serigrafia (silk_overlap en el DRC real). Arriba no pasa porque
    # ahi no hay ninguna pieza a esa altura.
    ("R24 R25 R26 = 20k (A LA REFERENCIA)", 71.0, 99.8, 0.9, 0),

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


def _aabb_descarta(caja1, caja2, limite: float) -> bool:
    '''La distancia entre cajas ya garantiza que no hay infraccion.

    La caja es una cota inferior: solo evita el calculo exacto cuando hasta
    los puntos mas cercanos cumplen el limite. La igualdad se descarta porque
    todos los revisores marcan exclusivamente distancias menores.
    '''
    if caja1[2] < caja2[0]:
        dx = caja2[0] - caja1[2]
    elif caja2[2] < caja1[0]:
        dx = caja1[0] - caja2[2]
    else:
        dx = 0.0
    if caja1[3] < caja2[1]:
        dy = caja2[1] - caja1[3]
    elif caja2[3] < caja1[1]:
        dy = caja1[1] - caja2[3]
    else:
        dy = 0.0
    return dx * dx + dy * dy >= limite * limite


def grafo_gnd(tracks, vias, red: str = "GND"):
    """Grafo del cobre de `red`: nodos (x, y, capa), vias como aristas.

    Un nodo es un punto DE UNA CAPA. Dos cobres que se cruzan en capas
    distintas no son un nodo -- eso es un cruce, no una union -- y por eso la
    transicion de capa tiene que entrar por su sitio: cada via de la red que
    encuentre cobre en sus dos caras aporta UNA arista entre sus dos nodos.
    Sin esa arista el grafo se parte por capas y una espira que sale por
    arriba y vuelve por abajo queda invisible, que es justo la que sec.7
    prohibe.

    Los tramos se parten en cada cruce o enganche interior de su eje: si una
    costilla fuera un solo tramo de punta a punta, el union-find solo veria
    sus dos extremos y un lazo de verdad pasaria sin que nadie lo viera.

    Las aristas de PISTA se procesan antes que las de VIA. Asi, cuando un
    lazo se puede romper quitando una via redundante, la que sobra sale
    marcada como `via` -- y quitarla nunca desconecta nada, porque una arista
    que cierra un ciclo jamas es un puente.

    Devuelve (aristas, cierres, tramos). `cierres` es la lista de
    (tipo, a, b) de las aristas que encontraron sus dos extremos ya unidos:
    una por cada lazo independiente. `tramos` es cada pista de la red partida
    en sus nodos, que es lo que necesita la poda para recortar sin adivinar.

    LIMITE DECLARADO: el grafo es de pistas y vias. Dos pads de la misma
    huella unidos por su propio cobre no son una arista aqui; esa
    conectividad la mide el ratsnest de KiCad en check_pcb.py.
    """
    eps = 1e-7
    # 1 um de tolerancia entre nodos, y se aplica AGRUPANDO, no redondeando.
    # Redondear no sirve: dos puntos a 0.5 um pueden caer a los dos lados de
    # la frontera de la rejilla y salir MAS separados que antes. Aqui el
    # primer punto de cada grupo se queda de representante y los que caen a
    # menos de TOL se le pegan.
    #
    # Hace falta porque dos cobres a media micra, con 1 mm de ancho, se
    # solapan enteros: son un nodo. Si la regla los separa, el lazo que pasa
    # por ahi deja de verse.
    tol = 0.001
    _celdas: dict = {}

    def punto(p):
        gx, gy = int(p[0] // tol), int(p[1] // tol)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for q in _celdas.get((gx + dx, gy + dy), ()):
                    if abs(q[0] - p[0]) <= tol and abs(q[1] - p[1]) <= tol:
                        return q
        q = (p[0], p[1])
        _celdas.setdefault((gx, gy), []).append(q)
        return q

    def resta(p, q):
        return (p[0] - q[0], p[1] - q[1])

    def cruz(p, q):
        return p[0] * q[1] - p[1] * q[0]

    def en_segmento(p, a, b):
        ab, ap = resta(b, a), resta(p, a)
        if abs(cruz(ab, ap)) > eps * max(1.0, abs(ab[0]) + abs(ab[1])):
            return False
        return (min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps
                and min(a[1], b[1]) - eps <= p[1]
                <= max(a[1], b[1]) + eps)

    def intersecciones(a, b, c, d):
        r, s = resta(b, a), resta(d, c)
        r2 = r[0] ** 2 + r[1] ** 2
        s2 = s[0] ** 2 + s[1] ** 2
        if r2 <= eps ** 2:
            return {a} if en_segmento(a, c, d) else set()
        if s2 <= eps ** 2:
            return {c} if en_segmento(c, a, b) else set()
        den = cruz(r, s)
        ca = resta(c, a)
        if abs(den) > eps:
            t, u = cruz(ca, s) / den, cruz(ca, r) / den
            if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
                return {punto((a[0] + t * r[0], a[1] + t * r[1]))}
            return set()
        if abs(cruz(ca, r)) > eps * max(1.0, abs(r[0]) + abs(r[1])):
            return set()
        return {
            p for p in (a, b, c, d)
            if en_segmento(p, a, b) and en_segmento(p, c, d)
        }

    padre: dict = {}
    aristas: set = set()
    cierres: list = []

    def raiz(n):
        while padre[n] != n:
            padre[n] = padre[padre[n]]
            n = padre[n]
        return n

    def unir(a, b, tipo):
        if a == b:
            return
        arista = tuple(sorted((a, b)))
        if arista in aristas:
            return
        aristas.add(arista)
        for n in (a, b):
            padre.setdefault(n, n)
        ra, rb = raiz(a), raiz(b)
        if ra == rb:
            cierres.append((tipo, a, b))
        else:
            padre[ra] = rb

    segmentos = []
    for idx, (net, capa, pts, ancho) in enumerate(tracks):
        if net.lstrip("/") != red:
            continue
        for i in range(len(pts) - 1):
            a, b = punto(pts[i]), punto(pts[i + 1])
            segmentos.append([capa, a, b, {a, b}, idx, ancho])

    for i, s1 in enumerate(segmentos):
        capa1, a, b, cortes1 = s1[:4]
        for s2 in segmentos[i + 1:]:
            capa2, c, d, cortes2 = s2[:4]
            if capa1 != capa2:
                continue
            if (max(a[0], b[0]) + eps < min(c[0], d[0])
                    or max(c[0], d[0]) + eps < min(a[0], b[0])
                    or max(a[1], b[1]) + eps < min(c[1], d[1])
                    or max(c[1], d[1]) + eps < min(a[1], b[1])):
                continue
            cruces = intersecciones(a, b, c, d)
            cortes1.update(cruces)
            cortes2.update(cruces)

    # LAS VIAS TAMBIEN PARTEN. Una via no siempre cae en la punta de un
    # tramo: puede posarse a mitad de recorrido, y ahi une igual. Si el tramo
    # no se parte por ella, sus dos caras no tienen nodo en ese punto, la
    # arista de via no se puede crear y el lazo que pasa por ahi se pierde.
    # Lo destapo un canario: coser las dos caras en (16.525, 66.0) cerraba
    # una espira que la regla no veia.
    for vx, vy, vnet, _a, _t in vias:
        if vnet.lstrip("/") != red:
            continue
        p = punto((vx, vy))
        for seg in segmentos:
            if en_segmento(p, seg[1], seg[2]):
                seg[3].add(p)

    tramos = []
    for capa, a, b, cortes, idx, ancho in segmentos:
        ordenados = sorted(
            cortes,
            key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2,
        )
        tramos.append((idx, capa, ordenados, ancho))
        for p, q in pairwise(ordenados):
            unir((*p, capa), (*q, capa), "pista")

    # LAS VIAS, DESPUES. Una via solo une lo que ya existe: si en una de sus
    # dos caras no hay cobre de la red, no hay nodo que unir y no aporta
    # arista -- ahi la via toca un pad, y de los pads se encarga el ratsnest.
    for vx, vy, vnet, _ancho, _taladro in vias:
        if vnet.lstrip("/") != red:
            continue
        p = punto((vx, vy))
        arriba, abajo = (*p, "F.Cu"), (*p, "B.Cu")
        if arriba in padre and abajo in padre:
            unir(arriba, abajo, "via")

    return aristas, cierres, tramos


def revisar_estrella() -> list[str]:
    """Que GND sea un ARBOL y no una malla (heredado v1, sec.7).

    «Aqui GND es un arbol: sale del punto de estrella, cada rama muere en su
    grupo funcional, y no hay ni un bucle» (design-notes sec.14.5). Un plano
    de masa une todo con todo por el camino mas corto, y un lazo alrededor
    del puente rectificador es una espira de 100 Hz acoplada a todo.

    Un bucle NO se ve mirando el dibujo -- se ve igual que una rama -- asi
    que se comprueba con union-find sobre el grafo de grafo_gnd(), vias
    incluidas. Cero bucles, sin tolerancia de area: el papel no la da.
    """
    _, cierres, _ = grafo_gnd(TRACKS, VIAS)
    return [
        f"bucle de GND al cerrar por {tipo} {a} con {b}"
        for tipo, a, b in cierres
    ]


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
    izquierda, derecha = cx - hw, cx + hw
    arriba, abajo = cy - hh, cy + hh

    def dentro(p):
        return izquierda <= p[0] <= derecha and arriba <= p[1] <= abajo

    if dentro(a) or dentro(b):
        return 0.0

    esquinas = [
        (izquierda, arriba),
        (derecha, arriba),
        (derecha, abajo),
        (izquierda, abajo),
    ]
    aristas = zip(esquinas, esquinas[1:] + esquinas[:1])
    return min(dist_seg(a, b, c, d) for c, d in aristas)


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
            caja_tramo = (min(a[0], b[0]), min(a[1], b[1]),
                          max(a[0], b[0]), max(a[1], b[1]))
            for nom, pnet, px, py, hw, hh, enF, enB in pads:
                if pnet == net:
                    continue
                if not (enF if capa == "F.Cu" else enB):
                    continue
                minimo = 2.5 if (es_red(net) or es_red(pnet)) else CLEARANCE_MM
                caja_pad = (px - hw, py - hh, px + hw, py + hh)
                if _aabb_descarta(caja_tramo, caja_pad,
                                  minimo + ancho / 2):
                    continue
                d = dist_seg_rect(a, b, px, py, hw, hh) - ancho / 2
                if d < minimo:
                    malos.append(f"{net} en {capa} a {d:.2f}mm del pad "
                                 f"{nom}[{pnet}] ({a}-{b})")
    return malos


def revisar_vias(board) -> list[str]:
    """Vias contra pads, pistas y otras vias -- de otra red por el cobre, de
    cualquiera por el taladro.

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
        caja_via = (vx, vy, vx, vy)
        for nom, pnet, px, py, hw, hh in pads:
            if pnet == vnet:
                continue
            minimo = 2.5 if (es_red(vnet) or es_red(pnet)) else CLEARANCE_MM
            caja_pad = (px - hw, py - hh, px + hw, py + hh)
            if _aabb_descarta(caja_via, caja_pad, minimo + vr):
                continue
            d = dist_seg_rect((vx, vy), (vx, vy), px, py, hw, hh) - vr
            if d < minimo:
                malos.append(f"via {vnet} en ({vx},{vy}) a {d:.2f}mm "
                             f"del pad {nom}[{pnet}]")
        for net, _capa, pts, ancho in TRACKS:
            if net == vnet:
                continue
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                minimo = 2.5 if (es_red(net) or es_red(vnet)) else CLEARANCE_MM
                caja_tramo = (min(a[0], b[0]), min(a[1], b[1]),
                              max(a[0], b[0]), max(a[1], b[1]))
                if _aabb_descarta(caja_via, caja_tramo,
                                  minimo + vr + ancho / 2):
                    continue
                d = dist_seg(a, b, (vx, vy), (vx, vy)) - vr - ancho / 2
                if d < minimo:
                    malos.append(f"via {vnet} en ({vx},{vy}) a {d:.2f}mm "
                                 f"de pista {net} ({a}-{b})")
    for i, (x1, y1, n1, a1, t1) in enumerate(VIAS):
        for x2, y2, n2, a2, t2 in VIAS[i + 1:]:
            centros = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            # Dos vias de la MISMA red pueden tocarse en cobre -- son el mismo
            # nodo -- pero sus TALADROS no: eso es una regla de fabricacion,
            # no electrica. El `continue` de aqui se comia justamente ese
            # caso, y el DRC real lo canto (dos vias de GND a 0.5 mm).
            minimo_taladros = t1 / 2 + t2 / 2 + HOLE_CLEARANCE
            if centros < minimo_taladros:
                malos.append(f"via {n1}({x1},{y1}) y via {n2}({x2},{y2}): "
                             f"taladros a {centros:.2f}mm de centro a centro "
                             f"y hacen falta {minimo_taladros:.2f}")
            if n1 == n2:
                continue
            d = centros - a1 / 2 - a2 / 2
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
            a, b = pts[i], pts[i + 1]
            caja = (min(a[0], b[0]), min(a[1], b[1]),
                    max(a[0], b[0]), max(a[1], b[1]))
            segs.append((net, capa, a, b, ancho, caja))
    malos = []
    for i, (n1, c1, a, b, w1, caja1) in enumerate(segs):
        for n2, c2, c, d, w2, caja2 in segs[i + 1:]:
            if c1 != c2 or n1 == n2:
                continue
            minimo = 2.5 if (es_red(n1) or es_red(n2)) else CLEARANCE_MM
            if _aabb_descarta(caja1, caja2, minimo + (w1 + w2) / 2):
                continue
            hueco = dist_seg(a, b, c, d) - (w1 + w2) / 2
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
    ds.m_TrackMinWidth = mm(CLEARANCE_MM)
    ds.m_MinClearance = mm(CLEARANCE_MM)
    ds.m_ViasMinSize = mm(VIA_D)
    ds.m_MinThroughDrill = mm(VIA_TALADRO)
    # La NETCLASS, y aqui dentro. El DRC no compara contra m_MinClearance --
    # eso es el suelo de la placa -- sino contra la clase que le toca a cada
    # red, y con una sola clase definida eso es siempre `Default`. Escribirlo
    # solo en el .kicad_pro no basta y costo dos rondas averiguarlo: la
    # primera version lo ponia ahi, y `kicad-cli pcb drc --save-board` volvio
    # a dejarlo en el 0.2 de fabrica -- porque el valor que guarda es el que
    # la PLACA lleva en memoria, no el que hubiera en el fichero de proyecto.
    # Escrito en el objeto, viaja con la placa lo guarde quien lo guarde.
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(CLEARANCE_MM))
    nc.SetViaDiameter(mm(VIA_D)) if hasattr(nc, "SetViaDiameter") else None
    nc.SetViaDrill(mm(VIA_TALADRO)) if hasattr(nc, "SetViaDrill") else None
    # No hace falta subir m_MinAnnularWidth (default de placa, 0.1mm): ya NO
    # hay pads por debajo de ese minimo. F3 (review fase C) RESOLVIO -- no
    # bendijo -- las 10 violaciones annular_width de los pads THT de U1/U2
    # (footprint TO-220-5 stock, taladro 1.1mm): antes daban un anillo real
    # de 0.0875mm (por debajo de la capability JLC de 2 capas, 0.13mm), y en
    # vez de documentarlas como excepcion aceptada se ensancho el eje corto
    # del pad a 1.4mm (ver main(), justo despues de colocar U1/U2) -> anillo
    # (1.4-1.1)/2=0.15mm, ya por encima del minimo real. DRC completo real:
    # 0 violaciones de cualquier tipo, no 10 bendecidas.


def reglas_proyecto() -> list[str]:
    """El clearance que aplica el DRC vive en la NETCLASS, y esa no la guarda
    SaveBoard(): esta en el .kicad_pro.

    `m_MinClearance` es el SUELO de la placa -- el valor por debajo del cual
    KiCad no deja bajar a nadie. El que el DRC compara de verdad, pista contra
    pista, es el de la netclass que le toque a cada red, y con una sola clase
    definida eso es siempre `Default`. Estaba en 0.2 mm: el default de fabrica
    de KiCad, que nadie eligio y que ningun comentario de este fichero
    menciona.

    El resultado fue tres verdades sobre el mismo numero -- CLEARANCE_MM
    (0.127, con fuente), `m_MinClearance` (0.127, escrito aqui) y la netclass
    (0.2, escrita por KiCad) -- y mandaba la unica que no estaba en el codigo:
    34 infracciones de margen de 0.15 y 0.175 mm con revisar_pistas() y
    revisar_pista_pad() en verde, porque las dos miden contra CLEARANCE_MM.

    Devuelve las claves que cambio, para que quien lo llame lo imprima. Un
    fichero de proyecto reescrito en silencio es la forma comoda de que la
    proxima discrepancia tarde otra version en salir.
    """
    with open(PRO, encoding="utf-8") as fh:
        pro = json.load(fh)
    cambios = []
    for clase in pro["net_settings"]["classes"]:
        for clave, valor in (("clearance", CLEARANCE_MM),
                             ("via_diameter", VIA_D),
                             ("via_drill", VIA_TALADRO)):
            if abs(clase.get(clave, 0) - valor) > 1e-9:
                cambios.append(f"{clase['name']}.{clave}: "
                               f"{clase.get(clave)} -> {valor}")
                clase[clave] = valor
    reglas_pcb = pro["board"]["design_settings"]["rules"]
    for clave, valor in (("min_clearance", CLEARANCE_MM),
                         ("min_track_width", CLEARANCE_MM),
                         ("min_hole_clearance", HOLE_CLEARANCE),
                         ("min_through_hole_diameter", VIA_TALADRO)):
        if clave in reglas_pcb and abs(reglas_pcb[clave] - valor) > 1e-9:
            cambios.append(f"rules.{clave}: {reglas_pcb[clave]} -> {valor}")
            reglas_pcb[clave] = valor
    if cambios:
        # indent 2 y salto de linea de la plataforma, que es como lo
        # escribe KiCad: el objetivo es que el diff sea el valor que
        # cambio y no el fichero entero.
        with open(PRO, "w", encoding="utf-8") as fh:
            json.dump(pro, fh, indent=2, ensure_ascii=False)
            fh.write(chr(10))
    return cambios


def distancia_bbox(a: pcbnew.BOX2I, b: pcbnew.BOX2I) -> float:
    """Separacion entre dos cajas, 0 si se tocan. En mm. Heredado v1."""
    dx = max(0, max(a.GetLeft() - b.GetRight(), b.GetLeft() - a.GetRight()))
    dy = max(0, max(a.GetTop() - b.GetBottom(), b.GetTop() - a.GetBottom()))
    return (dx * dx + dy * dy) ** 0.5 / 1e6


def bbox_de(board, refs: list[str]) -> pcbnew.BOX2I:
    """Caja que envuelve la huella de cada ref, SIN su serigrafia.

    `_caja_util()` y no `GetBoundingBox()` a secas, y la diferencia se midio:
    mover la referencia "C2" de sitio -- por un choque de serigrafia, decision
    puramente cosmetica -- estrechaba la diagonal del lazo de rectificacion a
    la isla de telemetria de 39.9 mm a 31.8, a dos milimetros de su umbral.

    Una regla que protege contra ACOPLAMIENTO no puede depender de donde este
    impresa una letra: lo que acopla es el cobre. El repo ya habia tropezado
    con esto por el otro lado y lo resolvio igual -- el campo Value se oculta
    en main() justo porque `GetBoundingBox()` lo cuenta e infla la caja de una
    pieza SMD hasta decenas de mm. El campo Reference hacia lo mismo y seguia
    contando.

    Los umbrales NO se tocan: 80 mm y 30 mm siguen siendo los de la spec. Lo
    que cambia es que ahora se comparan contra la distancia que existe.
    """
    caja = pcbnew.BOX2I()
    for ref in refs:
        caja.Merge(_caja_util(board.FindFootprintByReference(ref)))
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

    # CreateEmptyBoard() y no NewBoard(PCB): el segundo TRUNCA el fichero de
    # destino al crearlo, asi que cualquier fallo posterior -- una red que el
    # ruteador no cierra, una via que no cabe -- dejaba en el disco un
    # .kicad_pcb vacio en vez del ultimo bueno. Un artefacto vaciado pasa el
    # ERC con 0 avisos (constitucion, Principio VIII): el fichero solo se
    # escribe al final, cuando ya se sabe que hay algo que escribir.
    board = pcbnew.CreateEmptyBoard()
    contorno(board)
    franja_to220(board)
    reglas(board)
    cambios_pro = reglas_proyecto()
    print(f"reglas del .kicad_pro alineadas con el script: "
          f"{len(cambios_pro)} {cambios_pro}")

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
    for ref, (rx, ry) in SILK_REF.items():
        fp = board.FindFootprintByReference(ref)
        assert fp, f"SILK_REF nombra una pieza que no existe: {ref}"
        fp.Reference().SetPosition(pcbnew.VECTOR2I(mm(rx), mm(ry)))
    print(f"referencias de serigrafia apartadas: {len(SILK_REF)}")

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
    # EL RECORTE DE H4 APUNTABA FUERA DEL CONTORNO. Se escribio cuando la
    # placa medía 150x200 y H4 caia dentro de ISLA_REF; al girarla a 200x150
    # (Task 6) el taladro se fue a (193, 143) y el recorte se quedo -- un
    # "agujero" fuera de su propio poligono, que es geometria invalida.
    #
    # Lo que hacia, medido: la zona de 3256 mm2 sobre ISLA_REF se rellenaba
    # como UN trozo de 12.24 mm2 centrado en (193, 143), o sea alrededor del
    # taladro y a 140 mm de donde tenia que estar. De ahi salian el
    # `isolated_copper` del DRC y los seis pads de GNDREF sin conectar. El
    # segfault del ZONE_FILLER NO era esto: se probo a proposito con el
    # poligono ya arreglado y se sigue cayendo.
    #
    # Ahora se recorta lo que de verdad haya dentro, y si no hay nada no se
    # recorta. El patron de la v1 para taladros de fijacion sigue igual: sin
    # cobre alrededor, porque el puente chasis-masa es uno solo y va por J5.
    r_keepout = MOUNT_D / 2 + 0.4            # 1.6 + 0.4 = 2.0 mm
    dentro = [(hx, hy) for _ref, hx, hy in MOUNTING
              if x1 - r_keepout < hx < x2 + r_keepout
              and y1 - r_keepout < hy < y2 + r_keepout]
    for hx, hy in dentro:
        hole_idx = outline.NewHole(0)
        for i in range(16):
            ang = 2 * math.pi * i / 16
            outline.Append(mm(hx + r_keepout * math.cos(ang)),
                           mm(hy + r_keepout * math.sin(ang)), 0, hole_idx)
    print(f"taladros recortados de la zona GNDREF: {len(dentro)} {dentro}")

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
    # Los trozos de relleno que no tocan nada se TIRAN. El default de KiCad es
    # conservarlos, y entonces el gerber lleva cobre que no conecta con nada:
    # el DRC lo canta como `isolated_copper` y en la placa real es una isla
    # flotante junto a la referencia de los divisores, que es el peor sitio
    # donde dejar cobre sin potencial definido. Con la isla ultra ruteada
    # encima, la zona se trocea por fuerza y esos restos aparecen solos.
    zona.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zona.SetIsFilled(False)
    board.Add(zona)
    # LA ZONA SE ANADE SIN RELLENAR, Y NO ES UN OLVIDO. `ZONE_FILLER.Fill()`
    # desde el Python de KiCad 10.0 hace SEGFAULT con esta placa ya ruteada
    # (medido 2026-08-21: exit 139, sin traceback, con 1042 segmentos; con
    # 995 todavia pasaba). No es la zona ni su geometria: sigue petando con
    # el poligono ya arreglado -- el recorte de H4 apuntaba fuera de su
    # contorno, ver mas abajo -- y sin la zona la placa entera sale en verde.
    # Es el filler, y los dos fallos eran independientes.
    #
    # El relleno lo hace `kicad-cli pcb drc --refill-zones --save-board`, que
    # es el mismo codigo corriendo fuera del proceso y no se cae. Queda como
    # paso del pipeline en el README de fab -- declarado, no escondido: una
    # zona sin rellenar en un gerber es cobre que no existe.
    zona.SetIsFilled(False)
    print("zona GNDREF creada sobre ISLA_REF -- se rellena con kicad-cli")

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
    munones = revisar_cobre_muerto(board)
    print(f"cobre de masa sin servir (munones): {len(munones)} {munones[:4]}")
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
    assert not munones, f"cobre de masa colgando sin servir: {munones}"
    assert not cerca, f"taladros demasiado cerca de la red: {cerca}"
    assert not smd_mal, f"SMD fuera de F.Cu: {smd_mal}"
    assert not isla_mal, f"isla GNDREF mal: {isla_mal}"
    assert not diagonal_mal, f"lazo rectificador demasiado cerca de la isla ultra: {diagonal_mal}"
    assert not borde_mal, f"ceramicos demasiado cerca del borde: {borde_mal}"
    assert not tabs_mal, f"los TO-220 no casan con la pared del chasis: {tabs_mal}"


if __name__ == "__main__":
    sys.exit(main())
