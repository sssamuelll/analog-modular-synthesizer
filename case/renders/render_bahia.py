"""Vistas de la BAHIA INFERIOR — la tabla con el chasis del PSU encima.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P render_bahia.py

POR QUE EXISTE. Es el unico sitio del case cuyo interior es una DECISION y no
una consecuencia, y no se ve en ninguna de las dos vistas del conjunto: los
paneles y la tapa del valle lo tapan entero. Lo que hay que poder juzgar aqui:

  - la TABLA de madera como suelo (2026-08-27) -- se ve por dentro y por fuera
  - el chasis del PSU sentado encima, con su pared trasera colgando de
    `base trasera` y la delantera apoyada en la tabla. Fue el punto que dejo
    la Tarea 7 en rojo, y se decidio sin poder verlo
  - las TRES transversales que quedan, y el hueco que dejo `base delantera`
  - cuanto suelo libre queda por delante del chasis

Se importan TRES ensamblados y no uno porque son tres materiales: madera,
aluminio y acero. Pintarlos igual pierde justo lo que la vista existe para
ensenar. El acrilico y los paneles NO se importan: taparian la bahia.

Misma iluminacion y mismo mundo que render.py -- si aquello cambia, esto
tambien tiene que cambiar.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)


def importar(nombre):
    ruta = os.path.join(AQUI, "build", nombre + ".stl")
    if not os.path.exists(ruta):
        sys.exit(f"ROJO: falta {ruta} -- corre export.ps1 primero")
    try:
        bpy.ops.wm.stl_import(filepath=ruta)
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=ruta)
    return bpy.context.selected_objects[0]


def mat(nombre, **bsdf):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    n = m.node_tree.nodes["Principled BSDF"]
    for k, v in bsdf.items():
        n.inputs[k].default_value = v
    return m


# --- geometria y materiales ----------------------------------------------
mad = importar("assembly_madera")
mad.data.materials.append(mat(
    "nogal", **{"Base Color": (0.28, 0.16, 0.09, 1.0),
                "Roughness": 0.55, "Specular IOR Level": 0.35}))
alu = importar("assembly_esqueleto")
alu.data.materials.append(mat(
    "aluminio", **{"Base Color": (0.85, 0.86, 0.88, 1.0),
                   "Metallic": 1.0, "Roughness": 0.35}))
# El chasis es ACERO y va PINTADO o zincado, no pulido: mas oscuro y mas mate
# que el aluminio, que es lo que lo distingue de un vistazo.
ace = importar("assembly_acero")
ace.data.materials.append(mat(
    "acero", **{"Base Color": (0.42, 0.44, 0.47, 1.0),
                "Metallic": 1.0, "Roughness": 0.62}))

esc = bpy.context.scene
esc.render.engine = "CYCLES"
esc.cycles.samples = 256
esc.render.resolution_x, esc.render.resolution_y = 1600, 1200
esc.render.image_settings.file_format = "PNG"
esc.view_settings.view_transform = "Standard"

# --- mundo: igual que render.py ------------------------------------------
mundo = bpy.data.worlds.new("fondo")
mundo.use_nodes = True
nt = mundo.node_tree
fondo_visible = nt.nodes["Background"]
fondo_visible.inputs[0].default_value = (0.02, 0.02, 0.025, 1)
fondo_gi = nt.nodes.new("ShaderNodeBackground")
fondo_gi.inputs[0].default_value = (0.6, 0.6, 0.63, 1)
ruta_luz = nt.nodes.new("ShaderNodeLightPath")
mezcla = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(ruta_luz.outputs["Is Camera Ray"], mezcla.inputs[0])
nt.links.new(fondo_gi.outputs["Background"], mezcla.inputs[1])
nt.links.new(fondo_visible.outputs["Background"], mezcla.inputs[2])
nt.links.new(mezcla.outputs["Shader"], nt.nodes["World Output"].inputs["Surface"])
esc.world = mundo

# --- bbox de LA BAHIA, no del case ---------------------------------------
# Encuadrar contra el bbox entero deja la bahia diminuta en el centro: el
# esqueleto llega hasta el remate de arriba. Se encuadra contra la TABLA mas
# el chasis, que es lo que la vista trata.
esquinas = [obj.matrix_world @ Vector(c)
            for obj in (mad, ace) for c in obj.bound_box]
xs, ys, zs = ([p[i] for p in esquinas] for i in range(3))
minv = Vector((min(xs), min(ys), min(zs)))
maxv = Vector((max(xs), max(ys), max(zs)))
centro = (minv + maxv) / 2
radio = (maxv - minv).length / 2


def limpiar_camaras_y_luces():
    for o in [o for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")]:
        bpy.data.objects.remove(o, do_unlink=True)


def renderizar(nombre: str, elevacion_deg: float, azimut_deg: float,
               margen: float = 1.12) -> bool:
    limpiar_camaras_y_luces()
    elev = math.radians(elevacion_deg)
    azim = math.radians(azimut_deg)

    horizontal = Vector((-math.cos(azim), 0.0, math.sin(azim)))
    direccion = (horizontal * math.cos(elev)
                 + Vector((0.0, math.sin(elev), 0.0))).normalized()
    arriba_mundo = Vector((0.0, 1.0, 0.0))
    adelante = -direccion
    # A 90 grados de elevacion la camara mira recto abajo y el producto
    # vectorial contra el eje Y degenera. Se usa el eje de profundidad como
    # referencia de "arriba" en ese caso -- que es lo que uno quiere ver en
    # una planta: el frente del case abajo del cuadro.
    if abs(adelante.dot(arriba_mundo)) > 0.999:
        derecha = adelante.cross(Vector((1.0, 0.0, 0.0))).normalized()
    else:
        derecha = adelante.cross(arriba_mundo).normalized()
    arriba_cam = derecha.cross(adelante).normalized()

    cam_data = bpy.data.cameras.new("cam")
    cam_obj = bpy.data.objects.new("cam", cam_data)
    esc.collection.objects.link(cam_obj)
    esc.camera = cam_obj

    semi_ancho = max(abs((p - centro).dot(derecha)) for p in esquinas)
    semi_alto = max(abs((p - centro).dot(arriba_cam)) for p in esquinas)
    distancia = max(semi_ancho / math.tan(cam_data.angle_x / 2),
                    semi_alto / math.tan(cam_data.angle_y / 2)) * margen

    cam_obj.location = centro + direccion * distancia
    cam_obj.rotation_euler = Matrix(
        (derecha, arriba_cam, -adelante)).transposed().to_euler()
    cam_data.clip_start = 1.0
    cam_data.clip_end = max(distancia * 3.0, 2000.0)

    esc_luz = distancia / 700.0
    bpy.ops.object.light_add(
        type="AREA",
        location=centro + arriba_cam * radio * 1.3
                 + derecha * radio * 0.7 + adelante * distancia * 0.4)
    key = bpy.context.object
    key.data.energy = 4e6 * esc_luz ** 2
    key.data.size = 600 * esc_luz
    bpy.ops.object.light_add(
        type="AREA",
        location=centro - derecha * radio * 1.1
                 + arriba_cam * radio * 0.4 + adelante * distancia * 0.25)
    fill = bpy.context.object
    fill.data.energy = 1.5e6 * esc_luz ** 2
    fill.data.size = 400 * esc_luz

    ruta = os.path.join(AQUI, nombre)
    esc.render.filepath = ruta
    if bpy.ops.render.render(write_still=True) != {"FINISHED"}:
        print(f"ROJO [{nombre}]: render no devolvio FINISHED")
        return False
    print(f"render escrito: {ruta}")
    return True


# Convencion de azimut igual que render_detalle_trasera: 0 = frontal (-X),
# 180 = trasera (+X).
# El MARGEN va por vista y no compartido: el encuadre se calcula contra el bbox
# de tabla + chasis, y en picado casi cenital el esqueleto que sube por encima
# entra en cuadro sin contar para el encuadre. La planta pedia aire.
vistas = [
    # PLANTA: la que Samuel pidio. Cuanto suelo queda por delante del chasis,
    # y donde estaba `base delantera`.
    ("bahia-planta.png",             80,   0, 1.45),
    # Tres cuartos picado: el chasis sobre la tabla, las tres transversales y
    # el canto de la tabla asomando por los cuatro lados.
    ("bahia-3q.png",                 45,  35, 1.12),
    # Rasante desde el frente: el hueco libre bajo el riel del panel, que es
    # la cota que costo 8.46 mm de aparato.
    ("bahia-rasante.png",             8,   0, 1.12),
]

ok = True
for nombre, elev, azim, margen in vistas:
    if not renderizar(nombre, elev, azim, margen):
        ok = False
sys.exit(0 if ok else 2)
