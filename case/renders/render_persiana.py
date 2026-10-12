"""El case con la persiana (spec 2026-10-11, §11): el cuerpo en negro, los
Z-Rails en plata, la trasera ambar, la tabla, las dos persianas y la cara de
los paneles con sus tres filas (cara_panel.py). Es la escena del acta del
11-10 llevada al repo.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b --factory-startup -P render_persiana.py
    ... -P render_persiana.py -- frente,noche     (solo esas vistas)

    PERSIANA_MOTOR=eevee   para encuadrar: Eevee a 800 x 600
    PERSIANA_MUESTRAS      muestras de Cycles (128)

Las partes son STL de build/ y se re-exportan si el modelo es mas nuevo
(importar() de render.py, que mira tambien persiana_generada.scad). De
render.py se reusan el mundo, las luces, mat() y medir(); sus umbrales se
calibraron con un case naranja y plateado, y este lleva los suyos.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# --- 1. la escena de render.py: mundo, luces, camara, mat(), medir() ----------
ruta = os.path.join(AQUI, "render.py")
src = open(ruta, encoding="utf-8").read()
ns = {"__file__": ruta, "__name__": "render_persiana"}
exec(compile(src[:src.index("# --- RENDER: vista frontal")], ruta, "exec"), ns)
for o in (ns["acr"], ns["alu"], ns["jun"], ns["mad"]):
    bpy.data.objects.remove(o, do_unlink=True)
esc = bpy.context.scene
mat = ns["mat"]

sys.path.insert(0, AQUI)
import cara_panel as cp  # noqa: E402

ZD = cp.cb.leer_params()["ancho_total"]   # la cara de fuera del anillo derecho

# --- 2. materiales (color de mirar, no cota) -----------------------------------
mat("anodizado_negro", **{"Base Color": (0.014, 0.014, 0.016, 1.0), "Metallic": 0.0, "Roughness": 0.45})
mat("panel_oscuro", **{"Base Color": (0.10, 0.105, 0.115, 1.0), "Metallic": 0.9, "Roughness": 0.38})
mat("nogal_oscuro", **{"Base Color": (0.13, 0.075, 0.045, 1.0), "Roughness": 0.5, "Specular IOR Level": 0.35})
mat("luz_dentro", **{"Base Color": (0, 0, 0, 1), "Emission Color": (1.0, 0.42, 0.10, 1.0),
                     "Emission Strength": 6.0})


def parte(nombre, material):
    ob = ns["importar"](nombre)
    ob.name = nombre
    ob.data.materials.append(bpy.data.materials[material])
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


# --- 3. el cuerpo y las persianas ----------------------------------------------
objetos = [parte(n, m) for n, m in (("render_negro", "anodizado_negro"),
                                    ("render_rieles", "aluminio"),
                                    ("render_paneles", "panel_oscuro"),
                                    ("assembly_acrilico", "acrilico_naranja"),
                                    ("assembly_madera", "nogal_oscuro"),
                                    ("assembly_persiana", "anodizado_negro"))]
paneles = next(o for o in objetos if o.name == "render_paneles")

# --- 4. la cara: los mandos de las tres filas ----------------------------------
objetos += cp.vestir(ns, paneles)


# --- 5. luz de dentro (vista noche) --------------------------------------------
def luz_dentro():
    out = []
    for z in (ZD - 40.0, 40.0):
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(160.0, 120.0, z))
        pl = bpy.context.object
        pl.scale = (300.0, 220.0, 1.0)
        pl.data.materials.append(bpy.data.materials["luz_dentro"])
        pl.name = "luz_dentro"
        pl.visible_camera = False        # alumbra por dentro; la camara no la ve
        pl.visible_glossy = False
        out.append(pl)
    return out


# --- 6. camaras ----------------------------------------------------------------
TODOS = [o for o in esc.objects if o.type == "MESH"]
esquinas = [o.matrix_world @ Vector(c) for o in TODOS for c in o.bound_box]
lo = Vector([min(v[i] for v in esquinas) for i in range(3)])
hi = Vector([max(v[i] for v in esquinas) for i in range(3)])
ns["esquinas"], ns["centro"], ns["radio"] = esquinas, (lo + hi) / 2, (hi - lo).length / 2

if os.environ.get("PERSIANA_MOTOR", "").lower() == "eevee":
    esc.render.engine = "BLENDER_EEVEE"
    esc.eevee.taa_render_samples = 16
    esc.render.resolution_x, esc.render.resolution_y = 800, 600
else:
    esc.cycles.samples = int(os.environ.get("PERSIANA_MUESTRAS", "128"))
    esc.cycles.use_denoising = True


def base(az, el):
    horizontal = Vector((-math.cos(az), 0.0, math.sin(az)))
    direccion = (horizontal * math.cos(el) + Vector((0.0, math.sin(el), 0.0))).normalized()
    adelante = -direccion
    derecha = adelante.cross(Vector((0.0, 1.0, 0.0))).normalized()
    arriba_cam = derecha.cross(adelante).normalized()
    return direccion, derecha, arriba_cam, adelante


def encuadre(az, el, margen=1.1):
    _, derecha, arriba_cam, _ = base(math.radians(az), math.radians(el))
    vs = [o.matrix_world @ Vector(c) for o in TODOS for c in o.bound_box]
    u = [v.dot(derecha) for v in vs]
    w = [v.dot(arriba_cam) for v in vs]
    c = sum(vs, Vector()) / len(vs)
    foco = c + derecha * ((max(u) + min(u)) / 2 - c.dot(derecha)) + arriba_cam * ((max(w) + min(w)) / 2 - c.dot(arriba_cam))
    return foco, max((max(u) - min(u)) / 2, (max(w) - min(w)) / 2 * 4 / 3) * margen


LUZ = [1.0]


def disparar(nombre, az, el, foco, semi, orto=False, transparente=False):
    from bpy_extras.object_utils import world_to_camera_view
    direccion, derecha, arriba_cam, adelante = base(math.radians(az), math.radians(el))
    cd = bpy.data.cameras.new("cam_" + nombre)
    cam = bpy.data.objects.new("cam_" + nombre, cd)
    esc.collection.objects.link(cam)
    esc.camera = cam
    if orto:
        cd.type = "ORTHO"
        cd.ortho_scale = 2 * semi
        dist = 1500.0
    else:
        cd.lens = 50.0
        dist = semi / math.tan(cd.angle_x / 2)
    cam.location = foco + direccion * dist
    cam.rotation_euler = Matrix((derecha, arriba_cam, -adelante)).transposed().to_euler()
    cd.clip_start, cd.clip_end = 1.0, dist * 4.0 + 3000.0
    if not orto:
        # el bbox proyectado se centra y ocupa el 88 % del cuadro
        pts = [o.matrix_world @ Vector(k) for o in TODOS if o.name != "luz_dentro" for k in o.bound_box]
        for _ in range(4):
            bpy.context.view_layer.update()
            uv = [world_to_camera_view(esc, cam, p) for p in pts]
            u0, u1 = min(q.x for q in uv), max(q.x for q in uv)
            v0, v1 = min(q.y for q in uv), max(q.y for q in uv)
            cam.location += derecha * ((u0 + u1) / 2 - 0.5) * 2 * semi + arriba_cam * ((v0 + v1) / 2 - 0.5) * 1.5 * semi
            k = max(u1 - u0, v1 - v0) / 0.88
            cam.location = foco + (cam.location - foco - direccion * dist) + direccion * dist * k
            dist, semi = dist * k, semi * k
    ns["poner_luces"](derecha, arriba_cam, adelante, 700.0 if orto else max(dist, 700.0))
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            o.data.energy *= LUZ[0]
    if orto:
        bpy.ops.object.light_add(type="SUN", location=foco + direccion * 900 + arriba_cam * 600 - derecha * 500)
        sol = bpy.context.object
        sol.data.energy = 3.0
        ns["_apuntar"](sol, foco)
    esc.render.film_transparent = transparente
    salida = os.path.join(AQUI, nombre + ".png")
    esc.render.filepath = salida
    bpy.ops.render.render(write_still=True)
    print("OUT", nombre, flush=True)
    return salida


def todo(az, el, nombre, margen=1.08):
    return disparar(nombre, az, el, *encuadre(az, el, margen))


def noche(nombre, az, el):
    """Como la de lado, a oscuras, con la luz ambar de dentro encendida."""
    planos = luz_dentro()
    mundo = esc.world.node_tree
    gi = [n for n in mundo.nodes if n.type == "BACKGROUND" and n.name != "Background"][0]
    fuerza = gi.inputs["Strength"].default_value
    gi.inputs["Strength"].default_value, LUZ[0] = 0.10, 0.06
    salida = todo(az, el, nombre)
    gi.inputs["Strength"].default_value, LUZ[0] = fuerza, 1.0
    for p in planos:
        bpy.data.objects.remove(p, do_unlink=True)
    return salida


def costado(nombre):
    """El costado de frente, ortografico y sin fondo: la persiana como alzado."""
    c, d = (lo + hi) / 2, hi - lo
    return disparar(nombre, 90, 0, c, max(d.x, d.y * 4 / 3) / 2 * 1.08, orto=True, transparente=True)


VISTAS = {"frente": lambda: todo(32, 25, "sam17-persiana"),
          "trasera": lambda: todo(222, 19, "sam17-persiana-trasera", 1.06),
          "lado": lambda: todo(68, 14, "sam17-persiana-lado"),
          "noche": lambda: noche("sam17-persiana-noche", 68, 14),
          "costado": lambda: costado("sam17-persiana-costado")}
# UMBRALES PROPIOS (2026-10-12). Los de render.py (brillo 0.20) son de un case
# naranja y plateado; este es negro. Medidos en las dos primeras corridas: en
# Eevee (800 x 600) cobertura 0.31 a 0.52 y brillo 0.28 a 0.35 de dia y 0.056
# de noche; en Cycles (1600 x 1200, 128 muestras) cobertura 0.37 a 0.52 y brillo
# 0.25 a 0.28 de dia y 0.070 de noche, que es oscura por diseno y lleva su
# propio suelo. Un render que no los pasa es un render roto -- cuerpo fuera de
# cuadro, luces apagadas --, no uno feo.
COBERTURA_MINIMA = 0.05
BRILLO_MINIMO = {"noche": 0.03}
rojos = 0
for v in (args[0].split(",") if args else VISTAS):
    png = VISTAS[v.strip()]()
    frac, brillo = ns["medir"](png)
    minimo = BRILLO_MINIMO.get(v.strip(), 0.08)
    veredicto = "VERDE" if frac >= COBERTURA_MINIMA and brillo >= minimo else "ROJO"
    rojos += veredicto == "ROJO"
    print(f"{veredicto} [{os.path.basename(png)}]: cobertura {frac:.4f} (minimo "
          f"{COBERTURA_MINIMA}), brillo {brillo:.4f} (minimo {minimo})", flush=True)
print("FIN", flush=True)
if rojos:
    sys.exit(1)
