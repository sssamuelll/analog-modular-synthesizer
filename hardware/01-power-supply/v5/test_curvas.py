"""Pruebas de `v5/curvas.py`: series, no-extrapolacion y trazabilidad a PDF.

    python test_curvas.py
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(DIR, "..", "..", ".."))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

import curvas as cv  # noqa: E402


def test_archivos_fuente_existen() -> None:
    for diccionario in (cv.FUENTES_DERATING_V5, cv.FUENTES_PSRR_V5):
        for clave, (rel, pag, desc) in diccionario.items():
            ruta = os.path.join(RAIZ, rel)
            assert os.path.isfile(ruta), f"{clave}: no existe el PDF {ruta}"
            assert pag >= 1, f"{clave}: pagina invalida {pag}"
            assert desc.strip(), f"{clave}: descripcion vacia"


def test_sin_lm2941() -> None:
    assert "LM2941" not in cv.PSRR_DB_V5
    assert "LT1963A" in cv.PSRR_DB_V5
    assert "LT3015" in cv.PSRR_DB_V5
    assert "LT3045" in cv.PSRR_DB_V5
    assert "LT3094" in cv.PSRR_DB_V5


def test_derating_monotono_y_anclado() -> None:
    for nombre, pts in cv.DERATING_V5.items():
        for (_, y0), (_, y1) in zip(pts, pts[1:]):
            assert y1 <= y0 + 1e-12, f"{nombre}: el derating sube con la temperatura"
        assert abs(cv.derating(nombre, 25.0) - 1.0) < 1e-12

    # Puntos exactos de hoja a 65 C (convertidores) y 45 C (ladrillos):
    assert abs(cv.derating("THN-30-2422WI", 65.0) - 1.00) < 1e-12
    assert abs(cv.derating("THN-20-2413WI", 75.0) - 1.00) < 1e-12
    assert abs(cv.derating("URB2405YMD-20WR3", 65.0) - 1.00) < 1e-12
    assert abs(cv.derating("URB2405YMD-20WR3", 75.0) - 0.75) < 1e-12
    assert abs(cv.derating("K7805T-1000R3", 65.0) - 0.92) < 1e-12
    assert abs(cv.derating("TE90A2403F01", 45.0) * 90.0 - 82.5) < 1e-9
    assert abs(cv.derating("GST120A24-R7B-230V", 45.0) * 120.0 - 120.0) < 1e-9
    assert abs(cv.derating("GSM120A24-R7B", 45.0) * 120.0 - 108.0) < 1e-9


def test_no_extrapola() -> None:
    for fn, arg, x in (
        (cv.derating, "URB2405YMD-20WR3", -50.0),
        (cv.derating, "URB2405YMD-20WR3", 90.0),
        (cv.psrr_db, "LT1963A", 5.0),
        (cv.psrr_db, "LT1963A", 2_000_000.0),
        (cv.psrr_db, "LT3045", 20_000_000.0),
    ):
        try:
            fn(arg, x)
        except ValueError as exc:
            assert "no extrapola" in str(exc)
        else:
            raise AssertionError(f"extrapolo {arg} en {x}")


def main() -> int:
    test_archivos_fuente_existen()
    test_sin_lm2941()
    test_derating_monotono_y_anclado()
    test_no_extrapola()
    print("OK: test_curvas.py v5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
