"""El fusible de red: lo manda el rearranque en caliente, no el arranque frio.

    python fusible_budget.py         (sale con codigo 2: HUECO declarado)

## Por que existe

La v3 llevaba 1,6 A T calculado sobre 0,72 A rms de un toroide. La fuente v4
son seis modulos conmutados en paralelo y el numero que los gobierna cambio de
orden de magnitud, por una razon que el papel sec.5 dice bien: **la corriente
de red es la fila "AC CURRENT (Typ.)" de la hoja, no vatios entre voltios**.
Un flyback con rectificador y condensador tiene factor de potencia 0,25-0,30 y
esa division daba 0,94 A donde hay casi cuatro.

Y hay un caso que la v3 no podia tener porque su inrush lo ponia el toroide:
el **rearranque en caliente**. En frio la NTC limita; en un microcorte, con la
NTC todavia caliente, su resistencia es una fraccion de la de arranque y el
pico es un orden de magnitud mayor. Ese es el que dimensiona.

## Los cuatro hallazgos

**1. El papel suma 3,9 A rms y son 4,4.** La fila AC CURRENT de la IRM-45 es
una celda unica para toda la serie --0,9 A/230 Vac para los cuatro modelos-- y
D-F7 subio PS5 de IRM-20-5 a IRM-45-5. El papel sec.5 sigue sumando el 0,4 de
la IRM-20-5: 0,4+0,4+0,9+0,9+**0,4**+0,9 = 3,9. Con la hoja de la pieza que
ahora esta puesta son 0,4+0,4+0,9+0,9+**0,9**+0,9 = **4,4 A**. Lo mismo con el
inrush: 285 A sumados en el papel, **320** con la IRM-45-5.

**2. El 4 A T que el papel deja como hipotesis no llega POR NINGUNO DE LOS DOS
CAMINOS.** A la carga del liston son 3,25 A rms; al 70 % del calibre y con el
derratado de los 68,9 C del recinto piden 5,34 A. Y su I2t de fusion --77 A2s,
escalando con In^2 desde los 190 de la hoja-- tampoco aguanta el rearranque:
17,4 A2s contra 15,3 admisibles. Sale **6,3 A T**, que es exactamente el tope
que el plan de esta tanda ponia por arriba: el resultado aterriza en el borde
de su propia cota, y eso hay que decirlo en vez de celebrarlo.

(La tabla de tiempo-corriente de la hoja garantiza 60 min sin abrir a 1,5 x In,
que NO es "para siempre": de ahi el 70 % de regimen permanente, que es practica
de aplicacion y va declarado como ESTIMADO.)

**3. Subir a 6,3 A T arregla el rearranque en caliente de paso**, porque el
I2t de fusion escala con In^2. Con 190 A2s de la hoja, el rearranque se queda
en un porcentaje pequeno en vez del 18-53 % que el papel calculaba para el
1,6 A T.

**4. EL FUSIBLE DE LA HOJA NO SIRVE, Y NO POR SU CALIBRE.** La FST 5x20 es
"L = Low Breaking Capacity (Glass Tube)" y su poder de corte a 6,3 A es 10 x In
= 63 A. La corriente de cortocircuito disponible en el enchufe, con la
impedancia de referencia de la norma, son ~490 A. Un fusible de vidrio de bajo
poder de corte delante de eso no interrumpe: se vaporiza y mantiene el arco.
Hace falta uno CERAMICO de alto poder de corte (1500 A tipicos). La hoja que
esta en el arbol sirve para los tiempos y el I2t --que son de IEC 60127-2 y
valen para cualquier T de ese calibre-- y NO para la pieza. Ese es el hueco.

## Lo que este guion NO cubre

  * La curva I2t del fusible CERAMICO que se compre. La de la hoja de vidrio
    se usa como referencia de la norma, no como la de la pieza.
  * El MOV y el choke, que se redimensionan en el mismo sitio (papel sec.5) y
    no tienen hoja todavia.
  * La proteccion contra defecto a tierra: eso es el diferencial de la
    instalacion, no este fusible.
"""
from __future__ import annotations

import math
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
for _ruta in (DIR, os.path.join(DIR, "..", "..", "tools")):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
from calor_budget import (P_BASE, PLACA_A, SOSTENIDO,  # noqa: E402
                          aire_recinto_c, p_cajon_w, p_recinto_w)
from canario import borde_rojo  # noqa: E402
from margen_budget import I_CASCADA_A  # noqa: E402

# --- la red -----------------------------------------------------------------
V_RED_RMS = 230.0
V_RED_PICO = V_RED_RMS * math.sqrt(2.0)
# IEC 61000-3-3, impedancia de referencia de la red publica: 0,4 + j0,25 ohm.
# Es la que la norma usa para medir flicker, y la cota razonable de lo que hay
# detras del enchufe.
Z_RED_OHM = math.hypot(0.4, 0.25)
R_CABLE_Y_FILTRO_OHM = 0.10   # ESTIMADO: cordon, IEC, choke y pistas

# --- lo que consumen los seis, fila "AC CURRENT (Typ.)" de la hoja p. 2 -----
# LA CELDA DE LA IRM-45 ES UNICA PARA TODA LA SERIE: "1.5A/115Vac 0.9A/230Vac
# 0.75A/277Vac" vale igual para la de 5 V y la de 12 V. Por eso PS5, que con
# D-F7 paso de IRM-20-5 a IRM-45-5, sube de 0,4 a 0,9.
I_AC_NOMINAL_A = {"PS1": 0.4, "PS2": 0.4,      # IRM-20-15
                  "PS3": 0.9, "PS4": 0.9,      # IRM-45-12
                  "PS5": 0.9, "PS6": 0.9}      # IRM-45-5 (PS5 por D-F7)
# Potencia de salida NOMINAL de cada uno, fila RATED POWER de la misma pagina.
P_RATED_W = {"PS1": 21.0, "PS2": 21.0, "PS3": 45.6, "PS4": 45.6,
             "PS5": 40.0, "PS6": 40.0}
# INRUSH CURRENT (Typ.), COLD START, 230 Vac. La hoja NO publica duracion.
I_INRUSH_A = {"PS1": 40.0, "PS2": 40.0, "PS3": 60.0, "PS4": 60.0,
              "PS5": 60.0, "PS6": 60.0}

# Lo que cada modulo entrega en cada escenario, en vatios de SALIDA.
V_RIEL = {"PS3": 12.0, "PS4": 12.0, "PS5": 5.0, "PS6": 5.0}
RIEL_DE = {"PS3": "rack+12", "PS4": "rack-12", "PS5": "rack+5",
           "PS6": "digital+5"}


def p_salida_w(escenario: str) -> dict[str, float]:
    """Vatios de salida por modulo en cada escenario.

    `placa_modulo` es lo que los seis pueden dar A LA VEZ segun SU hoja: no es
    un estado que el instrumento produzca --el liston declara menos-- pero es
    la cota que el fusible tiene que tolerar sin abrir mientras la proteccion
    del propio modulo decide."""
    if escenario == "placa_modulo":
        return dict(P_RATED_W)
    tabla = {"liston": PLACA_A, "sostenido": SOSTENIDO}[escenario]
    fuera = {"PS1": 15.0 * I_CASCADA_A, "PS2": 15.0 * I_CASCADA_A}
    for ref, v in V_RIEL.items():
        fuera[ref] = v * tabla[RIEL_DE[ref]]
    return fuera


def i_red_rms_a(escenario: str = "liston") -> float:
    """Corriente de red rms, escalando la fila AC CURRENT con la carga.

    ESTIMADO en el escalado: la hoja publica la corriente de red A CARGA
    NOMINAL y nada mas. El factor de potencia y el rendimiento se mueven con
    la carga, asi que la proporcion lineal es una aproximacion --y va a favor
    de seguridad por arriba, porque el consumo en vacio no baja a cero."""
    salida = p_salida_w(escenario)
    return sum(I_AC_NOMINAL_A[r] * min(1.0, salida[r] / P_RATED_W[r])
               for r in I_AC_NOMINAL_A)


# --- la NTC: Ametherm SL22 5R012 -------------------------------------------
# ametherm.com/datasheets/sl225r012/, leido 2026-09-04. La v3 llevaba un
# SL10 5R002, misma resistencia y 2 A de regimen: aqui hacen falta cuatro.
NTC_REF = "Ametherm SL22 5R012"
R_NTC_FRIO_OHM = 5.0
R_NTC_FRIO_TOL = 0.20          # "5 Ohm +- 20 %"
I_NTC_MAX_A = 12.0             # "Max Steady State Current: 12 Amps"
E_NTC_MAX_J = 100.0            # "Max Recommended Energy: 100 Joules"
R_NTC_A_IMAX_OHM = 0.05        # "Resistance @ 100% Max Current: 0.05 Ohm"
R_NTC_A_MEDIA_IMAX_OHM = 0.12  # "Resistance @ 50% Max Current: 0.12 Ohm"
C_NTC_MAX_240VAC_UF = 1500.0   # "Max Capacitance @ 240 VAC: 1,500 uF"
K_DISIPACION_W_C = 32.4e-3     # "Dissipation Constant: 32.4 mw/C"
TAU_NTC_S = 94.0               # "Thermal Time Constant: 94 s"

# --- el banco de entrada de los seis ---------------------------------------
# ESTIMADO, papel sec.5: deducido del hold-up publicado, no de una hoja.
C_TOTAL_UF = 205.0

# --- el fusible -------------------------------------------------------------
I_FUSIBLE_A = 6.3
# schurter-fst-5x20-fuse-2026-09-04.pdf, p. 4, fila de 6,3 A: "Melting I2t
# 10.0 In typ. = 190 [A2s]". Los tiempos de la p. 3 son los de IEC 60127-2 y
# valen para cualquier T de este calibre: a 1,5 x In, 60 min como MINIMO sin
# abrir; a 2,1 x In, 120 s como maximo para abrir.
I2T_FUSIBLE_A2S = 190.0
FACTOR_NO_ABRE = 1.5           # el multiplo al que la norma garantiza 60 min
# Poder de corte de la pieza de esa hoja: "L = Low Breaking Capacity (Glass
# Tube)", y en su tabla, nota 2: "10 x In @ 250 VAC".
PODER_CORTE_FST_A = 10.0 * I_FUSIBLE_A
# IEC 60320: una toma C14 es de 10 A. Es la cota de arriba del calibre.
I_TOMA_C14_A = 10.0
# Fraccion del I2t de fusion que un arranque puede gastar sin fatigar. Practica
# de aplicacion (la propia hoja remite a su nota de "Pulse Strength"): por
# debajo de un quinto, el fusible no envejece con los ciclos. ESTIMADO.
FRAC_I2T_ADMISIBLE = 0.20
# Fraccion del calibre que se puede llevar en REGIMEN PERMANENTE, y cuanto
# calibre se pierde por grado sobre 25 C. Los dos, practica de aplicacion:
# ESTIMADO. El fusible de esta fuente vive dentro del recinto, a la
# temperatura que da calor_budget.py, no en un banco.
K_CONTINUO = 0.70
DERATE_TEMP_POR_C = 0.0030

ESTIMADOS = (
    f"C_TOTAL_UF={C_TOTAL_UF}: banco de entrada de los seis, deducido del "
    f"hold-up (papel sec.5), no leido de una hoja",
    "el escalado de la fila AC CURRENT con la carga: la hoja solo la publica "
    "a carga nominal",
    f"R_CABLE_Y_FILTRO_OHM={R_CABLE_Y_FILTRO_OHM}: cordon, IEC, choke y pistas",
    f"FRAC_I2T_ADMISIBLE={FRAC_I2T_ADMISIBLE}: practica de aplicacion para que "
    f"el fusible no envejezca con los ciclos",
)
HUECOS = (
    "la hoja del fusible CERAMICO de alto poder de corte. La que esta en el "
    "arbol es de vidrio y bajo poder de corte, y solo sirve para los tiempos "
    "y el I2t de la norma",
    "la hoja del MOV y la del choke, que se redimensionan a la vez (sec.5)",
)


def r_ntc_caliente_ohm(i_a: float) -> float:
    """La resistencia de la NTC ya caliente, a esa corriente de regimen.

    La hoja publica DOS puntos --0,05 ohm al 100 % de su corriente maxima y
    0,12 al 50 %-- y aqui se trabaja muy por debajo de los dos. Se interpola
    en log-log y se DECLARA que es extrapolacion: por debajo del 50 % de su
    corriente maxima la hoja no dice nada."""
    i1, r1 = I_NTC_MAX_A / 2.0, R_NTC_A_MEDIA_IMAX_OHM
    i2, r2 = I_NTC_MAX_A, R_NTC_A_IMAX_OHM
    k = math.log(r2 / r1) / math.log(i2 / i1)
    return r1 * (i_a / i1) ** k


def i2t_pulso(r_total_ohm: float, c_f: float) -> float:
    """I2t de cargar el banco a traves de esa resistencia, en A2s.

    Un RC: i(t) = (Vpico/R) e^(-t/RC), asi que la integral de i^2 dt de 0 a
    infinito es Vpico^2 * C / (2 R). Es exacta, no una aproximacion de pico
    por ancho."""
    return V_RED_PICO ** 2 * c_f / (2.0 * r_total_ohm)


def i_pico_a(r_total_ohm: float) -> float:
    return V_RED_PICO / r_total_ohm


def r_arranque_frio_ohm() -> float:
    """Peor caso del arranque frio: la NTC en su tolerancia BAJA (menos
    resistencia, mas pico) mas lo que hay detras del enchufe."""
    return (R_NTC_FRIO_OHM * (1.0 - R_NTC_FRIO_TOL) + Z_RED_OHM
            + R_CABLE_Y_FILTRO_OHM)


def r_rearranque_caliente_ohm(*, conservador: bool = True) -> float:
    """Peor caso del rearranque: la NTC lo mas caliente que la hoja publica.

    `conservador` usa los 0,05 ohm del 100 % de su corriente maxima --que es
    un dato LEIDO y la cota inferior de todo lo que la pieza puede valer--;
    con False usa la extrapolacion a la corriente real, que es mas realista y
    mas alta, y por lo tanto mejor."""
    r_ntc = (R_NTC_A_IMAX_OHM if conservador
             else r_ntc_caliente_ohm(i_red_rms_a()))
    return r_ntc + Z_RED_OHM + R_CABLE_Y_FILTRO_OHM


def i2t_arranque_frio() -> float:
    return i2t_pulso(r_arranque_frio_ohm(), C_TOTAL_UF * 1e-6)


def i2t_rearranque_caliente(**kw) -> float:
    return i2t_pulso(r_rearranque_caliente_ohm(**kw), C_TOTAL_UF * 1e-6)


def energia_arranque_j(c_f: float = C_TOTAL_UF * 1e-6) -> float:
    """Julios que la NTC se traga en un arranque frio: toda la energia que
    acaba en el banco se disipa tambien en ella."""
    return 0.5 * c_f * V_RED_PICO ** 2


def isc_disponible_a() -> float:
    """Corriente de cortocircuito disponible en el enchufe."""
    return V_RED_RMS / Z_RED_OHM


def calor_ntc_w(i_a: float | None = None) -> float:
    """Lo que la NTC disipa en regimen, DENTRO del recinto."""
    i = i_red_rms_a() if i_a is None else i_a
    return i * i * r_ntc_caliente_ohm(i)


def calibre_minimo_a(i_cont_a: float, t_c: float = 69.0) -> float:
    """El calibre mas pequeno que aguanta esa corriente CONTINUA a esa T.

    Dos factores, los dos ESTIMADO de practica de aplicacion:

      * K_CONTINUO: la tabla de IEC 60127-2 garantiza 60 min sin abrir a
        1,5 x In, que NO es "para siempre". La practica es no pasar del 70 %
        del calibre en regimen permanente.
      * K_TEMP: el fusible vive en el recinto, no en un banco a 25 C. Un 5x20
        pierde del orden del 13 % de calibre a 70 C.
    """
    k_temp = 1.0 - DERATE_TEMP_POR_C * max(0.0, t_c - 25.0)
    return i_cont_a / (K_CONTINUO * k_temp)


def _guarda_permanente(p: dict[str, float]) -> None:
    """El calibre contra la carga permanente, por los dos lados."""
    i = p["i_red_rms_a"]
    minimo = calibre_minimo_a(i, p["t_recinto_c"])
    assert p["i_fusible_a"] >= minimo, (
        f"se fatiga y abre un martes: fusible de {p['i_fusible_a']:.2f} A "
        f"contra {i:.2f} rms permanentes a {p['t_recinto_c']:.0f} C, que piden "
        f"{minimo:.2f}. La tabla de la hoja solo garantiza 60 min sin abrir a "
        f"{FACTOR_NO_ABRE:.1f} x In, y eso no es 'para siempre': por debajo "
        f"del {K_CONTINUO:.0%} del calibre y con el derratado de temperatura, "
        f"el fusible es parte de la carga y no de la proteccion")
    assert p["i_fusible_a"] <= I_TOMA_C14_A, (
        f"{p['i_fusible_a']:.1f} A por encima de los {I_TOMA_C14_A:.0f} de una "
        f"toma C14 (IEC 60320): el fusible dejaria de proteger la propia toma")


def _guarda_rearranque(p: dict[str, float]) -> None:
    """El I2t del rearranque en caliente contra el del fusible.

    El parametro es el tiempo entre el corte y la vuelta: cuanto mas corto,
    mas caliente esta la NTC y menos limita. Se modela con la constante de
    tiempo termica de la hoja (94 s)."""
    t_s = p["t_rearranque_ms"] / 1000.0
    frio = R_NTC_FRIO_OHM * (1.0 - R_NTC_FRIO_TOL)
    caliente = R_NTC_A_IMAX_OHM
    # La NTC se enfria exponencialmente hacia su valor frio.
    r_ntc = caliente + (frio - caliente) * (1.0 - math.exp(-t_s / TAU_NTC_S))
    i2t = i2t_pulso(r_ntc + Z_RED_OHM + R_CABLE_Y_FILTRO_OHM,
                    p["c_total_uf"] * 1e-6)
    assert i2t <= FRAC_I2T_ADMISIBLE * p["i2t_fusible_a2s"], (
        f"es el caso que manda: apagar y volver a encender a los "
        f"{p['t_rearranque_ms']:.0f} ms mete {i2t:.2f} A2s con la NTC a "
        f"{r_ntc:.3f} ohm, y el fusible admite "
        f"{FRAC_I2T_ADMISIBLE * p['i2t_fusible_a2s']:.1f} sin fatigarse "
        f"({p['i2t_fusible_a2s']:.0f} de fusion). Sube la talla del fusible o "
        f"pon NTC con rele de bypass")


# Tampoco a mano: el fusible vive en el recinto y su derratado depende de
# la temperatura que resuelve calor_budget.py, no de una cifra copiada.
T_RECINTO_C = aire_recinto_c(p_recinto_w(SOSTENIDO), p_cajon_w(SOSTENIDO),
                             area_venteo_mm2=P_BASE["area_venteo_mm2"])

P_BASE = {
    "i_fusible_a": I_FUSIBLE_A,
    "i_red_rms_a": i_red_rms_a(),
    "t_recinto_c": T_RECINTO_C,
    "t_rearranque_ms": 0.0,      # el PEOR: la NTC no se ha enfriado nada
    "i2t_fusible_a2s": I2T_FUSIBLE_A2S,
    "c_total_uf": C_TOTAL_UF,
}


def i2t_de_calibre_a2s(i_a: float) -> float:
    """El I2t de fusion de otro calibre de la misma familia.

    Escala con In^2: es la razon de que subir la talla arregle el rearranque
    de paso, y la que se usa para contestar por el 4 A T del papel."""
    return I2T_FUSIBLE_A2S * (i_a / I_FUSIBLE_A) ** 2


def _autocomprobacion() -> None:
    # 1. El permanente, por los dos lados.
    _guarda_permanente(dict(P_BASE))

    # 2. Arranque en FRIO: la NTC limita y el I2t cabe de sobra.
    assert i2t_arranque_frio() < FRAC_I2T_ADMISIBLE * I2T_FUSIBLE_A2S, (
        f"el arranque frio mete {i2t_arranque_frio():.2f} A2s y el fusible "
        f"admite {FRAC_I2T_ADMISIBLE * I2T_FUSIBLE_A2S:.1f} sin fatigarse")
    # Y el inrush de placa de los seis NO se ve nunca: la NTC lo tapa.
    assert i_pico_a(r_arranque_frio_ohm()) < sum(I_INRUSH_A.values()), (
        f"con la NTC el pico son {i_pico_a(r_arranque_frio_ohm()):.0f} A y el "
        f"inrush sumado de las hojas {sum(I_INRUSH_A.values()):.0f}: si el "
        f"primero fuera mayor, la NTC no estaria limitando nada")

    # 3. EL QUE MANDA: rearranque en CALIENTE.
    _guarda_rearranque(dict(P_BASE))

    # 4. La NTC, contra sus tres limites de hoja.
    assert i_red_rms_a("placa_modulo") < I_NTC_MAX_A, (
        f"la NTC aguanta {I_NTC_MAX_A:.0f} A de regimen y los seis a su placa "
        f"piden {i_red_rms_a('placa_modulo'):.2f}")
    assert energia_arranque_j() < E_NTC_MAX_J, (
        f"cada arranque frio le mete {energia_arranque_j():.1f} J y la hoja "
        f"recomienda como maximo {E_NTC_MAX_J:.0f}")
    assert C_TOTAL_UF < C_NTC_MAX_240VAC_UF, (
        f"el banco son {C_TOTAL_UF:.0f} uF y la NTC admite "
        f"{C_NTC_MAX_240VAC_UF:.0f} a 240 Vac")
    # Y la de la v3 NO habria valido, que es lo que el papel sec.5 dice:
    assert i_red_rms_a() > 2.0, (
        "si la corriente de red cupiera en los 2 A del SL10 5R002 de la v3, "
        "cambiar de NTC no haria falta y el papel sec.5 sobraria")

    # 5. EL PODER DE CORTE. La pieza de la hoja del arbol no sirve, y es el
    #    aserto mas importante de este guion: un fusible que no interrumpe no
    #    es proteccion, es un trozo de hilo con certificado.
    assert PODER_CORTE_FST_A < isc_disponible_a(), (
        f"si la FST de vidrio ({PODER_CORTE_FST_A:.0f} A de corte) aguantara "
        f"los {isc_disponible_a():.0f} A disponibles en el enchufe, este "
        f"hallazgo no existiria y la hoja del arbol seria la de la pieza")

    # 6. Y LA PREGUNTA QUE EL PAPEL DEJA ABIERTA: el 4 A T de hipotesis
    #    tampoco aguanta el rearranque, no solo el permanente.
    i2t_4a = i2t_de_calibre_a2s(4.0)
    assert i2t_rearranque_caliente() > FRAC_I2T_ADMISIBLE * i2t_4a, (
        f"si el 4 A T aguantara el rearranque ({i2t_rearranque_caliente():.1f} "
        f"A2s contra {FRAC_I2T_ADMISIBLE * i2t_4a:.1f} admisibles de sus "
        f"{i2t_4a:.0f} de fusion), la hipotesis del papel solo fallaria por el "
        f"permanente y este aserto sobraria")

    # 7. Los canarios, por biseccion y por el texto de su aserto. El del
    #    tiempo de rearranque NO muerde --el peor caso es 0 ms y cabe--, asi
    #    que los que vigilan al aserto del rearranque son los dos parametros
    #    que si lo mueven: el I2t del fusible y el tamano del banco.
    v = borde_rojo(_guarda_rearranque, dict(P_BASE), "i2t_fusible_a2s",
                   0.0, 2000.0, "es el caso que manda")
    u = borde_rojo(_guarda_rearranque, dict(P_BASE), "c_total_uf",
                   0.0, 20000.0, "es el caso que manda")
    w = borde_rojo(_guarda_permanente, dict(P_BASE), "i_fusible_a",
                   0.0, 20.0, "se fatiga y abre un martes")
    x = borde_rojo(_guarda_permanente, dict(P_BASE), "i_fusible_a",
                   0.0, 20.0, "toma C14")
    y = borde_rojo(_guarda_permanente, dict(P_BASE), "t_recinto_c",
                   0.0, 300.0, "se fatiga y abre un martes")
    print(f"  canario: con menos de {v:.0f} A2s de fusion (o sea con un "
          f"calibre por debajo de {I_FUSIBLE_A * math.sqrt(v / I2T_FUSIBLE_A2S):.2f} A)"
          f", el rearranque no cabe")
    print(f"  canario: con un banco de mas de {u:.0f} uF, el rearranque no cabe")
    print(f"  canario: por debajo de {w:.2f} A de calibre se fatiga; por "
          f"encima de {x:.2f} deja de proteger la toma")
    print(f"  canario: por encima de {y:.0f} C de recinto, el derratado se "
          f"come el calibre")


def demo() -> int:
    print("fusible_budget: el fusible de red de la fuente v4\n")

    print("  corriente de red, fila AC CURRENT (Typ.) de la hoja p. 2:")
    for esc, etiqueta in (("sostenido", "sostenido (calor_budget.py)"),
                          ("liston", "liston declarado (D-F1)"),
                          ("placa_modulo", "los seis a SU placa")):
        print(f"    {etiqueta:32s} {i_red_rms_a(esc):5.2f} A rms")
    print(f"    (el papel sec.5 suma 3,90 y son "
          f"{i_red_rms_a('placa_modulo'):.2f}: sigue contando el 0,4 A de la")
    print("     IRM-20-5 que D-F7 sustituyo por una IRM-45-5 de 0,9. La celda")
    print("     de AC CURRENT de la IRM-45 es UNICA para toda la serie.)")
    print(f"    inrush frio sumado: {sum(I_INRUSH_A.values()):.0f} A "
          f"(el papel dice 285, por lo mismo)")

    print(f"\n  la NTC: {NTC_REF} (la v3 llevaba un SL10 5R002 de 2 A)")
    print(f"    {R_NTC_FRIO_OHM:.0f} ohm +-{R_NTC_FRIO_TOL:.0%} en frio; "
          f"{R_NTC_A_MEDIA_IMAX_OHM:.2f} al 50 % de Imax y "
          f"{R_NTC_A_IMAX_OHM:.2f} al 100 %")
    print(f"    regimen {I_NTC_MAX_A:.0f} A (piden "
          f"{i_red_rms_a('placa_modulo'):.2f}); energia {E_NTC_MAX_J:.0f} J "
          f"(cada arranque le mete {energia_arranque_j():.1f});")
    print(f"    capacidad max a 240 Vac {C_NTC_MAX_240VAC_UF:.0f} uF (el banco "
          f"son {C_TOTAL_UF:.0f})")
    print(f"    y DISIPA {calor_ntc_w():.2f} W dentro del recinto a "
          f"{r_ntc_caliente_ohm(i_red_rms_a()):.3f} ohm. La tabla de calor")
    print("    del papel sec.6 no la cuenta: ver el aviso del final.")

    print(f"\n  los dos pulsos, con el banco de {C_TOTAL_UF:.0f} uF "
          f"(I2t = Vpico^2 C / 2R, exacto):")
    for etiqueta, r in (("arranque FRIO (NTC a "
                         f"{R_NTC_FRIO_OHM * (1 - R_NTC_FRIO_TOL):.1f} ohm)",
                         r_arranque_frio_ohm()),
                        ("rearranque CALIENTE (NTC a "
                         f"{R_NTC_A_IMAX_OHM:.2f} ohm)",
                         r_rearranque_caliente_ohm())):
        print(f"    {etiqueta:44s} pico {i_pico_a(r):6.0f} A  "
              f"tau {r * C_TOTAL_UF * 1e-6 * 1000:5.3f} ms  "
              f"I2t {i2t_pulso(r, C_TOTAL_UF * 1e-6):7.2f} A2s")
    print(f"    (y con la NTC a su resistencia REAL a "
          f"{i_red_rms_a():.2f} A --extrapolada de los dos puntos de la")
    print(f"     hoja, {r_ntc_caliente_ohm(i_red_rms_a()):.3f} ohm-- el "
          f"rearranque baja a "
          f"{i2t_rearranque_caliente(conservador=False):.2f} A2s. El veredicto")
    print("     usa el dato leido, no la extrapolacion.)")

    print(f"\n  el calibre: {I_FUSIBLE_A:.1f} A T")
    print(f"    por abajo: {i_red_rms_a():.2f} A continuos al "
          f"{K_CONTINUO:.0%} del calibre y con el derratado de")
    print(f"    {T_RECINTO_C:.0f} C del recinto piden "
          f"{calibre_minimo_a(i_red_rms_a(), T_RECINTO_C):.2f} A. "
          f"(La tabla de la hoja garantiza 60 min")
    print(f"    sin abrir a {FACTOR_NO_ABRE:.1f} x In, que no es 'para "
          f"siempre'.)")
    print(f"    por arriba: {I_TOMA_C14_A:.0f} A de una toma C14 (IEC 60320).")
    print("    El 4 A T que el papel deja como hipotesis no llega por ninguno "
          "de los dos")
    print(f"    caminos: ni el permanente ({calibre_minimo_a(i_red_rms_a(), T_RECINTO_C):.2f} > 4)"
          f" ni el rearranque "
          f"({i2t_rearranque_caliente():.1f} A2s")
    print(f"    contra {FRAC_I2T_ADMISIBLE * i2t_de_calibre_a2s(4.0):.1f} "
          f"admisibles de sus {i2t_de_calibre_a2s(4.0):.0f} de fusion).")
    print(f"    I2t de fusion {I2T_FUSIBLE_A2S:.0f} A2s (hoja p. 4, 10 x In "
          f"tipico); el rearranque gasta")
    print(f"    {i2t_rearranque_caliente() / I2T_FUSIBLE_A2S:.1%} de ese, "
          f"contra el 18-53 % que el papel calculaba para el 1,6 A T:")
    print("    el I2t escala con In^2, asi que subir la talla arregla el")
    print("    rearranque de paso.")

    print("\n  EL PODER DE CORTE, que es el hallazgo que decide la pieza:")
    print(f"    corriente de corto disponible en el enchufe: "
          f"{isc_disponible_a():.0f} A")
    print(f"    (230 V sobre la impedancia de referencia de IEC 61000-3-3, "
          f"{Z_RED_OHM:.3f} ohm)")
    print(f"    poder de corte de la FST 5x20 de la hoja: "
          f"{PODER_CORTE_FST_A:.0f} A ('L = Low Breaking")
    print("    Capacity (Glass Tube)', y su nota 2: 10 x In @ 250 VAC).")
    print("    Un fusible de vidrio de bajo poder de corte delante de 490 A no")
    print("    interrumpe: se vaporiza y mantiene el arco. Hace falta uno")
    print("    CERAMICO de alto poder de corte. La hoja del arbol vale para")
    print("    los tiempos y el I2t --que son de IEC 60127-2 y valen para")
    print("    cualquier T de este calibre-- y NO para la pieza.")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}; HUECO: {len(HUECOS)}")
    for e in ESTIMADOS:
        print(f"    ESTIMADO - {e}")
    for h in HUECOS:
        print(f"    HUECO    - {h}")

    _autocomprobacion()

    print()
    print(f"AVISO a calor_budget.py: la NTC disipa {calor_ntc_w():.2f} W "
          f"dentro del recinto y la tabla del papel sec.6 no la lleva "
          f"(tampoco al MOV ni al choke). Sobre 27,5 W son un "
          f"{calor_ntc_w() / 27.5:.0%} mas.")
    print()
    print("HUECO: el calibre sale 6,3 A T y la pieza NO. La hoja que hay en el "
          "arbol es una FST 5x20 de VIDRIO y bajo poder de corte (63 A a "
          "6,3 A) contra los ~490 A disponibles en el enchufe: hace falta un "
          "ceramico de alto poder de corte, y su hoja no esta. Lo que la del "
          "arbol si da y se usa: los tiempos de IEC 60127-2 y el I2t de fusion "
          "de 190 A2s, que valen para cualquier T de este calibre.")
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
