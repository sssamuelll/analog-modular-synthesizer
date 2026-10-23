"""Genera sam17-power-v5.kicad_sch y exporta el netlist, a partir de bom.csv.

    python build_schematic.py

Escribe el s-expr DIRECTAMENTE con symlib + schcheck, como el bus board, el
modulo 2 y el VCO (hardware/tools/README.md). La version de #474 hablaba con
un KiCAD-MCP-Server; el resultado fue una hoja con la mitad de los simbolos
propios mal numerados que ninguna puerta miro. Aqui:

  * cada patilla de cada simbolo tiene que aparecer en la tabla REDES, con su
    red o con None (no-connect explicito). Una patilla que falte es un error,
    no un NC silencioso;
  * cada patilla tiene que tener su pad en la huella, y cada pad de cobre su
    patilla (_cruzar_huellas). Es lo que habria cazado el SOT-223 del LT1963A,
    el Q2 sin pads y los TPS26630 con nueve pads al aire;
  * despues kicad-cli corre el ERC y exporta el netlist.

LAS DECISIONES QUE CORRIGEN #474 (cada una con su motivo junto a su bloque):
  M5  Q2 con la FUENTE en la entrada (proteccion de polaridad, lm74502.pdf p. 1)
      y D1 bidireccional: un TVS unidireccional en la entrada es un corto con
      el ladrillo al reves.
  M5  U16/U19 = TPS26631PWPR: la "TPS26630PWPR" de la BOM no existe (TI solo
      vende el TPS26630 en VQFN-24; tps2663.pdf, orderables).
  M5  U18 EN al aire: el EN del TPS709 aguanta 7 V y estaba en +24 V.
  D-V3 Trim de PS4/PS5 a -Vout con 45.3k: la nota de TRACO (thn15/20/30wi
      voltage adjustment) da 44.9k para 15.5 V. Con 240k a +Vout PS4 bajaba.
  #334 LC = 22 uH / 47 uF / 0.68 ohm + 220 uF: el que analizan
      rizado_budget.py y check_absmax.py. Con el de la BOM vieja U1 ve 21 V.
  D-F4 Umbral a 14.46 V con histeresis de ~31 mV (secuencia_budget.py), canal
      negativo referido a VREF y no a +5 V, y U19 FUERA del hilo SHDN_CASCADE
      (U19 alimenta el nodo que el propio detector mira: no arrancaba nunca).
  D-F6 Crowbar TL431 -> PNP -> puerta: con el anodo del TL431 en la puerta el
      umbral se corre V_GT*(1+R1/R2), de 3 a 8 V.
  Telemetria: INA226 U13/U14 con A1 a VS (0x44/0x45, no 0x48/0x49) y los
      BAT54S con el comun en la entrada del ADC.
  Cascada: R_SET = 2 x 120k en paralelo (dos LT3045/LT3094 suman 200 uA en
      SET, ltc3045 Figure 7) y PGFB a IN (si no, el arranque rapido de 2 mA no
      se apaga nunca).
  M5  SHDN de U16 con pull-down (R83) y FLT de U19 al MSP430 (R84, P1.2).
  #334 U19 sin UVLO (R82 a IN_SYS) y con Schottky de rueda libre (D19).
  D-F6 R_GK = 100 ohm: el dV/dt de 200 V/us del BT151 se garantiza con 100.
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
import tempfile
import uuid

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "..", "..", "tools"))
import schcheck  # noqa: E402
import symlib  # noqa: E402

symlib.anadir_ruta(DIR)

SCH = os.path.join(DIR, "sam17-power-v5.kicad_sch")
NET = os.path.join(DIR, "sam17-power-v5.net")
BOM = os.path.join(DIR, "..", "bom.csv")
EN_WINDOWS = os.name == "nt"
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" if EN_WINDOWS
    else "kicad-cli")
KICAD_FP = os.environ.get(
    "KICAD_FOOTPRINTS", r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
    if EN_WINDOWS else "/usr/share/kicad/footprints")

REV, DATE = "v5-B", "2026-10-22"
SHEET_UUID = "981fcf02-4c69-4923-8fc6-43cc6cc53d80"
G = 1.27


def g(n: float) -> float:
    return round(n * G, 3)


SYM = {
    "R": "Device:R", "C": "Device:C", "CP": "Device:C_Polarized",
    "L": "Device:L", "FB": "Device:FerriteBead", "F": "Device:Fuse",
    "D": "Device:D", "DZ": "Device:D_Zener", "DS": "Device:D_Schottky",
    "TVS2": "Device:D_TVS", "LED": "Device:LED", "RV": "Device:R_Potentiometer_Trim",
    "NT": "Device:NetTie_2", "BAT54S": "Diode:BAT54S",
    "TP": "Connector:TestPoint", "J1P": "Connector:Conn_01x01_Pin",
    "J2P": "Connector:Conn_01x02_Pin", "J4P": "Connector:Conn_01x04_Pin",
    "SW": "Switch:SW_Push",
    "CSD18534": "Transistor_FET:CSD18534Q5A", "PNP": "Transistor_BJT:MMBT3906",
    "TPS26631": "Power_Management:TPS26631PWP",
    "LT1963": "Regulator_Linear:LT1963AEQ", "LT3015": "Regulator_Linear:LT3015Q",
    "LT3045": "Regulator_Linear:LT3045xDD", "LT3094": "Regulator_Linear:LT3094xDD",
    "TL431": "Reference_Voltage:TL431DBZ", "LM393": "Comparator:LM393",
    "INA226": "Sensor_Energy:INA226", "ADS1115": "Analog_ADC:ADS1115IDGS",
    "TMP1075": "Sensor_Temperature:TMP1075DGK", "ISO1541": "Isolator:ISO1541",
    "LM74502": "sam17:LM74502DDF", "MSP430": "sam17:MSP430FR2111IPW16",
    "TPS709": "sam17:TPS70933DBV", "THN1": "sam17:TRACO_THN_Single",
    "THN2": "sam17:TRACO_THN_Dual", "URB": "sam17:Mornsun_URB_YMD-20WR3",
    "K78": "sam17:Mornsun_K78xxT-1000R3", "SCR": "sam17:BT151-500R",
    "FLAG": "power:PWR_FLAG",
}

# ----------------------------------------------------------------- las redes
# (ref, simbolo, bloque, {patilla: red | None}, unidad). Las pasivas de dos
# patillas se escriben como dos-tupla (red_1, red_2) con dos().
PARTES: list[tuple] = []


def P(ref: str, sym: str, bloque: str, redes: dict, unidad: int = 1) -> None:
    PARTES.append((ref, sym, bloque, redes, unidad))


def dos(ref: str, sym: str, bloque: str, red1: str, red2: str) -> None:
    P(ref, sym, bloque, {"1": red1, "2": red2})


def entrada_m5() -> None:
    b = "M5"
    P("J1", "J2P", b, {"1": "+24V_RAW", "2": "GND24"})
    P("TP1", "TP", b, {"1": "+24V_RAW"})
    P("TP2", "TP", b, {"1": "GND24"})
    # D1 BIDIRECCIONAL (SMBJ26CA): con el ladrillo al reves un unidireccional
    # conduce en directa y se come la corriente de limite del ladrillo.
    dos("D1", "TVS2", b, "+24V_RAW", "GND24")
    # Proteccion de polaridad con UN MOSFET: fuente en la entrada, drenador a
    # la carga. Su diodo de cuerpo conduce en directa al arrancar y bloquea con
    # -24 V. SRC y VS del LM74502 a la entrada (lm74502.pdf p. 1, "External
    # reverse polarity protection MOSFET"); OV a GND porque el OVP lo hace U16
    # (Table 5-1: "Connect OV pin to ground when OV feature is not used").
    P("Q2", "CSD18534", b, {"1": "+24V_RAW", "2": "+24V_RAW", "3": "+24V_RAW",
                            "4": "GATE_Q2", "5": "+24V_PROT"})
    P("U15", "LM74502", b, {"5": "+24V_RAW", "1": "+24V_RAW", "7": "GND24",
                            "2": "GND24", "6": "GATE_Q2", "8": "+24V_RAW",
                            "4": "VCAP_U15", "3": None})
    dos("C9", "C", b, "VCAP_U15", "+24V_RAW")     # C_VCAP entre VCAP y VS (p. 1)
    dos("C10", "C", b, "+24V_RAW", "GND24")       # 100 nF en VS (Table 5-1)
    # eFuse de entrada. MODE al aire = enclava tras sobrecarga (tps2663.pdf
    # Table 8-1): los reintentos los decide el MSP430 por SHDN (M5).
    P("U16", "TPS26631", b, {
        "1": "+24V_PROT", "2": "+24V_PROT", "3": "+24V_PROT", "4": None, "5": None,
        "6": "+24V_PROT", "7": "UVLO_U16", "8": "OVP_U16", "9": "GND24",
        "10": "DVDT_U16", "11": "ILIM_U16", "12": None, "13": "SHDN_M5",
        "14": None, "15": "FLT_M5", "16": "GND24", "17": None,
        "18": "+24V_SW", "19": "+24V_SW", "20": "+24V_SW", "21": "GND24"})
    # SHDN con pull-down: el pin tiene su propio pull-up (2.48..3.3 V en vacio,
    # hasta 10 uA, tps2663.pdf p. 7), asi que suelto ENCIENDE. Con 47k queda en
    # <= 0.47 V < V(SHUTF) = 0.8 V mientras el MSP430 no lo levante: al
    # enchufar, en un reset o programando, U16 sigue apagado hasta que el
    # firmware haya leido la bandera ABANDONADO de la FRAM.
    dos("R83", "R", b, "SHDN_M5", "GND24")
    dos("R11", "R", b, "ILIM_U16", "GND24")       # 18.1/4.02k = 4.50 A, < 4.875 del TE90
    # UVLO 17.9 V / OVP 32.7 V con V(UVLOR) = V(OVPR) = 1.2 V (p. 6)
    dos("R12", "R", b, "+24V_PROT", "UVLO_U16")
    dos("R13", "R", b, "UVLO_U16", "OVP_U16")
    dos("R14", "R", b, "OVP_U16", "GND24")
    dos("C11", "C", b, "DVDT_U16", "GND24")       # 1.775 uA * 25 / 22 nF = 2 V/ms
    # LDO del supervisor. 1k + zener de 24 V: D1 deja pasar hasta 42 V en un
    # transitorio y el TPS709 funciona hasta 30 V (32 V absoluto, tps709.pdf
    # p. 4). El BZT52C30 de antes llega a 32 V a solo 2 mA (diodes_bzt52.pdf
    # p. 2): ni un miliamperio de margen. check_absmax.py calcula U18 IN.
    dos("R64", "R", b, "+24V_PROT", "+24V_LDO")
    dos("D2", "DZ", b, "+24V_LDO", "GND24")
    dos("C7", "C", b, "+24V_LDO", "GND24")
    P("U18", "TPS709", b, {"1": "+24V_LDO", "3": None, "2": "GND24",
                           "5": "+3V3_MCU", "4": None})
    dos("C8", "C", b, "+3V3_MCU", "GND24")         # >= 2 uF efectivos (p. 21)
    # P1.2 lee el FLT de U19 (tope #334): un fallo de riel gasta un intento
    # (recuperacion_budget.py). Va al MCU y NO al SHDN de U16:
    # el TPS26631 baja FLT mientras su entrada esta por debajo de UVLO
    # (tps2663.pdf p. 19) y hasta 700 us despues (p. 8), asi que cableado al
    # SHDN mantendria U16 apagado en cada arranque, con +15V5_RAW subiendo.
    P("U17", "MSP430", b, {
        "5": "+3V3_MCU", "6": "GND24", "4": "MCU_RST", "3": "MCU_TEST",
        "7": None, "8": None, "2": None, "1": "FLT_M5", "16": "FLT_U19",
        "15": "SHDN_M5", "14": "LED_CTRL", "13": "SW_RESET", "12": None,
        "11": None, "10": None, "9": None})
    dos("C23", "C", b, "+3V3_MCU", "GND24")
    dos("R65", "R", b, "+3V3_MCU", "MCU_RST")      # 47k + 1 nF: compatible con SBW
    dos("C12", "C", b, "MCU_RST", "GND24")
    dos("R66", "R", b, "+3V3_MCU", "FLT_M5")       # FLT es drenador abierto
    dos("R84", "R", b, "+3V3_MCU", "FLT_U19")      # idem, el de U19
    dos("SW1", "SW", b, "SW_RESET", "GND24")
    dos("R31", "R", b, "LED_CTRL", "LED_ANODE")
    P("D18", "LED", b, {"1": "GND24", "2": "LED_ANODE"})
    P("J10", "J4P", b, {"1": "+3V3_MCU", "2": "MCU_TEST", "3": "MCU_RST", "4": "GND24"})


def convertidores() -> None:
    b = "DCDC"
    P("C14", "CP", b, {"1": "+24V_SW", "2": "GND24"})      # Cin del URB (p. 4)
    # TRACO THN: 1 +Vin, 2 -Vin, 3 +Vout, 4 Trim/Common, 5 -Vout, 6 Remote
    # (traco_thn20wi.pdf p. 4, thn30wi p. 5). Remote al aire = encendido.
    P("PS1", "THN2", b, {"1": "+24V_SW", "2": "GND24", "6": None,
                         "3": "+12V_RAW_RACK", "4": "GNDA", "5": "-12V_RAW_RACK"})
    P("PS2", "URB", b, {"3": "+24V_SW", "2": "GND24", "1": None,
                        "4": "+5V_RAW_DIG", "5": None, "6": "GNDD"})
    P("C29", "CP", b, {"1": "+5V_RAW_DIG", "2": "GNDD"})   # Cout del URB (p. 4)
    # K78: NO aislado. Su GND es el de la entrada (GND24) y la union con GNDA
    # se hace en NT1, pegada a sus pads de masa (decision de #474).
    P("PS3", "K78", b, {"1": "+24V_SW", "2": "+24V_SW", "10": None,
                        "3": "GND24", "7": "GND24", "4": "+5V_RAW_RACK",
                        "5": "+5V_RAW_RACK", "6": None})
    dos("C15", "C", b, "+24V_SW", "GND24")         # C1 10 uF/50 V (p. 4)
    dos("C16", "C", b, "+5V_RAW_RACK", "GND24")    # C2 22 uF (p. 4)
    P("NT1", "NT", b, {"1": "GND24", "2": "GNDA"})
    # +-15.5 V crudos: trim HACIA ARRIBA = resistencia de Trim a -Vout.
    P("PS4", "THN1", b, {"1": "+24V_SW", "2": "GND24", "6": None,
                         "3": "+15V5_RAW", "4": "TRIM_PS4", "5": "GNDA"})
    dos("R32", "R", b, "TRIM_PS4", "GNDA")
    P("PS5", "THN1", b, {"1": "+24V_SW", "2": "GND24", "6": None,
                         "3": "GNDA", "4": "TRIM_PS5", "5": "-15V5_RAW"})
    dos("R33", "R", b, "TRIM_PS5", "-15V5_RAW")


def tope_y_lc() -> None:
    b = "LC"
    # Tope M3 (#334) antes del LC, sensando del lado del modulo. MODE a GND =
    # reintento automatico; SHDN al aire (tiene pull-up interno, p. 7): NO va
    # al hilo D-F4, que mira la salida de este mismo eFuse. FLT al MSP430.
    # UVLO a IN_SYS por 6.8M = sin UVLO (tps2663.pdf p. 20: >= 300k si hay
    # inversion). A GND elegia el umbral interno de 15.1..15.9 V (p. 6), por
    # encima de los 15.5 V del riel que protege. Quien decide si el riel vale
    # es D-F4 (14.46 V, secuencia_budget.py), no U19.
    P("U19", "TPS26631", b, {
        "1": "+15V5_RAW", "2": "+15V5_RAW", "3": "+15V5_RAW", "4": None, "5": None,
        "6": "+15V5_RAW", "7": "UVLO_U19", "8": "OVP_U19", "9": "GNDA",
        "10": "DVDT_U19", "11": "ILIM_U19", "12": "GNDA", "13": None,
        "14": None, "15": "FLT_U19", "16": "GNDA", "17": None,
        "18": "+15V5_EFUSE", "19": "+15V5_EFUSE", "20": "+15V5_EFUSE", "21": "GNDA"})
    dos("R82", "R", b, "+15V5_RAW", "UVLO_U19")
    # Schottky de OUT a GND (tps2663.pdf p. 36 y 38): al abrir U19, la
    # corriente de L2 vuelve por aqui y no por OUT (-0.3 V absoluto, p. 5).
    dos("D19", "DS", b, "+15V5_EFUSE", "GNDA")
    dos("R34", "R", b, "ILIM_U19", "GNDA")          # 18/18.2k = 0.99 A
    dos("R35", "R", b, "+15V5_RAW", "OVP_U19")      # 1.2*(1+49.9/3.9) = 16.55 V
    dos("R36", "R", b, "OVP_U19", "GNDA")
    dos("C13", "C", b, "DVDT_U19", "GNDA")
    dos("L2", "L", b, "+15V5_EFUSE", "+15V5_LC")
    P("C3", "CP", b, {"1": "+15V5_LC", "2": "GNDA"})
    dos("C5", "C", b, "+15V5_LC", "GNDA")
    P("C1", "CP", b, {"1": "+15V5_LC", "2": "C1_NEG"})
    dos("R37", "R", b, "C1_NEG", "GNDA")
    dos("FB1", "FB", b, "+15V5_LC", "+15V5_FILT")
    dos("D10", "DZ", b, "+15V5_FILT", "GNDA")       # SMBJ16A en U1 IN
    dos("L3", "L", b, "-15V5_RAW", "-15V5_LC")
    P("C4", "CP", b, {"1": "GNDA", "2": "-15V5_LC"})
    dos("C6", "C", b, "GNDA", "-15V5_LC")
    P("C2", "CP", b, {"1": "GNDA", "2": "C2_NEG"})
    dos("R38", "R", b, "C2_NEG", "-15V5_LC")
    dos("FB2", "FB", b, "-15V5_LC", "-15V5_FILT")
    dos("D11", "DS", b, "GNDA", "-15V5_FILT")       # K a GNDA: VIN de U2 nunca > +0.3 V
    P("TP9", "TP", b, {"1": "+15V5_LC"})
    P("TP10", "TP", b, {"1": "-15V5_LC"})


def detector_df4() -> None:
    b = "DF4"
    # Canal +: SENSE_POS = 15.5 * 10/(48.1+10) sube y baja con el riel; dispara
    # a 2.495*5.81 = 14.50 V. Histeresis por R67 desde la salida.
    P("U20", "LM393", b, {"3": "SENSE_POS", "2": "VREF_2V5", "1": "SHDN_CASCADE"}, 1)
    # Canal -: el divisor va de VREF a -15.5 V y se compara con ~0 V, asi el
    # +5 V auxiliar no entra en el umbral. Dispara a 2.495*(58.3/10) = 14.55 V.
    P("U20", "LM393", b, {"5": "REF0_NEG", "6": "SENSE_NEG", "7": "SHDN_CASCADE"}, 2)
    P("U20", "LM393", b, {"8": "+5V_AUX", "4": "GNDA"}, 3)
    dos("C33", "C", b, "+5V_AUX", "GNDA")
    P("U21", "TL431", b, {"1": "VREF_2V5", "2": "VREF_2V5", "3": "GNDA"})
    dos("R63", "R", b, "+5V_AUX", "VREF_2V5")       # ~2 mA de catodo
    dos("R39", "R", b, "+15V5_LC", "SENSE_POS")
    dos("R40", "R", b, "SENSE_POS", "GNDA")
    dos("R67", "R", b, "SHDN_CASCADE", "SENSE_POS")
    dos("C34", "C", b, "SENSE_POS", "GNDA")
    dos("R41", "R", b, "VREF_2V5", "SENSE_NEG")
    dos("R42", "R", b, "SENSE_NEG", "-15V5_LC")
    dos("C35", "C", b, "SENSE_NEG", "GNDA")
    dos("R68", "R", b, "REF0_NEG", "GNDA")
    dos("R69", "R", b, "SHDN_CASCADE", "REF0_NEG")
    dos("R43", "R", b, "SHDN_CASCADE", "GNDA")      # hilo roto = apagado
    dos("R44", "R", b, "+5V_AUX", "SHDN_CASCADE")


def preregulador() -> None:
    b = "PRE"
    # LT1963AEQ (DD-PAK-5, ajustable): VADJ 1.21 V; 9.31k+RV2+1.00k cubre
    # 12.47..13.69 V con 13.10 V a media carrera.
    P("U1", "LT1963", b, {"1": "SHDN_CASCADE", "2": "+15V5_FILT", "3": "GNDA",
                          "4": "+13V1", "5": "ADJ_U1"})
    dos("R5", "R", b, "+13V1", "TRIM_U1_HI")
    P("RV2", "RV", b, {"1": "TRIM_U1_HI", "2": "ADJ_U1", "3": "ADJ_U1"})
    dos("R6", "R", b, "ADJ_U1", "GNDA")
    P("C17", "CP", b, {"1": "+13V1", "2": "GNDA"})
    dos("D12", "D", b, "+15V5_FILT", "+13V1")
    P("TP7", "TP", b, {"1": "+13V1"})
    # LT3015Q: el TAB es IN (lt3015-rev-b.pdf p. 2); el simbolo de KiCad lo
    # lleva al pad 3 de TO-263-5_TabPin3.
    P("U2", "LT3015", b, {"1": "SHDN_CASCADE", "2": "GNDA", "3": "-15V5_FILT",
                          "4": "ADJ_U2", "5": "-12V9"})
    dos("R7", "R", b, "-12V9", "TRIM_U2_HI")
    P("RV3", "RV", b, {"1": "TRIM_U2_HI", "2": "ADJ_U2", "3": "ADJ_U2"})
    dos("R8", "R", b, "ADJ_U2", "GNDA")
    P("C18", "CP", b, {"1": "GNDA", "2": "-12V9"})
    dos("D13", "D", b, "-12V9", "-15V5_FILT")
    P("TP8", "TP", b, {"1": "-12V9"})


def ultra() -> None:
    b = "ULTRA"
    for ref, out in (("U4", "OUT_U4"), ("U5", "OUT_U5")):
        P(ref, "LT3045", b, {"1": "+13V1", "2": "+13V1", "3": "+13V1", "4": None,
                             "5": "GNDA", "6": "+13V1", "7": "SET_POS", "8": "GNDA",
                             "9": "OUTS_POS", "10": out, "11": "GNDA"})
    dos("C36", "C", b, "+13V1", "GNDA")
    dos("R15", "R", b, "OUT_U4", "OUTS_POS")
    dos("R16", "R", b, "OUT_U5", "OUTS_POS")
    dos("R9", "R", b, "SET_POS", "GNDA")
    dos("R61", "R", b, "SET_POS", "GNDA")
    dos("C19", "C", b, "SET_POS", "GNDA")
    dos("C38", "C", b, "OUTS_POS", "GNDA")
    dos("R19", "R", b, "OUTS_POS", "+12V_ULTRA")
    dos("C20", "C", b, "+12V_ULTRA", "GNDA")
    for ref, out in (("U6", "OUT_U6"), ("U7", "OUT_U7")):
        P(ref, "LT3094", b, {"1": "-12V9", "2": "-12V9", "13": "-12V9",
                             "3": "-12V9", "4": None, "5": "-12V9", "6": "GNDA",
                             "7": None, "8": "SET_NEG", "9": "GNDA",
                             "10": "-12V_ULTRA", "11": out, "12": out})
    dos("C37", "C", b, "GNDA", "-12V9")
    dos("R17", "R", b, "OUT_U6", "-12V_ULTRA")
    dos("R18", "R", b, "OUT_U7", "-12V_ULTRA")
    dos("R10", "R", b, "SET_NEG", "GNDA")
    dos("R62", "R", b, "SET_NEG", "GNDA")
    dos("C21", "C", b, "SET_NEG", "GNDA")
    dos("C22", "C", b, "GNDA", "-12V_ULTRA")
    P("TP3", "TP", b, {"1": "+12V_ULTRA"})
    P("TP4", "TP", b, {"1": "-12V_ULTRA"})
    P("TP6", "TP", b, {"1": "GNDA"})
    dos("R1", "R", b, "+12V_ULTRA", "LED3_A")
    P("D3", "LED", b, {"1": "GNDA", "2": "LED3_A"})
    dos("R2", "R", b, "LED4_K", "-12V_ULTRA")
    P("D4", "LED", b, {"1": "LED4_K", "2": "GNDA"})


def _crowbar(n: int, riel: str, masa: str, q: str, u: str, scr: str,
             r_alta: str, r_baja: str, rb: str, rbe: str, rc: str, rgk: str,
             negativo: bool = False) -> None:
    """TL431 -> PNP -> puerta del SCR. El TL431 mide el riel CON SU ANODO EN LA
    REFERENCIA DEL RIEL, asi el umbral es 2.495*(1+R_alta/R_baja) sin V_GT."""
    b = "DF6"
    tlk, ref, qb, qc, gate = (f"TLK_CB{n}", f"REF_CB{n}", f"QB_CB{n}",
                              f"QC_CB{n}", f"GATE_SCR{n}")
    alto, bajo = (masa, riel) if negativo else (riel, masa)
    P(scr, "SCR", b, {"2": alto, "1": bajo, "3": gate})
    P(u, "TL431", b, {"1": tlk, "2": ref, "3": bajo})
    dos(r_alta, "R", b, alto, ref)
    dos(r_baja, "R", b, ref, bajo)
    P(q, "PNP", b, {"1": qb, "2": alto, "3": qc})
    dos(rb, "R", b, qb, tlk)
    dos(rbe, "R", b, alto, qb)
    dos(rc, "R", b, qc, gate)
    dos(rgk, "R", b, gate, bajo)


def rack() -> None:
    b = "DF6"
    dos("F2", "F", b, "+12V_RAW_RACK", "+12V_FUSED_RACK")
    dos("R29", "R", b, "+12V_FUSED_RACK", "+12V_RACK")
    _crowbar(1, "+12V_RACK", "GNDA", "Q3", "U22", "SCR1", "R45", "R47",
             "R70", "R74", "R78", "R53")
    dos("F3", "F", b, "-12V_RAW_RACK", "-12V_RACK")
    _crowbar(2, "-12V_RACK", "GNDA", "Q4", "U23", "SCR2", "R46", "R48",
             "R71", "R75", "R79", "R54", negativo=True)
    dos("F4", "F", b, "+5V_RAW_RACK", "+5V_FUSED_RACK")
    dos("R30", "R", b, "+5V_FUSED_RACK", "+5V_RACK")
    _crowbar(3, "+5V_RACK", "GNDA", "Q5", "U24", "SCR3", "R49", "R50",
             "R72", "R76", "R80", "R55")
    dos("F5", "F", b, "+5V_RAW_DIG", "+5V_DIG")
    _crowbar(4, "+5V_DIG", "GNDD", "Q6", "U25", "SCR4", "R51", "R52",
             "R73", "R77", "R81", "R56")
    P("TP5", "TP", b, {"1": "+5V_RACK"})
    P("TP11", "TP", b, {"1": "GNDD"})
    dos("R3", "R", b, "+5V_RACK", "LED6_A")
    P("D6", "LED", b, {"1": "GNDA", "2": "LED6_A"})
    dos("R4", "R", b, "+5V_DIG", "LED7_A")
    P("D7", "LED", b, {"1": "GNDD", "2": "LED7_A"})


def telemetria() -> None:
    b = "TEL"
    dos("R20", "R", b, "+5V_RAW_RACK", "+5V_AUX")
    # INA226 A1/A0 (ina226.pdf Table 6-2): GND/GND 0x40, GND/VS 0x41,
    # VS/GND 0x44, VS/VS 0x45. Nunca a SDA: con SDA salen 0x48/0x49 y chocan
    # con el ADS1115 y el TMP1075.
    ina = (("U8", "GNDA", "GNDA", "+12V_ULTRA", "OUTS_POS", "C24"),
           ("U12", "GNDA", "+5V_AUX", "+5V_AUX", "+5V_RAW_RACK", "C25"),
           ("U13", "+5V_AUX", "GNDA", "+12V_RACK", "+12V_FUSED_RACK", "C26"),
           ("U14", "+5V_AUX", "+5V_AUX", "+5V_RACK", "+5V_FUSED_RACK", "C27"))
    for ref, a1, a0, menos, mas, cdec in ina:
        P(ref, "INA226", b, {"1": a1, "2": a0, "3": None, "4": "SDA_A",
                             "5": "SCL_A", "6": "+5V_AUX", "7": "GNDA",
                             "8": menos, "9": menos, "10": mas})
        dos(cdec, "C", b, "+5V_AUX", "GNDA")
    P("U10", "ADS1115", b, {"1": "GNDA", "2": None, "3": "GNDA", "4": "AIN0",
                            "5": "AIN1", "6": "AIN2", "7": "AIN3", "8": "+5V_AUX",
                            "9": "SDA_A", "10": "SCL_A"})
    dos("C31", "C", b, "+5V_AUX", "GNDA")
    # Divisores 100k/20k y clamp BAT54S con el COMUN en la entrada: A a GNDA,
    # K a +5V_AUX. Al reves (A en la entrada, COM a masa) la entrada se queda
    # pegada a 0.3 V.
    canales = (("AIN0", "-12V_ULTRA", "+5V_AUX", "R21", "R25", "D14"),
               ("AIN1", "+15V5_LC", "GNDA", "R22", "R26", "D15"),
               ("AIN2", "-15V5_LC", "+5V_AUX", "R23", "R27", "D16"),
               ("AIN3", "-12V_RACK", "+5V_AUX", "R24", "R28", "D17"))
    for ain, riel, ref_baja, r_alta, r_baja, d in canales:
        dos(r_alta, "R", b, riel, ain)
        dos(r_baja, "R", b, ain, ref_baja)
        P(d, "BAT54S", b, {"1": "GNDA", "2": "+5V_AUX", "3": ain})
    P("U11", "TMP1075", b, {"1": "SDA_A", "2": "SCL_A", "3": None, "4": "GNDA",
                            "5": "GNDA", "6": "GNDA", "7": "+5V_AUX", "8": "+5V_AUX"})
    dos("C32", "C", b, "+5V_AUX", "GNDA")
    P("U9", "ISO1541", b, {"1": "+5V_AUX", "2": "SDA_A", "3": "SCL_A", "4": "GNDA",
                           "5": "GNDD", "6": "SCL_D", "7": "SDA_D", "8": "+3V3_DIG"})
    dos("C30", "C", b, "+5V_AUX", "GNDA")
    dos("C28", "C", b, "+3V3_DIG", "GNDD")
    dos("R57", "R", b, "+5V_AUX", "SDA_A")
    dos("R58", "R", b, "+5V_AUX", "SCL_A")
    dos("R59", "R", b, "+3V3_DIG", "SDA_D")
    dos("R60", "R", b, "+3V3_DIG", "SCL_D")


def conectores() -> None:
    b = "CON"
    # Bus de los modulos propios (ultra): DOS salidas iguales, una por segmento
    # de la placa bus, cada una con su par desde la estrella (bus-board/README).
    for ref in ("J2", "J7"):
        P(ref, "J4P", b, {"1": "-12V_ULTRA", "2": "GNDA", "3": "GNDA", "4": "+12V_ULTRA"})
    # Fila de invitados (D-B2): +12 / GND / -12 / +5 de rack.
    P("J3", "J4P", b, {"1": "+12V_RACK", "2": "GNDA", "3": "-12V_RACK", "4": "+5V_RACK"})
    P("J5", "J1P", b, {"1": "GNDA"})                         # puente unico a chasis
    P("J6", "J2P", b, {"1": "+5V_AUX", "2": "GNDA"})         # +5 V aux al modulo 2
    P("J8", "J4P", b, {"1": "+3V3_DIG", "2": "SDA_D", "3": "SCL_D", "4": "GNDD"})
    P("J9", "J2P", b, {"1": "+5V_DIG", "2": "GNDD"})


# Redes que entran o salen de algo pasivo (conector, modulo, resistencia
# shunt, ferrita...). Sin PWR_FLAG el ERC dice que nadie alimenta los power_in
# que cuelgan de ellas. Las que salen de un regulador no lo necesitan.
BANDERAS = ("+24V_RAW", "GND24", "GNDA", "GNDD", "+3V3_DIG", "+24V_PROT",
            "+24V_LDO", "+12V_RAW_RACK", "-12V_RAW_RACK",
            "+15V5_RAW", "-15V5_RAW", "+15V5_FILT", "-15V5_FILT",
            "+5V_RAW_DIG", "+5V_RAW_RACK", "+5V_AUX", "+5V_RACK", "+5V_DIG")


def construir() -> None:
    entrada_m5()
    convertidores()
    tope_y_lc()
    detector_df4()
    preregulador()
    ultra()
    rack()
    telemetria()
    conectores()


# ------------------------------------------------------------- comprobaciones
def leer_bom() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with open(BOM, encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            for ref in (r.strip() for r in fila["refs"].split(",")):
                if ref:
                    assert ref not in out, f"{ref} aparece dos veces en bom.csv"
                    out[ref] = fila
    return out


def _pads(fp: str) -> list[str]:
    """Numeros de pad de COBRE de una huella, leidos del .kicad_mod."""
    lib, _, nombre = fp.partition(":")
    base = os.path.join(DIR, "sam17.pretty") if lib == "sam17" else os.path.join(KICAD_FP, f"{lib}.pretty")
    ruta = os.path.join(base, f"{nombre}.kicad_mod")
    assert os.path.isfile(ruta), f"la huella {fp} no esta en disco ({ruta})"
    with open(ruta, encoding="utf-8") as fh:
        txt = fh.read()
    pads = []
    for m in re.finditer(r'\(pad\s+"([^"]*)"\s+(\w+)', txt):
        cola = txt[m.end():m.end() + 600]
        capas = re.search(r"\(layers([^)]*)\)", cola)
        if m.group(1) and capas and ("Cu" in capas.group(1)):
            pads.append(m.group(1))
    return pads


def cruzar_huellas(bom: dict[str, dict]) -> None:
    """Patillas del simbolo == pads de cobre de la huella, en los dos sentidos."""
    pines_por_ref: dict[str, set] = {}
    for ref, sym, _b, redes, unidad in PARTES:
        pines_por_ref.setdefault(ref, set()).update(symlib.pines(SYM[sym], unidad))
    malas = []
    for ref, pines in pines_por_ref.items():
        pads = set(_pads(bom[ref]["footprint"]))
        if pines - pads:
            malas.append(f"{ref}: patillas sin pad {sorted(pines - pads)}")
        if pads - pines:
            malas.append(f"{ref}: pads sin patilla {sorted(pads - pines)}")
    assert not malas, "simbolo y huella no casan:\n  " + "\n  ".join(malas)


def revisar_cobertura(bom: dict[str, dict]) -> None:
    refs = {p[0] for p in PARTES}
    assert refs == set(bom), (f"BOM y esquema no casan: sobran en BOM "
                              f"{sorted(set(bom) - refs)}, faltan en BOM {sorted(refs - set(bom))}")
    vistos = set()
    for ref, sym, _b, redes, unidad in PARTES:
        clave = (ref, unidad)
        assert clave not in vistos, f"{ref} unidad {unidad} colocada dos veces"
        vistos.add(clave)
        pines = set(symlib.pines(SYM[sym], unidad))
        assert set(redes) == pines, (f"{ref} ({SYM[sym]} u{unidad}): sin declarar "
                                     f"{sorted(pines - set(redes))}, sobran {sorted(set(redes) - pines)}")


# --------------------------------------------------------------- colocacion
_wires: list = []
_labels: list = []        # (nombre, x, y, angulo)
_ncs: list = []
_syms: list = []          # (lib, unidad, ref, val, x, y, rot, footprint)
_libs: set = set()

LARGO_STUB = g(4)
BLOQUES = (
    ("M5", "Entrada 24 V, polaridad (LM74502 + CSD18534Q5A), eFuse U16 y supervisor M5"),
    ("DCDC", "Convertidores: THN 30 (+-12 rack), URB (+5 digital M1), K78 (+5 rack), 2 x THN 20 (+-15.5)"),
    ("LC", "Tope M3 (#334): TPS26631 + filtro LC 22 uH / 47 uF / 0.68 ohm + 220 uF + SMBJ16A"),
    ("DF4", "Detector D-F4: LM393 + TL431, umbral 14.5 V con histeresis"),
    ("PRE", "Pre-reguladores LT1963A (+13.1 V) y LT3015 (-12.9 V)"),
    ("ULTRA", "Cascada ultra: 2 x LT3045 y 2 x LT3094 en paralelo, R_SET = 60k"),
    ("DF6", "Rack: fusibles y crowbars D-F6 (TL431 -> PNP -> BT151)"),
    ("TEL", "Telemetria I2C: 4 x INA226, ADS1115, TMP1075 e ISO1541"),
    ("CON", "Conectores"),
)
ANCHO_BLOQUE = 330.0
ORIGEN_X = 25.4


def _texto(n: str) -> float:
    return len(n) * 1.15 + 1.5


def _caja(sym: str, unidad: int, redes: dict) -> tuple[float, float, float, float]:
    """Extension (izq, arriba, der, abajo) respecto al origen del simbolo,
    contando stubs y etiquetas."""
    xs, ys = [0.0], [0.0]
    for num in symlib.pines(SYM[sym], unidad):
        px, py = symlib.pin_abs(SYM[sym], num, 0, 0, 0)
        xs.append(px)
        ys.append(py)
        dx, dy = symlib.pin_dir(SYM[sym], num, 0, unidad)
        largo = LARGO_STUB + (_texto(redes[num]) if redes.get(num) else 1.0)
        xs.append(px + dx * largo)
        ys.append(py + dy * largo)
    return (-min(xs), -min(ys) + g(3), max(xs), max(ys) + g(3))


def _rejilla(v: float) -> float:
    return round(round(v / (2 * G)) * 2 * G, 3)


def colocar(bom: dict[str, dict]) -> list[tuple]:
    """Estanteria por bloques. Devuelve los titulos de bloque [(texto, x, y)]."""
    titulos = []
    y_bloque = 25.4
    for clave, titulo in BLOQUES:
        partes = [p for p in PARTES if p[2] == clave]
        x, y_fila, alto_fila = ORIGEN_X, y_bloque + g(6), 0.0
        titulos.append((f"BLOQUE {clave}: {titulo}", ORIGEN_X, y_bloque))
        for ref, sym, _b, redes, unidad in partes:
            izq, arr, der, aba = _caja(sym, unidad, redes)
            # el Value va centrado debajo: que no pise al de al lado
            medio = max(0.0, _texto(bom[ref]["value"]) / 2 - min(izq, der))
            izq, der = izq + medio, der + medio
            ancho = izq + der + g(6)
            if x + ancho > ORIGEN_X + ANCHO_BLOQUE and x > ORIGEN_X:
                x, y_fila = ORIGEN_X, y_fila + alto_fila + g(6)
                alto_fila = 0.0
            ox, oy = _rejilla(x + izq), _rejilla(y_fila + arr)
            colocar_parte(ref, sym, redes, unidad, ox, oy)
            x += ancho
            alto_fila = max(alto_fila, arr + aba)
        y_bloque = y_fila + alto_fila + g(14)
    # banderas en una fila propia al final
    x, y = ORIGEN_X, _rejilla(y_bloque)
    titulos.append(("PWR_FLAG: redes que alimenta algo pasivo o un conector", ORIGEN_X, y - g(4)))
    for i, red in enumerate(BANDERAS):
        fx = _rejilla(x + (i % 8) * 40.64)
        fy = _rejilla(y + (i // 8) * 15.24 + g(4))
        _libs.add(SYM["FLAG"])
        _syms.append((SYM["FLAG"], 1, f"#FLG{i + 1:02d}", "PWR_FLAG", fx, fy, 0, ""))
        _wires.append((fx, fy, fx, round(fy + g(4), 3)))
        _labels.append((red, fx, round(fy + g(4), 3), 270))
    return titulos


def colocar_parte(ref: str, sym: str, redes: dict, unidad: int, ox: float, oy: float) -> None:
    lib = SYM[sym]
    _libs.add(lib)
    _syms.append((lib, unidad, ref, None, ox, oy, 0, None))
    for num in symlib.pines(lib, unidad):
        px, py = symlib.pin_abs(lib, num, ox, oy, 0)
        red = redes[num]
        if red is None:
            if (px, py) not in _ncs:
                _ncs.append((px, py))
            continue
        dx, dy = symlib.pin_dir(lib, num, 0, unidad)
        fx, fy = round(px + dx * LARGO_STUB, 3), round(py + dy * LARGO_STUB, 3)
        ang = 0 if dx > 0.5 else 180 if dx < -0.5 else 90 if dy < 0 else 270
        # Patillas APILADAS (los tres S de Q2, los tres IN del TPS26631): un
        # solo rabito y una sola etiqueta. Si dos apiladas pidieran redes
        # distintas, la segunda etiqueta caeria en el mismo punto con otro
        # nombre y revisar_fusiones() lo cantaria.
        if (px, py, fx, fy) not in _wires:
            _wires.append((px, py, fx, fy))
        if (red, fx, fy, ang) not in _labels:
            _labels.append((red, fx, fy, ang))


def revisar_rejilla() -> None:
    fuera = [v for w in _wires for v in w if abs(round(v / G) * G - v) > 1e-6]
    assert not fuera, f"cables fuera de rejilla de {G} mm: {fuera[:6]}"


def revisar_fusiones() -> None:
    malas = schcheck.redes_fusionadas(_wires, [(n, x, y) for n, x, y, _a in _labels], [])
    assert not malas, "redes fusionadas:\n  " + "\n  ".join(malas)


def revisar_solapes() -> None:
    """Dos simbolos no pueden compartir el mismo punto de patilla."""
    vistos: dict = {}
    for lib, unidad, ref, _v, x, y, rot, _fp in _syms:
        for num in symlib.pines(lib, unidad if unidad > 0 else None):
            p = symlib.pin_abs(lib, num, x, y, rot)
            assert p not in vistos or vistos[p] == ref, f"{ref}.{num} pisa a {vistos.get(p)} en {p}"
            vistos[p] = ref


# -------------------------------------------------------------------- salida
_NS = uuid.UUID(SHEET_UUID)


def _uid(clave: str) -> str:
    """UUID DETERMINISTA: el mismo objeto sale con el mismo UUID en cada
    regeneracion. Asi la hoja no cambia byte a byte si no cambia el diseno, y
    las huellas de la placa siguen enlazadas a su simbolo (path = /<uuid>)."""
    return str(uuid.uuid5(_NS, clave))


def escribir(bom: dict[str, dict], titulos: list[tuple]) -> None:
    xs = [s[4] for s in _syms] + [w[2] for w in _wires]
    ys = [s[5] for s in _syms] + [w[3] for w in _wires]
    ancho = int(max(xs) + 60)
    alto = int(max(ys) + 40)
    out = ["(kicad_sch", "\t(version 20260101)", '\t(generator "sam17-power-v5")',
           '\t(generator_version "10.0")', f'\t(uuid "{SHEET_UUID}")',
           f'\t(paper "User" {ancho} {alto})', "\t(title_block",
           '\t\t(title "SAM17 Modulo 01 v5 - Fuente: ladrillo 24 V y convertidores DC-DC")',
           f'\t\t(date "{DATE}")', f'\t\t(rev "{REV}")',
           '\t\t(company "SAM17 - Sintetizador analogico modular")',
           '\t\t(comment 1 "Generado por build_schematic.py: no editar a mano")',
           '\t\t(comment 2 "Pinouts de simbolos propios en build_simbolos.py, con su pagina de hoja")',
           '\t\t(comment 3 "GND24 y GNDA se unen SOLO en NT1, en los pads de masa de PS3 (K78 no aislado)")',
           '\t\t(comment 4 "GNDD no toca GNDA en esta placa (M1): ISO1541 y URB aislados")',
           "\t)", "\t(lib_symbols"]
    for lib in sorted(_libs):
        out.append("\t\t" + symlib.extraer(lib).replace("\n", "\n\t\t"))
    out.append("\t)")
    for i, (texto, x, y) in enumerate(titulos):
        out += [f'\t(text "{texto}"', "\t\t(exclude_from_sim no)", f"\t\t(at {x} {y} 0)",
                "\t\t(effects", "\t\t\t(font", "\t\t\t\t(size 2.54 2.54)", "\t\t\t\t(bold yes)",
                "\t\t\t)", "\t\t\t(justify left bottom)", "\t\t)", f'\t\t(uuid "{_uid(f"texto/{i}")}")', "\t)"]
    for x1, y1, x2, y2 in _wires:
        out += ["\t(wire", "\t\t(pts", f"\t\t\t(xy {x1} {y1}) (xy {x2} {y2})", "\t\t)",
                "\t\t(stroke", "\t\t\t(width 0)", "\t\t\t(type default)", "\t\t)",
                f'\t\t(uuid "{_uid(f"cable/{x1},{y1},{x2},{y2}")}")', "\t)"]
    for x, y in _ncs:
        out += ["\t(no_connect", f"\t\t(at {x} {y})", f'\t\t(uuid "{_uid(f"nc/{x},{y}")}")', "\t)"]
    # Etiquetas GLOBALES: una etiqueta local en la hoja raiz da la red "/GNDA",
    # y la placa la llama "GNDA". El DRC con paridad contaba 199 net_conflict
    # solo por esa barra. Con globales la red se llama igual en las dos.
    for nombre, x, y, ang in _labels:
        just = "left" if ang in (0, 90) else "right"
        out += [f'\t(global_label "{nombre}"', "\t\t(shape passive)", f"\t\t(at {x} {y} {ang})",
                "\t\t(effects", "\t\t\t(font", "\t\t\t\t(size 1.27 1.27)", "\t\t\t)",
                f"\t\t\t(justify {just})", "\t\t)", f'\t\t(uuid "{_uid(f"etiqueta/{nombre}/{x},{y}")}")', "\t)"]
    for lib, unidad, ref, _v, x, y, rot, _fp in _syms:
        es_flag = ref.startswith("#")
        fila = bom.get(ref, {})
        val = "PWR_FLAG" if es_flag else fila["value"]
        fp = "" if es_flag else fila["footprint"]
        izq, arr, der, aba = (0, g(3), 0, g(3)) if es_flag else (0, 0, 0, 0)
        if not es_flag:
            sym = next(s for r, s, _b, _r, u in PARTES if r == ref and u == unidad)
            redes = next(rd for r, _s, _b, rd, u in PARTES if r == ref and u == unidad)
            izq, arr, der, aba = _caja(sym, unidad, redes)
        out += ["\t(symbol", f'\t\t(lib_id "{lib}")', f"\t\t(at {x} {y} {rot})",
                f"\t\t(unit {unidad})", "\t\t(exclude_from_sim no)",
                f'\t\t(in_bom {"no" if es_flag else "yes"})',
                f'\t\t(on_board {"no" if es_flag else "yes"})', "\t\t(dnp no)",
                f'\t\t(uuid "{_uid(f"simbolo/{ref}/{unidad}")}")']
        campos = [("Reference", ref, x, round(y - arr + g(1), 2), es_flag),
                  ("Value", val, x, round(y + aba - g(1), 2), es_flag),
                  ("Footprint", fp, x, y, True), ("Datasheet", "", x, y, True),
                  ("Description", "", x, y, True)]
        if not es_flag:
            for clave in ("lcsc", "mpn"):
                if fila.get(clave):
                    campos.append((clave.upper(), fila[clave], x, y, True))
        for nombre, texto, xx, yy, esconder in campos:
            out += [f'\t\t(property "{nombre}" "{texto}"', f"\t\t\t(at {xx} {yy} 0)"]
            if esconder:
                out.append("\t\t\t(hide yes)")
            out += ["\t\t\t(show_name no)", "\t\t\t(do_not_autoplace no)", "\t\t\t(effects",
                    "\t\t\t\t(font", "\t\t\t\t\t(size 1.27 1.27)", "\t\t\t\t)", "\t\t\t)", "\t\t)"]
        for num in sorted(symlib.pines(lib, unidad if unidad > 0 else None)):
            out += [f'\t\t(pin "{num}"', f'\t\t\t(uuid "{_uid(f"patilla/{ref}/{unidad}/{num}")}")', "\t\t)"]
        out += ["\t\t(instances", '\t\t\t(project "sam17-power-v5"',
                f'\t\t\t\t(path "/{SHEET_UUID}"', f'\t\t\t\t\t(reference "{ref}")',
                f"\t\t\t\t\t(unit {unidad})", "\t\t\t\t)", "\t\t\t)", "\t\t)", "\t)"]
    out += ["\t(sheet_instances", '\t\t(path "/"', '\t\t\t(page "1")', "\t\t)", "\t)",
            "\t(embedded_fonts no)", ")"]
    with open(SCH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")


def main() -> int:
    bom = leer_bom()
    construir()
    revisar_cobertura(bom)
    cruzar_huellas(bom)
    titulos = colocar(bom)
    revisar_rejilla()
    revisar_solapes()
    revisar_fusiones()
    escribir(bom, titulos)
    piezas = {p[0] for p in PARTES}
    print(f"{len(piezas)} componentes, {len(_wires)} cables, {len(_labels)} etiquetas, "
          f"{len(_ncs)} no-connect")
    with tempfile.TemporaryDirectory() as tmp:
        erc = subprocess.run([KICAD_CLI, "sch", "erc", "--severity-all", "--exit-code-violations",
                              "-o", os.path.join(tmp, "erc.rpt"), SCH],
                             capture_output=True, text=True)
    print((erc.stdout or erc.stderr).strip()[-600:])
    r = subprocess.run([KICAD_CLI, "sch", "export", "netlist", "-o", NET, SCH],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"netlist: {r.stderr}"
    for ext in ("svg", "pdf"):
        destino = os.path.join(DIR, "..", "schematics")
        os.makedirs(destino, exist_ok=True)
        arg = destino if ext == "svg" else os.path.join(destino, "sam17-power-v5.pdf")
        subprocess.run([KICAD_CLI, "sch", "export", ext, "-o", arg, SCH],
                       capture_output=True, text=True)
    return erc.returncode


if __name__ == "__main__":
    sys.exit(main())
