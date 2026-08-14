"""Genera sam17-power.kicad_sch a partir de las notas de diseno del modulo.

Fuente: ../notes/design-notes.md (topologia, valores, presupuesto de
corriente). Trazado con cables reales sobre coordenadas de pin, no con
etiquetas de red — ver convenciones abajo.

Uso (requiere hardware/tools/kicad_mcp_client.py y un KiCAD-MCP-Server
corriendo/instalado, ver hardware/tools/README.md):

    python build_schematic.py

Es destructivo por diseno: create_schematic sobreescribe el .kicad_sch. Volver
a correrlo reconstruye la hoja desde cero a partir de este archivo, que es la
fuente de verdad real.

Convenciones del dibujo:
  - Flujo izquierda->derecha: J3/J1 -> BR1 -> reguladores -> J2 (±12V) y
    J6 (+5V).
  - Riel positivo arriba, negativo abajo, puente centrado entre ambos.
  - GND no es un bus largo: cada retorno es un stub corto a un simbolo power:GND
    (todos son la misma net). Los del riel negativo van girados 180 para que el
    grafico apunte hacia arriba.
  - Hoja A3: en A4 las parejas de condensadores quedaban a 12.7 mm y un valor
    como "4700uF/25V" mide ~15 mm, asi que los textos se solapaban. Con 25.4 mm
    de separacion la colocacion automatica de campos ya no choca.
  - Riel +5V (design-notes.md §10.1) en la fila intermedia, entre las filas de
    GND de +12V y -12V: solo 30.48 mm de hueco a cada lado, contra los ~50 mm
    que tienen +12V/-12V hacia fuera. El diodo de proteccion y las etiquetas de
    U3 se separaron a mano (uno arriba, otro abajo) para que no se pisen en ese
    espacio mas apretado — visto en el render, no adivinado.
  - J6 (issue #8, opcion C): el +5V sale de la placa por su propio conector de
    2 pines, NO por J2. El bus analogico J2 queda +12/G/G/-12 igual para todos
    los modulos; J6 va solo al modulo 2 (DAC + LCD) en conector polarizado
    distinto — imposible cruzarlo con ±12 — y su retorno se rutea DEDICADO
    hasta el punto de estrella (design-notes.md §10.1/§10.4). El motivo es
    fisico, no estetico: el backlight va PWM-eado y ~100 mA conmutados sobre
    ~50 mΩ de retorno compartido son ~5 mV de rebote en la referencia del
    DAC ≈ 6 cents de wobble en el CV.
  - Primario 230V/50Hz (variante Europa; design-notes.md §10.2/§10.3/§12),
    fila propia arriba de todo: F1 vive AQUI, no en el secundario — protege
    el primario contra un corto reflejado desde el secundario, que es lo que
    dice la nota de diseno. TR1 es externo a esta placa: J4 es la salida
    hacia su devanado primario, no hay wire directo entre J4 y J1 (son el
    mismo transformador, pero fuera de esta hoja).
  - RV1 es S20K275 (275VAC), no el V150LA20A (150VAC) de la variante
    Venezuela/110V original — un MOV de 150V en 230V nominal conduce todo el
    tiempo y falla. NT1 (SL10 5R020) SI se mantiene igual: toda la familia
    SL10 esta rated 265VAC max (datasheet Vishay/Ametherm, documento 24503),
    con margen sobre los 253V del +10% de tolerancia de la red europea.
  - Tierra de proteccion (design-notes.md §13): PE entra por J3.3 y muere en
    un simbolo Earth_Protective — no hay pista de PE cruzando la placa. J5 es
    el faston por el que GND sube al MISMO esparrago de chasis. Salen como dos
    redes distintas en el netlist a proposito: se tocan en el metal, fuera de
    la PCB, que es donde tiene que aguantar la corriente de falla. Puente duro
    y no red de lift porque los paneles son lamina galvanizada y los 40 jacks
    de 3.5 mm ya unen chasis y GND por el casquillo: una red de lift estaria
    cortocircuitada 40 veces y el plano estaria mintiendo.

Reglas de KiCad que mandan sobre el trazado, descubiertas midiendo (no estan
documentadas en el server):
  1. Un pin solo conecta si un cable TERMINA en el. Que el riel le pase por
     encima no conecta nada -> los rieles van partidos pin a pin.
  2. Aterrizar a media linea es fragil. Por eso los rieles se cortan tambien en
     cada punto donde entra un ramal, y cada union queda extremo contra extremo.
  3. KiCad SUMA la rotacion del simbolo al angulo de sus campos: un componente
     girado 90/270 necesita el angulo complementario en Reference/Value o el
     texto sale vertical y las dos etiquetas se pisan.
  4. Los pines de Conn_01x0N_Pin caen en ancla + (5.08, 2.54*(k-1) - 2.54*
     floor((N-1)/2)), con k el numero de pin empezando en 1. Es decir: el ancla
     se sienta en el CENTRO de la fila de pines redondeado a rejilla, no en el
     pin 1. Con N par el centro cae fuera de rejilla y KiCad lo baja al pin 1
     (N=2 -> offsets 0, +2.54); con N impar el ancla es el pin del medio
     (N=3 -> -2.54, 0, +2.54). Medido sobre cuatro instancias con el ancla ya
     en rejilla, y comprobado contra J2 (N=4, rot 180).
Todo en multiplos de 1.27 mm: un extremo fuera de rejilla envenena las uniones
de toda la hoja.

KiCad conecta un pin con un extremo de cable a menos de ~1 mm, asi que un
cableado torcido puede pasar el ERC igual. Eso disimulo durante una revision
que J3/J4 estuviesen cableados a (+4.94, +0.33) en vez de a los (+5.08, 0)
reales. Por eso main() no se fia del ERC: comprueba pin a pin que exista un
extremo de cable EXACTO (<0.01 mm) y aborta si no. La tolerancia es del
editor, no una licencia para dibujar a ojo.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
from kicad_mcp_client import Client  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
SCH = f"{DIR}/sam17-power.kicad_sch"
# Para comprobar que los footprints existen de verdad. Si la ruta no esta, la
# comprobacion se salta con un aviso en vez de romper el build en otra maquina.
KICAD_FP = os.environ.get("KICAD_FOOTPRINTS",
                          r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

YP, YN = 66.04, 167.64          # rieles positivo / negativo
YMID = 116.84                   # eje del puente y del conector de entrada
YG_P, YG_N = 86.36, 147.32      # fila de simbolos GND (arriba / abajo)
XU = 180.34                     # columna de los reguladores
YOFF = 25.4                     # baja todo el dibujo para centrarlo en A3
XPIN = 5.08                     # offset en x del pin de un Conn_01x0N_Pin sin girar
DATE, REV = "2026-08-14", "F"

# Riel +5V (design-notes.md §10.1): fila intermedia entre +12V y -12V. Cuelga
# del VRAW+ existente (tap sobre la union de la rail en x=106.68) en vez de
# repetir un bulk cap propio. YMID=116.84 ya esta ocupado por J2 y su jog a
# partir de x>=288, asi que la fila del +5V se queda x<272 y no choca.
Y5 = YMID                       # 116.84: altura del riel/regulador (como YP para U1)
Y5_ROW = Y5 + 3.81              # fila de C9/C10/C11/R3: su pin de ARRIBA cae en Y5,
                                 # igual que C1/C3/C5/C7/R1 se colocan en YP+3.81, no en YP
YG_5 = 129.54                   # fila de retornos a GND del riel +5V
YD5 = Y5 - 16.51                # diodo de proteccion, arriba (lado +12V)
YD6 = Y5_ROW + 15.24            # LED indicador (mismo offset que D3 desde R1)
X5_LED = 297.18                 # columna propia del indicador +5V, ver PARTS.
                                 # NO usar 306.07: coincide con el codo del
                                 # cableado GND de J2 y crea un corto +5V-GND.

# J6, feed de +5V (issue #8, opcion C): vive en el bloque vacio ENCIMA del riel
# +5V, pegado a J2 para que se lea como "las salidas de la placa". Girado 180
# como J2, asi que sus pines quedan a la izquierda del ancla y el pin 2 sube
# (mismo comportamiento medido en J4). La bajada del pin 1 al riel va por
# x=281.94, a la izquierda del codo +12V->J2 (vertical en 292.10, horizontal
# en y=111.76 desde alli): cero cruces.
X_J6A = 287.02                  # ancla de J6
X_J6 = X_J6A - XPIN             # = 281.94: columna del pin y de su bajada al riel
Y_J6 = 106.68                   # J6.1 (+5V); J6.2 (retorno) queda en Y_J6 - 2.54

# Lado primario 230 VAC (design-notes.md §10.2/§10.3/§12/§13), fila propia
# arriba de todo lo demas (y<45.72, hueco libre hasta ahora).
#
# J3 pasa a 3 pines para traer la tierra de proteccion (§13). Por la regla 4
# del docstring el ancla de un Conn_01x03_Pin ES su pin del medio, asi que
# anclarlo en Y_M deja L arriba, N en el ancla y PE abajo, los tres en
# rejilla. J4 sigue siendo de 2 pines y ahi el ancla ES el pin 1: va a Y_L
# para que sus dos pines caigan sobre las mismas lineas de L y N.
Y_M = 20.32                     # ancla de J3 = su pin 2
Y_L = Y_M - 2.54                # J3.1 linea/vivo (fusible + MOV + NTC en serie)
Y_N = Y_M                       # J3.2 neutro, solo el tramo hasta su codo
Y_PE = Y_M + 2.54               # J3.3 tierra de proteccion -> chasis (§13)
YRV = Y_L + 3.81                # centro del MOV: su pin1 cae EXACTO en Y_L

# El MOV va de L a N, pero mide 7.62 mm y los pines de J3 estan a 2.54: dibujado
# entre las dos lineas a la altura del conector, el cable de neutro le atraviesa
# el cuerpo. Asi salio impreso hasta la rev D. N baja a su propio carril nada mas
# salir de J3 y vuelve a subir justo antes de J4, que es lo que hace cualquier
# plano de red: los pines del conector se abren a carriles comodos.
Y_NL = 30.48                    # carril de neutro
X_NJ, X_NJ2 = 45.72, 116.84     # codos de bajada y de subida de N
# J4 se corre a la derecha respecto de la rev D: entre NT1 (acaba en 102.87) y
# el sitio viejo solo quedaban 5 mm de cable, y ahi no cabe la etiqueta L_TR sin
# montarse encima del numero de pin. Tambien separa "TR1 pri (ext)" de "NT1".
X_J4A = 127.00                  # ancla de J4
X_J4 = X_J4A - XPIN             # J4 va girado 180 (ver PARTS): sus pines quedan
                                # a la IZQUIERDA del ancla, no a la derecha
# PE baja por su propia columna, a la izquierda del codo de N, para no cruzarse
# con el: un cruce entre neutro y tierra de proteccion es justo el que no
# quieres tener que explicar mirando el plano.
X_PE, Y_PES = 33.02, 33.02      # columna de bajada de PE y altura de su simbolo
Y_PEF, X_PEF = 27.94, 40.64     # ramal del PWR_FLAG de la red PE
Y_CH = 40.64                    # fila del faston de chasis J5: debajo del bloque
                                # primario y muy por encima del riel VRAW+ (66.04)

PARTS = [
    # --- lado primario, 110 VAC (design-notes.md §10.2/§10.3): el fusible va
    # AQUI, no en el secundario — protege contra un corto reflejado desde el
    # secundario, no solo un corto local. TR1 es externo (no esta en esta
    # placa): J4 es la salida hacia su devanado primario. ---
    ("J3",  "Connector:Conn_01x03_Pin",       25.40, Y_M,     0, "AC 230V IN"),
    ("F1",  "Device:Fuse",                    53.34, Y_L,    90, "250mA T"),
    ("RV1", "Device:Varistor",                76.20, YRV,     0, "S20K275"),
    ("NT1", "Device:Thermistor_NTC",          99.06, Y_L,    90, "NTC 5R/2A"),
    ("J4",  "Connector:Conn_01x02_Pin",       X_J4A, Y_N,   180, "TR1 pri (ext)"),
    # Faston del puente unico GND -> chasis (§13). Va aqui, pegado al bloque
    # de red, para que se lea junto con el PE de J3: los dos cables acaban en
    # el mismo esparrago. Electricamente cuelga de GND como cualquier retorno.
    ("J5",  "Connector:Conn_01x01_Pin",       25.40, Y_CH,    0, "CHASIS"),
    ("J1",  "Connector:Conn_01x03_Pin",       30.48, YMID,    0, "12VAC CT 2A"),
    ("BR1", "Device:D_Bridge_+-AA",           91.44, YMID,   90, "KBP206"),
    # --- riel +12V ---
    ("C1",  "Device:C_Polarized",            121.92, 69.85,   0, "4700uF/25V"),
    # Segundo bulk por riel. Con 4700 uF el valle de VRAW+ a 207 V queda en
    # 13.66 V contra los 13.6 que exige el LM2940: +0.06 V no es margen, es
    # suerte. Con 9400 sube a 14.12 V (sec.16.5, simulado).
    ("C12", "Device:C_Polarized",            134.62, 69.85,   0, "4700uF/25V"),
    ("C3",  "Device:C",                      147.32, 69.85,   0, "0.47uF"),
    ("U1",  "Regulator_Linear:LM7812_TO220",    XU, YP,       0, "LM2940CT-12"),
    ("C5",  "Device:C_Polarized",            213.36, 69.85,   0, "100uF/25V ESR"),
    ("C7",  "Device:C",                      238.76, 69.85,   0, "0.1uF"),
    ("D1",  "Diode:1N4001",                     XU, 45.72,    0, "1N4001"),
    ("R1",  "Device:R",                      271.78, 69.85,   0, "2k2"),
    ("D3",  "Device:LED",                    271.78, 85.09,  90, "RED"),
    # --- riel -12V ---
    ("C2",  "Device:C_Polarized",            121.92, 163.83,  0, "4700uF/25V"),
    ("C13", "Device:C_Polarized",            134.62, 163.83,  0, "4700uF/25V"),
    ("C4",  "Device:C_Polarized",            147.32, 163.83,  0, "10uF/35V"),
    ("U2",  "Regulator_Linear:LM2990SX-12",     XU, YN,       0, "LM2990T-12"),
    ("C6",  "Device:C_Polarized",            213.36, 163.83,  0, "100uF/35V"),
    ("C8",  "Device:C",                      238.76, 163.83,  0, "DNP"),
    ("D2",  "Diode:1N4001",                     XU, 187.96, 180, "1N4001"),
    ("R2",  "Device:R",                      271.78, 144.78,  0, "2k2"),
    ("D4",  "Device:LED",                    271.78, 160.02, 90, "YEL"),
    ("J2",  "Connector:Conn_01x04_Pin",      320.04, 116.84, 180, "BUS +12/G/G/-12"),
    # --- riel +5V aux (design-notes.md §10.1): DAC del MIDI/CV + LCD, ~150 mA.
    # Cuelga del mismo VRAW+ que el 7812 — no lleva su propio bulk cap. ---
    ("C9",  "Device:C",                      147.32, Y5_ROW,  0, "0.33uF"),
    ("U3",  "Regulator_Linear:LM7805_TO220",     XU, Y5,      0, "LM7805"),
    ("C10", "Device:C_Polarized",            213.36, Y5_ROW,  0, "100uF"),
    ("C11", "Device:C",                      238.76, Y5_ROW,  0, "0.1uF"),
    ("D5",  "Diode:1N4001",                      XU, YD5,     0, "1N4001"),
    # Columna propia (306.07, no 271.78): esa columna ya la ocupan los
    # indicadores de +12V/-12V (R1/D3 arriba, R2/D4 abajo) y a la altura del
    # riel +5V caian encima de esos dos a la vez.
    ("R3",  "Device:R",                      X5_LED, Y5_ROW,  0, "680"),
    ("D6",  "Device:LED",                    X5_LED, YD6,    90, "GRN"),
    # --- feed de +5V al modulo 2 (issue #8, opcion C): conector propio, no
    # va en J2. Ver el bloque de constantes X_J6A/Y_J6 y el docstring. ---
    ("J6",  "Connector:Conn_01x02_Pin",       X_J6A, Y_J6,  180, "+5V/RTN"),
]

# Footprints. Van AQUI y no parcheados sobre el .kicad_sch porque este script
# reescribe la hoja entera cada vez: un footprint puesto a mano en el fichero
# desaparece en el siguiente build. Tres son de la libreria local sam17.pretty
# (varistor de 20mm, NTC de disco y faston) porque KiCad 10 no los trae: su
# Varistor.pretty llega a D12, no hay libreria de termistores THT y no hay
# ningun faston de PCB.
#
# BR1 es el unico sin resolver del todo. El nombre del simbolo codifica el
# ORDEN FISICO de patillas (+-AA = pin1:+, pin2:-, pin3:~, pin4:~) y KiCad trae
# cinco variantes justo por eso. Cual toca depende del puente que se compre, y
# las fuentes secundarias se contradicen entre si. La geometria DIP-4 es la
# misma en los cuatro casos, asi que la placa se puede colocar y rutear igual;
# lo que cambia es que pad cae en que red. VERIFICAR CONTRA EL DATASHEET DE LA
# PIEZA COMPRADA ANTES DE FABRICAR (design-notes.md sec.14, checklist sec.9).
FOOTPRINT = {
    # --- primario 230 VAC ---
    "J3":  "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-03P_1x03_P5.00mm",
    # Portafusible CERRADO, no clips abiertos: 230V al descubierto dentro de un
    # cajon de madera no pega con el aislamiento reforzado que se eligio. El
    # FPG4 esta rated IEC 60335-1 250VAC/10A VDE y ademas mide 12.5mm contra
    # los 24mm de un clip en linea.
    "F1":  "Fuse:Fuseholder_Cylinder-5x20mm_Schurter_FPG4_Vertical_Closed",
    "RV1": "sam17:RV_Disc_D21mm_W5.5mm_P10.0mm",
    "NT1": "sam17:NTC_Disc_D11.5mm_W4.5mm_P7.5mm",
    "J4":  "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm",
    "J5":  "sam17:Faston_6.3x0.8mm_PCB_2Leg_P5.0mm",
    # --- secundario ---
    "J1":  "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-03P_1x03_P5.00mm",
    "BR1": "Diode_THT:Diode_Bridge_DIP-4_W7.62mm_P5.08mm",
    # --- bulk: D16, NO D10. El bom.csv pedia Radial-D10 para 4700uF/25V, que
    # no existe fisicamente (un D10 a 25V ronda los 470uF). ---
    "C1":  "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    "C12": "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    "C13": "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    "C2":  "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    # --- reguladores: los tres verticales, con disipador propio. U2 no puede
    # compartir disipador (su tab es -Vin, no GND) — ver design-notes.md sec.4.
    "U1":  "Package_TO_SOT_THT:TO-220-3_Vertical",
    "U2":  "Package_TO_SOT_THT:TO-220-3_Vertical",
    "U3":  "Package_TO_SOT_THT:TO-220-3_Vertical",
    # --- salidas del bus ---
    "J2":  "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
    "J6":  "Connector_Molex:Molex_KK-254_AE-6410-02A_1x02_P2.54mm_Vertical",
}
# Los que se repiten por familia, para no escribir la misma cadena nueve veces.
for _refs, _fp in [
    (("C3", "C9"),       "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"),
    # C4 dejo de ser ceramico: el LM2990 pide >=10 uF de aluminio a la
    # entrada, asi que pasa a electrolitico radial pequeno.
    (("C4",),            "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm"),
    (("C5", "C6", "C10"), "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"),
    (("C7", "C8", "C11"), "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"),
    (("D1", "D2", "D5"),  "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"),
    (("D3", "D4", "D6"),  "LED_THT:LED_D3.0mm"),
    (("R1", "R2", "R3"),
     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"),
]:
    FOOTPRINT.update(dict.fromkeys(_refs, _fp))

POWER = [
    ("#G1",  "power:GND",  43.18, 124.46,   0),
    ("#G2",  "power:GND", 121.92, YG_P,     0),
    ("#G21", "power:GND", 134.62, YG_P,     0),
    ("#G3",  "power:GND", 147.32, YG_P,     0),
    ("#G4",  "power:GND",     XU, YG_P,     0),
    ("#G5",  "power:GND", 213.36, YG_P,     0),
    ("#G6",  "power:GND", 238.76, YG_P,     0),
    ("#G7",  "power:GND", 271.78,  95.25,   0),
    ("#G8",  "power:GND", 121.92, YG_N,   180),
    ("#G22", "power:GND", 134.62, YG_N,   180),
    ("#G9",  "power:GND", 147.32, YG_N,   180),
    ("#G10", "power:GND",     XU, YN + 12.7, 0),
    ("#G11", "power:GND", 213.36, YG_N,   180),
    ("#G12", "power:GND", 238.76, YG_N,   180),
    ("#G13", "power:GND", 271.78, 138.43, 180),
    ("#G14", "power:GND", 302.26, 115.57, 270),
    ("#P1",  "power:+12V", 254.00,  53.34,  0),
    ("#N1",  "power:-12V", 254.00, 180.34, 180),
    ("#FLG1", "power:PWR_FLAG", 106.68,  53.34,   0),
    ("#FLG2", "power:PWR_FLAG", 106.68, 180.34, 180),
    ("#FLG3", "power:PWR_FLAG", 195.58, YG_P,     0),
    ("#G15", "power:GND", 147.32, YG_5,   0),
    ("#G16", "power:GND",     XU, YG_5,   0),
    ("#G17", "power:GND", 213.36, YG_5,   0),
    ("#G18", "power:GND", 238.76, YG_5,   0),
    ("#G19", "power:GND", X5_LED, YD6 + 10.16, 0),
    ("#P2",  "power:+5V", 254.00, Y5 - 12.7, 0),
    # --- tierra de proteccion (§13). Earth_Protective, no GND ni Earth a
    # secas: es el simbolo IEC 60417-5019, el unico que dice "proteccion" y
    # no "referencia de señal". La red muere aqui a proposito. ---
    ("#PE1",  "power:Earth_Protective", X_PE,  Y_PES, 0),
    ("#FLG4", "power:PWR_FLAG",         X_PEF, Y_PEF, 0),
    ("#G20",  "power:GND",              53.34, Y_CH,  0),
    # Retorno de J6. En la HOJA es la misma red GND que todo lo demas; la
    # separacion del retorno que exige §10.1 es una regla de layout de la PCB
    # y del cableado, anotada en el texto de al lado de J6.
    ("#G21",  "power:GND",              269.24, Y_J6 - 2.54, 0),
]

# KiCad saca el nombre de una red de potencia del Value del simbolo, no del
# simbolo. "Earth_Protective" es como se llama el dibujo; la red se llama PE,
# que es como la llama cualquiera que abra el plano o el netlist.
POWER_VALUE = {"#PE1": "PE"}

# J4 es una salida: sin girar, el cable le entra por encima del cuerpo y de los
# numeros de pin, porque los pines de Conn_01x0N_Pin salen SIEMPRE hacia la
# derecha. Lo suyo seria espejarlo, pero add_schematic_component acepta
# mirrorY y lo ignora sin decir nada (comprobado: los pines siguen en +5.08).
# Asi que gira 180 como J2, y como en J2 eso invierte el orden vertical de los
# pines: anclando en Y_N el pin 2 sube a Y_L y el pin 1 se queda en Y_N, o sea
# J4.1 = neutro y J4.2 = linea. Lo desambiguan las etiquetas L_TR y N impresas
# en los propios cables; en un primario de transformador ademas da igual cual
# es cual, porque el devanado es flotante — lo que importa (fusible y MOV en la
# linea) queda aguas arriba de J4.

# nombra los rieles crudos; sin esto el netlist los llama Net-(BR1-+)
LABELS = [
    ("VRAW+", 99.06, YP), ("VRAW-", 99.06, YN),
    # La linea queda partida en tres nets por F1 y NT1, y sin nombre el netlist
    # las llama Net-(F1-Pad1). En una seccion de red interesa que la PCB diga
    # cual es cual sin tener que seguir el dibujo. PE no lleva etiqueta: se lo
    # nombra el propio simbolo Earth_Protective y dos nombres en la misma red
    # se pelean en el ERC.
    ("L",    35.56,  Y_L), ("L_F",  63.50,  Y_L),
    ("L_TR", 106.68, Y_L), ("N",    60.96,  Y_NL),
    # Las dos patas del secundario partido, por el mismo motivo: se llamaban
    # Net-(J1-Pin_1) y Net-(J1-Pin_3).
    ("SEC_A", 60.96, 104.14), ("SEC_B", 60.96, 135.89),
]

# Anotaciones de la hoja: la decision de §13 tiene que viajar CON el plano, no
# solo en el repo — quien monte esto mira el PDF, no design-notes.md. Sin "§"
# aqui: add_schematic_text lo escribe doble-codificado y sale "Â§" en el PDF
# (el cajetin si lo aguanta, porque se escribe por texto plano en el fichero).
TEXTS = [
    ("J5 = puente unico GND -> chasis. PE (J3.3) sube al MISMO esparrago.", 63.50, 39.37),
    ("No hay pista de PE en la PCB: la corriente de falla no pasa por la",  63.50, 41.91),
    ("placa. Apriete y ensayo de continuidad en design-notes.md sec. 13.",  63.50, 44.45),
    # La regla de layout del retorno de J6 viaja con el plano, igual que la
    # de PE: quien rutee la PCB mira el PDF, no design-notes.md.
    ("J6 = feed de +5V al modulo 2 (DAC + LCD, ~150 mA), issue #8 opcion C:", 300.99, 144.78),
    ("conector aparte del bus a proposito. Rutear el retorno (J6.2) DEDICADO", 300.99, 147.32),
    ("hasta el punto de estrella, separado del retorno analogico hasta el",    300.99, 149.86),
    ("ultimo cm (design-notes.md sec. 10.1) - el backlight va conmutado.",     300.99, 152.40),
]



def side_fields(ref: str, x: float, y: float) -> list:
    """Campos a la derecha de un componente vertical (C, R, LED girado).

    +7.62 en x: centrados a +3.81 el texto de "4700uF/25V" pisaba su propio
    simbolo, y a 25.4 mm del vecino todavia sobra sitio.
    """
    return [(ref, "Reference", x + 7.62, y - 2.54), (ref, "Value", x + 7.62, y + 2.54)]


# La colocacion automatica da campos verticales solapados en los simbolos
# girados (F1, BR1, D3, D4), asi que aqui va cada campo a mano.
FIELDS: list = []
for _r, _x, _y in [("C3", 147.32, 69.85), ("C5", 213.36, 69.85),
                   ("C7", 238.76, 69.85), ("C4", 147.32, 163.83),
                   ("C6", 213.36, 163.83), ("C8", 238.76, 163.83),
                   ("R1", 271.78, 69.85), ("D3", 271.78, 85.09),
                   ("R2", 271.78, 144.78), ("D4", 271.78, 160.02),
                   ("C9", 147.32, Y5_ROW), ("C10", 213.36, Y5_ROW), ("C11", 238.76, Y5_ROW),
                   ("R3", X5_LED, Y5_ROW), ("D6", X5_LED, YD6)]:
    FIELDS += side_fields(_r, _x, _y)
FIELDS += [
    # El bulk va en parejas a 12.7 mm, la mitad de la separacion habitual, asi
    # que sus etiquetas se reparten a lados opuestos: las del primero a la
    # izquierda y las del segundo a la derecha. Centradas las cuatro se pisan,
    # porque "4700uF/25V" mide ~15 mm y ahi solo hay 12.7.
    ("C1",  "Reference", 114.30,  67.31), ("C1",  "Value",     114.30,  72.39),
    # Las del segundo bulk van ENCIMA del riel (y debajo, en el negativo): a su
    # derecha caian mas cerca de C3/C4 que de su propio condensador y se leian
    # como si fueran de aquellos.
    ("C12", "Reference", 134.62,  57.15), ("C12", "Value",     134.62,  60.96),
    ("C2",  "Reference", 114.30, 161.29), ("C2",  "Value",     114.30, 166.37),
    ("C13", "Reference", 134.62, 172.72), ("C13", "Value",     134.62, 176.53),
    ("J1",  "Value",     30.48, 107.95), ("J1",  "Reference",  30.48, 125.73),
    ("BR1", "Reference", 78.74, 128.27), ("BR1", "Value",      78.74, 132.08),
    # --- lado primario 110V, fila propia arriba de todo. F1/NT1 (horizontales,
    # rot=90) mimican el offset de D1 (-7.62/-3.81 arriba); J3/J4 mimican el
    # offset de J1 (conector vertical, campos arriba/abajo del cuerpo). ---
    ("J3",  "Value",     25.40, 11.43), ("J3",  "Reference",  25.40, 29.21),
    ("F1",  "Reference", 53.34, 10.16), ("F1",  "Value",      53.34, 13.97),
    ("NT1", "Reference", 99.06, 10.16), ("NT1", "Value",      99.06, 13.97),
    ("J4",  "Value",     X_J4,  11.43), ("J4",  "Reference",  X_J4,  29.21),
    ("J5",  "Reference",  25.40, 44.45), ("J5", "Value",       25.40, 48.26),
    # RV1 no usa side_fields: a +-2.54 del centro sus campos caen encima de la
    # linea de L. Van al hueco que queda entre L (17.78) y el carril de N (30.48).
    ("RV1", "Reference",  83.82, 22.86), ("RV1", "Value",      83.82, 26.67),
    ("U1",  "Value",       XU,   52.07), ("U1",  "Reference",    XU,   55.88),
    ("U2",  "Reference", 180.34, 152.40), ("U2", "Value",     180.34, 156.21),
    ("D1",  "Reference",   XU,   38.10), ("D1",  "Value",        XU,   41.91),
    ("D2",  "Value",       XU,  191.77), ("D2",  "Reference",    XU,  195.58),
    ("J2",  "Value",    320.04, 106.68), ("J2",  "Reference", 320.04, 127.00),
    # El Value de #G14 va al hueco entre el cable de +12V (y=111.76) y el codo
    # de GND (y=114.30): en 111.76 exacto el cable de pin 4 le pasaba por el
    # medio a las letras y "GND" parecia etiquetar el +12V (visto en rev E/F).
    ("#G14", "Value",   297.18, 113.03),
    # Fila +5V, apretada entre las filas de GND de +12V y -12V (30.48 mm cada
    # lado): D5 arriba cerca del riel, U3 abajo cerca de su propio gnd —
    # separados para que sus etiquetas no se pisen entre si.
    ("D5",  "Reference",    XU,  92.71), ("D5",  "Value",        XU,  96.52),
    # U3 es el unico regulador que no puede llevar los campos ni encima ni
    # debajo: debajo estan su stub de GND y #G16, y encima el ramal de D5.
    # Van al hueco de abajo a la derecha del cuerpo, la unica zona despejada de
    # esta fila. x=190.5 aguanta el texto tanto si KiCad lo justifica a la
    # izquierda como si lo centra — el cable vertical de D5 acaba en y=116.84 y
    # aqui estamos por debajo.
    ("U3",  "Value",     190.50, 123.19), ("U3", "Reference",  190.50, 127.00),
    # J6: Value arriba y Reference debajo del cuerpo, como J1/J3 pero con menos
    # vuelo porque el conector es de 2 pines y la fila de abajo (y=111.76) la
    # roza el codo +12V->J2 a partir de x=292.10.
    ("J6",  "Value",     X_J6A, 99.06), ("J6",  "Reference", X_J6A, 111.76),
]

ROT = {p[0]: p[4] for p in PARTS} | {p[0]: p[4] for p in POWER}


def rail(y: float, xs: list[float], tag: str) -> list:
    """Riel horizontal partido en cada `xs`: todo corte es un punto de union."""
    return [(f"{tag}{i}", [[xs[i], y], [xs[i + 1], y]]) for i in range(len(xs) - 1)]


WIRES: list = [
    # --- entrada AC secundaria (J1, 12VAC del TR1 externo) ---
    # Sin fusible aqui: F1 esta en el primario ahora (bloque de abajo), no en
    # cada leg del secundario.
    ("AC1",      [[35.56, 114.30], [45.72, 114.30], [45.72, 104.14],
                  [83.82, 104.14], [83.82, YMID]]),
    ("AC2",      [[35.56, 119.38], [50.80, 119.38], [50.80, 135.89],
                  [99.06, 135.89], [99.06, YMID]]),
    ("CT->GND",  [[35.56, YMID], [43.18, YMID], [43.18, 124.46]]),
    ("BR+ sube", [[91.44, 109.22], [91.44, YP]]),
    ("BR- baja", [[91.44, 124.46], [91.44, YN]]),
    # --- entrada AC primaria, 230V (design-notes.md §10.2/§10.3/§12/§13) ---
    ("AC L a",   [[25.40 + XPIN, Y_L], [49.53, Y_L]]),           # J3.1 -> F1
    ("AC L b",   [[57.15, Y_L], [76.20, Y_L]]),                  # F1 -> tap RV1
    ("AC L c",   [[76.20, Y_L], [95.25, Y_L]]),                  # tap RV1 -> NT1
    ("AC L d",   [[102.87, Y_L], [X_J4, Y_L]]),                  # NT1 -> J4.1
    ("AC N a",   [[25.40 + XPIN, Y_N], [X_NJ, Y_N]]),            # J3.2 -> codo
    ("AC N b",   [[X_NJ, Y_N], [X_NJ, Y_NL]]),                   # baja al carril
    ("AC N c",   [[X_NJ, Y_NL], [76.20, Y_NL]]),                 # carril -> tap RV1
    ("AC N d",   [[76.20, Y_NL], [X_NJ2, Y_NL]]),                # tap RV1 -> codo
    ("AC N e",   [[X_NJ2, Y_NL], [X_NJ2, Y_N]]),                 # sube a la altura de J4
    ("AC N f",   [[X_NJ2, Y_N], [X_J4, Y_N]]),                   # -> J4.2
    ("RV1 tap",  [[76.20, YRV + 3.81], [76.20, Y_NL]]),          # RV1.pin2 -> carril N
    # --- PE (§13): sale de J3.3 y baja a su propio simbolo. No cruza L ni N y
    # no sigue hacia la placa: el cable de tierra va del bornero al esparrago
    # del chasis, no por cobre de PCB. El ramal del PWR_FLAG se parte en la
    # vertical para que toda union quede extremo contra extremo (regla 2). ---
    ("PE a",     [[25.40 + XPIN, Y_PE], [X_PE, Y_PE]]),          # J3.3 -> codo
    ("PE b",     [[X_PE, Y_PE], [X_PE, Y_PEF]]),                 # codo -> ramal
    ("PE c",     [[X_PE, Y_PEF], [X_PE, Y_PES]]),                # ramal -> #PE1
    ("PE flag",  [[X_PE, Y_PEF], [X_PEF, Y_PEF]]),               # ramal -> #FLG4
    # --- puente unico GND -> chasis: J5 es un retorno mas de la red GND. El
    # "punto unico" lo hace el esparrago, no el cobre. ---
    ("J5 gnd",   [[25.40 + XPIN, Y_CH], [53.34, Y_CH]]),
]
# cortes: FLG | C bulk | C ceramico | ramal D | entrada del regulador
WIRES += rail(YP, [91.44, 106.68, 121.92, 134.62, 147.32, 160.02, 172.72], "VRAW_P ")
WIRES += rail(YN, [91.44, 106.68, 121.92, 134.62, 147.32, 160.02, 170.18], "VRAW_N ")
# cortes: ramal D | C electrolitico | C ceramico | simbolo de riel | indicador
WIRES += rail(YP, [187.96, 195.58, 213.36, 238.76, 254.00, 271.78, 292.10], "+12V ")
WIRES += rail(YN, [190.50, 195.58, 213.36, 238.76, 254.00, 271.78, 288.29], "-12V ")
WIRES += [
    ("+12V->J2", [[292.10, YP], [292.10, 111.76], [314.96, 111.76]]),
    ("-12V->J2", [[288.29, YN], [288.29, 119.38], [314.96, 119.38]]),
    # --- retornos a GND (cada uno acaba en el pin del simbolo) ---
    ("C1 gnd",   [[121.92, 73.66], [121.92, YG_P]]),
    ("C12 gnd",  [[134.62, 73.66], [134.62, YG_P]]),
    ("C3 gnd",   [[147.32, 73.66], [147.32, YG_P]]),
    ("U1 gnd",   [[XU, 73.66], [XU, YG_P]]),
    ("FLG3",     [[XU, YG_P], [195.58, YG_P]]),
    ("C5 gnd",   [[213.36, 73.66], [213.36, YG_P]]),
    ("C7 gnd",   [[238.76, 73.66], [238.76, YG_P]]),
    ("C2 gnd",   [[121.92, 160.02], [121.92, YG_N]]),
    ("C13 gnd",  [[134.62, 160.02], [134.62, YG_N]]),
    ("C4 gnd",   [[147.32, 160.02], [147.32, YG_N]]),
    # La masa de U2 sale por DEBAJO del cuerpo, asi que su simbolo GND baja
    # con ella en vez de quedarse en la fila YG_N con los demas.
    ("U2 gnd",   [[XU, YN + 7.62], [XU, YN + 12.7]]),
    ("C6 gnd",   [[213.36, 160.02], [213.36, YG_N]]),
    ("C8 gnd",   [[238.76, 160.02], [238.76, YG_N]]),
    # --- diodos de proteccion: el pin va de ultimo waypoint ---
    ("D1 izq",   [[160.02, YP], [160.02, 45.72], [176.53, 45.72]]),
    ("D1 der",   [[195.58, YP], [195.58, 45.72], [184.15, 45.72]]),
    ("D2 izq",   [[160.02, YN], [160.02, 187.96], [176.53, 187.96]]),
    ("D2 der",   [[195.58, YN], [195.58, 187.96], [184.15, 187.96]]),
    # --- simbolos de riel y PWR_FLAG ---
    ("FLG1",     [[106.68, YP], [106.68, 53.34]]),
    ("FLG2",     [[106.68, YN], [106.68, 180.34]]),
    ("+12V sym", [[254.00, YP], [254.00, 53.34]]),
    ("-12V sym", [[254.00, YN], [254.00, 180.34]]),
    # --- indicadores LED ---
    ("R1->D3",   [[271.78, 73.66], [271.78, 81.28]]),
    ("D3 gnd",   [[271.78, 88.90], [271.78, 95.25]]),
    ("R2 gnd",   [[271.78, 140.97], [271.78, 138.43]]),
    ("R2->D4",   [[271.78, 148.59], [271.78, 156.21]]),
    ("D4->riel", [[271.78, 163.83], [271.78, YN]]),
    # --- GND del conector de salida ---
    ("J2 gnd a", [[314.96, 114.30], [306.07, 114.30], [306.07, 115.57]]),
    ("J2 gnd b", [[306.07, 115.57], [306.07, 116.84], [314.96, 116.84]]),
    ("J2 gnd c", [[306.07, 115.57], [302.26, 115.57]]),
    # --- riel +5V: tap sobre la union existente de VRAW_P en x=106.68 (no
    # sobre el pin de BR1, que ya esta congestionado por AC1/AC2/BR1-) ---
    ("VRAW+ ->5V", [[106.68, YP], [106.68, Y5], [147.32, Y5]]),
    ("C9->VI",     [[147.32, Y5], [172.72, Y5]]),
    ("VO->C10",    [[187.96, Y5], [213.36, Y5]]),
    ("C10->C11",   [[213.36, Y5], [238.76, Y5]]),
    ("C11->tap",   [[238.76, Y5], [254.00, Y5]]),
    ("tap->J6",    [[254.00, Y5], [X_J6, Y5]]),
    ("J6->R3",     [[X_J6, Y5], [X5_LED, Y5]]),
    ("+5V sym",    [[254.00, Y5], [254.00, Y5 - 12.7]]),
    # J6: bajada del pin de +5V al riel (union extremo contra extremo en
    # x=281.94, regla 2) y retorno a su propio simbolo GND.
    ("J6 +5V",     [[X_J6, Y_J6], [X_J6, Y5]]),
    ("J6 rtn",     [[X_J6, Y_J6 - 2.54], [269.24, Y_J6 - 2.54]]),
    ("R3->D6",     [[X5_LED, Y5_ROW + 3.81], [X5_LED, YD6 - 3.81]]),
    ("D6 gnd",     [[X5_LED, YD6 + 3.81], [X5_LED, YD6 + 10.16]]),
    ("C9 gnd",     [[147.32, Y5_ROW + 3.81], [147.32, YG_5]]),
    ("U3 gnd",     [[XU, Y5 + 7.62], [XU, YG_5]]),
    ("C10 gnd",    [[213.36, Y5_ROW + 3.81], [213.36, YG_5]]),
    ("C11 gnd",    [[238.76, Y5_ROW + 3.81], [238.76, YG_5]]),
    # D5: proteccion reversa +5V<->VRAW+, en la union de las patas VI/VO de
    # U3 (misma logica que D1 para el 7812), arriba y con menos recorrido
    # que D1/D2 porque aqui el hueco disponible es la mitad.
    ("D5 izq",     [[172.72, Y5], [172.72, YD5], [176.53, YD5]]),
    ("D5 der",     [[187.96, Y5], [187.96, YD5], [184.15, YD5]]),
]


def check_footprints() -> None:
    """Valida el mapa de huellas. Va ANTES de tocar el fichero a proposito.

    create_schematic trunca el .kicad_sch nada mas empezar, asi que un assert
    que salte despues deja la hoja vacia en disco — y una hoja vacia pasa el
    ERC con 0 avisos, o sea que no chilla por ningun lado. Ya paso una vez: se
    commiteo una hoja de 711 bytes creyendo que estaba entera. Esto es Python
    puro y no necesita servidor, asi que no hay razon para hacerlo mas tarde.
    """
    faltan = [p[0] for p in PARTS if p[0] not in FOOTPRINT]
    assert not faltan, f"componentes sin footprint: {faltan}"

    # Que la huella exista. Escribir mal el nombre no da ningun error al
    # colocar el componente: la hoja se genera igual, el ERC pasa igual, y el
    # fallo aparece al abrir la placa — con el ruteo ya hecho encima.
    if not os.path.isdir(KICAD_FP):
        print(f"AVISO: no encuentro {KICAD_FP}, no compruebo las huellas")
        return
    rotos = []
    for ref in [p[0] for p in PARTS]:
        lib, _, name = FOOTPRINT[ref].partition(":")
        base = (f"{DIR}/sam17.pretty" if lib == "sam17"
                else os.path.join(KICAD_FP, f"{lib}.pretty"))
        if not os.path.isfile(os.path.join(base, f"{name}.kicad_mod")):
            rotos.append(f"{ref} -> {FOOTPRINT[ref]}")
    print(f"huellas inexistentes: {len(rotos)} {rotos}")
    assert not rotos, f"huellas que no estan en disco: {rotos}"


# --- puntos de prueba (sec.16.10) -------------------------------------------
# Van en una fila propia debajo del circuito y NO colgando de los rieles: en los
# rieles no queda hueco sin pisarle las etiquetas a algun condensador.
#
# El valle del rizado de VRAW es el numero que decide si esta fuente regula o no
# (sec.16.5), y no hay forma de medirlo bien con un cocodrilo volando. TP1 y TP2
# existen para eso; los otros cuatro porque cuestan cero.
Y_TP = 208.28
TESTPOINTS = [
    ("TP1",  63.50, "VRAW+", "label"),
    ("TP2",  88.90, "VRAW-", "label"),
    ("TP3", 114.30, "+12V",  "sym"),
    ("TP4", 139.70, "-12V",  "sym"),
    ("TP5", 165.10, "+5V",   "sym"),
    ("TP6", 190.50, "GND",   "gnd"),
]
for _r, _x, _net, _tipo in TESTPOINTS:
    PARTS.append((_r, "Connector:TestPoint", _x, Y_TP, 0, _net))
    FOOTPRINT[_r] = "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm"
    FIELDS.append((_r, "Reference", _x + 6.35, Y_TP - 1.27))
    FIELDS.append((_r, "Value",     _x + 6.35, Y_TP + 2.54))
    if _tipo == "gnd":                       # el simbolo de masa cuelga por debajo
        POWER.append((f"#G{_r}", "power:GND", _x, Y_TP + 7.62, 0))
        WIRES.append((f"{_r} net", [[_x, Y_TP], [_x, Y_TP + 7.62]]))
    elif _tipo == "sym":                     # los de riel apuntan hacia arriba
        POWER.append((f"#P{_r}", f"power:{_net}", _x, Y_TP - 7.62, 0))
        WIRES.append((f"{_r} net", [[_x, Y_TP - 7.62], [_x, Y_TP]]))
    else:                                    # VRAW+/VRAW- no tienen simbolo de
        WIRES.append((f"{_r} net", [[_x, Y_TP], [_x, Y_TP - 7.62]]))  # potencia
        LABELS.append((_net, _x, Y_TP - 7.62))   # EN la punta del cable: a
        # media pista la etiqueta nombra la red pero deja el extremo suelto, y
        # el ERC lo canta como unconnected_wire_endpoint




# --- crowbar del riel de +12 V (sec.16.8) -----------------------------------
# Si U1 muere en corto, el bus ve VRAW+, que en el peor caso simulado son
# 20.54 V. El abs max del AS3340 son 18 V entre VCC y GND: se lleva los tres
# VCO por delante. El TL074 (42 V) y el LM13700 (36 V) ni se enteran, y el riel
# negativo no lo necesita porque el 3340 entra por un zener interno.
#
# Quien abre el circuito es F1, el fusible de primario que YA existe: el SCR
# cortocircuita el riel a traves del regulador ya muerto y F1 salta. Nada de
# fusible en serie en VRAW+ ni en el riel — eso se come el margen de dropout
# que costo todo el respin recuperar.
#
# Se usa el simbolo dedicado BT169D y no un Q_SCR_xxx generico a proposito: el
# sufijo de los genericos codifica el ORDEN FISICO de patillas, igual que en
# los puentes rectificadores, y ahi ya nos quemamos una vez.
X_CB, Y_CB = 246.38, 207.01   # corrido a la derecha: en 231 el campo
                              # de C14 se montaba con la etiqueta de TP6
X_Z,  X_C = X_CB - 15.24, X_CB - 27.94   # zener y condensador de gate
Y_GATE = Y_CB + 2.54                     # el gate del BT169D cae 2.54 bajo el ancla
PARTS += [
    ("Q1",  "Triac_Thyristor:BT169D", X_CB, Y_CB,          0, "BT169D"),
    # El zener HORIZONTAL y girado 180: asi su catodo mira al riel (queda en
    # inversa, que es como mide la tension). A 90 grados el catodo caia del
    # lado del gate, o sea en DIRECTA: conduciria a 0.7 V y dispararia el SCR
    # nada mas encender. Ademas en horizontal las etiquetas no salen giradas.
    ("D7",  "Device:D_Zener",         X_Z,  Y_CB - 3.81,  180, "BZX55C15"),
    ("R4",  "Device:R",               X_Z,  Y_GATE + 3.81,  0, "1k"),
    ("C14", "Device:C",               X_C,  Y_GATE + 3.81,  0, "100nF"),
]
FOOTPRINT.update({
    "Q1":  "Package_TO_SOT_THT:TO-92_Inline",
    "D7":  "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
    "R4":  "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "C14": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
})
POWER += [
    ("#P3",  "power:+12V", X_CB, Y_CB - 11.43, 0),
    ("#G23", "power:GND",  X_CB, Y_CB + 11.43, 0),
    ("#G24", "power:GND",  X_Z,  Y_GATE + 15.24, 0),
]
WIRES += [
    ("CB +12V",   [[X_CB, Y_CB - 11.43], [X_CB, Y_CB - 3.81]]),
    ("CB zener",  [[X_CB, Y_CB - 3.81], [X_Z + 3.81, Y_CB - 3.81]]),
    ("CB gate a", [[X_Z - 3.81, Y_CB - 3.81], [X_Z - 3.81, Y_GATE]]),
    ("CB gate b", [[X_Z - 3.81, Y_GATE], [X_CB - 3.81, Y_GATE]]),
    ("CB R4",     [[X_Z - 3.81, Y_GATE], [X_Z, Y_GATE]]),
    ("CB C14",    [[X_Z - 3.81, Y_GATE], [X_C, Y_GATE]]),
    ("CB catodo", [[X_CB, Y_CB + 3.81], [X_CB, Y_CB + 11.43]]),
    ("CB rc gnd", [[X_C, Y_GATE + 7.62], [X_Z, Y_GATE + 7.62]]),
    ("CB gnd",    [[X_Z, Y_GATE + 7.62], [X_Z, Y_GATE + 15.24]]),
]
FIELDS += [
    ("Q1",  "Reference", X_CB + 8.89, Y_CB - 1.27), ("Q1",  "Value", X_CB + 8.89, Y_CB + 2.54),
    ("D7",  "Reference", X_Z,  Y_CB - 8.89),        ("D7",  "Value", X_Z,  Y_CB - 6.35),
    ("R4",  "Reference", X_Z + 6.35, Y_GATE + 2.54),("R4",  "Value", X_Z + 6.35, Y_GATE + 6.35),
    ("C14", "Reference", X_C - 8.89, Y_GATE + 2.54),("C14", "Value", X_C - 8.89, Y_GATE + 6.35),
]


def main() -> None:
    check_footprints()
    c = Client()
    try:
        c.call("create_schematic", {"name": "sam17-power", "path": DIR})
        # A3: la plantilla nace en A4 y no hay tool para el tamano de hoja.
        # El cajetin es un (title_block ...) de nivel superior y tampoco tiene
        # tool; ambos se escriben aqui mismo por texto plano.
        with open(SCH, encoding="utf-8") as fh:
            txt = fh.read()
        title_block = (
            '(paper "A3")\n'
            "\t(title_block\n"
            '\t\t(title "Modulo 01 — Alimentacion ±12 V / +5V")\n'
            f'\t\t(date "{DATE}")\n'
            f'\t\t(rev "{REV}")\n'
            '\t\t(company "SAM17 — Sintetizador analogico modular")\n'
            '\t\t(comment 1 "Variante Europa: primario 230VAC/50Hz. Rieles ±12 V y +5V aux.")\n'
            '\t\t(comment 2 "Primario: fusible + MOV S20K275 + NTC soft-start (design-notes.md §10/§12)")\n'
            '\t\t(comment 3 "PE: J3.3 al esparrago de chasis; GND al mismo punto via J5 (§13)")\n'
            '\t\t(comment 4 "Bus: J2 analogico +12/G/G/-12; +5V por J6 con retorno dedicado (§10.1)")\n'
            "\t)"
        )
        with open(SCH, "w", encoding="utf-8") as fh:
            fh.write(txt.replace('(paper "A4")', title_block, 1))

        for ref, sym, x, y, rot, val in PARTS:
            c.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": sym, "reference": ref,
                "value": val, "footprint": FOOTPRINT[ref],
                "position": {"x": x, "y": y + YOFF, "unit": "mm"}})
            if rot:
                c.call("rotate_schematic_component",
                       {"schematicPath": SCH, "reference": ref, "angle": rot})
        for ref, sym, x, y, rot in POWER:
            c.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": sym, "reference": ref,
                "value": POWER_VALUE.get(ref, sym.split(":")[1]),
                "position": {"x": x, "y": y + YOFF, "unit": "mm"}})
            if rot:
                c.call("rotate_schematic_component",
                       {"schematicPath": SCH, "reference": ref, "angle": rot})
        print(f"colocados {len(PARTS)} componentes + {len(POWER)} simbolos de potencia")

        # Dos comprobaciones sobre los pines, antes de tirar un solo cable. La
        # segunda es la que importa: KiCad une pin y cable con ~1 mm de
        # tolerancia, asi que el ERC da por bueno un trazado torcido — asi
        # sobrevivieron J3/J4 cableados a 0.36 mm de sus pines durante toda una
        # revision. Aqui se exige coincidencia exacta contra los vertices
        # declarados en WIRES, y si falla se aborta antes de dibujar nada.
        ends = {(round(wx, 2), round(wy + YOFF, 2))
                for _lbl, wp in WIRES for wx, wy in wp}
        offgrid, loose = [], []
        for ref in [p[0] for p in PARTS] + [p[0] for p in POWER]:
            txt = str(c.call("get_schematic_pin_locations",
                             {"schematicPath": SCH, "reference": ref}))
            for n, _nm, x, y in re.findall(
                    r"Pin (\w+) \(([^)]+)\): x=([\d.]+), y=([\d.]+)",
                    txt.replace("\\n", "\n")):
                px, py = float(x), float(y)
                for v in (px, py):
                    if abs(round(v / 1.27) * 1.27 - v) > 0.01:
                        offgrid.append((ref, n, x, y))
                if not any(abs(px - ex) < 0.01 and abs(py - ey) < 0.01
                           for ex, ey in ends):
                    loose.append(f"{ref}.{n}@({px:.2f},{py:.2f})")
        print(f"pines fuera de rejilla: {len(offgrid)} {offgrid[:5]}")
        print(f"pines sin extremo de cable exacto: {len(loose)} {loose[:8]}")
        assert not loose, f"cableado a ojo; corrigelo antes de seguir: {loose}"

        bad = 0
        for label, wp in WIRES:
            shifted = [[wx, wy + YOFF] for wx, wy in wp]
            r = str(c.call("add_schematic_wire",
                           {"schematicPath": SCH, "waypoints": shifted}))
            if "success" not in r.lower():
                bad += 1
                print(f"  WIRE FAIL {label}: {r[:160]}")
        print(f"cables: {len(WIRES) - bad}/{len(WIRES)} OK")

        # position es un ARRAY [x, y] aqui, no un objeto: pasarlo como objeto
        # se acepta sin error pero la etiqueta no se coloca.
        for name, x, y in LABELS:
            r = str(c.call("add_schematic_net_label", {
                "schematicPath": SCH, "netName": name, "position": [x, y + YOFF]}))
            print(f"  label {name}: {r[:80]}")

        for text, x, y in TEXTS:
            c.call("add_schematic_text", {
                "schematicPath": SCH, "text": text, "position": [x, y + YOFF]})
        print(f"notas: {len(TEXTS)}")

        r = str(c.call("batch_set_schematic_property_positions", {
            "schematicPath": SCH,
            # KiCad SUMA la rotacion del simbolo al angulo del campo (regla 3
            # de arriba), asi que un 0 aqui sale vertical en F1/BR1/D3/D4 y
            # referencia y valor acaban uno encima del otro.
            "updates": [{"reference": ref, "property": prop,
                         "x": x, "y": y + YOFF,
                         "angle": (360 - ROT.get(ref, 0)) % 360
                                  if ROT.get(ref) in (90, 270) else 0}
                        for ref, prop, x, y in FIELDS]}))
        print(f"campos: {r[:90]}")
        print(str(c.call("lint_schematic_cosmetic", {
            "schematicPath": SCH, "passes": ["hide_pin_names"]}))[:80])

        erc = str(c.call("run_erc", {"schematicPath": SCH}))
        print(f"ERC: {erc[:110]}")
        for tool, ext in [("export_schematic_svg", "svg"), ("export_schematic_pdf", "pdf")]:
            out = f"{DIR}/../schematics/sam17-power.{ext}"
            c.call(tool, {"schematicPath": SCH, "outputPath": out})
        print("exportado a ../schematics/sam17-power.{svg,pdf}")
    finally:
        c.close()


if __name__ == "__main__":
    main()
