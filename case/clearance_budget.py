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
                "t_valle": 5, "ancho_total": 500, "t_cheek": 8})
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


def _x_chasis_frente(p: dict[str, float]) -> float:
    """Cara delantera del chasis del PSU.

    Cuelga del larguero TRASERO, a chasis_holgura_larguero, y de ahi hacia
    delante no hay nada: una sola cadena en un solo sentido. Estuvo escrita
    dentro de _centros_transversal() porque de ella colgaba `base delantera`,
    que se plantaba otra holgura por delante del chasis. Muerta esa barra el
    2026-08-27, la cadena se acaba en el chasis y quien la necesita es ch_pos()
    -- que la calculaba al reves, sumando vuelo + rail + holgura desde el canto
    de la plancha, y solo daba lo mismo por como estaba puesta la barra."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    bajo = _cajas_miembro(p, P, cr, 0.0, 0.0)["trasero bajo"]
    return (bajo[1] - p["chasis_holgura_larguero"]
            - _chasis(p)["tapa_y"])


# centros_transversal(), ct_base(), ct_valle() y ct_remate() MURIERON juntos
# el 2026-08-27. Sus tres 2020 se sustituyeron en el mismo cambio por miembros
# de chapa con volumen, caras de apoyo y mas de una linea de anclaje; reducirlos
# otra vez a un punto central perderia justo la geometria que los distingue.


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
# Caja = (nombre, x0, x1, y0, y1, z0, z1)
Caja = tuple
# Fila de agujeros de una placa = (placa, fila, eje, coordenada en ese eje,
# rail frontera al que DEBE anclar). El eje es el que recorre la placa de un
# rail frontera al otro: X en las bandejas (horizontales), Y en las pieles
# (verticales). El rail va declarado, no se busca el mas cercano:
# una fila que cae por casualidad en la centerline de otro rail no esta
# anclada donde el diseno dice, y ese acierto casual no debe pasar la puerta.
Fila = tuple
CAJAS_BAHIA = frozenset({
    "bahia suelo",
    "bahia ala delantera",
    "bahia ala trasera",
})


def _cajas_miembro(p: dict[str, float], P: list[tuple[float, float]],
                    cr: list[tuple[float, float]], z0: float,
                    z1: float) -> dict[str, Caja]:
    """Cajas fisicas montadas; la bahia es una bandeja, no un macizo."""
    secciones = {n: (w, d) for n, w, d in _secciones_miembro(p)}
    w_bajo, d_bajo = secciones["trasero bajo"]
    w_alto, _ = secciones["trasero alto"]
    w_bahia, d_bahia = secciones["bahia"]
    x_trasera = P[6][0] - p["t_piel"]
    y_meseta = P[5][1] - p["marco_sup"]
    # EL ALA DELANTERA DE LA BAHIA LA COLOCA EL BARRIDO, no la ventana.
    #
    # Se ruleo mal dos veces seguidas el 2026-08-27, y las dos por mirar la cota
    # equivocada. Primero se puso en el canto de la ventana entre los dos rieles
    # del valle (105.94) -- el hueco fisico, que parece lo obvio --, y ahi la
    # tapa no alcanzaba el ala trasera. Corregido eso, seguia mal por el otro
    # lado: a 105.94 el ala se mete en el BARRIDO de la fila de abajo al abrirse
    # y la deja en 95.8 grados de los 180 que el diseno protege.
    #
    # Lo que manda es el radio de giro del riel, no el alcance de su esquina
    # quieta: es la misma leccion que guarda_tapa() tiene escrita desde que un
    # riel "holgado parado" no cabia girando. El ala va a holgura_rail por
    # delante de donde llega el barrido.
    x0_bahia = cr[1][0] + _radio_giro_riel(p) + p["holgura_rail"]
    y1_bahia = P[3][1] - p["t_valle"]
    x1_bahia = x0_bahia + w_bahia
    y0_bahia = y1_bahia - d_bahia
    t = p["t_costilla"]
    return {
        "trasero bajo": ("trasero bajo", x_trasera - d_bajo, x_trasera,
                          0.0, w_bajo, z0, z1),
        "trasero alto": ("trasero alto", x_trasera - w_alto, x_trasera,
                          y_meseta - w_alto, y_meseta, z0, z1),
        "bahia suelo": ("bahia suelo", x0_bahia, x1_bahia,
                         y0_bahia, y0_bahia + t, z0, z1),
        "bahia ala delantera": ("bahia ala delantera",
                                  x0_bahia, x0_bahia + t,
                                  y0_bahia, y1_bahia, z0, z1),
        "bahia ala trasera": ("bahia ala trasera",
                                x1_bahia - t, x1_bahia,
                                y0_bahia, y1_bahia, z0, z1),
    }


def _envolvente_bahia(cajas: dict[str, Caja]) -> Caja:
    """Envolvente total para cuentas de luz, ancho y vuelo, nunca colisiones."""
    caras = [cajas[n] for n in CAJAS_BAHIA]
    return ("bahia",
            min(c[1] for c in caras), max(c[2] for c in caras),
            min(c[3] for c in caras), max(c[4] for c in caras),
            min(c[5] for c in caras), max(c[6] for c in caras))


def _centros_rail_1u(p: dict[str, float], P: list[tuple[float, float]],
                      bahia: Caja) -> list[tuple[float, float]]:
    """Dos Z-Rails 1U centrados en la boca, gemelos de centros_rail_1u()."""
    xc = (bahia[1] + bahia[2]) / 2
    sep = p["alto_panel_1u"] - 2 * p["inset_er"]
    y = P[3][1] - p["t_panel"] - p["rail_er_eje"]
    return [(xc - sep / 2, y), (xc + sep / 2, y)]


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
# LA PLACA ES EL MARCO DE LA FILA. UNA por TRAMO y por costado, no una por
# riel: corre el tramo entero entre las esquinas del anillo y recoge sus dos
# rieles. Lo decidio Samuel el 2026-08-28 mirando el render -- con placas
# sueltas de 28 quedaba una ranura de 6.15 mm abierta en cada punta de cada
# fila, el hueco entre el riel de 104 HP y la cara interior del anillo, y por
# ahi se veia el interior. El canto de 6 mm de la placa corrida lo tapa y
# desde delante se lee como el borde de aluminio de la fila.
#
# (nombre, vertice de arranque, vertice de fin, indices de centros_rail() que
# recoge). El valle recoge los DOS rieles 1U y va aparte porque su fondo no es
# placa_fondo -- ver _placa_1u_fondo().
# El ultimo campo dice cual de las DOS esquinas hondas va cortada a 45, y
# cuesta escribirlo asi: un chaflan que no hace falta se come el canto que el
# cajeado del riel necesita. Con la placa de la cara inferior chaflanada por
# los dos lados, el cajeado del riel del frente se quedaba a 4.32 mm del canto
# contra los 6.75 que pide -- 0.32 de pared tras un cajeado de 8.
# EN CADA VERTICE COMPARTIDO SE REPARTE EL RINCON, porque las dos placas
# vecinas quieren el mismo material: la cuna que queda entre sus dos fondos.
# En P2 -- el pico, convexo -- se parte a 45 con un chaflan por cabeza. En P3
# no hay cuna que partir (es concavo y los dos fondos divergen), pero la placa
# del valle SE PASA de largo hasta cubrir el cajeado de su segundo riel, asi
# que ahi cede la de la cara superior con un retiro extra. Los dos numeros los
# adjudico solapes() con la geometria real, y ninguno le quita canto a un
# cajeado: lo comprueba guarda_anclajes().
#   (nombre, vertice inicio, vertice fin, rieles, chaflan en cada esquina
#    honda, retiro extra en cada extremo)
TRAMOS_PLACA = [("cara_inf", 1, 2, (0, 1), (None, "bisectriz"), (0.0, 0.0)),
                ("valle",    2, 3, None,   ("bisectriz", None), (0.0, 0.0)),
                # la de arriba no reparte rincon con nadie: libra la BRIDA del
                # miembro trasero alto, que ocupa ese mismo sitio a z=14..15.5.
                # Y cede 12 mm en P3 porque ahi la placa del valle pasa de
                # largo para alcanzar el cajeado de su segundo riel.
                ("cara_sup", 3, 4, (2, 3), (None, "45"),        ("retiro_placa_sup", 0.0))]

# Radio de redondeo por vertice, gemelo de radios_perfil() en el .scad.
RADIOS_PERFIL = ["radio_punta", "radio_punta", "radio_pico", "radio_valle",
                 "radio_remate", "radio_trasero", "radio_trasero"]


def _retiro_placa(p: dict[str, float], P: list[tuple[float, float]],
                   i: int) -> float:
    """Cuanto se retira la placa del vertice i, a lo largo de su tramo.

    LA TANGENTE DEL REDONDEO si el vertice es CONVEXO -- ahi el contorno se
    mete hacia dentro y una esquina de placa apoyada sobre la recta se saldria
    de la silueta -- y CERO si es concavo, porque ahi el redondeo aparta el
    contorno y la placa puede pasar de largo. El perfil se recorre en sentido
    HORARIO (shoelace negativo), asi que convexo es producto vectorial < 0.

    Es lo que decide donde acaba cada placa, y quien lo comprueba contra el
    fichero que va al taller es cuerpos_dentro_del_anillo() en check_dxf."""
    A, V, B = P[(i - 1) % len(P)], P[i], P[(i + 1) % len(P)]
    cruz = (V[0] - A[0]) * (B[1] - V[1]) - (V[1] - A[1]) * (B[0] - V[0])
    return _tangente(V, A, B, p[RADIOS_PERFIL[i]]) if cruz < 0 else 0.0


# Como se reparte el rincon de P2 entre las dos placas que se encuentran ahi:
# que fraccion del angulo interior se lleva la que LLEGA al vertice (la de la
# cara inferior). La bisectriz -- 0.50 -- es el reparto justo y no vale: el
# riel del valle de abajo vive a 15.75 mm del pico y su cajeado se quedaba a
# 5.96 del corte contra los 6.75 que pide, asi que la del valle cede -- su
# riel mas cercano esta a 27.4 y no lo nota.
#
# LA VENTANA ES ESTRECHA y por eso el numero va con dos decimales: por debajo
# de 0.52 el cajeado de la cara inferior se queda corto (6.75) y por encima de
# 0.53 el corte se come el canto del M3 de la pestana de la banda, que vive en
# ese mismo rincon a 13.7 de profundidad y pide 5.10. Con 0.52 quedan 6.88 y
# 5.45. Las dos las comprueba guarda_anclajes(), asi que mover esto de oido
# sale en rojo.


def _corte_placa(p: dict[str, float], P: list[tuple[float, float]], i: int,
                  fondo: float, retiro: float, modo, fin: bool
                  ) -> tuple[float, float]:
    """(ds, db) del corte de una esquina honda de la placa.

    DOS CORTES DISTINTOS, y no son lo mismo aunque los dos quiten una esquina:

      "bisectriz"  reparte el rincon con la placa VECINA. Dos placas que se
                   encuentran en un vertice del anillo quieren la misma cuna de
                   material -- la que queda entre sus dos fondos -- y hay que
                   partirla. Se parte por la bisectriz del vertice, que es la
                   linea donde las dos tienen el mismo derecho: cada una llega
                   a fondo/tan(angulo/2) del vertice. Un chaflan de 45 no vale
                   aqui: con el pico a 125 grados y 26 de fondo haria falta un
                   corte de 30 mm sobre una placa de 26 de honda.
      "45"         libra una pieza concreta -- la brida del miembro alto -- y
                   ahi el corte es el de siempre, placa_chaflan a 45.

    Devuelve (0, 0) si no hay corte, y descuenta el retiro porque el corte se
    mide desde el VERTICE y la placa ya arranca retirada de el."""
    if modo == "45":
        return (p["placa_chaflan"], p["placa_chaflan"])
    if modo != "bisectriz":
        return (0.0, 0.0)
    A, V, B = P[(i - 1) % len(P)], P[i], P[(i + 1) % len(P)]
    ax, ay = A[0] - V[0], A[1] - V[1]
    bx, by = B[0] - V[0], B[1] - V[1]
    ang = math.acos(max(-1.0, min(1.0, (ax * bx + ay * by)
                                   / (math.hypot(ax, ay) * math.hypot(bx, by)))))
    r = p["reparto_rincon"]
    parte = ang * (r if fin else 1 - r)
    return (max(0.0, fondo / math.tan(parte) - retiro), fondo)


def _y_brida_bahia(p: dict[str, float]) -> float:
    """Y del M4 con el que cada ala de la bahia se cuelga de la placa del valle.

    LA BOCA DE LA BAHIA ESTA LLENA, y por eso la bahia no ancla al anillo
    (ruling R3): la franja del valle la ocupa entera la placa, y encima de ella
    los dos Z-Rails 1U calzan A RAS de las dos alas (guarda_fila_1u exige
    justamente esa igualdad: boca = separacion + un alto de riel). No queda ni
    un milimetro entre ala y riel.

    Lo unico libre es POR DEBAJO del riel, que baja rail_er_fondo/2 desde su
    eje. La lengueta se para 1 mm antes y su M4 va 1.5 D mas abajo."""
    P = _vertices(p)
    bahia = _envolvente_bahia(_cajas_miembro(p, P, _centros_rail(p, P), 0.0, 0.0))
    c1u = _centros_rail_1u(p, P, bahia)[0]
    return c1u[1] - _he_er(p, 90.0)[1] - 1.0 - 1.5 * p["d_M4_paso"]


def _placa_1u_fondo(p: dict[str, float]) -> float:
    """La placa del valle es MAS HONDA que las de 3U, y no por gusto.

    Las de 3U miden placa_fondo porque solo tienen que llegar al cajeado del
    riel (15.90 + el radio del cajeado). Esta ademas RECIBE LAS DOS LENGUETAS
    de la bahia, y esas tienen que caer por debajo del riel 1U: el fondo sale
    de donde cae su M4 mas 1.5 D de canto."""
    return _vertices(p)[3][1] - (_y_brida_bahia(p) - 1.5 * p["d_M4_paso"])


def _placas(p: dict[str, float]) -> list[tuple]:
    """(nombre, A, u, n, s0, s1, fondo, chaflan, ejes) de cada placa.

    A es el vertice de arranque del tramo, u el unitario a lo largo y n la
    normal hacia dentro -- la misma convencion de _centros_rail()
    (n = (d.y, -d.x)). Un punto de la placa es A + u*s + n*b, con s entre s0 y
    s1 y b entre 0 y fondo. `ejes` lleva, por cada riel que recoge,
    (s del eje sobre el tramo, punto, si lleva sus dos roscas ciegas).

    GEMELA de placas() en sam17_case.scad."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    bahia = _envolvente_bahia(_cajas_miembro(p, P, cr, 0.0, 0.0))
    c1u = _centros_rail_1u(p, P, bahia)
    out = []
    for nombre, i0, i1, idx, chaflanes, extra in TRAMOS_PLACA:
        A, B = P[i0], P[i1]
        L = math.hypot(B[0] - A[0], B[1] - A[1])
        u = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
        n = (u[1], -u[0])
        ex = [p[q] if isinstance(q, str) else q for q in extra]
        s0 = _retiro_placa(p, P, i0) + ex[0]
        s1 = L - _retiro_placa(p, P, i1) - ex[1]
        centros = [cr[i] for i in idx] if idx else c1u
        # LA SEGUNDA 1U NO LLEVA ROSCAS y no es un olvido: radio_valle = 54
        # curva la franja del valle y su fondo util pasa de 8.51 mm en x=128 a
        # 12.45 en x=148, o sea que una broca puesta ahi sale por la pared del
        # rebaje. Sus dos roscas se quedan sobre la primera, en el tramo recto.
        ejes = [((c[0] - A[0]) * u[0] + (c[1] - A[1]) * u[1], c,
                 bool(idx) or k == 0)
                for k, c in enumerate(centros)]
        # LA PLACA DEL VALLE SE ALARGA hasta cubrir el cajeado de su segundo
        # riel con 1.5 D de canto: ese eje cae PASADO P3 (150.38 contra 147.8)
        # y el tramo por si solo no llega. Puede pasarse porque P3 es concavo y
        # el redondeo de 54 aparta ahi el contorno -- lo verifica
        # cuerpos_dentro_del_anillo() esquina por esquina.
        if not idx:
            s1 = max(s1, max(e[0] for e in ejes) + 2 * p["d_M4_paso"])
        fondo = _placa_1u_fondo(p) if not idx else p["placa_fondo"]
        ch = tuple(_corte_placa(p, P, i, fondo, r, modo, fin)
                   for i, r, modo, fin in ((i0, s0, chaflanes[0], False),
                                            (i1, L - s1, chaflanes[1], True)))
        out.append((nombre, A, u, n, s0, s1, fondo, ch, ejes))
    return out


def _esquinas_placa(pl: tuple) -> list[tuple[float, float]]:
    """Las esquinas REALES de la placa ya girada con su tramo, con las dos
    esquinas hondas cortadas a 45.

    Hacen falta de verdad y no vale su caja: un rectangulo de 130 x 26 girado
    35 o 45 grados tiene una AABB de casi el doble de area, y en el rincon del
    valle -- donde en 60 mm conviven dos rieles, la banda, su pestana, un ala
    de la bahia y dos placas -- esa caja acusa de chocar a piezas que ni se
    rozan. Es la misma cuenta que _esquinas_er() hace con los rieles
    inclinados y por el mismo motivo."""
    _, A, u, n, s0, s1, fondo, (ch0, ch1), _ = pl
    ab = [(s0, 0.0), (s1, 0.0)]
    ab += ([(s1, fondo - ch1[1]), (s1 - ch1[0], fondo)] if ch1[0] > 0
           else [(s1, fondo)])
    ab += ([(s0 + ch0[0], fondo), (s0, fondo - ch0[1])] if ch0[0] > 0
           else [(s0, fondo)])
    # un corte que se come el fondo entero deja el vertice pegado al de la
    # arista de arriba; repetido rompe el SAT (arista de largo cero)
    ab = [q for i, q in enumerate(ab)
          if all(abs(q[0] - r[0]) + abs(q[1] - r[1]) > 1e-9 for r in ab[:i])]
    return [(A[0] + u[0] * a + n[0] * b, A[1] + u[1] * a + n[1] * b)
            for a, b in ab]


def _roscas_placa(p: dict[str, float], pl: tuple
                   ) -> list[tuple[str, tuple[float, float]]]:
    """(nombre, centro) de las dos roscas ciegas que lleva cada riel de una
    placa, a sep_rosca_riel del eje a lo largo del tramo.

    EL PAR SE ARRIMA AL RIEL, PERO NO SE SALE DE LA PLACA. La regla en crudo
    -- eje +- 7 -- deja la rosca del riel del frente a 1.01 mm del canto de su
    placa, porque ese riel arranca casi pegado al vertice P1; el par se corre
    lo justo para que las dos queden a 1.5 D del canto, la misma cota que se
    le exige a cualquier otro agujero de esta pletina. De paso saca de la zona
    estrecha a la del valle de arriba, donde el redondeo concavo de P3 aprieta
    la franja a 13.2 mm en vez de 14."""
    nm, A, u, n, s0, s1, fondo, cortes, ejes = pl
    sep = p["sep_rosca_riel"]
    d = p["dist_rosca_ciega"]
    # 1.6 D y no 1.5: la puerta exige 1.5, y una cota colocada justo en el
    # limite de su propia puerta vive del redondeo de coma flotante.
    canto = 1.6 * p["d_M4_paso"]

    def limite(s_ext, corte, signo):
        """Hasta donde llega una rosca a profundidad d sin acercarse a este
        extremo mas de `canto`. El margen NO es s1 - s cuando el extremo va
        cortado: el corte entra en diagonal y se come mas de lo que parece --
        3.11 mm en la placa de la cara inferior, a la altura de la rosca."""
        ds, db = corte
        if ds <= 0 or d <= fondo - db:
            return s_ext + signo * canto
        cos_a = db / math.hypot(ds, db)
        return s_ext + signo * (ds * (d - (fondo - db)) / db + canto / cos_a)

    lo, hi = limite(s0, cortes[0], +1), limite(s1, cortes[1], -1)
    out = []
    for s_eje, _, con_roscas in ejes:
        if not con_roscas:
            continue
        c = min(max(s_eje, lo + sep), hi - sep)
        for q in (c - sep, c + sep):
            out.append((f"placa {nm} {q:+.1f}",
                        (A[0] + u[0] * q + n[0] * d,
                         A[1] + u[1] * q + n[1] * d)))
    return out


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



def _cajas_placa(p: dict[str, float], z0: float, z1: float) -> list[Caja]:
    """La placa de anclaje como cuerpo: el tramo entero de largo x su fondo
    desde la silueta hacia dentro x t_placa, pegada a la cara interior del
    anillo. Es tambien la que retiene el acrilico hacia dentro y la que tapa,
    con su canto, la ranura del extremo de cada fila.

    La caja es la AABB de la placa girada; el solape fino lo resuelve
    _solape_riel_exacto() con las esquinas reales."""
    out: list[Caja] = []
    for pl in _placas(p):
        q = _esquinas_placa(pl)
        xs, ys = [e[0] for e in q], [e[1] for e in q]
        for lado, (za, zb) in enumerate(((z0, z0 + p["t_placa"]),
                                          (z1 - p["t_placa"], z1))):
            out.append((f"placa {pl[0]} {lado}", min(xs), max(xs),
                        min(ys), max(ys), za, zb))
    return out


def _bridas(p: dict[str, float], cajas: dict[str, Caja]) -> list[tuple]:
    """(nombre, rectangulo en el plano del perfil, centros M4, a que ancla).

    Lengueta de chapa de t_costilla doblada del extremo de cada miembro,
    plana contra la cara que la recibe, con relieve en las dos esquinas para
    que el doblez no muerda el ala vecina.

    LOS DOS TRASEROS doblan del ALMA y apoyan en la franja del anillo, dentro
    de sus 14 mm. La BAHIA (ruling R3) no: su boca esta ocupada por la placa
    de la fila 1U, asi que sus alas acaban t_placa antes del anillo y cada una
    dobla su lengueta contra esa placa, con un M4 roscado EN LA PLACA -- ese
    no entra en _centros_rosca_ciega().

    EL EJE DEL DOBLEZ ES LO QUE HACE LEGAL EL AGUJERO. La brida se dobla sobre
    una linea PERPENDICULAR al canto del anillo, asi que su largo corre a lo
    largo del canto: la distancia al doblez (9.75) y la distancia a la silueta
    (8.5) son cotas de ejes distintos y no compiten. Con el doblez paralelo al
    canto serian la MISMA cota y no habria agujero legal -- 9.75 pedido contra
    9.05 disponible. Es exactamente lo que le pasa a la pestana de la banda del
    valle, y por eso ella no rosca en el anillo sino en la PLACA del valle."""
    P = _vertices(p)
    t = p["t_costilla"]
    L = p["brida_largo"]
    # Regla de chapa: el agujero no entra en la zona del doblez. Setback mas
    # 2t mas el radio del agujero, la misma cuenta que pv_a() hace en la
    # pestana del valle.
    raiz = p["radio_doblez_costilla"] + t + 2 * t + p["d_M4_paso"] / 2
    libre = 1.5 * p["d_M4_paso"]
    bajo, alto = cajas["trasero bajo"], cajas["trasero alto"]
    x_alma = bajo[2]                        # cara trasera del alma, comun
    xs = (x_alma - raiz, x_alma - L + libre)
    out = [
        # el canto INFERIOR del anillo (y = 0) es el que recibe esta brida
        ("trasero bajo", (x_alma - L, x_alma, bajo[3], bajo[4]),
         [(x, P[0][1] + p["dist_rosca_ciega"]) for x in xs], "anillo"),
        # y la MESETA (y = P5.y) la de arriba. La brida acaba t_costilla por
        # debajo de ese canto -- ahi va la meseta, que es el otro ala -- y por
        # eso dist_rosca_ciega vale 8.5 y no 7: es esta la que se quedaba sin
        # canto libre.
        ("trasero alto", (x_alma - L, x_alma, alto[3], alto[4]),
         [(x, P[5][1] - p["dist_rosca_ciega"]) for x in xs], "anillo"),
    ]
    y_b = _y_brida_bahia(p)
    for nm, signo in (("bahia ala delantera", +1), ("bahia ala trasera", -1)):
        ala = cajas[nm]
        raiz_x = ala[1] if signo > 0 else ala[2]
        x0, x1 = sorted((raiz_x, raiz_x + signo * p["brida_bahia_vuelo"]))
        out.append((nm, (x0, x1, y_b - libre, y_b + libre),
                    [(raiz_x + signo * raiz, y_b)], "placa"))
    return out


def _cajas_brida(p: dict[str, float], cajas_miembro: dict[str, Caja],
                  z0: float, z1: float) -> list[Caja]:
    """Las bridas como cuerpos: t_costilla de espesor contra la cara que las
    recibe -- el anillo en las dos traseras, la placa 1U en las de la bahia."""
    out: list[Caja] = []
    t = p["t_costilla"]
    for nm, (x0, x1, y0, y1), _, ancla in _bridas(p, cajas_miembro):
        base = z0 + (p["t_placa"] if ancla == "placa" else 0.0)
        techo = z1 - (p["t_placa"] if ancla == "placa" else 0.0)
        for lado, (za, zb) in enumerate(((base, base + t), (techo - t, techo))):
            out.append((f"brida {nm} {lado}", x0, x1, y0, y1, za, zb))
    return out


# LOS CLIPS DE RETENCION, por tramo del perfil y por s del centro sobre ese
# tramo, medido desde el vertice de arranque. GEMELA de tramos_clip() en el
# .scad, y quien decide la lista es guarda_costado() en check_dxf: el acrilico
# empujado HACIA DENTRO se apoya en placas y clips, y donde no llega ninguno
# la flecha se dispara.
#
# SOLO EL SUELO, y no es lo que pedia la spec (§4 parte de seis por costado:
# dos suelo, dos trasera, uno frente, uno meseta). Los otros tres tramos NO
# TIENEN FRANJA LIBRE donde atornillar un clip, y eso lo dice la geometria, no
# el gusto:
#   trasera  la piel trasera se empotra entre los dos anillos y su canto apoya
#            en los 8 mm exteriores de la franja (x 299.41..307.41). Quedan 6
#            de los 14, y un clip que arrancara ahi dejaria su M4 a 0.35 mm
#            del propio canto del clip contra los 6.75 que pide el paso M4.
#   meseta   entre el chaflan de 45 de la placa cara_sup (x 266.72) y la brida
#            del miembro trasero alto (x 272.41) quedan 5.69 mm libres, y el
#            clip mide clip_largo = 20.
#   frente   el tramo entero mide alto_frontal = 19 -- menos que el clip -- y
#            ademas la punta de la placa cara_inf ya cruza por encima.
# Lo comprueba solapes(): meter un clip en cualquiera de los tres sale ROJO
# contra piel_trasera, brida trasero alto o placa cara_inf.
#
# Y NO HACEN FALTA ALLI: con estos dos el punto peor del acrilico se queda en
# el medio del canto trasero, a 95 mm de la placa cara_sup, y el techo del
# vano son 149. Los numeros los imprime guarda_costado() en cada corrida.
# DONDE CAEN LOS DOS, y ninguno de los dos numeros es a ojo. El suelo admite el
# centro del clip entre s = 45 y s = 262 (barrido de 1 mm contra los cuerpos de
# _cajas_solidas): por debajo de 45 el clip pisa la brida del miembro trasero
# bajo, y por encima de 262 la punta de la placa cara_inf, que baja hasta
# y = 11.86.
#   s = 50   lo pide la puerta. Es el rincon de atras del acrilico -- el punto
#            (291, 14) -- el que sale rojo sin el: 159.6 mm de vano y 0.68 de
#            flecha. Va lo mas arrimado al rincon que deja la brida.
#   s = 150  no mueve el numero global (ese lo fija el medio del canto trasero,
#            a 95.5 de la placa cara_sup) pero si el canto de abajo, que es el
#            unico que este clip puede cubrir: con el en 150 el peor punto de la
#            banda de abajo se queda a 53 mm de un apoyo, y con el arrimado al
#            frente -- s = 255, que es donde se probo primero -- a 89.8.
#   (tramo, vertice de arranque, vertice de fin, s del centro)
TRAMOS_CLIP: list[tuple[str, int, int, float]] = [("suelo", 6, 0, 50.0),
                                                  ("suelo", 6, 0, 150.0)]


def _clips(p: dict[str, float]
            ) -> list[tuple[str, list[tuple[float, float]], tuple[float, float]]]:
    """(nombre, esquinas en el plano del perfil, centro de su rosca ciega).

    Pletina de t_clip apoyada en la cara INTERIOR del anillo, de clip_largo a
    lo largo del tramo y clip_fondo hacia dentro desde la silueta, con un M4 a
    rosca ciega centrado a lo largo y a dist_rosca_ciega de la silueta -- la
    misma cota que placas y bridas, que es la unica que cabe en la franja.

    Misma convencion que _placas(): A el vertice de arranque, u el unitario a
    lo largo del tramo y n = (u.y, -u.x) la normal hacia dentro.

    GEMELA de clips() en sam17_case.scad."""
    P = _vertices(p)
    out = []
    for nombre, i0, i1, s in TRAMOS_CLIP:
        A, B = P[i0], P[i1]
        L = math.hypot(B[0] - A[0], B[1] - A[1])
        u = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
        n = (u[1], -u[0])
        pt = lambda a, b: (A[0] + u[0] * a + n[0] * b,
                           A[1] + u[1] * a + n[1] * b)
        s0, s1 = s - p["clip_largo"] / 2, s + p["clip_largo"] / 2
        f = p["clip_fondo"]
        out.append((f"{nombre} {s:g}",
                    [pt(s0, 0.0), pt(s1, 0.0), pt(s1, f), pt(s0, f)],
                    pt(s, p["dist_rosca_ciega"])))
    return out


def _cajas_clip(p: dict[str, float], z0: float, z1: float) -> list[Caja]:
    """Los clips como cuerpos, t_clip contra la cara interior de cada anillo.

    La caja es la AABB del rectangulo, y aqui eso es exacto y no una
    aproximacion: los cuatro tramos que admiten clip -- frente, meseta,
    trasera y suelo -- son los cuatro que corren a plomo o a nivel. Si algun
    dia entra un clip en un tramo inclinado habra que refinarlo con las
    esquinas reales en _solape_riel_exacto(), igual que las placas."""
    out: list[Caja] = []
    for nombre, q, _ in _clips(p):
        xs, ys = [e[0] for e in q], [e[1] for e in q]
        for lado, (za, zb) in enumerate(((z0, z0 + p["t_clip"]),
                                          (z1 - p["t_clip"], z1))):
            out.append((f"clip {nombre} {lado}", min(xs), max(xs),
                        min(ys), max(ys), za, zb))
    return out


def _roscas_clips(p: dict[str, float]
                   ) -> list[tuple[str, tuple[float, float]]]:
    """(nombre, centro) del M4 a rosca ciega de cada clip."""
    return [(f"clip {nombre}", c) for nombre, _, c in _clips(p)]


def _centros_rosca_ciega(p: dict[str, float]
                          ) -> list[tuple[str, tuple[float, float], float]]:
    """(nombre, centro, diametro de broca) de cada rosca ciega de la cara
    interior del anillo. GEMELA de centros_rosca_ciega() en el .scad; las cruza
    taladros_anillo() releyendo costilla_dorso_2d.dxf.

    TODAS SON M4 y todas caen a dist_rosca_ciega de la silueta: dos por riel
    3U, dos sobre el primer riel 1U, dos por brida de miembro trasero y una
    por clip de retencion.

    LO QUE NO ESTA AQUI, y no por olvido: las seis de la TABLA van en el CANTO
    inferior del anillo, no en el dorso, y un DXF de la cara no sabe dibujar
    un taladro que entra por el canto (van en el pliego, Tarea 5). Y las de la
    bahia y la pestana de la banda del valle no son del anillo: se roscan en
    los 6 mm de la placa del valle (ruling R3)."""
    out = []
    for pl in _placas(p):
        for nm, c in _roscas_placa(p, pl):
            out.append((nm, c, p["d_M4_rosca"]))
    P = _vertices(p)
    cajas = _cajas_miembro(p, P, _centros_rail(p, P), 0.0, 0.0)
    for nm, _, centros, ancla in _bridas(p, cajas):
        if ancla != "anillo":
            continue
        for i, c in enumerate(centros):
            out.append((f"brida {nm} {i}", c, p["d_M4_rosca"]))
    for nm, c in _roscas_clips(p):
        out.append((nm, c, p["d_M4_rosca"]))
    return out


def _distancia_a_silueta(P: list[tuple[float, float]],
                          c: tuple[float, float]) -> float:
    """Distancia del punto al tramo mas cercano de la silueta SIN redondear.

    Es la cota que decide si una rosca ciega cae en la franja. Se mide contra
    el poligono de pts_perfil() y no contra el DXF a proposito: aqui manda el
    modelo, y el DXF lo cruza taladros_anillo() en check_dxf.py."""
    def d_seg(a, b):
        ax, ay = a; bx, by = b; px, py = c
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2)) if L2 else 0.0
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    return min(d_seg(P[i], P[(i + 1) % len(P)]) for i in range(len(P)))


def guarda_anclajes(p: dict[str, float]) -> None:
    """Cada anclaje asienta en la franja del anillo, y cada tornillo tiene
    material alrededor en LAS DOS piezas que une.

    La cabeza del M4 del riel va del lado del anillo (el tornillo entra en el
    riel por su eje) y debajo de la placa, a z < t_anillo, hay acrilico hasta
    rehundido + t_cheek + tolerancia + junta. Por eso la placa mide 6 y no 4
    (plan, R1).

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
    tol = 0.4 + 0.1 * p["t_cheek"]
    techo_pmma = p["rehundido_acrilico"] + p["t_cheek"] + tol + p["t_junta_asiento"]
    assert techo_pmma <= p["t_anillo"], (
        f"el acrilico llega a z={techo_pmma:.2f} y la cara interior del anillo "
        f"esta en {p['t_anillo']:g}: el PMMA asoma por detras del anillo")
    # 2.2 es el alto de la cabeza del boton ISO 7380 M4; lo que el modelo fresa
    # es prof_cajeado_riel, y se LEE del parametro en vez de repetir aqui el
    # 2.5 a mano -- era la segunda copia del mismo numero, y la copia se
    # desincroniza al primer cambio.
    cabeza = 2.2
    assert p["prof_cajeado_riel"] >= cabeza, (
        f"el cajeado mide {p['prof_cajeado_riel']:g} y la cabeza del boton ISO "
        f"7380 M4 mide {cabeza:g} de alto: asomaria y pinzaria el acrilico")
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
    # EL CAJEADO DEL RIEL contra el poligono REAL de su placa, chaflan incluido.
    peor_eje = (float("inf"), "")
    for pl in _placas(p):
        q = _esquinas_placa(pl)
        agujeros = ([(f"cajeado de riel de '{pl[0]}'", e[1]) for e in pl[8]]
                    + [(f"rosca '{nm}'", c) for nm, c in _roscas_placa(p, pl)])
        for etiqueta, c in agujeros:
            dist = _dist_al_poligono(q, c)
            peor_eje = min(peor_eje,
                           (dist, f"{etiqueta} @ ({c[0]:.1f}, {c[1]:.1f})"))
            assert dist >= minimo, (
                f"el {etiqueta} en ({c[0]:.2f}, {c[1]:.2f}) cae a {dist:.2f} mm "
                f"del canto de su placa y se exigen {minimo:.2f} (1.5 D del "
                f"paso M4). Detras de un cajeado de {p['d_cajeado_riel']:g} eso "
                f"deja {dist - p['d_cajeado_riel'] / 2:.2f} mm de pared")
    # LA BRIDA CONTRA SU PROPIO CANTO, que no es la silueta. La del miembro
    # ALTO acaba t_costilla por debajo del canto del anillo -- ahi va la meseta,
    # que es el otro ala del mismo blank --, asi que su margen real es
    # dist_rosca_ciega - t_costilla. Es el caso que puso esa cota en 8.5, y
    # hasta hoy la unica comprobacion suponia que la brida llegaba al canto.
    cajas = _cajas_miembro(p, P, _centros_rail(p, P), 0.0, 0.0)
    peor_brida = (float("inf"), "")
    for nm, (x0, x1, y0, y1), agujeros, _ in _bridas(p, cajas):
        q = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for c in agujeros:
            dist = _dist_al_poligono(q, c)
            peor_brida = min(peor_brida, (dist, nm))
            assert dist >= minimo, (
                f"el M4 de la brida de '{nm}' en ({c[0]:.2f}, {c[1]:.2f}) cae a "
                f"{dist:.2f} mm del canto de la propia brida y se exigen "
                f"{minimo:.2f}. Ojo: el canto de la brida NO es la silueta -- la "
                f"del miembro alto acaba {p['t_costilla']:g} mm mas aca, que es "
                f"donde empieza la meseta")
    # EL CLIP CONTRA SU PROPIO CANTO. Por construccion su M4 cae a
    # clip_largo/2 de las puntas y a dist_rosca_ciega del canto que apoya en la
    # silueta, o sea holgado; se comprueba igual porque los dos numeros son
    # parametros y el dia que alguien acorte el clip para que quepa en un tramo
    # estrecho, el agujero se sale por el canto sin que ninguna otra puerta lo
    # vea.
    for nm, q, c in _clips(p):
        dist = _dist_al_poligono(q, c)
        assert dist >= minimo, (
            f"el M4 del clip '{nm}' en ({c[0]:.2f}, {c[1]:.2f}) cae a "
            f"{dist:.2f} mm del canto del propio clip y se exigen "
            f"{minimo:.2f} (1.5 D del paso M4). Es clip_largo/2 = "
            f"{p['clip_largo'] / 2:g} contra dist_rosca_ciega = "
            f"{p['dist_rosca_ciega']:g}: manda el menor de los dos")
    # EL M3 DE LA PESTANA de la banda del valle se rosca en la PLACA del valle
    # y no en el anillo: en la franja no cabe (su M3 cae a pv_a por debajo del
    # plano del valle y la franja solo admite hasta franja - 1.5 D de broca).
    valle = next(pl for pl in _placas(p) if pl[0] == "valle")
    m3 = _m3_pestana(p)
    d_m3 = _dist_al_poligono(_esquinas_placa(valle), m3)
    assert d_m3 >= 1.5 * p["d_M3_paso"], (
        f"el M3 de la pestana de la banda cae en ({m3[0]:.2f}, {m3[1]:.2f}), a "
        f"{d_m3:.2f} mm del canto de la placa del valle, y se exigen "
        f"{1.5 * p['d_M3_paso']:.2f}. Esa rosca va EN la placa (6 mm de "
        f"pletina), no en el anillo: en la franja de {franja:g} no cabe")
    # LA TABLA va al CANTO inferior del anillo y no al dorso: su M5 se centra
    # en los t_anillo de canto y necesita 1.5 D de broca a cada cara.
    assert p["t_anillo"] / 2 >= 1.5 * p["d_M5_rosca"], (
        f"el M5 de la tabla se rosca al medio del CANTO inferior del anillo, o "
        f"sea a {p['t_anillo'] / 2:.2f} mm de cada cara, y una broca de "
        f"{p['d_M5_rosca']:g} pide {1.5 * p['d_M5_rosca']:.2f}: ese canto no da "
        f"para roscarlo sin reventar una cara")
    print(f"anclajes: {len(centros)} roscas ciegas M4 por anillo en la franja "
          f"de {franja:g} (a {p['dist_rosca_ciega']:g} de la silueta, {canto:.2f} "
          f"de sobra de canto); placas de {p['t_placa']:g} con la cabeza dentro "
          f"(PMMA hasta z={techo_pmma:.2f})")
    print(f"  el agujero de placa mas justo es el {peor_eje[1]} a "
          f"{peor_eje[0]:.2f} del canto; el M4 de brida mas justo, '{peor_brida[1]}' a "
          f"{peor_brida[0]:.2f} (minimo {minimo:.2f}); el M3 de la pestana a "
          f"{d_m3:.2f} del canto de la placa del valle")


def _m3_pestana(p: dict[str, float]) -> tuple[float, float]:
    """Centro del M3 de la pestana de la banda del valle, en el plano del
    perfil. GEMELO del agujero que tapa_valle_2d() dibuja en el desarrollo y
    del que placa_riel() rosca en la placa del valle: x centrado en los 3 D
    finales del vuelo delantero, y a pv_a por debajo de la cara de arriba."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    bahia = _envolvente_bahia(_cajas_miembro(p, P, cr, 0.0, 0.0))
    return (_pv_x(p, {"bahia": bahia}), P[3][1] - _pv(p)["a"])


def _anclajes_miembro(p: dict[str, float], cajas: dict[str, Caja]
                       ) -> dict[tuple[str, str], tuple[float, float]]:
    """Lineas de tornillo sobre las caras reales de los tres miembros.

    La bahia se consume por sus dos alas: usar su envolvente pondria anclajes
    sobre el aire central que precisamente no debe entrar en las colisiones.
    """
    bajo, alto = (cajas[n] for n in ("trasero bajo", "trasero alto"))
    ala_del = cajas["bahia ala delantera"]
    ala_tras = cajas["bahia ala trasera"]
    t = p["t_costilla"]
    return {
        ("trasero bajo", "base"): ((bajo[1] + bajo[2]) / 2,
                                     (bajo[3] + bajo[4]) / 2),
        ("trasero alto", "remate"): (alto[2] - t / 2,
                                       alto[4] - p["marco_sup"]
                                       - p["canal_ancho"] / 2),
        ("bahia", "delantera"): ((ala_del[1] + ala_del[2]) / 2,
                                    (ala_del[3] + ala_del[4]) / 2),
        ("bahia", "trasera"): ((ala_tras[1] + ala_tras[2]) / 2,
                                 (ala_tras[3] + ala_tras[4]) / 2),
    }


def _caras_miembro(p: dict[str, float], cajas: dict[str, Caja]) -> list[Caja]:
    """Cajas de las caras de chapa, sin rellenar el vacio de cada plegado."""
    t = p["t_costilla"]
    bajo, alto = (cajas[n] for n in ("trasero bajo", "trasero alto"))
    z0, z1 = bajo[5], bajo[6]
    y_meseta = alto[4] - p["marco_sup"]
    return [
        ("trasero bajo", bajo[2] - t, bajo[2], bajo[3], bajo[4], z0, z1),
        ("trasero bajo", bajo[1], bajo[2], bajo[3], bajo[3] + t, z0, z1),
        ("trasero bajo", bajo[1], bajo[2], bajo[4] - t, bajo[4], z0, z1),
        ("trasero alto", alto[2] - t, alto[2], alto[3], y_meseta, z0, z1),
        # LA MESETA MIDE prof_sup, NO canal_fondo. La caja envolvente del
        # miembro se dibuja con el ala CORTA (20) porque es la seccion que la
        # puerta reclama -- se cobra el lado debil del canal --, pero la cara
        # fisica de arriba vuela prof_sup (37) hacia delante: es la tapa del
        # remate. Modelarla con 20 subestima la pieza 17 mm, y una caja corta
        # no da holgura: ESCONDE choques. Lo canto el delegado al terminar la
        # tarea, y comprobo aparte que con los 37 completos las dos tapas
        # siguen abriendo 180.0 grados.
        ("trasero alto", alto[2] - p["prof_sup"], alto[2],
         y_meseta, alto[4], z0, z1),
        ("trasero alto", alto[2] - p["canal_fondo"], alto[2],
         alto[3], alto[3] + t, z0, z1),
        *(cajas[n] for n in CAJAS_BAHIA),
    ]


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
    """
    return perfil(p)["ancho_util"] - 2 * p["hol_piel"]


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
    # LAS DOS ALAS DE LA BAHIA SE QUEDAN t_placa CORTAS POR PUNTA (ruling R3):
    # en su boca la franja del anillo la ocupa la placa de la fila 1U, y las
    # alas la tienen justo delante. Mueren contra ella y cada una dobla su
    # lengueta encima.
    #   EL SUELO NO. Corre 62 mm por debajo del valle, o sea muy lejos de la
    #   franja y de la placa, y ahi no hay nada entre el y el anillo: cruza
    #   ancho_util entero, que ademas es lo que mantiene su reticula alineada
    #   con la de los otros dos miembros (la mira taladros_reticula()).
    for nm in ("bahia ala delantera", "bahia ala trasera"):
        c = miembros[nm]
        miembros[nm] = c[:5] + (z0 + p["t_placa"], z1 - p["t_placa"])
    bahia = _envolvente_bahia(miembros)
    hx_1u, hy_1u = _he_er(p, 90.0)
    for i, c in enumerate(_centros_rail_1u(p, P, bahia)):
        railes.append((f"fila 1U {i}", c[0] - hx_1u, c[0] + hx_1u,
                       c[1] - hy_1u, c[1] + hy_1u,
                       z0 + p["t_placa"], z1 - p["t_placa"]))
    railes.extend(miembros.values())
    # LAS PLACAS Y LAS BRIDAS SON CUERPOS y van en `railes`, que es la lista
    # que solapes() cruza contra todo. Sin esto son dibujo: el modelo las
    # ensena en el render y ninguna puerta comprueba que quepan en el rincon
    # del valle, que es donde de verdad se pelean.
    railes.extend(_cajas_placa(p, z0, z1))
    railes.extend(_cajas_brida(p, miembros, z0, z1))
    # LOS CLIPS TAMBIEN SON CUERPOS, y en esta lista es donde se pelean: viven
    # en la misma franja de 14 mm que las bridas y a la misma altura que el
    # canto de la piel trasera, o sea entre las dos piezas con las que de
    # verdad pueden chocar. Sin esto el clip se dibujaria encima de ellas.
    railes.extend(_cajas_clip(p, z0, z1))
    anclajes = _anclajes_miembro(p, miembros)

    planchas: list[Caja] = []
    filas: list[Fila] = []
    # bandeja_base: LA TABLA. Cambio de sitio y de material el 2026-08-27 y es
    # el cambio mas grande que ha tenido esta pieza.
    #
    # Fue plancha de acrilico DENTRO del case (y = 0 a t_base) desde el
    # 2026-08-17, con los dos largueros montados encima, y su canto delantero
    # valio 8.46 mm de alto de aparato en su ultima vuelta. Ahora es una TABLA DE
    # MADERA MACIZA BAJO EL MARCO: ocupa y = -t_base .. 0, su cara de arriba ES
    # el suelo interior y su canto sobresale vuelo_zocalo por los cuatro lados.
    # Es la misma pieza que el "zocalo" de la spec 9, que hasta hoy eran dos.
    #
    # LO QUE ESO DESHACE, y por eso el modelo se simplifica en vez de crecer:
    #   - No hay voladizo. La plancha volaba 271.45 mm desde `base trasera` y
    #     pedia 10 mm de aluminio. Ahora las dos costillas se apoyan ENCIMA de
    #     la tabla y las cuatro paticas van debajo, casi en la misma vertical:
    #     el peso del case va de costilla a pata sin cruzar el vano.
    #   - No hay fila de M3 a un larguero. La tabla no cuelga de nada; el marco
    #     se le apoya. Su fijacion es a las dos costillas y va con AGUJERO
    #     ALARGADO, que es cosa de guarda_zocalo() y no de apoyo().
    #   - alto_frontal se suelta del espesor del suelo: el riel del frente solo
    #     tiene que librar y=0.
    v = p["vuelo_zocalo"]
    planchas.append(("bandeja_base",
                     -v, fondo(p) + v,
                     -p["t_base"], 0.0,
                     -v, p["ancho_total"] + v))
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
    # -- ya lo hace el del valle a la MISMA altura. Lo que costo se mide en
    # guarda_costado(), en check_dxf.py.
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
    x1_tv = bahia[1]
    planchas.append(("tapa_valle", x0_tv, x1_tv,
                     P[3][1] - t_acr, P[3][1], z0_tv, z1_tv))
    # LAS DOS PESTANAS de la tapa, dobladas hacia abajo contra la costilla.
    # Van en `railes` y no en `planchas` a proposito: es la lista que solapes()
    # cruza contra todo, y una pestana que se echa encima del larguero del valle
    # o del riel de abajo no la caza nadie mas. (Y `planchas` la recorre
    # _sobres() para sacar envolventes de DXF, que aqui no aplica.)
    x0_pv, x1_pv = x1_tv - 3 * p["d_M3_paso"], x1_tv
    pv_x = _pv_x(p, {"bahia": bahia})
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
    # piel_trasera: UNA sola plancha desde el 2026-08-21. Fueron dos, partidas
    # a la altura del entrepiso porque cada una se atornillaba a los dos
    # largueros de su piso; muerta esa bandeja la frontera dejo de existir. Va
    # en t_piel (8) y declara DOS filas, una por larguero trasero -- las de los
    # tres largueros de en medio se fueron con ellos el 2026-08-21.
    # Canto de abajo en el PLANO DEL SUELO (y=0), el mismo datum de la
    # bandeja de base. Estuvo en ce[1][1] - 15 y dejaba 3 mm de rebaje
    # corrido bajo la trasera -- ver guarda_piso(), assert 4.
    y0_pt = 0.0
    # LA TRASERA LLEGA AL PICO desde el 2026-08-27. Se quedaba marco_sup por
    # debajo porque la meseta era una plancha que se le montaba ENCIMA. Ahora la
    # meseta es el ala del miembro alto y acaba en la cara trasera del miembro
    # (300.94), asi que sobre la trasera no hay nada: si no subiera, quedaria un
    # hueco corrido de 8 x 3 mm a lo largo del canto superior trasero -- por ahi
    # entra polvo y se ve.
    alto_pt = P[5][1] - y0_pt
    # LA TRASERA SE EMPOTRA ENTRE LOS DOS ANILLOS, y desde el 2026-08-28 eso ya
    # no es lo mismo que z0/z1: la cara interior del anillo esta en t_anillo y
    # z0/z1 siguen en la cara interior del apilado viejo (chapa + acrilico)
    # hasta que la Tarea 2 los mueva. Medirla aqui con z0/z1 la hacia 9 mm mas
    # ancha que su propio DXF -- lo canto el sobre de check_dxf, que es justo
    # para lo que existe.
    #
    # ESTA CAJA ES LA GEMELA DE piel_trasera() EN EL .scad EN ANCHO Y EN
    # POSICION, y las dos cosas importan: el ancho es trasera_au()
    # (ancho_util - 2*hol_piel) y el arranque es t_anillo + hol_piel, o sea la
    # cara interior del anillo. Centrada sobre ancho_total da lo mismo escrito
    # de otra forma, y asi no hay dos maneras de decir donde empieza.
    au = _trasera_au(p)
    z_pt0, z_pt1 = (ancho_total - au) / 2, (ancho_total + au) / 2
    planchas.append(("piel_trasera", P[6][0] - p["t_piel"], P[6][0],
                     y0_pt, y0_pt + alto_pt, z_pt0, z_pt1))
    filas += [("piel_trasera", "base", "y",
               anclajes[("trasero bajo", "base")][1], "trasero bajo"),
              ("piel_trasera", "remate", "y",
               anclajes[("trasero alto", "remate")][1], "trasero alto")]
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
    hay_placa = a[0].startswith("placa ") or b[0].startswith("placa ")
    if not ((hay_inclinado and hay_pestana) or hay_placa):
        return True
    P = _vertices(p)
    cr = _centros_rail(p, P)
    datos = {nm: (c, p[ang])
             for nm, c, ang in zip(NOMBRES_CR, cr, ANGS_CR)}
    # las cajas llevan el lado en el nombre ("placa valle 0"); la geometria
    # es la misma para los dos, asi que se busca por el nombre sin lado
    placas = {f"placa {pl[0]}": pl for pl in _placas(p)}

    def poligonos(c: Caja) -> list[list[tuple[float, float]]]:
        raiz = c[0].rsplit(" ", 1)[0]
        if raiz in placas:
            return [_esquinas_placa(placas[raiz])]
        if c[0] in datos:
            centro, ang = datos[c[0]]
            q = _esquinas_er(p, centro, ang)
            return [[q[i] for i in (0, 1, 3, 2)]]
        if c[0].startswith("pestana valle"):
            m = p["muesca_riel_valle"]
            # Rectangulo menos la muesca inferior izquierda, como dos convexos.
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
    # riel de arriba de la tapa <-> pestana: solape de CAJA, cero de solape real.
    # Los dos van girados 45 con la cara y sobre ELLA se TOCAN a tope, sin
    # penetrarse: la pestana apoya en la cara de arriba del riel, que es de donde
    # cuelga su fijacion. Dos rectangulos girados que comparten una arista tienen
    # cajas que se pisan de largo -- de ahi la tolerancia gorda. guarda_tapa()
    # hace la cuenta exacta sobre la cara y exige que la junta valga CERO.
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
    miembros = _cajas_miembro(p, P, cr, 0.0, 0.0)
    esqueleto = _anclajes_miembro(p, miembros)
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
        if rail_decl == "bahia":
            # Cada fila apoya en SU ala. La envolvente total serviria para la
            # distancia exterior, pero esconderia si una fila cae sobre aire.
            miembro = esqueleto.get(f"bahia ala {fila}")
        else:
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
    P = _vertices(p)
    cr = _centros_rail(p, P)
    esqueleto = _anclajes_miembro(
        p, _cajas_miembro(p, P, cr, 0.0, 0.0))
    casos = (("bahia", "delantera", "x"), ("bahia", "trasera", "x"),
             ("trasero bajo", "base", "y"),
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
    for x, y in ((na, nb), (nb, na)):
        if not x.startswith("brida "):
            continue
        duena = x[len("brida "):].rsplit(" ", 1)[0]
        if y == duena or (duena in CAJAS_BAHIA and y in CAJAS_BAHIA):
            return True
    return False


def solapes(p: dict[str, float]) -> list[str]:
    """Seis rieles, tres miembros, tres placas, ocho bridas, dos pestanas y
    tres planchas: ningun par se pisa en 3D, salvo los
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
            # Suelo y alas son caras de UNA MISMA bandeja y se intersectan en
            # los dos dobleces. No son dos piezas chocando entre si.
            if a[0] in CAJAS_BAHIA and b[0] in CAJAS_BAHIA:
                continue
            if _misma_chapa(a[0], b[0]):
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


def guarda_parametros_vivos(p: dict[str, float]) -> None:
    """Ningun parametro promete una capacidad que el codigo no tiene.

    n_bulkheads dice '2 (3 si el vano flexa)' y la spec §11 lo remata: 'si el
    prototipo flexa, n_bulkheads pasa a 3 y se re-exporta'. Pero costados()
    dibuja DOS costados fijos, uno en z=0 y otro en z=ancho_total-t_cheek, sin
    ningun bucle sobre este parametro. Quien lo suba a 3 esperando un refuerzo
    central no recibe nada: ni costado, ni error, ni aviso. El .scad sigue
    sacando dos, y los DXF salen identicos.

    Eso es lo que hace peligroso al parametro muerto -- no que no haga nada,
    sino que PARECE que hace algo. Asi que en vez de borrarlo y perder la
    intencion documentada, la puerta convierte el silencio en un fallo: quien lo
    toque se entera de que hay codigo que escribir.

    Issue #54. Su hermano alto_pie ya se resolvio solo -- cuando entraron las
    paticas dejo de estar huerfano."""
    assert p["n_bulkheads"] == 2, (
        f"n_bulkheads = {p['n_bulkheads']}, y costados() solo sabe dibujar 2. "
        f"El tercer costado central NO esta implementado: subir este numero no "
        f"anade nada, solo lo parece. Para que sirva hay que tocar costados() "
        f"en sam17_case.scad, y de paso decidir como cruzan los largueros por "
        f"el (hoy van de punta a punta) y que agujeros lleva ese costado.")


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
    P = _vertices(p)
    cr = _centros_rail(p, P)
    anclajes = _anclajes_miembro(
        p, _cajas_miembro(p, P, cr, 0.0, 0.0))
    f_base = anclajes[("trasero bajo", "base")][1]
    f_tras = anclajes[("trasero alto", "remate")][1]
    y_bajas = f_base + 0.37 * (f_tras - f_base)
    y0 = f_base + p["valle_espina"] / 2 + p["vent_puente_min"]
    y1 = (y_bajas - p["vent_periodo"] * 0.35 - p["vent_ancho_ranura"] / 2
          - p["vent_separacion"])
    return y0, y1


def _rejilla_entrada(p: dict[str, float]) -> tuple[int, float, float, float]:
    """Las ranuras de ENTRADA, mismas cuentas que rejilla_entrada().

    Devuelve (n, largo, area, y_centroide). El centroide va en coordenadas del
    case porque lo que gobierna el tiro no es solo cuanta area hay sino a que
    ALTURA esta. Esta rejilla vive abajo del todo en la trasera; paso unas horas
    en el suelo (y=4, mas tiro y mas area) y volvio aqui porque en el vuelo de
    la bandeja se transparentaba por el canto inferior."""
    au = _trasera_au(p)
    # y=0: el canto de abajo de la plancha, en el plano del suelo. Da igual
    # para el resultado -- se resta al formar f_base/f_tras y se vuelve a
    # sumar al devolver el centroide, asi que se cancela -- pero tiene que
    # decir lo mismo que el .scad o el dia que deje de cancelarse miente.
    y0_pl = 0.0
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
    ns = [n for n in range(paso, int(n_hp) - paso + 1, paso)
          if abs(n * p["hp"] - x_iec) >= hueco]
    return (len(ns), y1 - y0,
            _area_ranuras(len(ns), y1 - y0, p["vent_ancho_ranura"]),
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
    La salida baja de 12609 a 9943 mm2 y el salto termico sube de 6.6 a 7.1 K
    contra el techo de 15.

    El motivo no es termico sino de lo que hay DETRAS de cada onda, medido
    contra el envolvente de un modulo de fondo_pcb_max:

        triangulo y cuadrada  y =  99.47   171 mm de aire (piso de abajo)
        sierra                y = 180.94    32 mm: dorso de los modulos de
                                            arriba -- ranura que ensena cable
                                            y deja entrar polvo

    LO QUE ESTE NUMERO NO DICE, y hay que decirlo: potencia_disipada son SOLO
    los reguladores del PSU. La disipacion de los modulos no esta en ningun
    presupuesto de este repo, asi que el 7.1 K describe el camino del PSU --
    que sale por el valle y por estas dos ondas, las dos por debajo del
    entrepiso-- y NO la bahia de arriba, que es la que el cajeado sella."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    anclajes = _anclajes_miembro(
        p, _cajas_miembro(p, P, cr, 0.0, 0.0))
    au = _trasera_au(p)
    # y=0: el canto de abajo de la plancha, en el plano del suelo. Da igual
    # para el resultado -- se resta al formar f_base/f_tras y se vuelve a
    # sumar al devolver el centroide, asi que se cancela -- pero tiene que
    # decir lo mismo que el .scad o el dia que deje de cancelarse miente.
    y0_pl = 0.0
    f_base = anclajes[("trasero bajo", "base")][1] - y0_pl
    f_tras = anclajes[("trasero alto", "remate")][1] - y0_pl
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
    efectiva y las perdidas del trafo son supuestos, y por eso el techo va en 15
    K y no pegado al resultado. Sirve para ordenes de magnitud y para que un
    cambio de geometria no empeore el tiro sin que nadie se entere."""
    n_ent, largo_ent, a_ent, y_ent = _rejilla_entrada(p)
    n_mes, largo_mes, a_mes, y_mes = _rejilla_valle(p)
    a_ond, y_ond = _ondas_trasera(p)
    a_sal = a_mes + a_ond
    y_sal = (a_mes * y_mes + a_ond * y_ond) / a_sal

    assert largo_ent >= 4 * p["vent_ancho_ranura"], (
        f"la rejilla de entrada mide {largo_ent:.1f} mm de largo con ranuras "
        f"de {p['vent_ancho_ranura']:.0f}: deja de leerse como campo y pasa a "
        f"rayitas (es la misma cuenta que recorto la espina del valle)")

    a_ef = 1.0 / math.sqrt(1 / a_ent ** 2 + 1 / a_sal ** 2)
    h = (y_sal - y_ent) / 1000.0
    assert h > 0, (
        f"la salida de aire ({y_sal:.1f} mm) no queda por encima de la entrada "
        f"({y_ent:.1f} mm): sin desnivel no hay tiro y la conveccion natural no "
        f"arranca")
    k = (RHO_AIRE * CP_AIRE * CD_TIRO * a_ef * 1e-6
         * math.sqrt(2 * G * h / T_AMB))
    dt = (p["potencia_disipada"] / k) ** (2.0 / 3.0)
    assert dt <= p["salto_termico_max"] + 1e-9, (
        f"el case sube {dt:.1f} K sobre ambiente con {p['potencia_disipada']:.2f} "
        f"W y el techo son {p['salto_termico_max']:.0f}. Entrada {a_ent:.0f} mm2 "
        f"a y={y_ent:.0f}, salida {a_sal:.0f} a y={y_sal:.0f}, tiro {h*1000:.0f} "
        f"mm. Sube el area de la rejilla o bajala mas (el tiro va con la raiz de "
        f"la altura, el area va lineal)")

    print(f"aire: entrada {a_ent:.0f} mm2 en {n_ent} ranuras de "
          f"{largo_ent:.1f} x {p['vent_ancho_ranura']:.0f} (trasera, y={y_ent:.0f})")
    print(f"  salida {a_sal:.0f} mm2 = {a_mes:.0f} de la meseta "
          f"({n_mes} ranuras de {largo_mes:.1f} x "
          f"{p['vent_ancho_ranura']:.0f}, y={y_mes:.0f}) + "
          f"{a_ond:.0f} de las DOS ondas abiertas (el relieve KONDOR es cajeado "
          f"ciego y no ventila), centroide y={y_sal:.0f}")
    print(f"  tiro {h*1000:.0f} mm, area efectiva {a_ef:.0f} mm2 -> "
          f"{dt:.1f} K sobre ambiente con {p['potencia_disipada']:.2f} W "
          f"(techo {p['salto_termico_max']:.0f}). SUPUESTO: C_D={CD_TIRO}, "
          f"sin perdidas de trafo")


# Coeficiente par-precarga de un tornillo de acero SECO. 0.2 es valor de
# manual. Con la rosca engrasada baja a ~0.15, o sea que el MISMO par mete un
# 30% mas de precarga -- y sobre acrilico eso fisura. Los M3 van secos, y va
# dicho en el pliego y en el orden de ensamblaje, no solo aqui.
K_PAR = 0.20
# Umbral de fluencia del PMMA. SUPUESTO DECLARADO (#106): nadie lo ha medido
# sobre el acrilico que se va a comprar. Vive aqui y no dentro de una guarda
# porque tiene DOS clientes -- guarda_apriete() y guarda_costado(), que esta en
# check_dxf.py e importa este modulo. Copiarlo seria el patron del `- 15`
# copiado en cinco sitios que ya costo una tanda en este repo.
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


def guarda_apriete(p: dict[str, float]) -> None:
    """El par de los M3 sale de la ARANDELA, no del tornillo.

    Hasta el 2026-08-24 la instruccion era "apretar hasta marcar, NO hasta
    fisurar" (README, procedimiento del cupon) y la spec §11 admitia que "el
    par maximo antes de fisura no esta medido". Veinte tornillos VISIBLES
    apretados a tacto sobre acrilico son veinte puntos de craquelado.

    Lo que decide si el PMMA craquela no es el tornillo sino cuanta area de
    acrilico reparte su precarga. Precedente en el propio BOM: con arandela
    M4 normal (d9) los ejes de giro daban 16.3 MPa y "el PMMA fluye en
    semanas"; con d16 dan 4.3 y aguantan. Aqui se hace la cuenta al reves --
    dada la arandela, cual es el par que no pasa del umbral.

    El segundo assert es el que sorprende: exige un par MINIMO. Un par por
    debajo de 1 N*m no lo da ninguna llave dinamometrica de 1/4", asi que
    volveria a apretarse a tacto, que es lo que este cambio vino a quitar.
    Lo que compra par es subir la arandela, no bajar el apriete.
    """
    area = math.pi * (p["d_arandela"] ** 2 - p["d_M3_paso"] ** 2) / 4
    par_max = K_PAR * (SIGMA_PMMA * area) * 0.003
    sigma = p["par_m3"] / (K_PAR * 0.003 * area)
    assert p["par_m3"] <= par_max, (
        f"par_m3 = {p['par_m3']} N*m con arandela d{p['d_arandela']:g} aplasta "
        f"el acrilico a {sigma:.1f} MPa, y el umbral son {SIGMA_PMMA}. Maximo "
        f"{par_max:.2f} N*m -- o sube la arandela, que es lo que de verdad "
        f"compra par.")
    assert p["par_m3"] >= 1.0, (
        f"par_m3 = {p['par_m3']} N*m: por debajo de 1 N*m no hay llave "
        f"dinamometrica de 1/4\" que lo de, asi que se volveria a apretar a "
        f"tacto. Sube la arandela hasta que el par quepa en una herramienta "
        f"que existe (d16 da {par_max:.2f} si ya la llevas).")
    print(f"apriete: 20 M3 a {p['par_m3']} N*m con arandela d{p['d_arandela']:g} "
          f"-> {sigma:.1f} MPa sobre el acrilico (techo {SIGMA_PMMA}, "
          f"par maximo {par_max:.2f})")


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
    t_min = min(p["t_cheek"], p["t_piel"])
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
# Ancho sobre el que reparte una mano apoyada de canto. Es EL SUPUESTO QUE MAS
# MANDA en esta puerta -- con 50 mm la tension se dobla contra los 100 -- y por
# eso va conservador: el canto de la mano, no la palma abierta.
B_MANO = 50.0


def guarda_valle(p: dict[str, float]) -> None:
    """La banda del vuelo delantero aguanta que alguien se apoye en ella.

    La tapa completa murio al entrar la fila 1U. Queda una banda de 18.30 mm,
    apoyada en el ala delantera de la bahia por su canto trasero: el 100 % de su
    fondo trabaja como un voladizo corto.

    Para carga hacia ABAJO la banda apoya en una LINEA CONTINUA y no sobre los
    dos M3 laterales. Lo que flexa es el VOLADIZO TRANSVERSAL:

        flecha = P L^3 / (3 E I)        sigma = 6 P L / (b t^2)
        I = b t^3 / 12,  L = voladizo,  b = B_MANO

    EN ACRILICO DE 5 ESTO NO PASABA: 22.3 MPa con 200 N repartidos en 50, sobre
    un umbral de 10 (#106), o sea que fluia a 90 N. Era la pieza mas floja del
    case y ademas la unica superficie HORIZONTAL -- donde se apoya quien se
    levanta, no donde se posa la mano al parchear.

    POR QUE NO SE ARREGLO CON ESPESOR NI CON LARGUERO, y conviene que quede
    escrito para que nadie lo reintente:
      - acrilico de 6: BLOQUEADO. La tapa invade el barrido del riel y la fila
        de abajo pasa de abrir 180 grados a 39.5. Lo canta guarda_tapa().
      - larguero de 30 en vez de 20: entra por 0.24 mm, que esta por debajo de
        la tolerancia de la propia extrusion. No es holgura, es suerte.
      - larguero de 40: NO ENTRA. Se pasa 4.76 mm de su ventana, que la fijan
        las esquinas giradas de los dos railes del valle. Lo canta
        guarda_escalon().
    El aluminio resuelve por rigidez especifica en vez de por espesor, y de
    paso DEVUELVE 2 mm de barrido en vez de comerselos."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    x0 = _x_valle(p, P, cr)[0]
    bahia = _envolvente_bahia(_cajas_miembro(p, P, cr, 0.0, 0.0))
    x1 = bahia[1]
    vol = x1 - x0
    t = p["t_valle"]

    I = B_MANO * t ** 3 / 12
    flecha = p["carga_mano"] * vol ** 3 / (3 * E_ALUMINIO * I)
    sigma = 6 * p["carga_mano"] * vol / (B_MANO * t ** 2)
    p_fluye = RP02_ALUMINIO * B_MANO * t ** 2 / (6 * vol)

    assert sigma <= RP02_ALUMINIO, (
        f"la tapa del valle trabaja a {sigma:.1f} MPa con {p['carga_mano']:.0f} N "
        f"repartidos en {B_MANO:.0f} mm, y el limite elastico del aluminio de "
        f"chapa son {RP02_ALUMINIO:.0f}. Vuela {vol:.2f} mm respecto a las "
        f"alas de la bahia: o sube t_valle, o hay que ensanchar el apoyo.")
    assert flecha <= p["flecha_costado_max"], (
        f"la tapa del valle cede {flecha:.2f} mm con {p['carga_mano']:.0f} N y "
        f"el techo son {p['flecha_costado_max']:.2f}. Es la unica cara "
        f"HORIZONTAL del case: la que se hunde bajo la mano se nota mas que "
        f"ninguna.")
    # Al tirar hacia ARRIBA ya no hay cinco M3 repartidos: solo los dos de las
    # pestanas laterales. El vano es la distancia entre sus planos medios y la
    # seccion resistente tiene el fondo de la banda, no B_MANO. Se imprime sin
    # assert porque este caso de carga nunca fue puerta, pero ya no se falsea.
    vano_arr = perfil(p)["ancho_util"] - t
    I_arr = (x1 - x0) * t ** 3 / 12
    f_arr = p["carga_mano"] * vano_arr ** 3 / (48 * E_ALUMINIO * I_arr)
    sigma_arr = 3 * p["carga_mano"] * vano_arr / (2 * (x1 - x0) * t ** 2)
    p_fluye_arr = RP02_ALUMINIO * 2 * (x1 - x0) * t ** 2 / (3 * vano_arr)
    print(f"valle: banda de ALUMINIO t={t:g}, vuela {vol:.2f} mm desde el ala "
          f"delantera de la bahia (100 % del fondo)")
    print(f"  con {p['carga_mano']:.0f} N en {B_MANO:.0f} mm cede {flecha:.3f} mm "
          f"y trabaja a {sigma:.1f} MPa (Rp0.2 {RP02_ALUMINIO:.0f}, fluye a "
          f"{p_fluye:.0f} N)")
    print(f"  levantandola entre los dos M3 laterales: vano {vano_arr:.2f} mm, "
          f"calculo elastico {f_arr:.1f} mm y {sigma_arr:.0f} MPa (fluye a "
          f"{p_fluye_arr:.0f} N; las ranuras no estan descontadas)")


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


def _pv_x(p: dict[str, float], cajas: dict[str, Caja]) -> float:
    """X del M3, centrado en los 3D finales del vuelo delantero."""
    return cajas["bahia"][1] - 1.5 * p["d_M3_paso"]


def bbox_desarrollo_tapa(p: dict[str, float]) -> tuple[float, float]:
    """Envolvente del DESARROLLO de la tapa del valle, no de la pieza doblada.

    Crece 2*vuelo por el ancho: cada punta saca su pestana desplegada por fuera
    del contorno. Derivado y no escrito a mano -- si el .scad y esta cuenta se
    separan, el bbox se sale del sobre y check_dxf se entera."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    x0 = _x_valle(p, P, cr)[0]
    bahia = _envolvente_bahia(_cajas_miembro(p, P, cr, 0.0, 0.0))
    return (_tapa_valle_au(p) + 2 * _pv(p)["vuelo"], bahia[1] - x0)


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
    P = _vertices(p)
    cr = _centros_rail(p, P)
    anclajes = _anclajes_miembro(
        p, _cajas_miembro(p, P, cr, 0.0, 0.0))
    au = _trasera_au(p)
    f_base = anclajes[("trasero bajo", "base")][1]
    lib0, lib1 = _banda_libre_trasera(p)   # la misma que centra la rejilla
    puente = p["vent_puente_min"]

    # 1. cabe de alto en la banda, y deja puente arriba y abajo. Va centrada,
    #    asi que el margen es el mismo por los dos lados -- se comprueba una vez
    #    y se nombran los dos.
    holgura_v = (lib1 - lib0 - p["iec_alto"]) / 2
    assert holgura_v >= puente, (
        f"la ventana de la entrada de red mide {p['iec_alto']:.1f} mm de alto y "
        f"la banda libre entre la fila de M3 y la onda mide {lib1 - lib0:.2f} "
        f"(y={lib0:.2f}..{lib1:.2f}): quedan {holgura_v:.2f} mm de acrilico "
        f"arriba y abajo y el puente minimo son {puente:.0f}. O baja iec_alto, o "
        f"la banda tiene que crecer -- y crecerla mueve vent_separacion, que es "
        f"cota de dibujo, o la fila de M3, que es estructura")

    # 2. el puente contra la ranura mas cercana NO SE ASEVERA, y conviene decir
    #    por que: seria un verde vacio. _rejilla_entrada() se salta columnas con
    #    la condicion |x - x_iec| >= (iec_ancho + vent_ancho_ranura)/2 + puente,
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
    x_iec = au - p["iec_margen_der"] - p["iec_ancho"] / 2
    paso = int(p["valle_paso_hp"])
    n_hp = round(p["largo_riel"] / p["hp"])
    hueco = (p["iec_ancho"] + p["vent_ancho_ranura"]) / 2 + puente
    xs = [n * p["hp"] for n in range(paso, int(n_hp) - paso + 1, paso)
          if abs(n * p["hp"] - x_iec) >= hueco]
    borde = min(abs(x - x_iec) - (p["iec_ancho"] + p["vent_ancho_ranura"]) / 2
                for x in xs)

    # 3. no se arrima al canto derecho de la plancha. Un hueco cerca de un
    #    canto libre en PMMA es el otro sitio donde arranca la fisura.
    assert p["iec_margen_der"] >= puente, (
        f"la ventana de la entrada de red deja {p['iec_margen_der']:.1f} mm "
        f"hasta el canto derecho de la trasera y el minimo son {puente:.0f}")

    print(f"entrada de red: ventana de {p['iec_ancho']:.1f} x {p['iec_alto']:.1f} "
          f"en x={x_iec - p['iec_ancho'] / 2:.2f}..{x_iec + p['iec_ancho'] / 2:.2f}, "
          f"y={lib0 + holgura_v:.2f}..{lib1 - holgura_v:.2f}")
    print(f"  {holgura_v:.2f} mm de puente arriba y abajo, {borde:.2f} contra la "
          f"ranura mas cercana, {p['iec_margen_der']:.1f} al canto derecho")
    print(f"  SIN DERIVAR de la Schurter KM00.1105.11 (hoja typ_KM.pdf p.3: "
          f"recorte 28 x 47, brida 30.5 x 50). Su snap-in agarra chapa de 1 a "
          f"2.5 mm y esta plancha tiene {p['t_piel']:.0f}: aqui NO se encaja")
    print(f"  la sostiene una pieza fija atornillada al miembro trasero bajo, "
          f"{lib0 + holgura_v - (f_base + p['rail'] / 2):.2f} mm mas "
          f"abajo -- sin dibujar todavia (#130)")


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
    print(f"fresado: ranura {p['vent_ancho_ranura']:.1f} y concavo minimo "
          f"{p['radio_valle']:.1f} contra fresa de {p['fresa_d']:.1f} "
          f"(radio {r:.1f}) -- sin cambio de util")




# Inercia de un 2020 ranurado de catalogo. SUPUESTO DECLARADO: cifra de oficio,
# no de hoja de datos. Va aqui y no en params.scad porque es la pieza que se
# JUBILA -- es el liston contra el que se mide su sustituto, no una cota del
# case. Si el proveedor publica la suya y es otra, este numero se cambia y las
# secciones de los miembros se recalculan solas.
I_2020 = 5600.0


def _seccion_canal(w: float, d: float,
                   t: float) -> tuple[float, float, float]:
    """Inercia, area y fibra mas alejada de un canal de cotas exteriores."""
    if d <= t:
        raise ValueError(
            f"canal inexistente: d ({d:g}) debe ser mayor que t ({t:g})")
    extension_ala = d - t
    A_alma, y_alma = w * t, t / 2.0
    A_ala, y_ala = extension_ala * t, t + extension_ala / 2.0
    A = A_alma + 2 * A_ala
    yc = (A_alma * y_alma + 2 * A_ala * y_ala) / A
    I = ((w * t ** 3 / 12 + A_alma * (y_alma - yc) ** 2)
         + 2 * (t * extension_ala ** 3 / 12
                + A_ala * (y_ala - yc) ** 2))
    return I, A, max(yc, d - yc)


def _secciones_miembro(p: dict[str, float]) -> list[tuple[str, float, float]]:
    """Los tres miembros de chapa con su seccion (nombre, w, d).

    LOS TRES NO SON IGUALES, y las dos excepciones van declaradas aqui porque
    cada una es un ruling y no una cota:

    'trasero alto' ES UN CANAL ASIMETRICO. Su ala de arriba es la MESETA del
    remate -- prof_sup, 37 mm -- y la de abajo es un retorno corto de
    canal_fondo. Un ala larga y otra corta.
      Se reclama la CORTA. La puerta compara contra el 2020 con la seccion que
      el canal garantiza en su lado debil, no con la que le regala el ala larga.
      La seccion real es mayor y ese margen no se cobra: es la diferencia entre
      "esta pieza aguanta" y "esta pieza aguanta si nadie acorta la meseta".
      Y el retorno de abajo NO es adorno: un ala libre de 528 mm en chapa de 1.5
      ondula, y ademas seria canto vivo en una pieza vista.

    'bahia' NO ES UN CANAL DE catalogo: es una bandeja, y su seccion sale de su
    propia geometria -- el alto de las alas es bahia_alto y el ancho del suelo lo
    fija la TAPA DEL VALLE, que es quien apoya en esas alas. Sale enormemente mas
    rigida que un 2020 (33.9x), y eso NO es sobredimensionar: es la consecuencia
    de que la pieza tenga que ser tambien pared y tambien canto de apoyo. Es el
    numero que la spec 5.3 dejo escrito como "sin medir".

    Y EL ANCHO DE LA BAHIA SE RULEO MAL LA PRIMERA VEZ. Se puso igual a la
    VENTANA entre los dos rieles del valle (105.94..162.42), que es el hueco
    fisico disponible y parece la respuesta obvia. Pero la tapa del valle acaba
    en 158.42 -- se retira 4 mm del riel de arriba -- asi que con el ala trasera
    en 162.42 la tapa NO LA ALCANZA: apoyaria solo en el ala delantera y volaria
    52.47 mm hacia atras, PEOR que los 23.24 que vuela hoy sobre su barra. El
    ala trasera va donde la tapa pueda pisarla: a ras de su canto. Vuelos
    resultantes: 14.00 delante y 0.00 detras.

    Lo canto el delegado preguntando antes de construirlo, no una puerta."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    x1_tapa = _x_valle(p, P, cr)[1]
    ancho_bahia = x1_tapa - (cr[1][0] + _radio_giro_riel(p) + p["holgura_rail"])
    return [("trasero bajo", p["canal_ancho"], p["canal_fondo"]),
            ("trasero alto", p["canal_ancho"], p["canal_fondo"]),
            ("bahia", ancho_bahia, p["bahia_alto"])]


def _bd_miembro(p: dict[str, float]) -> float:
    """Deduccion de un doblez a 90 para la chapa de los tres miembros."""
    sb = p["radio_doblez_costilla"] + p["t_costilla"]
    ba = math.pi / 2 * (p["radio_doblez_costilla"]
                        + p["k_factor"] * p["t_costilla"])
    return 2 * sb - ba


def bbox_desarrollo_miembro(p: dict[str, float], cual: str) -> tuple[float, float]:
    """Envolvente del blank de cada canal trasero, largo por desarrollo."""
    secciones = {nombre: (w, d) for nombre, w, d in _secciones_miembro(p)}
    if cual not in ("trasero bajo", "trasero alto"):
        raise ValueError(f"miembro sin desarrollo de canal: {cual!r}")
    w, d = secciones[cual]
    ala_superior = p["prof_sup"] if cual == "trasero alto" else d
    desarrollo = d + w + ala_superior - 2 * _bd_miembro(p)
    # EL BLANK CRECE POR LAS DOS BRIDAS desde el 2026-08-28: la lengueta que
    # ata cada punta al anillo sale del mismo recorte, tumbada, y descuenta un
    # BD como cualquier otro doblez.
    largo = (perfil(p)["ancho_util"]
             + 2 * (p["brida_largo"] - _bd_miembro(p)))
    return largo, desarrollo


def bbox_desarrollo_bahia(p: dict[str, float]) -> tuple[float, float]:
    """Envolvente del blank de la bandeja: suelo mas dos alas hacia arriba.

    Con sus dos lenguetas, que aqui no suman lo mismo que en los traseros: la
    bahia acaba t_placa antes del anillo (ruling R3), asi que el doblez cae
    t_placa DENTRO del recorte y la lengueta solo sobresale lo que le queda."""
    secciones = {nombre: (w, d) for nombre, w, d in _secciones_miembro(p)}
    suelo, ala = secciones["bahia"]
    desarrollo = suelo + 2 * ala - 2 * _bd_miembro(p)
    largo = (perfil(p)["ancho_util"]
             + 2 * (p["brida_bahia_vuelo"] - _bd_miembro(p) - p["t_placa"]))
    return largo, desarrollo

def autocomprobacion_canal() -> None:
    """La seccion del canal, a mano, ANTES de escribir la funcion.

    ES EL PATRON QUE SALVO LA COSTILLA el 2026-08-26: la cuenta a mano primero,
    la funcion despues. Aquella vez la aritmetica escrita a mano estaba mal
    (36*4.6875^2 son 791.0156 y no 790.92) y fue la autocomprobacion quien lo
    canto, no la funcion.

    Y ESTA CUENTA YA SE ESCRIBIO MAL UNA VEZ, el mismo 2026-08-27. La primera
    version partia el canal en tres rectangulos -- el alma (t x w) y dos alas
    enteras (d x t) -- y eso CUENTA DOS VECES las dos esquinas donde el alma se
    encuentra con las alas: 2 x 3 x 3 = 18 mm2 de metal que no existe. Inflaba
    el area un 11 % (180 contra 162) y la inercia un 10 % (6935 contra 6279).
    Lo canto el delegado al implementarla, no quien la escribio.

    Convencion: canal en U de cotas EXTERIORES w (perpendicular a la carga) x d
    (en la direccion de la carga), chapa de espesor t. Tres rectangulos que NO
    se solapan: el alma (t de extension en la direccion de la carga, w de ancho)
    y las dos alas, que arrancan DONDE ACABA EL ALMA y miden por tanto (d - t).

    Con w = d = 20 y t = 3, midiendo x desde la cara exterior del alma:
      alma:  extension 3, ancho 20  -> A = 60,  centroide x = 1.5
      alas:  extension 20-3 = 17, ancho 3 -> A = 51 cada una,
             centroide x = 3 + 17/2 = 11.5
      A total = 60 + 2*51 = 162
      xb = (60*1.5 + 102*11.5) / 162 = (90 + 1173) / 162 = 1263/162 = 7.796296
      I = [20*3^3/12 + 60*(7.7962963-1.5)^2]
        + 2*[3*17^3/12 + 51*(11.5-7.7962963)^2]
        = [45 + 60*39.643347] + 2*[1228.25 + 51*13.717421]
        = [45 + 2378.600823] + 2*[1228.25 + 699.588477]
        = 2423.600823 + 3855.676954
        = 6279.277778

    (La primera vez que se escribio esta cuenta a mano salio 6279.258: un
    desliz de 0.02 que la funcion canto en cuanto se apreto la tolerancia. Es
    exactamente lo que le paso a autocomprobacion_L el 2026-08-26 con
    36*4.6875^2. La cuenta a mano se equivoca; por eso se escribe entera.)
      ymax = max(xb, d - xb) = max(7.796296, 12.203704) = 12.203704

    Sigue ganandole al 2020 (5600), pero por 1.12x y no por 1.24x.
    """
    I, A, ymax = _seccion_canal(20.0, 20.0, 3.0)
    assert abs(A - 162.0) < 1e-6, f"area {A:.6f}, a mano 162"
    assert abs(I - 6279.277778) < 1e-4, f"I = {I:.6f}, a mano 6279.277778"
    assert abs(ymax - 12.203704) < 1e-4, f"ymax {ymax:.6f}, a mano 12.203704"


def guarda_miembros(p: dict[str, float]) -> None:
    """Cada miembro de chapa le gana al 2020 que sustituye.

    LA COMPARACION ES A IGUAL ENVOLVENTE, que es la unica honesta: un canal mas
    profundo gana siempre y eso no dice nada de la chapa, solo de la
    profundidad. Si un miembro necesita mas fondo que 20, el que sube es su
    parametro y esta puerta lo sigue midiendo contra el mismo 2020.

    POR QUE SE PUEDEN IR LOS 2020, en una linea: no estaban ahi por rigidez,
    estaban ahi porque era lo que se compra. Un canal doblado de la misma
    envolvente da mas inercia con el 39 % de la seccion. Lo que si se pierde es
    la ranura en T, y eso lo devuelve guarda_reticula() (spec 6)."""
    au = perfil(p)["ancho_util"]
    for nombre, w, d in _secciones_miembro(p):
        I, A, _ = _seccion_canal(w, d, p["t_costilla"])
        assert I >= I_2020, (
            f"el miembro '{nombre}' es un canal {w:g}x{d:g} en chapa de "
            f"{p['t_costilla']:g} y da {I:.0f} mm4 contra los {I_2020:.0f} del "
            f"2020 que sustituye. Un canal de 20x20 ya da 6279: si este no "
            f"llega, la seccion esta mal puesta")
        print(f"  miembro '{nombre}': canal {w:g}x{d:g} -> I={I:.0f} mm4 "
              f"({I / I_2020:.2f}x el 2020), {A * au * 2.70e-6:.3f} kg")


# Material minimo alrededor de un taladro, en diametros de canto a centro. Es
# el mismo criterio que check_dxf.py aplica a los cantos de las piezas planas;
# vive aqui porque desde el 2026-08-27 tambien lo necesita el ESQUELETO, y no en
# el canto de un contorno sino en el espesor de la chapa que recibe el tornillo.
AGARRE_MIN_D = 1.5


def guarda_agarre(p: dict[str, float]) -> None:
    """Todo tornillo muerde material MAS ANCHO que su propio agujero.

    ESTA PUERTA NACE DE UN DEFECTO QUE NINGUNA OTRA VIO. El 2026-08-26 murieron
    los perfiles 2020 y la tapa del valle paso a apoyar en las dos alas de la
    bahia. Sus diez M3 quedaron centrados en el ESPESOR del ala: agujero de paso
    de 3.40 sobre una chapa de 3.00. El agujero es mas ancho que el canto que
    tiene que morder -- no es una junta, es una ranura abierta por las dos caras
    -- y el aparato entero paso las dos puertas en verde durante un dia.

    Por que no lo vio nadie: alineacion() comprueba que la fila caiga en la
    centerline de su miembro, y caia; apoyo() comprueba que las filas de una
    placa apoyen a la misma distancia, y apoyaban; solapes() comprueba
    disyuncion, y dos chapas que se tocan en un tornillo no solapan. Las tres
    miraban DONDE cae el tornillo. Ninguna miraba EN QUE cae.

    El 2020 no tenia este modo de fallo porque su ranura en T corria por una
    cara de 20 mm: cualquier tornillo encontraba material. Un canal de chapa de
    3 solo lo encuentra si entra por la CARA, nunca por el canto.

    El criterio: la seccion del miembro medida sobre el eje que recorre la placa
    tiene que valer al menos AGARRE_MIN_D x D a cada lado del centro, o sea 3 D
    de ancho total. Es el mismo numero que check_dxf.py exige a los cantos, y
    por la misma razon fisica: menos que eso y el material se rasga."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    cajas = _cajas_miembro(p, P, cr, 0.0, 0.0)
    _, _, filas = _cajas_solidas(p)
    d = p["d_M3_paso"]
    minimo = 2 * AGARRE_MIN_D * d
    peor, peor_nm = float("inf"), ""
    for placa, fila, eje, coord, miembro in filas:
        i = 1 if eje == "x" else 3
        # de todas las sub-cajas de ese miembro, la que el tornillo atraviesa
        propias = [(nm, c) for nm, c in cajas.items() if nm.startswith(miembro)]
        assert propias, f"la fila [{placa}/{fila}] declara '{miembro}', que no tiene cajas"
        nm, caja = min(propias,
                       key=lambda t: abs((t[1][i] + t[1][i + 1]) / 2 - coord))
        ancho = caja[i + 1] - caja[i]
        if ancho < peor:
            peor, peor_nm = ancho, f"{placa}/{fila} en '{nm}'"
        assert ancho >= minimo, (
            f"el tornillo de [{placa}/{fila}] entra en '{nm}', que sobre el eje "
            f"{eje} mide {ancho:.2f} mm. Su agujero de paso mide {d:.2f} y se "
            f"exigen {minimo:.2f} ({2 * AGARRE_MIN_D} D). "
            + (f"El agujero es MAS ANCHO que el material: eso no es una junta, "
               f"es una ranura abierta por las dos caras. " if ancho < d else "")
            + f"Un tornillo entra por la CARA de una chapa, nunca por su canto")
    print(f"agarre: {len(filas)} filas revisadas, la mas justa es {peor_nm} con "
          f"{peor:.2f} mm de material (minimo {minimo:.2f} = {2 * AGARRE_MIN_D} D)")


# Separacion entre centros de taladro que Intellijel PUBLICA para su 1U, en mm.
# FUENTE: intellijel.com/support/1u-technical-specifications/ (consultada el
# 2026-08-27). El diagrama de esa pagina vive dentro de una imagen y no se pudo
# leer con la maquina: la cifra viene del hilo tecnico de MOD WIGGLER y de la
# ficha del formato. PENDIENTE DE CONFIRMAR CONTRA EL DIAGRAMA.
#
# Vive aqui y no en params.scad a proposito: NO es una cota nuestra que se pueda
# tocar. Es el numero de otro, y su unico trabajo es discutir con el nuestro.
S_1U_INTELLIJEL = 33.65


def guarda_fila_1u(p: dict[str, float]) -> None:
    """La fila del valle es un 1U de Intellijel de verdad, no un parecido.

    EL VALLE DEJA DE SER TAPA. Fue una plancha ranurada atornillada a un larguero
    2020; al morir el 2020 quedo atornillada al CANTO de las alas de la bahia, y
    eso no es una junta (lo canta guarda_agarre()). En vez de parchear ese
    apoyo, la cara pasa a ser una TERCERA FILA DE MODULOS: los railes se
    atornillan a la CARA del ala -- 60 mm de chapa -- y el defecto desaparece en
    lugar de arreglarse.

    POR QUE UN ESTANDAR Y NO UN FORMATO PROPIO. Se estudio hacer el nuestro y se
    descarto: a la altura que la boca permite, un formato KONDOR habria medido
    lo mismo que uno de mercado y habria costado dibujar cada tile a mano. El
    aparato se vende entero, pero el dueño puede querer meter una utilidad
    comprada, y a igual tamaño el catalogo sale gratis.

    LAS DOS CIFRAS TIENEN QUE CUADRAR SOLAS, y esa es la comprobacion que de
    verdad vale. La regla del repo para 3U -- S = H - 2*inset_er, con inset_er
    de 3.0 sacado de Doepfer -- aplicada al panel de Intellijel tiene que dar
    EXACTAMENTE la separacion de taladro que Intellijel publica. Si diera otra
    cosa, o su panel no mide lo que creemos o su inset no es el de Doepfer, y en
    cualquiera de los dos casos el modelo estaria inventando. Dos fuentes
    independientes coincidiendo al centesimo es mejor evidencia que una hoja."""
    H = p["alto_panel_1u"]
    S = H - 2 * p["inset_er"]
    assert abs(S - S_1U_INTELLIJEL) < 0.01, (
        f"el panel de {H:.2f} con el inset_er de {p['inset_er']:.1f} da una "
        f"separacion de taladro de {S:.2f}, y Intellijel publica "
        f"{S_1U_INTELLIJEL:.2f}. O el alto del panel no es ese, o su inset no "
        f"es el de Doepfer: el modelo no puede elegir cual de las dos")

    ancho_bahia = {n: w for n, w, d in _secciones_miembro(p)}["bahia"]
    boca = ancho_bahia - 2 * p["t_costilla"]
    pide = S + p["rail_er_alto"]
    assert abs(boca - pide) < 0.01, (
        f"la boca de la bahia mide {boca:.2f} y la fila 1U pide {pide:.2f} "
        f"(separacion {S:.2f} + el alto de un riel). La boca se gobierna con "
        f"paso_horizontal, que es el largo del tramo plano del valle: cada mm "
        f"de valle es un mm de boca y un mm de fondo de aparato")

    hp_1u = round(p["largo_riel"] / p["hp"])
    hp_3u = round(p["largo_riel"] / p["hp"])
    assert hp_1u == hp_3u, (
        f"la fila 1U trae {hp_1u} HP y las de 3U {hp_3u}: cruzan el mismo case "
        f"entre las mismas dos costillas, asi que es el mismo numero")

    fondo = p["bahia_alto"] - p["rail_er_fondo"]
    assert fondo >= 0.0, (
        f"la bahia tiene {p['bahia_alto']:.1f} mm de alto y el riel se come "
        f"{p['rail_er_fondo']:.1f}: no queda fondo para el modulo")
    print(f"fila 1U: panel {H:.2f} (Intellijel), railes a {S:.2f} entre centros "
          f"-- cuadra al centesimo con los {S_1U_INTELLIJEL:.2f} publicados")
    print(f"  {hp_1u} HP a paso {p['hp']:.2f}, boca de {boca:.2f}, "
          f"{fondo:.1f} mm de fondo para el tile tras el riel")




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
    """El acrilico cabe en el rebaje del anillo, y el anillo lo cubre entero.

    ES LA PUERTA QUE SUSTITUYE A guarda_apilado() Y A guarda_canto_visto() A LA
    VEZ. Con la costilla de chapa el acrilico iba APILADO detras (chapa, junta,
    PMMA) y un casquillo cruzaba las tres capas; con el anillo de pletina va
    COPLANAR dentro de su ventana, asentado en un rebaje por detras. Ya no hay
    orden de capas que verificar ni casquillo que dimensionar: hay un rebaje
    que tiene que ser MAS HONDO que el acrilico mas grueso del lote.

    Cuatro condiciones, y la primera es la que puso el espesor en 14:

      1. la profundidad del rebaje (t_anillo - rehundido) alcanza para el PMMA
         mas grueso del lote -- 8 + 1.2 de tolerancia Schaeffer -- mas la junta
         de asiento y media decima de aire. Con 12 de anillo el rebaje quedaba
         a -0.2: no cabia.
      2. la franja interior (cara_anillo - rebaje_anillo) admite un M4 a rosca
         ciega con 1.5 D a cada lado: 3 x d_M4_paso = 13.5. Es lo que puso la
         cara vista en 20.
      3. el acrilico solapa el labio al menos 5 mm, para que lo retenga.
      4. el labio tiene cuerpo sobre el acrilico: 3 mm de la spec, y nunca
         menos del doble del chaflan -- la arista de la ventana se lo come por
         la cara vista, y con rehundido = chaflan el labio se queda en filo.

    El canto del PMMA queda cubierto POR CONSTRUCCION: un anillo con ventana
    rodea al acrilico en todo su perimetro. Por eso esta puerta no recorre
    tramos -- ya no hay 'tramo con ala' que decidir."""
    tol = 0.4 + 0.1 * p["t_cheek"]            # Schaeffer AG, 2026-08-18
    hondo = p["t_anillo"] - p["rehundido_acrilico"]
    pide = p["t_cheek"] + tol + p["t_junta_asiento"] + 0.5
    assert hondo >= pide, (
        f"el rebaje del anillo tiene {hondo:.2f} mm de fondo (t_anillo "
        f"{p['t_anillo']:g} - rehundido {p['rehundido_acrilico']:g}) y el "
        f"acrilico mas grueso del lote pide {pide:.2f} ({p['t_cheek']:g} + "
        f"{tol:.1f} de tolerancia + {p['t_junta_asiento']:g} de junta + 0.5 de "
        f"aire). Con ese anillo el PMMA no entra: sube t_anillo, no bajes la "
        f"junta")
    franja = p["cara_anillo"] - p["rebaje_anillo"]
    assert franja >= 3 * p["d_M4_paso"], (
        f"la franja interior del anillo mide {franja:.2f} (cara {p['cara_anillo']:g} "
        f"- rebaje {p['rebaje_anillo']:g}) y una rosca ciega M4 con 1.5 D a cada "
        f"lado pide {3 * p['d_M4_paso']:.2f}. Ahi asientan las placas de anclaje")
    assert p["rebaje_anillo"] >= 5, (
        f"el acrilico solo solapa el labio {p['rebaje_anillo']:g} mm; con menos de "
        f"5 el labio no lo retiene")
    labio = max(3.0, 2 * p["chaflan_anillo"])
    assert p["rehundido_acrilico"] >= labio, (
        f"el labio tiene {p['rehundido_acrilico']:g} mm de cuerpo sobre el "
        f"acrilico y pide {labio:g}, que es el mayor de dos minimos: los 3 de "
        f"la spec (cuerpo del labio) y 2 x {p['chaflan_anillo']:g} de chaflan "
        f"-- el de la arista de la ventana se come {p['chaflan_anillo']:g} mm "
        f"de ese cuerpo por la cara vista, y se pide el doble para que quede "
        f"al menos otro tanto de labio entero debajo")
    print(f"rebaje: anillo de {p['t_anillo']:g}, acrilico {p['rehundido_acrilico']:g} "
          f"atras en un rebaje de {hondo:.1f} (pide {pide:.1f}); franja de "
          f"{franja:.0f} para las roscas ciegas; cara vista {p['cara_anillo']:g}")


def _seccion_anillo(p: dict[str, float]) -> tuple[float, float, float]:
    """Inercia, area y fibra mas alejada del anillo, flexion FUERA del plano.

    La seccion de un tramo es un rectangulo macizo de (cara - rebaje) x t_anillo
    -- la franja donde asientan las placas -- mas el LABIO de rebaje x rehundido
    que queda delante del acrilico. Eje neutro por el teorema de los ejes
    paralelos, como _seccion_canal(). NO vale para flexion en el plano: ahi el
    anillo es un marco y trabaja a traccion y compresion."""
    W, T = p["cara_anillo"], p["t_anillo"]
    B, R = p["rebaje_anillo"], p["rehundido_acrilico"]
    a1, y1 = (W - B) * T, T / 2.0
    a2, y2 = B * R, R / 2.0
    A = a1 + a2
    yb = (a1 * y1 + a2 * y2) / A
    I = ((W - B) * T ** 3 / 12 + a1 * (y1 - yb) ** 2
         + B * R ** 3 / 12 + a2 * (y2 - yb) ** 2)
    return I, A, max(yb, T - yb)


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
    I, A, ymax = _seccion_anillo(p)
    assert abs(A - 214.0) < 1e-9, f"area {A}, a mano 214"
    assert abs(I - 2384089 / 642) < 1e-6, f"I = {I:.6f}, a mano {2384089/642:.6f}"
    assert abs(ymax - (14 - 1399 / 214)) < 1e-9, f"ymax {ymax:.6f}"


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
    I, A, ymax = _seccion_anillo(p)
    P = _vertices(p)
    n = len(P)
    nombres = ["frente bajo", "cara inferior", "el valle", "cara superior",
               "meseta de remate", "la trasera", "el suelo"]
    print(f"anillo: pletina de {p['t_anillo']:g}, cara vista {p['cara_anillo']:g}, "
          f"rebaje {p['rebaje_anillo']:g} x {p['t_anillo'] - p['rehundido_acrilico']:g}, "
          f"chaflan {p['chaflan_anillo']:g} -> I={I:.0f} mm4, {A:.0f} mm2, "
          f"{A * _perimetro(P) * 2.70e-6:.2f} kg por costilla")
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        largo = math.hypot(b[0] - a[0], b[1] - a[1])
        flecha = p["carga_mano"] * largo ** 3 / (192 * E_ALUMINIO * I)
        sigma = (p["carga_mano"] * largo / 8) * ymax / I
        assert flecha <= p["flecha_costado_max"], (
            f"el anillo cede {flecha:.3f} mm en el tramo '{nombres[i]}' de "
            f"{largo:.2f} mm y el techo son {p['flecha_costado_max']:.2f}. La "
            f"chapa plegada de 27 x 16 x 1.5 daba I=1673 y pasaba: si esto no "
            f"pasa, alguien adelgazo el anillo o le comio la franja")
        assert sigma <= RP02_ALUMINIO, (
            f"el anillo trabaja a {sigma:.1f} MPa en '{nombres[i]}' contra "
            f"{RP02_ALUMINIO:.0f}")
        print(f"  {nombres[i]:<18} {largo:7.2f} mm  cede {flecha:.3f}")


def _perimetro(P: list[tuple[float, float]]) -> float:
    return sum(math.hypot(P[(i + 1) % len(P)][0] - P[i][0],
                          P[(i + 1) % len(P)][1] - P[i][1]) for i in range(len(P)))


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
    costo 8.46. Siguen siendo DOS asserts, pero la segunda cambio de signo: ya
    no se exige que la bandeja se aparte del riel sino que LLEGUE al frente.

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
    # 2. LA TABLA NO SE HUNDE BAJO EL CHASIS DEL PSU.
    #
    #    Aqui vivian tres asserts y los tres se cayeron al pasar el suelo a
    #    tabla bajo el marco:
    #      - "la bandeja LLEGA al frente" se volvio TAUTOLOGIA cuando su canto
    #        paso a derivarse de la tangente de la curva. Una puerta que no
    #        puede fallar no mide nada.
    #      - "el larguero de base delantera se aparta del riel" se quedo sin
    #        sujeto: ese larguero ya no existe.
    #      - el VOLADIZO de 271.45 mm, que pedia 10 mm de aluminio, no existe:
    #        la tabla no cuelga de una barra, el marco se le APOYA encima.
    #
    #    LO QUE QUEDA, y es lo unico que de verdad la dobla: el chasis del PSU
    #    sentado en medio del vano entre las dos costillas. El peso del propio
    #    case NO cuenta aqui -- las cuatro paticas van casi bajo las lineas de
    #    apoyo de las costillas, asi que ese camino no cruza el vano.
    #
    #    SUPUESTO HEREDADO y hay que decirlo: los 200 N son carga_mano, del
    #    costado. El peso real del chasis no esta itemizado en el repo (spec
    #    10). Se usa el conservador que ya existe. E_madera es a favor de veta
    #    y tambien es supuesto hasta que la especie este elegida.
    vano = perfil(p)["ancho_util"]
    b_tabla = fondo(p) + 2 * p["vuelo_zocalo"]
    I_z = b_tabla * p["t_base"] ** 3 / 12
    flecha_z = p["carga_mano"] * vano ** 3 / (48 * p["E_madera"] * I_z)
    assert flecha_z <= p["flecha_costado_max"], (
        f"la tabla cede {flecha_z:.3f} mm cruzando los {vano:.2f} mm entre las "
        f"dos costillas con el chasis del PSU encima, y el techo son "
        f"{p['flecha_costado_max']:.2f}. Con E_madera={p['E_madera']:.0f} hacen "
        f"falta 16 mm justos, 18 con margen y 20 si la especie es "
        f"contrachapado (E 8000). Subir t_base NO cuesta alto de aparato desde "
        f"que la tabla va debajo del marco.")
    print(f"suelo: TABLA DE MADERA MACIZA t={p['t_base']:g} bajo el marco, "
          f"{b_tabla:.2f} x {p['ancho_total'] + 2 * p['vuelo_zocalo']:.2f} "
          f"(vuela {p['vuelo_zocalo']:g} por los cuatro lados)")
    print(f"  con {p['carga_mano']:.0f} N en medio del vano de {vano:.2f} cede "
          f"{flecha_z:.3f} mm (techo {p['flecha_costado_max']:.2f}, "
          f"E {p['E_madera']:.0f} MPa a favor de veta)")
    # 4. y la trasera TAMBIEN llega al suelo. El suelo no lo cierra solo la
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
    assert abs(y0_pt) < 1e-6, (
        f"la trasera no llega al suelo: su canto de abajo cae en "
        f"y={y0_pt:.2f} y el plano inferior del case es y=0, o sea un rebaje "
        f"corrido de {caja_pt[6] - caja_pt[5]:.0f} x {y0_pt:.2f} x "
        f"{p['t_piel']:.0f} mm a lo largo de todo el canto trasero. La "
        f"plancha tiene que bajar hasta 0: la distancia al canto bajo la fila "
        f"de M3 CRECE al hacerlo (mas material alrededor del tornillo, no "
        f"menos), y las ondas y la rejilla no se mueven porque van derivadas "
        f"de f_base y f_tras, que salen de los dos miembros traseros")


# LAS DOS FILAS SE ABREN, cada una girando sobre el M4 de su riel de ARRIBA --
# el mismo tornillo que la fija de punta al costado, que entra a lo largo del
# ancho y por tanto ya es un eje. No hay bisagra en ningun sitio.
#   (nombre, indice del riel-EJE, cuerpos que giran, vertice de arranque de la
#    cara, angulo, inset del panel, alto del panel)
TAPAS = (
    ("fila de abajo", 1, frozenset({"cara_inf frente", "cara_inf valle"}),
     1, "angulo_inferior", "inset_inf_frente", "alto_panel_inf"),
    # remate_sup SALIO de este conjunto el 2026-08-21. Giraba con la tapa
    # porque iba PEGADA al Z-Rail, que es parte de la tapa. Desde que se
    # atornilla al larguero de remate trasero es pieza QUIETA, o sea un
    # obstaculo que la tapa tiene que librar al abrir -- que es justo lo que
    # esta puerta comprueba.
    ("fila de arriba", 3,
     frozenset({"cara_sup valle", "cara_sup remate"}),
     3, "angulo_superior", "inset_sup_valle", "alto_panel_sup"),
)

# Lo minimo que tiene que abrir una tapa para que sirva de algo. A 60 grados la
# cara queda casi vertical y el interior a la vista; por debajo de 45 no cabe la
# mano para cablear.
#
# ESTUVO EN 180 DURANTE UNA HORA el 2026-08-27 y se volvio a bajar, con permiso.
# Al montar la fila 1U la de abajo cayo a 63.8 y el presupuesto salio VERDE,
# porque la spec decia una cosa mas fuerte que la puerta: 9.3 listaba "las 180
# grados de apertura" entre lo que NO se toca. Se apreto la puerta a 180 para
# que el papel y el modelo dijeran lo mismo, se vio el rojo, y Samuel LIBERO la
# cota: "lo de los 180 ya no es importante, con 60 vamos mas que bien". La spec
# se enmendo en la misma tanda -- lo que no se podia dejar es una diciendo 180 y
# la otra 60, que es como se pierde una cota sin que nadie se entere.
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
    zr0, zr1 = railes[0][5], railes[0][6]
    miembros = _cajas_miembro(p, P, cr, zr0, zr1)
    nombres_miembro = set(miembros)
    obstaculos = ([c for c in railes if c[0] not in nombres_miembro]
                  + _caras_miembro(p, miembros) + planchas)
    # EL BARRIDO ES PLANO -- gira esquinas en XY -- y eso vale mientras todo lo
    # que estorba cruce el mismo ancho que lo que gira. Desde el 2026-08-28 hay
    # que decirlo aparte: TODO LO QUE GIRA vive entre z0 + t_placa y
    # z1 - t_placa (el riel mide ancho_util - 2*t_placa y muere contra su
    # placa; el panel se atornilla al riel y no puede ser mas largo que el),
    # mientras las PLACAS y las BRIDAS traseras viven justo en las dos
    # rebanadas que quedan fuera de ese hueco. En el plano se pisan; a lo ancho
    # no se tocan.
    #
    # LO QUE ESTE FILTRO NO SUELTA, y conviene que quede escrito porque estuvo
    # mal escrito un dia: la pestana de la banda del valle SIGUE SIENDO EL TOPE
    # de la fila de abajo, que abre 63.8 grados. La pestana ya no apoya contra
    # el anillo sino ENCIMA de la placa del valle (z = 20..23), o sea dentro
    # del mismo hueco que barren el riel y el panel: comparte su ancho y el
    # filtro no la quita. Y esta bien que no la quite -- ese tope es real y se
    # toca al abrir.
    #
    # 63.8 pasa porque APERTURA_MIN vale 60 desde el 2026-08-27, cuando Samuel
    # solto la cota de 180 al montar la fila 1U ("con 60 vamos mas que bien",
    # y la spec 9.3 se enmendo en la misma tanda). A 63.8 la cara queda casi
    # vertical y se cablea con la mano dentro, que es lo que la cota protege.
    # Lo que este filtro quita son las PLACAS y las BRIDAS traseras, que viven
    # en las dos rebanadas de 6 mm que quedan FUERA de ese hueco: en el plano
    # se pisan con el riel, a lo ancho no se tocan. Sin el, la placa del frente
    # salia como tope a 0.2 grados.
    obstaculos = [c for c in obstaculos if min(c[6], zr1) - max(c[5], zr0) > 1e-9]
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
        quietos = [c for c in obstaculos if c[0] not in propios]
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

    # LA JUNTA DE LA PESTANA vivio aqui hasta el 2026-08-21, y murio con su
    # sujeto. Medía el hueco entre la tira de remate y el Z-Rail, primero
    # exigiendo cero exacto (union atornillada) y despues una linea de pegado
    # entre 0 y medio milimetro (union pegada, tras descubrir que esa cara del
    # riel es pared de 1.2 mm). Desde que la pieza se atornilla al larguero de
    # remate trasero no hay junta con el riel que medir: lo que la sujeta lo
    # verifican alineacion() y apoyo() como a cualquier otra plancha, y que no
    # estorbe a la tapa lo verifica el barrido de aqui arriba.
    #
    # Lo que si sigue sin poder derivarse en params.scad -- ese fichero no
    # admite expresiones -- es que la tapa cubra la meseta entera, y eso es lo
    # que exige guarda_remate().


def guarda_remate(p: dict[str, float]) -> None:
    """La tapa de remate cubre la meseta del techo, ni mas ni menos.

    La meseta mide marco_remate y hay que repartirla ENTERA entre tres cosas.
    En params.scad no se pueden escribir expresiones, o sea que la relacion se
    mantiene A MANO y por eso hace falta una puerta: mover una sin mover las
    otras deja la meseta abierta o una pieza asomando por el plano trasero, y
    ninguna de las dos se ve en un DXF plano.

    ERAN DOS SUMANDOS HASTA EL 2026-08-27 y ahora son TRES, porque la meseta
    cambio de dueno. Antes era una plancha de acrilico apoyada encima del
    larguero y de la trasera, medida desde el plano trasero: cubria todo salvo
    el inset. Ahora es el ALA del miembro alto, y un ala se mide desde su
    doblez -- la cara trasera del miembro --, asi que se queda t_piel corta por
    detras. Ese trozo lo cubre el CANTO DE ARRIBA DE LA TRASERA, que por eso
    subio hasta el pico el mismo dia. El reparto es:

        inset_remate_frente   lo que queda ABIERTO para que la tapa de arriba
                              gire. No es estetica: es lo unico que la deja
                              abrir, y con prof_sup a 37 medido desde el doblez
                              la apertura caia de 180 a 45 grados.
        prof_sup              la meseta, o sea el ala del miembro alto.
        t_piel                el canto de arriba de la trasera.

    El inset NO se toca a la ligera. Ver su nota en params.scad."""
    suma = p["prof_sup"] + p["inset_remate_frente"] + p["t_piel"]
    assert abs(suma - p["marco_remate"]) < 1e-9, (
        f"la meseta no se reparte entera: inset_remate_frente "
        f"({p['inset_remate_frente']:.0f}, lo que queda abierto para que gire "
        f"la tapa) + prof_sup ({p['prof_sup']:.0f}, el ala del miembro alto) + "
        f"t_piel ({p['t_piel']:.0f}, el canto de la trasera) = {suma:.2f}, y "
        f"marco_remate mide {p['marco_remate']:.2f}. Sobra o falta "
        f"{suma - p['marco_remate']:+.2f} mm. Los cuatro se mantienen a mano "
        f"porque params.scad no admite expresiones")
    print(f"remate: meseta de {p['prof_sup']:.0f} mm integrada en el miembro "
          f"trasero alto, retirada {p['inset_remate_frente']:.0f} del pico para que "
          f"la tapa de arriba abra")


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
    # Aqui SI toca la envolvente: la puerta limita el ancho total que cabe
    # entre railes, no busca material dentro de la bandeja.
    bahia = _envolvente_bahia(_cajas_miembro(p, P, cr, 0.0, 0.0))
    r = (bahia[2] - bahia[1]) / 2
    x_valle = (bahia[1] + bahia[2]) / 2
    lo = cr[1][0] + _he_er(p, p["angulo_inferior"])[0] + r
    hi = cr[2][0] - _he_er(p, p["angulo_superior"])[0] - p["holgura_rail"] - r
    assert lo <= x_valle <= hi, (
        f"la bahia no cabe entre los dos railes del valle: va "
        f"centrado en x={x_valle:.2f} y su ventana es [{lo:.2f}, {hi:.2f}]. "
        f"Es lo que limita paso_horizontal, no el hueco SAT")


# Censo de anchos minimos de panel por piso, mm. ESTIMADOS (spec §11):
# cierran cuando cada panel este dibujado. Fuente: conteo de mandos/jacks
# de los README de modulo + patch bay normalizado que anade jacks.
ANCHOS_PISO_SUP = {"MIDI/CV": 80, "VCO1": 90, "VCO2": 90, "VCO3": 90}
ANCHOS_PISO_INF = {"VCF": 100, "ADSR": 110, "VCA": 80, "MIXER": 100}
EXPANSION_MIN = 40  # sitio reservado a crecer, por piso


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
    # caja es lo que se ve al abrir el case -- fue el primer comentario de Samuel
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
    pos_y = _x_chasis_frente(p) + p["vuelo_zocalo"]
    ax = pos_x + c["desfase"] + t + p["chasis_salida_x"] - hol
    ay = pos_y + c["desfase"] + t + p["chasis_salida_y"] - hol
    exige(0 <= ax and ax + w <= au
          and 0 <= ay and ay + h <= fondo_bandeja,
          f"el agujero de cables cae en x={ax:.1f}..{ax + w:.1f}, "
          f"y={ay:.1f}..{ay + h:.1f} y la tabla mide {au:.2f} x "
          f"{fondo_bandeja:.2f}: se sale de la pieza")

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
    P_ = _vertices(p)
    cr_ = _centros_rail(p, P_)
    miembros_ = _cajas_miembro(p, P_, cr_, 0.0, 0.0)
    libre_1 = miembros_["trasero bajo"][1] + p["vuelo_zocalo"] - hol
    exige(pos_y >= 0 and pos_y + c["tapa_y"] <= libre_1,
          f"el chasis ocupa y={pos_y:.1f}..{pos_y + c['tapa_y']:.1f} de la "
          f"tabla y, con {hol:.0f} mm de holgura al miembro trasero bajo, cabe "
          f"de 0.0 a {libre_1:.1f}")
    print(f"  cuelga por detras del miembro trasero bajo ("
          f"{libre_1 - (pos_y + c['tapa_y']):.2f} mm de sobra sobre el minimo "
          f"de {hol:.0f}) y apoya por delante en la tabla")

    # --- 6b. y los M5 con que cuelga caben en la pared ---------------------
    # SON DOS DESDE EL 2026-08-27, no cuatro: los otros dos iban a `base
    # delantera` y esa barra ya no existe. Esa pared apoya ahora en la tabla.
    # El tornillo entra por la ranura INTERIOR del 2020, cuyo eje esta a rail/2
    # sobre el suelo. Lo que queda de pared bajo ese eje es rail/2 -
    # chasis_pie, y de eso los primeros radio_doblez + t_chapa son CURVA: ahi
    # no se taladra. Es la cota que ata chasis_pie por arriba, y no la ve nadie
    # mas -- ni solapes(), ni el sobre del DXF, que es plano.
    anclajes_ = _anclajes_miembro(p, miembros_)
    sube = anclajes_[("trasero bajo", "base")][1] - p["chasis_pie"]
    curva = p["radio_doblez"] + p["t_chapa"]
    margen = sube - curva - p["d_M5_paso"] / 2
    exige(margen >= 0,
          f"el M5 que cuelga el chasis cae a {sube:.2f} mm del suelo de la caja "
          f"y ahi todavia hay doblez: la curva ocupa {curva:.2f} y el taladro "
          f"pide {p['d_M5_paso'] / 2:.2f} de radio ({margen:+.2f}). Baja "
          f"chasis_pie o el tornillo no se puede taladrar")
    exige(p["chasis_pie"] > 0,
          "chasis_pie a cero deja el suelo del chasis TOCANDO la tabla en toda "
          "su superficie. La pared delantera se le atornilla, si, pero por sus "
          "PIES: entre la chapa del toroide y la madera tiene que quedar aire, "
          "que es lo que el #106 pedia cuando debajo habia acrilico y sigue "
          "valiendo con madera")
    print(f"  cuelga de {int(p['chasis_anclajes'])} M5 a la reticula del miembro "
          f"trasero bajo por su pared TRASERA, a {sube:.1f} mm del suelo de la "
          f"caja ({margen:.2f} de margen tras el doblez); la delantera apoya "
          f"en la tabla con {p['chasis_pie']:.0f} mm de aire bajo la chapa")

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
    """Fondo de la TABLA, de canto a canto.

    ERA EL VANO ENTRE LOS DOS LARGUEROS. Hasta el 2026-08-21 ese vano y la
    plancha midieron lo mismo; luego no, porque la bandeja volaba por delante
    del larguero delantero para cerrar el suelo. El 2026-08-27 la pieza cambia
    de sitio -- pasa a ser tabla BAJO el marco -- y de vano ya no queda nada:
    es el fondo del case mas lo que la tabla sobresale por delante y por
    detras."""
    return fondo(p) + 2 * p["vuelo_zocalo"]


def main() -> int:
    p = leer_params()
    autocomprobacion(p)
    autocomprobacion_anillo()
    autocomprobacion_pv()
    autocomprobacion_canal()
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
    guarda_anclajes(p)
    guarda_miembros(p)
    guarda_agarre(p)
    guarda_fila_1u(p)
    guarda_meseta_es_chapa(p)
    guarda_piso(p)
    guarda_anillo(p)
    guarda_aire(p)
    guarda_chaflan(p)
    guarda_valle(p)
    guarda_apriete(p)
    guarda_paticas(p)
    canario_red(p)
    guarda_red(p)
    guarda_fresado(p)
    guarda_parametros_vivos(p)
    guarda_escalon(p)
    guarda_tapa(p)
    guarda_remate(p)
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
    # guarda_costado() vive alli y no aqui.
    exige(0.1 <= p["hol_riel"] <= p["rail"] / 2,
          f"hol_riel = {p['hol_riel']}: por debajo de 0.1 el riel entra a "
          f"presion contra el ala de la costilla, y por encima de "
          f"{p['rail'] / 2:.0f} se queda corto de costado a costado y sus M4 "
          f"de punta trabajan de mala manera")
    # CONTRA largo_riel Y NO CONTRA ancho_util desde el 2026-08-26. Fueron el
    # mismo numero mientras el riel iba de cara a cara del acrilico, y al
    # separarse (2*t_costilla) medir contra el hueco AFLOJA estas dos reglas en
    # silencio: daria 6 mm de panel que no existen. Los modulos se atornillan a
    # la pletina roscada del RIEL, asi que el riel es quien manda cuanto panel
    # cabe -- el hueco entre costados nunca fue el sujeto correcto, solo lo
    # parecia por coincidir.
    exige(sum(ANCHOS_PISO_SUP.values()) + EXPANSION_MIN <= p["largo_riel"],
          "el piso superior no cabe a lo largo del riel")
    exige(sum(ANCHOS_PISO_INF.values()) + EXPANSION_MIN <= p["largo_riel"],
          "el piso inferior no cabe a lo largo del riel")
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
    exige(p["vent_puente_min"] >= 0.8 * p["t_valle"],
          "puente de ventilacion fragil para el espesor")
    fallos.extend(solapes(p))
    fallos.extend(alineacion(p))
    fallos.extend(apoyo(p))

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
