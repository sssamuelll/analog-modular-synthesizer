"""Genera sam17-midicv.kicad_sch: DAC de 16 bits, 3 CV de 1 V/oct y GATE de 10 V.

    python build_schematic.py

Escribe el s-expr directamente y verifica con kicad-cli, igual que el bus board
y por el mismo motivo (hardware/tools/README.md).

LAS TRES DECISIONES QUE NO SON OBVIAS, y de donde salen:

1. **DOS MASAS SEPARADAS, y no se tocan en esta placa.**

   `GNDA` llega por J1 (el bus de +-12 V) y es la referencia de TODO lo
   analogico: la patilla GND del DAC, los amplificadores, los casquillos de los
   jacks. `GNDD` llega por J2, que es el retorno DEDICADO que el modulo 1 saca
   junto al +5 V (sec.10.1) porque el backlight del LCD va conmutado.

   Se unen en el punto de estrella del modulo 1 y **en ningun otro sitio**. Si
   se juntaran aqui, la corriente del backlight tendria dos caminos de vuelta y
   parte se iria por la masa analogica: 100 mA por unos 50 mohm son 5 mV, que
   amplificados por 2.8 son 14 mV, o sea **17 cents** de desafinacion que
   aparecen y desaparecen segun el brillo de la pantalla.

   Lo que SI cruza de un dominio al otro son las senales logicas (SPI, LCD,
   botones, gate). Da igual: el desnivel entre las dos masas son milivoltios y
   los umbrales logicos son cientos de milivoltios.

   Y por eso el DAC tiene VDD en +5 V pero **GND en GNDA**: su milliamperio de
   consumo vuelve por la masa analogica, que es donde tiene que estar
   referida su salida. Un mA sobre la masa del bus son 17 uV, 0.02 cents.

2. **VLOGIC va a +3V3, no a +5 V.** El AD5686R tiene una patilla de
   alimentacion de E/S aparte precisamente para esto. Atada a VDD = 5 V, el
   umbral VIH sube a 0.7 x 5 = 3.5 V y el Pi, que entrega 3.3 V, se queda por
   debajo: el SPI funcionaria a ratos y fallaria al calentarse. Con VLOGIC a
   3.3 V el umbral baja con ella y el margen vuelve a ser el de diseno.

3. **El GATE se construye con dos MOSFET, y son dos por una razon.** Uno solo
   invierte, y un gate invertido significa que **al encender, antes de que
   arranque el firmware, el GPIO esta en alta impedancia y todas las envolventes
   dispararian**. Con dos etapas el reposo es gate BAJO: Q1 en corte -> su
   drenador arriba -> Q2 en conduccion -> salida a cero. R14 ademas fija el
   gate de Q1 a masa para que no quede flotando mientras el Pi arranca.

El rango del CV baja de los 3-10 V de la tesis a **0-7 V**. Mismo span de 7
octavas y misma resolucion en cents, pero 3 V mas de margen contra el riel.
El motivo esta medido en ../tuning_budget.py. El offset absoluto no importa:
lo absorbe el trimmer de tono grueso del VCO, que hay que ajustar igual.
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

SCH = os.path.join(DIR, "sam17-midicv.kicad_sch")
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
KICAD_FP = os.environ.get(
    "KICAD_FOOTPRINTS", r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

REV, DATE = "A", "2026-08-15"
SHEET_UUID = "b0a17ea5-0000-4000-8000-11d1c0000002"
G = 1.27


def g(n: float) -> float:
    return round(n * G, 3)


# --------------------------------------------------------------- simbolos
SYM = {
    "conn2": "Connector:Conn_01x02_Pin",
    "conn4": "Connector:Conn_01x04_Pin",
    "conn16": "Connector_Generic:Conn_01x16",
    "pi": "Connector_Generic:Conn_02x20_Odd_Even",
    "dac": "sam17:AD5686RBRUZ",
    "opamp": "Amplifier_Operational:TL074",
    "r": "Device:R",
    "c": "Device:C",
    "pot": "Device:R_Potentiometer",
    "q": "Transistor_FET:2N7002",
    "sw": "Switch:SW_Push",
    "jack": "Connector_Audio:AudioJack2",
}
FP = {
    "conn2": "Connector_Molex:Molex_KK-254_AE-6410-02A_1x02_P2.54mm_Vertical",
    "conn4": "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
    "conn16": "Connector_PinHeader_2.54mm:PinHeader_1x16_P2.54mm_Vertical",
    "pi": "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
    "dac": "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
    "opamp": "Package_DIP:DIP-14_W7.62mm_Socket",
    "r": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "c": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "pot": "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical",
    "q": "Package_TO_SOT_SMD:SOT-23",
    "sw": "Button_Switch_THT:SW_PUSH_6mm",
    "jack": "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles",
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


def potencia(net: str, x: float, y: float, ref: str, rot: int = 0) -> None:
    _libs.add(f"power:{net}")
    _syms.append((f"power:{net}", 1, ref, net, x, y, rot, None))


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


# ------------------------------------------------------- mapa del Pi 40 pines
# Solo se cablea lo que usa el firmware (docs/modules/02-midi-cv.md). Los 5 V
# del Pi (pines 2 y 4) se dejan SIN CONECTAR a proposito: el Pi lleva su propia
# fuente USB (sec.3 del modulo 1) y unirlos seria alimentar uno desde el otro.
PI = {
    1: "+3V3", 6: "GNDD", 9: "GNDD", 14: "GNDD", 20: "GNDD", 25: "GNDD",
    30: "GNDD", 34: "GNDD", 39: "GNDD",
    7: "BTN_UP",       # GPIO4
    11: "BTN_DOWN",    # GPIO17
    36: "BTN_BACK",    # GPIO16
    37: "BTN_ENTER",   # GPIO26
    13: "GATE_IO",     # GPIO27
    31: "DAC_RESET",   # GPIO6
    22: "LCD_RS",      # GPIO25
    18: "LCD_EN",      # GPIO24
    16: "LCD_D4",      # GPIO23
    12: "LCD_D5",      # GPIO18
    10: "LCD_D6",      # GPIO15
    8: "LCD_D7",       # GPIO14
    19: "SDIN",        # GPIO10, MOSI
    23: "SCLK",        # GPIO11
    26: "SPI_CE1",     # GPIO7, CE1 -> device=1 como pide el firmware
}

# --------------------------------------------------------------- construccion
def canal_cv(idx: int, xc: float, yc: float) -> None:
    """Un buffer no inversor de ganancia 2.8, del DAC al jack.

    Se dibuja con cables de verdad y no con etiquetas: es LA cadena de senal de
    la placa y quien la revise tiene que poder seguirla con el dedo.
    """
    letra = "ABC"[idx]
    ref_u = "U2"
    pon("opamp", ref_u, "TL074H", xc, yc, 0, unidad=idx + 1)
    u = idx + 1
    n_mas, n_menos, n_out = {0: ("3", "2", "1"), 1: ("5", "6", "7"),
                             2: ("10", "9", "8")}[idx]
    p_mas = P("opamp", n_mas, xc, yc)
    p_menos = P("opamp", n_menos, xc, yc)
    p_out = P("opamp", n_out, xc, yc)

    # entrada: viene del DAC por etiqueta
    hilo(*p_mas, xc - g(20), p_mas[1])
    _labels.append((f"DAC_{letra}", xc - g(20), p_mas[1]))

    # nodo de realimentacion, a la izquierda y por debajo
    x_fb = xc - g(10)
    hilo(*p_menos, x_fb, p_menos[1])
    _juncs.append((x_fb, p_menos[1]))

    # R de arriba (18k) de la salida al nodo, por debajo del amplificador
    y_fb = yc + g(16)
    rh = f"R{idx*2+1}"
    pon("r", rh, "18k", xc, y_fb, 90)
    h1, h2 = P("r", "1", xc, y_fb, 90), P("r", "2", xc, y_fb, 90)
    hilo(*p_out, p_out[0], y_fb)
    hilo(p_out[0], y_fb, *max(h1, h2))
    hilo(*min(h1, h2), x_fb, y_fb)
    hilo(x_fb, y_fb, x_fb, p_menos[1])

    # R de abajo (10k) del nodo a masa analogica
    rl = f"R{idx*2+2}"
    x_rl = xc - g(16)
    pon("r", rl, "10k", x_rl, yc + g(8))
    l1, l2 = P("r", "1", x_rl, yc + g(8)), P("r", "2", x_rl, yc + g(8))
    hilo(x_fb, p_menos[1], x_rl, p_menos[1])
    hilo(x_rl, p_menos[1], *l1)
    hilo(*l2, l2[0], l2[1] + g(4))
    potencia("GNDA", l2[0], l2[1] + g(4), f"#PWRA{idx}")

    # salida al jack, con serie de 1k
    rs = f"R{idx+7}"
    x_rs = xc + g(14)
    pon("r", rs, "1k", x_rs, p_out[1], 90)
    s1, s2 = P("r", "1", x_rs, p_out[1], 90), P("r", "2", x_rs, p_out[1], 90)
    _juncs.append((p_out[0], p_out[1]))
    hilo(*p_out, *min(s1, s2))
    hilo(*max(s1, s2), max(s1, s2)[0] + g(4), p_out[1])
    _labels.append((f"CV{idx+1}", max(s1, s2)[0] + g(4), p_out[1]))


def construir() -> None:
    # ---- entradas de alimentacion -------------------------------------
    bloque("conn4", "J1", "BUS +12/G/G/-12", g(14), g(20), 0,
           {"1": "+12V", "2": "GNDA", "3": "GNDA", "4": "-12V"})
    bloque("conn2", "J2", "+5V/RTN (mod.1 J6)", g(14), g(34), 0,
           {"1": "+5V", "2": "GNDD"})

    # banderas: en esta placa no hay ni un regulador, todo entra de fuera
    for net, ref, yy in (("+12V", "#FLG1", g(12)), ("-12V", "#FLG2", g(16)),
                         ("+5V", "#FLG3", g(30)), ("GNDA", "#FLG4", g(24)),
                         ("GNDD", "#FLG5", g(38)), ("+3V3", "#FLG6", g(44))):
        _libs.add("power:PWR_FLAG")
        x = g(34)
        hilo(x, yy, x + g(4), yy)
        _labels.append((net, x, yy))
        _syms.append(("power:PWR_FLAG", 1, ref, "PWR_FLAG", x + g(4), yy, 0, None))

    # desacoplo de los rieles, junto al conector
    for i, (net, masa, val) in enumerate((("+12V", "GNDA", "100n"),
                                          ("-12V", "GNDA", "100n"),
                                          ("+5V", "GNDA", "10u"),
                                          ("+3V3", "GNDA", "100n"))):
        x, y = g(46) + g(10) * i, g(20)
        pon("c", f"C{i+1}", val, x, y)
        c1, c2 = P("c", "1", x, y), P("c", "2", x, y)
        hilo(*c1, c1[0], c1[1] - g(4))
        _labels.append((net, c1[0], c1[1] - g(4)))
        hilo(*c2, c2[0], c2[1] + g(4))
        potencia(masa, c2[0], c2[1] + g(4), f"#PWRC{i}")

    # ---- Raspberry Pi --------------------------------------------------
    bloque("pi", "J3", "RPi 3B+ GPIO", g(70), g(76), 0,
           {str(k): v for k, v in PI.items()}, largo=g(6))

    # ---- DAC ------------------------------------------------------------
    # GAIN a masa = x1 -> 0..2.5 V. RSTSEL a masa = arranca a fondo de escala
    # CERO, o sea CV = 0 V; con RSTSEL arriba arrancaria a media escala y el
    # sinte sonaria una nota sola al encender.
    bloque("dac", "U1", "AD5686RBRUZ", g(150), g(46), 0, {
        "1": "VREF", "2": "DAC_B", "3": "DAC_A", "4": "GNDA", "5": "+5V",
        "6": "DAC_C", "7": None, "8": None, "9": "GNDA", "10": "GNDA",
        "11": "+3V3", "12": "SCLK", "13": "SPI_CE1", "14": "SDIN",
        "15": "DAC_RESET", "16": "GNDA"}, largo=g(6))
    # condensador de la referencia
    x, y = g(178), g(60)
    pon("c", "C5", "100n", x, y)
    c1, c2 = P("c", "1", x, y), P("c", "2", x, y)
    hilo(*c1, c1[0], c1[1] - g(4))
    _labels.append(("VREF", c1[0], c1[1] - g(4)))
    hilo(*c2, c2[0], c2[1] + g(4))
    potencia("GNDA", c2[0], c2[1] + g(4), "#PWRVR")

    # ---- tres canales de CV ---------------------------------------------
    for i in range(3):
        canal_cv(i, g(230), g(24) + g(30) * i)

    # alimentacion del TL074 (unidad 5, la que solo lleva los rieles)
    pon("opamp", "U2", "TL074H", g(196), g(120), 0, unidad=5)
    for num, net in (("4", "+12V"), ("11", "-12V")):
        stub("opamp", num, g(196), g(120), 0, net, g(5), unidad=5)

    # ---- GATE -------------------------------------------------------------
    x_q = g(150)
    y_q1, y_q2 = g(112), g(130)
    for ref, yq, entrada, salida in (("Q1", y_q1, "GATE_G", "GATE_INV"),
                                     ("Q2", y_q2, "GATE_INV", "GATE_12")):
        bloque("q", ref, "2N7002", x_q, yq, 0,
               {"1": entrada, "2": "GNDD", "3": salida})
    # R de puerta y su fijacion a masa, para que no flote mientras arranca el Pi
    for ref, val, xx, yy, a, b in (
            ("R10", "1k", g(136), g(112), "GATE_IO", "GATE_G"),
            ("R14", "10k", g(128), g(120), "GATE_G", None),
            ("R11", "10k", g(158), g(104), "+12V", "GATE_INV"),
            ("R12", "2k", g(158), g(122), "+12V", "GATE_12"),
            ("R13", "10k", g(166), g(136), "GATE_12", None)):
        rot = 90 if a in ("GATE_IO", "GATE_G") else 0
        pon("r", ref, val, xx, yy, rot)
        p1, p2 = P("r", "1", xx, yy, rot), P("r", "2", xx, yy, rot)
        d = symlib.pin_dir(SYM["r"], "1", rot)
        hilo(*p1, p1[0] + d[0] * g(4), p1[1] + d[1] * g(4))
        _labels.append((a, p1[0] + d[0] * g(4), p1[1] + d[1] * g(4)))
        d = symlib.pin_dir(SYM["r"], "2", rot)
        fx, fy = p2[0] + d[0] * g(4), p2[1] + d[1] * g(4)
        hilo(*p2, fx, fy)
        if b is None:
            potencia("GNDD", fx, fy, f"#PWRG{ref}")
        else:
            _labels.append((b, fx, fy))
    # buffer del gate: unidad 4 del TL074
    pon("opamp", "U2", "TL074H", g(230), g(120), 0, unidad=4)
    for num, net in (("12", "GATE_12"), ("14", "GATE_OUT_B")):
        stub("opamp", num, g(230), g(120), 0, net, g(6), unidad=4)
    # seguidor: la entrada inversora va atada a la salida
    p13 = P("opamp", "13", g(230), g(120))
    p14 = P("opamp", "14", g(230), g(120))
    hilo(*p13, p13[0] - g(4), p13[1])
    hilo(p13[0] - g(4), p13[1], p13[0] - g(4), p13[1] + g(8))
    hilo(p13[0] - g(4), p13[1] + g(8), p14[0] + g(6), p13[1] + g(8))
    hilo(p14[0] + g(6), p13[1] + g(8), p14[0] + g(6), p14[1])
    _juncs.append((p14[0] + g(6), p14[1]))
    # serie de salida
    pon("r", "R15", "1k", g(248), g(120), 90)
    s1, s2 = P("r", "1", g(248), g(120), 90), P("r", "2", g(248), g(120), 90)
    hilo(*min(s1, s2), min(s1, s2)[0] - g(4), s1[1])
    _labels.append(("GATE_OUT_B", min(s1, s2)[0] - g(4), s1[1]))
    hilo(*max(s1, s2), max(s1, s2)[0] + g(4), s1[1])
    _labels.append(("GATE_OUT", max(s1, s2)[0] + g(4), s1[1]))

    # ---- jacks -----------------------------------------------------------
    for i, net in enumerate(("CV1", "CV2", "CV3", "GATE_OUT")):
        bloque("jack", f"J{i+4}", net, g(280), g(20) + g(14) * i, 0,
               {"S": net, "T": "GNDA"})

    # ---- LCD y contraste --------------------------------------------------
    bloque("conn16", "J8", "LCD 16x2 HD44780", g(320), g(60), 0, {
        "1": "GNDD", "2": "+5V", "3": "LCD_VO", "4": "LCD_RS", "5": "GNDD",
        "6": "LCD_EN", "7": None, "8": None, "9": None, "10": None,
        "11": "LCD_D4", "12": "LCD_D5", "13": "LCD_D6", "14": "LCD_D7",
        "15": "LCD_BLA", "16": "GNDD"}, largo=g(6))
    bloque("pot", "RV1", "10k", g(300), g(96), 0,
           {"1": "+5V", "2": "LCD_VO", "3": "GNDD"})
    pon("r", "R16", "47R", g(300), g(112), 90)
    b1, b2 = P("r", "1", g(300), g(112), 90), P("r", "2", g(300), g(112), 90)
    hilo(*min(b1, b2), min(b1, b2)[0] - g(4), b1[1])
    _labels.append(("+5V", min(b1, b2)[0] - g(4), b1[1]))
    hilo(*max(b1, b2), max(b1, b2)[0] + g(4), b1[1])
    _labels.append(("LCD_BLA", max(b1, b2)[0] + g(4), b1[1]))

    # ---- botones ----------------------------------------------------------
    for i, net in enumerate(("BTN_UP", "BTN_DOWN", "BTN_BACK", "BTN_ENTER")):
        xb, yb = g(300), g(130) + g(18) * i
        bloque("sw", f"SW{i+1}", net.split("_")[1], xb, yb, 0,
               {"1": net, "2": "GNDD"})
        pon("r", f"R{17+i}", "10k", xb + g(16), yb - g(6))
        u1, u2 = P("r", "1", xb + g(16), yb - g(6)), P("r", "2", xb + g(16), yb - g(6))
        hilo(*u1, u1[0], u1[1] - g(4))
        _labels.append(("+3V3", u1[0], u1[1] - g(4)))
        hilo(*u2, u2[0], u2[1] + g(4))
        _labels.append((net, u2[0], u2[1] + g(4)))


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


def revisar_pinout_dac() -> None:
    """El AD5686R lo dibujamos nosotros, asi que su pinout se contrasta aqui.

    El del TSSOP-16 NO es el del LFCSP-16: van desfasados dos pines. Copiar el
    diagrama equivocado pone VDD donde va una salida analogica.
    """
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


def revisar_rejilla() -> None:
    fuera = [v for x1, y1, x2, y2 in _wires for v in (x1, y1, x2, y2)
             if abs(round(v / G) * G - v) > 1e-6]
    fuera += [f"{s[2]}:{v}" for s in _syms for v in (s[4], s[5])
              if abs(round(v / G) * G - v) > 1e-6]
    assert not fuera, f"fuera de rejilla de {G} mm: {sorted(set(map(str, fuera)))[:8]}"


def revisar_fusiones() -> None:
    """Que no haya dos redes distintas unidas por un solape o una T.

    Ya paso dos veces en este repo y las dos llego al ERC en vez de saltar
    aqui. Ver hardware/tools/schcheck.py.
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
    out = ['(kicad_sch', '\t(version 20260101)', '\t(generator "sam17-midicv")',
           '\t(generator_version "10.0")', f'\t(uuid {SHEET_UUID})',
           '\t(paper "A3")', '\t(title_block',
           '\t\t(title "Modulo 02 — MIDI/CV: DAC 16 bits, 3x CV 1V/oct, GATE")',
           f'\t\t(date "{DATE}")', f'\t\t(rev "{REV}")',
           '\t\t(company "SAM17 — Sintetizador analogico modular")',
           '\t\t(comment 1 "GNDA (bus, J1) y GNDD (retorno dedicado, J2) NO se unen en esta placa")',
           '\t\t(comment 2 "VLOGIC del DAC a +3V3, no a +5V: si no, VIH=3.5V y el Pi no llega")',
           '\t\t(comment 3 "CV 0-7 V (la tesis usa 3-10). Presupuesto en ../tuning_budget.py")',
           '\t\t(comment 4 "GATE con dos MOSFET para que el reposo sea BAJO al arrancar")',
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
        out += ['\t\t(instances', '\t\t\t(project "sam17-midicv"',
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
                    os.path.join(DIR, "sam17-midicv.net"), SCH],
                   capture_output=True, text=True)
    sys.exit(erc.returncode)


if __name__ == "__main__":
    main()
