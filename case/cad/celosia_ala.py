"""El cachete como ALA: los filamentos de la lamina KONDOR sobre nuestro perfil.

Samuel (07-09, via vectorizer): un acabado «mas futuristico, delicado, suave y
fino: que se parezca mas a un ala de una mariposa androide que al esqueleto
de unas costillas», y la lamina KONDOR como el «asi». Lectura de venas: los
trazos negros de la lamina SON los filamentos y todo lo blanco es celda
abierta (89 % abierto). Lo contrario de la placa perforada del calco.

Fuente: D:/Desktop/kondor_filamentos.json (vectorizer): 769 ejes [x, y,
ancho_px] cada 2 px sobre la lamina de 2146 x 1088 px a 0,1185 mm/px (barra
de 5 cm), o sea 254 x 129 mm: la lamina esta dibujada a la escala de la
pieza. Se pone a 1:1, espejada (la parte alta de la lamina, las laminas
diagonales, queda ATRAS, paralela a la rampa alta) y con su base en la
nuestra: cubre el 82 % de la region. Lo que no cubre es el triangulo alto
trasero, y ahi cada filamento que la lamina cortaba en su borde se continua
por su propio rumbo hasta el marco -- el mismo aspecto que tiene el borde de
la lamina, solo que mas largo. Nada se estira: las anchuras van a una sola
escala y las celdas son las de la lamina.

Seccion: CINTA fina, no tubo (imprimir_piel.py, seccion «cinta»): primarios
de ~1,8 mm en planta siguiendo la variacion de la lamina (x1,4 en las
uniones), 3 mm de fondo; la rigidez sale del fondo, la finura de la planta.
Lineas finas solo las que cuelgan de la red por los dos extremos: sin
membrana, una linea que nace y muere en la celda flota.

Sale en el formato de celosia_rama.json para imprimir_piel.py (PIEL_RAMA).
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
from celosia_calco import offset  # noqa: E402

LAMINA = os.environ.get("KONDOR_FILAMENTOS", r"D:\Desktop\kondor_filamentos.json")
SALIDA = os.path.join(DIR, "celosia_ala.json")

FACTOR = 1.0         # x la escala de la lamina (0,1185 mm/px). 1 = tal cual
INSET = 22.0         # mm: la region del ala llega al canto interior del marco
PEGA = 9.0           # mm: cuanto entra cada filamento en el marco, recto
EXT_MAX = 25.0       # mm: hasta donde se continua un filamento que la lamina
                     # cortaba en su borde buscando el marco cercano
W_PRIM = 1.8         # mm en planta del primario mediano (2,8 px en la lamina)
W_PRIM_MAX = 2.6     # mm: las uniones, x1,4
W_PRIM_MIN = 1.5
W_FINO = 1.0         # mm: las lineas finas colgadas de la red
FONDO = 3.0          # mm: profundidad de la cinta
VOXEL = 0.3          # mm: remallado; una cinta de 1,5 no sobrevive al 0,6
TRAMO_MIN = 0.3      # mm: solo se tira lo que ya no es un segmento. (Con 4 mm
                     # se fueron 115 conectores de union y la red quedo rota.)
BORDE = ("borde", "marco")  # como llama cada trazado al nodo que muere en el borde de la lamina
ESPOLON_PX = 40.0    # px: un eje mas corto que esto que acaba en punta, o que se
                     # cierra sobre si mismo, es un espolon del esqueleto: fuera
# EL TRIANGULO ALTO TRASERO no lo cubre la lamina (124 mm de alto contra 212)
# y sus laminas son lentes cerradas: no hay nada que continuar, y copiarlas
# encima salio a pedazos. Se ESTIRA la lamina solo a lo largo de sus laminas
# (la diagonal +45, paralela a la rampa alta): cada rayo por esa direccion se
# alarga lo que le falta para llegar al marco, con factor 1 en la base y
# creciendo en cuadratico hacia arriba. Las lentes diagonales se alargan sin
# cambiar de rumbo ni de separacion; la trenza de abajo apenas se entera.
ESTIRA_SUAVE = 15.0        # mm: ventana en v para que el estiron no tenga escalon en la rampa


def _cruce(a: np.ndarray, b: np.ndarray, R: np.ndarray):
    """Donde el segmento a-b cruza el contorno R: (t, punto), t en [0,1]."""
    d = b - a
    mejor = None
    for i in range(len(R)):
        c, e = R[i], R[(i + 1) % len(R)]
        f = e - c
        den = d[0] * f[1] - d[1] * f[0]
        if abs(den) < 1e-12:
            continue
        w = c - a
        t = (w[0] * f[1] - w[1] * f[0]) / den
        u = (w[0] * d[1] - w[1] * d[0]) / den
        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0 and (mejor is None or t < mejor[0]):
            mejor = (t, a + d * t)
    return mejor


def _rayo(p: np.ndarray, u: np.ndarray, R: np.ndarray):
    """Distancia desde p por el rumbo u hasta el contorno R (None si no lo toca)."""
    hit = _cruce(p, p + u * 1e4, R)
    return None if hit is None else hit[0] * 1e4


def _rumbo_final(ln: np.ndarray, largo: float = 4.0) -> np.ndarray:
    """Rumbo con que la polilinea llega a su ultimo punto: el promedio de sus
    ultimos `largo` mm, para no heredar el ruido del trazado."""
    s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(ln[:, :2], axis=0).T))]
    k = int(np.searchsorted(s, s[-1] - largo))
    k = min(k, len(ln) - 2)
    u = ln[-1, :2] - ln[k, :2]
    n = np.linalg.norm(u)
    return u / n if n > 1e-9 else ln[-1, :2] - ln[-2, :2]


def _recorta(ln: np.ndarray, R: np.ndarray):
    """Trozos de ln (x, y, w) dentro de R; cada trozo es (puntos, cortado_a, cortado_b)."""
    dentro = celosia._dentro(R, ln[:, :2])
    trozos, actual, corte_a = [], [], False
    for i in range(len(ln)):
        if dentro[i]:
            if not actual and i > 0:
                t, q = _cruce(ln[i - 1, :2], ln[i, :2], R) or (0.0, ln[i, :2])
                actual.append([*q, ln[i - 1, 2] + (ln[i, 2] - ln[i - 1, 2]) * t])
                corte_a = True
            actual.append(list(ln[i]))
        elif actual:
            t, q = _cruce(ln[i - 1, :2], ln[i, :2], R) or (1.0, ln[i - 1, :2])
            actual.append([*q, ln[i - 1, 2] + (ln[i, 2] - ln[i - 1, 2]) * t])
            trozos.append((np.array(actual), corte_a, True))
            actual, corte_a = [], False
    if actual:
        trozos.append((np.array(actual), corte_a, False))
    return trozos


def _largo(ln: np.ndarray) -> float:
    return float(np.hypot(*np.diff(ln[:, :2], axis=0).T).sum())


def generar(medir=True):
    with open(LAMINA, encoding="utf-8") as f:
        c = json.load(f)
    s = c["escala_mm_por_px"] * FACTOR
    P = np.array(cb._vertices(cb.leer_params()), float)
    R = offset(P, INSET)
    x_atras, y_base = R[:, 0].max(), R[:, 1].min()
    sil = np.array(c["silueta"], float)
    xs0, ys1 = sil[:, 0].min(), sil[:, 1].max()

    def pon(xy):
        """px de la lamina (y abajo, laminas a la izquierda) -> mm en la pieza:
        espejada (laminas ATRAS) y con la base de la lamina en nuestra base."""
        xy = np.asarray(xy, float)
        return np.stack([x_atras - (xy[..., 0] - xs0) * s, y_base + (ys1 - xy[..., 1]) * s], axis=-1)

    nodos = {n["id"]: n for n in c["nodos"]}
    ejes = [e for e in c["ejes"] if not e.get("marco")]
    # trazos fantasma fuera de la silueta de la lamina, fuera
    ejes = [e for e in ejes
            if celosia._dentro(sil, np.asarray(e["puntos"], float)[len(e["puntos"]) // 2, None, :2])[0]]
    ejes = [e for e in ejes
            if not (e.get("longitud_px", 1e9) < ESPOLON_PX
                    and (e["nodo_a"] == e["nodo_b"]
                         or "punta" in (nodos[e["nodo_a"]]["tipo"], nodos[e["nodo_b"]]["tipo"])))]
    prim = [e for e in ejes if not e.get("fino")]
    finos = [e for e in ejes if e.get("fino")]

    # lineas finas: solo las componentes colgadas de la red primaria por >= 2 nodos
    de_prim = {e["nodo_a"] for e in prim} | {e["nodo_b"] for e in prim}
    padre = {}

    def raiz(x):
        while padre.get(x, x) != x:
            x = padre[x]
        return x

    for e in finos:
        a, b = raiz(e["nodo_a"]), raiz(e["nodo_b"])
        if a != b:
            padre[a] = b
    anclas = {}
    for e in finos:
        r = raiz(e["nodo_a"])
        anclas.setdefault(r, set()).update({n for n in (e["nodo_a"], e["nodo_b"]) if n in de_prim})
    finos_ok = [e for e in finos if len(anclas.get(raiz(e["nodo_a"]), ())) >= 2]

    w_med = float(np.median(np.concatenate([np.asarray(e["puntos"], float)[:, 2] for e in prim])))
    base = []
    for e in prim + finos_ok:
        pts = np.asarray(e["puntos"], float)
        if len(pts) < 2:
            continue
        xy = pon(pts[:, :2])
        if e.get("fino"):
            w = np.full(len(pts), W_FINO)
        else:
            w = np.clip(W_PRIM * pts[:, 2] / w_med, W_PRIM_MIN, W_PRIM_MAX)
        base.append((np.column_stack([xy, w]),
                     (nodos[e["nodo_a"]]["tipo"] in BORDE, nodos[e["nodo_b"]]["tipo"] in BORDE)))

    # --- el estiron a lo largo de las laminas ------------------------------
    SQ = math.sqrt(2.0)
    y_tope = y_base + (ys1 - sil[:, 1].min()) * s      # el borde alto de la lamina
    L = SQ * (y_tope - y_base)
    vs = np.arange(-400.0, 400.0, 1.0)
    E = np.zeros_like(vs)
    for k, v in enumerate(vs):
        q = np.array([(SQ * y_tope - v - v) / SQ, (SQ * y_tope - v + v) / SQ])   # el rayo v en y = y_tope
        q = np.array([y_tope - v * SQ / 1.0 * 0.5 * 2 / 2, y_tope])              # x = y_tope - v*sqrt2
        q[0] = y_tope - v * SQ
        if not celosia._dentro(R, q[None, :])[0]:
            continue
        d = _rayo(q, np.array([1.0, 1.0]) / SQ, R)
        E[k] = 0.0 if d is None else d
    nv = max(1, int(ESTIRA_SUAVE))
    E = np.convolve(E, np.ones(nv) / nv, mode="same")

    def estira(xy):
        u = (xy[:, 0] + xy[:, 1]) / SQ
        v = (xy[:, 1] - xy[:, 0]) / SQ
        t = np.clip((u - (SQ * y_base - v)) / L, 0.0, 1.0)
        u2 = u + np.interp(v, vs, E) * t ** 2
        return np.stack([(u2 - v) / SQ, (u2 + v) / SQ], axis=1)

    base = [(np.column_stack([estira(ln[:, :2]), ln[:, 2]]), borde) for ln, borde in base]
    n_copia = int(round(E.max()))

    fibras, n_cont, n_pega, n_libres = [], 0, 0, 0
    for ln, borde in base:
        for trozo, corte_a, corte_b in _recorta(ln, R):
            if _largo(trozo) < TRAMO_MIN and not (corte_a or corte_b):
                continue
            # los dos extremos: (cortado por nuestro contorno) o (cortado por el
            # borde de la lamina) -> hasta el marco; lo demas queda como esta
            for fin in (0, 1):
                t = trozo if fin else trozo[::-1]
                cortado = corte_b if fin else corte_a
                es_borde = borde[fin] and not cortado
                if not (cortado or es_borde):
                    continue
                u = _rumbo_final(t)
                d = 0.0 if cortado else _rayo(t[-1, :2], u, R)
                if d is None or d > EXT_MAX:
                    n_libres += 1
                    continue
                cola = np.array([[*(t[-1, :2] + u * (d + PEGA)), t[-1, 2]]])
                if d > 0:
                    n_cont += 1
                    medio = np.array([[*(t[-1, :2] + u * d), t[-1, 2]]])
                    cola = np.vstack([medio, cola])
                n_pega += 1
                t = np.vstack([t, cola])
                trozo = t if fin else t[::-1]
            if _largo(trozo) < TRAMO_MIN:
                continue
            fibras.append(np.column_stack([trozo[:, :2], np.zeros(len(trozo)), trozo[:, 2]]))

    marco = celosia.MARCO
    eje_marco = celosia._redondear(celosia._inset(P, marco / 2 - celosia.SOLAPE_CUBIERTA), r=14.0)
    agujeros = [tuple(q) for q in celosia._inset(P, celosia.MONTAJE_A)[[0, 2, 5, 6]]]
    x0, x1 = P[:, 0].min(), P[:, 0].max()
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    area_bbox = (x1 - x0) * (y1 - y0)
    rng = np.random.default_rng(3)
    N = 200_000 if medir else 4_000
    muestra = np.stack([rng.uniform(x0, x1, N), rng.uniform(y0, y1, N)], axis=1)
    en_perfil = celosia._dentro(P, muestra)
    dist = celosia._dist_borde(P, muestra)
    Sg = np.array([[*ln[k, :2], *ln[k + 1, :2], (ln[k, 3] + ln[k + 1, 3]) / 2]
                   for ln in fibras for k in range(len(ln) - 1)])
    pts = muestra[en_perfil]
    cubierto = np.zeros(len(pts), dtype=bool)
    for k in range(0, len(pts), 5_000):
        D = celosia._dist_segmentos(pts[k:k + 5_000], Sg)
        cubierto[k:k + 5_000] = (D <= Sg[:, 4] / 2.0).any(axis=1)
    ab = np.zeros(N, dtype=bool)
    ab[np.flatnonzero(en_perfil)] = ~cubierto
    ventana = float(cb.leer_params().get("marco_fondo", 26.0))
    area = lambda m: m.mean() * area_bbox  # noqa: E731
    return dict(fibras=fibras, n_fibras=len(fibras), n_soldaduras=n_cont, n_puentes=n_libres,
                n_pega=n_pega, n_finos=len(finos_ok), n_finos_fuera=len(finos) - len(finos_ok),
                n_copia=n_copia,
                eje_marco=eje_marco, agujeros=agujeros, escala=s,
                area_perfil=0.5 * abs(np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])),
                area_region=area(en_perfil & (dist >= marco)),
                area_abierta=area(en_perfil & (dist >= marco) & ab),
                area_ventana=area(en_perfil & (dist >= max(ventana, marco)) & ab),
                ventana=ventana, marco=marco, P=P)


def escribir(r: dict, ruta: str = SALIDA) -> None:
    doc = dict(
        generado_por="celosia_ala.py -- no editar a mano",
        fuente=LAMINA,
        seccion=dict(tipo="cinta", fondo=FONDO),
        voxel=VOXEL,
        marco=dict(ancho=r["marco"], espesor=celosia.MARCO_E, eje=np.round(r["eje_marco"], 2).tolist()),
        agujeros=dict(diametro=celosia.MONTAJE_D, centros=np.round(r["agujeros"], 2).tolist()),
        nudo=list(celosia.NUDO),
        perfil=np.round(r["P"], 2).tolist(),
        fibras=[np.round(f, 2).tolist() for f in r["fibras"]],
        medidas=dict(n_fibras=r["n_fibras"], n_finos=r["n_finos"], n_continuados=r["n_soldaduras"],
                     n_pegados=r["n_pega"], n_libres=r["n_puentes"],
                     area_perfil_mm2=round(r["area_perfil"]),
                     abierto_mm2=round(r["area_abierta"]),
                     abierto=round(r["area_abierta"] / r["area_perfil"], 3),
                     abierto_region=round(r["area_abierta"] / r["area_region"], 3),
                     abierto_ventana_mm2=round(r["area_ventana"]),
                     ventana_desde_perfil=r["ventana"]),
    )
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, separators=(",", ":"))
        f.write("\n")


def main():
    global FACTOR, W_PRIM, W_PRIM_MIN, W_PRIM_MAX, SALIDA, LAMINA
    a = sys.argv
    tag = ""
    if "--fuente" in a:
        LAMINA = a[a.index("--fuente") + 1]
    if "--factor" in a:
        FACTOR = float(a[a.index("--factor") + 1])
    if "--w" in a:
        W_PRIM = float(a[a.index("--w") + 1])
        W_PRIM_MIN, W_PRIM_MAX = W_PRIM / 1.2, W_PRIM * 1.45
    if "--tag" in a:
        tag = "_" + a[a.index("--tag") + 1]
        SALIDA = SALIDA.replace(".json", tag + ".json")
    r = generar()
    w = np.concatenate([f[:, 3] for f in r["fibras"]])
    L = sum(_largo(f) for f in r["fibras"])
    print(f"  {r['n_fibras']} filamentos ({r['n_finos']} finos colgados; {r['n_finos_fuera']} finos sueltos fuera), "
          f"{L:.0f} mm de cinta, anchura p10/p50/p90 = {np.percentile(w, 10):.2f}/{np.median(w):.2f}/{np.percentile(w, 90):.2f} mm")
    print(f"  estiron maximo a lo largo de las laminas: {r['n_copia']} mm")
    print(f"  escala {r['escala']:.4f} mm/px; {r['n_pega']} extremos pegados al marco, de ellos "
          f"{r['n_soldaduras']} continuados desde el borde de la lamina; {r['n_puentes']} quedaron libres")
    print(f"  ABIERTO: {r['area_abierta']:.0f} mm2 = {100 * r['area_abierta'] / r['area_perfil']:.0f} % del perfil, "
          f"{100 * r['area_abierta'] / r['area_region']:.0f} % de la region; respira por la ventana {r['area_ventana']:.0f} mm2")
    if "--preview" in sys.argv:
        ruta = os.path.join(DIR, "..", "renders", "build", f"celosia_ala{tag}.png")
        celosia.preview(r, ruta)
        print("  preview", os.path.abspath(ruta))
    else:
        escribir(r, SALIDA)
        print("  escrito", SALIDA)


if __name__ == "__main__":
    main()
