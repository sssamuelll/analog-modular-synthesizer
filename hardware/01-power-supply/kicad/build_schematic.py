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
  - Flujo izquierda->derecha: J1 -> F1 -> BR1 -> reguladores -> J2.
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

Reglas de KiCad que mandan sobre el trazado, descubiertas midiendo (no estan
documentadas en el server):
  1. Un pin solo conecta si un cable TERMINA en el. Que el riel le pase por
     encima no conecta nada -> los rieles van partidos pin a pin.
  2. Aterrizar a media linea es fragil. Por eso los rieles se cortan tambien en
     cada punto donde entra un ramal, y cada union queda extremo contra extremo.
  3. KiCad SUMA la rotacion del simbolo al angulo de sus campos: un componente
     girado 90/270 necesita el angulo complementario en Reference/Value o el
     texto sale vertical y las dos etiquetas se pisan.
Todo en multiplos de 1.27 mm: un extremo fuera de rejilla envenena las uniones
de toda la hoja.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
from kicad_mcp_client import Client  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
SCH = f"{DIR}/sam17-power.kicad_sch"

YP, YN = 66.04, 167.64          # rieles positivo / negativo
YMID = 116.84                   # eje del puente y del conector de entrada
YG_P, YG_N = 86.36, 147.32      # fila de simbolos GND (arriba / abajo)
XU = 180.34                     # columna de los reguladores
YOFF = 25.4                     # baja todo el dibujo para centrarlo en A3
DATE, REV = "2026-08-12", "D"

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

# Lado primario 110 VAC (design-notes.md §10.2/§10.3), fila propia arriba de
# todo lo demas (y<45.72, hueco libre hasta ahora).
#
# OJO con Conn_01x02_Pin: medido con get_schematic_pin_locations, NO es el
# offset simetrico +-2.54 que tienen otros conectores — es (+0.33, +2.87)
# desde el centro. Server de KiCad, no yo: confirmado con Conn_01x03_Pin
# tambien (offsets -2.21/+0.33/+2.87, no -2.54/0/+2.54). La tolerancia de
# snap (1 mm) disimulaba el error en J1 porque redondear a la rejilla de
# 1.27 quedaba a <0.33 mm del pin real; aqui J3/J4 usan los valores medidos
# directo, sin redondear a ojo.
Y_M = 20.32                     # centro de J3/J4
Y_L = Y_M + 0.33                # linea/vivo = pin1 (fusible + MOV + NTC en serie)
Y_N = Y_M + 2.87                # neutro = pin2 (paso directo, sin componentes)
YRV = Y_L + 3.81                # centro del MOV: su pin1 cae EXACTO en Y_L

PARTS = [
    # --- lado primario, 110 VAC (design-notes.md §10.2/§10.3): el fusible va
    # AQUI, no en el secundario — protege contra un corto reflejado desde el
    # secundario, no solo un corto local. TR1 es externo (no esta en esta
    # placa): J4 es la salida hacia su devanado primario. ---
    ("J3",  "Connector:Conn_01x02_Pin",       25.40, Y_M,     0, "AC 230V IN"),
    ("F1",  "Device:Fuse",                    53.34, Y_L,    90, "250mA T"),
    ("RV1", "Device:Varistor",                76.20, YRV,     0, "S20K275"),
    ("NT1", "Device:Thermistor_NTC",          99.06, Y_L,    90, "NTC 5R/2A"),
    ("J4",  "Connector:Conn_01x02_Pin",      113.03, Y_M,     0, "TR1 pri (ext)"),
    ("J1",  "Connector:Conn_01x03_Pin",       30.48, YMID,    0, "12VAC CT 2A"),
    ("BR1", "Device:D_Bridge_+-AA",           91.44, YMID,   90, "KBP206"),
    # --- riel +12V ---
    ("C1",  "Device:C_Polarized",            121.92, 69.85,   0, "4700uF/25V"),
    ("C3",  "Device:C",                      147.32, 69.85,   0, "0.33uF"),
    ("U1",  "Regulator_Linear:LM7812_TO220",    XU, YP,       0, "LM7812"),
    ("C5",  "Device:C_Polarized",            213.36, 69.85,   0, "100uF"),
    ("C7",  "Device:C",                      238.76, 69.85,   0, "0.1uF"),
    ("D1",  "Diode:1N4001",                     XU, 45.72,    0, "1N4001"),
    ("R1",  "Device:R",                      271.78, 69.85,   0, "2k2"),
    ("D3",  "Device:LED",                    271.78, 85.09,  90, "RED"),
    # --- riel -12V ---
    ("C2",  "Device:C_Polarized",            121.92, 163.83,  0, "4700uF/25V"),
    ("C4",  "Device:C",                      147.32, 163.83,  0, "0.33uF"),
    ("U2",  "Regulator_Linear:LM7912_TO220",    XU, YN,       0, "LM7912"),
    ("C6",  "Device:C_Polarized",            213.36, 163.83,  0, "100uF"),
    ("C8",  "Device:C",                      238.76, 163.83,  0, "0.1uF"),
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
]

POWER = [
    ("#G1",  "power:GND",  43.18, 124.46,   0),
    ("#G2",  "power:GND", 121.92, YG_P,     0),
    ("#G3",  "power:GND", 147.32, YG_P,     0),
    ("#G4",  "power:GND",     XU, YG_P,     0),
    ("#G5",  "power:GND", 213.36, YG_P,     0),
    ("#G6",  "power:GND", 238.76, YG_P,     0),
    ("#G7",  "power:GND", 271.78,  95.25,   0),
    ("#G8",  "power:GND", 121.92, YG_N,   180),
    ("#G9",  "power:GND", 147.32, YG_N,   180),
    ("#G10", "power:GND",     XU, YG_N,   180),
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
]

# nombra los rieles crudos; sin esto el netlist los llama Net-(BR1-+)
LABELS = [("VRAW+", 99.06, YP), ("VRAW-", 99.06, YN)]


def side_fields(ref: str, x: float, y: float) -> list:
    """Campos a la derecha de un componente vertical (C, R, LED girado).

    +7.62 en x: centrados a +3.81 el texto de "4700uF/25V" pisaba su propio
    simbolo, y a 25.4 mm del vecino todavia sobra sitio.
    """
    return [(ref, "Reference", x + 7.62, y - 2.54), (ref, "Value", x + 7.62, y + 2.54)]


# La colocacion automatica da campos verticales solapados en los simbolos
# girados (F1, BR1, D3, D4), asi que aqui va cada campo a mano.
FIELDS: list = []
for _r, _x, _y in [("C1", 121.92, 69.85), ("C3", 147.32, 69.85), ("C5", 213.36, 69.85),
                   ("C7", 238.76, 69.85), ("C2", 121.92, 163.83), ("C4", 147.32, 163.83),
                   ("C6", 213.36, 163.83), ("C8", 238.76, 163.83),
                   ("R1", 271.78, 69.85), ("D3", 271.78, 85.09),
                   ("R2", 271.78, 144.78), ("D4", 271.78, 160.02),
                   ("C9", 147.32, Y5_ROW), ("C10", 213.36, Y5_ROW), ("C11", 238.76, Y5_ROW),
                   ("R3", X5_LED, Y5_ROW), ("D6", X5_LED, YD6),
                   ("RV1", 76.20, YRV)]:
    FIELDS += side_fields(_r, _x, _y)
FIELDS += [
    ("J1",  "Value",     30.48, 107.95), ("J1",  "Reference",  30.48, 125.73),
    ("BR1", "Reference", 78.74, 128.27), ("BR1", "Value",      78.74, 132.08),
    # --- lado primario 110V, fila propia arriba de todo. F1/NT1 (horizontales,
    # rot=90) mimican el offset de D1 (-7.62/-3.81 arriba); J3/J4 mimican el
    # offset de J1 (conector vertical, campos arriba/abajo del cuerpo). ---
    ("J3",  "Value",     25.40, 11.43), ("J3",  "Reference",  25.40, 29.21),
    ("F1",  "Reference", 53.34, 10.16), ("F1",  "Value",      53.34, 13.97),
    ("NT1", "Reference", 99.06, 10.16), ("NT1", "Value",      99.06, 13.97),
    ("J4",  "Value",    113.03, 11.43), ("J4",  "Reference", 113.03, 29.21),
    ("U1",  "Value",       XU,   52.07), ("U1",  "Reference",    XU,   55.88),
    ("U2",  "Reference",   XU,  177.80), ("U2",  "Value",        XU,  181.61),
    ("D1",  "Reference",   XU,   38.10), ("D1",  "Value",        XU,   41.91),
    ("D2",  "Value",       XU,  191.77), ("D2",  "Reference",    XU,  195.58),
    ("J2",  "Value",    320.04, 106.68), ("J2",  "Reference", 320.04, 127.00),
    ("#G14", "Value",   299.72, 111.76),
    # Fila +5V, apretada entre las filas de GND de +12V y -12V (30.48 mm cada
    # lado): D5 arriba cerca del riel, U3 abajo cerca de su propio gnd —
    # separados para que sus etiquetas no se pisen entre si.
    ("D5",  "Reference",    XU,  92.71), ("D5",  "Value",        XU,  96.52),
    ("U3",  "Reference",    XU, 127.00), ("U3",  "Value",        XU, 130.81),
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
    # --- entrada AC primaria, 110V (design-notes.md §10.2/§10.3) ---
    ("AC L a",   [[30.34, Y_L], [49.53, Y_L]]),                 # J3.L -> F1
    ("AC L b",   [[57.15, Y_L], [76.20, Y_L]]),                 # F1 -> tap RV1
    ("AC L c",   [[76.20, Y_L], [95.25, Y_L]]),                 # tap RV1 -> NT1
    ("AC L d",   [[102.87, Y_L], [117.97, Y_L]]),                # NT1 -> J4.L
    ("AC N a",   [[30.34, Y_N], [76.20, Y_N]]),                  # J3.N -> tap RV1
    ("AC N b",   [[76.20, Y_N], [117.97, Y_N]]),                 # tap RV1 -> J4.N
    ("RV1 tap",  [[76.20, Y_N], [76.20, YRV + 3.81]]),           # tap N -> RV1.pin2
]
# cortes: FLG | C bulk | C ceramico | ramal D | entrada del regulador
WIRES += rail(YP, [91.44, 106.68, 121.92, 147.32, 160.02, 172.72], "VRAW_P ")
WIRES += rail(YN, [91.44, 106.68, 121.92, 147.32, 160.02, 172.72], "VRAW_N ")
# cortes: ramal D | C electrolitico | C ceramico | simbolo de riel | indicador
WIRES += rail(YP, [187.96, 195.58, 213.36, 238.76, 254.00, 271.78, 292.10], "+12V ")
WIRES += rail(YN, [187.96, 195.58, 213.36, 238.76, 254.00, 271.78, 288.29], "-12V ")
WIRES += [
    ("+12V->J2", [[292.10, YP], [292.10, 111.76], [314.96, 111.76]]),
    ("-12V->J2", [[288.29, YN], [288.29, 119.38], [314.96, 119.38]]),
    # --- retornos a GND (cada uno acaba en el pin del simbolo) ---
    ("C1 gnd",   [[121.92, 73.66], [121.92, YG_P]]),
    ("C3 gnd",   [[147.32, 73.66], [147.32, YG_P]]),
    ("U1 gnd",   [[XU, 73.66], [XU, YG_P]]),
    ("FLG3",     [[XU, YG_P], [195.58, YG_P]]),
    ("C5 gnd",   [[213.36, 73.66], [213.36, YG_P]]),
    ("C7 gnd",   [[238.76, 73.66], [238.76, YG_P]]),
    ("C2 gnd",   [[121.92, 160.02], [121.92, YG_N]]),
    ("C4 gnd",   [[147.32, 160.02], [147.32, YG_N]]),
    ("U2 gnd",   [[XU, 160.02], [XU, YG_N]]),
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
    ("tap->R3",    [[254.00, Y5], [X5_LED, Y5]]),
    ("+5V sym",    [[254.00, Y5], [254.00, Y5 - 12.7]]),
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


def main() -> None:
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
            "\t)"
        )
        with open(SCH, "w", encoding="utf-8") as fh:
            fh.write(txt.replace('(paper "A4")', title_block, 1))

        for ref, sym, x, y, rot, val in PARTS:
            c.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": sym, "reference": ref,
                "value": val, "position": {"x": x, "y": y + YOFF, "unit": "mm"}})
            if rot:
                c.call("rotate_schematic_component",
                       {"schematicPath": SCH, "reference": ref, "angle": rot})
        for ref, sym, x, y, rot in POWER:
            c.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": sym, "reference": ref,
                "value": sym.split(":")[1],
                "position": {"x": x, "y": y + YOFF, "unit": "mm"}})
            if rot:
                c.call("rotate_schematic_component",
                       {"schematicPath": SCH, "reference": ref, "angle": rot})
        print(f"colocados {len(PARTS)} componentes + {len(POWER)} simbolos de potencia")

        offgrid = []
        for ref in [p[0] for p in PARTS] + [p[0] for p in POWER]:
            txt = str(c.call("get_schematic_pin_locations",
                             {"schematicPath": SCH, "reference": ref}))
            for n, _nm, x, y in re.findall(
                    r"Pin (\d) \(([^)]+)\): x=([\d.]+), y=([\d.]+)", txt.replace("\\n", "\n")):
                for v in (float(x), float(y)):
                    if abs(round(v / 1.27) * 1.27 - v) > 0.01:
                        offgrid.append((ref, n, x, y))
        print(f"pines fuera de rejilla: {len(offgrid)} {offgrid[:5]}")

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
