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


def _sobres() -> dict[str, tuple[float, float, float, float]]:
    import clearance_budget as cb

    p = cb.leer_params()
    g = cb.perfil(p)
    _, planchas, _ = cb._cajas_solidas(p)

    dims: dict[str, tuple[float, float]] = {
        # el costado no es una plancha del cuerpo: es la mejilla, y su DXF es
        # la silueta lateral entera.
        "costado_2d": (cb.fondo(p), g["alto_total"]),
        # LA COSTILLA NO COMPARTE ENVOLVENTE CON EL COSTADO, y es a proposito:
        # su DXF es el DESARROLLO PLANO, no el contorno de la pieza doblada.
        # Sale mas grande porque cada tramo con ala saca su rectangulo por la
        # normal exterior. Derivado, no escrito a mano -- si el .scad y esta
        # cuenta se separan, el bbox se sale del sobre y aqui se entera.
        "costilla_2d": cb.bbox_desarrollo_costilla(p),
        # cupon: 2*margen + (n-1)*paso de la escalera, x 62 de alto. No sale
        # de _cajas_solidas porque no es una pieza del case.
        "coupon": (136.0, 62.0),
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


def _contorno_costado() -> list:
    """Aristas del contorno EXTERIOR de costado_2d, releidas del DXF.

    Se valida contra el ARCHIVO, no contra una copia de redondear() en Python:
    replicarla aqui seria la tercera copia de la misma matematica, y la version
    que cuenta es la que salio al fichero que va al laser. Los agujeros salen
    como componentes aparte; el contorno es la de bbox mas grande."""
    aristas, componentes = _componentes("costado_2d")
    if not aristas:
        return []
    def extension(comp):
        px = [p[0] for j in comp for p in aristas[j]]
        py = [p[1] for j in comp for p in aristas[j]]
        return (max(px) - min(px)) * (max(py) - min(py))

    return [aristas[j] for j in max(componentes, key=extension)]


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


# Distancia MINIMA del centro de un taladro al canto, en diametros. La regla de
# oficio para plastico es 2xD y lo ideal seria exigir eso, pero los tres
# largueros del plano trasero viven entre 1.94 y 2.0 D por geometria -- ponerlo
# en 2.0 seria una puerta gritando en falso sobre algo verificado. A 1.5 D queda
# margen de sobra y sigue cazando el fallo de verdad: mover un larguero contra
# una curva y no enterarse. Y el aplastamiento real no es el limite: el eje de
# la tapa, que es el M5 mas cargado del case, trabaja a 0.33 MPa sobre acrilico
# que aguanta ~100.
BORDE_MIN_D = 1.5


# taladros_con_material() MURIO el 2026-08-27, y conviene que quede dicho por
# que en vez de dejar la funcion vacia. Medía que cada taladro del costado
# tuviera acrilico alrededor -- 1.5 x D desde el centro al canto -- porque un M5
# a dos milimetros de una curva no falla al montarlo, falla al APRETARLO, y raja
# el costado. Esa puerta ya no tiene sujeto: el costado no lleva un solo
# taladro. Su criterio no se perdio, se MUDO con los tornillos: vive en
# taladros_costilla(), que ademas pide los dos cantos de la banda -- cosa que
# aqui no hacia falta porque el acrilico es macizo.

# Cuanto puede desviarse un agujero del DXF respecto de donde el modelo lo
# pone. No es tolerancia de fabricacion -- es cuanto se permite que MIENTAN el
# uno sobre el otro, y la respuesta es casi nada: son el mismo numero pasado
# por OpenSCAD.
DESVIO_DXF_MAX = 0.02


def agujeros_donde_toca() -> list[str]:
    """Los agujeros del DXF caen donde el modelo dice. Leidos DEL FICHERO.

    Esta puerta existe por el issue #51, y el issue traia su propia
    reproduccion: mover las dos filas de bandeja_base_2d +10 y -10 mm, exportar,
    y las dos puertas daban VERDE. check_dxf solo miraba el bbox -- que no
    cambia, porque las filas viven DENTRO del contorno -- y alineacion() en
    clearance_budget comparaba el modelo contra si mismo sin abrir un .dxf en
    ningun momento. Un fichero con los agujeros en otro sitio pasaba entero.

    Se comprueban dos cosas distintas segun lo que se pueda comparar sin
    duplicar formulas:

    COSTADO: comparacion EXACTA. costado_2d se dibuja directamente en las
    coordenadas de pts_perfil(), asi que los centros del DXF y los de
    _centros_rail()/_centros_transversal() viven en el mismo sistema y se restan
    sin traducir nada. Once agujeros, uno por larguero.

    PLANCHAS: se comprueba lo que es invariante dentro de su propio plano --
    cuantas filas hay, cuantos agujeros por fila, el paso en X, y la SEPARACION
    entre filas. Esa ultima es la que atrapa la reproduccion del issue: mover
    una fila +10 y otra -10 cambia su separacion en 20 mm. No se comprueba la
    posicion absoluta dentro de la plancha porque eso exigiria replicar aqui la
    colocacion 3D de cada pieza, que es justo la copia de matematica que este
    fichero evita a proposito."""
    import clearance_budget as cb

    p = cb.leer_params()
    P = cb._vertices(p)
    cr = cb._centros_rail(p, P)
    ce = cb._centros_transversal(p, P, cr)
    f: list[str] = []

    # --- costado: CERO agujeros ---
    # Fue comparacion exacta de once centros contra el DXF, y era de las
    # puertas mas utiles del fichero: costado_2d se dibuja en las coordenadas
    # de pts_perfil(), asi que los centros del modelo y los del fichero se
    # restaban sin traducir nada. El 2026-08-27 la pieza se quedo sin un solo
    # tornillo y la comparacion se quedo sin nada que comparar. Lo que queda es
    # el censo -- que siga sin ellos -- y eso lo pide taladros_costilla() con
    # su mensaje, asi que aqui no se repite.

    # --- planchas: filas, paso y separacion ---
    _, _, filas = cb._cajas_solidas(p)
    # DEL PRESUPUESTO, no recalculado: desde el 2026-08-26 ancho_util resta
    # tambien las dos alas de costilla, y una copia a mano de la formula aqui
    # se desincroniza del original en cuanto se toque t_costilla.
    au = cb.perfil(p)["ancho_util"]
    n = max(1, round(au / 100))
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
            ancho = cb.perfil(p)["ancho_util"]
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

    Ahora el costado no lleva un solo tornillo: queda capturado entre las dos
    alas de la costilla, que lo agarran por TODO su perimetro. El vano deja de
    ser "distancia a un punto" y pasa a ser "distancia al canto de la ventana",
    que es apoyo continuo.

    Y EL 2026-08-27 EL APOYO LE LLEGA POR LA OTRA CARA. Con la inversion, la
    costilla pasa a ser la capa de FUERA (z 0..t_costilla) y el acrilico queda
    por dentro: el marco ya no lo sostiene desde atras, lo PISA desde delante, y
    la junta de EPDM lo empuja contra las piezas interiores. La geometria del
    barrido no cambia -- la ventana esta en el mismo sitio en X y en Y, que es
    el plano donde esta puerta mide -- pero el modelo mental si, y el numero
    tiene que salir igual: vano 65.2 mm, flecha 0.11. Si esos dos se mueven,
    algo mas cambio y hay que averiguar que antes de seguir. Se mide contra costilla_2d.dxf -- el fichero, no una
    copia del offset en Python -- por la misma razon que el contorno.

    Lo que eso vale, y es el pago de todo el esqueleto: el vano cae de 119.0 a
    65.2 mm y la flecha de 0.38 a 0.11.

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
            f"se arregla con un anclaje: el apoyo es la VENTANA de la costilla, "
            f"asi que o se ensancha ala_costilla o sube t_cheek (la flecha va "
            f"con t^3)")
    if sigma > cb.SIGMA_PMMA:
        fallos.append(
            f"costado_2d: {sigma:.1f} MPa bajo la mano contra el umbral de "
            f"{cb.SIGMA_PMMA} (#106) — esto no deberia pasar antes que la "
            f"flecha, asi que revisa t_cheek y carga_mano antes de creerlo")
    print(f"costado: PIEL sin tornillos, apoyada en la banda de la costilla; "
          f"vano libre {vano:.1f} mm "
          f"(x={donde[0]:.0f}, y={donde[1]:.0f}); con {P:.0f} N se hunde "
          f"{flecha:.2f} mm (techo {p['flecha_costado_max']:.2f}, vano maximo "
          f"{vano_max:.0f}) y trabaja a {sigma:.1f} MPa (fluencia "
          f"{cb.SIGMA_PMMA})")
    return fallos


def railes_dentro_del_costado() -> list[str]:
    """Cada larguero 2020 tiene que caber DENTRO del acrilico del costado.

    Esto no lo miraba nadie. `solapes()` compara railes contra railes y contra
    planchas, o sea cuerpo contra cuerpo: un rail que se sale por el borde del
    costado no solapa con NADA y pasa en verde. Y la comprobacion se volvio
    urgente al redondear las esquinas en punta, porque el redondeo QUITA
    material justo donde viven dos largueros (el de la base delantera se apoya
    en el rincon del frente, que es el que mas radio se come).

    Se valida contra el CONTORNO RELEIDO DEL DXF, no contra una copia de la
    funcion redondear() en Python. Es a proposito: replicarla aqui es la
    tercera copia de la misma matematica, y la version que cuenta es la que
    salio al archivo que va al laser. Los centros y los angulos si vienen del
    budget -- el DXF sabe donde estan los agujeros pero no que rail es cual ni
    cuanto va girado."""
    import clearance_budget as cb

    f: list[str] = []
    contorno = _contorno_costado()
    if not contorno:
        return ["costado_2d: sin LINEs, no se puede verificar el contorno"]

    def dentro(pt) -> bool:
        return _dentro(contorno, pt)

    p = cb.leer_params()
    P = cb._vertices(p)
    cr = cb._centros_rail(p, P)
    ce = cb._centros_transversal(p, P, cr)
    r = p["rail"] / 2
    # Los railes de PANEL van girados con su cara; los de esqueleto, a plomo.
    # El signo del giro es -angulo, igual que en el modulo rails() del .scad:
    # un cuadrado girado -49 grados deja un par de caras a +41 del eje X, que
    # es justo la inclinacion de una cara a 49 grados DE LA VERTICAL. Con el
    # signo al reves la comprobacion acusaba a los cuatro railes de panel de
    # salirse -- eran falsos positivos, y con el signo bueno se ve que su cara
    # queda a 1.63 mm del plano del panel, o sea el t_panel de diseno.
    # Cada elemento aporta sus CUATRO ESQUINAS ya en coordenadas del perfil, no
    # un semilado: los rieles de panel son el EUROrack real (27.4 x 10, girado
    # con su cara) y los de esqueleto son 2020 rectos, asi que no hay una sola
    # cota que valga para todos.
    #
    # Aqui estan los CUATRO railes de panel, incluido el de arriba de la tapa:
    # cerrada, la tapa vive dentro del contorno como todo lo demas, y que ese
    # riel quepa en el vertice es justo la cota que obligo a engordar
    # marco_remate a 16. No hay ningun cuerpo excluido -- la bisagra que asomaba
    # por diseno ya no existe: el eje es el propio M5 del riel.
    cuerpos = [(n, cb._esquinas_er(p, c, p[a]))
               for n, c, a in zip(cb.NOMBRES_CR, cr, cb.ANGS_CR)]
    cuerpos += [(n, [(c[0] + dx, c[1] + dy)
                     for dx in (-r, r) for dy in (-r, r)])
                for n, c in ce.items()]
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
                f.append(f"costado_2d: el larguero '{nombre}' se sale del "
                         f"acrilico -- esquina ({ex:.1f}, {ey:.1f}) fuera del "
                         f"contorno (centro {cx:.1f}, {cy:.1f})")
                break
    if not f:
        print(f"  costado_2d: los {len(cuerpos)} largueros caben dentro del "
              f"contorno ({len(contorno)} aristas de perimetro)")
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


def taladros_costilla() -> list[str]:
    """Todos los tornillos del case viven en la COSTILLA, y no en el acrilico.

    Dos cosas, y hacen falta las dos. La primera es que esten AQUI con material
    alrededor; la segunda es que YA NO ESTEN ALLI. Sin la segunda, mover un
    taladro es anadirlo: el costado saldria al taller con agujeros que ya no
    sirven para nada y que le quitan material justo donde el radio de la
    esquina en punta ya andaba corto.

    EMPEZO CON LOS 4 M4 DE RIEL el 2026-08-26 y el 27 recibio los M5 de las
    transversales, cuando el costado quedo sin un solo tornillo estructural.

    EL CANTO QUE MANDA ES EL DE DENTRO. La costilla es una BANDA de
    `ala_costilla` de ancho, asi que cada taladro tiene dos bordes de los que
    apartarse y el critico es el de la ventana: los centros de riel caen a ~16
    mm del contorno exterior -- de sobra -- y eso los dejaba a 4 mm de la
    ventana con una banda de 20. La spec (10) ya lo habia dejado escrito como
    cota pendiente: la cota definitiva sale de que le cabe al tornillo del
    Z-Rail. Esta puerta es donde se cerro.

    Se mide contra el DXF releido, no contra `ala_costilla` en aritmetica: la
    banda sale de un `offset(delta=-ala_costilla)` de OpenSCAD sobre un contorno
    ya redondeado, y un offset sobre esquinas redondeadas no conserva el ancho
    en las curvas. La cifra que cuenta es la del archivo que va al laser."""
    import clearance_budget as cb

    f: list[str] = []
    cantos = _cantos("costilla_2d")
    if not cantos:
        return ["costilla_2d: sin LINEs, no se pueden verificar los taladros"]
    p = cb.leer_params()
    P = cb._vertices(p)
    cr = cb._centros_rail(p, P)
    ct = cb._centros_transversal(p, P, cr)
    # DOS DIAMETROS, y el margen se exige en diametros: con un solo `d` el
    # criterio saldria 22 % duro en unos y 22 % blando en otros. Es la misma
    # leccion que traia taladros_con_material() cuando esto vivia en el
    # acrilico, y se muda con los taladros.
    esperados = ([(nm, c, p["d_M4_paso"], "M4")
                  for nm, c in zip(cb.NOMBRES_CR, cr)]
                 + [(nm, c, p["d_M5_paso"], "M5") for nm, c in ct.items()]
                 # el M3 de la pestana de la tapa del valle, que atraviesa esta
                 # chapa y la pestana doblada. Es el mas apretado de los tres
                 # diametros: cae cerca del vertice CONCAVO P[3], y un concavo
                 # se come material al vaciar la ventana en vez de anadirlo.
                 + [("pestana del valle",
                     (cb._pv_x(p, ct), P[3][1] - cb._pv(p)["a"]),
                     p["d_M3_paso"], "M3")])

    # 1. estan en la costilla, donde el modelo dice, y con material alrededor
    redondos = _redondos("costilla_2d")
    peor, peor_nm, peor_d = float("inf"), "", 1.0
    for nm, c, d, rosca in esperados:
        cerca = [q for q in redondos
                 if math.hypot(q[0] - c[0], q[1] - c[1]) <= DESVIO_DXF_MAX
                 and abs(q[2] - (d + p["kerf"])) < 0.1]
        if not cerca:
            f.append(f"costilla_2d: falta el {rosca} de '{nm}' en ({c[0]:.2f}, "
                     f"{c[1]:.2f}). Los Z-Rails y las transversales atornillan "
                     f"a la costilla desde el 2026-08-27, no al acrilico")
            continue
        dist = _dist_al_contorno(cantos, c)
        if dist / d < peor / peor_d:
            peor, peor_nm, peor_d = dist, nm, d
        if dist < BORDE_MIN_D * d:
            f.append(f"costilla_2d: el {rosca} de '{nm}' cae a {dist:.2f} mm "
                     f"del canto mas cercano y se exige {BORDE_MIN_D * d:.2f} "
                     f"({BORDE_MIN_D} x D). Quedan {dist - d / 2:.2f} mm de "
                     f"aluminio: el canto que muerde es el de la VENTANA, no "
                     f"el de fuera, asi que lo que hay que subir es "
                     f"ala_costilla (hoy {p['ala_costilla']:.0f})")

    if len(redondos) != len(esperados):
        f.append(f"costilla_2d: el DXF trae {len(redondos)} agujeros redondos y "
                 f"el modelo pone {len(esperados)}. Uno de mas tampoco vale: "
                 f"la banda solo mide {p['ala_costilla']:.0f} mm de ancho")

    # 2. EL CENSO DEL COSTADO YA NO ES ASUNTO DE ESTA PUERTA.
    #
    #    Aqui vivia un "y el costado NO LLEVA NINGUNO" que exigia cero redondos
    #    en el acrilico. Duro un dia. Al pasar el marco POR FUERA el 2026-08-27,
    #    el costado recupera CUATRO agujeros -- el paso de los casquillos -- y
    #    esta puerta y taladros_costado() pasaron a pedir cosas incompatibles:
    #    una exigia cero y la otra exactamente cuatro.
    #
    #    Lo canto el delegado al implementar la tarea, no el escaneo previo del
    #    plan: el escaneo cruzaba tareas contra tareas y esto era puerta contra
    #    puerta. Vale la pena tenerlo escrito.
    #
    #    El censo del costado lo lleva ahora taladros_costado(), que ademas mira
    #    el DIAMETRO -- que es lo que de verdad decide si el tornillo muerde el
    #    PMMA o no. Aqui solo queda la costilla.

    if not f:
        print(f"  costilla_2d: los {len(esperados)} taladros (4 M4 de riel + "
              f"{len(ct)} M5 de transversal + 1 M3 de pestana) tienen material "
              f"alrededor (el mas "
              f"justo, '{peor_nm}', a {peor:.2f} mm del canto = "
              f"{peor / peor_d:.2f} D), y el costado ya no lleva ninguno")
    return f


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
    filas_x = [p["vuelo_zocalo"] + p["t_cheek"] + p["t_costilla"] / 2,
               (p["vuelo_zocalo"] + p["ancho_total"] - p["t_cheek"]
                - p["t_costilla"] / 2)]
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
    n = max(1, round((fondo_tabla := cb._fondo_bandeja(p)) / 100))
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
    return f


# Holgura del agujero del acrilico ALREDEDOR del casquillo, por lado. NO es
# holgura de montaje: es lo que garantiza que el apriete va costilla ->
# casquillo -> riel y nunca toca el PMMA. Con 0 el casquillo hace de escariador
# y vuelve el modo de fallo que la spec 3.2 evita: el acrilico pinzado entre dos
# caras de aluminio, fluyendo bajo la precarga que sujeta el riel.
HOL_CASQUILLO = 0.5


def taladros_costado() -> list[str]:
    """Los cuatro agujeros del costado son DE PASO y no de apriete.

    ESTA PUERTA MURIO Y VUELVE EL MISMO DIA, con otro criterio. Se llamaba
    taladros_con_material() y medía que cada taladro del costado tuviera
    acrilico alrededor para poder APRETAR contra el; el 2026-08-27, cuando el
    costado quedo sin un solo tornillo, se quedo sin sujeto y se borro.

    Vuelve porque la inversion le devuelve cuatro agujeros, y lo que hay que
    verificar ahora es lo contrario de antes: que el agujero sea lo bastante
    GRANDE. El tornillo no muerde el acrilico -- lo cruza dentro de un casquillo
    de aluminio que se come el apriete --, asi que un agujero a medida del
    tornillo no es mas seguro: es el fallo.

    Son exactamente cuatro, uno por Z-Rail. Cualquier otro redondo en esta pieza
    sobra: el costado es PIEL."""
    import clearance_budget as cb

    p = cb.leer_params()
    P = cb._vertices(p)
    cr = cb._centros_rail(p, P)
    d_esperado = p["d_M4_paso"] + 2 * HOL_CASQUILLO + p["kerf"]
    leidos = _redondos("costado_2d")
    f: list[str] = []
    if len(leidos) != len(cr):
        return [f"costado_2d: {len(leidos)} agujeros redondos y el modelo pone "
                f"{len(cr)}, uno por Z-Rail. El costado es PIEL: no lleva mas, "
                f"y desde la inversion (spec 3.2) tampoco menos -- por ahi pasa "
                f"el casquillo"]
    contorno = _contorno_costado()
    if not contorno:
        return ["costado_2d: sin LINEs, no se puede verificar el contorno"]
    peor, peor_nm = float("inf"), ""
    for nm, c in zip(cb.NOMBRES_CR, cr):
        cerca = [q for q in leidos
                 if math.hypot(q[0] - c[0], q[1] - c[1]) <= DESVIO_DXF_MAX]
        if not cerca:
            f.append(f"costado_2d: falta el paso de casquillo de '{nm}' en "
                     f"({c[0]:.2f}, {c[1]:.2f})")
            continue
        if abs(cerca[0][2] - d_esperado) > 0.1:
            f.append(f"costado_2d: el agujero de '{nm}' mide {cerca[0][2]:.2f} "
                     f"y se exige {d_esperado:.2f} (paso M4 + 2 x "
                     f"{HOL_CASQUILLO} de holgura de casquillo). A medida del "
                     f"tornillo, el apriete muerde el PMMA y la precarga del "
                     f"riel se relaja sola en semanas")
        dist = _dist_al_contorno(contorno, c)
        if dist < peor:
            peor, peor_nm = dist, nm
        if dist < BORDE_MIN_D * d_esperado:
            f.append(f"costado_2d: el agujero de '{nm}' cae a {dist:.2f} mm del "
                     f"canto y se exige {BORDE_MIN_D * d_esperado:.2f} "
                     f"({BORDE_MIN_D} x D). Quedan {dist - d_esperado / 2:.2f} "
                     f"mm de acrilico: eso se raja")
    if not f:
        print(f"  costado_2d: los 4 pasos de casquillo miden {d_esperado:.2f} "
              f"(M4 + 2 x {HOL_CASQUILLO}) y tienen acrilico alrededor (el mas "
              f"justo, '{peor_nm}', a {peor:.2f} mm del canto)")
    return f


def main() -> int:
    fallos: list[str] = []
    for nombre, sobre in SOBRES.items():
        ruta = PLANS / f"{nombre}.dxf"
        if not ruta.exists():
            fallos.append(f"{nombre}: FALTA el DXF")
            continue
        fallos += revisar(nombre, sobre)
    fallos += railes_dentro_del_costado()
    fallos += taladros_costilla()
    fallos += taladros_costado()
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


