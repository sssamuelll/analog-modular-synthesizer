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
    # el eje del M5 de punta esta a rail_er_eje del panel, no a rail/2: el riel
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


def _eje_visagra(p: dict[str, float],
                  P: list[tuple[float, float]]) -> tuple[float, float]:
    """Eje de giro de la tapa, misma formula que eje_visagra() en
    sam17_case.scad: en la ARISTA DEL TECHO, metido en la esquina EXTERIOR del
    vertice, con el nudillo tangente a las dos caras que la forman.

    Estuvo en la linea de tornillo de arriba del panel, que es donde va el riel.
    No caben los dos, y el que atornilla los modulos es el riel."""
    dx, dy = P[4][0] - P[3][0], P[4][1] - P[3][1]
    dl = math.hypot(dx, dy)
    dx, dy = dx / dl, dy / dl
    nf = (-dy, dx)                       # normal EXTERIOR de la cara del panel
    ux, uy = nf[0], nf[1] + 1.0          # bisectriz con la normal del techo
    ul = math.hypot(ux, uy)
    ux, uy = ux / ul, uy / ul
    k = (p["d_visagra"] / 2) / (ux * nf[0] + uy * nf[1])
    return (P[4][0] + ux * k, P[4][1] + uy * k)


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
    # ser un riel: el de verdad, el de arriba de la tapa. Contra su esquina de
    # ABAJO, que va girada con la cara, no contra su centro.
    por_riel = (cr[3][1] - _he_er(p, p["angulo_superior"])[1]
                - p["holgura_rail"] - r)
    return min(por_techo, por_cara, por_riel)


def _centros_esqueleto(p: dict[str, float], P: list[tuple[float, float]],
                        cr: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """6 centros de larguero de esqueleto, misma formula que
    centros_esqueleto() en sam17_case.scad. Eran 7: el septimo, "zocalo
    superior", se retiro con la plancha del zocalo cuando Samuel fijo DOS
    nodos en la esquina de abajo y no tres."""
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
            (fondo(p) - r, P[3][1] + 15)]


# Que inset gobierna cada punta de cada cara. El orden es el mismo que usa
# _centros_rail(): primero el de arranque, luego el de remate.
CARAS = {"inf": ("inset_inf_frente", "inset_inf_valle"),
         "sup": ("inset_sup_valle", "inset_sup_remate")}

# 4 railes de panel: dos por cara, como cualquier fila EUROrack. Los dos de la
# cara superior son TAPA -- no llevan M5 al costado, que si lo llevaran la tapa
# no abriria.
NOMBRES_CR = ["cara_inf frente", "cara_inf valle",
              "cara_sup valle", "cara_sup remate"]
ANGS_CR = ["angulo_inferior", "angulo_inferior",
           "angulo_superior", "angulo_superior"]
NOMBRES_CE = ["base delantera", "base trasera", "entrepiso delantero",
              "entrepiso trasero", "remate superior", "repisa"]


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
    # la cara de arriba, a ras por fuera y engordando t_cheek hacia dentro. Va
    # girada con la cara, asi que su AABB sale de las cuatro esquinas y no de un
    # semilado. Aqui interesa que no se pise con la bisagra ni con el larguero
    # de remate, que viven justo debajo.
    a2 = math.radians(p["angulo_superior"])
    d2 = (math.sin(a2), math.cos(a2))
    n2 = (d2[1], -d2[0])
    esq = [(P[3][0] + d2[0] * s + n2[0] * q, P[3][1] + d2[1] * s + n2[1] * q)
           for s in (p["alto_cara_sup"] - p["marco_sup"], p["alto_cara_sup"])
           for q in (0.0, p["t_cheek"])]
    planchas_extra = ("remate_sup",
                      min(e[0] for e in esq), max(e[0] for e in esq),
                      min(e[1] for e in esq), max(e[1] for e in esq),
                      t_cheek, ancho_total - t_cheek)
    # la bisagra entra en la misma bolsa que los railes: es un cuerpo continuo
    # de costado a costado y lo que interesa de ella aqui es que no se pise con
    # el larguero de remate ni con la piel superior.
    ev = _eje_visagra(p, P)
    rv = p["d_visagra"] / 2
    railes.append(("bisagra", ev[0] - rv, ev[0] + rv, ev[1] - rv, ev[1] + rv,
                   t_cheek, ancho_total - t_cheek))
    for nm, c in zip(NOMBRES_CE, ce):
        railes.append((nm, c[0] - rail / 2, c[0] + rail / 2,
                       c[1] - rail / 2, c[1] + rail / 2,
                       t_cheek, ancho_total - t_cheek))

    planchas: list[Caja] = [planchas_extra]
    filas: list[Fila] = []
    # bandeja_base: es el SUELO del case desde el 2026-08-17, de y = 0 a
    # y = t_base, con los dos largueros montados encima en vez de debajo. El
    # canto delantero lo pone el redondeo en punta (muere a alto_frontal/2) mas
    # 2 de material, no el larguero: ese se retiro para librar el riel de panel
    # y la bandeja lo vuela. El trasero sigue a ras de su larguero.
    x0_bb = p["alto_frontal"] / 2 + 2
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
    # Los dos van girados 45 con la cara y sobre ELLA estan separados -- el riel
    # remata a inset_sup_remate - rail_er_alto/2 del vertice y la pestana arranca
    # a marco_sup, o sea 2.75 mm limpios. El AABB no sabe distinguirlo;
    # guarda_tapa() hace la cuenta exacta en el sistema de la cara.
    frozenset({"cara_sup remate", "remate_sup"}): 3.0,
    # bisagra <-> pestana: se tocan EXACTAMENTE (el nudillo es tangente al plano
    # del techo, que es donde remata la pestana), asi que el solape de caja es
    # cero mas el ruido de coma flotante.
    frozenset({"bisagra", "remate_sup"}): 0.01,
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


def guarda_tapa(p: dict[str, float]) -> None:
    """La cara de arriba es una TAPA y tiene que poder abrir.

    Tres asserts duros, porque solapes() no ve ninguno: trabaja con cajas
    alineadas a ejes y aqui todo esta girado 45.

    1 y 2. EL EJE, FUERA DE LAS DOS CARAS. El nudillo va metido en la esquina
       EXTERIOR del vertice, tangente a la cara del panel y al techo. Si cae
       dentro de cualquiera de las dos, la tapa se traba contra su propia
       esquina en el primer grado -- y un modelo estatico no dice ni pio. Es la
       version buena del chequeo de barrido que habia antes: aquel media cuanto
       SUBE el canto del panel al girar, y esa cuenta murio cuando la pestana
       paso a ser tapa (entre las dos ya no hay movimiento relativo).

    3. EL RIEL DE ARRIBA CONTRA LA PESTANA. En el AABB se pisan (por eso van en
       TOLERADOS) pero sobre la cara estan separados, y esta es la cuenta buena:
       el riel remata a inset_sup_remate - rail_er_alto/2 del vertice y la
       pestana arranca a marco_sup."""
    P = _vertices(p)
    ev = _eje_visagra(p, P)
    rv = p["d_visagra"] / 2
    a2 = math.radians(p["angulo_superior"])
    # distancia del eje al plano de la cara del panel, positiva hacia DENTRO
    q = ((ev[0] - P[3][0]) * math.cos(a2) - (ev[1] - P[3][1]) * math.sin(a2))
    assert q <= -rv + 1e-6, (
        f"el eje de la bisagra queda DENTRO de la cara del panel ({q:+.2f} mm "
        f"del plano, se exige <= {-rv:.2f}): la tapa se traba contra su propia "
        f"esquina al abrir")
    assert ev[1] - P[4][1] >= rv - 1e-6, (
        f"el eje de la bisagra queda por DEBAJO del techo ({ev[1] - P[4][1]:+.2f}"
        f" mm sobre el, se exige >= {rv:.2f}): el nudillo pide sitio en el "
        f"acrilico del remate")

    hueco = p["inset_sup_remate"] - p["marco_sup"] - p["rail_er_alto"] / 2
    assert hueco >= 1.0, (
        f"el riel de arriba se come la pestana: {hueco:.2f} mm de hueco real "
        f"sobre la cara (se exige >= 1.0). Subir inset_sup_remate o bajar "
        f"marco_sup -- y ojo, inset_sup_remate tambien decide si el riel cabe "
        f"por detras (ver marco_remate)")


def guarda_piso(p: dict[str, float]) -> None:
    """El riel de panel del frente tiene que librar el SUELO del case.

    Es la condicion que fija alto_frontal y con el la altura entera del aparato,
    y hasta hoy vivia solo en un comentario de params.scad. Nadie la vigilaba:
    solapes() trabaja con cajas y solo canta cuando los cuerpos YA se tocan, o
    sea que se come los 4 mm de holgura sin protestar.

    El techo es el TOPE DE LA BANDEJA (t_base), no el lomo de un larguero. La
    distincion no es academica: cuando la bandeja iba apilada encima del 2020,
    derivarlo contra el larguero salia 5 mm de barato y dejaba 0.51 mm de solape
    real. Hoy la bandeja ES el suelo y el techo son t_base limpios, pero el error
    de mirar la pieza equivocada se repite igual de facil.

    Se mide sobre el centro REAL del riel (el que sale de _centros_rail), no
    rehaciendo la formula: si el .scad y el budget se separan, esto lo nota."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    y_bajo = cr[0][1] - _he_er(p, p["angulo_inferior"])[1]
    techo = p["t_base"] + p["holgura_rail"]
    assert y_bajo >= techo - 1e-9, (
        f"el riel de panel del frente se come el suelo: su esquina de abajo cae "
        f"en y={y_bajo:.2f} y el tope de la bandeja mas holgura_rail exige "
        f">={techo:.2f}. Subir alto_frontal o inset_inf_frente (van emparejados: "
        f"la curva en punta pide inset >= alto_frontal/2 + rail_er_alto/2 + 3)")


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
    # EUROrack en la primera fila. La cota que manda NO es el alto del panel
    # (128.5 mm) sino la SEPARACION ENTRE RIELES: "ER Screw distance vertical
    # = 122,50 mm" (Doepfer; los taladros van a 3.0 mm de cada canto del panel
    # y miden 3.2). Verificado el 2026-08-17 contra midisoft.de y
    # exploding-shed.com. Ojo: los rieles reales varian de marca -- Vector
    # pide 121.46 y Tiptop 122.43 --, asi que este numero hay que fijarlo
    # contra el riel que se compre, no contra el estandar a secas.
    #
    # ESTUVO EN ROJO A PROPOSITO, luego en 122.50 asumiendo el estandar Doepfer, y
    # desde el 2026-08-17 en 123.00: la cota REAL del riel de StudioRacks, que
    # llego por correo con sus planos. Ya no se simula contra un estandar de
    # catalogo sino contra el perfil que se compra, que es lo unico que atornilla.
    #
    # Sigue siendo una puerta y no un comentario: si alguien mueve un inset o
    # un alto de cara "para que quede mejor", esto vuelve a rojo antes de que
    # se corte nada.
    SEP_EUROrack = 123.0
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
    print(f"kerf aplicado: {p['kerf']:+.2f} mm (firmado; cupon manda)")
    print("  se espera NEGATIVO: el laser ENSANCHA y el modelo dibuja "
          "`d + kerf`, o sea que kerf compensa RESTANDO (README paso 2).")
    if p["kerf"] > 0:
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
