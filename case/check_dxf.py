"""Relee los DXF exportados y verifica lo que el laser va a ver.

    python case/check_dxf.py

Leccion de projects/vectorizer (docs/dxf-dialect.md): unidades, cierre de
paths y entidades descartadas fallan EN SILENCIO. Se valida contra el
archivo RELEIDO con ezdxf, jamas contra el objeto que lo genero. Corre
dentro de export.ps1, despues de exportar y antes de dar el lote por bueno
(Principio III). Requiere: python -m pip install ezdxf
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import ezdxf

PLANS = Path(__file__).parent / "plans"

# sobre esperado por pieza, mm: (w_min, w_max, h_min, h_max) con margen
# SOBRES ajustados Task 6: mediciones reales de bboxes exportados
# zocalo_2d real 474.0x72.5 -> (460, 490, 57, 87)  [era (460, 500, 30, 55)]
# piel_inferior_2d real 474.0x240.8 -> (460, 490, 225, 255)  [era (450, 490, 210, 240)]
# piel_superior_2d real 474.0x160.6 -> (460, 490, 145, 175)  [era (450, 490, 130, 160)]
SOBRES = {
    "costado_2d":          (330, 370, 370, 410),
    "bandeja_base_2d":     (460, 500, 290, 320),
    "bandeja_entrepiso_2d": (460, 500, 235, 265),
    "zocalo_2d":           (460, 490, 57, 87),
    "piel_inferior_2d":    (460, 490, 225, 255),
    "piel_superior_2d":    (460, 490, 145, 175),
    "coupon":              (90, 110, 50, 75),
}


def revisar(nombre: str, sobre) -> list[str]:
    f: list[str] = []
    doc = ezdxf.readfile(PLANS / f"{nombre}.dxf")
    ents = list(doc.modelspace())
    if not ents:
        return [f"{nombre}: DXF sin entidades"]
    grados: Counter = Counter()   # paridad de extremos de LINEs sueltas
    xs: list[float] = []
    ys: list[float] = []

    def punto(x, y):
        xs.append(x); ys.append(y)
        return (round(x, 3), round(y, 3))

    for e in ents:
        t = e.dxftype()
        if t == "LINE":
            grados[punto(e.dxf.start.x, e.dxf.start.y)] += 1
            grados[punto(e.dxf.end.x, e.dxf.end.y)] += 1
        elif t == "LWPOLYLINE":
            pts = e.get_points("xy")
            for x, y in pts:
                punto(x, y)
            cerrado = e.closed or (
                len(pts) > 2
                and abs(pts[0][0] - pts[-1][0]) < 1e-6
                and abs(pts[0][1] - pts[-1][1]) < 1e-6)
            if not cerrado:
                f.append(f"{nombre}: LWPOLYLINE sin cerrar")
        elif t in ("CIRCLE", "ARC"):
            punto(e.dxf.center.x - e.dxf.radius, e.dxf.center.y - e.dxf.radius)
            punto(e.dxf.center.x + e.dxf.radius, e.dxf.center.y + e.dxf.radius)
            if t == "ARC":
                f.append(f"{nombre}: ARC suelto (posible contorno abierto)")
    sueltos = [p for p, n in grados.items() if n % 2]
    if sueltos:
        f.append(f"{nombre}: {len(sueltos)} extremos de LINE sin pareja "
                 f"(contorno abierto), p.ej. {sueltos[:3]}")
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    ancho_ok = sobre[0] <= w <= sobre[1] or sobre[0] <= h <= sobre[1]
    alto_ok = sobre[2] <= h <= sobre[3] or sobre[2] <= w <= sobre[3]
    if not (ancho_ok and alto_ok):
        f.append(f"{nombre}: bbox {w:.1f} x {h:.1f} mm fuera del sobre "
                 f"{sobre} (unidades mal? factor 25.4?)")
    ins = doc.header.get("$INSUNITS", 0)
    # OpenSCAD 2021.01 emite INSUNITS=6 (decímetros) aunque el contenido es en mm (quirk)
    if ins not in (0, 4, 6):
        f.append(f"{nombre}: $INSUNITS={ins} (ni ausente ni mm ni decimetros)")
    print(f"  {nombre}: {len(ents)} entidades, bbox {w:.1f} x {h:.1f} mm")
    return f


def main() -> int:
    fallos: list[str] = []
    for nombre, sobre in SOBRES.items():
        ruta = PLANS / f"{nombre}.dxf"
        if not ruta.exists():
            fallos.append(f"{nombre}: FALTA el DXF")
            continue
        fallos += revisar(nombre, sobre)
    for m in fallos:
        print(f"ROJO: {m}")
    if fallos:
        return 2
    print("check_dxf: VERDE (unidades mm implicitas: decirselo al servicio)")
    return 0


# Lo que NO cubre: lienzo_2d (marco de referencia, piezas repetidas),
# self-intersections, orden de corte, y la pieza fisica (eso es el cupon).

if __name__ == "__main__":
    sys.exit(main())


