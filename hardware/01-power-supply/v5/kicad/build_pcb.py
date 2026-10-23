"""Genera sam17-power-v5.kicad_pcb: 200 x 150 mm, 4 capas, colocada y ruteada.

    python build_pcb.py                 coloca, rutea y pasa el DRC (sale != 0 si no cierra)
    python build_pcb.py --solo-colocar  coloca y pone el cobre de potencia, sin rutear
    python build_pcb.py --desde-ruteo=RUTA   repite lo de despues de Freerouting sobre
                                        la placa ruteada que guardo una corrida anterior

Rutear necesita Freerouting, que este script NO descarga (una build
reproducible no baja binarios sola):

    FREEROUTING_JAR=/ruta/freerouting-2.4.1-executable.jar
    JAVA=/ruta/a/java              # la 2.4.1 esta compilada para Java 25

LA PLACA DE #474 NO TENIA NI UNA PISTA: 161 huellas, 0 segmentos, 0 vias, y
todas las puertas en verde porque ninguna contaba conexiones. Esta se genera
entera desde el netlist y termina con el DRC de KiCad con todas las
severidades y la paridad con el esquematico: 0 y 0 sin conectar, o el script
sale con error.

EL STACKUP:

    F.Cu     componentes, ruteo, cobre de potencia y masa vertida al final
    In1.Cu   PLANOS DE MASA partidos por dominio: GND24 | GNDA | GNDD
    In2.Cu   ruteo
    B.Cu     ruteo y masa vertida al final

Dos capas no daban para 204 componentes con tres masas: igual que el VCO
(hardware/03-vco), la capa interna de masa no lleva pistas -- se declara de
POTENCIA en el DSN para que Freerouting no la toque -- y las senales se
cruzan por F.Cu, In2 y B.Cu.

LOS TRES DOMINIOS se deciden por las redes de cada pieza (dominio_de()):

  * GND24 (izquierda): la entrada del ladrillo, M5 y el lado de ENTRADA de los
    cinco convertidores. Los modulos van en una columna con las entradas a la
    izquierda y las salidas a la derecha, asi que la frontera pasa por debajo
    de su cuerpo, que es donde esta su barrera de aislamiento.
  * GNDA (derecha y centro): todo lo analogico, el rack y la telemetria.
  * GNDD (abajo, isla): la salida del URB2405 (M1), su crowbar, J8/J9 y el
    lado 2 del ISO1541. Hueco de 2 mm a las otras dos masas.

GND24 y GNDA se tocan SOLO en NT1, pegada a los pads de masa de PS3 (el K78 no
es aislado). Es la decision firmada en la revision de #474.

EL COBRE DE POTENCIA NO LO RUTEA FREEROUTING. Por la entrada de 24 V pasan
~2.9 A (ladrillo_budget.py: 64.6 W de cajon a 22.4 V) y por +5V_DIG hasta
2.9 A (DIGITAL_A, el maximo a TJ = 125 C). Una pista de 0.5 mm en 1 oz se
calienta 10 C con ~1.4 A; y si se deja al ruteador, el camino de 3 A puede
acabar pasando por el pad de 0.5 mm de un divisor. Esos caminos van como
pistas gordas BLOQUEADAS (COBRE): KiCad las exporta al DSN como (type fix),
Freerouting las respeta como cobre fijo de su red y les engancha el resto de
pads de la red con pistas normales. Lo mismo para la disipacion de U1 y U2
(~1.9 W cada uno en DD-PAK): cobre en su aleta y vias termicas.

LA COLOCACION: las piezas grandes y los CI van anclados a mano (ANCLAS); el
resto se coloca solo, cada una cerca del centroide de los pads con los que
comparte red, siempre dentro de su dominio de masa y nunca encima del cobre
de potencia (colocar_satelites()).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power-v5.kicad_pcb")
PRO = os.path.join(DIR, "sam17-power-v5.kicad_pro")
EVIDENCIA_DRC = os.path.join(DIR, "sam17-power-v5-drc.json")
RUTADA = os.path.join(tempfile.gettempdir(), "sam17-power-v5-rutada.kicad_pcb")
NET = os.path.join(DIR, "sam17-power-v5.net")
SCH_NOMBRE = "sam17-power-v5.kicad_sch"
EN_WINDOWS = os.name == "nt"
KICAD_CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or (
    r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" if EN_WINDOWS else "kicad-cli")
STOCK = os.environ.get("KICAD_FOOTPRINTS", r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
                       if EN_WINDOWS else "/usr/share/kicad/footprints")
JAVA = os.environ.get("JAVA", "java")
FREEROUTING = os.environ.get("FREEROUTING_JAR", "")
PASADAS = int(os.environ.get("FREEROUTING_PASADAS", "40"))
RONDAS = int(os.environ.get("FREEROUTING_RONDAS", "3"))

W, H = 200.0, 150.0
MARGEN = 1.5                 # cuerpo de componente al canto
MONTAJE = [("H1", 5.0, 5.0), ("H2", 195.0, 5.0), ("H3", 5.0, 145.0), ("H4", 195.0, 145.0)]
MONTAJE_D = 3.2
SEPARACION = 1.0             # entre courtyards de satelites: aire para rutear y coser
                             # (con 0.6 no cabia la via de masa de 19 pines de CI)
SEPARACION_THT = 1.5         # de mas para un satelite con pads THT: tapa las 4 capas
                             # (TP6/TP7 pegados a U4/U5 dejaban sus pines sin salida)

CLEARANCE = 0.15
PISTA = 0.25
VIA_D, VIA_DRILL = 0.6, 0.3
# Rieles de hasta ~1.3 A: 0.5 mm en 1 oz exterior. Lo que pasa de ahi va por
# COBRE (abajo), no por pista ruteada.
POTENCIA = 0.5
# Las que llevan carga (>= ~0.3 A). +5V_AUX (telemetria + 100 mA del modulo 2),
# +24V_LDO (el MSP430) y el amortiguador del LC (C1_NEG/C2_NEG) van en Default:
# a 0.5 mm no entraban en los pines de 0.5 mm de paso de los INA226 y el ADS1115.
REDES_POTENCIA = (
    "+24V_RAW", "+24V_PROT", "+24V_SW", "+12V_RAW_RACK", "-12V_RAW_RACK",
    "+12V_FUSED_RACK", "+12V_RACK", "-12V_RACK", "+15V5_RAW", "+15V5_EFUSE", "+15V5_LC",
    "+15V5_FILT", "-15V5_RAW", "-15V5_LC", "-15V5_FILT", "+13V1", "-12V9", "+5V_RAW_RACK",
    "+5V_FUSED_RACK", "+5V_RACK", "+5V_RAW_DIG", "+5V_DIG", "OUT_U4", "OUT_U5",
    "OUT_U6", "OUT_U7", "OUTS_POS", "+12V_ULTRA", "-12V_ULTRA")
# Las masas solo hacen el tramo de pad a via: 0.4 mm cabe entre pads de paso fino.
MASAS = ("GND24", "GNDA", "GNDD")
PISTA_MASA = 0.4

# ref: (centro del courtyard x, y, rotacion). Coordenadas de placa, Y hacia abajo.
ANCLAS = {
    # Columna de convertidores: ENTRADAS a la izquierda (GND24), SALIDAS a la
    # derecha. Rot 90 en los TRACO pone su fila 1-2-6 a la izquierda.
    "PS1": (61.0, 18.5, 90), "PS4": (61.0, 46.5, 90), "PS5": (61.0, 74.5, 90),
    "PS3": (61.0, 96.5, 0), "PS2": (61.0, 121.0, 0),
    "NT1": (65.0, 105.0, 0),
    # Entrada y M5 (GND24). J1 -> Q2 -> U16 en linea recta a la altura de
    # PS5, con D1 colgando del cobre de +24V_RAW y U15 debajo de la puerta de Q2.
    "J1": (7.5, 75.0, 90), "D1": (14.5, 81.0, 270), "Q2": (21.0, 75.0, 0),
    "U15": (19.5, 81.0, 0), "U16": (34.0, 75.0, 0), "C14": (41.0, 121.0, 90),
    "U18": (20.0, 103.0, 0), "U17": (24.0, 120.0, 0), "SW1": (12.0, 134.0, 0),
    # C15 (10 uF/50 V, la Cin que pide el K78) con su pad 1 SOBRE el ramal de
    # PS3: suelta, Freerouting no llegaba a unirla al bus (ronda 1).
    "C15": (49.5, 100.08, 90),
    "J10": (34.0, 137.0, 90),
    # Rack (franja de arriba)
    "J3": (112.0, 7.0, 180), "SCR1": (86.0, 27.0, 0), "SCR2": (98.0, 27.0, 0),
    "SCR3": (128.0, 27.0, 0),
    # Cascada
    "U19": (82.0, 48.0, 90), "L2": (97.0, 48.0, 0), "C1": (97.0, 62.0, 0),
    "C3": (110.0, 46.0, 90), "U1": (127.0, 47.0, 0),
    "L3": (97.0, 79.0, 0), "C2": (97.0, 93.0, 0), "C4": (110.0, 79.0, 90),
    "U2": (127.0, 79.0, 0), "U20": (112.0, 63.0, 0),
    "RV2": (127.0, 36.0, 0), "RV3": (127.0, 92.0, 0),
    "U4": (147.0, 42.0, 0), "U5": (147.0, 53.0, 0), "U6": (147.0, 73.0, 0), "U7": (147.0, 84.0, 0),
    # Salidas y telemetria
    "J2": (194.0, 44.0, 90), "J7": (194.0, 60.0, 90), "J6": (194.0, 78.0, 90),
    "J5": (187.0, 93.0, 0), "U10": (170.0, 96.0, 0), "U9": (152.0, 106.5, 270),
    # Isla GNDD: PS2.4 -> F5 -> J9, con C29 y el crowbar SCR4 en el camino
    "J9": (98.0, 145.0, 0), "J8": (118.0, 144.0, 90), "SCR4": (90.0, 128.0, 0),
    "C29": (79.5, 125.5, 0), "F5": (80.0, 131.2, 0),
}

# Regiones de dominio (rectangulos x0, y0, x1, y1). Cada satelite tiene que
# caer ENTERO dentro de su dominio.
REGIONES = {
    "P": [(0.0, 0.0, 61.0, H), (61.0, 88.0, 64.0, 106.0), (61.0, 106.0, 63.5, H)],
    "D": [(66.0, 107.5, 160.0, H)],
    "A": [(61.0, 0.0, W, 88.0), (64.0, 88.0, W, 105.5), (162.0, 105.5, W, H)],
}

REDES_P = {"GND24", "+24V_RAW", "+24V_PROT", "+24V_SW", "+24V_LDO", "VCAP_U15", "GATE_Q2",
           "UVLO_U16", "OVP_U16", "DVDT_U16", "ILIM_U16", "SHDN_M5", "FLT_M5", "+3V3_MCU",
           "MCU_RST", "MCU_TEST", "SW_RESET", "LED_CTRL", "LED_ANODE"}
REDES_D = {"GNDD", "+5V_RAW_DIG", "+5V_DIG", "+3V3_DIG", "SDA_D", "SCL_D", "GATE_SCR4",
           "REF_CB4", "TLK_CB4", "QB_CB4", "QC_CB4", "LED7_A"}

# Cobre fijo: (red, capa, (x0, y0, x1, y1)). Cada rectangulo se cubre con
# tiras paralelas bloqueadas (tiras()). Las cotas salen de los pads de las
# ANCLAS de arriba, con >= 0.3 mm a cualquier pad de otra red: si se mueve
# un ancla de la entrada, de M1 o de U1/U2, hay que mover su cobre.
COBRE = [
    # +24V_RAW: J1.1 -> fuentes de Q2 (pads 1-3), con D1.1 encima
    ("+24V_RAW", "F.Cu", (5.6, 74.1, 15.0, 79.4)),
    ("+24V_RAW", "F.Cu", (13.0, 72.6, 18.55, 76.3)),
    # +24V_PROT: drenador de Q2 -> U16 pads 1-3 (IN)
    ("+24V_PROT", "F.Cu", (19.9, 71.4, 31.95, 73.5)),
    ("+24V_PROT", "F.Cu", (19.9, 71.4, 24.3, 77.1)),
    # U16.6 (IN_SYS) queda entre dos pines sin salida hacia el cobre de arriba:
    # se le lleva uno fino (ronda 1: Freerouting no lo unio)
    ("+24V_PROT", "F.Cu", (29.2, 72.9, 30.0, 75.6)),
    ("+24V_PROT", "F.Cu", (29.2, 75.13, 30.9, 75.53)),
    # +24V_SW: U16 pads 18-20 (OUT) -> bus vertical -> +Vin de los cinco modulos y C14
    ("+24V_SW", "F.Cu", (36.05, 71.4, 46.0, 73.5)),
    ("+24V_SW", "F.Cu", (38.5, 69.5, 46.0, 75.5)),
    ("+24V_SW", "F.Cu", (44.5, 19.7, 47.0, 125.6)),
    # Los ramales y el tronco se meten DENTRO del bus: dos rectangulos que
    # solo se tocan por el canto NO estan conectados para KiCad (la ronda 1
    # dejo el tronco de U16 sin llegar al bus por eso). revisar_cobre() exige
    # >= SOLAPE en las dos direcciones.
    ("+24V_SW", "F.Cu", (44.5, 19.75, 52.2, 22.25)),     # PS1.1
    ("+24V_SW", "F.Cu", (44.5, 47.75, 52.2, 50.25)),     # PS4.1
    ("+24V_SW", "F.Cu", (44.5, 75.75, 52.2, 78.25)),     # PS5.1
    ("+24V_SW", "F.Cu", (44.5, 100.3, 59.0, 102.8)),     # PS3.1-2
    ("+24V_SW", "F.Cu", (44.5, 122.3, 52.3, 124.8)),     # PS2.3
    ("+24V_SW", "F.Cu", (39.0, 122.8, 46.0, 125.6)),     # C14.1
    # +5V digital: PS2.4 -> F5 -> J9.1, pasando por C29.1 y SCR4.2
    ("+5V_RAW_DIG", "F.Cu", (69.7, 129.7, 79.25, 132.6)),
    ("+5V_RAW_DIG", "F.Cu", (74.9, 124.5, 78.6, 132.6)),
    ("+5V_DIG", "F.Cu", (80.75, 130.3, 97.6, 132.6)),
    ("+5V_DIG", "F.Cu", (89.0, 128.0, 91.0, 131.6)),
    ("+5V_DIG", "F.Cu", (95.2, 130.3, 97.6, 146.1)),
]
TIRA_MAX = 2.5               # ancho maximo de cada tira de COBRE
SOLAPE = 0.3                 # entre rectangulos de COBRE de la misma red que se unen

# Disipacion de U1 y U2 (~1.9 W cada uno en DD-PAK). La aleta de U1 es GNDA y
# baja al plano de In1 por vias; la de U2 es su entrada -15V5_FILT, que no
# tiene plano: cobre propio en F.Cu, In2 y B.Cu. Este cobre NO puede estar
# durante el ruteo: Freerouting no trata un vertido de una capa de senal como
# obstaculo (probado: con un vertido de GNDA en F.Cu metio 186 tramos de otras
# redes dentro), y como pistas solapadas lo hace oscilar (normalizeTraces se
# atasca en -15V5_FILT y la primera pasada no acaba). Asi que durante el ruteo
# esas areas son ZONAS PROHIBIDAS (RESERVAS, se exportan como keepout) y el
# cobre y las vias se ponen despues (cobre_termico()).
#   (red, capa, rectangulo de cobre)
TERMICO = [
    ("GNDA", "F.Cu", (125.4, 39.6, 142.5, 54.4)),
    ("-15V5_FILT", "F.Cu", (125.4, 72.0, 142.5, 86.4)),
    ("-15V5_FILT", "In2.Cu", (124.5, 71.0, 142.5, 87.4)),
    ("-15V5_FILT", "B.Cu", (124.5, 71.0, 142.5, 87.4)),
]
# Vias termicas a la derecha de la aleta (sin via en el pad: el estano se iria
# por ellas al refluir). Atraviesan todas las capas: su rectangulo se reserva
# en F.Cu, In2 y B.Cu.
VIAS_TERMICAS = [("U1", "GNDA", (135.6, 39.6, 142.5, 54.4)),
                 ("U2", "-15V5_FILT", (135.6, 72.0, 142.5, 86.4))]
PASO_TERMICO = 1.6
RESERVAS = ([(rect, ("F.Cu", "In2.Cu", "B.Cu")) for _ref, _red, rect in VIAS_TERMICAS]
            + [(rect, (capa,)) for red, capa, rect in TERMICO if capa != "F.Cu"])

CAPAS = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}


# Las reglas (clases de red, holguras) viven en el .kicad_pro, no en la placa.
# Una placa cargada de una ruta SIN su .kicad_pro trae las de fabrica (0.2 mm),
# y SaveBoard reescribe el proyecto de la ruta destino con ellas: asi una ronda
# de Freerouting exporto el DSN a 0.2 mm y el .kicad_pro del repo quedo con la
# clase Default de fabrica. guardar() repone el proyecto bueno junto a CADA
# placa que escribe (el del repo y las copias temporales).
_PROYECTO: list[str] = []


def guardar(ruta: str, board) -> None:
    pcbnew.SaveBoard(ruta, board)
    if _PROYECTO:
        with open(ruta[:-len(".kicad_pcb")] + ".kicad_pro", "w", encoding="utf-8") as fh:
            fh.write(_PROYECTO[0])


def mm(v: float) -> int:
    return int(round(v * 1e6))


def quitar(board, item) -> None:
    """board.Remove() sin que Python destruya despues el objeto quitado.

    El Remove de pcbnew 10 le pasa a Python la propiedad del objeto
    (thisown=1). Al recogerlo, SWIG no encuentra su destructor ("detected a
    memory leak of type 'ZONE *', no destructor found") y lo que se crea
    despues en el mismo proceso sale corrupto: Outline() de una zona nueva
    devolvia un SwigPyObject pelado ("has no attribute 'NewOutline'"). Sin
    dueno, el objeto quitado se pierde al salir (unos KB) y nada mas.
    """
    board.Remove(item)
    item.thisown = 0


# ---------------------------------------------------------------- netlist
def leer_netlist() -> tuple[dict, dict]:
    """{ref: {footprint, value, tstamp}}, {(ref, pad): red}."""
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()
    comps: dict[str, dict] = {}
    for m in re.finditer(r'\(comp\s+\(ref\s+"([^"]+)"\)\s*\(value\s+"([^"]*)"\)\s*'
                         r'\(footprint\s+"([^"]*)"\)', txt):
        cola = txt[m.end():m.end() + 6000]
        # hasta el componente siguiente, o hasta (libparts si es el ultimo: alli
        # cada pieza de biblioteca trae su propio campo Reference ("TP"...)
        siguiente = re.search(r"\(comp\s|\(libparts|\(nets", cola)
        cola = cola[:siguiente.start()] if siguiente else cola
        ts = re.search(r'\(sheetpath[^)]*\)[^)]*\)\s*\)\s*\(tstamps\s+"([^"]+)"\)', cola, re.S)
        # los campos propios del simbolo (LCSC, MPN): la paridad del DRC exige
        # que la huella los lleve tambien
        campos = {k: v for k, v in re.findall(r'\(field\s+\(name\s+"([^"]+)"\)\s*"([^"]*)"\)', cola)
                  if k not in ("Reference", "Value", "Footprint", "Datasheet", "Description")}
        comps[m.group(1)] = {"value": m.group(2), "footprint": m.group(3),
                             "tstamp": ts.group(1) if ts else "", "campos": campos,
                             "sin_bom": '(name "exclude_from_bom")' in cola}
    redes: dict[tuple[str, str], str] = {}
    cab = list(re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)', txt))
    for i, m in enumerate(cab):
        fin = cab[i + 1].start() if i + 1 < len(cab) else len(txt)
        nombre = m.group(1).lstrip("/")
        for ref, pin in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', txt[m.end():fin]):
            redes[(ref, pin)] = nombre
    assert comps and redes, "netlist vacio: corre build_schematic.py"
    return comps, redes


def dominio_de(ref: str, redes: dict) -> str:
    propias = {n for (r, _p), n in redes.items() if r == ref}
    if propias & REDES_D:
        return "D"
    if propias & REDES_P:
        return "P"
    return "A"


# ---------------------------------------------------------------- reglas
def escribir_reglas() -> None:
    """Clases de red y reglas en el .kicad_pro, que es donde KiCad las lee."""
    with open(PRO, encoding="utf-8") as fh:
        pro = json.load(fh)
    ns = pro["net_settings"]
    base = dict(ns["classes"][0])
    base.update({"name": "Default", "clearance": CLEARANCE, "track_width": PISTA,
                 "via_diameter": VIA_D, "via_drill": VIA_DRILL})
    pot = dict(base)
    pot.update({"name": "Potencia", "track_width": POTENCIA, "via_diameter": 0.8,
                "via_drill": 0.4, "priority": 0})
    masa = dict(base)
    masa.update({"name": "Masa", "track_width": PISTA_MASA, "priority": 1})
    ns["classes"] = [base, pot, masa]
    ns["netclass_patterns"] = (
        [{"netclass": "Potencia", "pattern": re.escape(n).replace("\\-", "-")} for n in REDES_POTENCIA]
        + [{"netclass": "Masa", "pattern": n} for n in MASAS])
    ns["netclass_assignments"] = None
    ds = pro["board"]["design_settings"]
    ds["rules"].update({"min_clearance": CLEARANCE, "min_track_width": 0.15, "min_via_diameter": 0.6,
                        # 0.2: las vias termicas de las huellas DFN de KiCad son de 0.2 mm
                        # y JLC las taladra en 4 capas.
                        "min_through_hole_diameter": 0.2, "min_copper_edge_clearance": 0.5,
                        "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25})
    with open(PRO, "w", encoding="utf-8") as fh:
        json.dump(pro, fh, indent=2)
        fh.write("\n")
    with open(PRO, encoding="utf-8") as fh:
        _PROYECTO[:] = [fh.read()]


# ------------------------------------------------------------- colocacion
def cargar_huella(fpid: str) -> pcbnew.FOOTPRINT:
    lib, _, nombre = fpid.partition(":")
    base = os.path.join(DIR, "sam17.pretty") if lib == "sam17" else os.path.join(STOCK, f"{lib}.pretty")
    fp = pcbnew.FootprintLoad(base, nombre)
    assert fp, f"no se pudo cargar {fpid}"
    fp.SetFPID(pcbnew.LIB_ID(lib, nombre))
    return fp


def caja_cy(fp: pcbnew.FOOTPRINT) -> tuple[float, float, float, float]:
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False)
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6)


def mover_a(fp: pcbnew.FOOTPRINT, cx: float, cy: float, rot: float) -> None:
    """Rota y pone el CENTRO DEL COURTYARD en (cx, cy)."""
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    x0, y0, x1, y1 = caja_cy(fp)
    fp.SetPosition(pcbnew.VECTOR2I(mm(cx - (x0 + x1) / 2), mm(cy - (y0 + y1) / 2)))


def solapa(a, b, sep: float) -> bool:
    return not (a[2] + sep <= b[0] or b[2] + sep <= a[0] or a[3] + sep <= b[1] or b[3] + sep <= a[1])


def dentro_de(caja, rects) -> bool:
    """La caja entera dentro de la UNION de rectangulos (muestreo de bordes)."""
    x0, y0, x1, y1 = caja
    pasos = 6
    for i in range(pasos + 1):
        for j in range(pasos + 1):
            px, py = x0 + (x1 - x0) * i / pasos, y0 + (y1 - y0) * j / pasos
            if not any(r[0] <= px <= r[2] and r[1] <= py <= r[3] for r in rects):
                return False
    return True


def colocar_satelites(board, huellas: dict, redes: dict, ocupado: list) -> None:
    pendientes = [r for r in huellas if r not in ANCLAS]
    colocadas = set(ANCLAS)
    por_red: dict[str, list] = {}
    for (r, p), n in redes.items():
        por_red.setdefault(n, []).append((r, p))
    # Las redes enormes no dicen nada de donde va una pieza, y el bus I2C
    # tampoco: con el, los INA226 caian en el centro del bus -- entre los LDO
    # en paralelo (U12 entre U6 y U7) -- y no junto a su shunt.
    ignorar = ({n for n, nodos in por_red.items() if len(nodos) > 12} | set(MASAS)
               | {"SDA_A", "SCL_A", "SDA_D", "SCL_D"})

    def vecinos(ref: str) -> list[tuple[float, float]]:
        pts = []
        for pad in huellas[ref].Pads():
            n = redes.get((ref, pad.GetNumber()))
            if not n or n in ignorar:
                continue
            for r2, p2 in por_red[n]:
                if r2 != ref and r2 in colocadas:
                    for pd in huellas[r2].Pads():
                        if pd.GetNumber() == p2:
                            pts.append((pd.GetPosition().x / 1e6, pd.GetPosition().y / 1e6))
        return pts

    while pendientes:
        # primero la que mas conexiones tiene con lo ya colocado
        pendientes.sort(key=lambda r: -len(vecinos(r)))
        ref = pendientes.pop(0)
        fp = huellas[ref]
        dom = dominio_de(ref, redes)
        pts = vecinos(ref)
        if pts:
            tx = sum(p[0] for p in pts) / len(pts)
            ty = sum(p[1] for p in pts) / len(pts)
        else:
            r0 = REGIONES[dom][0]
            tx, ty = (r0[0] + r0[2]) / 2, (r0[1] + r0[3]) / 2
        sep = SEPARACION + (SEPARACION_THT if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                                                  for p in fp.Pads()) else 0.0)
        hecho = False
        for radio in [x * 0.5 for x in range(0, 200)]:
            n_ang = max(1, int(2 * math.pi * radio / 0.8))
            for k in range(n_ang):
                a = 2 * math.pi * k / n_ang
                cx, cy = tx + radio * math.cos(a), ty + radio * math.sin(a)
                for rot in (0, 90):
                    mover_a(fp, round(cx * 4) / 4, round(cy * 4) / 4, rot)
                    caja = caja_cy(fp)
                    if caja[0] < MARGEN or caja[1] < MARGEN or caja[2] > W - MARGEN or caja[3] > H - MARGEN:
                        continue
                    if not dentro_de(caja, REGIONES[dom]):
                        continue
                    if any(solapa(caja, o, sep) for o in ocupado):
                        continue
                    ocupado.append(caja)
                    colocadas.add(ref)
                    hecho = True
                    break
                if hecho:
                    break
            if hecho:
                break
        assert hecho, f"no encuentro sitio para {ref} (dominio {dom}) cerca de ({tx:.1f}, {ty:.1f})"


def colocar(board, comps: dict, redes: dict) -> dict:
    huellas: dict[str, pcbnew.FOOTPRINT] = {}
    netinfo: dict[str, pcbnew.NETINFO_ITEM] = {}
    for nombre in sorted(set(redes.values())):
        ni = pcbnew.NETINFO_ITEM(board, nombre)
        board.Add(ni)
        netinfo[nombre] = ni
    for ref, c in sorted(comps.items()):
        fp = cargar_huella(c["footprint"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.Value().SetVisible(False)
        if c["tstamp"]:
            fp.SetPath(pcbnew.KIID_PATH(f"/{c['tstamp']}"))
            fp.SetSheetname("/")
            fp.SetSheetfile(SCH_NOMBRE)
        board.Add(fp)
        for pad in fp.Pads():
            n = redes.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])
        huellas[ref] = fp
    ocupado = []
    for ref, (cx, cy, rot) in ANCLAS.items():
        mover_a(huellas[ref], cx, cy, rot)
        ocupado.append(caja_cy(huellas[ref]))
    for ref, x, y in MONTAJE:
        ocupado.append((x - 3.5, y - 3.5, x + 3.5, y + 3.5))
    # El cobre de potencia de la cara de arriba es terreno vedado: un satelite
    # encima quedaria con sus pads dentro del cobre de otra red.
    ocupado.extend(rect for _red, capa, rect in COBRE if capa == "F.Cu")
    # Y el cobre termico de U1/U2 con sus reservas: un satelite ahi dentro
    # quedaria en una zona sin pistas ni vias, imposible de rutear.
    ocupado.extend(rect for _red, _capa, rect in TERMICO)
    ocupado.extend(rect for rect, _capas in RESERVAS)
    colocar_satelites(board, huellas, redes, ocupado)
    for ref, x, y in MONTAJE:
        fp = cargar_huella(f"MountingHole:MountingHole_{MONTAJE_D}mm_M3")
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        board.Add(fp)
    sincronizar(board, comps)
    return huellas


def sincronizar(board, comps: dict) -> None:
    """Lo que la paridad del DRC compara entre simbolo y huella, copiado del netlist.

    Sin esto el DRC con --schematic-parity daba 414 diferencias: los campos
    del simbolo (LCSC, MPN) que la huella no llevaba, los TP y la NetTie que
    en la biblioteca de KiCad vienen "fuera de BOM" y en el esquema no, y los
    taladros de montaje, que no tienen simbolo y hay que marcar "solo placa".
    """
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in dict((r, 0) for r, _x, _y in MONTAJE):
            fp.SetBoardOnly(True)
            continue
        c = comps[ref]
        for nombre, valor in c["campos"].items():
            fp.SetField(nombre, valor)
            campo = fp.GetField(nombre)
            campo.SetVisible(False)
            campo.SetLayer(pcbnew.F_Fab)
        fp.SetExcludedFromBOM(c["sin_bom"])


# ------------------------------------------------------------------ cobre
def contorno(board) -> None:
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)


# Los planos de In1, UN poligono por dominio. El hueco solo existe en las
# fronteras entre dominios: si cada rectangulo de REGIONES se encogiera por
# sus cuatro lados, los trozos de una misma masa quedarian separados entre si
# y el relleno los tiraria como islas (primera ronda: 50 sin conectar, casi
# todos ramales de GNDA que no llegaban a su plano). Los mismos poligonos se
# vierten al final en F.Cu y B.Cu (tras_el_ruteo()).
PLANOS_IN1 = {
    "GND24": [(0.5, 0.5), (60.5, 0.5), (60.5, 88.0), (63.5, 88.0), (63.5, 149.5), (0.5, 149.5)],
    "GNDA": [(61.5, 0.5), (199.5, 0.5), (199.5, 149.5), (163.0, 149.5), (163.0, 105.5),
             (64.5, 105.5), (64.5, 87.0), (61.5, 87.0)],
    "GNDD": [(67.0, 107.5), (161.0, 107.5), (161.0, 149.0), (67.0, 149.0)],
}


def zona(board, red: str, capa: int, poligono: list, prioridad: int = 0,
         conexion=pcbnew.ZONE_CONNECTION_THERMAL) -> pcbnew.ZONE:
    z = pcbnew.ZONE(board)
    z.SetLayer(capa)
    z.SetNet(board.FindNet(red))
    o = z.Outline()
    o.NewOutline()
    for x, y in poligono:
        o.Append(pcbnew.VECTOR2I(mm(x), mm(y)))
    z.SetLocalClearance(mm(0.3))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(conexion)
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetAssignedPriority(prioridad)
    board.Add(z)
    return z


def tiras(rect: tuple) -> list[tuple[tuple[float, float], tuple[float, float], float]]:
    """Cubre un rectangulo con pistas paralelas de <= TIRA_MAX que se solapan.

    Una sola pista del alto del rectangulo dejaria sin cobre las esquinas (los
    extremos de una pista son redondos) y un tramo de 14 mm de ancho es un
    disparate para cualquier herramienta. Tiras estrechas solapadas cubren el
    rectangulo salvo un radio de TIRA_MAX/2 en cada esquina.

    Y dos tiras de traves, una en cada punta: sin ellas el extremo de cada
    tira paralela cae en el aire (las vecinas solo la tocan por el canto) y el
    DRC lo cuenta como pista colgando. Con ellas cada extremo cae dentro de
    otra tira de la misma red.
    """
    x0, y0, x1, y1 = rect
    horizontal = (x1 - x0) >= (y1 - y0)
    corto = (y1 - y0) if horizontal else (x1 - x0)
    n = max(1, math.ceil(corto / TIRA_MAX))
    ancho = min(corto, corto / n + 0.1)
    a, b = (x0 if horizontal else y0) + ancho / 2, (x1 if horizontal else y1) - ancho / 2
    if b < a:
        a = b = (a + b) / 2
    c0, c1 = (y0 if horizontal else x0) + ancho / 2, (y1 if horizontal else x1) - ancho / 2
    out = []
    for i in range(n):
        c = c0 + i * (c1 - c0) / max(1, n - 1)
        out.append(((a, c), (b, c), ancho) if horizontal else ((c, a), (c, b), ancho))
    if n > 1:
        for p in (a, b):
            out.append(((p, c0), (p, c1), ancho) if horizontal else ((c0, p), (c1, p), ancho))
    return out


def revisar_cobre() -> None:
    """Los rectangulos de COBRE de cada red forman UNA pieza, solapados de verdad."""
    for red in {r for r, _c, _x in COBRE}:
        rects = [x for r, _c, x in COBRE if r == red]
        unidos = {0}
        cambio = True
        while cambio:
            cambio = False
            for i, a in enumerate(rects):
                if i in unidos:
                    continue
                if any(min(a[2], rects[j][2]) - max(a[0], rects[j][0]) >= SOLAPE
                       and min(a[3], rects[j][3]) - max(a[1], rects[j][1]) >= SOLAPE for j in unidos):
                    unidos.add(i)
                    cambio = True
        sueltos = [rects[i] for i in range(len(rects)) if i not in unidos]
        assert not sueltos, f"COBRE de {red}: {sueltos} no se solapa >= {SOLAPE} mm con el resto"


def puentes(board) -> list[str]:
    """Une con una pista fija en B.Cu los pads THT de una misma pieza y red.

    El pulsador SW1 tiene dos patas por contacto y los trimmers RV2/RV3 van
    como reostato (cursor unido a un extremo): son la misma red DENTRO de la
    pieza y KiCad exige cobre entre ellos. Freerouting los dejo sin unir en la
    ronda 1. Se hace a mano, recto y en B.Cu, si no pasa cerca de otro pad.
    """
    hechos = []
    pads_todos = [_PadGeo(p) for fp in board.GetFootprints() for p in fp.Pads()
                  if p.GetNumber() or p.GetDrillSizeX() > 0]
    for fp in board.GetFootprints():
        por_red: dict[str, list] = {}
        for p in fp.Pads():
            red = p.GetNetname()
            # >= 0.5 mm de taladro: las vias termicas de un pad expuesto (0.2-0.3)
            # ya estan unidas por el propio pad
            if (p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetDrillSizeX() >= mm(0.5)
                    and red and red not in MASAS and not red.startswith("unconnected-")):
                por_red.setdefault(red, []).append(p)
        for red, ps in por_red.items():
            for a, b in zip(ps, ps[1:]):
                pa = (a.GetPosition().x / 1e6, a.GetPosition().y / 1e6)
                pb = (b.GetPosition().x / 1e6, b.GetPosition().y / 1e6)
                if math.hypot(pb[0] - pa[0], pb[1] - pa[1]) > 8:
                    continue
                if any(q.red != red and q.dist_seg(pa, pb) < POTENCIA / 2 + CLEARANCE + 0.05
                       for q in pads_todos):
                    continue
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(pa[0]), mm(pa[1])))
                t.SetEnd(pcbnew.VECTOR2I(mm(pb[0]), mm(pb[1])))
                t.SetWidth(mm(POTENCIA))
                t.SetLayer(pcbnew.B_Cu)
                t.SetNet(board.FindNet(red))
                t.SetLocked(True)
                board.Add(t)
                hechos.append(f"{fp.GetReference()}:{red}")
    return hechos


def cobre_fijo(board) -> None:
    """Pone el COBRE de potencia como pistas bloqueadas."""
    for red, capa, rect in COBRE:
        for (xa, ya), (xb, yb), ancho in tiras(rect):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(xa), mm(ya)))
            t.SetEnd(pcbnew.VECTOR2I(mm(xb), mm(yb)))
            t.SetWidth(mm(ancho))
            t.SetLayer(CAPAS[capa])
            t.SetNet(board.FindNet(red))
            t.SetLocked(True)
            board.Add(t)


def _dist_seg(p, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


class _PadGeo:
    """Un pad como rectangulo girado (o circulo), en mm, para medir holguras."""

    def __init__(self, pad):
        self.red = pad.GetNetname()
        self.x, self.y = pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6
        s = pad.GetSize(pcbnew.F_Cu)
        self.w, self.h = s.x / 1e6, s.y / 1e6
        self.ang = math.radians(pad.GetOrientationDegrees())
        self.redondo = pad.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE
        self.taladro = pad.GetDrillSizeX() / 2e6
        self.smd = pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
        self.ref = pad.GetParentFootprint().GetReference()

    def dist(self, x: float, y: float) -> float:
        """Distancia del punto al borde del pad (0 dentro)."""
        if self.redondo:
            return max(0.0, math.hypot(x - self.x, y - self.y) - self.w / 2)
        dx, dy = x - self.x, y - self.y
        lx = dx * math.cos(self.ang) - dy * math.sin(self.ang)
        ly = dx * math.sin(self.ang) + dy * math.cos(self.ang)
        ex, ey = max(0.0, abs(lx) - self.w / 2), max(0.0, abs(ly) - self.h / 2)
        return math.hypot(ex, ey)

    def punto_mas_cercano(self, x: float, y: float) -> tuple[float, float]:
        """Punto del pad mas cercano a (x, y), 0.2 mm hacia dentro."""
        dx, dy = x - self.x, y - self.y
        c, s = math.cos(self.ang), math.sin(self.ang)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        lx = max(-self.w / 2 + 0.2, min(self.w / 2 - 0.2, lx))
        ly = max(-self.h / 2 + 0.2, min(self.h / 2 - 0.2, ly))
        return (self.x + lx * c + ly * s, self.y - lx * s + ly * c)

    def dist_seg(self, a, b) -> float:
        """Distancia (aprox. por muestreo) de un tramo recto al borde del pad."""
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.05))
        return min(self.dist(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
                   for i in range(n + 1))


def _dentro_poligono(x: float, y: float, poly: list) -> bool:
    f = False
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            f = not f
    return f


def coser_masas(board) -> tuple[int, list[str]]:
    """Una via bloqueada, con su tramo, por cada pad SMD de masa. Antes de rutear.

    Los pads SMD de masa solo tocan su plano de In1 a traves de una via. En
    la primera ronda con Freerouting quedaron 70 de GNDA y 21 de GND24 sin
    ella: su fanout no encontraba sitio entre tanto 0805 y luego el ruteo
    tampoco. Aqui se busca, para cada pad, el hueco mas cercano donde cabe
    una via con todas las holguras (pads, taladros, cobre fijo, reservas y
    dentro del poligono de SU dominio en In1), y se deja bloqueada: para
    Freerouting ese pad ya esta conectado y solo le quedan las senales.

    Nunca encima de un pad (via en pad = estano que se va por el taladro) y
    primero fuera del courtyard de otras piezas. Devuelve (vias puestas,
    pads que no la tienen).
    """
    pads = [_PadGeo(p) for fp in board.GetFootprints() for p in fp.Pads()
            if p.GetNumber() or p.GetDrillSizeX() > 0]
    cajas = {fp.GetReference(): caja_cy(fp) for fp in board.GetFootprints()}
    centros = {fp.GetReference(): ((caja_cy(fp)[0] + caja_cy(fp)[2]) / 2,
                                   (caja_cy(fp)[1] + caja_cy(fp)[3]) / 2) for fp in board.GetFootprints()}
    fijas = [(t.GetNetname(), (t.GetStart().x / 1e6, t.GetStart().y / 1e6),
              (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6), t.GetWidth() / 2e6)
             for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    taladros = [(p.x, p.y, p.taladro, p.red) for p in pads if p.taladro > 0]
    taladros += [(x, y, MONTAJE_D / 2, "") for _r, x, y in MONTAJE]
    rv, rd, hol = VIA_D / 2, VIA_DRILL / 2, CLEARANCE + 0.05
    puestas, sin_via = 0, []
    objetivos = [p for p in pads if p.smd and p.red in MASAS]
    for pad in objetivos:
        if any(q.ref == pad.ref and q.red == pad.red and q.taladro > 0 and pad.dist(q.x, q.y) == 0
               for q in pads):
            continue                      # EP con sus vias termicas en la huella
        cerca = [q for q in pads if abs(q.x - pad.x) < 8 and abs(q.y - pad.y) < 8]
        cerca_fijas = [f for f in fijas if _dist_seg((pad.x, pad.y), f[1], f[2]) < 8]
        cerca_tal = [t for t in taladros if abs(t[0] - pad.x) < 8 and abs(t[1] - pad.y) < 8]
        stub = min(PISTA_MASA, pad.w, pad.h)
        # Si su propio CI tiene un pad expuesto de la MISMA masa con vias
        # termicas (TPS26631, LT3045/LT3094), el pin se une a el con un
        # tramo recto hacia dentro: es lo que pide la hoja y no gasta sitio.
        ep = _pad_expuesto(pad, pads)
        if ep is not None:
            destino = ep.punto_mas_cercano(pad.x, pad.y)
            if not any(q.red != pad.red and q.dist_seg((pad.x, pad.y), destino) < stub / 2 + hol
                       for q in cerca):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(pad.x), mm(pad.y)))
                t.SetEnd(pcbnew.VECTOR2I(mm(destino[0]), mm(destino[1])))
                t.SetWidth(mm(stub))
                t.SetLayer(pcbnew.F_Cu)
                t.SetNet(board.FindNet(pad.red))
                t.SetLocked(True)
                board.Add(t)
                fijas.append((pad.red, (pad.x, pad.y), destino, stub / 2))
                continue
        fx, fy = centros[pad.ref]
        hacia = math.atan2(pad.y - fy, pad.x - fx) if (pad.x, pad.y) != (fx, fy) else 0.0
        # Rejilla polar alrededor del pad, empezando hacia fuera del
        # encapsulado, MAS las cuatro direcciones de los ejes del propio pad:
        # un pin de paso fino solo escapa recto a lo largo de su eje (con 8.8
        # grados de inclinacion el tramo ya roza al vecino, que fue lo que
        # dejo sin via los GND de U6/U7 a 0.45 mm de paso).
        angulos = [(hacia + math.pi * 2 * k / 24, min(k, 24 - k)) for k in range(24)]
        for m in range(4):
            a = -pad.ang + m * math.pi / 2
            dif = abs((a - hacia + math.pi) % (2 * math.pi) - math.pi)
            angulos.append((a, dif / (math.pi / 12) - 1))
        # Pin de paso fino (otro pad a < 0.6 mm): la via justo delante tapa la
        # salida de los dos vecinos (U6/U7: SET_NEG y OUTS sin rutear). Ahi la
        # via va RECTA por el eje del pin y a mas de 1 mm de su punta, y los
        # vecinos salen en diagonal antes de llegar a ella.
        fino = any(q.red != pad.red and q.ref == pad.ref and q.dist(pad.x, pad.y) < 0.6 for q in cerca)
        r_min = 4
        if fino:
            angulos = [min(angulos[24:], key=lambda t: t[1])]   # el eje que mas mira afuera
            r_min = 10
        candidatos = []
        for r10 in range(r_min, 40):
            for a, desvio in angulos:
                r = r10 * 0.1 + abs(pad.w / 2 * math.cos(a + pad.ang)) + abs(pad.h / 2 * math.sin(a + pad.ang))
                candidatos.append((r + 0.15 * desvio, pad.x + r * math.cos(a), pad.y + r * math.sin(a)))
        candidatos.sort()
        hecho = False
        for pasada in (0, 1):
            for _c, x, y in candidatos:
                if pasada == 0 and any(ref != pad.ref and c[0] <= x <= c[2] and c[1] <= y <= c[3]
                                       for ref, c in cajas.items()):
                    continue
                if not _dentro_poligono(x, y, PLANOS_IN1[pad.red]) or any(
                        _dist_seg((x, y), a, b) < 0.8 for a, b in zip(
                            PLANOS_IN1[pad.red], PLANOS_IN1[pad.red][1:] + PLANOS_IN1[pad.red][:1])):
                    continue
                if any(x0 - rv - 0.3 <= x <= x1 + rv + 0.3 and y0 - rv - 0.3 <= y <= y1 + rv + 0.3
                       for (x0, y0, x1, y1), _c in RESERVAS):
                    continue
                if x < 1.5 or y < 1.5 or x > W - 1.5 or y > H - 1.5:
                    continue
                if any(q.dist(x, y) < rv + (hol if q.red != pad.red else 0.1) for q in cerca):
                    continue
                if any(math.hypot(tx - x, ty - y) < tr + rd + 0.3 for tx, ty, tr, _n in cerca_tal):
                    continue
                if any(n != pad.red and _dist_seg((x, y), a, b) < rv + w + hol
                       for n, a, b, w in cerca_fijas):
                    continue
                # el tramo empieza DENTRO del pad, donde ya tiene a sus vecinos a
                # la distancia de la huella: aqui manda la regla, no el colchon
                if any(q.red != pad.red and q.dist_seg((pad.x, pad.y), (x, y)) < stub / 2 + CLEARANCE + 0.01
                       for q in cerca):
                    continue
                if any(n != pad.red and dist_tramos((pad.x, pad.y), (x, y), a, b) < stub / 2 + w + hol
                       for n, a, b, w in cerca_fijas):
                    continue
                if any("F.Cu" in capas and _cruza_rect((pad.x, pad.y), (x, y), rect, stub / 2 + 0.1)
                       for rect, capas in RESERVAS):
                    continue
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                v.SetWidth(mm(VIA_D))
                v.SetDrill(mm(VIA_DRILL))
                v.SetNet(board.FindNet(pad.red))
                v.SetLocked(True)
                board.Add(v)
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(pad.x), mm(pad.y)))
                t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
                t.SetWidth(mm(stub))
                t.SetLayer(pcbnew.F_Cu)
                t.SetNet(board.FindNet(pad.red))
                t.SetLocked(True)
                board.Add(t)
                taladros.append((x, y, rd, pad.red))
                fijas.append((pad.red, (pad.x, pad.y), (x, y), stub / 2))
                pads.append(_ViaGeo(x, y, rv, pad.red))
                puestas += 1
                hecho = True
                break
            if hecho:
                break
        if not hecho:
            sin_via.append(f"{pad.ref}:{pad.red}")
    return puestas, sin_via


def _pad_expuesto(pad: _PadGeo, pads: list):
    """El pad expuesto (con vias termicas en la huella) del mismo CI y red, o None."""
    for q in pads:
        if (q.ref == pad.ref and q.red == pad.red and q is not pad and q.smd
                and q.w * q.h > 4 * pad.w * pad.h
                and any(t.ref == pad.ref and t.taladro > 0 and q.dist(t.x, t.y) == 0 for t in pads)):
            return q
    return None


class _ViaGeo(_PadGeo):
    """Una via ya puesta, para que las siguientes guarden distancia."""

    def __init__(self, x: float, y: float, r: float, red: str):  # noqa: D107 -- no llama al padre
        self.red, self.x, self.y, self.w, self.h = red, x, y, 2 * r, 2 * r
        self.ang, self.redondo, self.taladro, self.smd, self.ref = 0.0, True, VIA_DRILL / 2, False, ""


def _cruza_rect(a, b, rect, margen: float) -> bool:
    """El tramo a-b pasa a menos de `margen` del rectangulo (o por dentro)."""
    x0, y0, x1, y1 = rect[0] - margen, rect[1] - margen, rect[2] + margen, rect[3] + margen
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.05))
    return any(x0 <= a[0] + (b[0] - a[0]) * i / n <= x1 and y0 <= a[1] + (b[1] - a[1]) * i / n <= y1
               for i in range(n + 1))


def dist_tramos(a, b, c, d) -> float:
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0:
        return 0.0
    return min(_dist_seg(a, c, d), _dist_seg(b, c, d), _dist_seg(c, a, b), _dist_seg(d, a, b))


def _rectangulo(x0: float, y0: float, x1: float, y1: float) -> list:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def reservas(board) -> None:
    """Zonas prohibidas (sin pistas ni vias) donde ira el cobre termico."""
    for (x0, y0, x1, y1), capas in RESERVAS:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetDoNotAllowZoneFills(False)
        ls = pcbnew.LSET()
        for c in capas:
            ls.AddLayer(CAPAS[c])
        z.SetLayerSet(ls)
        o = z.Outline()
        o.NewOutline()
        for x, y in _rectangulo(x0, y0, x1, y1):
            o.Append(pcbnew.VECTOR2I(mm(x), mm(y)))
        board.Add(z)


def cobre_termico(board) -> int:
    """Tras el ruteo: quita las RESERVAS y pone el cobre TERMICO y sus vias.

    La aleta se suelda MACIZA a su cobre (sin radios de alivio termico): aqui
    el cobre esta para sacar calor, no para facilitar la soldadura. Devuelve
    cuantas vias termicas puso.
    """
    for z in [z for z in board.Zones() if z.GetIsRuleArea()]:
        quitar(board, z)
    for red, capa, (x0, y0, x1, y1) in TERMICO:
        zona(board, red, CAPAS[capa], _rectangulo(x0, y0, x1, y1), prioridad=2,
             conexion=pcbnew.ZONE_CONNECTION_FULL)
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    n = 0
    for ref, red, (x0, y0, x1, y1) in VIAS_TERMICAS:
        aleta = max(board.FindFootprintByReference(ref).Pads(),
                    key=lambda p: p.GetSize(pcbnew.F_Cu).x * p.GetSize(pcbnew.F_Cu).y)
        assert aleta.GetNetname() == red, f"la aleta de {ref} no es {red}"
        aleta.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        y = y0 + 0.8
        while y <= y1 - 0.8 + 1e-9:
            x = x0 + 0.8
            while x <= x1 - 0.8 + 1e-9:
                if not any(_cerca_de_pad(p, x, y, VIA_D / 2 + 0.35) for p in pads):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                    v.SetWidth(mm(VIA_D))
                    v.SetDrill(mm(VIA_DRILL))
                    v.SetNet(board.FindNet(red))
                    v.SetLocked(True)
                    board.Add(v)
                    n += 1
                x += PASO_TERMICO
            y += PASO_TERMICO
    return n


def _cerca_de_pad(pad, x: float, y: float, margen: float) -> bool:
    bb = pad.GetBoundingBox()
    return (bb.GetLeft() / 1e6 - margen <= x <= bb.GetRight() / 1e6 + margen
            and bb.GetTop() / 1e6 - margen <= y <= bb.GetBottom() / 1e6 + margen)


def zonas(board) -> None:
    for red, poligono in PLANOS_IN1.items():
        zona(board, red, pcbnew.In1_Cu, poligono)


def textos(board) -> None:
    """Rotulos de placa en la serigrafia de ABAJO, que esta vacia (todo se
    monta arriba): asi no pisan ni una referencia ni un pad de la cara de
    componentes."""
    for texto, x, y, t in (("SAM17 FUENTE v5-B  (ladrillo 24 V)", 150.0, 146.5, 1.5),
                           ("GND24", 30.0, 3.0, 1.2), ("GNDA", 150.0, 3.0, 1.2),
                           ("GNDD (M1)", 120.0, 112.0, 1.2)):
        tx = pcbnew.PCB_TEXT(board)
        tx.SetText(texto)
        tx.SetLayer(pcbnew.B_SilkS)
        tx.SetMirrored(True)
        tx.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        tx.SetTextSize(pcbnew.VECTOR2I(mm(t), mm(t)))
        tx.SetTextThickness(mm(t * 0.15))
        board.Add(tx)


# Referencias: 0.8 mm de alto y 0.15 de trazo, lo minimo que JLC imprime
# legible. Primero las que se buscan con la placa en la mano (puntos de
# prueba, conectores, CI); las pasivas de las zonas densas que no caben sin
# pisar un pad o otra serigrafia pasan a F.Fab (dibujo de montaje).
REF_ALTO, REF_TRAZO = 0.8, 0.15
REF_ORDEN = ("TP", "J", "PS", "U", "SCR", "SW", "RV", "Q", "F", "L", "D")


def _caja(bb, margen: float = 0.0) -> tuple:
    return (bb.GetLeft() / 1e6 - margen, bb.GetTop() / 1e6 - margen,
            bb.GetRight() / 1e6 + margen, bb.GetBottom() / 1e6 + margen)


def colocar_referencias(board) -> list[str]:
    """Pone cada referencia junto a su pieza sin pisar pads ni serigrafia.

    Prueba arriba, abajo, izquierda y derecha del courtyard (y corridas de
    1.5 y 3 mm), en horizontal y en vertical, y por ultimo el centro del
    cuerpo. Devuelve las que no cupieron (pasan a F.Fab).
    """
    obst = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            obst.append(_caja(p.GetBoundingBox(), 0.2))
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS and isinstance(g, pcbnew.PCB_SHAPE):
                obst.append(_caja(g.GetBoundingBox(), 0.2))

    def prioridad(fp) -> tuple:
        ref = fp.GetReference()
        pre = re.match(r"[A-Z]+", ref).group(0)
        cy = caja_cy(fp)
        return (REF_ORDEN.index(pre) if pre in REF_ORDEN else len(REF_ORDEN),
                -(cy[2] - cy[0]) * (cy[3] - cy[1]))

    puestas, fuera = [], []
    for fp in sorted((f for f in board.GetFootprints() if f.GetReference() not in dict(
            (r, 0) for r, _x, _y in MONTAJE)), key=prioridad):
        ref = fp.Reference()
        ref.SetLayer(pcbnew.F_SilkS)
        ref.SetTextSize(pcbnew.VECTOR2I(mm(REF_ALTO), mm(REF_ALTO)))
        ref.SetTextThickness(mm(REF_TRAZO))
        x0, y0, x1, y1 = caja_cy(fp)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        candidatos = []
        for ang in (0, 90):
            ref.SetTextAngleDegrees(ang)
            ref.SetPosition(pcbnew.VECTOR2I(0, 0))
            tb = _caja(ref.GetBoundingBox())
            tw, th, g = tb[2] - tb[0], tb[3] - tb[1], 0.25
            for d in (0.0, -1.5, 1.5, -3.0, 3.0):
                candidatos += [(ang, cx + d, y0 - th / 2 - g), (ang, cx + d, y1 + th / 2 + g),
                               (ang, x0 - tw / 2 - g, cy + d), (ang, x1 + tw / 2 + g, cy + d)]
            candidatos.append((ang, cx, cy))
        for ang, px, py in candidatos:
            ref.SetTextAngleDegrees(ang)
            ref.SetPosition(pcbnew.VECTOR2I(mm(px), mm(py)))
            tb = _caja(ref.GetBoundingBox())
            if tb[0] < 0.6 or tb[1] < 0.6 or tb[2] > W - 0.6 or tb[3] > H - 0.6:
                continue
            if any(solapa(tb, o, 0.0) for o in obst) or any(solapa(tb, o, 0.0) for o in puestas):
                continue
            puestas.append(_caja(ref.GetBoundingBox(), 0.15))
            break
        else:
            ref.SetLayer(pcbnew.F_Fab)
            fuera.append(fp.GetReference())
    return fuera


# ------------------------------------------------------------------ ruteo
def ajustar_dsn(dsn: str) -> None:
    """Dos retoques al DSN recien exportado, los dos imposibles desde KiCad.

    1. **In1 pasa a capa de POTENCIA.** KiCad exporta las cuatro capas de
       cobre como `(type signal)` y no tiene opcion para otra cosa. Specctra
       si: una capa `(type power)` es un plano y el router no le mete pistas
       -- la regla del stackup. Los vertidos de In1 salen como (plane ...) de
       su red y Freerouting baja a ellos con una via (el fanout).
    2. **El margen del router sube 0.01 mm sobre el del DRC.** Freerouting
       redondea sus coordenadas y deja pistas dos micras por debajo de lo que
       apunta (lo mismo que en el VCO): con la centesima de mas el redondeo
       cae del lado bueno.

    El cobre de potencia no necesita retoque: va bloqueado y KiCad ya lo
    exporta como (type fix).
    """
    with open(dsn, encoding="utf-8") as fh:
        txt = fh.read()
    viejo = "(layer In1.Cu\n      (type signal)"
    assert viejo in txt, "el DSN no trae In1.Cu como capa de senal"
    txt = txt.replace(viejo, "(layer In1.Cu\n      (type power)", 1)
    clase = f"(clearance {int(CLEARANCE * 1000)})"
    assert clase in txt, f"el DSN no trae {clase}"
    txt = txt.replace(clase, f"(clearance {int(CLEARANCE * 1000) + 10})")
    with open(dsn, "w", encoding="utf-8") as fh:
        fh.write(txt)


def ajustes_freerouting() -> list[str]:
    """Opciones de Freerouting por linea de comandos, sin tocar su JSON de usuario.

    La 2.4.1 acepta `--router.<clave>=<valor>` para cualquier clave de su
    configuracion (y avisa "Unknown settings property" si no existe, cosa que
    rutear() convierte en error). En el VCO, con la 2.1.0, habia que parchear
    el freerouting.json del usuario y restaurarlo despues.

    * fanout: la etapa que saca una via de escape por pad SMD hasta el plano
      de In1. Ya viene encendida en la 2.4.1; se fija igualmente.
    * automatic_neckdown: una red de 0.5 mm (OUTS_POS, -12V_ULTRA) estrecha la
      pista al llegar a un pin de 0.25 mm. Sin el, Freerouting dejaba sin unir
      el pin de paso fino y la pista pasaba de largo a 0.9 mm.
    * via_costs se deja DE FABRICA. En el VCO (2.1.0) bajarlo a 8 ayudaba; en
      la 2.4.1 y esta placa hunde el fanout: 242 de 533 pines escapados con 8
      contra 357 de 533 con el de fabrica, misma placa y mismo DSN.
    """
    return ["--router.fanout.enabled=true", "--router.automatic_neckdown=true",
            f"--router.max_passes={PASADAS}", "--router.max_threads=1", "--gui.enabled=false"]


def rellenar(ruta: str):
    """Rellena las zonas de la placa de `ruta`, la guarda y la devuelve lista.

    El relleno se hace sobre una placa RECIEN CARGADA de disco (sobre una que
    ya estaba en memoria, ZONE_FILLER.Fill() tumba el proceso, la misma trampa
    que en el VCO) y despues se recarga para que la conectividad cuente el
    cobre nuevo.
    """
    board = pcbnew.LoadBoard(ruta)
    board.BuildListOfNets()
    board.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(board).Fill(board.Zones(), False, None), "no se rellenaron las zonas"
    guardar(ruta, board)
    board = pcbnew.LoadBoard(ruta)
    board.BuildListOfNets()
    board.BuildConnectivity()
    return board


def rutear() -> None:
    """Rondas de Freerouting sobre la placa colocada; se queda con la MEJOR.

    -mt 1 no es opcional: el propio Freerouting avisa de que su optimizador
    multihilo genera infracciones de separacion. Y Freerouting es
    ESTOCASTICO: la misma placa da resultados distintos en dos corridas, asi
    que se guarda la mejor ronda, no la ultima. Cada ronda arranca del ruteo
    de la anterior (el DSN se exporta de la placa ya ruteada y Freerouting
    levanta y rehace lo que le estorba).
    """
    if not FREEROUTING or not os.path.isfile(FREEROUTING):
        sys.exit("FALTA FREEROUTING: apunta FREEROUTING_JAR al freerouting-2.4.1-executable.jar\n"
                 "  (github.com/freerouting/freerouting; la 2.4.1 pide Java 25, ver JAVA).\n"
                 "  Este script no lo descarga solo. Sin rutear: --solo-colocar.")
    tmp = tempfile.mkdtemp(prefix="sam17-power-v5-")
    dsn, ses = os.path.join(tmp, "v5.dsn"), os.path.join(tmp, "v5.ses")
    log = os.path.join(tmp, "freerouting.log")
    # el SES se importa SIEMPRE sobre la placa sin rutear (trae el ruteo entero)
    virgen = os.path.join(tmp, "sin-rutear.kicad_pcb")
    mejor = os.path.join(tmp, "mejor.kicad_pcb")
    guardar(virgen, pcbnew.LoadBoard(PCB))
    record = None
    for ronda in range(1, RONDAS + 1):
        assert pcbnew.ExportSpecctraDSN(pcbnew.LoadBoard(PCB), dsn), "no se exporto el DSN"
        ajustar_dsn(dsn)
        print(f"freerouting ronda {ronda}/{RONDAS}, hasta {PASADAS} pasadas (avance en {log})", flush=True)
        with open(log, "w", encoding="utf-8") as fh:
            subprocess.run([JAVA, "-jar", FREEROUTING, "-de", dsn, "-do", ses, "-mp", str(PASADAS),
                            "-mt", "1", *ajustes_freerouting()],
                           stdout=fh, stderr=subprocess.STDOUT, text=True, check=False)
        with open(log, encoding="utf-8") as fh:
            salida = fh.read()
        malas = re.findall(r"(?:Unknown settings property|Failed to apply CLI router setting).*", salida)
        assert not malas, "freerouting no entendio sus opciones:\n" + "\n".join(malas)
        assert os.path.isfile(ses), f"freerouting no dejo SES:\n{salida[-2000:]}"
        board = pcbnew.LoadBoard(virgen)
        assert pcbnew.ImportSpecctraSES(board, ses), "no se importo el SES"
        guardar(PCB, board)
        os.remove(ses)
        # Sin rellenar las zonas no se puede contar: los pads de masa solo
        # tocan su plano a traves del relleno de In1. Se rellena una COPIA: la
        # placa que se exporta en la ronda siguiente sigue sin rellenar.
        copia = os.path.join(tmp, "relleno.kicad_pcb")
        guardar(copia, pcbnew.LoadBoard(PCB))
        sueltos = rellenar(copia).GetConnectivity().GetUnconnectedCount(True)
        if record is None or sueltos < record:
            record = sueltos
            guardar(mejor, pcbnew.LoadBoard(PCB))
        print(f"  ronda {ronda}: {sueltos} conexiones sin rutear (mejor: {record})", flush=True)
        if sueltos == 0:
            break
    guardar(PCB, pcbnew.LoadBoard(mejor))
    # La placa recien ruteada se guarda aparte: con --desde-ruteo se repite lo
    # que viene despues sin volver a pagar los ~45 min de Freerouting.
    shutil.copyfile(mejor, RUTADA)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"placa ruteada guardada en {RUTADA}")


def tras_el_ruteo() -> int:
    """Cobre termico de U1/U2 y masas vertidas en F.Cu y B.Cu. Devuelve las vias termicas.

    Las masas exteriores van en el MISMO poligono que su plano de In1, asi el
    hueco entre dominios se repite en las cuatro capas, y despues del ruteo:
    antes, Freerouting no tendria donde rutear. Las islas que no tocan nada de
    su red se borran (ISLAND_REMOVAL_MODE_ALWAYS).

    Primero se VACIAN los rellenos viejos. Al guardar, KiCad reconstruye la
    conectividad y le PROPAGA a cada via o pista la red del cobre que toca: las
    36 vias termicas de U2 (-15V5_FILT) todavia no tocan su cobre, que esta
    sin rellenar, pero si el relleno de GNDA que In1 tenia de antes en ese
    sitio, y se guardaban en GNDA. Sin rellenos no hay contacto falso;
    rellenar() los rehace despues con sus holguras.
    """
    board = pcbnew.LoadBoard(PCB)
    for z in board.Zones():
        z.UnFill()
    n = cobre_termico(board)
    for red, poligono in PLANOS_IN1.items():
        for capa in (pcbnew.F_Cu, pcbnew.B_Cu):
            zona(board, red, capa, poligono, conexion=pcbnew.ZONE_CONNECTION_THERMAL)
    guardar(PCB, board)
    return n


# --------------------------------------------------------------------- drc
def _informe_drc(extra: tuple = ()) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        rpt = os.path.join(tmp, "drc.json")
        subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm",
                        *extra, "-o", rpt, PCB], capture_output=True, text=True, check=False)
        assert os.path.isfile(rpt), "kicad-cli no dejo informe de DRC"
        with open(rpt, encoding="utf-8") as fh:
            return json.load(fh)


def rescatar() -> tuple[int, list[str]]:
    """Cierra con rescate.py (A* propio) las conexiones que Freerouting dejo abiertas.

    Freerouting se estanca en unas pocas: grupos de pads unidos entre si a
    unos milimetros del cobre fijo de su red, pines de paso fino que su pista
    ancha no tocaba. La lista la da el DRC de KiCad (zonas rellenas), por
    UUID de los dos extremos; cada conexion se intenta con el ancho de su
    clase y, si no cabe, con PISTA. Devuelve (cerradas, las que no).
    """
    import rescate
    cerradas, abiertas_final = 0, []
    for _ in range(3):
        abiertas = _informe_drc(("--refill-zones",)).get("unconnected_items", [])
        if not abiertas:
            return cerradas, []
        board = pcbnew.LoadBoard(PCB)
        board.BuildListOfNets()
        board.BuildConnectivity()
        por_uuid = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
        por_uuid.update({p.m_Uuid.AsString(): p for fp in board.GetFootprints() for p in fp.Pads()})
        obst = rescate.obstaculos(board)
        abiertas_final, avance = [], False
        for v in abiertas:
            items = [por_uuid.get(i.get("uuid", "")) for i in v.get("items", [])]
            quien = " <-> ".join(i.get("description", "")[:45] for i in v.get("items", []))
            if len(items) != 2 or None in items:
                abiertas_final.append(quien)
                continue
            red = items[0].GetNetname()
            ancho = POTENCIA if red in REDES_POTENCIA else PISTA_MASA if red in MASAS else PISTA
            # Un lado es el TROZO de red del primer item (lo que KiCad tiene
            # unido a el); el otro, cualquier cobre de la red fuera de ese trozo.
            # El par que da el DRC es uno cualquiera: aterrizar en otro pad o
            # pista suele ser mucho mas facil. Se quedan los 6 mas cercanos.
            def cerca_de(lista, ref):
                lista.sort(key=lambda i: math.hypot(i.GetPosition().x - ref.GetPosition().x,
                                                    i.GetPosition().y - ref.GetPosition().y))
                return lista[:6]
            clases = ("PAD", "PCB_TRACK", "PCB_VIA")
            trozo = [items[0]] + [i for i in board.GetConnectivity().GetConnectedItems(items[0])
                                  if i.GetNetname() == red and i.GetClass() in clases]
            dentro = {i.m_Uuid.AsString() for i in trozo}
            resto = [i for i in list(board.GetTracks()) + [p for fp in board.GetFootprints() for p in fp.Pads()]
                     if i.GetNetname() == red and i.m_Uuid.AsString() not in dentro]
            grupos = [cerca_de(trozo, items[1]), cerca_de(resto, items[0])]
            if any(rescate.conectar(board, grupos[0], grupos[1], w, CLEARANCE, VIA_D, VIA_DRILL,
                                    (W, H, 0.5), obst) for w in sorted({ancho, PISTA}, reverse=True)):
                cerradas += 1
                avance = True
                board.BuildConnectivity()
                obst = rescate.obstaculos(board)      # lo nuevo estorba a lo siguiente
            else:
                abiertas_final.append(quien)
        guardar(PCB, board)
        if not avance:
            break
    return cerradas, abiertas_final


def limpiar_colgantes() -> int:
    """Quita los tramos y vias que Freerouting deja colgando. Devuelve cuantos.

    Los decide el DRC de KiCad (track_dangling / via_dangling sobre la placa
    ya rellenada), no una regla propia: se borra exactamente lo que el DRC
    senala, nunca algo bloqueado (cobre de potencia, costuras), y se repite
    porque quitar un rabo puede dejar colgando el tramo que lo alimentaba.
    """
    total = 0
    for _ in range(6):
        informe = _informe_drc()
        uuids = {i["uuid"] for v in informe.get("violations", [])
                 if v["type"] in ("track_dangling", "via_dangling") for i in v["items"]}
        if not uuids:
            break
        board = pcbnew.LoadBoard(PCB)
        sobran = [t for t in board.GetTracks() if t.m_Uuid.AsString() in uuids and not t.IsLocked()]
        if not sobran:
            break
        for t in sobran:
            quitar(board, t)
        guardar(PCB, board)
        rellenar(PCB)
        total += len(sobran)
    return total


def resolver_termicos() -> list[str]:
    """Pads a los que un vertido de masa no llega con radios de alivio (starved_thermal).

    Son pines de paso fino (los GND de U4/U5 unidos a su pad expuesto) y
    alguna pata THT rodeada de pistas. Todos estan ya unidos a su masa por su
    tramo, su via o el plano de In1: el vertido exterior no les hace falta.
    El SMD pasa a no conectar con los vertidos; el THT a conexion maciza (si
    se le quitara, perderia tambien el plano de In1). Decide el DRC.
    """
    hechos = []
    for _ in range(3):
        uuids = {i["uuid"] for v in _informe_drc().get("violations", [])
                 if v["type"] == "starved_thermal" for i in v["items"]}
        board = pcbnew.LoadBoard(PCB)
        tocados = [(fp, p) for fp in board.GetFootprints() for p in fp.Pads() if p.m_Uuid.AsString() in uuids]
        if not tocados:
            break
        for fp, p in tocados:
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_NONE if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
                                     else pcbnew.ZONE_CONNECTION_FULL)
            hechos.append(f"{fp.GetReference()}.{p.GetNumber()}")
        guardar(PCB, board)
        rellenar(PCB)
    return list(dict.fromkeys(hechos))      # el pad expuesto se repite: U4.11 x2


def drc() -> list[str]:
    """DRC de KiCad con TODAS las severidades y paridad con el esquematico.

    El informe se guarda (EVIDENCIA_DRC) con el sha256 del .kicad_pcb que
    comprobo: check_pcb.py, que corre sin KiCad, se fia de el solo si la
    placa commiteada es esa misma. Se guarda tambien cuando hay fallos, para
    que la puerta los cuente en vez de encontrar un informe viejo y limpio.
    """
    informe = _informe_drc(("--schematic-parity",))
    with open(PCB, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    evidencia = {"pcb": os.path.basename(PCB), "pcb_sha256": sha,
                 "kicad_version": informe.get("kicad_version", ""),
                 "severidades": "todas (--severity-all) + paridad con el esquematico"}
    for clave in ("violations", "unconnected_items", "schematic_parity"):
        evidencia[clave] = informe.get(clave, [])
    with open(EVIDENCIA_DRC, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(evidencia, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    fallos = []
    tipos: dict[str, int] = {}
    for v in informe.get("violations", []):
        tipos[v["type"]] = tipos.get(v["type"], 0) + 1
    for k, n in sorted(tipos.items()):
        fallos.append(f"DRC: {n} x {k}")
    if n := len(informe.get("unconnected_items", [])):
        fallos.append(f"DRC: {n} conexiones sin rutear")
    if n := len(informe.get("schematic_parity", [])):
        fallos.append(f"DRC: {n} diferencias de paridad con el esquematico")
    return fallos


# ------------------------------------------------------------------ main
def construir() -> None:
    escribir_reglas()
    comps, redes = leer_netlist()
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    contorno(board)
    colocar(board, comps, redes)
    zonas(board)
    revisar_cobre()
    cobre_fijo(board)
    reservas(board)
    unidos = puentes(board)
    cosidas, sin_via = coser_masas(board)
    textos(board)
    fuera = colocar_referencias(board)
    guardar(PCB, board)
    print(f"colocada: {len(comps)} componentes, {len(COBRE)} rectangulos de cobre fijo, "
          f"{cosidas} vias de masa cosidas, puentes en B.Cu: {' '.join(unidos)}")
    if sin_via:
        print(f"  pads de masa sin sitio para su via (los rutea Freerouting): {' '.join(sin_via)}")
    print(f"  {len(fuera)} referencias sin sitio en serigrafia pasan a F.Fab: {' '.join(fuera)}")


def main() -> int:
    desde = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--desde-ruteo=")), None)
    if desde:
        escribir_reglas()
        board = pcbnew.LoadBoard(desde)
        sincronizar(board, leer_netlist()[0])
        guardar(PCB, board)
        print(f"partiendo de la placa ruteada {desde}")
    else:
        construir()
        if "--solo-colocar" in sys.argv:
            return 0
        rutear()
    # Primero fuera los rabos que deja Freerouting (con las zonas rellenas: sin
    # el plano de In1, una via de bajada parece colgar), para que el rescate no
    # intente unir un pad con un trozo de pista que no lleva a ningun sitio.
    rellenar(PCB)
    limpiar_colgantes()
    cerradas, abiertas = rescatar()
    print(f"rescate: {cerradas} conexiones cerradas a mano tras Freerouting"
          + (f"; siguen abiertas: {abiertas}" if abiertas else ""))
    termicas = tras_el_ruteo()
    rellenar(PCB)
    if quitados := limpiar_colgantes():
        print(f"limpieza: {quitados} tramos o vias colgando que dejo Freerouting")
    if alivios := resolver_termicos():
        print(f"alivios termicos sin radios resueltos por pad: {' '.join(alivios)}")
    board = rellenar(PCB)
    pistas = sum(1 for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))
    vias = sum(1 for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
    print(f"placa {W:.0f} x {H:.0f} mm: {pistas} pistas, {vias} vias ({termicas} termicas)")
    fallos = drc()
    for f in fallos:
        print("FALLO:", f)
    if fallos:
        return 1
    print("DRC (todas las severidades + paridad): 0 infracciones, 0 sin conectar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
