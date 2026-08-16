"""Genera sam17-power-v2.kicad_sch a partir de las notas de diseno del modulo.

Fuente: ../notes/design-notes.md (topologia, valores, presupuesto de
corriente) + hardware/01-power-supply/kicad/build_schematic.py (v1, del que
este script hereda por cirugia: quita LM2940/LM2990, conserva todo lo demas).
Trazado con cables reales sobre coordenadas de pin, no con etiquetas de red —
ver convenciones abajo.

Uso (requiere hardware/tools/kicad_mcp_client.py y un KiCAD-MCP-Server
corriendo/instalado, ver hardware/tools/README.md):

    python build_schematic.py

Es destructivo por diseno: create_schematic sobreescribe el .kicad_sch. Volver
a correrlo reconstruye la hoja desde cero a partir de este archivo, que es la
fuente de verdad real.

CIRUGIA DE HERENCIA (Task 5 del plan v2, notes §3.1):
  - MUEREN: U1(v1)=LM2940CT-12 y sus pasivos directos (C3,C5,C7,D1); U2(v1)=
    LM2990T-12 y sus pasivos directos (C4,C6,C8,D2). Los designadores U1/U2
    se REUTILIZAN para los pre-reguladores nuevos (misma posicion en la
    cascada, ahora alimentan a la pareja LT3045/LT3094 de la Task 6 en vez
    de ser el regulador final).
  - SOBREVIVEN intactos: entrada 230V (J1/F1/RV1/NT1/J4+J5 faston),
    rectificacion (BR1), bulk (C1/C2/C12/C13), 7805 completo (C9/U3/C10/
    C11/D5/R3/D6/J6), crowbar completo (D7/Q1/R4/C14), LED de riel (R1/D3/
    R2/D4), J2, TP1-TP6, check_footprints().
  - NUEVO: U1=LM2941CT (pre-reg +13.1V), U2=LM2991T (pre-reg -12.9V), con
    sus divisores R5+RV2/R6 y R7+RV3/R8, C17/C18 (salida), C27/C28
    (entrada), D12/D13 (out->in), TP7/TP8, TVS D8/D9, y J7 (derivacion de
    red hacia la SMPS digital IRM-15-5).

NETS: +13V1 y -12V9 son nodos NUEVOS (salida de los pre-reg). El net "+12V"/
"-12V" de la v1 (LED indicador R1/D3, R2/D4, bus J2, TP3/TP4, crowbar) se
CONSERVA con el mismo nombre pero queda ISLA electrica en esta tarea —
self-driven por sus propios simbolos de potencia (#P1/#N1), sin wire hasta
U1/U2 nuevos. La Task 6 (etapa LT3045/LT3094) cuelga de +13V1/-12V9 y
probablemente sea quien reconecte ese bus a la salida final +12.000V/
-12.000V real. GNDREF (masa de referencia analogica) tampoco existe todavia
— los divisores R5+RV2/R6 y R7+RV3/R8 van a GND comun por ahora.

SIMBOLOS LOCALES: LM2941CT y LM2991T NO existen en ninguna libreria estandar
de KiCad 10 (grep vacio en Regulator_Linear.kicad_sym y en el resto de
symbols/*.kicad_sym) — se definen aqui mismo via create_symbol()/
register_symbol_library() en una libreria de proyecto sam17.kicad_sym (ver
setup_local_symbols()), con la pinera verificada contra el datasheet primario
de TI (paginas de "Pin Configuration and Functions", SNVS770I para el
LM2941 y SNVS099I para el LM2991, ambas p.3): pin1=ADJ, pin2=ON/OFF(activo-
segun cada chip, ver design-notes.md §1.1/§1.2), pin3=GND(LM2941)/IN(LM2991),
pin4=IN(LM2941)/GND(LM2991), pin5=OUT. El simbolo dibuja ambos chips con la
MISMA geometria de pines (IN izquierda, OUT derecha, GND abajo, ADJ/ON-OFF
arriba) — solo el NUMERO de pin en cada posicion cambia entre los dos chips,
igual que en el paquete fisico real.

Convenciones del dibujo (heredadas de v1, con lo que agrega esta tarea):
  - Flujo izquierda->derecha: J3/J1 -> BR1 -> reguladores -> J2 (±12V, isla)
    y J6 (+5V).
  - Riel positivo arriba, negativo abajo, puente centrado entre ambos.
  - GND no es un bus largo: cada retorno es un stub corto a un simbolo power:GND
    (todos son la misma net). Los del riel negativo van girados 180 para que el
    grafico apunte hacia arriba.
  - Hoja A3.
  - Riel +5V (design-notes.md §10.1) en la fila intermedia, sin cambios v1.
  - J6 sin cambios v1 (issue #8, opcion C).
  - Primario 230V/50Hz sin cambios v1, salvo J7 nuevo (Step 5 del plan v2):
    cuelga DESPUES de F1+RV1 y ANTES de NT1/J4 (lado 230V de la barrera,
    "antes del primario" de TR1) — mismo nodo L/N que ve NT1 a la entrada,
    para que el inrush-limiter de NT1 (dimensionado para TR1) no le imponga
    caida a la SMPS digital ni la SMPS le sume corriente de inrush al NTC.
  - Pre-reguladores U1/U2: se colocan en la MISMA columna XU que ocupaban
    LM2940/LM2990 en v1, pero con simbolo propio de 5 pines: IN/OUT en la
    fila del riel (offset ∓10.16 del ancla, verificado empiricamente —
    DISTINTO del offset ∓7.62 que usaba LM7812_TO220 en v1 y del ∓10.16 que
    ya usaba LM2990SX-12, cada simbolo con su propia geometria), GND abajo
    (offset +7.62, igual que ambos simbolos v1), ADJ/ON-OFF arriba del
    cuerpo (offset ∓3.81 en X, -7.62 en Y — pines nuevos, sin equivalente
    v1). D12/D13 (out->in) ocupan la MISMA posicion y rotacion que D1/D2 en
    v1 — se verifico con el datasheet que D1 (LM2940, positivo) usa
    anodo=OUT/catodo=IN y D2 (LM2990, negativo) usa anodo=IN/catodo=OUT (NO
    es un espejo trivial: para un regulador negativo la falla de backfeed
    ocurre cuando VIN sube por encima de VOUT al apagar, asi que el diodo
    debe conducir en sentido contrario) — D12/D13 replican ese patron exacto
    porque protegen la MISMA falla en el MISMO tipo de regulador.
  - Divisores R5+RV2/R6 y R7+RV3/R8: columna propia a la derecha de C17/C18,
    con huecos de 2.54mm explicitos entre cada pieza en serie — un pin no
    conecta con otro por simple coincidencia de coordenadas, hace falta un
    cable real terminando en el (comprobado empiricamente, ver mas abajo).
    RV2/RV3 se usan como reostato: el wiper (pin2) se cortocircuita al
    extremo que da hacia el riel, dejando el rango util entre wiper y el
    extremo que da hacia GND/ADJ (0 a 1k, igual que documenta el bom.csv).
  - TVS D8/D9: D8 catodo hacia +13V1 (protege sobretension positiva), D9
    catodo hacia GND / anodo hacia -12V9 ("invertido" respecto a D8, BOM
    dixit) — orientacion confirmada contra la GRAFICA del simbolo
    Diode:SMAJ15A (que extiende Diode:SM6T6V8A): el polyline de la barra
    esta del lado del pin1 y el triangulo (flecha) apunta hacia ese mismo
    lado — pin1=catodo, pin2=anodo, igual que en 1N4001.
  - TP7/TP8: a diferencia de TP1-TP6 (que viven en la fila comun Y_TP, lejos
    de todo, con conexion "a distancia" solo por nombre de red — tecnica que
    usa v1 para VRAW+/VRAW- via LABELS y para +12V/-12V/+5V via un simbolo
    power: dedicado), TP7/TP8 se sueldan con un stub DIRECTO y corto a la
    red +13V1/-12V9 real (mas simple: no hay simbolo power:+13V1 en ninguna
    libreria estandar, asi que un net label normal alcanza y de paso ya
    aporta la conexion fisica).
  - Bus "+12V"/"-12V" heredado (LED R1/D3, R2/D4, J2, TP3/TP4, crowbar):
    se copia intacto de v1, SIN wire hacia U1/U2 nuevos — sigue siendo una
    red valida para ERC porque los propios simbolos de potencia #P1/#N1 la
    manejan como salida (regla que ya usaba v1). La Task 6 debera
    reconectarla a la salida real de LT3045/LT3094 cuando esa etapa exista.

Reglas de KiCad que mandan sobre el trazado, descubiertas midiendo (no estan
documentadas en el server, algunas nuevas de esta tarea):
  1. Un pin solo conecta si un cable TERMINA en el. Que el riel le pase por
     encima no conecta nada -> los rieles van partidos pin a pin.
  2. Aterrizar a media linea es fragil. Por eso los rieles se cortan tambien en
     cada punto donde entra un ramal, y cada union queda extremo contra extremo.
  3. KiCad SUMA la rotacion del simbolo al angulo de sus campos: un componente
     girado 90/270 necesita el angulo complementario en Reference/Value o el
     texto sale vertical y las dos etiquetas se pisan.
  4. Los pines de Conn_01x0N_Pin caen en ancla + (5.08, 2.54*(k-1) - 2.54*
     floor((N-1)/2)), con k el numero de pin empezando en 1.
  5. DOS PINES EN LAS MISMAS COORDENADAS NO SE CONECTAN SI NINGUN CABLE LOS
     UNE (comprobado con generate_netlist: dos resistencias con pines
     tocandose, sin wire, salen como 4 redes "unconnected" separadas). Toda
     conexion, por corta que sea, necesita un add_schematic_wire real.
  6. Dos cables que se CRUZAN sin compartir un VERTICE (ni extremo-con-
     extremo ni extremo-sobre-el-cuerpo del otro) NO se conectan — es un
     cruce visual, no eléctrico (comprobado con generate_netlist/run_erc:
     dos resistencias en redes separadas cuyos cables se cruzan en "+"
     siguen dando 4 pines "not connected", cero fusion de red). Un cable
     SI se conecta si su EXTREMO cae sobre el CUERPO de otro cable ya
     trazado (asi es como TP7/TP8 y J7 "pinchan" un riel existente sin
     partirlo en la lista de cortes).
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
import uuid

# Algunos resultados del MCP server traen caracteres fuera de cp1252 (p.ej.
# "check" / "cross mark" en mensajes de estado) -- en Windows, con stdout
# redirigido a fichero, el print() por defecto revienta con
# UnicodeEncodeError a mitad de main(). Forzar UTF-8 aqui evita ese crash.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
from kicad_mcp_client import Client  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
SCH = f"{DIR}/sam17-power-v2.kicad_sch"
PRO = f"{DIR}/sam17-power-v2.kicad_pro"
SYM = f"{DIR}/sam17.kicad_sym"          # libreria local: LM2941CT/LM2991T
NET = f"{DIR}/sam17-power-v2.net"
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
DATE, REV = "2026-08-16", "A"

# Riel +5V (design-notes.md §10.1): fila intermedia entre +12V y -12V. Cuelga
# del VRAW+ existente (tap sobre la union de la rail en x=106.68) en vez de
# repetir un bulk cap propio. Sin cambios v1.
Y5 = YMID                       # 116.84: altura del riel/regulador (como YP para U1)
Y5_ROW = Y5 + 3.81              # fila de C9/C10/C11/R3
YG_5 = 129.54                   # fila de retornos a GND del riel +5V
YD5 = Y5 - 16.51                # diodo de proteccion, arriba (lado +12V)
YD6 = Y5_ROW + 15.24            # LED indicador
X5_LED = 297.18                 # columna propia del indicador +5V

# J6, feed de +5V (issue #8, opcion C). Sin cambios v1.
X_J6A = 287.02
X_J6 = X_J6A - XPIN
Y_J6 = 106.68

# Lado primario 230 VAC (design-notes.md §10.2/§10.3/§12/§13). Sin cambios v1.
Y_M = 20.32
Y_L = Y_M - 2.54
Y_N = Y_M
Y_PE = Y_M + 2.54
YRV = Y_L + 3.81
Y_NL = 30.48
X_NJ, X_NJ2 = 45.72, 116.84
X_J4A = 127.00
X_J4 = X_J4A - XPIN
X_PE, Y_PES = 33.02, 33.02
Y_PEF, X_PEF = 27.94, 40.64
Y_CH = 40.64

# --- J7 (Step 5 del plan v2): derivacion 230V hacia la SMPS digital
# IRM-15-5, DESPUES de F1+RV1 y ANTES de NT1/J4 (spec §7 — comparte fusible,
# no comparte inrush-limiter porque NT1 esta dimensionado para TR1). Tapa el
# nodo L en x=76.20 (mismo punto donde ya tapa RV1) y el carril de N en el
# mismo x, cada uno por su PROPIA columna vertical para no cruzarse entre si
# ni pisar la union RV1/carril-N que ya existe en (76.20, Y_NL). ---
X_J7A = 76.20                   # ancla de J7 (misma X que el tap de RV1)
Y_J7 = 53.34                    # fila propia, debajo del bloque 230V (Y_CH=40.64)
X_J7L = 88.90                   # columna vertical de la baja de L (evita cruzar
                                 # el nodo RV1/N en 76.20,30.48)
X_J7N = 93.98                   # columna vertical de la baja de N (distinta de
                                 # X_J7L para que las dos bajadas no se toquen)

PARTS = [
    # --- lado primario, 230 VAC (design-notes.md §10.2/§10.3): el fusible va
    # AQUI, no en el secundario. TR1 es externo (no esta en esta placa). ---
    ("J3",  "Connector:Conn_01x03_Pin",       25.40, Y_M,     0, "AC 230V IN"),
    # Subido de 250mA a 1.6A T (Step 6, notes v2 §3): con el TR1 real del BOM
    # (120 VA, no los 24 VA de la nota v1 que fijo 250mA) mas el tap nuevo de
    # J7 hacia la SMPS IRM-15-5 (0.2A/230Vac typ., datasheet meanwell.com),
    # la carga primaria sube a ~0.72A -- 250mA se fundiria en operacion normal.
    ("F1",  "Device:Fuse",                    53.34, Y_L,    90, "1.6A T"),
    ("RV1", "Device:Varistor",                76.20, YRV,     0, "S20K275"),
    ("NT1", "Device:Thermistor_NTC",          99.06, Y_L,    90, "NTC 5R/2A"),
    ("J4",  "Connector:Conn_01x02_Pin",       X_J4A, Y_N,   180, "TR1 pri (ext)"),
    # Faston del puente unico GND -> chasis (§13).
    ("J5",  "Connector:Conn_01x01_Pin",       25.40, Y_CH,    0, "CHASIS"),
    # J7: derivacion hacia la SMPS digital, lado 230V de la barrera (spec §7).
    ("J7",  "Connector:Conn_01x02_Pin",       X_J7A, Y_J7,    0, "SMPS 230V TAP"),
    ("J1",  "Connector:Conn_01x03_Pin",       30.48, YMID,    0, "12VAC CT 2A"),
    ("BR1", "Device:D_Bridge_+-AA",           91.44, YMID,   90, "DB207"),
    # --- riel +13V1 (pre-reg positivo, U1=LM2941CT) ---
    ("C1",  "Device:C_Polarized",            121.92, 69.85,   0, "4700uF/25V"),
    ("C12", "Device:C_Polarized",            134.62, 69.85,   0, "4700uF/25V"),
    ("C27", "Device:C",                      147.32, 69.85,   0, "0.47uF"),
    ("U1",  "sam17:LM2941CT",                   XU, YP,       0, "LM2941CT/NOPB"),
    ("D12", "Diode:1N4001",                     XU, 45.72,    0, "1N4001"),
    ("C17", "Device:C_Polarized",            213.36, 69.85,   0, "22uF ESR"),
    ("R5",  "Device:R",                      226.06, 69.85,   0, "8.66k"),
    ("RV2", "Device:R_Potentiometer_Trim",   226.06, 80.01,   0, "1k"),
    ("R6",  "Device:R",                      226.06, 90.17,   0, "1k"),
    ("D8",  "Diode:SMAJ15A",                 241.30, 69.85,  270, "SMAJ15A"),
    # --- riel -12V9 (pre-reg negativo, U2=LM2991T) ---
    ("C2",  "Device:C_Polarized",            121.92, 163.83,  0, "4700uF/25V"),
    ("C13", "Device:C_Polarized",            134.62, 163.83,  0, "4700uF/25V"),
    ("C28", "Device:C",                      147.32, 163.83,  0, "0.47uF"),
    ("U2",  "sam17:LM2991T",                    XU, YN,       0, "LM2991T/NOPB"),
    ("D13", "Diode:1N4001",                     XU, 187.96, 180, "1N4001"),
    ("C18", "Device:C_Polarized",            213.36, 163.83,  0, "22uF ESR"),
    ("R7",  "Device:R",                      226.06, 163.83,  0, "9.09k"),
    ("RV3", "Device:R_Potentiometer_Trim",   226.06, 153.67,  0, "1k"),
    ("R8",  "Device:R",                      226.06, 143.51,  0, "1k"),
    ("D9",  "Diode:SMAJ15A",                 241.30, 171.45,  90, "SMAJ15A"),
    # --- bus "+12V"/"-12V" heredado de v1 — LED indicador, isla electrica
    # hasta que la Task 6 lo reconecte a la salida real del LT3045/LT3094 ---
    ("R1",  "Device:R",                      271.78, 69.85,   0, "2k2"),
    ("D3",  "Device:LED",                    271.78, 85.09,  90, "RED"),
    ("R2",  "Device:R",                      271.78, 144.78,  0, "2k2"),
    ("D4",  "Device:LED",                    271.78, 160.02, 90, "YEL"),
    ("J2",  "Connector:Conn_01x04_Pin",      320.04, 116.84, 180, "BUS +12/G/G/-12"),
    # --- riel +5V aux (design-notes.md §10.1): sin cambios v1 ---
    ("C9",  "Device:C",                      147.32, Y5_ROW,  0, "0.33uF"),
    ("U3",  "Regulator_Linear:LM7805_TO220",     XU, Y5,      0, "LM7805"),
    ("C10", "Device:C_Polarized",            213.36, Y5_ROW,  0, "100uF"),
    ("C11", "Device:C",                      238.76, Y5_ROW,  0, "0.1uF"),
    ("D5",  "Diode:1N4001",                      XU, YD5,     0, "1N4001"),
    ("R3",  "Device:R",                      X5_LED, Y5_ROW,  0, "680"),
    ("D6",  "Device:LED",                    X5_LED, YD6,    90, "GRN"),
    ("J6",  "Connector:Conn_01x02_Pin",       X_J6A, Y_J6,  180, "+5V/RTN"),
]

FOOTPRINT = {
    # --- primario 230 VAC ---
    "J3":  "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-03P_1x03_P5.00mm",
    "F1":  "Fuse:Fuseholder_Cylinder-5x20mm_Schurter_FPG4_Vertical_Closed",
    "RV1": "sam17:RV_Disc_D21mm_W5.5mm_P10.0mm",
    "NT1": "sam17:NTC_Disc_D11.5mm_W4.5mm_P7.5mm",
    "J4":  "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm",
    "J5":  "sam17:Faston_6.3x0.8mm_PCB_2Leg_P5.0mm",
    # J7: mismo footprint que J4 (barrier block 2 pos), spec §7.
    "J7":  "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm",
    # --- secundario ---
    "J1":  "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-03P_1x03_P5.00mm",
    "BR1": "Diode_THT:Diode_Bridge_DIP-4_W7.62mm_P5.08mm",
    # --- bulk: D16, NO D10 ---
    "C1":  "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    "C12": "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    "C13": "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    "C2":  "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    # --- pre-reguladores: TO-220-5, ambos con disipador propio (HS1/HS2). U2
    # tab=IN (hasta -20V) -> mica obligatoria (bom.csv, notes §1.2). ---
    "U1":  "Package_TO_SOT_THT:TO-220-5_Vertical",
    "U2":  "Package_TO_SOT_THT:TO-220-5_Vertical",
    "U3":  "Package_TO_SOT_THT:TO-220-3_Vertical",
    # --- divisores de setpoint ---
    "R5":  "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "R6":  "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "R7":  "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "R8":  "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "RV2": "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical",
    "RV3": "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical",
    # --- caps de entrada/salida de los pre-reg ---
    "C27": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "C28": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "C17": "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
    "C18": "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
    # --- proteccion ---
    "D12": "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
    "D13": "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
    "D8":  "Diode_SMD:D_SMA",
    "D9":  "Diode_SMD:D_SMA",
    # --- salidas del bus ---
    "J2":  "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
    "J6":  "Connector_Molex:Molex_KK-254_AE-6410-02A_1x02_P2.54mm_Vertical",
}
for _refs, _fp in [
    (("C3", "C9"),       "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"),
    (("C10",),            "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"),
    (("C11",),            "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"),
    (("D5",),              "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"),
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
    ("#G_R6", "power:GND", 226.06, 96.52,   0),
    ("#G_D8", "power:GND", 241.30, 77.47,   0),
    ("#G_U1ONOFF", "power:GND", 201.93, 63.50, 0),
    ("#G7",  "power:GND", 271.78,  95.25,   0),
    ("#G8",  "power:GND", 121.92, YG_N,   180),
    ("#G22", "power:GND", 134.62, YG_N,   180),
    ("#G9",  "power:GND", 147.32, YG_N,   180),
    ("#G_R8", "power:GND", 226.06, 137.16, 180),
    ("#G_D9", "power:GND", 241.30, 179.07, 180),
    ("#G_U2ONOFF", "power:GND", 201.93, 154.94, 180),
    # U2 (LM2991T) saca su masa por DEBAJO del cuerpo (offset +7.62 en hoja,
    # igual que U1 pero del lado -12V9 eso es AWAY del centro, no hacia
    # YG_N) -- necesita su propio simbolo aqui, no comparte fila con los
    # demas (mismo patron que v1 "#G10"). Sin esto, U2.GND queda sin driver:
    # "power_pin_not_driven" + "pin_not_connected" en ERC real (bug real de
    # esta tarea, se cayo al reorganizar el POWER list de v1 a v2).
    ("#G10",  "power:GND",     XU, YN + 12.7, 180),
    ("#G11", "power:GND", 213.36, YG_N,   180),
    ("#G13", "power:GND", 271.78, 138.43, 180),
    ("#G14", "power:GND", 302.26, 115.57, 270),
    ("#P1",  "power:+12V", 254.00,  53.34,  0),
    ("#N1",  "power:-12V", 254.00, 180.34, 180),
    ("#FLG1", "power:PWR_FLAG", 106.68,  53.34,   0),
    ("#FLG2", "power:PWR_FLAG", 106.68, 180.34, 180),
    ("#FLG3", "power:PWR_FLAG", 195.58, YG_P,     0),
    # El bus "+12V"/"-12V" heredado queda ISLA electrica en esta tarea (sin
    # wire hasta U1/U2 nuevos, ver docstring): #P1/#N1 son simbolos power
    # pero su tipo de pin real es power_IN (asi son TODOS los simbolos
    # power: en KiCad, incluido power:GND) -- sin un power_out real en la
    # red (que en v1 era el OUT del regulador, ahora desconectado a
    # proposito), ERC real marca "power_pin_not_driven" en #P1/#N1. Mismo
    # arreglo que ya usa v1 para VRAW+/VRAW- (#FLG1/#FLG2): un PWR_FLAG
    # explicito le dice al ERC "esta red se da por buena a proposito".
    ("#FLG5", "power:PWR_FLAG", 271.78,  53.34,   0),
    ("#FLG6", "power:PWR_FLAG", 271.78, 180.34, 180),
    ("#G15", "power:GND", 147.32, YG_5,   0),
    ("#G16", "power:GND",     XU, YG_5,   0),
    ("#G17", "power:GND", 213.36, YG_5,   0),
    ("#G18", "power:GND", 238.76, YG_5,   0),
    ("#G19", "power:GND", X5_LED, YD6 + 10.16, 0),
    ("#P2",  "power:+5V", 254.00, Y5 - 12.7, 0),
    ("#PE1",  "power:Earth_Protective", X_PE,  Y_PES, 0),
    ("#FLG4", "power:PWR_FLAG",         X_PEF, Y_PEF, 0),
    ("#G20",  "power:GND",              53.34, Y_CH,  0),
    ("#G21b", "power:GND",              269.24, Y_J6 - 2.54, 0),
]

POWER_VALUE = {"#PE1": "PE"}

# nombra los rieles crudos; sin esto el netlist los llama Net-(BR1-+)
LABELS = [
    ("VRAW+", 99.06, YP), ("VRAW-", 99.06, YN),
    ("L",    35.56,  Y_L), ("L_F",  63.50,  Y_L),
    ("L_TR", 106.68, Y_L), ("N",    60.96,  Y_NL),
    ("SEC_A", 60.96, 104.14), ("SEC_B", 60.96, 135.89),
    # nets nuevos v2 (nodos intermedios de los pre-reg): un solo label en el
    # riel real basta, TP7/TP8 se conectan por wire directo (no por nombre a
    # distancia como TP1/TP2).
    ("+13V1", 203.20, YP), ("-12V9", 203.20, YN),
]

TEXTS = [
    ("J5 = puente unico GND -> chasis. PE (J3.3) sube al MISMO esparrago.", 63.50, 39.37),
    ("No hay pista de PE en la PCB: la corriente de falla no pasa por la",  63.50, 41.91),
    ("placa. Apriete y ensayo de continuidad en design-notes.md sec. 13.",  63.50, 44.45),
    ("J6 = feed de +5V al modulo 2 (DAC + LCD, ~150 mA), issue #8 opcion C:", 300.99, 144.78),
    ("conector aparte del bus a proposito. Rutear el retorno (J6.2) DEDICADO", 300.99, 147.32),
    ("hasta el punto de estrella, separado del retorno analogico hasta el",    300.99, 149.86),
    ("ultimo cm (design-notes.md sec. 10.1) - el backlight va conmutado.",     300.99, 152.40),
    # notas de la etapa pre-reg (Task 5, plan v2 Step 3/4)
    ("U1: setpoint 13.1V. El trimmer RV2 compra margen de valle contra la",  195.58, 100.33),
    ("medida real de la mula (design-notes.md v2 §1.5, margen +0.02V).",     195.58, 102.87),
    ("U2: el divisor R7+RV3/R8 ES la carga minima de 500uA del LM2991 -",    195.58, 175.26),
    ("no subir esos valores (design-notes.md v2 §1.2/spec §3).",             195.58, 177.80),
    ("Bus +12V/-12V heredado de v1 (LED, J2, TP3/TP4, crowbar): sigue como", 271.78, 41.91),
    ("isla electrica propia hasta que Task 6 lo cuelgue del LT3045/LT3094.", 271.78, 44.45),
]


def side_fields(ref: str, x: float, y: float) -> list:
    """Campos a la derecha de un componente vertical (C, R, LED girado)."""
    return [(ref, "Reference", x + 7.62, y - 2.54), (ref, "Value", x + 7.62, y + 2.54)]


FIELDS: list = []
for _r, _x, _y in [("C27", 147.32, 69.85), ("C17", 213.36, 69.85),
                   ("R5", 226.06, 69.85), ("R6", 226.06, 90.17),
                   ("C28", 147.32, 163.83), ("C18", 213.36, 163.83),
                   ("R7", 226.06, 163.83), ("R8", 226.06, 143.51),
                   ("R1", 271.78, 69.85), ("D3", 271.78, 85.09),
                   ("R2", 271.78, 144.78), ("D4", 271.78, 160.02),
                   ("C9", 147.32, Y5_ROW), ("C10", 213.36, Y5_ROW), ("C11", 238.76, Y5_ROW),
                   ("R3", X5_LED, Y5_ROW), ("D6", X5_LED, YD6)]:
    FIELDS += side_fields(_r, _x, _y)
FIELDS += [
    ("C1",  "Reference", 114.30,  67.31), ("C1",  "Value",     114.30,  72.39),
    ("C12", "Reference", 134.62,  57.15), ("C12", "Value",     134.62,  60.96),
    ("C2",  "Reference", 114.30, 161.29), ("C2",  "Value",     114.30, 166.37),
    ("C13", "Reference", 134.62, 172.72), ("C13", "Value",     134.62, 176.53),
    ("J1",  "Value",     30.48, 107.95), ("J1",  "Reference",  30.48, 125.73),
    ("BR1", "Reference", 78.74, 128.27), ("BR1", "Value",      78.74, 132.08),
    ("J3",  "Value",     25.40, 11.43), ("J3",  "Reference",  25.40, 29.21),
    ("F1",  "Reference", 53.34, 10.16), ("F1",  "Value",      53.34, 13.97),
    ("NT1", "Reference", 99.06, 10.16), ("NT1", "Value",      99.06, 13.97),
    ("J4",  "Value",     X_J4,  11.43), ("J4",  "Reference",  X_J4,  29.21),
    ("J5",  "Reference",  25.40, 44.45), ("J5", "Value",       25.40, 48.26),
    ("J7",  "Value",     X_J7A + XPIN, Y_J7 - 2.54), ("J7", "Reference", X_J7A + XPIN, Y_J7 + 5.08),
    ("RV1", "Reference",  83.82, 22.86), ("RV1", "Value",      83.82, 26.67),
    ("U1",  "Value",       XU,   38.10), ("U1",  "Reference",    XU,   41.91),
    ("D12", "Reference",   XU,   32.77), ("D12", "Value",        XU,   29.21),
    ("U2",  "Reference", 180.34, 199.39), ("U2", "Value",     180.34, 203.20),
    ("D13", "Value",       XU,  205.74), ("D13", "Reference",    XU,  209.55),
    ("J2",  "Value",    320.04, 106.68), ("J2",  "Reference", 320.04, 127.00),
    ("#G14", "Value",   297.18, 113.03),
    ("D5",  "Reference",    XU,  92.71), ("D5",  "Value",        XU,  96.52),
    ("U3",  "Value",     190.50, 123.19), ("U3", "Reference",  190.50, 127.00),
    ("J6",  "Value",     X_J6A, 99.06), ("J6",  "Reference", X_J6A, 111.76),
    ("D8",  "Reference", 246.38, 66.04), ("D8",  "Value",     246.38, 69.85),
    ("D9",  "Reference", 246.38, 167.64), ("D9", "Value",     246.38, 171.45),
]

ROT = {p[0]: p[4] for p in PARTS} | {p[0]: p[4] for p in POWER}


def rail(y: float, xs: list[float], tag: str) -> list:
    """Riel horizontal partido en cada `xs`: todo corte es un punto de union."""
    return [(f"{tag}{i}", [[xs[i], y], [xs[i + 1], y]]) for i in range(len(xs) - 1)]


WIRES: list = [
    # --- entrada AC secundaria (J1, 12VAC del TR1 externo) ---
    ("AC1",      [[35.56, 114.30], [45.72, 114.30], [45.72, 104.14],
                  [83.82, 104.14], [83.82, YMID]]),
    ("AC2",      [[35.56, 119.38], [50.80, 119.38], [50.80, 135.89],
                  [99.06, 135.89], [99.06, YMID]]),
    ("CT->GND",  [[35.56, YMID], [43.18, YMID], [43.18, 124.46]]),
    ("BR+ sube", [[91.44, 109.22], [91.44, YP]]),
    ("BR- baja", [[91.44, 124.46], [91.44, YN]]),
    # --- entrada AC primaria, 230V ---
    ("AC L a",   [[25.40 + XPIN, Y_L], [49.53, Y_L]]),
    ("AC L b",   [[57.15, Y_L], [76.20, Y_L]]),
    ("AC L c",   [[76.20, Y_L], [95.25, Y_L]]),
    ("AC L d",   [[102.87, Y_L], [X_J4, Y_L]]),
    ("AC N a",   [[25.40 + XPIN, Y_N], [X_NJ, Y_N]]),
    ("AC N b",   [[X_NJ, Y_N], [X_NJ, Y_NL]]),
    ("AC N c",   [[X_NJ, Y_NL], [76.20, Y_NL]]),
    # Cortada en X_J7N (regla 2 del docstring: "aterrizar a media linea es
    # fragil" -- un cable que TERMINA sobre el CUERPO de otro cable, sin
    # cortarlo, no conecta en ERC real aunque las coordenadas coincidan
    # exacto; medido: "unconnected_wire_endpoint" en el primer intento de
    # esta tarea, ver task-5-report.md). J7 N ahora arranca en este mismo
    # vertice, union extremo-contra-extremo de 3 cables, no un tap a medio
    # cable.
    ("AC N d1",  [[76.20, Y_NL], [X_J7N, Y_NL]]),
    ("AC N d2",  [[X_J7N, Y_NL], [X_NJ2, Y_NL]]),
    ("AC N e",   [[X_NJ2, Y_NL], [X_NJ2, Y_N]]),
    ("AC N f",   [[X_NJ2, Y_N], [X_J4, Y_N]]),
    ("RV1 tap",  [[76.20, YRV + 3.81], [76.20, Y_NL]]),
    ("PE a",     [[25.40 + XPIN, Y_PE], [X_PE, Y_PE]]),
    ("PE b",     [[X_PE, Y_PE], [X_PE, Y_PEF]]),
    ("PE c",     [[X_PE, Y_PEF], [X_PE, Y_PES]]),
    ("PE flag",  [[X_PE, Y_PEF], [X_PEF, Y_PEF]]),
    ("J5 gnd",   [[25.40 + XPIN, Y_CH], [53.34, Y_CH]]),
    # --- J7: tap del nodo L (via su propia columna X_J7L, evita cruzar el
    # nodo RV1/carril-N en 76.20,30.48) y del carril N (via X_J7N, empalma
    # directo en el cuerpo del carril — union valida por regla 6 del
    # docstring) ---
    ("J7 L",     [[76.20, Y_L], [X_J7L, Y_L], [X_J7L, Y_J7], [X_J7A + XPIN, Y_J7]]),
    ("J7 N",     [[X_J7N, Y_NL], [X_J7N, Y_J7 + 2.54], [X_J7A + XPIN, Y_J7 + 2.54]]),
]
# cortes: bulk | C entrada | D12 tap | entrada del regulador (offset propio
# del simbolo LM2941CT/LM2991T: IN a ∓10.16 del ancla, NO ∓7.62 como el
# LM7812_TO220 de v1 -- verificado con get_schematic_pin_locations)
WIRES += rail(YP, [91.44, 106.68, 121.92, 134.62, 147.32, 160.02, 170.18], "VRAW_P ")
WIRES += rail(YN, [91.44, 106.68, 121.92, 134.62, 147.32, 160.02, 170.18], "VRAW_N ")
# riel +13V1 / -12V9: cortes en OUT | tap D12/D13 | tap TP7/TP8 | C17/C18 |
# tap divisor | tap TVS
WIRES += rail(YP, [190.50, 195.58, 203.20, 213.36, 226.06, 241.30], "+13V1 ")
WIRES += rail(YN, [190.50, 195.58, 203.20, 213.36, 226.06, 241.30], "-12V9 ")
# bus "+12V"/"-12V" heredado de v1 (isla electrica, ver docstring): rieles
# cortos propios, SIN wire hasta U1/U2 nuevos. Cortes en el tap de #P1/#N1
# (254.00, via "+12V sym"/"-12V sym" mas abajo) y en el tap del LED
# indicador -- R1.pin_arriba para el positivo (66.04, la LED va DESPUES
# hacia GND), D4.pin_lejano para el negativo (167.64, la LED va ANTES desde
# GND -- ver "R2 gnd"/"D4->riel" mas abajo, mismo patron que v1).
WIRES += rail(YP, [254.00, 271.78, 292.10], "+12V ISLA ")
WIRES += rail(YN, [254.00, 271.78, 288.29], "-12V ISLA ")
WIRES += [
    # --- retornos a GND del bulk / entrada de los pre-reg ---
    ("C1 gnd",   [[121.92, 73.66], [121.92, YG_P]]),
    ("C12 gnd",  [[134.62, 73.66], [134.62, YG_P]]),
    ("C27 gnd",  [[147.32, 73.66], [147.32, YG_P]]),
    ("U1 gnd",   [[XU, 73.66], [XU, YG_P]]),
    ("FLG3",     [[XU, YG_P], [195.58, YG_P]]),
    ("C17 gnd",  [[213.36, 73.66], [213.36, YG_P]]),
    ("C2 gnd",   [[121.92, 160.02], [121.92, YG_N]]),
    ("C13 gnd",  [[134.62, 160.02], [134.62, YG_N]]),
    ("C28 gnd",  [[147.32, 160.02], [147.32, YG_N]]),
    ("U2 gnd",   [[XU, YN + 7.62], [XU, YN + 12.7]]),
    ("C18 gnd",  [[213.36, 160.02], [213.36, YG_N]]),
    # --- D12/D13: out->in, misma posicion/rotacion que D1/D2 en v1 ---
    ("D12 izq",  [[160.02, YP], [160.02, 45.72], [176.53, 45.72]]),
    ("D12 der",  [[195.58, YP], [195.58, 45.72], [184.15, 45.72]]),
    ("D13 izq",  [[160.02, YN], [160.02, 187.96], [176.53, 187.96]]),
    ("D13 der",  [[195.58, YN], [195.58, 187.96], [184.15, 187.96]]),
    # --- TP7/TP8: stub directo (no la tecnica "a distancia" de TP1-6) ---
    ("TP7 net",  [[203.20, YP], [203.20, 88.90]]),
    ("TP8 net",  [[203.20, YN], [203.20, 144.78]]),
    # --- TVS: D8 catodo(pin1,norte)->+13V1 via rail(), anodo(pin2,sur)->GND.
    # D9 catodo(pin1,sur)->GND, anodo(pin2,norte)->-12V9 via rail() ---
    ("D8 gnd",   [[241.30, 73.66], [241.30, 77.47]]),
    ("D9 gnd",   [[241.30, 175.26], [241.30, 179.07]]),
    # --- divisor U1 (R5 alta+RV2 trimmer / R6 baja), huecos de 2.54mm
    # explicitos entre cada tramo en serie (regla 5 del docstring) ---
    ("R5->RV2 gap",     [[226.06, 73.66], [226.06, 76.20]]),
    ("RV2 wiper short", [[226.06, 76.20], [229.87, 76.20], [229.87, 80.01]]),
    ("RV2->R6 gap",     [[226.06, 83.82], [226.06, 86.36]]),
    ("R6->GND gap",     [[226.06, 93.98], [226.06, 96.52]]),
    # ADJ(U1) hasta el nodo medio del divisor (pin1/top de R6): jog por
    # y=53.34 (fuera de la fila de ADJ/ON-OFF, y=58.42) y x=232.41 (columna
    # libre) para no pasar por el pin de ON/OFF ni por ningun vertice del
    # propio divisor -- solo cruza el riel +13V1 sin compartir vertice con
    # el (cruce seguro, regla 6).
    ("ADJ U1",   [[176.53, 58.42], [176.53, 53.34], [232.41, 53.34],
                  [232.41, 86.36], [226.06, 86.36]]),
    # ON/OFF(U1) atado a GND local (siempre-encendido, notes §1.1): jog por
    # x=201.93 para no pisar el tap de D12 (x=195.58).
    ("ONOFF U1", [[184.15, 58.42], [201.93, 58.42], [201.93, 63.50]]),
    # --- divisor U2 (R7 alta+RV3 trimmer / R8 baja), mismo patron espejado ---
    ("R7->RV3 gap",     [[226.06, 160.02], [226.06, 157.48]]),
    ("RV3 wiper short", [[226.06, 157.48], [229.87, 157.48], [229.87, 153.67]]),
    ("RV3->R8 gap",     [[226.06, 149.86], [226.06, 147.32]]),
    ("R8->GND gap",     [[226.06, 139.70], [226.06, 137.16]]),
    # ADJ(U2): jog hacia y=133.35 (fuera de la fila de ON-OFF/ADJ, y=160.02,
    # y fuera del rango ocupado por el propio divisor 137.16-163.83) antes
    # de cruzar por x=232.41 hasta el nodo medio (pin2/bottom de R8).
    ("ADJ U2",   [[176.53, 160.02], [176.53, 133.35], [232.41, 133.35],
                  [232.41, 147.32], [226.06, 147.32]]),
    ("ONOFF U2", [[184.15, 160.02], [201.93, 160.02], [201.93, 154.94]]),
    # --- simbolos de riel y PWR_FLAG ---
    ("FLG1",     [[106.68, YP], [106.68, 53.34]]),
    ("FLG2",     [[106.68, YN], [106.68, 180.34]]),
    ("+12V sym", [[254.00, YP], [254.00, 53.34]]),
    ("-12V sym", [[254.00, YN], [254.00, 180.34]]),
    # --- indicadores LED (bus +12V/-12V heredado, isla — ver docstring) ---
    ("FLG5",     [[271.78, 66.04], [271.78, 53.34]]),
    ("R1->D3",   [[271.78, 73.66], [271.78, 81.28]]),
    ("D3 gnd",   [[271.78, 88.90], [271.78, 95.25]]),
    ("R2 gnd",   [[271.78, 140.97], [271.78, 138.43]]),
    ("R2->D4",   [[271.78, 148.59], [271.78, 156.21]]),
    ("D4->riel", [[271.78, 163.83], [271.78, YN]]),
    ("FLG6",     [[271.78, YN], [271.78, 180.34]]),
    # --- GND del conector de salida J2 (bus heredado) ---
    ("J2 gnd a", [[314.96, 114.30], [306.07, 114.30], [306.07, 115.57]]),
    ("J2 gnd b", [[306.07, 115.57], [306.07, 116.84], [314.96, 116.84]]),
    ("J2 gnd c", [[306.07, 115.57], [302.26, 115.57]]),
    ("+12V->J2", [[292.10, YP], [292.10, 111.76], [314.96, 111.76]]),
    ("-12V->J2", [[288.29, YN], [288.29, 119.38], [314.96, 119.38]]),
    # --- riel +5V: sin cambios v1 ---
    ("VRAW+ ->5V", [[106.68, YP], [106.68, Y5], [147.32, Y5]]),
    ("C9->VI",     [[147.32, Y5], [172.72, Y5]]),
    ("VO->C10",    [[187.96, Y5], [213.36, Y5]]),
    ("C10->C11",   [[213.36, Y5], [238.76, Y5]]),
    ("C11->tap",   [[238.76, Y5], [254.00, Y5]]),
    ("tap->J6",    [[254.00, Y5], [X_J6, Y5]]),
    ("J6->R3",     [[X_J6, Y5], [X5_LED, Y5]]),
    ("+5V sym",    [[254.00, Y5], [254.00, Y5 - 12.7]]),
    ("J6 +5V",     [[X_J6, Y_J6], [X_J6, Y5]]),
    ("J6 rtn",     [[X_J6, Y_J6 - 2.54], [269.24, Y_J6 - 2.54]]),
    ("R3->D6",     [[X5_LED, Y5_ROW + 3.81], [X5_LED, YD6 - 3.81]]),
    ("D6 gnd",     [[X5_LED, YD6 + 3.81], [X5_LED, YD6 + 10.16]]),
    ("C9 gnd",     [[147.32, Y5_ROW + 3.81], [147.32, YG_5]]),
    ("U3 gnd",     [[XU, Y5 + 7.62], [XU, YG_5]]),
    ("C10 gnd",    [[213.36, Y5_ROW + 3.81], [213.36, YG_5]]),
    ("C11 gnd",    [[238.76, Y5_ROW + 3.81], [238.76, YG_5]]),
    ("D5 izq",     [[172.72, Y5], [172.72, YD5], [176.53, YD5]]),
    ("D5 der",     [[187.96, Y5], [187.96, YD5], [184.15, YD5]]),
]


def check_footprints() -> None:
    """Valida el mapa de huellas. Va ANTES de tocar el fichero a proposito."""
    faltan = [p[0] for p in PARTS if p[0] not in FOOTPRINT]
    assert not faltan, f"componentes sin footprint: {faltan}"

    if not os.path.isdir(KICAD_FP):
        print(f"AVISO: no encuentro {KICAD_FP}, no compruebo las huellas")
        return
    rotos = []
    for ref in [p[0] for p in PARTS]:
        lib, _, name = FOOTPRINT[ref].partition(":")
        base = (f"{DIR}/../../kicad/sam17.pretty" if lib == "sam17"
                else os.path.join(KICAD_FP, f"{lib}.pretty"))
        if not os.path.isfile(os.path.join(base, f"{name}.kicad_mod")):
            rotos.append(f"{ref} -> {FOOTPRINT[ref]}")
    print(f"huellas inexistentes: {len(rotos)} {rotos}")
    assert not rotos, f"huellas que no estan en disco: {rotos}"


# --- puntos de prueba TP1-TP6 (heredados v1, sec.16.10, tecnica "a
# distancia" via label/simbolo power: propio de cada TP) -------------------
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
    if _tipo == "gnd":
        POWER.append((f"#G{_r}", "power:GND", _x, Y_TP + 7.62, 0))
        WIRES.append((f"{_r} net", [[_x, Y_TP], [_x, Y_TP + 7.62]]))
    elif _tipo == "sym":
        POWER.append((f"#P{_r}", f"power:{_net}", _x, Y_TP - 7.62, 0))
        WIRES.append((f"{_r} net", [[_x, Y_TP - 7.62], [_x, Y_TP]]))
    else:
        WIRES.append((f"{_r} net", [[_x, Y_TP], [_x, Y_TP - 7.62]]))
        LABELS.append((_net, _x, Y_TP - 7.62))

# --- TP7/TP8 (nuevos v2, stub directo — ver WIRES/LABELS mas arriba) ------
PARTS.append(("TP7", "Connector:TestPoint", 203.20, 88.90, 0, "+13V1"))
PARTS.append(("TP8", "Connector:TestPoint", 203.20, 144.78, 0, "-12V9"))
FOOTPRINT["TP7"] = "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm"
FOOTPRINT["TP8"] = "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm"
FIELDS.append(("TP7", "Reference", 209.55, 87.63))
FIELDS.append(("TP7", "Value",     209.55, 91.44))
FIELDS.append(("TP8", "Reference", 209.55, 143.51))
FIELDS.append(("TP8", "Value",     209.55, 147.32))


# --- crowbar del riel de +12 V (sec.16.8, isla electrica heredada) ---------
X_CB, Y_CB = 246.38, 207.01
X_Z,  X_C = X_CB - 15.24, X_CB - 27.94
Y_GATE = Y_CB + 2.54
PARTS += [
    ("Q1",  "Triac_Thyristor:BT169D", X_CB, Y_CB,          0, "BT169D"),
    ("D7",  "Device:D_Zener",         X_Z,  Y_CB - 3.81,  180, "BZX55C15"),
    ("R4",  "Device:R",               X_Z,  Y_GATE + 3.81,  0, "1k"),
    ("C14", "Device:C",               X_C,  Y_GATE + 3.81,  0, "100nF"),
]
FOOTPRINT.update({
    "Q1":  "Package_TO_SOT_THT:TO-92_Inline_Wide",
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


def setup_local_symbols(c: Client) -> None:
    """Crea (o actualiza) LM2941CT/LM2991T en una libreria local del proyecto
    y la registra en el sym-lib-table del proyecto (scope="project", junto al
    .kicad_pro) para que add_schematic_component pueda resolver "sam17:...".

    Pinera verificada contra el datasheet primario de TI (Pin Configuration
    and Functions, p.3 de ambos DS — ver el docstring del modulo):
        LM2941CT: 1=ADJ 2=ON/OFF 3=GND 4=IN 5=OUT
        LM2991T:  1=ADJ 2=ON/OFF 3=IN  4=GND 5=OUT
    Geometria IDENTICA en los dos simbolos (solo cambia el numero en cada
    posicion): IN a la izquierda (offset ∓10.16 del ancla, confirmado con
    get_schematic_pin_locations), OUT a la derecha (mismo offset), GND abajo
    (offset 0,+7.62 en hoja — mismo patron que usaban LM7812_TO220/
    LM2990SX-12 en v1), ADJ/ON-OFF arriba del cuerpo (offset ∓3.81 en X,
    -7.62 en Y — pines nuevos, sin equivalente v1).
    """
    common = dict(
        libraryPath=SYM,
        referencePrefix="U",
        overwrite=True,
        rectangles=[{"x1": -7.62, "y1": 5.08, "x2": 7.62, "y2": -5.08}],
    )

    def pins(gnd_num: str, in_num: str) -> list:
        return [
            {"name": "IN",  "number": in_num,  "type": "power_in",
             "at": {"x": -10.16, "y": 0, "angle": 0}},
            {"name": "OUT", "number": "5", "type": "power_out",
             "at": {"x": 10.16, "y": 0, "angle": 180}},
            {"name": "GND", "number": gnd_num, "type": "power_in",
             "at": {"x": 0, "y": -7.62, "angle": 90}},
            {"name": "ADJ", "number": "1", "type": "input",
             "at": {"x": -3.81, "y": 7.62, "angle": 270}},
            {"name": "ON/OFF", "number": "2", "type": "input",
             "at": {"x": 3.81, "y": 7.62, "angle": 270}},
        ]

    r = c.call("create_symbol", {
        **common, "name": "LM2941CT",
        "description": "LDO ajustable positivo, pre-reg +13.1V (TO-220-5)",
        "keywords": "LDO regulator adjustable positive LM2941",
        "datasheet": "https://www.ti.com/lit/ds/symlink/lm2941.pdf",
        "footprint": "Package_TO_SOT_THT:TO-220-5_Vertical",
        "pins": pins(gnd_num="3", in_num="4"),
    })
    print(f"  create_symbol LM2941CT: {str(r)[:120]}")

    r = c.call("create_symbol", {
        **common, "name": "LM2991T",
        "description": "LDO ajustable negativo, pre-reg -12.9V (TO-220-5)",
        "keywords": "LDO regulator adjustable negative LM2991",
        "datasheet": "https://www.ti.com/lit/ds/symlink/lm2991.pdf",
        "footprint": "Package_TO_SOT_THT:TO-220-5_Vertical",
        "pins": pins(gnd_num="4", in_num="3"),
    })
    print(f"  create_symbol LM2991T: {str(r)[:120]}")

    r = c.call("register_symbol_library", {
        "libraryPath": SYM, "libraryName": "sam17",
        "description": "Simbolos locales sam17 (LM2941CT/LM2991T pre-reg v2)",
        "scope": "project", "projectPath": PRO,
    })
    print(f"  register_symbol_library: {str(r)[:160]}")


def _wire_sexpr(x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        "\t(wire\n\t\t(pts\n"
        f"\t\t\t(xy {x1} {y1}) (xy {x2} {y2})\n"
        "\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n"
        f'\t\t(uuid "{uuid.uuid4()}")\n\t)\n'
    )


def _label_sexpr(name: str, x: float, y: float) -> str:
    return (
        f'\t(label "{name}"\n'
        f"\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n"
        "\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n"
        f'\t\t(uuid "{uuid.uuid4()}")\n\t)\n'
    )


def _text_sexpr(text: str, x: float, y: float) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return (
        f'\t(text "{escaped}"\n'
        "\t\t(exclude_from_sim no)\n"
        f"\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n"
        "\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n"
        f'\t\t(uuid "{uuid.uuid4()}")\n\t)\n'
    )


def inject_wires_labels_texts(sch_path: str, wires: list, labels: list, texts: list) -> None:
    """Escribe wires/labels/texts DIRECTO al .kicad_sch por texto, sin pasar
    por el MCP server.

    Por que: add_schematic_wire/add_schematic_net_label via MCP demostraron
    ser catastroficamente lentos en esta hoja (medido: >5 min y 100% CPU
    colgado en el PRIMER cable, en tres corridas distintas, incluso en un
    proceso aislado sin otros servidores MCP corriendo) -- el mismo patron
    de cable en un esquematico chico (2-95 componentes, sin la mezcla de
    ~20 simbolos DISTINTOS + 2 simbolos locales que tiene esta hoja) tarda
    <1s via el mismo tool, asi que no es un limite del formato del cable en
    si. El formato exacto (wire/label/text) esta verificado contra el
    sam17-power.kicad_sch v1 YA GENERADO por este mismo pipeline (build
    probado, en el repo) -- se copia tal cual, solo con coordenadas y uuid
    propios. create_schematic/add_schematic_component (que SI corrieron
    rapido, <1 min para 95 componentes + 2 simbolos locales) siguen yendo
    por el MCP; esto reemplaza SOLO wires/labels/texts.
    """
    segs = []
    for _label, wp in wires:
        pts = [(round(x, 2), round(y, 2)) for x, y in wp]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            segs.append(_wire_sexpr(x1, y1, x2, y2))
    for name, x, y in labels:
        segs.append(_label_sexpr(name, round(x, 2), round(y, 2)))
    for text, x, y in texts:
        segs.append(_text_sexpr(text, round(x, 2), round(y, 2)))
    block = "".join(segs)

    with open(sch_path, encoding="utf-8") as fh:
        txt = fh.read()
    # Se inserta el bloque justo antes de "(sheet_instances", conservando lo
    # que haya antes (espacios/tabs/CRLF): el indentado de nivel superior de
    # un .kicad_sch recien creado por create_schematic (2 espacios) no es el
    # mismo que el de uno re-guardado por la GUI (tabs, visto en v1).
    anchor = "(sheet_instances"
    idx = txt.find(anchor)
    assert idx != -1, "no encontre el punto de insercion (sheet_instances)"
    txt = txt[:idx] + block + txt[idx:]
    with open(sch_path, "w", encoding="utf-8") as fh:
        fh.write(txt)


def main() -> None:
    check_footprints()
    c = Client()
    try:
        setup_local_symbols(c)

        c.call("create_schematic", {"name": "sam17-power-v2", "path": DIR})
        with open(SCH, encoding="utf-8") as fh:
            txt = fh.read()
        title_block = (
            '(paper "A3")\n'
            "\t(title_block\n"
            '\t\t(title "Modulo 01 v2 — Alimentacion sub-uV, ±12 V / +5V")\n'
            f'\t\t(date "{DATE}")\n'
            f'\t\t(rev "{REV}")\n'
            '\t\t(company "SAM17 — Sintetizador analogico modular")\n'
            '\t\t(comment 1 "Variante Europa: primario 230VAC/50Hz. Pre-reg LM2941/LM2991 -> +13V1/-12V9")\n'
            '\t\t(comment 2 "Primario: fusible + MOV S20K275 + NTC soft-start + J7 (SMPS digital, spec S7)")\n'
            '\t\t(comment 3 "PE: J3.3 al esparrago de chasis; GND al mismo punto via J5 (S13)")\n'
            '\t\t(comment 4 "Bus +12V/-12V heredado v1: isla hasta Task 6 (LT3045/LT3094 sobre +13V1/-12V9)")\n'
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

        # wires/labels/texts van DIRECTO al fichero (ver docstring de
        # inject_wires_labels_texts): el mismo trio via MCP se colgo >5 min
        # clavado en el PRIMER cable, en tres corridas distintas.
        wires_shifted = [(label, [[wx, wy + YOFF] for wx, wy in wp]) for label, wp in WIRES]
        labels_shifted = [(name, x, y + YOFF) for name, x, y in LABELS]
        texts_shifted = [(text, x, y + YOFF) for text, x, y in TEXTS]
        inject_wires_labels_texts(SCH, wires_shifted, labels_shifted, texts_shifted)
        n_segs = sum(len(wp) - 1 for _l, wp in WIRES)
        print(f"cables: {len(WIRES)} definidos ({n_segs} segmentos) + "
              f"{len(LABELS)} labels + {len(TEXTS)} notas, escritos directo al fichero")

        r = str(c.call("batch_set_schematic_property_positions", {
            "schematicPath": SCH,
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
        r = str(c.call("export_netlist", {"schematicPath": SCH, "outputPath": NET}))
        print(f"netlist: {r[:120]}")
        for tool, ext in [("export_schematic_svg", "svg"), ("export_schematic_pdf", "pdf")]:
            out = f"{DIR}/../schematics/sam17-power-v2.{ext}"
            c.call(tool, {"schematicPath": SCH, "outputPath": out})
        print("exportado a ../schematics/sam17-power-v2.{svg,pdf}")
    finally:
        c.close()


if __name__ == "__main__":
    main()
