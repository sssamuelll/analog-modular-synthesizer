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

EL AIRE lo cuenta desde el 2026-10-12 clearance_budget._tiro(), que es la
puerta, con el plano neutro: cada hueco a su altura, y por debajo del plano
entra y por encima sale. De aqui sale lo que respira cada persiana (franjas()
sobre geometria()["abierto"]); abajo se imprimen los escenarios del papel.
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


def _puntos_validos(p, linea) -> list[tuple[float, float, float]]:
    """Las muestras de la linea de tacos, cada 2 mm, a 10 mm o mas de toda rosca
    M4 del dorso y de todo M5 de la tabla: (s por la linea, x, y)."""
    m4 = [c for _n, c, _d in cb._centros_rosca_ciega(p)]
    m5 = cb._m5_tabla_x(p)
    out = []
    for i in range(int(linea.length / 2.0)):
        q = linea.interpolate(i * 2.0)
        lejos_m4 = all(math.dist((q.x, q.y), c) >= 10.0 for c in m4)
        lejos_m5 = all(abs(q.x - x) >= 10.0 for x in m5) or q.y > p["u_taco"] + 1.0
        if lejos_m4 and lejos_m5:
            out.append((i * 2.0, round(q.x, 3), round(q.y, 3)))
    return out


def _entre(validos, L, a, b, D):
    """Los tacos que hacen falta de a a b, hacia delante por la linea, para que
    ningun tramo pase de D: cada vez el punto valido mas lejano que llega. None
    si un tramo sin puntos validos ya pasa de D."""
    largo = (b[0] - a[0]) % L
    cand = sorted(((v[0] - a[0]) % L, v) for v in validos if 0 < (v[0] - a[0]) % L < largo)
    pos, out = 0.0, []
    while largo - pos > D + 1e-9:
        alcance = [c for c in cand if pos < c[0] <= pos + D + 1e-9]
        if not alcance:
            return None
        pos, v = max(alcance)
        out.append(v)
    return out


def tacos(p) -> list[tuple[float, float, str]]:
    """Diez tacos a u_taco de la silueta, a 10 mm o mas de toda rosca M4 del
    dorso y de todo M5 de la tabla. Dos localizan en el suelo: el de delante,
    redondo, en el punto valido mas cercano a x = 25, y el de atras, en colisa,
    a 30 del canto de atras (papel §4; Elke lo puso en x = 290). Los ocho que
    retienen se reparten para que el tramo mas largo de la linea sin taco sea
    el menor posible: es lo que aprieta la banda contra el anillo (papel §3.3).
    Los del tramo de atras llevan iman fino: detras esta el bolsillo de la
    trasera.

    HASTA EL 2026-10-12 SE REPARTIAN A PARTES IGUALES desde el localizador, y
    la colisa se movia despues a su sitio: quedaba un tramo de 166 mm en el
    suelo sin taco. Repartir parejo y llevar cada taco al punto valido mas
    cercano tampoco basta (114 a 122): hay tramos de hasta 42 mm donde ningun
    taco libra las roscas. Con diez tacos y las roscas donde estan, el tramo
    mayor no baja de 100, que es lo que pide el papel: lo declara el budget."""
    linea = perfil_real().buffer(-p["u_taco"], join_style="mitre").exterior
    L = linea.length
    validos = _puntos_validos(p, linea)
    fondo_x = cb._vertices(p)[5][0]
    suelo = [v for v in validos if v[2] <= p["u_taco"] + 1e-6]
    loc = min(suelo, key=lambda v: abs(v[1] - 25.0))
    colisa = min(suelo, key=lambda v: abs(v[1] - (fondo_x - 30.0)))
    assert colisa[1] - loc[1] >= 200.0, (
        "los dos localizadores tienen que caer en el suelo y a 200 mm o mas")
    lo, hi = 0.0, L
    for _ in range(50):
        D = (lo + hi) / 2
        ida, vuelta = _entre(validos, L, loc, colisa, D), _entre(validos, L, colisa, loc, D)
        if ida is not None and vuelta is not None and len(ida) + len(vuelta) <= 8:
            hi = D
        else:
            lo = D
    elegidos = [loc, colisa] + _entre(validos, L, loc, colisa, hi) + _entre(validos, L, colisa, loc, hi)
    while len(elegidos) < 10:            # si sobran, parten el tramo mas largo
        orden = sorted(elegidos)
        a, b = max(zip(orden, orden[1:] + [(orden[0][0] + L,) + orden[0][1:]]),
                   key=lambda ab: ab[1][0] - ab[0][0])
        medio = (a[0] + b[0]) / 2 % L
        libres = [v for v in validos if v not in elegidos]
        elegidos.append(min(libres, key=lambda v: min(abs(v[0] - medio), L - abs(v[0] - medio))))
    assert len(set(elegidos)) == 10, "dos tacos cayeron en el mismo punto"
    out = []
    for v in sorted(elegidos, key=lambda v: (v[0] - loc[0]) % L):
        _s, x, y = v
        if v == loc:
            tipo = "loc"
        elif v == colisa:
            tipo = "colisa"
        elif x > fondo_x - cb._cara_anillo_trasera(p):
            tipo = "fino"
        else:
            tipo = "ret"
        out.append((x, y, tipo))
    return out


def hueco_mayor(p, ts=None) -> float:
    """El tramo mas largo de la linea de tacos sin un taco, medido por ella. El
    papel (§3.3 y §4) pide un punto cada 100 mm o menos: es lo que aprieta la
    banda contra el anillo y sube el primer modo de frente hacia 900 Hz."""
    from shapely.geometry import Point
    linea = perfil_real().buffer(-p["u_taco"], join_style="mitre").exterior
    s = sorted(linea.project(Point(x, y)) for x, y, _t in (ts or tacos(p)))
    return max(b - a for a, b in zip(s, s[1:] + [s[0] + linea.length]))


def generado(p) -> str:
    v = ", ".join(f"{x:.3f}" for x in varillas_x(p))
    t = ", ".join(f'[{x:.3f}, {y:.3f}, "{tipo}"]' for x, y, tipo in tacos(p))
    n = geometria(p)["varillas"]
    return ("// GENERADO por case/cad/persiana.py -- no editar a mano. Lo compara\n"
            "// guarda_persiana_generada() en check_dxf.py.\n"
            f"varillas_persiana = [{v}];\n"
            f"tacos_persiana = [{t}];\n"
            f"n_varillas_persiana = {n};\n")


def _varillas(ranuras) -> int:
    """Las varillas libres: las que quedan entre dos ranuras. No son los centros
    del ritmo: el primero cae en el borde y el ultimo fuera del perfil, y hasta
    el 2026-10-12 se contaban esos (47 contra las 44 de verdad)."""
    return len(getattr(ranuras, "geoms", [ranuras])) - 1


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
            "pasante": pasante, "abierto": abierto, "varillas": _varillas(ranuras), "alto": alto}


# --- el aire ---------------------------------------------------------------------
def franjas(geom, paso=2.0):
    x0, y0, x1, y1 = geom.bounds
    out = []
    for y in np.arange(y0, y1, paso):
        a = geom.intersection(box(x0 - 1, y, x1 + 1, y + paso)).area
        if a > 0:
            out.append((y + paso / 2, a))
    return out


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
    print("\nEL AIRE (clearance_budget._tiro(): plano neutro; las persianas, la "
          "base, la rejilla de la trasera, la rendija del alero y las ondas)")
    print(f"  {'escenario':36s} {'W':>7s} {'C_D puerta':>11s} {'pesimista':>10s} {'techo':>6s}")
    w5 = p["potencia_disipada"]
    for nombre, W in (("v5 declarada, fuente afuera", w5),
                      ("fuente adentro (v5 + 25,02)", w5 + 25.02),
                      ("v4, que no se monta", 147.31)):
        q = {**p, "potencia_disipada": W}
        dt, dtp = cb._tiro(q)["dt"], cb._tiro_pesimista(q)["dt"]
        print(f"  {nombre:36s} {W:7.2f} {dt:9.1f} K {dtp:8.1f} K {p['salto_termico_max']:4.0f} K"
              f"{'' if dtp <= p['salto_termico_max'] else '   <- NO pasa el pesimista'}")
    print(f"  (plano neutro a {cb._tiro(p)['yn']:.0f} mm)")
    print(f"\n  con {w5:.2f} W, pesimista:")
    for nombre, kw in (("las dos persianas solas", {"trasera": False, "base": False}),
                       ("un costado tapado (contra una pared)", {"costados": 1}),
                       ("sin la base (sobre un pano)", {"base": False}),
                       ("sin persianas: el case de agosto", {"costados": 0, "base": False})):
        print(f"    {nombre:38s} {cb._tiro_pesimista(p, **kw)['dt']:5.1f} K")
    if "--escribir" in sys.argv:
        with open(GENERADO, "w", encoding="utf-8", newline="\n") as f:
            f.write(generado(p))
        print(f"\nescrito {GENERADO}")
    if "--json" in sys.argv:
        ruta = sys.argv[sys.argv.index("--json") + 1]
        capas_json(p, g, ruta)
        print(f"\ncapas escritas en {ruta}")
