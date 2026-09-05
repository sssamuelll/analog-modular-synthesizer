"""La celosia de los cachetes: FIBRAS de un campo de flujo, con lentes.

    python case/cad/celosia.py            -> escribe celosia_nervios.scad
    python case/cad/celosia.py --preview  -> y ademas build/celosia.png

PROPUESTA (2026-09-05): lo lee piel_organica.scad. Ninguna puerta lo corre.

TRES VERSIONES EN UN DIA, y las tres por mirar el render con Samuel:
  1. celdas de Voronoi (2bce743): parametrico, medible, LEIA A PANAL.
  2. ramas por colonizacion de espacio (d78c592): "parece modernista y
     parecen ramas de arbol". Salio un arbol: ramas sueltas que se cruzan.
     "no esta ni cerca".
  3. esta. La referencia (cuarto render de Samuel, el despiece) son FIBRAS:
     nervios largos que nacen del rincon de abajo-delante, se abanican hacia
     arriba-atras, se parten y se vuelven a juntar dejando huecos en forma
     de LENTE, escalonados como ladrillos en hiladas. Eso no es un arbol ni
     un teselado: es un CAMPO DE FLUJO. Y se genera como tal:

  * un campo de direcciones sobre el perfil: abanico desde un foco por
    delante y por debajo del case, con ondulacion suave para que las fibras
    se curven (Art Nouveau, no reticula);
  * lineas de flujo espaciadas (Jobard & Lefer 1997): se integra una
    fibra por el campo, se siembran vecinas a `SEPARACION` a cada lado, y
    una fibra muere cuando se acerca a otra. Donde el abanico se abre nacen
    fibras nuevas entre las viejas; donde se cierra, mueren. Es el
    "partirse y juntarse" de la referencia, y sale solo;
  * PUENTES entre fibras vecinas cada `LENTE` mm, escalonados de hilada en
    hilada, como curvas en S tangentes al flujo: cierran los huecos en
    lentes y son lo que atiranta la celosia (fibras paralelas solas no
    aguantan nada de traves);
  * y toda punta que muere se SUELDA a la fibra vecina: ninguna queda
    suelta.

Lo que sale: segmentos [x0, y0, x1, y1, w] en coordenadas del perfil, que
piel_organica.scad dibuja como capsulas y suelda con un cierre morfologico;
y las dos areas de siempre, lo que se ve y lo que respira (solo sobre la
ventana del anillo: detras de la orilla hay 26 mm de aluminio).
Determinista: misma semilla, mismas fibras.

Los numeros de la referencia, medidos sobre la imagen a ojo (la vista es en
perspectiva; son proporciones, no cotas): nervio ~1/60 del alto del cachete,
separacion entre fibras ~1/16, lentes de 3 a 6 separaciones de largo, marco
~1/15. Sobre 256 mm de alto: nervio ~4, separacion ~15, lentes 50-90, marco
~17. Son los valores de arranque de abajo.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

DIR = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(DIR, "..")
if CASE not in sys.path:
    sys.path.insert(0, CASE)
import clearance_budget as cb  # noqa: E402

# --- los parametros de la celosia ---------------------------------------
MARCO = 17.0        # mm, marco macizo alrededor de la celosia, desde el perfil
SEPARACION = 13.0   # mm, entre ejes de fibras vecinas
NERVIO = 4.2        # mm, grosor de la fibra
LENTE = 110.0       # mm, entre puentes: los puentes atirantan donde dos fibras
                    # corren paralelas mucho rato; las lentes las hace el campo
LENTE_JITTER = 0.35 # fraccion: las hiladas no van a compas
PASO = 2.0          # mm, paso de integracion
FOCO = (-140.0, -160.0) # de donde sale el abanico: delante y debajo del case,
                    # LEJOS: cerca (-40,-70) el abanico abria tanto que abajo
                    # las fibras eran rendijas y arriba huecos anchos
ONDA_A = 11.0       # grados, amplitud de la ondulacion de las fibras
ONDA_L = (150.0, 110.0) # mm, longitudes de onda (en y, en x)
GIRO_ARRIBA = 14.0  # grados: las fibras se enderezan hacia arriba al subir
# LAS LENTES CON PUNTA no salen de peldanos: salen de fibras vecinas que
# CONVERGEN y luego se SEPARAN. Se modula la direccion con el producto de una
# onda a lo largo del flujo (periodo LENTE_L) por otra a traves de el (periodo
# 2 x SEPARACION): fibras contiguas giran en sentidos opuestos, se acercan
# hasta que una muere soldada en la otra, y mas adelante nace otra entre las
# dos. Es el partirse y juntarse de la referencia.
LENTE_MOD = 11.0    # grados, amplitud de esa modulacion (7 daba lentes timidas)
LENTE_L = 80.0      # mm, periodo a lo largo del flujo
FLUJO_MEDIO = 50.0  # grados, direccion media del flujo para las coordenadas (s, t)
CIERRE = 2.0        # mm, radio del cierre que suelda horquillas (.scad)
SEMILLA = 17
SALIDA = os.path.join(DIR, "celosia_nervios.scad")


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


def _dist_segmentos(pts: np.ndarray, S: np.ndarray) -> np.ndarray:
    """Distancia de cada punto (N) a cada segmento (M): matriz N x M."""
    A, B = S[:, 0:2], S[:, 2:4]
    AB = B - A
    L2 = np.maximum((AB * AB).sum(axis=1), 1e-9)
    out = np.empty((len(pts), len(S)))
    for j in range(len(S)):
        t = np.clip(((pts - A[j]) @ AB[j]) / L2[j], 0.0, 1.0)
        proy = A[j] + t[:, None] * AB[j]
        out[:, j] = np.linalg.norm(pts - proy, axis=1)
    return out


class _Rejilla:
    """Puntos de todas las fibras en celdas de `d`, para preguntar rapido
    'hay algo de OTRA fibra a menos de r de aqui'."""

    def __init__(self, d: float):
        self.d = d
        self.celdas: dict[tuple[int, int], list[tuple[int, np.ndarray]]] = {}

    def _k(self, p):
        return (int(math.floor(p[0] / self.d)), int(math.floor(p[1] / self.d)))

    def mete(self, i: int, p: np.ndarray) -> None:
        self.celdas.setdefault(self._k(p), []).append((i, p))

    def cerca(self, p: np.ndarray, r: float, salvo: int = -1):
        """(distancia, fibra, punto) del mas cercano de otra fibra a < r."""
        kx, ky = self._k(p)
        n = int(math.ceil(r / self.d))
        mejor = (r, -1, None)
        for dx in range(-n, n + 1):
            for dy in range(-n, n + 1):
                for i, q in self.celdas.get((kx + dx, ky + dy), ()):
                    if i == salvo:
                        continue
                    dd = float(np.hypot(*(q - p)))
                    if dd < mejor[0]:
                        mejor = (dd, i, q)
        return mejor


def _campo(p: np.ndarray, H: float) -> np.ndarray:
    """Direccion unitaria del flujo en p: abanico desde FOCO, ondulado, y
    enderezandose hacia arriba con la altura."""
    v = p - np.array(FOCO)
    ang = math.atan2(v[1], v[0])
    ang += math.radians(ONDA_A) * (math.sin(2 * math.pi * p[1] / ONDA_L[0] + 0.6)
                                   + 0.6 * math.sin(2 * math.pi * p[0] / ONDA_L[1] + 2.1))
    ang += math.radians(GIRO_ARRIBA) * (p[1] / H)
    # la modulacion de las lentes, en coordenadas (s a lo largo, t a traves)
    a = math.radians(FLUJO_MEDIO)
    s = p[0] * math.cos(a) + p[1] * math.sin(a)
    t = -p[0] * math.sin(a) + p[1] * math.cos(a)
    ang += math.radians(LENTE_MOD) * (math.sin(2 * math.pi * s / LENTE_L)
                                      * math.sin(math.pi * t / SEPARACION))
    return np.array([math.cos(ang), math.sin(ang)])


def _bezier(A, TA, B, TB, n=8):
    """Curva en S de A a B, tangente a TA al salir y a TB al llegar."""
    k = 0.4 * float(np.hypot(*(B - A)))
    C1, C2 = A + TA * k, B - TB * k
    t = np.linspace(0.0, 1.0, n)[:, None]
    return ((1 - t) ** 3 * A + 3 * (1 - t) ** 2 * t * C1
            + 3 * (1 - t) * t ** 2 * C2 + t ** 3 * B)


def generar(marco=MARCO, sep=SEPARACION, w=NERVIO, lente=LENTE,
            lente_jitter=LENTE_JITTER, paso=PASO, semilla=SEMILLA):
    p = cb.leer_params()
    P = np.array(cb._vertices(p), dtype=float)
    rng = np.random.default_rng(semilla)
    x0, x1 = P[:, 0].min(), P[:, 0].max()
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    H = y1 - y0
    area_bbox = (x1 - x0) * (y1 - y0)
    area_perfil = 0.5 * abs(np.sum(P[:, 0] * np.roll(P[:, 1], -1)
                                   - np.roll(P[:, 0], -1) * P[:, 1]))

    def en_region(q):
        qq = np.asarray(q, dtype=float)[None, :]
        return bool(_dentro(P, qq)[0] and _dist_borde(P, qq)[0] >= marco)

    # --- las fibras: lineas de flujo espaciadas -----------------------------
    rej = _Rejilla(sep)
    fibras: list[np.ndarray] = []
    d_muere = 0.55 * sep          # una fibra muere al acercarse tanto a otra
    d_nace = 0.9 * sep            # y una semilla solo vale si esta a mas de esto

    soldaduras: list[list[float]] = []

    def integrar(semilla_pt, signo, i_propia):
        """Integra desde la semilla en un sentido. Si muere cerca de otra
        fibra, se SUELDA a ella: el tramo final va hasta el punto mas cercano
        de la vecina, para que ninguna punta quede suelta."""
        pts = []
        q = np.array(semilla_pt, dtype=float)
        for _ in range(2000):
            v = _campo(q, H) * signo
            qm = q + 0.5 * paso * v
            q2 = q + paso * _campo(qm, H) * signo
            if not en_region(q2):
                break
            d, k, qn = rej.cerca(q2, d_muere, salvo=i_propia)
            if k >= 0:
                pts.append(q2)
                soldaduras.append([*q2, *qn, w])
                break
            pts.append(q2)
            q = q2
        return pts

    cola = [np.array([(x0 + x1) / 2, (y0 + y1) / 2 - 30.0])]
    while cola:
        s = cola.pop(0)
        if not en_region(s) or rej.cerca(s, d_nace)[1] >= 0:
            continue
        i = len(fibras)
        atras = integrar(s, -1.0, i)[::-1]
        adelante = integrar(s, +1.0, i)
        linea = np.array(atras + [s] + adelante)
        if len(linea) * paso < 2.5 * sep:
            continue
        fibras.append(linea)
        for q in linea:
            rej.mete(i, q)
        # semillas a sep a cada lado, cada ~sep a lo largo
        for j in range(0, len(linea), max(1, int(sep / paso))):
            t = _campo(linea[j], H)
            n = np.array([-t[1], t[0]])
            for lado in (+1.0, -1.0):
                cola.append(linea[j] + n * sep * lado)

    # --- ninguna punta suelta: cada extremo de fibra que no muere en el marco
    # se suelda a la vecina mas cercana, con una curva tangente al flujo -----
    for i, f in enumerate(fibras):
        for extremo, signo in ((f[0], -1.0), (f[-1], +1.0)):
            if _dist_borde(P, extremo[None, :])[0] < marco + 1.5 * paso:
                continue                      # muere en el marco: ya esta sujeta
            d, k, qn = rej.cerca(extremo, 1.3 * sep, salvo=i)
            if k < 0:
                continue
            t = _campo(extremo, H) * signo
            tn = _campo(qn, H) * signo
            curva = _bezier(extremo, t, qn, tn, n=6)
            for a, b in zip(curva[:-1], curva[1:]):
                soldaduras.append([*a, *b, w])

    # --- puentes: lentes escalonadas, curvas en S tangentes al flujo --------
    segs: list[list[float]] = list(soldaduras)
    for i, f in enumerate(fibras):
        for a, b in zip(f[:-1], f[1:]):
            segs.append([*a, *b, w])
    puentes = 0
    for i, f in enumerate(fibras):
        largo = np.r_[0.0, np.cumsum(np.hypot(*np.diff(f, axis=0).T))]
        s_sig = rng.uniform(0.2, 0.8) * lente
        while s_sig < largo[-1] - 0.3 * lente:
            j = int(np.searchsorted(largo, s_sig))
            j = min(max(j, 1), len(f) - 2)
            A = f[j]
            t = _campo(A, H)
            n = np.array([-t[1], t[0]])
            # solo hacia la izquierda: cada par de fibras se puentea una vez
            d, k, B = rej.cerca(A + n * sep, 0.75 * sep, salvo=i)
            if k >= 0 and k > i:
                tb = _campo(B, H)
                curva = _bezier(A, t, B, tb)
                for a, b in zip(curva[:-1], curva[1:]):
                    segs.append([*a, *b, w])
                puentes += 1
            s_sig += lente * (1.0 + lente_jitter * rng.uniform(-1.0, 1.0))
    S = np.array(segs)

    # --- las dos areas, por muestreo --------------------------------------
    ventana = float(p.get("marco_fondo", 26.0))
    N = 120_000
    muestra = np.stack([rng.uniform(x0, x1, N), rng.uniform(y0, y1, N)], axis=1)
    en_perfil = _dentro(P, muestra)
    dist = _dist_borde(P, muestra)
    pts = muestra[en_perfil]
    cubierto = np.zeros(len(pts), dtype=bool)
    for k in range(0, len(pts), 10_000):
        D = _dist_segmentos(pts[k:k + 10_000], S)
        cubierto[k:k + 10_000] = (D <= S[:, 4] / 2.0).any(axis=1)
    ab_full = np.zeros(N, dtype=bool)
    ab_full[np.flatnonzero(en_perfil)] = ~cubierto
    area = lambda m: m.mean() * area_bbox  # noqa: E731
    area_region = area(en_perfil & (dist >= marco))
    area_abierta = area(en_perfil & (dist >= marco) & ab_full)
    area_ventana = area(en_perfil & (dist >= ventana) & ab_full)
    return dict(nervios=S, fibras=fibras, n_fibras=len(fibras), n_puentes=puentes,
                n_soldaduras=len(soldaduras),
                area_perfil=area_perfil, area_region=area_region,
                area_abierta=area_abierta, abierto=area_abierta / area_perfil,
                area_ventana=area_ventana, ventana=ventana, marco=marco, P=P)


def escribir(r: dict, ruta: str = SALIDA) -> None:
    lineas = ["// GENERADO por celosia.py -- no editar a mano. Nervios como segmentos",
              "// [x0, y0, x1, y1, w]; parametros y medida del area abierta al pie.",
              "celosia_nervios = ["]
    for s in r["nervios"]:
        lineas.append(f"  [{s[0]:.2f},{s[1]:.2f},{s[2]:.2f},{s[3]:.2f},{s[4]:.2f}],")
    lineas += ["];",
               f"celosia_cierre = {CIERRE};",
               f"celosia_marco = {r['marco']};",
               f"celosia_n = {len(r['nervios'])};   // segmentos: {r['n_fibras']} fibras, "
               f"{r['n_puentes']} puentes",
               f"celosia_abierto_mm2 = {r['area_abierta']:.0f};   // por cachete: lo que se VE",
               f"celosia_abierto = {r['abierto']:.3f};         // fraccion del perfil ({r['area_perfil']:.0f} mm2)",
               f"celosia_abierto_ventana_mm2 = {r['area_ventana']:.0f};   // por cachete, SOLO sobre la ventana del",
               f"                                     // anillo (a >= {r['ventana']:.0f} del perfil): lo que RESPIRA",
               ""]
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas))


def preview(r: dict, ruta: str) -> None:
    """Un PNG de la celosia en 2D, para mirarla en segundos y no en minutos."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    P = np.vstack([r["P"], r["P"][:1]])
    W_IN = 10.0
    fig = plt.figure(figsize=(W_IN, W_IN * 260 / 330), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal")
    ax.set_xlim(-5, 325)
    ax.set_ylim(-5, 262)
    ppmm = W_IN * 72 / 330.0
    ax.fill(P[:, 0], P[:, 1], color="#e8873a")
    ax.plot(P[:, 0], P[:, 1], color="#f4f4f0", lw=2 * r["marco"] * ppmm,
            solid_joinstyle="round")
    for x0, y0, x1, y1, w in r["nervios"]:
        ax.plot([x0, x1], [y0, y1], color="#f4f4f0", lw=w * ppmm,
                solid_capstyle="round")
    ax.set_title(f"{r['n_fibras']} fibras, {r['n_puentes']} puentes, "
                 f"abre {100 * r['abierto']:.0f} %")
    ax.axis("off")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, bbox_inches="tight")


if __name__ == "__main__":
    r = generar()
    escribir(r)
    print(f"celosia de fibras: {r['n_fibras']} fibras, {r['n_soldaduras']} soldaduras, "
          f"{r['n_puentes']} puentes, {len(r['nervios'])} segmentos")
    print(f"  perfil {r['area_perfil']:.0f} mm2 | region {r['area_region']:.0f} mm2")
    print(f"  ABIERTO por cachete: {r['area_abierta']:.0f} mm2 = {100*r['abierto']:.1f} % del perfil (lo que se ve)")
    print(f"  y de eso RESPIRA {r['area_ventana']:.0f} mm2 (sobre la ventana del anillo, a >= {r['ventana']:.0f} mm)")
    print(f"  escrito {SALIDA}")
    if "--preview" in sys.argv:
        ruta = os.path.join(DIR, "..", "renders", "build", "celosia.png")
        preview(r, ruta)
        print(f"  preview {os.path.abspath(ruta)}")
