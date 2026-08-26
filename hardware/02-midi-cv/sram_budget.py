#!/usr/bin/env python3
"""El censo de SRAM del N657: 4,2 MB para todo, y "todo" incluye el binario.

    python sram_budget.py

Spec del motor S8.5: "censo de SRAM CON EL BINARIO ADENTRO -- sin flash
interna, el firmware entero comparte los 4,2 MB con tablas, colas y
retardos". Y desde las dos actas del 2026-08-26: tambien con los buffers de
sample (tarde) y con el framebuffer de la pantalla (noche).

ESTE GUION ES UNA PUERTA. La spec de la pantalla (S1) escribio la regla:
"el conector del panel no se dibuja hasta que el censo de SRAM y la fila
LTDC de carga_motor esten verdes". Aqui esta la mitad de esa puerta.

EL DATO QUE MANDA, Y POR QUE ES INCOMODO

  El N657 NO TIENE FLASH INTERNA (spec S1, benchmark S4). El binario
  arranca desde el XSPI2 y vive en SRAM. Eso convierte una decision de
  pantalla en una decision de memoria: un doble buffer RGB888 son
  2 304 000 B, o sea el 55 % de los 4,2 MB antes de contar una sola tabla
  -- el numero que la junta de la pantalla puso sobre la mesa para exigir
  esta puerta.

LO QUE ES DATO Y LO QUE ES ESTIMADO

  DATO (fuente citada en su linea): la SRAM total y el TCM (DS p1), la
  aritmetica del framebuffer (800x480 por bytes/pixel), el tamano de una
  tabla clase Serum en f16 (spec S3: "~1 MB").

  ESTIMADO DECLARADO (sin fuente publicada, por eso rango ancho): el
  tamano del binario, las colas de audio, los retardos y las activaciones
  de la NPU. Cada uno lo dice al imprimirse. El bring-up los reemplaza por
  medidos (mapa del linker) y las aserciones siguen mandando.
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(errors="replace")

# --- lo que el chip trae (DS p1, spec S1) -----------------------------------
# El DS dice "4.2-Mbyte contiguous SRAM" sin darla en bytes. Se lee en
# DECIMAL, que es la lectura CONSERVADORA: si el mapa real de bancos suma en
# Kbytes binarios seria ~200 KB mas, y el error va en la direccion segura
# (este censo pediria de mas, no de menos). El mapa exacto es del RM0486y
# entra en el paso 2 del bring-up junto al mapa del linker.
SRAM_B = 4_200_000            # 4,2 MB contiguos
TCM_B = 192 * 1024            # 192 KB de TCM (ITCM+DTCM) -- fuera del censo:
                              # es para ISR criticas y tablas calientes

# --- la pantalla (acta camino A) --------------------------------------------
PANTALLA_ANCHO = 800
PANTALLA_ALTO = 480
FORMATOS = {                  # bytes por pixel del framebuffer (DS 3.29)
    "RGB565 (16 bits)": 2,
    "RGB888 (24 bits)": 3,
}

# --- las piezas del firmware ------------------------------------------------
TABLA_SERUM_B = 1_000_000     # spec S3: "una tabla clase Serum ~1 MB en f16"

# ESTIMADO DECLARADO -- sin fuente. Un firmware Rust con motores de audio,
# pila grafica y stack USB no tiene tamano publicado en ningun papel.
BINARIO_B = (700_000, 2_000_000)
# ESTIMADO: colas de audio (SAI in/out, CV, USB) y retardos del motor.
COLAS_B = (150_000, 400_000)
# ESTIMADO (acta de la noche + junta de la camara): activaciones del modelo
# de manos. Los PESOS no viven aqui -- se streamean desde XSPI2.
NPU_ACTIVACIONES_B = (200_000, 800_000)
# ESTIMADO: los CUADROS que el DCMIPP escribe a memoria antes de la
# inferencia. La spec de la camara (S5, fila 1) los manda a ESTE censo y la
# primera version no los tenia (hallazgo de la junta). El DCMIPP reescala en
# hardware, asi que lo que se guarda es la entrada reducida del modelo, con
# doble buffer para no leer un cuadro a medio escribir.
FRAMES_CAMARA_B = (150_000, 600_000)


def framebuffer_b(bytes_px: int, doble: bool) -> int:
    return PANTALLA_ANCHO * PANTALLA_ALTO * bytes_px * (2 if doble else 1)


def fijo_b(peor: bool) -> int:
    """Lo que no es ni framebuffer ni tablas ni samples."""
    i = 1 if peor else 0
    return (BINARIO_B[i] + COLAS_B[i] + NPU_ACTIVACIONES_B[i]
            + FRAMES_CAMARA_B[i])


def libre_b(bytes_px: int, doble: bool, peor: bool, tablas: int = 0) -> int:
    return (SRAM_B - framebuffer_b(bytes_px, doble) - fijo_b(peor)
            - tablas * TABLA_SERUM_B)


def demo() -> None:
    print("\nEL CENSO DE SRAM DEL N657 (spec S8.5)\n")
    print(f"  SRAM contigua: {SRAM_B:,} B. TCM aparte: {TCM_B:,} B (ISR")
    print("  criticas y tablas calientes por linker -- no entra al reparto).")
    print("  El chip NO tiene flash interna: el binario vive aqui dentro.\n")

    print("  Lo fijo (todo ESTIMADO, sin fuente publicada):")
    for nombre, (lo, hi) in (("binario del firmware", BINARIO_B),
                             ("colas de audio y retardos", COLAS_B),
                             ("activaciones de la NPU (gestos)",
                              NPU_ACTIVACIONES_B),
                             ("cuadros de camara (DCMIPP, doble buffer)",
                              FRAMES_CAMARA_B)):
        print(f"    {nombre:34s} {lo:>10,} - {hi:,} B")
    print(f"    {'CENTRAL':34s} {fijo_b(False):>10,} - {fijo_b(True):,} B")

    print("\n  El framebuffer, por formato (800x480, DS 3.29):")
    for nombre, bpx in FORMATOS.items():
        s, d = framebuffer_b(bpx, False), framebuffer_b(bpx, True)
        print(f"    {nombre:20s} simple {s:>9,} B   doble {d:>9,} B "
              f"({100*d/SRAM_B:.0f} % de la SRAM)")

    print("\n  LO QUE QUEDA PARA TABLAS Y SAMPLES, por configuracion:")
    print(f"    {'framebuffer':32s} {'mejor caso':>14s} {'peor caso':>14s}"
          f"  {'tablas Serum':>13s}")
    for nombre, bpx in FORMATOS.items():
        for doble in (False, True):
            et = f"{nombre}, {'doble' if doble else 'simple'}"
            mejor = libre_b(bpx, doble, peor=False)
            peor = libre_b(bpx, doble, peor=True)
            n_tab = max(0, peor // TABLA_SERUM_B)
            print(f"    {et:32s} {mejor:>14,} {peor:>14,}"
                  f"  {n_tab:>10d}")

    print("\n  LA PUERTA DE LA PANTALLA (spec pantalla S1): el conector del")
    print("  panel no se dibuja hasta que esto este verde. Y VERDE lo define")
    print("  ESTE guion, no la spec (que solo manda la puerta): queda sitio")
    print("  para al menos UNA tabla residente -- el minimo que motor S3")
    print("  publica ('entre 1 y 3') -- mas un buffer de sample de trabajo,")
    print("  en el PEOR caso de lo fijo.\n")
    pide = TABLA_SERUM_B + MINIMO_SAMPLE_B
    for nombre, bpx in FORMATOS.items():
        for doble in (False, True):
            peor = libre_b(bpx, doble, peor=True)
            et = f"{nombre}, {'doble' if doble else 'simple'}"
            print(f"    {et:32s} {'VERDE' if peor >= pide else 'ROJO '}  "
                  f"queda {peor:>10,} B (pide {pide:,})")
    print(f"    {'framebuffer FUERA (en la PSRAM)':32s} "
          f"{'VERDE' if libre_b(0, False, True) >= pide else 'ROJO '}  "
          f"queda {libre_b(0, False, True):>10,} B (pide {pide:,})")

    print("\n  EL NUMERO QUE DECIDE, Y NADIE HA MEDIDO: el binario.")
    print("  Es el ESTIMADO mas gordo de este censo y el que mueve el")
    print("  veredicto entero. Cuanto puede pesar como MAXIMO para que cada")
    print("  configuracion cierre (con el resto de lo fijo en su peor caso):")
    resto_peor = COLAS_B[1] + NPU_ACTIVACIONES_B[1]
    for nombre, bpx in FORMATOS.items():
        for doble in (False, True):
            techo = SRAM_B - framebuffer_b(bpx, doble) - resto_peor - pide
            et = f"{nombre}, {'doble' if doble else 'simple'}"
            v = f"{techo:,} B" if techo > 0 else "IMPOSIBLE"
            print(f"    {et:32s} binario <= {v}")
    techo_psram = SRAM_B - resto_peor - pide
    print(f"    {'framebuffer FUERA (en la PSRAM)':32s} "
          f"binario <= {techo_psram:,} B")
    print("\n  El framebuffer PUEDE vivir fuera de la SRAM: el LTDC lee por")
    print("  AXI con rafagas de 64/128 B y la GPU trae dos interfaces AXI de")
    print("  64 bits 'for texture and framebuffer access' (DS 3.29/3.30), y")
    print("  el XSPI mapea la PSRAM en memoria. Eso NO es gratis: muda el")
    print("  problema de bytes a CAUDAL, y el caudal lo mide psram_budget.py")
    print("  contra los granos del sampler. Es decision de arquitectura con")
    print("  numero, no atajo -- y no se toma en este guion.")

    print("\n  EL SAMPLER EN SRAM, contra la vara del EP-133:")
    peor_16s = libre_b(2, False, peor=True) - TABLA_SERUM_B
    seg = peor_16s / (F_MUESTRA_SAMPLE * BYTES_POR_MUESTRA)
    print(f"    con RGB565 simple y una tabla residente quedan "
          f"{peor_16s:,} B")
    print(f"    = {seg:.0f} s de audio a {F_MUESTRA_SAMPLE/1000:.0f} kHz "
          f"/ {BYTES_POR_MUESTRA*8} bits mono, EN LA SRAM DEL CHIP")
    print(f"    El EP-133 K.O. II tiene {EP133_B:,} B para TODO su universo")
    print(f"    ({EP133_SLOTS} slots, {EP133_KHZ} kHz / {EP133_BITS} bits, sin")
    print("    expansion). La SRAM no es donde competimos: la mesa de trabajo")
    print("    es la PSRAM (psram_budget.py) y el catalogo es el XSPI2.")


# --- la vara del EP-133 (pagina oficial de Teenage Engineering, verificada
#     2026-08-26; acta de Samuel: "tenemos que minimo alcanzar la memoria de
#     ellos") -----------------------------------------------------------------
EP133_B = 128 * 1024 * 1024
EP133_SLOTS = 999
EP133_KHZ = 46
EP133_BITS = 16
F_MUESTRA_SAMPLE = 48000.0
BYTES_POR_MUESTRA = 2

# Lo minimo que un sampler necesita residente en SRAM para trabajar aunque
# todo lo demas se streamee: ESTIMADO DECLARADO.
MINIMO_SAMPLE_B = 256_000


def _autocomprobacion() -> None:
    # 1. La aritmetica del framebuffer contra la cifra que el propio repo
    #    publica en micro_budget (768 000 B a 2 B/px).
    assert framebuffer_b(2, False) == 768_000
    assert framebuffer_b(3, True) == 2_304_000
    # 2. El numero que motivo la puerta: el doble buffer RGB888 pasa del
    #    50 % de la SRAM. Si dejara de ser verdad, la puerta se relee.
    assert framebuffer_b(3, True) / SRAM_B > 0.50
    # 3. Lo fijo tiene que ser rango, no punto: un ESTIMADO sin ancho es un
    #    numero disfrazado.
    assert fijo_b(True) > fijo_b(False) * 1.5
    # 4. El binario tiene que seguir siendo el ESTIMADO mas ancho -- es la
    #    conclusion que este censo publica ("el mayor desconocido"), y deja
    #    de ser cierta el dia que otra fila crezca mas. (La junta tumbo la
    #    version anterior de este pin: comparaba una resta contra si misma.)
    anchos = {"binario": BINARIO_B[1] - BINARIO_B[0],
              "colas": COLAS_B[1] - COLAS_B[0],
              "npu": NPU_ACTIVACIONES_B[1] - NPU_ACTIVACIONES_B[0],
              "frames": FRAMES_CAMARA_B[1] - FRAMES_CAMARA_B[0]}
    assert max(anchos, key=anchos.get) == "binario", (
        f"el binario dejo de ser el ESTIMADO mas ancho ({anchos}): la "
        f"conclusion que este censo publica hay que reescribirla")
    # 5. La vara del EP-133, tal como su pagina la publica -- escrita en
    #    forma distinta al dato para que un find-replace no mueva las dos.
    assert EP133_B == 134_217_728


def main() -> int:
    _autocomprobacion()
    demo()

    pide = TABLA_SERUM_B + MINIMO_SAMPLE_B

    # Asercion INVERSA que vigila el supuesto comodo: si algun dia el doble
    # buffer RGB888 cerrara en SRAM en el peor caso, es NOTICIA -- se relee
    # la puerta de la pantalla con el numero nuevo, no se hereda el miedo.
    assert libre_b(3, True, peor=True) < pide, (
        "el doble buffer RGB888 ya cabe en SRAM con el peor caso de lo "
        "fijo: releer la puerta de la pantalla (S1) -- la restriccion que "
        "la motivo dejo de existir")

    # Asercion INVERSA de la otra punta: en el MEJOR caso tiene que caber
    # algo. Si ni el mejor caso cerrara, el hueco de abajo estaria tapando
    # un rojo de verdad y habria que decirlo con esa palabra.
    assert libre_b(2, False, peor=False) >= pide, (
        "ni en el mejor caso de los ESTIMADO cabe la pantalla mas barata "
        "con una tabla: esto ya no es un hueco, es un ROJO -- caer al "
        "camino B (spec pantalla S1)")

    cierra = [f"{n}, {'doble' if d else 'simple'}"
              for n, bpx in FORMATOS.items() for d in (False, True)
              if libre_b(bpx, d, peor=True) >= pide]
    if cierra:
        print(f"\n  configuraciones que cierran en SRAM: {', '.join(cierra)}")
        print("\nOK: presupuesto cerrado.")
        return 0

    # HUECO, no ROJO -- y la diferencia importa. El dato que decide (el
    # binario) NO ESTA MEDIDO: sale del mapa del linker en el paso 2 del
    # bring-up. Declarar verde seria mentir; declarar rojo seria condenar la
    # pantalla con un numero inventado. Se declara el hueco con su salida
    # escrita -- Principio V: un fallo invisible es peor que un hueco
    # visible.
    solo_motor = libre_b(0, False, peor=True)
    print("\nHUECO: el censo no cierra, y su dato dominante no esta medido.")
    print(f"Con el PEOR caso de los ESTIMADO lo fijo se come "
          f"{fijo_b(True):,} B de {SRAM_B:,}, y entonces NO CIERRA NI SIN")
    print(f"PANTALLA (quedan {solo_motor:,} B y el motor pide {pide:,}).")
    print("O sea: el hallazgo de este censo no es de pantalla, es que **el")
    print("tamano del binario es hoy el mayor desconocido del motor**, y")
    print("decide mas que cualquier eleccion de framebuffer. En el mejor")
    print(f"caso sobra de sobra ({libre_b(2, False, peor=False):,} B con")
    print("RGB565 simple): entre las dos puntas cabe todo el diseno o nada,")
    print("y eso no se resuelve opinando. Tres salidas, ninguna se elige")
    print("aqui:")
    print("  1. MEDIR el binario (bring-up paso 2, Nucleo) y recorrer este")
    print("     censo. Es la unica que quita el hueco de raiz.")
    print("  2. MUDAR el framebuffer a la PSRAM -- en bytes cabe de sobra,")
    print("     y el precio pasa a ser caudal (psram_budget.py). Sube el")
    print("     techo del binario a {:,} B.".format(
        SRAM_B - COLAS_B[1] - NPU_ACTIVACIONES_B[1] - pide))
    print("  3. CAER al camino B (spec pantalla S1) si 1 y 2 fallan.")
    print("La puerta del conector del panel sigue CERRADA hasta que una de")
    print("las tres cierre con numero.")
    # La ultima linea es la que el resumen de gates.py se lleva: que diga
    # el hallazgo entero, no la cola de un parrafo.
    print(f"HUECO: el binario sin medir manda este censo (peor caso: lo "
          f"fijo pide {fijo_b(True):,} de {SRAM_B:,} B y no cierra ni sin "
          f"pantalla); tres salidas escritas, ninguna elegida sin acta")
    return 2


# ---------------------------------------------------------------------------
# LO QUE ESTE CALCULO **NO** CUBRE
#
#   * EL MAPA DEL LINKER. Este censo reparte BYTES, no direcciones. Que el
#     framebuffer y las colas de audio caigan en bancos distintos para no
#     pelearse en el bus es colocacion por linker, y es la fila 5 de riesgos
#     (soak concurrente con el LTDC refrescando).
#
#   * EL TAMANO REAL DEL BINARIO. Es el ESTIMADO mas gordo de aqui y el que
#     mas mueve el veredicto. Se mide en el primer arranque en la Nucleo
#     (orden del bring-up, paso 2) y este guion se recorre con el numero.
#
#   * EL CATALOGO DE SAMPLES. No vive aqui: vive en el XSPI2 (biblioteca,
#     no volatil) y su mesa de trabajo en la PSRAM del XSPI1. La vara del
#     EP-133 se contesta alli -- ver psram_budget.py.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())
