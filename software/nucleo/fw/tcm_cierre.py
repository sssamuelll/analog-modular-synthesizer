"""El cierre de llamadas del J2 en la ITCM: nada de lo que corre desde la ITCM salta fuera de ella.

    python tcm_cierre.py target/thumbv8m.main-none-eabihf/release/carga_j2 --raices TIM7,DMA2D,JPEG

Lee el desensamblado de `.itcm` (rust-objdump) y busca cada `bl`, `blx`, `b` y `b.w` a una
direccion fuera de `__sitcm`..`__eitcm`, contando como fuera los saltos a un veneer
(`__Thumbv7ABSLongThunk_*`) por el destino que nombra. Pasan solo los caminos frios: panicos,
`defmt` y el contaminador del banco. Cualquier otro sale con 1: el texto de una rutina del J2
que se capta desde la AXISRAM2 devuelve la cache fria a la fila del censo (papel v3, R-H4).

Con `--raices`, ademas, cada manejador nombrado (los vectores del J2: en el banco `TIM7`, `DMA2D` y
`JPEG`; en el hub, los que fije R-H1) tiene que estar dentro de la ITCM. El cierre solo mira lo que
sale; sin las raices, un manejador que se quede fuera no sale de ningun sitio y nada falla.
"""
import re
import subprocess
import sys

FRIOS = re.compile(r"panic|unwrap_failed|slice_index|div_by_zero|defmt|invalida_icache")


def main(elf, raices):
    nm = subprocess.run(["rust-nm", elf], capture_output=True, text=True, check=True).stdout
    lim = {m.group(2): int(m.group(1), 16) for m in re.finditer(r"^([0-9a-f]+) \w (__[se]itcm)$", nm, re.M)}
    ini, fin = lim["__sitcm"], lim["__eitcm"]
    simbolos = {m.group(2): int(m.group(1), 16) for m in re.finditer(r"^([0-9a-f]+) \w (\S+)$", nm, re.M)}
    fuera_raiz = []
    for r in raices:
        a = simbolos.get(r)
        if a is None or not ini <= (a & ~1) < fin:
            fuera_raiz.append(r)
            print(f"RAIZ {r} " + ("no existe" if a is None else f"en {a:#010x}, fuera de la ITCM"))
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
    print(f"tcm_cierre: .itcm {fin - ini} B, {len(fugas)} llamadas fuera de la ITCM, {len(raices) - len(fuera_raiz)} de {len(raices)} raices dentro")
    return 1 if fugas or fuera_raiz else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    raices = []
    if "--raices" in args:
        i = args.index("--raices")
        raices = [r for r in args[i + 1].split(",") if r]
        del args[i : i + 2]
    sys.exit(main(args[0], raices))
