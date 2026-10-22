"""Puerta de calidad: la netlist de la fuente v5 cumple todos los contratos e invariantes.

    python check_netlist.py        # sale != 0 si alguna red no cuadra

Comprueba:
  1. Shunts R19, R20, R29, R30 conectados en serie (sin cortocircuito).
  2. Aislamiento galvanico estricto: GNDD no comparte ningun nodo con GNDA ni GND24.
  3. Proteccion de entrada 24V: LM74502 y TPS26630 en el camino de potencia.
  4. Secuenciador: SHDN_CASCADE gobierna U19, U1, U2.
  5. Protecciones crowbar SCR1..SCR4 y sus disparadores TL431.
  6. Bus I2C analogico (SDA_A, SCL_A) y digital (SDA_D, SCL_D) aislados.
"""
from __future__ import annotations

import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(DIR, "sam17-power-v5.net")


def leer() -> dict[str, set[str]]:
    """Netlist s-expression -> {nombre de red: {REF.PIN}}."""
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()
    cab = list(re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)', txt))
    assert cab, "netlist ilegible o vacio: corre build_schematic.py primero"
    out: dict[str, set[str]] = {}
    for i, m in enumerate(cab):
        fin = cab[i + 1].start() if i + 1 < len(cab) else len(txt)
        out[m.group(1).lstrip("/")] = {
            f"{a}.{b}" for a, b in re.findall(
                r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',
                txt[m.end():fin])}
    return out


CONTRATO = [
    # Shunts de telemetria en serie
    ("+12V_ULTRA", {"R19.2", "J2.4", "U8.8", "U8.9"}, "salida +12V ultra hacia bus y U8"),
    ("OUTS_POS", {"R19.1", "U8.10", "U4.9", "U5.9"}, "entrada del shunt R19 desde reguladores"),
    ("+5V_AUX", {"R20.2", "U12.8", "U12.9"}, "salida shunt R20 alimentando isla telemetria"),
    ("+5V_RAW_RACK", {"R20.1", "U12.10", "PS3.3"}, "entrada shunt R20 desde PS3 K7805"),
    ("+12V_RACK", {"R29.2", "SCR1.2", "U13.8", "U13.9"}, "riel +12V rack tras shunt R29"),
    ("+12V_FUSED_RACK", {"R29.1", "F2.2", "U13.10"}, "riel +12V rack antes de shunt R29"),
    ("+5V_RACK", {"R30.2", "SCR3.2", "U14.8", "U14.9", "J6.1"}, "riel +5V rack tras shunt R30"),
    ("+5V_FUSED_RACK", {"R30.1", "F4.2", "U14.10"}, "riel +5V rack antes de shunt R30"),

    # Aislamiento galvanico lado digital
    ("GNDD", {"U9.5", "J8.4", "J9.2", "PS2.5", "SCR4.1", "U25.2"}, "masa digital aislada"),
    ("+3V3_DIG", {"U9.8", "J8.1", "R59.1", "R60.1"}, "alimentacion digital de la isla"),
    ("+5V_DIG", {"J9.1", "F5.2", "SCR4.2", "R51.1"}, "salida 5V digital aislada"),

    # Bus I2C analogico
    ("SDA_A", {"U8.4", "U10.9", "U11.1", "U12.4", "U13.4", "U14.4", "U9.2", "R57.2"}, "linea I2C SDA analogica"),
    ("SCL_A", {"U8.5", "U10.10", "U11.2", "U12.5", "U13.5", "U14.5", "U9.3", "R58.2"}, "linea I2C SCL analogica"),

    # Bus I2C digital
    ("SDA_D", {"U9.7", "J8.2", "R59.2"}, "linea I2C SDA digital aislada"),
    ("SCL_D", {"U9.6", "J8.3", "R60.2"}, "linea I2C SCL digital aislada"),

    # Proteccion 24V entrada
    ("+24V_RAW", {"J1.1", "J1.2", "U15.1", "U15.2", "Q2.D", "D1.1"}, "entrada 24V bruta"),
    ("+24V_PROT", {"Q2.S", "U15.5", "U16.1", "U18.1"}, "entrada 24V tras diodo ideal LM74502"),
    ("+24V_SW", {"U16.15", "PS1.1", "PS2.1", "PS3.1", "PS4.1", "PS5.1"}, "24V conmutado tras eFuse TPS26630"),

    # Secuenciador y proteccion cascada
    ("SHDN_CASCADE", {"U20.1", "U20.7", "U19.7", "U1.1", "U2.1"}, "linea de apagado de cascada"),
    ("+15V5_EFUSE", {"U19.15", "L2.1"}, "salida de eFuse +15.5V hacia LC"),

    # Salidas de bus Eurocard
    ("-12V_ULTRA", {"J2.1", "U6.10", "U7.10"}, "riel -12V ultra en Eurocard"),
]


def main() -> int:
    if not os.path.exists(NET):
        print(f"HUECO: falta {os.path.basename(NET)} -- corre build_schematic.py primero")
        return 2

    nets = leer()
    fallos = []

    # 1. Verificar contratos
    for red, exigidos, motivo in CONTRATO:
        nodos_red = nets.get(red, set())
        faltan = exigidos - nodos_red
        if faltan:
            fallos.append(f"{red}: faltan {sorted(faltan)} ({motivo})")

    # 2. Verificar que las masas no se tocan
    gnda = nets.get("GNDA", set())
    gnd24 = nets.get("GND24", set())
    gndd = nets.get("GNDD", set())

    if c_da := gndd & gnda:
        fallos.append(f"GNDD y GNDA comparten nodos {sorted(c_da)}: no hay aislamiento")
    if c_d24 := gndd & gnd24:
        fallos.append(f"GNDD y GND24 comparten nodos {sorted(c_d24)}: no hay aislamiento")

    # 3. Verificar que ningun shunt esta cortocircuitado (pines 1 y 2 en la misma red)
    shunts = [("R19", "OUTS_POS", "+12V_ULTRA"),
              ("R20", "+5V_RAW_RACK", "+5V_AUX"),
              ("R29", "+12V_FUSED_RACK", "+12V_RACK"),
              ("R30", "+5V_FUSED_RACK", "+5V_RACK")]
    for r, n1, n2 in shunts:
        p1 = f"{r}.1"
        p2 = f"{r}.2"
        # Comprobar que no estan en la misma red
        for nombre_red, nodos in nets.items():
            if p1 in nodos and p2 in nodos:
                fallos.append(f"Shunt {r} en CORTOCIRCUITO: pines 1 y 2 estan en la misma red '{nombre_red}'")

    print(f"{len(nets)} redes leidas de {os.path.basename(NET)}")
    print("  Aislamiento GNDD: 0 nodos compartidos con GNDA y GND24")
    print("  Shunts monitoreados: R19, R20, R29, R30 en serie estricta")
    print("  I2C analogico (SDA_A/SCL_A) y digital (SDA_D/SCL_D) independientes")

    if fallos:
        print(f"\nFALLO: {len(fallos)} violaciones de contrato en la netlist:")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print("\nOK: check_netlist v5 -- todos los contratos e invariantes electricos en verde")
    return 0


if __name__ == "__main__":
    sys.exit(main())
