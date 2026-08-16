"""Genera sam17-vco.kicad_pcb: 240 x 172 mm, 2 capas, UNA masa (GNDA) con
una isla GNDD minima en la esquina de J2.

NOTA DE TAMANO: el brief pedia partir de 120x80 y crecer si el ruteo lo
pedia. Lo pidio, y fuerte -- tres causas, cada una diagnosticada contra el
fallo real del router, no a ojo:

  1. Un 0805 mide 1.4-1.45 mm en el lado corto del pad; con los pasivos en
     columna recta a 2 mm de paso (la primera pasada, a 176x112) solo
     quedaban 0.6 mm libres entre vecinos -- menos de lo que pide una
     pista con su holgura (0.5 mm). Separarlos a 3.2-4.5 mm de paso resolvio
     la mayoria de las conexiones LOCALES (pin del QFN a su propio pasivo).
  2. Con los pasivos de una misma columna en el MISMO x (o fila en el mismo
     y), cualquier camino en L/Z cruza esa columna -- o la del propio QFN,
     a 0.4 mm de paso -- y un vecino de en medio corta el paso. En ZIGZAG
     (dos x o dos y alternados) cada pasivo tiene carril propio.
  3. Los buses que visitan los 4 canales (MIX_TRI/SAW/PULSE/SINE, VREF_2V5,
     SPI, +5V_LOC...) necesitan un CARRIL TRONCAL limpio para cruzar de
     canal a canal. Pegado el anillo a U9/la isla digital, competian por el
     mismo hueco estrecho que las conexiones locales. Separando U9 y la
     isla 18 mm mas del borde del anillo deja una franja de ~15 mm sin
     pasivos, dedicada a ese trafico.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Va con pcbnew directo, igual que el modulo 1, el modulo 2 y el bus board.

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

ASIMETRIA DE RUTEO: la pista de esta placa vive en F.Cu. B.Cu es el plano
-- GNDA cubre el 95% de la placa, GNDD el resto -- y el ruteador solo baja
una senal a B.Cu cuando F.Cu no tiene por donde y el salto no parte la isla
en trozos (revisar() lo comprueba: 1 sola isla por dominio). Es la misma
logica del modulo 2 llevada a su caso limite: si casi toda la placa es un
solo dominio, casi toda la placa rutea por encima del plano, no a traves de
el.

LA REGLA QUE MANDA LA COLOCACION (dac_local_budget.py): U5 (el DAC que manda
CV_PITCH a las 4 voces) va PEGADO al racimo U1-U4. Se le suman U6 y U7 (los
DAC de nivel de mezcla, que abastecen a los 4 canales por igual) en la misma
fila, y U8 (la referencia) entre los DAC y el racimo -- la ubicacion hace
literal el "star" corto de VREF_2V5 que pide tuning_budget.py.

EL EP DE CADA SSI2130 (pin 33, land termico) queda AISLADO a proposito: la
netlist ya lo trae con nombre unico "unconnected-(Un-EP-Pad33)" y este script
NO lo toca -- ni via, ni red, ni union al plano. El datasheet (pag.6,
Exposed Thermal Pad) lo prohibe: unir el EP a GND convierte el land en una
antena de acoplo entre las 4 voces y en un camino de fuga termica que el
autoafinado no puede compensar.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-vco.kicad_pcb")
NET = os.path.join(DIR, "sam17-vco.net")
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
STOCK = os.environ.get("KICAD_FOOTPRINTS",
                       r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

W, H = 240.0, 172.0
MARGEN = 4.0
# la isla GNDD: esquina inferior izquierda, x < ISLA_X1 e y > ISLA_Y1 (antes
# de descontar el hueco). Los dos bordes que SI dan a GNDA son el derecho
# (x=ISLA_X1) y el de arriba (y=ISLA_Y1); los otros dos coinciden con el
# borde de la placa, ahi no hace falta hueco.
ISLA_X1 = 66.0
ISLA_Y1 = 126.0
HUECO = 3.0                # ancho del hueco de cobre entre GNDA y GNDD, mm
G = HUECO / 2

ANCHO = 0.2                 # pista de senal. QFN de 0.4 mm de paso: con 0.25
                            # (lo del modulo 2) no cabe ni una entre pads.
ANCHO_MED = 0.3             # +5V_LOC / +3V3_LOC
ANCHO_POT = 0.5             # +12V / -12V: solo alimentan reguladores y TL074,
                            # corriente baja, no hace falta mas.
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

# ---------------------------------------------------------- las 4 voces
# Centro del QFN de cada canal. 50 mm de paso: el anillo de ~20 pasivos 0805
# alrededor de cada QFN mide ahora ~32x32 mm (ver la nota de tamano arriba),
# y hace falta pasillo de sobra entre canales para las 4 pistas de bus
# (MIX_TRI/SAW/PULSE/SINE, VREF_2V5, SPI, +5V_LOC...) que los cruzan.
CX = [35.0, 85.0, 135.0, 185.0]
CY = 74.0
JACK_Y = 16.0

# Plantilla de un canal: (formato-de-ref, dx, dy) relativo al centro del
# QFN. Cada lado del chip agrupa las senales que entran por ese lado (visto
# en el .kicad_mod, pin a pin -- ver el reporte):
#   IZQUIERDA (pines 1-8): red del conformador de seno + TRI_OUT + EXPO_FREQ
#     (el nodo que suma CV_PITCH del DAC y CVIN del jack) + V-.
#   DERECHA (17-24): red de VREF (LIN_FREQ, EXPO_SCALE) + bucle de SINE_OUT.
#   ABAJO (9-16): las 4 entradas del mezclador (vienen del DAC) + TCAP.
#   ARRIBA (25-32): MIX_OUT (hacia U9), BW_COMP, SQUARE_OUT (hacia U10).
# Paso de 3.2 mm en las columnas (izq/der) y 4.5 mm en las filas (arriba/
# abajo): el 0805 mide 1.4-1.45 mm en el lado corto del pad y 2.85 mm de
# huella entera de punta a punta -- con eso deja ~1.8/1.6 mm libres entre
# vecinos, de sobra para una pista de 0.2 mm con su holgura.
#
# EN ZIGZAG, no en columna recta: al principio los 7 de la columna
# izquierda estaban los siete en el MISMO x. El ruteador de caminos en L/Z
# solo tiene dos formas de llegar del pasivo al pin del chip, y las dos
# cruzan una vertical exactamente por esa columna -- o por la columna de
# pines del chip, que tiene el mismo problema a 0.4 mm de paso. Cualquier
# vecino de en medio corta el paso. Alternando el x (o el y, en las filas)
# entre dos valores, cada pasivo tiene su propio carril para el primer
# tramo del camino. (Se probo tambien dar a CADA pieza su propio x/y unico,
# no solo alternar entre dos -- salio peor, 83 sin rutear contra 77: el
# anillo mas ancho complica mas de lo que despeja. Ver el reporte.)
_PLANTILLA = [
    ("U{i}", 0.0, 0.0),
    ("R_SIN475B_{i}", -13.0, -11.2),
    ("R_SIN402_{i}", -16.0, -8.0),
    ("R_SIN475A_{i}", -13.0, -4.8),
    ("C_AC{i}A", -16.0, -1.6),
    # C_AC*B es un PUENTE de verdad: sus dos pines van a AUX1_IN (pin4,
    # lado izquierdo) y a SINE_OUT (pin24, esquina arriba-derecha) -- lados
    # OPUESTOS del chip. Se probo centrarlo arriba del chip (mas cerca de
    # las dos patas en linea recta) y salio PEOR (82 sin rutear contra 77):
    # le quita sitio al carril que ya usan R_IV/R_BW/C_BW/R_SQ. Se deja en
    # la columna izquierda -- la conexion SI tiene camino geometrico (visto
    # con el router en modo diagnostico), lo que le falta es turno, no
    # sitio. Ver el reporte.
    ("C_AC{i}B", -13.0, 1.6),
    ("R_PITCH{i}", -16.0, 4.8),
    ("R_CVIN{i}", -13.0, 8.0),
    ("R_LIN{i}", 13.0, -4.8),
    ("R_SCALE{i}", 16.0, -1.6),
    ("R_MIX{i}A", -9.0, 13.0),
    ("R_MIX{i}B", -4.5, 16.0),
    ("R_MIX{i}C", 0.0, 13.0),
    ("R_MIX{i}D", 4.5, 16.0),
    ("C_TCAP{i}", 9.0, 13.0),
    ("R_IV{i}", -6.75, -13.0),
    ("R_BW{i}", -2.25, -16.0),
    ("C_BW{i}", 2.25, -13.0),
    ("R_SQ{i}", 6.75, -16.0),
]
# desacoplos de 100 nF de cada canal: <2 mm del pin de alimentacion que
# desacoplan (regla 3). C_5V junto a V+ (derecha), C_12V junto a V- (izq).
_DESACOPLO_5V = {1: "C21", 2: "C22", 3: "C23", 4: "C24"}
_DESACOPLO_12V = {1: "C27", 2: "C28", 3: "C29", 4: "C30"}

COLOCACION: dict[str, tuple[str, float, float, int]] = {}
for _i, _cx in enumerate(CX, start=1):
    for _fmt, _dx, _dy in _PLANTILLA:
        _ref = _fmt.format(i=_i)
        _clave = "qfn32" if _ref.startswith("U") else (
            "c" if _ref.startswith("C") else "r")
        COLOCACION[_ref] = (_clave, _cx + _dx, CY + _dy, 0)
    COLOCACION[_DESACOPLO_5V[_i]] = ("c", _cx + 13.0, CY + 1.6, 0)
    COLOCACION[_DESACOPLO_12V[_i]] = ("c", _cx - 13.0, CY + 11.2, 0)
    COLOCACION[f"J_CV{_i}"] = ("jack", _cx - 11.0, JACK_Y, 0)
    COLOCACION[f"J_OUT{_i}"] = ("jack", _cx + 11.0, JACK_Y, 0)
    # puntos de prueba: pegados a la resistencia de su propia senal, un poco
    # mas afuera para no pisarla.
    COLOCACION[f"TP{5 + _i}"] = ("tp", _cx - 20.0, CY + 8.0, 0)       # CV_PITCH
    COLOCACION[f"TP{9 + _i}"] = ("tp", _cx - 6.75, CY - 22.0, 0)      # MIXO

# --------------------------------------------------- DAC + referencia + U9
# U5-U7 PEGADOS al racimo (regla 1 de dac_local_budget.py): la fila de DAC
# queda a menos de 60 mm del centro de cada canal, ver la medida real y la
# comparacion contra la cota pesimista (50 mm/20 mm) en el reporte. U8 entre
# los DAC y el racimo (regla 4): la estrella de VREF_2V5 sale corta hacia
# los dos lados.
COLOCACION.update({
    # U5 (el que manda CV_PITCH a las 4 voces, el critico para el
    # presupuesto) va en el CENTRO de la fila, no en una punta: centrado
    # entre canal 1 y canal 4 el peor caso (a U1 o a U4) baja de 94 a 85 mm.
    # U6 y U7 (nivel de mezcla, no afinacion) se reparten a los lados.
    "U6": ("tssop16", 100.0, 34.0, 0),
    "U5": ("tssop16", 110.0, 34.0, 0),
    "U7": ("tssop16", 120.0, 34.0, 0),
    # los dos desacoplos de cada DAC, los dos DEBAJO del chip: el courtyard
    # real del jack (Jack_3.5mm_QingPu...) llega hasta y=29 desde su punto
    # de montaje -- un desacoplo "arriba" a y=24 (donde estaba) cae dentro
    # y el DRC marca courtyards_overlap contra J_OUT2/J_CV3.
    "C14": ("c", 100.0, 40.0, 0), "C15": ("c", 100.0, 48.0, 0),
    "C12": ("c", 110.0, 40.0, 0), "C13": ("c", 110.0, 48.0, 0),
    "C16": ("c", 120.0, 40.0, 0), "C17": ("c", 120.0, 48.0, 0),
    "U8": ("soic8", 110.0, 52.0, 0),
    "C11": ("c", 116.0, 52.0, 0),
    "TP5": ("tp", 104.0, 52.0, 0),
    # U9 lejos del borde inferior del anillo (90.7) a proposito: entre los
    # dos queda un CARRIL TRONCAL de ~15 mm libre de pasivos, por donde
    # cruzan sin estorbarse los buses que visitan los 4 canales (MIX_*,
    # VREF_2V5, SPI, +5V_LOC...). Pegado al anillo, esos buses competian por
    # el mismo hueco estrecho que las conexiones locales pin-a-pasivo.
    "U9": ("soic14", 110.0, 116.0, 0),
})

# ------------------------------------------------- alimentacion + reguladores
# J1 en el borde OPUESTO a los jacks (regla 5): jacks arriba (y=16), J1 abajo
# a la derecha. Los reguladores locales +5V_LOC/+3V3_LOC viven pegados a J1,
# lejos del racimo -- no alimentan nada sensible a ruido de conmutacion.
COLOCACION.update({
    "J1": ("molex4", 226.0, 142.0, 0),
    "U11": ("sot89", 206.0, 130.0, 0),
    "U12": ("sot223", 216.0, 130.0, 0),
    "C8": ("c", 202.0, 138.0, 0), "C9": ("c", 220.0, 138.0, 0),
    "C10": ("c", 211.0, 122.0, 0),
    "C25": ("c", 226.0, 126.0, 0), "C26": ("c", 234.0, 126.0, 0),
    "TP1": ("tp", 220.0, 122.0, 0), "TP2": ("tp", 228.0, 134.0, 0),
    "TP3": ("tp", 198.0, 122.0, 0), "TP4": ("tp", 206.0, 114.0, 0),
    "TP14": ("tp", 140.0, 108.0, 0),
})

# --------------------------------------------------------- isla GNDD (J2)
# Solo lo que pide el brief: J2, U10, U13, U14, sus desacoplos y los pullups
# de I2C. U13 en la esquina de la isla mas cercana al racimo (canal 1) --
# mide la temperatura de los osciladores, no la del conector.
COLOCACION.update({
    "J2": ("idc12", 16.0, 136.0, 0),
    "U10": ("soic14", 44.0, 146.0, 0),
    "U13": ("vssop8", 58.0, 130.0, 0),
    # U14 y C20 NO en (14, ~150): el courtyard real del IDC-Header 2x06
    # (con el conector de cable, no solo el pin header) es -3.68..6.22 en x
    # y -5.6..18.3 en y desde el punto de montaje -- 24 mm de alto, no los
    # ~10 mm que parecia a ojo. A (14,154)/(14,146) caian DENTRO de ese
    # rectangulo. Movidos a x=24/30, fuera de el.
    "U14": ("sot235", 24.0, 162.0, 0),
    "C18": ("c", 44.0, 156.0, 0),
    "C19": ("c", 52.0, 134.0, 0),
    "C20": ("c", 30.0, 162.0, 0),
    "R_I2C1": ("r", 26.0, 130.0, 0),
    "R_I2C2": ("r", 32.0, 130.0, 0),
    "TP15": ("tp", 38.0, 160.0, 0),
})

# Componentes cuya red GNDD/GNDA los ata a un lado concreto: todo lo que cae
# en en_isla() debe ser de la isla, y viceversa. Se comprueba por PAD, no por
# esta lista -- esta lista es solo la lectura humana de lo mismo.
ISLA_REFS = {"J2", "U10", "U13", "U14", "C18", "C19", "C20",
             "R_I2C1", "R_I2C2", "TP15"}


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


def main() -> None:
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

    reglas = board.GetDesignSettings()
    reglas.m_TrackMinWidth = mm(ANCHO)
    reglas.m_MinClearance = mm(CLEARANCE)
    # m_MinClearance NO basta: el DRC de verdad (kicad-cli, no este script)
    # aplica el margen de la NETCLASS "Default", que nace en 0.2 mm y se
    # queda ahi si no se toca aparte. El ruteador (rutear_todo) ya asume
    # CLEARANCE=0.15 mm entre pads de 0.4 mm de paso; sin esta linea el DRC
    # real exige 0.2 y encuentra infracciones en pistas que el propio
    # ruteador dio por buenas -- 32 infracciones, todas de este origen, en
    # la primera pasada que no la tenia.
    board.GetAllNetClasses()["Default"].SetClearance(mm(CLEARANCE))

    # ------------------------------------------------------------ ruteo
    n_seg, n_via, sin_rutear = rutear_todo(board)
    print(f"ruteadas {n_seg} segmentos y {n_via} vias")
    if sin_rutear:
        print(f"SIN RUTEAR ({len(sin_rutear)}):")
        for s in sin_rutear:
            print("   ", s)

    pcbnew.SaveBoard(PCB, board)

    # el relleno hay que hacerlo sobre la placa RECARGADA: sobre la de
    # memoria ZONE_FILLER.Fill() se lleva el proceso por delante con un
    # access violation, sin excepcion que capturar (misma trampa que en el
    # bus board y en el modulo 2).
    board = pcbnew.LoadBoard(PCB)
    board.BuildListOfNets()
    board.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(board).Fill(board.Zones(), False, None), \
        "no se rellenaron las zonas"
    pcbnew.SaveBoard(PCB, board)

    fallos = revisar(board)
    for f in fallos:
        print("FALLO:", f)
    zonas = {z.GetNetname(): z for z in board.Zones()}
    print(f"{len(COLOCACION)} huellas colocadas, "
          f"{len(board.GetTracks())} segmentos, "
          f"zonas: {sorted(zonas)} en "
          f"{['F.Cu', '?', 'B.Cu'][zonas['GNDA'].GetLayer()]}")
    if fallos:
        sys.exit(1)

    drc = subprocess.run([KICAD_CLI, "pcb", "drc", "--severity-error",
                          "--exit-code-violations", PCB],
                         capture_output=True, text=True)
    print(drc.stdout.strip()[-800:] or drc.stderr.strip()[-300:])

    # Sale con error mientras queden redes sin rutear. La placa NO es
    # fabricable en ese estado, y un script que termina en verde con N redes
    # al aire es justo la clase de trampa que este repo intenta no dejar.
    if sin_rutear:
        print(f"\nLA PLACA NO ESTA TERMINADA: quedan {len(sin_rutear)} redes "
              f"sin rutear. Colocacion y masas si estan cerradas.")
        sys.exit(2)
    sys.exit(drc.returncode)


# Barrido denso de corredores, como el modulo 2: una lista corta de valores a
# ojo deja redes sin rutear porque el hueco bueno casi nunca cae justo en uno
# de los elegidos a mano.
CORREDORES_X = [4.0 + 1.5 * i for i in range(int((W - 8.0) / 1.5) + 1)]
CORREDORES_Y = [4.0 + 1.5 * i for i in range(int((H - 8.0) / 1.5) + 1)]
ESCAPES = ([(0.0, 0.0)]
           + [(d * s, 0.0) for d in (1.2, 2.2, 3.6, 5.2, 7.0) for s in (1, -1)]
           + [(0.0, d * s) for d in (1.2, 2.2, 3.6, 5.2, 7.0) for s in (1, -1)])


def _dist_punto_seg(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    tt = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / L))
    return ((p[0] - (a[0]+tt*dx))**2 + (p[1] - (a[1]+tt*dy))**2) ** 0.5


def _seg_seg(a, b, c, d) -> float:
    def o(p, q, r):
        v = (q[1]-p[1])*(r[0]-q[0]) - (q[0]-p[0])*(r[1]-q[1])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else 2)
    if o(a, b, c) != o(a, b, d) and o(c, d, a) != o(c, d, b):
        return 0.0
    return min(_dist_punto_seg(a, c, d), _dist_punto_seg(b, c, d),
               _dist_punto_seg(c, a, b), _dist_punto_seg(d, a, b))


def _dist_seg_rect(a, b, x0, y0, x1, y1) -> float:
    for p in (a, b):
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            return 0.0
    lados = (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
             ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))
    return min(_seg_seg(a, b, c, d) for c, d in lados)


def rutear_todo(board):
    """Ruteador minimo: para cada red prueba caminos en L, en Z y con
    escape, y se queda con el primero que no roce nada. Ver el modulo 2 para
    la explicacion completa; aqui solo cambia lo que exige esta placa:

    * F.Cu primero SIEMPRE. B.Cu solo entra si F.Cu no tiene por donde Y el
      salto no deja un via debajo del land termico de un SSI2130 (el EP,
      pin 33, tiene que quedar sin via bajo ningun concepto -- regla 2).
    * Despues de rutear, revisar() comprueba que ni GNDA ni GNDD quedaron
      partidos en mas de una isla: es la comprobacion real de la asimetria
      B.Cu, no una prohibicion ciega de pisar la capa de abajo.
    * Los obstaculos (pads, pistas ya puestas, vias) se indexan en una
      rejilla de CELDA mm. Con las 4 QFN de 33 pads cada una mas el resto,
      esta placa tiene ~4x los pads del modulo 2: comprobar cada candidato
      contra TODOS los pads (lo que hacia el modulo 2) tarda demasiado aqui.
      Indexado, cada comprobacion solo mira los obstaculos de las celdas por
      las que pasa el segmento.
    """
    # GetSize(), NO. Los 8 pads de esquina del QFN (1,8,9,16,17,24,25,32)
    # son de forma "custom" (poligono biselado para el fanout) y su
    # GetSize() devuelve el ancla interna -- 0.13x0.13 mm -- no el cobre
    # real, que mide 0.2x0.8 mm como cualquier otro pin. Con GetSize() el
    # ruteador los veia casi puntuales y dejaba pistas a 0.05 mm de un
    # vecino real (4 infracciones de DRC, todas TRI_n contra PWM_CV, mismo
    # patron en los 4 canales). GetBoundingBox() da el rectangulo real,
    # tambien para los pads roundrect normales.
    obst_pads = [(p.GetNetname(),
                  p.GetBoundingBox().GetLeft()/1e6,
                  p.GetBoundingBox().GetTop()/1e6,
                  p.GetBoundingBox().GetRight()/1e6,
                  p.GetBoundingBox().GetBottom()/1e6)
                 for fp in board.GetFootprints() for p in fp.Pads()]
    # los lands EP (pin 33 de U1-U4): radio de exclusion de VIA ancho aparte
    # de la comprobacion normal de pad, para que ningun salto a B.Cu ponga
    # una via encima ni al lado.
    ep_centros = [(p.GetX()/1e6, p.GetY()/1e6)
                  for fp in board.GetFootprints() for p in fp.Pads()
                  if p.GetNumber() == "33" and fp.GetReference().startswith("U")
                  and fp.GetReference()[1:].isdigit() and 1 <= int(fp.GetReference()[1:]) <= 4]

    # Indexado en rejilla: se INSERTA cada obstaculo con su extension real,
    # sin margen, y se CONSULTA expandiendo la caja de busqueda por la
    # distancia maxima que puede importar (MAXALCANCE). Repartir el margen
    # entre insercion y consulta es tentador para ahorrar memoria, pero con
    # celdas de 4 mm y margenes de un par de decimas un obstaculo pegado al
    # borde de su celda puede quedar a distancia real corta de un punto en
    # la celda VECINA sin que ninguna de las dos consultas lo vea -- toda la
    # holgura tiene que ir del lado de la consulta.
    CELDA = 4.0
    MAXALCANCE = 1.0   # > CLEARANCE + max(ancho)/2 + max(ancho)/2 y > VIA_D/2*2

    def celdas_de(x0, y0, x1, y1, pad=0.0):
        cx0, cx1 = int((x0 - pad) // CELDA), int((x1 + pad) // CELDA)
        cy0, cy1 = int((y0 - pad) // CELDA), int((y1 + pad) // CELDA)
        return [(cx, cy) for cx in range(cx0, cx1 + 1) for cy in range(cy0, cy1 + 1)]

    idx_pads: dict = {}
    for i, (_n, x0, y0, x1, y1) in enumerate(obst_pads):
        for c in celdas_de(x0, y0, x1, y1):
            idx_pads.setdefault(c, []).append(i)

    puestos: list = []          # (net, capa, a, b, ancho)
    vias: list = []             # (net, x, y, radio)
    idx_puestos: dict = {}
    idx_vias: dict = {}

    def indexar(indice, clave, x0, y0, x1, y1):
        for c in celdas_de(x0, y0, x1, y1):
            indice.setdefault(c, []).append(clave)

    def candidatos(indice, x0, y0, x1, y1):
        vistos: set = set()
        for c in celdas_de(x0, y0, x1, y1, MAXALCANCE):
            for i in indice.get(c, ()):
                if i not in vistos:
                    vistos.add(i)
                    yield i

    def ancho_de(net: str) -> float:
        if net in ("+12V", "-12V"):
            return ANCHO_POT
        return ANCHO_MED if net in ("+5V_LOC", "+3V3_LOC") else ANCHO

    def libre(net, capa, a, b, w) -> bool:
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        for i in candidatos(idx_pads, x0, y0, x1, y1):
            n, px0, py0, px1, py1 = obst_pads[i]
            if n == net:
                continue
            if _dist_seg_rect(a, b, px0, py0, px1, py1) < CLEARANCE + w / 2:
                return False
        for i in candidatos(idx_puestos, x0, y0, x1, y1):
            n, c, p, q, wo = puestos[i]
            if n == net or c != capa:
                continue
            if _seg_seg(a, b, p, q) < CLEARANCE + w / 2 + wo / 2:
                return False
        for i in candidatos(idx_vias, x0, y0, x1, y1):
            n, vx, vy, vr = vias[i]
            if n == net:
                continue
            if _dist_punto_seg((vx, vy), a, b) < CLEARANCE + w / 2 + vr:
                return False
        return True

    def caminos(a, b):
        yield [a, (b[0], a[1]), b]
        yield [a, (a[0], b[1]), b]
        orden_x = sorted(CORREDORES_X, key=lambda v: min(abs(v-a[0]), abs(v-b[0])))
        orden_y = sorted(CORREDORES_Y, key=lambda v: min(abs(v-a[1]), abs(v-b[1])))
        for mx in orden_x:
            yield [a, (mx, a[1]), (mx, b[1]), b]
        for my in orden_y:
            yield [a, (a[0], my), (b[0], my), b]
        for lado in (0, 1):
            for esc in ESCAPES[1:]:
                pa = (a[0] + esc[0], a[1] + esc[1]) if lado == 0 else a
                pb = b if lado == 0 else (b[0] + esc[0], b[1] + esc[1])
                for mx in orden_x[:28]:
                    yield [a, pa, (mx, pa[1]), (mx, pb[1]), pb, b]
                for my in orden_y[:28]:
                    yield [a, pa, (pa[0], my), (pb[0], my), pb, b]

    por_red: dict = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if not n or n in ("GNDA", "GNDD") or n.startswith("unconnected-"):
                continue
            por_red.setdefault(n, []).append((p.GetX()/1e6, p.GetY()/1e6))

    def via_cabe(net, punto) -> bool:
        r = VIA_D / 2 + CLEARANCE
        for ex, ey in ep_centros:
            # el land del EP mide 2.65x2.65, medio lado 1.325: nada de via
            # ni siquiera cerca, con margen de sobra.
            if abs(punto[0] - ex) < 1.325 + r and abs(punto[1] - ey) < 1.325 + r:
                return False
        px, py = punto
        for i in candidatos(idx_pads, px, py, px, py):
            n, x0, y0, x1, y1 = obst_pads[i]
            if n != net and _dist_seg_rect(punto, punto, x0, y0, x1, y1) < r:
                return False
        for i in candidatos(idx_puestos, px, py, px, py):
            n, _c, q1, q2, wo = puestos[i]
            if n != net and _dist_punto_seg(punto, q1, q2) < r + wo / 2:
                return False
        for i in candidatos(idx_vias, px, py, px, py):
            n, vx, vy, vr = vias[i]
            if n != net and ((punto[0]-vx)**2 + (punto[1]-vy)**2) ** 0.5 < r + vr:
                return False
        return True

    n_seg = n_via = 0
    sin_rutear = []

    # AL REVES que el modulo 2: redes CORTAS primero. Probado en tres
    # variantes (ver el reporte: todas las largas primero, un hibrido con
    # las 11 redes que visitan los 4 canales primero, y esta), redes cortas
    # primero es la que menos deja sin rutear -- 77, contra 83-109 de las
    # otras dos. Alli el board estaba casi vacio y las redes largas
    # necesitaban via libre antes que nadie mas lo ocupara; aqui las
    # conexiones cortas pin-a-pasivo son las que tienen MENOS margen (aun
    # con el anillo en zigzag) y una red larga que entra antes les quita el
    # hueco justo donde mas hace falta.
    def envergadura(par):
        pts = par[1]
        return (max(x for x, _ in pts) - min(x for x, _ in pts)
                 + max(y for _, y in pts) - min(y for _, y in pts))

    total_redes = len(por_red)
    for i_red, (net, pts) in enumerate(sorted(por_red.items(), key=envergadura), 1):
        if i_red % 20 == 0 or i_red == total_redes:
            print(f"  ruteando red {i_red}/{total_redes} ({net})...", flush=True)
        pts = sorted(set(pts))
        hechos, pend = [pts[0]], pts[1:]
        while pend:
            b = min(pend, key=lambda q: min(abs(q[0]-h[0]) + abs(q[1]-h[1])
                                            for h in hechos))
            a = min(hechos, key=lambda h: abs(b[0]-h[0]) + abs(b[1]-h[1]))
            pend.remove(b)
            elegido = None
            for capa in (pcbnew.F_Cu, pcbnew.B_Cu):
                if capa == pcbnew.B_Cu and not (via_cabe(net, a) and via_cabe(net, b)):
                    continue
                for cam in caminos(a, b):
                    tramos = [(cam[i], cam[i+1]) for i in range(len(cam)-1)
                              if cam[i] != cam[i+1]]
                    if all(libre(net, capa, p, q, ancho_de(net))
                           for p, q in tramos):
                        elegido = (capa, tramos)
                        break
                if elegido:
                    break
            if not elegido:
                sin_rutear.append(f"{net}: {a} -> {b}")
                hechos.append(b)
                continue
            capa, tramos = elegido
            for p, q in tramos:
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(mm(p[0]), mm(p[1])))
                tr.SetEnd(pcbnew.VECTOR2I(mm(q[0]), mm(q[1])))
                w = ancho_de(net)
                tr.SetWidth(mm(w))
                tr.SetLayer(capa)
                tr.SetNet(board.FindNet(net))
                board.Add(tr)
                clave = len(puestos)
                puestos.append((net, capa, p, q, w))
                x0, x1 = sorted((p[0], q[0]))
                y0, y1 = sorted((p[1], q[1]))
                indexar(idx_puestos, clave, x0, y0, x1, y1)
                n_seg += 1
            if capa == pcbnew.B_Cu:
                for punto in (a, b):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I(mm(punto[0]), mm(punto[1])))
                    v.SetDrill(mm(0.3))
                    v.SetWidth(mm(VIA_D))
                    v.SetNet(board.FindNet(net))
                    board.Add(v)
                    clave = len(vias)
                    vias.append((net, punto[0], punto[1], VIA_D / 2))
                    indexar(idx_vias, clave, punto[0], punto[1], punto[0], punto[1])
                    n_via += 1
            hechos.append(b)
    return n_seg, n_via, sin_rutear


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

    # cada plano tiene que seguir siendo UNA sola isla: es la comprobacion
    # real de la asimetria de ruteo (ver rutear_todo), no una cuenta de
    # pistas por capa.
    for n in ("GNDA", "GNDD"):
        if n in zonas:
            islas = zonas[n].GetFilledPolysList(pcbnew.B_Cu).OutlineCount()
            if islas != 1:
                fallos.append(f"el plano {n} quedo partido en {islas} islas: "
                              f"alguna pista de B.Cu lo corta y la corriente "
                              f"de retorno tiene que rodear")

    # cada pieza en su dominio, y el EP de cada SSI2130 sin via encima
    ep_vias = []
    ep_centros = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("H"):
            continue
        for pad in fp.Pads():
            k, red = f"{ref}-{pad.GetNumber()}", pad.GetNetname()
            px, py = pad.GetX() / 1e6, pad.GetY() / 1e6
            if red == "GNDD" and not en_isla(px, py):
                fallos.append(f"{k} es GNDD pero cae fuera de la isla")
            if red == "GNDA" and en_isla(px, py):
                fallos.append(f"{k} es GNDA pero cae dentro de la isla")
            if pad.GetNumber() == "33" and ref[1:].isdigit() and 1 <= int(ref[1:]) <= 4:
                if not red.startswith("unconnected-"):
                    fallos.append(f"{k} (EP): tiene red '{red}', tiene que "
                                  f"quedar SIN red (datasheet pag.6)")
                ep_centros[ref] = (px, py)
    for t in board.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA):
            continue
        vx, vy = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
        for ref, (ex, ey) in ep_centros.items():
            if abs(vx - ex) < 1.325 + 0.3 and abs(vy - ey) < 1.325 + 0.3:
                ep_vias.append(f"via en ({vx:.2f},{vy:.2f}) cerca del EP de {ref}")
    fallos += ep_vias

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


if __name__ == "__main__":
    main()
