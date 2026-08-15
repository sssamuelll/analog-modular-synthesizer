"""Presupuesto de error de afinacion de la cadena CV, en cents.

    python tuning_budget.py

Hermano de hardware/bus-board/ground_budget.py, y se compone con el: aquel mide
el error que mete la MASA entre modulos, este el que mete la ELECTRONICA del
MIDI/CV. Los dos se suman en el mismo oido.

LA DISTINCION QUE ORGANIZA TODO ESTO, y sin la cual el presupuesto no significa
nada:

  El firmware guarda una tabla de afinacion por nota (tuning.json, 84 notas).
  Esa tabla **absorbe cualquier error estatico y repetible**: el offset del
  amplificador, el error de ganancia de las resistencias, la no linealidad del
  DAC. Se calibra una vez con un afinador y desaparece.

  Lo que la tabla NO puede absorber es lo que cambia DESPUES de calibrar:

    * la deriva termica de la referencia y del amplificador,
    * el ruido,
    * y el error de masa, que depende de lo que esten consumiendo los OTROS
      modulos en ese instante.

  Por eso este fichero tiene dos columnas y solo una de ellas es el
  presupuesto. Meter el offset del TL074 en la cuenta seria inflarla; ignorar
  su DERIVA seria vaciarla.

Consecuencia de diseno que sale sola: entre dos piezas, gana la que menos
DERIVA, no la que menos offset tiene. Es exactamente lo que separa al TL074H
del TL074 clasico.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "bus-board"))
import ground_budget  # noqa: E402

CENTS_POR_MV = 1.2          # 1 V/oct: 1 V = 1200 cents
OBJETIVO_CENTS = 5.0        # la tesis reporto 0.45% en VCO1 = 7.8 cents

# --- rango del CV --------------------------------------------------------
# La tesis usa 3-10 V. Aqui se baja a 0-7 V: mismo span de 7 octavas (C1-C8),
# misma resolucion en cents, y 3 V mas de margen contra el riel de +12 V. El
# offset absoluto no importa — el conversor exponencial del VCO lo absorbe con
# su trimmer de tono grueso, que hay que ajustar de todas formas.
V_MIN, V_MAX = 0.0, 7.0
SPAN = V_MAX - V_MIN        # 7 V = 7 octavas = 8400 cents

# --- DAC: AD5686R --------------------------------------------------------
BITS = 16
VREF = 2.5                  # referencia interna
GAIN_DAC = 1                # pin GAIN: x1 -> 0..2.5 V. Ver decision() abajo.
# OJO con la hoja que se lea. La primera version de este fichero uso los
# numeros del AD5686R-**EP** (grado enhanced, LFCSP) porque fue el PDF que
# salio primero al buscar, y son PEORES: INL +-4 LSB y referencia 13 ppm/C max.
# El grado comercial AD5686RBRUZ (TSSOP-16), que es el que pide el BOM, da
# +-2 LSB y 2 ppm/C tipico / 5 ppm/C maximo. Verificado en la hoja
# ad5686r_5685r_5684r.pdf de ADI.
INL_LSB = 2.0               # +-2 LSB max a 16 bits, grado comercial
REF_TC_TIP = 2e-6           # ppm/C tipico
REF_TC_MAX = 5e-6           # ppm/C maximo
OFFSET_DAC = 1.5e-3         # +-1.5 mV max — ESTATICO, se calibra

# --- amplificador --------------------------------------------------------
OPAMPS = {
    "TL074C (clasico)": dict(vos=13e-3, tc=18e-6, margen_riel=3.0),
    "TL074H":           dict(vos=4e-3, tc=2e-6, margen_riel=0.210),
}
V_RIEL = 12.0
DELTA_T = 20.0              # C de excursion desde la calibracion. Un cajon
                            # cerrado con tres reguladores dentro sube facil
                            # 15-20 C sobre ambiente en una hora.


def cents(volts: float) -> float:
    return abs(volts) * 1000.0 * CENTS_POR_MV


def ganancia_amp() -> float:
    """Del fondo de escala del DAC al fondo de escala del CV."""
    return SPAN / (VREF * GAIN_DAC)


def resolucion_cents() -> float:
    """Un LSB del DAC, en cents. Solo depende del SPAN, no de la ganancia."""
    return cents(SPAN / (2 ** BITS - 1))


def presupuesto(opamp: str) -> tuple[list, list]:
    """Devuelve (estaticos, dinamicos) como listas de (concepto, cents)."""
    a = OPAMPS[opamp]
    g = ganancia_amp()

    estaticos = [
        (f"INL del DAC (+-{INL_LSB:.0f} LSB)",
         cents(INL_LSB * SPAN / (2 ** BITS - 1))),
        (f"offset del DAC (+-{OFFSET_DAC*1e3:.1f} mV)", cents(OFFSET_DAC * g)),
        (f"offset del amp ({a['vos']*1e3:.0f} mV)", cents(a["vos"] * g)),
        ("tolerancia 1% de la red de ganancia", cents(SPAN * 0.01)),
    ]
    dinamicos = [
        (f"deriva de la referencia ({REF_TC_TIP*1e6:.0f} ppm/C, {DELTA_T:.0f} C)",
         cents(SPAN * REF_TC_TIP * DELTA_T)),
        (f"deriva de offset del amp ({a['tc']*1e6:.0f} uV/C, {DELTA_T:.0f} C)",
         cents(a["tc"] * DELTA_T * g)),
        ("masa del bus board (ground_budget.py)", masa_del_bus()),
    ]
    return estaticos, dinamicos


def masa_del_bus() -> float:
    """El termino que viene de la otra placa, calculado por su propio script.

    Se importa en vez de copiar el numero: si alguien cambia el bus board, este
    presupuesto se entera. Un 1.21 escrito a mano aqui envejeceria en silencio.
    """
    gb = ground_budget
    corr = [gb.I_MASA_EURO, gb.I_MASA_SAM17, gb.I_MASA_SAM17,
            gb.I_MASA_SAM17, gb.I_MASA_SAM17, gb.I_MASA_EURO]
    v = gb.perfil_plano(corr)[1:5]
    d_plano = max(v) - min(v)
    d_cable = gb.I_MASA_SAM17 * gb.r_cable(150, "24AWG", 2)
    return gb.cents(d_plano) + gb.cents(d_cable)


def margen_de_swing(opamp: str) -> float:
    """Cuanto sobra entre el CV mas alto y lo que el amp puede dar."""
    return (V_RIEL - OPAMPS[opamp]["margen_riel"]) - V_MAX


def demo() -> None:
    g = ganancia_amp()
    print(f"CV {V_MIN:.0f}..{V_MAX:.0f} V = {SPAN:.0f} octavas = "
          f"{SPAN*1200:.0f} cents")
    print(f"DAC {BITS} bits, gain x{GAIN_DAC} -> 0..{VREF*GAIN_DAC:.1f} V, "
          f"amp x{g:.2f}")
    print(f"resolucion: 1 LSB = {resolucion_cents():.3f} cents\n")

    for nombre in OPAMPS:
        est, din = presupuesto(nombre)
        t_est = sum(c for _, c in est)
        t_din = sum(c for _, c in din)
        m = margen_de_swing(nombre)
        print(f"--- {nombre} ---")
        print(f"  margen de swing sobre {V_MAX:.0f} V: {m:+.2f} V "
              f"{'OK' if m > 0 else '<<< NO LLEGA'}")
        for k, c in est:
            print(f"  estatico  {k:.<52s} {c:7.2f}")
        print(f"  {'(se calibra: no cuenta)':.<62s} {t_est:7.2f}")
        for k, c in din:
            print(f"  DINAMICO  {k:.<52s} {c:7.2f}")
        print(f"  {'PRESUPUESTO REAL':.<62s} {t_din:7.2f} cents\n")

    # --- las comprobaciones que deciden ---------------------------------
    est_h, din_h = presupuesto("TL074H")
    est_c, din_c = presupuesto("TL074C (clasico)")
    total_h, total_c = sum(c for _, c in din_h), sum(c for _, c in din_c)

    assert total_h <= OBJETIVO_CENTS, f"ni con el TL074H se llega: {total_h:.2f}"
    print(f"OK: con TL074H el presupuesto dinamico son {total_h:.2f} cents "
          f"(objetivo <= {OBJETIVO_CENTS})")

    # El TL074 clasico contra los DOS rangos. Este bloque estuvo mal escrito
    # una vez: afirmaba que el clasico "no llega" DESPUES de haber bajado el
    # rango a 7 V, donde si llega con 2 V de sobra. Solo no llega a los 10 V
    # de la tesis. La asercion comprueba ahora lo que de verdad ocurre.
    v_tesis = 10.0
    margen_tesis = (V_RIEL - OPAMPS["TL074C (clasico)"]["margen_riel"]) - v_tesis
    assert margen_tesis < 0, \
        "el TL074 clasico deberia quedarse corto a 10 V; revisa el datasheet"
    print(f"OK: a los {v_tesis:.0f} V de la tesis el TL074 clasico se queda a "
          f"{-margen_tesis:.2f} V — no llega, y por eso el rango baja a "
          f"{V_MAX:.0f} V")
    assert margen_de_swing("TL074C (clasico)") > 0, \
        "a 7 V el clasico si deberia llegar"
    print(f"    A {V_MAX:.0f} V el clasico SI llega "
          f"({margen_de_swing('TL074C (clasico)'):+.2f} V), asi que el motivo "
          f"de preferir el H ya no es el swing:")
    print(f"    es la DERIVA, {din_c[1][1]/din_h[1][1]:.0f}x peor "
          f"({din_c[1][1]:.2f} contra {din_h[1][1]:.2f} cents), que es "
          f"justo lo que la tabla de afinacion no puede absorber")
    print(f"    (totales: clasico {total_c:.2f}, H {total_h:.2f} cents)")

    # el termino que sigue mandando es la masa, no el silicio
    masa = masa_del_bus()
    resto = total_h - masa
    print(f"\nreparto del presupuesto real: masa {masa:.2f} cents, "
          f"electronica {resto:.2f} cents")
    assert masa > resto, \
        ("si la electronica pasara a la masa habria que reabrir el bus board; "
         "hoy manda la masa y por eso se hizo primero")
    print("OK: sigue mandando la masa. El bus board era la prioridad correcta.")

    # y el caso feo de la referencia
    peor_ref = cents(SPAN * REF_TC_MAX * DELTA_T)
    print(f"\nsi la referencia fuese la de {REF_TC_MAX*1e6:.0f} ppm/C en vez "
          f"de {REF_TC_TIP*1e6:.0f}: {peor_ref:.2f} cents solo ese termino, "
          f"y el total subiria a {total_h - din_h[0][1] + peor_ref:.2f}")
    print("Hay que confirmar el tempco del grado EXACTO que se compre (sec.12).")


if __name__ == "__main__":
    demo()
