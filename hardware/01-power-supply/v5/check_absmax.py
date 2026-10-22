"""Supervivencia por riel, modelo RK4 de #334 y crowbars D-F6 en la fuente v5.

    python check_absmax.py

Cierra en codigo ejecutable para la v5 los trabajos **T14, T18, T19, T20, T21**
del censo D-V4 (`2026-09-08-censo-dv4-resolucion.md`) y los issues **#334** y
**#340**, con todas las hojas versionadas en `docs/reference/datasheets/`:

  1. **#334 (`H-V2-CORTO-DCDC`, T18): simulacion RK4 del escalon sobre el LC de `U1`.**
     - El convertidor crudo positivo (`TRACO THN 20-2413WI`, `traco_thn20wi.pdf`
       p. 2) tiene su OVP interno entre el 112 % y el 164 % de 15 V (`16,8 ..
       24,6 V`), y un puente entrada-salida aplicaria hasta `36 V` (o `24 V` del
       ladrillo) al filtro LC (`22 uH` + `47 uF` + `0,68 ohm` + `220 uF`).
     - `U1` es el `LT1963A` (D-F8, `lt1963a-rev-g-2021-02.pdf` p. 2), cuyo
       maximo absoluto de entrada es **+-20,0 V**.
     - Con el eFuse **TI TPS26631** (`tps2663.pdf` p. 6-8: `V(OVPR) = 1,176 ..
       1,224 V`, corte en `8,5..14 us`, `RON <= 53 mohm`) **antes del filtro LC,
       sensando del lado del modulo** (disparo nominal `16,55 V`, borde bajo
       `16,19 V` > maximo sano `16,01 V`, borde alto `16,92 V`) y el TVS
       **Bourns SMBJ16A** (`bourns_smbj.pdf` p. 2: `V_WM = 16,0 V`, `V_BR =
       17,8..19,7 V`) en `U1 IN`:
         * Con tope (sensado antes del LC, `t_corte = 14 us`, falla de `36 V`):
           el pico en `U1 IN` es **18,08 V < 20,0 V** (margen `+1,92 V`).
         * Sin tope: el pico en el LC sube a **27,14 V > 20,0 V** (ROJO).
         * Mutante con sensado DESPUES del LC: cuando el nodo de `U1` cruza
           `16,92 V`, la bobina de `22 uH` ya lleva corriente acumulada y el
           pico tras cortar sube a **22,21 V > 20,0 V** (ROJO: mutante cazado).

  2. **`U2` (`LT3015`, D-F9, T18):**
     - `IN Pin Voltage` maximo absoluto de **+-33,0 V** (`lt3015-rev-b.pdf` p. 2),
       por encima del OVP maximo del `THN 20-2413WI` (`-24,6 V`, margen `+8,40 V`),
       mas diodo Schottky en inversa `OUT-IN >= -0,3 V` (p. 2, Nota 10).

  3. **D-F6 en los tres rieles de rack (T20, #340, M3):**
     - SCR **NXP BT151-500R** (`nxp-bt151-500r.pdf` p. 2: `I_H <= 40 mA`,
       `I_GT <= 15 mA`, `I^2t = 72 A^2s`, `t_gt <= 2 us`) + referencia
       **TI TL431BI** (`tl431.pdf` p. 5: `+-0,5 %`, dispersion de disparo
       `+-0,30 V`) + fusible rapido **Bourns SF-1206F** (`bourns_sf1206f.pdf`).
     - En `+-12 V` (`THN 30-2422WI`, `traco_thn30wi.pdf` p. 2: sobrecarga tipica
       `150 %` de `1,25 A` = `1,875 A`) y `+5 V` (`RPMB5.0-2.0` / `K7805T-1000R3`),
       la corriente de pliegue supera en mas de 35 veces los `40 mA` de
       mantenimiento del `BT151-500R`.

  4. **Supervivencia del `+5 V` digital aislado (T19, `H-CENSO-DIGITAL`):**
     - El `Mornsun URB2405YMD-20WR3` (`mornsun_urb_ymd20wr3.pdf` p. 2) declara
       OVP entre `110 %` y `160 %` (`5,50..8,00 V`). Como `8,00 V` superaria los
       `6,30 V` de los condensadores de entrada de 5 V del modulo 2, M3 incluye
       un tope local con `TL431BI` (`5,65 V +- 0,30 V`, pico `<= 5,95 V < 6,30 V`).
"""
from __future__ import annotations

import csv
import os
import sys
from typing import Callable

DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(DIR, "absmax.csv")
if DIR not in sys.path:
    sys.path.insert(0, DIR)

from bom_valores import valor  # noqa: E402

# EL MODELO SIMULA LAS PIEZAS DE LA PLACA. L, C, Cd, Rd y el divisor del OVP
# se leen de bom.csv (#474: el modelo llevaba un LC y la BOM otro, y con el de
# la BOM U1 veia 21,0 V; ningun numero de este fichero lo habria delatado).

# --- Limites de U1 (LT1963A) y parametros del tope M3 (#334) ----------------
V_ABSMAX_U1_V = 20.0                   # lt1963a-rev-g-2021-02.pdf p. 2
V_ABSMAX_U2_V = 33.0                   # lt3015-rev-b.pdf p. 2
V_SANO_MAX_U1_V = 16.012               # de v5/margen_budget.py
V_OVPR_NOM_V = 1.200                   # tps2663.pdf p. 6: V(OVPR) 1,176..1,224 V
V_DISPARO_NOM_U1_V = V_OVPR_NOM_V * (1.0 + valor("R35") / valor("R36"))
TOL_OVPR_TPS26631_FRAC = 0.020         # tps2663.pdf p. 6: 1,176..1,224 V (+-2,0 %)
TOL_DIVISOR_01PCT_FRAC = 0.002         # dos resistencias de 0,1 %
V_DISPARO_MIN_U1_V = V_DISPARO_NOM_U1_V * (1.0 - TOL_OVPR_TPS26631_FRAC - TOL_DIVISOR_01PCT_FRAC)
V_DISPARO_MAX_U1_V = V_DISPARO_NOM_U1_V * (1.0 + TOL_OVPR_TPS26631_FRAC + TOL_DIVISOR_01PCT_FRAC)
T_CORTE_OVP_MAX_S = 14.0e-6            # tps2663.pdf p. 8: 8,5 us typ, 14 us max

# Parametros del filtro LC amortiguado + TVS Bourns SMBJ16A (bourns_smbj.pdf p. 2)
L_LC_H = valor("L2")
# TPS2663x RON max (53m) + bobina (30m, la DCR MAS BAJA amortigua menos: cota
# pesimista para el pico) + fuente/traza (50m).
R_SERIE_LC_OHM = 0.053 + 0.030 + 0.050
C_LC_F = valor("C3")
C_DAMP_F = valor("C1")
ESR_CD_OHM = 0.10                      # ESTIMADO: electrolitico de 220 uF (rizado_budget.py v4)
R_DAMP_OHM = valor("R37") + ESR_CD_OHM
I_CARGA_U1_A = 0.770                   # 650 mA + 120 mA Iq (#343)
# bourns_smbj.pdf p. 2: V_BR 17,8..19,7 V a 1 mA. Para el PICO manda el
# MAXIMO: con el minimo (que es lo que usaba #474) el TVS recorta antes y el
# modelo sale optimista.
V_BR_SMBJ16A_V = 19.70
R_DIN_SMBJ16A_OHM = 0.35               # pendiente dinamica del SMBJ16A en conduccion

# --- Parametros de D-F6 (NXP BT151-500R + TI TL431BI) -----------------------
I_MANTENIMIENTO_BT151_A = 0.040        # nxp-bt151-500r.pdf p. 2: I_H max 40 mA
I2T_BT151_A2S = 72.0                   # nxp-bt151-500r.pdf p. 2: I^2t = 72 A^2s
TOL_DISPARO_TL431BI_V = 0.30           # TL431BI 0,5 % + divisor + V_GK

# El disparo se calcula de los divisores de la placa: con el TL431 -> PNP ->
# puerta el umbral es 2,495 V * (1 + R_alta/R_baja), sin V_GT (en #474 el anodo
# del TL431 iba a la puerta y el umbral se corria V_GT*(1+R1/R2), de 3 a 8 V).
V_REF_TL431_V = 2.495                  # tl431.pdf p. 5


def _disparo(r_alta: str, r_baja: str) -> float:
    return V_REF_TL431_V * (1.0 + valor(r_alta) / valor(r_baja))


RACK_RIELES = {
    "rack+12": {"sano_max_v": 12.533, "ovp_max_v": 16.56, "victima_max_v": 16.00,
                "disparo_v": _disparo("R45", "R47"), "i_pliegue_min_a": 1.875},
    "rack-12": {"sano_max_v": 12.533, "ovp_max_v": 16.56, "victima_max_v": 16.00,
                "disparo_v": _disparo("R46", "R48"), "i_pliegue_min_a": 1.875},
    "rack+5":  {"sano_max_v": 5.231,  "ovp_max_v": 6.75,  "victima_max_v": 6.30,
                "disparo_v": _disparo("R49", "R50"), "i_pliegue_min_a": 2.500},
    "digital+5": {"sano_max_v": 5.150, "ovp_max_v": 8.00, "victima_max_v": 6.30,
                  "disparo_v": _disparo("R51", "R52"), "i_pliegue_min_a": 4.400},
}


def escalon_lc(*, v_fallo_v: float = 36.0,
               v_disparo_v: float = V_DISPARO_MAX_U1_V,
               t_corte_s: float = T_CORTE_OVP_MAX_S,
               sensa_antes_del_lc: bool = True,
               con_efuse: bool = True,
               con_tvs: bool = True) -> dict[str, float]:
    """Integracion RK4 del escalon de fallo sobre el LC amortiguado de U1 (#334).

    Estado:
      i_L: corriente en la bobina de 22 uH (A)
      v_1: tension en el condensador principal de 47 uF = entrada de U1 (V)
      v_d: tension en el condensador de amortiguacion de 220 uF (V)
    """
    v0 = 15.50
    i_l = I_CARGA_U1_A
    v_1 = v0 - i_l * R_SERIE_LC_OHM
    v_d = v_1

    dt = 0.05e-6
    t_fin = 250.0e-6
    n_pasos = int(t_fin / dt)

    t_deteccion: float | None = 0.0 if (con_efuse and sensa_antes_del_lc and v_fallo_v >= v_disparo_v) else None
    v_pico = v_1
    e_tvs_j = 0.0

    def derivadas(il: float, v1: float, vd: float, cortado: bool) -> tuple[float, float, float, float]:
        if cortado:
            # El eFuse abrio: si i_L > 0, el diodo de rueda libre / cuerpo a masa
            # descarga la bobina contra v1; si i_L <= 0, la bobina queda en 0 A.
            if il <= 0.0:
                dil = 0.0
            else:
                dil = (-v1 - il * R_SERIE_LC_OHM) / L_LC_H
        else:
            dil = (v_fallo_v - v1 - il * R_SERIE_LC_OHM) / L_LC_H

        i_damp = (v1 - vd) / R_DAMP_OHM
        i_tvs = 0.0
        if con_tvs and v1 > V_BR_SMBJ16A_V:
            i_tvs = (v1 - V_BR_SMBJ16A_V) / R_DIN_SMBJ16A_OHM

        dv1 = (il - I_CARGA_U1_A - i_damp - i_tvs) / C_LC_F
        dvd = i_damp / C_DAMP_F
        p_tvs = v1 * i_tvs
        return dil, dv1, dvd, p_tvs

    for paso in range(n_pasos):
        t = paso * dt
        if con_efuse and not sensa_antes_del_lc and t_deteccion is None and v_1 >= v_disparo_v:
            t_deteccion = t
        cortado = (t_deteccion is not None) and (t >= t_deteccion + t_corte_s)
        if cortado and i_l < 0.0:
            i_l = 0.0

        k1_i, k1_v1, k1_vd, p_tvs = derivadas(i_l, v_1, v_d, cortado)
        k2_i, k2_v1, k2_vd, _ = derivadas(
            max(0.0, i_l + 0.5 * dt * k1_i) if cortado else i_l + 0.5 * dt * k1_i,
            v_1 + 0.5 * dt * k1_v1, v_d + 0.5 * dt * k1_vd, cortado)
        k3_i, k3_v1, k3_vd, _ = derivadas(
            max(0.0, i_l + 0.5 * dt * k2_i) if cortado else i_l + 0.5 * dt * k2_i,
            v_1 + 0.5 * dt * k2_v1, v_d + 0.5 * dt * k2_vd, cortado)
        k4_i, k4_v1, k4_vd, _ = derivadas(
            max(0.0, i_l + dt * k3_i) if cortado else i_l + dt * k3_i,
            v_1 + dt * k3_v1, v_d + dt * k3_vd, cortado)

        i_l += (dt / 6.0) * (k1_i + 2.0 * k2_i + 2.0 * k3_i + k4_i)
        if cortado and i_l < 0.0:
            i_l = 0.0
        v_1 += (dt / 6.0) * (k1_v1 + 2.0 * k2_v1 + 2.0 * k3_v1 + k4_v1)
        v_d += (dt / 6.0) * (k1_vd + 2.0 * k2_vd + 2.0 * k3_vd + k4_vd)

        if v_1 > v_pico:
            v_pico = v_1
        e_tvs_j += p_tvs * dt

    return {"v_pico_v": v_pico, "energia_tvs_mj": e_tvs_j * 1e3}


P_BASE: dict[str, float] = {
    "t_corte_us": T_CORTE_OVP_MAX_S * 1e6,
    "v_disparo_u1_v": V_DISPARO_MAX_U1_V,
    "i_mantenimiento_scr_a": I_MANTENIMIENTO_BT151_A,
}


def _guarda_u1_rk4(p: dict[str, float]) -> None:
    assert V_DISPARO_MIN_U1_V > V_SANO_MAX_U1_V, (
        f"disparo bajo {V_DISPARO_MIN_U1_V:.2f} V <= sano max {V_SANO_MAX_U1_V:.2f} V")
    res = escalon_lc(
        v_fallo_v=36.0,
        v_disparo_v=p["v_disparo_u1_v"],
        t_corte_s=p["t_corte_us"] * 1e-6,
        sensa_antes_del_lc=True,
        con_efuse=True,
        con_tvs=True,
    )
    assert res["v_pico_v"] <= V_ABSMAX_U1_V, (
        f"U1 supera absmax: pico {res['v_pico_v']:.2f} V > {V_ABSMAX_U1_V:.1f} V")


def _guarda_enganche_scr(p: dict[str, float]) -> None:
    peor_pliegue = min(d["i_pliegue_min_a"] for d in RACK_RIELES.values())
    assert p["i_mantenimiento_scr_a"] < peor_pliegue, (
        f"el crowbar se suelta: I_H={p['i_mantenimiento_scr_a']:.2f} A >= "
        f"pliegue={peor_pliegue:.2f} A")


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


def leer_csv() -> list[dict[str, str]]:
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def demo() -> int:
    print("check_absmax v5: modelo RK4 de #334 (TPS26631 + SMBJ16A) y crowbars D-F6\n")
    filas = leer_csv()
    assert len(filas) == 8, f"esperaba 8 filas en absmax.csv y hay {len(filas)}"

    con_tope = escalon_lc(v_fallo_v=36.0, sensa_antes_del_lc=True,
                          con_efuse=True, con_tvs=True)
    sin_tope = escalon_lc(v_fallo_v=36.0, sensa_antes_del_lc=True,
                          con_efuse=False, con_tvs=False)
    post_lc = escalon_lc(v_fallo_v=36.0, sensa_antes_del_lc=False,
                         con_efuse=True, con_tvs=False)

    print("  1. Simulacion RK4 de #334 (escalon de 36 V sobre el filtro LC de U1):")
    print(f"    maximo sano en vacio:             {V_SANO_MAX_U1_V:.3f} V")
    print(f"    banda de disparo TPS26631 (0,1%): {V_DISPARO_MIN_U1_V:.2f} .. {V_DISPARO_MAX_U1_V:.2f} V "
          f"(nom {V_DISPARO_NOM_U1_V:.2f} V)")
    print(f"    [verde] CON TPS26631 antes del LC (14 us) + SMBJ16A: "
          f"pico = {con_tope['v_pico_v']:.2f} V <= {V_ABSMAX_U1_V:.1f} V "
          f"(energia TVS {con_tope['energia_tvs_mj']:.2f} mJ)")
    print(f"    [rojo ] SIN proteccion (puente 36 V):                "
          f"pico = {sin_tope['v_pico_v']:.2f} V >  {V_ABSMAX_U1_V:.1f} V")
    print(f"    [rojo ] MUTANTE sensando DESPUES del LC (sin TVS):   "
          f"pico = {post_lc['v_pico_v']:.2f} V >  {V_ABSMAX_U1_V:.1f} V\n")

    assert con_tope["v_pico_v"] < V_ABSMAX_U1_V
    assert sin_tope["v_pico_v"] > V_ABSMAX_U1_V
    assert post_lc["v_pico_v"] > V_ABSMAX_U1_V

    print("  2. Ventanas de disparo en rack (D-F6: BT151-500R + TL431BI) y digital (T19):")
    for riel, d in RACK_RIELES.items():
        bajo = d["disparo_v"] - TOL_DISPARO_TL431BI_V
        alto = d["disparo_v"] + TOL_DISPARO_TL431BI_V
        holgura_baja = bajo - d["sano_max_v"]
        holgura_alta = d["victima_max_v"] - alto
        assert holgura_baja > 0.0, f"{riel}: disparo bajo {bajo} <= sano {d['sano_max_v']}"
        assert holgura_alta >= 0.0, f"{riel}: disparo alto {alto} > victima {d['victima_max_v']}"
        print(f"    {riel:<10} sano<={d['sano_max_v']:.2f}V | "
              f"disparo {bajo:.2f}..{alto:.2f}V | "
              f"victima<={d['victima_max_v']:.2f}V | "
              f"I_pliegue={d['i_pliegue_min_a']:.2f}A >> I_H={I_MANTENIMIENTO_BT151_A*1000:.0f}mA")

    print("\n  3. Matriz completa de absmax.csv:")
    # La fila de U1 no se cree: tiene que coincidir con el modelo. Antes era un
    # 18,08 escrito a mano que se comparaba consigo mismo.
    fila_u1 = next(f for f in filas if f["victima"].startswith("U1 "))
    assert abs(float(fila_u1["v_pico_con_tope_v"]) - con_tope["v_pico_v"]) <= 0.05, (
        f"absmax.csv dice {fila_u1['v_pico_con_tope_v']} V en U1 y el modelo da "
        f"{con_tope['v_pico_v']:.2f} V: actualiza la fila")
    tope_rack = {"Invitados rack +12V": "rack+12", "Invitados rack -12V": "rack-12",
                 "Invitados rack +5V": "rack+5", "Cerebro digital +5V": "digital+5"}
    for victima, riel in tope_rack.items():
        f = next(f for f in filas if f["victima"] == victima)
        esperado = RACK_RIELES[riel]["disparo_v"] + TOL_DISPARO_TL431BI_V
        assert abs(float(f["v_pico_con_tope_v"]) - esperado) <= 0.02, (
            f"absmax.csv dice {f['v_pico_con_tope_v']} V en {victima} y los divisores "
            f"de la placa dan {esperado:.2f} V: actualiza la fila")
    for f in filas:
        v_con = float(f["v_pico_con_tope_v"])
        v_max = float(f["v_absmax_v"])
        assert v_con <= v_max, f"{f['victima']} supera absmax: {v_con} > {v_max}"
        print(f"    [verde] {f['victima']:<24} ve {v_con:>5.2f} V <= {v_max:>5.2f} V "
              f"(margen +{v_max - v_con:.2f} V)")

    _guarda_u1_rk4(dict(P_BASE))
    _guarda_enganche_scr(dict(P_BASE))
    # Canario de retardo cuando falla el TVS (solo el TPS26631 cortando antes del LC):
    def _guarda_u1_solo_efuse(p: dict[str, float]) -> None:
        r = escalon_lc(v_fallo_v=36.0, v_disparo_v=p["v_disparo_u1_v"],
                       t_corte_s=p["t_corte_us"] * 1e-6,
                       sensa_antes_del_lc=True, con_efuse=True, con_tvs=False)
        assert r["v_pico_v"] <= V_ABSMAX_U1_V, (
            f"U1 supera absmax: pico {r['v_pico_v']:.2f} V > {V_ABSMAX_U1_V:.1f} V")

    t_max_us = borde_rojo(_guarda_u1_solo_efuse, dict(P_BASE), "t_corte_us",
                          14.0, 100.0, "U1 supera absmax")
    ih_max = borde_rojo(_guarda_enganche_scr, dict(P_BASE), "i_mantenimiento_scr_a",
                        0.040, 5.0, "el crowbar se suelta")
    print(f"\n  canario #334 (sin TVS): si el corte del TPS26631 tarda > {t_max_us:.1f} us, "
          f"U1 supera 20,0 V (la hoja garantiza <= 14,0 us)")
    print(f"  canario D-F6: con I_H > {ih_max:.2f} A el crowbar se soltaria "
          f"(el BT151-500R pide <= 0,04 A)")

    print("\nOK: check_absmax.py v5 (#334, #340 y T18..T21 en verde)")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
