"""LA PERSIANA (firmada el 2026-10-11): el costado del SAM17 sin piel. Una
placa de t_persiana por fuera del anillo, tapandolo, con varillas rectas y
verticales; por donde respira el instrumento.

    python case/cad/persiana.py              # las cifras del papel
    python case/cad/persiana.py --escribir   # y reescribe persiana_generada.scad
    python case/cad/persiana.py --json F     # y la geometria por capas, para un render

Papel: docs/superpowers/specs/2026-10-11-case-persiana-design.md. Cada cifra
del papel sale de aqui y no de una cuenta a mano (H13 de la junta del 11-10).

LO QUE ESTO HACE QUE EL .scad NO SABE HACER BIEN: el ritmo de las varillas y
donde caben los tacos. Los escribe en persiana_generada.scad, que el .scad
incluye y que guarda_persiana_generada() (check_dxf.py) compara con esto. Las
cotas viven en params.scad, como todas.

LA GEOMETRIA, en el plano del costado (x = fondo desde el frente, y = alto
desde la tabla), con z hacia fuera desde la cara del anillo:
  - contorno: la silueta del anillo tal como sale al taller (costilla_2d.dxf),
    a suelo_persiana por encima de la tabla;
  - varillas verticales de varilla_persiana, a paso medio paso_persiana con una
    ola lenta y un azar DETERMINISTA (k * phi modulo 1: sin numpy.random, cuyo
    flujo puede cambiar entre versiones); borde macizo de borde_persiana;
  - las ranuras llevan el radio de la fresa (fresa_d / 2) en sus puntas;
  - dos ATADOS de alto_atado, a 1/3 y 2/3 del alto, y la BANDA sobre la cara del
    anillo: ahi la ranura no pasa, se queda a hondo_ciego_persiana desde fuera;
  - lo que atraviesa es la ranura dentro de la ventana del anillo menos los
    atados; lo que respira, lo que atraviesa DETRAS de la ventana real (el marco
    llega a marco_fondo del perfil, y a marco_fondo_trasera en el tramo de atras).

EL AIRE: plano neutro. Cada hueco a su altura; por debajo del plano entra y por
encima sale. Con una entrada y una salida da exactamente clearance_budget._tiro()
(se comprueba al arrancar). Es propuesta, no puerta: la puerta del aire es
guarda_aire(), y lo que la lleve al plano neutro es otro plan.
"""
import json
import math
import os
import sys

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import clearance_budget as cb  # noqa: E402

PHI = 0.6180339887498949            # el azar determinista: k * phi modulo 1
DXF_ANILLO = os.path.join(AQUI, "..", "plans", "costilla_2d.dxf")
GENERADO = os.path.join(AQUI, "persiana_generada.scad")
MARCO, MARCO_ATRAS = "marco_fondo", "marco_fondo_trasera"   # las claves de params
MATERIALES = {"aluminio 6082-T6": 2.70, "PA12 impreso": 1.01}   # g/cm3, de manual
ESCENARIOS = (("v5 declarada, fuente afuera", 64.2), ("fuente adentro (v5 + 25,02)", 89.2),
              ("v4, lo que lee hoy guarda_aire()", 147.31))


def perfil_real():
    """La silueta del anillo tal como sale al taller: el contorno exterior de
    costilla_2d.dxf (perfil_lateral(), con sus entasis y sus radios). Es la de
    la persiana: su canto cae sobre el del anillo."""
    import ezdxf
    from shapely.geometry import LineString
    from shapely.ops import polygonize
    doc = ezdxf.readfile(DXF_ANILLO)
    lineas = [LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
              for e in doc.modelspace() if e.dxftype() == "LINE"]
    # Salen dos: la banda (con la ventana de agujero) y la ventana. La ventana
    # tiene MAS area que la banda, asi que se escoge por el contorno exterior.
    return max((Polygon(q.exterior) for q in polygonize(lineas)), key=lambda q: q.area)


def contorno(p):
    perfil = perfil_real()
    return perfil, perfil.intersection(box(-50, p["suelo_persiana"], 400, 400))


def varillas_x(p) -> list[float]:
    """Los centros de las varillas, de delante atras: paso medio con una ola
    lenta y un azar determinista."""
    fondo_x = cb._vertices(p)[5][0]
    out, x, k = [], 4.0, 0
    while x < fondo_x + 10:
        out.append(round(x, 3))
        j = 2 * ((k * PHI) % 1.0) - 1
        x += p["paso_persiana"] * (1 + p["ola_persiana"] * math.sin(x / 23.0) + p["azar_persiana"] * j)
        k += 1
    return out


def tacos(p) -> list[tuple[float, float, str]]:
    """Diez tacos a u_taco de la silueta, repartidos por el contorno, a 10 mm o
    mas de toda rosca M4 del dorso y de todo M5 de la tabla. Dos localizan en
    el suelo (el de delante redondo, el de atras en colisa); los del tramo de
    atras llevan iman fino (detras esta el bolsillo de la trasera); el resto
    retiene. Es el reparto de Elke Brandt (junta del 11-10)."""
    perfil = perfil_real()
    linea = perfil.buffer(-p["u_taco"], join_style="mitre").exterior
    L = linea.length
    m4 = [c for _n, c, _d in cb._centros_rosca_ciega(p)]
    m5 = cb._m5_tabla_x(p)
    fondo_x = cb._vertices(p)[5][0]
    validos = []
    for i in range(int(L / 2.0)):
        q = linea.interpolate(i * 2.0)
        lejos_m4 = all(math.dist((q.x, q.y), c) >= 10.0 for c in m4)
        lejos_m5 = all(abs(q.x - x) >= 10.0 for x in m5) or q.y > p["u_taco"] + 1.0
        if lejos_m4 and lejos_m5:
            validos.append((i * 2.0, round(q.x, 3), round(q.y, 3)))
    suelo = [v for v in validos if v[2] <= p["u_taco"] + 1e-6]
    loc = min(suelo, key=lambda v: abs(v[1] - 25.0))
    elegidos = []
    for k in range(10):
        meta = (loc[0] + k * L / 10) % L
        elegidos.append(min(validos, key=lambda v: min(abs(v[0] - meta), L - abs(v[0] - meta))))
    # LA COLISA, al fondo del suelo: el reparto parejo deja el taco de suelo mas
    # atrasado donde caiga, y el segundo localizador quiere la base mas larga
    # posible. Se lleva al punto valido del suelo mas cercano a 30 del canto de
    # atras (Elke lo puso en x = 290).
    en_suelo = sorted((v for v in elegidos if v[2] <= p["u_taco"] + 1e-6), key=lambda v: v[1])
    colisa = min(suelo, key=lambda v: abs(v[1] - (fondo_x - 30.0)))
    elegidos[elegidos.index(en_suelo[-1])] = colisa
    assert len(set(elegidos)) == 10, "dos tacos cayeron en el mismo punto"
    en_suelo = sorted((v for v in elegidos if v[2] <= p["u_taco"] + 1e-6), key=lambda v: v[1])
    assert len(en_suelo) >= 2 and en_suelo[-1][1] - en_suelo[0][1] >= 200.0, (
        "los dos localizadores tienen que caer en el suelo y a 200 mm o mas")
    out = []
    for _s, x, y in elegidos:
        if (x, y) == en_suelo[0][1:]:
            tipo = "loc"
        elif (x, y) == en_suelo[-1][1:]:
            tipo = "colisa"
        elif x > fondo_x - cb._cara_anillo_trasera(p):
            tipo = "fino"
        else:
            tipo = "ret"
        out.append((x, y, tipo))
    return out


def generado(p) -> str:
    v = ", ".join(f"{x:.3f}" for x in varillas_x(p))
    t = ", ".join(f'[{x:.3f}, {y:.3f}, "{tipo}"]' for x, y, tipo in tacos(p))
    return ("// GENERADO por case/cad/persiana.py -- no editar a mano. Lo compara\n"
            "// guarda_persiana_generada() en check_dxf.py.\n"
            f"varillas_persiana = [{v}];\n"
            f"tacos_persiana = [{t}];\n")


def geometria(p):
    perfil, cont = contorno(p)
    V = cb._vertices(p)
    alto, fondo_x = V[5][1], V[5][0]
    v = p["varilla_persiana"]
    xs = varillas_x(p)
    dentro = cont.buffer(-p["borde_persiana"], join_style="mitre")
    franjas_x = unary_union([box(a + v / 2, -10, b - v / 2, 400) for a, b in zip(xs, xs[1:])])
    r = p["fresa_d"] / 2
    ranuras = dentro.intersection(franjas_x).buffer(-r).buffer(r)
    macizo = cont.difference(ranuras)
    atados = unary_union([box(-50, y - p["alto_atado"] / 2, 400, y + p["alto_atado"] / 2)
                          for y in (alto / 3, 2 * alto / 3)])
    ventana_anillo = perfil.buffer(-p["cara_anillo"], join_style="mitre").intersection(
        box(-50, -50, fondo_x - cb._cara_anillo_trasera(p), 400))
    pasante = ranuras.intersection(ventana_anillo).difference(atados)
    fondo = ranuras.difference(pasante)
    ventana_real = perfil.buffer(-p[MARCO], join_style="mitre").intersection(
        box(-50, -50, fondo_x - p[MARCO_ATRAS], 400))
    abierto = pasante.intersection(ventana_real)
    return {"contorno": cont, "macizo": macizo, "fondo": fondo, "ranuras": ranuras,
            "pasante": pasante, "abierto": abierto, "varillas": len(xs), "alto": alto}


# --- el aire ---------------------------------------------------------------------
def franjas(geom, paso=2.0):
    x0, y0, x1, y1 = geom.bounds
    out = []
    for y in np.arange(y0, y1, paso):
        a = geom.intersection(box(x0 - 1, y, x1 + 1, y + paso)).area
        if a > 0:
            out.append((y + paso / 2, a))
    return out


def plano_neutro(huecos):
    def sobra(yn):
        return (sum(a * math.sqrt(yn - y) for y, a in huecos if y < yn)
                - sum(a * math.sqrt(y - yn) for y, a in huecos if y > yn))
    lo, hi = min(y for y, _ in huecos), max(y for y, _ in huecos)
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if sobra(mid) > 0 else (mid, hi)
    yn = (lo + hi) / 2
    return yn, sum(a * math.sqrt(y - yn) for y, a in huecos if y > yn)


def salto(huecos, potencia_w, cd):
    yn, S = plano_neutro(huecos)                       # S en mm^2.5
    k = cb.RHO_AIRE * cb.CP_AIRE * cd * math.sqrt(2 * cb.G / cb.T_AMB) * S * 1e-6 * math.sqrt(1e-3)
    return (potencia_w / k) ** (2.0 / 3.0), yn


def huecos_case(p, abierto, costados=2, trasera=True):
    hs = [(y, a * costados) for y, a in franjas(abierto)] if costados else []
    if trasera:
        _n, _l, a_ent, y_ent = cb._rejilla_entrada(p)
        a_ren, y_ren = cb._rendija(p)
        a_ond, y_ond = cb._ondas_trasera(p)
        hs += [(y_ent, a_ent), (y_ren, a_ren), (y_ond, a_ond)]
    return hs


def autocomprobacion(p):
    """Con la entrada y la salida de _tiro(), el plano neutro da su cifra exacta."""
    t = cb._tiro(p, cb.CD_TIRO_PESIMISTA)
    dt, _ = salto([(t["y_ent"], t["a_ent"]), (t["y_sal"], t["a_sal"])],
                  p["potencia_disipada"], cb.CD_TIRO_PESIMISTA)
    assert abs(dt - t["dt"]) < 1e-6 * t["dt"], f"el plano neutro da {dt} y _tiro() {t['dt']}"


def autocomprobacion_ritmo(p) -> None:
    """El ritmo no depende de numpy: dos llamadas dan lo mismo, ninguna ranura
    queda mas estrecha que la fresa y el paso no se sale de la ola."""
    a, b = varillas_x(p), varillas_x(p)
    assert a == b, "el ritmo de las varillas no es determinista"
    pasos = [y - x for x, y in zip(a, a[1:])]
    lim = p["paso_persiana"] * (1 + p["ola_persiana"] + p["azar_persiana"])
    assert max(pasos) <= lim + 1e-9, f"un paso de {max(pasos):.2f} se sale de la ola ({lim:.2f})"
    ranura = min(pasos) - p["varilla_persiana"]
    assert ranura >= p["fresa_d"] - 1e-9, (
        f"la ranura mas estrecha mide {ranura:.2f} y la fresa {p['fresa_d']:g}")


# --- salida -----------------------------------------------------------------------
def capas_json(p, g, ruta):
    def a_json(geom):
        geoms = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        return [{"ext": list(map(list, q.exterior.coords)),
                 "huecos": [list(map(list, r.coords)) for r in q.interiors]}
                for q in geoms if q.geom_type == "Polygon" and q.area > 0.5]
    puente = p["t_persiana"] - p["hondo_ciego_persiana"]
    out = {"capas": {"macizo": {"poligonos": a_json(g["macizo"].buffer(0)), "z0": 0.0,
                                "z1": p["t_persiana"], "bisel": 0.2},
                     "fondo": {"poligonos": a_json(g["fondo"].buffer(0)), "z0": 0.0,
                               "z1": puente, "bisel": 0.0}}}
    with open(ruta, "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    p = cb.leer_params()
    autocomprobacion(p)
    autocomprobacion_ritmo(p)
    g = geometria(p)
    ab = g["abierto"]
    fr = franjas(ab)
    a_tot = sum(a for _, a in fr)
    y_c = sum(y * a for y, a in fr) / a_tot
    puente = p["t_persiana"] - p["hondo_ciego_persiana"]
    vol = g["macizo"].area * p["t_persiana"] + g["fondo"].area * puente
    print(f"LA PERSIANA: {g['varillas']} varillas de {p['varilla_persiana']:g} en "
          f"{p['t_persiana']:g} de fondo (esbeltez {p['t_persiana'] / p['varilla_persiana']:.1f}:1), "
          f"borde de {p['borde_persiana']:g}, atados de {p['alto_atado']:g} a {g['alto'] / 3:.0f} y "
          f"{2 * g['alto'] / 3:.0f} mm, ranuras con R{p['fresa_d'] / 2:.1f} de fresa")
    print(f"  se ve abierto {g['ranuras'].area:.0f} de {g['contorno'].area:.0f} mm2 "
          f"({100 * g['ranuras'].area / g['contorno'].area:.0f} %)")
    print(f"  respira {a_tot:.0f} mm2 por costado detras de la ventana real (marco a {p[MARCO]:g}, "
          f"{p[MARCO_ATRAS]:g} atras); su centro de area a {y_c:.0f} mm de {g['alto']:.0f}")
    for nombre, rho in MATERIALES.items():
        print(f"  pesa {vol / 1000 * rho:.0f} g por costado en {nombre}")
    print(f"  {len(tacos(p))} tacos: " + ", ".join(f"{t} en ({x:.1f}, {y:.1f})" for x, y, t in tacos(p)))
    print("\nEL AIRE (plano neutro; rejilla de la trasera, rendija del alero y ondas incluidas)")
    print(f"  {'escenario':36s} {'W':>7s} {'C_D puerta':>11s} {'pesimista':>10s} {'techo':>6s}")
    for nombre, W in ESCENARIOS:
        hs = huecos_case(p, ab)
        dt, yn = salto(hs, W, cb.CD_TIRO)
        dtp, _ = salto(hs, W, cb.CD_TIRO_PESIMISTA)
        print(f"  {nombre:36s} {W:7.2f} {dt:9.1f} K {dtp:8.1f} K {p['salto_termico_max']:4.0f} K"
              f"{'' if dtp <= p['salto_termico_max'] else '   <- NO pasa el pesimista'}")
    print(f"  (plano neutro a {yn:.0f} mm)")
    print("\n  con 64,2 W, pesimista:")
    for nombre, hs in (("las dos persianas solas", huecos_case(p, ab, trasera=False)),
                       ("un costado tapado (contra una pared)", huecos_case(p, ab, costados=1)),
                       ("sin persianas: el case de agosto", huecos_case(p, ab, costados=0))):
        dtp, _ = salto(hs, 64.2, cb.CD_TIRO_PESIMISTA)
        print(f"    {nombre:38s} {dtp:5.1f} K")
    if "--escribir" in sys.argv:
        with open(GENERADO, "w", encoding="utf-8", newline="\n") as f:
            f.write(generado(p))
        print(f"\nescrito {GENERADO}")
    if "--json" in sys.argv:
        ruta = sys.argv[sys.argv.index("--json") + 1]
        capas_json(p, g, ruta)
        print(f"\ncapas escritas en {ruta}")
