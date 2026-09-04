"""La cadena termica de la fuente v4, de la sala al silicio, y lo que sale de
ella: la corriente SOSTENIDA de cada riel. Es la columna que la sec.1 del papel
tiene vacia, y el dueno de techo del #151.

    python calor_budget.py

## Por que existe

Una corriente sostenible no es propiedad de un modulo: lo es de la terna
(modulo, recinto, ambiente). El liston se firmo el 2026-09-03 en corriente DE
PLACA --3,8 / 2,5 / 4,0 A de rack-- y la v1 del papel lo llamo "superior a la
A-100PSU3" sin mirar donde iba a vivir. La PSU3 entrega sus 2 A en un case
ABIERTO, al aire de la sala; estos IRM entregan lo que su curva de derating
diga al aire que haya dentro de una caja de acero. Samuel firmo D-F3 = A el
2026-09-03 --ventilar recinto y cajon por conveccion natural, sin
ventilador-- y este guion es el que dice cuanto compro esa decision.

## El modelo, en tres tramos

  1. Aire del cajon sobre la sala: la MISMA ecuacion de tiro de chimenea de
     guarda_aire() en case/clearance_budget.py (P = k * dT**1.5), con sus
     constantes importadas y no copiadas. Dos diferencias declaradas: la T
     absoluta del termino de flotabilidad son 318 K (sala de 45 C, spec del
     chasis sec.3.1) y no los 293 K del case --un cambio del 8,5 % en T
     absoluta que baja k un 4 % y sube dT un 2,8 %--; y el area efectiva de
     hoy (3299 mm2) y su tiro (105 mm) son los
     del case SIN las aberturas de D-F3: `area_venteo_mm2` se le suma.
  2. Aire del recinto de acero sobre el del cajon: conduccion por la chapa
     (0,1453 m2 x 9 W/m2K) en paralelo con una chimenea propia de
     `area_venteo_mm2` y 83 mm de tiro. Se resuelve por biseccion.
  3. El modulo: la hoja da su derating contra el aire que lo rodea, y ese
     aire es el del recinto. No se anade salto propio: la curva ya lo trae.

SOSTENIDO es un PUNTO FIJO, no una evaluacion: la corriente que el rack puede
dar calienta el cajon, el calor sube el aire, el aire recorta la corriente.
Se resuelve por biseccion sobre la temperatura del aire del recinto: la
cadena T -> corrientes(T) -> calor -> T' es no creciente en T (mas aire
caliente, menos corriente, menos calor), asi que T' - T tiene una sola raiz.
(La primera version iteraba sobre las corrientes con relajacion y oscilaba
con poco venteo entre un estado caliente y flojo y uno frio y fuerte; con el
min() de D-F7 dejo de converger. La biseccion no amortigua nada.)

## Lo que salio la primera vez, y la decision que provoco (D-F7)

La busqueda de area prueba primero la guarda con 200 000 mm2 y, si ahi ya
salta, publica infinito: no hay venteo que arregle un margen que no existe.
Con PS5 = IRM-20-5, como el papel la traia, salio INFINITO: la IRM-20-5 son
20 W a 5 V = 4,0 A de placa, exactamente el liston del +5 V de rack, y su
curva "3.3V,5V" tiene el codo a 45 C, justo la sala de diseno. Cero margen.
Los otros tres rieles pasaban holgados.

Samuel firmo el 2026-09-03 (D-F7) que PS5 pasa a **IRM-45-5** --8 A de placa,
codo a 50 C, la misma pieza que PS6-- y que el liston del +5 V de rack se
queda en 4,0 A declarados. Por eso este guion distingue dos numeros que el
papel mezclaba: MODULO_A, lo que el modulo puede dar (su placa, hoja p. 2), y
PLACA_A, lo que el instrumento declara (D-F1). El sostenido es el menor de
los dos: la placa del modulo recortada por su curva, y nunca por encima de lo
declarado. El -12 V ya venia asi sin decirlo (IRM-45-12 de 3,8 A declarada a
2,5), y el digital tambien (8 A de placa, 8 declarados).

## Lo que salio la segunda vez: el calor se cobraba mal (2026-09-03, tarde)

El reparto de calor era UN cociente agregado --sum(corrientes)/sum(PLACA_A),
en amperios-- aplicado a los dos totales. Las celdas del papel sec.6 estan en
VATIOS y no pesan igual: el digital son 8,0 de los 18,3 A (44 %) y solo 24,7
de los 120,3 W (20,5 %), y como ademas es el riel que mas se derratea, su
recorte arrastraba hacia abajo el calor que se le cobra a la FILA DE
INVITADOS, que no depende del digital para nada. En el punto fijo cobraba
80,4 W donde habia 89,2: un 11 % de menos, y el liston pasaba por 5 mA.
Ahora cada celda va a SU riel (V_RIEL, CAJON_DIGITAL_W, PERDIDA_RECINTO_W) y
las dos potencias maximas se DERIVAN en vez de transcribirse. Consecuencias:

  * el area minima sube de 16 803 a 20 525 mm2 (el papel sec.6 publicaba
    16 900 redondeados; el case pedia entonces 35 365 por su propio techo de
    15 K, asi que el encargo a #289 no se movia);
    y el 2026-09-04 sube otra vez a 22 148 al contar la franja de red, ver
    abajo;
  * el techo del digital casi no se mueve --21,10 -> 21,09 W-- porque en el
    area minima el liston se cumple justo, y el digital lo sigue;
  * la CAJA CERRADA deja de tener punto de trabajo. Antes publicaba
    0,95 / 0,95 / 2,0 A "a 92,6 C", que era un artefacto: las corrientes de
    la frontera de 85 C con la temperatura de otro punto. Una biseccion
    converge igual de bien sobre una discontinuidad que sobre una raiz, y
    derating() vale CERO por encima de 85 C. Con el calor bien cobrado el
    punto fijo aterriza arriba del acantilado --86,7 C, rack a CERO-- y eso
    si es consistente: sin venteo nuevo no opera ningun modulo del rack.
    _fixed_point() lo COMPRUEBA ahora, en amperios y no en kelvin, y donde no
    hay punto fijo devuelve CERO en vez de reventar: ver ahi por que un
    aserto habria convertido un dato termico en un rojo de CI.

## Lo que salio la tercera vez: a la tabla de calor le faltaba la franja de red

Escribiendo fusible_budget.py (2026-09-04) salio que la tabla de sec.6 lista
PS1..PS6, U1/U2, los LT y U3 -- y se olvida de lo que hay ANTES de los modulos.
La NTC de arranque disipa 2,75 W dentro del recinto a los 3,25 A rms de red del
liston, y el choke de modo comun otros 0,95 (ESTIMADO). El MOV no: en marcha
normal conduce microamperios.

No era un detalle. Con esos 3,70 W el recinto pasa de 27,55 a 31,25 W y el
venteo minimo de 20 525 a 22 148 mm2. Y sin ellos el liston del rack se cumplia
por 3,5 mA: metiendo el calor al area vieja, rack+12 cae a 1,948 A, por debajo
de los 2,0 de la A-100PSU3. El sostenido apenas se mueve --2,002 contra
2,003-- porque la busqueda de area lo vuelve a fijar ahi, que es justo lo que
esa busqueda hace.

fusible_budget.py CALCULA la cifra de la NTC y la asevera contra la constante
de aqui: la que entra en el punto fijo es esta, y el aserto es lo que impide
que se separen.

## Lo que este modelo NO cubre

  * El coeficiente de descarga (CD_TIRO) y h_conv (9 W/m2K) son supuestos,
    no medidas: el sostenido es una PREDICCION y el paso 7 del bring-up es lo
    que la vuelve cifra.
  * La conduccion por el encapsulado del IRM a la chapa (papel sec.12.7): se
    ignora, a favor de seguridad.
  * El transitorio: todo es regimen permanente.
  * La geometria del recinto de la spec del chasis (83 mm, 0,1453 m2) no es
    la del CAD de hoy (64 mm, 0,1257 m2): es un desfase conocido entre
    documentos, no una razon para cambiar el modelo en silencio.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Mapping

DIR = os.path.dirname(os.path.abspath(__file__))
CASE_DIR = os.path.join(DIR, "..", "..", "..", "case")
if CASE_DIR not in sys.path:
    sys.path.insert(0, CASE_DIR)
from clearance_budget import (CD_TIRO, CD_TIRO_PESIMISTA,  # noqa: E402
                              CP_AIRE, G, RHO_AIRE)
from curvas import derating  # noqa: E402

# Spec fuente-chasis-telemetria sec.3.1: ambiente peor caso.
T_SALA = 45.0
# Spec fuente-chasis-telemetria sec.3.3: geometria; sec.3.1 usa esta area.
AREA_RECINTO_M2 = 0.1453
# Spec fuente-chasis-telemetria sec.3.1: valor de manual, no medido.
H_CONV_W_M2K = 9.0
# CONTRA: case/cad/params.scad:1707 fija interior z=61; la salida actual de
# case/clearance_budget.py:5903-5905 deriva exterior z=64 mm.
# DERIVADO: 2(.3386*.064)+2(.1766*.064)+.3386*.1766 ~= 0.1257 m2.
# Lo que cada MODULO puede dar: su corriente de placa, fila "RATED CURRENT"
# de la hoja Mean Well, p. 2 (IRM-45, leida 2026-09-03).
MODULO_A = {"rack+12": 3.8,      # PS3 = IRM-45-12
            "rack-12": 3.8,      # PS4 = IRM-45-12
            "rack+5": 8.0,       # PS5 = IRM-45-5 (D-F7, 2026-09-03)
            "digital+5": 8.0}    # PS6 = IRM-45-5
# Lo que el instrumento DECLARA por riel: papel sec.1, D-F1 firmada
# 2026-09-03. Nunca por encima de MODULO_A.
PLACA_A = {"rack+12": 3.8,
           "rack-12": 2.5,
           "rack+5": 4.0,
           "digital+5": 8.0}
# doepfer.de/a100_man/a100t_e.htm, leido 2026-09-03 (papel sec.0).
PSU3_A = {"rack+12": 2.0,
          "rack-12": 1.2,
          "rack+5": 4.0}
# Que curva de derating lee cada riel (curvas.py). La IRM-45 dibuja UNA
# curva para toda la serie, tambien para su salida de 5 V.
CURVA = {"rack+12": "IRM-45",
         "rack-12": "IRM-45",
         "rack+5": "IRM-45",
         "digital+5": "IRM-45"}

# --- el calor, CELDA POR CELDA del papel sec.6 -----------------------------
# Hasta el 2026-09-03 esto era UN cociente agregado en amperios aplicado a los
# dos totales. Estaba mal por una razon simple: las celdas del papel estan en
# VATIOS y no pesan como los amperios. El digital son 8,0 de los 18,3 A de
# PLACA_A (44 %) y solo 24,7 de los 120,3 W (20,5 %); como ademas es el riel
# que mas se derratea, su recorte arrastraba hacia abajo el calor que se le
# cobra a la FILA DE INVITADOS, que no depende del digital para nada. Cobraba
# 80,4 W donde habia 89,2, un 11 % de menos, justo donde el liston pasaba por
# 5 mA: con el reparto bueno el area minima sube de 16 803 a 20 525 mm2.

# Lo que cada riel del RACK le cuesta al cajon: su tension. Todo lo que sale
# del riel se lo gastan los modulos invitados y acaba en calor dentro de la
# misma caja, asi que el calor es la potencia entregada, no una perdida.
V_RIEL = {"rack+12": 12.0, "rack-12": 12.0, "rack+5": 5.0}
# El digital NO entra por capacidad sino por CARGA: el modulo 2 pide lo que
# pide y da igual que PS6 pueda dar 8 A. Su peor caso son los 24,7 W del papel
# sec.6, que son los 4,935 A de la fila "Max TJ = 125 C, 4 N657, host a tope"
# de sec.4.4 -- o sea la salida de power_budget.py. Es una CONSTANTE, y por lo
# tanto conservadora: se cobra ese calor aunque el riel no pueda entregarlo.
CAJON_DIGITAL_W = 24.7
# DERIVADO, no transcrito (el papel publica 120,3 = 95,6 + 24,7).
P_CAJON_MAX = sum(PLACA_A[r] * V_RIEL[r] for r in V_RIEL) + CAJON_DIGITAL_W

# Perdidas DENTRO del recinto, celda por celda del maximo de sec.6. Las tres
# de PS3/PS4/PS5 escalan con lo que entrega su riel; el resto no depende del
# rack: PS1+PS2 alimentan la cascada ultra (3,71), PS6 sigue al digital que
# acabamos de declarar constante (4,88), y U1/U2/LT x4/U3 son la cascada.
PERDIDA_RECINTO_W = {"rack+12": 6.51,     # PS3, 45,6 x (1/0,875 - 1)
                     "rack-12": 4.29,     # PS4, 30 x 0,143
                     "rack+5": 3.95}      # PS5, 20 x (1/0,835 - 1), D-F7
# LA FRANJA DE RED TAMBIEN DISIPA, Y LA TABLA DEL PAPEL sec.6 NO LA LLEVA.
# Se descubrio el 2026-09-04, escribiendo fusible_budget.py: la tabla lista
# PS1..PS6, U1/U2, los LT y U3, y se olvida de lo que hay ANTES de los modulos.
# No es un detalle: con estos 3,7 W el venteo minimo sube de 20 525 a 22 147
# mm2, y sin ellos el liston del rack se cumple por 3,5 mA.
#
#   NTC de arranque: Ametherm SL22 5R012 a los 3,25 A rms de red del liston.
#   Su resistencia caliente a esa corriente son 0,261 ohm (extrapolados de los
#   dos puntos que la hoja publica, 0,12 al 50 % de Imax y 0,05 al 100 %).
#   Lo CALCULA fusible_budget.calor_ntc_w() y lo asevera contra esta constante,
#   que es la que el punto fijo usa: si la NTC o la corriente cambian, aquel
#   guion salta.
NTC_ARRANQUE_W = 2.75
#   Choke de modo comun de la red, redimensionado a >= 4 A (papel sec.5). Su
#   DCR pasa dos veces por la corriente de red. ESTIMADO: 0,09 ohm entre los
#   dos devanados, de catalogo para esa talla; no hay hoja de la pieza.
CHOKE_RED_W = 0.95
#   El MOV no entra: en marcha normal conduce microamperios. Solo disipa
#   durante una sobretension, que es un transitorio y no un punto de operacion.
MOV_RED_W = 0.0
_CONSTANTE_RECINTO_W = (3.71 + 4.88 + 1.24 + 1.37 + 1.30 + 0.30
                        + NTC_ARRANQUE_W + CHOKE_RED_W + MOV_RED_W)
# DERIVADO: el papel publica 27,5 W (28,9 antes de D-F7, con la IRM-20-5 de
# 5,32 W en PS5 donde ahora hay una IRM-45-5 de 3,95).
P_RECINTO_MAX = _CONSTANTE_RECINTO_W + sum(PERDIDA_RECINTO_W.values())
# Salida de `python case/clearance_budget.py` el 2026-09-03, sin D-F3.
A_EF_BASE_MM2 = 3299.0
H_TIRO_CAJON_M = 0.105
# Spec del chasis sec.3.3: exterior derivado 338.6 x 176.6 x 83 mm.
H_TIRO_RECINTO_M = 0.083
T_ABS_AIRE_K = 318.0         # K; mandato T3 para sala 45 C, no 293 K del case.

AREA_BUSQUEDA_MAX_MM2 = 200000.0  # mm2; mandato directo: buscar hasta aqui.
PASOS_BISECCION_T = 60            # COTA: 200 K / 2^60, precision sobrada.
TOLERANCIA_PUNTO_FIJO_A = 0.02    # fraccion de PLACA_A; la biseccion cierra
                                  # con residuo 1e-14 en un punto fijo real.
PASOS_BISECCION_AREA = 48         # COTA: resolucion mucho menor que 1 mm2.
PASOS_BISECCION_DT = 80           # COTA: biseccion termica, precision sobrada.
PASO_AREA_DISENO_MM2 = 100.0      # mm2; plan T3, redondear arriba a centena.
FRACCION_SENSIBILIDAD = 0.10      # Convencion: perturbacion comparativa 10 %.

ESTIMADOS = (
    "H_CONV_W_M2K=9.0: manual, no medido (chassis spec sec.3.1)",
    "CD_TIRO=0.65: SUPUESTO de rejilla (clearance_budget.py)",
    "P_BASE area: hipotesis para #289; el papel del case fija la real",
    f"CHOKE_RED_W={CHOKE_RED_W}: DCR de catalogo de un choke de >=4 A, sin hoja",
)
HUECOS = ()


def _k(area_mm2: float, altura_m: float, cd: float = CD_TIRO) -> float:
    # Formula de guarda_aire() del case; 1e-6 convierte mm2 a m2.
    return (RHO_AIRE * CP_AIRE * cd * area_mm2 * 1e-6
            * math.sqrt(2.0 * G * altura_m / T_ABS_AIRE_K))


def _biseccion_potencia(potencia: float, funcion) -> float:
    if potencia <= 0.0:
        return 0.0
    lo, hi = 0.0, 1.0
    while funcion(hi) < potencia:
        hi *= 2.0
    # Natural-stack guard equation: P = k * dT**1.5 (case guarda_aire).
    # Conversion mm2 -> m2 is 1e-6; exponent 2/3 inverts that equation.
    for _ in range(PASOS_BISECCION_DT):
        mid = (lo + hi) / 2.0
        if funcion(mid) < potencia:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def aire_recinto_c(p_recinto_w: float, p_cajon_w: float, *,
                   area_venteo_mm2: float, t_sala_c: float = T_SALA) -> float:
    """Return enclosure air temperature, with the cabinet stage in series.

    The enclosure loses only ``p_recinto_w`` through sheet convection and its
    new opening. The cabinet's ``p_cajon_w + p_recinto_w`` ends in the cabinet
    stack, as all enclosure heat ultimately enters that air path. The 83 mm
    enclosure height is DERIVED from the chassis document, not estimated.
    """
    if area_venteo_mm2 < 0.0 or p_recinto_w < 0.0 or p_cajon_w < 0.0:
        raise ValueError("area y potencia no pueden ser negativas")
    # Cajon->sala evacua p_cajon+p_recinto; el area nueva se suma a la actual.
    k_cajon = _k(A_EF_BASE_MM2 + area_venteo_mm2, H_TIRO_CAJON_M)
    dt_cajon = ((p_cajon_w + p_recinto_w) / k_cajon) ** (2.0 / 3.0)
    # Recinto->cajon: la chimenea propia usa solo el area nueva.
    k_recinto = (_k(area_venteo_mm2, H_TIRO_RECINTO_M)
                 if area_venteo_mm2 > 0 else 0.0)
    h_area = AREA_RECINTO_M2 * H_CONV_W_M2K
    dt_recinto = _biseccion_potencia(
        p_recinto_w,
        lambda dt: h_area * dt + k_recinto * dt ** 1.5)
    return t_sala_c + dt_recinto + dt_cajon


def _temperaturas(p_recinto_w: float, p_cajon_w: float, area_venteo_mm2: float,
                  t_sala_c: float = T_SALA, *, area_recinto_m2: float = AREA_RECINTO_M2,
                  h_conv: float = H_CONV_W_M2K, cd: float = CD_TIRO) -> tuple[float, float, float]:
    """Private parametrizable form: (air C, cabinet dT K, enclosure dT K)."""
    if area_venteo_mm2 < 0 or p_recinto_w < 0 or p_cajon_w < 0:
        raise ValueError("area y potencia no pueden ser negativas")
    kc = _k(A_EF_BASE_MM2 + area_venteo_mm2, H_TIRO_CAJON_M, cd)
    dc = ((p_cajon_w + p_recinto_w) / kc) ** (2.0 / 3.0)
    kr = _k(area_venteo_mm2, H_TIRO_RECINTO_M, cd) if area_venteo_mm2 else 0.0
    dr = _biseccion_potencia(p_recinto_w,
                             lambda x: area_recinto_m2 * h_conv * x + kr * x ** 1.5)
    return t_sala_c + dc + dr, dc, dr


def _sin_negativas(corrientes: Mapping[str, float]) -> None:
    if any(v < 0.0 for v in corrientes.values()):
        raise ValueError("corriente no puede ser negativa")


def p_cajon_w(corrientes: Mapping[str, float]) -> float:
    """Calor del cajon: cada riel del rack a SU tension, mas la carga fija del
    digital. Con PLACA_A entera son los 120,3 W del papel sec.6."""
    _sin_negativas(corrientes)
    return (sum(corrientes.get(r, 0.0) * V_RIEL[r] for r in V_RIEL)
            + CAJON_DIGITAL_W)


def p_recinto_w(corrientes: Mapping[str, float]) -> float:
    """Calor del recinto: lo que no depende del rack (cascada, PS1/PS2, PS6)
    mas la perdida de PS3/PS4/PS5 en proporcion a lo que entrega cada uno."""
    _sin_negativas(corrientes)
    return _CONSTANTE_RECINTO_W + sum(
        PERDIDA_RECINTO_W[r] * corrientes.get(r, 0.0) / PLACA_A[r]
        for r in PERDIDA_RECINTO_W)


def sostenido_a(riel: str, t_aire_c: float) -> float:
    """Lo que el riel puede dar SOSTENIDO a esa temperatura de aire: la placa
    del modulo recortada por su curva, y nunca por encima de lo declarado."""
    if riel not in PLACA_A:
        raise KeyError(riel)
    return min(PLACA_A[riel],
               MODULO_A[riel] * derating(t_aire_c, CURVA[riel]))


def _fixed_point(p: Mapping[str, float], *,
                 area_recinto_m2: float = AREA_RECINTO_M2,
                 h_conv: float = H_CONV_W_M2K, cd: float = CD_TIRO) -> dict[str, float]:
    """El punto fijo corriente -> calor -> aire -> derating -> corriente.

    Se busca por biseccion sobre la temperatura del aire del recinto. Para
    una T dada las corrientes son sostenido_a(riel, T), de ellas sale el
    calor, y la T' que ese calor produce es no creciente en T: mas aire
    caliente, menos corriente, menos calor. Asi que T' - T tiene una sola
    raiz entre la sala y la sala + 200 K, y esa raiz es el punto fijo."""
    # Las dos potencias del dict quedan como el MAXIMO declarado y ya no se
    # escalan con un cociente: desde el 2026-09-03 cada celda de sec.6 se le
    # cobra a su riel (ver p_cajon_w). Se comprueban para que nadie las toque
    # creyendo que mueven algo.
    assert abs(p["p_cajon_w"] - p_cajon_w(PLACA_A)) < 0.05, (
        f"p_cajon_w={p['p_cajon_w']:.2f} no es el maximo del modelo "
        f"({p_cajon_w(PLACA_A):.2f}): el calor sale de las celdas, no de esta clave")
    assert abs(p["p_recinto_w"] - p_recinto_w(PLACA_A)) < 0.05, (
        f"p_recinto_w={p['p_recinto_w']:.2f} no es el maximo del modelo "
        f"({p_recinto_w(PLACA_A):.2f}): el calor sale de las celdas, no de esta clave")

    def t_desde(temp: float) -> float:
        corrientes = {r: sostenido_a(r, temp) for r in PLACA_A}
        return _temperaturas(p_recinto_w(corrientes), p_cajon_w(corrientes),
                             p["area_venteo_mm2"], p["t_sala_c"],
                             area_recinto_m2=area_recinto_m2,
                             h_conv=h_conv, cd=cd)[0]

    lo, hi = p["t_sala_c"], p["t_sala_c"] + 200.0
    assert t_desde(hi) < hi, (
        "a 200 K sobre la sala ningun modulo da corriente y el aire no puede "
        "seguir ahi: el modelo del recinto esta roto")
    for _ in range(PASOS_BISECCION_T):
        mid = (lo + hi) / 2.0
        if t_desde(mid) > mid:      # el calor a esta T la empuja mas arriba
            lo = mid
        else:
            hi = mid
    temp = (lo + hi) / 2.0
    # Y QUE SEA UN PUNTO FIJO DE VERDAD, comprobado SOBRE LAS CORRIENTES.
    #
    # La biseccion converge igual de bien sobre una DISCONTINUIDAD que sobre
    # una raiz, y ahi devuelve un estado que no existe: hasta el 2026-09-03 la
    # caja cerrada publicaba 0,95 / 0,95 / 2,0 A "a 92,6 C", que son las
    # corrientes de la frontera de 85 C con la temperatura de otro punto.
    #
    # LA COMPROBACION VA EN AMPERIOS Y NO EN KELVIN, y la diferencia importa.
    # Un residuo de temperatura pequeno no prueba nada donde la curva salta:
    # entre 3716 y 3729 mm2 de venteo la biseccion aterriza en 85,0000 exacto,
    # publica esos mismos 0,95 A, y el residuo termico es 0,001-0,048 K --
    # dentro de cualquier tolerancia razonable. En corrientes no hay ventana:
    # el estado dice 0,95 A y a la temperatura que ese estado produce la hoja
    # da 0,00. El criterio es el mismo que usa test_SOSTENIDO_es_un_punto_fijo.
    #
    # Y NO ES UN ASERTO, es un RESULTADO. Que la curva salte donde el aparato
    # trabajaria no es un fallo del guion: es que ahi no hay estado sostenido
    # que prometer. Se devuelve cero --nada operativo-- y guarda_liston() dira
    # "SIGUE sin existir", que es lo que _busca_area_minima() sabe leer para
    # empujar el area hacia arriba. Un assert aqui reventaria el IMPORT del
    # modulo, y con el la puerta de power_budget.py, convirtiendo un dato
    # termico en un rojo de CI: la caja cerrada esta hoy a 1,7 K de eso, y lo
    # dispararian cambios que son MEJORAS (una sala peor caso mas benigna, un
    # censo digital mas ligero).
    corrientes = {r: sostenido_a(r, temp) for r in PLACA_A}
    reales = {r: sostenido_a(r, t_desde(temp)) for r in PLACA_A}
    if any(abs(corrientes[r] - reales[r]) > TOLERANCIA_PUNTO_FIJO_A * PLACA_A[r]
           for r in PLACA_A):
        return {r: 0.0 for r in PLACA_A}
    return corrientes


def guarda_liston(p: dict[str, float]) -> None:
    """Puerta rack contra PSU3; su texto estable alimenta el canario."""
    valores = _fixed_point(p)
    for riel in PSU3_A:
        assert valores[riel] >= PSU3_A[riel], (
            f"SIGUE sin existir: {riel} sostenido {valores[riel]:.3f} A < "
            f"PSU3 {PSU3_A[riel]:.3f} A")


def _falla_por_liston(p: dict[str, float]) -> tuple[bool, str]:
    try:
        guarda_liston(p)
    except AssertionError as exc:
        if "SIGUE sin existir" not in str(exc):
            raise
        return True, str(exc)
    return False, ""


def _busca_area_minima() -> tuple[float, float, str]:
    """Bisect the first green area, or publish infinity after testing 200000."""
    base = {
        "area_venteo_mm2": 0.0,  # mm2; physical lower boundary.
        "p_recinto_w": P_RECINTO_MAX,
        "p_cajon_w": P_CAJON_MAX,
        "t_sala_c": T_SALA,
    }
    alto = dict(base)
    alto["area_venteo_mm2"] = AREA_BUSQUEDA_MAX_MM2
    falla_alto, mensaje = _falla_por_liston(alto)
    if falla_alto:
        return float("inf"), AREA_BUSQUEDA_MAX_MM2, mensaje

    falla_bajo, _ = _falla_por_liston(base)
    if not falla_bajo:
        return 0.0, 0.0, ""

    lo, hi = 0.0, AREA_BUSQUEDA_MAX_MM2
    for _ in range(PASOS_BISECCION_AREA):
        medio = (lo + hi) / 2.0
        candidato = dict(base)
        candidato["area_venteo_mm2"] = medio
        falla, _ = _falla_por_liston(candidato)
        if falla:
            lo = medio
        else:
            hi = medio
    area_base = math.ceil(hi / PASO_AREA_DISENO_MM2) * PASO_AREA_DISENO_MM2
    return hi, area_base, ""


# OJO CON LA UNIDAD: es area ADICIONAL, no total. Se le SUMA a los
# A_EF_BASE_MM2 = 3299 mm2 efectivos que el case ya tiene (ver _k() en
# aire_recinto_c). guarda_aire() del case publica el TOTAL, asi que las dos
# cifras NO se comparan tal cual: el 2026-09-04 dos sesiones distintas se
# equivocaron con eso el mismo dia, una en cada sentido, y salio un 14 % de
# desacuerdo entre los dos modelos donde hay un 1,3 %.
AREA_VENTEO_MIN_MM2, _AREA_BASE_MM2, _FALLO_AREA_MAX = _busca_area_minima()
P_BASE = {
    # ESTIMADO - hipotesis para #289, el papel del case fija la real.
    # Como no existe area finita, queda el extremo explorado por mandato.
    "area_venteo_mm2": _AREA_BASE_MM2,
    "p_recinto_w": P_RECINTO_MAX,  # W; papel sec.6.
    "p_cajon_w": P_CAJON_MAX,      # W; papel sec.6.
    "t_sala_c": T_SALA,            # C; chassis spec sec.3.1.
}
SOSTENIDO = _fixed_point(P_BASE)
# El mismo punto fijo con el C_D pesimista del case (0,55 contra 0,65). No es
# otro escenario: es LA SENSIBILIDAD del que hay, al coeficiente de descarga
# del venteo -- la constante que mas manda de todo el modelo y la unica sin
# medir (lo dice demo() en cada corrida). El case publica su salto termico con
# estos mismos dos extremos, y quien importe un techo de aqui necesita el
# rango por la misma razon: sin ensayo, un solo numero afirma de mas.
SOSTENIDO_CD_PESIMISTA = _fixed_point(P_BASE, cd=CD_TIRO_PESIMISTA)


def demo() -> None:
    print("calor_budget: cadena termica (fuentes inline en constantes)")
    escenarios = ((0.0, "cerrado"), (P_BASE["area_venteo_mm2"], "P_BASE"))
    print("  tabla: escenario | dT cajon | dT recinto | T | riel / placa / PSU3")
    for area, etiqueta in escenarios:
        p = {**P_BASE, "area_venteo_mm2": area}
        valores = _fixed_point(p)
        # Scenario rows are fixed points: recompute heat from those currents,
        # rather than displaying the full-load P_BASE heat beside them.
        p_rec = p_recinto_w(valores)
        p_caj = p_cajon_w(valores)
        t, dc, dr = _temperaturas(p_rec, p_caj, area)
        print(f"  {etiqueta}: {dc:.2f} K | {dr:.2f} K | {t:.2f} C")
        for riel in PLACA_A:
            psu = PSU3_A.get(riel)
            comparacion = "---" if psu is None else f"{psu:.3f}"
            estado = ("N/A" if psu is None else
                      ("PASA" if valores[riel] >= psu else "NO PASA"))
            print(f"    {riel}: {valores[riel]:.3f} / {PLACA_A[riel]:.3f} / "
                  f"{comparacion} ({100 * valores[riel] / PLACA_A[riel]:.1f}%, {estado})")
        if not any(valores.values()):
            print(f"    ^ CERO no es un redondeo: a {t:.1f} C se acabo la "
                  f"curva de la hoja (85 C) y no opera ningun modulo. Sin el "
                  f"venteo de D-F3 = A la caja no tiene punto de trabajo")
    tf, dcf, drf = _temperaturas(P_RECINTO_MAX, P_CAJON_MAX, 0.0)
    tp, dcp, drp = _temperaturas(P_RECINTO_MAX, P_CAJON_MAX,
                                 P_BASE["area_venteo_mm2"])
    print(f"  cadena full-load: cerrado dT cajon {dcf:.2f} K + dT recinto "
          f"{drf:.2f} K = {tf:.2f} C; P_BASE dT cajon {dcp:.2f} K + "
          f"dT recinto {drp:.2f} K = {tp:.2f} C")
    print(f"  AREA_VENTEO_MIN_MM2={AREA_VENTEO_MIN_MM2}")
    if math.isinf(AREA_VENTEO_MIN_MM2):
        print("!" * 72)
        print(f"FALLO: NINGUNA AREA FINITA HASTA "
              f"{AREA_BUSQUEDA_MAX_MM2:.0f} MM2 CUMPLE EL LISTON")
        print(f"DETALLE: {_FALLO_AREA_MAX.upper()}")
        print("!" * 72)
    base = SOSTENIDO
    cambios = {}
    factor = 1.0 + FRACCION_SENSIBILIDAD
    for nombre, kw in (("CD_TIRO", {"cd": CD_TIRO * factor}),
                       ("H_CONV_W_M2K", {"h_conv": H_CONV_W_M2K * factor}),
                       ("AREA_RECINTO_M2", {"area_recinto_m2": AREA_RECINTO_M2 * factor})):
        v = _fixed_point(P_BASE, **kw)
        cambios[nombre] = max(abs(v[r] - base[r]) for r in PLACA_A)
    dominante = max(cambios, key=cambios.get)
    print(f"  sensibilidad +10%: {cambios}; dominante={dominante}")
    print(f"  ESTIMADO: {len(ESTIMADOS)} (incluye P_BASE); HUECO: {len(HUECOS)}")


def _corre_contrato() -> None:
    """Corre todos los test_* y reune los rojos contractuales al final.

    Corre tambien el contrato de curvas.py: gates.py recoge por glob
    `*_budget.py` y `check_*.py`, asi que ni curvas.py ni test_curvas.py
    entran solos. Este presupuesto es su consumidor y el que responde de que
    sus puntos sigan siendo los de la hoja."""
    import importlib.util
    fallos: list[tuple[str, str]] = []
    for fichero in ("test_curvas.py", "test_calor_budget.py"):
        test_path = os.path.join(DIR, fichero)
        spec = importlib.util.spec_from_file_location(fichero[:-3], test_path)
        tests = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(tests)
        for nombre, fn in sorted(vars(tests).items()):
            if nombre.startswith("test_") and callable(fn):
                try:
                    fn()
                except AssertionError as exc:
                    fallos.append((nombre, str(exc)))
                    print(f"ROJO {nombre}: {exc}")
    if fallos:
        resumen = "; ".join(f"{nombre}: {mensaje}" for nombre, mensaje in fallos)
        raise AssertionError(f"contrato calor: {len(fallos)} rojo(s): {resumen}")
    print("OK: calor_budget.py")


def main() -> None:
    demo()
    _corre_contrato()


if __name__ == "__main__":
    main()
