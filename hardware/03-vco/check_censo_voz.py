"""Censo del modulo de Voz: parametros, descriptor y memoria.

    python check_censo_voz.py

BLOQUEANTE (modulo-voz-total S7 y S9.4). Cuenta lo que el modulo tiene que
poder NOMBRAR, no lo que tiene que poder sonar, y lo compara contra tres techos
que ya estan escritos en cobre y en codigo:

  1. MAX_PARAMS         software/nucleo/core/src/modelo.rs      (LEIDO de ahi)
  2. 128 KB de EEPROM   acta E-7 (eran 32 KB hasta que este censo corrio)
  3. MAX_DESCRIPTOR_B   software/nucleo/core/src/descriptor.rs  (LEIDO de ahi)

Los dos primeros se miden AQUI, con assert, y los dos pasan. El tercero se
NOMBRA aqui y se mide en core: es un maximo POR DESCRIPTOR, y los descriptores
de la Voz todavia no existen como tales, asi que este guion no tiene con que
aseverarlo. Dice que falta y quien lo mide; no lo finge.

--- El techo 3 era otro, y era invalido -----------------------------------

Hasta el 2026-08-24 el tercer techo era el largo de blob de 1 byte de
descubrimiento.rs, y esa comparacion no existe: ese byte mide el blob de
CALIBRACION de la EEPROM de identidad de la placa, y el descriptor no pasa por
ahi -- sale por SysEx. Lo peor no es que estuviera mal: es que la correccion se
escribio en un print quince lineas DEBAJO del assert que la aseveraba, y el
assert se quedo vivo bloqueando el push contra una relacion que su propio autor
ya habia declarado inexistente. Encima fallaba al reves: saltaba si el
descriptor MEJORABA. Se borro.

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
def _const_del_cobre(archivo: str, nombre: str) -> int:
    """Lee `pub const <nombre>: usize = N;` de un fuente de core. No se copia.

    Tenerlo escrito aqui tambien era una segunda fuente de verdad, la misma
    trampa que el `- 15` del canto de la trasera: copiado en cinco sitios, y
    el dia que uno cambia los otros mienten en silencio. Aqui era peor,
    porque este guion es LA PUERTA: si el numero se queda viejo, la puerta
    jura que el modelo no cabe cuando ya cabe, o al reves.
    """
    import pathlib
    import re
    src = (pathlib.Path(__file__).resolve().parents[2]
           / "software" / "nucleo" / "core" / "src" / archivo)
    m = re.search(rf"pub const {nombre}: usize = ([0-9]+);",
                  src.read_text(encoding="utf-8"))
    assert m, f"no encuentro {nombre} en {src}"
    return int(m.group(1))


MAX_PARAMS = _const_del_cobre("modelo.rs", "MAX_PARAMS")
# El techo REAL del descriptor: el buffer del volcado de `mandar_descriptores`
# (fw/src/usb.rs) lo lee de aqui en vez de repetir el 256 por su cuenta, y este
# guion tambien. Es POR DESCRIPTOR, no por volcado entero.
MAX_DESCRIPTOR_B = _const_del_cobre("descriptor.rs", "MAX_DESCRIPTOR_B")

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
B_POR_ENTRADA_RICO = 100    # OBJETIVO DECLARADO, no medido. Y es una MEDIA
                            # para el presupuesto de EEPROM: no dice nada del
                            # maximo por entrada, que es otro techo (el 3)
MAS_GORDO_HOY_B = 106       # CITADO: descriptor.rs, comentario de
                            # OCUPACION_MAX_B, MEDIDO el 2026-08-24 --
                            # "cuantizacion global", de los que YA existen

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

    # ENMIENDA 2026-08-26 -- FALTA UN INQUILINO ENTERO, Y SE DICE AQUI.
    #
    #   Fila mandada del mapa de motor-digital §9: "los parametros del motor
    #   entran al censo contra el techo reventado". El motor digital del N657
    #   (FM, wavetable, espectral, granular, sampler) pide "decenas de
    #   parametros direccionables" -- palabras del papel, motor-digital §3 --
    #   y a este censo NO HA ENTRADO NI UNO.
    #
    #   NO SE INVENTA LA CIFRA. "Decenas" no es un numero, y meter aqui un 40
    #   o un 80 a ojo seria fabricar el dato que este guion existe para vigilar.
    #   Lo que se hace es lo unico honesto: contarlo como AUSENTE y visible.
    #
    #   Y hay mas de un inquilino sin contar: el mapeo de gestos de la camara
    #   (que destino mueve cada mano, con que profundidad, y si esta activo)
    #   tiene fila mandada en el mismo #172 desde el acta de la camara.
    #
    #   Ojo con la lectura facil de la holgura de abajo: los 232 que "sobran"
    #   son ANTES de meter al motor y a los gestos. No son margen: son la
    #   habitacion de dos inquilinos que todavia no han llegado.
    MOTOR_SIN_CENSAR = True

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
        f"{8 * (necesario - MAX_PARAMS)} B mas de SRAM; el STM32N657 tiene "
        f"4.2 Mbytes de SRAM de sistema (DS14791 Rev 10, Tabla 5, p. 21; "
        f"sec. 3.1, p. 23)")
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

    # --- 3. el techo del descriptor: SIN MEDIR, y por eso sin assert -------
    #
    # Aqui vivia un assert (`desc > BLOB_U8_TECHO * 50`) sobre una comparacion
    # que este mismo guion imprimia como invalida quince lineas mas abajo. Se
    # borro el 2026-08-24, por tres motivos que valen para cualquier puerta:
    #
    #   1. comparaba el VOLCADO ENTERO (todos los descriptores juntos) contra
    #      un techo POR DESCRIPTOR -- y encima contra el que no era;
    #   2. bloqueaba el push si el descriptor MEJORABA, o sea si bajaba de los
    #      11 900 B que salian de multiplicar un techo ajeno por 50;
    #   3. la correccion estaba escrita en un print y no en el codigo, que es
    #      la unica parte que decide si el push pasa.
    #
    # Lo que queda en su sitio no es una puerta mas floja: es la verdad de que
    # aqui no hay nada que aseverar todavia.
    volcado = e["descriptor"] + e["etiquetas de enumerados"]
    print(f"\nel techo del descriptor son {MAX_DESCRIPTOR_B} B POR DESCRIPTOR "
          f"(LEIDO de descriptor.rs):")
    print("  Es el buffer de `mandar_descriptores` en fw/src/usb.rs, que lo lee")
    print("  de core. Un descriptor que no quepa se salta (#182, fallo 5): el")
    print("  cliente se queda sin ese parametro y no puede enterarse.")
    print()
    print(f"    {'de los que YA existen, el mas gordo':<38}"
          f"{MAS_GORDO_HOY_B:5d} B   "
          f"{MAS_GORDO_HOY_B/MAX_DESCRIPTOR_B:4.0%} del techo   CITADO")
    print(f"    {f'de los {n} de la Voz, el mas gordo':<38}"
          f"{'?':>5} B   {'?':>4} del techo   POR_CONFIRMAR")
    print()
    print("  Ese interrogante no se rellena aqui. Los parametros de este censo")
    print("  no existen todavia como Descriptor en core, asi que su entrada mas")
    print("  grande no se puede medir -- y fabricarla seria peor que no tenerla.")
    print()
    print("  Quien lo mide: nadie a mano, y no hace falta guion nuevo. La puerta")
    print("  ya existe y es de Rust -- descriptor.rs, el test")
    print("  `ningun_descriptor_se_acerca_al_techo_del_volcado`, que recorre los")
    print("  descriptores que EXISTEN y avisa antes del acantilado. El dia que")
    print("  los de la Voz se escriban en core, esa puerta los mide sola. Lo que")
    print("  falta no es una cuenta: son los descriptores.")
    print()
    print(f"  Y ojo con el otro salto de categoria: los {B_POR_ENTRADA} B de "
          f"hoy y los {B_POR_ENTRADA_RICO} B")
    print(f"  del objetivo son MEDIAS, del presupuesto de EEPROM de arriba "
          f"({volcado} B")
    print("  de descriptor + etiquetas). Una media no asevera nada sobre un")
    print("  maximo por entrada, que es lo que mide el techo de esta seccion.")

    print()
    print("VEREDICTO: la memoria cabe, el modelo YA CABE, y del descriptor no se")
    print("  puede decir todavia ni que si ni que no.")
    print("  Eran tres techos con dos en rojo. El del modelo se cerro el")
    print("  2026-08-24 subiendo MAX_PARAMS de 512 a 1024 en modelo.rs, que")
    print("  cuesta 4 KB mas de SRAM y cero tiempo de ejecucion. El tercero no")
    print("  estaba en rojo: estaba mal medido, y ahora esta sin medir.")
    print(f"    MAX_PARAMS   {n} + {RESERVA_RESTO_INSTRUMENTO} de reserva "
          f"= {necesario} de {MAX_PARAMS}   (sobran {holgura})")
    print(f"    EEPROM       {total} B de {EEPROM_B} B   "
          f"({total/EEPROM_B:.0%})")
    print(f"    descriptor   la entrada mas grande, de {MAX_DESCRIPTOR_B} B   "
          f"POR_CONFIRMAR")
    print("                 (la mide core cuando existan, no este guion)")
    print(f"    motor+gestos {'AUSENTES':>9}   {'?':>4} del techo   SIN CENSAR")
    print("                 (motor-digital §9 y el acta de la camara los")
    print("                  mandan al #172; 'decenas' no es una cifra y aqui")
    print(f"                  no se inventa. Los {holgura} que sobran son ANTES")
    print("                  de meterlos: no son margen, son su habitacion)")
    print()
    print("OK: censo cerrado para la Voz. Dos techos aseverados, uno pendiente "
          "de medir, y DOS INQUILINOS SIN CENSAR (motor y gestos, #172).")


if __name__ == "__main__":
    demo()
