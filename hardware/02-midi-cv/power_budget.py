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

EL HALLAZGO, y es el que destraba el #151.

El #151 dice que la suma "no cierra": el margen de la IRM-15-5 al tope del #104
son +1.58 a +2.01 W y el host USB en su limite pide 2.50 W. Es verdad -- pero
solo si el tope de la cadena de LED se trata como una CARGA FIJA. No lo es: el
#104 existe precisamente para que sea un arbitro. Con el reparto puesto, el
instrumento cabe siempre; lo que el arbitro tiene que hacer es quitar brillo
cuando alguien enchufa un controlador que chupa sus 500 mA.

O sea que el #151 no pide una fuente mas grande. Pide que el arbitro exista.

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
# RP2350 "~0.2 A" -- spec de la fuente v2, citada por el #104 en su cuenta.
MICRO_A = 0.20
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
# Todo lo demas que cuelga del 3V3 y que no es el puente: micro ya contado
# aparte (esta en 3V3 pero su cifra citada es "del riel"), mux I2C, buffers,
# aislador. DECLARADO como cota, POR_CONFIRMAR al cerrar el BOM.
OTROS_3V3_A = 0.100


def carga_puente_media_a() -> float:
    """Corriente MEDIA del puente en su lado de 3.3 V, peor caso musical."""
    return PUENTE_TX_DUTY * PUENTE_TX_PICO_A + (1 - PUENTE_TX_DUTY) * PUENTE_RX_A


def desde_3v3(corriente_3v3_a: float) -> float:
    """Lo que una carga de 3.3 V le cuesta al riel de +5 V, con buck."""
    return corriente_3v3_a * PUENTE_V / (BUCK_EFICIENCIA * V_RIEL)


def duras_a(host_usb: bool) -> float:
    """Suma de las cargas que el arbitro NO puede tocar, en A del riel."""
    a = MICRO_A + desde_3v3(carga_puente_media_a() + OTROS_3V3_A)
    if host_usb:
        a += HOST_USB_A
    return a


def sobra_para_atenuables(host_usb: bool, techo_w: float) -> float:
    """Lo que queda para el arbitro despues de pagar lo duro, en A."""
    return techo_w / V_RIEL - duras_a(host_usb)


def arbitro(host_usb: bool, techo_w: float) -> float:
    """Techo de corriente que el arbitro del #104 puede darle a la cadena."""
    # Desde el 2026-08-27 esto es un paso directo, y NO sobra: el arbitro del
    # #104 es un concepto del diseno (que le queda a la cadena despues de las
    # cargas duras) y vuelve a tener resta el dia que aparezca otra carga
    # atenuable. La retroiluminacion era la unica que habia, y murio con la
    # pantalla de 2,8". Borrar la funcion seria borrar el nombre del arbitro.
    return sobra_para_atenuables(host_usb, techo_w)


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

    print("que le queda al arbitro del #104, por caso "
          "(techo pesimista):")
    print()
    print(f"  {'caso':<30} {'duras':>7} {'sobra':>7} {'cadena':>8}  veredicto")
    for nombre, host, pretende in CASOS:
        d = duras_a(host)
        s = sobra_para_atenuables(host, TECHO_W_PESIMISTA)
        cabe = arbitro(host, TECHO_W_PESIMISTA)
        ok = "OK" if cabe >= pretende else f"ARBITRA -{(pretende-cabe)*1000:.0f} mA"
        print(f"  {nombre:<30} {d:6.2f}A {s:6.2f}A {cabe:7.2f}A  {ok}")
    print()

    print("el pico NO es carga de la fuente:")
    print(f"  el regulador del 3V3 tiene que dar   "
          f"{pico_3v3_a()*1000:.0f} mA de pico")
    print(f"  la fuente solo ve la media           "
          f"{desde_3v3(med + OTROS_3V3_A)*1000:.0f} mA")
    print("  y el transitorio lo cubre el desacoplo local del modulo")
    print()

    deficit_real = LED_A_CASO_REAL - arbitro(True, TECHO_W_PESIMISTA)
    deficit_tope = LED_A_TOPE_104 - arbitro(True, TECHO_W_PESIMISTA)
    print("VEREDICTO")
    print(f"  Solo, el instrumento cabe con {LED_A_CASO_REAL:.2f} A de cadena "
          f"-- el brillo que de")
    print("  verdad usa segun el #104 (diez parejas de jack al 100% y el "
          "farol")
    print(f"  al 50%). Le sobran "
          f"{(arbitro(False, TECHO_W_PESIMISTA)-LED_A_CASO_REAL)*1000:.0f} mA.")
    print()
    print(f"  Enchufa un controlador USB que chupe sus {HOST_USB_A*1000:.0f} mA "
          f"y el arbitro tiene")
    print(f"  que quitar {deficit_real*1000:.0f} mA de cadena "
          f"({deficit_real/LED_A_CASO_REAL:.0%} del brillo real). Contra el")
    print("  tope del #104 el")
    print(f"  recorte serian {deficit_tope*1000:.0f} mA.")
    print()
    print("  Eso es exactamente lo que el #104 pedia y el #151 echaba en")
    print("  falta. La suma NO pide una fuente mas grande: pide que el")
    print("  arbitro exista.")
    print()
    print(f"  Blanco pleno son {LED_A_BLANCO_PLENO:.2f} A y no caben en ningun")
    print("  escenario: el tope no es cosmetico, es estructural.")
    print()
    print("Esto NO es una prueba: es una puerta. La medida que la cierra es la")
    print("corriente real del riel con el sensor de S9.1, contra la estimacion")
    print("que el arbitro hace antes de empujar cada cuadro.")


def _autocomprobacion() -> None:
    """Un caso a mano, para que el guion no se crea sus propias funciones."""
    # media del puente: 0.10*355 + 0.90*95 = 35.5 + 85.5 = 121 mA
    med = carga_puente_media_a()
    assert abs(med - 0.121) < 1e-6, med
    # al +5 V con buck al 90%: 121 mA * 3.3 / (0.9*5) = 88.7 mA
    assert abs(desde_3v3(med) - 0.0887333) < 1e-6, desde_3v3(med)
    # duras sin host: 0.20 + (0.121+0.100)*3.3/4.5 = 0.20 + 0.16207 = 0.36207
    assert abs(duras_a(False) - 0.3620666) < 1e-6, duras_a(False)


def main() -> int:
    _autocomprobacion()
    demo()

    # --- Las puertas ---------------------------------------------------------

    # 1. El criterio de cierre del #151, al derecho: las cargas DURAS con el
    #    host USB a su limite tienen que caber en el techo pesimista. Si esto
    #    falla, no hay arbitro que salve al instrumento.
    d = duras_a(True)
    assert d < TECHO_W_PESIMISTA / V_RIEL, (
        f"las cargas duras con el host USB a tope piden {d:.2f} A y el techo "
        f"derateado son {TECHO_W_PESIMISTA/V_RIEL:.2f} A: ni apagando cada LED "
        f"del instrumento cabe. Eso SI seria pedir otra fuente.")

    # 2. Y la otra mitad del mismo criterio: con el host enchufado, el caso de
    #    brillo real NO cabe sin arbitrar. Este aserto es al reves -- exige que
    #    el conflicto siga existiendo, porque el dia que deje de existir es que
    #    alguien movio un numero y el arbitro se quedo sin razon de ser.
    cabe_con_host = arbitro(True, TECHO_W_PESIMISTA)
    assert cabe_con_host < LED_A_CASO_REAL, (
        f"con el host USB a tope sobran {cabe_con_host:.2f} A para la cadena y "
        f"el caso real pide {LED_A_CASO_REAL:.2f}: ya no hace falta arbitrar. "
        f"Si esto es verdad, el #104 se puede cerrar -- pero revisa que numero "
        f"cambio antes de creertelo.")

    # 3. Sin host, el instrumento tiene que tocar con su brillo real. Si esto
    #    falla, el instrumento no funciona solo.
    cabe_solo = arbitro(False, TECHO_W_PESIMISTA)
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

    print()
    print("OK: presupuesto cerrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
