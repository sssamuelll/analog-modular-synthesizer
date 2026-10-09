"""Las piezas de la piel LISTAS PARA IMPRIMIR: la rama (cachete) y el tronco
(cubierta), levantadas en Blender y comprobadas como las mira un servicio.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P imprimir_piel.py

LA FILOSOFIA (Samuel, 05-09): toda la piel simula un arbol. La cubierta es el
TRONCO --la masa que envuelve el hueso, con corteza-- y cada cachete es UNA
RAMA que sale de el con extensiones. Ni una ni otra son planas: por eso ya no
salen de un extruido de OpenSCAD con las aristas a 90 grados sino que se
levantan aqui, en 3D, con seccion redonda y relieve.

EL CACHETE (la rama), de case/cad/celosia_rama.json (celosia.py):
  * cada fibra es un TUBO de seccion redonda y radio variable (curva con
    bevel y radio por punto): grueso junto al nudo, fino en las puntas, y
    ondulando en Z para que en cada cruce una pase por encima de la otra;
  * el MARCO es una seccion de almohada (superelipse: plana contra el
    anillo, abombada hacia fuera) barrida por su eje, con los cuatro
    pasantes M4 de las esquinas restados;
  * todo se FUNDE con un remallado por voxeles: las uniones salen con su
    garganta, como en el despiece. Y se suaviza un poco.
  Son DOS piezas espejo (la cara plana va contra el anillo, la abombada
  fuera): cachete_der.stl y cachete_izq.stl.

LA CUBIERTA (el tronco), de piel_organica.scad, DE UNA PIEZA:
  * la lamina de 6 mm que sigue el canto (OpenSCAD), remallada fina;
  * CORTEZA: dos desplazamientos por ruido sobre la cara exterior --pliegues
    largos a lo largo del perfil (+-3 mm) y grano fino--, solo hacia fuera:
    la cara interior sigue lisa contra el hueso;
  * remallado, suavizado, decimado.

Comprobaciones: malla cerrada (cero aristas no-manifold), tamano contra dos
bandejas --MJF 5200 (380 x 284 x 380) y SLS P 770 (700 x 380 x 580), cifras
de catalogo sin hoja en el repo-- y volumen -> gramos en PA12 (1.01 g/cm3).
La cubierta de una pieza NO cabe en la MJF: es la decision D-P6 del papel.

Salida: case/print/piel/{cachete_der,cachete_izq,cubierta}.stl. Artefactos
de salida, como los DXF del laser; los regenera este guion.
"""
import json
import math
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
RAMA = os.environ.get("PIEL_RAMA", os.path.join(CAD, "celosia_rama.json"))

VOXEL_CACHETE = 0.6      # mm; fibras de 4-11, marco 24 x 11
VOXEL_CUBIERTA = 0.8     # mm; lamina de 6 con pliegues de 3
SUAVIZADO = (0.5, 4)     # factor, iteraciones
DECIMAR = 0.35
BANDEJAS = {"MJF 5200": (380.0, 284.0, 380.0), "SLS P 770": (700.0, 380.0, 580.0)}
ALMOHADA_N = 3.5         # exponente de la superelipse del marco
# la corteza, tres capas sobre la cara exterior: PLIEGUES anchos como una
# manta gruesa (la referencia: la cubierta es masa, no lamina), VETAS largas
# a lo largo del perfil (estiradas en XY, que es el plano del perfil; Z es el
# ancho) y GRANO fino. `medio` es el nivel cero del ruido: 0.3 desplaza de
# -0.3 a +0.7 de la fuerza, o sea mas hacia fuera que hacia dentro, para que
# la lamina de 6 no baje de ~3 en los valles. Con +-3 (primer intento) era
# piel de naranja, no corteza.
PLIEGUES = dict(escala=58.0, estira=(1.6, 1.6, 1.0), fuerza=11.0, medio=0.3, hondura=1)
VETAS = dict(escala=16.0, estira=(4.0, 4.0, 1.0), fuerza=3.0, medio=0.5, hondura=1)
GRANO = dict(escala=6.0, estira=(1.0, 1.0, 1.0), fuerza=0.7, medio=0.5, hondura=1)
PIEL_E = 6.0             # = piel_e de piel_organica.scad


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


# --- EL CACHETE: la rama ---------------------------------------------------
def _seccion_almohada(ancho: float, alto: float, n: int = 14):
    """Puntos (u, v) del contorno: base plana en v = 0 de -a a +a y encima
    la superelipse |u/a|^N + (v/alto)^N = 1. Cerrado, antihorario."""
    a = ancho / 2
    pts = []
    for k in range(n + 1):
        u = -a + ancho * k / n
        v = alto * (max(0.0, 1.0 - abs(u / a) ** ALMOHADA_N)) ** (1.0 / ALMOHADA_N)
        pts.append((u, v))
    return pts                      # el ultimo (a, 0) cierra con el primero (-a, 0)


def marco(eje, ancho: float, alto: float):
    """El marco barrido: seccion almohada por el eje cerrado. Malla de quads."""
    E = np.array(eje, dtype=float)
    m = len(E)
    sec = _seccion_almohada(ancho, alto)
    verts, caras = [], []
    for i in range(m):
        t = E[(i + 1) % m] - E[i - 1]
        t /= np.linalg.norm(t)
        n = np.array([-t[1], t[0]])         # hacia fuera (perfil horario)
        for u, v in sec:
            q = E[i] + n * u
            verts.append((float(q[0]), float(q[1]), float(v)))
    S = len(sec)
    for i in range(m):
        for j in range(S):
            a = i * S + j
            b = i * S + (j + 1) % S
            c = ((i + 1) % m) * S + (j + 1) % S
            d = ((i + 1) % m) * S + j
            caras.append((a, b, c, d))
    me = bpy.data.meshes.new("marco")
    me.from_pydata(verts, [], caras)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # HACIA FUERA de verdad: recalc solo las hace consistentes, y con el eje
    # horario salian hacia dentro. El booleano EXACTO trata un solido
    # invertido como su complemento y devolvia un disco de 24 x 23 (medido).
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("marco", me)
    bpy.context.collection.objects.link(ob)
    return ob


def fibra(pts, z0: float):
    """Un tubo de seccion redonda y radio variable por una polilinea
    [x, y, z, w] (w = diametro), z relativo al plano medio z0."""
    cu = bpy.data.curves.new("fibra", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = 5
    cu.fill_mode = "FULL"
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, (x, y, z, w) in zip(sp.points, pts):
        p.co = (x, y, z0 + z, 1.0)
        p.radius = w / 2.0
    ob = bpy.data.objects.new("fibra", cu)
    bpy.context.collection.objects.link(ob)
    activo(ob)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.view_layer.objects.active


def cinta(pts, z0: float, fondo: float):
    """Una CINTA: seccion estadio vertical (w de ancho en planta, `fondo` de
    alto, cantos redondos) barrida por una polilinea [x, y, z, w]. La finura
    se ve en planta y la rigidez sale del fondo (el ala, 07-09)."""
    P = np.array([(x, y, z) for x, y, z, w in pts], dtype=float)
    W = np.array([w for x, y, z, w in pts], dtype=float)
    n = len(P)
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0], T[-1] = P[1] - P[0], P[-1] - P[-2]
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    N = np.stack([-T[:, 1], T[:, 0], np.zeros(n)], axis=1)
    K = 8
    verts, caras = [], []
    for i in range(n):
        r = W[i] / 2.0
        h = max(fondo / 2.0 - r, 0.0)
        anillo = [(math.cos(a) * r, h + math.sin(a) * r)
                  for a in (math.pi * k / K for k in range(K + 1))]
        anillo += [(math.cos(a) * r, -h + math.sin(a) * r)
                   for a in (math.pi + math.pi * k / K for k in range(K + 1))]
        for u, v in anillo:
            q = P[i] + N[i] * u
            verts.append((float(q[0]), float(q[1]), float(z0 + P[i, 2] + v)))
    S = 2 * (K + 1)
    for i in range(n - 1):
        for j in range(S):
            a = i * S + j
            b = i * S + (j + 1) % S
            c = (i + 1) * S + (j + 1) % S
            d = (i + 1) * S + j
            caras.append((a, b, c, d))
    caras.append(tuple(range(S))[::-1])
    caras.append(tuple((n - 1) * S + j for j in range(S)))
    me = bpy.data.meshes.new("cinta")
    me.from_pydata(verts, [], caras)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("cinta", me)
    bpy.context.collection.objects.link(ob)
    return ob


def placa(exterior, huecos, z0: float, fondo: float):
    """Una PLACA perforada: el exterior solido menos los huecos, un CSG
    (booleano EXACT) sin remallado previo -- el hueco tiene que salir
    nitido, no una hebra (Samuel, 07-09: "que solo queden los huecos de
    los circulitos")."""
    def prisma(pts, nombre, altura):
        cu = bpy.data.curves.new(nombre, "CURVE")
        cu.dimensions = "2D"
        cu.fill_mode = "BOTH"
        cu.extrude = altura / 2.0
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        sp.use_cyclic_u = True
        for p, (x, y) in zip(sp.points, pts):
            p.co = (x, y, 0.0, 1.0)
        ob = bpy.data.objects.new(nombre, cu)
        bpy.context.collection.objects.link(ob)
        ob.location.z = z0
        activo(ob)
        bpy.ops.object.convert(target="MESH")
        ob = bpy.context.view_layer.objects.active
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
        return ob

    base = prisma(exterior, "placa", fondo)
    cortes = [prisma(h, f"hueco{i}", fondo + 6.0) for i, h in enumerate(huecos)]
    cortes_obj = cortes[0]
    if len(cortes) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for c in cortes:
            c.select_set(True)
        bpy.context.view_layer.objects.active = cortes_obj
        bpy.ops.object.join()
        cortes_obj = bpy.context.view_layer.objects.active
    b = base.modifiers.new("huecos", "BOOLEAN")
    b.operation = "DIFFERENCE"
    b.solver = "EXACT"
    b.object = cortes_obj
    aplicar(base, "huecos")
    bpy.data.objects.remove(cortes_obj, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(base.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(base.data)
    bm.free()
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
    """Talla el lomo redondeado ESCULPIENDO la malla: remalla fino y
    mueve cada vertice por su propia normal segun la distancia (XY) al
    hueco mas cercano -- sin booleano. Un primer intento con un solido
    "campo de alturas" e interseccion EXACT revento el solver de Blender
    (malloc de 906 MB, 07-09): las mesetas a espesor constante son
    kilometros de caras coplanares, el peor caso para ese solver."""
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
        v.co += v.normal * float(dz)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def cachete():
    with open(RAMA, encoding="utf-8") as f:
        d = json.load(f)
    ancho, alto = d["marco"]["ancho"], d["marco"]["espesor"]
    z0 = alto / 2.0
    # ninguna pieza asoma por la cara plana (la que va contra el anillo)
    if d.get("tipo") == "placa":
        z0 = max(z0, 0.6 + d["fondo"] / 2.0)
        pl = placa(d["exterior"], d["huecos"], z0, d["fondo"])
        rv = d.get("relieve")
        if rv:
            relieve(pl, d["huecos"], rv["t_borde"], rv["t_max"], rv["w"])
        piezas = [pl]
    else:
        seccion = d.get("seccion", {})
        if seccion.get("tipo") == "cinta":
            zmin = min(p[2] for fb in d["fibras"] for p in fb) - seccion["fondo"] / 2.0
            z0 = max(z0, 0.6 - zmin)
            piezas = [cinta(fb, z0, seccion["fondo"]) for fb in d["fibras"] if len(fb) >= 2]
        else:
            zmin = min(p[2] - p[3] / 2.0 for fb in d["fibras"] for p in fb)
            z0 = max(z0, 0.6 - zmin)
            piezas = [fibra(fb, z0) for fb in d["fibras"]]
    mk = marco(d["marco"]["eje"], ancho, alto)
    # los cuatro pasantes, restados del marco antes de fundir
    for cx, cy in d["agujeros"]["centros"]:
        bpy.ops.mesh.primitive_cylinder_add(radius=d["agujeros"]["diametro"] / 2.0,
                                            depth=alto + 20.0, location=(cx, cy, alto / 2.0),
                                            vertices=32)
        cil = bpy.context.object
        b = mk.modifiers.new("agujero", "BOOLEAN")
        b.operation = "DIFFERENCE"
        # MANIFOLD, no EXACT: con la barrida en quads el exacto devolvia un
        # disco de 24 x 23 (medido 05-09, tambien triangulada); el manifold
        # resta los 0.5 cm3 del cilindro y deja los 221.7 del marco
        b.solver = "MANIFOLD"
        b.object = cil
        aplicar(mk, "agujero")
        bpy.data.objects.remove(cil, do_unlink=True)
    # guarda: el marco tiene que seguir ahi despues de taladrarlo. Con la
    # barrida cruzada en la nariz, el booleano exacto devolvia un disco de
    # 24 x 23 y la pieza salia sin marco, cerrada y 'lista' (medido 05-09).
    bm = bmesh.new()
    bm.from_mesh(mk.data)
    vol_marco = bm.calc_volume(signed=True)
    bm.free()
    if vol_marco < 150_000:
        raise SystemExit(f"ROJO: el marco quedo en {vol_marco/1000:.0f} cm3 tras los agujeros")
    piezas.append(mk)
    for ob in piezas:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = mk
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = "cachete_der"
    remallar(ob, float(d.get("voxel", VOXEL_CACHETE)))
    return ob


def espejo(obj, nombre: str):
    """La otra mano: la misma pieza reflejada en Z (la cara plana sigue
    siendo la que mira al anillo), con las normales rehechas."""
    activo(obj)
    bpy.ops.object.duplicate()
    ob = bpy.context.view_layer.objects.active
    ob.name = nombre
    ob.scale = (1.0, 1.0, -1.0)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


# --- LA CUBIERTA: el tronco -------------------------------------------------
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


def corteza(obj, P: np.ndarray, capa: dict, nombre: str) -> None:
    """Un desplazamiento por ruido, solo sobre la cara EXTERIOR (grupo
    'fuera'), con coordenadas de un Empty estirado para que los pliegues
    corran a lo largo del perfil."""
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


def cubierta(P: np.ndarray):
    ob = importar(exportar_scad("banda"))
    ob.name = "cubierta"
    # malla uniforme y fina antes de desplazar: el STL viene en quads enormes
    m = ob.modifiers.new("fino", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = 1.2
    aplicar(ob, "fino")
    # 'fuera': la cara exterior es la que esta a mas de 3 mm del perfil (la
    # lamina va de 0 a 6 por fuera de el); la interior sigue lisa
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    xy = co.reshape(-1, 3)[:, :2]
    peso = np.clip((_dist_perfil(P, xy) - 3.0) / 2.0, 0.0, 1.0)
    vg = ob.vertex_groups.new(name="fuera")
    for i, w in enumerate(peso):
        if w > 0:
            vg.add([i], float(w), "REPLACE")
    corteza(ob, P, PLIEGUES, "pliegues")
    corteza(ob, P, VETAS, "vetas")
    corteza(ob, P, GRANO, "grano")
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
    with open(RAMA, encoding="utf-8") as f:
        perfil = np.array(json.load(f)["perfil"], dtype=float)
    todo_ok = True
    der = cachete()
    izq = espejo(der, "cachete_izq")
    # PIEL_SOLO=cachete: para iterar la rama sin esperar los minutos de la
    # cubierta (el remallado de 580 mm)
    piezas = [der, izq]
    if os.environ.get("PIEL_SOLO", "") != "cachete":
        piezas.append(cubierta(perfil))
    for ob in piezas:
        todo_ok &= comprobar(ob, ob.name)
        escribir(ob, ob.name)
    sys.exit(0 if todo_ok else 1)
