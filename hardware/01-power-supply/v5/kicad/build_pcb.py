"""Genera sam17-power-v5.kicad_pcb: contorno 200x150 mm, colocacion limpia y conexion de redes.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Coloca los 157 componentes de la fuente v5 en su flujo funcional izquierda a derecha:
  - Entrada 24V (J1 Kycon) y supervisor M5 en el lateral izquierdo.
  - 5 Convertidores DC-DC aislados y buck en la seccion central-izquierda.
  - Etapa previa eFuse U19, filtro LC amortiguado y pre-reguladores U1/U2 en el centro.
  - Secuenciador y protecciones crowbar SCR1..SCR4 en la seccion inferior central.
  - Reguladores ultra-bajo ruido U4..U7 (LT3045/LT3094) e isla de telemetria I2C.
  - Conectores de salida Eurocard (J2), +5V rack (J6), I2C digital (J8), +5V digital (J9).
  - 4 Taladros de fijacion M3 (H1..H4) en las cuatro esquinas (7,7), (193,7), (7,143), (193,143).
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power-v5.kicad_pcb")
NET = os.path.join(DIR, "sam17-power-v5.net")
BOM = os.path.join(DIR, "..", "bom.csv")
STOCK = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
LOCAL = os.path.join(DIR, "sam17.pretty")
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"

W, H = 200.0, 150.0
MARGEN = 3.0
CLEARANCE_MM = 0.15
VIA_D = 0.6
VIA_TALADRO = 0.3
MOUNT_D = 3.2

MOUNTING = [
    ("H1", 7.0, 7.0),
    ("H2", 193.0, 7.0),
    ("H3", 7.0, 143.0),
    ("H4", 193.0, 143.0),
]


def mm(val: float) -> int:
    return int(val * 1e6)


def leer_bom() -> dict[str, str]:
    vals = {}
    with open(BOM, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for ref in (r.strip() for r in row["refs"].split(",") if r.strip()):
                vals[ref] = row["value"]
    return vals


def leer_netlist() -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()

    # 1. Componentes y footprints
    huellas = dict(re.findall(
        r'\(comp\s+\(ref\s+"([^"]+)"\).*?\(footprint\s+"([^"]+)"\)',
        txt, re.DOTALL))
    assert huellas, "no se encontraron componentes en el netlist"

    # 2. Redes
    cab = list(re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)', txt))
    assert cab, "no se encontraron redes en el netlist"
    redes = {}
    for i, m in enumerate(cab):
        fin = cab[i + 1].start() if i + 1 < len(cab) else len(txt)
        net_name = m.group(1).lstrip("/")
        for a, b in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', txt[m.end():fin]):
            redes[(a, b)] = net_name

    return huellas, redes


# Mapa de colocacion verificado: ref -> (x, y, rot)
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


def contorno(board: pcbnew.BOARD) -> None:
    esquinas = [
        (0.0, 0.0), (W, 0.0),
        (W, 0.0), (W, H),
        (W, H), (0.0, H),
        (0.0, H), (0.0, 0.0)
    ]
    for (x1, y1), (x2, y2) in zip(esquinas[0::2], esquinas[1::2]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.15))
        board.Add(seg)


def reglas(board: pcbnew.BOARD) -> None:
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(CLEARANCE_MM)
    ds.m_MinClearance = mm(CLEARANCE_MM)
    ds.m_ViasMinSize = mm(VIA_D)
    ds.m_MinThroughDrill = mm(VIA_TALADRO)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(CLEARANCE_MM))
    if hasattr(nc, "SetViaDiameter"):
        nc.SetViaDiameter(mm(VIA_D))
    if hasattr(nc, "SetViaDrill"):
        nc.SetViaDrill(mm(VIA_TALADRO))


def texto_silk(board: pcbnew.BOARD, texto: str, x: float, y: float, tam: float = 1.0, rot: float = 0.0) -> None:
    t = pcbnew.PCB_TEXT(board)
    t.SetText(texto)
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(pcbnew.VECTOR2I(mm(tam), mm(tam)))
    t.SetLayer(pcbnew.F_SilkS)
    if rot:
        t.SetTextAngle(int(rot * 10))
    board.Add(t)


def main() -> int:
    huellas, redes = leer_netlist()
    faltan = sorted(set(huellas) - set(PLACEMENT))
    assert not faltan, f"Componentes del netlist sin sitio en PLACEMENT: {faltan}"
    bom_valores = leer_bom()

    print(f"Generando {os.path.basename(PCB)}...")
    board = pcbnew.CreateEmptyBoard()
    contorno(board)
    reglas(board)

    # 1. Crear redes
    netinfo = {}
    for nombre in sorted(set(redes.values())):
        n = pcbnew.NETINFO_ITEM(board, nombre)
        board.Add(n)
        netinfo[nombre] = n

    # 2. Cargar y colocar huellas
    sin_red = []
    colocadas = {}
    for ref, fpid in sorted(huellas.items()):
        lib, _, name = fpid.partition(":")
        base = LOCAL if lib == "sam17" else os.path.join(STOCK, f"{lib}.pretty")
        fp = pcbnew.FootprintLoad(base, name)
        assert fp, f"Error cargando huella {fpid} para {ref}"
        x, y, rot = PLACEMENT[ref]
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        if rot:
            fp.SetOrientationDegrees(rot)
        fp.Value().SetVisible(False)
        val = bom_valores.get(ref)
        if val:
            fp.SetValue(val)
        board.Add(fp)
        fp.SetLocalClearance(0)
        colocadas[ref] = fp

        # Asignar redes a pads
        for pad in fp.Pads():
            si_cobre = (pad.GetLayerSet().Contains(pcbnew.F_Cu) or pad.GetLayerSet().Contains(pcbnew.B_Cu))
            if not si_cobre:
                continue
            red = redes.get((ref, pad.GetNumber()))
            if red and red in netinfo:
                pad.SetNet(netinfo[red])
            else:
                sin_red.append(f"{ref}.{pad.GetNumber()}")

    # 3. Taladros mecanicos de fijacion (H1..H4)
    for ref, x, y in MOUNTING:
        fp = pcbnew.FootprintLoad(
            os.path.join(STOCK, "MountingHole.pretty"),
            f"MountingHole_{MOUNT_D}mm_M3")
        assert fp, "Error cargando huella de MountingHole"
        fp.SetReference(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        board.Add(fp)

    # 4. Textos de serigrafia
    texto_silk(board, "SAM17 FUENTE v5 (LADRILLO 24V)", 100.0, 8.0, 1.5)
    texto_silk(board, "ENTRADA 24V", 18.0, 60.0, 1.0)
    texto_silk(board, "CONVERTIDORES DC-DC", 70.0, 18.0, 1.0)
    texto_silk(board, "FILTRO LC / CASCADA", 115.0, 12.0, 1.0)
    texto_silk(board, "CROWBARS D-F6", 138.0, 86.0, 1.0)
    texto_silk(board, "ULTRA-BAJO RUIDO", 164.0, 6.0, 1.0)
    texto_silk(board, "TELEMETRIA I2C", 176.0, 72.0, 1.0)
    texto_silk(board, "EUROCARD BUS", 192.0, 22.0, 1.0)

    # 5. Zonas de plano de masa
    # Zona GNDA en B.Cu
    zona_gnda = pcbnew.ZONE(board)
    zona_gnda.SetLayer(pcbnew.B_Cu)
    zona_gnda.SetNet(netinfo["GNDA"])
    outline_gnda = zona_gnda.Outline()
    outline_gnda.NewOutline()
    for zx, zy in [(5.0, 5.0), (165.0, 5.0), (165.0, 145.0), (5.0, 145.0)]:
        outline_gnda.Append(pcbnew.VECTOR2I(mm(zx), mm(zy)))
    zona_gnda.SetLocalClearance(mm(CLEARANCE_MM))
    zona_gnda.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zona_gnda.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zona_gnda.SetIsFilled(False)
    board.Add(zona_gnda)

    # Zona GNDD aislada en B.Cu (para seccion digital)
    zona_gndd = pcbnew.ZONE(board)
    zona_gndd.SetLayer(pcbnew.B_Cu)
    zona_gndd.SetNet(netinfo["GNDD"])
    outline_gndd = zona_gndd.Outline()
    outline_gndd.NewOutline()
    for zx, zy in [(168.0, 65.0), (195.0, 65.0), (195.0, 145.0), (168.0, 145.0)]:
        outline_gndd.Append(pcbnew.VECTOR2I(mm(zx), mm(zy)))
    zona_gndd.SetLocalClearance(mm(CLEARANCE_MM))
    zona_gndd.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zona_gndd.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zona_gndd.SetIsFilled(False)
    board.Add(zona_gndd)

    # 6. Validaciones previas al guardado
    print(f"Colocados {len(colocadas)} componentes electricos + {len(MOUNTING)} mecanicos.")
    print(f"Total redes en placa: {len(netinfo)}")

    # Verificar margenes
    fuera = []
    for ref, fp in colocadas.items():
        bb = fp.GetBoundingBox(False, False)
        if (bb.GetLeft() < mm(MARGEN) or bb.GetRight() > mm(W - MARGEN)
                or bb.GetTop() < mm(MARGEN) or bb.GetBottom() > mm(H - MARGEN)):
            fuera.append(ref)
    assert not fuera, f"Componentes fuera del margen ({MARGEN} mm): {fuera}"

    # Guardar placa
    pcbnew.SaveBoard(PCB, board)
    print(f"Placa guardada exitosamente en {PCB}")

    # Rellenar zonas con kicad-cli
    print("Rellenando zonas con kicad-cli...")
    r_fill = subprocess.run([KICAD_CLI, "pcb", "drc", "--refill-zones", "--save-board", PCB],
                            capture_output=True, text=True)
    print(f"Relleno completado (exit {r_fill.returncode})")

    # Exportar render SVG de la placa
    svg_out = os.path.join(DIR, "..", "pcb", "sam17-power-v5.svg")
    os.makedirs(os.path.dirname(svg_out), exist_ok=True)
    subprocess.run([KICAD_CLI, "pcb", "export", "svg", "--page-size-mode", "2",
                   "--layers", "F.Cu,B.Cu,F.SilkS,Edge.Cuts", "-o", svg_out, PCB],
                  capture_output=True, text=True)
    print(f"Render SVG exportado a {svg_out}")

    print("\nOK: build_pcb v5 completado exitosamente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
