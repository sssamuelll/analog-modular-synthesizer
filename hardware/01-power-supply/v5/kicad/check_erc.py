"""Puerta: el ERC de KiCad sobre sam17-power-v5.kicad_sch, con TODAS las severidades.

    python check_erc.py        # 0 = ERC limpio, 1 = infracciones, 2 = sin kicad-cli

Sustituye a check_collisions.py y check_layout.py de #474. El primero salia con
0 cuando faltaba la hoja (HUECO disfrazado de verde) y su expresion regular de
cables no casaba con el formato que escribe KiCad, asi que no comprobaba ningun
cable. El segundo comparaba una tabla de coordenadas escrita a mano --que no era
ni la hoja ni la placa-- y solo imprimia una ALERTA, sin salir nunca con error.

Aqui el juez es el ERC del propio KiCad. Las colisiones de redes al GENERAR la
hoja las caza build_schematic.py (schcheck.redes_fusionadas) antes de escribirla.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(DIR, "sam17-power-v5.kicad_sch")
KICAD_CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or (
    r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" if os.name == "nt" else "")


def main() -> int:
    if not os.path.exists(SCH):
        print("HUECO: falta sam17-power-v5.kicad_sch -- corre build_schematic.py")
        return 2
    if not KICAD_CLI or not os.path.exists(KICAD_CLI):
        print("HUECO: no hay kicad-cli en esta maquina (KICAD_CLI o PATH)")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        rpt = os.path.join(tmp, "erc.rpt")
        r = subprocess.run([KICAD_CLI, "sch", "erc", "--severity-all", "-o", rpt, SCH],
                           capture_output=True, text=True)
        if not os.path.exists(rpt):
            print(f"FALLO: kicad-cli no dejo informe: {r.stderr.strip()[-300:]}")
            return 1
        with open(rpt, encoding="utf-8", errors="replace") as fh:
            informe = fh.read()
    tipos = re.findall(r"^\[(\w+)\]: (.*)$", informe, re.M)
    print(f"ERC de {os.path.basename(SCH)}: {len(tipos)} infracciones (errores y avisos)")
    if tipos:
        for t, msg in tipos[:25]:
            print(f"  [{t}] {msg}")
        return 1
    print("OK: check_erc v5 -- ERC limpio con todas las severidades")
    return 0


if __name__ == "__main__":
    sys.exit(main())
