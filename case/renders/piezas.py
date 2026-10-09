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
materiales de render.py -- se ejecuta hasta su bloque RENDER, sin renderizar
-- y guarda el .blend en build/. No es un artefacto del repo: build/ esta
ignorado, y esto no es una puerta ni un render que se juzgue."""
import hashlib
import json
import os
import subprocess
import sys

import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(AQUI, "..", "cad")
DIR = os.path.join(AQUI, "build", "piezas")
PROTOTIPO_BOCA = os.environ.get("SAM17_VALLE_BOCA_PROTOTIPO") == "1"
SALIDA = os.path.join(
    AQUI,
    "build",
    "sam17-piezas-valle-boca.blend" if PROTOTIPO_BOCA else "sam17-piezas.blend",
)
OPENSCAD = r"C:\Program Files\OpenSCAD\openscad.exe"
TAPA_VALLE = "tapa_valle_boca_prototipo" if PROTOTIPO_BOCA else "tapa_valle"
RIELES = (["rieles_3u_reales_prototipo", "rieles_1u_reales_prototipo"]
          if PROTOTIPO_BOCA else ["rieles_3u", "rieles_1u"])
TIRAS_VALLE = ("tiras_boca_valle_prototipo" if PROTOTIPO_BOCA
               else "tira_anti_ruido_valle")
SERVICIO_M3 = (["cabezas_m3_boca_prototipo", "herramientas_m3_boca_prototipo",
                "boca_visual_valle_prototipo", "soportes_boca_valle_prototipo",
                "barrido_extraccion_boca_prototipo",
                "barrido_extraccion_soportes_prototipo",
                "barrido_extraccion_paneles_prototipo"]
               if PROTOTIPO_BOCA else [])
ALWAYS_REBUILD = {
    "barrido_extraccion_boca_prototipo",
    "barrido_extraccion_soportes_prototipo",
    "barrido_extraccion_paneles_prototipo",
}
SOURCE_FILES = {
    "sam17_case.scad": os.path.join(CAD, "sam17_case.scad"),
    "params.scad": os.path.join(CAD, "params.scad"),
    "piezas.scad": os.path.join(CAD, "piezas.scad"),
    "renders/piezas.py": os.path.abspath(__file__),
}


def source_hashes():
    return {
        name: hashlib.sha256(open(path, "rb").read()).hexdigest()
        for name, path in SOURCE_FILES.items()
    }

# nombre de pieza -> material de render.py (o el acero, que render.py no tiene)
GRUPOS = {
    "aluminio": ["anillos", "paneles", "marcos_ventana", "nariz", "talon",
                 "miembro_alto", TAPA_VALLE] + ([] if PROTOTIPO_BOCA else RIELES),
    "junta": [TIRAS_VALLE],
    "acrilico": ["costados", "piel_trasera"],
    "madera": ["tabla", "paticas"],
    "acero": ["chasis"],
}
if PROTOTIPO_BOCA:
    GRUPOS["zrail"] = RIELES
    GRUPOS["verificacion"] = SERVICIO_M3
MATERIAL = {"acrilico": "acrilico_naranja", "madera": "nogal",
            "aluminio": "aluminio", "junta": "anti_ruido", "acero": "acero",
            "zrail": "zrail_clear", "verificacion": "acero"}


def verificar_apoyo_valle() -> None:
    """El .blend nombrado conserva el contacto tira--primer KONDOR."""
    rieles = bpy.data.objects[
        "rieles_1u_reales_prototipo" if PROTOTIPO_BOCA else "rieles_1u"
    ]
    tira = bpy.data.objects[TIRAS_VALLE]
    y_riel = max((rieles.matrix_world @ Vector(p)).y for p in rieles.bound_box)
    # El prototipo agrupa cuatro tiras en un objeto; su minimo global en Y
    # pertenece al retorno 3U inferior. Busca la superficie que realmente
    # coincide con la cara de los KONDOR en vez de medir ese bounding box.
    gap = min(
        abs((tira.matrix_world @ vert.co).y - y_riel)
        for vert in tira.data.vertices
    )
    if abs(gap) > 0.01:
        raise RuntimeError(
            f"el .blend rompe el apoyo valle--KONDOR: gap Y = {gap:.3f} mm")


def exportar_piezas() -> None:
    os.makedirs(DIR, exist_ok=True)
    scad = os.path.join(CAD, "piezas.scad")
    fuentes = max(os.path.getmtime(os.path.join(CAD, f))
                  for f in ("piezas.scad", "sam17_case.scad", "params.scad"))
    for nombres in GRUPOS.values():
        for nombre in nombres:
            stl = os.path.join(DIR, nombre + ".stl")
            # Las envolventes del gate se regeneran siempre: su malla puede
            # depender de otra pieza aunque el reloj de Windows empate mtime.
            if (nombre not in ALWAYS_REBUILD and os.path.exists(stl)
                    and os.path.getmtime(stl) >= fuentes):
                continue
            print("exportando", nombre)
            subprocess.run([OPENSCAD, "-o", stl, "-D", f'PIEZA="{nombre}"', scad],
                           check=True, capture_output=True)


exportar_piezas()

# La escena de render.py hasta su bloque RENDER: mundo, luces, camara y los
# tres materiales. Despues se quitan sus tres ensamblados y entran las piezas.
ruta_render = os.path.join(AQUI, "render.py")
fuente = open(ruta_render, encoding="utf-8").read()
ns = {"__file__": ruta_render, "__name__": "escena_case"}
exec(compile(fuente[:fuente.index("# --- RENDER: vista frontal")], ruta_render, "exec"), ns)
ns["poner_luces"](*ns["construir_vista"](ns["AZIMUT_FRENTE"]))
for obj in (ns["acr"], ns["alu"], ns["jun"], ns["mad"]):
    bpy.data.objects.remove(obj, do_unlink=True)

acero = bpy.data.materials.new("acero")
acero.use_nodes = True
n = acero.node_tree.nodes["Principled BSDF"]
n.inputs["Base Color"].default_value = (0.45, 0.46, 0.48, 1)
n.inputs["Metallic"].default_value = 1.0
n.inputs["Roughness"].default_value = 0.45

zrail = bpy.data.materials.new("zrail_clear")
zrail.use_nodes = True
n = zrail.node_tree.nodes["Principled BSDF"]
n.inputs["Base Color"].default_value = (0.58, 0.60, 0.64, 1)
n.inputs["Metallic"].default_value = 1.0
n.inputs["Roughness"].default_value = 0.30

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
        if grupo == "verificacion":
            obj.hide_render = True
            obj.hide_viewport = True

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

if PROTOTIPO_BOCA:
    bpy.context.scene["valle_boca_source_hashes"] = json.dumps(
        source_hashes(), sort_keys=True,
    )
bpy.ops.wm.save_as_mainfile(filepath=SALIDA)
print("blend escrito:", SALIDA)
sys.exit(0)
