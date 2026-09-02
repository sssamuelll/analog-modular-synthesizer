"""Mide el lazo de carga del rectificador de la fuente v3 sobre el cobre RUTEADO.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" hum_loop.py

Por que este numero y no la orientacion del transformador: en una fuente lineal
el que mas radia casi nunca es el nucleo, es **el lazo de carga del
rectificador**. Por ahi no circula la corriente continua, circulan picos
estrechos de 2-3 veces la continua a 100 Hz con flancos de microsegundos. Y lo
que se acopla a un lazo vecino no va con I, va con dI/dt.

El toroide ya estaba elegido y la caja aun no existe; el lazo, en cambio, ya
esta decidido en cobre y se puede medir hoy. Si sale grande, no hay orientacion
de transformador que lo arregle (design-notes sec.18.1).

Modelo del acoplo, para saber que se esta midiendo:

  El lazo emisor es un dipolo magnetico m = I * A. El campo a distancia r cae
  como 1/r^3, y la tension que induce en un lazo victima de area Av vale

      V = (mu0 / 4pi) * (2 * Av / r^3) * A * dI/dt      (victima en el eje)

  Todo lo que se puede hacer esta en esa formula: bajar A (esta placa), bajar
  Av (la placa victima), o subir r (la caja). Solo la primera esta cerrada.

## Que cambio el 2026-09-02, y por que importa (#280)

Este guion media la **v1**, que no se construye. Apuntado a la v3 con el mismo
metodo de caja envolvente salio 15,16 cm2 contra los 6,81 de la v1.

Pero la caja envolvente no era el problema: era el metodo. Al **trazar el
cobre** -- seguir el camino electrico de verdad en vez de encerrarlo en un
rectangulo -- el lazo de la v3 daba **57,49 cm2**. La vuelta de masa desde el
bulk hasta la toma central del secundario se iba 379 mm: bajaba a la costilla
de y=99, cruzaba la placa entera hasta el tronco en x=11, subia, y volvia por
la costilla de y=66 hasta J1.2.

Una caja envolvente NO habria visto eso nunca. Un rectangulo alrededor de
cuatro piezas juntas mide lo mismo se vaya el retorno por donde se vaya. Lo que
acopla es el area que ENCIERRA el camino, y esa depende enteramente de por
donde vuelve la corriente. Por eso este guion ya no mide cajas: traza.

Para comparar con la misma vara, la v1 trazada da 3,90 cm2 (C1) y 1,02 cm2
(C12), con vueltas de 60 y 102 mm. La v1 tenia el punto de estrella EN el bulk
(design-notes sec.14.5) y por eso su lazo era corto.
"""
from __future__ import annotations

from collections import deque
import math
import os
import sys

import pcbnew

RAIZ = os.path.dirname(os.path.abspath(__file__))
KICAD_V3 = os.path.abspath(os.path.join(
    RAIZ, "..", "..", "hardware", "01-power-supply", "v3", "kicad"))
sys.path.insert(0, KICAD_V3)

# El grafo del cobre se toma prestado del generador en vez de reescribirlo.
# Tener dos versiones de "que esta unido con que" es como se pierde un lazo: la
# de build_pcb.py es la que las puertas ejercitan con sus canarios de mutacion.
import build_pcb as bp                                   # noqa: E402

MU0 = 4e-7 * math.pi
PCB = os.path.join(KICAD_V3, "sam17-power-v3.kicad_pcb")

I_PICO = 2.5         # A. ~2.6x la continua de 950 mA: en entrada capacitiva la
                     # corriente va en picos estrechos, no repartida.
T_FLANCO = 20e-6     # s. Flanco del pico de carga. Estimacion; es el parametro
                     # mas flojo de todo esto y por eso se da el barrido.
AV_VICTIMA = 10e-4   # m2. Lazo victima supuesto de un modulo (sec.18.6 punto 2).
R_REFERENCIA = 0.15  # m. La distancia de trabajo de sec.18.5.
REF_V = 7.75e-6      # -100 dBu, suelo razonable para una senal de linea.

# El lazo positivo se cierra por estas piezas: de la toma central del secundario
# al puente, del puente al bulk, y del bulk de vuelta a la toma central.
J1_SEC_A, J1_GND = ("J1", "1"), ("J1", "2")
BR1_VRAW, BR1_SEC_A = ("BR1", "1"), ("BR1", "3")
BULKS = (("C1", "1", "2"), ("C12", "1", "2"))


def pad_xy(board, ref: str, pin: str):
    for fp in board.GetFootprints():
        if fp.GetReference() != ref:
            continue
        for p in fp.Pads():
            if p.GetNumber() == pin:
                c = p.GetPosition()
                return (c.x / 1e6, c.y / 1e6)
    raise AssertionError(f"no existe el pad {ref}.{pin}")


def leer_cobre(board):
    tracks, vias = [], []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            vias.append((p.x / 1e6, p.y / 1e6, t.GetNetname(),
                         t.Padstack().Size(pcbnew.F_Cu).x / 1e6,
                         t.GetDrillValue() / 1e6))
            continue
        if isinstance(t, pcbnew.PCB_ARC):
            raise AssertionError("hay un arco de cobre y este guion no lo traza")
        a, b = t.GetStart(), t.GetEnd()
        tracks.append((t.GetNetname(), board.GetLayerName(t.GetLayer()),
                       [(a.x / 1e6, a.y / 1e6), (b.x / 1e6, b.y / 1e6)],
                       t.GetWidth() / 1e6))
    return tracks, vias


def adyacencia(board, tracks, vias, red: str):
    """El grafo de una red, con las vias Y LOS PADS PASANTES como aristas.

    El esqueleto es el mismo grafo_gnd() del arbol de masa, que no tiene nada
    de especifico de GND: parte los tramos en sus cruces y en sus vias, y
    agrupa los nodos con una micra de tolerancia.

    Lo que hay que anadirle aqui son los PADS PASANTES. La regla del arbol se
    puede permitir ignorarlos -- lo declara -- porque solo le interesa si el
    cobre ruteado cierra un lazo. A un trazador de corriente no: en esta placa
    el camino de VRAW+ del puente al bulk de C1 CAMBIA DE CAPA por el pad
    pasante de C12, sin ninguna via de por medio. Sin esta parte el camino no
    existe y el lazo no se puede medir.
    """
    _aristas, _cierres, tramos = bp.grafo_gnd(tracks, vias, red)
    ady: dict = {}

    def une(u, v):
        ady.setdefault(u, []).append(v)
        ady.setdefault(v, []).append(u)

    for _idx, capa, nodos, _ancho in tramos:
        for p, q in zip(nodos, nodos[1:]):
            une((*p, capa), (*q, capa))

    def puentea(x, y):
        arriba = next((n for n in ady if n[2] == "F.Cu"
                       and abs(n[0] - x) <= 0.05 and abs(n[1] - y) <= 0.05),
                      None)
        abajo = next((n for n in ady if n[2] == "B.Cu"
                      and abs(n[0] - x) <= 0.05 and abs(n[1] - y) <= 0.05),
                     None)
        if arriba and abajo:
            une(arriba, abajo)

    for vx, vy, vnet, _a, _t in vias:
        if vnet.lstrip("/") == red:
            puentea(vx, vy)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if (p.GetNetname().lstrip("/") == red
                    and p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD):
                c = p.GetPosition()
                puentea(c.x / 1e6, c.y / 1e6)
    return ady


def camino(ady, desde, hasta, red: str):
    """El recorrido de cobre entre dos puntos, el mas corto en numero de saltos."""
    def nodo(p):
        cerca = [n for n in ady
                 if abs(n[0] - p[0]) <= 0.05 and abs(n[1] - p[1]) <= 0.05]
        if not cerca:
            raise AssertionError(
                f"{red}: el punto ({p[0]:.2f}, {p[1]:.2f}) no toca cobre de "
                "esta red, asi que el lazo no se puede trazar")
        return cerca[0]

    a, b = nodo(desde), nodo(hasta)
    previo, cola = {a: None}, deque([a])
    while cola:
        n = cola.popleft()
        if n == b:
            break
        for m in ady[n]:
            if m not in previo:
                previo[m] = n
                cola.append(m)
    if b not in previo:
        raise AssertionError(
            f"{red}: no hay cobre entre ({desde[0]:.2f}, {desde[1]:.2f}) y "
            f"({hasta[0]:.2f}, {hasta[1]:.2f})")
    salida, n = [], b
    while n is not None:
        salida.append((n[0], n[1]))
        n = previo[n]
    return salida[::-1]


def largo(recorrido) -> float:
    return sum(math.dist(recorrido[i], recorrido[i + 1])
               for i in range(len(recorrido) - 1))


def area_encerrada(poligono) -> float:
    """Area NETA del poligono, en mm2 (formula del cordon de zapato).

    Neta y no sumada por tramos: lo que acopla es el flujo, y un camino que va
    y vuelve sobre si mismo no encierra flujo aunque gaste cobre. Firmar el
    area es lo que distingue un rodeo inutil de una espira de verdad.
    """
    n = len(poligono)
    s = sum(poligono[i][0] * poligono[(i + 1) % n][1]
            - poligono[(i + 1) % n][0] * poligono[i][1]
            for i in range(n))
    return abs(s) / 2.0


def inducido(area_mm2: float, r_m: float) -> float:
    m_punto = area_mm2 * 1e-6 * (I_PICO / T_FLANCO)      # A*m2/s
    return MU0 / (4 * math.pi) * 2 * AV_VICTIMA * m_punto / r_m ** 3


def area_maxima_mm2() -> float:
    """El area de emisor que agota la referencia a la distancia de trabajo.

    No es un numero elegido a ojo: sale de despejar A en la formula del dipolo
    con la victima, la distancia y el suelo de -100 dBu que sec.18.2 ya usaba.
    Da 10,5 cm2, que es de donde venia el tope de 10 escrito a mano.
    """
    k = MU0 / (4 * math.pi) * 2 * AV_VICTIMA * (I_PICO / T_FLANCO) * 1e-6
    return REF_V * R_REFERENCIA ** 3 / k


def medir(board):
    """(peor area en mm2, nombre del bulk, detalle por bulk)."""
    tracks, vias = leer_cobre(board)
    redes = {r: adyacencia(board, tracks, vias, r)
             for r in ("VRAW+", "GND", "SEC_A")}
    j1_sec = pad_xy(board, *J1_SEC_A)
    j1_gnd = pad_xy(board, *J1_GND)
    br_vraw = pad_xy(board, *BR1_VRAW)
    br_sec = pad_xy(board, *BR1_SEC_A)

    detalle = []
    for ref, pin_mas, pin_menos in BULKS:
        mas = pad_xy(board, ref, pin_mas)
        menos = pad_xy(board, ref, pin_menos)
        ida_sec = camino(redes["SEC_A"], j1_sec, br_sec, "SEC_A")
        ida_vraw = camino(redes["VRAW+"], br_vraw, mas, "VRAW+")
        vuelta = camino(redes["GND"], menos, j1_gnd, "GND")
        # El poligono cierra solo: de J1.2 a J1.1 se va por dentro del bornero.
        poligono = ida_sec + [br_vraw] + ida_vraw + [menos] + vuelta
        detalle.append((ref, area_encerrada(poligono),
                        largo(ida_sec), largo(ida_vraw), largo(vuelta)))
    peor = max(detalle, key=lambda d: d[1])
    return peor[1], peor[0], detalle


def main() -> int:
    board = pcbnew.LoadBoard(PCB)
    tope = area_maxima_mm2()
    peor, quien, detalle = medir(board)

    print("lazo de carga del rectificador, TRAZADO sobre el cobre de la v3")
    print(f"  tope derivado del modelo: {tope / 100:.2f} cm2")
    print(f"  (el area de emisor que pone {REF_V * 1e6:.2f} uV en un lazo "
          f"victima de {AV_VICTIMA * 1e4:.0f} cm2 a "
          f"{R_REFERENCIA * 1000:.0f} mm)")

    for ref, area, l_sec, l_vraw, l_gnd in detalle:
        print(f"\n  lazo por {ref}: {area:.0f} mm2 = {area / 100:.2f} cm2")
        print(f"     ida    SEC_A {l_sec:5.0f} mm + VRAW+ {l_vraw:5.0f} mm")
        print(f"     vuelta GND   {l_gnd:5.0f} mm")
        print(f"     inducido a {R_REFERENCIA * 1000:.0f} mm: "
              f"{inducido(area, R_REFERENCIA) * 1e6:.2f} uV")

    print(f"\nel que manda es {quien}: {peor / 100:.2f} cm2")
    print(f"barrido de distancia (I_pico {I_PICO} A, flanco "
          f"{T_FLANCO * 1e6:.0f} us, victima {AV_VICTIMA * 1e4:.0f} cm2):")
    for r_mm in (50, 100, 150, 200, 300):
        print(f"  a {r_mm:3d} mm: {inducido(peor, r_mm / 1000) * 1e6:8.2f} uV")
    print(f"\nreferencia: -100 dBu = {REF_V * 1e6:.2f} uV")

    if peor > tope:
        print(f"\nFALLO: el lazo mide {peor / 100:.2f} cm2 y el tope del "
              f"modelo son {tope / 100:.2f} cm2.")
        print("  El area ES el emisor: a esa distancia no hay orientacion de "
              "transformador que lo arregle (sec.18.1).")
        return 1

    print(f"\nOK: {peor / 100:.2f} cm2 por debajo del tope de "
          f"{tope / 100:.2f} cm2. A {R_REFERENCIA * 1000:.0f} mm quedan "
          f"{inducido(peor, R_REFERENCIA) * 1e6:.2f} uV.")
    print("El numero NO cierra el asunto: T_FLANCO es una estimacion y el "
          "campo del propio toroide no entra aqui (sec.18.6). Hay que medirlo "
          "en la caja.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
