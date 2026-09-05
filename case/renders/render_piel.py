"""Renders de la PIEL ORGANICA (propuesta 2026-09-05): el case con la piel del
concepto de Samuel en vez de las cinco chapas y acrilicos que sustituye.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P render_piel.py

Reutiliza la escena de render.py entera --mundo, luces, camara, materiales y
las dos metricas-- ejecutandolo hasta su bloque RENDER, igual que piezas.py.
Luego quita sus cuatro ensamblados y mete los de cad/piel_organica.scad, en
cinco STL: mejillas y banda (la piel, blanca), aluminio, acrilico (la trasera)
y madera. Tres vistas: las dos de siempre y una tercera casi de lado, que es
la unica desde la que se juzga la celosia.

No es una puerta: es lo que se mira para decidir. Y por eso re-exporta si el
.scad es mas nuevo que el STL: un render del modelo de hace tres horas es peor
que ninguno (render.py, importar()).
"""
import math
import os
import subprocess
import sys

import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(AQUI, "..", "cad")
DIR = os.path.join(AQUI, "build", "piel")
OPENSCAD = r"C:\Program Files\OpenSCAD\openscad.exe"
SCAD = os.path.join(CAD, "piel_organica.scad")

# parte -> material (los tres de render.py mas dos que se crean aqui: la piel
# y el panel oscuro)
PARTES = {"mejillas": "piel", "banda": "piel", "aluminio": "aluminio",
          "paneles": "panel_oscuro", "acrilico": "acrilico_naranja",
          "madera": "nogal"}


def exportar() -> None:
    os.makedirs(DIR, exist_ok=True)
    fuentes = max(os.path.getmtime(os.path.join(CAD, f)) for f in
                  ("piel_organica.scad", "celosia_nervios.scad",
                   "sam17_case.scad", "params.scad"))
    for parte in PARTES:
        stl = os.path.join(DIR, parte + ".stl")
        if os.path.exists(stl) and os.path.getmtime(stl) >= fuentes:
            continue
        print("exportando", parte, flush=True)
        r = subprocess.run([OPENSCAD, "-o", stl, "-D", f'PART="{parte}"', SCAD],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            raise SystemExit(f"OpenSCAD fallo en {parte}")


exportar()

ruta_render = os.path.join(AQUI, "render.py")
fuente = open(ruta_render, encoding="utf-8").read()
ns = {"__file__": ruta_render, "__name__": "escena_case"}
exec(compile(fuente[:fuente.index("# --- RENDER: vista frontal")], ruta_render, "exec"), ns)
for obj in (ns["acr"], ns["alu"], ns["jun"], ns["mad"]):
    bpy.data.objects.remove(obj, do_unlink=True)

# LA PIEL: blanca, mate, un poco cerosa -- nylon MJF tenido o resina. Sin
# metallic, roughness alta, y algo de subsuperficie para que la celosia no
# lea como carton. Es color de mirar, no cota.
piel = ns["mat"]("piel", **{"Base Color": (0.93, 0.93, 0.90, 1.0),
                            "Roughness": 0.55, "Metallic": 0.0})
try:
    n = piel.node_tree.nodes["Principled BSDF"]
    n.inputs["Subsurface Weight"].default_value = 0.12
except KeyError:
    pass
# LOS PANELES, oscuros: aluminio anodizado grafito, como en el concepto. Es
# el contraste que hace la idea -- panel duro dentro de marco blando -- y con
# el aluminio claro de render.py se fundian con la piel (visto en el primer
# render, 05-09). Color de mirar, no cota.
ns["mat"]("panel_oscuro", **{"Base Color": (0.10, 0.105, 0.115, 1.0),
                             "Metallic": 0.9, "Roughness": 0.38})

def _importar(ruta, nombre, material, dz=0.0):
    bpy.ops.wm.stl_import(filepath=ruta)
    obj = bpy.context.selected_objects[0]
    obj.name = nombre
    obj.location.z += dz
    obj.data.materials.append(bpy.data.materials[material])
    return obj


PRINT = os.path.join(AQUI, "..", "print", "piel")
objetos = []
for parte, material in PARTES.items():
    # PIEL_IMPRESA=1: la piel se importa de case/print/piel --lo que sale de
    # imprimir_piel.py, remallado y suavizado-- y no del extruido crudo. Es lo
    # que se imprime, asi que es lo que se mira. El cachete es UNA pieza que
    # va dos veces: a la izquierda (z = -piel_e) y a la derecha (z = ancho).
    if os.environ.get("PIEL_IMPRESA") and parte == "mejillas":
        ruta = os.path.join(PRINT, "cachete.stl")
        objetos.append(_importar(ruta, "cachete_izq", material, dz=-6.0))
        objetos.append(_importar(ruta, "cachete_der", material, dz=568.62))
        continue
    if os.environ.get("PIEL_IMPRESA") and parte == "banda":
        for mitad in ("banda_A", "banda_B"):
            objetos.append(_importar(os.path.join(PRINT, mitad + ".stl"), mitad, material))
        continue
    objetos.append(_importar(os.path.join(DIR, parte + ".stl"), parte, material))

# el bbox real de TODO lo importado: construir_vista() y las luces leen
# `esquinas` y `centro` de este mismo espacio de nombres
esquinas = [obj.matrix_world @ Vector(c) for obj in objetos for c in obj.bound_box]
xs, ys, zs = ([p[i] for p in esquinas] for i in range(3))
minv, maxv = Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))
ns["esquinas"] = esquinas
ns["centro"] = (minv + maxv) / 2
ns["radio"] = (maxv - minv).length / 2

# PIEL_BLEND=1: en vez de renderizar, guarda la escena en build/sam17-piel.blend
# con cada pieza como objeto con su nombre --mejillas, banda, aluminio,
# paneles, acrilico, madera-- para abrirla en Blender y girarla. Es lo que
# Samuel pidio el 05-09 ("necesito ver el render para decidir"): un PNG es
# una vista, el .blend son todas. Mismo mecanismo que piezas.py; build/ esta
# ignorado y esto no es un artefacto del repo.
if os.environ.get("PIEL_BLEND"):
    ns["poner_luces"](*ns["construir_vista"](ns["AZIMUT_FRENTE"]))
    for pantalla in bpy.data.screens:
        for area in pantalla.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type != "VIEW_3D":
                    continue
                space.shading.type = "MATERIAL"
                space.shading.use_scene_lights = True
                space.shading.use_scene_world = True
                space.clip_start = 1.0
                space.clip_end = 20000.0
                space.region_3d.view_perspective = "CAMERA"
    salida = os.path.join(AQUI, "build", "sam17-piel.blend")
    bpy.ops.wm.save_as_mainfile(filepath=salida)
    print("blend escrito:", salida)
    sys.exit(0)

# PIEL_VISTAS=lado para iterar la celosia con una sola vista (~4 min) en vez
# de tres; sin la variable salen las tres.
VISTAS = {"frente": ("sam17-piel.png", ns["AZIMUT_FRENTE"]),
          "trasera": ("sam17-piel-trasera.png", ns["AZIMUT_TRASERA"]),
          # casi de lado y un poco por encima: la celosia entera y el canto
          "lado": ("sam17-piel-lado.png", math.radians(78))}
pedidas = os.environ.get("PIEL_VISTAS", "frente,trasera,lado").split(",")
ok = True
for v in pedidas:
    nombre, azimut = VISTAS[v.strip()]
    ok &= ns["renderizar_vista"](nombre, azimut)
sys.exit(0 if ok else 1)
