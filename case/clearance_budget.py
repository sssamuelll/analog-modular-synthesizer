"""Presupuesto de holguras del case, en mm.

    python case/clearance_budget.py

Hermano de tuning_budget.py y ground_budget.py, pero mecanico: aqui lo que
se agota no son cents sino milimetros. La distincion que organiza esto:

  El modelo OpenSCAD (sam17_case.scad) DIBUJA; este script DECIDE si lo
  dibujado cabe. Los dos leen los mismos numeros (case/cad/params.scad,
  unica fuente de verdad), pero este recalcula la geometria con su propia
  trigonometria — si el .scad y el budget discrepan, uno de los dos miente
  y la autocomprobacion lo delata.

Convencion: angulos de cara medidos DESDE LA VERTICAL (spec §4 rev. 3).
Corre en verde ANTES de mandar nada a cortar (constitucion, Principio III).
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

PARAMS = Path(__file__).parent / "cad" / "params.scad"


def leer_params() -> dict[str, float]:
    texto = PARAMS.read_text(encoding="utf-8")
    pares = re.findall(r"^\s*(\w+)\s*=\s*(-?[0-9.]+)\s*;", texto, re.M)
    if len(pares) < 20:
        raise SystemExit(f"params.scad: solo {len(pares)} parametros parseados")
    return {k: float(v) for k, v in pares}


def fondo(p: dict[str, float]) -> float:
    """Fondo del case. DERIVADO del marco de remate, no parametro: es la
    proyeccion de la hipotenusa mas el marco (ver la nota en params.scad). Va
    asi para que la esquina de arriba NO cambie de forma cuando se mueve un
    angulo o un alto de piso."""
    return (p["alto_cara_inf"] * math.sin(math.radians(p["angulo_inferior"]))
            + p["paso_horizontal"]
            + p["alto_cara_sup"] * math.sin(math.radians(p["angulo_superior"]))
            + p["marco_remate"])


def perfil(p: dict[str, float]) -> dict[str, float]:
    """Vertices del perfil lateral (X = fondo hacia atras, Y = arriba)."""
    si, ci = math.sin(math.radians(p["angulo_inferior"])), math.cos(
        math.radians(p["angulo_inferior"]))
    ss, cs = math.sin(math.radians(p["angulo_superior"])), math.cos(
        math.radians(p["angulo_superior"]))
    y_entrepiso = p["alto_frontal"] + p["alto_cara_inf"] * ci
    x_cara_inf = p["alto_cara_inf"] * si
    x_cara_sup0 = x_cara_inf + p["paso_horizontal"]
    x_cara_sup1 = x_cara_sup0 + p["alto_cara_sup"] * ss
    alto_total = y_entrepiso + p["alto_cara_sup"] * cs
    return {
        "y_entrepiso": y_entrepiso,
        "alto_total": alto_total,
        "prof_sup_min": x_cara_sup1,
        # del tope del suelo al fondo de la bandeja de entrepiso. Antes se
        # medIa desde y = 0 y sobrestimaba en los 25 mm del sandwich viejo de
        # la base; hoy el suelo son t_base.
        "alto_interior_inferior": (y_entrepiso - p["t_acrilico"]
                                    - p["t_base"]),
        "ancho_util": p["ancho_total"] - 2 * p["t_cheek"],
    }


def autocomprobacion(p: dict[str, float]) -> None:
    """Caso hecho a mano (spec §4 rev. 3): 12/35 grados, panel 190, vertice
    frontal a 50. Son numeros FIJOS a proposito -- no los de params -- para
    que la trigonometria se compruebe contra una cuenta hecha a lapiz que no
    se mueve cuando el diseno cambia."""
    g = perfil({**p, "angulo_inferior": 12, "angulo_superior": 35,
                "alto_cara_inf": 190, "alto_cara_sup": 190,
                "alto_frontal": 50, "paso_horizontal": 20,
                "t_acrilico": 5, "ancho_total": 500, "t_cheek": 8})
    # A mano: 50 + 190*cos12 = 50 + 185.85 = 235.85
    assert abs(g["y_entrepiso"] - 235.85) < 0.05, g["y_entrepiso"]
    # A mano: 235.85 + 190*cos35 = 235.85 + 155.64 = 391.49
    assert abs(g["alto_total"] - 391.49) < 0.05, g["alto_total"]
    # A mano: 190*sin12 + 20 + 190*sin35 = 39.51 + 20 + 108.99 = 168.50
    assert abs(g["prof_sup_min"] - 168.50) < 0.05, g["prof_sup_min"]


def _vertices(p: dict[str, float]) -> list[tuple[float, float]]:
    """P0..P8 del perfil lateral, misma formula y numeracion que
    pts_perfil() en sam17_case.scad."""
    si, ci = math.sin(math.radians(p["angulo_inferior"])), math.cos(
        math.radians(p["angulo_inferior"]))
    ss, cs = math.sin(math.radians(p["angulo_superior"])), math.cos(
        math.radians(p["angulo_superior"]))
    ye = p["alto_frontal"] + p["alto_cara_inf"] * ci
    x2 = p["alto_cara_inf"] * si
    x3 = x2 + p["paso_horizontal"]
    x4 = x3 + p["alto_cara_sup"] * ss
    yt = ye + p["alto_cara_sup"] * cs
    pf = fondo(p)
    return [(0, 0), (0, p["alto_frontal"]), (x2, ye), (x3, ye), (x4, yt),
            # 7 puntos: canto trasero UNICO a plomo de toda la altura. Antes
            # eran 9, con una repisa escalonada entre prof_superior=250 y
            # prof_inferior=350 -- la que rompia la lectura de triangulo. El
            # ANTIGUO P[8] es ahora P[6].
            (pf, yt), (pf, 0)]


def _centros_rail(p: dict[str, float],
                   P: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """4 centros de rail de panel [inf frente, inf valle, sup valle,
    sup remate], misma formula que centros_rail() en sam17_case.scad.

    ESTUVIERON EN TRES hasta el 2026-08-17: la bisagra ocupaba la linea de
    tornillo de arriba y ahi no habia riel, o sea que los modulos de la fila de
    arriba no tenian donde atornillar por su canto superior. Un nudillo no es un
    riel. La bisagra se mudo a la arista del techo.

    OJO al leerlo contra costado_2d(): el costado solo perfora los DOS primeros.
    Los de la cara de arriba son TAPA y giran con ella."""
    # cada punta lleva SU inset, gobernado por la curva que la remata (ver la
    # tabla de insets en params.scad)
    caras = [(P[1], P[2], (p["inset_inf_frente"],
                           p["alto_cara_inf"] - p["inset_inf_valle"])),
             (P[3], P[4], (p["inset_sup_valle"],
                           p["alto_cara_sup"] - p["inset_sup_remate"]))]
    # el eje del M4 de punta esta a rail_er_eje del panel, no a rail/2: el riel
    # EUROrack es hondo (27.4) y su taladro cae en su centroide
    off = p["t_panel"] + p["rail_er_eje"]
    out = []
    for c0, c1, esses in caras:
        dx, dy = c1[0] - c0[0], c1[1] - c0[1]
        dl = math.hypot(dx, dy)
        dx, dy = dx / dl, dy / dl
        nx, ny = dy, -dx
        for s in esses:
            out.append((c0[0] + dx * s + nx * off, c0[1] + dy * s + ny * off))
    return out


def _he_er(p: dict[str, float], ang: float) -> tuple[float, float]:
    """Semiextension (x, y) del riel EUROrack ya girado con su cara, misma
    formula que he_er_x/he_er_y en sam17_case.scad.

    NO es un cuadrado y ahi esta la trampa: mide rail_er_alto (10) a lo largo de
    la cara y rail_er_fondo (27.4) hacia dentro, asi que cada eje del mundo
    recibe una mezcla distinta. Con el 2020 los dos ejes daban r*(|cos|+|sin|) y
    una sola cota servia; con la seccion real de StudioRacks no, y usar la vieja
    subestima el alcance vertical en 2 mm justo en la esquina del frente, que es
    donde el riel tiene que librar la bandeja del PSU."""
    a = math.radians(ang)
    ha, hf = p["rail_er_alto"] / 2, p["rail_er_fondo"] / 2
    return (hf * abs(math.cos(a)) + ha * abs(math.sin(a)),
            hf * abs(math.sin(a)) + ha * abs(math.cos(a)))


def _esquinas_er(p: dict[str, float], c: tuple[float, float],
                  ang: float) -> list[tuple[float, float]]:
    """Las 4 esquinas REALES (no la caja) del riel girado, para las cuentas SAT."""
    a = math.radians(ang)
    d = (math.sin(a), math.cos(a))          # a lo largo de la cara
    n = (d[1], -d[0])                        # hacia dentro
    ha, hf = p["rail_er_alto"] / 2, p["rail_er_fondo"] / 2
    return [(c[0] + sa * ha * d[0] + sf * hf * n[0],
             c[1] + sa * ha * d[1] + sf * hf * n[1])
            for sa in (-1, 1) for sf in (-1, 1)]


def _tangente(V: tuple[float, float], A: tuple[float, float],
               B: tuple[float, float], r: float) -> float:
    """Cuanto acrilico se come el redondeo de un vertice a lo largo de cada
    arista. Mismo recorte que _r_util/_arco en sam17_case.scad: el radio pedido
    se limita a lo que da de si la arista mas corta."""
    ax, ay = A[0] - V[0], A[1] - V[1]
    bx, by = B[0] - V[0], B[1] - V[1]
    la, lb = math.hypot(ax, ay), math.hypot(bx, by)
    ang = math.acos(max(-1.0, min(1.0, (ax * bx + ay * by) / (la * lb))))
    g = ang / 2
    re = min(r, min(la, lb) / 2 * math.tan(g) * 0.999)
    return re / math.tan(g)


def _x_valle(p: dict[str, float], P: list[tuple[float, float]],
              cr: list[tuple[float, float]]) -> tuple[float, float]:
    """Extremos de la tapa del valle, misma formula que x_valle() en
    sam17_case.scad: delante donde muere el redondeo del pico, detras
    holgura_rail por delante de la ESQUINA girada del riel del valle de arriba
    (no de su centro -- ese atajo ya costo tres fallos en este case)."""
    return (P[2][0] + _tangente(P[2], P[1], P[3], p["radio_pico"]),
            cr[2][0] - _he_er(p, p["angulo_superior"])[0] - p["holgura_rail"])


def _radio_giro_riel(p: dict[str, float]) -> float:
    """Radio del barrido del riel de arriba al girar sobre su propio M4.

    No hay eje de bisagra que calcular: el eje ES el taladro del riel, o sea
    _centros_rail()[3]. Lo unico que hace falta derivar es cuanto barre el riel
    al girar sobre el, que es la distancia de su centroide a su esquina."""
    return math.hypot(p["rail_er_fondo"], p["rail_er_alto"]) / 2


def _esquinas_pestana(p: dict[str, float],
                       P: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """4 esquinas de la pestana superior en coordenadas del perfil. Va girada
    con la cara, asi que su caja sale de las esquinas y no de un semilado."""
    a2 = math.radians(p["angulo_superior"])
    d2 = (math.sin(a2), math.cos(a2))
    n2 = (d2[1], -d2[0])
    return [(P[3][0] + d2[0] * s + n2[0] * q, P[3][1] + d2[1] * s + n2[1] * q)
            for s in (p["alto_cara_sup"] - p["marco_sup"], p["alto_cara_sup"])
            for q in (0.0, p["prof_sup"])]


def _y_remate(p: dict[str, float], P: list[tuple[float, float]],
              cr: list[tuple[float, float]], r: float) -> float:
    """Y del larguero de remate, misma formula que y_rs en sam17_case.scad:
    el mas bajo de tres techos -- el techo YA REDONDEADO, el plano del panel de
    arriba, y el riel de arriba de la tapa (el que manda)."""
    a2 = math.radians(p["angulo_superior"])
    # he_cs y NO r: lo que se acerca al plano del panel es la ESQUINA del
    # larguero, que en diagonal alcanza 14.14 en vez de 10. Con marco_remate=22
    # este techo nunca mandaba y el error dormia; con el marco en 8 manda, y con
    # la version vieja la esquina asomaba 2.54 mm por delante del panel.
    he_cs = r * (abs(math.cos(a2)) + abs(math.sin(a2)))
    por_cara = P[3][1] + (math.cos(a2) * (fondo(p) - r - P[3][0])
                          - (he_cs + p["t_panel"])) / math.sin(a2)
    # el larguero vive pegado al plano trasero (x = fondo - r), o sea que su
    # esquina de atras cae donde el arco de la esquina trasera de arriba ya bajo
    # su tangente (marco_remate/2). P[5].y - r a secas lo dejaba FUERA.
    por_techo = P[5][1] - r - p["marco_remate"] / 2
    # Este techo lo puso primero un rail de panel, luego el nudillo de la
    # bisagra cuando la bisagra ocupo esa linea, y desde el 2026-08-17 vuelve a
    # ser un riel: el de arriba de la tapa. Y NO basta su esquina de abajo --
    # ese riel GIRA sobre su propio M4, asi que lo que hay que librar es su
    # BARRIDO. he_er_y(45) da 13.22 y el radio de giro 14.58: 1.36 mm que solo
    # se notan abriendo la tapa, que es el peor momento para enterarse.
    por_riel = (cr[3][1] - _radio_giro_riel(p) - p["holgura_rail"] - r)
    return min(por_techo, por_cara, por_riel)


def _centros_esqueleto(p: dict[str, float], P: list[tuple[float, float]],
                        cr: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """7 centros de larguero de esqueleto, misma formula que
    centros_esqueleto() en sam17_case.scad. Fueron 7 (con un "zocalo superior"
    que se retiro), luego 6, y desde el 2026-08-17 son 7 otra vez: entro el del
    valle, que es el unico que existe por una plancha y no por una union."""
    r = p["rail"] / 2
    # Semiextension en X de un rail de PANEL tras su rotacion: el cuadrado
    # girado sobresale r*(|cos|+|sin|) de su centro, NO r. Los dos largueros
    # que se plantan detras de un rail girado se separan de esa esquina, no
    # del centro.
    #
    # x_ed estuvo escrito como `cr[2].x + rail + holgura_rail`, que deja el
    # canto delantero SIEMPRE en +14.00 del centro del rail girado, sin mirar
    # el angulo. La esquina real es r*(cos+sin) y vale 13.93 a 35 grados,
    # 14.14 a 45 y 14.11 a 49: o sea que la holgura de diseno (4 mm) NO
    # EXISTIO NUNCA en ningun angulo -- a 35 grados quedaban 0.07 mm, que
    # entre dos perfiles de aluminio es contacto y esta por debajo de la
    # tolerancia de la propia extrusion. La formula es negativa en toda la
    # ventana 36-54 grados, y vuelve a rozar el cero a 55. Al relajar la cara
    # superior a 49 el solape se hizo real (0.11 mm contra el larguero, 5 mm
    # contra la bandeja de entrepiso) y solapes() lo canto. El cambio de
    # angulo no rompio nada: destapo algo que llevaba roto desde Task 5.
    x_ed = cr[2][0] + _he_er(p, p["angulo_superior"])[0] + p["holgura_rail"] + r
    y_ep = P[3][1] - p["t_acrilico"] - r
    # Los dos largueros de la base ya NO viven en el canto de abajo. Desde que
    # la bandeja es el suelo (t_base) montan ENCIMA de ella, con su centro en
    # t_base + r, y a esa altura el redondeo de las esquinas de abajo deja de
    # afectarles: ahi ya hay acrilico de sobra. Al delantero lo coloca ahora el
    # riel de panel que le pasa por delante -- misma cuenta que x_ed, o sea
    # contra la ESQUINA del riel girado y no contra su centro. Estuvo en
    # alto_frontal/2 + r + 2, pegado al vertice, y ahi el riel se le montaba
    # encima en cuanto el vertice bajo.
    x_bd = cr[0][0] + _he_er(p, p["angulo_inferior"])[0] + p["holgura_rail"] + r
    y_bd = p["t_base"] + r
    return [(x_bd, y_bd),
            (fondo(p) - r - p["radio_perfil"], y_bd),
            (x_ed, y_ep), (fondo(p) - r, y_ep),
            # Remate superior: su Y se DERIVA de la cara que lo limita, no es
            # P[5].y - r. Al acortar el marco de arriba para que la esquina se
            # lea como punta, el rincon se cierra y un cuadrado de 20 pegado
            # al vertice asomaria por la cara superior. Centro a r + t_panel
            # de distancia perpendicular al plano del panel de arriba.
            (fondo(p) - r, _y_remate(p, P, cr, r)),
            (fondo(p) - r, P[3][1] + 15),
            # valle: el septimo, y el unico que existe por una plancha y no por
            # una union. Centrado bajo la tapa del valle para que los dos vuelos
            # sean iguales, y de paso ata los costados por la cintura.
            (sum(_x_valle(p, P, cr)) / 2, y_ep)]


# Que inset gobierna cada punta de cada cara. El orden es el mismo que usa
# _centros_rail(): primero el de arranque, luego el de remate.
CARAS = {"inf": ("inset_inf_frente", "inset_inf_valle"),
         "sup": ("inset_sup_valle", "inset_sup_remate")}

# 4 railes de panel: dos por cara, como cualquier fila EUROrack. Los dos de la
# cara superior son TAPA -- no llevan M4 al costado, que si lo llevaran la tapa
# no abriria.
NOMBRES_CR = ["cara_inf frente", "cara_inf valle",
              "cara_sup valle", "cara_sup remate"]
ANGS_CR = ["angulo_inferior", "angulo_inferior",
           "angulo_superior", "angulo_superior"]
NOMBRES_CE = ["base delantera", "base trasera", "entrepiso delantero",
              "entrepiso trasero", "remate superior", "repisa", "valle"]


# Caja = (nombre, x0, x1, y0, y1, z0, z1)
Caja = tuple
# Fila de agujeros de una placa = (placa, fila, eje, coordenada en ese eje,
# rail frontera al que DEBE anclar). El eje es el que recorre la placa de un
# rail frontera al otro: X en las bandejas (horizontales), Y en las pieles
# (verticales). El rail va declarado, no se busca el mas cercano:
# una fila que cae por casualidad en la centerline de otro rail no esta
# anclada donde el diseno dice, y ese acierto casual no debe pasar la puerta.
Fila = tuple


def _cajas_solidas(p: dict[str, float]) -> tuple[list[Caja], list[Caja],
                                                  list[Fila]]:
    """AABB de los railes (3 de panel + 6 de esqueleto), de la bisagra y de las
    planchas/pieles, misma formula que rails()/planchas_acrilico() en
    sam17_case.scad, mas las filas de agujeros de las placas (las mismas
    expresiones que dimensionan la caja, para que un cambio de placa arrastre
    su fila y no se puedan separar)."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ce = _centros_esqueleto(p, P, cr)
    rail, t_cheek = p["rail"], p["t_cheek"]
    t_acr, gap = p["t_acrilico"], p["gap_sombra"]
    ancho_total = p["ancho_total"]

    angs = [p[k] for k in ANGS_CR]
    railes: list[Caja] = []
    for nm, c, ang in zip(NOMBRES_CR, cr, angs):
        # el riel gira -ang para calzar a ras de la cara, y su AABB no es
        # simetrico porque la seccion no es cuadrada (ver _he_er)
        hx, hy = _he_er(p, ang)
        railes.append((nm, c[0] - hx, c[0] + hx, c[1] - hy, c[1] + hy,
                       t_cheek, ancho_total - t_cheek))
    # La PESTANA superior: banda de acrilico sobre los ultimos marco_sup mm de
    # la cara de arriba, a ras por fuera y engordando t_cheek hacia dentro.
    # Aqui interesa que no se pise con el riel de arriba ni con el larguero de
    # remate, que viven justo debajo.
    esq = _esquinas_pestana(p, P)
    planchas_extra = ("remate_sup",
                      min(e[0] for e in esq), max(e[0] for e in esq),
                      min(e[1] for e in esq), max(e[1] for e in esq),
                      t_cheek, ancho_total - t_cheek)
    for nm, c in zip(NOMBRES_CE, ce):
        railes.append((nm, c[0] - rail / 2, c[0] + rail / 2,
                       c[1] - rail / 2, c[1] + rail / 2,
                       t_cheek, ancho_total - t_cheek))

    planchas: list[Caja] = [planchas_extra]
    filas: list[Fila] = []
    # bandeja_base: es el SUELO del case desde el 2026-08-17, de y = 0 a
    # y = t_base, con los dos largueros montados encima en vez de debajo. Sus dos
    # cantos van a ras de sus largueros, y el delantero es el que importa: se
    # RETIRA por detras del riel de panel del frente para que ese riel pueda
    # bajar hasta la esquina. Ahi se ganan 8 mm de altura del aparato y se pagan
    # 32 mm de suelo abierto por delante (ver guarda_piso y alto_frontal).
    x0_bb = ce[0][0] - rail / 2
    fondo_bb = ce[1][0] + rail / 2 - x0_bb
    planchas.append(("bandeja_base", x0_bb, x0_bb + fondo_bb,
                     0.0, p["t_base"], t_cheek, ancho_total - t_cheek))
    filas += [("bandeja_base", "delantera", "x", ce[0][0], "base delantera"),
              ("bandeja_base", "trasera", "x", ce[1][0], "base trasera")]
    # bandeja_entrepiso: R2 — canto trasero a ras de entrepiso-trasero,
    # tope (no fondo) a ras de P3.y
    x0_be = ce[2][0] - rail / 2
    fondo_be = fondo(p) - ce[2][0] + rail / 2
    planchas.append(("bandeja_entrepiso", x0_be, x0_be + fondo_be,
                     P[3][1] - t_acr, P[3][1], t_cheek, ancho_total - t_cheek))
    filas += [("bandeja_entrepiso", "delantera", "x", x0_be + rail / 2,
               "entrepiso delantero"),
              ("bandeja_entrepiso", "trasera", "x", x0_be + fondo_be - rail / 2,
               "entrepiso trasero")]
    # tapa_valle: a ras del plano del valle, igual que la de entrepiso, y con
    # una sola fila de M3 -- la del larguero del valle, que va centrado bajo
    # ella. Lo que la coloca en Y es lo mismo que obligo a subir
    # inset_inf_valle: su cara de abajo tiene que librar la esquina de arriba
    # del riel del valle de la cara inferior.
    x0_tv, x1_tv = _x_valle(p, P, cr)
    planchas.append(("tapa_valle", x0_tv, x1_tv,
                     P[3][1] - t_acr, P[3][1], t_cheek, ancho_total - t_cheek))
    filas += [("tapa_valle", "unica", "x", ce[6][0], "valle")]
    # piel_inferior: R1 — volada hacia +X mas alla de prof_inferior
    alto_pi = ce[3][1] - ce[1][1] + 30
    y0_pi = ce[1][1] - 15
    planchas.append(("piel_inferior", P[6][0] + gap, P[6][0] + gap + t_acr,
                     y0_pi, y0_pi + alto_pi, t_cheek + gap, ancho_total - t_cheek - gap))
    filas += [("piel_inferior", "inferior", "y", y0_pi + 15, "base trasera"),
              ("piel_inferior", "superior", "y", y0_pi + alto_pi - 15,
               "entrepiso trasero")]
    # piel_superior: R1 — volada hacia +X mas alla de prof_superior;
    # re-anclada a la repisa (ce[5]) en vez de entrepiso trasero (R6)
    alto_ps = ce[4][1] - ce[5][1] + 30
    y0_ps = ce[5][1] - 15
    planchas.append(("piel_superior", P[6][0] + gap, P[6][0] + gap + t_acr,
                     y0_ps, y0_ps + alto_ps, t_cheek + gap, ancho_total - t_cheek - gap))
    filas += [("piel_superior", "inferior", "y", y0_ps + 15, "repisa"),
              ("piel_superior", "superior", "y", y0_ps + alto_ps - 15,
               "remate superior")]
    return railes, planchas, filas


def _overlap(a: Caja, b: Caja) -> tuple[float, float, float] | None:
    ax0, ax1, ay0, ay1, az0, az1 = a[1:]
    bx0, bx1, by0, by1, bz0, bz1 = b[1:]
    ox = min(ax1, bx1) - max(ax0, bx0)
    oy = min(ay1, by1) - max(ay0, by0)
    oz = min(az1, bz1) - max(az0, bz0)
    return (ox, oy, oz) if (ox > 1e-9 and oy > 1e-9 and oz > 1e-9) else None


# Pares tolerados: ronda de revision 1 dejo 2 aqui (bandeja_entrepiso vs
# piel_superior, y el par de railes tilted del quiebre P2-P3). Ronda 2 los
# resuelve los dos de verdad (R6 reancla piel_superior a la repisa en vez
# de entrepiso trasero; R7 abre paso_horizontal 20->25 y separa los railes
# — ver guarda_escalon() mas abajo, que hace el chequeo SAT exacto de ESE
# par como assert duro, no como tolerancia). Vacio a proposito: si un solape
# nuevo aparece y de verdad no se puede resolver sin tocar centros_rail()
# fuera de las reglas autorizadas, se documenta aqui igual que antes.
TOLERADOS: dict[frozenset[str], float] = {
    # riel de arriba de la tapa <-> pestana: solape de CAJA, cero de solape real.
    # Los dos van girados 45 con la cara y sobre ELLA se TOCAN a tope, sin
    # penetrarse: la pestana apoya en la cara de arriba del riel, que es de donde
    # cuelga su fijacion. Dos rectangulos girados que comparten una arista tienen
    # cajas que se pisan de largo -- de ahi la tolerancia gorda. guarda_tapa()
    # hace la cuenta exacta sobre la cara y exige que la junta valga CERO.
    # El solape de caja vale 10.18 mm con la seccion de hoy (marco_sup 8 x
    # prof_sup 16 girados 45); 12 deja aire para el ruido y sigue siendo un
    # numero, no un cheque en blanco.
    frozenset({"cara_sup remate", "remate_sup"}): 12.0,
}


# Tolerancia de alineacion placa<->rail. La coincidencia es una IDENTIDAD
# (la fila sale de la centerline del rail), asi que lo correcto es 0.00 y
# esto solo absorbe ruido de coma flotante. Referencia fisica: la holgura
# del agujero de paso M4 sobre el tornillo es 0.5 mm de diametro, o sea
# 0.25 mm de radio — un desvio de 0.05 ya es 1/5 de eso, y cualquier error
# de diseno real (milimetros, como el +18/-24 de la bandeja base) cae en
# rojo con muchisimo margen.
TOL_ALINEACION = 0.05


def _desvio(coord: float, eje: str, centro: tuple[float, float]) -> float:
    """Desvio FIRMADO de una fila respecto a una centerline de rail, sobre
    el eje que recorre la placa."""
    return coord - centro[0 if eje == "x" else 1]


def _mas_cercano(coord: float, eje: str,
                  candidatos: list[tuple[str, tuple[float, float]]]
                  ) -> tuple[float, str]:
    """Rail mas cercano de la lista (solo para el mensaje de diagnostico:
    el criterio es el rail DECLARADO, no este)."""
    return min(((_desvio(coord, eje, c), nm) for nm, c in candidatos),
               key=lambda t: abs(t[0]))


def alineacion(p: dict[str, float]) -> list[str]:
    """ANCLAJE: cada fila de agujeros de cada placa cae en la centerline de
    un rail del ESQUELETO (sin rotar).

    Por que existe: solapes() verifica DISYUNCION, y una placa flotando en
    el aire es perfectamente disjunta — nadie verificaba que las placas
    apoyaran en algo. Dos formas de fallar, las dos en rojo:

      (a) la fila no coincide con ningun rail: la placa se atornilla al
          aire. Es el defecto de bandeja_base de la ronda final (filas a
          +18.00 y -24.00 mm de sus railes, canto trasero flotando 4 mm
          sobre una bandeja que carga el transformador del PSU).
      (b) la fila coincide con un rail de PANEL: R3 los gira al angulo de
          su cara (12/35 grados), asi que el tornillo entraria en diagonal
          respecto al eje del agujero (~1.05 mm de descentre en 5 mm de
          acrilico contra 0.7-0.9 de holgura) y la arandela asentaria de
          canto — carga de borde sobre acrilico fragil. Las placas anclan
          UNICAMENTE a railes de esqueleto; los de panel estan rotados
          porque sirven a los paneles, no son superficie de anclaje.
    """
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ce = _centros_esqueleto(p, P, cr)
    esqueleto = dict(zip(NOMBRES_CE, ce))
    panel = dict(zip(NOMBRES_CR, cr))
    _, _, filas = _cajas_solidas(p)
    fallos: list[str] = []
    peor = 0.0
    for placa, fila, eje, coord, rail_decl in filas:
        if rail_decl in panel:
            d = _desvio(coord, eje, panel[rail_decl])
            fallos.append(
                f"anclaje [{placa}] fila {fila} ({eje}={coord:.2f}): declara "
                f"anclar al rail de PANEL '{rail_decl}' (desvio {d:+.2f} mm), y "
                f"esos van ROTADOS al angulo de su cara — las placas anclan "
                f"solo a railes de esqueleto")
            continue
        assert rail_decl in esqueleto, (
            f"fila [{placa}/{fila}] declara el rail '{rail_decl}', que no "
            f"existe ni en el esqueleto ni en los railes de panel")
        d = _desvio(coord, eje, esqueleto[rail_decl])
        peor = max(peor, abs(d))
        if abs(d) > TOL_ALINEACION:
            d_cerca, nm_cerca = _mas_cercano(coord, eje, list(esqueleto.items()))
            fallos.append(
                f"anclaje [{placa}] fila {fila} ({eje}={coord:.2f}): {d:+.2f} mm "
                f"de la centerline de '{rail_decl}' (tolerancia "
                f"{TOL_ALINEACION:.2f} mm) — la placa no apoya donde dice; el "
                f"rail mas cercano es '{nm_cerca}' a {d_cerca:+.2f} mm")
    print(f"alineacion: {len(filas)} filas de agujeros revisadas, desvio "
          f"maximo {peor:.2f} mm (tolerancia {TOL_ALINEACION:.2f})")
    return fallos


def canario_alineacion(p: dict[str, float]) -> None:
    """Autocomprobacion ROJA de alineacion(): si esto no dispara, el checker
    esta ciego y su VERDE no vale nada.

    Antes reconstruia las filas historicas de la bandeja_base PRE-FIX y exigia
    los desvios exactos de entonces (+18.00 y -24.00, que salian de la formula
    vieja de 'base delantera', rail/2 + 2). Se rompio en cuanto ese larguero se
    movio por una razon legitima -- retirarlo del trozo de acrilico que vacia el
    redondeo en punta --, y dio un fallo sobre geometria CORRECTA. Es el mismo
    vicio que tenian los sobres de check_dxf: el criterio clavado a un numero de
    otra epoca, que caduca y grita en falso.

    Ahora se desplaza a proposito una fila desde la centerline REAL y se exige
    que el checker devuelva ese desplazamiento. Es la propiedad que de verdad
    importa (¿mide bien el desvio y lo rechaza cuando pasa de la tolerancia?) y
    no depende de la historia. Se prueban los dos lados del umbral: desvios
    gordos como los del bloqueante real, uno finito justo por encima de la
    tolerancia, y la fila bien puesta, que tiene que PASAR."""
    P = _vertices(p)
    ce = _centros_esqueleto(p, P, _centros_rail(p, P))
    esqueleto = dict(zip(NOMBRES_CE, ce))
    casos = (("base delantera", "x"), ("base trasera", "x"),
             ("remate superior", "y"), ("repisa", "y"))
    for rail_decl, eje in casos:
        centro = esqueleto[rail_decl][0 if eje == "x" else 1]
        # los dos primeros son la magnitud del bloqueante real de la bandeja
        # base; el tercero comprueba que el umbral no este dormido
        for delta in (18.0, -24.0, TOL_ALINEACION * 2):
            d = _desvio(centro + delta, eje, esqueleto[rail_decl])
            assert abs(d - delta) < 0.01, (
                f"canario de alineacion: el desvio esta MAL MEDIDO -- fila a "
                f"{delta:+.2f} mm de '{rail_decl}' sobre el eje {eje} y el "
                f"checker devuelve {d:+.3f}")
            assert abs(d) > TOL_ALINEACION, (
                f"canario de alineacion no disparo: fila a {delta:+.2f} mm de "
                f"'{rail_decl}' y la tolerancia vigente es {TOL_ALINEACION} mm "
                f"— no confiar en el VERDE de alineacion()")
        d0 = _desvio(centro, eje, esqueleto[rail_decl])
        assert abs(d0) <= TOL_ALINEACION, (
            f"canario de alineacion: FALSO POSITIVO -- una fila puesta justo "
            f"en la centerline de '{rail_decl}' sale a {d0:+.3f} mm")


def solapes(p: dict[str, float]) -> list[str]:
    """11 railes + 5 planchas/pieles: ningun par se pisa en 3D, salvo los
    TOLERADOS de arriba (impresos igual, nunca silenciados) — vacio ahora
    mismo. Paneles inclinados (1.6 mm, PCB de aluminio de cada modulo): su
    clase la resuelve la rotacion de railes (R3), no entran en esta caja."""
    railes, planchas, _ = _cajas_solidas(p)
    fallos: list[str] = []
    todas = railes + planchas
    n_rail = len(railes)
    for i in range(len(todas)):
        for j in range(i + 1, len(todas)):
            a, b = todas[i], todas[j]
            ov = _overlap(a, b)
            if not ov:
                continue
            tol = TOLERADOS.get(frozenset({a[0], b[0]}))
            estrecho = min(ov[0], ov[1])
            if tol is not None and estrecho <= tol:
                print(f"AMARILLO (tolerado): {a[0]} <-> {b[0]}  "
                      f"dX={ov[0]:.2f} dY={ov[1]:.2f} dZ={ov[2]:.2f}")
                continue
            grupo = ("railes" if j < n_rail else
                      "railes-planchas" if i < n_rail else "planchas")
            fallos.append(f"solape [{grupo}] {a[0]} <-> {b[0]}: "
                          f"dX={ov[0]:.2f} dY={ov[1]:.2f} dZ={ov[2]:.2f}")
    return fallos


def canario_solapes(p: dict[str, float]) -> None:
    """Autocomprobacion roja: alimenta la posicion VIEJA (pre-fix, Task 5)
    del rail entrepiso-delantero y exige que el checker la marque como
    solape contra el rail de panel de la cara superior. Si esto
    no dispara, el checker esta ciego y no detecta nada de verdad."""
    P = _vertices(p)
    r = p["rail"] / 2
    old_ed = (P[3][0] + r, P[3][1] - r)          # formula pre-fix (Task 5)
    cr = _centros_rail(p, P)
    hx, hy = _he_er(p, p["angulo_superior"])
    c = cr[2]
    vecino = ("cara_sup valle", c[0] - hx, c[0] + hx, c[1] - hy, c[1] + hy,
              p["t_cheek"], p["ancho_total"] - p["t_cheek"])
    viejo = ("entrepiso delantero VIEJO",
             old_ed[0] - r, old_ed[0] + r, old_ed[1] - r, old_ed[1] + r,
             p["t_cheek"], p["ancho_total"] - p["t_cheek"])
    ov = _overlap(viejo, vecino)
    assert ov is not None, (
        "canario de solapes no disparo: el checker no detecta un choque "
        "conocido (17.6x12.6 mm) — no confiar en el resto de solapes()")


def _sat_gap(p: dict[str, float], c1: tuple[float, float], ang1: float,
             c2: tuple[float, float], ang2: float) -> float:
    """Holgura EXACTA (SAT, no AABB) entre 2 rieles de panel, cada uno girado
    con su cara. Positivo = hueco en mm; negativo = profundidad de solape.

    El AABB (usado en solapes()) SOBRESTIMA el alcance real de un rectangulo
    girado salvo en la direccion de sus propios ejes — para un umbral duro en mm
    hace falta el valor exacto. La seccion sale de _esquinas_er, o sea que sigue
    al riel real y no a un cuadrado."""

    def esquinas(c: tuple[float, float], ang: float) -> list[tuple[float, float]]:
        return _esquinas_er(p, c, ang)

    def proyeccion(pts: list[tuple[float, float]],
                    eje: tuple[float, float]) -> tuple[float, float]:
        vals = [px * eje[0] + py * eje[1] for px, py in pts]
        return min(vals), max(vals)

    p1, p2 = esquinas(c1, ang1), esquinas(c2, ang2)
    ejes = []
    for ang in (ang1, ang2):
        a = math.radians(ang)
        ejes.append((math.sin(a), math.cos(a)))     # a lo largo de la cara
        ejes.append((math.cos(a), -math.sin(a)))    # hacia dentro
    separaciones = []
    for eje in ejes:
        a0, a1 = proyeccion(p1, eje)
        b0, b1 = proyeccion(p2, eje)
        separaciones.append(min(a1, b1) - max(a0, b0))
    return -min(separaciones)  # min<=0 en algun eje separador -> hueco positivo


# La fresa mas chica de catalogo del taller. Schaeffer: "The smallest tool
# available is a milling cutter with a diameter of 1 mm."
FRESA_MIN_D = 1.0


# Largos de separador M4 que existen en catalogo. No es una lista de gustos: un
# separador se compra, no se mecaniza, y pedir 5.7 mm significa torneado a medida.
LARGOS_STANDOFF = (4, 5, 6, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40)


def guarda_standoff(p: dict[str, float]) -> None:
    """El separador de las pieles tiene que ser una pieza comprable.

    Las dos pieles van voladas: se atornillan a doce separadores M4 y no tocan
    el cuerpo. La distancia a la que quedan NO es un parametro aparte -- es
    gap_sombra, el mismo numero que las separa en el modelo. O sea que
    gap_sombra ES el largo del separador, aunque no lo diga su nombre.

    El issue #52 pedia esto cuando el case todavia tenia zocalo, con sus dos
    standoffs de 33.25 y 7.00 mm y el miedo de que el cuerpo del de arriba
    invadiera un riel girado. El zocalo se elimino y ese miedo se fue con el:
    quedan doce separadores, todos iguales, todos entre piel y cuerpo, sin nada
    girado cerca. Lo que sobrevive del issue es la otra mitad -- que el numero
    sea comprable --, y eso es lo que se comprueba aqui.

    Mismo criterio que marco_sup con el espesor de plancha: hay cotas que no las
    elige el diseno sino el catalogo, y confundirlas cuesta un torneado."""
    assert p["gap_sombra"] in LARGOS_STANDOFF, (
        f"gap_sombra = {p['gap_sombra']} es el largo del separador de las pieles, "
        f"y no esta en catalogo. Los que se compran: {LARGOS_STANDOFF}. Un valor "
        f"fuera de esa lista significa mandar tornear doce piezas.")
    print(f"standoff: 12 separadores M4 de {p['gap_sombra']:.0f} mm "
          f"(= gap_sombra), largo de catalogo")


def guarda_fresado(p: dict[str, float]) -> None:
    """Lo que una fresa puede hacer y un laser no obliga a pensar.

    Fresando, la geometria interior deja de ser libre: la herramienta es un
    cilindro. No entra en un hueco mas estrecho que su diametro, y no deja una
    esquina interior mas cerrada que su radio. Las esquinas EXTERIORES no
    limitan nada -- ahi la fresa pasa por fuera y el radio lo pone el dibujo --,
    asi que esta puerta solo mira huecos y concavos.

    Hoy pasa de sobra, y esa es justo la razon de escribirla: el dia que alguien
    estreche una ranura "para que se vea mas fina" o cierre el valle, el fallo
    no aparece en pantalla ni en el DXF. Aparece en el presupuesto, como un
    cambio de util que se paga, o en un correo del taller diciendo que la pieza
    no es fabricable. Eso es tarde."""
    r = p["fresa_d"] / 2
    # 1. Las ranuras son hull de dos circulos (ver ranura() y onda()): sus
    #    extremos ya son semicirculos de ancho/2, que es la forma que deja la
    #    fresa por si sola. Lo que hay que garantizar es que QUEPA.
    assert p["vent_ancho_ranura"] >= p["fresa_d"] - 1e-9, (
        f"ranura de {p['vent_ancho_ranura']} mm y fresa de {p['fresa_d']}: "
        f"la herramienta no entra. O se ensancha la ranura, o el taller cambia "
        f"a una fresa mas fina y lo cobra.")
    # 2. El valle es la unica esquina CONCAVA del perfil del costado; las otras
    #    (pico, punta, perfil) son convexas y no limitan.
    assert p["radio_valle"] >= r - 1e-9, (
        f"radio_valle={p['radio_valle']} por debajo del radio de la fresa "
        f"({r}): esa esquina interior no se puede fresar tal cual")
    # 3. Taladros: por debajo de la fresa mas chica no hay agujero que valga.
    for k in ("d_M3_paso", "d_M4_paso", "d_M5_paso"):
        assert p[k] >= FRESA_MIN_D - 1e-9, (
            f"{k}={p[k]} por debajo de la fresa mas chica ({FRESA_MIN_D} mm)")
    print(f"fresado: ranura {p['vent_ancho_ranura']:.1f} y concavo minimo "
          f"{p['radio_valle']:.1f} contra fresa de {p['fresa_d']:.1f} "
          f"(radio {r:.1f}) -- sin cambio de util")


def guarda_piso(p: dict[str, float]) -> None:
    """El riel de panel del frente tiene que librar el SUELO del case.

    Es la condicion que fija alto_frontal y con el la altura entera del aparato,
    y hasta hoy vivia solo en un comentario de params.scad. Nadie la vigilaba:
    solapes() trabaja con cajas y solo canta cuando los cuerpos YA se tocan, o
    sea que se come los 4 mm de holgura sin protestar.

    Y lo que hay debajo cambio dos veces el mismo dia. Primero era el lomo de un
    larguero (mal: la bandeja iba encima, 5 mm de barato y 0.51 de solape real).
    Luego el tope de la bandeja. Y desde que Samuel propuso retirar la bandeja
    por detras del riel, ya no hay nada: solo el canto de abajo del case. Cada
    version de esta cota valio milimetros de aparato, asi que son DOS asserts --
    el riel dentro del acrilico, y la bandeja fuera de su camino. Si alguien
    adelanta la bandeja sin subir el riel, cae aqui y no en solapes().

    Se mide sobre el centro REAL del riel (el que sale de _centros_rail), no
    rehaciendo la formula: si el .scad y el budget se separan, esto lo nota."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ce = _centros_esqueleto(p, P, cr)
    hx, hy = _he_er(p, p["angulo_inferior"])
    # 1. el riel dentro del acrilico por abajo, con material
    y_bajo = cr[0][1] - hy
    assert y_bajo >= p["holgura_rail"] - 1e-9, (
        f"el riel de panel del frente se sale del case por abajo: su esquina "
        f"cae en y={y_bajo:.2f} y se exige >={p['holgura_rail']:.2f} de acrilico "
        f"bajo ella. Subir alto_frontal o inset_inf_frente (van emparejados: la "
        f"curva en punta pide inset >= alto_frontal/2 + rail_er_alto/2 + 3)")
    # 2. y la bandeja retirada POR DETRAS de el, que es lo que paga la 1
    x0_bb = ce[0][0] - p["rail"] / 2
    hueco = x0_bb - (cr[0][0] + hx)
    assert hueco >= p["holgura_rail"] - 1e-9, (
        f"la bandeja de base le pasa por debajo al riel del frente: arranca en "
        f"x={x0_bb:.2f} y la esquina trasera del riel esta en "
        f"x={cr[0][0] + hx:.2f} ({hueco:+.2f} mm, se exige "
        f">={p['holgura_rail']:.2f}). O se retira la bandeja o sube el riel, y "
        f"subir el riel cuesta 8 mm de aparato")


# LAS DOS FILAS SE ABREN, cada una girando sobre el M4 de su riel de ARRIBA --
# el mismo tornillo que la fija de punta al costado, que entra a lo largo del
# ancho y por tanto ya es un eje. No hay bisagra en ningun sitio.
#   (nombre, indice del riel-EJE, cuerpos que giran, vertice de arranque de la
#    cara, angulo, inset del panel, alto del panel)
TAPAS = (
    ("fila de abajo", 1, frozenset({"cara_inf frente", "cara_inf valle"}),
     1, "angulo_inferior", "inset_inf_frente", "alto_panel_inf"),
    ("fila de arriba", 3,
     frozenset({"cara_sup valle", "cara_sup remate", "remate_sup"}),
     3, "angulo_superior", "inset_sup_valle", "alto_panel_sup"),
)

# Lo minimo que tiene que abrir una tapa para que sirva de algo. A 60 grados la
# cara queda casi vertical y el interior a la vista; por debajo de 45 no cabe la
# mano para cablear.
APERTURA_MIN = 60.0
# Linea de pegado maxima de la pestana. El metacrilato estructural de dos
# componentes trabaja bien entre 0.1 y 0.3 mm; medio milimetro es el punto donde
# deja de pegar y empieza a rellenar.
JUNTA_PEGADO_MAX = 0.5


def guarda_tapa(p: dict[str, float]) -> None:
    """Las dos caras de panel son TAPAS y las dos tienen que poder abrir.

    Cada una gira sobre el M4 de su riel de arriba. La de abajo pivota en el riel
    del valle y saca su canto delantero hacia arriba; la de arriba pivota en el
    del vertice y saca el valle. No hay bisagra que verificar porque no hay
    bisagra: es el propio tornillo de fijacion.

    Dos comprobaciones, y solapes() no ve ninguna -- mira la posicion CERRADA y
    con cajas alineadas a ejes:

    1. EL BARRIDO. Se gira cada tapa grado a grado y se busca contra que topa. No
       es una cota estimada: es el angulo real, y se imprime en cada corrida.
       Aqui esta la razon de que exista: parada, la fila de abajo libraba la tapa
       del valle por +2.06 mm; GIRANDO la perdia por -0.57, porque el riel barre
       su radio de giro (14.58) y no el alcance de su esquina quieta (11.95). La
       holgura estatica mentia y solo lo dijo el barrido.
       Se comprueban las esquinas de lo que gira contra las cajas de lo que no --
       o sea que caza el caso realista (una esquina entrando en un larguero) y no
       el patologico. Tampoco entra el FONDO de los modulos, que no esta
       modelado: eso lo vigila fondo_pcb_max por otro lado.

    2. LA PESTANA APOYADA EN EL RIEL. De esa cara de aluminio cuelga su unica
       fijacion (M3 por su canto), asi que no se comprueba que esten separadas
       sino que se TOQUEN. En el AABB se pisan porque van giradas 45 -- por eso
       siguen en TOLERADOS --, y esta es la cuenta buena, hecha sobre la cara."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    railes, planchas, _ = _cajas_solidas(p)
    for nombre, i_eje, propios, i_cara, k_ang, k_inset, k_panel in TAPAS:
        eje = cr[i_eje]
        ar = math.radians(p[k_ang])
        d, n = (math.sin(ar), math.cos(ar)), (math.cos(ar), -math.sin(ar))
        A = P[i_cara]
        s0 = p[k_inset] - p["inset_er"]
        giran = [(A[0] + d[0] * s + n[0] * q, A[1] + d[1] * s + n[1] * q)
                 for s in (s0, s0 + p[k_panel]) for q in (0.0, p["t_panel"])]
        for j, nm in enumerate(NOMBRES_CR):
            if nm in propios:
                giran += _esquinas_er(p, cr[j], p[ANGS_CR[j]])
        if "remate_sup" in propios:
            giran += _esquinas_pestana(p, P)
        quietos = [c for c in railes + planchas if c[0] not in propios]
        tope, culpable = 180.0, ""
        for i in range(1, 721):                   # 0.25 grados hasta 180
            th = math.radians(i * 0.25)
            co, si = math.cos(th), math.sin(th)
            for x, y in giran:
                dx, dy = x - eje[0], y - eje[1]
                rx, ry = eje[0] + dx * co + dy * si, eje[1] - dx * si + dy * co
                for c in quietos:
                    if c[1] <= rx <= c[2] and c[3] <= ry <= c[4]:
                        tope, culpable = i * 0.25, c[0]
                        break
                if culpable:
                    break
            if culpable:
                break
        print(f"tapa {nombre}: abre {tope:.1f} grados sobre el M4 de "
              f"'{NOMBRES_CR[i_eje]}'"
              + (f", topa con '{culpable}'" if culpable else " sin topar"))
        assert tope >= APERTURA_MIN, (
            f"la {nombre} solo abre {tope:.1f} grados antes de topar con "
            f"'{culpable}' (se exige >= {APERTURA_MIN:.0f}). Ojo: puede estar "
            f"holgada PARADA y no caber girando -- el riel barre su radio de "
            f"giro ({_radio_giro_riel(p):.2f}), no el alcance de su esquina")

    # LA JUNTA DE LA PESTANA. Esto exigia CERO EXACTO (abs < 0.01) y era correcto
    # mientras la union era atornillada: el tornillo aprieta contra el riel y lo
    # que no toca, no sujeta. Desde que la hoja de Tiptop enseno que esa cara es
    # pared de 1.2 mm, la union es PEGADA -- y una junta pegada quiere lo
    # contrario. El adhesivo estructural necesita linea de pegado; a cero no
    # tiene donde quedarse, y una interferencia negativa impide que la pieza
    # asiente.
    #
    # Asi que la puerta cambia de forma, no de rigor. Lo que de verdad no se
    # puede permitir es el signo negativo -- eso es interferencia. Por arriba, el
    # techo lo pone el adhesivo: pasado medio milimetro el metacrilato de dos
    # componentes rellena un hueco que no deberia existir y la junta pierde
    # resistencia en vez de ganarla.
    #
    # Hoy vale 0.000 y pasa. Si alguien quiere linea de pegado dibujada, sube
    # inset_sup_remate -- pero OJO: eso mueve alto_cara_sup y con el la silueta
    # del costado, o sea el DXF que ya esta presupuestado.
    junta = p["inset_sup_remate"] - p["marco_sup"] - p["rail_er_alto"] / 2
    assert junta >= -1e-9, (
        f"la pestana INTERFIERE con el riel: {junta:+.3f} mm. Negativo significa "
        f"que la pieza no asienta, y ninguna cantidad de adhesivo arregla eso. "
        f"El minimo es inset_sup_remate = marco_sup + rail_er_alto/2 = "
        f"{p['marco_sup'] + p['rail_er_alto']/2:.2f}")
    assert junta <= JUNTA_PEGADO_MAX, (
        f"la pestana se queda a {junta:.3f} mm del riel, y el maximo pegable es "
        f"{JUNTA_PEGADO_MAX}. Mas alla de eso el adhesivo esta rellenando hueco "
        f"en vez de pegar: la junta pierde resistencia segun engorda")


def guarda_escalon(p: dict[str, float]) -> None:
    """R7: paso_horizontal se abrio para separar los 2 railes tilted que
    R3 acerco en el quiebre P2-P3 (cara_inf valle, 12 grados, vs
    cara_sup valle, 35 grados — a paso_horizontal=20 se solapaban 2.52 mm
    exactos por SAT, verificado en la ronda de revision 1). Assert duro,
    no tolerancia: exige >=1.0 mm de hueco REAL (no la caja alineada a
    ejes, que aqui sobrestima)."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    gap = _sat_gap(p, cr[1], p["angulo_inferior"], cr[2], p["angulo_superior"])
    assert gap >= 1.0, (
        f"railes del escalon P2-P3 (cara_inf valle vs cara_sup "
        f"valle) a {gap:.3f} mm de hueco real (SAT) — se exige >=1.0 mm; "
        f"subir paso_horizontal")
    # Y el que de verdad limita cuanto se puede acortar el valle, que no es el
    # anterior: el LARGUERO DEL VALLE va centrado bajo su tapa, y al acortar el
    # valle su centro avanza mas rapido que el borde de su ventana. El SAT tiene
    # 72 mm de margen y este 1.5, asi que sin esto uno acorta mirando la cota
    # equivocada y se come la holgura del larguero sin enterarse.
    r = p["rail"] / 2
    ce = _centros_esqueleto(p, P, cr)
    x_valle = ce[6][0]
    lo = cr[1][0] + _he_er(p, p["angulo_inferior"])[0] + p["holgura_rail"] + r
    hi = cr[2][0] - _he_er(p, p["angulo_superior"])[0] - p["holgura_rail"] - r
    assert lo <= x_valle <= hi, (
        f"el larguero del valle no cabe entre los dos railes del valle: va "
        f"centrado en x={x_valle:.2f} y su ventana es [{lo:.2f}, {hi:.2f}]. "
        f"Es lo que limita paso_horizontal, no el hueco SAT")


# Censo de anchos minimos de panel por piso, mm. ESTIMADOS (spec §11):
# cierran cuando cada panel este dibujado. Fuente: conteo de mandos/jacks
# de los README de modulo + patch bay normalizado que anade jacks.
ANCHOS_PISO_SUP = {"MIDI/CV": 80, "VCO1": 90, "VCO2": 90, "VCO3": 90}
ANCHOS_PISO_INF = {"VCF": 100, "ADSR": 110, "VCA": 80, "MIXER": 100}
EXPANSION_MIN = 40  # sitio reservado a crecer, por piso


def main() -> int:
    p = leer_params()
    autocomprobacion(p)
    canario_solapes(p)
    canario_alineacion(p)
    guarda_piso(p)
    guarda_fresado(p)
    guarda_standoff(p)
    guarda_escalon(p)
    guarda_tapa(p)
    g = perfil(p)
    fallos: list[str] = []

    def exige(cond: bool, msg: str) -> None:
        (fallos.append if not cond else (lambda m: None))(msg)

    exige(g["alto_interior_inferior"]
          >= p["alto_transformador"] + p["margen_transformador"],
          "transformador no cabe en el piso inferior con margen")
    # Marco de remate = lo que queda del fondo detras de la cara superior.
    # AQUI HUBO un `marco >= 20` con el argumento "no caben los 20 mm del rail
    # de remate". La premisa caduco: el remate ya no vive en el marco, su Y se
    # deriva y baja por debajo del rail girado del panel (ver _y_remate). El
    # marco solo tiene que dar para que los largueros quepan DENTRO del
    # acrilico, y eso ya no se estima con una cota a ojo -- lo comprueba
    # `railes_dentro_del_costado()` en check_dxf.py, esquina por esquina y
    # contra el contorno RELEIDO del DXF, que es el unico que sabe cuanto
    # material se comio el redondeo en punta.
    #
    # Se conserva solo el techo, que sigue siendo un criterio de FORMA y no de
    # ajuste: pasado ese ancho el remate deja de leerse como punta y vuelve la
    # meseta trasera que hacia que la silueta pareciera una bota.
    marco = fondo(p) - g["prof_sup_min"]
    exige(marco <= 60,
          f"el marco de remate mide {marco:.1f} mm; por encima de 60 deja de "
          f"ser punta y vuelve la meseta trasera")
    exige(p["fondo_pcb_max"] + 10 <= fondo(p) - p["rail"],
          "la PCB mas honda del censo no cabe bajo la cara superior")
    # El ancho util ES el largo del riel, no una eleccion: los Z-Rails vienen en
    # largos de catalogo y el que se compro mide 528.32 (104 HP). Si esto se
    # desincroniza, o los rieles no llegan de costado a costado o hay que
    # cortarlos -- y cortar un extremo se lleva la punta por donde se fijan.
    exige(abs(g["ancho_util"] - p["largo_riel"]) < 0.01,
          f"ancho_util={g['ancho_util']:.2f} != largo_riel={p['largo_riel']}: "
          f"ancho_total tiene que valer largo_riel + 2*t_cheek = "
          f"{p['largo_riel'] + 2 * p['t_cheek']:.2f}")
    exige(sum(ANCHOS_PISO_SUP.values()) + EXPANSION_MIN <= g["ancho_util"],
          "el piso superior no cabe en el ancho util")
    exige(sum(ANCHOS_PISO_INF.values()) + EXPANSION_MIN <= g["ancho_util"],
          "el piso inferior no cabe en el ancho util")
    # CARA y PANEL ya no son el mismo numero, asi que por cada fila hay DOS
    # derivaciones que tienen que dar lo mismo y no una: la separacion de
    # railes sale de la cara (por donde se atornillan al costado) y tambien del
    # panel (por donde los ve el modulo). Si se separan, el panel no atornilla
    # -- que es exactamente el fallo que tuvo esta puerta en rojo.
    for piso, (ins_a, ins_b) in CARAS.items():
        sep = p[f"sep_railes_{piso}"]
        calc = p[f"alto_cara_{piso}"] - p[ins_a] - p[ins_b]
        exige(abs(sep - calc) < 0.001,
              f"sep_railes_{piso}={sep} no sale de alto_cara_{piso} - {ins_a} "
              f"- {ins_b} = {calc} (spec §6)")
        calc = p[f"alto_panel_{piso}"] - 2 * p["inset_er"]
        exige(abs(sep - calc) < 0.001,
              f"sep_railes_{piso}={sep} no sale del PANEL 3U "
              f"(alto_panel_{piso} - 2*inset_er = {calc}): la cara y la PCB "
              f"discrepan y el modulo no atornilla")
        # el panel tiene que CABER en su cara. Bisel CERO es legal y es lo que
        # pasa arriba a proposito: el panel remata a ras del vertice porque de
        # ahi cuelga la bisagra. Negativo no: seria panel volando sobre el aire.
        for nombre in (ins_a, ins_b):
            exige(p[nombre] - p["inset_er"] >= -1e-9,
                  f"el panel 3U desborda su cara por {nombre}: bisel "
                  f"{p[nombre] - p['inset_er']:.1f} mm (no puede ser negativo)")
    # EUROrack en las dos filas. La cota que manda NO es el alto del panel
    # (128.5 mm) sino la SEPARACION ENTRE RIELES: "ER Screw distance vertical
    # = 122,50 mm" (Doepfer; los taladros van a 3.0 mm de cada canto del panel
    # y miden 3.2). Verificado el 2026-08-17 contra midisoft.de y
    # exploding-shed.com.
    #
    # ESTUVO EN ROJO A PROPOSITO, luego en 122.50, luego en 123.00 -- la cota de
    # la MEJILLA FLAT-S de StudioRacks -- y de vuelta a 122.50 el 2026-08-17,
    # cuando Samuel confirmo que el riel que compra es el Z-Rail de Tiptop.
    # El 123.00 nunca fue una cota del riel: era la de una mejilla ya taladrada
    # que aqui no se compra, porque el costado lo cortamos nosotros. El Z-Rail
    # es una barra lisa con pletina roscada continua y acepta la separacion que
    # se le de, asi que quien manda vuelve a ser el panel.
    #
    # Sigue siendo una puerta y no un comentario: si alguien mueve un inset o
    # un alto de cara "para que quede mejor", esto vuelve a rojo antes de que
    # se corte nada.
    SEP_EUROrack = 122.5
    for piso, (ins_a, ins_b) in CARAS.items():
        exige(abs(p[f"sep_railes_{piso}"] - SEP_EUROrack) < 0.5,
              f"sep_railes_{piso}={p[f'sep_railes_{piso}']} != {SEP_EUROrack} "
              f"de EUROrack: un modulo 3U NO atornilla en esa fila. La cara se "
              f"dimensiona DESDE esta cota (alto_cara_{piso} = sep + {ins_a} + "
              f"{ins_b}), no al reves.")
    exige(p["vent_puente_min"] >= 0.8 * p["t_acrilico"],
          "puente de ventilacion fragil para el espesor")
    fallos.extend(solapes(p))
    fallos.extend(alineacion(p))

    print(f"perfil: alto_total={g['alto_total']:.1f}  "
          f"entrepiso={g['y_entrepiso']:.1f}  ancho_util={g['ancho_util']:.0f}")
    print(f"kerf aplicado: {p['kerf']:+.2f} mm  (proceso: FRESADO CNC)")
    if p["kerf"] == 0:
        print("  CERO es lo correcto fresando: el CAM compensa el radio de "
              "herramienta y la pieza sale a la cota del dibujo.")
    elif p["kerf"] < 0:
        print(f"AMARILLO: kerf {p['kerf']:+.2f} es NEGATIVO, que es "
              f"compensacion de LASER. Si de verdad se volvio al laser hay que "
              f"medirlo con el cupon Y por espesor -- la franja no es la misma "
              f"en 5 que en 8 mm. Si no, sobra y encoge todos los huecos.")
    else:
        print(f"AMARILLO: kerf {p['kerf']:+.2f} es POSITIVO — los agujeros "
              f"saldrian {2 * p['kerf']:.2f} mm sobre el nominal. Un kerf de "
              f"tabla de servicio (ancho de canal, siempre positivo) entra "
              f"aqui con el signo cambiado.")
    exige(-0.5 <= p["kerf"] <= 0.5,
          "kerf fuera de rango fisico [-0.5, +0.5] mm")
    for f in fallos:
        print(f"ROJO: {f}")
    if fallos:
        return 2
    print("clearance_budget: VERDE")
    return 0


# Lo que este calculo NO cubre (y donde se cierra):
#   * rigidez/flexion del vano de 500 mm  -> cargar el prototipo (spec §11)
#   * par de apriete sobre acrilico       -> probeta del cupon (spec §11)
#   * termica de la fuente v2             -> spec PSU v2 y su validacion
#   * nesting de planchas en el stock     -> lienzo del Task 5, a ojo
#   * largo de standoff / distancia perpendicular placa<->rail: alineacion()
#     verifica que la fila caiga en la centerline de un rail de esqueleto,
#     no cuanto hay entre la placa y ese rail — en las piezas voladas esa
#     distancia ES el largo del standoff (dato de compra del BOM, no una
#     holgura): 7 mm el par inferior del zocalo, ~33 el superior, 5 las
#     pieles. Se cierra midiendo los standoffs contra el modelo al comprar
#   * paneles inclinados (1.6 mm, PCB de aluminio de modulo) en solapes():
#     su ajuste lo resuelve la rotacion de railes (R3), no un AABB — un
#     rectangulo largo y fino en diagonal sobreestima demasiado con caja
#     alineada a ejes como para que el resultado signifique algo

if __name__ == "__main__":
    sys.exit(main())
