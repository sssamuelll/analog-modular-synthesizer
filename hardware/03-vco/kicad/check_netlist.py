"""Contrasta sam17-vco.net contra lo que el diseno DICE que debe conectar.

    python check_netlist.py

El ERC saliendo a cero solo dice que no hay conflictos electricos. Una hoja
con VLOGIC de los DAC en +5V, o con el V+ de un SSI2130 colgado de los 12V
del bus en vez de los 5V locales, pasa el ERC con cero avisos y el fallo
aparece meses despues: un DAC frito, o una voz que "a veces desafina" porque
su CV de pitch sale del canal del DAC equivocado.

Aqui se comprueban las cosas que, si estan mal, no se ven hasta que duelen.
"""
from __future__ import annotations

import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(DIR, "sam17-vco.net")


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

    def solo_en(pin: str, prefijo_red: str) -> bool:
        """True si `pin` aparece en el netlist en UNA sola red y esa red
        empieza por `prefijo_red` (usado para el pad termico y MIX AUX2:
        tienen que salir como unconnected-*, nunca soldados a nada)."""
        apariciones = [red for red, nodos in n.items() if pin in nodos]
        return len(apariciones) == 1 and apariciones[0].startswith(prefijo_red)

    # ---- 1. GNDA y GNDD son redes DISTINTAS ------------------------------
    # Es la decision estructural de la placa (igual que el modulo 2): si se
    # tocan, la corriente de retorno del bloque digital (74HC14, I2C, EEPROM)
    # vuelve por la masa analogica y desafina las cuatro voces.
    gnda, gndd = n.get("GNDA", set()), n.get("GNDD", set())
    exige(bool(gnda) and bool(gndd), "falta GNDA o GNDD")
    exige(not (gnda & gndd), f"GNDA y GNDD se tocan: {sorted(gnda & gndd)}")

    # ---- 2. VREF_2V5, la lista cerrada ------------------------------------
    # Una sola referencia (U8, ADR4525) para toda la placa: si algo mas se
    # cuelga de ahi (o algo de esta lista falta), dos DAC ya no comparten el
    # mismo cero y las voces se desafinan entre si aunque cada una calibre
    # bien sola. Ademas de lo que pide el brief, VREF_2V5 lleva legitimamente
    # su propio desacoplo de salida (C11, 1uF: build_schematic.py lo separa
    # a proposito del 100nF generico) y su test point (TP5) -- se incluyen
    # aqui en la lista cerrada en vez de tratarlos como fuga.
    esperado_vref = (
        {"U8-6"}                                    # VOUT de la referencia
        | {f"U{i}-1" for i in (5, 6, 7)}            # VREF de los tres DAC
        | {f"U{i}-23" for i in (1, 2, 3, 4)}        # VREF de los cuatro SSI2130
        | {f"R_SCALE{i}-1" for i in (1, 2, 3, 4)}   # ~94uA de EXPO SCALE
        | {f"R_LIN{i}-1" for i in (1, 2, 3, 4)}     # ~5uA: sin esto el osc SE PARA
        | {"C11-1", "TP5-1"}                        # su propio desacoplo + TP
    )
    vref = n.get("VREF_2V5", set())
    exige(vref == esperado_vref,
          f"VREF_2V5 no es exactamente la lista cerrada: sobra "
          f"{sorted(vref - esperado_vref)}, falta {sorted(esperado_vref - vref)}")

    # ---- 3. la cadena SPI en orden ----------------------------------------
    # MOSI->U5.SDIN->U5.SDO->U6.SDIN->U6.SDO->U7.SDIN->U7.SDO->MISO, y los
    # tres SYNC juntos en SPI_CS3 (un solo CS para los tres DAC: firmware
    # los direcciona por comando, no por chip select individual).
    exige("U5-14" in n.get("SPI_MOSI", set()), "MOSI no llega a U5.SDIN (pin 14)")
    exige({"U5-8", "U6-14"} <= n.get("DAC_LINK_12", set()),
          "U5.SDO (pin 8) no llega a U6.SDIN (pin 14)")
    exige({"U6-8", "U7-14"} <= n.get("DAC_LINK_23", set()),
          "U6.SDO (pin 8) no llega a U7.SDIN (pin 14)")
    exige("U7-8" in n.get("SPI_MISO", set()), "U7.SDO (pin 8) no llega a MISO")
    for u in (5, 6, 7):
        exige(f"U{u}-13" in n.get("SPI_CS3", set()), f"U{u}.SYNC (pin 13) no esta en SPI_CS3")

    # ---- 4. VLOGIC de los tres DAC a +3V3_LOC, NO a +5V_LOC ---------------
    # Igual que el modulo 2: VLOGIC en 5V sube el umbral VIH a 3.5V y el
    # bloque digital de esta placa (74HC14, I2C) trabaja en 3.3V.
    for u in (5, 6, 7):
        exige(f"U{u}-11" in n.get("+3V3_LOC", set()), f"U{u}.VLOGIC (pin 11) tiene que ir a +3V3_LOC")
        exige(f"U{u}-11" not in n.get("+5V_LOC", set()), f"U{u}.VLOGIC NO puede ir a +5V_LOC")

    # ---- 5. V+ de los cuatro SSI2130 a +5V_LOC, NO a +12V -----------------
    # El SSI2130 tiene V+ max absoluto 5.25V: colgarlo de los 12V del bus lo
    # frie el dia que se energiza la placa.
    for u in (1, 2, 3, 4):
        exige(f"U{u}-27" in n.get("+5V_LOC", set()), f"U{u}.V+ (pin 27) tiene que ir a +5V_LOC")
        exige(f"U{u}-27" not in n.get("+12V", set()),
              f"U{u}.V+ NO puede ir a +12V (max absoluto 5.25V del SSI2130)")

    # ---- 6. cada CV_PITCH_n sale del canal correcto de U5 y llega a SU voz-
    # U5 A-D = CV_PITCH_1..4 (VOUTA=3, VOUTB=2, VOUTC=6, VOUTD=7). Si el
    # canal se cruza, la voz 2 afina "casi bien" con el CV de la voz 3: un
    # bug que una sola nota de prueba nunca destapa.
    canal_dac = {1: "3", 2: "2", 3: "6", 4: "7"}
    for v in (1, 2, 3, 4):
        cv = n.get(f"CV_PITCH_{v}", set())
        exige(f"U5-{canal_dac[v]}" in cv, f"CV_PITCH_{v} no sale del canal correcto de U5")
        exige(f"R_PITCH{v}-1" in cv, f"CV_PITCH_{v} no entra por R_PITCH{v}")
        nodo = [k for k, vv in n.items() if f"R_PITCH{v}-2" in vv and f"U{v}-7" in vv]
        exige(len(nodo) == 1,
              f"R_PITCH{v} no llega al nodo EXPO FREQ (pin 7) de SU voz {v}: "
              f"riesgo de que la voz {v} afine con el CV de otra")

    # ---- 7. el TN de cada J_CV a GNDA (normalizado a 0V) -------------------
    for v in (1, 2, 3, 4):
        exige(f"J_CV{v}-TN" in gnda, f"J_CV{v}.TN deberia estar en GNDA (0V sin cable, spec)")

    # ---- 8. cada SQ_n a una entrada de U10, su salida a TUNE_OUT_n --------
    # 74HC14 hex inverter: unidades 1-3 del simbolo van en el orden fisico
    # normal (entrada/salida), pero la unidad 4 del simbolo esta INVERTIDA
    # respecto a su numeracion fisica (entrada=9, salida=8, no 13/12).
    u10_par = {1: ("1", "2"), 2: ("3", "4"), 3: ("5", "6"), 4: ("9", "8")}
    for v in (1, 2, 3, 4):
        entrada, salida = u10_par[v]
        exige(f"U10-{entrada}" in n.get(f"SQ_{v}", set()), f"SQ_{v} no entra a U10 pin {entrada}")
        red_salida = n.get(f"TUNE_OUT_{v}", set())
        exige(f"U10-{salida}" in red_salida, f"U10 pin {salida} no sale a TUNE_OUT_{v}")
        exige(any(p.startswith("J2-") for p in red_salida), f"TUNE_OUT_{v} no llega a J2")

    # ---- 9. TMP1075 y EEPROM en I2C con pullups a +3V3_LOC ----------------
    sda, scl = n.get("I2C_SDA", set()), n.get("I2C_SCL", set())
    exige("U13-1" in sda, "TMP1075 (U13) no esta en I2C_SDA")
    exige("U13-2" in scl, "TMP1075 (U13) no esta en I2C_SCL")
    exige("U14-3" in sda, "EEPROM (U14) no esta en I2C_SDA")
    exige("U14-1" in scl, "EEPROM (U14) no esta en I2C_SCL")
    for nombre, red in (("I2C_SDA", sda), ("I2C_SCL", scl)):
        pullups = sorted(p.split("-")[0] for p in red if p.startswith("R_I2C"))
        exige(len(pullups) == 1, f"deberia haber exactamente un pullup en {nombre}: {pullups}")
        if pullups:
            exige(f"{pullups[0]}-2" in n.get("+3V3_LOC", set()),
                  f"el pullup {pullups[0]} de {nombre} no tira a +3V3_LOC")

    # ---- 10. el pad termico y MIX AUX2 de U1-U4 no van a ningun lado ------
    # Dos rulings del datasheet: el EP (pad 33, pin termico del QFN) y MIX
    # AUX2 (pin 13) se dejan sin soldar. Si algun dia alguien los conecta
    # "por prolijidad" sin leer el datasheet, esto lo destapa.
    for u in (1, 2, 3, 4):
        exige(solo_en(f"U{u}-33", "unconnected-"), f"U{u} pin 33 (EP) deberia salir unconnected-*")
        exige(solo_en(f"U{u}-13", "unconnected-"), f"U{u} pin 13 (MIX AUX2) deberia salir unconnected-*")

    for f in fallos:
        print("FALLO:", f)
    if fallos:
        sys.exit(1)
    print(f"OK: {len(n)} redes. Masas separadas, VREF_2V5 cerrada, cadena SPI "
          f"en orden, alimentaciones locales bien puestas, 4 voces sin cruzar, "
          f"SQ->TUNE_OUT bien pareado, I2C con pullups, EP/MIX_AUX2 al aire.")


if __name__ == "__main__":
    main()
