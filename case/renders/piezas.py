"""El case en Blender con CADA PIEZA como objeto propio y con el nombre del repo.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P piezas.py
    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" build\\sam17-piezas.blend

Existe porque el 2026-08-29 Samuel pidio "que me ensenes a identificarte mejor
las piezas": una captura de Blender con una flecha roja costo media hora de
averiguar de que pieza hablaba. Aqui cada pieza es un objeto que se llama como
su modulo en sam17_case.scad -- `bahia`, `nariz`, `miembro_alto`... -- asi que
se hace clic, se lee el nombre en el Outliner y ese nombre es el del repo.

Exporta cada pieza con OpenSCAD desde cad/piezas.scad (solo las que falten o
esten mas viejas que el .scad), reusa el mundo, las luces, la camara y los
materiales de render.py -- la escena, que no renderiza nada -- y guarda el .blend en build/. No es un artefacto del repo: build/ esta
ignorado, y esto no es una puerta ni un render que se juzgue."""
import os
import subprocess
import sys

import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(AQUI, "..", "cad")
DIR = os.path.join(AQUI, "build", "piezas")
SALIDA = os.path.join(AQUI, "build", "sam17-piezas.blend")
OPENSCAD = r"C:\Program Files\OpenSCAD\openscad.exe"

# nombre de pieza -> material de render.py (o el acero, que render.py no tiene)
GRUPOS = {
    "aluminio": ["anillos", "rieles_3u", "rieles_1u", "paneles", "marcos_ventana",
                 "nariz", "talon", "miembro_alto", "tapa_valle", "persianas", "base"],
    "junta": ["tira_anti_ruido_valle"],
    "acrilico": ["piel_trasera"],
    "goma": ["paticas"],
    "acero": ["chasis"],
}
MATERIAL = {"acrilico": "acrilico_naranja", "goma": "goma",
            "aluminio": "aluminio", "junta": "anti_ruido", "acero": "acero"}


def verificar_apoyo_valle() -> None:
    """El .blend nombrado conserva el contacto tira--primer KONDOR."""
    rieles = bpy.data.objects["rieles_1u"]
    tira = bpy.data.objects["tira_anti_ruido_valle"]
    y_riel = max((rieles.matrix_world @ Vector(p)).y for p in rieles.bound_box)
    y_tira = min((tira.matrix_world @ Vector(p)).y for p in tira.bound_box)
    gap = y_tira - y_riel
    if abs(gap) > 0.01:
        raise RuntimeError(
            f"el .blend rompe el apoyo valle--KONDOR: gap Y = {gap:.3f} mm")


def exportar_piezas() -> None:
    os.makedirs(DIR, exist_ok=True)
    scad = os.path.join(CAD, "piezas.scad")
    fuentes = max(os.path.getmtime(os.path.join(CAD, f))
                  for f in ("piezas.scad", "sam17_case.scad", "params.scad",
                            "persiana_generada.scad"))
    for nombres in GRUPOS.values():
        for nombre in nombres:
            stl = os.path.join(DIR, nombre + ".stl")
            if os.path.exists(stl) and os.path.getmtime(stl) >= fuentes:
                continue
            print("exportando", nombre)
            subprocess.run([OPENSCAD, "-o", stl, "-D", f'PIEZA="{nombre}"', scad],
                           check=True, capture_output=True)


exportar_piezas()

# La escena de render.py, que no renderiza nada: mundo, luces, camara y los
# tres materiales. Despues se quitan sus tres ensamblados y entran las piezas.
ruta_render = os.path.join(AQUI, "render.py")
fuente = open(ruta_render, encoding="utf-8").read()
ns = {"__file__": ruta_render, "__name__": "escena_case"}
exec(compile(fuente, ruta_render, "exec"), ns)
ns["poner_luces"](*ns["construir_vista"](ns["AZIMUT_FRENTE"]))
for obj in (ns["acr"], ns["alu"], ns["jun"], ns["pat"]):
    bpy.data.objects.remove(obj, do_unlink=True)

acero = bpy.data.materials.new("acero")
acero.use_nodes = True
n = acero.node_tree.nodes["Principled BSDF"]
n.inputs["Base Color"].default_value = (0.45, 0.46, 0.48, 1)
n.inputs["Metallic"].default_value = 1.0
n.inputs["Roughness"].default_value = 0.45

for grupo, nombres in GRUPOS.items():
    col = bpy.data.collections.new(grupo)
    bpy.context.scene.collection.children.link(col)
    for nombre in nombres:
        bpy.ops.wm.stl_import(filepath=os.path.join(DIR, nombre + ".stl"))
        obj = bpy.context.selected_objects[0]
        obj.name = nombre
        obj.data.name = nombre
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        col.objects.link(obj)
        obj.data.materials.append(bpy.data.materials[MATERIAL[grupo]])

try:
    verificar_apoyo_valle()
except RuntimeError as exc:
    print(f"ROJO: {exc}", file=sys.stderr)
    sys.exit(1)

# que al abrir el archivo se vea algo: Material Preview con las luces y el mundo de la
# escena, mirando por la camara, y el clip subido -- el de fabrica (1000)
# recorta a esta escala.
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

bpy.ops.wm.save_as_mainfile(filepath=SALIDA)
print("blend escrito:", SALIDA)
sys.exit(0)
