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

import contextlib
import io
import functools
import math
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "hardware", "tools"))
from canario import borde_rojo as _borde_rojo          # noqa: E402

PARAMS = Path(__file__).parent / "cad" / "params.scad"


def leer_params() -> dict[str, float]:
    texto = PARAMS.read_text(encoding="utf-8")
    pares = re.findall(r"^\s*(\w+)\s*=\s*(-?[0-9.]+)\s*;", texto, re.M)
    if len(pares) < 20:
        raise SystemExit(f"params.scad: solo {len(pares)} parametros parseados")
    p = {k: float(v) for k, v in pares}
    # ancho_total es DERIVADO desde el 2026-08-26 y por eso la regex de arriba
    # -- que solo lee literales -- no lo encuentra. Se calcula aqui con la
    # MISMA formula que usa el .scad.
    #
    # POR QUE DEJO DE SER LITERAL: estuvo en 544.32 escrito a mano mientras el
    # comentario de al lado daba la formula, asi que ancho_util coincidia con
    # el largo del riel por casualidad aritmetica. Desde que el marco va POR
    # FUERA, el acrilico ya no fija el hueco entre marco y riel. Con la holgura
    # de montaje metida en ese hueco, un literal se desincroniza al primer
    # cambio y el sintoma es un riel que no entra.
    #
    # QUIEN FIJA EL HUECO cambio otra vez el 2026-08-28. Fue el casquillo que
    # atravesaba el acrilico mientras la costilla era chapa; muerto el apilado,
    # a cada lado del riel quedan la PLACA de anclaje (t_placa) y la pared del
    # anillo (t_anillo). El acrilico sale de la cuenta: va dentro de la ventana.
    derivado = (p["largo_riel"] + p["hol_riel"]
                + 2 * p["t_placa"] + 2 * p["t_anillo"])
    if "ancho_total" in p:
        raise SystemExit(
            f"params.scad: ancho_total volvio a ser un literal ({p['ancho_total']:.2f}). "
            f"Es DERIVADO desde el 2026-08-26: largo_riel + hol_riel + "
            f"2*t_placa + 2*t_anillo = {derivado:.2f}. Un literal aqui vuelve a "
            f"esconder si el riel cabe o no.")
    p["ancho_total"] = derivado
    return p


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
        # del tope del suelo al fondo de la TAPA DEL VALLE. Fue la bandeja de
        # entrepiso hasta el 2026-08-21, y el numero no cambio al morir ella:
        # las dos planchas eran coplanares y del mismo espesor, asi que el techo
        # solo cambio de dueno. Donde el chasis NO queda debajo de la tapa del
        # valle la altura real es mayor -- este numero se queda corto a
        # proposito, que es el lado seguro.
        # Ya NO resta t_base: desde el 2026-08-27 el suelo es la cara de
        # arriba de la TABLA, que vive bajo el marco (y = -t_base .. 0). El
        # datum del interior es y=0 y el case gana los 8 mm que ocupaba la
        # plancha de acrilico.
        "alto_interior_inferior": y_entrepiso - p["t_valle"],
        # EL HUECO ENTRE LAS CARAS INTERIORES DE LOS DOS ANILLOS, no el hueco
        # entre acrilicos: el acrilico va DENTRO de la ventana del anillo y su
        # espesor ya no fija esta cota. Lo unico que ancho_total suma a cada
        # lado es la pared del anillo, asi que restarla devuelve
        # largo_riel + hol_riel + 2*t_placa.
        #
        # LA PLACA DE ANCLAJE ESTA DENTRO de este hueco y por eso no se resta
        # aqui: el riel mide ancho_util - 2*t_placa y muere contra ella. Todo
        # lo demas que cruza el case de cara a cara -- miembros, planchas --
        # cruza ancho_util entero.
        "ancho_util": p["ancho_total"] - 2 * p["t_anillo"],
    }


def autocomprobacion(p: dict[str, float]) -> None:
    """Caso hecho a mano (spec §4 rev. 3): 12/35 grados, panel 190, vertice
    frontal a 50. Son numeros FIJOS a proposito -- no los de params -- para
    que la trigonometria se compruebe contra una cuenta hecha a lapiz que no
    se mueve cuando el diseno cambia."""
    g = perfil({**p, "angulo_inferior": 12, "angulo_superior": 35,
                "alto_cara_inf": 190, "alto_cara_sup": 190,
                "alto_frontal": 50, "paso_horizontal": 20,
                "t_valle": 5, "ancho_total": 500})
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

    Los cuatro rieles quedan fijos al marco por ambas puntas; ninguno funciona
    como eje o cierre manual."""
    # cada punta lleva SU inset, gobernado por la curva que la remata (ver la
    # tabla de insets en params.scad)
    caras = [(P[1], P[2], (p["inset_inf_frente"],
                           p["alto_cara_inf"] - p["inset_inf_valle"])),
             (P[3], P[4], (p["inset_sup_valle"],
                           p["alto_cara_sup"] - p["inset_sup_remate"]))]
    # el eje del M4 de punta esta a rail_er_eje del panel, no a rail/2: el riel
    # EUROrack es hondo (27.4) y su taladro cae en su centroide
    off = p["rehundido_panel"] + p["t_panel"] + p["rail_er_eje"]
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
    dx_inf = p["rehundido_panel"] * math.cos(
        math.radians(p["angulo_inferior"]))
    dx_sup = p["rehundido_panel"] * math.cos(
        math.radians(p["angulo_superior"]))
    return (P[2][0] + _tangente(P[2], P[1], P[3], p["radio_pico"]),
            cr[2][0] - _he_er(p, p["angulo_superior"])[0]
            - p["holgura_rail"] + dx_inf - dx_sup)



def _x_chasis_frente(p: dict[str, float]) -> float:
    """Cara delantera del chasis del PSU.

    Cuelga del larguero TRASERO, a chasis_holgura_larguero, y de ahi hacia
    delante no hay nada: una sola cadena en un solo sentido. Estuvo escrita
    dentro de _centros_transversal() porque de ella colgaba `base delantera`,
    que se plantaba otra holgura por delante del chasis. Muerta esa barra el
    2026-08-27, la cadena se acaba en el chasis y quien la necesita es ch_pos()
    -- que la calculaba al reves, sumando vuelo + rail + holgura desde el canto
    de la plancha, y solo daba lo mismo por como estaba puesta la barra."""
    return (_talon(p)["x_pie"] - p["chasis_holgura_larguero"]
            - _chasis(p)["tapa_y"])


def _chasis_tornillos(p: dict[str, float]) -> list[tuple[float, float]]:
    """Los cuatro M4 del suelo del chasis a la tabla, en coordenadas
    INTERIORES del chasis (x a lo largo, y en el fondo). GEMELA de
    chasis_tornillos_int() en el .scad."""
    tx, ty = p["chasis_tornillo_x"], p["chasis_tornillo_y"]
    return [(tx, ty), (p["chasis_int_x"] - tx, ty),
            (tx, p["chasis_int_y"] - ty),
            (p["chasis_int_x"] - tx, p["chasis_int_y"] - ty)]


def _chasis_tornillos_tabla(p: dict[str, float]) -> list[tuple[float, float]]:
    """Los mismos cuatro en coordenadas LOCALES de bandeja_base_2d: la misma
    cadena que salida_cables_xy() en el .scad (x local = z del mundo, y local
    = x del mundo, sin vuelo desde el papel del suelo; el interior arranca
    desfase + t dentro de la envolvente de la tapa). GEMELA de
    chasis_tornillos_tabla()."""
    c = _chasis(p)
    au = perfil(p)["ancho_util"]
    pos_x = p["t_anillo"] + au - p["chasis_margen_bandeja"] - c["tapa_x"]
    pos_y = _x_chasis_frente(p)
    d = c["desfase"] + p["t_chapa"]
    return [(pos_x + d + ix, pos_y + d + iy) for ix, iy in _chasis_tornillos(p)]


# _centros_transversal() murio aqui el 2026-08-27; sus gemelas del .scad --
# centros_transversal(), ct_base(), ct_valle() y ct_remate() -- aguantaron un
# dia mas, hasta el 2026-08-28, porque bom() todavia contaba esa lista para
# decir "x3". Hoy los cuenta miembros_lista(), que son los miembros mismos.
#
# Los tres 2020 que aquella lista describia se sustituyeron por miembros de
# chapa con volumen, caras de apoyo y mas de una linea de anclaje; reducirlos
# otra vez a un punto central perderia justo la geometria que los distingue.


# Que inset gobierna cada punta de cada cara. El orden es el mismo que usa
# _centros_rail(): primero el de arranque, luego el de remate.
CARAS = {"inf": ("inset_inf_frente", "inset_inf_valle"),
         "sup": ("inset_sup_valle", "inset_sup_remate")}

# 4 railes de panel fijos: dos por cara, como cualquier fila EUROrack.
NOMBRES_CR = ["cara_inf frente", "cara_inf valle",
              "cara_sup valle", "cara_sup remate"]
ANGS_CR = ["angulo_inferior", "angulo_inferior",
           "angulo_superior", "angulo_superior"]
# Caja = (nombre, x0, x1, y0, y1, z0, z1)
Caja = tuple
# Fila de agujeros de una placa = (placa, fila, eje, coordenada en ese eje,
# rail frontera al que DEBE anclar). El eje es el que recorre la placa de un
# rail frontera al otro: X en las bandejas (horizontales), Y en las pieles
# (verticales). El rail va declarado, no se busca el mas cercano:
# una fila que cae por casualidad en la centerline de otro rail no esta
# anclada donde el diseno dice, y ese acierto casual no debe pasar la puerta.
Fila = tuple
# --- LA TRASERA CAPTURADA (2026-08-29, noche, 2) ------------------------
#
# Samuel, mirando el render de #241: "preferiria que la relacion del acrilico
# con el acero en la parte de atras fuera igual que en las mejillas (la forma
# en que se unen)". La mejilla va DENTRO de un rebaje del anillo, rehundida
# tras un labio de 3, con 6 de acrilico en el bolsillo sobre una junta de 1,
# retenida hacia fuera por el labio y hacia dentro por el marco, sin un
# taladro. La trasera hace ahora lo mismo con LOS MISMOS TRES NUMEROS,
# girados: un BOLSILLO fresado en la cara interior de cada anillo a lo largo
# del tramo trasero -- labio de rehundido_acrilico en el canto, rebaje_anillo
# de hondo, t_anillo - rehundido de ancho --, sus puntas dentro, su cara vista
# rehundida labio + junta, y arriba y abajo dos chapas con labio por fuera:
# el talon (la nariz de atras) y el techo. Cero taladros, cero cabezas atras.
# Entra deslizando desde ABAJO, con la tabla fuera: el bolsillo sale por el
# canto de abajo y se cierra arriba. Spec
# 2026-08-29-trasera-capturada-talon-nariz-design.md.
#
# GEMELO de bolsillo_trasero(), trasera_*() y trasera_campo() en el .scad; el
# DXF lo cruzan anillo_tiene_bolsillo_trasero(), anillo_tiene_rebaje() y
# agujeros_donde_toca() en check_dxf.


# --- los derivados del rebaje de chapa (2026-08-30) --------------------------
# NINGUNO DE ESTOS ES UN PARAMETRO, y esa es la mitad del diseno. Cada uno sale
# de cotas mas primitivas y tiene su GEMELO en sam17_case.scad; el dia que
# alguien mueva rehundido_chapa o aire_labios en params.scad, todo esto se
# recoloca solo en los dos archivos y check_dxf lo cruza contra el DXF. Ponerlos
# en params.scad seria darle dos fuentes a la misma cota, que es como el repo se
# ha roto antes (cara_anillo_trasera fue derivado Y mutable a la vez, y la
# ronda 3 del revisor lo caz~o).

def _rehundido_trasera(p: dict[str, float]) -> float:
    """Cuanto retrocede la cara vista de la trasera del plano trasero, menos su
    junta de asiento. Fue rehundido_acrilico (3) hasta el 2026-08-30; ahora lo
    manda la RENDIJA: con la chapa rehundida 1, la cara interior del labio del
    techo se aleja 1 del plano, y para que entre ella y la plancha queden
    aire_labios de luz, la plancha tiene que retroceder lo mismo. Es la unica
    cota de la trasera que deja de ser "la del costado, girada".
    GEMELO de rehundido_trasera() en sam17_case.scad."""
    return (p["rehundido_chapa"] + p["t_costilla"]
            + p["aire_labios"] - p["t_junta_asiento"])


def _radio_borde(p: dict[str, float]) -> float:
    """El radio del contorno del anillo en las esquinas donde entra chapa. El
    contorno del anillo es la cara exterior de la chapa desplazada rehundido
    hacia fuera, asi que su radio es el del pliegue mas el rehundido, y los dos
    arcos quedan CONCENTRICOS: se leen como el mismo plano aunque el taller
    doble a 2.9 o a 3.1, porque la diferencia cae dentro de la junta de sombra y
    no sobre una arista compartida. GEMELO de radio_borde()."""
    return p["radio_chapa"] + p["rehundido_chapa"]


def _muesca_pie(p: dict[str, float]) -> float:
    """Lo que se recorta en cada punta del desarrollo de la nariz y del talon.

    LOS PIES NO SE REHUNDEN: apoyan en la tabla con su cara de abajo a ras de la
    del anillo, porque rehundir un tramo horizontal es levantarlo 1 mm de la
    tabla, y ahi no hay nada que ver ni que empotrar (la tabla lo tapa). Pero el
    resto de la pieza SI entra en el rebaje, y entra mas ancha. La diferencia se
    corta en la punta: la pared del rebaje esta rebaje_chapa dentro de la cara,
    lo rehundido se queda hol_chapa antes de ella, y el pie llega hol_piel
    despues de la cara. GEMELO de muesca_pie()."""
    return p["rebaje_chapa"] - p["hol_chapa"] + p["hol_piel"]


def _cara_anillo_trasera(p: dict[str, float]) -> float:
    """La franja del anillo en el tramo trasero, de fuera a dentro: el bolsillo
    de la trasera (labio + 11) + su pared + el rebaje (vacio desde el
    2026-10-11; fue lo que entraba el costado).

    FUE UN PARAMETRO DE 20 y es DERIVADO desde el 2026-08-30, con 22. El
    revisor de la ronda 3 cazo que se usaba como derivado Y se mutaba como
    parametro a la vez, o sea que tenia dos fuentes: la mutable es ahora
    entrada_costado_trasero. GEMELO de cara_anillo_trasera()."""
    bo = _bolsillo_trasero(p)
    return bo["rebaje_costado"] + p["entrada_costado_trasero"]


def _chapa_largo_rebaje(p: dict[str, float]) -> float:
    """Lo que mide una chapa de canto a canto entre las paredes de los dos
    rebajes: mas que el vano entre caras, y por eso las tres chapas entran con
    el segundo anillo, como la trasera y los costados. GEMELO de
    chapa_largo_rebaje()."""
    return p["ancho_total"] - 2 * (p["t_anillo"] + p["hol_piel"]
                                   - _muesca_pie(p))


def _bolsillo_trasero(p: dict[str, float]) -> dict:
    """El bolsillo de la trasera en el tramo trasero de cada anillo, en u
    (distancia al plano trasero) y z (desde la cara vista): labio u = 0..u0,
    bolsillo u = u0..u1 por z = z0..t_anillo.

    CERRADO POR LOS DOS EXTREMOS: de y_bot (0.5 bajo el canto de la trasera,
    que apoya en el pie del talon) a y_fin (0.5 sobre su otro canto, 1.0 bajo
    la brida del techo). Salir por arriba dejaba un agujero de 11 x 6 a la
    vista en el canto superior del anillo, junto al techo; salir por abajo
    obligaba a que toda la plancha pasara por la boca estrecha bajo el chaflan
    de P6, y no pasaba (el revisor del PR). La trasera entra al montar el
    segundo anillo, como los costados. Bajo y_paso (la coronacion de la pared
    de u = u0 sobre el chaflan, mas 0.5) arranca en u_paso para no morder la
    cara del chaflan: un escalon que la esquina de la plancha, a chaflan,
    libra. Y la pared con el bolsillo del costado, que en este tramo
    retrocede a u1 + pared (rebaje_costado). GEMELA de bolsillo_trasero_2d()."""
    u0 = _rehundido_trasera(p)                # DERIVADO desde el 2026-08-30
    u1 = u0 + (p["t_anillo"] - p["rehundido_acrilico"])   # el ancho no cambia: 11
    c, t = p["chaflan_nariz"], p["t_costilla"]
    y_bot = t - 0.5                           # 0.5 bajo el canto de la trasera, que apoya en el pie
    return {"u0": u0, "u1": u1, "ancho": u1 - u0,
            "z0": p["t_anillo"] - p["rebaje_anillo"],
            "hondo": p["rebaje_anillo"],
            "pared": p["pared_rebaje_trasera"],
            "rebaje_costado": u1 + p["pared_rebaje_trasera"],
            # CERRADO POR LOS DOS EXTREMOS: de y_bot a y_fin. Bajo y_paso (la
            # coronacion de la pared de u = u0 sobre el chaflan, mas 0.5) el
            # bolsillo arranca en u_paso para no morder la cara del chaflan.
            "y_bot": y_bot,
            "y_fin": _vertices(p)[5][1] - t - p["brida_ancho"] - 1.0,
            "y_paso": c - u0 + 0.5, "u_paso": c - y_bot + 0.5}


def _y_labio_techo(p: dict[str, float]) -> float:
    """El canto de abajo del labio (B) o de la banda (A) del techo, en y del
    mundo: la coronacion de lo que se ve de la trasera por arriba."""
    P = _vertices(p)
    if _chaflan_p5(p):
        return P[5][1] - p["chaflan_nariz"] - p["techo_labio"]
    return P[5][1] - p["banda_trasera"]


def _trasera(p: dict[str, float]) -> dict:
    """La trasera capturada: su caja y sus cotas. x1 es su cara vista
    (rehundida labio + junta del plano trasero), x0 su cara interior; z0/z1
    sus puntas, dentro de los bolsillos menos hol_piel; y0 sobre el pie del
    talon; y1 medio milimetro bajo lo que el techo tiene encima en su cara
    vista -- el chaflan (B) o el doblez de la banda (A)."""
    P = _vertices(p)
    b = _bolsillo_trasero(p)
    t = p["t_costilla"]
    x1 = P[6][0] - b["u0"] - p["t_junta_asiento"]
    z0 = b["z0"] + p["hol_piel"]
    # EL CANTO DE ARRIBA MUERE 1.5 BAJO LA BRIDA DEL TECHO: 0.5 de aire al fin
    # del bolsillo, que a su vez se cierra 1.0 por debajo del canto de la
    # brida (dos cosas en la misma cara del anillo no comparten arista). Una
    # trasera que subiera mas necesitaria las muescas de esquina de #241. Por
    # debajo del labio (o la banda) quedan 6.5 tapados.
    y1 = P[5][1] - t - p["brida_ancho"] - 1.5
    return {"x0": x1 - p["t_piel"], "x1": x1,
            "y0": t, "y1": y1,
            "z0": z0, "z1": p["ancho_total"] - z0,
            "au": p["ancho_total"] - 2 * z0,
            "alto": y1 - t,
            "entra": b["hondo"] - p["hol_piel"],
            "aire_labios": b["u0"] + p["t_junta_asiento"] - t,
            # EL CHAFLAN DE SU ARISTA DE ABAJO-FUERA, a 45 por todo el largo: lo
            # que hace falta para librar con 0.5 el escalon del bolsillo bajo el
            # chaflan del anillo con la plancha en el fondo del bolsillo (donde
            # descansa hasta que llega la tabla) y pegada al labio (junta
            # aplastada). GEMELA de chaflan_trasera_bajo() en el .scad.
            "chaflan_bajo": ((b["u_paso"] + 0.5 - b["u0"])
                             + (b["y_paso"] - b["y_bot"]))}


def _trasera_campo(p: dict[str, float]) -> tuple[float, float]:
    """Lo que de la trasera se VE entre los dos labios: de la coronacion del
    labio del talon a la del techo. A esto se anclan la rejilla, las ondas,
    el IEC y KONDOR desde que no hay filas de M3. GEMELA de trasera_campo()."""
    return (p["chaflan_nariz"] + p["talon_labio"], _y_labio_techo(p))


def _entre_anillos(p: dict[str, float]) -> float:
    """Lo que mide una chapa que va entre las CARAS interiores de los anillos
    con hol_piel a cada lado.

    Desde el 2026-08-30 esto solo vale para los tramos que NO entran en el
    rebaje: los pies de la nariz y del talon, que apoyan a ras en la tabla. Lo
    que entra en rebaje mide mas -- _chapa_largo_rebaje() -- y es lo que manda
    el blank; la diferencia se corta como muesca en cada punta del pie."""
    return perfil(p)["ancho_util"] - 2 * p["hol_piel"]


def _bd_pestana(p: dict[str, float]) -> float:
    """Bend deduction del doblez a 90 de una pestana lanzada, con su radio
    apretado (radio_doblez_pestana). GEMELA de pestana_bd() en el .scad."""
    r, t = p["radio_doblez_pestana"], p["t_costilla"]
    return 2 * (r + t) - math.pi / 2 * (r + p["k_factor"] * t)


def _cajas_miembro(p: dict[str, float], P: list[tuple[float, float]],
                    cr: list[tuple[float, float]], z0: float,
                    z1: float) -> dict[str, Caja]:
    """Las CARAS VISTAS de atras: el labio (B) o la banda (A) del techo y el
    labio del talon, t_costilla de espesor, REHUNDIDOS del plano trasero.

    Fueron las bandas de 24 que recibian los M3 de la trasera (#241); desde la
    trasera capturada no reciben nada: tapan. La meseta, el pie y las
    pestanas van aparte como caras (_caras_miembro).
    El argumento cr se queda por los llamadores.

    ESTABAN A RAS DEL PLANO TRASERO hasta el 2026-08-30 y ahora entran
    rehundido_chapa en el rebaje del anillo. No es cosmetico: estas cajas son
    las que cuerpos_dentro_del_anillo() compara contra el contorno del DXF, y
    con el contorno redondeado a radio_borde (5.5, mayor que antes) una caja a
    ras se sale por la esquina -- que es exactamente lo que el fichero correcto
    denunciaba."""
    t = p["t_costilla"]
    x1 = P[6][0] - p["rehundido_chapa"]
    c, lab = p["chaflan_nariz"], p["talon_labio"]
    if _chaflan_p5(p):
        lt = p["techo_labio"]
        alto = ("trasero alto", x1 - t, x1, P[5][1] - c - lt, P[5][1] - c, z0, z1)
    else:
        alto = ("trasero alto", x1 - t, x1, P[5][1] - p["banda_trasera"], P[5][1],
                z0, z1)
    return {"trasero alto": alto,
            "talon": ("talon", x1 - t, x1, c, c + lab, z0, z1)}


def _ventana_valle(p: dict[str, float], P: list[tuple[float, float]],
                   cr: list[tuple[float, float]]) -> tuple[float, float]:
    """(x0, x1) de la ventana del valle: lo libre entre los dos rieles 3U que
    miran al valle, donde vive la fila auxiliar KONDOR. GEMELA de
    ventana_valle().

    Delante la manda la envolvente CERRADA del riel del valle de la fila de
    abajo mas holgura. Los paneles se desmontan quitando tornillos: no giran
    sobre esos tornillos y ningun radio de apertura gobierna esta ventana.
    Detras manda la esquina cerrada del riel superior menos holgura_rail."""
    return (cr[1][0] + _he_er(p, p["angulo_inferior"])[0]
            + p["holgura_rail"],
            _x_valle(p, P, cr)[1])


def _guarda_frente_panel_fijo(actual: float, esperado: float) -> None:
    """La ventana usa la envolvente cerrada, nunca un barrido de apertura."""
    assert abs(actual - esperado) < 0.001, (
        f"el frente de la ventana queda en {actual:.6f}, pero con paneles "
        f"fijos la envolvente cerrada exige {esperado:.6f}; queda activo un "
        f"barrido heredado de tapa/bisagra")


def guarda_paneles_fijos(p: dict[str, float]) -> None:
    """Los paneles se desmontan por tornillos; no giran sobre los rieles."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    actual = _ventana_valle(p, P, cr)[0]
    esperado = (cr[1][0] + _he_er(p, p["angulo_inferior"])[0]
                + p["holgura_rail"])
    _guarda_frente_panel_fijo(actual, esperado)
    print("paneles fijos: la ventana usa la envolvente cerrada del Z-Rail; "
          "sin ejes, barridos ni angulo minimo de apertura")


def canario_paneles_fijos(p: dict[str, float]) -> None:
    """Reintroducir el radio de giro heredado debe tumbar la puerta."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    esperado = (cr[1][0] + _he_er(p, p["angulo_inferior"])[0]
                + p["holgura_rail"])
    barrido_heredado = (cr[1][0]
                        + math.hypot(p["rail_er_fondo"], p["rail_er_alto"]) / 2
                        + p["holgura_rail"])
    try:
        _guarda_frente_panel_fijo(barrido_heredado, esperado)
    except AssertionError as e:
        assert "barrido heredado" in str(e), (
            f"canario de panel fijo salto por '{str(e)}'")
        return
    raise AssertionError(
        "canario de panel fijo NO detecto el radio de giro heredado")


# El aire entre el labio de la chapa y el canto del panel (ficha 6, persiana
# del 11-10). Por abajo lo pone la nariz; por arriba, el retorno del techo.
# Cada labio tiene que hacer dos cosas a la vez: dejar que el panel salga de
# frente sin rozarlo (LABIO_AIRE_MIN al canto del panel) y pasar del canto del
# riel (LABIO_SOBRE_RIEL_MIN sobre su cara), porque si se queda corto, detras
# del ala del riel vuelve a verse el interior. Las dos reglas del barrido que
# dejaban la rendija abierta (1 mm de aire BAJO el riel, holgura_rail SOBRE el
# riel) eran de cuando las filas giraban; desde la tanda B los paneles son
# fijos (guarda_paneles_fijos()).
LABIO_AIRE_MIN = 1.0
LABIO_SOBRE_RIEL_MIN = 0.5
# Y como ahora el labio pasa POR DELANTE de la cara del riel, entre los dos
# tiene que quedar aire de fondo: la chapa ocupa t_costilla desde la silueta y
# la cara del riel esta detras del panel, a rehundido_panel + t_panel.
LABIO_FONDO_MIN = 0.5


def _labio_chapas(p: dict[str, float]) -> dict[str, tuple[float, float, float]]:
    """(donde acaba el labio, donde empieza la cara del riel, donde empieza el
    panel), en mm a lo largo de cada cara y medidos desde el canto del panel
    hacia fuera. Abajo, la nariz sube por la cara de abajo hasta s_top (GEMELA
    de nariz_s_top()); arriba, el retorno del techo baja por la cara de arriba
    hasta L - retorno_meseta (GEMELA de miembro_alto())."""
    s_nariz = _nariz(p)["s_top"]
    s_riel_inf = p["inset_inf_frente"] - p["rail_er_alto"] / 2
    s_panel_inf = p["inset_inf_frente"] - p["inset_er"]
    L = p["alto_cara_sup"]
    s_ret = L - p["retorno_meseta"]
    s_riel_sup = L - p["inset_sup_remate"] + p["rail_er_alto"] / 2
    s_panel_sup = p["inset_sup_valle"] - p["inset_er"] + p["alto_panel_sup"]
    # Abajo se mide desde P1 subiendo por la cara; arriba, desde el pico (P4)
    # bajando. Asi, en los dos, riel < labio < panel cuando la rendija esta
    # cerrada y el panel sale de frente.
    return {"abajo": (s_nariz, s_riel_inf, s_panel_inf),
            "arriba": (L - s_ret, L - s_riel_sup, L - s_panel_sup)}


def _guarda_labio(labios: dict[str, tuple[float, float, float]]) -> None:
    for donde, (labio, riel, panel) in labios.items():
        aire = panel - labio
        sobre = labio - riel
        assert aire >= LABIO_AIRE_MIN - 1e-9, (
            f"el labio de la chapa queda a {aire:.2f} mm del panel por {donde}: "
            f"con menos de {LABIO_AIRE_MIN:g} el panel no sale de frente sin "
            f"rozarla")
        assert sobre >= LABIO_SOBRE_RIEL_MIN - 1e-9, (
            f"el labio de la chapa pisa {sobre:.2f} mm de la cara del riel por "
            f"{donde} y se piden {LABIO_SOBRE_RIEL_MIN:g}: detras vuelve a verse "
            f"el interior (la rendija de la ficha 6)")


def _fondo_labio(p: dict[str, float]) -> dict[str, float]:
    """Aire, en la normal de la cara, entre la cara de dentro de la chapa y la
    cara del riel que el labio tapa por delante. NO ES EL MISMO EN LOS DOS: la
    nariz tapa el riel con su tramo [C3, C4], que va a ras de la silueta; el
    techo va entero rehundido rehundido_chapa, retorno incluido (techo() en
    sam17_case.scad). Hasta el 2026-10-12 los dos salian con la cuenta de la
    nariz, y el de arriba daba 1.60 donde hay 0.60."""
    riel = p["rehundido_panel"] + p["t_panel"]
    return {"abajo": riel - p["t_costilla"],
            "arriba": riel - p["rehundido_chapa"] - p["t_costilla"]}


def _guarda_fondo(fondos: dict[str, float]) -> None:
    for donde, fondo in fondos.items():
        assert fondo >= LABIO_FONDO_MIN - 1e-9, (
            f"el labio de la chapa pasa {donde} a {fondo:.2f} mm de la cara del "
            f"riel, por delante, y se piden {LABIO_FONDO_MIN:g}: la chapa toca el riel")


def guarda_labio_chapas(p: dict[str, float]) -> None:
    """La nariz y el techo acaban sobre el ala del riel, ni dentro de la huella
    del panel ni antes del canto del riel, y sin tocar la cara del riel por
    detras (ficha 6; persiana §7.3)."""
    labios = _labio_chapas(p)
    _guarda_labio(labios)
    fondos = _fondo_labio(p)
    _guarda_fondo(fondos)
    print("labio de las chapas (ficha 6): " + ", ".join(
        f"{d} a {panel - labio:.2f} del panel, {labio - riel:.2f} sobre el riel y "
        f"{fondos[d]:.2f} de fondo contra su cara"
        for d, (labio, riel, panel) in labios.items()))


def canario_labio_chapas(p: dict[str, float]) -> None:
    """Los dos lados tienen que saltar: un labio que pisa la huella del panel y
    uno que se queda antes del canto del riel. Y el fondo de arriba, que es el
    justo."""
    for cambio, aviso in (({"retorno_meseta": p["retorno_meseta"] + 0.5}, "no sale de frente"),
                          ({"retiro_placa_inf": p["retiro_placa_inf"] - 2.0}, "vuelve a verse")):
        try:
            _guarda_labio(_labio_chapas({**p, **cambio}))
        except AssertionError as e:
            assert aviso in str(e), f"canario del labio salto por '{e}'"
            continue
        raise AssertionError(f"canario del labio NO salto ({aviso})")
    # EL FONDO DE ARRIBA va a 0.6 contra 0.5: dos decimas mas de rehundido del
    # techo y la chapa toca el riel. El canario lo mide solo, porque esa misma
    # mutacion mueve antes el labio de la nariz.
    try:
        _guarda_fondo(_fondo_labio({**p, "rehundido_chapa": p["rehundido_chapa"] + 0.2}))
    except AssertionError as e:
        assert "arriba" in str(e) and "toca el riel" in str(e), f"canario del fondo salto por '{e}'"
    else:
        raise AssertionError("canario del fondo del labio NO salto (toca el riel)")


# Aire minimo entre la cara de fuera de la tira del valle y el camino del
# modulo KONDOR, que sale en vertical por su canto de atras (ficha 6).
TIRA_AIRE_MIN = 0.5


def _tira_valle(p: dict[str, float]) -> dict[str, object]:
    """La tira negra del valle (ficha 6), en el plano del perfil. GEMELA de
    tira_valle_pie()/tira_valle_arista()/tira_valle_2d_pts() de sam17_case.scad:
    el pie sobre el ala libre del riel de atras de la fila KONDOR, recostada en
    la arista de abajo del riel bajo de la fila alta, t_tira_valle de grueso
    hacia fuera."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ck = _centros_rail_1u(p, P, cr)
    a = math.radians(p["angulo_superior"])
    d = (math.sin(a), math.cos(a))
    n = (-math.cos(a), math.sin(a))
    c = cr[2]
    pie = (ck[1][0] + p["rail_er_alto"] / 2 - p["hol_tira_valle"],
           P[3][1] - p["rehundido_panel"] - p["t_panel"])
    arista = (c[0] - d[0] * p["rail_er_alto"] / 2 + n[0] * p["rail_er_eje"],
              c[1] - d[1] * p["rail_er_alto"] / 2 + n[1] * p["rail_er_eje"])
    ancho = math.hypot(arista[0] - pie[0], arista[1] - pie[1])
    u = ((arista[0] - pie[0]) / ancho, (arista[1] - pie[1]) / ancho)
    t = p["t_tira_valle"]
    pts = [pie, arista, (arista[0] - u[1] * t, arista[1] + u[0] * t),
           (pie[0] - u[1] * t, pie[1] + u[0] * t)]
    return {"pts": pts, "ancho": ancho,
            "largo": p["ancho_total"] - 2 * p["t_anillo"] - 2 * p["t_placa"]
            - 2 * p["hol_tira_valle_z"],
            "canto_kondor": ck[1][0] + p["inset_er"],
            "ala_kondor": ck[1][0] + p["rail_er_alto"] / 2}


def _guarda_tira(t: dict[str, object]) -> None:
    pie = t["pts"][0]
    assert t["canto_kondor"] < pie[0] <= t["ala_kondor"] + 1e-9, (
        f"el pie de la tira del valle cae en x={pie[0]:.2f}, fuera del ala libre "
        f"del riel KONDOR ({t['canto_kondor']:.2f}..{t['ala_kondor']:.2f}): "
        f"no apoya")
    x_min = min(q[0] for q in t["pts"])
    assert x_min - t["canto_kondor"] >= TIRA_AIRE_MIN, (
        f"la cara de fuera de la tira del valle llega a x={x_min:.2f}, a "
        f"{x_min - t['canto_kondor']:.2f} del canto del panel KONDOR: el modulo "
        f"sale hacia arriba y la roza (minimo {TIRA_AIRE_MIN:g})")


def guarda_tira_valle(p: dict[str, float]) -> None:
    """La tira negra del valle (ficha 6) apoya en el ala del riel KONDOR y no
    roza el camino del modulo KONDOR. Imprime las cotas de corte: son las del
    BOM y el pliego, que no las copian a mano."""
    t = _tira_valle(p)
    _guarda_tira(t)
    x_min = min(q[0] for q in t["pts"])
    print(f"tira del valle (ficha 6): chapa de {p['t_tira_valle']:g}, "
          f"{t['largo']:.2f} x {t['ancho']:.2f}; el pie en el ala del riel KONDOR "
          f"y {x_min - t['canto_kondor']:.2f} mm de aire al camino del modulo")


def canario_tira_valle(p: dict[str, float]) -> None:
    """Los dos lados tienen que saltar: un pie que se cae del ala y una tira
    tan gruesa que entra en el camino del modulo KONDOR."""
    for cambio, aviso in (({"hol_tira_valle": -0.5}, "no apoya"),
                          ({"t_tira_valle": 2.5}, "la roza")):
        try:
            _guarda_tira(_tira_valle({**p, **cambio}))
        except AssertionError as e:
            assert aviso in str(e), f"canario de la tira salto por '{e}'"
            continue
        raise AssertionError(f"canario de la tira NO salto con {cambio}")


def _frente_kondor(p: dict[str, float], P: list[tuple[float, float]],
                   cr: list[tuple[float, float]]) -> float:
    """X invariante del primer KONDOR antes de rehundir los paneles.

    El riel 3U inferior se desplaza por su normal y mueve lateralmente el borde
    conservador de _ventana_valle(). KONDOR solo debe bajar: se descuenta esa
    componente X para no arrastrar la fila, la tapa ni su camino de carga.
    """
    dx_rehundido_3u = p["rehundido_panel"] * math.cos(
        math.radians(p["angulo_inferior"]))
    return _ventana_valle(p, P, cr)[0] - dx_rehundido_3u


def _centros_rail_1u(p: dict[str, float], P: list[tuple[float, float]],
                      cr: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Dos Z-Rails KONDOR ARRIMADOS AL FRENTE de la ventana del valle, gemelos de
    centros_rail_1u(): el primer riel recibe bajo su cara delantera los 2 mm de
    prolongacion maciza y la tira anti-ruido, y lo que sobre de ventana queda
    detras, bajo el vuelo de la cara de arriba. Se centraban en la boca de la
    bahia hasta el 2026-08-29."""
    xa = _frente_kondor(p, P, cr) + p["rail_er_alto"] / 2
    sep = p["alto_panel_1u"] - 2 * p["inset_er"]
    y = (P[3][1] - p["rehundido_panel"] - p["t_panel"]
         - p["rail_er_eje"])
    return [(xa, y), (xa + sep, y)]


# --- LOS ANCLAJES DE LA CARA INTERIOR (2026-08-28) ---------------------
#
# NADA ATRAVIESA LA CARA VISTA. El eje del M4 de cada riel cae a 15.90 de la
# silueta, o sea dentro del rebaje, donde el anillo solo tiene 3 mm de labio:
# un tornillo ahi sale por fuera. Asi que el riel muere contra una PLACA de
# t_placa apoyada en la franja interior, y es la placa la que va al anillo con
# dos M4 a rosca ciega. Los miembros hacen lo mismo con una BRIDA doblada de
# su propio blank.
#
# Cuanto se corre cada placa a lo largo de su tramo respecto al pie del riel.
# CERO salvo donde solapes() lo obligo, y las dos excepciones llevan su numero
# porque son ADJUDICACIONES y no gustos:
# ---------------------------------------------------------------------------
# EL MARCO DE LA VENTANA (2026-08-29, noche). Samuel dijo el 28 que "la placa
# es el marco de la fila"; esto lo lleva hasta el final: las tres placas de
# anclaje, los dos clips y la escuadra de cada costado son UNA pletina de
# t_placa con el contorno de la ventana del anillo, corrida por los SIETE
# tramos. Sobre las tres filas es exactamente la placa de ayer -- mismo canto
# visto, mismos cajeados, mismas roscas --; en el frente, el suelo, la meseta
# y la trasera es el tope del acrilico que daban los clips y la escuadra.
#
# GEMELA de patas_marco(), marco_ventana_2d() y roscas_marco() en el .scad; el
# DXF lo cruza taladros_marco_ventana() en check_dxf.
#
# EL CANTO EXTERIOR NO VA SIEMPRE A LA SILUETA, y la razon es lo que hay
# encima de cada tramo:
#   filas (cara_inf, valle, cara_sup)   a la silueta: el marco de la fila que
#                                        Samuel aprobo, con los retiros de hoy
#   frente, suelo, meseta, cola de la    retirado t_costilla + hol_piel: encima
#   cara de arriba bajo el retorno       va chapa a ras de la silueta (nariz y
#                                        su pie, pie del talon, meseta, retorno)
#   trasera                              retirado t_piel + t_costilla + tol +
#                                        0.5: detras estan la banda y la trasera,
#                                        y delante de un acrilico de +-1.2 no
#                                        puede haber NADA a distancia fija
#                                        (guarda_trasera_dentro)
# El canto INTERIOR va a marco_fondo en los siete: 6 mas alla de la ventana.
#
# LA MUESCA DE LA BRIDA: en la franja de la meseta el marco vive justo donde
# la brida del miembro alto apoya en la cara del anillo, y la brida NO puede
# subirse encima del marco -- a z >= t_anillo + t_placa está la envolvente
# estática del panel superior fijo. Asi que el
# marco lleva una muesca abierta a su canto exterior sobre la huella de la
# brida, de brida_ancho + t_costilla + 0.5 de honda, y la brida se tumba en
# la cara del anillo como siempre.

# Radio de redondeo por vertice, gemelo de radios_perfil() en el .scad. El 0
# (frente-abajo) no lleva radio sino CHAFLAN (chaflan_nariz), que vive en el
# contorno (pts_contorno() en el .scad) y no en pts_perfil(); aqui va None. Los
# SEIS vertices restantes llevan chapa doblada encima -- la nariz en 1, el
# retorno en 4, la banda del miembro alto en 5, la del talon en 6 -- y
# compartian radio_chapa (2026-08-29); el 2 y el 3 tienen los suyos.
#
# DESDE EL 2026-08-30 los que llevan chapa van a radio_borde, que es
# radio_chapa + rehundido_chapa: el contorno del anillo es la cara exterior de
# la chapa desplazada el rehundido hacia fuera, asi que su arco es CONCENTRICO
# con el del pliegue, no el mismo. Es un DERIVADO, y por eso la lista guarda un
# callable y no un nombre de parametro para esos vertices.
RADIOS_PERFIL = [None, _radio_borde, "radio_pico", "radio_valle",
                 _radio_borde, _radio_borde, None]


def _chaflan_p5(p: dict[str, float]) -> bool:
    """El techo con chaflan (variante B, remate_trasero_chaflan = 1): P5 va a
    chaflan como P0 y P6. Con 0, la banda plana de #241 y P5 a radio_chapa."""
    return p["remate_trasero_chaflan"] >= 0.5


def _radios_perfil(p: dict[str, float]) -> list:
    """Radio por vertice con la variante del techo puesta. P6 no lleva radio
    desde la trasera capturada (2026-08-29, noche, 2): va a chaflan como P0 y
    el chaflan vive en el contorno, no en pts_perfil(). GEMELA de
    radios_perfil() en el .scad."""
    r = list(RADIOS_PERFIL)
    if _chaflan_p5(p):
        r[5] = None
    return r


def _retiro_vertice(p: dict[str, float], P: list[tuple[float, float]],
                    i: int) -> float:
    """Cuanto se retira una pata del vertice i, a lo largo de su tramo.

    LA TANGENTE DEL REDONDEO si el vertice es CONVEXO -- ahi el contorno se
    mete hacia dentro y una esquina de pletina apoyada sobre la recta se
    saldria de la silueta -- y CERO si es concavo, porque ahi el redondeo
    aparta el contorno. El perfil se recorre en sentido HORARIO (shoelace
    negativo), asi que convexo es producto vectorial < 0. Quien lo comprueba
    contra el fichero es cuerpos_dentro_del_anillo() en check_dxf."""
    A, V, B = P[(i - 1) % len(P)], P[i], P[(i + 1) % len(P)]
    cruz = (V[0] - A[0]) * (B[1] - V[1]) - (V[1] - A[1]) * (B[0] - V[0])
    r = _radios_perfil(p)[i]
    if not (cruz < 0 and r):
        return 0.0
    # Un vertice con chapa trae su radio como funcion derivada; los otros dos,
    # como nombre de parametro.
    return _tangente(V, A, B, r(p) if callable(r) else p[r])


def _tol_pmma(p: dict[str, float]) -> float:
    """Tolerancia de espesor del PMMA: +-(0.4 + 0.1 x t), Schaeffer AG
    (2026-08-18). Es la cota que manda en todo lo que vive delante o detras de
    una plancha de acrilico, y desde el 2026-10-11 la unica es la trasera: se
    calcula con su t_piel. Fue t_cheek, el de las mejillas, el mismo 8."""
    return 0.4 + 0.1 * p["t_piel"]


def _retiro_marco_pie(p: dict[str, float]) -> float:
    """Lo que el marco se retira de la silueta EN EL SUELO, bajo los pies de la
    nariz y del talon: el espesor de la chapa mas su holgura. Los pies no se
    rehunden -- apoyan a ras en la tabla --, asi que aqui no entra el rehundido.
    GEMELO de retiro_marco_pie()."""
    return p["t_costilla"] + p["hol_piel"]


def _retiro_marco(p: dict[str, float]) -> float:
    """Lo que el canto exterior del marco se retira de la silueta bajo cada
    chapa EMPOTRADA (frente, meseta y la cola bajo el retorno): el rehundido de
    la chapa, su espesor y su holgura. Fue t_costilla + hol_piel = 1.65 hasta el
    2026-08-30; con la chapa 1 mm dentro del rebaje son 2.65.
    GEMELO de retiro_marco_chapa()."""
    return p["rehundido_chapa"] + p["t_costilla"] + p["hol_piel"]


def _retiro_marco_trasera(p: dict[str, float]) -> float:
    """Lo que la pata trasera del marco se retira del plano trasero desde la
    trasera capturada (2026-08-29, noche, 2): el bolsillo de la trasera corre
    por la cara interior del anillo hasta u = t_anillo (labio + ancho del
    bolsillo) y el marco arranca medio milimetro mas alla, sobre la pared
    entre bolsillos. Su canto queda a 2.5 de la cara interior nominal del
    acrilico -- mas que los tol + 0.5 de la regla del postmortem -- y es su
    tope hacia dentro en esa rebanada, como el marco lo es del costado.

    DESDE EL 2026-08-30 no es t_anillo + 0.5 sino la pared del bolsillo + la
    holgura del costado: el bolsillo se corrio 1.5 hacia dentro con la rendija
    (u = 4.5..15.5) y la pata tiene que arrancar detras de EL, no del 14.5 de
    cuando el bolsillo empezaba en 3. Con el 14.5 viejo la pata se quedaba a
    1.00 de la cara interior de la trasera contra los 1.70 de la regla del
    postmortem, y guarda_trasera_capturada() lo caza."""
    return _bolsillo_trasero(p)["u1"] + p["hol_costado"]


def _muesca_brida(p: dict[str, float]) -> tuple[float, float]:
    """(x_min, y_min) de la muesca del marco sobre la brida: todo lo que quede
    a x >= x_min y y >= y_min se corta. x_min es la punta de la brida menos
    el aire; y_min, su canto de abajo menos 0.5."""
    P = _vertices(p)
    x_dob = P[6][0] - p["rehundido_chapa"] - p["t_costilla"]
    # LA HOLGURA ES hol_chapa, NO hol_piel (2026-08-30). El marco se aparta de
    # la BRIDA, y la brida es chapa metida en un cajeado: su holgura es la de
    # la chapa. El gemelo del .scad se cambio a hol_chapa el mismo dia y este
    # se quedo en hol_piel; los dos numeros diferian 0.35 mm y ninguna puerta
    # lo veia, porque taladros_marco_ventana() muestrea lejos de esa frontera.
    return (x_dob - p["brida_largo"] - p["hol_chapa"],
            P[5][1] - p["marco_sup"] - p["brida_ancho"] - p["hol_chapa"])


def _marco_ventana(p: dict[str, float]) -> list[dict]:
    """Las patas del marco, una por tramo del CONTORNO del anillo (ocho: el
    frente-abajo va chaflanado y son dos tramos).

    Cada pata es un dict: nombre, A (punto de arranque), u (unitario a lo
    largo), n (normal hacia dentro, la convencion de _centros_rail), s0/s1 (de
    donde a donde corre), retiro (su canto exterior, medido desde la silueta;
    con escalon donde cambia), fondo, ejes ((s, centro, con_roscas) por riel
    que recoge), poligono (en el plano del perfil, con escalones y muesca) y
    convexos (1-2 rectangulos que suman el poligono, para el SAT de solapes).
    Un punto de la pata es A + u*s + n*b."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    c1u = _centros_rail_1u(p, P, cr)
    c = p["chaflan_nariz"]
    rm, rmt, f = _retiro_marco(p), _retiro_marco_trasera(p), p["marco_fondo"]
    C0, C1 = (c, 0.0), (0.0, c)
    x_mu, y_mu = _muesca_brida(p)

    def rv(i: int) -> float:
        return _retiro_vertice(p, P, i)

    # EN CADA ESQUINA LA PATA ACABA DONDE MANDA LA MAS RETIRADA DE LAS DOS: la
    # tangente del redondeo, como las placas, o el retiro de la pata vecina si
    # es mayor -- la meseta no puede seguir hasta la tangente de P5 porque ahi
    # empieza la franja de la banda y la trasera, y el suelo arranca 11.2
    # detras de P6 por lo mismo. En las dos esquinas del chaflan (r = 0) manda
    # el retiro del vecino a secas.
    def ini(i: int | None, otro: float) -> float:
        return max(rv(i) if i is not None else 0.0, otro)

    def fin(L: float, i: int | None, otro: float) -> float:
        return L - ini(i, otro)

    def pata(nombre, A, B, s0, s1, retiro, ejes_c=(), con=(),
             puntos=None, convexos=None, fondo=None):
        L = math.hypot(B[0] - A[0], B[1] - A[1])
        u = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
        n = (u[1], -u[0])
        fo = f if fondo is None else fondo
        ejes = [((cc[0] - A[0]) * u[0] + (cc[1] - A[1]) * u[1], cc, k)
                for cc, k in zip(ejes_c, con)]
        pts = puntos or [(s0, retiro), (s1, retiro), (s1, fo), (s0, fo)]
        conv = convexos or [pts]
        def m(q):
            return (A[0] + u[0] * q[0] + n[0] * q[1],
                    A[1] + u[1] * q[0] + n[1] * q[1])
        # LOS CANTOS REALES de la pata son los que no estan en s0 ni en s1:
        # el marco es un anillo cerrado y en las esquinas sigue de largo, asi
        # que los dos lados que cierran el poligono ahi son ficticios. Un
        # agujero se mide contra estos, no contra el poligono entero.
        def en_extremo(a, b):
            return abs(a[0] - b[0]) < 1e-9 and (abs(a[0] - s0) < 1e-9
                                                or abs(a[0] - s1) < 1e-9)
        cantos = [(m(pts[i]), m(pts[(i + 1) % len(pts)])) for i in range(len(pts))
                  if not en_extremo(pts[i], pts[(i + 1) % len(pts)])]
        return {"nombre": nombre, "A": A, "u": u, "n": n, "L": L,
                "s0": s0, "s1": s1, "retiro": retiro, "fondo": fo, "ejes": ejes,
                "poligono": [m(q) for q in pts],
                "convexos": [[m(q) for q in cv] for cv in conv],
                "cantos": cantos, "_m": m}

    out = []
    # el chaflan y el frente, bajo la nariz
    out.append(pata("chaflan", C0, C1, ini(None, rm), fin(math.hypot(c, c), None, rm), rm))
    L_fr = math.hypot(P[1][0] - C1[0], P[1][1] - C1[1])
    out.append(pata("frente", C1, P[1], ini(None, rm), fin(L_fr, 1, rm), rm))
    # la cara de abajo: retirada bajo la nariz hasta retiro_placa_inf, y a la
    # silueta de ahi en adelante (el marco de la fila)
    L = math.hypot(P[2][0] - P[1][0], P[2][1] - P[1][1])
    s0, s1 = ini(1, rm), fin(L, 2, 0.0)
    s_esc = rv(1) + p["retiro_placa_inf"]
    out.append(pata("cara_inf", P[1], P[2], s0, s1, 0.0, (cr[0], cr[1]),
                    (True, True),
                    puntos=[(s0, rm), (s_esc, rm), (s_esc, 0.0), (s1, 0.0),
                            (s1, f), (s0, f)],
                    convexos=[[(s0, rm), (s_esc, rm), (s_esc, f), (s0, f)],
                              [(s_esc, 0.0), (s1, 0.0), (s1, f), (s_esc, f)]]))
    out[-1]["escalon"] = s_esc
    # el valle: recoge los dos rieles KONDOR y se pasa de P3 (concavo) hasta
    # cubrir el cajeado del segundo con 1.5 D de canto. El segundo KONDOR NO lleva
    # roscas: radio_valle curva la franja y una broca ahi sale por el rebaje.
    L = math.hypot(P[3][0] - P[2][0], P[3][1] - P[2][1])
    u = ((P[3][0] - P[2][0]) / L, (P[3][1] - P[2][1]) / L)
    s_ejes = [(q[0] - P[2][0]) * u[0] + (q[1] - P[2][1]) * u[1] for q in c1u]
    s1 = max(fin(L, 3, 0.0), max(s_ejes) + 2 * p["d_M4_paso"])
    out.append(pata("valle", P[2], P[3], ini(2, 0.0), s1, 0.0, tuple(c1u),
                    (True, False)))
    # la cara de arriba: a la silueta hasta la cola, retirada bajo el retorno
    L = math.hypot(P[4][0] - P[3][0], P[4][1] - P[3][1])
    s0, s1 = ini(3, 0.0) + p["retiro_placa_sup"], fin(L, 4, rm)
    s_esc = L - (p["retorno_meseta"] + 1.0)
    out.append(pata("cara_sup", P[3], P[4], s0, s1, 0.0, (cr[2], cr[3]),
                    (True, True),
                    puntos=[(s0, 0.0), (s_esc, 0.0), (s_esc, rm), (s1, rm),
                            (s1, f), (s0, f)],
                    convexos=[[(s0, 0.0), (s_esc, 0.0), (s_esc, f), (s0, f)],
                              [(s_esc, rm), (s1, rm), (s1, f), (s_esc, f)]]))
    out[-1]["escalon"] = s_esc
    # la meseta, bajo la chapa, con la muesca de la brida en su extremo trasero
    L = math.hypot(P[5][0] - P[4][0], P[5][1] - P[4][1])
    s0, s1 = ini(4, rm), fin(L, 5, rmt)
    s_mu, b_mu = x_mu - P[4][0], P[5][1] - y_mu
    out.append(pata("meseta", P[4], P[5], s0, s1, rm,
                    puntos=[(s0, rm), (s_mu, rm), (s_mu, b_mu), (s1, b_mu),
                            (s1, f), (s0, f)],
                    convexos=[[(s0, rm), (s_mu, rm), (s_mu, f), (s0, f)],
                              [(s_mu, b_mu), (s1, b_mu), (s1, f), (s_mu, f)]]))
    out[-1]["muesca"] = (s_mu, b_mu)
    # la trasera: retirada de la banda, la trasera y su tolerancia; la muesca
    # de la brida le come la esquina de arriba por fuera
    # LA PATA TRASERA ENTRA marco_fondo_trasera, no marco_fondo (2026-08-29,
    # noche, 2): arranca sobre la pared entre bolsillos (t_anillo + 0.5) y con
    # 26 se quedaba en 11.5 de ancho, a 129 MPa bajo carga_mano contra 130.
    L = math.hypot(P[6][0] - P[5][0], P[6][1] - P[5][1])
    s0, s1 = ini(5, rm), fin(L, 6, rm)
    s_mu, b_mu = P[5][1] - y_mu, P[6][0] - x_mu
    ft = p["marco_fondo_trasera"]
    if b_mu >= ft:
        # la muesca alcanza la pata entera: se lleva la esquina de arriba
        out.append(pata("trasera", P[5], P[6], s_mu, s1, rmt, fondo=ft))
    else:
        out.append(pata("trasera", P[5], P[6], s0, s1, rmt,
                        puntos=[(s_mu, rmt), (s1, rmt), (s1, ft), (s0, ft),
                                (s0, b_mu), (s_mu, b_mu)],
                        convexos=[[(s_mu, rmt), (s1, rmt), (s1, ft), (s_mu, ft)],
                                  [(s0, b_mu), (s_mu, b_mu), (s_mu, ft), (s0, ft)]],
                        fondo=ft))
    out[-1]["muesca"] = (s_mu, min(b_mu, ft))
    # el suelo, bajo los pies de la nariz y del talon, hasta el chaflan
    L = P[6][0] - c
    # EL SUELO NO LLEVA EL RETIRO DE LA CHAPA EMPOTRADA (2026-08-30): encima de
    # el van los PIES de la nariz y del talon, y los pies no se rehunden --
    # apoyan a ras en la tabla, que los tapa. Su retiro sigue siendo t + hol.
    rmp = _retiro_marco_pie(p)
    out.append(pata("suelo", P[6], C0, ini(6, rmt), fin(L, None, rmp), rmp))
    return out


def _pata(p: dict[str, float], nombre: str) -> dict:
    return next(q for q in _marco_ventana(p) if q["nombre"] == nombre)


def _dist_a_cantos(cantos: list[tuple[tuple[float, float], tuple[float, float]]],
                   c: tuple[float, float]) -> float:
    """Distancia del punto al mas cercano de una lista de segmentos."""
    def d_seg(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = (max(0.0, min(1.0, ((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / L2))
             if L2 else 0.0)
        return math.hypot(c[0] - (a[0] + t * dx), c[1] - (a[1] + t * dy))
    return min(d_seg(a, b) for a, b in cantos)


def _roscas_marco(p: dict[str, float]) -> list[tuple[str, tuple[float, float]]]:
    """(nombre, centro) de las dos roscas ciegas que lleva cada riel en su
    pata, a no menos de sep_rosca_riel del eje a lo largo del tramo y a
    dist_rosca_ciega de la silueta; y las dos de la pata del suelo, a
    rosca_suelo_retiro de cada extremo -- el trabajo de las de los clips: sin
    ellas la pata mas larga del marco cedia 3.31 mm bajo carga_mano. Doce por
    anillo. GEMELA de roscas_marco() en el .scad.

    EL PAR NUNCA SE ARRIMA AL RIEL PARA LIBRAR EL EXTREMO DE LA PATA (#242).
    Si cabe, lo abraza a +-sep_rosca_riel. Si una rosca caeria fuera del tramo
    legal, las dos pasan al lado interior del riel: la cercana conserva
    sep_rosca_riel y entre ambas quedan 2 D de paso M4. El marco sigue de largo
    por las esquinas, pero los extremos de las patas de las filas no son
    arbitrarios: el de la cara de arriba en P3 esta a retiro_placa_sup del
    vertice porque ahi el redondeo concavo estrecha la franja y una rosca se
    sale por el rebaje, y el de la cara de abajo en P1 es el escalon bajo la
    nariz. Lo cruza taladros_anillo() contra el rebaje releido del DXF."""
    sep, d = p["sep_rosca_riel"], p["dist_rosca_ciega"]
    canto = 1.6 * p["d_M4_paso"]
    paso_par = 2 * p["d_M4_paso"]
    out = []
    for q in _marco_ventana(p):
        # en la cara de abajo el par se mide desde el ESCALON (donde la pata
        # sale a la silueta, retiro_placa_inf tras P1), no desde la cabeza
        # retirada bajo la nariz: es la misma cota que el .scad usa de arranque
        s_ini = q["escalon"] if q["nombre"] == "cara_inf" else q["s0"]
        lo, hi = s_ini + canto, q["s1"] - canto
        for s_eje, _, con in q["ejes"]:
            if not con:
                continue
            ss = (s_eje - sep, s_eje + sep)
            if ss[0] < lo:
                ss = (s_eje + sep, s_eje + sep + paso_par)
            elif ss[1] > hi:
                ss = (s_eje - sep - paso_par, s_eje - sep)
            for s in ss:
                out.append((f"marco {q['nombre']} {s - s_eje:+.1f}",
                            q["_m"]((s, d))))
    q = _pata(p, "suelo")
    r = p["rosca_suelo_retiro"]
    for i, s in enumerate((q["s0"] + r, q["s1"] - r)):
        out.append((f"marco suelo {i}", q["_m"]((s, d))))
    return out


def bbox_marco_ventana(p: dict[str, float]) -> tuple[float, float]:
    """Envolvente del DXF del marco: la silueta menos los retiros. De la cara
    del frente (retirada bajo la nariz) a la pata trasera (retirada de la
    banda y la trasera), y del suelo (bajo los pies, que no van empotrados) a
    la meseta (bajo su chapa empotrada). Derivada, no escrita a mano: si una
    banda de retiro se mueve, el sobre se mueve con ella y revisar() lo canta.
    Hasta el 2026-10-12 el suelo se retiraba como la meseta y el sobre salia
    1 mm mas bajo que el DXF."""
    P = _vertices(p)
    rm, rmt = _retiro_marco(p), _retiro_marco_trasera(p)
    return (P[6][0] - rmt - rm, P[5][1] - rm - _retiro_marco_pie(p))


def _pasos_riel_marco(p: dict[str, float]) -> list[tuple[str, tuple[float, float]]]:
    """Los seis pasos M4 de riel del marco (con su cajeado por el lado del
    anillo): los cuatro 3U y los dos KONDOR."""
    return [(f"riel de '{q['nombre']}' @ s={e[0]:.1f}", e[1])
            for q in _marco_ventana(p) for e in q["ejes"]]


def _dist_al_poligono(q: list[tuple[float, float]],
                       c: tuple[float, float]) -> float:
    """Distancia del punto al canto mas cercano de un poligono cerrado."""
    def d_seg(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = (max(0.0, min(1.0, ((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / L2))
             if L2 else 0.0)
        return math.hypot(c[0] - (a[0] + t * dx), c[1] - (a[1] + t * dy))
    return min(d_seg(q[i], q[(i + 1) % len(q)]) for i in range(len(q)))



def _cajas_marco(p: dict[str, float], z0: float, z1: float) -> list[Caja]:
    """El marco de la ventana como cuerpos: la AABB de cada pata, pegada a la
    cara interior del anillo, por los dos costados. El solape fino contra lo
    que va girado lo resuelve _solape_riel_exacto() con los convexos reales de
    la pata (una AABB de un tramo a 35 o 45 grados es casi el doble de area, y
    la muesca de la brida no cabe en una caja)."""
    out: list[Caja] = []
    for q in _marco_ventana(p):
        xs, ys = [e[0] for e in q["poligono"]], [e[1] for e in q["poligono"]]
        for lado, (za, zb) in enumerate(((z0, z0 + p["t_placa"]),
                                          (z1 - p["t_placa"], z1))):
            out.append((f"marco {q['nombre']} {lado}", min(xs), max(xs),
                        min(ys), max(ys), za, zb))
    return out


def _raiz_m3(p: dict[str, float]) -> float:
    """Regla de chapa: el M3 no entra en la zona del doblez -- setback mas 2t
    mas el radio del agujero. La misma cuenta que _bridas() con el M4."""
    return p["radio_doblez_costilla"] + 3 * p["t_costilla"] + p["d_M3_paso"] / 2


def _bridas(p: dict[str, float]) -> list[dict]:
    """La brida de extremo del miembro alto: donde vive, sus M4 y su escalon.

    Lengueta de chapa de t_costilla doblada 90 del EXTREMO DE LA BANDA en cada
    punta, sobre una linea PERPENDICULAR a la silueta -- por eso su largo
    corre a lo largo del canto y la distancia al doblez y la distancia a la
    silueta son cotas de ejes distintos; con el doblez paralelo al canto no
    habria agujero legal (9.75 pedido contra 9.05 disponible). Acaba
    t_costilla por debajo de la meseta, que es el otro ala del mismo blank, y
    mide brida_ancho hacia abajo desde ahi.

    APOYA EN LA CARA DEL ANILLO, a z = t_anillo. En esa franja vive el marco
    de la ventana y la brida NO se sube encima: a z >= t_anillo + t_placa esta
    la envolvente estatica del panel superior fijo. Es el marco el que lleva una
    muesca sobre ella (_muesca_brida); la trasera capturada muere por debajo
    de ella, sin muesca. Sus dos M4: el de dentro a la mayor de la raiz del
    doblez (r + 3t + d/2) y de 1.5 D de broca de la pared del bolsillo de la
    trasera (brida_s_in), el de fuera a 1.5 D del canto libre. GEMELA de
    bridas_anillo() y brida_*() en el .scad. El miembro bajo ya no tiene
    brida: es el talon, y va a la tabla."""
    P = _vertices(p)
    t, d = p["t_costilla"], p["d_M4_paso"]
    # LA CARA INTERIOR DEL LABIO, que desde el 2026-08-30 esta rehundida:
    # la brida dobla del labio, y el labio entra rehundido_chapa en el rebaje.
    # Sin el rehundido aqui, sus dos M4 ciegos salian 1 mm fuera de donde el
    # .scad los taladra y check_dxf los daba por ausentes.
    x_dob = P[6][0] - p["rehundido_chapa"] - t
    y1 = P[5][1] - t
    y0 = y1 - p["brida_ancho"]
    raiz = p["radio_doblez_costilla"] + 3 * t + d / 2
    # (Se probo max(raiz, t_anillo + 1.6 D - t) la noche de la trasera
    # capturada, cuando el bolsillo salia por arriba y pasaba bajo la brida.
    # Cerrado, 8.5 por debajo de estas roscas, vuelve a ser la raiz.)
    s_in = raiz
    s_out = p["brida_largo"] - 1.5 * d
    y_m4 = P[5][1] - p["dist_rosca_ciega"]
    x0, x1 = x_dob - p["brida_largo"], x_dob
    # SU ESQUINA DE ARRIBA-ATRAS VA A CHAFLAN con el techo de chaflan (B): la
    # brida apoya en la cara del anillo, y en P5 esa cara esta cortada por
    # u + v = chaflan_nariz. Lo que quede fuera seria brida en el aire.
    c = p["chaflan_nariz"]
    if _chaflan_p5(p) and (P[6][0] - x1) + (P[5][1] - y1) < c:
        k = c - (P[6][0] - x1) - (P[5][1] - y1)      # lo que sobresale, en diagonal
        poligono = [(x0, y0), (x1, y0), (x1, y1 - k), (x1 - k, y1), (x0, y1)]
    else:
        poligono = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [{"nombre": "trasero alto", "x_dob": x_dob,
             "rect": (x0, x1, y0, y1), "poligono": poligono,
             "m4": [(x_dob - s_in, y_m4), (x_dob - s_out, y_m4)],
             "s_m4": (s_in, s_out), "raiz": raiz}]


def _cajas_brida(p: dict[str, float], z0: float, z1: float) -> list[Caja]:
    """Las bridas como cuerpos: t_costilla de espesor DENTRO DEL CAJEADO del
    anillo, por los dos costados.

    Los z0/z1 que recibe son el vano entre caras interiores, que es donde
    vivian hasta el 2026-08-30 -- apoyadas contra la cara. Ya no: la brida es
    el vuelo del techo doblado sobre su canto, asi que arranca donde arranca el
    techo (chapa_z0), 2.5 mm mas afuera. Con los z0/z1 de fuera, esta puerta
    analizaba las colisiones de un cuerpo que no esta donde lo pone el .scad,
    y no las de la brida. Los argumentos se conservan por los llamadores."""
    out: list[Caja] = []
    t = p["t_costilla"]
    z0 = p["t_anillo"] + p["hol_piel"] - _muesca_pie(p)     # = chapa_z0()
    z1 = z0 + _chapa_largo_rebaje(p)
    for b in _bridas(p):
        x0, x1, y0, y1 = b["rect"]
        for lado, (za, zb) in enumerate(((z0, z0 + t), (z1 - t, z1))):
            out.append((f"brida {b['nombre']} {lado}", x0, x1, y0, y1, za, zb))
    return out


def _centros_rosca_ciega(p: dict[str, float]
                          ) -> list[tuple[str, tuple[float, float], float]]:
    """(nombre, centro, diametro de broca) de cada rosca ciega de la cara
    interior del anillo. GEMELA de centros_rosca_ciega() en el .scad; las cruza
    taladros_anillo() releyendo costilla_dorso_2d.dxf.

    CATORCE POR ANILLO desde el 2026-08-29 por la noche, todas M4 y todas a
    dist_rosca_ciega de la silueta: doce del marco de la ventana -- dos por
    riel 3U, dos sobre el primer riel KONDOR y dos en la pata del suelo, que hacen
    el trabajo de las de los clips -- y dos de la brida del miembro alto. Eran
    dieciseis: las dos de la brida del miembro bajo murieron con el, que hoy
    es talon y va a la tabla.

    LO QUE NO ESTA AQUI, y no por olvido: las seis de la TABLA van en el CANTO
    inferior del anillo, no en el dorso, y un DXF de la cara no sabe dibujar
    un taladro que entra por el canto (van en el pliego). Y la de la pestana
    de la banda del valle no es del anillo: se rosca en los 6 mm del marco."""
    out = [(nm, c, p["d_M4_rosca"]) for nm, c in _roscas_marco(p)]
    for b in _bridas(p):
        for i, c in enumerate(b["m4"]):
            out.append((f"brida {b['nombre']} {i}", c, p["d_M4_rosca"]))
    return out


def _distancia_a_silueta(P: list[tuple[float, float]],
                          c: tuple[float, float]) -> float:
    """Distancia del punto al tramo mas cercano de la silueta SIN redondear.

    Es la cota que decide si una rosca ciega cae en la franja. Se mide contra
    el poligono de pts_perfil() y no contra el DXF a proposito: aqui manda el
    modelo, y el DXF lo cruza taladros_anillo() en check_dxf.py."""
    def d_seg(a, b):
        ax, ay = a
        bx, by = b
        px, py = c
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2)) if L2 else 0.0
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    return min(d_seg(P[i], P[(i + 1) % len(P)]) for i in range(len(P)))


def guarda_anclajes(p: dict[str, float]) -> None:
    """Cada anclaje asienta en la franja del anillo, y cada tornillo tiene
    material alrededor en LAS DOS piezas que une.

    La cabeza del M4 del riel va del lado del anillo (el tornillo entra en el
    riel por su eje). La placa mide 6 y no 4 (plan, R1) porque debajo, a
    z < t_anillo, hubo acrilico hasta el 2026-10-11; con la persiana el rebaje
    se queda vacio, y 6 se queda: bajarla mueve los seis rieles y no compra
    nada que se vea.

    Y LA FRANJA MANDA DOS VECES: por fuera la silueta, por dentro la pared del
    rebaje. Una rosca que se acerque a la primera raja el canto vista al
    apretar; una que se acerque a la segunda sale por el rebaje, donde solo
    quedan 3 mm de labio. 1.5 D de broca a cada una.

    LAS COMPROBACIONES DE CANTO SON CUATRO Y DISTINTAS, y hacen falta las
    cuatro. Aqui vivio un rato solo la de la silueta, y con ella en verde el
    cajeado del riel del valle de arriba se quedaba con 0.31 mm de pared: una
    rosca puede estar perfectamente puesta en la franja y el AGUJERO DE PASO de
    la pieza que apoya estar en el aire. Cada tornillo se mide contra el canto
    de SU pieza, con el poligono real de esa pieza."""
    # 2.2 es el alto de la cabeza del boton ISO 7380 M4; lo que el modelo fresa
    # es prof_cajeado_riel, y se LEE del parametro en vez de repetir aqui el
    # 2.5 a mano -- era la segunda copia del mismo numero, y la copia se
    # desincroniza al primer cambio.
    cabeza = 2.2
    assert p["prof_cajeado_riel"] >= cabeza, (
        f"el cajeado mide {p['prof_cajeado_riel']:g} y la cabeza del boton ISO "
        f"7380 M4 mide {cabeza:g} de alto: asomaria por la cara de la placa")
    assert p["t_placa"] - p["prof_cajeado_riel"] >= 3.0, (
        f"la placa de {p['t_placa']:g} con un cajeado de "
        f"{p['prof_cajeado_riel']:g} para la cabeza deja "
        f"{p['t_placa'] - p['prof_cajeado_riel']:.1f} mm bajo ella; hacen "
        f"falta 3. Ruling R1: 6 mm")
    P = _vertices(p)
    franja = p["cara_anillo"] - p["rebaje_anillo"]
    centros = _centros_rosca_ciega(p)
    for nm, c, d in centros:
        dist = _distancia_a_silueta(P, c)
        assert 1.5 * d <= dist <= franja - 1.5 * d, (
            f"la rosca ciega '{nm}' cae a {dist:.2f} de la silueta; la franja va "
            f"de {1.5 * d:.2f} a {franja - 1.5 * d:.2f}")
    # el agujero de PASO de la pieza que apoya tiene su propia regla, y es mas
    # exigente que la de la broca: 1.5 D de 4.5 contra 1.5 D de 3.3
    canto = p["dist_rosca_ciega"] - 1.5 * p["d_M4_paso"]
    assert canto >= 0, (
        f"la rosca va a {p['dist_rosca_ciega']:g} de la silueta y el agujero de "
        f"paso M4 de la placa pide {1.5 * p['d_M4_paso']:.2f} de canto: la placa "
        f"apoya CON su canto en la silueta, no hay mas material que ese")
    minimo = 1.5 * p["d_M4_paso"]
    # CADA AGUJERO DEL MARCO contra el poligono REAL de su pata, escalones y
    # muesca incluidos: los cajeados de los seis rieles, las diez roscas, los
    # dos pasos de la brida (en la meseta) y el M3 de la pestana (en el valle,
    # medido con el paso M3). El poligono de la pata acaba en las esquinas del
    # anillo donde el marco sigue de largo, asi que los extremos son cantos
    # ficticios -- pero ningun agujero vive cerca de una esquina, y contra el
    # escalon de la cara de abajo (bajo la nariz) y la muesca de la brida la
    # distancia SI es real. Es el mismo criterio que taladros_marco_ventana()
    # repite en check_dxf releyendo el fichero.
    peor_eje = (float("inf"), "")
    patas = _marco_ventana(p)
    por_pata = {q["nombre"]: q for q in patas}
    agujeros: list[tuple[str, str, tuple[float, float], float]] = []
    for q in patas:
        agujeros += [(q["nombre"], f"cajeado de riel de '{q['nombre']}'",
                      e[1], minimo) for e in q["ejes"]]
    for nm, c in _roscas_marco(p):
        agujeros.append((nm.split(" ")[1], f"rosca '{nm}'", c, minimo))
    for b in _bridas(p):
        agujeros += [("meseta", f"paso de brida {i}", c, minimo)
                     for i, c in enumerate(b["m4"])]
    agujeros.append(("valle", "M3 de la pestana de la banda", _m3_pestana(p),
                     1.5 * p["d_M3_paso"]))
    for pata_nm, etiqueta, c, min_c in agujeros:
        dist = _dist_a_cantos(por_pata[pata_nm]["cantos"], c)
        peor_eje = min(peor_eje,
                       (dist, f"{etiqueta} @ ({c[0]:.1f}, {c[1]:.1f})"))
        assert dist >= min_c, (
            f"el {etiqueta} en ({c[0]:.2f}, {c[1]:.2f}) cae a {dist:.2f} mm "
            f"del canto de la pata '{pata_nm}' del marco y se exigen "
            f"{min_c:.2f} (1.5 D). Detras de un cajeado de "
            f"{p['d_cajeado_riel']:g} eso deja {dist - p['d_cajeado_riel'] / 2:.2f} "
            f"mm de pared")
    # ACCESO DE MONTAJE (#242). La cabeza boton ISO 7380 M4 (Ø7.6) que fija
    # el marco al anillo tiene que quedar fuera de la seccion del Z-Rail, con
    # 0.5 mm para no diseñar a tangencia. Se comprueba contra el rectangulo real
    # del riel en las coordenadas locales de cada pata, no solo contra su eje.
    cabeza_r, hol_cabeza = 7.6 / 2, 0.5
    cabezas_bajo_riel: list[str] = []
    roscas_cerca_cajeado: list[str] = []
    peor_libre_cabeza = (float("inf"), "")
    peor_borde_cajeado = (float("inf"), "")
    for nm, c in _roscas_marco(p):
        pata_nm = nm.split(" ")[1]
        q = por_pata[pata_nm]
        s = ((c[0] - q["A"][0]) * q["u"][0]
             + (c[1] - q["A"][1]) * q["u"][1])
        n = ((c[0] - q["A"][0]) * q["n"][0]
             + (c[1] - q["A"][1]) * q["n"][1])
        for s_riel, c_riel, _ in q["ejes"]:
            n_riel = ((c_riel[0] - q["A"][0]) * q["n"][0]
                      + (c_riel[1] - q["A"][1]) * q["n"][1])
            ds = max(abs(s - s_riel) - p["rail_er_alto"] / 2, 0.0)
            n0 = n_riel - p["rail_er_eje"]
            n1 = n_riel + p["rail_er_fondo"] - p["rail_er_eje"]
            dn = max(n0 - n, n - n1, 0.0)
            libre = math.hypot(ds, dn) - cabeza_r
            peor_libre_cabeza = min(peor_libre_cabeza, (libre, nm))
            if libre < hol_cabeza - 1e-9:
                cabezas_bajo_riel.append(
                    f"{nm} deja {libre:.2f} mm al riel de s={s_riel:.2f}")

            # El cajeado Ø8 es un canto interior de la pletina: desde su borde
            # hasta el eje del paso M4 se conserva la misma regla de 1.5 D que
            # en el contorno exterior.
            entre_centros = math.hypot(c[0] - c_riel[0], c[1] - c_riel[1])
            al_borde_cajeado = entre_centros - p["d_cajeado_riel"] / 2
            peor_borde_cajeado = min(peor_borde_cajeado,
                                     (al_borde_cajeado, nm))
            if al_borde_cajeado < minimo - 1e-9:
                roscas_cerca_cajeado.append(
                    f"{nm} deja {al_borde_cajeado:.2f} mm al cajeado de "
                    f"s={s_riel:.2f}")
    assert not roscas_cerca_cajeado, (
        f"{len(roscas_cerca_cajeado)} pasos M4 quedan a menos de "
        f"{minimo:.2f} mm (1.5 D) del borde de un cajeado Ø"
        f"{p['d_cajeado_riel']:g}: " + "; ".join(roscas_cerca_cajeado))
    assert not cabezas_bajo_riel, (
        f"{len(cabezas_bajo_riel)} cabezas M4 quedan bajo la huella de un "
        f"Z-Rail (se exigen {hol_cabeza:.2f} mm libres): "
        + "; ".join(cabezas_bajo_riel))
    # LA BRIDA CONTRA SU PROPIO CANTO, que no es la silueta: acaba t_costilla
    # por debajo del canto del anillo -- ahi va la meseta, el otro ala del
    # mismo blank --, asi que su margen real es dist_rosca_ciega - t_costilla.
    # Es el caso que puso esa cota en 8.5. Y contra su ESCALON: el M4 de dentro
    # tiene que caer 2t + r + d/2 mas alla de la tangente, en chapa plana.
    peor_brida = (float("inf"), "")
    for b in _bridas(p):
        x0, x1, y0, y1 = b["rect"]
        q = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for c in b["m4"]:
            dist = _dist_al_poligono(q, c)
            peor_brida = min(peor_brida, (dist, b["nombre"]))
            assert dist >= minimo, (
                f"el M4 de la brida de '{b['nombre']}' en ({c[0]:.2f}, "
                f"{c[1]:.2f}) cae a {dist:.2f} mm del canto de la propia brida "
                f"y se exigen {minimo:.2f}. Ojo: el canto de arriba de la brida "
                f"NO es la silueta -- acaba {p['t_costilla']:g} mm mas aca, "
                f"donde empieza la meseta")
            assert b["x_dob"] - c[0] >= b["raiz"] - 1e-9, (
                f"el M4 de la brida en x={c[0]:.2f} cae a {b['x_dob'] - c[0]:.2f} "
                f"mm del doblez y la regla de chapa pide {b['raiz']:.2f} "
                f"(r + 3t + d/2): esta en el doblez")
    # EL M3 DE LA PESTANA de la banda del valle se rosca en el MARCO y no en
    # el anillo: en la franja no cabe (su M3 cae a pv_a por debajo del plano
    # del valle y la franja solo admite hasta franja - 1.5 D de broca). Contra
    # el canto de su pata va en la lista de arriba.
    m3 = _m3_pestana(p)
    d_m3 = _dist_a_cantos(por_pata["valle"]["cantos"], m3)
    # LA TABLA va al CANTO inferior del anillo y no al dorso: su M5 se centra
    # en los t_anillo de canto y necesita 1.5 D de broca a cada cara.
    assert p["t_anillo"] / 2 >= 1.5 * p["d_M5_rosca"], (
        f"el M5 de la tabla se rosca al medio del CANTO inferior del anillo, o "
        f"sea a {p['t_anillo'] / 2:.2f} mm de cada cara, y una broca de "
        f"{p['d_M5_rosca']:g} pide {1.5 * p['d_M5_rosca']:.2f}: ese canto no da "
        f"para roscarlo sin reventar una cara")
    print(f"anclajes: {len(centros)} roscas ciegas M4 por anillo en la franja "
          f"de {franja:g} (a {p['dist_rosca_ciega']:g} de la silueta, {canto:.2f} "
          f"de sobra de canto); marco de {p['t_placa']:g} con la cabeza dentro")
    print(f"  el agujero del marco mas justo es el {peor_eje[1]} a "
          f"{peor_eje[0]:.2f} del canto; el M4 de brida mas justo, '{peor_brida[1]}' a "
          f"{peor_brida[0]:.2f} (minimo {minimo:.2f}); el M3 de la pestana a "
          f"{d_m3:.2f} del canto de la pata del valle")
    print(f"  acceso #242: la cabeza mas justa, '{peor_libre_cabeza[1]}', deja "
          f"{peor_libre_cabeza[0]:.2f} al Z-Rail (minimo {hol_cabeza:.2f}); "
          f"el paso mas justo, '{peor_borde_cajeado[1]}', queda a "
          f"{peor_borde_cajeado[0]:.2f} del cajeado (minimo {minimo:.2f})")


def canario_acceso_marco(p: dict[str, float]) -> None:
    """El reparto viejo y un cajeado crecido deben disparar las dos puertas."""
    casos = (
        ({"sep_rosca_riel": 7.0, "d_cajeado_riel": 0.0},
         "cabezas M4", "reparto viejo bajo el riel"),
        # EL CAJEADO CRECE HASTA LOS PASOS, y el borde se busca (2026-10-12).
        # Fue sep_rosca_riel escrito a mano, 1.0 y luego 5.0: al juntar las
        # roscas salta antes "cabezas M4" (hoy de 9.3 a 6.0) y por debajo de
        # 3.15 el canto de la pata, asi que el numero se quedaba viejo con cada
        # cambio del techo. d_cajeado_riel no entra en ninguna otra regla, asi
        # que el tope de la busqueda puede ser holgado: crece con la separacion,
        # que es lo que mueve el borde (12.5 con 9.5, 15.6 con 11.5).
        ({"d_cajeado_riel": _borde_rojo(guarda_anclajes, p, "d_cajeado_riel",
                                        p["d_cajeado_riel"],
                                        p["d_cajeado_riel"] + 4 * p["sep_rosca_riel"],
                                        "pasos M4")},
         "pasos M4", "un cajeado crecido hasta los pasos M4"),
    )
    for cambios, clave, que in casos:
        roto = {**p, **cambios}
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                guarda_anclajes(roto)
        except AssertionError as exc:
            assert clave in str(exc), (
                f"el canario de {que} cayo por otra razon: {exc}")
        else:
            raise AssertionError(
                f"el canario de {que} no cayo: guarda_anclajes() ya no protege #242")


def _m3_pestana(p: dict[str, float]) -> tuple[float, float]:
    """Centro del M3 de la pestana de la banda del valle, en el plano del
    perfil. GEMELO del agujero que tapa_valle_2d() dibuja en el desarrollo y
    del que placa_riel() rosca en la placa del valle: x centrado en los 3 D
    finales del vuelo delantero, y a pv_a por debajo de la cara de arriba."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    return (_pv_x(p, _frente_kondor(p, P, cr)), P[3][1] - _pv(p)["a"])


def _caras_miembro(p: dict[str, float], cajas: dict[str, Caja]) -> list[Caja]:
    """Cajas de las caras de chapa del techo y del talon, sin rellenar el
    vacio de cada plegado: labio o banda y meseta del techo; labio, pie y
    pestanas del talon.

    EL RETORNO NO VA desde el 2026-10-12. Su caja nunca entraba en solapes()
    (la filtra _cajas_solidas()), y desde la ficha 6 tapa por delante la cara
    del riel de arriba a proposito: su AABB a 45 pisaria la del riel. Lo que
    hace con el riel y con el panel lo mide guarda_labio_chapas().

    LOS DOS CHAFLANES NO VAN: son tramos a 45 y su AABB pisaria la trasera
    sin tocarla (el de abajo, por la esquina del acrilico que descansa en el
    pie). Su holgura la mide guarda_trasera_capturada() en el plano, con la
    cara interior del chaflan de verdad."""
    t = p["t_costilla"]
    alto, talon = cajas["trasero alto"], cajas["talon"]
    z0, z1 = alto[5], alto[6]
    P = _vertices(p)
    tl = _talon(p)
    x_mes1 = P[6][0] - (p["chaflan_nariz"] if _chaflan_p5(p) else 0.0)
    out = [
        alto,
        # LA MESETA: del pico al plano trasero (A) o al pie del chaflan (B),
        # marco_sup (= t) de espesor
        ("trasero alto meseta", P[4][0], x_mes1, P[5][1] - p["marco_sup"],
         P[5][1], z0, z1),
        talon,
        ("talon pie", tl["x_pie"], tl["x_chaflan"], 0.0, t, tl["z0"], tl["z1"]),
    ]
    for i, zc in enumerate(tl["pestana_z"]):
        out.append((f"talon pestana {i}", tl["pestana_x"] - t, tl["pestana_x"],
                    t, t + p["talon_pestana_alto"],
                    zc - p["talon_pestana_ancho"] / 2,
                    zc + p["talon_pestana_ancho"] / 2))
    return out


def _trasera_au(p: dict[str, float]) -> float:
    """Ancho de la piel trasera: el hueco entre anillos menos su ajuste.

    GEMELA de trasera_au() en sam17_case.scad. La resta estuvo escrita a mano
    en TRES sitios con esta misma forma -- _rejilla_entrada(), _ondas_trasera()
    y guarda_red() -- y en otros dos sin el hol_piel: guarda_chasis(), que la
    usaba dentro de un exige() de verdad, y el mensaje de guarda_piso(). Todas
    eran `ancho_total - 2*t_cheek [- 2*hol_piel]`, la cuenta de cuando las caras
    interiores del case eran el acrilico.

    Al pasar la costilla a anillo las cinco se quedaron 12 mm por encima de la
    pieza real (552.32 contra 540.32) y ninguna lo cantaba, porque solo
    alimentaban areas de ventilacion, margenes de ventana y texto de mensaje.
    Se funden el 2026-08-28: aqui las tres que son la trasera; guarda_chasis()
    lee ancho_util directo y guarda_piso() saca el ancho de la propia caja.

    DESDE LA TRASERA CAPTURADA (2026-08-29, noche, 2) vuelve a medir 552.32,
    y esta vez es verdad: sus puntas viven DENTRO de los anillos, en los
    bolsillos del tramo trasero, a t_anillo - rebaje_anillo + hol_piel de cada
    cara vista. Lo que va entre anillos (nariz, talon, techo) es
    _entre_anillos()."""
    return _trasera(p)["au"]


def _cajas_solidas(p: dict[str, float]) -> tuple[list[Caja], list[Caja],
                                                  list[Fila]]:
    """AABB de los seis Z-Rails, tres miembros y planchas/pieles."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    t_acr = p["t_valle"]
    ancho_total = p["ancho_total"]
    # LAS CARAS INTERNAS DEL CASE son la cara interior del anillo desde el
    # 2026-08-28: el acrilico ya no esta en el apilado -- va dentro de la
    # ventana, a z = rehundido..rehundido + t_cheek -- y todo lo que vive
    # dentro apoya contra el anillo en z = t_anillo. Los rieles, ademas, contra
    # su placa: ver el bucle de abajo.
    #
    # FUE t_cheek + t_costilla mientras el acrilico iba APILADO detras de la
    # chapa (2026-08-26 al 27) y antes solo t_cheek. Las tres versiones dicen
    # lo mismo -- "donde acaba la piel y empieza el hueco" --, y la de hoy es
    # la primera en la que ese plano es UNA sola pieza.
    z0 = p["t_anillo"]
    z1 = ancho_total - p["t_anillo"]

    angs = [p[k] for k in ANGS_CR]
    railes: list[Caja] = []
    # LOS SEIS RIELES SE QUEDAN t_placa CORTOS POR PUNTA desde el 2026-08-28:
    # entre la punta del riel y la cara interior del anillo va la PLACA de
    # anclaje, que es quien lleva los dos M4 a rosca ciega. Sin este termino el
    # riel se dibuja invadiendo la placa y solapes() no lo canta, porque la
    # placa todavia no es un cuerpo del modelo.
    for nm, c, ang in zip(NOMBRES_CR, cr, angs):
        # el riel gira -ang para calzar a ras de la cara, y su AABB no es
        # simetrico porque la seccion no es cuadrada (ver _he_er)
        hx, hy = _he_er(p, ang)
        railes.append((nm, c[0] - hx, c[0] + hx, c[1] - hy, c[1] + hy,
                       z0 + p["t_placa"], z1 - p["t_placa"]))
    miembros = _cajas_miembro(p, P, cr, z0, z1)
    hx_1u, hy_1u = _he_er(p, 90.0)
    for i, c in enumerate(_centros_rail_1u(p, P, cr)):
        # El eje M4 NO esta centrado en el fondo de la seccion. Para el KONDOR
        # horizontal, la cara exterior queda rail_er_eje por encima del eje y
        # la interior a rail_er_fondo - rail_er_eje por debajo. La caja
        # simetrica anterior inventaba 2.4 mm de aire justo en este contacto.
        railes.append((f"fila KONDOR {i}", c[0] - hx_1u, c[0] + hx_1u,
                       c[1] - (p["rail_er_fondo"] - p["rail_er_eje"]),
                       c[1] + p["rail_er_eje"],
                       z0 + p["t_placa"], z1 - p["t_placa"]))
    # LAS DOS BANDAS (miembro alto y talon) son las cajas de los miembros; la
    # meseta, el pie del talon y sus pestanas van aparte como caras, porque un
    # canal ya no existe y la AABB de la L entera seria un hueco enorme que
    # acusaria de chocar al Z-Rail superior fijo.
    railes.extend(miembros.values())
    caras = _caras_miembro(p, miembros)
    railes.extend(c for c in caras
                  if c[0] in ("trasero alto meseta", "talon pie")
                  or c[0].startswith("talon pestana"))
    # EL MARCO DE LA VENTANA Y LA BRIDA SON CUERPOS y van en `railes`, que es
    # la lista que solapes() cruza contra todo. El marco vive en la rebanada
    # t_anillo .. t_anillo + t_placa por los dos costados, donde hasta hoy
    # vivian placas, clips y escuadras; la brida del miembro alto se le sube
    # encima con su escalon, y es aqui donde se decide que no se pisen.
    railes.extend(_cajas_marco(p, z0, z1))
    railes.extend(_cajas_brida(p, z0, z1))
    # EL PIE Y EL FRENTE DE LA NARIZ (2026-08-29): el pie va sobre la tabla,
    # donde viven los clips y el chasis, y aqui es donde se decide si caben.
    railes.extend(_cajas_nariz(p))

    planchas: list[Caja] = []
    filas: list[Fila] = []
    # bandeja_base: LA BASE de chapa (papel del suelo, 2026-10-12), bajo los
    # anillos y a ras de su huella, de y = -t_base a 0. Lo que sigue es la
    # historia de la tabla de nogal que fue esta pieza hasta ese dia.
    #
    # Fue plancha de acrilico DENTRO del case (y = 0 a t_base) desde el
    # 2026-08-17, con los dos largueros montados encima, y su canto delantero
    # valio 8.46 mm de alto de aparato en su ultima vuelta. Luego fue una TABLA
    # DE MADERA MACIZA BAJO EL MARCO (2026-08-27 a 2026-10-12), con su vuelo por
    # los cuatro lados. Ahora es la BASE de chapa: ocupa y = -t_base .. 0, a ras
    # de la huella del cuerpo, y su cara de arriba ES el suelo interior.
    # Es la misma pieza que el "zocalo" de la spec 9, que hasta hoy eran dos.
    #
    # LO QUE ESO DESHACE, y por eso el modelo se simplifica en vez de crecer:
    #   - No hay voladizo. La plancha volaba 271.45 mm desde `base trasera` y
    #     pedia 10 mm de aluminio. Ahora las dos costillas se apoyan ENCIMA de
    #     la base y las cuatro paticas van debajo, casi en la misma vertical:
    #     el peso del case va de costilla a pata sin cruzar el vano.
    #   - No hay fila de M3 a un larguero. La base no cuelga de nada; el marco
    #     se le apoya. Su fijacion es a las dos costillas, con seis M5 de paso
    #     redondo, que es cosa de guarda_bandeja_base() y no de apoyo().
    #   - alto_frontal se suelta del espesor del suelo: el riel del frente solo
    #     tiene que librar y=0.
    planchas.append(("bandeja_base",
                     p["chaflan_nariz"], fondo(p) - p["chaflan_nariz"],
                     -p["t_base"], 0.0,
                     0.0, p["ancho_total"]))
    # bandeja_entrepiso MURIO el 2026-08-21 ("vamos a evitar la complejidad").
    # Era el piso del piso de arriba, y su papel de barrera entre la fuente y
    # los modulos ya lo hace el chasis de ACERO (#107): la red y el toroide
    # viven dentro de una caja metalica a tierra, no detras de una plancha de
    # acrilico. Lo que si se fue con ella son sus 3 pasacables de 40 x 12 -- el
    # cable entre pisos se queda sin paso definido, y eso es del #103.
    #
    # Y NO SE QUEDA NINGUNO DE SUS DOS LARGUEROS. El trasero se fue el
    # 2026-08-21 con los otros dos de en medio -- ya solo daba una fila de
    # tornillo de la trasera, y esa fila no compra rigidez que la propia
    # plancha de 8 no de ya. El delantero aguanto hasta el 2026-08-25: era el
    # unico larguero del case sin plancha encima, o sea el unico que ninguna
    # puerta de anclaje miraba, y su papel -- atar los costados a media altura
    # -- ya lo hace el del valle a la MISMA altura. Lo que costo lo midio
    # guarda_costado(), en check_dxf.py, mientras hubo mejilla (hasta el
    # 2026-10-11).
    # tapa_valle: solo la banda lisa del vuelo delantero, a ras del plano
    # del valle. Las diez M3 al canto de las alas murieron con el resto de la
    # plancha; quedan unicamente las dos pestanas atornilladas a las costillas.
    # LA BANDA MUERE CONTRA LAS PLACAS, no contra el anillo, desde el
    # 2026-08-28: mide ancho_util - 2*t_placa igual que los rieles, y en los 6
    # mm que deja libres a cada punta esta el canto de la placa del valle --
    # que es lo que se ve desde arriba, a ras del plano del valle. Su pestana
    # ya no busca una rosca ciega en la franja (no cabia: pv_a = 13.7 contra
    # los 10.25 que admite) sino un M3 roscado EN la placa, igual que las
    # lenguetas de la bahia (ruling R3).
    z0_tv, z1_tv = z0 + p["t_placa"], z1 - p["t_placa"]
    x0_tv, _ = _x_valle(p, P, cr)
    # La chapa de 3 mm se prolonga 2 mm ENTERA sobre el primer KONDOR. Entre su
    # dorso y la cara del riel queda el gap que ocupa la tira anti-ruido.
    x1_tv = _frente_kondor(p, P, cr)
    x2_tv = x1_tv + p["apoyo_valle"]
    planchas.append(("tapa_valle", x0_tv, x2_tv,
                     P[3][1] - t_acr, P[3][1], z0_tv, z1_tv))
    y_rail = P[3][1] - p["rehundido_panel"] - p["t_panel"]
    calce = p["tira_valle_nominal"] - p["compresion_tira_valle"]
    # Con las pestanas terminando en la cara del riel, el calce vuelve a cubrir
    # todo el ancho util sin muescas destinadas a movimiento.
    planchas.append(("tira anti-ruido valle", x1_tv, x2_tv,
                     y_rail, y_rail + calce,
                     z0_tv, z1_tv))
    # LAS DOS PESTANAS de la tapa, dobladas hacia abajo contra la costilla.
    # Van en `railes` y no en `planchas` a proposito: es la lista que solapes()
    # cruza contra todo, y una pestana que se echa encima del larguero del valle
    # o del riel de abajo no la caza nadie mas. (Y `planchas` la recorre
    # _sobres() para sacar envolventes de DXF, que aqui no aplica.)
    # Las pestanas terminan en la cara del primer KONDOR. No se retrasan para
    # acomodar un barrido: los paneles son fijos y se desmontan por tornillos.
    x1_pv = _frente_kondor(p, P, cr)
    x0_pv = x1_pv - 3 * p["d_M3_paso"]
    pv_x = _pv_x(p, x1_pv)
    radio_m3 = p["d_M3_paso"] / 2
    assert x0_pv <= pv_x - radio_m3 and pv_x + radio_m3 <= x1_pv, (
        f"el M3 de la pestana cae en x={pv_x:.2f}, fuera de la pestana "
        f"acortada [{x0_pv:.2f}, {x1_pv:.2f}]: el agujero pide "
        f"{radio_m3:.2f} mm de radio")
    for lado, (za, zb) in enumerate(((z0_tv, z0_tv + p["t_valle"]),
                                     (z1_tv - p["t_valle"], z1_tv))):
        railes.append((f"pestana valle {lado}", x0_pv, x1_pv,
                       P[3][1] - p["pestana_valle"], P[3][1] - t_acr,
                       za, zb))
    # LAS DOS PERSIANAS (2026-10-11): por fuera de los anillos, de la tabla
    # (suelo_persiana por encima) a la silueta. Van en `railes` por lo mismo que
    # las pestanas: solapes() las cruza contra todo y _sobres() no les busca un
    # DXF con su nombre (los suyos son los tres persiana_*). Los tacos no van
    # en caja: viven en sus bolsillos y los mira guarda_tacos_persiana().
    x_fin = max(v[0] for v in P)
    y_fin = max(v[1] for v in P)
    for nombre, za, zb in (("persiana izquierda", -p["t_persiana"], 0.0),
                           ("persiana derecha", ancho_total,
                            ancho_total + p["t_persiana"])):
        railes.append((nombre, 0.0, x_fin, p["suelo_persiana"], y_fin, za, zb))
    # piel_trasera: UNA sola plancha desde el 2026-08-21. Fueron dos, partidas
    # a la altura del entrepiso porque cada una se atornillaba a los dos
    # largueros de su piso; muerta esa bandeja la frontera dejo de existir. Va
    # en t_piel (8).
    #
    # CAPTURADA COMO LAS MEJILLAS desde el 2026-08-29 por la noche (2): sus
    # puntas dentro de los bolsillos del tramo trasero de los anillos (z de
    # t_anillo - rebaje + hol_piel a su espejo), su cara vista rehundida labio
    # + junta del plano trasero, el canto de abajo sobre el pie del talon y el
    # de arriba bajo el techo. SIN FILAS: no la atraviesa nada. Una caja, no
    # tres: las muescas de esquina murieron con los M3 (la brida del techo
    # queda 5 mm por encima de su canto). Ver guarda_trasera_capturada().
    tr = _trasera(p)
    planchas.append(("piel_trasera", tr["x0"], tr["x1"], tr["y0"], tr["y1"],
                     tr["z0"], tr["z1"]))
    return railes, planchas, filas


def _overlap(a: Caja, b: Caja) -> tuple[float, float, float] | None:
    ax0, ax1, ay0, ay1, az0, az1 = a[1:]
    bx0, bx1, by0, by1, bz0, bz1 = b[1:]
    ox = min(ax1, bx1) - max(ax0, bx0)
    oy = min(ay1, by1) - max(ay0, by0)
    oz = min(az1, bz1) - max(az0, bz0)
    return (ox, oy, oz) if (ox > 1e-9 and oy > 1e-9 and oz > 1e-9) else None


def _sat_convexo(a: list[tuple[float, float]],
                 b: list[tuple[float, float]]) -> bool:
    """Solape estricto de dos poligonos convexos mediante ejes separadores."""
    for pol in (a, b):
        for p0, p1 in zip(pol, pol[1:] + pol[:1]):
            eje = (-(p1[1] - p0[1]), p1[0] - p0[0])
            pa = [x * eje[0] + y * eje[1] for x, y in a]
            pb = [x * eje[0] + y * eje[1] for x, y in b]
            if max(pa) <= min(pb) or max(pb) <= min(pa):
                return False
    return True


def _rect_xy(c: Caja) -> list[tuple[float, float]]:
    return [(c[1], c[3]), (c[2], c[3]), (c[2], c[4]), (c[1], c[4])]


def _solape_riel_exacto(p: dict[str, float], a: Caja, b: Caja) -> bool:
    """Refina contra la geometria real los cuerpos que van GIRADOS con su cara.

    Un rectangulo girado 35 o 45 grados tiene una caja de casi el doble de
    area, y en el rincon del valle -- donde en 60 mm conviven dos rieles, la
    banda, su pestana, un ala de la bahia y dos placas -- esa caja acusa de
    chocar a piezas que ni se rozan. Se refina lo que va girado: los Z-Rails
    inclinados (que ya se refinaban contra la pestana) y, desde el 2026-08-28,
    LAS PLACAS DE ANCLAJE, que son rectangulos girados con su tramo y ademas
    con las dos esquinas hondas cortadas.

    No es aflojar la puerta: es medir la pieza en vez de su envolvente. Lo que
    se afloja es la caja, no el criterio -- un solape real sigue en rojo.
    La muesca de la pestana usa la misma cota que tapa_valle_2d()."""
    inclinados = set(NOMBRES_CR)
    hay_inclinado = a[0] in inclinados or b[0] in inclinados
    hay_pestana = (a[0].startswith("pestana valle")
                   or b[0].startswith("pestana valle"))
    hay_marco = a[0].startswith("marco ") or b[0].startswith("marco ")
    if not ((hay_inclinado and hay_pestana) or hay_marco):
        return True
    P = _vertices(p)
    cr = _centros_rail(p, P)
    datos = {nm: (c, p[ang])
             for nm, c, ang in zip(NOMBRES_CR, cr, ANGS_CR)}
    # las cajas llevan el lado en el nombre ("marco valle 0"); la geometria
    # es la misma para los dos, asi que se busca por el nombre sin lado. Cada
    # pata pasa sus CONVEXOS reales: con escalon y muesca, no su caja.
    patas = {f"marco {q['nombre']}": q for q in _marco_ventana(p)}

    def poligonos(c: Caja) -> list[list[tuple[float, float]]]:
        raiz = c[0].rsplit(" ", 1)[0]
        if raiz in patas:
            return patas[raiz]["convexos"]
        if c[0] in datos:
            centro, ang = datos[c[0]]
            q = _esquinas_er(p, centro, ang)
            return [[q[i] for i in (0, 1, 3, 2)]]
        if c[0].startswith("pestana valle"):
            m = p["muesca_riel_valle"]
            # Rectangulo menos el alivio estatico, como dos convexos.
            return [[(c[1] + m, c[3]), (c[2], c[3]),
                     (c[2], c[4]), (c[1] + m, c[4])],
                    [(c[1], c[3] + m), (c[1] + m, c[3] + m),
                     (c[1] + m, c[4]), (c[1], c[4])]]
        return [_rect_xy(c)]

    return any(_sat_convexo(pa, pb)
               for pa in poligonos(a) for pb in poligonos(b))


# Pares tolerados: ronda de revision 1 dejo 2 aqui (bandeja_entrepiso vs
# piel_superior, y el par de railes tilted del quiebre P2-P3). Ronda 2 los
# resuelve los dos de verdad (R6 reancla piel_superior a la repisa en vez
# de entrepiso trasero; R7 abre paso_horizontal 20->25 y separa los railes
# — ver guarda_escalon() mas abajo, que hace el chequeo SAT exacto de ESE
# par como assert duro, no como tolerancia). Vacio a proposito: si un solape
# nuevo aparece y de verdad no se puede resolver sin tocar centros_rail()
# fuera de las reglas autorizadas, se documenta aqui igual que antes.
TOLERADOS: dict[frozenset[str], float] = {
    # El retorno y el miembro alto van girados 45 y comparten una arista sin
    # penetrarse; sus AABB se pisan aunque los solidos fijos solo se tocan.
    # El solape de caja vale 10.18 mm con la seccion de hoy (marco_sup 8 x
    # prof_sup 16 girados 45); 12 deja aire para el ruido y sigue siendo un
    # numero, no un cheque en blanco.
    frozenset({"cara_sup remate", "trasero alto"}): 12.0,
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
    # SIN ESQUELETO desde la trasera capturada (2026-08-29, noche, 2): no
    # queda ninguna fila que apoye en un miembro. La puerta se queda por si
    # vuelve una, y hoy revisa cero filas.
    esqueleto: dict[tuple[str, str], tuple[float, float]] = {}
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
        clave = (rail_decl, fila)
        assert clave in esqueleto, (
            f"fila [{placa}/{fila}] declara el rail '{rail_decl}', que no "
            f"existe ni en el esqueleto ni en los railes de panel")
        d = _desvio(coord, eje, esqueleto[clave])
        peor = max(peor, abs(d))
        if abs(d) > TOL_ALINEACION:
            candidatos = [(f"{nm}/{fi}", c) for (nm, fi), c in esqueleto.items()]
            d_cerca, nm_cerca = _mas_cercano(coord, eje, candidatos)
            fallos.append(
                f"anclaje [{placa}] fila {fila} ({eje}={coord:.2f}): {d:+.2f} mm "
                f"de la centerline de '{rail_decl}' (tolerancia "
                f"{TOL_ALINEACION:.2f} mm) — la placa no apoya donde dice; el "
                f"rail mas cercano es '{nm_cerca}' a {d_cerca:+.2f} mm")
    print(f"alineacion: {len(filas)} filas de agujeros revisadas, desvio "
          f"maximo {peor:.2f} mm (tolerancia {TOL_ALINEACION:.2f})")
    return fallos


def apoyo(p: dict[str, float]) -> list[str]:
    """ANCLAJE, el otro eje: las filas de una misma placa tienen que apoyar a
    la MISMA distancia de la cara de su larguero.

    alineacion() verifica que cada fila caiga en la centerline de su rail, y lo
    hace sobre el eje que RECORRE la placa. El eje perpendicular -- lo que
    separa la placa de la cara del larguero donde se apoya -- no lo miraba
    nadie, y por ahi se colo esto: piel_inferior declara su fila de abajo
    contra "base trasera", un larguero que vive 14 mm mas adelante que los
    otros tres traseros (lleva un - radio_perfil que los demas no llevan). La
    altura casa al micron y la profundidad no, asi que esa fila pide un
    separador de 19 mm mientras el BOM lista los doce de 5.

    Lo que se exige NO es una distancia concreta -- cuanto vale el separador lo
    decide el diseno -- sino que las filas de una misma placa COINCIDAN: el
    separador de una placa es uno solo, y si dos filas apoyan a distancias
    distintas hay una que no apoya. Con una sola fila no hay nada que comparar.
    """
    P = _vertices(p)
    cr = _centros_rail(p, P)
    esqueleto = _cajas_miembro(p, P, cr, 0.0, 0.0)
    _, planchas, filas = _cajas_solidas(p)
    cajas = {c[0]: c[1:] for c in planchas}
    fallos: list[str] = []
    por_placa: dict[str, list[tuple[str, float]]] = {}
    for placa, fila, eje, _coord, rail_decl in filas:
        miembro = esqueleto.get(rail_decl)
        if miembro is None or placa not in cajas:
            continue                       # de eso ya se queja alineacion()
        sup = "y" if eje == "x" else "x"
        x0, x1, y0, y1, _z0, _z1 = cajas[placa]
        lo, hi = (x0, x1) if sup == "x" else (y0, y1)
        mlo, mhi = ((miembro[1], miembro[2]) if sup == "x"
                    else (miembro[3], miembro[4]))
        hueco = lo - mhi if lo >= mhi else mlo - hi
        por_placa.setdefault(placa, []).append((fila, hueco))
    for placa, filas_placa in sorted(por_placa.items()):
        if len(filas_placa) < 2:
            continue
        huecos = [h for _, h in filas_placa]
        if max(huecos) - min(huecos) > TOL_ALINEACION:
            detalle = ", ".join(f"{nm} a {h:.2f}" for nm, h in filas_placa)
            fallos.append(
                f"apoyo [{placa}]: sus filas apoyan a distancias distintas de "
                f"la cara de su larguero ({detalle} mm). El separador de una "
                f"placa es UNO, asi que la que se sale no apoya en nada: o el "
                f"larguero se mueve, o esa fila declara otro")
    print(f"apoyo: {len(por_placa)} placas revisadas, "
          f"{sum(len(v) for v in por_placa.values())} filas")
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
    # SIN FILAS REALES desde la trasera capturada (2026-08-29, noche, 2): el
    # canario prueba el checker sobre dos anclajes sinteticos -- el centro del
    # labio del talon y el del techo -- que es lo unico que necesita: un punto
    # y un desvio.
    P = _vertices(p)
    cr = _centros_rail(p, P)
    cajas = _cajas_miembro(p, P, cr, 0.0, 0.0)
    esqueleto = {(nm, fila): ((c[1] + c[2]) / 2, (c[3] + c[4]) / 2)
                 for (nm, fila), c in ((("talon", "base"), cajas["talon"]),
                                       (("trasero alto", "remate"),
                                        cajas["trasero alto"]))}
    casos = (("talon", "base", "y"),
             ("trasero alto", "remate", "y"))
    for rail_decl, fila, eje in casos:
        anclaje = esqueleto[(rail_decl, fila)]
        centro = anclaje[0 if eje == "x" else 1]
        # los dos primeros son la magnitud del bloqueante real de la bandeja
        # base; el tercero comprueba que el umbral no este dormido
        for delta in (18.0, -24.0, TOL_ALINEACION * 2):
            d = _desvio(centro + delta, eje, anclaje)
            assert abs(d - delta) < 0.01, (
                f"canario de alineacion: el desvio esta MAL MEDIDO -- fila a "
                f"{delta:+.2f} mm de '{rail_decl}' sobre el eje {eje} y el "
                f"checker devuelve {d:+.3f}")
            assert abs(d) > TOL_ALINEACION, (
                f"canario de alineacion no disparo: fila a {delta:+.2f} mm de "
                f"'{rail_decl}' y la tolerancia vigente es {TOL_ALINEACION} mm "
                f"— no confiar en el VERDE de alineacion()")
        d0 = _desvio(centro, eje, anclaje)
        assert abs(d0) <= TOL_ALINEACION, (
            f"canario de alineacion: FALSO POSITIVO -- una fila puesta justo "
            f"en la centerline de '{rail_decl}' sale a {d0:+.3f} mm")


def _misma_chapa(na: str, nb: str) -> bool:
    """Una brida y el miembro del que se dobla son LA MISMA pieza.

    Mismo caso que suelo y alas de la bahia: se cruzan en el doblez porque
    salen del mismo blank. Lo que si tiene que seguir mirandose es la brida
    contra TODO lo demas -- ahi esta el valor -- y contra la brida de enfrente.
    """
    # las ocho patas del marco son UNA pletina: se tocan en las esquinas
    if na.startswith("marco ") and nb.startswith("marco ")             and na.rsplit(" ", 1)[1] == nb.rsplit(" ", 1)[1]:
        return True
    # la banda y la meseta del miembro alto, la banda y el pie del talon: la
    # misma chapa, que se cruza en su propio doblez
    if na.startswith(nb + " ") or nb.startswith(na + " "):
        return True
    for x, y in ((na, nb), (nb, na)):
        if not x.startswith("brida "):
            continue
        duena = x[len("brida "):].rsplit(" ", 1)[0]
        if duena.endswith(" escalon"):
            duena = duena[:-len(" escalon")]
        if y == duena or y.startswith(duena + " "):
            return True
        # el escalon y el tramo plano son la misma lengueta
        if y.startswith("brida ") and y[len("brida "):].rsplit(" ", 1)[0] \
                .replace(" escalon", "") == duena:
            return True
    return False


def solapes(p: dict[str, float]) -> list[str]:
    """Seis rieles, tres miembros, tres placas, ocho bridas, dos pestanas y
    tres planchas: ningun par se pisa en 3D, salvo los
    TOLERADOS de arriba (impresos igual, nunca silenciados) — vacio ahora
    mismo. Paneles inclinados (1.6 mm, PCB de aluminio de cada modulo): su
    clase la resuelve la rotacion de railes (R3), no entran en esta caja."""
    railes, planchas, _ = _cajas_solidas(p)
    # Las dos persianas tienen que estar entre las cajas que se cruzan. Lo
    # probaba canario_persiana_tabla(), hasta que la base dejo de pasar bajo
    # la persiana (papel del suelo, 2026-10-12).
    assert {"persiana izquierda", "persiana derecha"} <= {c[0] for c in railes}, (
        "las dos persianas no estan entre las cajas que solapes() cruza")
    fallos: list[str] = []
    todas = railes + planchas
    n_rail = len(railes)
    for i in range(len(todas)):
        for j in range(i + 1, len(todas)):
            a, b = todas[i], todas[j]
            if _misma_chapa(a[0], b[0]):
                continue
            # pie y frente de la nariz son la misma chapa doblada
            if a[0].startswith("nariz ") and b[0].startswith("nariz "):
                continue
            ov = _overlap(a, b)
            if not ov:
                continue
            if not _solape_riel_exacto(p, a, b):
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
    # Z EN EL PLANO DEL ANILLO, no en el de la mejilla. Las dos cajas iban de
    # t_cheek a ancho_total - t_cheek, que era donde acababa el hueco util
    # cuando el costado de acrilico era la pieza portante. Desde el 2026-08-28
    # el que cierra por los lados es el ANILLO, y el hueco va de t_anillo a
    # ancho_total - t_anillo: es lo que usa _cajas_solidas() para las cajas de
    # verdad. Aqui las dos comparten plano, asi que el canario disparaba igual;
    # lo que no puede quedarse es una cota de una pieza que ya no manda, porque
    # el dia que una de las dos cajas se derive del modelo real dejarian de
    # estar en el mismo sitio y el canario se apagaria en silencio.
    z0, z1 = p["t_anillo"], p["ancho_total"] - p["t_anillo"]
    vecino = ("cara_sup valle", c[0] - hx, c[0] + hx, c[1] - hy, c[1] + hy,
              z0, z1)
    viejo = ("entrepiso delantero VIEJO",
             old_ed[0] - r, old_ed[0] + r, old_ed[1] - r, old_ed[1] + r,
             z0, z1)
    ov = _overlap(viejo, vecino)
    assert ov is not None, (
        "canario de solapes no disparo: el checker no detecta un choque "
        "conocido (6.92 x 9.40 mm en planta) — no confiar en el resto de "
        "solapes()")


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


def guarda_parametros_vivos(p: dict[str, float]) -> None:
    """Ningun parametro promete una capacidad que el codigo no tiene.

    n_bulkheads dice '2 (3 si el vano flexa)' y la spec §11 lo remata: 'si el
    prototipo flexa, n_bulkheads pasa a 3 y se re-exporta'. Pero costillas()
    dibuja DOS anillos fijos -- uno en z = 0 y su espejo en ancho_total -- y
    persianas() las dos de fuera, sin ningun bucle sobre este parametro. Quien
    lo suba a 3 esperando un refuerzo central no recibe nada: ni anillo, ni
    error, ni aviso. El .scad sigue sacando dos, y los DXF salen identicos.

    EL SUJETO CAMBIO DOS VECES. Hasta el 2026-08-28 el costado portante era el
    acrilico, y la puerta nombraba costados(); desde entonces el que cierra por
    los lados es el ANILLO, y el 2026-10-11 las mejillas de acrilico se fueron
    con la persiana. El tabique central seria un tercer anillo: la persiana es
    una tapa de fuera y no tiene gemela en el centro.

    Eso es lo que hace peligroso al parametro muerto -- no que no haga nada,
    sino que PARECE que hace algo. Asi que en vez de borrarlo y perder la
    intencion documentada, la puerta convierte el silencio en un fallo: quien lo
    toque se entera de que hay codigo que escribir.

    Issue #54. Su hermano alto_pie ya se resolvio solo -- cuando entraron las
    paticas dejo de estar huerfano."""
    assert p["n_bulkheads"] == 2, (
        f"n_bulkheads = {p['n_bulkheads']}, y costillas() solo sabe dibujar 2. "
        f"El tercer anillo central NO esta implementado: subir este numero no "
        f"anade nada, solo lo parece. Para que sirva hay que tocar costillas() "
        f"en sam17_case.scad, y de paso decidir como cruzan los largueros por "
        f"el (hoy van de punta a punta) y que agujeros lleva ese anillo.")


# guarda_standoff() vivio aqui hasta el 2026-08-21. Comprobaba que gap_sombra
# -- que ERA el largo de los doce separadores de las pieles -- estuviera en
# catalogo, para no mandar tornear doce piezas. Murio con su sujeto: al
# empotrar las pieles contra la cara de los largueros no hay separador que
# comprar, y LARGOS_STANDOFF se fue con ella. Lo que aquella guarda no miraba
# -- si las dos filas de una piel apoyan a la MISMA distancia -- lo mira ahora
# apoyo(), y es justo por ahi por donde se colaba el fallo real.


def _area_ranuras(n: int, largo: float, ancho: float) -> float:
    """Area abierta de n ranuras de extremos redondos: el rectangulo central
    mas el circulo que forman las dos puntas juntas."""
    return n * ((largo - ancho) * ancho + math.pi * (ancho / 2) ** 2)


def _rejilla_valle(p: dict[str, float]) -> tuple[int, float, float, float]:
    """La rejilla de SALIDA de la MESETA, gemela de miembro_alto_2d().

    Conserva el nombre historico porque guarda_aire() lleva llamandola asi
    desde que la salida estaba en tapa_valle_2d(). Devuelve tambien el
    centroide en Y: mover la misma area de y~145 a y~253 cambia el tiro, y
    contar solo milimetros cuadrados falsearia justo el efecto buscado."""
    P = _vertices(p)
    largo = p["meseta_largo_ranura"]
    paso = int(p["meseta_paso_hp"])
    n_hp = round(p["largo_riel"] / p["hp"])
    ns = len(range(paso, int(n_hp) - paso + 1, paso))
    area = _area_ranuras(ns, largo, p["vent_ancho_ranura"])
    y = P[5][1] - p["marco_sup"] / 2
    return ns, largo, area, y


def _banda_libre_trasera(p: dict[str, float]) -> tuple[float, float]:
    """La banda de la trasera entre la fila de M3 de abajo y la onda de encima.

    La comparten la rejilla de entrada de aire y la ventana de la entrada de
    red, y por eso se calcula UNA vez. El .scad dice lo mismo con las mismas
    palabras en piel_trasera_2d(): si cada uno la rederivara, bastaria tocar
    vent_separacion para que los dos campos se movieran por separado.

    El termino vent_ancho_ranura/2 no es decorativo: la onda es un hull de
    circulos y su borde de MATERIAL cae medio ancho de ranura por debajo de su
    polilinea. La primera version se lo olvido y los 14 mm de vent_separacion
    salieron 12."""
    # ANCLADA AL CAMPO VISIBLE desde la trasera capturada (2026-08-29, noche,
    # 2): de la coronacion del labio del talon a la del techo. Fueron las dos
    # filas de M3, que ya no existen.
    f_base, f_tras = _trasera_campo(p)
    y_bajas = f_base + 0.37 * (f_tras - f_base)
    # SIN ESPINA: la fila de M3 que la rejilla tenia que librar murio con la
    # trasera capturada, y la rejilla arranca a un puente de la coronacion del
    # labio del talon.
    y0 = f_base + p["vent_puente_min"]
    y1 = (y_bajas - p["vent_periodo"] * 0.35 - p["vent_ancho_ranura"] / 2
          - p["vent_separacion"])
    return y0, y1


def _columnas_rejilla_entrada(
        p: dict[str, float]) -> tuple[list[float], float, float]:
    """Las columnas de la rejilla de entrada QUE DE VERDAD SE CORTAN: (xs, y0, y1).

    Mismas cuentas que rejilla_entrada() en el .scad, y la unica lista de esas
    columnas que hay en este guion.

    EXISTE PORQUE LA REGLA ESTABA EN TRES SITIOS Y UNO DE ELLOS LA TENIA A
    MEDIAS. Que columnas se cortan lo deciden DOS filtros -- apartarse de la
    ventana de la entrada de red, y saltarse las que el ala A de la escuadra
    tapa desde el 2026-08-28 --, y hasta hoy estaban escritos enteros en el
    .scad, enteros aqui, y en guarda_red() solo el primero. Consecuencia: el
    margen "contra la ranura mas cercana" que guarda_red() imprime se media
    contra una columna que el DXF ya no corta, o sea contra una ranura que no
    existe. Con una sola lista los dos consumidores ven las mismas ranuras.

    La copia del .scad sigue siendo copia -- son dos lenguajes --, y quien
    comprueba que hizo lo mismo es check_dxf.py releyendo el DXF exportado."""
    au = _trasera_au(p)
    # La banda sale de _banda_libre_trasera(), que es la unica que la calcula.
    # Estuvo copiada aqui y en _ondas_trasera(); ahora tambien la lee la ventana
    # de la entrada de red, o sea tres consumidores de la misma cuenta.
    y0, y1 = _banda_libre_trasera(p)
    paso = int(p["valle_paso_hp"])
    n_hp = round(p["largo_riel"] / p["hp"])
    # La tercera copia del mismo numero. Estuvo como "au - 70 + 24" con el 48
    # escrito a mano al lado -- el .scad lo tenia dos veces mas. Ahora sale de
    # params.scad, que es de donde tiene que salir para que el dia que la pieza
    # de red se elija no haya que acordarse de tres sitios.
    x_iec = au - p["iec_margen_der"] - p["iec_ancho"] / 2
    hueco = (p["iec_ancho"] + p["vent_ancho_ranura"]) / 2 + p["vent_puente_min"]
    # LAS COLUMNAS QUE TAPABA EL ALA A DE LA ESCUADRA se saltaron del 28-08 al
    # 29-08 por la noche; la escuadra murio con el marco de la ventana y la
    # rejilla vuelve a cortar todas las que libran la ventana de red.
    xs = [n * p["hp"] for n in range(paso, int(n_hp) - paso + 1, paso)
          if abs(n * p["hp"] - x_iec) >= hueco]
    return (xs, y0, y1)


def _rejilla_entrada(p: dict[str, float]) -> tuple[int, float, float, float]:
    """Cuanta entrada de aire hay y a que altura: (n, largo, area, y).

    Le pone largo y area a las columnas que devuelve
    _columnas_rejilla_entrada(). El centroide va en coordenadas del case porque
    lo que gobierna el tiro no es solo cuanta area hay sino a que ALTURA esta.
    Esta rejilla vive abajo del todo en la trasera; paso unas horas en el suelo
    (y=4, mas tiro y mas area) y volvio aqui porque en el vuelo de la bandeja se
    transparentaba por el canto inferior."""
    xs, y0, y1 = _columnas_rejilla_entrada(p)
    # y=0: el canto de abajo de la plancha, en el plano del suelo. Da igual
    # para el resultado -- se resta al formar f_base/f_tras y se vuelve a
    # sumar al devolver el centroide, asi que se cancela -- pero tiene que
    # decir lo mismo que el .scad o el dia que deje de cancelarse miente.
    y0_pl = 0.0
    return (len(xs), y1 - y0,
            _area_ranuras(len(xs), y1 - y0, p["vent_ancho_ranura"]),
            y0_pl + (y0 + y1) / 2)


def _onda_area(p: dict[str, float], tipo: str, largo: float) -> float:
    """Area abierta de una onda, mismas cuentas que onda() en el .scad.

    La onda es el barrido de un circulo de vent_ancho_ranura a lo largo de una
    polilinea, o sea una salchicha: largo del camino por el ancho, mas el
    circulo que forman las dos puntas. En los quiebres la cuenta se pasa y se
    queda corta alternativamente, y en un zigzag eso se compensa."""
    per = p["vent_periodo"]
    a = per * 0.35
    n = max(2, math.floor(largo / per))
    base = {"sierra": ((0, -a), (1, a)),
            "triangulo": ((0, -a), (0.5, a))}.get(
                tipo, ((0, -a), (0.001, a), (0.5, a), (0.501, -a)))
    pts = [((i + q[0]) * per, q[1]) for i in range(n) for q in base]
    L = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            for i in range(len(pts) - 1))
    w = p["vent_ancho_ranura"]
    return L * w + math.pi * (w / 2) ** 2


def _ondas_trasera(p: dict[str, float]) -> tuple[float, float]:
    """Las ondas ABIERTAS de la trasera: (area, y_centroide en el case).

    Son SALIDA, no entrada. Es la unica ventilacion que Samuel quiso dejar en
    esa pieza.

    SON DOS, NO TRES, DESDE EL 2026-08-24. La sierra dejo de existir: ese sitio
    lo ocupa ahora el CAJEADO CIEGO de la palabra KONDOR (kondor_prof), que no
    atraviesa la plancha y por tanto no ventila y no puede seguir sumando aqui.
    ESE DIA la salida bajo de 12609 a 9943 mm2 y el salto termico subio de 6.6
    a 7.1 K contra el techo de 15 -- es lo que midio el A/B del 2026-08-24, no
    la corrida de hoy. HOY, con la rejilla y el puente de fragilidad movidos el
    2026-08-28, guarda_aire() imprime 3141 mm2 de salida y 10.8 K.

    El motivo no es termico sino de lo que hay DETRAS de cada onda, medido
    contra el envolvente de un modulo de fondo_pcb_max:

        triangulo y cuadrada  y =  99.47   171 mm de aire (piso de abajo)
        sierra                y = 180.94    32 mm: dorso de los modulos de
                                            arriba -- ranura que ensena cable
                                            y deja entrar polvo

    LO QUE ESTE NUMERO CUENTA, desde el 2026-09-03: los reguladores de la
    fuente (29,23 W a placa: los 27,53 del papel sec.6 tras D-F7, mas los 3,70
    de la franja de red que esa tabla no llevaba, menos los 2,02 de PS6 que
    seguian a un digital con la cadena de LED retirada dentro) MAS lo que
    disipan la fila de invitados, el digital y la VOZ dentro del mismo cajon
    (95,6 + 14,475 + 8,00 = 118,08 W; los +-12 V ultra de la Voz faltaban
    enteros hasta el 2026-09-05). Hasta el 18-08 eran 9,22 --solo los TO-220
    de la v3-- y con eso
    el case se cerro el 18-08. El liston de la PSU3 (D-F1) y D-F3 = A cambiaron
    las dos cosas: hay mas calor Y hay que dejarlo salir.

    Lo que estas dos ondas siguen sin ser: salen por debajo del entrepiso, asi
    que el camino que dibujan es el del valle y NO la bahia de arriba, que es
    la que el cajeado sella."""
    au = _trasera_au(p)
    # ANCLADAS AL CAMPO VISIBLE desde la trasera capturada (2026-08-29, noche,
    # 2): de la coronacion del labio del talon a la del techo, en y del mundo.
    # Fueron las dos filas de M3, que ya no existen. y0_pl = 0 se cancela.
    y0_pl = 0.0
    f_base, f_tras = _trasera_campo(p)
    y_bajas = f_base + 0.37 * (f_tras - f_base)
    # La sierra iba aqui con (_onda_area(p, "sierra", au * 0.70), y_sierra) y
    # y_sierra = f_base + 0.74 * (f_tras - f_base). Se cae con el cajeado: el
    # dibujo sigue existiendo en la plancha, la ventilacion no.
    trozos = ((_onda_area(p, "triangulo", au * 0.35), y_bajas),
              (_onda_area(p, "cuadrada", au * 0.35), y_bajas))
    area = sum(a for a, _ in trozos)
    centro = sum(a * (y0_pl + y) for a, y in trozos) / area
    return area, centro


# Aire a 20 C y el coeficiente de descarga de una rejilla de ranuras. Los tres
# primeros son fisica; C_D es SUPUESTO -- 0.6-0.7 es lo que se usa para chapa
# perforada y ranurada, y es el numero que mas manda en el resultado.
RHO_AIRE, CP_AIRE, G, T_AMB = 1.2, 1005.0, 9.81, 293.0
CD_TIRO = 0.65
# El extremo pesimista del rango, para publicar el resultado por los dos lados.
# Una rendija larga y estrecha bajo un alero no descarga como chapa ranurada, y
# nadie ha medido cual de los dos es. Se imprime, no se aseverea.
CD_TIRO_PESIMISTA = 0.55
# LA PARED EXTERIOR TAMBIEN EVACUA, y con 151.55 W dentro deja de ser un
# detalle: medio metro cuadrado de envolvente mueve mas vatios que la chimenea.
# U es el coeficiente global aire de dentro -> pared -> sala, o sea las dos
# caras en serie: con h ~ 5-8 W/m2K por cara, U ~ 2.5-4. SUPUESTO, sin medir, y
# por eso NO entra en el veredicto -- un termino sin medir que hace una puerta
# MAS permisiva es como se quema un aparato. Se imprime para que el papel del
# case sepa que el area que se le pide es una COTA SUPERIOR, y cuanto.
U_PARED_W_M2K = 3.0

# LA SALA DE DISENO de la spec del chasis (sec.3.1): 45 C. El case cuenta su
# aire con T_AMB = 20 C. Con la densidad y la temperatura del aire de la sala,
# el salto va con la temperatura absoluta: k va con rho / sqrt(T), rho con 1/T,
# y dT con k^(-2/3). Cual de las dos es la sala del case no esta firmado:
# guarda_aire() imprime las dos y publica el HUECO si el pesimista no pasa.
T_SALA_DISENO_K = 318.0

# Tension superficial del agua y su densidad a 20 C. Van aqui y no dentro de
# guarda_rendija() porque son fisica, como RHO_AIRE: el mojado TOTAL (angulo de
# contacto cero) es el peor caso y es lo que se supone -- aluminio anodizado
# limpio moja bastante, y un aluminio sucio moja mas todavia.
GAMMA_AGUA, RHO_AGUA = 0.073, 1000.0


def _rendija(p: dict[str, float]) -> tuple[float, float]:
    """LA SALIDA DE AIRE desde el 2026-08-30: la rendija entre la cara interior
    del labio del techo y la cara vista de la trasera, mirando al SUELO, tapada
    por el vuelo del techo.

    Sustituye a las 16 ranuras de la meseta (_rejilla_valle), que Samuel mato
    mirando el .blend: "no me gustan los huecos, es una decision erratica del
    diseno ya que esa parte es sensible a que le entren liquidos". Era la unica
    cara horizontal de arriba, con agujeros mirando al cielo.

    El area es lo que los tacos dejan libre por la luz. Los tacos NO son
    relleno: son los que fijan la luz -- sin ellos la plancha se pega al labio
    y cierra la salida --, asi que su huella se descuenta y su espesor ES
    aire_labios. La rendija de ABAJO (bajo el labio del talon) no se cuenta:
    si entra aire por ahi mejora el tiro, y lo que no se cuenta no puede
    empeorar el numero."""
    assert p["taco_n"] >= 2 and p["taco_largo"] > 0, (
        f"taco_n = {p['taco_n']:g} y taco_largo = {p['taco_largo']:g}: sin "
        f"tacos NO HAY RENDIJA. Son ellos los que fijan la luz -- la plancha "
        f"se pega al labio y la cierra --, asi que quitarlos no ensancha la "
        f"salida: la elimina. Con menos de dos por labio la plancha se apoya "
        f"en un punto y bascula")
    libre = perfil(p)["ancho_util"] - p["taco_n"] * p["taco_largo"]
    assert libre > 0, (
        f"los {p['taco_n']:.0f} tacos de {p['taco_largo']:g} ocupan mas que el "
        f"vano ({perfil(p)['ancho_util']:.2f}): no queda rendija")
    # LA LUZ ES LA COMPRIMIDA, no la nominal (2026-08-30, tras el revisor). El
    # area se calculaba con aire_labios a secas mientras guarda_rendija() ya
    # reconocia que los tacos ceden: dos puertas sobre la misma junta, cada una
    # con su estado. El caudal tiene que salir por la rendija que existe cuando
    # el aparato esta montado y apretado, que es la estrecha.
    d = p["aire_labios"] * (1.0 - p["compresion_taco"])
    # a la altura del canto de arriba de la trasera, que es por donde el aire
    # pasa antes de salir: medio milimetro por debajo, donde la rendija empieza
    return libre * d, _trasera(p)["y1"] - 0.5


def guarda_rendija(p: dict[str, float]) -> None:
    """El agua no puede subir por la rendija hasta meterse dentro del case.

    Es la puerta que paga el haber quitado las ranuras. Un derrame sobre la
    meseta baja por el chaflan, por el labio, y gotea por el canto del labio
    POR DELANTE de la plancha: eso lo arregla la geometria. Lo que la geometria
    no arregla sola es que el agua SUBA por la rendija, porque entre dos planos
    paralelos separados d el agua sube sola

        h = 2*gamma / (rho * g * d)

    y esa altura crece cuando d se estrecha. O sea que el peor caso NO es la
    luz nominal: es la luz COMPRIMIDA, con los tacos aplastados. Y por encima
    de eso, una plancha alabeada tiene luces locales menores que la nominal en
    algun punto de sus 540 mm -- por eso no basta con que la subida quepa en el
    solape, se exige margen.

    Lo que tapa el labio del canto de la trasera (el solape) es lo que hay que
    ganar: si el agua sube mas que eso, pasa el canto y cae dentro."""
    d_nom = p["aire_labios"]
    # POR LOS DOS LADOS (2026-08-30, tras el revisor). Por arriba, un taco que
    # cede del todo cierra la rendija; por ABAJO, una compresion negativa
    # significaria un taco que CRECE al apretarlo, y con ella la puerta daba
    # verde alegremente sobre una luz mayor que la nominal -- justo al reves de
    # lo que hay que suponer. El peor caso es siempre el mas estrecho.
    assert 0.0 <= p["compresion_taco"] < 1.0, (
        f"compresion_taco = {p['compresion_taco']:g}: tiene que estar entre 0 "
        f"(un taco que no cede) y 1 (uno que se aplasta del todo y cierra la "
        f"rendija). Un valor negativo es un taco que crece al apretarlo, y "
        f"haria que esta puerta midiera una luz mayor que la nominal")
    d = d_nom * (1.0 - p["compresion_taco"])
    assert d > 0, (
        f"con compresion_taco = {p['compresion_taco']:g} la rendija se cierra "
        f"del todo: no hay salida de aire ni luz que medir")
    subida = 2 * GAMMA_AGUA / (RHO_AGUA * G * (d / 1000.0)) * 1000.0
    # Lo que el labio del techo tapa del canto de arriba de la trasera.
    # _y_labio_techo() ya trae el chaflan y el labio; la resta ES el solape,
    # sin recomponerlo de sus sumandos (que es como se cuela un error de signo).
    solape = _trasera(p)["y1"] - _y_labio_techo(p)
    assert solape > 0, (
        f"el labio del techo muere en y = {_y_labio_techo(p):.2f} y el canto de "
        f"la trasera esta en {_trasera(p)['y1']:.2f}: no la tapa, asi que la "
        f"rendija no es una rendija sino una ranura abierta al cielo")
    assert subida <= solape - 2.0 + 1e-9, (
        f"el agua sube {subida:.1f} mm por la rendija comprimida ({d:.2f} de "
        f"luz, {d_nom:g} nominal menos un {p['compresion_taco']*100:.0f} %) y el "
        f"labio solo tapa {solape:.1f} del canto de la trasera: quedan "
        f"{solape - subida:.1f} de margen y se piden 2, porque la plancha viene "
        f"alabeada y la luz local no es la nominal. Sube aire_labios (la subida "
        f"va con 1/d) o techo_labio (sube el solape)")

    print(f"rendija: {d_nom:g} de luz nominal, {d:.2f} comprimida; el agua sube "
          f"{subida:.1f} y el labio tapa {solape:.1f} del canto de la trasera "
          f"({solape - subida:.1f} de margen, se piden 2). "
          f"{p['taco_n']:.0f} tacos de {p['taco_largo']:g} por labio")


def _envolvente_m2(p: dict[str, float]) -> float:
    """Envolvente exterior del case, con el suelo. Hasta el papel del suelo
    (2026-10-12) restaba el suelo porque la tabla apoyaba en la mesa y no
    convectaba; la base de chapa va sobre patas, con aire debajo. DERIVADA del
    perfil (perimetro x ancho + las dos mejillas), no parametro."""
    V = _vertices(p)
    n = len(V)
    per = sum(math.dist(V[i], V[(i + 1) % n]) for i in range(n))
    mejilla = abs(sum(V[i][0] * V[(i + 1) % n][1] - V[(i + 1) % n][0] * V[i][1]
                      for i in range(n))) / 2.0
    return (per * p["ancho_total"] + 2 * mejilla) * 1e-6


def _potencia_del_cajon() -> float:
    """Los W que el case tiene que evacuar, LEIDOS DE DONDE SE CALCULAN.

    `potencia_disipada` de params.scad es una COPIA, y el .scad la necesita
    porque es OpenSCAD y no puede importar nada. Desde el 2026-10-12 es la de
    la fuente v5 (D-V4, firmada en direccion el 08-09): todo lo que baja por el
    cordon del ladrillo acaba en calor dentro de la caja, y lo unico que se
    queda fuera es la perdida AC-DC del propio ladrillo. El numero lo calcula
    hardware/01-power-supply/v5/ladrillo_budget.py, calor_del_cajon_w(). Hasta
    ese dia era la suma de la v4, p_cajon_w + p_recinto_w a placa: 147.31 W,
    con el recinto de la fuente dentro del cajon.

    ES UNA COTA DE ABAJO, y lo dice la propia v5: su enmienda M1 (08-09) aisla
    el +5 V digital, y ladrillo_budget.py lo sigue contando con el rendimiento
    de un buck sin barrera (ETA_BUCK). La perdida interior esta subestimada y
    no tiene valor nuevo hasta que haya pieza (H-CENSO-ETA-DIGITAL). El dia
    que la v5 la cuente, esta copia se pone roja sola; mientras, guarda_aire()
    imprime cuanto aguanta la chimenea con los dos C_D.

    EL 2026-09-04 ESA COPIA LLEVO UN DIA MINTIENDO. Decia 147.83 cuando la
    franja de red (2.75 W de la NTC de arranque y 0.95 del choke) ya la habia
    subido a 151.55, y con ella se le publico al #289 un encargo de 25113 mm2
    de venteo cuando eran 25742. Nadie hizo nada mal: el numero cambio en la
    fuente y aqui no habia nada que lo notara.

    EL IMPORT ES DIFERIDO A PROPOSITO. ladrillo_budget.py importa
    calor_budget.py de la v4, y calor_budget.py importa de este modulo
    (CD_TIRO, CD_TIRO_PESIMISTA, CP_AIRE, G, RHO_AIRE), asi que a nivel de
    modulo esto seria un ciclo. Y el aserto vive en guarda_potencia_vigente()
    y no al importar: un aserto al importar dejaria rojos tambien a
    power_budget, margen_budget, secuencia_budget, fusible_budget,
    invitados_budget y check_bringup, que no tienen la culpa de un numero
    descuadrado aqui."""
    import os
    import sys
    v5 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "hardware", "01-power-supply", "v5")
    if v5 not in sys.path:
        sys.path.insert(0, v5)
    from ladrillo_budget import calor_del_cajon_w
    return calor_del_cajon_w()


def _plano_neutro(huecos: list[tuple[float, float]]) -> tuple[float, float]:
    """El plano neutro de una caja con huecos (y, area), en mm y mm2: la altura
    yn donde lo que entra por debajo iguala lo que sale por encima. La presion
    de flotabilidad es lineal en la altura, asi que el caudal de cada hueco va
    con a * sqrt(|y - yn|), y yn es la raiz de

        suma(a sqrt(yn - y), los de abajo) = suma(a sqrt(y - yn), los de arriba)

    Devuelve (yn, S), con S la suma de arriba en mm^2.5. La diferencia crece
    con yn y es continua --cada hueco pasa de salir a entrar por cero--, asi
    que la biseccion no salta. Vivio en case/cad/persiana.py hasta el
    2026-10-12."""
    def sobra(yn: float) -> float:
        return (sum(a * math.sqrt(yn - y) for y, a in huecos if y < yn)
                - sum(a * math.sqrt(y - yn) for y, a in huecos if y > yn))
    lo, hi = min(y for y, _ in huecos), max(y for y, _ in huecos)
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if sobra(mid) > 0 else (mid, hi)
    yn = (lo + hi) / 2
    return yn, sum(a * math.sqrt(y - yn) for y, a in huecos if y > yn)


@functools.lru_cache(maxsize=8)
def _respira_persiana(clave: tuple) -> tuple[tuple[float, float], ...]:
    """Las franjas por las que respira UNA persiana, como (y, area) cada 2 mm:
    lo que atraviesa detras de la ventana real del anillo (persiana.py,
    geometria()["abierto"]).

    EN CACHE POR LA TUPLA ENTERA DE LOS PARAMETROS: la geometria de shapely
    tarda medio segundo y canario_techo() pide la chimenea varias veces. La
    clave no se recorta a las cotas de la persiana a proposito: una lista de
    claves escrita a mano se queda vieja el dia que la persiana lea una cota
    nueva.

    EL IMPORT ES DIFERIDO A PROPOSITO: persiana.py importa este modulo al
    cargarse, asi que a nivel de modulo seria un ciclo."""
    import os
    import sys
    cad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad")
    if cad not in sys.path:
        sys.path.insert(0, cad)
    import persiana
    return tuple(persiana.franjas(persiana.geometria(dict(clave))["abierto"]))


def _huecos(p: dict[str, float], costados: int = 2,
            trasera: bool = True) -> list[tuple[float, float]]:
    """Cada hueco por el que respira el case, como (y, area) en mm y mm2: las
    franjas de las persianas por cada costado libre, y las tres aberturas de la
    trasera --la rejilla baja, la rendija del alero y las dos ondas--."""
    hs = ([(y, a * costados) for y, a in _respira_persiana(tuple(sorted(p.items())))]
          if costados else [])
    if trasera:
        _n, _largo, a_ent, y_ent = _rejilla_entrada(p)
        a_ren, y_ren = _rendija(p)
        a_ond, y_ond = _ondas_trasera(p)
        hs += [(y_ent, a_ent), (y_ren, a_ren), (y_ond, a_ond)]
    return hs


# EL CANAL BAJO LA BASE (papel del suelo, sec.5). Es lo que el aire corre por
# el hueco de alto_pie entre la chapa y la mesa hasta el campo de agujeros. El
# flujo de verdad es 2D y converge; aqui es un canal solo, de ancho la rendija
# libre y de este largo. 60 es la estimacion: casi todo el perimetro queda a
# 25-30 mm de un agujero, y el tramo de atras a la derecha a unos 200, debajo
# del chasis. 120 es la pesimista, que va con CD_TIRO_PESIMISTA. SUPUESTO: se
# mide en la primera unidad (HUECO H2 del papel).
CANAL_BASE = 60.0
CANAL_BASE_PESIMISTA = 120.0
MU_AIRE = 1.8e-5          # Pa s, aire a ~30 C


def _camino_base(p: dict[str, float], costados: int = 2,
                 canal: float = CANAL_BASE) -> dict:
    """La entrada por la base, en serie: la rendija que dejan las patas en el
    perimetro de la chapa, el canal laminar de alto_pie y los agujeros del
    campo. Cada pata tapa su diametro de rendija, y una pared contra un costado
    tapa tambien el tramo de ese costado."""
    largo = fondo(p) - 2 * p["chaflan_nariz"]
    libre = (2 * (p["ancho_total"] + largo) - 4 * p["d_pie"]
             - (2 - costados) * (largo - 2 * p["d_pie"]))
    return {"a_base": len(_campo_base(p)) * math.pi * p["base_agujero"] ** 2 / 4,
            "w": libre, "largo": canal, "h": p["alto_pie"]}


def _caudal_base(dp: float, cd: float, a_base: float, w: float, largo: float,
                 h: float) -> float:
    """m3/s que suben por la base con dp Pa de tiro a y = 0:
        dp = rho/2 (Q / (C_D A_r))^2 + 12 mu L Q / (W h^3) + rho/2 (Q / (C_D A_b))^2
    La rendija y los agujeros son orificios; el canal, Poiseuille entre placas."""
    if dp <= 0 or a_base <= 0:
        return 0.0
    a = RHO_AIRE / 2 * (1 / (cd * w * h * 1e-6) ** 2 + 1 / (cd * a_base * 1e-6) ** 2)
    b = 12 * MU_AIRE * largo * 1e-3 / (w * 1e-3 * (h * 1e-3) ** 3)
    return (-b + math.sqrt(b * b + 4 * a * dp)) / (2 * a)


def _caudales(hs, cd: float, camino: dict | None, yn: float,
              dt: float) -> tuple[float, float]:
    """(entra, sale) en m3/s con el plano neutro en yn mm y el salto dt K."""
    g = RHO_AIRE * G * dt / T_AMB * 1e-3          # Pa por mm de altura
    entra = sale = 0.0
    for y, a in hs:
        q = cd * a * 1e-6 * math.sqrt(2 * g * abs(y - yn) / RHO_AIRE)
        if y < yn:
            entra += q
        else:
            sale += q
    if camino:
        entra += _caudal_base(g * yn, cd, **camino)
    return entra, sale


def _neutro(hs, cd: float, camino: dict | None, dt: float) -> float:
    """El plano neutro por balance de masa. Con la base deja de ser independiente
    de dT, porque el canal es lineal y los orificios no."""
    lo, hi = min(0.0, min(y for y, _ in hs)), max(y for y, _ in hs)
    for _ in range(50):
        yn = (lo + hi) / 2
        entra, sale = _caudales(hs, cd, camino, yn, dt)
        lo, hi = (lo, yn) if entra > sale else (yn, hi)
    return (lo + hi) / 2


def _potencia_con(hs, cd: float, camino: dict | None, dt: float) -> float:
    """W que la chimenea evacua con un salto de dt K."""
    yn = _neutro(hs, cd, camino, dt)
    return RHO_AIRE * CP_AIRE * _caudales(hs, cd, camino, yn, dt)[1] * dt


def _tiro(p: dict[str, float], cd: float = CD_TIRO, costados: int = 2,
          trasera: bool = True, base: bool = True,
          canal: float = CANAL_BASE) -> dict:
    """La chimenea del case: el plano neutro, lo que entra y lo que sale, el
    salto termico y lo que evacua al techo.

    DESDE EL PAPEL DEL SUELO (2026-10-12) LA BASE ES UN CAMINO DE ENTRADA EN
    SERIE (_camino_base()): rendija de las patas, canal laminar y agujeros. Con
    un termino lineal la chimenea deja de ser P = k dT^1.5 y se resuelve con
    dos bisecciones: el plano neutro por masa a cada dT (_neutro()) y dT por
    energia. Sin base (base=False) da la forma cerrada de antes al millonesimo
    (autocomprobacion_base()): P = k dT^1.5, k = rho cp C_D sqrt(2 g / T) S,
    con S la suma de a sqrt(y - yn) de los huecos de arriba (_plano_neutro()).

    FUE EN SERIE HASTA EL 2026-10-12: una entrada y una salida, A_ef^-2 =
    A_in^-2 + A_out^-2, y el tiro entre sus centroides. Con una entrada y una
    salida las dos cuentas son la misma (autocomprobacion_plano_neutro()); con
    las persianas no, porque su ventana es ancha abajo y una cuna arriba y cada
    franja entra o sale segun su altura. El modelo H/4-3H/4 de la piel, que
    ponia la entrada a un cuarto del alto y la salida a tres cuartos, daba un
    tiro mayor que este (papel de la persiana, sec.5).

    SALIO DE guarda_aire() EL 2026-09-03 para que canario_techo() pudiera leer
    los NUMEROS y no el mensaje de la puerta.

    `falta` es la potencia de dentro sobre la que la chimenea evacua al techo.
    Con la base ya no dice cuanta area hace falta: el canal no escala con el
    area de los agujeros."""
    hs = _huecos(p, costados, trasera)
    camino = _camino_base(p, costados, canal) if base else None
    techo = p["salto_termico_max"]
    lo, hi = 1e-3, 500.0
    for _ in range(50):
        dt = (lo + hi) / 2
        if _potencia_con(hs, cd, camino, dt) < p["potencia_disipada"]:
            lo = dt
        else:
            hi = dt
    dt = (lo + hi) / 2
    yn = _neutro(hs, cd, camino, dt)
    g = RHO_AIRE * G * dt / T_AMB * 1e-3
    p_evacuada = _potencia_con(hs, cd, camino, techo)
    return {"huecos": hs, "yn": yn,
            "a_entra": sum(a for y, a in hs if y < yn),
            "a_sale": sum(a for y, a in hs if y > yn),
            "a_base": camino["a_base"] if camino else 0.0,
            "q_base": _caudal_base(g * yn, cd, **camino) if camino else 0.0,
            "p_evacuada": p_evacuada,
            "p_pared": U_PARED_W_M2K * _envolvente_m2(p) * techo,
            "dt": dt,
            "falta": p["potencia_disipada"] / p_evacuada}


def _tiro_pesimista(p: dict[str, float], **kw) -> dict:
    """El pesimista junta los dos supuestos pesimistas: C_D 0.55 y el canal de
    120 bajo la base."""
    return _tiro(p, CD_TIRO_PESIMISTA, canal=CANAL_BASE_PESIMISTA, **kw)


def _potencia_a(p: dict[str, float], dt: float, cd: float = CD_TIRO,
                costados: int = 2, trasera: bool = True, base: bool = True,
                canal: float = CANAL_BASE) -> float:
    """W que la chimenea evacua con un salto de dt K: la inversa de _tiro().
    Con la base ya no hay k que elevar a 1.5, asi que los canarios que derivan
    una carga del techo pasan por aqui."""
    hs = _huecos(p, costados, trasera)
    camino = _camino_base(p, costados, canal) if base else None
    return _potencia_con(hs, cd, camino, dt)


def guarda_potencia_vigente(p: dict[str, float]) -> None:
    """El calor que este budget reparte tiene que ser el que la fuente calcula.

    Es ROJO y no HUECO a proposito: un desfase aqui no pide rediseñar nada --se
    arregla copiando un literal-- y mientras no se arregle sale mal TODO lo que
    guarda_aire() publica: el salto, el deficit y el encargo del #289. Fue
    exactamente lo que paso el 04-09 (ver _potencia_del_cajon()).

    VIVE APARTE DE guarda_aire() Y NO DENTRO, y no es cuestion de gusto:
    canario_techo() llama a guarda_aire() con potencia_disipada = 1.0 W a
    proposito, para probar que con carga de juguete la puerta NO publica el
    HUECO. Un cruce metido ahi dentro mataria ese canario -- una puerta nueva
    que rompe la prueba de otra puerta vieja. Una guarda, una cosa."""
    pot = _potencia_del_cajon()
    assert abs(p["potencia_disipada"] - pot) < 0.01, (
        f"potencia_disipada dice {p['potencia_disipada']:.2f} W y "
        f"ladrillo_budget.py de la fuente v5, que es donde se calcula, da "
        f"{pot:.2f}: lo que baja por el cordon del ladrillo, que acaba entero en "
        f"calor dentro de la caja. {abs(p['potencia_disipada'] - pot):.2f} W de "
        f"desfase. Este numero NO se toca aqui para que la puerta calle: si la "
        f"fuente lo cambio, copia el suyo a params.scad y vuelve a correr -- el "
        f"salto y el veredicto del aire se recalculan solos. Si el que esta mal "
        f"es el de la fuente, arreglalo alli y no aqui")
    print(f"potencia del cajon: {pot:.2f} W, y params.scad dice lo mismo "
          f"(la copia se cruza contra ladrillo_budget.py de la fuente v5; es "
          f"cota de abajo por su enmienda M1)")


def guarda_aire(p: dict[str, float]) -> None:
    """El case no puede calentarse mas de salto_termico_max sobre ambiente.

    ESTA PUERTA CAMBIO DE CRITERIO EL MISMO DIA QUE NACIO, y conviene saber por
    que. Nacio midiendo "entrada >= salida", que valia mientras la entrada era la
    rejilla de la trasera: 8317 mm2 contra 7499 de salida. Al mudarse la entrada
    al suelo -- Samuel pidio dejar la trasera solo con sus tres ondas -- el area
    baja a 3536 y esa desigualdad se rompe A PROPOSITO. Mantenerla habria sido
    tener una puerta roja sobre un diseno correcto, que es justo el vicio que ya
    costo una tanda entera en este repo.

    Lo que de verdad hay que exigir no es paridad de areas: es que el aparato no
    se caliente. Y eso se calcula, porque el area no es lo unico que manda --
    tambien manda la ALTURA entre entrada y salida. La rejilla del suelo tiene
    menos de la mitad de area que la de la trasera y aun asi sale casi igual de
    bien, porque entra a 4 mm en vez de a 53 y el tiro gana lo que pierde.

    Tiro de chimenea, regimen laminar de caja cerrada:

        Q = C_D * A_ef * sqrt(2 g h dT / T)        caudal
        P = rho * cp * Q * dT                      calor que se lleva
        =>  P = k * dT^1.5,  k = rho*cp*C_D*A_ef*sqrt(2 g h / T)

    A_ef son entrada y salida EN SERIE (1/A_ef^2 = 1/A_in^2 + 1/A_out^2), y h la
    distancia entre sus centroides. Nada de esto esta medido: C_D, la altura
    efectiva y las perdidas del trafo son supuestos, y por eso el techo va
    holgado y no pegado al resultado. Sirve para ordenes de magnitud y para que
    un cambio de geometria no empeore el tiro sin que nadie se entere.

    Y EL 2026-09-03 DEJA DE SER UN ASERTO. No porque el criterio se ablande
    --el techo no se toco ese dia; subio a 20 el 04-09 y por la razon contraria,
    para dejar de contradecir el DELTA_T = 20.0 con el que tuning_budget.py ya
    calculaba la deriva de afinacion-- sino porque la carga dejo de ser la del PSU
    solo: son 147.31 W (29,23 del recinto de la fuente + 118,08 de la fila de
    invitados, el digital y la Voz, papel de la fuente v4 sec.6), y esta
    geometria evacua 12.6. Eran 151.55 hasta el 2026-09-05, y ese dia se
    movieron dos celdas en sentido contrario: bajaron 12,24 de calor de la
    cadena de LED que D1 retiro el 03-09 y que el digital seguia cobrando, y
    subieron 8,00 de la Voz, que disipa aqui dentro los +-12 V ultra que la
    cascada le entrega y que no estaba en ninguna celda.
    Un rojo permanente sobre un diseno que nadie ha rehecho
    todavia no verifica nada: ensena a empujar con --no-verify, que es el
    habito que estas puertas existen para no crear. Asi que el deficit se
    PUBLICA como HUECO, con el area que hace falta y con quien lo cierra --
    el papel del case, D-F3 = A firmada el 03-09, issue #289--, igual que
    guarda_trasera_flexion() publica su banda de arriba. El dia que ese papel
    dibuje el venteo, esta puerta se pone verde sola.

    Y EL 2026-10-12 VUELVE A SER UN ASERTO. El venteo esta dibujado --las
    dos persianas, papel de la persiana sec.5-- y la potencia es la de la
    fuente v5, con la fuente afuera. Con C_D = 0.65 el case sube 16.9 K
    contra 20, y la puerta juzga con ese C_D (papel sec.5.5): el pesimista es
    la prueba de robustez y se imprime. Un costado contra una pared no pasa,
    y eso es una condicion de uso (PLIEGO sec.7), con su HUECO hasta que el
    arranque mida cuanta holgura hace falta. La sala de 45 C de la spec del
    chasis se imprime tambien, y publica su HUECO mientras no se decida.

    Y DESDE EL PAPEL DEL SUELO (2026-10-12) LA BASE RESPIRA. El aire entra
    tambien por la base, en serie con la rendija de las patas y el canal de
    debajo (_camino_base()). Los dos HUECOS se juzgan con el pesimista, que
    es C_D 0.55 con el canal de 120: con la base, el nominal de un costado
    tapado pasa y el pesimista no, y juzgarlo con el nominal lo callaba en
    silencio (papel del suelo, sec.5)."""
    _n, largo_ent, _a, _y = _rejilla_entrada(p)
    assert largo_ent >= 4 * p["vent_ancho_ranura"], (
        f"la rejilla de entrada mide {largo_ent:.1f} mm de largo con "
        f"ranuras de {p['vent_ancho_ranura']:.2f}: deja de leerse como campo y "
        f"pasa a rayitas (es la misma cuenta que recorto la espina del valle)")
    t = _tiro(p)
    techo = p["salto_termico_max"]
    print(f"aire: plano neutro a {t['yn']:.0f} mm; por debajo entran "
          f"{t['a_entra']:.0f} mm2 de huecos y los {t['a_base']:.0f} de la "
          f"base, y por encima salen {t['a_sale']:.0f}, en {len(t['huecos'])} "
          f"huecos: las franjas de las dos persianas, la rejilla baja de la "
          f"trasera, la rendija del alero y las ondas")
    print(f"  {t['dt']:.1f} K sobre ambiente con {p['potencia_disipada']:.2f} W "
          f"(techo {techo:.0f}; esta chimenea evacua {t['p_evacuada']:.1f} W a "
          f"ese techo). SUPUESTO: C_D={CD_TIRO}, aire a {T_AMB - 273.15:.0f} C")
    assert t["dt"] <= techo + 1e-9, (
        f"el case sube {t['dt']:.1f} K sobre ambiente con "
        f"{p['potencia_disipada']:.2f} W y el techo es {techo:g}: esta chimenea "
        f"evacua {t['p_evacuada']:.1f} W a ese techo. Hace falta mas area, "
        f"salidas mas altas o mas pata bajo la base: el tiro va con la RAIZ de "
        f"la altura")
    t_p = _tiro_pesimista(p)
    print(f"  aviso: con C_D={CD_TIRO_PESIMISTA} (rendija bajo alero, no chapa "
          f"ranurada) y el canal de {CANAL_BASE_PESIMISTA:g} bajo la base serian "
          f"{t_p['dt']:.1f} K, y evacua {t_p['p_evacuada']:.1f} W a ese techo. "
          f"Sin medir hasta el ensayo")
    f_sala = T_SALA_DISENO_K / T_AMB
    print(f"  aviso: con la sala a {T_SALA_DISENO_K - 273.15:.0f} C de la spec "
          f"del chasis serian {t['dt'] * f_sala:.1f} K, y "
          f"{t_p['dt'] * f_sala:.1f} con el pesimista")
    if t_p["dt"] * f_sala > techo + 1e-9:
        _HUECOS.append(
            f"la sala de diseno del case sin decidir: con la de la spec del "
            f"chasis ({T_SALA_DISENO_K - 273.15:.0f} C) el case sube "
            f"{t['dt'] * f_sala:.1f} K, y {t_p['dt'] * f_sala:.1f} con el C_D "
            f"pesimista contra un techo de {techo:.0f}. La puerta juzga con "
            f"{T_AMB - 273.15:.0f} C; cual es la sala del case lo decide Samuel")
    print(f"  aviso: la envolvente exterior ({_envolvente_m2(p):.3f} m2, con la "
          f"base, que va sobre patas) se lleva otros {t['p_pared']:.1f} W a ese techo con "
          f"U={U_PARED_W_M2K} W/m2K (SUPUESTO); no entra en el veredicto")
    t_1 = _tiro_pesimista(p, costados=1)
    print(f"  con un costado tapado (contra una pared), pesimista: {t_1['dt']:.1f} K")
    if t_1["dt"] > techo + 1e-9:
        _HUECOS.append(
            f"la holgura de los costados sin medir: con un costado tapado el "
            f"case sube {t_1['dt']:.1f} K con el pesimista y "
            f"{p['potencia_disipada']:.2f} W, y el techo es {techo:.0f}. Los dos "
            f"tienen que quedar libres (PLIEGO sec.7); cuanta holgura hace falta "
            f"a cada lado se mide en el arranque (papel de la persiana, HUECO 4)")
    t_0 = _tiro_pesimista(p, base=False)
    print(f"  aviso: sobre un pano o una alfombrilla la base no respira y el "
          f"pesimista sube a {t_0['dt']:.1f} K (PLIEGO sec.7: mesa dura, con "
          f"los {p['alto_pie']:g} mm de pata libres debajo)")


# Umbral de fluencia del PMMA. SUPUESTO DECLARADO (#106): nadie lo ha medido
# sobre el acrilico que se va a comprar. Vive aqui con su cliente,
# guarda_trasera_flexion(); hasta el 2026-10-11 lo leia tambien
# guarda_costado(), en check_dxf.py, que se fue con la mejilla.
SIGMA_PMMA = 10.0


def guarda_paticas(p: dict[str, float]) -> None:
    """Una goma dura no aisla menos: AMPLIFICA.

    El toroide excita a 100 Hz -- magnetostriccion al doble de la red, #106.
    La pata y la masa del case forman un muelle, y si su frecuencia propia
    cae cerca de esos 100 Hz la transmisibilidad se dispara: la mesa recibe
    MAS zumbido del que recibiria con el acrilico apoyado en seco. Una mesa
    es una superficie radiante mucho mayor que el case.

    Por eso la cota que decide una patica no es la dureza ni el diametro:
    es CUANTO SE HUNDE bajo carga. f_propia = 15.76 / sqrt(flecha_mm) es la
    formula de manual para un grado de libertad bajo su propio peso.

    Se exige f_propia <= 100/3. El factor 3 es el minimo habitual para que la
    transmisibilidad baje del 15 %; por debajo de 3 se entra en la zona donde
    la curva sube en vez de bajar.

    ES REQUISITO DE COMPRA, NO DE DIBUJO: la flecha sale de la curva
    carga-deformacion del fabricante. Una goma que no publica esa curva no se
    puede verificar, y por tanto no sirve.
    """
    MASA_CASE, F_TOROIDE = 9.30, 100.0        # kg (#106, con 5 largueros), Hz
    carga = MASA_CASE * 9.81 / 4
    f_propia = 15.76 / math.sqrt(p["flecha_pie"])
    transmision = 1 / abs((F_TOROIDE / f_propia) ** 2 - 1)
    flecha_min = (15.76 / (F_TOROIDE / 3)) ** 2
    assert f_propia <= F_TOROIDE / 3, (
        f"flecha_pie = {p['flecha_pie']} mm da f propia {f_propia:.1f} Hz "
        f"contra los {F_TOROIDE:.0f} Hz del toroide: transmite "
        f"{transmision*100:.0f} %. Una goma que se hunde poco NO aisla menos, "
        f"AMPLIFICA. Hace falta >= {flecha_min:.2f} mm de flecha.")
    print(f"paticas: {carga:.1f} N por pata, se hunden {p['flecha_pie']} mm "
          f"-> f propia {f_propia:.1f} Hz, transmiten {transmision*100:.0f} % "
          f"de los {F_TOROIDE:.0f} Hz del toroide")



def guarda_chaflan(p: dict[str, float]) -> None:
    """El chaflan mata el filo sin comerse la pieza.

    Existe porque el 2026-08-24 las dos esquinas traseras pasaron a VIVAS
    (radio_trasero = 0) para que la trasera empotre a ras, y ese mismo dia se
    decidio canto DIAMANTADO. Arista viva mas canto pulido es una esquina que
    se desportilla al primer roce, y la de fondo-abajo esta a ras del suelo,
    que es donde el case roza al arrastrarlo por una mesa.

    NO ES GEOMETRIA DE ESTE MODELO y por eso no aparece en ningun DXF: un
    fichero de corte 2D no sabe decir "y ademas matale el filo". Es cota de
    PLIEGO. Vive aqui para tener puerta y no perderse.

    Dos limites, y muerden por razones distintas:
      - por abajo, la maquina: un chaflan menor que 0.3 no se ejecuta como
        chaflan, se redondea solo. Pedir arista viva es otra cosa y se dice
        aparte.
      - por arriba, la plancha mas FINA: el chaflan se come material de las
        DOS caras, y en una plancha delgada uno grande deja el canto en filo
        otra vez, por el otro lado.

    LA TAPA DEL VALLE NO CUENTA AQUI desde el 2026-08-25, y es deliberado: es
    de ALUMINIO (t_valle = 3), y este chaflan es una exigencia del PLIEGO DE
    ACRILICO -- existe porque el PMMA con arista viva y canto diamantado se
    desportilla al primer roce. El aluminio ni craquela ni se desportilla asi,
    y su canto lo resuelve el taller de chapa con su propio desbarbado.
    Dejarla dentro clavaba el techo del chaflan en 0.75 mm por una pieza a la
    que la regla no le aplica, que es exactamente el vicio de la puerta que
    grita en falso.
    """
    # t_base SALE de esta cuenta el 2026-08-27: es una tabla de madera, y el
    # chaflan de esta puerta es cota de fresado de PMMA. Mismo motivo por el que
    # ya estaba fuera la tapa del valle -- una regla que no le aplica a la pieza
    # grita en falso.
    t_min = p["t_piel"]
    assert p["chaflan"] >= 0.3, (
        f"chaflan = {p['chaflan']} mm: por debajo de 0.3 el taller no lo "
        f"ejecuta como chaflan, lo redondea. Pedir 0 (arista viva) es otra "
        f"cosa y hay que decirlo aparte, no colarlo por aqui.")
    assert p["chaflan"] <= t_min / 4, (
        f"chaflan = {p['chaflan']} mm contra la plancha mas fina ({t_min:g} "
        f"mm): se come mas de un cuarto del espesor por cada cara y el canto "
        f"vuelve a quedar en filo. Maximo {t_min/4:.2f}.")
    print(f"chaflan PMMA: {p['chaflan']} mm x 45 en toda arista vista de "
          f"acrilico (techo por el PMMA mas fino de {t_min:g} mm: "
          f"{t_min/4:.2f})")


# La tapa del valle y el esqueleto son de ALUMINIO. Modulo elastico: 69 GPa,
# comun a las aleaciones y por eso no cambia. El limite elastico SI, y va
# CONSERVADOR: 130 MPa es el Rp0.2 de un 5754 H22, la chapa corriente de corte.
#
# SUBIO A 250 Y VOLVIO A BAJAR EL MISMO DIA (2026-08-27), y la vuelta atras es
# el dato bueno. Al pasar la chapa de 3 a 1.5 medi que la costilla llegaba a
# 144.4 MPa en el tramo del valle y conclui que hacia falta un 6082-T6. Estaba
# mal: esa medicion se tomo con el ala en CUATRO de los siete tramos. En la
# misma tanda el ala paso a los SIETE -- pedido por estetica, para que ningun
# canto de acrilico se vea -- y el tramo del valle dejo de ser pletina plana.
# Con el ala puesta trabaja a ~62 MPa y pasa de sobra con los 130. El cambio
# que se pidio por como se VE arreglo solo el problema de como AGUANTA.
#
# Lo cazo codex, que noto que mis cifras no salian de la formulacion actual de
# guarda_costilla() y lo dijo en vez de escribirlas igual.
#
# O sea: el 6082-T6 se puede pedir por margen, pero NO lo exige el calculo.
# Un cambio de material que ninguna puerta pide es sobreespecificar y lo paga
# el pliego. SUPUESTO DECLARADO: los 130 siguen sin medirse.
#
# guarda_costilla() murio el 2026-08-28 con la chapa plegada. Quien mide hoy
# contra estos 130 es guarda_anillo(), y con mas margen todavia: la pletina da
# I = 3714 mm4 contra los 1673 de la L, o sea que el material manda aun menos
# que cuando este parrafo se escribio.
E_ALUMINIO, RP02_ALUMINIO = 69000.0, 130.0
# El talon, el techo y la nariz van en 6082-T6 por pliego (PLIEGO.md, tabla de
# chapa) desde que el techo necesito los 240 con el labio a 13 -- y aunque
# volvio a 18 y pasa con 130, el pliego lo dejo escrito. Lo usan la lengueta
# de la pestana del talon, que con la reaccion en su punta trabaja a unos 200
# MPa, y desde el papel del suelo el borde de los agujeros de la base.
RP02_6082_T6 = 240.0
# Cuanto concentra el borde de un agujero la tension del puente entre agujeros
# (papel del suelo sec.3.2: «de 2 a 3 veces»; Elke, ESTIMADO). Va en el extremo
# alto: la puerta de la base se pone roja si el borde llega a la fluencia.
K_BORDE_AGUJERO = 3.0


def _geometria_apoyo_valle(p: dict[str, float]) -> dict[str, object]:
    """Mide la cadena banda--tira--primer KONDOR--marco en cajas reales."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ventana_x0 = _frente_kondor(p, P, cr)
    centros = _centros_rail_1u(p, P, cr)
    railes, planchas, _ = _cajas_solidas(p)
    primer = next(c for c in railes if c[0] == "fila KONDOR 0")
    tramos = [c for c in planchas if c[0].startswith("tapa_valle")]
    apoyo = max(tramos, key=lambda c: c[2])
    tira = next((c for c in planchas if c[0] == "tira anti-ruido valle"), None)
    marcos = [c for c in railes if c[0].startswith("marco valle")]
    x_fin = apoyo[2]
    panel_x0 = centros[0][0] - p["inset_er"]
    gap = apoyo[3] - primer[4]
    tira_real = tira[4] - tira[3] if tira else 0.0
    return {
        "apoyo": x_fin - primer[1],
        "espesor_apoyo": apoyo[4] - apoyo[3],
        "gap": gap,
        "tira_nominal": p.get("tira_valle_nominal", 0.0),
        "compresion": p.get("compresion_tira_valle", 0.0),
        "tira_real": tira_real,
        "tira_x": (tira[1], tira[2]) if tira else (0.0, 0.0),
        "apoyo_x": (primer[1], x_fin),
        "cara_inferior_apoyo": apoyo[3],
        "cara_exterior_rail": primer[4],
        "contactos_marco": [
            min(abs(primer[5] - m[6]), abs(primer[6] - m[5])) for m in marcos
        ],
        "primer_riel": centros[0],
        "primer_riel_esperado": (
            ventana_x0 + p["rail_er_alto"] / 2,
            P[3][1] - p["rehundido_panel"] - p["t_panel"]
            - p["rail_er_eje"],
        ),
        "x_fin": x_fin,
        "panel_x0": panel_x0,
        "z_apoyo": (apoyo[5], apoyo[6]),
        "z_tira": (tira[5], tira[6]) if tira else (0.0, 0.0),
        "z_rail": (primer[5], primer[6]),
    }


def _guarda_apoyo_valle(p: dict[str, float], g: dict[str, object]) -> None:
    """Contrato geometrico del apoyo macizo y su calce anti-ruido."""
    apoyo = float(g["apoyo"])
    assert apoyo > 0, (
        f"el apoyo horizontal del valle es {apoyo:.2f} mm: tiene que ser "
        f"positivo y no una arista")
    assert apoyo >= 2.00 - 0.001, (
        f"el apoyo horizontal del valle es {apoyo:.2f} mm y se exigen al "
        f"menos 2.00 mm sobre el primer Z-Rail KONDOR")
    espesor = float(g["espesor_apoyo"])
    assert abs(espesor - p["t_valle"]) < 0.001, (
        f"la prolongacion del valle tiene {espesor:.2f} mm: tiene que conservar "
        f"el espesor completo de {p['t_valle']:.2f} mm")
    assert abs(apoyo - p["apoyo_valle"]) < 0.001, (
        f"la prolongacion real es {apoyo:.2f} y apoyo_valle pide "
        f"{p['apoyo_valle']:.2f} mm")
    gap = float(g["gap"])
    assert abs(gap - 0.10) < 0.001, (
        f"el gap banda--primer KONDOR es {gap:.2f} mm y tiene que ser 0.10")
    nominal, compresion = float(g["tira_nominal"]), float(g["compresion"])
    assert abs(nominal - 0.20) < 0.001, (
        f"la tira anti-ruido es {nominal:.2f} nominal y tiene que ser 0.20 mm")
    assert abs(compresion - 0.10) < 0.001, (
        f"la compresion de la tira es {compresion:.2f} y tiene que ser 0.10 mm")
    calce = nominal - compresion
    assert abs(calce - gap) < 0.001, (
        f"el calce comprimido es {calce:.2f} y el gap mide {gap:.2f} mm")
    tira_real = float(g["tira_real"])
    assert tira_real > 0.0 and g["tira_x"] != (0.0, 0.0), (
        "tira ausente: el camino banda -> tira -> KONDOR queda abierto")
    assert abs(tira_real - calce) < 0.001, (
        f"la tira 3D ocupa {tira_real:.2f} mm y el calce comprimido "
        f"pide {calce:.2f} mm")
    assert g["tira_x"] == g["apoyo_x"], (
        f"la tira no cubre los 2.00 mm de apoyo: tira {g['tira_x']}, apoyo "
        f"{g['apoyo_x']}")
    assert float(g["x_fin"]) <= float(g["panel_x0"]) + 0.001, (
        f"el apoyo del valle acaba en x={float(g['x_fin']):.2f} e invade el "
        f"panel KONDOR, que empieza en x={float(g['panel_x0']):.2f}")
    c = g["primer_riel"]
    esperado = g["primer_riel_esperado"]
    assert isinstance(c, tuple) and isinstance(esperado, tuple)
    dx, dy = c[0] - esperado[0], c[1] - esperado[1]
    assert math.hypot(dx, dy) < 0.001, (
        f"el primer riel KONDOR se movio ({dx:+.3f}, {dy:+.3f}) mm al anadir "
        f"el apoyo del valle; tiene que quedar invariante")
    z_apoyo = g["z_apoyo"]
    z_tira = g["z_tira"]
    z_rail = g["z_rail"]
    assert z_apoyo == z_tira == z_rail, (
        f"la cadena no cubre todo el ancho util: apoyo z={z_apoyo}, "
        f"tira z={z_tira}, KONDOR z={z_rail}")
    assert len(g["contactos_marco"]) == 2 and all(
        abs(float(v)) < 0.001 for v in g["contactos_marco"]), (
        f"el primer KONDOR no entrega la carga a los dos lados del marco: "
        f"gaps {g['contactos_marco']}")


def guarda_valle(p: dict[str, float]) -> None:
    """Banda del valle como tira en voladizo apoyada en el primer KONDOR."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    x0 = _x_valle(p, P, cr)[0]
    x_rail = _frente_kondor(p, P, cr)
    vuelo, t = x_rail - x0, p["t_valle"]
    b_mano = p["b_mano_valle"]
    inercia = b_mano * t ** 3 / 12
    flecha = p["carga_mano"] * vuelo ** 3 / (3 * E_ALUMINIO * inercia)
    sigma = 6 * p["carga_mano"] * vuelo / (b_mano * t ** 2)
    g = _geometria_apoyo_valle(p)
    _guarda_apoyo_valle(p, g)
    assert sigma <= RP02_ALUMINIO, (
        f"la tira B_MANO={b_mano:.0f} del valle trabaja a {sigma:.1f} MPa "
        f"con {p['carga_mano']:.0f} N y supera Rp0.2={RP02_ALUMINIO:.0f} MPa")
    assert flecha <= p["flecha_costado_max"], (
        f"la tira B_MANO={b_mano:.0f} del valle cede {flecha:.3f} mm con "
        f"{p['carga_mano']:.0f} N y se admiten {p['flecha_costado_max']:.3f} mm")
    print(f"valle: tira conservadora B_MANO={b_mano:.0f} x {t:g}, vuelo "
          f"{vuelo:.2f} desde el pico al primer Z-Rail KONDOR")
    print(f"  con {p['carga_mano']:.0f} N en el borde: flecha {flecha:.3f} mm, "
          f"tension {sigma:.1f} MPa; apoyo macizo {float(g['apoyo']):.2f} mm")
    print(f"  camino banda -> tira -> primer KONDOR -> marco: gap "
          f"{float(g['gap']):.2f}, tira {float(g['tira_nominal']):.2f} nominal, "
          f"compresion {float(g['compresion']):.2f}, calce "
          f"{float(g['tira_real']):.2f} mm")


def canario_valle(p: dict[str, float]) -> None:
    """Mutaciones dirigidas del apoyo, gap, calce y cadena hasta el marco."""
    g = {
        "apoyo": 2.0, "espesor_apoyo": p["t_valle"], "gap": 0.10,
        "tira_nominal": 0.20, "compresion": 0.10, "tira_real": 0.10,
        "tira_x": (0.0, 2.0), "apoyo_x": (0.0, 2.0),
        "cara_inferior_apoyo": 0.0, "cara_exterior_rail": -0.10,
        "contactos_marco": [0.0, 0.0], "primer_riel": (0.0, 0.0),
        "primer_riel_esperado": (0.0, 0.0), "x_fin": 2.0,
        "panel_x0": 2.0, "z_apoyo": (0.0, 10.0),
        "z_tira": (0.0, 10.0),
        "z_rail": (0.0, 10.0),
    }
    casos = (
        ({"apoyo": 0.0}, "positivo", "apoyo 0"),
        ({"espesor_apoyo": p["t_valle"] - 0.1}, "espesor completo",
         "prolongacion adelgazada"),
        ({"gap": 0.2}, "gap banda", "gap incorrecto"),
        ({"compresion": 0.0}, "compresion", "tira sin comprimir"),
        ({"tira_real": 0.0, "tira_x": (0.0, 0.0)}, "tira ausente",
         "tira ausente"),
        ({"contactos_marco": [0.0, 0.1]}, "dos lados del marco",
         "camino cortado antes del marco"),
        ({"primer_riel": (g["primer_riel"][0] + 0.1,
                           g["primer_riel"][1])},
         "primer riel KONDOR se movio", "primer riel movido"),
    )
    for cambios, clave, que in casos:
        roto = dict(g)
        roto.update(cambios)
        try:
            _guarda_apoyo_valle(p, roto)
        except AssertionError as e:
            assert clave in str(e), (
                f"canario del valle ({que}) salto por '{str(e)}' y no por "
                f"'{clave}'")
            continue
        raise AssertionError(
            f"canario del valle NO disparo con {que}; no confiar en su VERDE")


# LA PESTANA DE LA TAPA DEL VALLE. GEMELAS de pv_*() en sam17_case.scad, y
# tienen que dar lo mismo: el M3 atraviesa la pestana Y la costilla, asi que si
# las dos cuentas se separan el agujero de una pieza no cae sobre el de la otra.
def _pv(p: dict[str, float]) -> dict[str, float]:
    """Plegado de la pestana: setback, bend allowance, deduction y vuelo."""
    sb = p["radio_doblez_valle"] + p["t_valle"]
    ba = math.pi / 2 * (p["radio_doblez_valle"] + p["k_factor"] * p["t_valle"])
    return {"sb": sb, "ba": ba, "bd": 2 * sb - ba,
            "vuelo": p["pestana_valle"] - (2 * sb - ba),
            # profundidad del M3 bajo la cara de arriba: la tangente del doblez
            # cae a SB y desde ahi la regla de chapa pide 2t antes de taladrar.
            "a": sb + 2 * p["t_valle"] + p["d_M3_paso"] / 2}


def _tapa_valle_au(p: dict[str, float]) -> float:
    """Ancho de la banda del valle: muere contra las placas, no contra el
    anillo. GEMELA de tapa_valle_au() en sam17_case.scad."""
    return perfil(p)["ancho_util"] - 2 * p["t_placa"]


def _pv_x(p: dict[str, float], x_fin_banda: float) -> float:
    """X del M3, centrado en los 3D finales del vuelo delantero."""
    return x_fin_banda - 1.5 * p["d_M3_paso"]


def bbox_desarrollo_tapa(p: dict[str, float]) -> tuple[float, float]:
    """Envolvente del DESARROLLO de la tapa del valle, no de la pieza doblada.

    Crece 2*vuelo por el ancho: cada punta saca su pestana desplegada por fuera
    del contorno. Derivado y no escrito a mano -- si el .scad y esta cuenta se
    separan, el bbox se sale del sobre y check_dxf se entera."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    x0 = _x_valle(p, P, cr)[0]
    return (_tapa_valle_au(p) + 2 * _pv(p)["vuelo"],
            _frente_kondor(p, P, cr) - x0 + p["apoyo_valle"])


def autocomprobacion_pv() -> None:
    """El desarrollo de la pestana, a mano.

    Con r = t = 3 y k = 0.42: SB = 6, BA = (pi/2)(3 + 1.26) = 6.6919,
    BD = 12 - 6.6919 = 5.3081. El M3 va a a = 6 + 6 + 1.7 = 13.7 bajo la cara de
    arriba, y en el desarrollo eso cae a BD - a = -8.3919 del contorno, o sea
    8.39 mm POR FUERA. El vuelo de la pestana desplegada son 21 - 5.3081 =
    15.6919, asi que el agujero queda dentro con 7.30 mm de sobra hasta el canto
    libre -- mas de los 5.10 que pide 1.5*D."""
    q = {"radio_doblez_valle": 3.0, "t_valle": 3.0, "k_factor": 0.42,
         "pestana_valle": 21.0, "d_M3_paso": 3.4}
    v = _pv(q)
    for nombre, sale, esperado in (("SB", v["sb"], 6.0),
                                   ("BA", v["ba"], 6.6919),
                                   ("BD", v["bd"], 5.3081),
                                   ("vuelo", v["vuelo"], 15.6919),
                                   ("a", v["a"], 13.7)):
        assert abs(sale - esperado) < 1e-3, (
            f"_pv: {nombre} sale {sale:.4f} y a mano da {esperado}")
    libre = v["vuelo"] - (v["a"] - v["bd"])
    assert abs(libre - 7.3) < 1e-3, f"canto libre {libre:.4f}, a mano 7.30"


def guarda_red(p: dict[str, float]) -> None:
    """La ventana de la entrada de red: que quepa, y que se sepa que es provisional.

    NACE PORQUE NADIE LA MIRABA. El hueco de la entrada de red eran dos literales
    (48 x 27.5) escritos dentro de sam17_case.scad, con su propio comentario
    diciendo "bloque snap-in tipico -- CONFIRMAR contra el datasheet de la pieza
    comprada", y el mismo numero copiado en tres sitios: dos en el .scad y uno
    aqui, en _rejilla_entrada(). Ninguna puerta lo tocaba. Es el mismo patron del
    `- 15` de la trasera, que estaba en cinco sitios y ninguno sabia donde estaba
    el suelo.

    Y CAMBIO DE NATURALEZA el 2026-08-23. Hasta ese dia el conector se encajaba a
    presion en el acrilico, lo cual rompia sin decirlo la regla que la spec del
    case escribe en su §7 -- "las pieles removibles nunca llevan mains" --, porque
    la trasera se quita con 10 M3. Samuel decidio montarlo en una PIEZA FIJA y
    dejar el acrilico con la ventana de paso. Eso mueve la cota critica al metal,
    que se rehace barato; el acrilico, que es lo que no se deshace, se queda con
    un hueco holgado.

    Por eso esta puerta no comprueba que el conector encaje -- ya no encaja aqui.
    Comprueba lo que le toca al acrilico, y son DOS cosas, no tres: que la
    ventana quepa en la banda libre sin comerse el puente, y que no se arrime al
    canto. El puente contra la ranura mas cercana se calcula y se imprime pero
    NO se asevera, porque seria un verde vacio -- ver la nota del punto 2.

    Y IMPRIME de que pieza NO se derivan las cotas. La Schurter KM00.1105.11 SI
    esta elegida (bom-chasis.csv de la fuente v3, hoja typ_KM.pdf) y su snap-in
    agarra chapa de 1 a 2.5 mm: en una plancha de 8 no se monta, y nunca pudo.
    Los 48 x 27.5 de hoy son su recorte girado 90 grados y redondeado a ojo. No
    se "arreglan" a 47 x 28 aqui: esta ventana ya no es un recorte de encaje
    sino un paso, y su cota la decide la pieza fija que aun no existe (#130).

    Su mutacion vive en canario_red(), como manda el Principio VIII."""
    au = _trasera_au(p)
    f_base = _trasera_campo(p)[0]          # la coronacion del labio del talon
    lib0, lib1 = _banda_libre_trasera(p)   # la misma que centra la rejilla
    puente = p["vent_puente_min"]

    # 1. cabe de alto en la banda, y deja puente arriba y abajo. Va centrada,
    #    asi que el margen es el mismo por los dos lados -- se comprueba una vez
    #    y se nombran los dos.
    holgura_v = (lib1 - lib0 - p["iec_alto"]) / 2
    assert holgura_v >= puente, (
        f"la ventana de la entrada de red mide {p['iec_alto']:.1f} mm de alto y "
        f"la banda libre entre el labio del talon y la onda mide {lib1 - lib0:.2f} "
        f"(y={lib0:.2f}..{lib1:.2f}): quedan {holgura_v:.2f} mm de acrilico "
        f"arriba y abajo y el puente minimo son {puente:.1f}. O baja iec_alto, o "
        f"la banda tiene que crecer -- y crecerla mueve vent_separacion, que es "
        f"cota de dibujo, o la fila de M3, que es estructura")

    # 2. el puente contra la ranura mas cercana NO SE ASEVERA, y conviene decir
    #    por que: seria un verde vacio. _columnas_rejilla_entrada() se salta
    #    columnas con la condicion
    #    |x - x_iec| >= (iec_ancho + vent_ancho_ranura)/2 + puente,
    #    y "el puente que queda" es esa misma desigualdad despejada. Aseverarlo
    #    aqui es preguntarle a la regla si cumple la regla: sale verde SIEMPRE,
    #    con cualquier valor de cualquier parametro, incluso con la geometria
    #    rota. Es exactamente lo que prohibe el Principio VIII -- y la primera
    #    version de esta puerta lo tenia escrito como assert, en verde, sin
    #    vigilar nada.
    #
    #    Se calcula igual porque el NUMERO si vale: sale impreso, y una persona
    #    que lo vea encoger sabe que la ventana esta comiendose el campo. Lo que
    #    de verdad protege ese puente es el propio salto de columnas del .scad,
    #    y quien comprueba que el .scad hizo lo que dice es check_dxf.py, que
    #    relee el DXF exportado -- no este guion.
    #    Y SE MIDE CONTRA LA LISTA DE VERDAD desde el 2026-08-28. Aqui habia
    #    una TERCERA copia del filtro de columnas, y le faltaba el de la
    #    escuadra: el margen salia medido contra la primera columna, que el ala
    #    A tapa y el DXF no corta. Ahora la lista la da
    #    _columnas_rejilla_entrada(), la misma que cuenta el area.
    x_iec = au - p["iec_margen_der"] - p["iec_ancho"] / 2
    xs, _, _ = _columnas_rejilla_entrada(p)
    borde = min(abs(x - x_iec) - (p["iec_ancho"] + p["vent_ancho_ranura"]) / 2
                for x in xs)

    # 3. no se arrima al canto derecho de la plancha. Un hueco cerca de un
    #    canto libre en PMMA es el otro sitio donde arranca la fisura.
    assert p["iec_margen_der"] >= puente, (
        f"la ventana de la entrada de red deja {p['iec_margen_der']:.1f} mm "
        f"hasta el canto derecho de la trasera y el minimo son {puente:.1f}")

    print(f"entrada de red: ventana de {p['iec_ancho']:.1f} x {p['iec_alto']:.1f} "
          f"en x={x_iec - p['iec_ancho'] / 2:.2f}..{x_iec + p['iec_ancho'] / 2:.2f}, "
          f"y={lib0 + holgura_v:.2f}..{lib1 - holgura_v:.2f}")
    print(f"  {holgura_v:.2f} mm de puente arriba y abajo, {borde:.2f} contra la "
          f"ranura mas cercana, {p['iec_margen_der']:.1f} al canto derecho")
    print(f"  SIN DERIVAR de la Schurter KM00.1105.11 (hoja typ_KM.pdf p.3: "
          f"recorte 28 x 47, brida 30.5 x 50). Su snap-in agarra chapa de 1 a "
          f"2.5 mm y esta plancha tiene {p['t_piel']:.0f}: aqui NO se encaja")
    print(f"  la sostiene una pieza fija atornillada al pie del talon (#130), "
          f"{lib0 + holgura_v - (f_base + p['rail'] / 2):.2f} mm mas "
          f"abajo -- sin dibujar todavia (#130)")


def canario_trasera(p: dict[str, float]) -> None:
    """Autocomprobacion ROJA de guarda_trasera_flexion(), guarda_talon() y
    guarda_trasera_capturada(): si esto no dispara, su VERDE no vale nada
    (Principio VIII). El revisor del PR #244 (ronda 4) cazo que las mutaciones
    que el PR citaba como prueba de la lengueta eran rojas por otra razon --
    por eso cada caso dice QUE aserto tiene que saltar, y se comprueba por el
    texto del error, no solo por el rojo.

    Y DESDE EL 2026-08-30, EL CASO DE LA PLANCHA SE DERIVA en vez de escribirse
    a mano. Ese caso ya se recalibro dos veces en un dia -- t_piel 7 dejo de
    morder al retroceder la trasera con la rendija, se bajo a 4, y volvio a
    dejar de morder cuando la rendija paso de 3.0 a 4.0 --, y eso no es mala
    suerte: su umbral es el chaflan de la plancha, que se recalcula con el
    bolsillo cada vez que la trasera se mueve. Un canario atado a un numero
    fijo sobre un borde movil se convierte en adorno sin avisar. Este se ata al
    BORDE: la plancha mas gruesa que todavia falla."""
    sordo = io.StringIO()
    # el aserto es c_p <= t_piel - 2, y c_p no depende de t_piel: falla con
    # cualquier plancha por debajo de c_p + 2. Medio milimetro por dentro.
    t_piel_rojo = round(_trasera(p)["chaflan_bajo"] + 2.0 - 0.5, 2)
    # y el del doblez de la pestana, por lo mismo. Su aserto es
    #   plano = tang_ch - (pestana_x + r + t) >= 2 t
    # asi que falla en cuanto r pasa de tang_ch - pestana_x - 3 t. Un cuarto de
    # milimetro por encima. pestana_x se deriva de la cara interior de la
    # trasera, o sea que este borde se mueve cada vez que la plancha se mueve:
    # el 30-08 lo hizo dos veces, y las dos dejaron el caso viejo en verde.
    _tl = _talon(p)
    _t = p["t_costilla"]
    _tang_ch = (_tl["x_chaflan"]
                - (p["radio_doblez_costilla"] + _t) * math.tan(math.radians(22.5)))
    radio_rojo = round(_tang_ch - _tl["pestana_x"] - 3 * _t + 0.25, 2)
    casos = (
        (guarda_trasera_flexion, {"carga_mano": p["carga_mano"] * 1.3},
         "del PMMA", "una mano un 30 % mas pesada pasa del techo del PMMA"),
        (guarda_trasera_flexion, {"talon_pestana_ancho": 12.0, "talon_pestana_alto": 6.0},
         "lengueta", "una lengueta de 12 x 6 fluye con su reaccion en la punta"),
        (guarda_trasera_flexion, {"talon_pestana_n": 2},
         "del PMMA", "dos pestanas dejan la mano baja sobre el techo"),
        (guarda_trasera_flexion, {"alivio_pestana": 12.0},
         "lengueta", "un alivio de 12 deja la raiz de la lengueta en 13.5 y fluye"),
        (guarda_trasera_flexion, {"rebaje_anillo": 2.0},
         "se sale del bolsillo", "embebida 1.85, la cuerda de 2.2 de la plancha combada la saca"),
        # RECALIBRADO EL 2026-08-30. Fue t_piel = 7.0, y dejo de morder: con el
        # labio del bolsillo en 4.5 (lo manda la rendija) el chaflan de la
        # plancha se recalcula y una de 7 SI deja los 2 de canto plano. El
        # borde se recalcula solo. Un canario que dejo de disparar no es un
        # canario, es un adorno -- y este llevaba un dia siendolo sin que nadie
        # lo viera. Por eso ya no lleva numero: lo deriva de t_piel_rojo.
        (guarda_trasera_capturada, {"t_piel": t_piel_rojo},
         "canto plano", f"una plancha de {t_piel_rojo:g} no deja 2 de canto "
         f"plano tras su chaflan de {_trasera(p)['chaflan_bajo']:.2f}"),
        (guarda_talon, {"talon_pestana_aire": 1.5},
         "talon_pestana_aire", "una pestana a menos de tol + 0.5 de la plancha"),
        # RECALIBRADO EL 2026-08-30. Fue 4.5 y quedo verde: al retroceder la
        # trasera 1.5 (rehundido_trasera 3 -> 4.5) la tangente del doblez del
        # chaflan se aparta y sobra plano donde antes no. El barrido de ese dia
        # pone el borde en 4.75; el caso va a 5.0 para no vivir en el filo.
        (guarda_talon, {"radio_doblez_pestana": radio_rojo},
         "de plano", f"un doblez de {radio_rojo:g} se come el plano tras el chaflan"),
    )
    for guarda, cambios, clave, que in casos:
        roto = dict(p)
        roto.update(cambios)
        try:
            with contextlib.redirect_stdout(sordo):
                guarda(roto)
        except AssertionError as e:
            assert clave in str(e), (
                f"canario de la trasera: con {cambios} {guarda.__name__} salto, pero "
                f"por otra razon ('{str(e)[:80]}...') y no por '{clave}'")
            continue
        raise AssertionError(
            f"canario de la trasera NO disparo: con {cambios} hay {que} y "
            f"{guarda.__name__}() lo deja pasar -- no confiar en su VERDE")
    n_huecos = len(_HUECOS)
    with contextlib.redirect_stdout(sordo):
        guarda_talon(dict(p))
        guarda_trasera_capturada(dict(p))
        guarda_trasera_flexion(dict(p))     # y con los parametros buenos, verde
    del _HUECOS[n_huecos:]                   # lo que publique aqui lo publica la corrida real


def canario_techo(p: dict[str, float]) -> None:
    """Autocomprobacion ROJA de las puertas del techo macizo y las chapas
    empotradas (2026-08-30). Mismo contrato que canario_trasera(): llama a la
    puerta OBJETIVO con el dict mutado y comprueba EL TEXTO, no solo el rojo.

    Que llame a la puerta directamente y no pase por main() es lo que hace que
    la prueba valga: da igual que otra puerta salte antes con la misma mutacion
    -- lo que se exige aqui es que ESTA salte, y por SU razon.

    Los casos no se eligieron a mano. Salen del barrido del 2026-08-30
    (scratchpad, `barrido.py`): cada parametro se recorrio en pasos de 0.1 sobre
    su rango util y se anoto donde cambiaba el veredicto. Ese barrido cazo dos
    cosas que a mano no se ven: que el fondo del rebaje solo tiene UN valor
    legal (2 t por abajo, 3:1 por arriba, y las dos paredes en 3), y que un
    reborde de 0.5 disparaba el aserto de esbeltez en vez del suyo -- por eso
    los dos asertos estan hoy en el otro orden."""
    # Y LA COMPRESION DEL TACO. El aserto es subida <= solape - 2 con
    #   subida = 2*gamma/(rho*g*d),  d = aire_labios*(1 - c)
    # asi que falla cuando la luz comprimida baja de d_crit = 2*gamma*1e6 /
    # (rho*g*(solape-2)), o sea cuando c pasa de 1 - d_crit/aire_labios. Este
    # borde se mueve con aire_labios Y con el solape: el 30-08, subir la
    # rendija de 3.0 a 4.0 dejo el caso viejo (0.4) en verde.
    _solape = _trasera(p)["y1"] - _y_labio_techo(p)
    _d_crit = 2 * GAMMA_AGUA * 1e6 / (RHO_AGUA * G * (_solape - 2.0))
    compresion_roja = round(1.0 - _d_crit / p["aire_labios"] + 0.03, 3)
    _subida = 2 * GAMMA_AGUA * 1e6 / (RHO_AGUA * G
                                      * p["aire_labios"] * (1 - p["compresion_taco"]))
    labio_rojo = round(p["techo_labio"] - (_solape - 2.0 - _subida) - 0.5, 2)
    sordo = io.StringIO()
    casos = (
        (guarda_rebaje_chapa, {"rebaje_chapa": _borde_rojo(
            guarda_rebaje_chapa, p, "rebaje_chapa", p["rebaje_chapa"], 0.5,
            "capturada")},
         "capturada", "un rebaje poco hondo no captura el canto de la chapa"),
        (guarda_rebaje_chapa, {"rebaje_chapa": _borde_rojo(
            guarda_rebaje_chapa, p, "rebaje_chapa", p["rebaje_chapa"], 8.0,
            "la fresa no pasa")},
         "la fresa no pasa", "un rebaje muy hondo deja el reborde demasiado esbelto"),
        (guarda_rebaje_chapa, {"rehundido_chapa": 0.5},
         "por debajo de 1", "un reborde de 0.5 es una rebaba, no una junta"),
        (guarda_rebaje_chapa, {"hol_chapa": 0.2},
         "no entra si viene larga", "0.2 no deja entrar una chapa cortada a +-0.3"),
        (guarda_rebaje_chapa, {"hol_chapa": _borde_rojo(
            guarda_rebaje_chapa, p, "hol_chapa", p["hol_chapa"], 4.0,
            "capturada")},
         "capturada", "pasada esa holgura la chapa deja de estar capturada en z"),
        (guarda_rebaje_chapa, {"aire_labios": 2.4},
         "la fresa", "con la rendija a 2.4 el rebaje mide 2.9 y la fresa es de 3"),
        (guarda_tramo_trasero, {"pared_rebaje_trasera": 2.0},
         "pared de 2 contra 3", "una pared de 2 entre dos vaciados se rompe al fresar"),
        (guarda_tramo_trasero, {"rebaje_anillo": 5.0},
         "el labio del bolsillo queda", "con 5 de bolsillo el labio se queda en 2 bajo la chapa"),
        # LA RENDIJA TENIA AQUI DOS CANARIOS Y SE MUDAN ABAJO (2026-09-03). Los
        # dos --taco_largo casi continuo, y potencia_disipada por encima de lo
        # que cabe-- se colgaban del aserto "sobre ambiente" de guarda_aire(),
        # y ese aserto ya no existe: con los 151.55 W del cajon el techo no se
        # cumple y la puerta lo publica como HUECO. _borde_rojo() sobre un
        # aserto que no muerde revienta con "el aserto no muerde", que es su
        # trabajo. Su SUJETO sigue vivo --que ahogar la salida se note, que la
        # potencia mande-- asi que se comprueba sobre los numeros de _tiro() y
        # sobre el hueco, dos lados, mas abajo.
        # DERIVADO TAMBIEN (2026-08-30, ronda 2 del revisor). Estaba fijo en 18
        # y con solo subir aire_labios a 4.2 se quedaba verde: el labio que hace
        # falta depende de cuanto sube el agua, y eso depende de la luz. El
        # aserto es subida <= solape - 2, y solape = labio + chaflan - (P5.y -
        # y1), asi que falla cuando el labio baja de labio_actual - (solape -
        # 2 - subida). Medio milimetro por debajo.
        (guarda_rendija, {"techo_labio": labio_rojo},
         "el agua sube", f"con el labio en {labio_rojo:g} el solape no tapa lo "
         f"que el agua sube por la rendija comprimida"),
        # Y UNO PARA taco_n, que no tenia: sin tacos no hay rendija.
        (guarda_aire, {"taco_n": 0.0},
         "sin tacos NO HAY RENDIJA", "quitar los tacos no ensancha la salida, la elimina"),
        (guarda_rendija, {"compresion_taco": compresion_roja},
         "el agua sube", f"un taco que cede el {compresion_roja*100:.0f} % "
         f"estrecha la rendija por debajo de los {_d_crit:.2f} mm que el "
         f"solape de {_solape:.1f} aguanta"),
        # LA BRIDA EN SU CAJEADO. El primero es el que justifica que el fondo
        # del rebaje no pueda crecer "un poco mas" para tener holgura de
        # fresado: se come la pletina bajo las roscas ciegas. Que esta mutacion
        # tambien ponga roja a guarda_rebaje_chapa da igual -- el canario llama
        # a guarda_miembro_alto DIRECTAMENTE, que es para lo que existe.
        (guarda_miembro_alto, {"rebaje_chapa": 6.5},
         "de pletina", "con un cajeado de 6.5 quedan 7.5 de pletina bajo los M4 ciegos"),
        (guarda_miembro_alto, {"radio_brida": 1.0},
         "no asienta", "una brida a R1 se monta sobre el R1.5 que deja la fresa"),
    )
    for guarda, cambios, clave, que in casos:
        roto = dict(p)
        roto.update(cambios)
        try:
            with contextlib.redirect_stdout(sordo):
                guarda(roto)
        except AssertionError as e:
            assert clave in str(e), (
                f"canario del techo: con {cambios} {guarda.__name__} salto, pero "
                f"por otra razon ('{str(e)[:80]}...') y no por '{clave}'")
            continue
        raise AssertionError(
            f"canario del techo NO disparo: con {cambios} hay {que} y "
            f"{guarda.__name__}() lo deja pasar -- no confiar en su VERDE")
    n_huecos = len(_HUECOS)
    with contextlib.redirect_stdout(sordo):
        guarda_rebaje_chapa(dict(p))          # y con los parametros buenos, verde
        guarda_tramo_trasero(dict(p))
        guarda_rendija(dict(p))
        guarda_aire(dict(p))
    # LA PUERTA DEL AIRE VUELVE A JUZGAR (2026-10-12), y tiene que morder por su
    # razon. Un 5 % por encima de lo que la chimenea evacua al techo el salto
    # pasa del techo (va con la potencia a la 2/3): derivado de la chimenea, no
    # escrito a mano.
    t = _tiro(p)
    roja = round(t["p_evacuada"] * 1.05, 2)
    try:
        with contextlib.redirect_stdout(sordo):
            guarda_aire({**p, "potencia_disipada": roja})
    except AssertionError as e:
        assert "sobre ambiente" in str(e), (
            f"canario del aire: con {roja} W guarda_aire() salto, pero por otra "
            f"razon ('{str(e)[:80]}...')")
    else:
        raise AssertionError(
            f"canario del aire NO disparo: con {roja} W dentro y "
            f"{t['p_evacuada']:.1f} evacuables al techo, guarda_aire() lo deja "
            f"pasar -- no confiar en su VERDE")
    # LOS HUECOS DEL AIRE MIRAN LA CARGA, por los dos lados. Con una carga que
    # la puerta deja pasar pero que ya no cabe con un costado tapado, ni en la
    # sala de 45 C con el pesimista, se publican los dos; con 1 W, ninguno. Un
    # hueco que se publica siempre no avisa de nada, y uno que no se publica
    # nunca se lleva la decision que nombra. La carga sale de la chimenea, a
    # medio camino entre el umbral mas alto de los dos y lo que la puerta
    # aguanta: con la de hoy el de la sala se publica con 2 W de holgura, y la
    # de hoy es cota de abajo (enmienda M1 de la v5).
    techo = p["salto_termico_max"]
    # Las dos cargas salen de la chimenea con el pesimista, que es como la
    # puerta juzga los dos huecos desde el papel del suelo.
    w_sala = _potencia_a(p, techo * T_AMB / T_SALA_DISENO_K, CD_TIRO_PESIMISTA,
                         canal=CANAL_BASE_PESIMISTA)
    w_costado = _potencia_a(p, techo, CD_TIRO_PESIMISTA, costados=1,
                            canal=CANAL_BASE_PESIMISTA)
    w_media = round((max(w_sala, w_costado) + t["p_evacuada"]) / 2, 2)
    n_media = len(_HUECOS)
    with contextlib.redirect_stdout(sordo):
        guarda_aire({**p, "potencia_disipada": w_media})
    for texto in ("holgura de los costados", "sala de diseno"):
        assert any(texto in h for h in _HUECOS[n_media:]), (
            f"canario del aire: con {w_media} W el case pasa la puerta pero no "
            f"cabe con un costado tapado ({w_costado:.1f} W) ni en la sala de "
            f"45 C con el pesimista ({w_sala:.1f} W), y guarda_aire() NO publico "
            f"el hueco de '{texto}' -- su silencio no vale")
    # Y JUZGA EL PESIMISTA, no el nominal. w_media queda por encima del umbral
    # nominal del costado, asi que con ella un guarda_aire() que volviera al
    # nominal seguiria publicando el hueco y nadie lo veria (revision final del
    # suelo). Entre el umbral nominal y el pesimista el nominal calla y el
    # pesimista publica: ahi es donde el hueco decide algo, y por eso la carga
    # se toma a medio camino de los dos, en cada uno de los dos huecos.
    for texto, w_pes, w_nom in (
            ("holgura de los costados", w_costado,
             _potencia_a(p, techo, costados=1)),
            ("sala de diseno", w_sala,
             _potencia_a(p, techo * T_AMB / T_SALA_DISENO_K))):
        w_entre = round((w_pes + w_nom) / 2, 2)
        n_entre = len(_HUECOS)
        with contextlib.redirect_stdout(sordo):
            guarda_aire({**p, "potencia_disipada": w_entre})
        assert any(texto in h for h in _HUECOS[n_entre:]), (
            f"canario del aire: con {w_entre} W, entre el umbral nominal "
            f"({w_nom:.1f} W) y el pesimista ({w_pes:.1f} W), guarda_aire() NO "
            f"publico el hueco de '{texto}': lo esta juzgando con el nominal, y "
            f"con el nominal el hueco calla justo donde el pesimista lo ve")
    n_verde = len(_HUECOS)
    with contextlib.redirect_stdout(sordo):
        guarda_aire({**p, "potencia_disipada": 1.0})
    assert len(_HUECOS) == n_verde, (
        f"canario del aire: con 1 W guarda_aire() sigue publicando "
        f"'{_HUECOS[-1][:60]}...' -- un hueco que no mira la carga no avisa de "
        f"nada y no se apagaria nunca")
    # Y QUE LA CHIMENEA VEA LO QUE HAY: tapar un costado, acortar el paso de la
    # persiana (si la cache devolviera las franjas de otra geometria, esto no
    # se moveria) y ahogar la rendija con una tira casi continua suben el salto.
    assert _tiro(p, costados=1)["dt"] > t["dt"] + 1.0, (
        f"canario del aire: con un costado tapado el salto no sube de "
        f"{t['dt']:.1f} K -- _tiro() no esta mirando las persianas")
    otro_paso = _tiro({**p, "paso_persiana": p["paso_persiana"] - 1.0})
    assert otro_paso["dt"] > t["dt"] + 0.5, (
        f"canario del aire: con la persiana a paso {p['paso_persiana'] - 1.0:g} "
        f"el salto da {otro_paso['dt']:.2f} K contra {t['dt']:.2f} -- la chimenea "
        f"no ve la geometria de la persiana")
    ahogado = _tiro({**p, "taco_largo": 89.0})
    assert ahogado["dt"] > t["dt"] + 0.1, (
        f"canario del aire: con los tacos vueltos una tira de 89 mm la rendija "
        f"se ahoga y el salto no sube ({ahogado['dt']:.2f} contra "
        f"{t['dt']:.2f} K) -- _tiro() no esta mirando la rendija")
    sin_base = _tiro({**p, "alto_pie": 0.5})
    assert sin_base["dt"] > t["dt"] + 1.0, (
        f"canario del aire: con las patas aplastadas a 0.5 mm el salto da "
        f"{sin_base['dt']:.2f} K contra {t['dt']:.2f} -- _tiro() no esta "
        f"mirando la base")
    del _HUECOS[n_huecos:]


def canario_red(p: dict[str, float]) -> None:
    """Autocomprobacion ROJA de guarda_red(): si esto no dispara, su VERDE no
    vale nada (Principio VIII).

    Se rompe la geometria a proposito por los DOS lados que la puerta asevera y
    se exige que salte; y despues se corre con los parametros de verdad y se
    exige que NO salte, que es la mitad que se olvida y la que caza un canario
    que dispara siempre.

    Las mutaciones no son numeros bonitos: son el modo de fallo real de cada
    aserto. La ventana crece hasta comerse el puente contra la onda -- que es lo
    que pasaria el dia que se elija una pieza mas alta que la inventada, o sea
    el desenlace mas probable del #130 -- y la ventana se arrima al canto
    derecho, que es donde el PMMA raja."""
    lib0, lib1 = _banda_libre_trasera(p)
    banda = lib1 - lib0
    sordo = io.StringIO()

    # el puente arriba y abajo es (banda - iec_alto)/2, asi que basta con que
    # iec_alto pase de banda - 2*puente para que el aserto 1 tenga que saltar
    alto_roto = banda - 2 * p["vent_puente_min"] + 0.5
    casos = (("iec_alto", alto_roto,
              "una ventana que se come el puente contra la onda"),
             ("iec_margen_der", p["vent_puente_min"] - 0.5,
              "una ventana pegada al canto derecho"))
    for clave, valor, que in casos:
        roto = dict(p)
        roto[clave] = valor
        try:
            with contextlib.redirect_stdout(sordo):
                guarda_red(roto)
        except AssertionError:
            continue
        raise AssertionError(
            f"canario de red NO disparo: con {clave}={valor:.2f} hay {que} y "
            f"guarda_red() la deja pasar — no confiar en su VERDE")

    with contextlib.redirect_stdout(sordo):
        guarda_red(dict(p))          # y con la geometria buena, verde


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
    print(f"fresado: ranura {p['vent_ancho_ranura']:.2f} y concavo minimo "
          f"{p['radio_valle']:.1f} contra fresa de {p['fresa_d']:.1f} "
          f"(radio {r:.1f}) -- sin cambio de util")


def guarda_puentes_ventilacion(p: dict[str, float]) -> None:
    """El puente que queda entre dos huecos aguanta el espesor de SU pieza.

    LA REGLA es la de siempre en plancha perforada: un puente mas fino que 0.8
    veces el espesor se dobla al manipular la pieza, y en PMMA es ademas por
    donde arranca la fisura. Lo que cambio el 2026-08-28 no es la regla: es a
    QUIEN se le aplica.

    ESTUVO ESCRITA CONTRA UNA PIEZA SIN AGUJEROS. Era una sola linea suelta en
    main() -- `vent_puente_min >= 0.8*t_valle` -- de cuando el campo de ranuras
    vivia en la banda del valle. Esa banda es MACIZA desde que las ranuras se
    mudaron a la meseta (ver valle_paso_hp en params.scad): hoy t_valle es el
    espesor de una tapa que no se perfora, asi que la puerta comparaba un
    puente contra un espesor que no tiene nada que ver con el.

    Y mientras tanto las dos rejillas que SI existen no las miraba nadie:

        trasera   PMMA de t_piel,      44 columnas a paso valle_paso_hp
        meseta    chapa de t_costilla, 16 ranuras a paso meseta_paso_hp

    Se mide donde hay ranuras, y con los puentes de verdad, que son DOS por
    pieza y salen de sitios distintos:

      * ENTRE COLUMNAS: paso menos ancho de ranura. Es GEOMETRIA -- no hay
        parametro que lo diga --, y es el puente que rompe el manipulado.
      * CONTRA CUALQUIER OTRO HUECO: vent_puente_min. Es la cota con la que
        _rejilla_entrada() se salta columnas junto a la ventana de red y con
        la que guarda_red() separa esa ventana de la onda; si no aguanta el
        espesor, esos dos huecos se comen el material que queda entre ellos.

    LO QUE COSTO PONERLA BIEN, para que no se deshaga por comodidad: con la
    regla apuntando a la pieza correcta el diseno salio ROJO por los dos lados
    de la trasera, y la fuente se movio en params.scad -- vent_ancho_ranura de
    4 a 3.75 y vent_puente_min de 4 a 6.5 --, no el umbral. Eso encoge la
    salida de aire y guarda_aire() lo cobra en salto termico."""
    # LA MESETA SALIO DE ESTA LISTA EL 2026-08-30, con sus ranuras. Queda UNA
    # pieza ranurada, la trasera. Y esto es lo que hay que mirar cuando una
    # puerta pierde un sujeto: no basta con que la regla siga siendo verdad --
    # medir el puente entre 16 ranuras que ya no se cortan es una puerta verde
    # sobre un muerto. meseta_paso_hp sigue en params.scad, pero como
    # referencia del techo VIEJO (el test de rotura de check_dxf lo reconstruye
    # con el), no como una cota que este presupuesto vigile.
    for pieza, paso_hp, t in (
            ("trasera", p["valle_paso_hp"], p["t_piel"]),):
        minimo = 0.8 * t
        entre = paso_hp * p["hp"] - p["vent_ancho_ranura"]
        assert entre >= minimo - 1e-9, (
            f"la rejilla de la {pieza} deja {entre:.2f} mm de puente entre "
            f"columnas ({paso_hp:.0f} HP = {paso_hp * p['hp']:.2f} menos la "
            f"ranura de {p['vent_ancho_ranura']:.2f}) sobre un espesor de "
            f"{t:.1f}: el minimo son {minimo:.2f} (0.8 x espesor). O el paso "
            f"sube, o la ranura adelgaza -- el umbral no se toca")
        assert p["vent_puente_min"] >= minimo - 1e-9, (
            f"vent_puente_min={p['vent_puente_min']:.2f} no aguanta el "
            f"espesor de la {pieza} ({t:.1f}): el minimo son {minimo:.2f}. "
            f"Es el aire que la rejilla le deja a los OTROS huecos de la "
            f"pieza -- hoy la ventana de la entrada de red")
    print(f"puentes de ventilacion: trasera "
          f"{p['valle_paso_hp'] * p['hp'] - p['vent_ancho_ranura']:.2f} mm "
          f"entre columnas sobre PMMA de {p['t_piel']:.0f} (minimo "
          f"{0.8 * p['t_piel']:.2f}), vent_puente_min "
          f"{p['vent_puente_min']:.2f}. La meseta ya no lleva ranuras: su "
          f"salida es la rendija del alero (guarda_rendija)")




# Inercia de un 2020 ranurado de catalogo. SUPUESTO DECLARADO: cifra de oficio,
# no de hoja de datos. Va aqui y no en params.scad porque es la pieza que se
# JUBILA -- es el liston contra el que se mide su sustituto, no una cota del
# case. Si el proveedor publica la suya y es otra, este numero se cambia y las
# secciones de los miembros se recalculan solas.
def _perimetro(P: list[tuple[float, float]]) -> float:
    return sum(math.hypot(P[(i + 1) % len(P)][0] - P[i][0],
                          P[(i + 1) % len(P)][1] - P[i][1]) for i in range(len(P)))


def _bd_miembro(p: dict[str, float]) -> float:
    """Bend deduction de un doblez a 90 en la chapa de los miembros: la
    misma cuenta que miembro_bd() en el .scad."""
    sb = p["radio_doblez_costilla"] + p["t_costilla"]
    ba = math.pi / 2 * (p["radio_doblez_costilla"] + p["k_factor"] * p["t_costilla"])
    return 2 * sb - ba


def _miembro_alto(p: dict[str, float]) -> dict:
    """El techo: meseta y, por detras, chaflan + labio (B) o banda (A), en
    t_costilla, y lo que aguanta SOLO con carga_mano al centro.

    Seccion por rectangulos en el plano del perfil (el chaflan como tira
    vertical de su alto, que es conservador): inercia por paralelas-a-ejes,
    tension en la fibra mas lejana del eje neutro, flecha biapoyada de
    ancho_util. GEMELA de la cuenta de guarda_miembro_alto()."""
    P = _vertices(p)
    t = p["t_costilla"]
    c, lab = p["chaflan_nariz"], p["techo_labio"]
    yt = P[5][1]
    # (ancho, alto, y del centro)
    if _chaflan_p5(p):
        rects = [(p["prof_sup"] - c, t, yt - t / 2),
                 (t, c, yt - c / 2),
                 (t, lab, yt - c - lab / 2)]
    else:
        rects = [(p["prof_sup"], t, yt - t / 2),
                 (t, p["banda_trasera"], yt - p["banda_trasera"] / 2)]
    A = sum(b * h for b, h, _ in rects)
    yb = sum(b * h * y for b, h, y in rects) / A
    inercia = sum(b * h ** 3 / 12 + b * h * (y - yb) ** 2 for b, h, y in rects)
    y_max = max(max(abs(y + h / 2 - yb), abs(y - h / 2 - yb)) for _, h, y in rects)
    au = perfil(p)["ancho_util"]
    F = p["carga_mano"]
    M = F * au / 4
    return {"I": inercia, "yb": yb, "sigma": M * y_max / inercia,
            "flecha": F * au ** 3 / (48 * E_ALUMINIO * inercia),
            "x_dob": P[6][0] - t, "rects": rects,
            "y_labio": _y_labio_techo(p)}


def _talon(p: dict[str, float]) -> dict:
    """El talon, la nariz de atras: pie sobre la tabla del canto libre al pie
    del chaflan, chaflan a 45 sobre P6 y labio vertical a ras del plano
    trasero. Tres M4 en el pie y talon_pestana_n pestanas lanzadas detras del
    canto de abajo de la trasera. GEMELA de talon_*() en el .scad."""
    P = _vertices(p)
    c, t = p["chaflan_nariz"], p["t_costilla"]
    xp = P[6][0]
    x_ch = xp - c
    x_pie = x_ch - p["talon_pie"]
    au = perfil(p)["ancho_util"]
    tr = _trasera(p)
    # el alivio va centrado en el corte (a w/2 + k/2 del eje de la pestana) y
    # lo que pasa de medio corte lo muerde a la raiz de la pestana por dentro,
    # y ensancha la ventana por fuera. Radio de la PIEZA, alivio/2: el .scad
    # dibuja alivio + kerf para que el taladro SALGA a alivio (params.scad,
    # kerf); la seccion que resiste es la cortada, no la dibujada. Con kerf
    # distinto de 0 el corte en U, que no se compensa, tambien se lleva
    # |kerf|/2 de cada canto de la pestana: lo avisa el AMARILLO del kerf
    k, r_al = p["corte_pestana"], p["alivio_pestana"] / 2
    return {"x_band": xp - t, "x_chaflan": x_ch, "x_pie": x_pie,
            "pestana_raiz": p["talon_pestana_ancho"] - 2 * max(0.0, r_al - k / 2),
            "pestana_ventana": p["talon_pestana_ancho"] / 2 + max(k, k / 2 + r_al),
            "contorno": [(x_pie, 0.0), (x_ch, 0.0), (xp, c),
                         (xp, c + p["talon_labio"])],
            "m4_x": x_pie + _m4_pie_borde(p),
            "m4_z": [p["t_anillo"] + au * f for f in (0.25, 0.5, 0.75)],
            "pestana_x": tr["x0"] - p["talon_pestana_aire"],
            "pestana_z": [p["t_anillo"] + au * (2 * i + 1) / (2 * p["talon_pestana_n"])
                          for i in range(int(round(p["talon_pestana_n"])))],
            "pestana_dev": p["talon_pestana_alto"] + t - _bd_pestana(p),
            # EL BLANK MIDE LO QUE ENTRA EN REBAJE (2026-08-30), no lo que hay
            # entre caras: el labio y el chaflan van empotrados y ganan 5.3.
            # "largo_pie" es lo que queda tras la muesca, y es lo que apoya.
            "largo": _chapa_largo_rebaje(p),
            "largo_pie": _entre_anillos(p),
            "muesca": _muesca_pie(p),
            "desarrollo": (p["talon_labio"] + c * math.sqrt(2) + p["talon_pie"]
                           - 2 * _bd_angulo(p, 45.0)),
            "z0": p["t_anillo"] + p["hol_piel"],
            "z1": p["ancho_total"] - p["t_anillo"] - p["hol_piel"]}


def bbox_desarrollo_miembro(p: dict[str, float], cual: str) -> tuple[float, float]:
    """Envolvente del blank de cada chapa trasera, como la ve el laser: mas
    grande que la pieza doblada.

    El techo tumba retorno, meseta y -- en B -- chaflan y labio (un doblez de
    45 - angulo, dos de 45), o -- en A -- la banda (uno de 90), y saca sus dos
    bridas por las puntas. El talon tumba labio, chaflan y pie (dos de 45) y
    mide lo que hay entre anillos."""
    bd90, bd45 = _bd_miembro(p), _bd_angulo(p, 45.0)
    if cual == "trasero alto":
        # LO QUE ENTRA EN REBAJE (2026-08-30): el techo tambien se empotra, y
        # su blank crece 5.0 sobre el ancho_util de antes. Las bridas siguen
        # saliendo de las puntas de ESE ancho.
        au = _chapa_largo_rebaje(p)
        alto = p["retorno_meseta"] - _bd_angulo(p, 90.0 - p["angulo_superior"])
        if _chaflan_p5(p):
            alto += (p["prof_sup"] - p["chaflan_nariz"]
                     + p["chaflan_nariz"] * math.sqrt(2) + p["techo_labio"]
                     - 2 * bd45)
        else:
            alto += p["prof_sup"] + p["banda_trasera"] - bd90
        return (au + 2 * (p["brida_largo"] - bd90), alto)
    return (_talon(p)["largo"], _talon(p)["desarrollo"])


def guarda_miembro_alto(p: dict[str, float]) -> None:
    """El techo se sostiene SOLO y sus bridas caen en macizo.

    SUSTITUYE A guarda_miembros() (2026-08-29, noche), que comparaba la
    inercia de cada canal con la del 2020 que jubilo. Aqui la carga es
    carga_mano en el centro de la meseta sobre la chapa SOLA -- sin la
    trasera, que ya no se atornilla a nada --, y se exige que no fluya
    (RP02_ALUMINIO) y se publica cuanto cede.

    Y la brida: cabe en el labio (o la banda) con la meseta encima, sus dos
    M4 a 2 D uno de otro y a 1.5 D de su canto de arriba, y EL DE DENTRO A
    1.5 D DE BROCA DE LA PARED DEL BOLSILLO DE LA TRASERA (2026-08-29, noche,
    2): con el bolsillo saliendo por arriba obligo a brida_largo = 34; cerrado
    8.5 por debajo de las roscas, pasa con 27. En B la brida sube por encima
    del labio, junto a la tira del chaflan: se publica el relieve."""
    m = _miembro_alto(p)
    P = _vertices(p)
    t = p["t_costilla"]
    como = ("chaflan de " + f"{p['chaflan_nariz']:g} + labio de {p['techo_labio']:g}"
            if _chaflan_p5(p) else f"banda de {p['banda_trasera']:g}")
    assert m["sigma"] <= RP02_ALUMINIO, (
        f"el techo SOLO -- meseta {p['prof_sup']:g} y {como} en {t:g} -- trabaja "
        f"a {m['sigma']:.0f} MPa con {p['carga_mano']:.0f} N en el centro de la "
        f"meseta, contra {RP02_ALUMINIO:.0f} de Rp0.2")
    b = _bridas(p)[0]
    alto_cara = (P[5][1] - m["y_labio"])
    assert p["brida_ancho"] + t <= alto_cara, (
        f"la brida mide {p['brida_ancho']:g} mas los {t:g} de la meseta y por "
        f"detras el techo solo tiene {alto_cara:g}")
    s_in, s_out = b["s_m4"]
    assert s_out - s_in >= 2 * p["d_M4_paso"], (
        f"los dos M4 de la brida estan a {s_out - s_in:.2f}; 2 D son "
        f"{2 * p['d_M4_paso']:.2f}")
    assert p["dist_rosca_ciega"] - t >= 1.5 * p["d_M4_paso"], (
        f"el M4 de la brida cae a {p['dist_rosca_ciega'] - t:.2f} de su canto de "
        f"arriba (dist_rosca_ciega - t_costilla) y pide "
        f"{1.5 * p['d_M4_paso']:.2f}")
    # EL BOLSILLO DE LA TRASERA SE CIERRA POR DEBAJO DE LAS ROSCAS DE LA
    # BRIDA: corre por la misma franja de la cara interior, y una rosca que
    # cayera sobre el o a menos de 1.5 D de su fin saldria por el.
    bo = _bolsillo_trasero(p)
    minimo = 1.5 * p["d_M4_rosca"]
    for i, c in enumerate(b["m4"]):
        assert c[1] - bo["y_fin"] >= minimo - 1e-9, (
            f"el M4 {i} de la brida cae en y={c[1]:.2f} y el bolsillo de la "
            f"trasera se cierra en y={bo['y_fin']:.2f}: a {c[1] - bo['y_fin']:.2f}, "
            f"y la broca pide {minimo:.2f}")
    # y el CUERPO de la brida, tumbado en esa misma cara, no comparte arista
    # con el fin del bolsillo: 1.0 de cara entera entre los dos
    assert b["rect"][2] - bo["y_fin"] >= 1.0 - 1e-9, (
        f"el canto de abajo de la brida (y={b['rect'][2]:.2f}) y el fin del "
        f"bolsillo de la trasera (y={bo['y_fin']:.2f}) se llevan "
        f"{b['rect'][2] - bo['y_fin']:.2f}; se pide 1.0 de cara entre los dos")
    # --- LA BRIDA EN SU CAJEADO (2026-08-30) --------------------------------
    # Dejo de apoyar en la cara del anillo y apoya en un cajeado de
    # rebaje_chapa de fondo. El cambio va en la direccion segura -- se aleja de
    # la envolvente estatica del panel fijo, ver el bloque de brida_largo en
    # params.scad -- pero se paga en pletina bajo las roscas ciegas.
    pletina = p["t_anillo"] - p["rebaje_chapa"]
    assert pletina >= 8.0 - 1e-9, (
        f"bajo el suelo del cajeado de la brida quedan {pletina:g} de pletina "
        f"(t_anillo {p['t_anillo']:g} - rebaje_chapa {p['rebaje_chapa']:g}) y "
        f"ahi van dos M4 ciegos: se piden 8 para que la rosca tenga hilos y el "
        f"anillo no se abra por detras")
    # El cajeado es la huella de la brida mas hol_chapa por lado, en las dos
    # direcciones. Si fueran distintas, la brida se posicionaria por el lado
    # apretado y el rebaje dejaria de ser el que manda.
    caj_l = p["brida_largo"] + 2 * p["hol_chapa"]
    caj_a = p["brida_ancho"] + 2 * p["hol_chapa"]
    assert caj_l > p["brida_largo"] and caj_a > p["brida_ancho"], (
        f"el cajeado de la brida ({caj_l:g} x {caj_a:g}) no deja holgura sobre "
        f"su huella ({p['brida_largo']:g} x {p['brida_ancho']:g})")
    # Y LA BRIDA VA REDONDEADA MAS QUE SU CAJEADO: la fresa deja las esquinas
    # interiores a fresa_d/2, y una brida de esquina viva no asienta en ellas
    # -- se queda montada sobre el radio y trabaja en voladizo.
    assert p["radio_brida"] >= p["fresa_d"] / 2 - 1e-9, (
        f"la brida lleva esquinas de R{p['radio_brida']:g} y el cajeado, "
        f"fresado con Ø{p['fresa_d']:g}, las deja en R{p['fresa_d']/2:g}: la "
        f"brida se monta sobre el radio y no asienta")
    # Y POR ARRIBA (2026-08-30, tras el revisor): un radio grande se come la
    # esquina donde va el M4 de dentro, que esta a brida_raiz del doblez. Con
    # el radio pasado de la mitad del ancho la brida deja de ser un rectangulo
    # redondeado y pasa a ser un ovalo, y su huella ya no cubre el cajeado.
    assert p["radio_brida"] <= p["brida_ancho"] / 2 - 1e-9, (
        f"la brida lleva R{p['radio_brida']:g} sobre un ancho de "
        f"{p['brida_ancho']:g}: pasado el medio ancho deja de ser un "
        f"rectangulo redondeado, y su huella no cubre el cajeado")

    relieve = (P[5][1] - t) - (m["y_labio"] + p["techo_labio"]) if _chaflan_p5(p) else 0.0
    au = perfil(p)["ancho_util"]
    print(f"techo: meseta {p['prof_sup']:g} y {como} en {t:g}, I={m['I']:.0f} mm4; "
          f"SOLO con {p['carga_mano']:.0f} N al centro de {au:.2f} cede "
          f"{m['flecha']:.2f} mm y trabaja a {m['sigma']:.0f} MPa (Rp0.2 "
          f"{RP02_ALUMINIO:.0f}); meseta maciza, sin canal ni paso de agua")
    print(f"  brida de {p['brida_largo']:g} x {p['brida_ancho']:g} (R"
          f"{p['radio_brida']:g}) en un cajeado de {caj_l:g} x {caj_a:g} x "
          f"{p['rebaje_chapa']:g} en la cara interior del anillo, con "
          f"{pletina:g} de pletina bajo sus roscas, "
          f"bajo la muesca del marco; M4 a {s_in:.2f} y {s_out:.2f} del "
          f"doblez, {b['m4'][0][1] - bo['y_fin']:.2f} por encima del fin del "
          f"bolsillo de la trasera"
          + (f"; relieve de {relieve:.2f} junto al chaflan" if relieve > 0 else ""))


# El PMMA colado como material: modulo, Poisson y el radio del disco sobre el
# que se reparte carga_mano (una mano apoyada, no una punta: con carga puntual
# la teoria de placas da tension infinita). Viven aqui, junto a SIGMA_PMMA,
# porque tuvieron DOS clientes: guarda_costado() en check_dxf.py (hasta el
# 2026-10-11, cuando la mejilla se fue con la persiana) y
# guarda_trasera_flexion() aqui. Hasta el 2026-08-30 estaban dos veces, con
# dos nombres y dos justificaciones.
E_PMMA = 3000.0       # MPa
NU_PMMA = 0.37
R_CONTACTO = 10.0     # mm


def _levy_base(k: float, y, y0: float, y1: float):
    """Base escalada de la ODE de Levy en el tramo [y0, y1]: e^-k(y-y0),
    (y-y0) e^-k(y-y0), e^-k(y1-y), (y1-y) e^-k(y1-y), y sus tres derivadas
    (4 derivadas x 4 funciones x puntos). Escalada para que k b grande no
    reviente el condicionamiento."""
    import numpy as np
    y = np.asarray(y, float)
    s = y - y0
    r = y1 - y
    e1 = np.exp(-k * s)
    e2 = np.exp(-k * r)
    k2, k3 = k * k, k ** 3
    return np.array([
        [e1, -k * e1, k2 * e1, -k3 * e1],
        [s * e1, (1 - k * s) * e1, (-2 * k + k2 * s) * e1, (3 * k2 - k3 * s) * e1],
        [e2, k * e2, k2 * e2, k3 * e2],
        [r * e2, (-1 + k * r) * e2, (-2 * k + k2 * r) * e2, (-3 * k2 + k3 * r) * e2],
    ]).transpose(1, 0, 2)          # [derivada, funcion, punto]


def _levy_Y(k: float, eta: float, b: float, D: float, nu: float, ys):
    """Y(y) e Y''(y) del modo k para q_m = delta(y - eta), con los dos bordes
    y = 0 e y = b LIBRES (M_y = 0, V_y = 0). Dos tramos, ocho constantes:
    continuidad de Y, Y', Y'' en eta y salto 1/D en la tercera derivada."""
    import numpy as np
    M = np.zeros((8, 8))
    rhs = np.zeros(8)
    for row, (y, y0, y1, c0) in ((0, (0.0, 0.0, eta, 0)), (2, (b, eta, b, 4))):
        B = _levy_base(k, [y], y0, y1)[:, :, 0]
        M[row, c0:c0 + 4] = B[2] - nu * k * k * B[0]
        M[row + 1, c0:c0 + 4] = B[3] - (2 - nu) * k * k * B[1]
    BA = _levy_base(k, [eta], 0.0, eta)[:, :, 0]
    BB = _levy_base(k, [eta], eta, b)[:, :, 0]
    for d in range(4):
        M[4 + d, 0:4] = BA[d]
        M[4 + d, 4:8] = -BB[d]
    rhs[7] = -1.0 / D
    C = np.linalg.solve(M, rhs)
    ys = np.asarray(ys, float)
    Y = np.empty(len(ys))
    Y2 = np.empty(len(ys))
    ia = ys <= eta
    if ia.any():
        B = _levy_base(k, ys[ia], 0.0, eta)
        Y[ia] = C[0:4] @ B[0]
        Y2[ia] = C[0:4] @ B[2]
    if (~ia).any():
        B = _levy_base(k, ys[~ia], eta, b)
        Y[~ia] = C[4:8] @ B[0]
        Y2[~ia] = C[4:8] @ B[2]
    return Y, Y2


@functools.lru_cache(maxsize=None)
def _levy_Y_memo(k: float, eta: float, b: float, D: float, nu: float, ys: tuple):
    """_levy_Y con memoria: en un barrido de manos las alturas eta se repiten
    (la fila de manos comparte y), y la ODE es la misma para cada (modo, eta)."""
    return _levy_Y(k, eta, b, D, nu, ys)


def _levy_campo(a: float, b: float, D: float, nu: float, cargas, xs, ys,
                modos: int = 60):
    """w, w_xx, w_yy en la malla xs x ys de una placa apoyada en x = 0 y
    x = a (w = 0, M_x = 0) y libre en y = 0 e y = b, por las cargas
    [(coeficiente_x(k), eta)]: cada carga aporta q_m(eta) = coef(k) al modo k.
    Un punto P en (xi, eta) es coef = 2 P sin(k xi) / a; una linea de P
    repartida en [x1, x2] a altura eta es 2 P (cos k x1 - cos k x2) / (a k L)."""
    import numpy as np
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    W = np.zeros((len(xs), len(ys)))
    Wxx = np.zeros_like(W)
    Wyy = np.zeros_like(W)
    for m in range(1, modos + 1):
        k = m * math.pi / a
        sx = np.sin(k * xs)
        por_eta: dict[float, float] = {}
        for coef, eta in cargas:
            por_eta[eta] = por_eta.get(eta, 0.0) + coef(k)
        for eta, qm in por_eta.items():
            if abs(qm) < 1e-15:
                continue
            Y, Y2 = _levy_Y_memo(k, eta, b, D, nu, tuple(ys))
            W += qm * np.outer(sx, Y)
            Wyy += qm * np.outer(sx, Y2)
            Wxx += -k * k * qm * np.outer(sx, Y)
    return W, Wxx, Wyy


def _placa_trasera(p: dict[str, float], apoyos_abajo: str = "pestanas",
                   carga: tuple[float, float] | None = None,
                   aire: float | None = None) -> dict:
    """Una mano sobre la trasera como PLACA: el caso `carga` = (x, y) -- el
    centro si no se dice -- de _placa_trasera_barrido(). Ver alli."""
    return _placa_trasera_barrido(p, [carga or (perfil(p)["ancho_util"] / 2,
                                                _trasera(p)["alto"] / 2)],
                                  apoyos_abajo, aire)[0]


def _placa_trasera_barrido(p: dict[str, float], manos, apoyos_abajo: str = "pestanas",
                           aire: float | None = None) -> list[dict]:
    """La trasera como PLACA, por Levy (exacta en y, serie de 60 modos en x):
    apoyada en los dos bolsillos (x = 0 y x = a: w = 0, momento libre), libre
    por arriba, y por abajo libre salvo donde la sujetan las pestanas del
    talon. LAS PESTANAS NO TOCAN LA PLANCHA: estan a talon_pestana_aire de su
    cara interior (>= tol_pmma + 0.5, como todo lo fijo tras el acrilico), asi
    que son un tope UNILATERAL a esa distancia -- la placa cede el aire antes
    de apoyarse, y una pestana que tuviera que tirar no existe --: apoyos por
    flexibilidad, w = aire en el centro de la lengueta (a media altura), con
    la reaccion repartida en su ancho. La primera version de esta puerta las
    ponia tocando (w = 0), y el revisor del PR #244 la cazo: con el aire, tres
    de las cinco manos que barria pasaban del techo.

    carga_mano en cada mano de `manos` = [(x, y)], repartida como presion
    uniforme en un disco de R_CONTACTO (el canto de una mano; fue tambien el
    de la puerta del costado de acrilico, retirada el 2026-10-11): integrada en x en cerrado modo a modo y en y por
    Gauss de seis nodos -- una carga suave, sin puntos singulares --, asi que
    la tension bajo la mano es la del contacto. La reaccion de cada pestana
    se reparte en su ancho y en su altura (tres lineas). Las funciones de
    Green de las pestanas se calculan una vez y se reutilizan mano a mano.

    apoyos_abajo = "pestanas" (las del talon), "libre" (solo los bolsillos:
    la cota de arriba) o "todo" (el canto entero apoyado, sin aire: la de
    abajo). `aire` sustituye a talon_pestana_aire si se da.
    Devuelve por mano: flecha maxima (el canto libre de arriba, que bascula),
    flecha bajo la carga, tension de flexion mayor sobre la malla, apoyos en
    contacto y reacciones (N, positivas) de cada pestana."""
    import numpy as np
    tr = _trasera(p)
    tl = _talon(p)
    a = perfil(p)["ancho_util"]
    b = tr["alto"]
    t = p["t_piel"]
    nu = NU_PMMA
    D = E_PMMA * t ** 3 / (12 * (1 - nu ** 2))
    F = p["carga_mano"]
    R = R_CONTACTO
    modos = 50
    # Gauss-Legendre de seis nodos en [-1, 1], normalizados para que el disco
    # sume exactamente F (la cuerda 2 sqrt(1 - xi^2) no es polinomio)
    GL = ((0.2386191861, 0.4679139346), (0.6612093865, 0.3607615730),
          (0.9324695142, 0.1713244924))
    nodos = [(s * xi, w) for xi, w in GL for s in (-1.0, 1.0)]
    norma = sum(w * 2 * math.sqrt(1 - xi * xi) for xi, w in nodos)

    def linea(P, xcl, L, eta):
        """P repartida en [xcl - L/2, xcl + L/2] a la altura eta."""
        x1, x2 = xcl - L / 2, xcl + L / 2
        return (lambda k, P=P: 2.0 * P * (math.cos(k * x1) - math.cos(k * x2)) / (a * k * L), eta)

    def disco(xc, yc):
        """carga_mano como presion uniforme en el disco de radio R: en cada
        nodo de Gauss, la cuerda del disco como linea con su peso."""
        out = []
        for xi, w in nodos:
            h = R * math.sqrt(1 - xi * xi)
            out.append(linea(F * w * 2 * math.sqrt(1 - xi * xi) / norma, xc, 2 * h, yc + R * xi))
        return out

    # las pestanas: tres lineas por su altura sobre el canto de la plancha, que
    # apoya en el pie (la lengueta sube alto - t sobre ese canto)
    h_tab = p["talon_pestana_alto"] - p["t_costilla"]
    y_tab = h_tab / 2.0
    ys_tab = [h_tab * f for f in (0.25, 0.5, 0.75)]
    L_tab = p["talon_pestana_ancho"]
    if apoyos_abajo == "pestanas":
        xs_ap = [zc - p["t_anillo"] for zc in tl["pestana_z"]]
        gap = p["talon_pestana_aire"] if aire is None else aire
    elif apoyos_abajo == "todo":
        xs_ap = list(np.linspace(0.0, a, 41)[1:-1])
        L_tab = a / 40.0
        gap = 0.0 if aire is None else aire
    else:
        xs_ap, gap = [], 0.0
    n = len(xs_ap)
    xs = np.linspace(0.0, a, 109)
    ys = np.linspace(0.0, b, 49)
    xa = np.array(xs_ap)
    # las funciones de Green de las pestanas, una vez: en las pestanas y en la malla
    G = np.zeros((n, n))
    campos_tab = []
    for j in range(n):
        tab = [linea(1.0 / 3, xs_ap[j], L_tab, yt) for yt in ys_tab]
        G[:, j] = _levy_campo(a, b, D, nu, tab, xa, [y_tab], modos)[0][:, 0]
        campos_tab.append(_levy_campo(a, b, D, nu, tab, xs, ys, modos))
    out = []
    for xc, yc in manos:
        mano = disco(xc, yc)
        reac = np.zeros(n)
        if n:
            g = _levy_campo(a, b, D, nu, mano, xa, [y_tab], modos)[0][:, 0]
            # TOPE UNILATERAL: en contacto, w = gap con reaccion r < 0 (empuja
            # contra la mano); sin contacto, w < gap y r = 0. Conjunto activo:
            # fuera la que tire (r > 0), dentro la que atraviese el aire.
            activas = [j for j in range(n) if g[j] > gap]
            for _ in range(2 * n + 2):
                reac = np.zeros(n)
                if activas:
                    A_ = np.ix_(activas, activas)
                    r = np.linalg.solve(G[A_], gap - g[activas])
                    for jj, j in enumerate(activas):
                        reac[j] = r[jj]
                tiran = [j for j in activas if reac[j] > 1e-9]
                if tiran:
                    activas = [j for j in activas if j not in tiran]
                    continue
                w_tab = g + G @ reac
                entran = [j for j in range(n) if j not in activas and w_tab[j] > gap + 1e-9]
                if not entran:
                    break
                activas = sorted(activas + entran)
            else:
                raise AssertionError(
                    f"el conjunto activo de las pestanas no converge para la mano "
                    f"({xc:.0f}, {yc:.0f}): {activas} tras {2 * n + 2} vueltas")
        Wm, Wxx, Wyy = _levy_campo(a, b, D, nu, mano, xs, ys, modos)
        for j in range(n):
            if reac[j]:
                Wm = Wm + reac[j] * campos_tab[j][0]
                Wxx = Wxx + reac[j] * campos_tab[j][1]
                Wyy = Wyy + reac[j] * campos_tab[j][2]
        sx = 6 * D * np.abs(Wxx + nu * Wyy) / t ** 2
        sy = 6 * D * np.abs(Wyy + nu * Wxx) / t ** 2
        s = np.maximum(sx, sy)
        i, j = np.unravel_index(int(s.argmax()), s.shape)
        # la flecha bajo la mano: el mayor de los cuatro nodos que la rodean
        ii = int(np.clip(np.searchsorted(xs, xc), 1, len(xs) - 1))
        jj = int(np.clip(np.searchsorted(ys, yc), 1, len(ys) - 1))
        w_carga = float(np.abs(Wm[ii - 1:ii + 1, jj - 1:jj + 1]).max())
        out.append({"mano": (xc, yc), "flecha": float(np.abs(Wm).max()),
                    "flecha_carga": w_carga, "sigma": float(s.max()),
                    "sigma_en": (float(xs[i]), float(ys[j])), "a": a, "b": b, "D": D,
                    "gap": gap, "apoyos": int(sum(1 for x in reac if x)),
                    "reacciones": [float(abs(x)) for x in reac]})
    return out


def guarda_trasera_flexion(p: dict[str, float]) -> None:
    """La trasera, sin un tornillo, se comba y vuelve: ni se sale del
    bolsillo ni pasa del techo del acrilico en la mitad de abajo, la empujen
    donde la empujen; y lo que pasa del techo arriba se publica con su
    extension, como HUECO.

    LA PUERTA QUE EL REVISOR DEL PR #244 PIDIO, Y LUEGO CORRIGIO. Sola en sus
    bolsillos (dos cantos), la placa de 8 x 541 x 237 cede 20 mm bajo
    carga_mano al centro (21 en el canto libre de arriba, que bascula) y
    trabaja a 14 MPa en el disco de contacto: sobre el techo. Con el canto de
    abajo sujeto por las pestanas del talon -- A SU AIRE, que es un tope y
    no un apoyo -- baja del techo, pero solo si hay pestanas bastantes: con
    cuatro, la mano baja entre dos pestanas queda a 9.8 MPa (por un pelo);
    con ocho (a 1/16, 3/16, ..., 15/16: las unicas cuentas que esquivan los
    tres M4 son las potencias de dos), a 8.9.
    Se BARRE la mano por lo que se ve de la placa (una rejilla de 16 x 16
    entre los dos labios mas la mano baja sobre cada pestana, no cinco puntos
    a mano: el maximo real caia fuera de ellos, y lo que tapan los labios no
    lo empuja una mano). Lo que se exige:
    (1) toda mano en la mitad de abajo (y <= b/2, donde mandan las pestanas)
    bajo SIGMA_PMMA; (2) la lengueta mas cargada, con la reaccion en su punta,
    bajo el Rp0.2 del 6082-T6 que el pliego manda para el talon (unos 200 MPa
    con 25 de ancho -- 23.5 en la raiz, tras el alivio -- y el doblez a 2 t:
    con los 130 genericos no pasa ninguna lengueta de 1.5); (3) combada como
    cota de arriba (sin pestanas) no se sale de los bolsillos: el acortamiento
    de cuerda 8w^2/3a queda por debajo del embebido menos 0.5. Y lo que se
    PUBLICA como hueco: la banda de arriba donde la mano pasa del techo -- el
    labio del techo solo para la plancha hacia fuera y por dentro no la
    sujeta nada entre los anillos --, con su altura por biseccion: unos 70 mm
    bajo el labio. Contrastada: 20.45 / 5.37 mm bajo la carga (dos y tres
    cantos, puntual, sin aire) contra 20.35 / 5.38 del revisor; y en la ronda
    4, con 50/100/150/200 modos y mallas de 109 x 49 a 325 x 145 el maximo
    se mueve entre 8.49 y 8.53: lo que la rejilla no ve no es la fisica."""
    tr = _trasera(p)
    a = perfil(p)["ancho_util"]
    b = tr["alto"]
    R = R_CONTACTO
    t_ch = p["t_costilla"]
    # la rejilla de manos: media placa (simetrica en x), y en alto SOLO LO QUE SE
    # VE -- del labio del talon al del techo (_trasera_campo): lo que tapan los
    # labios no lo puede empujar una mano, lo empuja la chapa --, con el disco
    # entero dentro del campo
    campo = _trasera_campo(p)
    y_lo, y_hi = campo[0] - t_ch + R, campo[1] - t_ch - R
    xs_m = [a * (i + 1) / 32 for i in range(16)]
    ys_m = [y_lo + (y_hi - y_lo) * i / 15 for i in range(16)]
    manos = [(x, y) for y in ys_m for x in xs_m]
    # y la mano baja justo sobre cada pestana, que es la que mas la carga
    manos += [(zc - p["t_anillo"], y_lo) for zc in _talon(p)["pestana_z"]
              if zc - p["t_anillo"] <= a / 2 + 1e-9]
    res = _placa_trasera_barrido(p, manos, "pestanas")
    # y alrededor de la mano que mas carga una pestana, una rejilla de 9 x 9 a
    # cuarto de paso, recortada al campo (la mano que mas carga esta en el borde
    # de abajo: por debajo no hay manos, no se pliegan) y sin repetir las que ya
    # estan: el maximo de la rejilla gruesa iba un 3 % por debajo del real
    # (ronda 5 del revisor: 154 N contra 159 con 825 manos), y ese numero es el
    # que va al taller como justificacion del 6082-T6
    x_r, y_r = max(res, key=lambda r: max(r["reacciones"]))["mano"]
    dx, dy = a / 32 / 4, (y_hi - y_lo) / 15 / 4
    finas = sorted({(min(x_r + i * dx, a / 2), min(y_r + j * dy, y_hi))
                    for i in range(-4, 5) for j in range(-4, 5)
                    if x_r + i * dx > 0 and y_r + j * dy >= y_lo - 1e-9}
                   - {r["mano"] for r in res})
    res += _placa_trasera_barrido(p, finas, "pestanas")
    peor_abajo = max((r for r in res if r["mano"][1] <= b / 2), key=lambda r: r["sigma"])
    assert peor_abajo["sigma"] <= SIGMA_PMMA + 1e-9, (
        f"la trasera con {p['carga_mano']:.0f} N en ({peor_abajo['mano'][0]:.0f}, "
        f"{peor_abajo['mano'][1]:.0f}), sujeta por los bolsillos y las pestanas del "
        f"talon a {peor_abajo['gap']:g} de aire, trabaja a {peor_abajo['sigma']:.1f} "
        f"MPa contra {SIGMA_PMMA:g} del PMMA ({peor_abajo['apoyos']} pestanas en "
        f"contacto, a {', '.join(f'{x:.0f}' for x in peor_abajo['reacciones'])} N). "
        f"Mas pestanas, menos aire, o mas espesor")
    # la lengueta: chapa de ancho x t, empotrada en su doblez, con la reaccion en
    # la punta (peor caso: la placa, inclinada, la toca arriba). Contra el
    # 6082-T6 que el pliego manda para el talon, no contra los 130 genericos:
    # a 200 MPa no hay lengueta de 1.5 que pase con 130 sin ser un peine.
    r_max = max(max(r["reacciones"]) for r in res)
    # la seccion que trabaja es LA RAIZ, en la linea del doblez, y ahi el alivio
    # (centrado en el corte, de radio mayor que medio corte) muerde la pestana
    # por los dos lados: 25 nominales son 23.5 de raiz (ronda 5 del revisor)
    raiz = _talon(p)["pestana_raiz"]
    Z = raiz * t_ch ** 2 / 6
    brazo = p["talon_pestana_alto"] + p["radio_doblez_pestana"]
    sigma_tab = r_max * brazo / Z
    assert sigma_tab <= RP02_6082_T6 + 1e-9, (
        f"la pestana mas cargada recibe {r_max:.0f} N y, como lengueta de "
        f"{raiz:g} x {t_ch:g} en la raiz ({p['talon_pestana_ancho']:g} menos lo que "
        f"muerde el alivio) con {brazo:g} de brazo, trabaja a {sigma_tab:.0f} MPa "
        f"contra {RP02_6082_T6:.0f} del 6082-T6: mas ancha, menos alivio, o mas "
        f"pestanas")
    sin = _placa_trasera(p, "libre")
    cuerda = 8 * sin["flecha"] ** 2 / (3 * a)
    assert cuerda <= tr["entra"] - 0.5 + 1e-9, (
        f"combada {sin['flecha']:.1f} mm (solo los bolsillos), la trasera acorta "
        f"{cuerda:.2f} mm por punta y entra {tr['entra']:.2f}: se sale del bolsillo")
    centro = next(r for r in res if abs(r["mano"][0] - a / 2) < 1e-9
                  and abs(r["mano"][1] - ys_m[min(range(len(ys_m)), key=lambda i: abs(ys_m[i] - b / 2))]) < 1e-9)
    peor = max(res, key=lambda r: r["sigma"])
    fallan = [r for r in res if r["sigma"] > SIGMA_PMMA]
    print(f"trasera como placa ({a:.0f} x {b:.0f} x {p['t_piel']:g}, mano de "
          f"{p['carga_mano']:.0f} N en un disco de R={R:g}, {len(res)} manos en media "
          f"placa; {len(_talon(p)['pestana_z'])} pestanas a "
          f"{p['talon_pestana_aire']:g} de aire): al centro cede "
          f"{centro['flecha_carga']:.1f} mm bajo la mano a {centro['sigma']:.1f} MPa; "
          f"la peor de la mitad de abajo, ({peor_abajo['mano'][0]:.0f}, "
          f"{peor_abajo['mano'][1]:.0f}): {peor_abajo['sigma']:.1f} MPa (techo "
          f"{SIGMA_PMMA:g}); la lengueta mas cargada, {r_max:.0f} N y {sigma_tab:.0f} "
          f"MPa en la raiz de {raiz:g} (6082-T6: {RP02_6082_T6:.0f}). Solo con los bolsillos, "
          f"{sin['flecha_carga']:.1f} ({sin['flecha']:.1f}) "
          f"mm a {sin['sigma']:.1f}, y acorta {cuerda:.2f} de los {tr['entra']:.2f} "
          f"embebidos")
    if fallan:
        # LA FRONTERA DE LA BANDA, POR BISECCION en la columna de la peor mano:
        # la rejilla solo la conoce a un paso de fila (13 mm), y publicarla
        # como exacta era mentir por abajo (ronda 4 del revisor)
        x_p = peor["mano"][0]
        col = sorted((r for r in res if abs(r["mano"][0] - x_p) < 1e-9), key=lambda r: r["mano"][1])
        y_ok = max((r["mano"][1] for r in col if r["sigma"] <= SIGMA_PMMA), default=y_lo)
        y_no = min(r["mano"][1] for r in col if r["sigma"] > SIGMA_PMMA)
        for _ in range(6):
            y_m = (y_ok + y_no) / 2
            if _placa_trasera(p, "pestanas", (x_p, y_m))["sigma"] > SIGMA_PMMA:
                y_no = y_m
            else:
                y_ok = y_m
        y_h = y_no + t_ch                                    # a coordenadas del case
        y_top = campo[1]                                     # donde empieza el labio del techo
        _HUECOS.append(
            f"la trasera empujada por encima de y = {y_h:.0f} (una banda de "
            f"{y_top - y_h:.0f} mm bajo el labio del techo, de lado a lado) pasa del "
            f"techo del PMMA: {peor['sigma']:.1f} MPa y {peor['flecha_carga']:.1f} mm "
            f"con {p['carga_mano']:.0f} N en ({peor['mano'][0]:.0f}, "
            f"{peor['mano'][1] + t_ch:.0f}), la mano mas alta que cabe entera en lo "
            f"visible (a R = {R:g} del labio; mas arriba empuja la chapa). El labio "
            f"del techo solo la para hacia fuera y por dentro no la sujeta nada entre "
            f"los anillos; un tope lanzado desde el techo dejaria una ventana a la "
            f"vista en la meseta. Queda por decidir (spec 2026-08-29 trasera "
            f"capturada, seccion 9)")


def guarda_talon(p: dict[str, float]) -> None:
    """El talon es la nariz de atras: P6 a chaflan, el labio que tapa el canto
    de abajo de la trasera, tres M4 en el pie con la boca lejos del acrilico,
    y las pestanas que le hacen de tope por dentro (cuantas, lo dice
    guarda_trasera_flexion).

    Es lo que Samuel pidio la noche del 2026-08-29 mirando el render de #241:
    "el mismo estilo y acabado que la nariz". Siete cosas, con su numero:
      1. P6 no lleva radio: el chaflan de chaflan_nariz, como P0.
      2. el labio mide lo que el frente de la nariz (alto_frontal - chaflan):
         las chapas del canto cierran igual.
      3. el chaflan pasa POR DEBAJO de la esquina de abajo-fuera de la
         trasera, que apoya en el pie: en la cara vista del acrilico la cara
         interior del chaflan queda por debajo de y0.
      4. los M4 del pie: fuera de la zona del doblez del chaflan (r + 3t +
         d/2), a 1.5 D del canto libre, y su BOCA a tol + 0.5 de la cara
         interior de la trasera -- es lo que pone el pie en 20.
      5. las pestanas a tol + 0.5 de esa cara, con 2 t de plano entre el
         doblez del chaflan y el suyo (las tangentes), su ventana dentro del
         pie con 2 t al canto libre, y a 1.5 D + medio ancho de cada M4.
      6. el labio tapa mas canto de trasera que el bolsillo del anillo (6).
      7. la nariz y el talon comparten pie, chaflan y frente: mismo estilo."""
    tl = _talon(p)
    tr = _trasera(p)
    c, t = p["chaflan_nariz"], p["t_costilla"]
    assert _radios_perfil(p)[6] is None, (
        "P6 va a chaflan como P0: la esquina de abajo-atras la corta "
        "chaflan_nariz, no un radio")
    assert abs(p["talon_labio"] - (p["alto_frontal"] - c)) < 1e-9, (
        f"el labio del talon mide {p['talon_labio']:g} y el frente de la nariz "
        f"{p['alto_frontal'] - c:g} (alto_frontal - chaflan_nariz): mismo estilo "
        f"es el mismo numero")
    y_ch = (tr["x1"] - tl["x_chaflan"]) - t * math.sqrt(2)
    assert y_ch <= tr["y0"] - 1e-9, (
        f"la cara interior del chaflan del talon pasa por y={y_ch:.2f} en la cara "
        f"vista de la trasera (x={tr['x1']:.2f}) y la trasera apoya en y="
        f"{tr['y0']:.2f}: se la come por la esquina")
    raiz = p["radio_doblez_costilla"] + 3 * t + p["d_M4_paso"] / 2
    assert tl["x_chaflan"] - tl["m4_x"] >= raiz - 1e-9, (
        f"el M4 del pie cae a {tl['x_chaflan'] - tl['m4_x']:.2f} de la linea del "
        f"chaflan y la regla de chapa pide {raiz:.2f}")
    assert tl["m4_x"] - tl["x_pie"] >= 1.5 * p["d_M4_paso"] - 1e-9, (
        f"el M4 del pie cae a {tl['m4_x'] - tl['x_pie']:.2f} de su canto libre")
    boca = tl["m4_x"] + p["d_cabeza_M4_avell"] / 2
    franja = _tol_pmma(p) + 0.5
    aire = tr["x0"] - boca
    assert aire >= franja - 1e-9, (
        f"la boca del avellanado del M4 del talon llega a x={boca:.2f} y la cara "
        f"interior de la trasera esta en {tr['x0']:.2f}: {aire:.2f} de aire, y "
        f"detras de un PMMA de +-{_tol_pmma(p):.1f} se piden {franja:.2f}. Sube "
        f"talon_pie")
    aire_p = tr["x0"] - tl["pestana_x"]
    assert aire_p >= franja - 1e-9, (
        f"la pestana del talon queda a {aire_p:.2f} de la cara interior de la "
        f"trasera y se piden {franja:.2f} (talon_pestana_aire)")
    tang_ch = tl["x_chaflan"] - (p["radio_doblez_costilla"] + t) * math.tan(math.radians(22.5))
    # r + t: la tangente EXTERIOR de los dos dobleces, la cuenta conservadora.
    # La pestana dobla con su radio interior hacia la plancha (la cara que la
    # toca es el interior del doblez), asi que el plano real es t mayor.
    tang_pe = tl["pestana_x"] + p["radio_doblez_pestana"] + t
    plano = tang_ch - tang_pe
    assert plano >= 2 * t - 1e-9, (
        f"entre la tangente del doblez del chaflan (x={tang_ch:.2f}) y la del "
        f"doblez de la pestana ({tang_pe:.2f}) quedan {plano:.2f} de plano; se "
        f"exigen 2 t = {2 * t:g}. Sube talon_pestana_aire o baja "
        f"radio_doblez_pestana")
    fin_ventana = tl["pestana_x"] - tl["pestana_dev"]
    assert fin_ventana - tl["x_pie"] >= 2 * t - 1e-9, (
        f"la ventana de la pestana llega a x={fin_ventana:.2f} y el canto libre "
        f"del pie esta en {tl['x_pie']:.2f}: menos de 2 t de puente")
    # el alivio: un taladro mas estrecho que la chapa no alivia nada (y mas
    # ancho, se come la raiz: eso lo acota la lengueta en guarda_trasera_flexion)
    assert p["alivio_pestana"] >= t - 1e-9, (
        f"el alivio de la pestana mide {p['alivio_pestana']:g} y la chapa {t:g}: "
        f"un alivio mas estrecho que el espesor no alivia el doblez")
    # la ventana no acaba en el ancho de la pestana: el corte y el alivio la
    # ensanchan (tl['pestana_ventana'] es el medio ancho real)
    sep_min = 1.5 * p["d_M4_paso"] + tl["pestana_ventana"] + p["d_M4_paso"] / 2
    for zc in tl["pestana_z"]:
        for zm in tl["m4_z"]:
            assert abs(zc - zm) >= sep_min - 1e-9, (
                f"la pestana en z={zc:.1f} y el M4 en z={zm:.1f} estan a "
                f"{abs(zc - zm):.1f}; piden {sep_min:.2f}")
    # LAS PESTANAS SON ESTRUCTURA (guarda_trasera_flexion, que decide cuantas
    # hacen falta): tienen que solapar el canto de la trasera al menos lo que
    # el bolsillo la embebe, ser mas anchas que altas y doblar con radio >= 1 t.
    assert p["talon_pestana_alto"] >= p["rebaje_anillo"] - 1e-9, (
        f"la pestana del talon sube {p['talon_pestana_alto']:g} sobre el pie y el "
        f"bolsillo embebe {p['rebaje_anillo']:g}: una retencion no puede ser "
        f"menor que la otra")
    assert p["talon_pestana_ancho"] >= 2 * p["talon_pestana_alto"] - 1e-9, (
        f"la pestana mide {p['talon_pestana_ancho']:g} de ancho por "
        f"{p['talon_pestana_alto']:g} de alto: una lengueta mas alta que ancha "
        f"se dobla sola")
    assert p["radio_doblez_pestana"] >= t - 1e-9, (
        f"radio_doblez_pestana = {p['radio_doblez_pestana']:g} y la chapa tiene "
        f"{t:g}: por debajo de 1 t el 6082-T6 raja en el doblez")
    tapa = c + p["talon_labio"] - tr["y0"]
    assert tapa >= p["rebaje_anillo"] - 1e-9, (
        f"el talon tapa {tapa:.2f} del canto de abajo de la trasera y el "
        f"bolsillo del anillo tapa {p['rebaje_anillo']:g}")
    assert abs(p["nariz_pie"] - p["talon_pie"]) <= 2.0 + 1e-9, (
        f"pie de la nariz {p['nariz_pie']:g} y del talon {p['talon_pie']:g}: "
        f"mismo estilo, y difieren mas de 2")
    print(f"talon: la nariz de atras -- chaflan de {c:g} en P6, labio de "
          f"{p['talon_labio']:g} a ras del plano trasero (tapa {tapa:.2f} de "
          f"trasera), pie de {p['talon_pie']:g}; 3 M4 avellanados en "
          f"x={tl['m4_x']:.2f} (boca a {aire:.2f} de la trasera, piden {franja:.2f}); "
          f"{len(tl['pestana_z'])} pestanas de {p['talon_pestana_ancho']:g} x {p['talon_pestana_alto']:g} "
          f"a {aire_p:.2f} de la trasera con {plano:.2f} de plano tras el chaflan; "
          f"desarrollo {tl['largo']:.2f} x {tl['desarrollo']:.2f}")


def guarda_trasera_capturada(p: dict[str, float]) -> None:
    """La trasera va DENTRO de los anillos, y nada la toca
    a distancia fija.

    SUSTITUYE A guarda_trasera_dentro() (#241), que vigilaba la trasera
    atornillada a las dos bandas. Lo que mide, con el numero de cada cosa:
      1. el bolsillo del tramo trasero tiene LOS TRES NUMEROS del bolsillo
         del costado (labio = rehundido_acrilico, hondo = rebaje_anillo,
         ancho = t_anillo - rehundido) y sitio para la plancha mas gruesa del
         lote mas la junta, con medio milimetro de sobra.
      2. la pared entre los dos bolsillos mide >= 3 (desde el 2026-10-11 el
         otro bolsillo es el rebaje vacio del costado).
      3. las puntas de la trasera entran >= 5 en los bolsillos.
      4. NADA FIJO a menos de tol + 0.5 de su cara interior nominal dentro
         de su huella: la pared del bolsillo (en la rebanada del anillo), la
         pata trasera del marco, las pestanas del talon, el chasis... Es la
         regla del postmortem (spec 26-08 s3), la misma de #241.
      5. el canto de abajo sobre el pie del talon (y0 = t_costilla) y el de
         arriba bajo el techo con 0.5: en B bajo el chaflan (su cara interior
         en la cara vista del acrilico), en A bajo el doblez de la banda.
      6. los labios la tapan >= rebaje_anillo arriba y abajo, y el aire entre
         el labio y su cara (labio + junta - t) se publica: es la tira de
         EPDM del pliego.
      7. cero filas: ninguna caja de fila apunta a la trasera."""
    P = _vertices(p)
    bo = _bolsillo_trasero(p)
    tr = _trasera(p)
    t = p["t_costilla"]
    # EL LABIO DEJO DE SER EL DEL COSTADO EL 2026-08-30. Los otros dos numeros
    # del bolsillo siguen siendo "los del costado, girados" -- hondo
    # rebaje_anillo, ancho t_anillo - rehundido_acrilico --, pero el labio lo
    # manda ahora la RENDIJA del alero: la cara interior del labio del techo se
    # aleja 1 del plano al rehundirse la chapa, y la plancha tiene que
    # retroceder lo mismo para que la luz siga siendo aire_labios. Es la unica
    # cota de la trasera que no se deriva del costado, y por eso _rehundido_-
    # trasera() vive aparte y con su propia explicacion.
    assert (abs(bo["u0"] - _rehundido_trasera(p)) < 1e-9
            and abs(bo["hondo"] - p["rebaje_anillo"]) < 1e-9
            and abs(bo["ancho"] - (p["t_anillo"] - p["rehundido_acrilico"])) < 1e-9), (
        "el bolsillo de la trasera tiene que llevar el labio que manda la "
        "rendija (rehundido_trasera) y, del bolsillo del costado girado, el "
        "hondo rebaje_anillo y el ancho t_anillo - rehundido_acrilico")
    sitio = bo["ancho"] - (p["t_piel"] + _tol_pmma(p) + p["t_junta_asiento"])
    assert sitio >= 0.5 - 1e-9, (
        f"el bolsillo de la trasera mide {bo['ancho']:g} y la plancha mas gruesa "
        f"del lote ({p['t_piel']:g} + {_tol_pmma(p):.1f}) mas la junta "
        f"({p['t_junta_asiento']:g}) dejan {sitio:.2f}; se piden 0.5")
    # LA PARED Y LA ENTRADA DEL COSTADO SE FUERON A guarda_tramo_trasero() el
    # 2026-08-30. Estaban aqui contra el literal 3 las dos; ahora la pared va
    # contra PARED_MIN_ANILLO (una constante con nombre, que es lo que se puede
    # subir de una vez para todo el anillo) y la entrada del costado contra
    # cara_anillo_trasera(), que dejo de ser el 20 uniforme: en este tramo la
    # franja mide 22, y medirla con cara_anillo habria puesto rojo el anillo
    # correcto.
    assert tr["entra"] >= 5.0 - 1e-9, (
        f"las puntas de la trasera entran {tr['entra']:.2f} en los bolsillos; se "
        f"piden 5")
    # EL BOLSILLO ESTA CERRADO POR LOS DOS EXTREMOS, con 0.5 de aire a cada
    # canto de la trasera: arriba es su tope y abajo es el pie del talon el que
    # la sostiene (el bolsillo se queda 0.5 por debajo). Y la plancha entra al
    # montar el segundo anillo, no por ningun canto: no hay camino que medir.
    assert abs(bo["y_fin"] - (tr["y1"] + 0.5)) < 1e-9, (
        f"el bolsillo se cierra en y={bo['y_fin']:.2f} y el canto de arriba de la "
        f"trasera esta en {tr['y1']:.2f}: tienen que llevarse 0.5")
    assert abs(bo["y_bot"] - (tr["y0"] - 0.5)) < 1e-9, (
        f"el bolsillo arranca en y={bo['y_bot']:.2f} y el canto de abajo de la "
        f"trasera esta en {tr['y0']:.2f}: tienen que llevarse 0.5")
    # EL ESCALON BAJO EL CHAFLAN: el bolsillo no muerde la cara del chaflan de
    # P6 (su esquina de abajo-fuera queda 0.5 dentro de la linea u + y = c), y
    # la esquina de abajo-fuera de la plancha, a chaflan, libra el escalon con
    # 0.5 en su punto peor (la esquina (u_paso, y_paso) del bolsillo).
    c_an = p["chaflan_nariz"]
    assert bo["u_paso"] + bo["y_bot"] >= c_an + 0.5 - 1e-9, (
        f"la esquina de abajo-fuera del bolsillo (u={bo['u_paso']:g}, "
        f"y={bo['y_bot']:g}) queda fuera de la cara del chaflan de P6 (u + y = "
        f"{c_an:g}) o a menos de 0.5 de ella")
    assert bo["u0"] + bo["y_paso"] >= c_an + 0.5 - 1e-9, (
        f"la pared de u={bo['u0']:g} del bolsillo arranca en y={bo['y_paso']:g}, "
        f"dentro del chaflan de P6")
    c_p = tr["chaflan_bajo"]
    # LA PLANCHA EN SU PEOR SITIO: descansando en el fondo del bolsillo (y_bot,
    # antes de que la tabla la suba a y0) y pegada al labio (u = u0, la junta
    # aplastada). Ahi, a la altura del escalon, su contorno empieza en
    # u0 + c_p - (y_paso - y_bot), y tiene que quedar 0.5 dentro del escalon.
    u_plancha = bo["u0"] + c_p - (bo["y_paso"] - bo["y_bot"])
    assert u_plancha >= bo["u_paso"] + 0.5 - 1e-9, (
        f"con la plancha en el fondo del bolsillo (y={bo['y_bot']:g}) y pegada al "
        f"labio, a la altura del escalon (y={bo['y_paso']:g}) su chaflan de "
        f"{c_p:.2f} la deja en u={u_plancha:.2f} y el escalon esta en "
        f"u={bo['u_paso']:g}: se piden 0.5")
    assert c_p <= p["t_piel"] - 2.0 + 1e-9, (
        f"el chaflan de la arista de abajo de la trasera mide {c_p:.2f} y deja "
        f"menos de 2 de canto plano sobre el pie")
    # Y LO QUE HACE QUE LA CUENTA SEA LA CUENTA: holgura y junta reales.
    assert p["hol_piel"] >= 0.1 and p["t_junta_asiento"] >= 0.5, (
        "hol_piel y t_junta_asiento fijan el ancho de la trasera y su rehundido: "
        "no pueden ser cero")
    franja = _tol_pmma(p) + 0.5
    x_pared = P[6][0] - bo["u1"]
    assert tr["x0"] - x_pared >= franja - 1e-9, (
        f"la pared del bolsillo (x={x_pared:.2f}) queda a {tr['x0'] - x_pared:.2f} "
        f"de la cara interior nominal de la trasera; se piden {franja:.2f}")
    railes, planchas, filas = _cajas_solidas(p)
    for c in railes + planchas:
        if c[0] == "piel_trasera":
            continue
        en_franja = c[2] > tr["x0"] - franja + 1e-9 and c[1] < tr["x0"] - 1e-9
        en_huella = (c[4] > tr["y0"] + 1e-9 and c[3] < tr["y1"] - 1e-9
                     and c[6] > tr["z0"] + 1e-9 and c[5] < tr["z1"] - 1e-9)
        if en_franja and en_huella:
            raise AssertionError(
                f"'{c[0]}' ocupa x={c[1]:.2f}..{c[2]:.2f} y la trasera acaba en "
                f"x={tr['x0']:.2f}: esta a {tr['x0'] - c[2]:.2f} de su cara interior, "
                f"dentro de los {franja:.2f} (tolerancia {_tol_pmma(p):.1f} + 0.5) "
                f"que una plancha mas gruesa del lote necesita. Nada fijo "
                f"detras del acrilico a distancia fija")
    c_ch = p["chaflan_nariz"]
    if _chaflan_p5(p):
        # la cara interior del chaflan del techo, en la cara vista del acrilico
        y_techo = (P[5][1] - (tr["x1"] - (P[6][0] - c_ch))) - t * math.sqrt(2)
        que = "el chaflan del techo"
    else:
        # la cara interior del doblez de la banda (radio r sobre la esquina)
        r = p["radio_doblez_costilla"]
        cx, cy = P[6][0] - (r + t), P[5][1] - (r + t)
        dx = tr["x1"] - cx
        y_techo = cy + math.sqrt(max(r * r - dx * dx, 0.0)) if abs(dx) <= r else P[5][1] - t
        que = "el doblez de la banda"
    y_techo = min(y_techo, P[5][1] - p["marco_sup"] - p["hol_piel"])
    assert tr["y1"] <= y_techo - 0.5 + 1e-9, (
        f"el canto de arriba de la trasera (y={tr['y1']:.2f}) se mete en {que}, "
        f"cuya cara interior pasa por y={y_techo:.2f} en la cara vista del "
        f"acrilico; se piden 0.5 de aire")
    tapa_arriba = tr["y1"] - _y_labio_techo(p)
    tapa_abajo = (c_ch + p["talon_labio"]) - tr["y0"]
    for nm, tapa in (("el techo", tapa_arriba), ("el talon", tapa_abajo)):
        assert tapa >= p["rebaje_anillo"] - 1e-9, (
            f"{nm} tapa {tapa:.2f} del canto de la trasera; el bolsillo del anillo "
            f"tapa {p['rebaje_anillo']:g} y aqui no se tapa menos")
    assert not any(f[0] == "piel_trasera" for f in filas), (
        "la trasera capturada no lleva filas: nada la atraviesa")
    print(f"trasera capturada: {tr['au']:.2f} x {tr['alto']:.2f} en {p['t_piel']:g}, "
          f"sin un taladro; puntas {tr['entra']:.2f} dentro de los bolsillos "
          f"(labio {bo['u0']:g}, hondo {bo['hondo']:g}, ancho {bo['ancho']:g}, "
          f"{sitio:.2f} de sobra), cara vista rehundida "
          f"{bo['u0'] + p['t_junta_asiento']:g} (la pared, en "
          f"guarda_tramo_trasero)")
    print(f"  tope hacia dentro: la pared del bolsillo a {tr['x0'] - x_pared:.2f} y el "
          f"marco a {tr['x0'] - (P[6][0] - _retiro_marco_trasera(p)):.2f} de su cara "
          f"interior; el techo la tapa {tapa_arriba:.2f} y el talon {tapa_abajo:.2f}; "
          f"tira de EPDM de {tr['aire_labios']:g} tras cada labio")
    print(f"  bolsillo cerrado de y = {bo['y_bot']:g} a {bo['y_fin']:.2f} (u = "
          f"{bo['u_paso']:g}..{bo['u1']:g} bajo y = {bo['y_paso']:g}, "
          f"{bo['u0']:g}..{bo['u1']:g} encima); la plancha entra al montar el "
          f"segundo anillo, con su arista de abajo-fuera a chaflan de {c_p:.2f}")


# HASTA DONDE, a lo largo del contorno, tiene que haber una rosca en la pata
# vecina para que una esquina EMPOTRE a la pata que no lleva tornillo. El
# momento de la pata sin tornillo entra en la vecina como torsion de un tramo
# corto de pletina (6 x 24: GJ/L ~ 1e6 N mm/rad a 100 mm), que bajo los 9 N m
# de la pata trasera gira 0.01 rad, o sea nada; mas lejos no se cuenta y la
# esquina es un apoyo. Es lo que justifica el 107 (empotrada-apoyada) de la

# Lo que se deja de pletina entre dos vaciados del anillo. Es una CONSTANTE y no
# el propio parametro: hasta el 2026-08-30 el aserto de la pared del bolsillo
# comparaba pared_rebaje_trasera consigo misma, o sea que era verde por
# construccion. Un umbral que se mueve con lo que mide no mide nada.
PARED_MIN_ANILLO = 3.0

# Relacion maxima alto:ancho de una pared fresada. El pliego trabaja con fresa
# de Ø3 y 3:1 es lo que un taller acepta sin pedir prima; el reborde de 1 x 3
# del rebaje de chapa esta JUSTO en ese limite, y por eso va al RFQ como
# pregunta con respuesta ya disenada (si piden 1.5, rehundido_chapa = 1.5).
ESBELTEZ_MAX_PARED = 3.0


def guarda_rebaje_chapa(p: dict[str, float]) -> None:
    """Las tres chapas del canto van EMPOTRADAS en un rebaje fresado en la cara
    interior del anillo, no apoyadas sobre ella (2026-08-30).

    Samuel, mirando la esquina en Blender: "el acabado debe sentirse perfecto
    con respecto a la esquina [...] tiene que ser una pieza que se sienta
    empotrada". El problema real que eso nombra es de TOLERANCIAS: con la chapa
    apoyada sobre la cara, las dos cotas que se ven -- donde muere la chapa y
    donde muere el anillo -- las cortaba la plegadora (+-0.3 en el desarrollo,
    +-0.5 en el doblez) y el desvio salia a la superficie como un escalon. Con
    la chapa dentro del rebaje, lo que se ve lo corta la FRESADORA: la junta de
    sombra de rehundido_chapa y el reborde que tapa el canto. El error de chapa
    se esconde debajo, donde antes se veia encima.

    Esta puerta mide el rebaje y su reborde. El tramo trasero, que es donde el
    rebaje convive con el bolsillo de la trasera, lo mide guarda_tramo_trasero();
    lo que el rebaje le hace a la salida de aire, guarda_rendija()."""
    t = p["t_costilla"]
    reb, reh, hol = p["rebaje_chapa"], p["rehundido_chapa"], p["hol_chapa"]

    # --- el fondo del rebaje, por los dos lados -----------------------------
    # EL SUELO ES FISICO, EL OBJETIVO ES PREFERENCIA (2026-08-30, ronda 2 del
    # revisor). Habia aqui un `reb >= 2 t` que, con el techo de esbeltez
    # (`reb <= 3 x reh`), dejaba el fondo SIN BANDA: 2.99 rojo, 3.00 verde,
    # 3.01 rojo. Un diseno cuyo nominal es el unico valor legal no se puede
    # fabricar: cualquier tolerancia de fresado lo saca.
    #
    # Y las dos reglas no pesan igual. Lo que la fisica pide es que la chapa
    # quede CAPTURADA: su canto engancha reb - hol en z, y con menos de un
    # espesor deja de estarlo -- ese aserto ya existe abajo y da el suelo real,
    # t + hol = 2.0. Los 2 t eran holgura de mas que nos dimos, no una
    # condicion. Asi que el suelo pasa a ser el fisico y el 2 t se queda como
    # OBJETIVO declarado: el nominal se pone arriba de la banda y la tolerancia
    # del taller baja, que es el lado seguro (mas fondo aprieta la esbeltez del
    # reborde; menos fondo solo gasta captura, y sobra).
    assert reb >= t + hol - 1e-9, (
        f"el rebaje de chapa tiene {reb:g} de fondo y la chapa engancha "
        f"{reb - hol:g} en z, menos de un espesor ({t:g}): deja de estar "
        f"capturada entre el suelo y el reborde, y vuelve a posicionarla el "
        f"doblez")
    # --- el reborde: lo unico que se ve ------------------------------------
    # ESTE VA ANTES QUE EL DE ESBELTEZ A PROPOSITO: un reborde de 0.5 falla los
    # dos (0.5 de ancho, y 6:1), y de los dos textos el accionable es este. El
    # barrido del 30-08 lo caz~o al reves y por eso estan en este orden.
    assert reh >= 1.0 - 1e-9, (
        f"el reborde mide {reh:g} de ancho: por debajo de 1 deja de ser una "
        f"junta de sombra fresable y pasa a ser una rebaba")
    assert reb <= ESBELTEZ_MAX_PARED * reh + 1e-9, (
        f"el reborde queda de {reh:g} de ancho por {reb:g} de alto "
        f"({reb/reh:.1f}:1) y la fresa no pasa de {ESBELTEZ_MAX_PARED:g}:1: es "
        f"la cota mas delicada de la pieza, y a esa esbeltez el taller la "
        f"rompe o pide prima. Sube rehundido_chapa antes que el fondo")

    # --- la holgura del canto, por los dos lados ---------------------------
    assert hol >= 0.3 - 1e-9, (
        f"la holgura del canto de la chapa contra la pared del rebaje es "
        f"{hol:g}: una chapa cortada a +-0.3 no entra si viene larga")
    # (el techo de hol_chapa lo pone el mismo aserto de captura de arriba:
    #  reb >= t + hol y reb - hol >= t son la misma desigualdad, y tenerla dos
    #  veces solo servia para que un canario saltara por el gemelo equivocado)

    # --- el ancho del rebaje: la fresa tiene que entrar ---------------------
    ancho = _rehundido_trasera(p) - reh
    assert ancho >= p["fresa_d"] - 1e-9, (
        f"el rebaje mide {ancho:.2f} de ancho y la fresa del pliego es de "
        f"Ø{p['fresa_d']:g}: no entra. El ancho es t + aire_labios - junta, o "
        f"sea que lo manda la rendija: subir aire_labios lo ensancha")
    assert ancho - t >= 1.0 - 1e-9, (
        f"tras la chapa quedan {ancho-t:.2f} mm hasta el suelo del rebaje: sin "
        f"1 mm de aire el suelo pasa a posicionar la chapa, y quien tiene que "
        f"posicionarla son las bridas y los M4 de los pies")

    # --- los derivados, contra su propia definicion -------------------------
    # No son asertos de diseno: son el cruce de las dos formulas gemelas. Si
    # alguien toca una y no la otra, el modelo y el presupuesto dibujan piezas
    # distintas y nadie se entera hasta el taller.
    luz = p["ancho_total"] - 2 * (p["t_anillo"] - reb)
    assert abs(_chapa_largo_rebaje(p) - (luz - 2 * hol)) < 1e-9, (
        f"lo que entra en rebaje mide {_chapa_largo_rebaje(p):.2f} por la via "
        f"de la muesca y {luz - 2*hol:.2f} por la via de la luz entre paredes: "
        f"las dos formulas gemelas no dicen lo mismo")
    assert abs(_radio_borde(p) - (p["radio_chapa"] + reh)) < 1e-9
    assert abs(_muesca_pie(p) - (reb - hol + p["hol_piel"])) < 1e-9

    # --- la muesca del pie y su alivio -------------------------------------
    m = _muesca_pie(p)
    assert m > 0, (
        f"la muesca del pie sale {m:g}: con rebaje {reb:g} y holgura {hol:g} el "
        f"pie mediria mas que lo que entra en rebaje, y no hay nada que cortar")
    assert m + p["alivio_pestana"] / 2 <= p["nariz_pie"] - 1e-9, (
        f"la muesca de {m:g} mas medio alivio de Ø{p['alivio_pestana']:g} se "
        f"come el pie de la nariz ({p['nariz_pie']:g}): el alivio caeria fuera "
        f"del pie en vez de a caballo de la linea de doblez")

    print(f"rebaje de chapa: {ancho:.2f} x {reb:g} en la cara interior, chapa "
          f"rehundida {reh:g} con reborde de {reh:g} x {reb:g} "
          f"({reb/reh:.1f}:1); entra {_chapa_largo_rebaje(p):.2f} entre paredes "
          f"(luz {luz:.2f} - 2 x {hol:g}); muesca del pie {m:g}")
    # EL FONDO ESTA EN UNA ESQUINA, y conviene decirlo en cada corrida en vez de
    # que alguien lo descubra con un rojo raro: 2 t por abajo y 3:1 por arriba
    # se cruzan justo en 3, asi que con t = 1.5 y reborde de 1 el rebaje NO
    # tiene rango -- 2.9 y 3.1 son rojos por motivos opuestos. La salida es la
    # pregunta del RFQ: si el taller pide un reborde de 1.5, la ventana se abre
    # de 3 a 4.5. No es fragilidad de la puerta: es que el diseno vive ahi.
    lo, hi = t + hol, ESBELTEZ_MAX_PARED * reh
    print(f"  el fondo puede ir de {lo:g} a {hi:g} (captura de un espesor por "
          f"abajo, {ESBELTEZ_MAX_PARED:g}:1 del reborde por arriba) y el "
          f"nominal es {reb:g}: la tolerancia del taller baja, que es el lado "
          f"seguro. Objetivo de captura 2 t = {2*t:g}, que se cumple con "
          f"{reb - hol:g} de enganche")
    if hi - lo < 0.4:
        print(f"  aviso: esa banda mide {hi - lo:g} y una fresa no la sostiene. "
              f"Subir rehundido_chapa la ensancha por arriba")


def guarda_tramo_trasero(p: dict[str, float]) -> None:
    """La cara vertical P5-P6 del anillo, donde se cruzan TRES vaciados: el
    bolsillo de la trasera, el rebaje del costado (vacio desde el 2026-10-11:
    la mejilla la sustituyo la persiana) y -- desde el 2026-08-30 -- el
    rebaje de chapa bajo los dos labios (el del techo arriba, el del talon
    abajo). Es el sitio mas cargado de la pieza, y el unico donde la franja no
    mide cara_anillo.

    Lo que hay en cada banda de altura, de fuera a dentro (§4.3 de la spec):

      y = 6..19 y 230.18..239.18  (bajo los labios de chapa)
        z 11..14  reborde 0..1; UN SOLO VACIADO de 1 a 15.5 (rebaje + bolsillo);
                  pared; rebaje vacio
        z  8..11  labio del bolsillo 0..4.5 con 3 DE HONDO; bolsillo; pared;
                  rebaje vacio
      y = 19..230.18  (sin chapa)
        z  8..14  labio del bolsillo con los 6 de hondo de siempre
      y = 239.18..250.18  (fin del bolsillo, y la brida)
        z 11..14  reborde; rebaje; y desde 240.18 el cajeado de la brida

    De ahi salen las dos cosas que esta puerta mide: que bajo los labios el
    labio del bolsillo conserve cuerpo, y que la pared entre vaciados no baje
    de PARED_MIN_ANILLO. Media tambien una tercera -- que el costado entrara
    al menos 3 y nunca mas que rebaje_anillo --, y murio con la mejilla el
    2026-10-11: entrada_costado_trasero sigue dibujando la franja trasera, pero
    ya no entra nada en ese rebaje."""
    bo = _bolsillo_trasero(p)
    reb, reh = p["rebaje_chapa"], p["rehundido_chapa"]

    # --- la pared entre los dos bolsillos, contra la constante --------------
    # Estaba en guarda_trasera_capturada() contra el literal 3. Vive aqui y
    # contra PARED_MIN_ANILLO: es la pared del anillo, no una cota de la
    # trasera, y el dia que el aluminio o la fresa cambien se sube una vez.
    assert bo["pared"] >= PARED_MIN_ANILLO - 1e-9, (
        f"la pared entre el bolsillo de la trasera y el rebaje del costado mide "
        f"{bo['pared']:g} contra {PARED_MIN_ANILLO:g} de minimo: pared de "
        f"{bo['pared']:g} contra {PARED_MIN_ANILLO:g}")
    # POR ARRIBA la manda la franja: la pared, el bolsillo y lo que entra el
    # costado tienen que caber en cara_anillo_trasera, y esa franja es lo que
    # se ve de aluminio desde el lado. Sin este lado, pared = 100 quedaba verde
    # y el anillo salia con una franja trasera de 119 (revisor del 30-08).
    assert _cara_anillo_trasera(p) <= p["cara_anillo"] + 6.0 + 1e-9, (
        f"la franja del tramo trasero mide {_cara_anillo_trasera(p):g} y la de "
        f"los otros seis tramos {p['cara_anillo']:g}: mas de 6 de diferencia "
        f"deja de leerse como el mismo anillo y se ve un escalon desde el lado")

    # --- el labio del bolsillo bajo los dos labios de chapa ----------------
    # Donde hay chapa, el rebaje (z = 11..14) se come los 3 de arriba del labio
    # del bolsillo y lo deja en z = 8..11. Lo que queda tiene que seguir
    # parando la plancha hacia fuera; por encima lo hace el propio labio de la
    # chapa, que a aire_labios de aire con los tacos no la deja salir.
    labio_bajo_chapa = p["rebaje_anillo"] - reb
    assert labio_bajo_chapa >= 3.0 - 1e-9, (
        f"bajo los labios de chapa el labio del bolsillo queda con "
        f"{labio_bajo_chapa:g} de hondo (rebaje_anillo {p['rebaje_anillo']:g} - "
        f"rebaje_chapa {reb:g}): con menos de 3 deja de sujetar la plancha en la "
        f"banda donde el techo y el talon ya no ayudan")

    # --- el rebaje y el bolsillo se funden: no puede quedar una aleta -------
    # El suelo del rebaje esta en u = rehundido_trasera y la pared exterior del
    # bolsillo tambien: son el mismo plano POR CONSTRUCCION (rehundido_trasera
    # se deriva de la rendija y el bolsillo arranca ahi). Si algun dia dejan de
    # coincidir queda una aleta de aluminio de menos de un milimetro colgando
    # entre los dos vaciados, que se rompe al fresar.
    assert abs(bo["u0"] - _rehundido_trasera(p)) < 1e-9, (
        f"el suelo del rebaje de chapa (u = {_rehundido_trasera(p):g}) y la "
        f"pared exterior del bolsillo (u = {bo['u0']:g}) tienen que ser el mismo "
        f"plano: si no, queda una aleta entre los dos vaciados")
    assert reh < bo["u0"] - 1e-9, (
        f"el reborde llega a u = {reh:g} y el bolsillo arranca en "
        f"{bo['u0']:g}: el reborde se comeria la boca del bolsillo")

    # --- el bolsillo sigue cerrado, y el cajeado empieza despues -----------
    y_fin = bo["y_fin"]
    y_cajeado = _vertices(p)[5][1] - p["marco_sup"] - p["brida_ancho"] - p["hol_chapa"]
    assert y_cajeado > y_fin - 1e-9, (
        f"el cajeado de la brida arranca en y = {y_cajeado:.2f} y el bolsillo de "
        f"la trasera no cierra hasta {y_fin:.2f}: se solapan, y el M4 de dentro "
        f"de la brida volveria a roscar sobre la boca del bolsillo")

    print(f"tramo trasero: franja {_cara_anillo_trasera(p):g} (bolsillo "
          f"{bo['u0']:g}..{bo['u1']:g}, pared {bo['pared']:g}, rebaje vacio "
          f"{p['entrada_costado_trasero']:g}); bajo los labios de chapa el labio del bolsillo queda "
          f"con {labio_bajo_chapa:g} de hondo y el rebaje con {reb:g}")
    # OTRA COTA SIN HOLGURA: rebaje_anillo - rebaje_chapa >= 3 se cumple con
    # IGUALDAD (6 - 3), o sea que el bolsillo del acrilico esta en su minimo
    # justo donde el rebaje de chapa se lo come. El barrido del 30-08 lo
    # encontro: 5.9 de bolsillo seria rojo. Junto con el fondo del rebaje (que
    # tampoco tiene rango, ver guarda_rebaje_chapa) esto dice que el empotrado
    # vive sin margen: la respuesta del taller a la pregunta del reborde mueve
    # varias cotas a la vez, no una.
    if labio_bajo_chapa - 3.0 < 0.05:
        print(f"  aviso: el labio del bolsillo bajo los labios de chapa esta "
              f"EN el minimo ({labio_bajo_chapa:g} contra 3). Subir "
              f"rebaje_chapa o bajar rebaje_anillo lo pone rojo")


# pata trasera en vez del 48 (apoyada-apoyada), que la dejaria en 2.95.
EMPOTRE_MAX = 100.0

# El contorno del marco en orden, tal como lo devuelve _marco_ventana(): las
# distancias por el contorno se miden con este orden.
CONTORNO_MARCO = ("chaflan", "frente", "cara_inf", "valle", "cara_sup",
                  "meseta", "trasera", "suelo")

# Las esquinas que NO empotran aunque la vecina lleve rosca cerca: la muesca
# de la brida deja en P5 un cuello de marco_fondo - b_muesca que sostiene pero
# no empotra. (pata, 0) es su esquina de arranque, (pata, 1) la del final.
CUELLOS_MARCO = {("meseta", 1), ("trasera", 0)}


def _m5_tabla_x(p: dict[str, float]) -> list[float]:
    """x de los M5 con que la tabla se rosca al CANTO inferior de cada anillo.
    GEMELA de la fila de bandeja_base_2d(): el fondo del CUERPO repartido en
    n_agujeros() con orillas de medio paso. Hasta el 10-10 se repartia el fondo
    de la tabla, y el vuelo (cota de mirar) movia las roscas del anillo: con 40
    pasaban de 3 a 4. Entran por el canto (y = 0) hacia arriba, centrados en
    los 14 del anillo: una rosca ciega del dorso que caiga en la misma x los
    cruza sin que ningun DXF lo ensene."""
    fb = _vertices(p)[6][0]
    n = max(1, math.floor(fb / p["reticula_paso"] + 0.5))
    return [fb * (i + 0.5) / n for i in range(n)]


def _m4_pie_borde(p: dict[str, float]) -> float:
    """Del canto libre del pie de nariz y talon al centro de su M4. Era 1.5 D;
    con D-T2 el M4 rosca en una tuerca de presion prensada en el pie, y la
    tuerca pide pem_borde al canto (papel del suelo, sec.3.4)."""
    return max(1.5 * p["d_M4_paso"], p["pem_borde"])


def _zonas_campo_base(p: dict[str, float]) -> list[tuple[float, float, float, float]]:
    """La L donde pueden ir los agujeros de la base, en mundo: (x0, x1, z0, z1).
    A va a la izquierda del chasis, de delante a atras; B, delante del chasis.
    Fuera quedan el canto de los anillos, los pies de nariz y talon y la huella
    del chasis, cada uno con base_orilla de margen. GEMELA de
    zonas_campo_base() en el .scad."""
    o = p["base_orilla"]
    c = _chasis(p)
    x0 = p["chaflan_nariz"] + p["nariz_pie"] + o
    x1 = _talon(p)["x_pie"] - o
    z0 = p["t_anillo"] + o
    z1 = p["ancho_total"] - p["t_anillo"] - o
    z_ch = (p["t_anillo"] + perfil(p)["ancho_util"] - p["chasis_margen_bandeja"]
            - c["tapa_x"])
    x_ch = _x_chasis_frente(p)
    return [(x0, x1, z0, z_ch - o), (x0, x_ch - o, z_ch - o, z1)]


def _campo_base(p: dict[str, float]) -> list[tuple[float, float]]:
    """Los centros (x, z) de los agujeros del campo, en mundo. Una sola red al
    tresbolillo anclada en la esquina de la L, que se queda con los agujeros
    que caben enteros en alguna de las dos zonas. Dos redes, cada una con su
    origen, dejarian en la costura un puente mas fino que el resto. GEMELA de
    campo_base() en el .scad: misma red, mismo filtro."""
    zonas = _zonas_campo_base(p)
    d, s = p["base_agujero"], p["base_paso"]
    r, fila = d / 2, s * math.sqrt(3) / 2
    x0, x1 = min(q[0] for q in zonas), max(q[1] for q in zonas)
    z0, z1 = min(q[2] for q in zonas), max(q[3] for q in zonas)
    ni = math.floor((x1 - x0 - d) / fila + 1e-9)
    nj = math.floor((z1 - z0 - d) / s + 1e-9)
    return [(x, z) for i in range(ni + 1) for j in range(nj + 1)
            for x, z in [(x0 + r + i * fila, z0 + r + (i % 2) * s / 2 + j * s)]
            if any(a + r - 1e-9 <= x <= b - r + 1e-9
                   and c + r - 1e-9 <= z <= e - r + 1e-9
                   for a, b, c, e in zonas)]


def _taladros_base(p: dict[str, float]) -> list[tuple[float, float, float, str]]:
    """Todo taladro de fijacion de la base, en mundo: (x, z, d, tipo). Los 6 M5
    de los anillos, los 3 + 3 M4 de nariz y talon (de paso: D-T2 los mete desde
    abajo a la tuerca de su pie), las 4 FH de las patas y los 4 M4 del chasis.
    Lo leen guarda_campo_base() y guarda_bandeja_base() en check_dxf."""
    nz, tl = _nariz(p), _talon(p)
    out = [(x, z, p["d_M5_base"], "M5") for x in _m5_tabla_x(p)
           for z in (p["t_anillo"] / 2, p["ancho_total"] - p["t_anillo"] / 2)]
    out += [(nz["m4_x"], z, p["d_M4_paso"], "M4 nariz") for z in nz["m4_z"]]
    out += [(tl["m4_x"], z, p["d_M4_paso"], "M4 talon") for z in tl["m4_z"]]
    out += [(x, z, p["pem_fh_m4"], "FH pata")
            for x in (p["alto_frontal"] / 2 + p["d_pie"] / 2,
                      tl["x_chaflan"] - p["talon_pie"] / 2)
            for z in (p["d_pie"] / 2, p["ancho_total"] - p["d_pie"] / 2)]
    out += [(yl, xl, p["d_M4_paso"], "M4 chasis") for xl, yl in _chasis_tornillos_tabla(p)]
    return out


def guarda_campo_base(p: dict[str, float]) -> None:
    """El campo de agujeros de la base: que respire lo que el aire cuenta sin
    debilitar la chapa ni pisar un inserto (papel del suelo, sec.3.2 y 5).

      1. El puente entre agujeros vecinos (la red es de paso base_paso en las
         tres direcciones) mide al menos el espesor: con menos, la mano apoyada
         plastifica el borde del agujero (Elke).
      2. Ningun agujero del campo queda a menos de pem_borde de un taladro de
         fijacion, de centro de taladro a canto de agujero.

    La huella del chasis no se asevera: la L se deriva de ella, y un aserto
    sobre lo que la propia construccion garantiza no puede fallar."""
    puente = p["base_paso"] - p["base_agujero"]
    assert puente >= p["t_base"] - 1e-9, (
        f"el puente del campo de la base mide {puente:.2f} mm (paso "
        f"{p['base_paso']:g} - agujero {p['base_agujero']:g}) y la chapa "
        f"{p['t_base']:g}: con la mano apoyada el borde del agujero plastifica. "
        f"Se pide un puente de una vez el espesor")
    campo = _campo_base(p)
    r = p["base_agujero"] / 2
    peor = min((math.hypot(x - tx, z - tz) - r, tipo)
               for x, z in campo for tx, tz, _d, tipo in _taladros_base(p))
    assert peor[0] >= p["pem_borde"] - 1e-9, (
        f"un agujero del campo queda a {peor[0]:.2f} mm de un taladro de "
        f"{peor[1]} y el inserto pide {p['pem_borde']:g} (pem_borde): sube "
        f"base_orilla o aparta el campo")
    abierto = len(campo) * math.pi * r * r
    print(f"base: {len(campo)} agujeros de {p['base_agujero']:g} cada "
          f"{p['base_paso']:g}, {abierto:.0f} mm2 abiertos; puente {puente:.1f} "
          f"contra {p['t_base']:g} de chapa; el mas cercano a un inserto, a "
          f"{peor[0]:.1f} mm ({peor[1]})")


def canario_campo_base(p: dict[str, float]) -> None:
    """Autocomprobacion ROJA de guarda_campo_base(): con el puente mas fino que
    la chapa, o con la distancia de un inserto mayor que la orilla que lo
    separa del campo, la puerta tiene que saltar y por SU razon; y con los
    parametros de verdad, callar."""
    for cambios, clave in (({"base_paso": p["base_agujero"] + p["t_base"] - 0.5}, "puente"),
                           ({"pem_borde": 25.0}, "inserto")):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                guarda_campo_base({**p, **cambios})
        except AssertionError as e:
            assert clave in str(e), (
                f"canario del campo: con {cambios} guarda_campo_base() salto, "
                f"pero por otra razon ('{str(e)[:80]}...')")
            continue
        raise AssertionError(
            f"canario del campo NO disparo con {cambios}: guarda_campo_base() "
            f"lo deja pasar -- no confiar en su VERDE")
    with contextlib.redirect_stdout(io.StringIO()):
        guarda_campo_base(dict(p))


def _flecha_pata(p: dict[str, float], L: float, b: float, empotres: int
                 ) -> tuple[float, float]:
    """Flecha y tension de un tramo del marco como viga de b x t_placa
    flexando en z (el empujon del acrilico) con carga_mano al centro, segun
    cuantos de sus dos extremos empotran: ninguno FL^3/48EI (M = FL/4), uno
    FL^3/107EI (3FL/16), los dos FL^3/192EI (FL/8)."""
    h = p["t_placa"]
    inercia = b * h ** 3 / 12
    W = b * h * h / 6
    F = p["carga_mano"]
    k, m = {0: (48.0, 0.25), 1: (107.0, 3.0 / 16.0), 2: (192.0, 0.125)}[empotres]
    return F * L ** 3 / (k * E_ALUMINIO * inercia), m * F * L / W


def guarda_marco_ventana(p: dict[str, float]) -> None:
    """El marco de la ventana: ocho patas, el canto donde toca, y cada tramo
    aguanta una mano con lo que tiene.

    Lo que mide, en orden: (1) el canto exterior de cada pata -- a la silueta
    en las tres filas, retirado t_costilla + hol_piel bajo cada chapa,
    retirado t_anillo + 0.5 detras, sobre la pared entre bolsillos --; (2) que
    la pata trasera no entre menos que las otras; (3) que cada pata aguante
    carga_mano por debajo de RP02: las patas CON roscas, por su vano mayor entre dos roscas como
    viga biempotrada; las patas SIN rosca (chaflan, frente, meseta y la
    trasera, que no puede llevarla porque en la franja trasera no cabe),
    enteras, y empotradas solo por las esquinas que lo merecen -- vecina con
    rosca a menos de EMPOTRE_MAX por el contorno y sin el cuello de la
    muesca --. Es lo que puso las dos roscas en la pata del suelo: sin ellas
    cedia 3.31 mm y era el tramo que sustituyo a los clips, que si llevaban;
    (4) que esas dos roscas no crucen los M5 de la tabla, que entran por el
    canto inferior del anillo en la misma franja; (5) que la muesca de la
    brida deje pata entera debajo -- es lo que puso brida_ancho en 14.5. Los
    agujeros contra el canto de su pata (las roscas del suelo a 6.85 del
    canto retirado, que pide 6.75) van en guarda_anclajes().

    EL CASO DE CARGA CAMBIO DE SUJETO EL 2026-10-11. Era el acrilico empujado
    desde fuera contra el marco, y con el se fueron dos asertos: que el marco
    pisara 6 de acrilico mas alla de la ventana, y que ninguna pata cediera mas
    de 2 mm, que era lo que el acrilico necesitaba para salirse del rebaje. La
    tension se queda: la persiana se quita para aspirar el interior por la
    ventana (spec de la persiana, §4), y entonces la mano llega al marco.
    marco_fondo_trasera = 30 se queda: lo puso el caso de carga que murio con
    la mejilla, y bajarlo no compra nada que se vea."""
    patas = _marco_ventana(p)
    por = {q["nombre"]: q for q in patas}
    rm, rmt = _retiro_marco(p), _retiro_marco_trasera(p)
    rmp = _retiro_marco_pie(p)
    # EL SUELO SE SEPARO DE LOS OTROS TRES EL 2026-08-30: bajo el chaflan, el
    # frente y la meseta va chapa EMPOTRADA (retiro rehundido + t + hol = 2.65);
    # sobre el suelo van los PIES, que no se rehunden porque la tabla los tapa,
    # y siguen con t + hol = 1.65. Que los cuatro compartieran retiro era
    # verdad hasta que la chapa se metio en el rebaje.
    for nm in ("chaflan", "frente", "meseta"):
        assert abs(por[nm]["retiro"] - rm) < 1e-9, nm
    assert abs(por["suelo"]["retiro"] - rmp) < 1e-9, (
        f"la pata del suelo se retira {por['suelo']['retiro']:.2f} y bajo ella "
        f"van los pies a ras, que piden {rmp:.2f}: si lleva el retiro de la "
        f"chapa empotrada, el marco se aparta 1 mm de mas justo donde no hay "
        f"nada que esquivar")
    for nm in ("cara_inf", "valle", "cara_sup"):
        assert por[nm]["retiro"] == 0.0, nm
    assert abs(por["trasera"]["retiro"] - rmt) < 1e-9
    sombra = p["marco_fondo"] - p["cara_anillo"]
    # LA PATA TRASERA ENTRA marco_fondo_trasera, y nunca menos que las demas:
    # por debajo de marco_fondo el .scad la dibujaria a marco_fondo (la ventana
    # manda) y esta gemela no.
    assert p["marco_fondo_trasera"] >= p["marco_fondo"] - 1e-9, (
        f"marco_fondo_trasera = {p['marco_fondo_trasera']:g} < marco_fondo = "
        f"{p['marco_fondo']:g}: la pata trasera no puede entrar menos que las otras")
    sombra_tr = p["marco_fondo_trasera"] - p["cara_anillo"]
    # (3) las roscas de cada pata, en s a lo largo de ella, y en S por el
    # contorno cerrado
    assert tuple(q["nombre"] for q in patas) == CONTORNO_MARCO
    s_de: dict[str, list[float]] = {nm: [] for nm in por}
    for nm, c in _roscas_marco(p):
        q = por[nm.split(" ")[1]]
        s_de[q["nombre"]].append((c[0] - q["A"][0]) * q["u"][0]
                                 + (c[1] - q["A"][1]) * q["u"][1])
    acum, S = {}, 0.0
    for nm in CONTORNO_MARCO:
        acum[nm] = S
        S += por[nm]["L"]
    total = S
    S_roscas = sorted(acum[nm] + s for nm in CONTORNO_MARCO for s in s_de[nm])

    def hasta_rosca(S_esq: float, sentido: int) -> float:
        if sentido > 0:
            c = [Sr - S_esq for Sr in S_roscas if Sr >= S_esq - 1e-9]
            return min(c) if c else S_roscas[0] + total - S_esq
        c = [S_esq - Sr for Sr in S_roscas if Sr <= S_esq + 1e-9]
        return min(c) if c else S_esq + total - S_roscas[-1]

    filas = []
    for q in patas:
        nm, b = q["nombre"], q["fondo"] - q["retiro"]
        if s_de[nm]:
            ss = sorted(s_de[nm])
            vanos = [b2 - a2 for a2, b2 in zip(ss, ss[1:])]
            L = max(vanos) if vanos else 0.0
            flecha, sigma = _flecha_pata(p, L, b, 2)
            modo = f"{len(ss)} roscas, vano mayor {L:.1f} entre dos"
        else:
            d0 = hasta_rosca(acum[nm], -1)
            d1 = hasta_rosca(acum[nm] + q["L"], +1)
            emp = sum(1 for d, k in ((d0, 0), (d1, 1))
                      if d <= EMPOTRE_MAX and (nm, k) not in CUELLOS_MARCO)
            L = q["s1"] - q["s0"]
            flecha, sigma = _flecha_pata(p, L, b, emp)
            modo = (f"sin tornillo, {L:.1f} de largo, {emp} esquina(s) "
                    f"empotrada(s) (rosca vecina a {d0:.0f} y {d1:.0f} por el "
                    f"contorno)")
        assert sigma <= RP02_ALUMINIO, (
            f"la pata '{nm}' del marco trabaja a {sigma:.0f} MPa con "
            f"{p['carga_mano']:.0f} N ({modo}); RP02 = {RP02_ALUMINIO:g}")
        filas.append((nm, b, flecha, sigma, modo))
    # (4) las roscas del suelo contra los M5 de la tabla, en x
    d_min = (p["d_M5_rosca"] + p["d_M4_rosca"]) / 2 + 2.0
    for nm, c in _roscas_marco(p):
        if not nm.startswith("marco suelo"):
            continue
        for xm in _m5_tabla_x(p):
            assert abs(c[0] - xm) >= d_min, (
                f"la rosca '{nm}' del marco cae en x={c[0]:.2f} y el M5 de la "
                f"tabla entra por el canto inferior del anillo en x={xm:.2f}: "
                f"a {abs(c[0] - xm):.2f}, y las dos brocas piden {d_min:.2f}. "
                f"Mueve rosca_suelo_retiro")
    # (5) la muesca de la brida deja pata entera
    s_mu, b_mu = por["meseta"]["muesca"]
    entera = p["marco_fondo"] - b_mu
    assert entera >= 8.0, (
        f"bajo la muesca de la brida quedan {entera:.2f} mm de pata en la "
        f"meseta; con menos de 8 la esquina trasera-alta del marco es un cuello. "
        f"Baja brida_ancho")
    print(f"marco de la ventana: {len(patas)} patas de {p['t_placa']:g} hasta "
          f"{p['marco_fondo']:g} de la silueta; canto a la silueta en las filas, "
          f"retirado {rm:.2f} bajo la chapa y {rmt:.2f} en la trasera; entra "
          f"{sombra:g} mas alla de la ventana en seis tramos y {sombra_tr:g} en "
          f"la trasera; "
          f"{len(S_roscas)} roscas")
    for nm, b, flecha, sigma, modo in filas:
        if flecha >= 0.05:
            print(f"  pata {nm} {b:.2f} x {p['t_placa']:g}: {flecha:.2f} mm y "
                  f"{sigma:.0f} MPa con {p['carga_mano']:.0f} N ({modo})")
    xs = ", ".join(f"{x:.1f}" for x in _m5_tabla_x(p))
    print(f"  roscas del suelo en x={', '.join(f'{c[0]:.1f}' for nm, c in _roscas_marco(p) if nm.startswith('marco suelo'))}, "
          f"los M5 de la tabla en x={xs}; muesca de la brida de {b_mu:.2f} deja "
          f"{entera:.2f} de pata")


# Material minimo alrededor de un taladro, en diametros de canto a centro. Es
# el mismo criterio que check_dxf.py aplica a los cantos de las piezas planas;
# vive aqui porque desde el 2026-08-27 tambien lo necesita el ESQUELETO, y no en
# el canto de un contorno sino en el espesor de la chapa que recibe el tornillo.
AGARRE_MIN_D = 1.5


# Separacion entre centros de taladro que Intellijel PUBLICA para su 1U, en mm.
# FUENTE: intellijel.com/support/1u-technical-specifications/ (consultada el
# 2026-08-27). El diagrama de esa pagina vive dentro de una imagen y no se pudo
# leer con la maquina: la cifra viene del hilo tecnico de MOD WIGGLER y de la
# ficha del formato. PENDIENTE DE CONFIRMAR CONTRA EL DIAGRAMA.
#
# Vive aqui y no en params.scad a proposito: NO es una cota nuestra ni define
# compatibilidad. Es solo la referencia minima externa contra la que se compara
# la separacion propia de KONDOR.
S_1U_INTELLIJEL = 33.65
ALTO_FILA_KONDOR = 55.00
S_FILA_KONDOR = 49.00
ALTO_FILA_AUX_ANTERIOR = 39.65
PASO_HORIZONTAL_ANTERIOR = 58.47
DESPLAZAMIENTO_SEGUNDO_RIEL_KONDOR = 15.35
REHUNDIDO_PANEL_OBJETIVO = 1.50


def _firma_marco_sin_ejes(p: dict[str, float]) -> tuple:
    """Geometria material del marco, excluyendo centros y cajeados de riel."""
    def punto(q):
        return (round(q[0], 9), round(q[1], 9))

    return tuple(
        (q["nombre"], round(q["s0"], 9), round(q["s1"], 9),
         round(q["retiro"], 9), round(q["fondo"], 9),
         tuple(punto(v) for v in q["poligono"]),
         tuple(tuple(punto(v) for v in c) for c in q["convexos"]))
        for q in _marco_ventana(p)
    )


def _geometria_rehundido_panel(p: dict[str, float]) -> dict[str, object]:
    """Desplazamiento de paneles, rieles y cajeados fijos en tres filas."""
    ras = dict(p)
    ras["rehundido_panel"] = 0.0
    P0, P = _vertices(ras), _vertices(p)
    cr0, cr = _centros_rail(ras, P0), _centros_rail(p, P)
    ck0 = _centros_rail_1u(ras, P0, cr0)
    ck = _centros_rail_1u(p, P, cr)
    pasos0 = dict(_pasos_riel_marco(ras))
    pasos = dict(_pasos_riel_marco(p))
    rehundido_panel = p.get("rehundido_panel", 0.0)

    def fila(nombre: str, centros0: list[tuple[float, float]],
             centros: list[tuple[float, float]],
             normal: tuple[float, float],
             origen: tuple[float, float],
             panel_sigue_primer_riel: bool = False) -> dict[str, object]:
        desplazamientos = [
            (c[0] - c0[0]) * normal[0] + (c[1] - c0[1]) * normal[1]
            for c0, c in zip(centros0, centros)
        ]
        laterales = [
            (c[0] - c0[0]) * -normal[1] + (c[1] - c0[1]) * normal[0]
            for c0, c in zip(centros0, centros)
        ]
        tangente = (-normal[1], normal[0])
        contactos = []
        for c in centros:
            s = ((c[0] - origen[0]) * tangente[0]
                 + (c[1] - origen[1]) * tangente[1])
            q = (origen[0] + tangente[0] * s,
                 origen[1] + tangente[1] * s)
            profundidad_eje = ((c[0] - q[0]) * normal[0]
                               + (c[1] - q[1]) * normal[1])
            cara_riel = profundidad_eje - p["rail_er_eje"]
            cara_interior_panel = rehundido_panel + p["t_panel"]
            contactos.append(cara_riel - cara_interior_panel)
        desplazamientos_cajeado = []
        laterales_cajeado = []
        for c0, c in zip(centros0, centros):
            nombre_paso0 = next(n for n, q in pasos0.items()
                                if math.hypot(q[0] - c0[0], q[1] - c0[1]) < 0.001)
            nombre_paso = next(n for n, q in pasos.items()
                               if math.hypot(q[0] - c[0], q[1] - c[1]) < 0.001)
            q0, q = pasos0[nombre_paso0], pasos[nombre_paso]
            desplazamientos_cajeado.append(
                (q[0] - q0[0]) * normal[0] + (q[1] - q0[1]) * normal[1])
            laterales_cajeado.append(
                (q[0] - q0[0]) * -normal[1] + (q[1] - q0[1]) * normal[0])
        return {
            "nombre": nombre,
            "panel": rehundido_panel,
            "panel_lateral": laterales[0] if panel_sigue_primer_riel else 0.0,
            "rieles": desplazamientos,
            "laterales": laterales,
            "cajeados": desplazamientos_cajeado,
            "laterales_cajeado": laterales_cajeado,
            "contactos": contactos,
        }

    ai = math.radians(p["angulo_inferior"])
    as_ = math.radians(p["angulo_superior"])
    filas = [
        fila("inferior", cr0[0:2], cr[0:2],
             (math.cos(ai), -math.sin(ai)), P[1]),
        fila("superior", cr0[2:4], cr[2:4],
             (math.cos(as_), -math.sin(as_)), P[3]),
        fila("KONDOR", ck0, ck, (0.0, -1.0), P[3], True),
    ]
    return {
        "filas": filas,
        "anillo_inmovil": P == P0,
        "marco_inmovil": _firma_marco_sin_ejes(p) == _firma_marco_sin_ejes(ras),
    }


def _guarda_rehundido_panel(g: dict[str, object]) -> None:
    """Contrato del rehundido conjunto, independiente de la formula que lo crea."""
    filas = g["filas"]
    assert isinstance(filas, list) and len(filas) == 3
    todos = [v for f in filas
             for k in ("panel", "rieles", "cajeados")
             for v in ([f[k]] if isinstance(f[k], float) else f[k])]
    assert any(abs(float(v)) > 0.001 for v in todos), (
        "rehundido cero: la geometria sigue a ras")
    for f in filas:
        panel = float(f["panel"])
        assert abs(panel - REHUNDIDO_PANEL_OBJETIVO) < 0.001, (
            f"panel inmovil en la fila {f['nombre']}: rehundido real "
            f"{panel:.2f}, se exigen {REHUNDIDO_PANEL_OBJETIVO:.2f} mm")
        rieles = [float(v) for v in f["rieles"]]
        assert max(rieles) - min(rieles) < 0.001, (
            f"desplazamiento desigual de rieles en la fila {f['nombre']}: "
            f"{rieles}")
        assert all(abs(v - REHUNDIDO_PANEL_OBJETIVO) < 0.001 for v in rieles), (
            f"riel inmovil en la fila {f['nombre']}: desplazamientos {rieles}, "
            f"se exigen {REHUNDIDO_PANEL_OBJETIVO:.2f} mm")
        cajeados = [float(v) for v in f["cajeados"]]
        assert max(cajeados) - min(cajeados) < 0.001, (
            f"desplazamiento desigual de ejes/cajeados en la fila "
            f"{f['nombre']}: {cajeados}")
        assert all(abs(v - REHUNDIDO_PANEL_OBJETIVO) < 0.001 for v in cajeados), (
            f"los ejes/cajeados de la fila {f['nombre']} no acompanaron al "
            f"riel: {cajeados}")
        panel_lateral = float(f["panel_lateral"])
        assert all(abs(float(v) - panel_lateral) < 0.001
                   for v in f["laterales"]), (
            f"desplazamiento desigual a lo largo de la fila {f['nombre']}: "
            f"panel {panel_lateral:.3f}, rieles {f['laterales']}")
        assert all(abs(float(v) - panel_lateral) < 0.001
                   for v in f["laterales_cajeado"]), (
            f"los ejes/cajeados de la fila {f['nombre']} no siguieron su "
            f"desplazamiento lateral: {f['laterales_cajeado']}")
        assert all(abs(float(v)) < 0.001 for v in f["contactos"]), (
            f"se perdio el contacto panel-riel en la fila {f['nombre']}: "
            f"gaps {f['contactos']}")
    assert g["anillo_inmovil"], "el anillo se movio al rehundir los paneles"
    assert g["marco_inmovil"], "el marco se movio al rehundir los paneles"


def guarda_rehundido_panel(p: dict[str, float]) -> None:
    g = _geometria_rehundido_panel(p)
    _guarda_rehundido_panel(g)
    print("rehundido panel: 1.50 mm reales en las tres filas; panel, riel y "
          "cajeados fijos se mueven juntos; anillo y marco inmoviles")


def canario_rehundido_panel() -> None:
    """Panel/riel inmoviles, movimiento desigual y rehundido cero deben caer."""
    def valida() -> dict[str, object]:
        return {
            "filas": [
                {"nombre": nombre, "panel": REHUNDIDO_PANEL_OBJETIVO,
                 "panel_lateral": 0.0,
                 "rieles": [REHUNDIDO_PANEL_OBJETIVO] * 2,
                 "laterales": [0.0, 0.0],
                 "cajeados": [REHUNDIDO_PANEL_OBJETIVO] * 2,
                 "laterales_cajeado": [0.0, 0.0],
                 "contactos": [0.0, 0.0]}
                for nombre in ("inferior", "superior", "KONDOR")
            ],
            "anillo_inmovil": True,
            "marco_inmovil": True,
        }

    casos = []
    g = valida()
    g["filas"][0]["panel"] = 0.0
    casos.append((g, "panel inmovil", "panel inmovil"))
    g = valida()
    g["filas"][0]["rieles"] = [0.0, 0.0]
    casos.append((g, "riel inmovil", "riel inmovil"))
    g = valida()
    g["filas"][1]["rieles"] = [1.50, 1.40]
    casos.append((g, "desplazamiento desigual", "desplazamiento desigual"))
    g = valida()
    for f in g["filas"]:
        f["panel"] = 0.0
        f["rieles"] = [0.0, 0.0]
        f["cajeados"] = [0.0, 0.0]
    casos.append((g, "rehundido cero", "rehundido cero"))

    for roto, clave, que in casos:
        try:
            _guarda_rehundido_panel(roto)
        except AssertionError as e:
            assert clave in str(e), (
                f"canario de rehundido ({que}) salto por '{str(e)}' y no por "
                f"'{clave}'")
            continue
        raise AssertionError(
            f"canario de rehundido NO disparo con {que}; no confiar en su VERDE")


def _guarda_transicion_fila_kondor(
        centros_anteriores: list[tuple[float, float]],
        centros_kondor: list[tuple[float, float]]) -> None:
    """Solo el segundo riel responde al cambio de alto de 39.65 a 55.00."""
    dx0 = centros_kondor[0][0] - centros_anteriores[0][0]
    dy0 = centros_kondor[0][1] - centros_anteriores[0][1]
    assert math.hypot(dx0, dy0) < 0.001, (
        f"el primer riel KONDOR se movio ({dx0:+.3f}, {dy0:+.3f}) mm al "
        f"mutar el alto {ALTO_FILA_AUX_ANTERIOR:.2f} <-> "
        f"{ALTO_FILA_KONDOR:.2f}; tiene que quedar invariante")

    dx1 = centros_kondor[1][0] - centros_anteriores[1][0]
    dy1 = centros_kondor[1][1] - centros_anteriores[1][1]
    assert (abs(dx1 - DESPLAZAMIENTO_SEGUNDO_RIEL_KONDOR) < 0.001
            and abs(dy1) < 0.001), (
        f"el segundo riel KONDOR se movio ({dx1:+.3f}, {dy1:+.3f}) mm; "
        f"solo el debe moverse exactamente "
        f"{DESPLAZAMIENTO_SEGUNDO_RIEL_KONDOR:.2f} mm en X")


def _guarda_transicion_tanda_b(
        centros_anteriores: list[tuple[float, float]],
        centros_kondor: list[tuple[float, float]]) -> None:
    """Contrato completo desde la geometria anterior a la Tanda B.

    El rehundido baja ambos rieles 1.50 mm. El cambio de alto conserva la X del
    primero y desplaza solo el segundo 15.35 mm. Medir ambas decisiones juntas
    evita que una referencia movil de la ventana esconda deriva lateral.
    """
    esperados = ((0.0, -REHUNDIDO_PANEL_OBJETIVO),
                 (DESPLAZAMIENTO_SEGUNDO_RIEL_KONDOR,
                  -REHUNDIDO_PANEL_OBJETIVO))
    nombres = ("primer", "segundo")
    for nombre, anterior, actual, esperado in zip(
            nombres, centros_anteriores, centros_kondor, esperados):
        dx, dy = actual[0] - anterior[0], actual[1] - anterior[1]
        assert (abs(dx - esperado[0]) < 0.001
                and abs(dy - esperado[1]) < 0.001), (
            f"el {nombre} riel KONDOR deriva ({dx:+.6f}, {dy:+.6f}) mm "
            f"desde la geometria anterior; se exige "
            f"({esperado[0]:+.2f}, {esperado[1]:+.2f}) mm")


def _guarda_ancho_hp_fila_kondor(ancho_kondor: float,
                                  anchos_3u: list[float], hp: float) -> None:
    """La fila propia cruza el mismo ancho y publica los mismos HP que 3U."""
    hp_kondor = round(ancho_kondor / hp)
    hp_3u = {round(ancho / hp) for ancho in anchos_3u}
    assert hp_3u == {hp_kondor}, (
        f"la fila KONDOR da {hp_kondor} HP y las filas 3U dan "
        f"{sorted(hp_3u)} HP")
    assert all(abs(ancho_kondor - ancho) < 0.001 for ancho in anchos_3u), (
        f"la fila KONDOR mide {ancho_kondor:.2f} mm y los rieles 3U miden "
        f"{', '.join(f'{ancho:.2f}' for ancho in anchos_3u)} mm")


def guarda_fila_1u(p: dict[str, float]) -> None:
    """La fila del valle es la fila auxiliar KONDOR de 55 mm.

    Conserva ancho, HP y herraje de las dos filas 3U, pero su alto y su
    separacion vertical son propios. S_1U_INTELLIJEL no define la fila: queda
    unicamente como referencia minima externa."""
    H = p["alto_panel_1u"]
    S = H - 2 * p["inset_er"]
    assert abs(H - ALTO_FILA_KONDOR) < 0.01, (
        f"el alto de la fila auxiliar KONDOR es {H:.2f} y tiene que ser "
        f"{ALTO_FILA_KONDOR:.2f}")
    assert S + 0.01 >= S_1U_INTELLIJEL, (
        f"la separacion KONDOR de {S:.2f} queda por debajo de la referencia "
        f"minima externa Intellijel de {S_1U_INTELLIJEL:.2f}; esto no afirma "
        f"compatibilidad")
    assert abs(S - S_FILA_KONDOR) < 0.01, (
        f"la separacion KONDOR derivada de alto_panel_1u - 2*inset_er es "
        f"{S:.2f} y tiene que ser {S_FILA_KONDOR:.2f}")

    # LA VENTANA, no la boca: sin bahia, la fila cabe o no cabe entre las
    # envolventes cerradas de los dos rieles fijos que limitan el valle.
    # Lo que sobre es paso_horizontal de mas: cada mm de valle es un mm de
    # fondo de aparato, y hoy sobran los 3 que ocupaban las dos alas.
    P = _vertices(p)
    cr = _centros_rail(p, P)
    x0, x1 = _ventana_valle(p, P, cr)
    pide = S + p["rail_er_alto"]
    sobra = (x1 - x0) - pide
    assert sobra >= -0.01, (
        f"la ventana del valle mide {x1 - x0:.2f} y la fila KONDOR pide "
        f"{pide:.2f} (separacion {S:.2f} + el alto de un riel). Se gobierna "
        f"con paso_horizontal, el largo del tramo plano del valle")

    anterior = dict(p)
    anterior["alto_panel_1u"] = ALTO_FILA_AUX_ANTERIOR
    anterior["paso_horizontal"] = PASO_HORIZONTAL_ANTERIOR
    P_anterior = _vertices(anterior)
    cr_anterior = _centros_rail(anterior, P_anterior)
    x0_a, x1_a = _ventana_valle(anterior, P_anterior, cr_anterior)
    S_anterior = ALTO_FILA_AUX_ANTERIOR - 2 * anterior["inset_er"]
    # La ventana geometrica anterior tenia 3 mm que ocupaban las dos alas de
    # t_costilla de la bahia. Su margen UTIL era por tanto el geometrico menos
    # 2*t_costilla: 0.003 mm. La bahia ya no existe, pero este es el margen
    # anterior que la cota 70.82 conserva.
    margen_anterior = ((x1_a - x0_a)
                       - (S_anterior + anterior["rail_er_alto"]
                          + 2 * anterior["t_costilla"]))
    assert abs(sobra - margen_anterior) < 0.01, (
        f"la ventana KONDOR deja {sobra:.3f} mm de margen y la anterior dejaba "
        f"{margen_anterior:.3f}; paso_horizontal tiene que conservar el margen "
        f"anterior")

    anterior_mismo_paso = dict(p)
    anterior_mismo_paso["alto_panel_1u"] = ALTO_FILA_AUX_ANTERIOR
    P_ant_paso = _vertices(anterior_mismo_paso)
    cr_ant_paso = _centros_rail(anterior_mismo_paso, P_ant_paso)
    c_anterior = _centros_rail_1u(anterior_mismo_paso, P_ant_paso, cr_ant_paso)
    c_kondor = _centros_rail_1u(p, P, cr)
    _guarda_transicion_fila_kondor(c_anterior, c_kondor)

    historica = dict(p)
    historica["alto_panel_1u"] = ALTO_FILA_AUX_ANTERIOR
    historica["paso_horizontal"] = PASO_HORIZONTAL_ANTERIOR
    historica["rehundido_panel"] = 0.0
    P_historica = _vertices(historica)
    cr_historica = _centros_rail(historica, P_historica)
    c_historica = _centros_rail_1u(historica, P_historica, cr_historica)
    _guarda_transicion_tanda_b(c_historica, c_kondor)

    railes, _, _ = _cajas_solidas(p)
    anchos_3u = [c[6] - c[5] for c in railes if c[0] in NOMBRES_CR]
    anchos_kondor = [c[6] - c[5] for c in railes
                     if c[0].startswith("fila KONDOR")]
    assert len(anchos_3u) == 4 and len(anchos_kondor) == 2, (
        f"se esperaban cuatro rieles 3U y dos KONDOR; aparecen "
        f"{len(anchos_3u)} y {len(anchos_kondor)}")
    _guarda_ancho_hp_fila_kondor(anchos_kondor[0], anchos_3u, p["hp"])
    assert abs(anchos_kondor[1] - anchos_kondor[0]) < 0.001, (
        f"los dos rieles KONDOR no tienen el mismo ancho: "
        f"{anchos_kondor[0]:.2f} y {anchos_kondor[1]:.2f}")

    # Debajo del riel no hay bandeja: el tile cuelga en el interior, como los
    # modulos 3U. Lo que tiene debajo es la tabla, a esta altura.
    y_riel = c_kondor[0][1] - _he_er(p, 90.0)[1]
    hp_kondor = round(anchos_kondor[0] / p["hp"])
    print(f"fila auxiliar KONDOR: panel {H:.2f}, railes a {S:.2f} entre centros "
          f"(referencia minima externa: {S_1U_INTELLIJEL:.2f})")
    print(f"  {hp_kondor} HP a paso {p['hp']:.2f}, ventana de {x1 - x0:.2f} para "
          f"{pide:.2f} de fila (sobran {sobra:.2f}); el riel baja hasta "
          f"y = {y_riel:.1f} y debajo hay {y_riel:.0f} mm hasta la tabla")


def canario_fila_kondor(p: dict[str, float]) -> None:
    """Mutaciones dirigidas de cada regla propia de la fila KONDOR."""
    sordo = io.StringIO()
    casos = (
        ({"alto_panel_1u": ALTO_FILA_AUX_ANTERIOR}, "alto de la fila auxiliar KONDOR",
         "volver al alto anterior"),
        ({"inset_er": 11.0}, "referencia minima externa",
         "bajar la separacion por debajo de la referencia externa"),
        ({"inset_er": 2.5}, "separacion KONDOR",
         "separar los rieles 50 mm en vez de 49"),
        ({"paso_horizontal": PASO_HORIZONTAL_ANTERIOR}, "ventana del valle",
         "dejar la ventana anterior para la fila nueva"),
        ({"paso_horizontal": p["paso_horizontal"] + 1.0}, "margen anterior",
         "agrandar la ventana sin conservar su margen"),
    )
    for cambios, clave, que in casos:
        roto = dict(p)
        roto.update(cambios)
        try:
            with contextlib.redirect_stdout(sordo):
                guarda_fila_1u(roto)
        except AssertionError as e:
            assert clave in str(e), (
                f"canario KONDOR: con {cambios} la puerta salto por otra razon "
                f"('{str(e)[:80]}...') y no por '{clave}'")
            continue
        raise AssertionError(
            f"canario KONDOR NO disparo: {que} y guarda_fila_1u() lo deja "
            f"pasar -- no confiar en su VERDE")

    P = _vertices(p)
    cr = _centros_rail(p, P)
    anterior = dict(p)
    anterior["alto_panel_1u"] = ALTO_FILA_AUX_ANTERIOR
    c_ant = _centros_rail_1u(anterior, _vertices(anterior),
                             _centros_rail(anterior, _vertices(anterior)))
    c_ok = _centros_rail_1u(p, P, cr)
    transiciones_rotas = (
        ([(c_ant[0][0] + 0.1, c_ant[0][1]), c_ok[1]], "primer riel KONDOR"),
        ([c_ok[0], (c_ant[1][0] + 15.34, c_ant[1][1])], "segundo riel KONDOR"),
    )
    for centros_rotos, clave in transiciones_rotas:
        try:
            _guarda_transicion_fila_kondor(c_ant, centros_rotos)
        except AssertionError as e:
            assert clave in str(e), (
                f"canario KONDOR de movimiento salto por '{str(e)}' y no por "
                f"'{clave}'")
            continue
        raise AssertionError(
            f"canario KONDOR NO disparo al mutar {clave.lower()}")

    historica = dict(p)
    historica["alto_panel_1u"] = ALTO_FILA_AUX_ANTERIOR
    historica["paso_horizontal"] = PASO_HORIZONTAL_ANTERIOR
    historica["rehundido_panel"] = 0.0
    P_hist = _vertices(historica)
    c_hist = _centros_rail_1u(
        historica, P_hist, _centros_rail(historica, P_hist))
    c_tanda_b = [
        (c_hist[0][0], c_hist[0][1] - REHUNDIDO_PANEL_OBJETIVO),
        (c_hist[1][0] + DESPLAZAMIENTO_SEGUNDO_RIEL_KONDOR,
         c_hist[1][1] - REHUNDIDO_PANEL_OBJETIVO),
    ]
    _guarda_transicion_tanda_b(c_hist, c_tanda_b)
    transiciones_tanda_b_rotas = (
        ([(c_tanda_b[0][0] + 0.1, c_tanda_b[0][1]), c_tanda_b[1]],
         "primer riel KONDOR"),
        ([c_tanda_b[0], (c_tanda_b[1][0] - 0.1, c_tanda_b[1][1])],
         "segundo riel KONDOR"),
    )
    for centros_rotos, clave in transiciones_tanda_b_rotas:
        try:
            _guarda_transicion_tanda_b(c_hist, centros_rotos)
        except AssertionError as e:
            assert clave in str(e), (
                f"canario KONDOR Tanda B salto por '{str(e)}' y no por "
                f"'{clave}'")
            continue
        raise AssertionError(
            f"canario KONDOR Tanda B NO disparo al mutar {clave.lower()}")

    railes, _, _ = _cajas_solidas(p)
    anchos_3u = [c[6] - c[5] for c in railes if c[0] in NOMBRES_CR]
    ancho = next(c[6] - c[5] for c in railes
                 if c[0].startswith("fila KONDOR"))
    for ancho_roto, clave in ((ancho + p["hp"], "HP"),
                              (ancho + 0.1, "mide")):
        try:
            _guarda_ancho_hp_fila_kondor(ancho_roto, anchos_3u, p["hp"])
        except AssertionError as e:
            assert clave in str(e), (
                f"canario KONDOR de ancho salto por '{str(e)}' y no por "
                f"'{clave}'")
            continue
        raise AssertionError(
            f"canario KONDOR NO disparo con ancho {ancho_roto:.2f}")

    with contextlib.redirect_stdout(sordo):
        guarda_fila_1u(dict(p))




def guarda_meseta_es_chapa(p: dict[str, float]) -> None:
    """La meseta del remate tiene el espesor de la chapa, porque ES la chapa.

    marco_sup dejo de ser una plancha de acrilico el 2026-08-27 y paso a ser la
    cara horizontal del miembro trasero alto -- un ALA doblada del mismo blank.
    Un ala no puede tener otro espesor que su chapa, pero marco_sup se quedo en
    el 3 que valia cuando t_costilla valia 3, y al bajar la chapa a 1.5 el
    modelo dibujaba una meseta de 3 pegada a un alma de 1.5.

    params.scad no admite expresiones, asi que el valor va a mano y esta puerta
    es lo que impide que se separen otra vez. Es el patron del repo: un literal
    con la formula solo en el comentario ya costo una tanda con ancho_total; un
    literal con PUERTA no se desincroniza en silencio."""
    assert abs(p["marco_sup"] - p["t_costilla"]) < 1e-9, (
        f"marco_sup vale {p['marco_sup']:g} y t_costilla {p['t_costilla']:g}. La "
        f"meseta es un ALA del miembro trasero alto, doblada de su mismo blank: "
        f"no puede tener otro espesor que la chapa de la que sale")


def guarda_rebaje(p: dict[str, float]) -> None:
    """La franja interior del anillo, entre su rebaje y la silueta, admite una
    rosca ciega M4 con 1.5 D a cada lado: 3 x d_M4_paso = 13.5. Es lo que puso
    la cara vista en 20, y ahi asientan las placas de anclaje.

    MEDIA CUATRO COSAS Y SE QUEDA CON UNA (2026-10-11). Las otras tres median
    la mejilla de acrilico en su rebaje, y se fueron con ella cuando la
    sustituyo la persiana: (1) que el rebaje fuera mas hondo que el PMMA mas
    grueso del lote mas su junta -- es la que puso el anillo en 14 --; (3) que
    el acrilico solapara el labio al menos 5 para que lo retuviera; y (4) que
    el labio tuviera cuerpo sobre el acrilico, 3 y el doble del chaflan. El
    rebaje se queda vacio y tapado por la persiana (spec, §7.2): sus cotas
    siguen dibujando el bolsillo de la trasera, y ese lo mide
    guarda_tramo_trasero().

    El rebaje ES UN HUECO DEL ANILLO, no una cota de la pieza que asentaba en
    el, y esta condicion lo mide asi: lo que queda de franja para los
    tornillos."""
    franja = p["cara_anillo"] - p["rebaje_anillo"]
    assert franja >= 3 * p["d_M4_paso"], (
        f"la franja interior del anillo mide {franja:.2f} (cara {p['cara_anillo']:g} "
        f"- rebaje {p['rebaje_anillo']:g}) y una rosca ciega M4 con 1.5 D a cada "
        f"lado pide {3 * p['d_M4_paso']:.2f}. Ahi asientan las placas de anclaje")
    print(f"rebaje: anillo de {p['t_anillo']:g}, rebaje vacio de "
          f"{p['rebaje_anillo']:g} x {p['t_anillo'] - p['rehundido_acrilico']:g} "
          f"tras un labio de {p['rehundido_acrilico']:g}; franja de {franja:.0f} "
          f"para las roscas ciegas; cara vista {p['cara_anillo']:g}")


def _seccion_anillo(p: dict[str, float], tramo: int | None = None
                    ) -> tuple[float, float, float]:
    """Inercia, area y fibra mas alejada del anillo, flexion FUERA del plano.
    Con tramo = 5, la seccion del TRAMO TRASERO con sus dos bolsillos.

    La seccion de un tramo es un rectangulo macizo de (cara - rebaje) x t_anillo
    -- la franja donde asientan las placas -- mas el LABIO de rebaje x rehundido
    que queda delante del acrilico. Eje neutro por el teorema de los ejes
    paralelos, como _seccion_canal(). NO vale para flexion en el plano: ahi el
    anillo es un marco y trabaja a traccion y compresion."""
    W, T = p["cara_anillo"], p["t_anillo"]
    B, R = p["rebaje_anillo"], p["rehundido_acrilico"]
    if tramo == 5:
        # EL TRAMO TRASERO desde la trasera capturada (2026-08-29, noche, 2):
        # el rebaje del costado retrocede a t_anillo + pared (3 de ancho) y
        # ademas lleva el bolsillo de la trasera, u = rehundido..t_anillo por
        # z = t_anillo - rebaje..t_anillo. Rectangulos con signo y ejes
        # paralelos, como abajo; -15 % de area y -36 % de inercia.
        bo = _bolsillo_trasero(p)
        B = W - bo["rebaje_costado"]
        rects = [(W, T, T / 2.0, +1),
                 (B, T - R, R + (T - R) / 2.0, -1),
                 (bo["ancho"], bo["hondo"], bo["z0"] + bo["hondo"] / 2.0, -1)]
        A = sum(s * w * h for w, h, _, s in rects)
        yb = sum(s * w * h * y for w, h, y, s in rects) / A
        inercia = sum(s * (w * h ** 3 / 12 + w * h * (y - yb) ** 2) for w, h, y, s in rects)
        return inercia, A, max(yb, T - yb)
    a1, y1 = (W - B) * T, T / 2.0
    a2, y2 = B * R, R / 2.0
    A = a1 + a2
    yb = (a1 * y1 + a2 * y2) / A
    inercia = ((W - B) * T ** 3 / 12 + a1 * (y1 - yb) ** 2
               + B * R ** 3 / 12 + a2 * (y2 - yb) ** 2)
    return inercia, A, max(yb, T - yb)


def autocomprobacion_anillo() -> None:
    """La seccion del anillo, a mano, con fracciones exactas.

    Es el patron que salvo la costilla el 2026-08-26 y el canal el 27: la
    cuenta primero, la funcion despues. Con cara 20, t 14, rebaje 6, rehundido 3:
      franja: A1 = 14*14 = 196, y1 = 7      labio: A2 = 6*3 = 18, y2 = 1.5
      A = 214;  yb = (196*7 + 18*1.5)/214 = 1399/214 = 6.537383
      I = 14*14^3/12 + 196*(7 - yb)^2 + 6*3^3/12 + 18*(1.5 - yb)^2
        = 2384089/642 = 3713.534268
      ymax = 14 - yb = 7.462617"""
    p = {"cara_anillo": 20.0, "t_anillo": 14.0, "rebaje_anillo": 6.0,
         "rehundido_acrilico": 3.0}
    inercia, A, ymax = _seccion_anillo(p)
    assert abs(A - 214.0) < 1e-9, f"area {A}, a mano 214"
    assert abs(inercia - 2384089 / 642) < 1e-6, f"I = {inercia:.6f}, a mano {2384089/642:.6f}"
    assert abs(ymax - (14 - 1399 / 214)) < 1e-9, f"ymax {ymax:.6f}"


def autocomprobacion_plano_neutro() -> None:
    """El plano neutro, a mano. Mismo patron que autocomprobacion_anillo(): la
    cuenta primero, la funcion despues.

    Una entrada de 3 a y = 0 y una salida de 4 a y = 25: el plano iguala
    3 sqrt(yn) = 4 sqrt(25 - yn), o sea 9 yn = 16 (25 - yn), yn = 16, y
    S = 4 sqrt(9) = 12. Es la cuenta en serie con la que el case conto su aire
    hasta el 2026-10-12: a_ef = 3 x 4 / sqrt(3^2 + 4^2) = 2.4, y
    a_ef sqrt(h) = 2.4 x 5 = 12. Con otra salida de 1 a y = 20, por encima
    del plano, sale mas aire: el plano sube y S crece."""
    yn, s = _plano_neutro([(0.0, 3.0), (25.0, 4.0)])
    assert abs(yn - 16.0) < 1e-9, f"plano neutro a {yn}, a mano 16"
    assert abs(s - 12.0) < 1e-9, f"S = {s}, a mano 12"
    yn3, s3 = _plano_neutro([(0.0, 3.0), (25.0, 4.0), (20.0, 1.0)])
    assert 16.0 < yn3 < 20.0 and s3 > 12.0, (
        f"con una salida mas el plano queda en {yn3:.3f} y S en {s3:.3f}: tenia "
        f"que subir de 16 sin pasar la salida nueva, y S que crecer de 12")


def autocomprobacion_base() -> None:
    """La chimenea con el camino de la base tiene que caer en las dos cuentas
    que ya se conocen. Sin base, la forma cerrada de toda la vida: P = k dT^1.5,
    con S de _plano_neutro(). Y con el canal sin roce, la rendija y los
    agujeros en serie, que son un orificio equivalente a_ef = (a1^-2 +
    a2^-2)^-1/2 metido como un hueco mas a y = 0 (papel del suelo, sec.5)."""
    p = leer_params()

    def cerrada(hs, cd):
        _yn, s = _plano_neutro(hs)
        k = (RHO_AIRE * CP_AIRE * cd * math.sqrt(2 * G / T_AMB)
             * s * 1e-6 * math.sqrt(1e-3))
        return (p["potencia_disipada"] / k) ** (2 / 3)

    for cd in (CD_TIRO, CD_TIRO_PESIMISTA):
        for costados in (2, 1):
            a = _tiro(p, cd, costados, base=False)["dt"]
            b = cerrada(_huecos(p, costados), cd)
            assert abs(a - b) < 1e-6 * b, (
                f"autocomprobacion de la base: sin base el solver da {a:.6f} K "
                f"y la forma cerrada {b:.6f} (C_D {cd}, {costados} costados)")
    cam = _camino_base(p, canal=0.0)
    a_ef = 1 / math.sqrt(1 / (cam["w"] * cam["h"]) ** 2 + 1 / cam["a_base"] ** 2)
    a = _tiro(p, canal=0.0)["dt"]
    b = cerrada(_huecos(p) + [(0.0, a_ef)], CD_TIRO)
    assert abs(a - b) < 1e-6 * b, (
        f"autocomprobacion de la base: con el canal sin roce el solver da "
        f"{a:.6f} K y el orificio equivalente {b:.6f}")


def _tacos_persiana_cotas(p: dict[str, float]) -> list[tuple[str, float, float]]:
    """(que, tiene, pide) de cada relacion de cotas entre tacos y bolsillos."""
    fondo_trasera = _bolsillo_trasero(p)["z0"]                   # el bolsillo de la trasera empieza ahi
    # BAJO LAS CHAPAS EMPOTRADAS el anillo no llega a t_anillo: el rebaje de la
    # chapa se come rebaje_chapa por la cara interior (guarda_rebaje_chapa()),
    # hoy de 1 a 5.5 de la silueta, y el asiento del iman arranca en 3.45: hay
    # asiento debajo del rebaje, y su pared es la de z. Hasta el 2026-10-12 se
    # medía contra t_anillo, 3 mm de mas bajo la nariz, la meseta y el retorno.
    fondo_chapa = p["t_anillo"] - p["rebaje_chapa"]
    return [
        ("aire bajo el taco", p["hondo_bolsillo_taco"] - p["alto_taco"], 0.3),
        ("holgura del taco en su bolsillo", p["d_bolsillo_taco"] - p["d_taco"], 0.5),
        ("pared hasta el rebaje del acrilico", (p["cara_anillo"] - p["rebaje_anillo"])
         - (p["u_taco"] + p["d_bolsillo_taco"] / 2), PARED_MIN_ANILLO),
        ("canto hasta el chaflan de la silueta", p["u_taco"] - p["d_bolsillo_taco"] / 2,
         p["chaflan_anillo"] + 0.5),
        ("pared hasta el bolsillo de la trasera (iman fino)", fondo_trasera
         - (p["hondo_bolsillo_taco"] + p["alto_iman_fino"] + 0.1), PARED_MIN_ANILLO),
        ("pared hasta el rebaje de la chapa (iman del anillo)", fondo_chapa
         - (p["hondo_bolsillo_taco"] + p["alto_iman_anillo"] + 0.1), PARED_MIN_ANILLO),
        ("el iman del taco cabe en el taco", p["alto_taco"] - (p["alto_iman_taco"] + 0.1), 1.0),
    ]


def guarda_tacos_persiana(p: dict[str, float]) -> None:
    """La persiana apoya en el anillo y no en sus tacos, y los bolsillos no
    rompen hacia el rebaje, el chaflan ni el bolsillo de la trasera (persiana
    §4). Lo que el DXF no puede decir: profundidades y holguras."""
    for que, tiene, pide in _tacos_persiana_cotas(p):
        assert tiene >= pide - 1e-9, f"{que}: {tiene:.2f} mm y se piden {pide:.2f}"
    print("tacos de la persiana: " + ", ".join(
        f"{que} {tiene:.2f}" for que, tiene, _ in _tacos_persiana_cotas(p)))
    # LO QUE ESTE FICHERO NO PUEDE COMPROBAR de la sujecion, y el papel pide
    # (persiana §3.3, §4 y §7.2). Sale como HUECO hasta que se mida o se decida.
    _HUECOS.append(
        "el tiron de los imanes de la persiana sin medir: el papel lo estima en "
        "50-70 N por persiana entera (ESTIMADO) contra los 3.6 N de su peso; se "
        "mide con dinamometro en la tira de muestra (#393, #398)")
    _HUECOS.append(
        "el reparto de los tacos de la persiana deja tramos de mas de 100 mm sin "
        "taco, y el papel pide 100 o menos para apretar la banda (3.3 y 4): con "
        "diez tacos y 10 mm a las roscas no se llega, y el tramo mas largo lo "
        "imprime check_dxf.py en cada corrida. Pasar a once tacos lo decide Samuel")


def canario_tacos_persiana(p: dict[str, float]) -> None:
    for cambio, aviso in (({"alto_taco": p["hondo_bolsillo_taco"]}, "aire bajo el taco"),
                          ({"u_taco": p["u_taco"] + 1.0}, "rebaje del acrilico"),
                          ({"alto_iman_fino": 3.0}, "bolsillo de la trasera"),
                          # el rebaje de la chapa llega al fondo del asiento
                          ({"rebaje_chapa": p["t_anillo"] - p["hondo_bolsillo_taco"]
                            - p["alto_iman_anillo"]}, "rebaje de la chapa")):
        try:
            guarda_tacos_persiana({**p, **cambio})
        except AssertionError as e:
            assert aviso in str(e), f"canario de los tacos salto por '{e}'"
            continue
        raise AssertionError(f"canario de los tacos NO salto ({aviso})")


def guarda_anillo(p: dict[str, float]) -> None:
    """El anillo aguanta que empujen el case de lado, tramo por tramo.

    SUSTITUYE A guarda_costilla() desde el 2026-08-28. Aquella media una L de
    chapa plegada tramo a tramo y decidia que tramos llevaban ala; este anillo
    es UNA pletina fresada y todos sus tramos tienen la misma seccion. Se queda
    la hipotesis: viga biempotrada -- las esquinas de un marco continuo lo son,
    y aqui ademas son de una pieza -- con carga_mano al centro del tramo, flecha
    contra flecha_costado_max y tension contra RP02_ALUMINIO.

    Lo que ya no hay que impedir: quitar el ala, dejar un tramo sin ella, mandar
    P3 como alivio en V. No hay ala, no hay pliegue, no hay P3 que soldar. Lo
    que SI impide: que alguien adelgace el anillo o le coma la franja por
    estetica y lo deje por debajo de lo que la chapa plegada ya pasaba."""
    inercia, A, ymax = _seccion_anillo(p)
    inercia5, A5, _ = _seccion_anillo(p, tramo=5)
    P = _vertices(p)
    n = len(P)
    nombres = ["frente bajo", "cara inferior", "el valle", "cara superior",
               "meseta de remate", "la trasera", "el suelo"]
    largo5 = math.hypot(P[6][0] - P[5][0], P[6][1] - P[5][1])
    masa = (A * (_perimetro(P) - largo5) + A5 * largo5) * 2.70e-6
    print(f"anillo: pletina de {p['t_anillo']:g}, cara vista {p['cara_anillo']:g}, "
          f"rebaje {p['rebaje_anillo']:g} x {p['t_anillo'] - p['rehundido_acrilico']:g}, "
          f"chaflan {p['chaflan_anillo']:g} -> I={inercia:.0f} mm4, {A:.0f} mm2 (el tramo "
          f"trasero, con sus dos bolsillos: I={inercia5:.0f}, {A5:.0f} mm2), "
          f"{masa:.2f} kg por costilla")
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        largo = math.hypot(b[0] - a[0], b[1] - a[1])
        # el tramo trasero lleva su propia seccion, con los dos bolsillos
        inercia, A, ymax = _seccion_anillo(p, tramo=5 if i == 5 else None)
        flecha = p["carga_mano"] * largo ** 3 / (192 * E_ALUMINIO * inercia)
        sigma = (p["carga_mano"] * largo / 8) * ymax / inercia
        assert flecha <= p["flecha_costado_max"], (
            f"el anillo cede {flecha:.3f} mm en el tramo '{nombres[i]}' de "
            f"{largo:.2f} mm y el techo son {p['flecha_costado_max']:.2f}. La "
            f"chapa plegada de 27 x 16 x 1.5 daba I=1673 y pasaba: si esto no "
            f"pasa, alguien adelgazo el anillo o le comio la franja")
        assert sigma <= RP02_ALUMINIO, (
            f"el anillo trabaja a {sigma:.1f} MPa en '{nombres[i]}' contra "
            f"{RP02_ALUMINIO:.0f}")
        print(f"  {nombres[i]:<18} {largo:7.2f} mm  cede {flecha:.3f}")


def _seccion_chapa(poly: list[tuple[float, float]], t: float) -> float:
    """Inercia (mm4) de una chapa de espesor t por su linea media, para flexion
    vertical: la seccion de la nariz o del talon tumbada (secciones.py de Elke,
    papel del suelo sec.3.2)."""
    segs = list(zip(poly[:-1], poly[1:]))
    area = sum(t * math.dist(a, b) for a, b in segs)
    yc = sum(t * math.dist(a, b) * (a[1] + b[1]) / 2 for a, b in segs) / area
    inercia = 0.0
    for a, b in segs:
        largo = math.dist(a, b)
        s = abs(b[1] - a[1]) / largo if largo else 0.0
        ym = (a[1] + b[1]) / 2
        inercia += (t * largo * (ym - yc) ** 2 + t * largo ** 3 * s ** 2 / 12
                    + largo * t ** 3 * (1 - s ** 2) / 12)
    return inercia


def _emparrillado(lx: float, lz: float, t: float, nx: int, nz: int, apoyos: str,
                  casos: list[list[tuple[float, float, float]]],
                  blando: list[tuple[float, float, float, float]] = (),
                  f_blando: float = 1.0, bordes: list[dict] | None = None,
                  lineas_z: tuple[float, ...] = ()) -> list[dict]:
    """Emparrillado de una placa de lx por lz y espesor t (analogia de Hambly,
    el modelo de Elke del papel del suelo): vigas en x y en z con la rigidez D
    de su franja y torsion, tres grados por nudo (w, giro en x, giro en z).
    Una sola matriz para todos los casos de carga. Devuelve, por caso,
    {"flecha": mm maximos, "m_campo": N mm/mm de la barra mas cargada dentro de
    los rectangulos blandos, "m_llena": lo mismo en la chapa llena}.

    El momento es el de los EXTREMOS DE CADA BARRA (k*u del elemento) entre su
    ancho tributario, no D*curvatura en el nudo. En la costura entre el campo y
    la chapa llena la curvatura por diferencias centrales mezcla las dos
    rigideces y se multiplica por una sola: el nudo de la esquina de la L daba
    el triple del momento de la barra de al lado (revision final del suelo).

    apoyos: "cuatro bordes" (la validacion) o "lineas" (w = 0 a lo largo de las
    z de lineas_z: el canto de los anillos). blando: rectangulos (x0, x1, z0,
    z1) con la rigidez por f_blando (el campo perforado). bordes: vigas de
    borde atadas en puntos, [{"x", "EI", "z_atados", "z_apoyos"}]. casos: listas
    de cargas (x, z, N), cada una en el nudo mas cercano. numpy denso: la malla
    de la puerta tiene unos 1 600 grados y se resuelve en menos de un segundo."""
    import numpy as np

    nu = 0.33
    xs, zs = np.linspace(0.0, lx, nx + 1), np.linspace(0.0, lz, nz + 1)
    d0 = E_ALUMINIO * t ** 3 / (12 * (1 - nu ** 2))
    nn = (nx + 1) * (nz + 1)
    bordes = bordes or []
    nb = nz + 1
    ndof = 3 * nn + 2 * nb * len(bordes)
    K = np.zeros((ndof, ndof))

    def idx(i, j):
        return i * (nz + 1) + j

    def kb(ei, L):
        c = ei / L ** 3
        return np.array([[12 * c, 6 * L * c, -12 * c, 6 * L * c],
                         [6 * L * c, 4 * L * L * c, -6 * L * c, 2 * L * L * c],
                         [-12 * c, -6 * L * c, 12 * c, -6 * L * c],
                         [6 * L * c, 2 * L * L * c, -6 * L * c, 4 * L * L * c]])

    def add(dofs, k):
        K[np.ix_(dofs, dofs)] += k

    def en_campo(x, z):
        return any(a <= x <= b and c <= z <= e for a, b, c, e in blando)

    barras = []                         # (grados, matriz, ancho tributario, en el campo)

    def barra(dofs, ei, largo, ancho, campo):
        ke = kb(ei, largo)
        add(dofs, ke)
        barras.append((dofs, ke, ancho, campo))

    dx, dz = np.diff(xs), np.diff(zs)
    torsion = np.array([[1.0, -1.0], [-1.0, 1.0]])
    for i in range(nx + 1):
        for j in range(nz + 1):
            if i < nx:
                s = (dz[j - 1] / 2 if j > 0 else 0) + (dz[j] / 2 if j < nz else 0)
                campo = en_campo((xs[i] + xs[i + 1]) / 2, zs[j])
                dl = d0 * (f_blando if campo else 1.0) * s
                n1, n2 = idx(i, j), idx(i + 1, j)
                barra([3 * n1, 3 * n1 + 1, 3 * n2, 3 * n2 + 1], dl, dx[i], s, campo)
                add([3 * n1 + 2, 3 * n2 + 2], torsion * dl / dx[i])
            if j < nz:
                s = (dx[i - 1] / 2 if i > 0 else 0) + (dx[i] / 2 if i < nx else 0)
                campo = en_campo(xs[i], (zs[j] + zs[j + 1]) / 2)
                dl = d0 * (f_blando if campo else 1.0) * s
                n1, n2 = idx(i, j), idx(i, j + 1)
                barra([3 * n1, 3 * n1 + 2, 3 * n2, 3 * n2 + 2], dl, dz[j], s, campo)
                add([3 * n1 + 1, 3 * n2 + 1], torsion * dl / dz[j])

    def ni(x):
        return int(np.argmin(abs(xs - x)))

    def nj(z):
        return int(np.argmin(abs(zs - z)))

    fijos = set()
    kpen = 1e7                         # N/mm, como Elke: tres ordenes sobre la malla
    for bi, bd in enumerate(bordes):
        b0 = 3 * nn + 2 * nb * bi
        for j in range(nz):
            add([b0 + 2 * j, b0 + 2 * j + 1, b0 + 2 * (j + 1), b0 + 2 * (j + 1) + 1],
                kb(bd["EI"], dz[j]))
        for z in bd["z_atados"]:
            a, b = 3 * idx(ni(bd["x"]), nj(z)), b0 + 2 * nj(z)
            add([a, b], kpen * torsion)
        for z in bd["z_apoyos"]:
            fijos.add(b0 + 2 * nj(z))
    if apoyos == "cuatro bordes":
        fijos |= {3 * idx(i, j) for i in range(nx + 1) for j in range(nz + 1)
                  if i in (0, nx) or j in (0, nz)}
    else:
        fijos |= {3 * idx(i, nj(z)) for z in lineas_z for i in range(nx + 1)}
    F = np.zeros((ndof, len(casos)))
    for k, cargas in enumerate(casos):
        for x, z, n in cargas:
            F[3 * idx(ni(x), nj(z)), k] -= n
    lib = np.array(sorted(set(range(ndof)) - fijos))
    U = np.zeros((ndof, len(casos)))
    U[lib] = np.linalg.solve(K[np.ix_(lib, lib)], F[lib])
    gl = np.array([b[0] for b in barras])
    ke = np.array([b[1] for b in barras])
    ancho = np.array([b[2] for b in barras])
    es_campo = np.array([b[3] for b in barras])
    assert not blando or es_campo.any(), (
        f"ninguna barra de la malla de {nx} x {nz} cae dentro de los "
        f"rectangulos blandos: el momento del campo saldria 0 y la puerta "
        f"pasaria sin medir nada")
    resultado = []
    for k in range(len(casos)):
        u = U[:, k]
        f = np.einsum("bij,bj->bi", ke, u[gl])
        m = np.maximum(abs(f[:, 1]), abs(f[:, 3])) / ancho
        resultado.append({
            "flecha": float(-u[0:3 * nn:3].min()),
            "m_campo": float(m[es_campo].max()) if es_campo.any() else 0.0,
            "m_llena": float(m[~es_campo].max()) if (~es_campo).any() else 0.0})
    return resultado


# La mano sobre el campo: huella de 40 x 60 mm, una posicion cada 60 mm.
HUELLA_MANO = (40.0, 60.0)
PASO_MANO = 60.0


def _manos_en_el_campo(p: dict[str, float]) -> list[tuple[str, float, float, list]]:
    """La mano de carga_mano --9 cargas puntuales en su huella de 40 x 60--
    barrida por los dos brazos de la L del campo, con la huella entera dentro:
    (brazo, x, z, cargas). No va solo en el centro de cada brazo: el peor sitio
    de la flecha (la fila de arriba del brazo A) y el del puente (junto a la
    esquina de la L) son distintos y ninguno es ese (revision final del suelo).
    Sale de _zonas_campo_base(): si la L cambia, la barrida la sigue."""
    hx, hz = HUELLA_MANO

    def barrido(lo: float, hi: float) -> list[float]:
        if hi <= lo:                    # el brazo es mas estrecho que la mano
            return [(lo + hi) / 2]
        n = math.ceil((hi - lo) / PASO_MANO) + 1
        return [lo + (hi - lo) * i / (n - 1) for i in range(n)]

    manos = []
    for brazo, (a, b, c, e) in zip("AB", _zonas_campo_base(p)):
        for x in barrido(a + hx / 2, b - hx / 2):
            for z in barrido(c + hz / 2, e - hz / 2):
                cargas = [(x + dx, z + dz, p["carga_mano"] / 9)
                          for dx in (-hx / 2, 0.0, hx / 2)
                          for dz in (-hz / 2, 0.0, hz / 2)]
                manos.append((brazo, x, z, cargas))
    return manos


def _flecha_base(p: dict[str, float], casos: list[list[tuple[float, float, float]]]
                 ) -> list[dict]:
    """La base con sus apoyos de verdad: el canto de los dos anillos (lineas en
    z = t_anillo/2 y ancho - t_anillo/2), y la nariz y el talon como vigas de
    borde atadas en sus tres M4 y apoyadas en el rebaje del anillo. El campo
    perforado, con el 30 % de la rigidez (Elke, O'Donnell-Langer, ligamento
    0.375; ESTIMADO). Coordenadas de la placa: x desde el chaflan delantero.
    Devuelve, por caso de carga, el dict de _emparrillado()."""
    x0 = p["chaflan_nariz"]
    lx = fondo(p) - 2 * x0
    nz_, tl = _nariz(p), _talon(p)
    t = p["t_costilla"]
    apoyos = (p["t_anillo"], p["ancho_total"] - p["t_anillo"])
    bordes = [{"x": nz_["m4_x"] - x0, "EI": E_ALUMINIO * _seccion_chapa(nz_["contorno"], t),
               "z_atados": nz_["m4_z"], "z_apoyos": apoyos},
              {"x": tl["m4_x"] - x0, "EI": E_ALUMINIO * _seccion_chapa(tl["contorno"], t),
               "z_atados": tl["m4_z"], "z_apoyos": apoyos}]
    blando = [(a - x0, b - x0, c, e) for a, b, c, e in _zonas_campo_base(p)]
    return _emparrillado(lx, p["ancho_total"], p["t_base"], 16, 28, "lineas",
                         [[(x - x0, z, n) for x, z, n in cargas] for cargas in casos],
                         blando, 0.30, bordes,
                         (p["t_anillo"] / 2, p["ancho_total"] - p["t_anillo"] / 2))


def canario_base_fina(p: dict[str, float]) -> None:
    """Una base mas fina tiene que saltar en guarda_piso(), y cada rama por SU
    razon. Con 2 mm, la que el papel descarto, la flecha todavia cabe en la
    rendija y lo que salta es el borde de los agujeros; con las patas a 3 mm el
    techo de la flecha baja a 2 y salta la mesa aunque la chapa sea la buena.
    Las dos ramas tienen que tener su prueba roja: una puerta cuyo aserto de
    tension nunca ha mordido no vale por su VERDE."""
    casos = (
        ({"t_base": 2.0}, "puente",
         "con 2 mm el borde del agujero llega al limite elastico"),
        ({"alto_pie": 3.0}, "toca la mesa",
         "con la rendija a 3 mm la flecha de la mano no cabe debajo"),
    )
    for cambios, clave, que in casos:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                guarda_piso({**p, **cambios})
        except AssertionError as e:
            assert clave in str(e), (
                f"canario de la base: con {cambios} guarda_piso() salto, pero "
                f"por otra razon ('{str(e)[:80]}...') y no por '{clave}'")
            continue
        raise AssertionError(f"canario de la base NO disparo: con {cambios} "
                             f"hay {que} y guarda_piso() lo deja pasar -- no "
                             f"confiar en su VERDE")


def autocomprobacion_emparrillado() -> None:
    """El emparrillado contra Timoshenko, en la flecha Y EN EL MOMENTO, sobre la
    placa cuadrada de 300 apoyada en los cuatro bordes.

    Flecha: 100 N al centro, w = 0.01160 P a^2 / D. Elke lo valido a n = 20
    dentro del 1.3 %; aqui se exige el 3 % con la malla de la puerta.

    Momento: carga uniforme q, M = 0.0479 q a^2 en el centro (nu = 0.3). La
    parrilla no acopla Poisson --cada barra solo siente su curvatura--, asi que
    lo que ha de dar es D*kappa = M / (1 + nu), y se exige el 5 % (la malla de
    la puerta da +3 %, y converge a +1 % con el doble de fina). Se mide en una
    ventana central de rigidez plena: el maximo global de la placa cae junto a
    la esquina apoyada, donde el momento de barra equilibra la torsion y no es
    flexion. Sin esta prueba nadie vigilaba la escala de los momentos de barra
    (su ancho tributario), de donde la puerta del suelo saca la tension del
    puente."""
    t, a, n = 3.0, 300.0, 16
    nu = 0.33
    d = E_ALUMINIO * t ** 3 / (12 * (1 - nu ** 2))
    w = _emparrillado(a, a, t, n, n, apoyos="cuatro bordes",
                      casos=[[(a / 2, a / 2, 100.0)]])[0]["flecha"]
    w_t = 0.01160 * 100.0 * a * a / d
    assert abs(w - w_t) < 0.03 * w_t, (
        f"el emparrillado da {w:.3f} mm y Timoshenko {w_t:.3f} en la placa "
        f"cuadrada: la malla o el ensamblado estan mal")
    q, h = 0.001, a / n
    uniforme = [(i * h, j * h, q * h * h * (0.5 if i in (0, n) else 1.0)
                 * (0.5 if j in (0, n) else 1.0))
                for i in range(n + 1) for j in range(n + 1)]
    m = _emparrillado(a, a, t, n, n, apoyos="cuatro bordes", casos=[uniforme],
                      blando=[(a / 4, 3 * a / 4, a / 4, 3 * a / 4)],
                      f_blando=1.0)[0]["m_campo"]
    m_t = 0.0479 * q * a * a / (1 + 0.3)
    assert abs(m - m_t) < 0.05 * m_t, (
        f"el emparrillado da {m:.3f} N mm/mm de momento de barra y Timoshenko "
        f"{m_t:.3f} (D*kappa = M / (1 + nu)) con carga uniforme: la escala de "
        f"los momentos de barra esta mal")


def guarda_piso(p: dict[str, float]) -> None:
    """El riel de panel del frente tiene que librar el SUELO del case.

    Es la condicion que fija alto_frontal y con el la altura entera del aparato,
    y hasta hoy vivia solo en un comentario de params.scad. Nadie la vigilaba:
    solapes() trabaja con cajas y solo canta cuando los cuerpos YA se tocan, o
    sea que se come los 4 mm de holgura sin protestar.

    Y lo que hay debajo cambio CUATRO veces. Primero era el lomo de un larguero
    (mal: la bandeja iba encima, 5 mm de barato y 0.51 de solape real). Luego el
    tope de la bandeja. Luego nada, cuando Samuel retiro la bandeja por detras
    del riel -- solo el canto de abajo del case. Y desde el 2026-08-21 vuelve a
    ser el tope de la bandeja, porque el suelo cierra: la plancha llega hasta
    donde muere la curva del costado y le pasa POR DEBAJO al riel.

    Cada version de esta cota valio milimetros de aparato, y la ultima vuelta
    costo 8.46. La segunda cambio de signo por el camino: ya no se exige que la
    bandeja se aparte del riel sino que LLEGUE al frente.

    SON TRES ASSERTS, no dos. El tercero -- que la trasera baje hasta el mismo
    plano del suelo -- entro el 2026-08-27 y nadie actualizo ni esta linea ni su
    numero, que se quedo en '4' porque venia de una version con cuatro. Aqui van
    numerados 1, 2 y 3, que es lo que hay.

    Se mide sobre el centro REAL del riel (el que sale de _centros_rail), no
    rehaciendo la formula: si el .scad y el budget se separan, esto lo nota."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    _, hy = _he_er(p, p["angulo_inferior"])
    # 1. el riel PASA POR ENCIMA DEL SUELO, con aire.
    #
    #    EL SUELO ES y=0 DESDE EL 2026-08-27. Antes esta cota se media contra
    #    el techo de la bandeja (t_base) y por eso mandaba sobre alto_frontal:
    #    cada milimetro de plancha eran uno de aparato, y la ultima vuelta costo
    #    8.46. Con la tabla DEBAJO del marco el suelo interior es el plano cero
    #    y la cota se suelta del espesor: la tabla puede engordar sin que el
    #    aparato crezca. Lo que queda es que el riel no baje del plano del
    #    suelo, que sigue siendo real -- por ahi entra el panel.
    y_bajo = cr[0][1] - hy
    minimo = p["holgura_rail"]
    assert y_bajo >= minimo - 1e-9, (
        f"el riel de panel del frente baja del plano del suelo: su esquina "
        f"girada cae en y={y_bajo:.2f} y se exige >={minimo:.2f} "
        f"(holgura_rail sobre y=0). Subir alto_frontal o inset_inf_frente "
        f"(van emparejados: la curva en punta pide "
        f"inset >= alto_frontal/2 + rail_er_alto/2 + 3)")
    # 2. LA BASE AGUANTA UNA MANO (papel del suelo, 2026-10-12, sec.3.2). Lo que
    #    la carga de verdad es poco: ella misma, el chasis en sus cuatro M4 y la
    #    trasera en el pie del talon (Elke, 0.31 a 0.41 mm). Lo que la decide es
    #    una mano de carga_mano apoyada en el campo, que es lo unico de la base
    #    que se alcanza, y se barre por toda la L. Dos condiciones, cada una en
    #    su peor sitio: no toca la mesa (flecha <= alto_pie - 1) y el borde de
    #    los agujeros no llega a la fluencia (el momento de la barra del campo,
    #    por el ligamento paso / (paso - agujero) del puente y por la
    #    concentracion K_BORDE_AGUJERO del papel, contra RP02_6082_T6). Es el
    #    criterio del papel: «en el borde de los agujeros, que concentra la
    #    tension de 2 a 3 veces, el aluminio se deforma para siempre». La chapa
    #    llena trabaja a una fraccion de eso (sin ligamento ni borde de agujero)
    #    y no se vigila aparte. Sustituye al aserto de la tabla de madera, que
    #    media 200 N en medio del vano contra 0.60 mm con E_madera.
    manos = _manos_en_el_campo(p)
    res = _flecha_base(p, [m[3] for m in manos])
    k_w = max(range(len(manos)), key=lambda k: res[k]["flecha"])
    k_s = max(range(len(manos)), key=lambda k: res[k]["m_campo"])
    paso, agujero, t_b = p["base_paso"], p["base_agujero"], p["t_base"]
    s_puente = 6 * res[k_s]["m_campo"] / t_b ** 2 * paso / (paso - agujero)
    s_borde = K_BORDE_AGUJERO * s_puente

    def donde(k: int) -> str:
        return f"brazo {manos[k][0]} (x={manos[k][1]:.0f}, z={manos[k][2]:.0f})"

    assert res[k_w]["flecha"] <= p["alto_pie"] - 1.0 + 1e-9, (
        f"la base cede {res[k_w]['flecha']:.2f} mm con una mano de "
        f"{p['carga_mano']:.0f} N en el {donde(k_w)} y las patas dejan "
        f"{p['alto_pie']:g}: toca la mesa. Sube t_base")
    assert s_borde <= RP02_6082_T6 + 1e-9, (
        f"el borde de los agujeros de la base llega a {s_borde:.0f} MPa "
        f"({K_BORDE_AGUJERO:g} x los {s_puente:.0f} del puente) con una mano de "
        f"{p['carga_mano']:.0f} N en el {donde(k_s)}, contra {RP02_6082_T6:.0f} "
        f"de limite elastico: el aluminio se deforma para siempre. Sube t_base "
        f"o cierra el campo")
    print(f"suelo: BASE de chapa t={t_b:g}; con {p['carga_mano']:.0f} N en "
          f"{len(manos)} sitios de la L cede {res[k_w]['flecha']:.2f} mm como "
          f"mucho, en el {donde(k_w)} (techo {p['alto_pie'] - 1:.0f}); el puente "
          f"trabaja a {s_puente:.0f} MPa y el borde del agujero a {s_borde:.0f} "
          f"(x{K_BORDE_AGUJERO:g}, en el {donde(k_s)}), contra {RP02_6082_T6:.0f}")
    # 3. y la trasera TAMBIEN llega al suelo. El suelo no lo cierra solo la
    #    bandeja: la cara trasera es la cuarta pared, y si su canto de abajo no
    #    baja hasta el mismo plano queda un rebaje corrido a lo largo de los
    #    528 mm. Eso es una JUNTA DE SOMBRA, que es justo el lenguaje que se
    #    enterro el 2026-08-21 cuando la trasera dejo de ser piel flotante y
    #    paso a plancha empotrada -- no es fuga (el canto de la bandeja lo
    #    cierra t_piel adentro), es que la pieza deja de leerse empotrada.
    #
    #    Nadie lo vigilaba: solapes() no canta porque no hay solape, y
    #    alineacion()/apoyo() solo miran filas de agujeros. El canto de abajo
    #    salia de un `- 15` sin derivar (la distancia al canto de la fila de
    #    M3), copiado en cinco sitios, y ese 15 no sabia donde estaba el suelo.
    #
    #    Se lee la caja DECLARADA, no se rehace la cuenta -- misma leccion que
    #    el assert 2.
    _, planchas, _ = _cajas_solidas(p)
    caja_pt = next(c for c in planchas if c[0] == "piel_trasera")
    y0_pt = caja_pt[3]
    assert abs(y0_pt - p["t_costilla"]) < 1e-6, (
        f"la trasera arranca en y={y0_pt:.2f} y el pie del talon acaba en "
        f"{p['t_costilla']:g}: o flota sobre el o se lo come. Desde el "
        f"2026-08-29 por la noche apoya EN el pie, no en el plano del suelo")






def guarda_remate(p: dict[str, float]) -> None:
    """La meseta del remate -- el ala del miembro trasero alto, no una tapa
    aparte del techo -- mide marco_remate entera, ni mas ni menos.

    En params.scad no se pueden escribir expresiones, o sea que prof_sup y
    marco_remate se mantienen iguales A MANO y por eso hace falta una puerta:
    mover uno sin el otro deja el techo corto o la banda asomando por el plano
    trasero, y ninguna de las dos se ve en un DXF plano.

    ERAN DOS SUMANDOS HASTA EL 2026-08-27, CUATRO HASTA LA MANANA DEL 29, TRES
    ESA TARDE Y UNO DESDE LA NOCHE, porque la meseta cambio de dueno tres
    veces. Antes era una plancha de acrilico apoyada encima del larguero y de
    la trasera, medida desde el plano trasero; despues el ala del miembro
    alto, que se quedaba t_piel + t_costilla corta por detras para que la
    trasera y su marco de chapa se metieran debajo (lo que abrio y cerro
    #234). Desde la noche del 29 la meseta LLEGA AL PLANO TRASERO y dobla ahi
    como banda -- la banda ES el miembro -- y la trasera va DENTRO de la
    banda, sin quitarle nada al techo. El reparto es uno solo:

        prof_sup              la meseta, del PICO al plano trasero, o sea
                              marco_remate entero.

    EL INSET MURIO EL 2026-08-29 al sustituir la meseta de acrilico apoyada por
    chapa de 1.5. La meseta LLEGA AL PICO, tapa el riel fijo y su retorno lo
    mide guarda_labio_chapas() (ficha 6)."""
    # UN SOLO SUMANDO DESDE EL 2026-08-29 POR LA NOCHE: la meseta llega al
    # plano trasero y dobla ahi como banda. Los otros dos (t_piel y
    # t_costilla, el ala del marco de la manana y su espesor) murieron con el
    # marco: la trasera va DENTRO de la banda, no debajo de un ala.
    assert abs(p["prof_sup"] - p["marco_remate"]) < 1e-9, (
        f"la meseta mide prof_sup = {p['prof_sup']:g} y el marco de remate "
        f"{p['marco_remate']:g}: la meseta va del pico al plano trasero, o sea "
        f"que son la misma cota y se mantienen a mano porque params.scad no "
        f"admite expresiones")
    P = _vertices(p)
    x_frente = P[6][0] - p["prof_sup"]
    assert abs(x_frente - P[4][0]) < 1e-9, (
        f"la meseta arranca en x = {x_frente:.2f} y el pico esta en "
        f"{P[4][0]:.2f}: o no llega, o se pasa")
    # :g y no :.0f -- una puerta que redondea la cota que vigila miente.
    print(f"remate: meseta de {p['prof_sup']:g} mm integrada en el miembro "
          f"trasero alto, hasta el pico (x = {P[4][0]:.2f})")


def _bd_angulo(p: dict[str, float], ang: float) -> float:
    """Bend deduction de un doblez de `ang` grados en la chapa de los
    miembros. A 90 da lo mismo que _bd_miembro(): SB = (r + t) tan(a/2),
    BA = a (r + k t) en radianes, BD = 2 SB - BA. Gemela de doblez_bd()."""
    r, t = p["radio_doblez_costilla"], p["t_costilla"]
    a = math.radians(ang)
    return 2 * (r + t) * math.tan(a / 2) - a * (r + p["k_factor"] * t)


def _nariz(p: dict[str, float]) -> dict:
    """La banda del frente: contorno, cotas y taladros. GEMELA de las
    funciones nariz_*() en sam17_case.scad.

    Chapa de t_costilla doblada sobre la nariz del anillo, del pie hacia
    arriba: pie sobre la tabla (y = 0..t, de x = c + pie a c), chaflan
    (c,0)-(0,c), frente vertical hasta P1 y un tramo subiendo por la cara de
    abajo hasta justo debajo de la placa de anclaje. Tres dobleces: dos a 45
    en el chaflan y uno de angulo_inferior en P1."""
    P = _vertices(p)
    c, t = p["chaflan_nariz"], p["t_costilla"]
    a = math.radians(p["angulo_inferior"])
    d, n = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
    s_top = _pata(p, "cara_inf")["escalon"] - p["hol_piel"]
    au = perfil(p)["ancho_util"]
    z0 = p["t_anillo"] + p["hol_piel"]
    contorno = [(c + p["nariz_pie"], 0.0), (c, 0.0), (0.0, c), P[1],
                (P[1][0] + d[0] * s_top, P[1][1] + d[1] * s_top)]
    cara = [P[1], contorno[4],
            (contorno[4][0] + n[0] * t, contorno[4][1] + n[1] * t),
            (P[1][0] + n[0] * t, P[1][1] + n[1] * t)]
    desarrollo = (p["nariz_pie"] + c * math.sqrt(2) + (p["alto_frontal"] - c)
                  + s_top - 2 * _bd_angulo(p, 45.0)
                  - _bd_angulo(p, p["angulo_inferior"]))
    return {"contorno": contorno, "s_top": s_top, "cara": cara,
            "m4_x": c + p["nariz_pie"] - _m4_pie_borde(p),
            "m4_z": [p["t_anillo"] + au * f for f in (0.25, 0.5, 0.75)],
            # Igual que el talon: el blank es lo que entra en rebaje (chaflan y
            # frente empotrados), y el pie queda en largo_pie tras la muesca.
            "largo": _chapa_largo_rebaje(p), "desarrollo": desarrollo,
            "largo_pie": au - 2 * p["hol_piel"],
            "muesca": _muesca_pie(p),
            "z0": z0, "z1": p["ancho_total"] - z0}


def _cajas_nariz(p: dict[str, float]) -> list[Caja]:
    """El pie y el frente de la nariz como cuerpos, alineados a ejes: son los
    que pueden pelearse con algo en 3D (clips, chasis, placas). El tramo de
    cara y el chaflan van girados y los mide guarda_nariz() contra lo suyo."""
    nz = _nariz(p)
    c, t = p["chaflan_nariz"], p["t_costilla"]
    return [("nariz pie", c, c + p["nariz_pie"], 0.0, t, nz["z0"], nz["z1"]),
            ("nariz frente", 0.0, t, c, p["alto_frontal"], nz["z0"], nz["z1"])]



def bbox_desarrollo_nariz(p: dict[str, float]) -> tuple[float, float]:
    """Envolvente del blank de la nariz: largo x desarrollo."""
    nz = _nariz(p)
    return nz["largo"], nz["desarrollo"]


def guarda_nariz(p: dict[str, float]) -> None:
    """La nariz cierra el frente sin estorbar a la fila de abajo, y el anillo
    dobla donde dobla la chapa.

    ES LA PUERTA DE LA NOTA 2 DE SAMUEL (2026-08-29): "en vez de una nariz
    curva, una nariz recta", con la esquina de abajo a 45 como en su
    referencia. Cinco cosas, cada una con su numero:

      1. radio_chapa ES el radio exterior del doblez (radio_doblez_costilla +
         t_costilla): la regla de que anillo y chapa compartan esquina.
      2. el chaflan deja frente vertical (>= 5) y no toca el riel del frente:
         la esquina del riel mas cercana a la nariz queda a x+y = 37.4 y el
         panel arranca a 39.2 -- debajo del riel hay aire, no modulos.
      3. (murio el 2026-10-11: la banda se paraba DEBAJO de la cara del riel
         con 1 mm de aire, regla del barrido de cuando las filas giraban; desde
         la persiana la nariz sube hasta pisar el riel y cerrar la rendija de
         la ficha 6, y lo vigila guarda_labio_chapas()).
      4. los M4 del pie: fuera de la zona del doblez del chaflan (setback +
         2t + d/2) y a 1.5 D del canto libre."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    nz = _nariz(p)
    c, t = p["chaflan_nariz"], p["t_costilla"]
    r_regla = p["radio_doblez_costilla"] + t
    assert abs(p["radio_chapa"] - r_regla) < 1e-9, (
        f"radio_chapa = {p['radio_chapa']:g} y el doblez de la chapa da "
        f"{r_regla:g} por fuera (radio_doblez_costilla + t_costilla): las "
        f"esquinas del anillo que llevan chapa encima tienen que doblar donde "
        f"dobla la chapa")
    frente = p["alto_frontal"] - c
    assert frente >= 5.0, (
        f"el chaflan de {c:g} deja {frente:.2f} mm de frente vertical sobre "
        f"los {p['alto_frontal']:g} de alto_frontal; se exigen 5")
    diag_riel = min(x + y for x, y in _esquinas_er(p, cr[0], p["angulo_inferior"]))
    assert diag_riel - c >= 5.0, (
        f"el chaflan de {c:g} se acerca a {diag_riel - c:.2f} mm de la esquina "
        f"del riel del frente (x+y = {diag_riel:.2f}); se exigen 5")
    raiz = p["radio_doblez_costilla"] + 3 * t + p["d_M4_paso"] / 2
    assert nz["m4_x"] - c >= raiz, (
        f"el M4 del pie cae a {nz['m4_x'] - c:.2f} de la linea del chaflan y "
        f"la regla de chapa pide {raiz:.2f}")
    canto = c + p["nariz_pie"] - nz["m4_x"]
    assert canto >= 1.5 * p["d_M4_paso"], (
        f"el M4 del pie queda a {canto:.2f} del canto libre; se exigen "
        f"{1.5 * p['d_M4_paso']:.2f}")
    print(f"nariz: chaflan de {c:g} a 45 ({frente:.2f} de frente vertical, "
          f"{diag_riel - c:.2f} al riel), banda de {t:g} hasta s = "
          f"{nz['s_top']:.2f} de la cara de abajo; panel y riel fijos")
    print(f"  la rendija la cierra el labio (guarda_labio_chapas); desarrollo "
          f"{nz['largo']:.2f} x {nz['desarrollo']:.2f}, {len(nz['m4_z'])} M4 a la tabla")


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
    # Y el que de verdad limita cuanto se puede acortar el valle no es este
    # SAT (72 mm de margen) sino la fila KONDOR dentro de su ventana, que lo mide
    # guarda_fila_1u() -- hasta el 2026-08-29 era la bahia centrada en ella.


# El censo de anchos de panel por piso MUERE aqui el 2026-08-27.
#
# Historia corta, porque la leccion vale mas que el diccionario: hasta hoy
# habia un ANCHOS_PISO_SUP = {"MIDI/CV": 80, "VCO1": 90, "VCO2": 90,
# "VCO3": 90} de la tesis. Se intento corregirlo entrada por entrada y salio
# PEOR: el numero nuevo se saco de hardware/03-vco/README.md, que se declara
# SUPERADO en su primera linea y trae los 114 mm en la columna «lo que esta
# carpeta asume» de la tabla que los mata. Cambiar un dato muerto por otro.
#
# Lo que lo disuelve no es un dato mejor sino una decision de Samuel del
# 2026-08-27: **la fila de arriba es UN modulo del ancho del riel, con la
# pantalla de 7" en su centro y todo lo demas ordenado a su alrededor**
# (docs/superpowers/specs/2026-08-27-panel-pantalla-al-centro-design.md).
#
# Con eso la fila superior deja de ser un reparto, asi que no hay nada que
# sumar: no es un diccionario con una clave, es que la pregunta cambio. Y el
# reparto que si sigue vivo -- el de la fila A entre PCB y bahia -- ya lo
# lleva hardware/03-vco/voz_total_budget.py, que corre como puerta propia.
# Duplicarlo aqui es lo que permitio que se desincronizara durante cuatro
# dias sin que nadie se enterara.

# La fila de ABAJO no tiene modelo aqui, y el diccionario vacio ES el hueco.
# Se deja vacio a proposito y no como bandera booleana: rellenarlo cierra la
# puerta sola, sin que nadie tenga que acordarse de apagar un flag. Por que
# esta abierta -- dos descripciones vivas que no coinciden -- en «Lo que este
# calculo NO cubre», al final del fichero.
FILA_INFERIOR: dict[str, float] = {}

ANCHO_PANTALLA_7 = 165.0        # mm. 2026-08-26-pantalla-motor-design.md sec.6
ALTO_PANTALLA_7 = 102.0         # mm. idem -- clase de pieza Adafruit 7"

# Lo que la fila A tenia que seguir albergando de mandos, DERIVADO y no
# tecleado: el panel viejo eran 83 HP y la bahia se llevaba 4 columnas a paso
# 17 (plan del panel sec.4). Lo que quede a los lados de la pantalla tiene que
# dar al menos eso, o el reencuadre no se sostiene -- es la cuenta del +9.68
# del papel, puesta como puerta en vez de como parrafo.
HP_FILA_A_VIEJA = 83
BAHIA_COLUMNAS, BAHIA_PASO = 4, 17.0

# Huecos declarados en ejecucion. Si queda alguno, main() sale con 2: HUECO
# visible, no fallo invisible. Constitucion, contrato de estados.
_HUECOS: list[str] = []


def flancos_fila_superior(p: dict[str, float]) -> dict[str, float]:
    """El lienzo de la fila de arriba con la pantalla al centro.

    Devuelve mm. El ancho de la fila es el RIEL, no el hueco entre costados:
    los modulos se atornillan a la pletina roscada del riel.
    """
    ancho = p["largo_riel"]
    return {
        "ancho_fila": ancho,
        "flanco": (ancho - ANCHO_PANTALLA_7) / 2,
        "franja": (p["alto_panel_sup"] - ALTO_PANTALLA_7) / 2,
    }


def guarda_fila_superior(p: dict[str, float]) -> list[str]:
    """La pantalla al centro tiene que caber en el panel, y en los DOS ejes.

    El eje que casi nadie mira es el vertical, y es el que aprieta: la
    pantalla se lleva 102 de los 128.5 de un 3U. Lo horizontal sobra por
    goleada y por eso no se asevera: seria una regla que no puede fallar.
    """
    fallos: list[str] = []
    f = flancos_fila_superior(p)

    if f["franja"] < 0:
        fallos.append(
            f"la pantalla de {ALTO_PANTALLA_7} mm no cabe de alto en un panel "
            f"de {p['alto_panel_sup']} mm")
    mandos_min = HP_FILA_A_VIEJA * p["hp"] - BAHIA_COLUMNAS * BAHIA_PASO
    mandos_hay = 2 * f["flanco"]
    if mandos_hay < mandos_min:
        fallos.append(
            f"los dos flancos dan {mandos_hay:.2f} mm de mando y el panel "
            f"viejo albergaba {mandos_min:.2f} (83 HP menos la bahia): el "
            f"reencuadre solo se sostiene si los flancos NO pierden sitio. "
            f"Con una pantalla de {ANCHO_PANTALLA_7:.0f} mm sobran "
            f"{mandos_hay - mandos_min:+.2f}")

    # Estos dos no son fallos: son cosas que este fichero NO PUEDE comprobar
    # todavia, y por eso salen como HUECO en vez de callarse. Mientras esten,
    # main() sale con 2 aunque todo lo demas cierre.
    _HUECOS.append(
        f"campo vertical util de una fila 3U sin derivar (#179 lo cifra en "
        f"112.5 y no dice de donde; con ese numero la franja cae de "
        f"{f['franja']:.2f} a {(112.5 - ALTO_PANTALLA_7) / 2:.2f} mm)")
    _HUECOS.append(
        "fondo de la pantalla sin medir contra la fila A, que el plan del "
        "panel declara al 100% con 0.6 mm de margen (E-C5)")
    return fallos


def guarda_dos_puertas_un_riel(p: dict[str, float]) -> list[str]:
    """Que voz_total_budget.py y este fichero repartan el MISMO riel.

    Los dos dividen los 528.32 mm de una fila, viven en directorios distintos
    y gates.py los corre en procesos separados, asi que nunca se ven. Aquel
    tiene RIEL_HP y HP cableados por valor. Esta guarda es el unico sitio
    donde los dos numeros se miran a la cara; sin ella, el dia que alguien
    cambie el riel aqui, alla sigue repartiendo el viejo y las dos puertas
    salen verdes contra realidades distintas.
    """
    fallos: list[str] = []
    import importlib.util
    ruta = Path(__file__).parent.parent / "hardware" / "03-vco" / "voz_total_budget.py"
    if not ruta.exists():
        return [f"voz_total_budget.py no esta en {ruta}: el reparto de la "
                f"fila A no tiene puerta"]
    spec = importlib.util.spec_from_file_location("_vtb", ruta)
    vtb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vtb)

    # Y CORRERLA. exec_module() la carga como `_vtb`, no como `__main__`, asi
    # que su demo() -- donde viven los assert del reparto de la fila A -- no
    # se ejecuta sola. Sin esto, delegar el reparto significaba dejar de
    # comprobarlo: verde aqui con la puerta delegada en rojo, y export.ps1
    # sacando DXF encima. Lo cazo codex en la revision del 2026-08-27.
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            vtb.demo()
        except AssertionError as e:
            fallos.append(f"voz_total_budget en ROJO (el reparto de la fila A "
                          f"no cierra): {str(e).splitlines()[0][:120]}")

    if abs(vtb.HP - p["hp"]) > 1e-9:
        fallos.append(f"voz_total_budget.HP={vtb.HP} != params.scad hp="
                      f"{p['hp']}")
    if abs(vtb.ANCHO_FILA - p["largo_riel"]) > 1e-9:
        fallos.append(f"voz_total_budget.ANCHO_FILA={vtb.ANCHO_FILA} != "
                      f"params.scad largo_riel={p['largo_riel']}: dos puertas "
                      f"reparten el mismo riel con numeros distintos")
    return fallos


def _chasis(p: dict[str, float]) -> dict[str, float]:
    """Geometria del chasis de acero, misma formula que sam17_case.scad.

    Se recalcula aqui en vez de leerla del .scad por la misma razon que el
    resto del budget: el .scad DIBUJA y este fichero DECIDE. Si las dos cuentas
    se separan, el desarrollo de la fibra neutra de mas abajo lo caza.
    """
    t, r, k = p["t_chapa"], p["radio_doblez"], p["k_factor"]
    sb = r + t
    ba = math.pi / 2 * (r + k * t)
    bd = 2 * sb - ba
    ext_x = p["chasis_int_x"] + 2 * t
    ext_y = p["chasis_int_y"] + 2 * t
    ext_z = p["chasis_int_z"] + t                    # cuerpo, sin tapa
    tapa_x = ext_x + p["chasis_hol_tapa"] + 2 * t
    tapa_y = ext_y + p["chasis_hol_tapa"] + 2 * t
    faldon = t + p["chasis_pestana"]
    return {
        "sb": sb, "ba": ba, "bd": bd,
        "ext_x": ext_x, "ext_y": ext_y, "ext_z": ext_z,
        "tapa_x": tapa_x, "tapa_y": tapa_y, "faldon": faldon,
        "alto": 2 * t + p["chasis_int_z"],           # exterior, con tapa
        "desfase": t + p["chasis_hol_tapa"] / 2,
        "blank_cuerpo_x": ext_x + 2 * ext_z - 2 * bd,
        "blank_cuerpo_y": ext_y + 2 * ext_z - 2 * bd,
        "blank_tapa_x": tapa_x + 2 * faldon - 2 * bd,
        "blank_tapa_y": tapa_y + 2 * faldon - 2 * bd,
    }


def _desarrollo_fibra(interior: float, alto_int: float,
                      p: dict[str, float]) -> float:
    """El desarrollo, andando la FIBRA NEUTRA en vez de restar deducciones.

    Esta es la unica comprobacion del chasis que no se puede escribir dos veces
    igual por accidente. La formula que usa el modelo -- desarrollo = suma de
    lados exteriores menos una bend deduction por doblez -- es la de taller, y
    es correcta, pero es OPACA: si el setback se escribe r en vez de r+t, o el
    signo de la deduccion se invierte, el numero sigue saliendo plausible y la
    chapa se corta mal. Cortada mal no se arregla: se vuelve a cortar.

    Asi que aqui se calcula por geometria, siguiendo la fibra que ni se estira
    ni se comprime, tramo por tramo:

        recto del suelo   +   arco de 90 grados   +   recto de la pared

    El centro del radio interior cae a (X_i - r, t + r) -- DENTRO de la esquina,
    que es la parte que se equivoca a ojo: la cara concava del doblez mira al
    interior de la caja. De ahi:

        recto del suelo por semi-lado = X_i - r
        arco (radio r + k*t, 90 grados) = BA
        recto de la pared = alto_interior - r

    y el total es el doble. Sale igual que la formula de taller -- lo cual es
    justo el punto: son dos caminos distintos al mismo numero.
    """
    t, r, k = p["t_chapa"], p["radio_doblez"], p["k_factor"]
    ba = math.pi / 2 * (r + k * t)
    return 2 * (interior / 2 - r) + 2 * ba + 2 * (alto_int - r)


def guarda_chasis(p: dict[str, float], g: dict[str, float]) -> list[str]:
    """El chasis de acero del PSU: cabe, contiene y se puede doblar (#107).

    Lo que NO comprueba, dicho aqui para que no se confunda con cobertura:
    que los tres agujeros de los TO-220 casen con los TO-220 de verdad. Esa
    fila la DECLARA el chasis y la consume la Task 6 al colocar la PCB; hasta
    que esa tarea exista, lo unico comprobable es que caigan en la pared con
    material alrededor, y eso si esta abajo.
    """
    c = _chasis(p)
    f: list[str] = []
    t = p["t_chapa"]

    def exige(cond: bool, msg: str) -> None:
        if not cond:
            f.append(msg)

    # --- 1. el desarrollo, por los dos caminos -----------------------------
    for nombre, interior, alto_int, blank in (
            ("cuerpo X", p["chasis_int_x"], p["chasis_int_z"],
             c["blank_cuerpo_x"]),
            ("cuerpo Y", p["chasis_int_y"], p["chasis_int_z"],
             c["blank_cuerpo_y"]),
            ("tapa X", c["tapa_x"] - 2 * t, p["chasis_pestana"],
             c["blank_tapa_x"]),
            ("tapa Y", c["tapa_y"] - 2 * t, p["chasis_pestana"],
             c["blank_tapa_y"])):
        fibra = _desarrollo_fibra(interior, alto_int, p)
        exige(abs(fibra - blank) < 1e-6,
              f"desarrollo [{nombre}]: la deduccion de doblez da {blank:.3f} mm "
              f"y la fibra neutra {fibra:.3f} mm ({blank - fibra:+.3f}). Una de "
              f"las dos cuentas esta mal y la chapa se corta con la del modelo")

    # --- 2. la caja cabe en el piso inferior del case ----------------------
    # EL HUECO ENTRE ANILLOS, no ancho_total - 2*t_cheek. Esa resta era la del
    # case de cuando la cara interior era el acrilico, y desde el 2026-08-28
    # daba 552.62 contra los 540.62 que hay de verdad: el chasis se comprobaba
    # contra una bandeja 12 mm mas ancha que la suya. g ES perfil(p) -- llega
    # calculado desde main(), no se rehace aqui.
    au = g["ancho_util"]
    fondo_bandeja = _fondo_bandeja(p)
    exige(c["alto"] + p["chasis_pie"] < g["alto_interior_inferior"],
          f"el chasis mide {c['alto'] + p['chasis_pie']:.1f} mm con sus pies y "
          f"el piso inferior da {g['alto_interior_inferior']:.2f}")
    exige(c["tapa_x"] + 2 * p["chasis_margen_bandeja"] <= au,
          f"el chasis mide {c['tapa_x']:.1f} de largo y la bandeja {au:.2f}")
    exige(c["tapa_y"] <= fondo_bandeja,
          f"el chasis mide {c['tapa_y']:.1f} de fondo y la bandeja "
          f"{fondo_bandeja:.2f}")

    # --- 3. el reparto interior cierra -------------------------------------
    # El toroide se mide con su holgura de salidas: la hoja avisa "allow extra
    # 4mm at leads", asi que la envolvente de diseno es diam + 4 y NO el diam.
    env = p["diam_transformador"] + 4
    borde_pcb = p["chasis_pcb_x"] + p["chasis_pcb_ancho"]
    exige(borde_pcb <= p["chasis_toroide_x"] - env / 2,
          f"la PCB acaba en x={borde_pcb:.0f} y el toroide empieza en "
          f"x={p['chasis_toroide_x'] - env / 2:.0f}: se pisan")
    exige(p["chasis_toroide_x"] + env / 2 <= p["chasis_int_x"] - p["chasis_pcb_x"],
          "el toroide se sale por la pared del fondo")
    exige(p["chasis_toroide_y"] - env / 2 >= 0
          and p["chasis_toroide_y"] + env / 2 <= p["chasis_int_y"],
          "el toroide se sale del interior por el fondo")
    exige(p["chasis_pcb_y"] + p["chasis_pcb_fondo"] <= p["chasis_int_y"],
          "la PCB no cabe en el fondo interior")
    exige(p["alto_transformador"] + p["margen_transformador"] <= p["chasis_int_z"],
          f"el toroide pide {p['alto_transformador'] + p['margen_transformador']:.0f} "
          f"mm de alto con margen y el interior da {p['chasis_int_z']:.0f}")
    # Y QUE NO SOBRE. El assert de arriba pide que el toroide QUEPA; este pide
    # que la caja no sea mas alta de lo que hace falta. Sin el, 19 mm de aire
    # vivieron dentro del chasis sin que nadie los reclamara, y el volumen de la
    # caja es lo que se ve al desmontar los paneles -- fue el primer comentario de Samuel
    # al mirar el render de la bahia: "parece de PSU de computadora".
    #
    # ES LA UNICA COTA DEL CHASIS QUE NO CUELGA DE OTRA PIEZA. El largo y el
    # fondo los manda la PCB, que esta dibujada (200 x 150 de Edge.Cuts en las
    # tres revisiones del repo); el alto solo lo manda el toroide.
    holgura_alto = p["chasis_int_z"] - (p["alto_transformador"]
                                        + p["margen_transformador"])
    exige(0 <= holgura_alto <= 2,
          f"el interior del chasis mide {p['chasis_int_z']:.0f} de alto y el "
          f"toroide pide {p['alto_transformador'] + p['margen_transformador']:.0f} "
          f"({holgura_alto:+.0f} mm de aire). Ver spec 8.1")

    # --- 4. los agujeros de pared, con material alrededor ------------------
    # Mismo criterio de borde que los taladros del acrilico (BORDE_MIN_D de
    # check_dxf): un agujero pegado al canto de una chapa doblada se abre al
    # doblar, y ademas se le come el radio del propio doblez.
    borde = p["radio_doblez"] + p["t_chapa"] + 1.0
    fila = [p["chasis_to220_x"] + p["chasis_to220_paso"] * (i - (p["chasis_to220_n"] - 1) / 2)
            for i in range(int(p["chasis_to220_n"]))]
    for x in fila:
        exige(borde <= x - p["d_M3_paso"] / 2 and
              x + p["d_M3_paso"] / 2 <= p["chasis_int_x"] - borde,
              f"el TO-220 de x={x:.0f} se sale de la pared larga")
    exige(borde <= p["chasis_to220_z"] - p["d_M3_paso"] / 2 and
          p["chasis_to220_z"] + p["d_M3_paso"] / 2
          <= p["chasis_int_z"] - p["chasis_tornillo_baja"] - p["d_M3_paso"],
          f"la fila de TO-220 a z={p['chasis_to220_z']:.0f} no deja material "
          f"contra el suelo o choca con la fila de tornillos de la tapa")
    exige(borde <= p["chasis_pe_y"] <= p["chasis_int_y"] - borde and
          borde <= p["chasis_pe_z"] <= p["chasis_int_z"] - borde,
          "el esparrago de PE se sale de la pared corta")

    # --- 5. la salida de cables ---------------------------------------------
    # Que la ranura del chasis CAIGA DENTRO del agujero del acrilico no se
    # comprueba aqui, y no por descuido: el .scad deriva el agujero de la
    # ranura con una sola funcion (salida_cables_xy), asi que la contencion es
    # cierta por construccion y un assert sobre ella no puede fallar nunca.
    # Una puerta que no puede ponerse roja es peor que no tenerla: se lee como
    # cobertura y no cubre nada.
    #
    # Lo que SI puede fallar es que la ranura se salga de la chapa o el agujero
    # de la plancha, y eso es lo que hay debajo.
    hol, rad = p["salida_holgura"], p["salida_radio"]
    w = p["chasis_salida_ancho"] + 2 * hol
    h = p["chasis_salida_fondo"] + 2 * hol
    exige(rad <= min(w, h) / 2,
          f"el redondeo de {rad:.0f} mm se come un agujero de {w:.0f} x {h:.0f}")
    borde_suelo = p["radio_doblez"] + p["t_chapa"] + 5.0
    exige(borde_suelo <= p["chasis_salida_x"] and
          p["chasis_salida_x"] + p["chasis_salida_ancho"]
          <= p["chasis_int_x"] - borde_suelo,
          f"la ranura de salida ocupa x={p['chasis_salida_x']:.0f}.."
          f"{p['chasis_salida_x'] + p['chasis_salida_ancho']:.0f} y el suelo "
          f"util va de {borde_suelo:.1f} a {p['chasis_int_x'] - borde_suelo:.1f}")
    exige(borde_suelo <= p["chasis_salida_y"] and
          p["chasis_salida_y"] + p["chasis_salida_fondo"]
          <= p["chasis_int_y"] - borde_suelo,
          "la ranura de salida se sale del suelo por el fondo")
    # y que no se la coma el toroide, que vive en el mismo suelo
    env = p["diam_transformador"] + 4
    exige(p["chasis_salida_x"] + p["chasis_salida_ancho"]
          <= p["chasis_toroide_x"] - env / 2,
          "la ranura de salida se mete debajo del toroide")
    # el agujero del acrilico, en coordenadas de bandeja_base_2d
    pos_x = au - p["chasis_margen_bandeja"] - c["tapa_x"]
    # El chasis se pega al larguero TRASERO, y de ahi hacia delante ya no hay
    # nada. Estuvo escrito como vuelo + rail + holgura -- la cadena leida al
    # reves desde el canto de la plancha -- y solo daba lo mismo porque `base
    # delantera` estaba justo ahi. Muerta esa barra el 2026-08-27 se escribe la
    # cadena en su sentido: la cara delantera del chasis, menos el canto de la
    # plancha. Da el mismo numero (91.85) y ahora por la razon correcta.
    pos_y = _x_chasis_frente(p)
    ax = pos_x + c["desfase"] + t + p["chasis_salida_x"] - hol
    ay = pos_y + c["desfase"] + t + p["chasis_salida_y"] - hol
    exige(0 <= ax and ax + w <= au
          and p["chaflan_nariz"] <= ay
          and ay + h <= p["chaflan_nariz"] + fondo_bandeja,
          f"el agujero de cables cae en x={ax:.1f}..{ax + w:.1f}, "
          f"y={ay:.1f}..{ay + h:.1f} y la base va de y={p['chaflan_nariz']:.2f} "
          f"a {p['chaflan_nariz'] + fondo_bandeja:.2f}: se sale de la pieza")

    # --- 6. el chasis: cuelga por detras y APOYA por delante ---------------
    # ESTA PREMISA SE HA INVERTIDO DOS VECES Y CONVIENE QUE LAS DOS ESTEN
    # ESCRITAS, porque la segunda deshace media razon de la primera.
    #
    # Hasta el 2026-08-21 era "la caja tiene que PASAR entre las dos barras sin
    # tocarlas": se apoyaba en la bandeja de ACRILICO, y esa plancha resuena
    # donde el toroide excita. El #106 la colgo de los dos largueros con 4 M5 a
    # la ranura interior del 2020 -- dos por pared larga -- y el acrilico dejo
    # de sostener el toroide.
    #
    # El 2026-08-27 se va `base delantera`, o sea el larguero del que colgaba la
    # PARED DELANTERA. Nadie lo habia mirado: ni la spec ni el plan mencionan el
    # chasis al retirar esa barra. Y el mismo dia el suelo deja de ser acrilico
    # y pasa a ser TABLA DE MADERA MACIZA bajo el marco, apoyada en las cuatro
    # paticas. O sea que el motivo por el que la caja no podia apoyarse -- que
    # debajo habia una plancha de PMMA colgada de dos barras -- ya no existe.
    #
    # Queda asi: la pared TRASERA sigue colgando de `base trasera` con sus 2 M5,
    # y la DELANTERA se atornilla hacia abajo a la tabla. Los dos caminos son
    # cortos y ninguno cruza el vano.
    #
    # LO QUE NO SE PUEDE CERRAR AQUI, y va dicho: si la tabla resuena bajo el
    # toroide no lo decide este presupuesto, porque el PESO DEL CHASIS NO ESTA
    # ITEMIZADO EN EL REPO (spec 10, sigue abierto). La madera amortigua un
    # orden de magnitud mas que el aluminio, y la tabla desnuda da del orden de
    # 120 Hz contra los 100 del toroide -- pero eso es la tabla sola. Se cierra
    # pesando el chasis.
    hol = p["chasis_holgura_larguero"]
    libre_1 = _talon(p)["x_pie"] - hol
    exige(pos_y >= 0 and pos_y + c["tapa_y"] <= libre_1,
          f"el chasis ocupa y={pos_y:.1f}..{pos_y + c['tapa_y']:.1f} de la "
          f"tabla y, con {hol:.0f} mm de holgura al pie del talon, cabe "
          f"de 0.0 a {libre_1:.1f}")
    print(f"  se arrima al pie del talon ({libre_1 - (pos_y + c['tapa_y']):.2f} "
          f"mm de sobra sobre el minimo de {hol:.0f}) y apoya en la tabla")

    # --- 6b. los cuatro M4 del suelo a la tabla (2026-08-29, noche) ---------
    # EL CHASIS COLGABA DE DOS M5 DE PARED "a la ranura interior de base
    # trasera", un 2020 que murio el 27-08; el modelo los siguio dibujando a
    # la altura de esa ranura dos dias y esta puerta solo miraba que cayeran
    # en la pared con material alrededor, no en que mordian. Muerto tambien el
    # miembro bajo, no queda nada ahi: el chasis apoya en la tabla y se
    # atornilla a ella por el suelo, desde abajo, a tuerca remachable.
    #
    # Los cuatro tienen que caer en suelo PLANO -- fuera de la curva del doblez
    # (r) con 1.5 D de margen --, fuera de la ranura de salida de cables y del
    # refuerzo del toroide (que es otra chapa remachada debajo: un agujero ahi
    # atraviesa dos), y lejos de los separadores de la PCB. Lo que va a la
    # base lo cruza guarda_bandeja_base() en check_dxf.
    borde_m4 = p["radio_doblez"] + 1.5 * p["d_M4_paso"]
    r_ref = p["chasis_refuerzo_lado"] / 2
    for ix, iy in _chasis_tornillos(p):
        exige(borde_m4 <= ix <= p["chasis_int_x"] - borde_m4
              and borde_m4 <= iy <= p["chasis_int_y"] - borde_m4,
              f"el M4 del suelo en ({ix:g}, {iy:g}) cae en la curva del doblez "
              f"de una pared: hacen falta {borde_m4:.2f} desde el interior")
        sx0 = p["chasis_salida_x"] - 1.5 * p["d_M4_paso"]
        sx1 = p["chasis_salida_x"] + p["chasis_salida_ancho"] + 1.5 * p["d_M4_paso"]
        sy0 = p["chasis_salida_y"] - 1.5 * p["d_M4_paso"]
        sy1 = p["chasis_salida_y"] + p["chasis_salida_fondo"] + 1.5 * p["d_M4_paso"]
        exige(not (sx0 < ix < sx1 and sy0 < iy < sy1),
              f"el M4 del suelo en ({ix:g}, {iy:g}) se mete en la ranura de "
              f"salida de cables")
        en_refuerzo = (abs(ix - p["chasis_toroide_x"]) < r_ref + p["d_M4_paso"] / 2
                       and abs(iy - p["chasis_toroide_y"]) < r_ref + p["d_M4_paso"] / 2)
        exige(not en_refuerzo,
              f"el M4 del suelo en ({ix:g}, {iy:g}) cae bajo el refuerzo del "
              f"toroide ({p['chasis_refuerzo_lado']:g} x {p['chasis_refuerzo_lado']:g} "
              f"centrado en ({p['chasis_toroide_x']:g}, {p['chasis_toroide_y']:g})): "
              f"atravesaria dos chapas y el refuerzo no lo lleva dibujado")
    exige(p["chasis_pie"] == 0,
          f"chasis_pie = {p['chasis_pie']:g}: el chasis se atornilla a la tabla "
          f"por el suelo y apoya en ella; el aire era para una bandeja de "
          f"acrilico que murio el 27-08")
    print(f"  4 M4 del suelo a la tabla desde abajo, a x={p['chasis_tornillo_x']:g} "
          f"e y={p['chasis_tornillo_y']:g} del interior (curva del doblez + 1.5 D "
          f"= {borde_m4:.2f}); ninguno bajo la ranura ni bajo el refuerzo")

    # --- 7. el tornillo de la tapa muerde faldon y pared a la vez ----------
    exige(p["chasis_tornillo_baja"] + p["d_M3_paso"] / 2 <= p["chasis_pestana"],
          f"el tornillo va a {p['chasis_tornillo_baja']:.0f} mm del techo y el "
          f"faldon solo baja {p['chasis_pestana']:.0f}: el agujero se sale")

    print(f"chasis: interior {p['chasis_int_x']:.0f} x {p['chasis_int_y']:.0f} x "
          f"{p['chasis_int_z']:.0f}, exterior {c['tapa_x']:.1f} x {c['tapa_y']:.1f} "
          f"x {c['alto']:.1f}")
    print(f"  desarrollo cuerpo {c['blank_cuerpo_x']:.2f} x {c['blank_cuerpo_y']:.2f}"
          f", tapa {c['blank_tapa_x']:.2f} x {c['blank_tapa_y']:.2f}  "
          f"(BA {c['ba']:.3f}, BD {c['bd']:.3f} por doblez)")
    print(f"  holgura en la bandeja: {au - c['tapa_x']:.1f} de largo, "
          f"{fondo_bandeja - c['tapa_y']:.1f} de fondo, "
          f"{g['alto_interior_inferior'] - c['alto'] - p['chasis_pie']:.1f} de alto")
    return f


def _fondo_bandeja(p: dict[str, float]) -> float:
    """Largo de la BASE en x, de chaflan a chaflan (papel del suelo,
    2026-10-12). Fue el vano entre los dos largueros hasta el 2026-08-21, y el
    fondo de la tabla con su vuelo hasta el papel del suelo."""
    return fondo(p) - 2 * p["chaflan_nariz"]


def main() -> int:
    p = leer_params()
    autocomprobacion(p)
    autocomprobacion_anillo()
    autocomprobacion_plano_neutro()
    autocomprobacion_base()
    autocomprobacion_emparrillado()
    autocomprobacion_pv()
    # LAS DOS COPIAS DE E SIGUEN CRUZADAS, y el motivo cambio el 2026-08-28. El
    # .scad la usaba para derivar alli que tramos de la costilla llevaban ala
    # (costilla_necesita_ala_rigidez), y eso murio con la chapa plegada: hoy la
    # flecha del anillo se calcula SOLO aqui. El parametro sigue en params.scad
    # y el assert sigue: el dia que alguien lo cambie alli -- porque el aluminio
    # de pletina es otro, por ejemplo -- este presupuesto tiene que enterarse en
    # vez de seguir dimensionando el anillo con el numero viejo.
    assert abs(p["E_aluminio"] - E_ALUMINIO) < 1, (
        f"params.scad dice E_aluminio = {p['E_aluminio']:.0f} y este modulo "
        f"usa {E_ALUMINIO:.0f}: el anillo se dimensionaria con un modulo que "
        f"el resto del repo no cree.")
    canario_solapes(p)
    canario_alineacion(p)
    guarda_rebaje(p)
    canario_acceso_marco(p)
    guarda_anclajes(p)
    guarda_marco_ventana(p)
    guarda_miembro_alto(p)
    guarda_talon(p)
    guarda_trasera_capturada(p)
    guarda_rebaje_chapa(p)
    guarda_tramo_trasero(p)
    guarda_trasera_flexion(p)
    canario_paneles_fijos(p)
    guarda_paneles_fijos(p)
    canario_labio_chapas(p)
    guarda_labio_chapas(p)
    canario_tira_valle(p)
    guarda_tira_valle(p)
    canario_fila_kondor(p)
    guarda_fila_1u(p)
    canario_rehundido_panel()
    guarda_rehundido_panel(p)
    guarda_meseta_es_chapa(p)
    guarda_piso(p)
    guarda_anillo(p)
    guarda_tacos_persiana(p)
    canario_tacos_persiana(p)
    guarda_rendija(p)
    guarda_potencia_vigente(p)
    guarda_campo_base(p)
    guarda_aire(p)
    guarda_chaflan(p)
    canario_valle(p)
    guarda_valle(p)

    guarda_paticas(p)
    canario_red(p)
    canario_trasera(p)
    canario_techo(p)
    canario_campo_base(p)
    canario_base_fina(p)
    guarda_red(p)
    guarda_fresado(p)
    guarda_puentes_ventilacion(p)
    guarda_parametros_vivos(p)
    guarda_escalon(p)
    guarda_remate(p)
    guarda_nariz(p)
    g = perfil(p)
    fallos: list[str] = []

    def exige(cond: bool, msg: str) -> None:
        (fallos.append if not cond else (lambda m: None))(msg)

    exige(g["alto_interior_inferior"]
          >= p["alto_transformador"] + p["margen_transformador"],
          "transformador no cabe en el piso inferior con margen")
    fallos += guarda_chasis(p, g)
    # Marco de remate = lo que queda del fondo detras de la cara superior.
    # AQUI HUBO un `marco >= 20` con el argumento "no caben los 20 mm del rail
    # de remate". La premisa caduco dos veces: primero el remate dejo de vivir
    # en el marco (su Y se derivaba y bajaba por debajo del rail girado del
    # panel), y desde el 2026-08-21 ese larguero ya no existe. El
    # marco solo tiene que dar para que los largueros quepan DENTRO de la
    # SILUETA -- la del anillo desde el 2026-08-28, no la del acrilico, que va
    # 14.5 mm mas adentro (Ruling R4) --, y eso ya no se estima con una cota a
    # ojo: lo comprueba `cuerpos_dentro_del_anillo()` en check_dxf.py (se llamo
    # `railes_dentro_del_costado()` mientras median contra el PMMA), esquina
    # por esquina y contra el contorno RELEIDO del DXF, que es el unico que
    # sabe cuanto material se comio el redondeo en punta.
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
    # ESTO FUE UNA IGUALDAD EXACTA hasta el 2026-08-26, y tenia razon mientras
    # ancho_util no era un hueco sino una CONSECUENCIA: los costados se
    # separaban lo que midieran las piezas que van de cara a cara, asi que el
    # riel no podia "no caber". Su argumento -- los Z-Rails son de catalogo, y
    # desincronizar significa o rieles que no llegan o rieles que hay que
    # cortar por la punta donde se fijan -- sigue vivo.
    #
    # AQUI SOLO SE COMPRUEBA QUE hol_riel SEA RAZONABLE, y conviene decir por
    # que tan poco: ancho_total se DERIVA de hol_riel, asi que
    # ancho_riel - largo_riel da hol_riel identicamente. Una banda sobre esa
    # resta seria tautologica -- no puede fallar --, que es exactamente el
    # vicio que este mismo bloque tenia antes con otra forma. Se probo: subir
    # hol_riel a 30 o bajarlo a -1 no ponia nada en rojo.
    #
    # LA VERIFICACION DE VERDAD VIVE EN check_dxf.py, contra el contorno
    # RELEIDO del DXF de la costilla, que es un artefacto independiente y por
    # tanto si puede contradecir al modelo. Mismo motivo por el que
    # guarda_costado() vivio alli, y no aqui, mientras hubo mejilla.
    #
    # Y ES POR LO QUE LA IGUALDAD ancho_util == largo_riel QUE TRAE EL MERGE
    # CON MAIN (2026-08-29) NO ENTRA AQUI. En `main` el riel sigue yendo de
    # costado a costado (ancho_total = largo_riel + 2*t_cheek) y esa igualdad
    # es cierta ahi. En esta arquitectura ancho_util = largo_riel + hol_riel +
    # 2*t_placa -- el riel flota dentro del anillo, detras de las placas --:
    # 541 contra 528.32, 12.68 mm de diferencia POR DISENO. Ese assert aqui
    # seria ROJO permanente sobre una geometria correcta.
    #
    # Y CON EL, MUEREN LOS DOS exige() de ANCHOS_PISO_SUP/ANCHOS_PISO_INF que
    # vivian justo debajo: esos diccionarios los disolvio main() el 2026-08-27
    # (el censo de panel por piso paso a ser la pantalla al centro,
    # guarda_fila_superior() mas abajo en este mismo fichero) y esta rama se
    # habia bifurcado de main ANTES de esa decision, asi que seguia
    # comprobando contra un modelo que ya no representa el panel.
    exige(0.1 <= p["hol_riel"] <= p["rail"] / 2,
          f"hol_riel = {p['hol_riel']}: por debajo de 0.1 el riel entra a "
          f"presion contra el ala de la costilla, y por encima de "
          f"{p['rail'] / 2:.0f} se queda corto de costado a costado y sus M4 "
          f"de punta trabajan de mala manera")
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
        # pasa arriba a proposito: el panel fijo remata a ras del vertice.
        # Negativo no: seria panel volando sobre el aire.
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
    fallos.extend(solapes(p))
    fallos.extend(alineacion(p))
    fallos.extend(apoyo(p))
    fallos.extend(guarda_fila_superior(p))
    fallos.extend(guarda_dos_puertas_un_riel(p))

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
    # El cierre (ROJO/HUECO/VERDE) esta UNA sola vez, al final: hasta el
    # 2026-08-27 habia un `for fallos / return` aqui y otro abajo, y el de
    # arriba cortocircuitaba la comprobacion de la fila de abajo.
    fl = flancos_fila_superior(p)
    print(f"fila superior: UN modulo de {fl['ancho_fila']:.2f} mm "
          f"({fl['ancho_fila'] / p['hp']:.0f} HP), pantalla de "
          f"{ANCHO_PANTALLA_7:.0f}x{ALTO_PANTALLA_7:.0f} al centro")
    print(f"  flancos de mando: 2 x {fl['flanco']:.2f} mm "
          f"({fl['flanco'] / p['hp']:.1f} HP) a los {p['alto_panel_sup']} de alto")
    print(f"  franja sobre y bajo la pantalla: {fl['franja']:.2f} mm -- "
          f"ahi NO cabe un potenciometro (#179 sigue abierto)")
    if not FILA_INFERIOR:
        _HUECOS.append(
            "la fila de abajo no tiene reparto aqui. No es falta de dato: el "
            "plan del panel y la spec de la Voz la describen distinto")
    else:
        # Rellenar el dict NO basta para dar verde: {'panel': 10000} tambien
        # es truthy. Lo cazo codex el 2026-08-27. Se comprueba el reparto.
        suma = sum(FILA_INFERIOR.values())
        if suma > p["largo_riel"]:
            fallos.append(
                f"la fila de abajo pide {suma:.2f} mm y el riel da "
                f"{p['largo_riel']:.2f}")
        for nombre, ancho_mm in FILA_INFERIOR.items():
            if ancho_mm <= 0:
                fallos.append(f"'{nombre}' tiene ancho {ancho_mm} en la fila "
                              f"de abajo")

    for f_ in fallos:
        print(f"ROJO: {f_}")
    if fallos:
        # ERA `return 2` hasta el 2026-08-27, y eso convertia TODO fallo real
        # de este budget en un HUECO a ojos de gates.py, que lee 2 como
        # "trabajo a medias, no rompe el resumen": la tanda cerraba con "GATES
        # EN VERDE" con el case en rojo. Mismo pecado que gates.py ya se
        # corrigio en _dep_ausente. Codigo 1 = ROJO; el 2 es solo para HUECO.
        return 1
    if _HUECOS:
        for h in _HUECOS[:-1]:
            print(f"  hueco: {h}")
        print(f"HUECO: {_HUECOS[-1]}")
        return 2
    print("clearance_budget: VERDE")
    return 0


# Lo que este calculo NO cubre (y donde se cierra):
#   * rigidez/flexion del vano de 500 mm  -> cargar el prototipo (spec §11)
#   * par de apriete sobre acrilico       -> probeta del cupon (spec §11)
#   * termica de la fuente v2             -> spec PSU v2 y su validacion
#   * nesting de planchas en el stock     -> lienzo del Task 5, a ojo
#   * el reparto de la FILA DE ABAJO. Abierto desde el 2026-08-27, y no por
#     falta de dato sino porque hay DOS descripciones vivas que no coinciden:
#       - el plan del panel (2026-08-23-panel-frontal-gramatica §4) la parte
#         en CABEZA 30 HP + INVITADOS 62 + SOMBRA 12 = 104 HP;
#       - la spec de la Voz (2026-08-23-modulo-voz-total §8) la parte en
#         cerebro 150 + mandos 120 + mixer 100 + reserva 40 = 410 de 528.
#     Mismo dia, misma fila, dos modelos. Y encima el 2026-08-27 se movieron
#     dos piezas: la CABEZA muere (la 7" es la unica cabeza) y los mandos se
#     suben a los flancos de la fila de arriba. Aqui NO se inventa un tercer
#     modelo: se deja dicho que el sitio esta abierto y con quien resolverlo.
#     Se cierra cuando el plan del panel y la spec de la Voz digan lo mismo.
#   * (CERRADO el 2026-08-21) distancia perpendicular placa<->rail. Decia que
#     alineacion() verifica que la fila caiga en la centerline de un rail pero
#     no cuanto hay entre la placa y ese rail. Ahora lo verifica apoyo(): exige
#     que todas las filas de una placa apoyen a la MISMA distancia, que es la
#     forma comprobable de la regla — el separador de una placa es uno solo.
#     Con eso salio el fallo que este hueco tapaba: la fila de abajo de
#     piel_inferior apoyaba 14 mm mas lejos que la de arriba
#   * paneles inclinados (1.6 mm, PCB de aluminio de modulo) en solapes():
#     su ajuste lo resuelve la rotacion de railes (R3), no un AABB — un
#     rectangulo largo y fino en diagonal sobreestima demasiado con caja
#     alineada a ejes como para que el resultado signifique algo

if __name__ == "__main__":
    sys.exit(main())
