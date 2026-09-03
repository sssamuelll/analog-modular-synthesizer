"""El contrato de curvas.py: lo que las hojas dicen en sus GRAFICAS.

    python hardware/01-power-supply/v4/test_curvas.py

Este test conoce la FORMA de las curvas y, para el derating, una lectura
independiente hecha con los ojos el 2026-09-03 sobre la p. 3 de cada hoja,
con tolerancia (+-2 C, +-6 puntos de carga). Exige ademas que cada numero
venga con su cita. Un numero sin figura citada es un numero inventado con
cara de hoja (2026-09-03: cuatro HUECOS de la v1 estaban dibujados en la p. 3).

Lo que la lectura de hoy corrigio del papel sec.6, y este test fija:

  * las curvas NO acaban en 70 C al 50 %: siguen bajando hasta 85 C (IRM-45:
    33 % a 80, 25 % a 85; IRM-20: 20 % a 80, 5 % a 85). Por encima de 85 C
    el modulo no opera: 0.
  * el codo de 45 C de las salidas de 5 V es de la IRM-20 y la IRM-30, NO de
    la IRM-45. PS6 (IRM-45-5) tiene codo a 50; PS5 (IRM-20-5) a 45.
"""
from __future__ import annotations

import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import curvas                                               # noqa: E402
from curvas import derating, codo_c, psrr_db, DERATING, PSRR_DB, FUENTE  # noqa: E402

PIEZAS = ("LM2941", "LM2991", "LT3045", "LT3094")
# Las curvas que la v4 usa: PS1/PS2 = IRM-20-15, PS3/PS4 = IRM-45-12,
# PS5 = IRM-20-5 (curva "3.3V,5V" de la IRM-20), PS6 = IRM-45-5 (la IRM-45
# dibuja UNA curva para toda la serie).
CURVAS = ("IRM-20", "IRM-20/5V", "IRM-45")

# Lectura independiente (Claude, 2026-09-03, p. 3 de cada hoja, a 230 Vac).
# (T de aire en C, fraccion de carga). Tolerancia abajo.
LEIDO = {
    "IRM-20":    ((50.0, 1.00), (70.0, 0.50), (80.0, 0.20), (85.0, 0.05)),
    "IRM-20/5V": ((45.0, 1.00), (70.0, 0.50), (80.0, 0.20), (85.0, 0.05)),
    "IRM-45":    ((50.0, 1.00), (70.0, 0.50), (80.0, 0.33), (85.0, 0.25)),
}
TOL_T = 2.0
TOL_F = 0.06


# --- derating: forma --------------------------------------------------------

def test_las_curvas_de_la_v4_estan() -> None:
    for c in CURVAS:
        assert c in DERATING, f"{c} no esta en DERATING"
        pts = DERATING[c]
        assert len(pts) >= 3, (c, pts)
        ts = [t for t, _ in pts]
        assert ts == sorted(ts), f"{c}: los puntos no van en T creciente"
        assert all(0.0 <= f <= 1.0 for _, f in pts), (c, pts)


def test_por_debajo_del_codo_es_placa_entera() -> None:
    for c in CURVAS:
        assert derating(25.0, c) == 1.0, c
        assert derating(-20.0, c) == 1.0, c
        assert derating(codo_c(c), c) == 1.0, c


def test_codo_es_la_ultima_temperatura_a_placa_entera() -> None:
    for c in CURVAS:
        assert derating(codo_c(c) + 0.5, c) < 1.0, (
            f"{c}: medio grado por encima del codo ({codo_c(c)}) sigue al 100 %")


def test_monotona_no_creciente_y_llega_a_cero() -> None:
    for c in CURVAS:
        prev = 1.0
        for t10 in range(-300, 1200):
            t = t10 / 10.0
            d = derating(t, c)
            assert 0.0 <= d <= prev + 1e-12, (c, t, d, prev)
            prev = d
        assert derating(120.0, c) == 0.0, (
            f"{c}: a 120 C de aire devuelve {derating(120.0, c)}. Por encima "
            f"del ultimo punto publicado (85 C) el modulo no opera: 0, no una "
            f"meseta con el ultimo valor leido")


def test_interpola_en_los_puntos_de_la_polilinea() -> None:
    for c in CURVAS:
        for t, f in DERATING[c]:
            assert abs(derating(t, c) - f) < 1e-9, (c, t, f, derating(t, c))


def test_interpola_linealmente_entre_puntos() -> None:
    for c in CURVAS:
        pts = DERATING[c]
        for (t0, f0), (t1, f1) in zip(pts, pts[1:]):
            tm = (t0 + t1) / 2.0
            assert abs(derating(tm, c) - (f0 + f1) / 2.0) < 1e-9, (c, t0, t1)


def test_curva_desconocida_se_queja() -> None:
    for c in ("IRM-15-5", "rack", "generico"):
        try:
            derating(50.0, c)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError(
                f"{c!r} no es una curva leida y tiene que fallar, no caer en "
                f"un valor por defecto")


# --- derating: contra la lectura independiente -----------------------------

def test_coincide_con_la_lectura_independiente() -> None:
    for c, leido in LEIDO.items():
        for t, f in leido:
            d = derating(t, c)
            assert abs(d - f) <= TOL_F, (
                f"{c} a {t:.0f} C: el guion da {d:.2f} y la lectura "
                f"independiente {f:.2f} (tolerancia {TOL_F})")
        assert abs(codo_c(c) - leido[0][0]) <= TOL_T, (
            f"{c}: codo en {codo_c(c)} y la lectura independiente en "
            f"{leido[0][0]}")


def test_la_salida_de_5v_de_la_irm20_quiebra_antes_que_las_otras() -> None:
    assert codo_c("IRM-20/5V") < codo_c("IRM-20"), (
        f"la curva '3.3V,5V' de la IRM-20 arranca a bajar a "
        f"{codo_c('IRM-20/5V')} y 'OTHERS' a {codo_c('IRM-20')}: tienen que "
        f"ser distintas, es la diferencia que hunde a PS5")
    assert derating(60.0, "IRM-20/5V") < derating(60.0, "IRM-20")


def test_la_irm45_no_distingue_la_salida_de_5v() -> None:
    # La hoja de la IRM-45 dibuja UNA curva para toda la serie. Si el guion
    # inventa una "IRM-45/5V" con codo a 45, esta copiando el papel y no la
    # hoja: PS6 (IRM-45-5) tiene codo a 50.
    assert "IRM-45/5V" not in DERATING, (
        "la IRM-45 no publica curva aparte para 5 V; esa clave no puede existir")
    assert abs(codo_c("IRM-45") - 50.0) <= TOL_T


def test_por_encima_de_70_sigue_bajando() -> None:
    # Es lo que el papel sec.6 no decia: "hasta el 50 % a 70 C" no es el final
    for c in CURVAS:
        assert derating(80.0, c) < derating(70.0, c) - 0.1, (
            f"{c}: entre 70 y 80 C no baja: {derating(70.0, c):.2f} -> "
            f"{derating(80.0, c):.2f}. La hoja sigue bajando hasta 85")


# --- PSRR -----------------------------------------------------------------

# Hasta donde llega el eje de frecuencia de cada figura (lectura independiente,
# Claude, 2026-09-03). Los LM publican hasta 1 MHz y NO MAS: pedirles 10 MHz
# es pedir un numero que la hoja no tiene.
F_MAX_PUBLICADA = {"LM2941": 1e6, "LM2991": 1e6, "LT3045": 10e6, "LT3094": 10e6}


def test_cada_pieza_tiene_puntos_hasta_donde_publica_su_hoja() -> None:
    for pieza in PIEZAS:
        fs = sorted(f for (p, f) in PSRR_DB if p == pieza)
        assert len(fs) >= 4, f"{pieza}: {len(fs)} puntos; hacen falta al menos 65 kHz, 100 kHz, 1 MHz y el ultimo publicado"
        assert fs[0] <= 65e3, f"{pieza}: el primer punto ({fs[0]:.3g}) esta por encima de 65 kHz"
        assert abs(fs[-1] - F_MAX_PUBLICADA[pieza]) / F_MAX_PUBLICADA[pieza] < 0.05, (
            f"{pieza}: el ultimo punto leido es {fs[-1]:.3g} Hz y la figura llega "
            f"hasta {F_MAX_PUBLICADA[pieza]:.3g}. Ni mas (seria inventado) ni "
            f"menos (se dejo sin leer el tramo de los flancos)")


def test_los_lm_no_tienen_datos_a_10_mhz() -> None:
    # Fig. 9 del LM2941 y Fig. 8 del LM2991 acaban en 1 MHz. Un valor a 10 MHz
    # para ellos es una invencion, y rizado_budget.py tiene que ENTERARSE de
    # que ahi no hay hoja (ValueError), no recibir un numero.
    for pieza in ("LM2941", "LM2991"):
        try:
            psrr_db(pieza, 10e6)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"{pieza}: a 10 MHz devolvio {psrr_db(pieza, 10e6):.0f} dB y la "
                f"figura acaba en 1 MHz")


def test_valores_de_db_creibles() -> None:
    for (p, f), db in PSRR_DB.items():
        assert 0.0 <= db <= 140.0, (p, f, db)


def test_psrr_cae_de_1khz_a_100khz() -> None:
    # Un LDO rechaza menos cuanto mas alta la frecuencia, pero NO de forma
    # monotona: el LM2941 tiene su valle en ~100 kHz y SUBE otra vez hacia
    # 1 MHz (Fig. 9), y los LT tienen un pico a ~1-2 MHz por la capacidad de
    # salida. Lo que si es cierto en las cuatro figuras: de 1 kHz a 100 kHz
    # baja. Es el tramo que separa la banda de audio de la conmutacion.
    for pieza in PIEZAS:
        assert psrr_db(pieza, 100e3) < psrr_db(pieza, 1e3), (
            f"{pieza}: PSRR a 100 kHz ({psrr_db(pieza, 100e3):.0f} dB) no es "
            f"menor que a 1 kHz ({psrr_db(pieza, 1e3):.0f}): los puntos estan "
            f"al reves o se leyo otra figura")


def test_los_lt_rechazan_mas_que_los_lm() -> None:
    # Es para lo que se compraron: el LT3045 publica >70 dB a 65 kHz donde el
    # LM2941 anda por los 30-50. Si salen parecidos, una de las dos lecturas
    # es de otra figura.
    assert psrr_db("LT3045", 65e3) > psrr_db("LM2941", 65e3) + 10.0
    assert psrr_db("LT3094", 65e3) > psrr_db("LM2991", 65e3) + 10.0


def test_interpola_en_los_puntos_leidos() -> None:
    for (p, f), db in PSRR_DB.items():
        assert abs(psrr_db(p, f) - db) < 1e-9, (p, f)


def test_interpola_entre_puntos_sin_salirse() -> None:
    for pieza in PIEZAS:
        pts = sorted((f, db) for (p, f), db in PSRR_DB.items() if p == pieza)
        for (f0, d0), (f1, d1) in zip(pts, pts[1:]):
            fm = (f0 * f1) ** 0.5           # medio en log(f)
            dm = psrr_db(pieza, fm)
            lo, hi = min(d0, d1), max(d0, d1)
            assert lo - 1e-9 <= dm <= hi + 1e-9, (pieza, f0, f1, dm)


def test_fuera_de_la_grafica_se_queja() -> None:
    for pieza in PIEZAS:
        for f in (0.1, 1e9):
            try:
                psrr_db(pieza, f)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    f"{pieza}: a {f:g} Hz no hay hoja que leer. Extrapolar el "
                    f"PSRR fuera de su grafica es inventarse el numero que "
                    f"decide si el riel de 0,8 uV existe")


def test_pieza_desconocida_se_queja() -> None:
    try:
        psrr_db("LM317", 65e3)
    except ValueError:
        pass
    else:
        raise AssertionError("una pieza sin puntos leidos tiene que fallar")


# --- la cita: cada numero dice de que pagina y figura sale ----------------

# Las paginas que se renderizaron y se leyeron con los ojos el 2026-09-03.
# Si una constante cita otra pagina, o se leyo otra cosa o se invento.
PAGINAS_LEIDAS = {
    "IRM-20": ("meanwell-irm-20-spec-2025-11-21.pdf", {3}),
    "IRM-20/5V": ("meanwell-irm-20-spec-2025-11-21.pdf", {3}),
    "IRM-45": ("meanwell-irm-45-spec-2025-11-21.pdf", {3}),
    "LM2941": ("lm2941-snvs770i-2015-01.pdf", {8}),
    "LM2991": ("lm2991-snvs099i-2016-10.pdf", {7}),
    "LT3045": ("lt3045-rev-d.pdf", {9, 10}),
    "LT3094": ("lt3094-rev-b.pdf", {11, 12}),
}


def _pagina_citada(cita: str) -> int | None:
    m = re.search(r"\bp(?:\.|ag(?:ina)?\.?)?\s*(\d+)\b", cita)
    return int(m.group(1)) if m else None


def test_cada_curva_de_derating_cita_su_hoja_y_pagina() -> None:
    for c in CURVAS:
        assert c in FUENTE, f"{c} no tiene cita en FUENTE"
        cita = FUENTE[c]
        hoja, pags = PAGINAS_LEIDAS[c]
        assert hoja in cita, f"{c}: la cita no nombra {hoja}: {cita!r}"
        p = _pagina_citada(cita)
        assert p in pags, f"{c}: cita p{p}, y lo leido fue {sorted(pags)}: {cita!r}"
        assert "230" in cita, (
            f"{c}: la cita no dice a que tension de entrada se leyo (230 Vac); "
            f"la IRM-30 dibuja curvas distintas a 100 y a 230: {cita!r}")


def test_cada_pieza_de_psrr_cita_su_figura() -> None:
    for pieza in PIEZAS:
        assert pieza in FUENTE, f"{pieza} no tiene cita en FUENTE"
        cita = FUENTE[pieza]
        hoja, pags = PAGINAS_LEIDAS[pieza]
        assert hoja in cita, f"{pieza}: la cita no nombra {hoja}: {cita!r}"
        p = _pagina_citada(cita)
        assert p in pags, f"{pieza}: cita p{p}, y lo leido fue {sorted(pags)}: {cita!r}"
        assert re.search(r"Fig(?:ure|\.)?\s*\d+|\bG\d\d\b", cita), (
            f"{pieza}: la cita no nombra la figura: {cita!r}")
        # La figura del LM2941 esta a IO = 10 mA y VO = 5 V; la G43 del
        # LT3045 a IL = 500 mA. Ninguna es la condicion de la v4 (650 mA,
        # 12 V). Si la cita no dice a que corriente se leyo, rizado_budget.py
        # no puede saber cuanto se aleja del punto real.
        assert re.search(r"\d+\s*mA", cita), (
            f"{pieza}: la cita no dice a que corriente de carga esta la "
            f"figura: {cita!r}")


def test_cada_dato_lleva_la_fecha_de_lectura() -> None:
    for k, cita in FUENTE.items():
        assert re.search(r"2026-\d\d-\d\d", cita), (
            f"{k}: la cita no dice cuando se leyo: {cita!r}")


if __name__ == "__main__":
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
    print("OK: curvas.py")
