"""Puerta: lo que se MANDA A FABRICAR, medido sobre los gerberes de verdad.

    python check_fab.py        # sale != 0 si el paquete de fab no cumple

## Por que existe, y por que ninguna de las otras puertas la sustituye

Todas las puertas de esta placa --las propias y el DRC de `kicad-cli`-- leen
el `.kicad_pcb`. Y a fabricar no se manda el `.kicad_pcb`: se manda un zip de
gerberes y un Excellon. Entre uno y otro hay un paso, `kicad-cli pcb export`,
que nadie comprueba.

Esta puerta mira el paquete POR DENTRO, y eso es todo lo que mira: no lee el
`.kicad_pcb` a proposito, para poder correr con un Python pelado sin `pcbnew`.
Quien cruza el paquete con la placa es `check_paquete.py`, que si la carga.
Las dos hacen falta y ninguna sustituye a la otra: en el #139 se podaron dos
vias y esta puerta siguio en verde con los gerbers de antes (#281).

Los fallos que viven EXACTAMENTE en ese hueco, y que el DRC no puede ver
porque mira otro fichero:

  * una capa que no se exporto, o que salio VACIA;
  * el contorno de placa abierto -- y entonces el fabricante decide por su
    cuenta por donde cierra;
  * el taladro y el cobre desalineados, o un taladro sin anillo anular;
  * el relleno de una zona que no llego al gerber. Esta placa tiene una zona
    (GNDREF) que `build_pcb.py` deja SIN rellenar a proposito, porque el
    filler de KiCad 10 hace segfault desde Python (#138): si alguien exporta
    sin pasar antes por `--refill-zones`, la isla de referencia sale vacia en
    el cobre y **el DRC no dice nada**, porque para el la zona esta bien.

Ese ultimo es el motivo concreto por el que esta puerta existe hoy y no en la
v2. El rodeo del #138 mete un paso manual en el pipeline, y un paso manual sin
puerta detras es un paso que algun dia no se da.

## Lo que mide, y con que criterio

    1. las seis capas y el drill existen y NO estan vacios
    2. el contorno cierra, y mide lo que el chasis le reserva
    3. todo el cobre esta dentro del contorno, con su separacion de borde
    4. cada taladro PTH cae en cobre, y cada NPTH NO -- o sea que el .drl y
       los gerberes, que son ficheros distintos, hablan del mismo sitio
    5. la barrera de 230 V, medida sobre el COBRE del gerber
    6. la zona de referencia llego al cobre (el paso manual del #138)

El anillo anular NO esta en la lista: se mide mal desde un gerber y ya lo
cubre el DRC. La razon larga esta junto a las constantes.

## El parser

RS-274X acotado a lo que KiCad 10 escribe: formato FSLAX46Y46 en mm, aperturas
C/R/O/P y macros, D01/D02/D03, y regiones G36/G37. No es un renderizador --no
hace falta-- pero si conoce el TAMANO de cada apertura, que es lo que separa
"hay cobre por aqui" de "el cobre llega hasta aqui".

Con las macros de apertura se queda con una COTA SUPERIOR: el mayor de sus
parametros como diametro. Eso hace la puerta conservadora, nunca optimista, y
se declara aqui porque un margen medido de mas se parece mucho a un margen que
no existe.

No se usa libreria externa a proposito: `gates.py` corre con un Python pelado
y ninguna otra puerta del repo pide un `pip install`.
"""
from __future__ import annotations

import math
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(DIR, "fab")
BASE = "sam17-power-v3"

# --- lo que el fabricante admite (JLCPCB, 2 capas, capability estandar) ----
# EL ANILLO ANULAR NO SE MIDE AQUI, y la primera version lo intento: dio 16
# taladros por debajo del minimo, y los 16 eran un falso positivo suyo. En el
# gerber un pad es una apertura, y tratar una oblonga de 1.20 x 1.75 como un
# circulo de su diagonal da un radio que no existe en la direccion que manda
# --- el anillo lo fija el lado MENOR. Contrastado contra el .kicad_pcb, que
# es donde el pad tiene forma: U1/U2 tienen 0.150 mm de anillo y J8 0.225,
# los dos por encima del minimo.
#
# Asi que el anillo se queda donde ya estaba cubierto: `reglas()` fija
# m_MinAnnularWidth en la placa y el DRC de kicad-cli lo comprueba, hoy con
# cero violaciones. Duplicarlo aqui con peor instrumento solo anadiria una
# segunda verdad, y peor medida.
#
# Lo que SI es propio de este par de ficheros, y ninguna otra puerta mira, es
# que el taladro y el cobre esten en el MISMO SITIO: eso se comprueba abajo.
COBRE_A_BORDE = 0.20       # mm de cobre al canto de la placa
FUGA_RED = 6.0             # mm entre cobre de red y cobre SELV (design-notes §14.2)
W, H = 200.0, 150.0        # el hueco que el chasis reserva

CAPAS = {
    "F_Cu": "gtl", "B_Cu": "gbl", "F_Mask": "gts",
    "B_Mask": "gbs", "F_Silkscreen": "gto", "Edge_Cuts": "gm1",
}


# ===========================================================================
# El parser
# ===========================================================================
class Gerber:
    """Un gerber leido: flashes, trazos y regiones, con su tamano."""

    def __init__(self, ruta: str) -> None:
        self.ruta, self.aperturas = ruta, {}
        self.flashes: list = []      # (x, y, diametro)
        self.trazos: list = []       # ((x1,y1), (x2,y2), ancho)
        self.regiones: list = []     # [[(x,y), ...]]
        self._lee(open(ruta, encoding="utf-8", errors="replace").read())

    # -- unidades: FSLAX46Y46 = 4 enteros + 6 decimales, con MOMM -> mm
    @staticmethod
    def _coord(txt: str, escala: int) -> float:
        return int(txt) / (10 ** escala)

    def _lee(self, src: str) -> None:
        escala = 6
        m = re.search(r"%FSLAX(\d)(\d)Y\d\d\*%", src)
        if m:
            escala = int(m.group(2))

        # aperturas: %ADD10C,0.6*% / R,1x2 / O,1x2 / P,1x6 / MACRO,args
        for cod, tipo, args in re.findall(
                r"%ADD(\d+)([A-Za-z_][\w.$]*),?([^*]*)\*%", src):
            nums = [float(v) for v in re.findall(r"-?[\d.]+", args)] or [0.0]
            self.aperturas[int(cod)] = (tipo, nums)
        # macros: se guarda el mayor numero que aparezca, como cota superior
        for nom, cuerpo in re.findall(r"%AM([\w.$]+)\*(.*?)%", src, re.S):
            nums = [abs(float(v)) for v in re.findall(r"-?\d+\.?\d*", cuerpo)]
            self.aperturas.setdefault("macro:" + nom, ("MACRO", nums or [0.0]))

        act, x, y, region, poly = None, 0.0, 0.0, False, []
        for lin in src.splitlines():
            lin = lin.strip()
            if lin.startswith("G04") or not lin:
                continue
            if lin.startswith("G36"):
                region, poly = True, []
                continue
            if lin.startswith("G37"):
                if len(poly) > 2:
                    self.regiones.append(poly)
                region, poly = False, []
                continue
            md = re.fullmatch(r"D(\d+)\*", lin)
            if md and int(md.group(1)) >= 10:
                act = int(md.group(1))
                continue
            mc = re.match(r"(?:G0[123]\*?)?"
                          r"(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?"
                          r"D0?([123])\*", lin)
            if not mc:
                continue
            nx = self._coord(mc.group(1), escala) if mc.group(1) else x
            ny = self._coord(mc.group(2), escala) if mc.group(2) else y
            op = mc.group(5)
            # El eje Y del gerber apunta al reves que el de la placa.
            px, py = nx, -ny
            if region:
                poly.append((px, py))
            elif op == "1":
                self.trazos.append(((x, -y), (px, py), self.diam(act)))
            elif op == "3":
                self.flashes.append((px, py, self.diam(act)))
            x, y = nx, ny

    def diam(self, cod) -> float:
        """Diametro efectivo de una apertura. Cota SUPERIOR en las macros."""
        ap = self.aperturas.get(cod)
        if not ap:
            return 0.0
        tipo, nums = ap
        if tipo == "C":
            return nums[0]
        if tipo in ("R", "O"):
            return math.hypot(nums[0], nums[1]) if len(nums) > 1 else nums[0]
        if tipo == "P":
            return nums[0]
        return max(nums) if nums else 0.0

    @property
    def vacio(self) -> bool:
        return not (self.flashes or self.trazos or self.regiones)

    def puntos(self):
        """Todo punto con cobre, con el radio que ocupa a su alrededor."""
        for x, y, d in self.flashes:
            yield x, y, d / 2
        for a, b, w in self.trazos:
            yield a[0], a[1], w / 2
            yield b[0], b[1], w / 2
        for poly in self.regiones:
            for px, py in poly:
                yield px, py, 0.0

    def caja(self):
        pts = list(self.puntos())
        if not pts:
            return None
        return (min(x - r for x, _, r in pts), min(y - r for _, y, r in pts),
                max(x + r for x, _, r in pts), max(y + r for _, y, r in pts))


def lee_drill(ruta: str) -> list:
    """Excellon de KiCad: (x, y, diametro). Unidades en mm (METRIC)."""
    src = open(ruta, encoding="utf-8", errors="replace").read()
    tools = {int(c): float(d)
             for c, d in re.findall(r"^T(\d+)C([\d.]+)", src, re.M)}
    fuera, act = [], None
    for lin in src.splitlines():
        lin = lin.strip()
        mt = re.fullmatch(r"T(\d+)", lin)
        if mt:
            act = int(mt.group(1))
            continue
        mc = re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)", lin)
        if mc and act in tools:
            fuera.append((float(mc.group(1)), -float(mc.group(2)), tools[act]))
    return fuera


def dentro(poly, x, y) -> bool:
    """Point-in-polygon por cruces. Una zona rellena TAMBIEN es cobre.

    Sin esto, un taladro dentro del relleno de GNDREF se contaba como taladro
    al aire: las regiones G36/G37 no tienen apertura, asi que no hay radio con
    el que medirlas.
    """
    n, dentro_ = len(poly), False
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            dentro_ = not dentro_
    return dentro_


def area(poly) -> float:
    """Area de un poligono por la formula del cordon del zapato."""
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1]
                   - poly[(i + 1) % n][0] * poly[i][1]
                   for i in range(n))) / 2


def main() -> int:
    fallos: list[str] = []
    capas = {}

    # --- 1. las capas existen y NO estan vacias ---------------------------
    for nom, ext in CAPAS.items():
        ruta = os.path.join(FAB, f"{BASE}-{nom}.{ext}")
        if not os.path.exists(ruta):
            fallos.append(f"falta la capa {nom} ({ext})")
            continue
        g = capas[nom] = Gerber(ruta)
        if g.vacio:
            fallos.append(f"la capa {nom} esta VACIA: se exporto sin nada")
    drl = os.path.join(FAB, f"{BASE}.drl")
    if not os.path.exists(drl):
        fallos.append("falta el fichero de taladros (.drl)")
        return informe(fallos, capas, [], None)
    taladros = lee_drill(drl)
    if not taladros:
        fallos.append("el .drl no trae un solo taladro")
    if fallos:
        return informe(fallos, capas, taladros, None)

    # --- 2. el contorno cierra y mide lo que el chasis reserva -------------
    borde = capas["Edge_Cuts"]
    bc = borde.caja()
    ancho, alto = bc[2] - bc[0], bc[3] - bc[1]
    # El contorno DIBUJADO tiene grosor (0.1 mm), asi que la caja sale 0.05
    # mas grande por lado. Mismo criterio y mismo motivo que en check_pcb.py.
    if abs(ancho - W) > 0.2 or abs(alto - H) > 0.2:
        fallos.append(f"el contorno mide {ancho:.2f} x {alto:.2f} y el chasis "
                      f"reserva {W:.0f} x {H:.0f}")
    extremos: dict = {}
    for a, b, _w in borde.trazos:
        for p in (a, b):
            extremos[(round(p[0], 3), round(p[1], 3))] = \
                extremos.get((round(p[0], 3), round(p[1], 3)), 0) + 1
    sueltos = [p for p, n in extremos.items() if n % 2]
    if sueltos:
        fallos.append(f"el contorno no cierra: {len(sueltos)} extremos sueltos "
                      f"{sueltos[:3]} -- el fabricante decidiria por su cuenta")

    # --- 3. el cobre, dentro del contorno y con aire al canto -------------
    x0, y0, x1, y1 = bc[0] + 0.05, bc[1] + 0.05, bc[2] - 0.05, bc[3] - 0.05
    for nom in ("F_Cu", "B_Cu"):
        peor, donde = 1e9, None
        for px, py, r in capas[nom].puntos():
            d = min(px - r - x0, x1 - px - r, py - r - y0, y1 - py - r)
            if d < peor:
                peor, donde = d, (px, py)
        if peor < COBRE_A_BORDE:
            fallos.append(f"{nom}: cobre a {peor:.2f} mm del canto en "
                          f"({donde[0]:.1f}, {donde[1]:.1f}), "
                          f"minimo {COBRE_A_BORDE}")

    # --- 4. el taladro y el cobre, en el mismo sitio ----------------------
    # Esta es LA pregunta que solo se puede hacer aqui: el .drl y los gerberes
    # son dos ficheros distintos, exportados por dos comandos distintos, y una
    # desalineacion entre ellos no la ve ninguna puerta que lea el .kicad_pcb.
    # Un taladro fuera de su pad sale de fabrica como un agujero al aire.
    #
    # Los NPTH de fijacion son la excepcion DECLARADA: van SIN cobre a
    # proposito (patron de la v1), porque el puente chasis-masa es uno solo y
    # va por el faston J5 -- un separador metalico no debe tocar la masa.
    npth = [t for t in taladros if t[2] >= 3.0]
    pth = [t for t in taladros if t[2] < 3.0]

    def en_cobre(capa, tx, ty) -> bool:
        for px, py, r in capa.flashes:
            if math.hypot(px - tx, py - ty) <= r / 2:
                return True
        for (ax, ay), (bx, by), w in capa.trazos:
            if math.hypot(ax - tx, ay - ty) <= w or math.hypot(bx - tx, by - ty) <= w:
                return True
        return any(dentro(p, tx, ty) for p in capa.regiones)

    al_aire = [(tx, ty, td) for tx, ty, td in pth
               if not en_cobre(capas["F_Cu"], tx, ty)]
    npth_con_cobre = [(tx, ty) for tx, ty, _td in npth
                      if en_cobre(capas["F_Cu"], tx, ty)]
    if al_aire:
        fallos.append(
            f"{len(al_aire)} taladros PTH sin cobre alrededor en F.Cu: "
            + ", ".join(f"({x:.1f},{y:.1f}) d{d}" for x, y, d in al_aire[:4])
            + " -- el .drl y el gerber no coinciden")
    if npth_con_cobre:
        fallos.append(f"{len(npth_con_cobre)} taladros NPTH con cobre "
                      f"alrededor {npth_con_cobre[:3]}: van SIN cobre a "
                      f"proposito (el puente al chasis es uno solo, por J5)")

    # --- 5. la barrera de 230 V, sobre el cobre del gerber ---------------
    # No hace falta saber de que red es cada trozo: la barrera es geometrica.
    # Todo lo que esta al sur de la ranura es red y todo lo que esta al norte
    # es SELV, asi que basta medir de un lado al otro.
    Y_SUR, Y_NORTE = 123.0, 121.0
    peor_fuga, par = 1e9, None
    for nom in ("F_Cu", "B_Cu"):
        pts = list(capas[nom].puntos())
        sur = [(x, y, r) for x, y, r in pts if y >= Y_SUR]
        norte = [(x, y, r) for x, y, r in pts if y <= Y_NORTE]
        for sx, sy, sr in sur:
            for nx, ny, nr in norte:
                d = math.hypot(sx - nx, sy - ny) - sr - nr
                if d < peor_fuga:
                    peor_fuga, par = d, (nom, (sx, sy), (nx, ny))
    if peor_fuga < FUGA_RED:
        fallos.append(f"la barrera de red mide {peor_fuga:.2f} mm en el cobre "
                      f"del gerber y hacen falta {FUGA_RED}: {par}")

    # --- 6. la zona llego al gerber --------------------------------------
    # El motivo por el que esta puerta existe hoy: el relleno de GNDREF lo
    # hace `kicad-cli --refill-zones` FUERA de build_pcb.py (#138), y un paso
    # manual sin puerta detras es un paso que algun dia no se da.
    relleno = sum(area(p) for p in capas["F_Cu"].regiones)
    if relleno < 500:
        fallos.append(f"F_Cu solo trae {relleno:.0f} mm2 de zona rellenada: la "
                      f"isla de referencia no llego al gerber. Falta el paso "
                      f"'kicad-cli pcb drc --refill-zones --save-board' antes "
                      f"de exportar (#138)")

    return informe(fallos, capas, taladros, (relleno, peor_fuga, ancho, alto))


def informe(fallos, capas, taladros, extra) -> int:
    for nom in CAPAS:
        g = capas.get(nom)
        if g:
            print(f"  {nom:<14} {len(g.flashes):>5} flashes, "
                  f"{len(g.trazos):>5} trazos, {len(g.regiones):>3} regiones")
    print(f"  {'drill':<14} {len(taladros):>5} taladros")
    if extra:
        relleno, fuga, ancho, alto = extra
        print(f"\n  contorno {ancho:.2f} x {alto:.2f} mm")
        print(f"  zona rellenada en F.Cu: {relleno:.0f} mm2")
        print(f"  barrera de red en el cobre: {fuga:.2f} mm "
              f"(minimo {FUGA_RED})")
    if fallos:
        print(f"\nFALLO: {len(fallos)} en el paquete de fabricacion")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\nOK: las seis capas y el drill son coherentes entre si, el "
          "contorno\n    cierra, la zona llego al cobre y la barrera de 230 V "
          "se mide en el gerber.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
