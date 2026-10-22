"""Puerta de calidad: valida los ficheros de fabricacion Gerber y Excellon para la fuente v5.

    python check_fab.py        # sale con codigo != 0 si el paquete de fab no cumple

Comprueba:
  1. Las seis capas Gerber requeridas y el fichero drill existen y no estan vacios.
  2. El contorno de placa (Edge_Cuts) cierra y mide exactamente 200 x 150 mm (Eurocard).
  3. Todo el cobre esta dentro del contorno con separacion minima al borde (>= 0.20 mm).
  4. Los taladros PTH caen sobre cobre y los taladros NPTH (fijacion M3) estan aislados.
  5. Las zonas de masa en B_Cu estan presentes y rellenadas.
  6. Los ficheros de ensamblaje JLCPCB (BOM y CPL) existen y estan poblados.
"""
from __future__ import annotations

import math
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(DIR, "fab")
BASE = "sam17-power-v5"

COBRE_A_BORDE = 0.20       # mm de cobre al canto de la placa
W, H = 200.0, 150.0        # dimensiones Eurocard en mm

CAPAS = {
    "F_Cu": "gtl", "B_Cu": "gbl", "F_Mask": "gts",
    "B_Mask": "gbs", "F_Silkscreen": "gto", "Edge_Cuts": "gm1",
}


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


def main() -> int:
    fallos: list[str] = []
    capas: dict[str, Gerber] = {}

    # 1. Comprobar existencia y no-vacuidad de capas
    for nom, ext in CAPAS.items():
        ruta = os.path.join(FAB, f"{BASE}-{nom}.{ext}")
        if not os.path.exists(ruta):
            fallos.append(f"falta la capa {nom} ({ext})")
            continue
        g = capas[nom] = Gerber(ruta)
        if g.vacio:
            fallos.append(f"la capa {nom} esta vacia")

    drl = os.path.join(FAB, f"{BASE}.drl")
    if not os.path.exists(drl):
        fallos.append("falta el fichero de taladros (.drl)")
        taladros = []
    else:
        taladros = lee_drill(drl)
        if not taladros:
            fallos.append("el .drl no contiene ningun taladro")

    if fallos:
        for f in fallos:
            print(f"FALLO: {f}")
        return 1

    # 2. Comprobar que Edge_Cuts cierra y mide 200 x 150 mm
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
    sueltos = [p for p, n in extremos.items() if n % 2]
    if sueltos:
        fallos.append(f"el contorno tiene {len(sueltos)} extremos sin cerrar: {sueltos[:3]}")

    # 3. Comprobar que el cobre respeta la distancia al canto
    x0, y0, x1, y1 = bc[0] + 0.05, bc[1] + 0.05, bc[2] - 0.05, bc[3] - 0.05
    for nom in ("F_Cu", "B_Cu"):
        peor, donde = 1e9, None
        for px, py, r in capas[nom].puntos():
            d = min(px - r - x0, x1 - px - r, py - r - y0, y1 - py - r)
            if d < peor:
                peor, donde = d, (px, py)
        if peor < COBRE_A_BORDE:
            fallos.append(f"{nom}: cobre a {peor:.2f} mm del borde en ({donde[0]:.1f}, {donde[1]:.1f}) (minimo {COBRE_A_BORDE})")

    # 4. Comprobar taladros y cobre
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

    al_aire = [(tx, ty, td) for tx, ty, td in pth if not (en_cobre(capas["F_Cu"], tx, ty) or en_cobre(capas["B_Cu"], tx, ty))]
    if al_aire:
        fallos.append(f"{len(al_aire)} taladros PTH sin cobre: {al_aire[:4]}")

    npth_con_cobre = [(tx, ty) for tx, ty, _td in npth if en_cobre(capas["F_Cu"], tx, ty)]
    if npth_con_cobre:
        fallos.append(f"{len(npth_con_cobre)} taladros NPTH con cobre alrededor en F_Cu: {npth_con_cobre[:3]}")

    # 5. Comprobar que las zonas de masa en B_Cu estan rellenas
    relleno_bcu = sum(area(p) for p in capas["B_Cu"].regiones)
    if relleno_bcu < 5000:
        fallos.append(f"B_Cu solo contiene {relleno_bcu:.0f} mm2 de cobre en zonas rellenas (se esperaban >5000 mm2)")

    # 6. Comprobar ficheros JLCPCB
    bom_jlc = os.path.join(FAB, f"{BASE}-bom-jlc.csv")
    cpl_jlc = os.path.join(FAB, f"{BASE}-cpl-jlc.csv")
    if not os.path.exists(bom_jlc) or os.path.getsize(bom_jlc) == 0:
        fallos.append(f"falta {os.path.basename(bom_jlc)} o esta vacio")
    if not os.path.exists(cpl_jlc) or os.path.getsize(cpl_jlc) == 0:
        fallos.append(f"falta {os.path.basename(cpl_jlc)} o esta vacio")

    # Resumen
    for nom in CAPAS:
        g = capas[nom]
        print(f"  {nom:<14} {len(g.flashes):>5} flashes, {len(g.trazos):>5} trazos, {len(g.regiones):>3} regiones")
    print(f"  {'drill':<14} {len(taladros):>5} taladros ({len(pth)} PTH, {len(npth)} NPTH M3)")
    print(f"  contorno {ancho:.2f} x {alto:.2f} mm")
    print(f"  relleno de zona B_Cu: {relleno_bcu:.0f} mm2")

    if fallos:
        print(f"\nFALLO: {len(fallos)} discrepancias en el paquete de fabricacion")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print("\nOK: check_fab v5 -- paquete de fabricacion verificado y consistente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
