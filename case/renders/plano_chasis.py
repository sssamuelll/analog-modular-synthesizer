"""Plano de plegado de las tres chapas de acero del chasis del PSU.

    python case/renders/plano_chasis.py

Existe porque el DXF NO es el entregable completo. Un .dxf lleva geometria de
corte y nada mas: dice donde esta el borde y donde estan los agujeros, y de
donde hay que DOBLAR no dice ni una palabra. Mandar solo el DXF a un taller de
plegado es mandar media pieza y confiar en que la adivine.

Asi que este script lee los mismos DXF que se mandan a cortar -- no el modelo,
los ficheros -- y les superpone lo que el taller necesita encima:

  * las lineas de plegado, en el centro del arco (ala + BA/2)
  * el sentido de cada doblez (todos hacia arriba, 90 grados)
  * los tres numeros de los que depende el desarrollo, dichos como SUPUESTOS
  * la cota exterior que tiene que salir, para que la mida al terminar

Lo ultimo es lo que convierte el plano en verificable: si el taller dobla con
otro radio del que dice aqui, la caja no le va a salir a la cota, y eso se ve
con un calibre antes de soldar nada.
"""
from __future__ import annotations

import sys
from pathlib import Path

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "case"))
import clearance_budget as cb                                   # noqa: E402

PLANS = RAIZ / "case" / "plans"
SALIDA = RAIZ / "case" / "renders" / "chasis-plano-plegado.png"

TINTA = "#1b1b1d"
DOBLEZ = "#c0392b"
COTA = "#2c6fb5"


def aristas(nombre: str) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Segmentos del DXF tal como los va a leer la maquina."""
    doc = ezdxf.readfile(PLANS / f"{nombre}.dxf")
    out = []
    for e in doc.modelspace():
        if e.dxftype() == "LINE":
            out.append(((e.dxf.start.x, e.dxf.start.y),
                        (e.dxf.end.x, e.dxf.end.y)))
        elif e.dxftype() == "LWPOLYLINE":
            pts = [(x, y) for x, y in e.get_points("xy")]
            cerrado = e.closed
            for i in range(len(pts) - (0 if cerrado else 1)):
                out.append((pts[i], pts[(i + 1) % len(pts)]))
    return out


def dibujar(ax, nombre: str, plegados: list[tuple[str, float]],
            titulo: str, subtitulo: str) -> None:
    segs = aristas(nombre)
    if not segs:
        raise SystemExit(f"{nombre}.dxf sin geometria -- correr export.ps1")
    for (x0, y0), (x1, y1) in segs:
        ax.plot([x0, x1], [y0, y1], color=TINTA, lw=0.9, solid_capstyle="round")

    xs = [c for s in segs for c in (s[0][0], s[1][0])]
    ys = [c for s in segs for c in (s[0][1], s[1][1])]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)

    for eje, pos in plegados:
        if eje == "v":
            ax.plot([pos, pos], [y0, y1], color=DOBLEZ, lw=1.1, ls=(0, (7, 4)))
        else:
            ax.plot([x0, x1], [pos, pos], color=DOBLEZ, lw=1.1, ls=(0, (7, 4)))

    m = 0.06 * max(x1 - x0, y1 - y0)
    ax.set_xlim(x0 - m, x1 + m)
    ax.set_ylim(y0 - m, y1 + m * 2.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(x0, y1 + m * 1.55, titulo, color=TINTA, fontsize=12,
            fontweight="bold", va="bottom")
    ax.text(x0, y1 + m * 0.55, subtitulo, color=COTA, fontsize=9, va="bottom")
    ax.annotate("", xy=(x0, y0 - m * 0.5), xytext=(x1, y0 - m * 0.5),
                arrowprops=dict(arrowstyle="<->", color=COTA, lw=0.8))
    ax.text((x0 + x1) / 2, y0 - m * 0.75, f"{x1 - x0:.2f}", color=COTA,
            fontsize=8, ha="center", va="top")
    ax.annotate("", xy=(x1 + m * 0.5, y0), xytext=(x1 + m * 0.5, y1),
                arrowprops=dict(arrowstyle="<->", color=COTA, lw=0.8))
    ax.text(x1 + m * 0.7, (y0 + y1) / 2, f"{y1 - y0:.2f}", color=COTA,
            fontsize=8, rotation=90, ha="left", va="center")


def main() -> int:
    p = cb.leer_params()
    c = cb._chasis(p)
    t, r, k = p["t_chapa"], p["radio_doblez"], p["k_factor"]
    ba = c["ba"]
    # Linea de plegado = centro del arco. Es lo que el operario alinea con el
    # punzon, y NO coincide con el canto del suelo: va media BA mas adentro.
    ala_c = c["ext_z"] - c["sb"]
    ala_t = c["faldon"] - c["sb"]
    lc, lt = ala_c + ba / 2, ala_t + ba / 2

    fig = plt.figure(figsize=(15, 11), facecolor="white")
    gs = fig.add_gridspec(2, 2, height_ratios=[1.5, 1], hspace=0.16, wspace=0.1)

    dibujar(fig.add_subplot(gs[0, :]), "chasis_cuerpo_2d",
            [("v", lc), ("v", c["blank_cuerpo_x"] - lc),
             ("h", lc), ("h", c["blank_cuerpo_y"] - lc)],
            "CUERPO — 4 dobleces de 90° hacia arriba, esquinas soldadas",
            f"montado {c['ext_x']:.1f} x {c['ext_y']:.1f} x {c['ext_z']:.1f} "
            f"exterior · agujeros: 1xM6, {int(p['chasis_to220_n'])}xM3 (TO-220), "
            f"1xM4 (PE), "
            f"{int(2 * (p['chasis_tornillos_largo'] + p['chasis_tornillos_corto']))}xM3 "
            f"(tapa), 4xM4 (a la tabla, por el suelo)")

    dibujar(fig.add_subplot(gs[1, 0]), "chasis_tapa_2d",
            [("v", lt), ("v", c["blank_tapa_x"] - lt),
             ("h", lt), ("h", c["blank_tapa_y"] - lt)],
            "TAPA — faldón de 15 por FUERA del cuerpo",
            f"encaja sobre {c['ext_x']:.1f} x {c['ext_y']:.1f} con "
            f"{p['chasis_hol_tapa']:.1f} de juego total")

    dibujar(fig.add_subplot(gs[1, 1]), "chasis_refuerzo_2d", [],
            "REFUERZO — plano, sin doblar",
            "DENTRO de la caja, sobre el suelo, contra el modo propio "
            "del toroide (#106)")

    fig.suptitle("SAM17 · chasis de acero del PSU — plano de plegado",
                 fontsize=15, fontweight="bold", color=TINTA, y=0.975)
    fig.text(0.5, 0.945,
             f"chapa {t} mm · radio interior {r} mm · factor K {k} · "
             f"BA {ba:.3f} · deducción {c['bd']:.3f} por doblez   —   "
             f"LOS TRES PRIMEROS SON SUPUESTOS: si el taller trabaja con otros, "
             f"el desarrollo cambia y hay que regenerar",
             ha="center", fontsize=9, color=DOBLEZ)
    fig.legend(handles=[Line2D([], [], color=TINTA, lw=1.2, label="corte"),
                        Line2D([], [], color=DOBLEZ, lw=1.2, ls=(0, (7, 4)),
                               label="línea de plegado (centro del arco)")],
               loc="lower center", ncol=2, frameon=False, fontsize=9)
    fig.savefig(SALIDA, dpi=140, bbox_inches="tight", facecolor="white")

    # Verificar el PNG, no confiar en que savefig no reviente (mismo criterio
    # que render.py: un fichero escrito no prueba que se vea nada).
    peso = SALIDA.stat().st_size
    if peso < 50_000:
        print(f"ROJO: {SALIDA.name} pesa {peso} B, sospechoso de estar vacio")
        return 1
    print(f"plano_chasis: {SALIDA.relative_to(RAIZ)} ({peso // 1024} KB)")
    print(f"  desarrollo cuerpo {c['blank_cuerpo_x']:.2f} x "
          f"{c['blank_cuerpo_y']:.2f}, lineas de plegado a {lc:.3f} del canto")
    print(f"  desarrollo tapa   {c['blank_tapa_x']:.2f} x "
          f"{c['blank_tapa_y']:.2f}, lineas de plegado a {lt:.3f} del canto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
