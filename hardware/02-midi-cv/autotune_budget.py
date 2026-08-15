"""Viabilidad del autoafinado: cuanto se puede medir y en cuanto tiempo.

    python autotune_budget.py

La idea: el modulo MIDI/CV OYE a los VCO, mide su frecuencia real y corrige la
tabla de afinacion solo. En vez de calibrar 84 notas a mano con un afinador, el
instrumento se afina el mismo cuando se lo pides.

POR QUE ESTO NO ES UNA COMODIDAD, es el arreglo del defecto mas grande

  Y con polifonia deja de ser opcional. Un oscilador desafinado en un sinte
  mono suena raro; **cuatro osciladores que no afinan ENTRE SI suenan mal de una
  forma que no se puede ignorar**, porque los batidos delatan errores que en
  monofonico ni notas.

  El convertidor exponencial de un VCO arrastra **-0.33 %/C** por el termino
  kT/q. El CEM3340 lleva compensador en el chip, pero hay que AJUSTARLO, y lo
  que quede sin ajustar deriva con la temperatura de la caja.

  Y la tesis midio **-18.62 % en el VCO3**, que son unos 350 cents — casi un
  tercio de octava. Eso no fue deriva termica, fue calibracion mala. Las dos
  cosas, la deriva y la calibracion mala, desaparecen si el aparato se mide a si
  mismo.

  Dicho de otra forma: ../tuning_budget.py separa los errores en los que la
  tabla de afinacion absorbe y los que no. **El autoafinado mueve casi todos al
  lado de los absorbidos**, porque recalibrar deja de costar una tarde. Lo unico
  que sigue sin absorberse es el error de MASA, que depende de lo que esten
  consumiendo los otros modulos en ese instante y cambia despues de calibrar.

  O sea: el suelo del instrumento pasa a ser el bus board. Que es justo lo que
  se arreglo primero.

COMO SE MIDE

  Conteo reciproco: se cronometra el tiempo T que tardan N periodos y se saca
  f = N/T. Es lo contrario de contar cuantos ciclos entran en un segundo, y es
  MUCHO mejor a frecuencias bajas — que es justo donde estan las notas graves.

  La onda del VCO se recorta con un disparador Schmitt a 3.3 V y el Pi
  cronometra los flancos. La precision no la pone el contador sino el JITTER del
  sellado de tiempo, y sale despreciable en cuanto se miden unos milisegundos.
"""
from __future__ import annotations

# --- que precision hace falta -------------------------------------------
OBJETIVO_CENTS = 0.5        # de la MEDIDA. El presupuesto total es otro: hay
                            # que dejarle sitio a la masa (1.21 cents).

# --- el sistema de medida ------------------------------------------------
JITTER = 5e-6               # s. Sellado de tiempo del Pi con pigpio, que
                            # muestrea por DMA. 1 us de resolucion y unos pocos
                            # de jitter. ES EL PARAMETRO MAS FLOJO: hay que
                            # medirlo antes de fiarse (ver seccion final).
ASENTAMIENTO = 20e-3        # s de espera tras cambiar el CV, antes de medir

# --- el instrumento -------------------------------------------------------
F_MIN, F_MAX = 32.70, 4186.0    # C1 a C8, las 84 notas de la tesis
N_NOTAS, N_VOCES = 84, 4        # SAM17 pasa a polifonico de 4 voces


def cents(rel: float) -> float:
    """De un error relativo de frecuencia a cents."""
    import math
    return 1200.0 * math.log2(1.0 + rel)


def rel_de_cents(c: float) -> float:
    return 2.0 ** (c / 1200.0) - 1.0


def tiempo_medida(f: float, objetivo: float = OBJETIVO_CENTS) -> float:
    """Cuanto hay que cronometrar esa nota para bajar del objetivo.

    Dos limites a la vez y manda el mayor:
      * el jitter: error relativo ~ JITTER / T, luego T > JITTER / rel
      * la fisica: no se puede medir menos de un periodo, y con dos flancos
        se mide uno. Se piden DOS periodos para tener margen.
    """
    return max(JITTER / rel_de_cents(objetivo), 2.0 / f)


def precision(f: float, T: float) -> float:
    """Cents de error de la medida al cronometrar T segundos."""
    return cents(JITTER / T)


def demo() -> None:
    print(f"objetivo de la MEDIDA: {OBJETIVO_CENTS} cents "
          f"= {rel_de_cents(OBJETIVO_CENTS)*1e6:.0f} ppm de frecuencia\n")

    print("nota      f (Hz)   t medida   precision   flancos que ve el Pi")
    total = 0.0
    for nombre, f in (("C1 (grave)", F_MIN), ("C4", 261.63),
                      ("C8 (aguda)", F_MAX)):
        T = tiempo_medida(f)
        print(f"{nombre:11s} {f:7.1f}   {T*1e3:6.1f} ms   "
              f"{precision(f, T):5.2f} c    {f*T:6.0f}")

    # barrido real sobre las 84 notas, en progresion temperada
    razon = (F_MAX / F_MIN) ** (1.0 / (N_NOTAS - 1))
    peor = 0.0
    for i in range(N_NOTAS):
        f = F_MIN * razon ** i
        T = tiempo_medida(f)
        peor = max(peor, precision(f, T))
        total += T + ASENTAMIENTO
    total *= N_VOCES

    print(f"\npeor precision de las {N_NOTAS} notas: {peor:.3f} cents")
    assert peor <= OBJETIVO_CENTS + 1e-9, "la medida no llega al objetivo"

    print(f"barrido completo {N_NOTAS} notas x {N_VOCES} voces: "
          f"**{total:.1f} s**")
    assert total < 60, "un barrido de mas de un minuto nadie lo usa"

    # --- que gana el instrumento -----------------------------------------
    # Sin autoafinado, lo que la tabla NO absorbe es la deriva (termica) mas la
    # masa. Con autoafinado, la deriva pasa a absorberse y entra la medida.
    masa = 1.21           # ../../bus-board/ground_budget.py
    deriva_m2 = 0.47      # ../tuning_budget.py, lo que no es masa
    print(f"\nsin autoafinado: masa {masa} + deriva del modulo 2 {deriva_m2} "
          f"= {masa + deriva_m2:.2f} cents")
    print(f"                 ...MAS lo que derive el VCO, que no esta acotado")
    print(f"con autoafinado: masa {masa} + medida {peor:.2f} "
          f"= {masa + peor:.2f} cents, y la deriva del VCO deja de contar")
    assert masa > peor, \
        ("si la medida fuese peor que la masa, el autoafinado seria el nuevo "
         "cuello de botella y habria que mejorar el sellado de tiempos")
    print("OK: la masa sigue siendo el suelo. El bus board era la prioridad.")

    # --- cuanto aguanta el Pi --------------------------------------------
    print(f"\ncarga para el Pi en la nota mas aguda: "
          f"{F_MAX:.0f} flancos/s durante {tiempo_medida(F_MAX)*1e3:.0f} ms "
          f"= {F_MAX*tiempo_medida(F_MAX):.0f} eventos")
    print("Es asumible sin divisor por hardware. Si en la placa real el jitter")
    print("sube, un 74HC4040 dividiendo por 16 lo baja a 262 flancos/s.")

    # --- lo que este calculo NO cubre ------------------------------------
    print("\nlo que NO esta confirmado:")
    print(f"  * el jitter de {JITTER*1e6:.0f} us es de manual, no medido en")
    print("    ESTA placa. Todo lo de arriba es proporcional a el.")
    print("  * el asentamiento de 20 ms tras cambiar el CV es una estimacion.")
    print("  * no cubre el error de UMBRAL del disparador Schmitt: desplaza la")
    print("    fase, no la frecuencia, asi que se cancela al medir periodos —")
    print("    pero conviene comprobarlo con una onda asimetrica de verdad.")


if __name__ == "__main__":
    demo()
