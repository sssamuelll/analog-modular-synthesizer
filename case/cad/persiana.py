"""LA PERSIANA (propuesta del 2026-10-11, no puerta): el costado del SAM17 sin
piel. Una placa de 6 mm por fuera del anillo, tapandolo, con varillas rectas y
verticales; por donde respira el instrumento.

    python case/cad/persiana.py            # imprime las cifras del papel
    python case/cad/persiana.py --json F   # y escribe la geometria por capas para el render

Papel: docs/superpowers/specs/2026-10-11-case-persiana-design.md. Este guion
existe para que cada cifra del papel salga de aqui y no de una cuenta a mano
(la regla de piel_termica.py, y el H13 de la junta del 11-10).

LA GEOMETRIA, en el plano del costado (x = fondo desde el frente, y = alto
desde la tabla), con z hacia fuera desde la cara del anillo:
  - contorno: el perfil real del anillo (`perfil_real` de piel_borde.json), a
    SUELO por encima de la tabla;
  - varillas verticales de VARILLA, a paso medio PASO con una ola lenta y un
    poco de azar con semilla fija; borde macizo de RIM;
  - las ranuras llevan el radio de la fresa (FRESA_D/2) en sus extremos;
  - dos ATADOS: puentes de PUENTE por detras, de ATADO_ALTO de alto, a un tercio
    y dos tercios del alto: ahi la ranura no pasa;
  - sobre la cara del anillo (BANDA, BANDA_ATRAS en el tramo de atras) la ranura
    tampoco pasa: detras esta el aluminio.
Capas: "macizo" (z 0..FONDO: varillas y borde) y "fondo" (z 0..PUENTE: la banda
ciega y los puentes de los atados).

EL AIRE: plano neutro. Cada hueco a su altura; por debajo del plano entra y por
encima sale. Con una entrada y una salida da exactamente clearance_budget._tiro()
(se comprueba al arrancar). Respira lo abierto DETRAS de la ventana real: el
marco de la ventana llega a MARCO del perfil, y a MARCO_ATRAS en el tramo de atras.
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

FONDO, RIM, SUELO = 6.0, 4.0, 0.3
VARILLA = 2.0                    # 6 / 2.0 = 3:1, ESBELTEZ_MAX_PARED de clearance_budget
PASO, OLA, AZAR, SEMILLA = 7.0, 0.16, 0.06, 17
ATADO_ALTO, PUENTE = 4.0, 2.0
BANDA, BANDA_ATRAS = 20.0, 23.0  # cara_anillo, y cara_anillo_trasera() del .scad
MARCO, MARCO_ATRAS = 26.0, 30.0  # marco_fondo, marco_fondo_trasera
AIRE_MIN = 13678.0               # mm2 por costado que pedia piel_termica.py (H/4-3H/4)
MATERIALES = {"aluminio 6082-T6": 2.70, "PA12 impreso": 1.01}   # g/cm3, de manual
ESCENARIOS = (("v5 declarada, fuente afuera", 64.2), ("fuente adentro (v5 + 25,02)", 89.2),
              ("v4, lo que lee hoy guarda_aire()", 147.31))


def contorno(p):
    with open(os.path.join(AQUI, "piel_borde.json"), encoding="utf-8") as f:
        perfil = Polygon(json.load(f)["perfil_real"]).buffer(0)
    return perfil, perfil.intersection(box(-50, SUELO, 400, 400))


def geometria(p):
    perfil, cont = contorno(p)
    V = cb._vertices(p)
    alto, fondo_x = V[5][1], V[5][0]
    rng = np.random.default_rng(SEMILLA)
    xs, x = [], 4.0
    while x < fondo_x + 10:
        xs.append(x)
        x += PASO * (1 + OLA * math.sin(x / 23.0) + AZAR * rng.standard_normal())
    varillas = unary_union([box(x - VARILLA / 2, -5, x + VARILLA / 2, alto + 20) for x in xs])
    dentro = cont.buffer(-RIM)
    # las ranuras, con el radio de la fresa en las puntas (apertura morfologica)
    r = p["fresa_d"] / 2
    ranuras = dentro.difference(varillas).buffer(-r).buffer(r)
    macizo = cont.difference(ranuras)
    atados = unary_union([box(-50, y - ATADO_ALTO / 2, 400, y + ATADO_ALTO / 2)
                          for y in (alto / 3, 2 * alto / 3)])
    banda = cont.difference(perfil.buffer(-BANDA, join_style="mitre")).union(
        cont.intersection(box(fondo_x - BANDA_ATRAS, -50, 400, 400)))
    fondo = ranuras.intersection(unary_union([atados, banda]))
    ventana = perfil.buffer(-MARCO, join_style="mitre").intersection(
        box(-50, -50, fondo_x - MARCO_ATRAS, 400))
    abierto = ventana.intersection(ranuras).difference(fondo)
    return {"contorno": cont, "macizo": macizo, "fondo": fondo, "ranuras": ranuras,
            "abierto": abierto, "varillas": len(xs), "alto": alto, "atados": (alto / 3, 2 * alto / 3)}


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


# --- salida -----------------------------------------------------------------------
def capas_json(g, ruta):
    def a_json(geom):
        geoms = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        return [{"ext": list(map(list, q.exterior.coords)),
                 "huecos": [list(map(list, r.coords)) for r in q.interiors]}
                for q in geoms if q.geom_type == "Polygon" and q.area > 0.5]
    out = {"capas": {"macizo": {"poligonos": a_json(g["macizo"].buffer(0)), "z0": 0.0, "z1": FONDO, "bisel": 0.2},
                     "fondo": {"poligonos": a_json(g["fondo"].buffer(0)), "z0": 0.0, "z1": PUENTE, "bisel": 0.0}}}
    with open(ruta, "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    p = cb.leer_params()
    autocomprobacion(p)
    g = geometria(p)
    ab = g["abierto"]
    fr = franjas(ab)
    a_tot = sum(a for _, a in fr)
    y_c = sum(y * a for y, a in fr) / a_tot
    vol = g["macizo"].area * FONDO + g["fondo"].area * PUENTE
    print(f"LA PERSIANA: {g['varillas']} varillas de {VARILLA} en {FONDO:.0f} de fondo "
          f"(esbeltez {FONDO / VARILLA:.1f}:1), borde de {RIM:.0f}, atados de {ATADO_ALTO:.0f} a "
          f"{g['atados'][0]:.0f} y {g['atados'][1]:.0f} mm, ranuras con R{p['fresa_d'] / 2:.1f} de fresa")
    print(f"  se ve abierto {g['ranuras'].area:.0f} de {g['contorno'].area:.0f} mm2 "
          f"({100 * g['ranuras'].area / g['contorno'].area:.0f} %)")
    print(f"  respira {a_tot:.0f} mm2 por costado detras de la ventana real (marco a {MARCO:.0f}, "
          f"{MARCO_ATRAS:.0f} atras); su centro de area a {y_c:.0f} mm de {g['alto']:.0f}")
    for nombre, rho in MATERIALES.items():
        print(f"  pesa {vol / 1000 * rho:.0f} g por costado en {nombre}")
    print(f"\nEL AIRE (plano neutro; rejilla de la trasera, rendija del alero y ondas incluidas)")
    print(f"  {'escenario':36s} {'W':>7s} {'C_D puerta':>11s} {'pesimista':>10s} {'techo':>6s}")
    for nombre, W in ESCENARIOS:
        hs = huecos_case(p, ab)
        dt, yn = salto(hs, W, cb.CD_TIRO)
        dtp, _ = salto(hs, W, cb.CD_TIRO_PESIMISTA)
        print(f"  {nombre:36s} {W:7.2f} {dt:9.1f} K {dtp:8.1f} K {p['salto_termico_max']:4.0f} K"
              f"{'' if dtp <= p['salto_termico_max'] else '   <- NO pasa el pesimista'}")
    print(f"  (plano neutro a {yn:.0f} mm)")
    print(f"\n  con 64,2 W, pesimista:")
    for nombre, hs in (("las dos persianas solas", huecos_case(p, ab, trasera=False)),
                       ("un costado tapado (contra una pared)", huecos_case(p, ab, costados=1)),
                       ("sin persianas: el case de agosto", huecos_case(p, ab, costados=0))):
        dtp, _ = salto(hs, 64.2, cb.CD_TIRO_PESIMISTA)
        print(f"    {nombre:38s} {dtp:5.1f} K")
    if "--json" in sys.argv:
        ruta = sys.argv[sys.argv.index("--json") + 1]
        capas_json(g, ruta)
        print(f"\ncapas escritas en {ruta}")
