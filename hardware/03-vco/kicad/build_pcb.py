"""Genera sam17-vco.kicad_pcb: 114 x 124 mm, 4 capas, UNA masa (GNDA) en
plano entero y una isla GNDD minima en la esquina de J2.

EL STACKUP, que es la decision que manda sobre todo lo demas:

    F.Cu     senal
    In1.Cu   GNDA SOLIDA, sin una sola pista
    In2.Cu   GNDD (la esquina de la isla) + potencia
    B.Cu     senal

La ronda anterior salio de aqui en 2 capas y no cerraba: 4 voces identicas
comparten 7 buses, ese grafo no es planar, las senales tienen que cruzarse,
y con dos capas la unica donde cruzar era el propio plano de masa. Once
configuraciones medidas acotaron el intercambio de punta a punta (155 tramos
al aire con el plano intacto, 15 con el plano al 96%) y ninguna cerraba las
dos cosas. Con 4 capas se cierran las dos a la vez y ademas el presupuesto
MEJORA: dac_local_budget.py modela un vertido de 20 mm de ancho, y lo que
hay ahora debajo del camino DAC->VCO es una capa interna entera.

    set FREEROUTING_JAR=C:\\ruta\\freerouting-2.1.0.jar
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Va con pcbnew directo para la colocacion y las masas, igual que el modulo 1,
el modulo 2 y el bus board. Lo que NO va a mano es el ruteo: ver abajo.

LA DECISION DE ESTA PLACA: **casi toda ella es dominio analogico.** A
diferencia del modulo 2 (mitad Pi/LCD/botones, mitad DAC/ampli), aqui el
digital de verdad es una esquina de nueve componentes: J2 (el mazo IDC hacia
el cerebro), U10 (74HC14, cuadra el TUNE_OUT), U13 (TMP1075, mide temperatura
para el autoafinado), U14 (EEPROM de identidad), sus desacoplos y los pullups
de I2C. Todo lo demas -- el racimo de 4 SSI2130, los 3 DAC locales, la
referencia, los jacks -- vive en GNDA.

Por eso la frontera no es una linea recta de punta a punta de la placa (como
en el modulo 2): es una ISLA en la esquina de J2, recortada del plano GNDA
con el mismo HUECO sin cobre que revisar_frontera() mide, adaptada para medir
distancia 2D entre los dos vertidos (aqui la frontera dobla una esquina) en
vez de solo la x. Los dos vertidos ya no comparten capa, asi que ese hueco
es una separacion EN PLANTA: In1 esta recortada justo debajo de la isla
digital para que los dos retornos no se solapen ni siquiera verticalmente.

LA COLOCACION ES UN CUADRO 2x2, NO UNA FILA DE 4. Es la correccion de fondo
de esta version. Con las 4 voces en fila el DAC de tono se queda en una punta
o en medio de una recta larga, y el peor par DAC->VCO se iba a 85 mm contra
los 50 mm que modela dac_local_budget.LARGO_LOCAL. En cuadro, los 3 DAC y la
referencia caben en el hueco central del cuadrado y las 4 voces quedan a la
MISMA distancia del DAC -- el peor par baja a 43.2 mm (39.0 el de U5, que es
el que manda la afinacion), dentro de la cota, y de paso la placa pasa de
240x172 a 114x124: 3x menos area. Esas dos cifras son las de la placa
COMMITTEADA, medidas sobre sus coordenadas finales; las de rondas anteriores
(41.8 / 37.7) se quedaron en un docstring que no se actualizo al recolocar.

EL RUTEO LO HACE FREEROUTING, no un ruteador casero. La version anterior de
este script traia un ruteador voraz de caminos en L/Z: cerraba 70 de 106
redes. Freerouting es un router de verdad, con rip-up y backtracking, y
cierra el 96% de las conexiones. El flujo -- exportar DSN, correr el jar
headless, importar SES, repetir -- vive en rutear(). El jar NO se descarga
solo: si falta, el script lo dice y aborta.

LA REGLA DE RUTEO, ahora que hay 4 capas: **In1 no se toca.** F.Cu y B.Cu
son dos capas de senal completas y por ellas puede ir lo que sea; por In1 no
pasa ni una pista. La asimetria vieja de B.Cu (que existia solo porque el
plano vivia ahi) se va con ella. Lo unico que atraviesa In1 son las VIAS,
que son inevitables -- todo el cobre es SMD en F.Cu, asi que cada pad de
masa baja al plano por una via y cada cambio de capa lo cruza. Una via deja
un AGUJERO, que la corriente de retorno rodea sin enterarse; una pista
dejaria una RANURA, que la obliga a dar la vuelta. revisar() lo comprueba a
posteriori sobre el relleno real: la isla mayor de In1 tiene que llevarse
mas del 99% del cobre.

LAS VIAS VAN AL LADO DE LOS PADS, NUNCA ENCIMA. Durante siete rondas
coser_masas() probaba el centro del pad como primer sitio para la via, y de
ahi salieron 15 vias taladradas dentro del agujero de un jack o de un
conector y 32 vias debajo de un pad SMD. Las dos cosas son mecanica, no
electricidad: la broca no lee el netlist y una via debajo de un pad exige
taponar y planarizar. Ahora la comprobacion de sitio esta partida en dos --
lejos() para el margen ELECTRICO (que si se salta la propia red) y
taladro_libre() para el MECANICO (que no se la salta) -- y revisar_taladros()
lo vuelve a medir sobre la placa terminada. Ademas hole_to_hole y
holes_co_located suben de aviso a ERROR en el .kicad_pro, que es lo que hace
que el DRC de --severity-error los vea.

EL TERMOMETRO VIVE CON LOS OSCILADORES. U13 (TMP1075) mide la temperatura
que desafina, asi que va pegado al QFN de la voz 2 (2.1 mm de cuerpo a
cuerpo) con un vertido termico AISLADO en medio, aunque electricamente siga
siendo GNDD y llegue a su masa por pista. Ver TERMOMETRO, mas abajo.

EL EP DE CADA SSI2130 (pin 33, land termico) queda AISLADO a proposito: la
netlist ya lo trae con nombre unico "unconnected-(Un-EP-Pad33)" y este script
NO lo toca -- ni via, ni red, ni union al plano. El datasheet (pag.6,
Exposed Thermal Pad) lo prohibe: unir el EP a GND convierte el land en una
antena de acoplo entre las 4 voces y en un camino de fuga termica que el
autoafinado no puede compensar. verificar_ep() lo comprueba al final, sobre
la placa ya ruteada, no sobre la intencion.
"""
from __future__ import annotations

import contextlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-vco.kicad_pcb")
NET = os.path.join(DIR, "sam17-vco.net")
RPT = os.path.join(DIR, "sam17-vco-drc.rpt")
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
STOCK = os.environ.get("KICAD_FOOTPRINTS",
                       r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
JAVA = os.environ.get("JAVA", "java")
FREEROUTING = os.environ.get("FREEROUTING_JAR", "")
PASADAS = int(os.environ.get("FREEROUTING_PASADAS", "250"))
RONDAS = int(os.environ.get("FREEROUTING_RONDAS", "3"))
# Coste de via del router. De fabrica 50, pensado para 2 capas donde bajar
# es caro de verdad. Aqui hay dos capas de senal y un plano solido: cambiar
# de capa es lo normal, y penalizarlo solo consigue que el router se ahogue
# en el anillo de un QFN de 0.4 mm de paso en vez de escapar hacia abajo.
VIA_COSTS = int(os.environ.get("FREEROUTING_VIA_COSTS", "8"))

W, H = 114.0, 124.0
MARGEN = 4.0
# la isla GNDD: esquina inferior izquierda, x < ISLA_X1 e y > ISLA_Y1 (antes
# de descontar el hueco). Los dos bordes que SI dan a GNDA son el derecho
# (x=ISLA_X1) y el de arriba (y=ISLA_Y1); los otros dos coinciden con el
# borde de la placa, ahi no hace falta hueco.
ISLA_X1 = 56.0
ISLA_Y1 = 96.0
HUECO = 3.0                # ancho del hueco de cobre entre GNDA y GNDD, mm
G = HUECO / 2

ANCHO = 0.12                # pista de senal. UNA sola anchura a proposito:
                            # lo mas "gordo" de esta placa son +-12V, que solo
                            # alimentan un TL074 y los pines V- de 4 SSI2130,
                            # decenas de mA. 0.12 mm en 1 oz aguanta ~0.4 A.
VIA_D = 0.45                # diametro exterior de via
VIA_DRILL = 0.20            # taladro
CLEARANCE = 0.10            # entre cobre de redes distintas
HOLE_CLEARANCE = 0.20       # de un taladro al cobre ajeno

# REGLAS AFINADAS A LA CAPACIDAD REAL DEL FABRICANTE. Verificado en
# jlcpcb.com/capabilities/pcb-capabilities el 2026-08-17, proceso ESTANDAR
# de 4 capas en 1 oz, sin HDI y sin via-in-pad:
#
#   pista / aislamiento minimos   0.09 / 0.09 mm  (3.5/3.5 mil, multicapa)
#   taladro de via minimo         0.15 mm
#   de taladro de via a pista     0.20 mm
#   de taladro a taladro          0.20 mm
#   via de 0.20 de taladro        SIN recargo si el diametro es >= 0.45 mm
#                                 (textual: "0.2mm or 0.25mm hole size with
#                                 via diameter less than 0.45mm, will cost
#                                 more" -- por eso 0.45 y no 0.4)
#
# De ahi salen los valores de arriba: 0.45/0.20 es justo el punto sin
# recargo, y 0.12/0.10 se quedan un 30% por encima del minimo publicado.
#
# POR QUE IMPORTA, y es la correccion de fondo de esta ronda: los valores
# viejos (via 0.6, margen 0.15, pista 0.2) venian del modulo 2 -- dos capas,
# componentes de paso ancho -- y aqui bloqueaban el escape de los QFN. Para
# que el rabito de un pin pase al lado de la via de su vecino hace falta
# VIA_D/2 + CLEARANCE + ANCHO/2, contra los 0.40 mm de paso del QFN:
#
#   0.6  / 0.15 / 0.2    ->  0.550 mm   NO CABE  (lo que atasco las rondas 5 y 6)
#   0.45 / 0.10 / 0.12   ->  0.385 mm   CABE     (0.395 con el margen del DSN)
#
# La pared era de unos defaults heredados, no del fabricante.
# _check_escape() lo comprueba antes de generar cobre.

MOUNT = [(6.0, 6.0), (W - 6.0, 6.0), (6.0, H - 6.0), (W - 6.0, H - 6.0)]
# Los taladros de montaje se anaden en su propio bucle, no por COLOCACION, asi
# que check_cobertura() no tiene de que eximirlos. El conjunto existe vacio a
# proposito: el dia que algo mecanico SI entre por COLOCACION, este es el sitio
# donde se declara, y no un `if` suelto dentro de la comprobacion.
MECANICAS: frozenset[str] = frozenset()
MOUNT_D = 3.2

# ---------------------------------------------------------------- huellas
# Las 136 huellas de este esquematico son TODAS de stock: el propio campo
# Footprint del esquematico (build_schematic.py ya lo dejo puesto) resuelve
# a Package_SO / Package_DFN_QFN / Connector_* / Resistor_SMD / etc, ninguna
# vive en un sam17.pretty local. check_huellas() lo verifica antes de tocar
# el fichero.
HUELLA = {
    "qfn32": ("Package_DFN_QFN", "QFN-32-1EP_4x4mm_P0.4mm_EP2.65x2.65mm"),
    "tssop16": ("Package_SO", "TSSOP-16_4.4x5mm_P0.65mm"),
    "soic8": ("Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm"),
    "soic14": ("Package_SO", "SOIC-14_3.9x8.7mm_P1.27mm"),
    "vssop8": ("Package_SO", "VSSOP-8_3x3mm_P0.65mm"),
    "sot235": ("Package_TO_SOT_SMD", "SOT-23-5"),
    "sot89": ("Package_TO_SOT_SMD", "SOT-89-3"),
    "sot223": ("Package_TO_SOT_SMD", "SOT-223-3_TabPin2"),
    "r": ("Resistor_SMD", "R_0805_2012Metric"),
    "c": ("Capacitor_SMD", "C_0805_2012Metric"),
    "jack": ("Connector_Audio",
             "Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"),
    "molex4": ("Connector_Molex", "Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical"),
    "idc12": ("Connector_IDC", "IDC-Header_2x06_P2.54mm_Vertical"),
    "tp": ("TestPoint", "TestPoint_Pad_D2.0mm"),
}

# ------------------------------------------------------- las 4 voces (2x2)
# Centro del QFN de cada canal, en cuadro. La celda de una voz mide 26.4 x
# 20.1 mm (medido sobre los courtyards reales, no a ojo), asi que con 62 mm
# de paso en x y 42 mm en y queda un hueco central de 35.6 x 21.9 mm: justo
# lo que ocupan los 3 DAC en columna, sus desacoplos, U8 y su C11.
#
#   voz 1 (30,35)     C14 U6 C15    voz 3 (92,35)
#             U8      C12 U5 C13
#             C11     C16 U7 C17
#   voz 2 (30,77)   (giradas 180)   voz 4 (92,77)
#
# El indice de voz mapea a (columna, fila) asi: 1->(0,0) 2->(0,1) 3->(1,0)
# 4->(1,1). Con los jacks del panel ordenados 1,2,3,4 de izquierda a derecha,
# cada par CV/OUT cae encima de su columna de voces.
CX = [27.0, 90.0]
CY = [35.0, 81.0]
CUADRANTE = {1: (0, 0), 2: (0, 1), 3: (1, 0), 4: (1, 1)}
# La fila de ABAJO va girada 180 grados. No es simetria por gusto: cada lado
# del QFN lleva unas senales fijas y girar la celda decide a que distancia
# queda cada bus. Contado conexion a conexion contra el centro de la placa:
#   voz 2 y voz 4 giradas -> los 4 R_MIX (MIX_TRI/SAW/PULSE/SINE) y R_PITCH
#     miran al centro (5 buses ganados) y solo VREF_2V5 y PWM_CV pasan al
#     lado de fuera (2 perdidos). Ademas R_SQ queda del lado de U10, que
#     vive en la isla digital de abajo.
#   voz 1 y voz 3 sin girar: ahi el balance sale al reves.
ROT_VOZ = {1: 0, 2: 180, 3: 0, 4: 180}
JACK_Y = 7.0
JACK_X0, JACK_PASO = 18.25, 11.5

# Plantilla de un canal: (formato-de-ref, dx, dy) relativo al centro del
# QFN. Cada lado del chip agrupa las senales que entran por ese lado (visto
# en el .kicad_mod, pin a pin):
#   IZQUIERDA (pines 1-8): red del conformador de seno + TRI_OUT + EXPO_FREQ
#     (el nodo que suma CV_PITCH del DAC y CVIN del jack) + V- (pin 8).
#   DERECHA (17-24): red de VREF (LIN_FREQ, EXPO_SCALE) + V+ (18) + bucle de
#     SINE_OUT.
#   ABAJO (9-16): las 4 entradas del mezclador (vienen del DAC) + TCAP (14).
#   ARRIBA (25-32): MIX_OUT (hacia U9), BW_COMP, SQUARE_OUT (hacia U10),
#     PWM_CV (32) y V+ (27).
# Los 7 pasivos del lado izquierdo van en BLOQUE 2x4, no en columna de 7:
# apilados en una sola columna el bloque mediria 20 mm de alto y la celda
# entera crecia con el; en dos columnas mide 11 y la voz cabe en 20 mm de
# alto. El anillo de la version anterior (+-16 mm, en zigzag) existia para
# darle carriles al ruteador voraz; con Freerouting no hace falta pagar ese
# ancho.
_PLANTILLA = [
    ("U{i}", 0.0, 0.0),
    # bloque izquierdo, columna exterior
    ("R_SIN475B_{i}", -15.2, -4.5),
    ("R_SIN402_{i}", -15.2, -1.5),
    ("R_SIN475A_{i}", -15.2, 1.5),
    ("C_AC{i}A", -15.2, 4.5),
    # bloque izquierdo, columna interior. C_AC*B es un PUENTE de verdad: sus
    # dos pines van a AUX1_IN (pin 4, izquierda) y a SINE_OUT (pin 24,
    # esquina arriba-derecha), lados OPUESTOS del chip. Se queda del lado de
    # su pin 4 y el rodeo lo resuelve el router.
    ("C_AC{i}B", -10.5, -3.0),
    ("R_PITCH{i}", -10.5, 0.0),
    ("R_CVIN{i}", -10.5, 3.0),
    # columna derecha: la red de VREF
    ("R_LIN{i}", 11.5, -3.0),
    ("R_SCALE{i}", 11.5, 0.0),
    # fila de arriba: lo que sale hacia U9 y U10
    ("R_IV{i}", -6.0, -9.0),
    ("R_BW{i}", -2.0, -9.0),
    ("C_BW{i}", 2.0, -9.0),
    ("R_SQ{i}", 6.0, -9.0),
    # segunda fila de arriba: la compensacion del I/V (simulations/vco/
    # iv_stage.py). C_IV va en la MISMA COLUMNA que R_IV y pegado a el, a 4 mm
    # -- el mismo paso que usa el resto de la fila: los dos estan en paralelo y
    # forman el lazo de realimentacion, asi que el area que encierran es parte
    # del circuito, no una cuestion de estetica. R_OUT no tiene esa exigencia
    # (vive FUERA del lazo) y va al lado, en la columna de R_BW.
    ("C_IV{i}", -6.0, -13.0),
    ("R_OUT{i}", -2.0, -13.0),
    # fila de abajo: las 4 entradas del mezclador
    ("R_MIX{i}A", -6.0, 9.0),
    ("R_MIX{i}B", -2.0, 9.0),
    ("R_MIX{i}C", 2.0, 9.0),
    ("R_MIX{i}D", 6.0, 9.0),
]
# Los tres condensadores que van pegados al chip, cada uno alineado con SU
# pin y girado para que sea el pad util (el 1) el que mira al chip -- girar
# 180 grados un 0805 mueve el pad 1 de -0.95 a +0.95 y ahorra 1.9 mm de
# lazo, que en un desacoplo es la mitad del asunto:
#   C_TCAP -> pin 14 (0.6, 1.95), abajo    -> 270 grados (pad 1 arriba)
#   C_5V   -> pin 18 (1.95, 1.0), derecha  ->   0 grados (pad 1 a la izq)
#   C_12V  -> pin 8  (-1.95, 1.4), izq     -> 180 grados (pad 1 a la der)
_DESACOPLO_5V = {1: "C21", 2: "C22", 3: "C23", 4: "C24"}
_DESACOPLO_12V = {1: "C27", 2: "C28", 3: "C29", 4: "C30"}
_PEGADOS = [
    ("C_TCAP{i}", 0.6, 5.2, 270),
    # C_5V desacopla V+, que sale por dos pines: el 18 (costado derecho) y
    # el 27 (arriba). Va junto al 18. Se probo ponerlo junto al 27 para
    # despejar el abanico del costado derecho, y salio PEOR (8 conexiones
    # abiertas contra 5): lo que despeja de un lado lo tapa del otro, y
    # arriba compiten MIXO, BW_COMP, SQUARE_OUT y PWM_CV.
    ("{c5v}", 5.6, 1.0, 0),
    ("{c12v}", -5.6, 1.4, 180),
]

COLOCACION: dict[str, tuple[str, float, float, int]] = {}
for _i, (_col, _fila) in CUADRANTE.items():
    _cx, _cy = CX[_col], CY[_fila]
    _r = ROT_VOZ[_i]
    _s = -1.0 if _r == 180 else 1.0
    for _fmt, _dx, _dy in _PLANTILLA:
        _ref = _fmt.format(i=_i)
        _clave = "qfn32" if _ref == f"U{_i}" else (
            "c" if _ref.startswith("C") else "r")
        COLOCACION[_ref] = (_clave, _cx + _s * _dx, _cy + _s * _dy, _r)
    for _fmt, _dx, _dy, _rot in _PEGADOS:
        _ref = _fmt.format(i=_i, c5v=_DESACOPLO_5V[_i], c12v=_DESACOPLO_12V[_i])
        COLOCACION[_ref] = ("c", _cx + _s * _dx, _cy + _s * _dy, (_rot + _r) % 360)
    # puntos de prueba de la voz, en la esquina libre de la celda
    COLOCACION[f"TP{5 + _i}"] = ("tp", _cx - _s * 15.2, _cy - _s * 9.6, 0)  # CV_PITCH
    COLOCACION[f"TP{9 + _i}"] = ("tp", _cx - _s * 15.2, _cy + _s * 9.6, 0)  # MIXO
    # jacks del panel, en el borde de arriba, en el orden 1,2,3,4
    COLOCACION[f"J_CV{_i}"] = ("jack", JACK_X0 + JACK_PASO * (2 * _i - 2),
                               JACK_Y, 0)
    COLOCACION[f"J_OUT{_i}"] = ("jack", JACK_X0 + JACK_PASO * (2 * _i - 1),
                                JACK_Y, 0)

# ------------------------------------------- DAC + referencia, en el centro
# Regla 1 de dac_local_budget.py llevada al limite: los 3 DAC y la referencia
# viven DENTRO del cuadrado de las 4 voces, asi que las 4 estan a la misma
# distancia y ninguna paga el ser "la ultima de la fila". medir_dac_vco()
# imprime la cifra real contra la cota del presupuesto.
# Regla 4: U8 (ADR4525) al lado de los DAC, con C11 y TP5 -- la estrella de
# VREF_2V5 sale corta hacia las cuatro voces por igual.
# Los DAC van en COLUMNA, no en fila, y U5 (el de la afinacion) en el medio:
# asi las cuatro voces le quedan a la misma distancia. Sus desacoplos van del
# LADO de su pin, que en un TSSOP-16 son los COSTADOS, no arriba y abajo:
# +5V es el pin 5 (izquierda) y +3V3 los pines 11/15 (derecha).
COLOCACION.update({
    "U6": ("tssop16", 58.5, 51.5, 0),
    "U5": ("tssop16", 58.5, 58.0, 0),
    "U7": ("tssop16", 58.5, 64.5, 0),
    "C14": ("c", 52.0, 51.825, 180), "C15": ("c", 65.0, 52.475, 0),   # U6
    "C12": ("c", 52.0, 58.325, 180), "C13": ("c", 65.0, 58.975, 0),   # U5
    "C16": ("c", 52.0, 64.825, 180), "C17": ("c", 65.0, 65.475, 0),   # U7
    "U8": ("soic8", 72.0, 58.0, 0),
    "C11": ("c", 78.0, 58.635, 0),
    "TP5": ("tp", 72.0, 65.0, 0),
    # U9 (TL074) en el canal central de ARRIBA, entre los jacks y la fila
    # superior de voces: recibe MIXO_1..4 (pin 25, lado de arriba de cada
    # QFN) y devuelve VOICE_OUT_1..4 a los jacks. Abajo, con la fuente,
    # cada salida de audio se iba 90 mm hasta su jack.
    "U9": ("soic14", 58.5, 32.0, 0),
    "TP14": ("tp", 68.0, 32.0, 0),
})

# ------------------------------------------------- alimentacion + reguladores
# J1 en el borde OPUESTO a los jacks (regla 5): jacks arriba (y=8), J1 abajo
# a la derecha. Los reguladores locales +5V_LOC/+3V3_LOC viven pegados a J1,
# lejos del racimo -- no alimentan nada sensible a ruido de conmutacion.
_PX, _PY = W - 20.0, ISLA_Y1 + 2.0   # esquina de la fuente, relativa al borde
COLOCACION.update({
    "J1": ("molex4", _PX, _PY + 16.0, 0),
    "U11": ("sot89", _PX - 10.0, _PY, 0),
    "U12": ("sot223", _PX + 4.0, _PY + 1.0, 0),
    "C8": ("c", _PX - 16.0, _PY, 0), "C10": ("c", _PX - 5.0, _PY, 0),
    "C9": ("c", _PX + 4.0, _PY + 8.0, 0),
    "C25": ("c", _PX - 24.0, _PY, 0), "C26": ("c", _PX - 30.0, _PY, 0),
    "TP1": ("tp", _PX - 24.0, _PY + 4.0, 0),
    "TP2": ("tp", _PX - 30.0, _PY + 4.0, 0),
    "TP3": ("tp", _PX - 16.0, _PY + 4.0, 0),
    "TP4": ("tp", _PX - 8.0, _PY + 8.0, 0),
})

# --------------------------------------------------------- isla GNDD (J2)
# Solo lo que pide el brief: J2, U10, U14, sus desacoplos y los pullups de
# I2C. U13 NO vive aqui -- ver TERMOMETRO, mas abajo.
# J2 GIRADO 90 grados: sin girar, el courtyard del IDC-2x06 con su cable
# mide 24 mm de alto y obliga a la isla a ser mas alta que la placa que
# queda por debajo del racimo. Girado mide 24 de ancho por 10 de alto y cabe
# en la franja de 22 mm. revisar() comprueba que sus pads siguen cayendo
# dentro de la isla, que es lo que de verdad importa del giro.
_IY = ISLA_Y1 + 4.0          # primera fila util de la isla
COLOCACION.update({
    "J2": ("idc12", 16.0, _IY + 15.0, 90),
    "U10": ("soic14", 12.0, _IY + 3.5, 0),
    "C18": ("c", 18.0, _IY - 0.31, 0),
    "U14": ("sot235", 26.0, _IY, 0),
    "R_I2C1": ("r", 33.0, _IY, 0),
    "C20": ("c", 26.0, _IY + 4.5, 0),
    "R_I2C2": ("r", 33.0, _IY + 5.5, 0),
    "TP15": ("tp", 40.0, _IY + 5.5, 0),
})

# ------------------------------------------------------------- TERMOMETRO
# U13 (TMP1075) mide la temperatura que DESAFINA, no la del aire de la
# placa. El brief lo pide "adyacente al racimo con vertido termico hacia
# ellos" y eso manda sobre la comodidad de tenerlo en la isla digital: en la
# esquina de la isla (donde estuvo hasta esta ronda) queda a 25.5 mm del QFN
# mas cercano y al otro lado del hueco de 3 mm, o sea midiendo ambiente.
#
# Ahora va PEGADO al QFN de la voz 2, en diagonal a su esquina inferior
# derecha: hueco cuerpo-a-cuerpo de 2.1 mm, dentro del area analogica. La
# diagonal no es capricho -- los 8 pines de cada costado del QFN escapan
# perpendiculares a su lado, asi que la esquina es la parte del anillo que
# menos usa el router. La voz 2 y no otra porque es la que cae encima de la
# isla digital: sus dos hilos de I2C y su retorno viajan 11-14 mm, no 60.
#
# ELECTRICAMENTE SIGUE EN GNDD. Lo que la doctrina del repo prohibe es
# UNIR las dos masas (los NETOS, el cobre); una senal o un retorno que
# cruzan de zona como PISTA son un cruce normal y controlado, que es lo que
# hacen ya SPI, I2C y +3V3_LOC. Consecuencia practica: los 5 pads de GNDD de
# U13/C19 no tienen plano debajo al que bajar, asi que quedan fuera del
# censo de coser_masas() (ver FUERA_DEL_PLANO) y de la regla de "GNDD dentro
# de la isla" de revisar(). La frontera se sigue midiendo donde de verdad
# importa: entre los dos VERTIDOS.
#
# C19 conserva su geometria exacta respecto a U13 (pad util contra el pin 8),
# solo que el par entero va girado 180 grados.
U13_X, U13_Y, U13_ROT = 32.0, 86.0, 180
COLOCACION.update({
    "U13": ("vssop8", U13_X, U13_Y, U13_ROT),
    "C19": ("c", U13_X - 5.0, U13_Y + 0.975, U13_ROT),
})
# El vertido termico de U13: cobre AISLADO, sin red, de la misma clase que
# los cuatro lands del EP. Va debajo y alrededor del termometro y se estira
# en diagonal hacia la esquina del QFN, que es el camino corto del calor.
# Sin red porque no debe conducir NADA: si se le pusiera GNDA seria una
# pista mas del plano analogico entrando en el anillo del QFN, y si se le
# pusiera GNDD uniria las dos masas por la puerta de atras.
VERTIDO_U13 = [(30.0, 82.6), (35.6, 82.6), (35.6, 88.4), (30.0, 88.4)]

# Los pads de estas huellas no tienen plano de su red debajo (U13 y su
# desacoplo viven en el area analogica pero son GNDD): coser_masas() no les
# busca bajada y revisar() no les exige caer dentro de la isla. Su conexion
# a GNDD la hace el router con una pista, como con cualquier otra senal.
FUERA_DEL_PLANO = {"U13", "C19"}

# La isla la forman J2, U10, U14, C18, C20, R_I2C1-2 y TP15, y nadie mas.
# No hay lista que lo diga: revisar() lo comprueba PAD a PAD contra la red
# (GNDD dentro de en_isla(), GNDA fuera), que es la unica version que no se
# puede quedar desfasada.


# ------------------------------------------------------------- el stackup
# 4 capas. La de en medio manda: In1 es GNDA ENTERA y no se rutea por ella.
#   F.Cu   senal
#   In1.Cu GNDA solida  <- el plano que sostiene dac_local_budget.py
#   In2.Cu GNDD (la esquina de la isla) + potencia
#   B.Cu   senal
CAPA_GNDA = pcbnew.In1_Cu
CAPA_GNDD = pcbnew.In2_Cu


def en_isla(x: float, y: float) -> bool:
    return x < ISLA_X1 and y > ISLA_Y1


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


def check_cobertura(nets: dict[str, str]) -> None:
    """COLOCACION tiene que cubrir el netlist EXACTAMENTE, en los dos sentidos.

    check_huellas() parecia cubrir esto y no lo cubria: mira que los FICHEROS
    de huella existan en disco, no que cada componente del esquematico tenga
    donde ir. Es un proxy de manual (Principio IV) -- pasa, te deja tranquilo,
    y el problema sigue entero.

    Lo que costo: al anadir C_IV1-4 y R_OUT1-4 al esquematico, colocar() itero
    sobre COLOCACION como siempre y los ocho quedaron fuera sin una palabra. La
    placa salio con 136 huellas contra 144 componentes, cerro el ruteo con CERO
    tramos al aire y DRC 0. Una placa verde que no era el esquematico, y lo que
    lo caza es netdiff, o sea DESPUES de media hora de Freerouting.

    Ahora aborta antes de crear un solo objeto.
    """
    del_net = {k.rsplit("-", 1)[0] for k in nets}
    del_col = set(COLOCACION)
    sin_sitio = sorted(del_net - del_col)
    assert not sin_sitio, (
        f"{len(sin_sitio)} componentes del esquematico sin entrada en "
        f"COLOCACION: {sin_sitio}\n"
        f"  La placa saldria sin ellos, y con el ruteo cerrado y el DRC en "
        f"cero.\n"
        f"  Anadelos a _PLANTILLA (si son de voz) o a COLOCACION.update().")
    # El otro sentido: MECANICAS son las que existen a proposito sin red
    # (taladros de montaje). Cualquier otra sobra y hay que enterarse.
    sobran = sorted(del_col - del_net - MECANICAS)
    assert not sobran, (
        f"colocadas y no estan en el esquematico: {sobran}")


def colocar():
    """Placa vacia con todo colocado, contorno, taladros, masas y reglas."""
    check_huellas()
    nets = leer_netlist()
    check_cobertura(nets)
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    for n in sorted(set(nets.values())):
        board.Add(pcbnew.NETINFO_ITEM(board, n))

    for ref, (clave, x, y, rot) in COLOCACION.items():
        lib, nombre = HUELLA[clave]
        fp = pcbnew.FootprintLoad(os.path.join(STOCK, lib + ".pretty"), nombre)
        assert fp, f"no se cargo {lib}:{nombre}"
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        if rot:
            fp.SetOrientationDegrees(rot)
        # SERIGRAFIA: nada por debajo del minimo publicado por el fabricante.
        # La misma hoja de capacidades que da la pista de 0.09 mm dice, para
        # la serigrafia, ALTURA MINIMA 1.0 mm ("less than that will be
        # unidentifiable") y TRAZO MINIMO 0.15 mm -- son dos especificaciones
        # distintas y la de la pista no vale para el texto. La version
        # anterior encogia los rotulos de los pasivos a 0.5/0.10 citando el
        # minimo de PISTA, y eso dejaba 112 avisos de text_height y una
        # serigrafia que el fabricante no garantiza legible.
        #
        # El problema que aquel encogimiento resolvia era real (en un anillo
        # de 0805 a 3 mm de paso los rotulos de 1 mm se pisan), pero la
        # solucion de la industria para SMD es otra: se OCULTA la referencia
        # de los pasivos. La identidad de cada pieza viaja en el fichero de
        # posiciones y en el BOM, que es lo que lee la maquina que las
        # coloca; el serigrafiado de R_MIX3C en la placa no lo mira nadie.
        # Los integrados y los conectores, que si se buscan a ojo, conservan
        # su rotulo a 1.0/0.15.
        t = fp.Reference()
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        t.SetTextThickness(mm(0.15))
        if clave in ("r", "c", "tp"):
            t.SetVisible(False)
        elif ref in ("U5", "U6", "U7"):
            # Los tres DAC van en columna a 6.5 mm de paso y el rotulo de
            # stock se dibuja 3.5 mm por encima del cuerpo: cae encima de la
            # silueta del vecino. Centrado sobre el propio cuerpo (4.4 mm de
            # ancho, el texto mide 1.9) no pisa a nadie.
            t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        elif ref == "U12":
            # Mismo problema que los DAC, con dos diferencias. La primera es
            # quien llego despues: C_IV4 (la compensacion del I/V, ver
            # simulations/vco/iv_stage.py) cae a dx=-2, dy=-5 de U12, y el
            # rotulo de stock se dibuja por ARRIBA -- justo encima de su pad.
            # El DRC lo saca como silk_over_copper y este script no perdona
            # avisos sin explicar.
            #
            # La segunda es que a U12 NO se le puede aplicar el truco de los
            # DAC. Es un SOT-223 y su pestana termica ocupa casi todo el
            # cuerpo: centrar el texto ahi cambia un silk_over_copper por
            # otro, sobre su propio cobre.
            #
            # Medido el vecindario: arriba-izquierda esta C_IV4, abajo C9 a
            # 7 mm. La derecha PARECE libre de componentes, y no lo esta de
            # cobre: un SOT-223 saca sus tres pines por el costado, asi que
            # correr el rotulo en x lo lleva directo al pin 2 (probado: cambio
            # un silk_over_copper por otro).
            #
            # La salida es la diagonal arriba-derecha: por encima de la fila
            # de pines (que estan a la altura del cuerpo) y a la derecha de
            # C_IV4. Verificado con el DRC, no a ojo.
            t.SetPosition(pcbnew.VECTOR2I(mm(x + 3.5), mm(y - 4.0)))
        board.Add(fp)
        for pad in fp.Pads():
            red = nets.get(f"{ref}-{pad.GetNumber()}")
            if red:
                pad.SetNet(board.FindNet(red))

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
    def zona(red: str, capa, puntos: list[tuple[float, float]]):
        z = pcbnew.ZONE(board)
        z.SetLayer(capa)
        z.SetNet(board.FindNet(red))
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        # Las motas de cobre de menos de 1 mm2 que deja el relleno entre
        # pistas se BORRAN, no se cuentan como isla. No es maquillar el
        # criterio: una mota de 0.7x0.7 mm no devuelve corriente de nadie, y
        # si estuviera conectada a algun pad borrarla lo dejaria suelto y lo
        # cantaria el conteo de tramos sin rutear. Un corte de verdad del
        # plano son cientos de mm2 y sigue apareciendo como isla aparte.
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_AREA)
        z.SetMinIslandArea(mm(1.0) * mm(1.0))
        z.SetIsFilled(False)
        v = pcbnew.VECTOR_VECTOR2I()
        for x, y in puntos:
            v.append(pcbnew.VECTOR2I(mm(x), mm(y)))
        z.AddPolygon(v)
        board.Add(z)
        return z

    # GNDA en In1: todo el contorno de la placa MENOS la esquina de la isla.
    # Los dos vertices que doblan la esquina (ISLA_X1+G, ISLA_Y1-G) son el
    # borde real que da a GNDD; el resto del borde de la isla coincide con el
    # borde de la placa y no necesita hueco. El recorte no es decorativo: es
    # lo que mantiene separados en PLANTA el retorno analogico y el digital,
    # aunque ahora vivan en capas distintas.
    zona("GNDA", CAPA_GNDA, [
        (MARGEN, MARGEN), (W - MARGEN, MARGEN), (W - MARGEN, H - MARGEN),
        (ISLA_X1 + G, H - MARGEN), (ISLA_X1 + G, ISLA_Y1 - G),
        (MARGEN, ISLA_Y1 - G),
    ])
    # GNDD en In2, junto con la potencia: el retorno digital solo tiene que
    # devolver corriente logica y le sobra con la esquina de la isla.
    zona("GNDD", CAPA_GNDD, [
        (MARGEN, ISLA_Y1 + G), (ISLA_X1 - G, ISLA_Y1 + G),
        (ISLA_X1 - G, H - MARGEN), (MARGEN, H - MARGEN),
    ])

    # El vertido termico de U13: una zona SIN RED en F.Cu, la misma clase de
    # cobre que los cuatro lands del EP. Une termicamente el termometro con
    # la esquina del QFN de la voz 2 sin unirlos electricamente. Al no tener
    # red, el relleno guarda margen contra TODO el cobre de la placa, asi que
    # las pistas que el router meta por ahi lo recortan en vez de chocar con
    # el; lo que quede sigue conduciendo calor.
    ter = pcbnew.ZONE(board)
    ter.SetLayer(pcbnew.F_Cu)
    ter.SetLocalClearance(mm(CLEARANCE))
    ter.SetMinThickness(mm(0.2))
    ter.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_AREA)
    ter.SetMinIslandArea(mm(0.5) * mm(0.5))
    ter.SetIsFilled(False)
    v = pcbnew.VECTOR_VECTOR2I()
    for x, y in VERTIDO_U13:
        v.append(pcbnew.VECTOR2I(mm(x), mm(y)))
    ter.AddPolygon(v)
    board.Add(ter)

    # In2 lleva la potencia Y el vertido de GNDD. Dentro de la esquina de
    # la isla digital se le prohiben las PISTAS: sin eso, el ruteo de
    # potencia cruza el vertido de GNDD y lo parte en dos trozos que el DRC
    # cuenta como conexion abierta (y que ademas obligan al retorno digital
    # a rodear). Fuera de la isla In2 sigue libre; la potencia vive en el
    # rincon opuesto y no necesita pasar por aqui.
    ka = pcbnew.ZONE(board)
    ka.SetLayer(CAPA_GNDD)
    ka.SetIsRuleArea(True)
    ka.SetDoNotAllowTracks(True)
    ka.SetDoNotAllowVias(False)
    ka.SetDoNotAllowZoneFills(False)
    ka.SetDoNotAllowPads(False)
    ka.SetDoNotAllowFootprints(False)
    v = pcbnew.VECTOR_VECTOR2I()
    for x, y in ((0.0, ISLA_Y1 - G), (ISLA_X1 + G, ISLA_Y1 - G),
                 (ISLA_X1 + G, H), (0.0, H)):
        v.append(pcbnew.VECTOR2I(mm(x), mm(y)))
    ka.AddPolygon(v)
    board.Add(ka)

    # "In1 no se toca" NO se dice con un area de reglas de KiCad. Se probo:
    # un keepout de placa entera sobre In1 se exporta como un wire_keepout
    # que cubre todo, y Freerouting se atasca en seco -- 200 conexiones sin
    # rutear desde la pasada 4 hasta la 139, sin moverse. Se dice en el DSN,
    # marcando In1 como capa de POTENCIA (ver _ajustar_dsn), que es el
    # idioma que Specctra tiene para esto: con eso el router baja de 222 a 80
    # en 14 pasadas. Del lado de KiCad lo vigila revisar(), contando pistas.

    reglas = board.GetDesignSettings()
    reglas.m_TrackMinWidth = mm(ANCHO)
    reglas.m_MinClearance = mm(CLEARANCE)
    # Los minimos de via tambien bajan, y con los numeros del fabricante, no
    # con los que le convengan al ruteo: el DRC tiene que seguir siendo un
    # examen de verdad. El anillo de una via 0.45/0.20 mide (0.45-0.20)/2 =
    # 0.125 mm, asi que el minimo de anillo se pone justo ahi -- si alguien
    # encoge la via sin encoger el taladro, salta.
    # El margen de TALADRO tambien venia del default de KiCad (0.25 mm) y no
    # de nadie mas. El fabricante publica 0.20 de taladro de via a pista y
    # 0.20 de taladro a taladro. Con via 0.45/0.20 el anillo mide 0.125, asi
    # que un vecino a CLEARANCE del cobre queda a 0.125+0.11 = 0.235 del
    # taladro: por encima de los 0.20 que pide el fabricante y por debajo de
    # los 0.25 que pedia el default. Eran 108 infracciones de una regla que
    # nos habiamos inventado nosotros.
    reglas.m_HoleClearance = mm(HOLE_CLEARANCE)
    reglas.m_HoleToHoleMin = mm(HOLE_CLEARANCE)
    reglas.m_ViasMinSize = mm(VIA_D)
    reglas.m_MinThroughDrill = mm(VIA_DRILL)
    reglas.m_ViasMinAnnularWidth = mm((VIA_D - VIA_DRILL) / 2)
    # Serigrafia: los minimos que publica el fabricante, no los de KiCad
    # (0.8/0.08). Si algun rotulo baja de aqui, el DRC lo canta.
    reglas.m_MinSilkTextHeight = mm(1.0)
    reglas.m_MinSilkTextThickness = mm(0.15)
    # m_MinClearance NO basta: el DRC de verdad (kicad-cli, no este script)
    # aplica el margen de la NETCLASS "Default", que nace en 0.2 mm y se
    # queda ahi si no se toca aparte. Ademas es lo que lee el exportador de
    # DSN, o sea lo que Freerouting cree que son las reglas -- sin esta
    # linea el router rutea a 0.2 y el DRC pide 0.2: coincide por suerte,
    # pero la anchura de pista (0.2) SI hay que decirsela.
    clase = board.GetAllNetClasses()["Default"]
    clase.SetClearance(mm(CLEARANCE))
    clase.SetTrackWidth(mm(ANCHO))
    clase.SetViaDiameter(mm(VIA_D))
    clase.SetViaDrill(mm(VIA_DRILL))

    pcbnew.SaveBoard(PCB, board)
    return board


# Reglas de taladro que KiCad trae como AVISO y aqui son ERROR. No es un
# gusto: las dos describen taladros que la fresa no puede hacer.
#
#   holes_co_located  dos taladros en el mismo sitio -- una via dentro del
#                     agujero de un pad PTH. La broca pasa dos veces por el
#                     mismo punto y el segundo paso rompe el barril del
#                     primero.
#   hole_to_hole      dos taladros a menos de 0.20 mm de pared a pared, que
#                     es el minimo publicado por el fabricante. Por debajo,
#                     el material entre los dos se desmigaja.
#
# En la ronda anterior la placa llevaba 15 vias DENTRO de taladros PTH y 3
# pares de vias por debajo del minimo, y el gate no se entero porque el DRC
# corre con --severity-error y estas dos venian de fabrica como "warning".
# Subirlas a error es lo que convierte el gate en un examen de verdad.
#
# Van en el .kicad_pro, no en el .kicad_pcb: es donde KiCad guarda las
# severidades, y el binding de Python no las expone (m_DRCSeverities llega
# como un puntero opaco). Se parchea el JSON, y AL FINAL de todo: dentro de
# un mismo proceso, la primera CreateEmptyBoard() deja cacheado un proyecto
# con los valores de fabrica y cada SaveBoard() posterior lo vuelve a
# escribir encima -- medido, no supuesto. Quien lee el fichero de verdad es
# el kicad-cli del gate, que es otro proceso y lo lee de disco.
SEVERIDADES = {"hole_to_hole": "error", "holes_co_located": "error"}


def _severidades_drc() -> None:
    ruta = PCB[:-len(".kicad_pcb")] + ".kicad_pro"
    with open(ruta, encoding="utf-8") as fh:
        proyecto = json.load(fh)
    proyecto["board"]["design_settings"]["rule_severities"].update(SEVERIDADES)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(proyecto, fh, indent=2)
        fh.write("\n")          # como lo deja KiCad: el diff son 2 lineas


def _dist_seg(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / L))
    return ((p[0] - (a[0]+t*dx))**2 + (p[1] - (a[1]+t*dy))**2) ** 0.5


# Las siete costuras que hay que RESERVAR antes de rutear, con su motivo.
# Son los pads de masa de los dos encapsulados de paso fino, y los unicos
# que el router deja sin salida si llega antes que ellos:
#
#   U1..U4 pin 20 (GNDA)  -- costado derecho del QFN, con un vecino de otra
#     red a 0.4 mm por arriba y otro por abajo. Su unica salida es hacia
#     afuera, y hacia afuera esta el desacoplo de +5V a 5.6 mm. Es un
#     pasillo de poco mas de 1 mm y el router lo llena con el abanico de
#     escape de las senales.
#   U5..U7 pin 4 (GNDA)   -- costado izquierdo del TSSOP, y a su izquierda
#     el desacoplo de +5V. El hueco entre los dos pads mide 1.45 mm: cabe
#     una via, pero solo si llega primero.
#
# SOLO MASA, y esto se midio: se probo extender el mecanismo a ESCAPES de
# senal para el abanico del costado derecho del QFN (pines 21 y 22, la red
# de VREF, que son los que mas veces se quedan sin cerrar) y sale PEOR.
#
#   sin escapes de senal (cinco corridas):  4, 5, 8, 9, 10 abiertas
#   con 8 escapes (pines 21, 22):           12
#   con 20 escapes (+ pines 2, 3, 4):       16
#
# El motivo es que el anillo del QFN no tiene sitio de sobra: una via
# reservada para un pin le quita al router justo el hueco que necesita para
# el fanout de sus vecinos, y como los 32 pines salen por el mismo anillo,
# se pierde mas de lo que se gana. Con la MASA no pasa: esos pines no tienen
# ninguna alternativa (el pasillo mide 1-1.45 mm y da para una via, no para
# un abanico), asi que reservarla es ganancia neta.
#
# Y el FANOUT COMPLETO -- una via por pin en tres coronas escalonadas
# alrededor de cada QFN -- tampoco entra, aunque parezca el paso natural
# despues de lo anterior. Se implemento entero y se midio; dos muros, los
# dos de aritmetica y no de mana:
#
#   1. NO CABE. Para que el rabito de un pin pase al lado de la via de su
#      vecino hacen falta VIA_D/2 + CLEARANCE + ANCHO/2 = 0.55 mm, y el paso
#      del QFN es 0.40. La via mas gorda que dejaria pasar al vecino mide
#      0.30 mm -- taladro laser, proceso HDI, otra liga de fabricacion. Con
#      las tres coronas los que COMPARTEN corona quedan a 1.2 mm y esos si
#      caben, pero los rabitos de las coronas de fuera tienen que cruzar la
#      de dentro y ahi se acaba: de 119 vias de fanout, entraron 91 y 28 se
#      quedaron fuera.
#   2. AHOGA AL ROUTER. Con esas 91 vias en el modelo, Freerouting paso de
#      ~15 s por pasada a ~8 minutos: veinte horas por ronda. Es el mismo
#      efecto que ya se habia medido con las ~95 vias de coser todas las
#      masas antes de rutear, y por eso aquella se movio a despues.
#
# Moraleja de las rondas 5 y 6, que es la que vale para el proximo QFN:
# pre-colocar cobre ayuda donde la geometria fuerza UNA solucion (los siete
# pines de masa de aqui arriba) y estorba donde hay varias, porque le quita
# al router sitio que el reparte mejor. El fanout completo de un 0.4 mm no
# es cuestion de insistir: es via-in-pad o HDI, y eso es decision de
# proceso, no de layout.
#
# Se ponen antes del ruteo: el router las ve como obstaculo y da la vuelta;
# puestas despues, no hay por donde. Son siete vias y el modelo del router
# apenas lo nota (con las ~95 de toda la placa, cada pasada pasaba de 15 s
# a tres minutos).
COSTURAS_RESERVADAS = ({(f"U{i}", "20") for i in (1, 2, 3, 4)}
                       | {(f"U{i}", "4") for i in (5, 6, 7)}
                       # Las CUATRO masas virtuales de los I/V (pines 3, 5, 10
                       # y 12 de U9: la entrada + de cada unidad, atada a
                       # GNDA). No es un pad de masa cualquiera: en un
                       # amplificador de transimpedancia esa entrada ES la
                       # referencia que define el punto virtual, y su
                       # impedancia hasta el plano forma parte del circuito --
                       # lo que se cuele ahi sale por el jack de esa voz.
                       #
                       # Entran aqui porque con las ocho piezas nuevas el
                       # centro se congestiono y el pin 12 se quedo sin
                       # camino: habia vias de GNDA a 3.27 y 5.39 mm, pero
                       # despues de rutear ya no habia por donde llegar. Es
                       # justo el caso que describe la moraleja de arriba --
                       # geometria que fuerza UNA solucion -- y por eso se
                       # reserva antes en vez de esperar a que sobre sitio.
                       # Van las cuatro y no solo la que fallo: las cuatro son
                       # el mismo nodo critico y cual falla depende del azar
                       # del router.
                       | {("U9", p) for p in ("3", "5", "10", "12")}
                       # La segunda masa de U7 (la primera, el pin 4, ya
                       # estaba). Mismo motivo: se quedo sin camino con vias
                       # a 1.60 mm.
                       | {("U7", "16")})


def _check_escape() -> None:
    """El rabito de un pin tiene que poder pasar al lado de la via del vecino.

    Es la condicion que decide si un QFN de 0.4 mm de paso se deja escapar, y
    la que bloqueo las rondas 5 y 6 con las reglas viejas. Si alguien vuelve
    a subir VIA_D, CLEARANCE o ANCHO, esto salta antes de generar cobre en
    vez de dejar once conexiones al aire y parecer mala suerte del router.
    """
    paso = 0.4                      # paso del QFN-32 4x4 del SSI2130
    hace_falta = VIA_D / 2 + CLEARANCE + ANCHO / 2
    assert hace_falta < paso, (
        f"con via {VIA_D}, margen {CLEARANCE} y pista {ANCHO} el escape pide "
        f"{hace_falta:.3f} mm y el paso del QFN es {paso}: no cabe")


def _pads_sin_plano(board, net: str) -> list:
    """Pads de `net` cuyo cobre NO llega a ninguna via, o sea al plano.

    La pregunta correcta no es "tiene una via cerca" ni "le sale un rabito",
    que es lo que preguntaban las dos versiones anteriores y por eso daban
    por resueltos pads que el DRC seguia contando sueltos. La pregunta es si
    el trozo de cobre del que forma parte el pad TOCA una via en algun sitio:
    todo el cobre es SMD en F.Cu y el plano esta dentro de la placa, asi que
    sin via no hay contacto, por muchos rabitos que haya.

    Se arma el grafo del neto (pads, pistas y vias, uniendo lo que se toca
    en la MISMA capa) y se devuelven los pads de los grupos que no tienen
    ninguna via.
    """
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()
            if p.GetNetname() == net]
    pistas = [t for t in board.GetTracks() if t.GetNetname() == net
              and not isinstance(t, pcbnew.PCB_VIA)]
    vias = [t for t in board.GetTracks() if t.GetNetname() == net
            and isinstance(t, pcbnew.PCB_VIA)]
    nodos = pads + pistas + vias
    padre = list(range(len(nodos)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    def unir(i, j):
        padre[raiz(i)] = raiz(j)

    def caja(p):
        c = p.GetBoundingBox()
        return (c.GetLeft() / 1e6 - 0.02, c.GetTop() / 1e6 - 0.02,
                c.GetRight() / 1e6 + 0.02, c.GetBottom() / 1e6 + 0.02)

    cajas = [caja(p) for p in pads]
    extremos = [((t.GetStart().x / 1e6, t.GetStart().y / 1e6),
                 (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6), t.GetLayer())
                for t in pistas]
    puntos_via = [(v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)
                  for v in vias]
    n_p, n_t = len(pads), len(pistas)

    def dentro(q, c):
        return c[0] <= q[0] <= c[2] and c[1] <= q[1] <= c[3]

    for i, (a, b, capa) in enumerate(extremos):        # pista <-> pad
        for j, c in enumerate(cajas):
            if capa == pads[j].GetLayer() or pads[j].GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                if dentro(a, c) or dentro(b, c):
                    unir(n_p + i, j)
    for i, (a, b, capa) in enumerate(extremos):        # pista <-> pista
        for k in range(i + 1, n_t):
            c, d, capa2 = extremos[k]
            if capa == capa2 and (_dist_seg(a, c, d) < 0.02
                                  or _dist_seg(b, c, d) < 0.02
                                  or _dist_seg(c, a, b) < 0.02
                                  or _dist_seg(d, a, b) < 0.02):
                unir(n_p + i, n_p + k)
    for v, q in enumerate(puntos_via):                 # via <-> pad y pista
        for j, c in enumerate(cajas):
            if dentro(q, c):
                unir(n_p + n_t + v, j)
        for i, (a, b, _capa) in enumerate(extremos):
            if _dist_seg(q, a, b) < VIA_D / 2:
                unir(n_p + n_t + v, n_p + i)

    con_via = {raiz(n_p + n_t + v) for v in range(len(vias))}
    return [p for j, p in enumerate(pads) if raiz(j) not in con_via]


def _abanico(px: float, py: float, ux: float, uy: float):
    """Sitios candidatos para la via de un pad, del mas cercano al mas lejano.

    (ux,uy) es el rumbo que se aleja del centro del encapsulado. A cada
    distancia se prueba ese rumbo primero y luego se abre en abanico a los
    dos lados, hasta darse la vuelta.

    EL CENTRO DEL PAD NO ES UN SITIO. Lo fue durante siete rondas -- este
    generador empezaba probando (px,py) -- y de ahi salieron las 15 vias
    metidas dentro del taladro de un jack o de un IDC y las 32 vias debajo
    de un pad SMD que encontro la revision. Una via en el centro de un pad
    PTH es la misma broca pasando dos veces por el mismo punto; una via
    debajo de un pad SMD es via-in-pad, que exige taponar y planarizar y que
    ya se habia descartado en la ronda 3 por ser decision de fabricacion.
    La via va AL LADO del pad y un rabito de medio milimetro los une: el
    pasillo que da para una via (la medida de la ronda 4) da para eso.

    Por eso la primera distancia baja a 0.75 mm y los pasos se afinan: sin
    el centro, el sitio bueno esta justo al borde del pad y hay que poder
    apuntarle.
    """
    for d in (0.75, 0.9, 1.05, 1.2, 1.4, 1.7, 2.1, 2.6, 3.2, 3.9, 4.6):
        for grados in (0, 30, -30, 60, -60, 90, -90, 130, -130, 180):
            r = math.radians(grados)
            vx = ux * math.cos(r) - uy * math.sin(r)
            vy = ux * math.sin(r) + uy * math.cos(r)
            yield px + vx * d, py + vy * d


def coser_masas(reservadas=False) -> int:
    """Una via de bajada al plano por cada pad de masa que no la tenga ya.

    Todo el cobre de esta placa es SMD en F.Cu y los dos planos de masa
    viven en capas internas (GNDA en In1, GNDD en In2): un pad de GNDA sin
    via al lado no toca su plano, lo mira desde arriba y se queda suelto.
    Freerouting pone algunas pero no llega a todas -- sin este paso dejaba
    7 pads de masa al aire.

    Va DESPUES de rutear, no antes. Metidas antes, esas ~95 vias entran en
    el modelo del router y cada pasada pasa de 15 s a casi 3 minutos, o sea
    nueve horas por corrida: para lo unico que hacen falta es para tocar el
    plano, y eso no necesita router. Aqui se comprueba el margen contra
    TODO lo que hay puesto -- pads, pistas y vias de otras redes -- que es
    lo que el router habria hecho por ellas.

    Una via de masa no agujerea el plano: es del mismo neto y el vertido la
    abraza. Por eso se permiten tambien dentro de la cruz central
    protegida, donde las pistas de senal no.

    La via se busca ALEJANDOSE del centro del encapsulado: hacia afuera hay
    hueco, hacia adentro estan los otros pines (y, en el QFN, el land del
    EP, que no se puede tocar ni de cerca).

    Y NUNCA ENCIMA DE UN PAD. El margen electrico (lejos()) se salta el
    cobre de la propia red, que es lo correcto para un corto y lo
    equivocado para una broca: taladro contra taladro y via contra pad
    son separaciones MECANICAS y no saben de redes. Eso lo comprueba
    taladro_libre(), aparte, y por eso existe.
    """
    board = pcbnew.LoadBoard(PCB)
    r_via = VIA_D / 2 + CLEARANCE
    cajas = [(p.GetNetname(), p.GetBoundingBox()) for fp in board.GetFootprints()
             for p in fp.Pads()]
    # Los dos censos MECANICOS, sin red: todos los taladros de la placa
    # (pads PTH y NPTH, mas las vias que se vayan poniendo) y todo el cobre
    # de pad. Un taladro nuevo pide HOLE_CLEARANCE contra cualquier otro,
    # aunque sean del mismo neto, y el cobre de una via no puede pisar el
    # pad de nadie -- ni el suyo.
    taladros = [(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6,
                 p.GetDrillSizeX() / 2e6)
                for fp in board.GetFootprints() for p in fp.Pads()
                if p.GetDrillSizeX() > 0]
    # TODOS los pads, tengan taladro o no. La primera version de esta ronda
    # solo miraba los pads SMD y dejo cuatro vias de masa taladradas sobre
    # la CORONA de los jacks: taladros legales (0.24 mm de hueco) pero
    # barril atravesando cobre soldable, que es via-in-pad igual. Lo que
    # decide no es el tipo de pad, es que haya cobre de pad donde va el
    # barril.
    pads_cobre = [p.GetBoundingBox()
                  for fp in board.GetFootprints() for p in fp.Pads()]
    segs, segs_todas, puntos = [], [], []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            puntos.append((t.GetNetname(), t.GetPosition().x / 1e6,
                           t.GetPosition().y / 1e6, VIA_D / 2))
            taladros.append((t.GetPosition().x / 1e6, t.GetPosition().y / 1e6,
                             t.GetDrillValue() / 2e6))
        else:
            segs_todas.append((t.GetNetname(),
                               (t.GetStart().x / 1e6, t.GetStart().y / 1e6),
                               (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6),
                               t.GetWidth() / 2e6))
        if not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.F_Cu:
            # SOLO F.Cu. El rabito que une el pad con su via vive en F.Cu, y
            # una pista de B.Cu o de In2 por debajo no le estorba: son capas
            # distintas. Meterlas todas en el mismo saco (lo que hacia la
            # primera version) daba por ocupado medio anillo del QFN y
            # dejaba 13 pads de masa sin bajada que en realidad si cabian.
            segs.append((t.GetNetname(),
                         (t.GetStart().x / 1e6, t.GetStart().y / 1e6),
                         (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6),
                         t.GetWidth() / 2e6))

    # Cerca() recorta el cobre de la placa a lo que hay a menos de 8 mm del
    # pad que se esta cosiendo. Sin ese recorte, cada candidato compara
    # contra ~500 pads, ~1400 pistas y ~250 vias, y probar 90 candidatos por
    # pad en 90 pads no termina nunca. Con el, cada comparacion mira dos
    # docenas de cosas.
    cerca_cajas = cerca_segs = cerca_todas = cerca_puntos = None
    cerca_taladros = cerca_pads = None

    def cerca(px: float, py: float) -> None:
        nonlocal cerca_cajas, cerca_segs, cerca_todas, cerca_puntos
        nonlocal cerca_taladros, cerca_pads
        R = 8.0
        cerca_cajas = [(n, c) for n, c in cajas
                       if abs((c.GetLeft() + c.GetRight()) / 2e6 - px) < R
                       and abs((c.GetTop() + c.GetBottom()) / 2e6 - py) < R]
        cerca_segs = [s for s in segs
                      if _dist_seg((px, py), s[1], s[2]) < R]
        cerca_todas = [s for s in segs_todas
                       if _dist_seg((px, py), s[1], s[2]) < R]
        cerca_puntos = [p for p in puntos
                        if abs(p[1] - px) < R and abs(p[2] - py) < R]
        cerca_taladros = [t for t in taladros
                          if abs(t[0] - px) < R and abs(t[1] - py) < R]
        cerca_pads = [c for c in pads_cobre
                      if abs((c.GetLeft() + c.GetRight()) / 2e6 - px) < R
                      and abs((c.GetTop() + c.GetBottom()) / 2e6 - py) < R]

    def taladro_libre(x: float, y: float) -> bool:
        """Un taladro nuevo en (x,y), contra la geometria y no contra la red.

        Dos comprobaciones que lejos() no puede hacer porque se salta el
        cobre de la propia red:

          * pared de taladro a pared de taladro >= HOLE_CLEARANCE contra
            TODOS los taladros de la placa. Dos vias de GNDA que se pisan
            son igual de irrealizables que dos de redes distintas -- la
            broca no lee el netlist. Aqui es donde se colaban las 15 vias
            plantadas dentro del taladro de un jack (hueco de -0.81 mm: los
            dos agujeros solapados).
          * el cobre de la via (no solo el taladro) no toca NINGUN pad --
            ni SMD ni la corona de un PTH. Via-in-pad obliga a taponar y
            planarizar, y esa decision de fabricacion ya se descarto; que
            el pad sea de la misma red no lo hace mas barato, y que el
            taladro quede al lado tampoco: por ahi se cuela la soldadura
            del pin del jack.

        Aqui el pad se mide por su CAJA y no por su forma, o sea de mas: es
        una funcion que ELIGE sitio y pasarse de prudente solo le cuesta
        descartar un candidato y probar el siguiente. Quien juzga la placa
        terminada es revisar_taladros(), y ese si pregunta por la forma real
        (un pad redondo tiene esquinas de caja que no son pad).
        """
        r = VIA_DRILL / 2
        for tx, ty, tr in cerca_taladros:
            if (x - tx) ** 2 + (y - ty) ** 2 < (r + tr + HOLE_CLEARANCE) ** 2:
                return False
        for c in cerca_pads:
            dx = max(0.0, c.GetLeft() / 1e6 - x, x - c.GetRight() / 1e6)
            dy = max(0.0, c.GetTop() / 1e6 - y, y - c.GetBottom() / 1e6)
            if dx * dx + dy * dy < (VIA_D / 2) ** 2:
                return False
        return True

    def lejos(x, y, net: str, margen: float, todas=False) -> bool:
        for otra, caja in cerca_cajas:
            if otra == net:
                continue
            dx = max(0.0, caja.GetLeft() / 1e6 - x, x - caja.GetRight() / 1e6)
            dy = max(0.0, caja.GetTop() / 1e6 - y, y - caja.GetBottom() / 1e6)
            if dx * dx + dy * dy < margen * margen:
                return False
        for otra, a, b, w in (cerca_todas + cerca_segs if todas else cerca_segs):
            if otra != net and _dist_seg((x, y), a, b) < margen + w:
                return False
        return all(otra == net or ((x - vx)**2 + (y - vy)**2) ** 0.5 >= margen + r
                   for otra, vx, vy, r in cerca_puntos)

    def libre(px, py, x: float, y: float, net: str) -> bool:
        """La via y el rabito que la une al pad, los dos con su margen.

        El rabito se comprueba por muestreo cada 0.2 mm en vez de con
        geometria exacta: mide 3 mm como mucho y el pad mas fino de la
        placa (el del QFN, 0.2 mm) es mas ancho que el paso de muestreo.
        """
        a, b = (px, py), (x, y)
        largo = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
        pasos = int(largo / 0.2) + 1
        return all(lejos(a[0] + (b[0] - a[0]) * i / pasos,
                         a[1] + (b[1] - a[1]) * i / pasos,
                         net, CLEARANCE + ANCHO / 2)
                   for i in range(1, pasos + 1))

    def camino(px, py, x, y, net, via=True, salida=None):
        """Tramos del rabito pad->destino, o None si no hay por donde.

        Recto primero y luego las dos eles. Con solo la recta (la version
        anterior) el rabito chocaba casi siempre en cuanto el destino no
        estaba en linea de vista; con las eles, el pad de masa encuentra la
        vuelta por encima o por el lado.

        `via=False` cuando el destino es cobre que YA existe (otra via, o el
        extremo de una pista de la misma red): ahi no se va a taladrar nada,
        asi que exigir el margen de una via en ese punto es pedirle sitio a
        algo que no lo necesita -- y era justo lo que hacia fallar todos los
        enganches en las zonas apretadas.
        """
        if via and not (lejos(x, y, net, r_via, todas=True)
                        and taladro_libre(x, y)):
            return None
        # Los pines de un QFN salen de costado y tienen un vecino de otra
        # red a 0.4 mm por cada lado: cualquier camino que empiece yendo
        # "hacia el destino" les pasa por encima. Por eso se prueban tambien
        # caminos que primero SALEN del chip (rumbo ux,uy) y luego doblan.
        rutas = [(), ((x, py),), ((px, y),)]
        if salida:
            for e in (1.0, 1.7):
                ex, ey = px + salida[0] * e, py + salida[1] * e
                rutas += [((ex, ey),), ((ex, ey), (x, ey)), ((ex, ey), (ex, y))]
        for esquinas in rutas:
            puntos_cam = [(px, py), *esquinas, (x, y)]
            tramos = [(puntos_cam[i], puntos_cam[i + 1])
                      for i in range(len(puntos_cam) - 1)
                      if puntos_cam[i] != puntos_cam[i + 1]]
            if all(libre(a[0], a[1], b[0], b[1], net) for a, b in tramos):
                return tramos
        return None

    def poner(tramos, net) -> None:
        for a, b in tramos:
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
            t.SetWidth(mm(ANCHO))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(board.FindNet(net))
            board.Add(t)
            segs.append((net, a, b, ANCHO / 2))

    pendientes = {_xy(p) for p in _pads_sin_plano(board, "GNDA")
                  + _pads_sin_plano(board, "GNDD")}
    nuevas = faltan = enganchadas = 0
    for fp in board.GetFootprints():
        fx, fy = fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6
        for pad in fp.Pads():
            net = pad.GetNetname()
            px, py = _xy(pad)
            if reservadas:
                # Modo pre-ruteo: solo los pines de la lista, que hoy son
                # los siete de masa (ver COSTURAS_RESERVADAS).
                if (fp.GetReference(), pad.GetNumber()) not in COSTURAS_RESERVADAS:
                    continue
            else:
                if net not in ("GNDA", "GNDD"):
                    continue
                if fp.GetReference() in FUERA_DEL_PLANO:
                    continue      # su plano no pasa por debajo: va por pista
                if (px, py) not in pendientes:
                    continue      # su cobre ya toca una via: llega al plano
            largo = ((px - fx) ** 2 + (py - fy) ** 2) ** 0.5
            if largo < 0.05:
                # El pad ESTA en el centro de su huella -- el manguito de un
                # jack, el pad de un punto de prueba -- asi que no existe un
                # "hacia afuera del encapsulado" y el rumbo salia (0,0): el
                # abanico entero degeneraba en un unico candidato, el propio
                # centro del pad. Con el yield del centro delante nadie lo
                # noto durante siete rondas, y de ahi salieron las ocho vias
                # clavadas en el manguito de los jacks. Se sale hacia afuera
                # de la PLACA y el abanico barre el resto de rumbos.
                fx, fy = W / 2, H / 2
                largo = ((px - fx) ** 2 + (py - fy) ** 2) ** 0.5 or 1.0
            ux, uy = (px - fx) / largo, (py - fy) / largo
            cerca(px, py)
            # Se prueba en ABANICO, no en una sola recta: primero el sitio
            # mas cercano, y a cada distancia el rumbo que se aleja del chip
            # y luego los que se van abriendo a los lados. Con una sola recta
            # (la version anterior) se quedaban 37 pads de masa sin bajada
            # entre el cobre que ya habia puesto el router; con el abanico,
            # casi ninguno.
            sitio = rabito = None
            for c in _abanico(px, py, ux, uy):
                rabito = camino(px, py, c[0], c[1], net, salida=(ux, uy))
                if rabito is not None:
                    sitio = c
                    break
            if sitio is None:
                # No cabe una via nueva: que se agarre a una que ya exista.
                # Un pad de masa no necesita bajada PROPIA, necesita LLEGAR
                # al plano, y varios pads compartiendo via es lo normal en
                # una placa hecha a mano. Se busca la via de su misma red
                # mas cercana y se le tira un rabito, si el camino esta
                # limpio.
                # Vale cualquier cobre de la misma red: una via, o el
                # extremo de una pista que el router ya dejo puesta. Varios
                # de estos pads tienen una pista de GNDA a 1.2 mm y lo unico
                # que les falta es el saltito.
                # Solo VIAS como destino. Se probo permitir tambien el
                # extremo de una pista de la misma red y no vale: esa pista
                # puede ser justo otro trozo que tampoco llega al plano, y
                # el pad se engancha a un vecino tan huerfano como el (se
                # veia en que cada vuelta "colgaba" los mismos 3 pads sin
                # que bajara el conteo). Una via siempre llega.
                vecinas = sorted(
                    [(vx, vy) for otra, vx, vy, _r in puntos if otra == net],
                    key=lambda q: (q[0]-px)**2 + (q[1]-py)**2)
                vecinas = [q for q in vecinas
                           if (q[0]-px)**2 + (q[1]-py)**2 < 36.0][:12]
                enganche = next(filter(None, (camino(px, py, q[0], q[1], net, via=False, salida=(ux, uy))
                                              for q in vecinas)), None)
                if enganche is None:
                    faltan += 1
                    continue
                poner(enganche, net)
                enganchadas += 1
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(sitio[0]), mm(sitio[1])))
            v.SetDrill(mm(VIA_DRILL))
            v.SetWidth(mm(VIA_D))
            v.SetNet(board.FindNet(net))
            board.Add(v)
            puntos.append((net, sitio[0], sitio[1], VIA_D / 2))
            taladros.append((sitio[0], sitio[1], VIA_DRILL / 2))
            nuevas += 1
            poner(rabito, net)
    pcbnew.SaveBoard(PCB, board)
    print(f"{'costuras reservadas' if reservadas else 'masas cosidas al plano'}"
          f": {nuevas} vias nuevas, {enganchadas} pads "
          f"colgados de una via vecina"
          + (f", {faltan} pads sin sitio" if faltan else ""))
    return faltan


# ------------------------------------------------------------------ ruteo
def ajustes_freerouting(tmp: str):
    """Las dos opciones que deciden la partida, y que NO tienen flag de CLI.

    Freerouting guarda sus preferencias en un JSON de usuario
    (<temp>/freerouting/freerouting.json) y su linea de comandos solo expone
    -mp/-mt/-oit y poco mas. Las dos que aqui valen oro hay que escribirlas
    en ese fichero:

    * **fanout: enabled**. Viene APAGADO de fabrica. En esta placa todo el
      cobre es SMD en F.Cu y el plano esta en B.Cu: sin la etapa de fanout el
      router no se plantea sacar una via de escape por pad y se ahoga en el
      anillo de cada QFN. Encenderlo, con todo lo demas igual, bajo los
      tramos sin rutear de 31 a 11 en la misma placa y el mismo numero de
      pasadas. Es el cambio mas grande de toda la tanda.
    * **via_costs** (de fabrica 50, ver VIA_COSTS). En 4 capas bajar es
      barato: hay dos capas de senal y un plano solido en medio. Penalizar
      el cambio de capa solo consigue que el router se ahogue en el anillo
      de un QFN de 0.4 mm de paso en vez de escapar hacia abajo. De 30 a 8,
      en la misma placa: de ~40 conexiones sin cerrar a 24.

    Se PARCHEA el fichero, no se reescribe entero: el resto son preferencias
    del usuario (perfil, telemetria, GUI) que no son asunto de este script.
    Y se devuelve el original para poder DEJARLO COMO ESTABA al terminar --
    tocar la configuracion de una herramienta fuera del repo esta bien si es
    para la corrida, no si se queda puesto: quien abra Freerouting a mano
    despues no tiene por que encontrarse el fanout encendido.
    """
    ruta = os.path.join(tmp, "freerouting", "freerouting.json")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    try:
        with open(ruta, encoding="utf-8") as fh:
            original = fh.read()
        cfg = json.loads(original)
    except (OSError, ValueError):
        original, cfg = None, {}
    router = cfg.setdefault("router", {})
    router.setdefault("fanout", {}).update(
        {"enabled": True, "algorithm": "freerouting-fanout", "max_passes": 100})
    router.setdefault("scoring", {})["via_costs"] = VIA_COSTS
    router["max_threads"] = 1
    # y el numero de pasadas TAMBIEN va aqui: -mp de la linea de comandos
    # queda por debajo del JSON (con -mp 150 y el JSON en 40, se paro en 45).
    router["max_passes"] = PASADAS
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    print(f"freerouting: fanout ON, via_costs {VIA_COSTS}, max_passes {PASADAS}\n"
          f"  (parche temporal sobre {ruta}; se restaura al terminar)")
    return ruta, original


def restaurar_freerouting(ruta: str, original: str | None) -> None:
    """Deja el freerouting.json del usuario como estaba antes de la corrida."""
    if original is None:
        with contextlib.suppress(OSError):
            os.remove(ruta)          # no existia: no dejamos uno nuevo
        return
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(original)


def rutear() -> None:
    """Exporta DSN, llama a Freerouting headless, importa el SES.

    El jar oficial (github.com/freerouting/freerouting, un solo .jar) NO se
    descarga desde aqui a proposito: una build reproducible no baja binarios
    de internet sola. Se le pasa por FREEROUTING_JAR.

    -mt 1 no es opcional: el propio Freerouting avisa de que su optimizador
    multihilo "is broken and it is known to generate clearance violations".
    Con los 23 hilos que coge por defecto, la primera pasada terminaba en
    0,3 s dejando las 316 conexiones sin rutear.

    Ojo con la version del jar: la 2.3.0 esta compilada para Java 25 (class
    file 69) y no arranca con el Java 21 de este equipo. La 2.1.0 si.
    """
    if not FREEROUTING or not os.path.isfile(FREEROUTING):
        sys.exit(
            "FALTA FREEROUTING.\n"
            "  Baja el jar de https://github.com/freerouting/freerouting/releases\n"
            "  (freerouting-2.1.0.jar; la 2.3.0 pide Java 25) y apunta:\n"
            "      set FREEROUTING_JAR=C:\\ruta\\freerouting-2.1.0.jar\n"
            "  Este script no lo descarga solo.")

    tmp = tempfile.gettempdir()
    ajustes, previo = ajustes_freerouting(tmp)
    try:
        _rondas(tmp)
    finally:
        restaurar_freerouting(ajustes, previo)


def _ajustar_dsn(dsn: str) -> None:
    """Dos retoques al DSN recien exportado, los dos imposibles desde KiCad.

    1. **In1 pasa a capa de POTENCIA.** KiCad exporta las cuatro capas de
       cobre como `(type signal)` y no tiene opcion para decir otra cosa.
       Specctra si: una capa `(type power)` es un plano y el router no le
       mete pistas -- que es exactamente la regla del stackup. Se probo
       primero con un area de reglas de KiCad (keepout de placa entera sobre
       In1): se exporta como wire_keepout y Freerouting se atasca en seco,
       200 conexiones sin rutear desde la pasada 4 hasta la 139 sin moverse.
       Con `(type power)` baja de 222 a 80 en 14 pasadas.
    2. **El margen del router sube 0.01 mm sobre el del DRC** (0.11 contra
       los 0.10 de CLEARANCE). Freerouting redondea sus coordenadas y deja
       pistas dos micras por debajo de lo que apunta -- una infraccion de
       DRC por pura aritmetica. Con la decima de mas el redondeo cae del
       lado bueno.

    Es un fichero temporal que acabamos de generar nosotros: no toca nada
    del repo ni de la configuracion de KiCad.
    """
    with open(dsn, encoding="utf-8") as fh:
        txt = fh.read()
    viejo = "(layer In1.Cu\n      (type signal)"
    assert viejo in txt, "el DSN no trae In1.Cu como capa de senal"
    txt = txt.replace(viejo, "(layer In1.Cu\n      (type power)", 1)
    holgado = f"(clearance {int(CLEARANCE * 1000) + 10})"
    txt = txt.replace(f"(clearance {int(CLEARANCE * 1000)})", holgado)
    # 3. El cobre de masa que ya esta puesto se marca como PROTEGIDO. KiCad
    #    exporta todo el cableado existente como (type route), que para
    #    Freerouting significa "puedes levantarlo si te estorba" -- y las
    #    costuras reservadas existen justo para que NO se las levante.
    for red in ("GNDA", "GNDD"):
        txt = txt.replace(f"(net {red})(type route)", f"(net {red})(type protect)")
    with open(dsn, "w", encoding="utf-8") as fh:
        fh.write(txt)


def _rondas(tmp: str) -> None:
    dsn = os.path.join(tmp, "sam17-vco.dsn")
    ses = os.path.join(tmp, "sam17-vco.ses")
    log = os.path.join(tmp, "sam17-vco-freerouting.log")
    # copia con la colocacion y SIN cobre: el SES de cada ronda se importa
    # siempre sobre ella, nunca encima de las pistas de la ronda anterior
    # (el SES ya trae el ruteo entero, el viejo y el nuevo).
    virgen = os.path.join(tmp, "sam17-vco-sin-rutear.kicad_pcb")
    pcbnew.SaveBoard(virgen, pcbnew.LoadBoard(PCB))

    # Freerouting es ESTOCASTICO: la misma placa y la misma configuracion,
    # dos corridas, dan entre 15 y 31 tramos sin cerrar. Por eso se guarda
    # la MEJOR ronda, no la ultima -- quedarse con la ultima es tirar a
    # cara o cruz el resultado de una hora de maquina.
    mejor = os.path.join(tmp, "sam17-vco-mejor.kicad_pcb")
    sueltos, record = None, None
    for ronda in range(1, RONDAS + 1):
        assert pcbnew.ExportSpecctraDSN(pcbnew.LoadBoard(PCB), dsn), \
            "no se exporto el DSN"
        _ajustar_dsn(dsn)
        print(f"freerouting ronda {ronda}/{RONDAS}, {PASADAS} pasadas\n"
              f"  (el avance, pasada a pasada, en {log})", flush=True)
        with open(log, "w", encoding="utf-8") as fh:
            subprocess.run([JAVA, "-jar", FREEROUTING, "-de", dsn, "-do", ses,
                            "-mp", str(PASADAS), "-mt", "1"],
                           stdout=fh, stderr=subprocess.STDOUT, text=True)
        salida = open(log, encoding="utf-8").read()
        assert os.path.isfile(ses), f"freerouting no dejo SES:\n{salida[-2000:]}"

        board = pcbnew.LoadBoard(virgen)
        assert pcbnew.ImportSpecctraSES(board, ses), "no se importo el SES"
        pcbnew.SaveBoard(PCB, board)
        # Contar SIN rellenar las zonas no vale: todo el cobre es SMD en
        # F.Cu y los ~85 pads de masa solo tocan el plano a traves del
        # vertido, asi que sin relleno salen todos "sueltos" (una ronda que
        # de verdad iba por 38 se reportaba como 100). Se rellena una copia
        # aparte: la placa que se exporta a DSN en la ronda siguiente tiene
        # que seguir siendo la de las zonas sin rellenar.
        copia = os.path.join(tmp, "sam17-vco-relleno.kicad_pcb")
        pcbnew.SaveBoard(copia, pcbnew.LoadBoard(PCB))
        board = rellenar(copia)
        antes, sueltos = sueltos, board.GetConnectivity().GetUnconnectedCount(True)
        if record is None or sueltos < record:
            record = sueltos
            pcbnew.SaveBoard(mejor, pcbnew.LoadBoard(PCB))
        print(f"  ronda {ronda}: {sueltos} tramos sin rutear "
              f"(mejor hasta ahora: {record})", flush=True)
        # Cada ronda ARRANCA del ruteo de la anterior (el DSN se exporta de la
        # placa ya ruteada y Freerouting respeta ese cobre): es rip-up y
        # re-rutear a escala de placa entera. Se para cuando cierra.
        if sueltos == 0:
            break
    if record is not None and sueltos != record:
        print(f"  me quedo con la mejor ronda ({record}), no con la ultima")
        pcbnew.SaveBoard(PCB, pcbnew.LoadBoard(mejor))


# ------------------------------------------------------------ mediciones
def _pads(board) -> dict[str, list]:
    out: dict[str, list] = {}
    for fp in board.GetFootprints():
        out[fp.GetReference()] = list(fp.Pads())
    return out


def _xy(pad) -> tuple[float, float]:
    return pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6


def _d(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def medir_dac_vco(board) -> float:
    """El camino DAC->VCO del peor par, contra la cota del presupuesto.

    Se mide de centro de encapsulado a centro de encapsulado, que es lo que
    modela dac_local_budget.LARGO_LOCAL: el largo del trozo de plano que la
    corriente de retorno del CV tiene que recorrer entre los dos chips.
    """
    centros = {fp.GetReference(): (fp.GetPosition().x / 1e6,
                                   fp.GetPosition().y / 1e6)
               for fp in board.GetFootprints()}
    peor, par = 0.0, ("", "")
    for dac in ("U5", "U6", "U7"):
        for voz in ("U1", "U2", "U3", "U4"):
            dist = _d(centros[dac], centros[voz])
            if dist > peor:
                peor, par = dist, (dac, voz)
    print(f"camino DAC->VCO, peor par: {par[0]}->{par[1]} = {peor:.1f} mm "
          f"(cota de dac_local_budget.LARGO_LOCAL: 50.0 mm)")
    u5 = max(_d(centros["U5"], centros[v]) for v in ("U1", "U2", "U3", "U4"))
    print(f"  y el que manda la afinacion (U5 -> la voz mas lejana): "
          f"{u5:.1f} mm")
    return peor


def medir_desacoplos(board) -> list[str]:
    """Cada 100 nF y cada C_TCAP contra el pin que desacopla.

    Se mide el HUECO DE COBRE entre el pad util del condensador y el pad del
    pin: borde a borde, no centro a centro. Es la lectura correcta de "a
    menos de 2 mm de su chip" -- centro a centro un 0805 arrastra sus
    propios 0.95 mm de pad y la cota de 2 mm seria geometricamente imposible
    contra un TSSOP (el pad del chip ya llega a 4.25 mm de su centro).
    """
    pads = _pads(board)

    def hueco(cref, cpin, uref, upin) -> float:
        a = [p for p in pads[cref] if p.GetNumber() == cpin][0].GetBoundingBox()
        b = [p for p in pads[uref] if p.GetNumber() == upin][0].GetBoundingBox()
        dx = max(0.0, max(a.GetLeft() - b.GetRight(), b.GetLeft() - a.GetRight()))
        dy = max(0.0, max(a.GetTop() - b.GetBottom(), b.GetTop() - a.GetBottom()))
        return (dx * dx + dy * dy) ** 0.5 / 1e6

    medidas = []
    for i in range(1, 5):
        medidas.append((f"C_TCAP{i} -> U{i}.14 (TCAP)",
                        hueco(f"C_TCAP{i}", "1", f"U{i}", "14")))
        medidas.append((f"{_DESACOPLO_5V[i]} -> U{i}.18 (V+)",
                        hueco(_DESACOPLO_5V[i], "1", f"U{i}", "18")))
        medidas.append((f"{_DESACOPLO_12V[i]} -> U{i}.8 (V-)",
                        hueco(_DESACOPLO_12V[i], "1", f"U{i}", "8")))
    for dac, c5, c33 in (("U5", "C12", "C13"), ("U6", "C14", "C15"),
                         ("U7", "C16", "C17")):
        medidas.append((f"{c5} -> {dac}.5 (+5V)", hueco(c5, "1", dac, "5")))
        medidas.append((f"{c33} -> {dac}.11 (+3V3)", hueco(c33, "1", dac, "11")))
    medidas.append(("C19 -> U13.8 (+3V3)", hueco("C19", "1", "U13", "8")))
    medidas.append(("C18 -> U10.14 (+3V3)", hueco("C18", "1", "U10", "14")))
    medidas.append(("C11 -> U8.6 (VREF)", hueco("C11", "1", "U8", "6")))
    peores = sorted(medidas, key=lambda t: -t[1])
    print("desacoplos, hueco de cobre pad-a-pad (los 4 peores):")
    for nombre, d in peores[:4]:
        print(f"    {nombre:28s} {d:5.2f} mm")
    return [f"{n}: {d:.2f} mm > 2 mm" for n, d in medidas if d > 2.0]


def verificar_ep(board) -> list[str]:
    """Los 4 EP: sin red y sin via encima, medido sobre la placa ruteada."""
    fallos, centros = [], {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if not (ref.startswith("U") and ref[1:].isdigit()
                and 1 <= int(ref[1:]) <= 4):
            continue
        for pad in [p for p in fp.Pads() if p.GetNumber() == "33"]:
            red = pad.GetNetname()
            if not red.startswith("unconnected-"):
                fallos.append(f"{ref}-EP: tiene red '{red}', tiene que quedar "
                              f"SIN red (datasheet pag.6)")
            centros[ref] = _xy(pad)
    assert len(centros) == 4, f"no aparecieron los 4 EP: {sorted(centros)}"
    # el land mide 2.65x2.65 (medio lado 1.325); ni una via cerca, con margen
    for t in board.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA):
            continue
        vx, vy = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
        for ref, (ex, ey) in centros.items():
            if abs(vx - ex) < 1.325 + 0.3 and abs(vy - ey) < 1.325 + 0.3:
                fallos.append(f"via en ({vx:.2f},{vy:.2f}) encima del EP de {ref}")
    if not fallos:
        print(f"EP: los 4 lands ({', '.join(sorted(centros))}) siguen sin red "
              f"y sin ninguna via encima")
    return fallos


def revisar_taladros(board) -> list[str]:
    """Ninguna via dentro de un pad, y ningun taladro pegado a otro.

    Esta es la comprobacion que faltaba durante siete rondas, y por eso se
    escribe aparte y con nombre propio. La placa de la ronda 7 llevaba, sin
    que ningun gate se enterara:

        15 vias plantadas DENTRO del taladro de un pad PTH (jacks, J1, J2),
           con solapes de -0.81 y -0.71 mm: dos agujeros pisandose;
        32 vias debajo de un pad SMD -- via-in-pad -- incluidos pads de QFN
           de 0.2 mm de ancho con una via de 0.45 encima;
         3 parejas de vias por debajo del minimo de taladro a taladro del
           fabricante, una de ellas a 0.0000 mm.

    Se escapaban por dos rendijas a la vez: coser_masas() daba por bueno el
    centro del pad como sitio para la via, y el DRC de KiCad trae
    hole_to_hole y holes_co_located como AVISO, asi que --severity-error no
    los veia. Las dos rendijas estan tapadas (ver _abanico, taladro_libre y
    SEVERIDADES); esto es el cinturon encima de los tirantes, y ademas mide
    y dice el peor caso en vez de solo aprobar o suspender.
    """
    # GetWidth() de una via PIDE capa en KiCad 10 (un padstack puede tener
    # un diametro por capa); sin el argumento salta un assert y el proceso
    # se queda esperando un dialogo que en headless no ve nadie.
    vias = [(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6,
             t.GetDrillValue() / 2e6, t.GetWidth(pcbnew.F_Cu) / 2e6)
            for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    pads = [(f"{fp.GetReference()}-{p.GetNumber()}", p)
            for fp in board.GetFootprints() for p in fp.Pads()]

    en_pad = []
    peor_pth = peor_via = (99.0, "")
    for nombre, p in pads:
        px, py = _xy(p)
        taladro = p.GetDrillSizeX() / 2e6
        for vx, vy, vd, vw in vias:
            if taladro > 0:                       # taladro contra taladro
                hueco = ((vx - px) ** 2 + (vy - py) ** 2) ** 0.5 - vd - taladro
                peor_pth = min(peor_pth, (hueco, nombre))
            # Y el cobre de la via contra la FORMA REAL del pad -- de
            # CUALQUIER pad, tenga taladro o no --, no contra su caja: TP14
            # es un circulo de 2 mm y una via en la esquina de su caja esta
            # fuera del pad por 0.34 mm. HitTest(punto, holgura) pregunta
            # contra la geometria de verdad, que es la misma leccion que el
            # GetSize() mentiroso de los pads custom del QFN.
            if p.HitTest(pcbnew.VECTOR2I(mm(vx), mm(vy)), mm(vw)):
                en_pad.append(nombre)
    for i, (x1, y1, d1, _w) in enumerate(vias):
        for x2, y2, d2, _w2 in vias[i + 1:]:
            peor_via = min(peor_via,
                           (((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 - d1 - d2,
                            f"({x1:.3f},{y1:.3f})"))

    fallos = []
    if peor_pth[0] < HOLE_CLEARANCE:
        fallos.append(f"hay vias a menos de {HOLE_CLEARANCE} mm del taladro de "
                      f"un pad: la peor contra {peor_pth[1]}, "
                      f"{peor_pth[0]:+.3f} mm de hueco")
    if en_pad:
        fallos.append(f"{len(en_pad)} vias con su cobre encima de un pad "
                      f"(via-in-pad): {sorted(set(en_pad))[:8]}")
    if peor_via[0] < HOLE_CLEARANCE:
        fallos.append(f"hay vias por debajo del minimo de taladro a taladro: "
                      f"la peor en {peor_via[1]}, {peor_via[0]:+.3f} mm")
    if not fallos:
        print(f"taladros: 0 vias dentro de un pad, 0 via-in-pad; el peor hueco "
              f"de taladro a taladro es {peor_pth[0]:.3f} mm contra un PTH y "
              f"{peor_via[0]:.3f} mm entre vias (minimo del fabricante "
              f"{HOLE_CLEARANCE})")
    return fallos


def medir_u13(board) -> float:
    """Del cuerpo de U13 al cuerpo del SSI2130 mas cercano, borde a borde."""
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    ux, uy = (fps["U13"].GetPosition().x / 1e6, fps["U13"].GetPosition().y / 1e6)
    peor, cual = 1e9, ""
    for v in ("U1", "U2", "U3", "U4"):
        qx = fps[v].GetPosition().x / 1e6
        qy = fps[v].GetPosition().y / 1e6
        # cuerpos reales: VSSOP-8 3x3, QFN-32 4x4
        dx = max(0.0, (ux - 1.5) - (qx + 2.0), (qx - 2.0) - (ux + 1.5))
        dy = max(0.0, (uy - 1.5) - (qy + 2.0), (qy - 2.0) - (uy + 1.5))
        d = (dx * dx + dy * dy) ** 0.5
        if d < peor:
            peor, cual = d, v
    print(f"U13 (termometro) al SSI2130 mas cercano ({cual}): {peor:.2f} mm "
          f"de cuerpo a cuerpo, con vertido termico aislado en medio")
    return peor


def _areas_islas(zona) -> list[float]:
    """Area de cada isla del relleno de una zona, en mm2 (formula del cordon
    de zapato sobre el contorno; los agujeros interiores no cuentan aparte --
    aqui lo que interesa es si el plano quedo PARTIDO, no su area exacta)."""
    poly = zona.GetFilledPolysList(zona.GetLayer())
    fuera = []
    for i in range(poly.OutlineCount()):
        o = poly.Outline(i)
        p = [(o.CPoint(j).x / 1e6, o.CPoint(j).y / 1e6)
             for j in range(o.PointCount())]
        fuera.append(abs(sum(p[k][0] * p[(k + 1) % len(p)][1]
                             - p[(k + 1) % len(p)][0] * p[k][1]
                             for k in range(len(p)))) / 2)
    return fuera or [0.0]


def revisar(board) -> list[str]:
    fallos: list[str] = []
    zonas = {z.GetNetname(): z for z in board.Zones()}

    for n, capa in (("GNDA", CAPA_GNDA), ("GNDD", CAPA_GNDD)):
        if n not in zonas:
            fallos.append(f"falta el vertido de {n}")
        elif zonas[n].GetLayer() != capa:
            fallos.append(f"el vertido de {n} no esta en la capa que le toca")
    if not fallos:
        fallos += revisar_frontera(board, zonas)

    # In1 (GNDA) tiene que seguir siendo un plano CONTINUO. Es la regla del
    # stackup de 4 capas, y sustituye a la vieja asimetria de B.Cu: ahora
    # B.Cu es una capa de senal como F.Cu y por ahi puede ir lo que sea.
    # Lo que no puede pasar es que el plano quede partido y la corriente de
    # retorno tenga que rodear. Se exige que la isla mayor se lleve mas del
    # 99% del cobre: las vias dejan agujeros (inevitables, todo el cobre es
    # SMD) pero no deben aislar trozos. Del digital no se exige nada: alli
    # el plano no mide, solo devuelve corriente logica.
    en_in1 = [t for t in board.GetTracks()
              if not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == CAPA_GNDA]
    if en_in1:
        fallos.append(f"hay {len(en_in1)} pistas en In1: esa capa es el plano "
                      f"de GNDA y no se rutea por ella")

    if "GNDA" in zonas:
        areas = sorted(_areas_islas(zonas["GNDA"]), reverse=True)
        parte = areas[0] / sum(areas)
        print(f"plano GNDA en In1: {len(areas)} isla(s), la mayor "
              f"{areas[0]:.0f} mm2 ({100 * parte:.2f}% del cobre vertido)")
        if parte <= 0.99:
            fallos.append(
                f"el plano ANALOGICO se fragmento: la isla mayor solo tiene "
                f"el {100 * parte:.2f}% del cobre ({len(areas)} islas; "
                f"sueltos {', '.join(f'{a:.1f}' for a in areas[1:6])} mm2). "
                f"Algo esta cortando In1.")

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("H") or ref in FUERA_DEL_PLANO:
            continue          # el termometro es GNDD por PISTA, no por plano
        for pad in fp.Pads():
            k, red = f"{ref}-{pad.GetNumber()}", pad.GetNetname()
            px, py = _xy(pad)
            if red == "GNDD" and not en_isla(px, py):
                fallos.append(f"{k} es GNDD pero cae fuera de la isla")
            if red == "GNDA" and en_isla(px, py):
                fallos.append(f"{k} es GNDA pero cae dentro de la isla")

    fallos += verificar_ep(board)
    fallos += revisar_taladros(board)
    medir_u13(board)

    # el QFN-32-1EP trae 4 pads SIN NUMERO (solo F.Paste, para segmentar la
    # pasta de soldar bajo el land termico y que no se junte en un charco):
    # no llevan cobre ni pueden llevar red, y no son huerfanos de verdad.
    huerfanos = [f"{fp.GetReference()}-{p.GetNumber()}"
                 for fp in board.GetFootprints() for p in fp.Pads()
                 if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                 and p.GetNumber() != ""
                 and p.GetNetname() == ""
                 and not fp.GetReference().startswith("H")]
    if huerfanos:
        fallos.append(f"pads sin red: {sorted(set(huerfanos))[:8]}")

    for fp in board.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        m = min(bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                W - bb.GetRight() / 1e6, H - bb.GetBottom() / 1e6)
        if m < 0:
            fallos.append(f"{fp.GetReference()} se sale de la placa ({m:.2f} mm)")
    return fallos


def rellenar(ruta: str):
    """Rellena las zonas de la placa de `ruta`, la guarda y la devuelve lista.

    El relleno hay que hacerlo sobre una placa RECIEN CARGADA de disco: sobre
    una que ya este en memoria de antes, ZONE_FILLER.Fill() se lleva el
    proceso por delante con un access violation, sin excepcion que capturar
    (misma trampa que en el bus board y en el modulo 2). Y despues hay que
    volver a cargarla para que la conectividad cuente el cobre nuevo.
    """
    board = pcbnew.LoadBoard(ruta)
    board.BuildListOfNets()
    board.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(board).Fill(board.Zones(), False, None), \
        "no se rellenaron las zonas"
    pcbnew.SaveBoard(ruta, board)
    board = pcbnew.LoadBoard(ruta)
    board.BuildListOfNets()
    board.BuildConnectivity()
    return board


def revisar_frontera(board, zonas) -> list[str]:
    """Hueco de cobre entre GNDA y GNDD, medido en 2D sobre el relleno real.

    Adaptacion de la version del modulo 2: alli la frontera era una linea
    vertical de punta a punta de la placa y bastaba comparar coordenadas x.
    Aqui la frontera dobla una esquina (la isla de J2), asi que se mide la
    distancia euclidiana minima entre los vertices de los dos poligonos
    rellenados -- no hay operaciones booleanas en el binding de Python de
    pcbnew, recorrer vertices mide lo mismo.

    Con el stackup de 4 capas los dos vertidos ya no comparten capa (GNDA en
    In1, GNDD en In2), asi que esto mide la separacion EN PLANTA: In1 esta
    recortada justo debajo de la isla digital, para que el retorno analogico
    y el digital no se solapen ni siquiera verticalmente. Es la misma cifra
    de siempre y sigue siendo la que importa.
    """
    def puntos(z) -> list[tuple[float, float]]:
        poly = z.GetFilledPolysList(z.GetLayer())
        out = []
        for i in range(poly.OutlineCount()):
            linea = poly.Outline(i)
            for j in range(linea.PointCount()):
                p = linea.CPoint(j)
                out.append((p.x / 1e6, p.y / 1e6))
        return out

    pa, pd = puntos(zonas["GNDA"]), puntos(zonas["GNDD"])
    if not pa or not pd:
        return ["algun vertido de masa quedo vacio"]
    hueco = min(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
                for x1, y1 in pa for x2, y2 in pd)
    if hueco <= 0:
        return ["GNDA y GNDD SE TOCAN: las dos masas quedan unidas"]
    if hueco < HUECO * 0.5:
        return [f"el hueco entre masas quedo en {hueco:.2f} mm, muy justo"]
    print(f"hueco medido entre los dos vertidos de masa: {hueco:.2f} mm")
    return []


def main() -> None:
    _check_escape()
    board = colocar()
    medir_dac_vco(board)
    coser_masas(reservadas=True)   # antes de rutear: ver COSTURAS_RESERVADAS
    rutear()
    # Tres vueltas: cada una deja vias nuevas por la placa y la siguiente
    # las aprovecha para enganchar los pads que antes no tenian de donde
    # agarrarse. Es idempotente -- un pad que ya tiene bajada se salta.
    for _ in range(3):
        coser_masas()
    board = rellenar(PCB)
    fallos = revisar(board) + medir_desacoplos(board)
    peor = medir_dac_vco(board)
    if peor >= 50.0:
        fallos.append(f"el peor par DAC->VCO ({peor:.1f} mm) pasa de la cota "
                      f"de 50 mm de dac_local_budget.py")

    sueltos = board.GetConnectivity().GetUnconnectedCount(True)
    pistas = sum(1 for t in board.GetTracks()
                 if not isinstance(t, pcbnew.PCB_VIA))
    vias = sum(1 for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
    print(f"placa {W:.0f}x{H:.0f} mm, {len(COLOCACION)} huellas, "
          f"{pistas} pistas + {vias} vias, {sueltos} tramos sin rutear")
    if sueltos:
        fallos.append(f"quedan {sueltos} tramos sin rutear")

    _severidades_drc()      # justo antes del DRC: ver SEVERIDADES
    # El informe se saca con TODAS las severidades, no solo errores (falta
    # --severity-all y el informe solo trae errores): la serigrafia por
    # debajo del minimo del fabricante es un AVISO de KiCad (text_height) y
    # aun asi es un defecto de fabricacion -- 112 de esos avisos fue lo que
    # dejo la ronda anterior por encoger los rotulos.
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "report",
                    "--severity-all", "-o", RPT, PCB],
                   capture_output=True, text=True)
    with open(RPT, encoding="utf-8") as fh:
        informe = fh.read()
    avisos: dict[str, int] = {}
    for linea in informe.splitlines():
        if linea.startswith("["):
            k = linea[1:linea.index("]")]
            avisos[k] = avisos.get(k, 0) + 1
    print("DRC por tipo (todas las severidades): "
          + (", ".join(f"{k} {n}" for k, n in sorted(avisos.items())) or "nada"))
    # El vertido termico de U13 (SIN RED a proposito, ver ~582-599) es la
    # UNICA infraccion deliberada de la placa: con --severity-all el DRC la
    # marca "isolated_copper". Se descuenta nombrandola, exactamente una vez
    # -- cualquier otro aviso (una segunda isla sin red incluida, o la
    # propia serigrafia que motivo este gate) lo tumba.
    EXCLUSIONES_DRC = {"isolated_copper": 1}
    for tipo, n in sorted(avisos.items()):
        de_mas = n - EXCLUSIONES_DRC.get(tipo, 0)
        if de_mas > 0:
            fallos.append(f"{de_mas} avisos de {tipo} sin explicar "
                          f"(DRC --severity-all)")

    for f in fallos:
        print("FALLO:", f)
    if fallos:
        sys.exit(1)

    drc = subprocess.run([KICAD_CLI, "pcb", "drc", "--severity-error",
                          "--exit-code-violations", PCB],
                         capture_output=True, text=True)
    print(drc.stdout.strip()[-800:] or drc.stderr.strip()[-300:])
    sys.exit(drc.returncode)


if __name__ == "__main__":
    main()
