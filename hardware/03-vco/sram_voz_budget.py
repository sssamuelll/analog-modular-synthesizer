#!/usr/bin/env python3
"""El censo de SRAM DE LA VOZ: 4,2 MB para el binario y el motor de audio.

    python hardware/03-vco/sram_voz_budget.py

Spec del motor S8.5: "censo de SRAM CON EL BINARIO ADENTRO -- sin flash
interna, el firmware entero comparte los 4,2 MB con tablas, colas y
retardos". Desde el acta del 2026-08-26 tambien con el buffer de sample.

Este es el descendiente de hardware/02-midi-cv/sram_budget.py. El papel
2026-08-30-hub-n657-y-radios-design.md sec.9 mando partirlo en dos: Voz sin
cara, hub con cara. Conserva el sampler, las tablas clase Serum y la vara
del EP-133; la puerta de la pantalla vive en sram_hub_budget.py.

QUE CAMBIO DE CHIP, Y QUE SIGUE ABIERTO

  D2 esta firmada desde el 2026-08-30: la cara es del hub. La camara y la
  NPU tampoco pertenecen a la Voz, con D3-prima o sin ella: son del hub
  mientras esa forma siga pendiente, o del mago al firmarse. La ausencia
  de esas reservas aqui no firma D3-prima. La linea de firma de sec.0 y
  la tension entre sec.10 filas 2 y 11 se resuelven en su propio papel.

  La Voz sigue pagando su motor de audio. En el peor caso del escenario
  heredado quedan 1 800 000 B, mas que la tabla y el buffer minimo de
  1 256 000 B. Es aritmetica de un ESTIMADO: no cierra el presupuesto de
  un firmware que todavia no existe.

LO QUE ES DATO Y LO QUE ES ESTIMADO

  DATO (fuente citada en su linea): SRAM y TCM del chip, una tabla clase
  Serum en f16, la vara del EP-133 y la calibracion del hub: 82 280 B de
  secciones ALLOC de software/nucleo/fw, medidos el 2026-09-09 en escritorio.

  ESTIMADO DECLARADO: binario de la Voz, colas y retardos, buffer minimo de
  sample. El rango del binario se conserva como escenario provisional; la
  medida del hub calibra USB, protocolo y modelo, pero no mide motores de
  audio. No hay un rango nuevo derivado de esa medida ni un firmware de la
  Voz cuyo mapa del linker permita sustituir el supuesto.
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(errors="replace")

# --- lo que el chip trae (DS p1, spec S1) -----------------------------------
# El DS dice "4.2-Mbyte contiguous SRAM" sin darla en bytes. Se lee en
# DECIMAL, que es la lectura CONSERVADORA: si el mapa real de bancos suma en
# Kbytes binarios seria ~200 KB mas, y el error va en la direccion segura
# (este censo pediria de mas, no de menos). El mapa exacto es del RM0486 y
# entra en el reparto por bancos junto al mapa del linker.
SRAM_B = 4_200_000            # DS p1, motor S1: 4,2 MB contiguos
TCM_B = 192 * 1024           # DS p1: 192 KB TCM (ITCM+DTCM), fuera del censo:
                             # es para ISR criticas y tablas calientes

# --- las piezas del firmware ------------------------------------------------
TABLA_SERUM_B = 1_000_000     # spec motor S3: "una tabla clase Serum ~1 MB en f16"

# MEDIDO 2026-09-09: software/nucleo/fw, origin/main c521302,
# cargo build --release, target thumbv8m.main-none-eabihf, vector 0x341A0000.
# Suma de secciones ALLOC; NO el tamano del ELF en disco, que incluye debug.
# sram_hub_budget.py publica las secciones y deriva de ellas su total.
# Es un piso de referencia del software compartido: pila USB, protocolo,
# modelo, servidor, descubrimiento y pinout. No es el binario terminado de
# la Voz ni una medida de sus motores de audio, que todavia no existen.
# Tampoco se suma a BINARIO_VOZ_B: ese rango ya representa el binario entero.
CALIBRACION_HUB_B = 82_280

# ESTIMADO DECLARADO -- sin fuente publicada ni firmware de la Voz.
# Se conserva el rango heredado como ESCENARIO PROVISIONAL, no como una
# medicion de los motores ni como un rango nuevo deducido de la calibracion.
# Los 82 280 B ya acotan el orden de la parte compartida; el trabajo de
# audio sigue sin medir. La separacion de chips no autoriza a adivinarlo.
BINARIO_VOZ_B = (700_000, 2_000_000)
# ESTIMADO: colas de audio (SAI in/out, CV, USB) y retardos del motor.
# Rango heredado: no hay tamanos de buffers ni medicion que lo descompongan.
# No incluye por decreto la futura interfaz multicanal de hub sec.6.2: su
# papel propio tiene que decidir donde vive y que memoria anade al dueno.
COLAS_B = (150_000, 400_000)

# --- la vara del EP-133 (pagina oficial de Teenage Engineering, verificada
#     2026-08-26; acta de Samuel: "tenemos que minimo alcanzar la memoria de
#     ellos") -----------------------------------------------------------------
EP133_B = 128 * 1024 * 1024  # Pagina oficial TE, verificada 2026-08-26.
EP133_SLOTS = 999            # Pagina oficial TE, verificada 2026-08-26.
EP133_KHZ = 46               # Pagina oficial TE, verificada 2026-08-26.
EP133_BITS = 16              # Pagina oficial TE, verificada 2026-08-26.
F_MUESTRA_SAMPLE = 48000.0   # Audio del motor, misma tasa que psram_budget.py.
BYTES_POR_MUESTRA = 2        # 16 bits mono, misma clase que EP-133; censo padre.

# Lo minimo que un sampler necesita residente en SRAM para trabajar aunque
# todo lo demas se streamee: ESTIMADO DECLARADO, heredado del primer censo.
MINIMO_SAMPLE_B = 256_000    # ESTIMADO: buffer de trabajo sin dimensionar.


def demanda_voz_b() -> int:
    """Una tabla residente y el buffer de sample de trabajo del motor."""
    return TABLA_SERUM_B + MINIMO_SAMPLE_B


def fijo_b(peor: bool, binario: int | float | None = None) -> int | float:
    """Binario entero y colas/retardos; tablas y samples se cobran aparte.

    Esta es LA cuenta de lo fijo. El binario opcional permite despejar el
    techo y buscar el borde con el canario, sin repetir los sumandos."""
    i = 1 if peor else 0
    return (BINARIO_VOZ_B[i] if binario is None else binario) + COLAS_B[i]


def libre_b(peor: bool, binario: int | float | None = None) -> int | float:
    """Lo que queda para tablas y samples tras pagar lo fijo de la Voz."""
    return SRAM_B - fijo_b(peor, binario=binario)


def techo_binario_b() -> int | float:
    """DERIVADO del mismo reparto que decide la guarda, con colas al peor.

    El censo viejo olvidaba los cuadros de camara en dos techos escritos a
    mano. Hoy no son de este chip, pero el fallo era tener dos cuentas: la
    identidad libre_b(peor=True, binario=techo) == demanda_voz_b() lo vigila.
    Todo techo publicado tiene que salir de aqui."""
    return libre_b(peor=True, binario=0) - demanda_voz_b()


def parametros() -> dict[str, int | float]:
    """Escenario heredado mas exigente; el canario mueve solo el binario."""
    return {"binario": BINARIO_VOZ_B[1]}


def guarda_voz(p: dict[str, int | float]) -> None:
    """La demanda minima tiene que caber; texto estable para el canario.

    Pasar esta guarda significa caber con el binario suministrado y las
    colas estimadas al peor. No significa que ese binario este medido."""
    libre = libre_b(peor=True, binario=p["binario"])
    assert libre >= demanda_voz_b(), (
        f"no cabe en la SRAM de la Voz: quedan {libre:,} B y la tabla mas "
        f"el buffer minimo piden {demanda_voz_b():,} B")


def demo() -> None:
    print("\nEL CENSO DE SRAM DE LA VOZ (motor S8.5; hub D2, sec.9)\n")
    print(f"  SRAM contigua: {SRAM_B:,} B. TCM aparte: {TCM_B:,} B (ISR")
    print("  criticas y tablas calientes por linker -- no entra al reparto).")
    print("  El chip NO tiene flash interna: el binario vive aqui dentro.")
    print("  Pantalla, camara y NPU pertenecen a los otros chips; la Voz")
    print("  conserva el sampler, las tablas y sus colas de audio.\n")

    print("  LA MEDIDA QUE YA EXISTE, Y HASTA DONDE LLEGA:")
    print(f"    calibracion del hub: {CALIBRACION_HUB_B:,} B, MEDIDO 2026-09-09")
    print("    software/nucleo/fw, origin/main c521302; cargo build --release")
    print("    thumbv8m.main-none-eabihf; vector 0x341A0000; suma ALLOC.")
    print("    Es el piso compartido de USB, protocolo, modelo, servidor,")
    print("    descubrimiento y pinout. No es una cifra terminada de la Voz:")
    print("    todavia no hay firmware de sus motores de audio que medir.")
    print("    No se anade como otro costo al rango del binario entero.\n")

    print("  Lo fijo (ESTIMADOS heredados, sin fuente publicada):")
    for nombre, (lo, hi) in (("binario entero de la Voz", BINARIO_VOZ_B),
                             ("colas de audio y retardos", COLAS_B)):
        print(f"    {nombre:34s} {lo:>10,} - {hi:,} B")
    print(f"    {'TOTAL':34s} {fijo_b(False):>10,} - {fijo_b(True):,} B")
    print("    El rango del binario es un escenario provisional conservado;")
    print("    no mide audio ni sale de escalar el firmware del hub.")
    print("    Las colas tampoco tienen buffers dimensionados o medidos.\n")

    print("  LO QUE QUEDA PARA TABLAS Y SAMPLES:")
    print(f"    {'escenario':20s} {'libre':>14s} {'tablas completas':>18s}")
    for peor, nombre in ((False, "mejor ESTIMADO"), (True, "peor ESTIMADO")):
        libre = libre_b(peor=peor)
        n_tab = max(0, (libre - MINIMO_SAMPLE_B) // TABLA_SERUM_B)
        print(f"    {nombre:20s} {libre:>14,} B {n_tab:>15d}")
    print("    Las tablas completas se cuentan reservando primero el buffer")
    print(f"    de sample de {MINIMO_SAMPLE_B:,} B, tambien ESTIMADO.")
    print("    Motor S3 publica entre 1 y 3 tablas residentes: el minimo")
    print("    que este censo exige es UNA, no las tres simultaneamente.")
    print(f"    Demanda minima de la Voz: {demanda_voz_b():,} B.\n")

    print("  EL TECHO DEL BINARIO, CON LAS COLAS EN EL PEOR CASO:")
    print(f"    binario <= {techo_binario_b():,} B para alojar el minimo.")
    print("    Sale de libre_b(peor=True, binario=0) menos la demanda; la")
    print("    guarda y el techo pagan exactamente los mismos costos fijos.")
    print("    Si se anade otra reserva, se cobra en fijo_b y mueve a ambos.")
    print("    Este techo depende de las colas estimadas; no es una medida.\n")

    print("  EL SAMPLER EN SRAM, contra la vara del EP-133:")
    para_sample = libre_b(peor=True) - TABLA_SERUM_B
    seg = para_sample / (F_MUESTRA_SAMPLE * BYTES_POR_MUESTRA)
    print(f"    con una tabla residente, peor ESTIMADO: {para_sample:,} B")
    print(f"    = {seg:.2f} s de audio a {F_MUESTRA_SAMPLE/1000:.0f} kHz")
    print(f"    / {BYTES_POR_MUESTRA*8} bits mono, EN LA SRAM DEL CHIP.")
    print("    Es la capacidad de trabajo tras la tabla, no un catalogo ni")
    print("    una duracion garantizada: depende del firmware aun estimado.")
    print(f"    El EP-133 K.O. II tiene {EP133_B:,} B para TODO su universo")
    print(f"    ({EP133_SLOTS} slots, {EP133_KHZ} kHz / {EP133_BITS} bits, sin")
    print("    expansion). La mesa de trabajo es la PSRAM (psram_budget.py)")
    print("    y el catalogo es el XSPI2. El caudal de granos se comprueba")
    print("    alli; que sobren bytes aqui no demuestra ese caudal.")


def _autocomprobacion() -> None:
    # 1. La ausencia es parte del contrato: ni con D3-prima ni sin ella
    #    vuelven estos costos a la Voz. Sus escenarios son del otro censo.
    for ajeno in ("framebuffer_b", "NPU_ACTIVACIONES_B", "FRAMES_CAMARA_B"):
        assert ajeno not in globals(), f"{ajeno} no pertenece a la Voz"
    # 2. Lo fijo tiene que ser rango, no punto: un ESTIMADO sin ancho es un
    #    numero disfrazado. La calibracion del hub no rellena el firmware.
    assert fijo_b(True) > fijo_b(False) * 1.5
    # 3. El binario sigue siendo el ESTIMADO mas ancho, ahora entre los
    #    costos que son de este chip. Si otra fila crece mas, la conclusion
    #    publicada se relee; no se compara una resta consigo misma.
    anchos = {"binario": BINARIO_VOZ_B[1] - BINARIO_VOZ_B[0],
              "colas": COLAS_B[1] - COLAS_B[0]}
    assert max(anchos, key=anchos.get) == "binario", (
        f"el binario dejo de ser el ESTIMADO mas ancho ({anchos}): la "
        "conclusion que este censo publica hay que reescribirla")
    # 4. La vara del EP-133, escrita de otra forma para que un find-replace
    #    de la capacidad no mueva tambien el testigo sin que nadie lo vea.
    assert EP133_B == 134_217_728
    # 5. El techo entra por la misma puerta que la guarda, hasta el byte.
    assert libre_b(peor=True, binario=techo_binario_b()) == demanda_voz_b()


def main() -> int:
    _autocomprobacion()
    demo()

    # Asercion INVERSA de la punta favorable: si ni el mejor supuesto cabe,
    # declarar solo el firmware ausente estaria tapando un rojo del modelo.
    assert libre_b(peor=False) >= demanda_voz_b(), (
        "ni en el mejor caso de los ESTIMADOS cabe el minimo de la Voz: "
        "esto ya no es solo firmware sin medir, es un ROJO del escenario")
    guarda_voz(parametros())
    # Asercion INVERSA del alcance publicado: el peor supuesto permite una
    # tabla, pero no dos junto al sample minimo. Si alcanza para dos, cambia
    # lo que este censo cuenta sobre el margen; se relee, no se hereda.
    assert libre_b(peor=True) < demanda_voz_b() + TABLA_SERUM_B, (
        "ya caben dos tablas y el sample minimo en el peor ESTIMADO: "
        "releer el margen de la Voz con este escenario nuevo")

    # HUECO pese a pasar la guarda. El rango provisional no es evidencia de
    # un firmware que falta: pasar con ese supuesto no da permiso para
    # llamarlo presupuesto cerrado. Tampoco requiere esperar la placa:
    # cuando exista firmware de la Voz se enlaza y se suman sus ALLOC.
    print("\nHUECO: la Voz no tiene firmware de audio que medir.")
    print(f"El peor ESTIMADO deja {libre_b(peor=True):,} B para tablas y")
    print(f"samples; el minimo pide {demanda_voz_b():,} B y quedan")
    print(f"{libre_b(peor=True) - demanda_voz_b():,} B de margen supuesto.")
    print(f"El techo derivado del binario es {techo_binario_b():,} B.")
    print("La medida del hub ya calibra el software compartido. Lo que")
    print("falta es implementar y enlazar los motores, medir las secciones")
    print("ALLOC de ese firmware en escritorio y dimensionar colas y")
    print("retardos. La interfaz multicanal de sec.6.2 sigue sin dueno")
    print("firmado: si le toca a la Voz, su papel tiene que ampliar el censo.")
    # gates.py conserva la ultima linea: el motivo tiene que entrar primero
    # para que su resumen no confunda un supuesto holgado con un cierre.
    print("HUECO: Voz sin firmware de audio; binario y colas ESTIMADOS")
    return 2


# ---------------------------------------------------------------------------
# LO QUE ESTE CALCULO **NO** CUBRE
#
#   * EL MAPA DEL LINKER. Reparte BYTES, no direcciones, alineacion o bancos.
#     TCM, ISR, tablas calientes y DMA se colocan por linker. La suma ALLOC
#     del firmware tampoco prueba el maximo uso de pila ni las reservas
#     dinamicas: al existir esos motores hay que enumerar que queda fuera.
#
#   * EL TAMANO REAL DEL BINARIO DE LA VOZ. La calibracion del hub mide su
#     software compartido, no los motores. El rango conservado es provisional
#     y no tiene fuente nueva. No falta una placa para medirlo: falta ese
#     firmware, que despues se puede enlazar y medir desde el escritorio.
#
#   * COLAS, RETARDOS E INTERFAZ MULTICANAL. Se conserva el rango heredado sin
#     tamanos de buffers ni medida. Hub sec.6.2 deja el dueno de la interfaz
#     pendiente de su papel: aqui no se elige ni se le inventa una reserva.
#
#   * EL CATALOGO DE SAMPLES Y EL CAUDAL. La biblioteca no volatil vive en
#     XSPI2 y su mesa de trabajo en la PSRAM del XSPI1. La vara del EP-133 y
#     la contencion de los granos se contestan en psram_budget.py. Ni la
#     holgura de SRAM ni el minimo de trabajo prometen polifonia o latencia.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())
