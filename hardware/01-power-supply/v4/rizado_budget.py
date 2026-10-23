"""El rizado del riel ultra, mirado hasta 20 MHz, y lo que este guion NO cubre.

    python rizado_budget.py

## Por que existe

Los 0,8 uVrms del riel ultra son lo que este instrumento vende. Con el toroide
lo que habia que rechazar eran 100 Hz de una senoide; con la fuente v4 son
200 mVp-p a 65 kHz de un flyback Y SUS FLANCOS. El papel sec.4.2 hizo la
cuenta del fundamental --de 71 mVrms a 0,3 uVrms hacen falta 107 dB-- y la
cascada los da de sobra. Lo que NO sobra es la banda de 1 a 20 MHz:

  * los 200 mVp-p de la hoja estan medidos a 20 MHz de ancho de banda, o sea
    que incluyen los picos de conmutacion;
  * ahi el LC vive por encima de la resonancia propia de sus piezas;
  * el pre-regulador da ~0 dB (su curva de la hoja acaba en 1 MHz);
  * y el LT3045/LT3094 tambien se sale de su grafica (acaba en 10 MHz).

Y todo eso queda FUERA de la banda de 10 Hz a 100 kHz en la que se especifican
los 0,8 uVrms: el LNA del #58 puede dar verde mientras entra RF en cada
op-amp. Es el riesgo 2 del papel, y un presupuesto que solo mirase 65 kHz lo
reproduciria con cara de puerta.

## Lo que este guion decide, y el numero que lo decide

La ferrita de entrada de cada regulador DEJA DE SER UNA BUENA IDEA Y PASA A
SER UN REQUISITO, porque el modelo lo dice en decibelios: sin ella el peor
punto de la banda se queda en ~21 uV contra una cota de 0,3 --37 dB por
encima, y justo el orden de magnitud que el papel sec.4.2 anticipaba ("2-20 uV
de RF en el riel")--; con ella, 0,008 uV. El LC cuida los 65 kHz; la ferrita,
los MHz. Ninguna de las dos hace el trabajo de la otra.

La segunda decision es la AMORTIGUACION, y hace falta DOS VECES.

  * El LC. Un 22 uH / 47 uF sin amortiguar pica +21 dB en su resonancia de
    4,9 kHz, que cae DENTRO de la banda de 10 Hz-100 kHz en la que se mide el
    riel. Con Rd = 0,68 ohm + Cd = 220 uF en paralelo con C el pico baja a
    +2,6 dB. El papel lo pedia citando a Middlebrook; la razon que se sostiene
    sola es mas simple que la cita: un filtro que amplifica dentro de la banda
    que se especifica no es un filtro.
  * LA PERLA, y esto NO estaba en el papel. "Perla + ceramico" es la receta de
    manual y es tambien un LC: 955 nH de perla con 100 nF de ceramico resuenan
    en 516 kHz con Z0 = 3,1 ohm sobre una ESR de 10 mohm, o sea Q ~ 300, y ahi
    el divisor AMPLIFICA +34 dB en vez de atenuar. Cae dentro de la banda que
    este guion vigila y una decada y media por debajo de donde uno buscaria el
    problema. Se amortigua con Rd2 = 2,2 ohm + Cd2 = 2,2 uF: el pico queda en
    +0,6 dB y a 20 MHz sigue atenuando 68 dB, que es para lo que la perla
    esta. El pico es ESTRECHO y hay que barrerlo fino: con los 241 puntos
    del barrido de la banda se leen 32,1 dB y con 1601 se leen 34,0. La
    diferencia no cambia el veredicto --32 dB tambien se salen de
    cualquier criterio-- pero si el numero que se publica, y un pico
    estrecho medido con paso grueso siempre sale mas bajo de lo que es.

## Lo que este guion NO cubre, dicho como asercion y no como nota al pie

EL MODO COMUN. Ningun PSRR lo rechaza (design-notes v1 sec.18.7: "el PSRR no
lo rechaza... llega como una corriente que circula por la masa"). Todo lo de
aqui es modo DIFERENCIAL. Quien cierra el modo comun es D-F5 --un Y2 del borne
de estrella de cada modulo al chasis, para que el lazo se cierre en
centimetros-- y su medida con los seis encendidos. La constante
CUBRE_MODO_COMUN vive aqui en False y esta aseverada: si algun dia se pone en
True sin que el modelo cambie, se estara prometiendo lo que no se mide.

Tampoco cubre: el ruido propio de los reguladores (es el otro sumando de los
0,8 uV y lo mide el LNA), ni el acoplo por radiacion del campo de un IRM
encapsulado (sec.8: se fija al montar y se mide con el LNA), ni la estabilidad
del lazo de U1/U2 con esta impedancia de fuente (paso 2 del bring-up).

## De donde sale cada numero, y cual es supuesto

Las piezas de la cascada tienen hoja y su PSRR esta en curvas.py, leido con
los ojos. Lo que NO tiene hoja todavia son los PARASITOS: la ESR y la ESL del
condensador, la resonancia propia de la bobina y la impedancia de la ferrita.
Van como ESTIMADO --numero con razonamiento y sin hoja-- y el guion los cuenta
al final. Lo que este guion entrega a la tanda B no es "compra esta pieza":
son las COTAS que la pieza que se compre tiene que cumplir, y el canario dice
por donde pasa cada una.
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
import curvas  # noqa: E402
from curvas import psrr_db  # noqa: E402

# --- la fuente de rizado ---------------------------------------------------
# Fila "RIPPLE & NOISE (max.)" de la hoja Mean Well, p. 2, y papel sec.3. Es
# el modulo que alimenta la cascada ultra: PS1 y PS2, IRM-20-15.
RIZADO_IRM_VPP = 0.200
# Los otros cuatro, para la tabla informativa: no alimentan al riel ultra.
RIZADO_OTROS_VPP = {"PS3/PS4 (IRM-45-12)": 0.150, "PS5/PS6 (IRM-45-5)": 0.080}
# La hoja mide ese numero con 20 MHz DE ANCHO DE BANDA y por el metodo de su
# nota 2 (par trenzado de 12", 0,1 uF || 47 uF). O sea que dentro van el
# fundamental de 65 kHz Y los picos de los flancos, y la hoja NO publica como
# se reparten. El reparto de abajo es la unica pieza de este modelo que no
# sale ni de una hoja ni de una cuenta:
#
# ESTIMADO (papel sec.4.2): "los 200 mVp-p ... son sobre todo picos de 1-20
# MHz. Veinte milivoltios de pico ahi". Se toma la envolvente peor:
#   f <= 100 kHz  -> los 200 mVp-p ENTEROS al fundamental (conservador: se
#                    cuenta dos veces la misma energia)
#   f >= 1 MHz    -> 40 mVp-p, que son los 20 mV de pico del papel
#   entre medias  -> interpolado en log(f)
FUENTE_BAJA_VPP = RIZADO_IRM_VPP
FUENTE_ALTA_VPP = 0.040
F_CODO_BAJO_HZ = 100e3
F_CODO_ALTO_HZ = 1e6

F_CONMUTACION_HZ = 65e3      # diagrama de bloques, p. 3: "fosc : 65KHz"
F_BANDA_MAX_HZ = 20e6        # el ancho de banda con el que la hoja mide
PUNTOS_BANDA = 241           # barrido logaritmico, no dos puntos a mano


def banda_hz() -> list[float]:
    """El barrido de la banda, en logaritmico. NO dos puntos elegidos a mano:
    el peor punto de un producto de curvas con resonancias no esta donde uno
    lo pondria."""
    lo, hi = math.log10(F_CONMUTACION_HZ), math.log10(F_BANDA_MAX_HZ)
    paso = (hi - lo) / (PUNTOS_BANDA - 1)
    return [10.0 ** (lo + i * paso) for i in range(PUNTOS_BANDA)]


BANDA_HZ = banda_hz()

# --- la cota -------------------------------------------------------------
# Papel sec.4.2: "para dejar <= 0,3 uVrms de 71 mVrms (200 mVp-p senoidal) a
# 65 kHz hacen falta 107 dB". Los 0,3 uV son la PARTE del presupuesto de
# 0,8 uVrms que se le asigna al rizado de la fuente; el resto es ruido propio
# de los reguladores y lo mide el LNA (#58).
COTA_RUIDO_V = 0.3e-6
COTA_TOTAL_RIEL_V = 0.8e-6

# --- el LC de salida de cada IRM ------------------------------------------
# Valores del papel sec.4.2: "un 22 uH / 47 uF da 4,9 kHz y ~45 dB ideales a
# 65 kHz". Se conservan; lo que este guion anade es la amortiguacion y los
# parasitos.
L_H = 22e-6
C_F = 47e-6
# ESTIMADO: bobina de potencia SMD de 22 uH. DCR de catalogo para esa talla a
# 1,4 A, y resonancia propia tipica. Sin hoja: son las COTAS que la pieza
# elegida en la tanda B tiene que cumplir, y el canario dice cuanto margen hay.
DCR_OHM = 0.030
SRF_L_HZ = 8e6
# ESTIMADO: electrolitico de baja ESR de 47 uF/25 V con su ESL de patilla.
ESR_OHM = 0.030
ESL_H = 10e-9
# Amortiguacion: rama Rd + Cd en paralelo con C. Rd sale de la impedancia
# caracteristica del filtro, R0 = sqrt(L/C) = 0,684 ohm -> 0,68 de la E24;
# Cd = 220 uF, que es n = 4,7 veces C. La busqueda numerica que eligio este
# par esta en la tabla que imprime demo().
RD_OHM = 0.68
CD_F = 220e-6
ESR_D_OHM = 0.10             # ESTIMADO: electrolitico corriente de 220 uF
ESL_D_H = 15e-9              # ESTIMADO: mismo encapsulado, patilla mas larga
PICO_MAX_DB = 3.0            # criterio: Q <= ~1,35. Ver _autocomprobacion.

# --- la ferrita y el ceramico de la entrada de cada regulador -------------
# ESTIMADO: perla de ferrita de 600 ohm a 100 MHz, modelada por debajo de su
# propia resonancia como inductancia pura Z/(2*pi*f). Es el modelo pobre y va
# a favor de seguridad: una perla real tiene ademas parte resistiva, que
# atenua mas y no resuena.
Z_FERRITA_100MHZ_OHM = 600.0
R_FERRITA_DC_OHM = 0.05      # ESTIMADO: DCR de catalogo de una perla de 2 A
C_CER_F = 100e-9             # ceramico X7R de 100 nF pegado al regulador
ESR_CER_OHM = 0.010          # ESTIMADO
ESL_CER_H = 1.0e-9           # ESTIMADO: 0805 con via corta
# Y SU AMORTIGUACION, que la receta de manual no trae y este guion destapo.
# La perla (955 nH) y su ceramico (100 nF) son un LC de 515 kHz con Z0 = 3,1
# ohm y una ESR de 10 mohm: Q ~ 300, y el divisor AMPLIFICA +34 dB ahi en vez
# de atenuar. Cae dentro de la banda que este presupuesto vigila y por debajo
# de donde uno buscaria el problema. La rama Rd2 + Cd2 en paralelo con el
# ceramico lo baja a +0,6 dB sin tocar los 68 dB de 20 MHz, que es para lo
# que la perla esta puesta. Los dos son valores de catalogo.
RD_CER_OHM = 2.2
CD_CER_F = 2.2e-6
ESR_D_CER_OHM = 0.0          # la resistencia de la rama ES Rd2; el X7R no suma
ESL_D_CER_H = 3.0e-9         # ESTIMADO: 0805 + la resistencia en serie

# Fuera de la grafica LEIDA, el PSRR se cuenta como CERO. No es una lectura:
# es la unica lectura honesta que se puede hacer de una curva que se acaba.
# curvas.psrr_db() levanta ValueError ahi a proposito --extrapolarla seria
# inventar el numero que decide si el riel de 0,8 uV existe-- y este guion lo
# convierte en 0 dB y lo dice en voz alta.
PSRR_FUERA_DE_GRAFICA_DB = 0.0

# LO QUE HAY QUE PONERLE AL LT3015 PARA QUE SU CURVA SEA LA QUE SE LEYO.
#
# La G41 de su hoja (p. 11) dibuja TRES trazas y a 65 kHz --la conmutacion del
# IRM, o sea justo la frecuencia que decide este presupuesto-- valen ~41 dB
# (COUT 47 uF + CFF 10 nF), ~38 (10 uF + CFF) y ~15 (10 uF SIN CFF). Sin el
# condensador de avance el LT3015 rechaza MENOS que el LM2991 al que
# sustituye (24,5 dB), o sea que el cambio de pieza saldria al reves.
#
# Por eso las dos piezas se DECLARAN aqui y no se dan por supuestas, y el
# aserto de mas abajo comprueba que la cita de la curva sigue siendo la de
# estos dos valores. Si algun dia se relee la G41 en otras condiciones, la
# puerta lo dice en vez de dejar la lectura vieja con el BOM nuevo.
COUT_U2_F = 47e-6            # DECLARADO: la traza roja de la G41
CFF_U2_F = 10e-9             # DECLARADO: de ADJ a OUT. NO es opcional

# Las dos ramas de la cascada, con su pareja de reguladores vigentes (D-F8 y D-F9).
RAMAS = {"+15 -> U1 -> LT3045": ("LT1963A", "LT3045"),
         "-15 -> U2 -> LT3094": ("LT3015", "LT3094")}

# LO QUE ESTE PRESUPUESTO NO CUBRE. Aseverado, no anotado.
CUBRE_MODO_COMUN = False

# El mismo criterio de pico para la perla que para el LC: si un filtro
# amplifica dentro de la banda en la que se mide el riel, no es un filtro.
PICO_PERLA_MAX_DB = 3.0

ESTIMADOS = (
    "reparto espectral de los 200 mVp-p (papel sec.4.2, la hoja no lo publica)",
    f"DCR={DCR_OHM} ohm y SRF={SRF_L_HZ / 1e6:g} MHz de la bobina de {L_H * 1e6:g} uH",
    f"ESR={ESR_OHM} ohm y ESL={ESL_H * 1e9:g} nH del condensador de {C_F * 1e6:g} uF",
    f"ESR={ESR_D_OHM} ohm y ESL={ESL_D_H * 1e9:g} nH del condensador de amortiguacion",
    f"perla de ferrita de {Z_FERRITA_100MHZ_OHM:g} ohm a 100 MHz, modelada como inductancia pura",
    f"ESR={ESR_CER_OHM} ohm y ESL={ESL_CER_H * 1e9:g} nH del ceramico de {C_CER_F * 1e9:g} nF",
    f"ESL={ESL_D_CER_H * 1e9:g} nH de la rama de amortiguacion de la perla",
)


def _z_bobina(f: float, dcr: float = DCR_OHM, srf: float = SRF_L_HZ) -> complex:
    """La bobina con su capacidad de devanado en paralelo.

    Por encima de la resonancia propia una bobina deja de ser bobina: el
    acoplo pasa por esa capacidad, y ES lo que fija cuanto atenua el LC en la
    banda de los flancos. Modelarla como jwL a 20 MHz seria prometer 100 dB
    donde hay 56."""
    w = 2.0 * math.pi * f
    c_dev = 1.0 / ((2.0 * math.pi * srf) ** 2 * L_H)
    z_ideal = complex(dcr, w * L_H)
    z_dev = 1.0 / complex(0.0, w * c_dev)
    return z_ideal * z_dev / (z_ideal + z_dev)


def _z_cond(f: float, c: float, esr: float, esl: float) -> complex:
    w = 2.0 * math.pi * f
    return complex(esr, w * esl - 1.0 / (w * c))


def h_lc(f: float, *, rd: float = RD_OHM, cd: float = CD_F,
         esl: float = ESL_H) -> float:
    """Transferencia del LC amortiguado, en veces (no en dB)."""
    z_c = _z_cond(f, C_F, ESR_OHM, esl)
    z_d = _z_cond(f, cd, RD_OHM if rd is None else rd + ESR_D_OHM, ESL_D_H)
    z_par = z_c * z_d / (z_c + z_d)
    return abs(z_par / (_z_bobina(f) + z_par))


def h_ferrita(f: float, *, z100: float = Z_FERRITA_100MHZ_OHM,
              esl_cer: float = ESL_CER_H, cd: float = CD_CER_F,
              rd: float = RD_CER_OHM) -> float:
    """Transferencia de la perla + ceramico amortiguado de entrada de U1/U2."""
    if z100 <= 0.0:
        return 1.0                      # sin perla no hay divisor: pasa todo
    w = 2.0 * math.pi * f
    l_ferrita = z100 / (2.0 * math.pi * 100e6)
    z_f = complex(R_FERRITA_DC_OHM, w * l_ferrita)
    z_c = _z_cond(f, C_CER_F, ESR_CER_OHM, esl_cer)
    if cd > 0.0:
        z_d = _z_cond(f, cd, rd + ESR_D_CER_OHM, ESL_D_CER_H)
        z_c = z_c * z_d / (z_c + z_d)
    return abs(z_c / (z_f + z_c))


def _db(veces: float) -> float:
    """Atenuacion en dB positivos de una transferencia menor que 1."""
    return -20.0 * math.log10(veces) if veces > 0 else float("inf")


def psrr_leido_db(pieza: str, f: float) -> float:
    """El PSRR de la hoja donde la hoja lo dibuja, y CERO donde se acaba."""
    try:
        return psrr_db(pieza, f)
    except ValueError:
        return PSRR_FUERA_DE_GRAFICA_DB


def v_fuente_vrms(f: float) -> float:
    """La envolvente de rizado del IRM a esa frecuencia, en Vrms.

    De p-p a rms se divide por 2*sqrt(2), que es la conversion de una
    SENOIDE. Para los picos de los flancos eso sobrestima la energia
    (un pico estrecho tiene menos rms que una senoide del mismo p-p), asi
    que va a favor de seguridad."""
    if f <= F_CODO_BAJO_HZ:
        vpp = FUENTE_BAJA_VPP
    elif f >= F_CODO_ALTO_HZ:
        vpp = FUENTE_ALTA_VPP
    else:
        k = ((math.log10(f) - math.log10(F_CODO_BAJO_HZ))
             / (math.log10(F_CODO_ALTO_HZ) - math.log10(F_CODO_BAJO_HZ)))
        vpp = FUENTE_BAJA_VPP + k * (FUENTE_ALTA_VPP - FUENTE_BAJA_VPP)
    return vpp / (2.0 * math.sqrt(2.0))


def cadena_db(rama: str, f: float, *, con_ferrita: bool = True,
              z100: float = Z_FERRITA_100MHZ_OHM,
              esl_cer: float = ESL_CER_H) -> float:
    """Los decibelios que la cadena entera pone entre el IRM y el riel."""
    pre, lt = RAMAS[rama]
    total = _db(h_lc(f)) + psrr_leido_db(pre, f) + psrr_leido_db(lt, f)
    if con_ferrita:
        total += _db(h_ferrita(f, z100=z100, esl_cer=esl_cer))
    return total


def v_ruido_riel_v(f: float, rama: str | None = None, **kw) -> float:
    """Voltios rms que llegan al riel a esa frecuencia. Sin rama, la PEOR."""
    ramas = RAMAS if rama is None else {rama: RAMAS[rama]}
    return max(v_fuente_vrms(f) / 10.0 ** (cadena_db(r, f, **kw) / 20.0)
               for r in ramas)


def peor_de_la_banda(**kw) -> tuple[float, float]:
    """(frecuencia, voltios) del peor punto del barrido."""
    return max(((f, v_ruido_riel_v(f, **kw)) for f in BANDA_HZ),
               key=lambda x: x[1])


def pico_perla(z100: float = Z_FERRITA_100MHZ_OHM, **kw) -> tuple[float, float]:
    """(frecuencia, dB) del pico de la resonancia perla-ceramico.

    Positivo en dB significa que AMPLIFICA. Se barre toda la banda con paso
    fino porque el pico es estrecho: con 241 puntos entre 65 kHz y 20 MHz
    se leen 32,1 dB y con 1601 se leen 34,0. Un pico estrecho medido con
    paso grueso siempre sale mas bajo de lo que es."""
    fs = [10.0 ** (4.0 + 4.0 * i / 1600.0) for i in range(1601)]  # 10 kHz-100 MHz
    f, h = max(((f, h_ferrita(f, z100=z100, **kw)) for f in fs),
               key=lambda x: x[1])
    return f, 20.0 * math.log10(h)


def pico_lc_db(rd: float = RD_OHM, cd: float = CD_F) -> float:
    """Cuanto AMPLIFICA el LC en su resonancia, en dB. Positivo es malo."""
    fs = [10.0 ** (1.0 + 4.0 * i / 600.0) for i in range(601)]   # 10 Hz-100 kHz
    return 20.0 * math.log10(max(h_lc(f, rd=rd, cd=cd) for f in fs))


def _guarda_banda(p: dict[str, float]) -> None:
    """La banda entera contra la cota; su texto alimenta al canario.

    LOS DOS LADOS. Por abajo: una perla que no impide nada deja pasar los
    flancos. Por arriba: una impedancia de perla absurda no es una perla, es
    una bobina, y en serie con el consumo de U1 caeria tension continua --el
    margen de margen_budget.py-- ademas de resonar con el ceramico dentro de
    la banda."""
    z100 = p["z_ferrita_100mhz_ohm"]
    assert z100 <= Z_FERRITA_MAX_OHM, (
        f"perla de {z100:.0f} ohm a 100 MHz: por encima de "
        f"{Z_FERRITA_MAX_OHM:.0f} deja de ser una perla y es una bobina en "
        f"serie con la entrada de U1, con su caida continua y su resonancia")
    f, v = peor_de_la_banda(z100=z100, esl_cer=p["esl_ceramico_nh"] * 1e-9)
    assert v < COTA_RUIDO_V, (
        f"el peor punto de la banda esta en {f / 1e6:.3g} MHz con "
        f"{v * 1e6:.3f} uV contra {COTA_RUIDO_V * 1e6:.2f} de cota. El LNA "
        f"puede seguir dando verde en SU banda de 10 Hz-100 kHz: por eso se "
        f"mira hasta {F_BANDA_MAX_HZ / 1e6:.0f} MHz")


# Cota superior de la perla. DERIVADA, no elegida: la caida continua sobre el
# DCR de una perla no depende de su Z a 100 MHz, pero su inductancia si, y una
# perla de mas de 5 kohm a 100 MHz son ya 8 uH, del orden del propio LC.
Z_FERRITA_MAX_OHM = 5000.0

P_BASE = {
    "z_ferrita_100mhz_ohm": Z_FERRITA_100MHZ_OHM,
    "esl_ceramico_nh": ESL_CER_H * 1e9,
}


def _autocomprobacion() -> None:
    # 0. LA CURVA DEL LT3015 ES LA DE SUS DOS CONDENSADORES, y este aserto es
    #    el unico sitio donde el BOM y la lectura de la figura se tocan.
    #    Sin la CFF la traza buena de la G41 no aplica --y sin ella el LT3015
    #    rechaza menos que el LM2991 al que sustituye-- asi que declararla en
    #    un comentario no basta: si alguien relee la figura en otras
    #    condiciones, aqui salta.
    cita_u2 = curvas.FUENTE["LT3015"]
    for texto in (f"COUT = {COUT_U2_F * 1e6:.0f} uF",
                  f"CFF = {CFF_U2_F * 1e9:.0f} nF"):
        assert texto in cita_u2, (
            f"la curva de PSRR del LT3015 se leyo en otras condiciones que "
            f"las que este presupuesto declara: falta '{texto}' en la cita "
            f"{cita_u2!r}. O se cambia el BOM o se vuelve a leer la figura")

    # 1. A 65 kHz, el fundamental. Es la cuenta que el papel sec.4.2 ya
    #    publica (107 dB de necesidad) y aqui se comprueba con la cadena.
    v65 = v_ruido_riel_v(F_CONMUTACION_HZ)
    assert v65 < COTA_RUIDO_V, (
        f"a {F_CONMUTACION_HZ / 1e3:.0f} kHz llegan {v65 * 1e6:.3f} uV al riel "
        f"y la cota son {COTA_RUIDO_V * 1e6:.2f}")
    necesarios = 20.0 * math.log10(v_fuente_vrms(F_CONMUTACION_HZ)
                                   / COTA_RUIDO_V)
    assert abs(necesarios - 107.0) < 1.0, (
        f"para bajar de {v_fuente_vrms(F_CONMUTACION_HZ) * 1e3:.1f} mVrms a "
        f"{COTA_RUIDO_V * 1e6:.1f} uV hacen falta {necesarios:.1f} dB y el "
        f"papel sec.4.2 publica 107: la fuente o la cota no son las suyas")

    # 2. Y EN TODA LA BANDA, no solo en la fundamental. Es el riesgo 2 del
    #    papel: el LNA mira su banda y da verde mientras esto entra por otro
    #    lado.
    f_peor, v_peor = peor_de_la_banda()
    assert v_peor < COTA_RUIDO_V, (
        f"el peor punto de la banda esta en {f_peor / 1e6:.3g} MHz con "
        f"{v_peor * 1e6:.3f} uV contra {COTA_RUIDO_V * 1e6:.2f} de cota")

    # 3. LA FERRITA ES UN REQUISITO, Y ESTE ES EL NUMERO QUE LO DICE. Sin
    #    ella la banda no pasa; con ella si. Un aserto que solo comprobara el
    #    caso bueno no diria que la pieza hace falta.
    f_sin, v_sin = peor_de_la_banda(con_ferrita=False)
    assert v_sin > COTA_RUIDO_V, (
        f"sin la ferrita el peor punto sale {v_sin * 1e6:.3f} uV y la cota son "
        f"{COTA_RUIDO_V * 1e6:.2f}: si tambien pasara sin ella, este modelo no "
        f"esta viendo los flancos y la ferrita de sec.4.2 no tiene apoyo")

    # 4. La amortiguacion, por los dos lados. Sin ella el LC AMPLIFICA dentro
    #    de la banda de 10 Hz-100 kHz en la que se especifica el riel; con
    #    ella el pico cabe en el criterio.
    pico = pico_lc_db()
    pico_sin = pico_lc_db(rd=1e-9, cd=1e-15)
    assert pico <= PICO_MAX_DB, (
        f"el LC amortiguado pica {pico:.2f} dB en su resonancia y el criterio "
        f"son {PICO_MAX_DB:.1f} (Q ~ 1,35). Un filtro que amplifica dentro de "
        f"la banda en la que se mide el riel no es un filtro")
    assert pico_sin - pico >= 15.0, (
        f"la amortiguacion solo baja el pico de {pico_sin:.1f} a {pico:.1f} "
        f"dB: o Rd y Cd no estan haciendo nada, o el modelo no ve la "
        f"resonancia")

    # 4b. LA RESONANCIA DE LA PROPIA PERLA, que la receta de manual no cuenta.
    #     "Perla + ceramico" es un LC: 955 nH con 100 nF resuenan en 515 kHz
    #     con Z0 = 3,1 ohm sobre una ESR de 10 mohm, y ahi el divisor
    #     AMPLIFICA. Sin mirarlo se habria firmado una pieza que empeora en
    #     media banda lo que vino a arreglar en la otra media. La rama
    #     Rd2 + Cd2 la amortigua, y los dos asertos de abajo son los dos
    #     lados: que la resonancia EXISTE en el modelo (si no, el modelo no
    #     ve un divisor LC) y que la amortiguacion la deja bajo criterio.
    f_pico, pico_p = pico_perla()
    _, pico_sin_amortiguar = pico_perla(cd=0.0)
    assert pico_sin_amortiguar > 20.0, (
        f"sin amortiguar, la perla y su ceramico tendrian que picar mucho "
        f"({pico_sin_amortiguar:.1f} dB): si el modelo no ve esa resonancia "
        f"no esta modelando un divisor LC, y el Rd2 + Cd2 que este guion pide "
        f"esta puesto sin motivo")
    assert pico_p <= PICO_PERLA_MAX_DB, (
        f"la perla amplifica {pico_p:.1f} dB en {f_pico / 1e3:.0f} kHz, por "
        f"encima de los {PICO_PERLA_MAX_DB:.1f} de criterio. Un filtro que "
        f"amplifica dentro de la banda en la que se mide el riel no es un "
        f"filtro: se amortigua, no se explica")
    assert pico_sin_amortiguar - pico_p >= 15.0, (
        f"la amortiguacion de la perla solo baja el pico de "
        f"{pico_sin_amortiguar:.1f} a {pico_p:.1f} dB: Rd2 y Cd2 no estan "
        f"haciendo su trabajo")
    assert v_ruido_riel_v(f_pico) < COTA_RUIDO_V, (
        f"en la resonancia de la perla ({f_pico / 1e3:.0f} kHz) llegan "
        f"{v_ruido_riel_v(f_pico) * 1e6:.4f} uV: la pieza que se puso para los "
        f"flancos es la que rompe la banda")
    assert _db(h_ferrita(F_BANDA_MAX_HZ)) > 40.0, (
        f"amortiguar la perla no puede costarle su trabajo: a "
        f"{F_BANDA_MAX_HZ / 1e6:.0f} MHz sigue teniendo que atenuar, y da "
        f"{_db(h_ferrita(F_BANDA_MAX_HZ)):.1f} dB")

    # 5. El veredicto NO se apoya en un dB que la hoja no publica. Los
    #    PSRR fuera de grafica se cuentan como cero, y si se les diera
    #    cualquier valor positivo el resultado solo puede mejorar: se
    #    comprueba que la banda pasa con el peor supuesto posible.
    assert PSRR_FUERA_DE_GRAFICA_DB == 0.0, (
        "el PSRR fuera de la grafica leida tiene que contarse como CERO. "
        "Cualquier otro valor es una extrapolacion, que es justo lo que "
        "curvas.psrr_db() se niega a hacer")

    # 6. Lo que este guion NO cubre, aseverado.
    assert CUBRE_MODO_COMUN is False, (
        "este presupuesto es de modo DIFERENCIAL. El modo comun no lo rechaza "
        "ningun PSRR (design-notes v1 sec.18.7): vuelve como corriente por la "
        "masa, y quien lo cierra es D-F5 (Y2 por modulo) y su medida con los "
        "seis encendidos. Si algun dia esta constante se pone en True sin que "
        "el modelo cambie, se estara prometiendo lo que no se mide")

    # 7. Los canarios, por biseccion y por el texto de su aserto.
    v = borde_rojo(_guarda_banda, dict(P_BASE), "z_ferrita_100mhz_ohm",
                   0.0, Z_FERRITA_MAX_OHM, "el peor punto de la banda")
    print(f"  canario: por debajo de {v:.0f} ohm a 100 MHz de perla, el peor "
          f"punto de la banda no pasa")
    w = borde_rojo(_guarda_banda, dict(P_BASE), "z_ferrita_100mhz_ohm",
                   0.0, 10.0 * Z_FERRITA_MAX_OHM, "deja de ser una perla")
    print(f"  canario: por encima de {w:.0f} ohm a 100 MHz ya no es una perla, "
          f"es una bobina en serie con U1")


def demo() -> None:
    print("rizado_budget: la cadena del riel ultra, de 65 kHz a 20 MHz\n")

    print(f"la fuente: {RIZADO_IRM_VPP * 1e3:.0f} mVp-p de PS1/PS2 "
          f"(IRM-20-15, hoja p. 2, medidos a 20 MHz de ancho de banda)")
    print(f"  = {v_fuente_vrms(F_CONMUTACION_HZ) * 1e3:.1f} mVrms a "
          f"{F_CONMUTACION_HZ / 1e3:.0f} kHz si se toma senoidal")
    print(f"  ESTIMADO: por encima de 1 MHz se toman "
          f"{FUENTE_ALTA_VPP * 1e3:.0f} mVp-p (papel sec.4.2: '20 mV de pico')")
    for nombre, vpp in RIZADO_OTROS_VPP.items():
        print(f"  (informativo, no alimentan al riel ultra: {nombre} "
              f"{vpp * 1e3:.0f} mVp-p)")

    print(f"\nel LC: {L_H * 1e6:g} uH / {C_F * 1e6:g} uF -> f0 = "
          f"{1.0 / (2 * math.pi * math.sqrt(L_H * C_F)):.0f} Hz, amortiguado "
          f"con Rd = {RD_OHM:g} ohm + Cd = {CD_F * 1e6:g} uF")
    print(f"  pico en resonancia: {pico_lc_db():+.2f} dB amortiguado, "
          f"{pico_lc_db(rd=1e-9, cd=1e-15):+.1f} dB sin amortiguar")
    print("  (la resonancia cae en 4,9 kHz, DENTRO de la banda de 10 Hz-100")
    print("   kHz en la que se especifican los 0,8 uV: sin amortiguar el")
    print("   filtro amplificaria justo donde se mide el riel)")
    print(f"  carga capacitiva a la salida del IRM: "
          f"{(C_F + CD_F) * 1e6:.0f} uF por riel. La hoja no publica maximo:")
    print("   se comprueba en el paso 1 del bring-up, con el IRM solo.")

    print(f"\nla cadena, dB por tramo (rama peor de las {len(RAMAS)}):")
    print(f"  {'f':>10s} {'LC':>7s} {'perla':>7s} {'pre-reg':>8s} {'LT':>7s} "
          f"{'total':>7s} {'fuente':>9s} {'al riel':>10s}")
    for f in (65e3, 100e3, 500e3, 1e6, 2e6, 5e6, 10e6, 20e6):
        peor_r = max(RAMAS, key=lambda r: v_ruido_riel_v(f, r))
        pre, lt = RAMAS[peor_r]
        etiqueta = (f"{f / 1e3:.0f}k" if f < 1e6 else f"{f / 1e6:g}M")
        print(f"  {etiqueta:>10s} {_db(h_lc(f)):7.1f} {_db(h_ferrita(f)):7.1f} "
              f"{psrr_leido_db(pre, f):8.1f} {psrr_leido_db(lt, f):7.1f} "
              f"{cadena_db(peor_r, f):7.1f} "
              f"{v_fuente_vrms(f) * 1e3:8.2f}m "
              f"{v_ruido_riel_v(f) * 1e6:9.4f}u")
    print(f"  (pre-reg y LT en {PSRR_FUERA_DE_GRAFICA_DB:.0f} dB donde su "
          f"curva se acaba: LM a 1 MHz, LT a 10 MHz)")

    f_peor, v_peor = peor_de_la_banda()
    f_sin, v_sin = peor_de_la_banda(con_ferrita=False)
    print(f"\nbarrido de {PUNTOS_BANDA} puntos entre "
          f"{F_CONMUTACION_HZ / 1e3:.0f} kHz y {F_BANDA_MAX_HZ / 1e6:.0f} MHz:")
    print(f"  CON ferrita: peor punto {f_peor / 1e6:.3g} MHz, "
          f"{v_peor * 1e6:.4f} uV  (cota {COTA_RUIDO_V * 1e6:.2f})")
    print(f"  SIN ferrita: peor punto {f_sin / 1e6:.3g} MHz, "
          f"{v_sin * 1e6:.2f} uV  <- {20 * math.log10(v_sin / COTA_RUIDO_V):.0f}"
          f" dB POR ENCIMA de la cota")
    print("  Ese 'sin ferrita' es el riesgo 2 del papel con un numero: el")
    print("  papel anticipaba '2-20 uV de RF en el riel' y el modelo lo")
    print("  reproduce. La ferrita de entrada de cada regulador no es una")
    print("  buena idea, es lo que hace que la banda cierre.")

    f_pico, pico_p = pico_perla()
    f_sa, pico_sa = pico_perla(cd=0.0)
    print("\n  Y la perla trae SU PROPIA resonancia con el ceramico. La "
          "receta de manual")
    print(f"  --perla + 100 nF-- es un LC de {f_sa / 1e3:.0f} kHz con Z0 = "
          f"{math.sqrt((Z_FERRITA_100MHZ_OHM / (2 * math.pi * 100e6)) / C_CER_F):.1f}"
          f" ohm sobre una ESR de")
    print(f"  {ESR_CER_OHM * 1e3:.0f} mohm: AMPLIFICA {pico_sa:+.1f} dB ahi, "
          f"dentro de la banda que este guion")
    print("  vigila y muy por debajo de donde uno buscaria el problema.")
    print(f"  Con la rama Rd2 = {RD_CER_OHM:g} ohm + Cd2 = {CD_CER_F * 1e6:g} uF"
          f" el pico queda en {pico_p:+.2f} dB")
    print(f"  y a {F_BANDA_MAX_HZ / 1e6:.0f} MHz sigue atenuando "
          f"{_db(h_ferrita(F_BANDA_MAX_HZ)):.0f} dB, que es para lo que esta.")
    print("  Es el mismo fallo que el LC sin amortiguar, una escala mas abajo,")
    print("  y hay que barrerlo fino: con los 241 puntos de la banda se leen")
    print(f"  {20 * math.log10(max(h_ferrita(f, cd=0.0) for f in BANDA_HZ)):.1f} dB y con 1601 se leen")
    print(f"  {pico_sa:.1f}.")

    print(f"\nlo que este presupuesto NO cubre: el modo comun "
          f"(CUBRE_MODO_COMUN={CUBRE_MODO_COMUN}).")
    print("  Lo cierra D-F5 --un Y2 por modulo al chasis-- y su medida con los")
    print("  seis encendidos, no un PSRR. Tampoco cubre el ruido propio de")
    print(f"  los reguladores, que es el resto de los "
          f"{COTA_TOTAL_RIEL_V * 1e6:.1f} uV y lo mide el LNA (#58).")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}")
    for e in ESTIMADOS:
        print(f"    - {e}")
    print("  Ninguno tiene hoja todavia. Lo que este guion entrega a la tanda")
    print("  B no es una pieza: son las cotas que la pieza tiene que cumplir.")

    _autocomprobacion()
    print("\nOK: rizado_budget.py")


if __name__ == "__main__":
    demo()
