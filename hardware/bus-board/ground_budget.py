"""Presupuesto de masa del bus board, en cents de desafinacion.

Por que existe este fichero y no un parrafo en las notas: el ancho del cobre,
la longitud de los cables de bajada y el numero de conductores de masa son
NUMEROS, y si alguien los cambia el diseno se rompe en silencio. Aqui se rompe
en voz alta.

    python ground_budget.py

La cadena causal, que es lo que hay que tener en la cabeza:

  1 V/octava -> 1 V = 1200 cents -> **1 mV = 1.2 cents**.

  Un CV de tono sale del MIDI/CV referido a SU masa local y lo lee el VCO
  referido a la SUYA. Si las dos masas no estan al mismo potencial, la
  diferencia se suma al CV y el VCO desafina. No es ruido: es un error de
  continua que se oye como que el sinte no afina.

  Objetivo: <= 2 cents entre CUALQUIER par de modulos de la cadena de tono
  (MIDI/CV + los tres VCO). 2 cents = 1.67 mV de diferencia de masa.

Lo que este calculo destapo y no era obvio:

  * El plano de masa del bus NO es el cuello de botella. Aporta ~0.2 cents.
    El presupuesto se lo comen el cable de bajada y sus contactos.
  * Pero solo si es PLANO. Una pista de 5 mm haciendo el mismo trabajo son
    ~3 cents ella sola, y el diseno se cae.
  * En el cable, el cobre ya no manda: **mandan los contactos**. Engordar de
    24 AWG a 20 AWG casi no mueve la aguja porque los crimpados son el suelo.
    Lo que si mueve la aguja es usar los DOS conductores de masa de J2.
  * Con dos segmentos aparece un termino nuevo que no existiria con uno solo:
    si los dos tiran corrientes distintas, sus cables de alimentacion caen
    distinto y TODO el segmento A se desplaza respecto al B. Por eso la
    cadena de tono va entera en el MISMO segmento (ver REGLA_SEGMENTO).
"""
from __future__ import annotations

import os
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
from canario import borde_rojo  # noqa: E402

# --- constantes fisicas -------------------------------------------------
RHO_20 = 1.72e-8         # resistividad del cobre a 20 C [ohm*m]
ALPHA = 0.00393          # coef. de temperatura del cobre [1/C]
T_OP = 40.0              # dentro del cajon, no a 20 C
RHO = RHO_20 * (1 + ALPHA * (T_OP - 20.0))

ESPESOR_1OZ = 35e-6      # cobre de 1 oz [m]
R_CUADRO = RHO / ESPESOR_1OZ * 1000.0   # [mohm/cuadro]

CENTS_POR_MV = 1.2       # 1 V/oct: 1 V = 1200 cents
OBJETIVO_CENTS = 2.0

# --- geometria del segmento ---------------------------------------------
LARGO = 320.0            # mm
ANCHO_PLANO_EFECTIVO = 30.0   # mm de plano que sobrevive a los taladros de
                              # los conectores. El plano bruto son 56 mm; se
                              # descuenta a ojo de buen cubero POR LO BAJO.
X_ALIMENTACION = LARGO / 2    # el feed entra por el CENTRO, no por la punta:
                              # parte en dos el camino mas largo, gratis.
# Posiciones reales de los slots en la placa (build_pcb.py, SLOTS_X). Hay un
# hueco de 36 mm en el centro porque ahi va el bornero de alimentacion, no por
# nada electrico.
SLOTS_X = [26.0, 74.0, 122.0, 198.0, 246.0, 294.0]
N_SLOTS = len(SLOTS_X)

# --- corrientes ----------------------------------------------------------
# OJO: la corriente de masa de un modulo NO es su consumo de riel. Un modulo
# analogico simetrico chupa I de +12 y devuelve I por -12, y por masa solo
# circula el DESEQUILIBRIO. Lo que si va integro por masa: los LED de panel y
# cualquier carga colgada de un solo riel.
I_MASA_SAM17 = 0.050     # A. VCO (~5 mA de desequilibrio) + holgura para
                         # una fila de LED de panel. Pesimista a proposito.
I_MASA_EURO = 0.150      # A. Un modulo Eurorack digital con su regulador de
                         # 5 V colgado de +12 devuelve TODO por masa.

# --- cable de bajada -----------------------------------------------------
SECCION = {"20AWG": 0.518e-6, "24AWG": 0.205e-6, "28AWG": 0.081e-6,
           "2.5mm2": 2.5e-6}     # el retorno del rack, papel fuente v4 sec.4.1
R_CONTACTO = 10e-3       # ohm por contacto crimpado/IDC. Dos por conductor
                         # (un extremo en la placa, otro en el modulo).
                         # Valor de manual para contacto de laton estanado.


def r_plano(largo_mm: float, ancho_mm: float) -> float:
    """Resistencia de un tramo de plano, en ohm."""
    return R_CUADRO * (largo_mm / ancho_mm) / 1000.0


def r_cable(largo_mm: float, awg: str, n_conductores: int) -> float:
    """Resistencia de un cable de bajada, contactos incluidos.

    n_conductores en PARALELO: es el unico sitio del diseno donde duplicar
    un pin divide la resistencia por dos de verdad.
    """
    r_cobre = RHO / SECCION[awg] * (largo_mm / 1000.0)
    return (r_cobre + 2 * R_CONTACTO) / n_conductores


def slots_x() -> list[float]:
    return list(SLOTS_X)


def perfil_plano(corrientes: list[float]) -> list[float]:
    """Potencial de masa en cada slot [V], referido al punto de alimentacion.

    Modelo: los slots cuelgan de una tira de plano alimentada por el CENTRO,
    asi que son dos ramas independientes. Se camina cada rama de dentro hacia
    fuera y cada tramo lleva la suma de las corrientes que quedan por delante.

        feed ---- s3 ---- s2 ---- s1
             I3+I2+I1  I2+I1     I1

    Version anterior de esta funcion cogia un solo tramo feed->slot con la
    corriente de mas alla del slot, y se dejaba fuera la corriente de los
    slots intermedios en el trozo interior. Infravaloraba ~8%.
    """
    xs = slots_x()
    v = [0.0] * N_SLOTS
    for signo in (-1, +1):
        rama = [i for i in range(N_SLOTS)
                if (xs[i] - X_ALIMENTACION) * signo > 0]
        rama.sort(key=lambda i: abs(xs[i] - X_ALIMENTACION))   # de dentro a fuera
        pot, prev = 0.0, X_ALIMENTACION
        for pos, i in enumerate(rama):
            i_tramo = sum(corrientes[k] for k in rama[pos:])    # lo que queda fuera
            pot += i_tramo * r_plano(abs(xs[i] - prev), ANCHO_PLANO_EFECTIVO)
            prev = xs[i]
            v[i] = pot
    return v


def cents(volts: float) -> float:
    return abs(volts) * 1000.0 * CENTS_POR_MV


# =========================================================================
# El rack de invitados: I x R_retorno, y N no es 1 (fuente v4, sec.4.1)
# =========================================================================
#
# Todo lo de arriba mide UN bus board: el del instrumento, con sus seis slots
# y sus corrientes de desequilibrio de decenas de miliamperios. La fuente v4
# mete debajo una fila Eurorack de 104 HP con rieles propios y AMPERIOS de
# retorno, y la junta del 2026-09-03 lo dijo con una frase que es ahora el
# invariante de esa fuente:
#
#   "El potencial contra el que se mide la cadena de tono lo fija una sola
#    corriente --la del instrumento-- para cualquier patch y cualquier
#    chasis."
#
# Lo que rompe ese invariante no es el consumo del rack: es POR DONDE VUELVE.
# Un cable de patch de 3,5 mm tiene la malla a masa en las dos puntas, asi que
# rack e instrumento son UN SOLO dominio de masa en cuanto hay un patch. Y la
# corriente de retorno de un invitado no obedece a la regla que uno le
# escriba: vuelve por TODAS las ramas en paralelo, repartida por impedancia.
#
#   (a)  bus board de invitados -> cable -> nodo estrella
#   (b)  N cables de patch -> jacks de la bahia -> plano del INSTRUMENTO ->
#        J2 -> nodo estrella
#
# Con N = 1 la rama (b) son 120 mohm contra 4,2 de (a) y casi todo vuelve por
# donde debe. El numero es comodo y es FALSO: los patches van en paralelo, y
# con diez son 12 mohm, del mismo orden que (a). Ahi es donde amperios ajenos
# entran en el plano del instrumento.
#
# Y ojo con el segundo termino, que sigue existiendo aunque (b) no exista:
# aunque volviera todo por (a), la fila entera queda I x R_a por encima de
# GNDA, y ese desfase se suma a cualquier CV que cruce de la fila al 1 V/oct.
# "Grueso y directo" no lo arregla: la funcion de abajo despeja el cobre que
# haria falta y es una pletina, no un cable.

# Retorno del rack: 2,5 mm2 x 300 mm y dos bornes (papel sec.4.1).
LARGO_RETORNO_RACK_MM = 300.0
SECCION_RETORNO_RACK = "2.5mm2"
# Los dos extremos del retorno del rack son BORNES DE TORNILLO, no crimpados.
# La diferencia es 5x en el total y el papel da las dos cotas a proposito:
# con borne salen 4,2 mohm y con crimpado 22. Se calculan las dos.
R_BORNE = 1e-3           # ohm por borne de tornillo (papel sec.4.1)

# Un cable de patch: hilo fino y dos casquillos de jack de 3,5 mm. El papel
# lo da redondo, "~120 mohm por cable (dos jacks y un hilo fino)"; aqui se
# desglosa para poder discutirlo pieza a pieza, y la suma tiene que caer
# encima de esos 120.
LARGO_PATCH_MM = 300.0
AWG_PATCH = "28AWG"
R_JACK = 25e-3           # ohm por casquillo de 3,5 mm. ESTIMADO: contacto de
                         # muelle, no crimpado; sin hoja, del mismo orden que
                         # el R_CONTACTO de arriba y peor por ser deslizante.
R_PATCH_PAPEL = 0.120    # ohm; el redondo del papel sec.4.1, para contraste

# El neto del rack: lo que sale por +12 y +5 menos lo que vuelve por -12. Se
# importa de calor_budget.py --no se copia-- porque hay DOS cifras y las dos
# importan: la de placa (D-F1, el peor caso comprado) y la sostenida (lo que
# el calor deja, y lo que el dueno va a vivir).
_V4 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "01-power-supply", "v4")
if _V4 not in sys.path:
    sys.path.insert(0, _V4)
from calor_budget import PLACA_A as _PLACA_A          # noqa: E402
from calor_budget import SOSTENIDO as _SOSTENIDO      # noqa: E402


def _neto(tabla: dict[str, float]) -> float:
    """Corriente neta que el rack devuelve por masa: los dos positivos menos
    el negativo. Un modulo simetrico devuelve por -12 lo que chupa de +12."""
    return tabla["rack+12"] + tabla["rack+5"] - tabla["rack-12"]


I_RACK_PLACA_A = _neto(_PLACA_A)          # 5,3 A: 3,8 + 4,0 - 2,5 (sec.4.1)
I_RACK_SOSTENIDO_A = _neto(_SOSTENIDO)    # lo que el calor deja (sec.6)

# Cuantos patches se consideran el peor caso realista de un rack de 104 HP.
# ESTIMADO: el papel razona con 10 y con 20; se toma el peor de los dos.
N_PATCHES_PEOR = 20

# --- los dos requisitos que este presupuesto le entrega a la bahia --------
# No son mecanismos que este fichero disene: son las dos condiciones sin las
# cuales los numeros de abajo desafinan el instrumento. Viven aqui como
# CONSTANTES ASEVERADAS porque ese es el unico sitio del arbol donde se
# comprueban; el papel de la bahia (#166 sec.5, #183) las implementa.
BAHIA_JACKS_EN_ISLA_DE_RACK = True
BAHIA_RECIBE_EN_DIFERENCIAL = True
# Y AQUI ESTA LA TRAMPA QUE HAY QUE DECIR EN VOZ ALTA: las dos de arriba son
# constantes de ESTE fichero, asi que `assert BAHIA_RECIBE_EN_DIFERENCIAL`
# solo puede saltar si alguien edita esta linea. Aseverarlas y salir en verde
# seria una puerta que no vigila nada --el patron del aserto que no puede
# fallar-- justo encima de una tabla que dice 20,29 cents contra un objetivo
# de 2. Lo que las convierte en algo es MIRAR SI SU DUENO EXISTE: el papel de
# la bahia (#166 sec.5, #183), que es quien tiene que implementarlas. Mientras
# no exista, este guion sale en HUECO y lo dice, igual que
# consumo_total_budget.py hizo con invitados_budget.py.
_ESPECIFICACIONES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", "docs", "superpowers", "specs")


def papel_de_la_bahia() -> str | None:
    """La ruta del papel de la bahia, si ya existe. No se afirma que no."""
    try:
        nombres = os.listdir(_ESPECIFICACIONES)
    except OSError:
        return None
    for n in sorted(nombres):
        if "bahia" in n.lower() and n.endswith(".md"):
            return os.path.join(_ESPECIFICACIONES, n)
    return None


def r_retorno_rack(r_contacto: float = R_BORNE) -> float:
    """Rama (a): el retorno del rack al nodo estrella, contactos incluidos."""
    r_cobre = RHO / SECCION[SECCION_RETORNO_RACK] * (LARGO_RETORNO_RACK_MM
                                                     / 1000.0)
    return r_cobre + 2 * r_contacto


def r_patch() -> float:
    """Rama (b), UN cable: hilo fino y dos casquillos de jack."""
    r_cobre = RHO / SECCION[AWG_PATCH] * (LARGO_PATCH_MM / 1000.0)
    return r_cobre + 2 * R_JACK


def r_rama_patches(n_patches: float) -> float:
    """Los N patches en PARALELO. Es el numero que la version con N = 1 de
    este fichero no tenia, y el que convierte 120 mohm en 6."""
    if n_patches <= 0:
        return float("inf")
    return r_patch() / n_patches


def desfase_mv(i_rack_a: float, n_patches: float, *,
               isla: bool = BAHIA_JACKS_EN_ISLA_DE_RACK,
               r_contacto: float = R_BORNE) -> float:
    """Milivoltios entre la masa de la fila de invitados y el nodo estrella.

    Es la magnitud que mide el paso nuevo del bring-up: pinza en +12 de rack
    y voltimetro entre la masa del bus board de invitados y GNDREF de C.

    Con la isla de masa del rack bajo los jacks (requisito 2 del papel), la
    rama (b) NO EXISTE --los casquillos no tocan GNDA-- y todo el retorno va
    por (a): el desfase es I x R_a, el peor de los dos. Sin la isla, las dos
    ramas van en paralelo y el desfase BAJA... a cambio de meter la
    diferencia por el plano del instrumento, que es peor. Por eso este numero
    no se puede leer solo: va con i_por_el_plano_a()."""
    r_a = r_retorno_rack(r_contacto)
    r = r_a if isla else (r_a * r_rama_patches(n_patches)
                          / (r_a + r_rama_patches(n_patches)))
    return i_rack_a * r * 1000.0


def i_por_el_plano_a(i_rack_a: float, n_patches: float, *,
                     isla: bool = BAHIA_JACKS_EN_ISLA_DE_RACK,
                     r_contacto: float = R_BORNE) -> float:
    """Amperios del rack que cruzan el plano de masa DEL INSTRUMENTO.

    Divisor de corriente entre las dos ramas: por (b) se va la fraccion
    R_a / (R_a + R_b). Con la isla puesta, cero por construccion."""
    if isla:
        return 0.0
    r_a = r_retorno_rack(r_contacto)
    r_b = r_rama_patches(n_patches)
    return i_rack_a * r_a / (r_a + r_b)


def i_max_plano_a() -> float:
    """La corriente ajena que sola se come el presupuesto de la cadena de tono.

    DERIVADA, no elegida: se toma el tramo de plano que separa a los cuatro
    modulos de la cadena de tono (del slot mas interior al mas exterior de
    los suyos) y se despeja la corriente que produce ahi el objetivo entero
    de 2 cents."""
    tono = SLOTS_X[1:5]
    r = r_plano(max(tono) - min(tono), ANCHO_PLANO_EFECTIVO)
    return (OBJETIVO_CENTS / CENTS_POR_MV) / 1000.0 / r


def cobre_para_cents(i_rack_a: float, objetivo_cents: float) -> float:
    """Los ohm de retorno que harian falta para bajar el desfase a ese
    objetivo. Existe para contestar de una vez a "hazlo grueso y directo"."""
    return (objetivo_cents / CENTS_POR_MV) / 1000.0 / i_rack_a


def _guarda_desfase(p: dict[str, float]) -> None:
    """El desfase rack->instrumento contra el presupuesto de la cadena de tono.

    La aserción NO es que el desfase sea pequeno --no lo es-- sino que o bien
    cabe en el presupuesto, o bien la bahia lo resta recibiendo cada CV en
    diferencial. Es la unica de las dos salidas que el cobre puede dar."""
    if p["diferencial"] >= 0.5:
        return
    mv = desfase_mv(p["i_rack_a"], p["n_patches"])
    assert cents(mv / 1000.0) <= OBJETIVO_CENTS, (
        f"el rack desafina el instrumento: {mv:.2f} mV = "
        f"{cents(mv / 1000.0):.2f} cents con {p['i_rack_a']:.2f} A netos, "
        f"contra un objetivo de {OBJETIVO_CENTS:.1f}. Eso NO se arregla "
        f"ensanchando cobre: haria falta un retorno de "
        f"{cobre_para_cents(p['i_rack_a'], OBJETIVO_CENTS) * 1000:.3f} mohm, "
        f"que es una pletina y no un cable. Se arregla recibiendo cada CV en "
        f"diferencial en la bahia (papel fuente v4 sec.4.1 y sec.10)")


def _guarda_plano(p: dict[str, float]) -> None:
    """La corriente ajena que entra en el plano del instrumento.

    Aqui la salida tampoco es cobre: es que los jacks de la bahia vivan en
    una isla de masa DEL RACK, con lo que la rama (b) no existe."""
    if p["isla"] >= 0.5:
        return
    ia = i_por_el_plano_a(p["i_rack_a"], p["n_patches"], isla=False)
    assert ia <= i_max_plano_a(), (
        f"corriente ajena en el plano: {ia:.2f} A del rack cruzan el plano "
        f"del instrumento con {p['n_patches']:.0f} patches, y el presupuesto "
        f"de la cadena de tono se lo come entero a partir de "
        f"{i_max_plano_a():.2f} A. La salida es la isla de masa del rack bajo "
        f"los jacks de la bahia, no mas cobre")


def _autocomprobacion_rack() -> None:
    """El modelo del rack, contra los tres numeros que el papel publica."""
    # 1. Reproducir sec.4.1 en sus dos cotas de contacto. Si el modelo no da
    #    esos dos, no esta midiendo lo que el papel discutio.
    r_borne = r_retorno_rack(R_BORNE) * 1000.0
    r_crimp = r_retorno_rack(R_CONTACTO) * 1000.0
    assert abs(r_borne - 4.2) < 0.15, (
        f"el retorno con bornes da {r_borne:.2f} mohm y el papel sec.4.1 dice "
        f"4,2: el modelo y el papel no hablan del mismo cable")
    assert abs(r_crimp - 22.0) < 0.6, (
        f"el retorno con crimpados da {r_crimp:.1f} mohm y el papel dice 22")
    # 2. Y la rama de patches, contra su redondo.
    rp = r_patch()
    assert abs(rp - R_PATCH_PAPEL) < 0.020, (
        f"un patch da {rp * 1000:.0f} mohm desglosado y el papel lo redondea "
        f"a {R_PATCH_PAPEL * 1000:.0f}: uno de los dos esta mal")
    # 3. El 22 mV = 27 cents de sec.4.1, con la corriente de PLACA.
    mv = desfase_mv(I_RACK_PLACA_A, 10)
    assert abs(mv - 22.0) < 1.0 and abs(cents(mv / 1000.0) - 27.0) < 1.5, (
        f"a {I_RACK_PLACA_A:.1f} A el papel publica 22 mV = 27 cents y este "
        f"modelo da {mv:.2f} mV = {cents(mv / 1000.0):.2f} cents")
    # 4. LOS DOS LADOS de N. Sin isla, mas patches BAJAN el desfase y SUBEN
    #    la corriente por el plano: los dos terminos van al reves, y por eso
    #    hacen falta los dos requisitos y no uno.
    d1 = desfase_mv(I_RACK_SOSTENIDO_A, 1, isla=False)
    d20 = desfase_mv(I_RACK_SOSTENIDO_A, 20, isla=False)
    i1 = i_por_el_plano_a(I_RACK_SOSTENIDO_A, 1, isla=False)
    i20 = i_por_el_plano_a(I_RACK_SOSTENIDO_A, 20, isla=False)
    assert d20 < d1 and i20 > i1, (
        "con mas patches el desfase tiene que BAJAR y la corriente por el "
        "plano SUBIR; si los dos van en el mismo sentido, el divisor de "
        "corriente esta escrito al reves")
    # 5. Los dos requisitos a la bahia, aseverados donde se comprueban.
    peor_mv = desfase_mv(I_RACK_SOSTENIDO_A, N_PATCHES_PEOR)
    assert BAHIA_RECIBE_EN_DIFERENCIAL, (
        f"con {N_PATCHES_PEOR} patches y {I_RACK_SOSTENIDO_A:.2f} A netos el "
        f"desfase son {peor_mv:.2f} mV = {cents(peor_mv / 1000.0):.2f} cents, "
        f"muy por encima de los {OBJETIVO_CENTS:.1f} de objetivo. Eso NO se "
        f"arregla ensanchando cobre: se arregla recibiendo cada CV en "
        f"diferencial en la bahia (papel fuente v4 sec.4.1 y sec.10). Si esta "
        f"constante se pone en False, el instrumento se desafina con el rack "
        f"cargado")
    assert BAHIA_JACKS_EN_ISLA_DE_RACK, (
        f"sin la isla de masa del rack bajo los jacks, con "
        f"{N_PATCHES_PEOR} patches se van "
        f"{i_por_el_plano_a(I_RACK_SOSTENIDO_A, N_PATCHES_PEOR, isla=False):.2f}"
        f" A del rack por el plano del instrumento, y el presupuesto de la "
        f"cadena de tono se agota en {i_max_plano_a():.2f} A")
    # 6. Los dos canarios, por biseccion y por el texto de su aserto.
    base = {"i_rack_a": I_RACK_SOSTENIDO_A, "n_patches": float(N_PATCHES_PEOR),
            "diferencial": 0.0, "isla": 0.0}
    v = borde_rojo(_guarda_desfase, dict(base), "i_rack_a", 0.0, 20.0,
                   "el rack desafina")
    w = borde_rojo(_guarda_plano, dict(base), "n_patches", 0.0, 200.0,
                   "corriente ajena en el plano")
    print(f"  canario: sin diferencial en la bahia, con mas de {v:.2f} A "
          f"netos de rack el desfase se sale de {OBJETIVO_CENTS:.0f} cents")
    print(f"  canario: sin isla de masa bajo los jacks, con mas de {w:.1f} "
          f"patches el plano del instrumento se pasa de "
          f"{i_max_plano_a():.2f} A")


def _rack_e_instrumento() -> None:
    print("\n--- el rack de invitados contra el instrumento (fuente v4) ---")
    print(f"  retorno del rack (a): {r_retorno_rack(R_BORNE) * 1000:5.2f} mohm "
          f"con bornes de tornillo, {r_retorno_rack(R_CONTACTO) * 1000:5.1f} "
          f"con crimpados")
    print(f"  un cable de patch (b): {r_patch() * 1000:5.0f} mohm "
          f"({R_JACK * 1000:.0f} mohm por casquillo, ESTIMADO)")
    print(f"  neto del rack: {I_RACK_PLACA_A:.2f} A de placa (D-F1), "
          f"{I_RACK_SOSTENIDO_A:.2f} A sostenidos (calor_budget.py)")
    print(f"\n  SIN la isla de masa del rack, N patches en paralelo "
          f"(a {I_RACK_SOSTENIDO_A:.2f} A netos):")
    print(f"    {'N':>3s} {'rama (b)':>9s} {'desfase':>9s} {'cents':>7s} "
          f"{'por el plano':>13s}")
    for n in (1, 2, 5, 10, 20):
        mv = desfase_mv(I_RACK_SOSTENIDO_A, n, isla=False)
        ia = i_por_el_plano_a(I_RACK_SOSTENIDO_A, n, isla=False)
        print(f"    {n:3d} {r_rama_patches(n) * 1000:8.1f}m {mv:8.2f}mV "
              f"{cents(mv / 1000.0):7.2f} {ia:12.2f}A")
    print(f"    (el plano de la cadena de tono se agota en "
          f"{i_max_plano_a():.2f} A: por encima de eso, la corriente de un")
    print("     invitado desafina al instrumento y ningun cobre lo arregla)")
    mv_isla = desfase_mv(I_RACK_SOSTENIDO_A, N_PATCHES_PEOR)
    print("\n  CON la isla puesta, la rama (b) no existe y queda solo el "
          "desfase comun:")
    print(f"    {mv_isla:.2f} mV = {cents(mv_isla / 1000.0):.2f} cents, "
          f"cero amperios por el plano.")
    print(f"    Para bajarlo a {OBJETIVO_CENTS:.0f} cents con cobre harian "
          f"falta {cobre_para_cents(I_RACK_SOSTENIDO_A, OBJETIVO_CENTS) * 1000:.3f}"
          f" mohm de retorno:")
    print("    es una pletina, no un cable. Por eso el CV se recibe en")
    print("    diferencial en la bahia y el termino se resta en vez de sumarse.")
    _autocomprobacion_rack()


# --- reglas de diseno que salen de los numeros ---------------------------
REGLA_SEGMENTO = (
    "Los cuatro modulos de la cadena de tono (MIDI/CV + VCO1..3) van en el "
    "MISMO segmento. Si se reparten entre los dos, el desequilibrio entre los "
    "cables de alimentacion de cada segmento se les suma entero."
)
REGLA_MASA_DOBLE = (
    "Los DOS pines de masa de J2 se pueblan siempre. Poblar uno solo dobla el "
    "termino de cable y se sale del presupuesto."
)
REGLA_NO_PTC_EN_MASA = (
    "El PTC va en +12 V y en -12 V. NUNCA en masa: 1.3 ohm en el retorno son "
    "78 mV a 60 mA, o sea 94 cents. Mataria el instrumento."
)
REGLA_ISLA_BAHIA = (
    "Los jacks de la bahia viven en una isla de masa DEL RACK: sus casquillos "
    "no tocan GNDA. Sin eso, N cables de patch en paralelo son una rama de "
    "retorno del rack por el plano del instrumento, y N no es 1."
)
REGLA_DIFERENCIAL_BAHIA = (
    "Cada CV que cruza la bahia hacia el instrumento se recibe en "
    "diferencial, midiendo el jack contra la masa del rack EN ESE JACK. El "
    "desfase de la fila se resta en vez de sumarse; ningun cobre lo arregla."
)


def _autocomprobacion_plano() -> None:
    """perfil_plano() ya estuvo mal una vez. Se contrasta a mano.

    Tres slots por rama a 38/86/134 mm del centro con 150/50/50 mA en las
    posiciones exterior/media/interior. A mano, acumulando de dentro a fuera:

        V(38)  = (0.15+0.05+0.05) * r * 38
        V(86)  = V(38)  + (0.15+0.05) * r * 48
        V(134) = V(86)  +  0.15      * r * 48
    """
    r = R_CUADRO / ANCHO_PLANO_EFECTIVO / 1000.0        # ohm por mm
    v38 = 0.25 * r * 38
    v86 = v38 + 0.20 * r * 48
    v134 = v86 + 0.15 * r * 48
    esperado = [v134, v86, v38, v38, v86, v134]
    obtenido = perfil_plano([I_MASA_EURO, I_MASA_SAM17, I_MASA_SAM17,
                             I_MASA_SAM17, I_MASA_SAM17, I_MASA_EURO])
    for e, o in zip(esperado, obtenido):
        assert abs(e - o) < 1e-9, f"perfil_plano mal: {o*1e6:.1f} != {e*1e6:.1f} uV"


def demo() -> int:
    _autocomprobacion_plano()
    print(f"cobre a {T_OP:.0f} C: {R_CUADRO:.3f} mohm/cuadro\n")

    # ---- 1. el plano, con la cadena de tono junta y cerca del centro ----
    # peor reparto realista: un Euro glotonon en cada punta, los SAM17 dentro
    corr = [I_MASA_EURO, I_MASA_SAM17, I_MASA_SAM17,
            I_MASA_SAM17, I_MASA_SAM17, I_MASA_EURO]
    v = perfil_plano(corr)
    sam17 = v[1:5]
    d_plano = max(sam17) - min(sam17)
    print("perfil de masa del plano [uV]:",
          " ".join(f"{x*1e6:6.1f}" for x in v))
    print(f"  peor par DENTRO de la cadena de tono: {cents(d_plano):.2f} cents")

    # ---- 2. el cable de bajada -----------------------------------------
    r_sam17 = r_cable(150, "24AWG", 2)      # J2: 2 pines de masa
    r_euro = r_cable(150, "28AWG", 6)       # 16 pines: 3 pares de masa = 6
    d_cable = I_MASA_SAM17 * r_sam17
    print(f"\ncable SAM17 (150 mm, 2x24 AWG + contactos): {r_sam17*1000:.1f} mohm"
          f" -> {cents(d_cable):.2f} cents")
    print(f"cable Euro  (150 mm, 6x28 AWG + contactos): {r_euro*1000:.1f} mohm")

    total = cents(d_plano) + cents(d_cable)
    print(f"\nTOTAL cadena de tono: {total:.2f} cents "
          f"(objetivo <= {OBJETIVO_CENTS})")
    assert total <= OBJETIVO_CENTS, f"presupuesto de masa reventado: {total:.2f}"

    # ---- 3. lo que pasa si te saltas cada regla -------------------------
    print("\nsi se rompe cada regla:")
    r_pista = r_plano(160, 5.0)             # pista de 5 mm en vez de plano
    mal_pista = cents(0.35 * r_pista)       # 350 mA por medio segmento
    print(f"  pista de 5 mm en vez de plano ... +{mal_pista:5.2f} cents")
    assert mal_pista > OBJETIVO_CENTS, "la pista deberia suspender"

    r_1masa = r_cable(150, "24AWG", 1)
    print("  un solo pin de masa en J2 ...... "
          f"+{cents(I_MASA_SAM17*(r_1masa - r_sam17)):5.2f} cents")

    r_largo = r_cable(500, "24AWG", 2)
    print("  cable de 500 mm en vez de 150 .. "
          f"+{cents(I_MASA_SAM17*(r_largo - r_sam17)):5.2f} cents")

    # El punto de partida: la tesis, con jumpers en cadena. Aqui el numero no
    # lo pone el cobre sino el CONTACTO, y un Dupont crimpado a mano no es un
    # contacto de 10 mohm: la horquilla de manual es 50-100 mohm, y empeora al
    # oxidarse. Se dan las dos cotas porque la diferencia es 5x y taparla
    # inflando o desinflando el numero seria hacer trampa en las dos
    # direcciones.
    r_cobre_tesis = RHO / SECCION["24AWG"] * 0.5
    for etiqueta, r_c in (("contacto bueno, 10 mohm", 10e-3),
                          ("Dupont real,   75 mohm", 75e-3)):
        r_tesis = r_cobre_tesis + 6 * r_c        # 3 saltos = 6 contactos
        print(f"  daisy-chain tesis ({etiqueta}) {cents(I_MASA_SAM17*r_tesis):6.1f} cents")
    r_tesis = r_cobre_tesis + 6 * 75e-3
    assert cents(I_MASA_SAM17 * r_tesis) > 10 * total, \
        "el daisy-chain deberia ser MUCHO peor; si no, algo esta mal calculado"

    # ---- 4. el PTC jamas en masa ---------------------------------------
    ptc = cents(0.060 * 1.3)                # 60 mA sobre 1.3 ohm
    print(f"\n  PTC puesto en masa por error ... {ptc:5.1f} cents  <- {REGLA_NO_PTC_EN_MASA[:38]}...")
    assert ptc > 50, "el PTC en masa tiene que salir catastrofico"

    # ---- 5. el rack de invitados (fuente v4, sec.4.1) -------------------
    _rack_e_instrumento()

    # ---- 6. y si los dos requisitos de la bahia tienen dueno ------------
    papel = papel_de_la_bahia()
    if papel is not None:
        print()
        print("  los dos requisitos de la bahia tienen papel: "
              + os.path.basename(papel))
        print("")
        print("OK: presupuesto cerrado.")
        return 0
    print()
    print("  " + REGLA_ISLA_BAHIA)
    print("  " + REGLA_DIFERENCIAL_BAHIA)
    print()
    print("HUECO: el presupuesto de masa del INSTRUMENTO cierra en 1,21 "
          "cents, pero el del RACK no cierra por cobre: con la carga "
          "sostenida el desfase son 20,29 cents contra un objetivo de 2, "
          "y lo que lo arregla son dos requisitos que este guion NO puede "
          "verificar --la isla de masa del rack bajo los jacks y la "
          "recepcion diferencial de cada CV--. Aqui viven como "
          "constantes, y aseverarlas contra si mismas seria una puerta "
          "que no vigila nada. Su dueno es el papel de la bahia (#166 "
          "sec.5, #183), que todavia no existe en docs/superpowers/"
          "specs/. Cuando exista, esta puerta se pone verde sola.")
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
