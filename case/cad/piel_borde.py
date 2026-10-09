"""EL BORDE DE LA PIEL: la cubierta se enrolla sobre el costado y la celosia
sale de debajo. Escribe piel_borde.json, que levanta imprimir_piel.py.

    python piel_borde.py              -> piel_borde.json
    python piel_borde.py --preview    -> renders/build/piel_borde.png

LA DECISION (ficha 7, A, firmada por Samuel el 2026-10-09 en la revision
"SAM17 de cerca"): la cubierta y el marco del cachete eran dos tubos uno al
lado del otro con un canal en medio; en el concepto la celosia nace del borde
de la cubierta. Asi que el marco del cachete deja de existir: el borde de la
cubierta se ENROLLA sobre el costado (el ROLLO) y el cachete queda como la
celosia mas una PESTANA escondida debajo de ese rollo. El borde engorda abajo
y adelgaza hacia arriba, como un tronco.

LO QUE OBLIGA LA FISICA. La cubierta se pone bajando desde arriba (el papel,
seccion 8). Un rollo por el canto de ABAJO del costado barreria la celosia al
bajar, asi que abajo el borde lo pone el cachete: una BASE con la misma
seccion que el rollo, apoyada en la tabla. El rollo baja hasta la tabla por
delante y por detras --sus dos patas-- y la base va entre ellas. Se encuentran
a INGLETE, como las esquinas de un marco de cuadro: en cada esquina de abajo,
la bisectriz del angulo, con una junta de HOLGURA. Es la unica junta que se
ve; en el resto del contorno va debajo del rollo. (La primera version cortaba
en horizontal a 36 mm y la base envolvia la esquina: dos juntas cruzadas en
cada esquina, render del 09-10.)

LA SECCION, en coordenadas locales de cada punto del contorno: u = distancia
al perfil del anillo (positiva hacia fuera), v = altura sobre la cara exterior
del anillo (z = ancho_total en el lado derecho).
  - por fuera del perfil (u de 0 a PIEL_E) la lamina de la cubierta llega
    hasta el costado y dobla con una esquina de radio R;
  - sobre el costado, el LABIO entra W hacia dentro, de v0 a T, y acaba en
    una NARIZ redonda de radio (T - v0) / 2;
  - debajo del labio, de v = 0 a PESTANA_T, va la pestana del cachete, y
    entre los dos HOLGURA (v0 = PESTANA_T + HOLGURA).
W cambia con la altura: W_ABAJO junto a la tabla, W_ARRIBA en la cumbre. T
puede cambiar igual (T_ABAJO/T_ARRIBA), pero hoy es constante: ver T_ABAJO.

COMO SE CONSTRUYE. Rebanadas en v de PASO_V: en cada una, la region entre el
perfil desplazado hacia dentro y hacia fuera lo que dice la seccion, armada
con tiras cortas a lo largo del contorno (cada una con su T y su W) y discos
en las esquinas, y unidas con shapely. imprimir_piel.py extruye cada rebanada
y las funde con el remallado: el escalon de PASO_V desaparece.
"""
import json
import math
import os
import re
import sys

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.join(DIR, "..") not in sys.path:
    sys.path.insert(0, os.path.join(DIR, ".."))
import clearance_budget as cb  # noqa: E402

SALIDA = os.path.join(DIR, "piel_borde.json")

T_ABAJO, T_ARRIBA = 12.0, 12.0  # mm, grueso del borde sobre la cara del anillo
                                # (11 era el marco del cachete que sustituye).
                                # CONSTANTE: con 13 abajo y 9.5 arriba la cara del
                                # costado salia apenas inclinada y el remallado
                                # por voxeles la hacia escalera -- rayas finas en
                                # todo el borde (render del 09-10). Lo que engorda
                                # abajo es W, que no deja rayas.
W_ABAJO, W_ARRIBA = 28.0, 21.0  # mm, cuanto entra el labio sobre el costado.
                                # Tapa la cara vista del anillo (20) siempre.
R_FRAC = 0.55                   # radio de la esquina de fuera, x T
PESTANA_T = 3.0                 # mm = el fondo de la placa (celosia_placa FONDO)
PESTANA_MAS = 4.0               # mm que la pestana sigue mas alla de W
HOLGURA = 0.6                   # mm: labio-pestana y la junta de las esquinas.
                                # Con 0.3 el remallado (medio voxel por pieza)
                                # la cerraba: salia -0.47 (09-10). MJF pide 0.3-0.5
                                # de juego para piezas que se montan.
SOLAPE_V = 2.0                  # mm que el rollo se mete en la lamina para fundirse
PASO_V = 0.12                   # mm entre rebanadas. Con 0.35 se veian rayas
                                # cada ~25 mm sobre el rollo: el grueso cambia con
                                # la altura y cada vez que cruzaba una rebanada
                                # dejaba un escalon de 0.35 (render del 09-10).
PASO_S = 2.5                    # mm de cada tira a lo largo del contorno
HUECOS_DESDE = 14.0             # mm: la celosia puede tener huecos desde aqui;
                                # entre esto y W quedan debajo del labio


def piel_e() -> float:
    with open(os.path.join(DIR, "piel_organica.scad"), encoding="utf-8") as f:
        m = re.search(r"^piel_e\s*=\s*([\d.]+)", f.read(), re.M)
    return float(m.group(1))


OPENSCAD = r"C:\Program Files\OpenSCAD\openscad.exe"
SVG = os.path.join(DIR, "..", "renders", "build", "piel", "perfil.svg")


def perfil_real() -> np.ndarray:
    """El contorno DE VERDAD del anillo: perfil_lateral() de sam17_case.scad,
    con la entasis de sus cantos y los radios de sus esquinas. El poligono de
    clearance_budget._vertices() es el recto, y el rollo hecho sobre el se
    metia en el aluminio hasta 4.1 mm en el escalon y 0.8 en las pendientes
    (check_piel.py, 2026-10-09). La lamina de la cubierta ya seguia este, y el
    borde tiene que seguir el mismo. Horario, como el recto."""
    fuentes = max(os.path.getmtime(os.path.join(DIR, f)) for f in
                  ("piel_organica.scad", "sam17_case.scad", "params.scad"))
    if not os.path.exists(SVG) or os.path.getmtime(SVG) < fuentes:
        import subprocess
        os.makedirs(os.path.dirname(SVG), exist_ok=True)
        r = subprocess.run([OPENSCAD, "-o", SVG, "-D", 'PART="perfil_2d"',
                            os.path.join(DIR, "piel_organica.scad")],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("OpenSCAD fallo exportando el perfil: " + r.stderr[-400:])
    with open(SVG, encoding="utf-8") as f:
        d = re.search(r'<path d="([^"]+)"', f.read()).group(1)
    pts = np.array([(float(x), -float(y)) for x, y in re.findall(r"([-\d.e]+),([-\d.e]+)", d)])
    if np.allclose(pts[0], pts[-1]):
        pts = pts[:-1]
    if Polygon(pts).exterior.is_ccw:
        pts = pts[::-1]
    return pts


def _suave(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def params_en(y: float, alto: float) -> tuple[float, float]:
    """(T, W) a la altura y: engorda abajo, adelgaza arriba."""
    s = _suave(y / alto)
    return T_ABAJO + (T_ARRIBA - T_ABAJO) * s, W_ABAJO + (W_ARRIBA - W_ABAJO) * s


def seccion(v: float, T: float, W: float, E: float, pieza: str):
    """(dentro, fuera) a la altura v: cuanto llega hacia dentro y hacia fuera
    del perfil. None si a esa altura no hay nada. `pieza`: 'rollo' o 'base'."""
    v0 = PESTANA_T + HOLGURA
    if v > T:
        return None
    R = min(R_FRAC * T, T - v0 - 0.5)
    fuera = E if v <= T - R else E - R + math.sqrt(max(R * R - (v - (T - R)) ** 2, 0.0))
    r = (T - v0) / 2.0
    if v >= v0:
        dentro = W - r + math.sqrt(max(r * r - (v - (v0 + r)) ** 2, 0.0))
    elif pieza == "rollo":
        dentro = 0.0                     # el hueco de la pestana
    elif v <= PESTANA_T:
        dentro = W + PESTANA_MAS         # la pestana, en la base
    else:
        dentro = W - r                   # sin rendija dentro de la base
    if pieza == "base" and v < 0:
        return None
    if pieza == "rollo" and v < 0:
        dentro = 0.0                     # solape con la lamina, solo por fuera
    return dentro, fuera


def _tangentes(P: np.ndarray):
    n = len(P)
    t = [(P[(i + 1) % n] - P[i]) / np.linalg.norm(P[(i + 1) % n] - P[i]) for i in range(n)]
    return t


def rebanada(P: np.ndarray, v: float, E: float, pieza: str):
    """La region de una rebanada, como union de tiras y esquinas."""
    alto = P[:, 1].max()
    perfil = Polygon(P)
    trozos = []
    n = len(P)
    tt = _tangentes(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        L = float(np.linalg.norm(b - a))
        k = max(1, int(math.ceil(L / PASO_S)))
        t = tt[i]
        nn = np.array([-t[1], t[0]])            # hacia fuera (perfil horario)
        for j in range(k):
            p0 = a + (b - a) * (j / k)
            p1 = a + (b - a) * ((j + 1) / k)
            T, W = params_en(float((p0[1] + p1[1]) / 2), alto)
            s = seccion(v, T, W, E, pieza)
            if s is None:
                continue
            dentro, fuera = s
            if fuera + dentro <= 1e-6:
                continue
            q = [p0 + nn * fuera, p1 + nn * fuera, p1 - nn * dentro, p0 - nn * dentro]
            trozos.append(Polygon(q).buffer(0.05))
    for i in range(n):
        p = P[i]
        t_in, t_out = tt[i - 1], tt[i]
        giro = t_in[0] * t_out[1] - t_in[1] * t_out[0]
        if abs(giro) < math.sin(math.radians(0.5)):
            continue                     # un tramo casi recto: las tiras ya se tocan
        convexa = giro < 0               # giro a la derecha
        T, W = params_en(float(p[1]), alto)
        s = seccion(v, T, W, E, pieza)
        if s is None:
            continue
        dentro, fuera = s
        if convexa and fuera > 0:
            trozos.append(Point(p).buffer(fuera, 48).difference(perfil))
        if not convexa and dentro > 0:
            sector = Point(p).buffer(dentro, 48)
            if fuera < 0:
                sector = sector.difference(Point(p).buffer(-fuera, 48))
            trozos.append(sector.intersection(perfil))
    if not trozos:
        return None
    region = unary_union(trozos)
    region = region.intersection(box(-100, 0.3, 500, 400))      # sobre la tabla
    base = zona_base(P)
    if pieza == "rollo":
        region = region.difference(base.buffer(HOLGURA / 2, join_style=2))
    else:
        region = region.intersection(base.buffer(-HOLGURA / 2, join_style=2))
    return region if not region.is_empty else None


def zona_base(P: np.ndarray) -> Polygon:
    """Lo que es de la BASE: lo que queda por debajo de las dos lineas de
    inglete. Cada una va de la esquina de fuera (abajo, en el perfil recto) a
    la esquina de DENTRO del borde, donde el labio de la base (a W_ABAJO de la
    tabla) se cruza con el del canto de al lado. Atras el canto es vertical y
    sale a 45 grados; delante la nariz mide 19 y enseguida empieza la
    pendiente, asi que el inglete sale mas tendido. (La primera version usaba
    la bisectriz de 45 grados en las dos y le daba a la base un trozo del
    escalon y del labio de la pendiente: preview del 09-10.)"""
    recto = np.array(cb._vertices(cb.leer_params()), dtype=float)
    x_del, x_atr = recto[:, 0].min(), recto[:, 0].max()
    W = W_ABAJO
    # el contorno recto sin el canto de abajo (y = 0)
    lados = [LineString([recto[i], recto[(i + 1) % len(recto)]]) for i in range(len(recto))
             if not (abs(recto[i][1]) < 1e-6 and abs(recto[(i + 1) % len(recto)][1]) < 1e-6)]
    otros = unary_union(lados)
    xs = np.arange(x_del, x_atr, 0.05)
    libres = [x for x in xs if otros.distance(Point(x, W)) >= W]
    x_in_del, x_in_atr = libres[0], libres[-1]
    k_del = W / (x_in_del - x_del)
    k_atr = W / (x_atr - x_in_atr)
    # el vertice de arriba: donde se cruzan las dos lineas
    xa = (k_atr * x_atr + k_del * x_del) / (k_del + k_atr)
    ya = k_del * (xa - x_del)
    return Polygon([(x_del - 60 / k_del, -60), (x_atr + 60 / k_atr, -60), (xa, ya)])


def _rejilla(v_ini: float) -> list[tuple[float, float]]:
    """Los cortes en v, con un borde EXACTO en las alturas que deciden una
    holgura: 0 (la cara del anillo), PESTANA_T (la cara de la pestana) y v0 (la
    de debajo del labio). Con un paso fijo desde -SOLAPE_V, la rebanada que
    cruzaba cada una se la quedaba entera y la holgura de 0.3 salia en 0.1
    (medido 09-10). Entre esas alturas, pasos iguales de como mucho PASO_V."""
    v0 = PESTANA_T + HOLGURA
    cortes = sorted({v_ini, 0.0, PESTANA_T, v0, T_ARRIBA, T_ABAJO})
    cortes = [c for c in cortes if c >= v_ini]
    out = []
    for a, b in zip(cortes, cortes[1:]):
        k = max(1, int(math.ceil((b - a) / PASO_V - 1e-9)))
        out += [(a + (b - a) * i / k, a + (b - a) * (i + 1) / k) for i in range(k)]
    return out


def _anillos(geom) -> list:
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    out = []
    for g in polys:
        if g.area < 0.5:
            continue
        out.append([np.round(np.asarray(g.exterior.coords)[:-1], 3).tolist()]
                   + [np.round(np.asarray(h.coords)[:-1], 3).tolist() for h in g.interiors])
    return out


def generar() -> dict:
    recto = np.array(cb._vertices(cb.leer_params()), dtype=float)
    P = perfil_real()
    E = piel_e()
    doc = dict(generado_por="piel_borde.py -- no editar a mano",
               params=dict(T_ABAJO=T_ABAJO, T_ARRIBA=T_ARRIBA, W_ABAJO=W_ABAJO,
                           W_ARRIBA=W_ARRIBA, R_FRAC=R_FRAC, PESTANA_T=PESTANA_T,
                           PESTANA_MAS=PESTANA_MAS, HOLGURA=HOLGURA,
                           SOLAPE_V=SOLAPE_V, PASO_V=PASO_V, PIEL_E=E,
                           HUECOS_DESDE=HUECOS_DESDE),
               perfil=recto.round(3).tolist(), perfil_real=P.round(3).tolist(),
               rollo=[], base=[])
    for pieza, v_ini in (("rollo", -SOLAPE_V), ("base", 0.0)):
        for v, v1 in _rejilla(v_ini):
            reg = rebanada(P, (v + v1) / 2, E, pieza)
            if reg is not None:
                reg = reg.simplify(0.02)
                doc[pieza].append(dict(v0=round(v, 3), v1=round(v1, 3), poligonos=_anillos(reg)))
    perfil = Polygon(P)
    doc["placa_exterior"] = _anillos(perfil.buffer(-HOLGURA, join_style=2))
    doc["huecos_dentro"] = _anillos(perfil.buffer(-HUECOS_DESDE, join_style=2))
    return doc


def _preview(doc: dict, ruta: str) -> None:
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(14, 6))
    P = np.array(doc["perfil_real"])
    for ax, pieza, color in ((axs[0], "rollo", "#e8913a"), (axs[0], "base", "#5aa0e0")):
        for reb in doc[pieza][:: max(1, len(doc[pieza]) // 6)]:
            for pol in reb["poligonos"]:
                ax.fill(*np.array(pol[0]).T, fc=color, alpha=0.18, ec=color, lw=0.6)
    axs[0].plot(*np.vstack([P, P[:1]]).T, "k-", lw=0.8)
    axs[0].set_aspect("equal")
    axs[0].set_title("rebanadas: rollo (naranja) y base (azul)")
    # la seccion en tres alturas
    alto = P[:, 1].max()
    for y, c in ((5, "#1f77b4"), (130, "#2ca02c"), (250, "#d62728")):
        T, W = params_en(y, alto)
        for pieza, ls in (("rollo", "-"), ("base", ":")):
            us, vs = [], []
            for v in np.arange(-SOLAPE_V, T + 1e-9, 0.1):
                s = seccion(v, T, W, doc["params"]["PIEL_E"], pieza)
                if s:
                    us += [-s[0], s[1]]
                    vs += [v, v]
            axs[1].plot(np.array(us)[0::2], vs[0::2], ls, c=c, lw=1)
            axs[1].plot(np.array(us)[1::2], vs[1::2], ls, c=c, lw=1, label=f"y={y} {pieza}")
    axs[1].axhline(0, c="k", lw=0.5)
    axs[1].axvline(0, c="k", lw=0.5)
    axs[1].set_aspect("equal")
    axs[1].legend(fontsize=7)
    axs[1].set_title("seccion: u (fuera +) contra v")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=110, bbox_inches="tight")


def main():
    doc = generar()
    print(f"  rollo: {len(doc['rollo'])} rebanadas, base: {len(doc['base'])} rebanadas")
    if "--preview" in sys.argv:
        ruta = os.path.join(DIR, "..", "renders", "build", "piel_borde.png")
        _preview(doc, ruta)
        print("  preview", os.path.abspath(ruta))
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, separators=(",", ":"))
        f.write("\n")
    print("  escrito", SALIDA, f"({os.path.getsize(SALIDA) // 1024} KB)")


if __name__ == "__main__":
    main()
