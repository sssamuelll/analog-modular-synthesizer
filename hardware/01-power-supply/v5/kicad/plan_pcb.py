import csv
import os
import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
STOCK = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
LOCAL = os.path.join(DIR, "sam17.pretty")
BOM = os.path.join(DIR, "..", "bom.csv")
NET = os.path.join(DIR, "sam17-power-v5.net")

W, H = 200.0, 150.0
MARGEN = 3.0

MOUNTING = [
    ("H1", 7.0, 7.0),
    ("H2", 193.0, 7.0),
    ("H3", 7.0, 143.0),
    ("H4", 193.0, 143.0),
]

def mm(val):
    return int(val * 1e6)

bom_fps = {}
bom_vals = {}
with open(BOM, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        for ref in (r.strip() for r in row["refs"].split(",") if r.strip()):
            bom_fps[ref] = row["footprint"]
            bom_vals[ref] = row["value"]

PLACEMENT = {
    # ---------------- Bloque 1: Entrada 24V y Supervisor M5 (X: 12..45, Y: 15..135)
    "J1":  ( 18.0,  75.0,   0),  # Kycon KPJX-PM-4S entrada 24V
    "D1":  ( 32.0,  75.0,  90),  # TVS SMBJ26A
    "U15": ( 38.0,  70.0,   0),  # LM74502 ideal diode
    "Q2":  ( 38.0,  80.0,   0),  # MOSFET 60V 40A
    "U16": ( 38.0,  50.0,   0),  # TPS26630 eFuse 24V
    "R11": ( 28.0,  46.0,   0),  # R_ILIM U16
    "R12": ( 28.0,  52.0,   0),  # R_UVLO high
    "R13": ( 28.0,  58.0,   0),  # R_OVPR mid
    "R14": ( 28.0,  64.0,   0),  # R_OVPR low
    "U18": ( 28.0,  95.0,   0),  # TPS70933 LDO 3.3V
    "C7":  ( 22.0,  95.0,   0),  # C_IN U18
    "C8":  ( 34.0,  95.0,   0),  # C_OUT U18
    "U17": ( 28.0, 110.0,   0),  # MSP430FR2111 MCU
    "C23": ( 20.0, 110.0,   0),  # C local MCU
    "SW1": ( 18.0, 130.0,   0),  # Reset switch
    "D18": ( 28.0, 125.0,   0),  # LED azul supervisor
    "R31": ( 34.0, 125.0,   0),  # R limitador LED D18
    "J10": ( 38.0, 110.0,   0),  # SBW header
    "J5":  ( 18.0,  25.0,   0),  # Faston 6.3mm PE chasis
    "TP1": ( 18.0,  42.0,   0),  # TP +24V_RAW
    "TP2": ( 18.0,  52.0,   0),  # TP GND24

    # ---------------- Bloque 2: Convertidores DC-DC (X: 55..98, Y: 18..135)
    "PS1": ( 56.0,  32.0,   0),  # TRACO THN 30WI (+-12V rack)
    "PS2": ( 56.0,  68.0,   0),  # Mornsun URB-YMD 20WR3 (5V dig isolated)
    "PS3": ( 56.0, 105.0,   0),  # Mornsun K7805T (5V rack buck)
    "PS4": ( 90.0,  32.0,   0),  # TRACO THN 20WI (+15.5V cascada)
    "R32": ( 90.0,  50.0,   0),  # R trim PS4
    "PS5": ( 90.0,  75.0,   0),  # TRACO THN 20WI (-15.5V cascada)
    "R33": ( 90.0,  93.0,   0),  # R trim PS5
    "TP9": ( 90.0, 110.0,   0),  # TP +15V5_LC
    "TP10":( 90.0, 122.0,   0),  # TP -15V5_LC

    # ---------------- Bloque 3: Proteccion eFuse U19 y Filtro LC (X: 105..128, Y: 15..95)
    "U19": (108.0,  25.0,   0),  # TPS26630 eFuse cascada
    "R34": (108.0,  35.0,   0),  # R_ILIM U19
    "R35": (108.0,  40.0,   0),  # R_OVP high
    "R36": (108.0,  45.0,   0),  # R_OVP low
    "L2":  (120.0,  22.0,   0),  # Bobina LC +15.5V
    "L3":  (120.0,  38.0,   0),  # Bobina LC -15.5V
    "C1":  (108.0,  55.0,   0),  # Damp cap +15.5V
    "C2":  (120.0,  55.0,   0),  # Damp cap -15.5V
    "R37": (108.0,  64.0,   0),  # R_damp +15.5V
    "R38": (120.0,  64.0,   0),  # R_damp -15.5V
    "C3":  (108.0,  72.0,   0),  # Ceramic 22uF +15.5V
    "C4":  (120.0,  72.0,   0),  # Ceramic 22uF -15.5V
    "C5":  (108.0,  80.0,   0),  # 100nF +15.5V
    "C6":  (120.0,  80.0,   0),  # 100nF -15.5V
    "FB1": (108.0,  88.0,   0),  # Ferrite +15.5V
    "FB2": (120.0,  88.0,   0),  # Ferrite -15.5V
    "D10": (108.0,  96.0,   0),  # SMBJ16A TVS
    "D11": (120.0,  96.0,   0),  # BAT54WS Schottky

    # ---------------- Bloque 4: Secuenciador D-F4 / M4 (X: 105..125, Y: 108..140)
    "U20": (110.0, 115.0,   0),  # LM393B
    "U21": (120.0, 115.0,   0),  # TL431BI
    "R39": (106.0, 125.0,   0),  # R sense pos high
    "R40": (112.0, 125.0,   0),  # R sense pos low
    "R41": (118.0, 125.0,   0),  # R sense neg high
    "R42": (124.0, 125.0,   0),  # R sense neg low
    "R43": (110.0, 135.0,   0),  # R pull-down SHDN
    "R44": (120.0, 135.0,   0),  # R pull-up SHDN

    # ---------------- Bloque 5: Cascada Primera Etapa (X: 135..152, Y: 15..80)
    "U1":  (136.0,  25.0,   0),  # LT1963A (+13.1V)
    "U2":  (138.0,  55.0,   0),  # LT3015 (-12.9V)
    "D12": (148.0,  22.0,   0),  # D anti-backfeed +13.1V
    "D13": (150.0,  52.0,   0),  # D anti-backfeed -12.9V
    "R5":  (148.0,  30.0,   0),  # R5 divisor U1
    "RV2": (150.0,  38.0,   0),  # RV2 trimmer U1
    "R6":  (148.0,  45.0,   0),  # R6 divisor U1
    "R7":  (150.0,  60.0,   0),  # R7 divisor U2
    "RV3": (150.0,  68.0,   0),  # RV3 trimmer U2
    "R8":  (150.0,  75.0,   0),  # R8 divisor U2
    "C17": (136.0,  38.0,   0),  # C17 output U1
    "C18": (138.0,  68.0,   0),  # C18 output U2
    "TP7": (136.0,  46.0,   0),  # TP +13V1
    "TP8": (138.0,  76.0,   0),  # TP -12V9

    # ---------------- Bloque 7: Fuses y Crowbars Rack (X: 132..148, Y: 85..142)
    "F2":  (134.0,  92.0,   0),  # Fuse +12V rack
    "U22": (140.0,  92.0,   0),  # TL431 crowbar +12V
    "SCR1":(146.0,  92.0,   0),  # BT151 crowbar +12V
    "R45": (134.0,  98.0,   0),  # R high crowbar +12V
    "R47": (140.0,  98.0,   0),  # R low crowbar +12V
    "R53": (146.0,  98.0,   0),  # R gate pull-down SCR1

    "F3":  (134.0, 106.0,   0),  # Fuse -12V rack
    "U23": (140.0, 106.0,   0),  # TL431 crowbar -12V
    "SCR2":(146.0, 106.0,   0),  # BT151 crowbar -12V
    "R46": (134.0, 112.0,   0),  # R high crowbar -12V
    "R48": (140.0, 112.0,   0),  # R low crowbar -12V
    "R54": (146.0, 112.0,   0),  # R gate pull-down SCR2

    "F4":  (134.0, 120.0,   0),  # Fuse +5V rack
    "U24": (140.0, 120.0,   0),  # TL431 crowbar +5V rack
    "SCR3":(146.0, 120.0,   0),  # BT151 crowbar +5V rack
    "R49": (134.0, 126.0,   0),  # R high crowbar +5V rack
    "R50": (140.0, 126.0,   0),  # R low crowbar +5V rack
    "R55": (146.0, 126.0,   0),  # R gate pull-down SCR3

    "F5":  (134.0, 134.0,   0),  # Fuse +5V digital
    "U25": (140.0, 134.0,   0),  # TL431 crowbar +5V dig
    "SCR4":(146.0, 134.0,   0),  # BT151 crowbar +5V dig
    "R51": (134.0, 140.0,   0),  # R high crowbar +5V dig
    "R52": (140.0, 140.0,   0),  # R low crowbar +5V dig
    "R56": (146.0, 140.0,   0),  # R gate pull-down SCR4

    # ---------------- Bloque 6: Cascada Ultra-Bajo Ruido (X: 160..175, Y: 15..75)
    "U4":  (160.0,  20.0,   0),  # LT3045 #1 (+12V ultra)
    "U5":  (172.0,  20.0,   0),  # LT3045 #2 (+12V ultra)
    "R15": (160.0,  28.0,   0),  # Ballast U4
    "R16": (172.0,  28.0,   0),  # Ballast U5
    "R9":  (166.0,  20.0,   0),  # R_SET +12V
    "C19": (166.0,  28.0,   0),  # C_SET +12V
    "C20": (166.0,  35.0,   0),  # C_OUT +12V ultra

    "U6":  (160.0,  50.0,   0),  # LT3094 #1 (-12V ultra)
    "U7":  (172.0,  50.0,   0),  # LT3094 #2 (-12V ultra)
    "R17": (160.0,  58.0,   0),  # Ballast U6
    "R18": (172.0,  58.0,   0),  # Ballast U7
    "R10": (166.0,  50.0,   0),  # R_SET -12V
    "C21": (166.0,  58.0,   0),  # C_SET -12V
    "C22": (166.0,  65.0,   0),  # C_OUT -12V ultra

    # ---------------- Bloque 8: Telemetria I2C (X: 160..186, Y: 75..145)
    "R19": (174.0,  35.0,   0),  # Shunt +12V ultra
    "U8":  (182.0,  35.0,   0),  # INA226 +12V ultra (0x40)
    "C24": (182.0,  42.0,   0),  # Desacoplo U8

    "R29": (160.0,  78.0,   0),  # Shunt +12V rack
    "U13": (168.0,  78.0,   0),  # INA226 +12V rack (0x44)
    "C26": (168.0,  84.0,   0),  # Desacoplo U13

    "R30": (160.0,  92.0,   0),  # Shunt +5V rack
    "U14": (168.0,  92.0,   0),  # INA226 +5V rack (0x45)
    "C27": (168.0,  98.0,   0),  # Desacoplo U14

    "R20": (160.0, 106.0,   0),  # Shunt +5V aux
    "U12": (168.0, 106.0,   0),  # INA226 +5V aux (0x41)
    "C25": (168.0, 112.0,   0),  # Desacoplo U12

    "U10": (176.0,  78.0,   0),  # ADS1115 (0x48)
    "R21": (174.0,  86.0,   0),  # Divisor AIN0 high
    "R25": (178.0,  86.0,   0),  # Divisor AIN0 low
    "D14": (183.0,  86.0,   0),  # Clamp AIN0
    "R22": (174.0,  92.0,   0),  # Divisor AIN1 high
    "R26": (178.0,  92.0,   0),  # Divisor AIN1 low
    "D15": (183.0,  92.0,   0),  # Clamp AIN1
    "R23": (174.0,  98.0,   0),  # Divisor AIN2 high
    "R27": (178.0,  98.0,   0),  # Divisor AIN2 low
    "D16": (183.0,  98.0,   0),  # Clamp AIN2
    "R24": (174.0, 104.0,   0),  # Divisor AIN3 high
    "R28": (178.0, 104.0,   0),  # Divisor AIN3 low
    "D17": (183.0, 104.0,   0),  # Clamp AIN3

    "U11": (176.0, 115.0,   0),  # TMP1075 (0x49)
    "R57": (174.0, 122.0,   0),  # Pull-up SDA_A
    "R58": (180.0, 122.0,   0),  # Pull-up SCL_A

    "U9":  (176.0, 132.0,   0),  # ISO1541 aislador I2C
    "C28": (168.0, 132.0,   0),  # Desacoplo digital U9
    "R59": (174.0, 140.0,   0),  # Pull-up SDA_D
    "R60": (180.0, 140.0,   0),  # Pull-up SCL_D

    # ---------------- Bloque 9: Conectores, Indicadores y Test Points (X: 188..195, Y: 15..145)
    "J2":  (192.0,  30.0, 270),  # Eurocard bus 4 pos (-12V, GNDA, GNDA, +12V)
    "J6":  (192.0,  55.0, 270),  # Molex 2 pos +5V rack
    "J8":  (192.0,  75.0, 270),  # PinHeader 1x4 I2C digital aislado
    "J9":  (192.0,  95.0, 270),  # Molex 2 pos +5V digital aislado

    "D3":  (192.0, 110.0,   0),  # LED rojo +12V ultra
    "R1":  (186.0, 110.0,   0),  # R limitador LED D3
    "D4":  (192.0, 118.0,   0),  # LED amarillo -12V ultra
    "R2":  (186.0, 118.0,   0),  # R limitador LED D4
    "D6":  (192.0, 126.0,   0),  # LED verde +5V rack
    "R3":  (186.0, 126.0,   0),  # R limitador LED D6
    "D7":  (192.0, 134.0,   0),  # LED azul +5V digital
    "R4":  (186.0, 134.0,   0),  # R limitador LED D7

    "TP3": (180.0,  18.0,   0),  # TP +12V_ULTRA
    "TP4": (186.0,  18.0,   0),  # TP -12V_ULTRA
    "TP5": (192.0,  18.0,   0),  # TP +5V_RACK
    "TP6": (166.0,  12.0,   0),  # TP GNDA
    "TP11":(186.0,  68.0,   0),  # TP GNDD
}

# 1. Verify coverage of all BOM components
faltan = sorted(set(bom_fps) - set(PLACEMENT))
assert not faltan, f"Faltan en PLACEMENT: {faltan}"
sobran = sorted(set(PLACEMENT) - set(bom_fps))
assert not sobran, f"Sobran en PLACEMENT: {sobran}"
print(f"Placement cubre exactamente los {len(PLACEMENT)} componentes del BOM!")

# 2. Check bounds and margins
fuera = []
for ref, (x, y, rot) in PLACEMENT.items():
    if not (MARGEN <= x <= W - MARGEN and MARGEN <= y <= H - MARGEN):
        fuera.append((ref, x, y))
assert not fuera, f"Componentes fuera del margen ({MARGEN} mm): {fuera}"
print("Todos los componentes dentro de los margenes de la placa (200x150 mm)!")

# 3. Create board and load all footprints to verify bounding boxes
board = pcbnew.CreateEmptyBoard()
fps = {}
for ref, (x, y, rot) in PLACEMENT.items():
    fpid = bom_fps[ref]
    lib, _, name = fpid.partition(":")
    base = LOCAL if lib == "sam17" else os.path.join(STOCK, f"{lib}.pretty")
    fp = pcbnew.FootprintLoad(base, name)
    assert fp, f"Error cargando huella {fpid} para {ref}"
    fp.SetReference(ref)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    if rot:
        fp.SetOrientationDegrees(rot)
    fp.Value().SetVisible(False)
    board.Add(fp)
    fps[ref] = fp

# Check pairwise overlap
solapes = []
for ref1, fp1 in fps.items():
    bb1 = fp1.GetBoundingBox(False, False)
    for ref2, fp2 in fps.items():
        if ref1 >= ref2:
            continue
        bb2 = fp2.GetBoundingBox(False, False)
        # Check overlap
        if bb1.Intersects(bb2):
            solapes.append((ref1, ref2, bb1, bb2))

if solapes:
    print(f"ALERTA: {len(solapes)} solapes detectados:")
    for r1, r2, b1, b2 in solapes:
        p1 = PLACEMENT[r1]
        p2 = PLACEMENT[r2]
        print(f"  {r1} {p1} <-> {r2} {p2}")
else:
    print("VERDE: Cero solapes entre componentes!")
