"""Las piezas de la piel LISTAS PARA IMPRIMIR: el cachete y la cubierta,
levantadas en Blender y comprobadas como las mira un servicio.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P imprimir_piel.py

UNA SOLA MASA (ficha 7, A, firmada el 2026-10-09). La cubierta y el marco del
cachete eran dos tubos uno al lado del otro; en el concepto la celosia nace del
borde de la cubierta. Ahora:

  * LA CUBIERTA es la lamina de 6 mm de piel_organica.scad (de nariz a talon
    por el techo, de un anillo al otro) mas el ROLLO de cada costado: su borde
    se enrolla sobre la cara del anillo, entra W y acaba en una nariz redonda.
    Engorda abajo y adelgaza arriba. La geometria del rollo la escribe
    case/cad/piel_borde.py en piel_borde.json, en rebanadas; aqui se extruyen
    y se funden con la lamina en un remallado.
  * EL CACHETE es la celosia de celosia_placa.json --la placa del concepto,
    PESTANA_T de fondo, apoyada en la cara del anillo-- mas la BASE, que pone
    el borde de abajo con la misma seccion que el rollo (la cubierta baja desde
    arriba y un rollo por abajo barreria la celosia). Debajo del rollo la placa
    hace de pestana: el rollo la tapa, con HOLGURA entre los dos, y la celosia
    sale de debajo de la nariz. Dos piezas espejo, cachete_der y cachete_izq.
  * El RELIEVE de la placa (el lomo de cada banda, preset de celosia_placa)
    mueve solo la cara de arriba y la de abajo, en Z: las paredes de los
    huecos se quedan rectas (ficha 5: empujarlas por su normal las dejaba
    picadas).

LO ESCOGIDO (Samuel, 10-10, en el acta): el cachete lleva el lomo HONDO de la
ficha 9 y la cubierta la VETA HONDA de la ficha 8. Para comparar con lo de
antes: PIEL_RELIEVE=hoy (el relieve B de celosia_placa) o suave|medio, y
PIEL_CORTEZA=lisa|veta|veta_marcada|ruido. PIEL_SALIDA manda las STL a otra
carpeta y PIEL_SOLO=cachete|cubierta fabrica solo esa pieza.

Comprobaciones: malla cerrada, tamano contra dos bandejas --MJF 5200 (380 x 284
x 380) y SLS P 770 (700 x 380 x 580), cifras de catalogo sin hoja en el repo--,
gramos en PA12 (1.01 g/cm3) y, desde la ficha 16, las dos reglas de
piel_choques.py: UNA ISLA por pieza y NINGUNA pieza dentro de otra.

Salida: case/print/piel/{cachete_der,cachete_izq,cubierta}.stl. Artefactos de
salida, como los DXF del laser; los regenera este guion.
"""
import json
import os
import subprocess
import sys

import bmesh
import bpy
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(AQUI, "..", "cad")
CRUDO = os.path.join(AQUI, "build", "piel")
SALIDA = os.path.join(AQUI, "..", "print", "piel")
OPENSCAD = r"C:\Program Files\OpenSCAD\openscad.exe"
SCAD = os.path.join(CAD, "piel_organica.scad")
RAMA = os.environ.get("PIEL_RAMA", os.path.join(CAD, "celosia_placa.json"))
BORDE = os.path.join(CAD, "piel_borde.json")
CORTEZA = os.environ.get("PIEL_CORTEZA", "veta_honda")   # ficha 8, escogida el 10-10
SALIDA = os.environ.get("PIEL_SALIDA", SALIDA)   # variantes para escoger, fuera del repo
# EL LOMO de la ficha 9, en tres grados para escoger mirando (PIEL_RELIEVE).
# Cada banda sube de LOMO_BORDE junto al hueco, en cuarto de circulo de radio
# `rho`, hasta t_max: la que mide menos de 2 rho de ancho no llega arriba, asi
# que las finas quedan por debajo de las anchas sin decirselo a nadie. La media
# banda tipica mide 2,8 mm (p50 en la cresta, 09-10): pico tipico 4,0 / 5,2 /
# 6,4 mm. Con mas, la banda fina se vuelve aleta ("ala, no costillas"). Sin
# PIEL_RELIEVE, el hondo, que escogio Samuel el 10-10; PIEL_RELIEVE=hoy da el
# relieve B de celosia_placa.
GRADOS = {"suave": dict(rho=3.5, t_max=4.0), "medio": dict(rho=4.5, t_max=5.5),
          "hondo": dict(rho=5.5, t_max=7.0)}
GRADO = os.environ.get("PIEL_RELIEVE", "hondo")   # ficha 9, escogido el 10-10; "hoy" = relieve B
if GRADO not in (*GRADOS, "hoy"):
    raise SystemExit(f"PIEL_RELIEVE={GRADO}: tiene que ser hoy, {', '.join(GRADOS)}")
LOMO_BORDE = 2.0         # mm junto al hueco
LOMO_ALISADO = 12        # pasadas de vecinos sobre la malla de 0,5 mm: redondea la cresta
# LA VETA de la ficha 8: surcos a lo largo de la pieza, cada uno a una
# distancia del canto de su franja medida EN EL PERFIL (veta()). hondo y ancho
# en mm; niveles: a que distancia del canto va cada surco. Si salen parejos,
# pana. veta_marcada es la que se acerca al concepto (Samuel, 10-10: «la veta
# del concept es super marcada, parece el tronco de un arbol digital»): surcos
# anchos y juntos, que dejan lomos redondos entre ellos. Se ensena; no esta
# escogida.
VETAS = {"veta": dict(hondo=0.5, ancho=1.0, meandro=1.2,
                     niveles=(3.5, 6.0, 9.0, 12.5, 16.5, 21.0, 26.0, 32.0)),
         "veta_honda": dict(hondo=0.9, ancho=1.4, meandro=1.6,
                           niveles=(3.5, 6.5, 10.0, 14.0, 18.5, 23.5, 29.0, 35.0)),
         "veta_marcada": dict(hondo=1.8, ancho=2.6, meandro=2.4,
                             niveles=(4.0, 9.0, 14.5, 20.5, 27.0, 34.0, 41.5, 49.5))}
if CORTEZA not in (*VETAS, "lisa", "ruido"):
    raise SystemExit(f"PIEL_CORTEZA={CORTEZA}: tiene que ser lisa, ruido o {', '.join(VETAS)}")
VETA_APAGADO = (1.5, 3.5)   # mm del canto: dentro de esto, el canto limpio
SEMILLA_VETA = 17

VOXEL_CUBIERTA = 0.6     # mm; lamina de 6 y rollo de 9.5 a 13. Mueve cada cara
                         # hasta medio voxel: con 0.8 se comia la holgura del labio
SUAVIZADO = (0.5, 4)     # factor, iteraciones
DECIMAR = 0.35
BANDEJAS = {"MJF 5200": (380.0, 284.0, 380.0), "SLS P 770": (700.0, 380.0, 580.0)}
# la corteza de ruido, solo con PIEL_CORTEZA=ruido: PLIEGUES anchos, VETAS_RUIDO
# largas a lo largo del perfil y GRANO fino, sobre la cara exterior de la lamina
PLIEGUES = dict(escala=58.0, estira=(1.6, 1.6, 1.0), fuerza=11.0, medio=0.3, hondura=1)
VETAS_RUIDO = dict(escala=16.0, estira=(4.0, 4.0, 1.0), fuerza=3.0, medio=0.5, hondura=1)
GRANO = dict(escala=6.0, estira=(1.0, 1.0, 1.0), fuerza=0.7, medio=0.5, hondura=1)


def exportar_scad(pieza: str) -> str:
    os.makedirs(CRUDO, exist_ok=True)
    stl = os.path.join(CRUDO, pieza + ".stl")
    fuentes = max(os.path.getmtime(os.path.join(CAD, f)) for f in
                  ("piel_organica.scad", "sam17_case.scad", "params.scad"))
    if not (os.path.exists(stl) and os.path.getmtime(stl) >= fuentes):
        print("exportando", pieza, flush=True)
        r = subprocess.run([OPENSCAD, "-o", stl, "-D", f'PART="{pieza}"', SCAD],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            raise SystemExit(f"OpenSCAD fallo en {pieza}")
    return stl


def importar(stl: str):
    bpy.ops.wm.stl_import(filepath=stl)
    return bpy.context.selected_objects[0]


def activo(obj) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def aplicar(obj, nombre: str) -> None:
    activo(obj)
    bpy.ops.object.modifier_apply(modifier=nombre)


def unir(objs: list):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def remallar(obj, voxel: float, suavizado=SUAVIZADO, decimar=DECIMAR) -> None:
    m = obj.modifiers.new("remallar", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    m.use_smooth_shade = True
    aplicar(obj, "remallar")
    s = obj.modifiers.new("suavizar", "SMOOTH")
    s.factor, s.iterations = suavizado
    aplicar(obj, "suavizar")
    d = obj.modifiers.new("decimar", "DECIMATE")
    d.ratio = decimar
    aplicar(obj, "decimar")


def _normales_fuera(ob) -> None:
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def prisma(anillos, nombre: str, z0: float, z1: float):
    """Un poligono (con sus agujeros) extruido de z0 a z1. Curva 2D con
    relleno: los anillos interiores restan solos."""
    cu = bpy.data.curves.new(nombre, "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = (z1 - z0) / 2.0
    for anillo in anillos:
        sp = cu.splines.new("POLY")
        sp.points.add(len(anillo) - 1)
        sp.use_cyclic_u = True
        for p, (x, y) in zip(sp.points, anillo):
            p.co = (x, y, 0.0, 1.0)
    ob = bpy.data.objects.new(nombre, cu)
    bpy.context.collection.objects.link(ob)
    ob.location.z = (z0 + z1) / 2.0
    activo(ob)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.view_layer.objects.active
    _normales_fuera(ob)
    return ob


def losas(rebanadas, z_base: float, signo: int, nombre: str):
    """Las rebanadas de piel_borde.json apiladas en Z a partir de z_base
    (signo +1: hacia +Z, lado derecho; -1: lado izquierdo). Cada una se solapa
    0.02 con la siguiente para que el remallado las funda en un solido."""
    piezas = []
    for k, reb in enumerate(rebanadas):
        a = z_base + signo * reb["v0"]
        b = z_base + signo * reb["v1"]
        lo, hi = min(a, b) - 0.02, max(a, b) + 0.02
        for j, pol in enumerate(reb["poligonos"]):
            piezas.append(prisma(pol, f"{nombre}_{k}_{j}", lo, hi))
    ob = unir(piezas)
    ob.name = nombre
    return ob


# --- EL CACHETE --------------------------------------------------------------
def placa(exterior, huecos, z0: float, fondo: float):
    """Una PLACA perforada: el exterior solido menos los huecos, un CSG
    (booleano EXACT) sin remallado previo -- el hueco tiene que salir
    nitido, no una hebra (Samuel, 07-09: "que solo queden los huecos de
    los circulitos")."""
    base = prisma(exterior, "placa", z0 - fondo / 2.0, z0 + fondo / 2.0)
    cortes = [prisma([h], f"hueco{i}", z0 - fondo / 2.0 - 3.0, z0 + fondo / 2.0 + 3.0)
              for i, h in enumerate(huecos)]
    cortes_obj = unir(cortes)
    b = base.modifiers.new("huecos", "BOOLEAN")
    b.operation = "DIFFERENCE"
    b.solver = "EXACT"
    # use_self: dos huecos de celosia_placa.json (el 5 y el 32) se solapan
    # 0.5 mm2 desde que crecieron 0.3 por lado, y el cortador queda cruzado
    # consigo mismo. Sin esto el EXACT devolvia una placa VACIA sin error, y
    # el MANIFOLD la devolvia sin cortar (medido 09-10).
    b.use_self = True
    b.object = cortes_obj
    bm = bmesh.new()
    bm.from_mesh(base.data)
    v_base = bm.calc_volume()
    bm.free()
    aplicar(base, "huecos")
    bpy.data.objects.remove(cortes_obj, do_unlink=True)
    _normales_fuera(base)
    # guarda: la placa tiene que salir con los huecos cortados, ni vacia ni
    # entera. Una placa que desaparece pasa todas las demas comprobaciones.
    area = sum(0.5 * abs(np.dot(np.asarray(h)[:, 0], np.roll(np.asarray(h)[:, 1], 1))
                         - np.dot(np.asarray(h)[:, 1], np.roll(np.asarray(h)[:, 0], 1)))
               for h in huecos)
    esperado = v_base - area * fondo
    bm = bmesh.new()
    bm.from_mesh(base.data)
    v = bm.calc_volume()
    bm.free()
    if abs(v - esperado) > 0.02 * esperado:
        raise SystemExit(f"ROJO: la placa salio con {v/1000:.1f} cm3 y con los huecos cortados "
                         f"deberia tener {esperado/1000:.1f}")
    return base


def _distancia_a_huecos(xy: np.ndarray, huecos, w: float) -> np.ndarray:
    """Distancia (XY) de cada punto al segmento mas cercano de CUALQUIER
    hueco, recortada a `w`. Filtra por bbox de cada hueco antes de medir
    -- sin esto, 34 huecos x cientos de miles de vertices del remallado
    fino revento la memoria de Blender (07-09)."""
    sys.path.insert(0, CAD)
    import celosia
    dmin = np.full(len(xy), w + 10.0)
    margen = w + 2.0
    for hp in huecos:
        H = np.asarray(hp, dtype=float)
        x0, y0 = H[:, 0].min() - margen, H[:, 1].min() - margen
        x1, y1 = H[:, 0].max() + margen, H[:, 1].max() + margen
        cerca = (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)
        if not cerca.any():
            continue
        dmin[cerca] = np.minimum(dmin[cerca], celosia._dist_borde(H, xy[cerca]))
    return np.minimum(dmin, w)


def relieve(ob, huecos, t_borde: float, t_max: float, w: float, voxel: float = 0.6):
    """El lomo redondeado de cada banda, ESCULPIDO: remalla fino y baja la cara
    de arriba (y sube la de abajo) segun la distancia en XY al hueco mas
    cercano: t_borde junto al hueco, t_max a `w` de el. Solo en Z, y en
    proporcion a cuanto mira la cara hacia arriba o abajo: las paredes de los
    huecos no se mueven. Antes cada vertice iba por su normal, y las paredes
    se empujaban de lado y salian picadas (ficha 5, 09-10)."""
    m = ob.modifiers.new("relieve_fino", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    aplicar(ob, "relieve_fino")
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    xy = np.array([(v.co.x, v.co.y) for v in bm.verts])
    d = _distancia_a_huecos(xy, huecos, w)
    z = t_borde + (t_max - t_borde) * np.sqrt(np.clip(1 - (1 - d / w) ** 2, 0.0, None))
    disp = (z - t_max) / 2.0
    for v, dz in zip(bm.verts, disp):
        v.co.z += v.normal.z * float(dz)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def _labio(xy: np.ndarray, borde: dict) -> np.ndarray:
    """Cuanto queda cada punto MAS ALLA de la nariz del labio (negativo:
    debajo del labio o de la base). W varia con la altura como en
    piel_borde.params_en, y se mide sobre el contorno real del anillo."""
    p = borde["params"]
    P = np.asarray(borde["perfil_real"], dtype=float)
    alto = np.asarray(borde["perfil"], dtype=float)[:, 1].max()
    d = np.full(len(xy), np.inf)
    y_cerca = np.zeros(len(xy))
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        ab = b - a
        t = np.clip(((xy - a) @ ab) / (ab @ ab), 0.0, 1.0)
        q = a + t[:, None] * ab
        di = np.linalg.norm(xy - q, axis=1)
        mejor = di < d
        d[mejor], y_cerca[mejor] = di[mejor], q[mejor, 1]
    s = np.clip(y_cerca / alto, 0.0, 1.0)
    s = s * s * (3 - 2 * s)
    W = p["W_ABAJO"] + (p["W_ARRIBA"] - p["W_ABAJO"]) * s
    return d - W - p["HOLGURA"]


def lomo(ob, huecos, borde: dict, grado: dict, voxel: float = 0.5):
    """La ficha 9: el lomo de cada banda, ESCULPIDO solo hacia fuera. La
    cara que apoya en el anillo se queda en z = 0 y cada vertice sube en
    proporcion (z * t / PESTANA_T), asi que las paredes de los huecos siguen
    verticales. Bajo el labio la placa no pasa de PESTANA_T; mas alla de la
    nariz, el labio cuenta como un borde mas, de PESTANA_T de alto."""
    pt = borde["params"]["PESTANA_T"]
    m = ob.modifiers.new("lomo_fino", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    aplicar(ob, "lomo_fino")
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    xy = co[:, :2]
    rho, t_max = grado["rho"], grado["t_max"]
    h = _distancia_a_huecos(xy, huecos, rho)
    dl = _labio(xy, borde)

    def cuarto(d, e):
        f = np.sqrt(np.clip(1.0 - (1.0 - np.minimum(d / rho, 1.0)) ** 2, 0.0, 1.0))
        return e + (np.maximum(t_max, e) - e) * f

    # fuera del labio, la nariz es un borde mas, de PESTANA_T de alto (la
    # banda que llega al labio se mete debajo sin escalon)
    lab = np.where(dl > 0, dl, np.inf)
    t = np.where(dl > 0, cuarto(np.minimum(h, lab), np.where(lab < h, pt, LOMO_BORDE)),
                 np.minimum(cuarto(h, LOMO_BORDE), pt))
    # la cresta de una banda fina es una arista (los dos cuartos de circulo se
    # cortan en el eje): se alisa como un escalar sobre la malla, a pasadas de
    # vecinos, y bajo el labio se vuelve a recortar
    E = np.empty(len(ob.data.edges) * 2, dtype=np.int64)
    ob.data.edges.foreach_get("vertices", E)
    E = E.reshape(-1, 2)
    vecinos = np.bincount(E.ravel(), minlength=len(t)).astype(float)
    for _ in range(LOMO_ALISADO):
        s = (np.bincount(E[:, 0], weights=t[E[:, 1]], minlength=len(t))
             + np.bincount(E[:, 1], weights=t[E[:, 0]], minlength=len(t)))
        t = (t + s) / (1.0 + vecinos)
    t = np.where(dl > 0, t, np.minimum(t, pt))
    # en coordenadas del MUNDO: la malla es local a un origen en z = pt/2, y
    # escalar en local engordaba la placa hacia los dos lados (medio t por
    # debajo de la cara del anillo, visto el 09-10 en la cota z del STL)
    z0 = ob.location.z
    co[:, 2] = (co[:, 2] + z0) * t / pt - z0
    ob.data.vertices.foreach_set("co", co.ravel())
    ob.data.update()
    return ob


def cachete(borde: dict):
    with open(RAMA, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("tipo") != "placa":
        raise SystemExit(f"ROJO: {RAMA} no es una placa: el cachete de una sola masa "
                         f"(ficha 7) se arma sobre la placa del concepto")
    p = borde["params"]
    # los huecos no pueden asomar donde va la base ni bajo la parte maciza de
    # la pestana: piel_borde los deja desde HUECOS_DESDE
    P = np.array(borde["perfil"])
    hx = np.vstack([np.asarray(h) for h in d["huecos"]])
    sys.path.insert(0, CAD)
    import celosia
    cerca = float(celosia._dist_borde(P, hx).min())
    if cerca < p["HUECOS_DESDE"]:
        raise SystemExit(f"ROJO: un hueco llega a {cerca:.1f} mm del perfil; la pestana "
                         f"es maciza hasta {p['HUECOS_DESDE']}")
    pt = p["PESTANA_T"]
    pl = placa(borde["placa_exterior"][0], d["huecos"], pt / 2.0, pt)
    rv = d.get("relieve")
    if GRADO in GRADOS:
        lomo(pl, d["huecos"], borde, GRADOS[GRADO])
    elif rv:
        if rv["t_max"] > pt + 1e-6:
            raise SystemExit(f"ROJO: el relieve pide {rv['t_max']} mm de fondo y bajo el "
                             f"rollo solo caben {pt} (PESTANA_T)")
        relieve(pl, d["huecos"], rv["t_borde"], rv["t_max"], rv["w"])
    base = losas(borde["base"], 0.0, +1, "base")
    ob = unir([pl, base])
    ob.name = "cachete_der"
    remallar(ob, float(d.get("voxel", 0.3)))
    return ob


def espejo(obj, nombre: str):
    """La otra mano: la misma pieza reflejada en Z (la cara plana sigue
    siendo la que mira al anillo), con las normales rehechas. Se refleja
    respecto a z = 0 del MUNDO: el objeto unido hereda el origen de la placa
    (z = 1.5), y reflejar respecto a el dejaba el izquierdo 3 mm dentro del
    anillo (check_piel.py, 09-10)."""
    activo(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.duplicate()
    ob = bpy.context.view_layer.objects.active
    ob.name = nombre
    ob.scale = (1.0, 1.0, -1.0)
    bpy.ops.object.transform_apply(scale=True)
    _normales_fuera(ob)
    return ob


# --- LA CUBIERTA ---------------------------------------------------------------
def _dist_perfil(P: np.ndarray, pts: np.ndarray) -> np.ndarray:
    d = np.full(len(pts), np.inf)
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        ab = b - a
        t = np.clip(((pts - a) @ ab) / (ab @ ab), 0.0, 1.0)
        d = np.minimum(d, np.linalg.norm(pts - (a + t[:, None] * ab), axis=1))
    return d


def _ruido(nombre: str, escala: float, hondura: int):
    tx = bpy.data.textures.new(nombre, type="CLOUDS")
    tx.noise_scale = escala
    tx.noise_depth = hondura
    tx.noise_basis = "IMPROVED_PERLIN"
    return tx


def corteza(obj, capa: dict, nombre: str) -> None:
    """Un desplazamiento por ruido, solo sobre el grupo 'fuera', con
    coordenadas de un Empty estirado para que corran a lo largo del perfil."""
    vac = bpy.data.objects.new(nombre + "_coord", None)
    bpy.context.collection.objects.link(vac)
    vac.scale = capa["estira"]
    dm = obj.modifiers.new(nombre, "DISPLACE")
    dm.texture = _ruido(nombre, capa["escala"], capa["hondura"])
    dm.texture_coords = "OBJECT"
    dm.texture_coords_object = vac
    dm.direction = "NORMAL"
    dm.mid_level = capa["medio"]
    dm.strength = capa["fuerza"]
    dm.vertex_group = "fuera"
    aplicar(obj, nombre)
    bpy.data.objects.remove(vac, do_unlink=True)


def _s_perfil(P: np.ndarray, pts: np.ndarray):
    """(d, s, radial): distancia al perfil, abscisa s (mm a lo largo del
    perfil, de la nariz al talon) del punto mas cercano, y la direccion del
    perfil al punto."""
    lados = np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1)
    L = np.r_[0.0, np.cumsum(lados)]
    d = np.full(len(pts), np.inf)
    s = np.zeros(len(pts))
    q = np.zeros_like(pts)
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        ab = b - a
        t = np.clip(((pts - a) @ ab) / (ab @ ab), 0.0, 1.0)
        qi = a + t[:, None] * ab
        di = np.linalg.norm(pts - qi, axis=1)
        m = di < d
        d[m], s[m], q[m] = di[m], L[i] + t[m] * lados[i], qi[m]
    radial = (pts - q) / np.maximum(d, 1e-9)[:, None]
    return d, s, radial


def _fibras(de, s, z, v: dict, rng) -> np.ndarray:
    """Surcos que siguen el canto mas cercano --las curvas de nivel de la
    distancia al canto--, con un meandro lento y huecos a lo largo: rodean las
    esquinas de las ventanas y doblan sobre las franjas de los lados, como en
    el concepto. Cada nivel con su hondura, su ancho y sus huecos, para que no
    lea a moldura ni a pana."""
    D = np.zeros(len(de))
    for c in v["niveles"]:
        p = rng.uniform(0, 2 * np.pi, 5)
        meandro = v["meandro"] * (
            np.sin(2 * np.pi * s / rng.uniform(70, 120) + p[0]) * np.sin(2 * np.pi * z / rng.uniform(110, 190) + p[1])
            + 0.6 * np.sin(2 * np.pi * (s + z) / rng.uniform(40, 70) + p[2])) / 1.6
        n = 0.5 + 0.5 * np.sin(2 * np.pi * s / rng.uniform(80, 140) + p[3]) * np.cos(2 * np.pi * z / rng.uniform(120, 220) + p[4])
        hay = np.clip((n - 0.3) / 0.3, 0.0, 1.0)
        hay = hay * hay * (3 - 2 * hay)
        hondo = v["hondo"] * rng.uniform(0.7, 1.15)
        w = v["ancho"] * rng.uniform(0.85, 1.2)
        D -= hondo * hay * np.exp(-((de + meandro - c) / w) ** 2)
    return D


def _ventanas(s: np.ndarray, z: np.ndarray, ancho: float, hueco: float = 8.0):
    """Los tramos del perfil donde a media anchura no hay lamina (las ventanas)
    y los cantos de las franjas largas: los bordes de las ventanas y las dos
    puntas de la lamina, en mm de perfil."""
    medio = np.sort(s[np.abs(z - ancho / 2) < 40.0])
    saltos = np.flatnonzero(np.diff(medio) > hueco)
    ventanas = [(float(medio[i]), float(medio[i + 1])) for i in saltos]
    cantos = np.array([medio[0], medio[-1]] + [c for v in ventanas for c in v])
    return ventanas, cantos


def veta(ob, borde: dict, ancho: float, modo: str, voxel: float = 0.6) -> None:
    """La ficha 8: surcos finos que siguen la forma (VETAS[modo]), solo sobre
    la cara de fuera de la lamina y apagados en los ultimos milimetros de cada
    canto -- ventanas, extremos de la lamina (donde se funde el rollo) y bajos --:
    el canto se queda limpio y de radio constante."""
    from mathutils import kdtree
    m = ob.modifiers.new("fino", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    aplicar(ob, "fino")
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    nor = np.empty(n * 3)
    me.vertex_normals.foreach_get("vector", nor)
    nor = nor.reshape(-1, 3)
    d, s, radial = _s_perfil(np.asarray(borde["perfil"], dtype=float), co[:, :2])
    alinea = (nor[:, :2] * radial).sum(axis=1)
    fuera = (d > 3.0) & (alinea > 0.8)
    pared = (np.abs(alinea) < 0.5) | (np.abs(nor[:, 2]) > 0.5)
    kd = kdtree.KDTree(int(pared.sum()))
    for i, p in zip(np.flatnonzero(pared), co[pared]):
        kd.insert(p, int(i))
    kd.balance()
    idx = np.flatnonzero(fuera)
    al_canto = np.array([kd.find(co[i])[2] for i in idx])
    a0, a1 = VETA_APAGADO
    t = np.clip((al_canto - a0) / (a1 - a0), 0.0, 1.0)
    peso = t * t * (3 - 2 * t)
    # EL SITIO DE CADA SURCO SE MIDE EN EL PERFIL (10-10): a s constante, el
    # surco corre a lo largo de z y no dobla. Medido al canto mas cercano en 3D,
    # todos doblaban juntos en cada esquina de ventana y se leian como la
    # moldura de un cuadro (render del 09-10). Las franjas de los lados de cada
    # ventana --donde a media anchura el perfil no tiene lamina-- quedan lisas,
    # como el rollo al que llegan.
    sv, zv = s[idx], co[idx, 2]
    ventanas, cantos = _ventanas(sv, zv, ancho)
    en_s = np.min(np.abs(sv[:, None] - cantos[None, :]), axis=1)
    lado = np.zeros(len(idx))
    for v0, v1 in ventanas:
        u = np.clip(np.minimum(sv - v0, v1 - sv) / 3.0, 0.0, 1.0)
        lado = np.maximum(lado, u * u * (3 - 2 * u))
    D = _fibras(en_s, sv, zv, VETAS[modo], np.random.default_rng(SEMILLA_VETA)) * (1.0 - lado)
    co[idx] += nor[idx] * (D * peso)[:, None]
    print("  ventanas en el perfil (mm): " + ", ".join(f"{a:.0f}-{b:.0f}" for a, b in ventanas), flush=True)
    me.vertices.foreach_set("co", co.ravel())
    me.update()
    print(f"  veta '{modo}': {len(idx)} vertices de la cara de fuera, hasta {-D.min():.2f} mm de hondo",
          flush=True)


def cubierta(borde: dict, ancho: float):
    ob = importar(exportar_scad("banda"))
    ob.name = "cubierta"
    if CORTEZA in VETAS:
        veta(ob, borde, ancho, CORTEZA)
    elif CORTEZA == "ruido":
        m = ob.modifiers.new("fino", "REMESH")
        m.mode = "VOXEL"
        m.voxel_size = 1.2
        aplicar(ob, "fino")
        # 'fuera': la cara exterior de la lamina (a mas de 3 mm del perfil),
        # lejos de los costados, donde el rollo se funde
        co = np.empty(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        peso = np.clip((_dist_perfil(np.array(borde["perfil"]), co[:, :2]) - 3.0) / 2.0, 0.0, 1.0)
        peso *= np.clip(np.minimum(co[:, 2], ancho - co[:, 2]) / 20.0, 0.0, 1.0)
        vg = ob.vertex_groups.new(name="fuera")
        for i, w in enumerate(peso):
            if w > 0:
                vg.add([i], float(w), "REPLACE")
        for capa, nombre in ((PLIEGUES, "pliegues"), (VETAS_RUIDO, "vetas"), (GRANO, "grano")):
            corteza(ob, capa, nombre)
    rollos = [losas(borde["rollo"], ancho, +1, "rollo_der"),
              losas(borde["rollo"], 0.0, -1, "rollo_izq")]
    ob = unir([ob] + rollos)
    ob.name = "cubierta"
    remallar(ob, VOXEL_CUBIERTA, suavizado=(0.5, 2))
    return ob


# --- comprobar y escribir ----------------------------------------------------
def comprobar(obj, pieza: str) -> bool:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    no_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    volumen = bm.calc_volume()
    bm.free()
    dims = sorted(obj.dimensions, reverse=True)
    caben = [n for n, b in BANDEJAS.items()
             if all(d <= bb for d, bb in zip(dims, sorted(b, reverse=True)))]
    print(f"  {pieza}: {obj.dimensions.x:.0f} x {obj.dimensions.y:.0f} x {obj.dimensions.z:.0f} mm, "
          f"{len(obj.data.polygons)} triangulos, volumen {volumen/1000:.0f} cm3 "
          f"(~{volumen/1000*1.01:.0f} g en PA12), aristas no-manifold {no_manifold}, "
          f"cabe en: {', '.join(caben) if caben else 'NINGUNA bandeja'}")
    ok = no_manifold == 0 and bool(caben)
    if not ok:
        print(f"  ROJO [{pieza}]: {'no es cerrada' if no_manifold else 'no cabe en ninguna bandeja'}")
    return ok


def escribir(obj, pieza: str) -> None:
    activo(obj)
    salida = os.path.join(SALIDA, pieza + ".stl")
    bpy.ops.wm.stl_export(filepath=salida, export_selected_objects=True)
    print(f"  escrito {salida}")


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(SALIDA, exist_ok=True)
    with open(BORDE, encoding="utf-8") as f:
        borde = json.load(f)
    sys.path.insert(0, AQUI)
    import piel_choques
    ancho = piel_choques.ancho_total()
    todo_ok = True
    # PIEL_SOLO=cachete: para iterar la celosia sin esperar los minutos de la
    # cubierta (el remallado de 580 mm); PIEL_SOLO=cubierta, para la corteza
    solo = os.environ.get("PIEL_SOLO", "")
    piezas = []
    if solo != "cubierta":
        der = cachete(borde)
        piezas += [der, espejo(der, "cachete_izq")]
    if solo != "cachete":
        piezas.append(cubierta(borde, ancho))
    for ob in piezas:
        todo_ok &= comprobar(ob, ob.name)
        escribir(ob, ob.name)
    # las dos reglas de la ficha 16, sobre lo que se acaba de escribir
    if len(piezas) == 3:
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        info = piel_choques.revisar(piel_choques._cargar())
        piel_choques.imprimir_informe(info)
        todo_ok &= info["ok"]
    sys.exit(0 if todo_ok else 1)
