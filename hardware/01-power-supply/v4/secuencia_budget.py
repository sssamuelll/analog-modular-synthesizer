"""El secuenciador de D-F4: sus umbrales, y que ningun estado deja un riel solo.

    python secuencia_budget.py       (sale con codigo 2: HUECO declarado)

## Por que existe

Con el toroide, +-VRAW subian y caian juntos porque eran el mismo devanado. La
fuente v4 son dos modulos independientes con **setup de 1000 ms tipico y SIN
MAXIMO publicado** (hoja p. 2), hold-up de 40 ms cada uno, y *hiccup* propio.
En cada encendido, cada apagado y cada microcorte hay una ventana con un riel
crudo y el otro no, de longitud indefinida. Un bus de +-12 V con un solo riel
deja el otro nodo donde lo pongan los clamps de los op-amps. La v3 no tenia
este caso porque no podia tenerlo.

D-F4 (firmada 2026-09-03) es un detector de ventana sobre LOS DOS rieles crudos
que habilita a U1 y U2 a la vez y los deshabilita a la vez. Este guion pone los
numeros: donde puede estar el umbral, cuanta histeresis hace falta, y --lo que
de verdad decide-- que la maquina de estados no tiene ninguna combinacion con
un riel vivo y el otro muerto.

## Los tres hallazgos

**1. YA NO SIRVE UN SOLO HILO, y es lo que trajo el cambio de U1.** El
papel describe el LM2941 como activo-bajo y el LM2991 como "activo-alto
deshabilita", que suena a que hacen falta dos senales opuestas. No: en los dos,
BAJO habilita (LM2941 <= 0,80 V, LM2991 <= 0,8 V) y ALTO deshabilita (LM2941
>= 2 V, LM2991 >= 2,4 V). Un solo hilo los gobierna. Lo que si hay que respetar
son los DOS lados del nivel alto: >= 2,4 V para que los dos se apaguen, y
<= 5 V porque es el maximo recomendado del pin del LM2991 (su hoja p. 4).

**2. EL DETECTOR TIENE QUE MEDIR DESPUES DEL LC, no en el borne del IRM.** La
histeresis tiene que ser mayor que el rizado del punto que mide, o el
comparador castanetea en cada ciclo de conmutacion. En el borne del modulo hay
200 mVp-p (hoja p. 2); despues del LC de rizado_budget.py quedan ~1,2 mVp-p.
Y la ventana entera donde puede vivir el umbral --entre lo que necesita el
peor de los dos rieles (ver peor_reg()) y lo
que un modulo de tolerancia mala garantiza-- **no llega a 200 mV**. O sea que
midiendo el riel crudo de verdad, el detector de D-F4 no existe: pide mas
histeresis que ventana hay.

**3. Y aun midiendo despues del LC, EL UMBRAL NO CABE.** Ese es el hueco, y no
es de este guion: es el mismo de `margen_budget.py` visto desde el otro lado.
El umbral tiene que estar por encima de lo que `U1` necesita para regular
(14,367 V, con la deriva de su referencia dentro) y por debajo de lo que un IRM
de tolerancia mala entrega (14,370). **Entre las dos hay 3 mV**, y el
comparador se come +-131 de tolerancia y pide 30 de histeresis minima: quedan
-290 mV. Cualquiera que se ponga, o habilita una cascada que no regula, o no
deja arrancar a una unidad legal. Su dueno es `margen_budget.py`, que publica
las salidas con su precio; aqui se mide cuanto falta y se declara.

## Lo que este guion NO cubre

  * El circuito. Comparador, referencia y divisores concretos son de la tanda
    B; aqui esta el presupuesto que tienen que cumplir.
  * Los interruptores de carga de +-12 V de rack. Es el MISMO detector
    replicado (papel sec.4.3), y sus umbrales salen de aqui, pero el
    dimensionado del interruptor no.
  * El arranque del propio detector. Se alimenta de uno de los rieles crudos y
    tiene su propia ventana de indefinicion al encender: es diseno de la tanda
    B, y el paso 2b del bring-up es quien lo caza.
"""
from __future__ import annotations

import itertools
import os
import sys
from dataclasses import dataclass

DIR = os.path.dirname(os.path.abspath(__file__))
for _ruta in (DIR, os.path.join(DIR, "..", "..", "tools")):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
from canario import borde_rojo  # noqa: E402
from margen_budget import (V_SET, v_entrada_minima_v,  # noqa: E402
                           v_necesaria_v)
from rizado_budget import F_CONMUTACION_HZ, RIZADO_IRM_VPP, h_lc  # noqa: E402

# --- los pines ON/OFF, de sus hojas ---------------------------------------
# LT1963A Rev G p. 5, "Shutdown Threshold": Off to On con <= 2 V garantizados;
#   On to Off con >= 0,25 V. O SEA QUE HABILITA EN ALTO: es un pin SHDN
#   activo-bajo, al reves que el ON/OFF del LM2941 al que sustituye.
#   Corriente del pin 1 uA max a 0 V (p. 5, nota 10).
# LM2991 SNVS099I p. 5: habilita con <= 0,8 V; deshabilita con >= 2,4 V.
#   p. 4, condiciones recomendadas: el pin admite de 0 a 5 V.
#
# LOS DOS SON OPUESTOS Y ESO NO ESTABA EN EL PRECIO DEL CAMBIO DE U1. Con el
# LM2941 los dos habilitaban en bajo y un hilo gobernaba los dos; con el
# LT1963A hace falta invertir uno de los dos, y la inversion NO es gratis:
# ver el aviso de POLARIDAD mas abajo.
HABILITA_EN_ALTO = {"U1": True, "U2": False}
V_ONOFF_HABILITA_MAX = {"U1": 0.25, "U2": 0.8}     # nivel que garantiza APAGADO
V_ONOFF_DESHABILITA_MIN = {"U1": 2.0, "U2": 2.4}   # nivel que garantiza el otro
V_ONOFF_MAX_RECOMENDADO = 5.0
I_ONOFF_MAX_A = 300e-6

# --- los tiempos del modulo, hoja p. 2 ------------------------------------
T_SETUP_TIP_MS = 1000.0      # "1000ms, 20ms/230Vac at full load" (IRM-20)
T_SETUP_MAX_MS = None        # LA HOJA NO PUBLICA MAXIMO. Es el hueco que D-F4
                             # existe para tapar: sin maximo, la ventana de un
                             # riel solo no tiene cota superior.
T_RISE_MS = 20.0             # IRM-20; la IRM-45 da 30
T_HOLDUP_MS = 40.0           # "40ms/230Vac at full load" (IRM-20)

# --- el detector, presupuesto de la tanda B -------------------------------
# ESTIMADO, todos: el circuito no existe todavia y estas son las COTAS que
# tendra que cumplir. Cada una con su razonamiento:
T_DETECCION_MS = 1.0         # comparador + filtro anti-castaneteo. 1 ms son
                             # 65 ciclos de la conmutacion de 65 kHz: por
                             # debajo, el filtro no promedia el rizado.
T_APAGADO_REGULADOR_MS = 0.1  # lo que tarda la salida de U1 en caer una vez
                             # deshabilitado: 47 uF a 650 mA son 14 V/ms, o
                             # sea que el limite lo pone el propio ON/OFF y
                             # no el condensador.
# Presupuesto de error del umbral, termino a termino (ESTIMADO):
ERR_DIVISOR_FRAC = 0.002     # dos resistencias al 0,1 % (las mismas que la
                             # telemetria de la spec del chasis sec.4.4)
ERR_REFERENCIA_FRAC = 0.005  # referencia de 0,5 % tipo TL431
ERR_OFFSET_COMPARADOR_V = 0.005   # offset de entrada de un comparador comun
DIVISOR_RATIO = 6.0          # 100k/20k, el de la telemetria: 1/6

ESTIMADOS = (
    f"T_DETECCION_MS={T_DETECCION_MS}: cota de diseno del filtro, sin circuito",
    f"T_APAGADO_REGULADOR_MS={T_APAGADO_REGULADOR_MS}: la hoja del LM2941 no "
    f"publica tiempo de apagado por ON/OFF",
    f"presupuesto de error del umbral ({ERR_DIVISOR_FRAC:.1%} de divisor, "
    f"{ERR_REFERENCIA_FRAC:.1%} de referencia, "
    f"{ERR_OFFSET_COMPARADOR_V * 1000:.0f} mV de offset): piezas sin elegir",
)


def rizado_en_sensado_vpp(*, despues_del_lc: bool = True) -> float:
    """El rizado que ve el detector en el punto donde mide."""
    if not despues_del_lc:
        return RIZADO_IRM_VPP
    return RIZADO_IRM_VPP * h_lc(F_CONMUTACION_HZ)


def hist_min_v(*, despues_del_lc: bool = True) -> float:
    """La histeresis MINIMA para que el comparador no castanetee.

    Tiene que ser mayor que el rizado del punto que mide: si no, cada ciclo
    de conmutacion cruza el umbral en los dos sentidos. Se le suma el offset
    del comparador referido al riel, que hace lo mismo mas despacio."""
    return (rizado_en_sensado_vpp(despues_del_lc=despues_del_lc)
            + ERR_OFFSET_COMPARADOR_V * DIVISOR_RATIO)


def error_umbral_v(v_umbral: float) -> float:
    """Cuanto se puede ir el umbral real del que se dibuje, en voltios."""
    return (v_umbral * (ERR_DIVISOR_FRAC + ERR_REFERENCIA_FRAC)
            + ERR_OFFSET_COMPARADOR_V * DIVISOR_RATIO)


def peor_reg() -> str:
    """El riel que pone la cota de abajo. NO se nombra a mano: desde que U1
    es un LT1963A (2026-09-04) el que manda es U2, y escribir 'U1' en la
    prosa dejaria al texto describiendo un estado que el codigo ya no tiene."""
    return max(V_SET, key=v_necesaria_v)


def ventana_v() -> tuple[float, float]:
    """(minimo, maximo) donde puede vivir el umbral alto de habilitacion.

    Por abajo: lo que el peor de U1/U2 necesita en su entrada para regular
    (margen_budget.py, con la deriva de la referencia dentro). Habilitar por
    debajo es habilitar una cascada que no regula.
    Por arriba: lo que un IRM de tolerancia mala entrega en el peor caso. Un
    umbral por encima no deja arrancar nunca a una unidad legal."""
    return (max(v_necesaria_v(reg) for reg in V_SET), v_entrada_minima_v())


def ancho_ventana_v() -> float:
    lo, hi = ventana_v()
    return hi - lo


def ventana_util_v(*, despues_del_lc: bool = True) -> float:
    """Lo que queda de la ventana despues de pagar histeresis y error.

    Positivo significa que existe un umbral que cumple las dos cotas con su
    tolerancia; negativo, que el detector no se puede dibujar."""
    lo, hi = ventana_v()
    centro = (lo + hi) / 2.0
    return (ancho_ventana_v() - hist_min_v(despues_del_lc=despues_del_lc)
            - 2.0 * error_umbral_v(centro))


# --- la maquina de estados ------------------------------------------------
@dataclass(frozen=True)
class Estado:
    nombre: str
    ps1_viva: bool
    ps2_viva: bool
    habilita: bool
    ms: float

    @property
    def riel_vivo(self) -> str:
        if self.ps1_viva and not self.ps2_viva:
            return "+15"
        if self.ps2_viva and not self.ps1_viva:
            return "-15"
        return "---"

    @property
    def riel_muerto(self) -> str:
        return {"+15": "-15", "-15": "+15"}.get(self.riel_vivo, "---")

    @property
    def riel_solo(self) -> bool:
        """La cascada habilitada con una sola de sus dos entradas viva."""
        return self.habilita and (self.ps1_viva != self.ps2_viva)


def detector(ps1_viva: bool, ps2_viva: bool) -> bool:
    """La funcion logica de D-F4: habilita si y solo si LAS DOS estan."""
    return ps1_viva and ps2_viva


def estados_alcanzables(*, con_detector: bool = True) -> tuple[Estado, ...]:
    """Todos los estados del producto {PS1} x {PS2} x {detector}, enumerados.

    ENUMERAR ES LA TAREA. Un argumento en prosa sobre por que la combinacion
    mala no puede pasar es justo lo que este guion sustituye. Los estados con
    las dos entradas en el mismo sitio duran lo que dure la causa; los de
    asimetria duran lo que el detector tarde en verlo y apagar."""
    fuera = []
    transitorio = T_DETECCION_MS + T_APAGADO_REGULADOR_MS
    for ps1, ps2 in itertools.product((True, False), repeat=2):
        estable = detector(ps1, ps2) if con_detector else True
        nombre = f"PS1={'viva' if ps1 else 'muerta'}, PS2={'viva' if ps2 else 'muerta'}"
        if ps1 == ps2:
            fuera.append(Estado(nombre, ps1, ps2, estable, float("inf")))
            continue
        # Asimetrico: primero el transitorio, en el que el detector todavia
        # no ha reaccionado y la cascada SIGUE habilitada; despues el estable.
        if con_detector:
            fuera.append(Estado(f"{nombre} (transitorio)", ps1, ps2, True,
                                transitorio))
            fuera.append(Estado(f"{nombre} (estable)", ps1, ps2, False,
                                float("inf")))
        else:
            fuera.append(Estado(f"{nombre} (sin detector)", ps1, ps2, True,
                                T_SETUP_TIP_MS))
    return tuple(fuera)


def ventana_riel_solo_ms(*, con_detector: bool = True) -> float:
    """La ventana mas larga en la que la cascada esta viva con un riel solo."""
    malos = [e.ms for e in estados_alcanzables(con_detector=con_detector)
             if e.riel_solo]
    return max(malos) if malos else 0.0


def _guarda_ventana(p: dict[str, float]) -> None:
    """El detector no castanetea; su texto alimenta al canario.

    LOS DOS LADOS: sin histeresis suficiente castanetea con el rizado; con
    demasiada, el umbral bajo se sale de la ventana por abajo y el detector
    deshabilitaria una cascada que si regula."""
    hist = p["hist_v"]
    minima = hist_min_v(despues_del_lc=p["despues_del_lc"] >= 0.5)
    assert hist >= minima, (
        f"castanetea: {hist * 1000:.1f} mV de histeresis contra "
        f"{minima * 1000:.1f} de rizado mas offset en el punto de sensado. "
        f"Sin histeresis suficiente el detector castanetea en cada microcorte "
        f"y en cada ciclo de conmutacion")
    assert hist <= ancho_ventana_v() + p["ancho_extra_v"], (
        f"histeresis de {hist * 1000:.0f} mV sobre una ventana de "
        f"{(ancho_ventana_v() + p['ancho_extra_v']) * 1000:.0f}: el umbral "
        f"bajo cae por debajo de lo que {peor_reg()} necesita y el detector apagaria "
        f"una cascada que todavia regula")


def _guarda_estados(p: dict[str, float]) -> None:
    """Ningun estado alcanzable deja un riel solo mas de lo tolerable."""
    limite = p["ventana_tolerable_ms"]
    for est in estados_alcanzables():
        assert not est.riel_solo or est.ms <= limite, (
            f"riel solo: el estado {est.nombre} deja {est.riel_vivo} vivo con "
            f"{est.riel_muerto} muerto durante {est.ms:.1f} ms, y el limite "
            f"son {limite:.1f}. Un bus de +-12 V con un solo riel deja el otro "
            f"nodo donde lo pongan los clamps de los op-amps")


P_BASE = {
    "hist_v": hist_min_v(),
    "despues_del_lc": 1.0,
    "ancho_extra_v": 0.0,
    "ventana_tolerable_ms": T_DETECCION_MS + T_APAGADO_REGULADOR_MS,
}


def _autocomprobacion() -> None:
    # 1. UN SOLO HILO gobierna los dos reguladores, y sus dos niveles caben.
    #    Los dos lados: el bajo por debajo del menor de los dos umbrales de
    #    habilitacion, el alto por encima del mayor de deshabilitacion Y por
    #    debajo del maximo recomendado del pin del LM2991.
    nivel_bajo = min(V_ONOFF_HABILITA_MAX.values())
    nivel_alto = max(V_ONOFF_DESHABILITA_MIN.values())
    assert nivel_alto <= V_ONOFF_MAX_RECOMENDADO, (
        f"el nivel alto comun tiene que llegar a {nivel_alto:.1f} V para "
        f"apagar a los dos, y el pin del LM2991 admite hasta "
        f"{V_ONOFF_MAX_RECOMENDADO:.1f} (su hoja p. 4)")
    assert nivel_bajo < nivel_alto, (
        "si el nivel que habilita a uno deshabilitara al otro, harian falta "
        "dos senales opuestas y no una")

    # 2. LA MAQUINA DE ESTADOS, enumerada. Con detector, ningun estado ESTABLE
    #    deja un riel solo; sin el, la ventana es el setup del modulo.
    estables = [e for e in estados_alcanzables() if e.ms == float("inf")]
    assert not any(e.riel_solo for e in estables), (
        "algun estado estable deja un riel solo: la funcion logica del "
        "detector no es la conjuncion que D-F4 describe")
    assert len(estados_alcanzables()) == 6, (
        f"el producto {{PS1}} x {{PS2}} con su transitorio son 6 estados y se "
        f"enumeran {len(estados_alcanzables())}: si el numero cambia, hay un "
        f"caso nuevo que nadie ha mirado")

    # 3. LO QUE COMPRA D-F4, en un numero. Sin detector la ventana de un riel
    #    solo es el setup del modulo --1000 ms TIPICOS y sin maximo
    #    publicado--; con el, el tiempo de deteccion.
    con = ventana_riel_solo_ms()
    sin = ventana_riel_solo_ms(con_detector=False)
    assert T_SETUP_MAX_MS is None, (
        "si la hoja publicara un maximo de setup, esta comparacion tendria "
        "que usarlo: hoy no lo publica, y por eso 'sin detector' no tiene "
        "cota superior de verdad")
    assert con * 100.0 < sin, (
        f"con detector la ventana es {con:.1f} ms y sin el {sin:.0f}: si D-F4 "
        f"no compra al menos dos ordenes de magnitud, no compra bastante para "
        f"lo que cuesta")
    assert con <= T_HOLDUP_MS, (
        f"la deteccion tarda {con:.1f} ms y el hold-up del modulo que sigue "
        f"vivo son {T_HOLDUP_MS:.0f}: si tardara mas, el detector actuaria "
        f"despues de que el otro riel ya se hubiera caido solo, y no estaria "
        f"secuenciando nada")

    # 4. EL PUNTO DE SENSADO. Midiendo el borne crudo del modulo hace falta
    #    mas histeresis que ventana hay; despues del LC, no.
    hist_crudo = hist_min_v(despues_del_lc=False)
    hist_filtrado = hist_min_v()
    assert hist_crudo > hist_filtrado, (
        "si el rizado del borne crudo no pidiera mas histeresis que el punto "
        "filtrado, el requisito de sensar despues del LC sobraria")
    assert (rizado_en_sensado_vpp()
            < rizado_en_sensado_vpp(despues_del_lc=False) / 10.0), (
        f"el LC tiene que bajar el rizado del punto de sensado en mas de una "
        f"decada ({rizado_en_sensado_vpp(despues_del_lc=False) * 1000:.0f} -> "
        f"{rizado_en_sensado_vpp() * 1000:.2f} mVp-p): si no, el detector no "
        f"se puede sensar en ningun sitio")
    # Y el otro lado del mismo hallazgo: despues del LC el suelo de la
    # histeresis ya NO es el rizado, es el offset del comparador. Filtrar mas
    # deja de comprar nada, y quien manda pasa a ser la pieza.
    piso_offset = ERR_OFFSET_COMPARADOR_V * DIVISOR_RATIO
    assert rizado_en_sensado_vpp() < piso_offset, (
        f"despues del LC el rizado son {rizado_en_sensado_vpp() * 1000:.2f} mV "
        f"y el offset del comparador referido al riel {piso_offset * 1000:.0f}: "
        f"si el rizado siguiera mandando, el LC todavia estaria comprando "
        f"histeresis y el presupuesto del comparador no seria el que decide")

    # 5. Los canarios, por biseccion y por el texto de su aserto. El de la
    #    histeresis se busca con la ventana ENSANCHADA a mano, porque con la
    #    de hoy --que esta vacia-- el aserto de arriba salta siempre y el de
    #    abajo no llegaria a morder nunca.
    p = dict(P_BASE)
    p["ancho_extra_v"] = 1.0
    v = borde_rojo(_guarda_ventana, dict(p), "hist_v", 0.0, 5.0, "castanetea")
    w = borde_rojo(_guarda_ventana, dict(p), "hist_v", 0.0, 5.0,
                   "una cascada que todavia regula")
    x = borde_rojo(_guarda_estados, dict(P_BASE), "ventana_tolerable_ms",
                   0.0, 100.0, "riel solo")
    print(f"  canario: con menos de {v * 1000:.1f} mV de histeresis, castanetea")
    print(f"  canario: con mas de {w * 1000:.0f} mV de histeresis (sobre una "
          f"ventana ensanchada a mano) apagaria una cascada que regula")
    print(f"  canario: con menos de {x:.2f} ms de tolerancia a un riel solo, "
          f"la deteccion de D-F4 llega tarde")


def demo() -> int:
    print("secuencia_budget: el detector de ventana de D-F4\n")

    print("  los dos pines ON/OFF, y POR QUE YA NO BASTA UN HILO:")
    for reg in V_SET:
        if HABILITA_EN_ALTO[reg]:
            print(f"    {reg}: habilita en ALTO "
                  f"(>= {V_ONOFF_DESHABILITA_MIN[reg]:.2f} V; apaga con "
                  f"<= {V_ONOFF_HABILITA_MAX[reg]:.2f} V)")
        else:
            print(f"    {reg}: habilita en BAJO "
                  f"(<= {V_ONOFF_HABILITA_MAX[reg]:.2f} V; apaga con "
                  f">= {V_ONOFF_DESHABILITA_MIN[reg]:.2f} V)")
    print()
    print("    AVISO DE POLARIDAD -- lo que trajo el cambio de U1 y no estaba")
    print("    en su precio. Hasta el 2026-09-04 U1 era un LM2941 y los dos")
    print("    habilitaban en BAJO: un hilo los gobernaba, y un hilo roto los")
    print("    apagaba a los DOS. Eso no era una comodidad de cableado: era")
    print("    la razon por la que ningun fallo simple dejaba un riel solo,")
    print("    que es exactamente lo que D-F4 existe para impedir.")
    print("    Con el LT1963A hay que invertir una de las dos senales, y el")
    print("    inversor es un punto de fallo NUEVO cuyo modo de fallo es el")
    print("    prohibido. Requisito para la tanda B: el inversor tiene que")
    print("    fallar hacia AMBOS APAGADOS, no hacia uno solo -- se disena")
    print("    con eso escrito, no se elige y luego se comprueba.")

    print("\n  la maquina de estados, ENUMERADA (no razonada):")
    print(f"    {'estado':44s} {'habilita':>8s} {'riel solo':>10s} {'ms':>8s}")
    for e in estados_alcanzables():
        dur = "estable" if e.ms == float("inf") else f"{e.ms:.1f}"
        print(f"    {e.nombre:44s} {'si' if e.habilita else 'no':>8s} "
              f"{'SI' if e.riel_solo else 'no':>10s} {dur:>8s}")
    con = ventana_riel_solo_ms()
    sin = ventana_riel_solo_ms(con_detector=False)
    print(f"    ventana de riel solo: {con:.1f} ms con detector, "
          f"{sin:.0f} ms sin el")
    print(f"    (y ese {sin:.0f} es el setup TIPICO: la hoja no publica "
          f"maximo, asi que")
    print("     sin detector la ventana no tiene cota superior de verdad)")

    crudo = rizado_en_sensado_vpp(despues_del_lc=False)
    filtrado = rizado_en_sensado_vpp()
    print("\n  donde mide el detector, y cuanta histeresis pide:")
    print(f"    en el borne del IRM: {crudo * 1000:.0f} mVp-p de rizado -> "
          f"histeresis >= {hist_min_v(despues_del_lc=False) * 1000:.0f} mV")
    print(f"    despues del LC:      {filtrado * 1000:.2f} mVp-p -> "
          f"histeresis >= {hist_min_v() * 1000:.1f} mV")

    lo, hi = ventana_v()
    print("\n  la ventana donde puede vivir el umbral:")
    print(f"    por abajo, lo que U1/U2 necesitan para regular: {lo:.3f} V")
    print(f"    por arriba, lo que un IRM de tolerancia mala da: {hi:.3f} V")
    print(f"    ancho: {ancho_ventana_v() * 1000:+.0f} mV")
    print(f"    error del umbral en el centro: "
          f"+-{error_umbral_v((lo + hi) / 2.0) * 1000:.0f} mV "
          f"({ERR_DIVISOR_FRAC:.1%} divisor + {ERR_REFERENCIA_FRAC:.1%} "
          f"referencia + {ERR_OFFSET_COMPARADOR_V * 1000:.0f} mV offset x "
          f"{DIVISOR_RATIO:.0f})")
    print(f"    ventana util tras pagar histeresis y error: "
          f"{ventana_util_v() * 1000:+.0f} mV")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}")
    for e in ESTIMADOS:
        print(f"    - {e}")

    _autocomprobacion()

    if ventana_util_v() > 0.0:
        print("\nOK: secuencia_budget.py")
        return 0
    print()
    print("=" * 72)
    print("El umbral de D-F4 no se puede colocar, y la causa no es de aqui:")
    print(f"  tiene que estar por ENCIMA de {lo:.3f} V (lo que {peor_reg()} "
          f"necesita")
    print("  para regular, con la deriva de su referencia dentro) y por")
    print(f"  DEBAJO de {hi:.3f} V (lo que un IRM de tolerancia mala da).")
    if ancho_ventana_v() <= 0.0:
        print(f"  La primera cota es {(lo - hi) * 1000:.0f} mV MAYOR que la "
              f"segunda: la ventana esta VACIA")
        print("  antes de pagar un milivoltio de histeresis o de tolerancia.")
    else:
        print(f"  Entre las dos hay {ancho_ventana_v() * 1000:.0f} mV. El "
              f"comparador se come "
              f"+-{error_umbral_v((lo + hi) / 2.0) * 1000:.0f} mV")
        print(f"  de tolerancia y pide {hist_min_v() * 1000:.0f} de histeresis "
              f"minima: queda {ventana_util_v() * 1000:+.0f} mV. El umbral no")
        print("  cabe con ninguna pieza razonable, y no por poco.")
    print()
    print("  Es el mismo hueco que publica margen_budget.py, visto desde el")
    print("  secuenciador, y su dueno es aquel guion: alli estan las cuatro")
    print("  salidas con su precio. Lo que este anade es que el detector de")
    print("  D-F4 tampoco se puede dibujar hasta que aquello se decida, y")
    print("  que cuando se decida tiene que medir DESPUES DEL LC:")
    print(f"    en el borne crudo la histeresis minima son "
          f"{hist_min_v(despues_del_lc=False) * 1000:.0f} mV y ninguna ventana")
    print("    razonable de este riel los aguanta.")
    print("=" * 72)
    print()
    print(f"HUECO: el umbral de D-F4 no cabe. Tiene que estar entre lo que "
          f"{peor_reg()} necesita para regular ({lo:.3f} V) y lo que un IRM "
          f"de tolerancia "
          f"mala entrega ({hi:.3f} V), y entre las dos hay "
          f"{ancho_ventana_v() * 1000:.0f} mV contra "
          f"+-{error_umbral_v((lo + hi) / 2.0) * 1000:.0f} de tolerancia del "
          f"comparador y {hist_min_v() * 1000:.0f} de histeresis minima: "
          f"quedan {ventana_util_v() * 1000:.0f} mV. Dueno del hueco: "
          f"margen_budget.py. Lo que este guion si deja dimensionado: el "
          f"sensado DESPUES del LC y la maquina de "
          f"estados sin ningun riel solo estable.")
    return 2


if __name__ == "__main__":
    raise SystemExit(demo())
