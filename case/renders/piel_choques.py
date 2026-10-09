"""Las reglas de la PIEL IMPRESA que las tres comprobaciones de siempre no ven
(Blender). Las usan imprimir_piel.py, al terminar, y check_piel.py, la puerta.

    blender -b --factory-startup -P piel_choques.py -- salida.json

POR QUE (ficha 16 de la revision del 2026-10-09): el cachete de la placa
pasaba las tres de imprimir_piel.comprobar() --cerrado, cabe en la bandeja,
gramos-- y salia en SIETE islas (la celosia suelta a 6 mm del marco y cinco
migas), con el marco 5.9 mm dentro de la tabla y pisando la cubierta en todo
el borde. Ninguna de las tres miraba eso. Dos reglas:

  1. UNA ISLA por pieza. Una pieza impresa que sale en dos es dos piezas, y la
     que no toca a la otra se cae al sacarla de la maquina.
  2. NINGUNA PIEZA DENTRO DE OTRA: cada pieza de la piel contra las otras y
     contra lo que ya existe (tabla, anillos y rieles, paneles, trasera). Se
     mide la PROFUNDIDAD: los vertices de A que caen dentro de B y a que
     distancia de su cara. Apoyar cara contra cara se permite hasta TOL.

Las piezas se colocan como en render_piel.py: el cachete derecho contra la
cara exterior del anillo derecho (z = ancho_total), el izquierdo en z = 0.
"""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

AQUI = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(AQUI, "..")
PRINT = os.environ.get("PIEL_SALIDA", os.path.join(CASE, "print", "piel"))   # PIEL_SALIDA: variantes para escoger

# Cuanto puede entrar una pieza en otra sin que sea un choque. La cubierta se
# remalla a 0.8 mm (imprimir_piel.VOXEL_CUBIERTA): el remallado mueve cada cara
# hasta medio voxel, asi que una cara que apoya en el anillo puede salir 0.4 mm
# metida sin que nadie la haya dibujado asi. 0.5 cubre eso y no esconde nada
# que se pueda montar mal: el choque mas pequeno que encontro la revision del
# 09-10 son 5.9 mm.
TOL = 0.5
PIEL = ("cachete_der", "cachete_izq", "cubierta")
PARTES = ("madera", "aluminio", "paneles", "acrilico")


def ancho_total() -> float:
    if CASE not in sys.path:
        sys.path.insert(0, CASE)
    import clearance_budget as cb
    return float(cb.leer_params()["ancho_total"])


def colocar(ob, pieza: str) -> None:
    """La misma colocacion que render_piel.PIEL."""
    if pieza == "cachete_der":
        ob.location.z += ancho_total()


def islas(ob) -> list[dict]:
    """Las piezas sueltas de una malla, de mayor a menor: caras y caja."""
    bpy.ops.object.select_all(action="DESELECT")
    copia = ob.copy()
    copia.data = ob.data.copy()
    bpy.context.collection.objects.link(copia)
    copia.select_set(True)
    bpy.context.view_layer.objects.active = copia
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-4)
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    trozos = list(bpy.context.selected_objects)
    res = []
    for t in trozos:
        co = np.empty(len(t.data.vertices) * 3)
        t.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3) @ np.array(t.matrix_world)[:3, :3].T + np.array(t.matrix_world)[:3, 3]
        res.append(dict(caras=len(t.data.polygons), lo=co.min(0).round(1).tolist(),
                        hi=co.max(0).round(1).tolist()))
    for t in trozos:
        bpy.data.objects.remove(t, do_unlink=True)
    return sorted(res, key=lambda r: -r["caras"])


def _mundo(ob):
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    m = np.array(ob.matrix_world)
    return co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]


def _arbol(ob, vs):
    return BVHTree.FromPolygons([Vector(v) for v in vs], [tuple(p.vertices) for p in ob.data.polygons])


# Dos rumbos sin eje: un rayo paralelo a una cara del modelo (casi todas
# siguen X, Y o Z) roza en vez de cortar y la cuenta de cruces miente.
RUMBOS = (Vector((0.3713, 0.5621, 0.7391)).normalized(),
          Vector((-0.6234, 0.2817, -0.7293)).normalized())


def _cruces(arbol, o: Vector, d: Vector) -> int:
    n = 0
    for _ in range(256):
        loc, _nor, _i, _dist = arbol.ray_cast(o, d)
        if loc is None:
            return n
        n += 1
        o = loc + d * 1e-4
    return n


def _dentro(va, arbol_b, lo, hi):
    """Profundidad maxima de los vertices de A que caen dentro de B, cuantos
    pasan de TOL, y la caja de esos.

    Dentro se decide en dos pasos. El rapido -- el punto queda del lado de
    dentro de la cara mas cercana -- se equivoca junto a una arista viva: con
    el canto de las ventanas de la cubierta daba vertices del aluminio 27.6 mm
    "dentro" de una lamina de 6 a 13 de espesor (medido 09-10). Por eso solo
    filtra; lo confirma la paridad: un rayo desde el punto cruza la superficie
    un numero impar de veces si y solo si sale de dentro. Dos rumbos, y los
    dos tienen que estar de acuerdo."""
    cand = np.all((va >= lo - 1.0) & (va <= hi + 1.0), axis=1)
    peor, malos = 0.0, []
    for v in va[cand]:
        p = Vector(v)
        loc, nor, _i, dist = arbol_b.find_nearest(p)
        if loc is None or (p - loc).dot(nor) >= 0.0:
            continue
        if dist <= TOL:
            peor = max(peor, dist)
            continue                       # contacto: no hace falta confirmar
        if not all(_cruces(arbol_b, p, d) % 2 == 1 for d in RUMBOS):
            continue
        peor = max(peor, dist)
        malos.append(v)
    return peor, np.array(malos).reshape(-1, 3)


def _zonas(m: np.ndarray, hueco: float = 20.0, maximo: int = 4) -> list[dict]:
    """Las cajas de los puntos en choque, partidas donde hay un vacio de mas
    de `hueco` mm: dos choques en los dos extremos del ancho no son UNA zona
    de 568 mm (la primera corrida asi lo decia, 09-10)."""
    grupos = [m]
    while len(grupos) < maximo:
        mejor = None
        for gi, g in enumerate(grupos):
            for eje in range(3):
                s = np.sort(g[:, eje])
                if len(s) < 2:
                    continue
                k = int(np.argmax(np.diff(s)))
                if s[k + 1] - s[k] > hueco and (mejor is None or s[k + 1] - s[k] > mejor[0]):
                    mejor = (s[k + 1] - s[k], gi, eje, (s[k] + s[k + 1]) / 2)
        if mejor is None:
            break
        _, gi, eje, corte = mejor
        g = grupos.pop(gi)
        grupos += [g[g[:, eje] < corte], g[g[:, eje] >= corte]]
    return [dict(lo=g.min(0).round(1).tolist(), hi=g.max(0).round(1).tolist(), n=len(g))
            for g in grupos]


def revisar(objetos: dict) -> dict:
    """objetos: nombre -> objeto ya colocado en mundo. Revisa las dos reglas y
    devuelve un informe; ok=False si alguna falla."""
    info = {"tol_mm": TOL, "islas": {}, "choques": [], "ok": True}
    for p in PIEL:
        if p in objetos:
            ii = islas(objetos[p])
            info["islas"][p] = ii
            if len(ii) != 1:
                info["ok"] = False
    vs = {n: _mundo(o) for n, o in objetos.items()}
    cajas = {n: (v.min(0), v.max(0)) for n, v in vs.items()}
    arboles = {}
    pares = [(a, b) for i, a in enumerate(PIEL) for b in list(PIEL[i + 1:]) + list(PARTES)
             if a in objetos and b in objetos]
    for a, b in pares:
        (la, ha), (lb, hb) = cajas[a], cajas[b]
        if np.any(ha < lb - TOL) or np.any(hb < la - TOL):
            continue                       # ni se acercan
        for n in (a, b):
            if n not in arboles:
                arboles[n] = _arbol(objetos[n], vs[n])
        p1, m1 = _dentro(vs[a], arboles[b], lb, hb)
        p2, m2 = _dentro(vs[b], arboles[a], la, ha)
        peor = max(p1, p2)
        malos = np.vstack([m1, m2])
        fila = dict(a=a, b=b, profundidad_mm=round(peor, 2), vertices_dentro=len(malos),
                    zonas=_zonas(malos) if len(malos) else [])
        info["choques"].append(fila)
        if peor > TOL:
            info["ok"] = False
    return info


def imprimir_informe(info: dict) -> None:
    for p, ii in info["islas"].items():
        marca = "OK  " if len(ii) == 1 else "ROJO"
        print(f"  {marca} {p}: {len(ii)} isla(s)" +
              ("" if len(ii) == 1 else "  -> " + "; ".join(
                  f"{t['caras']} caras en x{t['lo'][0]:.0f}..{t['hi'][0]:.0f} y{t['lo'][1]:.0f}..{t['hi'][1]:.0f}"
                  for t in ii[:4])))
    for c in info["choques"]:
        marca = "OK  " if c["profundidad_mm"] <= info["tol_mm"] else "ROJO"
        zona = "; ".join(f"x{z['lo'][0]:.0f}..{z['hi'][0]:.0f} y{z['lo'][1]:.0f}..{z['hi'][1]:.0f} "
                         f"z{z['lo'][2]:.0f}..{z['hi'][2]:.0f}" for z in c["zonas"])
        print(f"  {marca} {c['a']} contra {c['b']}: entra {c['profundidad_mm']:.2f} mm"
              + (f"  en {zona}" if zona else ""))
    print("PIEL " + ("EN VERDE" if info["ok"] else "EN ROJO") + f" (tolerancia {info['tol_mm']} mm)")


def _cargar() -> dict:
    sys.path.insert(0, AQUI)
    import imprimir_piel as ip
    objetos = {}
    for p in PIEL:
        ob = ip.importar(os.path.join(PRINT, p + ".stl"))
        ob.name = p
        colocar(ob, p)
        objetos[p] = ob
    for parte in PARTES:
        ob = ip.importar(ip.exportar_scad(parte))
        ob.name = parte
        objetos[parte] = ob
    bpy.context.view_layer.update()
    return objetos


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    salida = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
    info = revisar(_cargar())
    imprimir_informe(info)
    if salida:
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(info, f)
    sys.exit(0 if info["ok"] else 1)
