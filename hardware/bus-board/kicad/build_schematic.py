"""Genera sam17-bus.kicad_sch: bus board de 6 slots con PTC e indicador de falla.

    python build_schematic.py

NO usa el KiCAD-MCP-Server, al reves que el modulo 1. Escribe el s-expr a pelo
apoyandose en symlib.py y verifica con kicad-cli, que es la herramienta oficial.
Dos motivos:

  1. El server ya trunco un .kicad_sch de este proyecto a 215 bytes devolviendo
     success:true, y una hoja VACIA pasa el ERC con 0 avisos
     (hardware/tools/README.md). Un fallo que no se ve no es un fallo: es una
     trampa.
  2. Esta placa son 6 bloques IDENTICOS. Generarlos en un bucle es tres lineas;
     colocarlos por RPC son ~200 llamadas que hay que acertar una a una.

Que hay en cada slot (x6), y por que:

  * Un peine Eurorack de 16 pines SIN caja ni llave. Doepfer lo prohibe
    expresamente: "it's not allowed to use bus boards with polarized pin
    headers (boxed pin headers with code gap). These force the user to connect
    the bus cable in a certain direction which may be the wrong one". La
    orientacion la marca la franja roja = -12 V, serigrafiada.
  * Un KK-254 de 4 pines para los modulos SAM17, este SI con llave: es un
    conector propietario y ahi la llave protege en vez de estorbar.
  * DOS PTC, uno por riel. En +12 V y en -12 V. **Nunca en masa** — 1.3 ohm en
    el retorno son 94 cents de desafinacion (ground_budget.py).
  * Un LED con 4k7 en paralelo con cada PTC. Con el PTC intacto caen ~0.1 V y
    el LED ni se entera; con el PTC disparado quedan los 12 V y se enciende.
    Senala QUE conector fallo sin un solo componente activo.

Polaridad de los dos LED, que es la trampa fina: en +12 V la corriente cae del
riel hacia el modulo, y en -12 V sube del modulo hacia el riel. Al dibujar los
dos bloques con el lado de MODULO arriba, los dos LED quedan con el anodo
arriba — identicos. Si se dibujara -12 V "mirando hacia abajo" saldria del
reves y no encenderia jamas.

Y el +5 V del bus Eurorack va sin conectar A PROPOSITO (pines 11-12), igual que
CV y Gate. El +5 V del SAM17 sale por J6 con retorno dedicado porque el
backlight del LCD va conmutado (sec.10.1 del modulo 1); meterlo en este bus le
devolveria la corriente por la masa de audio. Serigrafiado como NC.
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import symlib  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(DIR, "sam17-bus.kicad_sch")
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
KICAD_FP = os.environ.get(
    "KICAD_FOOTPRINTS", r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

REV, DATE = "A", "2026-08-15"
SLOTS = 6

# TODA coordenada de esta hoja es multiplo de 1.27 mm (50 mil), que es la
# rejilla de conexion de KiCad. Fuera de rejilla el ERC saca un aviso por cada
# extremo — salieron 306 de golpe — y, peor, deja de ser evidente que dos cosas
# que se ven alineadas lo esten. Se declara todo en unidades de rejilla y se
# comprueba en revisar_rejilla().
G = 1.27


def g(n: float) -> float:
    return round(n * G, 3)


XC0, PASO = g(60), g(45)        # columna del slot 0 y paso entre slots
XB = g(16)                      # desplazamiento de la rama LED+R respecto a XC

SYMS = {
    "euro": "Connector_Generic:Conn_02x08_Odd_Even",
    "sam17": "Connector:Conn_01x04_Pin",
    "ptc": "Device:Polyfuse",
    "led": "Device:LED",
    "r": "Device:R",
}
FOOTPRINT = {
    "euro": "Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical",
    "sam17": "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
    "ptc": "sam17:PTC_Radial_P5.08mm_Dual",
    "led": "LED_THT:LED_D3.0mm",
    "r": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "feed": "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-04P_1x04_P5.00mm",
}
VALOR = {"ptc": "0.25A", "led": "FALLA", "r": "4k7"}

# El bus Eurorack por PARES de pines: los dos pines de cada par van al mismo
# sitio (Doepfer: "left and right pins are always connected on the bus board").
# El par 1 es el de la FRANJA ROJA y es -12 V. Equivocar esta fila destruye
# todos los modulos que se enchufen, asi que va en la lista de verificar antes
# de fabricar igual que BR1 (issue #11).
PARES_EURO = ["-12S", "GND", "GND", "GND", "+12S", None, None, None]
ETIQUETA_PAR = ["-12V", "GND", "GND", "GND", "+12V", "+5V NC", "CV NC", "GATE NC"]

SHEET_UUID = "b0a17ea5-0000-4000-8000-5a17b0a5d000"

_wires: list[tuple[float, float, float, float]] = []
_juncs: list[tuple[float, float]] = []
_labels: list[tuple[str, float, float]] = []
_ncs: list[tuple[float, float]] = []
_syms: list[tuple[str, str, str, float, float, int]] = []   # lib,ref,val,x,y,rot
_libs: set[str] = set()


def uid() -> str:
    return str(uuid.uuid4())


def hilo(x1: float, y1: float, x2: float, y2: float) -> None:
    assert (x1, y1) != (x2, y2), f"cable de longitud cero en {x1},{y1}"
    _wires.append((round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)))


def pon(lib: str, ref: str, val: str, x: float, y: float, rot: int = 0) -> None:
    _libs.add(lib)
    _syms.append((lib, ref, val, x, y, rot))


def pin(lib: str, num: str, x: float, y: float, rot: int = 0):
    return symlib.pin_abs(lib, num, x, y, rot)


def bloque_riel(xc: float, k: int, riel: str, y_top: float,
                riel_arriba: bool, ref_f: str, ref_d: str, ref_r: str) -> None:
    """Un PTC con su LED+R en paralelo, entre el riel y el modulo.

    y_top       = y del nodo de arriba
    riel_arriba = True en +12 V (el riel manda desde arriba), False en -12 V

    Los dos bloques se dibujan con el LED en la misma postura para que los dos
    queden con el anodo arriba y no haya dos polaridades que recordar. Sale
    solo: en +12 V la corriente baja del riel al modulo, y en -12 V sube del
    modulo al riel, asi que con el lado "que esta a mas potencial" siempre
    arriba, el anodo tambien.
    """
    # LED (rot 90 => anodo arriba) y R, en la rama de la derecha
    yd, yr = y_top + g(3), y_top + g(13)
    pon(SYMS["led"], ref_d, VALOR["led"], xc + XB, yd, 90)
    pon(SYMS["r"], ref_r, VALOR["r"], xc + XB, yr, 0)
    a_led = pin(SYMS["led"], "2", xc + XB, yd, 90)      # anodo
    k_led = pin(SYMS["led"], "1", xc + XB, yd, 90)      # catodo
    r1 = pin(SYMS["r"], "1", xc + XB, yr, 0)
    r2 = pin(SYMS["r"], "2", xc + XB, yr, 0)
    assert abs(a_led[1] - y_top) < 1e-6, "el anodo tiene que caer en el nodo de arriba"
    hilo(*k_led, *r1)

    # PTC en la columna principal, alineado con la rama por los dos extremos
    yf = y_top + g(7)
    pon(SYMS["ptc"], ref_f, VALOR["ptc"], xc, yf, 0)
    f1 = pin(SYMS["ptc"], "1", xc, yf, 0)
    f2 = pin(SYMS["ptc"], "2", xc, yf, 0)

    hilo(xc, y_top, *f1)                       # nodo de arriba
    hilo(xc, y_top, xc + XB, y_top)
    _juncs.append((xc, y_top))
    y_bot = r2[1]
    hilo(*f2, xc, y_bot)                       # nodo de abajo
    hilo(xc, y_bot, xc + XB, y_bot)
    _juncs.append((xc, y_bot))

    # etiqueta al lado modulo, simbolo de potencia al lado riel
    y_m, y_r = (y_bot, y_top) if riel_arriba else (y_top, y_bot)
    d_m, d_r = (g(5), -g(5)) if riel_arriba else (-g(5), g(5))
    hilo(xc, y_m, xc, y_m + d_m)
    _labels.append((f"{riel}S{k+1}", xc, y_m + d_m))
    hilo(xc, y_r, xc, y_r + d_r)
    pon(f"power:{riel}V", f"#PWR{riel[0]}{k+1}", f"{riel}V", xc, y_r + d_r, 0)


def gnd(xs: float, ys: list[float], hacia: float, dx: float, ref: str) -> None:
    """Une varios pines de masa en una vertical y les cuelga un simbolo GND.

    El simbolo sale HACIA UN LADO (dx), no hacia abajo. Bajar era lo natural y
    estaba mal: en el peine Eurorack los pines de +12 V estan POR DEBAJO de los
    de masa, asi que la bajada les pasaba por encima y KiCad une un extremo de
    cable que aterriza en mitad de otro cable. Resultado: +12S1 cortocircuitado
    contra GND, con el ERC gritandolo. Saliendo de lado no se cruza con nada.
    """
    for y in ys:
        hilo(xs, y, hacia, y)
    for a, b in zip(ys, ys[1:]):
        hilo(hacia, a, hacia, b)
    for y in ys[1:-1]:
        _juncs.append((hacia, y))
    hilo(hacia, ys[-1], hacia + dx, ys[-1])
    _juncs.append((hacia, ys[-1]))
    pon("power:GND", ref, "GND", hacia + dx, ys[-1], 0)


def bandera(net: str, x: float, y: float, dx: float, ref: str) -> None:
    """PWR_FLAG: le dice al ERC que esta red la alimenta alguien de fuera.

    Sin esto los tres rieles salen como 'Input Power pin not driven': en esta
    placa no hay ni un regulador, la potencia entra por J7 desde el modulo 1.
    """
    hilo(x, y, x + dx, y)
    _juncs.append((x, y))
    pon("power:PWR_FLAG", ref, "PWR_FLAG", x + dx, y, 0)


Y_EURO, Y_SAM17 = g(79), g(111)     # y de los dos peines de cada slot


def construir() -> None:
    # ---- alimentacion de entrada (viene del punto de estrella del modulo 1)
    xj, yj = g(16), g(48)
    pon(SYMS["sam17"], "J7", "PSU +12/G/G/-12", xj, yj, 0)
    p = [pin(SYMS["sam17"], str(n), xj, yj, 0) for n in "1234"]
    hilo(*p[0], g(40), p[0][1]); hilo(g(40), p[0][1], g(40), g(36))
    pon("power:+12V", "#PWRIN+", "+12V", g(40), g(36), 0)
    gnd(p[1][0], [p[1][1], p[2][1]], g(33), g(5), "#PWRING")
    hilo(*p[3], g(27), p[3][1]); hilo(g(27), p[3][1], g(27), g(60))
    pon("power:-12V", "#PWRIN-", "-12V", g(27), g(60), 0)
    bandera("+12V", g(40), g(36), g(5), "#FLG+")
    bandera("GND", g(38), g(50), g(5), "#FLGG")
    bandera("-12V", g(27), g(60), g(5), "#FLG-")

    for k in range(SLOTS):
        xc = XC0 + k * PASO
        bloque_riel(xc, k, "+12", y_top=g(12), riel_arriba=True,
                    ref_f=f"F{2*k+1}", ref_d=f"D{2*k+1}", ref_r=f"R{2*k+1}")
        bloque_riel(xc, k, "-12", y_top=g(126), riel_arriba=False,
                    ref_f=f"F{2*k+2}", ref_d=f"D{2*k+2}", ref_r=f"R{2*k+2}")

        # ---- peine Eurorack de 16 pines -------------------------------
        pon(SYMS["euro"], f"J{k+1}", "EURORACK 16P", xc, Y_EURO, 0)
        gnd_izq, gnd_der = [], []
        for i, destino in enumerate(PARES_EURO):
            pi = pin(SYMS["euro"], str(2 * i + 1), xc, Y_EURO, 0)
            pp = pin(SYMS["euro"], str(2 * i + 2), xc, Y_EURO, 0)
            if destino is None:                       # +5V, CV, Gate
                _ncs.extend([pi, pp])
            elif destino == "GND":
                gnd_izq.append(pi[1]); gnd_der.append(pp[1])
            else:
                for px, hacia in ((pi, xc - g(10)), (pp, xc + g(12))):
                    hilo(*px, hacia, px[1])
                    _labels.append((f"{destino}{k+1}", hacia, px[1]))
        gnd(xc - g(4), gnd_izq, xc - g(10), -g(5), f"#PWRGL{k+1}")
        gnd(xc + g(6), gnd_der, xc + g(12), g(5), f"#PWRGR{k+1}")

        # ---- peine SAM17 de 4 pines (con llave) -----------------------
        pon(SYMS["sam17"], f"P{k+1}", "SAM17 4P", xc, Y_SAM17, 0)
        q = [pin(SYMS["sam17"], str(n), xc, Y_SAM17, 0) for n in "1234"]
        for px, etq in ((q[0], f"+12S{k+1}"), (q[3], f"-12S{k+1}")):
            hilo(*px, xc + g(11), px[1])
            _labels.append((etq, xc + g(11), px[1]))
        gnd(q[1][0], [q[1][1], q[2][1]], xc + g(11), g(5), f"#PWRGP{k+1}")


# --------------------------------------------------------------------------
def check_footprints() -> None:
    """Antes de tocar el fichero, a proposito.

    Misma leccion que el modulo 1: escribir(SCH) trunca el fichero nada mas
    empezar, asi que un assert posterior deja una hoja vacia en disco — y una
    hoja vacia pasa el ERC con 0 avisos.
    """
    rotos = []
    for clave, fp in FOOTPRINT.items():
        lib, _, nombre = fp.partition(":")
        base = (os.path.join(DIR, "sam17.pretty") if lib == "sam17"
                else os.path.join(KICAD_FP, f"{lib}.pretty"))
        if not os.path.isfile(os.path.join(base, f"{nombre}.kicad_mod")):
            rotos.append(f"{clave} -> {fp}")
    assert not rotos, f"huellas que no estan en disco: {rotos}"


def revisar_rejilla() -> None:
    """Todo en multiplos de 1.27 mm. Fuera de rejilla el ERC saca un aviso por
    extremo (salieron 306) y, lo que de verdad importa, dos cosas que se ven
    alineadas pueden no estarlo."""
    fuera = []
    for x1, y1, x2, y2 in _wires:
        for v in (x1, y1, x2, y2):
            if abs(round(v / G) * G - v) > 1e-6:
                fuera.append(v)
    for _lib, ref, _v, x, y, _r in _syms:
        for v in (x, y):
            if abs(round(v / G) * G - v) > 1e-6:
                fuera.append(f"{ref}:{v}")
    assert not fuera, f"fuera de rejilla de {G} mm: {sorted(set(map(str, fuera)))[:8]}"


def revisar_hilos() -> None:
    """Todo extremo de cable tiene que morir en un pin, una etiqueta, un NC,
    o en otro extremo de cable. Un extremo suelto es una red que no existe.

    KiCad une pin y cable con ~1 mm de tolerancia y el ERC da por bueno un
    trazado torcido: esa fue la trampa que se comio una revision entera del
    modulo 1. Aqui se exige coincidencia EXACTA."""
    anclas = {(round(x, 3), round(y, 3)) for _n, x, y in _labels}
    anclas |= {(round(x, 3), round(y, 3)) for x, y in _ncs}
    for lib, _ref, _val, x, y, rot in _syms:
        for num in symlib.pines(lib):
            anclas.add(pin(lib, num, x, y, rot))
    extremos: dict[tuple, int] = {}
    for x1, y1, x2, y2 in _wires:
        for p in ((x1, y1), (x2, y2)):
            extremos[p] = extremos.get(p, 0) + 1
    sueltos = [p for p, n in extremos.items() if n == 1 and p not in anclas]
    assert not sueltos, f"extremos de cable en el aire: {sueltos[:8]}"


def escribir() -> None:
    out = ['(kicad_sch', '\t(version 20260101)', '\t(generator "sam17-bus")',
           '\t(generator_version "10.0")', f'\t(uuid {SHEET_UUID})',
           '\t(paper "A3")', '\t(title_block',
           '\t\t(title "Bus board — distribucion ±12 V")',
           f'\t\t(date "{DATE}")', f'\t\t(rev "{REV}")',
           '\t\t(company "SAM17 — Sintetizador analogico modular")',
           '\t\t(comment 1 "6 slots: peine Eurorack 16P SIN llave + KK-254 4P con llave")',
           '\t\t(comment 2 "PTC por riel con LED de falla en paralelo. NUNCA PTC en masa")',
           '\t\t(comment 3 "Masa = PLANO en B.Cu. Presupuesto en ground_budget.py: 1.2 cents")',
           '\t\t(comment 4 "Par 1 del peine = FRANJA ROJA = -12 V (Doepfer). Verificar antes de fabricar")',
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

    for lib, ref, val, x, y, rot in _syms:
        fp = ""
        for clave, s in SYMS.items():
            if s == lib:
                fp = FOOTPRINT["feed"] if ref == "J7" else FOOTPRINT[clave]
        oculto = ref.startswith("#")
        out += ['\t(symbol', f'\t\t(lib_id "{lib}")', f'\t\t(at {x} {y} {rot})',
                '\t\t(unit 1)', '\t\t(exclude_from_sim no)',
                f'\t\t(in_bom {"no" if oculto else "yes"})',
                f'\t\t(on_board {"no" if oculto else "yes"})', '\t\t(dnp no)',
                f'\t\t(uuid "{uid()}")']
        campos = [("Reference", ref, y - 7.0, oculto),
                  ("Value", val, y + 7.0, False),
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
        for num in sorted(symlib.pines(lib)):
            out += [f'\t\t(pin "{num}"', f'\t\t\t(uuid "{uid()}")', '\t\t)']
        out += ['\t\t(instances', '\t\t\t(project "sam17-bus"',
                f'\t\t\t\t(path "/{SHEET_UUID}"', f'\t\t\t\t\t(reference "{ref}")',
                '\t\t\t\t\t(unit 1)', '\t\t\t\t)', '\t\t\t)', '\t\t)', '\t)']

    out += ['\t(sheet_instances', '\t\t(path "/"', '\t\t\t(page "1")',
            '\t\t)', '\t)', ')']
    with open(SCH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


def main() -> None:
    check_footprints()
    construir()
    revisar_rejilla()
    revisar_hilos()
    escribir()
    piezas = [s for s in _syms if not s[1].startswith("#")]
    print(f"{len(piezas)} componentes, {len(_wires)} cables, "
          f"{len(_labels)} etiquetas, {len(_ncs)} no-connect")

    erc = subprocess.run([KICAD_CLI, "sch", "erc", "--severity-all",
                          "--exit-code-violations", SCH],
                         capture_output=True, text=True)
    print(erc.stdout.strip()[-700:] or erc.stderr.strip()[-700:])
    net = os.path.join(DIR, "sam17-bus.net")
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "-o", net, SCH],
                   capture_output=True, text=True, check=True)
    for herr, ext in (("svg", "svg"), ("pdf", "pdf")):
        subprocess.run([KICAD_CLI, "sch", "export", herr, "-o",
                        os.path.join(DIR, "..", "schematics"), SCH],
                       capture_output=True, text=True)
    print(f"netlist -> {net}")
    sys.exit(erc.returncode)


if __name__ == "__main__":
    main()
