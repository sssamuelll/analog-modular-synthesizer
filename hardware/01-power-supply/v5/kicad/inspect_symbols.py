import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
from kicad_mcp_client import Client

symbols = [
    "Sensor_Energy:INA226",
    "Analog_ADC:ADS1115IDGS",
    "Sensor_Temperature:TMP1075DGK",
    "Isolator:ISO1541",
    "Regulator_Linear:LT3045xDD",
    "Regulator_Linear:LT3094xDD",
    "Reference_Voltage:TL431LP",
    "Comparator:LM393",
    "Regulator_Linear:LP2985-3.3",
    "Diode:BAT54S",
    "Device:R_Shunt",
    "Device:R_Potentiometer_Trim",
    "Switch:SW_Push",
    "Connector:Conn_01x04_Pin",
    "Connector:Conn_01x02_Pin",
    "Connector:Conn_01x01_Pin",
    "Connector:TestPoint",
    "Device:Q_NMOS",
    "Device:D_TVS",
    "Device:D_Schottky",
    "Device:D",
    "Device:LED",
    "Device:Fuse",
    "Device:FerriteBead",
    "Device:L",
    "Device:C",
    "Device:C_Polarized",
    "Device:R",
]

c = Client()
try:
    for sym in symbols:
        res = c.call("list_symbol_pins", {"symbol": sym})
        print(f"=== {sym} ===")
        print(res)
finally:
    c.close()
