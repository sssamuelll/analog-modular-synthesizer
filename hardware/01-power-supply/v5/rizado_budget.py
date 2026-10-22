"""Rechazo de rizado diferencial de la cascada ultra en la fuente v5 (T12).

    python rizado_budget.py

En la v5 los convertidores crudos **TRACO THN 20-2413WI** (`traco_thn20wi.pdf`
p. 2) conmutan a **330 kHz** tipicos (270-330 kHz) con un rizado de salida de
**75 mVp-p tipico / 100 mVp-p maximo** en 20 MHz de ancho de banda (con un
condensador ceramico de 10 uF/25 V X7R MLCC, Nota 1 de p. 2). Es la mitad del
rizado de 200 mVp-p de los Mean Well IRM-20-15 de la v4 y a una frecuencia 5
veces mas alta, donde el filtro LC amortiguado de 4,95 kHz atenua todavia mas.

La cadena de rechazo conserva:
  - Filtro LC amortiguado (`22 uH` + `47 uF` + rama `Rd = 0,68 ohm` + `220 uF`)
  - Perla de ferrita amortiguada (`600 ohm @ 100 MHz` + `100 nF` + `2,2 ohm` + `2,2 uF`)
  - Prerreguladores: `U1 = LT1963A` (D-F8, curva leida en `lt1963a-rev-g-2021-02.pdf`
    p. 11 G31) y `U2 = LT3015` (D-F9, `lt3015-rev-b.pdf` p. 11 G41)
  - Reguladores finales: `U3 = LT3045` (`lt3045-rev-d.pdf` p. 10 G43) y
    `U4 = LT3094` (`lt3094-rev-b.pdf` p. 11 G43)

Verifica el barrido completo de 65 kHz a 20 MHz y particularmente la fundamental
de 330 kHz del THN 20-2413WI contra el techo de `0,30 uVrms`.
"""
from __future__ import annotations

import importlib.util
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(DIR, "..", "v4")
if V4 not in sys.path:
    sys.path.append(V4)

_spec_rb4 = importlib.util.spec_from_file_location(
    "_v4_rizado_budget", os.path.join(V4, "rizado_budget.py"))
assert _spec_rb4 and _spec_rb4.loader
rb4 = importlib.util.module_from_spec(_spec_rb4)
_spec_rb4.loader.exec_module(rb4)

# Datos de hoja del TRACO THN 20-2413WI (traco_thn20wi.pdf p. 2):
F_SW_THN_HZ = 330_000.0
RIZADO_THN_TYP_VPP = 0.075
RIZADO_THN_MAX_VPP = 0.100
COTA_RIEL_UV = rb4.COTA_RUIDO_V * 1e6  # 0,30 uVrms


def rizado_al_riel_330khz_uv(*, vpp_fuente: float = RIZADO_THN_MAX_VPP) -> float:
    """Rizado en el riel ultra a 330 kHz (fundamental del THN 20-2413WI)."""
    v_rms_in = vpp_fuente / (2.0 * (2.0 ** 0.5))
    peor_db = min(rb4.cadena_db(rama, F_SW_THN_HZ) for rama in rb4.RAMAS)
    return v_rms_in * (10.0 ** (-peor_db / 20.0)) * 1e6


def demo() -> int:
    print("rizado_budget v5: rechazo desde el THN 20-2413WI (330 kHz, <= 100 mVp-p) hasta +-12 V ultra\n")
    assert rb4.RAMAS["+15 -> U1 -> LT3045"] == ("LT1963A", "LT3045"), (
        "la rama positiva debe usar LT1963A (D-F8)")
    assert rb4.RAMAS["-15 -> U2 -> LT3094"] == ("LT3015", "LT3094"), (
        "la rama negativa debe usar LT3015 (D-F9)")

    f_330 = F_SW_THN_HZ
    lc_db = rb4._db(rb4.h_lc(f_330))
    perla_db = rb4._db(rb4.h_ferrita(f_330))
    for nombre_rama, (pre, lt) in rb4.RAMAS.items():
        pre_db = rb4.psrr_leido_db(pre, f_330)
        lt_db = rb4.psrr_leido_db(lt, f_330)
        tot_db = rb4.cadena_db(nombre_rama, f_330)
        print(f"  rama {nombre_rama} @ 330 kHz:")
        print(f"    LC={lc_db:.1f} dB + perla={perla_db:.1f} dB + "
              f"pre={pre_db:.1f} dB + LT={lt_db:.1f} dB -> total={tot_db:.1f} dB")

    u_330 = rizado_al_riel_330khz_uv()
    f_peor, v_peor = rb4.peor_de_la_banda(con_ferrita=True)
    f_sin, v_sin = rb4.peor_de_la_banda(con_ferrita=False)
    u_peor = v_peor * 1e6
    u_sin = v_sin * 1e6
    print(f"\n  a 330 kHz (100 mVp-p max del THN 20-2413WI): {u_330:.6f} uVrms "
          f"(cota <= {COTA_RIEL_UV:.2f} uVrms)")
    print(f"  peor punto en barrido 65 kHz..20 MHz CON ferrita: "
          f"{u_peor:.4f} uVrms @ {f_peor/1e6:.1f} MHz")
    print(f"  peor punto en barrido 65 kHz..20 MHz SIN ferrita: "
          f"{u_sin:.2f} uVrms @ {f_sin/1e6:.1f} MHz (ROJO sin ferrita)")

    rb4._guarda_banda(dict(rb4.P_BASE))
    z_min = rb4.borde_rojo(
        rb4._guarda_banda, dict(rb4.P_BASE),
        "z_ferrita_100mhz_ohm", 1.0, 600.0, "contra 0.30 de cota")
    print(f"  canario: por debajo de {z_min:.0f} ohm @ 100 MHz en la perla, "
          f"el barrido supera los {COTA_RIEL_UV:.2f} uVrms")

    assert u_330 < 0.001
    assert u_peor <= COTA_RIEL_UV
    assert u_sin > COTA_RIEL_UV
    print("\nOK: rizado_budget.py v5")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
