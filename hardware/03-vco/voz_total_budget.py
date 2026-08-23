"""Geometria del modulo de Voz: entran los ocho chips del estereo?

    python voz_total_budget.py

BLOQUEANTE. La spec (modulo-voz-total S8) lo declara VERDE y "se adopta como
puerta", pero el guion no existia: la puerta estaba declarada y no cerrada.
Aqui se escribe, se calibra contra las dos cifras que la spec SI publica, y se
vuelve a correr con lo que el acta le echo encima.

--- Como se calibra, y por que asi ------------------------------------------

La spec publica dos puntos del mismo modelo y ningun modelo:

    ancho 305 mm con factor de ruteo x2,2 (estimado)
    ancho 388 mm es el maximo, y "el ruteo tendria que salir x4,6" para fallar

Dos puntos de una recta dan la recta. De ahi sale:

    ancho(f) = ANCHO_FIJO + K * f      con K = (388-305)/(4,6-2,2) = 34,58
                                       y ANCHO_FIJO = 305 - K*2,2 = 228,9

Y ANCHO_FIJO cae en 228,9 contra los 228,6 mm que mide el modulo 3 v1 (45 HP
exactos). Eso NO es casualidad: el modelo de la spec es "el modulo de cuatro
voces que ya existe, mas lo que el area nueva pide". La reconstruccion se
asevera abajo contra los dos puntos publicados -- si un dia la spec cambia sus
cifras, este guion falla antes de mentir.

--- Y por que el resultado se calcula en RATIO ------------------------------

Las areas de encapsulado de aqui son NOMINALES de catalogo, no medidas de la
libreria de huellas. Usarlas en absoluto seria inventar precision. Se usan solo
para la razon area_nueva/area_v2, donde el error sistematico de las huellas se
cancela: si todas las huellas estan un 10% cortas, la razon no se mueve.

--- Lo que NO esta confirmado -----------------------------------------------

  * Las areas de encapsulado son nominales JEDEC, no de la libreria del
    proyecto. Se miden al dibujar.
  * Los pasivos por canal del filtro, del VCA y del DAC son DECLARADOS. Los
    del oscilador salen del BOM v1 (hardware/03-vco/bom.csv).
  * El factor de ruteo x2,2 sigue siendo el estimado de la spec. No es medida.
  * El ancho de panel de la bahia (100 mm) es el de la spec S8, con sus jacks
    de entonces.
"""
from __future__ import annotations

# --- los dos puntos que la spec publica (S8) --------------------------------
ANCHO_SPEC = 305.0          # mm, con FACTOR_SPEC
ANCHO_MAX_SPEC = 388.0      # mm, y el factor al que fallaria
FACTOR_SPEC = 2.2
FACTOR_FALLO = 4.6

K = (ANCHO_MAX_SPEC - ANCHO_SPEC) / (FACTOR_FALLO - FACTOR_SPEC)
ANCHO_FIJO = ANCHO_SPEC - K * FACTOR_SPEC

ANCHO_V1 = 228.6            # mm. Modulo 3 v1 = 45 HP exactos (45 * 5.08)

# --- la fila, del case ------------------------------------------------------
RIEL_HP = 104               # Z-Rails de Tiptop comprados (case-design S rev.4)
HP = 5.08                   # mm
ANCHO_FILA = RIEL_HP * HP   # 528.32 mm
RESERVA_BORDE = 40.0        # mm. La reserva que la spec S8 ya declaraba.
ANCHO_BAHIA = 100.0         # mm. Panel de 8+8 jacks (spec S8)

# --- areas de encapsulado, NOMINALES de catalogo (ver cabecera) -------------
QFN32_4X4 = 4.0 * 4.0       # SSI2130 (BOM v1: "QFN-32 4x4mm EP")
SOIC16 = 9.9 * 6.0          # LM13700, SSI2164
SOIC14 = 8.65 * 6.0         # TL074 (BOM v1)
TSSOP16 = 5.0 * 6.4         # AD5686R (BOM v1)
TSSOP28 = 9.7 * 6.4         # codec de 24 bits que llega con E-5
PASIVO_0805 = 3.2 * 1.6     # huella con pads

# --- pasivos: los del oscilador salen del BOM v1, el resto son DECLARADOS ---
# BOM v1, por 4 voces: C_TCAP 4 + R_PITCH 4 + R_CVIN 4 + R_SCALE 4 + R_MIX 16
# + R_IV 4 + R_SQ 4 + R_LIN 4 + R_SIN 12 = 56 -> 14 por voz.
PASIVOS_OSC = 14
PASIVOS_FILTRO = 12         # DECLARADO: MS-20 en dos celdas, con sus LEDs
PASIVOS_VCA = 4             # DECLARADO: por VCA (SSI2164 es cuadruple)
PASIVOS_DAC = 6             # DECLARADO: desacoplo + salida, por chip


def area(**piezas: float) -> float:
    return sum(piezas.values())


def area_v2() -> float:
    """Area que el modulo v2 anade sobre el v1 de cuatro voces.

    Censo de la spec S8: "16 SSI2130 + 16 LM13700 + 16 TL074 + 8 SSI2164 +
    DACs". El v1 ya traia 4 SSI2130, 1 TL074 y 3 AD5686R (BOM v1).
    """
    dac_v2 = 12                 # 16 canales x 3 CV / 4 canales por AD5686R
    return area(
        osc=(16 - 4) * QFN32_4X4,
        filtro=16 * SOIC16,
        opamp=(16 - 1) * SOIC14,
        vca=8 * SOIC16,
        dac=(dac_v2 - 3) * TSSOP16,
        pasivos=((16 - 4) * PASIVOS_OSC + 16 * PASIVOS_FILTRO
                 + 32 * PASIVOS_VCA + (dac_v2 - 3) * PASIVOS_DAC)
        * PASIVO_0805,
    )


def area_estereo() -> float:
    """Lo que anade el acta E-6 topologia A: 4 SSI2164 + 4 AD5686R.

    16 VCA de resonancia + 32 de voz = 48 -> 12 SSI2164 (eran 8).
    16 canales x 4 CV = 64 -> 16 AD5686R (eran 12).
    """
    return area(
        vca=4 * SOIC16,
        dac=4 * TSSOP16,
        pasivos=(16 * PASIVOS_VCA + 4 * PASIVOS_DAC) * PASIVO_0805,
    )


def area_mixer() -> float:
    """Lo que anade el acta E-5: el modulo 4 se muda aqui.

    Suma de 16, volumen general, etapa de salida y los oidos (codec 24 bits).
    """
    return area(
        suma=2 * SOIC14,
        codec=1 * TSSOP28,
        pasivos=40 * PASIVO_0805,   # DECLARADO
    )


def ancho(factor: float, area_extra: float = 0.0) -> float:
    """Ancho del modulo con el modelo reconstruido de la spec."""
    escala = (area_v2() + area_extra) / area_v2()
    return ANCHO_FIJO + K * factor * escala


def holgura(a: float, techo: float) -> float:
    return (techo - a) / a


# --- el fondo, con el modelo que la spec S8 SI publica ----------------------
FONDO_DISPONIBLE = 50.0     # mm
FONDO_PANEL = 5.0
FONDO_PCB = 1.6
FONDO_SEPARACION = 10.6     # por piso, dos pisos
PLACAS = 2


def fondo(h_componente: float) -> float:
    return (FONDO_PANEL + FONDO_PCB
            + PLACAS * FONDO_SEPARACION + PLACAS * h_componente)


def demo() -> None:
    print("Geometria del modulo de Voz\n")

    # --- 1. la reconstruccion se demuestra, no se promete ----------------
    print("modelo reconstruido de los dos puntos que publica la spec S8:")
    print(f"  ancho(f) = {ANCHO_FIJO:.1f} + {K:.2f} * f")
    print(f"  ancho({FACTOR_SPEC}) = {ancho(FACTOR_SPEC):.1f} mm "
          f"(la spec dice {ANCHO_SPEC:.0f})")
    print(f"  ancho({FACTOR_FALLO}) = {ancho(FACTOR_FALLO):.1f} mm "
          f"(la spec dice {ANCHO_MAX_SPEC:.0f})")
    print(f"  termino fijo {ANCHO_FIJO:.1f} mm contra el modulo v1 de "
          f"{ANCHO_V1:.1f} mm (45 HP)")
    assert abs(ancho(FACTOR_SPEC) - ANCHO_SPEC) < 0.5
    assert abs(ancho(FACTOR_FALLO) - ANCHO_MAX_SPEC) < 0.5
    assert abs(ANCHO_FIJO - ANCHO_V1) < 1.0, (
        "el termino fijo deberia ser el modulo v1; si se separa, el modelo "
        "reconstruido no es el de la spec y hay que preguntar")
    assert abs(holgura(ANCHO_SPEC, ANCHO_MAX_SPEC) - 0.27) < 0.01, (
        "la spec declara 27% de holgura: si no sale, la lectura esta mal")
    print("  -> reproduce las dos cifras y el 27%. El modelo es el suyo.\n")

    # --- 2. lo que el acta le echa encima ---------------------------------
    a2, ae, am = area_v2(), area_estereo(), area_mixer()
    print("area anadida sobre el modulo v1 (nominal, se usa en RAZON):\n")
    print(f"  v2, dieciseis canales      {a2:8.0f} mm2   (base)")
    print(f"  + estereo A (E-6)          {ae:8.0f} mm2   {ae/a2:+6.1%}")
    print(f"  + mixer y oidos (E-5)      {am:8.0f} mm2   {am/a2:+6.1%}")

    extra = ae + am
    print(f"  = total anadido por el acta {extra:7.0f} mm2   {extra/a2:+6.1%}\n")

    # --- 3. el ancho, antes y despues -------------------------------------
    a_spec = ancho(FACTOR_SPEC)
    a_nuevo = ancho(FACTOR_SPEC, extra)
    print("ancho del modulo de Voz al factor estimado x2,2:\n")
    print(f"  spec de anoche             {a_spec:6.1f} mm")
    print(f"  con estereo y mixer        {a_nuevo:6.1f} mm   "
          f"({a_nuevo - a_spec:+.1f})")

    # --- 4. la fila, con la bahia ya dentro (acta E-3) --------------------
    techo_fila = ANCHO_FILA - RESERVA_BORDE
    fila = a_nuevo + ANCHO_BAHIA
    print(f"\nfila A, con la bahia fundida dentro del modulo (E-3):\n")
    print(f"  Voz {a_nuevo:.1f} + bahia {ANCHO_BAHIA:.0f} = {fila:.1f} mm")
    print(f"  techo: riel de {RIEL_HP} HP = {ANCHO_FILA:.2f} - reserva "
          f"{RESERVA_BORDE:.0f} = {techo_fila:.2f} mm")
    print(f"  holgura: {holgura(fila, techo_fila):.1%}")
    assert fila <= techo_fila, (
        f"la fila A se pasa: {fila:.1f} contra {techo_fila:.1f}")

    # --- 5. a que factor de ruteo se rompe ahora --------------------------
    f = FACTOR_SPEC
    while ancho(f, extra) + ANCHO_BAHIA <= techo_fila:
        f += 0.01
    print(f"\n  se rompe con factor de ruteo x{f:.2f} "
          f"(era x{FACTOR_FALLO:.1f} antes del acta)")
    assert f > 3.0, (
        "si el margen de ruteo baja de x3 el modulo deja de ser robusto a "
        "una estimacion que NADIE ha medido todavia")

    # --- 6. el fondo -------------------------------------------------------
    h_max = (FONDO_DISPONIBLE - FONDO_PANEL - FONDO_PCB
             - PLACAS * FONDO_SEPARACION) / PLACAS
    print(f"\nfondo: {FONDO_PANEL} + {FONDO_PCB} + {PLACAS}x"
          f"{FONDO_SEPARACION} + {PLACAS}xh = {fondo(11.1):.1f} de "
          f"{FONDO_DISPONIBLE:.0f} mm  (h <= {h_max:.1f})")
    print("  los ocho chips nuevos son SOIC y TSSOP, 1,2 y 2,65 mm de alto:")
    print("  no mueven el fondo. La cota la sigue poniendo el jack y el "
          "conector.")
    assert fondo(2.65) < FONDO_DISPONIBLE

    print("\nVEREDICTO: cierra, pero el margen de ruteo se estrecha.")
    print(f"  La holgura del modulo pasa de 27% a "
          f"{holgura(fila, techo_fila):.0%} de fila, y el factor de ruteo al")
    print(f"  que rompe baja de x{FACTOR_FALLO} a x{f:.2f}. Sigue siendo el")
    print("  numero menos medido de todo el diseno: se mide al dibujar la")
    print("  primera columna, no despues.")
    print("\nOK: presupuesto cerrado.")


if __name__ == "__main__":
    demo()
