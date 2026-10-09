"""PUERTA de la piel impresa: las piezas de case/print/piel/ salen en UNA isla
cada una y ninguna se mete en otra (ni en la tabla, los anillos, los paneles o
la trasera). Las reglas viven en piel_choques.py; esto las corre en Blender y
traduce el resultado al codigo de salida de hardware/tools/gates.py.

    python check_piel.py        0 = verde, 1 = rojo, 2 = HUECO (no se pudo mirar)

HUECO, no rojo, cuando no hay que mirar: los STL de la piel no se versionan
hasta la firma (el papel del 2026-09-05, seccion 9.1), asi que en un clon
limpio no existen; y sin Blender no hay con que medirlos. Ninguno de los dos
casos dice que la piel este bien, y por eso tampoco sale en verde.
"""
import json
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
PRINT = os.path.join(AQUI, "..", "print", "piel")
BLENDER = os.environ.get("SAM17_BLENDER",
                         r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe")
PIEZAS = ("cachete_der", "cachete_izq", "cubierta")


def main() -> int:
    faltan = [p for p in PIEZAS if not os.path.exists(os.path.join(PRINT, p + ".stl"))]
    if faltan:
        print(f"HUECO: no hay piel impresa ({', '.join(faltan)}): corre imprimir_piel.py")
        return 2
    if not os.path.exists(BLENDER):
        print(f"HUECO: necesita Blender en {BLENDER} (o SAM17_BLENDER)")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        salida = os.path.join(tmp, "piel.json")
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P",
                            os.path.join(AQUI, "piel_choques.py"), "--", salida],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=540)
        for linea in (r.stdout or "").splitlines():
            if linea.startswith(("  OK", "  ROJO", "PIEL ")):
                print(linea)
        if not os.path.exists(salida):
            print("ROJO: piel_choques.py no llego a escribir su informe")
            print((r.stdout or "")[-1500:] + (r.stderr or "")[-1500:])
            return 1
        with open(salida, encoding="utf-8") as f:
            info = json.load(f)
    return 0 if info["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
