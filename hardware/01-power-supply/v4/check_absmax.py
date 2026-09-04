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

# --- el crowbar de D-F6: lo que se declara y lo que se exige --------------
# El disparo que el papel sec.4.3 propone para +-12 ("un SCR a ~14 V"), y el
# del +5 que el papel no daba y sale de la ventana de abajo.
V_DISPARO_V = {"rack+12": 14.0, "rack-12": 14.0, "rack+5": 5.8}
# REQUISITOS al SCR, publicados aqui porque no hay hoja de ninguno todavia:
I_MANTENIMIENTO_MAX_A = 0.100   # corriente de mantenimiento MAXIMA admisible
TOL_DISPARO_V = 0.4             # cuanto se puede ir el disparo de su nominal
                                # (referencia + dispersion del SCR), ESTIMADO
T_DISPARO_MAX_US = 10.0         # ESTIMADO: por encima de esto el riel sube
                                # mientras el SCR decide

ESTIMADOS = (
    "los maximos absolutos de los modulos invitados: no hay hoja de terceros "
    "y se toma el electrolitico del riel, que es la pieza que revienta primero",
    f"TOL_DISPARO_V={TOL_DISPARO_V}: dispersion del disparo del crowbar, sin "
    f"pieza elegida",
    f"T_DISPARO_MAX_US={T_DISPARO_MAX_US}: tiempo de disparo, sin pieza",
)
HUECOS = (
    "la pieza del SCR: sin hoja en el arbol, su corriente de mantenimiento, "
    "su I2t y su dv/dt son requisitos publicados y no cifras leidas",
)


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
        f"+-{TOL_DISPARO_V:.1f} y el riel sano llega a {lo:.2f} V")
    assert v + TOL_DISPARO_V < hi, (
        f"llega tarde: el crowbar de {riel} dispara a {v:.2f} V "
        f"+-{TOL_DISPARO_V:.1f} y un modulo ajeno aguanta {hi:.2f} V")


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
    "v_disparo_v": V_DISPARO_V["rack+12"],
    "riel_es_5v": 0.0,
    "i_mantenimiento_a": I_MANTENIMIENTO_MAX_A,
}


def main() -> int:
    filas = leer_absmax()
    rojo = False
    print("check_absmax v4: OVP de los modulos contra lo que alimentan\n")

    # --- 1. La cascada ultra --------------------------------------------
    print("=== 1. El OVP de PS1/PS2 contra la cascada ultra ===\n")
    ovp = OVP_V["PS1/PS2 (IRM-20-15)"][1]
    for nombre, riel in (("U1 LM2941", "+15 crudo"), ("U2 LM2991", "-15 crudo")):
        fila = next(f for f in filas if f["victima"] == nombre)
        lim = float(fila["v_absmax"])
        ok = ovp < lim
        rojo = rojo or not ok
        print(f"  [{'verde' if ok else 'ROJO '}] {nombre}: ve {ovp:.2f} V de "
              f"OVP contra {lim:.1f} de maximo -> margen {lim - ovp:+.2f} V")
        assert ok, (f"{nombre} no aguanta el OVP de su propio modulo: "
                    f"{ovp:.2f} contra {lim:.1f}")
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
    print()
    print("HUECO: D-F6 esta dimensionada en COTAS y no en una pieza. No hay "
          "hoja de ningun SCR en el arbol, asi que su corriente de "
          "mantenimiento (<= 100 mA), su I2t y su dv/dt son requisitos que "
          "este guion publica, no cifras leidas. Se cierra bajando la hoja del "
          "SCR que se elija y volviendo a correr.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
