"""Mide el lazo de carga del rectificador del modulo 1 sobre la placa RUTEADA.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" hum_loop.py

Por que este numero y no la orientacion del transformador: en una fuente lineal
el que mas radia casi nunca es el nucleo, es **el lazo de carga del
rectificador**. Por ahi no circula la corriente continua, circulan picos
estrechos de 2-3 veces la continua a 100 Hz con flancos de microsegundos. Y lo
que se acopla a un lazo vecino no va con I, va con dI/dt.

El toroide ya estaba elegido y la caja aun no existe; el lazo, en cambio, ya
esta decidido en cobre y se puede medir hoy. Si sale grande, no hay orientacion
de transformador que lo arregle.

Modelo del acoplo, para saber que se esta midiendo:

  El lazo emisor es un dipolo magnetico m = I * A. El campo a distancia r cae
  como 1/r^3, y la tension que induce en un lazo victima de area Av vale

      V = (mu0 / 4pi) * (2 * Av / r^3) * dI/dt        (victima en el eje)

  Todo lo que se puede hacer esta en esa formula: bajar A (esta placa), bajar
  Av (la placa victima), o subir r (la caja). Solo la primera esta cerrada.
"""
from __future__ import annotations

import os
import sys

import pcbnew

MU0 = 4e-7 * 3.141592653589793
PCB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "hardware", "01-power-supply", "kicad",
                   "sam17-power.kicad_pcb")

# El lazo positivo se cierra por estas piezas: del centro del secundario (J1)
# al puente, del puente al bulk positivo, y del bulk de vuelta a la estrella.
GRUPO = {"J1", "BR1", "C1", "C12"}
# Los nombres de red de etiqueta local llevan "/" delante en el fichero; los
# de simbolo de potencia no. Se normaliza en vez de escribirlos a mano.
REDES = {"VRAW+", "GND", "SEC_A", "SEC_B"}


def red(x) -> str:
    return x.GetNetname().lstrip("/")

I_PICO = 2.5        # A. ~2.6x la continua de 950 mA: en entrada capacitiva la
                    # corriente va en picos estrechos, no repartida.
T_FLANCO = 20e-6    # s. Flanco del pico de carga. Estimacion; es el parametro
                    # mas flojo de todo esto y por eso se da el barrido.


def main() -> None:
    board = pcbnew.LoadBoard(os.path.abspath(PCB))
    pads = [(f"{fp.GetReference()}.{p.GetNumber()}",
             p.GetX() / 1e6, p.GetY() / 1e6)
            for fp in board.GetFootprints() if fp.GetReference() in GRUPO
            for p in fp.Pads() if red(p) in REDES]
    assert pads, "no se encontro el grupo del rectificador"

    xs = [p[1] for p in pads]
    ys = [p[2] for p in pads]
    ancho, alto = max(xs) - min(xs), max(ys) - min(ys)
    area_mm2 = ancho * alto
    print(f"grupo rectificador: {len(pads)} pads de {sorted(GRUPO)}")
    print(f"  caja envolvente {ancho:.1f} x {alto:.1f} mm "
          f"-> COTA SUPERIOR del lazo = {area_mm2/100:.2f} cm2")

    # la cota es generosa: el lazo real es mas estrecho porque VRAW+ y el
    # retorno de masa van casi pegados. Se mide la separacion real entre el
    # conductor de ida y el de vuelta a lo largo del recorrido.
    ida = [(t.GetStart().x/1e6, t.GetStart().y/1e6,
            t.GetEnd().x/1e6, t.GetEnd().y/1e6)
           for t in board.GetTracks() if red(t) == "VRAW+"]
    vuelta = [(t.GetStart().x/1e6, t.GetStart().y/1e6,
               t.GetEnd().x/1e6, t.GetEnd().y/1e6)
              for t in board.GetTracks() if red(t) == "GND"]
    assert ida and vuelta, "sin pistas de VRAW+ o de GND"

    def dist(px, py, s):
        ax, ay, bx, by = s
        dx, dy = bx - ax, by - ay
        L = dx*dx + dy*dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy)/L))
        return ((px - (ax+t*dx))**2 + (py - (ay+t*dy))**2) ** 0.5

    sep = []
    for ax, ay, bx, by in ida:
        if min(ay, by) > 70:          # solo el tramo puente->bulk, no las
            continue                  # bajadas largas a los reguladores
        for f in (0.0, 0.5, 1.0):
            px, py = ax + f*(bx-ax), ay + f*(by-ay)
            sep.append(min(dist(px, py, s) for s in vuelta))
    sep_media = sum(sep) / len(sep)
    print(f"  separacion media VRAW+ <-> retorno de masa: {sep_media:.1f} mm")

    # AQUI habia un estimador "largo de la ida x separacion media" que daba
    # 7.82 cm2 — MAS que su propia caja envolvente de 6.81, que es imposible
    # para un lazo cerrado. Contaba los 157 mm enteros de VRAW+, incluidas las
    # bajadas a los reguladores y a TP1, que no forman parte del lazo de carga.
    # Se queda la caja envolvente, que es una cota superior de verdad, y la
    # separacion medida vale como evidencia de que el lazo real es mas estrecho
    # que la cota. Mejor un numero conservador que uno halagador y falso.
    area_real = area_mm2

    print(f"\ntension inducida en un lazo victima de 10 cm2 "
          f"(I_pico {I_PICO} A, flanco {T_FLANCO*1e6:.0f} us):")
    av = 10e-4
    for r_mm in (50, 100, 150, 200, 300):
        r = r_mm / 1000.0
        m_punto = area_real * 1e-6 * (I_PICO / T_FLANCO)      # A*m2/s
        v = MU0 / (4*3.141592653589793) * 2 * av * m_punto / r**3
        print(f"  a {r_mm:3d} mm: {v*1e6:8.1f} uV")

    # -100 dBu = 7.75 uV es un suelo razonable para una senal de linea
    r = 0.15
    m_punto = area_real * 1e-6 * (I_PICO / T_FLANCO)
    v150 = MU0 / (4*3.141592653589793) * 2 * av * m_punto / r**3
    print(f"\nreferencia: -100 dBu = 7.75 uV")
    assert area_real < 10.0 * 100, \
        f"el lazo del rectificador se fue a {area_real/100:.1f} cm2"
    print(f"OK: cota del lazo por debajo de 10 cm2. A 150 mm quedan {v150*1e6:.1f} uV, "
          f"que es {'holgado' if v150*1e6 < 7.75 else 'JUSTO O PEOR'}.")
    print("El numero NO cierra el asunto: T_FLANCO es una estimacion y el "
          "campo del propio toroide no entra aqui. Hay que medirlo en la caja.")


if __name__ == "__main__":
    sys.exit(main())
