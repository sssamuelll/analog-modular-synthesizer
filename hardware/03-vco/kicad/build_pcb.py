"""Genera sam17-vco.kicad_pcb: 114 x 118 mm, 2 capas, UNA masa (GNDA) con
una isla GNDD minima en la esquina de J2.

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
vez de solo la x.

LA COLOCACION ES UN CUADRO 2x2, NO UNA FILA DE 4. Es la correccion de fondo
de esta version. Con las 4 voces en fila el DAC de tono se queda en una punta
o en medio de una recta larga, y el peor par DAC->VCO se iba a 85 mm contra
los 50 mm que modela dac_local_budget.LARGO_LOCAL. En cuadro, los 3 DAC y la
referencia caben en el hueco central del cuadrado y las 4 voces quedan a la
MISMA distancia del DAC -- el peor par baja a 41.8 mm (37.7 el de U5, que es
el que manda la afinacion), dentro de la cota, y de paso la placa pasa de
240x172 a 114x118: 3.1x menos area, y por debajo de los 14.000 mm2 del
objetivo, aunque casi cuadrada en vez de apaisada.

EL RUTEO LO HACE FREEROUTING, no un ruteador casero. La version anterior de
este script traia un ruteador voraz de caminos en L/Z: cerraba 70 de 106
redes. Freerouting es un router de verdad, con rip-up y backtracking, y
cierra el 96% de las conexiones. El flujo -- exportar DSN, correr el jar
headless, importar SES, repetir -- vive en rutear(). El jar NO se descarga
solo: si falta, el script lo dice y aborta.

LO QUE NO CIERRA, dicho aqui y no solo en el reporte: quedan 18 conexiones
sin rutear (de ~500) y el plano analogico acaba en 30 islas, con el 96.5%
del cobre en la mayor. El script sale con ERROR mientras eso pase.

Las dos cosas son el mismo problema: 4 voces identicas comparten 7 buses,
ese grafo no es planar, las senales tienen que cruzarse, y en dos capas la
unica donde cruzar es B.Cu -- que es el plano. Cada cruce es una ranura.
Medido de punta a punta: con B.Cu prohibido en todo el analogico (la regla
literal del brief) quedan 155 tramos y el plano intacto; con la cruz
central protegida, 15-22 y el plano al 96%; con B.Cu abierto salvo el
cuadro de los DAC, 16 y el plano al 97%. Agrandar la placa a 122x128 NO
ayuda (18, y peor plano): el cuello es topologico, no de sitio. Es una
placa de 4 capas o un remate manual; esa decision no es de este script.

ASIMETRIA DE RUTEO: la pista de esta placa vive en F.Cu. B.Cu es el plano
-- GNDA cubre el 95% de la placa, GNDD el resto. La comprobacion que importa
no es "cuantas pistas hay en B.Cu" sino que el plano ANALOGICO siga siendo
UNA SOLA ISLA (revisar() lo mide sobre el relleno real): lo que hace dano no
es el cobre de abajo, es que la corriente de retorno tenga que rodear. Es la
misma regla del modulo 2, dicha en la misma forma.

EL EP DE CADA SSI2130 (pin 33, land termico) queda AISLADO a proposito: la
netlist ya lo trae con nombre unico "unconnected-(Un-EP-Pad33)" y este script
NO lo toca -- ni via, ni red, ni union al plano. El datasheet (pag.6,
Exposed Thermal Pad) lo prohibe: unir el EP a GND convierte el land en una
antena de acoplo entre las 4 voces y en un camino de fuga termica que el
autoafinado no puede compensar. verificar_ep() lo comprueba al final, sobre
la placa ya ruteada, no sobre la intencion.
"""
from __future__ import annotations

import json
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
RONDAS = int(os.environ.get("FREEROUTING_RONDAS", "6"))

W, H = 114.0, 118.0
MARGEN = 4.0
# la isla GNDD: esquina inferior izquierda, x < ISLA_X1 e y > ISLA_Y1 (antes
# de descontar el hueco). Los dos bordes que SI dan a GNDA son el derecho
# (x=ISLA_X1) y el de arriba (y=ISLA_Y1); los otros dos coinciden con el
# borde de la placa, ahi no hace falta hueco.
ISLA_X1 = 56.0
ISLA_Y1 = 90.0
HUECO = 3.0                # ancho del hueco de cobre entre GNDA y GNDD, mm
G = HUECO / 2

ANCHO = 0.2                 # pista. QFN de 0.4 mm de paso: con 0.25 (lo del
                            # modulo 2) no cabe ni una entre pads.
                            # UNA sola anchura, a proposito: lo mas "gordo"
                            # de esta placa son +-12V, que solo alimentan un
                            # TL074 y los pines V- de 4 SSI2130 -- decenas de
                            # mA. 0.2 mm en 1 oz aguanta ~0.7 A. Una netclass
                            # aparte para potencia seria complicar el DSN sin
                            # ganar nada medible.
VIA_D = 0.6                 # diametro exterior de via (drill 0.3)
CLEARANCE = 0.15            # entre cobre de redes distintas. JLCPCB estandar
                            # aguanta 0.127; 0.15 deja margen y sigue cabiendo
                            # entre pads de 0.4 mm de paso.

MOUNT = [(6.0, 6.0), (W - 6.0, 6.0), (6.0, H - 6.0), (W - 6.0, H - 6.0)]
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
CX = [30.0, 92.0]
CY = [35.0, 77.0]
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
JACK_Y = 8.0
JACK_X0, JACK_PASO = 18.3, 11.5

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
    ("R_SIN475B_{i}", -13.9, -4.5),
    ("R_SIN402_{i}", -13.9, -1.5),
    ("R_SIN475A_{i}", -13.9, 1.5),
    ("C_AC{i}A", -13.9, 4.5),
    # bloque izquierdo, columna interior. C_AC*B es un PUENTE de verdad: sus
    # dos pines van a AUX1_IN (pin 4, izquierda) y a SINE_OUT (pin 24,
    # esquina arriba-derecha), lados OPUESTOS del chip. Se queda del lado de
    # su pin 4 y el rodeo lo resuelve el router.
    ("C_AC{i}B", -9.5, -3.0),
    ("R_PITCH{i}", -9.5, 0.0),
    ("R_CVIN{i}", -9.5, 3.0),
    # columna derecha: la red de VREF
    ("R_LIN{i}", 9.0, -3.0),
    ("R_SCALE{i}", 9.0, 0.0),
    # fila de arriba: lo que sale hacia U9 y U10
    ("R_IV{i}", -6.0, -8.0),
    ("R_BW{i}", -2.0, -8.0),
    ("C_BW{i}", 2.0, -8.0),
    ("R_SQ{i}", 6.0, -8.0),
    # fila de abajo: las 4 entradas del mezclador
    ("R_MIX{i}A", -6.0, 8.0),
    ("R_MIX{i}B", -2.0, 8.0),
    ("R_MIX{i}C", 2.0, 8.0),
    ("R_MIX{i}D", 6.0, 8.0),
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
    ("C_TCAP{i}", 0.6, 4.5, 270),
    ("{c5v}", 5.0, 1.0, 0),
    ("{c12v}", -5.2, 1.4, 180),
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
    COLOCACION[f"TP{5 + _i}"] = ("tp", _cx - _s * 13.9, _cy - _s * 8.5, 0)  # CV_PITCH
    COLOCACION[f"TP{9 + _i}"] = ("tp", _cx - _s * 13.9, _cy + _s * 8.5, 0)  # MIXO
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
    "U6": ("tssop16", 61.0, 49.0, 0),
    "U5": ("tssop16", 61.0, 55.5, 0),
    "U7": ("tssop16", 61.0, 62.0, 0),
    "C14": ("c", 54.5, 49.325, 180), "C15": ("c", 67.5, 49.975, 0),   # U6
    "C12": ("c", 54.5, 55.825, 180), "C13": ("c", 67.5, 56.475, 0),   # U5
    "C16": ("c", 54.5, 62.325, 180), "C17": ("c", 67.5, 62.975, 0),   # U7
    "U8": ("soic8", 46.0, 52.0, 0),
    "C11": ("c", 51.5, 52.635, 0),
    "TP5": ("tp", 46.0, 58.5, 0),
    # U9 (TL074) en el canal central de ARRIBA, entre los jacks y la fila
    # superior de voces: recibe MIXO_1..4 (pin 25, lado de arriba de cada
    # QFN) y devuelve VOICE_OUT_1..4 a los jacks. Abajo, con la fuente,
    # cada salida de audio se iba 90 mm hasta su jack.
    "U9": ("soic14", 58.0, 32.0, 0),
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
# Solo lo que pide el brief: J2, U10, U13, U14, sus desacoplos y los pullups
# de I2C. U13 en la frontera de la isla ADYACENTE al racimo: mide la
# temperatura de los osciladores, no la del conector. En (44,94) queda a
# 20.8 mm del QFN de la voz 2 -- la esquina util de la isla, tan cerca del
# racimo como deja el hueco de 3 mm.
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
    "U13": ("vssop8", ISLA_X1 - 12.0, _IY, 0),
    "C19": ("c", ISLA_X1 - 7.0, _IY - 0.975, 0),
    "C20": ("c", 26.0, _IY + 4.5, 0),
    "R_I2C2": ("r", 33.0, _IY + 5.5, 0),
    "TP15": ("tp", 40.0, _IY + 5.5, 0),
})

# La isla la forman J2, U10, U13, U14, C18-C20, R_I2C1-2 y TP15, y nadie mas.
# No hay lista que lo diga: revisar() lo comprueba PAD a PAD contra la red
# (GNDD dentro de en_isla(), GNDA fuera), que es la unica version que no se
# puede quedar desfasada.


# --------------------------------------------------- donde se puede bajar
# Freerouting NO respeta un (plane ...) del DSN como obstaculo: da por hecho
# que el vertido se rehara alrededor de sus pistas, y rutea por B.Cu tan
# campante. Suelto sobre la placa entera metio 242 vias y dejo el plano
# ANALOGICO partido en 12 islas -- justo el dano que revisar() existe para
# cazar. Prohibido del todo (keepout sobre todo el analogico), la placa se
# queda en una sola capa y no cierra: 155 tramos al aire.
#
# La linea que si sostiene el presupuesto: la CRUZ CENTRAL se queda de cobre
# macizo -- la banda vertical x[41.5,75.5] y la horizontal y[46,66], que es
# donde viven los DAC y por donde corre el camino DAC->VCO con su corriente
# de retorno. Fuera de la cruz (las cuatro esquinas donde estan las voces, y
# la franja de abajo con la isla digital y la fuente) se puede bajar. Es la
# asimetria del modulo 2 aplicada a esta geometria: el cobre de abajo se
# protege donde el presupuesto lo mide, no en toda la placa por principio.
VENTANAS_BCU = [(0.0, 0.0, 46.0, 46.0),           # esquina de la voz 1
                (0.0, 66.0, 46.0, ISLA_Y1 - G),   # esquina de la voz 2
                (71.0, 0.0, W, 46.0),             # esquina de la voz 3
                (71.0, 66.0, W, ISLA_Y1 - G),     # esquina de la voz 4
                (0.0, ISLA_Y1 - G, W, H)]         # isla digital + fuente


def _keepouts_bcu() -> list[tuple[float, float, float, float]]:
    """El complemento de VENTANAS_BCU, en rectangulos.

    Un area de reglas de KiCad no sabe decir "aqui SI"; solo "aqui no". Se
    trocea la placa por las coordenadas de los bordes de las ventanas y se
    queda con las celdas que no caen dentro de ninguna.
    """
    xs = sorted({0.0, W} | {v for r in VENTANAS_BCU for v in (r[0], r[2])})
    ys = sorted({0.0, H} | {v for r in VENTANAS_BCU for v in (r[1], r[3])})
    fuera = []
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if not any(a <= cx <= c and b <= cy <= d
                       for a, b, c, d in VENTANAS_BCU):
                fuera.append((x0, y0, x1, y1))
    return fuera


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


def colocar() -> None:
    """Placa vacia con todo colocado, contorno, taladros, masas y reglas."""
    check_huellas()
    nets = leer_netlist()
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)
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
        if clave in ("r", "c", "tp"):
            # La referencia de stock mide 1x1 mm y en un anillo de 0805 a
            # 3 mm de paso se pisa con la del vecino: el DRC de serigrafia
            # cantaba 73 solapes, todos entre rotulos de pasivos. A 0.5 mm
            # sigue siendo legible en la serigrafia real (paso minimo de
            # JLCPCB: 0.15 mm de trazo) y dejan de pisarse.
            t = fp.Reference()
            t.SetTextSize(pcbnew.VECTOR2I(mm(0.5), mm(0.5)))
            t.SetTextThickness(mm(0.1))
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

    # GNDA: todo el contorno de la placa MENOS la esquina de la isla. Los dos
    # vertices que doblan la esquina (ISLA_X1+G, ISLA_Y1-G) son el borde real
    # que da a GNDD; el resto del borde de la isla coincide con el borde de
    # la placa y no necesita hueco.
    zona("GNDA", pcbnew.B_Cu, [
        (MARGEN, MARGEN), (W - MARGEN, MARGEN), (W - MARGEN, H - MARGEN),
        (ISLA_X1 + G, H - MARGEN), (ISLA_X1 + G, ISLA_Y1 - G),
        (MARGEN, ISLA_Y1 - G),
    ])
    zona("GNDD", pcbnew.B_Cu, [
        (MARGEN, ISLA_Y1 + G), (ISLA_X1 - G, ISLA_Y1 + G),
        (ISLA_X1 - G, H - MARGEN), (MARGEN, H - MARGEN),
    ])

    # ---- las areas prohibidas de B.Cu: la asimetria, dicha en un idioma
    # que Freerouting entiende. Ver VENTANAS_BCU.
    for x0, y0, x1, y1 in _keepouts_bcu():
        ka = pcbnew.ZONE(board)
        ka.SetLayer(pcbnew.B_Cu)
        ka.SetIsRuleArea(True)
        ka.SetDoNotAllowTracks(True)
        # Vias SI, a proposito. Todo el cobre de esta placa es SMD en F.Cu:
        # sin una via al lado, cada pad de GNDA se queda mirando el plano
        # desde arriba sin tocarlo (con las vias prohibidas el DRC cantaba 50
        # pads sueltos, casi todos de masa). Y una via de GNDA no agujerea el
        # plano: es del mismo neto, el vertido la abraza. Lo que parte el
        # plano son las PISTAS de otras redes, y esas siguen prohibidas.
        ka.SetDoNotAllowVias(False)
        ka.SetDoNotAllowZoneFills(False)
        ka.SetDoNotAllowPads(False)
        ka.SetDoNotAllowFootprints(False)
        v = pcbnew.VECTOR_VECTOR2I()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            v.append(pcbnew.VECTOR2I(mm(x), mm(y)))
        ka.AddPolygon(v)
        board.Add(ka)

    reglas = board.GetDesignSettings()
    reglas.m_TrackMinWidth = mm(ANCHO)
    reglas.m_MinClearance = mm(CLEARANCE)
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
    clase.SetViaDrill(mm(0.3))

    pcbnew.SaveBoard(PCB, board)
    return board


def _dist_seg(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / L))
    return ((p[0] - (a[0]+t*dx))**2 + (p[1] - (a[1]+t*dy))**2) ** 0.5


def coser_masas() -> int:
    """Una via de bajada al plano por cada pad de masa que no la tenga ya.

    Todo el cobre de esta placa es SMD en F.Cu y las dos masas viven en
    B.Cu: un pad de GNDA sin via al lado no toca el plano, mira el cobre
    desde arriba y se queda suelto. Freerouting pone algunas pero no llega
    a todas -- sin este paso dejaba 7 pads de masa al aire.

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
    """
    board = pcbnew.LoadBoard(PCB)
    r_via = VIA_D / 2 + CLEARANCE
    cajas = [(p.GetNetname(), p.GetBoundingBox()) for fp in board.GetFootprints()
             for p in fp.Pads()]
    segs, puntos = [], []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            puntos.append((t.GetNetname(), t.GetPosition().x / 1e6,
                           t.GetPosition().y / 1e6, VIA_D / 2))
        else:
            segs.append((t.GetNetname(),
                         (t.GetStart().x / 1e6, t.GetStart().y / 1e6),
                         (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6),
                         t.GetWidth() / 2e6))

    def lejos(x: float, y: float, net: str, margen: float) -> bool:
        for otra, caja in cajas:
            if otra == net:
                continue
            dx = max(0.0, caja.GetLeft() / 1e6 - x, x - caja.GetRight() / 1e6)
            dy = max(0.0, caja.GetTop() / 1e6 - y, y - caja.GetBottom() / 1e6)
            if dx * dx + dy * dy < margen * margen:
                return False
        for otra, a, b, w in segs:
            if otra != net and _dist_seg((x, y), a, b) < margen + w:
                return False
        return all(otra == net or ((x - vx)**2 + (y - vy)**2) ** 0.5 >= margen + r
                   for otra, vx, vy, r in puntos)

    def libre(px, py, x: float, y: float, net: str) -> bool:
        """La via y el rabito que la une al pad, los dos con su margen.

        El rabito se comprueba por muestreo cada 0.2 mm en vez de con
        geometria exacta: mide 3 mm como mucho y el pad mas fino de la
        placa (el del QFN, 0.2 mm) es mas ancho que el paso de muestreo.
        """
        if not lejos(x, y, net, r_via):
            return False
        largo = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
        pasos = int(largo / 0.2) + 1
        return all(lejos(px + (x - px) * i / pasos, py + (y - py) * i / pasos,
                         net, CLEARANCE + ANCHO / 2)
                   for i in range(1, pasos + 1))

    nuevas = faltan = 0
    for fp in board.GetFootprints():
        fx, fy = fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net not in ("GNDA", "GNDD"):
                continue
            px, py = _xy(pad)
            if any(otra == net and ((px - vx)**2 + (py - vy)**2) ** 0.5 < 1.2
                   for otra, vx, vy, _r in puntos):
                continue          # el router ya le dejo una al lado
            largo = ((px - fx) ** 2 + (py - fy) ** 2) ** 0.5 or 1.0
            ux, uy = (px - fx) / largo, (py - fy) / largo
            sitio = next(((px + ux * d, py + uy * d)
                          for d in (0.0, 0.9, 1.3, 1.7, 2.1, 2.5, 3.0)
                          if libre(px, py, px + ux * d, py + uy * d, net)), None)
            if sitio is None:
                faltan += 1
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(sitio[0]), mm(sitio[1])))
            v.SetDrill(mm(0.3))
            v.SetWidth(mm(VIA_D))
            v.SetNet(board.FindNet(net))
            board.Add(v)
            puntos.append((net, sitio[0], sitio[1], VIA_D / 2))
            nuevas += 1
            if sitio != (px, py):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(px), mm(py)))
                t.SetEnd(pcbnew.VECTOR2I(mm(sitio[0]), mm(sitio[1])))
                t.SetWidth(mm(ANCHO))
                t.SetLayer(pcbnew.F_Cu)
                t.SetNet(board.FindNet(net))
                board.Add(t)
                segs.append((net, (px, py), sitio, ANCHO / 2))
    pcbnew.SaveBoard(PCB, board)
    print(f"masas cosidas al plano: {nuevas} vias nuevas"
          + (f", {faltan} pads sin sitio" if faltan else ""))
    return faltan


# ------------------------------------------------------------------ ruteo
def ajustes_freerouting(tmp: str) -> None:
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
    * **via_costs: 30** (de fabrica 50). Con las ventanas de B.Cu ya
      limitando DONDE se puede bajar, penalizar tanto la via solo consigue
      que el router prefiera dar la vuelta por F.Cu y se quede sin sitio.

    Se PARCHEA el fichero, no se reescribe entero: el resto son preferencias
    del usuario (perfil, telemetria, GUI) que no son asunto de este script.
    """
    ruta = os.path.join(tmp, "freerouting", "freerouting.json")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    try:
        with open(ruta, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except (OSError, ValueError):
        cfg = {}
    router = cfg.setdefault("router", {})
    router.setdefault("fanout", {}).update(
        {"enabled": True, "algorithm": "freerouting-fanout", "max_passes": 100})
    router.setdefault("scoring", {})["via_costs"] = 30
    router["max_threads"] = 1
    # y el numero de pasadas TAMBIEN va aqui: -mp de la linea de comandos
    # queda por debajo del JSON (con -mp 150 y el JSON en 40, se paro en 45).
    router["max_passes"] = PASADAS
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    print(f"freerouting: fanout ON, via_costs 30 (escrito en {ruta})")


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
    ajustes_freerouting(tmp)
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


def _areas_islas(zona) -> list[float]:
    """Area de cada isla del relleno de una zona, en mm2 (formula del cordon
    de zapato sobre el contorno; los agujeros interiores no cuentan aparte --
    aqui lo que interesa es si el plano quedo PARTIDO, no su area exacta)."""
    poly = zona.GetFilledPolysList(pcbnew.B_Cu)
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

    for n in ("GNDA", "GNDD"):
        if n not in zonas:
            fallos.append(f"falta el vertido de {n}")
        elif zonas[n].GetLayer() != pcbnew.B_Cu:
            fallos.append(f"el vertido de {n} no esta en B.Cu")
    if not fallos:
        fallos += revisar_frontera(board, zonas)

    # El plano ANALOGICO tiene que seguir siendo UNA sola isla: es la
    # comprobacion real de la asimetria B.Cu (ver la cabecera), no una cuenta
    # de pistas por capa. Lo que hace dano no es que haya cobre en la capa de
    # abajo, es que el plano quede PARTIDO y el retorno tenga que rodear.
    # Del digital no se exige: alli el plano no mide nada, solo devuelve
    # corriente logica.
    if "GNDA" in zonas:
        areas = sorted(_areas_islas(zonas["GNDA"]), reverse=True)
        print(f"plano GNDA: {len(areas)} isla(s), la mayor {areas[0]:.0f} mm2 "
              f"({100 * areas[0] / sum(areas):.2f}% del cobre vertido)")
        if len(areas) != 1:
            fallos.append(
                f"el plano ANALOGICO quedo partido en {len(areas)} islas "
                f"({', '.join(f'{a:.1f}' for a in areas[1:])} mm2 sueltos "
                f"frente a {areas[0]:.0f}): alguna pista de B.Cu lo corta y "
                f"la corriente de retorno tiene que rodear")

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("H"):
            continue
        for pad in fp.Pads():
            k, red = f"{ref}-{pad.GetNumber()}", pad.GetNetname()
            px, py = _xy(pad)
            if red == "GNDD" and not en_isla(px, py):
                fallos.append(f"{k} es GNDD pero cae fuera de la isla")
            if red == "GNDA" and en_isla(px, py):
                fallos.append(f"{k} es GNDA pero cae dentro de la isla")

    fallos += verificar_ep(board)

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
    """
    def puntos(z) -> list[tuple[float, float]]:
        poly = z.GetFilledPolysList(pcbnew.B_Cu)
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
    board = colocar()
    medir_dac_vco(board)
    rutear()
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
    for f in fallos:
        print("FALLO:", f)
    if fallos:
        sys.exit(1)

    subprocess.run([KICAD_CLI, "pcb", "drc", "--severity-error",
                    "--format", "report", "-o", RPT, PCB],
                   capture_output=True, text=True)
    drc = subprocess.run([KICAD_CLI, "pcb", "drc", "--severity-error",
                          "--exit-code-violations", PCB],
                         capture_output=True, text=True)
    print(drc.stdout.strip()[-800:] or drc.stderr.strip()[-300:])
    sys.exit(drc.returncode)


if __name__ == "__main__":
    main()
