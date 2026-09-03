"""Seis fugas y los Y2 de D-F5, contra el limite de la norma.

    python fuga_budget.py            (sale con codigo 2: HUECO declarado)

## Por que existe

Seis modulos con su fuga a PE **suman**, y D-F5 anade seis Y2 mas que tambien
fugan. El papel sec.4.1 estima el total en ~1,4 mA y lo llama "el no-problema"
porque el limite de la norma esta "un orden de magnitud por encima". Este guion
hace la cuenta con las condiciones de medida de la norma --1,1 veces la tension
nominal, y la frecuencia peor-- y sale bastante mas apretado que eso.

Y hace la otra cuenta, que es la tension real de D-F5: **el Y2 grande cierra
mejor el modo comun y fuga mas**. Aqui ese compromiso tiene un numero en vez de
una opinion.

## Los tres hallazgos

**1. La fuga no es "un orden de magnitud" por debajo del limite: es el 87 %.**
Con la tension de ensayo de la norma (253 V, o sea 1,1 x 230) y 60 Hz, los seis
modulos ponen 1,37 mA, los seis Y2 de D-F5 a 2,2 nF ponen 1,26 y los dos del
filtro de red 0,42: **3,05 de 3,5 mA**. El margen que queda no da para subir
el Y2 mucho mas, y el guion despeja el maximo: 2,99 nF por modulo.

**2. D-F5 ES UN MECANISMO DE MEGAHERCIOS, NO DE 65 kHz.** El papel justifica el
Y2 local diciendo que "el lazo de modo comun se cierre en centimetros ... y no
por los hilos de la estrella". Los dos caminos van EN PARALELO --la corriente
se reparte por impedancia, igual que los retornos de `ground_budget.py`-- asi
que lo que D-F5 compra no es un camino mejor: es DESVIAR corriente del camino
que pasa por donde vive la cadena de tono. A 65 kHz los dos acaban en un
condensador parecido y los 300 nH de treinta centimetros de hilo pesan 0,12 ohm
contra los 1113 del Y2: la corriente se parte por la mitad y el Y2 local desvia
1,5 veces. A 20 MHz desvia 14,2. Lo que sostiene la decision son los flancos,
no la fundamental.

Y hay una banda, alrededor de la resonancia serie del hilo con los Y2 del
filtro (~4,4 MHz), donde el camino LARGO es de baja impedancia y D-F5 casi no
desvia nada: el peor punto desvia 1,00 veces. No es una mejora uniforme, y
donde cae esa banda depende de parasitos ESTIMADO. Va aseverado para que no se
pueda leer al reves, y quien lo arbitra es la medida con los seis encendidos.

**3. LA NOTA DEL FABRICANTE NO DICE LO QUE EL PAPEL LE ATRIBUYE.** El papel
sec.4.2 cita "EMI testing of component power supplies" de Mean Well como la
fuente del mecanismo de D-F5. La nota (ya en el arbol, leida 2026-09-04) no
habla de condensadores Y: habla de que el modulo se monte sobre **una placa
metalica definida** y de que **el cable de salida vaya trenzado y apoyado sobre
esa placa**, y de que la EMC solo se puede comprobar con el sistema entero. O
sea que la Clase B que la hoja promete esta condicionada a DOS cosas de montaje
que no estaban escritas en ningun sitio del repo, y que este guion asevera como
requisitos.

## Lo que este guion NO cubre, y por que sale en HUECO

**La cifra de IEC 62368-1.** Es norma de pago y no esta en el arbol. Se trabaja
con **3,5 mA**, que es el limite de corriente de contacto para equipo de Clase
I conectable de tipo A, con su origen citado y marcado como valor de trabajo.
Un limite de fuga inventado es exactamente el tipo de numero que no se puede
publicar, asi que el guion sale en codigo 2 hasta que el texto de la norma se
consiga.

Tampoco cubre: la medida real con los seis encendidos (paso del bring-up), el
modo comun RADIADO, ni el reparto de la fuga entre L y N.
"""
from __future__ import annotations

import math
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
for _ruta in (DIR, os.path.join(DIR, "..", "..", "tools")):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
from canario import borde_rojo  # noqa: E402

# --- las condiciones de medida de la norma --------------------------------
V_RED_NOMINAL = 230.0
# IEC 62368-1 mide la corriente de contacto a 1,1 veces la tension nominal.
FACTOR_ENSAYO = 1.1
V_ENSAYO = V_RED_NOMINAL * FACTOR_ENSAYO
# La fuga capacitiva sube con la frecuencia, asi que 60 Hz es peor que 50 y es
# la que manda para un aparato que se vende en los dos sitios.
F_RED_PEOR_HZ = 60.0

# EL LIMITE. HUECO: IEC 62368-1 es de pago y no esta en el arbol. 3,5 mA es el
# limite de corriente de contacto para equipo de Clase I conectable de tipo A
# --el mismo que traia IEC 60950-1-- y se usa como VALOR DE TRABAJO, con su
# origen dicho y sin fingir que se leyo.
LIMITE_NORMA_MA = 3.5
LIMITE_ORIGEN = ("IEC 62368-1, corriente de contacto de equipo de Clase I "
                 "conectable de tipo A. VALOR DE TRABAJO: la norma es de pago "
                 "y no esta en el arbol")

# --- las seis fugas de los modulos ----------------------------------------
# Fila LEAKAGE CURRENT de las cuatro hojas: "< 0.25mA/277Vac". Es la unica
# tension que publican, y la fuga capacitiva escala con la tension.
FUGA_MODULO_MA_A_277 = 0.25
V_FUGA_MODULO_REF = 277.0
N_MODULOS = 6

# --- los Y2 de D-F5 -------------------------------------------------------
# Uno del borne de estrella de cada modulo al chasis, junto al modulo.
C_Y2_NF = 2.2
ESL_Y2_NH = 2.0            # ESTIMADO: patilla corta y via al chasis
# Los del filtro de red que ya existen (choke L_F con sus Y2, commit fec315e).
# ESTIMADO: no hay hoja del choke y el valor no esta escrito en ningun sitio.
C_Y2_FILTRO_NF = 2.2
N_Y2_FILTRO = 2

# --- el lazo de modo comun ------------------------------------------------
# Treinta centimetros de hilo hasta la estrella. ~1 nH/mm es la regla de un
# conductor suelto sobre un plano.
L_HILO_ESTRELLA_NH = 300.0
L_LAYOUT_LOCAL_NH = 5.0    # ESTIMADO: el Y2 pegado al modulo
F_CONMUTACION_HZ = 65e3
F_FLANCOS_HZ = 20e6

# --- lo que la nota del fabricante SI exige -------------------------------
# meanwell-emi-statement-2023-12-20.pdf, leida 2026-09-04. Dos requisitos de
# montaje, aseverados aqui porque es donde se comprueban:
#   "assemble the power supply on a defined metal plate"
#   "The output wire should be twisted and flatly placed on and within the
#    range of the metal plate"
# y la advertencia que los enmarca: "EMC cannot be tested independently. It
# needs to be installed into the end system and connected to the load."
MODULOS_SOBRE_PLACA_METALICA = True
SALIDAS_TRENZADAS_SOBRE_LA_PLACA = True
EMC_SE_VERIFICA_EN_EL_EQUIPO = True

ESTIMADOS = (
    f"C_Y2_FILTRO_NF={C_Y2_FILTRO_NF}: los Y2 del choke de red no tienen hoja "
    f"ni valor escrito en el repo",
    f"ESL_Y2_NH={ESL_Y2_NH} y L_LAYOUT_LOCAL_NH={L_LAYOUT_LOCAL_NH}: "
    f"parasitos de montaje",
    f"L_HILO_ESTRELLA_NH={L_HILO_ESTRELLA_NH}: 1 nH/mm sobre 30 cm de hilo",
)
HUECOS = (
    f"la cifra de IEC 62368-1. Se trabaja con {LIMITE_NORMA_MA} mA: "
    f"{LIMITE_ORIGEN}",
)


def fuga_capacitiva_ma(c_nf: float, v: float = V_ENSAYO,
                       f: float = F_RED_PEOR_HZ) -> float:
    """La corriente que un condensador a PE deja pasar a la frecuencia de red."""
    return 2.0 * math.pi * f * c_nf * 1e-9 * v * 1000.0


def fuga_modulos_ma(v: float = V_ENSAYO) -> float:
    """Los seis modulos, escalando su fuga publicada con la tension."""
    return N_MODULOS * FUGA_MODULO_MA_A_277 * v / V_FUGA_MODULO_REF


def fuga_y2_df5_ma(c_nf: float = C_Y2_NF, **kw) -> float:
    return N_MODULOS * fuga_capacitiva_ma(c_nf, **kw)


def fuga_y2_filtro_ma(**kw) -> float:
    return N_Y2_FILTRO * fuga_capacitiva_ma(C_Y2_FILTRO_NF, **kw)


def fuga_total_ma(c_y2_nf: float = C_Y2_NF, **kw) -> float:
    return (fuga_modulos_ma(**kw) + fuga_y2_df5_ma(c_y2_nf, **kw)
            + fuga_y2_filtro_ma(**kw))


def c_y2_maximo_nf() -> float:
    """El Y2 mas grande que todavia cabe bajo el limite. Es LA cifra que este
    presupuesto le entrega al BOM de la placa R."""
    sobra_ma = (LIMITE_NORMA_MA - fuga_modulos_ma() - fuga_y2_filtro_ma())
    if sobra_ma <= 0.0:
        return 0.0
    return sobra_ma / (N_MODULOS * 2.0 * math.pi * F_RED_PEOR_HZ
                       * V_ENSAYO * 1e-9 * 1000.0)


def z_local_ohm(f_hz: float, c_nf: float = C_Y2_NF) -> float:
    """El Y2 de D-F5 pegado al modulo: su capacidad y su montaje."""
    w = 2.0 * math.pi * f_hz
    return abs(w * (L_LAYOUT_LOCAL_NH + ESL_Y2_NH) * 1e-9
               - 1.0 / (w * c_nf * 1e-9))


def z_estrella_ohm(f_hz: float) -> float:
    """El camino largo: 30 cm de hilo hasta la estrella y de ahi al chasis
    por los Y2 del filtro de red."""
    w = 2.0 * math.pi * f_hz
    return abs(w * (L_HILO_ESTRELLA_NH + ESL_Y2_NH) * 1e-9
               - 1.0 / (w * C_Y2_FILTRO_NF * N_Y2_FILTRO * 1e-9))


def fraccion_por_la_estrella(f_hz: float, c_nf: float = C_Y2_NF) -> float:
    """Que parte de la corriente de modo comun se vuelve por la estrella.

    LOS DOS CAMINOS ESTAN EN PARALELO, no compiten: la corriente se reparte
    por impedancia, igual que los retornos de ground_budget.py. Lo que D-F5
    compra no es "un camino mejor" sino DESVIAR corriente del camino que pasa
    por donde vive la cadena de tono. Sin Y2 local, la fraccion es 1."""
    zl = z_local_ohm(f_hz, c_nf)
    ze = z_estrella_ohm(f_hz)
    return zl / (zl + ze)


def reduccion_df5(f_hz: float, **kw) -> float:
    """Cuantas veces baja la corriente por la estrella al poner el Y2 local."""
    return 1.0 / fraccion_por_la_estrella(f_hz, **kw)


def _guarda_fuga(p: dict[str, float]) -> None:
    """La fuga total contra el limite de la norma; su texto va al canario.

    LOS DOS LADOS son las dos caras de D-F5, y esta es la de la fuga: un Y2
    grande cierra mejor el modo comun y fuga mas. La otra cara la vigila
    _guarda_modo_comun()."""
    total = fuga_total_ma(p["c_y2_nf"])
    assert total < p["limite_ma"], (
        f"la fuga a PE suma {total:.3f} mA contra {p['limite_ma']:.2f} de la "
        f"norma: {fuga_modulos_ma():.3f} de los seis modulos + "
        f"{fuga_y2_df5_ma(p['c_y2_nf']):.3f} de los seis Y2 de D-F5 a "
        f"{p['c_y2_nf']:.1f} nF + {fuga_y2_filtro_ma():.3f} de los del filtro, "
        f"medidos a {V_ENSAYO:.0f} V y {F_RED_PEOR_HZ:.0f} Hz")


def _guarda_modo_comun(p: dict[str, float]) -> None:
    """La otra cara: un Y2 demasiado pequeno no cierra el lazo de los flancos.

    Se mide donde D-F5 de verdad compra algo --arriba, en los MHz-- y no a
    65 kHz, donde el cable no se nota."""
    g = reduccion_df5(F_FLANCOS_HZ, c_nf=p["c_y2_nf"])
    assert g >= p["ganancia_min"], (
        f"con {p['c_y2_nf']:.2f} nF el Y2 local solo desvia {g:.1f} veces la "
        f"corriente de modo comun a {F_FLANCOS_HZ / 1e6:.0f} MHz, y el "
        f"criterio es {p['ganancia_min']:.0f}: por debajo deja de ser el "
        f"camino corto y la corriente de modo comun se vuelve por los hilos de "
        f"la estrella, que es justo lo que D-F5 existe para evitar")


GANANCIA_MIN = 5.0

P_BASE = {
    "c_y2_nf": C_Y2_NF,
    "limite_ma": LIMITE_NORMA_MA,
    "ganancia_min": GANANCIA_MIN,
}


def _autocomprobacion() -> None:
    # 1. La fuga cabe bajo el valor de trabajo.
    _guarda_fuga(dict(P_BASE))
    # 2. Y el Y2 cierra el lazo donde importa.
    _guarda_modo_comun(dict(P_BASE))

    # 3. El hallazgo 1, aseverado: la fuga NO esta un orden de magnitud por
    #    debajo del limite. Si lo estuviera, el papel sec.4.1 tendria razon y
    #    este presupuesto seria un tramite.
    assert fuga_total_ma() > LIMITE_NORMA_MA / 10.0, (
        f"si la fuga ({fuga_total_ma():.3f} mA) estuviera de verdad un orden "
        f"de magnitud por debajo del limite ({LIMITE_NORMA_MA:.2f}), el "
        f"'no-problema' del papel sec.4.1 seria cierto y este guion sobraria")

    # 4. El hallazgo 2: D-F5 es de MHz. A 65 kHz los dos caminos acaban en un
    #    condensador parecido y el hilo casi no pesa, asi que la corriente se
    #    parte por la mitad; arriba, el hilo manda y el Y2 local se la lleva.
    g65 = reduccion_df5(F_CONMUTACION_HZ)
    g20 = reduccion_df5(F_FLANCOS_HZ)
    assert g65 < 3.0, (
        f"a {F_CONMUTACION_HZ / 1e3:.0f} kHz el Y2 local solo desvia "
        f"{g65:.2f} veces: si desviara de verdad ahi, el motivo que el papel "
        f"escribe --el lazo corto A 65 kHz-- se sostendria y este hallazgo no "
        f"existiria")
    assert g20 > 3.0 * g65, (
        f"D-F5 tiene que comprar en los MHz mucho mas que en la fundamental "
        f"({g20:.1f} contra {g65:.2f}): si no, no es un mecanismo de flancos y "
        f"su sitio en el papel es otro")
    # Y LO QUE NO SE PUEDE CALLAR: hay una banda, alrededor de la resonancia
    # serie del propio hilo con los Y2 del filtro, en la que el camino largo
    # es de BAJA impedancia y el Y2 local casi no desvia nada. Se busca, se
    # publica y se asevera que existe: taparla seria vender D-F5 como una
    # mejora uniforme, y no lo es.
    peor_f, peor_g = min(
        ((10.0 ** (4.0 + 4.0 * i / 400.0),
          reduccion_df5(10.0 ** (4.0 + 4.0 * i / 400.0))) for i in range(401)),
        key=lambda x: x[1])
    assert peor_g < 2.0, (
        f"el peor punto de la banda desvia {peor_g:.2f} veces en "
        f"{peor_f / 1e6:.2f} MHz: si D-F5 mejorara en TODA la banda, esta "
        f"advertencia sobraria y el modelo no estaria viendo la resonancia "
        f"del hilo con los Y2 del filtro")

    # 5. El hallazgo 3: lo que la nota del fabricante SI exige. Van como
    #    requisitos aseverados porque este es el unico sitio del arbol donde
    #    se comprueban.
    assert MODULOS_SOBRE_PLACA_METALICA, (
        "la nota EMI de Mean Well cualifica la Clase B con el modulo montado "
        "sobre 'a defined metal plate'. Si los seis no van contra la chapa, "
        "la Clase B que la hoja promete se midio en otro montaje")
    assert SALIDAS_TRENZADAS_SOBRE_LA_PLACA, (
        "la misma nota: 'The output wire should be twisted and flatly placed "
        "on and within the range of the metal plate'. El enlace R->C ya iba a "
        "ir trenzado por sec.4.2; esto lo convierte en requisito del "
        "fabricante y lo extiende a las SEIS salidas")
    assert EMC_SE_VERIFICA_EN_EL_EQUIPO, (
        "'EMC cannot be tested independently. It needs to be installed into "
        "the end system': la Clase B de la hoja no es la del instrumento")

    # 6. Los canarios, por biseccion y por el texto de cada aserto. Son las
    #    dos caras del compromiso de D-F5, y por eso van los dos.
    v = borde_rojo(_guarda_fuga, dict(P_BASE), "c_y2_nf", 0.0, 100.0,
                   "la fuga a PE suma")
    # El extremo bajo no puede ser 0,0: la impedancia de un condensador nulo
    # es infinita y la division revienta, y borde_rojo se traga la excepcion
    # como "no salta". Un canario que no muerde porque el modelo se rompio no
    # se distingue de uno que no muerde porque el aserto perdio los dientes.
    w = borde_rojo(_guarda_modo_comun, dict(P_BASE), "c_y2_nf", 1e-3, 100.0,
                   "deja de ser el camino corto")
    print(f"  canario: por encima de {v:.2f} nF de Y2, la fuga se pasa")
    print(f"  canario: por debajo de {w:.3f} nF de Y2, el lazo de modo comun "
          f"deja de cerrarse en corto")
    assert w < C_Y2_NF < v, (
        f"el Y2 elegido ({C_Y2_NF:.1f} nF) tiene que caer ENTRE los dos "
        f"bordes ({w:.3f} y {v:.2f}): si no, no hay valor que cumpla las dos "
        f"caras de D-F5")
    assert abs(v - c_y2_maximo_nf()) < 0.05, (
        f"el canario da {v:.3f} nF de maximo y la cuenta directa "
        f"{c_y2_maximo_nf():.3f}: la guarda y el modelo no miden lo mismo")


def demo() -> int:
    print("fuga_budget: seis fugas y seis Y2 contra el limite de la norma\n")

    print(f"  condiciones de medida: {V_ENSAYO:.0f} V "
          f"({FACTOR_ENSAYO:.1f} x {V_RED_NOMINAL:.0f} nominales) y "
          f"{F_RED_PEOR_HZ:.0f} Hz,")
    print("  que es la frecuencia peor de las dos en las que esto se vende.")

    print(f"\n  {'concepto':38s} {'mA':>7s}")
    print(f"  {'seis modulos (< 0,25 mA/277 Vac, hoja)':38s} "
          f"{fuga_modulos_ma():7.3f}")
    print(f"  {'seis Y2 de D-F5 a ' + f'{C_Y2_NF:.1f} nF':38s} "
          f"{fuga_y2_df5_ma():7.3f}")
    print(f"  {f'{N_Y2_FILTRO} Y2 del filtro de red (ESTIMADO)':38s} "
          f"{fuga_y2_filtro_ma():7.3f}")
    print(f"  {'TOTAL':38s} {fuga_total_ma():7.3f}")
    print(f"  {'limite de trabajo':38s} {LIMITE_NORMA_MA:7.2f}")
    print(f"  {'ocupacion':38s} "
          f"{fuga_total_ma() / LIMITE_NORMA_MA:6.0%}")
    print("  El papel sec.4.1 estima ~1,4 mA y lo llama 'el no-problema' "
          "porque el")
    print("  limite estaria 'un orden de magnitud por encima'. Con las "
          "condiciones")
    print(f"  de la norma son {fuga_total_ma():.2f} mA: el "
          f"{fuga_total_ma() / LIMITE_NORMA_MA:.0%} del limite, no el 10 %.")
    print(f"  Y2 MAXIMO que todavia cabe: {c_y2_maximo_nf():.2f} nF por modulo.")

    print("\n  la otra cara de D-F5: cuanta corriente de modo comun desvia")
    print("  (los dos caminos van en PARALELO y la corriente se reparte por")
    print("   impedancia, igual que los retornos de ground_budget.py)")
    print(f"  {'f':>10s} {'Y2 local':>10s} {'por estrella':>13s} "
          f"{'% estrella':>11s} {'veces':>8s}")
    for f in (F_CONMUTACION_HZ, 200e3, 1e6, 5e6, F_FLANCOS_HZ):
        etiqueta = f"{f / 1e3:.0f}k" if f < 1e6 else f"{f / 1e6:g}M"
        print(f"  {etiqueta:>10s} {z_local_ohm(f):9.2f}o "
              f"{z_estrella_ohm(f):12.2f}o "
              f"{fraccion_por_la_estrella(f):10.1%} {reduccion_df5(f):8.2f}")
    f_res = 1.0 / (2 * math.pi * math.sqrt(
        (L_HILO_ESTRELLA_NH + ESL_Y2_NH) * 1e-9
        * C_Y2_FILTRO_NF * N_Y2_FILTRO * 1e-9))
    peor_f, peor_g = min(
        ((10.0 ** (4.0 + 4.0 * i / 400.0),
          reduccion_df5(10.0 ** (4.0 + 4.0 * i / 400.0))) for i in range(401)),
        key=lambda x: x[1])
    print(f"  A {F_CONMUTACION_HZ / 1e3:.0f} kHz los dos caminos acaban en un "
          f"condensador parecido y el hilo")
    print(f"  no pesa ({2 * math.pi * F_CONMUTACION_HZ * L_HILO_ESTRELLA_NH * 1e-9:.2f}"
          f" ohm de 30 cm contra {z_local_ohm(F_CONMUTACION_HZ):.0f} del Y2): "
          f"la corriente se")
    print("  parte por la mitad. Arriba, pasada la resonancia del hilo con "
          "los Y2 del")
    print(f"  filtro (~{f_res / 1e6:.1f} MHz), el hilo manda y el Y2 local se "
          f"la lleva.")
    print("  Y LO QUE NO SE PUEDE CALLAR: alrededor de esa resonancia el "
          "camino largo")
    print("  es de BAJA impedancia y D-F5 casi no desvia nada: el peor punto "
          "esta en")
    print(f"  {peor_f / 1e6:.2f} MHz y solo desvia {peor_g:.2f} veces. D-F5 no "
          f"es una mejora uniforme, y")
    print("  donde cae esa banda depende de parasitos ESTIMADO: quien lo")
    print("  arbitra es la medida con los seis encendidos del bring-up.")
    print("  La decision D-F5 es buena; el motivo que el papel escribe --'que")
    print("  el lazo se cierre en centimetros' a 65 kHz-- no es el que la")
    print("  sostiene. Lo que la sostiene son los flancos.")

    print("\n  lo que la nota del fabricante SI exige (y el papel no recogia):")
    print("    meanwell-emi-statement-2023-12-20.pdf, leida 2026-09-04")
    print("    - 'assemble the power supply on a defined metal plate'")
    print("    - 'The output wire should be twisted and flatly placed on and")
    print("       within the range of the metal plate'")
    print("    - 'EMC cannot be tested independently. It needs to be installed")
    print("       into the end system and connected to the load'")
    print("    Ninguna de las tres habla de condensadores Y. Son requisitos de")
    print("    MONTAJE, y de ellos depende la Clase B que la hoja promete.")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}; HUECO: {len(HUECOS)}")
    for e in ESTIMADOS:
        print(f"    ESTIMADO - {e}")
    for h in HUECOS:
        print(f"    HUECO    - {h}")

    _autocomprobacion()

    print()
    print(f"HUECO: el limite de fuga sale de un VALOR DE TRABAJO y no de la "
          f"norma leida. {LIMITE_ORIGEN}. Con el, la fuga total "
          f"({fuga_total_ma():.2f} mA) ocupa el "
          f"{fuga_total_ma() / LIMITE_NORMA_MA:.0%} y el Y2 maximo por modulo "
          f"son {c_y2_maximo_nf():.2f} nF. Se cierra consiguiendo el texto de "
          f"IEC 62368-1 y volviendo a correr; si la cifra fuera otra, el Y2 se "
          f"mueve con ella.")
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
