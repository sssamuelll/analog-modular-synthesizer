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

  * T_ASENTAMIENTO_CANAL: el mux + la impedancia real del pote contra el
    condensador de muestreo del ADC. Es el numero que decide si el barrido
    rapido es fisicamente posible. No hay placa de panel todavia.
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
T_ASENTAMIENTO_CANAL_US = 5.0   # POR_CONFIRMAR: mux + pote + S/H del ADC
TAU_RC_MS = 0.0                 # POR_CONFIRMAR: no hay filtro elegido

CANDIDATAS_HZ = (500.0, 1_000.0, 2_000.0, 4_000.0, 8_000.0)


def suelo_midi_din_ms() -> float:
    """Lo que tarda un note-on en ENTRAR por MIDI DIN. Aritmetica, no opinion."""
    return BITS_NOTE_ON_DIN / BAUDIOS_MIDI_DIN * 1e3


def t_transmision_ms() -> float:
    """Sondeo del panel + escritura a la Voz, en el mismo giro del lazo."""
    return (BITS_SONDEO_PANEL + BITS_ESCRITURA) / SCLK_J2 * 1e3


def ocupacion(f_lazo: float) -> float:
    return t_transmision_ms() * 1e-3 * f_lazo


def cadena(f_barrido: float, f_lazo: float) -> dict[str, float]:
    """Peor caso, etapa por etapa, en ms."""
    return {
        "barrido del pote": 1e3 / f_barrido,
        "espera de sondeo": 1e3 / f_lazo,
        "transmision J2": t_transmision_ms(),
        "render de la Voz": 1e3 / F_RENDER_VOZ,
        "RC (por confirmar)": TAU_RC_MS,
    }


def us_por_canal(f_barrido: float) -> float:
    return 1e6 / f_barrido / N_POTES


def main() -> None:
    print("LATENCIA MANO -> DAC")
    print()
    print(f"  Suelo de MIDI DIN (solo entrar):  {suelo_midi_din_ms():.3f} ms")
    print(f"  Objetivo declarado (peor caso):   {OBJETIVO_MS:.3f} ms")
    print(f"  Transmision por giro del lazo:    {t_transmision_ms()*1e3:.1f} us")
    print()
    print("  El bus no es el cuello: la cadencia del lazo lo es.")
    print()
    print(f"  {'lazo':>8}  {'total':>9}  {'ocupacion':>10}  {'us/canal':>9}  veredicto")

    viables = []
    for f in CANDIDATAS_HZ:
        etapas = cadena(f, f)
        total = sum(etapas.values())
        ocu = ocupacion(f)
        upc = us_por_canal(f)
        cabe = total <= OBJETIVO_MS and ocu <= TECHO_OCUPACION
        if cabe:
            viables.append((f, total, ocu, upc))
        marca = "OK" if cabe else ("bus" if ocu > TECHO_OCUPACION else "lento")
        print(f"  {f/1e3:6.1f}k  {total:7.3f}ms  {ocu*100:8.1f}%  {upc:7.2f}us  {marca}")

    print()
    if viables:
        f, total, ocu, upc = viables[0]
        print(f"  La mas lenta que cumple: {f/1e3:.1f} kHz")
        print(f"    {total:.3f} ms peor caso, {total/2:.3f} ms promedio")
        print(f"    {ocu*100:.1f}% del J2 -- queda {(1-ocu)*100:.1f}% libre")
        print(f"    {suelo_midi_din_ms()/total:.1f}x por debajo del suelo de MIDI DIN")
        print()
        print("  Desglose del peor caso:")
        for nombre, ms in cadena(f, f).items():
            print(f"    {nombre:<22} {ms:7.3f} ms")
        print()
        print("  EL CUELLO NO ESTA EN EL BUS. Esta aqui:")
        print(f"    {upc:.2f} us por canal para mux + asentamiento + conversion,")
        print(f"    con {T_ASENTAMIENTO_CANAL_US:.1f} us POR_CONFIRMAR de asentamiento solo.")
        if upc < T_ASENTAMIENTO_CANAL_US * 2:
            print("    -> Margen menor de 2x. Se mide con la placa del panel antes")
            print("       de congelar la tasa, o se barre en dos mitades alternas.")

    # --- las puertas -------------------------------------------------------
    assert viables, (
        f"Ninguna cadencia candidata cumple {OBJETIVO_MS} ms con "
        f"{TECHO_OCUPACION*100:.0f}% de techo de bus."
    )
    f_ok = viables[0][0]
    total_ok = viables[0][1]
    assert total_ok < suelo_midi_din_ms(), (
        "El objetivo tiene que quedar POR DEBAJO del suelo de MIDI DIN, "
        "o la frase 'la latencia mas baja' no significa nada."
    )
    # La agrupacion es lo que lo hace posible: sin ella, un parametro por trama.
    sin_agrupar = BITS_TRAMA_VCO / SCLK_J2 * 1e3 * 1e-3 * f_ok * 16
    assert sin_agrupar > ocupacion(f_ok), (
        "Si mandar 16 parametros sueltos NO costara mas que el bloque agrupado, "
        "R-M4 no tendria razon de ser y esta cuenta estaria mal montada."
    )
    print()
    print(f"  Sin agrupar (16 tramas sueltas a {f_ok/1e3:.0f} kHz): "
          f"{sin_agrupar*100:.1f}% del bus")
    print(f"  Agrupado (R-M4):                        {ocupacion(f_ok)*100:.1f}%")
    print(f"  La agrupacion es lo que compra la velocidad, no el reloj.")
    print()
    print("OK: presupuesto cerrado.")
    print()
    print("NO cubre: nota -> VCA (evento_budget.py), el jitter del lazo, el")
    print("asentamiento del DAC, ni la comparacion contra instrumentos reales")
    print("-- esa se mide con osciloscopio o no se dice.")


if __name__ == "__main__":
    main()
