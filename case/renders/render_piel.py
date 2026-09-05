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
                  ("piel_organica.scad", "celosia_celdas.scad",
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

objetos = []
for parte, material in PARTES.items():
    bpy.ops.wm.stl_import(filepath=os.path.join(DIR, parte + ".stl"))
    obj = bpy.context.selected_objects[0]
    obj.name = parte
    obj.data.materials.append(bpy.data.materials[material])
    objetos.append(obj)

# el bbox real de TODO lo importado: construir_vista() y las luces leen
# `esquinas` y `centro` de este mismo espacio de nombres
esquinas = [obj.matrix_world @ Vector(c) for obj in objetos for c in obj.bound_box]
xs, ys, zs = ([p[i] for p in esquinas] for i in range(3))
minv, maxv = Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))
ns["esquinas"] = esquinas
ns["centro"] = (minv + maxv) / 2
ns["radio"] = (maxv - minv).length / 2

ok = True
ok &= ns["renderizar_vista"]("sam17-piel.png", ns["AZIMUT_FRENTE"])
ok &= ns["renderizar_vista"]("sam17-piel-trasera.png", ns["AZIMUT_TRASERA"])
# casi de lado y un poco por encima: la celosia entera y el canto de la piel
ok &= ns["renderizar_vista"]("sam17-piel-lado.png", math.radians(78))
sys.exit(0 if ok else 1)
