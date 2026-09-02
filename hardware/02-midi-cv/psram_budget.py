#!/usr/bin/env python3
"""La PSRAM del sampler: cuanto cabe, cuanto corre, y cuantos granos aguanta.

    python psram_budget.py

Nace por dos actas de Samuel del 2026-08-26. La de la tarde la hizo pieza v1
("granular y sampler van a v1... lo que sea necesario"), y el spec del motor
le mando guion propio (S8.7): "caudal y latencia del XSPI1 contra la demanda
de granos/sampler". La de la noche le puso vara: "una de las cosas que le
critican al Teenage Engineering EP-133 K.O. II es la poca memoria que tiene.
tenemos que minimo alcanzar la memoria de ellos".

LAS DOS PREGUNTAS, QUE SON DISTINTAS

  ESPACIO -- cuantos samples caben. Se contesta con densidad de la pieza y
  con la biblioteca del XSPI2. Es donde vive la vara del EP-133.

  CAUDAL -- cuantos granos pueden LEER a la vez sin ahogar el bus. Es el
  cuello real del granular, y no tiene nada que ver con el espacio: mil
  granos en 64 MB no caben en el bus aunque sobren bytes.

DE DONDE SALEN LOS NUMEROS

  DATO: el techo electrico del XSPI (DS Tablas 75-76, citadas por el spec
  S8.7): SDR 185 MHz a 1,8 V / 140 MHz a 3,3 V; DTR 180 / 140 MHz. El bus
  octal son 8 lineas = 1 byte por transferencia, y DTR mueve dos por ciclo.
  La vara del EP-133: 128 MB, 999 slots, 46 kHz / 16 bits -- pagina oficial
  de Teenage Engineering, verificada 2026-08-26.

  ESTIMADO DECLARADO: la densidad de la pieza (la clase octal llega a
  512 Mbit = 64 MB; la pieza NO esta elegida -- R-M3), la eficiencia real
  del bus con lecturas cortas y aleatorias, y el tamano de la lectura por
  grano. Cada uno lo dice al imprimirse.
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(errors="replace")

# --- el techo electrico del XSPI -------------------------------------------
# El spec S8.7 cita las Tablas 75-76 -- y esa fuente esta INCOMPLETA para
# ESTE diseno (hallazgo de la junta de la tanda 2, verificado en el PDF):
#   Tabla 75 (p180) SDR:            185 MHz a 1,65-1,98 V | 140 a 2,7-3,6 V
#   Tabla 76 (p181) DTR SIN DQS:    180 MHz a 1,65-1,98 V | 140 a 2,7-3,6 V
#   Tabla 77 (p182) DTR CON DQS:    200 MHz a 1,65 V < VDD < 3,6 V -- o sea
#                                   a CUALQUIER voltaje de los dos
# Y el censo de pines sienta XSPIM_P1_DQS0 en PO2 (micro_budget.py): la
# PSRAM de este instrumento lee CON DQS, asi que la tabla aplicable es la
# 77. Consecuencia que el papel todavia no dice: el voltaje NO decide el
# techo en el modo del diseno. Se enmienda S8.7 -- arreglar la fuente, no
# la regla.
#   (etiqueta, MHz, modo, aplica-a-este-diseno)
XSPI_TECHO = (
    ("SDR, 2,7-3,6 V (Tabla 75)", 140.0, "SDR", False),
    ("SDR, 1,65-1,98 V (Tabla 75)", 185.0, "SDR", False),
    ("DTR sin DQS, 2,7-3,6 V (Tabla 76)", 140.0, "DTR", False),
    ("DTR sin DQS, 1,65-1,98 V (Tabla 76)", 180.0, "DTR", False),
    ("DTR CON DQS, cualquier V (Tabla 77)", 200.0, "DTR", True),
)
LINEAS_OCTAL = 8              # el bus del acta: octal = 1 byte por transfer
TRANSFERS_POR_CICLO = {"SDR": 1, "DTR": 2}
# El crecimiento censado: 16 bits (necesita VFBGA223+, ya cubierto por el 264)
LINEAS_16B = 16

# --- la pieza, sin nombre todavia (R-M3) ------------------------------------
# ESTIMADO DECLARADO: el techo de densidad conocido de la clase octal.
DENSIDAD_MBIT = 512
PSRAM_B = DENSIDAD_MBIT * 1024 * 1024 // 8

# --- la vara (pagina oficial de TE, verificada 2026-08-26) ------------------
EP133_B = 128 * 1024 * 1024
EP133_SLOTS = 999
EP133_KHZ = 46.0
EP133_BITS = 16

# --- el audio del SAM17 -----------------------------------------------------
F_MUESTRA = 48000.0
BYTES_POR_MUESTRA = 2         # 16 bits mono, la misma clase que el EP-133

# --- la pantalla, por si se muda aqui (acta camino A) -----------------------
PANTALLA_PX = 800 * 480
PANTALLA_HZ = 60.0

# --- el modelo del grano ----------------------------------------------------
# Un grano lee su posicion con interpolacion y avanza secuencialmente dentro
# de su ventana: no son 4 bytes sueltos por muestra, son rafagas que
# alimentan muchas muestras.
#
# ESTIMADO DECLARADO, SIN PRECEDENTE APLICABLE (correccion de la junta: la
# version anterior lo justificaba con "el spec del modulo 3 usa 0,60", y esa
# cifra ni vive en una spec ni es la misma fisica -- es un ESTIMADO de
# spi_privado_budget.py:57 para huecos de CS en un SPI punto a punto). Aqui
# el descuento cubre otra cosa: comando + latencia de lectura de la clase
# octal, refresco propio de una PSRAM (que es DRAM por dentro) y el
# desperdicio de rafaga cuando un grano nace o salta. Sin hoja de pieza
# (R-M3) no hay numero mejor que un rango prudente.
EFICIENCIA = 0.60
# ESTIMADO DECLARADO: la velocidad de reproduccion. Un grano transpuesto lee
# proporcional a su ratio -- +1 octava son 2x bytes, +2 octavas 4x. El
# granular existe para transponer, asi que modelar solo 1.0 seria optimismo
# (la junta lo cazo: con ratio alto el veredicto "manda la CPU" se voltea).
RATIOS = (1.0, 2.0, 4.0)


def caudal_bruto_bs(mhz: float, modo: str, lineas: int = LINEAS_OCTAL) -> float:
    """Bytes por segundo del bus, sin descuentos."""
    return mhz * 1e6 * TRANSFERS_POR_CICLO[modo] * (lineas / 8)


def caudal_util_bs(mhz: float, modo: str, lineas: int = LINEAS_OCTAL) -> float:
    return caudal_bruto_bs(mhz, modo, lineas) * EFICIENCIA


def bytes_por_grano_s(ratio: float = 1.0) -> float:
    """Bytes/s que pide UN grano sonando a velocidad `ratio`.

    Avanza por su ventana a `ratio` x velocidad de muestra: transponerlo
    hacia arriba lo hace leer mas rapido, y eso es bus, no ciclos.
    """
    return F_MUESTRA * BYTES_POR_MUESTRA * ratio


def granos_por_caudal(mhz: float, modo: str, lineas: int = LINEAS_OCTAL,
                      ratio: float = 1.0) -> int:
    return int(caudal_util_bs(mhz, modo, lineas) // bytes_por_grano_s(ratio))


def granos_de_cpu() -> tuple[int, int]:
    """Los que compra la CPU, RECALCULADOS desde carga_motor_budget -- no
    copiados a mano (la junta cazo los literales 129/289 pudriendose en
    silencio). El mas apretado sale del motor base mas caro; el mas holgado,
    de un instrumento solo-granular."""
    import carga_motor_budget as cm
    pm = cm.presupuesto_motor()
    caro = max(hi for _, (_lo, hi) in cm.MOTORES_PUBLICADOS.items())
    return (cm.granos_que_caben(pm - caro), cm.granos_que_caben(pm))


def segundos_de_audio(b: int) -> float:
    return b / (F_MUESTRA * BYTES_POR_MUESTRA)


def demo() -> None:
    print("\nLA PSRAM DEL SAMPLER (spec S8.7)\n")
    print("  PREGUNTA 1 -- ESPACIO: la vara del EP-133 K.O. II\n")
    print(f"    EP-133: {EP133_B:,} B para TODO su universo "
          f"({EP133_SLOTS} slots,")
    print(f"            {EP133_KHZ:.0f} kHz / {EP133_BITS} bits, sin ranura ni "
          f"expansion)")
    print(f"          = {segundos_de_audio(EP133_B)/60:.0f} min de audio en "
          f"total, para siempre")
    print()
    print(f"    SAM17, mesa de trabajo (PSRAM en XSPI1): {PSRAM_B:,} B "
          f"ESTIMADO")
    print(f"          = {segundos_de_audio(PSRAM_B)/60:.1f} min de audio VIVO "
          f"a la vez")
    print("    SAM17, catalogo (biblioteca en XSPI2, no volatil): la clase")
    print("          de flash del puerto va de cientos de MB a GB -- ordenes")
    print("          de magnitud sobre el universo entero del EP-133, y es")
    print("          el sitio donde de verdad se compara. Pieza sin elegir.")
    print()
    print("    veredicto de espacio, en dos mitades y sin trampa:")
    print(f"      MESA: {100*PSRAM_B/EP133_B:.0f} % de TODO el EP-133 -- y")
    print("      esto SI esta aseverado abajo (criterio propio de este")
    print("      guion: la mesa sola debe llegar a la mitad de la vara,")
    print("      porque el catalogo cubre el resto). Pasa por IGUALDAD")
    print("      EXACTA con la densidad ESTIMADA de hoy: margen cero, o")
    print("      sea que una pieza mas chica que 512 Mbit lo rompe.")
    print("      CATALOGO: sin pieza, sin cifra y SIN ASEVERAR. Que la")
    print("      clase de flash del XSPI2 pase de largo la vara es")
    print("      razonable y no es un hecho: es fila de R-M3.")
    print("    -> la vara del acta queda MEDIO cerrada. Se cierra entera")
    print("       el dia que el catalogo tenga pieza y numero.")

    print("\n  PREGUNTA 2 -- CAUDAL: cuantos granos aguanta el bus\n")
    print(f"    un grano a velocidad 1.0 pide {bytes_por_grano_s()/1e3:.0f} "
          f"kB/s ({F_MUESTRA/1e3:.0f} kHz x {BYTES_POR_MUESTRA} B); "
          f"transponerlo")
    print(f"    lo multiplica: {' , '.join(f'x{r:.0f} = ' + str(int(bytes_por_grano_s(r)/1e3)) + ' kB/s' for r in RATIOS[1:])}")
    print(f"    eficiencia aplicada: {EFICIENCIA:.2f} ESTIMADO sin "
          f"precedente aplicable (ver arriba)")
    print()
    cab = "  ".join(f"x{r:.0f}" for r in RATIOS)
    print(f"    {'configuracion':38s} {'util':>10s}   granos a {cab}")
    for et, mhz, modo, aplica in XSPI_TECHO:
        marca = "*" if aplica else " "
        gr = "  ".join(f"{granos_por_caudal(mhz, modo, ratio=r):>4d}"
                       for r in RATIOS)
        print(f"  {marca} {et:38s} {caudal_util_bs(mhz, modo)/1e6:>6.0f} MB/s"
              f"   {gr}")
    et16, mhz16, modo16, _ = XSPI_TECHO[-1]
    gr = "  ".join(f"{granos_por_caudal(mhz16, modo16, LINEAS_16B, r):>4d}"
                   for r in RATIOS)
    print(f"    {'16 bits, misma tabla (crecimiento)':38s} "
          f"{caudal_util_bs(mhz16, modo16, LINEAS_16B)/1e6:>6.0f} MB/s   {gr}")
    print("    (* la fila que aplica a ESTE diseno: el censo sienta DQS0)")

    print("\n  LAS DOS PREGUNTAS, JUNTAS: quien manda\n")
    cpu_lo, cpu_hi = granos_de_cpu()
    print(f"    la CPU compra {cpu_lo}-{cpu_hi} granos segun el motor base")
    print("    (recalculado en vivo desde carga_motor_budget, no copiado)")
    for r in RATIOS:
        bus = min(granos_por_caudal(mhz, modo, ratio=r)
                  for _, mhz, modo, ap in XSPI_TECHO if ap)
        if bus >= cpu_hi:
            quien = "manda la CPU"
        elif bus < cpu_lo:
            quien = "manda el BUS"
        else:
            quien = "manda uno u otro segun el motor base"
        print(f"    a velocidad x{r:.0f}: el bus da {bus:>4d} granos -> "
              f"{quien}")
    print("    El techo real es el mas apretado de los dos, y ninguno se")
    print("    promete hasta que el bring-up mida.")
    print()
    print("    Y no todos los granos leen de PSRAM: los que caben en SRAM")
    print("    (censo de sram_budget.py) no tocan este bus. El reparto")
    print("    SRAM/PSRAM es del linker, y es la fila 5 de riesgos.")

    print("\n  EL CLIENTE QUE PODRIA MUDARSE AQUI: el framebuffer\n")
    print("    si el censo de SRAM manda el framebuffer a la PSRAM (su")
    print("    salida 2), el LTDC leeria de este mismo bus SIN PAUSA y sin")
    print("    negociar -- y cuanto, depende del formato que se elija:")
    et, mhz, modo, _ = [f for f in XSPI_TECHO if f[3]][0]
    u = caudal_util_bs(mhz, modo)
    for fmt, bpx in (("RGB565", 2), ("RGB888", 3)):
        fb = PANTALLA_PX * bpx * PANTALLA_HZ
        queda = u - fb
        g = int(queda // bytes_por_grano_s()) if queda > 0 else 0
        print(f"    framebuffer {fmt} ({bpx} B/px): {fb/1e6:>3.0f} MB/s de "
              f"los {u/1e6:.0f} -> quedan {queda/1e6:>4.0f} MB/s = {g} "
              f"granos")
    print(f"    (en la fila que aplica: {et})")
    print("    Esa es la cuenta que decide la salida 2 del censo de SRAM --")
    print("    y a x1.0 de velocidad: con granos transpuestos, menos.")


def _autocomprobacion() -> None:
    # 1. La aritmetica del bus: octal DTR mueve 2 bytes por ciclo.
    assert caudal_bruto_bs(100.0, "DTR") == 200e6
    assert caudal_bruto_bs(100.0, "SDR") == 100e6
    assert caudal_bruto_bs(100.0, "DTR", LINEAS_16B) == 400e6
    # 2. Los techos del DS, cotejados por su CAUDAL derivado y no por una
    #    copia literal del mismo tuple (la junta cazo que un find-replace
    #    movia dato y pin a la vez y el pin nunca gritaba). Los MHz se
    #    escriben aqui como cita: Tabla 75 p180, Tabla 76 p181, Tabla 77
    #    p182 del DS14791 Rev 2.
    por_etiqueta = {e: (mhz, modo, ap) for e, mhz, modo, ap in XSPI_TECHO}
    assert caudal_bruto_bs(*por_etiqueta[
        "SDR, 1,65-1,98 V (Tabla 75)"][:2]) == 185e6
    assert caudal_bruto_bs(*por_etiqueta[
        "DTR sin DQS, 1,65-1,98 V (Tabla 76)"][:2]) == 360e6
    assert caudal_bruto_bs(*por_etiqueta[
        "DTR CON DQS, cualquier V (Tabla 77)"][:2]) == 400e6
    # 3. Y la tabla aplicable es UNA sola: la del modo que el censo de
    #    pines sienta (con DQS). Si alguien marcara dos, el veredicto de
    #    "quien manda" dejaria de tener fila unica.
    assert sum(1 for *_r, ap in XSPI_TECHO if ap) == 1
    # 4. La vara del EP-133, tal como su pagina la publica.
    assert EP133_B == 134_217_728 and EP133_SLOTS == 999
    # 5. Un grano pide su audio por su ratio: si alguien cambiara la tasa,
    #    los bytes por muestra o los ratios, los granos se mueven solos.
    assert bytes_por_grano_s() == 96_000.0
    assert bytes_por_grano_s(2.0) == 2 * bytes_por_grano_s()
    assert RATIOS[0] == 1.0 and max(RATIOS) >= 2.0
    # 6. La eficiencia es un descuento declarado, no un adorno.
    assert 0.0 < EFICIENCIA < 1.0


def main() -> int:
    _autocomprobacion()
    demo()

    # 1. LA MITAD DE LA VARA QUE ESTE GUION PUEDE ASEVERAR. El acta pide
    #    alcanzar los 128 MB del EP-133; eso lo cumplen mesa + catalogo, y
    #    el catalogo no tiene pieza ni cifra (R-M3). Asi que lo aseverado
    #    es un criterio PROPIO de este guion, declarado como tal: la mesa
    #    sola debe llegar a la mitad de la vara, porque el catalogo cubre
    #    el resto por clase. Hoy pasa por igualdad EXACTA (margen cero):
    #    cualquier pieza por debajo de 512 Mbit lo rompe, y eso es
    #    justamente lo que tiene que gritarle a R-M3.
    assert PSRAM_B >= EP133_B // 2, (
        f"la PSRAM ESTIMADA ({PSRAM_B:,} B) no llega a la mitad de la vara "
        f"del EP-133 ({EP133_B // 2:,} B): con esa pieza la mesa de trabajo "
        f"no sostiene el criterio de este guion y la vara del acta queda "
        f"colgando entera del catalogo -- releer R-M3 antes de comprar")

    # 2. El caudal tiene que comprar granos suficientes para que granular
    #    sea un motor y no una demo: al menos una voz por canal (16), y en
    #    el PEOR ratio modelado, no solo a velocidad 1.0.
    peor = min(granos_por_caudal(mhz, modo, ratio=max(RATIOS))
               for _, mhz, modo, ap in XSPI_TECHO if ap)
    assert peor >= 16, (
        f"a velocidad x{max(RATIOS):.0f} el bus solo aguanta {peor} granos "
        f"desde PSRAM: por debajo de una voz por canal, granular no es "
        f"motor de v1")

    # 3. Asercion INVERSA sobre el framebuffer mudado: hoy la mudanza CABE
    #    en caudal -- en el formato mas caro y con granos transpuestos --
    #    y por eso es salida viva del censo de SRAM. El dia que deje de
    #    caber, esa salida muere y hay que releer las tres.
    fb_caro = PANTALLA_PX * 3 * PANTALLA_HZ
    for et, mhz, modo, ap in XSPI_TECHO:
        if not ap:
            continue
        assert caudal_util_bs(mhz, modo) > fb_caro, (
            f"el framebuffer RGB888 solo ({fb_caro/1e6:.0f} MB/s) ya no "
            f"cabe en {et}: la salida 2 del censo de SRAM (mudar el "
            f"framebuffer a PSRAM) deja de existir")

    print("\n  LATENCIA: fuera de este guion hasta que la pieza tenga hoja")
    print("  (R-M3). El spec S8.7 manda 'caudal Y latencia'; esto cierra el")
    print("  caudal. Un grano que nace espera el comando de lectura antes")
    print("  del primer byte, y esa fecha limite no sale del ancho de banda.")
    print("\nOK: caudal cerrado; latencia pendiente de pieza.")
    return 0


# ---------------------------------------------------------------------------
# LO QUE ESTE CALCULO **NO** CUBRE
#
#   * LA LATENCIA, que el spec pide junto al caudal (S8.7) y aqui NO esta:
#     un grano que nace tiene que esperar el comando de lectura del XSPI
#     antes del primer byte, y ese numero sale de la hoja de la pieza (R-M3)
#     y del arbol de relojes, no de la aritmetica de ancho de banda. Con la
#     pieza nombrada, entra aqui como fila propia. Declarado, no escondido.
#
#   * LA PIEZA. Densidad, voltaje (que decide el techo: 1,8 V corre mas
#     rapido), SDR o DTR, y si trae los 16 bits del crecimiento. Todo eso es
#     R-M3 con hoja en arbol antes de dibujar. Este guion dice que restringe
#     a la pieza, no cual comprar.
#
#   * LA GRABACION EN VIVO. Escribir samples mientras suenan granos usa el
#     mismo bus en la otra direccion; el reparto lectura/escritura no esta
#     modelado y es fila de bring-up.
#
#   * EL CATALOGO DEL XSPI2. Su pieza tampoco esta elegida, y el streaming
#     de biblioteca comparte ese bus con los pesos de la NPU (hallazgo de la
#     junta de la camara). Ese choque se mide, no se supone.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())
