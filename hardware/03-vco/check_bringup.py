"""Cierra el lazo del bring-up: contrasta lo MEDIDO contra lo PREDICHO.

    python check_bringup.py               comprueba notes/medidas.csv
    python check_bringup.py --plantilla   escribe la hoja de campo vacia

`notes/bring-up.md` predice un numero en cada punto de la placa y lo hace antes
de que la placa exista, que es exactamente un test escrito antes de la
implementacion. Lo que faltaba era la otra mitad: cuando el numero se mida, que
algo lo compare. Sin eso, el bring-up es un PDF que alguien lee una vez y las
medidas se quedan en un cuaderno.

Aqui la prediccion vive en codigo, con su fuente en la misma linea, y la medida
vive en `notes/medidas.csv` -- que se rellena en el banco, con el multimetro en
la mano, y se commitea. A partir de ahi:

  * una medida fuera de rango pone los gates en ROJO;
  * un punto sin medir deja el script en codigo 2 (trabajo a medias), nunca en
    verde;
  * la segunda placa se compara con la primera sin discutir de memoria.

## Los codigos de salida, y por que 2

Precedente del repo (constitucion, corolario del Principio III): `build_pcb.py`
del modulo 2 sale con 2 mientras queden redes sin rutear, para que no se
confunda con terminado. Aqui igual:

    0   todos los puntos con criterio medidos y dentro de rango
    1   alguna medida FUERA de rango -- la placa no pasa
    2   faltan medidas. Ni bien ni mal: no se sabe todavia

Con la placa aun sin fabricar, lo correcto es 2 y no 0. Un fichero de medidas
vacio que saliera en verde seria la version de banco del esquematico de 711
bytes que paso el ERC con cero errores.

## Dos clases de punto

  * **criterio**: `bring-up.md` da un rango y suspender significa algo. Son los
    que deciden.
  * **registro**: no hay rango que valga porque el numero AUN no existe -- el
    tempco de cada chip, el codigo de PWM al 50 %, el reloj SPI que aguante. Se
    anotan porque el Paso 7 no es aprobado/suspenso: es el primer punto de una
    serie que solo significa algo comparada con la siguiente placa.

Un registro nunca pone nada en rojo. Pero se cuenta y se lista, para que la
placa 2 tenga con que compararse.
"""
from __future__ import annotations

import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(DIR, "notes", "medidas.csv")
COLS = ["paso", "magnitud", "unidad", "medido", "placa", "fecha", "nota"]

R_PITCH_NOM = 16.5e3    # bom.csv
LSB = 38.15e-6          # V, bring-up par.4


class Punto:
    """Un numero que bring-up.md predice, con de donde sale."""

    def __init__(self, paso: str, magnitud: str, unidad: str, fuente: str,
                 lo: float | None = None, hi: float | None = None,
                 literal: str | None = None) -> None:
        self.paso, self.magnitud, self.unidad = paso, magnitud, unidad
        self.fuente, self.lo, self.hi, self.literal = fuente, lo, hi, literal

    @property
    def clave(self) -> str:
        return f"{self.paso}|{self.magnitud}"

    @property
    def es_criterio(self) -> bool:
        return not (self.lo is None and self.hi is None and self.literal is None)

    def rango(self) -> str:
        if self.literal is not None:
            return f"= {self.literal}"
        if self.lo is not None and self.hi is not None:
            return f"{self.lo:g} .. {self.hi:g}"
        if self.hi is not None:
            return f"<= {self.hi:g}"
        if self.lo is not None:
            return f">= {self.lo:g}"
        return "registro"

    def juzga(self, bruto: str) -> str | None:
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


def _puntos() -> list[Punto]:
    P, p = Punto, []

    # --- Paso 1: rieles y VREF (bring-up par.1, tabla) --------------------
    p += [P("1", "I_+12V", "mA", "par.1: 30-40 mA con chips, 10-15 sin; "
            "'si pasa de 60 mA, apaga'", hi=60.0),
          P("1", "I_-12V", "mA", "par.1: 12-18 mA con chips, ~2 sin; "
            "'si pasa de 30 mA, apaga'", hi=30.0),
          P("1", "TP3_+5V_LOC", "V", "par.1: 5.00 V +-5 %", lo=4.75, hi=5.25),
          P("1", "TP4_+3V3_LOC", "V", "par.1: 3.30 V +-5 %", lo=3.14, hi=3.47),
          P("1", "TP5_VREF_antes_de_0111", "V",
            "par.1: ventana ANCHA, 4 referencias peleando", lo=2.490, hi=2.510)]
    for v in (1, 2, 3, 4):
        p.append(P("1", f"TP{5+v}_CV_PITCH_{v}_al_arrancar", "V",
                   "par.1: RSTSEL a GNDA -> fondo de escala cero", lo=0.0, hi=0.005))

    # --- Paso 2: I2C (bring-up par.2) -------------------------------------
    p += [P("2", "I2C_responde_0x48_TMP1075", "si/no", "par.2", literal="si"),
          P("2", "I2C_responde_0x50_EEPROM", "si/no", "par.2", literal="si"),
          P("2", "T_inicial", "C", "par.2: registro, no hay rango")]

    # --- Paso 3: SPI (bring-up par.3) -------------------------------------
    p += [P("3", "passthrough_aciertos_de_1000", "tramas",
            "par.3: 1000/1000, BLOQUEANTE", lo=1000, hi=1000),
          P("3", "reloj_SPI_de_la_prueba", "MHz", "par.3: registro")]

    # --- Paso 4: VREF fijada y barrido del DAC (bring-up par.4) -----------
    p.append(P("4", "TP5_VREF_tras_0111", "V",
               "par.4: 2.5000 V +-0.0005 (precision inicial ADR4525B)",
               lo=2.4995, hi=2.5005))
    codigos = (("0x0000", 0.0), ("0x4000", 0.6250), ("0x8000", 1.2500),
               ("0xC000", 1.8750), ("0xFFFF", 2.5000))
    for v in (1, 2, 3, 4):
        for cod, esperado in codigos:
            p.append(P("4", f"TP{5+v}_CV_PITCH_{v}_a_{cod}", "V",
                       f"par.4: barrido del DAC, {esperado:.4f} V +-1 mV "
                       f"(1 LSB = {LSB*1e6:.2f} uV)",
                       lo=esperado - 0.001, hi=esperado + 0.001))

    # --- Paso 5: LA apuesta trimless (bring-up par.5) ---------------------
    for v in (1, 2, 3, 4):
        p += [P("5", f"span_B_extrapolado_voz{v}", "oct",
                "par.5: EL criterio de aprobado. pitch_budget.py lo predice",
                lo=7.0),
              P("5", f"span_A_usable_voz{v}", "oct",
                "par.5: registro. Sale por debajo de B por los 5 uA de R_LIN"),
              P("5", f"R_PITCH_montada_voz{v}", "ohm",
                f"par.5: registro. {R_PITCH_NOM/1e3:.1f} k salvo bodge")]

    # --- Paso 5b: audio (bring-up par.5b) ---------------------------------
    for v in (1, 2, 3, 4):
        p.append(P("5b", f"TP{9+v}_MIXO_{v}", "V",
                   "par.5b: tierra virtual del TL074H, |V| < 5 mV",
                   lo=-0.005, hi=0.005))
    for v in (1, 2, 3, 4):
        p.append(P("5b", f"codigo_PWM_50pc_voz{v}", "codigo",
                   "par.5b: registro. Van a salir distintos entre voces"))

    # --- Paso 6: autoafinado (bring-up par.6) -----------------------------
    p += [P("6", "segunda_pasada_error", "cents",
            "par.6: 2a pasada por debajo de 1 cent", hi=1.0),
          P("6", "barrido_completo", "s", "par.6: registro"),
          P("6", "blob_releido_tras_ciclar", "si/no", "par.6", literal="si")]

    # --- Paso 7: temperatura (bring-up par.7) -----------------------------
    for v in (1, 2, 3, 4):
        p.append(P("7", f"cents_por_C_voz{v}", "cents/C",
                   "par.7: registro. Primer punto de la serie, no hay rango"))

    # --- Paso 8: diafonia del mazo (bring-up par.8) -----------------------
    p += [P("8", "sigma_con_SPI_quieto", "cents",
            "par.8: suelo de medida del autoafinado", hi=0.5),
          P("8", "sigma_con_SPI_a_10MHz", "cents",
            "par.8: 'no empeora por encima de 0.5 cents'", hi=0.5),
          P("8", "reloj_SPI_adoptado", "MHz",
            "par.8: registro. ESTE numero es el contrato, no el <=10 del spec")]
    return p


PUNTOS = _puntos()
POR_CLAVE = {q.clave: q for q in PUNTOS}


def plantilla() -> None:
    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    with open(CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for q in PUNTOS:
            w.writerow([q.paso, q.magnitud, q.unidad, "", "", "", ""])
    print(f"escrita la hoja de campo: {os.path.relpath(CSV, DIR)} "
          f"({len(PUNTOS)} puntos, columna 'medido' vacia)")


def lee() -> list[dict]:
    if not os.path.exists(CSV):
        return []
    with open(CSV, encoding="utf-8", newline="") as fh:
        return [f for f in csv.DictReader(fh)]


def autocomprobacion() -> None:
    """Que el juez DETECTE lo que tiene que detectar.

    Un comparador que devuelve 'dentro de rango' pase lo que pase deja el
    bring-up entero en verde con la placa echando humo.
    """
    q = POR_CLAVE["1|TP3_+5V_LOC"]
    assert q.juzga("5.00") is None, "un 5.00 V bueno no puede suspender"
    assert q.juzga("5.60") is not None, "5.60 V esta fuera y paso"
    assert q.juzga("4.10") is not None, "4.10 V esta fuera y paso"
    assert q.juzga("5,01") is None, "coma decimal: se mide en Europa"
    assert q.juzga("hola") is not None, "texto donde va un numero"

    b = POR_CLAVE["5|span_B_extrapolado_voz1"]
    assert b.juzga("7.58") is None and b.juzga("6.90") is not None, \
        "el criterio del par.5 (B >= 7.0) no discrimina"

    lit = POR_CLAVE["2|I2C_responde_0x48_TMP1075"]
    assert lit.juzga("si") is None and lit.juzga("no") is not None

    reg = POR_CLAVE["7|cents_por_C_voz1"]
    assert not reg.es_criterio and reg.juzga("-1.4") is None, \
        "un registro no puede suspender"

    assert len({q.clave for q in PUNTOS}) == len(PUNTOS), "claves repetidas"
    print(f"autocomprobacion OK (juez de rango, literales, registros, "
          f"{len(PUNTOS)} claves unicas)")


def main(argv: list[str]) -> int:
    autocomprobacion()
    if "--plantilla" in argv:
        plantilla()
        return 0

    filas = lee()
    if not filas:
        print(f"\nno existe {os.path.relpath(CSV, DIR)}. "
              f"Corre: python check_bringup.py --plantilla")
        return 2

    medidas = {f"{f['paso']}|{f['magnitud']}": f for f in filas
               if (f.get("medido") or "").strip()}
    desconocidas = sorted(set(medidas) - set(POR_CLAVE))
    criterios = [q for q in PUNTOS if q.es_criterio]
    registros = [q for q in PUNTOS if not q.es_criterio]

    malas: list[str] = []
    for q in PUNTOS:
        f = medidas.get(q.clave)
        if f and (motivo := q.juzga(f["medido"])):
            malas.append(f"Paso {q.paso} {q.magnitud}: {motivo}\n"
                         f"      predicho: {q.rango()} {q.unidad}  ({q.fuente})"
                         + (f"\n      nota: {f['nota']}" if f.get("nota") else ""))

    c_med = sum(1 for q in criterios if q.clave in medidas)
    r_med = sum(1 for q in registros if q.clave in medidas)
    print(f"\nbring-up del modulo 3, contra notes/bring-up.md\n")
    print(f"  criterios (deciden):  {c_med:3}/{len(criterios):3} medidos, "
          f"{len(malas)} fuera de rango")
    print(f"  registros (anotar):   {r_med:3}/{len(registros):3} medidos")

    for m in malas:
        print(f"\n  FUERA DE RANGO  {m}")
    for k in desconocidas:
        print(f"\n  AVISO: '{k}' esta en el CSV y no en bring-up.md. "
              f"Si es una medida nueva, anadela a _puntos() con su fuente.")

    if malas:
        print(f"\n{len(malas)} medida(s) fuera de rango. La placa NO pasa.")
        return 1
    faltan = len(criterios) - c_med
    if faltan:
        print("\n(codigo 2 = trabajo a medias, no es un fallo)")
        print(f"faltan {faltan} de {len(criterios)} criterios por medir en la "
              f"placa fisica")
        return 2
    print(f"\nlos {len(criterios)} criterios medidos y dentro de rango. "
          f"BRING-UP EN VERDE.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
