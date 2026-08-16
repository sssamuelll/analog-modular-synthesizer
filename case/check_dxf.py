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
#
# Los sobres de bandeja_base_2d, zocalo_2d y coupon salen de la GEOMETRIA
# ESPERADA (params.scad + centros_esqueleto()), NO de medir el DXF. Medir el
# artefacto para fijar el criterio que juzga al artefacto no valida nada: el
# sobre viejo de bandeja_base_2d (290-320) se calibro midiendo la pieza
# DEFECTUOSA de 306 mm de fondo, o sea que bendecia exactamente el fallo que
# tenia que cazar (bandeja sin apoyo en su rail trasero).
#   bandeja_base_2d = ancho_util x (ce[1].x + rail/2 - (ce[0].x - rail/2))
#                   = 484 x 348  -> (460, 500, 333, 363)
#   zocalo_2d       = (ancho_util - 2*gap_sombra) x (ce[6].y - ce[0].y + 30)
#                   = 474 x 55   -> (460, 490, 40, 70)
#   coupon          = (2*8 + (n-1)*paso) x 62 = 136 x 62 -> (126, 146, 50, 75)
#
# Los otros cuatro conservan los valores que Task 6 calibro MIDIENDO. Se
# re-derivaron hoy de params para auditarlos (costado 350.00x391.49,
# entrepiso 484.00x259.13, piel inf 474.00x240.85, piel sup 474.00x160.64) y
# los cuatro caen dentro de su sobre: la calibracion vieja no escondia ningun
# desvio. Aun asi el criterio correcto es el derivado — quien toque una de
# esas piezas recalcula su sobre de params, no lo vuelve a medir del DXF.
SOBRES = {
    "costado_2d":          (330, 370, 370, 410),
    "bandeja_base_2d":     (460, 500, 333, 363),
    "bandeja_entrepiso_2d": (460, 500, 235, 265),
    "zocalo_2d":           (460, 490, 40, 70),
    "piel_inferior_2d":    (460, 490, 225, 255),
    "piel_superior_2d":    (460, 490, 145, 175),
    "coupon":              (126, 146, 50, 75),
}


def revisar(nombre: str, sobre) -> list[str]:
    f: list[str] = []
    ruta = PLANS / f"{nombre}.dxf"
    doc = ezdxf.readfile(ruta)
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
    # ezdxf SINTETIZA un header completo al leer: doc.header reporta
    # $INSUNITS=6 aunque el archivo no lo traiga (verificado: la cadena
    # aparece 0 veces). OpenSCAD 2021.01 emite R12 SIN seccion HEADER, asi
    # que el DXF no declara unidades y la unica fuente honesta es el texto.
    # Ausente = correcto (numeros crudos en mm; se le dice al servicio).
    if "$INSUNITS" in ruta.read_text(encoding="utf-8", errors="replace"):
        ins = doc.header.get("$INSUNITS", 0)
        if ins not in (0, 4):
            f.append(f"{nombre}: $INSUNITS={ins} (ni ausente ni mm)")
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


