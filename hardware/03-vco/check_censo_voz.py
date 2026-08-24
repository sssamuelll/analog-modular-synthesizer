"""Censo del modulo de Voz: parametros, descriptor y memoria.

    python check_censo_voz.py

BLOQUEANTE (modulo-voz-total S7 y S9.4). Cuenta lo que el modulo tiene que
poder NOMBRAR, no lo que tiene que poder sonar, y lo compara contra tres techos
que ya estan escritos en cobre y en codigo:

  1. MAX_PARAMS = 512   software/nucleo/core/src/modelo.rs:9
  2. 128 KB de EEPROM   acta E-7 (eran 32 KB hasta que este censo corrio)
  3. largo del blob u8  software/nucleo/core/src/descubrimiento.rs:87

Los tres se miden aqui. Dos de ellos NO pasan, y no pasan a proposito: la spec
ya declara los cambios 2, 12 y 18 del nucleo como PRERREQUISITO BLOQUEANTE.
Este guion existe para que ese "bloqueante" sea un numero y no un adjetivo.

--- De donde sale cada cuenta ----------------------------------------------

Todo esta citado o derivado de cifras publicadas:

  * 226 parametros del modulo v2 y "+9 por canal" -> voz-total S7, tabla
  * ~42 B por entrada de descriptor y ~3 000 B de etiquetas -> dieciseis S13
  * 84 notas x 16 osciladores x 16 bits de calibracion -> dieciseis S13
  * ~1,6 KB de curvas de caracterizacion -> voz-total S7
  * el resto hasta los ~520 que S7 declara se atribuye a aristas y vinculos

--- Lo que NO esta confirmado ----------------------------------------------

  * El reparto aristas/vinculos esta DERIVADO hacia atras del total que la
    spec publica, no contado pieza a pieza. Cuando el esquema del cambio 15
    exista, se cuenta de verdad y esta constante muere.
  * El parametro de paneo por canal se cuenta como UNO. Si el diseno acaba
    queriendo posicion y anchura por voz, son dos.
"""
from __future__ import annotations

# --- techos que ya existen (citados) ----------------------------------------
def _max_params_del_cobre() -> int:
    """MAX_PARAMS se LEE de modelo.rs. No se copia.

    Tenerlo escrito aqui tambien era una segunda fuente de verdad, la misma
    trampa que el `- 15` del canto de la trasera: copiado en cinco sitios, y
    el dia que uno cambia los otros mienten en silencio. Aqui era peor,
    porque este guion es LA PUERTA: si el numero se queda viejo, la puerta
    jura que el modelo no cabe cuando ya cabe, o al reves.
    """
    import pathlib
    import re
    src = (pathlib.Path(__file__).resolve().parents[2]
           / "software" / "nucleo" / "core" / "src" / "modelo.rs")
    m = re.search(r"pub const MAX_PARAMS: usize = ([0-9]+);",
                  src.read_text(encoding="utf-8"))
    assert m, f"no encuentro MAX_PARAMS en {src}"
    return int(m.group(1))


MAX_PARAMS = _max_params_del_cobre()        # LEIDO de modelo.rs, no copiado

# MAX_PARAMS es del INSTRUMENTO ENTERO y este censo solo cuenta la Voz total.
# Lo que sobre tiene que alcanzarle al cerebro, la bahia, el modulo de mandos,
# la telemetria de la fuente y los invitados de la fila B.
#
# DECLARADO, no medido: no existe censo a nivel de instrumento. Es lo que este
# guion exige que quede libre despues de meter la Voz. El dia que ese censo
# exista, esta constante muere.
RESERVA_RESTO_INSTRUMENTO = 256
EEPROM_B = 128 * 1024       # acta E-7: 24AA1025. Eran 32 KB (24AA256UID)
                            # hasta que este censo dio 91 % de ocupacion.
MARGEN_MIN = 0.30           # tiene que sobrar al menos un 30 %: el censo se
                            # movio 21,7 % en una sola sesion (acta E-5/E-6)
CANDIDATAS_KB = (32, 64, 128, 256)

# El numero que DECIDE el tamano no es cuantos parametros caben: es cuantos
# bytes ocupa la entrada de cada uno. Hoy son 42 (dieciseis S13), pero el
# descriptor no es un dato interno -- architecture-compute S6: "los nombres y
# las unidades de cada parametro no son cosmetica: son la documentacion que el
# modelo va a leer". Nombre legible + unidad + rango + defecto + una linea de
# que hace no caben en 42 B.
B_POR_ENTRADA_RICO = 100    # OBJETIVO DECLARADO, no medido
BLOB_U8_TECHO = 238         # descubrimiento.rs: u8 con FIN_ZONA_LIBRE = 0xFA

# --- el censo de parametros -------------------------------------------------
CANALES = 16
BASE_V2 = 226               # voz-total S7: parametros escribibles de #164
POR_CANAL = 9               # voz-total S7: "+9/canal x16"
ARISTAS_Y_VINCULOS = 150    # DERIVADO: resto hasta los ~520 que S7 declara
PANEO_POR_CANAL = 1         # acta E-6: el sitio de la voz en el estereo

# --- el descriptor y la memoria (citados de dieciseis S13) ------------------
B_POR_ENTRADA = 42          # "~300 entradas x ~42 B"
B_ETIQUETAS = 3_000         # "los selectores de fuente son enumerados de 17"
NOTAS_CAL = 84
OSC = 16
B_POR_PUNTO_CAL = 2         # 16 bits
B_CURVAS_FILTRO = 1_600     # voz-total S7: "+ curvas (~1,6 KB)"


def params(con_estereo: bool) -> int:
    n = BASE_V2 + POR_CANAL * CANALES + ARISTAS_Y_VINCULOS
    if con_estereo:
        n += PANEO_POR_CANAL * CANALES
    return n


def calibracion() -> int:
    return NOTAS_CAL * OSC * B_POR_PUNTO_CAL


def eeprom(con_estereo: bool) -> dict:
    return {
        "calibracion de afinado": calibracion(),
        "descriptor": params(con_estereo) * B_POR_ENTRADA,
        "etiquetas de enumerados": B_ETIQUETAS,
        "curvas de caracterizacion": B_CURVAS_FILTRO,
    }


def demo() -> None:
    print("Censo del modulo de Voz\n")

    # --- 1. parametros contra el modelo del nucleo ------------------------
    print("parametros escribibles:\n")
    print(f"  base del modulo v2 (#164)        {BASE_V2:5d}")
    print(f"  + {POR_CANAL} por canal x {CANALES}            "
          f"{POR_CANAL * CANALES:5d}")
    print(f"  + aristas y vinculos (DERIVADO)  {ARISTAS_Y_VINCULOS:5d}")
    print(f"  = sin estereo                    {params(False):5d}")
    print(f"  + paneo, {PANEO_POR_CANAL} por canal (E-6)      "
          f"{PANEO_POR_CANAL * CANALES:5d}")
    print(f"  = CON estereo                    {params(True):5d}")

    n = params(True)
    necesario = n + RESERVA_RESTO_INSTRUMENTO
    holgura = MAX_PARAMS - necesario
    print()
    print(f"  techo del modelo: MAX_PARAMS = {MAX_PARAMS} "
          f"(LEIDO de modelo.rs)")
    print(f"  este modulo, con estereo         {n:5d}")
    print(f"  + reserva del resto (DECLARADO)  {RESERVA_RESTO_INSTRUMENTO:5d}")
    print(f"  = hace falta                     {necesario:5d}")
    if holgura >= 0:
        print(f"  ->  contra {MAX_PARAMS}: sobran {holgura} "
              f"({necesario/MAX_PARAMS:.0%} ocupado)")
    else:
        print(f"  ->  contra {MAX_PARAMS}: FALTAN {-holgura}  <<< ROJO")
    assert necesario <= MAX_PARAMS, (
        f"el modelo no aguanta el instrumento: la Voz total son {n} "
        f"parametros y la reserva declarada para todo lo demas (cerebro, "
        f"bahia, mandos, telemetria, invitados) son "
        f"{RESERVA_RESTO_INSTRUMENTO}, o sea {necesario} contra un "
        f"MAX_PARAMS de {MAX_PARAMS}. Sube MAX_PARAMS en modelo.rs: son 8 B "
        f"por ranura (&'static Descriptor + Valor = i32), la busqueda es "
        f"binaria sobre el conteo REAL y no sobre la capacidad, asi que "
        f"subirlo NO cuesta tiempo de ejecucion -- solo "
        f"{8 * (necesario - MAX_PARAMS)} B mas de SRAM de los 520 KB del "
        f"RP2350B")
    print("  OJO: este censo es de UN modulo y el techo es del INSTRUMENTO.")
    print("  No existe censo a nivel de instrumento: la reserva de arriba es")
    print("  DECLARADA, y ese censo es el que la mata.")

    # --- 2. la memoria ----------------------------------------------------
    print(f"\nmemoria del modulo, contra los {EEPROM_B//1024} KB elegidos:\n")
    e = eeprom(True)
    total = sum(e.values())
    for k, v in sorted(e.items(), key=lambda kv: -kv[1]):
        print(f"  {k:28s} {v:7d} B  ({v/EEPROM_B:5.1%})")
    print(f"  {'TOTAL':28s} {total:7d} B  ({total/EEPROM_B:5.1%})")

    sin = sum(eeprom(False).values())
    print(f"\n  sin estereo serian {sin} B ({sin/EEPROM_B:.1%}): el paneo "
          f"cuesta {total - sin} B")
    fijo = total - e["descriptor"]
    print()
    print("cuanto descriptor aguanta cada tamano, que es lo que decide:")
    print()
    print(f"  {'':7s} {'B por entrada':>14s}   con el objetivo declarado de "
          f"{B_POR_ENTRADA_RICO} B")
    for kb in CANDIDATAS_KB:
        util = kb * 1024 * (1 - MARGEN_MIN)
        techo = (util - fijo) / n
        rico = fijo + n * B_POR_ENTRADA_RICO
        veredicto = "cabe" if rico <= util else "NO CABE"
        marca = "  <- elegido" if kb * 1024 == EEPROM_B else ""
        print(f"  {kb:3d} KB {techo:11.1f} B    {rico:7d} B de {util:7.0f} "
              f"utiles  {veredicto:7s}{marca}")
    print()
    print(f"  hoy la entrada son {B_POR_ENTRADA} B ({total} B en total).")

    assert total <= EEPROM_B * (1 - MARGEN_MIN), (
        f"no cabe ni hoy: {total} B contra "
        f"{EEPROM_B * (1 - MARGEN_MIN):.0f} B utiles")
    assert fijo + n * B_POR_ENTRADA_RICO <= EEPROM_B * (1 - MARGEN_MIN), (
        "el tamano elegido no aguanta el descriptor rico, que es la razon "
        "por la que se eligio")
    assert fijo + n * B_POR_ENTRADA_RICO > 64 * 1024 * (1 - MARGEN_MIN), (
        "si 64 KB aguantara el descriptor rico, el acta E-7 estaria eligiendo "
        "128 sin motivo y habria que revisarla: el 1025 cuesta la costura "
        "del bloque en firmware")

    # --- 3. el techo que rompe primero ------------------------------------
    desc = e["descriptor"] + e["etiquetas de enumerados"]
    print(f"\nel largo del blob se lee como u8 "
          f"(descubrimiento.rs, techo {BLOB_U8_TECHO} B):")
    print(f"  el descriptor son {desc} B  ->  {desc/BLOB_U8_TECHO:.0f}x el "
          "techo  <<< ROJO")
    assert desc > BLOB_U8_TECHO * 50, (
        "el desbordamiento tiene que ser de orden, no de detalle: es el "
        "cambio 18 (u8 -> u16)")
    print("  Es el cambio 18. Sin el, la identidad del modulo literalmente no")
    print("  cabe por el camino que la lee.")
    print()
    print("  PERO OJO, y esto lo corrigio la v2 del pase del nucleo: este")
    print("  guion compara el descriptor contra el largo de blob de 1 byte de")
    print("  descubrimiento.rs, y son magnitudes SIN RELACION. Ese byte mide el")
    print("  blob de CALIBRACION en la EEPROM de identidad del modulo; el")
    print("  descriptor no pasa por ahi, sale por SysEx. El techo real es")
    print("  fw/src/usb.rs:159, `[0u8; 256]` POR DESCRIPTOR, y el `?` de la 162")
    print("  aborta el volcado ENTERO en silencio si uno solo se pasa (#182,")
    print("  fallo 5). La comparacion correcta es la entrada MAS GRANDE contra")
    print("  256 B, y ese numero no esta medido: no se fabrica aqui.")

    print()
    print("VEREDICTO: la memoria cabe, el modelo YA CABE, el descriptor no.")
    print("  Eran tres techos con dos en rojo. El del modelo se cerro el")
    print("  2026-08-24 subiendo MAX_PARAMS de 512 a 1024 en modelo.rs, que")
    print("  cuesta 4 KB mas de SRAM y cero tiempo de ejecucion. Queda uno:")
    print(f"    MAX_PARAMS   {n} + {RESERVA_RESTO_INSTRUMENTO} de reserva "
          f"= {necesario} de {MAX_PARAMS}   (sobran {holgura})")
    print(f"    blob u8      {desc} B de {BLOB_U8_TECHO} B   "
          f"({desc/BLOB_U8_TECHO:.0f}x)   <- ver la nota de arriba")
    print(f"    EEPROM       {total} B de {EEPROM_B} B   "
          f"({total/EEPROM_B:.0%})")
    print()
    print("OK: censo cerrado.")


if __name__ == "__main__":
    demo()
