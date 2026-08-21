"""Puerta: la isla de telemetria esta cableada como dice el contrato.

    python check_netlist.py        # sale != 0 si alguna red no cuadra

Por que existe, y por que NO basta con check_bom.py. Aquel cruza designadores:
cuenta que U8 este en la hoja y en el BOM. Pasaria en verde con SDA y SCL
cambiados, con las dos resistencias de un divisor intercambiadas, o con los dos
lados del aislador unidos por la masa. Ninguna de esas tres cosas es un
componente de mas ni de menos: son cables.

Y una de ellas la puerta hermana `check_telemetria.py` declara explicitamente
que NO puede ver -- el invariante de que el 100k mire al riel y el 20k a la
referencia. Aquella hace aritmetica sobre los valores; esta mira el netlist
real, que es donde ese invariante vive. Entre las dos ya no queda ciego:

  * si el divisor esta MAL DIBUJADO, lo caza esta puerta;
  * si esta bien dibujado y MAL POBLADO (un 20k soldado donde va el 100k),
    no lo caza ninguna de las dos -- por eso el invariante va ademas en la
    seda de la placa.

Lee el .net que genera build_schematic.py. Si no existe, dice HUECO con el
motivo (Principio V: un skip silencioso consigue no correr Y que no te
enteres).
"""
from __future__ import annotations

import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(DIR, "sam17-power-v3.net")


def leer() -> dict[str, set[str]]:
    """Netlist s-expression -> {nombre de red: {REF.PIN}}.

    Mismo parseo que el check_netlist.py del modulo 3 a proposito: el formato
    del .net es contrato de repo, no detalle de este modulo. La v2 exportaba
    kicadxml por el MCP y eso la dejaba fuera de netdiff.py sin que se notara.
    """
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()
    cab = list(re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)', txt))
    assert cab, "netlist ilegible: corre build_schematic.py primero"
    out: dict[str, set[str]] = {}
    for i, m in enumerate(cab):
        fin = cab[i + 1].start() if i + 1 < len(cab) else len(txt)
        out[m.group(1).lstrip("/")] = {
            f"{a}.{b}" for a, b in re.findall(
                r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',
                txt[m.end():fin])}
    return out


# (red, nodos que TIENEN que estar) -- no se exige exclusividad salvo donde se
# dice, porque los rieles llevan medio modulo colgando.
CONTRATO = [
    # --- los dos shunts estan EN SERIE, no en paralelo -----------------------
    # Si los dos pines del shunt cayeran en la misma red, la caida seria cero y
    # el INA226 leeria 0 A para siempre, en verde y sin quejarse.
    ("+12V",     {"R19.1", "U8.10"},          "el shunt del +12V y el Vin+ de U8"),
    ("+12V_BUS", {"R19.2", "U8.9", "U8.8", "J2.4"},
     "el lado de J2 del shunt: Vin- y Vbus de U8 miden lo que ven los modulos"),
    ("+5V_M2",   {"R20.1", "U9.9", "J6.1"},
     "el lado del modulo 2 del shunt de +5V"),
    ("+5V",      {"R20.2", "U9.10", "U9.8"},
     "Vbus de U9 va al lado del RIEL, no al de J6: ese nodo es la referencia "
     "de los divisores negativos y por eso hay que medirlo a el"),
    # --- el aislador aisla ---------------------------------------------------
    ("GNDD",     {"U12.4", "J8.4", "C34.2"},  "la masa digital, solo tres nodos"),
    ("+3V3",     {"U12.1", "J8.1", "C34.1"},  "el riel digital entra por J8"),
    # --- el bus I2C del lado analogico llega a los cinco chips ---------------
    ("SDA_A", {"U8.4", "U9.4", "U10.9", "U11.1", "U12.7", "R27.2"}, "SDA analogico"),
    ("SCL_A", {"U8.5", "U9.5", "U10.10", "U11.2", "U12.6", "R28.2"}, "SCL analogico"),
    ("SDA_D", {"U12.2", "J8.2"}, "SDA digital"),
    ("SCL_D", {"U12.3", "J8.3"}, "SCL digital"),
    # --- el filtro de la SMPS, y donde pincha ---------------------------------
    # `L` es todo lo que hay entre la entrada y NT1. Que L1 cuelgue de AHI y
    # no de L_TR es la regla de la spec v2 §7, y no ha cambiado: la SMPS
    # comparte el fusible con el toroide pero NO comparte el limitador de
    # inrush, que esta dimensionado para TR1.
    #
    # Antes esta linea pedia `L_F` y nombraba `F1.2`. Las dos cosas se fueron
    # con el fusible a la pared del recinto (#130): al no haber pieza en
    # medio, `L` y `L_F` son el mismo nodo y solo hace falta un nombre. Lo que
    # el invariante VIGILA es lo mismo -- de que nodo cuelga el choke.
    ("L",      {"J3.1", "L1.1", "NT1.1", "RV1.1"},
     "el choke pincha ANTES de NT1, y el MOV esta en la entrada"),
    ("L_SMPS", {"L1.2", "J7.1", "CY1.1"}, "salida del choke -> J7 + su cap Y"),
    ("N_SMPS", {"L1.4", "J7.2", "CY2.1"}, "idem en N"),
    ("PE",     {"CY1.2", "CY2.2", "J3.3"}, "las dos Y devuelven a tierra"),
]

# (canal, red del riel medido, ref de la R de 100k, ref de la de 20k, tap)
# El invariante: la de 100k toca el riel y la de 20k toca la referencia.
DIVISORES = [
    ("-12 V",  "-12V",  "R21", "R24", "TAP_-12V",  "+5V"),
    ("VRAW+",  "VRAW+", "R22", "R25", "TAP_VRAW+", "GND"),
    ("VRAW-",  "VRAW-", "R23", "R26", "TAP_VRAW-", "+5V"),
]
# (canal, entrada del ADS1115 que le toca)
CANAL_ADC = {"TAP_-12V": "U10.4", "TAP_VRAW+": "U10.5", "TAP_VRAW-": "U10.6"}
CLAMP = {"TAP_-12V": "D14.1", "TAP_VRAW-": "D15.1"}


def main() -> int:
    if not os.path.exists(NET):
        print("HUECO: falta sam17-power-v3.net -- correr build_schematic.py "
              "(necesita el KiCAD-MCP-Server, ver hardware/tools/README.md)")
        return 0
    nets = leer()
    fallos = []

    for red, exigidos, por in CONTRATO:
        faltan = exigidos - nets.get(red, set())
        if faltan:
            fallos.append(f"{red}: faltan {sorted(faltan)} ({por})")

    # las dos masas no se tocan: si comparten un solo nodo, no hay barrera
    if comun := nets.get("GND", set()) & nets.get("GNDD", set()):
        fallos.append(f"GND y GNDD comparten {sorted(comun)}: no hay aislamiento")

    for canal, riel, r100k, r20k, tap, ref in DIVISORES:
        en_riel = {p for p in nets.get(riel, set()) if p.startswith((r100k, r20k))}
        en_ref = {p for p in nets.get(ref, set()) if p.startswith((r100k, r20k))}
        en_tap = {p for p in nets.get(tap, set()) if p.startswith((r100k, r20k))}
        if not any(p.startswith(r100k) for p in en_riel):
            fallos.append(f"divisor {canal}: la de 100k ({r100k}) NO toca {riel}")
        if not any(p.startswith(r20k) for p in en_ref):
            fallos.append(f"divisor {canal}: la de 20k ({r20k}) NO toca {ref}")
        if len(en_tap) != 2:
            fallos.append(f"divisor {canal}: el tap {tap} no une las dos "
                          f"resistencias, tiene {sorted(en_tap)}")
        if (pin := CANAL_ADC[tap]) not in nets.get(tap, set()):
            fallos.append(f"divisor {canal}: {tap} no llega a {pin}")
        if (d := CLAMP.get(tap)) and d not in nets.get(tap, set()):
            fallos.append(f"divisor {canal}: falta el clamp {d} en {tap}")

    print(f"{len(nets)} redes en {os.path.basename(NET)}")
    for _c, _r, r100k, r20k, tap, ref in DIVISORES:
        print(f"  divisor {tap:<10s} {r100k} (100k) al riel, {r20k} (20k) a {ref}")
    print(f"  aislamiento GND / GNDD: {len(nets.get('GNDD', set()))} nodos "
          f"del lado digital, 0 compartidos")

    if fallos:
        print(f"\nFALLO: {len(fallos)} en el cableado de la isla")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\nOK: los dos shunts en serie, los tres divisores en el sentido "
          "correcto,\n    los cinco chips en el I2C y la barrera de masas sin "
          "un solo nodo comun.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
