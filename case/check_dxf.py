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
# cada caja, las dos mayores son las del DXF y la menor es t_acrilico.
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
# legitima -- 1.7 mm en el canto de abajo con bombeo = 0.5. No afloja lo que
# importa: 4 mm sobre una pieza de 345 es un 1.2 %, y un error de escala del
# 5 % (17 mm) o el factor 25.4 siguen cayendo de largo.
TOL = 4.0

# Piezas que el modelo YA coloca pero que todavia no tienen fichero de corte, con
# el motivo. No es una lista de excepciones para tapar pendientes: cada entrada
# se imprime en cada corrida, asi que el hueco se ve. La alternativa era emitir
# un DXF de contorno sin taladros, y eso es peor -- un fichero que parece
# completo y se manda a cortar (constitucion, Principio V).
SIN_DXF = {
    "remate_sup": "pestana superior: es el canto de ataque de la TAPA y queda "
                  "2.75 mm por delante del riel de arriba; a 8 mm de ancho no "
                  "cabe una fila de M4, asi que la fijacion (escuadra al riel, "
                  "costadillo de tapa o pegado) esta sin decidir y sus taladros "
                  "no existen",
}


def _sobres() -> dict[str, tuple[float, float, float, float]]:
    import clearance_budget as cb

    p = cb.leer_params()
    g = cb.perfil(p)
    _, planchas, _ = cb._cajas_solidas(p)

    dims: dict[str, tuple[float, float]] = {
        # el costado no es una plancha del cuerpo: es la mejilla, y su DXF es
        # la silueta lateral entera.
        "costado_2d": (cb.fondo(p), g["alto_total"]),
        # cupon: 2*margen + (n-1)*paso de la escalera, x 62 de alto. No sale
        # de _cajas_solidas porque no es una pieza del case.
        "coupon": (136.0, 62.0),
    }
    for caja in planchas:
        nombre, x0, x1, y0, y1, z0, z1 = caja
        if nombre in SIN_DXF:
            continue
        aristas = sorted((x1 - x0, y1 - y0, z1 - z0), reverse=True)
        dims[f"{nombre}_2d"] = (aristas[0], aristas[1])   # se cae el espesor

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


def _contorno_costado() -> list:
    """Aristas del contorno EXTERIOR de costado_2d, releidas del DXF.

    Se valida contra el ARCHIVO, no contra una copia de redondear() en Python:
    replicarla aqui seria la tercera copia de la misma matematica, y la version
    que cuenta es la que salio al fichero que va al laser. Los agujeros salen
    como componentes aparte; el contorno es la de bbox mas grande."""
    doc = ezdxf.readfile(PLANS / "costado_2d.dxf")
    aristas = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))
               for e in doc.modelspace() if e.dxftype() == "LINE"]
    if not aristas:
        return []
    vecinos: dict[tuple, list[int]] = {}
    for i, (a, b) in enumerate(aristas):
        for pt in (a, b):
            vecinos.setdefault((round(pt[0], 3), round(pt[1], 3)), []).append(i)
    visto: set[int] = set()
    componentes: list[list[int]] = []
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
        componentes.append(comp)

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


def taladros_con_material() -> list[str]:
    """Cada taladro del costado necesita acrilico alrededor.

    Esto no lo miraba nadie, igual que no se miraba si los largueros CABEN
    (railes_dentro_del_costado). Y son cosas distintas: un larguero puede caber
    de sobra y su M5 caer a dos milimetros de una curva, porque el taladro esta
    en el centro del larguero y las curvas del contorno se mueven solas cada vez
    que cambia un radio o un angulo. Un M5 asi no falla al montarlo -- falla al
    apretarlo, y raja el costado."""
    import clearance_budget as cb

    contorno = _contorno_costado()
    if not contorno:
        return ["costado_2d: sin LINEs, no se puede verificar el contorno"]
    p = cb.leer_params()
    P = cb._vertices(p)
    cr = cb._centros_rail(p, P)
    ce = cb._centros_esqueleto(p, P, cr)
    d = p["d_M5_paso"]
    minimo = BORDE_MIN_D * d
    f: list[str] = []
    peor, peor_nm = float("inf"), ""
    for nm, c in zip(cb.NOMBRES_CR + cb.NOMBRES_CE, list(cr) + list(ce)):
        dist = _dist_al_contorno(contorno, c)
        if dist < peor:
            peor, peor_nm = dist, nm
        if dist < minimo:
            f.append(f"costado_2d: el M5 de '{nm}' cae a {dist:.2f} mm del canto "
                     f"(se exige {minimo:.2f} = {BORDE_MIN_D} x D). Quedan "
                     f"{dist - d/2:.2f} mm de acrilico entre el agujero y el "
                     f"borde: eso se raja al apretar")
    if not f:
        print(f"  costado_2d: los {len(cr) + len(ce)} taladros M5 tienen material "
              f"alrededor (el mas justo, '{peor_nm}', a {peor:.2f} mm del canto "
              f"= {peor / d:.2f} D)")
    return f


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
    ce = cb._centros_esqueleto(p, P, cr)
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
                for n, c in zip(cb.NOMBRES_CE, ce)]
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


def main() -> int:
    fallos: list[str] = []
    for nombre, sobre in SOBRES.items():
        ruta = PLANS / f"{nombre}.dxf"
        if not ruta.exists():
            fallos.append(f"{nombre}: FALTA el DXF")
            continue
        fallos += revisar(nombre, sobre)
    fallos += railes_dentro_del_costado()
    fallos += taladros_con_material()
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


