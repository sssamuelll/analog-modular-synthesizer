"""Margen de caida de la cascada ultra en la fuente v5 (T11, D-V3, #343, M3).

    python margen_budget.py

En la v5 los dos rieles crudos de la cascada ya no salen de dos Mean Well
IRM-20-15 a 15,0 V de catalogo: salen de dos convertidores aislados **TRACO
THN 20-2413WI** (`traco_thn20wi.pdf` p. 1-3) recortados por su pin `Trim` a
**15,5 V** nominales (D-V3), con el eFuse **TI TPS26631** (`tps2663.pdf` p. 7)
en serie en la rama positiva antes del filtro LC (M3, #334).

Este guion incorpora:
1. `#343`: la corriente de masa maxima del `LT1963A` (`U1`, D-F8) a plena carga
   sobre temperatura (`Iq_max = 120 mA` a 1,5 A, `lt1963a-rev-g-2021-02.pdf`
   p. 5), que sube la corriente por el filtro LC positivo a `0,770 A`
   (`0,650 + 0,120 A`), y la del `LT3015` (`U2`, D-F9, `Iq_max = 70 mA`,
   `lt3015-rev-b.pdf` p. 4), que deja la rama negativa en `0,720 A`.
2. La caida adicional del eFuse `TPS26631` en la rama positiva (`RON_max =
   53 mohm` entre -40 y +125 C, `tps2663.pdf` p. 7: `40,8 mV` a `0,770 A`).
3. Las cotas de regulacion del `THN 20-2413WI` (`traco_thn20wi.pdf` p. 2):
   exactitud base +-1 %, regulacion de linea +-0,2 % max, regulacion de carga
   +-0,5 % max, coeficiente termico +-0,02 %/K max y rizado 100 mVp-p max (se
   conserva la envolvente combinada de +-2,5 % de `ladrillo_budget.py` tras el
   recorte por Trim, que es mas exigente que la suma de hoja).
"""
from __future__ import annotations

import importlib.util
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(DIR, "..", "v4")
if V4 not in sys.path:
    sys.path.append(V4)
TOOLS = os.path.join(DIR, "..", "..", "tools")
if TOOLS not in sys.path:
    sys.path.append(TOOLS)
from canario import borde_rojo  # noqa: E402  (la biseccion de los canarios vive en UN sitio)

_spec_mb4 = importlib.util.spec_from_file_location(
    "_v4_margen_budget", os.path.join(V4, "margen_budget.py"))
assert _spec_mb4 and _spec_mb4.loader
mb4 = importlib.util.module_from_spec(_spec_mb4)
_spec_mb4.loader.exec_module(mb4)

# --- Parametros de los crudos v5 (2 x TRACO THN 20-2413WI + Trim) ----------
V_NOM_V5 = 15.50
TOL_CRUDO_V5 = 0.025                  # +-2,5 % conservador tras Trim
TEMPCO_PPM_K_V5 = 200.0               # +-0,02 %/K max (traco_thn20wi.pdf p. 2)
DELTA_T_K_V5 = 40.0                   # de 25 C a 65 C en el interior del case
RIZADO_CRUDO_VPP_MAX = 0.100          # 100 mVp-p max (traco_thn20wi.pdf p. 2)
RIZADO_TRAS_LC_VPP = mb4.rizado_en_u1_vpp()  # 1,22 mVp-p tras el LC

# --- Corrientes por rama (#343) y resistencias serie (M3 + LC + ferrita) ----
I_CARGA_A = mb4.RIEL_MA / 1000.0      # 0,650 A (D-F1)
IQ_U1_MAX_A = mb4.IQ_U1_MAX_A         # 0,120 A (lt1963a-rev-g-2021-02.pdf p. 5)
IQ_U2_MAX_A = mb4.IQ_U2_MAX_A         # 0,070 A (lt3015-rev-b.pdf p. 5)

R_DCR_BOBINA_OHM = mb4.DCR_OHM             # 0,030 ohm (22 uH)
R_DCR_FERRITA_OHM = mb4.R_FERRITA_DC_OHM   # 0,050 ohm (perla 600 ohm @ 100 MHz)
R_ON_EFUSE_U1_OHM = 0.053                  # TI TPS26631 RON max (tps2663.pdf p. 7)

ESTIMADOS = (
    "TOL_CRUDO_V5=2,5 %: envolvente conservadora para el THN 20-2413WI recortado "
    "a 15,5 V con resistencias de 0,1 % (la hoja da +-1 % base + +-0,2 % linea + "
    "+-0,5 % carga = +-1,7 % sin Trim, traco_thn20wi.pdf p. 2)",
    "R_DCR_BOBINA_OHM=30 mohm y R_DCR_FERRITA_OHM=50 mohm: cotas de pasivos del LC",
)


def corriente_rama_a(reg: str) -> float:
    """Corriente total que atraviesa el filtro y proteccion de entrada de `reg`."""
    if reg == "U1":
        return I_CARGA_A + IQ_U1_MAX_A
    if reg == "U2":
        return I_CARGA_A + IQ_U2_MAX_A
    raise KeyError(reg)


def resistencia_serie_rama_ohm(reg: str, *, r_efuse_u1: float = R_ON_EFUSE_U1_OHM) -> float:
    """Resistencia DC total entre la salida del THN 20-2413WI y el pin IN de `reg`.

    En `U1` incluye el eFuse `TPS26631` de M3 (#334) antes del LC; en `U2` no
    hay eFuse en serie porque el `LT3015` aguanta +-33 V de entrada (`lt3015-rev-b.pdf`
    p. 2) frente a los -24,6 V maximos de OVP del THN.
    """
    r_base = R_DCR_BOBINA_OHM + R_DCR_FERRITA_OHM
    if reg == "U1":
        return r_base + r_efuse_u1
    if reg == "U2":
        return r_base
    raise KeyError(reg)


def v_entrada_minima_rama_v(reg: str, *, v_nom: float = V_NOM_V5,
                            tol: float = TOL_CRUDO_V5,
                            r_efuse_u1: float = R_ON_EFUSE_U1_OHM) -> float:
    """Tension minima efectiva en el pin IN de `reg` en el corner frio/bajo."""
    deriva_frac = (TEMPCO_PPM_K_V5 * 1e-6) * DELTA_T_K_V5
    v_thn_min = v_nom * (1.0 - tol - deriva_frac)
    caida_dc = corriente_rama_a(reg) * resistencia_serie_rama_ohm(
        reg, r_efuse_u1=r_efuse_u1)
    valle_rizado = 0.5 * RIZADO_TRAS_LC_VPP
    return v_thn_min - caida_dc - valle_rizado


def v_entrada_maxima_sana_v(*, v_nom: float = V_NOM_V5,
                            tol: float = TOL_CRUDO_V5) -> float:
    """Tension maxima sana en vacio en la salida del THN 20-2413WI."""
    deriva_frac = (TEMPCO_PPM_K_V5 * 1e-6) * DELTA_T_K_V5
    return v_nom * (1.0 + tol + deriva_frac) + 0.5 * RIZADO_TRAS_LC_VPP


def v_necesaria_minima_v(reg: str) -> float:
    """Suelo exigido por la cascada en el pin IN de `reg` (importado de v4)."""
    return mb4.v_necesaria_v(reg)


def margen_v5_v(reg: str, *, v_nom: float = V_NOM_V5,
                tol: float = TOL_CRUDO_V5,
                r_efuse_u1: float = R_ON_EFUSE_U1_OHM) -> float:
    """Holgura de regulacion en voltios en el pin IN de `reg`."""
    return (
        v_entrada_minima_rama_v(reg, v_nom=v_nom, tol=tol, r_efuse_u1=r_efuse_u1)
        - v_necesaria_minima_v(reg)
    )


P_BASE: dict[str, float] = {
    "v_nom_v": V_NOM_V5,
    "tol_crudo": TOL_CRUDO_V5,
    "r_efuse_u1_ohm": R_ON_EFUSE_U1_OHM,
}


def _guarda_margen_u1(p: dict[str, float]) -> None:
    m = margen_v5_v("U1", v_nom=p["v_nom_v"], tol=p["tol_crudo"],
                    r_efuse_u1=p["r_efuse_u1_ohm"])
    assert m >= 0.0, f"U1 (LT1963A) pierde regulacion: margen {m*1000:+.1f} mV"


def _guarda_margen_u2(p: dict[str, float]) -> None:
    m = margen_v5_v("U2", v_nom=p["v_nom_v"], tol=p["tol_crudo"],
                    r_efuse_u1=p["r_efuse_u1_ohm"])
    assert m >= 0.0, f"U2 (LT3015) pierde regulacion: margen {m*1000:+.1f} mV"


def demo() -> int:
    print("margen_budget v5: los dos THN 20-2413WI recortados a 15,5 V + eFuse M3\n")
    for reg, pieza in (("U1", "LT1963A (D-F8, Iq_max=120 mA #343, eFuse TPS26631)"),
                       ("U2", "LT3015  (D-F9, Iq_max=70 mA)")):
        i_tot = corriente_rama_a(reg)
        r_tot = resistencia_serie_rama_ohm(reg)
        v_in = v_entrada_minima_rama_v(reg)
        v_nec = v_necesaria_minima_v(reg)
        m_mv = margen_v5_v(reg) * 1000.0
        print(f"  {reg} -- {pieza}:")
        print(f"    corriente por filtro: {i_tot*1000:.0f} mA "
              f"(carga {I_CARGA_A*1000:.0f} + Iq {(i_tot-I_CARGA_A)*1000:.0f})")
        print(f"    resistencia serie:    {r_tot*1000:.0f} mohm "
              f"-> caida DC {i_tot*r_tot*1000:.1f} mV")
        print(f"    llega al pin IN:      {v_in:.3f} V")
        print(f"    necesita (suelo):     {v_nec:.3f} V")
        print(f"    MARGEN:               {m_mv:+.0f} mV\n")

    print(f"  maximo sano en vacio del crudo: {v_entrada_maxima_sana_v():.3f} V "
          f"(contra 20,0 V absmax de U1 y 16,92 V max de disparo del TPS26631)\n")

    _guarda_margen_u1(dict(P_BASE))
    _guarda_margen_u2(dict(P_BASE))
    v_min_u1 = borde_rojo(_guarda_margen_u1, dict(P_BASE), "v_nom_v",
                          13.5, 15.5, "pierde regulacion")
    v_min_u2 = borde_rojo(_guarda_margen_u2, dict(P_BASE), "v_nom_v",
                          13.5, 15.5, "pierde regulacion")
    r_max_efuse = borde_rojo(_guarda_margen_u1, dict(P_BASE), "r_efuse_u1_ohm",
                             0.0, 2.0, "pierde regulacion")
    print(f"  canario U1: por debajo de {v_min_u1:.2f} V nominales de crudo, U1 pierde regulacion")
    print(f"  canario U2: por debajo de {v_min_u2:.2f} V nominales de crudo, U2 pierde regulacion")
    print(f"  canario eFuse M3: por encima de {r_max_efuse*1000:.0f} mohm de RON, U1 pierde regulacion")

    print(f"\n  ESTIMADO: {len(ESTIMADOS)}")
    for e in ESTIMADOS:
        print(f"    - {e}")

    assert margen_v5_v("U1") > 0.700
    assert margen_v5_v("U2") > 1.000
    assert v_entrada_maxima_sana_v() < 16.10
    print("\nOK: margen_budget.py v5")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
