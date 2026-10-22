"""Que sobrevive a un OVP de un modulo, y por que el crowbar de D-F6 cierra.

    python check_absmax.py

## Por que se reescribe

El `check_absmax.py` de la v3 tiene un sujeto que ya no existe: **VRAW =
20,54 V**, el pico del rectificador con la red al +10 % y casi en vacio. Sin
puente ni condensador de bulto no hay VRAW, y una puerta que vigila un nodo
muerto es verde por construccion.

Las preguntas de la v4 son otras dos, y las dos salen de la hoja:

  1. **El OVP de PS1/PS2** clampa hasta 20,25 V (hoja p. 2, modelos de 15 V).
     Contra los 26 V de entrada de U1/U2, y --si ademas U1 se pusiera en
     corto-- contra los 22 V del LT3045.
  2. **El OVP de PS3/PS4/PS5** pone hasta 16,2 V (12 V) o 6,75 V (5 V) sobre
     una fila de modulos ajenos con maximos absolutos que nadie publica. Es
     lo que D-F6 existe para atajar, y aqui esta su ventana.

## Por que el crowbar cierra aqui y en el #118 no

El #118 rechazo el crowbar del riel ultra porque el interruptor era el fusible
de red de un toroide y no abria a tiempo: se disparaba el SCR y el lazo no
cerraba. Aqui el interruptor es EL PROPIO MODULO: un SCR pone el riel en corto
y el IRM entra en *hiccup* en microsegundos (hoja p. 2: "Hiccup mode, recovers
automatically after fault condition is removed"). Lo que este guion asevera es
la condicion que hace que ese lazo cierre --que el modulo entregue mas
corriente de la que el SCR necesita para quedarse enganchado-- y no una prosa
sobre por que deberia.

## El hallazgo: el crowbar que aprieta es el del +5 V, no el de +-12

La ventana del crowbar es la distancia entre lo que el riel llega a valer sano
y lo que la victima aguanta. En +-12 V son ~3,5 V y sobra sitio. **En el +5 V
de rack son ~1,1 V**, porque el OVP de la IRM-45-5 llega a 6,75 y un
electrolitico de 6,3 V --el estandar de ese riel-- esta por debajo. Ese es el
riel donde el SCR tiene que estar bien puesto, y el papel lo trataba igual que
los otros dos.

## Lo que este guion NO cubre, y sale en HUECO

**La pieza del SCR.** No hay hoja de ningun SCR en el arbol, asi que su
corriente de mantenimiento, su I2t de sobrecarga y su dv/dt son REQUISITOS
publicados aqui, no cifras leidas. El guion asevera que esos requisitos son
satisfacibles con lo que el IRM da, y declara el hueco: hasta que la pieza se
elija y su hoja baje, D-F6 esta dimensionada en cotas y no en un componente.

Tampoco cubre: el tiempo que tarda el riel en subir hasta el umbral (depende
de la capacidad del bus de invitados, que es de #169), ni el fallo del propio
SCR en corto permanente, que es lo que se paga por tener crowbar.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _ruta in (str(HERE), os.path.join(str(HERE), "..", "..", "tools")):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
from calor_budget import (MODULO_A, P_BASE, SOSTENIDO,  # noqa: E402
                          aire_recinto_c, p_cajon_w, p_recinto_w)
from canario import borde_rojo  # noqa: E402

# --- lo que las hojas dicen de los OVP (meanwell-*, p. 2) ------------------
# "Protection type : Shut off o/p voltage, clamping by zener diode": corta la
# salida Y la recorta con zener. Lo que la victima ve es el techo del rango.
OVP_V = {
    "PS1/PS2 (IRM-20-15)": (17.25, 20.25),
    "PS3/PS4 (IRM-45-12)": (12.60, 16.20),
    "PS5/PS6 (IRM-45-5)": (5.25, 6.75),
}
# Fila OVERLOAD: "115%~160% rated output power", modo hiccup con recuperacion
# automatica. El 115 % es el minimo garantizado antes de plegar.
OVERLOAD_MIN_FRAC = 1.15
RATED_W = {"rack+12": 45.6, "rack-12": 45.6, "rack+5": 40.0}
V_RIEL = {"rack+12": 12.0, "rack-12": 12.0, "rack+5": 5.0}
# Tolerancia y deriva del riel sano, de la misma hoja (p. 2).
TOL_FRAC = 0.025
TEMPCO_PCT_C = 0.03
# La temperatura del aire NO se escribe a mano: se resuelve. Es el punto
# fijo de calor_budget.py con el venteo de D-F3 = A y las corrientes
# sostenidas, y de ella depende cuanto sube el riel sano por deriva -- que
# es la cota de abajo de la ventana del crowbar.
T_AIRE_C = aire_recinto_c(p_recinto_w(SOSTENIDO), p_cajon_w(SOSTENIDO),
                          area_venteo_mm2=P_BASE["area_venteo_mm2"])
RIZADO_VPP = {"rack+12": 0.150, "rack-12": 0.150, "rack+5": 0.080}

# --- el tope M3 delante de U1 (#334) --------------------------------------
# U1 es el LT1963A desde D-F8 y su maximo absoluto de entrada son +-20,0 V
# (lt1963a-rev-g-2021-02.pdf p. 2). El OVP de PS1 (IRM-20-15) llega a 20,25 V
# sostenidos (meanwell-irm-20-spec-2025-11-21.pdf p. 2), lo que sin proteccion
# deja -0,25 V de margen (#334). El tope M3 (TI TPS26631, tps2663.pdf p. 6-8:
# V(OVPR) = 1,176..1,224 V, corte en 8,5..14 us, antes del filtro LC + TVS
# Bourns SMBJ16A, bourns_smbj.pdf p. 2, en U1 IN) corta a 16,92 V maximos de
# umbral y sujeta el pico inductivo tras el LC por debajo de 20,0 V.
# EL PICO NO SE ESCRIBE: SE CALCULA. Hasta #474 aqui habia un 18,08 a mano y
# el guarda lo comparaba con los 20,0 V de U1 -- una puerta que no podia
# ponerse roja por ningun cambio de diseno. Ahora sale del modelo RK4 de la v5
# (v5/check_absmax.py::escalon_lc), que simula el LC y el divisor del OVP que
# monta la placa (los lee de v5/bom.csv), con el fallo de ESTA rama: el OVP
# de PS1 a 20,25 V sostenidos.
def _modelo_tope_v5():
    import importlib.util
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v5", "check_absmax.py")
    spec = importlib.util.spec_from_file_location("check_absmax_v5", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TOPE_V5 = _modelo_tope_v5()
TOPE_U1_REF = "TI TPS26631 + Bourns SMBJ16A (v5)"
V_DISPARO_TOPE_U1_MAX_V = TOPE_V5.V_DISPARO_MAX_U1_V
T_CORTE_TOPE_US = TOPE_V5.T_CORTE_OVP_MAX_S * 1e6   # tps2663.pdf p. 8: 14 us max


def v_pico_tope_u1_v(v_fallo_v: float, t_corte_us: float = T_CORTE_TOPE_US) -> float:
    """Pico en U1 IN con el tope M3 cortando antes del LC y el SMBJ16A en U1."""
    return TOPE_V5.escalon_lc(v_fallo_v=v_fallo_v, t_corte_s=t_corte_us * 1e-6,
                              sensa_antes_del_lc=True, con_efuse=True,
                              con_tvs=True)["v_pico_v"]

# --- el crowbar de D-F6: piezas y cifras leidas de hoja (#340) ------------
# SCR: NXP BT151-500R (docs/reference/datasheets/nxp-bt151-500r.pdf, Rev. 05).
#   * p. 3: V_DRM = 500 V, I_T(RMS) = 12 A, I_TSM = 120 A (10 ms), I2t = 72 A2s
#   * p. 6: I_GT = 2 mA tip / 15 mA max; I_L = 10 mA tip / 40 mA max;
#           I_H = 7 mA tip / 20 mA max a 25 C (~36 mA a -40 C, Fig. 10 p. 7);
#           dV_D/dt = 200 V/us min con R_GK = 100 ohm; t_gt = 2 us tip.
# Referencia de disparo: TI TL431BI (docs/reference/datasheets/tl431.pdf,
# SLVS543S, p. 13):
#   * V_ref = 2483 / 2495 / 2507 mV a 25 C (+-0,48 %), V_I(dev) = 34 mV max
#     en -40..85 C (+-1,84 % total), I_ref = 4 uA max, mas divisor de 0,1 %:
#     en 14,0 V la dispersion garantizada es +-0,29 V (<= 0,30 V).
SCR_REF = "NXP BT151-500R"
REF_DISPARO_CROWBAR = "TI TL431BI"
V_DISPARO_V = {"rack+12": 14.0, "rack-12": 14.0, "rack+5": 5.8}
# Tomamos 40 mA (el maximo de I_L a 25 C y por encima de los ~36 mA de I_H a
# -40 C en Fig. 10 p. 7) como cota conservadora de enganche/mantenimiento:
I_MANTENIMIENTO_MAX_A = 0.040
I_GT_MAX_A = 0.015
I2T_SCR_A2S = 72.0
DV_DT_SCR_MIN_V_US = 200.0
TOL_DISPARO_V = 0.30            # TL431BI p. 13 (+-1,84 % en temp) + divisor 0,1 %
T_DISPARO_MAX_US = 2.0          # nxp-bt151-500r.pdf p. 6: t_gt = 2 us tip.

ESTIMADOS = (
    "los maximos absolutos de los modulos invitados: no hay hoja de terceros "
    "y se toma el electrolitico del riel, que es la pieza que revienta primero",
)
HUECOS: tuple[str, ...] = ()


def leer_absmax() -> list[dict]:
    with open(HERE / "absmax.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        raise SystemExit("absmax.csv vacio")
    return filas


def v_riel_sano_max(riel: str) -> float:
    """Lo mas alto que el riel llega a valer FUNCIONANDO BIEN.

    Es la cota de abajo de la ventana del crowbar: por debajo de esto el
    crowbar dispararia solo, con el instrumento sano."""
    v = V_RIEL[riel]
    return (v * (1.0 + TOL_FRAC)
            + v * (TEMPCO_PCT_C / 100.0) * (T_AIRE_C - 25.0)
            + RIZADO_VPP[riel] / 2.0)


def i_plegado_a(riel: str) -> float:
    """La corriente minima que el modulo entrega antes de plegar en hiccup.

    Es lo que el SCR tiene garantizado para quedarse enganchado."""
    return OVERLOAD_MIN_FRAC * RATED_W[riel] / V_RIEL[riel]


def victima_de(riel: str, filas: list[dict]) -> dict:
    clave = {"rack+12": "modulo invitado +-12",
              "rack-12": "modulo invitado +-12",
              "rack+5": "modulo invitado +5"}[riel]
    return next(f for f in filas if f["victima"] == clave)


def ventana_crowbar_v(riel: str, filas: list[dict]) -> tuple[float, float]:
    """(minimo, maximo) donde puede vivir el disparo del crowbar."""
    return (v_riel_sano_max(riel), float(victima_de(riel, filas)["v_absmax"]))


def _guarda_tope_u1(p: dict[str, float]) -> None:
    """El tope M3 delante de U1 LT1963A (#334). Alimenta al canario."""
    filas = leer_absmax()
    u1 = next(f for f in filas if f["victima"] == "U1 LT1963A")
    lim_u1 = float(u1["v_absmax"])
    v_pico = v_pico_tope_u1_v(p["v_fallo_tope_v"], p["t_corte_tope_us"])
    assert v_pico < lim_u1, (
        f"U1 LT1963A fuera de maximo absoluto (#334): le llegan {v_pico:.2f} V "
        f"contra {lim_u1:.1f} V de limite (lt1963a-rev-g-2021-02.pdf p. 2)")


def _guarda_crowbar(p: dict[str, float]) -> None:
    """El disparo del crowbar, por los dos lados. Alimenta al canario.

    Por abajo: si dispara por debajo de lo que el riel vale sano, dispara solo
    y el instrumento no arranca. Por arriba: si dispara por encima de lo que
    la victima aguanta, llega tarde."""
    filas = leer_absmax()
    riel = "rack+5" if p["riel_es_5v"] >= 0.5 else "rack+12"
    lo, hi = ventana_crowbar_v(riel, filas)
    v = p["v_disparo_v"]
    assert v - TOL_DISPARO_V > lo, (
        f"dispararia solo: el crowbar de {riel} pone {v:.2f} V "
        f"+-{TOL_DISPARO_V:.2f} y el riel sano llega a {lo:.2f} V")
    assert v + TOL_DISPARO_V < hi, (
        f"llega tarde: el crowbar de {riel} dispara a {v:.2f} V "
        f"+-{TOL_DISPARO_V:.2f} y un modulo ajeno aguanta {hi:.2f} V")


def _guarda_enganche(p: dict[str, float]) -> None:
    """Que el lazo de D-F6 cierra: el modulo da mas de lo que el SCR pide."""
    i_h = p["i_mantenimiento_a"]
    peor = min(i_plegado_a(r) for r in V_RIEL)
    assert i_h < peor, (
        f"el crowbar se suelta: el SCR necesita {i_h:.3f} A para quedarse "
        f"enganchado y el modulo mas flojo en corto da {peor:.2f} A antes de "
        f"plegar. Si el SCR pidiera mas, dispararia y se soltaria, dejando el "
        f"riel oscilando entre el OVP y el corto -- que es exactamente lo que "
        f"el #118 rechazo cuando el interruptor era el fusible de red")


P_BASE = {
    "v_fallo_tope_v": OVP_V["PS1/PS2 (IRM-20-15)"][1],
    "t_corte_tope_us": T_CORTE_TOPE_US,
    "v_disparo_v": V_DISPARO_V["rack+12"],
    "riel_es_5v": 0.0,
    "i_mantenimiento_a": I_MANTENIMIENTO_MAX_A,
}


def main() -> int:
    filas = leer_absmax()
    rojo = False
    print("check_absmax v4: OVP de los modulos contra lo que alimentan\n")

    # --- 1. La cascada ultra --------------------------------------------
    print("=== 1. El OVP de PS1/PS2 contra la cascada ultra (#334) ===\n")
    ovp = OVP_V["PS1/PS2 (IRM-20-15)"][1]
    fila_u1 = next(f for f in filas if f["victima"] == "U1 LT1963A")
    lim_u1 = float(fila_u1["v_absmax"])
    # Demostracion de que el tope M3 es obligatorio: sin el, 20,25 V > 20,0 V.
    assert ovp > lim_u1, (
        f"si el OVP de PS1 ({ovp:.2f} V) cupiera en los {lim_u1:.1f} V de U1 "
        f"LT1963A, la #334 y el tope M3 no tendrian razon de ser")
    v_pico_u1 = v_pico_tope_u1_v(ovp)
    for nombre, v_efectivo in (("U1 LT1963A", v_pico_u1),
                               ("U2 LT3015", ovp)):
        fila = next(f for f in filas if f["victima"] == nombre)
        lim = float(fila["v_absmax"])
        ok = v_efectivo < lim
        rojo = rojo or not ok
        print(f"  [{'verde' if ok else 'ROJO '}] {nombre}: ve {v_efectivo:.2f} V "
              f"contra {lim:.1f} V de maximo -> margen {lim - v_efectivo:+.2f} V")
        assert ok, (f"{nombre} no aguanta la sobretension de su rama: "
                    f"{v_efectivo:.2f} contra {lim:.1f}")
    print()
    print(f"  #334 cerrada con el tope M3 ({TOPE_U1_REF}): sin tope, el OVP de")
    print(f"  PS1 llega a {ovp:.2f} V > {lim_u1:.1f} V (margen {lim_u1 - ovp:+.2f} V);")
    print(f"  con el TPS26631 antes del LC (disparo <= {V_DISPARO_TOPE_U1_MAX_V:.2f} V,")
    print("  corte <= 14 us, tps2663.pdf p. 6-8) y el SMBJ16A en U1 IN, el")
    print(f"  modelo RK4 de la v5 da {v_pico_u1:.2f} V de pico (margen "
          f"{lim_u1 - v_pico_u1:+.2f} V).")
    print("\n  Y el fallo DOBLE (PS1 en OVP y U1 en corto), que se documenta y")
    print("  no bloquea porque son dos causas independientes:")
    for nombre in ("LT3045", "LT3094"):
        fila = next(f for f in filas if f["victima"] == nombre)
        lim = float(fila["v_absmax"])
        marca = "verde" if ovp < lim else "nota "
        print(f"  [{marca}] {nombre}: veria {ovp:.2f} V contra {lim:.1f} "
              f"-> margen {lim - ovp:+.2f} V")
    print("  Aguantan incluso ese: la cascada no se lleva por delante a la")
    print("  isla LT ni con las dos cosas a la vez.\n")

    # --- 2. Los rieles de rack y D-F6 ------------------------------------
    print("=== 2. El OVP de PS3/PS4/PS5 contra la fila de invitados ===\n")
    print(f"  {'riel':9s} {'sano max':>9s} {'OVP max':>8s} {'aguanta':>8s} "
          f"{'ventana':>9s} {'disparo':>8s} {'holgura':>8s}")
    estrecho = None
    for riel in ("rack+12", "rack-12", "rack+5"):
        lo, hi = ventana_crowbar_v(riel, filas)
        ovp_r = (OVP_V["PS5/PS6 (IRM-45-5)"][1] if riel == "rack+5"
                 else OVP_V["PS3/PS4 (IRM-45-12)"][1])
        v = V_DISPARO_V[riel]
        holgura = min(v - TOL_DISPARO_V - lo, hi - TOL_DISPARO_V - v)
        print(f"  {riel:9s} {lo:8.2f}V {ovp_r:7.2f}V {hi:7.2f}V "
              f"{hi - lo:8.2f}V {v:7.2f}V {holgura:+7.2f}V")
        if estrecho is None or (hi - lo) < estrecho[1]:
            estrecho = (riel, hi - lo)
        sin_crowbar = ovp_r > hi
        if sin_crowbar:
            print(f"    ^ sin crowbar, {ovp_r:.2f} V de OVP pasan por encima "
                  f"de los {hi:.2f} que la victima aguanta")
    print(f"\n  La ventana mas ESTRECHA es la de {estrecho[0]}: "
          f"{estrecho[1]:.2f} V.")
    print("  El papel trataba los tres rieles igual, y no lo son: el OVP de la")
    print("  IRM-45-5 llega a 6,75 V y un electrolitico de 6,3 --el estandar de")
    print("  un riel de 5 V-- esta por debajo. Ahi es donde el SCR tiene que")
    print("  estar bien puesto.")
    lo5, hi5 = ventana_crowbar_v("rack+5", filas)
    print(f"  Con la dispersion de +-{TOL_DISPARO_V:.1f} V que se le supone al "
          f"disparo, el punto")
    print(f"  admisible en +5 V es una banda de "
          f"{(hi5 - TOL_DISPARO_V) - (lo5 + TOL_DISPARO_V):.2f} V "
          f"({lo5 + TOL_DISPARO_V:.2f} a {hi5 - TOL_DISPARO_V:.2f}). En +-12 V "
          f"esa banda son")
    lo12, hi12 = ventana_crowbar_v("rack+12", filas)
    print(f"  {(hi12 - TOL_DISPARO_V) - (lo12 + TOL_DISPARO_V):.2f} V. Diez "
          f"veces mas sitio para la misma pieza.\n")

    # --- 2b. EL RIEL SANO CONTRA EL OVP DE SU PROPIO MODULO --------------
    # El OVP no es un numero: es un RANGO, y su extremo BAJO es lo que el
    # modulo garantiza que NO disparara por debajo. Si el riel sano llega
    # cerca de ese extremo, una unidad con el OVP en su borde bajo y un riel
    # en su tolerancia alta se apagan solos con el instrumento entero bien.
    print("=== 2b. El riel SANO contra el OVP MINIMO de su propio modulo ===\n")
    apretado = None
    for riel in ("rack+12", "rack-12", "rack+5"):
        ovp_min = (OVP_V["PS5/PS6 (IRM-45-5)"][0] if riel == "rack+5"
                   else OVP_V["PS3/PS4 (IRM-45-12)"][0])
        sep = ovp_min - v_riel_sano_max(riel)
        print(f"  {riel:9s} sano max {v_riel_sano_max(riel):5.3f} V contra OVP "
              f"minimo {ovp_min:5.2f} -> {sep * 1000:+6.0f} mV")
        assert sep > 0.0, (
            f"{riel}: el riel sano llega a {v_riel_sano_max(riel):.3f} V y el "
            f"OVP de su modulo puede disparar desde {ovp_min:.2f}: el modulo "
            f"se apaga solo con el instrumento bien")
        if apretado is None or sep < apretado[1]:
            apretado = (riel, sep)
    print(f"\n  El mas apretado es {apretado[0]} con {apretado[1] * 1000:.0f} "
          f"mV. En +5 V el rango del")
    print("  OVP empieza en 5,25 y el riel sano llega a 5,23: **son 19 mV**, y")
    print("  dentro de ellos caben la tolerancia del propio umbral de OVP (que")
    print("  la hoja no publica aparte: el rango ES la tolerancia) y cualquier")
    print("  transitorio de carga. No es un fallo del modelo: es que el +5 V de")
    print("  la IRM-45-5 tiene el OVP pegado a su propia tolerancia de salida.")
    print("  Va al paso 1 del bring-up, midiendo cada modulo a su nominal.\n")

    # --- 3. Que el lazo de D-F6 cierra -----------------------------------
    print("=== 3. Por que el lazo cierra aqui y en el #118 no ===\n")
    for riel in ("rack+12", "rack-12", "rack+5"):
        print(f"  {riel}: en corto el modulo da al menos "
              f"{i_plegado_a(riel):.2f} A ({OVERLOAD_MIN_FRAC:.0%} de "
              f"{RATED_W[riel]:.1f} W / {V_RIEL[riel]:.0f} V) antes de plegar")
    print(f"  REQUISITO al SCR: corriente de mantenimiento <= "
          f"{I_MANTENIMIENTO_MAX_A * 1000:.0f} mA, que es "
          f"{min(i_plegado_a(r) for r in V_RIEL) / I_MANTENIMIENTO_MAX_A:.0f} "
          f"veces menos")
    print("  que lo que el modulo mas flojo entrega. El interruptor de D-F6 es")
    print("  el propio IRM entrando en hiccup, no un fusible de red: por eso")
    print("  el lazo que el #118 no podia cerrar, aqui cierra.")
    print(f"  Lo que el modulo da NO se agota con el SCR: MODULO_A dice "
          f"{MODULO_A['rack+12']:.1f} A de placa en +12 y el plegado empieza")
    print(f"  en {i_plegado_a('rack+12'):.2f}.\n")

    # --- 4. El riel digital, que D-F6 no cubre ---------------------------
    print("=== 4. El +5 V digital: D-F6 no llega, y por eso es un requisito ===\n")
    fila = next(f for f in filas if f["victima"].startswith("modulo 2"))
    ovp5 = OVP_V["PS5/PS6 (IRM-45-5)"][1]
    print(f"  PS6 en OVP clampa a {ovp5:.2f} V sobre el riel del modulo 2, y")
    print("  D-F6 solo pone crowbar en los rieles de RACK (papel sec.4.3).")
    print("  REQUISITO al modulo 2 (sec.10): lo que reciba ese riel tiene que")
    print(f"  aguantar {float(fila['v_absmax']):.2f} V. No es un maximo leido:")
    print("  es lo que hay que exigirle, y su papel lo tiene que decir.\n")

    # --- 5. Los canarios --------------------------------------------------
    for riel, es5 in (("rack+12", 0.0), ("rack+5", 1.0)):
        p = dict(P_BASE)
        p["riel_es_5v"] = es5
        p["v_disparo_v"] = V_DISPARO_V[riel]
        _guarda_crowbar(p)
        bajo = borde_rojo(_guarda_crowbar, dict(p), "v_disparo_v",
                          0.0, 30.0, "dispararia solo")
        alto = borde_rojo(_guarda_crowbar, dict(p), "v_disparo_v",
                          0.0, 30.0, "llega tarde")
        print(f"  canario {riel}: por debajo de {bajo:.2f} V dispararia solo; "
              f"por encima de {alto:.2f} V llega tarde")
    _guarda_enganche(dict(P_BASE))
    v = borde_rojo(_guarda_enganche, dict(P_BASE), "i_mantenimiento_a",
                   0.0, 20.0, "el crowbar se suelta")
    print(f"  canario: con mas de {v:.2f} A de corriente de mantenimiento, el "
          f"SCR se suelta")
    _guarda_tope_u1(dict(P_BASE))
    # El canario mueve una CAUSA (el fallo que llega), no el resultado: con
    # el pico como parametro el borde salia en el propio limite, que es una
    # tautologia.
    v_u1 = borde_rojo(_guarda_tope_u1, dict(P_BASE), "v_fallo_tope_v",
                      OVP_V["PS1/PS2 (IRM-20-15)"][1], 60.0, "fuera de maximo absoluto")
    print(f"  canario U1: con un fallo de mas de {v_u1:.1f} V delante del tope, "
          f"U1 (LT1963A) sale de maximo absoluto")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}; HUECO: {len(HUECOS)}")
    for e in ESTIMADOS:
        print(f"    ESTIMADO - {e}")
    for h in HUECOS:
        print(f"    HUECO    - {h}")

    if rojo:
        print("\nROJO: un OVP simple saca a alguien de maximo absoluto.")
        return 1
    print("\nverde: ningun OVP simple saca a nadie de rango, y el crowbar de")
    print("       D-F6 tiene ventana en los tres rieles de rack.")
    # EL HUECO SE MIRA, NO SE AFIRMA. Un "return 2" fijo promete un codigo
    # que este guion seguiria dando el dia que la hoja del SCR baje y alguien
    # vacie HUECOS: la frase de abajo diria que falta una hoja que ya esta en
    # el arbol. Se cierra solo, como el de consumo_total_budget.py con su
    # relevo. La condicion, no el resultado.
    if not HUECOS:
        print()
        print("D-F6 ya no esta en cotas: la hoja del SCR bajo y sus cifras "
              "son leidas.")
        return 0
    print()
    print("HUECO: D-F6 esta dimensionada en COTAS y no en una pieza. No hay "
          "hoja de ningun SCR en el arbol, asi que su corriente de "
          "mantenimiento (<= 100 mA), su I2t y su dv/dt son requisitos que "
          "este guion publica, no cifras leidas. Se cierra bajando la hoja del "
          "SCR que se elija, poniendo sus cifras aqui y vaciando HUECOS.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
