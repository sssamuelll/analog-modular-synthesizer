"""El cierre de llamadas del J2 en la ITCM: nada de lo que corre desde la ITCM salta fuera de ella.

    python tcm_cierre.py target/thumbv8m.main-none-eabihf/release/carga_j2

Lee el desensamblado de `.itcm` (rust-objdump) y busca cada `bl`, `blx`, `b` y `b.w` a una
direccion fuera de `__sitcm`..`__eitcm`, contando como fuera los saltos a un veneer
(`__Thumbv7ABSLongThunk_*`) por el destino que nombra. Pasan solo los caminos frios: panicos,
`defmt` y el contaminador del banco. Cualquier otro sale con 1: el texto de una rutina del J2
que se capta desde la AXISRAM2 devuelve la cache fria a la fila del censo (papel v3, R-H4).
"""
import re
import subprocess
import sys

FRIOS = re.compile(r"panic|unwrap_failed|slice_index|div_by_zero|defmt|invalida_icache")


def main(elf):
    nm = subprocess.run(["rust-nm", elf], capture_output=True, text=True, check=True).stdout
    lim = {m.group(2): int(m.group(1), 16) for m in re.finditer(r"^([0-9a-f]+) \w (__[se]itcm)$", nm, re.M)}
    ini, fin = lim["__sitcm"], lim["__eitcm"]
    dis = subprocess.run(
        ["rust-objdump", "-d", "--no-show-raw-insn", "-C", "--section=.itcm", elf],
        capture_output=True, text=True, check=True,
    ).stdout
    quien, fugas = None, set()
    for linea in dis.splitlines():
        m = re.match(r"^[0-9a-f]{8} <(.*)>:", linea)
        if m:
            quien = m.group(1)
            continue
        m = re.search(r"\s(?:bl|blx|b|b\.w)\s+0x([0-9a-f]+)\s+<([^>]*)>", linea)
        if not m or quien is None:
            continue
        destino, nombre = int(m.group(1), 16), m.group(2)
        fuera = not ini <= destino < fin or nombre.startswith("__Thumbv7ABSLongThunk_")
        if fuera and not FRIOS.search(nombre):
            fugas.add((quien, nombre))
    for quien, nombre in sorted(fugas):
        print(f"FUGA {quien} -> {nombre}")
    print(f"tcm_cierre: .itcm {fin - ini} B, {len(fugas)} llamadas fuera de la ITCM")
    return 1 if fugas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
