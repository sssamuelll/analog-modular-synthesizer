# ENMIENDA 2026-08-30 (D1) -- EL SUJETO DE ESTE GUION MURIO: EL CEREBRO
# YA NO ES UN RP2350.
#
#   D1 (spec del hub N657, 2026-08-30) sello el chip del cerebro como
#   STM32N657. Este guion mide maquinas de PIO, memoria de instrucciones,
#   canales de DMA y pines de un RP2350B: el N657 no tiene PIO, asi que no
#   hay a quien medir. Se cumple lo que su propia cabecera preveia
#   ("muriendo entero si el cerebro no acaba siendo un RP2350", 2026-08-26).
#
#   No se toca su codigo ni sus constantes: se conserva como historia de un
#   diseno dirigido que D1 cerro. El censo de pines del hub de hoy es el del
#   N657 (micro_budget.py, #213).
#
"""Que cabe en el cerebro: maquinas de PIO, memoria de instrucciones, canales
de DMA, pines — y el reloj que el host USB le puede robar al afinado.

    python pio_budget.py

POR QUE ESTE GUION EXISTE

  Este proyecto tiene presupuestos ejecutables para el ancho del panel, los
  umbrales de sync, la corriente por riel, el flanco del enlace, la afinacion y
  las masas. No tenia ninguno para **lo unico que de verdad va a escasear en el
  cerebro**: las doce maquinas de estado del PIO, los pines, y el reloj de
  sistema.

  Y lo que lo hace urgente no es el conteo. Es que `clk_sys` tiene dos duenos
  que no se conocen:

    * `autotune_budget.py` fija F_PIO = 150 MHz y **todo el presupuesto de
      afinacion cuelga de ahi**: el sellado de un tick del PIO son 6.67 ns, y de
      ahi salen los 131 ns que el 74HC14 tiene permitido temblar.
    * Pico-PIO-USB bit-banguea el host USB y **puede imponer el reloj de
      sistema** para cumplir el temporizado de USB.

  Dos funciones, un solo `clk_sys`, y cada spec asume que es suyo. El dia que el
  host fije otro reloj, los 131 ns se mueven **sin que nadie haya tocado el
  afinado** — el presupuesto del que mas orgulloso esta este diseno, invalidado
  por una decision tomada en otro documento. Este guion pone esa colision en un
  assert.

  Issue #150. La spec del cerebro lo declara en su sec.11 con este nombre.

  ENMIENDA 2026-08-26 -- Y PASO ALGO QUE NADIE HABIA PREVISTO: el assert salto,
  pero no porque el host cambiara el reloj. Salto porque **el afinado se fue a
  otro chip**. Los dieciseis cronometros son hoy capturas de TIM del STM32N657
  del modulo de Voz (motor-digital §7), no PIO del cerebro.

  Asi que la colision del #150 no se resolvio: **se disolvio**. Dos relojes en
  dos silicios distintos no pelean por nada. El guion sigue vivo y sigue
  midiendo el cerebro, pero esa comparacion concreta pasa a HUECO declarado —
  aseverar los 150 MHz del host contra si mismos seria un verde de mentira
  (Principio VIII). Lo que sobrevive del #150 esta escrito en el bloque del
  reloj, mas abajo, y no es poco: el requisito real de Pico-PIO-USB sigue sin
  leerse.

  Y hay una moraleja para el repo, porque el import hizo su trabajo: la spec
  del cerebro sec.11 exigio "ninguno reescribe autotune_budget.py: lo importa,
  para que los 131 ns se enteren si algo se mueve". Se movio algo MAS GRANDE
  que un numero, y el import lo caso igual.

POR QUE LOS PINES ESTAN AQUI Y NO EN SU PROPIO GUION

  Porque **la ventana de 32 GPIO ata las dos cosas a la vez**. Un programa de
  PIO no falla por pedir demasiadas maquinas: falla porque sus pines cayeron a
  los dos lados de la frontera del GPIO 32, y entonces la maquina no alcanza el
  pin. Ese fallo no se ve censando maquinas ni censando pines por separado —
  solo se ve mirando las dos cosas juntas.

  Asi que este guion cubre tres de las cuatro comprobaciones que sec.11.1 le
  pide a `check_pinout.py`: capacidad, ventana de PIO y GPIO libres. La cuarta
  —que cada pin pueda hacer lo que se le pide, contra la tabla de funciones por
  GPIO del datasheet— NO esta aqui, y queda dicha abajo en lo que NO cubre.

  **Lo que este guion NO es: no es `pines_budget.py`.** Conviene decirlo porque
  el nombre invita a confundirlos y estuvo a punto de pasar. Ese otro guion sale
  de dieciseis sec.15 y presupuesta **los dos micros del modulo de Voz** — su
  propia ficha lo delata con la cifra: *«16 de 24 maquinas de PIO»*, y 24 son
  2 x 12, o sea dos chips. Aquel reparto y este no comparten ni pines, ni reloj,
  ni inquilinos: son dos RP2350B distintos. Fundirlos habria metido el reparto
  de dos silicios en un solo censo, y el primero que lo leyera habria tenido que
  deshacerlo. Los dos guiones hacen falta y son hermanos, no duplicados.

  El del micro de Voz esta mandado en papel (enlace sin jefe sec.9, y el riesgo
  4 de dieciseis) y su censo esta **mas apretado que este**: issue #205.

LO QUE MIDE, Y CONTRA QUE

  Mide el **artefacto**, no la intencion: los pines los lee de
  `software/nucleo/core/src/pinout.rs`, no de una copia en Python. Si alguien
  anade un pin alli, este guion se entera. Esa es la leccion del #139 y la razon
  por la que sec.11.1 insiste en que una puerta que compara la propuesta consigo
  misma no es una puerta.

  Lo que no puede leer de ningun artefacto —cuantas instrucciones ocupa cada
  programa de PIO, y que reloj exige Pico-PIO-USB— se DECLARA con su fuente o
  se marca ESTIMADO, y se asevera contra el valor declarado. Asi el guion falla
  el dia que alguien lo cambie sin mirar el resto.
"""
from __future__ import annotations

import os
import re
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _AQUI)
import autotune_budget as ab  # noqa: E402

# --- lo que da el chip ----------------------------------------------------
#
# Fuente primaria: docs/reference/datasheets/rp2350-datasheet-2024-08.pdf
# (Raspberry Pi Ltd, agosto 2024). Paginas anotadas por si alguien las quiere
# contrastar sin buscarlas.
#
#   pag. 877, Figura 44: "There are three PIO blocks, each containing four
#   state machines. The four state machines simultaneously execute programs
#   from shared instruction memory. [...] GPIO mapping logic allows each state
#   machine to observe and manipulate up to 32 GPIOs."
BLOQUES_PIO = 3
SM_POR_BLOQUE = 4
SM_TOTALES = BLOQUES_PIO * SM_POR_BLOQUE      # 12
#   pag. 877 ("Instruction Memory 32 Instructions, 4 Read Ports") y pag. 881
#   ("Each PIO instance has a 32-slot instruction memory, which all 4 state
#   machines share"). OJO: es POR BLOQUE y COMPARTIDA, no por maquina.
INSTR_POR_BLOQUE = 32
#   pag. 1096, lista de diferencias contra el RP2040: "Increased the number of
#   DMA channels from 12 to 16."
CANALES_DMA = 16
#   pag. 877, Figura 44. Es la restriccion que ata pines y PIO a la vez.
VENTANA_PIO = 32

# El RP2350B, del product brief (rp2350-product-brief-2024-08.pdf): QFN-80,
# 48 GPIO y 8 entradas analogicas. El A da 30 y por eso no servia.
GPIO_TOTALES = 48

# --- lo que pide el cerebro ------------------------------------------------
#
# Un consumidor por renglon, con de donde sale la obligacion. `sm` son maquinas
# de estado; `instr` son instrucciones de memoria de PIO; `dma` son canales.
#
# LAS INSTRUCCIONES SON EL TERMINO FLOJO DE ESTA TABLA y se dicen asi a
# proposito: no salen de ningun artefacto de este repo, salen del tamano de
# programas de terceros. Estan marcadas ESTIMADO y el assert de abajo las trata
# como lo que son. Medirlas es `pioasm` sobre el programa real, y es trabajo de
# bring-up, no de aritmetica.
#
# QUE PINES TOCA CADA PROGRAMA NO ESTA AQUI. Vive en `PROGRAMAS_PIO`, dentro de
# pinout.rs, y este guion lo lee. Es un dato de pines —cual va con cual— y
# tenerlo en dos sitios garantiza que se separen: es el modo de fallo del #152
# y del #128, un dato repartido que otro importa como verdad y que envejece sin
# que nadie lo note. Aqui solo vive el COSTE de cada programa.
COSTES_PIO = {
    # nombre (tiene que coincidir con pinout.rs): (sm, instr, dma, fuente)
    #
    # ENMIENDA 2026-08-26 -- ESTA FILA SOBRECUENTA Y SE DEJA A PROPOSITO.
    #   El autoafinado se mudo al N657 del modulo de Voz (ver el bloque del
    #   reloj, mas abajo): estas 4 maquinas, 8 instrucciones y 4 canales de DMA
    #   **ya no los gasta el cerebro**. Quitarla de aqui obliga a tocar
    #   pinout.rs, que es firmware recien mergeado (#208) y cuyo nombre este
    #   guion cruza con un assert. Eso es cascada, y la cascada se propone,
    #   no se cuela en una enmienda de papel.
    #   Se deja porque sobrecontar es CONSERVADOR -- el censo se cree con menos
    #   sitio del que tiene, nunca con mas -- y porque un numero inflado con su
    #   cartel puesto es mejor que un censo que cambia sin que nadie lo revise.
    #   Al retirarla, el cerebro RECUPERA 4 de sus 12 maquinas de PIO.
    "cronometros de afinacion": (
        4, 8, 4,
        "nucleo sec.5.1 + autotune_budget.py; conteo reciproco, uno por "
        "oscilador. instr ESTIMADO. **SOBRECUENTA desde 2026-08-26: se mudo "
        "al N657 de la Voz**"),
    "host USB (Pico-PIO-USB)": (
        2, 24, 2,
        "nucleo sec.5.3; issue #77 (la pila es C). sm e instr ESTIMADO: el "
        "programa es de terceros y no se ha corrido pioasm contra el"),
    "cadena WS2812": (
        1, 4, 1,
        "pinout.rs d(21) + nucleo sec.6.2. instr ESTIMADO"),
}
# NO son PIO y por eso no estan arriba, pero conviene decirlo para que nadie
# los sume dos veces: el J2 va en el SPI0 de hardware y el I2C del mux tambien
# es periferico de hardware.

# --- el reloj, que es el motivo de este guion ------------------------------
#
# F_PIO se IMPORTA de autotune_budget.py. No se copia. Si alli sube o baja, el
# assert de abajo lo ve. La spec del cerebro sec.11 lo exige con estas palabras:
# "Ninguno reescribe autotune_budget.py: lo importa, para que los 131 ns del
# 74HC14 se enteren si algo se mueve."
F_PIO_AFINADO = ab.F_PIO
#
# ENMIENDA 2026-08-26 -- LA COLISION DEL #150 NO SE RESOLVIO: SE DISOLVIO,
# PORQUE UNO DE LOS DOS DUENOS SE MUDO DE CHIP.
#
#   El import de arriba hizo EXACTAMENTE lo que se le pidio. El dia que
#   autotune_budget.py se movio, este assert salto -- y al mirarlo de cerca,
#   lo que habia cambiado no era un numero: era el silicio.
#
#   El autoafinado YA NO CORRE EN EL CEREBRO. Los dieciseis cronometros son
#   ahora capturas de TIM del STM32N657 del modulo de Voz (motor-digital §7:
#   "16 cronometros | 14 en TIM2-5 + 2 en TIM1 ... sellado <= ~13 ns (assert
#   de autotune_budget.py)"). Los pulsos del Schmitt van al micro local, que
#   esta en la misma placa que los VCO, en vez de cruzar hasta el cerebro.
#
#   Consecuencia para ESTE guion, que es su motivo de existir: **clk_sys del
#   cerebro ya no tiene dos duenos. Tiene uno.** El afinado se fue de la casa.
#
#   Por eso el assert de abajo NO se puede mantener como estaba: comparaba dos
#   relojes que hoy viven en silicios distintos. Un N657 a 200 MHz y un RP2350
#   a 150 MHz no colisionan -- no comparten nada.
#
#   Y NO se sustituye por un assert nuevo, porque el unico que cabria seria
#   F_CLK_HOST_USB contra si mismo: una asercion que no puede fallar por
#   construccion, que es justo lo que el Principio VIII prohibe. Lo que queda
#   es un HUECO honesto, y esta escrito abajo.
#
#   LO QUE SOBREVIVE INTACTO DEL #150, y conviene no perderlo en la mudanza:
#     * punto 2 -- el reloj que Pico-PIO-USB exige DE VERDAD sigue sin leerse
#       contra su fuente. Que el afinado se fuera no lo contesta.
#     * punto 3 -- el reparto de nucleos del cerebro sigue sin decidirse.
#     * y nace uno: el censo de PIO de abajo AHORA SOBRECUENTA (ver COSTES_PIO).
COLISION_150_DISUELTA = True

# Huecos declarados en tiempo de ejecucion. Si queda alguno, el guion sale con
# codigo 2: HUECO visible, no fallo invisible (Principio V). No rompe el CI.
_HUECOS: list[str] = []

# Lo que Pico-PIO-USB exige del reloj de sistema. **SIN CONFIRMAR** — es
# exactamente el hueco que abrio el #150. Se declara igual al del afinado para
# que el presupuesto salga verde HOY y se ponga rojo el dia que alguien lo
# corrija con el numero real. Si se deja en None, el guion avisa y no asevera.
F_CLK_HOST_USB = 150e6      # Hz. SIN CONFIRMAR: no se ha leido el requisito
                            # de Pico-PIO-USB contra su fuente. #150 punto 2.

# --- los pines, leidos del artefacto ---------------------------------------
RUTA_PINOUT = os.path.join(_AQUI, "..", "..", "software", "nucleo", "core",
                           "src", "pinout.rs")

# Lo que la placa del cerebro le va a anadir a pinout.rs, que hoy no esta
# escrito alli. Cuenta vigente tras la derogacion de la cabeza local en sec.7:
#   39 hoy, +5 de sec.12.14, -3 de los digitos retirados = 41 de 48
PINES_NUEVOS_12_14 = 5      # bandera y EN del host (sec.6.2), EN y arranque del
                            # puente (sec.6.6), RESET del mux I2C (sec.8)
# RETIRADA 2026-08-27: se eliminaron del censo los cinco GPIO de la pantalla
# SPI de 2,8" porque sec.7 la deroga junto con toda la cabeza local. La pantalla
# de 7" cuelga del STM32N657 del motor y no consume GPIO de este RP2350B.
PINES_DIGITOS = 3           # DIG_DATA, DIG_CLK, DIG_LATCH: se retiraron con la
                            # cabeza local y no vuelven; pinout.rs TODAVIA los
                            # declara (#180)
# La cabeza local esta DEROGADA (spec del cerebro sec.7, 2026-08-27): la
# pantalla de 7" del motor es la unica del instrumento y cuelga de otro chip.
# Su coste en pines se deja EXPLICITO y clavado a cero, en vez de borrado, por
# la regla de mutacion de la constitucion: si alguien resucita los 5 GPIO de
# la 2,8", la asercion de abajo canta en vez de dejar el censo pasar callado.
PINES_CABEZA_LOCAL = 0

MARGEN_PINES_MIN = 2        # sec.12.16: "A partir de aqui, cualquier funcion
                            # nueva que pida mas de dos pines no entra sin
                            # quitar otra cosa"


def leer_pinout() -> list[tuple[int, str]]:
    """Los pines declarados en pinout.rs, leidos del fichero de verdad.

    Se lee el artefacto y no una copia porque una puerta que compara la
    propuesta consigo misma no es una puerta (cerebro sec.11.1).
    """
    with open(RUTA_PINOUT, encoding="utf-8") as f:
        texto = f.read()
    # d(13, "TUNE_OUT 1")  /  a(40, "pedal")
    return [(int(g), n) for g, n in
            re.findall(r'\b[da]\(\s*(\d+)\s*,\s*"([^"]*)"\s*\)', texto)]


def leer_programas_pio() -> list[tuple[str, list[str]]]:
    """`PROGRAMAS_PIO` de pinout.rs: que pines toca cada programa.

    Se lee del mismo artefacto que los pines para que no haya dos verdades.
    """
    with open(RUTA_PINOUT, encoding="utf-8") as f:
        texto = f.read()
    bloque = re.search(r"PROGRAMAS_PIO[^=]*=\s*&\[(.*?)\n\];", texto, re.S)
    if bloque is None:
        raise SystemExit(
            "no se encontro PROGRAMAS_PIO en pinout.rs. O se renombro o se "
            "borro; en cualquiera de los dos casos este presupuesto no puede "
            "saber que pines toca cada programa de PIO y no debe adivinarlo")
    return [(nombre, re.findall(r'"([^"]+)"', pines))
            for nombre, pines in
            re.findall(r'"([^"]+)"\s*,\s*&\[(.*?)\]', bloque.group(1), re.S)]


def ventana_de(gpio: int) -> int:
    """A que ventana de 32 GPIO pertenece un pin. 0 o 1 en el RP2350B."""
    return gpio // VENTANA_PIO


def ventanas_de(nombres: list[str], pines: dict[str, int]) -> set[int]:
    """Las ventanas que toca un programa de PIO, por los pines que usa."""
    return {ventana_de(pines[n]) for n in nombres if n in pines}


def demo() -> None:
    pinout = leer_pinout()
    por_nombre = {n: g for g, n in pinout}
    programas = leer_programas_pio()

    # Las dos mitades tienen que hablar del mismo conjunto de programas. Si
    # alguien anade uno a pinout.rs y no le pone coste aqui, el presupuesto
    # saldria verde ignorandolo — que es exactamente como se cuela un
    # consumidor sin contar.
    en_rust = {n for n, _ in programas}
    assert en_rust == set(COSTES_PIO), (
        f"pinout.rs declara los programas de PIO {sorted(en_rust)} y este "
        f"presupuesto tiene costes para {sorted(COSTES_PIO)}. El que sobra o "
        f"falta no se esta contando: o se le pone coste aqui, o se quita de "
        f"PROGRAMAS_PIO")

    # (nombre, sm, instr, dma, pines, fuente) — pines de pinout.rs, coste de aqui
    CONSUMIDORES_PIO = [(n, *COSTES_PIO[n][:3], p, COSTES_PIO[n][3])
                        for n, p in programas]

    print(f"RP2350B, de su datasheet: {BLOQUES_PIO} bloques de PIO x "
          f"{SM_POR_BLOQUE} maquinas = **{SM_TOTALES} maquinas de estado**,")
    print(f"   {INSTR_POR_BLOQUE} instrucciones por bloque COMPARTIDAS entre "
          f"sus {SM_POR_BLOQUE} maquinas, {CANALES_DMA} canales de DMA,")
    print(f"   {GPIO_TOTALES} GPIO, y cada maquina ve una ventana de "
          f"{VENTANA_PIO} GPIO.\n")

    # --- maquinas de estado ------------------------------------------------
    print("consumidor                    sm  instr  dma   ventana")
    sm = instr = dma = 0
    for nombre, s, i, d, pines, _fuente in CONSUMIDORES_PIO:
        v = ventanas_de(pines, por_nombre)
        vtxt = ",".join(str(x) for x in sorted(v)) if v else "-"
        print(f"  {nombre:27s} {s:2d}   {i:3d}   {d:2d}     {vtxt}")
        sm += s
        instr += i
        dma += d
    print(f"  {'TOTAL':27s} {sm:2d}   {instr:3d}   {dma:2d}")
    print(f"  {'da el chip':27s} {SM_TOTALES:2d}   "
          f"{INSTR_POR_BLOQUE * BLOQUES_PIO:3d}   {CANALES_DMA:2d}")
    print(f"  {'queda libre':27s} {SM_TOTALES - sm:2d}   "
          f"{INSTR_POR_BLOQUE * BLOQUES_PIO - instr:3d}   "
          f"{CANALES_DMA - dma:2d}\n")

    assert sm <= SM_TOTALES, (
        f"el cerebro pide {sm} maquinas de estado y el RP2350B da "
        f"{SM_TOTALES}. No hay salida por firmware: o se quita un consumidor "
        f"o alguna funcion deja de ir por PIO")
    assert dma <= CANALES_DMA, (
        f"el cerebro pide {dma} canales de DMA y el chip da {CANALES_DMA}")

    # --- la memoria de instrucciones, que es POR BLOQUE --------------------
    #
    # El total no basta: la memoria es de bloque y compartida, asi que un
    # programa de 24 instrucciones no cabe en un bloque donde ya viven 12,
    # aunque el TOTAL del chip diga que sobra sitio. Se comprueba el peor caso:
    # que el programa mas gordo quepa en un bloque el solo.
    mas_gordo = max(CONSUMIDORES_PIO, key=lambda c: c[2])
    print(f"el programa mas gordo es '{mas_gordo[0]}' con {mas_gordo[2]} "
          f"instrucciones,")
    print(f"   contra las {INSTR_POR_BLOQUE} que tiene un bloque. Ocupa el "
          f"{mas_gordo[2] / INSTR_POR_BLOQUE * 100:.0f} % de su bloque.")
    assert mas_gordo[2] <= INSTR_POR_BLOQUE, (
        f"'{mas_gordo[0]}' pide {mas_gordo[2]} instrucciones y un bloque de "
        f"PIO solo tiene {INSTR_POR_BLOQUE}. La memoria es POR BLOQUE y "
        f"compartida: que el total del chip alcance no significa nada")

    # Y el reparto por bloque tiene que existir, no solo el total. Con tres
    # bloques y tres consumidores el reparto trivial es uno cada uno; se
    # asevera que ese reparto cabe, que es la condicion suficiente.
    assert len(CONSUMIDORES_PIO) <= BLOQUES_PIO, (
        "hay mas programas de PIO que bloques, asi que alguno tiene que "
        "compartir memoria de instrucciones con otro y el reparto deja de ser "
        "trivial: hay que escribirlo a mano en este guion")
    print("   y hay un bloque por programa, asi que ninguno comparte memoria "
          "con otro.\n")

    # --- la ventana de 32 GPIO ---------------------------------------------
    #
    # Cada maquina ve 32 GPIO consecutivos. Un programa cuyos pines caigan a
    # los dos lados de la frontera NO se puede escribir: no es que vaya lento,
    # es que la maquina no alcanza el pin.
    print("la ventana de 32 GPIO, que es la restriccion que nadie tenia "
          "escrita:")
    for nombre, _s, _i, _d, pines, _f in CONSUMIDORES_PIO:
        v = ventanas_de(pines, por_nombre)
        gpios = [por_nombre[n] for n in pines if n in por_nombre]
        print(f"   {nombre:27s} GPIO {gpios} -> ventana(s) {sorted(v)}")
        assert len(v) <= 1, (
            f"'{nombre}' usa GPIO {sorted(gpios)}, que caen en ventanas "
            f"{sorted(v)} distintas. Una maquina de PIO solo ve "
            f"{VENTANA_PIO} GPIO consecutivos: este programa NO SE PUEDE "
            f"ESCRIBIR tal como estan repartidos los pines")
        assert v, (
            f"'{nombre}' no encontro ninguno de sus pines {pines} en "
            f"pinout.rs. O se renombraron alli o esta tabla envejecio")
    print()

    # --- los pines -----------------------------------------------------------
    hoy = len(pinout)
    assert PINES_CABEZA_LOCAL == 0, (
        f"PINES_CABEZA_LOCAL vale {PINES_CABEZA_LOCAL} y la cabeza local esta "
        f"derogada desde el 2026-08-27 (spec del cerebro sec.7). Si de verdad "
        f"vuelve una pantalla al cerebro, esto no se sube: se reabre la "
        f"seccion 7, porque la 7\" del motor es la unica cabeza")
    manana = hoy + PINES_NUEVOS_12_14 - PINES_DIGITOS + PINES_CABEZA_LOCAL
    libres = GPIO_TOTALES - manana
    print(f"pines: {hoy} declarados hoy en pinout.rs")
    print(f"   +{PINES_NUEVOS_12_14} de sec.12.14 (bandera y EN del host, EN y "
          f"arranque del puente, RESET del mux)")
    print(f"   -{PINES_DIGITOS} de los digitos retirados con la cabeza local (sec.7)")
    print(f"   = **{manana} de {GPIO_TOTALES}**, quedan {libres} libres\n")

    # El 39 no se escribe aqui: se cuenta del fichero. Si alguien anade un pin
    # a pinout.rs sin mirar sec.12.16, esta cuenta se mueve sola y el assert salta.
    assert libres >= MARGEN_PINES_MIN, (
        f"quedarian {libres} GPIO libres y sec.12.16 fija el suelo en "
        f"{MARGEN_PINES_MIN}. La salida sancionada NO es un segundo micro "
        f"—eso compra un problema de coherencia de modelo para resolver uno "
        f"de conteo—: es un expansor colgado del bus I2C del mux, que ya esta "
        f"puesto (sec.8)")

    # pinout.rs todavia declara los tres digitos que sec.7 dice haber devuelto.
    # No es un fallo de este guion arreglarlo, pero si es su trabajo verlo.
    digitos_vivos = [n for _g, n in pinout if "digito" in n.lower()]
    if digitos_vivos:
        print(f"AVISO (#180, hallazgo H-6): pinout.rs todavia declara "
              f"{len(digitos_vivos)} pines de digitos")
        print(f"   {digitos_vivos}")
        print("   que la spec sec.7 dice haber devuelto.")
        print("   El artefacto contradice a su spec. La cuenta de arriba usa "
              "la spec, no el fichero.\n")

    # --- la colision de clk_sys: DISUELTA, no resuelta (enmienda 2026-08-26)
    print("el reloj de sistema, y sus duenos:")
    print(f"   el host USB exige   {F_CLK_HOST_USB/1e6:>6.1f} MHz  "
          f"(SIN CONFIRMAR -- #150 punto 2, sigue abierto)")
    print(f"   el afinado suponia  {F_PIO_AFINADO/1e6:>6.1f} MHz  "
          f"**y YA NO ES DE ESTA CASA**")
    print("   el autoafinado se mudo al STM32N657 del modulo de Voz: son")
    print("   capturas de TIM en la placa de los VCO, no PIO del cerebro")
    print("   (motor-digital §7). Dos relojes en dos silicios NO colisionan.")
    print(f"   sellado del afinado alla: {1e9/F_PIO_AFINADO:.2f} ns "
          f"-- lo asevera autotune_budget.py, no este guion\n")

    print("HUECO: la colision del #150 se DISOLVIO (un dueno se mudo de chip),")
    print("       pero no se resolvio nada de lo que la hacia peligrosa:")
    print(f"       * los {F_CLK_HOST_USB/1e6:.0f} MHz del host USB siguen sin "
          f"leerse contra su fuente;")
    print("       * aseverarlos contra si mismos seria un verde de mentira "
          "(Principio VIII);")
    print("       * y el censo de PIO de arriba SOBRECUENTA: los cronometros "
          "de afinacion")
    print("         ya no viven aqui. Ver COSTES_PIO.")
    print("       Se cierra leyendo el requisito real de Pico-PIO-USB, o "
          "muriendo entero")
    print("       si el cerebro no acaba siendo un RP2350 (su chip sigue "
          "dirigido, no sellado).\n")
    _HUECOS.append("clk_sys: colision disuelta, requisito del host sin leer")

    # --- lo que este calculo NO cubre --------------------------------------
    print("lo que NO esta confirmado:")
    print(f"  * **el reloj que Pico-PIO-USB exige de verdad**. Los "
          f"{F_CLK_HOST_USB/1e6:.0f} MHz de arriba se pusieron iguales a los")
    print("    del afinado cuando el afinado vivia aqui. Ya no vive, asi que "
          "hoy no los sostiene")
    print("    ni esa coincidencia: nadie ha leido el requisito contra su "
          "fuente.")
    print("    Es el punto 2 del #150 y es lo unico que puede tumbar este "
          "presupuesto entero.")
    print("  * **las instrucciones de PIO de los tres programas son "
          "ESTIMADO**, no medidas. Se cierran")
    print("    corriendo pioasm sobre el programa real, en el bring-up (#86). "
          "El total da holgura,")
    print(f"    pero el que importa es el mas gordo contra su bloque: "
          f"{mas_gordo[2]}/{INSTR_POR_BLOQUE}.")
    print(f"  * **las maquinas que pide Pico-PIO-USB** (aqui {COSTES_PIO["host USB (Pico-PIO-USB)"][0]}) "
          f"salen de leer el proyecto, no de")
    print(f"    correrlo. Si pidiera una mas, el margen baja de "
          f"{SM_TOTALES - sm} a {SM_TOTALES - sm - 1}.")
    print("  * **el reparto de los dos nucleos NO se decide aqui.** Hoy el "
          "nucleo 0 es tiempo real y el 1")
    print("    atribucion (nucleo sec.7), y el host USB no tiene sitio "
          "declarado. Ese es el tercer punto")
    print("    del #150 y es decision de arquitectura, no de guion: va en "
          "propuesta aparte.")
    print("  * **la cuarta comprobacion de check_pinout.py** —que cada pin "
          "pueda hacer lo que se le pide,")
    print("    contra la tabla de funciones por GPIO del datasheet— no esta "
          "aqui. Este guion mide")
    print("    capacidad y ventana, no identidad de funcion.")
    print("  * **el micro del modulo de Voz es OTRO censo** y no esta aqui: "
          "issue #205. Este guion")
    print("    cubre el cerebro y solo el cerebro. Y desde el 2026-08-26 **ya "
          "ni siquiera es el mismo")
    print("    chip**: la Voz lleva un N657 y este censo sigue siendo de un "
          "RP2350 sin sellar.")


if __name__ == "__main__":
    import sys
    demo()
    if _HUECOS:
        print(f"HUECO: {_HUECOS[0]}; el censo del cerebro sobrecuenta 4 "
              f"maquinas de PIO desde que el afinado se mudo al N657")
        sys.exit(2)
