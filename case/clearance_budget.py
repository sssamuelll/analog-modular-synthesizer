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
    # el largo del riel por casualidad aritmetica. Con la holgura de montaje
    # metida en ese hueco, un literal se desincroniza al primer cambio y el
    # sintoma es un riel que no entra.
    derivado = (p["largo_riel"] + p["hol_riel"]
                + 2 * p["t_costilla"] + 2 * p["t_cheek"])
    if "ancho_total" in p:
        raise SystemExit(
            f"params.scad: ancho_total volvio a ser un literal ({p['ancho_total']:.2f}). "
            f"Es DERIVADO desde el 2026-08-26: largo_riel + hol_riel + "
            f"2*t_costilla + 2*t_cheek "
            f"= {derivado:.2f}. Un literal aqui vuelve a esconder si el riel "
            f"cabe o no.")
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
        # EL HUECO ENTRE COSTILLAS, no entre acrilicos, desde el 2026-08-26.
        # Todo lo que vive dentro del case -- largueros, rieles, planchas -- va
        # de cara interna a cara interna, y esas caras dejaron de ser el
        # acrilico: son el ala de la costilla, que se le monta encima. Restar
        # solo t_cheek dejaria 2*t_costilla de hueco fantasma, y las planchas
        # crecerian 6.3 mm para llenar un sitio que ya esta ocupado.
        "ancho_util": (p["ancho_total"] - 2 * p["t_cheek"]
                       - 2 * p["t_costilla"]),
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


def _caja_remate(p: dict[str, float],
                 P: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Caja de la tapa de remate en el perfil: (x0, x1, y0, y1).

    Fue _esquinas_pestana() y devolvia CUATRO ESQUINAS porque la pieza iba
    girada con la cara de arriba -- una tira de canto pegada al Z-Rail. Desde
    el 2026-08-21 es una plancha HORIZONTAL sobre la meseta del techo,
    atornillada al larguero de remate trasero, asi que su caja vuelve a estar
    alineada con los ejes y las esquinas sobran."""
    return (P[4][0] + p["inset_remate_frente"], P[5][0],
            P[5][1] - p["marco_sup"], P[5][1])


def _x_chasis_frente(p: dict[str, float]) -> float:
    """Cara delantera del chasis del PSU.

    Cuelga del larguero TRASERO, a chasis_holgura_larguero, y de ahi hacia
    delante no hay nada: una sola cadena en un solo sentido. Estuvo escrita
    dentro de _centros_transversal() porque de ella colgaba `base delantera`,
    que se plantaba otra holgura por delante del chasis. Muerta esa barra el
    2026-08-27, la cadena se acaba en el chasis y quien la necesita es ch_pos()
    -- que la calculaba al reves, sumando vuelo + rail + holgura desde el canto
    de la plancha, y solo daba lo mismo por como estaba puesta la barra."""
    x_tr = fondo(p) - p["rail"] / 2 - p["t_piel"]
    return ((x_tr - p["rail"] / 2) - p["chasis_holgura_larguero"]
            - _chasis(p)["tapa_y"])


def _centros_transversal(p: dict[str, float], P: list[tuple[float, float]],
                        cr: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """4 centros de larguero de esqueleto, misma formula que
    centros_transversal() en sam17_case.scad. Fueron 7 (con un "zocalo superior"
    que se retiro), luego 6, 7 otra vez, y 8 al entrar el remate trasero. El
    2026-08-21 bajaron a 5 -- junto al plano trasero quedan DOS y no cinco -- y
    el 2026-08-25 a CUATRO, al retirarse el entrepiso delantero: era el unico
    que no sostenia ninguna plancha, y a su misma altura ya ata el del valle.
    Entrepiso trasero, repisa y remate superior nacieron cada uno por una pieza
    -- la bandeja de entrepiso, la piel superior y la tira de remate pegada de
    canto -- y ninguna de las tres existe ya. Seguian ahi solo como filas de
    tornillo de la trasera, y una plancha continua de 8 atornillada arriba y
    abajo es mejor alma de cortante para esa cara que cinco barras sueltas."""
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
    y_ep = P[3][1] - p["t_valle"] - r
    # El larguero de base apoya en el SUELO, que desde el 2026-08-27 es la cara
    # de arriba de la tabla y esta en y=0. Su centro va en r, o sea su cara de
    # abajo a ras del plano del suelo. Estuvo en t_base + r mientras la bandeja
    # era una plancha DENTRO del case y el larguero montaba encima de ella. Al delantero lo coloca ahora el
    # riel de panel que le pasa por delante -- misma cuenta que x_ed, o sea
    # contra la ESQUINA del riel girado y no contra su centro. Estuvo en
    # alto_frontal/2 + r + 2, pegado al vertice, y ahi el riel se le montaba
    # encima en cuanto el vertice bajo.
    # El chasis del PSU se pega al larguero TRASERO y el delantero al chasis:
    # una sola cadena, x_tr -> chasis -> base delantera. Estuvo derivado del
    # riel de panel (x=49.68) y ahi hacia dos cosas malas a la vez: se leia
    # pegado al riel (4.00 mm clavados) y se metia en el envolvente de los
    # modulos de la fila de abajo. Ver la nota larga en el .scad -- el limitante
    # de verdad era el chasis, no el.
    y_bd = r
    # Los DOS largueros traseros comparten X, y por eso es UNA cota y no dos
    # copias: la cara donde apoya la trasera tiene que ser un plano. Se retira
    # t_piel del canto para que la plancha atornillada encima remate
    # EXACTAMENTE en el plano trasero. El de base estuvo 14 mm mas adelante
    # (- radio_perfil) y por ahi se colo el fallo que caza apoyo().
    x_tr = fondo(p) - r - p["t_piel"]
    return {"base trasera": (x_tr, y_bd),
            # valle: el unico que existe por una plancha y no por una union.
            # Centrado bajo la tapa para que los dos vuelos sean iguales, y de
            # paso ata los costados por la cintura.
            "valle": (sum(_x_valle(p, P, cr)) / 2, y_ep),
            # remate trasero: el QUINTO, del 2026-08-21. Le da a la tapa del
            # techo a que atornillarse -- antes iba PEGADA al Z-Rail porque ahi
            # arriba no habia otra cosa, y era la unica junta irreversible del
            # case. A ras del plano trasero, cara de arriba a marco_sup del
            # techo. No puede adelantarse: el barrido del Z-Rail se lo come.
            # Comparte X con el de base: la trasera le pasa por delante a los
            # dos, y entre ellos vuela 211.73 mm sin apoyo intermedio.
            "remate trasero": (x_tr, P[5][1] - p["marco_sup"] - r)}


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
# LAS TRANSVERSALES, y ya no se llaman "largueros de esqueleto". Cada una
# esta donde esta porque una pieza necesita una linea de apoyo AHI, y no como
# reticula generica -- por eso el censo va con el motivo escrito al lado y
# guarda_transversales() exige que el modelo diga exactamente esto.
#
# Lo canta un dict y no una lista: el 2026-08-27, al morir base delantera, doce
# indices numericos (ce[0], ce[1]...) se habrian corrido en silencio uno a uno.
MOTIVO_CT = {
    "base trasera": "arrinconada contra la cara interior de la trasera "
                    "(x=300.94) y el techo del suelo (y=8): dos caras, o sea "
                    "que ya es transversal de marco. Recibe la fila baja de "
                    "la trasera y la trasera de la bandeja",
    "valle": "sostiene la tapa del valle, que es la unica cara HORIZONTAL del "
             "case. Ningun riel la alcanza -- el de arriba se queda 4.00 mm "
             "corto y el de abajo 8.10 por debajo -- y el tramo del valle de "
             "la costilla es el UNICO sin ala, asi que tampoco hay repisa",
    "remate trasero": "misma esquina que base trasera pero arriba: a tope "
                      "contra la trasera y contra el canto bajo de remate_sup",
}
NOMBRES_CT = list(MOTIVO_CT)


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
    ce = _centros_transversal(p, P, cr)
    rail, t_cheek = p["rail"], p["t_cheek"]
    t_acr, hol = p["t_valle"], p["hol_piel"]
    ancho_total = p["ancho_total"]
    # LAS CARAS INTERNAS DEL CASE dejaron de ser el acrilico el 2026-08-26: el
    # ala de la costilla se le monta encima, y todo lo que vive dentro apoya
    # contra ELLA. Sin este termino las planchas se dibujan 2*t_costilla mas
    # anchas de lo que caben y solapes() no lo canta, porque una plancha que
    # invade una costilla que el modelo no dibuja no solapa con nada.
    z0 = t_cheek + p["t_costilla"]
    z1 = ancho_total - t_cheek - p["t_costilla"]

    angs = [p[k] for k in ANGS_CR]
    railes: list[Caja] = []
    for nm, c, ang in zip(NOMBRES_CR, cr, angs):
        # el riel gira -ang para calzar a ras de la cara, y su AABB no es
        # simetrico porque la seccion no es cuadrada (ver _he_er)
        hx, hy = _he_er(p, ang)
        railes.append((nm, c[0] - hx, c[0] + hx, c[1] - hy, c[1] + hy,
                       z0, z1))
    # La PESTANA superior: banda de acrilico sobre los ultimos marco_sup mm de
    # la cara de arriba, a ras por fuera y engordando t_cheek hacia dentro.
    # Aqui interesa que no se pise con el riel de arriba ni con el larguero de
    # remate, que viven justo debajo.
    rx0, rx1, ry0, ry1 = _caja_remate(p, P)
    planchas_extra = ("remate_sup", rx0, rx1, ry0, ry1,
                      z0, z1)
    for nm, c in ce.items():
        railes.append((nm, c[0] - rail / 2, c[0] + rail / 2,
                       c[1] - rail / 2, c[1] + rail / 2,
                       z0, z1))

    planchas: list[Caja] = [planchas_extra]
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
    # tapa_valle: a ras del plano del valle, igual que la de entrepiso, y con
    # una sola fila de M3 -- la del larguero del valle, que va centrado bajo
    # ella. Lo que la coloca en Y es lo mismo que obligo a subir
    # inset_inf_valle: su cara de abajo tiene que librar la esquina de arriba
    # del riel del valle de la cara inferior.
    x0_tv, x1_tv = _x_valle(p, P, cr)
    planchas.append(("tapa_valle", x0_tv, x1_tv,
                     P[3][1] - t_acr, P[3][1], z0, z1))
    # LAS DOS PESTANAS de la tapa, dobladas hacia abajo contra la costilla.
    # Van en `railes` y no en `planchas` a proposito: es la lista que solapes()
    # cruza contra todo, y una pestana que se echa encima del larguero del valle
    # o del riel de abajo no la caza nadie mas. (Y `planchas` la recorre
    # _sobres() para sacar envolventes de DXF, que aqui no aplica.)
    pv = _pv(p)
    x0_pv = ce["valle"][0] + rail / 2 + p["holgura_rail"]
    for lado, (za, zb) in enumerate(((z0, z0 + p["t_valle"]),
                                     (z1 - p["t_valle"], z1))):
        railes.append((f"pestana valle {lado}", x0_pv, x1_tv,
                       P[3][1] - p["pestana_valle"], P[3][1] - t_acr,
                       za, zb))
    filas += [("tapa_valle", "unica", "x", ce["valle"][0], "valle")]
    # piel_trasera: UNA sola plancha desde el 2026-08-21. Fueron dos, partidas
    # a la altura del entrepiso porque cada una se atornillaba a los dos
    # largueros de su piso; muerta esa bandeja la frontera dejo de existir. Va
    # en t_piel (8) y declara DOS filas, una por larguero trasero -- las de los
    # tres largueros de en medio se fueron con ellos el 2026-08-21.
    # Canto de abajo en el PLANO DEL SUELO (y=0), el mismo datum de la
    # bandeja de base. Estuvo en ce[1][1] - 15 y dejaba 3 mm de rebaje
    # corrido bajo la trasera -- ver guarda_piso(), assert 4.
    y0_pt = 0.0
    alto_pt = (P[5][1] - p["marco_sup"]) - y0_pt
    planchas.append(("piel_trasera", P[6][0] - p["t_piel"], P[6][0],
                     y0_pt, y0_pt + alto_pt, z0 + hol,
                     z1 - hol))
    filas += [("piel_trasera", "base", "y", ce["base trasera"][1],
               "base trasera"),
              ("piel_trasera", "remate", "y", ce["remate trasero"][1],
               "remate trasero"),
              ("remate_sup", "unica", "x", ce["remate trasero"][0],
               "remate trasero")]
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
    ce = _centros_transversal(p, P, cr)
    esqueleto = ce
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
    ce = _centros_transversal(p, P, cr)
    esqueleto = ce
    _, planchas, filas = _cajas_solidas(p)
    cajas = {c[0]: c[1:] for c in planchas}
    r = p["rail"] / 2
    fallos: list[str] = []
    por_placa: dict[str, list[tuple[str, float]]] = {}
    for placa, fila, eje, _coord, rail_decl in filas:
        if rail_decl not in esqueleto or placa not in cajas:
            continue                       # de eso ya se queja alineacion()
        sup = "y" if eje == "x" else "x"
        x0, x1, y0, y1, _z0, _z1 = cajas[placa]
        lo, hi = (x0, x1) if sup == "x" else (y0, y1)
        c = esqueleto[rail_decl][0 if sup == "x" else 1]
        hueco = lo - (c + r) if lo >= c else (c - r) - hi
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
    ce = _centros_transversal(p, P, _centros_rail(p, P))
    esqueleto = ce
    casos = (("valle", "x"), ("base trasera", "x"),
             ("base trasera", "y"), ("remate trasero", "y"))
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
    """9 railes + 4 planchas: ningun par se pisa en 3D, salvo los
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


def _rejilla_valle(p: dict[str, float]) -> tuple[int, float, float]:
    """Las ranuras de SALIDA, mismas cuentas que tapa_valle_2d()."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    ce = _centros_transversal(p, P, cr)
    xv = _x_valle(p, P, cr)
    largo = xv[1] - xv[0]
    y_esp = ce["valle"][0] - xv[0]
    campos = ((p["valle_margen"], y_esp - p["valle_espina"] / 2),
              (y_esp + p["valle_espina"] / 2, largo - p["valle_margen"]))
    paso = int(p["valle_paso_hp"])
    n_hp = round(p["largo_riel"] / p["hp"])
    ns = len(range(paso, int(n_hp) - paso + 1, paso))
    area = sum(_area_ranuras(ns, c[1] - c[0], p["vent_ancho_ranura"])
               for c in campos)
    return 2 * ns, campos[0][1] - campos[0][0], area


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
    ce = _centros_transversal(p, P, _centros_rail(p, P))
    f_base, f_tras = ce["base trasera"][1], ce["remate trasero"][1]
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
    P = _vertices(p)
    ce = _centros_transversal(p, P, _centros_rail(p, P))
    au = p["ancho_total"] - 2 * p["t_cheek"] - 2 * p["hol_piel"]
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
    ce = _centros_transversal(p, P, _centros_rail(p, P))
    au = p["ancho_total"] - 2 * p["t_cheek"] - 2 * p["hol_piel"]
    # y=0: el canto de abajo de la plancha, en el plano del suelo. Da igual
    # para el resultado -- se resta al formar f_base/f_tras y se vuelve a
    # sumar al devolver el centroide, asi que se cancela -- pero tiene que
    # decir lo mismo que el .scad o el dia que deje de cancelarse miente.
    y0_pl = 0.0
    f_base = ce["base trasera"][1] - y0_pl
    f_tras = ce["remate trasero"][1] - y0_pl
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
    n_val, largo_val, a_val = _rejilla_valle(p)
    P = _vertices(p)
    y_val = P[3][1] - p["t_valle"] / 2
    a_ond, y_ond = _ondas_trasera(p)
    a_sal = a_val + a_ond
    y_sal = (a_val * y_val + a_ond * y_ond) / a_sal

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
    print(f"  salida {a_sal:.0f} mm2 = {a_val:.0f} del valle ({n_val} ranuras) + "
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
    par maximo antes de fisura no esta medido". Treinta tornillos VISIBLES
    apretados a tacto sobre acrilico son treinta puntos de craquelado.

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
    print(f"apriete: 30 M3 a {p['par_m3']} N*m con arandela d{p['d_arandela']:g} "
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
    print(f"chaflan: {p['chaflan']} mm x 45 en toda arista vista "
          f"(techo por la plancha de {t_min:g} mm: {t_min/4:.2f})")


# La tapa del valle es de ALUMINIO desde el 2026-08-25. Modulo elastico: 69 GPa,
# que es comun a todos los aluminios y no depende de la aleacion. El limite
# elastico SI depende, y va conservador: 130 MPa es el Rp0.2 de un 5754 H22, la
# chapa corriente de corte. Un 6082-T6 da ~250 y aguantaria el doble; pedir la
# aleacion exacta es cosa del pliego, no de esta puerta. SUPUESTO DECLARADO.
E_ALUMINIO, RP02_ALUMINIO = 69000.0, 130.0
# Ancho sobre el que reparte una mano apoyada de canto. Es EL SUPUESTO QUE MAS
# MANDA en esta puerta -- con 50 mm la tension se dobla contra los 100 -- y por
# eso va conservador: el canto de la mano, no la palma abierta.
B_MANO = 50.0
# paso_junta_L() y sus constantes (AS_M3, TAU_M3, MU_ALU_SECO) vivieron aqui
# unas horas el 2026-08-26. Calculaban el paso de los M3 que cosian una tira de
# canto a la costilla, y su hallazgo era bueno: mandaba el DESLIZAMIENTO de la
# junta (34 mm) y no la resistencia del tornillo (109), porque una junta que
# desliza deja de trabajar como seccion sin romperse ni avisar.
#
# Se los llevo el plegado. La tira iba atornillada al CANTO de la costilla, y
# ese canto mide 3 mm mientras el agujero de paso de un M3 mide 3.4: el agujero
# era mas ancho que la pieza. Al pasar la costilla a chapa plegada el ala sale
# del propio material, y sin junta no hay cortante que transmitir, ni paso que
# calcular, ni 78 M3 que comprar. La cuenta queda en la spec del 2026-08-26 por
# si alguna vez vuelve una junta atornillada a este case.
def _seccion_L(t: float, b: float, c: float) -> tuple[float, float, float]:
    """Inercia, fibra mas alejada y momento estatico del ala separada.

    Seccion en L flexionando FUERA del plano de la costilla, que es su
    direccion floja: el ala 1 es la plancha (ancho b DENTRO del plano, espesor
    t fuera) y el ala 2 es la tira de canto (ancho c fuera del plano, espesor
    t). Q es el momento estatico de la TIRA respecto al eje neutro, o sea
    exactamente lo que la junta entre las dos tiene que transmitir para que
    trabajen como una sola seccion en vez de como dos pletinas sueltas.

    NO VALE PARA FLEXION EN EL PLANO. En su plano la costilla es un marco y
    trabaja a traccion y compresion en los tramos, que es un orden de magnitud
    mas rigido; quien llame a esto para ese modo saca un numero pesimista y no
    se entera."""
    A1, y1 = b * t, t / 2.0
    A2, y2 = c * t, t + c / 2.0
    A = A1 + A2
    yc = (A1 * y1 + A2 * y2) / A
    I = (b * t ** 3 / 12 + A1 * (y1 - yc) ** 2) + (t * c ** 3 / 12 + A2 * (y2 - yc) ** 2)
    return I, max(yc, (t + c) - yc), A2 * (y2 - yc)


def autocomprobacion_L() -> None:
    """La seccion en L de la costilla, verificada a mano antes de escribirla.

    Para t=3, b=20, c=12 -- los valores de la spec 2026-08-26 SS4.1:

        ala 1 (la plancha): A1 = 20*3 = 60      y1 = 1.5
        ala 2 (la tira):    A2 = 12*3 = 36      y2 = 3 + 6 = 9
        A = 96 ; yc = (60*1.5 + 36*9)/96 = 414/96 = 4.3125
        I = (20*27/12   + 60*2.8125^2) + (3*1728/12 + 36*4.6875^2)
          = (45         + 474.609375)  + (432       + 791.015625)
          = 1742.625
        Q = A2*(y2 - yc) = 36*4.6875 = 168.75
        ymax = max(4.3125, 15 - 4.3125) = 10.6875

    LA CUENTA DE ARRIBA SE HIZO MAL LA PRIMERA VEZ y esta puerta la caza: el
    termino 36*4.6875^2 se escribio 790.92 cuando son 791.015625, y de ahi un I
    de 1742.53 que no existe. Es exactamente para esto que la autocomprobacion
    va ANTES que la funcion -- si se escribe despues, uno copia la salida del
    codigo y la puerta deja de verificar nada.
    """
    I, ymax, Q = _seccion_L(3.0, 20.0, 12.0)
    assert abs(I - 1742.625) < 0.001, I
    assert abs(Q - 168.75) < 0.01, Q
    assert abs(ymax - 10.6875) < 0.001, ymax


def paso_junta_L(p: dict[str, float], t: float, b: float,
                 c: float) -> tuple[float, float]:
    """Paso maximo de tornillo en la junta costilla-tira, por dos criterios.

    EL QUE MANDA ES EL SEGUNDO, y esa es toda la trampa de este calculo. Quien
    dimensione la junta por RESISTENCIA pone tornillos cada 109 mm; a ese paso
    la junta desliza en la holgura del agujero antes de que el tornillo llegue
    a trabajar, las dos alas flexan por separado y la costilla deja de ser una
    L. O sea que el error no da una costilla un poco peor: da la fila "sin
    tira" de la spec SS4.1, la que no pasa a NINGUN espesor y a 3 mm ademas
    fluye a 257 MPa. Y no avisa -- una junta que desliza no se rompe.

        q = V*Q/I     flujo de cortante en la junta, N/mm
        V = P/2       cortante de una biempotrada con la carga al centro

    Criterio 1, RESISTENCIA: el M3 a cortante, AS_M3 * TAU_M3.
    Criterio 2, NO DESLIZAMIENTO: friccion mu*N, con N la precarga del par.
    N ~ T/(0.2*d) es la relacion par-precarga de manual, con 0.2 de factor de
    apriete para ROSCA SECA -- y seca es como va: engrasarla mete un 30 % mas
    de precarga con el mismo par, que en par_m3 es un peligro y aqui seria un
    regalo. No se cuenta ese regalo."""
    I, _, Q = _seccion_L(t, b, c)
    q = (p["carga_mano"] / 2.0) * Q / I
    precarga = p["par_m3"] * 1000.0 / (0.2 * 3.0)      # N*m -> N*mm, d = 3
    return AS_M3 * TAU_M3 / q, MU_ALU_SECO * precarga / q


def _tramos_costilla(p: dict[str, float]) -> list[tuple[str, float, bool, bool]]:
    """Los 7 tramos del contorno: largo, si llevan ala, y si su vertice gira mal.

    QUE UN TRAMO LLEVE ALA SE DERIVA, no se elige: la lleva si como pletina
    plana no pasa el techo de flecha. Salen cuatro -- las dos caras inclinadas,
    la trasera y el suelo -- y se quedan sin ella el frente (19 mm), el valle
    (60) y la meseta (50), que sobran de largo para necesitarla.

    El bool de vertice marca si el giro EN EL FINAL de ese tramo es CONCAVO. En
    un contorno plegado, una esquina convexa se resuelve con corte de alivio en
    V -- practica normal de chapa, se dibuja en el desarrollo --, pero una
    CONCAVA hace que las dos alas vecinas diverjan y quede hueco. El perfil
    tiene seis convexas y una concava: P3, el fin del valle."""
    P = _vertices(p)
    n = len(P)
    nombres = ["frente bajo", "cara inferior", "el valle", "cara superior",
               "meseta de remate", "la trasera", "el suelo"]
    I_pletina = p["ala_costilla"] * p["t_costilla"] ** 3 / 12
    out = []
    for i in range(n):
        a, b, c = P[i], P[(i + 1) % n], P[(i + 2) % n]
        largo = math.hypot(b[0] - a[0], b[1] - a[1])
        f_pletina = p["carga_mano"] * largo ** 3 / (192 * E_ALUMINIO * I_pletina)
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        concavo = (ux * vy - uy * vx) > 0
        out.append((nombres[i], largo, f_pletina > p["flecha_costado_max"],
                    concavo))
    return out


def plegado_costilla(p: dict[str, float]) -> tuple[float, float, float]:
    """Setback, bend allowance y vuelo del desarrollo, para 90 grados.

    Misma formula que ch_ba() del chasis, con los parametros de ESTA chapa:
    aluminio de 3 mm, no acero de 1.5. SB es lo que la linea de plegado se mete
    hacia DENTRO del contorno; el borde del desarrollo acaba sobresaliendo
    (ala_doblez - BD) del contorno de la pieza doblada."""
    sb = p["radio_doblez_costilla"] + p["t_costilla"]
    ba = math.pi / 2 * (p["radio_doblez_costilla"]
                        + p["k_factor"] * p["t_costilla"])
    return sb, ba, p["ala_doblez"] - (2 * sb - ba)


def bbox_desarrollo_costilla(p: dict[str, float]) -> tuple[float, float]:
    """Envolvente del DESARROLLO PLANO, derivada y no escrita a mano.

    El desarrollo es mas grande que la pieza doblada: cada tramo con ala saca
    un rectangulo por su normal EXTERIOR, y cuanto crece la envolvente depende
    de hacia donde mire ese tramo -- el suelo empuja en Y, la trasera en X, y
    las dos caras inclinadas reparten segun su angulo.

    GEMELA de costilla_ala() en el .scad. Si las dos se separan, revisar() lo
    canta como bbox fuera del sobre, que es justo para lo que sirve."""
    P = _vertices(p)
    n = len(P)
    _, _, vuelo = plegado_costilla(p)
    pts = list(P)
    for i, (_, _, ala, _) in enumerate(_tramos_costilla(p)):
        if not ala:
            continue
        a, b = P[i], P[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        pts += [(a[0] + nx * vuelo, a[1] + ny * vuelo),
                (b[0] + nx * vuelo, b[1] + ny * vuelo)]
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


def guarda_costilla(p: dict[str, float]) -> None:
    """La costilla aguanta que empujen el case de lado, tramo por tramo.

    ES LA PIEZA PORTANTE desde el 2026-08-26: el costado de acrilico paso a
    piel y no sostiene nada. El modo critico es fuera del plano de la costilla,
    que es su direccion floja -- en su plano es un marco y trabaja a traccion y
    compresion, un orden de magnitud mas rigido. Viga biempotrada porque las
    esquinas de un marco continuo lo son, con carga_mano al centro del tramo.

    ES CHAPA PLEGADA, y el ala sale del propio material. Fue a estar
    atornillada media hora: la tira iba al CANTO de la costilla, y ese canto
    mide 3 mm mientras el agujero de paso de un M3 mide 3.4. El agujero era mas
    ancho que la pieza.

    LO QUE ESTA PUERTA IMPIDE son tres cosas, y las tres callan:

    1. QUE ALGUIEN QUITE EL ALA por estetica. Sin ella la seccion es una
       pletina plana y no pasa a NINGUN espesor -- ni la de 6 mm; la de 3
       ademas fluye a 257 MPa.
    2. QUE UN TRAMO LARGO SE QUEDE SIN ALA. Que un tramo la lleve se DERIVA de
       si la necesita, no se elige a mano, y esta puerta comprueba las dos
       familias: los que la llevan como seccion en L, los que no como pletina.
    3. QUE UN ALA CRUCE UNA ESQUINA CONCAVA. Ahi las dos alas vecinas divergen
       y queda hueco -- no se puede plegar. El perfil tiene una sola esquina
       concava, P3 (fin del valle), y sale bien PORQUE el valle no lleva ala:
       pero eso es una coincidencia afortunada del calculo, no una garantia, y
       si un dia el valle se alarga hasta necesitarla habria que enterarse
       AQUI y no en el taller de plegado."""
    I_L, ymax_L, _ = _seccion_L(p["t_costilla"], p["ala_costilla"],
                                p["ala_doblez"])
    I_p = p["ala_costilla"] * p["t_costilla"] ** 3 / 12
    ymax_p = p["t_costilla"] / 2
    tramos = _tramos_costilla(p)
    con_ala = sum(1 for _, _, a, _ in tramos if a)
    for nombre, largo, ala, _ in tramos:
        I, ymax = (I_L, ymax_L) if ala else (I_p, ymax_p)
        flecha = p["carga_mano"] * largo ** 3 / (192 * E_ALUMINIO * I)
        sigma = (p["carga_mano"] * largo / 8) * ymax / I
        assert flecha <= p["flecha_costado_max"], (
            f"la costilla cede {flecha:.3f} mm en el tramo '{nombre}' de "
            f"{largo:.2f} mm {'CON' if ala else 'sin'} ala, y el techo son "
            f"{p['flecha_costado_max']:.2f}. Si acabas de tocar ala_doblez: "
            f"sin ella NINGUN espesor pasa en los tramos largos, ni el de 6 mm.")
        assert sigma <= RP02_ALUMINIO, (
            f"la costilla trabaja a {sigma:.1f} MPa en '{nombre}' y el Rp0.2 "
            f"del aluminio de chapa son {RP02_ALUMINIO:.0f}.")
    for i, (nombre, _, ala, concavo) in enumerate(tramos):
        siguiente = tramos[(i + 1) % len(tramos)]
        assert not (concavo and ala and siguiente[2]), (
            f"el ala cruza una esquina CONCAVA entre '{nombre}' y "
            f"'{siguiente[0]}': ahi las dos alas divergen y queda hueco, o sea "
            f"que no se puede plegar. Hay que interrumpir el ala en uno de los "
            f"dos, o esa esquina pide solape o soldadura.")
    sb, ba, vuelo = plegado_costilla(p)
    w, h = bbox_desarrollo_costilla(p)
    print(f"costilla: CHAPA PLEGADA de {p['t_costilla']:g}, ala de "
          f"{p['ala_doblez']:g} doblada a 90 en {con_ala} de {len(tramos)} "
          f"tramos (los otros {len(tramos)-con_ala} no la necesitan)")
    # ESTO ES LO QUE EL DXF NO SABE DECIR, y sin ello la pieza vuelve del
    # taller PLANA. Mismo caso que el chasis, que viaja con su plano de
    # plegado porque un corte no dice de donde doblar.
    print(f"  desarrollo {w:.2f} x {h:.2f} (la pieza doblada mide "
          f"{fondo(p):.2f} x {perfil(p)['alto_total']:.2f}); r interior "
          f"{p['radio_doblez_costilla']:g}, BA {ba:.3f}, BD {2*sb-ba:.3f}")
    print(f"  linea de plegado a {sb:.3f} mm HACIA DENTRO del contorno de la "
          f"pieza, y el desarrollo sobresale {vuelo:.3f} por fuera")
    print(f"  alivio cuadrado de {sb:.0f} x {sb:.0f} donde concurren dos alas "
          f"-- solo en P6, entre la trasera y el suelo")
    for nombre, largo, ala, concavo in tramos:
        I, ymax = (I_L, ymax_L) if ala else (I_p, ymax_p)
        f = p["carga_mano"] * largo ** 3 / (192 * E_ALUMINIO * I)
        print(f"  {nombre:<18} {largo:7.2f} mm  {'con ala' if ala else 'plana '}"
              f"  cede {f:.3f}{'   (su vertice gira CONCAVO)' if concavo else ''}")


def guarda_valle(p: dict[str, float]) -> None:
    """La tapa del valle aguanta que alguien se apoye en ella.

    NACE CON EL CAMBIO DE MATERIAL, y el numero que la justifica es la
    proporcion en voladizo: la tapa mide 66.5 mm de fondo y el larguero solo la
    toca 20, asi que el 70 % de la pieza vuela -- 23.24 mm a cada lado de una
    banda de apoyo continua.

    OJO CON EL MODO DE CARGA, que es donde este calculo se hizo mal primero: el
    larguero del valle corre los 528 mm ENTEROS, o sea que para carga hacia
    ABAJO la tapa apoya en una LINEA CONTINUA y no sobre los 5 M3. El vano
    entre tornillos no existe en este modo; los M3 solo trabajan cuando se tira
    de la tapa hacia arriba. Lo que flexa es el VOLADIZO TRANSVERSAL:

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
    ce = _centros_transversal(p, P, cr)
    x0, x1 = _x_valle(p, P, cr)
    xl = ce["valle"][0]
    r = p["rail"] / 2
    vol = max((xl - r) - x0, x1 - (xl + r))
    t = p["t_valle"]

    I = B_MANO * t ** 3 / 12
    flecha = p["carga_mano"] * vol ** 3 / (3 * E_ALUMINIO * I)
    sigma = 6 * p["carga_mano"] * vol / (B_MANO * t ** 2)
    p_fluye = RP02_ALUMINIO * B_MANO * t ** 2 / (6 * vol)

    assert sigma <= RP02_ALUMINIO, (
        f"la tapa del valle trabaja a {sigma:.1f} MPa con {p['carga_mano']:.0f} N "
        f"repartidos en {B_MANO:.0f} mm, y el limite elastico del aluminio de "
        f"chapa son {RP02_ALUMINIO:.0f}. Vuela {vol:.2f} mm a cada lado del "
        f"larguero: o sube t_valle, o hay que ensanchar el apoyo.")
    assert flecha <= p["flecha_costado_max"], (
        f"la tapa del valle cede {flecha:.2f} mm con {p['carga_mano']:.0f} N y "
        f"el techo son {p['flecha_costado_max']:.2f}. Es la unica cara "
        f"HORIZONTAL del case: la que se hunde bajo la mano se nota mas que "
        f"ninguna.")
    # El otro modo, que no rompe pero se siente: tirar de la tapa hacia arriba
    # entre dos M3. Aqui SI hay vano.
    paso = perfil(p)["ancho_util"] / 5
    f_arr = p["carga_mano"] * paso ** 3 / (48 * E_ALUMINIO * I)
    print(f"valle: tapa de ALUMINIO t={t:g}, vuela {vol:.2f} mm a cada lado del "
          f"larguero ({100*2*vol/(x1-x0):.0f} % del fondo)")
    print(f"  con {p['carga_mano']:.0f} N en {B_MANO:.0f} mm cede {flecha:.3f} mm "
          f"y trabaja a {sigma:.1f} MPa (Rp0.2 {RP02_ALUMINIO:.0f}, fluye a "
          f"{p_fluye:.0f} N); levantandola entre dos M3, {f_arr:.2f} mm")


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


def _pv_x(p: dict[str, float], ce: dict) -> float:
    """X del tornillo de la pestana. Lo mas lejos del vertice concavo P[3] que
    el larguero del valle deja."""
    return (ce["valle"][0] + p["rail"] / 2 + p["holgura_rail"]
            + 1.5 * p["d_M3_paso"])


def bbox_desarrollo_tapa(p: dict[str, float]) -> tuple[float, float]:
    """Envolvente del DESARROLLO de la tapa del valle, no de la pieza doblada.

    Crece 2*vuelo por el ancho: cada punta saca su pestana desplegada por fuera
    del contorno. Derivado y no escrito a mano -- si el .scad y esta cuenta se
    separan, el bbox se sale del sobre y check_dxf se entera."""
    P = _vertices(p)
    x0, x1 = _x_valle(p, P, _centros_rail(p, P))
    return (perfil(p)["ancho_util"] + 2 * _pv(p)["vuelo"], x1 - x0)


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
    ce = _centros_transversal(p, P, _centros_rail(p, P))
    au = p["ancho_total"] - 2 * p["t_cheek"] - 2 * p["hol_piel"]
    f_base = ce["base trasera"][1]
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
    print(f"  la sostiene una pieza fija atornillada al larguero de base "
          f"trasera, {lib0 + holgura_v - (f_base + p['rail'] / 2):.2f} mm mas "
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
    ce = _centros_transversal(p, P, cr)
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
    y0_pt = next(c[3] for c in planchas if c[0] == "piel_trasera")
    assert abs(y0_pt) < 1e-6, (
        f"la trasera no llega al suelo: su canto de abajo cae en "
        f"y={y0_pt:.2f} y el plano inferior del case es y=0, o sea un rebaje "
        f"corrido de {p['ancho_total'] - 2 * p['t_cheek']:.0f} x {y0_pt:.2f} x "
        f"{p['t_piel']:.0f} mm a lo largo de todo el canto trasero. La "
        f"plancha tiene que bajar hasta 0: la distancia al canto bajo la fila "
        f"de M3 CRECE al hacerlo (mas material alrededor del tornillo, no "
        f"menos), y las ondas y la rejilla no se mueven porque van derivadas "
        f"de f_base y f_tras, que son diferencias contra la base trasera")


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

    La meseta mide marco_remate. La tapa mide prof_sup y arranca
    inset_remate_frente por detras del pico, asi que los dos numeros tienen que
    sumar el primero. En params.scad no se pueden escribir expresiones, o sea
    que esta relacion se mantiene A MANO y por eso hace falta una puerta: mover
    marco_remate sin mover prof_sup deja la meseta abierta por detras o la tapa
    asomando por el plano trasero, y ninguna de las dos se ve en un DXF plano.

    El inset NO es estetica y no se toca a la ligera: es la unica razon por la
    que la tapa de la fila de arriba sigue abriendo. Ver su nota en params.scad.
    """
    suma = p["prof_sup"] + p["inset_remate_frente"]
    assert abs(suma - p["marco_remate"]) < 1e-9, (
        f"la tapa de remate no cuadra con la meseta: prof_sup + "
        f"inset_remate_frente = {suma:.2f} y marco_remate = "
        f"{p['marco_remate']:.2f}. Sobra o falta {suma - p['marco_remate']:+.2f} "
        f"mm. Los tres se mantienen a mano porque params.scad no admite "
        f"expresiones")
    print(f"remate: tapa de {p['prof_sup']:.0f} mm atornillada al larguero "
          f"trasero, retirada {p['inset_remate_frente']:.0f} del pico para que "
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
    r = p["rail"] / 2
    ce = _centros_transversal(p, P, cr)
    x_valle = ce["valle"][0]
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
    au = p["ancho_total"] - 2 * p["t_cheek"]
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
    rail = p["rail"]
    hol = p["chasis_holgura_larguero"]
    P_ = _vertices(p)
    ce_ = _centros_transversal(p, P_, _centros_rail(p, P_))
    libre_1 = (ce_["base trasera"][0] - rail / 2) + p["vuelo_zocalo"] - hol
    exige(pos_y >= 0 and pos_y + c["tapa_y"] <= libre_1,
          f"el chasis ocupa y={pos_y:.1f}..{pos_y + c['tapa_y']:.1f} de la "
          f"tabla y, con {hol:.0f} mm de holgura al larguero trasero, cabe "
          f"de 0.0 a {libre_1:.1f}")
    print(f"  cuelga por detras de 'base trasera' ("
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
    sube = p["rail"] / 2 - p["chasis_pie"]
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
    print(f"  cuelga de {int(p['chasis_anclajes'])} M5 a la ranura interior "
          f"del 2020 por su pared TRASERA, a {sube:.1f} mm del suelo de la "
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
    autocomprobacion_L()
    autocomprobacion_pv()
    # El .scad tiene su propia copia de E porque deriva alli que tramos de la
    # costilla llevan ala. Si las dos se separan, el DXF deja de ser la pieza
    # que este presupuesto verifica -- y el sintoma seria un desarrollo con el
    # ala en el tramo equivocado, que nadie mira a ojo.
    assert abs(p["E_aluminio"] - E_ALUMINIO) < 1, (
        f"params.scad dice E_aluminio = {p['E_aluminio']:.0f} y este modulo "
        f"usa {E_ALUMINIO:.0f}: la costilla se derivaria distinta en el .scad "
        f"que aqui.")
    canario_solapes(p)
    canario_alineacion(p)
    guarda_piso(p)
    guarda_costilla(p)
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
