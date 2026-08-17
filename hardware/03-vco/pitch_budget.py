"""La apuesta trimless, en numeros: cuanta dispersion de chip aguanta la placa.

    python pitch_budget.py

El modulo 3 no tiene un solo trimmer. La escala de tono la fijan la ADR4525 y
resistencias del 1 %, y el autoafinado absorbe el resto (spec par.11.2). La
apuesta es que los cuatro SSI2130 reales quepan en el margen. Hasta ahora esa
apuesta estaba escrita en prosa y su unica evaluacion era "medir la placa".

Esto la convierte en un numero ANTES de la placa: **con las resistencias en su
peor caso, cuanto se puede desviar el convertidor exponencial de un chip antes
de que su voz suspenda**, y con que probabilidad suspende una placa entera de
cuatro voces para una dispersion dada.

## Por que esto y no SPICE

`simulations/vco/` sigue vacio y no es un olvido -- ver su README. El camino de
tono de esta placa es un nodo de suma de CORRIENTES sin un solo amplificador:
R_PITCH desde el DAC, R_CVIN desde el jack, R_LIN desde VREF, las tres contra
la entrada del convertidor exponencial. Ahi SPICE no anade nada que no diga la
ley de Ohm. Y del SSI2130 no hay modelo publico, asi que la parte que SI se
beneficiaria de SPICE es justo la que no se puede simular.

Lo que decide el exito no es la forma de onda: es una tolerancia estadistica.
Eso se calcula.

## El modelo, y de donde sale cada numero

Todo de `bom.csv` de este modulo y de `notes/bring-up.md` par.5, que a su vez
citan el datasheet:

    I_fondo_escala = VREF / R_PITCH = 2.5 / 16.5k = 151.5 uA      (bom.csv)
    I_OCT          = 20 uA por octava                             (bring-up par.5)
    span           = 151.5 / 20 = 7.576 octavas
    objetivo       = 7.0 octavas (84 notas, C1-C8)

    I_escala expo  = VREF / R_SCALE = 2.5 / 26.7k = 93.6 uA       (bom.csv)
    I_lineal       = VREF / R_LIN   = 2.5 / 499k  = 5.01 uA       (bom.csv)

## Los dos spans, que no son el mismo criterio

`bring-up.md` par.5 define dos, y solo uno es la puerta:

  * **B, extrapolado**: la pendiente del expo por 65535. Es el criterio de
    aprobado (B >= 7.0) y **no depende de R_LIN**.
  * **A, usable**: log2(f(0xFFFF)/f(0x0000)). Sale MENOR que B porque los
    5.01 uA fijos de R_LIN levantan el suelo. Se calcula aqui abajo, pero no
    decide nada -- y confundirlos manda al bodge equivocado.

## VREF no protege el span (y eso esta bien)

Las dos corrientes cuelgan del MISMO nodo VREF: la de fondo de escala por
R_PITCH y la de escala del expo por R_SCALE. En el cociente que da el span,
VREF se cancela a primer orden. O sea que los 2 ppm/C de la ADR4525 **no son
lo que sostiene la apuesta trimless**: sostienen la afinacion ABSOLUTA entre
pasadas del autoafinado, que es de lo que habla dac_local_budget.py. Aqui su
tolerancia inicial (+-0.02 %) entra tres ordenes de magnitud por debajo del
margen del 7.6 % y se calcula igual, para dejar demostrado que no importa.

## Lo NO confirmado (Principio I)

  * **Que I_OCT sea exactamente proporcional a I_escala** (o sea, a 1/R_SCALE)
    es una relacion INTERNA del chip que no esta verificada contra datasheet
    aqui. Se modela asi porque es la topologia estandar de un convertidor
    exponencial con corriente de escala externa, y porque el bring-up manda
    tocar R_SCALE para mover el span. Si la relacion fuese otra, lo que cambia
    es cuanto pesa la tolerancia de R_SCALE -- un termino del 1 % dentro de un
    margen del 7.6 %. La conclusion no se mueve; el reparto de culpas si.
  * **La dispersion chip a chip del convertidor exponencial no la garantiza
    ningun datasheet.** Es EL numero desconocido y por eso aqui se BARRE en vez
    de suponerse: la salida es "cuanta dispersion se aguanta", no "cuanto se
    espera". Cerrarlo pide medir los cuatro chips (bring-up par.5).
  * **La razon I_lineal / I_expo(codigo 0)** decide cuanto se comprime A frente
    a B. Se toma I_expo(0) = I_escala, que es lo natural si la corriente de
    escala fija el suelo del exponencial, pero tampoco esta verificado. Por eso
    A se barre en un rango y no se publica un solo numero.
"""
from __future__ import annotations

import math
import random

# --- fuentes primarias: bom.csv de este modulo ------------------------------
VREF = 2.5              # V     ADR4525BRZ
R_PITCH = 16.5e3        # ohm   1 %
R_SCALE = 26.7e3        # ohm   1 %
R_LIN = 499e3           # ohm   1 %
TOL_R = 0.01            # 1 %, resistencias E96
TOL_VREF = 0.0002       # +-0.02 % de precision inicial (bring-up par.1)

# --- de notes/bring-up.md par.5 (que cita el datasheet) ---------------------
I_OCT = 20e-6           # A por octava en la entrada del expo
OBJETIVO = 7.0          # octavas. 84 notas, C1-C8
VOCES = 4

SEMILLA = 20260817      # Monte Carlo reproducible: un gate que da un numero
                        # distinto cada corrida no es un gate.
N = 40000


def span_B(vref: float = VREF, r_pitch: float = R_PITCH,
           r_scale: float = R_SCALE, e_chip: float = 0.0) -> float:
    """Span extrapolado, en octavas. Es el criterio de aprobado.

    I_OCT se escala con R_SCALE (1/R_SCALE, ver 'lo NO confirmado') y con el
    error propio del chip. VREF entra en las dos corrientes y se cancela sola:
    no se le quita a mano para que el barrido lo demuestre en vez de asumirlo.
    """
    i_fondo = vref / r_pitch
    i_oct = I_OCT * (R_SCALE / r_scale) * (vref / VREF) * (1.0 + e_chip)
    return i_fondo / i_oct


def span_A(b: float, razon_lin: float) -> float:
    """Span usable. razon_lin = I_lineal / I_expo(codigo 0).

    Los 5 uA fijos de R_LIN se suman a la corriente del nucleo, asi que la nota
    mas grave sale mas aguda de lo que predice la recta y el recorrido usable
    se comprime por abajo. No es un fallo: sin esa corriente el oscilador se
    para (datasheet pag. 5 y 9).
    """
    return math.log2((2.0 ** b + razon_lin) / (1.0 + razon_lin))


def bodge_r_pitch(b_medido: float, objetivo: float = 7.5) -> float:
    """La R_PITCH de recambio que manda bring-up.md par.5."""
    return R_PITCH * b_medido / objetivo


def autocomprobacion() -> None:
    """Contra las cuentas hechas a mano en bom.csv y bring-up.md par.5.

    Si el modelo no reproduce los numeros que ya estaban escritos y revisados,
    el que esta mal es el modelo.
    """
    assert abs(VREF / R_PITCH - 151.5e-6) < 0.1e-6, "I de fondo de escala"
    assert abs(VREF / R_SCALE - 93.6e-6) < 0.2e-6, "I de escala del expo"
    assert abs(VREF / R_LIN - 5.01e-6) < 0.02e-6, "I lineal de R_LIN"
    assert abs(span_B() - 7.576) < 0.002, f"span nominal: {span_B():.4f}"

    # VREF se cancela: moverla un 1 % entero no puede mover el span.
    assert abs(span_B(vref=VREF * 1.01) - span_B()) < 1e-9, \
        "VREF no se cancela en el modelo -- revisa span_B"

    # La tabla de bodges de bring-up.md par.5, punto por punto.
    for b_med, r_esperada in ((7.0, 15.40e3), (6.8, 14.96e3),
                              (6.5, 14.30e3), (6.0, 13.20e3)):
        r = bodge_r_pitch(b_med)
        assert abs(r - r_esperada) < 10.0, \
            f"la tabla de bodges no cuadra en B={b_med}: {r:.0f} != {r_esperada:.0f}"

    # A tiene que salir por DEBAJO de B, siempre, y converger a B si R_LIN->inf.
    assert span_A(7.576, 0.0535) < 7.576
    assert abs(span_A(7.576, 0.0) - 7.576) < 1e-12

    # El "margen de diseno: 7.6 %" que bring-up.md par.5 declara en prosa.
    margen = 1.0 - OBJETIVO / span_B()
    assert abs(margen - 0.076) < 0.001, \
        f"el margen del 7.6 % de bring-up.md par.5 no sale: {100*margen:.2f} %"
    print("autocomprobacion OK (corrientes, span nominal, cancelacion de VREF, "
          "tabla de bodges, margen del 7.6 %)")


def peor_caso() -> float:
    """B con TODAS las tolerancias pasivas alineadas en contra, sin error de chip."""
    return span_B(vref=VREF * (1 - TOL_VREF), r_pitch=R_PITCH * (1 + TOL_R),
                  r_scale=R_SCALE * (1 - TOL_R))


def monte_carlo(sigma_chip: float, rnd: random.Random) -> tuple[float, float]:
    """(rendimiento por voz, rendimiento por placa de 4 voces), en tanto por uno.

    Resistencias: uniforme dentro de su tolerancia. Es lo honesto para un lote
    del 1 % -- la distribucion real de un fabricante no es gaussiana y suponerla
    gaussiana infla el rendimiento regalando cola.

    Chip: gaussiana de media 0. La dispersion de un proceso si lo es, y ademas
    es el reparto que MAS castiga en la cola, que es donde vive el fallo.
    """
    voces_ok = placas_ok = 0
    for _ in range(N):
        placa_ok = True
        for _ in range(VOCES):
            b = span_B(
                vref=VREF * (1 + rnd.uniform(-TOL_VREF, TOL_VREF)),
                r_pitch=R_PITCH * (1 + rnd.uniform(-TOL_R, TOL_R)),
                r_scale=R_SCALE * (1 + rnd.uniform(-TOL_R, TOL_R)),
                e_chip=rnd.gauss(0.0, sigma_chip))
            if b >= OBJETIVO:
                voces_ok += 1
            else:
                placa_ok = False
        placas_ok += placa_ok
    return voces_ok / (N * VOCES), placas_ok / N


def demo() -> None:
    autocomprobacion()
    nominal, peor = span_B(), peor_caso()

    print(f"\nspan extrapolado B (el criterio: B >= {OBJETIVO:.1f} octavas)\n")
    print(f"  {'':36} {'span':>9}   {'se puede perder':>15}")
    print(f"  nominal                              {nominal:9.3f}   "
          f"{100*(1 - OBJETIVO/nominal):14.1f} %")
    print(f"  pasivos en su PEOR caso (R 1 %)      {peor:9.3f}   "
          f"{100*(1 - OBJETIVO/peor):14.1f} %")
    tolerable = 1.0 - OBJETIVO / peor
    print(f"\n  'se puede perder' es la fraccion del span que se puede ir antes de\n"
          f"  suspender -- la misma definicion del 7.6 % de bring-up.md par.5.\n"
          f"  -> con las tres resistencias en contra, al chip todavia le quedan\n"
          f"     {100*tolerable:.1f} % de desviacion propia antes de que la voz caiga.")

    assert nominal > 7.5, f"el span nominal se cayo a {nominal:.3f}"
    assert peor > OBJETIVO, \
        (f"PASIVOS SOLOS suspenden ({peor:.3f} < {OBJETIVO}): la apuesta trimless "
         f"ya no depende del chip, depende de las resistencias. Re-elige valores.")
    assert tolerable > 0.05, \
        (f"solo quedan {100*tolerable:.1f} % para el chip. Por debajo del 5 % la "
         f"apuesta trimless deja de ser razonable sin dato de dispersion.")

    print(f"\nrendimiento frente a la dispersion chip a chip ({N} placas por fila)")
    print("dispersion es la sigma del error del convertidor exponencial.\n")
    print(f"  {'sigma chip':>10} | {'voces OK':>9} | {'placas 4/4 OK':>13} | "
          f"{'bodges por 100 placas':>21}")
    print("  " + "-" * 66)
    rnd = random.Random(SEMILLA)
    tope = None
    for sigma in (0.005, 0.010, 0.015, 0.020, 0.025, 0.030, 0.040):
        r_voz, r_placa = monte_carlo(sigma, rnd)
        if r_placa >= 0.95:
            tope = sigma
        print(f"  {100*sigma:8.1f} % | {100*r_voz:7.2f} % | {100*r_placa:11.2f} % | "
              f"{100*VOCES*(1-r_voz):21.1f}")

    print(f"\n  -> con dispersion de hasta {100*tope:.1f} % sigma, 95 de cada 100 "
          f"placas salen\n     sin tocar una resistencia. El bodge previsto en "
          f"bring-up.md par.5 cubre el resto.")
    assert tope is not None and tope >= 0.02, \
        ("el diseno no aguanta ni un 2 % de sigma con 95 % de placas limpias: "
         "eso ya no es una apuesta, es un trimmer que falta")

    # --- el span usable A, y por que no es la puerta ------------------------
    print(f"\nspan usable A (lo que el instrumento toca de verdad)")
    print("  razon I_lineal/I_expo(0) no esta confirmada -- se barre:\n")
    print(f"  {'razon':>8} | {'A':>7} | {'compresion frente a B':>21}")
    print("  " + "-" * 44)
    for razon in (0.027, 0.0535, 0.107):
        a = span_A(nominal, razon)
        print(f"  {razon:8.4f} | {a:6.3f}  | {nominal - a:20.3f} oct")
    a_nom = span_A(nominal, (VREF / R_LIN) / (VREF / R_SCALE))
    print(f"\n  con I_expo(0) = I_escala (93.6 uA): A = {a_nom:.3f} oct, "
          f"{nominal - a_nom:.3f} por debajo de B.")
    print(f"  Sigue por encima del objetivo de {OBJETIVO:.1f}: la compresion de "
          f"R_LIN no se come la apuesta.")
    assert a_nom > OBJETIVO, \
        (f"A cae por debajo de {OBJETIVO} ({a_nom:.3f}): entonces el bodge no es "
         f"R_PITCH sino SUBIR R_LIN (bring-up par.5), y son distintos")

    # --- un fleco de la tabla de bodges, dicho en voz alta (Principio VII) --
    b_med = 7.0
    r_75, r_real = bodge_r_pitch(b_med), bodge_r_pitch(b_med, nominal)
    print(f"\nfleco: la tabla de bodges de bring-up.md par.5 normaliza contra 7.5 "
          f"y no\ncontra el span nominal de {nominal:.3f}. Para B medido = 7.0 pide "
          f"{r_75/1e3:.2f} k\ncuando la cuenta exacta da {r_real/1e3:.2f} k: "
          f"{100*(r_75/r_real - 1):.1f} % de resistencia de mas, o sea "
          f"{100*(r_75/r_real - 1):.1f} % menos\nde span del que se podria "
          f"recuperar. Sobra margen, asi que no se toca -- pero el\nnumero es ese "
          f"y no un redondeo inocente.")

    # --- lo que este calculo NO cubre --------------------------------------
    print("\nlo que este presupuesto NO cubre:")
    print("  * la LINEALIDAD dentro del span (0.3 % de no conformidad del expo, "
          "~3.6 cents):\n    se la come la tabla de 84 notas de tuning.json, y se "
          "mide en bring-up par.5")
    print("  * la DERIVA TERMICA del span: es C_TCAP (C0G) y la compensacion en "
          "chip.\n    Vive en el Paso 7 del bring-up, no aqui")
    print("  * la afinacion ABSOLUTA y su deriva entre pasadas: dac_local_budget.py")
    print("  * la diafonia entre voces por R_MIX y PWM_CV: bring-up par.8")
    print("\nOK: presupuesto cerrado.")


if __name__ == "__main__":
    demo()
