"""Render del case: acrilico naranja translucido + aluminio.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P render.py

Dos rulings de la Task 8 que no vienen del brief original:

  Encuadre (mas abajo, seccion CAMARA): calculado desde el bounding box
  REAL de las dos mallas importadas, no desde una posicion de camara fija.
  Lo unico constante es el ANGULO de vista (tres cuartos, elevado — la
  decision estetica del board); la posicion y la distancia salen del
  tamano real del ensamblado. Si params.scad cambia ancho_total o
  angulo_superior y se regenera el STL, el render se sigue encuadrando
  solo, sin tocar este script.

  Cobertura (mas abajo, seccion VERIFICACION): un PNG >100 KB no prueba
  que el case este en cuadro -- un fondo casi vacio con algo de ruido
  tambien pesa eso. Tras escribir el PNG se relee con bpy.data.images.load
  y se mide que fraccion de pixeles no es fondo. Si el case no aparece
  (camara al vacio, recorte, etc.) el script sale con codigo != 0 y un
  mensaje ROJO.

Nombres de la API de materiales (Principled BSDF) verificados a mano en
Blender 5.0.1: "Base Color", "Metallic", "Roughness" y "Transmission
Weight" existen tal cual (no ambiguos con otro Weight). Si esto cambia en
otra version, listar con print([i.name for i in n.inputs]) y ajustar.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "sam17-case.png")

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


# --- geometria y materiales --------------------------------------------
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
esc.render.filepath = SALIDA

# --- CAMARA: encuadre calculado desde el bbox real (Ruling B) -----------
# Ejes del ensamblado (ver sam17_case.scad/costado(): perfil en XY con
# linear_extrude sobre Z): X = profundidad ("fondo hacia atras"),
# Y = altura (arriba), Z = ancho. Confirmado con el bbox real del STL:
# X en [-10, 360], Y en [-5, 396], Z en [0, 500] -- coincide con el board.
esquinas = [obj.matrix_world @ Vector(c)
            for obj in (acr, alu) for c in obj.bound_box]
xs, ys, zs = ([p[i] for p in esquinas] for i in range(3))
minv = Vector((min(xs), min(ys), min(zs)))
maxv = Vector((max(xs), max(ys), max(zs)))
centro = (minv + maxv) / 2

# Angulo tres cuartos elevado (foto hero del board): desde el frente
# (X negativo respecto del centro), elevado (Y positivo) y desplazado
# hacia un costado (Z). Esto es lo UNICO fijo a mano en toda la camara.
AZIMUT = math.radians(35)      # desvio desde el frente (-X) hacia +Z
ELEVACION = math.radians(22)   # sobre la horizontal
horizontal = Vector((-math.cos(AZIMUT), 0.0, math.sin(AZIMUT)))
direccion = (horizontal * math.cos(ELEVACION)
             + Vector((0.0, math.sin(ELEVACION), 0.0))).normalized()

# Base ortonormal de la camara sin asumir Z-arriba de Blender (aqui Y es
# "arriba" del ensamblado) -- to_track_quat() de mathutils referencia
# siempre el +Z de mundo para resolver el roll, que aqui es el eje ancho,
# asi que se arma la base a mano con Y como arriba.
arriba_mundo = Vector((0.0, 1.0, 0.0))
adelante = -direccion
derecha = adelante.cross(arriba_mundo).normalized()
arriba_cam = derecha.cross(adelante).normalized()

cam_data = bpy.data.cameras.new("camara")
cam_obj = bpy.data.objects.new("camara", cam_data)
esc.collection.objects.link(cam_obj)
esc.camera = cam_obj

# Distancia: se proyectan las 16 esquinas de ambos bbox sobre los ejes
# derecha/arriba de ESTA vista concreta (no X/Y/Z crudos) y se usa el FOV
# que Blender ya calculo para 1600x1200 (cam_data.angle_x/angle_y, no un
# sensor/lens supuesto a mano).
semi_ancho = max(abs((p - centro).dot(derecha)) for p in esquinas)
semi_alto = max(abs((p - centro).dot(arriba_cam)) for p in esquinas)
MARGEN = 1.15  # aire alrededor del case en el cuadro, no pegado al borde
dist_h = semi_ancho / math.tan(cam_data.angle_x / 2)
dist_v = semi_alto / math.tan(cam_data.angle_y / 2)
distancia = max(dist_h, dist_v) * MARGEN

cam_obj.location = centro + direccion * distancia
cam_obj.rotation_euler = Matrix((derecha, arriba_cam, -adelante)).transposed().to_euler()
cam_data.clip_start = 1.0
# el clip_end de fabrica (1000) recorta en silencio si el bbox es grande
# y la distancia calculada lo supera -- ver bbox: diagonal ~700 mm.
cam_data.clip_end = max(distancia * 3.0, 2000.0)

# --- LUCES: ancladas a la camara/tamano real, no a coordenadas fijas ----
# key/fill del brief original, pero la posicion sale de la base de camara
# (derecha/arriba_cam/adelante) y la energia escala con el cuadrado de la
# distancia (ley del inverso del cuadrado: si el ensamblado crece y la
# camara se aleja proporcionalmente, hay que subir energia con distancia^2
# para mantener la misma iluminancia sobre la pieza). Constantes (4e6,
# 1.5e6, 600, 400) calibradas a ojo a distancia de referencia 700 mm.
radio = (maxv - minv).length / 2
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

esc.world = bpy.data.worlds.new("fondo")
esc.world.use_nodes = True
esc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.025, 1)

# --- RENDER ---------------------------------------------------------------
resultado = bpy.ops.render.render(write_still=True)
if resultado != {"FINISHED"}:
    print(f"ROJO: bpy.ops.render.render no devolvio FINISHED: {resultado}")
    sys.exit(1)
print("render escrito:", esc.render.filepath)


# --- VERIFICACION: cobertura real de pixeles, no el peso del PNG (Ruling A)
# El criterio "Length -lt 100kb" del brief es un proxy comodo: un render
# con el case fuera de cuadro (fondo casi entero) puede pesar de sobra por
# el ruido de Cycles y pasar esa prueba igual. Lo que importa es si el
# case esta REALMENTE en el cuadro.
def medir_cobertura(ruta_png: str) -> float:
    """Fraccion de pixeles cuyo color se aparta del fondo. El fondo real
    se toma de las 4 esquinas del PNG ya renderizado (no del RGBA lineal
    que se le paso al world) porque el view transform de color (AgX por
    defecto en Blender 4/5) no es la identidad -- comparar contra el valor
    que de verdad quedo escrito es lo unico confiable."""
    img = bpy.data.images.load(ruta_png)
    try:
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)[:, :, :3]
        fondo = np.array([px[0, 0], px[0, -1], px[-1, 0], px[-1, -1]]).mean(axis=0)
        TOLERANCIA_COLOR = 0.04  # canal 0..1; separa fondo (~0.02-0.15 tras AgX) de acrilico/aluminio
        dist = np.abs(px - fondo).max(axis=2)
        return float((dist > TOLERANCIA_COLOR).mean())
    finally:
        bpy.data.images.remove(img)


frac = medir_cobertura(SALIDA)
print(f"cobertura medida: {frac:.4f} ({frac * 100:.1f}% de pixeles no-fondo)")

# Umbral elegido a mano (juicio, no derivado): el render bueno de
# referencia (build/ actual, MARGEN=1.15) midio 0.1229 (12.3% de pixeles
# no-fondo) -- bajo porque el case es translucido/oscuro contra un fondo
# casi negro y el perfil en cuna deja aire en las esquinas del bbox, no
# porque este mal encuadrado (ver PNG). 0.05 (5%) queda comodo bajo ese
# 12.3% real para absorber variaciones legitimas de iluminacion/encuadre,
# y sigue mordiendo fuerte ante un cuadro vacio o la camara al vacio (ver
# la prueba en rojo del reporte de la Task 8, que fuerza esto a 0.0).
COBERTURA_MINIMA = 0.05
if frac < COBERTURA_MINIMA:
    print(f"ROJO: cobertura {frac:.4f} por debajo del minimo {COBERTURA_MINIMA} "
          f"-- el case no esta en cuadro (vacio, negro o recortado)")
    sys.exit(1)
print(f"cobertura VERDE: {frac:.4f} >= {COBERTURA_MINIMA}")
sys.exit(0)
