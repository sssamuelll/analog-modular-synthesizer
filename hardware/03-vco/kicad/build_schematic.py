"""Genera sam17-vco.kicad_sch: alimentacion local, referencia unica y los 15
test points del modulo VCO x4 (SSI2130).

    python build_schematic.py

Escribe el s-expr directamente y verifica con kicad-cli, igual que el bus
board y el modulo 2 (hardware/tools/README.md).

Esta es la Tarea 2 del epic: deja el esqueleto -- alimentacion y referencia
-- listo para que la Tarea 3 (bloque digital: 74HC14, TMP1075, EEPROM, J2) y
la Tarea 4 (las 4 voces: SSI2130 x4 + DAC x3) extiendan `construir()` con sus
propios bloques (`bloque_digital()`, `voz(idx)`), sin tener que tocar nada de
lo de aqui.

LAS DECISIONES QUE NO SON OBVIAS DE ESTA PLACA:

1. **V+ LOCAL A 5 V, NO A LOS 12 DEL BUS.** El bus solo trae +-12V, pero ni
   el DAC (AD5686R, VDD max 5.5V) ni la referencia (ADR4525, igual) los
   aguantan. Por eso U11 (78L05) baja +12V -> +5V_LOC antes de que toque
   ningun chip logico, y U12 (LD1117-3.3) saca de ahi +3V3_LOC para
   VLOGIC/I2C -- la misma razon que en el modulo 2: VIH sube con VDD, y a
   5V el bus digital se queda sin margen.

2. **UNA SOLA REFERENCIA para toda la placa, y la interna de cada DAC se
   apaga por firmware** (bom.csv, registro 0111). Sin esto cada uno de los
   tres DAC deriva por su cuenta y las cuatro voces se desafinan entre si
   aunque cada una calibre bien sola. VREF_2V5 (U8, ADR4525, 2ppm/C max)
   alimenta los tres DAC Y el pin VREF de los cuatro SSI2130: un solo
   numero, una sola deriva.

3. **TRIMLESS.** R_SCALE (26.7k, EXPO_SCALE) y R_PITCH (16.5k) son fijas
   (bom.csv, sin trim de fabrica): la precision de afinacion no la da un
   trimmer que alguien tiene que ajustar, la da esta referencia de 2ppm/C
   mas resistencias del 1%. Por eso U8 le importa a la placa entera y
   lleva su propio 100nF de entrada + 1uF de salida, no el generico 100nF
   que llevan los demas chips.

GNDA/GNDD entran por J1/J2 sin generarse en esta placa (igual que el modulo
2): GNDA es la masa de TODO lo analogico -- los tres GND de U11/U12/U8 van
ahi --, GNDD es el retorno del bloque digital que anade la Tarea 3. No se
tocan entre si en esta placa.

Nota tecnica sobre potencia(): +5V_LOC, +3V3_LOC y VREF_2V5 no tienen forma
propia en la libreria de KiCad (son rieles locales de esta placa, no un
riel de fabrica). Se resuelve pidiendo prestada la forma de un riel
estandar (+5V, +3V3, +2V5) y pisandole el campo Value con el nombre real:
es la tecnica normal de KiCad para nombrar un riel que no viene de fabrica
-- la conectividad de un simbolo de potencia la decide el texto de Value,
no el lib_id (confirmado en power:+5V: pin sin nombre, y su Description
dice literal "creates a global label with name...").
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "..", "tools"))
import schcheck  # noqa: E402
import symlib  # noqa: E402

symlib.anadir_ruta(DIR)

SCH = os.path.join(DIR, "sam17-vco.kicad_sch")
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
KICAD_FP = os.environ.get(
    "KICAD_FOOTPRINTS", r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

REV, DATE = "A", "2026-08-16"
SHEET_UUID = "b0a17ea5-0000-4000-8000-11d1c0000003"
G = 1.27


def g(n: float) -> float:
    return round(n * G, 3)


# --------------------------------------------------------------- simbolos
# Tareas 3-4 anaden aqui sus propias claves ("vco", "dac", "eeprom", "sw14",
# "tempsens", "jack", los conectores J2/J_CV/J_OUT...) sin tocar lo de arriba.
SYM = {
    "conn4": "Connector:Conn_01x04_Pin",
    "reg5": "Regulator_Linear:L78L05_SOT89",
    "reg33": "Regulator_Linear:LD1117S33TR_SOT223",
    "vref": "Reference_Voltage:ADR4525",
    "c": "Device:C",
    "tp": "Connector:TestPoint",
    # Tarea 3: cadena DAC + mazo + telemetria
    "dac": "sam17:AD5686RBRUZ",
    "r": "Device:R",
    "hc14": "74xx:74HC14",
    "tempsens": "Sensor_Temperature:TMP1075DGK",
    "eeprom": "Memory_EEPROM:24AA02E-OT",
    "j2": "Connector_Generic:Conn_02x06_Odd_Even",
}
FP = {
    "conn4": "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
    "reg5": "Package_TO_SOT_SMD:SOT-89-3",
    "reg33": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "vref": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "c": "Capacitor_SMD:C_0805_2012Metric",
    "tp": "TestPoint:TestPoint_Pad_D2.0mm",
    "dac": "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
    "r": "Resistor_SMD:R_0805_2012Metric",
    "hc14": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "tempsens": "Package_SO:VSSOP-8_3x3mm_P0.65mm",
    "eeprom": "Package_TO_SOT_SMD:SOT-23-5",
    "j2": "Connector_IDC:IDC-Header_2x06_P2.54mm_Vertical",
}

_wires: list = []
_juncs: list = []
_labels: list = []
_ncs: list = []
_syms: list = []          # (lib, unidad, ref, val, x, y, rot, clave_fp)
_libs: set = set()


def uid() -> str:
    return str(uuid.uuid4())


def hilo(x1, y1, x2, y2) -> None:
    assert (round(x1, 3), round(y1, 3)) != (round(x2, 3), round(y2, 3)), \
        f"cable de longitud cero en {x1},{y1}"
    _wires.append((round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)))


def pon(clave: str, ref: str, val: str, x: float, y: float,
        rot: int = 0, unidad: int = 1) -> None:
    _libs.add(SYM[clave])
    _syms.append((SYM[clave], unidad, ref, val, x, y, rot, clave))


def P(clave: str, num: str, x: float, y: float, rot: int = 0):
    return symlib.pin_abs(SYM[clave], num, x, y, rot)


# Los tres rieles LOCALES no tienen simbolo de fabrica: se reutiliza la
# forma de un riel estandar y se pisa el Value con el nombre real (ver nota
# tecnica en el docstring). GNDA/GNDD/+12V/-12V si existen en la libreria de
# potencia de KiCad, asi que ahi no hace falta prestar nada.
POWER_SHAPE = {"+5V_LOC": "+5V", "+3V3_LOC": "+3V3", "VREF_2V5": "+2V5"}


def potencia(net: str, x: float, y: float, ref: str, rot: int = 0) -> None:
    forma = POWER_SHAPE.get(net, net)
    _libs.add(f"power:{forma}")
    _syms.append((f"power:{forma}", 1, ref, net, x, y, rot, None))


def stub(clave: str, num: str, ox: float, oy: float, rot: int,
         net: str | None, largo: float = g(4), unidad: int = 1) -> None:
    """Saca un rabito del pin y le cuelga la etiqueta de su red (o un NC)."""
    px, py = symlib.pin_abs(SYM[clave], num, ox, oy, rot)
    if net is None:
        _ncs.append((px, py))
        return
    dx, dy = symlib.pin_dir(SYM[clave], num, rot, unidad)
    fx, fy = round(px + dx * largo, 3), round(py + dy * largo, 3)
    hilo(px, py, fx, fy)
    _labels.append((net, fx, fy))


def bloque(clave: str, ref: str, val: str, x: float, y: float, rot: int,
           redes: dict, largo: float = g(4)) -> None:
    """Coloca un componente y le cuelga un stub+etiqueta a CADA patilla.

    Las patillas que no aparecen en `redes` reciben un no-connect explicito:
    dejarlas mudas es como el ERC se salta un pin olvidado.
    """
    pon(clave, ref, val, x, y, rot)
    for num in symlib.pines(SYM[clave]):
        stub(clave, num, x, y, rot, redes.get(num), largo)


# --------------------------------------------------------------------- mapa
# Todo el bloque de alimentacion en una franja horizontal, para que la Tarea
# 3 pueda seguir hacia la derecha (bloque digital) y la Tarea 4 hacia abajo
# (las 4 voces) sin tener que reordenar nada de esto.
X_J1, Y_J1 = g(20), g(30)
X_FLG, Y_FLG0 = g(50), g(10)
X_U11, Y_U11 = g(90), g(20)
X_U12, Y_U12 = g(120), g(20)
X_U8, Y_U8 = g(150), g(20)
X_TP0, Y_TP = g(20), g(80)
TP_PITCH = g(12)

# Los 15 TP de la tabla maestra del plan (bom.csv). CV_PITCH_x y MIXO_x
# quedan con su red puesta aunque hoy sean redes de un solo miembro -- las
# Tareas 3-4 las completan cableando el resto sin volver a tocar esta lista.
TESTPOINTS = ["+12V", "-12V", "+5V_LOC", "+3V3_LOC", "VREF_2V5",
              "CV_PITCH_1", "CV_PITCH_2", "CV_PITCH_3", "CV_PITCH_4",
              "MIXO_1", "MIXO_2", "MIXO_3", "MIXO_4", "GNDA", "GNDD"]

# El bloque digital de la Tarea 3 sigue hacia la DERECHA de la alimentacion
# (que termina en X~g(190)) y se queda por debajo de Y~g(150): la Tarea 4
# tiene toda la franja de abajo libre para las 4 voces.
X_DAC = g(220)
Y_DAC1, Y_DAC2, Y_DAC3 = g(15), g(65), g(115)   # U5, U6, U7 en columna
X_HC14, Y_HC14_0, HC14_PITCH = g(270), g(10), g(12)  # U10, 6 unidades + comun
X_TEMP, Y_TEMP = g(300), g(100)                 # U13
X_EEPROM, Y_EEPROM = g(300), g(125)              # U14
X_PU, Y_PU = g(320), g(112)                      # R_I2C1-2 (pullups 4.7k)
X_J2, Y_J2 = g(340), g(60)                       # J2 (IDC 2x6)

# J2 (IDC 2x6): CONTRATO del enlace -- misma tabla, mismas posiciones, en los
# modulos 5, 6 y 7 (spec par.7). Se deja comentada a proposito -- vive como
# texto de referencia, no como dict vivo: sus claves son int y el resto del
# script usa claves str (las que da symlib.pines()), asi que si alguien la
# reutilizara tal cual para cablear se rompería en silencio (redes.get("1")
# nunca encontraría la clave 1). El cableado real de J2 esta mas abajo, en
# bloque_digital(), con las mismas redes escritas con claves str.
#
# J2_PINOUT = {  # contrato del enlace — modulos 5/6/7 usan las mismas posiciones
#     1: "SPI_SCLK", 2: "GNDD",   3: "SPI_MOSI", 4: "SPI_MISO",
#     5: "SPI_CS3",  6: "GNDD",   7: "I2C_SDA",  8: "I2C_SCL",
#     9: "TUNE_OUT_1", 10: "TUNE_OUT_2", 11: "TUNE_OUT_3", 12: "TUNE_OUT_4",
# }


# --------------------------------------------------------------- construccion
def bloque_alimentacion() -> None:
    """J1 (bus +12/G/G/-12), los dos reguladores locales y la referencia."""
    bloque("conn4", "J1", "PSU +12/G/G/-12", X_J1, Y_J1, 0,
           {"1": "+12V", "2": "GNDA", "3": "GNDA", "4": "-12V"})

    # Banderas: +12V/-12V/GNDA/GNDD no se generan en esta placa, solo entran
    # por el conector -- sin PWR_FLAG el ERC dice que nadie alimenta el pin
    # power_in que los consume (U11 IN, los tres GND...). Los rieles que SI
    # se generan aqui (+5V_LOC, +3V3_LOC, VREF_2V5) no necesitan bandera: su
    # propio pin de salida ya es power_out y con eso el ERC se da por
    # satisfecho.
    for i, net in enumerate(("+12V", "-12V", "GNDA", "GNDD")):
        ref = f"#FLG{i + 1}"
        y = Y_FLG0 + g(8) * i
        _libs.add("power:PWR_FLAG")
        hilo(X_FLG, y, X_FLG + g(4), y)
        _labels.append((net, X_FLG, y))
        _syms.append(("power:PWR_FLAG", 1, ref, "PWR_FLAG",
                       X_FLG + g(4), y, 0, None))

    # U11: 78L05, +12V -> +5V_LOC (~20mA, bom.csv)
    bloque("reg5", "U11", "L78L05", X_U11, Y_U11, 0,
           {"1": "+5V_LOC", "2": "GNDA", "3": "+12V"})

    # U12: LD1117-3.3, +5V_LOC -> +3V3_LOC
    bloque("reg33", "U12", "LD1117S33TR", X_U12, Y_U12, 0,
           {"1": "GNDA", "2": "+3V3_LOC", "3": "+5V_LOC"})

    # U8: ADR4525, +5V_LOC -> VREF_2V5. LA referencia de la placa entera.
    # Value = ADR4525BRZ (grado B): el spec dice que el grado A revienta el
    # presupuesto de afinacion. El lib_id se queda en Reference_Voltage:ADR4525
    # (asi resuelve KiCad el simbolo); el Value es la pieza que se compra de
    # verdad, igual que AD5686RBRUZ/TL074H en el modulo 2.
    bloque("vref", "U8", "ADR4525BRZ", X_U8, Y_U8, 0,
           {"1": None, "2": "+5V_LOC", "3": None, "4": "GNDA", "5": None,
            "6": "VREF_2V5", "7": None, "8": None})

    # Bulk de 10uF en cada riel local, pegado a la salida de su regulador.
    for ref, net, x, y in (("C8", "+5V_LOC", X_U11 + g(16), Y_U11),
                            ("C9", "+3V3_LOC", X_U12 + g(16), Y_U12)):
        pon("c", ref, "10u", x, y)
        c1, c2 = P("c", "1", x, y), P("c", "2", x, y)
        hilo(*c1, c1[0], c1[1] - g(4))
        _labels.append((net, c1[0], c1[1] - g(4)))
        hilo(*c2, c2[0], c2[1] + g(4))
        potencia("GNDA", c2[0], c2[1] + g(4), f"#PWRB{ref}")

    # Desacoplo de U8: 100n en la entrada (aisla el regulador previo), 1u en
    # la salida -- el que de verdad importa, porque el ruido de la
    # referencia se ve multiplicado por la ganancia de cada DAC.
    for ref, net, val, x in (("C10", "+5V_LOC", "100n", X_U8 + g(16)),
                              ("C11", "VREF_2V5", "1u", X_U8 + g(28))):
        pon("c", ref, val, x, Y_U8)
        c1, c2 = P("c", "1", x, Y_U8), P("c", "2", x, Y_U8)
        hilo(*c1, c1[0], c1[1] - g(4))
        _labels.append((net, c1[0], c1[1] - g(4)))
        hilo(*c2, c2[0], c2[1] + g(4))
        potencia("GNDA", c2[0], c2[1] + g(4), f"#PWRV{ref}")


def bloque_testpoints() -> None:
    """Los 15 TP de TESTPOINTS, en una fila propia debajo del circuito."""
    for i, net in enumerate(TESTPOINTS):
        x = X_TP0 + TP_PITCH * i
        bloque("tp", f"TP{i + 1}", net, x, Y_TP, 0, {"1": net})


# Pines ESTATICOS del AD5686R, iguales en los tres DAC (U5-U7). Mismo
# tratamiento que decidio el modulo 2 para LDAC/GAIN/RSTSEL -- a GNDA los
# tres: LDAC bajo = cada escritura SPI actualiza la salida al vuelo (no hace
# falta pulso de carga sincrona), GAIN bajo = x1 (salida 0-2.5V, que es lo
# que pide el spec par.4: R_PITCH/R_SCALE estan dimensionadas para VREF de
# 2.5V, no 5V), RSTSEL bajo = al arrancar cae a fondo de escala CERO (con
# RSTSEL alto arrancaria a media escala y las 4 voces sonarian una nota sola
# al encender).
#
# RESET es la excepcion: el modulo 2 lo ata a un GPIO del Pi (DAC_RESET) para
# que el firmware pueda resetear el chip por software. Esta placa NO tiene
# esa linea -- el contrato del enlace serie (J2_PINOUT arriba) no reserva un
# pin de reset, solo SPI+I2C+TUNE_OUT. Sin GPIO que lo controle, dejarlo a
# GNDA lo dejaria en reset PERMANENTE (activo bajo, ~RESET) y el DAC nunca
# arrancaria. Se ata a VLOGIC (+3V3_LOC): inactivo, el chip queda fuera de
# reset todo el tiempo, que es el equivalente estatico correcto cuando no
# hay quien lo controle.
_DAC_STATICOS = {
    "1": "VREF_2V5", "4": "GNDA", "5": "+5V_LOC", "11": "+3V3_LOC",
    "9": "GNDA", "10": "GNDA", "16": "GNDA", "15": "+3V3_LOC",
}


def revisar_pinout_dac() -> None:
    """El AD5686R lo dibujamos nosotros (sam17.kicad_sym) -- se contrasta aqui
    igual que en el modulo 2, mismo motivo: TSSOP-16 y LFCSP-16 van
    desfasados dos pines y copiar el diagrama equivocado pone VDD donde va
    una salida analogica."""
    esperado = {"1": "VREF", "2": "VOUTB", "3": "VOUTA", "4": "GND",
                "5": "VDD", "6": "VOUTC", "7": "VOUTD", "8": "SDO",
                "9": "LDAC", "10": "GAIN", "11": "VLOGIC", "12": "SCLK",
                "13": "SYNC", "14": "SDIN", "15": "RESET", "16": "RSTSEL"}
    import re
    b = symlib.extraer(SYM["dac"])
    got = {}
    for m in re.finditer(r"\(pin\s", b):
        w = b[m.start():m.start() + 400].replace("\n", " ")
        nm = re.search(r'\(name "([^"]+)"', w)
        nu = re.search(r'\(number "([^"]+)"', w)
        if nm and nu:
            got[nu.group(1)] = nm.group(1).replace("~{", "").replace("}", "")
    assert got == esperado, f"pinout del DAC mal: {got}"


def bloque_dac() -> None:
    """3x AD5686R en cadena soldada (DCEN): U5.SDO->U6.SDIN->U7.SDO->MISO.

    Sin capacitores de desacoplo propios -- a diferencia del DAC unico del
    modulo 2 (C5-C7), esta tarea no los pide (bom.csv reserva C_DEC* para
    todo el modulo, y el layout de la Tarea 6 es quien decide donde va cada
    100nF pegado a cada chip). ponytail: si una revision de diseno los
    quiere ya en el esquematico, es un bloque de 3 capacitores trivial de
    anadir aqui, igual que hace bloque_alimentacion() con C10/C11.
    """
    # U5: canales A-D = CV_PITCH 1-4. Primero de la cadena: SDIN <- SPI_MOSI.
    bloque("dac", "U5", "AD5686RBRUZ", X_DAC, Y_DAC1, 0, {
        **_DAC_STATICOS, "14": "SPI_MOSI", "12": "SPI_SCLK", "13": "SPI_CS3",
        "8": "DAC_LINK_12",
        "3": "CV_PITCH_1", "2": "CV_PITCH_2", "6": "CV_PITCH_3", "7": "CV_PITCH_4",
    }, largo=g(6))

    # U6: A=PWM (compartido por las 4 voces), B-D = mezcla sierra/tri/pulso.
    bloque("dac", "U6", "AD5686RBRUZ", X_DAC, Y_DAC2, 0, {
        **_DAC_STATICOS, "14": "DAC_LINK_12", "12": "SPI_SCLK", "13": "SPI_CS3",
        "8": "DAC_LINK_23",
        "3": "PWM_CV", "2": "MIX_SAW", "6": "MIX_TRI", "7": "MIX_PULSE",
    }, largo=g(6))

    # U7: A=mezcla de seno. B-D quedan de RESERVA (spec par.6: "ch 10-12 de
    # reserva, un parametro futuro cuesta cero hilos") -- NC con su cruz, no
    # etiquetas colgando de nada. Ultimo de la cadena: SDO -> SPI_MISO.
    bloque("dac", "U7", "AD5686RBRUZ", X_DAC, Y_DAC3, 0, {
        **_DAC_STATICOS, "14": "DAC_LINK_23", "12": "SPI_SCLK", "13": "SPI_CS3",
        "8": "SPI_MISO",
        "3": "MIX_SINE", "2": None, "6": None, "7": None,
    }, largo=g(6))


# Unidad de 74HC14 -> (pin de entrada, pin de salida), sacado con symlib
# directamente del simbolo (74xx:74HC14 no viene documentado pin a pin en
# ningun sitio del repo, y el orden de un inversor multi-unidad no es obvio
# a ojo). Unidad 7 es la comun: GND=pin7, VCC=pin14.
_HC14_UNIDADES = [(1, "1", "2"), (2, "3", "4"), (3, "5", "6"),
                  (4, "9", "8"), (5, "11", "10"), (6, "13", "12")]


def bloque_hc14() -> None:
    """U10: Schmitt trigger que limpia SQUARE_OUT (open-collector, RC del
    pullup) antes del TUNE_OUT digital. 4 de las 6 puertas en uso; las 2
    sobrantes con la entrada a GNDD y la salida en NC (spec par.6)."""
    for i, (u, pin_in, pin_out) in enumerate(_HC14_UNIDADES):
        y = Y_HC14_0 + HC14_PITCH * i
        pon("hc14", "U10", "74HC14", X_HC14, y, 0, unidad=u)
        if i < 4:
            n_in, n_out = f"SQ_{i + 1}", f"TUNE_OUT_{i + 1}"
        else:
            n_in, n_out = "GNDD", None
        stub("hc14", pin_in, X_HC14, y, 0, n_in, g(4), unidad=u)
        stub("hc14", pin_out, X_HC14, y, 0, n_out, g(4), unidad=u)

    # unidad comun: VCC a 3.3V (nunca 5V -- mismo umbral VIH que el DAC),
    # GND al retorno digital.
    y7 = Y_HC14_0 - HC14_PITCH
    pon("hc14", "U10", "74HC14", X_HC14, y7, 0, unidad=7)
    stub("hc14", "14", X_HC14, y7, 0, "+3V3_LOC", g(4), unidad=7)
    stub("hc14", "7", X_HC14, y7, 0, "GNDD", g(4), unidad=7)


def bloque_telemetria() -> None:
    """U13 (sensor de temperatura) + U14 (EEPROM de identidad), mismo bus
    I2C con pullups 4.7k. Los dos con GND en GNDD -- es el retorno de todo
    lo digital, no de los DAC (que van a GNDA con el resto del audio)."""
    # U13: TMP1075DGK. Direccion por straps = 0 (A2/A1/A0 los tres a GNDD).
    # Los modulos 5/6/7 usaran las direcciones 1/2/3 -- otra combinacion de
    # straps, mismo sensor, mismo bus. ALERT sin usar: NC (no hay linea de
    # interrupcion en el contrato del enlace, J2_PINOUT arriba).
    bloque("tempsens", "U13", "TMP1075DGK", X_TEMP, Y_TEMP, 0, {
        "1": "I2C_SDA", "2": "I2C_SCL", "3": None, "4": "GNDD",
        "5": "GNDD", "6": "GNDD", "7": "GNDD", "8": "+3V3_LOC",
    })

    # U14: 24AA02E-OT en la libreria de KiCad = 24AA02E48 real (bom.csv:
    # mismo pinout, sin el sufijo E48 en el simbolo de sistema). Pin 5 no se
    # cablea con bloque() (que le pondria una cruz de no-conexion): en el
    # propio simbolo ya esta tipado "no_connect" -- el mismo caso que el EP
    # del SSI2130 (Tarea 1). Un pin no_connect no lleva NADA encima, ni
    # siquiera la cruz: ponersela es un no_connect que no ancla a ningun
    # cable ("no_connect_dangling" en el ERC), justo el fallo que ya se
    # evito en el EP.
    pon("eeprom", "U14", "24AA02E48", X_EEPROM, Y_EEPROM, 0)
    for num, net in (("1", "I2C_SCL"), ("2", "GNDD"),
                      ("3", "I2C_SDA"), ("4", "+3V3_LOC")):
        stub("eeprom", num, X_EEPROM, Y_EEPROM, 0, net)

    # R_I2C1-2 (bom.csv): pullups del bus, a +3V3_LOC -- nunca a +5V, mismo
    # motivo VIH que todo lo demas de este bloque.
    for i, (ref, net) in enumerate((("R_I2C1", "I2C_SDA"), ("R_I2C2", "I2C_SCL"))):
        x = X_PU + g(10) * i
        pon("r", ref, "4.7k", x, Y_PU)
        p1, p2 = P("r", "1", x, Y_PU), P("r", "2", x, Y_PU)
        hilo(*p1, p1[0], p1[1] - g(4))
        _labels.append((net, p1[0], p1[1] - g(4)))
        hilo(*p2, p2[0], p2[1] + g(4))
        _labels.append(("+3V3_LOC", p2[0], p2[1] + g(4)))


def bloque_mazo() -> None:
    """J2: el conector fisico del contrato de enlace (J2_PINOUT arriba),
    cableado con las mismas 12 redes -- por posicion, tal cual la tabla."""
    bloque("j2", "J2", "Mazo digital IDC 2x6", X_J2, Y_J2, 0, {
        "1": "SPI_SCLK", "2": "GNDD", "3": "SPI_MOSI", "4": "SPI_MISO",
        "5": "SPI_CS3", "6": "GNDD", "7": "I2C_SDA", "8": "I2C_SCL",
        "9": "TUNE_OUT_1", "10": "TUNE_OUT_2", "11": "TUNE_OUT_3", "12": "TUNE_OUT_4",
    })


def bloque_digital() -> None:
    bloque_dac()
    bloque_hc14()
    bloque_telemetria()
    bloque_mazo()


def construir() -> None:
    bloque_alimentacion()
    bloque_testpoints()
    bloque_digital()
    # Tarea 4: voz(idx) x4 -- SSI2130, jacks CV-IN/OUT. Cierra los avisos que
    # deja pendientes esta tarea: SQ_1..4 colgantes (los produce el SQUARE
    # OUT de cada voz) y PWM_CV/MIX_* de un solo miembro (los consume el
    # mezclador interno de cada SSI2130).


# ------------------------------------------------------------ comprobaciones
def check_footprints() -> None:
    """Antes de tocar el fichero, a proposito (leccion del modulo 1)."""
    rotos = []
    for clave, fp in FP.items():
        lib, _, nombre = fp.partition(":")
        base = (os.path.join(DIR, "sam17.pretty") if lib == "sam17"
                else os.path.join(KICAD_FP, f"{lib}.pretty"))
        if not os.path.isfile(os.path.join(base, f"{nombre}.kicad_mod")):
            rotos.append(f"{clave} -> {fp}")
    assert not rotos, f"huellas que no estan en disco: {rotos}"


def revisar_rejilla() -> None:
    fuera = [v for x1, y1, x2, y2 in _wires for v in (x1, y1, x2, y2)
             if abs(round(v / G) * G - v) > 1e-6]
    fuera += [f"{s[2]}:{v}" for s in _syms for v in (s[4], s[5])
              if abs(round(v / G) * G - v) > 1e-6]
    assert not fuera, f"fuera de rejilla de {G} mm: {sorted(set(map(str, fuera)))[:8]}"


def revisar_fusiones() -> None:
    """Que no haya dos redes distintas unidas por un solape o una T.

    Ver hardware/tools/schcheck.py -- ya paso dos veces en este repo y las
    dos llego al ERC en vez de saltar aqui.
    """
    pot = [(v, x, y) for lib, _u, _r, v, x, y, _rot, k in _syms
           if k is None and lib.startswith("power:") and not v.startswith("PWR")]
    malas = schcheck.redes_fusionadas(_wires, _labels, pot)
    assert not malas, "redes fusionadas:\n  " + "\n  ".join(malas)


def revisar_hilos() -> None:
    """Ningun extremo de cable en el aire. KiCad une pin y cable con ~1 mm de
    tolerancia y el ERC da por bueno un trazado torcido; aqui se exige
    coincidencia exacta."""
    anclas = {(round(x, 3), round(y, 3)) for _n, x, y in _labels}
    anclas |= {(round(x, 3), round(y, 3)) for x, y in _ncs}
    for lib, unidad, _ref, _v, x, y, rot, _k in _syms:
        for num in symlib.pines(lib):
            anclas.add(symlib.pin_abs(lib, num, x, y, rot))
    cuenta: dict = {}
    for x1, y1, x2, y2 in _wires:
        for p in ((x1, y1), (x2, y2)):
            cuenta[p] = cuenta.get(p, 0) + 1
    sueltos = [p for p, n in cuenta.items() if n == 1 and p not in anclas]
    assert not sueltos, f"extremos de cable en el aire: {sueltos[:8]}"


def escribir() -> None:
    out = ['(kicad_sch', '\t(version 20260101)', '\t(generator "sam17-vco")',
           '\t(generator_version "10.0")', f'\t(uuid {SHEET_UUID})',
           '\t(paper "A3")', '\t(title_block',
           '\t\t(title "Modulo 03 - VCO x4 SSI2130: alimentacion, referencia y 4 voces")',
           f'\t\t(date "{DATE}")', f'\t\t(rev "{REV}")',
           '\t\t(company "SAM17 - Sintetizador analogico modular")',
           '\t\t(comment 1 "V+ local a 5V (U11) y 3V3 (U12), no a los 12V del bus: ni el DAC ni la ref los aguantan")',
           '\t\t(comment 2 "Referencia UNICA (U8, ADR4525): la interna de cada DAC se apaga por firmware, reg 0111")',
           '\t\t(comment 3 "Trimless: precision de R_PITCH/R_SCALE fijas + ref 2ppm/C, no un trimmer de fabrica")',
           '\t\t(comment 4 "GNDA (bus, J1) y GNDD (mazo digital, J2 en Tarea 3) NO se unen en esta placa")',
           '\t)', '\t(lib_symbols']
    for lib in sorted(_libs):
        out.append("\t\t" + symlib.extraer(lib).replace("\n", "\n\t\t"))
    out.append('\t)')

    for x1, y1, x2, y2 in _wires:
        out += ['\t(wire', '\t\t(pts', f'\t\t\t(xy {x1} {y1}) (xy {x2} {y2})',
                '\t\t)', '\t\t(stroke', '\t\t\t(width 0)',
                '\t\t\t(type default)', '\t\t)', f'\t\t(uuid "{uid()}")', '\t)']
    for x, y in sorted(set(_juncs)):
        out += ['\t(junction', f'\t\t(at {x} {y})', '\t\t(diameter 0)',
                '\t\t(color 0 0 0 0)', f'\t\t(uuid "{uid()}")', '\t)']
    for x, y in _ncs:
        out += ['\t(no_connect', f'\t\t(at {x} {y})', f'\t\t(uuid "{uid()}")', '\t)']
    for nombre, x, y in _labels:
        out += [f'\t(label "{nombre}"', f'\t\t(at {x} {y} 0)', '\t\t(effects',
                '\t\t\t(font', '\t\t\t\t(size 1.27 1.27)', '\t\t\t)',
                '\t\t\t(justify left bottom)', '\t\t)',
                f'\t\t(uuid "{uid()}")', '\t)']

    for lib, unidad, ref, val, x, y, rot, clave in _syms:
        fp = FP.get(clave, "")
        oculto = ref.startswith("#")
        out += ['\t(symbol', f'\t\t(lib_id "{lib}")', f'\t\t(at {x} {y} {rot})',
                f'\t\t(unit {unidad})', '\t\t(exclude_from_sim no)',
                f'\t\t(in_bom {"no" if oculto else "yes"})',
                f'\t\t(on_board {"no" if oculto else "yes"})', '\t\t(dnp no)',
                f'\t\t(uuid "{uid()}")']
        campos = [("Reference", ref, y - g(7), oculto),
                  ("Value", val, y + g(7), False),
                  ("Footprint", fp, y, True), ("Datasheet", "", y, True),
                  ("Description", "", y, True)]
        for nombre, texto, yy, esconder in campos:
            out += [f'\t\t(property "{nombre}" "{texto}"',
                    f'\t\t\t(at {x} {round(yy, 2)} 0)']
            if esconder:
                out.append('\t\t\t(hide yes)')
            out += ['\t\t\t(show_name no)', '\t\t\t(do_not_autoplace no)',
                    '\t\t\t(effects', '\t\t\t\t(font',
                    '\t\t\t\t\t(size 1.27 1.27)', '\t\t\t\t)', '\t\t\t)', '\t\t)']
        for num in sorted(symlib.pines(lib, unidad if unidad > 0 else None)):
            out += [f'\t\t(pin "{num}"', f'\t\t\t(uuid "{uid()}")', '\t\t)']
        out += ['\t\t(instances', '\t\t\t(project "sam17-vco"',
                f'\t\t\t\t(path "/{SHEET_UUID}"', f'\t\t\t\t\t(reference "{ref}")',
                f'\t\t\t\t\t(unit {unidad})', '\t\t\t\t)', '\t\t\t)', '\t\t)', '\t)']

    out += ['\t(sheet_instances', '\t\t(path "/"', '\t\t\t(page "1")',
            '\t\t)', '\t)', ')']
    with open(SCH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


def main() -> None:
    check_footprints()
    revisar_pinout_dac()
    construir()
    revisar_rejilla()
    revisar_hilos()
    revisar_fusiones()
    escribir()
    piezas = {s[2] for s in _syms if not s[2].startswith("#")}
    print(f"{len(piezas)} componentes, {len(_wires)} cables, "
          f"{len(_labels)} etiquetas, {len(_ncs)} no-connect")

    erc = subprocess.run([KICAD_CLI, "sch", "erc", "--severity-all",
                          "--exit-code-violations", SCH],
                         capture_output=True, text=True)
    print(erc.stdout.strip()[-800:] or erc.stderr.strip()[-800:])
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "-o",
                    os.path.join(DIR, "sam17-vco.net"), SCH],
                   capture_output=True, text=True)
    sys.exit(erc.returncode)


if __name__ == "__main__":
    main()
