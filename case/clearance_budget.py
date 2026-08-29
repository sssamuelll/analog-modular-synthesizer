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
    cadena que salida_cables_xy() en el .scad (x local = vuelo + z del mundo,
    y local = vuelo + x del mundo; el interior arranca desfase + t dentro de
    la envolvente de la tapa). GEMELA de chasis_tornillos_tabla()."""
    c = _chasis(p)
    au = perfil(p)["ancho_util"]
    v = p["vuelo_zocalo"]
    pos_x = v + p["t_anillo"] + au - p["chasis_margen_bandeja"] - c["tapa_x"]
    pos_y = _x_chasis_frente(p) + v
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
def _cajas_miembro(p: dict[str, float], P: list[tuple[float, float]],
                    cr: list[tuple[float, float]], z0: float,
                    z1: float) -> dict[str, Caja]:
    """Las BANDAS del miembro alto y del talon, que son la cara que recibe la
    trasera: t_costilla de espesor a ras del plano trasero, banda_trasera de
    alto, la del alto colgando de la meseta y la del talon subiendo del pie.

    Fueron tres canales hasta el 2026-08-29 por la manana y dos por la tarde;
    desde esa noche el alto es una L y el bajo es el talon, y de cada uno la
    caja que aqui importa es su banda -- es donde muerden los M3 de la
    trasera (guarda_agarre) y donde caen sus filas (alineacion). La meseta, el
    retorno y el pie van aparte como caras (_caras_miembro). El argumento cr
    se queda por los llamadores; ya no lo usa nadie aqui."""
    t, h = p["t_costilla"], p["banda_trasera"]
    x1 = P[6][0]
    return {
        "trasero alto": ("trasero alto", x1 - t, x1, P[5][1] - h, P[5][1], z0, z1),
        "talon": ("talon", x1 - t, x1, 0.0, h, z0, z1),
    }


def _ventana_valle(p: dict[str, float], P: list[tuple[float, float]],
                   cr: list[tuple[float, float]]) -> tuple[float, float]:
    """(x0, x1) de la ventana del valle: lo libre entre los dos rieles 3U que
    miran al valle, donde vive la fila 1U. GEMELA de ventana_valle().

    Delante la manda el BARRIDO del riel del valle de la fila de abajo -- que
    gira sobre su propio M4: radio de giro mas holgura, no su esquina quieta,
    la misma leccion de guarda_tapa() --; detras, la esquina girada del riel de
    arriba menos holgura_rail, que es donde acaba x_valle(). Era la boca de la
    bahia hasta el 2026-08-29."""
    return (cr[1][0] + _radio_giro_riel(p) + p["holgura_rail"],
            _x_valle(p, P, cr)[1])


def _centros_rail_1u(p: dict[str, float], P: list[tuple[float, float]],
                      cr: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Dos Z-Rails 1U ARRIMADOS AL FRENTE de la ventana del valle, gemelos de
    centros_rail_1u(): el primero arranca donde acaba la banda, y lo que sobre
    de ventana queda detras, bajo el vuelo de la cara de arriba. Se centraban
    en la boca de la bahia hasta el 2026-08-29."""
    xa = _ventana_valle(p, P, cr)[0] + p["rail_er_alto"] / 2
    sep = p["alto_panel_1u"] - 2 * p["inset_er"]
    y = P[3][1] - p["t_panel"] - p["rail_er_eje"]
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
# subirse encima del marco -- a z >= t_anillo + t_placa esta el barrido del
# panel de arriba (se probo: la tapa pasaba de 121.5 a 52 grados). Asi que el
# marco lleva una muesca abierta a su canto exterior sobre la huella de la
# brida, de brida_ancho + t_costilla + 0.5 de honda, y la brida se tumba en
# la cara del anillo como siempre.

# Radio de redondeo por vertice, gemelo de radios_perfil() en el .scad. El 0
# (frente-abajo) no lleva radio sino CHAFLAN (chaflan_nariz), que vive en el
# contorno (pts_contorno() en el .scad) y no en pts_perfil(); aqui va None. Los
# SEIS vertices restantes llevan chapa doblada encima -- la nariz en 1, el
# retorno en 4, la banda del miembro alto en 5, la del talon en 6 -- y
# comparten radio_chapa (2026-08-29); el 2 y el 3 tienen los suyos.
RADIOS_PERFIL = [None, "radio_chapa", "radio_pico", "radio_valle",
                 "radio_chapa", "radio_chapa", "radio_chapa"]


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
    r = RADIOS_PERFIL[i]
    return _tangente(V, A, B, p[r]) if (cruz < 0 and r) else 0.0


def _tol_pmma(p: dict[str, float]) -> float:
    """Tolerancia de espesor del PMMA: +-(0.4 + 0.1 x t), Schaeffer AG
    (2026-08-18). Es la cota que manda en todo lo que vive delante o detras de
    una plancha de acrilico."""
    return 0.4 + 0.1 * p["t_cheek"]


def _retiro_marco(p: dict[str, float]) -> float:
    """Lo que el canto exterior del marco se retira de la silueta bajo cada
    chapa: su espesor mas el aire con que las chapas se empotran."""
    return p["t_costilla"] + p["hol_piel"]


def _retiro_marco_trasera(p: dict[str, float]) -> float:
    """Lo que la pata trasera se retira del plano trasero: la banda, la
    trasera MAS GRUESA del lote y medio milimetro de aire. Es la regla de
    guarda_trasera_dentro() escrita como cota."""
    return p["t_piel"] + p["t_costilla"] + _tol_pmma(p) + 0.5


def _muesca_brida(p: dict[str, float]) -> tuple[float, float]:
    """(x_min, y_min) de la muesca del marco sobre la brida: todo lo que quede
    a x >= x_min y y >= y_min se corta. x_min es la punta de la brida menos
    el aire; y_min, su canto de abajo menos 0.5."""
    P = _vertices(p)
    x_dob = P[6][0] - p["t_costilla"]
    return (x_dob - p["brida_largo"] - p["hol_piel"],
            P[5][1] - p["t_costilla"] - p["brida_ancho"] - 0.5)


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
             puntos=None, convexos=None):
        L = math.hypot(B[0] - A[0], B[1] - A[1])
        u = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
        n = (u[1], -u[0])
        ejes = [((cc[0] - A[0]) * u[0] + (cc[1] - A[1]) * u[1], cc, k)
                for cc, k in zip(ejes_c, con)]
        pts = puntos or [(s0, retiro), (s1, retiro), (s1, f), (s0, f)]
        conv = convexos or [pts]
        m = lambda q: (A[0] + u[0] * q[0] + n[0] * q[1],
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
                "s0": s0, "s1": s1, "retiro": retiro, "fondo": f, "ejes": ejes,
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
    # el valle: recoge los dos rieles 1U y se pasa de P3 (concavo) hasta
    # cubrir el cajeado del segundo con 1.5 D de canto. La segunda 1U NO lleva
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
    L = math.hypot(P[6][0] - P[5][0], P[6][1] - P[5][1])
    s0, s1 = ini(5, rm), fin(L, 6, rm)
    s_mu, b_mu = P[5][1] - y_mu, P[6][0] - x_mu
    if b_mu >= f:
        # la muesca alcanza la pata entera: se lleva la esquina de arriba
        out.append(pata("trasera", P[5], P[6], s_mu, s1, rmt))
    else:
        out.append(pata("trasera", P[5], P[6], s0, s1, rmt,
                        puntos=[(s_mu, rmt), (s1, rmt), (s1, f), (s0, f),
                                (s0, b_mu), (s_mu, b_mu)],
                        convexos=[[(s_mu, rmt), (s1, rmt), (s1, f), (s_mu, f)],
                                  [(s0, b_mu), (s_mu, b_mu), (s_mu, f), (s0, f)]]))
    out[-1]["muesca"] = (s_mu, min(b_mu, f))
    # el suelo, bajo los pies de la nariz y del talon, hasta el chaflan
    L = P[6][0] - c
    out.append(pata("suelo", P[6], C0, ini(6, rmt), fin(L, None, rm), rm))
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
    pata: eje +- sep_rosca_riel a lo largo del tramo, a dist_rosca_ciega de la
    silueta. Diez por anillo. GEMELA de roscas_marco() en el .scad.

    EL PAR SE ARRIMA AL RIEL PERO NO SE SALE DE SU PATA: se corre lo justo
    para que las dos queden a 1.6 D de los extremos de la pata (1.6 y no 1.5
    para no vivir del redondeo de coma flotante). El marco sigue de largo por
    las esquinas, pero los extremos de las patas de las filas no son
    arbitrarios: el de la cara de arriba en P3 esta a retiro_placa_sup del
    vertice porque ahi el redondeo concavo estrecha la franja y una rosca se
    sale por el rebaje, y el de la cara de abajo en P1 es el escalon bajo la
    nariz. Lo cruza taladros_anillo() contra el rebaje releido del DXF."""
    sep, d = p["sep_rosca_riel"], p["dist_rosca_ciega"]
    canto = 1.6 * p["d_M4_paso"]
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
            c = min(max(s_eje, lo + sep), hi - sep)
            for s in (c - sep, c + sep):
                out.append((f"marco {q['nombre']} {s - s_eje:+.1f}",
                            q["_m"]((s, d))))
    return out


def bbox_marco_ventana(p: dict[str, float]) -> tuple[float, float]:
    """Envolvente del DXF del marco: la silueta menos los retiros. De la cara
    del frente (retirada bajo la nariz) a la pata trasera (retirada de la
    banda y la trasera), y del suelo a la meseta (retirados bajo sus chapas).
    Derivada, no escrita a mano: si una banda de retiro se mueve, el sobre se
    mueve con ella y revisar() lo canta."""
    P = _vertices(p)
    rm, rmt = _retiro_marco(p), _retiro_marco_trasera(p)
    return (P[6][0] - rmt - rm, P[5][1] - 2 * rm)


def _pasos_riel_marco(p: dict[str, float]) -> list[tuple[str, tuple[float, float]]]:
    """Los seis pasos M4 de riel del marco (con su cajeado por el lado del
    anillo): los cuatro 3U y los dos 1U."""
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

    APOYA EN LA CARA DEL ANILLO, a z = t_anillo, fuera de la rebanada en la
    que giran los paneles -- y desde el 2026-08-29 por la noche eso es lo que
    manda su geometria: en esa franja vive el marco de la ventana, y la brida
    NO se sube encima (a z >= t_anillo + t_placa esta el barrido del panel de
    arriba: la tapa pasaba de 121.5 a 52 grados). Es el marco el que lleva una
    muesca sobre ella (_muesca_brida), y la trasera una muesca de esquina
    porque la brida le pasa por debajo. Sus dos M4: el de dentro a la raiz
    del doblez (r + 3t + d/2), el de fuera a 1.5 D del canto libre. GEMELA de
    bridas_anillo() y brida_*() en el .scad. El miembro bajo ya no tiene
    brida: es el talon, y va a la tabla."""
    P = _vertices(p)
    t, d = p["t_costilla"], p["d_M4_paso"]
    x_dob = P[6][0] - t                     # la cara interior de la banda
    y1 = P[5][1] - t
    y0 = y1 - p["brida_ancho"]
    raiz = p["radio_doblez_costilla"] + 3 * t + d / 2
    s_in, s_out = raiz, p["brida_largo"] - 1.5 * d
    y_m4 = P[5][1] - p["dist_rosca_ciega"]
    return [{"nombre": "trasero alto", "x_dob": x_dob,
             "rect": (x_dob - p["brida_largo"], x_dob, y0, y1),
             "m4": [(x_dob - s_in, y_m4), (x_dob - s_out, y_m4)],
             "s_m4": (s_in, s_out), "raiz": raiz}]


def _cajas_brida(p: dict[str, float], z0: float, z1: float) -> list[Caja]:
    """Las bridas como cuerpos: t_costilla de espesor contra la cara del
    anillo, por los dos costados."""
    out: list[Caja] = []
    t = p["t_costilla"]
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

    DOCE POR ANILLO desde el 2026-08-29 por la noche, todas M4 y todas a
    dist_rosca_ciega de la silueta: diez del marco de la ventana -- dos por
    riel 3U y dos sobre el primer riel 1U -- y dos de la brida del miembro
    alto. Eran dieciseis: las dos de los clips murieron con ellos y las dos de
    la brida del miembro bajo con el, que hoy es talon y va a la tabla.

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
          f"de sobra de canto); marco de {p['t_placa']:g} con la cabeza dentro "
          f"(PMMA hasta z={techo_pmma:.2f})")
    print(f"  el agujero del marco mas justo es el {peor_eje[1]} a "
          f"{peor_eje[0]:.2f} del canto; el M4 de brida mas justo, '{peor_brida[1]}' a "
          f"{peor_brida[0]:.2f} (minimo {minimo:.2f}); el M3 de la pestana a "
          f"{d_m3:.2f} del canto de la pata del valle")


def _m3_pestana(p: dict[str, float]) -> tuple[float, float]:
    """Centro del M3 de la pestana de la banda del valle, en el plano del
    perfil. GEMELO del agujero que tapa_valle_2d() dibuja en el desarrollo y
    del que placa_riel() rosca en la placa del valle: x centrado en los 3 D
    finales del vuelo delantero, y a pv_a por debajo de la cara de arriba."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    return (_pv_x(p, _ventana_valle(p, P, cr)[0]), P[3][1] - _pv(p)["a"])


def _anclajes_miembro(p: dict[str, float], cajas: dict[str, Caja]
                       ) -> dict[tuple[str, str], tuple[float, float]]:
    """Lineas de tornillo de la trasera sobre las DOS BANDAS: a media banda,
    en la cara interior de la banda. La fila de arriba va en la banda del
    miembro alto, la de abajo en la del talon."""
    alto, talon = cajas["trasero alto"], cajas["talon"]
    t = p["t_costilla"]
    return {
        ("trasero alto", "remate"): (alto[2] - t / 2, (alto[3] + alto[4]) / 2),
        ("talon", "base"): (talon[2] - t / 2, (talon[3] + talon[4]) / 2),
    }


def _caras_miembro(p: dict[str, float], cajas: dict[str, Caja]) -> list[Caja]:
    """Cajas de las caras de chapa del miembro alto y del talon, sin rellenar
    el vacio de cada plegado: la meseta, la banda y el retorno del alto; la
    banda y el pie del talon."""
    t = p["t_costilla"]
    alto, talon = cajas["trasero alto"], cajas["talon"]
    z0, z1 = alto[5], alto[6]
    P = _vertices(p)
    return [
        ("trasero alto", alto[1], alto[2], alto[3], alto[4], z0, z1),
        # LA MESETA: del pico al plano trasero, marco_sup (= t) de espesor
        ("trasero alto meseta", P[4][0], P[6][0], P[5][1] - p["marco_sup"],
         P[5][1], z0, z1),
        # EL RETORNO (2026-08-29): dobla en el pico y baja por la cara de
        # arriba. Su caja es la AABB del tramo girado -- conservadora, y sin
        # falso positivo: lo que gira pasa por debajo, lo mide
        # guarda_retorno_meseta() con la distancia radial exacta.
        _retorno_meseta(p)["caja"] + (z0, z1),
        ("talon", talon[1], talon[2], talon[3], talon[4], z0, z1),
        ("talon pie", talon[2] - t - p["talon_pie"], talon[2] - t, 0.0, t,
         z0, z1),
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
    hx_1u, hy_1u = _he_er(p, 90.0)
    for i, c in enumerate(_centros_rail_1u(p, P, cr)):
        railes.append((f"fila 1U {i}", c[0] - hx_1u, c[0] + hx_1u,
                       c[1] - hy_1u, c[1] + hy_1u,
                       z0 + p["t_placa"], z1 - p["t_placa"]))
    # LAS DOS BANDAS (miembro alto y talon) son las cajas de los miembros; la
    # meseta, el pie del talon y el retorno van aparte como caras, porque un
    # canal ya no existe y la AABB de la L entera seria un hueco enorme que
    # acusaria de chocar al riel-eje de la fila de arriba.
    railes.extend(miembros.values())
    caras = _caras_miembro(p, miembros)
    railes.extend(c for c in caras
                  if c[0] in ("trasero alto meseta", "talon pie"))
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
    # acaba donde arranca la ventana del valle, o sea en la cara del primer
    # Z-Rail 1U (desde el 2026-08-29; antes, en el ala de la bahia)
    x1_tv = _ventana_valle(p, P, cr)[0]
    planchas.append(("tapa_valle", x0_tv, x1_tv,
                     P[3][1] - t_acr, P[3][1], z0_tv, z1_tv))
    # LAS DOS PESTANAS de la tapa, dobladas hacia abajo contra la costilla.
    # Van en `railes` y no en `planchas` a proposito: es la lista que solapes()
    # cruza contra todo, y una pestana que se echa encima del larguero del valle
    # o del riel de abajo no la caza nadie mas. (Y `planchas` la recorre
    # _sobres() para sacar envolventes de DXF, que aqui no aplica.)
    x0_pv, x1_pv = x1_tv - 3 * p["d_M3_paso"], x1_tv
    pv_x = _pv_x(p, x1_tv)
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
    # en t_piel (8) y declara DOS filas, una por banda.
    # DESDE EL 2026-08-29 POR LA NOCHE VA DENTRO DE LAS DOS BANDAS: su cara
    # trasera contra la cara interior de las bandas (rehundida t_costilla del
    # plano trasero, como con el marco de la manana), su canto de abajo SOBRE
    # EL PIE DEL TALON (y = t_costilla, ya no el plano del suelo) y el de
    # arriba hol_piel bajo la meseta. Ver guarda_piso(), assert 3.
    y0_pt = p["t_costilla"]
    # SE QUEDA marco_sup POR DEBAJO DEL PICO, y esta gemela estuvo 1.5 mm
    # desincronizada del 27-08 al 29-08. El .scad siempre corto la plancha en
    # `P[5].y - marco_sup` -- la cara de abajo de la meseta -- y aqui se escribio
    # `P[5][1]` con un comentario que decia que llegaba al pico. Nadie lo vio:
    # el unico cruce era el sobre del DXF, y TOL vale 4 mm.
    #
    # Lo de fondo era que ninguna de las dos estaba bien. Con la plancha a
    # 254.68 quedaba un hueco corrido de 8 x 1.5 a lo largo de los 540 mm del
    # canto trasero de arriba, y subirla al pico lo cerraba con CANTO DE
    # ACRILICO en la cara que se mira desde arriba -- que es la mitad de #234.
    # Desde el 2026-08-29 esa rebanada la ocupa el ala B de marco_trasera_sup:
    # metal, coplanar con la meseta, y la plancha se queda donde su .scad la
    # tuvo siempre.
    alto_pt = P[5][1] - p["marco_sup"] - p["hol_piel"] - y0_pt
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
    x0_pt, x1_pt = P[6][0] - p["t_piel"] - p["t_costilla"], P[6][0] - p["t_costilla"]
    # LAS DOS MUESCAS DE ESQUINA de arriba (2026-08-29, noche): por ahi pasa la
    # brida del miembro alto, tumbada en la cara del anillo justo donde la
    # trasera apoya su esquina. La caja principal se queda entre las muescas y
    # las dos tiras laterales llegan hasta debajo de ellas: tres cajas para que
    # solapes() vea la muesca. Las tiras llevan "lado" en el nombre y
    # _sobres() las salta -- el DXF es el contorno entero.
    mz, my = _muesca_trasera(p)
    planchas.append(("piel_trasera", x0_pt, x1_pt, y0_pt, y0_pt + alto_pt,
                     z_pt0 + mz, z_pt1 - mz))
    for lado, (za, zb) in enumerate(((z_pt0, z_pt0 + mz), (z_pt1 - mz, z_pt1))):
        planchas.append((f"piel_trasera lado {lado}", x0_pt, x1_pt,
                         y0_pt, y0_pt + alto_pt - my, za, zb))
    filas += [("piel_trasera", "base", "y",
               anclajes[("talon", "base")][1], "talon"),
              ("piel_trasera", "remate", "y",
               anclajes[("trasero alto", "remate")][1], "trasero alto")]
    return railes, planchas, filas


def _muesca_trasera(p: dict[str, float]) -> tuple[float, float]:
    """(honda en z desde el canto lateral, alta en y desde el canto de arriba)
    de cada muesca de esquina de la trasera: la brida del miembro alto le pasa
    por debajo de la esquina, tumbada en la cara del anillo, asi que la
    trasera cede t_costilla + 0.5 en z (arranca hol_piel por encima de la cara
    y la brida sube t_costilla) por brida_ancho + 0.5 en y. GEMELA de
    muesca_trasera() en el .scad."""
    return (p["t_costilla"] + 0.5, p["brida_ancho"] + 0.5)


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
    prototipo flexa, n_bulkheads pasa a 3 y se re-exporta'. Pero costados()
    dibuja DOS costados fijos -- uno en z=rehundido_acrilico y otro en
    z=ancho_total - rehundido_acrilico - t_cheek, o sea los dos ASENTADOS EN EL
    REBAJE de su anillo desde el 2026-08-28; no en z=0 y ancho_total-t_cheek,
    que era donde vivian cuando la mejilla era la pieza exterior --, sin
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
    f_base = anclajes[("talon", "base")][1]
    f_tras = anclajes[("trasero alto", "remate")][1]
    y_bajas = f_base + 0.37 * (f_tras - f_base)
    y0 = f_base + p["valle_espina"] / 2 + p["vent_puente_min"]
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

    LO QUE ESTE NUMERO NO DICE, y hay que decirlo: potencia_disipada son SOLO
    los reguladores del PSU. La disipacion de los modulos no esta en ningun
    presupuesto de este repo, asi que el salto termico describe el camino del PSU --
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
    f_base = anclajes[("talon", "base")][1] - y0_pl
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
        f"de {p['vent_ancho_ranura']:.2f}: deja de leerse como campo y pasa a "
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
          f"{largo_ent:.1f} x {p['vent_ancho_ranura']:.2f} (trasera, y={y_ent:.0f})")
    print(f"  salida {a_sal:.0f} mm2 = {a_mes:.0f} de la meseta "
          f"({n_mes} ranuras de {largo_mes:.1f} x "
          f"{p['vent_ancho_ranura']:.2f}, y={y_mes:.0f}) + "
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
    """La banda del vuelo delantero: lo que aguanta y lo que no.

    HASTA EL 2026-08-29 ESTA PUERTA MEDIA UN APOYO QUE NO EXISTIA. Decia que la
    banda apoyaba "en el ala delantera de la bahia por su canto trasero" y
    calculaba un voladizo corto desde esa linea (48.8 MPa, "pasa con margen").
    Pero la banda acababa EN la cara exterior del ala y el ala arrancaba ahi
    mismo: se tocaban en una arista, y una arista no es un apoyo. La bahia
    murio ese dia (nota 1 de Samuel) y con ella la ficcion: la banda esta
    sujeta SOLO por sus dos pestanas, en las puntas, y entre ellas cruza
    ancho_util - 2 t_placa sin tocar nada -- el riel 1U arranca detras de su
    canto y su cara queda 1.6 por debajo del plano del valle, con la banda de
    3.

    Asi que el unico modelo honesto es la viga biapoyada entre pestanas, y
    vale igual para la mano que se apoya que para la que levanta: la misma
    seccion, el mismo vano. Con esa cuenta la banda NO PASA: cede decenas de
    milimetros y fluye a ~27 N. No es ROJO porque no es un fallo nuevo -- era
    el punto abierto del §10 de la spec del 28-08 ("la banda del valle fluye a
    ~27 N ... hay que apoyarla o convertirlo en assert"), solo que ahora el
    numero es el de verdad -- sino HUECO declarado, con las salidas escritas
    en la spec del 29-08: apoyar el canto trasero de la banda sobre el labio
    del riel 1U (un rebaje de 1.4 en ese canto: es una pieza de 3 mm que va
    al taller de mecanizado con los anillos), o un retorno hacia abajo, o
    los dos. Se decide mirando el render, como todo lo que se ve."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    x0 = _x_valle(p, P, cr)[0]
    x1 = _ventana_valle(p, P, cr)[0]
    b, t = x1 - x0, p["t_valle"]
    vano = _tapa_valle_au(p) - t
    I = b * t ** 3 / 12
    flecha = p["carga_mano"] * vano ** 3 / (48 * E_ALUMINIO * I)
    sigma = 3 * p["carga_mano"] * vano / (2 * b * t ** 2)
    p_fluye = RP02_ALUMINIO * 2 * b * t ** 2 / (3 * vano)
    print(f"valle: banda de ALUMINIO {b:.2f} x {t:g}, del pico al primer "
          f"Z-Rail 1U, sujeta SOLO por sus dos pestanas (vano {vano:.2f})")
    print(f"  con {p['carga_mano']:.0f} N en el centro cede {flecha:.1f} mm y "
          f"trabaja a {sigma:.0f} MPa (Rp0.2 {RP02_ALUMINIO:.0f}, fluye a "
          f"{p_fluye:.0f} N)")
    if sigma > RP02_ALUMINIO or flecha > p["flecha_costado_max"]:
        _HUECOS.append(
            f"la banda del valle ({b:.2f} x {t:g}) solo apoya en sus dos "
            f"pestanas: con {p['carga_mano']:.0f} N en el centro cede "
            f"{flecha:.1f} mm y fluye a {p_fluye:.0f} N. Le falta apoyo (spec "
            f"2026-08-29, seccion 7): rebaje sobre el labio del riel 1U o retorno")


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
            _ventana_valle(p, P, cr)[0] - x0)


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
    f_base = anclajes[("talon", "base")][1]
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
    for pieza, paso_hp, t in (
            ("trasera", p["valle_paso_hp"], p["t_piel"]),
            ("meseta", p["meseta_paso_hp"], p["t_costilla"])):
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
          f"{0.8 * p['t_piel']:.2f}), meseta "
          f"{p['meseta_paso_hp'] * p['hp'] - p['vent_ancho_ranura']:.2f} sobre "
          f"chapa de {p['t_costilla']:.1f} (minimo {0.8 * p['t_costilla']:.2f}), "
          f"vent_puente_min {p['vent_puente_min']:.2f}")




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
    """La L del miembro alto: la meseta (prof_sup) y la banda (banda_trasera)
    en t_costilla, y lo que aguanta SOLA con carga_mano en el centro.

    Seccion: el ala horizontal arriba (prof_sup x t) y el alma vertical detras
    (t x banda). Inercia por paralelas-a-ejes sobre dos rectangulos que no se
    solapan -- el alma arranca donde acaba el ala --, la tension en el canto
    libre de la banda (el punto mas lejos del eje neutro) y la flecha de viga
    biapoyada de ancho_util. GEMELA de la cuenta de guarda_miembro_alto()."""
    t, b, h = p["t_costilla"], p["prof_sup"], p["banda_trasera"]
    A1, y1 = b * t, h - t / 2                # el ala, arriba
    A2, y2 = t * (h - t), (h - t) / 2        # el alma, de abajo hasta el ala
    yb = (A1 * y1 + A2 * y2) / (A1 + A2)
    I = (b * t ** 3 / 12 + A1 * (y1 - yb) ** 2
         + t * (h - t) ** 3 / 12 + A2 * (y2 - yb) ** 2)
    au = perfil(p)["ancho_util"]
    F = p["carga_mano"]
    M = F * au / 4
    sigma = M * yb / I                       # el canto libre de la banda
    flecha = F * au ** 3 / (48 * E_ALUMINIO * I)
    P = _vertices(p)
    return {"I": I, "yb": yb, "sigma": sigma, "flecha": flecha,
            "y_fila": P[5][1] - h / 2, "x_dob": P[6][0] - t}


def _talon(p: dict[str, float]) -> dict:
    """El talon: la banda de abajo del plano trasero y su pie sobre la tabla.
    GEMELA de talon_*() en el .scad."""
    P = _vertices(p)
    t = p["t_costilla"]
    x_band = P[6][0] - t
    au = perfil(p)["ancho_util"]
    return {"x_band": x_band, "x_pie": x_band - p["talon_pie"],
            "m4_x": x_band - p["talon_pie"] + 1.5 * p["d_M4_paso"],
            "m4_z": [p["t_anillo"] + au * f for f in (0.25, 0.5, 0.75)],
            "y_fila": p["banda_trasera"] / 2,
            "largo": _trasera_au(p),
            "desarrollo": p["banda_trasera"] + p["talon_pie"] - _bd_miembro(p),
            "z0": p["t_anillo"] + p["hol_piel"],
            "z1": p["ancho_total"] - p["t_anillo"] - p["hol_piel"]}


def bbox_desarrollo_miembro(p: dict[str, float], cual: str) -> tuple[float, float]:
    """Envolvente del blank de cada pieza de chapa trasera, como la ve el
    laser: mas grande que la pieza doblada.

    El miembro alto tumba retorno, meseta y banda (un doblez de 45 y otro de
    90) y saca sus dos bridas por las puntas (un doblez de 90 cada una); el
    escalon de la brida se dibuja plano y lo descuenta el taller. El talon
    tumba banda y pie (un doblez de 90) y mide lo que la trasera."""
    bd = _bd_miembro(p)
    if cual == "trasero alto":
        au = perfil(p)["ancho_util"]
        return (au + 2 * (p["brida_largo"] - bd),
                p["retorno_meseta"] + p["prof_sup"] + p["banda_trasera"]
                - bd - _bd_angulo(p, 90.0 - p["angulo_superior"]))
    return (_talon(p)["largo"], _talon(p)["desarrollo"])


def guarda_miembro_alto(p: dict[str, float]) -> None:
    """El miembro alto se sostiene SOLO, y su brida y su fila caen en chapa
    plana.

    SUSTITUYE A guarda_miembros() (2026-08-29, noche), que comparaba la inercia
    de cada canal con la del 2020 que jubilo -- un piso heredado, no una
    carga. Aqui la carga es la de siempre, carga_mano en el centro de la
    meseta, sobre la L SOLA: sin la trasera, que atornillada cada 100 es en
    ese sentido una viga de canto 165 veces mas rigida y se lleva todo. Se
    exige que la L no fluya sola (RP02_ALUMINIO, el conservador de siempre) y
    se publica cuanto cede. Es lo que puso banda_trasera en 24: con 20 daba
    158 MPa.

    Y la brida: cabe en la banda con la meseta encima, sus dos M4 a 2 D uno
    de otro y a 1.5 D de su canto de arriba; la fila de M3 de la banda, a la
    raiz del doblez de arriba y a 1.5 D del canto libre."""
    m = _miembro_alto(p)
    assert m["sigma"] <= RP02_ALUMINIO, (
        f"el miembro alto SOLO -- meseta {p['prof_sup']:g} x banda "
        f"{p['banda_trasera']:g} en {p['t_costilla']:g} -- trabaja a "
        f"{m['sigma']:.0f} MPa en el canto libre de la banda con {p['carga_mano']:.0f} "
        f"N en el centro de la meseta, contra {RP02_ALUMINIO:.0f} de Rp0.2. Sube "
        f"banda_trasera (22 da 131, 24 da 110) u obliga 6082-T6 en el pliego")
    t, h = p["t_costilla"], p["banda_trasera"]
    raiz = _raiz_m3(p)
    assert h / 2 >= raiz, (
        f"la fila de M3 de la banda cae a {h / 2:.2f} del doblez de la meseta y "
        f"la regla de chapa pide {raiz:.2f} (r + 3t + d/2)")
    assert h / 2 >= 1.5 * p["d_M3_paso"], (
        f"la fila de M3 cae a {h / 2:.2f} del canto libre de la banda; 1.5 D son "
        f"{1.5 * p['d_M3_paso']:.2f}")
    b = _bridas(p)[0]
    assert p["brida_ancho"] + t <= h, (
        f"la brida mide {p['brida_ancho']:g} mas los {t:g} de la meseta y la "
        f"banda solo tiene {h:g}")
    s_in, s_out = b["s_m4"]
    assert s_out - s_in >= 2 * p["d_M4_paso"], (
        f"los dos M4 de la brida estan a {s_out - s_in:.2f}; 2 D son "
        f"{2 * p['d_M4_paso']:.2f}")
    assert p["dist_rosca_ciega"] - t >= 1.5 * p["d_M4_paso"], (
        f"el M4 de la brida cae a {p['dist_rosca_ciega'] - t:.2f} de su canto de "
        f"arriba (dist_rosca_ciega - t_costilla) y pide "
        f"{1.5 * p['d_M4_paso']:.2f}")
    au = perfil(p)["ancho_util"]
    tr = _trasera_au(p)
    alto_tr = _vertices(p)[5][1] - p["marco_sup"] - p["hol_piel"] - t
    EI_tr = E_PMMA_TRASERA * p["t_piel"] * alto_tr ** 3 / 12
    print(f"miembro alto: L de {p['prof_sup']:g} x {h:g} en {t:g}, I={m['I']:.0f} "
          f"mm4; SOLA con {p['carga_mano']:.0f} N al centro de {au:.2f} cede "
          f"{m['flecha']:.2f} mm y trabaja a {m['sigma']:.0f} MPa (Rp0.2 "
          f"{RP02_ALUMINIO:.0f}); la trasera atornillada es {EI_tr / (E_ALUMINIO * m['I']):.0f}x "
          f"mas rigida en ese sentido")
    print(f"  brida de {p['brida_largo']:g} x {p['brida_ancho']:g} en la cara "
          f"del anillo, bajo la muesca del marco; M4 a {s_in:.2f} y {s_out:.2f} "
          f"del doblez; fila de M3 a {h / 2:g} del canto libre ({tr:.2f} de largo)")


# Modulo del PMMA colado con el que esta acotada la trasera (E_PMMA en
# check_dxf.py); aqui solo para decir cuanto mas rigida es que la L.
E_PMMA_TRASERA = 3000.0


def guarda_talon(p: dict[str, float]) -> None:
    """El talon: la banda de abajo a ras del plano trasero, el pie sobre la
    tabla, sus tres M4 lejos de todo y la esquina del anillo con su radio.

    Es lo que queda del miembro trasero bajo (2026-08-29, noche): un angulo
    de la misma chapa que dobla en P6 sobre la tabla, como la nariz dobla en
    el chaflan. No lleva bridas ni rosca en el anillo -- su fijacion es la
    TABLA, que ya esta atada a los dos anillos con seis M5 -- y no carga nada
    en vertical porque apoya en ella en toda su longitud. La trasera se
    asienta en su pie y se atornilla a su banda cada 100."""
    tl = _talon(p)
    P = _vertices(p)
    t = p["t_costilla"]
    assert RADIOS_PERFIL[6] == "radio_chapa", (
        "la esquina de abajo-atras del anillo (P6) tiene que llevar radio_chapa: "
        "el talon dobla ahi sobre la tabla y una esquina viva bajo un doblez a "
        "90 asoma 1.9 mm")
    x_tr = P[6][0] - t - p["t_piel"]
    cabeza = 7.6                             # boton ISO 7380 M4
    aire = x_tr - (tl["m4_x"] + cabeza / 2)
    assert aire >= 0.5, (
        f"la cabeza del M4 del pie del talon llega a x={tl['m4_x'] + cabeza / 2:.2f} "
        f"y la trasera arranca en {x_tr:.2f}: se le mete {-aire:.2f} debajo. "
        f"Sube talon_pie")
    assert tl["m4_x"] - tl["x_pie"] >= 1.5 * p["d_M4_paso"] - 1e-9, (
        f"el M4 del pie cae a {tl['m4_x'] - tl['x_pie']:.2f} de su canto libre")
    raiz = _raiz_m3(p)
    assert tl["y_fila"] >= raiz, (
        f"la fila de M3 del talon cae a {tl['y_fila']:.2f} del doblez de abajo y "
        f"la regla de chapa pide {raiz:.2f}")
    assert tl["y_fila"] <= p["banda_trasera"] - 1.5 * p["d_M3_paso"], (
        f"la fila de M3 del talon se sale por el canto libre de la banda")
    print(f"talon: banda de {p['banda_trasera']:g} a ras del plano trasero y pie "
          f"de {p['talon_pie']:g} sobre la tabla; 3 M4 en x={tl['m4_x']:.2f} "
          f"({aire:.2f} de aire a la trasera); fila de M3 a {tl['y_fila']:g}; "
          f"desarrollo {tl['largo']:.2f} x {tl['desarrollo']:.2f}")


def guarda_trasera_dentro(p: dict[str, float]) -> None:
    """La trasera va DENTRO de las bandas y delante de ella no hay nada a
    distancia fija.

    ES LA REGLA QUE EL MARCO DE LA MANANA ROMPIA. Schaeffer manda el PMMA de 8
    a +-1.2, y el marco pinzaba la trasera entre dos chapas a 8.00 justos: con
    una plancha de 9.2 la banda asomaba 1.2 del plano trasero, con una de 6.8
    el M3 la hundia. Es la ranura de ancho fijo que el postmortem del case
    prohibe (spec 26-08 s3). Con la banda estructural la trasera se atornilla
    a la banda y la tolerancia se va hacia dentro, como en el costado -- si
    no hay NADA fijo en la franja tol + 0.5 delante de su cara interior.

    Cuatro cosas: (1) esa franja esta vacia dentro de la huella de la trasera
    -- ahi cayo la pata trasera del marco, que se retiro por esto --; (2) la
    meseta cubre su canto de arriba hasta el plano trasero; (3) el pie del
    talon esta bajo su canto de abajo; (4) las dos muescas de esquina libran
    la brida del miembro alto, que pasa por debajo, con medio milimetro."""
    railes, planchas, _ = _cajas_solidas(p)
    tr = next(c for c in planchas if c[0] == "piel_trasera")
    lados = [c for c in planchas if c[0].startswith("piel_trasera lado")]
    x_tr, y0, y1 = tr[1], tr[3], tr[4]
    z0, z1 = lados[0][5], lados[1][6]
    franja = _tol_pmma(p) + 0.5
    for c in railes + planchas:
        if c[0].startswith("piel_trasera"):
            continue
        en_franja = c[2] > x_tr - franja + 1e-9 and c[1] < x_tr - 1e-9
        en_huella = c[4] > y0 + 1e-9 and c[3] < y1 - 1e-9 \
            and c[6] > z0 + 1e-9 and c[5] < z1 - 1e-9
        if en_franja and en_huella and not c[0].startswith("brida "):
            raise AssertionError(
                f"'{c[0]}' ocupa x={c[1]:.2f}..{c[2]:.2f} y la trasera acaba en "
                f"x={x_tr:.2f}: esta a {x_tr - c[2]:.2f} de su cara interior, "
                f"dentro de los {franja:.2f} (tolerancia {_tol_pmma(p):.1f} + 0.5) "
                f"que una plancha mas gruesa del lote necesita. Nada fijo "
                f"delante del acrilico")
    P = _vertices(p)
    meseta = next(c for c in railes if c[0] == "trasero alto meseta")
    assert meseta[2] >= P[6][0] - 1e-9 and meseta[3] <= y1 + p["hol_piel"] + 1e-9, (
        f"la meseta llega a x={meseta[2]:.2f} y la trasera acaba en y={y1:.2f}: "
        f"queda canto de PMMA sin tapar arriba")
    pie = next(c for c in railes if c[0] == "talon pie")
    assert abs(pie[4] - y0) < 1e-9 and pie[2] >= tr[2] - p["t_costilla"] - 1e-9, (
        f"la trasera arranca en y={y0:.2f} y el pie del talon acaba en "
        f"{pie[4]:.2f}: no apoya en el")
    mz, my = _muesca_trasera(p)
    for b in _cajas_brida(p, z0 - p["hol_piel"], z1 + p["hol_piel"]):
        L = int(b[0][-1])
        lado = lados[L]
        # la brida vive en la rebanada z0..z0+t junto a la cara del anillo y
        # la muesca tiene que cubrirla en z y dejarle 0.5 en y
        dentro_z = (b[6] <= lado[6] + 1e-9) if L == 0 else (b[5] >= lado[5] - 1e-9)
        assert dentro_z, (
            f"la muesca de esquina de la trasera ({mz:g} de honda) no cubre la "
            f"brida '{b[0]}' (z={b[5]:.2f}..{b[6]:.2f})")
        assert lado[4] <= b[3] - 0.5 + 1e-9, (
            f"la muesca de la trasera llega a y={lado[4]:.2f} y la brida "
            f"arranca en {b[3]:.2f}: hacen falta 0.5 de aire")
    print(f"trasera dentro: {x_tr - max(c[2] for c in railes + planchas if c[2] < x_tr and not c[0].startswith('piel_trasera')):.2f} "
          f"mm libres delante de su cara interior (piden {franja:.2f}); canto de "
          f"arriba bajo la meseta, canto de abajo sobre el pie del talon; muescas "
          f"de esquina de {mz:g} x {my:g}")


def guarda_marco_ventana(p: dict[str, float]) -> None:
    """El marco de la ventana: ocho patas, el canto donde toca, y la trasera
    aguanta sin tornillo.

    Lo que mide, en orden: (1) el canto exterior de cada pata -- a la silueta
    en las tres filas, retirado t_costilla + hol_piel bajo cada chapa,
    retirado banda + trasera + tolerancia + 0.5 detras --; (2) que pise 6 de
    acrilico mas alla de la ventana; (3) que la pata trasera, que no lleva
    tornillo porque en la franja trasera no cabe uno, aguante el empujon de
    carga_mano como viga empotrada entre las patas de arriba y de abajo con
    menos de 1 mm de flecha (el acrilico necesita 3 para salirse del
    rebaje); (4) que los dos pasos de la brida queden a 1.5 D del canto
    retirado de la meseta -- es lo que puso el retiro en 1.65 y no en 2 --;
    (5) que la muesca de la brida deje pata entera debajo -- es lo que puso
    brida_ancho en 14.5. Los agujeros contra el canto de su pata van en
    guarda_anclajes()."""
    patas = _marco_ventana(p)
    por = {q["nombre"]: q for q in patas}
    rm, rmt = _retiro_marco(p), _retiro_marco_trasera(p)
    for nm in ("chaflan", "frente", "meseta", "suelo"):
        assert abs(por[nm]["retiro"] - rm) < 1e-9, nm
    for nm in ("cara_inf", "valle", "cara_sup"):
        assert por[nm]["retiro"] == 0.0, nm
    assert abs(por["trasera"]["retiro"] - rmt) < 1e-9
    sombra = p["marco_fondo"] - p["cara_anillo"]
    assert sombra >= 6.0 - 1e-9, (
        f"el marco pisa {sombra:.2f} mm de acrilico mas alla de la ventana; el "
        f"tope pide 6 (era lo que pisaban las placas)")
    # la pata trasera como viga: ancho fondo - retiro, canto t_placa, flexion
    # en z. Empotrada abajo en la pata del suelo y APOYADA arriba: la muesca
    # de la brida deja en la esquina trasera-alta un cuello de marco_fondo -
    # b_muesca de ancho que no empotra, solo sostiene. Viga empotrada-apoyada
    # con carga al centro: FL^3/(107 EI). El acrilico necesita 3 mm para
    # salirse del rebaje; se piden menos de 2.
    q = por["trasera"]
    b, h, L = p["marco_fondo"] - rmt, p["t_placa"], q["s1"] - q["s0"]
    I = b * h ** 3 / 12
    flecha = p["carga_mano"] * L ** 3 / (107 * E_ALUMINIO * I)
    assert flecha <= 2.0, (
        f"la pata trasera del marco ({b:.2f} x {h:g}, {L:.1f} de largo, sin "
        f"tornillo) cede {flecha:.2f} mm con {p['carga_mano']:.0f} N: mas de 2")
    minimo = 1.5 * p["d_M4_paso"]
    for c in _bridas(p)[0]["m4"]:
        d_canto = p["dist_rosca_ciega"] - rm
        assert d_canto >= minimo - 1e-9, (
            f"el paso de la brida en el marco cae a {d_canto:.2f} del canto "
            f"retirado de la meseta y pide {minimo:.2f}: baja el retiro o sube "
            f"dist_rosca_ciega")
    s_mu, b_mu = por["meseta"]["muesca"]
    entera = p["marco_fondo"] - b_mu
    assert entera >= 8.0, (
        f"bajo la muesca de la brida quedan {entera:.2f} mm de pata en la "
        f"meseta; con menos de 8 la esquina trasera-alta del marco es un cuello. "
        f"Baja brida_ancho")
    print(f"marco de la ventana: {len(patas)} patas de {p['t_placa']:g} hasta "
          f"{p['marco_fondo']:g} de la silueta; canto a la silueta en las filas, "
          f"retirado {rm:.2f} bajo la chapa y {rmt:.2f} en la trasera; pisa "
          f"{sombra:g} de acrilico en los siete tramos")
    print(f"  pata trasera {b:.2f} x {h:g} sin tornillo: {flecha:.2f} mm con "
          f"{p['carga_mano']:.0f} N; muesca de la brida de {b_mu:.2f} deja "
          f"{entera:.2f} de pata")


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

    # LA VENTANA, no la boca (2026-08-29): sin bahia, la fila cabe o no cabe
    # entre el barrido del riel del valle de abajo y la esquina del de arriba.
    # Lo que sobre es paso_horizontal de mas: cada mm de valle es un mm de
    # fondo de aparato, y hoy sobran los 3 que ocupaban las dos alas.
    P = _vertices(p)
    cr = _centros_rail(p, P)
    x0, x1 = _ventana_valle(p, P, cr)
    pide = S + p["rail_er_alto"]
    sobra = (x1 - x0) - pide
    assert sobra >= -0.01, (
        f"la ventana del valle mide {x1 - x0:.2f} y la fila 1U pide "
        f"{pide:.2f} (separacion {S:.2f} + el alto de un riel). Se gobierna "
        f"con paso_horizontal, el largo del tramo plano del valle")

    hp_1u = round(p["largo_riel"] / p["hp"])
    hp_3u = round(p["largo_riel"] / p["hp"])
    assert hp_1u == hp_3u, (
        f"la fila 1U trae {hp_1u} HP y las de 3U {hp_3u}: cruzan el mismo case "
        f"entre las mismas dos costillas, asi que es el mismo numero")

    # Debajo del riel no hay bandeja: el tile cuelga en el interior, como los
    # modulos 3U. Lo que tiene debajo es la tabla, a esta altura.
    c1u = _centros_rail_1u(p, P, cr)
    y_riel = c1u[0][1] - _he_er(p, 90.0)[1]
    print(f"fila 1U: panel {H:.2f} (Intellijel), railes a {S:.2f} entre centros "
          f"-- cuadra al centesimo con los {S_1U_INTELLIJEL:.2f} publicados")
    print(f"  {hp_1u} HP a paso {p['hp']:.2f}, ventana de {x1 - x0:.2f} para "
          f"{pide:.2f} de fila (sobran {sobra:.2f}); el riel baja hasta "
          f"y = {y_riel:.1f} y debajo hay {y_riel:.0f} mm hasta la tabla")




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
                  + _caras_miembro(p, miembros) + planchas
                  # LA NARIZ ENTERA (2026-08-29): es fija y la fila de abajo
                  # pasa por encima al abrir. Cajas conservadoras.
                  + _cajas_nariz_barrido(p))
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
    # el pie y el frente de la nariz entran por railes Y por el barrido
    vistos: set[tuple] = set()
    obstaculos = [c for c in obstaculos if not (c in vistos or vistos.add(c))]
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
    """La meseta del remate -- el ala del miembro trasero alto, no una tapa
    aparte del techo -- se reparte entera entre tres piezas, ni mas ni menos.

    La meseta mide marco_remate y hay que repartirla ENTERA entre tres cosas.
    En params.scad no se pueden escribir expresiones, o sea que la relacion se
    mantiene A MANO y por eso hace falta una puerta: mover una sin mover las
    otras deja la meseta abierta o una pieza asomando por el plano trasero, y
    ninguna de las dos se ve en un DXF plano.

    ERAN DOS SUMANDOS HASTA EL 2026-08-27, CUATRO HASTA EL 29 Y TRES DESDE
    ENTONCES, porque la meseta cambio de dueno dos veces. Antes era una plancha
    de acrilico apoyada encima del larguero y de la trasera, medida desde el
    plano trasero. Ahora es el ALA del miembro alto, y un ala se mide desde su
    doblez -- la cara trasera del miembro --, asi que se queda t_piel corta por
    detras. El reparto es:

        prof_sup              la meseta, o sea el ala del miembro alto, del
                              doblez al PICO.
        t_piel                lo que la trasera se mete por debajo del ala
                              del marco. Fue el CANTO DE ARRIBA DE LA TRASERA
                              hasta el 2026-08-29 -- 8 mm de acrilico visto en
                              el pico del case, que es lo que abrio #234 -- y
                              hoy es el ala B de marco_trasera_sup, que se lo
                              tapa entero y muere contra el doblez de la
                              meseta.
        t_costilla            el espesor de ese marco: lo que la trasera se
                              rehunde para que su cara vista quede a ras del
                              plano trasero.

    EL INSET MURIO EL 2026-08-29. Llevaba escrito que era "lo unico que deja
    abrir la tapa de arriba" con una tabla (retiro 0 -> 13.2 grados) medida
    cuando la meseta era ACRILICO DE 8 apoyado en el riel. Con la chapa de 1.5
    la cara de abajo de la meseta queda a 18.9 mm del eje y nada de lo que
    gira pasa de 16.2: se corrio guarda_tapa() con la meseta en el pico y la
    fila de arriba siguio abriendo 121.5 grados. Asi que la meseta LLEGA AL
    PICO -- el reparto son tres sumandos -- y lo que asomaba en esos 13 mm, el
    riel-eje desnudo, queda tapado. El retorno que dobla en el pico es cosa de
    guarda_retorno_meseta()."""
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


# Margen radial entre lo que gira sobre el riel-eje de la fila de arriba (el
# canto alto de su panel, a 16.18 del eje) y la esquina interior del retorno
# de la meseta, que es fijo. Medio milimetro: la tolerancia de un doblez.
MARGEN_BARRIDO_RETORNO = 0.5


def _bd_angulo(p: dict[str, float], ang: float) -> float:
    """Bend deduction de un doblez de `ang` grados en la chapa de los
    miembros. A 90 da lo mismo que _bd_miembro(): SB = (r + t) tan(a/2),
    BA = a (r + k t) en radianes, BD = 2 SB - BA. Gemela de doblez_bd()."""
    r, t = p["radio_doblez_costilla"], p["t_costilla"]
    a = math.radians(ang)
    return 2 * (r + t) * math.tan(a / 2) - a * (r + p["k_factor"] * t)


def _retorno_meseta(p: dict[str, float]) -> dict:
    """El retorno de la meseta: sus cuatro esquinas en el perfil y su caja.

    Dobla en el pico (P4) y baja retorno_meseta por la cara de arriba, con el
    espesor hacia dentro. El doblez es de 90 - angulo_superior: lo que esa cara
    se aparta de la horizontal de la meseta. GEMELA del retorno en
    miembro_alto() y miembro_alto_2d()."""
    P = _vertices(p)
    a = math.radians(p["angulo_superior"])
    d, n = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
    r, t = p["retorno_meseta"], p["t_costilla"]
    q = [P[4],
         (P[4][0] - d[0] * r, P[4][1] - d[1] * r),
         (P[4][0] - d[0] * r + n[0] * t, P[4][1] - d[1] * r + n[1] * t),
         (P[4][0] + n[0] * t, P[4][1] + n[1] * t)]
    xs, ys = [e[0] for e in q], [e[1] for e in q]
    return {"esquinas": q, "esquina_interior": q[2],
            "doblez": 90.0 - p["angulo_superior"],
            "caja": ("trasero alto retorno", min(xs), max(xs), min(ys), max(ys))}


def guarda_retorno_meseta(p: dict[str, float]) -> None:
    """El retorno de la meseta tapa el riel-eje sin estorbar a la tapa.

    Lo que gira en la fila de arriba gira sobre el M4 de su riel de arriba
    (guarda_tapa), y el punto que mas se aleja de ese eje cerca del pico es el
    CANTO ALTO DEL PANEL: 16.18 mm. A 1.5 mm bajo la cara -- la cara interior
    de una chapa de 1.5 puesta a ras -- ese circulo llega hasta s = 149.4 de
    los 155 de la cara. El retorno es FIJO y tiene que quedarse fuera del
    circulo con margen: se mide la distancia radial de su esquina interior al
    eje contra el radio del canto del panel.

    Y por eso queda una linea de sombra sobre el panel, y se imprime: el labio
    del riel (2 mm, a 1.6 de profundidad) mas el aire hasta el retorno. Menos
    que eso no lo permite el barrido, salvo con un liston mecanizado de cara
    interior concava concentrica al eje -- que no es esta pieza."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    a = math.radians(p["angulo_superior"])
    d = (math.sin(a), math.cos(a))
    L = p["alto_cara_sup"]
    s_panel = p["inset_sup_valle"] - p["inset_er"] + p["alto_panel_sup"]
    canto = (P[3][0] + d[0] * s_panel, P[3][1] + d[1] * s_panel)
    r_canto = math.dist(canto, cr[3])
    ret = _retorno_meseta(p)
    r_esq = math.dist(ret["esquina_interior"], cr[3])
    margen = r_esq - r_canto
    assert margen >= MARGEN_BARRIDO_RETORNO, (
        f"el retorno de la meseta baja {p['retorno_meseta']:g} mm por la cara "
        f"de arriba y su esquina interior queda a {r_esq:.2f} del eje de la "
        f"tapa; el canto alto del panel gira a {r_canto:.2f}. Margen "
        f"{margen:+.2f} contra {MARGEN_BARRIDO_RETORNO:.2f}: el panel choca "
        f"con el retorno al abrir. Acortar retorno_meseta")
    s_ret = L - p["retorno_meseta"]
    s_riel = L - p["inset_sup_remate"] + p["rail_er_alto"] / 2
    assert s_ret > s_riel, (
        f"el retorno acaba en s = {s_ret:.2f} y la cara del riel-eje llega "
        f"hasta {s_riel:.2f}: una pieza fija encima de un riel que gira")
    print(f"retorno de la meseta: {p['retorno_meseta']:g} mm por la cara de "
          f"arriba, doblez de {ret['doblez']:g}; esquina interior a "
          f"{r_esq:.2f} del eje contra {r_canto:.2f} del canto del panel "
          f"(margen {margen:.2f})")
    print(f"  linea de sombra sobre el panel: {s_ret - s_panel:.2f} mm "
          f"({s_riel - s_panel:.2f} de labio del riel + {s_ret - s_riel:.2f} "
          f"de aire)")


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
            "m4_x": c + p["nariz_pie"] - 1.5 * p["d_M4_paso"],
            "m4_z": [p["t_anillo"] + au * f for f in (0.25, 0.5, 0.75)],
            "largo": au - 2 * p["hol_piel"], "desarrollo": desarrollo,
            "z0": z0, "z1": p["ancho_total"] - z0}


def _cajas_nariz(p: dict[str, float]) -> list[Caja]:
    """El pie y el frente de la nariz como cuerpos, alineados a ejes: son los
    que pueden pelearse con algo en 3D (clips, chasis, placas). El tramo de
    cara y el chaflan van girados y los mide guarda_nariz() contra lo suyo."""
    nz = _nariz(p)
    c, t = p["chaflan_nariz"], p["t_costilla"]
    return [("nariz pie", c, c + p["nariz_pie"], 0.0, t, nz["z0"], nz["z1"]),
            ("nariz frente", 0.0, t, c, p["alto_frontal"], nz["z0"], nz["z1"])]


def _cajas_nariz_barrido(p: dict[str, float]) -> list[Caja]:
    """La nariz entera como obstaculos AABB del barrido de la fila de abajo:
    conservador (la caja de un tramo girado es mayor que el tramo), y sin
    falso positivo comprobado: lo que gira sale por la cara POR ENCIMA del
    tramo de cara, no a traves de su caja."""
    nz = _nariz(p)
    c = p["chaflan_nariz"]
    xs, ys = [q[0] for q in nz["cara"]], [q[1] for q in nz["cara"]]
    return _cajas_nariz(p) + [
        ("nariz chaflan", 0.0, c, 0.0, c, nz["z0"], nz["z1"]),
        ("nariz cara", min(xs), max(xs), min(ys), max(ys), nz["z0"], nz["z1"])]


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
      3. la banda se para DEBAJO de la cara del riel con al menos 1 mm de aire
         (la linea de sombra): el riel se mueve y la nariz no.
      4. EL BARRIDO: la fila de abajo gira sobre el riel del valle y al abrir
         las esquinas del riel del frente salen por la cara de abajo. Se
         calcula donde cruza cada una la cara interior de la nariz (a t de
         profundidad) y se exige que sea 1.5 mm por encima de su canto alto.
         Es la misma leccion de guarda_tapa(): holgado parado y no girando.
      5. los M4 del pie: fuera de la zona del doblez del chaflan (setback +
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
    s_riel = p["inset_inf_frente"] - p["rail_er_alto"] / 2
    aire = s_riel - nz["s_top"]
    assert aire >= 1.0, (
        f"la nariz sube hasta s = {nz['s_top']:.2f} por la cara de abajo y la "
        f"cara del riel del frente arranca en {s_riel:.2f}: {aire:.2f} de aire "
        f"contra 1.0. Una pieza fija encima de un riel que gira")
    # EL BARRIDO. Cada esquina del riel del frente, girando sobre cr[1], cruza
    # la cara interior de la nariz (profundidad t) en algun s: el de la
    # esquina que cruza mas abajo es el que manda.
    a = math.radians(p["angulo_inferior"])
    d, n = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
    eje = cr[1]
    se = (eje[0] - P[1][0]) * d[0] + (eje[1] - P[1][1]) * d[1]
    qe = (eje[0] - P[1][0]) * n[0] + (eje[1] - P[1][1]) * n[1]
    peor = float("inf")
    for x, y in _esquinas_er(p, cr[0], p["angulo_inferior"]):
        r = math.hypot(x - eje[0], y - eje[1])
        dq = qe - t
        if r > abs(dq):
            peor = min(peor, se - math.sqrt(r * r - dq * dq))
    margen = peor - nz["s_top"]
    assert margen >= 1.5, (
        f"al abrir la fila de abajo, una esquina del riel del frente sale por "
        f"la cara en s = {peor:.2f} y la nariz llega hasta {nz['s_top']:.2f}: "
        f"{margen:.2f} de margen contra 1.5. Holgada parada y no girando")
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
          f"{nz['s_top']:.2f} de la cara de abajo; el riel sale girando por "
          f"s = {peor:.2f} (margen {margen:.2f})")
    print(f"  linea de sombra: {aire:.2f} de aire + "
          f"{p['inset_inf_frente'] - p['inset_er'] - s_riel:.2f} de labio del "
          f"riel bajo el panel; desarrollo {nz['largo']:.2f} x "
          f"{nz['desarrollo']:.2f}, {len(nz['m4_z'])} M4 a la tabla")


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
    # SAT (72 mm de margen) sino la FILA 1U dentro de su ventana, que lo mide
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
    libre_1 = _talon(p)["x_pie"] + p["vuelo_zocalo"] - hol
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
    # tabla lo cruza guarda_zocalo() en check_dxf.
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
    guarda_marco_ventana(p)
    guarda_miembro_alto(p)
    guarda_talon(p)
    guarda_trasera_dentro(p)
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
    guarda_puentes_ventilacion(p)
    guarda_parametros_vivos(p)
    guarda_escalon(p)
    guarda_tapa(p)
    guarda_remate(p)
    guarda_retorno_meseta(p)
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
    # guarda_costado() vive alli y no aqui.
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
