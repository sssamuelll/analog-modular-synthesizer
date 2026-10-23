"""Temperatura de union de U1 (LT1963A) y U2 (LT3015) en la placa v5 (#478).

    python hardware/01-power-supply/v5/tj_budget.py

Tj = aire del cajon + P * theta_JA <= 125 C (TJMAX de las dos hojas, p. 2).

  * P: (Vin - Vout) * Iout + Vin * Ignd (lt1963a-rev-g-2021-02.pdf p. 19 y
    lt3015-rev-b.pdf p. 19), con la cascada de `ladrillo_budget.cascada_w()`.
    La Ignd sale interpolada entre las filas de la columna MAX de la hoja
    (LT1963A p. 5, LT3015 p. 5) a la corriente que pasa por el regulador, no
    de la fila de 1,5 A. Las filas crecen cada vez mas deprisa, asi que la
    recta entre dos filas queda por encima de la curva; y las dos hojas dicen
    que la Ignd baja con mas tension de entrada (LT1963A Note 8, LT3015
    Note 6), que aqui es 2,7..2,9 V por encima de la salida.
  * theta_JA: la fila de la tabla de la hoja cuyo cobre el de la placa iguala
    o supera en las tres columnas (cara de arriba, cara de abajo, area de
    placa). Mas cobre y mas placa solo bajan theta_JA, asi que esa fila es una
    cota. Si ninguna fila queda cubierta, la union no tiene cota: HUECO.
    El cobre se mide en `kicad/sam17-power-v5.kicad_pcb` (los rellenos de la
    red de la aleta que tocan su campo de vias), y los rectangulos se leen de
    TERMICO y VIAS_TERMICAS en `kicad/build_pcb.py`.
  * Aire: `derating_budget.aire_cajon_c()`, la sala de diseno del case (45 C)
    mas el salto pesimista de su chimenea.

Tablas (still air, cobre de una onza en la LT1963A; la LT3015 midio en una
placa de 4 capas con 2 oz fuera y sin vias, que no es la nuestra):
  LT1963A p. 19, Table 3, DD:  2500/2500/2500 23 C/W, 1000/2500/2500 25,
                               125/2500/2500 33.
  LT3015 p. 19, Table 4, DD-Pak: 2500/2500/2500 14 C/W, 1000/2500/2500 16,
                               225/2500/2500 19.

LO QUE ESTE CALCULO NO CUBRE (se imprime al final):
  * El calor de las otras piezas que comparten los planos de la aleta: las
    tablas miden la pieza sola en su placa.
  * El aire junto a la placa por encima del salto medio de la chimenea.
"""
from __future__ import annotations

import ast
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

import derating_budget as db        # noqa: E402
import ladrillo_budget as lb        # noqa: E402

PCB = os.path.join(DIR, "kicad", "sam17-power-v5.kicad_pcb")
BUILD_PCB = os.path.join(DIR, "kicad", "build_pcb.py")
TJ_MAX_C = 125.0     # lt1963a p. 2 y lt3015 p. 2, "TJMAX = 125C"

# Columna MAX de "GND Pin Current" (A de carga -> A de Ignd).
IGND_MAX_A = {
    "U1": ((0.100, 0.0055), (0.500, 0.025), (1.500, 0.120)),   # lt1963a p. 5
    "U2": ((0.100, 0.007), (0.500, 0.023), (1.500, 0.070)),    # lt3015 p. 5
}
# (cara de arriba mm2, cara de abajo mm2, placa mm2, C/W)
TABLA_THETA = {
    "U1": ((2500, 2500, 2500, 23.0), (1000, 2500, 2500, 25.0), (125, 2500, 2500, 33.0)),
    "U2": ((2500, 2500, 2500, 14.0), (1000, 2500, 2500, 16.0), (225, 2500, 2500, 19.0)),
}
HOJA = {"U1": "lt1963a-rev-g-2021-02.pdf p. 19, Table 3",
        "U2": "lt3015-rev-b.pdf p. 19, Table 4"}

_HUECOS: list[str] = []


def ignd_a(reg: str, i_a: float) -> float:
    """La Ignd MAX interpolada entre las dos filas que encierran `i_a`."""
    filas = IGND_MAX_A[reg]
    for (x0, y0), (x1, y1) in zip(filas, filas[1:]):
        if x0 <= i_a <= x1:
            return y0 + (y1 - y0) * (i_a - x0) / (x1 - x0)
    raise ValueError(f"{reg}: {i_a:.3f} A fuera de las filas de la hoja")


def i_regulador_a(reg: str) -> float:
    return lb.CASCADA_A + lb.N_LDO_ULTRA_POR_RAMA * lb.IGND_LDO_ULTRA_MAX_A[reg]


def potencia_w(reg: str) -> float:
    v_thn = lb.V_CRUDO_CASCADA * (1 + lb.TOL_CRUDO)
    return lb.cascada_w(reg, v_thn=v_thn, iq_pre=ignd_a(reg, i_regulador_a(reg)))[
        f"{reg} (pre-regulador)"]


def _literal(nombre: str):
    arbol = ast.parse(open(BUILD_PCB, encoding="utf-8").read())
    for n in arbol.body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == nombre for t in n.targets):
            return ast.literal_eval(n.value)
    raise AssertionError(f"build_pcb.py ya no define {nombre}")


def _rellenos(txt: str) -> list[tuple[str, str, list[tuple[float, float]]]]:
    """(red, capa, contorno) de cada relleno de zona del .kicad_pcb."""
    out = []
    for m in re.finditer(r"\n\t\(zone\n", txt):
        i, prof = m.start() + 2, 0                  # en el "(" de "(zone"
        for j in range(i, len(txt)):
            prof += {"(": 1, ")": -1}.get(txt[j], 0)
            if prof == 0:
                break
        zona = txt[i:j + 1]
        red = re.search(r'\(net "([^"]*)"\)', zona).group(1)
        for f in re.finditer(r'\(filled_polygon\s*\(layer "([^"]+)"\)\s*\(pts(.*?)\)\s*\)', zona, re.S):
            pts = [(float(a), float(b)) for a, b in re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", f.group(2))]
            out.append((red, f.group(1), pts))
    return out


def _area(pts) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def _dentro(pts, x: float, y: float) -> bool:
    c = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def cobre_mm2() -> dict[str, dict[str, float]]:
    """Cobre de la red de la aleta, por capa, que toca su campo de vias termicas."""
    txt = open(PCB, encoding="utf-8").read()
    rellenos = _rellenos(txt)
    placa = _area_placa_mm2(txt)
    out = {}
    for ref, red, (x0, y0, x1, y1) in _literal("VIAS_TERMICAS"):
        puntos = [(x0 + (x1 - x0) * a / 4, y0 + (y1 - y0) * b / 4) for a in (1, 2, 3) for b in (1, 2, 3)]
        por_capa = {}
        for capa in ("F.Cu", "B.Cu"):
            por_capa[capa] = sum(_area(pts) for r, c, pts in rellenos
                                 if r == red and c == capa and any(_dentro(pts, x, y) for x, y in puntos))
        vias = [v for v in re.findall(r'\(via\s*\(at ([-\d.]+) ([-\d.]+)\).*?\(net "([^"]*)"\)', txt, re.S)
                if v[2] == red and x0 <= float(v[0]) <= x1 and y0 <= float(v[1]) <= y1]
        por_capa.update(vias=len(vias), red=red, placa=placa)
        out[ref] = por_capa
    return out


def _area_placa_mm2(txt: str) -> float:
    """El rectangulo que encierra Edge.Cuts."""
    pts = [(float(a), float(b)) for blk in re.findall(r'\((?:gr_line|gr_rect)(.*?)\(layer "Edge\.Cuts"\)', txt, re.S)
           for a, b in re.findall(r"\((?:start|end) ([-\d.]+) ([-\d.]+)\)", blk)]
    assert pts, "el .kicad_pcb no tiene Edge.Cuts"
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def theta_ja(reg: str, cobre: dict) -> float | None:
    """La fila mas baja de la tabla que el cobre de la placa cubre, o None."""
    filas = [th for arriba, abajo, placa, th in TABLA_THETA[reg]
             if cobre["F.Cu"] >= arriba and cobre["B.Cu"] >= abajo and cobre["placa"] >= placa]
    return min(filas) if filas else None


def _guarda(p: dict[str, float]) -> None:
    for reg in ("U1", "U2"):
        th = p[f"theta_{reg}"]
        if th is None:
            continue
        tj = p["t_aire_c"] + p[f"p_{reg}"] * th
        assert tj <= TJ_MAX_C, (
            f"{reg} llega a {tj:.1f} C de union con {p[f'p_{reg}']:.2f} W, {th:g} C/W y el "
            f"aire a {p['t_aire_c']:.1f} C: pasa de TJMAX")


def _autocomprobacion() -> None:
    # A mano: 0,7 A en la LT1963A cae entre las filas de 0,5 A (25 mA) y 1,5 A
    # (120 mA): 25 + 0,2 * 95 = 44 mA.
    assert abs(ignd_a("U1", 0.700) - 0.044) < 1e-9
    for reg, filas in IGND_MAX_A.items():
        pend = [(y1 - y0) / (x1 - x0) for (x0, y0), (x1, y1) in zip(filas, filas[1:])]
        assert all(b > a for a, b in zip(pend, pend[1:])), (
            f"{reg}: las filas de Ignd ya no crecen cada vez mas deprisa; la recta "
            f"entre filas dejaria de ser cota")


def demo() -> int:
    _autocomprobacion()
    t_aire = db.aire_cajon_c()
    cobre = cobre_mm2()
    p = {"t_aire_c": t_aire}
    print(f"Union de U1/U2 con el aire del cajon a {t_aire:.1f} C\n")
    for reg in ("U1", "U2"):
        c = cobre[reg]
        i = i_regulador_a(reg)
        p[f"p_{reg}"] = potencia_w(reg)
        p[f"theta_{reg}"] = theta_ja(reg, c)
        print(f"  {reg}: {i * 1e3:.0f} mA por el regulador, Ignd {ignd_a(reg, i) * 1e3:.1f} mA "
              f"(fila de 1,5 A: {lb.IQ_PRE_A[reg] * 1e3:.0f}), {p[f'p_{reg}']:.2f} W "
              f"(con la fila de 1,5 A: {lb.quema_pre_regulador_w(reg):.2f})")
        print(f"      {c['red']}: {c['F.Cu']:.0f} mm2 arriba, {c['B.Cu']:.0f} abajo, "
              f"{c['vias']} vias, placa {c['placa']:.0f} mm2")
        th = p[f"theta_{reg}"]
        if th is None:
            peor = min(f[3] for f in TABLA_THETA[reg])
            _HUECOS.append(
                f"{reg}: su cobre ({c['F.Cu']:.0f} mm2 arriba, {c['B.Cu']:.0f} abajo) no cubre "
                f"ninguna fila de {HOJA[reg]}, que piden 2500 mm2 abajo: sin cota de union. "
                f"Con la fila mejor ({peor:g} C/W, que no es la suya) seria "
                f"{t_aire + p[f'p_{reg}'] * peor:.1f} C")
            print(f"      [HUECO] ninguna fila de {HOJA[reg]} queda cubierta")
        else:
            print(f"      cota {th:g} C/W ({HOJA[reg]}) -> Tj {t_aire + p[f'p_{reg}'] * th:.1f} C "
                  f"contra {TJ_MAX_C:.0f}")
    _guarda(p)

    print("\n  LO QUE NO CUBRE:")
    print("    - el calor de las otras piezas en los planos de la aleta (la tabla mide la pieza sola)")
    print("    - el aire junto a la placa por encima del salto medio de la chimenea")
    if _HUECOS:
        print("\nHUECOS:")
        for h in _HUECOS:
            print(f"  - {h}")
        print(f"\nHUECO: tj_budget.py v5 ({len(_HUECOS)} sin cota)")
        return 2
    print("\nOK: tj_budget.py v5 (#478)")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
