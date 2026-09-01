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

import clearance_budget as cb

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

# Consumibles modelados como caja para solapes/camino de carga, no piezas de
# corte. No son un DXF pendiente y por eso no entran en SIN_DXF: la tira del
# valle se compra en rollo y se corta al montar.
SIN_ARTEFACTO = {"tira anti-ruido valle"}

# Piezas que van GIRADAS con una cara, o sea que su caja en el mundo NO es su
# DXF. Esta vacio desde el 2026-08-21: la unica que estaba era la pestana de
# remate, que iba de canto sobre la cara de arriba y median 10.75 x 528 de caja
# por la diagonal de su seccion a 45 grados. Ahora es una plancha HORIZONTAL
# sobre la meseta, alineada con los ejes, y su caja YA es su DXF -- o sea que
# sale sola de _cajas_solidas y no hay que declarar su sobre a mano.
GIRADAS: set[str] = set()

# Las tres placas de anclaje (PLACAS_DXF), el clip y la escuadra murieron el
# 2026-08-29 por la noche: son el MARCO DE LA VENTANA, un DXF por costado,
# que relee taladros_marco_ventana().


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
    # Y EL BOLSILLO DE LA TRASERA (2026-08-29, noche, 2): arranca a y_bot, 1 mm
    # del canto de abajo, llega hasta la cara interior del labio y se cierra
    # arriba por debajo de las roscas de la brida, que ya estaban en el sobre.
    x1 = max(x1, cb.fondo(p) - cb._bolsillo_trasero(p)["u0"])
    y0 = min(y0, cb._bolsillo_trasero(p)["y_bot"])
    # Y EL REBAJE DE CHAPA (2026-08-30): corre por el contorno de lo que se ve
    # de las tres chapas, a rehundido_chapa de la silueta -- mas afuera que
    # todo lo anterior, y por los cuatro lados. Con el reborde de 1, el dorso
    # llega casi al canto de la pieza; el sobre lo tiene que saber o el
    # fichero sale rojo por una razon que no es un defecto, que es justo lo
    # que este helper existe para evitar.
    x0 = min(x0, p["rehundido_chapa"])
    x1 = max(x1, cb.fondo(p) - p["rehundido_chapa"])
    y0 = min(y0, p["rehundido_chapa"])
    y1 = max(y1, g["alto_total"] - p["rehundido_chapa"])
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
        # Y SU CANTO TRASERO ENTRA 3, NO 6, desde la trasera capturada
        # (2026-08-29, noche, 2): retrocede a la pared entre bolsillos.
        "costado_2d": (cb.fondo(p) - _retiro_costado(p)
                       - (p["t_anillo"] + p["pared_rebaje_trasera"] + p["hol_costado"]),
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
        # las dos tiras laterales de la trasera (bajo sus muescas de esquina)
        # son cajas para solapes(), no piezas: el DXF es el contorno entero
        if (nombre in SIN_DXF or nombre in SIN_ARTEFACTO
                or nombre in GIRADAS or " lado " in nombre):
            continue
        aristas = sorted((x1 - x0, y1 - y0, z1 - z0), reverse=True)
        dims[f"{nombre}_2d"] = (aristas[0], aristas[1])   # se cae el espesor

    # DESPUES del bucle, y por eso: la tapa del valle SI es una plancha del
    # cuerpo, asi que el bucle le pone la caja de la pieza doblada -- y su DXF
    # es el DESARROLLO, que sale 2*vuelo mas ancho por las dos pestanas. Es el
    # mismo error que el sobre del chasis tiene que cazar: exportar el contorno
    # de la pieza montada en vez del recorte da un DXF valido e inservible.
    dims["tapa_valle_2d"] = cb.bbox_desarrollo_tapa(p)
    # LOS DOS MIEMBROS DE CHAPA. Sus DXF son DESARROLLOS y salen mas grandes
    # que la pieza doblada, igual que la costilla, la tapa del valle y las tres
    # del chasis. Derivados, no escritos a mano: si el .scad y la cuenta de
    # Python se separan, el bbox real del fichero se sale del sobre y revisar()
    # lo canta. Es la unica forma de cruzar dos gemelas que viven en lenguajes
    # distintos.
    # EL MIEMBRO ALTO (una L con dos bridas) Y EL TALON (un angulo), desde el
    # 2026-08-29 por la noche. El miembro bajo, la escuadra y los dos marcos
    # de la trasera murieron esa noche: el marco de la ventana hace de tope y
    # la banda de cada miembro hace de marco.
    dims["miembro_alto_2d"] = cb.bbox_desarrollo_miembro(p, "trasero alto")
    dims["talon_2d"] = cb.bbox_desarrollo_miembro(p, "talon")
    # LA NARIZ (2026-08-29): la banda del frente. Otro desarrollo de la misma
    # chapa, con TRES dobleces (dos a 45 en el chaflan y uno de angulo_inferior
    # en P1), y otra vez la cuenta vive en Python y el dibujo en el .scad.
    dims["nariz_2d"] = cb.bbox_desarrollo_nariz(p)

    # EL MARCO DE LA VENTANA (2026-08-29, noche): una pletina por costado con
    # el contorno de la ventana del anillo, UN DXF para las dos (el lado
    # espejado comparte contorno y se cajea por la otra cara). Su sobre es la
    # silueta menos los retiros, derivado en el budget.
    dims["marco_ventana_2d"] = cb.bbox_marco_ventana(p)

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


def _x_blank(p: dict[str, float], z: float) -> float:
    """De z del mundo a x del desarrollo de la nariz o del talon.

    EL ORIGEN DEL BLANK SE MOVIO EL 2026-08-30. Era la cara interior del anillo
    (t_anillo + hol_piel): la chapa se apoyaba sobre ella. Con la chapa
    empotrada el blank arranca DENTRO del rebaje, muesca_pie() antes, y todo lo
    que el DXF coloca por z -- los M4 del pie, las ocho pestanas del talon y
    sus alivios -- se corre con el. Estaba escrito cuatro veces con la formula
    a mano, y las cuatro se quedaron viejas a la vez; ahora es una."""
    return z - (p["t_anillo"] + p["hol_piel"] - cb._muesca_pie(p))


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
    # --- trasera: CERO agujeros de tornillo desde la trasera capturada ---
    # (2026-08-29, noche, 2). Tuvo 16 con las escuadras y 10 con las bandas;
    # va DENTRO de los bolsillos de los anillos como el costado, y nada la
    # atraviesa. Lo que si lleva -- rejilla, ondas, ventana de la red -- no
    # es redondo, y lo miran sus propias puertas.
    if (PLANS / "piel_trasera_2d.dxf").exists() and _redondos("piel_trasera_2d"):
        f.append(f"piel_trasera_2d: {len(_redondos('piel_trasera_2d'))} agujero(s) "
                 f"redondo(s) en el acrilico. La trasera va CAPTURADA como el "
                 f"costado: cero")

    # --- planchas: filas, paso y separacion ---
    _, _, filas = cb._cajas_solidas(p)
    # DEL PRESUPUESTO, no recalculado: desde el 2026-08-26 ancho_util resta
    # tambien las dos alas de costilla, y una copia a mano de la formula aqui
    # se desincroniza del original en cuanto se toque t_costilla.
    # EL BLANK DEL TECHO CRECIO 5.0 EL 2026-08-30: ya no mide el vano entre
    # caras sino lo que entra en rebaje, y las dos bridas doblan de SUS puntas,
    # no de las de antes. Con ancho_util aqui, los cuatro M4 salian a 5 mm de
    # donde estan y el fichero correcto daba rojo.
    au = cb._chapa_largo_rebaje(p)
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
    # (Las dos bandas del marco de la trasera se releian aqui del 29-08 por la
    # manana a la noche; desde entonces la fila de la trasera vive en la banda
    # del miembro alto y en la del talon, y la relee taladros_reticula().)

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
# Viven en clearance_budget.py junto a SIGMA_PMMA (dos clientes: esta puerta
# y guarda_trasera_flexion); aqui solo el alias.
R_CONTACTO, NU_PMMA, E_PMMA = cb.R_CONTACTO, cb.NU_PMMA, cb.E_PMMA


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

    El costado no lleva un solo tornillo: queda ASENTADO EN EL REBAJE DEL
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
                   de la ventana. Es la medicion de apoyo de siempre.
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
    # DESDE EL 2026-08-29 POR LA NOCHE EL APOYO HACIA DENTRO ES CONTINUO: el
    # marco de la ventana, una pletina por costado que corre los siete tramos
    # y pisa 6 mm de acrilico mas alla de la ventana. Placas, clips y escuadra
    # murieron en el. Cada pata pasa su poligono real (con el escalon del
    # canto exterior y la muesca de la brida); en las esquinas las patas se
    # solapan o dejan un triangulo minimo, y el barrido lo trata como lo que
    # es: el vano hasta el canto interior del marco.
    apoyos = [q["poligono"] for q in cb._marco_ventana(p)]
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
            f"contra {p['flecha_costado_max']:.2f}. Hacia dentro lo para el "
            f"marco de la ventana: sube marco_fondo")
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
    print(f"  hacia DENTRO lo para el marco de la ventana ({len(apoyos)} patas "
          f"por costado, {p['marco_fondo']:g} desde la silueta): vano interior "
          f"{vano_in:.1f} mm (x={donde_in[0]:.0f}, y={donde_in[1]:.0f}) y se "
          f"hunde {flecha_in:.2f} mm (techo {p['flecha_costado_max']:.2f}, vano "
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
    # EL TRAMO TRASERO ES LA EXCEPCION, y hasta el 2026-08-30 esta puerta era
    # CIEGA a el. Su canto de ventana esta a cara_anillo_trasera del plano
    # trasero (22 desde que el bolsillo se corrio con la rendija; antes 20), y
    # la medida de arriba no lo ve: para esos dos vertices el punto de silueta
    # mas cercano no es el plano trasero sino el chaflan de arriba o el de
    # abajo, que caen a 20 justos. O sea que el anillo podia salir con la
    # franja trasera en cualquier ancho y esto seguia verde. Se mide aparte, y
    # contra el DERIVADO: cara_anillo_trasera no es un parametro, sale del
    # bolsillo mas su pared mas lo que entra el costado.
    ct = cb._cara_anillo_trasera(p)
    x_ct = cb.fondo(p) - ct
    canto_tras = [a for j in ventana for a in [aristas[j]]
                  if abs(a[0][0] - x_ct) <= CARA_DXF_MAX
                  and abs(a[1][0] - x_ct) <= CARA_DXF_MAX
                  and abs(a[0][1] - a[1][1]) > 100.0]
    if not canto_tras:
        xs = sorted({round(q[0], 2) for j in ventana for q in aristas[j]})
        return [f"costilla_2d: la ventana no tiene canto trasero a plomo en "
                f"x = {x_ct:.2f} (cara_anillo_trasera = {ct:g} del plano "
                f"trasero, derivado del bolsillo + pared + entrada del "
                f"costado). Su canto mas atrasado esta en x = {xs[-1]:.2f}, "
                f"o sea a {cb.fondo(p) - xs[-1]:.2f} del plano trasero"]

    print(f"  costilla_2d: anillo de cara {min(ds):.2f}..{max(ds):.2f} mm "
          f"(cara_anillo {p['cara_anillo']:g}) entre silueta y ventana, y "
          f"{ct:g} en el tramo trasero (derivado)")
    return []


def _caja_cajeado_brida(cb, p: dict[str, float]) -> tuple[float, float, float, float]:
    """La caja del cajeado de la brida del techo en el dorso, en coordenadas del
    perfil: la huella de la brida mas hol_chapa por lado. Existe desde el
    2026-08-30, cuando la brida dejo de apoyar en la cara del anillo y paso a
    apoyar en un cajeado de rebaje_chapa de fondo."""
    b = cb._bridas(p)[0]
    h = p["hol_chapa"]
    return (b["rect"][0] - h, b["rect"][1] + h,
            b["rect"][2] - h, b["rect"][3] + h)


def anillo_tiene_rebaje() -> list[str]:
    """El DXF del DORSO es el mapa de lo que se FRESA en la cara interior, y
    cada canto suyo tiene que caer a una distancia LEGAL de la silueta.

    HERMANA DE anillo_tiene_ventana(), y nace del mismo agujero. El dorso solo
    lo miraba su SOBRE, con TOL = 4 mm: eso deja pasar un retiro entre 12 y 16
    sin decir nada, y sobre todo deja pasar que alguien exporte ahi la silueta
    entera o la ventana en vez del rebaje -- las tres son contornos parecidos y
    ninguna caja las distingue. Un DXF valido e inservible.

    HASTA EL 2026-08-30 la regla era una sola distancia (cara - rebaje, o la
    del tramo trasero) y el contorno exterior del dorso era el rebaje del
    costado. Con la chapa empotrada ya no: el rebaje de chapa corre mucho mas
    afuera, a rehundido_chapa de la silueta, y es EL el contorno exterior por
    los tramos donde hay chapa. Asi que la regla pasa a ser una LISTA de
    distancias legales, y se exige que las dos principales aparezcan de verdad
    -- si el rebaje de chapa no esta, las chapas no se empotran y nadie mas lo
    caza; si el del costado no esta, el marco no asienta.

    Se mide la DISTANCIA, no la caja, porque offset() es exacto en la distancia
    y no en el bbox: los vertices en punta se resuelven a inglete. Y la silueta
    contra la que se mide se relee del OTRO fichero, costilla_2d.dxf, que es
    donde vive: el dorso no la lleva dibujada -- si la llevara, la fresa se
    comeria el contorno de la pieza."""
    import clearance_budget as cb

    p = cb.leer_params()
    rebaje = _contorno_exterior("costilla_dorso_2d")
    silueta = _contorno_exterior("costilla_2d")
    if not rebaje or not silueta:
        return ["costilla_dorso_2d: sin LINEs en el dorso o en la cara, no se "
                "puede medir el retiro del rebaje"]
    retiro = p["cara_anillo"] - p["rebaje_anillo"]
    # EN EL TRAMO TRASERO EL REBAJE RETROCEDE a la pared con el bolsillo de la
    # trasera (2026-08-29, noche, 2), que desde el 30-08 es un derivado: el
    # bolsillo se corrio 1.5 hacia dentro con la rendija.
    retiro_tras = cb._bolsillo_trasero(p)["rebaje_costado"]
    reh = p["rehundido_chapa"]
    fondo = cb.fondo(p)
    bo = cb._bolsillo_trasero(p)

    # LO MAS FINO QUE EL DISENO DEJA entre un vaciado y la cara de la pieza: la
    # esquina del escalon del bolsillo bajo el chaflan de P6, que arranca a 0.5
    # en x de esa cara. Es geometria ANTERIOR a la chapa empotrada (la formula
    # trae su +0.5 desde el 2026-08-29) y nadie la medía, porque hasta hoy el
    # bolsillo y el rebaje del costado se tocaban y esa esquina no salia al
    # contorno exterior. Se toma como suelo, no como bendicion: 0.35 mm
    # perpendiculares a lo largo de 6 de hondo es un filo, y queda anotado.
    minimo = _dist_al_contorno(silueta, (fondo - bo["u_paso"], bo["y_bot"]))

    ds = [_dist_al_contorno(silueta, q) for a in rebaje for q in a]
    if not ds:
        return ["costilla_dorso_2d: contorno exterior vacio"]

    # 1. NO ES LA SILUETA NI LA VENTANA. Las tres son contornos parecidos y
    #    ninguna caja las distingue; esto es lo que evita exportar el fichero
    #    equivocado y mandarlo al taller.
    if min(ds) < minimo - CARA_DXF_MAX:
        q = min(((_dist_al_contorno(silueta, q), q) for a in rebaje for q in a),
                key=lambda m: m[0])[1]
        return [f"costilla_dorso_2d: un canto del dorso corre a "
                f"{min(ds):.2f} mm de la silueta en ({q[0]:.1f}, {q[1]:.1f}), y "
                f"lo mas fino que el diseno deja son {minimo:.2f} (la esquina "
                f"del escalon del bolsillo). O el fichero no es el dorso, o hay "
                f"un vaciado que se sale a la cara de la pieza"]

    # 2. Y LAS DOS COSAS QUE EL TALLER TIENE QUE FRESAR ESTAN. Sin la primera
    #    las chapas no se empotran; sin la segunda el marco no asienta. Que la
    #    envolvente cuadre no dice nada de esto.
    for v, que in ((reh, "el rebaje de chapa, a rehundido_chapa de la silueta"),
                   (retiro, "el rebaje del costado, a cara - rebaje")):
        if not any(abs(d - v) <= CARA_DXF_MAX for d in ds):
            return [f"costilla_dorso_2d: ningun canto del dorso cae a {v:g} mm "
                    f"de la silueta, o sea que {que} NO esta en el fichero. Es "
                    f"lo que el taller fresa; sin el, la pieza sale lisa"]

    # 3. El canto trasero del rebaje del costado, a plomo: es el que dice que en
    #    ese tramo el costado retrocede sobre la pared entre bolsillos.
    atras = sum(1 for a in rebaje
                if abs(a[0][0] - (fondo - retiro_tras)) <= CARA_DXF_MAX
                and abs(a[1][0] - (fondo - retiro_tras)) <= CARA_DXF_MAX
                and abs(a[0][1] - a[1][1]) > 100.0)
    if not atras:
        return [f"costilla_dorso_2d: el rebaje no tiene canto trasero a plomo a "
                f"{retiro_tras:g} del plano trasero: tiene que retroceder a la "
                f"pared entre bolsillos"]

    # 4. Y EL CAJEADO DE LA BRIDA, LEIDO DEL FICHERO (2026-08-30). No se mide
    #    por distancia a la silueta: entra hasta ~30 mm porque la brida mide 27
    #    de largo, y es la unica pieza del dorso que no corre paralela al
    #    contorno. Se buscan SUS DOS CANTOS LIBRES -- el de la izquierda a
    #    plomo y el de abajo a nivel --, que son los que fijan la huella; los
    #    otros dos los recorta el contorno del anillo.
    #
    #    LA PRIMERA VERSION DE ESTO ERA UNA TAUTOLOGIA, y la caz~o el revisor
    #    del 30-08: derivaba la caja de los parametros y la comparaba contra
    #    los mismos parametros, asi que con brida_largo = 10 y el DXF intacto
    #    devolvia verde ANUNCIANDO que habia leido un cajeado de 11 x 15.5. Una
    #    puerta que no abre el fichero no es una puerta: es un comentario.
    caj = _caja_cajeado_brida(cb, p)
    y_med = (caj[2] + caj[3]) / 2
    x_med = (caj[0] + caj[1]) / 2
    izq = [a for a in rebaje
           if abs(a[0][0] - a[1][0]) <= CARA_DXF_MAX
           and min(a[0][1], a[1][1]) <= y_med <= max(a[0][1], a[1][1])
           and caj[0] - 2.0 <= a[0][0] <= caj[0] + 2.0]
    aba = [a for a in rebaje
           if abs(a[0][1] - a[1][1]) <= CARA_DXF_MAX
           and min(a[0][0], a[1][0]) <= x_med <= max(a[0][0], a[1][0])
           and caj[2] - 2.0 <= a[0][1] <= caj[2] + 2.0]
    if not izq or not aba:
        return [f"costilla_dorso_2d: no encuentro el cajeado de la brida en el "
                f"fichero. Se buscaba su canto izquierdo a plomo cerca de "
                f"x = {caj[0]:.2f} y su canto de abajo a nivel cerca de "
                f"y = {caj[2]:.2f} (la huella de la brida mas hol_chapa por "
                f"lado). Sin cajeado la brida invade la envolvente estatica "
                f"del panel fijo"]
    x_leido, y_leido = izq[0][0][0], aba[0][0][1]
    if abs(x_leido - caj[0]) > CARA_DXF_MAX or abs(y_leido - caj[2]) > CARA_DXF_MAX:
        return [f"costilla_dorso_2d: el cajeado de la brida arranca en el "
                f"fichero en ({x_leido:.2f}, {y_leido:.2f}) y la huella de la "
                f"brida ({p['brida_largo']:g} x {p['brida_ancho']:g}) mas "
                f"hol_chapa ({p['hol_chapa']:g}) por lado lo pone en "
                f"({caj[0]:.2f}, {caj[2]:.2f})"]
    esperado = (p["brida_largo"] + 2 * p["hol_chapa"],
                p["brida_ancho"] + 2 * p["hol_chapa"])

    print(f"  costilla_dorso_2d: cantos a {min(ds):.2f}..{max(ds):.2f} mm de la "
          f"silueta; estan el rebaje de chapa ({reh:g}) y el del costado "
          f"({retiro:g}, {retiro_tras:g} atras), y los cajeados de brida de "
          f"{esperado[0]:g} x {esperado[1]:g}")
    return []



def anillo_tiene_bolsillo_trasero() -> list[str]:
    """El dorso lleva el bolsillo de la trasera: de canto a canto del tramo
    trasero, entre la pared del fondo (u1) y la cara interior de su labio (u0).

    ES LA MITAD DEL DORSO QUE NO ES EL REBAJE (2026-08-29, noche, 2). Si alguien
    exporta el rebaje solo, el anillo sale sin sitio para la trasera y ninguna
    otra puerta lo ve. La profundidad (rebaje_anillo, no los t_anillo -
    rehundido del rebaje) va en el pliego: un DXF de planta no la sabe decir.

    HASTA EL 2026-08-30 se buscaba un COMPONENTE SUELTO con la caja exacta del
    bolsillo. Ya no lo hay: bajo los dos labios de chapa -- el del techo arriba,
    el del talon abajo -- el bolsillo y el rebaje de chapa se funden en un solo
    vaciado de u = rehundido_chapa a u1, porque el suelo del rebaje ES la pared
    exterior del bolsillo por construccion (§4.3 de la spec). Asi que ya no se
    busca una caja: se buscan LAS DOS PAREDES del bolsillo, que es lo que de
    verdad tiene que estar fresado, y el escalon bajo el chaflan."""
    import clearance_budget as cb

    p = cb.leer_params()
    bo = cb._bolsillo_trasero(p)
    fondo = cb.fondo(p)
    x0, x1 = fondo - bo["u1"], fondo - bo["u0"]
    x_paso = fondo - bo["u_paso"]
    aristas, comps = _componentes("costilla_dorso_2d")
    if not comps:
        return ["costilla_dorso_2d: sin componentes, no se puede buscar el "
                "bolsillo de la trasera"]

    def plomo(x, y_lo, y_hi, largo_min):
        """Aristas verticales en x que caigan dentro de [y_lo, y_hi]."""
        return [a for a in aristas
                if abs(a[0][0] - x) <= CARA_DXF_MAX
                and abs(a[1][0] - x) <= CARA_DXF_MAX
                and abs(a[0][1] - a[1][1]) >= largo_min
                and min(a[0][1], a[1][1]) >= y_lo - CARA_DXF_MAX
                and max(a[0][1], a[1][1]) <= y_hi + CARA_DXF_MAX]

    # 1. LA PARED DEL FONDO (u1). Corre de punta a punta del tramo trasero y es
    #    la que fija cuanto entra la trasera: sin ella no hay bolsillo.
    if not plomo(x0, bo["y_bot"], bo["y_fin"], 100.0):
        return [f"costilla_dorso_2d: falta la pared del fondo del bolsillo de la "
                f"trasera, a plomo en x = {x0:.2f} (u = {bo['u1']:g} del plano "
                f"trasero). Sin ella la trasera no tiene donde meterse"]

    # 2. LA PARED EXTERIOR (u0), en el tramo SIN chapa. Donde hay labio de chapa
    #    esta pared no existe -- el rebaje se la come, que es el diseno --, asi
    #    que se busca entre los dos labios, que es donde tiene que estar.
    y_lo = p["chaflan_nariz"] + p["talon_labio"]
    y_hi = cb._y_labio_techo(p)
    if not plomo(x1, y_lo, y_hi, 50.0):
        return [f"costilla_dorso_2d: falta la pared exterior del bolsillo (el "
                f"labio), a plomo en x = {x1:.2f} (u = {bo['u0']:g}) entre y = "
                f"{y_lo:g} y {y_hi:.2f}. Ahi no hay labio de chapa que la "
                f"sustituya: el labio del bolsillo tiene que estar"]

    # 3. EL ESCALON BAJO EL CHAFLAN de P6: bajo y_paso el bolsillo arranca en
    #    u_paso para no morder la cara del chaflan.
    if not any(abs(q[0] - x_paso) <= CARA_DXF_MAX
               and abs(q[1] - bo["y_paso"]) <= CARA_DXF_MAX
               for a in aristas for q in a):
        return [f"costilla_dorso_2d: el bolsillo de la trasera no lleva el "
                f"escalon bajo el chaflan: falta el vertice en ({x_paso:.2f}, "
                f"{bo['y_paso']:.2f})"]

    print(f"  costilla_dorso_2d: bolsillo de la trasera en u = "
          f"{bo['u0']:g}..{bo['u1']:g} del plano trasero, cerrado de y = "
          f"{bo['y_bot']:g} a {bo['y_fin']:.2f} (arranca en u = "
          f"{bo['u_paso']:g} bajo y = {bo['y_paso']:g}; hondo {bo['hondo']:g}, "
          f"en el pliego). Bajo los dos labios de chapa se funde con el rebaje "
          f"en un solo vaciado, y ahi su labio lo hace el reborde")
    return []


def anillo_tiene_chaflan() -> list[str]:
    """Las esquinas del anillo que llevan chapa doblada a 45 van a CHAFLAN, y
    entre chaflanes los cantos van a plomo.

    ES LA PUERTA DE LA NOTA 2 DE SAMUEL (2026-08-29): "en vez de una nariz
    curva, una nariz recta", con la esquina de abajo cortada a 45 como en su
    referencia. Desde la trasera capturada (misma noche, 2) la esquina de
    abajo-atras va igual -- el talon es la nariz de atras -- y la de
    arriba-atras tambien cuando el techo lleva chaflan. Se relee del DXF que
    va al taller, no de una copia de redondear() en Python: que el punto del
    contorno mas cercano a cada esquina viva este sobre su linea a 45 (|dx| +
    |dy| = chaflan), que el frente y el canto trasero sean verticales entre
    los chaflanes y los radios, y que el suelo llegue a los dos chaflanes."""
    import clearance_budget as cb

    p = cb.leer_params()
    c, r = p["chaflan_nariz"], p["radio_chapa"]
    fondo, alto = cb.fondo(p), cb.perfil(p)["alto_total"]
    aristas = _contorno_exterior("costilla_2d")
    if not aristas:
        return ["costilla_2d: sin contorno exterior, no se puede ver la nariz"]
    pts = [q for a in aristas for q in a]
    f: list[str] = []
    esquinas = [("frente-abajo (la nariz)", (0.0, 0.0)),
                ("atras-abajo (el talon)", (fondo, 0.0))]
    if cb._chaflan_p5(p):
        esquinas.append(("atras-arriba (el techo)", (fondo, alto)))
    for nm, (ex, ey) in esquinas:
        diag = min(abs(x - ex) + abs(y - ey) for x, y in pts)
        if abs(diag - c) > CARA_DXF_MAX:
            f.append(f"costilla_2d: la esquina {nm} no lleva el chaflan de {c:g}: "
                     f"el punto del contorno mas cercano cae a |dx|+|dy| = "
                     f"{diag:.2f} y el chaflan pide {c:.2f}. Con radio en vez de "
                     f"chaflan la punta sale REDONDA")
    frente = [y for x, y in pts if abs(x) <= CARA_DXF_MAX]
    if (not frente or min(frente) > c + r + CARA_DXF_MAX
            or max(frente) < p["alto_frontal"] - r - CARA_DXF_MAX):
        f.append(f"costilla_2d: el frente no es vertical: el contorno toca x = 0 "
                 f"entre y = {min(frente) if frente else float('nan'):.2f} y "
                 f"{max(frente) if frente else float('nan'):.2f}, y la nariz "
                 f"recta pide un plomo desde el chaflan (y = {c + r:.2f}) hasta "
                 f"el radio de arriba (y = {p['alto_frontal'] - r:.2f})")
    tras = [y for x, y in pts if abs(x - fondo) <= CARA_DXF_MAX]
    y_alto = alto - (c + r if cb._chaflan_p5(p) else r)
    if (not tras or min(tras) > c + r + CARA_DXF_MAX
            or max(tras) < y_alto - CARA_DXF_MAX):
        f.append(f"costilla_2d: el canto trasero no es vertical: toca x = {fondo:.2f} "
                 f"entre y = {min(tras) if tras else float('nan'):.2f} y "
                 f"{max(tras) if tras else float('nan'):.2f}, y se pide un plomo "
                 f"desde el chaflan del talon (y = {c + r:.2f}) hasta "
                 f"{y_alto:.2f}")
    suelo = [x for x, y in pts if abs(y) <= CARA_DXF_MAX]
    if (not suelo or min(suelo) > c + r + CARA_DXF_MAX
            or max(suelo) < fondo - c - r - CARA_DXF_MAX):
        f.append(f"costilla_2d: el suelo no llega a los dos chaflanes: toca y = 0 "
                 f"desde x = {min(suelo) if suelo else float('nan'):.2f} hasta "
                 f"{max(suelo) if suelo else float('nan'):.2f}, y los chaflanes "
                 f"acaban en {c + r:.2f} y {fondo - c - r:.2f}")
    if not f:
        print(f"  costilla_2d: {len(esquinas)} esquinas a chaflan de {c:g} a 45 "
              f"({', '.join(nm.split(' ')[0] for nm, _ in esquinas)}), frente a "
              f"plomo de y = {min(frente):.2f} a {max(frente):.2f}, canto trasero "
              f"a plomo de {min(tras):.2f} a {max(tras):.2f}")
    return f


def taladros_nariz() -> list[str]:
    """La nariz trae sus tres M4 en el pie, y la tabla los mismos tres debajo.

    Dos ficheros y un solo herraje: el M4 atraviesa el pie de la nariz
    (nariz_2d, en el DESARROLLO, a 1.5 D del canto libre del pie -- un canto
    libre no se mueve al plegar) y entra en la tabla (bandeja_base_2d, con el
    mismo diametro que los pies, d_pie_tornillo, porque es el mismo herraje a
    la misma madera). Si uno de los dos se mueve, el tornillo no cae."""
    import clearance_budget as cb

    p = cb.leer_params()
    nz = cb._nariz(p)
    dxf = "nariz_2d"
    if not (PLANS / f"{dxf}.dxf").exists():
        return []                      # de eso ya se queja el bucle de main()
    f: list[str] = []
    cantos = _cantos(dxf)
    leidos = _redondos(dxf)
    d = p["d_M4_paso"] + p["kerf"]
    esperados = [(_x_blank(p, z), 1.5 * p["d_M4_paso"])
                 for z in nz["m4_z"]]
    for ex, ey in esperados:
        cerca = [q for q in leidos
                 if math.hypot(q[0] - ex, q[1] - ey) <= DESVIO_DXF_MAX
                 and abs(q[2] - d) < 0.1]
        if not cerca:
            f.append(f"{dxf}: falta el M4 del pie en ({ex:.2f}, {ey:.2f})")
            continue
        dist = _dist_al_contorno(cantos, (ex, ey))
        if dist < BORDE_MIN_D * p["d_M4_paso"] - DESVIO_DXF_MAX:
            f.append(f"{dxf}: el M4 de ({ex:.2f}, {ey:.2f}) cae a {dist:.2f} mm "
                     f"del canto y se exigen {BORDE_MIN_D * p['d_M4_paso']:.2f}")
    if len(leidos) != len(esperados):
        f.append(f"{dxf}: {len(leidos)} agujeros en el DXF y el modelo pone "
                 f"{len(esperados)}")
    v = p["vuelo_zocalo"]
    d_t = p["d_pie_tornillo"] + p["kerf"]
    tabla = _redondos("bandeja_base_2d")
    for z in nz["m4_z"]:
        ex, ey = v + z, v + nz["m4_x"]
        if not any(math.hypot(q[0] - ex, q[1] - ey) <= DESVIO_DXF_MAX
                   and abs(q[2] - d_t) < 0.1 for q in tabla):
            f.append(f"bandeja_base_2d: falta el taladro de la nariz en "
                     f"({ex:.2f}, {ey:.2f}), d={d_t:.2f}")
    if not f:
        print(f"  {dxf}: {len(esperados)} M4 en el pie a "
              f"{1.5 * p['d_M4_paso']:.2f} del canto libre, y los mismos "
              f"{len(esperados)} en la tabla (d={d_t:.2f})")
    return f


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
    # EL REBAJE DE CHAPA Y SU REBORDE entran en el cupon el 2026-08-30, y son
    # LA RAZON de que el cupon siga existiendo: el reborde es una pared de
    # rehundido_chapa de ancho por rebaje_chapa de alto -- 1 x 3, en el limite
    # de lo que la fresa hace -- y es la unica cota de toda la pieza que se ve.
    # Ninguna planta la puede decir. Cuatro vertices mas: la muesca del rebaje,
    # que deja el reborde entre ella y el canto de la silueta.
    u0, u1 = p["rehundido_chapa"], cb._rehundido_trasera(p)
    z0 = T - p["rebaje_chapa"]
    esperados = [(c, 0.0), (W - c, 0.0), (W, c), (W, R),
                 (W - B, R), (W - B, T),
                 (u1, T), (u1, z0), (u0, z0), (u0, T),
                 (0.0, T), (0.0, c)]
    aristas, comps = _componentes("cupon_anillo_2d")
    if len(comps) != 1:
        return [f"cupon_anillo_2d: {len(comps)} contorno(s) y la seccion del "
                f"anillo es UNO cerrado"]
    pts = {(round(q[0], 3), round(q[1], 3)) for j in comps[0] for q in aristas[j]}
    f: list[str] = []
    nombres = ["arranque del chaflan de la silueta", "arranque del chaflan de "
               "la ventana", "final del chaflan de la ventana",
               "canto del labio", "asiento del rebaje del costado",
               "fondo del rebaje del costado",
               "suelo del rebaje de chapa en el dorso",
               "fondo del rebaje de chapa",
               "cara interior del reborde",
               "reborde en el dorso",
               "dorso en la silueta", "final del chaflan de la silueta"]
    for (x, y), nm in zip(esperados, nombres):
        if not any(math.hypot(q[0] - x, q[1] - y) <= DESVIO_DXF_MAX for q in pts):
            f.append(f"cupon_anillo_2d: falta el vertice '{nm}' en "
                     f"({x:.2f}, {y:.2f}): el perfil dibujado no es el que "
                     f"fresa costilla()")
    if len(pts) != len(esperados):
        f.append(f"cupon_anillo_2d: {len(pts)} vertices y la seccion tiene "
                 f"{len(esperados)}")
    # Y EL REBORDE POR SU ANCHO, no solo por sus vertices: es la cota que el
    # RFQ pregunta, y la que decide si esta pieza se puede hacer. Se mide
    # sobre el fichero, entre el canto de la silueta y la pared del rebaje.
    if not f:
        anchos = sorted(q[0] for q in pts if abs(q[1] - z0) <= DESVIO_DXF_MAX)
        if len(anchos) < 2 or abs(anchos[0] - u0) > DESVIO_DXF_MAX:
            f.append(f"cupon_anillo_2d: el reborde mide "
                     f"{anchos[0] if anchos else float('nan'):.2f} de ancho en "
                     f"el fichero y rehundido_chapa dice {u0:g}. Es LA cota "
                     f"delicada de la pieza y la unica que se ve: el cupon "
                     f"existe para medirla sobre metal")
    if not f:
        print(f"  cupon_anillo_2d: seccion de {W:g} x {T:g}, labio de {R:g}, "
              f"rebaje del costado {B:g} x {T - R:g}, rebaje de chapa "
              f"{u1 - u0:g} x {p['rebaje_chapa']:g} con reborde de {u0:g} x "
              f"{p['rebaje_chapa']:g}, chaflan {c:g} x 45 en las dos aristas "
              f"de la cara -- cupon de {p['cupon_largo']:g} mm")
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


def taladros_marco_ventana() -> list[str]:
    """El marco de la ventana trae sus taladros donde el modelo dice, con
    material alrededor, y su contorno es el de las patas del modelo.

    HERMANA DE taladros_anillo() PERO DEL OTRO LADO: aquella relee el DORSO
    del anillo -- las roscas ciegas donde el marco se atornilla. Esta relee el
    MARCO en si. Sustituye a taladros_placas() (2026-08-29, noche): las tres
    placas, el clip y la escuadra son hoy esta pieza.

    CUATRO CLASES DE TALADRO, y las cuatro se comprueban:
      1. los doce M4 CIEGOS al anillo -- _roscas_marco(), diametro de PASO:
         diez en las tres filas y dos en la pata del suelo;
      2. los seis pasos M4 de riel -- _pasos_riel_marco(). El cajeado (Ø8 x
         prof_cajeado_riel, por el lado del anillo) es NOTA DE MECANIZADO en
         el pliego, no un circulo aqui: un DXF 2D no sabe decir profundidad;
      3. la rosca M3 de la pestana de la banda del valle, dibujada a
         d_M3_rosca (pasante) y medida al canto con d_M3_paso.
    (La brida del miembro alto no lo atraviesa: ahi va la muesca.) Todos a
    BORDE_MIN_D x D del contorno RELEIDO, no de la copia en Python.

    Y EL CONTORNO: por cada pata del modelo, el punto medio de su canto
    exterior y el de su canto interior caen sobre el contorno del fichero.
    Es lo que cruza las dos gemelas -- las bandas de retiro del .scad contra
    los poligonos del budget -- en los ocho tramos, escalones incluidos. Con
    dos salvedades que son de la pieza y no de la puerta: en las tres filas
    la silueta va ABOMBADA (bombeo, hasta 0.78 en la cara de abajo) y las
    patas del budget son rectas, asi que ahi se tolera 1 mm; y las dos patas
    del frente (chaflan y frente) no tienen canto interior propio -- el
    rincon de la nariz las rellena hasta (marco_fondo, marco_fondo) -- y solo
    se mira su canto exterior."""
    import clearance_budget as cb

    p = cb.leer_params()
    dxf = "marco_ventana_2d"
    if not (PLANS / f"{dxf}.dxf").exists():
        return []
    f: list[str] = []
    cantos = _cantos(dxf)
    if not cantos:
        return [f"{dxf}: sin LINEs, no se puede verificar el marco"]
    d4, d3 = p["d_M4_paso"], p["d_M3_paso"]
    esperados = [(f"M4 ciego '{nm}'", c, d4, d4) for nm, c in cb._roscas_marco(p)]
    esperados += [(f"paso M4 de {nm}", c, d4, d4)
                  for nm, c in cb._pasos_riel_marco(p)]
    esperados.append(("M3 pestana valle", cb._m3_pestana(p), p["d_M3_rosca"], d3))
    leidos = _redondos(dxf)
    for etiqueta, c, d, d_canto in esperados:
        cerca = [q for q in leidos
                 if math.hypot(q[0] - c[0], q[1] - c[1]) <= DESVIO_DXF_MAX
                 and abs(q[2] - d) < 0.1]
        if not cerca:
            f.append(f"{dxf}: falta el taladro '{etiqueta}' (d={d:.2f}) en "
                     f"({c[0]:.2f}, {c[1]:.2f})")
            continue
        dist = _dist_al_contorno(cantos, c)
        if dist < BORDE_MIN_D * d_canto - DESVIO_DXF_MAX:
            f.append(f"{dxf}: el taladro '{etiqueta}' cae a {dist:.2f} mm del "
                     f"canto y se exigen {BORDE_MIN_D * d_canto:.2f} "
                     f"({BORDE_MIN_D} x D)")
    if len(leidos) != len(esperados):
        f.append(f"{dxf}: {len(leidos)} agujeros en el DXF y el modelo pone "
                 f"{len(esperados)}")
    # el contorno, pata por pata: el punto medio de cada canto
    for q in cb._marco_ventana(p):
        sm = (q["s0"] + q["s1"]) / 2
        filas = q["nombre"] in ("cara_inf", "valle", "cara_sup")
        tol = 1.0 if filas else 0.05
        for etiqueta, b in (("exterior", q["retiro"]), ("interior", q["fondo"])):
            if etiqueta == "interior" and q["nombre"] in ("chaflan", "frente"):
                continue
            if etiqueta == "exterior" and "escalon" in q:
                # en las patas con escalon el punto medio se mide en el tramo
                # que va a la silueta (retiro 0)
                sm_e = (q["escalon"] + (q["s1"] if q["nombre"] == "cara_inf"
                                        else q["s0"])) / 2
                pt = q["_m"]((sm_e, 0.0))
            elif etiqueta == "exterior" and "muesca" in q:
                # en las patas con muesca (la meseta por su final, la trasera
                # por su arranque) el canto exterior solo existe fuera de ella
                s_mu = q["muesca"][0]
                sm_e = ((q["s0"] + s_mu) / 2 if q["nombre"] == "meseta"
                        else (s_mu + q["s1"]) / 2)
                pt = q["_m"]((sm_e, b))
            else:
                pt = q["_m"]((sm, b))
            dist = _dist_al_contorno(cantos, pt)
            if dist > tol:
                f.append(f"{dxf}: el canto {etiqueta} de la pata '{q['nombre']}' "
                         f"no pasa por ({pt[0]:.2f}, {pt[1]:.2f}) donde el modelo "
                         f"lo pone: el contorno mas cercano queda a {dist:.2f}")
    if not any(m.startswith(dxf + ":") for m in f):
        print(f"  {dxf}: {len(leidos)} taladros verificados a >= {BORDE_MIN_D}xD "
              f"del canto, y el contorno pasa por las {len(cb._marco_ventana(p))} "
              f"patas del modelo")
    return f


def taladros_talon() -> list[str]:
    """El talon trae sus tres M4 en el pie, y la tabla lleva debajo los tres
    del talon y los cuatro del chasis.

    Como taladros_nariz(): dos ficheros y un solo herraje. Los M4 del pie
    atraviesan el talon (talon_2d, en el desarrollo, a 1.5 D del canto libre
    del pie) y entran en la tabla (bandeja_base_2d, con d_pie_tornillo, el
    mismo herraje a la misma madera). Y los cuatro M4 del suelo del chasis --
    que desde el 2026-08-29 por la noche va a la tabla y no a un miembro --
    tienen que estar en la tabla donde chasis_cuerpo_2d los lleva. La fila
    de M3 de la trasera murio con la trasera capturada: el talon no lleva
    mas agujeros redondos que sus tres M4."""
    import clearance_budget as cb

    p = cb.leer_params()
    tl = cb._talon(p)
    f: list[str] = []
    dxf = "talon_2d"
    if (PLANS / f"{dxf}.dxf").exists():
        cantos = _cantos(dxf)
        leidos = _redondos(dxf)
        d4 = p["d_M4_paso"] + p["kerf"]
        esperados = [(_x_blank(p, z),
                      tl["desarrollo"] - 1.5 * p["d_M4_paso"]) for z in tl["m4_z"]]
        for ex, ey in esperados:
            cerca = [q for q in leidos
                     if math.hypot(q[0] - ex, q[1] - ey) <= DESVIO_DXF_MAX
                     and abs(q[2] - d4) < 0.1]
            if not cerca:
                f.append(f"{dxf}: falta el M4 del pie en ({ex:.2f}, {ey:.2f})")
                continue
            dist = _dist_al_contorno(cantos, (ex, ey))
            if dist < BORDE_MIN_D * p["d_M4_paso"] - DESVIO_DXF_MAX:
                f.append(f"{dxf}: el M4 de ({ex:.2f}, {ey:.2f}) cae a {dist:.2f} "
                         f"mm del canto y se exigen "
                         f"{BORDE_MIN_D * p['d_M4_paso']:.2f}")
        # y los alivios de las pestanas: dos por pestana, de alivio_pestana, a
        # caballo de la linea del doblez en el eje de cada corte. NO son
        # agujeros aparte: el circulo se funde con el corte en U y sale como el
        # fondo redondo de una ranura, asi que se buscan sus aristas -- las del
        # poligono que caen en la circunferencia -- y no un CIRCLE.
        r_al = (p["alivio_pestana"] + p["kerf"]) / 2
        ym = tl["desarrollo"] - (tl["pestana_x"] - tl["x_pie"])
        w, k = p["talon_pestana_ancho"], p["corte_pestana"]
        aristas, _ = _componentes(dxf)
        alivios = [(_x_blank(p, zc) + s * (w / 2 + k / 2), ym)
                   for zc in tl["pestana_z"] for s in (-1, 1)]
        for ex, ey in alivios:
            arco = sum(1 for a in aristas
                       if abs(math.hypot(a[0][0] - ex, a[0][1] - ey) - r_al) <= 0.06
                       and abs(math.hypot(a[1][0] - ex, a[1][1] - ey) - r_al) <= 0.06)
            if arco < 6:
                f.append(f"{dxf}: falta el alivio de {2 * r_al:g} de la pestana en "
                         f"({ex:.2f}, {ey:.2f}): {arco} aristas sobre su circunferencia")
        if len(leidos) != len(esperados):
            f.append(f"{dxf}: {len(leidos)} agujeros redondos en el DXF y el modelo "
                     f"pone {len(esperados)} (los tres M4; los alivios de las pestanas "
                     f"van fundidos con el corte en U, y la fila de M3 murio con la "
                     f"trasera capturada)")
    v = p["vuelo_zocalo"]
    tabla = _redondos("bandeja_base_2d")
    d_t = p["d_pie_tornillo"] + p["kerf"]
    for z in tl["m4_z"]:
        ex, ey = v + z, v + tl["m4_x"]
        if not any(math.hypot(q[0] - ex, q[1] - ey) <= DESVIO_DXF_MAX
                   and abs(q[2] - d_t) < 0.1 for q in tabla):
            f.append(f"bandeja_base_2d: falta el taladro del talon en "
                     f"({ex:.2f}, {ey:.2f}), d={d_t:.2f}")
    d4t = p["d_M4_paso"] + p["kerf"]
    for ex, ey in cb._chasis_tornillos_tabla(p):
        if not any(math.hypot(q[0] - ex, q[1] - ey) <= DESVIO_DXF_MAX
                   and abs(q[2] - d4t) < 0.1 for q in tabla):
            f.append(f"bandeja_base_2d: falta el taladro del chasis en "
                     f"({ex:.2f}, {ey:.2f}), d={d4t:.2f}")
    if not f:
        print(f"  talon_2d: 3 M4 en el pie a {1.5 * p['d_M4_paso']:.2f} del canto "
              f"libre; la tabla lleva los 3 del talon (d={d_t:.2f}) y los 4 del "
              f"chasis (d={d4t:.2f})")
    return f


def techo_macizo() -> list[str]:
    """LA MESETA DEL TECHO NO TIENE UN AGUJERO (2026-08-30).

    Samuel, mirando el .blend: "en la pieza miembro alto no me gustan los
    huecos, es una decision erratica del diseno ya que esa parte es sensible a
    que le entren liquidos". Tenia razon: era la unica cara horizontal de
    arriba, y llevaba 16 ranuras mirando al cielo. La salida de aire se mudo a
    la rendija del alero, que mira al SUELO.

    Esta puerta existe porque el resto del fichero no lo dice. guarda_aire()
    calcula un caudal y nunca leyo un DXF; los sobres miden la envolvente, que
    no cambia si alguien vuelve a poner las ranuras dentro; y bridas_techo()
    mira los cuatro M4 y las esquinas. Un techo con ranuras pasaria todo eso.

    Asi que se cuenta: dentro del blank no puede haber NADA cerrado salvo los
    cuatro M4 de las bridas. Si vuelven las ranuras -- por un merge, por
    reactivar meseta_paso_hp, por copiar un modulo viejo -- esto se pone rojo y
    dice cuantas."""
    import clearance_budget as cb

    p = cb.leer_params()
    dxf = "miembro_alto_2d"
    if not (PLANS / f"{dxf}.dxf").exists():
        return [f"{dxf}: FALTA el DXF, no se puede comprobar que la meseta es maciza"]
    leidos = _redondos(dxf)
    d4 = p["d_M4_paso"] + p["kerf"]
    m4 = [q for q in leidos if abs(q[2] - d4) < 0.1]
    otros = [q for q in leidos if abs(q[2] - d4) >= 0.1]
    if otros:
        q = otros[0]
        return [f"{dxf}: hay {len(otros)} agujero(s) que no son M4 de brida, el "
                f"primero de Ø{q[2]:.2f} en ({q[0]:.1f}, {q[1]:.1f}). La meseta "
                f"del techo va MACIZA desde el 2026-08-30: la salida de aire es "
                f"la rendija del alero, no un agujero mirando al cielo"]
    if len(m4) != 4:
        return [f"{dxf}: {len(m4)} taladros de Ø{d4:.2f} y las dos bridas ponen "
                f"4: o falta uno, o hay un agujero de mas en una pieza que tiene "
                f"que ser maciza"]
    # y ninguna ranura: una ranura es obround, no la caza _redondos(). Se cuenta
    # por componentes cerrados dentro del blank, descontando los cuatro M4.
    aristas, comps = _componentes(dxf)
    largo = cb._chapa_largo_rebaje(p)
    dentro = 0
    for comp in comps:
        pts = [q for j in comp for q in aristas[j]]
        cx = sum(q[0] for q in pts) / len(pts)
        cy = sum(q[1] for q in pts) / len(pts)
        ancho = max(q[0] for q in pts) - min(q[0] for q in pts)
        if 1.0 < cx < largo - 1.0 and cy > 1.0 and ancho < largo / 2:
            dentro += 1
    if dentro > len(m4):
        return [f"{dxf}: {dentro} contornos cerrados dentro del blank y solo "
                f"deberian estar los {len(m4)} M4 de las bridas. La meseta lleva "
                f"algo cortado -- si son las ranuras de ventilacion, salieron el "
                f"2026-08-30 y no vuelven: la salida es la rendija del alero"]
    print(f"  {dxf}: meseta MACIZA -- {len(m4)} taladros en el blank, los cuatro "
          f"M4 de las bridas, y ninguna ranura")
    return []


def muescas_del_pie() -> list[str]:
    """LA MUESCA DEL PIE en los desarrollos de la nariz y del talon.

    Es la pieza que hace que las chapas se empotren SIN levantar los pies de la
    tabla: el blank mide lo que entra en rebaje (mas ancho), y en cada punta se
    corta muesca_pie() desde el canto libre del pie hasta la linea de doblez,
    con un alivio de Ø2 a caballo de esa linea para que el pliegue no rasgue
    desde la esquina.

    Ninguna puerta la miraba (revisor del 2026-08-30). Y es la clase de cota
    que se pierde callando: el sobre del DXF no cambia -- la muesca esta DENTRO
    del blank --, los taladros siguen donde estaban, y una chapa sin muesca
    entra igual en la maquina. Lo que pasa es que el pie no apoya: se queda
    2.65 mm en el aire a cada lado, sobre el rebaje del anillo.

    Se mide lo que de verdad hay que cortar: la profundidad de la muesca, y que
    el alivio este SOBRE la linea de doblez -- no antes, donde no sirve, ni
    despues, donde se come el pie."""
    import clearance_budget as cb

    p = cb.leer_params()
    fallos: list[str] = []
    m = cb._muesca_pie(p)
    r_al = (p["alivio_pestana"] + p["kerf"]) / 2
    bd = cb._bd_angulo(p, 45.0)
    for dxf, pie, y_pie, s in (("nariz_2d", p["nariz_pie"], 0.0, +1),
                               ("talon_2d", p["talon_pie"], None, -1)):
        if not (PLANS / f"{dxf}.dxf").exists():
            fallos.append(f"{dxf}: FALTA el DXF, no se puede medir la muesca")
            continue
        largo = cb._chapa_largo_rebaje(p)
        if y_pie is None:                       # el talon lleva el pie arriba
            y_pie = cb._talon(p)["desarrollo"]
        y_dob = y_pie + s * (pie - bd / 2)
        aristas, _ = _componentes(dxf)
        # LA PARED DE LA MUESCA: una arista a plomo en x = m y en x = largo - m,
        # entre el canto libre del pie y la linea de doblez.
        for x_esp, lado in ((m, "izquierda"), (largo - m, "derecha")):
            hay = any(abs(a[0][0] - x_esp) <= DESVIO_DXF_MAX
                      and abs(a[1][0] - x_esp) <= DESVIO_DXF_MAX
                      and abs(a[0][1] - a[1][1]) > 1.0
                      and min(a[0][1], a[1][1]) >= min(y_pie, y_dob) - 1.0
                      and max(a[0][1], a[1][1]) <= max(y_pie, y_dob) + 1.0
                      for a in aristas)
            if not hay:
                fallos.append(
                    f"{dxf}: falta la pared de la muesca {lado} del pie, a "
                    f"plomo en x = {x_esp:.2f} entre y = {min(y_pie, y_dob):.2f} "
                    f"y {max(y_pie, y_dob):.2f}. Sin ella el pie mide lo mismo "
                    f"que lo que entra en rebaje y se queda {m:.2f} mm en el "
                    f"aire a cada lado, sobre el rebaje del anillo")
        # EL ALIVIO, centrado en la esquina interior y SOBRE la linea de doblez
        for x_esp, lado in ((m, "izquierda"), (largo - m, "derecha")):
            arco = sum(1 for a in aristas
                       if abs(math.hypot(a[0][0] - x_esp, a[0][1] - y_dob) - r_al)
                       <= 0.06)
            if arco < 3:
                fallos.append(
                    f"{dxf}: falta el alivio de Ø{p['alivio_pestana']:g} en la "
                    f"esquina {lado} de la muesca, centrado en ({x_esp:.2f}, "
                    f"{y_dob:.2f}) -- sobre la linea de doblez, que esta a "
                    f"largo - BD/2 del canto y no a largo. Sin el, el pliegue "
                    f"rasga desde la esquina viva")
    if not fallos:
        print(f"  nariz_2d y talon_2d: muesca del pie de {m:.2f} en cada punta "
              f"hasta la linea de doblez, con su alivio de "
              f"Ø{p['alivio_pestana']:g} a caballo de ella")
    return fallos


def bridas_techo() -> list[str]:
    """El desarrollo del techo trae sus cuatro M4 de brida donde el modelo los
    pone y, con el chaflan (variante B), el relieve y la esquina cortada de
    cada brida.

    LA UNICA CHAPA DE ESTA TANDA SIN PUERTA PROPIA hasta que el revisor del PR
    lo dijo: su sobre de +-4 mm dejaba pasar techo_labio 18 -> 20 y
    corte_pestana 1.5 sin decir nada. Se relee: los cuatro M4 (a
    brida_raiz y a 1.5 D del canto libre de cada lengueta, a dist_rosca_ciega
    del canto de arriba de la cara trasera), y en B los dos relieves de
    corte_pestana en la linea del doblez (de techo_labio a techo_labio +
    chaflan - t) y las dos aristas a 45 de la esquina de arriba (3 x 3)."""
    import clearance_budget as cb

    p = cb.leer_params()
    dxf = "miembro_alto_2d"
    if not (PLANS / f"{dxf}.dxf").exists():
        return []
    f: list[str] = []
    # EL BLANK DEL TECHO CRECIO 5.0 EL 2026-08-30: ya no mide el vano entre
    # caras sino lo que entra en rebaje, y las dos bridas doblan de SUS puntas,
    # no de las de antes. Con ancho_util aqui, los cuatro M4 salian a 5 mm de
    # donde estan y el fichero correcto daba rojo.
    au = cb._chapa_largo_rebaje(p)
    bd = cb._bd_miembro(p)
    b = cb._bridas(p)[0]
    t, c = p["t_costilla"], p["chaflan_nariz"]
    cara_alto = (p["techo_labio"] + c) if cb._chaflan_p5(p) else p["banda_trasera"]
    y_m4 = cara_alto - p["dist_rosca_ciega"]
    leidos = _redondos(dxf)
    d4 = p["d_M4_paso"] + p["kerf"]
    esperados = []
    for s in b["s_m4"]:
        esperados += [(bd - s, y_m4), (au - bd + s, y_m4)]
    for ex, ey in esperados:
        if not any(math.hypot(q[0] - ex, q[1] - ey) <= DESVIO_DXF_MAX
                   and abs(q[2] - d4) < 0.1 for q in leidos):
            f.append(f"{dxf}: falta el M4 de brida en ({ex:.2f}, {ey:.2f})")
    if len(leidos) != len(esperados):
        f.append(f"{dxf}: {len(leidos)} agujeros redondos y el modelo pone "
                 f"{len(esperados)} (los M4 de las dos bridas)")

    # EL RADIO DE LAS ESQUINAS DE LA BRIDA (2026-08-30, ronda 2 del revisor).
    # Ninguna puerta lo leia del fichero: radio_brida = 1 quedaba VERDE. Y no
    # es cosmetico -- el cajeado donde la brida apoya lo fresa una Ø3, o sea
    # que sus esquinas interiores salen a R1.5, y una brida de esquina mas
    # cerrada no asienta: se monta sobre el radio y trabaja en voladizo.
    # Se cuenta el arco: una esquina a R2 deja un cordon de segmentos a esa
    # distancia de su centro, y una viva no deja ninguno.
    aristas_b, _ = _componentes(dxf)
    r_b = p["radio_brida"]
    v_b = cb._bridas(p)[0]
    y_v = techo_cara_alto = p["techo_labio"] + p["chaflan_nariz"]
    for lado, x0 in ((0, 0.0), (1, au)):
        # la esquina de ABAJO del vuelo, la que no toca ni el chaflan ni el
        # relieve: su centro esta a r_b de las dos caras del vuelo.
        vuelo = p["brida_largo"] - cb._bd_miembro(p)
        xc = (x0 - vuelo + r_b) if lado == 0 else (x0 + vuelo - r_b)
        yc = y_v - t - p["brida_ancho"] + r_b
        arco = sum(1 for a in aristas_b
                   if abs(math.hypot(a[0][0] - xc, a[0][1] - yc) - r_b) <= 0.08)
        if arco < 3:
            f.append(f"{dxf}: la esquina de abajo del vuelo de la brida {lado} "
                     f"no lleva el radio R{r_b:g} que el modelo pide (centro "
                     f"{xc:.2f}, {yc:.2f}): el cajeado lo fresa una "
                     f"Ø{p['fresa_d']:g} y sus esquinas salen a "
                     f"R{p['fresa_d']/2:g}; una brida mas cerrada se monta "
                     f"sobre el radio y no asienta")

    if cb._chaflan_p5(p):
        aristas, _ = _componentes(dxf)
        k = p["corte_pestana"]
        y_r0 = p["techo_labio"]
        for lado, x0 in ((0, 0.0), (1, au)):
            # el relieve: una arista vertical en la cara exterior del corte,
            # desde la linea del doblez (techo_labio); la esquina a 45 le
            # corta la punta, asi que se le pide al menos 1 mm de alto
            x_rel = x0 - k if lado == 0 else x0 + k
            relieve = any(abs(a[0][0] - x_rel) <= 0.05 and abs(a[1][0] - x_rel) <= 0.05
                          and min(a[0][1], a[1][1]) <= y_r0 + 0.05
                          and max(a[0][1], a[1][1]) >= y_r0 + 1.0 for a in aristas)
            if not relieve:
                f.append(f"{dxf}: falta el relieve de {k:g} de la brida {lado} "
                         f"junto a la tira del chaflan (x = {x_rel:.2f}, desde y = "
                         f"{y_r0:.2f})")
            # la esquina: una arista a 45 sobre la recta v = (cara_alto - c + t)
            # + |x - x0|, de al menos 2 mm, dentro del vuelo de c - 2t
            v0 = cara_alto - c + t
            def en_recta(q):
                return (abs(q[1] - abs(q[0] - x0) - v0) <= 0.1
                        and -0.1 <= (x0 - q[0] if lado == 0 else q[0] - x0) <= c - 2 * t + 0.1)
            esquina = any(en_recta(a[0]) and en_recta(a[1])
                          and abs(abs(a[1][0] - a[0][0]) - abs(a[1][1] - a[0][1])) <= 0.1
                          and math.hypot(a[1][0] - a[0][0], a[1][1] - a[0][1]) >= 2.0
                          for a in aristas)
            if not esquina:
                f.append(f"{dxf}: falta la esquina a 45 de la brida {lado} "
                         f"(la recta v = {v0:.2f} + |x - {x0:.2f}|, hasta "
                         f"{c - 2 * t:g} de vuelo)")
    if not f:
        print(f"  {dxf}: 4 M4 de brida a {b['s_m4'][0]:.2f} y {b['s_m4'][1]:.2f} "
              f"del doblez" + (", con relieve y esquina a 45 en las dos bridas"
                                if cb._chaflan_p5(p) else ""))
    return f


def pestanas_talon() -> list[str]:
    """El talon trae las ventanas de sus pestanas (talon_pestana_n) donde el
    modelo las pone: un corte en U de tres lados, hacia el canto libre del
    pie, con la linea del doblez sin cortar.

    Son la unica retencion hacia dentro del canto de abajo de la trasera
    entre los anillos (2026-08-29, noche, 2), y un DXF sin ellas es un talon
    que se pliega igual y no sujeta nada. Se buscan las tres aristas de cada
    U: las dos a lo largo del desarrollo, en x = centro +- ancho/2 y entre
    y = doblez e y = doblez + desarrollo de la pestana, y la del fondo, en y
    = doblez + desarrollo, de un lado al otro."""
    import clearance_budget as cb

    p = cb.leer_params()
    tl = cb._talon(p)
    dxf = "talon_2d"
    if not (PLANS / f"{dxf}.dxf").exists():
        return []
    aristas, _ = _componentes(dxf)
    d = tl["desarrollo"]
    ym = d - (tl["pestana_x"] - tl["x_pie"])
    dv = tl["pestana_dev"]
    w = p["talon_pestana_ancho"]
    tol = 0.05
    f: list[str] = []
    # el corte va POR FUERA de la pestana: lo que se busca son las aristas
    # que la delimitan -- sus dos lados, de y = doblez a y = doblez +
    # desarrollo, y su fondo -- que son las caras interiores del corte en U
    # el alivio de cada esquina se come el arranque del lado: el lado empieza
    # donde el circulo cruza la cara del corte, a r_al*cos(asin(k/2r)) del doblez
    r_al = (p["alivio_pestana"] + p["kerf"]) / 2
    y_lado = ym + math.sqrt(max(r_al ** 2 - (p["corte_pestana"] / 2) ** 2, 0.0))
    for zc in tl["pestana_z"]:
        zb = _x_blank(p, zc)
        lados = 0
        for x_esp in (zb - w / 2, zb + w / 2):
            if any(abs(a[0][0] - x_esp) <= tol and abs(a[1][0] - x_esp) <= tol
                   and min(a[0][1], a[1][1]) <= y_lado + 0.2
                   and max(a[0][1], a[1][1]) >= ym + dv - tol for a in aristas):
                lados += 1
        fondo_ok = any(abs(a[0][1] - (ym + dv)) <= tol and abs(a[1][1] - (ym + dv)) <= tol
                       and min(a[0][0], a[1][0]) <= zb - w / 2 + tol
                       and max(a[0][0], a[1][0]) >= zb + w / 2 - tol for a in aristas)
        if lados < 2 or not fondo_ok:
            f.append(f"{dxf}: falta la ventana de la pestana centrada en x={zb:.2f} "
                     f"(lados en x = {zb - w / 2:.2f} y {zb + w / 2:.2f} de y = "
                     f"{ym:.2f} a {ym + dv:.2f}, fondo en y = {ym + dv:.2f}): "
                     f"{lados} lados y fondo {'si' if fondo_ok else 'no'}")
    if not f:
        print(f"  talon_2d: {len(tl['pestana_z'])} ventanas de pestana de {w:g} x "
              f"{dv:.2f} con el doblez en y = {ym:.2f}, hacia el canto libre del pie, "
              f"con alivio de {p['alivio_pestana']:g} en las esquinas")
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
    # de la fila 1U, todos fijados de punta al marco. Todos viven dentro del
    # contorno estatico; que el superior quepa en el vertice es justo la cota
    # que obligo a engordar marco_remate a 16. No hay cuerpos excluidos.
    cuerpos = [(n, cb._esquinas_er(p, c, p[a]))
               for n, c, a in zip(cb.NOMBRES_CR, cr, cb.ANGS_CR)]
    cuerpos += [(f"fila 1U {i}", cb._esquinas_er(p, c, 90.0))
                for i, c in enumerate(cb._centros_rail_1u(p, P, cr))]
    # LOS DOS LABIOS (techo y talon). El del talon arranca sobre el chaflan de
    # P6 y no necesita recorte; el del techo, con la banda plana (A), dobla en
    # la esquina de arriba con radio_chapa y su caja llega al vertice vivo
    # pero la chapa no: se recorta radio_chapa por el lado del doblez. Con el
    # chaflan (B) arranca bajo el chaflan de P5 y tampoco.
    # Y DONDE EL LABIO MUERE CONTRA UN CHAFLAN, el contorno redondea la
    # esquina del chaflan con radio_chapa: la tangente queda r x tan(22.5)
    # dentro del vertice, y el labio empieza (o acaba) ahi.
    r_ch = p["radio_chapa"]
    tg = r_ch * math.tan(math.radians(22.5)) + 0.05
    recorte = {"trasero alto": (0.0, -tg if cb._chaflan_p5(p) else -r_ch),
               "talon": (tg, 0.0)}
    cuerpos += [(n, [(c[x], c[y] + (recorte[n][0] if y == 3 else recorte[n][1]))
                     for x in (1, 2) for y in (3, 4)])
                for n, c in miembros.items()]
    # LAS PLACAS Y LAS BRIDAS entran el 2026-08-28, y esta es LA puerta que
    # dice donde acaban. Una placa corre el tramo entero pegada a la silueta:
    # si su extremo se pasa de la tangente del redondeo, la esquina se sale por
    # fuera del contorno y no lo caza nadie mas -- solapes() compara cuerpo
    # contra cuerpo y una placa que asoma por el borde no choca con nada. En
    # HEAD dos esquinas de placa asomaban 0.59 y 0.71 mm y las dos puertas
    # daban verde. Las placas pasan su POLIGONO REAL, chaflan incluido.
    # EL MARCO DE LA VENTANA, pata por pata con su poligono real (escalones y
    # muesca incluidos): en las tres filas va pegado a la silueta y sus
    # extremos se retiran la tangente del redondeo; en los demas tramos va
    # retirado bajo la chapa. Una esquina que se pase del redondeo asoma por
    # fuera y no la caza nadie mas. Y la brida del miembro alto, en la franja
    # de la meseta.
    cuerpos += [(f"marco {q['nombre']}", q["poligono"])
                for q in cb._marco_ventana(p)]
    cuerpos += [(f"brida {b['nombre']}", b["poligono"]) for b in cb._bridas(p)]
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
    # los 4 M4 del suelo a la tabla (2026-08-29, noche; eran 2 M5 de pared)
    anclajes = len(cb._chasis_tornillos(p))
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
    tl = cb._talon(p)
    x_frente = p["alto_frontal"] / 2 + p["d_pie"] / 2
    x_trasero = tl["x_chaflan"] - p["talon_pie"] / 2  # centro_talon().x: el pie va del chaflan hacia dentro
    d_pie_taladro = p["d_pie_tornillo"] + p["kerf"]
    esperados_pie = [(v + wz, v + wx)
                     for wx in (x_frente, x_trasero)
                     for wz in (p["d_pie"] / 2, p["ancho_total"] - p["d_pie"] / 2)]
    redondos = _redondos("bandeja_base_2d")
    # LOS TRES DE LA NARIZ llevan el mismo diametro (mismo herraje a la misma
    # tabla) y NO son pies: se apartan por posicion, y los cuenta
    # taladros_nariz(). Sin esto, el censo de pies decia 7.
    # Y LOS TRES DEL TALON Y LOS CUATRO DEL CHASIS (2026-08-29, noche), por lo
    # mismo: mismo diametro, se apartan por posicion y los cuenta
    # taladros_talon().
    nz = cb._nariz(p)
    de_otros = ([(v + z, v + nz["m4_x"]) for z in nz["m4_z"]]
                + [(v + z, v + tl["m4_x"]) for z in tl["m4_z"]]
                + cb._chasis_tornillos_tabla(p))
    pies = [q for q in redondos if abs(q[2] - d_pie_taladro) < 0.1
            and not any(math.hypot(q[0] - ex, q[1] - ey) <= DESVIO_DXF_MAX
                        for ex, ey in de_otros)]
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




# Las dos chapas traseras con fila de M3, nombre de DXF -> (miembro, ancho
# sobre el que se reparte la fila, desfase de la fila en el blank). LA FILA
# ES LA DE LA TRASERA -- los mismos cinco centros --, y la trasera es
# 2*hol_piel mas estrecha que el hueco entre anillos: el miembro alto cruza el
# hueco entero y lleva la fila corrida hol_piel; el talon mide lo que la
# trasera y la lleva a ras. (Era miembro_bajo/miembro_alto con la fila sobre
# ancho_util hasta el 2026-08-29 por la noche.)
# VACIO desde la trasera capturada (2026-08-29, noche, 2): las dos filas de
# M3 de las bandas murieron con los tornillos de la trasera, y ni el techo ni
# el talon llevan reticula. La puerta se queda por si vuelve un miembro con
# fila; hoy no revisa nada.
MIEMBROS_DXF: dict[str, tuple[str, str, object]] = {}


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
    # EL BLANK DEL TECHO CRECIO 5.0 EL 2026-08-30: ya no mide el vano entre
    # caras sino lo que entra en rebaje, y las dos bridas doblan de SUS puntas,
    # no de las de antes. Con ancho_util aqui, los cuatro M4 salian a 5 mm de
    # donde estan y el fichero correcto daba rojo.
    au = cb._chapa_largo_rebaje(p)
    paso = p["reticula_paso"]
    n = max(1, round(au / paso))
    d_ret = p["d_M3_paso"] + p["kerf"]
    f: list[str] = []
    for dxf, (miembro, sobre, desfase) in MIEMBROS_DXF.items():
        ancho = cb._trasera_au(p) if sobre == "trasera" else au
        off = p[desfase] if isinstance(desfase, str) else desfase
        rejilla = [off + ancho * (i + 0.5) / n for i in range(n)]
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
                         f"(paso {paso:.0f}, {n} sobre {ancho:.2f}). Con la ranura "
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
            # EN 2D desde el 2026-08-29 por la noche: el talon lleva sus M4 en
            # el pie, a 28 mm de la fila en y y justo encima de una columna en
            # x, y medir solo en x los daba por rasgados
            d = min(math.hypot(q[0] - x, q[1] - ys[0]) for x in rejilla) if ys \
                else min(abs(q[0] - x) for x in rejilla)
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
                  f"{ancho:.2f}" + (f", mas {extra} agujero(s) declarado(s) con "
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
    fallos += anillo_tiene_bolsillo_trasero()
    fallos += anillo_tiene_chaflan()
    fallos += seccion_del_cupon()
    fallos += taladros_anillo()
    fallos += taladros_marco_ventana()
    fallos += taladros_nariz()
    fallos += taladros_talon()
    fallos += pestanas_talon()
    fallos += bridas_techo()
    fallos += techo_macizo()
    fallos += muescas_del_pie()
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
