"""La cadena mano -> DAC: cuanto tarda el sonido en obedecer al dedo.

    python latencia_mano_budget.py

NUEVO Y BLOQUEANTE PARA EL PANEL. El objetivo lo puso Samuel el 2026-08-23:
"el mas minimo tiempo de latencia de todo el mercado". Este guion existe para
que esa frase sea un numero con puerta, y no publicidad.

--- Que se mide, y que NO --------------------------------------------------

Se mide MANO -> DAC: giras un pote y el CV se mueve. Es OTRO camino que el de
nota -> VCA (<=3 ms, voz-total S3.3), que ya tiene su cota y su guion pendiente
(evento_budget.py). Este no lo sustituye.

--- La regla que gobierna la cuenta ----------------------------------------

La latencia de una etapa periodica NO es lo que tarda en transmitir: es su
PERIODO. Una trama de 288 bits tarda 28.8 us en salir a 10 MHz, pero si solo
sale una cada 10 ms, la latencia son 10 ms. El bus no es el cuello; la cadencia
del lazo lo es.

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

  * T_ASENTAMIENTO y T_CONVERSION: el mux + la impedancia real del pote contra
    el condensador de muestreo, y la tasa del SAR del RP2350B, que el repo NO
    documenta. Juntos deciden si el barrido rapido es fisicamente posible, y
    hoy son EL CUELLO: a 8 kHz el bus va al 43 % y el barrido ya no da.
    No hay placa de panel para medirlos.
  * TAU_RC: la reconstruccion analogica detras del DAC. Es latencia tambien, y
    es el suelo duro: el filtro que borra los escalones ES el retardo.
  * SCLK_J2 = 10 MHz es el techo del contrato congelado; el maximo real del
    AD5686R nunca se leyo de la hoja (j2.rs: tres intentos con timeout).
  * El canal de vuelta del J2 para el panel NO EXISTE como contrato. Aqui se
    dimensiona lo que costaria; que exista es trabajo de #178.
"""
from __future__ import annotations

# --- citado ------------------------------------------------------------------
SCLK_J2 = 10e6              # j2.rs: contrato congelado, "<=10 MHz"
BITS_TRAMA_VCO = 72         # j2.rs: 3 x AD5686R en cadena
BITS_BLOQUE_TONO = 288      # orquestacion R-M4: 16 x 16 bits + cabecera
PARAMS_POR_BLOQUE = 16      # orquestacion R-M4: los parametros que ese bloque
                            # agrupa. Es el 16 de la linea de arriba, con nombre
                            # -- el payload que las dos configuraciones mueven
F_RENDER_VOZ = 10_000.0     # voz-total S3.1: render de envolventes a 10 kHz
N_POTES = 45                # plan del panel S4: 16 curadas + 4 macro + margen
BAUDIOS_MIDI_DIN = 31250.0  # norma MIDI 1.0
BITS_NOTE_ON_DIN = 30       # 3 bytes x (1 arranque + 8 datos + 1 parada)

# --- declarado (esto es lo que se decide aqui) -------------------------------
OBJETIVO_MS = 1.0           # mano -> DAC, peor caso, parte digital
TECHO_OCUPACION = 0.50      # del J2; la mitad se reserva a todo lo demas
BITS_SONDEO_PANEL = 256     # bloque de vuelta del panel: deltas + cabecera
BITS_ESCRITURA = BITS_BLOQUE_TONO   # el bloque agrupado hacia la Voz

# --- por confirmar (con su valor de trabajo) ---------------------------------
T_ASENTAMIENTO_US = 5.0     # POR_CONFIRMAR: mux + impedancia del pote + S/H
T_CONVERSION_US = 2.0       # POR_CONFIRMAR: el repo NO documenta la tasa del
                            # ADC del RP2350B. Valor de trabajo; sale de la hoja
TAU_RC_MS = 0.0             # POR_CONFIRMAR: no hay filtro de reconstruccion
                            # elegido, y su tau ES latencia

# La correccion del 2026-08-23: la v1 de este guion modelo el barrido como
# SECUENCIAL -- 45 canales en fila, asentamiento + conversion cada uno. Es
# falso por topologia, no por datasheet: si hay N muxes colgando de N entradas
# de ADC, TODOS reciben la misma direccion y asientan A LA VEZ. El
# asentamiento se paga UNA vez por paso de direccion y se reparte entre N
# conversiones. Con un solo SAR las conversiones si van en fila.
N_MUXES = 3                 # DECLARADO: 3 de las 8 entradas analogicas
                            # (48 GPIO / 8 ADC del RP2350B, citado en el repo)

CANDIDATAS_HZ = (500.0, 1_000.0, 2_000.0, 4_000.0, 8_000.0, 16_000.0)


def suelo_midi_din_ms() -> float:
    """Lo que tarda un note-on en ENTRAR por MIDI DIN. Aritmetica, no opinion."""
    return BITS_NOTE_ON_DIN / BAUDIOS_MIDI_DIN * 1e3


def bits_por_giro(agrupado: bool = True) -> int:
    """Bits que el J2 mueve en un giro del lazo, con el MISMO payload.

    El payload son los 16 parametros hacia la Voz, en las dos configuraciones:
    agrupados van en UN bloque de 288 bits (R-M4); sueltos, en 16 tramas de 72.

    El sondeo del panel es comun a las dos y por eso se carga a las dos. La v1
    de este guion se lo cargaba SOLO al lado agrupado, o sea comparaba cargas
    distintas -- y la de mas peso se la ponia a la opcion que defiende.
    """
    carga = BITS_ESCRITURA if agrupado else PARAMS_POR_BLOQUE * BITS_TRAMA_VCO
    return BITS_SONDEO_PANEL + carga


def t_transmision_ms(agrupado: bool = True) -> float:
    """Sondeo del panel + escritura a la Voz, en el mismo giro del lazo."""
    return bits_por_giro(agrupado) / SCLK_J2 * 1e3


def ocupacion(f_lazo: float, agrupado: bool = True) -> float:
    return t_transmision_ms(agrupado) * 1e-3 * f_lazo


def cadena(f_barrido: float, f_lazo: float) -> dict[str, float]:
    """Peor caso, etapa por etapa, en ms."""
    return {
        "barrido del pote": 1e3 / f_barrido,
        "espera de sondeo": 1e3 / f_lazo,
        "transmision J2": t_transmision_ms(),
        "render de la Voz": 1e3 / F_RENDER_VOZ,
        "RC (por confirmar)": TAU_RC_MS,
    }


def t_barrido_necesario_us(n_muxes: int) -> float:
    """Lo que TARDA un barrido completo de los potes, por topologia.

    Pasos de direccion = potes / muxes. En cada paso los N muxes asientan a la
    vez (una sola espera) y luego el SAR convierte los N en fila.
    """
    pasos = -(-N_POTES // n_muxes)          # techo de la division
    return pasos * (T_ASENTAMIENTO_US + n_muxes * T_CONVERSION_US)


def holgura_barrido(f_barrido: float, n_muxes: int) -> float:
    """Cuantas veces cabe el barrido en su propio periodo. <1 = no cabe."""
    return (1e6 / f_barrido) / t_barrido_necesario_us(n_muxes)


def main() -> None:
    print("LATENCIA MANO -> DAC")
    print()
    print(f"  Suelo de MIDI DIN (solo entrar):  {suelo_midi_din_ms():.3f} ms")
    print(f"  Objetivo declarado (peor caso):   {OBJETIVO_MS:.3f} ms")
    print(f"  Transmision por giro del lazo:    {t_transmision_ms()*1e3:.1f} us")
    print()
    print("  El bus no es el cuello: la cadencia del lazo lo es.")
    print()
    print(f"  {'lazo':>8}  {'total':>9}  {'bus':>8}  {'barrido':>9}  veredicto")

    viables = []
    for f in CANDIDATAS_HZ:
        total = sum(cadena(f, f).values())
        ocu = ocupacion(f)
        holg = holgura_barrido(f, N_MUXES)
        cabe = total <= OBJETIVO_MS and ocu <= TECHO_OCUPACION and holg >= 1.0
        if cabe:
            viables.append((f, total, ocu, holg))
        if ocu > TECHO_OCUPACION:
            marca = "bus lleno"
        elif holg < 1.0:
            marca = "no barre"
        elif total > OBJETIVO_MS:
            marca = "lento"
        else:
            marca = "OK"
        print(f"  {f/1e3:6.1f}k  {total:7.3f}ms  {ocu*100:6.1f}%  {holg:7.2f}x  {marca}")

    print()
    print(f"  Barrido de {N_POTES} potes con {N_MUXES} muxes en paralelo:")
    print(f"    {-(-N_POTES // N_MUXES)} pasos de direccion x "
          f"({T_ASENTAMIENTO_US:.0f} us de asentamiento + "
          f"{N_MUXES} x {T_CONVERSION_US:.0f} us) = "
          f"{t_barrido_necesario_us(N_MUXES):.0f} us")
    print(f"    Secuencial (1 mux) serian "
          f"{t_barrido_necesario_us(1):.0f} us -- "
          f"{t_barrido_necesario_us(1)/t_barrido_necesario_us(N_MUXES):.1f}x peor.")
    print("    El asentamiento se paga UNA vez por paso: los muxes asientan a la vez.")
    print()

    if viables:
        f, total, ocu, holg = viables[-1]   # la MAS RAPIDA que cumple
        print(f"  La mas rapida que cumple: {f/1e3:.1f} kHz")
        print(f"    {total:.3f} ms peor caso, {total/2:.3f} ms promedio")
        print(f"    {ocu*100:.1f}% del J2 -- queda {(1-ocu)*100:.1f}% libre")
        print(f"    barrido con {holg:.2f}x de holgura")
        print(f"    {suelo_midi_din_ms()/total:.1f}x por debajo del suelo de MIDI DIN")
        print()
        print("  Desglose del peor caso:")
        for nombre, ms in cadena(f, f).items():
            print(f"    {nombre:<22} {ms:7.3f} ms")

    # --- las puertas -------------------------------------------------------
    assert viables, (
        f"Ninguna cadencia candidata cumple {OBJETIVO_MS} ms con "
        f"{TECHO_OCUPACION*100:.0f}% de techo de bus."
    )
    f_ok = viables[-1][0]
    total_ok = viables[-1][1]
    assert total_ok < suelo_midi_din_ms(), (
        "El objetivo tiene que quedar POR DEBAJO del suelo de MIDI DIN, "
        "o la frase 'la latencia mas baja' no significa nada."
    )
    # --- la puerta que justifica R-M4 --------------------------------------
    #
    # La v1 comparaba 16 tramas sueltas SIN sondeo del panel contra el bloque
    # agrupado CON los 256 bits del sondeo: dos cargas distintas, y la de mas
    # peso puesta del lado que el guion defiende. Y encima f_ok se cancelaba en
    # los dos lados, asi que la desigualdad real era 1152 > 544 -- cierta para
    # cualquier cadencia y cualquier reloj. Un assert que no puede fallar no es
    # una puerta: es una decoracion que se lee como aval.
    #
    # Esto es lo que R-M4 promete y lo que SI puede romperse: con el mismo
    # payload y el mismo sondeo cargado a las dos, los parametros sueltos se
    # pasan del techo de bus declarado a la cadencia elegida, y el bloque
    # agrupado no.
    ocu_suelta = ocupacion(f_ok, agrupado=False)
    ocu_agrupada = ocupacion(f_ok, agrupado=True)
    assert ocu_suelta > TECHO_OCUPACION, (
        f"Con {PARAMS_POR_BLOQUE} parametros sueltos el J2 va al "
        f"{ocu_suelta*100:.1f}% y el techo declarado es "
        f"{TECHO_OCUPACION*100:.0f}%: CABEN. Si caben, R-M4 no se sostiene por "
        f"presupuesto de bus. Habra que justificarla por otra cosa -- que el "
        f"cambio de tono llegue atomico, el jitter entre parametros -- o "
        f"retirarla, pero no con esta cuenta."
    )
    # Que la agrupada quepa no se asevera aqui: ya lo exigio el filtro de
    # `viables` (ocu <= TECHO_OCUPACION) para elegir f_ok. Aseverarlo otra vez
    # seria otra decoracion.
    sclk_que_la_apaga = bits_por_giro(False) * f_ok / TECHO_OCUPACION
    f_que_la_apaga = TECHO_OCUPACION * SCLK_J2 / bits_por_giro(False)
    print()
    print(f"  R-M4, el mismo payload de {PARAMS_POR_BLOQUE} parametros a "
          f"{f_ok/1e3:.0f} kHz")
    print(f"  (los {BITS_SONDEO_PANEL} bits del sondeo del panel van en las dos):")
    print(f"    sueltos   {bits_por_giro(False):5d} bits/giro   "
          f"{ocu_suelta*100:5.1f}% del J2")
    print(f"    agrupado  {bits_por_giro(True):5d} bits/giro   "
          f"{ocu_agrupada*100:5.1f}% del J2")
    print(f"    {'techo de bus declarado':<28}{TECHO_OCUPACION*100:5.1f}%")
    print("  La agrupacion es lo que compra la velocidad, no el reloj.")
    print()
    print("  Esta puerta se pone ROJA -- y tiene como -- si los sueltos pasan a")
    print(f"  caber: con el J2 a {sclk_que_la_apaga/1e6:.2f} MHz o mas (hoy "
          f"{SCLK_J2/1e6:.0f}), con el lazo por debajo de "
          f"{f_que_la_apaga/1e3:.1f} kHz,")
    print(f"  o subiendo el techo de bus por encima del {ocu_suelta*100:.1f}%.")
    print()
    print("OK: presupuesto cerrado.")
    print()
    print("NO cubre: nota -> VCA (evento_budget.py), el jitter del lazo, el")
    print("asentamiento del DAC, ni la comparacion contra instrumentos reales")
    print("-- esa se mide con osciloscopio o no se dice.")


if __name__ == "__main__":
    main()
