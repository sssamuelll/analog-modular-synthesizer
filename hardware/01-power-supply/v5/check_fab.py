"""Puerta: el paquete de fabricacion de la v5 es el de la placa commiteada y es fabricable.

    python check_fab.py        # 0 verde, 1 rojo, 2 hueco (sin kicad-cli para reexportar)

Lo que se manda a JLC es fab/, no el .kicad_pcb: si alguien rerutea y no
reexporta, el pedido sale con la placa vieja. La v5 de #474 subio unos
gerbers de DOS capas de una placa sin pistas, con un README que decia
"ruteada y con DRC en cero". Esta puerta:

  1. Reexporta con las MISMAS ordenes que build_fab.py (las importa de alli)
     y compara fichero a fichero, quitando solo las lineas de fecha y version
     de herramienta. Distinto = rojo. Sin kicad-cli: hueco, no verde.
  2. Lee los gerbers y el taladro sin KiCad, como los leeria el fabricante:
       * estan las 10 capas (4 de cobre) y el .drl, y no estan vacias;
       * el contorno cierra y mide 200 x 150 mm;
       * el cobre de las 4 capas queda a >= 0.20 mm del canto;
       * cada taladro metalizado cae en cobre y los M3 (NPTH) no tienen cobre;
       * los planos de In1 estan rellenados (> 20000 mm2) y hay masa vertida
         en B.Cu (> 5000 mm2).
  3. BOM y CPL de JLC: cada codigo LCSC es el de bom.csv para esas
     referencias, y el CPL coloca exactamente lo que el BOM dice, todo con
     posicion en el fichero de posiciones.
"""
from __future__ import annotations

import csv
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(DIR, "fab")
sys.path.insert(0, os.path.join(DIR, "kicad"))
import build_fab  # noqa: E402  (las ordenes de exportacion viven alli)

BASE = build_fab.BASE
COBRE_A_BORDE = 0.20       # mm de cobre al canto de la placa
W, H = 200.0, 150.0        # dimensiones Eurocard en mm
COBRE = ("F_Cu", "In1_Cu", "In2_Cu", "B_Cu")
AREA_IN1_MIN = 20000.0     # mm2 de los tres planos de masa rellenados
AREA_BCU_MIN = 5000.0      # mm2 de masa vertida en B.Cu


class Gerber:
    """Parser Gerber RS-274X para validacion de primitivas y cotas."""

    def __init__(self, ruta: str) -> None:
        self.ruta = ruta
        self.aperturas: dict = {}
        self.flashes: list = []      # (x, y, diametro)
        self.trazos: list = []       # ((x1,y1), (x2,y2), ancho)
        self.regiones: list = []     # [[(x,y), ...]]
        self._lee(open(ruta, encoding="utf-8", errors="replace").read())

    @staticmethod
    def _coord(txt: str, escala: int) -> float:
        return int(txt) / (10 ** escala)

    def _lee(self, src: str) -> None:
        escala = 6
        m = re.search(r"%FSLAX(\d)(\d)Y\d\d\*%", src)
        if m:
            escala = int(m.group(2))

        for cod, tipo, args in re.findall(r"%ADD(\d+)([A-Za-z_][\w.$]*),?([^*]*)\*%", src):
            nums = [float(v) for v in re.findall(r"-?[\d.]+", args)] or [0.0]
            self.aperturas[int(cod)] = (tipo, nums)

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
            px, py = nx, -ny
            if region:
                poly.append((px, py))
            elif op == "1":
                self.trazos.append(((x, -y), (px, py), self.diam(act)))
            elif op == "3":
                self.flashes.append((px, py, self.diam(act)))
            x, y = nx, ny

    def diam(self, cod) -> float:
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


def lee_drill(ruta: str) -> list[tuple[float, float, float]]:
    src = open(ruta, encoding="utf-8", errors="replace").read()
    tools = {int(c): float(d) for c, d in re.findall(r"^T(\d+)C([\d.]+)", src, re.M)}
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


def dentro(poly: list[tuple[float, float]], x: float, y: float) -> bool:
    n, flag = len(poly), False
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            flag = not flag
    return flag


def area(poly: list[tuple[float, float]]) -> float:
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
                   for i in range(n))) / 2


def canon(ruta: str) -> list[str]:
    """El fichero sin las lineas que cambian entre dos exportaciones identicas
    (fecha de creacion y version de KiCad en comentarios G04 y ';')."""
    fecha = re.compile(r"\d{4}-\d{2}-\d{2}|CreationDate|GenerationSoftware|KiCad|ProjectId")
    out = []
    with open(ruta, encoding="utf-8", errors="replace") as fh:
        for cruda in fh:
            linea = cruda.rstrip("\r\n")
            if (linea.startswith("G04") or linea.startswith(";")) and fecha.search(linea):
                continue
            out.append(linea)
    return out


def reexportar() -> tuple[list[str], list[str]]:
    """(salidas que no son las de esta placa, huecos)."""
    cli = build_fab.KICAD_CLI
    if not cli or not os.path.exists(cli):
        return [], ["no hay kicad-cli para reexportar y comparar fab/ con la placa"]
    viejas = []
    tmp = tempfile.mkdtemp(prefix="sam17-v5-fab-")
    try:
        for orden in build_fab.exports(tmp):
            r = subprocess.run(orden, capture_output=True, text=True)
            if r.returncode != 0:
                return [f"kicad-cli fallo al reexportar: {r.stderr.strip()[-300:]}"], []
        for nombre in build_fab.GERBERS + (build_fab.TALADROS, build_fab.POSICIONES):
            a, b = os.path.join(FAB, nombre), os.path.join(tmp, nombre)
            if not os.path.isfile(b) or canon(a) != canon(b):
                viejas.append(nombre)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if viejas:
        return [f"{len(viejas)} salidas de fab/ NO son las de la placa commiteada: {viejas}. "
                f"Corre kicad/build_fab.py"], []
    return [], []


def jlc() -> list[str]:
    fallos = []
    bom_jlc = os.path.join(FAB, f"{BASE}-bom-jlc.csv")
    cpl_jlc = os.path.join(FAB, f"{BASE}-cpl-jlc.csv")
    pos = os.path.join(FAB, build_fab.POSICIONES)
    lcsc_de = {}
    with open(os.path.join(DIR, "bom.csv"), encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            for r in fila["refs"].split(","):
                lcsc_de[r.strip()] = fila.get("lcsc", "").strip()
    en_bom = set()
    with open(bom_jlc, encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            for r in fila["Designator"].split(","):
                en_bom.add(r)
                if lcsc_de.get(r) != fila["LCSC Part #"]:
                    fallos.append(f"BOM de JLC: {r} lleva {fila['LCSC Part #']} y bom.csv dice "
                                  f"'{lcsc_de.get(r, 'nada')}'")
    with open(cpl_jlc, encoding="utf-8", newline="") as fh:
        en_cpl = {f["Designator"] for f in csv.DictReader(fh)}
    with open(pos, encoding="utf-8", newline="") as fh:
        en_pos = {f["Ref"] for f in csv.DictReader(fh)}
    if en_cpl != en_bom:
        fallos.append(f"CPL y BOM de JLC no colocan lo mismo: sobran {sorted(en_cpl - en_bom)}, "
                      f"faltan {sorted(en_bom - en_cpl)}")
    if sin_pos := sorted(en_cpl - en_pos):
        fallos.append(f"el CPL coloca piezas sin posicion en {build_fab.POSICIONES}: {sin_pos}")
    return fallos


def main() -> int:
    fallos: list[str] = []
    capas: dict[str, Gerber] = {}
    faltan = [n for n in build_fab.GERBERS + (build_fab.TALADROS, build_fab.POSICIONES,
                                              f"{BASE}-bom-jlc.csv", f"{BASE}-cpl-jlc.csv")
              if not os.path.isfile(os.path.join(FAB, n)) or not os.path.getsize(os.path.join(FAB, n))]
    if faltan:
        print(f"FALLO: faltan o estan vacios en fab/: {faltan} -- corre kicad/build_fab.py")
        return 1
    for nombre in build_fab.GERBERS:
        clave = nombre[len(BASE) + 1:].split(".")[0]
        g = capas[clave] = Gerber(os.path.join(FAB, nombre))
        if g.vacio:
            fallos.append(f"la capa {clave} esta vacia")
    taladros = lee_drill(os.path.join(FAB, build_fab.TALADROS))
    if not taladros:
        fallos.append("el .drl no contiene ningun taladro")

    # contorno
    borde = capas["Edge_Cuts"]
    bc = borde.caja()
    ancho, alto = bc[2] - bc[0], bc[3] - bc[1]
    if abs(ancho - W) > 0.25 or abs(alto - H) > 0.25:
        fallos.append(f"el contorno mide {ancho:.2f} x {alto:.2f} mm y se esperaba {W:.0f} x {H:.0f} mm")
    extremos: dict = {}
    for a, b, _w in borde.trazos:
        for p in (a, b):
            k = (round(p[0], 3), round(p[1], 3))
            extremos[k] = extremos.get(k, 0) + 1
    if sueltos := [p for p, n in extremos.items() if n % 2]:
        fallos.append(f"el contorno tiene {len(sueltos)} extremos sin cerrar: {sueltos[:3]}")

    # cobre al canto, en las cuatro capas
    x0, y0, x1, y1 = bc[0] + 0.05, bc[1] + 0.05, bc[2] - 0.05, bc[3] - 0.05
    for nom in COBRE:
        peor, donde = 1e9, None
        for px, py, r in capas[nom].puntos():
            d = min(px - r - x0, x1 - px - r, py - r - y0, y1 - py - r)
            if d < peor:
                peor, donde = d, (px, py)
        if peor < COBRE_A_BORDE:
            fallos.append(f"{nom}: cobre a {peor:.2f} mm del borde en ({donde[0]:.1f}, {donde[1]:.1f}) "
                          f"(minimo {COBRE_A_BORDE})")

    # taladros
    npth = [t for t in taladros if t[2] >= 3.0]
    pth = [t for t in taladros if t[2] < 3.0]

    def en_cobre(capa: Gerber, tx: float, ty: float) -> bool:
        for px, py, r in capa.flashes:
            if math.hypot(px - tx, py - ty) <= r / 2:
                return True
        for (ax, ay), (bx, by), w in capa.trazos:
            if math.hypot(ax - tx, ay - ty) <= w or math.hypot(bx - tx, by - ty) <= w:
                return True
        return any(dentro(p, tx, ty) for p in capa.regiones)

    al_aire = [(tx, ty, td) for tx, ty, td in pth
               if not (en_cobre(capas["F_Cu"], tx, ty) or en_cobre(capas["B_Cu"], tx, ty))]
    if al_aire:
        fallos.append(f"{len(al_aire)} taladros PTH sin cobre: {al_aire[:4]}")
    if npth_con_cobre := [(tx, ty) for tx, ty, _td in npth if en_cobre(capas["F_Cu"], tx, ty)]:
        fallos.append(f"{len(npth_con_cobre)} taladros NPTH con cobre alrededor en F_Cu: {npth_con_cobre[:3]}")
    if len(npth) != 4:
        fallos.append(f"se esperaban los 4 taladros M3 de fijacion y hay {len(npth)} de >= 3 mm")

    # planos y vertidos
    relleno_in1 = sum(area(p) for p in capas["In1_Cu"].regiones)
    relleno_bcu = sum(area(p) for p in capas["B_Cu"].regiones)
    if relleno_in1 < AREA_IN1_MIN:
        fallos.append(f"In1_Cu solo tiene {relleno_in1:.0f} mm2 de plano relleno (minimo {AREA_IN1_MIN:.0f})")
    if relleno_bcu < AREA_BCU_MIN:
        fallos.append(f"B_Cu solo tiene {relleno_bcu:.0f} mm2 de cobre vertido (minimo {AREA_BCU_MIN:.0f})")

    fallos += jlc()
    viejas, huecos = reexportar()
    fallos += viejas

    for nom in capas:
        g = capas[nom]
        print(f"  {nom:<14} {len(g.flashes):>5} flashes, {len(g.trazos):>5} trazos, {len(g.regiones):>4} regiones")
    print(f"  {'drill':<14} {len(taladros):>5} taladros ({len(pth)} PTH, {len(npth)} NPTH M3)")
    print(f"  contorno {ancho:.2f} x {alto:.2f} mm; In1 {relleno_in1:.0f} mm2, B.Cu {relleno_bcu:.0f} mm2")
    if fallos:
        print(f"\nFALLO: {len(fallos)} discrepancias en el paquete de fabricacion")
        for f in fallos:
            print(f"  - {f}")
        return 1
    if huecos:
        for h in huecos:
            print(f"\nHUECO: {h}")
        return 2
    print("\nOK: check_fab v5 -- fab/ es la placa commiteada, 4 capas, fabricable y con BOM/CPL coherentes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
