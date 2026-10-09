"""La chimenea de la piel: lo que respira la rama, en kelvin.

    python case/cad/piel_termica.py

PROPUESTA (2026-09-05), no puerta. La misma fisica que clearance_budget._tiro()
--P = k dT^1.5, k = rho cp C_D A_ef sqrt(2 g h / T), A_ef = 1/sqrt(1/A_ent^2 +
1/A_sal^2)-- con las dos mejillas como chimenea: la mitad baja de cada una
entra (centroide a H/4), la mitad alta sale (3H/4), mas la rejilla baja de la
trasera de hoy como entrada. Lo que respira sale de celosia_placa.json (lo
abierto sobre la ventana del anillo, a >= marco_fondo del perfil). Existe
para que la tabla del papel salga de aqui y no de una cuenta a mano: el 05-09
la misma resta de dos columnas distintas se hizo tres veces en un dia.
"""
import json
import math
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.join(DIR, "..") not in sys.path:
    sys.path.insert(0, os.path.join(DIR, ".."))
import clearance_budget as cb  # noqa: E402

ESCENARIOS = (("v5 declarada, fuente afuera", 64.2), ("v5 a censo", 35.1),
              ("fuente ADENTRO (v5 + 25.02)", 89.2))


def salto(p, potencia_w, cd, respira_mm2, con_rejilla=True, serie_mm2=()):
    """serie_mm2: secciones que el aire cruza EN SERIE con la celosia, por
    mitad de cachete (la placa ambar de la ficha 10: el canal y la rendija).
    Mismo C_D en todas: 1/A^2 = suma de 1/A_i^2."""
    H = cb._vertices(p)[5][1]
    _n, _l, a_rej, y_rej = cb._rejilla_entrada(p)
    mitad = respira_mm2 / 2                # por cachete: mitad entra, mitad sale
    if serie_mm2:
        mitad = 1.0 / math.sqrt(1 / mitad ** 2 + sum(1 / a ** 2 for a in serie_mm2))
    a_ent_m = a_sal = 2 * mitad
    a_ent = a_ent_m + (a_rej if con_rejilla else 0.0)
    y_ent = (a_ent_m * H / 4 + (a_rej * y_rej if con_rejilla else 0.0)) / a_ent
    h = (3 * H / 4 - y_ent) / 1000.0
    a_ef = 1.0 / math.sqrt(1 / a_ent ** 2 + 1 / a_sal ** 2)
    k = cb.RHO_AIRE * cb.CP_AIRE * cd * a_ef * 1e-6 * math.sqrt(2 * cb.G * h / cb.T_AMB)
    return (potencia_w / k) ** (2.0 / 3.0), a_ef, h * 1000.0


# LA PLACA AMBAR de la ficha 10 (D-P3): acrilico detras de cada cachete, del
# contorno de la ventana del anillo (el perfil menos la cara vista) menos una
# rendija alrededor, por donde el aire entra y sale. Va dentro de la pletina,
# contra su cara de dentro: entre el anillo y el primer riel quedan 6 mm, y el
# interior es de los modulos. El aire del cachete cruza en serie el canal que
# queda entre la placa y el cachete (t_anillo - ESPESOR_PLACA de fondo, a lo
# largo del borde de la placa) y la rendija. ORDEN DE MAGNITUD: el mismo C_D
# para todo, y sin el rozamiento del canal, que solo empeoraria la cifra.
ESPESOR_PLACA = 3.0
RENDIJAS_PLACA = (8.0, 12.0, 16.0)


def placa_ambar(p, rendija):
    """(canal, rendija) en mm2 por mitad de cachete."""
    from shapely.geometry import Polygon
    with open(os.path.join(DIR, "piel_borde.json"), encoding="utf-8") as f:
        perfil = Polygon(json.load(f)["perfil_real"])
    ventana = perfil.buffer(-p["cara_anillo"], join_style=2)
    placa = perfil.buffer(-(p["cara_anillo"] + rendija), join_style=1)
    canal = (p["t_anillo"] - ESPESOR_PLACA) * placa.length
    return canal / 2, (ventana.area - placa.area) / 2


if __name__ == "__main__":
    p = cb.leer_params()
    with open(os.environ.get("PIEL_RAMA", os.path.join(DIR, "celosia_placa.json")), encoding="utf-8") as f:
        m = json.load(f)["medidas"]
    respira = m["abierto_ventana_mm2"]
    techo = p["salto_termico_max"]
    print(f"respira {respira} mm2 por cachete (abre {m['abierto_mm2']} a la vista); "
          f"techo {techo:.0f} K; C_D {cb.CD_TIRO} / pesimista {cb.CD_TIRO_PESIMISTA}")
    print(f"{'escenario':30s} {'W':>6s} {'salto':>7s} {'pesim.':>7s} {'sin rej.':>9s}")
    for nombre, P in ESCENARIOS:
        dt, a_ef, h = salto(p, P, cb.CD_TIRO, respira)
        dtp, _, _ = salto(p, P, cb.CD_TIRO_PESIMISTA, respira)
        dts, _, _ = salto(p, P, cb.CD_TIRO, respira, con_rejilla=False)
        marca = "" if dtp <= techo else "   <- NO pasa el pesimista"
        print(f"{nombre:30s} {P:6.1f} {dt:6.1f} K {dtp:6.1f} K {dts:8.1f} K{marca}")
    print(f"area efectiva {a_ef:.0f} mm2, tiro {h:.0f} mm")
    # la respiracion que haria falta para pasar el pesimista con la fuente afuera
    P = ESCENARIOS[0][1]
    lo, hi = 1000.0, 60000.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if salto(p, P, cb.CD_TIRO_PESIMISTA, mid)[0] > techo:
            lo = mid
        else:
            hi = mid
    if hi > respira:
        print(f"para pasar el pesimista con {P} W hace falta respirar {hi:.0f} mm2 por cachete: "
              f"un {100 * (hi / respira - 1):.0f} % mas")
    else:
        print(f"pasa el pesimista con {P} W: bastan {hi:.0f} mm2 por cachete y respira {respira} "
              f"({100 * (respira / hi - 1):.0f} % de margen)")

    print("")
    print(f"la placa ambar (ficha 10, D-P3): canal de {p['t_anillo'] - ESPESOR_PLACA:.0f} mm, "
          f"en serie con la celosia; K con el C_D de la puerta / pesimista")
    print(f"{'':20s} {'declarada 64,2 W':>17s} {'censo 35,1 W':>15s}")
    filas = [("sin placa", ())] + [(f"rendija {r:.0f} mm", placa_ambar(p, r)) for r in RENDIJAS_PLACA]
    for nombre, serie in filas:
        celdas = []
        for P in (ESCENARIOS[0][1], ESCENARIOS[1][1]):
            a = salto(p, P, cb.CD_TIRO, respira, serie_mm2=serie)[0]
            b_ = salto(p, P, cb.CD_TIRO_PESIMISTA, respira, serie_mm2=serie)[0]
            celdas.append(f"{a:5.1f} / {b_:5.1f}{'' if b_ <= techo else ' X'}")
        print(f"{nombre:20s} {celdas[0]:>17s} {celdas[1]:>15s}")
    serie = placa_ambar(p, 12.0)
    for nombre, P in ESCENARIOS[:2]:
        d = (salto(p, P + 1.0, cb.CD_TIRO_PESIMISTA, respira, serie_mm2=serie)[0]
             - salto(p, P, cb.CD_TIRO_PESIMISTA, respira, serie_mm2=serie)[0])
        print(f"cada vatio de luz dentro, con la rendija de 12 y {nombre}: +{d:.2f} K (pesimista)")
