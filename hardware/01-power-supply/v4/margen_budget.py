"""Lo que le llega a U1/U2, contra lo que necesitan para regular.

    python margen_budget.py          (sale con codigo 2: HUECO declarado)

## Por que existe, y a quien sustituye

Es el sustituto de `valle_budget.py` de la v3, que muere con el rectificador
(Tarea 12). La pregunta es la misma --le llega a U1/U2 bastante tension para
que regulen?-- y el problema ya no tiene 100 Hz que integrar: sin puente ni
condensador de bulto no hay valle. Lo que hay es una CADENA DE CONTINUA.

## EL HALLAZGO: al papel le faltan dos terminos, y con ellos NO QUEDA MARGEN

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

Con lo que la hoja GARANTIZA --la Vref de la unidad en todo su rango de
temperatura, sobre un divisor fijo disenado con la tipica-- el margen sale
**-388 mV en `U1` y -170 en `U2`**.

Y si se ajusta placa a placa **y ademas** se supone que la unidad conserva su
sitio dentro de la ventana al calentarse --cosa que la hoja NO promete, porque
da las dos ventanas como filas independientes-- lo mejor que puede pasar son
**+2,8 mV**. Ese 2,8 hay que leerlo contra otra cosa que este guion tambien
calcula: **la incertidumbre de su propio modelo son 127 mV**, que es lo que se
mueve la cadena si los dos ESTIMADO --la deriva termica extrapolada por encima
de los 50 C que la hoja garantiza, y la resistencia serie de dos piezas sin
elegir-- se van un 50 %. Un margen mas pequeno que la barra de error de su
propio modelo no es un margen, y ese es el aserto que decide el veredicto.

O sea que por los dos caminos, el garantizado y el optimista, la respuesta es
la misma: **no hay margen**. Y es la misma doctrina que este guion aplica al
dropout, donde usa el garantizado a 1 A y no el tipico de la curva.

**Esto no se arregla bajando el aserto.** Es una decision de arquitectura de la
cascada y le toca a Samuel; el guion la deja escrita con sus numeros al final,
para que la decision se tome sobre cifras y no sobre una impresion.

### Y una coherencia que la primera version de este guion no tenia

La primera version restaba los 200 mVp-p ENTEROS del rizado en la entrada de
`U1` **y a la vez** restaba la caida de continua en el DCR de ese mismo LC: le
cobraba al filtro su perdida y le negaba su trabajo, en el mismo nodo. Con esa
incoherencia el margen salia -97 mV en vez de +2,9, o sea que el titular
colgaba de ella. El LC esta entre el IRM y `U1`, asi que lo que `U1` ve es el
rizado FILTRADO: 1,2 mVp-p a 65 kHz.

Lo que el LC NO quita --rizado por debajo de su codo de 4,9 kHz-- queda como
`RIZADO_LF_VPP`, parametro con canario en vez de suposicion enterrada. La hoja
no publica el reparto en frecuencia; lo poco que se sabe apunta a cero, porque
line y load regulation estan DENTRO de la tolerancia de +-2,5 % por su Note.3 y
esa ya se resta entera. **Bastan 5,8 mVp-p ahi para acabar con el margen**, y
la hoja no dice si los hay: eso es parte del hueco.

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

import math
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
for _ruta in (DIR, os.path.join(DIR, "..", "..", "tools")):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
# hardware/03-vco va POR DETRAS, con append y no con insert(0): alli vive otro
# check_bringup.py y de aqui solo hace falta consumo_total_budget. Con insert(0)
# el directorio del VCO quedaba delante del propio, y "import margen_budget;
# import check_bringup" cargaba el del VCO en silencio -- sin ImportError y con
# otras predicciones.
_VCO = os.path.join(DIR, "..", "..", "03-vco")
if _VCO not in sys.path:
    sys.path.append(_VCO)
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
# Lo que el LC NO quita: rizado por debajo de su codo de 4,9 kHz. La hoja da
# los 200 mVp-p a 20 MHz de ancho de banda y NO publica como se reparten en
# frecuencia. Lo que se sabe apunta a cero: line regulation (+-0,3 %) y load
# regulation (+-0,5 %) estan DENTRO de la tolerancia de +-2,5 % por la Note.3
# de la hoja, y esa ya se resta entera. Queda como PARAMETRO CON CANARIO --no
# como suposicion enterrada-- porque el margen de este riel es tan fino que
# unos pocos milivoltios aqui lo deciden.
RIZADO_LF_VPP = 0.0
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
#   LT1963A Rev G p. 5, "ADJ Pin Voltage (Notas 4, 5)": 1,210 V tipicos;
#                       1,192-1,228 a 25 C; 1,174-1,246 sobre temperatura
#   LM2991 SNVS099I p. 5: -1,210 tipicos; -1,186/-1,234 a 25 C;
#                         -1,15/-1,27 sobre temperatura
#
# U1 ERA UN LM2941 (1,211-1,339 sobre temperatura, 0,658 V de ventana sobre el
# setpoint) y con el la cadena salia a -388 mV: sin margen. Samuel firmo el
# cambio el 2026-09-04, con la tabla del bloque de enmiendas del papel delante.
# La ventana baja a 0,390 V y el margen pasa a +330 mV.
VREF = {"U1": {"typ": 1.210, "25c": (1.192, 1.228), "temp": (1.174, 1.246)},
        "U2": {"typ": 1.210, "25c": (1.186, 1.234), "temp": (1.150, 1.270)}}
# Dropout GARANTIZADO sobre el rango de temperatura, con LA CORRIENTE A LA QUE
# LA HOJA LO GARANTIZA -- que no es la nuestra en ninguno de los dos casos:
#   LT1963A Rev G p. 5: "Dropout Voltage ... ILOAD = 1.5A ... 0.34 0.45 0.55"
#   LM2991 SNVS099I p. 5: 0,8 V max a TJ = 25 C, y 1 V sobre temperatura a 1 A
#
# NINGUNA DE LAS DOS PUBLICA UN MAXIMO A LOS 710 mA REALES de la cascada, asi
# que se toma la cota de la corriente MAYOR. Es pesimista a proposito y por
# igual para los dos: el LT1963A salta de 500 mA (0,35 V) a 1,5 A (0,55) y
# entre medias no hay nada garantizado.
V_DROPOUT_MAX = {"U1": 0.55, "U2": 1.0}
I_DROPOUT_GARANTIZADO_A = {"U1": 1.5, "U2": 1.0}
# El TIPICO de tabla mas cercano por debajo. NO decide: se imprime.
#   LT1963A p. 5 a 500 mA: 0,19 V; LM2991 p. 6 ~0,42 V a 650 mA
V_DROPOUT_TIP = {"U1": 0.19, "U2": 0.42}
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
# LT1963A Rev G p. 14, "Output Capacitors and Stability": "In all cases, a
# minimum of 10uF is required while the maximum ESR allowable is 3 Ohm."
#
# ESTA VENTANA NO ES LA DEL LM2941, Y LA DIFERENCIA ES LA MITAD DE LA HISTORIA.
# El LM2941 exigia ESR de AL MENOS 100 mohm (p. 12, sec.8.1): un ceramico X7R
# moderno de 22 uF tiene 5 mohm y lo hacia oscilar. El LT1963A NO tiene cota
# inferior --acepta ceramico-- y sube el techo a 3 ohm. La cota de abajo
# desaparece porque desaparecio la pieza que la pedia, no porque se relaje nada.
COUT_U1_MIN_F = 10e-6
ESR_COUT_U1_VENTANA_OHM = (0.0, 3.0)
COUT_U1_F = 47e-6            # DECLARADO: se queda el de la v3, y sobra
ESR_COUT_U1_OHM = 0.30       # DECLARADO: electrolitico, dentro de la ventana

ESTIMADOS = (
    f"la deriva termica se evalua por encima de los {T_TOPE_HOJA_C:.0f} C "
    f"hasta donde la hoja la garantiza (0 ~ {T_TOPE_HOJA_C:.0f} C)",
    f"ESR declarada del COUT de U1 ({ESR_COUT_U1_OHM} ohm): de catalogo, sin "
    f"hoja de la pieza concreta",
    "RIZADO_LF_VPP=0: la hoja no publica donde cae en frecuencia su rizado, y "
    "el LC solo quita lo que esta por encima de su codo de 4,9 kHz",
)


def t_aire_diseno_c() -> float:
    """La temperatura del aire del recinto en el punto de diseno.

    No es 25 C ni es un supuesto: es el punto fijo que resuelve
    calor_budget.py con el venteo de D-F3 = A y las corrientes sostenidas."""
    return aire_recinto_c(p_recinto_w(SOSTENIDO), p_cajon_w(SOSTENIDO),
                          area_venteo_mm2=P_BASE["area_venteo_mm2"])


def tol_setpoint_v(reg: str, *, ajustado: bool = False) -> float:
    """Cuanto se puede ir el setpoint de su valor nominal, en voltios.

    POR DEFECTO, LO GARANTIZADO. Con un divisor fijo disenado sobre la Vref
    tipica, el setpoint cae donde caiga la Vref de esa unidad EN TODO SU RANGO
    DE TEMPERATURA: la hoja publica esa ventana entera y no promete nada mas.
    Es la misma doctrina que este guion aplica al dropout --el garantizado, no
    el de la curva tipica-- y da +-5,0 % en `U1`.

    `ajustado=True` es el mejor caso posible Y NO ESTA GARANTIZADO: supone que
    la placa se lleva a su setpoint en el bring-up y que la unidad conserva su
    sitio DENTRO de la ventana al calentarse, con lo que solo queda la deriva
    --la diferencia entre la ventana de 25 C y la de todo el rango, +-2,0 %--.
    La hoja da las dos ventanas como filas independientes y no dice que una
    unidad del borde bajo a 25 C no pueda estar en el alto a 85. Se calcula y
    se imprime para ver cuanto compraria ajustar, y no decide."""
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


def rizado_en_u1_vpp(*, filtrado: bool = True,
                     lf_vpp: float = RIZADO_LF_VPP) -> float:
    """El rizado que ve la entrada del pre-regulador.

    EL LC ESTA ENTRE EL IRM Y U1, asi que lo que U1 ve es el rizado FILTRADO.
    La primera version de este guion restaba los 200 mVp-p enteros aqui y a la
    vez restaba la caida de continua en el DCR de ese mismo LC: le cobraba al
    filtro su perdida y le negaba su trabajo, en el mismo nodo. Con eso el
    margen salia -97 mV y sin eso +3, o sea que el titular de todo el
    presupuesto colgaba de una incoherencia.

    Lo que queda declarado es la parte que el LC de verdad NO quita: el rizado
    por debajo de su codo de 4,9 kHz. La hoja no publica el reparto en
    frecuencia, y lo poco que se sabe apunta a que ahi no hay casi nada --
    line y load regulation estan DENTRO de la tolerancia de +-2,5 % por su
    Note.3, y ya se restan--. Se deja como parametro con canario en vez de
    como suposicion enterrada: ver RIZADO_LF_VPP."""
    if not filtrado:
        return RIZADO_VPP
    return RIZADO_VPP * h_lc(F_CONMUTACION_HZ) + lf_vpp


def v_entrada_minima_v(*, t_c: float | None = None,
                       tempco_pct_c: float = TEMPCO_PCT_C,
                       r_serie_ohm: float = R_SERIE_OHM,
                       i_a: float = I_CASCADA_A,
                       filtrado: bool = True,
                       lf_vpp: float = RIZADO_LF_VPP) -> float:
    """El peor caso apilado de lo que le llega a un pre-regulador."""
    t = t_aire_diseno_c() if t_c is None else t_c
    return (V_NOM * (1.0 - TOL_FRAC)
            - deriva_tempco_v(t, tempco_pct_c)
            - rizado_en_u1_vpp(filtrado=filtrado, lf_vpp=lf_vpp) / 2.0
            - i_a * r_serie_ohm)


def incertidumbre_estimados_v(*, factor: float = 1.5) -> float:
    """Cuanto se mueve la cadena si los ESTIMADO se van un `factor`.

    DERIVADA, no elegida: es la barra de error del propio modelo. Los dos
    terminos que no salen de una hoja son la deriva termica --extrapolada por
    encima de los 50 C hasta donde la hoja la garantiza-- y la resistencia
    serie del LC y la perla, que son piezas sin elegir. Sirve para el unico
    veredicto honesto que este guion puede dar: un margen mas pequeno que la
    barra de error de su propio modelo no es un margen."""
    base = v_entrada_minima_v()
    peor = v_entrada_minima_v(tempco_pct_c=TEMPCO_PCT_C * factor,
                              r_serie_ohm=R_SERIE_OHM * factor)
    return base - peor


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
    return abs(V_SET[reg]) + t + V_DROPOUT_MAX[reg]


def margen_v(reg: str, *, tol_set: float | None = None, **kw) -> float:
    return v_entrada_minima_v(**kw) - v_necesaria_v(reg, tol_set=tol_set)


def tol_set_admisible_v(reg: str, **kw) -> float:
    """La ventana de setpoint mas ancha que todavia deja regular a `reg`.

    Es LA cifra que este presupuesto le entrega a la tanda B y al bring-up."""
    return (v_entrada_minima_v(**kw) - abs(V_SET[reg])
            - V_DROPOUT_MAX[reg])


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
                               i_a=p["i_cascada_a"],
                               lf_vpp=p["rizado_lf_vpp"])
    for reg in V_SET:
        necesita = v_necesaria_v(reg, tol_set=p["tol_set_v"])
        assert v_min >= necesita, (
            f"{reg} deja de regular: le llegan {v_min:.3f} V en el peor caso "
            f"y necesita {necesita:.3f} (setpoint {abs(V_SET[reg]):.1f} + "
            f"{p['tol_set_v']:.3f} de ventana de setpoint + "
            f"{V_DROPOUT_MAX[reg]:.2f} de dropout garantizado a "
            f"{I_DROPOUT_GARANTIZADO_A[reg]:.1f} A). Por debajo "
            f"el pre-regulador deja de regular y el ruido del IRM pasa entero "
            f"a la isla LT")


P_BASE_MARGEN = {
    "tempco_pct_c": TEMPCO_PCT_C,
    "r_serie_ohm": R_SERIE_OHM,
    "i_cascada_a": I_CASCADA_A,
    "tol_set_v": 0.0,        # el supuesto del papel: setpoint exacto
    "rizado_lf_vpp": RIZADO_LF_VPP,
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
    # El papel no resta rizado ninguno en ese punto de su cadena, y con el LC
    # puesto el rizado que llega son 0,6 mV: cae dentro de su propio redondeo.
    papel = v_entrada_minima_v(t_c=75.0, r_serie_ohm=0.0, i_a=0.0, lf_vpp=0.0)
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
        garantizado = tol_setpoint_v(reg)
        optimista = tol_setpoint_v(reg, ajustado=True)
        assert optimista < garantizado, (
            f"{reg}: el supuesto optimista --ajustar y que la unidad conserve "
            f"su sitio en la ventana-- tiene que estrechar el numero "
            f"({optimista:.3f} contra {garantizado:.3f}); si no, no seria "
            f"optimista y no habria dos lecturas que distinguir")
        assert garantizado > TOL_SET_V3_V, (
            f"{reg}: la referencia garantiza +-{garantizado:.3f} V de setpoint "
            f"y el bring-up de la v3 acepta +-{TOL_SET_V3_V:.1f}: si cupiera "
            f"con un divisor fijo, esa ventana no diria nada y no habria que "
            f"ajustar placa a placa")

    # 5. El requisito de estabilidad de U1, de su propia hoja.
    #
    # OJO CON LA COTA DE ABAJO. Con el LM2941 la ventana era (0,100 - 1,0) y
    # el aserto mordia por los dos lados. La del LT1963A es (0 - 3,0): un
    # "lo <= ESR" con lo = 0 es un ASERTO QUE NO PUEDE FALLAR, porque una ESR
    # negativa no existe. Escribirlo asi daria una puerta que parece vigilar
    # dos cosas y vigila una. Se comprueba lo que la hoja dice y nada mas.
    lo, hi = ESR_COUT_U1_VENTANA_OHM
    assert lo == 0.0, (
        f"la ventana de ESR de U1 tiene cota inferior ({lo} ohm): el aserto "
        f"de abajo la esta ignorando. Si vuelve a haber una pieza que exija "
        f"ESR MINIMA --como el LM2941, que pedia 100 mohm-- hay que volver a "
        f"comprobar los dos lados")
    assert COUT_U1_F >= COUT_U1_MIN_F, (
        f"COUT de U1 son {COUT_U1_F * 1e6:.0f} uF y la hoja exige al menos "
        f"{COUT_U1_MIN_F * 1e6:.0f}")
    assert ESR_COUT_U1_OHM <= hi, (
        f"la ESR declarada del COUT de U1 ({ESR_COUT_U1_OHM} ohm) pasa del "
        f"maximo de {hi} que la hoja del LT1963A exige (Rev G p. 14). Es "
        f"requisito de estabilidad del lazo, no una recomendacion")

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
    z = borde_rojo(_guarda_margen, dict(P_BASE_MARGEN), "rizado_lf_vpp",
                   0.0, 5.0, "deja de regular")
    print(f"  canario: con el setpoint mas de {v * 1000:.0f} mV por encima de "
          f"su nominal, no regula")
    print(f"  canario: con mas de {w:.3f} ohm de serie (LC + perla), no regula")
    print(f"  canario: con mas de {x:.4f} %/C de deriva del IRM, no regula "
          f"({x / TEMPCO_PCT_C:.1f} veces la publicada)")
    print(f"  canario: con mas de {y:.1f} %/C se pasaria del maximo absoluto")
    print(f"  canario: con mas de {z * 1000:.0f} mVp-p de rizado por DEBAJO "
          f"del codo del LC, no regula")
    print("           (ese borde se busca con el setpoint EXACTO, que es el "
          "supuesto del papel;")
    print(f"            con la deriva real de la referencia bastan "
          f"{2000 * min(margen_v(r) for r in V_SET):.1f} mVp-p)")
    peor = min(tol_set_admisible_v(reg) for reg in V_SET)
    assert abs(v - peor) < 0.005, (
        f"el canario encuentra el borde en {v:.4f} V y la cuenta directa da "
        f"{peor:.4f}: la guarda y el modelo no miden lo mismo")

    # 7. Y EL ASERTO QUE DECIDE EL VEREDICTO: un margen mas pequeno que la
    #    barra de error del propio modelo no es un margen. La barra se DERIVA
    #    de los dos ESTIMADO de la cadena --la deriva extrapolada por encima
    #    de los 50 C que la hoja garantiza, y la resistencia serie de dos
    #    piezas sin elegir-- y no se escoge.
    banda = incertidumbre_estimados_v()
    assert banda > 0.0, (
        "si mover los ESTIMADO un 50 % no moviera la cadena, no serian los "
        "terminos que este guion dice que son")
    assert min(margen_v(r) for r in V_SET) < banda, (
        f"si el margen ({min(margen_v(r) for r in V_SET) * 1000:.1f} mV) "
        f"superara la incertidumbre del modelo ({banda * 1000:.0f} mV), este "
        f"guion podria salir en verde y el HUECO de abajo sobraria")


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
    print(f"   -{rizado_en_u1_vpp() / 2:.4f}  medio rizado DESPUES del LC   "
          f"({RIZADO_VPP * 1000:.0f} mVp-p / {-20 * math.log10(h_lc(F_CONMUTACION_HZ)):.0f} dB)")
    print(f"   -{I_CASCADA_A * R_SERIE_OHM:.3f}   {I_CASCADA_A * 1000:.0f} mA x "
          f"{R_SERIE_OHM * 1000:.0f} mohm         (LC + perla)")
    print(f"    {v_entrada_minima_v():.3f} V le llegan a U1/U2 en el peor caso")
    print(f"    ({v_entrada_minima_v(filtrado=False):.3f} si TODO el rizado "
          f"cayera por debajo del codo del LC")
    print("     y este no quitara nada; ver el canario de rizado_lf_vpp)")

    print(f"\n  {'reg':4s} {'setpoint':>9s} {'ventana':>8s} {'dropout':>8s} "
          f"{'necesita':>9s} {'llega':>7s} {'margen':>8s}")
    deficit = {}
    for reg in V_SET:
        m = margen_v(reg)
        deficit[reg] = m
        print(f"  {reg:4s} {abs(V_SET[reg]):8.2f}V "
              f"{tol_setpoint_v(reg):+7.3f}V {V_DROPOUT_MAX[reg]:7.2f}V "
              f"{v_necesaria_v(reg):8.3f}V {v_entrada_minima_v():6.3f}V "
              f"{m * 1000:+7.0f}mV")
    print("  (la ventana es lo que la hoja GARANTIZA: la Vref de la unidad en")
    print("   todo su rango de temperatura, sobre un divisor fijo disenado")
    print("   con la tipica. Si se ajusta placa a placa Y se supone que la")
    print("   unidad conserva su sitio dentro de la ventana al calentarse")
    print(f"   --que la hoja NO promete-- bajarian a "
          f"{tol_setpoint_v('U1', ajustado=True):.3f} V en U1 y "
          f"{tol_setpoint_v('U2', ajustado=True):.3f} en U2, y el margen")
    print(f"   seria {margen_v('U1', tol_set=tol_setpoint_v('U1', ajustado=True)) * 1000:+.1f}"
          f" mV en U1: sigue sin haber margen.)")

    print("\n  con el dropout TIPICO de la curva a 650 mA (que no es una "
          "garantia y no decide):")
    for reg in V_SET:
        m_tip = (v_entrada_minima_v() - abs(V_SET[reg])
                 - tol_setpoint_v(reg) - V_DROPOUT_TIP[reg])
        print(f"    {reg}: {m_tip * 1000:+.0f} mV con "
              f"{V_DROPOUT_TIP[reg]:.2f} V de dropout")

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
    banda = incertidumbre_estimados_v()
    if deficit[peor_reg] >= banda:
        print(f"\nOK: margen_budget.py (el peor es {peor_reg} con "
              f"{deficit[peor_reg] * 1000:+.0f} mV sobre una incertidumbre de "
              f"{banda * 1000:.0f})")
        return 0

    admisible = min(tol_set_admisible_v(reg) for reg in V_SET)
    print()
    print("=" * 72)
    print("La cadena no tiene MARGEN, y no es un fallo de este guion:")
    for reg in V_SET:
        print(f"  {reg}: {deficit[reg] * 1000:+.1f} mV de margen "
              f"(necesita {v_necesaria_v(reg):.3f} V, le llegan "
              f"{v_entrada_minima_v():.3f})")
    print(f"  Y la INCERTIDUMBRE del propio modelo son {banda * 1000:.0f} mV: "
          f"lo que se mueve la")
    print("  cadena si los dos ESTIMADO --la deriva termica, extrapolada por")
    print(f"  encima de los {T_TOPE_HOJA_C:.0f} C hasta donde la hoja la "
          f"garantiza, y la resistencia")
    print("  serie de dos piezas sin elegir-- se van un 50 %. Un margen mas")
    print("  pequeno que la barra de error de su propio modelo no es un margen.")
    print()
    print("  Y con la eleccion contraria sobre el rizado --que la hoja no")
    print("  publica-- el margen se va a "
          f"{margen_v(peor_reg, filtrado=False) * 1000:+.0f} mV. Bastan "
          f"{2000 * deficit[peor_reg]:.1f} mVp-p de rizado")
    print("  por debajo del codo del LC para acabar con el, sobre los 200 que")
    print("  la hoja publica sin decir donde caen.")
    print("  La ventana de setpoint mas ancha que dejaria regular a los dos")
    print(f"  son +-{admisible * 1000:.0f} mV. La deriva de la referencia del "
          f"pre-regulador,")
    print(f"  con la placa YA AJUSTADA, son +-{tol_setpoint_v('U1') * 1000:.0f}"
          f" mV en U1 y +-{tol_setpoint_v('U2') * 1000:.0f} en U2.")
    print()
    print("  LO QUE FALTA ES UNA PIEZA, Y SE SABE CUAL HACE FALTA:")
    pres = v_entrada_minima_v() - abs(V_SET[peor_reg])
    gasta = tol_setpoint_v(peor_reg) + V_DROPOUT_MAX[peor_reg]
    print(f"   {peor_reg} tiene un presupuesto de ventana+dropout de "
          f"{pres:.3f} V")
    print(f"   y la pieza de hoy gasta {gasta:.3f}. Para que el margen valga "
          f"mas que")
    print(f"   la incertidumbre del modelo hay que bajar de {pres - banda:.3f} "
          f"V, o sea")
    print(f"   {(gasta - pres + banda) * 1000:.0f} mV mejor que la de hoy en "
          f"la SUMA de las dos.")
    print("   Y el reparto importa: TODO el desajuste sale del dropout SOBRE")
    print("   TEMPERATURA (0,8 V a 25 C contra 1,0 garantizado), no de la")
    print("   referencia. Dicho asi es una busqueda acotada; dicho como 'el")
    print("   mercado casi no fabrica LDO negativos' es una excusa.")
    print()
    print("   Lo que NO sirve, y esta medido:")
    print("    - Enfriar el recinto. El equilibrio de U2 esta en aire a 25 C,")
    print("      o sea un recinto sin calor dentro: vaciarlo entero da 6 mV")
    print("      de los 170. La temperatura del aire la manda el cajon.")
    print("    - Bajar el setpoint. PROHIBIDO por v2 sec.1.5.1: el headroom")
    print("      del LT3045/94 son 1,1 V y no puede bajar.")
    print("    - Aceptar el tipico en vez del garantizado. Es lo que hace un")
    print("      catalogo, no un presupuesto.")
    print()
    print("   Y una via que EXISTE y tiene precio: un regulador POSITIVO")
    print("   referenciado al nodo negativo, que se puede porque PS2 flota")
    print("   (sec.4.2). Funciona y no cuesta un vatio, pero deja el ON/OFF")
    print("   referenciado a -12,9 V y mete un semiconductor en el retorno de")
    print("   la carga negativa, en serie con GNDA. Cambiar la pieza es una")
    print("   decision de BOM; cambiar la topologia de masa es de arquitectura.")
    print("=" * 72)
    print()
    buenos = [r for r in V_SET if deficit[r] >= banda]
    print(f"HUECO: {peor_reg} se queda con {deficit[peor_reg] * 1000:+.1f} mV "
          f"de margen de entrada en su peor caso, y la incertidumbre del "
          f"propio modelo son {banda * 1000:.0f}. "
          + (f"{', '.join(buenos)} ya esta resuelto (LT1963A, firmado el "
             f"2026-09-04). " if buenos else "")
          + "Lo que falta es la pieza de arriba: mientras no exista en el "
            "arbol una hoja que la cumpla, este guion sale en HUECO. NO es un "
            "aserto que se baje, y NO se cierra decidiendo: se cierra con una "
            "hoja de datos.")
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
