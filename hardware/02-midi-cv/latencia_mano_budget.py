"""La cadena mano -> DAC: cuanto tarda el sonido en obedecer al dedo.

    python latencia_mano_budget.py

NUEVO Y BLOQUEANTE PARA EL PANEL. El objetivo lo puso Samuel el 2026-08-23:
"el mas minimo tiempo de latencia de todo el mercado". Este guion existe para
que esa frase sea un numero con puerta, y no publicidad.

REESCRITO por el J2 punto a punto (#210 S7): "El lazo del panel contra el
enlace privado de la Voz: el techo de 9,19 kHz se recalcula; SCLK_J2 deja de
ser global". Antes el giro del lazo (sondeo del panel + escritura a la Voz,
544 bits) viajaba por UN bus a 10 MHz y tocaba el techo del 50 % a 9,19 kHz.
Ahora el sondeo va por el enlace del modulo de mandos y la escritura por el
enlace de la Voz -- dos relojes, dos techos, y R-P1 prohibe sumarlos. Cada
uno se asevera contra el suyo; los relojes y el techo por enlace los da
trama_j2_budget.py y de ahi se importan.

--- Que se mide, y que NO --------------------------------------------------

Se mide MANO -> DAC: giras un pote y el CV se mueve. Es OTRO camino que el de
nota -> VCA (<=3 ms, voz-total S3.3), que ya tiene su cota y su guion pendiente
(evento_budget.py). Este no lo sustituye.

--- La regla que gobierna la cuenta ----------------------------------------

La latencia de una etapa periodica NO es lo que tarda en transmitir: es su
PERIODO. Una trama de 328 bits tarda 32,8 us en salir a 10 MHz, pero si solo
sale una cada 10 ms, la latencia son 10 ms. El bus no es el cuello; la cadencia
del lazo lo es. Y desde el punto a punto, el bus NI SIQUIERA acota la cadencia:
la acotan los EXTREMOS (D6) -- el barrido analogico del panel por un lado y la
tasa de render de la Voz por el otro.

Peor caso = acabas de perder el barrido / el sondeo. Promedio = la mitad.
Se asevera sobre el PEOR caso.

--- El ancla competitiva, y su honestidad ----------------------------------

NO tengo una cifra medida de Moog ni de nadie, y fabricarla seria peor que no
tenerla. Lo que si es aritmetica verificable: un note-on por MIDI DIN son 3
bytes a 31250 baudios con bit de arranque y parada, o sea 30 bits => 960 us
SOLO en entrar por la puerta. Ese es el suelo de CUALQUIER sinte cuyo camino de
control externo sea MIDI DIN, antes de procesar nada.

Nuestro camino de panel no pasa por MIDI. El objetivo declarado se pone por
debajo de ese suelo, con margen, y la comparacion real contra instrumentos
concretos queda POR_CONFIRMAR: se mide con osciloscopio, no se declara.

--- Lo que NO esta confirmado ----------------------------------------------

  * T_ASENTAMIENTO: el mux + la impedancia real del pote contra el condensador
    de muestreo. Es EL CUELLO del barrido. No hay placa de panel para medirlo.
  * TAU_RC: la reconstruccion analogica detras del DAC. Es latencia tambien, y
    es el suelo duro: el filtro que borra los escalones ES el retardo.
  * El enlace del modulo de mandos no tiene papel (#178): corre al piso legado
    y su ocupacion se evalua ahi. El canal de vuelta del panel NO EXISTE como
    contrato; aqui se dimensiona lo que costaria.
  * Esta cuenta mantiene el barrido en el cerebro. El #178 lo muda al modulo de
    mandos con su ADC propio, pero esa pertenencia no esta sancionada en su
    papel; este guion no toma esa decision de arquitectura.
"""
from __future__ import annotations

import trama_j2_budget as tj

# --- citado ------------------------------------------------------------------
BITS_TRAMA_VCO = 72         # j2.rs: 3 x AD5686R en cadena -- el dialecto legado
BITS_BLOQUE_TONO = tj.BITS_BLOQUE_TONO     # orquestacion R-M4: 16 x 16 + cabecera
PARAMS_POR_BLOQUE = 16      # los parametros que ese bloque agrupa
F_RENDER_VOZ = 10_000.0     # voz-total S3.1: render a 10 kHz por canal. Es el
                            # EXTREMO de la Voz: mandar tono mas rapido que
                            # eso no se aplica mas rapido que eso
N_POTES = 45                # plan del panel S4: 16 curadas + 4 macro + margen
BAUDIOS_MIDI_DIN = 31250.0  # norma MIDI 1.0
BITS_NOTE_ON_DIN = 30       # 3 bytes x (1 arranque + 8 datos + 1 parada)

# --- declarado (esto es lo que se decide aqui) -------------------------------
OBJETIVO_MS = 1.0           # mano -> DAC, peor caso, parte digital
BITS_SONDEO_PANEL = tj.BITS_SONDEO_PANEL   # bloque de vuelta: deltas + cabecera
BITS_ESCRITURA = BITS_BLOQUE_TONO           # el bloque agrupado hacia la Voz

# --- por confirmar (con su valor de trabajo) ---------------------------------
T_ASENTAMIENTO_US = 5.0     # POR_CONFIRMAR: mux + impedancia del pote + S/H
T_CONVERSION_CICLOS_12B = 13.5  # DS14791 Rev 10, Tabla 97, p. 205: tC
T_CONVERSION_US: float | None = None  # HUECO: faltan fADC, resolucion y tS
TAU_RC_MS = 0.0             # POR_CONFIRMAR: no hay filtro de reconstruccion
                            # elegido. Cero no es una medida, es un HUECO: el
                            # "peor caso" de abajo son CUATRO etapas de cinco
N_MUXES = 3                 # DECLARADO: 3 de las 8 entradas analogicas

CANDIDATAS_HZ = (500.0, 1_000.0, 2_000.0, 4_000.0, 8_000.0, 16_000.0)

# --- los dos enlaces, de trama_j2_budget.py (D2, D6) --------------------------
VOZ = tj.enlace("Voz total")
MANDOS = tj.enlace("modulo de mandos")
TECHO_OCUPACION = tj.TECHO_OCUPACION_ENLACE


def suelo_midi_din_ms() -> float:
    """Lo que tarda un note-on en ENTRAR por MIDI DIN. Aritmetica, no opinion."""
    return BITS_NOTE_ON_DIN / BAUDIOS_MIDI_DIN * 1e3


def bits_escritura(agrupado: bool = True) -> int:
    """Lo que el enlace de la VOZ mueve por giro, con el mismo payload:
    agrupados, UN bloque de 328 (cabecera S4); sueltos, 16 tramas del dialecto
    legado de 72."""
    return BITS_ESCRITURA if agrupado else PARAMS_POR_BLOQUE * BITS_TRAMA_VCO


def t_transmision_ms(agrupado: bool = True) -> float:
    """Sondeo por el enlace de mandos y luego escritura por el de la Voz. Van
    en serie en la CAUSA (primero se lee el pote, luego se escribe el tono),
    aunque sean dos enlaces: por eso se suman los tiempos, no las
    ocupaciones."""
    return (BITS_SONDEO_PANEL / MANDOS.reloj_operacion_hz()
            + bits_escritura(agrupado) / VOZ.reloj_operacion_hz()) * 1e3


def ocupacion_voz(f_lazo: float, agrupado: bool = True) -> float:
    return bits_escritura(agrupado) * f_lazo / VOZ.reloj_operacion_hz()


def ocupacion_mandos(f_lazo: float) -> float:
    return BITS_SONDEO_PANEL * f_lazo / MANDOS.reloj_operacion_hz()


def cabe_en_los_enlaces(f_lazo: float) -> bool:
    """Cada enlace contra SU techo. Nunca la suma (R-P1)."""
    return (ocupacion_voz(f_lazo) <= TECHO_OCUPACION
            and ocupacion_mandos(f_lazo) <= TECHO_OCUPACION)


def cadena(f_barrido: float, f_lazo: float) -> dict[str, float]:
    """Peor caso, etapa por etapa, en ms."""
    return {
        "barrido del pote": 1e3 / f_barrido,
        "espera de sondeo": 1e3 / f_lazo,
        "transmision (2 enlaces)": t_transmision_ms(),
        "render de la Voz": 1e3 / F_RENDER_VOZ,
        "RC (por confirmar)": TAU_RC_MS,
    }


def t_barrido_necesario_us(n_muxes: int) -> float:
    """Pasos de direccion = potes / muxes. En cada paso los N muxes asientan a
    la vez (una sola espera) y luego el SAR convierte los N en fila."""
    pasos = -(-N_POTES // n_muxes)
    return pasos * (T_ASENTAMIENTO_US + n_muxes * T_CONVERSION_US)


def holgura_barrido(f_barrido: float, n_muxes: int) -> float:
    """Cuantas veces cabe el barrido en su propio periodo. <1 = no cabe."""
    return (1e6 / f_barrido) / t_barrido_necesario_us(n_muxes)


def autocomprobacion() -> None:
    """Que la puerta mire cada enlace y NO la suma (R-P1).

    Con las cifras de hoy (23 % + 20,5 %) sumar y no sumar dan el mismo
    veredicto, asi que ninguna aseveracion de main() distinguiria una
    version que volviera a sumar. Este testigo si: una cadencia que deja el
    enlace mas apretado al 45 % cabe enlace por enlace, y la suma de los dos
    pasa del 50 % siempre que el otro enlace no sea >9x mas rapido. Barrido
    en vez de valor a mano, para que no coincida por accidente.
    """
    f_voz, f_man = VOZ.reloj_operacion_hz(), MANDOS.reloj_operacion_hz()
    f_w = 0.45 * min(f_voz / BITS_ESCRITURA, f_man / BITS_SONDEO_PANEL)
    assert cabe_en_los_enlaces(f_w), (
        f"a {f_w:.0f} Hz ningun enlace pasa del 45 % y la puerta dice que no "
        "cabe: alguien volvio a sumar ocupaciones de enlaces distintos (R-P1)")
    for f in (0.5 * f_w, f_w, 1.2 * f_w):
        assert cabe_en_los_enlaces(f) == (
            ocupacion_voz(f) <= TECHO_OCUPACION
            and ocupacion_mandos(f) <= TECHO_OCUPACION)


def main() -> int:
    autocomprobacion()
    f_voz, f_man = VOZ.reloj_operacion_hz(), MANDOS.reloj_operacion_hz()
    print("LATENCIA MANO -> DAC")
    print()
    print(f"  Suelo de MIDI DIN (solo entrar):  {suelo_midi_din_ms():.3f} ms")
    print(f"  Objetivo declarado (peor caso):   {OBJETIVO_MS:.3f} ms")
    print(f"  Enlace de la Voz corre a          {f_voz/1e6:.1f} MHz"
          f"   {'(piso legado, sin sancion)' if VOZ.sancionado_hz is None else '(sancionado)'}")
    print(f"  Enlace de mandos corre a          {f_man/1e6:.1f} MHz"
          f"   {'(piso legado, sin papel)' if MANDOS.ranura.papel is None else ''}")
    print(f"  Transmision por giro del lazo:    {t_transmision_ms()*1e3:.1f} us"
          f"   ({BITS_SONDEO_PANEL} por mandos + {BITS_ESCRITURA} por la Voz)")
    print()
    print("  El bus no es el cuello: la cadencia del lazo lo es. Y la cadencia")
    print("  la acotan los extremos, no el bus (D6).")
    print()

    print("AVISO (#178): esta cuenta mantiene el ADC en el cerebro; el papel")
    print("  del modulo de mandos puede mudar el barrido y aun no esta sancionado.")
    print("  Este guion no resuelve esa pertenencia.")
    print()
    if T_CONVERSION_US is None:
        print("HUECO: DS14791 Rev 10, Tabla 97, p. 205 da "
              f"tC = {T_CONVERSION_CICLOS_12B:g} / fADC para 12 bits, no us.")
        print("  Faltan la frecuencia y resolucion configuradas, y el tiempo de")
        print("  muestreo tS. No se conserva ni se reemplaza el 2 us del RP2350.")
        print("  El presupuesto mano -> DAC no se puede cerrar con una cifra ADC.")
        return 2

    print(f"  {'lazo':>8}  {'total':>9}  {'Voz':>7}  {'mandos':>7}  {'barrido':>9}  veredicto")

    for f in CANDIDATAS_HZ:
        total = sum(cadena(f, f).values())
        ov, om, holg = ocupacion_voz(f), ocupacion_mandos(f), holgura_barrido(f, N_MUXES)
        if not cabe_en_los_enlaces(f):
            marca = "enlace lleno"
        elif f > F_RENDER_VOZ:
            marca = "> render Voz"
        elif holg < 1.0:
            marca = "no barre"
        elif total > OBJETIVO_MS:
            marca = "lento"
        else:
            marca = "OK"
        print(f"  {f/1e3:6.1f}k  {total:7.3f}ms  {ov*100:5.1f}%  {om*100:5.1f}%  {holg:7.2f}x  {marca}")

    print()
    print(f"  Barrido de {N_POTES} potes con {N_MUXES} muxes en paralelo:")
    print(f"    {-(-N_POTES // N_MUXES)} pasos x ({T_ASENTAMIENTO_US:.0f} us + "
          f"{N_MUXES} x {T_CONVERSION_US:.0f} us) = {t_barrido_necesario_us(N_MUXES):.0f} us")
    print()

    # --- la cadencia, DESACOPLADA (decision de Samuel, 2026-08-24) ---------
    # Al BARRIDO lo limita el analogico. Al LAZO ya no lo limita el bus: lo
    # limita el extremo de la Voz (render a 10 kHz) -- y los dos enlaces se
    # comprueban aparte por si algun dia el limite volviera a ser el cable.
    f_barrido = max((f for f in CANDIDATAS_HZ
                     if holgura_barrido(f, N_MUXES) >= 1.0), default=0.0)
    f_lazo = max((f for f in CANDIDATAS_HZ
                  if cabe_en_los_enlaces(f) and f <= F_RENDER_VOZ), default=0.0)
    assert f_barrido and f_lazo, (
        f"Sin candidata viable: barrido {f_barrido}, lazo {f_lazo}.")

    # trama_j2_budget.py DECLARA esta cadencia en la fila del bloque de tono.
    # Aqui se DERIVA. Si no coinciden, uno de los dos miente y canta aqui.
    assert f_lazo == tj.F_LAZO_HZ, (
        f"el lazo que sale de aqui es {f_lazo:.0f} Hz y trama_j2_budget.py "
        f"declara {tj.F_LAZO_HZ:.0f}: actualiza F_LAZO_HZ alla con esta cifra")

    total_ok = sum(cadena(f_barrido, f_lazo).values())
    print(f"  Desacoplado: barrido {f_barrido/1e3:.0f} kHz, lazo {f_lazo/1e3:.2f} kHz")
    print(f"    {total_ok:.3f} ms peor caso")
    print(f"    enlace de la Voz al {ocupacion_voz(f_lazo)*100:.1f}%, "
          f"el de mandos al {ocupacion_mandos(f_lazo)*100:.1f}% -- cada uno del suyo")
    print(f"    barrido con {holgura_barrido(f_barrido, N_MUXES):.2f}x de holgura")
    print(f"    {suelo_midi_din_ms()/total_ok:.1f}x por debajo del suelo de MIDI DIN")
    print()
    print("  Desglose del peor caso:")
    etapas = cadena(f_barrido, f_lazo)
    huecos = [n for n, ms in etapas.items() if ms == 0.0]
    for nombre, ms in etapas.items():
        marca = "  <- HUECO, no medido" if ms == 0.0 else ""
        print(f"    {nombre:<24} {ms:7.3f} ms{marca}")
    if huecos:
        print(f"    -> el total son {len(etapas) - len(huecos)} etapas de {len(etapas)};"
              f" {', '.join(huecos)} entra sumando cuando se mida")
    print()

    # --- el heredero del 9,19 kHz ------------------------------------------
    techo_voz = VOZ.techo_lazo_hz(BITS_ESCRITURA)
    techo_man = MANDOS.techo_lazo_hz(BITS_SONDEO_PANEL)
    print("  El techo del lazo, recalculado (D6 mando matar el 9,19 kHz):")
    print(f"    por el enlace de la Voz     {techo_voz/1e3:5.1f} kHz  ({BITS_ESCRITURA} bits al "
          f"{TECHO_OCUPACION:.0%} de {f_voz/1e6:.0f} MHz)")
    print(f"    por el enlace de mandos     {techo_man/1e3:5.1f} kHz  ({BITS_SONDEO_PANEL} bits al "
          f"{TECHO_OCUPACION:.0%} de {f_man/1e6:.0f} MHz)")
    print(f"    por el render de la Voz     {F_RENDER_VOZ/1e3:5.1f} kHz  <- EL QUE MANDA")
    assert F_RENDER_VOZ < min(techo_voz, techo_man), (
        "el bus volvio a ser el cuello del lazo: algun enlace acota por debajo "
        "del render de la Voz. Revisar el reloj de ese enlace")
    print("  El lazo ya no es del bus: lo acota el extremo. Subirlo de 8 kHz")
    print("  pide render mas rapido en la Voz, no cable.")

    # --- las puertas -------------------------------------------------------
    assert total_ok <= OBJETIVO_MS, (
        f"Desacoplado da {total_ok:.3f} ms y el objetivo declarado es {OBJETIVO_MS} ms.")
    assert total_ok < suelo_midi_din_ms(), (
        "El objetivo tiene que quedar POR DEBAJO del suelo de MIDI DIN, "
        "o la frase 'la latencia mas baja' no significa nada.")

    # --- la puerta que justifica R-M4, ahora por el enlace de la Voz -------
    #
    # R-M4 se sostiene POR PRESUPUESTO mientras los 16 parametros sueltos (16
    # tramas de 72) rebasen el techo del enlace y el bloque agrupado no. Con
    # el mismo payload y la misma cadencia, en el enlace de la Voz:
    ocu_suelta = ocupacion_voz(f_lazo, agrupado=False)
    ocu_agrupada = ocupacion_voz(f_lazo, agrupado=True)
    f_voz_que_la_apaga = bits_escritura(False) * f_lazo / TECHO_OCUPACION
    print()
    print(f"  R-M4, el mismo payload de {PARAMS_POR_BLOQUE} parametros a {f_lazo/1e3:.0f} kHz,"
          f" por el enlace de la Voz a {f_voz/1e6:.0f} MHz:")
    print(f"    sueltos   {bits_escritura(False):5d} bits/giro   {ocu_suelta*100:5.1f}%")
    print(f"    agrupado  {bits_escritura(True):5d} bits/giro   {ocu_agrupada*100:5.1f}%")
    print(f"    {'techo del enlace':<28}{TECHO_OCUPACION*100:5.1f}%")
    print()
    print("  AVISO, y es a proposito: esta puerta se pone ROJA el dia que el")
    print(f"  enlace de la Voz se sancione a {f_voz_que_la_apaga/1e6:.1f} MHz o mas. La Voz")
    print(f"  declara {VOZ.ranura.reloj_declarado_hz/1e6:.1f} (D8). Ese dia R-M4 deja de sostenerse por")
    print("  presupuesto y necesita su otra razon -- que los 16 tonos lleguen")
    print("  atomicos, el jitter entre parametros -- o se retira. Decision de")
    print("  Samuel, no de este guion.")
    assert ocu_suelta > TECHO_OCUPACION, (
        f"Con {PARAMS_POR_BLOQUE} parametros sueltos el enlace de la Voz va al "
        f"{ocu_suelta*100:.1f}% y el techo es {TECHO_OCUPACION*100:.0f}%: CABEN. "
        f"R-M4 ya no se sostiene por presupuesto de enlace (el enlace corre a "
        f"{f_voz/1e6:.1f} MHz). Hay que justificarla por otra cosa o retirarla, "
        f"pero no con esta cuenta.")
    print()
    print("OK: presupuesto cerrado.")
    print()
    print("NO cubre: nota -> VCA (evento_budget.py), el jitter del lazo, el")
    print("asentamiento del DAC, ni la comparacion contra instrumentos reales")
    print("-- esa se mide con osciloscopio o no se dice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
