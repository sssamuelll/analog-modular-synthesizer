"""Rescate: cierra con un A* propio las pocas conexiones que Freerouting deja abiertas.

Lo llama build_pcb.py despues de las rondas de Freerouting y antes de verter
las masas exteriores. No es un ruteador de placa: es un buscador de camino
para UNA conexion cada vez, sobre una rejilla de 0.05 mm alrededor de los dos
extremos, en F.Cu, In2.Cu y B.Cu (In1 es plano y no se toca), con vias.

Las conexiones que deja Freerouting son las que su modelo da por hechas o
imposibles y KiCad no: un grupo de pads unidos entre si a 3 mm del cobre
fijo de su red, un pin de paso fino que la pista ancha no podia tocar. El
juez es el DRC de KiCad: build_pcb.py le pide a kicad-cli la lista de
conexiones abiertas (con las zonas rellenas), y cada pista que pone este
modulo guarda la holgura del DRC, mas SEGURIDAD, contra todo lo que no es de
su red -- pads, pistas, vias, zonas prohibidas y el canto.
"""
from __future__ import annotations

import heapq
import math

import pcbnew

G = 0.05                                  # mm por celda: un pin de 0.45 mm de paso
                                          # tiene 0.2 mm reales de aire, y con 0.1 no cabia
CAPAS = (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
COSTE_VIA = 80                            # en celdas: una via "vale" 4 mm de pista
MARGEN_CAJA = 8.0                         # mm alrededor de los dos extremos
# Una pista entre dos centros de celda libres puede pasar hasta media celda
# (en diagonal, G/sqrt(2) = 0.035 mm) mas cerca de un obstaculo que los centros.
SEGURIDAD = 0.04                          # mm de mas sobre la holgura del DRC
MAX_EXPANSIONES = 3_000_000


def _seg_dist(px, py, ax, ay, bx, by) -> float:
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


class _Obstaculo:
    """Cobre de otra red (o zona prohibida): distancia a su borde y sus capas."""

    def __init__(self, tipo, datos, capas, red, taladro=0.0):
        self.tipo, self.datos, self.capas, self.red, self.taladro = tipo, datos, capas, red, taladro
        self.caja = self._caja()

    def _caja(self):
        if self.tipo == "seg":
            (ax, ay), (bx, by), r = self.datos
            return min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r
        if self.tipo == "circ":
            (x, y), r = self.datos
            return x - r, y - r, x + r, y + r
        if self.tipo == "rect":
            (x, y), w, h, _ang = self.datos
            r = math.hypot(w, h) / 2
            return x - r, y - r, x + r, y + r
        return self.datos

    def dist(self, x, y) -> float:
        if self.tipo == "seg":
            (ax, ay), (bx, by), r = self.datos
            return max(0.0, _seg_dist(x, y, ax, ay, bx, by) - r)
        if self.tipo == "circ":
            (cx, cy), r = self.datos
            return max(0.0, math.hypot(x - cx, y - cy) - r)
        if self.tipo == "rect":
            (cx, cy), w, h, ang = self.datos
            dx, dy = x - cx, y - cy
            lx = dx * math.cos(ang) - dy * math.sin(ang)
            ly = dx * math.sin(ang) + dy * math.cos(ang)
            return math.hypot(max(0.0, abs(lx) - w / 2), max(0.0, abs(ly) - h / 2))
        x0, y0, x1, y1 = self.datos
        return math.hypot(max(0.0, x0 - x, x - x1), max(0.0, y0 - y, y - y1))


def obstaculos(board) -> list[_Obstaculo]:
    out = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not (p.GetNumber() or p.GetDrillSizeX() > 0):
                continue                        # aperturas de pasta sin cobre
            x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            s = p.GetSize(pcbnew.F_Cu)
            capas = (pcbnew.F_Cu,) if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD else CAPAS
            taladro = p.GetDrillSizeX() / 2e6
            if p.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
                out.append(_Obstaculo("circ", ((x, y), s.x / 2e6), capas, p.GetNetname(), taladro))
            else:
                out.append(_Obstaculo("rect", ((x, y), s.x / 1e6, s.y / 1e6,
                                               math.radians(p.GetOrientationDegrees())),
                                      capas, p.GetNetname(), taladro))
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            x, y = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
            out.append(_Obstaculo("circ", ((x, y), t.GetFrontWidth() / 2e6), CAPAS, t.GetNetname(),
                                  t.GetDrillValue() / 2e6))
        else:
            out.append(_Obstaculo("seg", ((t.GetStart().x / 1e6, t.GetStart().y / 1e6),
                                          (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6), t.GetWidth() / 2e6),
                                  (t.GetLayer(),), t.GetNetname()))
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
            bb = z.Outline().BBox()
            capas = tuple(c for c in CAPAS if z.GetLayerSet().Contains(c))
            out.append(_Obstaculo("caja", (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                                           bb.GetRight() / 1e6, bb.GetBottom() / 1e6), capas, "<prohibida>"))
    return out


class _Rejilla:
    def __init__(self, caja, obst, red, ancho, holgura, via_d, via_drill, borde, origen):
        # la rejilla se alinea con `origen` (el pad mas fino): asi la pista sale por el
        # eje del pin y no media celda desplazada hacia un vecino
        x0, y0, x1, y1 = caja
        self.x0 = origen[0] - math.ceil((origen[0] - x0) / G) * G
        self.y0 = origen[1] - math.ceil((origen[1] - y0) / G) * G
        self.nx = int((x1 - self.x0) / G) + 1
        self.ny = int((y1 - self.y0) / G) + 1
        n = self.nx * self.ny
        self.bloq = {c: bytearray(n) for c in CAPAS}
        self.sin_via = bytearray(n)
        W, H, m = borde
        for j in range(self.ny):
            for i in range(self.nx):
                x, y = self.x0 + i * G, self.y0 + j * G
                if min(x, y, W - x, H - y) < m + max(ancho, via_d) / 2:
                    k = j * self.nx + i
                    for c in CAPAS:
                        self.bloq[c][k] = 1
                    self.sin_via[k] = 1
        r_pista = holgura + ancho / 2 + SEGURIDAD
        r_via = holgura + via_d / 2 + SEGURIDAD
        for o in obst:
            ajena = o.red != red
            # una via nunca encima de un pad, ni de su propia red
            r_via_propia = 0.1 + via_d / 2 if o.tipo in ("rect", "circ") else 0.0
            # y su taladro lejos de cualquier otro (la broca no lee el netlist)
            r_taladro = (o.taladro + via_drill / 2 + 0.25 + SEGURIDAD) if o.taladro > 0 else 0.0
            r_max = max(r_pista if ajena else 0.0, r_via if ajena else r_via_propia, r_taladro)
            if r_max <= 0:
                continue
            a0, b0, a1, b1 = o.caja
            i0, j0 = max(0, int((a0 - r_max - self.x0) / G)), max(0, int((b0 - r_max - self.y0) / G))
            i1 = min(self.nx - 1, int((a1 + r_max - self.x0) / G) + 1)
            j1 = min(self.ny - 1, int((b1 + r_max - self.y0) / G) + 1)
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    x, y = self.x0 + i * G, self.y0 + j * G
                    d = o.dist(x, y)
                    k = j * self.nx + i
                    if ajena and d < r_pista:
                        for c in o.capas:
                            self.bloq[c][k] = 1
                    if (ajena and d < r_via) or (not ajena and d < r_via_propia):
                        self.sin_via[k] = 1
                    if r_taladro and math.hypot(x - o.datos[0][0], y - o.datos[0][1]) < r_taladro:
                        self.sin_via[k] = 1

    def celda(self, x, y):
        return int(round((x - self.x0) / G)), int(round((y - self.y0) / G))

    def punto(self, i, j):
        return self.x0 + i * G, self.y0 + j * G

    def libre(self, i, j, c) -> bool:
        return 0 <= i < self.nx and 0 <= j < self.ny and not self.bloq[c][j * self.nx + i]


def _a_estrella(rej: _Rejilla, inicio: list, meta: list):
    """inicio/meta: [(i, j, capa)]. Devuelve la lista de estados del camino, o None."""
    metas = set(meta)
    mi = sorted({(i, j) for i, j, _c in meta})

    def h(i, j):
        return min(max(abs(i - a), abs(j - b)) + 0.414 * min(abs(i - a), abs(j - b)) for a, b in mi)

    abiertos, g, padre = [], {}, {}
    for s in inicio:
        g[s] = 0.0
        heapq.heappush(abiertos, (h(s[0], s[1]), 0.0, s))
    pasos = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
             (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    n = 0
    while abiertos and n < MAX_EXPANSIONES:
        _f, gs, s = heapq.heappop(abiertos)
        if gs > g.get(s, 1e18):
            continue
        if s in metas:
            camino = [s]
            while camino[-1] in padre:
                camino.append(padre[camino[-1]])
            return camino[::-1]
        n += 1
        i, j, c = s
        vecinos = [((i + di, j + dj, c), coste) for di, dj, coste in pasos]
        if not rej.sin_via[j * rej.nx + i]:
            vecinos += [((i, j, c2), COSTE_VIA) for c2 in CAPAS if c2 != c]
        for t, coste in vecinos:
            if not rej.libre(*t):
                continue
            # en diagonal, las dos celdas de la esquina tienen que estar libres
            if t[2] == c and t[0] != i and t[1] != j and not (rej.libre(t[0], j, c) and rej.libre(i, t[1], c)):
                continue
            ng = gs + coste
            if ng < g.get(t, 1e18):
                g[t] = ng
                padre[t] = s
                heapq.heappush(abiertos, (ng + h(t[0], t[1]), ng, t))
    return None


def _anclas(item, ancho: float) -> list[tuple]:
    """Puntos (x, y, capa, origen, ancho_conector, desde_chequeo) donde puede empezar la pista.

    El conector es el tramo recto de `origen` (dentro del cobre del item) al
    punto. Solo se comprueba desde `desde_chequeo`, donde sale de ese cobre:
    la parte de dentro no anade nada (va sobre el pad o la pista de su red), y
    medirla rechazaria un pin al que Freerouting ya le paso al lado a su
    holgura justa. En un pad se recorre su eje largo hasta 0.8 mm fuera, y el
    conector va con el ancho del pin si la pista es mas ancha que el (lo que
    Freerouting llama neckdown). En una pista se aterriza sobre su eje o a un
    lado, con un conector corto y perpendicular.
    """
    if isinstance(item, pcbnew.PAD):
        x, y = item.GetPosition().x / 1e6, item.GetPosition().y / 1e6
        capas = (pcbnew.F_Cu,) if item.GetAttribute() == pcbnew.PAD_ATTRIB_SMD else CAPAS
        s = item.GetSize(pcbnew.F_Cu)
        w, h = s.x / 1e6, s.y / 1e6
        a = math.radians(item.GetOrientationDegrees())
        if w >= h:
            ux, uy = math.cos(-a), math.sin(-a)
        else:
            ux, uy = math.cos(-a + math.pi / 2), math.sin(-a + math.pi / 2)
        medio = max(w, h) / 2
        estrecho = min(ancho, min(w, h))
        out, t = [], 0.0
        while t <= medio + 0.8 + 1e-9:
            for sg in (1, -1):
                punto = (x + sg * t * ux, y + sg * t * uy)
                borde = punto if t <= medio else (x + sg * medio * ux, y + sg * medio * uy)
                out += [(punto[0], punto[1], c, (x, y), estrecho, borde) for c in capas]
            t += G / 2
        return out
    if isinstance(item, pcbnew.PCB_VIA):
        x, y = item.GetPosition().x / 1e6, item.GetPosition().y / 1e6
        return [(x + dx * 0.1, y + dy * 0.1, c, (x, y), ancho, (x + dx * 0.1, y + dy * 0.1))
                for c in CAPAS for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)]
    if item.GetLayer() not in CAPAS:
        return []
    ax, ay = item.GetStart().x / 1e6, item.GetStart().y / 1e6
    bx, by = item.GetEnd().x / 1e6, item.GetEnd().y / 1e6
    largo = math.hypot(bx - ax, by - ay)
    n = max(1, int(largo / (G / 2)))
    w = item.GetWidth() / 1e6
    # Una pista de Freerouting va a SU holgura justa de lo ajeno (0.16 mm): su
    # eje no es celda libre con SEGURIDAD, asi que tambien se aterriza a un lado.
    nx, ny = ((ay - by) / largo, (bx - ax) / largo) if largo else (0.0, 1.0)
    out = []
    for k in range(n + 1):
        px, py = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
        for d in (0.0, 0.1, -0.1, 0.2, -0.2, 0.3, -0.3):
            punto = (px + d * nx, py + d * ny)
            dentro = math.copysign(min(abs(d), w / 2), d)
            borde = (px + dentro * nx, py + dentro * ny)
            out.append((punto[0], punto[1], item.GetLayer(), (px, py), min(ancho, w), borde))
    return out


def _conector_libre(origen, punto, capa, ancho, red, obst, holgura) -> bool:
    """El tramo recto origen-punto, de `ancho`, guarda la holgura con el cobre ajeno."""
    largo = math.hypot(punto[0] - origen[0], punto[1] - origen[1])
    n = max(1, int(largo / 0.02))
    lim = holgura + ancho / 2 + 0.02
    for o in obst:
        if o.red == red or capa not in o.capas:
            continue
        for k in range(n + 1):
            x = origen[0] + (punto[0] - origen[0]) * k / n
            y = origen[1] + (punto[1] - origen[1]) * k / n
            if o.dist(x, y) < lim:
                return False
    return True


def conectar(board, grupo_a: list, grupo_b: list, ancho: float, holgura: float, via_d: float,
             via_drill: float, borde: tuple, obst: list) -> bool:
    """Une con pistas (y vias) cualquier cobre de `grupo_a` con cualquiera de `grupo_b`.

    Los grupos son los items (pads, pistas, vias) de los dos trozos de la
    misma red que KiCad da por sueltos. True si pudo.
    """
    red = grupo_a[0].GetNetname()
    an_a = [a for it in grupo_a for a in _anclas(it, ancho)]
    an_b = [a for it in grupo_b for a in _anclas(it, ancho)]
    if not an_a or not an_b:
        return False
    xs = [p[0] for p in an_a + an_b]
    ys = [p[1] for p in an_a + an_b]
    W, H, _m = borde
    caja = (max(0.0, min(xs) - MARGEN_CAJA), max(0.0, min(ys) - MARGEN_CAJA),
            min(W, max(xs) + MARGEN_CAJA), min(H, max(ys) + MARGEN_CAJA))
    cerca = [o for o in obst if not (o.caja[2] < caja[0] - 2 or o.caja[0] > caja[2] + 2
                                     or o.caja[3] < caja[1] - 2 or o.caja[1] > caja[3] + 2)]
    # La rejilla se alinea con el pad MAS ESTRECHO de los dos grupos, que es el
    # unico que no perdona media celda: un pin de 0.25 mm a 0.45 mm de paso
    # solo deja salir la pista por su eje (U6.10 se quedaba sin salida cuando
    # la rejilla seguia al otro extremo).
    pads = [it for it in grupo_a + grupo_b if isinstance(it, pcbnew.PAD)]
    if pads:
        fino = min(pads, key=lambda p: min(p.GetSize(pcbnew.F_Cu).x, p.GetSize(pcbnew.F_Cu).y))
        origen = (fino.GetPosition().x / 1e6, fino.GetPosition().y / 1e6)
    else:
        origen = an_a[0][3]
    rej = _Rejilla(caja, cerca, red, ancho, holgura, via_d, via_drill, borde, origen)
    desde_a, desde_b = {}, {}
    for anclas, desde in ((an_a, desde_a), (an_b, desde_b)):
        for x, y, capa, origen, w_con, borde_cobre in anclas:
            i, j = rej.celda(x, y)
            if (i, j, capa) in desde or not rej.libre(i, j, capa):
                continue
            junto = [o for o in cerca if o.caja[0] - 2 < origen[0] < o.caja[2] + 2
                     and o.caja[1] - 2 < origen[1] < o.caja[3] + 2]
            if _conector_libre(borde_cobre, rej.punto(i, j), capa, w_con, red, junto, holgura):
                desde[(i, j, capa)] = (origen, w_con)
    if not desde_a or not desde_b:
        return False
    camino = _a_estrella(rej, list(desde_a), list(desde_b))
    if camino is None:
        return False
    neto = board.FindNet(red)

    def pista(p, q, capa, w):
        if math.hypot(p[0] - q[0], p[1] - q[1]) < 1e-6:
            return
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(int(round(p[0] * 1e6)), int(round(p[1] * 1e6))))
        t.SetEnd(pcbnew.VECTOR2I(int(round(q[0] * 1e6)), int(round(q[1] * 1e6))))
        t.SetWidth(int(round(w * 1e6)))
        t.SetLayer(capa)
        t.SetNet(neto)
        board.Add(t)

    # Conectores de entrada y salida con su ancho (estrechado en un pin fino)
    (o_a, w_a), (o_b, w_b) = desde_a[camino[0]], desde_b[camino[-1]]
    pista(o_a, rej.punto(*camino[0][:2]), camino[0][2], w_a)
    pista(rej.punto(*camino[-1][:2]), o_b, camino[-1][2], w_b)
    # El cuerpo del camino: vias donde cambia de capa y tramos rectos que
    # juntan los pasos que siguen la misma direccion
    puntos = []
    for k, (i, j, c) in enumerate(camino):
        p = rej.punto(i, j)
        if k and c != camino[k - 1][2]:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(int(round(p[0] * 1e6)), int(round(p[1] * 1e6))))
            v.SetWidth(int(round(via_d * 1e6)))
            v.SetDrill(int(round(via_drill * 1e6)))
            v.SetNet(neto)
            board.Add(v)
        puntos.append((p, c))
    tramo_ini, ultima = puntos[0][0], None
    for k in range(1, len(puntos)):
        (p, c), (q, c2) = puntos[k - 1], puntos[k]
        if c != c2:
            pista(tramo_ini, p, c, ancho)
            tramo_ini, ultima = p, None
            continue
        d = (q[0] - p[0], q[1] - p[1])
        norma = math.hypot(*d) or 1.0
        d = (round(d[0] / norma, 2), round(d[1] / norma, 2))
        if ultima is not None and d != ultima:
            pista(tramo_ini, p, c, ancho)
            tramo_ini = p
        ultima = d
    pista(tramo_ini, puntos[-1][0], puntos[-1][1], ancho)
    return True
