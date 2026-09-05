"""La celosia de las mejillas: celdas de Voronoi sobre el perfil del case.

    python case/cad/celosia.py            -> escribe celosia_celdas.scad

PROPUESTA (2026-09-05), no artefacto de fabricacion: lo lee piel_organica.scad
y nada mas. Ninguna puerta lo corre todavia.

Por que Voronoi y por que por guion. El concepto de Samuel (tres renders del
05-09) tiene las mejillas en una celosia organica, tipo hueso, que respira.
Dibujarla a mano no tiene sentido: lo que importa de ella son TRES numeros
--cuanto abre, cuanto nervio le queda y cuanto borde macizo la enmarca-- y
esos tres tienen que ser parametros, porque el primero es el que lee el modelo
termico (clearance_budget) y los otros dos los que lee la rigidez. Un dibujo
no tiene parametros; esto si.

Lo que sale:
  * celosia_celdas       las celdas como poligonos en coordenadas del perfil
                         (x = fondo, y = alto, mm), CONVEXAS -- son celdas de
                         Voronoi y una transformacion afin conserva la
                         convexidad. piel_organica.scad las encoge
                         celosia_nervio/2 y les redondea las esquinas.
  * celosia_abierto_mm2  el area abierta POR MEJILLA, ya con el nervio
                         descontado, medida por muestreo (200k puntos). Es el
                         numero que va al modelo termico. Las esquinas
                         redondeadas del .scad quitan un poco mas (<2 %): se
                         declara, no se corrige.
  * celosia_abierto      la misma cifra como fraccion del area del perfil.

La anisotropia (ANISO) estira las celdas en vertical antes de calcular el
Voronoi y las devuelve despues: celdas mas altas que anchas, como en el
concepto. Las semillas fantasma fuera del perfil cierran las celdas del borde
(sin ellas, las regiones de la orilla son infinitas y scipy las descarta).
"""
from __future__ import annotations

import os
import sys

import numpy as np
from scipy.spatial import Voronoi, cKDTree

DIR = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(DIR, "..")
if CASE not in sys.path:
    sys.path.insert(0, CASE)
import clearance_budget as cb  # noqa: E402

# --- los parametros de la celosia ---------------------------------------
CELDA = 22.0        # mm, paso medio entre semillas (antes de estirar). Fue 26
                    # en el primer render (05-09): celdas grandes respecto al
                    # case; el concepto las tiene mas finas y mas altas
ANISO = 1.8         # estiramiento vertical de las celdas (fue 1.5)
JITTER = 0.42       # fraccion del paso: 0 = reticula, 0.5 = casi aleatorio
NERVIO = 3.5        # mm, ancho del nervio entre celdas (fue 4.0)
REDONDEO = 3.0      # mm, radio de las esquinas de cada celda
BORDE = 12.0        # mm, marco macizo alrededor de la celosia (medido desde
                    # el perfil; la piel anade su espesor por fuera)
SEMILLA = 17        # el generador es determinista: mismo numero, misma celosia
SALIDA = os.path.join(DIR, "celosia_celdas.scad")


def _dentro(P: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Ray casting vectorizado: True donde pts cae dentro del poligono P."""
    x, y = pts[:, 0], pts[:, 1]
    dentro = np.zeros(len(pts), dtype=bool)
    n = len(P)
    for i in range(n):
        x0, y0 = P[i]
        x1, y1 = P[(i + 1) % n]
        cruza = (y0 > y) != (y1 > y)
        xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0 + 1e-12)
        dentro ^= cruza & (x < xi)
    return dentro


def _dist_borde(P: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Distancia de cada punto al segmento mas cercano del poligono."""
    d = np.full(len(pts), np.inf)
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        ab = b - a
        t = np.clip(((pts - a) @ ab) / (ab @ ab), 0.0, 1.0)
        proy = a + t[:, None] * ab
        d = np.minimum(d, np.linalg.norm(pts - proy, axis=1))
    return d


def _ccw(c: np.ndarray) -> np.ndarray:
    """Orienta un poligono convexo en sentido antihorario."""
    area = 0.5 * np.sum(c[:, 0] * np.roll(c[:, 1], -1) - np.roll(c[:, 0], -1) * c[:, 1])
    return c if area > 0 else c[::-1]


def generar(celda=CELDA, aniso=ANISO, jitter=JITTER, nervio=NERVIO,
            borde=BORDE, semilla=SEMILLA):
    p = cb.leer_params()
    P = np.array(cb._vertices(p), dtype=float)
    rng = np.random.default_rng(semilla)

    # semillas: reticula con jitter, en el espacio ESTIRADO (y / aniso)
    x0, x1 = P[:, 0].min(), P[:, 0].max()
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    xs = np.arange(x0 - 2 * celda, x1 + 3 * celda, celda)
    ys = np.arange(y0 / aniso - 2 * celda, y1 / aniso + 3 * celda, celda)
    gx, gy = np.meshgrid(xs, ys)
    semillas_e = np.stack([gx.ravel(), gy.ravel()], axis=1)
    semillas_e += rng.uniform(-jitter, jitter, semillas_e.shape) * celda
    semillas = semillas_e * [1.0, aniso]                # de vuelta al mundo

    # las celdas que cuentan: semilla dentro del perfil. Las de fuera se
    # quedan como fantasmas para cerrar las del borde.
    vivas = _dentro(P, semillas)
    vor = Voronoi(semillas_e)
    celdas = []
    for i in np.flatnonzero(vivas):
        reg = vor.regions[vor.point_region[i]]
        if not reg or -1 in reg:
            continue
        c = vor.vertices[reg] * [1.0, aniso]
        celdas.append(_ccw(c))

    # --- el area abierta, por muestreo ---------------------------------
    # DOS areas y no una. La celosia abre desde `borde` hacia dentro, que es
    # lo que se VE. Pero detras de la mejilla esta el anillo (cara_anillo de
    # cara) y el marco de la ventana (hasta marco_fondo del perfil), y las
    # celdas que caen sobre ese metal no respiran: ensenan aluminio. Lo que
    # respira es lo abierto SOBRE LA VENTANA del anillo, y ese es el numero
    # que va al modelo termico. marco_fondo_trasera es 30 y no 26: se usa 26
    # en todo el contorno, 4 mm optimista en el tramo trasero. Declarado.
    ventana = float(p.get("marco_fondo", 26.0))
    N = 200_000
    muestra = np.stack([rng.uniform(x0, x1, N), rng.uniform(y0, y1, N)], axis=1)
    en_perfil = _dentro(P, muestra)
    dist = _dist_borde(P, muestra)
    area_perfil = 0.5 * abs(np.sum(P[:, 0] * np.roll(P[:, 1], -1)
                                   - np.roll(P[:, 0], -1) * P[:, 1]))
    area_bbox = (x1 - x0) * (y1 - y0)
    pts = muestra[en_perfil]
    # a que celda pertenece cada punto: la semilla mas cercana EN EL ESPACIO
    # ESTIRADO, que es donde se calculo el Voronoi
    arbol = cKDTree(semillas_e)
    _, idx = arbol.query(pts * [1.0, 1.0 / aniso])
    abierto = np.zeros(len(pts), dtype=bool)
    # mapa semilla viva -> celda emitida (mismo orden que `celdas`)
    indice = {}
    k = 0
    for i in np.flatnonzero(vivas):
        reg = vor.regions[vor.point_region[i]]
        if not reg or -1 in reg:
            continue
        indice[int(i)] = k
        k += 1
    for i_sem in np.unique(idx):
        if int(i_sem) not in indice:
            continue
        c = celdas[indice[int(i_sem)]]
        sel = np.flatnonzero(idx == i_sem)
        q = pts[sel]
        ok = np.ones(len(q), dtype=bool)
        n = len(c)
        for j in range(n):                       # convexa y CCW: dentro si
            a, b = c[j], c[(j + 1) % n]          # queda a la izquierda de
            e = b - a                            # cada arista a >= nervio/2
            L = np.hypot(*e)
            s = (e[0] * (q[:, 1] - a[1]) - e[1] * (q[:, 0] - a[0])) / L
            ok &= s >= nervio / 2
        abierto[sel] = ok
    # mascaras sobre la muestra ENTERA, para que todas las areas salgan de la
    # misma regla de tres contra el bbox
    ab_full = np.zeros(N, dtype=bool)
    ab_full[np.flatnonzero(en_perfil)] = abierto
    area = lambda m: m.mean() * area_bbox  # noqa: E731
    area_region = area(en_perfil & (dist >= borde))
    area_abierta = area(en_perfil & (dist >= borde) & ab_full)
    area_ventana = area(en_perfil & (dist >= ventana) & ab_full)
    return dict(celdas=celdas, area_perfil=area_perfil, area_region=area_region,
                area_abierta=area_abierta, abierto=area_abierta / area_perfil,
                area_ventana=area_ventana, ventana=ventana,
                nervio=nervio, borde=borde)


def escribir(r: dict, ruta: str = SALIDA) -> None:
    lineas = ["// GENERADO por celosia.py -- no editar a mano. Parametros y",
              "// medida del area abierta al pie.",
              "celosia_celdas = ["]
    for c in r["celdas"]:
        lineas.append("  [" + ", ".join(f"[{x:.2f},{y:.2f}]" for x, y in c) + "],")
    lineas += ["];",
               f"celosia_nervio = {r['nervio']};",
               f"celosia_redondeo = {REDONDEO};",
               f"celosia_borde = {r['borde']};",
               f"celosia_n = {len(r['celdas'])};",
               f"celosia_abierto_mm2 = {r['area_abierta']:.0f};   // por mejilla, nervio descontado: lo que se VE",
               f"celosia_abierto = {r['abierto']:.3f};         // fraccion del perfil ({r['area_perfil']:.0f} mm2)",
               f"celosia_abierto_ventana_mm2 = {r['area_ventana']:.0f};   // por mejilla, SOLO sobre la ventana del",
               f"                                     // anillo (a >= {r['ventana']:.0f} del perfil): lo que RESPIRA",
               ""]
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas))


if __name__ == "__main__":
    r = generar()
    escribir(r)
    print(f"celosia: {len(r['celdas'])} celdas, nervio {r['nervio']} mm, borde {r['borde']} mm")
    print(f"  perfil {r['area_perfil']:.0f} mm2 | region de celosia {r['area_region']:.0f} mm2")
    print(f"  ABIERTO por mejilla: {r['area_abierta']:.0f} mm2 = {100*r['abierto']:.1f} % del perfil (lo que se ve)")
    print(f"  y de eso RESPIRA {r['area_ventana']:.0f} mm2: lo que cae sobre la ventana del anillo "
          f"(a >= {r['ventana']:.0f} mm del perfil); el resto ensena aluminio")
    print(f"  escrito {SALIDA}")
