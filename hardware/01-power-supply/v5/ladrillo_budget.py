"""La fuente v5: un ladrillo de catalogo afuera y la conversion adentro.

    python ladrillo_budget.py

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

Para que esa identidad sea una comprobacion fisica y no una tautologia (#338),
este guion calcula los dos lados por caminos independientes:
- `salida_ladrillo_w()` suma la potencia electrica que entra a cada convertidor
  desde el bus de 24 V (`V_riel * I_riel / eta_riel`).
- `calor_del_cajon_w()` suma el calor disipado en cada subsistema fisico dentro
  de la caja: las cargas de la fila B y la pantalla, el cerebro digital, la
  quema en los prerreguladores (`U1`/`U2`), la quema en los LDO ultra
  (`LT3045`/`LT3094`), la carga analogica de +-12 V ultra y la perdida de
  conversion de los DC-DC interiores.

**2. La tension cruda deja de ser un dato de catalogo, y eso da holgura a la
cascada.** El 06-09 se firmo **D-F9** y `U2` paso a LT3015. Con **D-F8** (`U1`
en LT1963A) e `Iq_max = 120 mA` a plena carga sobre temperatura (#343,
`lt1963a-rev-g-2021-02.pdf` p. 5), `U1` a 15,0 V queda en +283 mV y a 15,5 V
sube a +764 mV (+723 mV tras los 41 mV del eFuse `TPS26630` de M3).

**3. M1 y H-CENSO-ETA-DIGITAL cerrados con hoja.** La decision M1 (2026-09-08)
exige aislar el convertidor del +5 V digital. El modulo **Mornsun
URB2405YMD-20WR3** (`mornsun_urb_ymd20wr3.pdf` p. 1) garantiza **88 % minimo**
(90 % tipico) a plena carga con aislamiento de 1500 VDC. Al pasar la rama
digital de `0,90` (buck no aislado) a `0,88` (minimo garantizado aislado), la
perdida interior sube en **+0,37 W** (de 7,99 W a 8,36 W) y la salida pedida al
ladrillo pasa de **64,22 W (2,68 A)** a **64,58 W (2,69 A)**.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Callable

DIR = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(DIR, "..", "v4")
if V4 not in sys.path:
    sys.path.append(V4)

# --- lo que la v4 ya decidio y aqui NO se vuelve a escribir ----------------
# Se importan para que un cambio alli se vea aqui, en vez de quedarse pegado.
from calor_budget import (CAJON_DIGITAL_A, PLACA_A,       # noqa: E402
                          V_RIEL, p_cajon_w, p_recinto_w)

_spec_mb = importlib.util.spec_from_file_location(
    "_v4_margen_budget", os.path.join(V4, "margen_budget.py"))
assert _spec_mb and _spec_mb.loader
mb = importlib.util.module_from_spec(_spec_mb)
_spec_mb.loader.exec_module(mb)

# --- D-B2, firmada el 2026-09-05 -------------------------------------------
FILA_B_A = 0.500          # A/riel declarados en la fila de abajo
# La cascada ultra: D-F1, sin tocar. Su censo real (invitados_budget) son
# 340 + 327 mA, o sea 334 mA/riel: la declaracion es el doble del censo.
CASCADA_A = 0.650
CASCADA_CENSO_A = (0.340 + 0.327) / 2
# El digital: cargas duras del peor caso de la hoja, ya SIN la cadena de LED que
# D1 retiro (ver calor_budget). El tipico son 0,965 A: 3,0 veces menos. #256.
DIGITAL_A = CAJON_DIGITAL_A
DIGITAL_TYP_A = 0.965
# La pantalla de 7": pantalla-motor l.250-256 la manda al presupuesto de la
# fuente "cuando la pieza tenga nombre". Va con retorno dedicado, no por el bus.
PANTALLA_A = 0.550

# --- el ladrillo (D-V2) y los candidatos con hoja --------------------------
V_LADRILLO = 24.0
TOL_LADRILLO = 0.05       # +-5 % ventana de salida estandar en 24 V
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
# Vigilante de entrada M5: TI TPS26630 (tps2663.pdf p. 7: RON max 53 mohm a
# TJ=125 C) + bloqueo de polaridad TI LM74502 (lm74502.pdf p. 1) con MOSFET
# externo de 15 mohm max.
R_ON_EFUSE_ENTRADA_OHM = 0.053
R_ON_POLARIDAD_OHM = 0.015
# UVLO maximo de arranque de los convertidores interiores:
# URB2405YMD-20WR3: 9.0 V max (mornsun_urb_ymd20wr3.pdf p. 2)
# THN 20-2413WI / THN 30-2422WI: 8.8 V max (traco_thn20wi.pdf / thn30wi.pdf p. 1)
# K7805T-1000R3: 8.0 V min de rango operativo (mornsun_k78_t1000r3.pdf p. 1)
V_ARRANQUE_DCDC_MAX_V = 9.0

# --- los convertidores de dentro (M1, H-CENSO-ETA-DIGITAL) -----------------
# Cotas conservadoras de diseno para el presupuesto termico (incluyendo carga
# parcial al 40-50 % en las ramas aisladas de TRACO, cuya hoja solo publica el
# tipico a plena carga) y eficiencias de hoja:
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
    "+5 rack (bus fila B)": 0.88,               # RECOM RPMB5.0-2.0 p. 2 (88% typ)
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
    f"PANTALLA_A={PANTALLA_A}: centro del rango 450-550 mA de pantalla-motor l.250-256",
    f"ETA_BUCK={ETA_BUCK}, ETA_INVERSOR={ETA_INVERSOR}, ETA_AISLADO={ETA_AISLADO}: "
    "cotas conservadoras a carga parcial frente al 88-89 % tipico a plena carga de "
    "THN 30-2422WI, THN 20-2413WI y RPMB5.0-2.0",
    f"TOL_CRUDO={TOL_CRUDO}: +-2,5 % conservador tras recorte Trim (+-1 % base en thn20wi.pdf p. 2)",
    "#256: DIGITAL_A entra con el maximo a TJ=125 C (2,895 A frente a 0,965 A tipicos)",
)

HUECOS: tuple[str, ...] = ()


def rieles(*, eta_digital: float = ETA_DIGITAL_AISLADO) -> list[dict]:
    """Cada convertidor de dentro: que entrega y que pierde.

    El +12 de rack lleva DOS cargas por cables distintos: el bus de la fila de
    abajo y la pantalla con su retorno dedicado. Van juntas en el convertidor y
    separadas en el cableado, que es lo que pide pantalla-motor.
    """
    v_alto = V_CRUDO_CASCADA * (1 + TOL_CRUDO)   # el peor caso PARA EL CALOR
    return [
        {"nombre": "+12 rack (bus fila B + pantalla)", "v": V_RIEL["rack+12"],
         "a": FILA_B_A + PANTALLA_A, "eta": ETA_BUCK,
         "pieza": "TRACO THN 30-2422WI (rama +12 V)"},
        {"nombre": "-12 rack (bus fila B)", "v": V_RIEL["rack-12"],
         "a": FILA_B_A, "eta": ETA_INVERSOR,
         "pieza": "TRACO THN 30-2422WI (rama -12 V)"},
        {"nombre": "+5 rack (bus fila B)", "v": V_RIEL["rack+5"],
         "a": FILA_B_A, "eta": ETA_BUCK,
         "pieza": "RECOM RPMB5.0-2.0 / Mornsun K7805T-1000R3"},
        {"nombre": "+5 digital (4 x N657 + host USB)", "v": 5.0,
         "a": DIGITAL_A, "eta": eta_digital,
         "pieza": "Mornsun URB2405YMD-20WR3 (aislado M1, 88% min)"},
        {"nombre": "crudo +cascada (a U1)", "v": v_alto,
         "a": CASCADA_A, "eta": ETA_AISLADO,
         "pieza": "TRACO THN 20-2413WI #1 (Trim +15,5 V)"},
        {"nombre": "crudo -cascada (a U2)", "v": v_alto,
         "a": CASCADA_A, "eta": ETA_AISLADO,
         "pieza": "TRACO THN 20-2413WI #2 (invertido, Trim -15,5 V)"},
    ]


def entregado_w() -> float:
    """Potencia electrica entregada a la salida de los convertidores DC-DC."""
    return sum(r["v"] * r["a"] for r in rieles())


def perdida_dcdc_w(*, eta_digital: float = ETA_DIGITAL_AISLADO) -> float:
    """Calor disipado en los convertidores DC-DC interiores."""
    return sum(r["v"] * r["a"] * (1.0 / r["eta"] - 1.0)
               for r in rieles(eta_digital=eta_digital))


def salida_ladrillo_w(*, eta_digital: float = ETA_DIGITAL_AISLADO) -> float:
    """Lado electrico (cordon de 24 V): suma de entradas de cada convertidor.

    Se calcula desde la frontera electrica de 24 V (`P_in = V_out * I_out / eta`),
    sin llamar a `calor_del_cajon_w()`.
    """
    return sum((r["v"] * r["a"]) / r["eta"]
               for r in rieles(eta_digital=eta_digital))


def salida_ladrillo_tipica_hoja_w() -> float:
    """Lo que pide el conjunto usando las eficiencias tipicas de hoja a 24 V."""
    return sum((r["v"] * r["a"]) / ETA_HOJA_TIPICA[r["nombre"]]
               for r in rieles())


def quema_pre_regulador_w(reg: str, *, v_nom: float = V_CRUDO_CASCADA,
                          tol: float = TOL_CRUDO) -> float:
    """Lo que U1 o U2 disipa: la caida por la corriente, en el corner ALTO."""
    return ((v_nom * (1 + tol)) - SETPOINT_V[reg]) * CASCADA_A


def quema_ldo_ultra_w(reg: str) -> float:
    """Lo que el LT3045 (tras U1) o el LT3094 (tras U2) disipa hacia +-12 V."""
    return (SETPOINT_V[reg] - V_ULTRA_SALIDA_V) * CASCADA_A


def calor_fila_y_pantalla_w() -> float:
    """Calor disipado en los modulos de la fila B y en la pantalla de 7\"."""
    return (
        V_RIEL["rack+12"] * (FILA_B_A + PANTALLA_A)
        + V_RIEL["rack-12"] * FILA_B_A
        + V_RIEL["rack+5"] * FILA_B_A
    )


def calor_digital_w() -> float:
    """Calor disipado en el cerebro digital (4 x STM32N657 + host USB)."""
    return 5.0 * DIGITAL_A


def calor_cascada_w(*, v_nom: float = V_CRUDO_CASCADA,
                    tol: float = TOL_CRUDO) -> float:
    """Calor total del dominio analogico ultra: U1/U2 + LT3045/LT3094 + carga."""
    total = 0.0
    for reg in ("U1", "U2"):
        total += quema_pre_regulador_w(reg, v_nom=v_nom, tol=tol)
        total += quema_ldo_ultra_w(reg)
        total += V_ULTRA_SALIDA_V * CASCADA_A
    return total


def calor_cargas_w(*, v_nom: float = V_CRUDO_CASCADA,
                   tol: float = TOL_CRUDO) -> float:
    """Suma de todos los disipadores finales de calor despues de los DC-DC."""
    return (
        calor_fila_y_pantalla_w()
        + calor_digital_w()
        + calor_cascada_w(v_nom=v_nom, tol=tol)
    )


def calor_del_cajon_w(*, eta_digital: float = ETA_DIGITAL_AISLADO) -> float:
    """Lado termico (#338): suma independiente de los focos de calor del cajon.

    No llama a `salida_ladrillo_w()`. Suma:
      1. calor en fila B + pantalla (`calor_fila_y_pantalla_w()`)
      2. calor en el cerebro digital (`calor_digital_w()`)
      3. calor en prerreguladores U1/U2 + LDOs LT3045/LT3094 + carga ultra
         (`calor_cascada_w()`)
      4. calor de conversion en los DC-DC interiores (`perdida_dcdc_w()`)
    """
    return calor_cargas_w() + perdida_dcdc_w(eta_digital=eta_digital)


def pedido_a_la_red_w() -> float:
    """Lo que el ladrillo pide a la red. La diferencia se disipa FUERA."""
    return salida_ladrillo_w() / ETA_LADRILLO


def corriente_del_cordon_a() -> float:
    return salida_ladrillo_w() / V_LADRILLO


def caida_cordon_v(ohm_por_m: float, largo_m: float) -> float:
    """Ida y vuelta. El cordon es de DOS hilos: no hay rieles en el."""
    return 2.0 * ohm_por_m * largo_m * corriente_del_cordon_a()


def caida_entrada_completa_v(ohm_por_m: float = 0.0132,
                             largo_m: float = 2.0) -> float:
    """Caida total desde el ladrillo hasta la entrada de los DC-DC (D-V5, M5).

    Suma: cordon (2 hilos) + conector Kycon KPJX-PM-4S/KPPX-4P (2 pines/polo) +
    MOSFET de polaridad LM74502 + eFuse de entrada TPS26630.
    """
    i_cordon = corriente_del_cordon_a()
    r_serie = R_BUCLE_CONECTOR_OHM + R_ON_POLARIDAD_OHM + R_ON_EFUSE_ENTRADA_OHM
    return caida_cordon_v(ohm_por_m, largo_m) + i_cordon * r_serie


def tension_minima_en_dcdc_v(ohm_por_m: float = 0.0132,
                             largo_m: float = 2.0) -> float:
    """Tension minima que llega a la entrada de los convertidores DC-DC."""
    v_ladrillo_min = V_LADRILLO * (1.0 - TOL_LADRILLO)
    return v_ladrillo_min - caida_entrada_completa_v(ohm_por_m, largo_m)


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
    """El mismo cajon con los censos en vez de las declaraciones."""
    v_alto = V_CRUDO_CASCADA * (1 + TOL_CRUDO)
    filas = [
        (V_RIEL["rack+12"], 0.300 + PANTALLA_A, ETA_BUCK),
        (V_RIEL["rack-12"], 0.300, ETA_INVERSOR),
        (V_RIEL["rack+5"], 0.300, ETA_BUCK),
        (5.0, DIGITAL_TYP_A, ETA_DIGITAL_AISLADO),
        (v_alto, CASCADA_CENSO_A, ETA_AISLADO),
        (v_alto, CASCADA_CENSO_A, ETA_AISLADO),
    ]
    return sum(v * a / eta for v, a, eta in filas)


P_BASE: dict[str, float] = {
    "fuga_no_contada_w": 0.0,
    "carga_fantasma_w": 0.0,
    "v_arranque_dcdc_v": V_ARRANQUE_DCDC_MAX_V,
}


def _guarda_balance_energia(p: dict[str, float]) -> None:
    """#338: el calor sumado por subsistemas y la salida del ladrillo coinciden.

    Si alguien anade una carga al cajon sin pasarla por un convertidor
    (`carga_fantasma_w`) o una potencia que baja por el cordon sin sumarse al
    calor (`fuga_no_contada_w`), los dos lados se separan y la guarda salta.
    """
    lado_termico = calor_del_cajon_w() + p["carga_fantasma_w"]
    lado_electrico = salida_ladrillo_w() + p["fuga_no_contada_w"]
    assert abs(lado_termico - lado_electrico) <= 1e-9, (
        f"descuadre de energia (#338): calor_del_cajon={lado_termico:.6f} W != "
        f"salida_ladrillo={lado_electrico:.6f} W")


def _guarda_ventana_entrada_dcdc(p: dict[str, float]) -> None:
    """D-V2/D-V5: la tension minima tras cordon, conector y eFuse arranca todo."""
    v_llega = tension_minima_en_dcdc_v()
    assert v_llega >= p["v_arranque_dcdc_v"], (
        f"caida excesiva en entrada de 24 V: llegan {v_llega:.2f} V < "
        f"{p['v_arranque_dcdc_v']:.2f} V de arranque")


def borde_rojo(guarda: Callable[[dict[str, float]], None],
               base: dict[str, float], clave: str,
               lo: float, hi: float, Subcadena: str) -> float:
    """Biseccion hasta la frontera exacta donde `guarda` salta con `Subcadena`."""
    def pasa(v: float) -> bool:
        q = dict(base)
        q[clave] = v
        try:
            guarda(q)
            return True
        except AssertionError as e:
            assert Subcadena in str(e), (
                f"En {clave}={v}: esperaba {Subcadena!r} y salio {str(e)!r}")
            return False

    p_lo, p_hi = pasa(lo), pasa(hi)
    assert p_lo != p_hi, (
        f"{clave} no cruza el rojo entre {lo} y {hi} "
        f"(pasa(lo)={p_lo}, pasa(hi)={p_hi})")
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if pasa(m) == p_lo:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def _autocomprobacion() -> None:
    """Lo que tiene que seguir siendo verdad, comprobado y no prometido."""
    # 1. #338: identidad termico-electrica no tautologica + prueba de mutacion.
    assert calor_del_cajon_w is not salida_ladrillo_w
    _guarda_balance_energia(dict(P_BASE))
    for clave in ("carga_fantasma_w", "fuga_no_contada_w"):
        q = dict(P_BASE)
        q[clave] = 0.001
        try:
            _guarda_balance_energia(q)
        except AssertionError as exc:
            assert "descuadre de energia (#338)" in str(exc)
        else:
            raise AssertionError(f"#338: mutacion {clave}=+1 mW no detectada")

    # 2. H-CENSO-ETA-DIGITAL (M1): aislar el digital con el minimo garantizado
    #    del URB2405YMD-20WR3 (88 %) sube la perdida respecto al buck (90 %).
    delta_m1 = salida_ladrillo_w(eta_digital=ETA_DIGITAL_AISLADO) - salida_ladrillo_w(eta_digital=ETA_BUCK)
    assert abs(delta_m1 - 0.3655303030303025) < 1e-6, (
        f"H-CENSO-ETA-DIGITAL: incremento inesperado {delta_m1:.6f} W")

    # 3. El ladrillo le pide a la red MAS de lo que entrega, nunca menos.
    assert pedido_a_la_red_w() > salida_ladrillo_w(), "rendimiento >= 1"

    # 4. Todos los ladrillos candidatos aguantan la demanda continua a 45 C.
    i_cordon = corriente_del_cordon_a()
    p_total_cordon = salida_ladrillo_w() + i_cordon * caida_entrada_completa_v()
    for nombre_ladrillo, w_45c in LADRILLOS_45C_W.items():
        assert w_45c >= p_total_cordon, (
            f"{nombre_ladrillo} da {w_45c:.1f} W a 45 C < {p_total_cordon:.2f} W")

    # 5. La ventana de 24 V cierra con holgura sobre el arranque de los DC-DC.
    _guarda_ventana_entrada_dcdc(dict(P_BASE))
    tope_arranque = borde_rojo(
        _guarda_ventana_entrada_dcdc, dict(P_BASE),
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
    assert censo_optimista_w() < salida_ladrillo_w(), (
        "el censo pide mas que lo declarado: la declaracion no cubre el uso")


def demo() -> int:
    print("La fuente v5: el ladrillo afuera, la conversion adentro\n")

    print("  los rieles de dentro, cada uno con su convertidor:")
    print(f"    {'riel':<38} {'V':>7} {'A':>7} {'eta':>6} {'sale':>8} {'pierde':>8}")
    for r in rieles():
        w = r["v"] * r["a"]
        print(f"    {r['nombre']:<38} {r['v']:>7.2f} {r['a']:>7.3f} "
              f"{r['eta']:>5.0%} {w:>7.2f} W {w*(1/r['eta']-1):>6.2f} W")
    print(f"    {'-'*38} {'-'*7} {'-'*7} {'-'*6} {'-'*8} {'-'*8}")
    print(f"    {'entregado a las cargas':<38} {'':>7} {'':>7} {'':>6} "
          f"{entregado_w():>7.2f} W")
    print(f"    {'perdido convirtiendo, DENTRO (M1)':<38} {'':>7} {'':>7} {'':>6} "
          f"{'':>8} {perdida_dcdc_w():>6.2f} W")
    w_antes_m1 = salida_ladrillo_w(eta_digital=ETA_BUCK)
    p_antes_m1 = perdida_dcdc_w(eta_digital=ETA_BUCK)
    print(f"    (antes de M1 con buck 90 % en digital: {p_antes_m1:.2f} W perdidos, "
          f"{w_antes_m1:.2f} W de salida; H-CENSO-ETA-DIGITAL suma "
          f"+{salida_ladrillo_w() - w_antes_m1:.2f} W con el 88 % min del "
          f"URB2405YMD-20WR3; con las eficiencias tipicas de hoja a 24 V "
          f"serian {salida_ladrillo_tipica_hoja_w():.2f} W)")

    print("\n  desglose independiente del calor dentro del cajon (#338):")
    print(f"    fila B (+12, -12, +5) + pantalla 7\"    {calor_fila_y_pantalla_w():>7.2f} W")
    print(f"    cerebro digital (+5 V, 4xN657 + USB)   {calor_digital_w():>7.2f} W")
    print(f"    cascada ultra (U1/U2 + LT + carga)     {calor_cascada_w():>7.2f} W")
    print(f"    perdida de conversion DC-DC interior   {perdida_dcdc_w():>7.2f} W")
    print(f"    total lado termico (calor_del_cajon_w) {calor_del_cajon_w():>7.2f} W")
    print(f"    total lado electrico (salida_ladrillo) {salida_ladrillo_w():>7.2f} W")

    print("\n  el ladrillo y los candidatos a 45 C:")
    print(f"    tension                        {V_LADRILLO:>7.1f} V   (D-V2, firmada)")
    print(f"    salida a convertidores         {salida_ladrillo_w():>7.2f} W")
    print(f"    corriente del cordon           {corriente_del_cordon_a():>7.2f} A")
    print(f"    lo que le pide a la red        {pedido_a_la_red_w():>7.2f} W")
    print(f"    se disipa FUERA de la caja     "
          f"{pedido_a_la_red_w()-salida_ladrillo_w():>7.2f} W")
    for nombre_ladrillo, w_45c in LADRILLOS_45C_W.items():
        holgura = w_45c - salida_ladrillo_w()
        print(f"    candidato {nombre_ladrillo:<56} {w_45c:>6.1f} W (holgura +{holgura:>5.2f} W)")

    print(f"\n  EL CALOR DEL CAJON = LA SALIDA DEL LADRILLO = "
          f"{calor_del_cajon_w():.2f} W")
    print("    Todo lo que baja por el cordon acaba en calor dentro. Lo unico")
    print("    que se queda fuera es la perdida AC-DC del ladrillo.")
    print(f"    La v4 declara {declarado_v4_w():.2f} W: son "
          f"{100*(1-calor_del_cajon_w()/declarado_v4_w()):.0f} % menos.")

    print("\n  y con los CENSOS en vez de las declaraciones:")
    print(f"    fila a 300 mA, cascada a {CASCADA_CENSO_A*1000:.0f} mA, digital al tipico")
    print(f"    calor del cajon                {censo_optimista_w():>7.2f} W")
    print(f"    lo declarado lo separa en      "
          f"{salida_ladrillo_w()/censo_optimista_w():>7.2f} veces")

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
    print(f"    La columna de la derecha es el precio, y va en el MISMO corner "
          f"que\n    la de al lado no va: subir a 15,5 V cuesta "
          f"{quema_pre_regulador_w('U2') - quema_pre_regulador_w('U2', v_nom=15.0):+.2f} W "
          f"en U2, no el\n    +0,98 que sale de comparar el corner alto contra el bajo.")

    print("\n  el cordon, el conector Kycon KPJX-PM-4S/KPPX-4P y el vigilante M5:")
    print(f"    {'calibre':>9} {'ohm/m':>8} {'1 m':>9} {'2 m':>9} {'total 2m+con+M5':>17}")
    for et, ohm in (("18 AWG", 0.0210), ("16 AWG", 0.0132), ("14 AWG", 0.0083)):
        c1 = caida_cordon_v(ohm, 1.0)
        c2 = caida_cordon_v(ohm, 2.0)
        ctot = caida_entrada_completa_v(ohm, 2.0)
        print(f"    {et:>9} {ohm:>8.4f} {c1*1000:>7.0f} mV {c2*1000:>7.0f} mV "
              f"{ctot*1000:>14.0f} mV")
    v_min_dcdc = tension_minima_en_dcdc_v(0.0132, 2.0)
    print(f"    Con ladrillo al -5 % ({V_LADRILLO*(1-TOL_LADRILLO):.1f} V), cordon 16 AWG "
          f"de 2 m, conector Kycon (30 mohm bucle 2p/polo),\n    LM74502 (15 mohm) "
          f"y TPS26630 (53 mohm), llegan {v_min_dcdc:.2f} V a los DC-DC contra "
          f"{V_ARRANQUE_DCDC_MAX_V:.1f} V max de arranque\n    "
          f"(holgura +{v_min_dcdc - V_ARRANQUE_DCDC_MAX_V:.2f} V).")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}; HUECO: {len(HUECOS)}")
    for e in ESTIMADOS:
        print(f"    ESTIMADO - {e}")
    for h in HUECOS:
        print(f"    HUECO    - {h}")

    _autocomprobacion()

    if not HUECOS:
        print("\nOK: ladrillo_budget.py (#338 y H-CENSO-ETA-DIGITAL cerrados con hoja)")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
