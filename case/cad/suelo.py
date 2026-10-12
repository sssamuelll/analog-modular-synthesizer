"""El suelo del case sin tabla: el aire con el suelo abierto.

Imprime las cifras del papel docs/superpowers/specs/2026-10-12-case-suelo-design.md
(§5). Es PROPUESTA, no puerta, como persiana.py: la puerta entra con el plan.

EL SUELO ES UN CAMINO DE ENTRADA EN SERIE, no un hueco suelto. El aire entra por
la rendija que dejan las patas en el perimetro, corre por el canal de alto_pie
que queda entre la chapa y la mesa hasta el campo de agujeros, y sube por ellos.
La rendija y los agujeros son orificios (la perdida va con Q^2); el canal es
laminar, Poiseuille entre dos placas (va con Q):

    dp = rho/2 (Q / (C_D A_rendija))^2 + 12 mu L Q / (W h^3) + rho/2 (Q / (C_D A_suelo))^2

Con un termino lineal la chimenea deja de ser P = k dT^1.5 y se resuelve con dos
bisecciones: el plano neutro por balance de masa a cada dT, y dT por balance de
energia. Sin el suelo da _tiro() exacto (autocomprobacion()).

El canal se reduce a uno solo, de ancho W (la rendija libre del perimetro) y
largo L (lo que corre el aire bajo la chapa hasta los agujeros). Es la cuenta
mas cruda del modelo: el flujo de verdad es 2D y converge. Por eso el papel da
las cifras para varios L, y el canal es su HUECO (se mide en la primera unidad).
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import clearance_budget as cb  # noqa: E402

MU_AIRE = 1.8e-5      # Pa s, aire a ~30 C
T_SUELO = 3.0         # mm, la chapa (§3.1)
D_PATA = 20.0         # mm, cada pata tapa su diametro de rendija


def huella(p: dict[str, float]) -> tuple[float, float]:
    """El suelo: de cara de fuera a cara de fuera de los anillos, y a lo largo
    del canto inferior del anillo, de chaflan a chaflan."""
    return p["ancho_total"], cb.fondo(p) - 2 * p["chaflan_nariz"]


ABIERTO_RV58 = math.pi / 4 * 5 ** 2 / (8 ** 2 * math.sqrt(3) / 2)   # Ø5 cada 8, tresbolillo
ORILLA = 10.0         # mm del campo a anillos, pies de nariz y talon, y chasis


def campo(p: dict[str, float]) -> list[tuple[float, float, float, float]]:
    """Donde pueden ir agujeros, como rectangulos (x0, x1, z0, z1): el suelo sin
    el canto de los anillos, sin los pies de nariz y talon, y sin la huella del
    chasis, que se queda (sec. 4 del papel). Sale una L: A a la izquierda del
    chasis, de delante a atras, y B delante de el."""
    ancho, _ = huella(p)
    c = cb._chasis(p)
    x_fr = cb._x_chasis_frente(p)
    z_ch = p["t_anillo"] + cb.perfil(p)["ancho_util"] - p["chasis_margen_bandeja"] - c["tapa_x"]
    x0 = p["chaflan_nariz"] + p["nariz_pie"] + ORILLA + 8.5   # + medio M4 y su inserto
    x1 = cb._talon(p)["x_pie"] - ORILLA - 8.5
    z0, z1 = p["t_anillo"] + ORILLA, ancho - p["t_anillo"] - ORILLA
    return [(x0, x1, z0, z_ch - ORILLA), (x0, x_fr - ORILLA, z_ch - ORILLA, z1)]


def rendija_libre(p: dict[str, float], costados: int = 2) -> float:
    """Lo que queda abierto del perimetro, en mm: sin las cuatro patas, y sin el
    costado tapado si lo hay (una pared contra la persiana tapa tambien la
    rendija de ese lado)."""
    ancho, largo = huella(p)
    libre = 2 * (ancho + largo) - 4 * D_PATA
    return libre - (2 - costados) * (largo - 2 * D_PATA)


def caudal_suelo(dp: float, a_suelo: float, w: float, largo: float, h: float,
                 cd: float) -> float:
    """m3/s que sube por el suelo con dp Pa de tiro a y = 0."""
    if dp <= 0 or a_suelo <= 0:
        return 0.0
    rho = cb.RHO_AIRE
    a_ent, a_ag = w * h * 1e-6, a_suelo * 1e-6
    a = rho / 2 * (1 / (cd * a_ent) ** 2 + 1 / (cd * a_ag) ** 2)
    b = 12 * MU_AIRE * (largo * 1e-3) / ((w * 1e-3) * (h * 1e-3) ** 3)
    return (-b + math.sqrt(b * b + 4 * a * dp)) / (2 * a)


def _caudales(huecos, yn, dt, cd, suelo):
    """(entra, sale) en m3/s con el plano neutro en yn mm y dT en K."""
    g = cb.RHO_AIRE * cb.G * dt / cb.T_AMB          # Pa por metro de altura
    entra = sale = 0.0
    for y, a in huecos:
        q = cd * a * 1e-6 * math.sqrt(2 * g * abs(y - yn) * 1e-3 / cb.RHO_AIRE)
        if y < yn:
            entra += q
        else:
            sale += q
    if suelo:
        entra += caudal_suelo(g * yn * 1e-3, cd=cd, **suelo)
    return entra, sale


def salto(p: dict[str, float], cd: float = cb.CD_TIRO, costados: int = 2,
          suelo: dict | None = None) -> dict:
    """dT de la chimenea con el suelo (o sin el, suelo=None), y su plano neutro."""
    hs = cb._huecos(p, costados)

    def neutro(dt):
        lo, hi = 0.0, max(y for y, _ in hs)
        for _ in range(80):
            yn = (lo + hi) / 2
            e, s = _caudales(hs, yn, dt, cd, suelo)
            lo, hi = (lo, yn) if e > s else (yn, hi)
        return (lo + hi) / 2

    def potencia(dt):
        yn = neutro(dt)
        _, s = _caudales(hs, yn, dt, cd, suelo)
        return cb.RHO_AIRE * cb.CP_AIRE * s * dt, yn

    lo, hi = 0.01, 300.0
    for _ in range(80):
        dt = (lo + hi) / 2
        lo, hi = (dt, hi) if potencia(dt)[0] < p["potencia_disipada"] else (lo, dt)
    dt = (lo + hi) / 2
    _, yn = potencia(dt)
    q_suelo = caudal_suelo(cb.RHO_AIRE * cb.G * dt / cb.T_AMB * yn * 1e-3, cd=cd,
                           **suelo) if suelo else 0.0
    return {"dt": dt, "yn": yn, "q_suelo": q_suelo,
            "q_total": p["potencia_disipada"] / (cb.RHO_AIRE * cb.CP_AIRE * dt)}


def autocomprobacion() -> None:
    """Sin suelo tiene que dar _tiro(); y con el canal sin roce, la serie de
    rendija y agujeros tiene que dar el orificio equivalente de toda la vida,
    a_ef = (a1^-2 + a2^-2)^-1/2, metido en _huecos()."""
    p = cb.leer_params()
    for cd in (cb.CD_TIRO, cb.CD_TIRO_PESIMISTA):
        for costados in (2, 1):
            a = salto(p, cd, costados)["dt"]
            b = cb._tiro(p, cd, costados)["dt"]
            assert abs(a - b) < 1e-6 * b, (a, b)
    w, a_s = 1700.0, 20000.0
    a_ef = 1 / math.sqrt(1 / (w * 10) ** 2 + 1 / a_s ** 2)
    hs = cb._huecos(p) + [(0.0, a_ef)]
    yn, s = cb._plano_neutro(hs)
    k = (cb.RHO_AIRE * cb.CP_AIRE * cb.CD_TIRO * math.sqrt(2 * cb.G / cb.T_AMB)
         * s * 1e-6 * math.sqrt(1e-3))
    esperado = (p["potencia_disipada"] / k) ** (2 / 3)
    sin_roce = salto(p, suelo={"a_suelo": a_s, "w": w, "largo": 0.0, "h": 10.0})
    assert abs(sin_roce["dt"] - esperado) < 1e-6 * esperado, (sin_roce["dt"], esperado)


if __name__ == "__main__":
    autocomprobacion()
    p = cb.leer_params()
    ancho, largo = huella(p)
    f_sala = cb.T_SALA_DISENO_K / cb.T_AMB
    print(f"suelo {ancho:.2f} x {largo:.2f}, perimetro {2 * (ancho + largo):.2f}; "
          f"rendija libre {rendija_libre(p):.0f} mm (un costado tapado: "
          f"{rendija_libre(p, 1):.0f}); {p['potencia_disipada']} W, techo "
          f"{p['salto_termico_max']:g} K")
    print("pesimista: C_D", cb.CD_TIRO_PESIMISTA, "| sala 45: x", round(f_sala, 4))
    zonas = campo(p)
    bruto = sum((x1 - x0) * (z1 - z0) for x0, x1, z0, z1 in zonas)
    for n, (x0, x1, z0, z1) in zip("AB", zonas):
        print(f"campo {n}: x {x0:.1f}..{x1:.1f}, z {z0:.1f}..{z1:.1f} ({(x1 - x0) * (z1 - z0):.0f} mm2)")
    print(f"campo: {bruto:.0f} mm2; con agujeros de 5 cada 8 ({ABIERTO_RV58:.1%}) abre hasta "
          f"{bruto * ABIERTO_RV58:.0f} mm2")
    print()
    print("abierto | patas | canal L | salto  pesim | 1 costado (pesim) | sala 45 (pesim) | suelo/total")
    hoy = [salto(p, cd)["dt"] for cd in (cb.CD_TIRO, cb.CD_TIRO_PESIMISTA)]
    hoy1 = salto(p, cb.CD_TIRO_PESIMISTA, 1)["dt"]
    print(f"{'hoy':>7} | {'-':>5} | {'-':>7} | {hoy[0]:5.2f}  {hoy[1]:5.2f} | "
          f"{hoy1:17.2f} | {hoy[1] * f_sala:15.2f} |")
    for h in (10.0, 20.0):
        for largo_canal in (60.0, 120.0):
            for a_s in (20000.0,):
                fila = []
                for cd, costados in ((cb.CD_TIRO, 2), (cb.CD_TIRO_PESIMISTA, 2),
                                     (cb.CD_TIRO_PESIMISTA, 1)):
                    s = {"a_suelo": a_s, "w": rendija_libre(p, costados),
                         "largo": largo_canal, "h": h}
                    fila.append(salto(p, cd, costados, s))
                frac = fila[1]["q_suelo"] / fila[1]["q_total"]
                print(f"{a_s:7.0f} | {h:5.0f} | {largo_canal:7.0f} | {fila[0]['dt']:5.2f}  "
                      f"{fila[1]['dt']:5.2f} | {fila[2]['dt']:17.2f} | "
                      f"{fila[1]['dt'] * f_sala:15.2f} | {frac:6.0%}")
        print()
