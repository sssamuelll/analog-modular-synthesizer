"""Puerta Blender del prototipo de boca desmontable del valle.

Uso:
  blender -b build/sam17-piezas-valle-boca.blend -P verify_valle_boca.py
"""

import atexit
import hashlib
import json
import os

import bmesh
import bpy
import sys
from mathutils.bvhtree import BVHTree

MAX_INTERSECTION_VOLUME_MM3 = 0.000001
MAX_SERVICE_INTERSECTION_MM3 = 0.000001
# Solo para contactos nominales, despues de verificar espesor y gap dimensional.
MAX_CONTACT_RESIDUAL_VOLUME_MM3 = 0.2
MIN_PANEL_CLEARANCE_MM = 0.09
MAX_MOUTH_RAIL_CLEARANCE_MM = 0.11
MAX_SUPPORT_ERROR_MM = 0.01
STRIP_COVERAGE_MM = 2.25
STRIP_THICKNESS_MM = 0.10

MOUTH = "tapa_valle_boca_prototipo"
VISIBLE = "boca_visual_valle_prototipo"
SUPPORTS = "soportes_boca_valle_prototipo"
STRIPS = "tiras_boca_valle_prototipo"
RAILS_1U = "rieles_1u_reales_prototipo"
RAILS_3U = "rieles_3u_reales_prototipo"
PANELS = "paneles"
FRAMES = "marcos_ventana"
RINGS = "anillos"
HEADS = "cabezas_m3_boca_prototipo"
TOOLS = "herramientas_m3_boca_prototipo"
EXTRACTION = "barrido_extraccion_boca_prototipo"
PANELS_EXTRACTION = "barrido_extraccion_paneles_prototipo"
SUPPORTS_EXTRACTION = "barrido_extraccion_soportes_prototipo"
AQUI = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(AQUI, "..", "cad")
SOURCE_FILES = {
    "sam17_case.scad": os.path.join(CAD, "sam17_case.scad"),
    "params.scad": os.path.join(CAD, "params.scad"),
    "piezas.scad": os.path.join(CAD, "piezas.scad"),
    "renders/piezas.py": os.path.join(AQUI, "piezas.py"),
}
_GATE_COMPLETED = False


def fail_closed_on_exit():
    if not _GATE_COMPLETED:
        os._exit(1)


atexit.register(fail_closed_on_exit)


def source_hashes():
    return {
        name: hashlib.sha256(open(path, "rb").read()).hexdigest()
        for name, path in SOURCE_FILES.items()
    }


def fail(message):
    print(f"BOCA_COLLISION_GATE FAIL: {message}", file=sys.stderr)
    sys.exit(1)

def component_vertex_sets(obj):
    neighbors = {vertex.index: set() for vertex in obj.data.vertices}
    for edge in obj.data.edges:
        a, b = edge.vertices
        neighbors[a].add(b)
        neighbors[b].add(a)
    pending = set(neighbors)
    components = []
    while pending:
        first = pending.pop()
        component = {first}
        stack = [first]
        while stack:
            current = stack.pop()
            unseen = neighbors[current] & pending
            pending.difference_update(unseen)
            component.update(unseen)
            stack.extend(unseen)
        components.append(component)
    return components


def connected_components(obj):
    return len(component_vertex_sets(obj))


def component_xy_diameters(obj):
    """Diámetro de cada componente en su sección X-Y, independiente del SCAD."""
    result = []
    for component in component_vertex_sets(obj):
        points = [obj.matrix_world @ obj.data.vertices[index].co
                  for index in component]
        result.append(max(
            ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
            for a in points for b in points
        ))
    return result


def component_xy_thicknesses(obj):
    """Eje menor de cada seccion rectangular mediante covarianza 2D."""
    result = []
    for component in component_vertex_sets(obj):
        points = sorted({
            (round((obj.matrix_world @ obj.data.vertices[index].co).x, 5),
             round((obj.matrix_world @ obj.data.vertices[index].co).y, 5))
            for index in component
        })
        cx = sum(point[0] for point in points) / len(points)
        cy = sum(point[1] for point in points) / len(points)
        xx = sum((point[0] - cx) ** 2 for point in points) / len(points)
        yy = sum((point[1] - cy) ** 2 for point in points) / len(points)
        xy = sum((point[0] - cx) * (point[1] - cy) for point in points) / len(points)
        discriminant = ((xx - yy) ** 2 + 4 * xy**2) ** 0.5
        minor = max(0.0, (xx + yy - discriminant) / 2)
        result.append(2 * minor**0.5)
    return result


def component_support_distances(obj, target_names):
    """Centro X y distancia de cada tira a cada grupo de rieles exportado."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {
        name: BVHTree.FromObject(bpy.data.objects[name], depsgraph)
        for name in target_names
    }
    result = []
    for component in component_vertex_sets(obj):
        vertices = [obj.matrix_world @ obj.data.vertices[index].co
                    for index in component]
        # Las tiras recorren todo Z, pero sus vertices caen solo en los
        # extremos, justo donde los alojamientos de soporte interrumpen el
        # contacto. Los centroides de cara prueban tambien el tramo poblado.
        points = vertices + [
            obj.matrix_world @ polygon.center
            for polygon in obj.data.polygons
            if set(polygon.vertices) <= component
        ]
        distances = {}
        for name, tree in trees.items():
            target = bpy.data.objects[name]
            inverse = target.matrix_world.inverted()
            values = []
            for point_world in points:
                nearest = tree.find_nearest(inverse @ point_world)
                if nearest[0] is not None:
                    nearest_world = target.matrix_world @ nearest[0]
                    values.append((point_world - nearest_world).length)
            distances[name] = min(values)
        result.append((sum(point.x for point in vertices) / len(vertices), distances))
    return result


def intersection_volume(a_name, b_name):
    source = bpy.data.objects[a_name]
    obj = source.copy()
    obj.data = source.data.copy()
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new(name="intersection", type="BOOLEAN")
    modifier.operation = "INTERSECT"
    modifier.solver = "EXACT"
    modifier.object = bpy.data.objects[b_name]
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    volume = abs(mesh.calc_volume(signed=True)) if mesh.faces else 0.0
    mesh.free()
    bpy.data.objects.remove(obj, do_unlink=True)
    return volume


def surface_clearance(a_name, b_name):
    """Distancia mínima bidireccional vértice--superficie entre dos mallas."""
    depsgraph = bpy.context.evaluated_depsgraph_get()

    def one_way(source_name, target_name):
        source = bpy.data.objects[source_name]
        target = bpy.data.objects[target_name]
        tree = BVHTree.FromObject(target, depsgraph)
        distances = []
        for vertex in source.data.vertices:
            point_world = source.matrix_world @ vertex.co
            point_local = target.matrix_world.inverted() @ point_world
            nearest = tree.find_nearest(point_local)
            if nearest[0] is not None:
                nearest_world = target.matrix_world @ nearest[0]
                distances.append((point_world - nearest_world).length)
        return min(distances)

    return min(one_way(a_name, b_name), one_way(b_name, a_name))


required = {
    MOUTH, STRIPS, RAILS_1U, RAILS_3U, PANELS, FRAMES, RINGS, HEADS, TOOLS,
    VISIBLE, SUPPORTS, EXTRACTION, PANELS_EXTRACTION, SUPPORTS_EXTRACTION,
}
try:
    stored_hashes = json.loads(bpy.context.scene["valle_boca_source_hashes"])
except (KeyError, TypeError, json.JSONDecodeError):
    fail("blend obsoleto o sin firma de fuentes")
if stored_hashes != source_hashes():
    fail("blend obsoleto: las fuentes cambiaron desde su generacion")
missing = sorted(required - set(bpy.data.objects.keys()))
if missing:
    fail(f"faltan objetos del prototipo: {missing}")
if "tapa_valle" in bpy.data.objects:
    fail("el blend mezcla tapa_valle de produccion con el prototipo")
if connected_components(bpy.data.objects[MOUTH]) != 4:
    fail("la boca ensamblada no contiene dos bandas y dos soportes independientes")
if connected_components(bpy.data.objects[VISIBLE]) != 2:
    fail("la boca visual no conserva sus dos bandas separables")
if connected_components(bpy.data.objects[SUPPORTS]) != 2:
    fail("los dos soportes de extremo no son independientes")
if connected_components(bpy.data.objects[STRIPS]) != 4:
    fail("las cuatro tiras de apoyo no son independientes")
strip_widths = [
    max(0.0, diameter**2 - STRIP_THICKNESS_MM**2) ** 0.5
    for diameter in component_xy_diameters(bpy.data.objects[STRIPS])
]
strip_thicknesses = component_xy_thicknesses(bpy.data.objects[STRIPS])
print("STRIP_COVERAGE_WIDTHS_MM", *[f"{width:.6f}" for width in strip_widths])
if min(strip_widths) < STRIP_COVERAGE_MM - 0.01:
    fail(f"cobertura exportada de tira insuficiente: {strip_widths}")
print("STRIP_THICKNESSES_MM", *[f"{value:.6f}" for value in strip_thicknesses])
if any(abs(value - STRIP_THICKNESS_MM) > 0.01 for value in strip_thicknesses):
    fail(f"espesor comprimido de tira incorrecto: {strip_thicknesses}")
for name in (RAILS_1U, RAILS_3U):
    materials = {material.name for material in bpy.data.objects[name].data.materials}
    if "zrail_clear" not in materials:
        fail(f"{name} no usa el material de Z-Rail plata")

supports = component_support_distances(
    bpy.data.objects[STRIPS], (RAILS_1U, RAILS_3U, MOUTH),
)
supports_1u = [(center, distances[RAILS_1U]) for center, distances in supports
               if distances[RAILS_1U] <= MAX_SUPPORT_ERROR_MM]
supports_3u = [(center, distances[RAILS_3U]) for center, distances in supports
               if distances[RAILS_3U] <= MAX_SUPPORT_ERROR_MM]
print("STRIP_SUPPORTS", supports)
if (len(supports_1u) != 2 or len(supports_3u) != 2
        or abs(supports_1u[0][0] - supports_1u[1][0]) < 40
        or abs(supports_3u[0][0] - supports_3u[1][0]) < 40):
    fail(f"apoyos 1U/3U incompletos o duplicados: {supports}")
mouth_rail_gaps = []
for index, (_, distances) in enumerate(supports):
    rail_distance = min(distances[RAILS_1U], distances[RAILS_3U])
    mouth_distance = distances[MOUTH]
    mouth_rail_gaps.append(
        mouth_distance + strip_thicknesses[index] + rail_distance
    )
    if mouth_distance > MAX_SUPPORT_ERROR_MM or rail_distance > MAX_SUPPORT_ERROR_MM:
        fail(f"tira sin contacto en ambos lados: {supports[index]}")
print("MOUTH_RAIL_CLEARANCE_MM", mouth_rail_gaps)
if any(not MIN_PANEL_CLEARANCE_MM <= value <= MAX_MOUTH_RAIL_CLEARANCE_MM
       for value in mouth_rail_gaps):
    fail(f"gap dimensional boca--riel no admite tira de 0.10: {mouth_rail_gaps}")

panel_clearance = surface_clearance(MOUTH, PANELS)
print("MOUTH_PANEL_CLEARANCE_MM", f"{panel_clearance:.9f}")
if panel_clearance < MIN_PANEL_CLEARANCE_MM:
    fail(f"holgura boca--panel insuficiente: {panel_clearance:.6f} mm")

failures = []
for pair in (
    (MOUTH, PANELS),
    (MOUTH, RAILS_1U),
    (MOUTH, RAILS_3U),
    (MOUTH, FRAMES),
    (MOUTH, RINGS),
):
    volume = intersection_volume(*pair)
    print("INTERSECTION_VOLUME_MM3", *pair, f"{volume:.9f}")
    if volume > MAX_INTERSECTION_VOLUME_MM3:
        failures.append((pair, volume))
if failures:
    fail(f"intersecciones volumetricas: {failures}")

contact_failures = []
for pair in ((MOUTH, STRIPS), (STRIPS, PANELS)):
    volume = intersection_volume(*pair)
    print("CONTACT_RESIDUAL_VOLUME_MM3", *pair, f"{volume:.9f}")
    if volume > MAX_CONTACT_RESIDUAL_VOLUME_MM3:
        contact_failures.append((pair, volume))
if contact_failures:
    fail(f"penetracion en contactos nominales: {contact_failures}")

service_failures = []
for pair in (
    (PANELS_EXTRACTION, VISIBLE),
    (SUPPORTS_EXTRACTION, VISIBLE),
    (SUPPORTS_EXTRACTION, PANELS),
    (SUPPORTS_EXTRACTION, RAILS_1U),
    (SUPPORTS_EXTRACTION, RAILS_3U),
    (SUPPORTS_EXTRACTION, RINGS),
    (EXTRACTION, RAILS_1U),
    (EXTRACTION, RAILS_3U),
    (EXTRACTION, FRAMES),
    (EXTRACTION, RINGS),
    (TOOLS, MOUTH),
    (TOOLS, PANELS),
    (TOOLS, RAILS_1U),
    (TOOLS, RAILS_3U),
    (TOOLS, FRAMES),
    (TOOLS, RINGS),
    (HEADS, PANELS),
    (HEADS, RAILS_1U),
    (HEADS, RAILS_3U),
    (HEADS, FRAMES),
    (HEADS, RINGS),
):
    volume = intersection_volume(*pair)
    print("SERVICE_INTERSECTION_VOLUME_MM3", *pair, f"{volume:.9f}")
    if volume > MAX_SERVICE_INTERSECTION_MM3:
        service_failures.append((pair, volume))
if service_failures:
    fail(f"acceso M3 obstruido: {service_failures}")

_GATE_COMPLETED = True
print("BOCA_COLLISION_GATE PASS")
