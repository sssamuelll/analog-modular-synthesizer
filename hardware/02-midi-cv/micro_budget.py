#!/usr/bin/env python3
"""Que micro aguanta cada sitio: el cerebro y el modulo de Voz, dos candidatos.

    python micro_budget.py

POR QUE EXISTE ESTE GUION

  El RP2350 nunca se comparo contra otro microcontrolador. Se comparo contra una
  Raspberry Pi 3B+ que iba dentro del instrumento (nucleo S1), gano, y se quedo.
  Desde entonces gobierna dos decisiones grandes que nadie ha vuelto a mirar:

    1. El modulo de Voz lleva DOS micros. Y por UN solo numero: dieciseis
       osciladores piden dieciseis cronometros, y el chip da doce maquinas de
       PIO (dieciseis S3: "lo que sostiene los dos micros es solo el PIO").
       De esa particion salen la base de tiempo compartida, el arranque en dos
       mitades y la historia entera de recuperacion entre columnas.

    2. El cerebro se quedo con una pantalla de 2,8" porque el framebuffer de la
       grande no cabe en su SRAM (cerebro S9.1). O sea que el tamano de la
       pantalla del instrumento lo decidio el chip, no el instrumento.

  Este guion pone los dos sitios y los dos candidatos en la misma tabla, con los
  numeros de las hojas y no de la memoria de nadie.

QUE DECIDE Y QUE NO

  Decide si un chip DA los recursos que cada sitio pide: canales de medida con
  su DMA, resolucion de sellado, ancho de contador, memoria y USB.

  NO decide cual se compra. El reparto de pines, la dificultad de la placa, el
  precio y el ruido son terminos reales que este guion no mira, y estan listados
  abajo uno por uno.

FUENTES

  RP2350B   docs/reference/datasheets/rp2350-product-brief-2024-08.pdf
            p2: "Three high-performance Programmable I/O (PIO) co-processors,
                 with a total of twelve independent state machines"
            p2: "variants: with 30 or 48 GPIO pins"
            p3: "520 KB on-chip SRAM, in ten independent banks"
            p3: "Support for up to 16 MB of external QSPI flash/PSRAM"

  STM32H750 docs/reference/datasheets/stm32h750-ds12556-rev8.pdf
            Tabla 4 (p39-40): canales de captura/comparacion por temporizador,
                 con su columna de "DMA request generation" y de resolucion
            p2:  "2x USB OTG interfaces (1FS, 1HS/FS)"
            p2:  "LCD-TFT controller up to XGA resolution"
            p2:  "1 Mbyte RAM"
            p31: cuatro instancias de DMA; la MDMA con 16 canales
"""
from __future__ import annotations

# --- lo que pide el modulo de Voz ----------------------------------------
#
# Los cronometros son la afinacion: conteo reciproco sobre el pulso logico que
# el disparador Schmitt saca por oscilador (autotune_budget.py). Samuel decidio
# el 2026-08-25 que los DIECISEIS se miden a la vez -- multiplexarlos alargaba
# el barrido de 2,75 s a 3,82 s y cerraba la puerta a medir mientras se toca.
OSCILADORES = 16
CRONOMETROS_VOZ = OSCILADORES

# El oyente del J2 en broadcast. 1 hoy; 2 si el evento de nota sale fuera de la
# cadencia y el receptor pasa a ser de largo variable (issue #205).
OYENTE_J2_MIN = 1
OYENTE_J2_MAX = 2

# El codec de los oidos. El acta E-5 de voz-total lo muda a esta placa y el
# RP2350 no trae periferico I2S, asi que sale por PIO (issue #205).
CODEC_MIN = 1
CODEC_MAX = 2

# --- lo que pide el cerebro ----------------------------------------------
#
# La pantalla que la spec del cerebro rechazo, con su cuenta (cerebro S9.1).
PANTALLA_ANCHO = 800
PANTALLA_ALTO = 480
PANTALLA_BPP = 16

# La de 2,8" que se quedo en su sitio, para tener el contraste.
PANTALLA_CHICA_ANCHO = 320
PANTALLA_CHICA_ALTO = 240

# --- RP2350B, contra su hoja ----------------------------------------------
RP_MAQUINAS_PIO = 12          # product brief p2, "twelve independent state machines"
RP_GPIO = 48                  # product brief p2, variante B
RP_SRAM_B = 520 * 1024        # product brief p3, "520 KB on-chip SRAM"
RP_F_PIO = 150e6              # Hz. clk_sys sin dividir; el mismo supuesto que
                              # autotune_budget.py declara y marca como tal
RP_CONTADOR_BITS = 32         # el cronometro de PIO cuenta en un registro de 32
RP_USB_NATIVO = 1             # un controlador. El host sale por PIO
RP_TIENE_LTDC = False         # no hay controlador de pantalla: el frame se
                              # empuja por SPI

# --- STM32H750, contra su hoja --------------------------------------------
#
# Tabla 4, paginas 39-40. Solo cuentan los canales cuya fila dice que SI genera
# peticion de DMA: medir a mano se lo come el procesador, que es justo lo que el
# PIO del RP2350 evita ("with little or no CPU overhead").
#
#   (nombre, canales, bits del contador, genera DMA)
H7_TEMPORIZADORES = (
    ("TIM1, TIM8",          8, 16, True),
    ("TIM2, TIM5",          8, 32, True),
    ("TIM3, TIM4",          8, 16, True),
    ("TIM15",               2, 16, True),
    ("TIM16, TIM17",        2, 16, True),
    ("TIM12, TIM13, TIM14", 4, 16, False),
)
H7_F_TIM = 240e6              # Hz. Tabla 4, columna "Max timer clock" de los
                              # TIM1..TIM17. El HRTIM1 llega a 480 y NO se cuenta
H7_SRAM_B = 1024 * 1024       # p2, "1 Mbyte RAM"
H7_USB_OTG = 2                # p2, "2x USB OTG interfaces (1FS, 1HS/FS)"
H7_TIENE_LTDC = True          # p2, "LCD-TFT controller up to XGA resolution"

# --- el presupuesto de afinacion que gobierna la medida --------------------
#
# IMPORTADOS de autotune_budget.py, que es su fuente viva. No se re-derivan
# aqui: si aquel cambia, este tiene que romperse, y para eso esta la
# autocomprobacion de abajo.
VENTANA_LARGA_S = 61.2e-3     # la nota mas grave del barrido (C1)
VENTANA_CORTA_S = 478e-6      # la mas aguda (C8), la que menos perdona
JITTER_MAX_S = 131e-9         # lo que puede temblar el 74HC14 y aun cumplir


def canales_con_dma(temporizadores) -> int:
    """Canales de captura utiles: los que pueden sellar sin gastar procesador."""
    return sum(n for _, n, _, dma in temporizadores if dma)


def canales_de_32_bits(temporizadores) -> int:
    """Los que aguantan la ventana larga sin llevar cuenta de desbordes."""
    return sum(n for _, n, bits, dma in temporizadores if dma and bits >= 32)


def resolucion_s(f_hz: float) -> float:
    """Cuanto vale un tick: el suelo del sellado de tiempo."""
    return 1.0 / f_hz


def ventana_maxima_sin_desborde_s(bits: int, f_hz: float) -> float:
    """Cuanto puede durar una medida antes de que el contador de la vuelta."""
    return (2 ** bits) / f_hz


def divisor_para_ventana(ventana_s: float, bits: int, f_hz: float) -> float:
    """El divisor de reloj que haria caber `ventana_s` en `bits`.

    Devuelve el factor, no el registro: lo que interesa es la resolucion que
    deja detras, que es `divisor / f_hz`.
    """
    return ventana_s * f_hz / (2 ** bits)


def framebuffer_b(ancho: int, alto: int, bpp: int) -> int:
    return ancho * alto * bpp // 8


def piden_voz(oyente: int, codec: int) -> int:
    """Canales de medida y de interfaz que el modulo de Voz necesita a la vez."""
    return CRONOMETROS_VOZ + oyente + codec


def _autocomprobacion() -> None:
    """Contra casos hechos a mano, no contra el propio calculo."""
    # A mano: 8 + 8 + 8 + 2 + 2 = 28 con DMA; los TIM12/13/14 no cuentan.
    assert canales_con_dma(H7_TEMPORIZADORES) == 28, canales_con_dma(H7_TEMPORIZADORES)
    assert canales_de_32_bits(H7_TEMPORIZADORES) == 8

    # A mano: 65536 ticks a 240 MHz son 273,07 us.
    t16 = ventana_maxima_sin_desborde_s(16, 240e6)
    assert abs(t16 - 273.07e-6) < 0.01e-6, f"16 bits a mano: {t16*1e6:.2f} us"

    # A mano: 800*480*16/8 = 768 000 B.
    assert framebuffer_b(800, 480, 16) == 768_000

    # A mano: un tick a 150 MHz son 6,667 ns, que es lo que autotune_budget.py
    # publica como sellado del PIO.
    assert abs(resolucion_s(150e6) - 6.667e-9) < 0.001e-9


def demo() -> None:
    print("LOS DOS CANDIDATOS\n")
    print(f"  {'':28s} {'RP2350B':>14s} {'STM32H750':>14s}")
    print("  " + "-" * 58)

    h7_dma = canales_con_dma(H7_TEMPORIZADORES)
    h7_32 = canales_de_32_bits(H7_TEMPORIZADORES)
    print(f"  {'canales de medida con DMA':28s} {RP_MAQUINAS_PIO:>14d} {h7_dma:>14d}")
    print(f"  {'   de ellos, de 32 bits':28s} {RP_MAQUINAS_PIO:>14d} {h7_32:>14d}")
    print(f"  {'resolucion del sellado':28s} "
          f"{resolucion_s(RP_F_PIO)*1e9:>13.2f}n {resolucion_s(H7_F_TIM)*1e9:>13.2f}n")
    print(f"  {'SRAM interna':28s} "
          f"{RP_SRAM_B/1024:>13.0f}K {H7_SRAM_B/1024:>13.0f}K")
    print(f"  {'controladores USB nativos':28s} {RP_USB_NATIVO:>14d} {H7_USB_OTG:>14d}")
    print(f"  {'controlador de pantalla':28s} "
          f"{'no':>14s} {'si (XGA)':>14s}")

    print("\n\nSITIO 1 -- EL MODULO DE VOZ\n")
    print(f"  cronometros (los 16 a la vez, decision del 2026-08-25) : {CRONOMETROS_VOZ:>3d}")
    print(f"  oyente del J2                                          : {OYENTE_J2_MIN:>3d} a {OYENTE_J2_MAX}")
    print(f"  codec de los oidos (E-5)                               : {CODEC_MIN:>3d} a {CODEC_MAX}")
    lo, hi = piden_voz(OYENTE_J2_MIN, CODEC_MIN), piden_voz(OYENTE_J2_MAX, CODEC_MAX)
    print(f"  {'':55s}  ---")
    print(f"  piden                                                  : {lo:>3d} a {hi}")
    print()
    print(f"  RP2350B da {RP_MAQUINAS_PIO:>2d}  ->  "
          f"{'NO CABE' if hi > RP_MAQUINAS_PIO else 'cabe'}"
          f"   (por eso el modulo lleva DOS)")
    print(f"  H750    da {h7_dma:>2d}  ->  "
          f"{'no cabe' if hi > h7_dma else 'CABE'}"
          f", y sobran {h7_dma - hi} canales en el peor caso")

    print("\n  El detalle que no se puede olvidar: el ancho del contador\n")
    print(f"    la ventana mas larga del barrido (C1) dura {VENTANA_LARGA_S*1e3:.1f} ms")
    for bits in (16, 32):
        v = ventana_maxima_sin_desborde_s(bits, H7_F_TIM)
        cabe = "aguanta" if v >= VENTANA_LARGA_S else "DA LA VUELTA"
        u = f"{v*1e6:.0f} us" if v < 1 else f"{v:.1f} s"
        print(f"    contador de {bits} bits a {H7_F_TIM/1e6:.0f} MHz: {u:>8s}  -> {cabe}")
    div = divisor_para_ventana(VENTANA_LARGA_S, 16, H7_F_TIM)
    res = div / H7_F_TIM
    print(f"\n    Dividir el reloj para que quepa deja la resolucion en {res*1e9:.0f} ns,")
    print(f"    que son {res/JITTER_MAX_S:.0f}x el presupuesto de jitter de {JITTER_MAX_S*1e9:.0f} ns.")
    print("    O sea: dividir NO es salida.")
    en_16 = CRONOMETROS_VOZ - h7_32
    print(f"\n    De los {CRONOMETROS_VOZ} cronometros, {h7_32} caben en los canales de 32 bits")
    print(f"    (TIM2 y TIM5) y los otros {en_16} tienen que llevar la cuenta de sus")
    print("    desbordes en firmware. Es tecnica conocida, pero es trabajo por canal.")

    print("\n\nSITIO 2 -- EL CEREBRO\n")
    fb = framebuffer_b(PANTALLA_ANCHO, PANTALLA_ALTO, PANTALLA_BPP)
    fbc = framebuffer_b(PANTALLA_CHICA_ANCHO, PANTALLA_CHICA_ALTO, PANTALLA_BPP)
    # En bytes y no en "KB": cerebro S9.1 dice 768 KB contando 1 KB = 1000 B, y
    # esta seccion dice 520 KB contando 1 KB = 1024. Comparar las dos cifras tal
    # como estan escritas alli es comparar dos unidades distintas.
    print(f"  framebuffer de {PANTALLA_ANCHO}x{PANTALLA_ALTO} a {PANTALLA_BPP} bits"
          f" : {fb:>9,d} B")
    print(f"  framebuffer de la de 2,8\" ({PANTALLA_CHICA_ANCHO}x{PANTALLA_CHICA_ALTO})"
          f"    : {fbc:>9,d} B")
    print()
    for nombre, sram, ltdc in (("RP2350B", RP_SRAM_B, RP_TIENE_LTDC),
                               ("H750", H7_SRAM_B, H7_TIENE_LTDC)):
        veredicto = "cabe" if fb <= sram else "NO CABE"
        print(f"  {nombre:8s} SRAM {sram:>9,d} B -> la grande {veredicto}"
              f"   | controlador de pantalla: {'si' if ltdc else 'no'}")
    print()
    print("  Y el USB, que es la razon por la que el RP2350 esta ahi:")
    print("    RP2350   1 controlador nativo + host por PIO (Pico-PIO-USB),")
    print("             cuyo censo de instrucciones sigue ESTIMADO (issue #205)")
    print("    H750     2 controladores OTG nativos: host y device sin truco")


def main() -> int:
    _autocomprobacion()
    demo()

    h7_dma = canales_con_dma(H7_TEMPORIZADORES)
    pide_max = piden_voz(OYENTE_J2_MAX, CODEC_MAX)
    fb = framebuffer_b(PANTALLA_ANCHO, PANTALLA_ALTO, PANTALLA_BPP)

    # 1. El numero que parte el modulo en dos. Es una asercion INVERSA: falla el
    #    dia que deje de ser verdad, y ese dia hay que releer la decision de los
    #    dos micros en vez de heredarla.
    assert CRONOMETROS_VOZ > RP_MAQUINAS_PIO, (
        "los 16 cronometros ya caben en un RP2350B. La particion en dos columnas "
        "existe SOLO por este numero (dieciseis S3): releer esa decision")

    # 2. El candidato grande tiene que dar los canales con su DMA, no a secas.
    assert h7_dma >= pide_max, (
        f"el H750 da {h7_dma} canales con DMA y el peor caso del modulo de Voz "
        f"pide {pide_max}")

    # 3. Los dos chips tienen que sellar por debajo del presupuesto de jitter,
    #    o el autoafinado se degrada al cambiar de hierro.
    for nombre, f in (("RP2350B", RP_F_PIO), ("H750", H7_F_TIM)):
        assert resolucion_s(f) < JITTER_MAX_S, (
            f"{nombre} sella a {resolucion_s(f)*1e9:.1f} ns, por encima del "
            f"presupuesto de {JITTER_MAX_S*1e9:.0f} ns")

    # 4. Dividir el reloj para meter la ventana larga en 16 bits NO puede ser
    #    salida. Si algun dia lo fuera, la cuenta de desbordes deja de ser
    #    obligatoria y este guion tiene que decirlo en voz alta.
    res_dividido = divisor_para_ventana(VENTANA_LARGA_S, 16, H7_F_TIM) / H7_F_TIM
    assert res_dividido > JITTER_MAX_S, (
        "dividir el reloj ya cabe en el presupuesto de jitter: la cuenta de "
        "desbordes de los canales de 16 bits deja de ser obligatoria")

    # (Aqui vivia una asercion `h7_32 < CRONOMETROS_VOZ`, para que nadie
    #  presupuestase 16 canales de 32 bits limpios. Se quito al mutarla: NO
    #  PUEDE FALLAR NUNCA. Si se toca la tabla, la autocomprobacion salta antes;
    #  si se bajan los cronometros por debajo de 8, salta la asercion 1. Una
    #  asercion inalcanzable no vigila nada y se disfraza de verde -- Principio
    #  VIII. Lo que de verdad guarda ese hecho es la autocomprobacion sobre
    #  `canales_de_32_bits`, y la linea que la demo imprime.)

    # 5. La pantalla grande contra la SRAM de cada uno. Es el numero que
    #    encogio la pantalla del instrumento.
    assert fb > RP_SRAM_B, (
        "el framebuffer de 800x480 ya cabe en la SRAM del RP2350: releer el "
        "rechazo de la pantalla grande en cerebro S9.1")
    assert fb < H7_SRAM_B, "el framebuffer no cabe ni en el H750"

    # 6. El USB del cerebro: hoy es un controlador y un truco.
    assert RP_USB_NATIVO < 2 <= H7_USB_OTG, (
        "el reparto de controladores USB cambio: releer por que el host va "
        "por PIO en el cerebro")

    print("\nOK: presupuesto cerrado.")
    return 0


# ---------------------------------------------------------------------------
# LO QUE ESTE CALCULO **NO** CUBRE
#
#   * EL REPARTO DE PINES. Es lo mas importante que falta y no es un detalle:
#     que el H750 tenga 28 canales de captura no dice que sus pines lleguen
#     donde hacen falta, ni que queden libres despues del codec, la memoria
#     externa y el J2. Eso lo cierra `pines_budget.py` (dieciseis S15), que
#     sigue sin escribirse y que aquel papel manda escribir ANTES que ninguna
#     otra cosa del bloque digital.
#
#   * EL SUBMODULO DE CLASE DAISY. El acta E-5 pone los oidos en la placa de
#     Voz con un Daisy Patch Submodule (~£35, STM32H750 + codec + 64 MB SDRAM).
#     Este guion mide el CHIP DESNUDO. Cuantos pines saca ese modulo, y a que
#     temporizador va cada uno, no esta en ninguna hoja que se haya podido
#     descargar -- la documentacion oficial da 404. Sin ese dato no se sabe si
#     el camino barato (no dibujar nada) existe.
#
#   * LA DIFICULTAD DE LA PLACA. Rutear un Cortex-M7 a 480 MHz con memoria
#     externa no es lo mismo que rutear un RP2350: mas capas, mas rieles, y
#     temporizacion de memoria. Es trabajo real y no tiene cifra aqui.
#
#   * EL PRECIO. Un RP2350B ronda el dolar; un H750, diez o quince. En una
#     unidad no decide; en el numero de placas de este instrumento, tampoco
#     esta calculado.
#
#   * EL RUIDO. El codec de 24 bits esta en la placa de Voz porque "la medida
#     vive donde vive el audio" (nucleo S7.4) y para que NINGUNA linea analogica
#     cruce a lo digital. Poner en ese mismo chip dieciseis conversores y
#     treinta y dos jacks mete conmutacion al lado del convertidor. La frontera
#     GNDA/GNDD tiene su propio presupuesto y este no lo toca.
#
#   * EL CONSUMO. Ni el del chip ni el de la memoria externa. El +5 V del
#     instrumento ya va justo (power_budget.py, issue #151).
#
#   * LA MUDANZA DEL FIRMWARE. Se sabe que `core` son 8.840 lineas sin atar al
#     chip y `fw` 401 atadas a el, pero eso mide el tamano, no la dificultad:
#     cambiar de HAL, de arranque y de herramienta no es proporcional a las
#     lineas.
#
#   * CUANTAS MAQUINAS PIDE DE VERDAD Pico-PIO-USB. Sigue ESTIMADO hasta que
#     alguien compile su programa y cuente instrucciones (issue #205). Si
#     pidiera una mas, el margen del cerebro que aqui se da por bueno se
#     estrecha, y este guion no lo veria.
#
#   * EL HRTIM1. La hoja le da 10 canales mas a 480 MHz. No se cuentan porque
#     es un temporizador de alta resolucion pensado para conversion de potencia
#     y usarlo de captura pide leer el manual de referencia, no la hoja.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())
