"""Cierra el lazo del bring-up de la fuente: lo MEDIDO contra lo PREDICHO.

    python check_bringup.py               comprueba notes/medidas.csv
    python check_bringup.py --plantilla   escribe la hoja de campo vacia

`notes/bring-up.md` predice un numero en cada punto de la placa, y lo hace
antes de que la placa exista -- que es exactamente un test escrito antes de la
implementacion. Lo que faltaba era la otra mitad: que cuando el numero se mida,
algo lo compare. Sin eso el bring-up es un PDF que alguien lee una vez y las
medidas se quedan en un cuaderno.

Mismo patron que `hardware/03-vco/check_bringup.py`, que ya lo hacia bien: la
prediccion vive en codigo con su fuente en la misma linea, y la medida vive en
un CSV que se rellena en el banco y se commitea.

## Los codigos de salida, y por que 2

    0   todos los puntos con criterio medidos y dentro de rango
    1   alguna medida FUERA de rango -- la placa no pasa
    2   faltan medidas. Ni bien ni mal: no se sabe todavia

Con la placa aun sin fabricar lo correcto es 2, no 0. Un fichero de medidas
vacio que saliera en verde seria la version de banco de la hoja de 711 bytes
que paso el ERC con cero errores (constitucion, Principio III).

## Dos clases de punto

  * **criterio**: `bring-up.md` da un rango y suspender significa algo.
  * **registro**: no hay rango que valga porque el numero AUN no existe -- la
    temperatura del aire del recinto, la de la pared junto a los tabs. Se
    anotan porque solo significan algo comparados con la placa siguiente.

Un registro nunca pone nada en rojo, pero se cuenta y se lista.

## El punto 0.1 no es un criterio mas

El aislamiento de los tres tabs es lo unico de esta lista que decide si la
placa se enchufa o no. Dos de los tres estan a VRAW+ y VRAW-, y la pared
contra la que atornillan es acero a PE: una mica que falle pone el recinto a
+-20 V. Por eso va primero y por eso su umbral es de megaohmios y no de
porcentajes.
"""
from __future__ import annotations

import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(DIR, "notes", "medidas.csv")
COLS = ["paso", "magnitud", "unidad", "medido", "placa", "fecha", "nota"]

# Umbral de aborto del valle, v2 §4.1: 12.000 (V_OUT) + 0.450 (dropout MAX del
# LT3045 en el bin de 500 mA) + 0.007 (ballast) + 1.000 (dropout MAX del
# pre-regulador). Lo fija el riel positivo; los dos comparten front-end.
VALLE_MIN = 13.46
TOL_TELE = 0.01          # +-1 %: divisores al 0.1 % mas el error del ADS1115


class Punto:
    """Un numero que bring-up.md predice, con de donde sale."""

    def __init__(self, paso, magnitud, unidad, fuente,
                 lo=None, hi=None, literal=None):
        self.paso, self.magnitud, self.unidad = paso, magnitud, unidad
        self.fuente, self.lo, self.hi, self.literal = fuente, lo, hi, literal

    @property
    def clave(self):
        return f"{self.paso}|{self.magnitud}"

    @property
    def es_criterio(self):
        return not (self.lo is None and self.hi is None and self.literal is None)

    def rango(self):
        if self.literal is not None:
            return f"= {self.literal}"
        if self.lo is not None and self.hi is not None:
            return f"{self.lo:g} .. {self.hi:g}"
        if self.hi is not None:
            return f"<= {self.hi:g}"
        if self.lo is not None:
            return f">= {self.lo:g}"
        return "registro"

    def juzga(self, bruto):
        """None si pasa; si no, por que falla."""
        if self.literal is not None:
            return (None if bruto.strip().lower() == self.literal.lower()
                    else f"'{bruto}' != '{self.literal}'")
        try:
            v = float(bruto.replace(",", "."))
        except ValueError:
            return f"'{bruto}' no es un numero"
        if self.lo is not None and v < self.lo:
            return f"{v:g} {self.unidad} por debajo de {self.lo:g}"
        if self.hi is not None and v > self.hi:
            return f"{v:g} {self.unidad} por encima de {self.hi:g}"
        return None


def _puntos():
    P, p = Punto, []

    # --- Paso 0: con el equipo DESENCHUFADO -------------------------------
    for ref, red in (("U1", "VRAW+"), ("U2", "VRAW-"), ("U3", "+5V in")):
        p.append(P("0", f"aislamiento_tab_{ref}_a_chasis", "Mohm",
                   f"par.0.1: el tab de {ref} esta a {red} y la pared es "
                   f"acero a PE. ESTA medida autoriza a enchufar", lo=10.0))
    p += [P("0", "continuidad_tierra_clavija_a_J5", "mohm",
            "par.0.2: mili u decenas de miliohmios (design-notes §13.4)",
            hi=100.0),
          P("0", "BR1_esquina_mas_contra_cruz_del_silk", "si/no",
            "par.0.3: girado 180 cabe igual y cruza el puente", literal="si"),
          P("0", "fusible_IEC_es_1A6_lento_cerrado", "si/no",
            "par.0.4: el fusible ya no esta en la placa (#130). Si no lo es, "
            "no se enchufa: la placa no tiene red detras", literal="si"),
          P("0", "referencia_del_IEC_montado", "texto",
            "par.0.4: registro, para el BOM del chasis")]

    # --- Paso 1: solo el transformador ------------------------------------
    p += [P("1", "secundario_A_a_toma_central", "V", "par.1: +-17 V",
            lo=15.5, hi=18.5),
          P("1", "secundario_B_a_toma_central", "V", "par.1: +-17 V",
            lo=15.5, hi=18.5)]

    # --- Paso 2: placa sin carga ------------------------------------------
    for tp, senal, nom, tol in (("TP7", "+13V1", 13.1, 0.3),
                                ("TP8", "-12V9", -12.9, 0.3),
                                ("TP3", "+12V", 12.00, 0.05),
                                ("TP4", "-12V", -12.00, 0.05),
                                ("TP5", "+5V", 5.00, 0.25)):
        p.append(P("2", f"{tp}_{senal}_sin_carga", "V",
                   f"par.2: {nom} +-{tol}", lo=nom - tol, hi=nom + tol))

    # --- Paso 3: el rotulo de J2 (#121) -----------------------------------
    # El pin 1 es -12 V y el 4 es +12 V. El rotulo dijo lo contrario durante
    # dos versiones: quien montara el mazo leyendo esa columna metia +-12 V
    # al reves en los SEIS modulos.
    for pin, nom in ((1, -12.0), (2, 0.0), (3, 0.0), (4, 12.0)):
        p.append(P("3", f"J2_pin{pin}", "V",
                   f"par.3: {nom:+g} V medido, no leido del rotulo",
                   lo=nom - 0.5, hi=nom + 0.5))

    # --- Paso 4: LA puerta que decide la placa ----------------------------
    for riel in ("VRAW+", "VRAW-"):
        for cond in ("frio", "30min_caliente"):
            p.append(P("4", f"valle_{riel}_{cond}", "V",
                       f"par.4: umbral de aborto {VALLE_MIN} V (v2 §4.1). "
                       f"Por debajo no hay setpoint que funcione",
                       lo=VALLE_MIN))
    p += [P("4", "tension_de_red_del_momento", "V", "par.4: registro"),
          P("4", "I_dummy_positivo", "A", "par.4: ~0.6 A", lo=0.5, hi=0.75),
          P("4", "I_dummy_negativo", "A", "par.4: ~0.6 A", lo=0.5, hi=0.75)]

    # --- Paso 5: rizado ----------------------------------------------------
    for riel in ("+12V", "-12V"):
        p.append(P("5", f"rizado_pp_{riel}", "mV",
                   "par.5: bajo el suelo del osciloscopio a 20 MHz BW. El "
                   "criterio PLENO necesita el LNA (#58): esto es registro"))

    # --- Paso 6: la telemetria se estrena ---------------------------------
    for ref, chip, dire in (("U8", "INA226", "0x40"), ("U9", "INA226", "0x41"),
                            ("U10", "ADS1115", "0x49"), ("U11", "TMP1075", "0x48")):
        p.append(P("6", f"I2C_responde_{dire}_{ref}_{chip}", "si/no",
                   "par.6.1: direccion fijada por straps", literal="si"))
    p += [P("6", "I2C_direcciones_inesperadas", "cuantas",
            "par.6.1: 0x50 esta reservada a la EEPROM de OTRAS placas; "
            "si aparece aqui hay algo mal atado", lo=0, hi=0),
          P("6", "aislamiento_GNDA_a_GNDD", "Mohm",
            "par.6.2: la barrera del ISO1541, comprobada en COBRE y no en "
            "el dibujo", lo=1.0)]
    # 6.3 -- el error RELATIVO de cada canal contra el multimetro. Es donde se
    # caza un divisor mal POBLADO: 100k y 20k son dos 0805 identicas, y eso no
    # lo ve check_netlist.py ni ninguna puerta anterior a esta medida.
    for canal in ("U8_V_+12V", "U8_I_+12V", "U9_V_+5V", "U10_V_-12V",
                  "U10_V_VRAW+", "U10_V_VRAW-"):
        p.append(P("6", f"error_relativo_{canal}", "%",
                   f"par.6.3: +-{TOL_TELE*100:g} % contra el multimetro. Fuera "
                   f"de escala -> mirar R21-R26 contra las dos lineas de seda",
                   lo=-TOL_TELE * 100, hi=TOL_TELE * 100))

    # --- Paso 7: termica CON EL CHASIS CERRADO ----------------------------
    for ref in ("U1", "U2", "U3"):
        p.append(P("7", f"T_case_{ref}", "C",
                   "par.7: < 70 C (§10.4.1 del datasheet del LM2941). El "
                   "disipador es la PARED, y la caja esta cerrada", hi=70.0))
    for ref in ("U4", "U5", "U6", "U7"):
        p.append(P("7", f"T_case_{ref}", "C",
                   "par.7: < 90 C, ceramicos de precision", hi=90.0))
    p += [P("7", "T_ambiente", "C", "par.7: registro"),
          P("7", "T_aire_del_recinto_U11", "C",
            "par.7: registro -- es el primer dato que existe de esto"),
          P("7", "T_pared_junto_a_los_tabs", "C", "par.7: registro"),
          P("7", "delta_T_case_U4_U5", "C",
            "par.7: > 5 C es la asimetria intra-pareja de las granjas EP "
            "(v2 §3.2)", hi=5.0),
          P("7", "delta_T_case_U6_U7", "C", "par.7: idem", hi=5.0)]

    # --- Paso 8: cierre de margenes ---------------------------------------
    for riel in ("positivo", "negativo"):
        p.append(P("8", f"margen_{riel}", "V",
                   "par.8: valle - dropout_max - setpoint. Aceptar con "
                   ">= 0.2 V; si no, bajar RV2/RV3", lo=0.2))
    p += [P("8", "setpoint_final_TP7", "V",
            "par.8: suelo bajable garantizado 12.46 V", lo=12.46, hi=13.4),
          P("8", "setpoint_final_TP8", "V",
            "par.8: suelo bajable garantizado -12.42 V", lo=-13.2, hi=-12.42)]
    return p


def plantilla(puntos):
    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    with open(CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for pt in puntos:
            w.writerow([pt.paso, pt.magnitud, pt.unidad, "", "", "",
                        pt.fuente])
    print(f"hoja de campo escrita: {CSV}")
    print(f"  {len(puntos)} puntos, "
          f"{sum(1 for x in puntos if x.es_criterio)} con criterio")
    return 0


def main() -> int:
    puntos = _puntos()
    if "--plantilla" in sys.argv:
        return plantilla(puntos)

    criterios = [p for p in puntos if p.es_criterio]
    registros = [p for p in puntos if not p.es_criterio]
    print(f"bring-up de la fuente v3: {len(puntos)} puntos "
          f"({len(criterios)} con criterio, {len(registros)} de registro)")

    if not os.path.exists(CSV):
        print(f"\nHUECO: no existe {os.path.relpath(CSV, DIR)} -- la placa no "
              f"se ha medido todavia.")
        print("       'python check_bringup.py --plantilla' escribe la hoja.")
        return 2

    medido = {}
    with open(CSV, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            bruto = (fila.get("medido") or "").strip()
            if bruto:
                medido[f"{fila['paso']}|{fila['magnitud']}"] = bruto

    malos, faltan = [], []
    for pt in criterios:
        if pt.clave not in medido:
            faltan.append(pt)
            continue
        porque = pt.juzga(medido[pt.clave])
        if porque:
            malos.append((pt, medido[pt.clave], porque))

    for pt, bruto, porque in malos:
        print(f"  FUERA  paso {pt.paso} {pt.magnitud}: {porque}")
        print(f"         ({pt.rango()}) {pt.fuente}")
    sin_registro = [p for p in registros if p.clave not in medido]

    print(f"\n  medidos y en rango: {len(criterios) - len(malos) - len(faltan)}"
          f" / {len(criterios)}")
    print(f"  fuera de rango:     {len(malos)}")
    print(f"  sin medir:          {len(faltan)} criterios, "
          f"{len(sin_registro)} registros")

    if malos:
        print("\nFALLO: la placa no pasa el bring-up.")
        return 1
    if faltan:
        print(f"\nHUECO: faltan {len(faltan)} de {len(criterios)} criterios "
              f"por medir en la placa fisica.")
        for pt in faltan[:6]:
            print(f"  - paso {pt.paso} {pt.magnitud} ({pt.rango()})")
        if len(faltan) > 6:
            print(f"  ... y {len(faltan) - 6} mas")
        return 2
    print("\nOK: la placa pasa el bring-up entero.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
