"""La celosia del cachete RECREADA del tejido KONDOR: placa con lentes, no tubos.

    python celosia_kondor.py --preview   -> renders/build/kondor.png
    python celosia_kondor.py             -> escribe celosia_kondor.json

EL ERROR QUE ESTO CORRIGE. En la lamina "KONDOR - ORGANIC LATTICE GEOMETRY" las
lineas negras son CANTOS, no fibras: el material es la banda BLANCA entre
huecos, y las lineas de 1 px que se ven dentro de la masa son lineas de flujo
DIBUJADAS sobre la superficie, no geometria. Tres versiones del 06-09
(esqueleto -> tubos, y `celosia.py` recalibrado) construyeron el negativo del
dibujo y por eso leian a alambre. La pieza es PLACA MENOS LENTES, con el canto
redondeado -- que es exactamente lo que ensena el render de acabado de Samuel:
una masa continua perforada, con gargantas suaves donde dos bandas se funden.

NO HAY FORMULA FISICA DEBAJO DEL DIBUJO: es una ilustracion, sus etiquetas
evocan flujo pero nadie integro un campo para trazarla. Asi que lo unico
honesto es MEDIRLA y recrear su gramatica, que es lo que Samuel pidio
("aprender la forma para recrearla en el espacio que tenemos disponible").

LA GRAMATICA, medida sobre las 75 lentes de `kondor_lentes.json`:
  - fraccion abierta 32,9 %; alargamiento mediana 4,05 (p10 1,9 · p90 7,0)
  - eje mayor mediana 143 px, menor 35 px
  - la lente NO es una elipse: cuerpo eliptico y puntas que cierran con angulo
    finito (mediana 35 grados). Con elipses lee a agujero de queso.
  - curvatura "banana": flecha/longitud 0,04 mediana, 0,08 p90
  - dos regimenes: arriba laminas diagonales a ~45 grados con lentes largas;
    abajo una trenza casi horizontal con lentes cortas alternando inclinacion.
    El campo se transporta de la lamina, no se inventa: se interpola de los
    centroides y angulos de las 75 lentes en coordenadas normalizadas.

Por eso no se estira el dibujo para que quepa: un warp por columnas subiria las
diagonales de 45 a 60 grados y bajaria el alargamiento de la trenza de 4 a 2,6,
que es justo lo que da caracter. Se recrea colocando las lentes REALES --las de
la lamina, normalizadas como sellos-- a lo largo de las lineas de flujo de ese
campo, con el tamano que les toca por region.
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np
from scipy import ndimage

DIR = os.path.dirname(os.path.abspath(__file__))
LENTES = os.environ.get("KONDOR_LENTES", r"D:\Desktop\kondor_lentes.json")
SALIDA = os.path.join(DIR, "celosia_kondor.json")

# --- la pieza ---------------------------------------------------------------
PERFIL = [[0.0, 0.0], [0.0, 19.0], [89.33, 146.58], [160.15, 146.58],
          [269.76, 256.18], [319.76, 256.18], [319.76, 0.0]]
MARCO = 28.0            # mm que el marco ocupa hacia dentro del perfil
MARGEN_LENTE = 3.0      # mm: ninguna lente se acerca mas que esto al marco.
                        # En el render de acabado no hay UNA sola lente cortada.

# --- la recreacion ----------------------------------------------------------
ESCALA = 0.38           # mm por px de lamina. 0.147 (mapear el ancho del
                        # lienzo al ancho util) daba lentes de 21 x 5 mm:
                        # granos de arroz. En el render de acabado la lente
                        # larga mide un tercio largo de la pieza.
SEP_BANDA = 1.12        # separacion entre lineas de flujo, x el eje menor local
PASO_LENTE = 1.10       # avance entre lentes de una misma linea, x el eje mayor
PASO_INT = 1.5          # mm, paso de integracion de la linea de flujo
FILLET = 1.2            # mm, radio de garganta. Con 2.4 sobre lentes de 13 mm
                        # de ancho se comia las puntas y salian capsulas: el
                        # angulo de punta (35 grados en la lamina) es caracter.
PARED_MIN = 2.2         # mm, banda de material mas fina admisible en PA12
SEMILLA = 7

# el campo se suaviza asi al interpolar de las 75 muestras: cada lente pesa
# 1/(d^2 + SUAVE^2) en coordenadas normalizadas (0..1 del lienzo)
SUAVE = 0.05            # con 0.13 el campo se promediaba a casi horizontal en
                        # toda la pieza y se perdian los dos regimenes de la
                        # lamina (diagonales a 45 arriba, trenza abajo)


def _leer():
    d = json.load(open(LENTES, encoding="utf-8"))
    W, H = 1795.0, 910.0
    vb = d.get("viewBox")
    if isinstance(vb, (list, tuple)) and len(vb) == 4:
        W, H = float(vb[2]), float(vb[3])
    elif isinstance(vb, str):
        p = vb.split()
        W, H = float(p[2]), float(p[3])
    buenas = [h for h in d["huecos"] if h["tipo"] in ("lente", "lente_recuperada")]
    return d, buenas, W, H


def sellos(buenas, W, H):
    """Cada lente normalizada: centrada, eje mayor a 0 grados, escala unidad.

    Se guarda tambien donde estaba (u, v) y su tamano, porque el tamano y el
    rumbo son funcion del sitio: laminas largas arriba, trenza corta abajo.
    """
    out = []
    for h in buenas:
        P = np.array(h["puntos"], float)
        c = P.mean(axis=0)
        # el angulo del JSON es en el sistema de imagen (y hacia abajo)
        t = math.radians(h["angulo_eje_mayor_grados"])
        R = np.array([[math.cos(-t), -math.sin(-t)], [math.sin(-t), math.cos(-t)]])
        Q = (P - c) @ R.T
        L = max(h["eje_mayor_px"], 1e-6)
        out.append({"forma": Q / L,                      # eje mayor = 1
                    "u": h["centroide"][0] / W, "v": h["centroide"][1] / H,
                    "mayor": h["eje_mayor_px"], "menor": h["eje_menor_px"],
                    "alarg": h["alargamiento"], "ang": h["angulo_eje_mayor_grados"]})
    return out


def _pesos(S, u, v):
    du = np.array([s["u"] for s in S]) - u
    dv = np.array([s["v"] for s in S]) - v
    w = 1.0 / (du * du + dv * dv + SUAVE * SUAVE)
    return w / w.sum()


def campo(S, u, v):
    """Rumbo local, en radianes y en el sistema de la PIEZA (y hacia arriba).

    Se interpola el angulo DOBLE porque una direccion es modulo 180 grados:
    promediar 179 y 1 grado como numeros da 90, y como direcciones da 0.
    """
    w = _pesos(S, u, v)
    a = np.radians(np.array([s["ang"] for s in S]) * 2.0)
    t2 = math.atan2(float(w @ np.sin(a)), float(w @ np.cos(a)))
    return -t2 / 2.0            # y de imagen va hacia abajo: se invierte


def tamano(S, u, v):
    """(eje mayor, eje menor) en px de lamina, interpolados del sitio."""
    w = _pesos(S, u, v)
    return (float(w @ np.array([s["mayor"] for s in S])),
            float(w @ np.array([s["menor"] for s in S])))


def dentro(poly, pts):
    P = np.asarray(poly, float)
    x, y = np.asarray(pts, float).reshape(-1, 2).T
    d = np.zeros(len(x), bool)
    for (x0, y0), (x1, y1) in zip(P, np.roll(P, -1, axis=0)):
        cruza = (y0 > y) != (y1 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = (x1 - x0) * (y - y0) / (y1 - y0) + x0
        d ^= cruza & (x < xi)
    return d


def generar():
    d, buenas, W, H = _leer()
    S = sellos(buenas, W, H)
    P = np.array(PERFIL, float)
    ancho, alto = P[:, 0].max(), P[:, 1].max()
    rng = np.random.default_rng(SEMILLA)

    # region util: dentro del perfil y a mas de MARCO + margen del borde
    nx, ny = int(ancho / 0.5) + 1, int(alto / 0.5) + 1
    gx, gy = np.meshgrid(np.arange(nx) * 0.5, np.arange(ny) * 0.5)
    malla = np.stack([gx.ravel(), gy.ravel()], 1)
    en_perfil = dentro(P, malla).reshape(ny, nx)
    dist = ndimage.distance_transform_edt(en_perfil) * 0.5
    util = dist > (MARCO + MARGEN_LENTE)

    def libre(p):
        i, j = int(p[1] / 0.5), int(p[0] / 0.5)
        return 0 <= i < ny and 0 <= j < nx and util[i, j]

    def uv(p):
        return min(max(p[0] / ancho, 0.0), 1.0), min(max(1.0 - p[1] / alto, 0.0), 1.0)

    # --- las lentes, sembradas por DARDOS sobre toda la region --------------
    # Antes se integraban lineas de flujo largas y se colgaban lentes de ellas.
    # Las lineas se cortan donde la region se estrecha, asi que la rampa alta
    # quedaba vacia en las tres escalas probadas. Sembrar por dardos cubre toda
    # la pieza por construccion: cada lente se orienta con el campo local y se
    # acepta solo si respeta la pared minima con las ya puestas.
    MM = 0.4                                   # mm/px de la mascara de ocupacion
    W_ = int(ancho / MM) + 1
    H_ = int(alto / MM) + 1
    ocup = np.zeros((H_, W_), bool)
    from PIL import Image, ImageDraw

    def pinta(pol, mask):
        im = Image.fromarray(mask.astype(np.uint8) * 255).convert("1")
        ImageDraw.Draw(im).polygon([(x / MM, y / MM) for x, y in pol], fill=1)
        return np.asarray(im, bool)

    def choca(pol):
        xs, ys = pol[:, 0] / MM, pol[:, 1] / MM
        x0, x1 = int(max(xs.min() - 2, 0)), int(min(xs.max() + 3, W_))
        y0, y1 = int(max(ys.min() - 2, 0)), int(min(ys.max() + 3, H_))
        if x1 <= x0 or y1 <= y0:
            return True
        im = Image.new("1", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(im).polygon([(x / MM - x0, y / MM - y0) for x, y in pol], fill=1)
        return bool((np.asarray(im, bool) & ocup[y0:y1, x0:x1]).any())

    k_pared = int(round((PARED_MIN / 2.0) / MM))
    el_pared = np.hypot(*np.mgrid[-k_pared:k_pared + 1, -k_pared:k_pared + 1]) <= k_pared

    puestas = []
    lineas = []
    DARDOS = 24000
    for _ in range(DARDOS):
        c = np.array([rng.uniform(0, ancho), rng.uniform(0, alto)])
        if not libre(c):
            continue
        u_, v_ = uv(c)
        mayor_px, menor_px = tamano(S, u_, v_)
        L = mayor_px * ESCALA
        objetivo = mayor_px / max(menor_px, 1e-6)
        w = _pesos(S, u_, v_) * np.exp(
            -((np.array([x["alarg"] for x in S]) - objetivo) / 1.2) ** 2)
        sel = S[int(rng.choice(len(S), p=w / w.sum()))]
        ang = campo(S, u_, v_)
        R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
        puesta = None
        for f in (1.0, 0.82, 0.66, 0.52, 0.4):
            Q = sel["forma"] * (L * f)
            Q = Q.copy()
            # banana: la lente sigue el flujo, no es recta (flecha/largo 0,04)
            flecha = 0.045 * L * f * rng.uniform(0.3, 1.7) * rng.choice([-1.0, 1.0])
            Q[:, 1] += flecha * (1.0 - (2.0 * Q[:, 0] / max(L * f, 1e-6)) ** 2)
            pol = Q @ R.T + c
            if not dentro(P, pol).all() or not all(libre(q) for q in pol[::3]):
                continue
            if choca(pol):
                continue
            puesta = pol
            break
        if puesta is None:
            continue
        puestas.append(puesta)
        # se marca la lente MAS la media pared: nada podra acercarse mas
        m = pinta(puesta, np.zeros((H_, W_), bool))
        ocup |= ndimage.binary_dilation(m, el_pared)

    return {"P": P, "perfil": PERFIL, "lentes": puestas, "lineas": lineas,
            "util": util, "ancho": ancho, "alto": alto, "S": S}


def mascara(r, mmpx=0.25):
    """La PLACA MENOS LAS LENTES, con la garganta redondeada.

    El fillet es morfologico y hace las dos cosas del render de acabado: cerrar
    (quita las paredes mas finas que PARED_MIN y funde dos bandas en una
    garganta suave) y abrir (redondea las puntas de material que quedan). Es el
    buffer(-r).buffer(+r) de siempre, en raster.
    """
    from PIL import Image, ImageDraw
    ancho, alto = r["ancho"], r["alto"]
    W, H = int(ancho / mmpx) + 1, int(alto / mmpx) + 1
    im = Image.new("1", (W, H), 0)
    d = ImageDraw.Draw(im)
    d.polygon([(x / mmpx, y / mmpx) for x, y in r["perfil"]], fill=1)
    placa = np.asarray(im, bool)
    im2 = Image.new("1", (W, H), 0)
    d2 = ImageDraw.Draw(im2)
    for pol in r["lentes"]:
        d2.polygon([(x / mmpx, y / mmpx) for x, y in pol], fill=1)
    huecos = np.asarray(im2, bool)
    masa = placa & ~huecos
    k = int(round(FILLET / mmpx))
    el = np.hypot(*np.mgrid[-k:k + 1, -k:k + 1]) <= k
    masa = ndimage.binary_closing(masa, el)          # funde gargantas
    masa = ndimage.binary_opening(masa, el) | placa & masa & ~huecos
    masa &= placa
    return placa, huecos, masa, mmpx


def preview(r, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    placa, huecos, masa, mmpx = mascara(r)
    fig, ax = plt.subplots(figsize=(11, 9))
    rgb = np.zeros(masa.shape + (3,), float)
    rgb[...] = 1.0
    rgb[placa] = (1.0, 0.55, 0.15)                    # el ambar de detras
    rgb[masa] = (0.96, 0.96, 0.94)                    # la masa impresa
    ax.imshow(rgb, origin="lower", extent=(0, r["ancho"], 0, r["alto"]))
    C = np.vstack([r["P"], r["P"][:1]])
    ax.plot(C[:, 0], C[:, 1], color="#888", lw=0.8)
    abierto = (placa & ~masa).sum() * mmpx * mmpx
    ax.set_title(f"{len(r['lentes'])} lentes · abre {abierto:.0f} mm² "
                 f"({100*abierto/(placa.sum()*mmpx*mmpx):.1f} % del perfil)")
    ax.axis("off")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=150, bbox_inches="tight", facecolor="white")
    print("preview:", os.path.normpath(ruta))
    return abierto


def main():
    global ESCALA, SEP_BANDA, PASO_LENTE
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--escala", type=float, default=ESCALA)
    ap.add_argument("--sep", type=float, default=SEP_BANDA)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    ESCALA, SEP_BANDA = a.escala, a.sep
    r = generar()
    print(f"lineas {len(r['lineas'])} · lentes colocadas {len(r['lentes'])}")
    if a.preview:
        preview(r, os.path.join(DIR, "..", "renders", "build", f"kondor{a.tag}.png"))
        return
    json.dump({"generado_por": "celosia_kondor.py",
               "perfil": PERFIL, "marco": MARCO,
               "lentes": [np.round(p, 2).tolist() for p in r["lentes"]]},
              open(SALIDA, "w"), separators=(",", ":"))
    print("escrito", SALIDA)


if __name__ == "__main__":
    main()
