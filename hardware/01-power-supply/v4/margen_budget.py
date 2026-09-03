"""Lo que le llega a U1/U2, contra lo que necesitan para regular.

    python margen_budget.py          (sale con codigo 2: HUECO declarado)

## Por que existe, y a quien sustituye

Es el sustituto de `valle_budget.py` de la v3, que muere con el rectificador
(Tarea 12). La pregunta es la misma --le llega a U1/U2 bastante tension para
que regulen?-- y el problema ya no tiene 100 Hz que integrar: sin puente ni
condensador de bulto no hay valle. Lo que hay es una CADENA DE CONTINUA.

## EL HALLAZGO: al papel le faltan dos terminos, y con ellos el margen es
## NEGATIVO

El papel sec.4.2 escribe la cadena asi y le salen +0,30 V:

    15 V - 2,5 % de tolerancia            = 14,625
         - 0,03 %/C x 50 K de deriva      = 14,40
    setpoint de U1 + dropout max a 1 A    = 13,1 + 1,0 = 14,1
    margen                                = +0,30 V

Ese +0,30 es el margen de una placa **cuyo setpoint cae exactamente en 13,1 V**.
No hay ninguna que lo haga. Los dos terminos que faltan:

  1. **La tolerancia del setpoint.** El propio bring-up de la v3 acepta TP7 en
     13,1 +-0,3 V. En el borde alto de esa ventana U1 pide 0,3 V mas de
     entrada, y el margen se acaba. La v3 podia permitirselo porque venia de
     un VRAW de 20,5 V; la v4 viene de 15 V y no.
  2. **De donde sale esa ventana**: de la REFERENCIA del propio pre-regulador.
     LM2941 (hoja p. 5): Vref 1,237-1,313 V a 25 C y 1,211-1,339 sobre
     temperatura, sobre 1,275 tipicos. O sea +-3,0 % de dispersion inicial y
     +-2,0 % mas de deriva. Con un divisor fijo el setpoint de 13,1 V sale en
     cualquier punto de +-5 % = +-0,65 V. Aunque se AJUSTE placa a placa en el
     bring-up, la deriva termica sigue ahi: +-2,0 % = +-0,27 V para U1, y
     +-3,0 % = +-0,38 V para U2 (LM2991, Vref -1,186/-1,234 a 25 C y
     -1,15/-1,27 sobre temperatura).

Con el setpoint ajustado --el mejor caso posible-- los margenes salen
NEGATIVOS en los dos rieles. El guion publica cuanto, y sale en HUECO.

**Esto no se arregla bajando el aserto.** Es una decision de arquitectura de la
cascada y le toca a Samuel; el guion la deja escrita con sus numeros al final,
para que la decision se tome sobre cifras y no sobre una impresion.

## El otro hallazgo, mas pequeno: la deriva se usa fuera de su rango

La hoja publica TEMP. COEFFICIENT +-0,03 %/C **(0 ~ 50 C)**. El punto de diseno
tiene el aire del recinto a ~69 C: veinte grados por encima de donde la hoja
deja de hablar. El papel ya extrapolaba ("tempco, 25 -> 75 C") sin decir que
extrapolaba. Aqui se extrapola igual --no hay otra cifra-- pero se declara, se
cuenta como ESTIMADO y lleva canario.

## Los dos lados de la puerta

Por abajo manda el dropout; por arriba, el maximo absoluto de entrada de U1/U2
(26 V continuos, hojas p. 4-5). En marcha normal el maximo ni se acerca --15,7
contra 26-- y ese lado pasa holgado. El caso que si aprieta por arriba es el
OVP del propio IRM, y lo lleva `check_absmax.py` (Tarea 12), que es su dueno.

## Lo que este guion NO cubre

  * El transitorio de arranque y el microcorte. Los IRM tienen setup de 1000 ms
    tipico sin maximo y hold-up de 40 ms, y durante esas ventanas la tension no
    esta en un punto de operacion. Es de `secuencia_budget.py` (D-F4).
  * El dropout GARANTIZADO a 650 mA. La hoja solo lo garantiza a 1 A y a
    100 mA; interpolar entre dos garantias no da una garantia. El veredicto usa
    el de 1 A --que es peor y por lo tanto valido-- y se imprime el tipico de
    la curva al lado, que NO decide.
  * Donde cae en frecuencia el rizado del IRM. La hoja da 200 mVp-p a 20 MHz de
    ancho de banda y no publica su reparto, asi que el veredicto supone la
    colocacion PEOR: todo por debajo del codo del LC, o sea sin filtrar. Se
    imprime tambien lo que quedaria si fuera todo de 65 kHz.
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
for _ruta in (DIR, os.path.join(DIR, "..", "..", "tools"),
              os.path.join(DIR, "..", "..", "03-vco")):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
from calor_budget import (P_BASE, SOSTENIDO, aire_recinto_c,  # noqa: E402
                          p_cajon_w, p_recinto_w)
from canario import borde_rojo  # noqa: E402
from consumo_total_budget import RIEL_MA  # noqa: E402
from rizado_budget import (DCR_OHM, F_CONMUTACION_HZ,  # noqa: E402
                           R_FERRITA_DC_OHM, RIZADO_IRM_VPP, h_lc)

# --- lo que entrega el modulo (IRM-20-15, hoja p. 2) ----------------------
V_NOM = 15.0             # fila DC VOLTAGE, columna IRM-20-15
# fila VOLTAGE TOLERANCE. Note.3 de la hoja: "Tolerance : includes set up
# tolerance, line regulation and load regulation." O SEA QUE LINE Y LOAD
# REGULATION NO SE SUMAN APARTE: ya estan dentro de este 2,5 %. Sumarlas
# seria contar tres veces lo mismo, que es como se infla un peor caso hasta
# que deja de ser creible.
TOL_FRAC = 0.025
# fila TEMP. COEFFICIENT: "+-0.03%/C (0 ~ 50C)". El parentesis es el rango en
# el que la hoja lo garantiza, y el punto de diseno esta FUERA.
TEMPCO_PCT_C = 0.03
T_REF_TEMPCO_C = 25.0    # Note.1: todo medido a 230 Vac, carga nominal, 25 C
T_TOPE_HOJA_C = 50.0     # hasta aqui la hoja garantiza el coeficiente
RIZADO_VPP = RIZADO_IRM_VPP   # fila RIPPLE & NOISE (max.), Note.2, 20 MHz
# El IRM-20 NO tiene ajuste de tension de salida: la p. 2 solo trae VOLTAGE
# RANGE en el bloque de ENTRADA (85~305 Vac). Los 15 V son los que son.
HAY_AJUSTE_DE_SALIDA = False

# --- lo que necesitan los pre-reguladores ---------------------------------
# Setpoints de la cascada, iguales que en la v3: check_bringup.py de la v3,
# TP7 = +13,1 V y TP8 = -12,9 V. El 13,1 no puede bajar: el headroom del
# LT3045 es 13,1 - 12,0 = 1,1 V nominal (v2 sec.1.5.1, papel sec.4.2).
V_SET = {"U1": 13.1, "U2": -12.9}
# La ventana con la que el bring-up de la v3 acepta esos setpoints.
TOL_SET_V3_V = 0.3
# LA REFERENCIA DE CADA PRE-REGULADOR, que es de donde sale esa ventana.
#   LM2941 SNVS770I p. 5: 1,275 V tipicos; 1,237-1,313 a 25 C;
#                         1,211-1,339 sobre el rango de temperatura
#   LM2991 SNVS099I p. 5: -1,210 tipicos; -1,186/-1,234 a 25 C;
#                         -1,15/-1,27 sobre temperatura
VREF = {"U1": {"typ": 1.275, "25c": (1.237, 1.313), "temp": (1.211, 1.339)},
        "U2": {"typ": 1.210, "25c": (1.186, 1.234), "temp": (1.150, 1.270)}}
# Dropout GARANTIZADO a 1 A sobre el rango de temperatura de operacion:
#   LM2941 p. 5: "Dropout voltage | IOUT = 1 A | | 0.5 | 1 | V"
#   LM2991 p. 5: 0,8 V max a TJ = 25 C, y 1 V sobre temperatura
V_DROPOUT_MAX_1A = {"U1": 1.0, "U2": 1.0}
# El TIPICO leido en la curva de cada hoja a 650 mA. NO decide: se imprime.
#   LM2941 p. 7 ~0,32 V; LM2991 p. 6 ~0,42 V
V_DROPOUT_TIP_650MA = {"U1": 0.32, "U2": 0.42}
# Maximo absoluto de entrada (LM2941 p. 5, LM2991 p. 4) y el umbral al que el
# LM2941 se apaga solo por sobretension (p. 10).
V_ABSMAX_ENTRADA = 26.0
V_OVSD_U1 = 30.0

# --- la corriente real de la cascada --------------------------------------
# 650 mA/riel es lo que la PCB de la cascada rutea y lo que vigila
# consumo_total_budget.py; se importa, no se copia. Encima, el consumo propio
# del pre-regulador a plena carga (LM2941 p. 5: 60 mA max sobre temperatura).
IQ_U1_MAX_A = 0.060
I_CASCADA_A = RIEL_MA / 1000.0 + IQ_U1_MAX_A
I_PLACA_PS1_A = 1.4      # hoja p. 2, RATED CURRENT del IRM-20-15

# --- la resistencia serie que se le puso delante --------------------------
# Se IMPORTA de rizado_budget.py: son las mismas piezas. Si alli se cambia el
# LC o la perla, aqui cambia el margen sin que nadie tenga que acordarse.
R_SERIE_OHM = DCR_OHM + R_FERRITA_DC_OHM

# --- requisito de estabilidad de U1, de su propia hoja --------------------
# LM2941 SNVS770I p. 12, sec.8.1: "The output capacitor, COUT, must have a
# capacitance value of at least 22 uF with an equivalent series resistance
# (ESR) of at least 100 mOhm, but no more than 1 Ohm."
#
# Es un REQUISITO DE LAZO, no una recomendacion, y es la trampa clasica: un
# ceramico X7R moderno de 22 uF tiene 5 mOhm de ESR y deja al LM2941 fuera de
# su ventana de estabilidad.
COUT_U1_MIN_F = 22e-6
ESR_COUT_U1_VENTANA_OHM = (0.100, 1.0)
COUT_U1_F = 47e-6            # DECLARADO: con margen sobre el minimo
ESR_COUT_U1_OHM = 0.30       # DECLARADO: electrolitico, dentro de la ventana

ESTIMADOS = (
    f"la deriva termica se evalua por encima de los {T_TOPE_HOJA_C:.0f} C "
    f"hasta donde la hoja la garantiza (0 ~ {T_TOPE_HOJA_C:.0f} C)",
    f"ESR declarada del COUT de U1 ({ESR_COUT_U1_OHM} ohm): de catalogo, sin "
    f"hoja de la pieza concreta",
    "el rizado se cuenta SIN filtrar porque la hoja no publica donde cae en "
    "frecuencia; si fuera todo de 65 kHz el LC lo dejaria en microvoltios",
)


def t_aire_diseno_c() -> float:
    """La temperatura del aire del recinto en el punto de diseno.

    No es 25 C ni es un supuesto: es el punto fijo que resuelve
    calor_budget.py con el venteo de D-F3 = A y las corrientes sostenidas."""
    return aire_recinto_c(p_recinto_w(SOSTENIDO), p_cajon_w(SOSTENIDO),
                          area_venteo_mm2=P_BASE["area_venteo_mm2"])


def tol_setpoint_v(reg: str, *, ajustado: bool = True) -> float:
    """Cuanto se puede ir el setpoint de su valor nominal, en voltios.

    `ajustado=True` es el mejor caso posible: la placa se lleva a su setpoint
    en el bring-up y solo queda la DERIVA de la referencia con la
    temperatura, que es la diferencia entre la ventana de 25 C y la de todo
    el rango. `ajustado=False` es un divisor fijo sin ajustar, donde entra la
    dispersion inicial entera."""
    v = VREF[reg]
    typ = v["typ"]
    if ajustado:
        frac = max((v["temp"][1] - v["25c"][1]) / typ,
                   (v["25c"][0] - v["temp"][0]) / typ)
    else:
        frac = max((v["temp"][1] - typ) / typ, (typ - v["temp"][0]) / typ)
    return abs(V_SET[reg]) * frac


def deriva_tempco_v(t_c: float, tempco_pct_c: float = TEMPCO_PCT_C) -> float:
    """Voltios que se mueve la salida del IRM por deriva termica.

    Lineal desde los 25 C de la condicion de medida. Por encima de 50 C la
    hoja no garantiza el coeficiente: esto es una EXTRAPOLACION declarada."""
    return V_NOM * (tempco_pct_c / 100.0) * abs(t_c - T_REF_TEMPCO_C)


def rizado_en_u1_vpp(*, filtrado: bool = False) -> float:
    """El rizado que ve la entrada del pre-regulador.

    Sin filtrar es el peor caso de colocacion en frecuencia; filtrado es lo
    que quedaria si todo estuviera en la fundamental de 65 kHz."""
    if not filtrado:
        return RIZADO_VPP
    return RIZADO_VPP * h_lc(F_CONMUTACION_HZ)


def v_entrada_minima_v(*, t_c: float | None = None,
                       tempco_pct_c: float = TEMPCO_PCT_C,
                       r_serie_ohm: float = R_SERIE_OHM,
                       i_a: float = I_CASCADA_A,
                       filtrado: bool = False) -> float:
    """El peor caso apilado de lo que le llega a un pre-regulador."""
    t = t_aire_diseno_c() if t_c is None else t_c
    return (V_NOM * (1.0 - TOL_FRAC)
            - deriva_tempco_v(t, tempco_pct_c)
            - rizado_en_u1_vpp(filtrado=filtrado) / 2.0
            - i_a * r_serie_ohm)


def v_entrada_maxima_v(*, t_c: float | None = None,
                       tempco_pct_c: float = TEMPCO_PCT_C) -> float:
    """El otro lado: en vacio, a tolerancia alta y con la cresta del rizado.

    Sin corriente no hay caida en el DCR, asi que ese termino desaparece: el
    peor caso por arriba es justo el que no lleva carga."""
    t = t_aire_diseno_c() if t_c is None else t_c
    return (V_NOM * (1.0 + TOL_FRAC)
            + deriva_tempco_v(t, tempco_pct_c)
            + RIZADO_VPP / 2.0)


def v_necesaria_v(reg: str, *, tol_set: float | None = None) -> float:
    """Lo que el pre-regulador necesita en su entrada para seguir regulando."""
    t = tol_setpoint_v(reg) if tol_set is None else tol_set
    return abs(V_SET[reg]) + t + V_DROPOUT_MAX_1A[reg]


def margen_v(reg: str, *, tol_set: float | None = None, **kw) -> float:
    return v_entrada_minima_v(**kw) - v_necesaria_v(reg, tol_set=tol_set)


def tol_set_admisible_v(reg: str, **kw) -> float:
    """La ventana de setpoint mas ancha que todavia deja regular a `reg`.

    Es LA cifra que este presupuesto le entrega a la tanda B y al bring-up."""
    return (v_entrada_minima_v(**kw) - abs(V_SET[reg])
            - V_DROPOUT_MAX_1A[reg])


def _guarda_margen(p: dict[str, float]) -> None:
    """La cadena de continua contra el dropout; su texto alimenta al canario.

    LOS DOS LADOS: por abajo el dropout, por arriba el maximo absoluto."""
    # El lado de ARRIBA va primero a proposito. Si fuera al reves, el aserto
    # de abajo saltaria antes en cualquier barrido y el canario del maximo
    # absoluto no encontraria nunca su borde: un canario que no muerde por su
    # texto no vigila nada.
    v_max = v_entrada_maxima_v(tempco_pct_c=p["tempco_pct_c"])
    assert v_max <= V_ABSMAX_ENTRADA, (
        f"maximo absoluto: en vacio y a tolerancia alta llegan {v_max:.2f} V "
        f"contra los {V_ABSMAX_ENTRADA:.1f} de U1/U2")
    v_min = v_entrada_minima_v(tempco_pct_c=p["tempco_pct_c"],
                               r_serie_ohm=p["r_serie_ohm"],
                               i_a=p["i_cascada_a"])
    for reg in V_SET:
        necesita = v_necesaria_v(reg, tol_set=p["tol_set_v"])
        assert v_min >= necesita, (
            f"{reg} deja de regular: le llegan {v_min:.3f} V en el peor caso "
            f"y necesita {necesita:.3f} (setpoint {abs(V_SET[reg]):.1f} + "
            f"{p['tol_set_v']:.3f} de ventana de setpoint + "
            f"{V_DROPOUT_MAX_1A[reg]:.1f} de dropout garantizado). Por debajo "
            f"el pre-regulador deja de regular y el ruido del IRM pasa entero "
            f"a la isla LT")


P_BASE_MARGEN = {
    "tempco_pct_c": TEMPCO_PCT_C,
    "r_serie_ohm": R_SERIE_OHM,
    "i_cascada_a": I_CASCADA_A,
    "tol_set_v": 0.0,        # el supuesto del papel: setpoint exacto
}


def _autocomprobacion() -> None:
    t = t_aire_diseno_c()

    # 1. El lado de ARRIBA de la puerta, que si pasa y hay que aseverarlo.
    assert v_entrada_maxima_v() <= V_ABSMAX_ENTRADA, (
        f"en vacio y a tolerancia alta llegan {v_entrada_maxima_v():.2f} V "
        f"contra los {V_ABSMAX_ENTRADA:.1f} de maximo absoluto")
    assert v_entrada_maxima_v() < V_OVSD_U1, (
        f"el LM2941 se apaga solo por encima de {V_OVSD_U1:.0f} V (hoja p. 10) "
        f"y en marcha normal llegan {v_entrada_maxima_v():.2f}")

    # 2. El modelo reproduce la cuenta del papel sec.4.2 en SU escenario:
    #    setpoint exacto, sin filtro, a 75 C. Si no cayera cerca, la
    #    discrepancia seria del modelo y no un hallazgo.
    papel = (v_entrada_minima_v(t_c=75.0, r_serie_ohm=0.0, i_a=0.0)
             + RIZADO_VPP / 2.0)
    assert abs(papel - 14.40) < 0.03, (
        f"el papel sec.4.2 publica 14,40 V antes del rizado y este modelo da "
        f"{papel:.3f} en su mismo escenario: la discrepancia no seria un "
        f"hallazgo, seria un error de este guion")
    assert abs((papel - (13.1 + 1.0)) - 0.30) < 0.03, (
        f"el papel publica +0,30 V de margen con el setpoint exacto y este "
        f"modelo da {papel - 14.1:+.3f}")

    # 3. Que el guion mida a la temperatura del recinto y no a 25 C, y que la
    #    deriva tenga el signo bueno.
    assert t > T_TOPE_HOJA_C, (
        f"el punto de diseno da {t:.1f} C de aire. Por debajo de "
        f"{T_TOPE_HOJA_C:.0f} la hoja cubriria la deriva y este guion no "
        f"tendria que extrapolar: sobraria media advertencia del docstring")
    assert (margen_v("U1", t_c=T_REF_TEMPCO_C) > margen_v("U1")), (
        "el margen a 25 C tiene que ser MAYOR que a la temperatura del "
        "recinto: si no, la deriva esta con el signo cambiado")

    # 4. Que la ventana de setpoint de la v3 no es un capricho: sale de la
    #    referencia del pre-regulador y es del mismo orden.
    for reg in V_SET:
        sin_ajustar = tol_setpoint_v(reg, ajustado=False)
        ajustado = tol_setpoint_v(reg)
        assert ajustado < sin_ajustar, (
            f"{reg}: ajustar la placa tiene que estrechar la ventana "
            f"({ajustado:.3f} contra {sin_ajustar:.3f})")
        assert sin_ajustar > TOL_SET_V3_V, (
            f"{reg}: con divisor fijo la referencia da +-{sin_ajustar:.3f} V "
            f"de setpoint, y el bring-up de la v3 acepta +-{TOL_SET_V3_V:.1f}: "
            f"si cupiera sin ajustar, esa ventana no diria nada")

    # 5. El requisito de estabilidad de U1, de su propia hoja.
    lo, hi = ESR_COUT_U1_VENTANA_OHM
    assert COUT_U1_F >= COUT_U1_MIN_F, (
        f"COUT de U1 son {COUT_U1_F * 1e6:.0f} uF y la hoja exige al menos "
        f"{COUT_U1_MIN_F * 1e6:.0f}")
    assert lo <= ESR_COUT_U1_OHM <= hi, (
        f"la ESR declarada del COUT de U1 ({ESR_COUT_U1_OHM} ohm) esta fuera "
        f"de la ventana {lo}-{hi} que la hoja exige (p. 12, sec.8.1). Es "
        f"requisito de estabilidad del lazo, no una recomendacion: un "
        f"ceramico X7R de 22 uF tiene 5 mohm y lo hace oscilar")

    # 6. Los canarios. El de tol_set_v es EL numero de esta tarea: la ventana
    #    de setpoint mas ancha que todavia deja regular.
    v = borde_rojo(_guarda_margen, dict(P_BASE_MARGEN), "tol_set_v",
                   0.0, 5.0, "deja de regular")
    w = borde_rojo(_guarda_margen, dict(P_BASE_MARGEN), "r_serie_ohm",
                   0.0, 5.0, "deja de regular")
    x = borde_rojo(_guarda_margen, dict(P_BASE_MARGEN), "tempco_pct_c",
                   0.0, 1.0, "deja de regular")
    y = borde_rojo(_guarda_margen, dict(P_BASE_MARGEN), "tempco_pct_c",
                   0.0, 20.0, "maximo absoluto")
    print(f"  canario: con el setpoint mas de {v * 1000:.0f} mV por encima de "
          f"su nominal, no regula")
    print(f"  canario: con mas de {w:.3f} ohm de serie (LC + perla), no regula")
    print(f"  canario: con mas de {x:.4f} %/C de deriva del IRM, no regula "
          f"({x / TEMPCO_PCT_C:.1f} veces la publicada)")
    print(f"  canario: con mas de {y:.1f} %/C se pasaria del maximo absoluto")
    peor = min(tol_set_admisible_v(reg) for reg in V_SET)
    assert abs(v - peor) < 0.005, (
        f"el canario encuentra el borde en {v:.4f} V y la cuenta directa da "
        f"{peor:.4f}: la guarda y el modelo no miden lo mismo")


def demo() -> int:
    t = t_aire_diseno_c()
    print("margen_budget: lo que le llega a U1/U2 contra su dropout\n")
    print(f"  temperatura del aire del recinto: {t:.2f} C "
          f"(calor_budget.py, punto fijo con D-F3 = A)")
    print(f"  corriente de la cascada: {I_CASCADA_A * 1000:.0f} mA "
          f"({RIEL_MA:.0f} de riel + {IQ_U1_MAX_A * 1000:.0f} de U1), sobre "
          f"{I_PLACA_PS1_A:.1f} A de placa de PS1")
    print(f"  resistencia serie: {R_SERIE_OHM * 1000:.0f} mohm "
          f"({DCR_OHM * 1000:.0f} del LC + {R_FERRITA_DC_OHM * 1000:.0f} de la "
          f"perla, importados de rizado_budget.py)")

    print("\n  la cadena, termino a termino:")
    print(f"    {V_NOM:.3f} V nominales                     (hoja p. 2; "
          f"sin ajuste de salida)")
    print(f"   -{V_NOM * TOL_FRAC:.3f}   tolerancia {TOL_FRAC:.1%}              "
          f"(incluye line y load, Note.3)")
    print(f"   -{deriva_tempco_v(t):.3f}   deriva {TEMPCO_PCT_C}%/C x "
          f"{t - T_REF_TEMPCO_C:.1f} K   (EXTRAPOLADA por encima de "
          f"{T_TOPE_HOJA_C:.0f} C)")
    print(f"   -{RIZADO_VPP / 2:.3f}   medio rizado                 "
          f"(sin filtrar: peor colocacion)")
    print(f"   -{I_CASCADA_A * R_SERIE_OHM:.3f}   {I_CASCADA_A * 1000:.0f} mA x "
          f"{R_SERIE_OHM * 1000:.0f} mohm         (LC + perla)")
    print(f"    {v_entrada_minima_v():.3f} V le llegan a U1/U2 en el peor caso")
    print(f"    ({v_entrada_minima_v(filtrado=True):.3f} si todo el rizado "
          f"fuera de 65 kHz y lo filtrara el LC)")

    print(f"\n  {'reg':4s} {'setpoint':>9s} {'ventana':>8s} {'dropout':>8s} "
          f"{'necesita':>9s} {'llega':>7s} {'margen':>8s}")
    deficit = {}
    for reg in V_SET:
        m = margen_v(reg)
        deficit[reg] = m
        print(f"  {reg:4s} {abs(V_SET[reg]):8.2f}V "
              f"{tol_setpoint_v(reg):+7.3f}V {V_DROPOUT_MAX_1A[reg]:7.2f}V "
              f"{v_necesaria_v(reg):8.3f}V {v_entrada_minima_v():6.3f}V "
              f"{m * 1000:+7.0f}mV")
    print("  (la ventana es la DERIVA de la referencia del pre-regulador con")
    print("   la placa YA AJUSTADA en el bring-up: el mejor caso posible. Sin")
    print("   ajustar, con divisor fijo, son "
          f"{tol_setpoint_v('U1', ajustado=False):.3f} V en U1 y "
          f"{tol_setpoint_v('U2', ajustado=False):.3f} en U2.)")

    print("\n  con el dropout TIPICO de la curva a 650 mA (que no es una "
          "garantia y no decide):")
    for reg in V_SET:
        m_tip = (v_entrada_minima_v() - abs(V_SET[reg])
                 - tol_setpoint_v(reg) - V_DROPOUT_TIP_650MA[reg])
        print(f"    {reg}: {m_tip * 1000:+.0f} mV con "
              f"{V_DROPOUT_TIP_650MA[reg]:.2f} V de dropout")

    print(f"\n  por arriba: {v_entrada_maxima_v():.2f} V en vacio y a "
          f"tolerancia alta, contra {V_ABSMAX_ENTRADA:.0f} de maximo")
    print(f"  absoluto y {V_OVSD_U1:.0f} de apagado por sobretension del "
          f"LM2941: ese lado pasa holgado. El")
    print("  caso que si aprieta por arriba es el OVP del IRM, y es de")
    print("  check_absmax.py.")

    print(f"\n  requisito de la hoja de U1 (p. 12): COUT >= "
          f"{COUT_U1_MIN_F * 1e6:.0f} uF con ESR entre "
          f"{ESR_COUT_U1_VENTANA_OHM[0]} y {ESR_COUT_U1_VENTANA_OHM[1]} ohm.")
    print(f"  DECLARADO: {COUT_U1_F * 1e6:.0f} uF con {ESR_COUT_U1_OHM} ohm. "
          f"NO es un ceramico: un X7R de")
    print("  22 uF tiene 5 mohm y deja el lazo fuera de su ventana.")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}")
    for e in ESTIMADOS:
        print(f"    - {e}")

    _autocomprobacion()

    peor_reg = min(deficit, key=lambda r: deficit[r])
    if deficit[peor_reg] > 0.0:
        print(f"\nOK: margen_budget.py (el peor es {peor_reg} con "
              f"{deficit[peor_reg] * 1000:+.0f} mV)")
        return 0

    admisible = min(tol_set_admisible_v(reg) for reg in V_SET)
    print()
    print("=" * 72)
    print("La cadena NO cierra, y no es un fallo de este guion:")
    for reg in V_SET:
        print(f"  {reg}: {deficit[reg] * 1000:+.0f} mV de margen "
              f"(necesita {v_necesaria_v(reg):.3f} V, le llegan "
              f"{v_entrada_minima_v():.3f})")
    print("  La ventana de setpoint mas ancha que dejaria regular a los dos")
    print(f"  son +-{admisible * 1000:.0f} mV. La deriva de la referencia del "
          f"pre-regulador,")
    print(f"  con la placa YA AJUSTADA, son +-{tol_setpoint_v('U1') * 1000:.0f}"
          f" mV en U1 y +-{tol_setpoint_v('U2') * 1000:.0f} en U2.")
    print()
    print("  Lo que se puede mover, con su precio, para que Samuel decida:")
    coste = (24.0 - abs(V_SET["U1"])) * I_CASCADA_A * 2
    hoy = (V_NOM - abs(V_SET["U1"])) * I_CASCADA_A * 2
    print("   a) PS1/PS2 a IRM-20-24 en vez de -15: sobra margen, y U1+U2")
    print(f"      pasan de disipar {hoy:.1f} W a {coste:.1f} W dentro del "
          f"recinto")
    print(f"      (+{coste - hoy:.1f} W sobre los 27,5 de sec.6: mueve "
          f"calor_budget.py y el venteo).")
    print("   b) Otro pre-regulador con referencia mejor y menos dropout. El")
    print("      margen se lo comen la deriva de Vref (+-2 a 3 %) y el "
          "dropout")
    print("      garantizado de 1,0 V a 1 A, que son los dos del LM2941/91.")
    print("   c) Bajar el setpoint de 13,1 V. PROHIBIDO por v2 sec.1.5.1: el")
    print("      headroom del LT3045 son 1,1 V y no puede bajar.")
    print("   d) Aceptar el tipico en vez del garantizado. Es lo que hace un")
    print("      catalogo, no un presupuesto.")
    print("=" * 72)
    print()
    print("HUECO: al riel ultra le faltan "
          f"{-deficit[peor_reg] * 1000:.0f} mV de margen de entrada en su peor "
          "caso. El papel sec.4.2 publica +0,30 V porque cuenta el setpoint "
          "exacto; con la deriva de la referencia del pre-regulador el margen "
          "es negativo. Es una decision de arquitectura de la cascada, no un "
          "aserto que se baje: hasta que se tome, este guion sale en codigo 2.")
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
