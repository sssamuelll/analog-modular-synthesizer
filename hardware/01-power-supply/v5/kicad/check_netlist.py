"""Puerta: la netlist de la fuente v5 hace lo que dicen los presupuestos.

    python check_netlist.py        # 0 verde, 1 rojo, 2 falta el netlist

La version de #474 solo comprobaba que ciertos pines estuvieran en ciertas
redes, y con eso dejo pasar una placa que no arrancaba: INA226 que chocaban de
direccion con el ADS1115, una R_SET que ponia los +12 V ultra a 24 V, los TL431
de los crowbar cortocircuitando la puerta en vez de dispararla, clamps que
pegaban las entradas del ADC a 0,3 V...

Esta comprueba RESULTADOS: lee el netlist y los valores de bom.csv y CALCULA
lo que el circuito va a hacer, contra la cifra del presupuesto que lo pide.

  1. Contratos de topologia (redes con sus pines).
  2. Masas: GNDD aislada; GND24 y GNDA unidas SOLO por NT1.
  3. Direcciones I2C, calculadas de los pines A0/A1/ADDR (unicas y las de la doc).
  4. Tensiones calculadas: R_SET de las cascadas, trim de PS4/PS5, divisores de
     U1/U2, UVLO/OVP de U16, OVP de U19, umbrales de D-F4 contra la ventana de
     secuencia_budget.py y disparos de D-F6.
  5. Patillas que no admiten lo que tienen: EN del TPS709, PGFB/VIOC de las
     cascadas, SHDN de U19 fuera de D-F4, orientacion de TL431 y BAT54S,
     UVLO y FLT de U19, Schottky de rueda libre, pull-down de SHDN_M5 y R_GK.
"""
from __future__ import annotations

import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.dirname(DIR)
NET = os.path.join(DIR, "sam17-power-v5.net")
sys.path.insert(0, V5)

from bom_valores import paralelo, valor  # noqa: E402


def leer() -> dict[str, set[str]]:
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()
    cab = list(re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)', txt))
    assert cab, "netlist ilegible o vacio"
    out: dict[str, set[str]] = {}
    for i, m in enumerate(cab):
        fin = cab[i + 1].start() if i + 1 < len(cab) else len(txt)
        out[m.group(1).lstrip("/")] = {
            f"{a}.{b}" for a, b in re.findall(
                r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', txt[m.end():fin])}
    return out


CONTRATO = [
    ("+24V_RAW", {"J1.1", "D1.1", "Q2.1", "Q2.2", "Q2.3", "U15.5", "U15.8", "U15.1"},
     "entrada; FUENTE de Q2 y VS/SRC del LM74502 (proteccion de polaridad)"),
    ("+24V_PROT", {"Q2.5", "U16.1", "U16.2", "U16.3", "U16.6", "R12.1"},
     "drenador de Q2 -> IN e IN_SYS del eFuse U16"),
    ("+24V_SW", {"U16.18", "U16.19", "U16.20", "PS1.1", "PS2.3", "PS3.1", "PS3.2",
                 "PS4.1", "PS5.1"}, "salida de U16 a los cinco convertidores"),
    ("GND24", {"J1.2", "PS1.2", "PS2.2", "PS3.3", "PS3.7", "PS4.2", "PS5.2", "U16.9",
               "U16.21", "U17.6", "U18.2", "NT1.1"}, "retorno del ladrillo"),
    ("+15V5_RAW", {"PS4.3", "U19.1", "U19.2", "U19.3", "U19.6", "R35.1"},
     "PS4 -> eFuse U19, con el OVP sensando ANTES del LC (#334)"),
    ("+15V5_EFUSE", {"U19.18", "U19.19", "U19.20", "L2.1"}, "U19 -> L2"),
    ("+15V5_LC", {"L2.2", "C3.1", "C1.1", "FB1.1", "R39.1", "R22.1"}, "nodo del LC"),
    ("+15V5_FILT", {"FB1.2", "D10.1", "U1.2", "D12.1"}, "entrada de U1 con su TVS"),
    ("-15V5_FILT", {"FB2.2", "D11.2", "U2.3", "D13.2"}, "entrada de U2 (TAB del LT3015)"),
    ("+13V1", {"U1.4", "U4.1", "U4.2", "U5.1", "U5.2", "C17.1"}, "+13,1 V"),
    ("-12V9", {"U2.5", "U6.1", "U6.13", "U7.1", "U7.13", "C18.2"}, "-12,9 V"),
    ("OUTS_POS", {"U4.9", "U5.9", "R15.2", "R16.2", "R19.1", "U8.10"},
     "punto de regulacion del +12 V ultra, antes del shunt de U8"),
    ("+12V_ULTRA", {"R19.2", "J2.4", "J7.4", "U8.8", "U8.9"}, "+12 V ultra a las dos salidas de bus"),
    ("-12V_ULTRA", {"U6.10", "U7.10", "R17.2", "R18.2", "J2.1", "J7.1"}, "-12 V ultra"),
    ("SHDN_CASCADE", {"U20.1", "U20.7", "U1.1", "U2.1", "R43.1", "R44.2"},
     "hilo D-F4: los dos comparadores y los dos pre-reguladores"),
    ("+12V_RACK", {"R29.2", "SCR1.2", "U13.8", "J3.1"}, "+12 V de rack a la fila de invitados"),
    ("-12V_RACK", {"F3.2", "SCR2.1", "J3.3", "R24.1"}, "-12 V de rack"),
    ("+5V_RACK", {"R30.2", "SCR3.2", "U14.8", "J3.4"}, "+5 V de rack"),
    ("+5V_AUX", {"R20.2", "J6.1", "U12.8", "U20.8", "R63.1"}, "+5 V auxiliar: modulo 2 y la logica de la fuente"),
    ("+5V_DIG", {"F5.2", "SCR4.2", "J9.1"}, "+5 V digital aislado"),
    ("SDA_A", {"U8.4", "U10.9", "U11.1", "U12.4", "U13.4", "U14.4", "U9.2", "R57.2"}, "I2C analogico"),
    ("SCL_A", {"U8.5", "U10.10", "U11.2", "U12.5", "U13.5", "U14.5", "U9.3", "R58.2"}, "I2C analogico"),
    ("SDA_D", {"U9.7", "J8.2", "R59.2"}, "I2C digital aislado"),
    ("SCL_D", {"U9.6", "J8.3", "R60.2"}, "I2C digital aislado"),
]

# Direcciones que documenta docs/modules/01-power-supply.md (Telemetria).
DIRECCIONES = {"U8": 0x40, "U12": 0x41, "U13": 0x44, "U14": 0x45, "U10": 0x48, "U11": 0x49}


def red_de(nets: dict[str, set[str]], nodo: str) -> str | None:
    """Red del nodo, o None si esta al aire (KiCad la llama unconnected-...)."""
    red = next((n for n, nodos in nets.items() if nodo in nodos), None)
    return None if red is None or red.startswith("unconnected-") else red


def direccion_ina226(a1: str, a0: str) -> int:
    """ina226.pdf Table 6-2: A1/A0 en {GND, VS, SDA, SCL} -> 0x40..0x4F."""
    cod = {"GNDA": 0, "+5V_AUX": 1, "SDA_A": 2, "SCL_A": 3}
    return 0x40 + 4 * cod[a1] + cod[a0]


def resistencias_entre(nets: dict[str, set[str]], red_a: str, red_b: str) -> list[str]:
    """Designadores R* con una patilla en cada red."""
    out = []
    for nodo in nets.get(red_a, set()):
        ref, pin = nodo.split(".")
        if not ref.startswith("R") or ref.startswith("RV"):
            continue
        otro = f"{ref}.{'2' if pin == '1' else '1'}"
        if otro in nets.get(red_b, set()):
            out.append(ref)
    return sorted(out)


def cerca(real: float, objetivo: float, tol: float) -> bool:
    return abs(real - objetivo) <= tol


def main() -> int:
    if not os.path.exists(NET):
        print("HUECO: falta sam17-power-v5.net -- corre build_schematic.py")
        return 2
    nets = leer()
    fallos: list[str] = []

    # 1. Contratos
    for red, exigidos, motivo in CONTRATO:
        if faltan := exigidos - nets.get(red, set()):
            fallos.append(f"{red}: faltan {sorted(faltan)} ({motivo})")

    # 2. Masas
    gnda, gnd24, gndd = nets.get("GNDA", set()), nets.get("GND24", set()), nets.get("GNDD", set())
    puentes = {n.split(".")[0] for n in gnd24} & {n.split(".")[0] for n in gnda}
    puentes -= {"PS1", "PS4", "PS5"}          # el aislamiento de un modulo no es un puente
    if puentes != {"NT1"}:
        fallos.append(f"GND24 y GNDA se tocan en {sorted(puentes)}: tiene que ser SOLO NT1")
    toca_gndd = ({n.split(".")[0] for n in gndd} & ({n.split(".")[0] for n in gnda} |
                                                      {n.split(".")[0] for n in gnd24})) - {"PS2", "U9"}
    if toca_gndd:
        fallos.append(f"GNDD comparte componente con GNDA/GND24: {sorted(toca_gndd)} (M1)")

    # 3. Direcciones I2C
    dirs: dict[str, int] = {}
    for u in ("U8", "U12", "U13", "U14"):
        dirs[u] = direccion_ina226(red_de(nets, f"{u}.1"), red_de(nets, f"{u}.2"))
    dirs["U10"] = {"GNDA": 0x48, "+5V_AUX": 0x49, "SDA_A": 0x4A, "SCL_A": 0x4B}[red_de(nets, "U10.1")]
    a = [red_de(nets, f"U11.{p}") == "+5V_AUX" for p in ("5", "6", "7")]   # A2, A1, A0
    dirs["U11"] = 0x48 + 4 * a[0] + 2 * a[1] + a[2]
    vistas: dict[int, str] = {}
    for u, d in dirs.items():
        if d in vistas:
            fallos.append(f"I2C: {u} y {vistas[d]} comparten la direccion 0x{d:02X}")
        vistas[d] = u
        if d != DIRECCIONES[u]:
            fallos.append(f"I2C: {u} queda en 0x{d:02X} y la documentacion dice 0x{DIRECCIONES[u]:02X}")

    # 4. Tensiones calculadas con los valores de bom.csv
    rset_p = resistencias_entre(nets, "SET_POS", "GNDA")
    rset_n = resistencias_entre(nets, "SET_NEG", "GNDA")
    n_p = len({n.split(".")[0] for n in nets["SET_POS"] if n.startswith("U")})
    n_n = len({n.split(".")[0] for n in nets["SET_NEG"] if n.startswith("U")})
    v_ultra_p = 100e-6 * n_p * paralelo(*rset_p)
    v_ultra_n = 100e-6 * n_n * paralelo(*rset_n)
    for nombre, v in (("+12 V ultra", v_ultra_p), ("-12 V ultra", v_ultra_n)):
        if not cerca(v, 12.0, 0.012):
            fallos.append(f"{nombre}: SET da {v:.3f} V (100 uA x reguladores x R_SET), no 12,000")

    def trim_thn(r: str) -> float:   # nota TRACO THN xx-xx13WI: G 10000, H 5110, K 12.5, L 2.5
        return 2.5 + 12.5 + 10000 * 2.5 / (valor(r) + 5110)
    for ps, r, menos in (("PS4", "R32", "GNDA"), ("PS5", "R33", "-15V5_RAW")):
        if red_de(nets, f"{r}.1") != f"TRIM_{ps}" or red_de(nets, f"{r}.2") != menos:
            fallos.append(f"{ps}: {r} tiene que ir de Trim a -Vout ({menos}) para subir la salida")
        elif not cerca(trim_thn(r), 15.5, 0.05):
            fallos.append(f"{ps}: el trim da {trim_thn(r):.2f} V, no 15,5")

    lo1 = 1.210 * (1 + valor("R5") / valor("R6"))
    hi1 = 1.210 * (1 + (valor("R5") + valor("RV2")) / valor("R6"))
    lo2 = 1.220 * (1 + valor("R7") / valor("R8"))
    hi2 = 1.220 * (1 + (valor("R7") + valor("RV3")) / valor("R8"))
    if not lo1 + 0.2 <= 13.10 <= hi1 - 0.2:
        fallos.append(f"U1: el divisor cubre {lo1:.2f}..{hi1:.2f} V y 13,10 no cae dentro con margen")
    if not lo2 + 0.2 <= 12.90 <= hi2 - 0.2:
        fallos.append(f"U2: el divisor cubre -{lo2:.2f}..-{hi2:.2f} V y -12,90 no cae dentro con margen")

    total = valor("R12") + valor("R13") + valor("R14")
    uvlo = 1.2 * total / (valor("R13") + valor("R14"))
    ovp16 = 1.2 * total / valor("R14")
    if not (17.0 <= uvlo <= 19.0 and 32.0 <= ovp16 <= 33.5):
        fallos.append(f"U16: UVLO {uvlo:.2f} V / OVP {ovp16:.2f} V fuera de 18 / 33 V")
    ovp19 = 1.2 * (1 + valor("R35") / valor("R36"))
    if not cerca(ovp19, 16.55, 0.05):
        fallos.append(f"U19: OVP a {ovp19:.2f} V; check_absmax.py modela 16,55 V")

    import secuencia_budget as sb  # noqa: E402  (vive en v5/)
    suelo, techo = sb.suelo_ventana_v(), sb.techo_ventana_v()
    err = sb.error_umbral_v()
    umbral_p = 2.495 * (1 + valor("R39") / valor("R40"))
    umbral_n = 2.495 * valor("R42") / valor("R41")
    for canal, u in (("D-F4 +", umbral_p), ("D-F4 -", umbral_n)):
        if not suelo + err + sb.HISTERESIS_V <= u <= techo - err:
            fallos.append(f"{canal}: umbral {u:.3f} V fuera de la ventana util "
                          f"{suelo + err + sb.HISTERESIS_V:.3f}..{techo - err:.3f} V (secuencia_budget.py)")
    if red_de(nets, "U20.3") != "SENSE_POS" or red_de(nets, "U20.6") != "SENSE_NEG":
        fallos.append("D-F4: SENSE_POS tiene que ir a IN1+ y SENSE_NEG a IN2- (polaridad)")
    if red_de(nets, "R41.1") != "VREF_2V5":
        fallos.append("D-F4: el divisor del canal - tiene que colgar de VREF, no del +5 V")
    if "U21.1" not in nets.get("VREF_2V5", set()) or not resistencias_entre(nets, "+5V_AUX", "VREF_2V5"):
        fallos.append("U21: el TL431 de referencia necesita su resistencia de polarizacion")
    for r_h in ("R67", "R69"):
        if "SHDN_CASCADE" not in (red_de(nets, f"{r_h}.1"), red_de(nets, f"{r_h}.2")):
            fallos.append(f"D-F4: falta la histeresis {r_h} desde SHDN_CASCADE")

    disparos = {"1": ("R45", "R47", 13.8), "2": ("R46", "R48", 13.8),
                "3": ("R49", "R50", 5.8), "4": ("R51", "R52", 5.65)}
    for n, (ra, rb, obj) in disparos.items():
        v = 2.495 * (1 + valor(ra) / valor(rb))
        if not cerca(v, obj, 0.05):
            fallos.append(f"crowbar {n}: dispara a {v:.2f} V, no a {obj}")
        scr = f"SCR{n}"
        u = {"1": "U22", "2": "U23", "3": "U24", "4": "U25"}[n]
        if red_de(nets, f"{u}.1") != f"TLK_CB{n}" or red_de(nets, f"{u}.3") != red_de(nets, f"{scr}.1"):
            fallos.append(f"{u}: catodo al PNP y anodo al catodo de {scr} (TL431 referido al riel)")
        if red_de(nets, f"{scr}.3") == red_de(nets, f"{u}.1"):
            fallos.append(f"{u}: el catodo del TL431 NO puede ir a la puerta (la cortocircuita)")

    # 5. Patillas
    if red_de(nets, "U18.3") is not None:
        fallos.append("U18: el EN del TPS709 aguanta 7 V: tiene que quedar al aire")
    for u in ("U4", "U5"):
        if red_de(nets, f"{u}.6") != "+13V1":
            fallos.append(f"{u}: PGFB a IN (+13V1), si no el arranque rapido no se apaga")
    for u in ("U6", "U7"):
        if red_de(nets, f"{u}.5") != "-12V9":
            fallos.append(f"{u}: PGFB a IN (-12V9)")
        if red_de(nets, f"{u}.7") is not None:
            fallos.append(f"{u}: VIOC al aire (lt3094-rev-b.pdf p. 9)")
    if red_de(nets, "U19.13") == "SHDN_CASCADE":
        fallos.append("U19: su SHDN no puede colgar de D-F4, que mira la salida de U19")
    # U19 sin UVLO: a GND el umbral interno es 15.1..15.9 V (tps2663.pdf p. 6),
    # por encima del riel de 15.5 V que protege. A IN_SYS por >= 300k (p. 20).
    r_uv = resistencias_entre(nets, "+15V5_RAW", "UVLO_U19")
    if red_de(nets, "U19.7") != "UVLO_U19" or not r_uv or min(valor(r) for r in r_uv) < 300e3:
        fallos.append("U19: UVLO a IN_SYS (+15V5_RAW) por >= 300k; a GND el umbral "
                      "interno de 15.1..15.9 V queda por encima del riel de 15.5 V")
    # El FLT de U19 al MSP430, nunca al SHDN de U16: en UVLO baja FLT
    # (tps2663.pdf p. 19) y U16 no arrancaria nunca.
    if red_de(nets, "U19.15") != "FLT_U19" or "U17.16" not in nets.get("FLT_U19", set()):
        fallos.append("U19: FLT a P1.2 del MSP430 (sobretension de riel = abandono)")
    elif red_de(nets, "U19.15") == red_de(nets, "U16.13"):
        fallos.append("U19: su FLT no puede ir al SHDN de U16: en UVLO baja y U16 no arranca")
    if not resistencias_entre(nets, "+3V3_MCU", "FLT_U19"):
        fallos.append("U19: FLT es drenador abierto y necesita pull-up a +3V3_MCU")
    if (red_de(nets, "D19.1"), red_de(nets, "D19.2")) != ("+15V5_EFUSE", "GNDA"):
        fallos.append("D19: Schottky con K en OUT de U19 y A en GNDA (tps2663.pdf p. 36, 38)")
    # SHDN de U16 con pull-down: el pull-up interno da hasta 10 uA (p. 7) y
    # tiene que quedar por debajo de V(SHUTF) = 0.8 V con el MCU sin levantarlo.
    r_pd = resistencias_entre(nets, "SHDN_M5", "GND24")
    if not r_pd or paralelo(*r_pd) * 10e-6 >= 0.8:
        fallos.append("U16: SHDN_M5 necesita pull-down <= 80k a GND24 (sin el, U16 "
                      "enciende antes de que el MCU lea la FRAM)")
    # D-F6: el dV/dt de 200 V/us del BT151 se garantiza con R_GK = 100 ohm
    # (nxp-bt151-500r.pdf p. 6); con la puerta mas floja vale 50 V/us.
    for n in ("1", "2", "3", "4"):
        r_gk = resistencias_entre(nets, f"GATE_SCR{n}", red_de(nets, f"SCR{n}.1") or "")
        if not r_gk or paralelo(*r_gk) > 100.0:
            fallos.append(f"SCR{n}: R_GK <= 100 ohm (dV/dt de 200 V/us, nxp-bt151-500r.pdf p. 6)")
    for d, ain in (("D14", "AIN0"), ("D15", "AIN1"), ("D16", "AIN2"), ("D17", "AIN3")):
        if (red_de(nets, f"{d}.3"), red_de(nets, f"{d}.1"), red_de(nets, f"{d}.2")) != (ain, "GNDA", "+5V_AUX"):
            fallos.append(f"{d}: BAT54S con COM en {ain}, A en GNDA y K en +5V_AUX")
    for nodo in ("Q2.1", "Q2.4", "Q2.5"):
        if red_de(nets, nodo) is None:
            fallos.append(f"{nodo} sin red")

    print(f"{len(nets)} redes leidas de {os.path.basename(NET)}")
    print("  direcciones I2C: " + ", ".join(f"{u} 0x{d:02X}" for u, d in sorted(dirs.items())))
    print(f"  +-12 V ultra por R_SET: {v_ultra_p:.3f} / -{v_ultra_n:.3f} V")
    print(f"  trim PS4/PS5: {trim_thn('R32'):.3f} / -{trim_thn('R33'):.3f} V")
    print(f"  U1 {lo1:.2f}..{hi1:.2f} V, U2 -{lo2:.2f}..-{hi2:.2f} V")
    print(f"  U16 UVLO {uvlo:.2f} V / OVP {ovp16:.2f} V; U19 OVP {ovp19:.2f} V")
    print(f"  D-F4: umbrales {umbral_p:.3f} / -{umbral_n:.3f} V en la ventana "
          f"{suelo + err + sb.HISTERESIS_V:.3f}..{techo - err:.3f} V")

    if fallos:
        print(f"\nFALLO: {len(fallos)}")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\nOK: check_netlist v5 -- topologia y valores calculados en verde")
    return 0


if __name__ == "__main__":
    sys.exit(main())
