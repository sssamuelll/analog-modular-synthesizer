"""Lo que le llega a U1/U2, contra lo que necesitan para regular.

    python margen_budget.py          (verde desde D-F9, 2026-09-06)

## Por que existe, y a quien sustituye

Es el sustituto de `valle_budget.py` de la v3, que muere con el rectificador
(Tarea 12). La pregunta es la misma --le llega a U1/U2 bastante tension para
que regulen?-- y el problema ya no tiene 100 Hz que integrar: sin puente ni
condensador de bulto no hay valle. Lo que hay es una CADENA DE CONTINUA.

## EL ESTADO, PRIMERO: verde, y lo cerraron DOS PIEZAS

Margen de entrada garantizado: **+330 mV en `U1` y +536 en `U2`**, sobre una
incertidumbre de modelo de 127 mV. El peor de los dos es hoy `U1`.

Este guion estuvo en HUECO del 2026-09-04 al 06 y **no se cerro decidiendo
nada**: se cerro cambiando las dos piezas de la cascada, cada una con su firma
y su hoja de datos en el arbol.

| | era | es | ventana + dropout | margen |
|---|---|---|---|---|
| `U1` | LM2941 | **LT1963A** (D-F8, 04-09) | 1,658 -> 0,940 V | -388 -> **+330 mV** |
| `U2` | LM2991 | **LT3015** (D-F9, 06-09) | 1,640 -> 0,934 V | -170 -> **+536 mV** |

Lo que sigue es POR QUE el hueco existio, y se conserva entero porque es el
razonamiento que hay que rehacer si alguna de las dos piezas vuelve a cambiar.

## EL HALLAZGO (2026-09-04): al papel le faltaban dos terminos, y sin ellos
## el margen no existia

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
temperatura, sobre un divisor fijo disenado con la tipica-- el margen salia
**-388 mV en `U1` y -170 en `U2`** con las piezas de entonces.

Y si se ajusta placa a placa **y ademas** se supone que la unidad conserva su
sitio dentro de la ventana al calentarse --cosa que la hoja NO promete, porque
da las dos ventanas como filas independientes-- lo mejor que puede pasar son
**+2,8 mV**. Ese 2,8 hay que leerlo contra otra cosa que este guion tambien
calcula: **la incertidumbre de su propio modelo son 127 mV**, que es lo que se
mueve la cadena si los dos ESTIMADO --la deriva termica extrapolada por encima
de los 50 C que la hoja garantiza, y la resistencia serie de dos piezas sin
elegir-- se van un 50 %. Un margen mas pequeno que la barra de error de su
propio modelo no es un margen, y ese es el aserto que decide el veredicto.

O sea que por los dos caminos, el garantizado y el optimista, la respuesta era
la misma: **no habia margen**. Y es la misma doctrina que este guion aplica al
dropout, donde usa el garantizado a la corriente MAYOR y no el tipico de la
curva.

**Eso no se arreglaba bajando el aserto**, y no se bajo. Con el LT1963A y el
LT3015 los dos rieles pasan **con lo garantizado**, sin recurrir al supuesto
optimista y sin ajustar placa a placa. De hecho la ventana del LT3015 (0,254 V)
es MAS ESTRECHA que los +-0,3 V con los que el bring-up de la v3 acepta el
setpoint: el -12,9 V cabe con divisor fijo. Eso rompio un aserto que daba por
sentado lo contrario --ver el punto 4 de `_autocomprobacion`-- y romperlo era
lo correcto: exigia que la pieza nueva fuera tan mala como la vieja.

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

Por abajo manda el dropout; por arriba, el maximo absoluto de entrada. Desde
D-F9 los dos ya no se parecen: **LT1963A +-20 V** (Rev G p. 2) y **LT3015
+-33 V** (rev B p. 2), asi que la cota de este guion es la del LT1963A. En
marcha normal el maximo ni se acerca --15,7 contra 20-- y ese lado pasa.

**El caso que si aprieta por arriba es el OVP del propio IRM, y ahi NO cabe:**
la hoja del IRM-20 (p. 2) clampa hasta **20,25 V sostenidos** contra los 20,00
del LT1963A. Eso lo lleva `check_absmax.py`, que es su dueno, y esta abierto
como la **#334** -- junto con el aserto de `V_OVSD_U1`, que vigila una
prestacion del LM2941 que el LT1963A no tiene.

## Lo que este guion NO cubre

  * El transitorio de arranque y el microcorte. Los IRM tienen setup de 1000 ms
    tipico sin maximo y hold-up de 40 ms, y durante esas ventanas la tension no
    esta en un punto de operacion. Es de `secuencia_budget.py` (D-F4).
  * El dropout GARANTIZADO a los 710 mA de la cascada. NINGUNA de las dos
    hojas lo publica ahi: el LT1963A salta de 500 mA (0,35 V) a 1,5 A (0,55) y
    el LT3015 de 500 mA (0,39) a 1,5 A (0,68). Interpolar entre dos garantias
    no da una garantia. El veredicto usa el de 1,5 A --que es peor y por lo
    tanto valido-- y se imprime el tipico de la tabla al lado, que NO decide.
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
#   LT3015 rev B p. 5, "ADJ Pin Voltage (Notas 2, 3)": -1,22 V tipicos;
#                      -1,208/-1,232 a 25 C; -1,196/-1,244 en la fila marcada
#                      con `l`, que en las hojas de Linear es la que vale
#                      SOBRE TODO EL RANGO DE TEMPERATURA. Y esa fila lleva
#                      ademas las condiciones -30V < VIN < -2,3V y
#                      -1,5A < ILOAD < -1mA: o sea que dentro de esos 48 mV
#                      YA ESTAN la regulacion de linea y la de carga. Es una
#                      garantia mas inclusiva que la del LM2991, no solo mas
#                      estrecha.
#
# LOS DOS SUJETOS CAMBIARON, Y CADA UNO CON SU FIRMA:
#   U1 ERA UN LM2941 (1,211-1,339 sobre temperatura, 0,658 V de ventana sobre
#   el setpoint) y con el la cadena salia a -388 mV. D-F8, 2026-09-04.
#   La ventana baja a 0,390 V y el margen pasa a +330 mV.
#   U2 ERA UN LM2991 (-1,15/-1,27 sobre temperatura, 0,640 V de ventana) y con
#   el la cadena salia a -170 mV: este guion estuvo en HUECO por el desde el
#   2026-09-04 hasta el 06. D-F9, 2026-09-06. La ventana baja a 0,254 V,
#   el dropout de 1,00 a 0,68, y el margen pasa a +536 mV.
VREF = {"U1": {"typ": 1.210, "25c": (1.192, 1.228), "temp": (1.174, 1.246)},
        "U2": {"typ": 1.220, "25c": (1.208, 1.232), "temp": (1.196, 1.244)}}
# Dropout GARANTIZADO sobre el rango de temperatura, con LA CORRIENTE A LA QUE
# LA HOJA LO GARANTIZA -- que no es la nuestra en ninguno de los dos casos:
#   LT1963A Rev G p. 5: "Dropout Voltage ... ILOAD = 1.5A ... 0.34 0.45 0.55"
#   LT3015 rev B p. 5: "Dropout Voltage ... ILOAD = -1.5A (DD-PAK/TO-220)",
#     fila `l`: 0,68 V max. OJO CON EL ENCAPSULADO: la misma tabla da 0,50 V
#     para el DFN/MSOP a la misma corriente, y el que va contra la pared del
#     chasis es el TO-220. Se toma SU fila, que es la peor de las dos.
#
# NINGUNA DE LAS DOS PUBLICA UN MAXIMO A LOS 710 mA REALES de la cascada, asi
# que se toma la cota de la corriente MAYOR. Es pesimista a proposito y por
# igual para los dos: el LT1963A salta de 500 mA (0,35 V) a 1,5 A (0,55) y
# entre medias no hay nada garantizado; el LT3015 salta de 500 mA (0,39) a
# 1,5 A (0,68).
V_DROPOUT_MAX = {"U1": 0.55, "U2": 0.68}
I_DROPOUT_GARANTIZADO_A = {"U1": 1.5, "U2": 1.5}
# El TIPICO de tabla mas cercano por debajo. NO decide: se imprime.
#   LT1963A p. 5 a 500 mA: 0,19 V; LT3015 p. 5 a 500 mA (DD-PAK/TO-220): 0,20
V_DROPOUT_TIP = {"U1": 0.19, "U2": 0.20}
# Maximo absoluto de entrada. ES EL MENOR DE LOS DOS, y desde D-F9 los dos ya
# no se parecen:
#   U1 LT1963A Rev G p. 2: "IN Pin Voltage ... +-20V"
#   U2 LT3015 rev B p. 2:  "IN Pin Voltage ... +-33V"
# Citaba 26,0 de "(LM2941 p. 5, LM2991 p. 4)" y ninguna de las dos piezas
# sigue en la placa. Aqui se corrige la mitad que D-F9 toca (U2) y de paso la
# otra, porque dejar el numero de un muerto es como se llega a una puerta
# verde sobre nadie.
#
# ESTE GUION SIGUE PASANDO POR ARRIBA: en marcha normal llegan 15,67 V. Lo que
# NO cabe es el OVP de PS1 --20,25 V sostenidos, hoja del IRM-20 p. 2-- contra
# los 20,00 del LT1963A, y ESO es la #334: vive en check_absmax.py, que es su
# dueno, y no se decide aqui.
V_ABSMAX_ENTRADA = 20.0

# --- la corriente real de la cascada (#343) -------------------------------
# RIEL_MA es la carga declarada de la cascada (D-F1: 650 mA/riel hasta el
# 2026-10-23, 450 desde entonces) y lo que vigila consumo_total_budget.py; se
# importa, no se copia. Encima, el consumo propio
# del pre-regulador a plena carga:
#   * U1 (LT1963A, lt1963a-rev-g-2021-02.pdf p. 5, "GND Pin Current",
#     IL = 1,5 A, VIN = VOUT(NOMINAL) + 1 V, fila de punto negro para todo el
#     rango de temperatura): 80 mA tip., 120 mA max. (Sustituye a los 60 mA del
#     LM2941 retirado por D-F8: issue #343).
#   * U2 (LT3015, lt3015-rev-b.pdf p. 5, "GND Pin Current", IL = -1,5 A,
#     fila de punto negro): 35 mA tip., 70 mA max.
# La cota comun conservadora toma el maximo de los dos (120 mA de U1).
IQ_U1_MAX_A = 0.120
IQ_U2_MAX_A = 0.070
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
        # ESTE ASERTO CAMBIO DE SUJETO CON D-F9, y el cambio es la noticia.
        #
        # Decia: "la ventana garantizada tiene que ser MAS ANCHA que los
        # +-0,3 V del bring-up, porque si cupiera con un divisor fijo esa
        # ventana no diria nada y no habria que ajustar placa a placa".
        # Con el LT3015 ya NO es verdad, y no es un fallo: su ventana son
        # 0,254 V, o sea MENOS que los 0,3 del bring-up. El -12,9 V cabe con
        # divisor fijo y sin ajustar. Dejar el aserto viejo habria sido
        # exigirle a la pieza nueva que fuera tan mala como la vieja --y
        # habria puesto la puerta roja por MEJORAR el diseno.
        #
        # Lo que si vale siempre, y es lo que se asevera ahora: la ventana con
        # la que el bring-up ACEPTA una placa tiene que caber dentro de la que
        # todavia deja regular. Si no, el paso 2 da por buena una placa que en
        # el peor caso se sale de regulacion.
        assert TOL_SET_V3_V <= tol_set_admisible_v(reg), (
            f"{reg}: el bring-up de la v3 acepta +-{TOL_SET_V3_V:.1f} V de "
            f"setpoint y la cadena solo aguanta "
            f"+-{tol_set_admisible_v(reg):.3f}: el paso 2 daria por buena una "
            f"placa que no regula")

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
    # EL TECHO DE ESTE BARRIDO BAJO DE 1,0 A 0,5 CON D-F9, y no por gusto.
    # `_guarda_margen` tiene DOS asertos y el del maximo absoluto va primero.
    # Mientras V_ABSMAX_ENTRADA valia los 26 V del LM2941 --una pieza que ya
    # no esta-- ese lado no saltaba hasta 1,60 %/C y el barrido hasta 1,0
    # solo podia morir por "deja de regular". Con los 20,0 V reales del
    # LT1963A el maximo absoluto salta en 0,69 %/C, o sea DENTRO del barrido
    # viejo: en el extremo el canario moria por el otro aserto y no
    # encontraba su borde. El borde que busca esta en ~0,14 %/C, asi que
    # 0,5 lo deja holgado y por debajo del otro.
    x = borde_rojo(_guarda_margen, dict(P_BASE_MARGEN), "tempco_pct_c",
                   0.0, 0.5, "deja de regular")
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
    # Y EL ASERTO SE DIO LA VUELTA CON D-F9. Hasta el 2026-09-06 decia "el
    # margen tiene que ser MENOR que la banda, porque si no el HUECO sobraria":
    # era la guarda de un hueco declarado, y con el LM2991 en U2 se cumplia
    # sola. Con el LT3015 el margen pasa a +536 mV sobre una banda de 127, o
    # sea que el hueco se cerro y lo que hay que vigilar es lo contrario.
    peor = min(margen_v(r) for r in V_SET)
    peor_reg = min(V_SET, key=margen_v)
    assert peor >= banda, (
        f"{peor_reg} se queda con {peor * 1000:+.1f} mV de margen y la "
        f"incertidumbre del propio modelo son {banda * 1000:.0f}: un margen "
        f"mas pequeno que la barra de error de su propio modelo NO ES UN "
        f"MARGEN. Antes de tocar este aserto, mirar que se movio -- la "
        f"cadena la resuelven piezas, no cotas: asi se cerro el hueco de U2 "
        f"(D-F9, LM2991 -> LT3015) y el de U1 (D-F8, LM2941 -> LT1963A)")


def demo() -> int:
    t = t_aire_diseno_c()
    print("margen_budget: lo que le llega a U1/U2 contra su dropout\n")
    print(f"  temperatura del aire del recinto: {t:.2f} C "
          f"(calor_budget.py, punto fijo con D-F3 = A)")
    print(f"  corriente de la cascada: {I_CASCADA_A * 1000:.0f} mA "
          f"({RIEL_MA:.0f} de riel + {IQ_U1_MAX_A * 1000:.0f} de U1, #343), sobre "
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
          f" mV en U1. Pero NO HACE FALTA ese supuesto: la")
    print("   cadena ya pasa con lo garantizado, que es lo que decide.)")

    print("\n  con el dropout TIPICO de la curva a 650 mA (que no es una "
          "garantia y no decide):")
    for reg in V_SET:
        m_tip = (v_entrada_minima_v() - abs(V_SET[reg])
                 - tol_setpoint_v(reg) - V_DROPOUT_TIP[reg])
        print(f"    {reg}: {m_tip * 1000:+.0f} mV con "
              f"{V_DROPOUT_TIP[reg]:.2f} V de dropout")

    print(f"\n  por arriba: {v_entrada_maxima_v():.2f} V en vacio y a "
          f"tolerancia alta, contra {V_ABSMAX_ENTRADA:.0f} de maximo")
    print("  absoluto (el menor de los dos: LT1963A +-20 V, LT3015 +-33). "
          "En marcha")
    print("  normal ese lado pasa holgado. El caso que SI aprieta por arriba "
          "es el")
    print("  OVP del IRM --20,25 V sostenidos-- y es de check_absmax.py (#334).")

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

    # LA RAMA DEL HUECO. Hasta el 2026-09-06 esto eran setenta lineas
    # explicando que la cadena no tenia margen, cual era la pieza que hacia
    # falta y las cuatro salidas con su precio. Ya no hace falta: la pieza
    # existe, esta en el arbol y es el LT3015 (D-F9). Lo que se guarda es la
    # capacidad de VOLVER a declarar el hueco, no la prosa de uno cerrado --
    # esa vive en el papel de la v4 y en el docstring de aqui arriba.
    #
    # En la practica esta rama no se alcanza: el aserto 7 de
    # _autocomprobacion() salta antes y con el diagnostico dentro. Si algun
    # dia alguien quita ese aserto, esto sigue diciendo la verdad en vez de
    # devolver 0 en silencio.
    print()
    print(f"HUECO: {peor_reg} se queda con {deficit[peor_reg] * 1000:+.1f} mV "
          f"de margen de entrada en su peor caso, y la incertidumbre del "
          f"propio modelo son {banda * 1000:.0f}: un margen mas pequeno que "
          f"la barra de error de su propio modelo no es un margen. La ventana "
          f"de setpoint mas ancha que dejaria regular a los dos son "
          f"+-{min(tol_set_admisible_v(r) for r in V_SET) * 1000:.0f} mV. "
          f"Esto NO se cierra bajando el aserto ni aceptando el tipico: se "
          f"cierra con una hoja de datos, que es como se cerraron D-F8 y "
          f"D-F9.")
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
