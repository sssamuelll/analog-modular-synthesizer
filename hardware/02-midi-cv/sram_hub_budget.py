#!/usr/bin/env python3
"""El censo de SRAM del hub: la cara tiene chip, su demanda todavia no.

    python sram_hub_budget.py

Nace de la enmienda del 2026-08-30, hub-n657-y-radios S9: partir el censo
en Voz sin cara y hub con cara. D2 esta firmada; el framebuffer es de este
chip. El sampler, las tablas clase Serum y la vara del EP-133 se quedaron
en hardware/03-vco/sram_voz_budget.py. No se le pide al hub que reserve la
mesa de trabajo de su cliente: hub S3.1 dice "ningun sampler".

ESTE GUION ES UNA PUERTA. La spec de la pantalla (S1) exige el censo de
SRAM verde y el soak de contencion con el refresco LTDC activo antes de
dibujar el conector. El propio papel corrigio la antigua "fila LTDC de
carga_motor": los ciclos promedio no prueban contencion. Desde D2 la
memoria de esa puerta es la del hub; el sujeto del soak que el papel
sigue atribuyendo al motor queda por enmendar.

EL DATO QUE SE MIDIO, Y LO QUE NO COMPRA

  El N657 NO TIENE FLASH INTERNA (DS p1, motor S1). El binario vive en
  SRAM. El 2026-09-09 se midieron las secciones ALLOC del ELF de
  software/nucleo/fw, origin/main en c521302, cargo build --release,
  target thumbv8m.main-none-eabihf, vectores en 0x341A0000. Su suma son
  82 280 B, no los 3 570 972 B del archivo: release lleva debug = 2.

  Es un PISO medido, no una cota superior. Tiene el USB device, el
  protocolo, el modelo, el servidor, el descubrimiento y el pinout: la
  parte compartida. NO tiene motores de audio, ni pila grafica del LTDC,
  ni pegamento de NPU, ni driver de SPI del J2, ni XSPI/PSRAM. Medir ese
  firmware no equivale a medir el firmware terminado.

LO QUE SIGUE ABIERTO, CON SU DUENO

  D3-prima sigue PENDIENTE: lo dice la firma al final de hub S0. S10 fila
  2 cobra NPU y cuadros de camara al hub; S10 fila 11 se los da al mago.
  Es una CONTRADICCION del papel. Este censo la nombra y cobra ambos
  costos por defecto; no firma D3-prima ni resuelve el papel.

  Donde vive el audio (hub S6.2) sigue sin decidirse y su prerrequisito
  es el papel de la interfaz, que no existe. None cobra las colas; solo
  una decision explicita de sacarlas permite descontarlas.

  LA DEMANDA PROPIA DEL HUB NO ESTA ENUMERADA EN NINGUN PAPEL. Cero es lo
  enumerado hoy, no lo que el hub necesita. Falta escribir que debe vivir
  al lado del framebuffer: composicion de UI, buffers del protocolo, DMA
  de J2, y su reparto sin contar dos veces lo que el ELF ya lleva. Son
  trabajos por censar, no cifras que este guion tenga permiso de inventar.

EL FALLO QUE ESTE DESCENDIENTE NO PUEDE HEREDAR

  El censo anterior cobraba los cuadros de camara en fijo_b(), pero los
  olvidaba al publicar los techos del binario: 600 000 B de mas en cada
  techo (punta alta del ESTIMADO de camara). Ahora el techo sale de
  libre_b() con binario cero; libre_b() cobra fijo_b(). Un costo fijo
  nuevo entra en esa funcion y mueve a la vez saldo, guarda y techo.
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(errors="replace")

# --- lo que el chip trae (DS14791 p1, hub S3.1) -----------------------------
# El DS dice "4.2-Mbyte contiguous SRAM" sin darla en bytes. Se lee en
# DECIMAL, que es la lectura CONSERVADORA: si el mapa real de bancos suma en
# Kbytes binarios seria ~200 KB mas, y el error va en la direccion segura
# (este censo pediria de mas, no de menos). El mapa exacto es del RM0486 y
# entra junto al mapa del linker: contar bytes no coloca bancos.
SRAM_B = 4_200_000             # DS14791 p1: 4,2 MB contiguos, lectura decimal.
TCM_B = 192 * 1024             # DS14791 p1: 192 KB, ISR criticas, fuera del censo.

# --- la pantalla que D2 le dio al hub --------------------------------------
PANTALLA_ANCHO = 800           # Hub S3.1, A-7/A-8: misma resolucion en 5 y 7".
PANTALLA_ALTO = 480            # Hub S3.1, A-7/A-8: la pulgada no cambia los bytes.
FORMATOS = {                  # Bytes por pixel (DS 3.29, pantalla S1).
    "RGB565 (16 bits)": 2,
    "RGB888 (24 bits)": 3,
}

# --- el binario: MEDIDO, con las partes atadas al total ---------------------
# Fuente de CADA fila: secciones ALLOC del ELF de software/nucleo/fw,
# origin/main c521302, cargo build --release, thumbv8m.main-none-eabihf,
# medida del 2026-09-09 entregada con esta enmienda. No es una nueva medida
# hecha por este guion ni incluye firmware que todavia no esta escrito.
SECCIONES_MEDIDAS = {
    ".vector_table": 844,      # ELF c521302, 2026-09-09: ALLOC, cargable.
    ".text": 51_092,           # ELF c521302, 2026-09-09: ALLOC, cargable.
    ".rodata": 10_916,         # ELF c521302, 2026-09-09: ALLOC, cargable.
    ".data": 500,              # ELF c521302, 2026-09-09: ALLOC, cargable.
    ".bss": 17_904,            # ELF c521302, 2026-09-09: ALLOC, NOBITS.
    ".uninit": 1_024,          # ELF c521302, 2026-09-09: ALLOC, NOBITS.
}
BINARIO_HUB_B = sum(SECCIONES_MEDIDAS.values())  # DERIVADO: toda la SRAM ocupada.
ELF_EN_DISCO_B = 3_570_972     # Misma medida: debug = 2; NO entra al presupuesto.
# HISTORIA, no entrada del censo. ESTIMADO viejo sin fuente publicada ni
# firmware completo: se conserva solo para comparar lo que se afirmaba.
BINARIO_ANTERIOR_B = (700_000, 2_000_000)

# --- decisiones pendientes, valor conservador -----------------------------
D3P_FIRMADA = False           # Hub S0, firma del 2026-08-30: pendiente S3.2.
AUDIO_EN_EL_HUB = None        # Hub S6.2: falta decidir y falta el papel propio.
DEMANDA_HUB_ENUMERADA = False  # Hub S3.1/S10.2 no enumeran residentes propios.

# --- lo fijo que aun es ESTIMADO ------------------------------------------
# ESTIMADO heredado, sin fuente de tamano ni firmware completo: colas de
# audio SAI in/out, CV, USB y retardos. Hub S6.2 manda cobrarlas si el audio
# vive aqui; no enumera canales ni profundidades. La horquilla vieja NO
# demuestra que alcance para la interfaz multicanal nueva.
COLAS_B = (150_000, 400_000)
# ESTIMADO (camara-gestos S5, hub S3.2): activaciones del modelo de manos;
# no hay modelo compilado ni mapa de activaciones que mida su huella.
# Los PESOS no viven aqui: se streamean desde XSPI2, como en el censo padre.
NPU_ACTIVACIONES_B = (200_000, 800_000)
# ESTIMADO (camara-gestos S5 fila 1, hub S10 fila 2): entrada reducida por
# DCMIPP, doble buffer para no leer un cuadro a medio escribir. No hay
# modelo elegido que fije resolucion y formato de esa entrada.
FRAMES_CAMARA_B = (150_000, 600_000)


def framebuffer_b(bytes_px: int, doble: bool) -> int:
    return PANTALLA_ANCHO * PANTALLA_ALTO * bytes_px * (2 if doble else 1)


def demanda_hub_b() -> int:
    """Lo ENUMERADO fuera del framebuffer y lo fijo; no la necesidad real.

    Hub S3.1 no le da sampler ni tablas Serum. Ningun papel ha escrito la
    lista propia. El cero mantiene la cuenta ejecutable; el indicador
    DEMANDA_HUB_ENUMERADA impide que ese cero se convierta en verde.
    """
    return 0


def fijo_b(peor: bool, *, d3p: bool | None = None,
           audio: bool | None = None, binario: int | None = None) -> int:
    """Lo que no es ni framebuffer ni demanda propia: se cobra SOLO aqui."""
    i = 1 if peor else 0
    if d3p is None:
        d3p = D3P_FIRMADA
    if audio is None:
        audio = AUDIO_EN_EL_HUB
    return ((BINARIO_HUB_B if binario is None else binario)
            + (COLAS_B[i] if audio is not False else 0)
            + (0 if d3p else NPU_ACTIVACIONES_B[i] + FRAMES_CAMARA_B[i]))


def libre_b(bytes_px: int, doble: bool, peor: bool, *,
            d3p: bool | None = None, audio: bool | None = None,
            binario: int | None = None, framebuffer: int | None = None) -> int:
    # La sustitucion de framebuffer deja al canario mover sus bytes sin
    # inventar otro saldo en la guarda. Cero B/px representa PSRAM propia.
    fb = framebuffer_b(bytes_px, doble) if framebuffer is None else framebuffer
    return SRAM_B - fb - fijo_b(peor, d3p=d3p, audio=audio, binario=binario)


def techo_binario_b(bytes_px: int, doble: bool, *,
                    d3p: bool | None = None, audio: bool | None = None) -> int:
    """Binario maximo con lo DEMAS en peor caso, desde la misma cuenta.

    Es un techo condicionado a la demanda enumerada, hoy cero. No es una
    prediccion del binario terminado ni una autorizacion de la pantalla.
    Puede salir negativo: ni con binario cero cerraria esa configuracion.
    """
    return (libre_b(bytes_px, doble, peor=True, d3p=d3p, audio=audio, binario=0)
            - demanda_hub_b())


def parametros() -> dict:
    """Hub S10 fila 2: framebuffer en PSRAM propia, pendientes conservadores."""
    return {"binario": BINARIO_HUB_B, "framebuffer": 0, "peor": True,
            "d3p": D3P_FIRMADA, "audio": AUDIO_EN_EL_HUB}


def guarda_hub(p: dict) -> None:
    """Puerta de bytes ENUMERADOS; su texto estable alimenta al canario."""
    libre = libre_b(0, False, p["peor"], d3p=p["d3p"], audio=p["audio"],
                    binario=p["binario"], framebuffer=p["framebuffer"])
    assert libre >= demanda_hub_b(), (
        f"no cabe en la SRAM del hub: quedan {libre:,.0f} B y lo enumerado "
        f"pide {demanda_hub_b():,}. Esto es ROJO aun sin completar la demanda")


def demo() -> None:
    print("\nEL CENSO DE SRAM DEL HUB (hub S3.1, S10 fila 2)\n")
    print(f"  SRAM contigua: {SRAM_B:,} B. TCM aparte: {TCM_B:,} B (ISR")
    print("  criticas por linker -- no entra al reparto).")
    print("  El chip NO tiene flash interna: el binario vive aqui dentro.\n")

    print("  MEDIDO: software/nucleo/fw, origin/main c521302, 2026-09-09.")
    print("  cargo build --release, thumbv8m.main-none-eabihf;")
    print("  vectores en 0x341A0000. Secciones ALLOC del ELF:")
    for nombre, b in SECCIONES_MEDIDAS.items():
        print(f"    {nombre:34s} {b:>10,} B")
    nobits = sum(SECCIONES_MEDIDAS[n] for n in (".bss", ".uninit"))
    print(f"    {'cargable':34s} {BINARIO_HUB_B - nobits:>10,} B")
    print(f"    {'NOBITS (tambien ocupa SRAM)':34s} {nobits:>10,} B")
    print(f"    {'TOTAL RESIDENTE':34s} {BINARIO_HUB_B:>10,} B")
    print(f"  El ELF en disco pesa {ELF_EN_DISCO_B:,} B: debug = 2.")
    print("  El archivo NO es la huella. Es un PISO medido, no una cota superior.")
    print("  Tiene USB device, protocolo, modelo, servidor, descubrimiento")
    print("  y pinout: la parte compartida. NO tiene motores de audio,")
    print("  ni pila grafica del LTDC, ni pegamento de NPU, ni driver de SPI")
    print("  del J2, ni XSPI/PSRAM. Falta firmware; no se presume su tamano.")
    print(f"  La punta baja del viejo ESTIMADO era "
          f"{BINARIO_ANTERIOR_B[0] / BINARIO_HUB_B:.1f}x esta huella.")

    print("\n  Lo fijo que sigue ESTIMADO, sin medida ni tamanos publicados:")
    for nombre, (lo, hi) in (("colas de audio y retardos", COLAS_B),
                            ("activaciones de la NPU (gestos)", NPU_ACTIVACIONES_B),
                            ("cuadros de camara (DCMIPP, doble)", FRAMES_CAMARA_B)):
        print(f"    {nombre:34s} {lo:>10,} - {hi:,} B")
    ancho = sum(hi - lo for lo, hi in
                (COLAS_B, NPU_ACTIVACIONES_B, FRAMES_CAMARA_B))
    print(f"  Amplitud combinada: {ancho:,} B; EXACTAMENTE la del viejo")
    print("  rango del binario. Decir que el binario decidia solo ya era")
    print("  sobreafirmar antes de medirlo: las otras tres filas movian igual.")

    print(f"\n  D3P_FIRMADA = {D3P_FIRMADA}: pendiente en la firma de hub S0.")
    print("  CONTRADICCION: S10 fila 2 cobra NPU y camara al hub; fila 11")
    print("  se las da al mago. Aqui se cobran hasta firma; el papel decide.")
    print(f"  AUDIO_EN_EL_HUB = {AUDIO_EN_EL_HUB}: S6.2 no eligio el chip.")
    print("  Falta el papel propio de la interfaz; mientras tanto se cobra.")
    print(f"  Lo fijo por defecto: {fijo_b(False):,} - {fijo_b(True):,} B.")
    print("  Escenarios EXPLICITOS, sin convertirlos en decisiones:")
    for d3p in (False, True):
        for audio in (False, True):
            print(f"    D3-prima={str(d3p):5s}, audio={str(audio):5s}: "
                  f"{fijo_b(False, d3p=d3p, audio=audio):>10,} - "
                  f"{fijo_b(True, d3p=d3p, audio=audio):,} B")

    print("\n  El framebuffer, por formato (800x480, DS 3.29):")
    for nombre, bpx in FORMATOS.items():
        s, d = framebuffer_b(bpx, False), framebuffer_b(bpx, True)
        print(f"    {nombre:20s} simple {s:>9,} B   doble {d:>9,} B "
              f"({100*d/SRAM_B:.0f} % de la SRAM)")

    print("\n  LO QUE QUEDA AL LADO DEL FRAMEBUFFER, pendientes conservadores:")
    print("  Se cobra el piso medido y los ESTIMADO; la demanda propia falta.")
    print(f"    {'framebuffer':32s} {'mejor caso':>14s} {'peor caso':>14s}"
          f"  {'techo binario':>14s}")
    configuraciones = [(f"{n}, {'doble' if d else 'simple'}", bpx, d)
                       for n, bpx in FORMATOS.items() for d in (False, True)]
    configuraciones.append(("framebuffer FUERA (PSRAM propia)", 0, False))
    for nombre, bpx, doble in configuraciones:
        techo = techo_binario_b(bpx, doble)
        print(f"    {nombre:32s} {libre_b(bpx, doble, False):>14,} "
              f"{libre_b(bpx, doble, True):>14,}  {techo:>14,}")
    print("  Todos los techos salen de fijo_b(), con el binario puesto a")
    print("  cero y el resto en peor caso. Son condicionales: demanda")
    print(f"  ENUMERADA = {demanda_hub_b():,} B, "
          f"DEMANDA_HUB_ENUMERADA = {DEMANDA_HUB_ENUMERADA}.")
    print("  Una celda positiva no es VERDE: nadie ha escrito cuanto pide")
    print("  la UI residente ni que falta de protocolo y DMA fuera del ELF.")

    print("\n  El framebuffer PUEDE vivir fuera de la SRAM: el LTDC lee por")
    print("  AXI con rafagas de 64/128 B y la GPU trae dos interfaces AXI de")
    print("  64 bits 'for texture and framebuffer access' (DS 3.29/3.30), y")
    print("  el XSPI mapea la PSRAM en memoria. Eso NO es gratis: muda el")
    print("  problema de bytes a CAUDAL. Hub S10 fila 2 lo sienta en PSRAM")
    print("  propia, sin sampler; la contencion con granos que calcula")
    print("  psram_budget.py pertenece al escenario integrado anterior.")
    print("  Su verde no mide el bus del hub ni cierra su demanda residente.")


def _autocomprobacion() -> None:
    # Cuentas a mano contra pantalla S1 / micro_budget y medida del ELF:
    # 800x480x2 = 768000; doble RGB888 = 2304000. No sumas de constantes.
    assert framebuffer_b(2, False) == 768_000
    assert framebuffer_b(3, True) == 2_304_000
    assert BINARIO_HUB_B == 82_280  # Medida ALLOC del 2026-09-09, c521302.
    # Las tres horquillas heredadas movian tanto como la del binario viejo.
    ancho = sum(hi - lo for lo, hi in
                (COLAS_B, NPU_ACTIVACIONES_B, FRAMES_CAMARA_B))
    assert ancho == BINARIO_ANTERIOR_B[1] - BINARIO_ANTERIOR_B[0], (
        "las otras tres horquillas ya no igualan a la del binario viejo: "
        "releer la comparacion historica que este censo publica")
    # Asercion INVERSA: si ni quitando el framebuffer cabe lo ENUMERADO,
    # la demanda sin escribir estaria tapando un ROJO que ya es demostrable.
    guarda_hub(parametros())


def main() -> int:
    _autocomprobacion()
    demo()
    if not DEMANDA_HUB_ENUMERADA:
        print("\nHUECO: lo que el hub necesita residente al lado del framebuffer")
        print("no lo ha escrito nadie. Cero enumera la lista vacia; no mide")
        print("la necesidad. La tabla Serum y el sample son de la Voz.")
        print("Se cierra enumerando esa demanda en papel, midiendo el firmware")
        print("que la implemente y recorriendo el mismo censo. D3-prima y el")
        print("audio conservan sus duenos y sus pendientes: no se firman aqui.")
        print("HUECO: demanda residente del hub sin enumerar; binario = PISO medido")
        return 2
    # Enumerar la lista no convierte el ELF parcial en firmware terminado.
    print("HUECO: binario del hub = PISO medido; falta medir el firmware completo")
    return 2


# ---------------------------------------------------------------------------
# LO QUE ESTE CALCULO **NO** CUBRE
#
#   * EL MAPA DEL LINKER. Este censo reparte BYTES, no direcciones. Los
#     bancos, su colocacion respecto a TCM, las pilas y la contencion entre
#     LTDC, DMA del J2 y lo que finalmente cuelgue aqui necesitan mapa y
#     ensayo concurrente. El total decimal del DS no demuestra colocacion.
#
#   * EL FIRMWARE TERMINADO. La medida ALLOC ya incluye .data, .bss y
#     .uninit: no se deben cobrar otra vez al enumerar los residentes. El
#     incremento por grafica, SPI del J2, XSPI y, si quedan aqui, audio y
#     NPU no tiene cifra. Las colas heredadas son reserva conservadora,
#     no una medida de la interfaz multicanal ni un desglose del ELF.
#
#   * LA DEMANDA PROPIA. La puerta queda HUECO aunque todos los saldos sean
#     positivos. Hub S3.1 hereda framebuffer; no enumera el resto de UI,
#     protocolo y DMA. Una lista vacia nunca es prueba de que alcanza.
#
#   * EL MAGO Y EL AUDIO. D3-prima requiere firma; hub S10 filas 2 y 11
#     se contradicen. Hub S6.2 necesita el papel propio de la interfaz.
#     Mostrar sus escenarios no resuelve ninguna de las dos decisiones.
#
#   * LA PSRAM DEL HUB. Sacar el framebuffer compra bytes aqui, no caudal
#     fuera. La pieza, el refresco y la contencion de este chip necesitan
#     su censo; el de los granos de la Voz no se hereda como resultado.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())
