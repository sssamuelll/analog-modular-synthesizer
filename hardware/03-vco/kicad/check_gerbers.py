"""Lo que se manda a fabricar ES la placa que se diseño. Ultimo paso sin puerta.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" check_gerbers.py
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" check_gerbers.py --mutar

POR QUE EXISTE
--------------------------------------------------------------------------
El repositorio tenia puertas para el esquematico (ERC, check_netlist, el
golden de netdiff) y para la placa (DRC, las medidas de build_pcb.py). No
tenia ninguna para el paso siguiente, que es el unico que cuesta dinero:
exportar los gerbers y subirlos.

Y ese paso NO lo hace build_pcb.py -- lo hace kicad-cli aparte, a mano, con
seis comandos escritos en pcb/README.md. Nada comprobaba que los ficheros
commiteados en pcb/ siguieran siendo los de la placa commiteada en kicad/.
Bastaba con reruteear y olvidarse de reexportar para tener en el repositorio
un juego de gerbers de una placa anterior, listo para subir, sin que ninguna
puerta dijera nada.

Es el Principio III aplicado al final del proceso: la comprobacion va donde
esta el paso destructivo, y aqui el paso destructivo es el pedido.

COMO LO COMPRUEBA
--------------------------------------------------------------------------
Reexporta a un directorio temporal y compara. No mira "parece correcto": mira
si el fichero que hay en pcb/ es byte a byte el que sale de la placa de hoy,
descontando las lineas de cabecera que llevan fecha y version de herramienta.
Es el mismo truco del .netgold de netdiff.py, y trae el mismo corolario
gratis: si la reexportacion no reproduce lo commiteado, uno de los dos miente.

LO QUE **NO** CUBRE
--------------------------------------------------------------------------
  * Que los gerbers sean correctos. Eso lo dice el DRC sobre la placa, y el
    visor del fabricante antes de pagar. Esto dice que SON LOS DE ESTA PLACA.
  * El zip que se sube: se arma a mano al pedir.
  * Los codigos LCSC y su stock. Se re-verifican el dia de mandar (issue
    #57); aqui solo se cuenta cuantas filas del BOM siguen sin cerrar.
"""
from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(DIR, "sam17-vco.kicad_pcb")
FAB = os.path.join(DIR, "..", "pcb")
KICAD_CLI = os.environ.get(
    "KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")

CAPAS = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu", "F.Mask", "B.Mask",
         "F.Silkscreen", "B.Silkscreen", "Edge.Cuts")
GERBERS = ("F_Cu.gtl", "In1_Cu.g1", "In2_Cu.g2", "B_Cu.gbl",
           "F_Mask.gts", "B_Mask.gbs", "F_Silkscreen.gto",
           "B_Silkscreen.gbo", "Edge_Cuts.gm1")
BOM = os.path.join(FAB, "sam17-vco-bom.csv")
CPL = os.path.join(FAB, "sam17-vco-cpl-jlc.csv")
POS = os.path.join(FAB, "sam17-vco-pos.csv")
DRL = os.path.join(FAB, "sam17-vco.drl")


def canon(ruta: str) -> list[str]:
    """El fichero sin lo que cambia entre dos exportaciones identicas.

    Los gerbers llevan la fecha de creacion y la version de KiCad en
    comentarios G04; el Excellon, en lineas que empiezan por ';'. Comparar en
    crudo daria un falso rojo en cada corrida y el gate se volveria ruido que
    la gente aprende a ignorar, que es la peor clase de gate.
    """
    fecha = re.compile(r"\d{4}-\d{2}-\d{2}|CreationDate|GenerationSoftware"
                       r"|KiCad|ProjectId")
    out = []
    for cruda in open(ruta, encoding="utf-8", errors="replace"):
        linea = cruda.rstrip("\r\n")
        if linea.startswith("G04") or linea.startswith(";"):
            if fecha.search(linea):
                continue
        out.append(linea)
    return out


def reexportar(tmp: str) -> None:
    subprocess.run([KICAD_CLI, "pcb", "export", "gerbers", "--output", tmp,
                    "--layers", ",".join(CAPAS), "--no-x2", PCB],
                   capture_output=True, text=True, check=True)
    subprocess.run([KICAD_CLI, "pcb", "export", "drill", "--output", tmp,
                    "--format", "excellon", "--excellon-units", "mm", PCB],
                   capture_output=True, text=True, check=True)
    subprocess.run([KICAD_CLI, "pcb", "export", "pos", "--output",
                    os.path.join(tmp, "sam17-vco-pos.csv"), "--format", "csv",
                    "--units", "mm", "--side", "both", "--smd-only", PCB],
                   capture_output=True, text=True, check=True)


def main() -> int:
    fallos: list[str] = []
    huecos: list[str] = []

    faltan = [g for g in GERBERS
              if not os.path.isfile(os.path.join(FAB, "sam17-vco-" + g))]
    for extra in (DRL, POS, CPL, BOM):
        if not os.path.isfile(extra):
            faltan.append(os.path.basename(extra))
    if faltan:
        print(f"HUECO: faltan salidas de fabricacion: {faltan}")
        print("  Generalas con los comandos del final de pcb/README.md")
        return 2

    tmp = tempfile.mkdtemp(prefix="sam17-vco-fab-")
    try:
        reexportar(tmp)
        viejos = []
        for g in GERBERS + ("sam17-vco.drl",):
            nombre = g if g.endswith(".drl") else "sam17-vco-" + g
            a, b = os.path.join(FAB, nombre), os.path.join(tmp, nombre)
            if not os.path.isfile(b):
                fallos.append(f"la reexportacion no genero {nombre}")
                continue
            if canon(a) != canon(b):
                viejos.append(nombre)
        a, b = POS, os.path.join(tmp, "sam17-vco-pos.csv")
        if canon(a) != canon(b):
            viejos.append("sam17-vco-pos.csv")
        if viejos:
            fallos.append(
                f"{len(viejos)} salidas NO son las de esta placa: {viejos}\n"
                f"    La placa se toco despues de exportar. Reexporta con los "
                f"comandos del final de pcb/README.md antes de pedir nada.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    board = pcbnew.LoadBoard(PCB)
    caja = board.GetBoardEdgesBoundingBox()
    ancho, alto = caja.GetWidth() / 1e6, caja.GetHeight() / 1e6

    # "Pieza que la maquina coloca" es el ATRIBUTO de la huella, no "tiene
    # algun pad SMD". La primera version usaba lo segundo y daba 134 contra
    # los 119 del CPL: los 15 test points son pads SMD que nadie coloca, y el
    # gate los reclamaba como huecos de montaje. Proxy comodo, Principio IV, y
    # esta vez en la propia puerta que estaba escribiendo.
    #
    # Los tres grupos de esta placa, medidos: attr=1 THT (los 10 conectores,
    # se sueldan a mano), attr=2 SMD (119, los del CPL), attr=12 excluidos de
    # posiciones y de BOM (4 taladros de montaje + 15 test points).
    smd = {fp.GetReference() for fp in board.GetFootprints()
           if fp.GetAttributes() & pcbnew.FP_SMD
           and not fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES}
    filas_cpl = {f["Designator"] for f in csv.DictReader(open(CPL, encoding="utf-8"))}
    sobran, corto = sorted(filas_cpl - smd), sorted(smd - filas_cpl)
    if sobran:
        fallos.append(f"el CPL coloca piezas que no estan en la placa: {sobran}")
    if corto:
        fallos.append(
            f"huellas SMD de la placa sin linea en el CPL: {corto}\n"
            f"    La maquina deja esos pads vacios y no avisa.")

    sin_lcsc = [f["Designator"].split(",")[0]
                for f in csv.DictReader(open(BOM, encoding="utf-8"))
                if not (f.get("LCSC Part#") or "").strip()]
    subir = os.path.join(FAB, "sam17-vco-bom-jlc.csv")
    if sin_lcsc:
        huecos.append(
            f"{len(sin_lcsc)} filas del BOM sin codigo LCSC: {sin_lcsc}. "
            f"Celda vacia es lo correcto hasta verificarlo EN VIVO -- nunca "
            f"un codigo inventado. Sin ellas, bom_jlc.py se niega a escribir "
            f"el fichero que se sube, que es exactamente lo que tiene que "
            f"pasar.")
        if os.path.isfile(subir):
            fallos.append(
                "sam17-vco-bom-jlc.csv existe con el BOM SIN cerrar. Ese es "
                "el fichero que se sube: si esta y esta viejo, alguien lo "
                "sube. Borralo -- que falte es visible, que este mal no.")
    elif not os.path.isfile(subir):
        fallos.append(
            "el BOM esta cerrado pero falta sam17-vco-bom-jlc.csv: corre "
            "bom_jlc.py")

    print(f"placa {ancho:.1f} x {alto:.1f} mm, {len(smd)} huellas SMD")
    print(f"{len(GERBERS)} gerbers + taladro + posiciones reexportados y "
          f"comparados contra pcb/")
    print(f"CPL: {len(filas_cpl)} designadores, cuadran con la placa "
          f"en los dos sentidos")

    for f in fallos:
        print("\nFALLO:", f)
    if fallos:
        return 1
    for h in huecos:
        print("\nHUECO:", h)
    return 2 if huecos else 0


def _mutar() -> int:
    """Prueba que el gate DISTINGUE (constitucion, Principio VIII).

    Verde sobre unas salidas correctas no demuestra nada: podria estar
    comparando mal y salir verde siempre. La mutacion ensucia UN gerber con
    una linea de geometria de mas -- el tipo de cambio que de verdad ocurre
    cuando alguien rerutea y no reexporta -- y exige que el gate se ponga
    rojo. Se restaura pase lo que pase.
    """
    victima = os.path.join(FAB, "sam17-vco-F_Cu.gtl")
    copia = victima + ".bak"
    shutil.copy2(victima, copia)
    try:
        with open(victima, "a", encoding="utf-8") as fh:
            fh.write("X100000Y100000D02*\n")
        rc = main()
        if rc == 1:
            print("\nOK: el gate detecta un gerber que no es el de esta placa")
            return 0
        print(f"\nFALLO: la mutacion salio con {rc}. El gate NO compara nada.")
        return 1
    finally:
        shutil.move(copia, victima)


if __name__ == "__main__":
    sys.exit(_mutar() if "--mutar" in sys.argv else main())
