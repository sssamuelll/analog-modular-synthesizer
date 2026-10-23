"""Puerta: el DRC de KiCad sobre sam17-power-v5.kicad_pcb, en vivo y con todo.

    python check_drc.py        # 0 = limpio, 1 = infracciones, 2 = sin kicad-cli

Todas las severidades (errores Y avisos: la serigrafia sobre un pad es un
aviso y aun asi es un defecto de fabricacion), la paridad con el esquematico
y las zonas RE-rellenadas antes de mirar, para que un relleno guardado y
viejo no tape una pista movida a mano despues.

check_pcb.py mira lo mismo sin KiCad, pero de segunda mano: se fia del
informe que dejo build_pcb.py si la placa es la misma (sha256). Esta lo
vuelve a correr. Donde hay KiCad corren las dos; en el CI, solo aquella.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-power-v5.kicad_pcb")
KICAD_CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or (
    r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" if os.name == "nt" else "")


def main() -> int:
    if not os.path.exists(PCB):
        print("HUECO: falta sam17-power-v5.kicad_pcb -- corre build_pcb.py")
        return 2
    if not KICAD_CLI or not os.path.exists(KICAD_CLI):
        print("HUECO: no hay kicad-cli en esta maquina (KICAD_CLI o PATH)")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        rpt = os.path.join(tmp, "drc.json")
        r = subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all",
                            "--schematic-parity", "--refill-zones", "--units", "mm", "-o", rpt, PCB],
                           capture_output=True, text=True)
        if not os.path.exists(rpt):
            print(f"FALLO: kicad-cli no dejo informe: {r.stderr.strip()[-300:]}")
            return 1
        with open(rpt, encoding="utf-8") as fh:
            informe = json.load(fh)
    infr = informe.get("violations", [])
    sueltos = informe.get("unconnected_items", [])
    paridad = informe.get("schematic_parity", [])
    print(f"DRC de {os.path.basename(PCB)} (KiCad {informe.get('kicad_version', '?')}): "
          f"{len(infr)} infracciones, {len(sueltos)} sin conectar, {len(paridad)} de paridad")
    for v in (infr + sueltos + paridad)[:25]:
        quien = " | ".join(i.get("description", "")[:60] for i in v.get("items", []))
        print(f"  [{v.get('type', '?')}] {v.get('description', '')}: {quien}")
    if infr or sueltos or paridad:
        return 1
    print("OK: check_drc v5 -- DRC limpio con todas las severidades, zonas rellenadas y paridad")
    return 0


if __name__ == "__main__":
    sys.exit(main())
