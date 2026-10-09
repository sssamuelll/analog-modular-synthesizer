#!/usr/bin/env python3
"""El riel de +5 V digital: quien lo gasta, y que le queda al arbitro del #104.

POR QUE EXISTE, y por que hasta hoy no podia escribirse.

La spec del cerebro S11 lo declara y S9.1 le pone el criterio: "power_budget.py
lo importa de la spec de la fuente en vez de transcribirlo". El issue #151 le
puso el criterio de cierre: "importa el tope del #104 de la fuente de verdad,
suma la cadena de LED, y falla con el host USB a su limite si no cabe".

Faltaba un numero para poder escribirlo: el consumo del puente inalambrico. El
issue #162 lo pedia "de su hoja, no estimado", y la pieza no estaba elegida. Ya
lo esta (sesion 2026-08-25) y la hoja esta leida: ver PUENTE_* abajo.

EL RESULTADO, y lo que la fuente v4 cambio de el (2026-09-03, Tarea 5).

La cuenta anterior concluyo que el #151 solo pedia arbitrar brillo cuando se
enchufara un host USB. Esa conclusion usaba como diseno una columna que no era
un tipico a 85 C y, ademas, el modelo de alimentacion equivocado. Contra el Max
publicado para SMPS interno, cuatro N657 mas el host EXCEDIAN el +5 V con las
cargas DURAS -- 2.895 A contra los 2.82 que daba la IRM-15-5 de la v3 --, el
arbitro no podia salvarlo ni apagando cada LED. El guion no llegaba a ROJO
--salia en HUECO, codigo 2, porque el punto de trabajo no esta publicado--
pero su veredicto reabria el presupuesto de la fuente.

Eso lo cierra la fuente v4, y por la via que el #151 pedia: PS6 pasa a ser una
IRM-45-5 de 8 A de placa y el techo DEJA DE SER UN LITERAL. Lo importa este
guion de calor_budget.py, que resuelve el punto fijo termico. Salen 19.4 -
21.1 W contra los 14.1 - 14.5 de antes, y con eso las duras caben en LOS DOS
extremos: el 7.4x de incertidumbre entre Typ y Max deja de voltear el
veredicto. Lo que sigue abierto no es si caben, es con cuanto margen -- y para
eso el punto de trabajo si manda, asi que la NPU y el Max a 85 C siguen siendo
HUECO y este guion sigue saliendo con codigo 2.

EL LAZO QUE ESTE IMPORT CIERRA, declarado porque nadie mas lo dice. En
calor_budget.py el cajon paga 14.475 W de digital, y esos 14.475 W son
2.895 A x 5 V: la fila "Max TJ = 125 C, 4 N657, host a tope" de este mismo
guion, en su columna de cargas DURAS. O sea carga -> calor -> aire ->
derating -> techo -> carga.

Y EL LAZO CAMBIO DE LADO EL 2026-09-05. Hasta ese dia el cajon cobraba
4.935 A --2.895 de duras MAS 2.04 de la cadena WS2812 que D1 retiro el
03-09-- y esos 4.94 quedaban POR ENCIMA del techo publicado (4.22 A): el
calor se cobraba de mas, el lazo cerraba con colchon, y el censo de aqui
podia crecer 2 A sin mover una sola celda de la fuente. Retirar la cadena era
lo correcto --era calor de una pieza que no se monta-- pero se llevo el
colchon con ella: hoy se cobra el censo exacto, 2.895 A, y el techo esta por
ENCIMA (3.89 pesimista, 4.22 optimista).

Lo que hay que vigilar desde entonces: el censo de este guion ya no tiene
delante ningun margen prestado. Cada miliamperio que suba aqui sube el calor
del cajon uno a uno, y CAJON_DIGITAL_A hay que moverlo en la misma tanda.
Antes bastaba mirar el techo; ahora se mira el censo.

LA CORRECCION CONTRA DS14791 REV 10, DICHA EN VOZ ALTA.

La reescritura anterior leyo mal las columnas: eran Typ seguido de Max a
25/85/105/125 C, no tipicos por temperatura. Los 0.2067 A que llamo "tipico a
85 C" eran el maximo a 25 C. Como esto es un presupuesto de fuente, mandan los
maximos publicados, no los tipicos.

Tambien uso las tablas equivocadas. Rev 10 trae cada medida pareada como
"SMPS external" y "SMPS internal". Este instrumento propone el conmutado
interno del chip, asi que aqui solo entran las cuatro tablas "SMPS internal".
Como referencia de la correccion, sin usarla en ninguna cuenta, la tabla
externa de IDDCORE (DS14791 Rev 10, Tabla 33, p. 148) da Typ 172 mA y Max
211/423/586/855 mA a 25/85/105/125 C.

Por ultimo, con SMPS interno ST publica IDDSMPS en la entrada de 1.8 V y esa
corriente YA INCLUYE el nucleo. No se suma IDDCORE y desaparece el rendimiento
estimado del DC/DC: ese HUECO nacia de un modelo que no corresponde. Las cuatro
tablas internas solo publican Typ y Max a TJ = 125 C. No hay Max a 85 C para
esta configuracion: eso queda como HUECO y no se interpola.

El camino D-R1 propuesto es +5 V --buck--> 3.3 V --LDO--> 1.8 V. El LDO no
escala corriente: lo que pide el riel de 1.8 V es lo que pide a 3.3 V; solo el
buck existente se refleja por potencia al +5 V.

LA CORRECCION AL CRITERIO DEL #162.

El #162 manda meter "el pico de corriente al transmitir" en este presupuesto.
Meterlo crudo hace fallar el guion por la razon equivocada: un pico de radio de
milisegundos NO lo paga la fuente. Son tres niveles con tres duenos:

  1. el transitorio (microsegundos)  -> el desacoplo local del modulo
  2. el pico sostenido de TX          -> el REGULADOR del 3V3, que tiene que
                                         poder entregarlo (aserto abajo)
  3. la media del peor caso musical   -> la fuente. Es lo unico que suma aqui.

Confundir el 2 con el 3 empuja a comprar vatios de fuente para un problema que
se resuelve con un condensador y un buck bien elegido.

ALCANCE: el riel de +5 V digital de PS6 -- una IRM-45-5 desde la fuente v4;
era la IRM-15-5 de la v3 --, el que la spec de la fuente le asigna a este
modulo y que S9.1 del cerebro acepta.

LO QUE NO CUBRE:
  - El lazo termico ya NO se ignora: lo resuelve calor_budget.py como punto
    fijo y este guion importa su resultado. Lo que sigue fuera es el VENTEO
    del que ese resultado depende: el techo importado supone los 22 200 mm2
    de abertura nueva que D-F3 = A le encarga al papel del case (#289) y que
    nadie ha dibujado todavia. Con la caja de hoy, cerrada, el aire pasa de
    los 85 C donde acaba la curva de la hoja y PS6 no opera.
  - Los +-12 V del peine, que tienen su propio presupuesto.
  - El J6 / 7805 heredado de la v1: es OTRO riel de 5 V, referenciado a GNDA
    (cerebro S9). No se mezcla aqui a proposito.
  - La transitoria de arranque (inrush) de PS6 y del host USB. La de los
    seis IRM la lleva fusible_budget.py de la v4, no este guion.
  - El consumo del STM32N657 con la NPU trabajando. DS14791 caracteriza el
    Run mode con CoreMark; mago e interfaz quieren usar la NPU y no hay una
    cifra publicada para sumarla. Es un HUECO, no se inventa aqui.
  - El maximo a 85 C con SMPS interno. Las tablas solo dan Typ y Max a 125 C;
    el punto de trabajo del instrumento sigue siendo un HUECO.
  - Nada esta medido. Son hojas y specs.
"""

from __future__ import annotations

import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_DIR, "..", "01-power-supply", "v4"))
from calor_budget import MODULO_A as _MODULO_FUENTE_A       # noqa: E402
from calor_budget import PLACA_A as _PLACA_FUENTE_A         # noqa: E402
from calor_budget import PSU3_A as _PSU3_FUENTE_A           # noqa: E402
from calor_budget import (P_BASE, SOSTENIDO,                # noqa: E402
                          SOSTENIDO_CD_PESIMISTA)

# --- El techo, IMPORTADO de la fuente de verdad (#151, criterio de cierre) ---
# HASTA EL 2026-09-03 ESTO ERAN DOS LITERALES: 14.1 y 14.5 W, leidos a ojo de
# la curva de derating de la IRM-15-5 "con el aire dentro a 52.3 C" (spec de
# la fuente S3.1, fila de 2.50 A). Esa fuente ya no existe -- la v4 pone una
# IRM-45-5 de 8 A de placa en PS6 -- y el criterio de cierre del #151 pedia
# justamente esto: "importa el tope de la fuente de verdad" en vez de
# transcribirlo. Ahora sale de calor_budget.py, que resuelve el punto fijo
# corriente -> calor -> aire -> derating -> corriente con la sala a 45 C.
#
# EL RANGO YA NO ES LA DIFERENCIA DE DOS LECTURAS OCULARES de una curva que no
# se leia limpia. Es la sensibilidad al COEFICIENTE DE DESCARGA del venteo
# (C_D 0.55 contra 0.65), que es la constante que mas manda del modelo termico
# y la unica sin medir. El case publica su propio salto termico con esos dos
# mismos extremos; aqui, como antes, manda la pesimista.
#
# Y AHORA LO INCOMODO, QUE UNA REVISION ADVERSARIAL SACO EL MISMO DIA: el
# extremo OPTIMISTA no mide lo que PS6 aguanta termicamente. P_BASE es, por
# construccion, el area MINIMA que hace pasar el liston, asi que el punto fijo
# aterriza siempre donde el +12 V de rack toca exactamente los 2,0 A de la
# A-100PSU3. Como el digital lee la MISMA curva IRM-45 y su tope de placa (8 A)
# no muerde ahi, el techo sale forzado a
#
#     MODULO_A["digital+5"] / MODULO_A["rack+12"] * PSU3_A["rack+12"] * V_RIEL
#     =  8,0 / 3,8 * 2,0 * 5,0  =  21,05 W
#
# pase lo que pase con el calor. Se midio: subir la sala de 45 a 60 C mueve el
# area minima un 5x y el techo un 0,2 %; cuatro repartos de calor distintos lo
# mueven 0,13 %. O sea que lo que llega aqui es EL LISTON DOEPFER reescrito en
# la moneda del digital, no una cifra de derating. Lo que SI lo mueve: MODULO_A
# (que modulo se compra), PSU3_A (contra que se mide el liston) y PLACA_A. El
# termico de verdad es el OTRO extremo, el pesimista: mismo venteo, peor C_D.
#
# LO QUE ESTE NUMERO ARRASTRA, y hay que decirlo en voz alta: sale del punto
# fijo evaluado en el VENTEO MINIMO que calor_budget despeja, o sea de una
# obra que el papel del case todavia no ha dibujado (D-F3 = A, issue #289).
# Con la caja de hoy, cerrada, no hay techo ninguno: el aire se va a 87.7 C,
# por encima de donde acaba la curva de la hoja, y PS6 no opera. Este guion es
# verde CON ESA OBRA HECHA, y lo imprime en cada corrida.
V_RIEL = 5.0                    # V. PS6 = IRM-45-5, 5 V / 8 A de placa
TECHO_W_PESIMISTA = SOSTENIDO_CD_PESIMISTA["digital+5"] * V_RIEL
TECHO_W_OPTIMISTA = SOSTENIDO["digital+5"] * V_RIEL
TECHO_VENTEO_MM2 = P_BASE["area_venteo_mm2"]

# --- Cargas DURAS: presencia o ausencia, no se atenuan ----------------------
# Los STM32N657 cuelgan del riel de 1.8 V propuesto por D-R1. Ese riel sale del
# 3V3 mediante LDO, asi que I_3V3 = I_1V8; el buck existente refleja despues la
# carga al +5 V. IDDSMPS ya incluye el nucleo: IDDCORE NO se suma aparte.
#
# Condicion de las cuatro tablas "SMPS internal": codigo desde ITCM con HSI,
# todos los perifericos habilitados, VOS high, 800 MHz. Solo dan Typ y Max a
# TJ = 125 C; no publican Max a 85 C. Ese punto es HUECO y no se interpola.
N657_IDDSMPS_TIP_A = 0.09993       # A. DS14791 Rev 10, Tabla 39, p. 154
N657_IDDSMPS_MAX_125_A = 0.7573    # A. DS14791 Rev 10, Tabla 39, p. 154
N657_IDDA1V8_TIP_A = 0.00267       # A. DS14791 Rev 10, Tabla 36, p. 151
N657_IDDA1V8_MAX_125_A = 0.00312   # A. DS14791 Rev 10, Tabla 36, p. 151
N657_IDDA1V8AON_TIP_A = 0.00045    # A. DS14791 Rev 10, Tabla 38, p. 153
N657_IDDA1V8AON_MAX_125_A = 0.00056  # A. DS14791 Rev 10, Tabla 38, p. 153
N657_IDD_TIP_A = 0.00027           # A. DS14791 Rev 10, Tabla 32, p. 147
N657_IDD_MAX_125_A = 0.00040       # A. DS14791 Rev 10, Tabla 32, p. 147

# Un presupuesto de fuente se calcula contra Max. Typ se conserva y se imprime
# como referencia; no se presenta como una cota a ninguna temperatura.
# TRES estan decididos -- hub (D1), Voz (sellada el 26-08) y mago (D3') -- y el
# CUARTO, la interfaz de audio, es PROPUESTA SIN FIRMAR (D-A1, papel de la
# interfaz 2026-08-31). Se modela en 4 a proposito: si el presupuesto solo
# cerrara con 3, la firma de D-A1 se decidiria contra un numero que nadie
# habria corrido. La demo imprime los dos casos para que se vea el precio.
N657_CANTIDAD = 4

# Host USB: interruptor de carga a 500 mA (cerebro S6.2). El #151: "es
# presencia o ausencia y no se atenua".
HOST_USB_A = 0.500

# --- El puente inalambrico. HOJA LEIDA (sesion 2026-08-25) ------------------
# ESP32-S3-WROOM-1U, datasheet v1.8.
#   Tabla 6-4 p.28: Wi-Fi TX pico 355 mA (802.11b 1 Mbps @20.5 dBm), RX 95 mA.
#   Tabla 6-5 p.28: BLE TX pico 344 mA @20 dBm, RX 93 mA.
#   Medido a 3.3 V, 25 C, "TX current consumption is rated at a 100% duty
#   cycle" -- de ahi que el pico NO sea la carga de la fuente.
PUENTE_V = 3.3
PUENTE_TX_PICO_A = 0.355
PUENTE_RX_A = 0.095
# DECLARADO, no medido: fraccion del tiempo que el puente TRANSMITE en el peor
# caso musical (sirviendo la UI web + punto de acceso + Link a la vez). Los
# beacons de un AP son ~1-2 ms cada 100 ms; el trafico de UI va a rafagas al
# cargar la app y luego son parametros sueltos; Link son paquetes cortos.
# El 10% es una cota generosa: sube TREINTA veces el trafico de beacon.
PUENTE_TX_DUTY = 0.10
# El resto del tiempo el radio esta escuchando, no dormido: en modo AP tiene
# que oir a quien se asocie. Se cuenta RX continuo, que es conservador.

# --- Cargas ATENUABLES: el arbitro del #104 las puede bajar ------------------
# La retroiluminacion se deja EXPLICITA y clavada a cero en vez de borrada,
# por la regla de mutacion de la constitucion: la constante y su asercion hacen
# que restaurar los 80 mA de la pantalla derogada falle de frente, sin depender
# de que otra desigualdad del presupuesto lo detecte por accidente.
BACKLIGHT_A = 0.0

# RETIRADA 2026-08-27: se eliminaron los 0-80 mA de retroiluminacion de la
# pantalla SPI de 2,8" porque sec.7 del cerebro la deroga. La pantalla de 7" NO
# se agrega aqui: lleva regulador local desde +12 V y retorno dedicado.
#
# RETIRADA 2026-09-03: la cadena WS2812 entera, y con ella el arbitro del #104.
# Eran 160 LEDs (100 de panel + 60 del farol del #42) a 60 mA: 9.60 A a blanco
# pleno, 2.04 A en el caso real, 2.50 A de tope de arbitraje vigente. Fuente:
# docs/superpowers/specs/2026-09-03-instrumento-entero-design.md D1.
#
# Aqui NO se aplica la regla de "a cero con asercion" que sostiene BACKLIGHT_A
# doce lineas mas arriba, y conviene decir por que, porque parece la misma
# situacion y no lo es. Esa regla guarda una carga derogada de un riel que
# SIGUE teniendo arbitro. Las tres constantes de la cadena tenian tres asertos
# que exigian lo CONTRARIO -- que el conflicto siguiera existiendo -- y el de
# LED_A_CASO_REAL dejaba escrita la instruccion: "Si esto es verdad, el #104 se
# puede cerrar, pero revisa que numero cambio antes de creertelo". Puestos a
# cero, dos de esos asertos revientan y el tercero pasa trivialmente, o sea que
# la puerta dejaria de morder sin avisar. Lo que murio no es la carga: es el
# arbitro. Un aserto se retira nombrando a su sujeto, no se relaja.
#
# De luz solo sobreviven las 4 coronas de los MACROS (spec D7), que no son
# cadena y todavia no tienen pieza ni cifra. Cuando #297 elija driver vuelven
# aqui como carga nueva, con su hoja.

# --- El regulador del 3V3 ---------------------------------------------------
# Decision de Samuel (2026-08-25): conmutado, no lineal. Con LDO la corriente
# de entrada es la de salida y el puente costaria PUENTE_TX_PICO_A * 5 V; con
# buck cuesta la potencia, no la corriente.
BUCK_EFICIENCIA = 0.90         # DECLARADO. Conservador para un buck de 3.3 V
                               # a esta corriente; el real se cita al elegirlo.
# Todo lo demas que cuelga del 3V3 y que no es el puente ni los N657: mux I2C,
# buffers y aislador. Los N657 se cuentan aparte para distinguir Typ de Max.
# DECLARADO como cota, POR_CONFIRMAR al cerrar el BOM.
OTROS_3V3_A = 0.100


def carga_puente_media_a() -> float:
    """Corriente MEDIA del puente en su lado de 3.3 V, peor caso musical."""
    return PUENTE_TX_DUTY * PUENTE_TX_PICO_A + (1 - PUENTE_TX_DUTY) * PUENTE_RX_A


def desde_3v3(corriente_3v3_a: float) -> float:
    """Lo que una carga de 3.3 V le cuesta al riel de +5 V, con buck."""
    return corriente_3v3_a * PUENTE_V / (BUCK_EFICIENCIA * V_RIEL)


def corriente_n657_1v8_a(*, maximo_125: bool) -> float:
    """Corriente de un N657 en el riel de 1.8 V, Typ o Max a 125 C."""
    if maximo_125:
        return (
            N657_IDDSMPS_MAX_125_A
            + N657_IDDA1V8_MAX_125_A
            + N657_IDDA1V8AON_MAX_125_A
            + N657_IDD_MAX_125_A
        )
    return (
        N657_IDDSMPS_TIP_A
        + N657_IDDA1V8_TIP_A
        + N657_IDDA1V8AON_TIP_A
        + N657_IDD_TIP_A
    )


def n657_al_5v_a(
    cantidad_n657: int = N657_CANTIDAD,
    *,
    maximo_125: bool = True,
) -> float:
    """Corriente que los N657 reflejan al +5 V por LDO y buck existentes."""
    corriente_1v8_a = cantidad_n657 * corriente_n657_1v8_a(
        maximo_125=maximo_125,
    )
    # D-R1 propuesto: el LDO conserva corriente, I_3V3 = I_1V8.
    return desde_3v3(corriente_1v8_a)


def duras_a(
    host_usb: bool,
    cantidad_n657: int = N657_CANTIDAD,
    *,
    maximo_125: bool = True,
) -> float:
    """Suma de las cargas que el arbitro NO puede tocar, en A del riel."""
    a = n657_al_5v_a(cantidad_n657, maximo_125=maximo_125)
    a += desde_3v3(carga_puente_media_a() + OTROS_3V3_A)
    if host_usb:
        a += HOST_USB_A
    return a


def sobra_para_atenuables(
    host_usb: bool,
    techo_w: float,
    cantidad_n657: int = N657_CANTIDAD,
    *,
    maximo_125: bool = True,
) -> float:
    """Lo que queda para el arbitro despues de pagar lo duro, en A."""
    return techo_w / V_RIEL - duras_a(
        host_usb,
        cantidad_n657,
        maximo_125=maximo_125,
    )


# arbitro() vivio aqui hasta el 2026-09-03. Su comentario avisaba de que
# "borrar la funcion seria borrar el nombre del arbitro", y eso es exactamente
# lo que decide D1 del papel del instrumento entero: sin cadena y sin farol, el
# #104 se queda sin los dos consumidores que se repartian el riel, y no hay
# nada que arbitrar. sobra_para_atenuables() se queda porque sigue diciendo
# algo verdadero: cuanta holgura tiene el riel despues de las cargas duras.


def pico_3v3_a() -> float:
    """Pico que el REGULADOR del 3V3 tiene que poder entregar (no la fuente)."""
    return PUENTE_TX_PICO_A + OTROS_3V3_A


CASOS = (
    # (nombre, host_usb). La tercera columna era la carga de cadena que se
    # pretendia; murio con la cadena (2026-09-03). Lo que queda es la holgura
    # del riel, que sigue siendo la cifra que decide si la fuente cabe.
    ("solo",                         False),
    ("con controlador USB a tope",   True),
)


def demo() -> None:
    print("El riel de +5 V digital del SAM17")
    print()
    print(f"  techo IMPORTADO de calor_budget  {TECHO_W_PESIMISTA:.1f} - "
          f"{TECHO_W_OPTIMISTA:.1f} W   ({TECHO_W_PESIMISTA/V_RIEL:.2f} - "
          f"{TECHO_W_OPTIMISTA/V_RIEL:.2f} A)")
    print(f"    punto fijo termico de PS6 con la sala a 45 C y "
          f"{TECHO_VENTEO_MM2:.0f} mm2 de venteo nuevo (D-F3 = A, #289);")
    print("    el rango es C_D 0.55 - 0.65. SIN ese venteo no hay techo: el "
          "aire pasa de 85 C y PS6 no opera")
    print("  IMPORTADO de la spec de la fuente S3.1, fila de 2.50 A")
    print()

    print("los STM32N657 (DS14791 Rev 10; SMPS internal; Run/CoreMark):")
    print("  simbolo       tabla pagina       Typ  Max TJ=125 C    riel")
    print(f"  IDDSMPS          39   154   {N657_IDDSMPS_TIP_A*1000:8.2f} mA"
          f" {N657_IDDSMPS_MAX_125_A*1000:10.2f} mA   1.8 V")
    print(f"  IDDA1V8          36   151   {N657_IDDA1V8_TIP_A*1000:8.2f} mA"
          f" {N657_IDDA1V8_MAX_125_A*1000:10.2f} mA   1.8 V")
    print(f"  IDDA1V8AON       38   153   {N657_IDDA1V8AON_TIP_A*1000:8.2f} mA"
          f" {N657_IDDA1V8AON_MAX_125_A*1000:10.2f} mA   1.8 V")
    print(f"  IDD              32   147   {N657_IDD_TIP_A*1000:8.2f} mA"
          f" {N657_IDD_MAX_125_A*1000:10.2f} mA   1.8 V")
    print("  IDDSMPS incluye el nucleo: IDDCORE no se suma.")
    print("  Las tablas no publican Max a 85 C; no se interpola.")
    print("  Camino D-R1 PROPUESTO: +5 V --buck--> 3.3 V --LDO--> 1.8 V;")
    print("  el LDO conserva corriente y el buck usa su 90% declarado.")
    for nombre, maximo_125 in (("Typ", False), ("Max TJ=125 C", True)):
        corriente_por_chip = corriente_n657_1v8_a(maximo_125=maximo_125)
        for cantidad in (1, N657_CANTIDAD):
            corriente_1v8 = cantidad * corriente_por_chip
            corriente_5v = n657_al_5v_a(
                cantidad,
                maximo_125=maximo_125,
            )
            print(f"  {nombre:<12} {cantidad} N657: 1.8 V "
                  f"{corriente_1v8*1000:7.2f} mA; +5 V "
                  f"{corriente_5v*1000:8.3f} mA")
    print()

    med = carga_puente_media_a()
    print("el puente inalambrico (ESP32-S3-WROOM-1U, hoja v1.8):")
    print(f"  TX pico            {PUENTE_TX_PICO_A*1000:5.0f} mA a 3.3 V   "
          f"(Tabla 6-4, al 100% de ciclo)")
    print(f"  RX                 {PUENTE_RX_A*1000:5.0f} mA a 3.3 V")
    print(f"  media declarada    {med*1000:5.0f} mA a 3.3 V   "
          f"({PUENTE_TX_DUTY:.0%} de TX + RX continuo)")
    print(f"  cuesta al +5 V     {desde_3v3(med)*1000:5.0f} mA   "
          f"(buck al {BUCK_EFICIENCIA:.0%}); con LDO serian "
          f"{med*1000:.0f} mA")
    print()

    print(f"holgura del riel con {N657_CANTIDAD} STM32N657, "
          "Max TJ=125 C (techo pesimista):")
    print()
    print(f"  {'caso':<30} {'duras':>7} {'sobra':>7}  veredicto")
    for nombre, host in CASOS:
        d = duras_a(host)
        s = sobra_para_atenuables(host, TECHO_W_PESIMISTA)
        if d > TECHO_W_PESIMISTA / V_RIEL:
            ok = f"ROJO: DURAS +{(d-TECHO_W_PESIMISTA/V_RIEL)*1000:.0f} mA"
        else:
            ok = "cabe"
        print(f"  {nombre:<30} {d:6.2f}A {s:6.2f}A  {ok}")
    print()

    print("el pico NO es carga de la fuente:")
    print(f"  el regulador del 3V3 tiene que dar   "
          f"{pico_3v3_a()*1000:.0f} mA de pico")
    print(f"  la fuente solo ve la media           "
          f"{desde_3v3(med + OTROS_3V3_A)*1000:.0f} mA")
    print("  y el transitorio lo cubre el desacoplo local del modulo")
    print()

    print("VEREDICTO")
    print(f"  El techo pesimista son {TECHO_W_PESIMISTA/V_RIEL:.2f} A del +5 V.")
    print("  Caso comprobado: host USB a tope, ya sin cadena de LED.")
    for nombre, maximo_125 in (("Typ", False), ("Max TJ=125 C", True)):
        for cantidad in (1, N657_CANTIDAD):
            duras_host = duras_a(
                True,
                cantidad,
                maximo_125=maximo_125,
            )
            margen = TECHO_W_PESIMISTA / V_RIEL - duras_host
            if margen < 0:
                resultado = f"ROJO: duras exceden {-margen*1000:.0f} mA"
            else:
                resultado = f"CABE, sobran {margen*1000:.0f} mA"
            print(f"  {nombre:<12} {cantidad} N657: duras {duras_host:.3f} A "
                  f"-- {resultado}")
    print("  El presupuesto se decide con Max TJ=125 C. Hasta la fuente v3 ahi")
    print("  las cargas duras SOLAS excedian el +5 V -- 2.895 A contra los")
    print("  2.82 de la IRM-15-5 --, y el guion quedaba ROJO. Con PS6 =")
    print("  IRM-45-5 caben en LOS DOS extremos, asi que el 7.4x de")
    print("  incertidumbre entre Typ y Max deja de voltear el veredicto de")
    print("  las duras. La NPU sigue fuera: no hay cifra para extenderlo.")
    print()
    print("  La cadena de LED se retiro el 2026-09-03 (spec del instrumento")
    print("  entero, D1) y con ella el arbitro del #104: se fueron sus 9.60 A")
    print("  de blanco pleno, los 2.04 A del caso real y el farol del #42.")
    print("  Lo que el riel gana con eso NO reabre la fuente: el techo que")
    print(f"  manda es termico ({TECHO_W_OPTIMISTA/V_RIEL:.1f} A / "
          f"{TECHO_W_OPTIMISTA:.0f} W, importados de calor_budget), no de")
    print("  cadena. Esa frase estaba escrita a mano ese mismo dia; desde hoy")
    print("  el numero lo pone el guion de la fuente.")
    print()
    print("Esto NO es una prueba: es una puerta. La medida que la cierra es la")
    print("corriente real del riel con el sensor de S9.1, contra lo que este")
    print("guion estima.")
    print()
    print("HUECO: las tablas SMPS internal dan Typ y Max a TJ=125 C, pero no")
    print("  publican Max a 85 C. No se interpola ese punto.")
    print("HUECO: DS14791 caracteriza estas medidas con CoreMark, no con la NPU")
    print("  trabajando. No hay cifra para la carga NPU que quieren mago e "
          "interfaz.")


def _autocomprobacion() -> None:
    """Un caso a mano, para que el guion no se crea sus propias funciones."""
    # media del puente: 0.10*355 + 0.90*95 = 35.5 + 85.5 = 121 mA
    med = carga_puente_media_a()
    assert abs(med - 0.121) < 1e-6, med
    # al +5 V con buck al 90%: 121 mA * 3.3 / (0.9*5) = 88.7 mA
    assert abs(desde_3v3(med) - 0.0887333) < 1e-6, desde_3v3(med)
    # N657, riel de 1.8 V: las sumas literales de las cuatro tablas internas.
    assert abs(corriente_n657_1v8_a(maximo_125=False) - 0.10332) < 1e-9
    assert abs(corriente_n657_1v8_a(maximo_125=True) - 0.76138) < 1e-9
    # El LDO conserva corriente; el buck refleja 3.3 V / (0.90 * 5 V).
    assert abs(n657_al_5v_a(1, maximo_125=False) - 0.075768) < 1e-9
    assert abs(n657_al_5v_a(1, maximo_125=True) - 0.5583453333333333) < 1e-9
    # La parametrizacion tiene que escalar la misma carga, no esconder otro
    # consumo fijo por cada N657. El presupuesto usa maximo por defecto.
    assert abs(n657_al_5v_a(4, maximo_125=False) - 0.303072) < 1e-9
    assert abs(n657_al_5v_a(4) - 2.2333813333333333) < 1e-9
    assert abs(duras_a(True) - 2.895448) < 1e-9
    # EL TECHO IMPORTADO, POR LOS DOS LADOS. Por abajo: la IRM-15-5 de la v3
    # ya daba 14.1 W con MENOS modulo, asi que menos que eso significa que
    # alguien encogio lo declarado o cambio de pieza. Por arriba: no puede
    # pasar de la placa de PS6, que son 40 W.
    #
    # OJO CON LO QUE ESTOS DOS ASERTOS *NO* VIGILAN, medido y no supuesto: el
    # techo es el liston de la PSU3 reescrito (ver la nota de arriba), asi que
    # NINGUNA constante termica lo mueve lo bastante para dispararlos --sala a
    # 60 C lo deja en 20.15 W, h_conv a 2 en 19.34, el calor del digital x3 en
    # 19.29--. Lo unico que los dispara es tocar lo DECLARADO: bajar
    # PLACA_A["digital+5"] a 2.5 A da 6.1 W y salta. Son guardas del contrato
    # con la fuente, no un termometro.
    tope_placa_w = _PLACA_FUENTE_A["digital+5"] * V_RIEL
    assert 14.1 < TECHO_W_PESIMISTA <= tope_placa_w, (
        f"el techo del +5 V digital sale {TECHO_W_PESIMISTA:.1f} W. Por abajo "
        f"la IRM-15-5 de la v3 ya daba 14.1 con menos modulo; por arriba la "
        f"placa de PS6 son {tope_placa_w:.0f} W y nadie puede prometer mas. "
        f"Mira MODULO_A, PSU3_A y PLACA_A de calor_budget antes que el modelo "
        f"termico: son ellos los que mueven este numero")
    assert TECHO_W_PESIMISTA < TECHO_W_OPTIMISTA <= tope_placa_w, (
        f"el rango del techo esta al reves o se sale: {TECHO_W_PESIMISTA:.2f} "
        f"W con C_D pesimista contra {TECHO_W_OPTIMISTA:.2f} con el nominal")
    # Y LA IDENTIDAD QUE DE VERDAD DESCRIBE EL OPTIMISTA, para que se vea que
    # es aritmetica del liston y no una casualidad del punto fijo.
    pinado_w = (_MODULO_FUENTE_A["digital+5"] / _MODULO_FUENTE_A["rack+12"]
                * _PSU3_FUENTE_A["rack+12"] * V_RIEL)
    assert abs(TECHO_W_OPTIMISTA - pinado_w) < 0.05, (
        f"el techo optimista son {TECHO_W_OPTIMISTA:.3f} W y el liston "
        f"reescrito da {pinado_w:.3f}: si estos dos se separan es que en el "
        f"area minima ya no manda el +12 V de rack, y entonces el techo SI "
        f"pasa a ser termico. Buena noticia, pero hay que releer la nota")


def main() -> int:
    _autocomprobacion()
    demo()

    # --- Las puertas ---------------------------------------------------------

    # 1. El criterio de cierre del #151, al derecho: las cargas DURAS con el
    #    host USB a su limite tienen que caber en el techo pesimista.
    #
    #    ESTE ASERTO NO PUEDE EMITIRSE HOY, y decir por que es mas util que
    #    pintarlo de rojo o de verde. La puerta necesita el consumo en el
    #    PUNTO DE TRABAJO del instrumento, y para SMPS interno DS14791 Rev 10
    #    no lo publica: sus cuatro tablas dan Typ y Max a TJ = 125 C, y nada
    #    en medio. Entre los dos extremos hay 7.4x.
    #
    #    Con Max a 125 C las duras NO caben -- pero ese caso supone los cuatro
    #    chips a temperatura de UNION maxima a la vez, y si eso pasara el
    #    instrumento tiene un problema termico mucho antes que electrico.
    #    Afirmar "no cabe" con ese numero seria afirmar mas de lo que sabemos.
    #    Con Typ si cabe, pero un tipico no es cota de nada.
    #
    #    Asi que se imprime el veredicto de los dos extremos y se declara
    #    HUECO. Cuando ST publique el Max a 85 C (o se mida en la Discovery,
    #    #231), este aserto se ARMA contra ese numero y decide de verdad.
    d_tip = duras_a(True, maximo_125=False)
    d_max = duras_a(True, maximo_125=True)
    techo = TECHO_W_PESIMISTA / V_RIEL
    print()
    print("LA PUERTA DEL #151 NO SE PUEDE CERRAR HOY:")
    print(f"  duras + host, Typ         {d_tip:.3f} A  contra techo {techo:.2f} A"
          f"  -> {'cabe' if d_tip < techo else 'NO CABE'}")
    print(f"  duras + host, Max 125 C   {d_max:.3f} A  contra techo {techo:.2f} A"
          f"  -> {'cabe' if d_max < techo else 'NO CABE'}")
    print("  el punto de trabajo (Max a 85 C) NO ESTA PUBLICADO para SMPS")
    print("  interno. Con la fuente v3 eso decidia el veredicto, porque los")
    print("  dos extremos caian a lados distintos del techo. Con PS6 caben")
    print("  los dos, asi que lo que sigue abierto NO es si las duras caben:")
    print("  es con cuanto margen, y para eso el punto de trabajo si manda.")
    assert d_tip < techo, (
        f"ni siquiera en el tipico caben las duras con el host: {d_tip:.2f} A "
        f"contra {techo:.2f} A. Eso SI seria pedir otra fuente, sin discusion.")

    # 2. Y la otra mitad del mismo criterio: con el host enchufado, el caso de
    #    brillo real NO cabe sin arbitrar. Este aserto es al reves -- exige que
    #    el conflicto siga existiendo, porque el dia que deje de existir es que
    #    alguien movio un numero y el arbitro se quedo sin razon de ser.
    assert BACKLIGHT_A == 0.0, (
        f"BACKLIGHT_A vale {BACKLIGHT_A*1000:.0f} mA y la pantalla de 2,8 que "
        f"la pedia esta derogada (spec del cerebro sec.7). La de 7 pulgadas NO "
        f"carga este riel: lleva regulador local desde +12 V con retorno "
        f"dedicado (pantalla-motor sec.6)")
    # Los dos asertos que aqui vigilaban a la cadena -- que al arbitro le
    # faltara corriente con el host a tope, y que le sobrara sin el -- se
    # retiraron el 2026-09-03 con su sujeto. El primero dejaba escrita su
    # propia instruccion de salida: "si esto es verdad, el #104 se puede
    # cerrar, pero revisa que numero cambio antes de creertelo". Revisado: el
    # numero que cambio no fue ninguno de los suyos ni el techo del riel, fue
    # que la cadena dejo de existir (spec del instrumento entero, D1). El #104
    # se cierra por eso, no porque el riel diera mas de si.

    # 3. La correccion al #162: el pico del puente es problema del REGULADOR
    #    del 3V3, no de la fuente. Se asevera que el pico cabe holgado en lo
    #    que un buck de 3.3 V de catalogo entrega (1 A es el escalon comun),
    #    para que nadie lo meta en el presupuesto de la fuente.
    assert pico_3v3_a() < 1.0, (
        f"el pico del 3V3 son {pico_3v3_a()*1000:.0f} mA y ya no cabe en un "
        f"buck de 1 A: hay que elegir el regulador a proposito y decirlo en la "
        f"spec, no heredarlo.")

    # 4. El aserto de "blanco pleno no cabe ni sonando el instrumento solo" se
    #    retiro el 2026-09-03: sus 9.60 A eran el conteo de una cadena que ya
    #    no existe. Guardaba la razon de que el tope de brillo existiera, y el
    #    tope se fue con el arbitro. NO se reescribe contra las 4 coronas de
    #    MACRO que sobreviven (spec D7) hasta que #297 elija pieza y traiga su
    #    hoja: un aserto sin cifra de hoja es un comentario con sintaxis.

    # Codigo 2: los HUECO impresos por demo() son trabajo a medias, no un
    # verde. gates.py los cuenta sin convertirlos en un FALLO electrico.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
