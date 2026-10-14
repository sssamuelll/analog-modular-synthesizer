"""Que le cuesta al musico un cuelgue del SPI del cerebro, y cuanto margen queda.

    python recuperacion_j2_budget.py

Spec: `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md` sec.8.
Plan: `docs/superpowers/plans/2026-09-04-maestro-j2-recuperacion.md`, tarea 6.

El problema que mide: hay un defecto abierto en el SPI del STM32N6 o en su
driver (embassy-rs/embassy#5607, sin diagnostico desde 2026-03-05). Cuando el
maestro se cuelga, el modulo deja de recibir trama y a los ~50 ms suelta todas
las notas. Este guion contesta una sola pregunta: **cuanto tarda el cerebro en
recuperarse, contra cuanto aguanta el modulo.**

R-MJ4 manda que los umbrales NO se copien aqui: se LEEN de `maestro_j2.rs`. Si
alguien cambia un ESTIMADO en el Rust y no aqui, este guion se entera. Si
alguien renombra el struct, este guion FALLA en vez de aseverar sobre aire --
un presupuesto que asevera contra su propia copia de los numeros no asevera
nada.

Lo que este guion NO sabe, y sale con HUECO por ello:

  * La tasa REAL del defecto en nuestro montaje. El hilo da dos ordenes de
    magnitud de otro montaje (cuelgues con periodo de 10-900 s) y esas no son
    las nuestras: reloj, largo y cadencia son distintos. Sale de la Discovery
    (#231) y se anota en `resistencia_j2.csv`.
  * `T_IWDG`, que es del papel del hub (#291) y todavia no esta declarado.
  * La densidad de EVENTO por giro, que es del musico y no de un guion.
"""
from __future__ import annotations

import os
import re
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _AQUI)
import enlace_budget as eb       # noqa: E402
import trama_j2_budget as tb     # noqa: E402

_RS = os.path.join(_AQUI, "..", "..", "software", "nucleo", "core", "src",
                   "maestro_j2.rs")
_CSV = os.path.join(_AQUI, "..", "..", "software", "nucleo", "fw",
                    "resistencia_j2.csv")

# ESTIMADO. Spec sec.3, con D4 enmendado el 2026-10-14: soltar los canales del
# GPDMA (sin cifra: su Drop espera a que el canal pare) + el reset del SPI por
# RCC + reescribir CFG1 y CFG2. Lo mide el bring-up con osciloscopio.
T_REINICIO_S = 20e-6

# Cuantos giros cuesta alinearse otra vez con el lazo despues de un reinicio.
# El plazo vence en cualquier punto del giro, asi que se pierde el resto del
# giro en curso (1) y sale en el siguiente (1). Spec sec.3: "plazo + reinicio +
# alineacion al giro + un giro".
GIROS_DE_ALINEACION = 2

# Margen que este papel exige entre recuperarse y que el modulo suelte. No es
# de ninguna hoja: es el criterio del propio presupuesto, y se declara.
MARGEN_EXIGIDO = 10.0


def _lee_const_rust(txt: str, nombre: str) -> int:
    m = re.search(rf"pub const {nombre}: u32 = ([\d_]+);", txt)
    if not m:
        raise SystemExit(
            f"maestro_j2.rs no expone `pub const {nombre}: u32`. R-MJ4 dice "
            "que los umbrales viven en un solo sitio y que este guion los LEE: "
            "si el Rust cambio de forma o de nombre, arregla el guion. NO "
            "copies el numero aqui.")
    return int(m.group(1).replace("_", ""))


def del_rust(ruta: str = _RS) -> dict:
    """Lee POR_DEFECTO y las dos constantes de tiempo de maestro_j2.rs (R-MJ4)."""
    with open(ruta, encoding="utf-8") as f:
        txt = f.read()
    m = re.search(r"pub const POR_DEFECTO: Umbrales = Umbrales \{(.+?)\n    \};",
                  txt, re.S)
    if not m:
        raise SystemExit(
            "maestro_j2.rs no expone `pub const POR_DEFECTO: Umbrales`. Ver "
            "R-MJ4: este guion LEE los umbrales, no los copia.")
    campos = {k: int(v.replace("_", ""))
              for k, v in re.findall(r"(\w+): ([\d_]+)", m.group(1))}
    esperados = {"factor_plazo", "t_suelo_plazo_us", "ventana_salud_us",
                 "umbral_inestable", "umbral_muda"}
    faltan = esperados - campos.keys()
    if faltan:
        raise SystemExit(f"POR_DEFECTO no trae {sorted(faltan)}: R-MJ4 roto.")
    campos["periodo_giro_us"] = _lee_const_rust(txt, "PERIODO_GIRO_US")
    campos["t_watchdog_trama_us"] = _lee_const_rust(txt, "T_WATCHDOG_TRAMA_US")
    return campos


def plazo_s(bytes_clocados: int, f_reloj_hz: float, u: dict) -> float:
    """La misma cuenta que `plazo_us()` en maestro_j2.rs (spec D3).

    Si esta funcion y aquella se separan, el presupuesto miente sobre el
    codigo. Por eso los umbrales vienen del Rust y solo la formula se repite.
    """
    t_nominal = bytes_clocados * 8 / f_reloj_hz
    return u["factor_plazo"] * t_nominal + u["t_suelo_plazo_us"] * 1e-6


def csv_tiene_fila(ruta: str = _CSV) -> bool:
    if not os.path.exists(ruta):
        return False
    with open(ruta, encoding="utf-8") as f:
        return len([ln for ln in f if ln.strip()]) > 1


def demo() -> int:
    u = del_rust()
    t_wd = u["t_watchdog_trama_us"] * 1e-6
    periodo = 1.0 / tb.F_LAZO_HZ
    huecos = []

    print(__doc__.split("\n")[0])
    print(f"\n  umbrales LEIDOS de maestro_j2.rs (R-MJ4): {u}")
    print(f"  piso del enlace {tb.F_CONTRATO_HZ/1e6:.0f} MHz, "
          f"peldano 2 (D8) {eb.F_PELDANO_2_HZ/1e6:.1f} MHz, "
          f"lazo {tb.F_LAZO_HZ/1e3:.0f} kHz")

    # --- 1. el plazo respeta su cota, para todo mensaje ------------------
    # R-E1: ningun mensaje del J2 dura mas de T_MENSAJE_MAX_S al piso. De ahi
    # sale el mayor tsize que puede existir, y con el la cota del plazo.
    tsize_max = int(tb.T_MENSAJE_MAX_S * tb.F_CONTRATO_HZ / 8)
    cota_plazo = u["factor_plazo"] * tb.T_MENSAJE_MAX_S + u["t_suelo_plazo_us"] * 1e-6

    print(f"\nEL PLAZO (D3), contra la cota de R-E1 ({tb.T_MENSAJE_MAX_S*1e6:.0f} us)\n")
    print(f"  el mensaje mas largo que R-E1 permite al piso: {tsize_max} B")
    peor = 0.0
    for f_hz, etiq in ((tb.F_CONTRATO_HZ, "piso"), (eb.F_PELDANO_2_HZ, "D8")):
        p = plazo_s(tsize_max, f_hz, u)
        peor = max(peor, p)
        print(f"    a {f_hz/1e6:5.1f} MHz ({etiq:4s}): plazo {p*1e6:6.1f} us")
    print(f"  cota: {cota_plazo*1e6:.0f} us")
    assert peor <= cota_plazo + 1e-12, (
        f"el plazo ({peor*1e6:.1f} us) pasa su propia cota ({cota_plazo*1e6:.0f} "
        "us): o R-E1 cambio o la formula de D3 ya no es la del Rust")

    # Barrido, no dos valores elegidos a mano: NINGUN tsize legal la pasa.
    for b in range(1, tsize_max + 1):
        assert plazo_s(b, tb.F_CONTRATO_HZ, u) <= cota_plazo + 1e-12, \
            f"tsize {b} pide mas plazo que la cota"

    # --- 2. la recuperacion, contra la ventana del modulo ----------------
    t_rec = peor + T_REINICIO_S + GIROS_DE_ALINEACION * periodo
    margen = t_wd / t_rec

    print("\nLA RECUPERACION (D4), contra la ventana del modulo\n")
    print(f"  plazo maximo        {peor*1e6:7.1f} us")
    print(f"  reinicio            {T_REINICIO_S*1e6:7.1f} us   ESTIMADO")
    print(f"  {GIROS_DE_ALINEACION} giros de alineacion {GIROS_DE_ALINEACION*periodo*1e6:7.1f} us")
    print("  ---------------------------------")
    print(f"  recuperacion        {t_rec*1e6:7.1f} us  = "
          f"{t_rec/periodo:.0f} giros")
    print(f"  ventana del modulo  {t_wd*1e6:7.0f} us   ESTIMADO (voz-total sec.9.2)")
    print(f"  MARGEN              {margen:7.0f}x   (exigido {MARGEN_EXIGIDO:.0f}x)")
    assert margen > MARGEN_EXIGIDO, (
        f"la recuperacion ({t_rec*1e6:.0f} us) no deja {MARGEN_EXIGIDO:.0f}x de "
        f"margen contra los {t_wd*1e3:.0f} ms del modulo: da {margen:.1f}x. El "
        "musico oiria el cuelgue")

    # --- 3. la marca `muda` sube ANTES de que el modulo suelte -----------
    t_muda = u["umbral_muda"] * periodo
    print(f"\n  la marca `muda` sube a los {t_muda*1e3:.1f} ms "
          f"({u['umbral_muda']} giros), antes de los {t_wd*1e3:.0f} ms del "
          "modulo")
    assert t_muda < t_wd, (
        "la marca `muda` subiria despues de que el modulo suelte las notas: "
        "llegaria de luto. Es la misma cota que Umbrales::nuevos asevera en "
        "el Rust; si aqui falla y alli no, uno de los dos lee mal")

    # --- 4. CPU por reinicios: cota impresa, sin aserto ------------------
    cpu = tb.F_LAZO_HZ * T_REINICIO_S
    print("\nCPU POR REINICIOS, peor caso (cota por construccion, sin aserto)\n")
    print(f"  una ranura colgandose SIEMPRE: {cpu*100:.0f} % de un nucleo")
    print(f"  las {6} a la vez:              {cpu*6*100:.0f} %")
    print("  Es el instrumento roto, y se acepta que un instrumento roto gaste")
    print("  CPU en intentar no estarlo (D7.2).")

    # --- 5. el golpe perdido: funcion, sin cifra -------------------------
    giros_perdidos = round(t_rec / periodo)
    print("\nEL GOLPE PERDIDO (D6), como funcion de lo que toque el musico\n")
    print(f"  P(golpe perdido por cuelgue) = {giros_perdidos} x P(EVENTO en un giro)")
    for p_ev in (1e-3, 1e-2, 1e-1):
        print(f"    con P(EVENTO)={p_ev:<6g}  ->  {giros_perdidos*p_ev:.3f} por cuelgue")
    print("  Sin aserto: los dos parametros no son de este guion (uno es de la")
    print("  Discovery, el otro del musico). `EVENTO` no tiene red y eso lo")
    print("  decidio la cabecera D7, no este papel.")

    # --- 6. los HUECOS ---------------------------------------------------
    if not csv_tiene_fila():
        huecos.append(
            "resistencia_j2.csv no tiene ni una fila: la tasa REAL del defecto "
            "en nuestro montaje no se conoce (R-MJ8, #231)")
    huecos.append(
        "T_IWDG no esta declarado por el papel del hub (#291). La cota que "
        f"este papel le manda es T_IWDG > {t_wd*1e3:.0f} ms, para que cuando "
        "el chip se reinicie el modulo ya este en release por su cuenta y el "
        "reinicio no anada silencio")
    huecos.append(
        "los ESTIMADO sin sustituir: FACTOR_PLAZO, T_SUELO_PLAZO, T_REINICIO "
        "y la propia ventana de ~50 ms del modulo ('N del plan')")

    print("\nHUECOS (Principio V)\n")
    for h in huecos:
        print(f"  * {h}")

    print(f"\nHUECO: el margen sale {margen:.0f}x con ESTIMADO. Sale con codigo 2 "
          "hasta que\n  la Discovery ponga una fila y el hub declare T_IWDG.")
    return 2


if __name__ == "__main__":
    sys.exit(demo())
