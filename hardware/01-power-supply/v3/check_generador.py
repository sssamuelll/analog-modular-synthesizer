"""Puerta: el generador sigue produciendo el cobre que la placa lleva.

    python check_generador.py    # sale != 0 si el guion y la placa discrepan

## Por que existe (#282)

Hasta el #139, `check_pcb.py` llamaba a `rutear(board)` en cada corrida. Era el
problema de rendimiento -- 228,8 s -- pero tambien la unica cosa que ejercitaba
el ruteador dentro de `gates.py`. Al pasar la puerta a leer el cobre
commiteado, que es lo correcto, `rutear()` se quedo sin correr en ninguna
puerta: solo se invoca desde `build_pcb.py`, y a `build_pcb.py` no lo ejecuta
ni `gates.py` ni el gancho de subida.

Lo que dejo de correr solo no era cosmetico. Son las aserciones internas del
generador, cada una con su nombre y apellido:

  * `la placa no tiene pads de GND` -- el filtro de red se rompio
  * `la via de GND de {ref}.{pin} no cabe: ni recta ni girando` -- un fanout
    sin sitio
  * `ni el calibre mas fino cabe en {pad}` -- una escapada imposible
  * `PENDIENTES nombra una red que no existe` -- una red renombrada

## Como se paga sin volver a los tres minutos

El ruteo tiene dos mitades y **el precio esta todo en una**. Medido el
2026-09-02:

    rutear_red + rutear_rieles + escapar_pines_finos + rutear_gnd    0,49 s
    rutear_resto (el laberinto de Lee, 126 conexiones)             ~180 s

Esta puerta corre la primera mitad -- la que se define por su FORMA y no por
su longitud -- y no toca la segunda. Con eso vuelven cuatro de las cinco
aserciones por medio segundo.

Y de paso cierra la otra mitad del criterio del #139, que pedia «comprobar
aparte que coinciden con las que el script genera»: cada tramo y cada via que
el guion produce tiene que estar en el `.kicad_pcb` commiteado. Una pista
arrastrada a mano en la GUI sobre la parte escrita a mano sale aqui.

## Lo que NO cubre, y cuanto costaria

El laberinto. Su aserción -- `el laberinto no cerro` -- no se ejercita, y una
regresion en el BFS de Lee no pone roja ninguna puerta hasta que alguien
regenere. Cubrirla cuesta los ~180 s enteros, que es exactamente lo que el
#139 quito. La comprobacion barata que si queda sobre el laberinto es que su
resultado esta en la placa y `check_pcb.py` lo mide ahi.
"""
from __future__ import annotations

from collections import Counter
import os
import sys
import time

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "kicad"))

try:
    import pcbnew                                        # noqa: F401
except ImportError:
    print("HUECO: necesita el Python de KiCad (pcbnew) para leer la placa")
    raise SystemExit(2) from None

import build_pcb as bp                                   # noqa: E402
import check_pcb as cp                                   # noqa: E402


def normaliza_tramos(tracks):
    """Cada pista, partida en segmentos y con las puntas ordenadas.

    Ordenadas porque una pista de a a b es la misma que de b a a, y partida
    porque el guion emite polilineas y el fichero guarda segmentos sueltos.
    """
    salida: Counter = Counter()
    for net, capa, pts, ancho in tracks:
        for i in range(len(pts) - 1):
            a = tuple(round(v, 4) for v in pts[i])
            b = tuple(round(v, 4) for v in pts[i + 1])
            salida[(net.lstrip("/"), capa, min(a, b), max(a, b),
                    round(ancho, 4))] += 1
    return salida


def normaliza_vias(vias):
    return Counter((round(x, 4), round(y, 4), n.lstrip("/"),
                    round(ancho, 4), round(taladro, 4))
                   for x, y, n, ancho, taladro in vias)


def main() -> int:
    if not os.path.exists(cp.PCB):
        print("HUECO: falta sam17-power-v3.kicad_pcb -- correr build_pcb.py")
        return 2

    board = pcbnew.LoadBoard(cp.PCB)

    # Las cuatro que se definen por su forma. Van en ESTE orden porque el
    # arbol de masa se aparta de lo que ya hay: si corriera primero, sus vias
    # se posarian en el pasillo por el que despues sale un pin de MSOP.
    inicio = time.time()
    try:
        r = bp.Ruteo(board)
        bp.rutear_red(r)
        bp.rutear_rieles(r)
        bp.escapar_pines_finos(r)
        bp.rutear_gnd(r)
    except AssertionError as exc:
        # Esto es lo que la puerta vino a recuperar: una asercion del
        # generador que se rompio. Sale como FALLO con su texto, no como
        # traceback, porque el resumen de gates.py no clasifica un traceback.
        print(f"\nFALLO: el generador se planto -- {exc}")
        return 1
    dt = time.time() - inicio

    tramos_guion = normaliza_tramos(r.tracks)
    vias_guion = normaliza_vias(r.vias)
    print(f"  el guion traza {sum(tramos_guion.values())} tramos y "
          f"{sum(vias_guion.values())} vias en {dt:.2f} s "
          f"(sin el laberinto, que son ~180 s mas)")

    tracks, vias = cp.leer_ruteo(board)
    faltan_t = tramos_guion - normaliza_tramos(tracks)
    faltan_v = vias_guion - normaliza_vias(vias)

    fallos: list[str] = []
    if faltan_t:
        fallos.append(
            f"{sum(faltan_t.values())} tramos que el guion traza y la placa "
            f"commiteada NO tiene. Ejemplo: {sorted(faltan_t)[0]}")
    if faltan_v:
        fallos.append(
            f"{sum(faltan_v.values())} vias que el guion traza y la placa "
            f"commiteada NO tiene. Ejemplo: {sorted(faltan_v)[0]}")

    if fallos:
        print(f"\nFALLO: {len(fallos)} en el generador")
        for f in fallos:
            print(f"  - {f}")
        print("\n  O el guion cambio y nadie regenero la placa, o la placa se "
              "toco a mano.\n  Los dos se arreglan corriendo build_pcb.py y "
              "mirando el diff.")
        return 1

    print("\nOK: las cuatro aserciones del ruteo a mano pasan, y cada tramo y "
          "cada via\n    que el guion traza esta en la placa commiteada.")
    print("    NO cubre el laberinto (rutear_resto): su aserto solo corre al "
          "regenerar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
