"""Genera sam17-power-v3.kicad_sch a partir de las notas de diseno del modulo.

Fuente: ../../notes/design-notes.md (topologia, valores, presupuesto de
corriente) + ../../v2/kicad/build_schematic.py, del que este script hereda por
cirugia. Trazado con cables reales sobre coordenadas de pin, no con etiquetas
de red — ver convenciones abajo.

QUE ES LA v3 (plan docs/superpowers/plans/2026-08-18-fuente-v3-goat.md):
  La v1 y la v2 son diseños de papel. La v1 se abandono el 2026-08-17 sin
  fabricar; la v2 llego a tener gerbers, BOM y CPL generados y tampoco se
  pidio. La v3 es la TERCERA y la PRIMERA que se construye. Por eso su
  constraint: lo que no quede decidido sale con huella y DNP, nunca con una v4.

  La v2 NO SE TOCA. Se lee y se copia, igual que se hizo con la v1 al nacer
  esta. Un diseño congelado que se sigue editando deja de ser un registro de
  lo que se decidio y pasa a ser un borrador con fecha equivocada.

CIRUGIA DE HERENCIA v2 -> v3 (Tasks 4 y 5 del plan v3):
  - MUEREN: el crowbar entero (D7 zener, Q1 SCR, R4 pull-down de gate, C14
    filtro de dv/dt). No se sustituye por nada — issue #118: la cascada de dos
    etapas ya protege sola (ningun fallo simple pone mas de +-13,1 V en el bus)
    y el lazo del crowbar no cerraba con ningun SCR, porque el fusible de 1,6 A no esta
    obligado a abrir a los 2,79 A que refleja el fallo.
  - SOBREVIVE todo lo demas del circuito, sin un cable movido: entrada 230 V,
    rectificacion, bulk, los dos pre-reguladores, las dos parejas
    LT3045/LT3094, el 7805, los LED de riel, J2, J6, J7, TP1-TP8.
  - NUEVO: la isla de telemetria — U8/U9 (INA226), U10 (ADS1115), U11
    (TMP1075), U12 (ISO1541), sus shunts R19/R20, los tres divisores
    R21-R26, los pull-ups R27/R28 (+R29/R30 DNP), el desacoplo C29-C35, los
    clamps D14/D15, el conector aislado J8 y los taps TP9-TP11. El contrato
    esta en ../bom.csv y la aritmetica en ../check_telemetria.py.
  - Lo que cambia FUERA de esta hoja: los tres TO-220 pasan de disipador
    individual a tab contra la pared del chasis (Fase C/D). Aqui no se nota:
    es colocacion, no conectividad.

Uso (requiere hardware/tools/kicad_mcp_client.py y un KiCAD-MCP-Server
corriendo/instalado, ver hardware/tools/README.md):

    python build_schematic.py

Es destructivo por diseno: create_schematic sobreescribe el .kicad_sch. Volver
a correrlo reconstruye la hoja desde cero a partir de este archivo, que es la
fuente de verdad real.

HERENCIA v1 -> v2, conservada como registro:
  - MUEREN: U1(v1)=LM2940CT-12 y sus pasivos directos (C3,C5,C7,D1); U2(v1)=
  LM2990T-12 y sus pasivos directos (C4,C6,C8,D2). Los designadores U1/U2
  se REUTILIZAN para los pre-reguladores nuevos (misma posicion en la
  cascada, ahora alimentan a la pareja LT3045/LT3094 de la Task 6 en vez
  de ser el regulador final).
  - SOBREVIVEN intactos: entrada 230V (J1/RV1/NT1/J4+J5 faston),
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
    cuelga DESPUES de RV1 y ANTES de NT1/J4 (lado 230V de la barrera,
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
import subprocess
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
SCH = f"{DIR}/sam17-power-v3.kicad_sch"
PRO = f"{DIR}/sam17-power-v3.kicad_pro"
SYM = f"{DIR}/sam17.kicad_sym"          # libreria local: LM2941CT/LM2991T
NET = f"{DIR}/sam17-power-v3.net"
# Para comprobar que los footprints existen de verdad. Si la ruta no esta, la
# comprobacion se salta con un aviso en vez de romper el build en otra maquina.
KICAD_FP = os.environ.get("KICAD_FOOTPRINTS",
                          r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

ISLA_DX = 203.20   # Task 6: desplaza la isla +12V/-12V (LED/J2) para hacer
                   # sitio a U4-U7 + red SET/ILIM/ballast entre el pre-reg y
                   # ella. Nada mas cambia de sitio.
X_P12 = X_N12 = 317.50   # columna del nodo de salida real (OUTS+ballast) de
                         # la etapa ultra -- arranque de la isla +12V/-12V.

YP, YN = 66.04, 167.64          # rieles positivo / negativo
YMID = 116.84                   # eje del puente y del conector de entrada
YG_P, YG_N = 86.36, 147.32      # fila de simbolos GND (arriba / abajo)
XU = 180.34                     # columna de los reguladores
YOFF = 25.4                     # baja todo el dibujo para centrarlo en A3
XPIN = 5.08                     # offset en x del pin de un Conn_01x0N_Pin sin girar
DATE, REV = "2026-08-19", "v3-A"

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
# IRM-15-5, DESPUES de RV1 y ANTES de NT1/J4 (spec §7 — comparte el
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
    # --- lado primario, 230 VAC (design-notes.md §10.2/§10.3). El fusible NO
    # esta en esta placa: va en el IEC C14 de la pared (#130). TR1 tampoco --
    # es externo, sale por J4 y vuelve por J1. ---
    ("J3",  "Connector:Conn_01x03_Pin",       25.40, Y_M,     0, "AC 230V IN"),
    # EL FUSIBLE YA NO ESTA EN LA PLACA. La spec del case §7 pone un IEC C14
    # **con portafusible** en la pared del recinto, y `F1` estaba aqui: dos
    # fusibles en serie en el mismo primario, que es peor que uno solo --
    # el mismo fallo los ve a los dos y no hay forma de saber cual miro.
    #
    # Se queda el del IEC porque es el ACCESIBLE: cambiarlo no obliga a abrir
    # un recinto de acero cerrado, que es como se hace en equipo de audio de
    # red. El valor y su justificacion no se van con la pieza -- 1.6 A lento,
    # por el inrush del toroide de 120 VA mas los 0.2 A de la SMPS IRM-15-5:
    # siguen aplicando, solo que a un fusible que vive en el chasis (#130).
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
    # GIRADO 180 para que su pin 1 sea el de GNDREF, igual que en R8.
    # Los dos son el mismo divisor a cada lado de la placa y estan
    # dibujados espejados -- R6 lleva GNDREF abajo y R8 arriba -- asi que
    # el pin que toca la referencia era el 2 en uno y el 1 en el otro. En
    # la PLACA eso mandaba el pad de GNDREF de R6 a x=57.16, fuera de
    # ISLA_REF (que acaba en 54), donde ni la zona lo alcanzaba ni una
    # pista puede ir sin sacar la referencia de su isla: R6.2 no ha estado
    # conectado en ninguna version. Con el simbolo girado el cableado del
    # esquematico no se mueve ni un milimetro y la huella tampoco -- un
    # resistor es simetrico -- pero el pad de GNDREF pasa a ser el 1, que
    # esta en x=47 y dentro de la isla, como el de R8.
    ("R6",  "Device:R",                      226.06, 90.17, 180, "1k"),
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
    # --- bus "+12V"/"-12V" heredado de v1 — LED indicador. Task 6 lo
    # reconecta a la salida real de U4-U7 (ver rail() de +12V/-12V ISLA mas
    # abajo); se corre ISLA_DX a la derecha para hacer sitio a la etapa
    # ultra entre el pre-reg y aqui. ---
    ("R1",  "Device:R",                      271.78 + ISLA_DX, 69.85,   0, "2k2"),
    ("D3",  "Device:LED",                    271.78 + ISLA_DX, 85.09,  90, "RED"),
    ("R2",  "Device:R",                      271.78 + ISLA_DX, 144.78,  0, "2k2"),
    ("D4",  "Device:LED",                    271.78 + ISLA_DX, 160.02, 90, "YEL"),
    ("J2",  "Connector:Conn_01x04_Pin",      320.04 + ISLA_DX, 116.84, 180, "BUS -12/G/G/+12"),
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
    "RV1": "sam17:RV_Disc_D21mm_W5.5mm_P10.0mm",
    "NT1": "sam17:NTC_Disc_D10.0mm_W4.0mm_P5.1mm",
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
    # #G_R6: BORRADO (Task 6 Step 4) -- el fondo del divisor de U1 (R6) se
    # mueve de GND a GNDREF, ver LABELS mas abajo (spec §6.3).
    ("#G_D8", "power:GND", 241.30, 77.47,   0),
    ("#G_U1ONOFF", "power:GND", 201.93, 63.50, 0),
    ("#G7",  "power:GND", 271.78 + ISLA_DX,  95.25,   0),
    ("#G8",  "power:GND", 121.92, YG_N,   180),
    ("#G22", "power:GND", 134.62, YG_N,   180),
    ("#G9",  "power:GND", 147.32, YG_N,   180),
    # #G_R8: BORRADO (Task 6 Step 4) -- el fondo del divisor de U2 (R8) se
    # mueve de GND a GNDREF, ver LABELS mas abajo.
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
    ("#G13", "power:GND", 271.78 + ISLA_DX, 138.43, 180),
    ("#G14", "power:GND", 302.26 + ISLA_DX, 115.57, 270),
    ("#P1",  "power:+12V", 254.00 + ISLA_DX,  53.34,  0),
    ("#N1",  "power:-12V", 254.00 + ISLA_DX, 180.34, 180),
    ("#FLG1", "power:PWR_FLAG", 106.68,  53.34,   0),
    ("#FLG2", "power:PWR_FLAG", 106.68, 180.34, 180),
    ("#FLG3", "power:PWR_FLAG", 195.58, YG_P,     0),
    # Task 6: el bus "+12V"/"-12V" heredado deja de ser isla -- ahora cuelga
    # de verdad de U4-U7 via ballast (ver rail() "+12V/-12V ISLA" en WIRES,
    # que arranca en el nodo de salida real de la etapa ultra). #P1/#N1
    # (power:+12V/-12V, tipo power_in como TODO simbolo power: de KiCad) y
    # sus PWR_FLAG (#FLG5/#FLG6) se DEJAN tal cual -- TP3/TP4 (mas abajo,
    # TESTPOINTS) tambien ponen su propio simbolo power:+12V/-12V en esta
    # misma red por nombre, y siguen necesitando el PWR_FLAG igual que antes
    # (ERC no razona "ya hay una resistencia de ballast aguas arriba", solo
    # mira tipos de pin) -- quitar el flag rompe TP3/TP4, no hace falta.
    ("#FLG5", "power:PWR_FLAG", 271.78 + ISLA_DX,  53.34,   0),
    ("#FLG6", "power:PWR_FLAG", 271.78 + ISLA_DX, 180.34, 180),
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
    ("L",    35.56,  Y_L),
    ("L_TR", 106.68, Y_L), ("N",    60.96,  Y_NL),
    ("SEC_A", 60.96, 104.14), ("SEC_B", 60.96, 135.89),
    # nets nuevos v2 (nodos intermedios de los pre-reg): un solo label en el
    # riel real basta, TP7/TP8 se conectan por wire directo (no por nombre a
    # distancia como TP1/TP2).
    ("+13V1", 203.20, YP), ("-12V9", 203.20, YN),
    # GNDREF (Task 6, spec §6.3): masa de referencia analogica -- SET/ILIM de
    # U4-U7 y el fondo de los divisores de U1/U2. Union con GND SOLO por
    # JP1 (net tie). Varios LABELS "GNDREF" en puntos distintos de la hoja
    # SIN wire fisico entre ellos: KiCad los funde en una sola red por
    # nombre (mismo mecanismo que ya usan +13V1/VRAW+ "a distancia"), asi
    # que no hace falta trazar un unico riel continuo por toda la hoja.
    ("GNDREF", 226.06, 96.52),   # fondo de R6 (divisor U1) -- Step 4
    ("GNDREF", 226.06, 137.16),  # fondo de R8 (divisor U2) -- Step 4
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
    ("U1: setpoint 13.1V solo tiene +0.02V de margen: BAJAR RV2 a ~12.9V",   195.58, 100.33),
    ("en bring-up. Valle minimo 13.46V (design-notes.md v2 §4.1).",          195.58, 102.87),
    ("U2: el divisor R7+RV3/R8 ES la carga minima de 500uA del LM2991 -",    195.58, 175.26),
    ("no subir esos valores (design-notes.md v2 §1.2/spec §3).",             195.58, 177.80),
    ("Bus +12V/-12V heredado de v1 (LED, J2, TP3/TP4, crowbar): reconectado", 271.78 + ISLA_DX, 41.91),
    ("en Task 6 al ballast real de U4/U5 (+12V) y U6/U7 (-12V). Ya no es isla.", 271.78 + ISLA_DX, 44.45),
]

# Cruces de no-conexion (Task 6: PG/PGFB/VIOC de U4-U7, flotantes a proposito
# segun DS -- ver bloque "etapa ultra" mas abajo, que las llena).
NO_CONNECTS: list = []


def side_fields(ref: str, x: float, y: float) -> list:
    """Campos a la derecha de un componente vertical (C, R, LED girado)."""
    return [(ref, "Reference", x + 7.62, y - 2.54), (ref, "Value", x + 7.62, y + 2.54)]


FIELDS: list = []
for _r, _x, _y in [("C27", 147.32, 69.85), ("C17", 213.36, 69.85),
                   ("R5", 226.06, 69.85), ("R6", 226.06, 90.17),
                   ("C28", 147.32, 163.83), ("C18", 213.36, 163.83),
                   ("R7", 226.06, 163.83), ("R8", 226.06, 143.51),
                   ("R1", 271.78 + ISLA_DX, 69.85), ("D3", 271.78 + ISLA_DX, 85.09),
                   ("R2", 271.78 + ISLA_DX, 144.78), ("D4", 271.78 + ISLA_DX, 160.02),
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
    ("NT1", "Reference", 99.06, 10.16), ("NT1", "Value",      99.06, 13.97),
    ("J4",  "Value",     X_J4,  11.43), ("J4",  "Reference",  X_J4,  29.21),
    ("J5",  "Reference",  25.40, 44.45), ("J5", "Value",       25.40, 48.26),
    ("J7",  "Value",     X_J7A + XPIN, Y_J7 - 2.54), ("J7", "Reference", X_J7A + XPIN, Y_J7 + 5.08),
    ("RV1", "Reference",  83.82, 22.86), ("RV1", "Value",      83.82, 26.67),
    ("U1",  "Value",       XU,   38.10), ("U1",  "Reference",    XU,   41.91),
    ("D12", "Reference",   XU,   32.77), ("D12", "Value",        XU,   29.21),
    ("U2",  "Reference", 180.34, 199.39), ("U2", "Value",     180.34, 203.20),
    ("D13", "Value",       XU,  205.74), ("D13", "Reference",    XU,  209.55),
    ("J2",  "Value",    320.04 + ISLA_DX, 106.68), ("J2",  "Reference", 320.04 + ISLA_DX, 127.00),
    ("#G14", "Value",   297.18 + ISLA_DX, 113.03),
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


def vrail(x: float, ys: list[float], tag: str) -> list:
    """Riel VERTICAL partido en cada `ys` -- mismo criterio que rail() pero en
    Y (Task 6: troncales de IN/SET/ballast de U4-U7, todas verticales)."""
    return [(f"{tag}{i}", [[x, ys[i]], [x, ys[i + 1]]]) for i in range(len(ys) - 1)]


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
    # De J3 al nodo de RV1 de una pieza: aqui iban los dos pines de F1 y el
    # hueco de 7.62 mm que dejaban entre ellos.
    ("AC L a",   [[25.40 + XPIN, Y_L], [76.20, Y_L]]),
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
    ("AC N d",   [[76.20, Y_NL], [X_NJ2, Y_NL]]),
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
    # v3: J7 ya no cuelga del riel directamente. Entre el riel y la SMPS va el
    # filtro de modo comun (L1 + CY1/CY2, mas abajo), y J7 cuelga de su salida
    # por nombre -- L_SMPS / N_SMPS.
    ("J7 L",     [[X_J7A + XPIN, Y_J7], [X_J7A + XPIN + 7.62, Y_J7]]),
    ("J7 N",     [[X_J7A + XPIN, Y_J7 + 2.54], [X_J7A + XPIN + 7.62, Y_J7 + 2.54]]),
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
# bus "+12V"/"-12V" heredado de v1 (Task 6: YA NO es isla). Arranca en el
# nodo real de salida de la etapa ultra (X_P12=317.50/X_N12=317.50, cortes
# de la red vertical de ballast+OUTS mas abajo -- ahi es donde entra la
# corriente real), sigue hasta el tap de #P1/#N1 (shiftado) y el LED
# indicador -- R1.pin_arriba para el positivo (66.04, la LED va DESPUES
# hacia GND), D4.pin_lejano para el negativo (167.64, la LED va ANTES desde
# GND -- ver "R2 gnd"/"D4->riel" mas abajo, mismo patron que v1).
# --- shunts de la telemetria (v3): en serie con lo que SALE de la placa ----
X_SH12 = 506.73                  # R19, dentro del cable "+12V->J2"
PARTS += [
    ("R19", "Device:R", X_SH12, 111.76, 90, "20mOhm"),
    ("R20", "Device:R", X_J6, (Y_J6 + Y5) / 2, 0, "100mOhm"),
]
FOOTPRINT.update({"R19": "Resistor_SMD:R_1206_3216Metric",
                  "R20": "Resistor_SMD:R_1206_3216Metric"})
FIELDS += [("R19", "Reference", X_SH12, 106.68), ("R19", "Value", X_SH12, 116.84),
           ("R20", "Reference", X_J6 + 8.89, 110.49),
           ("R20", "Value", X_J6 + 8.89, 114.30)]
LABELS += [("+12V_BUS", X_SH12 + 3.81, 111.76), ("+5V_M2", X_J6, Y_J6 + 1.27)]

WIRES += rail(YP, [X_P12, 254.00 + ISLA_DX, 271.78 + ISLA_DX, 292.10 + ISLA_DX], "+12V ISLA ")
WIRES += rail(YN, [X_N12, 254.00 + ISLA_DX, 271.78 + ISLA_DX, 288.29 + ISLA_DX], "-12V ISLA ")
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
    # Task 6 Step 4: el fondo de R6 va a GNDREF (LABEL, no power:GND -- ver
    # LABELS), no a GND. Mismo punto que antes, cambia solo el nombre de red.
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
    # Task 6 Step 4: idem R6, el fondo de R8 va a GNDREF (LABEL).
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
    ("+12V sym", [[254.00 + ISLA_DX, YP], [254.00 + ISLA_DX, 53.34]]),
    ("-12V sym", [[254.00 + ISLA_DX, YN], [254.00 + ISLA_DX, 180.34]]),
    # --- indicadores LED (bus +12V/-12V heredado -- Task 6 ya no es isla) ---
    ("FLG5",     [[271.78 + ISLA_DX, 66.04], [271.78 + ISLA_DX, 53.34]]),
    ("R1->D3",   [[271.78 + ISLA_DX, 73.66], [271.78 + ISLA_DX, 81.28]]),
    ("D3 gnd",   [[271.78 + ISLA_DX, 88.90], [271.78 + ISLA_DX, 95.25]]),
    ("R2 gnd",   [[271.78 + ISLA_DX, 140.97], [271.78 + ISLA_DX, 138.43]]),
    ("R2->D4",   [[271.78 + ISLA_DX, 148.59], [271.78 + ISLA_DX, 156.21]]),
    ("D4->riel", [[271.78 + ISLA_DX, 163.83], [271.78 + ISLA_DX, YN]]),
    ("FLG6",     [[271.78 + ISLA_DX, YN], [271.78 + ISLA_DX, 180.34]]),
    # --- GND del conector de salida J2 (bus heredado) ---
    ("J2 gnd a", [[314.96 + ISLA_DX, 114.30], [306.07 + ISLA_DX, 114.30], [306.07 + ISLA_DX, 115.57]]),
    ("J2 gnd b", [[306.07 + ISLA_DX, 115.57], [306.07 + ISLA_DX, 116.84], [314.96 + ISLA_DX, 116.84]]),
    ("J2 gnd c", [[306.07 + ISLA_DX, 115.57], [302.26 + ISLA_DX, 115.57]]),
    # R19 parte este cable: el tramo de la derecha ya no es "+12V" sino
    # "+12V_BUS", que es lo que ven los modulos. U8 mide la diferencia.
    ("+12V->R19", [[292.10 + ISLA_DX, YP], [292.10 + ISLA_DX, 111.76], [X_SH12 - 3.81, 111.76]]),
    ("R19->J2",   [[X_SH12 + 3.81, 111.76], [314.96 + ISLA_DX, 111.76]]),
    ("-12V->J2", [[288.29 + ISLA_DX, YN], [288.29 + ISLA_DX, 119.38], [314.96 + ISLA_DX, 119.38]]),
    # --- riel +5V: sin cambios v1 ---
    ("VRAW+ ->5V", [[106.68, YP], [106.68, Y5], [147.32, Y5]]),
    ("C9->VI",     [[147.32, Y5], [172.72, Y5]]),
    ("VO->C10",    [[187.96, Y5], [213.36, Y5]]),
    ("C10->C11",   [[213.36, Y5], [238.76, Y5]]),
    ("C11->tap",   [[238.76, Y5], [254.00, Y5]]),
    ("tap->J6",    [[254.00, Y5], [X_J6, Y5]]),
    ("J6->R3",     [[X_J6, Y5], [X5_LED, Y5]]),
    ("+5V sym",    [[254.00, Y5], [254.00, Y5 - 12.7]]),
    # R20 parte este cable. Va SOLO en la rama de J6 (lo que sale hacia el
    # modulo 2), no en el riel: asi la isla y el LED quedan aguas arriba y el
    # +5 V que U9 usa de referencia es el mismo nodo al que se atan los
    # divisores. Si la isla colgara detras de su propio shunt, la referencia
    # dependeria de la caida del shunt -- una autorreferencia silenciosa.
    ("J6 +5V a",   [[X_J6, Y_J6], [X_J6, Y_J6 + 1.27]]),
    ("J6 +5V b",   [[X_J6, Y5 - 1.27], [X_J6, Y5]]),
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



# --- filtro de modo comun de la derivacion de la SMPS (v3, design-notes 18.7)
#
# Por que existe: la IRM-15 inyecta modo comun en la red compartida, la
# capacidad entre devanados del toroide lo cruza al secundario, y el PSRR no lo
# rechaza porque no llega como variacion de alimentacion sino como corriente por
# la masa. Y su certificado EN 55032 clase B no cubre el fundamental: conmuta a
# 65 kHz y la emision conducida de esa norma empieza a medir en 150 kHz.
#
# POR QUE EL CHOKE SE PUEBLA Y LAS Y NO. Es la diferencia entre un elemento SERIE
# y uno PARALELO, y no es un detalle de estilo:
#
#   * L1 esta EN SERIE con la alimentacion de la SMPS. Un componente serie no
#     puede ir DNP: sin poblar, la SMPS se queda sin red. O va puesto, o hay que
#     puentearlo, y un puente de 230 V a 0.2 A no es un net-tie.
#   * CY1/CY2 estan EN PARALELO. Sin poblar no rompen nada. Por eso SI pueden ser
#     huella, y por eso son ellas las que esperan.
#
# Y esperan por un numero que este repo no puede acotar: la fuga a tierra que
# anaden. 2 x 1 nF son 145 uA a 230 V/50 Hz, y el limite aplicable esta en la
# clausula de IEC 62368-1 que design-notes 13.4 ya declino citar por ser de pago.
# Se puebla con la medida del bring-up delante, no antes.
#
# La aritmetica de por que hacen falta las dos cosas, a 65 kHz:
#   choke de 10 mH .................... 4.1 kohm
#   C entre devanados del toroide ..... ~12 kohm (200 pF SUPUESTOS: nadie la publica)
#   solo el choke ..... sigue pasando el 75 % de la corriente al toroide
#   choke + 2 x 1 nF .. pasa el 7 %
# El choke solo es teatro. La pantalla del toroide sigue siendo la solucion en
# el sitio correcto: quita el camino en vez de repartir la corriente.
X_FILT, Y_FILT = 45.72, 66.04
PARTS += [
    ("L1",  "Device:L_Coupled", X_FILT, Y_FILT, 0, "10mH CM"),
    ("CY1", "Device:C", 40.64, 81.28, 0, "1nF Y2"),
    ("CY2", "Device:C", 55.88, 81.28, 0, "1nF Y2"),
]
FOOTPRINT.update({
    "L1":  "Inductor_THT:L_CommonMode_Toroid_Vertical_L30.5mm_W15.2mm_"
           "Px10.16mm_Py20.32mm_Bourns_8100",
    "CY1": "Capacitor_THT:C_Disc_D10.5mm_W5.0mm_P7.50mm",
    "CY2": "Capacitor_THT:C_Disc_D10.5mm_W5.0mm_P7.50mm",
})
WIRES += [
    ("L1 L in",  [[X_FILT - 5.08, Y_FILT - 2.54], [33.02, Y_FILT - 2.54]]),
    ("L1 N in",  [[X_FILT - 5.08, Y_FILT + 2.54], [33.02, Y_FILT + 2.54]]),
    ("L1 L out", [[X_FILT + 5.08, Y_FILT - 2.54], [58.42, Y_FILT - 2.54]]),
    ("L1 N out", [[X_FILT + 5.08, Y_FILT + 2.54], [58.42, Y_FILT + 2.54]]),
    ("CY1 top",  [[40.64, 77.47], [40.64, 74.93]]),
    ("CY1 pe",   [[40.64, 85.09], [40.64, 88.90]]),
    ("CY2 top",  [[55.88, 77.47], [55.88, 74.93]]),
    ("CY2 pe",   [[55.88, 85.09], [55.88, 88.90]]),
]
LABELS += [
    ("L",       33.02, Y_FILT - 2.54),
    ("N",       33.02, Y_FILT + 2.54),
    ("L_SMPS",  58.42, Y_FILT - 2.54),
    ("N_SMPS",  58.42, Y_FILT + 2.54),
    ("L_SMPS",  40.64, 74.93),
    ("N_SMPS",  55.88, 74.93),
    ("L_SMPS",  X_J7A + XPIN + 7.62, Y_J7),
    ("N_SMPS",  X_J7A + XPIN + 7.62, Y_J7 + 2.54),
]
POWER += [
    ("#PE2", "power:Earth_Protective", 40.64, 88.90, 180),
    ("#PE3", "power:Earth_Protective", 55.88, 88.90, 180),
]
POWER_VALUE.update({"#PE2": "PE", "#PE3": "PE"})
FIELDS += [
    ("L1",  "Reference", X_FILT, Y_FILT - 8.89), ("L1",  "Value", X_FILT, Y_FILT + 8.89),
    ("CY1", "Reference", 33.02, 80.01), ("CY1", "Value", 33.02, 83.82),
    ("CY2", "Reference", 63.50, 80.01), ("CY2", "Value", 63.50, 83.82),
]
TEXTS += [
    ("Filtro de modo comun de la SMPS (design-notes 18.7). L1 va POBLADO: en serie,", 25.40, 57.15),
    ("sin el la SMPS se queda sin red. CY1/CY2 van SIN POBLAR: en paralelo, y su valor", 25.40, 59.69),
    ("depende de un presupuesto de fuga a tierra que hoy no esta acotado.", 25.40, 62.23),
]

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


# ============================================================================
# Task 6 -- etapa ultra: LT3045 x2 (U4/U5, riel +12.000V) + LT3094 x2 (U6/U7,
# riel -12.000V) en paralelo, con red SET compartida por riel, ILIM por chip
# (Kelvin al GND propio de cada chip, design-notes.md v2 §1.3/§1.4), ballast
# de 20 mOhm por chip, OUTS al nodo real de salida, y la isla de masa de
# referencia GNDREF (SET + fondo de los divisores de U1/U2) unida a GND por
# el UNICO puente JP1.
#
# Simbolos: Regulator_Linear:LT3045xDD / LT3094xDD, de la libreria ESTANDAR
# de KiCad (Regulator_Linear.kicad_sym) -- NO simbolos locales. Pinera
# verificada leyendo el .kicad_sym instalado (no de memoria) contra las
# tablas de §1.3/§1.4: coincide pin a pin en los dos chips, incluidos el
# EP (pin 11 del LT3045, apilado en la MISMA coordenada que el pin 8/GND --
# conecta solo, sin wire aparte, por ser el mismo simbolo) y el EP del
# LT3094 (pin 13, apilado con el pin 1/IN -- misma logica). La asimetria
# real EP(LT3045)=GND / EP(LT3094)=IN que pide el brief queda resuelta por
# la GEOMETRIA del propio simbolo estandar, no hace falta forzarla a mano.
#
# Geometria de pines (offset en HOJA respecto al ancla, sin rotar -- OJO: el
# eje Y del simbolo en la libreria crece hacia ARRIBA, pero en la hoja crece
# hacia ABAJO, asi que el offset en hoja es (dx_local, -dy_local); verificado
# contra el patron ya usado en LM2941CT/LM2991T, docstring de
# setup_local_symbols, "GND abajo" = dy_local negativo -> offset hoja
# positivo):
#   LT3045xDD (U4/U5): IN(dx-10.16,dy-2.54) EN/UV(dx-10.16,dy+0)
#     ILIM(dx-10.16,dy+2.54) SET(dx-10.16,dy+5.08) GND/EP(dx0,dy+10.16)
#     OUTS(dx+10.16,dy+0) OUT(dx+10.16,dy-2.54) PG(dx+10.16,dy+5.08)
#     PGFB(dx+10.16,dy+2.54)
#   LT3094xDD (U6/U7): IN/EP(dx-10.16,dy-5.08) EN/UV(dx-10.16,dy-2.54)
#     PG(dx-10.16,dy+0) PGFB(dx+10.16,dy+0) ILIM(dx+10.16,dy+2.54)
#     VIOC(dx-10.16,dy+2.54) SET(dx-10.16,dy+5.08) GND(dx0,dy+10.16)
#     OUTS(dx+10.16,dy-2.54) OUT(dx+10.16,dy-5.08)
# (ILIM cambia de lado entre los dos chips -- real, no error de transcripcion:
# confirmado leyendo el .kicad_sym, no supuesto por simetria.)
#
# PG y PGFB: NC en los 4 chips. PG porque el DS pide flotarlo si no se usa
# (§1.3/§1.4, "float the PG pin"). PGFB (pin de threshold del comparador de
# PG) NO tiene componente en el bom.csv ni cita del DS en design-notes.md
# para esta puerta -- dejarlo NC (en vez de inventar un tie a OUT sin
# respaldo) es la lectura conservadora: PG ya esta sin monitorear, asi que
# el threshold que fija PGFB no tiene efecto observable, y no maquillar una
# conexion "inferida" que ningun documento pide es mas honesto que
# inventarla. VIOC (solo LT3094): NC, "if unused, float the VIOC pin" (DS,
# §1.4).
XU45, XU67 = 274.32, 274.32          # ancla en X de U4/U5 y U6/U7 (misma
                                      # columna, alineado visualmente)
YU4, YU5 = 60.96, 86.36              # ancla en Y de U4/U5 (25.4mm aparte)
YU6, YU7 = 161.29, 186.69            # ancla en Y de U6/U7
XPL, XPR = 274.32 - 10.16, 274.32 + 10.16   # columnas de pines izq/der (264.16/284.48)

X_C1922 = 248.92    # caps de entrada (C19-C22), pegadas al pin IN de cada chip
X_C2326 = 299.72    # caps de salida (C23-C26), pegadas al pin OUT (pre-ballast)
X_IN_TRUNK = 257.81  # troncal vertical que une IN+EN/UV de la pareja + feed
X_SET_TRUNK = 261.62 # troncal vertical que une SET de la pareja -> R_SET/C_SET
X_RILIM_L = 252.73   # columna de R11/R12 (ILIM a la IZQUIERDA en el LT3045)
X_RILIM_R = 294.64   # columna de R13/R14 (ILIM a la DERECHA en el LT3094)
X_RCSET = 245.11     # columna de R9/R10 (rama R del SET->GNDREF)
X_RCSET2 = 238.76    # columna de C15/C16 (rama C, EN PARALELO con R9/R10 --
                     # fix round 1: R9/C15 estaban en SERIE, R_SET tiene que
                     # ir del pin SET a GNDREF con C_SET en paralelo, no en
                     # cascada -- si no el pin SET no tiene camino DC a masa)
X_D = 287.02          # ancla de D10/D11 (puente IN_TRUNK <-> nodo de salida).
                       # OJO: tiene que caer en la rejilla de 1.27mm -- el
                       # punto medio geometrico entre X_IN_TRUNK y X_P12/X_N12
                       # (287.655) NO cae, y el MCP lo redondeaba en silencio
                       # al colocar el componente, dejando las wires (que
                       # usan X_D-3.81/X_D+3.81, calculadas contra el valor
                       # sin redondear) apuntando 0.63mm a un lado del pin
                       # real -- "pines sin extremo de cable exacto" real,
                       # cazado por el propio assert de main(), no un bug
                       # cosmetico. 287.02 = 226 x 1.27, en rejilla.
YD_P, YD_N = 76.20, 176.53   # fila de D10 / D11 (hueco entre cada pareja)

PARTS += [
    # --- pareja positiva U4/U5 (LT3045xDD, riel +12.000V) ---
    ("U4", "Regulator_Linear:LT3045xDD", XU45, YU4, 0, "LT3045EDD#TRPBF"),
    ("U5", "Regulator_Linear:LT3045xDD", XU45, YU5, 0, "LT3045EDD#TRPBF"),
    ("C19", "Device:C", X_C1922, YU4 + 1.27, 0, "10uF"),
    ("C20", "Device:C", X_C1922, YU5 + 1.27, 0, "10uF"),
    ("C23", "Device:C", X_C2326, YU4 + 1.27, 0, "10uF"),
    ("C24", "Device:C", X_C2326, YU5 + 1.27, 0, "10uF"),
    ("R11", "Device:R", X_RILIM_L, YU4 + 6.35, 0, "374"),
    ("R12", "Device:R", X_RILIM_L, YU5 + 6.35, 0, "374"),
    ("R15", "Device:R", X_P12, YU4 + 1.27, 0, "20mOhm"),
    ("R16", "Device:R", X_P12, YU5 + 1.27, 0, "20mOhm"),
    ("R9",  "Device:R", X_RCSET, 82.55, 0, "120k"),
    ("C15", "Device:C", X_RCSET2, 82.55, 0, "22uF"),
    ("D10", "Diode:SS14", X_D, YD_P, 0, "SS14"),
    # --- pareja negativa U6/U7 (LT3094xDD, riel -12.000V) ---
    ("U6", "Regulator_Linear:LT3094xDD", XU67, YU6, 0, "LT3094EDD#PBF"),
    ("U7", "Regulator_Linear:LT3094xDD", XU67, YU7, 0, "LT3094EDD#PBF"),
    ("C21", "Device:C", X_C1922, YU6 - 1.27, 0, "10uF"),
    ("C22", "Device:C", X_C1922, YU7 - 1.27, 0, "10uF"),
    ("C25", "Device:C", X_C2326, YU6 - 1.27, 0, "10uF"),
    ("C26", "Device:C", X_C2326, YU7 - 1.27, 0, "10uF"),
    ("R13", "Device:R", X_RILIM_R, YU6 + 6.35, 0, "9.31k"),
    ("R14", "Device:R", X_RILIM_R, YU7 + 6.35, 0, "9.31k"),
    ("R17", "Device:R", X_N12, YU6 - 1.27, 0, "20mOhm"),
    ("R18", "Device:R", X_N12, YU7 - 1.27, 0, "20mOhm"),
    ("R10", "Device:R", X_RCSET, 182.88, 0, "120k"),
    ("C16", "Device:C", X_RCSET2, 182.88, 0, "22uF"),
    ("D11", "Diode:SS14", X_D, YD_N, 180, "SS14"),
    # --- GNDREF <-> GND: unico puente ---
    ("JP1", "Device:NetTie_2", 350.52, YMID, 0, "GNDREF-GND"),
]

FOOTPRINT.update({
    "U4": "Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm",
    "U5": "Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm",
    # sin _ThermalVias (Tarea 8 ronda 1, orquestador): esa variante trae
    # taladro 0.2mm, fuera de la capability JLC 2 capas (min 0.3mm) y de
    # m_MinThroughDrill de la placa. Granja de vias 0.3mm manual en el EP,
    # igual que U4/U5, ver build_pcb.py.
    "U6": "Package_DFN_QFN:DFN-12-1EP_3x3mm_P0.45mm_EP1.65x2.38mm",
    "U7": "Package_DFN_QFN:DFN-12-1EP_3x3mm_P0.45mm_EP1.65x2.38mm",
    "R9": "Resistor_SMD:R_0805_2012Metric", "R10": "Resistor_SMD:R_0805_2012Metric",
    "R11": "Resistor_SMD:R_0603_1608Metric", "R12": "Resistor_SMD:R_0603_1608Metric",
    "R13": "Resistor_SMD:R_0603_1608Metric", "R14": "Resistor_SMD:R_0603_1608Metric",
    "R15": "Resistor_SMD:R_1206_3216Metric", "R16": "Resistor_SMD:R_1206_3216Metric",
    "R17": "Resistor_SMD:R_1206_3216Metric", "R18": "Resistor_SMD:R_1206_3216Metric",
    "C15": "Capacitor_SMD:C_1210_3225Metric", "C16": "Capacitor_SMD:C_1210_3225Metric",
})
FOOTPRINT.update(dict.fromkeys(
    ("C19", "C20", "C21", "C22", "C23", "C24", "C25", "C26"),
    "Capacitor_SMD:C_1206_3216Metric"))
FOOTPRINT.update({"D10": "Diode_SMD:D_SMA", "D11": "Diode_SMD:D_SMA",
                  "JP1": "NetTie:NetTie-2_SMD_Pad0.5mm"})

POWER += [
    # GND propio de cada chip -- Kelvin real: R_ILIM llega DIRECTO a este
    # mismo punto (ver WIRES), no a un riel de GND compartido y lejano.
    ("#G_U4", "power:GND", XU45, YU4 + 12.70, 0),
    ("#G_U5", "power:GND", XU45, YU5 + 12.70, 0),
    ("#G_U6", "power:GND", XU67, YU6 + 12.70, 0),
    ("#G_U7", "power:GND", XU67, YU7 + 12.70, 0),
    ("#G_C1922", "power:GND", X_C1922, 99.06, 0),
    ("#G_C2122", "power:GND", X_C1922, 196.85, 0),
    ("#G_C2326", "power:GND", X_C2326, 99.06, 0),
    ("#G_C2526", "power:GND", X_C2326, 196.85, 0),
    ("#G_JP1", "power:GND", 356.87, YMID, 0),
]

WIRES += [
    # ===================== pareja positiva (U4/U5) =====================
    # IN+EN/UV: jumper local dentro de cada chip (mismo X, EN/UV 2.54mm mas
    # abajo que IN) -- ver docstring, "atar a IN" (§1.3).
    ("U4 en tie", [[XPL, YU4 - 2.54], [XPL, YU4]]),
    ("U5 en tie", [[XPL, YU5 - 2.54], [XPL, YU5]]),
    # troncal IN: feed desde +13V1 (fin del riel existente en x=241.30) +
    # tap de D10 + IN de U4/U5, todo en una columna vertical propia (evita
    # pasar por ILIM/SET, que viven en la MISMA X que IN/EN-UV pero mas
    # abajo -- columna separada, sin pass-through sobre pines ajenos).
    ("+13V1 feed", [[241.30, YP], [X_IN_TRUNK, YP]]),
    ("U4 IN tap", [[XPL, YU4 - 2.54], [X_IN_TRUNK, YU4 - 2.54]]),
    ("U5 IN tap", [[XPL, YU5 - 2.54], [X_IN_TRUNK, YU5 - 2.54]]),
] + vrail(X_IN_TRUNK, [YU4 - 2.54, YP, YD_P, YU5 - 2.54], "U45 IN trunk ") + [
    # C19/C20: entrada, pegadas al pin IN de cada chip; retorno a GND propio.
    ("C19 tap", [[X_C1922, YU4 - 2.54], [XPL, YU4 - 2.54]]),
    ("C20 tap", [[X_C1922, YU5 - 2.54], [XPL, YU5 - 2.54]]),
] + vrail(X_C1922, [YP, YU5 + 5.08, 99.06], "C1920 gnd ") + [
    # ILIM(U4/U5) -> R11/R12 -> GND propio del chip (Kelvin: el jog llega
    # exacto al mismo punto donde nace el stub de GND de ese chip).
    ("R11 ilim", [[XPL, YU4 + 2.54], [X_RILIM_L, YU4 + 2.54]]),
    ("R11 gnd",  [[X_RILIM_L, YU4 + 10.16], [XU45, YU4 + 10.16]]),
    ("R12 ilim", [[XPL, YU5 + 2.54], [X_RILIM_L, YU5 + 2.54]]),
    ("R12 gnd",  [[X_RILIM_L, YU5 + 10.16], [XU45, YU5 + 10.16]]),
    ("U4 gnd stub", [[XU45, YU4 + 10.16], [XU45, YU4 + 12.70]]),
    ("U5 gnd stub", [[XU45, YU5 + 10.16], [XU45, YU5 + 12.70]]),
    # SET(U4/U5) unidos entre si -> R9(120k)+C15(22uF) -> GNDREF (spec
    # §1.3: "tie all SET pins together").
    ("U4 SET tap", [[XPL, YU4 + 5.08], [X_SET_TRUNK, YU4 + 5.08]]),
    ("U5 SET tap", [[XPL, YU5 + 5.08], [X_SET_TRUNK, YU5 + 5.08]]),
] + vrail(X_SET_TRUNK, [YU4 + 5.08, 78.74, YU5 + 5.08], "U45 SET trunk ") \
  + rail(78.74, [X_RCSET2, X_RCSET, X_SET_TRUNK], "U45 SET tap ") + [
    # R9 (120k) y C15 (22uF) EN PARALELO -- fix round 1 (task review): iban
    # en serie (SET->R9->C15->GNDREF), lo que le quita a I_SET su camino DC
    # a masa (el cap bloquea DC). Topologia correcta del DS (§1.3): ambos
    # de SET a GNDREF, compartiendo los dos extremos.
] + rail(86.36, [X_RCSET2, X_RCSET], "U45 SET gndref tie ") + [
    ("C15 gndref", [[X_RCSET, 86.36], [X_RCSET, 88.90]]),
    # OUTS(U4/U5) y OUT(U4/U5)->ballast(R15/R16), todos al nodo +12V real.
    # C23/C24 (salida, pre-ballast) cuelgan del mismo tap que OUT.
] + rail(YU4 - 2.54, [XPR, X_C2326, X_P12], "U4 out ") \
  + rail(YU5 - 2.54, [XPR, X_C2326, X_P12], "U5 out ") \
  + vrail(X_C2326, [YP, YU5 + 5.08, 99.06], "C2324 gnd ") + [
    ("U4 outs", [[XPR, YU4], [X_P12, YU4]]),
    ("U5 outs", [[XPR, YU5], [X_P12, YU5]]),
] + vrail(X_P12, [YU4, YP, YD_P, YU5, YU5 + 5.08], "12V node ") + [
    # D10: K(izq, sin rotar)->troncal IN(+13V1), A(der)->nodo +12V real
    # (anodo en OUT/+12V, catodo en IN/+13V1 -- §1.3, orientacion inferida).
    ("D10 k", [[X_IN_TRUNK, YD_P], [X_D - 3.81, YD_P]]),
    ("D10 a", [[X_D + 3.81, YD_P], [X_P12, YD_P]]),

    # ===================== pareja negativa (U6/U7) =====================
    ("U6 en tie", [[XPL, YU6 - 5.08], [XPL, YU6 - 2.54]]),
    ("U7 en tie", [[XPL, YU7 - 5.08], [XPL, YU7 - 2.54]]),
    ("-12V9 feed", [[241.30, YN], [X_IN_TRUNK, YN]]),
    ("U6 IN tap", [[XPL, YU6 - 5.08], [X_IN_TRUNK, YU6 - 5.08]]),
    ("U7 IN tap", [[XPL, YU7 - 5.08], [X_IN_TRUNK, YU7 - 5.08]]),
] + vrail(X_IN_TRUNK, [YU6 - 5.08, YN, YD_N, YU7 - 5.08], "U67 IN trunk ") + [
    ("C21 tap", [[X_C1922, YU6 - 5.08], [XPL, YU6 - 5.08]]),
    ("C22 tap", [[X_C1922, YU7 - 5.08], [XPL, YU7 - 5.08]]),
] + vrail(X_C1922, [YU6 + 2.54, YU7 + 2.54, 196.85], "C2122 gnd ") + [
    # ILIM(U6/U7) esta del lado DERECHO (asimetria real LT3094, ver
    # docstring) -> R13/R14 -> GND propio, columna X_RILIM_R.
    ("R13 ilim", [[XPR, YU6 + 2.54], [X_RILIM_R, YU6 + 2.54]]),
    ("R13 gnd",  [[X_RILIM_R, YU6 + 10.16], [XU67, YU6 + 10.16]]),
    ("R14 ilim", [[XPR, YU7 + 2.54], [X_RILIM_R, YU7 + 2.54]]),
    ("R14 gnd",  [[X_RILIM_R, YU7 + 10.16], [XU67, YU7 + 10.16]]),
    ("U6 gnd stub", [[XU67, YU6 + 10.16], [XU67, YU6 + 12.70]]),
    ("U7 gnd stub", [[XU67, YU7 + 10.16], [XU67, YU7 + 12.70]]),
    ("U6 SET tap", [[XPL, YU6 + 5.08], [X_SET_TRUNK, YU6 + 5.08]]),
    ("U7 SET tap", [[XPL, YU7 + 5.08], [X_SET_TRUNK, YU7 + 5.08]]),
] + vrail(X_SET_TRUNK, [YU6 + 5.08, 179.07, YU7 + 5.08], "U67 SET trunk ") \
  + rail(179.07, [X_RCSET2, X_RCSET, X_SET_TRUNK], "U67 SET tap ") + [
    # R10/C16 en paralelo, mismo fix que R9/C15 arriba.
] + rail(186.69, [X_RCSET2, X_RCSET], "U67 SET gndref tie ") + [
    ("C16 gndref", [[X_RCSET, 186.69], [X_RCSET, 189.23]]),
] + rail(YU6 - 5.08, [XPR, X_C2326, X_N12], "U6 out ") \
  + rail(YU7 - 5.08, [XPR, X_C2326, X_N12], "U7 out ") \
  + vrail(X_C2326, [YU6 + 2.54, YU7 + 2.54, 196.85], "C2526 gnd ") + [
    ("U6 outs", [[XPR, YU6 - 2.54], [X_N12, YU6 - 2.54]]),
    ("U7 outs", [[XPR, YU7 - 2.54], [X_N12, YU7 - 2.54]]),
] + vrail(X_N12, [YU6 - 2.54, YU6 + 2.54, YN, YD_N, YU7 - 2.54, YU7 + 2.54], "-12V node ") + [
    # D11: espejo negativo de D10 -- rotado 180, mismo patron que D13
    # espeja a D12 (§1.4: gap real, inferencia por analogia con D10/D13).
    # A(izq tras rotar)->troncal IN(-12V9), K(der tras rotar)->nodo -12V.
    ("D11 a", [[X_IN_TRUNK, YD_N], [X_D - 3.81, YD_N]]),
    ("D11 k", [[X_D + 3.81, YD_N], [X_N12, YD_N]]),

    # ===================== isla de referencia GNDREF <-> GND =====================
    ("JP1 gndref", [[350.52 - 2.54, YMID], [344.17, YMID]]),
    ("JP1 gnd",    [[350.52 + 2.54, YMID], [356.87, YMID]]),
]

LABELS += [
    ("GNDREF", X_RCSET, 88.90),    # fondo comun R9/C15 (SET positivo) -> GNDREF
    ("GNDREF", X_RCSET, 189.23),   # fondo comun R10/C16 (SET negativo) -> GNDREF
    ("GNDREF", 344.17, YMID),      # JP1, lado GNDREF
]

for _r, _x, _y in [("R9", X_RCSET, 82.55), ("C15", X_RCSET2, 82.55),
                   ("R10", X_RCSET, 182.88), ("C16", X_RCSET2, 182.88),
                   ("R11", X_RILIM_L, YU4 + 6.35), ("R12", X_RILIM_L, YU5 + 6.35),
                   ("R13", X_RILIM_R, YU6 + 6.35), ("R14", X_RILIM_R, YU7 + 6.35),
                   ("R15", X_P12, YU4 + 1.27), ("R16", X_P12, YU5 + 1.27),
                   ("R17", X_N12, YU6 - 1.27), ("R18", X_N12, YU7 - 1.27),
                   ("C19", X_C1922, YU4 + 1.27), ("C20", X_C1922, YU5 + 1.27),
                   ("C21", X_C1922, YU6 - 1.27), ("C22", X_C1922, YU7 - 1.27),
                   ("C23", X_C2326, YU4 + 1.27), ("C24", X_C2326, YU5 + 1.27),
                   ("C25", X_C2326, YU6 - 1.27), ("C26", X_C2326, YU7 - 1.27)]:
    FIELDS += side_fields(_r, _x, _y)
FIELDS += [
    ("U4", "Reference", 266.70, 52.07), ("U4", "Value", 266.70, 54.61),
    ("U5", "Reference", 266.70, 77.47), ("U5", "Value", 266.70, 80.01),
    ("U6", "Reference", 266.70, 149.86), ("U6", "Value", 266.70, 152.40),
    ("U7", "Reference", 266.70, 175.26), ("U7", "Value", 266.70, 177.80),
    ("D10", "Reference", X_D + 5.08, YD_P - 3.81), ("D10", "Value", X_D + 5.08, YD_P),
    ("D11", "Reference", X_D + 5.08, YD_N - 3.81), ("D11", "Value", X_D + 5.08, YD_N),
    ("JP1", "Reference", 350.52, YMID - 6.35), ("JP1", "Value", 350.52, YMID + 6.35),
]

# PG/PGFB: NC en los 4 chips (ver comentario grande arriba). VIOC: NC, solo
# LT3094 (U6/U7 no tienen VIOC).
NO_CONNECTS += [
    (XPR, YU4 + 5.08), (XPR, YU4 + 2.54),   # U4 PG, PGFB
    (XPR, YU5 + 5.08), (XPR, YU5 + 2.54),   # U5 PG, PGFB
    (XPL, YU6), (XPR, YU6), (XPL, YU6 + 2.54),   # U6 PG, PGFB, VIOC
    (XPL, YU7), (XPR, YU7), (XPL, YU7 + 2.54),   # U7 PG, PGFB, VIOC
]

TEXTS += [
    ("GNDREF: isla de referencia -- SET, OUTS y divisores; unico puente JP1.",
     322.58, 100.33),
    ("0.8 uVrms es dato de datasheet con el layout de la nota de aplicacion:",
     322.58, 102.87),
    ("no se presume hasta medir con el LNA (spec S11.7).", 322.58, 105.41),
    ("OUTS de U4/U5 y U6/U7 van al nodo +12V/-12V real (no a GNDREF, pese",
     322.58, 107.95),
    ("a la nota de arriba): el Kelvin fisico unico lo impone el PCB (Task 8).",
     322.58, 110.49),
    ("D10: orientacion inferida (no confirmada por el DS), verificar contra",
     X_IN_TRUNK, 53.34),
    ("demo board DC2491A/DC2624A antes de soldar (design-notes.md v2 S1.3).",
     X_IN_TRUNK, 55.88),
    ("D11: orientacion inferida por analogia con D10/D13 (no hay cita del",
     X_IN_TRUNK, 203.20),
    ("DS del LT3094 -- design-notes.md v2 S1.4), verificar contra demo board.",
     X_IN_TRUNK, 205.74),
]
# ============================================================ fin Task 6 ==



# ============================================================================
# Isla de telemetria (Task 5 del plan v3; spec 2026-08-18 §4)
#
# Cinco chips que miden la fuente desde dentro. Vive en la banda y=235..330,
# libre en la A2 despues de la etapa ultra.
#
# POR QUE CASI TODO VA POR ETIQUETA Y NO POR CABLE. El resto de esta hoja
# cablea sobre coordenadas de pin a proposito. Aqui no: los cinco chips
# comparten dos redes (SDA_A/SCL_A) y tres nodos de divisor, y dibujarlos con
# cables reales seria una maraña que cruza media hoja sin decir nada. El bus
# I2C se dibuja como se dibuja un bus. El mecanismo es el mismo que ya usan
# GNDREF y VRAW+ (varios labels sin cable entre ellos, KiCad los funde).
#
# LOS DOS SHUNTS SI SON CIRUGIA REAL, y estan lejos de aqui:
#   R19 parte el cable "+12V->J2" -> el nodo de abajo se llama +12V_BUS.
#   R20 parte el cable "J6 +5V"   -> el nodo de abajo se llama +5V_M2.
# En los dos casos el shunt queda AGUAS ABAJO del riel, asi que lo que se mide
# es la corriente que SALE de la placa, no la que consumen los LED indicadores
# ni la propia isla. Y en los dos casos el pin Vbus del INA226 se ata al lado
# que interesa, que NO es el mismo en los dos:
#   U8 (+12 V): Vbus al lado de J2 -- lo que ven los modulos.
#   U9 (+5 V):  Vbus al lado del riel -- porque ese nodo ES la referencia de
#               los divisores negativos de U10, y medirlo es lo que hace que
#               la lectura de -12 V se autocalibre.
#
# EL SENTIDO KELVIN de los shunts es regla de PCB, no de esquematico: las
# pistas de sensado salen de los pads del shunt, nunca del cobre de potencia.
# Va en la Fase C.
# ---------------------------------------------------------------------------

# --- geometria de los tres divisores ---------------------------------------
X_DIV = {"-12V": 137.16, "VRAW+": 154.94, "VRAW-": 172.72}
Y_ARR, Y_RSUP = 238.76, 246.38     # fila del simbolo de arriba / R superior
Y_TAP = 254.00                      # fila del punto medio (la que se mide)
Y_RINF, Y_ABA = 261.62, 271.78      # R inferior / simbolo de abajo

# (canal, ref de la R superior, ref de la inferior, terminal arriba, abajo)
# INVARIANTE: la R de 100k mira SIEMPRE al riel medido y la de 20k SIEMPRE a
# la referencia. En el canal positivo la referencia es GNDA (abajo) y en los
# negativos es el +5 V (arriba), asi que las dos resistencias cambian de sitio
# entre canales -- pero cual toca el riel no cambia nunca. Eso es lo que va en
# la seda de la placa: es el unico error de esta isla que ninguna puerta ve.
DIVISORES = [
    ("-12V",  "R24", "20k",  "R21", "100k", ("sym", "power:+5V"), ("sym", "power:-12V")),
    ("VRAW+", "R22", "100k", "R25", "20k",  ("lbl", "VRAW+"),     ("sym", "power:GND")),
    ("VRAW-", "R26", "20k",  "R23", "100k", ("sym", "power:+5V"), ("lbl", "VRAW-")),
]
TAP_LBL = {"-12V": "TAP_-12V", "VRAW+": "TAP_VRAW+", "VRAW-": "TAP_VRAW-"}
TP_ISLA = {"-12V": ("TP9", 144.78), "VRAW+": ("TP10", 162.56), "VRAW-": ("TP11", 180.34)}

_isla_pw = 0


def _pw(sym: str, x: float, y: float, rot: int) -> str:
    """Anade un simbolo de potencia con referencia unica y la devuelve."""
    global _isla_pw
    _isla_pw += 1
    ref = f"#T{_isla_pw}"
    POWER.append((ref, sym, x, y, rot))
    return ref


for _ch, _rsup, _vsup, _rinf, _vinf, _arr, _aba in DIVISORES:
    _x = X_DIV[_ch]
    PARTS += [(_rsup, "Device:R", _x, Y_RSUP, 0, _vsup),
              (_rinf, "Device:R", _x, Y_RINF, 0, _vinf)]
    FOOTPRINT[_rsup] = FOOTPRINT[_rinf] = "Resistor_SMD:R_0805_2012Metric"
    WIRES += [
        (f"div {_ch} arr",  [[_x, Y_ARR],   [_x, Y_RSUP - 3.81]]),
        (f"div {_ch} med1", [[_x, Y_RSUP + 3.81], [_x, Y_TAP]]),
        (f"div {_ch} med2", [[_x, Y_TAP],   [_x, Y_RINF - 3.81]]),
        (f"div {_ch} aba",  [[_x, Y_RINF + 3.81], [_x, Y_ABA]]),
    ]
    for _tipo, _que, _y, _rot in ((_arr[0], _arr[1], Y_ARR, 0), (_aba[0], _aba[1], Y_ABA, 180)):
        if _tipo == "sym":
            # GND se dibuja apuntando hacia abajo (rot 0 al llegar bajando);
            # los rieles apuntan hacia arriba (rot 0 al llegar subiendo).
            _r = 0 if (_que.endswith("GND") and _y == Y_ABA) or _y == Y_ARR else 180
            _pw(_que, _x, _y, _r)
        else:
            LABELS.append((_que, _x, _y))
    LABELS.append((TAP_LBL[_ch], _x, Y_TAP))
    _tp, _xtp = TP_ISLA[_ch]
    PARTS.append((_tp, "Connector:TestPoint", _xtp, Y_TAP, 0, TAP_LBL[_ch]))
    FOOTPRINT[_tp] = "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm"
    FIELDS += [(_tp, "Reference", _xtp + 1.27, Y_TAP - 5.08),
               (_tp, "Value", _xtp + 1.27, Y_TAP - 2.54)]
    WIRES.append((f"tap {_ch} TP", [[_x, Y_TAP], [_xtp, Y_TAP]]))

# --- los cinco chips --------------------------------------------------------
PARTS += [
    ("U8",  "Sensor_Energy:INA226",       238.76, 251.46, 0, "INA226 0x40"),
    ("U9",  "Sensor_Energy:INA226",       238.76, 292.10, 0, "INA226 0x41"),
    ("U10", "Analog_ADC:ADS1115IDGS",     200.66, 264.16, 0, "ADS1115 0x49"),
    ("U11", "Sensor_Temperature:TMP1075DGK", 299.72, 246.38, 0, "TMP1075 0x48"),
    ("U12", "Isolator:ISO1541",           317.50, 274.32, 180, "ISO1541"),
    ("J8",  "Connector:Conn_01x04_Pin",   355.60, 274.32, 180, "I2C AISLADO"),
]
FOOTPRINT.update({
    # OJO: el encapsulado DGS de TI se llama VSSOP-10 en su datasheet y
    # MSOP-10 en la libreria de KiCad. Es el mismo cuerpo de 3x3 mm y 0.5 mm
    # de paso; el bom.csv dice VSSOP porque es el nombre del fabricante.
    "U8":  "Package_SO:MSOP-10_3x3mm_P0.5mm",
    "U9":  "Package_SO:MSOP-10_3x3mm_P0.5mm",
    "U10": "Package_SO:MSOP-10_3x3mm_P0.5mm",
    "U11": "Package_SO:VSSOP-8_3x3mm_P0.65mm",
    "U12": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    # Paso de 2.00 mm A PROPOSITO: J2 y J6 son KK-254 de 2.54 y este cable no
    # tiene que poder entrar ahi ni por error (spec §4.3).
    "J8":  "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
})

# --- pasivos de la isla -----------------------------------------------------
X_DESAC = [137.16, 154.94, 172.72, 190.50, 208.28, 226.06]   # C29-C33 + C35
Y_DESAC, Y_D5V, Y_DGND = 320.04, 316.23, 323.85
for _ref, _x, _val, _fp in zip(
        ["C29", "C30", "C31", "C32", "C33", "C35"], X_DESAC,
        ["0.1uF", "0.1uF", "0.1uF", "0.1uF", "0.1uF", "10uF"],
        ["Capacitor_SMD:C_0603_1608Metric"] * 5 + ["Capacitor_SMD:C_0805_2012Metric"]):
    PARTS.append((_ref, "Device:C", _x, Y_DESAC, 0, _val))
    FOOTPRINT[_ref] = _fp
    FIELDS += [(_ref, "Reference", _x + 5.08, Y_DESAC - 1.27),
               (_ref, "Value", _x + 5.08, Y_DESAC + 2.54)]
WIRES += rail(Y_D5V, [127.00] + X_DESAC, "isla +5V ")
WIRES += rail(Y_DGND, [127.00] + X_DESAC, "isla GND ")
WIRES += [("isla +5V sym", [[127.00, Y_D5V], [127.00, 311.15]]),
          ("isla GND sym", [[127.00, Y_DGND], [127.00, 328.93]])]
_pw("power:+5V", 127.00, 311.15, 0)
_pw("power:GND", 127.00, 328.93, 0)

# C34: el desacoplo del LADO 1 del aislador. Va aparte de la fila de arriba a
# proposito -- su masa es GNDD, no la de la fuente, y ese es justo el punto de
# todo el chip. Si acabara en la misma fila que C29-C33 el aislador no
# aislaria nada.
PARTS.append(("C34", "Device:C", 345.44, 292.10, 0, "0.1uF"))
FOOTPRINT["C34"] = "Capacitor_SMD:C_0603_1608Metric"
FIELDS += [("C34", "Reference", 350.52, 290.83), ("C34", "Value", 350.52, 294.64)]
WIRES += [("C34 vcc", [[345.44, 288.29], [345.44, 283.21]]),
          ("C34 gnd", [[345.44, 295.91], [345.44, 300.99]])]
_pw("power:+3V3", 345.44, 283.21, 0)
_pw("power:GNDD", 345.44, 300.99, 0)

# Pull-ups. Los del lado analogico se pueblan; los del digital NO (R29/R30
# salen DNP): el modulo 2 no esta disenado (#111) y no se sabe si los lleva.
# Son mutuamente excluyentes -- poblar las dos parejas da 1.1k en paralelo y
# 3 mA, y el lado 1 del ISO1541 solo sumidera 3.5 mA especificados.
for _ref, _x, _net, _riel, _val in [
        ("R27", 269.24, "SDA_A", "power:+5V",  "2k2"),
        ("R28", 276.86, "SCL_A", "power:+5V",  "2k2"),
        ("R29", 325.12, "SDA_D", "power:+3V3", "2k2 DNP"),
        ("R30", 317.50, "SCL_D", "power:+3V3", "2k2 DNP")]:
    _y = 292.10 if _net.endswith("_A") else 300.99
    PARTS.append((_ref, "Device:R", _x, _y, 0, _val))
    FOOTPRINT[_ref] = "Resistor_SMD:R_0603_1608Metric"
    FIELDS += [(_ref, "Reference", _x + 5.08, _y - 1.27),
               (_ref, "Value", _x + 5.08, _y + 2.54)]
    WIRES += [(f"{_ref} riel", [[_x, _y - 3.81], [_x, _y - 8.89]]),
              (f"{_ref} net",  [[_x, _y + 3.81], [_x, _y + 8.89]])]
    _pw(_riel, _x, _y - 8.89, 0)
    LABELS.append((_net, _x, _y + 8.89))

# Clamps: la razon de que existan no es supervivencia (los 100k del divisor ya
# limitan a 126 uA, 79x bajo el limite de 10 mA que TI publica en §9.1.3) sino
# el §7.3.1 del ADS1115 -- sobreexcitar una entrada altera las conversiones de
# las OTRAS. Sin diodo, un fallo del +5 V le quita la razon a las tres medidas
# a la vez, justo cuando hacen falta para diagnosticarlo.
for _ref, _y, _net in [("D14", 281.94, "TAP_-12V"), ("D15", 292.10, "TAP_VRAW-")]:
    PARTS.append((_ref, "Device:D_Schottky", 146.05, _y, 0, "BAT54"))
    FOOTPRINT[_ref] = "Diode_SMD:D_SOD-323"
    FIELDS += [(_ref, "Reference", 146.05, _y - 5.08), (_ref, "Value", 146.05, _y - 2.54)]
    WIRES += [(f"{_ref} k", [[142.24, _y], [137.16, _y]]),
              (f"{_ref} a", [[149.86, _y], [154.94, _y], [154.94, _y + 5.08]])]
    LABELS.append((_net, 137.16, _y))
    _pw("power:GND", 154.94, _y + 5.08, 0)

# --- cableado pin a pin de los cinco chips ---------------------------------
# (x, y del pin, polilinea hasta el terminal, terminal)
#   ("sym", simbolo, rot) | ("lbl", nombre) | ("nc",)
_PINES = [
    # U8 -- INA226 del +12 V (0x40)
    ((238.76, 238.76), [[238.76, 233.68]],                      ("sym", "power:+5V", 0)),
    ((238.76, 264.16), [[238.76, 269.24]],                      ("sym", "power:GND", 0)),
    ((228.60, 254.00), [[220.98, 254.00], [220.98, 248.92]],    ("sym", "power:+12V", 0)),
    ((228.60, 256.54), [[218.44, 256.54]],                      ("lbl", "+12V_BUS")),
    ((228.60, 243.84), [[218.44, 243.84]],                      ("lbl", "+12V_BUS")),
    ((248.92, 251.46), [[259.08, 251.46]],                      ("lbl", "SDA_A")),
    ((248.92, 254.00), [[259.08, 254.00]],                      ("lbl", "SCL_A")),
    ((248.92, 243.84), [[254.00, 243.84], [254.00, 236.22]],    ("sym", "power:GND", 180)),
    ((248.92, 246.38), [[259.08, 246.38], [259.08, 236.22]],    ("sym", "power:GND", 180)),
    ((248.92, 259.08), None,                                    ("nc",)),
    # U9 -- INA226 del +5 V de U3 (0x41)
    ((238.76, 279.40), [[238.76, 274.32]],                      ("sym", "power:+5V", 0)),
    ((238.76, 304.80), [[238.76, 309.88]],                      ("sym", "power:GND", 0)),
    ((228.60, 294.64), [[215.90, 294.64], [215.90, 289.56]],    ("sym", "power:+5V", 0)),
    ((228.60, 284.48), [[220.98, 284.48], [220.98, 279.40]],    ("sym", "power:+5V", 0)),
    ((228.60, 297.18), [[218.44, 297.18]],                      ("lbl", "+5V_M2")),
    ((248.92, 292.10), [[259.08, 292.10]],                      ("lbl", "SDA_A")),
    ((248.92, 294.64), [[259.08, 294.64]],                      ("lbl", "SCL_A")),
    ((248.92, 284.48), [[254.00, 284.48], [254.00, 276.86]],    ("sym", "power:GND", 180)),
    ((248.92, 287.02), [[259.08, 287.02], [259.08, 276.86]],    ("sym", "power:+5V", 0)),
    ((248.92, 299.72), None,                                    ("nc",)),
    # U10 -- ADS1115 (0x49). ADDR a VDD y no a GND: con ADDR a GND responde
    # en 0x48, que es donde vive U11 (TI SBAS444E tabla 7-2 y SBOS854F p.14).
    ((190.50, 261.62), [[182.88, 261.62]],                      ("lbl", "TAP_-12V")),
    ((190.50, 264.16), [[182.88, 264.16]],                      ("lbl", "TAP_VRAW+")),
    ((190.50, 266.70), [[182.88, 266.70]],                      ("lbl", "TAP_VRAW-")),
    ((190.50, 269.24), [[182.88, 269.24], [182.88, 274.32]],    ("sym", "power:GND", 0)),
    ((200.66, 251.46), [[200.66, 246.38]],                      ("sym", "power:+5V", 0)),
    ((200.66, 274.32), [[200.66, 279.40]],                      ("sym", "power:GND", 0)),
    ((210.82, 269.24), [[226.06, 269.24], [226.06, 259.08]],    ("sym", "power:+5V", 0)),
    ((210.82, 266.70), [[215.90, 266.70]],                      ("lbl", "SDA_A")),
    ((210.82, 264.16), [[215.90, 264.16]],                      ("lbl", "SCL_A")),
    ((210.82, 259.08), None,                                    ("nc",)),
    # U11 -- TMP1075 (0x48). Straps identicos a los del U13 del modulo 3.
    ((299.72, 238.76), [[299.72, 233.68]],                      ("sym", "power:+5V", 0)),
    ((299.72, 254.00), [[299.72, 259.08]],                      ("sym", "power:GND", 0)),
    ((289.56, 243.84), [[284.48, 243.84], [284.48, 236.22]],    ("sym", "power:GND", 180)),
    ((289.56, 246.38), [[279.40, 246.38], [279.40, 236.22]],    ("sym", "power:GND", 180)),
    ((289.56, 248.92), [[274.32, 248.92], [274.32, 236.22]],    ("sym", "power:GND", 180)),
    ((309.88, 243.84), [[317.50, 243.84]],                      ("lbl", "SDA_A")),
    ((309.88, 246.38), [[317.50, 246.38]],                      ("lbl", "SCL_A")),
    ((309.88, 248.92), None,                                    ("nc",)),
    # U12 -- ISO1541. Girado 180 para que el LADO 2 (la isla, GNDA, 5 V) mire
    # a la izquierda y el LADO 1 (el micro del modulo 2 (N657), GNDD, 3.3 V) mire a J8.
    ((307.34, 276.86), [[294.64, 276.86], [294.64, 271.78]],    ("sym", "power:+5V", 0)),
    ((307.34, 274.32), [[302.26, 274.32]],                      ("lbl", "SDA_A")),
    ((307.34, 271.78), [[302.26, 271.78]],                      ("lbl", "SCL_A")),
    ((307.34, 269.24), [[302.26, 269.24], [302.26, 264.16]],    ("sym", "power:GND", 180)),
]
for _pin, _poli, _term in _PINES:
    if _term[0] == "nc":
        NO_CONNECTS.append(_pin)
        continue
    WIRES.append((f"isla {_pin[0]:.0f},{_pin[1]:.0f}", [list(_pin)] + [list(p) for p in _poli]))
    _fin = _poli[-1]
    if _term[0] == "sym":
        _pw(_term[1], _fin[0], _fin[1], _term[2])
    else:
        LABELS.append((_term[1], _fin[0], _fin[1]))

# --- lado 1: U12 <-> J8, cuatro cables rectos ------------------------------
# El pinado de J8 se eligio para que no haya un solo cruce: 1 +3V3D, 2 SDA,
# 3 SCL, 4 GNDD, en el mismo orden en que salen los pines del ISO1541.
for _y, _nombre in [(276.86, "VCC1"), (274.32, "SDA1"),
                    (271.78, "SCL1"), (269.24, "GND1")]:
    if _nombre in ("VCC1", "GND1"):
        WIRES += [(f"J8 {_nombre} a", [[327.66, _y], [332.74, _y]]),
                  (f"J8 {_nombre} b", [[332.74, _y], [340.36, _y]]),
                  (f"J8 {_nombre} c", [[340.36, _y], [350.52, _y]])]
    else:
        WIRES.append((f"J8 {_nombre}", [[327.66, _y], [350.52, _y]]))
        LABELS.append(("SDA_D" if _nombre == "SDA1" else "SCL_D", 340.36, _y))
# +3V3D y GNDD entran de fuera por J8 (pines pasivos): sin PWR_FLAG el ERC los
# da por no alimentados, igual que ya pasa con los rieles de esta hoja.
WIRES += [("J8 3v3 sym",  [[332.74, 276.86], [332.74, 284.48]]),
          ("J8 3v3 flag", [[340.36, 276.86], [340.36, 284.48]]),
          ("J8 gndd sym", [[332.74, 269.24], [332.74, 261.62]]),
          ("J8 gndd flag",[[340.36, 269.24], [340.36, 261.62]])]
_pw("power:+3V3", 332.74, 284.48, 180)
_pw("power:PWR_FLAG", 340.36, 284.48, 180)
_pw("power:GNDD", 332.74, 261.62, 180)
_pw("power:PWR_FLAG", 340.36, 261.62, 0)

FIELDS += [
    ("U8",  "Reference", 238.76, 231.14), ("U8",  "Value", 238.76, 267.97),
    ("U9",  "Reference", 238.76, 271.78), ("U9",  "Value", 238.76, 308.61),
    ("U10", "Reference", 200.66, 243.84), ("U10", "Value", 200.66, 283.21),
    ("U11", "Reference", 299.72, 231.14), ("U11", "Value", 299.72, 257.81),
    ("U12", "Reference", 317.50, 265.43), ("U12", "Value", 317.50, 283.21),
    ("J8",  "Reference", 358.14, 271.78), ("J8",  "Value", 358.14, 267.97),
]
for _r, _v, _x, _y in [("R21", 0, 137.16, 261.62), ("R24", 0, 137.16, 246.38),
                       ("R22", 0, 154.94, 246.38), ("R25", 0, 154.94, 261.62),
                       ("R26", 0, 172.72, 246.38), ("R23", 0, 172.72, 261.62)]:
    FIELDS += [(_r, "Reference", _x - 8.89, _y - 1.27),
               (_r, "Value", _x - 8.89, _y + 2.54)]

TEXTS += [
    ("Isla de telemetria (spec 2026-08-18 §4). Los divisores: el 100k mira SIEMPRE al riel", 127.00, 226.06),
    ("medido y el 20k a la referencia. Atenuacion 1/6 en los tres canales: el pin del ADC", 127.00, 228.60),
    ("llega a 0.000 V justo cuando VRAW- llega a -25 V, la tension nominal del bulk.", 127.00, 231.14),
    ("R29/R30 van DNP: pull-ups del lado GNDD, excluyentes con los del modulo 2 (#111).", 127.00, 306.07),
]

# ========================================================= fin isla v3 ======


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
    _normalizar_sym_lib_table()


def _normalizar_sym_lib_table() -> None:
    """register_symbol_library escribe la uri de la libreria como ruta
    ABSOLUTA, y ademas es idempotente-por-nombre: si ya hay una entrada
    "sam17" contesta already_registered=True y NO la reescribe. Las dos cosas
    juntas son una bomba de relojeria: el sym-lib-table commiteado quedo
    apuntando a .claude/worktrees/psu-v2/... (el worktree de la ejecucion SDD,
    ya borrado), asi que en cualquier otra ruta la libreria no resuelve,
    add_schematic_component falla EN SILENCIO para U1/U2, y la corrida
    regenera un esquematico sin los dos pre-reguladores (ERC pasa de 0 a 2
    errores y el .kicad_sch encoge ~500 lineas). Se detecto al regenerar
    desde un worktree nuevo el 2026-08-17.

    Se reescribe a ${KIPRJMOD}, que es lo que ya hacia bien el fp-lib-table
    de al lado. Idempotente: si ya esta normalizado no toca el fichero.
    """
    tabla = f"{DIR}/sym-lib-table"
    if not os.path.exists(tabla):
        return
    original = open(tabla, encoding="utf-8").read()
    nuevo = re.sub(r'(\(name "sam17"\)\(type "KiCad"\)\(uri ")[^"]*(")',
                   r'\1${KIPRJMOD}/sam17.kicad_sym\2', original)
    if nuevo != original:
        open(tabla, "w", encoding="utf-8").write(nuevo)
        print("  sym-lib-table: uri normalizada a ${KIPRJMOD}")


# Namespace fijo del proyecto para UUIDs deterministas (fix F2 del task
# review: uuid.uuid4() hacia ~543 lineas de ruido en git en cada corrida,
# porque cada wire/label/texto se re-escribia con un UUID al azar aunque el
# contenido no cambiara). Creado UNA vez con uuid.uuid4() y hardcodeado --
# no tiene significado, solo tiene que quedar fijo para siempre.
PROJECT_UUID_NAMESPACE = uuid.UUID("a17f9c2e-8b3d-4f61-9e2a-5c7d1b0f4a63")

# Cuenta cuantas veces se pidio cada clave semantica, para que dos elementos
# con la MISMA clave (p.ej. dos wires con las mismas coordenadas) no colisionen
# en el mismo UUID -- el contador es estable porque WIRES/LABELS/TEXTS son
# listas fijas recorridas siempre en el mismo orden (build determinista).
_uuid_seen: dict[str, int] = {}


def _stable_uuid(key: str) -> str:
    """uuid5(PROJECT_UUID_NAMESPACE, clave) -- mismo texto de entrada, mismo
    UUID en toda corrida, a diferencia de uuid4() (al azar cada vez)."""
    n = _uuid_seen.get(key, 0)
    _uuid_seen[key] = n + 1
    return str(uuid.uuid5(PROJECT_UUID_NAMESPACE, key if n == 0 else f"{key}#{n}"))


def _wire_sexpr(x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        "\t(wire\n\t\t(pts\n"
        f"\t\t\t(xy {x1} {y1}) (xy {x2} {y2})\n"
        "\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n"
        f'\t\t(uuid "{_stable_uuid(f"wire:{x1},{y1},{x2},{y2}")}")\n\t)\n'
    )


def _label_sexpr(name: str, x: float, y: float) -> str:
    return (
        f'\t(label "{name}"\n'
        f"\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n"
        "\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n"
        f'\t\t(uuid "{_stable_uuid(f"label:{name}:{x},{y}")}")\n\t)\n'
    )


def _text_sexpr(text: str, x: float, y: float) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return (
        f'\t(text "{escaped}"\n'
        "\t\t(exclude_from_sim no)\n"
        f"\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n"
        "\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n"
        f'\t\t(uuid "{_stable_uuid(f"text:{x},{y}:{text}")}")\n\t)\n'
    )


def _no_connect_sexpr(x: float, y: float) -> str:
    """Cruz de no-conexion explicita (Task 6: PG/PGFB/VIOC de U4-U7, flotantes
    a proposito segun DS -- §1.3/§1.4). Mismo patron ya usado en
    hardware/03-vco/kicad/build_schematic.py para pines genuinamente sin
    usar: sin esto, ERC marca pin_not_connected en un pin que el propio
    datasheet pide dejar al aire."""
    return (
        "\t(no_connect\n"
        f"\t\t(at {x} {y})\n"
        f'\t\t(uuid "{_stable_uuid(f"nc:{x},{y}")}")\n\t)\n'
    )


def inject_wires_labels_texts(sch_path: str, wires: list, labels: list, texts: list,
                               no_connects: list | None = None) -> None:
    """Escribe wires/labels/texts/no_connects DIRECTO al .kicad_sch por texto,
    sin pasar por el MCP server.

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
    for x, y in (no_connects or []):
        segs.append(_no_connect_sexpr(round(x, 2), round(y, 2)))
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

        c.call("create_schematic", {"name": "sam17-power-v3", "path": DIR})
        with open(SCH, encoding="utf-8") as fh:
            txt = fh.read()
        title_block = (
            # A2 (no A3): la etapa ultra (Task 6) necesita ~280mm mas de ancho
            # a la derecha del pre-reg para U4-U7 + red SET/ILIM/ballast antes
            # de la isla +12V/-12V (que se corre a la derecha, ver ISLA_DX).
            '(paper "A2")\n'
            "\t(title_block\n"
            '\t\t(title "Modulo 01 v3 — Alimentacion sub-uV, ±12 V / +5V + telemetria")\n'
            f'\t\t(date "{DATE}")\n'
            f'\t\t(rev "{REV}")\n'
            '\t\t(company "SAM17 — Sintetizador analogico modular")\n'
            '\t\t(comment 1 "Variante Europa: primario 230VAC/50Hz. Pre-reg LM2941/LM2991 -> +13V1/-12V9")\n'
            '\t\t(comment 2 "Primario: fusible + MOV S20K275 + NTC soft-start + J7 (SMPS digital, spec S7)")\n'
            '\t\t(comment 3 "PE: J3.3 al esparrago de chasis; GND al mismo punto via J5 (S13)")\n'
            '\t\t(comment 4 "v3: sin crowbar (issue #118). Isla de telemetria U8-U12 en GNDA, aislada por U12")\n'
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
        # PG/PGFB/VIOC de U4-U7 (Task 6): flotantes a proposito (DS dixit),
        # sin wire -- cuentan como "extremo valido" via su propia cruz NC,
        # si no el check de pines sueltos de abajo los marca como cableado a
        # ojo cuando en realidad es un no-connect intencional.
        ends |= {(round(nx, 2), round(ny + YOFF, 2)) for nx, ny in NO_CONNECTS}
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
        nc_shifted = [(x, y + YOFF) for x, y in NO_CONNECTS]
        inject_wires_labels_texts(SCH, wires_shifted, labels_shifted, texts_shifted, nc_shifted)
        n_segs = sum(len(wp) - 1 for _l, wp in WIRES)
        print(f"cables: {len(WIRES)} definidos ({n_segs} segmentos) + "
              f"{len(LABELS)} labels + {len(TEXTS)} notas + {len(NO_CONNECTS)} "
              f"no-connects, escritos directo al fichero")

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
        # El netlist NO sale por el MCP: su export_netlist escribe el formato
        # kicadxml y el resto del repo (modulos 2 y 3, netdiff.py, los
        # check_netlist.py) lee el s-expression que saca kicad-cli. Un formato
        # distinto en un solo modulo deja a ese modulo fuera del golden test de
        # conectividad sin que nadie se entere -- que es exactamente lo que
        # pasaba con la v2, cuyo .net nunca llego a existir en disco cuando
        # corrian las puertas.
        kcli = os.environ.get(
            "KICAD_CLI", "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe")
        r = subprocess.run([kcli, "sch", "export", "netlist", "-o", NET, SCH],
                           capture_output=True, text=True)
        print(f"netlist: {(r.stdout or r.stderr).strip()[:120] or NET}")
        for tool, ext in [("export_schematic_svg", "svg"), ("export_schematic_pdf", "pdf")]:
            out = f"{DIR}/../schematics/sam17-power-v3.{ext}"
            c.call(tool, {"schematicPath": SCH, "outputPath": out})
        print("exportado a ../schematics/sam17-power-v3.{svg,pdf}")
    finally:
        c.close()


if __name__ == "__main__":
    main()
