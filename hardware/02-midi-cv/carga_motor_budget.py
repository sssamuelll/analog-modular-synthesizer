#!/usr/bin/env python3
"""El libro bilateral del N657: cuanto pide el motor y cuanto lo heredado.

    python carga_motor_budget.py

R-M2 del spec del motor (S3, S7): el presupuesto de computo es EJECUTABLE y
tiene DOS mitades. La v1 del papel aseveraba solo la del motor y la junta lo
llamo coartada; aqui viven las dos, y la mitad heredada -- la que carga todas
las garantias de S2 -- es la que NO cede jamas.

Este guion nace por el acta de Samuel del 2026-08-26 (tarde): granular y
sampler entran a v1 "sin cifra hasta que su fila corra en carga_motor"
(spec S3). Aqui corre. Y por el acta de la noche suma los dos clientes
nuevos: el pegamento de la pantalla y el de los gestos.

DE DONDE SALE CADA NUMERO

  Publicados por el spec (S3 y S7), como ESTIMADO suyo -- se copian, no se
  inventan, y el bring-up los reemplaza por medidos (riesgo 2):
    FM 6 operadores (16 voces)     1 200-2 800 ciclos/muestra
    Wavetable con unisono          2 000-4 600  (hasta 256 osciladores)
    Espectral (FFT/iFFT amortiz.)    ~400       (las 16 voces)
    la mitad heredada entera       1 600-2 150  (tabla de S7, seis filas)

  DERIVADOS aqui, con su regla escrita:
    granular y sampler no tienen cifra en el papel A PROPOSITO. El spec dice
    que un grano es "lecturas interpoladas con ventana, LA MISMA CLASE DE
    TRABAJO POR MUESTRA QUE EL WAVETABLE" (S3). Esa frase es el ancla: del
    rango publicado del wavetable se saca el costo por oscilador
    (2 000-4 600 / 256 = 7.8-18.0 ciclos) y de ahi el del grano y el de la
    voz de sampler, cada uno con su factor DECLARADO abajo. Es derivacion
    de un numero publicado, no un numero nuevo -- pero sigue siendo
    ESTIMADO, y lo dice cada vez que lo imprime.

LO QUE ESTE GUION DECIDE Y LO QUE NO

  Decide: si las dos mitades caben, y CUANTOS GRANOS compra lo que sobra en
  cada escenario de voces. No decide "el numero de granos del instrumento":
  eso es una eleccion de preset, y depende de que motor corran las 16 voces.
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(errors="replace")

# --- el reloj y la muestra --------------------------------------------------
F_CPU = 800e6                 # Hz. Cortex-M55 del N657 (spec S1, DS p1)
F_MUESTRA = 48000.0           # Hz. La tasa rapida (ley de dos tasas, acta A-4)
CICLOS_POR_MUESTRA = F_CPU / F_MUESTRA

# El reparto del acta A-3: mitad y mitad. El motor es TECHO CON VALVULA (lo
# que no quepa lo toca el computo invitado, S6); la heredada es piso duro.
FRACCION_MOTOR = 0.50
FRACCION_HEREDADA = 0.50

# --- lo que el spec publica (S3): motores, ciclos/muestra por las 16 voces --
# (nombre, minimo, maximo, unidades del rango)
MOTORES_PUBLICADOS = {
    "FM 6 operadores (clase DX7)": (1200.0, 2800.0),
    "Wavetable con unisono (clase Serum)": (2000.0, 4600.0),
    "Espectral (FFT/iFFT amortizada)": (400.0, 400.0),
}
WT_OSCILADORES = 256          # "hasta 256 osciladores" (spec S3)

# --- los dos clientes nuevos (actas de la noche del 2026-08-26) -------------
# NINGUNO de los dos es el trabajo pesado de su subsistema: la pantalla la
# refresca el LTDC por DMA y los gestos los infiere la NPU -- ni un ciclo de
# CPU en ninguno de los dos casos. Lo que SI cuesta ciclos es el pegamento:
# componer la UI y convertir landmarks en senal de modulacion. Ambos son
# trabajo de tasa LENTA amortizado a la muestra rapida, y ambos son ESTIMADO
# sin fuente publicada -- por eso entran con rango ancho y con la nota.
UI_HZ = 60.0                  # cuadros/s de la pantalla (spec pantalla S5)
UI_CICLOS_POR_CUADRO = (20e3, 120e3)   # ESTIMADO: componer capas y listas
GESTOS_HZ = 60.0              # landmarks/s (spec camara S2)
GESTOS_CICLOS_POR_CUADRO = (5e3, 40e3)  # ESTIMADO: suavizado y mapeo


def _amort(ciclos: tuple, hz: float) -> tuple[float, float]:
    f = hz / F_MUESTRA
    return (ciclos[0] * f, ciclos[1] * f)


# --- la mitad heredada, tabla de S7 -- MAS las dos filas del acta ----------
# La junta de esta tanda cazo el disfraz: la primera version llamaba
# "pegamento" a la pantalla y a los gestos y los aseveraba contra un umbral
# de 200 ciclos SIN FUENTE, mientras su propio comentario declaraba la regla
# de verdad ("menor que la fila mas barata del libro"). Con el numero en la
# mano, el pegamento de la pantalla (hasta 150) TRIPLICA la fila entera del
# oyente J2 (20-50) e iguala la de los 16 ADSR. O sea: no es pegamento, es
# una fila. Aqui esta, con su ESTIMADO declarado y sin umbral inventado --
# lo que la vigila es la misma asercion dura que a todas: la mitad heredada
# con error de 3x.
HEREDADA = (
    ("16+ ADSR de canal (a 10 kHz, lazo automatico)", 150.0, 150.0),
    ("Escritor de CV: 64 valores + empaquetado + DMA", 500.0, 800.0),
    ("FFT de oidos amortizada", 190.0, 190.0),
    ("Mezcla digital + fade R-M1 + ISR/scheduler", 650.0, 650.0),
    ("USB invitado (UAC2 asincrono, feedback)", 100.0, 300.0),
    ("Oyente J2 amortizado", 20.0, 50.0),
    ("UI de la pantalla, amortizada (ESTIMADO, acta noche)",
     _amort(UI_CICLOS_POR_CUADRO, UI_HZ)[0],
     _amort(UI_CICLOS_POR_CUADRO, UI_HZ)[1]),
    ("Mapeo de gestos, amortizado (ESTIMADO, acta noche)",
     _amort(GESTOS_CICLOS_POR_CUADRO, GESTOS_HZ)[0],
     _amort(GESTOS_CICLOS_POR_CUADRO, GESTOS_HZ)[1]),
)
# Las seis primeras son las que el spec S7 publica; las dos ultimas nacen
# con las actas de la noche y NO estan en el papel todavia -- por eso se
# cuentan aparte para poder cotejar la tabla publicada sin que las nuevas
# la ensucien.
FILAS_PUBLICADAS_S7 = 6

# --- las derivaciones del acta (granular y sampler) -------------------------
# Ancla: el costo por oscilador de wavetable, del rango publicado.
WT_MIN, WT_MAX = MOTORES_PUBLICADOS["Wavetable con unisono (clase Serum)"]
CICLOS_POR_OSC_WT = (WT_MIN / WT_OSCILADORES, WT_MAX / WT_OSCILADORES)

# Un GRANO = la lectura interpolada de un oscilador de wavetable + la ventana
# (multiplicacion por la envolvente del grano y su avance). El factor de la
# ventana es ESTIMADO DECLARADO: no hay fuente, y por eso es rango.
FACTOR_VENTANA = (1.2, 1.6)
# Una VOZ DE SAMPLER = la misma lectura interpolada, sin la maquinaria de
# fase/morph del wavetable ni ventana por grano. Mas barata, mismo orden.
FACTOR_SAMPLER = (0.8, 1.2)

# El factor de error con el que el spec estresa el libro ("con error de 3x en
# todo: ~58-77 % -- cabe", S7). Es la prueba dura de este guion.
FACTOR_ERROR = 3.0


def presupuesto_motor() -> float:
    return CICLOS_POR_MUESTRA * FRACCION_MOTOR


def presupuesto_heredada() -> float:
    return CICLOS_POR_MUESTRA * FRACCION_HEREDADA


def suma(filas) -> tuple[float, float]:
    """(minimo, maximo) de una lista de (nombre, min, max)."""
    return (sum(f[1] for f in filas), sum(f[2] for f in filas))


def amortizado(ciclos_por_evento: tuple, hz: float) -> tuple[float, float]:
    """Trabajo de tasa lenta, repartido entre las muestras rapidas."""
    por_muestra = hz / F_MUESTRA
    return (ciclos_por_evento[0] * por_muestra,
            ciclos_por_evento[1] * por_muestra)


def ciclos_por_grano() -> tuple[float, float]:
    return (CICLOS_POR_OSC_WT[0] * FACTOR_VENTANA[0],
            CICLOS_POR_OSC_WT[1] * FACTOR_VENTANA[1])


def ciclos_por_voz_sampler() -> tuple[float, float]:
    return (CICLOS_POR_OSC_WT[0] * FACTOR_SAMPLER[0],
            CICLOS_POR_OSC_WT[1] * FACTOR_SAMPLER[1])


def granos_que_caben(sobra_ciclos: float, peor_caso: bool = True) -> int:
    """Cuantos granos simultaneos compra lo que sobra del presupuesto."""
    coste = ciclos_por_grano()[1 if peor_caso else 0]
    return max(0, int(sobra_ciclos // coste))


def demo() -> None:
    pm, ph = presupuesto_motor(), presupuesto_heredada()
    print("\nEL LIBRO BILATERAL DEL MOTOR (R-M2)\n")
    print(f"  reloj {F_CPU/1e6:.0f} MHz / muestra {F_MUESTRA/1e3:.0f} kHz"
          f" = {CICLOS_POR_MUESTRA:.0f} ciclos por muestra")
    print(f"  reparto del acta A-3: motor {pm:.0f} (techo con valvula) | "
          f"heredada {ph:.0f} (no cede jamas)")

    print("\n  MITAD HEREDADA (seis filas del spec S7 + dos de las actas):")
    for i, (nombre, lo, hi) in enumerate(HEREDADA):
        r = f"{lo:.0f}" if lo == hi else f"{lo:.0f}-{hi:.0f}"
        marca = " " if i < FILAS_PUBLICADAS_S7 else "*"
        print(f"  {marca} {nombre:52s} {r:>12s}")
    print("    (* fila nueva: nace con las actas de la noche y todavia no")
    print("     esta en el papel -- S7 se enmienda con estos numeros)")
    h_lo, h_hi = suma(HEREDADA)
    p_lo, p_hi = suma(HEREDADA[:FILAS_PUBLICADAS_S7])
    print(f"    {'  las seis publicadas':52s} {p_lo:>6.0f}-{p_hi:.0f}"
          f"  (el spec S7 dice 1600-2150)")
    print(f"    {'  CENTRAL con las dos nuevas':52s} {h_lo:>6.0f}-{h_hi:.0f}"
          f"  = {100*h_lo/ph:.0f}-{100*h_hi/ph:.0f} % de su mitad")
    print(f"    con error de {FACTOR_ERROR:.0f}x en todo: "
          f"{100*h_lo*FACTOR_ERROR/ph:.0f}-"
          f"{100*h_hi*FACTOR_ERROR/ph:.0f} % -- "
          f"{'cabe' if h_hi*FACTOR_ERROR <= ph else 'NO CABE'}")

    print("\n  MITAD DEL MOTOR -- los publicados (spec S3, 16 voces):")
    for nombre, (lo, hi) in MOTORES_PUBLICADOS.items():
        r = f"{lo:.0f}" if lo == hi else f"{lo:.0f}-{hi:.0f}"
        print(f"    {nombre:52s} {r:>12s}  "
              f"({100*hi/pm:.0f} % de su mitad en el peor caso)")

    print("\n  LOS DOS DEL ACTA, derivados del ancla del wavetable:")
    print(f"    ancla: {WT_MIN:.0f}-{WT_MAX:.0f} ciclos / {WT_OSCILADORES} "
          f"osciladores = {CICLOS_POR_OSC_WT[0]:.1f}-"
          f"{CICLOS_POR_OSC_WT[1]:.1f} ciclos por lectura interpolada")
    g = ciclos_por_grano()
    s = ciclos_por_voz_sampler()
    print(f"    un GRANO (lectura + ventana, x{FACTOR_VENTANA[0]}-"
          f"{FACTOR_VENTANA[1]}): {g[0]:.1f}-{g[1]:.1f} ciclos  ESTIMADO")
    print(f"    una VOZ DE SAMPLER (lectura sola, x{FACTOR_SAMPLER[0]}-"
          f"{FACTOR_SAMPLER[1]}): {s[0]:.1f}-{s[1]:.1f} ciclos  ESTIMADO")

    print("\n  LA PREGUNTA QUE EL ACTA HACE: cuantos granos caben.")
    print("  (peor caso de todo: el motor base en su maximo y el grano en el")
    print("   suyo. El presupuesto del motor es techo CON valvula: pasarse")
    print("   no rompe el instrumento, lo cede al invitado -- S6.)")
    print("  OJO, y esto NO es letra chica: lo de abajo es un TECHO DE CPU")
    print("  PELADA. No cuenta el costo de MEMORIA de cada grano -- el ancla")
    print("  sale del wavetable, que lee de tabla residente, y un grano que")
    print("  lee de PSRAM paga bus ademas de ciclos. El techo real es el mas")
    print("  apretado de los dos: ver psram_budget.py.\n")
    escenarios = [
        ("16 voces de sampler, el resto a granos",
         16 * s[1]),
        ("16 voces FM y granos encima", MOTORES_PUBLICADOS[
            "FM 6 operadores (clase DX7)"][1]),
        ("16 voces wavetable y granos encima", WT_MAX),
        ("espectral (barato) y granos encima", 400.0),
    ]
    for nombre, gastado in escenarios:
        sobra = pm - gastado
        n = granos_que_caben(sobra)
        opt = granos_que_caben(pm - gastado, peor_caso=False)
        print(f"    {nombre:44s} gasta {gastado:>6.0f} -> "
              f"sobra {sobra:>6.0f} = {n:>4d} granos "
              f"(hasta {opt} si el grano sale barato)")

    print("\n  Y si el instrumento quisiera SOLO granos (sin otro motor):")
    print(f"    {granos_que_caben(pm):d} granos en el peor caso, "
          f"{granos_que_caben(pm, peor_caso=False):d} en el mejor.")
    print("    Son granos SIMULTANEOS sonando, no granos por segundo.")


def _autocomprobacion() -> None:
    """Contra las cifras publicadas, no contra el codigo de arriba."""
    # 1. El reparto del acta A-3 contra el numero que el spec publica:
    #    "50 % del nucleo = ~8 300 ciclos por muestra" (S3).
    assert abs(presupuesto_motor() - 8333.0) < 50, presupuesto_motor()
    assert presupuesto_motor() + presupuesto_heredada() == CICLOS_POR_MUESTRA
    # 2. Las SEIS filas publicadas por S7 tienen que sumar lo que S7 dice
    #    ("~1 600-2 150 = 20-26 %"). Se cotejan solas, sin las dos nuevas:
    #    si alguien edita una fila publicada, salta contra el papel.
    p_lo, p_hi = suma(HEREDADA[:FILAS_PUBLICADAS_S7])
    assert 1590 <= p_lo <= 1620, p_lo
    assert 2130 <= p_hi <= 2150, p_hi
    assert 19 <= 100 * p_lo / presupuesto_heredada() <= 21
    assert 25 <= 100 * p_hi / presupuesto_heredada() <= 27
    # 3. El ancla del wavetable es una DIVISION de cifras publicadas: si el
    #    spec cambia el rango o el numero de osciladores, esto se mueve solo.
    assert 7.0 < CICLOS_POR_OSC_WT[0] < 9.0, CICLOS_POR_OSC_WT
    assert 17.0 < CICLOS_POR_OSC_WT[1] < 19.0, CICLOS_POR_OSC_WT
    # 4. Un grano cuesta mas que una lectura pelada y una voz de sampler
    #    menos: los factores declarados no pueden invertirse sin avisar.
    assert ciclos_por_grano()[0] > CICLOS_POR_OSC_WT[0]
    assert ciclos_por_voz_sampler()[1] < ciclos_por_grano()[1]
    # 5. Las dos filas nuevas son de tasa LENTA: su costo amortizado tiene
    #    que ser una fraccion chica de su trabajo por cuadro. Si alguna
    #    dejara de serlo, no es una fila del libro: es un lazo mas y
    #    necesita su sitio en la arquitectura de tiempo real (S7).
    for ciclos, hz in ((UI_CICLOS_POR_CUADRO, UI_HZ),
                       (GESTOS_CICLOS_POR_CUADRO, GESTOS_HZ)):
        assert hz < F_MUESTRA / 100, (
            f"un cliente a {hz} Hz ya no es de tasa lenta contra "
            f"{F_MUESTRA} Hz: se le busca sitio en S7, no una fila")
        assert _amort(ciclos, hz)[1] < presupuesto_heredada() * 0.05, (
            f"una fila amortizada pide {_amort(ciclos, hz)[1]:.0f} ciclos, "
            f"mas del 5 % de la mitad heredada: deja de ser trabajo de "
            f"borde y hay que darle dueno y lazo propios")


def main() -> int:
    _autocomprobacion()
    demo()

    pm, ph = presupuesto_motor(), presupuesto_heredada()
    h_lo, h_hi = suma(HEREDADA)

    # LA ASERCION DURA: la mitad heredada NO CEDE JAMAS (regla de cesion,
    # S7), y el spec la estresa con error de 3x. Si esta falla, el
    # instrumento no cumple sus garantias -- y no hay valvula que lo salve.
    assert h_hi * FACTOR_ERROR <= ph, (
        f"la mitad heredada pide {h_hi:.0f} ciclos y con el error de "
        f"{FACTOR_ERROR:.0f}x del spec se sale de sus {ph:.0f}: releer la "
        f"regla de cesion (S7) -- esta mitad no tiene valvula")

    # EL MOTOR es techo CON valvula, asi que no se asevera que todo quepa.
    # Lo que si se vigila -- y esta version SI puede fallar (la junta tumbo
    # la anterior por inalcanzable, Principio VIII: los pines de la
    # autocomprobacion la hacian cierta por algebra): CADA motor publicado
    # cabe hoy en su mitad. El peor es el wavetable al 55 %. El dia que un
    # numero MEDIDO del bring-up pase del 100 %, esto grita y la valvula
    # del invitado deja de ser opcion para ese motor: es requisito.
    for nombre, (_lo, hi) in MOTORES_PUBLICADOS.items():
        assert hi <= pm, (
            f"{nombre} pide {hi:.0f} ciclos y su mitad da {pm:.0f}: ese "
            f"motor ya no cabe sin el invitado -- releer S3 y S6 antes de "
            f"prometerlo en un preset")

    # Y la fila que el acta de la tarde mando: granular y sampler TIENEN
    # numero. Que exista y sea sano se vigila aqui.
    assert granos_que_caben(pm) >= 16, (
        f"el presupuesto del motor entero solo compra "
        f"{granos_que_caben(pm)} granos: por debajo de una voz por canal, "
        f"granular no es motor de v1 -- releer el acta 2026-08-26")

    print("\nOK: presupuesto cerrado.")
    return 0


# ---------------------------------------------------------------------------
# LO QUE ESTE CALCULO **NO** CUBRE
#
#   * NADA DE ESTO ESTA MEDIDO. Todas las filas son ESTIMADO -- las del spec
#     porque el spec las declara asi, y las derivadas porque su ancla lo es.
#     El bring-up las reemplaza por ciclos medidos desde TCM con DMA de fondo
#     (riesgo 2, orden del bring-up paso 3) y estas aserciones siguen
#     mandando con los numeros nuevos.
#
#   * EL ANCHO DE MEMORIA, que es el cuello REAL y no los ciclos. Un grano no
#     solo cuesta ciclos: cuesta una lectura aleatoria a SRAM o PSRAM, y mil
#     granos leyendo a la vez es un problema de bus, no de CPU. Eso vive en
#     psram_budget.py y en la fila 5 de riesgos (soak con LTDC refrescando).
#
#   * LA LATENCIA DE INTERRUPCION bajo carga plena. El spec la manda al libro
#     (S7, arquitectura de tiempo real) y el bring-up la mide; un presupuesto
#     de ciclos promedio no dice nada del peor caso de un ISR.
#
#   * QUE MOTOR CORRE CADA VOZ. Es eleccion de preset. Este guion imprime
#     escenarios, no elige.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())
