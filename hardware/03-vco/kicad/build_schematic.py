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
}
FP = {
    "conn4": "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
    "reg5": "Package_TO_SOT_SMD:SOT-89-3",
    "reg33": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "vref": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "c": "Capacitor_SMD:C_0805_2012Metric",
    "tp": "TestPoint:TestPoint_Pad_D2.0mm",
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


def construir() -> None:
    bloque_alimentacion()
    bloque_testpoints()
    # Tarea 3: bloque_digital() -- 74HC14, TMP1075, 24AA02E, J2 (mazo GNDD)
    # Tarea 4: voz(idx) x4 -- SSI2130, DAC (AD5686R x3), jacks CV-IN/OUT


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
