"""Relee los DXF exportados y verifica lo que el laser va a ver.

    python case/check_dxf.py

Leccion de projects/vectorizer (docs/dxf-dialect.md): unidades, cierre de
paths y entidades descartadas fallan EN SILENCIO. Se valida contra el
archivo RELEIDO con ezdxf, jamas contra el objeto que lo genero. Corre
dentro de export.ps1, despues de exportar y antes de dar el lote por bueno
(Principio III). Requiere: python -m pip install ezdxf
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

import ezdxf

PLANS = Path(__file__).parent / "plans"

# Sobre esperado por pieza, mm: (w_min, w_max, h_min, h_max).
#
# SE DERIVAN DE params.scad, no se cablean. Los sobres estuvieron escritos
# como literales con margen de +-15 mm, y eso se rompio dos veces por razones
# opuestas:
#
#  1. Por MEDIR EL ARTEFACTO. El sobre viejo de bandeja_base_2d (290-320) se
#     calibro midiendo la pieza DEFECTUOSA de 306 mm de fondo, o sea que
#     bendecia exactamente el fallo que tenia que cazar (la bandeja del PSU
#     sin apoyo en su rail trasero). Calibrar el criterio con el objeto que
#     el criterio juzga no valida nada.
#  2. Por ENVEJECER. Al pasar la silueta al triangulo (fondo 350 -> 235,
#     zocalo 50 -> 45) tres piezas cambiaron de tamano A PROPOSITO y los tres
#     literales dieron ROJO sobre geometria correcta. Un gate que grita en
#     falso cada vez que el diseno se mueve se acaba desactivando, y ese es
#     el peor final posible para una puerta.
#
# Derivar mata las dos. El espesor se descarta solo: de las tres aristas de
# cada caja, las dos mayores son las del DXF y la menor es su espesor.
#
# QUE PUEDE Y QUE NO PUEDE CAZAR ESTE CHEQUEO, dicho claro: como la
# expectativa sale de las mismas formulas con que el modelo dibuja, NO puede
# cazar un error DE FORMULA -- para eso estan la autocomprobacion a mano,
# solapes() y alineacion() de clearance_budget. Lo que si caza, y es su
# trabajo, es que el DXF releido no coincida con lo que el modelo cree haber
# exportado: unidades (el factor 25.4 clasico), escala, entidades
# descartadas en silencio y contornos abiertos. Por eso la tolerancia es
# CERRADA (+-2 mm, no +-15): con margen ancho un error de escala del 5% se
# cuela, y el kerf no entra en juego porque solo se aplica a los huecos, no
# a los contornos exteriores.
#
# Estuvo en 2.0 y subio a 4.0 al meter el BOMBEO del contorno (la entasis de
# las rectas): el abombamiento va hacia fuera, asi que crece el bbox de forma
# legitima. No afloja lo que importa: 4 mm sobre una pieza de 309 es un 1.3 %,
# y un error de escala del 5 % (15 mm) o el factor 25.4 siguen cayendo de largo.
#
# ESTA NOTA CULPABA AL CANTO DE ABAJO ("1.7 mm en el canto de abajo") y ese
# canto esta EXENTO de bombeo desde que entro en sin_bombeo por las paticas
# -- o sea que no crecia nada. Quien se comia la tolerancia era el CANTO
# TRASERO: 1.197 mm medidos sobre este mismo DXF. El 2026-08-24 se eximio
# tambien (y con el la meseta del techo, 0.250 mm), asi que hoy la mayor
# flecha del contorno son 0.779 mm en la cara del panel de abajo.
#
# TOL NO SE BAJA AQUI a proposito, aunque ahora sobre: esta puerta existe para
# cazar unidades y escala, no flechas de decimas, y estrecharla a la medida de
# la geometria de hoy la vuelve fragil al proximo cambio de silueta.
TOL = 4.0

# Piezas que el modelo YA coloca pero que todavia no tienen fichero de corte, con
# el motivo. No es una lista de excepciones para tapar pendientes: cada entrada
# se imprime en cada corrida, asi que el hueco se ve. La alternativa era emitir
# un DXF de contorno sin taladros, y eso es peor -- un fichero que parece
# completo y se manda a cortar (constitucion, Principio V).
SIN_DXF: dict[str, str] = {}

# Piezas que van GIRADAS con una cara, o sea que su caja en el mundo NO es su
# DXF. Esta vacio desde el 2026-08-21: la unica que estaba era la pestana de
# remate, que iba de canto sobre la cara de arriba y median 10.75 x 528 de caja
# por la diagonal de su seccion a 45 grados. Ahora es una plancha HORIZONTAL
# sobre la meseta, alineada con los ejes, y su caja YA es su DXF -- o sea que
# sale sola de _cajas_solidas y no hay que declarar su sobre a mano.
GIRADAS: set[str] = set()

# Las tres placas de anclaje, nombre de tramo -> nombre de DXF. GEMELA de
# TRAMOS_PLACA en clearance_budget.py y de tramos_placa() en el .scad: el
# orden no importa aqui (se recorre por nombre), pero los TRES nombres si --
# son los que placa_2d() usa para buscar su tramo en placas().
PLACAS_DXF = {"cara_inf": "placa_cara_inf_2d", "valle": "placa_valle_2d",
              "cara_sup": "placa_cara_sup_2d"}


def _retiro_costado(p: dict[str, float]) -> float:
    """Cuanto se retranquea el acrilico del costado respecto a la silueta."""
    return p["cara_anillo"] - p["rebaje_anillo"] + p["hol_costado"]


def _sobre_dorso(cb, p: dict[str, float],
                  g: dict[str, float]) -> tuple[float, float]:
    """Envolvente del DXF del dorso: el contorno del rebaje MAS los circulos
    de las roscas ciegas, que caen fuera de el.

    El rebaje es la silueta retirada cara - rebaje por los cuatro lados; las
    roscas viven entre esa linea y la silueta, o sea que asoman. Sin sumarlas
    el sobre se queda 14 mm corto en Y y el fichero sale rojo por una razon
    que no es un defecto."""
    retiro = p["cara_anillo"] - p["rebaje_anillo"]
    x0, x1 = retiro, cb.fondo(p) - retiro
    y0, y1 = retiro, g["alto_total"] - retiro
    for _, c, d in cb._centros_rosca_ciega(p):
        x0, x1 = min(x0, c[0] - d / 2), max(x1, c[0] + d / 2)
        y0, y1 = min(y0, c[1] - d / 2), max(y1, c[1] + d / 2)
    return x1 - x0, y1 - y0


def _sobres() -> dict[str, tuple[float, float, float, float]]:
    import clearance_budget as cb

    p = cb.leer_params()
    g = cb.perfil(p)
    _, planchas, _ = cb._cajas_solidas(p)

    dims: dict[str, tuple[float, float]] = {
        # EL COSTADO VA DENTRO DE LA VENTANA DEL ANILLO desde el 2026-08-28:
        # su contorno es la silueta retranqueada (cara - rebaje + holgura).
        "costado_2d": (cb.fondo(p) - 2 * _retiro_costado(p),
                       g["alto_total"] - 2 * _retiro_costado(p)),
        # LA COSTILLA VUELVE A SER EL CONTORNO DE LA PIEZA: un anillo fresado
        # no tiene desarrollo. Silueta entera, con la ventana dentro.
        "costilla_2d": (cb.fondo(p), g["alto_total"]),
        # El dorso: lo que se fresa POR DETRAS -- el contorno del rebaje y los
        # centros de las roscas ciegas. Es otro DXF porque un 2D no sabe decir
        # "a 11 de profundidad": mismo caso que kondor_cajeado_2d.
        # SU BBOX NO ES LA DEL REBAJE desde el 2026-08-28: las roscas ciegas
        # viven en la FRANJA, o sea POR FUERA del contorno del rebaje, asi que
        # la envolvente del fichero es la union de los dos. Derivada, no a
        # mano: si una rosca se sale de la franja, el sobre crece con ella y no
        # canta nada -- de eso responden guarda_anclajes() y taladros_anillo().
        "costilla_dorso_2d": _sobre_dorso(cb, p, g),
        # cupon: 2*margen + (n-1)*paso de la escalera, x 62 de alto. No sale
        # de _cajas_solidas porque no es una pieza del case.
        "coupon": (136.0, 62.0),
        # LA SECCION DEL ANILLO, de la que se corta el cupon de 100 mm (#237).
        # Es la seccion y no el cupon entero: el largo va en la nota del pliego
        # porque un DXF de seccion no lo dice, igual que no dice profundidades
        # el de planta. cara x pletina, tal cual.
        "cupon_anillo_2d": (p["cara_anillo"], p["t_anillo"]),
    }
    # Las tres de ACERO. No salen de _cajas_solidas porque no son planchas del
    # cuerpo del case, y sobre todo porque su DXF NO es su caja: el desarrollo
    # de una chapa doblada es mas grande que la pieza montada (492.69 x 330.69
    # de recorte para una caja de 338.6 x 176.6). Ese es justo el error que
    # este sobre tiene que cazar -- exportar el contorno de la caja en vez del
    # desarrollo da un DXF valido, con las cotas de la pieza, e inservible.
    ch = cb._chasis(p)
    dims["chasis_cuerpo_2d"] = (ch["blank_cuerpo_x"], ch["blank_cuerpo_y"])
    dims["chasis_tapa_2d"] = (ch["blank_tapa_x"], ch["blank_tapa_y"])
    dims["chasis_refuerzo_2d"] = (p["chasis_refuerzo_lado"],
                                  p["chasis_refuerzo_lado"])
    for caja in planchas:
        nombre, x0, x1, y0, y1, z0, z1 = caja
        if nombre in SIN_DXF or nombre in GIRADAS:
            continue
        aristas = sorted((x1 - x0, y1 - y0, z1 - z0), reverse=True)
        dims[f"{nombre}_2d"] = (aristas[0], aristas[1])   # se cae el espesor

    # DESPUES del bucle, y por eso: la tapa del valle SI es una plancha del
    # cuerpo, asi que el bucle le pone la caja de la pieza doblada -- y su DXF
    # es el DESARROLLO, que sale 2*vuelo mas ancho por las dos pestanas. Es el
    # mismo error que el sobre del chasis tiene que cazar: exportar el contorno
    # de la pieza montada en vez del recorte da un DXF valido e inservible.
    dims["tapa_valle_2d"] = cb.bbox_desarrollo_tapa(p)
    # LOS TRES MIEMBROS DE CHAPA. Sus DXF son DESARROLLOS y salen mas grandes
    # que la pieza doblada, igual que la costilla, la tapa del valle y las tres
    # del chasis. Derivados, no escritos a mano: si el .scad y la cuenta de
    # Python se separan, el bbox real del fichero se sale del sobre y revisar()
    # lo canta. Es la unica forma de cruzar dos gemelas que viven en lenguajes
    # distintos.
    dims["miembro_bajo_2d"] = cb.bbox_desarrollo_miembro(p, "trasero bajo")
    dims["miembro_alto_2d"] = cb.bbox_desarrollo_miembro(p, "trasero alto")
    dims["bahia_2d"] = cb.bbox_desarrollo_bahia(p)
    # LA ESCUADRA DE LA TRASERA es de la misma chapa y por eso su DXF es otro
    # DESARROLLO: las dos alas por su cota exterior menos un BD. Sale 3.3 mm
    # mas estrecho que la suma de las dos alas montadas, y esa diferencia ES la
    # pieza -- exportar la L ya doblada da un fichero valido e inservible.
    dims["escuadra_trasera_2d"] = cb.bbox_desarrollo_escuadra(p)

    # LAS TRES PLACAS DE ANCLAJE Y EL CLIP. Entran el 2026-08-28 (Tarea 6,
    # item del controller): hasta hoy placas()/clips() eran solidos del
    # modelo sin fichero de corte -- piezas que el render ensena pero que
    # nadie manda a fresar. UN DXF POR TRAMO, no por costado: el lado
    # espejado (z) comparte el mismo contorno xy (ver la nota de
    # placa_cara_inf_2d() en el .scad), asi que el sobre sale del bbox de
    # esquinas_placa(), sin doblar nada por la mitad.
    for nombre, dxf in PLACAS_DXF.items():
        pl = next(pl for pl in cb._placas(p) if pl[0] == nombre)
        q = cb._esquinas_placa(pl)
        xs, ys = [c[0] for c in q], [c[1] for c in q]
        dims[dxf] = (max(xs) - min(xs), max(ys) - min(ys))
    # El clip es una pieza GENERICA (no depende de a que tramo ni a que s se
    # atornille): clip_largo x clip_fondo, igual que dibuja clip_2d().
    dims["clip_2d"] = (p["clip_largo"], p["clip_fondo"])

    return {n: (w - TOL, w + TOL, h - TOL, h + TOL) for n, (w, h) in dims.items()}


SOBRES = _sobres()


def revisar(nombre: str, sobre) -> list[str]:
    f: list[str] = []
    ruta = PLANS / f"{nombre}.dxf"
    doc = ezdxf.readfile(ruta)
    ents = list(doc.modelspace())
    if not ents:
        return [f"{nombre}: DXF sin entidades"]
    grados: Counter = Counter()   # paridad de extremos de LINEs sueltas
    xs: list[float] = []
    ys: list[float] = []

    def punto(x, y):
        xs.append(x); ys.append(y)
        return (round(x, 3), round(y, 3))

    for e in ents:
        t = e.dxftype()
        if t == "LINE":
            grados[punto(e.dxf.start.x, e.dxf.start.y)] += 1
            grados[punto(e.dxf.end.x, e.dxf.end.y)] += 1
        elif t == "LWPOLYLINE":
            pts = e.get_points("xy")
            for x, y in pts:
                punto(x, y)
            cerrado = e.closed or (
                len(pts) > 2
                and abs(pts[0][0] - pts[-1][0]) < 1e-6
                and abs(pts[0][1] - pts[-1][1]) < 1e-6)
            if not cerrado:
                f.append(f"{nombre}: LWPOLYLINE sin cerrar")
        elif t in ("CIRCLE", "ARC"):
            punto(e.dxf.center.x - e.dxf.radius, e.dxf.center.y - e.dxf.radius)
            punto(e.dxf.center.x + e.dxf.radius, e.dxf.center.y + e.dxf.radius)
            if t == "ARC":
                f.append(f"{nombre}: ARC suelto (posible contorno abierto)")
    sueltos = [p for p, n in grados.items() if n % 2]
    if sueltos:
        f.append(f"{nombre}: {len(sueltos)} extremos de LINE sin pareja "
                 f"(contorno abierto), p.ej. {sueltos[:3]}")
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    ancho_ok = sobre[0] <= w <= sobre[1] or sobre[0] <= h <= sobre[1]
    alto_ok = sobre[2] <= h <= sobre[3] or sobre[2] <= w <= sobre[3]
    if not (ancho_ok and alto_ok):
        f.append(f"{nombre}: bbox {w:.1f} x {h:.1f} mm fuera del sobre "
                 f"{sobre} (unidades mal? factor 25.4?)")
    # ezdxf SINTETIZA un header completo al leer: doc.header reporta
    # $INSUNITS=6 aunque el archivo no lo traiga (verificado: la cadena
    # aparece 0 veces). OpenSCAD 2021.01 emite R12 SIN seccion HEADER, asi
    # que el DXF no declara unidades y la unica fuente honesta es el texto.
    # Ausente = correcto (numeros crudos en mm; se le dice al servicio).
    if "$INSUNITS" in ruta.read_text(encoding="utf-8", errors="replace"):
        ins = doc.header.get("$INSUNITS", 0)
        if ins not in (0, 4):
            f.append(f"{nombre}: $INSUNITS={ins} (ni ausente ni mm)")
    print(f"  {nombre}: {len(ents)} entidades, bbox {w:.1f} x {h:.1f} mm")
    return f


def _componentes(nombre: str) -> tuple[list, list[list[int]]]:
    """Parte el DXF en componentes conexas por sus extremos de LINE.

    Devuelve (aristas, componentes). El contorno exterior y cada agujero salen
    como componentes separadas porque no comparten ningun vertice."""
    doc = ezdxf.readfile(PLANS / f"{nombre}.dxf")
    aristas = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))
               for e in doc.modelspace() if e.dxftype() == "LINE"]
    if not aristas:
        return [], []
    vecinos: dict[tuple, list[int]] = {}
    for i, (a, b) in enumerate(aristas):
        for pt in (a, b):
            vecinos.setdefault((round(pt[0], 3), round(pt[1], 3)), []).append(i)
    visto: set[int] = set()
    comps: list[list[int]] = []
    for i in range(len(aristas)):
        if i in visto:
            continue
        pila, comp = [i], []
        visto.add(i)
        while pila:
            j = pila.pop()
            comp.append(j)
            for pt in aristas[j]:
                for k in vecinos[(round(pt[0], 3), round(pt[1], 3))]:
                    if k not in visto:
                        visto.add(k)
                        pila.append(k)
        comps.append(comp)
    return aristas, comps


def _redondos(nombre: str) -> list[tuple[float, float, float]]:
    """Centros y diametros de los agujeros REDONDOS leidos del DXF.

    Redondo = componente cuya caja es cuadrada dentro de una decima. Deja fuera
    el contorno (que no lo es) y las ranuras del valle (obround, mas largas que
    anchas), que no son agujeros de tornillo."""
    aristas, comps = _componentes(nombre)
    out = []
    for comp in comps:
        px = [p[0] for j in comp for p in aristas[j]]
        py = [p[1] for j in comp for p in aristas[j]]
        w, h = max(px) - min(px), max(py) - min(py)
        if w < 0.1 or abs(w - h) > 0.1 or w > 30:
            continue
        out.append(((min(px) + max(px)) / 2, (min(py) + max(py)) / 2, (w + h) / 2))
    return out


def _cantos(nombre: str) -> list:
    """TODAS las aristas de canto de una pieza: contorno exterior, ventana
    interior y cualquier vaciado. Fuera quedan los agujeros de tornillo.

    `_contorno_costado()` se queda con la componente mas grande y basta para el
    costado, que es macizo. La COSTILLA no lo es: es una banda, y un taladro
    suyo tiene DOS cantos de los que apartarse. Mirar solo el de fuera es
    exactamente el fallo que esta puerta caza -- los cuatro M4 caen a 16 mm del
    contorno, que sobra, y a 4 mm de la ventana, que no."""
    aristas, comps = _componentes(nombre)
    out = []
    for comp in comps:
        px = [p[0] for j in comp for p in aristas[j]]
        py = [p[1] for j in comp for p in aristas[j]]
        w, h = max(px) - min(px), max(py) - min(py)
        if w < 30 and abs(w - h) <= 0.1:       # agujero redondo de tornillo
            continue
        out += [aristas[j] for j in comp]
    return out


def _contorno_exterior(nombre: str) -> list:
    """El anillo de aristas mas grande de un DXF: la silueta, no la ventana.

    Devuelve ARISTAS y no vertices ordenados, que es lo que comen _dentro() y
    _dist_al_contorno(). Se valida contra el ARCHIVO, no contra una copia de
    redondear() en Python: replicarla aqui seria la tercera copia de la misma
    matematica, y la version que cuenta es la que salio al fichero que va al
    taller. Los agujeros -- y la ventana del anillo -- salen como componentes
    aparte; la silueta es la de bbox mas grande."""
    aristas, comps = _componentes(nombre)
    if not comps:
        return []

    def area(comp):
        px = [q[0] for j in comp for q in aristas[j]]
        py = [q[1] for j in comp for q in aristas[j]]
        return (max(px) - min(px)) * (max(py) - min(py))

    return [aristas[j] for j in max(comps, key=area)]


def _contorno_costado() -> list:
    """Aristas del contorno EXTERIOR de costado_2d, releidas del DXF."""
    return _contorno_exterior("costado_2d")


def _dentro(contorno, pt) -> bool:
    """Ray casting horizontal contra la lista de aristas (no necesita que
    esten ordenadas en anillo)."""
    x, y = pt
    cruces = 0
    for (x0, y0), (x1, y1) in contorno:
        if (y0 > y) != (y1 > y):
            xc = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if xc > x:
                cruces += 1
    return cruces % 2 == 1


def tapa_valle_conectada() -> list[str]:
    """Una isla de material y solo los dos M3 de sus pestanas.

    El contorno principal es la componente de mayor bbox. Los agujeros y las
    ranuras tienen su centro dentro de ese contorno; una pestana separada forma
    otra componente cuyo centro queda fuera, aunque el bbox total siga igual.
    """
    import clearance_budget as cb

    aristas, comps = _componentes("tapa_valle_2d")
    if not aristas:
        return ["tapa_valle_2d: sin LINEs, no se puede verificar conectividad"]

    def datos(comp):
        puntos = [p for i in comp for p in aristas[i]]
        xs, ys = zip(*puntos)
        area_bbox = (max(xs) - min(xs)) * (max(ys) - min(ys))
        centro = (sum(xs) / len(xs), sum(ys) / len(ys))
        return area_bbox, centro

    principal = max(comps, key=lambda c: datos(c)[0])
    contorno = [aristas[i] for i in principal]
    sueltas = [c for c in comps if c is not principal and not _dentro(contorno, datos(c)[1])]
    f = []
    if sueltas:
        f.append(f"tapa_valle_2d: {len(sueltas)} contornos de material separados "
                 f"de la banda. La banda y sus dos pestanas tienen que salir de "
                 f"UNA sola pieza conectada")

    p = cb.leer_params()
    # la banda muere contra las placas del valle: su ancho no es el del hueco
    au = cb._tapa_valle_au(p)
    redondos = _redondos("tapa_valle_2d")
    interiores = [q for q in redondos if 0 <= q[0] <= au]
    if len(redondos) != 2 or interiores:
        f.append(f"tapa_valle_2d: trae {len(redondos)} M3 redondos, "
                 f"{len(interiores)} dentro de la banda. Tienen que quedar "
                 f"exactamente los 2 de las pestanas y CERO de los diez que "
                 f"atornillaban al canto de las alas")
    if not f:
        print("  tapa_valle_2d: UNA pieza conectada, 2 M3 de pestana y CERO en la banda")
    return f


def _dist_al_contorno(contorno, pt) -> float:
    """Distancia del punto a la arista mas cercana del contorno."""
    x, y = pt
    mejor = float("inf")
    for (x0, y0), (x1, y1) in contorno:
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        s = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x0) * dx
                                                    + (y - y0) * dy) / L2))
        mejor = min(mejor, math.hypot(x - (x0 + s * dx), y - (y0 + s * dy)))
    return mejor


def _dist_al_apoyo(q, pt) -> float:
    """Distancia del punto al apoyo, y CERO si cae encima de el.

    `_dist_al_contorno()` mide al canto y por eso no sirve sola aqui: un punto
    del acrilico que este justo debajo de una placa tiene apoyo, y esa funcion
    le devolveria hasta 13 mm de "vano". Lo que se mide es cuanto le falta al
    punto para llegar al apoyo mas cercano, no cuanto le sobra.

    `q` son los VERTICES del apoyo (poligono cerrado), no sus aristas: los
    clips son rectangulos y las placas van giradas con su tramo y con las dos
    esquinas hondas cortadas."""
    aristas = [(q[i], q[(i + 1) % len(q)]) for i in range(len(q))]
    return 0.0 if _dentro(aristas, pt) else _dist_al_contorno(aristas, pt)


# Distancia MINIMA del centro de un taladro al canto, en diametros. La regla de
# oficio para plastico es 2xD y lo ideal seria exigir eso, pero los tres
# largueros del plano trasero viven entre 1.94 y 2.0 D por geometria -- ponerlo
# en 2.0 seria una puerta gritando en falso sobre algo verificado. A 1.5 D queda
# margen de sobra y sigue cazando el fallo de verdad: mover un larguero contra
# una curva y no enterarse. Y el aplastamiento real no es el limite: el eje de
# la tapa, que es el M5 mas cargado del case, trabaja a 0.33 MPa sobre acrilico
# que aguanta ~100.
#
# LA REUSA taladros_placas() (Tarea 6) para las placas y el clip de ALUMINIO,
# no solo para el acrilico de esta nota: es la misma regla de oficio -- 1.5 D
# al canto -- aplicada por reutilizacion conservadora, no porque se haya
# recalculado para pletina de 6/4 mm. RFQ.md la confirma como el minimo que
# el taller ya trabaja sin margen de sobra (6.75 mm en el M4 de brida).
BORDE_MIN_D = 1.5


# taladros_con_material() MURIO el 2026-08-27, y conviene que quede dicho por
# que en vez de dejar la funcion vacia. Medía que cada taladro del costado
# tuviera acrilico alrededor -- 1.5 x D desde el centro al canto -- porque un M5
# a dos milimetros de una curva no falla al montarlo, falla al APRETARLO, y raja
# el costado. Esa puerta ya no tiene sujeto: el costado no lleva un solo
# taladro. Su criterio se MUDO con los tornillos a taladros_costilla(), que
# ademas pedia los dos cantos de la banda -- cosa que aqui no hacia falta
# porque el acrilico es macizo.
#
# Y taladros_costilla() murio a su vez el 2026-08-28: el anillo fresado no
# lleva un solo agujero PASANTE. Los tornillos del riel y de los miembros van
# a roscas CIEGAS por la cara interior, que un DXF de contorno no sabe dibujar
# -- salen en costilla_dorso_2d, con su profundidad en el pliego --, y quien
# las cuente sera la puerta de la Tarea 3, cuando las placas de anclaje
# existan. Hasta entonces el hueco esta declarado aqui y no escondido.

# Cuanto puede desviarse un agujero del DXF respecto de donde el modelo lo
# pone. No es tolerancia de fabricacion -- es cuanto se permite que MIENTAN el
# uno sobre el otro, y la respuesta es casi nada: son el mismo numero pasado
# por OpenSCAD.
#
# TAMBIEN HACE DE HOLGURA DE CANTO en taladros_placas() (Tarea 6): las dos
# lenguetas de bahia de placa_valle_2d viven EXACTO en el limite de
# BORDE_MIN_D por diseno (placa_1u_fondo() en clearance_budget.py), asi que
# el ruido de tessellation del viaje OpenSCAD -> DXF -> ezdxf cae del lado
# equivocado de un `<` estricto sin esta rebaja. Prestamo, no una tolerancia
# nueva: mismo numero, dos usos.
DESVIO_DXF_MAX = 0.02


def agujeros_donde_toca() -> list[str]:
    """Los agujeros del DXF caen donde el modelo dice. Leidos DEL FICHERO.

    Esta puerta existe por el issue #51, y el issue traia su propia
    reproduccion: mover las dos filas de bandeja_base_2d +10 y -10 mm, exportar,
    y las dos puertas daban VERDE. check_dxf solo miraba el bbox -- que no
    cambia, porque las filas viven DENTRO del contorno -- y alineacion() en
    clearance_budget comparaba el modelo contra si mismo sin abrir un .dxf en
    ningun momento. Un fichero con los agujeros en otro sitio pasaba entero.

    Se comprueba lo que es invariante dentro del plano de cada plancha --
    cuantas filas hay, cuantos agujeros por fila, el paso en X, y la SEPARACION
    entre filas. Esa ultima es la que atrapa la reproduccion del issue: mover
    una fila +10 y otra -10 cambia su separacion en 20 mm. No se comprueba la
    posicion absoluta dentro de la plancha porque eso exigiria replicar aqui la
    colocacion 3D de cada pieza, que es justo la copia de matematica que este
    fichero evita a proposito."""
    import clearance_budget as cb

    p = cb.leer_params()
    f: list[str] = []

    # --- costado: CERO agujeros, otra vez ---
    # Los tuvo (once M5), no los tuvo (2026-08-27 por la manana), tuvo cuatro
    # pasos de casquillo (por la tarde) y desde el 2026-08-28 no tiene ninguno:
    # va DENTRO de la ventana del anillo, coplanar, y nada lo atraviesa.
    if _redondos("costado_2d"):
        f.append(f"costado_2d: {len(_redondos('costado_2d'))} agujero(s) redondo(s) "
                 f"en el acrilico. El costado es PIEL dentro del anillo: cero")

    # --- planchas: filas, paso y separacion ---
    _, _, filas = cb._cajas_solidas(p)
    # DEL PRESUPUESTO, no recalculado: desde el 2026-08-26 ancho_util resta
    # tambien las dos alas de costilla, y una copia a mano de la formula aqui
    # se desincroniza del original en cuanto se toque t_costilla.
    au = cb.perfil(p)["ancho_util"]
    # EL PASO SE LEE, no se escribe. Fue un 100 a mano hasta el 2026-08-27 y
    # era la tercera copia del mismo numero (las otras dos: fila_agujeros()
    # y n_agujeros()). Con reticula_paso gobernando los agujeros de los
    # miembros, una copia aqui desincroniza la puerta de la pieza.
    n = max(1, round(au / p["reticula_paso"]))
    e = au / n
    # DOS REJILLAS, no una. Las bandejas y la tapa del valle se atornillan a un
    # larguero a lo largo y usan fila_agujeros() -- n agujeros repartidos con
    # margenes iguales. Las pieles cuelgan de separadores y usan otra cosa: tres
    # columnas fijas, la del medio porque con solo las esquinas el vano de 518
    # se descuelga 1.76 mm de peso propio. Meterlas en el mismo saco daba ROJO
    # en la primera corrida de esta puerta, y el fallo era del saco.
    # Y las pieles ni siquiera son igual de anchas: se meten hol_piel por cada
    # lado (piel_inferior_2d y piel_superior_2d lo definen asi). Usar el ancho
    # util del case aqui daba la columna del medio corrida, que es exactamente
    # el tipo de fallo que esta puerta busca -- solo que en la puerta y no en la
    # pieza. Con las pieles empotradas ese margen bajo de 5 mm a 0.15, pero la
    # cuenta es la misma y por eso sigue leyendo el parametro.
    # La trasera usa la MISMA rejilla que las bandejas -- fila_agujeros con 5
    # taladros -- pero sobre SU ancho, que es 2*hol_piel mas estrecho que el
    # util del case porque va empotrada entre los costados. Calcular su rejilla
    # con el ancho del case corre cada columna 0.06 mm y la ultima 0.27: la
    # puerta lo canto a la primera corrida de esta tanda, que es para lo que
    # esta. Fueron tres columnas ([15, medio, ancho-15]) mientras las pieles
    # colgaban de separadores; desde que se atornillan a los largueros usan el
    # mismo paso que el resto de las planchas.
    au_piel = au - 2 * p["hol_piel"]
    e_piel = au_piel / n
    REJILLA_FILA = [e * (i + 0.5) for i in range(n)]
    REJILLA_PIEL = [e_piel * (i + 0.5) for i in range(n)]
    GRIDS = {"piel_trasera": REJILLA_PIEL}
    por_placa: dict[str, list[float]] = {}
    for placa, _, _, coord, _ in filas:
        por_placa.setdefault(placa, []).append(coord)
    for placa, coords in sorted(por_placa.items()):
        nombre = f"{placa}_2d"
        if not (PLANS / f"{nombre}.dxf").exists():
            continue
        rejilla = GRIDS.get(placa, REJILLA_FILA)
        leidos = _redondos(nombre)
        # LA TAPA DEL VALLE trae DOS agujeros que no son de fila: los M3 de sus
        # pestanas, que viven FUERA del contorno de la plancha (en el
        # desarrollo caen a BD - a del canto, o sea del lado de afuera). Se
        # apartan por POSICION y no por conteo: si alguien mueve uno hacia
        # dentro, deja de contar como pestana y la rejilla lo caza.
        if placa == "tapa_valle":
            # SU ANCHO NO ES ancho_util desde el 2026-08-28: la banda muere
            # contra las placas del valle, 2*t_placa mas estrecha.
            ancho = cb._tapa_valle_au(p)
            fuera = [q for q in leidos if q[0] < 0 or q[0] > ancho]
            if len(fuera) != 2:
                f.append(f"{nombre}: {len(fuera)} agujeros fuera del contorno "
                         f"de la plancha y las pestanas son 2. Un M3 de "
                         f"pestana que cae DENTRO no se dobla: se queda en la "
                         f"cara de arriba de la tapa")
            leidos = [q for q in leidos if 0 <= q[0] <= ancho]
        # LA TRASERA trae SEIS M3 que no son de fila desde el 2026-08-28: los
        # de las dos ESCUADRAS, tres por costado, en columna a 9.05 mm de cada
        # canto. Se apartan por POSICION y no por conteo, igual que los M3 de
        # pestana de la tapa del valle: si alguien mueve uno, deja de contar
        # como escuadra y la rejilla de la pieza lo caza como intruso.
        #
        # Y SE CUENTAN APARTE, no dentro de las filas: meterlos en la rejilla
        # habria sido decir que la trasera tiene tres filas de cinco y media,
        # que es justo la clase de censo que pasa en verde con un agujero
        # menos. Aqui el numero que se exige es el del modelo, escuadra por
        # escuadra.
        if placa == "piel_trasera":
            esperados = cb._centros_m3_escuadra(p)
            de_escuadra = [q for q in leidos
                           if any(math.hypot(q[0] - ex, q[1] - ey)
                                  <= DESVIO_DXF_MAX for ex, ey in esperados)]
            if len(de_escuadra) != len(esperados):
                f.append(f"{nombre}: {len(de_escuadra)} M3 de escuadra en el "
                         f"DXF y el modelo pone {len(esperados)} "
                         f"({int(p['escuadra_m3'])} por costado, a "
                         f"{esperados[0][0]:.2f} mm del canto). Sin ellos la "
                         f"escuadra no tiene por donde atornillarse y el canto "
                         f"trasero del costado se queda otra vez sin tope")
            leidos = [q for q in leidos if q not in de_escuadra]
        if len(leidos) != len(rejilla) * len(coords):
            f.append(f"{nombre}: {len(leidos)} agujeros en el DXF y el modelo "
                     f"pone {len(rejilla) * len(coords)} ({len(coords)} filas de "
                     f"{len(rejilla)})")
            continue
        for cx, _, _ in leidos:
            if min(abs(cx - r) for r in rejilla) > DESVIO_DXF_MAX:
                f.append(f"{nombre}: un agujero en x={cx:.2f} se sale de la "
                         f"rejilla de la pieza ({[round(r,1) for r in rejilla]})")
                break
        ys = sorted({round(cy, 3) for _, cy, _ in leidos})
        if len(ys) != len(coords):
            f.append(f"{nombre}: el DXF tiene {len(ys)} filas distintas y el "
                     f"modelo pone {len(coords)}")
        elif len(ys) > 1:
            sep_dxf = round(ys[-1] - ys[0], 3)
            sep_mod = round(max(coords) - min(coords), 3)
            if abs(sep_dxf - sep_mod) > DESVIO_DXF_MAX:
                f.append(f"{nombre}: las filas estan a {sep_dxf:.2f} mm en el DXF "
                         f"y a {sep_mod:.2f} en el modelo (difieren "
                         f"{sep_dxf - sep_mod:+.2f}) -- una de las dos se movio")
    if not f:
        print(f"  planchas: {sum(len(c) for c in por_placa.values())} filas de "
              f"agujeros verificadas contra el DXF")
    return f


def _anillo(aristas, comp) -> list[tuple[float, float]]:
    """Ordena las aristas de una componente conexa en un anillo de vertices.

    Hace falta porque OpenSCAD 2021.01 emite DXF R12, que NO tiene
    LWPOLYLINE: cada contorno llega como un monton de LINE sueltas, sin
    orden. Para rellenar un poligono hay que devolverles el orden.
    """
    def clave(pt):
        return (round(pt[0], 3), round(pt[1], 3))

    porpunto: dict[tuple, list[int]] = {}
    for i in comp:
        for pt in aristas[i]:
            porpunto.setdefault(clave(pt), []).append(i)
    inicio = comp[0]
    anillo = [aristas[inicio][0], aristas[inicio][1]]
    usados = {inicio}
    while True:
        actual = clave(anillo[-1])
        sig = [i for i in porpunto.get(actual, []) if i not in usados]
        if not sig:
            return anillo
        i = sig[0]
        usados.add(i)
        a, b = aristas[i]
        anillo.append(b if clave(a) == actual else a)


def guarda_kondor() -> list[str]:
    """El relieve KONDOR: que la fuente sea la buena y que la fresa entre.

    DOS FALLOS DISTINTOS, los dos silenciosos, y por eso hay puerta:

    1. SUSTITUCION DE FUENTE. text() en OpenSCAD NO falla si la fuente no
       esta instalada: avisa por consola y pone otra. El DXF sale, parece
       bueno, y la pieza es otra. La huella de Franklin Gothic Medium con los
       parametros de params.scad son 10 CONTORNOS (K1 O2 N1 D2 O2 R2) y una
       caja de 216.87 x 32.44 mm.

    2. TRAZO MAS FINO QUE LA FRESA. Es un CAJEADO, o sea que la fresa tiene
       que entrar DENTRO del trazo de cada letra: un trazo mas estrecho que
       fresa_d no se puede vaciar. Se comprueba erosionando la palabra el
       radio de la fresa y contando trozos. Medido el 2026-08-24: Franklin
       Medium y Demi aguantan hasta fresa de 4 mm; Bahnschrift, Arial y
       Franklin Book se rompen ahi.

    guarda_fresado() en clearance_budget mira las ranuras y los concavos, no
    la palabra. Este es su hueco.
    """
    import clearance_budget as cb
    import numpy as np
    from matplotlib.path import Path as MPath
    from scipy import ndimage

    fallos: list[str] = []
    p = cb.leer_params()
    aristas, comps = _componentes("kondor_cajeado_2d")
    if len(comps) != 10:
        return [f"kondor: {len(comps)} contornos y se esperan 10 "
                f"(K1 O2 N1 D2 O2 R2). La fuente se sustituyo."]
    anillos = [_anillo(aristas, c) for c in comps]
    xs = [q[0] for a in anillos for q in a]
    ys = [q[1] for a in anillos for q in a]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if abs(w - 216.87) > 0.5 or abs(h - 32.44) > 0.5:
        fallos.append(f"kondor: caja {w:.2f} x {h:.2f} y se espera "
                      f"216.87 x 32.44. La fuente se sustituyo o cambio de "
                      f"version.")

    # Fresabilidad: rasterizar y erosionar el radio de la fresa.
    ESC = 4.0                                  # px por mm
    W, H = int(w * ESC) + 20, int(h * ESC) + 20
    yy, xx = np.mgrid[0:H, 0:W]
    px = xx / ESC + min(xs) - 10 / ESC
    py = yy / ESC + min(ys) - 10 / ESC
    pts = np.column_stack([px.ravel(), py.ravel()])
    dentro = np.zeros((H, W), dtype=int)
    for a in anillos:                          # par-impar: las contras restan
        dentro += MPath(a).contains_points(pts).reshape(H, W).astype(int)
    img = (dentro % 2) == 1
    r_px = int(round(p["fresa_d"] / 2 * ESC))
    ero = ndimage.binary_erosion(
        img, ndimage.generate_binary_structure(2, 1), iterations=r_px)
    # SE CALIBRA SOLO: se comparan los trozos ANTES y DESPUES de erosionar en
    # vez de contra un numero fijo. Si la palabra cambia -- otra fuente, otro
    # texto, otro cuerpo -- la referencia cambia con ella. Un numero magico
    # aqui se rompe en cuanto alguien toque kondor_size.
    _, antes = ndimage.label(img)
    _, despues = ndimage.label(ero)
    if despues != antes:
        fallos.append(
            f"kondor: la palabra son {antes} trozos y al erosionar el radio "
            f"de la fresa ({p['fresa_d']/2:g} mm) quedan {despues}: algun "
            f"trazo mide menos que la fresa y no se puede vaciar. Sube "
            f"kondor_size o pasa a una fuente con mas peso.")
    elif not fallos:
        print(f"  kondor_cajeado_2d: 10 contornos, {w:.2f} x {h:.2f} mm, y los "
              f"{antes} trozos sobreviven a la fresa de {p['fresa_d']:g} -- "
              f"fuente correcta y fresable")
    return fallos


# Paso del barrido con que se busca el punto mas desasistido del costado. 2 mm
# sobre una pieza de 309 x 256 son ~10 mil puntos dentro del contorno: el vano
# sale con +-1 mm, que sobra para una cota que hoy vale 119 y tiene el techo en
# 173. Bajarlo a 1 cuadruplica el tiempo y mueve el resultado 0.3 mm.
PASO_BARRIDO = 2.0
# Radio de contacto de la carga. Es el canto de una mano o la base de un pulgar
# apoyado, no una punta: con carga estrictamente puntual la teoria de placas da
# tension infinita y no dice nada util.
R_CONTACTO = 10.0
NU_PMMA = 0.37      # Poisson del PMMA colado
E_PMMA = 3000.0     # MPa. El mismo modulo con el que se acoto la trasera


def guarda_costado() -> list[str]:
    """El costado no se hunde con la mano entre sus anclajes.

    NACE EL 2026-08-25, con el retiro del entrepiso delantero. Ese larguero era
    el unico del case que no sostenia ninguna plancha -- las seis filas de M3
    van a base delantera, base trasera, valle y remate trasero -- asi que
    ninguna de las puertas de anclaje lo miraba: alineacion() y apoyo() solo
    ven filas de agujeros, y solapes() solo verifica disyuncion. Se podia
    retirar sin que nada se pusiera rojo, y eso es justo lo que hace peligroso
    el cambio, no el cambio.

    Lo que se pierde al quitar un larguero no es una fila de tornillos: es un
    ANCLAJE DEL COSTADO. El costado deja de tener cinco M5 y pasa a tener
    cuatro, y el parche de acrilico que queda sin apoyo crece.

    EL MODELO, declarado entero porque es la mitad del resultado: el parche
    desasistido se trata como PLACA CIRCULAR EMPOTRADA de radio a, donde a es
    la distancia del punto interior mas lejano a su ancla mas cercana.

        D = E t^3 / (12 (1 - v^2))
        flecha central   = P a^2 / (16 pi D)
        tension bajo la carga = 3P/(2 pi t^2) * [(1+v) ln(a/r0) + 1]

    Y SE MIDE SOBRE EL FICHERO: el contorno y los taladros salen de
    costado_2d.dxf, no de una copia de la geometria en Python. Por eso la
    puerta vive aqui y no en clearance_budget -- misma razon que
    _contorno_costado().

    EL APOYO CAMBIO DE NATURALEZA EL 2026-08-27, y con el esta puerta. Hasta
    entonces el costado colgaba de ANCLAS -- los M5 de larguero, cuatro puntos
    -- y el vano era la distancia al tornillo mas cercano. Se contaban solo los
    M5: los cuatro M4 de riel quedaban fuera a proposito, porque dos son ejes de
    giro y los otros dos tornillos DE MANO que el usuario quita para abrir, y un
    anclaje desmontable no es estructura.

    Ahora el costado no lleva un solo tornillo: queda ASENTADO EN EL REBAJE DEL
    ANILLO, y el labio lo sostiene hacia fuera por todo el perimetro. El vano
    deja de ser "distancia a un punto" y pasa a ser "distancia al canto de la
    ventana", que es apoyo continuo.

    Y EL 2026-08-27 EL APOYO LE LLEGA POR LA OTRA CARA. Con la inversion, la
    costilla pasa a ser la capa de FUERA y el acrilico queda por dentro: el
    marco ya no lo sostiene desde atras, lo PISA desde delante. Se mide contra
    costilla_2d.dxf -- el fichero, no una copia del offset en Python -- por la
    misma razon que el contorno.

    EL 2026-08-28 CAMBIA LA PIEZA PERO NO EL MODELO. El costado ya no se apila
    detras de una chapa: entra por detras en la ventana del anillo y asienta en
    su rebaje, coplanar. Lo que esta puerta mide es lo mismo -- distancia al
    canto de la ventana -- pero ese canto se movio: la banda de chapa media 27
    y la cara del anillo mide 20, o sea que la ventana es MAS GRANDE y el vano
    libre crece. Ese numero se anota en cada corrida y su techo lo sigue
    poniendo la flecha, no el gusto.

    Y EL 2026-08-28 LA PUERTA MIDE DOS VECES, porque el costado no se sujeta
    igual por las dos caras y hasta hoy solo se miraba una:

      HACIA FUERA  el labio del rebaje lo pisa por TODO el perimetro de la
                   ventana. Apoyo continuo, y el vano es la distancia al canto
                   de la ventana. Es el barrido de siempre.
      HACIA DENTRO no hay labio: entre la cara del PMMA y la cara interior del
                   anillo quedan 3 mm de aire, y por ahi el acrilico se sale
                   del rebaje. Lo unico que lo para son APOYOS PUNTUALES sobre
                   la cara interior -- las placas de anclaje, que corren tres
                   tramos enteros, y los clips de la Tarea 4 --, asi que el
                   vano es la distancia al apoyo mas cercano, no a un canto.

    Es la misma formula de placa circular con dos vanos distintos, y hoy manda
    el de FUERA: 69.4 mm contra 65.0 el de dentro.

    NO SIEMPRE FUE ASI, Y EL CAMBIO ES LA TAREA 4b. Del 27 al 28-08 el vano de
    dentro valia 95.5 mm y su punto peor caia en (292.8, 117.5), a menos de 1
    mm del canto TRASERO del acrilico -- 227 mm de canto sin un solo apoyo
    hacia dentro --, y ahi la formula de placa EMPOTRADA no vale: supone
    material sujeto alrededor del punto, y un canto libre no lo esta. Samuel
    eligio la salida (a) de las tres que la spec §10 dejaba abiertas y la
    ESCUADRA DE LA TRASERA se construyo: el canto trasero esta cogido por las
    dos caras en el 91 % de su largo libre, el punto peor se mudo a (221, 84)
    -- centro del panel, con material alrededor por los cuatro lados, que es
    donde el modelo SI vale -- y el vano de dentro bajo a 65.0.

    Lo que esta puerta hace es medir siempre los dos y dejar los numeros
    escritos en cada corrida.

    Lo que el esqueleto vale sigue siendo enorme contra el costado atornillado:
    el vano era 119.0 mm con cuatro anclas y la flecha 0.38.

    LO QUE NO CUBRE: el racking del cajon entero. Esta puerta mira UNA pieza
    plana. La rigidez del vano de 528 sigue siendo la heuristica que la spec
    no ha cerrado, y se cierra cargando el prototipo."""
    import clearance_budget as cb
    p = cb.leer_params()
    contorno = _contorno_costado()
    if not contorno:
        return ["costado_2d: sin contorno, no se puede medir el vano"]
    cantos = _cantos("costilla_2d")
    if not cantos:
        return ["costilla_2d: sin cantos, no se puede medir el apoyo del costado"]

    xs = [q[0] for a in contorno for q in a]
    ys = [q[1] for a in contorno for q in a]
    vano, donde = 0.0, (0.0, 0.0)
    y = min(ys)
    while y <= max(ys):
        x = min(xs)
        while x <= max(xs):
            if _dentro(contorno, (x, y)):
                d = _dist_al_contorno(cantos, (x, y))
                if d > vano:
                    vano, donde = d, (x, y)
            x += PASO_BARRIDO
        y += PASO_BARRIDO

    t = p["t_cheek"]
    D = E_PMMA * t ** 3 / (12 * (1 - NU_PMMA ** 2))
    P = p["carga_mano"]
    flecha = P * vano ** 2 / (16 * math.pi * D)

    # HACIA DENTRO el apoyo es PUNTUAL: placas y clips sobre la cara interior
    # del anillo, en los sitios donde asoman sobre la ventana. La mano empuja
    # hacia dentro y ahi el labio no ayuda -- pisa la cara de fuera del PMMA,
    # que es justo la que se separa de el.
    #
    # LOS APOYOS PASAN SU POLIGONO REAL y no su caja. Las tres placas van
    # giradas con su tramo (35 y 45 grados) y con una esquina honda cortada:
    # su AABB se mete hasta 20 mm de mas en el rincon del valle y en la punta
    # de la cara superior, o sea que el vano interior saldria optimista justo
    # donde el acrilico esta mas suelto. Los clips van a plomo y hoy su caja y
    # su poligono son la misma cosa, pero se piden a _clips() -- que es de
    # donde salen sus esquinas -- y no a _cajas_clip(): esa devuelve una caja
    # POR CARA, o sea el doble de apoyos con el mismo contorno, y con ella la
    # cuenta de esta lista no cuadraba con la que se imprime abajo.
    #
    # Y DESDE EL 2026-08-28 HAY UN APOYO MAS, que no es puntual: el ala B de la
    # ESCUADRA DE LA TRASERA. Corre 194.68 mm a lo largo del canto trasero del
    # acrilico y lo pisa 5.5 mm hacia dentro -- exactamente el trozo que el
    # labio pisa por fuera --, o sea que ese canto pasa de no tener nada a
    # estar cogido por las dos caras. Es LA pieza que la Tarea 4b existe para
    # poner, y este barrido es el numero que la juzga: antes de ella el peor
    # punto de dentro caia en (291, 116), a menos de 1 mm de ese canto libre,
    # que es donde la formula de placa empotrada no vale.
    #
    # Se pasa UNA por costado y solo su ala B: el ala A vive detras del canto
    # del acrilico (x >= 297.9) y no pisa un solo milimetro de PMMA.
    clips = cb._clips(p)
    ala_b = cb._escuadras_trasera(p)[0]["cajas"][1]
    escuadra = [(ala_b[1], ala_b[3]), (ala_b[2], ala_b[3]),
                (ala_b[2], ala_b[4]), (ala_b[1], ala_b[4])]
    apoyos = ([cb._esquinas_placa(pl) for pl in cb._placas(p)]
              + [q for _, q, _ in clips] + [escuadra])
    vano_in, donde_in = 0.0, (0.0, 0.0)
    y = min(ys)
    while y <= max(ys):
        x = min(xs)
        while x <= max(xs):
            if _dentro(contorno, (x, y)):
                d = min(_dist_al_apoyo(q, (x, y)) for q in apoyos)
                if d > vano_in:
                    vano_in, donde_in = d, (x, y)
            x += PASO_BARRIDO
        y += PASO_BARRIDO
    flecha_in = P * vano_in ** 2 / (16 * math.pi * D)
    sigma = (3 * P / (2 * math.pi * t ** 2)
             * ((1 + NU_PMMA) * math.log(vano / R_CONTACTO) + 1))
    # Vano que agotaria el techo de flecha, para que el mensaje diga cuanto
    # margen queda en la cota que de verdad se mueve.
    vano_max = math.sqrt(p["flecha_costado_max"] * 16 * math.pi * D / P)

    fallos = []
    if flecha > p["flecha_costado_max"]:
        fallos.append(
            f"costado_2d: con {P:.0f} N el costado se hunde {flecha:.2f} mm y "
            f"el techo son {p['flecha_costado_max']:.2f} (flecha_costado_max). "
            f"El vano sin apoyo vale {vano:.1f} mm en (x={donde[0]:.0f}, "
            f"y={donde[1]:.0f}) y el maximo que cabe son {vano_max:.1f}. Ya no "
            f"se arregla con un anclaje: el apoyo es la VENTANA del anillo, "
            f"asi que o se ensancha cara_anillo o sube t_cheek (la flecha va "
            f"con t^3)")
    if flecha_in > p["flecha_costado_max"]:
        fallos.append(
            f"costado_2d: empujado hacia DENTRO se hunde {flecha_in:.2f} mm "
            f"(vano {vano_in:.1f} en x={donde_in[0]:.0f}, y={donde_in[1]:.0f}) "
            f"contra {p['flecha_costado_max']:.2f}. Hacia dentro lo paran las "
            f"placas y los clips: falta un clip cerca de ese punto")
    if sigma > cb.SIGMA_PMMA:
        fallos.append(
            f"costado_2d: {sigma:.1f} MPa bajo la mano contra el umbral de "
            f"{cb.SIGMA_PMMA} (#106) — esto no deberia pasar antes que la "
            f"flecha, asi que revisa t_cheek y carga_mano antes de creerlo")
    print(f"costado: PIEL sin tornillos, asentada en el rebaje del anillo; "
          f"vano libre {vano:.1f} mm "
          f"(x={donde[0]:.0f}, y={donde[1]:.0f}); con {P:.0f} N se hunde "
          f"{flecha:.2f} mm (techo {p['flecha_costado_max']:.2f}, vano maximo "
          f"{vano_max:.0f}) y trabaja a {sigma:.1f} MPa (fluencia "
          f"{cb.SIGMA_PMMA})")
    print(f"  hacia DENTRO lo paran {len(apoyos)} apoyos "
          f"({len(apoyos) - len(clips) - 1} placas + {len(clips)} clips + la "
          f"escuadra de la trasera, por costado): vano interior {vano_in:.1f} "
          f"mm (x={donde_in[0]:.0f}, y={donde_in[1]:.0f}) y se hunde "
          f"{flecha_in:.2f} mm (techo {p['flecha_costado_max']:.2f}, vano "
          f"maximo {vano_max:.0f})")
    return fallos


# Cuanto se le tolera al ancho de la cara del anillo, medido del DXF. No es
# tolerancia de fabricacion: offset() es exacto y los 47 vertices de la ventana
# salieron entre 19.9994 y 20.0069 de la silueta. Es el ruido de la
# poligonalizacion de las curvas, y nada mas.
CARA_DXF_MAX = 0.1


def anillo_tiene_ventana() -> list[str]:
    """El DXF de la costilla es un ANILLO, y su cara mide lo que dice params.

    NACE DE UN TEST DE ROTURA QUE NO ROMPIO (2026-08-28). El plan pedia quitar
    la ventana de costilla_2d() y esperaba ROJO en guarda_costado() o en
    cuerpos_dentro_del_anillo(). Las dos siguieron VERDES, y cada una tiene su
    razon: la silueta EXTERIOR no se mueve al quitar la ventana, asi que los
    cuerpos siguen cabiendo y el sobre mide exactamente lo mismo; y el vano
    libre del acrilico solo sube de 69.4 a 89.4 mm, porque su canto de apoyo
    pasa a ser la silueta, que esta 14.5 mm mas afuera -- lejos todavia del
    techo de 150.

    O sea que una PLETINA MACIZA de 307 x 256 pasaba entera: el doble de
    aluminio, sin ventana por donde se vea el acrilico y sin sitio donde
    meterlo. Es el fallo que este fichero ya conoce de otras veces -- un DXF
    valido e inservible -- y el bbox no lo puede ver, porque no cambia.

    SE MIDE LA CARA, no la envolvente de la ventana. La ventana encoge el bbox
    45 mm en X y 40 en Y, no 2 x cara_anillo, porque los vertices en punta se
    resuelven a inglete y el interior se mete mas: comparar cajas daria una
    puerta que grita en falso en cuanto alguien toque un radio. Lo que si es
    exacto en un offset() es la DISTANCIA: cada vertice de la ventana esta a
    cara_anillo de la silueta. Eso es ademas la cota que le importa al taller y
    a Samuel -- el ancho del metal que se ve."""
    import clearance_budget as cb

    p = cb.leer_params()
    aristas, comps = _componentes("costilla_2d")
    if not aristas:
        return ["costilla_2d: sin LINEs, no se puede verificar la ventana"]
    if len(comps) != 2:
        return [f"costilla_2d: {len(comps)} contorno(s) cerrado(s) y un anillo "
                f"tiene DOS, silueta y ventana. Con uno solo es una pletina "
                f"maciza: el doble de aluminio, nada que ver y ningun sitio "
                f"donde asiente el acrilico"]
    ancho = lambda cm: (max(q[0] for j in cm for q in aristas[j])
                        - min(q[0] for j in cm for q in aristas[j]))
    ventana, silueta = sorted(comps, key=ancho)
    canto = [aristas[j] for j in silueta]
    ds = [_dist_al_contorno(canto, q) for j in ventana for q in aristas[j]]
    peor = max(ds, key=lambda d: abs(d - p["cara_anillo"]))
    if abs(peor - p["cara_anillo"]) > CARA_DXF_MAX:
        return [f"costilla_2d: la cara del anillo mide {peor:.2f} mm en su "
                f"punto peor y cara_anillo dice {p['cara_anillo']:g}. O la "
                f"ventana se dibujo con otro offset, o alguien le metio mano "
                f"al contorno: lo que se ve del case es este ancho"]
    print(f"  costilla_2d: anillo de cara {min(ds):.2f}..{max(ds):.2f} mm "
          f"(cara_anillo {p['cara_anillo']:g}) entre silueta y ventana")
    return []


def anillo_tiene_rebaje() -> list[str]:
    """El DXF del DORSO es el contorno del REBAJE, retirado lo que dice params.

    HERMANA DE anillo_tiene_ventana(), y nace del mismo agujero. El dorso solo
    lo miraba su SOBRE, con TOL = 4 mm: eso deja pasar un retiro entre 12 y 16
    sin decir nada, y sobre todo deja pasar que alguien exporte ahi la silueta
    entera o la ventana en vez del rebaje -- las tres son contornos parecidos y
    ninguna caja las distingue. Un DXF valido e inservible otra vez.

    Se mide la DISTANCIA, no la caja, por lo mismo que alli: offset() es
    exacto en la distancia y no en el bbox, porque los vertices en punta se
    resuelven a inglete. Y la silueta contra la que se mide se relee del OTRO
    fichero, costilla_2d.dxf, que es donde vive: el dorso no la lleva dibujada
    -- si la llevara, la fresa se comeria el contorno de la pieza."""
    import clearance_budget as cb

    p = cb.leer_params()
    rebaje = _contorno_exterior("costilla_dorso_2d")
    silueta = _contorno_exterior("costilla_2d")
    if not rebaje or not silueta:
        return ["costilla_dorso_2d: sin LINEs en el dorso o en la cara, no se "
                "puede medir el retiro del rebaje"]
    retiro = p["cara_anillo"] - p["rebaje_anillo"]
    ds = [_dist_al_contorno(silueta, q) for a in rebaje for q in a]
    peor = max(ds, key=lambda d: abs(d - retiro))
    if abs(peor - retiro) > CARA_DXF_MAX:
        return [f"costilla_dorso_2d: el contorno del rebaje corre a {peor:.2f} mm "
                f"de la silueta en su punto peor y cara - rebaje dice "
                f"{retiro:g}. O no es el rebaje lo que se exporto ahi, o el "
                f"offset cambio: la franja donde asientan las placas es "
                f"justamente esta distancia"]
    print(f"  costilla_dorso_2d: rebaje a {min(ds):.2f}..{max(ds):.2f} mm de la "
          f"silueta (cara {p['cara_anillo']:g} - rebaje {p['rebaje_anillo']:g} "
          f"= {retiro:g})")
    return []


def seccion_del_cupon() -> list[str]:
    """El DXF de la seccion del anillo dice las PROFUNDIDADES, y dice las del
    anillo que se va a cortar.

    ES EL UNICO PLANO QUE LAS PUEDE DECIR (#237). Los otros dos ficheros del
    anillo son vistas de planta: anillo_tiene_ventana() cruza cara_anillo
    releyendo costilla_2d y anillo_tiene_rebaje() cruza cara - rebaje
    releyendo costilla_dorso_2d, o sea que las cotas EN EL PLANO ya estan
    atadas al fichero que se corta. Las otras tres -- pletina de t_anillo,
    labio de rehundido_acrilico, chaflan de chaflan_anillo -- no salen en
    ninguna planta y hasta hoy vivian solo en params.scad y en la prosa del
    PLIEGO. El cupon existe justamente para medirlas sobre metal, y sin un
    plano de la seccion lo que llegaria al taller seria un parrafo.

    Se comprueba la seccion ENTERA por sus ocho vertices y no dimension a
    dimension: un poligono con los ocho puntos donde toca es la seccion, y
    ademas caza los dos errores que una lista de cotas no caza -- el chaflan
    dibujado en una sola arista (costilla() los pone en las DOS: offset(-f)
    sobre la silueta y offset(-cara + f) sobre la ventana) y el rebaje
    dibujado desde la cara vista en vez de desde el dorso, que da un fichero
    valido, con las mismas cotas, y un perfil que es otro.

    Lo que este fichero NO dice, y por eso va en la nota del pliego: el largo
    del cupon (cupon_largo), la rosca ciega M4 a media altura y el punto de
    bonding enmascarado. Un DXF de seccion no sabe decir cuanto mide la pieza
    a lo largo, igual que uno de planta no sabe decir a que profundidad."""
    import clearance_budget as cb

    p = cb.leer_params()
    c, W = p["chaflan_anillo"], p["cara_anillo"]
    T, R, B = p["t_anillo"], p["rehundido_acrilico"], p["rebaje_anillo"]
    esperados = [(c, 0.0), (W - c, 0.0), (W, c), (W, R),
                 (W - B, R), (W - B, T), (0.0, T), (0.0, c)]
    aristas, comps = _componentes("cupon_anillo_2d")
    if len(comps) != 1:
        return [f"cupon_anillo_2d: {len(comps)} contorno(s) y la seccion del "
                f"anillo es UNO cerrado de ocho lados"]
    pts = {(round(q[0], 3), round(q[1], 3)) for j in comps[0] for q in aristas[j]}
    f: list[str] = []
    nombres = ["arranque del chaflan de la silueta", "arranque del chaflan de "
               "la ventana", "final del chaflan de la ventana",
               "canto del labio", "asiento del rebaje", "fondo del rebaje",
               "dorso en la silueta", "final del chaflan de la silueta"]
    for (x, y), nm in zip(esperados, nombres):
        if not any(math.hypot(q[0] - x, q[1] - y) <= DESVIO_DXF_MAX for q in pts):
            f.append(f"cupon_anillo_2d: falta el vertice '{nm}' en "
                     f"({x:.2f}, {y:.2f}): el perfil dibujado no es el que "
                     f"fresa costilla()")
    if len(pts) != len(esperados):
        f.append(f"cupon_anillo_2d: {len(pts)} vertices y la seccion tiene "
                 f"{len(esperados)}")
    if not f:
        print(f"  cupon_anillo_2d: seccion de {W:g} x {T:g}, labio de {R:g}, "
              f"rebaje {B:g} x {T - R:g}, chaflan {c:g} x 45 en las dos "
              f"aristas de la cara -- cupon de {p['cupon_largo']:g} mm")
    return f


def taladros_anillo() -> list[str]:
    """Las roscas ciegas del anillo estan en el dorso, donde el modelo dice,
    con material alrededor y dentro de la FRANJA.

    NADA ATRAVIESA LA CARA VISTA desde el 2026-08-28. Rieles, miembros y clips
    se atornillan por la cara interior a roscas ciegas de 10 mm en la pletina
    de 14. Los centros salen en costilla_dorso_2d a diametro de BROCA (M4 3.3;
    todas son M4) y la profundidad va en el pliego.

    Dos cantos mandan, y solo UNO esta en este fichero: el contorno del
    REBAJE, porque mas adentro de el solo quedan 3 mm de labio y una rosca
    ahi sale por la cara vista. El otro -- la silueta -- no se dibuja en el
    dorso (dibujarla seria mandar fresar el contorno de la pieza), asi que de
    ese lado responde guarda_anclajes() contra el perfil, y de que el rebaje
    este donde toca responde anillo_tiene_rebaje() releyendo la otra hoja.
    Entre las tres queda cubierto el sandwich entero."""
    import clearance_budget as cb

    p = cb.leer_params()
    esperados = cb._centros_rosca_ciega(p)
    leidos = _redondos("costilla_dorso_2d")
    cantos = _cantos("costilla_dorso_2d")
    if not cantos:
        return ["costilla_dorso_2d: sin LINEs, no se pueden verificar las roscas"]
    f: list[str] = []
    for nm, c, d in esperados:
        cerca = [q for q in leidos
                 if math.hypot(q[0] - c[0], q[1] - c[1]) <= DESVIO_DXF_MAX
                 and abs(q[2] - d) < 0.1]
        if not cerca:
            f.append(f"costilla_dorso_2d: falta la rosca ciega de '{nm}' "
                     f"(broca {d:.1f}) en ({c[0]:.2f}, {c[1]:.2f})")
            continue
        dist = _dist_al_contorno(cantos, c)
        if dist < BORDE_MIN_D * d:
            f.append(f"costilla_dorso_2d: la rosca de '{nm}' cae a {dist:.2f} mm "
                     f"del contorno del rebaje y se exige "
                     f"{BORDE_MIN_D * d:.2f}. Fuera de la franja solo hay labio "
                     f"de 3: por ahi la rosca sale por la cara vista")
    if len(leidos) != len(esperados):
        f.append(f"costilla_dorso_2d: {len(leidos)} circulos y el modelo pone "
                 f"{len(esperados)} roscas ciegas")
    if not f:
        print(f"  costilla_dorso_2d: {len(esperados)} roscas ciegas en la franja, "
              f"todas con 1.5 D al rebaje")
    return f


def ranuras_rejilla_entrada() -> list[str]:
    """Las ranuras de la rejilla de entrada estan CORTADAS en la trasera, donde
    el modelo las pone y con el largo con que guarda_aire() las cuenta.

    LA GEMELA ESTABA POR LECTURA, Y ESO NO ES UNA GEMELA (#236). El area de
    entrada de aire la calcula _rejilla_entrada() en Python a partir de una
    lista de columnas que el .scad vuelve a derivar por su cuenta en
    rejilla_entrada(); check_dxf solo censaba CIRCULOS (_redondos deja fuera
    todo lo que no sea cuadrado dentro de una decima) y una ranura es obround.
    O sea que el unico numero que cruzaba los dos lenguajes era el que un
    humano contaba a mano: el 2026-08-28, al saltarse la rejilla la columna que
    tapa el ala de la escuadra, se comprobo contando LINEs del fichero
    (3418 -> 3368) y ahi se quedo. Un filtro nuevo en cualquiera de los dos
    lados -- y ya van dos, el IEC y la escuadra -- se lleva por delante area de
    ventilacion sin que nada lo cante.

    Tres cosas, y las tres juntas cierran el area que usa guarda_aire():
      1. hay una ranura por CADA columna que _columnas_rejilla_entrada()
         adjudica, en su x, y ninguna de mas (las de mas serian columnas que
         un filtro dice que no se cortan y el DXF corta igual);
      2. cada una mide vent_ancho_ranura + kerf de ancho -- el ancho es la
         mitad del area y ademas lo que fija vent_puente_min;
      3. cada una mide la banda libre entera de alto y esta centrada en ella.
    Con (1), (2) y (3) el area del presupuesto termico deja de ser un numero
    de fe: es n x largo x ancho, y los tres salen del fichero que se corta.

    La firma con que se reconoce una ranura es su caja: ancho estrecho y
    fijo, alto de decenas de mm. En este DXF no la comparte nada -- los M3
    son 3.4 x 3.4, las dos ondas pasan de 140 de ancho, la ventana del IEC es
    48 x 27.5 y el contorno mide 540 x 255 --, asi que el filtro no puede
    confundirse de pieza. Si algun dia se le pareciera algo, el assert de
    cantidad lo cantaria por exceso antes que por defecto."""
    import clearance_budget as cb

    p = cb.leer_params()
    xs, y0, y1 = cb._columnas_rejilla_entrada(p)
    w_esp = p["vent_ancho_ranura"] + p["kerf"]
    h_esp = y1 - y0
    # y0 del DXF: plancha() arranca en el origen y rejilla_entrada() centra la
    # ranura en (y0 + y1)/2 con la banda ya medida desde el canto de abajo de
    # la plancha, que es y = 0 en las dos gemelas (ver _rejilla_entrada()).
    yc_esp = (y0 + y1) / 2
    aristas, comps = _componentes("piel_trasera_2d")
    if not aristas:
        return ["piel_trasera_2d: sin LINEs, no se pueden contar las ranuras"]
    # LA FIRMA NO MIRA EL ANCHO, y no es descuido: si filtrara por ancho, una
    # ranura mal dibujada dejaria de parecer ranura y el fallo saldria como
    # "falta la ranura" en las 44 -- verdadero, pero apuntando al sitio
    # equivocado. Reconocer por ALTO (que lo marcan los dos centros del hull y
    # es exacto) y por "mas estrecha que 8" deja que el ancho lo juzgue un
    # assert que sabe decir cuanto se desvio. En este fichero eso identifica la
    # pieza sin ambiguedad: los M3 miden 3.4 de alto, las ondas 31.75, la
    # ventana del IEC 27.5 y el contorno 254.68.
    leidas = []
    for comp in comps:
        px = [q[0] for j in comp for q in aristas[j]]
        py = [q[1] for j in comp for q in aristas[j]]
        w, h = max(px) - min(px), max(py) - min(py)
        if abs(h - h_esp) <= 0.1 and w < 8:
            leidas.append(((min(px) + max(px)) / 2, (min(py) + max(py)) / 2, w, h))
    f: list[str] = []
    for x in xs:
        cerca = [q for q in leidas if abs(q[0] - x) <= DESVIO_DXF_MAX]
        if not cerca:
            f.append(f"piel_trasera_2d: falta la ranura de entrada en x={x:.2f} "
                     f"(la adjudica _columnas_rejilla_entrada y el DXF no la corta)")
            continue
        _, yc, w, h = cerca[0]
        if abs(yc - yc_esp) > DESVIO_DXF_MAX:
            f.append(f"piel_trasera_2d: la ranura de x={x:.2f} esta centrada en "
                     f"y={yc:.2f} y la banda libre en y={yc_esp:.2f}")
        if abs(w - w_esp) > 0.05:
            f.append(f"piel_trasera_2d: la ranura de x={x:.2f} mide {w:.2f} de "
                     f"ancho y vent_ancho_ranura + kerf es {w_esp:.2f}")
    if len(leidas) != len(xs):
        f.append(f"piel_trasera_2d: {len(leidas)} ranuras de entrada en el "
                 f"fichero y el modelo adjudica {len(xs)}: guarda_aire() cuenta "
                 f"area que no se corta (o se corta area que no cuenta)")
    if not f:
        area = cb._area_ranuras(len(xs), h_esp, w_esp)
        print(f"  piel_trasera_2d: {len(xs)} ranuras de entrada de "
              f"{h_esp:.1f} x {w_esp:.2f} mm en su sitio, {area:.0f} mm2 de "
              f"entrada que SI estan cortados")
    return f


def taladros_placas() -> list[str]:
    """Las placas de anclaje y los clips traen sus taladros donde el modelo
    dice, con material alrededor.

    HERMANA DE taladros_anillo() PERO DEL OTRO LADO: aquella releia el DORSO
    del anillo -- las roscas ciegas donde placas y clips se atornillan. Esta
    relee las PLACAS Y EL CLIP en si, que hasta la Tarea 6 (controller) eran
    solidos del modelo sin DXF de corte: placas() y clips() dibujaban la
    pieza que el render ensena, pero nadie mandaba fresar esa pieza -- salia
    del taller como si no existiera.

    CADA PLACA LLEVA TRES CLASES DE TALADRO, y las tres se comprueban:
      1. el par de M4 CIEGOS a la placa la ata al anillo -- roscas_placa(),
         diametro de PASO (d_M4_paso).
      2. el PASO M4 de cada riel que la placa recoge -- pl[8], diametro
         d_M4_paso. FIX ROUND 1 (Tarea 6): esta puerta pidio primero
         d_cajeado_riel (8) aqui, porque la primera version de placa_2d()
         en el .scad dibujaba el CAJEADO en vez del agujero que de verdad
         sujeta el tornillo del riel -- una pieza que habria salido del
         taller sin donde meter el tornillo. El cajeado (Ø8 x
         prof_cajeado_riel, por el lado del anillo) sigue existiendo en la
         pieza real, pero es NOTA DE MECANIZADO en PLIEGO.md, no un circulo
         en este DXF: un DXF 2D no sabe decir profundidad.
      3. SOLO LA DEL VALLE: el M3 de la pestana de la banda
         (roscas_placa_valle()/_m3_pestana) y el M4 de cada lengueta de la
         bahia (_bridas() con ancla == "placa") -- DOS, una por ala
         (delantera y trasera), no cuatro: cada lengueta lleva un solo M4
         roscado en la placa (ver la nota de _bridas() en clearance_budget.py
         y el BOM, "tornillo M4 x4 -- las dos lenguetas de la BAHIA", que
         cuenta las DOS placas del case, no los taladros de esta).

    LA REGLA DE CANTO ES LA MISMA QUE guarda_anclajes() YA APLICA EN 3D
    (_dist_al_poligono contra las esquinas reales de la placa, minimo 1.5 D)
    -- aqui se repite releyendo el FICHERO, con _cantos() en vez de la copia
    en Python, por la misma razon que taladros_anillo() no confia en el
    offset() de sam17_case.scad: la version que cuenta es la que el laser va
    a ver.

    EL CLIP ES MAS SIMPLE: una pieza generica (no depende de tramo ni de s),
    un solo M4 de paso centrado, a 1.5 D de sus cuatro cantos.

    CADA DXF SE GUARDA SI NO EXISTE TODAVIA: la puerta de _sobres()/main() ya
    dice "FALTA el DXF" por su cuenta, y leer aqui un fichero que no esta en
    disco seria un traceback (FileNotFoundError de ezdxf) en vez de un ROJO
    legible -- justo lo que esta puerta existe para evitar."""
    import clearance_budget as cb

    p = cb.leer_params()
    f: list[str] = []
    cajas_miembro = None
    for nombre, dxf in PLACAS_DXF.items():
        if not (PLANS / f"{dxf}.dxf").exists():
            continue
        pl = next(pl for pl in cb._placas(p) if pl[0] == nombre)
        cantos = _cantos(dxf)
        if not cantos:
            f.append(f"{dxf}: sin LINEs, no se puede verificar la placa")
            continue
        # (etiqueta, centro, d_leido, d_canto). d_leido es lo que _redondos()
        # tiene que encontrar dibujado; d_canto es CON QUE D se multiplica
        # BORDE_MIN_D, y las dos NO siempre son la misma cota -- el caso que
        # queda es el M3 de pestana (dibujado a d_M3_rosca, canto a
        # d_M3_paso, mas abajo). Para el paso M4 de riel las dos coinciden:
        # el DXF dibuja el agujero de PASO (FIX ROUND 1: no el cajeado, ver
        # el .scad), y el canto que le exige guarda_anclajes() en 3D -- y
        # RFQ.md (S "Preguntas de cota", el M4 de brida a 6.75 mm, "el minimo
        # exigido, 1.5 diametros del M4 de paso, sin margen de sobra") -- es
        # el de ese mismo diametro: 1.5 x d_M4_paso, 6.75 mm.
        esperados = [(f"M4 ciego '{nm}'", c, p["d_M4_paso"], p["d_M4_paso"])
                     for nm, c in cb._roscas_placa(p, pl)]
        esperados += [(f"paso M4 de riel @ s={e[0]:.1f}", e[1],
                       p["d_M4_paso"], p["d_M4_paso"])
                      for e in pl[8]]
        if nombre == "valle":
            # MISMA COTA DE CANTO QUE guarda_anclajes(): d_M3_paso (3.4), no
            # d_M3_rosca (2.5) -- el diametro DIBUJADO en la placa si es
            # d_M3_rosca (rosca pasante, ver roscas_placa_valle() en el
            # .scad), pero el margen de canto se mide con el paso, otra vez
            # por lo mismo: `assert d_m3 >= 1.5 * p["d_M3_paso"]` en
            # clearance_budget.py.
            esperados.append(("M3 pestana valle", cb._m3_pestana(p),
                              p["d_M3_rosca"], p["d_M3_paso"]))
            if cajas_miembro is None:
                P = cb._vertices(p)
                cajas_miembro = cb._cajas_miembro(p, P, cb._centros_rail(p, P),
                                                   0.0, 0.0)
            # LAS DOS LENGUETAS DE LA BAHIA: guarda_anclajes() solo las mide
            # contra el canto de su propia BRIDA (la chapa doblada), nunca
            # contra el de esta placa -- son dos piezas de metal distintas y
            # cada una puede rajarse por su lado. Esta puerta anade la mitad
            # que faltaba, la de la placa, con el mismo d_M4_paso de canto
            # que el resto de la familia M4.
            esperados += [(nm_b, c, p["d_M4_rosca"], p["d_M4_paso"])
                          for nm_b, _, centros, ancla
                          in cb._bridas(p, cajas_miembro)
                          if ancla == "placa" for c in centros]
        leidos = _redondos(dxf)
        for etiqueta, c, d, d_canto in esperados:
            cerca = [q for q in leidos
                     if math.hypot(q[0] - c[0], q[1] - c[1]) <= DESVIO_DXF_MAX
                     and abs(q[2] - d) < 0.1]
            if not cerca:
                f.append(f"{dxf}: falta el taladro '{etiqueta}' (d={d:.2f}) "
                         f"en ({c[0]:.2f}, {c[1]:.2f})")
                continue
            dist = _dist_al_contorno(cantos, c)
            # - DESVIO_DXF_MAX: las dos lenguetas de la bahia viven EXACTO en
            # el limite por diseno -- placa_1u_fondo() en clearance_budget.py
            # se define como "donde cae su M4 mas 1.5 D de canto", o sea que
            # el margen real es CERO a proposito, no un descuido. Medido:
            # 6.749931 mm contra un umbral de 6.75 -- 69 NANOMETROS de sobra
            # que el redondeo de $fn en el arco de la placa y el viaje por
            # DXF/ezdxf se comen. Es el mismo fenomeno que ya vive en este
            # fichero (EPS de cuerpos_dentro_del_anillo(), la nota de
            # dist_rosca_ciega sobre "vive del redondeo de coma flotante") y
            # se trata igual: una tolerancia, no un canto mas generoso.
            if dist < BORDE_MIN_D * d_canto - DESVIO_DXF_MAX:
                f.append(f"{dxf}: el taladro '{etiqueta}' cae a {dist:.2f} mm "
                         f"del canto y se exigen {BORDE_MIN_D * d_canto:.2f} "
                         f"({BORDE_MIN_D} x D)")
        if len(leidos) != len(esperados):
            f.append(f"{dxf}: {len(leidos)} agujeros en el DXF y el modelo "
                     f"pone {len(esperados)}")
        elif not any(m.startswith(dxf + ":") for m in f):
            print(f"  {dxf}: {len(leidos)} taladros verificados, todos a "
                  f">= {BORDE_MIN_D}xD del canto")
    if (PLANS / "clip_2d.dxf").exists():
        cantos = _cantos("clip_2d")
        if not cantos:
            f.append("clip_2d: sin LINEs, no se puede verificar el clip")
        else:
            leidos = _redondos("clip_2d")
            if len(leidos) != 1:
                f.append(f"clip_2d: {len(leidos)} agujeros en el DXF y el "
                         f"modelo pone 1")
            else:
                cx, cy, d = leidos[0]
                if abs(d - p["d_M4_paso"]) > 0.1:
                    f.append(f"clip_2d: el agujero mide d={d:.2f} y se "
                             f"espera d_M4_paso={p['d_M4_paso']:.2f}")
                dist = _dist_al_contorno(cantos, (cx, cy))
                minimo = BORDE_MIN_D * p["d_M4_paso"]
                if dist < minimo:
                    f.append(f"clip_2d: el agujero cae a {dist:.2f} mm del "
                             f"canto y se exigen {minimo:.2f} ({BORDE_MIN_D} x D)")
                elif not any(m.startswith("clip_2d:") for m in f):
                    print(f"  clip_2d: 1 taladro d_M4_paso a {dist:.2f} mm "
                          f"del canto (>= {minimo:.2f})")
    return f


def cuerpos_dentro_del_anillo() -> list[str]:
    """Cada riel y miembro tiene que caber DENTRO de la silueta del anillo.

    Esto no lo miraba nadie. `solapes()` compara railes contra railes y contra
    planchas, o sea cuerpo contra cuerpo: un rail que se sale por el borde no
    solapa con NADA y pasa en verde. Y la comprobacion se volvio urgente al
    redondear las esquinas en punta, porque el redondeo QUITA material justo
    donde viven dos largueros (el de la base delantera se apoya en el rincon
    del frente, que es el que mas radio se come).

    SE LLAMO railes_dentro_del_costado() Y MEDIA CONTRA EL ACRILICO hasta el
    2026-08-28. Cambia el contorno de referencia, no el criterio: el acrilico
    dejo de ser la silueta del case -- va retranqueado 14.5 mm dentro de la
    ventana del anillo -- y medir contra el habria acusado de salirse a los
    cuerpos que en realidad pasan por delante del anillo, que es donde de
    verdad tienen que caber. La pieza que da la silueta es la costilla.

    Se valida contra el CONTORNO RELEIDO DEL DXF, no contra una copia de la
    funcion redondear() en Python. Es a proposito: replicarla aqui es la
    tercera copia de la misma matematica, y la version que cuenta es la que
    salio al archivo que va al taller. Los centros y los angulos si vienen del
    budget -- el DXF sabe donde estan los agujeros pero no que rail es cual ni
    cuanto va girado."""
    import clearance_budget as cb

    f: list[str] = []
    contorno = _contorno_exterior("costilla_2d")
    if not contorno:
        return ["costilla_2d: sin LINEs, no se puede verificar el contorno"]

    def dentro(pt) -> bool:
        return _dentro(contorno, pt)

    p = cb.leer_params()
    P = cb._vertices(p)
    cr = cb._centros_rail(p, P)
    miembros = cb._cajas_miembro(p, P, cr, 0.0, 0.0)
    # Los railes de PANEL van girados con su cara; los de esqueleto, a plomo.
    # El signo del giro es -angulo, igual que en el modulo rails() del .scad:
    # un cuadrado girado -49 grados deja un par de caras a +41 del eje X, que
    # es justo la inclinacion de una cara a 49 grados DE LA VERTICAL. Con el
    # signo al reves la comprobacion acusaba a los cuatro railes de panel de
    # salirse -- eran falsos positivos, y con el signo bueno se ve que su cara
    # queda a 1.63 mm del plano del panel, o sea el t_panel de diseno.
    # Cada elemento aporta sus CUATRO ESQUINAS ya en coordenadas del perfil. Los
    # rieles de panel son el EUROrack real, girado con su cara; los miembros de
    # chapa pasan sus cajas. La bahia pasa sus tres cajas fisicas por separado:
    # rellenar su envolvente esconderia que el centro es aire.
    #
    # Aqui estan los SEIS railes de panel: los cuatro 3U y los dos horizontales
    # de la fila 1U, todos fijados de punta a la costilla.
    # cerrada, la tapa vive dentro del contorno como todo lo demas, y que ese
    # riel quepa en el vertice es justo la cota que obligo a engordar
    # marco_remate a 16. No hay ningun cuerpo excluido -- la bisagra que asomaba
    # por diseno ya no existe: el eje es el propio M5 del riel.
    cuerpos = [(n, cb._esquinas_er(p, c, p[a]))
               for n, c, a in zip(cb.NOMBRES_CR, cr, cb.ANGS_CR)]
    bahia = cb._envolvente_bahia(miembros)
    cuerpos += [(f"fila 1U {i}", cb._esquinas_er(p, c, 90.0))
                for i, c in enumerate(cb._centros_rail_1u(p, P, bahia))]
    cuerpos += [(n, [(c[x], c[y])
                     for x in (1, 2) for y in (3, 4)])
                for n, c in miembros.items()]
    # LAS PLACAS Y LAS BRIDAS entran el 2026-08-28, y esta es LA puerta que
    # dice donde acaban. Una placa corre el tramo entero pegada a la silueta:
    # si su extremo se pasa de la tangente del redondeo, la esquina se sale por
    # fuera del contorno y no lo caza nadie mas -- solapes() compara cuerpo
    # contra cuerpo y una placa que asoma por el borde no choca con nada. En
    # HEAD dos esquinas de placa asomaban 0.59 y 0.71 mm y las dos puertas
    # daban verde. Las placas pasan su POLIGONO REAL, chaflan incluido.
    cuerpos += [(f"placa {pl[0]}", cb._esquinas_placa(pl))
                for pl in cb._placas(p)]
    cuerpos += [(f"brida {n}", [(x, y) for x in (x0, x1) for y in (y0, y1)])
                for n, (x0, x1, y0, y1), _, _ in cb._bridas(p, miembros)]
    # LOS CLIPS, por lo mismo que las placas: van pegados a la silueta y su
    # sitio a lo largo del tramo es un numero escrito a mano en TRAMOS_CLIP.
    # Correr uno hacia una esquina para librar una brida -- que es justo lo que
    # pide su vecindario -- lo mete en el redondeo y se sale por el borde, y
    # solapes() no lo ve porque un cuerpo que asoma por fuera no choca con
    # nada.
    cuerpos += [(f"clip {n}", q) for n, q, _ in cb._clips(p)]
    # LAS DOS ALAS DE LA ESCUADRA, por lo mismo: van pegadas al canto trasero
    # -- el ala A a 8 mm de la silueta, que es el espesor de la trasera -- y su
    # largo lo fijan las bridas de los miembros, o sea que crece hacia las dos
    # esquinas donde el redondeo se come material. Se pasa la del lado 0: la
    # del 1 es su espejo en z y en el plano del perfil son la misma.
    cuerpos += [(c[0], [(c[1], c[3]), (c[2], c[3]), (c[2], c[4]), (c[1], c[4])])
                for c in cb._escuadras_trasera(p)[0]["cajas"]]
    # Varios largueros van A RAS del contorno por diseno (los de la cara
    # trasera tienen su centro en prof_inferior - r, o sea que su cara de atras
    # coincide con el plano trasero; los de la base apoyan en y=0). Un punto
    # exactamente sobre la arista no lo decide el ray casting, asi que la
    # esquina se prueba tirada EPS hacia el centro del rail: a ras pasa, y
    # cualquier salida real es mucho mayor que EPS.
    EPS = 0.05
    for nombre, esquinas in cuerpos:
        cx = sum(e[0] for e in esquinas) / len(esquinas)
        cy = sum(e[1] for e in esquinas) / len(esquinas)
        for ex, ey in esquinas:
            largo = math.hypot(ex - cx, ey - cy)
            esq = (cx + (ex - cx) * (largo - EPS) / largo,
                   cy + (ey - cy) * (largo - EPS) / largo)
            if not dentro(esq):
                f.append(f"costilla_2d: el cuerpo '{nombre}' se sale de la "
                         f"silueta -- esquina ({ex:.1f}, {ey:.1f}) fuera del "
                         f"contorno (centro {cx:.1f}, {cy:.1f})")
                break
    if not f:
        print(f"  costilla_2d: los {len(cuerpos)} cuerpos caben dentro de la "
              f"silueta ({len(contorno)} aristas de perimetro)")
    return f


def chasis_agujeros() -> list[str]:
    """Las tres chapas de acero traen todos sus agujeros.

    El sobre no lo ve: un agujero que desaparece no mueve el contorno ni un
    milimetro, y el fichero sigue siendo valido. Ya paso una vez en este repo
    -- la pestana perdio sus cinco M3 y quedo en un rectangulo perfecto de 378
    bytes. Aqui duele mas que en el acrilico: la fila de los TO-220 ES la
    refrigeracion (Tj de U2, 101 -> 61 C) y el M4 del esparrago ES la tierra de
    proteccion. Una chapa sin ellos se dobla, se pinta y se monta antes de que
    nadie note nada.

    Se cuentan los REDONDOS, que es lo que _redondos() sabe leer. La ranura de
    salida es obround y queda fuera a proposito: su tamano si lo ve el sobre de
    clearance_budget, que comprueba que cabe en el suelo.
    """
    import clearance_budget as cb

    p = cb.leer_params()
    torn = 2 * (p["chasis_tornillos_largo"] + p["chasis_tornillos_corto"])
    # los 4 M5 con que el chasis cuelga de los largueros, dos por pared larga
    anclajes = 2 * int(p["chasis_anclajes"])
    esperado = {
        # 1 M6 del toroide + los TO-220 + 1 M4 de PE + los de la tapa + anclajes
        "chasis_cuerpo_2d": int(1 + p["chasis_to220_n"] + 1 + torn + anclajes),
        "chasis_tapa_2d": int(torn),
        "chasis_refuerzo_2d": 1 + 4,             # M6 central + 4 remaches
    }
    f: list[str] = []
    for nombre, n in esperado.items():
        if not (PLANS / f"{nombre}.dxf").exists():
            continue
        hay = len(_redondos(nombre))
        if hay != n:
            f.append(f"{nombre}: {hay} agujeros redondos y se esperaban {n}")
        else:
            ds = sorted({round(d, 1) for _, _, d in _redondos(nombre)})
            print(f"  {nombre}: {hay} agujeros, diametros {ds}")
    return f


def todo_dxf_tiene_quien_lo_mire() -> list[str]:
    """Ningun DXF sale al taller sin que una puerta lo mire.

    EL BUCLE DE main() VA AL REVES QUE ESTA PUERTA, y por eso hacia falta:
    recorre SOBRES buscando su DXF, o sea que caza la pieza que falta. La que
    SOBRA no la caza nadie -- un DXF nuevo en plans/ se exporta, se manda a
    cortar y no lo verifica nada, sin un solo mensaje.

    Se descubrio el 2026-08-26 al anadir costilla_2d: la pieza portante del
    case entero paso el gate en VERDE sin que nadie le mirara ni la envolvente.
    Habia dos huerfanos mas de antes, los dos legitimos y ninguno declarado
    como tal, que es justo lo que hacia el hueco invisible."""
    import pathlib
    exentos = {
        "lienzo_2d": "preview de nesteado, NO SE CORTA (lo dice el PLIEGO)",
        "kondor_cajeado_2d": "no es una pieza: es el cajeado ciego de la "
                             "trasera, y lo mira guarda_kondor() entero",
    }
    en_disco = {q.stem for q in PLANS.glob("*.dxf")}
    huerfanos = sorted(en_disco - set(SOBRES) - set(exentos))
    for nombre, motivo in exentos.items():
        if nombre in en_disco:
            print(f"  sin envolvente A PROPOSITO: {nombre} -- {motivo}")
    return [f"{n}.dxf se exporta y NINGUNA puerta lo mira: o entra en "
            f"_sobres() o se declara exento con su motivo" for n in huerfanos]




def guarda_zocalo() -> list[str]:
    """La tabla se puede mover, y por eso sus tornillos no son todos redondos.

    ES LA UNICA PIEZA DE MADERA DEL CASE Y DESDE EL 2026-08-27 CARGA. Una tabla
    maciza cambia de tamano con la humedad: a contraveta, del orden del 1 % entre
    un invierno seco y un verano humedo, o sea 3 mm sobre los 329 de fondo. El
    marco de aluminio no se mueve. Si los seis tornillos fueran redondos, en
    diciembre la tabla tira de ellos y o se raja por la fila o se sueltan.

    La solucion es de ebanisteria y tiene DOS mitades, y las dos hay que
    verificarlas porque cada una sola no sirve:
      1. Todos los tornillos menos uno van en RANURA, alargada en la direccion
         en que la tabla se mueve -- que es su FONDO, porque la veta corre a lo
         largo (los 570 mm del ancho del case, como en la foto de referencia).
      2. UNO de cada fila va REDONDO. Es el punto fijo. Sin el, la tabla no se
         queda quieta: se arrastra hacia un extremo y el vuelo deja de ser
         simetrico. Con dos redondos vuelve el problema entero.

    Se lee del DXF y no del modelo porque lo que va al carpintero es el DXF, y
    una ranura que sale redonda de la exportacion no la nota nadie: el contorno
    no cambia y la pieza parece correcta hasta que llega el invierno."""
    import clearance_budget as cb

    p = cb.leer_params()
    d = p["d_M5_paso"] + p["kerf"]
    viaje = 2 * p["holgura_veta"]
    # AL MEDIO DEL CANTO INFERIOR DEL ANILLO desde el 2026-08-28, gemela de
    # bandeja_base_2d(). Fue t_cheek + t_costilla/2 mientras la costilla era
    # chapa apoyada detras del acrilico; hoy el canto ES el anillo, 14 mm de
    # pletina, y el M5 va a una rosca ciega en su centro.
    filas_x = [p["vuelo_zocalo"] + p["t_anillo"] / 2,
               p["vuelo_zocalo"] + p["ancho_total"] - p["t_anillo"] / 2]
    aristas, comps = _componentes("bandeja_base_2d")
    if not aristas:
        return ["bandeja_base_2d: sin LINEs, no se puede verificar la tabla"]

    # Todo lo que mide d de ancho es tornillo de fijacion: redondo si es
    # cuadrado, ranura si es mas largo que ancho.
    tornillos = []
    for comp in comps:
        px = [q[0] for j in comp for q in aristas[j]]
        py = [q[1] for j in comp for q in aristas[j]]
        w, h = max(px) - min(px), max(py) - min(py)
        if abs(w - d) > 0.1 or h < d - 0.1:
            continue
        tornillos.append(((min(px) + max(px)) / 2, (min(py) + max(py)) / 2, h))

    f: list[str] = []
    # LA QUINTA COPIA DEL PASO, y la ultima. Fue un 100 a mano hasta el
    # 2026-08-27; la destapo el test de rotura de la reticula -- subir
    # reticula_paso a 137 movia la fila de la tabla en el modelo y no
    # aqui, y esta puerta cantaba "2 tornillos y el modelo pone 3".
    # La tabla usa n_agujeros(), que desde hoy lee reticula_paso.
    n = max(1, round((fondo_tabla := cb._fondo_bandeja(p))
                     / p["reticula_paso"]))
    for xc in filas_x:
        fila = sorted((t for t in tornillos if abs(t[0] - xc) < 0.1),
                      key=lambda t: t[1])
        if len(fila) != n:
            f.append(f"bandeja_base_2d: la fila de x={xc:.2f} trae "
                     f"{len(fila)} tornillos y el modelo pone {n} sobre "
                     f"{fondo_tabla:.2f} mm de fondo")
            continue
        redondos = [t for t in fila if abs(t[2] - d) < 0.1]
        if len(redondos) != 1:
            f.append(f"bandeja_base_2d: la fila de x={xc:.2f} tiene "
                     f"{len(redondos)} tornillos REDONDOS y tiene que tener "
                     f"exactamente 1. Ninguno: la tabla no tiene punto fijo y "
                     f"se arrastra hacia un extremo. Dos o mas: vuelve a estar "
                     f"clavada a un marco que no se mueve, y se raja")
            continue
        if abs(redondos[0][1] - fila[n // 2][1]) > 1e-6:
            f.append(f"bandeja_base_2d: el tornillo redondo de la fila de "
                     f"x={xc:.2f} no es el del MEDIO. Fijar por una punta deja "
                     f"toda la carrera hacia el otro lado y el vuelo del "
                     f"zocalo deja de ser simetrico")
        for t in fila:
            if abs(t[2] - d) < 0.1:
                continue
            if abs(t[2] - (d + viaje)) > 0.1:
                f.append(f"bandeja_base_2d: la ranura de (x={t[0]:.1f}, "
                         f"y={t[1]:.1f}) mide {t[2]:.2f} de largo y se exige "
                         f"{d + viaje:.2f} (paso M5 + 2 x holgura_veta). La "
                         f"carrera cubre lo que la madera se mueve a "
                         f"contraveta: acortarla es volver a clavarla")
    if not f:
        print(f"  bandeja_base_2d: {len(tornillos)} tornillos en 2 filas, "
              f"1 redondo y {n - 1} en ranura de {d + viaje:.1f} mm por fila "
              f"-- la tabla puede moverse {viaje:.1f} mm a contraveta")

    # LOS CUATRO TALADROS DE PIE (Tarea 6). ADEMAS de las dos filas de M5, no
    # en vez de ellas: paticas() atornilla las cuatro paticas de goma A LA
    # TABLA, y esos cuatro agujeros son un censo aparte con su propio
    # diametro (d_pie_tornillo, no d_M5_paso).
    #
    # LA CONVERSION DE COORDENADAS ES LA MISMA que usan las dos filas de
    # arriba: local x = vuelo_zocalo + z del mundo, local y = vuelo_zocalo +
    # x del mundo (comentario largo sobre bandeja_base_2d() en el .scad,
    # "x local de la tabla = vuelo_zocalo + z del mundo"). GEMELA de
    # paticas(): mismos cuatro centros del .scad, sin la rotacion a Z que ahi
    # hace falta para plantar el cilindro y aqui no, porque esto es 2D.
    v = p["vuelo_zocalo"]
    P = cb._vertices(p)
    bajo = cb._cajas_miembro(p, P, cb._centros_rail(p, P), 0.0, 0.0)["trasero bajo"]
    x_frente = p["alto_frontal"] / 2 + p["d_pie"] / 2
    x_trasero = (bajo[1] + bajo[2]) / 2       # centro_miembro_bajo().x
    d_pie_taladro = p["d_pie_tornillo"] + p["kerf"]
    esperados_pie = [(v + wz, v + wx)
                     for wx in (x_frente, x_trasero)
                     for wz in (p["d_pie"] / 2, p["ancho_total"] - p["d_pie"] / 2)]
    redondos = _redondos("bandeja_base_2d")
    pies = [q for q in redondos if abs(q[2] - d_pie_taladro) < 0.1]
    if len(pies) != 4:
        f.append(f"bandeja_base_2d: faltan los 4 taladros de pie -- hay "
                 f"{len(pies)} de d={d_pie_taladro:.2f} mm (d_pie_tornillo) "
                 f"en el DXF y paticas() pone 4")
    else:
        faltan_pie = []
        for ex, ey in esperados_pie:
            if not any(math.hypot(q[0] - ex, q[1] - ey) <= DESVIO_DXF_MAX
                       for q in pies):
                faltan_pie.append((ex, ey))
        if faltan_pie:
            f.append(f"bandeja_base_2d: el taladro de pie en "
                     f"{faltan_pie[0]} no cae donde paticas() lo pone")
        else:
            print(f"  bandeja_base_2d: 4 taladros de pie d={d_pie_taladro:.2f} "
                  f"mm en las posiciones de paticas()")
    return f




MIEMBROS_DXF = {"miembro_bajo_2d": "trasero bajo",
                "miembro_alto_2d": "trasero alto",
                "bahia_2d": "bahia"}


def taladros_reticula() -> list[str]:
    """Los tres miembros de chapa llevan su reticula, y nada se le pega encima.

    ES LA PIEZA QUE SUSTITUYE A LA RANURA EN T, y por eso hay puerta. El 2020
    traia una ranura corrida con tuercas de insercion lateral: un tornillo se
    podia anadir DESPUES, con el case montado. Con canales de chapa eso se
    acaba -- cada agujero se decide en el DXF y anadir uno mas tarde es taladrar
    el aparato armado. Lo que se pierde en libertad se devuelve en RETICULA: una
    fila de agujeros a paso regular a lo largo del alma de cada canal.

    LOS TRES SALIERON DE LA TAREA 4 LISOS. `square([ancho_util, desarrollo])` y
    nada mas: ni la reticula, ni los agujeros de las filas de plancha que ya
    apoyan en ellos, ni los M5 de los que cuelga el chasis del PSU. Tres canales
    sin un solo agujero pasaron las dos puertas en verde, porque las dos miraban
    la ENVOLVENTE. Esta mira dentro.

    DOS COSAS, y la segunda es la que cuesta una pieza:

      1. la reticula esta COMPLETA -- los n agujeros de M3 a paso regular, con
         el mismo reparto de medio paso en los margenes que usa fila_agujeros()
         para las planchas. Ese reparto compartido es el motivo de que
         reticula_paso valga lo que vale: las filas que ya existen caen en la
         reticula por construccion, no por suerte.

      2. todo agujero que NO sea de la reticula -- los M5 del chasis son los
         unicos que quedan -- guarda BORDE_MIN_D x D de PUENTE contra su vecino
         de reticula. Un M5 a 2 mm de un M3 en chapa de 3 no es un agujero de
         mas: es una ranura, y se rasga al plegar. Es el modo de fallo que la
         ranura en T no tenia, porque alli no habia vecinos.

      3. la fila ES UNA FILA -- los n agujeros comparten una sola Y -- y esa Y
         guarda BORDE_MIN_D x D contra los dos cantos del desarrollo.

    LO QUE ESTA PUERTA NO CAZA, y va declarado: que la fila caiga en la BANDA
    EQUIVOCADA del desarrollo -- sobre un ala en vez de sobre el alma. Verlo
    exigiria saber donde estan las lineas de plegado, y eso es replicar aqui la
    matematica de doblez de sam17_case.scad, que es justo la copia que este
    fichero evita a proposito (lo dice agujeros_donde_toca() con todas sus
    letras). De la banda responden los solidos plegados y solapes(); de aqui
    para afuera, el censo, la fila y los puentes."""
    import clearance_budget as cb

    p = cb.leer_params()
    au = cb.perfil(p)["ancho_util"]
    paso = p["reticula_paso"]
    n = max(1, round(au / paso))
    rejilla = [au * (i + 0.5) / n for i in range(n)]
    d_ret = p["d_M3_paso"] + p["kerf"]
    f: list[str] = []
    for dxf, miembro in MIEMBROS_DXF.items():
        leidos = _redondos(dxf)
        if not leidos:
            f.append(f"{dxf}: CERO agujeros. El miembro '{miembro}' es un canal "
                     f"de chapa, no un 2020: sin reticula no se le puede "
                     f"atornillar nada, ni hoy ni despues de montado")
            continue
        sobra = list(leidos)
        for x in rejilla:
            cerca = [q for q in sobra
                     if abs(q[0] - x) <= DESVIO_DXF_MAX
                     and abs(q[2] - d_ret) <= 0.1]
            if not cerca:
                f.append(f"{dxf}: falta el agujero de reticula en x={x:.2f} "
                         f"(paso {paso:.0f}, {n} sobre {au:.2f}). Con la ranura "
                         f"en T daba igual donde cayera un tornillo; aqui no")
                continue
            sobra.remove(cerca[0])
        ys = sorted(q[1] for q in leidos if abs(q[2] - d_ret) <= 0.1)
        if ys and ys[-1] - ys[0] > DESVIO_DXF_MAX:
            f.append(f"{dxf}: los agujeros de reticula se reparten entre "
                     f"y={ys[0]:.2f} y y={ys[-1]:.2f}. Es una FILA a lo largo "
                     f"del alma, no una nube: si no comparten Y, la plancha que "
                     f"apoya encima no apoya en todos")
        elif ys:
            aristas, _ = _componentes(dxf)
            todos = [pt[1] for a in aristas for pt in a]
            canto = min(ys[0] - min(todos), max(todos) - ys[-1])
            if canto < BORDE_MIN_D * d_ret:
                f.append(f"{dxf}: la fila de reticula corre a {canto:.2f} mm "
                         f"del canto mas cercano del desarrollo y se exigen "
                         f"{BORDE_MIN_D * d_ret:.2f} ({BORDE_MIN_D} x D)")
        for q in sobra:
            d = min(abs(q[0] - x) for x in rejilla)
            puente = d - (q[2] + d_ret) / 2
            minimo = BORDE_MIN_D * max(q[2], d_ret)
            if puente < minimo:
                f.append(f"{dxf}: el agujero de {q[2]:.2f} en x={q[0]:.2f} deja "
                         f"{puente:.2f} mm de puente contra el de reticula mas "
                         f"cercano y se exigen {minimo:.2f} ({BORDE_MIN_D} x D). "
                         f"Dos agujeros a esa distancia en chapa de "
                         f"{p['t_costilla']:.0f} son una ranura: se rasga al "
                         f"plegar")
        if not f:
            extra = len(leidos) - n
            print(f"  {dxf}: reticula de {n} M3 a paso {paso:.0f} sobre "
                  f"{au:.2f}" + (f", mas {extra} agujero(s) declarado(s) con "
                                 f"puente" if extra else ""))
    return f


def main() -> int:
    fallos: list[str] = []
    for nombre, sobre in SOBRES.items():
        ruta = PLANS / f"{nombre}.dxf"
        if not ruta.exists():
            fallos.append(f"{nombre}: FALTA el DXF")
            continue
        fallos += revisar(nombre, sobre)
    fallos += anillo_tiene_ventana()
    fallos += anillo_tiene_rebaje()
    fallos += seccion_del_cupon()
    fallos += taladros_anillo()
    fallos += taladros_placas()
    fallos += ranuras_rejilla_entrada()
    fallos += cuerpos_dentro_del_anillo()
    fallos += tapa_valle_conectada()
    fallos += taladros_reticula()
    fallos += guarda_zocalo()
    fallos += guarda_kondor()
    fallos += guarda_costado()
    fallos += agujeros_donde_toca()
    fallos += chasis_agujeros()
    fallos += todo_dxf_tiene_quien_lo_mire()
    for nombre, motivo in SIN_DXF.items():
        print(f"  PENDIENTE (sin DXF, no bloquea): {nombre} -- {motivo}")
    for m in fallos:
        print(f"ROJO: {m}")
    if fallos:
        return 2
    print("check_dxf: VERDE (unidades mm implicitas: decirselo al servicio)")
    return 0


# Lo que NO cubre: lienzo_2d (marco de referencia, piezas repetidas),
# self-intersections, orden de corte, y la pieza fisica (eso es el cupon).

if __name__ == "__main__":
    sys.exit(main())
