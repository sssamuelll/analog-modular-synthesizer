"""El cachete PLACA PERFORADA: la mascara de material del cachete del
concepto -placa solida menos los huecos de las celdas- llevada tal cual a
nuestro perfil. Giro de direccion (07-09, via vectorizer): tras ver un
render de vena simple Samuel lo quiso "mas relleno, que solo queden los
huecos de los circulitos" y pego cachete_concepto_material.png como el
"asi" (blanco = placa, negro = hueco). Ni kondor_filamentos ni
kondor_bandas aplican a esta lectura: vuelve a ser placa-menos-huecos, pero
esta vez con los huecos REALES del concepto, trazados, no sembrados por
estadistica (ver aprende-la-forma-no-la-recortes).

La fuente es el trazado de vectorizer (D:/Desktop/cachete_placa.json): el
MISMO marco de coordenadas que cachete_concepto.json (recorte 1010x1370, y
hacia abajo) y los mismos 7 nombres de hitos -> el registro MLS de
celosia_calco.py sirve sin tocar nada, asi que este guion IMPORTA sus
funciones en vez de repetirlas.

Construccion: el EXTERIOR es NUESTRA region_celosia real (ya esta en mm, no
hace falta deformarla: deformar la del concepto solo la aproximaria). Los
34 huecos del concepto se deforman con el mismo campo MLS que calco.py
valido en 0 pliegues. imprimir_piel.py arma la pieza como un CSG limpio
(prisma menos prismas, booleano EXACT) sin remallado agresivo: el hueco
tiene que salir nitido, no una hebra.

RELIEVE EN Z (07-09, via vectorizer, aprobado por Samuel): la placa plana
"se volaba el detalle de la dimension Z". Las lineas grises del concepto
son el sombreado de un lomo redondeado: cada banda sube desde el borde del
hueco (t_borde, delgado) y se aplana en el centro (t_max, el espesor de
hoy). Este guion solo decide el preset (A/B/C, la anchura `w` de la
caida) y pasa los huecos ya deformados en mm; imprimir_piel.py talla el
lomo esculpiendo la malla directo (remalla fino + cada vertice por su
normal segun la distancia en XY al hueco mas cercano). Un primer intento
con un solido "campo de alturas" y booleano EXACT revento el solver de
Blender (out of memory, 07-09) -- las mesetas a espesor constante son
enormes zonas coplanares, el peor caso para ese solver.
"""
import json
import os
import sys

import numpy as np

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)
import celosia  # noqa: E402
from celosia_calco import INSET_HITOS, ORDEN, _area, cb, controles, mls, offset  # noqa: E402

PLACA = os.environ.get("CACHETE_PLACA", r"D:\Desktop\cachete_placa.json")
PERFIL = os.environ.get("CACHETE_PERFIL", r"D:\Desktop\cachete_perfil.json")
SALIDA = os.path.join(DIR, "celosia_placa.json")

FONDO = 3.0    # mm de espesor de la placa (igual que la cinta del ala) = t_max
VOXEL = 0.3    # mm, remallado fino al fundir con el marco: que el hueco
               # no salga romo

T_BORDE = 1.0        # mm, espesor del lomo justo en el borde del hueco
PRESETS = {"A": 1.0, "B": 2.0, "C": 3.0}   # mm, anchura de la caida `w`
DELTA_HUECOS = 0.0   # mm, crecimiento de cada hueco hacia fuera (Samuel,
                     # 07-09: cerrar el 8 % que le falta al termico)


def _leer_perfil() -> dict:
    with open(PERFIL, encoding="utf-8") as f:
        return json.load(f)




def _autointerseccion(Q: np.ndarray) -> bool:
    """Fuerza bruta O(n^2): algun tramo se cruza con otro no vecino."""
    def lado(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def cruzan(a, b, c, d):
        d1, d2 = lado(a, b, c), lado(a, b, d)
        d3, d4 = lado(c, d, a), lado(c, d, b)
        return d1 * d2 < 0 and d3 * d4 < 0

    n = len(Q)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if cruzan(Q[i], Q[(i + 1) % n], Q[j], Q[(j + 1) % n]):
                return True
    return False


def generar(medir=True, preset="B", delta=DELTA_HUECOS):
    with open(PLACA, encoding="utf-8") as f:
        c = json.load(f)
    W, H = c["recorte"]["ancho"], c["recorte"]["alto"]

    def voltea(xy):
        xy = np.asarray(xy, float)
        return np.stack([W - xy[..., 0], H - xy[..., 1]], axis=-1)

    P = np.array(cb._vertices(cb.leer_params()), float)
    S = voltea([c["hitos"][h] for h in ORDEN])
    T = offset(P, INSET_HITOS)
    assert len(T) == 6, f"a {INSET_HITOS} mm el perfil tiene {len(T)} esquinas, no 6"
    Pc, Qc = controles(S, T)

    exterior = np.array(_leer_perfil()["region_celosia"], float)

    huecos_px = [np.asarray(h["poligono"], float) for h in c["huecos"]]
    tipos = [h["tipo"] for h in c["huecos"]]
    todos = np.concatenate(huecos_px)
    XY = mls(Pc, Qc, voltea(todos))
    huecos_mm, k = [], 0
    for hp in huecos_px:
        n = len(hp)
        huecos_mm.append(XY[k:k + n])
        k += n
    cruces = [i for i, hp in enumerate(huecos_mm) if _autointerseccion(hp)]
    huecos_ok = [hp for i, hp in enumerate(huecos_mm) if i not in cruces]
    if delta:
        # offset() empuja hacia DENTRO con d positivo (reduce el area
        # encerrada); para CRECER un hueco hace falta lo contrario.
        huecos_ok = [offset(hp, -delta) for hp in huecos_ok]

    # --- deformacion, medida igual que celosia_calco.py ----------------------
    h_ = 2.0
    G = np.array([[x, y] for x in np.arange(S[:, 0].min(), S[:, 0].max(), 25.0)
                  for y in np.arange(S[:, 1].min(), S[:, 1].max(), 25.0)])
    G = G[celosia._dentro(S, G)]
    fx = (mls(Pc, Qc, G + [h_, 0]) - mls(Pc, Qc, G - [h_, 0])) / (2 * h_)
    fy = (mls(Pc, Qc, G + [0, h_]) - mls(Pc, Qc, G - [0, h_])) / (2 * h_)
    J = np.stack([fx, fy], axis=-1)
    det = np.linalg.det(J)
    deform = dict(pliegues=int((det <= 0).sum()), det_min=float(det.min()))

    # --- marco y agujeros: igual que celosia.py / celosia_calco.py -----------
    marco = celosia.MARCO
    eje_marco = celosia._redondear(celosia._inset(P, marco / 2 - celosia.SOLAPE_CUBIERTA), r=14.0)
    agujeros = [tuple(q) for q in celosia._inset(P, celosia.MONTAJE_A)[[0, 2, 5, 6]]]

    # --- areas: exactas por poligono, no muestreadas por segmento -----------
    x0, x1 = P[:, 0].min(), P[:, 0].max()
    y0, y1 = P[:, 1].min(), P[:, 1].max()
    area_bbox = (x1 - x0) * (y1 - y0)
    rng = np.random.default_rng(3)
    N = 120_000 if medir else 4_000
    muestra = np.stack([rng.uniform(x0, x1, N), rng.uniform(y0, y1, N)], axis=1)
    en_perfil = celosia._dentro(P, muestra)
    dist = celosia._dist_borde(P, muestra)
    ab = np.zeros(N, dtype=bool)
    for hp in huecos_ok:
        ab |= celosia._dentro(hp, muestra)
    ventana = float(cb.leer_params().get("marco_fondo", 26.0))
    area = lambda m: m.mean() * area_bbox  # noqa: E731

    return dict(exterior=exterior, huecos=huecos_ok, tipos=tipos, cruces=cruces,
                eje_marco=eje_marco, agujeros=agujeros, area_perfil=_area(P),
                area_region=area(en_perfil & (dist >= marco)),
                area_abierta=area(en_perfil & (dist >= marco) & ab),
                area_ventana=area(en_perfil & (dist >= max(ventana, marco)) & ab),
                ventana=ventana, marco=marco, P=P, deform=deform,
                preset=preset, relieve_w=PRESETS[preset], delta=delta)


def escribir(r: dict, ruta: str = SALIDA) -> None:
    doc = dict(
        generado_por="celosia_placa.py -- no editar a mano",
        fuente=PLACA,
        tipo="placa",
        fondo=FONDO,
        voxel=VOXEL,
        relieve=dict(preset=r["preset"], w=r["relieve_w"], t_borde=T_BORDE, t_max=FONDO),
        delta_huecos=r["delta"],
        marco=dict(ancho=r["marco"], espesor=celosia.MARCO_E, eje=np.round(r["eje_marco"], 2).tolist()),
        agujeros=dict(diametro=celosia.MONTAJE_D, centros=np.round(r["agujeros"], 2).tolist()),
        nudo=list(celosia.NUDO),
        perfil=np.round(r["P"], 2).tolist(),
        exterior=np.round(r["exterior"], 2).tolist(),
        huecos=[np.round(hp, 2).tolist() for hp in r["huecos"]],
        medidas=dict(
            n_huecos=len(r["huecos"]), huecos_excluidos_autointerseccion=len(r["cruces"]),
            area_perfil_mm2=round(r["area_perfil"]),
            abierto_mm2=round(r["area_abierta"]),
            abierto=round(r["area_abierta"] / r["area_perfil"], 3),
            abierto_region=round(r["area_abierta"] / r["area_region"], 3),
            abierto_ventana_mm2=round(r["area_ventana"]),
            ventana_desde_perfil=r["ventana"],
            deformacion={k: round(v, 3) for k, v in r["deform"].items()},
        ),
    )
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, separators=(",", ":"))
        f.write("\n")


def _preview(r: dict, ruta: str) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPoly

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.add_patch(MplPoly(r["exterior"], closed=True, facecolor="white", edgecolor="none"))
    for hp in r["huecos"]:
        ax.add_patch(MplPoly(hp, closed=True, facecolor="black", edgecolor="none"))
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.set_xlim(r["P"][:, 0].min() - 10, r["P"][:, 0].max() + 10)
    ax.set_ylim(r["P"][:, 1].min() - 10, r["P"][:, 1].max() + 10)
    ax.set_aspect("equal")
    ax.axis("off")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=150, bbox_inches="tight", facecolor="black")
    plt.close(fig)


def main():
    preset = "B"
    if "--preset" in sys.argv:
        preset = sys.argv[sys.argv.index("--preset") + 1].upper()
    delta = DELTA_HUECOS
    if "--delta" in sys.argv:
        delta = float(sys.argv[sys.argv.index("--delta") + 1])
    r = generar(preset=preset, delta=delta)
    n_celda = sum(1 for t in r["tipos"] if t == "celda")
    n_vano = sum(1 for t in r["tipos"] if t == "vano")
    print(f"  {len(r['huecos'])} huecos ({n_celda} celda / {n_vano} vano de {len(r['tipos'])} trazados), "
          f"{len(r['cruces'])} excluidos por autointerseccion tras la deformacion")
    print(f"  deformacion: det min {r['deform']['det_min']:.4f} ({r['deform']['pliegues']} pliegues)")
    print(f"  ABIERTO: {r['area_abierta']:.0f} mm2 = {100 * r['area_abierta'] / r['area_perfil']:.0f} % del perfil, "
          f"{100 * r['area_abierta'] / r['area_region']:.0f} % de la region; "
          f"respira por la ventana {r['area_ventana']:.0f} mm2")
    print(f"  relieve preset {r['preset']}: w={r['relieve_w']} mm, t_borde={T_BORDE} mm, t_max={FONDO} mm")
    if r["delta"]:
        print(f"  huecos crecidos {r['delta']:.2f} mm por lado")
    if "--preview" in sys.argv:
        ruta = os.path.join(DIR, "..", "renders", "build", "celosia_placa.png")
        _preview(r, ruta)
        print("  preview", os.path.abspath(ruta))
    else:
        salida = SALIDA
        if "--tag" in sys.argv:
            salida = os.path.join(DIR, f"celosia_placa_{sys.argv[sys.argv.index('--tag') + 1]}.json")
        escribir(r, salida)
        print("  escrito", salida)


if __name__ == "__main__":
    main()
