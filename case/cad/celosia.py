"""La celosia de las mejillas: RAMAS que nacen del marco y crecen hacia dentro.

    python case/cad/celosia.py            -> escribe celosia_ramas.scad

PROPUESTA (2026-09-05), no artefacto de fabricacion: lo lee piel_organica.scad
y nada mas. Ninguna puerta lo corre todavia.

POR QUE RAMAS Y NO CELDAS. La primera version (commit 2bce743) repartia el
hueco en celdas de Voronoi: parametrica, medible, y leia a PANAL. Samuel,
mirando el render: "la piel con esa forma organica que parece modernista y
parecen ramas de arbol". Ramas: nacen del marco, suben, se abren, se afinan
hacia la punta y se curvan. Eso no es un teselado, es un CRECIMIENTO, y se
genera como tal: colonizacion de espacio (Runions et al. 2007, el algoritmo
con que se simulan arboles y venas). Se siembran puntos de atraccion por el
hueco; desde unas raices en el marco cada nodo crece un paso hacia la media de
los atractores que lo tienen por vecino mas cercano; un atractor alcanzado se
consume. Sale un arbol. Dos cosas encima, porque una celosia no es un arbol:

  * GROSOR de tronco a punta (modelo de tuberia: w_padre^2 = suma de
    w_hijos^2, con tope), para que lea a rama y no a alambre;
  * las PUNTAS SE SUELDAN a la rama vecina mas cercana (anastomosis, como
    la venacion cerrada de una hoja): sin eso cada rama es un voladizo de
    100 mm en nylon de 6, y con eso la red cierra lazos y se sostiene.

Lo que importa de la celosia sigue siendo tres numeros --cuanto abre, cuanto
nervio, cuanto borde-- y los tres siguen siendo parametros. Lo que sale:

  * celosia_ramas        segmentos [x0, y0, x1, y1, w] en coordenadas del
                         perfil (x = fondo, y = alto, mm). piel_organica.scad
                         los dibuja como capsulas y les suelda las horquillas
                         con un cierre morfologico (offset +r, -r).
  * celosia_abierto_mm2  area abierta POR MEJILLA, medida por muestreo: lo
                         que se ve.
  * celosia_abierto_ventana_mm2  lo que RESPIRA: solo sobre la ventana del
                         anillo (detras de la orilla hay 26 mm de aluminio).
                         Es el numero que va al modelo termico.

Determinista: misma semilla, mismas ramas.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from scipy.spatial import cKDTree

DIR = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(DIR, "..")
if CASE not in sys.path:
    sys.path.insert(0, CASE)
import clearance_budget as cb  # noqa: E402

# --- los parametros de la celosia ---------------------------------------
BORDE = 12.0        # mm, marco macizo alrededor de la celosia, desde el perfil
# El primer intento (densidad 320, paso 7, influencia 75, consumo 13, raices
# solo abajo cada 55) dio cinco palos que subian y se paraban: cada atractor
# se consumia en dos pasos y no habia atractores que sobraran para desviar
# nada. Una RED de ramas pide una nube densa de atractores por la que las
# ramas serpenteen, paso corto, y raices por TODO el marco, para que nazcan
# de el por los cuatro lados y se encuentren en el medio.
DENSIDAD = 70.0     # mm2 por atractor: cuanto hueco "pide" una rama
PASO = 5.0          # mm, lo que crece un nodo por iteracion
R_INFLUENCIA = 55.0 # mm, hasta donde un atractor tira de su nodo mas cercano.
                    # Corto ramifica; largo va recto al centroide de la nube.
                    # Si nadie alcanza y quedan atractores, el alcance crece
                    # solo (x1.5) hasta que alguien tire, y vuelve a este
R_CONSUMO = 9.0     # mm, a esa distancia el atractor se da por alcanzado
RAIZ_CADA = 40.0    # mm, separacion de las raices a lo largo de TODO el marco
W_PUNTA = 2.6       # mm, grosor de una rama en su punta
W_MAX = 7.0         # mm, tope del grosor en el tronco
R_SOLDADURA = 18.0  # mm, una punta a menos de esto de otra rama se suelda a ella
PODA = 4            # segmentos: una punta sin soldar mas corta que esto se poda
                    # (lee a espina, no a rama)
SUAVIZADO = 4       # pasadas de suavizado de cada rama: zigzag -> curva
CIERRE = 2.0        # mm, radio del cierre que rellena las horquillas (.scad)
JITTER = 0.12       # ruido en la direccion de crecimiento: rectas -> curvas
SEMILLA = 17
SALIDA = os.path.join(DIR, "celosia_ramas.scad")


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


def generar(borde=BORDE, densidad=DENSIDAD, paso=PASO, r_inf=R_INFLUENCIA,
            r_con=R_CONSUMO, raiz_cada=RAIZ_CADA, w_punta=W_PUNTA, w_max=W_MAX,
            r_sold=R_SOLDADURA, poda=PODA, suavizado=SUAVIZADO, jitter=JITTER,
            semilla=SEMILLA):
    p = cb.leer_params()
    P = np.array(cb._vertices(p), dtype=float)
    rng = np.random.default_rng(semilla)
    x0, x1 = P[:, 0].min(), P[:, 0].max()
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    area_bbox = (x1 - x0) * (y1 - y0)
    area_perfil = 0.5 * abs(np.sum(P[:, 0] * np.roll(P[:, 1], -1)
                                   - np.roll(P[:, 0], -1) * P[:, 1]))

    def en_region(pts):
        return _dentro(P, pts) & (_dist_borde(P, pts) >= borde)

    # --- el area de la region, por muestreo (sirve para todo lo demas) ----
    N = 150_000
    muestra = np.stack([rng.uniform(x0, x1, N), rng.uniform(y0, y1, N)], axis=1)
    en_perfil = _dentro(P, muestra)
    dist = _dist_borde(P, muestra)
    region_m = en_perfil & (dist >= borde)
    area_region = region_m.mean() * area_bbox

    # --- atractores: puntos repartidos por el hueco ------------------------
    n_atr = int(area_region / densidad)
    atr = muestra[region_m][:n_atr].copy()

    # --- raices: por todo el marco, cada raiz_cada a lo largo del perfil ----
    # El perfil va en sentido horario; la normal hacia DENTRO de A->B es
    # (d.y, -d.x). Cada raiz va borde + 0.5 hacia dentro, justo donde el
    # marco macizo acaba y empieza el hueco, para que la rama nazca de el.
    raices = []
    for i in range(len(P)):
        A, B = P[i], P[(i + 1) % len(P)]
        d = B - A
        L = float(np.hypot(*d))
        n_in = np.array([d[1], -d[0]]) / L
        for s in np.arange(raiz_cada / 2, L, raiz_cada):
            raices.append(A + d * (s / L) + n_in * (borde + 0.5))
    raices = np.array(raices)
    raices = raices[en_region(raices)]
    nodos = [r for r in raices]
    padre = [-1] * len(nodos)

    # --- crecimiento: colonizacion de espacio -------------------------------
    n_atr0, iteraciones, motivo = len(atr), 0, "atractores agotados"
    alcance = r_inf
    for iteraciones in range(1, 401):
        arbol = cKDTree(np.array(nodos))
        d, idx = arbol.query(atr, distance_upper_bound=alcance)
        tira: dict[int, list[np.ndarray]] = {}
        for a, (dd, ii) in enumerate(zip(d, idx)):
            if ii == len(nodos):
                continue
            v = atr[a] - nodos[ii]
            nv = np.linalg.norm(v)
            if nv > 1e-9:
                tira.setdefault(int(ii), []).append(v / nv)
        if not tira:
            # nadie alcanza: el alcance crece hasta que alguien tire, y vuelve
            # al nominal en cuanto haya crecido algo. Asi un hueco lejano no
            # para el crecimiento y el alcance normal sigue siendo el corto,
            # que es el que ramifica en vez de ir recto al centroide
            if len(atr) and alcance < 6 * r_inf:
                alcance *= 1.5
                continue
            motivo = "ningun atractor alcanza a un nodo"
            break
        alcance = r_inf
        nuevos = []
        for ii, vs in tira.items():
            v = np.mean(vs, axis=0)
            nv = np.linalg.norm(v)
            if nv < 1e-6:
                continue
            v = v / nv + rng.normal(0.0, jitter, 2)
            v /= np.linalg.norm(v)
            q = nodos[ii] + paso * v
            if en_region(q[None, :])[0]:
                nuevos.append((q, ii))
        if not nuevos:
            motivo = "los atractores se anulan entre si (media cero) o sacan fuera"
            break
        for q, ii in nuevos:
            nodos.append(q)
            padre.append(ii)
        arbol = cKDTree(np.array(nodos))
        dk, _ = arbol.query(atr)
        atr = atr[dk > r_con]
        if len(atr) == 0:
            break
    nodos = np.array(nodos)
    hijos: dict[int, list[int]] = {}
    for i, pa in enumerate(padre):
        if pa >= 0:
            hijos.setdefault(pa, []).append(i)

    # --- suavizado: cada nodo hacia la media de su padre y sus hijos --------
    # El crecimiento a pasos de 5 mm con ruido da un zigzag; una rama
    # modernista es una curva larga. Laplaciano suave, y la topologia no se
    # toca: solo se mueven posiciones. RAICES Y PUNTAS QUIETAS: un laplaciano
    # mueve un extremo libre hacia su unico vecino en cada pasada, o sea que
    # las ramas se RETRAEN despues de haber crecido y dejan vacio lo que ya
    # habian llenado (medido: los huecos del tercer preview eran eso, no
    # atractores sin alcanzar -- se consumian los 582).
    for _ in range(suavizado):
        nuevo = nodos.copy()
        for i in range(len(nodos)):
            if padre[i] < 0 or i not in hijos:
                continue
            vecinos = [nodos[padre[i]]] + [nodos[h] for h in hijos[i]]
            nuevo[i] = 0.65 * nodos[i] + 0.35 * np.mean(vecinos, axis=0)
        nodos = nuevo

    # --- anastomosis: cada punta se suelda a la rama vecina mas cercana ----
    def segmentos_de(vivo):
        return np.array([[*nodos[pa], *nodos[i], 0.0]
                         for i, pa in enumerate(padre) if pa >= 0 and vivo[i]]), \
               [i for i, pa in enumerate(padre) if pa >= 0 and vivo[i]]
    vivo = np.ones(len(nodos), dtype=bool)
    S0, idx0 = segmentos_de(vivo)
    puntas = [i for i in range(len(nodos)) if i not in hijos and padre[i] >= 0]
    soldaduras, soldadas = [], set()
    for t in puntas:
        linaje = set()
        k = t
        for _ in range(5):
            if k < 0:
                break
            linaje.add(k)
            k = padre[k]
        propios = np.array([(padre[i] in linaje) or (i in linaje) for i in idx0])
        d = _dist_segmentos(nodos[t][None, :], S0)[0]
        d[propios] = np.inf
        j = int(np.argmin(d))
        if d[j] <= r_sold:
            A, B = S0[j, 0:2], S0[j, 2:4]
            AB = B - A
            tt = np.clip(((nodos[t] - A) @ AB) / max((AB @ AB), 1e-9), 0.0, 1.0)
            soldaduras.append([*nodos[t], *(A + tt * AB), w_punta])
            soldadas.add(t)

    # --- poda: una punta sin soldar y mas corta que `poda` segmentos se va --
    for t in puntas:
        if t in soldadas:
            continue
        cadena, k = [t], padre[t]
        while k >= 0 and padre[k] >= 0 and len(hijos.get(k, [])) == 1:
            cadena.append(k)
            k = padre[k]
        if len(cadena) < poda:
            vivo[cadena] = False
    hijos = {pa: [h for h in hs if vivo[h]] for pa, hs in hijos.items()}
    hijos = {pa: hs for pa, hs in hijos.items() if hs}

    # --- grosor: modelo de tuberia, de la punta al tronco --------------------
    w = np.full(len(nodos), w_punta)
    for i in range(len(nodos) - 1, -1, -1):          # los hijos tienen indice mayor
        if i in hijos:
            w[i] = min(w_max, float(np.sqrt(sum(w[h] ** 2 for h in hijos[i]))))
    segs = [[*nodos[pa], *nodos[i], w[i]]
            for i, pa in enumerate(padre) if pa >= 0 and vivo[i]]
    S = np.array(segs)
    S = np.vstack([S, np.array(soldaduras)]) if soldaduras else S
    puntas = [t for t in puntas if vivo[t]]

    # --- las dos areas, por muestreo --------------------------------------
    # cubierto = a menos de w/2 de algun segmento (capsulas). El cierre
    # morfologico del .scad rellena horquillas estrechas y quita un poco mas
    # (< 2 %): se declara, no se corrige.
    ventana = float(p.get("marco_fondo", 26.0))
    pts = muestra[en_perfil]
    cubierto = np.zeros(len(pts), dtype=bool)
    for k in range(0, len(pts), 20_000):
        D = _dist_segmentos(pts[k:k + 20_000], S)
        cubierto[k:k + 20_000] = (D <= S[:, 4] / 2.0).any(axis=1)
    ab_full = np.zeros(N, dtype=bool)
    ab_full[np.flatnonzero(en_perfil)] = ~cubierto
    area = lambda m: m.mean() * area_bbox  # noqa: E731
    area_abierta = area(en_perfil & (dist >= borde) & ab_full)
    area_ventana = area(en_perfil & (dist >= ventana) & ab_full)
    return dict(ramas=S, n_raices=len(raices), n_puntas=len(puntas),
                n_soldaduras=len(soldaduras), area_perfil=area_perfil,
                iteraciones=iteraciones, motivo=motivo,
                atractores=(n_atr0, len(atr)),
                area_region=area_region, area_abierta=area_abierta,
                abierto=area_abierta / area_perfil, area_ventana=area_ventana,
                ventana=ventana, borde=borde)


def escribir(r: dict, ruta: str = SALIDA) -> None:
    lineas = ["// GENERADO por celosia.py -- no editar a mano. Ramas como segmentos",
              "// [x0, y0, x1, y1, w]; parametros y medida del area abierta al pie.",
              "celosia_ramas = ["]
    for s in r["ramas"]:
        lineas.append(f"  [{s[0]:.2f},{s[1]:.2f},{s[2]:.2f},{s[3]:.2f},{s[4]:.2f}],")
    lineas += ["];",
               f"celosia_cierre = {CIERRE};",
               f"celosia_borde = {r['borde']};",
               f"celosia_n = {len(r['ramas'])};   // segmentos, {r['n_raices']} raices, "
               f"{r['n_puntas']} puntas, {r['n_soldaduras']} soldadas",
               f"celosia_abierto_mm2 = {r['area_abierta']:.0f};   // por mejilla: lo que se VE",
               f"celosia_abierto = {r['abierto']:.3f};         // fraccion del perfil ({r['area_perfil']:.0f} mm2)",
               f"celosia_abierto_ventana_mm2 = {r['area_ventana']:.0f};   // por mejilla, SOLO sobre la ventana del",
               f"                                     // anillo (a >= {r['ventana']:.0f} del perfil): lo que RESPIRA",
               ""]
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas))


if __name__ == "__main__":
    r = generar()
    escribir(r)
    print(f"celosia de ramas: {len(r['ramas'])} segmentos desde {r['n_raices']} raices; "
          f"{r['n_puntas']} puntas, {r['n_soldaduras']} soldadas a una rama vecina")
    print(f"  crecimiento: {r['iteraciones']} iteraciones, paro por '{r['motivo']}'; "
          f"atractores {r['atractores'][0]} -> quedan {r['atractores'][1]}")
    print(f"  perfil {r['area_perfil']:.0f} mm2 | region {r['area_region']:.0f} mm2")
    print(f"  ABIERTO por mejilla: {r['area_abierta']:.0f} mm2 = {100*r['abierto']:.1f} % del perfil (lo que se ve)")
    print(f"  y de eso RESPIRA {r['area_ventana']:.0f} mm2 (sobre la ventana del anillo, a >= {r['ventana']:.0f} mm)")
    print(f"  escrito {SALIDA}")
