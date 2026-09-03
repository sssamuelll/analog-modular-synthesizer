"""El canario del canario: que borde_rojo() encuentra bordes y avisa si no hay.

    python hardware/tools/test_canario.py

borde_rojo() vivia privada en case/clearance_budget.py. Sale a hardware/tools/
porque la fuente v4 estrena nueve presupuestos y cada uno tiene que ver morder
sus asertos por biseccion, no con dos valores frontera elegidos a mano (que
pasan con y sin la guarda: ya paso, 2026-08-30, cuatro canarios en un dia).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canario import borde_rojo                              # noqa: E402


def _guarda_de_juguete(p: dict[str, float]) -> None:
    assert p["x"] <= 10.0, f"x se pasa de 10: {p['x']:.2f} (texto que muerde)"


def _guarda_con_dos_asertos(p: dict[str, float]) -> None:
    assert p["x"] >= 0.0, "x negativa (otro aserto distinto)"
    assert p["x"] <= 10.0, f"x se pasa de 10: {p['x']:.2f} (texto que muerde)"


def test_encuentra_el_borde() -> None:
    v = borde_rojo(_guarda_de_juguete, {"x": 1.0}, "x", 0.0, 100.0,
                   "texto que muerde")
    assert 10.0 <= v <= 10.5, f"el borde esta en 10, no en {v}"


def test_encuentra_el_borde_desde_arriba() -> None:
    # el rango puede venir al reves: hi no salta y lo salta. Tiene que dar el
    # mismo borde, no depender del orden en que se le den los extremos.
    v = borde_rojo(_guarda_de_juguete, {"x": 50.0}, "x", 100.0, 0.0,
                   "texto que muerde")
    assert 10.0 <= v <= 10.5, f"el borde esta en 10, no en {v}"


def test_avisa_si_el_aserto_no_muerde() -> None:
    try:
        borde_rojo(_guarda_de_juguete, {"x": 1.0}, "x", 0.0, 9.0,
                   "texto que muerde")
    except AssertionError as e:
        assert "no hay ningun valor" in str(e), str(e)
    else:
        raise AssertionError(
            "tenia que quejarse: en [0, 9] la guarda nunca salta")


def test_no_confunde_un_aserto_con_otro() -> None:
    # En [-5, 5] la guarda salta por "x negativa", NO por "texto que muerde".
    # Un canario que acepte cualquier AssertionError deja de distinguir el
    # aserto que vigila del que se rompio de camino.
    try:
        borde_rojo(_guarda_con_dos_asertos, {"x": 1.0}, "x", -5.0, 5.0,
                   "texto que muerde")
    except AssertionError as e:
        assert "no hay ningun valor" in str(e), str(e)
    else:
        raise AssertionError(
            "acepto un AssertionError ajeno como si fuera el suyo")


def test_no_muta_el_diccionario_original() -> None:
    p = {"x": 1.0, "y": 2.0}
    borde_rojo(_guarda_de_juguete, p, "x", 0.0, 100.0, "texto que muerde")
    assert p == {"x": 1.0, "y": 2.0}, (
        "borde_rojo() toco el dict que le pasaron: el siguiente canario "
        "arrancaria desde un estado roto")


def test_no_deja_salida_por_consola() -> None:
    import contextlib
    import io

    def ruidosa(p: dict[str, float]) -> None:
        print("ruido que no debe llegar al informe")
        assert p["x"] <= 10.0, "texto que muerde"

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        borde_rojo(ruidosa, {"x": 1.0}, "x", 0.0, 100.0, "texto que muerde")
    assert buf.getvalue() == "", (
        "las 24 evaluaciones de la biseccion imprimieron: el informe del "
        "presupuesto se llena de basura")


if __name__ == "__main__":
    test_encuentra_el_borde()
    test_encuentra_el_borde_desde_arriba()
    test_avisa_si_el_aserto_no_muerde()
    test_no_confunde_un_aserto_con_otro()
    test_no_muta_el_diccionario_original()
    test_no_deja_salida_por_consola()
    print("OK: canario.py")
