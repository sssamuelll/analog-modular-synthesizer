"""La carga de cada convertidor contra su derating, al aire del cajon (#478).

    python hardware/01-power-supply/v5/derating_budget.py

Cruza tres cosas que viven en sitios distintos y que nadie cruzaba:

  * la carga de cada riel, de `ladrillo_budget.rieles()`;
  * la curva de derating de cada convertidor, de `curvas.derating()` (cada
    curva cita su figura de hoja);
  * el aire del cajon: la sala de diseno del case (`T_SALA_DISENO_K`, 45 C) mas
    el salto de su chimenea con el C_D pesimista, escalado a esa sala, como lo
    escala `case/clearance_budget.guarda_aire()`. El salto sale de
    `potencia_disipada` en `params.scad`, que clearance_budget cruza con
    `ladrillo_budget.calor_del_cajon_w()`.

La carga de un convertidor es la mayor de sus fracciones: la corriente de cada
salida contra la nominal de su hoja y la potencia total contra la nominal. Pasa
si esa fraccion cabe bajo la curva a la temperatura del aire.

Nominales (todas en la p. 1 de su hoja, `docs/reference/datasheets/`):
  PS1 THN 30-2422WI   +-12 V, +-1250 mA, 30 W    traco_thn30wi.pdf
  PS2 URB2405YMD-20WR3   5 V,  4000 mA, 20 W     mornsun_urb_ymd20wr3.pdf
  PS3 K7805T-1000R3      5 V,  1000 mA           mornsun_k78_t1000r3.pdf
  PS4, PS5 THN 20-2413WI 15 V, 1330 mA, 20 W     traco_thn20wi.pdf

LO QUE ESTE CALCULO NO CUBRE (se imprime al final):
  * El aire junto a cada convertidor puede ir por encima del salto medio de la
    chimenea, que es una media de la columna de aire.
  * Las curvas son las de la hoja sin disipador ni flujo forzado; el cajon
    tiene tiro natural, que es la condicion de la hoja.
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(DIR, "..", "..", "..", "case")
TOOLS = os.path.join(DIR, "..", "..", "tools")
for _d in (DIR, CASE, TOOLS):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import clearance_budget as cb       # noqa: E402
import ladrillo_budget as lb        # noqa: E402
from canario import borde_rojo      # noqa: E402
from curvas import DERATING_V5, derating  # noqa: E402

#   ref: (curva de curvas.py, A nominales por salida, W nominales, rieles de rieles())
CONVERTIDORES = {
    "PS1": ("THN-30-2422WI", 1.25, 30.0,
            ("+12 rack (bus fila B + pantalla)", "-12 rack (bus fila B)")),
    "PS2": ("URB2405YMD-20WR3", 4.0, 20.0, ("+5 digital (4 x N657 + host USB)",)),
    "PS3": ("K7805T-1000R3", 1.0, 5.0, ("+5 rack (bus fila B + +5V_AUX)",)),
    "PS4": ("THN-20-2413WI", 1.33, 20.0, ("crudo +cascada (a U1)",)),
    "PS5": ("THN-20-2413WI", 1.33, 20.0, ("crudo -cascada (a U2)",)),
}


def aire_cajon_c() -> float:
    """La sala de diseno del case mas el salto pesimista de su chimenea."""
    p = cb.leer_params()
    f_sala = cb.T_SALA_DISENO_K / cb.T_AMB
    return cb.T_SALA_DISENO_K - 273.15 + cb._tiro_pesimista(p)["dt"] * f_sala


def carga(ref: str, x_carga: float = 1.0) -> float:
    """La mayor fraccion de nominal que pide `ref`: por salida o en total."""
    _curva, i_nom, p_nom, nombres = CONVERTIDORES[ref]
    rieles = {r["nombre"]: r for r in lb.rieles()}
    assert all(n in rieles for n in nombres), (
        f"{ref}: rieles() ya no tiene {[n for n in nombres if n not in rieles]}")
    i = max(rieles[n]["a"] for n in nombres) * x_carga
    w = sum(abs(rieles[n]["v"]) * rieles[n]["a"] for n in nombres) * x_carga
    return max(i / i_nom, w / p_nom)


def _guarda(p: dict[str, float], solo: str | None = None) -> None:
    for ref, (curva, *_resto) in CONVERTIDORES.items():
        if solo and ref != solo:
            continue
        f = carga(ref, p["x_carga"])
        tope = derating(curva, p["t_aire_c"])
        assert f <= tope, (
            f"{ref} ({curva}) pide el {f:.0%} de su nominal y a {p['t_aire_c']:.1f} C "
            f"su derating deja el {tope:.0%}: se sale de su derating")


def _fin(ref: str) -> float:
    """El final de la curva de `ref`: mas alla curvas.derating() no extrapola."""
    return DERATING_V5[CONVERTIDORES[ref][0]][-1][0]


def _guarda_de(ref: str):
    def guarda(p: dict[str, float]) -> None:
        _guarda(p, solo=ref)
    guarda.__name__ = f"_guarda_{ref}"
    return guarda


def _autocomprobacion() -> None:
    # A mano, PS3: la curva del K78 baja del 92 % en 65 C al 60 % en 85 C
    # (mornsun_k78_t1000r3.pdf p. 3), 1,6 puntos por grado. Con 0,80 A de 1 A
    # se queda sin derating en 65 + (0,92 - 0,80) / 0,016 = 72,5 C.
    assert abs(carga("PS3") - 0.80) < 1e-9, f"PS3 pide {carga('PS3'):.3f}, no 0,80"
    borde = borde_rojo(_guarda_de("PS3"), {"t_aire_c": 20.0, "x_carga": 1.0},
                       "t_aire_c", 20.0, _fin("PS3"), "se sale de su derating")
    assert abs(borde - 72.5) < 0.2, f"el borde de PS3 sale en {borde:.2f} C, no 72,5"


def demo() -> int:
    _autocomprobacion()
    t = aire_cajon_c()
    p = {"t_aire_c": t, "x_carga": 1.0}
    print(f"Derating de los convertidores con el aire del cajon a {t:.1f} C "
          f"(sala de {cb.T_SALA_DISENO_K - 273.15:.0f} C + chimenea pesimista)\n")
    print(f"  {'':4} {'pieza':<18} {'pide':>6} {'deja':>6}   rojo con el aire a")
    for ref, (curva, *_resto) in CONVERTIDORES.items():
        _guarda(p, solo=ref)
        borde = borde_rojo(_guarda_de(ref), p, "t_aire_c", t, _fin(ref), "se sale de su derating")
        print(f"  [verde] {ref} {curva:<18} {carga(ref):>5.0%} {derating(curva, t):>5.0%}"
              f"   {borde:.1f} C (+{borde - t:.1f} K)")
    x = borde_rojo(_guarda, p, "x_carga", 1.0, 3.0, "se sale de su derating")
    print(f"\n  canario: con las cargas x {x:.2f} algun convertidor se sale de su derating")

    print("\n  LO QUE NO CUBRE:")
    print("    - el aire junto a cada convertidor por encima del salto medio de la chimenea")
    print("    - curvas de hoja sin disipador ni flujo forzado (el cajon va por tiro natural)")
    print("\nOK: derating_budget.py v5 (#478)")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
