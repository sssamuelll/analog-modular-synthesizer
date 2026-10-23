"""Curvas de derating y PSRR de la fuente v5, leidas de las hojas versionadas.

    python curvas.py

Releva a `v4/curvas.py` para los convertidores DC-DC interiores y los ladrillos
AC-DC candidatos de la v5, manteniendo los cuatro reguladores de la cascada
ultra (`LT1963A`, `LT3015`, `LT3045`, `LT3094`). Ninguna serie conserva ya al
`LM2941` retirado por D-F8.

Todas las hojas estan en `docs/reference/datasheets/` y registradas en
`docs/references.md`. Fuera del dominio impreso en la figura se lanza
`ValueError`: no se extrapola.
"""
from __future__ import annotations

import importlib.util
import math
import os

Punto = tuple[float, float]


def _valida_serie(nombre: str, pts: tuple[Punto, ...]) -> None:
    if len(pts) < 2:
        raise ValueError(f"{nombre}: una serie necesita al menos dos puntos")
    for (x0, _), (x1, _) in zip(pts, pts[1:]):
        if not (x1 > x0):
            raise ValueError(f"{nombre}: las abscisas no son estrictamente crecientes ({x0} >= {x1})")


# ---------------------------------------------------------------------------
# 1. DERATING TERMICO (fraccion de potencia/corriente nominal, 0..1)
#    Abscisa: temperatura ambiente en grados Celsius.
# ---------------------------------------------------------------------------
DERATING_V5: dict[str, tuple[Punto, ...]] = {
    # TRACO THN 30-2422WI (`traco_thn30wi.pdf` p. 2, "Operating temperature
    # range -40C to +85C, derating above 65C without heatsink, max case
    # temperature +105C"): 100 % hasta 65 C, cae linealmente a 0 % en 105 C.
    "THN-30-2422WI": (
        (-40.0, 1.00),
        (65.0,  1.00),
        (85.0,  0.50),
        (105.0, 0.00),
    ),
    # TRACO THN 20-2413WI (`traco_thn20wi.pdf` p. 2, "Operating temperature
    # range -40C to +85C, derating above 75C without heatsink, max case
    # temperature +105C"): 100 % hasta 75 C, cae linealmente a 0 % en 105 C.
    "THN-20-2413WI": (
        (-40.0, 1.00),
        (65.0,  1.00),
        (75.0,  1.00),
        (90.0,  0.50),
        (105.0, 0.00),
    ),
    # Mornsun URB2405YMD-20WR3 (`mornsun_urb_ymd20wr3.pdf` p. 3, Fig. 1
    # "Temperature Derating Curve" a 24 VDC): 100 % de -40 C a +65 C, cae
    # linealmente al 50 % en +85 C.
    "URB2405YMD-20WR3": (
        (-40.0, 1.00),
        (65.0,  1.00),
        (85.0,  0.50),
    ),
    # Mornsun K7805T-1000R3 (`mornsun_k78_t1000r3.pdf` p. 3, Fig. 1 "Temperature
    # Derating Curve" para Vin = 8..26 VDC): 100 % de -40 C a +60 C, cae
    # linealmente al 60 % en +85 C (a 65 C da 92 %).
    "K7805T-1000R3": (
        (-40.0, 1.00),
        (60.0,  1.00),
        (65.0,  0.92),
        (85.0,  0.60),
    ),
    # RECOM RPMB5.0-2.0 (`recom_rpmb20.pdf` p. 1, 3, "Thermal Derating" a
    # Vin = 24 V): 100 % (2,0 A) de -40 C a +75 C, cae a 0 A en +100 C.
    "RPMB5.0-2.0": (
        (-40.0, 1.00),
        (65.0,  1.00),
        (75.0,  1.00),
        (100.0, 0.00),
    ),
    # AE/SL Power TE90A2403F01 (`ae-TE90-datasheet.pdf` p. 3, "Operating
    # Temperature: -20C to +70C. Derate linearly above 40C to 50% load at 70C"):
    # 90 W hasta 40 C, 82,5 W (91,67 %) a 45 C, 45 W (50 %) a 70 C.
    "TE90A2403F01": (
        (-20.0, 1.00),
        (40.0,  1.00),
        (45.0,  82.5 / 90.0),
        (70.0,  0.50),
    ),
    # Mean Well GST120A24-R7B a 230 VAC (`meanwell-GST120A-spec.pdf` p. 3,
    # "Derating Curve" curva 230 VAC): 100 % (120 W) de -30 C a +50 C, cae
    # linealmente al 50 % en +70 C.
    "GST120A24-R7B-230V": (
        (-30.0, 1.00),
        (45.0,  1.00),
        (50.0,  1.00),
        (70.0,  0.50),
    ),
    # Mean Well GST120A24-R7B a 100 VAC (`meanwell-GST120A-spec.pdf` p. 3,
    # "Derating Curve" curva 100 VAC): 100 % hasta 40 C, 90 % a 45 C, 80 % a
    # 50 C, 40 % a 70 C.
    "GST120A24-R7B-100V": (
        (-30.0, 1.00),
        (40.0,  1.00),
        (45.0,  0.90),
        (50.0,  0.80),
        (70.0,  0.40),
    ),
    # Mean Well GSM120A24-R7B (`meanwell-GSM120A-spec.pdf` p. 3, "Derating
    # Curve" a 230 VAC): 100 % de -30 C a +40 C, 90 % a 45 C, 80 % a 50 C,
    # 40 % a 70 C.
    "GSM120A24-R7B": (
        (-30.0, 1.00),
        (40.0,  1.00),
        (45.0,  0.90),
        (50.0,  0.80),
        (70.0,  0.40),
    ),
}

FUENTES_DERATING_V5: dict[str, tuple[str, int, str]] = {
    "THN-30-2422WI": (
        "docs/reference/datasheets/traco_thn30wi.pdf", 2,
        "Operating temperature range -40..+85 C, derating above 65 C, Tc max 105 C",
    ),
    "THN-20-2413WI": (
        "docs/reference/datasheets/traco_thn20wi.pdf", 2,
        "Operating temperature range -40..+85 C, derating above 75 C, Tc max 105 C",
    ),
    "URB2405YMD-20WR3": (
        "docs/reference/datasheets/mornsun_urb_ymd20wr3.pdf", 3,
        "Fig. 1 Temperature Derating Curve (Vin=24 VDC): 100% <= 65 C, 50% @ 85 C",
    ),
    "K7805T-1000R3": (
        "docs/reference/datasheets/mornsun_k78_t1000r3.pdf", 3,
        "Fig. 1 Temperature Derating Curve (Vin=8..26 VDC): 100% <= 60 C, 60% @ 85 C",
    ),
    "RPMB5.0-2.0": (
        "docs/reference/datasheets/recom_rpmb20.pdf", 3,
        "Thermal Derating @ Vin=24 V: 100% <= 75 C, 0% @ 100 C",
    ),
    "TE90A2403F01": (
        "docs/reference/datasheets/ae-TE90-datasheet.pdf", 3,
        "Operating Temperature: 90 W <= 40 C, -1.5 W/C to 45 W @ 70 C (82.5 W @ 45 C)",
    ),
    "GST120A24-R7B-230V": (
        "docs/reference/datasheets/meanwell-GST120A-spec.pdf", 3,
        "Derating Curve (230 VAC): 100% <= 50 C, 50% @ 70 C",
    ),
    "GST120A24-R7B-100V": (
        "docs/reference/datasheets/meanwell-GST120A-spec.pdf", 3,
        "Derating Curve (100 VAC): 100% <= 40 C, 90% @ 45 C, 80% @ 50 C, 40% @ 70 C",
    ),
    "GSM120A24-R7B": (
        "docs/reference/datasheets/meanwell-GSM120A-spec.pdf", 3,
        "Derating Curve (230 VAC): 100% <= 40 C, 90% @ 45 C, 80% @ 50 C, 40% @ 70 C",
    ),
}


# ---------------------------------------------------------------------------
# 2. PSRR DE LA CASCADA ULTRA (dB, positivo = atenua)
#    Abscisa: frecuencia en Hz (interpolacion en log10(f)).
# ---------------------------------------------------------------------------
PSRR_DB_V5: dict[str, tuple[Punto, ...]] = {
    # ADI LT1963A (`lt1963a-rev-g-2021-02.pdf` p. 11, G31 "Ripple Rejection",
    # I_L = 0.75 A, COUT = 10 uF ceramico): D-F8 (U1).
    "LT1963A": (
        (1_000.0,     68.0),
        (10_000.0,    56.0),
        (65_000.0,    38.0),
        (100_000.0,   35.0),
        (1_000_000.0, 23.0),
    ),
    # ADI LT3015 (`lt3015-rev-b.pdf` p. 11, G41 "Input Ripple Rejection",
    # traza roja COUT=47 uF, CFF=10 nF, IL=-1.5 A, VOUT=-5 V): D-F9 (U2).
    "LT3015": (
        (1_000.0,      52.0),
        (10_000.0,     51.5),
        (65_000.0,     41.0),
        (100_000.0,    39.0),
        (1_000_000.0,  46.5),
        (2_000_000.0,  35.5),
        (10_000_000.0, 33.0),
    ),
    # ADI LT3045 (`lt3045-rev-d.pdf` p. 10, G43 "Power Supply Ripple Rejection",
    # traza roja IL=500 mA, VIN=5 V, COUT=10 uF, CSET=0.47 uF): U3 (+12 ultra).
    "LT3045": (
        (1_000.0,      109.0),
        (10_000.0,      91.0),
        (65_000.0,      79.5),
        (100_000.0,     77.5),
        (1_000_000.0,   76.0),
        (2_000_000.0,   88.0),
        (10_000_000.0,  54.0),
    ),
    # ADI LT3094 (`lt3094-rev-b.pdf` p. 11, G43 "Power Supply Ripple Rejection",
    # traza roja IL=-500 mA, VIN=-5 V, COUT=10 uF, CSET=4.7 uF): U4 (-12 ultra).
    "LT3094": (
        (1_000.0,      107.0),
        (10_000.0,      94.0),
        (65_000.0,      78.0),
        (100_000.0,     75.0),
        (1_000_000.0,   72.0),
        (2_000_000.0,   81.0),
        (10_000_000.0,  27.0),
    ),
}

FUENTES_PSRR_V5: dict[str, tuple[str, int, str]] = {
    "LT1963A": (
        "docs/reference/datasheets/lt1963a-rev-g-2021-02.pdf", 11,
        "Ripple Rejection (1963A G31), IL=0.75A, COUT=10uF",
    ),
    "LT3015": (
        "docs/reference/datasheets/lt3015-rev-b.pdf", 11,
        "Input Ripple Rejection (3015 G41), COUT=47uF, CFF=10nF, IL=-1.5A",
    ),
    "LT3045": (
        "docs/reference/datasheets/lt3045-rev-d.pdf", 10,
        "Power Supply Ripple Rejection (3045 G43), IL=500mA, COUT=10uF, CSET=0.47uF",
    ),
    "LT3094": (
        "docs/reference/datasheets/lt3094-rev-b.pdf", 11,
        "Power Supply Ripple Rejection (3094 G43), IL=-500mA, COUT=10uF, CSET=4.7uF",
    ),
}

for _k, _pts in (*DERATING_V5.items(), *PSRR_DB_V5.items()):
    _valida_serie(_k, _pts)


def _interp(pts: tuple[Punto, ...], x: float, *, logx: bool,
            etiqueta: str) -> float:
    xmin, xmax = pts[0][0], pts[-1][0]
    if not (xmin <= x <= xmax):
        raise ValueError(
            f"{etiqueta}={x:g} cae fuera de [{xmin:g}, {xmax:g}] de la figura "
            f"de la hoja; este modulo no extrapola")
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            if x == x0:
                return y0
            if x == x1:
                return y1
            if logx:
                t = (math.log10(x) - math.log10(x0)) / (math.log10(x1) - math.log10(x0))
            else:
                t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return pts[-1][1]


_DIR = os.path.dirname(os.path.abspath(__file__))
_V4_CURVAS_PATH = os.path.join(_DIR, "..", "v4", "curvas.py")
_spec_cv4 = importlib.util.spec_from_file_location("_v4_curvas", _V4_CURVAS_PATH)
assert _spec_cv4 and _spec_cv4.loader
_cv4 = importlib.util.module_from_spec(_spec_cv4)
_spec_cv4.loader.exec_module(_cv4)

DERATING = {**_cv4.DERATING, **DERATING_V5}
PSRR_DB = _cv4.PSRR_DB
FUENTE = _cv4.FUENTE
codo_c = _cv4.codo_c


def derating(a: str | float, b: float | str) -> float:
    """Fraccion de potencia/corriente admisible (0..1).

    Acepta tanto `(pieza, t_amb_c)` (convencion v5) como `(t_amb_c, curva)`
    (convencion de `v4/calor_budget.py` cuando importa `curvas` con `v5` en
    `sys.path`).
    """
    if isinstance(a, str):
        pieza, t_amb_c = a, float(b)
        if pieza not in DERATING_V5:
            raise KeyError(f"sin curva de derating para {pieza!r} en v5")
        return _interp(DERATING_V5[pieza], t_amb_c, logx=False,
                       etiqueta=f"T_amb({pieza})")
    return _cv4.derating(float(a), str(b))


def psrr_db(regulador: str, f_hz: float) -> float:
    """PSRR en dB (positivo = atenua) a `f_hz` Hz, interpolado en log10(f)."""
    if regulador not in PSRR_DB_V5:
        raise KeyError(f"sin curva de PSRR para {regulador!r} en v5")
    return _interp(PSRR_DB_V5[regulador], f_hz, logx=True,
                   etiqueta=f"f({regulador})")


def _demo() -> int:
    print("curvas.py v5 -- derating de convertidores/ladrillos y PSRR de cascada\n")
    print("  1. Derating de convertidores interiores a T_case = 65 C (techo v5 sec.6):")
    for pieza in ("THN-30-2422WI", "THN-20-2413WI", "URB2405YMD-20WR3",
                  "K7805T-1000R3", "RPMB5.0-2.0"):
        pdf, pag, _ = FUENTES_DERATING_V5[pieza]
        f65 = derating(pieza, 65.0)
        f85 = derating(pieza, 85.0)
        print(f"    {pieza:<20} @ 65 C: {100*f65:5.1f}%   @ 85 C: {100*f85:5.1f}%   "
              f"({pdf} p.{pag})")

    print("\n  2. Derating de ladrillos externos a T_amb = 45 C (sala de diseno):")
    for pieza, w_nom in (("TE90A2403F01", 90.0),
                         ("GST120A24-R7B-230V", 120.0),
                         ("GST120A24-R7B-100V", 120.0),
                         ("GSM120A24-R7B", 120.0)):
        pdf, pag, _ = FUENTES_DERATING_V5[pieza]
        f45 = derating(pieza, 45.0)
        print(f"    {pieza:<20} @ 45 C: {100*f45:5.1f}% ({w_nom*f45:5.1f} W)   "
              f"({pdf} p.{pag})")

    print("\n  3. PSRR de la cascada ultra en 330 kHz (conmutacion THN 20-2413WI):")
    for reg in ("LT1963A", "LT3015", "LT3045", "LT3094"):
        pdf, pag, _ = FUENTES_PSRR_V5[reg]
        print(f"    {reg:<10} @ 1 kHz: {psrr_db(reg, 1e3):5.1f} dB   "
              f"@ 330 kHz: {psrr_db(reg, 330e3):5.1f} dB   "
              f"@ 1 MHz: {psrr_db(reg, 1e6):5.1f} dB   ({pdf} p.{pag})")

    assert "LM2941" not in PSRR_DB_V5, "LM2941 retirado por D-F8 no debe estar en v5"
    print("\nOK: curvas.py v5")
    return 0


if __name__ == "__main__":
    raise SystemExit(_demo())
