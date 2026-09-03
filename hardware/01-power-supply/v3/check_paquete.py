"""Puerta: el paquete de fabricacion commiteado es EL DE ESTA PLACA.

    python check_paquete.py     # sale != 0 si el paquete no casa con el PCB

## Por que existe, y por que check_fab.py no la sustituye

`check_fab.py` mide el paquete **por dentro**: que las seis capas existan y no
esten vacias, que el contorno cierre, que el cobre este dentro, que cada
taladro caiga donde debe, la barrera de red sobre el cobre del gerber, y que la
zona de referencia llegara al cobre.

Las seis son ciertas de un paquete **coherente consigo mismo**. Ninguna
pregunta si ese paquete corresponde al `.kicad_pcb` que esta commiteado a su
lado, porque `check_fab.py` no lee el `.kicad_pcb` a proposito -- corre con un
Python pelado, sin `pcbnew`, y esa independencia vale la pena conservarla.

El hueco que dejaban las dos juntas no es hipotetico (#281). En el #139 se
podaron dos vias del arbol de masa y la puerta de fabricacion siguio **en
verde** con los gerbers de la placa anterior: describian dos vias que ya no
existian y el drill traia dos taladros de mas. Se regenero el paquete porque
alguien se acordo, no porque una puerta lo pidiera.

## Lo que mide

Cruza los dos ficheros, que es lo unico que caza un paquete viejo:

  1. los trazos de cada gerber de cobre contra las pistas de la placa, uno a
     uno y con su ancho. Salen 1:1 -- 663 en F.Cu y 336 en B.Cu el 2026-09-02 --
     asi que no hay que estimar nada: o coinciden o no;
  2. los taladros del Excellon contra las vias mas los pads pasantes. 292 el
     mismo dia, y tambien uno a uno.

Una pista movida a mano en la GUI, una via podada, un pad que cambia de
huella: cualquiera de las tres rompe una de las dos listas.

## Lo que NO mide, y donde vive

La serigrafia, las mascaras y el contorno no se cruzan aqui. Los cubre
`check_fab.py` por dentro, y una mascara desfasada no manda cobre equivocado a
fabricar. Si algun dia importa, se anade una tercera lista.
"""
from __future__ import annotations

from collections import Counter
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "kicad"))

try:
    import pcbnew                                        # noqa: F401
except ImportError:
    print("HUECO: necesita el Python de KiCad (pcbnew) para leer la placa")
    raise SystemExit(2) from None

import check_fab as cf                                   # noqa: E402
import check_pcb as cp                                   # noqa: E402


def main() -> int:
    if not os.path.exists(cp.PCB):
        print("HUECO: falta sam17-power-v3.kicad_pcb -- correr build_pcb.py")
        return 2
    if not os.path.isdir(cf.FAB):
        print(f"HUECO: no existe {cf.FAB}, no hay paquete que cruzar")
        return 2

    board = pcbnew.LoadBoard(cp.PCB)
    tracks, vias = cp.leer_ruteo(board)
    fallos: list[str] = []

    def r(p):
        return (round(p[0], 4), round(p[1], 4))

    for capa, nombre in (("F.Cu", "F_Cu"), ("B.Cu", "B_Cu")):
        ruta = os.path.join(cf.FAB, f"{cf.BASE}-{nombre}.{cf.CAPAS[nombre]}")
        if not os.path.exists(ruta):
            fallos.append(f"falta el gerber de {nombre}")
            continue
        # Counter y no set: dos pistas identicas encima una de otra son un
        # defecto de verdad, y un conjunto las funde en una sola.
        gerber = Counter((min(r(a), r(b)), max(r(a), r(b)), round(w, 4))
                         for a, b, w in cf.Gerber(ruta).trazos)
        placa = Counter((min(r(pts[0]), r(pts[1])), max(r(pts[0]), r(pts[1])),
                         round(ancho, 4))
                        for _net, c, pts, ancho in tracks if c == capa)
        sin_exportar, de_mas = placa - gerber, gerber - placa
        print(f"  {nombre}: {sum(placa.values())} pistas en la placa, "
              f"{sum(gerber.values())} trazos en el gerber")
        if sin_exportar or de_mas:
            fallos.append(
                f"{nombre}: el gerber no es de esta placa -- "
                f"{sum(sin_exportar.values())} pistas sin exportar y "
                f"{sum(de_mas.values())} que el gerber trae de mas. "
                f"Ejemplo: {sorted(sin_exportar or de_mas)[0]}")

    drl = os.path.join(cf.FAB, f"{cf.BASE}.drl")
    if not os.path.exists(drl):
        fallos.append("falta el Excellon de taladros")
        return informe(fallos)

    taladros = [(vx, vy, taladro) for vx, vy, _n, _a, taladro in vias]
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                continue
            dx, dy = p.GetDrillSizeX() / 1e6, p.GetDrillSizeY() / 1e6
            if dx <= 0:
                continue
            if abs(dx - dy) > 1e-6:
                print(f"HUECO: el pad {fp.GetReference()}.{p.GetNumber()} "
                      "tiene taladro alargado y esta puerta solo cruza "
                      "taladros redondos")
                return 2
            c = p.GetPosition()
            taladros.append((c.x / 1e6, c.y / 1e6, dx))

    en_placa = sorted((round(x, 3), round(y, 3), round(d, 3))
                      for x, y, d in taladros)
    en_drl = sorted((round(x, 3), round(y, 3), round(d, 3))
                    for x, y, d in cf.lee_drill(drl))
    print(f"  taladros: {len(en_placa)} en la placa, {len(en_drl)} en el .drl")
    if en_placa != en_drl:
        faltan = sorted(set(en_placa) - set(en_drl))
        sobran = sorted(set(en_drl) - set(en_placa))
        fallos.append(
            f"el .drl no es de esta placa -- {len(faltan)} taladros sin "
            f"exportar y {len(sobran)} de mas. "
            f"Ejemplo: {(faltan or sobran)[0]}")
    return informe(fallos)


def informe(fallos: list[str]) -> int:
    if fallos:
        print(f"\nFALLO: {len(fallos)} en el paquete de fabricacion")
        for f in fallos:
            print(f"  - {f}")
        print("\n  El paquete se regenera con la secuencia de fab/README.md.")
        return 1
    print("\nOK: los gerbers de cobre y el drill commiteados son los de esta "
          "placa,\n    pista a pista y taladro a taladro.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
