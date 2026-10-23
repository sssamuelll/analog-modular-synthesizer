"""Exporta el paquete de fabricacion de la placa v5 desde el .kicad_pcb commiteado.

    python build_fab.py        # escribe ../fab/ y ../pcb/; necesita kicad-cli

  ../fab/  gerbers de las 4 capas de cobre + pasta, mascaras, serigrafias y
           contorno; taladros (PTH y NPTH en un .drl); posiciones; BOM y CPL
           de JLCPCB (bom_jlc.py, cpl_jlc.py).
  ../pcb/  vistas: SVG de la cara de arriba y PDF de una pagina por capa, mas
           el dibujo de montaje (F.Fab, donde estan TODAS las referencias:
           las de las zonas densas no caben en la serigrafia).

check_fab.py reexporta con estas mismas ordenes y compara contra lo
commiteado: si alguien rerutea y no reexporta, se pone rojo. Por eso las
ordenes viven en UN sitio (EXPORTS) y las dos leen de aqui.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BASE = "sam17-power-v5"
PCB = os.path.join(DIR, f"{BASE}.kicad_pcb")
FAB = os.path.join(DIR, "..", "fab")
VISTAS = os.path.join(DIR, "..", "pcb")
KICAD_CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or (
    r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" if os.name == "nt" else "")

CAPAS_GERBER = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu", "F.Paste", "F.Mask", "B.Mask",
                "F.Silkscreen", "B.Silkscreen", "Edge.Cuts")
GERBERS = tuple(f"{BASE}-{n}" for n in (
    "F_Cu.gtl", "In1_Cu.g1", "In2_Cu.g2", "B_Cu.gbl", "F_Paste.gtp", "F_Mask.gts",
    "B_Mask.gbs", "F_Silkscreen.gto", "B_Silkscreen.gbo", "Edge_Cuts.gm1"))
TALADROS = f"{BASE}.drl"
POSICIONES = f"{BASE}-pos.csv"


def exports(destino: str) -> list[list[str]]:
    """Las ordenes de kicad-cli que producen los ficheros de fabricacion."""
    return [
        [KICAD_CLI, "pcb", "export", "gerbers", "--output", destino, "--layers", ",".join(CAPAS_GERBER),
         "--no-x2", PCB],
        [KICAD_CLI, "pcb", "export", "drill", "--output", destino, "--format", "excellon",
         "--excellon-units", "mm", PCB],
        [KICAD_CLI, "pcb", "export", "pos", "--output", os.path.join(destino, POSICIONES),
         "--format", "csv", "--units", "mm", "--side", "front", "--smd-only", PCB],
    ]


def correr(orden: list[str]) -> None:
    r = subprocess.run(orden, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FALLO: {' '.join(orden[:4])}:\n{r.stdout[-800:]}{r.stderr[-800:]}")


def main() -> int:
    if not KICAD_CLI or not os.path.exists(KICAD_CLI):
        print("FALLO: no hay kicad-cli (KICAD_CLI o PATH)")
        return 1
    os.makedirs(FAB, exist_ok=True)
    os.makedirs(VISTAS, exist_ok=True)
    for orden in exports(FAB):
        correr(orden)
    for nombre in GERBERS + (TALADROS, POSICIONES):
        assert os.path.isfile(os.path.join(FAB, nombre)), f"kicad-cli no escribio {nombre}"
    for guion in ("bom_jlc.py", "cpl_jlc.py"):
        r = subprocess.run([sys.executable, os.path.join(DIR, guion)], capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode != 0:
            print(r.stderr.strip())
            return 1
    correr([KICAD_CLI, "pcb", "export", "svg", "--output", os.path.join(VISTAS, f"{BASE}.svg"),
            "--layers", "F.Cu,F.Silkscreen,Edge.Cuts", "--mode-single", "--exclude-drawing-sheet",
            "--fit-page-to-board", PCB])
    correr([KICAD_CLI, "pcb", "export", "pdf", "--output", os.path.join(VISTAS, f"{BASE}.pdf"),
            "--layers", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Fab",
            "--common-layers", "Edge.Cuts", "--mode-multipage", "--sketch-pads-on-fab-layers", PCB])
    print(f"fab/: {len(GERBERS)} gerbers, {TALADROS}, {POSICIONES}; pcb/: {BASE}.svg y {BASE}.pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
