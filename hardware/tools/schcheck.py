"""Detector de redes fusionadas por accidente en una hoja generada.

Existe porque esta clase de fallo ya ha salido DOS veces en este repo y las dos
se coló hasta el ERC:

  * bus board: la bajada de masa del peine terminaba justo encima del ramal de
    +12S, y KiCad une un extremo de cable que aterriza en mitad de otro cable.
  * modulo 2: los rabitos de dos resistencias de pull-up contiguas se solapaban
    porque el paso entre filas era menor que el largo del componente con sus
    rabitos. Resultado: los cuatro botones colgados de +3V3.

Las dos veces el trazado "se veia bien" y el ERC lo canto DESPUES de escribir el
fichero. Esto lo caza ANTES, y con un mensaje que dice que dos redes se han
juntado, no que hay un aviso en unas coordenadas.

El metodo: se reconstruye la conectividad como la ve KiCad — extremos que
coinciden, extremos que caen sobre otro segmento, y segmentos colineales que se
pisan — y se exige que cada grupo resultante tenga UN solo nombre de red.
"""
from __future__ import annotations

TOL = 1e-6


def _busca(padre: dict, a):
    padre.setdefault(a, a)
    while padre[a] != a:
        padre[a] = padre[padre[a]]
        a = padre[a]
    return a


def _une(padre: dict, a, b) -> None:
    ra, rb = _busca(padre, a), _busca(padre, b)
    if ra != rb:
        padre[ra] = rb


def _en_segmento(p, s) -> bool:
    """El punto p cae sobre el segmento s (extremos incluidos)."""
    (ax, ay, bx, by), (px, py) = s, p
    cruz = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if abs(cruz) > 1e-6:
        return False
    punto = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    largo = (bx - ax) ** 2 + (by - ay) ** 2
    return -TOL <= punto <= largo + TOL


def redes_fusionadas(wires: list, etiquetas: list,
                     potencias: list) -> list[str]:
    """wires: [(x1,y1,x2,y2)]; etiquetas y potencias: [(nombre, x, y)].

    Devuelve una lista de descripciones de grupos con mas de un nombre. Vacia
    si todo esta bien.
    """
    padre: dict = {}
    for x1, y1, x2, y2 in wires:
        _une(padre, (x1, y1), (x2, y2))
    # extremos que caen sobre otro segmento (T) y solapes colineales
    puntos = {p for w in wires for p in ((w[0], w[1]), (w[2], w[3]))}
    for s in wires:
        for p in puntos:
            if p in ((s[0], s[1]), (s[2], s[3])):
                continue
            if _en_segmento(p, s):
                _une(padre, p, (s[0], s[1]))
    # un nombre puede estar anclado en cualquier punto de la maraña
    grupos: dict = {}
    for nombre, x, y in list(etiquetas) + list(potencias):
        ancla = None
        if (x, y) in padre:
            ancla = _busca(padre, (x, y))
        else:
            for s in wires:
                if _en_segmento((x, y), s):
                    ancla = _busca(padre, (s[0], s[1]))
                    break
        if ancla is None:
            continue
        grupos.setdefault(ancla, set()).add(nombre)
    return [f"{sorted(n)} han quedado en la MISMA red"
            for n in grupos.values() if len(n) > 1]
