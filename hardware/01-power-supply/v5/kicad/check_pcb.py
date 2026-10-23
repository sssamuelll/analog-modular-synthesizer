"""Puerta: la placa COMMITEADA es la del esquematico, esta ruteada y su DRC esta en cero.

    python check_pcb.py           # 0 verde, 1 rojo. Python pelado: corre en el CI
    python check_pcb.py --mutar   # los canarios: cada rotura tiene que salir roja

POR QUE EN PYTHON PELADO. gates.py da por HUECO cualquier guion que necesite
el Python de KiCad cuando no lo hay, y en el CI no lo hay. El check_pcb de
#474 lo necesitaba: en el CI nunca corrio, y en local solo comparaba la
colocacion con la tabla del propio script. Asi entro una placa de 161
huellas sin una sola pista con todas las puertas en verde. Esta lee el
.kicad_pcb como lo que es, un fichero de texto, y no le hace falta KiCad.

QUE MIRA:

  1. Paridad con el netlist: cada componente esta, con su huella de
     biblioteca, y cada pad lleva la red que el netlist le da. Nada de mas.
  2. Stackup y contorno: 4 capas de cobre, 200 x 150 mm.
  3. Que esta ruteada: hay pistas y vias, y los tres planos de In1 estan
     rellenados (sin relleno, la mitad de las masas no llega a ningun sitio).
  4. Que el DRC esta en cero PARA ESTA PLACA: sam17-power-v5-drc.json es el
     informe de kicad-cli (todas las severidades y paridad con el
     esquematico) que escribe build_pcb.py, con el sha256 del .kicad_pcb que
     comprobo. Si la placa cambio despues, rojo: hay que volver a pasarlo.
     check_drc.py lo vuelve a correr en vivo donde hay KiCad.
  5. Que los caminos de ~3 A (entrada de 24 V y +5 V digital) van por cobre
     de >= ANCHO_MIN de pad a pad, sin pasar por una pista ruteada de 0.5 mm.
  6. Que las masas no se tocan: >= 2 mm entre GNDD y las otras dos en todas
     las capas, >= 1 mm entre GND24 y GNDA (que solo une NT1).
  7. Que U1 y U2 tienen sus vias termicas.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BASE = "sam17-power-v5"
PCB = os.path.join(DIR, f"{BASE}.kicad_pcb")
NET = os.path.join(DIR, f"{BASE}.net")
DRC = os.path.join(DIR, f"{BASE}-drc.json")

W, H = 200.0, 150.0
CAPAS_COBRE = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
MONTAJE = {"H1", "H2", "H3", "H4"}           # taladros M3: solo existen en la placa
# 1.4 mm en 1 oz exterior: ~3 A con 10 C de subida (IPC-2221, k = 0.048).
# Las pistas que rutea Freerouting son de 0.25/0.4/0.5 mm: no cuentan.
ANCHO_MIN = 1.4
SOLAPE_MIN = 0.1                              # mm de cobre comun para contar como unido
CAMINOS = [
    ("+24V_RAW", "J1.1", ["Q2.1", "Q2.2", "Q2.3", "D1.1"]),
    ("+24V_PROT", "Q2.5", ["U16.1", "U16.2", "U16.3"]),
    ("+24V_SW", "U16.18", ["U16.19", "U16.20", "PS1.1", "PS4.1", "PS5.1", "PS3.1", "PS3.2",
                           "PS2.3", "C14.1"]),
    ("+5V_RAW_DIG", "PS2.4", ["F5.1", "C29.1"]),
    ("+5V_DIG", "F5.2", ["J9.1", "SCR4.2"]),
]
HUECOS = [("GNDD", "GNDA", 2.0), ("GNDD", "GND24", 2.0), ("GND24", "GNDA", 1.0)]
VIAS_TERMICAS_MIN = 20

_TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def leer_sexpr(ruta: str) -> list:
    pila: list[list] = [[]]
    with open(ruta, encoding="utf-8") as fh:
        for m in _TOK.finditer(fh.read()):
            t = m.group(0)
            if t == "(":
                pila.append([])
            elif t == ")":
                x = pila.pop()
                pila[-1].append(x)
            elif t[0] == '"':
                pila[-1].append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
            else:
                pila[-1].append(t)
    return pila[0][0]


def hijos(nodo: list, clave: str) -> list[list]:
    return [c for c in nodo if isinstance(c, list) and c and c[0] == clave]


def hijo(nodo: list, clave: str) -> list | None:
    r = hijos(nodo, clave)
    return r[0] if r else None


# ------------------------------------------------------------- geometria
def _dist_punto_seg(p, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _cruzan(a, b, c, d) -> bool:
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return (o(a, b, c) * o(a, b, d) < 0) and (o(c, d, a) * o(c, d, b) < 0)


def dist_seg_seg(a, b, c, d) -> float:
    if _cruzan(a, b, c, d):
        return 0.0
    return min(_dist_punto_seg(a, c, d), _dist_punto_seg(b, c, d),
               _dist_punto_seg(c, a, b), _dist_punto_seg(d, a, b))


class Pad:
    def __init__(self, ref, num, x, y, ang, w, h, red, capas):
        self.ref, self.num, self.x, self.y = ref, num, x, y
        self.ang, self.w, self.h, self.red, self.capas = ang, w, h, red, capas

    def local(self, p):
        a = math.radians(self.ang)
        dx, dy = p[0] - self.x, p[1] - self.y
        return (dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))

    def dist_seg(self, a, b) -> float:
        """Distancia del rectangulo del pad a un segmento (0 si se cortan)."""
        la, lb = self.local(a), self.local(b)
        hw, hh = self.w / 2, self.h / 2
        esquinas = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        if any(abs(p[0]) <= hw and abs(p[1]) <= hh for p in (la, lb)):
            return 0.0
        lados = list(zip(esquinas, esquinas[1:] + esquinas[:1]))
        return min(dist_seg_seg(la, lb, c, d) for c, d in lados)


def dist_poligonos(p, q) -> float:
    """Distancia entre dos poligonos (0 si se solapan)."""
    def dentro(pt, poly):
        x, y = pt
        f = False
        for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                f = not f
        return f
    if dentro(p[0], q) or dentro(q[0], p):
        return 0.0
    ep = list(zip(p, p[1:] + p[:1]))
    eq = list(zip(q, q[1:] + q[:1]))
    return min(dist_seg_seg(a, b, c, d) for a, b in ep for c, d in eq)


# ------------------------------------------------------------------ placa
def leer_placa(arbol: list) -> dict:
    pads, huellas = [], {}
    for fp in hijos(arbol, "footprint"):
        ref = next(p[2] for p in hijos(fp, "property") if p[1] == "Reference")
        at = hijo(fp, "at")
        X, Y = float(at[1]), float(at[2])
        A = float(at[3]) if len(at) > 3 else 0.0
        huellas[ref] = fp[1]
        a = math.radians(A)
        for pd in hijos(fp, "pad"):
            if not pd[1]:
                continue                          # aperturas de pasta sin numero
            pat = hijo(pd, "at")
            px, py = float(pat[1]), float(pat[2])
            ang = float(pat[3]) if len(pat) > 3 else A
            size = hijo(pd, "size")
            red = hijo(pd, "net")
            capas = hijo(pd, "layers")[1:]
            pads.append(Pad(ref, pd[1], X + px * math.cos(a) + py * math.sin(a),
                            Y - px * math.sin(a) + py * math.cos(a), ang,
                            float(size[1]), float(size[2]), red[1] if red else "", capas))
    segs = []
    for s in hijos(arbol, "segment"):
        st, en = hijo(s, "start"), hijo(s, "end")
        segs.append({"a": (float(st[1]), float(st[2])), "b": (float(en[1]), float(en[2])),
                     "w": float(hijo(s, "width")[1]), "capa": hijo(s, "layer")[1],
                     "red": hijo(s, "net")[1] if hijo(s, "net") else ""})
    vias = []
    for v in hijos(arbol, "via"):
        at = hijo(v, "at")
        vias.append({"p": (float(at[1]), float(at[2])), "red": hijo(v, "net")[1] if hijo(v, "net") else ""})
    zonas = []
    for z in hijos(arbol, "zone"):
        capa = hijo(z, "layer")
        poly = hijo(z, "polygon")
        pts = [(float(p[1]), float(p[2])) for p in hijos(hijo(poly, "pts"), "xy")] if poly else []
        zonas.append({"red": hijo(z, "net")[1] if hijo(z, "net") else "",
                      "capa": capa[1] if capa else "", "pts": pts,
                      "rellena": bool(hijos(z, "filled_polygon"))})
    capas = [c[1] for c in hijo(arbol, "layers")[1:] if isinstance(c, list) and c[1].endswith(".Cu")]
    bordes = []
    for g in hijos(arbol, "gr_line") + hijos(arbol, "gr_rect"):
        if hijo(g, "layer") and hijo(g, "layer")[1] == "Edge.Cuts":
            st, en = hijo(g, "start"), hijo(g, "end")
            bordes += [(float(st[1]), float(st[2])), (float(en[1]), float(en[2]))]
    return {"pads": pads, "huellas": huellas, "segs": segs, "vias": vias, "zonas": zonas,
            "capas": capas, "bordes": bordes}


def leer_netlist() -> tuple[dict, dict]:
    arbol = leer_sexpr(NET)
    comps = {}
    for c in hijos(hijo(arbol, "components"), "comp"):
        comps[hijo(c, "ref")[1]] = hijo(c, "footprint")[1]
    redes = {}
    for n in hijos(hijo(arbol, "nets"), "net"):
        nombre = hijo(n, "name")[1].lstrip("/")
        for nodo in hijos(n, "node"):
            redes[(hijo(nodo, "ref")[1], hijo(nodo, "pin")[1])] = nombre
    return comps, redes


# ---------------------------------------------------------------- puertas
def paridad(placa: dict, comps: dict, redes: dict) -> list[str]:
    fallos = []
    en_placa = set(placa["huellas"]) - MONTAJE
    if faltan := sorted(set(comps) - en_placa):
        fallos.append(f"paridad: faltan en la placa {faltan}")
    if sobran := sorted(en_placa - set(comps)):
        fallos.append(f"paridad: la placa trae piezas que el netlist no tiene {sobran}")
    for ref in sorted(set(comps) & en_placa):
        if placa["huellas"][ref] != comps[ref]:
            fallos.append(f"paridad: {ref} lleva {placa['huellas'][ref]} y el netlist dice {comps[ref]}")
    vistos = set()
    for p in placa["pads"]:
        if p.ref in MONTAJE:
            continue
        esperado = redes.get((p.ref, p.num), "")
        vistos.add((p.ref, p.num))
        if p.red != esperado:
            fallos.append(f"paridad: {p.ref}.{p.num} en la red '{p.red}' y el netlist dice '{esperado}'")
    if sin_pad := sorted(k for k in redes if k not in vistos):
        fallos.append(f"paridad: pines del netlist sin pad en la placa {sin_pad[:6]}")
    return fallos


def estructura(placa: dict) -> list[str]:
    fallos = []
    if placa["capas"] != CAPAS_COBRE:
        fallos.append(f"stackup: capas de cobre {placa['capas']}, se esperaban {CAPAS_COBRE}")
    if placa["bordes"]:
        xs = [p[0] for p in placa["bordes"]]
        ys = [p[1] for p in placa["bordes"]]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if abs(w - W) > 0.01 or abs(h - H) > 0.01:
            fallos.append(f"contorno de {w:.2f} x {h:.2f} mm, se esperaba {W:.0f} x {H:.0f}")
    else:
        fallos.append("la placa no tiene contorno en Edge.Cuts")
    if not placa["segs"] or not placa["vias"]:
        fallos.append(f"sin rutear: {len(placa['segs'])} pistas y {len(placa['vias'])} vias")
    planos = {z["red"]: z for z in placa["zonas"] if z["capa"] == "In1.Cu"}
    for red in ("GND24", "GNDA", "GNDD"):
        if red not in planos:
            fallos.append(f"falta el plano {red} en In1.Cu")
        elif not planos[red]["rellena"]:
            fallos.append(f"el plano {red} de In1.Cu no esta rellenado: guarda la placa con las zonas rellenas")
    return fallos


def evidencia_drc(sha: str | None = None) -> list[str]:
    if not os.path.exists(DRC):
        return [f"falta {os.path.basename(DRC)}: lo escribe build_pcb.py al pasar el DRC"]
    with open(DRC, encoding="utf-8") as fh:
        informe = json.load(fh)
    if sha is None:
        with open(PCB, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
    fallos = []
    if informe.get("pcb_sha256") != sha:
        fallos.append(f"{os.path.basename(DRC)} es de OTRA placa (sha256 distinto): la placa cambio "
                      f"despues del DRC; vuelve a correr build_pcb.py")
    for clave, que in (("violations", "infracciones"), ("unconnected_items", "conexiones sin rutear"),
                       ("schematic_parity", "diferencias de paridad")):
        if clave not in informe:
            fallos.append(f"el informe de DRC no trae '{clave}'")
        elif informe[clave]:
            tipos = sorted({v.get("type", "?") for v in informe[clave]})
            fallos.append(f"DRC: {len(informe[clave])} {que} {tipos[:5]}")
    return fallos


def caminos(placa: dict) -> list[str]:
    """Cada destino de CAMINOS se alcanza desde el origen por cobre >= ANCHO_MIN."""
    fallos = []
    pads = {f"{p.ref}.{p.num}": p for p in placa["pads"]}
    for red, origen, destinos in CAMINOS:
        anchas = [s for s in placa["segs"] if s["red"] == red and s["w"] >= ANCHO_MIN - 1e-6]
        nodos = [("pad", pads[n]) for n in [origen] + destinos] + [("seg", s) for s in anchas]
        visto = {0}
        cola = [0]
        while cola:
            i = cola.pop()
            ti, a = nodos[i]
            for j, (tj, b) in enumerate(nodos):
                if j in visto:
                    continue
                # SOLAPE de verdad, no tangencia: dos tiras que solo se tocan por
                # el canto no estan unidas para KiCad (ronda 1: el tronco de
                # U16 no llegaba al bus por 0 mm y esta puerta lo daba por bueno).
                if ti == "seg" and tj == "seg":
                    toca = (a["capa"] == b["capa"] and dist_seg_seg(a["a"], a["b"], b["a"], b["b"])
                            <= (a["w"] + b["w"]) / 2 - SOLAPE_MIN)
                elif ti == "seg" or tj == "seg":
                    s, p = (a, b) if ti == "seg" else (b, a)
                    toca = s["capa"] in p.capas or "*.Cu" in p.capas
                    toca = toca and p.dist_seg(s["a"], s["b"]) <= s["w"] / 2 - SOLAPE_MIN
                else:
                    toca = False
                if toca:
                    visto.add(j)
                    cola.append(j)
        for k, n in enumerate(destinos, start=1):
            if k not in visto:
                fallos.append(f"{red}: {n} no se alcanza desde {origen} por cobre de >= {ANCHO_MIN} mm")
    return fallos


def huecos_de_masa(placa: dict) -> list[str]:
    fallos = []
    por_capa: dict[str, dict] = {}
    for z in placa["zonas"]:
        if z["red"] in ("GND24", "GNDA", "GNDD") and z["pts"]:
            por_capa.setdefault(z["capa"], {}).setdefault(z["red"], []).append(z["pts"])
    for capa, zs in sorted(por_capa.items()):
        for r1, r2, minimo in HUECOS:
            for p in zs.get(r1, []):
                for q in zs.get(r2, []):
                    d = dist_poligonos(p, q)
                    if d < minimo - 1e-6:
                        fallos.append(f"{capa}: {r1} y {r2} a {d:.2f} mm (minimo {minimo})")
    return fallos


def vias_termicas(placa: dict) -> list[str]:
    fallos = []
    for ref, red in (("U1", "GNDA"), ("U2", "-15V5_FILT")):
        aleta = max((p for p in placa["pads"] if p.ref == ref), key=lambda p: p.w * p.h)
        n = sum(1 for v in placa["vias"] if v["red"] == red
                and abs(v["p"][0] - aleta.x) <= aleta.w / 2 + 8 and abs(v["p"][1] - aleta.y) <= aleta.h / 2 + 8)
        if aleta.red != red:
            fallos.append(f"la aleta de {ref} esta en '{aleta.red}' y deberia ser {red}")
        if n < VIAS_TERMICAS_MIN:
            fallos.append(f"{ref}: {n} vias termicas de {red} junto a la aleta (minimo {VIAS_TERMICAS_MIN})")
    return fallos


def revisar(placa: dict, comps: dict, redes: dict, sha: str | None = None) -> list[str]:
    return (paridad(placa, comps, redes) + estructura(placa) + evidencia_drc(sha)
            + caminos(placa) + huecos_de_masa(placa) + vias_termicas(placa))


def mutar() -> int:
    """Prueba que la puerta DISTINGUE: cada mutacion tiene que ponerla roja.

    Verde sobre la placa buena no demuestra nada -- podria no estar mirando.
    Se rompe una copia EN MEMORIA de lo leido (el fichero no se toca), cada
    vez de una forma que de verdad puede pasar, y se exige el fallo que toca.
    """
    import copy
    base = leer_placa(leer_sexpr(PCB))
    comps, redes = leer_netlist()
    limpio = revisar(base, comps, redes)
    if limpio:
        print("FALLO: la placa de partida no esta en verde; los canarios no prueban nada")
        return 1

    def sin_bus(pl):
        pl["segs"] = [s for s in pl["segs"] if not (s["red"] == "+24V_SW" and s["w"] >= ANCHO_MIN
                                                    and abs(s["a"][1] - s["b"][1]) > 50)]

    def red_cambiada(pl):
        p = next(p for p in pl["pads"] if p.ref == "U16" and p.num == "7")
        p.red = "OVP_U16"

    def gndd_pegada(pl):
        for z in pl["zonas"]:
            if z["red"] == "GNDD":
                z["pts"] = [(x, y - 1.5) for x, y in z["pts"]]

    def sin_vias(pl):
        pl["vias"] = []

    def termicas_en_gnda(pl):
        # lo que paso de verdad: KiCad propago a las vias termicas de U2 la red
        # del relleno viejo de GNDA en In1 al guardar (build_pcb.tras_el_ruteo)
        for v in pl["vias"]:
            if v["red"] == "-15V5_FILT":
                v["red"] = "GNDA"

    canarios = [("se corta el bus de +24V_SW", sin_bus, "+24V_SW"),
                ("U16.7 cambia de red", red_cambiada, "paridad"),
                ("GNDD a 0.5 mm de GNDA", gndd_pegada, "GNDD y GNDA"),
                ("placa sin vias", sin_vias, "sin rutear"),
                ("las vias termicas de U2 pasan a GNDA", termicas_en_gnda, "U2:"),
                ("placa editada despues del DRC", None, "OTRA placa")]
    malos = 0
    for nombre, f, espera in canarios:
        pl = copy.deepcopy(base)
        if f:
            f(pl)
        fallos = revisar(pl, comps, redes, sha="0" * 64 if f is None else None)
        cazado = any(espera in x for x in fallos)
        print(f"  {'OK   ' if cazado else 'FALLO'} {nombre}: {len(fallos)} fallos")
        malos += not cazado
    print(f"OK: los {len(canarios)} canarios ponen la puerta en rojo" if not malos
          else f"FALLO: {malos} canarios pasan")
    return 1 if malos else 0


def main() -> int:
    for ruta in (PCB, NET):
        if not os.path.exists(ruta):
            print(f"FALLO: falta {os.path.basename(ruta)}")
            return 1
    if "--mutar" in sys.argv:
        return mutar()
    placa = leer_placa(leer_sexpr(PCB))
    comps, redes = leer_netlist()
    fallos = revisar(placa, comps, redes)
    n_pistas = sum(1 for s in placa["segs"])
    print(f"{len(placa['huellas'])} huellas, {len(placa['pads'])} pads, {n_pistas} pistas, "
          f"{len(placa['vias'])} vias, {len(placa['zonas'])} zonas")
    if fallos:
        print(f"\nFALLO: {len(fallos)}")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("OK: check_pcb v5 -- paridad con el netlist, DRC en cero para esta placa, "
          "caminos de 3 A en cobre ancho y masas separadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
