"""Las piezas de la piel LISTAS PARA IMPRIMIR: del STL de OpenSCAD al STL del
servicio, con el acabado de la referencia y las comprobaciones de impresion.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P imprimir_piel.py

Lo que hace por pieza (cachete, banda_A, banda_B):
  1. exporta el STL crudo con OpenSCAD desde cad/piel_organica.scad si esta
     viejo (misma regla que render_piel.py);
  2. REMALLA por voxeles y SUAVIZA: el extruido de OpenSCAD tiene todas las
     aristas a 90 grados, y el despiece de Samuel tiene los nervios como
     tubos blandos y el marco redondeado. Un remallado a `VOXEL` mm seguido
     de un suavizado convierte cada nervio de seccion rectangular en seccion
     casi redonda, y funde las uniones. Es lo que hace que lea a hueso y no a
     recorte de tabla. Cuesta un poco de nervio (el suavizado adelgaza): se
     mide y se imprime;
  3. comprueba lo que un servicio de impresion mira: malla cerrada (cero
     aristas no-manifold), tamano contra la bandeja MJF (380 x 284 x 380,
     cifra de catalogo sin hoja en el repo), y volumen (= gramos x 1.01 en
     PA12);
  4. escribe case/print/piel/<pieza>.stl.

Son ARTEFACTOS de salida --lo que se manda al servicio--, como los DXF del
laser: se versionan, y los regenera este guion.
"""
import os
import subprocess
import sys

import bmesh
import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(AQUI, "..", "cad")
CRUDO = os.path.join(AQUI, "build", "piel")
SALIDA = os.path.join(AQUI, "..", "print", "piel")
OPENSCAD = r"C:\Program Files\OpenSCAD\openscad.exe"
SCAD = os.path.join(CAD, "piel_organica.scad")

PIEZAS = ("cachete", "banda_A", "banda_B")
VOXEL = 0.7          # mm; los nervios son 4.2, el marco 23, la piel 6
SUAVIZADO = (0.5, 6)  # factor, iteraciones
DECIMAR = 0.35        # ratio: el remallado dispara los triangulos
BANDEJA = (380.0, 284.0, 380.0)   # MJF, mm (catalogo, de memoria)


def exportar(pieza: str) -> str:
    os.makedirs(CRUDO, exist_ok=True)
    stl = os.path.join(CRUDO, pieza + ".stl")
    fuentes = max(os.path.getmtime(os.path.join(CAD, f)) for f in
                  ("piel_organica.scad", "celosia_nervios.scad",
                   "sam17_case.scad", "params.scad"))
    if not (os.path.exists(stl) and os.path.getmtime(stl) >= fuentes):
        print("exportando", pieza, flush=True)
        r = subprocess.run([OPENSCAD, "-o", stl, "-D", f'PART="{pieza}"', SCAD],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            raise SystemExit(f"OpenSCAD fallo en {pieza}")
    return stl


def importar(stl: str):
    bpy.ops.wm.stl_import(filepath=stl)
    return bpy.context.selected_objects[0]


def acabado(obj) -> None:
    """Remallado por voxeles + suavizado + decimado, aplicados."""
    m = obj.modifiers.new("remallar", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = VOXEL
    m.use_smooth_shade = True
    s = obj.modifiers.new("suavizar", "SMOOTH")
    s.factor, s.iterations = SUAVIZADO
    d = obj.modifiers.new("decimar", "DECIMATE")
    d.ratio = DECIMAR
    bpy.context.view_layer.objects.active = obj
    for mod in ("remallar", "suavizar", "decimar"):
        bpy.ops.object.modifier_apply(modifier=mod)


def comprobar(obj, pieza: str) -> bool:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    no_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    volumen = bm.calc_volume()
    bm.free()
    dims = obj.dimensions
    cabe = all(d <= b for d, b in zip(sorted(dims, reverse=True),
                                       sorted(BANDEJA, reverse=True)))
    print(f"  {pieza}: {dims.x:.0f} x {dims.y:.0f} x {dims.z:.0f} mm, "
          f"{len(obj.data.polygons)} triangulos, volumen {volumen/1000:.0f} cm3 "
          f"(~{volumen/1000*1.01:.0f} g en PA12), aristas no-manifold {no_manifold}, "
          f"{'cabe' if cabe else 'NO CABE'} en la bandeja MJF")
    ok = no_manifold == 0 and cabe
    if not ok:
        print(f"  ROJO [{pieza}]: {'no es cerrada' if no_manifold else 'no cabe'}")
    return ok


bpy.ops.wm.read_factory_settings(use_empty=True)
os.makedirs(SALIDA, exist_ok=True)
todo_ok = True
for pieza in PIEZAS:
    stl = exportar(pieza)
    obj = importar(stl)
    obj.name = pieza
    acabado(obj)
    todo_ok &= comprobar(obj, pieza)
    salida = os.path.join(SALIDA, pieza + ".stl")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.wm.stl_export(filepath=salida, export_selected_objects=True)
    print(f"  escrito {salida}")
    bpy.data.objects.remove(obj, do_unlink=True)
sys.exit(0 if todo_ok else 1)
