"""El cachete es UNA RAMA: la celosia como rama con extensiones, en 3D.

    python case/cad/celosia.py            -> escribe celosia_rama.json
    python case/cad/celosia.py --preview  -> y ademas renders/build/celosia.png

PROPUESTA (2026-09-05). Lo lee case/renders/imprimir_piel.py, que levanta la
pieza en Blender (tubos de seccion redonda y radio variable, marco de seccion
D, remallado) y la deja lista para imprimir. Ninguna puerta lo corre.

LA FILOSOFIA, dicha por Samuel el 05-09 mirando la cuarta version:
  «toda esta pieza simula un arbol. los cachetes son como ramas (las ramas
  deberian tener una estructura natural de rama) [...] se interpreta como
  una rama con extensiones, todo lo que envuelve al aluminio se comporta
  como un tronco. hasta que no entiendas esto no lograremos el acabado».
La cubierta es el TRONCO (imprimir_piel.py le pone la corteza); cada cachete
es una RAMA que sale del tronco por el hombro del valle: entra gruesa por el
NUDO, cruza el cachete en diagonal hacia el talon como VENA principal, y por
el camino suelta EXTENSIONES --largas hacia la cumbre trasera, cortas hacia el
suelo-- que se parten, se juntan en haces y se funden en el marco dejando
LENTES. Todo de seccion redonda: grueso junto al nudo, fino en las puntas,
unas pasando por encima de otras.

CUATRO VERSIONES EN UN DIA, y las tres primeras eran DIBUJOS PLANOS:
  1. celdas de Voronoi (2bce743): leia a panal.
  2. ramas por colonizacion de espacio (d78c592): un arbol dibujado, ramas
     sueltas que se cruzan. "no esta ni cerca".
  3. fibras de un campo de flujo (73a9bf1): el tejido bueno, pero fibras
     todas iguales, planas, sin nudo, sin tronco. Sin organismo.
  4. esta: el mismo motor de lineas de flujo (Jobard & Lefer 1997), pero el
     campo es RADIAL desde el nudo, el grosor es JERARQUICO (cae con la
     distancia al nudo, la vena va mas gruesa, y a lo largo de cada fibra
     sube y baja: gruesa a media carrera, fina donde se parte), las vecinas
     se ACERCAN hasta fundirse en un haz y luego se separan (bifurcacion),
     cada soldadura lleva su NUDO, y cada fibra ondula en Z para que en los
     cruces una pase por encima de la otra.

Las dos referencias nuevas de Samuel (05-09, noche): el perfil 2D del
cachete --nudo bajo el hombro del valle, vena al talon, marco grueso y
redondo, CUATRO fijaciones en las esquinas-- y la geometria de la celosia
--"variable core thickness", "filament bifurcation point", "integrated nodal
point", "irregular void shape", "interwoven flow path". Mandan sobre
lenguaje, no sobre cotas: la escala de la segunda daria filamentos de 2 mm,
y eso en nylon no es estructura. Los grosores de abajo son de imprimir.

Lo que sale (celosia_rama.json): fibras como polilineas [x, y, z, w] en
coordenadas del perfil (z = relieve sobre el plano medio del cachete, w =
diametro), el eje del marco, los cuatro agujeros y las dos areas de siempre
(lo que se ve, lo que respira). Determinista: misma semilla, mismas fibras.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

DIR = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(DIR, "..")
if CASE not in sys.path:
    sys.path.insert(0, CASE)
import clearance_budget as cb  # noqa: E402

# --- el marco --------------------------------------------------------------
MARCO = 28.0        # mm, ancho del marco: SOLAPE_CUBIERTA fuera del perfil y el
                    # resto dentro, tapando la cara del anillo (20) y casi el
                    # marco de la ventana (26): las fibras nacen del marco, sin
                    # franja de aluminio entre medias (vista en el render, 05-09)
MARCO_E = 11.0      # mm, espesor del marco (seccion D: plano al anillo,
                    # abombado hacia fuera)
MONTAJE_D = 4.5     # mm, pasante para M4, uno en cada esquina (la referencia)
MONTAJE_A = 12.0    # mm, del canto del perfil al eje, en las dos direcciones
SOLAPE_CUBIERTA = 6.0   # mm, = piel_e de piel_organica.scad: el marco del
                        # cachete pisa el canto de la cubierta, como en el despiece

# --- la rama ---------------------------------------------------------------
NUDO = (56.0, 38.0)     # donde entra la rama: LA PUNTA INFERIOR DELANTERA, la
                        # nariz (Samuel, 05-09: "quiero que el punto del que
                        # salen todas las ramificaciones sea la punta inferior
                        # delantera"). Justo dentro del rincon de la region:
                        # ~10 mm de la cara baja y del suelo (marco 28)
NUDO_R = 18.0           # mm, radio del nudo: ahi las fibras no mueren, se funden
# DEL NUDO SALEN TRES, y las demas NACEN MAS ARRIBA (Samuel, 05-09: "mejor
# que salgan varias de ese nodo, unas tres, y luego otras nazcan de algun
# punto mas arriba, cada una en donde va el primer row del rack"): las tres
# primarias, por rumbo desde el nudo (el suelo, la vena a la cumbre, la cara
# baja); el resto brota de una rama que ya pasa por la banda de la fila de
# abajo (BROTE_Y, en mm de altura) y hacia atras muere fundida en su madre.
PRIMARIAS = (2.0, 39.0, 54.0)
BROTE_Y = (28.0, 150.0)
MUERE_ATRAS = 0.6       # x espaciado: hacia atras, una fibra nueva muere en la madre
SOLDADURA_L = 2.5       # x hueco: cuanto se tiende la Y al fundirse en la madre
PRIMARIA_W = 1.3        # las tres del nudo, x esto de gruesas (la vena lleva VENA)
SEPARACION = 12.0       # mm, entre ejes de fibras vecinas, JUNTO al nudo...
SEP_CRECE = 0.25        # ...y crece con la distancia: x(1 + SEP_CRECE*d/250).
                        # La referencia: celdas chicas en el nudo, grandes lejos
NERVIO_NUDO = 8.0       # mm, diametro junto al nudo
NERVIO_PUNTA = 3.6      # mm, diametro en las puntas, lejos
LAMBDA = 95.0           # mm, con que distancia al nudo cae el grosor
VENA = 1.5              # la vena principal, nudo -> cumbre: x esto de gruesa
# (Hubo una RAIZ explicita, un tronco de rama del marco al nudo, mientras el
# nudo flotaba bajo el hombro. Con el nudo en la nariz, a 12 mm del marco y
# con NUDO_R = 18, el nudo mismo se funde con la esquina del marco: la raiz
# sobraba y ademas asomaba por fuera del marco. Fuera.)
VENA_ANG = 39.0         # grados, rumbo de la vena: de la nariz a la cumbre
                        # trasera (P5), la diagonal larga del cachete
VENA_ANCHO = 12.0       # grados a cada lado del rumbo que cuentan como vena
GROSOR_ONDA = 0.18      # fraccion: el grosor sube y baja a lo largo
GROSOR_L = 70.0         # mm, periodo de esa onda
PASO = 2.0              # mm, paso de integracion
ONDA_A = 8.0            # grados, ondulacion de las fibras
ONDA_L = (140.0, 100.0) # mm, longitudes de onda (en y, en x)
GIRO = 6.0              # grados, torsion del abanico, cae con la distancia
# LA PARED: cerca del marco el flujo se hace tangente a el, y las fibras
# corren pegadas al marco antes de fundirse en el, de refilon. Sin esto, las
# que salen del nudo hacia el hombro chocan de frente a 20 mm y mueren cortas,
# y encima del nudo no queda nada (medido: 24 fibras, arriba vacio).
PARED_D = 40.0          # mm desde el marco donde empieza a doblar
PARED_K = 0.9           # cuanto dobla como maximo (1 = nunca llega al marco)
# LOS HACES: las fibras NO mueren por acercarse a otra (MUERE = 0): se funden
# en un haz y, cuando la modulacion las separa, se abren -- la bifurcacion de
# la referencia. Hacia el nudo todas se juntan en pocos brazos gordos, que
# es la jerarquia de una rama sin dibujarla. (Con muerte a 0.38-0.5 del
# espaciado, medido: 15 fibras en trios paralelos y huecos de 30 mm.) Lo
# que gobierna la densidad es solo el sembrado: una semilla vale si no hay
# fibra a menos de NACE x espaciado local.
MUERE = 0.0
NACE = 0.55
MIN_LARGO = 1.8         # x espaciado: mas corta que esto no se queda
# LOS HACES Y LAS LENTES: fibras vecinas giran en sentidos opuestos, se
# acercan hasta fundirse en un haz (o morir soldadas) y se vuelven a abrir.
LENTE_MOD = 6.0         # grados, amplitud (solo ondula: las lentes las
                        # cierran los pellizcos de abajo)
LENTE_L = 75.0          # mm, periodo a lo largo del flujo (radial)
LENTE = 95.0            # mm, entre pellizcos (local: x(0.55 + d/220))
LENTE_JITTER = 0.35
PELLIZCO_SOLAPE = 1.5   # mm, cuanto se meten una en otra al tocarse
PELLIZCO_ORILLA = 30.0  # mm, sin pellizcos a menos de esto de una punta
# LAS PUNTAS entran al marco de refilon (fundir_en_marco): PEGA_L mm mas
# adelante, tangentes. Y una fibra que corre a menos de PEGA_D del marco
# durante PEGA_MAX se funde en el sin esperar a tocarlo.
PEGA_L = 26.0
PEGA_D = 9.0
PEGA_MAX = 70.0
Z_AMP = 1.8             # mm, cuanto ondula cada fibra en profundidad
Z_L = 90.0              # mm, periodo de esa onda
Z_VENA = 2.6            # mm, la vena va por encima
SEMILLA = 17
SALIDA = os.path.join(DIR, "celosia_rama.json")


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


_PERFIL: np.ndarray | None = None      # lo pone generar(); lo lee _campo()
_MARCO = MARCO


def _sep(p: np.ndarray) -> float:
    d = float(np.hypot(*(p - np.array(NUDO))))
    return SEPARACION * (1.0 + SEP_CRECE * d / 250.0)


def _pared(p: np.ndarray):
    """(distancia al marco, normal hacia fuera del tramo mas cercano)."""
    P = _PERFIL
    mejor, n_mejor = np.inf, None
    m = len(P)
    for i in range(m):
        a, b = P[i], P[(i + 1) % m]
        ab = b - a
        t = float(np.clip(((p - a) @ ab) / (ab @ ab), 0.0, 1.0))
        dd = float(np.linalg.norm(p - (a + t * ab)))
        if dd < mejor:
            mejor, n_mejor = dd, _nrm(a, b)
    return mejor - _MARCO, n_mejor


def _campo(p: np.ndarray) -> np.ndarray:
    """Direccion unitaria del flujo en p, SALIENDO del nudo: abanico radial,
    torcido cerca del nudo, ondulado, con la modulacion que hace haces y
    lentes en coordenadas polares (s radial, t de arco), y doblando a
    tangente cerca de la pared."""
    v = p - np.array(NUDO)
    d = float(np.hypot(*v))
    ang = math.atan2(v[1], v[0])
    ang += math.radians(GIRO) * math.exp(-d / 110.0)
    ang += math.radians(ONDA_A) * (math.sin(2 * math.pi * p[1] / ONDA_L[0] + 0.6)
                                   + 0.6 * math.sin(2 * math.pi * p[0] / ONDA_L[1] + 2.1))
    t = math.atan2(v[1], v[0]) * max(d, 1.0)     # arco alrededor del nudo
    ang += math.radians(LENTE_MOD) * (math.sin(2 * math.pi * d / LENTE_L)
                                      * math.sin(math.pi * t / _sep(p)))
    u = np.array([math.cos(ang), math.sin(ang)])
    if _PERFIL is not None:
        db, n = _pared(p)
        if db < PARED_D:
            hacia = float(u @ n)                  # > 0: va contra la pared
            if hacia > 0:
                k = PARED_K * (1.0 - max(db, 0.0) / PARED_D) ** 1.2
                tang = u - hacia * n
                L = np.linalg.norm(tang)
                if L > 1e-6:
                    u = (1.0 - k) * u + k * tang / L
                    u /= np.linalg.norm(u)
    return u


def _es_vena(p: np.ndarray) -> bool:
    v = p - np.array(NUDO)
    a = math.degrees(math.atan2(v[1], v[0]))
    return abs((a - VENA_ANG + 180) % 360 - 180) < VENA_ANCHO


def _grosor(p: np.ndarray, s: float, fase: float, vena: bool) -> float:
    """Diametro en p: cae con la distancia al nudo, sube y baja a lo largo
    (s), y la vena va mas gruesa."""
    d = float(np.hypot(*(p - np.array(NUDO))))
    base = NERVIO_PUNTA + (NERVIO_NUDO - NERVIO_PUNTA) * math.exp(-d / LAMBDA)
    onda = 1.0 + GROSOR_ONDA * math.sin(2 * math.pi * s / GROSOR_L + fase)
    return base * onda * (VENA if vena else 1.0)


def _bezier(A, TA, B, TB, n=8):
    """Curva en S de A a B, tangente a TA al salir y a TB al llegar."""
    k = 0.4 * float(np.hypot(*(B - A)))
    C1, C2 = A + TA * k, B - TB * k
    t = np.linspace(0.0, 1.0, n)[:, None]
    return ((1 - t) ** 3 * A + 3 * (1 - t) ** 2 * t * C1
            + 3 * (1 - t) * t ** 2 * C2 + t ** 3 * B)


def _redondear(P: np.ndarray, r: float, n: int = 6) -> np.ndarray:
    """El contorno P con cada esquina sustituida por un arco de radio r."""
    out = []
    m = len(P)
    for i in range(m):
        a, b, c = P[i - 1], P[i], P[(i + 1) % m]
        u = (a - b) / np.linalg.norm(a - b)
        v = (c - b) / np.linalg.norm(c - b)
        ang = math.acos(np.clip(u @ v, -1, 1))
        # el radio se limita por LONGITUD TANGENTE (0.72 del lado mas corto),
        # no por una fraccion fija: en la nariz (lado de 19) la fraccion 0.45
        # dejaba 8.5 mm de radio, menos que la media anchura del marco (12), y
        # la seccion barrida se cruzaba a si misma (el booleano de los
        # agujeros devolvia un disco). Con 0.72: 13.7, y el vecino cabe.
        t_max = 0.72 * min(np.linalg.norm(a - b), np.linalg.norm(c - b))
        rr = min(r, t_max * math.tan(ang / 2))
        t = rr / math.tan(ang / 2)
        p0, p1 = b + u * t, b + v * t
        bis = (u + v) / np.linalg.norm(u + v)
        centro = b + bis * rr / math.sin(ang / 2)
        a0 = math.atan2(*(p0 - centro)[::-1])
        a1 = math.atan2(*(p1 - centro)[::-1])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(n + 1):
            aa = a0 + da * k / n
            out.append(centro + rr * np.array([math.cos(aa), math.sin(aa)]))
    return np.array(out)


def _inset(P: np.ndarray, d: float) -> np.ndarray:
    """El poligono P (horario) metido d hacia dentro, vertice a vertice."""
    out = []
    m = len(P)
    for i in range(m):
        a, b, c = P[i - 1], P[i], P[(i + 1) % m]
        n1 = _nrm(a, b)
        n2 = _nrm(b, c)
        bis = n1 + n2
        bis /= max(np.linalg.norm(bis), 1e-9)
        out.append(b - bis * d / max(bis @ n1, 0.3))
    return np.array(out)


def _nrm(A, B):
    """Normal hacia FUERA de la arista A->B (el perfil va en sentido horario
    en sam17_case.scad: nrm() alli)."""
    d = B - A
    L = np.linalg.norm(d)
    return np.array([-d[1], d[0]]) / L


def generar(marco=MARCO, sep=SEPARACION, paso=PASO, semilla=SEMILLA, medir=True):
    p = cb.leer_params()
    P = np.array(cb._vertices(p), dtype=float)
    rng = np.random.default_rng(semilla)
    x0, x1 = P[:, 0].min(), P[:, 0].max()
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    area_bbox = (x1 - x0) * (y1 - y0)
    area_perfil = 0.5 * abs(np.sum(P[:, 0] * np.roll(P[:, 1], -1)
                                   - np.roll(P[:, 0], -1) * P[:, 1]))
    nudo = np.array(NUDO)

    global _PERFIL, _MARCO
    _PERFIL, _MARCO = P, marco

    def en_region(q):
        qq = np.asarray(q, dtype=float)[None, :]
        return bool(_dentro(P, qq)[0] and _dist_borde(P, qq)[0] >= marco)

    # --- las fibras: lineas de flujo espaciadas, saliendo del nudo -----------
    # El espaciado es LOCAL (_sep): junto al nudo `sep`, lejos hasta x1.55.
    # Una semilla solo vale a mas de NACE x el espaciado local de cualquier
    # fibra; la muerte por cercania esta apagada (MUERE), ver arriba.
    rej = _Rejilla(sep)
    fibras: list[np.ndarray] = []      # cada una: [x, y] por punto

    def fundir_en_marco(q, u):
        """La punta entra en el marco DE REFILON: una curva tangente desde q
        (rumbo u) hasta un punto medio marco dentro del marco y PEGA_L mas
        adelante, llegando paralela a el. Es como la referencia funde las
        fibras en el marco: no de frente, deslizando."""
        db, n = _pared(q)
        hondo = max(db, 0.0) + marco * 0.5
        tang = u - float(u @ n) * n
        L = float(np.linalg.norm(tang))
        if L < 0.45:                       # llega casi de frente: recta y corta
            return [q + u * hondo]
        tang /= L
        # el tramo tangente se acorta hasta caber: en una esquina 26 mm de
        # deslizamiento cruzan el canto vecino
        for largo_t in (PEGA_L, 0.6 * PEGA_L, 0.3 * PEGA_L, 0.0):
            fin = q + tang * largo_t + n * hondo
            ff = fin[None, :]
            if _dentro(P, ff)[0] and _dist_borde(P, ff)[0] >= 0.3 * marco:
                break
        return [c for c in _bezier(q, u, fin, tang if largo_t > 0 else u, n=8)[1:]]

    def integrar(semilla_pt, signo, i_propia, es_prim=True):
        """Integra desde la semilla en un sentido (+1 aleja del nudo, -1
        acerca). Dentro de NUDO_R se funde en el nudo. Al llegar al marco, o
        tras correr PEGA_MAX pegada a el, se funde en el de refilon. Hacia
        atras, una fibra NO primaria muere al acercarse a otra: nace de ella
        (la punta se suelda tangente despues)."""
        pts = []
        q = np.array(semilla_pt, dtype=float)
        pegada = 0.0
        for _ in range(2000):
            v = _campo(q) * signo
            qm = q + 0.5 * paso * v
            u = _campo(qm) * signo
            q2 = q + paso * u
            if not en_region(q2):
                pts += fundir_en_marco(q, u)
                break
            db, _n = _pared(q2)
            pegada = pegada + paso if db < PEGA_D else 0.0
            if pegada > PEGA_MAX:
                pts += fundir_en_marco(q2, u)
                break
            if float(np.hypot(*(q2 - nudo))) < NUDO_R:
                pts.append(q2)
                if signo < 0:                  # llego al nudo: hasta el centro
                    pts.append(nudo.copy())
                    break
                q = q2
                continue
            muere = MUERE if signo > 0 or es_prim else MUERE_ATRAS
            if muere > 0 and rej.cerca(q2, muere * _sep(q2), salvo=i_propia)[1] >= 0:
                pts.append(q2)
                break
            pts.append(q2)
            q = q2
        return pts

    # semillas: las tres primarias desde el nudo; el resto, brotes en la banda
    cola = [(nudo + NUDO_R * np.array([math.cos(math.radians(a)), math.sin(math.radians(a))]), True)
            for a in PRIMARIAS]
    primaria: list[bool] = []
    while cola:
        s, es_prim = cola.pop(0)
        if not en_region(s) or rej.cerca(s, NACE * _sep(s))[1] >= 0:
            continue
        if not es_prim and not (BROTE_Y[0] <= s[1] <= BROTE_Y[1]):
            continue
        i = len(fibras)
        atras = integrar(s, -1.0, i, es_prim)[::-1]
        adelante = integrar(s, +1.0, i, es_prim)
        linea = np.array(atras + [s] + adelante)
        if len(linea) * paso < MIN_LARGO * sep:
            continue
        fibras.append(linea)
        primaria.append(es_prim)
        for q in linea:
            rej.mete(i, q)
        for j in range(0, len(linea), max(1, int(sep / paso))):
            t = _campo(linea[j])
            n = np.array([-t[1], t[0]])
            sl = _sep(linea[j])
            for lado in (+1.0, -1.0):
                cola.append((linea[j] + n * sl * lado, False))

    # --- ninguna punta suelta: cada extremo que no muere en el marco ni en el
    # nudo se funde en la vecina con una curva tangente al flujo -------------
    extra: list[np.ndarray] = []
    for i, f in enumerate(fibras):
        for extremo, signo in ((f[0], -1.0), (f[-1], +1.0)):
            if (_dist_borde(P, extremo[None, :])[0] < marco + 1.5 * paso
                    or float(np.hypot(*(extremo - nudo))) < NUDO_R + paso):
                continue
            d, k, qn = rej.cerca(extremo, 1.3 * _sep(extremo), salvo=i)
            if k < 0:
                continue
            # la union entra en la madre SOLDADURA_L veces el hueco mas alla
            # del punto mas cercano, siguiendo la madre: una Y tendida, no un
            # munon a 90 grados (visto en el preview, 05-09)
            madre = fibras[k]
            j = int(np.argmin(np.hypot(*(madre - qn).T)))
            paso_m = max(1, int(SOLDADURA_L * max(d, 2.0) / paso))
            j2 = min(max(j + int(signo) * paso_m, 0), len(madre) - 1)
            B = madre[j2]
            extra.append(_bezier(extremo, _campo(extremo) * signo, B,
                                 _campo(B) * signo, n=10))
    soldaduras = len(extra)

    # --- LAS LENTES, por pellizcos ------------------------------------------
    # Dos fibras que corren vecinas se ACERCAN hasta tocarse cada LENTE mm y se
    # vuelven a abrir: eso deja huecos en forma de lente con las dos puntas
    # tangentes, y cada toque es la "bifurcacion" de la referencia leida desde
    # el otro lado. Antes esto eran puentes en S entre fibras, y salian como
    # rayos en zigzag: el hueco de la referencia lo cierran las fibras mismas.
    # Para cada fibra i y cada muestra, su vecina IZQUIERDA (a +n, dentro de un
    # cono de 55 grados, a menos de 3.5 espaciados); cada pasillo largo entre
    # i y una misma j recibe estaciones cada LENTE (local, crece con d), y en
    # cada estacion las dos se desplazan hacia el medio con ventana coseno.
    puntos = {}                                        # (i, k) -> punto
    for i, f in enumerate(fibras):
        for k, q in enumerate(f):
            puntos[(i, k)] = q
    rej2 = _Rejilla(sep)
    for (i, k), q in puntos.items():
        rej2.mete(i * 100000 + k, q)

    def vecina_izq(i, k):
        f = fibras[i]
        q = f[k]
        t = f[min(k + 1, len(f) - 1)] - f[max(k - 1, 0)]
        t /= max(np.linalg.norm(t), 1e-9)
        n = np.array([-t[1], t[0]])
        R = 3.5 * _sep(q)
        mejor = (R, -1, -1)
        kx, ky = rej2._k(q)
        m = int(math.ceil(R / rej2.d))
        for dx in range(-m, m + 1):
            for dy in range(-m, m + 1):
                for cod, qq in rej2.celdas.get((kx + dx, ky + dy), ()):
                    j, kk = divmod(cod, 100000)
                    if j == i:
                        continue
                    dv = qq - q
                    dd = float(np.hypot(*dv))
                    if dd < 1e-6 or dd >= mejor[0] or float(dv @ n) < 0.57 * dd:
                        continue
                    mejor = (dd, j, kk)
        return mejor, n

    desplaza = [np.zeros_like(f) for f in fibras]
    largos = [np.r_[0.0, np.cumsum(np.hypot(*np.diff(f, axis=0).T))] for f in fibras]
    pellizcos = 0
    for i, f in enumerate(fibras):
        muestras = list(range(0, len(f), 2))
        vec = [vecina_izq(i, k) for k in muestras]
        a = 0
        while a < len(muestras):
            j = vec[a][0][1]
            b = a
            while b + 1 < len(muestras) and vec[b + 1][0][1] == j:
                b += 1
            if j >= 0:
                s_a, s_b = largos[i][muestras[a]], largos[i][muestras[b]]
                d_med = float(np.hypot(*(f[muestras[(a + b) // 2]] - nudo)))
                lente = LENTE * (0.55 + d_med / 220.0)
                if s_b - s_a > 0.7 * lente:
                    s_est = s_a + lente * rng.uniform(0.25, 0.55)
                    while s_est < s_b - 0.2 * lente:
                        m = a + int(np.searchsorted(largos[i][muestras[a:b + 1]], s_est))
                        m = min(max(m, a), b)
                        (g, jj, kk), n = vec[m]
                        ki = muestras[m]
                        # ni en las puntas ni junto al nudo: ahi se funden
                        # solas, y un pellizco tuerce la punta
                        lejos = (largos[i][ki] > PELLIZCO_ORILLA
                                 and largos[i][-1] - largos[i][ki] > PELLIZCO_ORILLA
                                 and largos[jj][kk] > PELLIZCO_ORILLA
                                 and largos[jj][-1] - largos[jj][kk] > PELLIZCO_ORILLA)
                        fj = fibras[jj]
                        tj = fj[min(kk + 1, len(fj) - 1)] - fj[max(kk - 1, 0)]
                        ti = f[min(ki + 1, len(f) - 1)] - f[max(ki - 1, 0)]
                        paralelas = abs(float(ti @ tj)) > 0.8 * np.linalg.norm(ti) * np.linalg.norm(tj)
                        wi = _grosor(f[ki], 0.0, 0.0, False)
                        wj = _grosor(fibras[jj][kk], 0.0, 0.0, False)
                        D = 0.5 * (g - 0.5 * (wi + wj) + PELLIZCO_SOLAPE)
                        D = min(max(D, 0.0), 0.33 * g)
                        if D > 0.5 and lejos and paralelas:
                            H = 0.5 * lente
                            for (fi, kc, signo) in ((i, ki, +1.0), (jj, kk, -1.0)):
                                Lf = largos[fi]
                                sc = Lf[kc]
                                sel = np.flatnonzero(np.abs(Lf - sc) < H)
                                peso = np.cos(0.5 * math.pi * (Lf[sel] - sc) / H) ** 2
                                # y se apaga en los ultimos 20 mm: la punta no se tuerce
                                peso *= np.clip(np.minimum(Lf[sel], Lf[-1] - Lf[sel]) / 20.0, 0.0, 1.0)
                                desplaza[fi][sel] += signo * D * peso[:, None] * n
                            pellizcos += 1
                        s_est += lente * (1.0 + LENTE_JITTER * rng.uniform(-1.0, 1.0))
            a = b + 1
    fibras = [f + d for f, d in zip(fibras, desplaza)]
    puentes = pellizcos

    # --- grosor y relieve por punto -----------------------------------------
    def vestir(linea: np.ndarray, fase: float, z_fase: float, vena: bool,
               es_extra: bool, es_prim: bool = False) -> np.ndarray:
        s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(linea, axis=0).T))]
        out = np.empty((len(linea), 4))
        for k, q in enumerate(linea):
            w = _grosor(q, s[k], fase, vena)
            if es_prim and not vena:
                w *= PRIMARIA_W
            z = Z_AMP * math.sin(2 * math.pi * s[k] / Z_L + z_fase)
            if vena:
                z += Z_VENA
            if es_extra:
                w *= 0.85
            out[k] = (q[0], q[1], z, w)
        return out

    salida = []
    for f, es_prim in zip(fibras, primaria):
        mitad = f[len(f) // 2]
        salida.append(vestir(f, rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi),
                             es_prim and _es_vena(mitad), False, es_prim))
    for e in extra:
        salida.append(vestir(e, rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi),
                             False, True))

    # --- el marco y los agujeros -------------------------------------------
    # el marco va de SOLAPE_CUBIERTA fuera del perfil a (marco - SOLAPE) dentro
    eje_marco = _redondear(_inset(P, marco / 2 - SOLAPE_CUBIERTA), r=14.0)
    agujeros = [tuple(q) for q in _inset(P, MONTAJE_A)[[0, 2, 5, 6]]]

    # --- las dos areas, por muestreo ----------------------------------------
    S = np.array([[*ln[k, :2], *ln[k + 1, :2], (ln[k, 3] + ln[k + 1, 3]) / 2]
                  for ln in salida for k in range(len(ln) - 1)])
    ventana = float(p.get("marco_fondo", 26.0))
    N = 120_000 if medir else 4_000      # medir=False: barridos rapidos
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
    return dict(fibras=salida, n_fibras=len(fibras), n_soldaduras=soldaduras,
                n_puentes=puentes, eje_marco=eje_marco, agujeros=agujeros,
                area_perfil=area_perfil,
                area_region=area(en_perfil & (dist >= marco)),
                area_abierta=area(en_perfil & (dist >= marco) & ab_full),
                # lo que respira: abierto sobre la ventana del anillo Y fuera del
                # marco (con marco > ventana, la franja entre los dos la tapa el
                # marco aunque no haya fibra: sin el max() se contaba como aire)
                area_ventana=area(en_perfil & (dist >= max(ventana, marco)) & ab_full),
                ventana=ventana, marco=marco, P=P)


def escribir(r: dict, ruta: str = SALIDA) -> None:
    doc = dict(
        generado_por="celosia.py -- no editar a mano",
        marco=dict(ancho=r["marco"], espesor=MARCO_E, eje=np.round(r["eje_marco"], 2).tolist()),
        agujeros=dict(diametro=MONTAJE_D, centros=np.round(r["agujeros"], 2).tolist()),
        nudo=list(NUDO),
        perfil=np.round(r["P"], 2).tolist(),
        fibras=[np.round(f, 2).tolist() for f in r["fibras"]],
        medidas=dict(n_fibras=r["n_fibras"], n_soldaduras=r["n_soldaduras"],
                     n_puentes=r["n_puentes"],
                     area_perfil_mm2=round(r["area_perfil"]),
                     abierto_mm2=round(r["area_abierta"]),
                     abierto=round(r["area_abierta"] / r["area_perfil"], 3),
                     abierto_ventana_mm2=round(r["area_ventana"]),
                     ventana_desde_perfil=r["ventana"]),
    )
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, separators=(",", ":"))
        f.write("\n")


def preview(r: dict, ruta: str) -> None:
    """Un PNG de la rama en 2D: grosor real, la vena y lo que va por encima
    mas claro. Para mirarla en segundos y no en minutos."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # los ejes llenan la figura: asi los puntos por mm son exactos y los
    # grosores se dibujan a escala (con margenes salian un 30 % gordos)
    W_IN, X0, X1, Y0, Y1 = 10.0, -30.0, 350.0, -30.0, 285.0
    fig = plt.figure(figsize=(W_IN, W_IN * (Y1 - Y0) / (X1 - X0)), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ppmm = W_IN * 72 / (X1 - X0)
    # el marco real: SOLAPE fuera del perfil y (marco - SOLAPE) dentro; entre
    # el marco y la region de las fibras asoma la cara del anillo (gris)
    borde = _redondear(_inset(r["P"], -SOLAPE_CUBIERTA), 14.0 + SOLAPE_CUBIERTA)
    region = _redondear(_inset(r["P"], r["marco"] - SOLAPE_CUBIERTA), 8.0)
    interior = _redondear(_inset(r["P"], r["marco"]), 6.0)
    ax.fill(borde[:, 0], borde[:, 1], color="#f4f4f0")
    ax.fill(region[:, 0], region[:, 1], color="#b9bcc0")
    ax.fill(interior[:, 0], interior[:, 1], color="#e8873a")
    for f in sorted(r["fibras"], key=lambda ln: float(np.mean(ln[:, 2]))):
        for k in range(len(f) - 1):
            z = 0.5 * (f[k, 2] + f[k + 1, 2])
            g = 0.86 + 0.05 * z                   # mas alto = mas claro
            g = min(max(g, 0.7), 1.0)
            ax.plot(f[k:k + 2, 0], f[k:k + 2, 1], color=(g, g, g * 0.98),
                    lw=0.5 * (f[k, 3] + f[k + 1, 3]) * ppmm, solid_capstyle="round")
    # el marco ENCIMA: las puntas se funden dentro de el y no se ven
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    anillo = Path(np.vstack([borde, borde[:1], region[::-1], region[-1:]]),
                  [Path.MOVETO] + [Path.LINETO] * (len(borde) - 1) + [Path.CLOSEPOLY]
                  + [Path.MOVETO] + [Path.LINETO] * (len(region) - 1) + [Path.CLOSEPOLY])
    ax.add_patch(PathPatch(anillo, facecolor="#f4f4f0", edgecolor="none", zorder=3))
    for cx, cy in r["agujeros"]:
        ax.add_patch(plt.Circle((cx, cy), MONTAJE_D / 2, color="#333", zorder=4))
    ax.plot(*NUDO, marker="+", color="#a33", ms=8)
    ax.text(X0 + 5, Y1 - 12, f"rama: {r['n_fibras']} fibras, {r['n_soldaduras']} soldaduras, "
            f"{r['n_puentes']} puentes, abre {100 * r['area_abierta'] / r['area_perfil']:.0f} %",
            fontsize=9, color="#333")
    ax.axis("off")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta)


if __name__ == "__main__":
    r = generar()
    escribir(r)
    print(f"rama: {r['n_fibras']} fibras, {r['n_soldaduras']} soldaduras, "
          f"{r['n_puentes']} puentes, {sum(len(f) - 1 for f in r['fibras'])} segmentos")
    print(f"  perfil {r['area_perfil']:.0f} mm2 | region {r['area_region']:.0f} mm2")
    print(f"  ABIERTO por cachete: {r['area_abierta']:.0f} mm2 = "
          f"{100 * r['area_abierta'] / r['area_perfil']:.1f} % del perfil (lo que se ve)")
    print(f"  y de eso RESPIRA {r['area_ventana']:.0f} mm2 (sobre la ventana del anillo y "
          f"fuera del marco, a >= {max(r['ventana'], r['marco']):.0f} mm)")
    print(f"  escrito {SALIDA}")
    if "--preview" in sys.argv:
        ruta = os.path.join(DIR, "..", "renders", "build", "celosia.png")
        preview(r, ruta)
        print(f"  preview {os.path.abspath(ruta)}")
