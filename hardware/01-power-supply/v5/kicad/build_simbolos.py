"""Genera sam17.kicad_sym: los simbolos propios de la fuente v5, uno por pieza
que KiCad no trae.

    python build_simbolos.py

POR QUE EXISTE. La libreria anterior se escribio a mano y TODOS sus simbolos
de circuito integrado y de modulo tenian el pinout mal (#474): el TPS26630
con una numeracion inventada que llevaba SHDN e IN_SYS a masa, el LM74502 con
GND en +24 V y GATE en GND, el MSP430 sin alimentar (DVCC/DVSS en dos GPIO),
los TRACO con +Vout en Common y el LT1963A en un SOT-223 que solo existe en
version FIJA. Nada de eso lo vio ninguna puerta, porque ninguna comparaba el
simbolo con la hoja.

Aqui cada pinout es una TABLA con la pagina de la hoja de la que sale, y
check_simbolos.py la cruza contra el fichero generado y contra los pads de la
huella. Donde KiCad ya trae el simbolo correcto (TPS26631PWP, LT1963AEQ,
LT3015Q, CSD18534Q5A, TL431DBZ, LM393...) se usa el suyo y no se copia aqui.
"""
from __future__ import annotations

import os

DIR = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(DIR, "sam17.kicad_sym")
DS = "docs/reference/datasheets"

# lado: "L" izquierda, "R" derecha. Orden de arriba abajo dentro de cada lado.
# tipo: el electrico de KiCad. Las salidas de los modulos DC-DC van PASSIVE a
# proposito: la masa de referencia de un modulo (Common, -Vout, 0V) no es una
# salida de potencia, y declararla asi da conflictos de ERC entre modulos que
# comparten GNDA. Los rieles que generan llevan PWR_FLAG en la hoja.
SIMBOLOS: dict[str, dict] = {
    "LM74502DDF": {
        "ref": "U",
        "fp": "Package_TO_SOT_SMD:SOT-23-8",
        "hoja": f"{DS}/lm74502.pdf p. 3 (Figure 5-1 DDF y Table 5-1)",
        "desc": "Controlador de MOSFET con proteccion de inversion de polaridad y OV",
        "pines": [
            ("5", "VS", "power_in", "L"),
            ("1", "EN/UVLO", "input", "L"),
            ("7", "OV", "input", "L"),
            ("2", "GND", "power_in", "L"),
            ("6", "GATE", "output", "R"),
            ("8", "SRC", "passive", "R"),
            ("4", "VCAP", "passive", "R"),
            ("3", "NC", "no_connect", "R"),
        ],
    },
    "MSP430FR2111IPW16": {
        "ref": "U",
        "fp": "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
        "hoja": f"{DS}/msp430fr2111.pdf p. 8 (Figure 7-1, 16-Pin PW)",
        "desc": "MCU MSP430FR2111, FRAM 3.75 KB, TSSOP-16",
        "pines": [
            ("5", "DVCC", "power_in", "L"),
            ("6", "DVSS", "power_in", "L"),
            ("4", "RST/NMI/SBWTDIO", "bidirectional", "L"),
            ("3", "TEST/SBWTCK", "input", "L"),
            ("7", "P2.7/XIN", "bidirectional", "L"),
            ("8", "P2.6/XOUT", "bidirectional", "L"),
            ("2", "P1.0", "bidirectional", "R"),
            ("1", "P1.1", "bidirectional", "R"),
            ("16", "P1.2", "bidirectional", "R"),
            ("15", "P1.3", "bidirectional", "R"),
            ("14", "P1.4", "bidirectional", "R"),
            ("13", "P1.5", "bidirectional", "R"),
            ("12", "P1.6", "bidirectional", "R"),
            ("11", "P1.7", "bidirectional", "R"),
            ("10", "P2.0", "bidirectional", "R"),
            ("9", "P2.1", "bidirectional", "R"),
        ],
    },
    "TPS70933DBV": {
        "ref": "U",
        "fp": "Package_TO_SOT_SMD:SOT-23-5",
        "hoja": "TI SBVS186H (TPS709) p. 3, Table 5-1, columna DBV",
        "desc": "LDO 30 V / 150 mA, 3.3 V fijo. EN <= 6.5 V: se deja al aire",
        "pines": [
            ("1", "IN", "power_in", "L"),
            ("3", "EN", "input", "L"),
            ("2", "GND", "power_in", "L"),
            ("5", "OUT", "power_out", "R"),
            ("4", "NC", "no_connect", "R"),
        ],
    },
    "TRACO_THN_Single": {
        "ref": "PS",
        "fp": "Converter_DCDC:Converter_DCDC_TRACO_THL30-xxxxWI_THT",
        "hoja": f"{DS}/traco_thn20wi.pdf p. 4 (Pinout, columna Single)",
        "desc": "TRACO THN 20WI salida simple, 1x1 pulgada",
        "pines": [
            ("1", "+Vin", "power_in", "L"),
            ("2", "-Vin", "power_in", "L"),
            ("6", "Remote", "input", "L"),
            ("3", "+Vout", "passive", "R"),
            ("4", "Trim", "passive", "R"),
            ("5", "-Vout", "passive", "R"),
        ],
    },
    "TRACO_THN_Dual": {
        "ref": "PS",
        "fp": "Converter_DCDC:Converter_DCDC_TRACO_THL30-xxxxWI_THT",
        "hoja": f"{DS}/traco_thn30wi.pdf p. 5 (Pinout, columna Dual)",
        "desc": "TRACO THN 30WI salida doble, 1x1 pulgada",
        "pines": [
            ("1", "+Vin", "power_in", "L"),
            ("2", "-Vin", "power_in", "L"),
            ("6", "Remote", "input", "L"),
            ("3", "+Vout", "passive", "R"),
            ("4", "Common", "passive", "R"),
            ("5", "-Vout", "passive", "R"),
        ],
    },
    "Mornsun_URB_YMD-20WR3": {
        "ref": "PS",
        "fp": "sam17:Converter_DCDC_Mornsun_URB_YMD-20WR3_Horizontal_THT",
        "hoja": f"{DS}/mornsun_urb_ymd20wr3.pdf p. 6 (Pin-Out, encapsulado horizontal)",
        "desc": "Mornsun URB_YMD-20WR3, DC-DC aislado 20 W, 1500 VDC",
        "pines": [
            ("3", "Vin", "power_in", "L"),
            ("2", "GND", "power_in", "L"),
            ("1", "Ctrl", "input", "L"),
            ("4", "+Vo", "passive", "R"),
            ("5", "Trim", "passive", "R"),
            ("6", "0V", "passive", "R"),
        ],
    },
    "Mornsun_K78xxT-1000R3": {
        "ref": "PS",
        "fp": "sam17:Converter_DCDC_Mornsun_K78_T-1000R3_SMD",
        "hoja": f"{DS}/mornsun_k78_t1000r3.pdf p. 5 (Pin-Out y PCB Layout)",
        "desc": "Mornsun K78_T-1000R3, regulador conmutado NO aislado 1 A, SMD",
        "pines": [
            ("1", "+Vin", "power_in", "L"),
            ("2", "+Vin", "power_in", "L"),
            ("10", "Remote", "input", "L"),
            ("3", "GND", "power_in", "L"),
            ("7", "GND", "power_in", "L"),
            ("4", "+Vout", "passive", "R"),
            ("5", "+Vout", "passive", "R"),
            ("6", "Vadj", "passive", "R"),
        ],
    },
}

# El SCR va aparte porque no es una caja: se dibuja como tiristor.
# nxp-bt151-500r.pdf p. 2, Table 2: 1 = K, 2 = A, 3 = G (mb = A).
BT151 = {
    "hoja": f"{DS}/nxp-bt151-500r.pdf p. 2 (Table 2, Pinning information)",
    "pines": [("1", "K", "passive"), ("2", "A", "passive"), ("3", "G", "input")],
}

PASO = 2.54
LARGO = 2.54


def _fuente(t: float = 1.27) -> str:
    return f"(effects (font (size {t} {t})))"


def _prop(nombre: str, valor: str, x: float, y: float, oculto: bool = False) -> str:
    h = " (hide yes)" if oculto else ""
    return (f'    (property "{nombre}" "{valor}" (at {x:g} {y:g} 0) '
            f'{_fuente()}{h})')


def _caja(nombre: str, d: dict) -> str:
    izq = [p for p in d["pines"] if p[3] == "L"]
    der = [p for p in d["pines"] if p[3] == "R"]
    filas = max(len(izq), len(der))
    alto = (filas + 1) * PASO
    largo_nombre = max(len(p[1]) for p in d["pines"])
    ancho = max(10.16, round((largo_nombre * 1.27 * 2 + 5.08) / PASO) * PASO)
    x0, x1 = -ancho / 2, ancho / 2
    y0 = alto / 2
    out = [f'  (symbol "{nombre}"',
           "    (exclude_from_sim no)", "    (in_bom yes)", "    (on_board yes)",
           _prop("Reference", d["ref"], x0, y0 + 1.27),
           _prop("Value", nombre, x0, -y0 - 1.27),
           _prop("Footprint", d["fp"], 0, 0, True),
           _prop("Datasheet", d["hoja"], 0, 0, True),
           _prop("Description", d["desc"], 0, 0, True),
           f'    (symbol "{nombre}_0_1"',
           f"      (rectangle (start {x0:g} {y0:g}) (end {x1:g} {-y0:g}) "
           "(stroke (width 0.254) (type default)) (fill (type background)))",
           "    )",
           f'    (symbol "{nombre}_1_1"']
    for lado, pines in (("L", izq), ("R", der)):
        for i, (num, pin, tipo, _l) in enumerate(pines):
            y = round(y0 - PASO * (i + 1), 2)
            x, ang = (x0 - LARGO, 0) if lado == "L" else (x1 + LARGO, 180)
            out.append(f"      (pin {tipo} line (at {x:g} {y:g} {ang}) (length {LARGO}) "
                       f'(name "{pin}" {_fuente()}) (number "{num}" {_fuente()}))')
    out += ["    )", "  )"]
    return "\n".join(out)


def _tiristor() -> str:
    n = "BT151-500R"
    p = {num: (nom, tipo) for num, nom, tipo in BT151["pines"]}
    return "\n".join([
        f'  (symbol "{n}"',
        "    (exclude_from_sim no)", "    (in_bom yes)", "    (on_board yes)",
        _prop("Reference", "SCR", 3.81, 1.27),
        _prop("Value", n, 3.81, -1.27),
        _prop("Footprint", "Package_TO_SOT_THT:TO-220-3_Vertical", 0, 0, True),
        _prop("Datasheet", BT151["hoja"], 0, 0, True),
        _prop("Description", "Tiristor 500 V 12 A", 0, 0, True),
        f'    (symbol "{n}_0_1"',
        # Triangulo con la punta hacia ABAJO: corriente de A (arriba) a K (abajo).
        "      (polyline (pts (xy -2.54 1.27) (xy 2.54 1.27) (xy 0 -1.27) (xy -2.54 1.27)) "
        "(stroke (width 0.254) (type default)) (fill (type outline)))",
        "      (polyline (pts (xy -2.54 -1.27) (xy 2.54 -1.27)) "
        "(stroke (width 0.254) (type default)) (fill (type none)))",
        "      (polyline (pts (xy 1.27 -1.27) (xy 2.54 -2.54)) "
        "(stroke (width 0.254) (type default)) (fill (type none)))",
        "    )",
        f'    (symbol "{n}_1_1"',
        f'      (pin {p["2"][1]} line (at 0 3.81 270) (length 2.54) (name "{p["2"][0]}" {_fuente()}) (number "2" {_fuente()}))',
        f'      (pin {p["1"][1]} line (at 0 -3.81 90) (length 2.54) (name "{p["1"][0]}" {_fuente()}) (number "1" {_fuente()}))',
        f'      (pin {p["3"][1]} line (at 5.08 -2.54 180) (length 2.54) (name "{p["3"][0]}" {_fuente()}) (number "3" {_fuente()}))',
        "    )", "  )"])


def main() -> int:
    partes = ["(kicad_symbol_lib", "  (version 20241209)",
              '  (generator "sam17-build_simbolos")', '  (generator_version "10.0")']
    for nombre in sorted(SIMBOLOS):
        partes.append(_caja(nombre, SIMBOLOS[nombre]))
    partes.append(_tiristor())
    partes.append(")")
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(partes) + "\n")
    print(f"{len(SIMBOLOS) + 1} simbolos escritos en {os.path.basename(SALIDA)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
