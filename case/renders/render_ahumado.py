"""Render del case: variante en acrilico ahumado oscuro translucido.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P render_ahumado.py

Copia de render.py con el material de acrilico cambiado a ahumado oscuro
(como el board de intencion propuesta-diseno-2026-08-16.png). Solo cambia
el color del material — geometria, luces y camara son identicas.
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
        bpy.ops.wm.stl_import(filepath=ruta)          # Blender 4/5
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=ruta)        # por si acaso
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
    "acrilico_ahumado", **{
        # Ahumado oscuro translucido — como el board de intencion.
        # Tono neutro-calido muy oscuro, alta transmision para que la luz
        # de Cycles atraviese y revele la estructura de aluminio detras.
        "Base Color": (0.12, 0.10, 0.09, 1.0),
        "Roughness": 0.06,
        "Transmission Weight": 0.88,
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

# --- mundo: fondo oscuro para la camara, relleno GI brillante -----------
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

# --- bbox real de las 2 mallas ------------------------------------------
esquinas = [obj.matrix_world @ Vector(c)
            for obj in (acr, alu) for c in obj.bound_box]
xs, ys, zs = ([p[i] for p in esquinas] for i in range(3))
minv = Vector((min(xs), min(ys), min(zs)))
maxv = Vector((max(xs), max(ys), max(zs)))
centro = (minv + maxv) / 2
radio = (maxv - minv).length / 2

ELEVACION = math.radians(22)
AZIMUT_FRENTE = math.radians(35)
AZIMUT_TRASERA = math.pi - AZIMUT_FRENTE
MARGEN = 1.15


def construir_vista(azimut: float):
    horizontal = Vector((-math.cos(azimut), 0.0, math.sin(azimut)))
    direccion = (horizontal * math.cos(ELEVACION)
                 + Vector((0.0, math.sin(ELEVACION), 0.0))).normalized()
    arriba_mundo = Vector((0.0, 1.0, 0.0))
    adelante = -direccion
    derecha = adelante.cross(arriba_mundo).normalized()
    arriba_cam = derecha.cross(adelante).normalized()

    cam_data = bpy.data.cameras.new("camara")
    cam_obj = bpy.data.objects.new("camara", cam_data)
    esc.collection.objects.link(cam_obj)
    esc.camera = cam_obj

    semi_ancho = max(abs((p - centro).dot(derecha)) for p in esquinas)
    semi_alto = max(abs((p - centro).dot(arriba_cam)) for p in esquinas)
    dist_h = semi_ancho / math.tan(cam_data.angle_x / 2)
    dist_v = semi_alto / math.tan(cam_data.angle_y / 2)
    distancia = max(dist_h, dist_v) * MARGEN

    cam_obj.location = centro + direccion * distancia
    cam_obj.rotation_euler = Matrix((derecha, arriba_cam, -adelante)).transposed().to_euler()
    cam_data.clip_start = 1.0
    cam_data.clip_end = max(distancia * 3.0, 2000.0)
    return derecha, arriba_cam, adelante, distancia


def poner_luces(derecha, arriba_cam, adelante, distancia):
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    esc_luz = distancia / 700.0
    bpy.ops.object.light_add(type="AREA", location=centro + arriba_cam * radio * 1.3
                              + derecha * radio * 0.7 + adelante * distancia * 0.4)
    key = bpy.context.object
    key.data.energy = 4e6 * esc_luz ** 2
    key.data.size = 600 * esc_luz
    bpy.ops.object.light_add(type="AREA", location=centro - derecha * radio * 1.1
                              + arriba_cam * radio * 0.4 + adelante * distancia * 0.25)
    fill = bpy.context.object
    fill.data.energy = 1.5e6 * esc_luz ** 2
    fill.data.size = 400 * esc_luz


def renderizar_vista(nombre_archivo: str, azimut: float) -> bool:
    derecha, arriba_cam, adelante, distancia = construir_vista(azimut)
    poner_luces(derecha, arriba_cam, adelante, distancia)

    ruta = os.path.join(AQUI, nombre_archivo)
    esc.render.filepath = ruta
    resultado = bpy.ops.render.render(write_still=True)
    if resultado != {"FINISHED"}:
        print(f"ROJO [{nombre_archivo}]: render no devolvio FINISHED: {resultado}")
        return False
    print(f"render escrito: {ruta}")
    return True


# --- RENDER: frontal y trasera en ahumado --------------------------------
ok_frente = renderizar_vista("sam17-case-ahumado.png", AZIMUT_FRENTE)
ok_trasera = renderizar_vista("sam17-case-ahumado-trasera.png", AZIMUT_TRASERA)

if not (ok_frente and ok_trasera):
    sys.exit(1)
sys.exit(0)
