"""La fuente v5: un ladrillo de catalogo afuera y la conversion adentro.

    python ladrillo_budget.py        (sale con codigo 2: HUECOS declarados)

## Por que existe

Samuel decidio el 2026-09-05 sacar la etapa AC-DC de la caja de madera. La v4
mete seis modulos Mean Well, la entrada de red, el fusible, la NTC de arranque,
el choke de modo comun y los Y2 al chasis DENTRO de un instrumento de madera; y
ademas los mete en un recinto de acero de 338,6 x 176,6 x 83 mm que ocupa el
30 % del suelo interior.

La v5 compra ese trozo hecho --un ladrillo AC-DC certificado, una tension-- y
deriva los rieles dentro con DC-DC. Este guion pone las cifras.

## Lo que este guion contesta, y que nadie mas contestaba

**1. El calor que se va NO es el que la gente supone.** El calor de una caja lo
hacen las CARGAS, y las cargas no se mudan. Lo que se muda es la perdida de
CONVERSION. Dicho al reves y en su forma mas limpia:

    todo lo que baja por el cordon acaba en calor dentro de la caja.

Asi que el calor del cajon es, exactamente, la potencia de SALIDA del ladrillo.
Lo que se queda fuera es la perdida AC-DC del propio ladrillo, y nada mas.

**2. La tension cruda deja de ser un dato de catalogo, y eso da holgura a la
cascada.** Cuando se escribio este guion (05-09) el argumento era `U2`: llevaba
desde el 03-09 en -170 mV y no parecia tener salida por piezas. El 06-09 se
firmo **D-F9** y `U2` paso a LT3015: hoy cierra en **+536 mV con el crudo de
catalogo**, sin que esta arquitectura haga nada. El regalo se cobro por otra
caja.

Lo que la tension cruda sigue comprando es holgura en **`U1`**, que a 15,0 V es
el peor riel con +330 mV sobre una incertidumbre de modelo de 127, y a 15,5 se
va a +811. Ese es el argumento vivo de D-V3, y cuesta lo mismo: 0,33 W mas de
disipacion en U2 (medidos los dos en el corner alto, que es el unico modo
honesto de compararlos). La diferencia es que antes se pagaban por cerrar un
rojo y ahora por ensanchar un verde, y esto es un papel que va de bajar calor.
Ver la enmienda del 07-09 en la sec.5 del papel.

**3. Declarado y censado se separan mas que nunca.** D-B2 declara 500 mA/riel
de rack (firmado 2026-09-05); la cascada declara 650 mA/riel (D-F1) contra un
censo de 334; y el digital declara el maximo de la hoja a 125 C contra un tipico
7,4 veces menor (#256). El ladrillo se dimensiona por lo DECLARADO, que es lo
correcto, pero el venteo del case se ha estado encargando contra esa misma cifra
sin decir que la separacion es de casi el doble.

## Lo que NO decide este guion

La topologia de cada convertidor, las piezas, el conector y la secuencia de
arranque. Eso es del papel y de su plan. Aqui solo hay potencias, perdidas y
margenes.
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(DIR, "..", "v4")
if V4 not in sys.path:
    sys.path.insert(0, V4)

# --- lo que la v4 ya decidio y aqui NO se vuelve a escribir ----------------
# Se importan para que un cambio alli se vea aqui, en vez de quedarse pegado.
from calor_budget import CAJON_DIGITAL_A, V_RIEL          # noqa: E402
import margen_budget as mb                                 # noqa: E402

# --- D-B2, firmada el 2026-09-05 -------------------------------------------
# "Los otros modulos los vamos a fabricar nosotros tambien" (Samuel, 04-09). La
# fila de abajo deja de ser un censo de invitados de mercado y pasa a ser un
# presupuesto de diseno propio. El liston "PSU3 o superior" se firmo pensando en
# terceros y ese ya no es el supuesto.
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
# fuente "cuando la pieza tenga nombre" y la pieza sigue sin nombre. Va con
# retorno dedicado, no por el bus (su corriente son 9-11 veces I_MASA_SAM17).
PANTALLA_A = 0.550        # HUECO: 450-550 segun panel, 600 el backpack Adafruit

# --- el ladrillo ------------------------------------------------------------
# 24 V y no 19: los dos bucan bien a los 15,5 V de la cascada, pero a 24 el
# cordon lleva menos corriente y sobra margen para el arranque de la cascada.
# Es una PROPUESTA de este papel (D-V2), no un dato.
V_LADRILLO = 24.0
# Rendimiento AC-DC del ladrillo. No entra en el calor de la caja --se disipa
# FUERA-- pero decide lo que se le pide a la red. ESTIMADO de clase VI.
ETA_LADRILLO = 0.88

# --- los convertidores de dentro -------------------------------------------
# ESTIMADO en los tres casos. Un buck sincrono bien dimensionado a estas
# potencias esta en 90-93 %; el inversor y el aislado pagan su topologia.
ETA_BUCK = 0.90
ETA_INVERSOR = 0.85       # buck-boost inversor para el -12 de rack
ETA_AISLADO = 0.85        # flyback de doble salida para el crudo de la cascada

# --- la tension cruda de la cascada: LA DECISION QUE CIERRA U2 -------------
# mb.V_NOM son los 15,0 V de la hoja del IRM. Con DC-DC propio se elige.
V_CRUDO_CASCADA = 15.5
TOL_CRUDO = 0.025         # conservador: un DC-DC nuestro deberia hacerlo mejor

ESTIMADOS = (
    f"ETA_BUCK={ETA_BUCK}: buck sincrono a estas potencias, sin pieza elegida",
    f"ETA_INVERSOR={ETA_INVERSOR}: buck-boost inversor, sin pieza elegida",
    f"ETA_AISLADO={ETA_AISLADO}: flyback de doble salida, sin pieza elegida",
    f"ETA_LADRILLO={ETA_LADRILLO}: clase VI generica; no entra en el calor del case",
    f"TOL_CRUDO={TOL_CRUDO}: se supone la MISMA tolerancia que un IRM de catalogo",
)


def rieles() -> list[dict]:
    """Cada convertidor de dentro: que entrega y que pierde.

    El +12 de rack lleva DOS cargas por cables distintos: el bus de la fila de
    abajo y la pantalla con su retorno dedicado. Van juntas en el convertidor y
    separadas en el cableado, que es lo que pide pantalla-motor.
    """
    v_alto = V_CRUDO_CASCADA * (1 + TOL_CRUDO)   # el peor caso PARA EL CALOR
    return [
        {"nombre": "+12 rack (bus fila B + pantalla)", "v": V_RIEL["rack+12"],
         "a": FILA_B_A + PANTALLA_A, "eta": ETA_BUCK},
        {"nombre": "-12 rack (bus fila B)", "v": V_RIEL["rack-12"],
         "a": FILA_B_A, "eta": ETA_INVERSOR},
        {"nombre": "+5 rack (bus fila B)", "v": V_RIEL["rack+5"],
         "a": FILA_B_A, "eta": ETA_BUCK},
        {"nombre": "+5 digital (4 x N657 + host USB)", "v": 5.0,
         "a": DIGITAL_A, "eta": ETA_BUCK},
        {"nombre": "crudo +cascada (a U1)", "v": v_alto,
         "a": CASCADA_A, "eta": ETA_AISLADO},
        {"nombre": "crudo -cascada (a U2)", "v": v_alto,
         "a": CASCADA_A, "eta": ETA_AISLADO},
    ]


def entregado_w() -> float:
    return sum(r["v"] * r["a"] for r in rieles())


def perdida_dcdc_w() -> float:
    return sum(r["v"] * r["a"] * (1.0 / r["eta"] - 1.0) for r in rieles())


def salida_ladrillo_w() -> float:
    """Lo que baja por el cordon. ES, EXACTAMENTE, el calor del cajon.

    Nada de lo que entra por el cordon sale de la caja por otro sitio: la
    potencia de audio son milivatios y no cambia la tercera cifra.
    """
    return entregado_w() + perdida_dcdc_w()


def calor_del_cajon_w() -> float:
    return salida_ladrillo_w()


def pedido_a_la_red_w() -> float:
    """Lo que el ladrillo pide a la red. La diferencia se disipa FUERA."""
    return salida_ladrillo_w() / ETA_LADRILLO


def corriente_del_cordon_a() -> float:
    return salida_ladrillo_w() / V_LADRILLO


def caida_cordon_v(ohm_por_m: float, largo_m: float) -> float:
    """Ida y vuelta. El cordon es de DOS hilos: no hay rieles en el."""
    return 2.0 * ohm_por_m * largo_m * corriente_del_cordon_a()


def margen_cascada_v(reg: str, *, v_nom: float = V_CRUDO_CASCADA,
                     tol: float = TOL_CRUDO) -> float:
    """El margen de U1/U2 con la tension cruda que ESTE papel elige.

    Reusa margen_budget entero --la cadena de tolerancia, deriva, rizado y
    caida en el LC-- y solo le cambia el nominal y su tolerancia. Si aquel
    modelo cambia, este numero cambia con el.
    """
    nom0, tol0 = mb.V_NOM, mb.TOL_FRAC
    try:
        mb.V_NOM, mb.TOL_FRAC = v_nom, tol
        return mb.margen_v(reg)
    finally:
        mb.V_NOM, mb.TOL_FRAC = nom0, tol0


SETPOINT_V = {"U1": 13.10, "U2": 12.90}


def quema_pre_regulador_w(reg: str, *, v_nom: float = V_CRUDO_CASCADA,
                          tol: float = TOL_CRUDO) -> float:
    """Lo que U1 o U2 disipa: la caida por la corriente, en el corner ALTO.

    El corner que aprieta el margen es el BAJO; el que aprieta el calor es el
    ALTO. No son el mismo, y usar uno para las dos cosas es como se publica un
    margen que no existe o un calor que no se disipa.

    Y LA TRAMPA DE VERDAD ES COMPARAR: al escribir el papel compare la quema
    NUEVA en el corner alto contra la VIEJA en el corner bajo, y salio "+0,98 W"
    donde son +0,33. Por eso `v_nom` es un parametro y no la constante del
    modulo: para que el antes y el despues se midan en el MISMO corner o no se
    puedan medir.
    """
    return ((v_nom * (1 + tol)) - SETPOINT_V[reg]) * CASCADA_A


def censo_optimista_w() -> float:
    """El mismo cajon con los censos en vez de las declaraciones.

    No es un escenario de diseno: es la MEDIDA de cuanto separa lo declarado de
    lo que el instrumento va a pedir. Si esa separacion es grande, encargar el
    venteo contra lo declarado es una decision, no una consecuencia.
    """
    v_alto = V_CRUDO_CASCADA * (1 + TOL_CRUDO)
    filas = [
        (V_RIEL["rack+12"], 0.300 + PANTALLA_A, ETA_BUCK),
        (V_RIEL["rack-12"], 0.300, ETA_INVERSOR),
        (V_RIEL["rack+5"], 0.300, ETA_BUCK),
        (5.0, DIGITAL_TYP_A, ETA_BUCK),
        (v_alto, CASCADA_CENSO_A, ETA_AISLADO),
        (v_alto, CASCADA_CENSO_A, ETA_AISLADO),
    ]
    return sum(v * a / eta for v, a, eta in filas)


HUECOS = (
    "La pantalla de 7 pulgadas sigue sin pieza. pantalla-motor l.250-256 manda "
    "su fila 'cuando la pieza tenga nombre'. Aqui entra con 550 mA de +12 V, "
    "que es el centro del rango 450-550 que aquel papel cita (600 el backpack "
    "de Adafruit). Son 6,6 W de los que este presupuesto declara: no es un "
    "redondeo",
    "Ningun convertidor tiene pieza elegida, asi que los tres rendimientos son "
    "ESTIMADO. La perdida DC-DC entera se mueve con ellos, y es el unico "
    "termino de este presupuesto que no esta anclado a una hoja",
    "#256 sigue abierto: el digital entra por su maximo a TJ=125 C porque el "
    "punto de trabajo real (85 C) no esta publicado. Entre ese maximo y el "
    "tipico hay 3,0 veces de corriente",
)


def _autocomprobacion() -> None:
    """Lo que tiene que seguir siendo verdad, comprobado y no prometido."""
    # 1. La identidad que sostiene el papel entero: el calor del cajon ES la
    #    salida del ladrillo. Si algun dia alguien mete aqui un termino que no
    #    baje por el cordon, esto salta.
    assert abs(calor_del_cajon_w() - salida_ladrillo_w()) < 1e-12, (
        "el calor del cajon dejo de ser la salida del ladrillo: o entra "
        "potencia por otro sitio o sale por otro sitio, y hay que decir cual")
    # 2. El ladrillo le pide a la red MAS de lo que entrega, nunca menos.
    assert pedido_a_la_red_w() > salida_ladrillo_w(), "rendimiento >= 1"
    # 3. La tension cruda elegida tiene que cerrar la cascada entera.
    #    OJO, PERDIO DIENTES CON D-F9 (06-09): se escribio para cazar a quien
    #    bajara V_CRUDO_CASCADA "para que caliente menos", y mordia porque a
    #    15,0 V el LM2991 daba -170 mV. Con el LT3015 da +536, asi que a 15,0
    #    ya no salta nadie. Sigue siendo la propiedad correcta que vigilar --y
    #    volveria a morder si alguien revirtiera la pieza-- pero hoy el que
    #    aprieta es U1 (+330 a 15,0 V), no U2.
    for reg in ("U1", "U2"):
        assert margen_cascada_v(reg) > 0, (
            f"{reg} sigue sin margen con {V_CRUDO_CASCADA} V de crudo "
            f"({margen_cascada_v(reg)*1000:+.0f} mV). Que la cascada regule es "
            f"la razon de elegir la tension cruda; si no lo hace, no vale la pena")
    # 4. Y que el margen MEJORE con la tension, que es la direccion del arreglo.
    assert margen_cascada_v("U2", v_nom=16.0) > margen_cascada_v("U2", v_nom=15.0), (
        "subir el crudo no mejora el margen: el modelo esta al reves")
    # 5. Lo declarado no puede quedar por debajo del censo, o la declaracion no
    #    declara nada.
    assert censo_optimista_w() < salida_ladrillo_w(), (
        "el censo pide mas que lo declarado: la declaracion no cubre el uso")


def demo() -> int:
    print("La fuente v5: el ladrillo afuera, la conversion adentro\n")

    print("  los rieles de dentro, cada uno con su convertidor:")
    print(f"    {'riel':<38} {'V':>7} {'A':>7} {'sale':>8} {'pierde':>8}")
    for r in rieles():
        w = r["v"] * r["a"]
        print(f"    {r['nombre']:<38} {r['v']:>7.2f} {r['a']:>7.3f} "
              f"{w:>7.2f} W {w*(1/r['eta']-1):>6.2f} W")
    print(f"    {'-'*38} {'-'*7} {'-'*7} {'-'*8} {'-'*8}")
    print(f"    {'entregado a las cargas':<38} {'':>7} {'':>7} "
          f"{entregado_w():>7.2f} W")
    print(f"    {'perdido convirtiendo, DENTRO':<38} {'':>7} {'':>7} "
          f"{'':>8} {perdida_dcdc_w():>6.2f} W")

    print("\n  el ladrillo:")
    print(f"    tension                        {V_LADRILLO:>7.1f} V   (D-V2, propuesta)")
    print(f"    salida, o sea lo que baja      {salida_ladrillo_w():>7.2f} W")
    print(f"    corriente del cordon           {corriente_del_cordon_a():>7.2f} A")
    print(f"    lo que le pide a la red        {pedido_a_la_red_w():>7.2f} W")
    print(f"    se disipa FUERA de la caja     "
          f"{pedido_a_la_red_w()-salida_ladrillo_w():>7.2f} W")

    print(f"\n  EL CALOR DEL CAJON = LA SALIDA DEL LADRILLO = "
          f"{calor_del_cajon_w():.2f} W")
    print("    Todo lo que baja por el cordon acaba en calor dentro. Lo unico")
    print("    que se queda fuera es la perdida AC-DC del ladrillo.")
    print(f"    La v4 declaraba 139,31 W: son "
          f"{100*(1-calor_del_cajon_w()/139.31):.0f} % menos.")

    print("\n  y con los CENSOS en vez de las declaraciones:")
    print(f"    fila a 300 mA, cascada a {CASCADA_CENSO_A*1000:.0f} mA, digital al tipico")
    print(f"    calor del cajon                {censo_optimista_w():>7.2f} W")
    print(f"    lo declarado lo separa en      "
          f"{salida_ladrillo_w()/censo_optimista_w():>7.2f} veces")

    print("\n  EL REGALO: la tension cruda cierra U2")
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
        et = "  <- el crudo de hoy; era el rojo de U2 hasta D-F9" if nom == 15.0 else (
             "  <- D-V3, propuesta" if nom == V_CRUDO_CASCADA else "")
        print(f"    {nom:>6.1f} V {llega:>8.3f} V {m1:>+10.0f} {m2:>+10.0f} "
              f"{q:>8.2f} W{et}")
    print(f"    La columna de la derecha es el precio, y va en el MISMO corner "
          f"que\n    la de al lado no va: cerrar U2 cuesta "
          f"{quema_pre_regulador_w('U2') - quema_pre_regulador_w('U2', v_nom=15.0):+.2f} W "
          f"en U2, no el\n    +0,98 que sale de comparar el corner alto contra el bajo.")

    print("\n  el cordon, de dos hilos (no lleva rieles, lleva UNA tension):")
    print(f"    {'calibre':>9} {'ohm/m':>8} {'1 m':>9} {'2 m':>9}")
    for et, ohm in (("18 AWG", 0.0210), ("16 AWG", 0.0132), ("14 AWG", 0.0083)):
        c1 = caida_cordon_v(ohm, 1.0)
        c2 = caida_cordon_v(ohm, 2.0)
        print(f"    {et:>9} {ohm:>8.4f} {c1*1000:>7.0f} mV {c2*1000:>7.0f} mV")
    print(f"    Sobre {V_LADRILLO:.0f} V esa caida es el "
          f"{100*caida_cordon_v(0.0132, 2.0)/V_LADRILLO:.1f} % con 16 AWG y 2 m, y")
    print("    la absorbe el convertidor de dentro: NO llega a la cascada. Es la")
    print("    diferencia con bajar los rieles hechos, donde esa caida caia")
    print("    justo encima del margen de U1/U2.")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}; HUECO: {len(HUECOS)}")
    for e in ESTIMADOS:
        print(f"    ESTIMADO - {e}")
    for h in HUECOS:
        print(f"    HUECO    - {h}")

    _autocomprobacion()

    print(f"\nHUECO: los tres rendimientos de los convertidores son ESTIMADO y "
          f"mueven\n  {perdida_dcdc_w():.2f} W de los {salida_ladrillo_w():.2f} "
          f"que este presupuesto declara. Se cierran eligiendo\n  las piezas, que "
          f"es trabajo del plan de esta v5. Y la pantalla de 7\" sigue\n  sin "
          f"pieza: sus 6,6 W entran por una cita, no por una hoja.")
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
