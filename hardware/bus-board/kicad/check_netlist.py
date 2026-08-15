"""Contrasta sam17-bus.net contra lo que el diseno DICE que debe conectar.

    python check_netlist.py

Por que hace falta si el ERC ya sale a cero: el ERC comprueba que no haya
conflictos, no que la placa sea la que uno queria. Una hoja con los +12 V y
los -12 V intercambiados pasa el ERC con 0 avisos y frie todos los modulos.

Aqui las redes se declaran A MANO, leyendo el diseno, y se comparan pin a pin
con lo que kicad-cli saco del esquematico. Si las dos descripciones coinciden
es porque el generador hizo lo que se le pidio.
"""
from __future__ import annotations

import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(DIR, "sam17-bus.net")
SLOTS = 6


def esperado() -> dict[str, set[str]]:
    """Las redes segun el diseno, sin mirar el netlist.

    El bus Eurorack por pares, desde la FRANJA ROJA hacia arriba:
        1-2 = -12V | 3-4,5-6,7-8 = GND | 9-10 = +12V | 11-16 = NC
    El peine SAM17, igual que J2 del modulo 1:
        1 = +12V | 2,3 = GND | 4 = -12V
    """
    redes: dict[str, set[str]] = {"GND": set(), "+12V": set(), "-12V": set()}
    redes["+12V"] |= {"J7-1"}
    redes["GND"] |= {"J7-2", "J7-3"}
    redes["-12V"] |= {"J7-4"}

    for k in range(SLOTS):
        j, p = f"J{k+1}", f"P{k+1}"
        f_pos, f_neg = f"F{2*k+1}", f"F{2*k+2}"
        d_pos, d_neg = f"D{2*k+1}", f"D{2*k+2}"
        r_pos, r_neg = f"R{2*k+1}", f"R{2*k+2}"

        # lado RIEL: el PTC por un extremo y el anodo/catodo del LED
        redes["+12V"] |= {f"{f_pos}-1", f"{d_pos}-2"}      # anodo al riel
        redes["-12V"] |= {f"{f_neg}-2", f"{r_neg}-2"}      # catodo (via R) al riel

        # lado MODULO: el otro extremo del PTC, la R (o el LED) y los peines
        redes[f"+12S{k+1}"] = {f"{f_pos}-2", f"{r_pos}-2",
                               f"{j}-9", f"{j}-10", f"{p}-1"}
        redes[f"-12S{k+1}"] = {f"{f_neg}-1", f"{d_neg}-2",
                               f"{j}-1", f"{j}-2", f"{p}-4"}

        redes["GND"] |= {f"{j}-{n}" for n in (3, 4, 5, 6, 7, 8)}
        redes["GND"] |= {f"{p}-2", f"{p}-3"}

        # el nudo interno de cada indicador: catodo del LED con su 4k7. KiCad
        # lo bautiza Net-(Dn-K) porque no lleva etiqueta, y no la necesita.
        redes[f"Net-({d_pos}-K)"] = {f"{d_pos}-1", f"{r_pos}-1"}
        redes[f"Net-({d_neg}-K)"] = {f"{d_neg}-1", f"{r_neg}-1"}
    return redes


def leer() -> dict[str, set[str]]:
    """El cuerpo de cada red va desde su cabecera hasta la cabecera SIGUIENTE.

    Antes se buscaba el literal '(net (code' con find() para cortar, y kicad-cli
    no escribe esos espacios asi: no encontraba nada, cortaba al final del
    fichero y METIA TODOS LOS PINES EN TODAS LAS REDES. Parecia que la placa
    estuviera entera en cortocircuito. Ahora el corte lo da el propio finditer.
    """
    with open(NET, encoding="utf-8") as fh:
        txt = fh.read()
    cabeceras = list(re.finditer(
        r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)', txt))
    assert cabeceras, "no se reconocio ninguna red: cambio el formato del netlist"
    redes: dict[str, set[str]] = {}
    for i, m in enumerate(cabeceras):
        fin = cabeceras[i + 1].start() if i + 1 < len(cabeceras) else len(txt)
        redes[m.group(1).lstrip("/")] = {
            f"{a}-{b}" for a, b in
            re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',
                       txt[m.end():fin])}
    return redes


def main() -> None:
    esp, real = esperado(), leer()
    fallos = []
    for nombre, pines in sorted(esp.items()):
        tiene = real.get(nombre)
        if tiene is None:
            fallos.append(f"falta la red {nombre}")
        elif tiene != pines:
            fallos.append(f"{nombre}: sobran {sorted(tiene - pines)}, "
                          f"faltan {sorted(pines - tiene)}")
    # ninguna red inventada aparte de las declaradas y las de un solo pin
    # (los no-connect no salen en el netlist, asi que no deberia haber ninguna)
    extra = [n for n in real if n not in esp and len(real[n]) > 1]
    if extra:
        fallos.append(f"redes que el diseno no declara: {extra}")

    for f in fallos:
        print("FALLO:", f)
    if fallos:
        sys.exit(1)
    total = sum(len(v) for v in esp.values())
    print(f"OK: {len(esp)} redes, {total} pines, cuadran una a una con el diseno")

    # el error que de verdad mata: +12 y -12 intercambiados en el peine
    assert "J1-1" in esp["-12S1"], "el par 1 (franja roja) tiene que ser -12 V"
    assert "J1-9" in esp["+12S1"], "el par 5 tiene que ser +12 V"
    print("OK: par 1 = franja roja = -12 V, par 5 = +12 V")


if __name__ == "__main__":
    main()
