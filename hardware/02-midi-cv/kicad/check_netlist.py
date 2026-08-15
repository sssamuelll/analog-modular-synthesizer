"""Contrasta sam17-midicv.net contra lo que el diseno DICE que debe conectar.

    python check_netlist.py

El ERC saliendo a cero solo dice que no hay conflictos. Una hoja con VDD y
VLOGIC intercambiados, o con las dos masas unidas, pasa el ERC con cero avisos
y el fallo aparece meses despues como "a veces desafina".

Aqui se comprueban las cosas que, si estan mal, no se ven hasta que duelen.
"""
from __future__ import annotations

import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(DIR, "sam17-midicv.net")


def leer() -> dict[str, set[str]]:
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()
    cab = list(re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)', txt))
    assert cab, "netlist ilegible: corre build_schematic.py primero"
    out = {}
    for i, m in enumerate(cab):
        fin = cab[i + 1].start() if i + 1 < len(cab) else len(txt)
        out[m.group(1).lstrip("/")] = {
            f"{a}-{b}" for a, b in
            re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',
                       txt[m.end():fin])}
    return out


def main() -> None:
    n = leer()
    fallos: list[str] = []

    def exige(cond: bool, msg: str) -> None:
        if not cond:
            fallos.append(msg)

    # ---- 1. las DOS masas siguen separadas ------------------------------
    # Es la decision estructural de la placa. Si se tocan, la corriente del
    # backlight del LCD vuelve por la masa analogica y desafina el sinte segun
    # el brillo de la pantalla.
    gnda, gndd = n.get("GNDA", set()), n.get("GNDD", set())
    exige(bool(gnda) and bool(gndd), "falta GNDA o GNDD")
    exige(not (gnda & gndd), f"GNDA y GNDD se tocan: {sorted(gnda & gndd)}")
    # lo digital NO puede aparecer en la masa analogica
    digital = {r for r in gndd if r.split("-")[0] in
               ("J8", "SW1", "SW2", "SW3", "SW4", "Q1", "Q2", "RV1")}
    exige(bool(digital), "GNDD deberia llevar el LCD, los botones y los MOSFET")
    exige(not any(p.split("-")[0].startswith(("J8", "SW", "Q", "RV")) for p in gnda),
          f"algo digital colgado de la masa analogica: {sorted(gnda)}")
    # y lo analogico NO puede aparecer en la digital
    exige("U1-4" in gnda, "la patilla GND del DAC tiene que ir a GNDA, no a GNDD")
    exige(not any(p.startswith(("U1-", "U2-")) for p in gndd),
          f"DAC o amplificador colgados de la masa digital: {sorted(gndd)}")

    # ---- 2. el DAC, patilla a patilla -----------------------------------
    # VLOGIC en +5V en vez de +3V3 sube el umbral VIH a 3.5 V y el Pi da 3.3.
    exige("U1-11" in n.get("+3V3", set()), "VLOGIC (pin 11) tiene que ir a +3V3")
    exige("U1-5" in n.get("+5V", set()), "VDD (pin 5) tiene que ir a +5V")
    exige("U1-11" not in n.get("+5V", set()), "VLOGIC NO puede ir a +5V")
    # GAIN a masa = x1 (0..2.5 V). Arriba serian 0..5 V y con VDD=5 V la salida
    # se comprime en el ultimo tramo justo donde estan las notas agudas.
    exige("U1-10" in gnda, "GAIN (pin 10) a masa para ganancia x1")
    # RSTSEL a masa = arranca a fondo de escala CERO. Arriba arrancaria a media
    # escala y el sinte soltaria una nota sola al encender.
    exige("U1-16" in gnda, "RSTSEL (pin 16) a masa: arranque a escala cero")
    exige("U1-9" in gnda, "LDAC (pin 9) a masa")
    for pin, red in (("U1-12", "SCLK"), ("U1-14", "SDIN"), ("U1-13", "SPI_CE1"),
                     ("U1-15", "DAC_RESET")):
        exige(pin in n.get(red, set()), f"{pin} deberia estar en {red}")

    # ---- 3. los tres canales de CV --------------------------------------
    for i in range(3):
        letra, ch = "ABC"[i], i + 1
        mas, menos, out = {0: ("3", "2", "1"), 1: ("5", "6", "7"),
                           2: ("10", "9", "8")}[i]
        dac_pin = {"A": "U1-3", "B": "U1-2", "C": "U1-6"}[letra]
        exige(dac_pin in n.get(f"DAC_{letra}", set()),
              f"la salida {letra} del DAC no llega a DAC_{letra}")
        exige(f"U2-{mas}" in n.get(f"DAC_{letra}", set()),
              f"DAC_{letra} no entra por la patilla NO inversora")
        # el nodo de realimentacion lleva exactamente las dos R y la entrada
        nodo = [k for k, v in n.items()
                if f"U2-{menos}" in v and f"R{i*2+1}" in " ".join(v)]
        exige(len(nodo) == 1, f"el nodo de realimentacion del canal {ch} esta mal")
        if nodo:
            v = n[nodo[0]]
            exige(len(v) == 3, f"al nodo del canal {ch} le sobra o falta algo: {sorted(v)}")
        exige(f"U2-{out}" in n.get(f"CV{ch}", set()) or
              any(f"U2-{out}" in vv for kk, vv in n.items() if f"R{i+7}" in " ".join(vv)),
              f"la salida del canal {ch} no llega a su resistencia serie")

    # ---- 4. el GATE es NO inversor --------------------------------------
    # Con una sola etapa el reposo seria gate ALTO y al encender dispararian
    # todas las envolventes antes de que arranque el firmware.
    exige("Q1-1" in n.get("GATE_G", set()), "la puerta de Q1 no cuelga de GATE_G")
    exige("Q2-1" in n.get("GATE_INV", set()), "Q2 no lo manda el drenador de Q1")
    exige("Q1-3" in n.get("GATE_INV", set()), "el drenador de Q1 no es GATE_INV")
    exige("Q2-3" in n.get("GATE_12", set()), "el drenador de Q2 no es GATE_12")
    exige("R14-2" in gndd or "R14-1" in gndd,
          "falta la R que fija el gate de Q1 mientras arranca el Pi")

    # ---- 5. ningun riel cruzado -----------------------------------------
    for a, b in (("+12V", "-12V"), ("+12V", "+5V"), ("+5V", "+3V3"),
                 ("+12V", "GNDA"), ("+5V", "GNDD")):
        exige(not (n.get(a, set()) & n.get(b, set())), f"{a} y {b} se tocan")

    for f in fallos:
        print("FALLO:", f)
    if fallos:
        sys.exit(1)
    print(f"OK: {len(n)} redes. Masas separadas, DAC bien atado, "
          f"3 canales de CV completos, gate no inversor.")


if __name__ == "__main__":
    main()
