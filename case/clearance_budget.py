"""Presupuesto de holguras del case, en mm.

    python case/clearance_budget.py

Hermano de tuning_budget.py y ground_budget.py, pero mecanico: aqui lo que
se agota no son cents sino milimetros. La distincion que organiza esto:

  El modelo OpenSCAD (sam17_case.scad) DIBUJA; este script DECIDE si lo
  dibujado cabe. Los dos leen los mismos numeros (case/cad/params.scad,
  unica fuente de verdad), pero este recalcula la geometria con su propia
  trigonometria — si el .scad y el budget discrepan, uno de los dos miente
  y la autocomprobacion lo delata.

Convencion: angulos de cara medidos DESDE LA VERTICAL (spec §4 rev. 3).
Corre en verde ANTES de mandar nada a cortar (constitucion, Principio III).
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

PARAMS = Path(__file__).parent / "cad" / "params.scad"


def leer_params() -> dict[str, float]:
    texto = PARAMS.read_text(encoding="utf-8")
    pares = re.findall(r"^\s*(\w+)\s*=\s*(-?[0-9.]+)\s*;", texto, re.M)
    if len(pares) < 20:
        raise SystemExit(f"params.scad: solo {len(pares)} parametros parseados")
    return {k: float(v) for k, v in pares}


def perfil(p: dict[str, float]) -> dict[str, float]:
    """Vertices del perfil lateral (X = fondo hacia atras, Y = arriba)."""
    si, ci = math.sin(math.radians(p["angulo_inferior"])), math.cos(
        math.radians(p["angulo_inferior"]))
    ss, cs = math.sin(math.radians(p["angulo_superior"])), math.cos(
        math.radians(p["angulo_superior"]))
    y_entrepiso = p["alto_frontal"] + p["alto_panel"] * ci
    x_cara_inf = p["alto_panel"] * si
    x_cara_sup0 = x_cara_inf + p["paso_horizontal"]
    x_cara_sup1 = x_cara_sup0 + p["alto_panel"] * ss
    alto_total = y_entrepiso + p["alto_panel"] * cs
    return {
        "y_entrepiso": y_entrepiso,
        "alto_total": alto_total,
        "prof_sup_min": x_cara_sup1,
        "alto_interior_inferior": y_entrepiso - p["t_acrilico"],
        "ancho_util": p["ancho_total"] - 2 * p["t_cheek"],
    }


def autocomprobacion(p: dict[str, float]) -> None:
    """Caso hecho a mano (spec §4): 12/35 grados, panel 190, zocalo 50."""
    g = perfil({**p, "angulo_inferior": 12, "angulo_superior": 35,
                "alto_panel": 190, "alto_frontal": 50, "paso_horizontal": 20,
                "t_acrilico": 5, "ancho_total": 500, "t_cheek": 8})
    # A mano: 50 + 190*cos12 = 50 + 185.85 = 235.85
    assert abs(g["y_entrepiso"] - 235.85) < 0.05, g["y_entrepiso"]
    # A mano: 235.85 + 190*cos35 = 235.85 + 155.64 = 391.49
    assert abs(g["alto_total"] - 391.49) < 0.05, g["alto_total"]
    # A mano: 190*sin12 + 20 + 190*sin35 = 39.51 + 20 + 108.99 = 168.50
    assert abs(g["prof_sup_min"] - 168.50) < 0.05, g["prof_sup_min"]


def _vertices(p: dict[str, float]) -> list[tuple[float, float]]:
    """P0..P8 del perfil lateral, misma formula y numeracion que
    pts_perfil() en sam17_case.scad."""
    si, ci = math.sin(math.radians(p["angulo_inferior"])), math.cos(
        math.radians(p["angulo_inferior"]))
    ss, cs = math.sin(math.radians(p["angulo_superior"])), math.cos(
        math.radians(p["angulo_superior"]))
    ye = p["alto_frontal"] + p["alto_panel"] * ci
    x2 = p["alto_panel"] * si
    x3 = x2 + p["paso_horizontal"]
    x4 = x3 + p["alto_panel"] * ss
    yt = ye + p["alto_panel"] * cs
    return [(0, 0), (0, p["alto_frontal"]), (x2, ye), (x3, ye), (x4, yt),
            (p["prof_superior"], yt), (p["prof_superior"], ye),
            (p["prof_inferior"], ye), (p["prof_inferior"], 0)]


def _centros_rail(p: dict[str, float],
                   P: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """4 centros de rail de panel [cara_inf x2, cara_sup x2], misma formula
    que centros_rail() en sam17_case.scad."""
    caras = [(P[1], P[2]), (P[3], P[4])]
    off = p["t_panel"] + p["rail"] / 2
    out = []
    for c0, c1 in caras:
        dx, dy = c1[0] - c0[0], c1[1] - c0[1]
        dl = math.hypot(dx, dy)
        dx, dy = dx / dl, dy / dl
        nx, ny = dy, -dx
        for s in (p["inset_tornillo"], p["alto_panel"] - p["inset_tornillo"]):
            out.append((c0[0] + dx * s + nx * off, c0[1] + dy * s + ny * off))
    return out


def _centros_esqueleto(p: dict[str, float], P: list[tuple[float, float]],
                        cr: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """6 centros de larguero de esqueleto, misma formula que
    centros_esqueleto() en sam17_case.scad (entrepiso delantero reubicado,
    ambos railes de entrepiso a la altura nueva, y repisa — ronda de
    revision 2, R6: piel_superior se reancla aqui en vez de en entrepiso
    trasero, que vive en el plano del piso inferior y no del superior)."""
    r = p["rail"] / 2
    x_ed = cr[2][0] + p["rail"] + p["holgura_rail"]
    y_ep = P[3][1] - p["t_acrilico"] - r
    return [(r + 2, r), (p["prof_inferior"] - r, r),
            (x_ed, y_ep), (p["prof_inferior"] - r, y_ep),
            (p["prof_superior"] - r, P[5][1] - r),
            (p["prof_superior"] - r, P[3][1] + 15)]


# Caja = (nombre, x0, x1, y0, y1, z0, z1)
Caja = tuple


def _cajas_solidas(p: dict[str, float]) -> tuple[list[Caja], list[Caja]]:
    """AABB de los 10 railes y de las 5 planchas/pieles, misma formula que
    rails()/planchas_acrilico() en sam17_case.scad."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ce = _centros_esqueleto(p, P, cr)
    rail, t_cheek = p["rail"], p["t_cheek"]
    t_acr, gap = p["t_acrilico"], p["gap_sombra"]
    ancho_total = p["ancho_total"]

    nombres_cr = ["cara_inf s=inset", "cara_inf s=alto-inset",
                  "cara_sup s=inset", "cara_sup s=alto-inset"]
    angs = [p["angulo_inferior"], p["angulo_inferior"],
            p["angulo_superior"], p["angulo_superior"]]
    railes: list[Caja] = []
    for nm, c, ang in zip(nombres_cr, cr, angs):
        # R3: el rail gira -ang sobre su eje largo para calzar a ras de la
        # cara. El AABB real de un cuadrado girado crece a
        # (rail/2)*(|cos|+|sin|) — usar rail/2 sin mas SUBESTIMA el alcance
        # de la esquina (0.261 mm de error verificado en la ronda de
        # revision: rail/2*(|n.x|+|n.y|)=11.861 > off=11.6).
        he = (rail / 2) * (abs(math.cos(math.radians(ang)))
                            + abs(math.sin(math.radians(ang))))
        railes.append((nm, c[0] - he, c[0] + he, c[1] - he, c[1] + he,
                       t_cheek, ancho_total - t_cheek))
    nombres_ce = ["base delantera", "base trasera", "entrepiso delantero",
                  "entrepiso trasero", "remate superior", "repisa"]
    for nm, c in zip(nombres_ce, ce):
        railes.append((nm, c[0] - rail / 2, c[0] + rail / 2,
                       c[1] - rail / 2, c[1] + rail / 2,
                       t_cheek, ancho_total - t_cheek))

    planchas: list[Caja] = []
    # bandeja_base: sin cambios en esta ronda
    depth_bb = p["prof_inferior"] - 2 * rail - 4
    planchas.append(("bandeja_base", rail, rail + depth_bb, rail, rail + t_acr,
                     t_cheek, ancho_total - t_cheek))
    # bandeja_entrepiso: R2 — canto trasero a ras de entrepiso-trasero,
    # tope (no fondo) a ras de P3.y
    x0_be = ce[2][0] - rail / 2
    fondo_be = p["prof_inferior"] - ce[2][0] + rail / 2
    planchas.append(("bandeja_entrepiso", x0_be, x0_be + fondo_be,
                     P[3][1] - t_acr, P[3][1], t_cheek, ancho_total - t_cheek))
    # zocalo: R1 — volado hacia -X (standoffs), ya no bolonado directo
    alto_zoc = cr[0][1] - ce[0][1] + 30
    y0_zoc = ce[0][1] - 15
    planchas.append(("zocalo", -gap - t_acr, -gap, y0_zoc, y0_zoc + alto_zoc,
                     t_cheek + gap, ancho_total - t_cheek - gap))
    # piel_inferior: R1 — volada hacia +X mas alla de prof_inferior
    alto_pi = ce[3][1] - ce[1][1] + 30
    y0_pi = ce[1][1] - 15
    planchas.append(("piel_inferior", P[8][0] + gap, P[8][0] + gap + t_acr,
                     y0_pi, y0_pi + alto_pi, t_cheek + gap, ancho_total - t_cheek - gap))
    # piel_superior: R1 — volada hacia +X mas alla de prof_superior;
    # re-anclada a la repisa (ce[5]) en vez de entrepiso trasero (R6)
    alto_ps = ce[4][1] - ce[5][1] + 30
    y0_ps = ce[5][1] - 15
    planchas.append(("piel_superior", P[6][0] + gap, P[6][0] + gap + t_acr,
                     y0_ps, y0_ps + alto_ps, t_cheek + gap, ancho_total - t_cheek - gap))
    return railes, planchas


def _overlap(a: Caja, b: Caja) -> tuple[float, float, float] | None:
    ax0, ax1, ay0, ay1, az0, az1 = a[1:]
    bx0, bx1, by0, by1, bz0, bz1 = b[1:]
    ox = min(ax1, bx1) - max(ax0, bx0)
    oy = min(ay1, by1) - max(ay0, by0)
    oz = min(az1, bz1) - max(az0, bz0)
    return (ox, oy, oz) if (ox > 1e-9 and oy > 1e-9 and oz > 1e-9) else None


# Pares tolerados: ronda de revision 1 dejo 2 aqui (bandeja_entrepiso vs
# piel_superior, y el par de railes tilted del quiebre P2-P3). Ronda 2 los
# resuelve los dos de verdad (R6 reancla piel_superior a la repisa en vez
# de entrepiso trasero; R7 abre paso_horizontal 20->25 y separa los railes
# — ver guarda_escalon() mas abajo, que hace el chequeo SAT exacto de ESE
# par como assert duro, no como tolerancia). Vacio a proposito: si un solape
# nuevo aparece y de verdad no se puede resolver sin tocar centros_rail()
# fuera de las reglas autorizadas, se documenta aqui igual que antes.
TOLERADOS: dict[frozenset[str], float] = {}


def solapes(p: dict[str, float]) -> list[str]:
    """10 railes + 5 planchas/pieles: ningun par se pisa en 3D, salvo los
    TOLERADOS de arriba (impresos igual, nunca silenciados) — vacio ahora
    mismo. Paneles inclinados (1.6 mm, PCB de aluminio de cada modulo): su
    clase la resuelve la rotacion de railes (R3), no entran en esta caja."""
    railes, planchas = _cajas_solidas(p)
    fallos: list[str] = []
    todas = railes + planchas
    n_rail = len(railes)
    for i in range(len(todas)):
        for j in range(i + 1, len(todas)):
            a, b = todas[i], todas[j]
            ov = _overlap(a, b)
            if not ov:
                continue
            tol = TOLERADOS.get(frozenset({a[0], b[0]}))
            estrecho = min(ov[0], ov[1])
            if tol is not None and estrecho <= tol:
                print(f"AMARILLO (tolerado): {a[0]} <-> {b[0]}  "
                      f"dX={ov[0]:.2f} dY={ov[1]:.2f} dZ={ov[2]:.2f}")
                continue
            grupo = ("railes" if j < n_rail else
                      "railes-planchas" if i < n_rail else "planchas")
            fallos.append(f"solape [{grupo}] {a[0]} <-> {b[0]}: "
                          f"dX={ov[0]:.2f} dY={ov[1]:.2f} dZ={ov[2]:.2f}")
    return fallos


def canario_solapes(p: dict[str, float]) -> None:
    """Autocomprobacion roja: alimenta la posicion VIEJA (pre-fix, Task 5)
    del rail entrepiso-delantero y exige que el checker la marque como
    solape contra el rail de panel cara-superior s=inset_tornillo. Si esto
    no dispara, el checker esta ciego y no detecta nada de verdad."""
    P = _vertices(p)
    r = p["rail"] / 2
    old_ed = (P[3][0] + r, P[3][1] - r)          # formula pre-fix (Task 5)
    cr = _centros_rail(p, P)
    ang = p["angulo_superior"]
    he = (p["rail"] / 2) * (abs(math.cos(math.radians(ang)))
                             + abs(math.sin(math.radians(ang))))
    c = cr[2]
    vecino = ("cara_sup s=inset", c[0] - he, c[0] + he, c[1] - he, c[1] + he,
              p["t_cheek"], p["ancho_total"] - p["t_cheek"])
    viejo = ("entrepiso delantero VIEJO",
             old_ed[0] - r, old_ed[0] + r, old_ed[1] - r, old_ed[1] + r,
             p["t_cheek"], p["ancho_total"] - p["t_cheek"])
    ov = _overlap(viejo, vecino)
    assert ov is not None, (
        "canario de solapes no disparo: el checker no detecta un choque "
        "conocido (17.6x12.6 mm) — no confiar en el resto de solapes()")


def _sat_gap(rail: float, c1: tuple[float, float], ang1: float,
             c2: tuple[float, float], ang2: float) -> float:
    """Holgura EXACTA (SAT, no AABB) entre 2 cuadrados de lado 'rail',
    cada uno girado -ang grados sobre su eje largo (mismo signo que
    rotate([0,0,-ang]) en rails(), R3). Positivo = hueco en mm; negativo =
    profundidad de solape en mm. El AABB (usado en solapes()) SOBRESTIMA
    el alcance real de un cuadrado girado salvo en la propia direccion de
    la normal — para un umbral duro en mm hace falta el valor exacto."""
    half = rail / 2

    def esquinas(c: tuple[float, float], ang: float) -> list[tuple[float, float]]:
        a = math.radians(-ang)
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -math.sin(a), math.cos(a)
        return [(c[0] + sx * half * ux + sy * half * vx,
                 c[1] + sx * half * uy + sy * half * vy)
                for sx in (-1, 1) for sy in (-1, 1)]

    def proyeccion(pts: list[tuple[float, float]],
                    eje: tuple[float, float]) -> tuple[float, float]:
        vals = [px * eje[0] + py * eje[1] for px, py in pts]
        return min(vals), max(vals)

    p1, p2 = esquinas(c1, ang1), esquinas(c2, ang2)
    ejes = []
    for ang in (ang1, ang2):
        a = math.radians(-ang)
        ejes.append((math.cos(a), math.sin(a)))
        ejes.append((-math.sin(a), math.cos(a)))
    separaciones = []
    for eje in ejes:
        a0, a1 = proyeccion(p1, eje)
        b0, b1 = proyeccion(p2, eje)
        separaciones.append(min(a1, b1) - max(a0, b0))
    return -min(separaciones)  # min<=0 en algun eje separador -> hueco positivo


def guarda_escalon(p: dict[str, float]) -> None:
    """R7: paso_horizontal se abrio para separar los 2 railes tilted que
    R3 acerco en el quiebre P2-P3 (cara_inf s=alto-inset, 12 grados, vs
    cara_sup s=inset, 35 grados — a paso_horizontal=20 se solapaban 2.52 mm
    exactos por SAT, verificado en la ronda de revision 1). Assert duro,
    no tolerancia: exige >=1.0 mm de hueco REAL (no la caja alineada a
    ejes, que aqui sobrestima)."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    gap = _sat_gap(p["rail"], cr[1], p["angulo_inferior"], cr[2], p["angulo_superior"])
    assert gap >= 1.0, (
        f"railes del escalon P2-P3 (cara_inf s=alto-inset vs cara_sup "
        f"s=inset) a {gap:.3f} mm de hueco real (SAT) — se exige >=1.0 mm; "
        f"subir paso_horizontal")


# Censo de anchos minimos de panel por piso, mm. ESTIMADOS (spec §11):
# cierran cuando cada panel este dibujado. Fuente: conteo de mandos/jacks
# de los README de modulo + patch bay normalizado que anade jacks.
ANCHOS_PISO_SUP = {"MIDI/CV": 80, "VCO1": 90, "VCO2": 90, "VCO3": 90}
ANCHOS_PISO_INF = {"VCF": 100, "ADSR": 110, "VCA": 80, "MIXER": 100}
EXPANSION_MIN = 40  # sitio reservado a crecer, por piso


def main() -> int:
    p = leer_params()
    autocomprobacion(p)
    canario_solapes(p)
    guarda_escalon(p)
    g = perfil(p)
    fallos: list[str] = []

    def exige(cond: bool, msg: str) -> None:
        (fallos.append if not cond else (lambda m: None))(msg)

    exige(g["alto_interior_inferior"]
          >= p["alto_transformador"] + p["margen_transformador"],
          "transformador no cabe en el piso inferior con margen")
    exige(p["prof_superior"] >= g["prof_sup_min"] + 10,
          "prof_superior no cubre la proyeccion de la cara superior + 10")
    exige(p["prof_inferior"] >= p["prof_superior"] + 60,
          "la repisa trasera del piso inferior queda menor de 60 mm")
    exige(p["fondo_pcb_max"] + 10 <= p["prof_superior"] - p["rail"],
          "la PCB mas honda del censo no cabe bajo la cara superior")
    exige(sum(ANCHOS_PISO_SUP.values()) + EXPANSION_MIN <= g["ancho_util"],
          "el piso superior no cabe en el ancho util")
    exige(sum(ANCHOS_PISO_INF.values()) + EXPANSION_MIN <= g["ancho_util"],
          "el piso inferior no cabe en el ancho util")
    exige(p["sep_railes"] == p["alto_panel"] - 2 * p["inset_tornillo"],
          "sep_railes no sale de alto_panel - 2*inset (spec §6)")
    exige(p["vent_puente_min"] >= 0.8 * p["t_acrilico"],
          "puente de ventilacion fragil para el espesor")
    fallos.extend(solapes(p))

    print(f"perfil: alto_total={g['alto_total']:.1f}  "
          f"entrepiso={g['y_entrepiso']:.1f}  ancho_util={g['ancho_util']:.0f}")
    for f in fallos:
        print(f"ROJO: {f}")
    if fallos:
        return 2
    print("clearance_budget: VERDE")
    return 0


# Lo que este calculo NO cubre (y donde se cierra):
#   * rigidez/flexion del vano de 500 mm  -> cargar el prototipo (spec §11)
#   * par de apriete sobre acrilico       -> probeta del cupon (spec §11)
#   * termica de la fuente v2             -> spec PSU v2 y su validacion
#   * nesting de planchas en el stock     -> lienzo del Task 5, a ojo
#   * paneles inclinados (1.6 mm, PCB de aluminio de modulo) en solapes():
#     su ajuste lo resuelve la rotacion de railes (R3), no un AABB — un
#     rectangulo largo y fino en diagonal sobreestima demasiado con caja
#     alineada a ejes como para que el resultado signifique algo

if __name__ == "__main__":
    sys.exit(main())
