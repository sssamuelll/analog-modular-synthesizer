"""La fuente v5: un ladrillo de catalogo afuera y la conversion adentro.

    python ladrillo_budget.py        (sale con codigo 2: HUECOS declarados)

## Por que existe

Samuel decidio el 2026-09-05 sacar la etapa AC-DC de la caja de madera. La v4
mete seis modulos Mean Well, la entrada de red, el fusible, la NTC de arranque,
el choke de modo comun y los Y2 al chasis DENTRO de un instrumento de madera; y
ademas los mete en un recinto de acero de 338,6 x 176,6 x 83 mm que ocupa el
30 % del suelo interior.

La v5 compra ese trozo hecho --un ladrillo AC-DC certificado, una tension-- y
deriva los rieles dentro con DC-DC. Este guion pone las cifras con las hojas
versionadas en `docs/reference/datasheets/`.

## Lo que este guion contesta, y que nadie mas contestaba

**1. El calor que se va NO es el que la gente supone (#338).** El calor de una
caja lo hacen las CARGAS, y las cargas no se mudan. Lo que se muda es la
perdida de CONVERSION. Dicho al reves y en su forma mas limpia:

    todo lo que baja por el cordon acaba en calor dentro de la caja.

Para que esa identidad sea una comprobacion y no una tautologia (#338), los dos
lados salen de dos descripciones distintas del mismo circuito:
- `potencia_que_entra_w()`, el lado ELECTRICO: cada convertidor por lo que
  DECLARA entregar (`rieles()`: la tension de su riel por su corriente
  declarada, la de la cascada importada de `margen_budget.py`) dividido por su
  rendimiento. Con eso se resuelve la corriente del cordon, y lo que entra en
  la caja es lo que da el ladrillo menos lo que el cordon quema por fuera.
- `calor_del_cajon_w()`, el lado TERMICO: lo que disipa cada pieza con su
  propia fisica, de abajo arriba y sin leer la corriente que declara su
  convertidor (`focos_de_calor()`): cada carga a su tension, el shunt por
  I^2 R, cada LDO por (Vin - Vout) * Iout + Vin * Ignd con la Ignd de SU hoja,
  cada DC-DC por Pout * (1/eta - 1) con la Pout que le piden sus piezas, y la
  cadena de entrada (conector, MOSFET de polaridad, eFuse) por I^2 R.
Solo coinciden si cada convertidor declara exactamente lo que cuelga de el: una
pieza que falta en un lado, una Ignd que no llega a la corriente de su rama o
una perdida mal formulada los separan, y `_guarda_balance_energia` salta. Lo
que ningun balance ve es una carga que falta en los DOS lados (`no_cubre()`).

**2. La tension cruda deja de ser un dato de catalogo, y eso da holgura a la
cascada.** El 06-09 se firmo **D-F9** y `U2` paso a LT3015. Con **D-F8** (`U1`
en LT1963A) e `Iq_max = 120 mA` a plena carga sobre temperatura (#343,
`lt1963a-rev-g-2021-02.pdf` p. 5), `U1` a 15,0 V queda en +283 mV y a 15,5 V
sube a +764 mV (+723 mV tras los 41 mV del eFuse `TPS26631` de M3).

**3. M1 y H-CENSO-ETA-DIGITAL cerrados con hoja.** La decision M1 (2026-09-08)
exige aislar el convertidor del +5 V digital. El modulo **Mornsun
URB2405YMD-20WR3** (`mornsun_urb_ymd20wr3.pdf` p. 1) garantiza **88 % minimo**
(90 % tipico) a plena carga con aislamiento de 1500 VDC. Al pasar la rama
digital de `0,90` (buck no aislado) a `0,88` (minimo garantizado aislado), la
perdida interior sube en **+0,37 W** (de 7,99 W a 8,36 W) y la salida pedida al
ladrillo pasa de **64,22 W (2,68 A)** a **64,58 W (2,69 A)**; cifras de antes de
contar la Ignd de U1/U2 y de los LT, el +5V_AUX y la cadena de entrada.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(DIR, "..", "v4")
TOOLS = os.path.join(DIR, "..", "..", "tools")
for _d in (V4, TOOLS):
    if _d not in sys.path:
        sys.path.append(_d)

# --- lo que la v4 ya decidio y aqui NO se vuelve a escribir ----------------
# Se importan para que un cambio alli se vea aqui, en vez de quedarse pegado.
from calor_budget import (CAJON_DIGITAL_A, PLACA_A,       # noqa: E402
                          V_RIEL, p_cajon_w, p_recinto_w)
from canario import borde_rojo                            # noqa: E402


def _carga(nombre: str, ruta: str):
    """Un guion hermano por su ruta: v3, v4 y v5 repiten nombres de fichero."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mb = _carga("_v4_margen_budget", os.path.join(V4, "margen_budget.py"))
m5 = _carga("_v5_margen_budget", os.path.join(DIR, "margen_budget.py"))

# --- D-B2, firmada el 2026-09-05 -------------------------------------------
FILA_B_A = 0.500          # A/riel declarados en la fila de abajo

# --- la cascada ultra (D-F1, #343): IMPORTADA de margen_budget.py v5 -------
# margen_budget es el dueno de la corriente de cada rama: la carga de D-F1 mas
# la Ignd del pre-regulador a plena carga sobre temperatura (LT1963A 120 mA,
# lt1963a-rev-g-2021-02.pdf p. 5; LT3015 70 mA, lt3015-rev-b.pdf p. 5; las dos
# en la fila de 1,5 A, cota de los ~0,7 A que llevan).
CASCADA_A = m5.I_CARGA_A
IQ_PRE_A = {"U1": m5.IQ_U1_MAX_A, "U2": m5.IQ_U2_MAX_A}
# El censo real (invitados_budget) son 340 + 327 mA: la declaracion es el doble.
CASCADA_CENSO_A = (0.340 + 0.327) / 2
# Detras de cada pre-regulador va un PAR de LDO ultra en paralelo (bom.csv:
# U4,U5 = LT3045 tras U1; U6,U7 = LT3094 tras U2). Su Ignd entra por el pin IN,
# sale por la masa y no llega a la carga: la pagan U1/U2 y el THN. Fila de
# ILOAD = 500 mA con VIN = VOUT, que es el peor caso (en caida: Note 6 de la
# LT3045, Note 11 de la LT3094); cada pieza lleva ~325 mA y la Ignd crece con
# la carga.
LDO_ULTRA = {"U1": "LT3045", "U2": "LT3094"}
N_LDO_ULTRA_POR_RAMA = 2
IGND_LDO_ULTRA_MAX_A = {"U1": 0.025,    # lt3045-rev-d.pdf p. 3, GND Pin Current
                        "U2": 0.023}    # lt3094-rev-b.pdf p. 4, GND Pin Current
# El digital: cargas duras del peor caso de la hoja, ya SIN la cadena de LED que
# D1 retiro (ver calor_budget). El tipico son 0,965 A: 3,0 veces menos. #256.
DIGITAL_A = CAJON_DIGITAL_A
DIGITAL_TYP_A = 0.965
# La pantalla de 7": 2026-08-26-pantalla-motor-design.md l.268-277 la manda al
# presupuesto de la fuente "cuando la pieza tenga nombre". Va con retorno
# dedicado, no por el bus.
PANTALLA_A = 0.550

# --- el +5 V auxiliar ------------------------------------------------------
# Sale de PS3 por el shunt R20 (kicad/build_schematic.py, telemetria()) y
# alimenta la isla de telemetria (4 x INA226, ADS1115, TMP1075, lado 1 del
# ISO1541, el detector D-F4) y J6 al modulo 2. Corriente y shunt son los de la
# fila U12 de check_telemetria.SHUNTS_V5, la que dimensiona su medida: 300 mA,
# el techo de diseno de ese riel desde la fuente v2
# (2026-08-18-fuente-chasis-telemetria.md sec.3.1, "300 mA como limite de diseno";
# docs/architecture-poly.md sec.9: "de diseno, no una estimacion que se pueda estirar").
# El shunt se lee de bom.csv. La corriente vive AQUI y check_telemetria la
# importa para dimensionar el INA226 U12.
R_SHUNT_AUX_OHM = _carga("_v5_bom_valores", os.path.join(DIR, "bom_valores.py")).valor("R20")
AUX_A = 0.300
# Censo: "con el modulo 2 mas la isla de telemetria ... ~30 mA" (misma spec, sec.3.1).
AUX_CENSO_A = 0.030

# --- el ladrillo (D-V2) y los candidatos con hoja --------------------------
V_LADRILLO = 24.0
TOL_LADRILLO = 0.05       # +-5 % ventana de salida estandar en 24 V
V_LADRILLO_MIN = V_LADRILLO * (1.0 - TOL_LADRILLO)
ETA_LADRILLO = 0.88       # DoE Level VI (>= 88 % en 90-120 W)

# Potencia continua garantizada a 45 C de ambiente (curvas de derating en hoja):
LADRILLOS_45C_W = {
    "AE/SL Power TE90A2403F01 (ae-TE90-datasheet.pdf p.3)": 82.5,
    "Mean Well GST120A24-R7B 230VAC (meanwell-GST120A-spec.pdf p.3)": 120.0,
    "Mean Well GST120A24-R7B 100VAC (meanwell-GST120A-spec.pdf p.3)": 108.0,
    "Mean Well GSM120A24-R7B (meanwell-GSM120A-spec.pdf p.3)": 108.0,
}

# --- la cadena de entrada de 24 V (D-V5, M5) -------------------------------
# Conector Kycon KPJX-PM-4S + KPPX-4P (kycon_KPJX-PM-4S.pdf p. 1,
# kycon_KPPX-4P.pdf p. 1): 30 mohm max por pin, 7.5 A/pin, 2 pines en paralelo
# por polo -> 15 mohm por polo, 30 mohm de bucle ida y vuelta.
R_CONTACTO_PIN_OHM = 0.030
N_PINES_PARALELO = 2
R_BUCLE_CONECTOR_OHM = 2.0 * (R_CONTACTO_PIN_OHM / N_PINES_PARALELO)
# Vigilante de entrada M5: TI TPS26631 (tps2663.pdf p. 7: RON max 53 mohm a
# TJ=125 C) + bloqueo de polaridad TI LM74502 (lm74502.pdf p. 1) con MOSFET
# externo de 15 mohm max.
R_ON_EFUSE_ENTRADA_OHM = 0.053
R_ON_POLARIDAD_OHM = 0.015
# Todo eso vive en la caja: su I^2 R es calor del cajon, no del cordon.
R_ENTRADA_CAJA_OHM = R_BUCLE_CONECTOR_OHM + R_ON_POLARIDAD_OHM + R_ON_EFUSE_ENTRADA_OHM
# El cordon de diseno: 16 AWG de 2 m, cobre a 20 C.
OHM_POR_M_CORDON = 0.0132
LARGO_CORDON_M = 2.0
# UVLO maximo de arranque de los convertidores interiores:
# URB2405YMD-20WR3: 9.0 V max (mornsun_urb_ymd20wr3.pdf p. 2)
# THN 20-2413WI / THN 30-2422WI: 8.8 V max (traco_thn20wi.pdf / thn30wi.pdf p. 1)
# K7805T-1000R3: 8.0 V min de rango operativo (mornsun_k78_t1000r3.pdf p. 1)
V_ARRANQUE_DCDC_MAX_V = 9.0

# --- los convertidores de dentro (M1, H-CENSO-ETA-DIGITAL) -----------------
# Cotas de diseno para el presupuesto termico. Las hojas de TRACO, Mornsun K78
# y RECOM solo publican el tipico (ver ESTIMADOS).
ETA_BUCK = 0.90
ETA_INVERSOR = 0.85
ETA_AISLADO = 0.85
# M1 (H-CENSO-ETA-DIGITAL): Mornsun URB2405YMD-20WR3 publica 88 % minimo
# garantizado y 90 % tipico a plena carga (mornsun_urb_ymd20wr3.pdf p. 1).
ETA_DIGITAL_AISLADO = 0.88

# Eficiencias publicadas en hoja a 24 V nominales para comparacion directa:
ETA_HOJA_TIPICA = {
    "+12 rack (bus fila B + pantalla)": 0.89,   # TRACO THN 30-2422WI p. 1 (89% typ)
    "-12 rack (bus fila B)": 0.89,              # TRACO THN 30-2422WI p. 1 (89% typ)
    "+5 rack (bus fila B + +5V_AUX)": 0.88,     # RECOM RPMB5.0-2.0 p. 2 (88% typ)
    "+5 digital (4 x N657 + host USB)": 0.90,   # Mornsun URB2405YMD-20WR3 p. 1 (90% typ, 88% min)
    "crudo +cascada (a U1)": 0.89,              # TRACO THN 20-2413WI p. 1 (89% typ)
    "crudo -cascada (a U2)": 0.89,              # TRACO THN 20-2413WI p. 1 (89% typ)
}

# --- la tension cruda de la cascada (D-V3) ---------------------------------
V_CRUDO_CASCADA = 15.5
TOL_CRUDO = 0.025         # +-2,5 % tras recorte por pin Trim (+3,3 % nominal)
SETPOINT_V = {"U1": 13.10, "U2": 12.90}
V_ULTRA_SALIDA_V = 12.0

ESTIMADOS = (
    f"ETA_BUCK={ETA_BUCK}, ETA_INVERSOR={ETA_INVERSOR}, ETA_AISLADO={ETA_AISLADO}: "
    "THN 30-2422WI, THN 20-2413WI, K7805T-1000R3 y RPMB5.0-2.0 solo publican "
    "tipicos (el K78 da 93/85 % a Vin min/max, p. 1). ETA_BUCK queda POR ENCIMA "
    "del tipico en +12 rack (89 %) y +5 rack (88 % del RPMB); la rama -12 y las "
    "de la cascada van por debajo",
    f"TOL_CRUDO={TOL_CRUDO}: +-2,5 % conservador tras recorte Trim (+-1 % base en thn20wi.pdf p. 2)",
    "IGND_LDO_ULTRA_MAX_A: la fila de 500 mA de la hoja aplicada a ~325 mA por "
    "pieza; es cota por arriba, la hoja no publica la de 325 mA",
    f"AUX_A={AUX_A}: techo de diseno del +5V_AUX, no un limite fisico (nada en "
    "el riel corta a 300 mA). El modulo de la fuente cita 100 mA a J6; la fuente "
    "v2 censaba ~30 mA con el modulo 2 y la telemetria",
)

HUECOS: tuple[str, ...] = (
    "Pantalla de 7 pulgadas sin pieza: pantalla-motor l.268-277 manda su fila "
    "'cuando la pieza tenga nombre'. Entra con 550 mA de +12 V: el techo de los "
    "450-550 mA que aquel papel cita para un tactil de 7 (600 el backpack de "
    "Adafruit), cobrados enteros a 12 V. Son 6,6 W de carga mas su conversion, "
    "y salen de una cita, no de una hoja",
    "#256 abierto: el digital entra por su maximo a TJ=125 C (2,895 A) porque el "
    "punto de trabajo real (85 C) no esta publicado. El tipico son 0,965 A: 3,0 "
    "veces menos",
)

# Lo que el lado TERMICO deja mover para que los canarios prueben el balance.
P_BASE: dict[str, float] = {
    "iq_U1_a": IQ_PRE_A["U1"],
    "iq_U2_a": IQ_PRE_A["U2"],
    "aux_a": AUX_A,
    "v_arranque_dcdc_v": V_ARRANQUE_DCDC_MAX_V,
}


# === lado ELECTRICO: lo que declara cada convertidor =======================

def corriente_thn_a(reg: str) -> float:
    """Lo que DECLARA entregar el THN 20-2413WI de la rama de `reg`.

    `margen_budget.corriente_rama_a()` cuenta la carga y la Ignd del
    pre-regulador (#343), pero no la Ignd del par de LDO ultra, que tambien
    entra por el pin IN de U1/U2 y pasa por su LC. Se suma aqui; el dia que
    margen_budget la cuente, `_guarda_balance_energia` salta por doble cuenta
    y este sumando sobra.
    """
    return m5.corriente_rama_a(reg) + N_LDO_ULTRA_POR_RAMA * IGND_LDO_ULTRA_MAX_A[reg]


def rieles(*, eta_digital: float = ETA_DIGITAL_AISLADO) -> list[dict]:
    """Cada convertidor de dentro y lo que declara entregar.

    El +12 de rack lleva DOS cargas por cables distintos: el bus de la fila de
    abajo y la pantalla con su retorno dedicado. Van juntas en el convertidor y
    separadas en el cableado, que es lo que pide pantalla-motor. PS3 lleva el
    +5 de la fila y, por R20, el +5V_AUX.
    """
    v_alto = V_CRUDO_CASCADA * (1 + TOL_CRUDO)   # el peor caso PARA EL CALOR
    return [
        {"nombre": "+12 rack (bus fila B + pantalla)", "v": V_RIEL["rack+12"],
         "a": FILA_B_A + PANTALLA_A, "eta": ETA_BUCK,
         "pieza": "TRACO THN 30-2422WI (rama +12 V)"},
        {"nombre": "-12 rack (bus fila B)", "v": V_RIEL["rack-12"],
         "a": FILA_B_A, "eta": ETA_INVERSOR,
         "pieza": "TRACO THN 30-2422WI (rama -12 V)"},
        {"nombre": "+5 rack (bus fila B + +5V_AUX)", "v": V_RIEL["rack+5"],
         "a": FILA_B_A + AUX_A, "eta": ETA_BUCK,
         "pieza": "Mornsun K7805T-1000R3 (PS3) / RECOM RPMB5.0-2.0"},
        {"nombre": "+5 digital (4 x N657 + host USB)", "v": 5.0,
         "a": DIGITAL_A, "eta": eta_digital,
         "pieza": "Mornsun URB2405YMD-20WR3 (aislado M1, 88% min)"},
        {"nombre": "crudo +cascada (a U1)", "v": v_alto,
         "a": corriente_thn_a("U1"), "eta": ETA_AISLADO,
         "pieza": "TRACO THN 20-2413WI #1 (Trim +15,5 V)"},
        {"nombre": "crudo -cascada (a U2)", "v": v_alto,
         "a": corriente_thn_a("U2"), "eta": ETA_AISLADO,
         "pieza": "TRACO THN 20-2413WI #2 (invertido, Trim -15,5 V)"},
    ]


def entregado_w() -> float:
    """Lo que declaran entregar los DC-DC interiores."""
    return sum(r["v"] * r["a"] for r in rieles())


def entrada_dcdc_w(*, eta_digital: float = ETA_DIGITAL_AISLADO) -> float:
    """Lo que piden los DC-DC por su entrada de 24 V: `V_out * I_out / eta`."""
    return sum(r["v"] * r["a"] / r["eta"] for r in rieles(eta_digital=eta_digital))


def entrada_dcdc_tipica_hoja_w() -> float:
    """Lo mismo con las eficiencias tipicas de hoja a 24 V."""
    return sum(r["v"] * r["a"] / ETA_HOJA_TIPICA[r["nombre"]] for r in rieles())


def r_cordon_ohm(ohm_por_m: float = OHM_POR_M_CORDON,
                 largo_m: float = LARGO_CORDON_M) -> float:
    """Ida y vuelta. El cordon es de DOS hilos: no hay rieles en el."""
    return 2.0 * ohm_por_m * largo_m


def _corriente_a(p_dcdc_w: float, ohm_por_m: float, largo_m: float) -> float:
    """Una carga de potencia constante detras de toda la resistencia serie, con
    el ladrillo en el borde bajo de su ventana: V * I - R * I^2 = P, la raiz
    pequena."""
    r = r_cordon_ohm(ohm_por_m, largo_m) + R_ENTRADA_CAJA_OHM
    v = V_LADRILLO_MIN
    return (v - math.sqrt(v * v - 4.0 * r * p_dcdc_w)) / (2.0 * r)


def corriente_del_cordon_a(ohm_por_m: float = OHM_POR_M_CORDON,
                           largo_m: float = LARGO_CORDON_M) -> float:
    """La corriente continua del cordon, en su peor caso.

    Los DC-DC piden POTENCIA, no corriente: cuanto menos tension les llega, mas
    tiran. El peor caso es el ladrillo al -5 % con el cordon, el conector, el
    MOSFET de polaridad y el eFuse delante de `entrada_dcdc_w()`.
    """
    return _corriente_a(entrada_dcdc_w(), ohm_por_m, largo_m)


def salida_ladrillo_w() -> float:
    """Lo que el ladrillo entrega por su borne en ese peor caso."""
    return V_LADRILLO_MIN * corriente_del_cordon_a()


def potencia_que_entra_w() -> float:
    """Lado ELECTRICO (#338): lo que el cordon mete en la caja, visto desde el
    ladrillo: lo que da por su borne menos lo que el cordon quema por fuera."""
    i = corriente_del_cordon_a()
    return salida_ladrillo_w() - i * i * r_cordon_ohm()


def pedido_a_la_red_w() -> float:
    """Lo que el ladrillo pide a la red. La diferencia se disipa FUERA."""
    return salida_ladrillo_w() / ETA_LADRILLO


def caida_cordon_v(ohm_por_m: float, largo_m: float) -> float:
    return r_cordon_ohm(ohm_por_m, largo_m) * corriente_del_cordon_a(ohm_por_m, largo_m)


def caida_entrada_completa_v(ohm_por_m: float = OHM_POR_M_CORDON,
                             largo_m: float = LARGO_CORDON_M) -> float:
    """Caida total desde el ladrillo hasta la entrada de los DC-DC (D-V5, M5).

    Suma: cordon (2 hilos) + conector Kycon KPJX-PM-4S/KPPX-4P (2 pines/polo) +
    MOSFET de polaridad LM74502 + eFuse de entrada TPS26631.
    """
    r = r_cordon_ohm(ohm_por_m, largo_m) + R_ENTRADA_CAJA_OHM
    return r * corriente_del_cordon_a(ohm_por_m, largo_m)


def tension_minima_en_dcdc_v(ohm_por_m: float = OHM_POR_M_CORDON,
                             largo_m: float = LARGO_CORDON_M) -> float:
    """Tension minima que llega a la entrada de los convertidores DC-DC."""
    return V_LADRILLO_MIN - caida_entrada_completa_v(ohm_por_m, largo_m)


# === lado TERMICO: lo que disipa cada pieza ================================

def cascada_w(reg: str, *, v_thn: float, iq_pre: float) -> dict[str, float]:
    """Una rama de la cascada desde el borne de su THN, pieza a pieza.

    Las corrientes se arman de abajo arriba: la carga mas la Ignd del par de LDO
    es lo que sale de U1/U2; mas la Ignd de U1/U2, lo que pasa por el LC. Cada
    LDO: (Vin - Vout) * Iout + Vin * Ignd (lt1963a-rev-g-2021-02.pdf p. 19 y
    lt3015-rev-b.pdf p. 19, "Calculating Junction Temperature"). Los ballast
    R15..R18 y el shunt de U8 quedan dentro del par y de la carga.
    """
    i_gnd_ldo = N_LDO_ULTRA_POR_RAMA * IGND_LDO_ULTRA_MAX_A[reg]
    i_pre = CASCADA_A + i_gnd_ldo
    i_rama = i_pre + iq_pre
    r_serie = m5.resistencia_serie_rama_ohm(reg)
    v_in = v_thn - i_rama * r_serie
    v_pre = SETPOINT_V[reg]
    return {
        "filtro de entrada (LC, ferrita" + (", eFuse M3)" if reg == "U1" else ")"):
            i_rama ** 2 * r_serie,
        f"{reg} (pre-regulador)": (v_in - v_pre) * i_pre + v_in * iq_pre,
        f"{LDO_ULTRA[reg]} x{N_LDO_ULTRA_POR_RAMA}":
            (v_pre - V_ULTRA_SALIDA_V) * CASCADA_A + v_pre * i_gnd_ldo,
        "carga ultra": V_ULTRA_SALIDA_V * CASCADA_A,
    }


def focos_de_calor(p: dict[str, float] = P_BASE) -> dict[str, dict[str, float]]:
    """Lo que disipa cada pieza, agrupado por el convertidor del que cuelga.

    Ninguna cifra sale de la corriente que declara el convertidor: cada pieza
    pone la suya.
    """
    v_alto = V_CRUDO_CASCADA * (1 + TOL_CRUDO)
    v5 = V_RIEL["rack+5"]
    return {
        "+12 rack (bus fila B + pantalla)": {
            "fila B": V_RIEL["rack+12"] * FILA_B_A,
            "pantalla 7\"": V_RIEL["rack+12"] * PANTALLA_A},
        "-12 rack (bus fila B)": {
            "fila B": V_RIEL["rack-12"] * FILA_B_A},
        "+5 rack (bus fila B + +5V_AUX)": {
            "fila B": v5 * FILA_B_A,
            "R20 (shunt del +5V_AUX)": p["aux_a"] ** 2 * R_SHUNT_AUX_OHM,
            "+5V_AUX (telemetria y J6)": (v5 - p["aux_a"] * R_SHUNT_AUX_OHM) * p["aux_a"]},
        "+5 digital (4 x N657 + host USB)": {
            "cerebro digital": 5.0 * DIGITAL_A},
        "crudo +cascada (a U1)": cascada_w("U1", v_thn=v_alto, iq_pre=p["iq_U1_a"]),
        "crudo -cascada (a U2)": cascada_w("U2", v_thn=v_alto, iq_pre=p["iq_U2_a"]),
    }


def perdida_dcdc_w(p: dict[str, float] = P_BASE) -> float:
    """Calor de conversion de los DC-DC: la Pout que les piden sus piezas por
    (1/eta - 1)."""
    eta = {r["nombre"]: r["eta"] for r in rieles()}
    return sum(sum(f.values()) * (1.0 / eta[n] - 1.0)
               for n, f in focos_de_calor(p).items())


def calor_del_cajon_w(p: dict[str, float] = P_BASE) -> float:
    """Lado TERMICO (#338): todo lo que se disipa dentro de la caja.

    Las piezas de `focos_de_calor()`, la conversion de los DC-DC y la cadena de
    entrada (Kycon, MOSFET del LM74502, TPS26631) por I^2 R, con la corriente
    que piden ESTAS piezas. No llama a `potencia_que_entra_w()`.
    """
    piezas = sum(sum(f.values()) for f in focos_de_calor(p).values())
    conversion = perdida_dcdc_w(p)
    i = _corriente_a(piezas + conversion, OHM_POR_M_CORDON, LARGO_CORDON_M)
    return piezas + conversion + i * i * R_ENTRADA_CAJA_OHM


def perdida_entrada_w() -> float:
    """Lo que quema la cadena de entrada DENTRO de la caja."""
    return corriente_del_cordon_a() ** 2 * R_ENTRADA_CAJA_OHM


def quema_pre_regulador_w(reg: str, *, v_nom: float = V_CRUDO_CASCADA,
                          tol: float = TOL_CRUDO) -> float:
    """Lo que U1 o U2 disipa con el THN en `v_nom * (1 + tol)`."""
    return cascada_w(reg, v_thn=v_nom * (1 + tol),
                     iq_pre=IQ_PRE_A[reg])[f"{reg} (pre-regulador)"]


# === lo demas ==============================================================

def margen_cascada_v(reg: str, *, v_nom: float = V_CRUDO_CASCADA,
                     tol: float = TOL_CRUDO) -> float:
    """El margen de U1/U2 con la tension cruda que ESTE papel elige."""
    nom0, tol0 = mb.V_NOM, mb.TOL_FRAC
    try:
        mb.V_NOM, mb.TOL_FRAC = v_nom, tol
        return mb.margen_v(reg)
    finally:
        mb.V_NOM, mb.TOL_FRAC = nom0, tol0


def declarado_v4_w() -> float:
    """Lo que la v4 declara que hay que evacuar de esta caja, para comparar."""
    return p_cajon_w(PLACA_A) + p_recinto_w(PLACA_A)


def censo_optimista_w() -> float:
    """Lo que piden los DC-DC con los censos en vez de las declaraciones."""
    v_alto = V_CRUDO_CASCADA * (1 + TOL_CRUDO)
    filas = [
        (V_RIEL["rack+12"], 0.300 + PANTALLA_A, ETA_BUCK),
        (V_RIEL["rack-12"], 0.300, ETA_INVERSOR),
        (V_RIEL["rack+5"], 0.300 + AUX_CENSO_A, ETA_BUCK),
        (5.0, DIGITAL_TYP_A, ETA_DIGITAL_AISLADO),
        (v_alto, CASCADA_CENSO_A, ETA_AISLADO),
        (v_alto, CASCADA_CENSO_A, ETA_AISLADO),
    ]
    return sum(v * a / eta for v, a, eta in filas)


def no_cubre() -> tuple[str, ...]:
    return (
        "Una carga que falta en los DOS lados: el balance cruza dos descripciones "
        "del mismo circuito, no el circuito. Siguen fuera, de mA cada una: los LED "
        "de estado, la polarizacion de los TL431 de D-F6, el MSP430FR2111 con su "
        "TPS709 y R64/D2 desde 24 V, y el consumo propio del LM74502 y del TPS26631",
        "Dentro de cada riel, los fusibles F2..F5, los shunts de 20 mohm de U8, "
        "U13 y U14, los ballast R15..R18, J1 y el cable del Kycon a J1 no son "
        "piezas aparte: la carga se cobra a la tension del convertidor y su I^2 R "
        "va dentro. El total no cambia, solo donde se disipa",
        "Un rendimiento por convertidor, sin curva frente a la carga ni a la "
        f"tension que de verdad les llega ({tension_minima_en_dcdc_v():.1f} a "
        f"{V_LADRILLO * (1 + TOL_LADRILLO):.1f} V)",
        "El cordon con el cobre a 20 C: caliente cae mas y tira mas corriente",
        "La carga de cada convertidor contra su nominal con derating: PS3 lleva "
        f"{FILA_B_A + AUX_A:.2f} A de su 1 A (K7805T-1000R3); el derating vive "
        "en curvas.py y nadie cruza las dos cosas",
        "Solo regimen permanente: ni arranque, ni dv/dt del eFuse, ni transitorios",
    )


def _guarda_balance_energia(p: dict[str, float]) -> None:
    """#338: lo que disipan las piezas y lo que el cordon mete en la caja coinciden.

    Salen de descripciones distintas (ver el docstring del guion): si una pieza
    falta en el inventario, o un convertidor declara una corriente que no es la
    suma de lo que cuelga de el, se separan.
    """
    termico = calor_del_cajon_w(p)
    electrico = potencia_que_entra_w()
    assert abs(termico - electrico) <= 1e-9, (
        f"descuadre de energia (#338): las piezas disipan {termico:.6f} W y el "
        f"cordon mete {electrico:.6f} W en la caja")


def _guarda_ventana_entrada_dcdc(p: dict[str, float]) -> None:
    """D-V2/D-V5: la tension minima tras cordon, conector y eFuse arranca todo."""
    v_llega = tension_minima_en_dcdc_v()
    assert v_llega >= p["v_arranque_dcdc_v"], (
        f"caida excesiva en entrada de 24 V: llegan {v_llega:.2f} V < "
        f"{p['v_arranque_dcdc_v']:.2f} V de arranque")


def _autocomprobacion() -> None:
    """Lo que tiene que seguir siendo verdad, comprobado y no prometido."""
    # 1. #338: el balance cuadra con los datos de verdad, y muerde. Quitarle al
    #    inventario de piezas la Ignd de U1 o de U2 (#343) o la carga del
    #    +5V_AUX lo descuadra contra lo que declaran los convertidores.
    _guarda_balance_energia(dict(P_BASE))
    for clave in ("iq_U1_a", "iq_U2_a", "aux_a"):
        borde_rojo(_guarda_balance_energia, P_BASE, clave, 0.0, P_BASE[clave],
                   "descuadre de energia (#338)")

    # 2. H-CENSO-ETA-DIGITAL (M1): aislar el digital con el minimo garantizado
    #    del URB2405YMD-20WR3 (88 %) sube la perdida respecto al buck (90 %).
    delta_m1 = (entrada_dcdc_w(eta_digital=ETA_DIGITAL_AISLADO)
                - entrada_dcdc_w(eta_digital=ETA_BUCK))
    assert abs(delta_m1 - 0.3655303030303025) < 1e-6, (
        f"H-CENSO-ETA-DIGITAL: incremento inesperado {delta_m1:.6f} W")

    # 3. El ladrillo le pide a la red MAS de lo que entrega, nunca menos.
    assert pedido_a_la_red_w() > salida_ladrillo_w(), "rendimiento >= 1"

    # 4. Todos los ladrillos candidatos aguantan la demanda continua a 45 C.
    for nombre_ladrillo, w_45c in LADRILLOS_45C_W.items():
        assert w_45c >= salida_ladrillo_w(), (
            f"{nombre_ladrillo} da {w_45c:.1f} W a 45 C < {salida_ladrillo_w():.2f} W")

    # 5. La ventana de 24 V cierra con holgura sobre el arranque de los DC-DC.
    _guarda_ventana_entrada_dcdc(dict(P_BASE))
    tope_arranque = borde_rojo(
        _guarda_ventana_entrada_dcdc, P_BASE,
        "v_arranque_dcdc_v", 9.0, 24.0, "caida excesiva en entrada de 24 V")
    assert tope_arranque > 22.0

    # 6. La tension cruda elegida tiene que cerrar la cascada entera.
    for reg in ("U1", "U2"):
        assert margen_cascada_v(reg) > 0, (
            f"{reg} sigue sin margen con {V_CRUDO_CASCADA} V de crudo "
            f"({margen_cascada_v(reg)*1000:+.0f} mV)")
    assert margen_cascada_v("U2", v_nom=16.0) > margen_cascada_v("U2", v_nom=15.0), (
        "subir el crudo no mejora el margen: el modelo esta al reves")

    # 7. Lo declarado no puede quedar por debajo del censo.
    assert censo_optimista_w() < entrada_dcdc_w(), (
        "el censo pide mas que lo declarado: la declaracion no cubre el uso")


def demo() -> int:
    print("La fuente v5: el ladrillo afuera, la conversion adentro\n")

    print("  lado electrico: cada convertidor y lo que declara entregar")
    print(f"    {'riel':<38} {'V':>7} {'A':>7} {'eta':>6} {'sale':>8} {'pierde':>8}")
    for r in rieles():
        w = r["v"] * r["a"]
        print(f"    {r['nombre']:<38} {r['v']:>7.2f} {r['a']:>7.3f} "
              f"{r['eta']:>5.0%} {w:>7.2f} W {w*(1/r['eta']-1):>6.2f} W")
    print(f"    {'-'*38} {'-'*7} {'-'*7} {'-'*6} {'-'*8} {'-'*8}")
    print(f"    {'entregado a las cargas':<38} {'':>7} {'':>7} {'':>6} "
          f"{entregado_w():>7.2f} W")
    print(f"    {'piden los DC-DC a 24 V':<38} {'':>7} {'':>7} {'':>6} "
          f"{entrada_dcdc_w():>7.2f} W")
    w_antes_m1 = entrada_dcdc_w(eta_digital=ETA_BUCK)
    print(f"    (con buck 90 % en el digital, antes de M1, serian {w_antes_m1:.2f} W; "
          f"H-CENSO-ETA-DIGITAL suma +{entrada_dcdc_w() - w_antes_m1:.2f} W con el "
          f"88 % min del URB2405YMD-20WR3; con los tipicos de hoja a 24 V serian "
          f"{entrada_dcdc_tipica_hoja_w():.2f} W)")

    print("\n  lado termico: lo que disipa cada pieza, de abajo arriba (#338)")
    eta = {r["nombre"]: r["eta"] for r in rieles()}
    for nombre, focos in focos_de_calor().items():
        print(f"    {nombre}")
        for pieza, w in focos.items():
            print(f"      {pieza:<46} {w:>7.3f} W")
        print(f"      {'conversion del DC-DC':<46} "
              f"{sum(focos.values()) * (1/eta[nombre] - 1):>7.3f} W")
    print(f"    {'cadena de entrada (Kycon + LM74502 + TPS26631)':<48} "
          f"{perdida_entrada_w():>7.3f} W")
    print(f"    {'total, calor_del_cajon_w()':<48} {calor_del_cajon_w():>7.3f} W")
    print(f"    {'lo que el cordon mete en la caja':<48} {potencia_que_entra_w():>7.3f} W")

    print("\n  el ladrillo y los candidatos a 45 C:")
    print(f"    tension                        {V_LADRILLO:>7.1f} V   (D-V2, firmada; "
          f"{V_LADRILLO_MIN:.1f} V en el borde bajo)")
    print(f"    corriente del cordon           {corriente_del_cordon_a():>7.3f} A   "
          f"(peor caso; a {V_LADRILLO:.0f} V sin caidas serian "
          f"{entrada_dcdc_w() / V_LADRILLO:.3f} A)")
    print(f"    salida del ladrillo            {salida_ladrillo_w():>7.2f} W")
    print(f"    lo que le pide a la red        {pedido_a_la_red_w():>7.2f} W")
    print(f"    se disipa FUERA de la caja     "
          f"{pedido_a_la_red_w() - potencia_que_entra_w():>7.2f} W   (AC-DC y cordon)")
    for nombre_ladrillo, w_45c in LADRILLOS_45C_W.items():
        holgura = w_45c - salida_ladrillo_w()
        print(f"    candidato {nombre_ladrillo:<56} {w_45c:>6.1f} W (holgura {holgura:+6.2f} W)")

    print(f"\n  EL CALOR DEL CAJON = LO QUE EL CORDON METE EN LA CAJA = "
          f"{calor_del_cajon_w():.2f} W")
    print("    Todo lo que baja por el cordon acaba en calor dentro. Lo unico")
    print("    que se queda fuera es la perdida AC-DC del ladrillo y la del cordon.")
    print(f"    La v4 declara {declarado_v4_w():.2f} W: son "
          f"{100*(1-calor_del_cajon_w()/declarado_v4_w()):.0f} % menos.")

    print("\n  y con los CENSOS en vez de las declaraciones:")
    print(f"    fila a 300 mA, cascada a {CASCADA_CENSO_A*1000:.0f} mA sin Ignd, "
          f"+5V_AUX a {AUX_CENSO_A*1000:.0f} mA, digital al tipico")
    print(f"    piden los DC-DC                {censo_optimista_w():>7.2f} W")
    print(f"    lo declarado lo separa en      "
          f"{entrada_dcdc_w()/censo_optimista_w():>7.2f} veces")

    print("\n  EL REGALO: la tension cruda da holgura a U1 y U2 (#343 incluido)")
    print(f"    {'crudo':>7} {'llega':>9} {'margen U1':>11} {'margen U2':>11} "
          f"{'quema U2':>10}")
    nom0, tol0 = mb.V_NOM, mb.TOL_FRAC
    for nom in (15.0, 15.5, 16.0):
        try:
            mb.V_NOM, mb.TOL_FRAC = nom, TOL_CRUDO
            llega = mb.v_entrada_minima_v()
        finally:
            mb.V_NOM, mb.TOL_FRAC = nom0, tol0
        m1 = margen_cascada_v("U1", v_nom=nom) * 1000
        m2 = margen_cascada_v("U2", v_nom=nom) * 1000
        q = quema_pre_regulador_w("U2", v_nom=nom)
        et = "  <- el crudo de la v4 (con D-F9 e Iq=120 mA de #343)" if nom == 15.0 else (
             "  <- D-V3, firmada" if nom == V_CRUDO_CASCADA else "")
        print(f"    {nom:>6.1f} V {llega:>8.3f} V {m1:>+10.0f} {m2:>+10.0f} "
              f"{q:>8.2f} W{et}")
    sube = quema_pre_regulador_w("U2") - quema_pre_regulador_w("U2", v_nom=15.0)
    cruzado = (quema_pre_regulador_w("U2")
               - quema_pre_regulador_w("U2", v_nom=15.0, tol=-TOL_CRUDO))
    print(f"    La columna de la derecha es el precio, y va en el MISMO corner "
          f"que\n    la de al lado no va: subir a 15,5 V cuesta {sube:+.2f} W "
          f"en U2, no el\n    {cruzado:+.2f} que sale de comparar el corner alto "
          f"contra el bajo.")

    print("\n  el cordon, el conector Kycon KPJX-PM-4S/KPPX-4P y el vigilante M5:")
    print(f"    {'calibre':>9} {'ohm/m':>8} {'1 m':>9} {'2 m':>9} {'total 2m+con+M5':>17}")
    for et, ohm in (("18 AWG", 0.0210), ("16 AWG", 0.0132), ("14 AWG", 0.0083)):
        c1 = caida_cordon_v(ohm, 1.0)
        c2 = caida_cordon_v(ohm, 2.0)
        ctot = caida_entrada_completa_v(ohm, 2.0)
        print(f"    {et:>9} {ohm:>8.4f} {c1*1000:>7.0f} mV {c2*1000:>7.0f} mV "
              f"{ctot*1000:>14.0f} mV")
    v_min_dcdc = tension_minima_en_dcdc_v()
    print(f"    Con ladrillo al -5 % ({V_LADRILLO_MIN:.1f} V), cordon 16 AWG "
          f"de 2 m, conector Kycon (30 mohm bucle 2p/polo),\n    LM74502 (15 mohm) "
          f"y TPS26631 (53 mohm), llegan {v_min_dcdc:.2f} V a los DC-DC contra "
          f"{V_ARRANQUE_DCDC_MAX_V:.1f} V max de arranque\n    "
          f"(holgura +{v_min_dcdc - V_ARRANQUE_DCDC_MAX_V:.2f} V).")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}; HUECO: {len(HUECOS)}")
    for e in ESTIMADOS:
        print(f"    ESTIMADO - {e}")
    for h in HUECOS:
        print(f"    HUECO    - {h}")

    print("\n  lo que este guion NO cubre:")
    for n in no_cubre():
        print(f"    - {n}")

    _autocomprobacion()

    if HUECOS:
        print("\nHUECO: " + "; ".join(h.split(":")[0] for h in HUECOS))
        return 2
    print("\nOK: ladrillo_budget.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
