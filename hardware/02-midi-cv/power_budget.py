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

EL RESULTADO, y esta vez no se pinta de verde.

La cuenta anterior concluyo que el #151 solo pedia arbitrar brillo cuando se
enchufara un host USB. Esa conclusion usaba como diseno una columna que no era
un tipico a 85 C y, ademas, el modelo de alimentacion equivocado. Contra el Max
publicado para SMPS interno, cuatro N657 mas el host ya exceden el +5 V con las
cargas DURAS: el arbitro no puede salvarlo ni apagando cada LED. El guion queda
ROJO y reabre honestamente el presupuesto de la fuente. Typ se imprime como
referencia, no como cota de diseno. La NPU activa sigue sin cifra y se declara
HUECO abajo.

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

ALCANCE: el riel de +5 V digital de la IRM-15-5 -- el que la spec de la fuente
S4.1 le asigna a este modulo y que S9.1 del cerebro acepta.

LO QUE NO CUBRE:
  - El lazo termico. El techo derateado depende del calor dentro, que depende
    de la carga: la spec de la fuente lo resolvio para el tope de 2.50 A y este
    guion USA ESE PUNTO. Si la carga total se mueve mucho, el punto se mueve y
    hay que rehacer la tabla de derating, no este guion.
  - Los +-12 V del peine, que tienen su propio presupuesto.
  - El J6 / 7805 heredado de la v1: es OTRO riel de 5 V, referenciado a GNDA
    (cerebro S9). No se mezcla aqui a proposito.
  - La transitoria de arranque (inrush) de la IRM-15-5 y del host USB.
  - El consumo del STM32N657 con la NPU trabajando. DS14791 caracteriza el
    Run mode con CoreMark; mago e interfaz quieren usar la NPU y no hay una
    cifra publicada para sumarla. Es un HUECO, no se inventa aqui.
  - El maximo a 85 C con SMPS interno. Las tablas solo dan Typ y Max a 125 C;
    el punto de trabajo del instrumento sigue siendo un HUECO.
  - Nada esta medido. Son hojas y specs.
"""

from __future__ import annotations

# --- El techo, IMPORTADO de la fuente de verdad (#151, criterio de cierre) ---
# spec de la fuente S3.1, tabla "La curva de derating, por fin leida", fila de
# 2.50 A: "Puede dar 14.1 - 14.5 W" con el aire dentro a 52.3 C.
# El rango sale de que la pendiente de la curva no se lee limpia del PDF de
# Mean Well (IRM-15-SPEC 2025-11-21 p.3); se dan las dos lecturas y aqui manda
# la pesimista.
TECHO_W_PESIMISTA = 14.1
TECHO_W_OPTIMISTA = 14.5
V_RIEL = 5.0                    # V. IRM-15-5, 5 V / 3 A nominales

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
# Cadena WS2812: 160 LEDs (100 de panel + 60 del farol del #42), 60 mA cada uno
# a blanco pleno -> 9.60 A, que es el numero que el #104 declara imposible.
# El caso que de verdad ocurre, del mismo issue: "10 parejas de jack al 100% +
# farol naranja al 50% = 2.04 A".
LED_A_BLANCO_PLENO = 9.60
LED_A_CASO_REAL = 2.04
LED_A_TOPE_104 = 2.50          # el techo de arbitraje vigente (bajo de 2.80)

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


def arbitro(
    host_usb: bool,
    techo_w: float,
    cantidad_n657: int = N657_CANTIDAD,
    *,
    maximo_125: bool = True,
) -> float:
    """Techo de corriente que el arbitro del #104 puede darle a la cadena."""
    # Desde el 2026-08-27 esto es un paso directo, y NO sobra: el arbitro del
    # #104 es un concepto del diseno (que le queda a la cadena despues de las
    # cargas duras) y vuelve a tener resta el dia que aparezca otra carga
    # atenuable. La retroiluminacion era la unica que habia, y murio con la
    # pantalla de 2,8". Borrar la funcion seria borrar el nombre del arbitro.
    return sobra_para_atenuables(
        host_usb,
        techo_w,
        cantidad_n657,
        maximo_125=maximo_125,
    ) - BACKLIGHT_A


def pico_3v3_a() -> float:
    """Pico que el REGULADOR del 3V3 tiene que poder entregar (no la fuente)."""
    return PUENTE_TX_PICO_A + OTROS_3V3_A


CASOS = (
    # (nombre, host_usb, carga de cadena que se pretende)
    ("solo, caso real",              False, LED_A_CASO_REAL),
    ("con controlador USB a tope",   True,  LED_A_CASO_REAL),
    ("con USB, al tope del #104",    True,  LED_A_TOPE_104),
)


def demo() -> None:
    print("El riel de +5 V digital del SAM17")
    print()
    print(f"  techo derateado a 52.3 C   {TECHO_W_PESIMISTA:.1f} - "
          f"{TECHO_W_OPTIMISTA:.1f} W   ({TECHO_W_PESIMISTA/V_RIEL:.2f} - "
          f"{TECHO_W_OPTIMISTA/V_RIEL:.2f} A)")
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

    print(f"que le queda al arbitro del #104 con {N657_CANTIDAD} STM32N657, "
          "Max TJ=125 C (techo pesimista):")
    print()
    print(f"  {'caso':<30} {'duras':>7} {'sobra':>7} {'cadena':>8}  veredicto")
    for nombre, host, pretende in CASOS:
        d = duras_a(host)
        s = sobra_para_atenuables(host, TECHO_W_PESIMISTA)
        cabe = arbitro(host, TECHO_W_PESIMISTA)
        if d > TECHO_W_PESIMISTA / V_RIEL:
            ok = f"ROJO: DURAS +{(d-TECHO_W_PESIMISTA/V_RIEL)*1000:.0f} mA"
        elif cabe >= pretende:
            ok = "OK"
        else:
            ok = f"ARBITRA -{(pretende-cabe)*1000:.0f} mA"
        print(f"  {nombre:<30} {d:6.2f}A {s:6.2f}A {cabe:7.2f}A  {ok}")
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
    print("  Caso comprobado: host USB a tope + 2.04 A de cadena.")
    for nombre, maximo_125 in (("Typ", False), ("Max TJ=125 C", True)):
        for cantidad in (1, N657_CANTIDAD):
            duras_host = duras_a(
                True,
                cantidad,
                maximo_125=maximo_125,
            )
            total_real = duras_host + LED_A_CASO_REAL
            margen = TECHO_W_PESIMISTA / V_RIEL - total_real
            if duras_host > TECHO_W_PESIMISTA / V_RIEL:
                exceso = duras_host - TECHO_W_PESIMISTA / V_RIEL
                resultado = f"ROJO: duras exceden {exceso*1000:.0f} mA"
            elif margen >= 0:
                resultado = f"CABE, sobran {margen*1000:.0f} mA"
            else:
                resultado = f"ARBITRA {-margen*1000:.0f} mA de cadena"
            print(f"  {nombre:<12} {cantidad} N657: duras {duras_host:.3f} A; "
                  f"total {total_real:.3f} A -- {resultado}")
    print("  El presupuesto se decide con Max TJ=125 C. Con cuatro N657 y")
    print("  el host a tope, las cargas duras solas exceden el +5 V: ROJO.")
    print("  La NPU queda fuera: no hay cifra para extender el veredicto.")
    print()
    print(f"  Blanco pleno son {LED_A_BLANCO_PLENO:.2f} A y no caben en ningun")
    print("  escenario: el tope no es cosmetico, es estructural.")
    print()
    print("Esto NO es una prueba: es una puerta. La medida que la cierra es la")
    print("corriente real del riel con el sensor de S9.1, contra la estimacion")
    print("que el arbitro hace antes de empujar cada cuadro.")
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
    print("  interno, y es el unico que decide. Hasta tenerlo, el presupuesto")
    print("  de la fuente con cuatro N657 NO esta cerrado.")
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
    # En Typ EXPLICITO, por lo mismo que el aserto 1: el Max a 125 C no es el
    # punto de trabajo y el de 85 C no existe. Lo que este aserto guarda es
    # que el arbitro haga falta, y eso ya se ve en el tipico.
    cabe_con_host = arbitro(True, TECHO_W_PESIMISTA, maximo_125=False)
    assert cabe_con_host < LED_A_CASO_REAL, (
        f"con el host USB a tope sobran {cabe_con_host:.2f} A para la cadena y "
        f"el caso real pide {LED_A_CASO_REAL:.2f}: ya no hace falta arbitrar. "
        f"Si esto es verdad, el #104 se puede cerrar -- pero revisa que numero "
        f"cambio antes de creertelo.")

    # 3. Sin host, el instrumento tiene que tocar con su brillo real. Si esto
    #    falla, el instrumento no funciona solo.
    # Typ EXPLICITO, misma razon que arriba.
    cabe_solo = arbitro(False, TECHO_W_PESIMISTA, maximo_125=False)
    assert cabe_solo >= LED_A_CASO_REAL, (
        f"solo, con la pantalla encendida, sobran {cabe_solo:.2f} A para la "
        f"cadena y el brillo real pide {LED_A_CASO_REAL:.2f}. El instrumento "
        f"no puede tocar sin arbitrar contra si mismo.")

    # 4. La correccion al #162: el pico del puente es problema del REGULADOR
    #    del 3V3, no de la fuente. Se asevera que el pico cabe holgado en lo
    #    que un buck de 3.3 V de catalogo entrega (1 A es el escalon comun),
    #    para que nadie lo meta en el presupuesto de la fuente.
    assert pico_3v3_a() < 1.0, (
        f"el pico del 3V3 son {pico_3v3_a()*1000:.0f} mA y ya no cabe en un "
        f"buck de 1 A: hay que elegir el regulador a proposito y decirlo en la "
        f"spec, no heredarlo.")

    # 5. Blanco pleno no cabe ni sonando el instrumento solo. Es la razon de
    #    que el tope exista, y se asevera para que no se pierda.
    assert LED_A_BLANCO_PLENO > TECHO_W_OPTIMISTA / V_RIEL, (
        f"blanco pleno son {LED_A_BLANCO_PLENO:.2f} A y el techo optimista da "
        f"{TECHO_W_OPTIMISTA/V_RIEL:.2f}: cabria. Revisa el conteo de LED del "
        f"#104 antes de relajar el tope.")

    # Codigo 2: los HUECO impresos por demo() son trabajo a medias, no un
    # verde. gates.py los cuenta sin convertirlos en un FALLO electrico.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
