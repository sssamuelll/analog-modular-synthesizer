"""Puerta: la red entra por una pieza que existe, y el chasis tiene su hueco.

    python check_red_chasis.py

## El fallo que esto persigue

El fusible de red de esta fuente ya no esta en la PCB. Estaba, y ademas del
del recinto: dos fusibles en serie en el mismo primario, sin nadie que dijera
cual protege que. Se quito el de la placa, y con eso el instrumento se quedo
**sin ningun fusible declarado en ningun sitio** -- porque el del recinto era
una frase en el #107 ("la entrada IEC C14 con fusible e interruptor"), no una
pieza.

Una frase no se compra, no tiene recorte y no tiene hoja. Y el recorte de una
entrada de red es distinto en cada referencia: sin pieza elegida, el hueco de
la chapa es un numero inventado, y una chapa cortada mal no se arregla.

## Lo que comprueba

1. `bom-chasis.csv` existe y trae las tres piezas: modulo, cajon y fusible
2. el fusible es el que pide sec.14.2 -- 1.6 A lento -- y hay DOS, porque el
   portafusibles es bipolar
3. `F1` NO ha vuelto al BOM de la placa: un solo fusible, y esta en el chasis
4. el espesor de chapa del chasis cae dentro del rango snap-in del modulo
5. el recorte del modulo cabe en la altura interior de la pared del chasis
6. el recorte esta parametrizado en `case/cad/params.scad`

La 6 es la que hoy sale en HUECO, y sale con las cotas puestas: el chasis lo
esta dibujando otra rama, y meterle la mano a `params.scad` desde aqui seria
pisar trabajo en curso. Lo que se puede hacer sin pisar nada es dejar el
numero medido y que la puerta lo reclame hasta que este.
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BOM_CHASIS = os.path.join(DIR, "bom-chasis.csv")
BOM_PLACA = os.path.join(DIR, "bom.csv")
PARAMS = os.path.join(DIR, "..", "..", "..", "case", "cad", "params.scad")

# --- el modulo de entrada, hoja Schurter `typ_KM.pdf` (Power Entry Modules
# without Line Filter, PG05), variante KM00.1105.11 = clase I, portafusibles
# 2 polos, interruptor 2 polos, sin blindaje EMC.
#   p.1 Technical Data: "Panel Thickness S / Snap-in: 1/1.5/2/2.5 mm
#                        (all steps with one variant)"
#   p.3 Dimensions, "KM without shield":
#        recorte  28 (+0.10/-0.05)  x  47 (+0.10/-0.05),  esquinas max R 0.3
#        brida    30.5 x 50, sobresale 2.5 del panel
#        detras   26.15 mm de cuerpo + 3.2 mm de clips
MODULO = "KM00.1105.11"
CHAPAS_SNAP_IN = (1.0, 1.5, 2.0, 2.5)
RECORTE_X, RECORTE_Y = 28.0, 47.0
RECORTE_R_MAX = 0.3
FONDO_DETRAS = 26.15 + 3.2
# Margen de chapa alrededor del recorte. No es del datasheet: es taller. Menos
# de 5 mm de acero entre un recorte y el doblez se deforma al plegar.
MARGEN_CHAPA = 5.0

# --- el fusible, sec.14.2 del design-notes: 1.6 A lento. La v1 llevaba 250 mA
# y el inrush del toroide de 120 VA lo fundia.
FUSIBLE_A = 1.6
FUSIBLE_CURVA = "T"
FUSIBLE_N = 2          # el portafusibles es bipolar


def lee_scad(clave):
    if not os.path.exists(PARAMS):
        return None
    texto = open(PARAMS, encoding="utf-8").read()
    m = re.search(r"^\s*" + clave + r"\s*=\s*([\d.]+)\s*;", texto, re.M)
    return float(m.group(1)) if m else None


def main() -> int:
    fallos: list[str] = []
    huecos: list[str] = []

    # --- 1. las tres piezas -------------------------------------------------
    if not os.path.exists(BOM_CHASIS):
        print("FALLO: no existe " + os.path.basename(BOM_CHASIS))
        return 1
    filas = list(csv.DictReader(open(BOM_CHASIS, newline="", encoding="utf-8")))
    por_ref = {f["refs"]: f for f in filas}
    print(f"{len(filas)} piezas de red fuera de la placa:")
    for f in filas:
        print("  {:8} {} {}  x{}".format(
            f["refs"], f["fabricante"], f["referencia"], f["quantity"]))
    print()

    if "X1" not in por_ref:
        fallos.append("no hay entrada de red (X1) en bom-chasis.csv")
    elif por_ref["X1"]["referencia"] != MODULO:
        fallos.append("X1 es {} y las cotas de recorte de esta puerta son "
                      "las del {}".format(por_ref["X1"]["referencia"], MODULO))
    if "X1A" not in por_ref:
        fallos.append("falta el cajon portafusibles (X1A): la hoja del KM lo "
                      "lista como 'Required Accessory' y NO viene incluido, "
                      "asi que sin el no hay donde meter el fusible")

    # --- 2. el fusible es el que pide sec.14.2 ------------------------------
    fus = por_ref.get("F1;F2")
    if not fus:
        fallos.append("no hay fusible (F1;F2) en bom-chasis.csv: el "
                      "instrumento se quedaria sin ninguno, porque F1 salio "
                      "de la placa")
    else:
        v = fus["value"]
        if str(FUSIBLE_A) not in v:
            fallos.append("el fusible dice '{}' y sec.14.2 pide {} A".format(
                v, FUSIBLE_A))
        if not re.search(r"\b" + FUSIBLE_CURVA + r"\b", v):
            fallos.append("el fusible dice '{}' y sec.14.2 pide curva {} "
                          "(lento): el inrush del toroide de 120 VA funde uno "
                          "rapido".format(v, FUSIBLE_CURVA))
        if int(fus["quantity"]) != FUSIBLE_N:
            fallos.append("hay {} fusible(s) y el portafusibles del {} es "
                          "bipolar: hacen falta {}".format(
                              fus["quantity"], MODULO, FUSIBLE_N))
        print("  fusible: {}  x{}  -> OK".format(v, fus["quantity"]))

    # --- 3. F1 no ha vuelto a la placa --------------------------------------
    # Es la comprobacion que impide deshacer sin querer la decision de esta
    # tanda. Dos fusibles en serie no es "el doble de protegido": es que el
    # primero que funda decide, y no esta escrito cual es.
    refs_placa = {f["refs"] for f in
                  csv.DictReader(open(BOM_PLACA, newline="", encoding="utf-8"))}
    if "F1" in refs_placa:
        fallos.append("F1 ha vuelto al BOM de la placa. Con el del chasis son "
                      "DOS fusibles en serie en el mismo primario, y ninguno "
                      "de los dos documentos dice cual protege que")
    else:
        print("  F1 no esta en el BOM de la placa -> un solo fusible, OK")

    # --- 4. la chapa del chasis y el snap-in --------------------------------
    t = lee_scad("t_chapa")
    if t is None:
        huecos.append("no se pudo leer t_chapa de case/cad/params.scad")
    else:
        marca = "OK" if t in CHAPAS_SNAP_IN else "NO"
        print("  chapa del chasis {} mm  vs snap-in del modulo {}  -> {}"
              .format(t, CHAPAS_SNAP_IN, marca))
        if t not in CHAPAS_SNAP_IN:
            fallos.append(
                "el chasis es de {} mm de chapa y el {} solo entra a presion "
                "en {} mm. O cambia la chapa, o hay que ir a la version de "
                "tornillo (DD11)".format(t, MODULO, CHAPAS_SNAP_IN))

    # --- 5. el recorte cabe en la pared -------------------------------------
    z = lee_scad("chasis_int_z")
    if z is None:
        huecos.append("no se pudo leer chasis_int_z de case/cad/params.scad")
    else:
        libre = z - RECORTE_Y - 2 * MARGEN_CHAPA
        print("  pared interior {} mm de alto, recorte {} + 2x{} de margen  "
              "-> {:+.1f} mm".format(z, RECORTE_Y, MARGEN_CHAPA, libre))
        if libre < 0:
            fallos.append(
                "el recorte de {} mm no cabe en una pared de {} mm dejando {} "
                "mm de chapa a cada lado: faltan {:.1f} mm".format(
                    RECORTE_Y, z, MARGEN_CHAPA, -libre))

    # --- 6. el recorte, en el case ------------------------------------------
    ancho = lee_scad("chasis_iec_ancho")
    alto = lee_scad("chasis_iec_alto")
    if ancho is None or alto is None:
        huecos.append(
            "el recorte del {} no esta en case/cad/params.scad. Hacen falta "
            "chasis_iec_ancho = {} y chasis_iec_alto = {} (esquinas R {} max, "
            "hoja typ_KM.pdf p.3), con {:.2f} mm libres detras de la pared"
            .format(MODULO, RECORTE_X, RECORTE_Y, RECORTE_R_MAX, FONDO_DETRAS))
    else:
        print("  recorte en el case: {} x {} mm".format(ancho, alto))
        if abs(ancho - RECORTE_X) > 0.1 or abs(alto - RECORTE_Y) > 0.1:
            fallos.append(
                "el case recorta {} x {} y la hoja del {} pide {} x {}".format(
                    ancho, alto, MODULO, RECORTE_X, RECORTE_Y))

    if fallos:
        print("\nFALLO: {}".format(len(fallos)))
        for f in fallos:
            print("  - " + f)
        return 1
    if huecos:
        print("\nHUECO: {}".format(len(huecos)))
        for h in huecos:
            print("  - " + h)
        return 2
    print("\nOK: la red entra por una pieza con hoja, con un solo fusible, y "
          "el chasis\n    tiene su recorte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
