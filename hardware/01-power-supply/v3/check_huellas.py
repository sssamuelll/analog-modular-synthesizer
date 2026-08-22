"""Puerta: las huellas hechas a mano dicen la verdad sobre la pieza que llevan.

    python check_huellas.py

## El fallo que esto persigue

Una huella equivocada es el fallo que no perdona: pasa el ERC, pasa el DRC,
pasa la netlist, se fabrica, se monta, y aparece cuando la pieza no entra o
entra girada. Ninguna puerta de las que hay lo ve, porque todas comprueban
CONECTIVIDAD y esto es geometria.

Esta placa monta huellas propias, en `../kicad/sam17.pretty`, y existen porque
KiCad 10 no las trae (design-notes sec.14.3). Una huella de libreria la ha
revisado mucha gente; una propia, solo quien la dibujo. La libreria es UNA para
las tres versiones, asi que la puerta lee los tres BOM: quien monta cada huella
es un dato, no una suposicion.

## Lo que comprueba, y lo que NO puede comprobar

Comprueba la **coherencia interna**: que el paso que anuncia el nombre sea el
paso real de los pads, que el cuerpo que anuncia quepa en su courtyard, y que
el BOM y la huella hablen de la misma pieza.

Lo que NO puede comprobar es lo unico que cierra el asunto de verdad: que esas
cotas sean las de la pieza REAL, que eso solo sale del datasheet del
fabricante. Eso queda como hueco declarado abajo, con nombre y apellido.

Un nombre de huella es un contrato: `P10.0mm` promete 10 mm entre pads, y si
la geometria dice otra cosa, quien elija la pieza por el nombre se equivoca.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.join(DIR, "..", "kicad", "sam17.pretty")
BOM = os.path.join(DIR, "bom.csv")
# sam17.pretty es UNA libreria para las tres versiones, asi que "esta huella no
# la usa nadie" solo es verdad si no la usa NINGUN BOM. Mirando solo el de la v3
# la puerta daba rojo sobre la huella vieja del NTC el dia que la v3 dejo de
# usarla -- y esa huella sigue siendo la que monta la v2, que esta congelada.
BOMS = [("v3", BOM),
        ("v2", os.path.join(DIR, "..", "v2", "bom.csv")),
        ("v1", os.path.join(DIR, "..", "bom.csv"))]

# Cotas CONFIRMADAS contra la hoja del fabricante. La clave es el designador y
# el valor es (paso de patas, diametro de cuerpo, de donde sale). None = no se
# ha podido confirmar, y eso NO se disimula: se lista abajo con su motivo.
#
# El repo ya tiene grabada la leccion de fiarse de un distribuidor: los 45 mm
# de alto del toroide, "corregidos" a 52,1 con dos listados coincidentes, y la
# hoja del fabricante dijo 46. Por eso aqui solo entra lo que sale de la hoja.
CONFIRMADO = {
    # Ametherm SL10 5R002, hoja del fabricante (ametherm.com, rev. 2012-03-29):
    # D 10.0 max, T 4.0 max, S 5.1 nom, pata 0.5 nom, 5.0 ohm +-20%, 2.00 A.
    "NT1": (5.1, 10.0, ("pata", 0.50), "hoja Ametherm SL10 5R002"),
    # EPCOS/TDK SIOV StandarD B722*, marzo 2018, p.17 (VRMS = 275 V), fila
    # B72220S0271K101 = SIOV-S20K275:
    #     e 10.0 +-1   a 2.0 tip   wmax 21.5   thmax 5.4   hmax 25.5
    #     lmin 25.0    d 1.0 +-0.05
    # Y confirma la leccion del toroide otra vez: DOS distribuidores decian
    # 22.5 mm de ancho y la hoja dice 21.5. Un milimetro, en el numero que
    # decidio bajar la barrera de red.
    "RV1": (10.0, 21.5, ("pata", 1.00), "hoja EPCOS/TDK SIOV StandarD p.17"),
    # Vogt AG, "Steckzungen fuer gedruckte Schaltungen", DIN 46342 parte 1,
    # fila 3866A: A 5 (paso entre las dos patas), B1 8 (ancho de la base),
    # S 0.8 (espesor de lengueta), y "Print Bohrung / Trou / Hole" = 1.3.
    # Ese ultimo es el caso comodo: el fabricante da EL AGUJERO, asi que no
    # hay que derivarlo de la pata ni aplicarle IPC-2222 -- y por eso el
    # tercer campo dice de que cota se trata en vez de asumir que es la pata.
    "J5": (5.0, 8.0, ("taladro", 1.30), "hoja Vogt AG, Steckzungen DIN 46342 p.1"),
}

# Holgura minima entre el taladro y la pata que va dentro. IPC-2222 pide para
# un agujero metalizado 0.25 mm nominal sobre el diametro de la pata, y no
# baja de 0.15 en ningun caso. Por debajo de eso la pieza entra a presion o no
# entra: la tolerancia de taladrado de JLC es +-0.08 mm, asi que un agujero
# nominal de 1.1 puede salir de 1.02.
HOLGURA_MIN = 0.15

# Lo que falta por confirmar contra la hoja del fabricante, con QUE habria que
# medir. No se disimula: se lista, se cuenta y se imprime (Principio V).
SIN_CONFIRMAR = [
    ("J5", "Vogt 3866A.68",
     "el FONDO de la pieza (eje Y en planta). La tabla de Vogt da A, B1, S, "
     "L, L1, T, D y B, pero solo A, B1 y S se pueden leer sin el dibujo "
     "acotado; el courtyard reserva 8.0 mm en Y y eso no esta contrastado",
     "es el UNICO puente chasis-masa de todo el instrumento (sec.13). El "
     "paso, el ancho de base y el taladro SI estan confirmados"),
]


def lee_huella(ruta: str) -> dict:
    s = open(ruta, encoding="utf-8").read()
    pads = [(n, float(x), float(y)) for n, x, y in re.findall(
        r'\(pad "([^"]*)"\s+\w+\s+\w+\s*\(at ([-\d.]+) ([-\d.]+)', s)]
    drills = [float(d) for d in re.findall(r"\(drill ([\d.]+)\)", s)]
    crt = re.findall(
        r'\(fp_(?:line|rect)\s*\(start ([-\d.]+) ([-\d.]+)\)\s*'
        r'\(end ([-\d.]+) ([-\d.]+)\).*?"F\.CrtYd"', s, re.S)
    xs = [float(v) for t in crt for v in (t[0], t[2])]
    ys = [float(v) for t in crt for v in (t[1], t[3])]
    return {"pads": pads, "drills": drills,
            "crt": (max(xs) - min(xs), max(ys) - min(ys)) if xs else None}


def main() -> int:
    fallos: list[str] = []
    usadas: dict[str, dict[str, list[str]]] = {}
    for ver, ruta in BOMS:
        if not os.path.exists(ruta):
            continue
        with open(ruta, newline="", encoding="utf-8") as fh:
            for fila in csv.DictReader(fh):
                hu = fila.get("footprint", "")
                if hu.startswith("sam17:"):
                    nom_hu = hu.split(":", 1)[1]
                    usadas.setdefault(nom_hu, {}).setdefault(
                        ver, []).append(fila["refs"])

    ficheros = sorted(f for f in os.listdir(PRETTY) if f.endswith(".kicad_mod"))
    print(f"{len(ficheros)} huellas propias en sam17.pretty\n")

    for fn in ficheros:
        nom = fn[:-len(".kicad_mod")]
        h = lee_huella(os.path.join(PRETTY, fn))
        por_ver = usadas.get(nom, {})
        # Contra la pieza real solo se mide lo que monta la v3: es la unica que
        # se va a fabricar. Una huella que solo usan v1/v2 se queda en la
        # coherencia interna, y se dice que es legado en vez de callarlo.
        quien = ", ".join(por_ver.get("v3", [])) or "NADIE"
        legado = ", ".join(f"{v}: {', '.join(r)}"
                           for v, r in por_ver.items() if v != "v3")
        print(f"  {nom}")
        print(f"    la usa: {quien}" + (f"   (legado -- {legado})"
                                        if legado else ""))

        # 1) el paso que promete el nombre contra el paso real
        mp = re.search(r"_P([\d.]+)mm", nom)
        if mp and len(h["pads"]) >= 2:
            declarado = float(mp.group(1))
            xs = sorted(p[1] for p in h["pads"])
            real = max(xs) - min(xs)
            marca = "OK" if abs(real - declarado) < 0.01 else "NO CUADRA"
            print(f"    paso: nombre dice {declarado} mm, los pads dan "
                  f"{real:.2f} mm  -> {marca}")
            if marca != "OK":
                fallos.append(f"{nom}: el nombre promete {declarado} mm de paso "
                              f"y los pads estan a {real:.2f}. Quien elija la "
                              f"pieza por el nombre se equivoca")

        # 2) el cuerpo que anuncia el nombre tiene que caber en el courtyard
        md = re.search(r"_D([\d.]+)mm", nom)
        if md and h["crt"]:
            cuerpo, (cx, cy) = float(md.group(1)), h["crt"]
            holgura = min(cx, cy) - cuerpo
            print(f"    cuerpo: nombre dice D{cuerpo} mm, courtyard "
                  f"{cx:.2f} x {cy:.2f} -> {holgura:+.2f} mm de holgura")
            if holgura < 0:
                fallos.append(f"{nom}: el courtyard ({min(cx,cy):.2f} mm) es "
                              f"MENOR que el cuerpo que anuncia el nombre "
                              f"(D{cuerpo}): la pieza no cabe en su propia caja")

        # 3) EL PASO DE LA PIEZA REAL, cuando hay hoja. Es la unica de las
        #    comprobaciones que puede decir que la pieza NO ENTRA -- las de
        #    arriba solo miran que la huella sea coherente consigo misma, y
        #    una huella puede ser perfectamente coherente y no casar con nada.
        for ref in quien.split(", "):
            if ref not in CONFIRMADO:
                continue
            paso_real, ancho_real, (cota, valor), fuente = CONFIRMADO[ref]
            xs = sorted(p[1] for p in h["pads"])
            paso_huella = max(xs) - min(xs)
            taladro = min(h["drills"]) if h["drills"] else 0.0
            # El courtyard se mide EN EL EJE DE LOS PADS, no por su lado
            # menor. Un faston es ancho en x y estrecho en y: comparar su
            # base de 8 mm contra el lado corto medía dos cosas distintas y
            # daba verde por accidente.
            crt_x = h["crt"][0] if h["crt"] else 0.0
            print(f"    contra la pieza ({fuente}):")
            print(f"      paso     pieza {paso_real} mm  vs huella "
                  f"{paso_huella:.2f} mm")
            print(f"      ancho    pieza {ancho_real} mm  vs courtyard en x "
                  f"{crt_x:.2f} mm")
            if abs(paso_huella - paso_real) > 0.5:
                fallos.append(
                    f"{nom}: {ref} tiene las patas a {paso_real} mm "
                    f"({fuente}) y la huella las pone a {paso_huella:.2f}. "
                    f"Hay que doblarlas {abs(paso_huella-paso_real)/2:.2f} mm "
                    f"por lado para que entre")
            if h["crt"] and crt_x < ancho_real:
                fallos.append(f"{nom}: {ref} mide {ancho_real} mm de ancho "
                              f"({fuente}) y su courtyard en x {crt_x:.2f}")

            if cota == "pata":
                holgura = taladro - valor
                print(f"      taladro  pata {valor} mm  vs agujero {taladro} "
                      f"mm  -> {holgura:+.2f} mm de holgura")
                if holgura < HOLGURA_MIN:
                    fallos.append(
                        f"{nom}: la pata de {ref} mide {valor} mm ({fuente}) "
                        f"y el agujero {taladro}: {holgura:.2f} mm de "
                        f"holgura, por debajo de los {HOLGURA_MIN} que pide "
                        f"IPC-2222. Con la tolerancia de taladrado de JLC "
                        f"(+-0.08) el agujero puede salir de "
                        f"{taladro-0.08:.2f} y la pata no entra")
            else:   # "taladro": el fabricante da el agujero, punto
                print(f"      taladro  la hoja manda {valor} mm  vs huella "
                      f"{taladro} mm")
                if abs(taladro - valor) > 0.01:
                    fallos.append(
                        f"{nom}: la hoja de {ref} especifica un taladro de "
                        f"{valor} mm ({fuente}) y la huella taladra "
                        f"{taladro}. Cuando el fabricante da el agujero no "
                        f"hay nada que derivar: se pone el suyo")

        # 4) una huella propia que no usa nadie es una huella que sobra, y una
        #    que usa alguien sin estar aqui la habria cazado ya check_bom.py
        if quien == "NADIE" and not legado:
            fallos.append(f"{nom}: no la usa ningun componente de ningun BOM")
        print(f"    taladros: {sorted(set(h['drills']))}")
        print()

    print(f"lo NO confirmado contra la hoja del fabricante: "
          f"{len(SIN_CONFIRMAR)}")
    for ref, pieza, que, porque in SIN_CONFIRMAR:
        print(f"  - {ref} ({pieza}): falta {que}")
        print(f"    importa porque {porque}")

    if fallos:
        print(f"\nFALLO: {len(fallos)}")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\nOK: las {n} huellas propias son coherentes con su nombre y las "
          "usa\n    alguien. Lo que sigue sin confirmar contra la hoja esta "
          "listado arriba.".format(n=len(ficheros)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
