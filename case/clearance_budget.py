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
    """7 centros de larguero de esqueleto, misma formula que
    centros_esqueleto() en sam17_case.scad (entrepiso delantero reubicado,
    ambos railes de entrepiso a la altura nueva, repisa — ronda de
    revision 2, R6: piel_superior se reancla aqui en vez de en entrepiso
    trasero, que vive en el plano del piso inferior y no del superior — y
    zocalo superior, ronda final: la fila de arriba del zocalo anclaba a un
    rail de PANEL, que va rotado)."""
    r = p["rail"] / 2
    x_ed = cr[2][0] + p["rail"] + p["holgura_rail"]
    y_ep = P[3][1] - p["t_acrilico"] - r
    # semiextension en X del rail de panel cara-inferior TRAS la rotacion R3
    # (cuadrado girado: r*(|cos|+|sin|)); el rail del zocalo se planta
    # holgura_rail por detras de esa esquina, que es lo mas adelante que
    # cabe sin invadirlo.
    he_ci = r * (abs(math.cos(math.radians(p["angulo_inferior"])))
                  + abs(math.sin(math.radians(p["angulo_inferior"]))))
    x_zs = cr[0][0] + he_ci + p["holgura_rail"] + r
    return [(r + 2, r), (p["prof_inferior"] - r, r),
            (x_ed, y_ep), (p["prof_inferior"] - r, y_ep),
            (p["prof_superior"] - r, P[5][1] - r),
            (p["prof_superior"] - r, P[3][1] + 15),
            (x_zs, p["alto_frontal"] - 15)]


NOMBRES_CR = ["cara_inf s=inset", "cara_inf s=alto-inset",
              "cara_sup s=inset", "cara_sup s=alto-inset"]
NOMBRES_CE = ["base delantera", "base trasera", "entrepiso delantero",
              "entrepiso trasero", "remate superior", "repisa",
              "zocalo superior"]


# Caja = (nombre, x0, x1, y0, y1, z0, z1)
Caja = tuple
# Fila de agujeros de una placa = (placa, fila, eje, coordenada en ese eje,
# rail frontera al que DEBE anclar). El eje es el que recorre la placa de un
# rail frontera al otro: X en las bandejas (horizontales), Y en el zocalo y
# las pieles (verticales). El rail va declarado, no se busca el mas cercano:
# una fila que cae por casualidad en la centerline de otro rail no esta
# anclada donde el diseno dice, y ese acierto casual no debe pasar la puerta.
Fila = tuple


def _cajas_solidas(p: dict[str, float]) -> tuple[list[Caja], list[Caja],
                                                  list[Fila]]:
    """AABB de los 11 railes y de las 5 planchas/pieles, misma formula que
    rails()/planchas_acrilico() en sam17_case.scad, mas las 10 filas de
    agujeros de las placas (las mismas expresiones que dimensionan la caja,
    para que un cambio de placa arrastre su fila y no se puedan separar)."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ce = _centros_esqueleto(p, P, cr)
    rail, t_cheek = p["rail"], p["t_cheek"]
    t_acr, gap = p["t_acrilico"], p["gap_sombra"]
    ancho_total = p["ancho_total"]

    angs = [p["angulo_inferior"], p["angulo_inferior"],
            p["angulo_superior"], p["angulo_superior"]]
    railes: list[Caja] = []
    for nm, c, ang in zip(NOMBRES_CR, cr, angs):
        # R3: el rail gira -ang sobre su eje largo para calzar a ras de la
        # cara. El AABB real de un cuadrado girado crece a
        # (rail/2)*(|cos|+|sin|) — usar rail/2 sin mas SUBESTIMA el alcance
        # de la esquina (0.261 mm de error verificado en la ronda de
        # revision: rail/2*(|n.x|+|n.y|)=11.861 > off=11.6).
        he = (rail / 2) * (abs(math.cos(math.radians(ang)))
                            + abs(math.sin(math.radians(ang))))
        railes.append((nm, c[0] - he, c[0] + he, c[1] - he, c[1] + he,
                       t_cheek, ancho_total - t_cheek))
    for nm, c in zip(NOMBRES_CE, ce):
        railes.append((nm, c[0] - rail / 2, c[0] + rail / 2,
                       c[1] - rail / 2, c[1] + rail / 2,
                       t_cheek, ancho_total - t_cheek))

    planchas: list[Caja] = []
    filas: list[Fila] = []
    # bandeja_base: ronda final — fondo y colocacion derivados de sus DOS
    # railes frontera (antes: plancha de prof_inferior-2*rail-4 puesta en
    # x=rail, filas a +18 y -24 mm de las centerlines y canto trasero a
    # 4 mm de tocar el rail; la bandeja que carga el PSU no apoyaba atras).
    x0_bb = ce[0][0] - rail / 2
    fondo_bb = ce[1][0] + rail / 2 - x0_bb
    y0_bb = ce[0][1] + rail / 2          # apoya en el lomo del rail
    planchas.append(("bandeja_base", x0_bb, x0_bb + fondo_bb,
                     y0_bb, y0_bb + t_acr, t_cheek, ancho_total - t_cheek))
    filas += [("bandeja_base", "delantera", "x", x0_bb + rail / 2,
               "base delantera"),
              ("bandeja_base", "trasera", "x", x0_bb + fondo_bb - rail / 2,
               "base trasera")]
    # bandeja_entrepiso: R2 — canto trasero a ras de entrepiso-trasero,
    # tope (no fondo) a ras de P3.y
    x0_be = ce[2][0] - rail / 2
    fondo_be = p["prof_inferior"] - ce[2][0] + rail / 2
    planchas.append(("bandeja_entrepiso", x0_be, x0_be + fondo_be,
                     P[3][1] - t_acr, P[3][1], t_cheek, ancho_total - t_cheek))
    filas += [("bandeja_entrepiso", "delantera", "x", x0_be + rail / 2,
               "entrepiso delantero"),
              ("bandeja_entrepiso", "trasera", "x", x0_be + fondo_be - rail / 2,
               "entrepiso trasero")]
    # zocalo: R1 — volado hacia -X (standoffs), ya no bolonado directo.
    # Ronda final: fila superior anclada al rail de esqueleto "zocalo
    # superior" (ce[6]) en vez del rail de PANEL cara_inf s=inset, que R3
    # gira 12 grados.
    alto_zoc = ce[6][1] - ce[0][1] + 30
    y0_zoc = ce[0][1] - 15
    planchas.append(("zocalo", -gap - t_acr, -gap, y0_zoc, y0_zoc + alto_zoc,
                     t_cheek + gap, ancho_total - t_cheek - gap))
    filas += [("zocalo", "inferior", "y", y0_zoc + 15, "base delantera"),
              ("zocalo", "superior", "y", y0_zoc + alto_zoc - 15,
               "zocalo superior")]
    # piel_inferior: R1 — volada hacia +X mas alla de prof_inferior
    alto_pi = ce[3][1] - ce[1][1] + 30
    y0_pi = ce[1][1] - 15
    planchas.append(("piel_inferior", P[8][0] + gap, P[8][0] + gap + t_acr,
                     y0_pi, y0_pi + alto_pi, t_cheek + gap, ancho_total - t_cheek - gap))
    filas += [("piel_inferior", "inferior", "y", y0_pi + 15, "base trasera"),
              ("piel_inferior", "superior", "y", y0_pi + alto_pi - 15,
               "entrepiso trasero")]
    # piel_superior: R1 — volada hacia +X mas alla de prof_superior;
    # re-anclada a la repisa (ce[5]) en vez de entrepiso trasero (R6)
    alto_ps = ce[4][1] - ce[5][1] + 30
    y0_ps = ce[5][1] - 15
    planchas.append(("piel_superior", P[6][0] + gap, P[6][0] + gap + t_acr,
                     y0_ps, y0_ps + alto_ps, t_cheek + gap, ancho_total - t_cheek - gap))
    filas += [("piel_superior", "inferior", "y", y0_ps + 15, "repisa"),
              ("piel_superior", "superior", "y", y0_ps + alto_ps - 15,
               "remate superior")]
    return railes, planchas, filas


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


# Tolerancia de alineacion placa<->rail. La coincidencia es una IDENTIDAD
# (la fila sale de la centerline del rail), asi que lo correcto es 0.00 y
# esto solo absorbe ruido de coma flotante. Referencia fisica: la holgura
# del agujero de paso M4 sobre el tornillo es 0.5 mm de diametro, o sea
# 0.25 mm de radio — un desvio de 0.05 ya es 1/5 de eso, y cualquier error
# de diseno real (milimetros, como el +18/-24 de la bandeja base) cae en
# rojo con muchisimo margen.
TOL_ALINEACION = 0.05


def _desvio(coord: float, eje: str, centro: tuple[float, float]) -> float:
    """Desvio FIRMADO de una fila respecto a una centerline de rail, sobre
    el eje que recorre la placa."""
    return coord - centro[0 if eje == "x" else 1]


def _mas_cercano(coord: float, eje: str,
                  candidatos: list[tuple[str, tuple[float, float]]]
                  ) -> tuple[float, str]:
    """Rail mas cercano de la lista (solo para el mensaje de diagnostico:
    el criterio es el rail DECLARADO, no este)."""
    return min(((_desvio(coord, eje, c), nm) for nm, c in candidatos),
               key=lambda t: abs(t[0]))


def alineacion(p: dict[str, float]) -> list[str]:
    """ANCLAJE: cada fila de agujeros de cada placa cae en la centerline de
    un rail del ESQUELETO (sin rotar).

    Por que existe: solapes() verifica DISYUNCION, y una placa flotando en
    el aire es perfectamente disjunta — nadie verificaba que las placas
    apoyaran en algo. Dos formas de fallar, las dos en rojo:

      (a) la fila no coincide con ningun rail: la placa se atornilla al
          aire. Es el defecto de bandeja_base de la ronda final (filas a
          +18.00 y -24.00 mm de sus railes, canto trasero flotando 4 mm
          sobre una bandeja que carga el transformador del PSU).
      (b) la fila coincide con un rail de PANEL: R3 los gira al angulo de
          su cara (12/35 grados), asi que el tornillo entraria en diagonal
          respecto al eje del agujero (~1.05 mm de descentre en 5 mm de
          acrilico contra 0.7-0.9 de holgura) y la arandela asentaria de
          canto — carga de borde sobre acrilico fragil. Las placas anclan
          UNICAMENTE a railes de esqueleto; los de panel estan rotados
          porque sirven a los paneles, no son superficie de anclaje.
    """
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ce = _centros_esqueleto(p, P, cr)
    esqueleto = dict(zip(NOMBRES_CE, ce))
    panel = dict(zip(NOMBRES_CR, cr))
    _, _, filas = _cajas_solidas(p)
    fallos: list[str] = []
    peor = 0.0
    for placa, fila, eje, coord, rail_decl in filas:
        if rail_decl in panel:
            d = _desvio(coord, eje, panel[rail_decl])
            fallos.append(
                f"anclaje [{placa}] fila {fila} ({eje}={coord:.2f}): declara "
                f"anclar al rail de PANEL '{rail_decl}' (desvio {d:+.2f} mm), y "
                f"esos van ROTADOS al angulo de su cara — las placas anclan "
                f"solo a railes de esqueleto")
            continue
        assert rail_decl in esqueleto, (
            f"fila [{placa}/{fila}] declara el rail '{rail_decl}', que no "
            f"existe ni en el esqueleto ni en los railes de panel")
        d = _desvio(coord, eje, esqueleto[rail_decl])
        peor = max(peor, abs(d))
        if abs(d) > TOL_ALINEACION:
            d_cerca, nm_cerca = _mas_cercano(coord, eje, list(esqueleto.items()))
            fallos.append(
                f"anclaje [{placa}] fila {fila} ({eje}={coord:.2f}): {d:+.2f} mm "
                f"de la centerline de '{rail_decl}' (tolerancia "
                f"{TOL_ALINEACION:.2f} mm) — la placa no apoya donde dice; el "
                f"rail mas cercano es '{nm_cerca}' a {d_cerca:+.2f} mm")
    print(f"alineacion: {len(filas)} filas de agujeros revisadas, desvio "
          f"maximo {peor:.2f} mm (tolerancia {TOL_ALINEACION:.2f})")
    return fallos


def canario_alineacion(p: dict[str, float]) -> None:
    """Autocomprobacion roja de alineacion(): alimenta las filas de la
    bandeja_base PRE-FIX (plancha de prof_inferior-2*rail-4 colocada en
    x=rail, ronda final) y exige que el checker las rechace con los desvios
    conocidos. Si esto no dispara, el checker esta ciego y su VERDE no vale
    nada. Los desvios esperados salen del algebra, no de una medicion:
    fila delantera = (rail + rail/2) - (rail/2 + 2) = rail - 2;
    fila trasera = (prof_inferior - 1.5*rail - 4) - (prof_inferior - rail/2)
                 = -(rail + 4)."""
    P = _vertices(p)
    ce = _centros_esqueleto(p, P, _centros_rail(p, P))
    esqueleto = dict(zip(NOMBRES_CE, ce))
    rail = p["rail"]
    fondo_viejo = p["prof_inferior"] - 2 * rail - 4      # fondo pre-fix
    casos = ((rail + rail / 2, "base delantera", rail - 2),
             (rail + fondo_viejo - rail / 2, "base trasera", -(rail + 4)))
    for coord, rail_decl, esperado in casos:
        d = _desvio(coord, "x", esqueleto[rail_decl])
        assert abs(d) > TOL_ALINEACION and abs(d - esperado) < 0.01, (
            f"canario de alineacion no disparo: la fila pre-fix en x={coord} "
            f"sale a {d:+.3f} mm de '{rail_decl}' (se esperaba {esperado:+.2f}) "
            f"y la tolerancia vigente es {TOL_ALINEACION} mm — no confiar en "
            f"el VERDE de alineacion()")


def solapes(p: dict[str, float]) -> list[str]:
    """11 railes + 5 planchas/pieles: ningun par se pisa en 3D, salvo los
    TOLERADOS de arriba (impresos igual, nunca silenciados) — vacio ahora
    mismo. Paneles inclinados (1.6 mm, PCB de aluminio de cada modulo): su
    clase la resuelve la rotacion de railes (R3), no entran en esta caja."""
    railes, planchas, _ = _cajas_solidas(p)
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
    canario_alineacion(p)
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
    fallos.extend(alineacion(p))

    print(f"perfil: alto_total={g['alto_total']:.1f}  "
          f"entrepiso={g['y_entrepiso']:.1f}  ancho_util={g['ancho_util']:.0f}")
    print(f"kerf aplicado: {p['kerf']:+.2f} mm (firmado; cupon manda)")
    print("  se espera NEGATIVO: el laser ENSANCHA y el modelo dibuja "
          "`d + kerf`, o sea que kerf compensa RESTANDO (README paso 2).")
    if p["kerf"] > 0:
        print(f"AMARILLO: kerf {p['kerf']:+.2f} es POSITIVO — los agujeros "
              f"saldrian {2 * p['kerf']:.2f} mm sobre el nominal. Un kerf de "
              f"tabla de servicio (ancho de canal, siempre positivo) entra "
              f"aqui con el signo cambiado.")
    exige(-0.5 <= p["kerf"] <= 0.5,
          "kerf fuera de rango fisico [-0.5, +0.5] mm")
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
#   * largo de standoff / distancia perpendicular placa<->rail: alineacion()
#     verifica que la fila caiga en la centerline de un rail de esqueleto,
#     no cuanto hay entre la placa y ese rail — en las piezas voladas esa
#     distancia ES el largo del standoff (dato de compra del BOM, no una
#     holgura): 7 mm el par inferior del zocalo, ~33 el superior, 5 las
#     pieles. Se cierra midiendo los standoffs contra el modelo al comprar
#   * paneles inclinados (1.6 mm, PCB de aluminio de modulo) en solapes():
#     su ajuste lo resuelve la rotacion de railes (R3), no un AABB — un
#     rectangulo largo y fino en diagonal sobreestima demasiado con caja
#     alineada a ejes como para que el resultado signifique algo

if __name__ == "__main__":
    sys.exit(main())
