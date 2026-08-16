"""El DAC vive en la placa del VCO: que le hace eso al suelo de afinacion.

    python dac_local_budget.py

Tercer hermano de ground_budget.py y tuning_budget.py, y como ellos importa en
vez de copiar numeros: si el bus board o la cadena CV cambian, este se entera.

La decision que cuantifica (docs/architecture-poly.md par.8): los DAC no viven
en el cerebro mandando voltajes por cables — viven en el modulo que los
consume, y por el bus viaja un enlace serie. El CV de tono nace y muere en la
MISMA placa que el VCO.

Lo que cambia y lo que no:

  * El termino de MASA del pitch deja de ser el bus (plano + cable de bajada)
    y pasa a ser el plano LOCAL de la placa del VCO. Es la unica cifra nueva
    de verdad: todo lo demas se muda con los muebles.
  * La electronica del CV (DAC, amplificador, red de ganancia) se muda entera
    al modulo 3 con sus derivas intactas: tuning_budget.py sigue valiendo
    termino a termino.
  * Las 4 voces salen de UN AD5686R con UNA referencia interna: la deriva de
    la VREF es COMUN a las voces — el acorde no se desafina entre si, y el
    autoafinado la reabsorbe en la siguiente pasada. Ya era asi cuando el
    chip iba en el cerebro; mudarlo no lo estropea.
  * El CV PATCHEADO entre modulos sigue viendo el bus: para el patch bay el
    presupuesto de ground_budget.py sigue vigente tal cual.

Y las dos condiciones que esto impone al modulo 3:

  * La referencia tiene que ser el grado B (AD5686RB...): 2 ppm/C tipico,
    5 maximo. El grado A es 20 ppm/C maximo y aqui se demuestra que no cabe.
    (Verificado en ad5686r_5685r_5684r.pdf de ADI, tabla de specs, pag. 4.
    Ojo ademas con el -EP: 13 ppm/C, tampoco vale — tuning_budget.py ya
    tropezo una vez con esa hoja.)
  * REGLA DE LAYOUT: el DAC va PEGADO a los VCO y el retorno del modulo no
    cruza entre ellos. La cota pesimista de abajo (todo el retorno del modulo
    atravesando el camino DAC->VCO) es el techo de lo que puede pasar si el
    layout se descuida — y aun asi cabe, que es lo que la hace regla y no
    plegaria.
"""
from __future__ import annotations

import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_AQUI, "..", "bus-board"))
sys.path.insert(0, os.path.join(_AQUI, "..", "02-midi-cv"))
import ground_budget as gb      # noqa: E402
import tuning_budget as tb      # noqa: E402
import autotune_budget as ab    # noqa: E402

# --- el camino local DAC -> VCO ------------------------------------------
# 50 mm de recorrido sobre 20 mm de vertido efectivo: generoso para un chip
# que la regla de layout manda poner PEGADO a los VCO.
LARGO_LOCAL = 50.0   # mm
ANCHO_LOCAL = 20.0   # mm

I_DESEQUILIBRIO = 0.005      # A. Lo que de verdad cruza con el layout bien
                             # hecho: el desequilibrio del VCO (ground_budget).
I_MODULO_ENTERO = gb.I_MASA_SAM17   # A. Cota: TODO el retorno del modulo
                                    # atravesando el camino DAC->VCO.


def masa_local(corriente: float) -> float:
    """Cents de error de masa del camino DAC->VCO dentro de la placa."""
    return gb.cents(corriente * gb.r_plano(LARGO_LOCAL, ANCHO_LOCAL))


def demo() -> None:
    medida = ab.OBJETIVO_CENTS
    masa_bus = tb.masa_del_bus()
    suelo_hoy = masa_bus + medida
    assert abs(suelo_hoy - 1.71) < 0.02, \
        f"el suelo de partida se movio: {suelo_hoy:.2f} != 1.71 — revisa que"
    " ground_budget o autotune_budget no hayan cambiado sin actualizar esto"

    local_bien = masa_local(I_DESEQUILIBRIO)
    local_cota = masa_local(I_MODULO_ENTERO)
    suelo_nuevo = local_cota + medida

    print("suelo de afinacion del pitch, en cents:\n")
    print(f"  DAC en el cerebro (hoy):   masa del bus {masa_bus:.2f} "
          f"+ medida {medida:.2f} = {suelo_hoy:.2f}")
    print(f"  DAC en la placa del VCO:   plano local {local_cota:.2f} "
          f"+ medida {medida:.2f} = {suelo_nuevo:.2f}")
    print(f"\n  plano local ({LARGO_LOCAL:.0f} mm / {ANCHO_LOCAL:.0f} mm):")
    print(f"    layout bien hecho ({I_DESEQUILIBRIO*1e3:.0f} mA): "
          f"{local_bien:.3f} cents")
    print(f"    cota pesimista    ({I_MODULO_ENTERO*1e3:.0f} mA): "
          f"{local_cota:.3f} cents")
    assert local_cota < 0.1, \
        "hasta la cota pesimista debe ser despreciable frente a la medida"
    assert suelo_nuevo < 0.7, f"el suelo nuevo se infla: {suelo_nuevo:.2f}"
    print(f"\n  mejora: {suelo_hoy:.2f} -> {suelo_nuevo:.2f} "
          f"({suelo_hoy/suelo_nuevo:.1f}x). Pasa a mandar la MEDIDA, "
          "no la masa.")

    # --- la referencia: comun a las 4 voces, y el grado importa ----------
    # Deriva entre pasadas del autoafinado, con la excursion termica de
    # tuning_budget. Es COMUN a las voces (una ref por chip): desplaza el
    # teclado entero, no el acorde.
    print("\nderiva COMUN de la referencia entre pasadas del autoafinado"
          f" ({tb.DELTA_T:.0f} C):")
    for grado, tc in (("grado B, 5 ppm/C max", tb.REF_TC_MAX),
                      ("grado A, 20 ppm/C max", 20e-6)):
        c = tb.cents(tb.SPAN * tc * tb.DELTA_T)
        print(f"  {grado:24s} {c:5.2f} cents "
              f"{'OK' if c <= 1.0 else '<<< NO CABE'}")
    assert tb.cents(tb.SPAN * tb.REF_TC_MAX * tb.DELTA_T) <= 1.0
    assert tb.cents(tb.SPAN * 20e-6 * tb.DELTA_T) > 2.0, \
        "el grado A deberia suspender con claridad; si no, revisa el calculo"
    print("  -> el BOM del modulo 3 exige AD5686RB. La tolerancia estatica "
          "(+-2.5 mV) la absorbe tuning.json.")

    # --- lo que NO mejora, dicho en voz alta -----------------------------
    print(f"\nel CV patcheado entre modulos sigue viendo el bus: "
          f"{masa_bus:.2f} cents. Las reglas de ground_budget.py no se tocan.")

    print("\nOK: presupuesto cerrado.")


if __name__ == "__main__":
    demo()
