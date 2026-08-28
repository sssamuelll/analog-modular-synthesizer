"""Render del case: acrilico naranja translucido + aluminio.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P render.py

Dos vistas (frontal y trasera, Fix round 1 FIX 3), mismo pipeline. Tres
rulings/fixes de la Task 8 que no vienen del brief original:

  Encuadre (seccion "bbox real" + construir_vista): calculado desde el
  bounding box REAL de las dos mallas importadas, no desde una posicion de
  camara fija. Lo unico constante es el ANGULO de vista (tres cuartos,
  elevado -- la decision estetica del board); posicion y distancia salen
  del tamano real del ensamblado. Si params.scad cambia ancho_total o
  angulo_superior y se regenera el STL, el render se sigue encuadrando
  solo, sin tocar este script.

  Verificacion (medir() + renderizar_vista): un PNG >100 KB no prueba que
  el case este en cuadro NI que se vea -- ver Fix round 1. Tras escribir
  cada PNG se relee con bpy.data.images.load y se miden dos cosas sobre
  los pixeles que no son fondo: la FRACCION del cuadro que ocupan
  (cobertura) y el BRILLO medio (para no dejar pasar un render tecnicamente
  "en cuadro" pero tan oscuro que no se distingue del fondo). Si cualquiera
  de las dos vistas falla cualquiera de los dos umbrales, el script sale
  con codigo != 0 y un mensaje ROJO.

  Iluminacion (mundo con Light Path / Is Camera Ray): el fondo oscuro
  original (visible a camara, como en el board) tambien era la UNICA luz
  de entorno, y con eso el metal/acrilico en sombra o transmitido rendeaba
  casi del color del fondo -- el naranja leia marron. Se desacopla: la
  camara sigue viendo el fondo oscuro, pero el resto de los rayos
  (rebotes, transmision, reflejos) ven un fondo mucho mas brillante que
  ilumina la pieza sin aclarar el fondo visible. Medido en el Fix round 1:
  esto solo subio el brillo de 0.051 a ~0.60-0.64 Y la cobertura de 0.123 a
  ~0.34 (pixeles que antes eran indistinguibles del fondo casi negro ahora
  se distinguen -- ver comentario de MARGEN mas abajo).

Nombres de la API de materiales (Principled BSDF) verificados a mano en
Blender 5.0.1: "Base Color", "Metallic", "Roughness" y "Transmission
Weight" existen tal cual (no ambiguos con otro Weight). Si esto cambia en
otra version, listar con print([i.name for i in n.inputs]) y ajustar.

Task 6: se anaden "Anisotropic" y "Anisotropic Rotation" para el aluminio
cepillado -- RECONFIRMADOS igual a mano (mismo metodo, Blender 5.0) antes
de tocar el material: existen tal cual, sin ambiguedad.
"""
import math
import os
import sys

import bpy
import numpy as np
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
    "acrilico_naranja", **{
        "Base Color": (1.0, 0.24, 0.04, 1.0),
        "Roughness": 0.08,
        "Transmission Weight": 0.85,
    }))
alu = importar("assembly_aluminio")
# CEPILLADO, no pulido (Tarea 6). FIX ROUND 1: el primer intento subia
# Anisotropic a 0.6 para simular la microestria del cepillado -- y en el
# render salia PLASTICO MATE BLANCO, sin grano y casi sin contraste
# especular. La causa no era el valor: es que las mallas vienen de STL SIN
# UV NI TANGENTE. Sin un mapa de tangente por cara, Cycles arma una base
# tangente ARBITRARIA por triangulo para el lobulo anisotropico -- cada
# triangulo "cepilla" en una direccion distinta y sin relacion con la pasada
# real de la herramienta, asi que lo que deberia leerse como grano se
# promedia a RUIDO, no a brillo estirado. Anisotropic vuelve a 0.0: es la
# opcion honesta mientras no haya geometria con tangente real por pieza (un
# mapa de tangente por UV es el siguiente paso si hace falta el grano de
# verdad, no antes).
#
# LO QUE SI LEE COMO METAL sin mentir sobre un grano que no esta modelado:
# Roughness mas bajo (0.28 -> 0.25, un pelo mas especular) y Base Color mas
# oscuro/neutro (0.80,0.81,0.83 -> 0.72,0.73,0.75, menos "blanco lavado") --
# y la luz KEY mas chica y mas fuerte (ver poner_luces()), para que la
# arista tenga un highlight definido en vez de un degradado ancho y suave.
alu.data.materials.append(mat(
    "aluminio", **{"Base Color": (0.72, 0.73, 0.75, 1.0),
                   "Metallic": 1.0, "Roughness": 0.25,
                   "Anisotropic": 0.0, "Anisotropic Rotation": 0.0}))
# LA TABLA, en su propio STL desde el 2026-08-27. Estuvo dentro del ensamblado
# de acrilico mientras el suelo era PMMA, y meterla ahi ahora la pintaria de
# naranja translucido: un render que miente sobre una decision de material.
#
# EL COLOR ES DE MIRAR, NO UNA COTA -- igual que el naranja del acrilico (ver
# README). La especie no esta elegida: las cuentas del modelo van contra
# E = 11000 MPa, que es nogal o arce, y esto es un nogal de catalogo. Cuando
# el pliego cierre la especie, este numero se cambia aqui y en ningun otro
# sitio. Sin Metallic y con roughness alto: la madera no brilla.
mad = importar("assembly_madera")
mad.data.materials.append(mat(
    "nogal", **{"Base Color": (0.28, 0.16, 0.09, 1.0),
                "Roughness": 0.55, "Specular IOR Level": 0.35}))

esc = bpy.context.scene
esc.render.engine = "CYCLES"
esc.cycles.samples = 256
esc.render.resolution_x, esc.render.resolution_y = 1600, 1200
esc.render.image_settings.file_format = "PNG"
# Standard, no AgX (el default de Blender 4/5): AgX desatura y apaga los
# colores saturados. Confirmado a mano (Fix round 1): con la MISMA luz de
# relleno GI, AgX midio brillo 0.5842 sobre la pieza y Standard 0.6370 --
# ambos con luz corregida, pero el punto es que Standard no le suma
# compresion de gamut encima al naranja. Es la palanca secundaria (la
# principal fue el relleno GI, ver el mundo mas abajo).
esc.view_settings.view_transform = "Standard"

# --- mundo: fondo oscuro para la camara, relleno GI brillante (Fix 1) ----
# Truco estandar de Cycles (Light Path -> Is Camera Ray -> Mix Shader): la
# camara ve "fondo_visible" (oscuro, igual que antes -- el look del
# board), el resto de los rayos ven "fondo_gi" (brillante, ilumina sin
# aclarar lo que se ve). Sin esto, el fondo oscuro era la UNICA fuente de
# luz de entorno y el metal/transmision en sombra rendeaba casi negro.
mundo = bpy.data.worlds.new("fondo")
mundo.use_nodes = True
nt = mundo.node_tree
fondo_visible = nt.nodes["Background"]
fondo_visible.inputs[0].default_value = (0.02, 0.02, 0.025, 1)  # lo que ve la camara
fondo_gi = nt.nodes.new("ShaderNodeBackground")
fondo_gi.inputs[0].default_value = (0.6, 0.6, 0.63, 1)          # relleno GI, invisible a camara
ruta_luz = nt.nodes.new("ShaderNodeLightPath")
mezcla = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(ruta_luz.outputs["Is Camera Ray"], mezcla.inputs[0])
nt.links.new(fondo_gi.outputs["Background"], mezcla.inputs[1])       # Fac=0 (no camara) -> GI
nt.links.new(fondo_visible.outputs["Background"], mezcla.inputs[2])  # Fac=1 (camara)    -> oscuro
nt.links.new(mezcla.outputs["Shader"], nt.nodes["World Output"].inputs["Surface"])
esc.world = mundo

# --- bbox real de las 3 mallas (Ruling B) --------------------------------
# El chasis de acero del PSU (#107) NO se importa aqui, y se probo: se rendeo
# con el dentro y no se ve en ninguna de las dos vistas -- vive en el piso
# inferior, detras de los paneles y de la piel. Meterlo costaba minutos de
# Cycles y 3,8 MB de diff en dos PNG que salian identicos. Para verlo estan
# las vistas de OpenSCAD (build/vista_chasis_*.png) y el plano de plegado.
# Ejes del ensamblado (sam17_case.scad/costado(): perfil en XY con
# linear_extrude sobre Z): X = profundidad, Y = altura (arriba),
# Z = ancho. Confirmado con el bbox real: X en [-10, 360], Y en [-5, 396],
# Z en [0, 500] -- coincide con el board.
# LAS TRES MALLAS, no dos. La tabla sobresale 10 mm del cuerpo por los cuatro
# lados y es lo mas bajo del case: dejarla fuera del bbox encuadra un aparato
# que no es el que se ve, y el zocalo saldria cortado por abajo.
esquinas = [obj.matrix_world @ Vector(c)
            for obj in (acr, alu, mad) for c in obj.bound_box]
xs, ys, zs = ([p[i] for p in esquinas] for i in range(3))
minv = Vector((min(xs), min(ys), min(zs)))
maxv = Vector((max(xs), max(ys), max(zs)))
centro = (minv + maxv) / 2
radio = (maxv - minv).length / 2

ELEVACION = math.radians(22)   # sobre la horizontal -- estetica, fija
# Tres cuartos elevado (foto hero del board): frente = mayormente -X
# (delante del case) con desvio hacia +Z. Trasera (Fix round 1, FIX 3):
# espejo sobre el eje de profundidad (pi - azimut), mismo costado +Z -- no
# es un numero nuevo, es el mismo AZIMUT_FRENTE reflejado.
AZIMUT_FRENTE = math.radians(35)
AZIMUT_TRASERA = math.pi - AZIMUT_FRENTE
# Aire alrededor del case en el cuadro, no pegado al borde. Con el fix de
# brillo la cobertura ya cae en el rango pedido (30-45%, medido 34.2%) SIN
# tocar este valor -- la causa real del 12.3% original no era margen de
# camara de mas (Fix round 1, FIX 2): era que gran parte de la silueta
# rendeaba casi del mismo color que el fondo y la metrica no la contaba.
# Verificado con el diagnostico de exposicion, no supuesto.
MARGEN = 1.15


def construir_vista(azimut: float):
    """Base de camara para un azimut dado. Devuelve (derecha, arriba_cam,
    adelante, distancia) -- todo derivado del bbox real + FOV real de
    Blender para esta resolucion, nada hardcodeado (Ruling B)."""
    horizontal = Vector((-math.cos(azimut), 0.0, math.sin(azimut)))
    direccion = (horizontal * math.cos(ELEVACION)
                 + Vector((0.0, math.sin(ELEVACION), 0.0))).normalized()
    # Base ortonormal a mano (no to_track_quat(), que referencia siempre
    # el +Z de mundo para el roll; aqui Y es "arriba" del ensamblado).
    arriba_mundo = Vector((0.0, 1.0, 0.0))
    adelante = -direccion
    derecha = adelante.cross(arriba_mundo).normalized()
    arriba_cam = derecha.cross(adelante).normalized()

    cam_data = bpy.data.cameras.new("camara")
    cam_obj = bpy.data.objects.new("camara", cam_data)
    esc.collection.objects.link(cam_obj)
    esc.camera = cam_obj

    # Distancia: proyecta las 16 esquinas de ambos bbox sobre los ejes
    # derecha/arriba de ESTA vista concreta y usa el FOV que Blender ya
    # calculo para 1600x1200 (cam_data.angle_x/angle_y), no un sensor/lente
    # supuesto a mano.
    semi_ancho = max(abs((p - centro).dot(derecha)) for p in esquinas)
    semi_alto = max(abs((p - centro).dot(arriba_cam)) for p in esquinas)
    dist_h = semi_ancho / math.tan(cam_data.angle_x / 2)
    dist_v = semi_alto / math.tan(cam_data.angle_y / 2)
    distancia = max(dist_h, dist_v) * MARGEN

    cam_obj.location = centro + direccion * distancia
    cam_obj.rotation_euler = Matrix((derecha, arriba_cam, -adelante)).transposed().to_euler()
    cam_data.clip_start = 1.0
    # el clip_end de fabrica (1000) recorta en silencio a esta escala (bbox
    # diagonal ~700 mm y la distancia calculada lo supera).
    cam_data.clip_end = max(distancia * 3.0, 2000.0)
    return derecha, arriba_cam, adelante, distancia


def poner_luces(derecha: Vector, arriba_cam: Vector, adelante: Vector, distancia: float) -> None:
    """Key/fill ancladas a la base de camara de ESTA vista (no coordenadas
    de mundo fijas) y escaladas con el cuadrado de la distancia (inverso
    del cuadrado: si el ensamblado crece y la camara se aleja
    proporcionalmente, hay que subir energia con distancia^2 para mantener
    la misma iluminancia sobre la pieza). Constantes de FILL (1.5e6, 400)
    calibradas a ojo a distancia de referencia 700 mm -- probado que
    subirlas x4 no mueve el brillo casi nada (Fix round 1 de otra tarea,
    ronda de diagnostico 1): la palanca real ahi era el relleno GI del
    mundo, no esto. Quita las luces de la vista anterior antes de poner las
    nuevas -- si no, se suman e iluminan la vista siguiente desde el lado
    equivocado.

    LA KEY CAMBIA EN Fix round 1 DE LA TAREA 6: tamano a la mitad (600 ->
    300 * esc_luz) y energia al doble (4e6 -> 8e6 * esc_luz^2). Con el
    aluminio en Roughness bajo y SIN anisotropico (ver el material en el
    bloque de arriba -- sin UV/tangente por pieza, el lobulo anisotropico
    solo anadia ruido), una luz de area grande y suave da un degradado
    ancho sin punto de brillo: una fuente mas chica y mas intensa concentra
    el highlight especular en la arista real -- que es lo que un ojo lee
    como "metal", no el tono de gris de fondo. La energia sube con el
    cuadrado del tamano para que el area bajo la curva de luz (y por tanto
    el brillo medio que mide medir()) no caiga: una fuente 1/2 de tamano
    necesita ~4x la radiancia para verter la misma potencia total."""
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    esc_luz = distancia / 700.0
    bpy.ops.object.light_add(type="AREA", location=centro + arriba_cam * radio * 1.3
                              + derecha * radio * 0.7 + adelante * distancia * 0.4)
    key = bpy.context.object
    key.data.energy = 8e6 * esc_luz ** 2
    key.data.size = 300 * esc_luz
    bpy.ops.object.light_add(type="AREA", location=centro - derecha * radio * 1.1
                              + arriba_cam * radio * 0.4 + adelante * distancia * 0.25)
    fill = bpy.context.object
    fill.data.energy = 1.5e6 * esc_luz ** 2
    fill.data.size = 400 * esc_luz


def medir(ruta_png: str) -> tuple[float, float]:
    """Cobertura (fraccion de pixeles no-fondo) y brillo medio de esos
    pixeles no-fondo, ambos sobre el PNG YA renderizado (post
    view-transform): el fondo real se toma de las 4 esquinas del PNG, no
    del RGBA lineal que se le paso al world, porque el view transform no
    es la identidad -- comparar contra lo que de verdad quedo escrito es
    lo unico confiable."""
    img = bpy.data.images.load(ruta_png)
    try:
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)[:, :, :3]
        fondo = np.array([px[0, 0], px[0, -1], px[-1, 0], px[-1, -1]]).mean(axis=0)
        TOLERANCIA_COLOR = 0.04  # canal 0..1; separa fondo (~0.15 con Standard) de acrilico/aluminio
        dist = np.abs(px - fondo).max(axis=2)
        mascara = dist > TOLERANCIA_COLOR
        frac = float(mascara.mean())
        brillo = float(px[mascara].mean()) if mascara.any() else 0.0
        return frac, brillo
    finally:
        bpy.data.images.remove(img)


# Umbrales elegidos a mano (juicio, no derivado), calibrados contra DOS
# renders reales, no uno solo:
#   - el render SUBEXPUESTO de la Task 8 original (antes de este fix):
#     cobertura 0.1229, brillo 0.0509 -- tiene que dar ROJO con la metrica
#     de brillo nueva (antes no existia).
#   - el render corregido de mas abajo: cobertura ~0.34, brillo ~0.60-0.64.
# COBERTURA_MINIMA se deja en 0.05 (ya mordia bien, sigue mordiendo -- ver
# prueba en rojo del reporte). BRILLO_MINIMO en 0.20: por encima del 0.0509
# del render viejo (para que ESE caso de verdad falle si se repite) y
# comodo por debajo del ~0.60 del render bueno.
COBERTURA_MINIMA = 0.05
BRILLO_MINIMO = 0.20


def renderizar_vista(nombre_archivo: str, azimut: float) -> bool:
    derecha, arriba_cam, adelante, distancia = construir_vista(azimut)
    poner_luces(derecha, arriba_cam, adelante, distancia)

    ruta = os.path.join(AQUI, nombre_archivo)
    esc.render.filepath = ruta
    resultado = bpy.ops.render.render(write_still=True)
    if resultado != {"FINISHED"}:
        print(f"ROJO [{nombre_archivo}]: bpy.ops.render.render no devolvio FINISHED: {resultado}")
        return False
    print(f"render escrito: {ruta}")

    frac, brillo = medir(ruta)
    print(f"{nombre_archivo}: cobertura={frac:.4f} ({frac * 100:.1f}%) brillo={brillo:.4f}")

    ok = True
    if frac < COBERTURA_MINIMA:
        print(f"ROJO [{nombre_archivo}]: cobertura {frac:.4f} por debajo del minimo {COBERTURA_MINIMA} "
              f"-- el case no esta en cuadro (vacio, negro o recortado)")
        ok = False
    if brillo < BRILLO_MINIMO:
        print(f"ROJO [{nombre_archivo}]: brillo {brillo:.4f} por debajo del minimo {BRILLO_MINIMO} "
              f"-- se ve casi negro/apagado, no como acrilico naranja iluminado")
        ok = False
    if ok:
        print(f"VERDE [{nombre_archivo}]: cobertura {frac:.4f} >= {COBERTURA_MINIMA}, "
              f"brillo {brillo:.4f} >= {BRILLO_MINIMO}")
    return ok


# --- RENDER: vista frontal (brief original) + vista trasera (Fix round 1,
# FIX 3 -- una vista tres cuartos frontal no puede mostrar, por geometria,
# las ranuras de ventilacion en onda de las pieles traseras) -------------
ok_frente = renderizar_vista("sam17-case.png", AZIMUT_FRENTE)
ok_trasera = renderizar_vista("sam17-case-trasera.png", AZIMUT_TRASERA)

if not (ok_frente and ok_trasera):
    sys.exit(1)
sys.exit(0)
