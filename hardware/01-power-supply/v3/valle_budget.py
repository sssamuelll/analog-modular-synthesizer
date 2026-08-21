"""El valle de VRAW de la v3, simulado y aseverado. El numero que decide la placa.

    python valle_budget.py          (necesita el Python de KiCad: ngspice.dll)

## Por que existe

El paso 4 del bring-up para la placa si el valle medido cae por debajo de
**13,46 V**: por debajo de ahi no hay setpoint que funcione y ningun giro de
trimmer lo arregla. Contra ese umbral se compara un valle **simulado de
14,12 V**, y ese numero vivia en una TABLA de markdown -- `design-notes.md`
sec.16.4 y sec.16.5 -- sin un solo script que lo reprodujera.

El unico simulador ejecutable de la fuente, `simulations/power/run_sim.py`,
modela la **v1**: 12 V a 2 A de secundario, 4700 uF de bulk, 450 mA de carga y
2 V de dropout de 78xx. Nada de eso esta en la v3. El propio script lo declara
como HUECO desde el issue #128.

O sea: el numero que decide la placa estaba simulado, pero no se podia volver
a correr. Eso es exactamente lo que la constitucion llama un numero en prosa,
y envejece en silencio.

## Lo que este script hace distinto del de la v1

`run_sim.py` **barre** la regulacion del transformador (`reg`) en tres valores,
porque la v1 no sabia cual era: el BOM no la fijaba. Aqui no hace falta barrer
nada. La hoja de Nuvotem del `0120P1-2-012` da los dos extremos --13,42 V en
vacio y 12 V a 5 A-- y de ahi sale la resistencia efectiva por semidevanado sin
suponer nada:

    R_SEC = (13,42 - 12) / 5 = 0,284 ohm

Confirmada contra la hoja el 2026-08-19 (design-notes sec.16.4). El 47 % de
esos 0,284 es resistencia ohmica (0,1336) y el resto reactancia de dispersion,
pero para el valle manda la efectiva, que es la que limita el pico de carga.

## La cota es pesimista a proposito

Red a **207 V** (-10 %), carga al **techo** del censo (650 mA por riel) y en
frio. Si el caso peor todavia cabe, es una regla; si solo cabe el tipico, es
una plegaria.

## Lo que este calculo NO cubre

  * **El arranque.** El inrush con 9400 uF por riel y el NTC de 5 ohm
    limitando: es lo que justifica el fusible de 1,6 A lento del IEC, y hoy
    sigue siendo un calculo de I2t en prosa (v2 sec.3.0.1), no simulado.
  * **La cascada aguas abajo.** Aqui se simula hasta VRAW. Que el pre-regulador
    y los LT3045/LT3094 conviertan ese valle en +-12,000 V lo responden sus
    dropouts garantizados (v2 sec.1.5), no este modelo.
  * **El ruido.** Es lo que compra los LT3045, y no se simula: se mide, y hace
    falta el LNA del issue #58.
  * **La temperatura.** Los 0,284 ohm son a temperatura de hoja. Un devanado
    caliente sube su resistencia y baja el valle; por eso el bring-up mide en
    frio Y tras 30 min.
"""
from __future__ import annotations

import os
import sys

# El arnes de ngspice ya existe y funciona: se importa en vez de duplicarlo.
# `run_sim.py` no ejecuta nada al importarse (todo cuelga de su __main__).
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "..", "..", "simulations", "power"))
from run_sim import Ng                                          # noqa: E402

# --- el transformador, de la hoja del fabricante --------------------------
# Nuvotem Talema 0120P1-2-012, hoja completa confirmada 2026-08-19
# (design-notes sec.16.4). Los dos extremos de la recta de regulacion:
V_VACIO = 13.42                 # V por semidevanado, sin carga
V_PLENA = 12.00                 # V por semidevanado, a I_PLENA
I_PLENA = 5.00                  # A
R_SEC = (V_VACIO - V_PLENA) / I_PLENA          # 0.284 ohm efectivos

# --- el resto del front-end ----------------------------------------------
C_BULK = 9400e-6                # 2 x 4700 uF por riel (design-notes sec.16.5)
I_CARGA = 0.650                 # A, techo del censo por riel (spec v2)
V_NOM, V_RED_BAJA = 230.0, 207.0               # red europea y su -10 %

# --- el criterio ----------------------------------------------------------
# 12,000 (V_OUT) + 0,450 (dropout MAX del LT3045 en el bin de 500 mA)
# + 0,007 (ballast) + 1,000 (dropout MAX del pre-regulador). Lo fija el riel
# positivo; los dos comparten front-end. (v2 sec.4.1)
UMBRAL_ABORTO = 13.46
# Lo que la tabla de design-notes sec.16.5 dice que sale, y que este script
# NO reproduce: da 14.62 V, medio voltio por encima. Se biseco y ninguna
# variante razonable del devanado lo explica --
#
#     R pura de 0.284 (la efectiva de la hoja)      14.62 V
#     R pura de 0.1336 (solo la parte ohmica)       15.02 V
#     R 0.1336 + L 0.479 mH (dispersion aparte)     14.73 V
#
# -- y en cambio SI encaja con el modelo de la v1, que calculaba la
# resistencia del devanado como `reg * 12 / 2 A` porque su transformador era
# de 2 A: eso da 0.6 a 0.9 ohm, y barriendo `reg` entre 10 y 15 % salen 13.96
# y 14.27, con 14.12 justo en medio.
#
# O sea: los 14.12 parecen venir de la resistencia del trafo PEQUENO, no del
# 0.284 que la propia tabla escribe en su columna. Issue #141.
#
# NO se asevera contra este numero, y no es por comodidad: la tabla no es un
# criterio de diseno sino un resultado anterior cuya procedencia no se puede
# reconstruir. El criterio de la placa es el umbral de aborto, y este modelo
# lo supera con MAS margen que la tabla -- la direccion tranquilizadora. Si
# diera MENOS, seria una parada, y esa comprobacion sigue abajo.
VALLE_TABULADO = 14.12


def netlist(v_red: float, c_bulk: float, i_carga: float,
            r_sec: float = R_SEC) -> str:
    """Secundario partido + puente + bulk + cargas de corriente constante.

    Las cargas son fuentes de CORRIENTE y no resistencias, igual que en la v1
    y por el mismo motivo: un regulador lineal en regulacion consume corriente
    casi constante pase lo que pase con el rizado de su entrada. Con una
    resistencia el rizado saldria optimista.
    """
    v_pico = V_VACIO * 2 ** 0.5 * (v_red / V_NOM)
    return f"""sam17 v3 - valle de VRAW
V1 a 0 SIN(0 {v_pico:.4f} 50)
V2 0 b SIN(0 {v_pico:.4f} 50)
Rw1 a a1 {r_sec:.4f}
Rw2 b b1 {r_sec:.4f}
D1 a1 vp DMOD
D2 b1 vp DMOD
D3 vn a1 DMOD
D4 vn b1 DMOD
Vmc vp cp 0
C1 cp 0 {c_bulk}
C2 0 vn {c_bulk}
I1 vp 0 {i_carga}
I2 0 vn {i_carga}
.model DMOD D(IS=1e-8 N=1.9 RS=0.025 BV=1000)
.ic v(vp)=15 v(vn)=-15
.tran 20u 400m 340m 20u
.end
"""


def mide(ng: Ng, **kw) -> dict:
    ng.corre(netlist(**kw))
    vp, vn = ng.vec("v(vp)"), ng.vec("v(vn)")
    ic = ng.vec("i(vmc)")
    return {"valle_pos": min(vp), "pico_pos": max(vp),
            "rizado_pos": max(vp) - min(vp),
            "valle_neg": max(vn), "pico_neg": min(vn),
            "rizado_neg": max(vn) - min(vn),
            "ic_rms": (sum(i * i for i in ic) / len(ic)) ** 0.5}


def autocomprobacion(ng: Ng) -> None:
    """Valida el MODELO contra dos casos de respuesta conocida.

    Un integrador propio da numeros con toda la confianza del mundo aunque el
    circuito este mal escrito. Estos dos casos tienen respuesta sabida de
    antemano, asi que si el modelo miente, mienten ellos primero.
    """
    # 1) Sin carga el valle tiene que subir hasta el pico rectificado menos lo
    #    que caigan DOS diodos, y no hay que rizado que lo baje: nadie descarga
    #    el bulk.
    #
    #    La cota se deja entre 0 y 1,4 V de caida a proposito, y la primera
    #    version de esta comprobacion no lo hacia: pedia 1,4 V clavados y
    #    fallo con 18,19 V medidos contra 17,58 esperados. El modelo estaba
    #    bien y la expectativa mal -- 0,7 V por diodo es la caida a PLENA
    #    corriente, y aqui la carga es de 1 uA: con IS=1e-8 y N=1.9 la union
    #    cae unos 0,23 V, no 0,7. La autocomprobacion sirvio para lo que
    #    existe, solo que el primero al que cazo fue a quien la escribio.
    sin_carga = mide(ng, v_red=V_NOM, c_bulk=C_BULK, i_carga=1e-6)
    pico = V_VACIO * 2 ** 0.5
    assert pico - 1.4 <= sin_carga["valle_pos"] <= pico, (
        f"sin carga el valle deberia caer entre {pico-1.4:.2f} y {pico:.2f} V "
        f"(el pico menos dos diodos) y sale {sin_carga['valle_pos']:.2f}")
    assert sin_carga["rizado_pos"] < 0.05, (
        f"sin carga no puede haber {sin_carga['rizado_pos']*1000:.0f} mV de rizado")

    # 2) Con el DOBLE de bulk el rizado tiene que bajar, y aproximadamente a la
    #    mitad: en un filtro capacitivo Vpp ~ I / (2*f*C).
    normal = mide(ng, v_red=V_RED_BAJA, c_bulk=C_BULK, i_carga=I_CARGA)
    doble = mide(ng, v_red=V_RED_BAJA, c_bulk=2 * C_BULK, i_carga=I_CARGA)
    razon = normal["rizado_pos"] / doble["rizado_pos"]
    assert 1.7 < razon < 2.3, (
        f"doblar el bulk deberia bajar el rizado ~2x y lo baja {razon:.2f}x")
    print(f"autocomprobacion OK (sin carga {sin_carga['valle_pos']:.2f} V, "
          f"entre {pico-1.4:.2f} y {pico:.2f}; doblar el bulk divide el "
          f"rizado por {razon:.2f})")


def main() -> int:
    ng = Ng()
    autocomprobacion(ng)

    print(f"\ntransformador Talema 0120P1-2-012 (hoja del fabricante):")
    print(f"  {V_VACIO} V en vacio, {V_PLENA} V a {I_PLENA} A "
          f"-> R_SEC = {R_SEC:.4f} ohm por semidevanado")
    print(f"bulk {C_BULK*1e6:.0f} uF/riel, carga {I_CARGA*1000:.0f} mA/riel\n")

    print(f"{'red':>6}  {'valle +':>9}  {'valle -':>9}  {'rizado':>8}  "
          f"{'I_C rms':>8}  margen sobre {UMBRAL_ABORTO}")
    print("-" * 68)
    peor = None
    for v_red in (V_RED_BAJA, V_NOM, V_NOM * 1.1):
        r = mide(ng, v_red=v_red, c_bulk=C_BULK, i_carga=I_CARGA)
        margen = r["valle_pos"] - UMBRAL_ABORTO
        print(f"{v_red:6.0f}  {r['valle_pos']:8.2f} V  {r['valle_neg']:8.2f} V  "
              f"{r['rizado_pos']*1000:6.0f} mV  {r['ic_rms']:6.2f} A  "
              f"{margen:+6.2f} V")
        if peor is None or r["valle_pos"] < peor["valle_pos"]:
            peor = r
            peor_red = v_red

    valle = peor["valle_pos"]
    print(f"\npeor caso: red a {peor_red:.0f} V, valle {valle:.2f} V")

    # --- la asercion, y el desacuerdo que se registra -----------------------
    assert valle >= UMBRAL_ABORTO, (
        f"el valle simulado ({valle:.2f} V) esta por debajo del umbral de "
        f"aborto ({UMBRAL_ABORTO} V): ningun setpoint funcionaria")

    delta = valle - VALLE_TABULADO
    print(f"  contra la tabla de design-notes sec.16.5 ({VALLE_TABULADO} V): "
          f"{delta:+.2f} V  <- NO la reproduce, ver #141")
    if delta < 0:
        # Este si es motivo de parada: significaria que el numero con el que
        # se ha razonado el margen hasta hoy era OPTIMISTA.
        raise AssertionError(
            f"este modelo da {valle:.2f} V, por DEBAJO de los "
            f"{VALLE_TABULADO} V tabulados. El colchon que anuncia el README "
            f"seria menor de lo que dice: parar y reconciliar antes de pedir")

    print(f"  contra el umbral de aborto ({UMBRAL_ABORTO} V): "
          f"{valle - UMBRAL_ABORTO:+.2f} V de colchon "
          f"({(valle - UMBRAL_ABORTO) / UMBRAL_ABORTO * 100:.1f} %)")
    print(f"\nOK: presupuesto cerrado. El valle queda {valle - UMBRAL_ABORTO:.2f} V por encima"
          f"\n    del umbral que hace la placa irrecuperable, y {delta:+.2f} V respecto"
          f"\n    de la tabla de sec.16.5 (#141).")
    print("    NO cubre: arranque, cascada aguas abajo, ruido ni deriva "
          "termica (ver docstring).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
