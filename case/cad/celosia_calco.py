"""El cachete CALCADO del concepto: la composicion entera del cachete de la
lamina --los ejes de las bandas con sus uniones, anclajes y puntas-- llevada a
nuestro perfil y vestida con anchuras a UNA escala global. Sale en el formato
de celosia_rama.json, asi que imprimir_piel.py la levanta en 3D sin cambios.

Por que calcar y no regenerar (07-09): con las lentes reales sembradas por
estadistica la pieza le leyo «caotica» a Samuel; lo que faltaba era la
ORGANIZACION --bandas continuas que se separan y se vuelven a pegar--, y eso
no sale de medidas locales, sale de heredar el grafo del concepto entero.

La fuente es el trazado de vectorizer (D:/Desktop/cachete_concepto.json):
136 ejes [x, y, ancho_px] cada 2 px, 119 nodos (union / marco / punta /
paso), sobre la vista interior del concepto. Tres cosas suyas que mandan aqui:
  - el concepto tiene SEIS esquinas: el hombro desemboca en el lado de la
    nariz. A 20 mm dentro del perfil nuestra nariz de 19 mm desaparece y el
    perfil tambien queda con seis, asi que el registro cae solo;
  - hacia el marco no hay lentes sino ramas sobre un vacio continuo (31 % del
    plano), con 12 puntas libres y 32 anclajes: la placa se construye desde
    los ejes, y los huecos son lo que queda;
  - el estiron (concepto 0,75 de relacion, pieza 1,25) no puede caer sobre
    las anchuras: la deformacion es lo mas parecida a una similitud (MLS,
    Schaefer 2006) y la anchura se escala con un solo factor.
"""
import json
import math
import os
import sys

import numpy as np

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)
import celosia  # noqa: E402
import clearance_budget as cb  # noqa: E402

CONCEPTO = os.environ.get("KONDOR_CONCEPTO", r"D:\Desktop\cachete_concepto.json")
SALIDA = os.path.join(DIR, "celosia_calco.json")

INSET_HITOS = 20.0   # mm: la linea interior del marco del concepto cae aqui, dentro
                     # del perfil. Las bandas mueren ~2,7 mm mas adentro (la pared
                     # interior del marco del dibujo), o sea en el canto interior
                     # de nuestro marco (22).
PEGA = 9.0           # mm: cada anclaje sigue recto su rumbo esto dentro del marco
ANCHO_MIN = 2.2      # mm, pared minima en PA12
ANCHO_MAX = 11.0     # mm = MARCO_E. ponytail: seccion redonda; las raices del
                     # concepto llegan a 14-20 mm y aqui se recortan. Para
                     # recuperarlas hace falta seccion eliptica en fibra().
ALFA = 1.0           # MLS: peso 1/d^(2*ALFA)
PASO_CONTROL = 6.0   # mm entre puntos de control sobre el contorno
ORDEN = ["nariz", "hombro_bajo", "hombro", "cumbre", "trasera_alta", "trasera_baja"]


def offset(P: np.ndarray, d: float) -> np.ndarray:
    """El perfil metido d hacia dentro, con esquinas netas. Un canto mas corto
    que d desaparece (la nariz de 19 mm): se quita su recta y se cruzan las
    vecinas, que es lo que celosia._inset no hace."""
    area2 = np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    sgn = 1.0 if area2 > 0 else -1.0
    lineas = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        t = (b - a) / np.linalg.norm(b - a)
        lineas.append((a + sgn * np.array([-t[1], t[0]]) * d, t))

    def esquinas(L):
        Q = []
        for i in range(len(L)):
            (p1, t1), (p2, t2) = L[i - 1], L[i]
            s = np.linalg.solve(np.array([t1, -t2]).T, p2 - p1)
            Q.append(p1 + t1 * s[0])
        return np.array(Q)

    while True:
        Q = esquinas(lineas)
        malas = [i for i in range(len(lineas))
                 if np.dot(Q[(i + 1) % len(lineas)] - Q[i], lineas[i][1]) < 0]
        if not malas:
            return Q
        del lineas[malas[0]]


def _area(A: np.ndarray) -> float:
    return 0.5 * abs(np.sum(A[:, 0] * np.roll(A[:, 1], -1) - np.roll(A[:, 0], -1) * A[:, 1]))


def controles(S: np.ndarray, T: np.ndarray):
    """Puntos de control: cada tramo del contorno fuente contra el mismo tramo
    del destino, muestreados a la misma fraccion de longitud de arco."""
    ps, qs = [], []
    for k in range(len(S)):
        a, b = S[k], S[(k + 1) % len(S)]
        c, d = T[k], T[(k + 1) % len(T)]
        n = max(3, int(round(np.linalg.norm(d - c) / PASO_CONTROL)))
        for j in range(n):                       # t = 1 es el vertice del tramo siguiente
            t = j / n
            ps.append(a + (b - a) * t)
            qs.append(c + (d - c) * t)
    return np.array(ps), np.array(qs)


def mls(Pc: np.ndarray, Qc: np.ndarray, V: np.ndarray) -> np.ndarray:
    """Deformacion MLS de similitud (Schaefer, McPhail, Warren 2006): en cada
    punto v, la similitud que mejor lleva los controles Pc a Qc con pesos
    1/d^2. Interpola los controles y no estira: donde el destino no cabe en
    una similitud, reparte el error, no lo concentra en las anchuras."""
    out = np.empty_like(V)
    for k in range(0, len(V), 2000):
        v = V[k:k + 2000]
        d2 = ((v[:, None, :] - Pc[None, :, :]) ** 2).sum(-1)
        w = 1.0 / (d2 + 1e-6) ** ALFA
        sw = w.sum(1, keepdims=True)
        ps = (w @ Pc) / sw
        qs = (w @ Qc) / sw
        ph = Pc[None, :, :] - ps[:, None, :]
        qh = Qc[None, :, :] - qs[:, None, :]
        mu = (w * (ph ** 2).sum(-1)).sum(1)
        a = (w * (ph * qh).sum(-1)).sum(1) / mu
        b = (w * (ph[..., 0] * qh[..., 1] - ph[..., 1] * qh[..., 0])).sum(1) / mu
        vh = v - ps
        out[k:k + 2000, 0] = a * vh[:, 0] - b * vh[:, 1] + qs[:, 0]
        out[k:k + 2000, 1] = b * vh[:, 0] + a * vh[:, 1] + qs[:, 1]
    return out


def generar(medir=True):
    with open(CONCEPTO, encoding="utf-8") as f:
        c = json.load(f)
    W, H = c["recorte"]["ancho"], c["recorte"]["alto"]

    def voltea(xy):
        """px del recorte (y abajo, parte alta a la izquierda) -> px con y arriba
        y la parte alta a la derecha, la mano de nuestro perfil."""
        xy = np.asarray(xy, float)
        return np.stack([W - xy[..., 0], H - xy[..., 1]], axis=-1)

    P = np.array(cb._vertices(cb.leer_params()), float)
    S = voltea([c["hitos"][h] for h in ORDEN])
    T = offset(P, INSET_HITOS)
    assert len(T) == 6, f"a {INSET_HITOS} mm el perfil tiene {len(T)} esquinas, no 6"
    escala = math.sqrt(_area(T) / _area(S))          # mm por px, UNA para todo
    Pc, Qc = controles(S, T)

    # --- los ejes, deformados; la anchura escalada, no deformada ------------
    tipo = {n["id"]: n["tipo"] for n in c["nodos"]}
    fibras, n_union, n_punta, n_marco = [], 0, 0, 0
    todos = np.concatenate([np.asarray(e["puntos"], float)[:, :2] for e in c["ejes"]])
    XY = mls(Pc, Qc, voltea(todos))
    k = 0
    for e in c["ejes"]:
        pts = np.asarray(e["puntos"], float)
        n = len(pts)
        xy = XY[k:k + n]
        k += n
        w = np.clip(pts[:, 2] * escala, ANCHO_MIN, ANCHO_MAX)
        if n < 2:
            continue
        ln = np.column_stack([xy, np.zeros(n), w])
        # un anclaje entra recto en el marco, siguiendo el rumbo con que llega
        if tipo.get(e["nodo_b"]) == "marco":
            u = ln[-1, :2] - ln[-2, :2]
            ln = np.vstack([ln, [*(ln[-1, :2] + u / np.linalg.norm(u) * PEGA), 0.0, w[-1]]])
        if tipo.get(e["nodo_a"]) == "marco":
            u = ln[0, :2] - ln[1, :2]
            ln = np.vstack([[*(ln[0, :2] + u / np.linalg.norm(u) * PEGA), 0.0, w[0]], ln])
        fibras.append(ln)
    n_union = sum(1 for t in tipo.values() if t == "union")
    n_punta = sum(1 for t in tipo.values() if t == "punta")
    n_marco = sum(1 for t in tipo.values() if t == "marco")

    # --- la deformacion, medida: pliegues y anisotropia ----------------------
    h = 2.0
    G = np.array([[x, y] for x in np.arange(S[:, 0].min(), S[:, 0].max(), 25.0)
                  for y in np.arange(S[:, 1].min(), S[:, 1].max(), 25.0)])
    G = G[celosia._dentro(S, G)]
    fx = (mls(Pc, Qc, G + [h, 0]) - mls(Pc, Qc, G - [h, 0])) / (2 * h)
    fy = (mls(Pc, Qc, G + [0, h]) - mls(Pc, Qc, G - [0, h])) / (2 * h)
    J = np.stack([fx, fy], axis=-1)                     # columnas = d/dx, d/dy
    det = np.linalg.det(J)
    sv = np.linalg.svd(J, compute_uv=False)
    aniso = sv[:, 0] / np.maximum(sv[:, 1], 1e-9)
    deform = dict(escala=escala, det_min=float(det.min()), pliegues=int((det <= 0).sum()),
                  aniso_mediana=float(np.median(aniso)), aniso_p90=float(np.percentile(aniso, 90)),
                  aniso_max=float(aniso.max()), escala_local_min=float(sv[:, 1].min()),
                  escala_local_max=float(sv[:, 0].max()))

    # --- marco, agujeros y areas: igual que celosia.py ------------------------
    marco = celosia.MARCO
    eje_marco = celosia._redondear(celosia._inset(P, marco / 2 - celosia.SOLAPE_CUBIERTA), r=14.0)
    agujeros = [tuple(q) for q in celosia._inset(P, celosia.MONTAJE_A)[[0, 2, 5, 6]]]
    x0, x1 = P[:, 0].min(), P[:, 0].max()
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    area_bbox = (x1 - x0) * (y1 - y0)
    rng = np.random.default_rng(3)
    N = 120_000 if medir else 4_000
    muestra = np.stack([rng.uniform(x0, x1, N), rng.uniform(y0, y1, N)], axis=1)
    en_perfil = celosia._dentro(P, muestra)
    dist = celosia._dist_borde(P, muestra)
    Sg = np.array([[*ln[k, :2], *ln[k + 1, :2], (ln[k, 3] + ln[k + 1, 3]) / 2]
                   for ln in fibras for k in range(len(ln) - 1)])
    pts = muestra[en_perfil]
    cubierto = np.zeros(len(pts), dtype=bool)
    for k in range(0, len(pts), 10_000):
        D = celosia._dist_segmentos(pts[k:k + 10_000], Sg)
        cubierto[k:k + 10_000] = (D <= Sg[:, 4] / 2.0).any(axis=1)
    ab = np.zeros(N, dtype=bool)
    ab[np.flatnonzero(en_perfil)] = ~cubierto
    ventana = float(cb.leer_params().get("marco_fondo", 26.0))
    area = lambda m: m.mean() * area_bbox  # noqa: E731
    return dict(fibras=fibras, n_fibras=len(fibras), n_soldaduras=n_union, n_puentes=n_punta,
                n_anclajes=n_marco, eje_marco=eje_marco, agujeros=agujeros,
                area_perfil=_area(P), area_region=area(en_perfil & (dist >= marco)),
                area_abierta=area(en_perfil & (dist >= marco) & ab),
                area_ventana=area(en_perfil & (dist >= max(ventana, marco)) & ab),
                ventana=ventana, marco=marco, P=P, deform=deform,
                anchos=np.concatenate([ln[:, 3] for ln in fibras]))


def escribir(r: dict, ruta: str = SALIDA) -> None:
    doc = dict(
        generado_por="celosia_calco.py -- no editar a mano",
        fuente=CONCEPTO,
        marco=dict(ancho=r["marco"], espesor=celosia.MARCO_E, eje=np.round(r["eje_marco"], 2).tolist()),
        agujeros=dict(diametro=celosia.MONTAJE_D, centros=np.round(r["agujeros"], 2).tolist()),
        nudo=list(celosia.NUDO),
        perfil=np.round(r["P"], 2).tolist(),
        fibras=[np.round(f, 2).tolist() for f in r["fibras"]],
        medidas=dict(n_fibras=r["n_fibras"], n_uniones=r["n_soldaduras"], n_puntas=r["n_puentes"],
                     n_anclajes=r["n_anclajes"],
                     area_perfil_mm2=round(r["area_perfil"]),
                     abierto_mm2=round(r["area_abierta"]),
                     abierto=round(r["area_abierta"] / r["area_perfil"], 3),
                     abierto_region=round(r["area_abierta"] / r["area_region"], 3),
                     abierto_ventana_mm2=round(r["area_ventana"]),
                     ventana_desde_perfil=r["ventana"],
                     deformacion={k: round(v, 3) for k, v in r["deform"].items()}),
    )
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, separators=(",", ":"))
        f.write("\n")


def main():
    r = generar()
    d, a = r["deform"], r["anchos"]
    print(f"  {r['n_fibras']} bandas, {r['n_soldaduras']} uniones, {r['n_anclajes']} anclajes, "
          f"{r['n_puentes']} puntas libres")
    print(f"  escala {d['escala']:.4f} mm/px; anchura p10/p50/p90/max = "
          f"{np.percentile(a, 10):.1f} / {np.median(a):.1f} / {np.percentile(a, 90):.1f} / {a.max():.1f} mm "
          f"(recortadas a {ANCHO_MAX}: {100 * (a >= ANCHO_MAX - 1e-9).mean():.0f} % de los puntos)")
    print(f"  deformacion: det min {d['det_min']:.4f} ({d['pliegues']} pliegues), anisotropia mediana "
          f"{d['aniso_mediana']:.2f}, p90 {d['aniso_p90']:.2f}, max {d['aniso_max']:.2f}; "
          f"escala local {d['escala_local_min']:.3f}-{d['escala_local_max']:.3f} mm/px")
    print(f"  ABIERTO: {r['area_abierta']:.0f} mm2 = {100 * r['area_abierta'] / r['area_perfil']:.0f} % del perfil, "
          f"{100 * r['area_abierta'] / r['area_region']:.0f} % de la region; "
          f"respira por la ventana {r['area_ventana']:.0f} mm2")
    if "--preview" in sys.argv:
        ruta = os.path.join(DIR, "..", "renders", "build", "celosia_calco.png")
        celosia.preview(r, ruta)
        print("  preview", os.path.abspath(ruta))
    else:
        escribir(r)
        print("  escrito", SALIDA)


if __name__ == "__main__":
    main()
