"""Ruteador de laberinto sobre rejilla (Lee/BFS) para las PCB del SAM17.

El anterior probaba caminos en L y en Z contra los obstaculos y se quedaba con
el primero que no rozara. Funciona en placas holgadas y se atasco en el modulo
2: con tres quiebros como maximo no hay forma de cruzar un lado congestionado, y
se quedaron 17 redes al aire. Este no adivina caminos, los BUSCA.

Como funciona, en tres frases:

  * La placa se discretiza en una rejilla de PASO mm. Cada celda guarda que red
    la ocupa (0 = libre).
  * Para cada red se hace un BFS desde TODO lo que ya esta conectado de esa red
    hasta el siguiente pad. Es el algoritmo de Lee, que da el camino mas corto
    si existe, y si no existe lo dice — que es la otra mitad del trabajo.
  * Se llama primero con UNA capa. Solo si no hay paso se reintenta con las
    dos. Sale el mismo efecto que penalizar la via — solo se usa cuando hace
    falta — con un BFS pelado en vez de una cola de prioridad. Y nunca se pone
    una via donde no cabe: eso lo decide via_ok().

La parte fina es la HOLGURA. No basta con marcar el cobre: hay que marcar
tambien el aire que necesita alrededor, y ese aire depende del ancho de la
pista que vaya a pasar. Por eso hay un mapa por ANCHO de pista, y cada obstaculo
se dibuja en cada mapa con su propio margen. Marcar todo con el margen del riel
mas gordo bloquearia el TSSOP entero; marcarlo con el de la pista mas fina
dejaria cortos que el DRC canta despues.
"""
from __future__ import annotations

import math
from collections import deque

class Rejilla:
    def __init__(self, ancho_mm: float, alto_mm: float, paso: float,
                 clearance: float, anchos: dict[str, float],
                 n_capas: int = 2) -> None:
        self.paso = paso
        self.cl = clearance
        self.anchos = anchos
        self.nx = int(ancho_mm / paso) + 1
        self.ny = int(alto_mm / paso) + 1
        self.nc = n_capas
        self.n = self.nx * self.ny
        # un mapa por ancho de pista; dentro, una capa por cara
        self.mapa = {k: [bytearray(self.n) for _ in range(n_capas)]
                     for k in anchos}
        self.red_de = {k: [{} for _ in range(n_capas)] for k in anchos}

    # -------------------------------------------------------------- utilidad
    def idx(self, ix: int, iy: int) -> int:
        return iy * self.nx + ix

    def a_celda(self, x: float, y: float) -> tuple[int, int]:
        return (int(round(x / self.paso)), int(round(y / self.paso)))

    def a_mm(self, ix: int, iy: int) -> tuple[float, float]:
        return (round(ix * self.paso, 3), round(iy * self.paso, 3))

    def _pintar(self, red_id, cx0, cy0, cx1, cy1, r, clase, capa):
        """Marca las celdas cuyo CENTRO cae dentro del rectangulo + r mm.

        El centro, no el solape. La primera version redondeaba hacia fuera por
        los dos lados -- `int()` abajo, `+1` arriba -- y con eso una celda
        quedaba bloqueada por estar hasta un paso entero FUERA del margen que
        el obstaculo pide. En una placa holgada no se nota; en el lado este de
        un DFN de 0.45 mm de paso se lo come todo: el pasillo real por el que
        puede ir el eje de una pista de 0.2 mm entre dos pines mide 0.196 mm,
        y el redondeo generoso bloqueaba las dos unicas celdas que caben.

        `r` ya es el margen entero (clearance + medio ancho de quien vaya a
        pasar, mas medio ancho del obstaculo si es una pista), asi que una
        celda cuyo centro esta a mas de `r` del cobre es legal por
        construccion. Redondear hacia dentro no afloja el criterio: lo aplica.

        La guarda del final es para el caso degenerado -- un rectangulo mas
        estrecho que la rejilla y mal alineado no contendria ningun centro, y
        un obstaculo sin pintar es peor que uno pintado de mas.
        """
        m = self.mapa[clase][capa]
        d = self.red_de[clase][capa]
        i0 = max(0, math.ceil((cx0 - r) / self.paso))
        i1 = min(self.nx - 1, math.floor((cx1 + r) / self.paso))
        j0 = max(0, math.ceil((cy0 - r) / self.paso))
        j1 = min(self.ny - 1, math.floor((cy1 + r) / self.paso))
        if i1 < i0 or j1 < j0:
            ix, iy = self.a_celda((cx0 + cx1) / 2, (cy0 + cy1) / 2)
            if 0 <= ix < self.nx and 0 <= iy < self.ny:
                k = iy * self.nx + ix
                d[k] = red_id if (not m[k] or d.get(k) == red_id) else 0
                m[k] = 1
            return
        for j in range(j0, j1 + 1):
            base = j * self.nx
            for i in range(i0, i1 + 1):
                k = base + i
                # Una celda que reclaman DOS redes distintas no es de ninguna.
                # Antes se la quedaba la ultima en pintar, y la otra red la
                # veia como propia y pasaba por ella: dos pistas del mismo
                # ancho compartiendo el aire que cada una creia suyo. Sale
                # como un roce de decimas de mm en el sitio mas apretado --
                # entre dos pines de un MSOP -- y con el BFS en verde, porque
                # para el la celda era legal. `red_id` empieza en 1, asi que
                # el 0 no coincide con nadie y bloquea a las dos.
                d[k] = red_id if (not m[k] or d.get(k) == red_id) else 0
                m[k] = 1

    # ------------------------------------------------------------ obstaculos
    def pad(self, red_id: int, x0: float, y0: float, x1: float, y1: float,
            capas=None) -> None:
        """Un pad pasante ocupa TODAS las capas; uno SMD solo la suya."""
        for clase, w in self.anchos.items():
            for capa in (range(self.nc) if capas is None else capas):
                self._pintar(red_id, x0, y0, x1, y1,
                             self.cl + w / 2, clase, capa)

    def pista(self, red_id: int, a, b, clase_pista: str, capa: int) -> None:
        """Una pista ya puesta: rectangulo por tramo, engordado por los dos
        anchos (el suyo y el de quien vaya a pasar al lado)."""
        wp = self.anchos[clase_pista]
        x0, x1 = min(a[0], b[0]), max(a[0], b[0])
        y0, y1 = min(a[1], b[1]), max(a[1], b[1])
        for clase, w in self.anchos.items():
            self._pintar(red_id, x0, y0, x1, y1,
                         self.cl + w / 2 + wp / 2, clase, capa)

    def via(self, red_id: int, x: float, y: float, diam: float) -> None:
        for capa in range(self.nc):
            for clase, w in self.anchos.items():
                self._pintar(red_id, x - diam / 2, y - diam / 2,
                             x + diam / 2, y + diam / 2,
                             self.cl + w / 2, clase, capa)

    # ---------------------------------------------------------------- buscar
    def libre(self, clase: str, capa: int, k: int, red_id: int) -> bool:
        return (not self.mapa[clase][capa][k]
                or self.red_de[clase][capa].get(k) == red_id)

    def buscar(self, red_id: int, clase: str, origen: set, destino: set,
               via_ok, capas: tuple = (0,)) -> list | None:
        """BFS de un conjunto de celdas a otro. Devuelve [(ix, iy, capa)...].

        Nodos como ENTEROS planos (capa*n + iy*nx + ix) y `prev` como lista, no
        como diccionario de tuplas: sobre 257.000 celdas por capa la version con
        tuplas tardaba segundos por red.

        El coste de la via no se modela con pesos. Se llama dos veces: primero
        con una sola capa, y solo si no hay paso se reintenta con las dos. Sale
        el mismo efecto — vias solo cuando hacen falta — con un BFS pelado en
        vez de una cola de prioridad.
        """
        N, nx, ny = self.n, self.nx, self.ny
        total = N * self.nc
        prev = [-2] * total
        cola = deque()
        for nodo in origen:
            if 0 <= nodo < total and prev[nodo] == -2:
                prev[nodo] = -1
                cola.append(nodo)
        mapas = [self.mapa[clase][c] for c in range(self.nc)]
        redes = [self.red_de[clase][c] for c in range(self.nc)]
        while cola:
            nodo = cola.popleft()
            if nodo in destino:
                cam = []
                while nodo != -1:
                    capa, k = divmod(nodo, N)
                    cam.append((k % nx, k // nx, capa))
                    nodo = prev[nodo]
                return cam[::-1]
            capa, k = divmod(nodo, N)
            ix, iy = k % nx, k // nx
            m, d = mapas[capa], redes[capa]
            for jx, jy, jk in ((ix + 1, iy, k + 1), (ix - 1, iy, k - 1),
                               (ix, iy + 1, k + nx), (ix, iy - 1, k - nx)):
                if not (0 <= jx < nx and 0 <= jy < ny):
                    continue
                sig = capa * N + jk
                if prev[sig] != -2 or (m[jk] and d.get(jk) != red_id):
                    continue
                prev[sig] = nodo
                cola.append(sig)
            for otra in capas:
                if otra == capa:
                    continue
                sig = otra * N + k
                mo, do = mapas[otra], redes[otra]
                if (prev[sig] == -2
                        and not (mo[k] and do.get(k) != red_id)
                        and via_ok(self.a_mm(ix, iy))):
                    prev[sig] = nodo
                    cola.append(sig)
        return None

    def nodo(self, x: float, y: float, capa: int) -> int:
        ix, iy = self.a_celda(x, y)
        return capa * self.n + iy * self.nx + ix

    def celdas_rect(self, x0, y0, x1, y1, capa) -> set:
        """Nodos planos ESTRICTAMENTE dentro de un rectangulo.

        El BFS arranca de todas las celdas del pad y no de su centro, para que
        pueda salir por donde quiera. Pero tienen que estar DENTRO: la primera
        version redondeaba hacia fuera y anadia una celda de mas por cada lado,
        con lo que las pistas nacian y morian hasta un paso de rejilla fuera del
        cobre. KiCad las daba por desconectadas — 126 elementos sueltos con la
        placa practicamente ruteada — y el fallo no se veia en el dibujo porque
        0.25 mm no se aprecian.

        Si el pad es mas pequeño que la rejilla no queda ninguna celda dentro;
        en ese caso se devuelve la del centro, que es lo unico razonable.
        """
        out = set()
        i0 = max(0, math.ceil(x0 / self.paso))
        i1 = min(self.nx - 1, math.floor(x1 / self.paso))
        j0 = max(0, math.ceil(y0 / self.paso))
        j1 = min(self.ny - 1, math.floor(y1 / self.paso))
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                out.add(capa * self.n + j * self.nx + i)
        if not out:
            ix, iy = self.a_celda((x0 + x1) / 2, (y0 + y1) / 2)
            out.add(capa * self.n + iy * self.nx + ix)
        return out


def comprimir(camino: list) -> list:
    """De una lista de celdas a tramos rectos: quita los puntos intermedios de
    cada recta. Una pista de 40 celdas no son 40 segmentos, es uno."""
    if not camino:
        return []
    salida = [camino[0]]
    for i in range(1, len(camino) - 1):
        ax, ay, ac = camino[i - 1]
        bx, by, bc = camino[i]
        cx, cy, cc = camino[i + 1]
        recto = (ac == bc == cc
                 and (bx - ax, by - ay) == (cx - bx, cy - by))
        if not recto:
            salida.append(camino[i])
    salida.append(camino[-1])
    return salida


def demo() -> None:
    """Autocomprobacion: un pasillo con una pared y un hueco."""
    r = Rejilla(20.0, 10.0, 0.25, 0.2, {"f": 0.25}, n_capas=1)
    # pared vertical en x=10 con un hueco en y=8..10
    r.pad(99, 9.9, 0.0, 10.1, 7.5)
    a = {r.nodo(2.0, 5.0, 0)}
    b = {r.nodo(18.0, 5.0, 0)}
    cam = r.buscar(1, "f", a, b, lambda p: False)
    assert cam, "deberia encontrar camino rodeando la pared por abajo"
    ys = [c[1] for c in cam]
    assert max(ys) * 0.25 > 7.5, "el camino tiene que bajar a buscar el hueco"
    print(f"OK: rodea la pared, {len(cam)} celdas, "
          f"{len(comprimir(cam))} tramos tras comprimir")

    # y ahora sin hueco: tiene que decir que NO, no inventarse nada
    r2 = Rejilla(20.0, 10.0, 0.25, 0.2, {"f": 0.25}, n_capas=1)
    r2.pad(99, 9.9, -1.0, 10.1, 11.0)
    a2 = {r2.nodo(2.0, 5.0, 0)}
    b2 = {r2.nodo(18.0, 5.0, 0)}
    assert r2.buscar(1, "f", a2, b2, lambda p: False) is None, \
        "sin hueco no puede haber camino"
    print("OK: cuando no hay paso, lo dice")


if __name__ == "__main__":
    demo()
