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

  La onda del VCO se recorta con un disparador Schmitt **en el propio modulo del
  VCO**, y lo que llega al cerebro es un pulso logico por oscilador. No viaja
  audio analogico entre modulos: ni se ensucia el bus ni hace falta mux,
  atenuador ni fuente negativa en el cerebro. Y al ser lineas independientes,
  las cuatro voces se miden A LA VEZ. La precision no la pone el contador sino el JITTER del
  sellado de tiempo, y sale despreciable en cuanto se miden unos milisegundos.
"""
from __future__ import annotations

# --- que precision hace falta -------------------------------------------
OBJETIVO_CENTS = 0.5        # de la MEDIDA. El presupuesto total es otro: hay
                            # que dejarle sitio a la masa (1.21 cents).

# --- el sistema de medida ------------------------------------------------
#
# EL JITTER YA NO ES UN NUMERO PRESTADO. Antes aqui vivia JITTER = 5e-6, el
# sellado de tiempo del Pi con pigpio, con un comentario que decia "ES EL
# PARAMETRO MAS FLOJO". Lo era: venia de un manual ajeno, de un aparato que
# este diseno ya no usa, y todo el presupuesto colgaba de el.
#
# Con el PIO del RP2350 el sellado lo hace el hardware, y su incertidumbre no
# se estima: SE DERIVA del reloj. El PIO muestrea el pin de forma sincrona,
# asi que un flanco queda resuelto dentro de un ciclo. En conteo reciproco se
# sellan dos flancos y se resta, luego el error de la DIFERENCIA esta acotado
# por un tick.
#
# Y lo importante: el termino dominante deja de ser el micro y pasa a ser el
# disparador Schmitt (74HC14), cuyo cruce de umbral tiembla con el ruido de la
# onda del VCO. Ese SI esta sin medir. Pero en vez de suponerlo, este guion
# lo DESPEJA: calcula cuanto puede temblar como maximo sin romper el objetivo.
# Medirlo despues deja de ser una incognita abierta y pasa a ser un aprobado
# o suspenso contra un numero.
F_PIO = 150e6               # Hz. Reloj de sistema del RP2350 (dual Cortex-M33)
JITTER_TIMESTAMP = 1.0 / F_PIO   # s. Un tick: la cota del error de la resta
JITTER_PI_HISTORICO = 5e-6  # s. Lo que habia antes, para comparar de que se
                            # viene. No se usa en ningun calculo.

# El unico jitter que entra en el presupuesto de medida es el del sellado.
# El del comparador se despeja abajo y se contrasta contra su holgura.
JITTER = JITTER_TIMESTAMP

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


def jitter_comparador_max(T: float, objetivo: float = OBJETIVO_CENTS) -> float:
    """Cuanto puede temblar el 74HC14 sin romper el objetivo, en segundos.

    Se suman los dos jitter LINEALMENTE, que es el peor caso (en realidad son
    independientes y sumarian en cuadratura, asi que esto es pesimista a
    proposito). Despejando de cents((t_sellado + t_comp)/T) <= objetivo:

        t_comp <= rel(objetivo) * T - t_sellado

    Se evalua en la ventana MAS CORTA del barrido, que es la que menos
    perdona: la nota mas aguda.
    """
    return rel_de_cents(objetivo) * T - JITTER_TIMESTAMP


def demo() -> None:
    print(f"objetivo de la MEDIDA: {OBJETIVO_CENTS} cents "
          f"= {rel_de_cents(OBJETIVO_CENTS)*1e6:.0f} ppm de frecuencia\n")

    print("nota      f (Hz)   t medida   precision   flancos minimos")
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
    # Las N voces se miden EN PARALELO, no una detras de otra: se ponen las
    # cuatro en la misma nota y se cronometran los cuatro pulsos a la vez.
    # Se puede porque lo que llega del modulo 3 son senales LOGICAS
    # independientes, una por oscilador — con el multiplexor analogico que
    # habia antes habia que ir de una en una y el barrido duraba N veces mas.

    print(f"\npeor precision de las {N_NOTAS} notas: {peor:.3f} cents")
    assert peor <= OBJETIVO_CENTS + 1e-9, "la medida no llega al objetivo"

    print(f"barrido completo: {N_NOTAS} notas, las {N_VOCES} voces en "
          f"paralelo -> **{total:.1f} s**")
    print(f"   (de una en una, como exigia el multiplexor, serian "
          f"{total*N_VOCES:.1f} s)")
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

    # --- de que se viene -------------------------------------------------
    print(f"\nsellado de tiempos: {JITTER_TIMESTAMP*1e9:.2f} ns "
          f"(un tick del PIO a {F_PIO/1e6:.0f} MHz), derivado del reloj")
    print(f"   contra los {JITTER_PI_HISTORICO*1e6:.0f} us del Pi con pigpio: "
          f"**{JITTER_PI_HISTORICO/JITTER_TIMESTAMP:.0f}x mejor**")
    print("   y ya no es un numero de manual ajeno: sale del propio hardware")

    # El PIO cuenta por hardware, asi que no hay "eventos que atender": el
    # micro lee dos registros al final. La carga por flanco desaparece y con
    # ella la necesidad del divisor 74HC4040 que hacia falta con el Pi.
    print(f"\ncarga de CPU: ninguna por flanco. El PIO cronometra por")
    print(f"   hardware y el nucleo lee el resultado al final. El divisor")
    print(f"   74HC4040 que hacia falta con el Pi sobra.")

    # --- el termino que queda, DESPEJADO en vez de supuesto ---------------
    # La ventana mas corta del barrido es la que menos perdona.
    T_corta = min(tiempo_medida(F_MIN * razon ** i) for i in range(N_NOTAS))
    j_comp = jitter_comparador_max(T_corta)
    print(f"\nel termino que queda es el disparador Schmitt, y esta DESPEJADO:")
    print(f"   ventana mas corta del barrido: {T_corta*1e6:.0f} us")
    print(f"   el 74HC14 puede temblar hasta **{j_comp*1e9:.0f} ns** "
          f"y aun se cumple el objetivo")
    print(f"   eso es {j_comp/JITTER_TIMESTAMP:.0f}x el sellado, o sea que el "
          f"sellado se lleva el {100/(1+j_comp/JITTER_TIMESTAMP):.0f}% "
          f"del presupuesto")
    # El criterio no es un numero bonito: es que el sellado sea DESPRECIABLE.
    # Con 10x, el micro aporta menos del 10% del error permitido y es ruido de
    # redondeo frente al comparador. Por debajo de eso deja de ser despreciable
    # y volveria a ser un termino que hay que defender.
    assert j_comp > 10 * JITTER_TIMESTAMP, \
        ("el sellado del PIO tiene que ser despreciable (<10% del error "
         "permitido) frente al comparador. Si no lo es, el micro vuelve a ser "
         "un termino real: hay que subir F_PIO o alargar la ventana de medida")
    print("OK: medir el jitter del 74HC14 deja de ser una incognita abierta")
    print("    y pasa a ser un aprobado/suspenso contra ese numero.")

    # --- lo que este calculo NO cubre ------------------------------------
    print("\nlo que NO esta confirmado:")
    print(f"  * el jitter real del 74HC14 sigue SIN MEDIR. Lo que cambia es")
    print(f"    que ahora hay contra que medirlo: {j_comp*1e9:.0f} ns.")
    print("  * el asentamiento de 20 ms tras cambiar el CV es una estimacion.")
    print("  * no cubre el error de UMBRAL del disparador Schmitt: desplaza la")
    print("    fase, no la frecuencia, asi que se cancela al medir periodos —")
    print("    pero conviene comprobarlo con una onda asimetrica de verdad.")
    print(f"  * F_PIO = {F_PIO/1e6:.0f} MHz supone el reloj de sistema sin")
    print("    dividir para el PIO. Si el firmware lo divide, este numero")
    print("    baja en la misma proporcion y hay que recalcular.")


if __name__ == "__main__":
    demo()
