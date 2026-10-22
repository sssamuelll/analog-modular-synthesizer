"""Genera sam17-power-v5.kicad_sch y exporta sam17-power-v5.net a partir de bom.csv.

Construye la arquitectura completa v5:
- Entrada 24V externa por Kycon KPJX-PM-4S (J1) con proteccion inversa LM74502 (U15) y CSD18534Q5A (Q2)
- eFuse de entrada TPS26630 (U16) con supervisor MSP430FR2111 (U17) y LDO TPS70933 (U18)
- 5 convertidores DC-DC:
    * PS1: TRACO THN 30-2422WI (+-12V rack, 30W)
    * PS2: Mornsun URB2405YMD-20WR3 (+5V digital aislado M1, 20W)
    * PS3: Mornsun K7805T-1000R3 (+5V rack, 5W)
    * PS4: TRACO THN 20-2413WI (+15.5V crudo cascada positiva)
    * PS5: TRACO THN 20-2413WI (-15.5V crudo cascada negativa invertida)
- eFuse de cascada TPS26630 (U19) y filtro LC amortiguado (L2, L3, C1-C6, FB1, FB2, D10, D11)
- Secuenciador analógico LM393B (U20) + TL431BI (U21) D-F4 / M4
- Cascada primera etapa LT1963A (U1) y LT3015 (U2) (+13.10V / -12.90V)
- Cascada segunda etapa ultra-bajo ruido 2x LT3045 (U4, U5) y 2x LT3094 (U6, U7)
- Fuses y crowbars rack D-F6: 4x BT151-500R + TL431BI (SCR1-SCR4, U22-U25, F2-F5)
- Telemetría I2C aislada: 4x INA226 (U8, U12, U13, U14), ADS1115 (U10), TMP1075 (U11), ISO1541 (U9)
- Conectores J1, J2, J5, J6, J8, J9, J10, indicadores LED D3, D4, D6, D7, D18 y test points TP1-TP11.

Uso:
    python build_schematic.py
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
from kicad_mcp_client import Client

DIR = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
SCH = f"{DIR}/sam17-power-v5.kicad_sch"
PRO = f"{DIR}/sam17-power-v5.kicad_pro"
NET = f"{DIR}/sam17-power-v5.net"
BOM = f"{DIR}/../bom.csv"
KICAD_CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")


def leer_bom_refs() -> dict[str, dict]:
    bom = {}
    with open(BOM, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            for ref in row["refs"].split(","):
                ref = ref.strip()
                if ref and ref != "—":
                    bom[ref] = {
                        "value": row["value"],
                        "footprint": row["footprint"],
                        "notes": row["notes"]
                    }
    return bom


def define_parts(bom: dict[str, dict]) -> list[dict]:
    """Asigna symbol, footprint y posicion ampliamente espaciada a cada ref del BOM."""
    parts = []

    # Bloque 1: Entrada 24V y Supervisor M5 (X: 35..185, Y: 40..120)
    b1 = [
        ("J1", "sam17:KPJX-PM-4S", 35.00, 60.00, 0),
        ("D1", "Device:D_TVS", 55.00, 60.00, 0),
        ("U15", "sam17:LM74502DDFR", 75.00, 60.00, 0),
        ("Q2", "Device:Q_NMOS", 95.00, 60.00, 0),
        ("U16", "sam17:TPS26630PWPR", 125.00, 60.00, 0),
        ("R11", "Device:R", 105.00, 45.00, 0),
        ("R12", "Device:R", 105.00, 70.00, 0),
        ("R13", "Device:R", 105.00, 95.00, 0),
        ("R14", "Device:R", 105.00, 120.00, 0),
        ("U18", "Regulator_Linear:LP2985-3.3", 135.00, 95.00, 0),
        ("C7", "Device:C", 125.00, 115.00, 0),
        ("C8", "Device:C", 145.00, 115.00, 0),
        ("U17", "sam17:MSP430FR2111IPW16", 165.00, 75.00, 0),
        ("C23", "Device:C", 165.00, 95.00, 0),
        ("SW1", "Switch:SW_Push", 185.00, 95.00, 0),
        ("D18", "Device:LED", 185.00, 75.00, 0),
        ("R31", "Device:R", 185.00, 55.00, 0),
        ("J10", "Connector:Conn_01x04_Pin", 165.00, 120.00, 0),
    ]

    # Bloque 2: Convertidores DC-DC (X: 215..240, Y: 45..185)
    b2 = [
        ("PS1", "sam17:TRACO_THN_30-2422WI", 215.00, 50.00, 0),
        ("PS2", "sam17:Mornsun_URB2405YMD-20WR3", 215.00, 80.00, 0),
        ("PS3", "sam17:Mornsun_K7805T-1000R3", 215.00, 110.00, 0),
        ("PS4", "sam17:TRACO_THN_20-2413WI", 215.00, 145.00, 0),
        ("PS5", "sam17:TRACO_THN_20-2413WI", 215.00, 180.00, 0),
        ("R32", "Device:R", 235.00, 145.00, 0),
        ("R33", "Device:R", 235.00, 180.00, 0),
    ]

    # Bloque 3: Proteccion previa y LC cascada (X: 245..330, Y: 130..205)
    b3 = [
        ("U19", "sam17:TPS26630PWPR", 255.00, 145.00, 0),
        ("R34", "Device:R", 245.00, 125.00, 0),
        ("R35", "Device:R", 245.00, 150.00, 0),
        ("R36", "Device:R", 245.00, 175.00, 0),
        ("L2", "Device:L", 275.00, 135.00, 90),
        ("L3", "Device:L", 275.00, 175.00, 90),
        ("C1", "Device:C_Polarized", 285.00, 145.00, 0),
        ("R37", "Device:R", 285.00, 160.00, 0),
        ("C2", "Device:C_Polarized", 285.00, 185.00, 0),
        ("R38", "Device:R", 285.00, 200.00, 0),
        ("C3", "Device:C", 295.00, 145.00, 0),
        ("C4", "Device:C", 295.00, 185.00, 0),
        ("C5", "Device:C", 305.00, 145.00, 0),
        ("C6", "Device:C", 305.00, 185.00, 0),
        ("FB1", "Device:FerriteBead", 315.00, 135.00, 90),
        ("FB2", "Device:FerriteBead", 315.00, 175.00, 90),
        ("D10", "Device:D_TVS", 325.00, 145.00, 0),
        ("D11", "Device:D_Schottky", 325.00, 185.00, 0),
    ]

    # Bloque 4: Secuenciador D-F4 / M4 (X: 330..380, Y: 130..180)
    b4 = [
        ("U20", "sam17:LM393BDR", 345.00, 150.00, 0),
        ("U21", "Reference_Voltage:TL431LP", 335.00, 175.00, 0),
        ("R39", "Device:R", 330.00, 135.00, 0),
        ("R40", "Device:R", 330.00, 155.00, 0),
        ("R41", "Device:R", 360.00, 135.00, 0),
        ("R42", "Device:R", 360.00, 155.00, 0),
        ("R43", "Device:R", 375.00, 135.00, 0),
        ("R44", "Device:R", 375.00, 155.00, 0),
    ]

    # Bloque 5: Cascada primera etapa (X: 395..440, Y: 110..200)
    b5 = [
        ("U1", "sam17:LT1963AEST", 395.00, 135.00, 0),
        ("U2", "sam17:LT3015EQ", 395.00, 175.00, 0),
        ("D12", "Device:D", 395.00, 115.00, 0),
        ("D13", "Device:D", 395.00, 195.00, 0),
        ("R5", "Device:R", 410.00, 135.00, 0),
        ("RV2", "Device:R_Potentiometer_Trim", 410.00, 150.00, 0),
        ("R6", "Device:R", 410.00, 165.00, 0),
        ("R7", "Device:R", 425.00, 165.00, 0),
        ("RV3", "Device:R_Potentiometer_Trim", 425.00, 180.00, 0),
        ("R8", "Device:R", 425.00, 195.00, 0),
        ("C17", "Device:C_Polarized", 435.00, 135.00, 0),
        ("C18", "Device:C_Polarized", 435.00, 175.00, 0),
    ]

    # Bloque 6: Cascada segunda etapa ultra-bajo ruido (X: 450..490, Y: 125..200)
    b6 = [
        ("U4", "Regulator_Linear:LT3045xDD", 450.00, 130.00, 0),
        ("U5", "Regulator_Linear:LT3045xDD", 450.00, 150.00, 0),
        ("U6", "Regulator_Linear:LT3094xDD", 450.00, 170.00, 0),
        ("U7", "Regulator_Linear:LT3094xDD", 450.00, 190.00, 0),
        ("R9", "Device:R", 465.00, 135.00, 0),
        ("R10", "Device:R", 465.00, 175.00, 0),
        ("R15", "Device:R", 475.00, 130.00, 90),
        ("R16", "Device:R", 475.00, 150.00, 90),
        ("R17", "Device:R", 475.00, 170.00, 90),
        ("R18", "Device:R", 475.00, 190.00, 90),
        ("C19", "Device:C", 465.00, 145.00, 0),
        ("C21", "Device:C", 465.00, 185.00, 0),
        ("C20", "Device:C", 485.00, 135.00, 0),
        ("C22", "Device:C", 485.00, 175.00, 0),
    ]

    # Bloque 7: Fuses y Crowbars Rack (X: 250..270, Y: 35..160)
    b7 = [
        ("F2", "Device:Fuse", 250.00, 45.00, 90),
        ("U22", "Reference_Voltage:TL431LP", 260.00, 45.00, 0),
        ("SCR1", "sam17:BT151-500R", 270.00, 45.00, 0),
        ("R45", "Device:R", 260.00, 35.00, 0),
        ("R47", "Device:R", 260.00, 55.00, 0),
        ("R53", "Device:R", 270.00, 55.00, 0),

        ("F3", "Device:Fuse", 250.00, 70.00, 90),
        ("U23", "Reference_Voltage:TL431LP", 260.00, 70.00, 0),
        ("SCR2", "sam17:BT151-500R", 270.00, 70.00, 0),
        ("R46", "Device:R", 260.00, 80.00, 0),
        ("R48", "Device:R", 260.00, 90.00, 0),
        ("R54", "Device:R", 270.00, 80.00, 0),

        ("F4", "Device:Fuse", 250.00, 105.00, 90),
        ("U24", "Reference_Voltage:TL431LP", 260.00, 105.00, 0),
        ("SCR3", "sam17:BT151-500R", 270.00, 105.00, 0),
        ("R49", "Device:R", 260.00, 115.00, 0),
        ("R50", "Device:R", 260.00, 125.00, 0),
        ("R55", "Device:R", 270.00, 115.00, 0),

        ("F5", "Device:Fuse", 250.00, 140.00, 90),
        ("U25", "Reference_Voltage:TL431LP", 260.00, 140.00, 0),
        ("SCR4", "sam17:BT151-500R", 270.00, 140.00, 0),
        ("R51", "Device:R", 260.00, 150.00, 0),
        ("R52", "Device:R", 260.00, 160.00, 0),
        ("R56", "Device:R", 270.00, 150.00, 0),
    ]

    # Bloque 8: Telemetria y Monitoreo (X: 290..575, Y: 45..155)
    b8 = [
        ("R29", "Device:R_Shunt", 290.00, 45.00, 90),
        ("U13", "Sensor_Energy:INA226", 305.00, 45.00, 0),
        ("C26", "Device:C", 305.00, 60.00, 0),

        ("R30", "Device:R_Shunt", 290.00, 105.00, 90),
        ("U14", "Sensor_Energy:INA226", 305.00, 105.00, 0),
        ("C27", "Device:C", 305.00, 120.00, 0),

        ("R20", "Device:R_Shunt", 290.00, 140.00, 90),
        ("U12", "Sensor_Energy:INA226", 305.00, 140.00, 0),
        ("C25", "Device:C", 305.00, 155.00, 0),

        ("R21", "Device:R", 330.00, 50.00, 0),
        ("R25", "Device:R", 345.00, 50.00, 0),
        ("D14", "Diode:BAT54S", 360.00, 50.00, 0),

        ("R22", "Device:R", 330.00, 65.00, 0),
        ("R26", "Device:R", 345.00, 65.00, 0),
        ("D15", "Diode:BAT54S", 360.00, 65.00, 0),

        ("R23", "Device:R", 330.00, 85.00, 0),
        ("R27", "Device:R", 345.00, 85.00, 0),
        ("D16", "Diode:BAT54S", 360.00, 85.00, 0),

        ("R24", "Device:R", 330.00, 100.00, 0),
        ("R28", "Device:R", 345.00, 100.00, 0),
        ("D17", "Diode:BAT54S", 360.00, 100.00, 0),

        ("U10", "Analog_ADC:ADS1115IDGS", 375.00, 75.00, 0),
        ("U11", "Sensor_Temperature:TMP1075DGK", 410.00, 75.00, 0),
        ("R57", "Device:R", 425.00, 55.00, 0),
        ("R58", "Device:R", 425.00, 95.00, 0),
        ("U9", "Isolator:ISO1541", 445.00, 75.00, 0),
        ("C28", "Device:C", 445.00, 90.00, 0),

        ("R59", "Device:R", 470.00, 55.00, 0),
        ("R60", "Device:R", 470.00, 95.00, 0),

        ("U8", "Sensor_Energy:INA226", 575.00, 115.00, 0),
        ("R19", "Device:R_Shunt", 565.00, 115.00, 90),
        ("C24", "Device:C", 575.00, 130.00, 0),
    ]

    # Bloque 9: Conectores, Indicadores y Test Points (X: 35..590, Y: 35..205)
    b9 = [
        ("J2", "Connector:Conn_01x04_Pin", 590.00, 135.00, 180),
        ("J5", "Connector:Conn_01x01_Pin", 35.00, 100.00, 0),
        ("J6", "Connector:Conn_01x02_Pin", 320.00, 120.00, 180),
        ("J8", "Connector:Conn_01x04_Pin", 485.00, 75.00, 180),
        ("J9", "Connector:Conn_01x02_Pin", 280.00, 180.00, 180),
        ("D3", "Device:LED", 575.00, 95.00, 0),
        ("R1", "Device:R", 575.00, 105.00, 0),
        ("D4", "Device:LED", 575.00, 155.00, 0),
        ("R2", "Device:R", 575.00, 165.00, 0),
        ("D6", "Device:LED", 320.00, 135.00, 0),
        ("R3", "Device:R", 320.00, 145.00, 0),
        ("D7", "Device:LED", 280.00, 195.00, 0),
        ("R4", "Device:R", 280.00, 205.00, 0),
        ("TP1", "Connector:TestPoint", 50.00, 35.00, 0),
        ("TP2", "Connector:TestPoint", 65.00, 35.00, 0),
        ("TP3", "Connector:TestPoint", 80.00, 35.00, 0),
        ("TP4", "Connector:TestPoint", 95.00, 35.00, 0),
        ("TP5", "Connector:TestPoint", 110.00, 35.00, 0),
        ("TP6", "Connector:TestPoint", 125.00, 35.00, 0),
        ("TP7", "Connector:TestPoint", 140.00, 35.00, 0),
        ("TP8", "Connector:TestPoint", 155.00, 35.00, 0),
        ("TP9", "Connector:TestPoint", 170.00, 35.00, 0),
        ("TP10", "Connector:TestPoint", 185.00, 35.00, 0),
        ("TP11", "Connector:TestPoint", 200.00, 35.00, 0),
    ]

    all_blocks = b1 + b2 + b3 + b4 + b5 + b6 + b7 + b8 + b9
    vistos = set()
    for ref, sym, x, y, rot in all_blocks:
        assert ref in bom, f"ref {ref} no esta en bom.csv!"
        assert ref not in vistos, f"ref {ref} duplicada en placement!"
        vistos.add(ref)
        parts.append({
            "reference": ref,
            "symbol": sym,
            "value": bom[ref]["value"],
            "footprint": bom[ref]["footprint"],
            "position": {"x": x, "y": y},
            "rotation": rot
        })

    faltan = set(bom) - vistos
    assert not faltan, f"Faltan referencias del BOM en el placement: {faltan}"
    return parts


def define_connections() -> dict[str, dict[str, str]]:
    """Mapa exhaustivo de conexiones {ref: {pin: netName}} para todos los 157 componentes."""
    c: dict[str, dict[str, str]] = {}

    # ---------------- Bloque 1: Entrada 24V y Supervisor M5
    c["J1"] = {"1": "+24V_RAW", "2": "+24V_RAW", "3": "GND24", "4": "GND24", "5": "PE"}
    c["D1"] = {"1": "+24V_RAW", "2": "GND24"}  # D_TVS 1=A1, 2=A2
    c["U15"] = {"1": "+24V_RAW", "2": "+24V_RAW", "4": "GATE_Q2", "5": "+24V_PROT", "6": "GND24"}
    c["Q2"] = {"G": "GATE_Q2", "D": "+24V_RAW", "S": "+24V_PROT"}
    c["U16"] = {
        "1": "+24V_PROT", "4": "UVLO_U16", "5": "OVPR_U16", "6": "GND24", "7": "SHDN_M5",
        "8": "GND24", "9": "GND24", "10": "FLT_M5", "11": "IMON_M5", "12": "ILIM_U16",
        "13": "GND24", "15": "+24V_SW"
    }
    c["R11"] = {"1": "ILIM_U16", "2": "GND24"}
    c["R12"] = {"1": "+24V_PROT", "2": "UVLO_U16"}
    c["R13"] = {"1": "UVLO_U16", "2": "OVPR_U16"}
    c["R14"] = {"1": "OVPR_U16", "2": "GND24"}
    c["U18"] = {"1": "+24V_PROT", "2": "GND24", "3": "+24V_PROT", "5": "+3V3_MCU"}
    c["C7"] = {"1": "+24V_PROT", "2": "GND24"}
    c["C8"] = {"1": "+3V3_MCU", "2": "GND24"}
    c["U17"] = {
        "13": "+3V3_MCU", "14": "GND24", "2": "FLT_M5", "4": "SHDN_M5",
        "5": "LED_CTRL", "6": "SW_RESET", "11": "MCU_RST", "12": "MCU_TEST"
    }
    c["C23"] = {"1": "+3V3_MCU", "2": "GND24"}
    c["SW1"] = {"1": "SW_RESET", "2": "GND24"}
    c["D18"] = {"1": "GND24", "2": "LED_ANODE"}
    c["R31"] = {"1": "LED_CTRL", "2": "LED_ANODE"}
    c["J10"] = {"1": "+3V3_MCU", "2": "MCU_TEST", "3": "MCU_RST", "4": "GND24"}

    # ---------------- Bloque 2: Convertidores DC-DC
    c["PS1"] = {"1": "+24V_SW", "2": "GND24", "4": "+12V_RAW_RACK", "5": "GNDA", "6": "-12V_RAW_RACK"}
    c["PS2"] = {"1": "+24V_SW", "2": "GND24", "4": "+5V_RAW_DIG", "5": "GNDD"}
    c["PS3"] = {"1": "+24V_SW", "2": "GNDA", "3": "+5V_RAW_RACK"}
    c["PS4"] = {"1": "+24V_SW", "2": "GND24", "4": "+15V5_RAW", "5": "GNDA", "6": "TRIM_PS4"}
    c["PS5"] = {"1": "+24V_SW", "2": "GND24", "4": "GNDA", "5": "-15V5_RAW", "6": "TRIM_PS5"}
    c["R32"] = {"1": "TRIM_PS4", "2": "+15V5_RAW"}
    c["R33"] = {"1": "TRIM_PS5", "2": "-15V5_RAW"}

    # ---------------- Bloque 3: Proteccion Previa y LC Cascada
    c["U19"] = {
        "1": "+15V5_RAW", "4": "+15V5_RAW", "5": "OVPR_U19", "6": "GNDA", "7": "SHDN_CASCADE",
        "8": "GNDA", "9": "GNDA", "10": "FLT_U19", "11": "IMON_U19", "12": "ILIM_U19",
        "13": "GNDA", "15": "+15V5_EFUSE"
    }
    c["R34"] = {"1": "ILIM_U19", "2": "GNDA"}
    c["R35"] = {"1": "+15V5_RAW", "2": "OVPR_U19"}
    c["R36"] = {"1": "OVPR_U19", "2": "GNDA"}
    c["L2"] = {"1": "+15V5_EFUSE", "2": "+15V5_LC"}
    c["C1"] = {"1": "+15V5_LC", "2": "C1_NEG"}
    c["R37"] = {"1": "C1_NEG", "2": "GNDA"}
    c["C3"] = {"1": "+15V5_LC", "2": "GNDA"}
    c["C5"] = {"1": "+15V5_LC", "2": "GNDA"}
    c["FB1"] = {"1": "+15V5_LC", "2": "+15V5_FILT"}
    c["D10"] = {"1": "+15V5_FILT", "2": "GNDA"}
    c["L3"] = {"1": "-15V5_RAW", "2": "-15V5_LC"}
    c["C2"] = {"1": "GNDA", "2": "C2_NEG"}
    c["R38"] = {"1": "C2_NEG", "2": "-15V5_LC"}
    c["C4"] = {"1": "GNDA", "2": "-15V5_LC"}
    c["C6"] = {"1": "GNDA", "2": "-15V5_LC"}
    c["FB2"] = {"1": "-15V5_LC", "2": "-15V5_FILT"}
    c["D11"] = {"1": "GNDA", "2": "-15V5_FILT"}

    # ---------------- Bloque 4: Secuenciador D-F4 / M4
    c["U20"] = {
        "8": "+5V_AUX", "4": "GNDA", "2": "VREF_2V5", "3": "SENSE_POS",
        "1": "SHDN_CASCADE", "6": "VREF_2V5", "5": "SENSE_NEG", "7": "SHDN_CASCADE"
    }
    c["U21"] = {"3": "VREF_2V5", "1": "VREF_2V5", "2": "GNDA"}  # 1=REF, 2=A, 3=K
    c["R39"] = {"1": "+15V5_LC", "2": "SENSE_POS"}
    c["R40"] = {"1": "SENSE_POS", "2": "GNDA"}
    c["R41"] = {"1": "+5V_AUX", "2": "SENSE_NEG"}
    c["R42"] = {"1": "SENSE_NEG", "2": "-15V5_LC"}
    c["R43"] = {"1": "SHDN_CASCADE", "2": "GNDA"}
    c["R44"] = {"1": "+5V_AUX", "2": "SHDN_CASCADE"}

    # ---------------- Bloque 5: Cascada Primera Etapa
    c["U1"] = {"2": "+15V5_FILT", "1": "SHDN_CASCADE", "3": "GNDA", "4": "+13V1", "5": "ADJ_U1"}
    c["U2"] = {"2": "-15V5_FILT", "1": "SHDN_CASCADE", "3": "GNDA", "4": "-12V9", "5": "ADJ_U2"}
    c["D12"] = {"1": "+15V5_FILT", "2": "+13V1"}
    c["D13"] = {"1": "-12V9", "2": "-15V5_FILT"}
    c["R5"] = {"1": "+13V1", "2": "TRIM_U1_HI"}
    c["RV2"] = {"1": "TRIM_U1_HI", "2": "ADJ_U1", "3": "ADJ_U1"}
    c["R6"] = {"1": "ADJ_U1", "2": "GNDA"}
    c["R7"] = {"1": "-12V9", "2": "TRIM_U2_HI"}
    c["RV3"] = {"1": "TRIM_U2_HI", "2": "ADJ_U2", "3": "ADJ_U2"}
    c["R8"] = {"1": "ADJ_U2", "2": "GNDA"}
    c["C17"] = {"1": "+13V1", "2": "GNDA"}
    c["C18"] = {"1": "GNDA", "2": "-12V9"}

    # ---------------- Bloque 6: Cascada Segunda Etapa Ultra-Bajo Ruido
    c["U4"] = {
        "1": "+13V1", "2": "+13V1", "3": "+13V1", "5": "GNDA", "6": "GNDA",
        "7": "SET_POS", "8": "GNDA", "9": "OUTS_POS", "10": "OUT_U4", "11": "GNDA"
    }
    c["U5"] = {
        "1": "+13V1", "2": "+13V1", "3": "+13V1", "5": "GNDA", "6": "GNDA",
        "7": "SET_POS", "8": "GNDA", "9": "OUTS_POS", "10": "OUT_U5", "11": "GNDA"
    }
    c["R15"] = {"1": "OUT_U4", "2": "OUTS_POS"}
    c["R16"] = {"1": "OUT_U5", "2": "OUTS_POS"}
    c["R9"] = {"1": "SET_POS", "2": "GNDA"}
    c["C19"] = {"1": "SET_POS", "2": "GNDA"}
    c["U6"] = {
        "1": "-12V9", "2": "-12V9", "3": "-12V9", "5": "GNDA", "6": "GNDA", "7": "GNDA",
        "8": "SET_NEG", "9": "GNDA", "10": "-12V_ULTRA", "11": "OUT_U6", "12": "OUT_U6", "13": "-12V9"
    }
    c["U7"] = {
        "1": "-12V9", "2": "-12V9", "3": "-12V9", "5": "GNDA", "6": "GNDA", "7": "GNDA",
        "8": "SET_NEG", "9": "GNDA", "10": "-12V_ULTRA", "11": "OUT_U7", "12": "OUT_U7", "13": "-12V9"
    }
    c["R17"] = {"1": "OUT_U6", "2": "-12V_ULTRA"}
    c["R18"] = {"1": "OUT_U7", "2": "-12V_ULTRA"}
    c["R10"] = {"1": "SET_NEG", "2": "GNDA"}
    c["C21"] = {"1": "SET_NEG", "2": "GNDA"}
    c["C20"] = {"1": "+12V_ULTRA", "2": "GNDA"}
    c["C22"] = {"1": "GNDA", "2": "-12V_ULTRA"}

    # ---------------- Bloque 7: Fuses y Crowbars Rack
    c["F2"] = {"1": "+12V_RAW_RACK", "2": "+12V_FUSED_RACK"}
    c["SCR1"] = {"1": "GNDA", "2": "+12V_RACK", "3": "GATE_SCR1"}
    c["U22"] = {"3": "GATE_SCR1", "1": "REF_CB1", "2": "GNDA"}
    c["R45"] = {"1": "+12V_RACK", "2": "REF_CB1"}
    c["R47"] = {"1": "REF_CB1", "2": "GNDA"}
    c["R53"] = {"1": "GATE_SCR1", "2": "GNDA"}
    c["F3"] = {"1": "-12V_RAW_RACK", "2": "-12V_RACK"}
    c["SCR2"] = {"1": "-12V_RACK", "2": "GNDA", "3": "GATE_SCR2"}
    c["U23"] = {"3": "GATE_SCR2", "1": "REF_CB2", "2": "-12V_RACK"}
    c["R46"] = {"1": "GNDA", "2": "REF_CB2"}
    c["R48"] = {"1": "REF_CB2", "2": "-12V_RACK"}
    c["R54"] = {"1": "GATE_SCR2", "2": "-12V_RACK"}
    c["F4"] = {"1": "+5V_RAW_RACK", "2": "+5V_FUSED_RACK"}
    c["SCR3"] = {"1": "GNDA", "2": "+5V_RACK", "3": "GATE_SCR3"}
    c["U24"] = {"3": "GATE_SCR3", "1": "REF_CB3", "2": "GNDA"}
    c["R49"] = {"1": "+5V_RACK", "2": "REF_CB3"}
    c["R50"] = {"1": "REF_CB3", "2": "GNDA"}
    c["R55"] = {"1": "GATE_SCR3", "2": "GNDA"}
    c["F5"] = {"1": "+5V_RAW_DIG", "2": "+5V_DIG"}
    c["SCR4"] = {"1": "GNDD", "2": "+5V_DIG", "3": "GATE_SCR4"}
    c["U25"] = {"3": "GATE_SCR4", "1": "REF_CB4", "2": "GNDD"}
    c["R51"] = {"1": "+5V_DIG", "2": "REF_CB4"}
    c["R52"] = {"1": "REF_CB4", "2": "GNDD"}
    c["R56"] = {"1": "GATE_SCR4", "2": "GNDD"}

    # ---------------- Bloque 8: Telemetria y Monitoreo
    c["R19"] = {"1": "OUTS_POS", "2": "+12V_ULTRA", "3": "OUTS_POS", "4": "+12V_ULTRA"}
    c["R29"] = {"1": "+12V_FUSED_RACK", "2": "+12V_RACK", "3": "+12V_FUSED_RACK", "4": "+12V_RACK"}
    c["R30"] = {"1": "+5V_FUSED_RACK", "2": "+5V_RACK", "3": "+5V_FUSED_RACK", "4": "+5V_RACK"}
    c["R20"] = {"1": "+5V_RAW_RACK", "2": "+5V_AUX", "3": "+5V_RAW_RACK", "4": "+5V_AUX"}
    c["U8"] = {
        "1": "GNDA", "2": "GNDA", "4": "SDA_A", "5": "SCL_A",
        "6": "+5V_AUX", "7": "GNDA", "8": "+12V_ULTRA", "9": "+12V_ULTRA", "10": "OUTS_POS"
    }
    c["U12"] = {
        "1": "GNDA", "2": "+5V_AUX", "4": "SDA_A", "5": "SCL_A",
        "6": "+5V_AUX", "7": "GNDA", "8": "+5V_AUX", "9": "+5V_AUX", "10": "+5V_RAW_RACK"
    }
    c["U13"] = {
        "1": "SDA_A", "2": "GNDA", "4": "SDA_A", "5": "SCL_A",
        "6": "+5V_AUX", "7": "GNDA", "8": "+12V_RACK", "9": "+12V_RACK", "10": "+12V_FUSED_RACK"
    }
    c["U14"] = {
        "1": "SDA_A", "2": "+5V_AUX", "4": "SDA_A", "5": "SCL_A",
        "6": "+5V_AUX", "7": "GNDA", "8": "+5V_RACK", "9": "+5V_RACK", "10": "+5V_FUSED_RACK"
    }
    c["U10"] = {
        "1": "GNDA", "3": "GNDA", "4": "AIN0", "5": "AIN1", "6": "AIN2", "7": "AIN3",
        "8": "+5V_AUX", "9": "SDA_A", "10": "SCL_A"
    }
    c["R21"] = {"1": "-12V_ULTRA", "2": "AIN0"}
    c["R25"] = {"1": "AIN0", "2": "+5V_AUX"}
    c["D14"] = {"1": "AIN0", "2": "+5V_AUX", "3": "GNDA"}
    c["R22"] = {"1": "+15V5_LC", "2": "AIN1"}
    c["R26"] = {"1": "AIN1", "2": "GNDA"}
    c["D15"] = {"1": "AIN1", "2": "+5V_AUX", "3": "GNDA"}
    c["R23"] = {"1": "-15V5_LC", "2": "AIN2"}
    c["R27"] = {"1": "AIN2", "2": "+5V_AUX"}
    c["D16"] = {"1": "AIN2", "2": "+5V_AUX", "3": "GNDA"}
    c["R24"] = {"1": "-12V_RACK", "2": "AIN3"}
    c["R28"] = {"1": "AIN3", "2": "+5V_AUX"}
    c["D17"] = {"1": "AIN3", "2": "+5V_AUX", "3": "GNDA"}
    c["U11"] = {"1": "SDA_A", "2": "SCL_A", "4": "GNDA", "5": "GNDA", "6": "GNDA", "7": "+5V_AUX", "8": "+5V_AUX"}
    c["U9"] = {"1": "+5V_AUX", "2": "SDA_A", "3": "SCL_A", "4": "GNDA", "5": "GNDD", "6": "SCL_D", "7": "SDA_D", "8": "+3V3_DIG"}
    c["R57"] = {"1": "+5V_AUX", "2": "SDA_A"}
    c["R58"] = {"1": "+5V_AUX", "2": "SCL_A"}
    c["R59"] = {"1": "+3V3_DIG", "2": "SDA_D"}
    c["R60"] = {"1": "+3V3_DIG", "2": "SCL_D"}
    c["C24"] = {"1": "+5V_AUX", "2": "GNDA"}
    c["C25"] = {"1": "+5V_AUX", "2": "GNDA"}
    c["C26"] = {"1": "+5V_AUX", "2": "GNDA"}
    c["C27"] = {"1": "+5V_AUX", "2": "GNDA"}
    c["C28"] = {"1": "+3V3_DIG", "2": "GNDD"}

    # ---------------- Bloque 9: Conectores, Indicadores y Test Points
    c["J2"] = {"1": "-12V_ULTRA", "2": "GNDA", "3": "GNDA", "4": "+12V_ULTRA"}
    c["J5"] = {"1": "GNDA"}
    c["J6"] = {"1": "+5V_RACK", "2": "GNDA"}
    c["J8"] = {"1": "+3V3_DIG", "2": "SDA_D", "3": "SCL_D", "4": "GNDD"}
    c["J9"] = {"1": "+5V_DIG", "2": "GNDD"}
    c["D3"] = {"1": "GNDA", "2": "LED3_A"}
    c["R1"] = {"1": "+12V_ULTRA", "2": "LED3_A"}
    c["D4"] = {"1": "LED4_K", "2": "GNDA"}
    c["R2"] = {"1": "LED4_K", "2": "-12V_ULTRA"}
    c["D6"] = {"1": "GNDA", "2": "LED6_A"}
    c["R3"] = {"1": "+5V_RACK", "2": "LED6_A"}
    c["D7"] = {"1": "GNDD", "2": "LED7_A"}
    c["R4"] = {"1": "+5V_DIG", "2": "LED7_A"}
    c["TP1"] = {"1": "+24V_RAW"}
    c["TP2"] = {"1": "GND24"}
    c["TP3"] = {"1": "+12V_ULTRA"}
    c["TP4"] = {"1": "-12V_ULTRA"}
    c["TP5"] = {"1": "+5V_RACK"}
    c["TP6"] = {"1": "GNDA"}
    c["TP7"] = {"1": "+13V1"}
    c["TP8"] = {"1": "-12V9"}
    c["TP9"] = {"1": "+15V5_LC"}
    c["TP10"] = {"1": "-15V5_LC"}
    c["TP11"] = {"1": "GNDD"}

    return c


def inject_texts_and_title(sch_path: str) -> None:
    texts = [
        ("SAM17 FUENTE v5 (LADRILLO EXTERNO 24V + 5 CONVERTIDORES DC-DC)", 30.0, 20.0),
        ("BLOQUE 1: Entrada 24V, Supervisor M5 (MSP430FR2111 + TPS26630) y Proteccion Inversa (LM74502)", 30.0, 30.0),
        ("BLOQUE 2: DC-DCs (TRACO THN 30WI +-12V, Mornsun URB 5V DIG, Mornsun K78 5V RACK, 2x THN 20WI +-15.5V)", 210.0, 30.0),
        ("BLOQUE 3: Filtro LC y eFuse TPS26630 M3 / #334 + Bourns SMBJ16A", 240.0, 115.0),
        ("BLOQUE 4: Secuenciador D-F4 / M4 (LM393B + TL431BI)", 330.0, 115.0),
        ("BLOQUE 5: Cascada Primera Etapa (LT1963A + LT3015)", 390.0, 105.0),
        ("BLOQUE 6: Cascada Segunda Etapa Ultra-Bajo Ruido (2x LT3045 + 2x LT3094)", 450.0, 115.0),
        ("BLOQUE 7: Protecciones Rack Crowbar D-F6 (4x BT151-500R + TL431BI + Fuses)", 240.0, 25.0),
        ("BLOQUE 8: Telemetria I2C Aislada (4x INA226, ADS1115, TMP1075, ISO1541)", 290.0, 30.0),
    ]
    segs = []
    for text, x, y in texts:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        segs.append(
            f'\t(text "{escaped}"\n'
            "\t\t(exclude_from_sim no)\n"
            f"\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n"
            "\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n"
            '\t\t(uuid "text-doc-{:04d}")\n\t)\n'.format(len(segs))
        )
    block = "".join(segs)

    with open(sch_path, encoding="utf-8") as fh:
        txt = fh.read()
    anchor = "(sheet_instances"
    idx = txt.find(anchor)
    if idx != -1:
        txt = txt[:idx] + block + txt[idx:]
    with open(sch_path, "w", encoding="utf-8") as fh:
        fh.write(txt)


def main() -> int:
    bom = leer_bom_refs()
    parts = define_parts(bom)
    connections = define_connections()

    print(f"BOM: {len(bom)} designadores cargados.")
    print(f"Placement: {len(parts)} componentes definidos.")
    print(f"Conexiones: {len(connections)} componentes con redes asignadas.")

    # Validacion previa estricta
    faltan_conn = set(bom) - set(connections)
    assert not faltan_conn, f"Faltan conexiones para: {faltan_conn}"

    c = Client()
    try:
        # 1. Crear esquematico nuevo
        print("Creando esquematico nuevo...")
        r_create = c.call("create_schematic", {"name": "sam17-power-v5", "path": SCH})
        print("create_schematic:", r_create)

        # Ajustar cajetin de titulo y formato A2
        with open(SCH, encoding="utf-8") as fh:
            txt = fh.read()
        title_block = (
            '(paper "A2")\n'
            "\t(title_block\n"
            '\t\t(title "SAM17 Modulo 01 v5 — Fuente de Alimentacion Ladrillo 24V y DC-DCs")\n'
            '\t\t(date "2026-10-22")\n'
            '\t\t(rev "v5-A")\n'
            '\t\t(company "SAM17 — Sintetizador analogico modular")\n'
            '\t\t(comment 1 "Entrada 24VDC externa (TE90A2403F01 / GST120A / GSM120A) por Kycon KPJX-PM-4S")\n'
            '\t\t(comment 2 "Proteccion M5 (TI TPS26630 + MSP430FR2111 FRAM) y bloqueo polaridad (TI LM74502)")\n'
            '\t\t(comment 3 "Convertidores THN30 (+-12V rack), URB2405 (5V dig M1), K7805 (5V rack), 2x THN20 (+-15.5V)")\n'
            '\t\t(comment 4 "Cascada ultra-bajo ruido U1..U7 con eFuse U19 M3 / #334 y secuenciador D-F4 / M4")\n'
            "\t)"
        )
        if '(paper "A4")' in txt:
            txt = txt.replace('(paper "A4")', title_block, 1)
        else:
            txt = re.sub(r'\(paper "[^"]*"\)', title_block, txt, count=1)
        with open(SCH, "w", encoding="utf-8") as fh:
            fh.write(txt)

        # 2. Agregar componentes en lotes de 15 para evitar timeout del server MCP
        chunk_size = 15
        components_mcp = [
            {
                "symbol": p["symbol"],
                "reference": p["reference"],
                "value": p["value"],
                "footprint": p["footprint"],
                "position": p["position"],
                "rotation": p["rotation"]
            }
            for p in parts
        ]

        print(f"Agregando {len(components_mcp)} componentes en lotes de {chunk_size}...")
        for i in range(0, len(components_mcp), chunk_size):
            chunk = components_mcp[i:i + chunk_size]
            t0 = time.time()
            c.call("batch_add_components", {
                "schematicPath": SCH,
                "components": chunk
            })
            dt = time.time() - t0
            print(f"  Lote {i // chunk_size + 1}/{(len(components_mcp) - 1) // chunk_size + 1} ({len(chunk)} comps) en {dt:.2f}s")

        # 3. Conectar pines en lotes de 4 componentes para evitar timeouts
        conn_chunk_size = 4
        conn_items = list(connections.items())
        total_conn_chunks = (len(conn_items) - 1) // conn_chunk_size + 1
        print(f"Conectando {len(conn_items)} componentes en lotes de {conn_chunk_size} ({total_conn_chunks} lotes)...")
        for i in range(0, len(conn_items), conn_chunk_size):
            chunk_dict = dict(conn_items[i:i + conn_chunk_size])
            t0 = time.time()
            r_conn = c.call("batch_connect", {
                "schematicPath": SCH,
                "connections": chunk_dict,
                "labelType": "label",
                "replace": False
            })
            dt = time.time() - t0
            print(f"  Lote {i // conn_chunk_size + 1}/{total_conn_chunks} ({len(chunk_dict)} comps) en {dt:.2f}s: {r_conn}")

        # 4. Inyectar notas de documentacion de bloques
        inject_texts_and_title(SCH)

        # 5. Exportar netlist con kicad-cli
        print("Exportando netlist...")
        r_net = subprocess.run([KICAD_CLI, "sch", "export", "netlist", "-o", NET, SCH],
                               capture_output=True, text=True)
        assert r_net.returncode == 0, f"Error exportando netlist: {r_net.stderr}"
        print(f"Netlist exportado exitosamente a {NET}")

        # 6. Exportar SVG y PDF
        print("Exportando renders esquematicos...")
        for ext in ("svg", "pdf"):
            out = f"{DIR}/../schematics/sam17-power-v5.{ext}"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            subprocess.run([KICAD_CLI, "sch", "export", ext, "-o", out, SCH],
                           capture_output=True, text=True)
        print("Esquematicos exportados a schematics/sam17-power-v5.{svg,pdf}")

    finally:
        c.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
