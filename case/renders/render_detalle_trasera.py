"""Renders de detalle de las pieles traseras — multiples angulos.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P render_detalle_trasera.py

Seis vistas del case centradas en la parte trasera para apreciar:
  - Las ranuras de ventilacion en forma de onda (sierra, triangulo, cuadrada)
  - La junta de sombra (gap de 5 mm entre piel y cuerpo)
  - La separacion entre piel inferior y superior
Material naranja (el oficial). Misma iluminacion que render.py.
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
acr = importar("assembly_acrilico")
acr.data.materials.append(mat(
    "acrilico_naranja", **{
        "Base Color": (1.0, 0.35, 0.05, 1.0),
        "Roughness": 0.08,
        "Transmission Weight": 0.85,
    }))
alu = importar("assembly_aluminio")
alu.data.materials.append(mat(
    "aluminio", **{"Base Color": (0.85, 0.86, 0.88, 1.0),
                   "Metallic": 1.0, "Roughness": 0.35}))

esc = bpy.context.scene
esc.render.engine = "CYCLES"
esc.cycles.samples = 256
esc.render.resolution_x, esc.render.resolution_y = 1600, 1200
esc.render.image_settings.file_format = "PNG"
esc.view_settings.view_transform = "Standard"

# --- mundo ---------------------------------------------------------------
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

# --- bbox ----------------------------------------------------------------
esquinas = [obj.matrix_world @ Vector(c)
            for obj in (acr, alu) for c in obj.bound_box]
xs, ys, zs = ([p[i] for p in esquinas] for i in range(3))
minv = Vector((min(xs), min(ys), min(zs)))
maxv = Vector((max(xs), max(ys), max(zs)))
centro = (minv + maxv) / 2
radio = (maxv - minv).length / 2


def limpiar_camaras_y_luces():
    for o in [o for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")]:
        bpy.data.objects.remove(o, do_unlink=True)


def renderizar(nombre: str, elevacion_deg: float, azimut_deg: float,
               margen: float = 1.15) -> bool:
    """Renderiza una vista desde (elevacion, azimut) sobre el centro del bbox."""
    limpiar_camaras_y_luces()

    elev = math.radians(elevacion_deg)
    azim = math.radians(azimut_deg)

    horizontal = Vector((-math.cos(azim), 0.0, math.sin(azim)))
    direccion = (horizontal * math.cos(elev)
                 + Vector((0.0, math.sin(elev), 0.0))).normalized()
    arriba_mundo = Vector((0.0, 1.0, 0.0))
    adelante = -direccion
    derecha = adelante.cross(arriba_mundo).normalized()
    arriba_cam = derecha.cross(adelante).normalized()

    cam_data = bpy.data.cameras.new("cam")
    cam_obj = bpy.data.objects.new("cam", cam_data)
    esc.collection.objects.link(cam_obj)
    esc.camera = cam_obj

    semi_ancho = max(abs((p - centro).dot(derecha)) for p in esquinas)
    semi_alto = max(abs((p - centro).dot(arriba_cam)) for p in esquinas)
    dist_h = semi_ancho / math.tan(cam_data.angle_x / 2)
    dist_v = semi_alto / math.tan(cam_data.angle_y / 2)
    distancia = max(dist_h, dist_v) * margen

    cam_obj.location = centro + direccion * distancia
    cam_obj.rotation_euler = Matrix(
        (derecha, arriba_cam, -adelante)).transposed().to_euler()
    cam_data.clip_start = 1.0
    cam_data.clip_end = max(distancia * 3.0, 2000.0)

    # luces ancladas a la vista
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
    resultado = bpy.ops.render.render(write_still=True)
    if resultado != {"FINISHED"}:
        print(f"ROJO [{nombre}]: render no devolvio FINISHED")
        return False
    print(f"render escrito: {ruta}")
    return True


# --- Seis vistas de la trasera -------------------------------------------
# Convencion de azimut: 0 = frontal (-X), 180 = trasera (+X)
#
# 1. Trasera centrada — vista recta desde atras, ligeramente elevada
# 2. Trasera 3/4 izquierda — muestra la junta de sombra del costado
# 3. Trasera 3/4 derecha — el otro costado
# 4. Trasera baja — desde abajo hacia arriba, muestra la separacion entre pieles
# 5. Trasera elevada — desde arriba, ve las ondas en escorzo
# 6. Lateral puro — perfil del case mostrando el gap de las pieles

vistas = [
    ("detalle-trasera-centro.png",       15,  180),   # recta de atras
    ("detalle-trasera-3q-izq.png",       20,  215),   # 3/4 por la izquierda
    ("detalle-trasera-3q-der.png",       20,  145),   # 3/4 por la derecha
    ("detalle-trasera-baja.png",          5,  170),   # baja, casi a ras
    ("detalle-trasera-elevada.png",      40,  190),   # picado desde arriba
    ("detalle-lateral.png",              15,  270),   # perfil lateral puro
]

ok = True
for nombre, elev, azim in vistas:
    if not renderizar(nombre, elev, azim):
        ok = False

sys.exit(0 if ok else 1)
