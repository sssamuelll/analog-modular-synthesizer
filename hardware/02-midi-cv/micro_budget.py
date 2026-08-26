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
#   1. Las 16 entradas de captura TIM2..TIM5 x CH1..CH4 (el autoafinado).
#   2. El SAI full-duplex del codec: MCLK+SCK+FS del subbloque A (boca) y
#      SD del A mas SD del B en sincrono (oidos). 5 pines.
#   3. Los 3 buses SPI maestros del CV con NSS por hardware (spec S5):
#      SCK+MOSI+NSS por bus. El MISO no se reserva: el DAC no se lee en v1
#      (si R-M3 trae lectura, es un pin mas por bus y el censo se recorre).
#   4. El J2 esclavo full-duplex: SCK+MOSI+MISO+NSS (#210).
#   5. RGMII del GMAC completo (14 senales) + MDC/MDIO -- reservado AUNQUE
#      D9 siga en cuarentena: el censo prueba el peor caso. Si D9 elige
#      LVDS, estos pines se liberan (escenario aparte, abajo).
#   6. El control del codec: I2C (SCL+SDA). ESTIMADO: el codec no esta
#      nombrado (R-M3); si su control fuera SPI, es un CS mas y se recorre.
#   7. Dos entradas de ADC: el camino rapido a los oidos (D-P4) y la
#      telemetria del puente (S4).
#   8. Reservas fijas fuera de la mesa: SWD (PA13/PA14), HSE (PH0/PH1),
#      XSPI2 completo en el puerto PN (PN0..PN12: arranque + biblioteca por
#      NCS2 -- presente en LOS SEIS encapsulados), USB con pines dedicados
#      (OTG1/OTG2 HSDM/HSDP/ID/TXRTUNE, fuera del conteo GPIO), BOOT0 y
#      NRST dedicados.
#
# LO QUE EL VERDE NO DICE (y donde se cierra):
#   * Que el reloj kernel de CADA instancia SPI alcance los 50 MHz: la
#     Tabla 99 (105 MHz en maestro, 3.0-3.6 V) es el techo ELECTRICO del
#     kit; el arbol de relojes POR INSTANCIA es del RM0486 y NO se ha
#     verificado -- se verifica al escribir el arranque. Por eso el
#     veredicto de compra usa el escenario mas restringido (los 3 CV en
#     SPI1-3): restringir instancias solo puede QUITAR repartos, nunca
#     regalar uno -- si aun asi hay verde, el verde no depende de esa
#     verificacion pendiente. Si solo el escenario amplio (CV en cualquier
#     SPI) diera verde, la compra queda AMBAR hasta abrir el RM0486.
#   * Dominios VDDIO, zonas analogicas y EMI (riesgo 11), ruteo, LDAC/CLR
#     del DAC, errata: cada uno tiene su fila en el spec S11.
#   * XSPI1 (puerto PO/PP, la RAM externa de crecimiento) NO se reserva:
#     existe desde VFBGA198 (8 bits) y 223 (16 bits); queda anotado como
#     techo de crecimiento, no como demanda v1.

N6_PAQUETES = ("VFBGA142", "VFBGA169", "VFBGA178", "VFBGA198", "VFBGA223",
               "VFBGA264")

# Filas P[A-Q]x de la Tabla 16 presentes por encapsulado (el pool de GPIO).
N6_GPIO_TOTAL = {"VFBGA142": 75, "VFBGA169": 90, "VFBGA178": 106,
                 "VFBGA198": 127, "VFBGA223": 144, "VFBGA264": 165}

# Reservas fijas que salen del pool GPIO antes de repartir:
#   SWD PA13/PA14 + HSE PH0/PH1 + XSPI2 PN0..PN12 (13, presentes en los 6
#   encapsulados -- verificado en la extraccion).
N6_RESERVA_GPIO = 4 + 13

# Cuantos GPIO libres exige el resto del diseno tras el reparto:
#   la inhibicion de estado seguro R-M5 (1) y la carga del crosspoint (1,
#   ESTIMADO: AD75019 en cadena; si cuelga de un bus CV es solo el strobe).
N6_GPIO_VARIOS = 2

# pin -> (presencia "142 169 178 198 223 264", senales demandadas que puede
# llevar). Destilado de la Tabla 16; "ADC_IN" marca funcion adicional
# ADCx_INPn. Solo pines que llevan al menos una senal demandada.
N6_PINES = {
    "PA0": ("xxxxxx", ("ADC_IN", "SAI2_SD_B", "SPI6_NSS", "TIM2_CH1", "TIM5_CH1")),
    "PA1": ("xxxxxx", ("ADC_IN", "TIM2_CH2", "TIM5_CH2")),
    "PA2": ("xxxxxx", ("ADC_IN", "TIM2_CH3", "TIM5_CH3")),
    "PA3": (".xxxxx", ("SAI1_SD_B", "SPI5_NSS")),
    "PA4": ("....xx", ("SPI5_MOSI",)),
    "PA5": ("xxxxxx", ("ADC_IN", "SPI1_SCK", "SPI6_SCK", "TIM2_CH1")),
    "PA6": ("xxxxxx", ("ADC_IN", "SPI1_MISO", "SPI6_MISO", "TIM3_CH1")),
    "PA7": ("..xxxx", ("ADC_IN", "SPI1_MOSI", "SPI6_MOSI", "TIM3_CH2")),
    "PA8": ("xxxxxx", ("ADC_IN", "I2C3_SCL")),
    "PA9": ("xxxxxx", ("ADC_IN", "I2C3_SDA", "SPI2_SCK")),
    "PA10": ("xxxxxx", ("ADC_IN",)),
    "PA11": ("xxxxxx", ("ADC_IN", "SPI2_NSS")),
    "PA12": ("xxxxxx", ("ADC_IN", "SPI2_SCK")),
    "PA15": ("xxxxxx", ("SPI1_NSS", "SPI3_NSS", "SPI6_NSS", "TIM2_CH1")),
    "PB0": ("xxxxxx", ("SAI1_FS_A", "SPI4_NSS")),
    "PB1": ("....xx", ("TIM3_CH4",)),
    "PB2": ("..x.xx", ("SAI1_SD_A", "SPI3_MOSI")),
    "PB4": ("xxxxxx", ("SPI1_MISO", "SPI2_NSS", "SPI3_MISO", "SPI6_MISO", "TIM3_CH1")),
    "PB5": ("xxxxxx", ("SPI1_MOSI", "SPI3_MOSI", "SPI6_MOSI", "TIM3_CH2")),
    "PB6": ("xxxxxx", ("SAI1_SCK_A", "SPI4_MISO")),
    "PB7": ("xxxxxx", ("SAI1_SD_A", "SPI4_MOSI")),
    "PB8": ("....xx", ("SPI1_MISO",)),
    "PB9": ("....xx", ("SPI1_SCK",)),
    "PB10": ("xxxxxx", ("ADC_IN", "I2C2_SCL", "SPI2_SCK", "TIM2_CH3")),
    "PB11": ("xxxxxx", ("ADC_IN", "I2C2_SDA", "TIM2_CH4")),
    "PB12": ("xxxxxx", ("SPI2_NSS",)),
    "PB13": ("....xx", ("SPI6_SCK",)),
    "PB15": ("....xx", ("SPI6_NSS",)),
    "PC0": (".....x", ("SPI1_SCK", "SPI3_SCK", "SPI6_SCK", "TIM2_CH2")),
    "PC1": ("..xxxx", ("I2C1_SDA", "SPI2_NSS", "TIM4_CH4")),
    "PC2": (".....x", ("SAI1_SCK_A", "SPI3_MOSI")),
    "PC3": (".....x", ("SPI1_MOSI",)),
    "PC4": (".....x", ("SPI2_MISO",)),
    "PC5": (".....x", ("SAI2_SD_B", "SPI1_NSS")),
    "PC6": ("..xxxx", ("TIM3_CH1",)),
    "PC7": ("..xxxx", ("TIM3_CH2",)),
    "PC8": ("xxxxxx", ("TIM3_CH3",)),
    "PC9": ("xxxxxx", ("I2C3_SDA", "TIM3_CH4")),
    "PC10": ("xxxxxx", ("I2C4_SCL", "SPI3_SCK")),
    "PC11": ("xxxxxx", ("I2C4_SDA", "SPI3_MISO")),
    "PC12": ("xxxxxx", ("SPI3_MOSI", "SPI6_SCK")),
    "PD1": ("xxxxxx", ("ETH1_MDC",)),
    "PD2": (".xxxxx", ("SAI1_SD_A", "SPI2_MOSI")),
    "PD4": (".xxxxx", ("I2C2_SDA", "SPI5_MISO")),
    "PD6": (".xxxxx", ("SPI2_MISO",)),
    "PD7": (".xxxxx", ("SPI2_MOSI", "SPI3_NSS")),
    "PD11": (".xxxxx", ("I2C4_SDA", "SPI2_MISO")),
    "PD12": (".xxxxx", ("ETH1_MDIO",)),
    "PD13": ("..xxxx", ("SAI2_SCK_A", "TIM4_CH2")),
    "PD14": (".xxxxx", ("I2C2_SCL",)),
    "PD15": (".xxxxx", ("I2C2_SDA",)),
    "PE0": ("xxxxxx", ("SAI2_MCLK_A",)),
    "PE2": ("xxxxxx", ("SAI1_MCLK_A", "SPI4_SCK")),
    "PE3": ("xxxxxx", ("SAI1_SD_B",)),
    "PE4": (".....x", ("SPI6_MISO",)),
    "PE5": (".xxxxx", ("I2C1_SCL", "TIM4_CH1")),
    "PE6": ("..xxxx", ("I2C1_SDA", "TIM4_CH2")),
    "PE7": ("xxxxxx", ("SAI2_SD_B",)),
    "PE11": (".xxxxx", ("SAI2_SD_B", "SPI4_NSS")),
    "PE12": ("xxxxxx", ("SPI4_SCK",)),
    "PE13": ("xxxxxx", ("I2C4_SCL", "SPI4_MISO")),
    "PE14": ("xxxxxx", ("I2C4_SDA", "SPI4_MOSI")),
    "PE15": ("xxxxxx", ("SPI5_SCK",)),
    "PF0": ("...xxx", ("ETH1_RGMII_GTX_CLK", "TIM4_CH4")),
    "PF1": ("...xxx", ("TIM4_CH3",)),
    "PF2": ("xxxxxx", ("ETH1_RGMII_CLK125", "SPI2_SCK")),
    "PF3": ("xxxxxx", ("ADC_IN",)),
    "PF4": ("xxxxxx", ("ADC_IN", "ETH1_MDIO", "SPI1_NSS", "SPI3_NSS", "SPI6_NSS")),
    "PF5": ("xxxxxx", ("SAI2_SD_A",)),
    "PF6": ("..xxxx", ("ADC_IN", "TIM2_CH4", "TIM5_CH4")),
    "PF7": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_RX_CLK", "SPI1_SCK", "TIM3_CH3")),
    "PF8": ("xxxxxx", ("ETH1_RGMII_RXD2",)),
    "PF9": ("...xxx", ("ETH1_RGMII_RXD3",)),
    "PF10": ("xxxxxx", ("ETH1_RGMII_RX_CTL",)),
    "PF11": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_TX_CTL", "SAI2_SD_B", "SPI5_MOSI")),
    "PF12": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_TXD0", "SPI5_MISO")),
    "PF13": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_TXD1", "SPI5_NSS")),
    "PF14": ("xxxxxx", ("ADC_IN", "ETH1_RGMII_RXD0", "SPI5_MOSI", "TIM2_CH2")),
    "PF15": ("xxxxxx", ("ETH1_RGMII_RXD1", "SPI5_SCK")),
    "PG1": ("..xxxx", ("SPI5_MISO",)),
    "PG2": ("xxxxxx", ("SPI5_MOSI",)),
    "PG3": ("...xxx", ("ETH1_RGMII_TXD2",)),
    "PG4": ("...xxx", ("ETH1_RGMII_TXD3",)),
    "PG7": (".....x", ("SAI1_MCLK_A",)),
    "PG8": ("..xxxx", ("SPI2_MOSI",)),
    "PG10": ("xxxxxx", ("SPI2_SCK",)),
    "PG12": ("..xxxx", ("SPI5_SCK",)),
    "PG13": ("xxxxxx", ("SAI2_FS_A", "TIM4_CH1")),
    "PG14": ("xxxxxx", ("SPI6_MOSI",)),
    "PG15": ("..xxxx", ("ADC_IN",)),
    "PH5": (".....x", ("ETH1_MDC", "SPI5_SCK")),
    "PH6": (".....x", ("SPI5_NSS",)),
    "PH7": (".....x", ("SPI5_MOSI",)),
    "PH8": (".....x", ("SPI5_MISO",)),
    "PH9": ("..xxxx", ("I2C1_SCL", "TIM4_CH3")),
    "PP8": ("....xx", ("SPI2_MISO",)),
    "PP9": ("....xx", ("SPI2_MOSI",)),
    "PP10": ("....xx", ("ETH1_MDC",)),
    "PQ6": (".....x", ("SAI2_SD_B",)),
}

CAPTURAS = tuple(f"TIM{t}_CH{c}" for t in (2, 3, 4, 5) for c in (1, 2, 3, 4))
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
              con_rgmii: bool, sai2_extra: bool = False) -> list | None:
    """La mesa completa: [(etiqueta, candidatos)]. None si una senal ya no
    tiene NINGUN pin en este encapsulado (rojo inmediato, sin buscar).
    `sai2_extra` sienta ademas el subbloque A del otro SAI (la boca
    multicanal TDM del crecimiento, spec S10) -- los 4 subbloques del chip
    a la mesa, como pide el issue #213."""
    mesa = []
    for s in CAPTURAS:
        mesa.append((s, _candidatos(s, ipaq)))
    for sub in ("MCLK_A", "SCK_A", "FS_A", "SD_A", "SD_B"):
        s = f"{sai}_{sub}"
        mesa.append((s, _candidatos(s, ipaq)))
    if sai2_extra:
        otro = "SAI2" if sai == "SAI1" else "SAI1"
        for sub in ("MCLK_A", "SCK_A", "FS_A", "SD_A"):
            s = f"{otro}_{sub}"
            mesa.append((f"TDM:{s}", _candidatos(s, ipaq)))
    for n, spi in enumerate(cvs, 1):
        for rol in ("SCK", "MOSI", "NSS"):
            s = f"{spi}_{rol}"
            mesa.append((f"CV{n}:{s}", _candidatos(s, ipaq)))
    for rol in ("SCK", "MOSI", "MISO", "NSS"):
        s = f"{j2}_{rol}"
        mesa.append((f"J2:{s}", _candidatos(s, ipaq)))
    for rol in ("SCL", "SDA"):
        s = f"{i2c}_{rol}"
        mesa.append((f"CODEC:{s}", _candidatos(s, ipaq)))
    if con_rgmii:
        for s in RGMII:
            mesa.append((s, _candidatos(s, ipaq)))
    adc = _candidatos("ADC_IN", ipaq)
    mesa.append(("ADC:oidos-rapidos", adc))
    mesa.append(("ADC:telemetria", adc))
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


def _estrangulamiento(mesa: list) -> str:
    """Nombra al culpable de un reparto imposible: propaga las demandas de
    candidato unico y dice cual se queda sin pin y quien se los llevo."""
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
                return f"{et} se queda sin pin ({'; '.join(fuentes)})"


def censo_paquete(ipaq: int, spis_cv: tuple, con_rgmii: bool = True):
    """Busca UN reparto valido en el encapsulado `ipaq` probando las
    combinaciones de instancias (SAI, 3 SPI de CV, SPI del J2, I2C del
    codec). Devuelve (asignacion, escenario) o (None, senal_sin_pin)."""
    from itertools import combinations

    primera_mesa = None
    for sai in ("SAI1", "SAI2"):
        for cvs in combinations(spis_cv, 3):
            libres_spi = [s for s in ("SPI1", "SPI2", "SPI3", "SPI4", "SPI5",
                                      "SPI6") if s not in cvs]
            for j2 in libres_spi:
                for i2c in ("I2C1", "I2C2", "I2C3", "I2C4"):
                    mesa = _demandas(ipaq, sai, cvs, j2, i2c, con_rgmii)
                    if mesa is None:
                        continue
                    if primera_mesa is None:
                        primera_mesa = mesa
                    reparto = _asignar(mesa)
                    if reparto is not None:
                        return reparto, {"sai": sai, "cv": cvs, "j2": j2,
                                         "i2c": i2c}
    # el mensaje del rojo: o una senal sin pin en el encapsulado, o el
    # estrangulamiento del primer escenario
    rgmii_demanda = RGMII if con_rgmii else ()
    for s in CAPTURAS + rgmii_demanda:
        if not _candidatos(s, ipaq):
            return None, f"sin pin para {s}"
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
    # A mano, pin por pin: PA0/1/2/5/6/7/15, PB1/4/5/10/11, PC0/1/6/7/8/9,
    # PD13, PE5/6, PF0/1/6/7/14, PG13, PH9 = 28 pines llevan captura TIM2-5.
    con_captura = sum(1 for _, (_, ss) in N6_PINES.items()
                      if any(s in ss for s in CAPTURAS))
    assert con_captura == 28, con_captura
    # La escalera de GPIO del DS crece monotona con el encapsulado.
    escalera = [N6_GPIO_TOTAL[p] for p in N6_PAQUETES]
    assert escalera == sorted(escalera) and escalera[0] == 75 and escalera[-1] == 165
    # En el encapsulado grande ninguna senal demandada queda sin candidato.
    todas = set(CAPTURAS) | set(RGMII) | {"ADC_IN"}
    todas |= {f"SAI{i}_{s}" for i in (1, 2)
              for s in ("MCLK_A", "SCK_A", "FS_A", "SD_A", "SD_B")}
    todas |= {f"SPI{i}_{s}" for i in (1, 2, 3, 4, 5, 6)
              for s in ("SCK", "MOSI", "MISO", "NSS")}
    todas |= {f"I2C{i}_{s}" for i in (1, 2, 3, 4) for s in ("SCL", "SDA")}
    for s in sorted(todas):
        assert _candidatos(s, 5), f"{s} sin candidato en VFBGA264"


def demo_censo() -> tuple[str, dict, dict]:
    """Corre el censo entero e imprime el veredicto por encapsulado.
    Devuelve (paquete elegido, reparto, escenario)."""
    print("\n\nEL CENSO DE PINES DEL N657 (puerta 2 -- issue #213)\n")
    print("  escenario de compra: CV en SPI1-3 (reloj kernel conservador),")
    print("  RGMII reservado aunque D9 siga en cuarentena.\n")

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
          f"J2={escenario['j2']}, codec={escenario['i2c']}")
    print(f"    GPIO: {N6_GPIO_TOTAL[paq]} en el paquete - {N6_RESERVA_GPIO} "
          f"reservas fijas - {len(reparto)} repartidos = {libres} libres")

    print("\n  el reparto, funcion por funcion:")
    grupos = (("capturas", lambda e: e.startswith("TIM")),
              ("SAI (boca+oidos)", lambda e: e.startswith("SAI")),
              ("CV", lambda e: e.startswith("CV")),
              ("J2", lambda e: e.startswith("J2")),
              ("codec", lambda e: e.startswith("CODEC")),
              ("RGMII", lambda e: e.startswith("ETH")),
              ("ADC", lambda e: e.startswith("ADC")))
    for titulo, filtro in grupos:
        pares = [f"{e}={p}" for e, p in sorted(reparto.items()) if filtro(e)]
        print(f"    {titulo:18s}: " + ", ".join(pares))

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
    # multicanal TDM que el spec S10 difiere). Informativo, no bloquea.
    crece = None
    for j2c in ("SPI4", "SPI5", "SPI6"):
        for i2cc in ("I2C1", "I2C2", "I2C3", "I2C4"):
            mesa_c = _demandas(len(N6_PAQUETES) - 1, "SAI1",
                               ("SPI1", "SPI2", "SPI3"), j2c, i2cc, True,
                               sai2_extra=True)
            if mesa_c is not None:
                crece = _asignar(mesa_c)
            if crece:
                break
        if crece:
            break
    print("\n  crecimiento (v1 + SAI2 entero, boca multicanal TDM) en "
          f"{N6_PAQUETES[-1]}: {'VERDE' if crece else 'ROJO'}")

    print("\n  la cuenta que ata el encapsulado a D9: PF14 es el UNICO pin")
    print("  del RXD0 del RGMII (y del RMII) y a la vez el suplente de")
    print("  TIM2_CH2 -- PA1 se lo lleva TIM5_CH2, y el tercer candidato")
    print("  (PC0) solo existe en VFBGA264. Ethernet en la Voz = VFBGA264;")
    print("  D9 = LVDS libera el paquete hasta el minimo de arriba.")

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
        "rechazo de la pantalla grande en cerebro S9.1")
    assert fb < H7_SRAM_B, "el framebuffer no cabe ni en el H750"

    # 6. El USB del cerebro: hoy es un controlador y un truco.
    assert RP_USB_NATIVO < 2 <= H7_USB_OTG, (
        "el reparto de controladores USB cambio: releer por que el host va "
        "por PIO en el cerebro")

    # 7. EL CENSO DE PINES DEL N657 (puerta 2 del sello, issue #213).
    _autocomprobacion_censo()
    paq, reparto, _escenario, minimo_sin_rgmii = demo_censo()

    # La asercion del issue #213: ningun pin con dos duenos.
    pines = list(reparto.values())
    assert len(pines) == len(set(pines)), "dos funciones piden el mismo pin"

    # Todo pin repartido existe en la variante elegida.
    ipaq = N6_PAQUETES.index(paq)
    for etiqueta, pin in reparto.items():
        assert N6_PINES[pin][0][ipaq] == "x", (
            f"{etiqueta} quedo en {pin}, que no existe en {paq}")

    # Tras el reparto y las reservas fijas quedan GPIO para lo vario
    # (R-M5 + crosspoint) -- y se exige holgura, no empate.
    libres = N6_GPIO_TOTAL[paq] - N6_RESERVA_GPIO - len(reparto)
    assert libres >= N6_GPIO_VARIOS + 4, (
        f"la variante {paq} deja {libres} GPIO libres; lo vario pide "
        f"{N6_GPIO_VARIOS} y sin holgura no se compra")

    # El resultado del censo, congelado como asercion INVERSA: si una nueva
    # revision del DS (o una edicion de la tabla) moviera estos veredictos,
    # este guion tiene que gritar y la compra se relee.
    assert paq == "VFBGA264", (
        f"el censo con RGMII ya no elige VFBGA264 (elige {paq}): releer la "
        "cuenta de PF14/TIM2_CH2 y el acoplamiento con D9")
    assert minimo_sin_rgmii == "VFBGA178", (
        f"el minimo sin RGMII cambio a {minimo_sin_rgmii}: releer la "
        "clausula de D9 en el issue #213")

    print("\n  VERDE: el censo cierra. Se levanta el bloqueo de compra "
          f"del issue #213 con la variante {paq}.")

    print("\nOK: presupuesto cerrado.")
    return 0


# ---------------------------------------------------------------------------
# LO QUE ESTE CALCULO **NO** CUBRE
#
#   * EL REPARTO DE PINES DEL CEREBRO. El de la Voz ya lo cierra el censo
#     del N657 de arriba (issue #213); el del cerebro (RP2350B: maquinas de
#     PIO + pines) sigue abierto y es la herencia real de `pines_budget.py`
#     (dieciseis S15) -- otra sesion lo trabaja en `pio_budget.py`.
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
