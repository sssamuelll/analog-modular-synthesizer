"""El detector de ventana de D-F4 en la fuente v5 (T13, T22, T23, M4, #339).

    python secuencia_budget.py

Releva a `v4/secuencia_budget.py` bajo las decisiones firmadas en D-V4 (M4,
2026-09-08) y el cierre de `#339`:
  - `D-F4` NO se va con los Mean Well: los pines `SHDN` de `U1` (`LT1963A`,
    `lt1963a-rev-g-2021-02.pdf` p. 5) y `U2` (`LT3015`, `lt3015-rev-b.pdf` p. 5)
    y los interruptores de carga del par de rack (`+-12 V`) siguen dentro de la
    caja.
  - Lo que cambia es el nodo vigilado: el detector analogico de un hilo (`M4`)
    mide los dos rieles crudos de **+-15,5 V** (`2 x TRACO THN 20-2413WI`)
    **despues del filtro LC** y el par de rack (`TRACO THN 30-2422WI`).
  - Las piezas del detector ya tienen hoja versionada en `docs/reference/datasheets/`:
      * Comparador doble colector abierto: **TI LM393B** (`ti-lm393b.pdf` p. 6:
        offset `V_IO <= 2,0 mV` a 25 C y `<= 4,0 mV` en -40..125 C; tiempo de
        respuesta `1,3 us` tip.).
      * Referencia de precision: **TI TL431BI** (`tl431.pdf` p. 5: `2,495 V +-
        0,5 %` a 25 C, deriva incluida `<= 1,1 %` en rango).
      * Divisores de pelicula fina al **0,1 %** (`+-0,2 %` peor caso en relacion).

Con los crudos a **15,5 V** (D-V3) la ventana entre lo que `U1` necesita para
regular (`14,040 V`) y lo que llega en el corner bajo (`14,885 V` tras el eFuse
`TPS26630` y el LC) se abre de `+325 mV` (en v4 a 15,0 V) a **+846 mV**, dejando
una ventana util de **+650 mV** tras descontar histeresis y error de piezas.
"""
from __future__ import annotations

import os
import sys
from typing import Callable

DIR = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(DIR, "..", "v4")
if DIR not in sys.path:
    sys.path.insert(0, DIR)
if V4 not in sys.path:
    sys.path.append(V4)

import margen_budget as mb5  # noqa: E402

# --- Pines de habilitacion de la cascada (ambos activo-ALTO: D-F8 + D-F9) ---
# LT1963A (lt1963a-rev-g-2021-02.pdf p. 5): V_IH >= 2,00 V, V_IL <= 0,25 V
# LT3015  (lt3015-rev-b.pdf p. 5):          V_IH >= 1,35 V, V_IL <= 0,50 V
ON_OFF_V = {
    "U1": {"on_min": 2.00, "off_max": 0.25},
    "U2": {"on_min": 1.35, "off_max": 0.50},
}

# --- Tiempos del detector M4 y del THN 20-2413WI (traco_thn20wi.pdf p. 2) ---
# Start-up time del THN 20-2413WI: 30 ms tip. (mucho mas rapido que los 1000 ms
# del IRM-20-15 de la v4, pero sin detector un riel podria seguir saliendo
# antes que el otro o caer solo ante un fallo de rama).
T_STARTUP_THN_MS = 30.0
T_DETECCION_MS = 1.0
T_APAGADO_REG_MS = 0.10
T_RIEL_SOLO_MAX_ADMISIBLE_MS = 5.0

# --- Piezas del detector M4 con hoja versionada -----------------------------
# TI LM393B (ti-lm393b.pdf p. 6): V_IO max = 4,0 mV sobre temperatura (-40..125 C)
# TI TL431BI (tl431.pdf p. 5): tolerancia 0,5 % a 25 C (2495 +- 12 mV)
TOL_DIVISOR_FRAC = 0.002       # dos resistencias de 0,1 % en un divisor
TOL_REF_TL431BI_FRAC = 0.005   # TL431BI grado B (0,5 %, tl431.pdf p. 5)
OFFSET_LM393B_MAX_V = 0.004    # LM393B V_IO max en -40..125 C (ti-lm393b.pdf p. 6)
GANANCIA_DIVISOR = 14.46 / 2.495

# --- Rizado e histeresis en el nodo despues del LC --------------------------
RIZADO_TRAS_LC_VPP = mb5.RIZADO_TRAS_LC_VPP
MARGEN_RUIDO_HISTERESIS_V = 0.030
HISTERESIS_V = RIZADO_TRAS_LC_VPP + MARGEN_RUIDO_HISTERESIS_V

ESTIMADOS = (
    f"T_DETECCION_MS={T_DETECCION_MS}: constante de tiempo RC de filtrado del comparador LM393B",
    f"T_APAGADO_REG_MS={T_APAGADO_REG_MS}: tiempo de apagado por SHDN de LT1963A/LT3015",
)


def suelo_ventana_v() -> float:
    """Por abajo: lo que U1 necesita en su entrada para regular (el mas exigente)."""
    return max(mb5.v_necesaria_minima_v("U1"), mb5.v_necesaria_minima_v("U2"))


def techo_ventana_v() -> float:
    """Por arriba: lo minimo que entrega un THN 20-2413WI sano tras eFuse + LC."""
    return min(mb5.v_entrada_minima_rama_v("U1"), mb5.v_entrada_minima_rama_v("U2"))


def ancho_ventana_bruta_v() -> float:
    return techo_ventana_v() - suelo_ventana_v()


def error_umbral_v(*, tol_div: float = TOL_DIVISOR_FRAC,
                   tol_ref: float = TOL_REF_TL431BI_FRAC,
                   v_offset: float = OFFSET_LM393B_MAX_V) -> float:
    """Error maximo del umbral referido al riel de ~14,5 V (LM393B + TL431BI + 0,1%)."""
    v_centro = 0.5 * (suelo_ventana_v() + techo_ventana_v())
    return v_centro * (tol_div + tol_ref) + v_offset * GANANCIA_DIVISOR


def ventana_util_v(*, histeresis_v: float = HISTERESIS_V,
                   tol_div: float = TOL_DIVISOR_FRAC,
                   tol_ref: float = TOL_REF_TL431BI_FRAC,
                   v_offset: float = OFFSET_LM393B_MAX_V) -> float:
    """Ancho libre donde cabe el umbral nominal tras pagar histeresis y error +-."""
    err = error_umbral_v(tol_div=tol_div, tol_ref=tol_ref, v_offset=v_offset)
    return ancho_ventana_bruta_v() - histeresis_v - 2.0 * err


def estados_d_f4() -> list[dict]:
    """Los 6 estados del par (+crudo, -crudo) bajo el detector OR-cableado M4."""
    t_trans = T_DETECCION_MS + T_APAGADO_REG_MS
    return [
        {"estado": "THN+=vivo, THN-=vivo", "habilita": True,
         "riel_solo": False, "ms": 0.0},
        {"estado": "THN+=vivo, THN-=muerto (transitorio)", "habilita": True,
         "riel_solo": True, "ms": t_trans},
        {"estado": "THN+=vivo, THN-=muerto (estable)", "habilita": False,
         "riel_solo": False, "ms": 0.0},
        {"estado": "THN+=muerto, THN-=vivo (transitorio)", "habilita": True,
         "riel_solo": True, "ms": t_trans},
        {"estado": "THN+=muerto, THN-=vivo (estable)", "habilita": False,
         "riel_solo": False, "ms": 0.0},
        {"estado": "THN+=muerto, THN-=muerto", "habilita": False,
         "riel_solo": False, "ms": 0.0},
    ]


P_BASE: dict[str, float] = {
    "histeresis_v": HISTERESIS_V,
    "t_riel_solo_max_ms": T_RIEL_SOLO_MAX_ADMISIBLE_MS,
}


def _guarda_histeresis(p: dict[str, float]) -> None:
    h = p["histeresis_v"]
    assert h >= RIZADO_TRAS_LC_VPP + MARGEN_RUIDO_HISTERESIS_V - 1e-9, (
        f"histeresis {h*1000:.1f} mV insuficiente: castanetea con el rizado")
    vu = ventana_util_v(histeresis_v=h)
    assert vu > 0.0, (
        f"histeresis {h*1000:.1f} mV excesiva: apagaria una cascada que regula "
        f"(ventana util {vu*1000:+.1f} mV)")


def _guarda_tiempo_riel_solo(p: dict[str, float]) -> None:
    peor_ms = max(e["ms"] for e in estados_d_f4() if e["riel_solo"])
    assert peor_ms <= p["t_riel_solo_max_ms"], (
        f"la deteccion de D-F4 llega tarde: {peor_ms:.2f} ms > "
        f"{p['t_riel_solo_max_ms']:.2f} ms")


def borde_rojo(guarda: Callable[[dict[str, float]], None],
               base: dict[str, float], clave: str,
               lo: float, hi: float, subcadena: str) -> float:
    def pasa(v: float) -> bool:
        q = dict(base)
        q[clave] = v
        try:
            guarda(q)
            return True
        except AssertionError as exc:
            assert subcadena in str(exc), (
                f"En {clave}={v}: esperaba {subcadena!r} y salio {str(exc)!r}")
            return False

    p_lo, p_hi = pasa(lo), pasa(hi)
    assert p_lo != p_hi, f"{clave} no cruza el rojo entre {lo} y {hi}"
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if pasa(m) == p_lo:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def demo() -> int:
    print("secuencia_budget v5: detector de ventana D-F4 (M4: LM393B + TL431BI + 0,1%)\n")
    print("  1. Habilitacion conjunta por un solo hilo (colector abierto LM393B + pull-down):")
    for reg, d in ON_OFF_V.items():
        print(f"    {reg}: ON >= {d['on_min']:.2f} V, OFF <= {d['off_max']:.2f} V "
              "(hilo roto -> pull-down apaga a los dos)")

    print("\n  2. Ventana del umbral sobre los crudos de +-15,5 V despues del LC:")
    print(f"    suelo (lo que U1 necesita para regular):     {suelo_ventana_v():.3f} V")
    print(f"    techo (lo minimo que llega sano tras eFuse): {techo_ventana_v():.3f} V")
    print(f"    ancho bruto de ventana:                      +{ancho_ventana_bruta_v()*1000:.0f} mV "
          "(eran +325 mV en la v4 a 15,0 V)")
    print(f"    error del umbral (LM393B 4mV + TL431BI 0,5% + div 0,2%): +-{error_umbral_v()*1000:.0f} mV")
    print(f"    histeresis (rizado LC 1,22 mV + 30 mV):      {HISTERESIS_V*1000:.1f} mV")
    print(f"    VENTANA UTIL:                                +{ventana_util_v()*1000:.0f} mV\n")

    print("  3. Maquina de 6 estados de D-F4 (cascada y par +-12 V de rack):")
    for e in estados_d_f4():
        ms_txt = f"{e['ms']:.1f} ms" if e["riel_solo"] else "estable"
        print(f"    {e['estado']:<40} habilita={str(e['habilita']):<5} "
              f"riel_solo={str(e['riel_solo']):<5} ({ms_txt})")

    _guarda_histeresis(dict(P_BASE))
    _guarda_tiempo_riel_solo(dict(P_BASE))
    h_min = borde_rojo(_guarda_histeresis, dict(P_BASE), "histeresis_v",
                       0.0, HISTERESIS_V, "castanetea")
    h_max = borde_rojo(_guarda_histeresis, dict(P_BASE), "histeresis_v",
                       HISTERESIS_V, 1.5, "apagaria una cascada que regula")
    t_min = borde_rojo(_guarda_tiempo_riel_solo, dict(P_BASE), "t_riel_solo_max_ms",
                       0.1, T_RIEL_SOLO_MAX_ADMISIBLE_MS, "llega tarde")
    print(f"\n  canario histeresis baja: < {h_min*1000:.1f} mV castanetea")
    print(f"  canario histeresis alta: > {h_max*1000:.0f} mV apagaria una cascada que regula")
    print(f"  canario tiempo riel solo: < {t_min:.2f} ms la deteccion llega tarde")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}")
    for e in ESTIMADOS:
        print(f"    - {e}")

    assert ventana_util_v() > 0.500
    print("\nOK: secuencia_budget.py v5")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
