"""Presupuesto de masa del bus board, en cents de desafinacion.

Por que existe este fichero y no un parrafo en las notas: el ancho del cobre,
la longitud de los cables de bajada y el numero de conductores de masa son
NUMEROS, y si alguien los cambia el diseno se rompe en silencio. Aqui se rompe
en voz alta.

    python ground_budget.py

La cadena causal, que es lo que hay que tener en la cabeza:

  1 V/octava -> 1 V = 1200 cents -> **1 mV = 1.2 cents**.

  Un CV de tono sale del MIDI/CV referido a SU masa local y lo lee el VCO
  referido a la SUYA. Si las dos masas no estan al mismo potencial, la
  diferencia se suma al CV y el VCO desafina. No es ruido: es un error de
  continua que se oye como que el sinte no afina.

  Objetivo: <= 2 cents entre CUALQUIER par de modulos de la cadena de tono
  (MIDI/CV + los tres VCO). 2 cents = 1.67 mV de diferencia de masa.

Lo que este calculo destapo y no era obvio:

  * El plano de masa del bus NO es el cuello de botella. Aporta ~0.2 cents.
    El presupuesto se lo comen el cable de bajada y sus contactos.
  * Pero solo si es PLANO. Una pista de 5 mm haciendo el mismo trabajo son
    ~3 cents ella sola, y el diseno se cae.
  * En el cable, el cobre ya no manda: **mandan los contactos**. Engordar de
    24 AWG a 20 AWG casi no mueve la aguja porque los crimpados son el suelo.
    Lo que si mueve la aguja es usar los DOS conductores de masa de J2.
  * Con dos segmentos aparece un termino nuevo que no existiria con uno solo:
    si los dos tiran corrientes distintas, sus cables de alimentacion caen
    distinto y TODO el segmento A se desplaza respecto al B. Por eso la
    cadena de tono va entera en el MISMO segmento (ver REGLA_SEGMENTO).
"""
from __future__ import annotations

# --- constantes fisicas -------------------------------------------------
RHO_20 = 1.72e-8         # resistividad del cobre a 20 C [ohm*m]
ALPHA = 0.00393          # coef. de temperatura del cobre [1/C]
T_OP = 40.0              # dentro del cajon, no a 20 C
RHO = RHO_20 * (1 + ALPHA * (T_OP - 20.0))

ESPESOR_1OZ = 35e-6      # cobre de 1 oz [m]
R_CUADRO = RHO / ESPESOR_1OZ * 1000.0   # [mohm/cuadro]

CENTS_POR_MV = 1.2       # 1 V/oct: 1 V = 1200 cents
OBJETIVO_CENTS = 2.0

# --- geometria del segmento ---------------------------------------------
LARGO = 320.0            # mm
ANCHO_PLANO_EFECTIVO = 30.0   # mm de plano que sobrevive a los taladros de
                              # los conectores. El plano bruto son 56 mm; se
                              # descuenta a ojo de buen cubero POR LO BAJO.
X_ALIMENTACION = LARGO / 2    # el feed entra por el CENTRO, no por la punta:
                              # parte en dos el camino mas largo, gratis.
# Posiciones reales de los slots en la placa (build_pcb.py, SLOTS_X). Hay un
# hueco de 36 mm en el centro porque ahi va el bornero de alimentacion, no por
# nada electrico.
SLOTS_X = [26.0, 74.0, 122.0, 198.0, 246.0, 294.0]
N_SLOTS = len(SLOTS_X)

# --- corrientes ----------------------------------------------------------
# OJO: la corriente de masa de un modulo NO es su consumo de riel. Un modulo
# analogico simetrico chupa I de +12 y devuelve I por -12, y por masa solo
# circula el DESEQUILIBRIO. Lo que si va integro por masa: los LED de panel y
# cualquier carga colgada de un solo riel.
I_MASA_SAM17 = 0.050     # A. VCO (~5 mA de desequilibrio) + holgura para
                         # una fila de LED de panel. Pesimista a proposito.
I_MASA_EURO = 0.150      # A. Un modulo Eurorack digital con su regulador de
                         # 5 V colgado de +12 devuelve TODO por masa.

# --- cable de bajada -----------------------------------------------------
SECCION = {"20AWG": 0.518e-6, "24AWG": 0.205e-6, "28AWG": 0.081e-6}
R_CONTACTO = 10e-3       # ohm por contacto crimpado/IDC. Dos por conductor
                         # (un extremo en la placa, otro en el modulo).
                         # Valor de manual para contacto de laton estanado.


def r_plano(largo_mm: float, ancho_mm: float) -> float:
    """Resistencia de un tramo de plano, en ohm."""
    return R_CUADRO * (largo_mm / ancho_mm) / 1000.0


def r_cable(largo_mm: float, awg: str, n_conductores: int) -> float:
    """Resistencia de un cable de bajada, contactos incluidos.

    n_conductores en PARALELO: es el unico sitio del diseno donde duplicar
    un pin divide la resistencia por dos de verdad.
    """
    r_cobre = RHO / SECCION[awg] * (largo_mm / 1000.0)
    return (r_cobre + 2 * R_CONTACTO) / n_conductores


def slots_x() -> list[float]:
    return list(SLOTS_X)


def perfil_plano(corrientes: list[float]) -> list[float]:
    """Potencial de masa en cada slot [V], referido al punto de alimentacion.

    Modelo: los slots cuelgan de una tira de plano alimentada por el CENTRO,
    asi que son dos ramas independientes. Se camina cada rama de dentro hacia
    fuera y cada tramo lleva la suma de las corrientes que quedan por delante.

        feed ---- s3 ---- s2 ---- s1
             I3+I2+I1  I2+I1     I1

    Version anterior de esta funcion cogia un solo tramo feed->slot con la
    corriente de mas alla del slot, y se dejaba fuera la corriente de los
    slots intermedios en el trozo interior. Infravaloraba ~8%.
    """
    xs = slots_x()
    v = [0.0] * N_SLOTS
    for signo in (-1, +1):
        rama = [i for i in range(N_SLOTS)
                if (xs[i] - X_ALIMENTACION) * signo > 0]
        rama.sort(key=lambda i: abs(xs[i] - X_ALIMENTACION))   # de dentro a fuera
        pot, prev = 0.0, X_ALIMENTACION
        for pos, i in enumerate(rama):
            i_tramo = sum(corrientes[k] for k in rama[pos:])    # lo que queda fuera
            pot += i_tramo * r_plano(abs(xs[i] - prev), ANCHO_PLANO_EFECTIVO)
            prev = xs[i]
            v[i] = pot
    return v


def cents(volts: float) -> float:
    return abs(volts) * 1000.0 * CENTS_POR_MV


# --- reglas de diseno que salen de los numeros ---------------------------
REGLA_SEGMENTO = (
    "Los cuatro modulos de la cadena de tono (MIDI/CV + VCO1..3) van en el "
    "MISMO segmento. Si se reparten entre los dos, el desequilibrio entre los "
    "cables de alimentacion de cada segmento se les suma entero."
)
REGLA_MASA_DOBLE = (
    "Los DOS pines de masa de J2 se pueblan siempre. Poblar uno solo dobla el "
    "termino de cable y se sale del presupuesto."
)
REGLA_NO_PTC_EN_MASA = (
    "El PTC va en +12 V y en -12 V. NUNCA en masa: 1.3 ohm en el retorno son "
    "78 mV a 60 mA, o sea 94 cents. Mataria el instrumento."
)


def _autocomprobacion_plano() -> None:
    """perfil_plano() ya estuvo mal una vez. Se contrasta a mano.

    Tres slots por rama a 38/86/134 mm del centro con 150/50/50 mA en las
    posiciones exterior/media/interior. A mano, acumulando de dentro a fuera:

        V(38)  = (0.15+0.05+0.05) * r * 38
        V(86)  = V(38)  + (0.15+0.05) * r * 48
        V(134) = V(86)  +  0.15      * r * 48
    """
    r = R_CUADRO / ANCHO_PLANO_EFECTIVO / 1000.0        # ohm por mm
    v38 = 0.25 * r * 38
    v86 = v38 + 0.20 * r * 48
    v134 = v86 + 0.15 * r * 48
    esperado = [v134, v86, v38, v38, v86, v134]
    obtenido = perfil_plano([I_MASA_EURO, I_MASA_SAM17, I_MASA_SAM17,
                             I_MASA_SAM17, I_MASA_SAM17, I_MASA_EURO])
    for e, o in zip(esperado, obtenido):
        assert abs(e - o) < 1e-9, f"perfil_plano mal: {o*1e6:.1f} != {e*1e6:.1f} uV"


def demo() -> None:
    _autocomprobacion_plano()
    print(f"cobre a {T_OP:.0f} C: {R_CUADRO:.3f} mohm/cuadro\n")

    # ---- 1. el plano, con la cadena de tono junta y cerca del centro ----
    # peor reparto realista: un Euro glotonon en cada punta, los SAM17 dentro
    corr = [I_MASA_EURO, I_MASA_SAM17, I_MASA_SAM17,
            I_MASA_SAM17, I_MASA_SAM17, I_MASA_EURO]
    v = perfil_plano(corr)
    sam17 = v[1:5]
    d_plano = max(sam17) - min(sam17)
    print("perfil de masa del plano [uV]:",
          " ".join(f"{x*1e6:6.1f}" for x in v))
    print(f"  peor par DENTRO de la cadena de tono: {cents(d_plano):.2f} cents")

    # ---- 2. el cable de bajada -----------------------------------------
    r_sam17 = r_cable(150, "24AWG", 2)      # J2: 2 pines de masa
    r_euro = r_cable(150, "28AWG", 6)       # 16 pines: 3 pares de masa = 6
    d_cable = I_MASA_SAM17 * r_sam17
    print(f"\ncable SAM17 (150 mm, 2x24 AWG + contactos): {r_sam17*1000:.1f} mohm"
          f" -> {cents(d_cable):.2f} cents")
    print(f"cable Euro  (150 mm, 6x28 AWG + contactos): {r_euro*1000:.1f} mohm")

    total = cents(d_plano) + cents(d_cable)
    print(f"\nTOTAL cadena de tono: {total:.2f} cents "
          f"(objetivo <= {OBJETIVO_CENTS})")
    assert total <= OBJETIVO_CENTS, f"presupuesto de masa reventado: {total:.2f}"

    # ---- 3. lo que pasa si te saltas cada regla -------------------------
    print("\nsi se rompe cada regla:")
    r_pista = r_plano(160, 5.0)             # pista de 5 mm en vez de plano
    mal_pista = cents(0.35 * r_pista)       # 350 mA por medio segmento
    print(f"  pista de 5 mm en vez de plano ... +{mal_pista:5.2f} cents")
    assert mal_pista > OBJETIVO_CENTS, "la pista deberia suspender"

    r_1masa = r_cable(150, "24AWG", 1)
    print("  un solo pin de masa en J2 ...... "
          f"+{cents(I_MASA_SAM17*(r_1masa - r_sam17)):5.2f} cents")

    r_largo = r_cable(500, "24AWG", 2)
    print("  cable de 500 mm en vez de 150 .. "
          f"+{cents(I_MASA_SAM17*(r_largo - r_sam17)):5.2f} cents")

    # El punto de partida: la tesis, con jumpers en cadena. Aqui el numero no
    # lo pone el cobre sino el CONTACTO, y un Dupont crimpado a mano no es un
    # contacto de 10 mohm: la horquilla de manual es 50-100 mohm, y empeora al
    # oxidarse. Se dan las dos cotas porque la diferencia es 5x y taparla
    # inflando o desinflando el numero seria hacer trampa en las dos
    # direcciones.
    r_cobre_tesis = RHO / SECCION["24AWG"] * 0.5
    for etiqueta, r_c in (("contacto bueno, 10 mohm", 10e-3),
                          ("Dupont real,   75 mohm", 75e-3)):
        r_tesis = r_cobre_tesis + 6 * r_c        # 3 saltos = 6 contactos
        print(f"  daisy-chain tesis ({etiqueta}) {cents(I_MASA_SAM17*r_tesis):6.1f} cents")
    r_tesis = r_cobre_tesis + 6 * 75e-3
    assert cents(I_MASA_SAM17 * r_tesis) > 10 * total, \
        "el daisy-chain deberia ser MUCHO peor; si no, algo esta mal calculado"

    # ---- 4. el PTC jamas en masa ---------------------------------------
    ptc = cents(0.060 * 1.3)                # 60 mA sobre 1.3 ohm
    print(f"\n  PTC puesto en masa por error ... {ptc:5.1f} cents  <- {REGLA_NO_PTC_EN_MASA[:38]}...")
    assert ptc > 50, "el PTC en masa tiene que salir catastrofico"

    print("\nOK: presupuesto cerrado.")


if __name__ == "__main__":
    demo()
