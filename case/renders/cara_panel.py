"""LA CARA del render (ficha 14 del acta del 09-10): los mandos sobre los
paneles, para juzgar el case con su cara puesta. Solo render: nada de esto se
fabrica desde aqui. Lo llama render_persiana.py; aparte no corre.

FILA DE ARRIBA, con el reparto que esta en papel (plan del panel §4, enmendado
el 27-08 por 2026-08-27-panel-pantalla-al-centro-design.md): la pantalla de 7"
al centro, y en los dos flancos de 181,66 mm las 4 macros (tapa de 38 en cuadro
2x2, con su corona de LED), las 16 perillas curadas (tapa de 20, paso 28 x 34)
y los 11 botones (de 12, paso 18: MATRIZ y diez fuentes). COMO SE REPARTEN
entre los dos flancos no esta escrito: aqui va el orden del paquete firmado el
23-08 (macros, perillas, fuentes) con las perillas partidas 3 y 5 alrededor de
la pantalla. Es una eleccion del render, no del panel.

FILA DE ABAJO, PROVISIONAL: son modulos KONDOR que nadie ha dibujado. Van los
tres bloques que dejo escritos el plan (30, 62 y 12 HP) con caras genericas
--perillas arriba, jacks abajo--, para ver el case con una cara puesta y no
para decidir que va ahi.

LA FILA KONDOR DEL VALLE, PROVISIONAL tambien (2026-10-11): la conexion con el
exterior, en cuatro modulos. Ver fila_valle().

El marco de cada panel sale de las gemelas de clearance_budget (el perfil y
panel_cara() de sam17_case.scad), y vestir() lo comprueba contra el STL de los
paneles: si una esquina no cae sobre un vertice, sale en ROJO antes de pintar.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

CASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if CASE not in sys.path:
    sys.path.insert(0, CASE)
import clearance_budget as cb  # noqa: E402

HP = 5.08
# la pantalla: la pieza de clase Adafruit 7" (~165 x 102, pantalla-motor §6) y
# su zona activa, ESTIMADA como 7" de diagonal a 800 x 480 (5:3). La hoja de la
# pieza no esta en el repo: es de mirar.
PANTALLA = (165.0, 102.0)
DIAG = 7 * 25.4
ACTIVA = (DIAG * 5 / math.hypot(5, 3), DIAG * 3 / math.hypot(5, 3))
FLANCO = 181.66              # (104 HP - 165) / 2: lo que deja la pantalla a cada lado
# los mandos (plan del panel §4)
MACRO, PERILLA, BOTON = 38.0, 20.0, 12.0
AIRE = 8.0                   # minimo de pinza entre tapas (Elke, plan §4)
PASO_MACRO = MACRO + AIRE    # el cuadro de 2x2 en 91
PASO_PERILLA = (PERILLA + AIRE, 34.0)
PASO_BOTON = 18.0
CORONA = MACRO / 2 + 2.0     # el anillo de LED, justo fuera de la tapa
AMBAR = (1.0, 0.42, 0.07)
# los tres bloques de la fila de abajo: HP, columnas de perillas (dos filas
# cada una) y jacks como (columnas, filas). PROVISIONAL, ver arriba.
MODULOS = ((30, 4, (6, 1)), (62, 8, (8, 1)), (12, 1, (2, 2)))
# cuanto marca cada perilla y cada corona: solo para que no salgan iguales
VALORES = (0.62, 0.35, 0.80, 0.48, 0.20, 0.71, 0.55, 0.90, 0.40, 0.66, 0.15,
           0.58, 0.83, 0.30, 0.50, 0.74, 0.44, 0.27, 0.69, 0.52)


def marcos() -> dict:
    """Por fila, la matriz que lleva (w, u, c) del panel al mundo: w a lo ancho
    (de izquierda a derecha mirando de frente), u subiendo por la cara y c
    hacia fuera, con c = 0 en la cara exterior del panel. Es panel_cara() de
    sam17_case.scad con los mismos numeros."""
    p = cb.leer_params()
    P = cb._vertices(p)
    ancho = p["ancho_total"] - 2 * p["t_anillo"] - 2 * p["t_placa"]
    filas = {"abajo": (P[1], P[2], p["inset_inf_frente"] - p["inset_er"], p["alto_panel_inf"]),
             "arriba": (P[3], P[4], p["inset_sup_valle"] - p["inset_er"], p["alto_panel_sup"])}
    # EL VALLE es horizontal: w a lo ancho, u hacia atras y c hacia arriba. El
    # panel 1U arranca inset_er antes del eje de su primer riel, y su cara
    # queda rehundido_panel bajo el plano del valle.
    c = cb._centros_rail_1u(p, P, cb._centros_rail(p, P))[0]
    out = {"valle": (Matrix(((0, 1, 0, c[0] - p["inset_er"]),
                             (0, 0, 1, P[3][1] - p["rehundido_panel"]),
                             (1, 0, 0, p["t_anillo"] + p["t_placa"]), (0, 0, 0, 1))),
                     p["alto_panel_1u"], ancho)}
    for fila, (A, B, s0, alto) in filas.items():
        L = math.hypot(B[0] - A[0], B[1] - A[1])
        dx, dy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
        nx, ny = -dy, dx                       # la normal hacia fuera, como nrm()
        ox = A[0] + dx * s0 - nx * p["rehundido_panel"]
        oy = A[1] + dy * s0 - ny * p["rehundido_panel"]
        M = Matrix(((0, dx, nx, ox), (0, dy, ny, oy),
                    (1, 0, 0, p["t_anillo"] + p["t_placa"]), (0, 0, 0, 1)))
        out[fila] = (M, alto, ancho)
    return out


def comprobar(paneles, filas: dict) -> None:
    """Las cuatro esquinas de la cara de cada fila tienen que ser vertices del
    STL de los paneles. Si la gemela se separa del .scad, los mandos flotarian
    o se hundirian sin que nadie lo viera."""
    vs = np.array([tuple(paneles.matrix_world @ v.co) for v in paneles.data.vertices])
    for fila, (M, alto, ancho) in filas.items():
        for w in (0.0, ancho):
            for u in (0.0, alto):
                q = np.array(tuple(M @ Vector((w, u, 0.0))))
                d = float(np.min(np.linalg.norm(vs - q, axis=1)))
                if d > 0.05:
                    raise SystemExit(f"ROJO: la cara de la fila de {fila} no cae sobre su panel "
                                     f"({d:.2f} mm en la esquina w={w:.1f}, u={u:.1f})")


# --- mallas: una por material, no un objeto por mando -----------------------
class Malla:
    def __init__(self, nombre: str, material: str):
        self.nombre, self.material = nombre, material
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new()

    def torno(self, M: Matrix, perfil, lados: int = 48) -> None:
        """Gira el perfil [(r, c)] alrededor del eje c, de abajo arriba; r = 0
        en las puntas lo cierra."""
        anillos = []
        for r, c in perfil:
            if r == 0:
                anillos.append([self.bm.verts.new(M @ Vector((0.0, 0.0, c)))])
            else:
                anillos.append([self.bm.verts.new(M @ Vector((r * math.cos(t), r * math.sin(t), c)))
                                for t in (2 * math.pi * k / lados for k in range(lados))])
        for a, b in zip(anillos, anillos[1:]):
            for k in range(lados):
                cara = [a[k % len(a)], a[(k + 1) % len(a)], b[(k + 1) % len(b)], b[k % len(b)]]
                cara = list(dict.fromkeys(cara))   # junto al polo, el quad es triangulo
                if len(cara) >= 3:
                    self.bm.faces.new(cara)

    def caja(self, M: Matrix, x0: float, x1: float, ly: float, c0: float, c1: float) -> None:
        bmesh.ops.create_cube(self.bm, size=1.0,
                              matrix=M @ Matrix.Translation(((x0 + x1) / 2, 0, (c0 + c1) / 2))
                              @ Matrix.Diagonal((x1 - x0, ly, c1 - c0, 1)))

    def plano(self, M: Matrix, lx: float, ly: float, c: float) -> None:
        vs = [self.bm.verts.new(M @ Vector((x * lx / 2, y * ly / 2, c)))
              for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = self.bm.faces.new(vs)
        for bucle, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            bucle[self.uv].uv = uv

    def objeto(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(self.nombre)
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(self.nombre, me)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(bpy.data.materials[self.material])
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(40))
        return ob


def _en(M: Matrix, w: float, u: float, giro: float = 0.0) -> Matrix:
    return M @ Matrix.Translation((w, u, 0)) @ Matrix.Rotation(giro, 4, "Z")


def _giro(valor: float) -> float:
    """De 7 y media (cero) a 4 y media (lleno), por arriba: 270 grados."""
    return math.radians(225 - 270 * valor)


class Cara:
    def __init__(self, fila: str):
        self.mallas = {m: Malla(f"{m}_{fila}", m) for m in
                       ("mando", "indicador", "niquel", "agujero", "led", "led_apagado", "costura")}
        self.n = 0

    def _valor(self) -> float:
        self.n += 1
        return VALORES[self.n % len(VALORES)]

    def perilla(self, M, w, u):
        r, h = PERILLA / 2, 15.0
        E = _en(M, w, u, _giro(self._valor()))
        self.mallas["mando"].torno(E, [(0, 0), (r + 1.8, 0), (r + 1.8, 1.6), (r, 1.6),
                                       (r - 0.4, h - 1.1), (r - 1.5, h), (0, h)])
        self.mallas["indicador"].caja(E, 1.0, r - 2.0, 1.0, h - 0.05, h + 0.12)

    def macro(self, M, w, u):
        r, h, v = MACRO / 2, 16.8, self._valor()
        E = _en(M, w, u, _giro(v))
        self.mallas["mando"].torno(E, [(0, 0), (r, 0), (r, h - 1.8), (r - 1.8, h), (0, h)])
        self.mallas["indicador"].caja(E, 2.0, r - 3.0, 1.4, h - 0.05, h + 0.12)
        n = 21                                       # la corona: 270 grados de LED
        for k in range(n):
            t = _giro(k / (n - 1))
            self.mallas["led" if k / (n - 1) <= v else "led_apagado"].torno(
                _en(M, w + CORONA * math.cos(t), u + CORONA * math.sin(t)),
                [(0, 0), (1.0, 0), (1.0, 0.35), (0, 0.35)], 12)

    def boton(self, M, w, u, encendido=False):
        r = BOTON / 2
        if encendido:                                # el aro del boton, encendido (A4)
            self.mallas["led"].torno(_en(M, w, u), [(0, 0), (r + 2.0, 0), (r + 2.0, 0.6), (0, 0.6)])
        self.mallas["mando"].torno(_en(M, w, u), [(0, 0), (r + 1.2, 0), (r + 1.2, 0.8), (r, 0.8),
                                                  (r, 3.2), (r - 0.8, 4.0), (0, 4.0)])

    def jack(self, M, w, u):
        self.mallas["niquel"].torno(_en(M, w, u), [(0, 0), (4.62, 0), (4.62, 2.0), (0, 2.0)], 6)
        self.mallas["niquel"].torno(_en(M, w, u), [(0, 1.9), (3.1, 1.9), (3.1, 3.6), (0, 3.6)], 32)
        self.mallas["agujero"].torno(_en(M, w, u), [(0, 3.55), (1.75, 3.55), (1.75, 3.7), (0, 3.7)], 24)

    def tornillo(self, M, w, u):
        self.mallas["mando"].torno(_en(M, w, u), [(0, 0), (2.8, 0), (2.6, 0.7), (1.6, 1.3), (0, 1.4)], 24)

    def costura(self, M, w, alto):
        self.mallas["costura"].caja(_en(M, w, alto / 2), -0.35, 0.35, alto, 0.0, 0.03)

    def objetos(self) -> list:
        return [m.objeto() for m in self.mallas.values()]


def fila_arriba(cara: Cara, M: Matrix, alto: float, ancho: float) -> None:
    w0 = (ancho - 104 * HP) / 2                       # el riel de 104 HP, centrado
    uc = alto / 2
    pant0 = ancho / 2 - PANTALLA[0] / 2
    pant1 = ancho / 2 + PANTALLA[0] / 2
    # 5 M3 por riel, 10 en total (plan §4, «la fijacion»), a inset_er del canto
    for w in np.linspace(w0 + 7.5, w0 + 104 * HP - 7.5, 5):
        for u in (3.0, alto - 3.0):
            cara.tornillo(M, w, u)
    # flanco izquierdo: el cuadro de macros y tres columnas de perillas, con el
    # mismo aire al canto que a la pantalla
    cuadro = MACRO + PASO_MACRO
    tres = PERILLA + 2 * PASO_PERILLA[0]
    borde = (FLANCO - cuadro - AIRE - tres) / 2
    for i in range(2):
        for j in (-1, 1):
            cara.macro(M, w0 + borde + MACRO / 2 + i * PASO_MACRO, uc + j * PASO_MACRO / 2)
    for i in range(3):
        for j in (-1, 1):
            cara.perilla(M, pant0 - borde - PERILLA / 2 - i * PASO_PERILLA[0],
                         uc + j * PASO_PERILLA[1] / 2)
    # flanco derecho: cinco columnas de perillas y dos de botones (6 + 5, al
    # tresbolillo). El de arriba de la primera es MATRIZ.
    cinco = PERILLA + 4 * PASO_PERILLA[0]
    dos = BOTON + PASO_BOTON
    borde = (FLANCO - cinco - AIRE - dos) / 2
    for i in range(5):
        for j in (-1, 1):
            cara.perilla(M, pant1 + borde + PERILLA / 2 + i * PASO_PERILLA[0],
                         uc + j * PASO_PERILLA[1] / 2)
    b0 = pant1 + borde + cinco + AIRE + BOTON / 2
    for k in range(6):
        cara.boton(M, b0, uc + PASO_BOTON * (k - 2.5), encendido=(k == 5))
    for k in range(5):
        cara.boton(M, b0 + PASO_BOTON, uc + PASO_BOTON * (k - 2), encendido=(k == 3))


def fila_abajo(cara: Cara, M: Matrix, alto: float, ancho: float) -> None:
    """PROVISIONAL: los tres bloques del plan (30, 62, 12 HP), caras genericas."""
    w = (ancho - 104 * HP) / 2
    for i, (hp, columnas, (jc, jf)) in enumerate(MODULOS):
        a = hp * HP
        if i:
            cara.costura(M, w, alto)
        for x in (w + 7.5, w + a - 7.5):             # 4 M3 por modulo
            for u in (3.0, alto - 3.0):
                cara.tornillo(M, x, u)
        paso = min(36.0, (a - 20) / columnas)
        for k in range(columnas):
            for u in (96.0, 62.0):
                cara.perilla(M, w + a / 2 + (k - (columnas - 1) / 2) * paso, u)
        paso = min(36.0, (a - 16) / jc)
        for k in range(jc):
            for u in ((30.0, 14.0) if jf == 2 else (22.0,)):
                cara.jack(M, w + a / 2 + (k - (jc - 1) / 2) * paso, u)
        w += a


def fila_valle(cara: Cara, M: Matrix, alto: float, ancho: float) -> None:
    """PROVISIONAL: nadie ha decidido que va en el valle; es la conexion con el
    exterior que el papel del instrumento le pone (instrumento-entero §6.2),
    firmada como punto de partida (D-S6). Cuatro modulos en 104 HP: cascos
    (14), ocho entradas y salidas con su luz (44), MIDI y reloj (30), y USB con
    un nivel (16)."""

    def perillita(w, u):
        r, h = 6.5, 11.0
        E = _en(M, w, u, _giro(cara._valor()))
        cara.mallas["mando"].torno(E, [(0, 0), (r + 1.2, 0), (r + 1.2, 1.2), (r, 1.2),
                                       (r - 0.3, h - 0.8), (r - 1.0, h), (0, h)])
        cara.mallas["indicador"].caja(E, 0.8, r - 1.5, 0.8, h - 0.05, h + 0.1)

    def led(w, u, encendido):
        cara.mallas["led" if encendido else "led_apagado"].torno(
            _en(M, w, u), [(0, 0), (1.6, 0), (1.6, 0.8), (0, 0.8)], 16)

    w = (ancho - 104 * HP) / 2
    um = alto / 2
    for i, hp in enumerate((14, 44, 30, 16)):
        a = hp * HP
        if i:
            cara.costura(M, w, alto)
        for x in (w + 7.5, w + a - 7.5):
            for u in (3.0, alto - 3.0):
                cara.tornillo(M, x, u)
        if i == 0:                       # cascos: nivel y salida
            perillita(w + a * 0.36, um)
            cara.jack(M, w + a * 0.76, um)
        elif i == 1:                     # ocho entradas y salidas, con su luz
            for k in range(8):
                ww = w + 16 + k * (a - 32) / 7
                cara.jack(M, ww, um - 6)
                led(ww, um + 12, k in (1, 2, 5))
        elif i == 2:                     # MIDI y reloj
            for k in range(5):
                cara.jack(M, w + 18 + k * (a - 36) / 4, um - 4)
            for k in range(2):
                led(w + 18 + k * (a - 36) / 4, um + 13, k == 0)
        else:                            # USB y un nivel
            cara.mallas["agujero"].caja(_en(M, w + a * 0.3, um), -4.5, 4.5, 3.2, -0.4, 0.15)
            cara.mallas["niquel"].caja(_en(M, w + a * 0.3, um), -5.5, 5.5, 4.4, -0.1, 0.05)
            perillita(w + a * 0.72, um)
        w += a


# --- la pantalla --------------------------------------------------------------
def imagen_ui(ancho: int = 800, alto: int = 480):
    """Una pantalla ENCENDIDA, no un diseno de interfaz: reticula, una onda y
    las 16 voces. Ambar, como la trasera."""
    y, x = np.mgrid[0:alto, 0:ancho].astype(np.float32)   # y = 0 abajo, como Blender
    amb = np.array(AMBAR, np.float32)
    img = np.empty((alto, ancho, 3), np.float32)
    img[:] = (0.012, 0.010, 0.009)
    img[((x % 50) < 1) | ((y % 48) < 1)] = amb * 0.06
    t = (np.arange(ancho, dtype=np.float32) - 40) / 720
    onda = 262 + 82 * np.sin(2 * np.pi * 2.5 * t) * np.exp(-1.4 * t) \
        + 12 * np.sin(2 * np.pi * 11 * t) * np.exp(-3 * t)
    dentro = (x >= 40) & (x <= 760)
    d = np.abs(y - onda[None, :])
    halo = dentro & (d < 9)
    img[halo] = np.maximum(img[halo], amb * 0.16)
    img[dentro & (d < 1.8)] = amb
    for i, h in enumerate((44, 58, 22, 70, 35, 12, 63, 49, 28, 66, 40, 18, 55, 31, 61, 46)):
        x0 = 40 + i * 45
        barra = (x >= x0) & (x < x0 + 30) & (y >= 34) & (y < 34 + h)
        img[barra] = amb * 0.45
        img[barra & (y >= 34 + h - 3)] = amb
    img[dentro & (y >= 430) & (y < 432)] = amb * 0.35
    for i in range(4):
        x0 = 40 + i * 95
        img[(x >= x0) & (x < x0 + 80) & (y >= 442) & (y < 462)] = amb * (0.85 if i == 0 else 0.14)
    return np.concatenate([img, np.ones((alto, ancho, 1), np.float32)], axis=2)


def pantalla(M: Matrix, alto: float, ancho: float) -> list:
    E = _en(M, ancho / 2, alto / 2)
    img = bpy.data.images.new("pantalla_ui", 800, 480, alpha=False)
    img.pixels.foreach_set(imagen_ui().ravel())
    try:
        img.pack()          # que viaje dentro del .blend de PIEL_BLEND
    except RuntimeError:
        pass
    m = bpy.data.materials.new("pantalla_ui")
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    for k, v in {"Base Color": (0, 0, 0, 1), "Roughness": 0.06, "Coat Weight": 1.0,
                 "Emission Strength": 1.6}.items():
        bsdf.inputs[k].default_value = v
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    piezas = []
    for nombre, mat, (lx, ly), c in (("pantalla_bisel", "bisel", (PANTALLA[0] - 5, PANTALLA[1] - 8), 0.03),
                                     ("pantalla", "pantalla_ui", ACTIVA, 0.06)):
        malla = Malla(nombre, mat)
        malla.plano(E, lx, ly, c)
        piezas.append(malla.objeto())
    return piezas


def materiales(mat) -> None:
    """mat es la de render.py: material nuevo con su Principled BSDF."""
    mat("mando", **{"Base Color": (0.03, 0.03, 0.033, 1), "Metallic": 1.0, "Roughness": 0.32})
    mat("indicador", **{"Base Color": (0.85, 0.84, 0.80, 1), "Roughness": 0.45})
    mat("niquel", **{"Base Color": (0.74, 0.74, 0.76, 1), "Metallic": 1.0, "Roughness": 0.22})
    mat("agujero", **{"Base Color": (0.004, 0.004, 0.004, 1), "Roughness": 0.9})
    # fuerza baja a proposito: con mas, el ambar se recorta a amarillo
    mat("led", **{"Base Color": (0, 0, 0, 1), "Emission Color": (*AMBAR, 1), "Emission Strength": 1.8})
    mat("led_apagado", **{"Base Color": (0.035, 0.03, 0.028, 1), "Roughness": 0.25})
    mat("costura", **{"Base Color": (0.003, 0.003, 0.003, 1), "Roughness": 0.9})
    mat("bisel", **{"Base Color": (0.004, 0.004, 0.005, 1), "Roughness": 0.08, "Coat Weight": 1.0})


def vestir(ns: dict, paneles) -> list:
    filas = marcos()
    comprobar(paneles, filas)
    materiales(ns["mat"])
    objetos = []
    for fila, rellenar in (("arriba", fila_arriba), ("abajo", fila_abajo), ("valle", fila_valle)):
        M, alto, ancho = filas[fila]
        cara = Cara(fila)
        rellenar(cara, M, alto, ancho)
        objetos += cara.objetos()
    M, alto, ancho = filas["arriba"]
    return objetos + pantalla(M, alto, ancho)
