"""Genera panel-template-{inf,sup}.kicad_pcb: panel de aluminio del SAM17.

    "C:/Program Files/KiCad/10.0/bin/python.exe" case/panels/build_template.py       [--ancho 100] [--piso inf|sup]

Corre desde la raiz del repo o desde case/panels: el import de
clearance_budget y la escritura del .kicad_pcb se resuelven contra la
ubicacion de este propio archivo (Path(__file__)), nunca contra el cwd.

Alto de panel, inset de tornillo, diametro de taladro M3 y espesor de PCB
NO se hardcodean aqui: salen de case/cad/params.scad via leer_params() de
clearance_budget.py (unica fuente de verdad dimensional del proyecto).
Solo --ancho sigue siendo argumento de linea de comandos, porque es lo
unico que varia por modulo. Antes de dibujar nada corren dos guardas:

  1. que alto_panel - 2*inset_y cuadre con sep_railes (spec §6) -- si
     params.scad se desincroniza, no atornilla contra los railes reales;
  2. que el --ancho pedido deje puente de material entre los dos taladros
     M3 de una misma cara (separacion en X = ancho - 2*inset_x, minimo
     d_M3_paso + 2 mm de puente -- ese 2 mm es un juicio de diseno,
     no un numero derivado de ninguna spec) -- sin esto, un panel angosto
     (ej. 2HP Eurorack = 10.16 mm) genera dos agujeros superpuestos sin
     avisar (fallo invisible hasta fabricacion, Principio V).

Si cualquiera falla, el script sale en ROJO en vez de generar una plantilla
rota (Principio III de la constitucion: la comprobacion corre antes del
paso destructivo).

Dibuja: contorno rectangular en Edge.Cuts (ancho x alto del piso); 4 taladros
M3 no plateados (NPTH) en los centros de rail, a inset_x / inset_y mm de cada
borde EN LOS DOS EJES (X e Y: no solo arriba/abajo, tambien izquierda/
derecha; en el piso EUROrack esos dos insets NO son el mismo numero, ver
insets()), sin kerf (el kerf es del corte laser del acrilico, no de un
taladro de PCB: el diametro que da params.scad ya es el final); rotulo de
plantilla en F.Silkscreen.

Fabricacion: PCB de aluminio, espesor fijado desde t_panel de params.scad
via GetDesignSettings().SetBoardThickness() -- no es el default de
pcbnew, se lee de la fuente de verdad (spec §2; JLCPCB estandar 1.6 mm);
serigrafia blanca.

Los modulos futuros COPIAN el .kicad_pcb generado y lo editan; el artefacto
de verdad es este script, no el s-expr ("el artefacto es el script").
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from clearance_budget import leer_params  # noqa: E402


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def insets(p: dict[str, float], piso: str) -> tuple[float, float]:
    """Inset del taladro (x, y) del piso, en mm desde el canto del PANEL.

    Desde el 2026-08-17 LAS DOS FILAS son 3U, asi que las dos se taladran con
    las cotas de EUROrack: inset_er = 3.0 mm de los cantos de arriba y abajo
    (de ahi los 122.50 entre centros) y inset_er_x = 7.5 del izquierdo. NO son
    el mismo numero en los dos ejes -- el estandar no es simetrico, y eso es
    justo lo que este fichero hacia mal cuando usaba un solo inset.

    Sigue tomando `piso` aunque hoy devuelva lo mismo para los dos: es aqui
    donde se ramifica el dia que una fila deje de ser 3U, y mientras tanto
    verificar_coherencia() comprueba cada fila contra SU sep_railes, asi que
    una divergencia en params.scad sale en rojo y no en silencio."""
    del piso
    return p["inset_er_x"], p["inset_er"]


def verificar_coherencia(p: dict[str, float], piso: str) -> None:
    """Ruling A: si alguien cambia params.scad y alto_panel/inset dejan de
    cuadrar con sep_railes, ese quiebre tiene que verse ANTES de generar la
    plantilla, no despues como un panel que no atornilla.

    Desde el 2026-08-17 las dos filas son 3U de EUROrack (128.5 mm, taladro a
    3.0 del canto), asi que las dos plantillas salen iguales. Ojo: alto_panel_*
    es la PCB, no el tramo de perfil del costado -- eso es alto_cara_*, y ya no
    valen lo mismo en ninguna de las dos filas."""
    alto = p[f"alto_panel_{piso}"]
    sep = p[f"sep_railes_{piso}"]
    _, inset_y = insets(p, piso)
    calc = alto - 2 * inset_y
    if abs(calc - sep) > 1e-6:
        print(f"ROJO: alto_panel_{piso}({alto}) - 2*inset_y({inset_y}) = "
              f"{calc} != sep_railes_{piso}({sep}) -- params.scad "
              f"incoherente (spec §6)")
        sys.exit(2)


def verificar_ancho_minimo(p: dict[str, float], ancho: float,
                            inset_x: float) -> None:
    """Fix review Task 7: el inset posiciona los taladros M3 en LOS DOS ejes,
    no solo en Y -- con --ancho chico los dos agujeros de una misma cara
    (izquierda y derecha) se acercan en X y pueden superponerse sin que nada
    avise (fallo invisible hasta fabricacion, Principio V). PUENTE_MIN=2.0 mm
    es un juicio de diseno (cuanto material minimo dejar entre dos taladros),
    no un numero derivado de ninguna spec."""
    PUENTE_MIN = 2.0
    sep_centros = ancho - 2 * inset_x
    minimo = p["d_M3_paso"] + PUENTE_MIN
    if sep_centros < minimo:
        ancho_min = 2 * inset_x + minimo
        print(f"ROJO: ancho={ancho} deja los taladros M3 de una cara a "
              f"{sep_centros:.2f} mm de separacion entre centros (minimo "
              f"{minimo:.2f} mm = d_M3_paso + {PUENTE_MIN} mm de puente) "
              f"-- ancho minimo viable {ancho_min:.2f} mm")
        sys.exit(2)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="SAM17: genera panel-template-{inf,sup}.kicad_pcb")
    ap.add_argument("--ancho", type=float, default=100.0,
                     help="ancho del panel en mm (varia por modulo)")
    ap.add_argument("--piso", choices=("inf", "sup"), default="sup",
                     help="piso del panel: las dos filas son 3U EUROrack "
                          "(128.5 mm) y hoy salen identicas; el flag existe "
                          "para el dia que una deje de serlo")
    args = ap.parse_args()
    ancho, piso = args.ancho, args.piso

    p = leer_params()
    verificar_coherencia(p, piso)
    inset_x, inset_y = insets(p, piso)
    verificar_ancho_minimo(p, ancho, inset_x)
    alto = p[f"alto_panel_{piso}"]
    d_taladro = p["d_M3_paso"]  # sin kerf: taladro de PCB, diametro final

    board = pcbnew.CreateEmptyBoard()
    board.GetDesignSettings().SetBoardThickness(mm(p["t_panel"]))
    # contorno
    pts = [(0, 0), (ancho, 0), (ancho, alto), (0, alto)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(mm(pts[i][0]), mm(pts[i][1])))
        seg.SetEnd(pcbnew.VECTOR2I(mm(pts[(i + 1) % 4][0]), mm(pts[(i + 1) % 4][1])))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.1))
        board.Add(seg)
    # 4 agujeros M3 no plateados (NPTH) en los centros de rail
    for x in (inset_x, ancho - inset_x):
        for y in (inset_y, alto - inset_y):
            fp = pcbnew.FOOTPRINT(board)
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            pad = pcbnew.PAD(fp)
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
            pad.SetDrillSize(pcbnew.VECTOR2I(mm(d_taladro), mm(d_taladro)))
            pad.SetSize(pcbnew.VECTOR2I(mm(d_taladro), mm(d_taladro)))
            pad.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.Add(pad)
            board.Add(fp)
    # rotulo de plantilla
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText("SAM17 PANEL TEMPLATE")
    txt.SetPosition(pcbnew.VECTOR2I(mm(ancho / 2), mm(alto / 2)))
    txt.SetLayer(pcbnew.F_SilkS)
    board.Add(txt)

    # El nombre lleva el piso: los dos altos son plantillas DISTINTAS y con
    # un solo nombre la segunda corrida se comia a la primera en silencio.
    out = HERE / f"panel-template-{piso}.kicad_pcb"
    pcbnew.SaveBoard(str(out), board)
    print(f"escrito {out.name} ({ancho} x {alto} mm, taladro M3 d={d_taladro} mm)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
