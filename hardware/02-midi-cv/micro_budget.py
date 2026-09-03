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
       grande no cabe en su SRAM (cerebro S7). O sea que el tamano de la
       pantalla del instrumento lo decidio el chip, no el instrumento.

  Este guion pone los dos sitios y los dos candidatos en la misma tabla, con los
  numeros de las hojas y no de la memoria de nadie.

QUE DECIDE Y QUE NO

  Decide si un chip DA los recursos que cada sitio pide: canales de medida con
  su DMA, resolucion de sellado, ancho de contador, memoria y USB.

  NO decide cual se compra. El reparto de pines, la dificultad de la placa, el
  precio y el ruido son terminos reales que este guion no mira, y estan listados
  abajo uno por uno.

NOTA 2026-08-26: el sello del N657 (spec motor-digital, PR #212) retira al
  H750 como clase y disuelve la particion de dos RP2350B. La comparacion de
  abajo queda como historia de la decision; la vara v2 la trae #214 (tanda 2).
  Lo NUEVO de este guion es el CENSO DE PINES DEL N657 (puerta 2 del sello,
  issue #213), al final del archivo: sin su verde no se compra silicio.

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
# La pantalla que la spec del cerebro rechazo, con su cuenta (cerebro S7).
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
# COPIADOS A MANO de lo que autotune_budget.py deriva; verificados contra
# su recalculo el 2026-08-26 (61.16 ms / 477.8 us / 131.3 ns). La junta de
# la pantalla cazo que la version anterior de esta nota juraba un
# acoplamiento automatico que no existe: nada grita si autotune cambia.
# Importarlos de verdad exige exponer las formulas alla -- fila del #214.
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
    # En bytes y no en "KB": cerebro S7 dice 768 KB contando 1 KB = 1000 B, y
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


# ===========================================================================
# EL CENSO DE PINES DEL N657 -- la puerta 2 del sello (issue #213)
# ===========================================================================
#
# El spec del motor digital (docs/superpowers/specs/2026-08-26-motor-digital-
# design.md, S1.2) sella el STM32N657 con dos puertas de papel. La primera
# (peticiones de DMA) se cruzo el mismo dia (RM0486 Rev 4, Tablas 86 y 98).
# Esta es la segunda: sentar a TODAS las funciones a la mesa A LA VEZ y
# probar que existe un reparto donde ningun pin tiene dos duenos. Clausula
# del spec: "No se compra silicio hasta su verde". Rojo = el chip cae desde
# el papel y el retorno declarado es el RA8M1 (benchmark S5-S6).
#
# FUENTE   docs/reference/datasheets/stm32n657-ds14791-rev2.pdf
#          Tabla 16 (pp86-109): una fila por pin, con su ball en cada uno de
#          los seis encapsulados (VFBGA142/169/178/198/223/264) y sus
#          funciones alternas y adicionales. La tabla de abajo es la
#          destilacion de esa tabla a LAS SENALES QUE ESTE INSTRUMENTO PIDE:
#          extraccion determinista por script (pypdf), con las 60 filas que
#          el PDF vuelca rotadas (todas de pines que solo viven en los
#          encapsulados grandes) reconstruidas y verificadas contra el
#          volcado crudo. Ningun modelo de lenguaje toco estos datos.
#
# QUE SE SIENTA A LA MESA (spec S1.2 punto 2 y S11 riesgo 1):
#   1. Las 16 entradas de captura del autoafinado: TIM2..TIM5 x CH1..CH4,
#      MENOS dos canales que el acta de la pantalla muda a TIM1 (punto 10
#      y el comentario de CAPTURAS).
#   2. El SAI full-duplex del codec: MCLK+SCK+FS del subbloque A (boca) y
#      SD del A mas SD del B en sincrono (oidos). 5 pines.
#   3. Los 3 buses SPI maestros del CV con NSS por hardware (spec S5):
#      SCK+MOSI+NSS por bus. El MISO no se reserva: el DAC no se lee en v1
#      (si R-M3 trae lectura, es un pin mas por bus y el censo se recorre).
#   4. El J2 esclavo full-duplex: SCK+MOSI+MISO+NSS (#210).
#   4b. El crosspoint de la bahia (acta 2026-09-02, issue #171): los dos
#      AD75019 en cadena por un SPI PROPIO, SCK+MOSI, distinto de los tres
#      de CV (que son DMA puro con NSS por hardware y no se comparten) y del
#      J2. Sin NSS (el chip no tiene chip select) ni MISO (el SOUT no se lee
#      en v1). El strobe PCLK es un GPIO y sigue en N6_GPIO_VARIOS.
#   5. RGMII del GMAC: 13 senales (las 12 del estandar mas CLK125, reserva
#      prudente cuya necesidad depende del arbol de relojes del PHY) +
#      MDC/MDIO = 15 lineas -- reservado AUNQUE D9 siga en cuarentena: el
#      censo prueba el peor caso. La junta verifico que soltar CLK125 (y
#      hasta MDC/MDIO) NO salva a los encapsulados menores: el
#      estrangulamiento es RXD0/PF14, no la reserva prudente.
#   6. El control del codec: I2C (SCL+SDA). ESTIMADO: el codec no esta
#      nombrado (R-M3); si su control fuera SPI, es un CS mas y se recorre.
#   7. Dos entradas de ADC. La primera es el camino rapido a los oidos
#      (D-P4, spec S4). La segunda la pide el issue #213 como "telemetria
#      del puente (S4)" -- la junta verifico que NINGUN papel vigente la
#      respalda (el S4 no contiene la palabra telemetria; la unica
#      telemetria del repo es la de la fuente, otro modulo y otro chip).
#      Se sienta igual como RESERVA barata y la cita huerfana queda
#      anotada aqui para que nadie la herede como hecho.
#   8. La PSRAM del sampler en XSPI1 (acta de Samuel 2026-08-26: granular y
#      sampler van a v1, la RAM externa deja de ser crecimiento). Octal:
#      NCS1 (PO0) + DQS0 (PO2) + CLK (PO4) + IO0..IO7 (PP0..PP7) = 11
#      pines, que solo existen desde VFBGA198. El ancho de 16 bits
#      (PP8..PP15 + DQS1/PO3) queda de crecimiento, 223+. La pieza concreta
#      se nombra con su hoja en el arbol antes de dibujar (R-M3).
#   9. Reservas fijas fuera de la mesa: SWD (PA13/PA14), HSE (PH0/PH1),
#      LSE del RTC (PC14/PC15 -- nada decide hoy que no haya cristal de
#      32 kHz, asi que se reservan), XSPI2 completo en el puerto PN
#      (PN0..PN12: arranque + biblioteca por NCS2 -- presente en LOS SEIS
#      encapsulados), USB con pines dedicados (OTG1/OTG2
#      HSDM/HSDP/ID/TXRTUNE, fuera del conteo GPIO), BOOT0 y NRST
#      dedicados.
#  10. La pantalla del motor (acta de Samuel 2026-08-26, noche: "Vamos
#      con A" -- 7" tactil directa al LTDC). El bus RGB paralelo de
#      24 bits: LCD_R0..R7 + G0..G7 + B0..B7 + HSYNC + VSYNC + DE + CLK =
#      28 pines. Entrar le costo a las capturas dos mudanzas de timer,
#      porque el VERDE del panel es el color apretado: LCD_G2 solo sale
#      por PA1 (que era el unico pin de TIM5_CH2 -- dos demandas y un
#      pin no tienen reparto) y LCD_G6 solo por PB11 (adonde la cadena
#      TIM5_CH4->PF6 forzaba a TIM2_CH4). La mudanza y su precio, en el
#      comentario de CAPTURAS. El tactil capacitivo comparte el I2C del
#      codec (control lento ambos, direcciones distintas); su INT/RST y
#      el PWM de retroiluminacion van en N6_GPIO_VARIOS. LCD_B4/LCD_B6
#      tambien salen por PN10/PN11 en el DS, pero el puerto PN entero es
#      reserva XSPI2 y no compite (igual se filtra en la puerta de
#      reproducibilidad).
#
# LO QUE EL VERDE NO DICE (y donde se cierra):
#   * Que el reloj kernel de CADA instancia SPI alcance los 50 MHz: la
#     Tabla 99 (105 MHz en maestro, 3.0-3.6 V) es el techo ELECTRICO del
#     kit; el arbol de relojes POR INSTANCIA es del RM0486 y NO se ha
#     verificado -- se verifica al escribir el arranque. La junta dejo
#     claro lo que ese pendiente puede y no puede mover: si el RM0486
#     descartara instancias, el reparto SE MUDA de instancias y el censo
#     se recorre -- lo que no se mueve es el encapsulado, porque el barrido
#     de abajo prueba TODOS los tercetos de CV posibles y el veredicto por
#     paquete no depende de cual gane. El escenario impreso (CV en SPI1-3)
#     es solo el reparto de muestra.
#   * El minimo "sin RGMII" asume que la opcion LVDS de D9 no pide pines
#     propios del N657 -- ESTIMADO: el transceptor no esta elegido (#210
#     D9, "la parte concreta NO esta elegida y este papel no la inventa").
#   * El CAUDAL de los 3 buses de CV: spi_privado_budget.py sigue modelando
#     los dos RP2350B viejos; su recorrido con la ley de dos tasas y la
#     trama real es fila del #214 (tanda 2). Este censo reparte PINES, no
#     ancho de banda. (Si el crosspoint colgaba de uno ya no es pregunta:
#     desde el acta 2026-09-02 va en SPI propio, punto 4b de arriba.)
#   * TIM1 y el RM0486, partido en dos (junta de la pantalla): el reloj
#     kernel es cola HEREDADA (la misma de las instancias SPI); el DMA de
#     captura de tim1_cc2/tim1_cc4 es pendiente NUEVO -- reabre en dos
#     lineas la clausula 1 del sello del motor, que solo verifico
#     tim2_cc1..tim5_cc4 (RM0486 Tablas 86/98). Y el desenlace honesto si
#     el RM0486 los negara NO es "re-repartir": TIM5_CH2 y LCD_G2 siguen
#     compartiendo {PA1}, asi que la salida real seria recortar verde al
#     panel o caer al camino B (controlador con framebuffer propio, spec
#     pantalla S1). "El encapsulado no se mueve" sigue siendo verdad,
#     pero por su razon vieja: el censo SIN pantalla ya elegia VFBGA264.
#   * Donde VIVE el framebuffer (768 000 B a 2 B/px; 1 152 000 B a 3; el
#     doble con doble buffer) dentro de los 4.2 MB de SRAM, y su CAUDAL
#     de refresco sostenido por AXI (800x480x60 = 23.04 Mpx/s: 46, 69 o
#     92 MB/s segun el formato del framebuffer -- la salida es RGB888 de
#     24 bits para este panel; el LTDC tambien saca YUV422-16, que aqui
#     no aplica, y el formato de ENTRADA lo elige cada capa, DS 3.29) contra
#     los grains del sampler: filas nuevas del censo de SRAM (spec S8.5)
#     y de carga_motor (#214 tanda 2). Este censo reparte PINES, no
#     memoria ni ancho de banda.
#   * Dominios VDDIO, zonas analogicas y EMI (riesgo 11), ruteo, LDAC/CLR
#     del DAC, errata: cada uno tiene su fila en el spec S11.

N6_PAQUETES = ("VFBGA142", "VFBGA169", "VFBGA178", "VFBGA198", "VFBGA223",
               "VFBGA264")

# Filas P[A-Q]x de la Tabla 16 presentes por encapsulado (el pool de GPIO).
N6_GPIO_TOTAL = {"VFBGA142": 75, "VFBGA169": 90, "VFBGA178": 106,
                 "VFBGA198": 127, "VFBGA223": 144, "VFBGA264": 165}

# Reservas fijas que salen del pool GPIO antes de repartir:
#   SWD PA13/PA14 + HSE PH0/PH1 + LSE PC14/PC15 (hallazgo de la junta: son
#   filas P[A-Q]x del pool y nadie las restaba) + XSPI2 PN0..PN12 (13,
#   presentes en los 6 encapsulados -- verificado en la extraccion).
N6_RESERVA_GPIO = 4 + 2 + 13

# Cuantos GPIO libres exige el resto del diseno tras el reparto:
#   la inhibicion de estado seguro R-M5 (1), el strobe PCLK del crosspoint
#   (1; su SCK y su MOSI ya no son "varios": se sientan a la mesa como SPI
#   propio desde el acta 2026-09-02, #171 -- punto 4b del encabezado)
#   y la pantalla (3, ESTIMADO hasta nombrar las piezas: INT y RST del
#   tactil capacitivo + PWM de retroiluminacion -- el tactil comparte el
#   I2C del codec, asi que no pide bus propio). OJO del ESTIMADO (junta):
#   el PWM del backlight NO es "cualquier GPIO" -- exige un pin con canal
#   de timer de salida; cuando la pieza tenga nombre (R-M3) se sienta a
#   la mesa como senal TIMx_CHy concreta. Hoy sobran candidatos (TIM1
#   CH1/CH3, TIM8 en PQ, TIM12-17 y LPTIM no estan demandados).
N6_GPIO_VARIOS = 2 + 3

# pin -> (presencia "142 169 178 198 223 264", senales demandadas que puede
# llevar). Destilado de la Tabla 16; "ADC_IN" marca funcion adicional
# ADCx_INPn. Solo pines que llevan al menos una senal demandada.
N6_PINES = {
    "PA0": ("xxxxxx", ("ADC_IN", "LCD_G3", "SAI2_SD_B", "SPI6_NSS", "TIM2_CH1", "TIM5_CH1")),
    "PA1": ("xxxxxx", ("ADC_IN", "LCD_G2", "TIM2_CH2")),
    "PA2": ("xxxxxx", ("ADC_IN", "LCD_B7", "TIM2_CH3", "TIM5_CH3")),
    "PA3": (".xxxxx", ("SAI1_SD_B", "SPI5_NSS")),
    "PA4": ("....xx", ("SPI5_MOSI",)),
    "PA5": ("xxxxxx", ("ADC_IN", "LCD_CLK", "SPI1_SCK", "SPI6_SCK", "TIM2_CH1")),
    "PA6": ("xxxxxx", ("ADC_IN", "LCD_B7", "LCD_HSYNC", "SPI1_MISO", "SPI6_MISO", "TIM3_CH1")),
    "PA7": ("..xxxx", ("ADC_IN", "LCD_B1", "LCD_R4", "SPI1_MOSI", "SPI6_MOSI", "TIM3_CH2")),
    "PA8": ("xxxxxx", ("ADC_IN", "I2C3_SCL", "LCD_B6")),
    "PA9": ("xxxxxx", ("ADC_IN", "I2C3_SDA", "LCD_B5", "SPI2_SCK", "TIM1_CH2")),
    "PA10": ("xxxxxx", ("ADC_IN", "LCD_B4")),
    "PA11": ("xxxxxx", ("ADC_IN", "LCD_B3", "SPI2_NSS", "TIM1_CH4")),
    "PA12": ("xxxxxx", ("ADC_IN", "LCD_B2", "SPI2_SCK")),
    "PA15": ("xxxxxx", ("LCD_R5", "SPI1_NSS", "SPI3_NSS", "SPI6_NSS", "TIM2_CH1")),
    "PB0": ("xxxxxx", ("SAI1_FS_A", "SPI4_NSS", "TIM1_CH4")),
    "PB1": ("....xx", ("LCD_R1", "TIM3_CH4")),
    "PB2": ("..x.xx", ("LCD_B2", "SAI1_SD_A", "SPI3_MOSI")),
    "PB4": ("xxxxxx", ("LCD_R3", "SPI1_MISO", "SPI2_NSS", "SPI3_MISO", "SPI6_MISO", "TIM3_CH1")),
    "PB5": ("xxxxxx", ("LCD_R2", "SPI1_MOSI", "SPI3_MOSI", "SPI6_MOSI", "TIM3_CH2")),
    "PB6": ("xxxxxx", ("SAI1_SCK_A", "SPI4_MISO")),
    "PB7": ("xxxxxx", ("SAI1_SD_A", "SPI4_MOSI")),
    "PB8": ("....xx", ("SPI1_MISO",)),
    "PB9": ("....xx", ("SPI1_SCK",)),
    "PB10": ("xxxxxx", ("ADC_IN", "I2C2_SCL", "LCD_G7", "SPI2_SCK", "TIM2_CH3")),
    "PB11": ("xxxxxx", ("ADC_IN", "I2C2_SDA", "LCD_G6")),
    "PB12": ("xxxxxx", ("LCD_G5", "SPI2_NSS")),
    "PB13": ("....xx", ("LCD_CLK", "SPI6_SCK")),
    "PB14": ("....xx", ("LCD_HSYNC",)),
    "PB15": ("....xx", ("LCD_G4", "SPI6_NSS")),
    "PC0": (".....x", ("LCD_R4", "SPI1_SCK", "SPI3_SCK", "SPI6_SCK", "TIM2_CH2")),
    "PC1": ("..xxxx", ("I2C1_SDA", "SPI2_NSS", "TIM4_CH4")),
    "PC2": (".....x", ("SAI1_SCK_A", "SPI3_MOSI")),
    "PC3": (".....x", ("SPI1_MOSI",)),
    "PC4": (".....x", ("LCD_DE", "LCD_VSYNC", "SPI2_MISO")),
    "PC5": (".....x", ("SAI2_SD_B", "SPI1_NSS")),
    "PC6": ("..xxxx", ("TIM3_CH1",)),
    "PC7": ("..xxxx", ("TIM3_CH2",)),
    "PC8": ("xxxxxx", ("LCD_B0", "TIM3_CH3")),
    "PC9": ("xxxxxx", ("I2C3_SDA", "LCD_B3", "TIM3_CH4")),
    "PC10": ("xxxxxx", ("I2C4_SCL", "SPI3_SCK")),
    "PC11": ("xxxxxx", ("I2C4_SDA", "SPI3_MISO")),
    "PC12": ("xxxxxx", ("SPI3_MOSI", "SPI6_SCK", "TIM1_CH4")),
    "PD1": ("xxxxxx", ("ETH1_MDC",)),
    "PD2": (".xxxxx", ("SAI1_SD_A", "SPI2_MOSI")),
    "PD4": (".xxxxx", ("I2C2_SDA", "SPI5_MISO")),
    "PD6": (".xxxxx", ("SPI2_MISO",)),
    "PD7": (".xxxxx", ("SPI2_MOSI", "SPI3_NSS", "TIM1_CH2")),
    "PD8": ("xxxxxx", ("LCD_R7",)),
    "PD9": ("..xxxx", ("LCD_R1",)),
    "PD11": (".xxxxx", ("I2C4_SDA", "SPI2_MISO")),
    "PD12": (".xxxxx", ("ETH1_MDIO",)),
    "PD13": ("..xxxx", ("LCD_R6", "SAI2_SCK_A", "TIM4_CH2")),
    "PD14": (".xxxxx", ("I2C2_SCL",)),
    "PD15": (".xxxxx", ("I2C2_SDA", "LCD_R2")),
    "PE0": ("xxxxxx", ("SAI2_MCLK_A",)),
    "PE2": ("xxxxxx", ("SAI1_MCLK_A", "SPI4_SCK")),
    "PE3": ("xxxxxx", ("SAI1_SD_B",)),
    "PE4": (".....x", ("LCD_G1", "SPI6_MISO")),
    "PE5": (".xxxxx", ("I2C1_SCL", "TIM4_CH1")),
    "PE6": ("..xxxx", ("I2C1_SDA", "TIM4_CH2")),
    "PE7": ("xxxxxx", ("SAI2_SD_B",)),
    "PE11": (".xxxxx", ("LCD_VSYNC", "SAI2_SD_B", "SPI4_NSS", "TIM1_CH2")),
    "PE12": ("xxxxxx", ("SPI4_SCK",)),
    "PE13": ("xxxxxx", ("I2C4_SCL", "SPI4_MISO")),
    "PE14": ("xxxxxx", ("I2C4_SDA", "SPI4_MOSI", "TIM1_CH4")),
    "PE15": ("xxxxxx", ("SPI5_SCK",)),
    "PF0": ("...xxx", ("ETH1_RGMII_GTX_CLK", "TIM4_CH4")),
    "PF1": ("...xxx", ("TIM4_CH3",)),
    "PF2": ("xxxxxx", ("ETH1_RGMII_CLK125", "LCD_B1", "SPI2_SCK")),
    "PF3": ("xxxxxx", ("ADC_IN", "LCD_R4")),
    "PF4": ("xxxxxx", ("ADC_IN", "ETH1_MDIO", "LCD_R3", "SPI1_NSS", "SPI3_NSS", "SPI6_NSS")),
    "PF5": ("xxxxxx", ("LCD_G0", "SAI2_SD_A")),
    "PF6": ("..xxxx", ("ADC_IN", "LCD_DE", "TIM5_CH4")),
    "PF7": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_RX_CLK", "LCD_VSYNC", "SPI1_SCK", "TIM3_CH3")),
    "PF8": ("xxxxxx", ("ETH1_RGMII_RXD2", "LCD_R6")),
    "PF9": ("...xxx", ("ETH1_RGMII_RXD3", "LCD_HSYNC")),
    "PF10": ("xxxxxx", ("ETH1_RGMII_RX_CTL", "LCD_R1")),
    "PF11": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_TX_CTL", "LCD_B0", "SAI2_SD_B", "SPI5_MOSI")),
    "PF12": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_TXD0", "SPI5_MISO")),
    "PF13": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_TXD1", "SPI5_NSS")),
    "PF14": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_RXD0", "LCD_G0", "SPI5_MOSI", "TIM2_CH2")),
    "PF15": ("xxxxxx", ("ETH1_RGMII_RXD1", "LCD_G1", "SPI5_SCK")),
    "PG0": ("..xxxx", ("LCD_R0", "LCD_VSYNC")),
    "PG1": ("..xxxx", ("LCD_G1", "SPI5_MISO")),
    "PG2": ("xxxxxx", ("LCD_R0", "SPI5_MOSI")),
    "PG3": ("...xxx", ("ETH1_RGMII_TXD2",)),
    "PG4": ("...xxx", ("ETH1_RGMII_TXD3", "LCD_B0")),
    "PG5": ("...xxx", ("LCD_B1",)),
    "PG6": ("...xxx", ("LCD_B3",)),
    "PG7": (".....x", ("SAI1_MCLK_A",)),
    "PG8": ("..xxxx", ("LCD_G7", "SPI2_MOSI")),
    "PG9": ("...xxx", ("LCD_R7",)),
    "PG10": ("xxxxxx", ("LCD_G4", "SPI2_SCK")),
    "PG11": ("...xxx", ("ETH1_MDC", "LCD_R6")),
    "PG12": ("..xxxx", ("LCD_G0", "SPI5_SCK")),
    "PG13": ("xxxxxx", ("LCD_DE", "SAI2_FS_A", "TIM4_CH1")),
    "PG14": ("xxxxxx", ("LCD_B1", "SPI6_MOSI")),
    "PG15": ("..xxxx", ("ADC_IN", "LCD_B0", "TIM1_CH4")),
    "PH3": (".....x", ("LCD_B4",)),
    "PH4": (".....x", ("LCD_R4",)),
    "PH5": (".....x", ("ETH1_MDC", "SPI5_SCK")),
    "PH6": (".....x", ("LCD_B5", "SPI5_NSS")),
    "PH7": (".....x", ("SPI5_MOSI",)),
    "PH8": (".....x", ("SPI5_MISO",)),
    "PH9": ("..xxxx", ("I2C1_SCL", "TIM4_CH3")),
    "PP8": ("....xx", ("SPI2_MISO",)),
    "PP9": ("....xx", ("SPI2_MOSI",)),
    "PP10": ("....xx", ("ETH1_MDC",)),
    "PP15": ("....xx", ("LCD_B5",)),
    "PQ6": (".....x", ("SAI2_SD_B",)),
    # XSPI1 -- la PSRAM del sampler (acta 2026-08-26). Senales de un solo
    # pin cada una: el puerto es dedicado y nace en VFBGA198. PO2/PO3/PO4
    # llevan ademas suplencias LCD_* segun el DS: la mesa arbitra, y la
    # PSRAM (senales de pin unico) siempre gana la suya.
    "PO0": ("...xxx", ("XSPIM_P1_NCS1",)),
    "PO2": ("...xxx", ("LCD_B7", "XSPIM_P1_DQS0")),
    "PO3": ("....xx", ("LCD_G3",)),
    "PO4": ("...xxx", ("LCD_B4", "XSPIM_P1_CLK")),
    "PP0": ("...xxx", ("XSPIM_P1_IO0",)),
    "PP1": ("...xxx", ("XSPIM_P1_IO1",)),
    "PP2": ("...xxx", ("XSPIM_P1_IO2",)),
    "PP3": ("...xxx", ("XSPIM_P1_IO3",)),
    "PP4": ("...xxx", ("XSPIM_P1_IO4",)),
    "PP5": ("...xxx", ("XSPIM_P1_IO5",)),
    "PP6": ("...xxx", ("XSPIM_P1_IO6",)),
    "PP7": ("...xxx", ("XSPIM_P1_IO7",)),
}

# La PSRAM octal del sampler: 11 senales, cada una con su unico pin.
PSRAM = ("XSPIM_P1_NCS1", "XSPIM_P1_DQS0", "XSPIM_P1_CLK", "XSPIM_P1_IO0",
         "XSPIM_P1_IO1", "XSPIM_P1_IO2", "XSPIM_P1_IO3", "XSPIM_P1_IO4",
         "XSPIM_P1_IO5", "XSPIM_P1_IO6", "XSPIM_P1_IO7")

# Las 16 capturas del autoafinado. La base es TIM2..TIM5 (contadores de
# 32 bits, DS Tabla 97) -- pero el acta de la pantalla (2026-08-26,
# noche) muda DOS canales a TIM1, de 16 bits, porque sus pines eran los
# unicos del verde del panel (punto 10 del encabezado). El precio, con su
# fuente: un contador de 16 bits a 200 MHz (techo de reloj kernel, DS
# Tabla 97) da la vuelta cada 327.68 us -- menos que la ventana MAS CORTA
# del barrido (C8, 478 us), asi que los dos canales mudados llevan la
# cuenta de desbordes en firmware EN LAS 84 NOTAS, no solo en las graves
# (la junta cazo la causal subdeclarada: la larga de C1, 61.2 ms, da ~187
# vueltas; la corta da al menos una). Ese
# analisis NO es nuevo: es el de la seccion H750 de este mismo archivo,
# que lo declaro "tecnica conocida, pero trabajo por canal" -- y alla
# eran OCHO canales asi; aqui son dos. La resolucion de sello no se toca
# (1/200 MHz = 5 ns << 131 ns de jitter presupuestado) porque el reloj no
# se divide: se cuenta.
CAPTURAS = (
    "TIM2_CH1", "TIM2_CH2", "TIM2_CH3", "TIM1_CH4",   # TIM2_CH4 -> TIM1_CH4
    "TIM3_CH1", "TIM3_CH2", "TIM3_CH3", "TIM3_CH4",
    "TIM4_CH1", "TIM4_CH2", "TIM4_CH3", "TIM4_CH4",
    "TIM5_CH1", "TIM1_CH2", "TIM5_CH3", "TIM5_CH4",   # TIM5_CH2 -> TIM1_CH2
)

# La pantalla del motor (acta 2026-08-26, camino A): el bus RGB paralelo
# del LTDC a 24 bits mas sus cuatro senales de sincronia. El repliegue a
# 16 bits (RGB565: R3..R7 + G2..G7 + B3..B7, 20 pines) queda documentado
# como salida de apuro, no como plan.
PANTALLA = tuple(f"LCD_{c}{i}" for c in "RGB" for i in range(8)) + (
    "LCD_HSYNC", "LCD_VSYNC", "LCD_DE", "LCD_CLK")
RGMII = ("ETH1_RGMII_GTX_CLK", "ETH1_RGMII_CLK125", "ETH1_RGMII_TX_CTL",
         "ETH1_RGMII_TXD0", "ETH1_RGMII_TXD1", "ETH1_RGMII_TXD2",
         "ETH1_RGMII_TXD3", "ETH1_RGMII_RX_CLK", "ETH1_RGMII_RX_CTL",
         "ETH1_RGMII_RXD0", "ETH1_RGMII_RXD1", "ETH1_RGMII_RXD2",
         "ETH1_RGMII_RXD3", "ETH1_MDC", "ETH1_MDIO")


def _candidatos(senal: str, ipaq: int) -> frozenset:
    """Pines que llevan `senal` y existen en el encapsulado `ipaq` (0..5)."""
    return frozenset(pin for pin, (pres, senales) in N6_PINES.items()
                     if senal in senales and pres[ipaq] == "x")


def _demandas(ipaq: int, sai: str, cvs: tuple, j2: str, i2c: str,
              con_rgmii: bool, sai2_extra: bool = False,
              xp: str | None = None) -> list | None:
    """La mesa completa: [(etiqueta, candidatos)]. None si una senal ya no
    tiene NINGUN pin en este encapsulado (rojo inmediato, sin buscar).
    `sai2_extra` sienta ademas el otro SAI entero -- su subbloque A completo
    y el SD de su B en sincrono, igual que el titular (la boca multicanal
    TDM del crecimiento, spec S10): los 4 subbloques del chip a la mesa,
    como pide el issue #213. (La junta cazo la v1 de este parametro
    sentando 3 de 4: le faltaba el SD_B del segundo SAI.)
    `xp` es la instancia SPI del crosspoint de la bahia (punto 4b del
    encabezado): SCK + MOSI, sin NSS ni MISO."""
    mesa = []
    for s in CAPTURAS:
        mesa.append((s, _candidatos(s, ipaq)))
    for sub in ("MCLK_A", "SCK_A", "FS_A", "SD_A", "SD_B"):
        s = f"{sai}_{sub}"
        mesa.append((s, _candidatos(s, ipaq)))
    if sai2_extra:
        otro = "SAI2" if sai == "SAI1" else "SAI1"
        for sub in ("MCLK_A", "SCK_A", "FS_A", "SD_A", "SD_B"):
            s = f"{otro}_{sub}"
            mesa.append((f"TDM:{s}", _candidatos(s, ipaq)))
    for s in PSRAM:
        mesa.append((f"PSRAM:{s}", _candidatos(s, ipaq)))
    for s in PANTALLA:
        # sin prefijo: el nombre LCD_* ya agrupa solo (acta camino A)
        mesa.append((s, _candidatos(s, ipaq)))
    for n, spi in enumerate(cvs, 1):
        for rol in ("SCK", "MOSI", "NSS"):
            s = f"{spi}_{rol}"
            mesa.append((f"CV{n}:{s}", _candidatos(s, ipaq)))
    for rol in ("SCK", "MOSI", "MISO", "NSS"):
        s = f"{j2}_{rol}"
        mesa.append((f"J2:{s}", _candidatos(s, ipaq)))
    if xp is not None:
        for rol in ("SCK", "MOSI"):
            s = f"{xp}_{rol}"
            mesa.append((f"XP:{s}", _candidatos(s, ipaq)))
    for rol in ("SCL", "SDA"):
        s = f"{i2c}_{rol}"
        mesa.append((f"CODEC:{s}", _candidatos(s, ipaq)))
    if con_rgmii:
        for s in RGMII:
            mesa.append((s, _candidatos(s, ipaq)))
    adc = _candidatos("ADC_IN", ipaq)
    mesa.append(("ADC:oidos-rapidos", adc))
    # la segunda entrada: cita huerfana del issue #213 (ver punto 7 del
    # encabezado) -- se sienta como reserva, no como hecho de papel
    mesa.append(("ADC:reserva-issue213", adc))
    if any(not c for _, c in mesa):
        return None
    return mesa


def _asignar(mesa: list) -> dict | None:
    """Reparto inyectivo por vuelta atras con la senal mas apretada primero.
    Devuelve {etiqueta: pin} o None si no existe reparto."""
    asignado: dict = {}
    usados: set = set()

    def paso(pendientes) -> bool:
        if not pendientes:
            return True
        pendientes = sorted(pendientes, key=lambda d: len(d[1] - usados))
        etiqueta, cands = pendientes[0]
        for pin in sorted(cands - usados):
            asignado[etiqueta] = pin
            usados.add(pin)
            if paso(pendientes[1:]):
                return True
            del asignado[etiqueta]
            usados.remove(pin)
        return False

    return dict(asignado) if paso(mesa) else None


def _senal_de(etiqueta: str) -> str:
    """La senal del DS detras de una etiqueta de demanda."""
    if etiqueta.startswith("ADC:"):
        return "ADC_IN"
    # Cualquier prefijo "ROL:" es de agrupacion (CV1:, J2:, XP:, CODEC:, TDM:,
    # PSRAM:, y los del censo del hub R1:..R6:, MUX:, AUDIO:); la senal del
    # DS es lo que va despues de los dos puntos.
    if ":" in etiqueta:
        return etiqueta.split(":", 1)[1]
    return etiqueta


def _verificar_reparto(mesa: list, reparto: dict, ipaq: int) -> None:
    """El testigo se verifica contra las restricciones, NO contra el
    buscador que lo produjo. (La junta cazo la version anterior: una
    asercion de inyectividad sobre la salida de _asignar es inalcanzable
    por construccion -- Principio VIII, el mismo que este archivo invoca.)
    Aqui se re-deriva todo desde N6_PINES: cobertura, pertenencia, senal
    y presencia."""
    assert len(reparto) == len(mesa), (
        f"el reparto cubre {len(reparto)} de {len(mesa)} demandas")
    vistos: set = set()
    for etiqueta, _ in mesa:
        pin = reparto.get(etiqueta)
        assert pin is not None, f"{etiqueta} quedo sin asignar"
        assert pin not in vistos, f"{pin} tiene dos duenos"
        vistos.add(pin)
        pres, senales = N6_PINES[pin]
        assert pres[ipaq] == "x", f"{etiqueta}={pin} no existe en el paquete"
        assert _senal_de(etiqueta) in senales, (
            f"{pin} no lleva {_senal_de(etiqueta)} segun la Tabla 16")


def _estrangulamiento(mesa: list) -> str:
    """DIAGNOSTICO, no veredicto: nombra UNA cadena de forzados que mata el
    reparto del PRIMER escenario. La junta lo dejo escrito: el "culpable"
    es un eslabon de esa cadena (el orden puede nombrar a otro), y un
    conflicto sin singletons (violacion de Hall pura) cae al mensaje
    generico. El rojo lo decide la busqueda exhaustiva, nunca esto."""
    duenos: dict = {}
    pend = {et: set(c) for et, c in mesa}
    while True:
        forzada = next((et for et, c in pend.items() if len(c) == 1), None)
        if forzada is None:
            return "conflicto sin cadena de forzados (revisar a mano)"
        pin = next(iter(pend.pop(forzada)))
        duenos[pin] = forzada
        for et, c in pend.items():
            c.discard(pin)
            if not c:
                fuentes = [f"{p} es de {duenos[p]}" for p in
                           dict(mesa)[et] if p in duenos]
                return (f"una cadena que mata el reparto: {et} sin pin "
                        f"({'; '.join(fuentes)})")


def censo_paquete(ipaq: int, spis_cv: tuple, con_rgmii: bool = True):
    """Busca UN reparto valido en el encapsulado `ipaq` probando las
    combinaciones de instancias (SAI, 3 SPI de CV, SPI del J2, SPI del
    crosspoint, I2C del codec). Devuelve (asignacion, escenario) o
    (None, senal_sin_pin)."""
    from itertools import combinations

    primera_mesa = None
    for sai in ("SAI1", "SAI2"):
        for cvs in combinations(spis_cv, 3):
            libres_spi = [s for s in ("SPI1", "SPI2", "SPI3", "SPI4", "SPI5",
                                      "SPI6") if s not in cvs]
            for j2 in libres_spi:
                # el crosspoint en SPI propio (punto 4b): ni el J2 ni los CV
                for xp in (s for s in libres_spi if s != j2):
                    for i2c in ("I2C1", "I2C2", "I2C3", "I2C4"):
                        mesa = _demandas(ipaq, sai, cvs, j2, i2c, con_rgmii,
                                         xp=xp)
                        if mesa is None:
                            continue
                        if primera_mesa is None:
                            primera_mesa = mesa
                        reparto = _asignar(mesa)
                        if reparto is not None:
                            _verificar_reparto(mesa, reparto, ipaq)
                            return reparto, {"sai": sai, "cv": cvs, "j2": j2,
                                             "xp": xp, "i2c": i2c}
    # el mensaje del rojo: las senales sin pin en el encapsulado (todas,
    # no solo la primera -- hallazgo de la junta: "sin pin para TIM4_CH2"
    # invitaba a creer que con un pin se salvaba el 142, y le faltaban 8),
    # o el estrangulamiento del primer escenario
    rgmii_demanda = RGMII if con_rgmii else ()
    huerfanas = [s for s in CAPTURAS + rgmii_demanda + PSRAM + PANTALLA
                 if not _candidatos(s, ipaq)]
    if huerfanas:
        resto = f" (+{len(huerfanas) - 1} senales mas sin pin)" \
            if len(huerfanas) > 1 else ""
        return None, f"sin pin para {huerfanas[0]}{resto}"
    if primera_mesa is not None:
        return None, _estrangulamiento(primera_mesa)
    return None, "ninguna combinacion de instancias tiene mesa completa"


def _autocomprobacion_censo() -> None:
    """Contra cuentas hechas a mano sobre la Tabla 16, no contra el codigo."""
    # A mano contra el DS: TIM5 solo sale por PA0/PA1/PA2/PF6; el CH4 solo
    # por PF6, que no existe en VFBGA142/169. Es EL pin que decide el
    # encapsulado minimo de las capturas.
    assert _candidatos("TIM5_CH4", 5) == {"PF6"}
    assert _candidatos("TIM5_CH1", 5) == {"PA0"}
    assert _candidatos("TIM5_CH4", 0) == frozenset()
    assert _candidatos("TIM5_CH4", 1) == frozenset()
    # A mano: SAI1_FS_A solo en PB0; el GTX_CLK del RGMII solo en PF0 (que
    # nace en VFBGA198); el FS_A del SAI2 solo en PG13.
    assert _candidatos("SAI1_FS_A", 5) == {"PB0"}
    assert _candidatos("ETH1_RGMII_GTX_CLK", 5) == {"PF0"}
    assert _candidatos("ETH1_RGMII_GTX_CLK", 2) == frozenset()
    assert _candidatos("SAI2_FS_A", 5) == {"PG13"}
    # A mano, pin por pin -- y se compara la LISTA, no solo el numero (la
    # junta cazo que contar 28 deja pasar un pin cambiado por otro). Tras
    # la mudanza de la pantalla: sale PB11 (solo llevaba TIM2_CH4, que ya
    # no se demanda) y entran los pines de TIM1_CH2/TIM1_CH4.
    con_captura = {p for p, (_, ss) in N6_PINES.items()
                   if any(s in ss for s in CAPTURAS)}
    assert con_captura == {
        "PA0", "PA1", "PA2", "PA5", "PA6", "PA7", "PA9", "PA11", "PA15",
        "PB0", "PB1", "PB4", "PB5", "PB10",
        "PC0", "PC1", "PC6", "PC7", "PC8", "PC9", "PC12",
        "PD7", "PD13", "PE5", "PE6", "PE11", "PE14",
        "PF0", "PF1", "PF6", "PF7", "PF14",
        "PG13", "PG15", "PH9"}, sorted(con_captura)
    # A mano contra el DS, para la pantalla (acta camino A): el verde del
    # panel es el color apretado -- G2/G5/G6 y el R5 son de pin unico, y
    # de ahi salio la mudanza de capturas.
    assert _candidatos("LCD_G2", 5) == {"PA1"}
    assert _candidatos("LCD_G5", 5) == {"PB12"}
    assert _candidatos("LCD_G6", 5) == {"PB11"}
    assert _candidatos("LCD_R5", 5) == {"PA15"}
    # El piso sin RGMII lo pone ahora la pantalla: LCD_G3 solo sale por
    # PA0 (que es el unico pin de TIM5_CH1) o por PO3, y PO3 nace en el
    # VFBGA223.
    assert _candidatos("TIM5_CH1", 5) == {"PA0"}
    assert _candidatos("LCD_G3", 3) == {"PA0"}
    assert _candidatos("LCD_G3", 4) == {"PA0", "PO3"}
    # Las dos capturas mudadas, contra la Tabla 16. OJO heredado de la
    # primera pasada: PB14 y PF1 llevan LPTIM1_CH2, no TIM1_CH2 -- la
    # puerta de reproducibilidad cazo la extraccion sin frontera
    # izquierda que los colaba.
    assert _candidatos("TIM1_CH2", 5) == {"PA9", "PD7", "PE11"}
    assert _candidatos("TIM1_CH4", 5) == {"PA11", "PB0", "PC12", "PE14",
                                          "PG15"}
    assert "TIM5_CH2" not in CAPTURAS and "TIM2_CH4" not in CAPTURAS
    assert len(CAPTURAS) == 16 and len(set(CAPTURAS)) == 16
    assert len(PANTALLA) == 28 and len(set(PANTALLA)) == 28
    # La escalera de GPIO del DS crece monotona con el encapsulado.
    escalera = [N6_GPIO_TOTAL[p] for p in N6_PAQUETES]
    assert escalera == sorted(escalera) and escalera[0] == 75 and escalera[-1] == 165
    # En el encapsulado grande ninguna senal demandada queda sin candidato.
    todas = set(CAPTURAS) | set(RGMII) | set(PSRAM) | set(PANTALLA) | {"ADC_IN"}
    todas |= {f"SAI{i}_{s}" for i in (1, 2)
              for s in ("MCLK_A", "SCK_A", "FS_A", "SD_A", "SD_B")}
    todas |= {f"SPI{i}_{s}" for i in (1, 2, 3, 4, 5, 6)
              for s in ("SCK", "MOSI", "MISO", "NSS")}
    todas |= {f"I2C{i}_{s}" for i in (1, 2, 3, 4) for s in ("SCL", "SDA")}
    for s in sorted(todas):
        assert _candidatos(s, 5), f"{s} sin candidato en VFBGA264"


def demo_censo() -> tuple[str, dict, dict, str | None]:
    """Corre el censo entero e imprime el veredicto por encapsulado.
    Devuelve (paquete elegido, reparto, escenario, minimo sin RGMII)."""
    print("\n\nEL CENSO DE PINES DEL N657 (puerta 2 -- issue #213)\n")
    print("  escenario impreso: CV en SPI1-3; RGMII reservado aunque D9 siga")
    print("  en cuarentena; PSRAM del sampler sentada (acta 2026-08-26);")
    print("  pantalla de 7\" al LTDC en 24 bits (acta camino A, misma fecha,")
    print("  noche) con dos capturas mudadas a TIM1.\n")

    elegido = None
    for ipaq, paq in enumerate(N6_PAQUETES):
        reparto, extra = censo_paquete(ipaq, ("SPI1", "SPI2", "SPI3"))
        if reparto is None:
            print(f"  {paq}: ROJO   ({extra})")
        else:
            usados = len(reparto)
            libres = N6_GPIO_TOTAL[paq] - N6_RESERVA_GPIO - usados
            print(f"  {paq}: VERDE  ({usados} pines repartidos, "
                  f"{libres} GPIO libres tras reservas)")
            if elegido is None:
                elegido = (paq, ipaq, reparto, extra)

    if elegido is None:
        # antes de declarar rojo pleno: el escenario amplio (CV en
        # cualquier SPI) distingue AMBAR de ROJO.
        amplio = any(censo_paquete(i, ("SPI1", "SPI2", "SPI3", "SPI4",
                                       "SPI5", "SPI6"))[0] is not None
                     for i in range(len(N6_PAQUETES)))
        if amplio:
            raise AssertionError(
                "AMBAR: solo hay reparto con CV fuera de SPI1-3. La compra "
                "queda bloqueada hasta verificar el arbol de relojes por "
                "instancia (RM0486) -- no se compra con un verde de truco")
        raise AssertionError(
            "ROJO EN LOS SEIS ENCAPSULADOS: el N657 cae desde el papel. "
            "El retorno declarado es el RA8M1 (benchmark S5-S6)")

    paq, ipaq, reparto, escenario = elegido
    libres = N6_GPIO_TOTAL[paq] - N6_RESERVA_GPIO - len(reparto)
    print(f"\n  LA VARIANTE ELEGIDA POR EL CENSO: {paq}")
    print(f"    instancias: SAI={escenario['sai']}, CV={'/'.join(escenario['cv'])}, "
          f"J2={escenario['j2']}, crosspoint={escenario['xp']}, "
          f"codec={escenario['i2c']}")
    print(f"    GPIO: {N6_GPIO_TOTAL[paq]} en el paquete - {N6_RESERVA_GPIO} "
          f"reservas fijas - {len(reparto)} repartidos = {libres} libres")

    print("\n  el reparto, funcion por funcion:")
    grupos = (("capturas", lambda e: e.startswith("TIM")),
              ("SAI (boca+oidos)", lambda e: e.startswith("SAI")),
              ("CV", lambda e: e.startswith("CV")),
              ("J2", lambda e: e.startswith("J2")),
              ("crosspoint (SPI)", lambda e: e.startswith("XP")),
              ("codec", lambda e: e.startswith("CODEC")),
              ("RGMII", lambda e: e.startswith("ETH")),
              ("ADC", lambda e: e.startswith("ADC")),
              ("PSRAM (XSPI1)", lambda e: e.startswith("PSRAM")),
              ("pantalla (LTDC)", lambda e: e.startswith("LCD")))
    for titulo, filtro in grupos:
        pares = [f"{e}={p}" for e, p in sorted(reparto.items()) if filtro(e)]
        print(f"    {titulo:18s}: " + ", ".join(pares))

    # Robustez a instancias (hallazgo de la junta): el arbol de relojes del
    # RM0486 sigue sin abrirse, asi que se prueba que el veredicto del
    # paquete NO depende del terceto de CV elegido -- se barren los 20.
    from itertools import combinations as _comb
    tercetos = list(_comb(("SPI1", "SPI2", "SPI3", "SPI4", "SPI5", "SPI6"), 3))
    cierran = sum(1 for t in tercetos if censo_paquete(ipaq, t)[0] is not None)
    print(f"\n  robustez a instancias: {cierran}/{len(tercetos)} tercetos "
          f"de CV cierran en {paq} -- si el RM0486 descarta instancias, "
          f"el reparto se muda, el encapsulado no")

    # El mismo censo sin RGMII: cuanto compra la decision LVDS de D9.
    print("\n  sin RGMII (si D9 eligiera LVDS):")
    minimo_sin_rgmii = None
    for ipaq2, paq2 in enumerate(N6_PAQUETES):
        r2, extra2 = censo_paquete(ipaq2, ("SPI1", "SPI2", "SPI3"),
                                   con_rgmii=False)
        v = "VERDE" if r2 is not None else f"ROJO ({extra2})"
        print(f"    {paq2}: {v}")
        if r2 is not None:
            minimo_sin_rgmii = paq2
            break

    # Crecimiento: los 4 subbloques de SAI a la mesa a la vez (la boca
    # multicanal TDM que el spec S10 difiere). Informativo, no bloquea --
    # pero el barrido es COMPLETO (junta de la pantalla): se prueban las
    # CUATRO instancias I2C del codec y se publica el conjunto que
    # cierra, porque "fuera de I2C1" era caracterizacion incompleta (I2C3
    # tambien mata el crecimiento) y el tactil de la pantalla comparte
    # ese mismo bus: la instancia equivocada rompe dos cosas.
    ult = len(N6_PAQUETES) - 1
    i2c_que_cierran = []
    for i2cc in ("I2C1", "I2C2", "I2C3", "I2C4"):
        cerro = False
        for j2c in ("SPI4", "SPI5", "SPI6"):
            for xpc in (s for s in ("SPI4", "SPI5", "SPI6") if s != j2c):
                mesa_c = _demandas(ult, "SAI1", ("SPI1", "SPI2", "SPI3"),
                                   j2c, i2cc, True, sai2_extra=True, xp=xpc)
                if mesa_c is None:
                    continue
                r_c = _asignar(mesa_c)
                if r_c:
                    _verificar_reparto(mesa_c, r_c, ult)
                    i2c_que_cierran.append(i2cc)
                    cerro = True
                    break
            if cerro:
                break
    if i2c_que_cierran:
        print(f"\n  crecimiento (v1 + SAI2 entero A+B, boca multicanal TDM) "
              f"en {N6_PAQUETES[-1]}: VERDE")
        muertas = [i for i in ("I2C1", "I2C2", "I2C3", "I2C4")
                   if i not in i2c_que_cierran]
        print(f"    el codec (y el tactil, que comparte su bus) solo puede "
              f"vivir en {{{', '.join(i2c_que_cierran)}}}: las otras "
              f"({', '.join(muertas)}) entierran la boca TDM sin que "
              f"ninguna puerta grite. El esquematico elige DE ESTA LISTA.")
        if escenario["i2c"] not in i2c_que_cierran:
            print(f"    OJO: el reparto de muestra de arriba usa "
                  f"codec={escenario['i2c']}, que NO esta en la lista -- es "
                  f"reparto de v1, no eleccion de esquematico")
        # Robustez del crecimiento a instancias (junta de la pantalla: el
        # 20/20 de v1 no vigilaba al crecimiento). Un bucle sobre codigo
        # que ya existe.
        crecen = 0
        for t in tercetos:
            libres_c = [s for s in ("SPI1", "SPI2", "SPI3", "SPI4",
                                    "SPI5", "SPI6") if s not in t]
            ok = False
            for j2c in libres_c:
                for xpc in (s for s in libres_c if s != j2c):
                    for i2cc in ("I2C1", "I2C2", "I2C3", "I2C4"):
                        mesa_c = _demandas(ult, "SAI1", t, j2c, i2cc, True,
                                           sai2_extra=True, xp=xpc)
                        if mesa_c is not None and _asignar(mesa_c):
                            ok = True
                            break
                    if ok:
                        break
                if ok:
                    break
            crecen += ok
        print(f"    robustez del crecimiento: {crecen}/{len(tercetos)} "
              f"tercetos de CV cierran con la boca TDM y la pantalla")
    else:
        print(f"\n  crecimiento (v1 + SAI2 entero A+B) en "
              f"{N6_PAQUETES[-1]}: ROJO")

    print("\n  la cuenta que ata el encapsulado a D9: PF14 sigue siendo el")
    print("  UNICO pin del RXD0 del RGMII (y del RMII). Con la pantalla")
    print("  sentada, PA1 se lo lleva LCD_G2 (su unico pin en todo el DS),")
    print("  asi que TIM2_CH2 queda entre PC0 -- que solo existe en el")
    print("  VFBGA264 -- y PF14. Ethernet por el GMAC interno + pantalla =")
    print("  VFBGA264 (un MAC externo por SPI no toca PF14, pero esa clase")
    print("  no da el ancho que D9 discute -- decision de D9, no de aqui).")
    print("  PREMISA DECLARADA de esta cuenta (junta de la pantalla): no se")
    print("  muda una TERCERA captura. Con TIM2_CH2->TIM1_CH3 el VFBGA223")
    print("  cerraria hasta con RGMII completo -- al precio de un tercer")
    print("  canal de 16 bits con cuenta de desbordes. La cuenta INFORMA la")
    print("  economia de D9; no la decide, y la compra del 264 ya esta")
    print("  sellada por la asercion inversa de abajo. D9 = LVDS baja el")
    print("  minimo al de arriba, con su ESTIMADO de siempre (la huella del")
    print("  transceptor no esta elegida, #210 D9) -- y ese piso ya no lo")
    print("  pone la PSRAM en el 198: lo sube la pantalla al VFBGA223, por")
    print("  dos cadenas independientes: LCD_G3 solo sale por PA0 (unico")
    print("  pin de TIM5_CH1) o por PO3, y LCD_CLK solo por PA5 o PB13 --")
    print("  y PO3 y PB13 nacen los dos en el 223.")

    return paq, reparto, escenario, minimo_sin_rgmii


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
        "rechazo de la pantalla grande en cerebro S7")
    assert fb < H7_SRAM_B, "el framebuffer no cabe ni en el H750"

    # 6. El USB del cerebro: hoy es un controlador y un truco.
    assert RP_USB_NATIVO < 2 <= H7_USB_OTG, (
        "el reparto de controladores USB cambio: releer por que el host va "
        "por PIO en el cerebro")

    # 7. EL CENSO DE PINES DEL N657 (puerta 2 del sello, issue #213 --
    #    con la pantalla del acta camino A sentada al LTDC).
    _autocomprobacion_censo()
    paq, reparto, _escenario, minimo_sin_rgmii = demo_censo()

    # La asercion del issue #213 ("ningun pin con dos duenos") vive en
    # _verificar_reparto: el testigo se comprueba contra N6_PINES, no
    # contra el buscador que lo produjo. La version anterior de esta
    # guarda era inalcanzable por construccion y la junta la tumbo con el
    # Principio VIII de este mismo archivo.

    # Tras el reparto y las reservas fijas quedan GPIO para lo vario
    # (R-M5 + crosspoint + INT/RST del tactil y PWM del backlight de la
    # pantalla) -- y se exige holgura, no empate.
    libres = N6_GPIO_TOTAL[paq] - N6_RESERVA_GPIO - len(reparto)
    assert libres >= N6_GPIO_VARIOS + 4, (
        f"la variante {paq} deja {libres} GPIO libres; lo vario pide "
        f"{N6_GPIO_VARIOS} y sin holgura no se compra")

    # El resultado del censo, congelado como asercion INVERSA: si una nueva
    # revision del DS (o una edicion de la tabla) moviera estos veredictos,
    # este guion tiene que gritar y la compra se relee. OJO: tambien salta
    # si la noticia es BUENA (un encapsulado mas chico que empieza a
    # cerrar) -- se relee y se actualiza, no se borra.
    assert paq == "VFBGA264", (
        f"el censo con RGMII ya no elige VFBGA264 (elige {paq}): releer la "
        "cuenta de PF14/TIM2_CH2 y el acoplamiento con D9")
    assert minimo_sin_rgmii == "VFBGA223", (
        f"el minimo sin RGMII cambio a {minimo_sin_rgmii}: releer la "
        "clausula de D9 del issue #213 y el piso de la pantalla (acta "
        "camino A: LCD_G3 vive en PO3, que nace en el 223 -- antes el "
        "piso era la PSRAM en el 198)")

    print("\n  VERDE: el censo cierra. Se levanta el bloqueo de compra "
          f"del issue #213 con la variante {paq}.")

    # 8. EL CENSO DE PINES DEL HUB (spec 2026-08-30 S10 fila 1: "verde
    #    antes de firmar D1"). El escenario base se asevera; audio (A-6) y
    #    RGMII (D9) se imprimen porque donde viven sigue sin acta.
    _mutacion_hub()
    _reparto_hub, libres_hub = demo_censo_hub()
    assert libres_hub - HUB_GPIO_VARIOS >= HUB_HOLGURA, (
        f"el hub deja {libres_hub} GPIO libres en VFBGA264; lo vario pide "
        f"{HUB_GPIO_VARIOS} y sin holgura de {HUB_HOLGURA} no se firma D1")
    print(f"\n  VERDE: el hub cierra en VFBGA264 con {libres_hub} GPIO libres "
          f"({libres_hub - HUB_GPIO_VARIOS:+d} tras lo vario). Queda mandado "
          "destilar los USART de la Tabla 16 para sentar las dos ranuras "
          "restantes con nombre de pin.")

    print("\nOK: presupuesto cerrado.")
    return 0


# ===========================================================================
# EL CENSO DE PINES DEL HUB (spec 2026-08-30-hub-n657-y-radios, S10 fila 1)
#
# El cerebro pasa a un segundo N657 (D1) y se lleva la cara (D2). Este censo
# reparte SUS pines sobre la misma Tabla 16, con el mismo buscador y el mismo
# testigo que el de la Voz. Lo que se sienta a la mesa, con su fuente:
#
#   * SEIS ranuras J2 en maestros SPI de hardware (J2 punto a punto D3: "6
#     maestros SPI de hardware -- 4 activas + 2 de repuesto rapido"), cada
#     una con SCK, MOSI, MISO y NSS (D4: full duplex, MISO privado).
#   * La pantalla al LTDC en 24 bits (D2: el mismo camino A de la Voz).
#   * La PSRAM por XSPI1 para el framebuffer (spec hub S3.1: "su PSRAM por
#     XSPI queda libre para el framebuffer").
#   * El tronco I2C del arbol de descubrimiento (nucleo S3.5). El tactil
#     comparte ese I2C, como el tactil compartia el del codec en la Voz.
#   * El pedal, a entrada analogica (nucleo S10: "para que sirva tambien de
#     expresion").
#   * Opcional: SAI para la interfaz de audio (acta A-6), si cuelga del hub.
#   * Opcional: RGMII para la autopista (D9), si el hub es su maestro.
#
# Lo que NO se sienta porque no es GPIO del pool o no esta en N6_PINES, y
# se cobra como "varios" contra los GPIO libres:
#   * Las DOS ranuras restantes por USART sincrono (D3). Sus senales
#     (USARTx_CK/TX/RX) no estan destiladas en N6_PINES -- la tabla solo
#     trae senales que el censo de la Voz demandaba. Se cobran 4 GPIO por
#     ranura (CK, TX, RX y el CS por GPIO que D3 declara) y queda mandado
#     destilar los USART de la Tabla 16 antes de sellar D1.
#   * USB OTG1/OTG2 (pines dedicados, DS), CSI (dedicado; y por D3' la
#     camara ya no vive en el hub), XSPI2 del arranque (ya en la reserva).
#   * MIDI DIN in/out por UART (2), el ESP32-S3 por UART + EN + boot (4),
#     la radio ESB por SPI/UART + IRQ + EN (4, ESTIMADO sin pieza),
#     clock/reset in/out (4), INT/RST del tactil + PWM del backlight (3),
#     RESET del mux (1). La cadena WS2812 cobraba aqui 1 pin con canal de
#     timer o MOSI; se retiro el 2026-09-03 (spec del instrumento entero, D1)
#     y el censo baja de 27 a 26.
HUB_SPIS = ("SPI1", "SPI2", "SPI3", "SPI4", "SPI5", "SPI6")
HUB_RANURAS_USART = 2
HUB_GPIO_VARIOS = (HUB_RANURAS_USART * 4   # CK, TX, RX, CS-por-GPIO
                   + 2                     # MIDI DIN in/out (UART)
                   + 4                     # ESP32-S3: UART x2, EN, boot
                   + 4                     # radio ESB: bus x2, IRQ, EN (ESTIMADO)
                   + 4                     # clock/reset in/out
                   + 3                     # tactil INT/RST + PWM backlight
                   + 1)                    # RESET del mux I2C
HUB_HOLGURA = 4                            # la misma que exige el censo de la Voz


def _demandas_hub(ipaq: int, i2c: str, con_audio: str | None,
                  con_rgmii: bool) -> list | None:
    """La mesa del hub: [(etiqueta, candidatos)], o None si una senal no
    tiene ningun pin en el encapsulado."""
    mesa = []
    for n, spi in enumerate(HUB_SPIS, 1):
        for rol in ("SCK", "MOSI", "MISO", "NSS"):
            s = f"{spi}_{rol}"
            mesa.append((f"R{n}:{s}", _candidatos(s, ipaq)))
    for s in PANTALLA:
        mesa.append((s, _candidatos(s, ipaq)))
    for s in PSRAM:
        mesa.append((f"PSRAM:{s}", _candidatos(s, ipaq)))
    for rol in ("SCL", "SDA"):
        s = f"{i2c}_{rol}"
        mesa.append((f"MUX:{s}", _candidatos(s, ipaq)))
    mesa.append(("ADC:pedal", _candidatos("ADC_IN", ipaq)))
    if con_audio:
        for sub in ("MCLK_A", "SCK_A", "FS_A", "SD_A", "SD_B"):
            s = f"{con_audio}_{sub}"
            mesa.append((f"AUDIO:{s}", _candidatos(s, ipaq)))
    if con_rgmii:
        for s in RGMII:
            mesa.append((s, _candidatos(s, ipaq)))
    if any(not c for _, c in mesa):
        return None
    return mesa


def censo_hub_paquete(ipaq: int, con_audio: bool, con_rgmii: bool):
    """Un reparto valido del hub en el encapsulado `ipaq`, probando el I2C
    del tronco y (si hay audio) el SAI. Devuelve (reparto, escenario) o
    (None, diagnostico)."""
    primera_mesa = None
    sais = ("SAI1", "SAI2") if con_audio else (None,)
    for sai in sais:
        for i2c in ("I2C1", "I2C2", "I2C3", "I2C4"):
            mesa = _demandas_hub(ipaq, i2c, sai, con_rgmii)
            if mesa is None:
                continue
            if primera_mesa is None:
                primera_mesa = mesa
            reparto = _asignar(mesa)
            if reparto is not None:
                _verificar_reparto(mesa, reparto, ipaq)
                return reparto, {"i2c": i2c, "sai": sai}
    if primera_mesa is not None:
        return None, _estrangulamiento(primera_mesa)
    huerfanas = [s for s in PANTALLA + PSRAM
                 + tuple(f"{spi}_{r}" for spi in HUB_SPIS
                         for r in ("SCK", "MOSI", "MISO", "NSS"))
                 if not _candidatos(s, ipaq)]
    if huerfanas:
        resto = f" (+{len(huerfanas) - 1} senales mas sin pin)" \
            if len(huerfanas) > 1 else ""
        return None, f"sin pin para {huerfanas[0]}{resto}"
    return None, "ninguna combinacion de instancias tiene mesa completa"


def _mutacion_hub() -> None:
    """Principio VIII, tres mordidas:
    1. El buscador sabe decir que NO: el VFBGA142 no puede sentar la mesa
       del hub (75 GPIO menos 19 de reserva son 56, y solo los 6 SPI y la
       pantalla piden 52 antes de la PSRAM).
    2. Las instancias se cuentan POR CONSTRUCCION, no por pines. La primera
       version de esta mutacion pedia SPI1 dos veces y el buscador ENCONTRO
       reparto: la Tabla 16 da mas de un pin a cada senal de SPI1, y un
       censo de pines no sabe que una instancia no puede ser dos maestros.
       Lo que guarda "seis ranuras y no siete" es que HUB_SPIS sean
       exactamente las instancias SPI que el DS destilado conoce.
    3. El testigo muerde: un reparto corrompido (un pin que no lleva la
       senal) tiene que tumbar _verificar_reparto."""
    reparto, _ = censo_hub_paquete(0, con_audio=False, con_rgmii=False)
    assert reparto is None, "el censo del hub cierra en VFBGA142: no vigila"

    instancias = {s.split("_", 1)[0] for _, senales in N6_PINES.values()
                  for s in senales if s.startswith("SPI")}
    assert instancias == set(HUB_SPIS), (
        f"las instancias SPI de la tabla son {sorted(instancias)} y el hub "
        f"pide {HUB_SPIS}: una ranura sin instancia o una instancia sin ranura")

    mesa = _demandas_hub(5, "I2C1", None, False)
    assert mesa is not None
    bueno = _asignar(mesa)
    assert bueno is not None
    etiqueta = next(et for et, _ in mesa if et.startswith("R1:"))
    senal = _senal_de(etiqueta)
    ajeno = next(p for p, (pres, senales) in N6_PINES.items()
                 if pres[5] == "x" and senal not in senales
                 and p not in bueno.values())
    corrupto = dict(bueno, **{etiqueta: ajeno})
    try:
        _verificar_reparto(mesa, corrupto, 5)
    except AssertionError:
        pass
    else:
        raise AssertionError(
            f"{etiqueta}={ajeno} no lleva {senal} y el testigo lo dio por bueno")


def demo_censo_hub() -> tuple[dict, int]:
    """Corre el censo del hub e imprime el veredicto por encapsulado y por
    escenario. Devuelve (reparto del escenario base en VFBGA264, libres)."""
    print("\n\nEL CENSO DE PINES DEL HUB (spec 2026-08-30, S10 fila 1)\n")
    print("  base: 6 ranuras J2 en SPI1-6, pantalla al LTDC en 24 bits,")
    print("  PSRAM del framebuffer, tronco I2C del descubrimiento, pedal.")
    print(f"  Lo vario se cobra aparte: {HUB_GPIO_VARIOS} GPIO (2 ranuras por")
    print("  USART sincrono, MIDI, ESP32-S3, radio ESB, clock/reset,")
    print("  tactil, mux) mas holgura de", HUB_HOLGURA, "-- ESTIMADO sin piezas.\n")

    escenarios = (("base", False, False), ("+ audio (A-6 en el hub)", True, False),
                  ("+ RGMII (D9, el hub maestro)", False, True),
                  ("+ audio + RGMII", True, True))
    base = None
    for nombre, audio, rgmii in escenarios:
        print(f"  escenario {nombre}:")
        for ipaq, paq in enumerate(N6_PAQUETES):
            reparto, extra = censo_hub_paquete(ipaq, audio, rgmii)
            if reparto is None:
                print(f"    {paq}: ROJO   ({extra})")
                continue
            libres = N6_GPIO_TOTAL[paq] - N6_RESERVA_GPIO - len(reparto)
            sobra = libres - HUB_GPIO_VARIOS
            veredicto = "VERDE" if sobra >= HUB_HOLGURA else "ROJO "
            print(f"    {paq}: {veredicto}  ({len(reparto)} repartidos, "
                  f"{libres} libres, {sobra:+d} tras lo vario)")
            if nombre == "base" and paq == "VFBGA264":
                base = (reparto, libres)
    assert base is not None, "el escenario base del hub no cierra en VFBGA264"
    return base


# ---------------------------------------------------------------------------
# LO QUE ESTE CALCULO **NO** CUBRE
#
#   * EL PINOUT DEL CEREBRO CON NOMBRE DE PIN. El censo del hub de arriba
#     demuestra que el reparto cabe y propone uno de muestra; el pinout real
#     lo elige el esquematico del hub, que no existe, y `pinout.rs` lo
#     declara como indices de propuesta hasta entonces. `pio_budget.py`
#     (maquinas de PIO del RP2350B) se retiro a historia el 2026-09-03: su
#     sujeto murio con el hub D1, y desde ese dia el NSS por hardware que
#     este censo reparte es REQUISITO del maestro del J2 (D1), no reparto.
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
