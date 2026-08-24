"""Corre TODAS las puertas de calidad del hardware, en local y en CI.

    python hardware/tools/gates.py

La constitucion dice desde el principio que ninguna tanda de hardware se cierra
sin ERC, DRC, netlist, BOM y presupuestos en verde. Hasta ahora eso lo hacia
cumplir la memoria de quien mandaba el PR: el CI solo miraba el firmware de
Python y los enlaces de los markdown. Trece scripts con aserciones reales
vivian en el repo sin que nada los ejecutara.

Esto es lo unico que hace este fichero: ejecutarlos todos y sumar. No inventa
comprobaciones nuevas -- las que hay ya son buenas, lo que faltaba era el
disparador.

## Como decide que ejecutar

Por patron, no por lista. Una lista de scripts hay que acordarse de ampliarla,
y el dia que a alguien se le olvida el gate nuevo nace ya sin correr:

  * `check_*.py`  de cualquier modulo -- netlist y BOM
  * `*_budget.py` de cualquier sitio  -- los presupuestos ejecutables
  * `simulations/*/*.py`              -- una simulacion existe para validar
  * `netdiff.py`                      -- firma de conectividad y coherencia

Anadir un gate = escribir el fichero con uno de esos nombres. No se toca nada
aqui.

## Huecos: se declaran, no se esconden

Dos scripts no corren en un Python pelado -- `hum_loop.py` necesita `pcbnew` y
`run_sim.py` necesita `ngspice.dll`, y las dos cosas solo existen dentro de la
instalacion de KiCad. Se resuelve en este orden:

  1. si hay un Python de KiCad en la maquina, se usa ESE para ellos;
  2. si no lo hay, el script sale como **HUECO**, con el motivo escrito.

Un hueco no rompe el CI, pero se imprime en el resumen y se cuenta. Es el
Principio V aplicado a la propia herramienta: un fallo invisible es peor que un
hueco visible, y un `skip` silencioso es la forma mas comoda de tener las dos
cosas a la vez -- ni corre, ni te enteras.

Que un script necesita KiCad no se declara a mano: se lee de su codigo. Si
menciona `pcbnew` o `ngspice`, lo necesita.
"""
from __future__ import annotations

import contextlib
import glob
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATRONES = (
    "hardware/**/check_*.py",
    "hardware/**/*_budget.py",
    "case/**/*_budget.py",
    "simulations/*/*.py",
)
EXCLUIR = ("__pycache__", ".venv", os.path.join(".claude", "worktrees"), "site-packages")

# Cuanto se le da a UN guion antes de darlo por colgado.
#
# Estaba en 300 s y se puso rojo el 2026-08-24 con la maquina cargada.
# check_pcb.py de la fuente v3 es el unico que se acerca: 141 s documentados
# con la maquina libre, MEDIDO 226 s con renders y varios servidores KiCad
# corriendo al lado. O sea que el margen real eran 74 s, y se lo come
# cualquier otra cosa que este pasando en la maquina.
#
# Una puerta que se pone roja por carga y no por la placa es peor que no
# tenerla: ensena a empujar con --no-verify. 600 s deja el doble de lo medido
# y sigue cazando un cuelgue de verdad, que es lo que esto va a buscar.
TIMEOUT_S = 600

def _python_kicad() -> str | None:
    """El Python que trae KiCad, o None. `KICAD_PYTHON=none` lo desactiva.

    El desactivador existe para poder probar EN LOCAL la rama que va a correr
    el CI. Sin el, la unica forma de ver el camino "sin KiCad" seria desinstalar
    KiCad o esperar a que el CI falle, que es enterarse tarde.
    """
    env = os.environ.get("KICAD_PYTHON", "")
    if env.lower() in ("none", "0", "off"):
        return None
    if env:
        return env if os.path.exists(env) else None
    candidatos = sorted(glob.glob(r"C:\Program Files\KiCad\*\bin\python.exe"),
                        reverse=True) + ["/usr/lib/kicad/bin/python3"]
    return next((p for p in candidatos if os.path.exists(p)), None)


# Python de KiCad: trae pcbnew y ngspice.dll, que el del sistema no tiene.
PY_KICAD = _python_kicad()


def descubrir() -> list[str]:
    vistos: list[str] = []
    for pat in PATRONES:
        for p in glob.glob(os.path.join(RAIZ, pat), recursive=True):
            # El filtro va contra la ruta RELATIVA a RAIZ, no contra la
            # absoluta. Con la absoluta, correr gates.py DENTRO de un worktree
            # (que es .claude/worktrees/<algo>/) excluia TODAS las puertas: la
            # cadena ".claude\worktrees" esta en la ruta de cada una. Salian 1
            # de 24 y el resumen decia GATES EN VERDE.
            #
            # Es el mismo fallo invisible que el HUECO fabricado y el gate que
            # salia en verde encontrando cosas: no corre Y no te enteras. Y
            # pegaba justo donde mas duele, porque el worktree es el flujo
            # aislado que recomienda el propio repo.
            rel = os.path.relpath(p, RAIZ)
            if any(x in rel for x in EXCLUIR) or p in vistos:
                continue
            vistos.append(p)
    if not vistos:
        raise SystemExit(
            f"FALLO: los patrones no encontraron ni una puerta bajo {RAIZ}.\n"
            "  Eso no es un repositorio sin gates, es el descubridor roto.\n"
            "  Cero puertas NUNCA es verde.")
    netdiff = os.path.join(RAIZ, "hardware", "tools", "netdiff.py")
    return [netdiff] + sorted(vistos, key=lambda p: os.path.relpath(p, RAIZ))


def necesita_kicad(ruta: str) -> str:
    """Devuelve que dependencia de KiCad usa el script, o '' si ninguna."""
    with open(ruta, encoding="utf-8") as fh:
        src = fh.read()
    if "pcbnew" in src:
        return "pcbnew"
    if "ngspice" in src:
        return "ngspice.dll"
    return ""


def corre(ruta: str) -> tuple[str, str, float]:
    """(estado, detalle, segundos). estado in {OK, FALLO, HUECO}."""
    dep = necesita_kicad(ruta)
    interprete = PY_KICAD if (dep and PY_KICAD) else sys.executable
    if dep and not PY_KICAD:
        return "HUECO", f"necesita {dep} (solo existe dentro de KiCad)", 0.0
    t0 = time.time()
    try:
        r = subprocess.run([interprete, os.path.basename(ruta)],
                           cwd=os.path.dirname(ruta), capture_output=True,
                           text=True, timeout=TIMEOUT_S, encoding="utf-8",
                           errors="replace")
    except subprocess.TimeoutExpired:
        return "FALLO", f"timeout a los {TIMEOUT_S} s", time.time() - t0
    dt = time.time() - t0
    salida = (r.stdout or "") + (r.stderr or "")
    ultima = [l for l in salida.strip().splitlines() if l.strip()]
    if r.returncode == 0:
        return "OK", (ultima[-1][:64] if ultima else ""), dt
    if r.returncode == 2:
        # Convencion del repo: 2 = trabajo a medias, no fallo. La estreno
        # build_pcb.py del modulo 2 con las redes sin rutear, y la usa
        # check_bringup.py mientras falten medidas de la placa fisica.
        return "HUECO", (ultima[-1][:64] if ultima else "codigo 2"), dt
    if dep and _dep_ausente(salida, dep):
        return "HUECO", f"necesita {dep}: {salida.strip().splitlines()[-1][:60]}", dt
    return "FALLO", salida.strip(), dt


def _dep_ausente(salida: str, dep: str) -> bool:
    """¿El script murio por FALTA de la dependencia, o por lo que fue a mirar?

    Antes se daba por hecho lo primero: cualquier salida distinta de cero en un
    script que necesitara KiCad se reportaba como HUECO "necesita pcbnew". Eso
    convierte un FALLO REAL en un hueco, y el hueco no rompe el resumen -- asi
    que la tanda se cerraba con "GATES EN VERDE" encima de una placa con
    problemas. Caso: check_pcb.py de la fuente v3 corria 141 s con pcbnew bien
    cargado, encontraba 5 pistas GNDREF fuera de su isla, salia con codigo 1, y
    se reportaba como que no se habia podido comprobar.

    Es el Principio V al reves: la herramienta fabricaba la invisibilidad. Un
    hueco solo es hueco si la dependencia de verdad no esta, y eso lo dice el
    import que revienta, no el codigo de salida.
    """
    modulo = dep.split(".")[0].lower()
    bajo = salida.lower()
    return any(
        marca in bajo and modulo in bajo
        for marca in ("modulenotfounderror", "importerror", "dll load failed",
                      "no module named")
    )


def main() -> int:
    # La salida de los gates se decodifica con errors="replace", asi que puede
    # traer U+FFFD. En una consola cp1252 (la de Windows por defecto) eso hace
    # que el propio runner reviente a media lista y las puertas que quedaban
    # NO se corran -- que es exactamente el fallo invisible del Principio V:
    # el resumen final nunca llega y nadie se entera de que falta la mitad.
    for flujo in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            flujo.reconfigure(encoding="utf-8", errors="replace")

    scripts = descubrir()
    print(f"puertas de calidad del SAM17 -- {len(scripts)} scripts")
    print(f"python del sistema: {sys.version.split()[0]}")
    print(f"python de KiCad:    {PY_KICAD or 'NO ENCONTRADO (habra huecos)'}\n")

    fallos: list[tuple[str, str]] = []
    huecos: list[tuple[str, str]] = []
    for ruta in scripts:
        rel = os.path.relpath(ruta, RAIZ).replace("\\", "/")
        print(f"  {rel:52}", end=" ", flush=True)
        estado, detalle, dt = corre(ruta)
        print(f"{estado:6} {dt:5.1f}s  {detalle.splitlines()[0][:52] if detalle else ''}")
        if estado == "FALLO":
            fallos.append((rel, detalle))
        elif estado == "HUECO":
            huecos.append((rel, detalle))

    print()
    for rel, detalle in fallos:
        print(f"--- FALLO en {rel} " + "-" * max(0, 50 - len(rel)))
        print("\n".join("    " + l for l in detalle.splitlines()[-25:]))
        print()

    ok = len(scripts) - len(fallos) - len(huecos)
    print(f"resumen: {ok} en verde, {len(fallos)} en rojo, {len(huecos)} sin cubrir")
    for rel, motivo in huecos:
        print(f"  HUECO  {rel}: {motivo}")
    if huecos and not PY_KICAD:
        print("  -> en una maquina con KiCad instalado estos SI corren. "
              "En CI no: instalar KiCad entero por dos scripts no compensa, "
              "y el hueco esta declarado aqui a proposito.")
    if fallos:
        print("\nGATES EN ROJO. No se cierra la tanda.")
        return 1
    print("\nGATES EN VERDE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
