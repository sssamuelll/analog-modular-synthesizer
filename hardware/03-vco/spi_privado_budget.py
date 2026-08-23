"""El SPI privado del modulo de Voz: cuanto caudal piden las envolventes.

    python spi_privado_budget.py

BLOQUEANTE E INVALIDANTE por spec (modulo-voz-total S3.1 y S9.4): si el caudal
no cierra con las envolventes a 10 kHz, la seccion de generadores CAE. No se
"ajusta en el plan".

Y sirve para lo segundo que la spec dejo abierto: decidir la topologia de
paneo del acta E-6. Dos caminos con el mismo resultado musical:

    A  dos VCA por canal (L/R), cada rama escrita con envolvente x paneo
    B  un VCA de envolvente + etapa de paneo detras, paneo escrito al evento

El acta suponia que A "duplica el caudal" y que por eso B protegia el
presupuesto invalidante. ESTE GUION DESMIENTE ESA SUPOSICION, y el porque
esta en la cuenta de abajo: el CV de corte YA es un flujo a tasa de render.

--- El hallazgo que sale de correr las cuentas -------------------------------

La spec se cuenta mal a si misma. S3.1 dice "8 envolventes x 10 kHz son 80k
escrituras/s por micro" -- una envolvente por canal. Pero S2 dice que el CV de
corte lo escribe el micro sumando "valor base + curva de calibracion +
ENVOLVENTE DE FILTRO LOCAL + modulacion", o sea que el corte es un SEGUNDO
flujo a tasa de render. Y el modulo 6 que desaparece (S1) eran DOS generadores
ADSR en el diseno final de la tesis, no uno.

Asi que la linea base de la spec esta a la mitad de lo que su propio S2
implica, ANTES de meter estereo. Se declara aqui y se mide en los dos casos.

--- Lo que NO esta confirmado -----------------------------------------------

  * SCLK_TECHO no lo declara ninguna spec. Se pone un techo conservador y el
    guion reporta el reloj que HARIA FALTA, para que la decision se tome sobre
    ese numero y no sobre el techo. El maximo real del AD5686R hay que leerlo
    de la hoja antes de moverlo.
  * F_EVENTOS y F_PARAM son cotas DECLARADAS de peor caso musical, no medidas.
  * EFICIENCIA (CS, huecos entre transferencias) es declarada.
"""
from __future__ import annotations

# --- lo que la topologia del modulo fija (citado) ---------------------------
CANALES_POR_MICRO = 8       # dieciseis S3: "ocho osciladores por micro es lo
                            # que hace que la cuenta del PIO cierre"
MICROS = 2                  # maestro + esclavo, una columna cada uno
F_RENDER = 10_000.0         # Hz. voz-total S3.1, tras H-BP1
BITS_DAC = 24               # palabra del AD5686R. orquestacion S8 cambio 1:
                            # BITS_TRAMA = N_DACS * 24
F_TONO = 1_000.0            # Hz. orquestacion R-M4: tasa minima del bloque
                            # de tono por modulo

# --- cotas declaradas (peor caso musical, NO medidas) -----------------------
F_EVENTOS = 100.0           # Hz por micro. Ocho canales redisparando a 12,5 Hz
                            # cada uno: mas rapido que cualquier arpegio real.
F_PARAM = 100.0             # Hz. Resonancia y demas parametros lentos, movidos
                            # por perilla o por el agente.
EFICIENCIA = 0.60           # Fraccion util del reloj: CS, huecos entre tramas
                            # y el resto de inquilinos del bus privado.

# --- los otros inquilinos del SPI privado (citados) -------------------------
# dieciseis: "Los registros cuelgan del SPI privado, no del bus del
# instrumento." Y desde el acta E-3, tambien el crosspoint de la bahia.
BITS_REGISTROS = 16         # cadena de registros de desplazamiento
F_REGISTROS = 100.0         # Hz
BITS_CROSSPOINT = 256       # AD75019, imagen sombra completa (voz-total S5.3)
F_CROSSPOINT = 10.0         # Hz. Cota generosa: reconfigurar el patch diez
                            # veces por segundo ya es mas de lo que hacen una
                            # mano o un preset.
BITS_ESCLAVO = 64           # mensaje maestro->esclavo, por evento y por trama
F_ESCLAVO = F_EVENTOS + F_TONO

RELOJ_MICRO = 150e6         # Hz. autotune_budget.py: F_PIO = 150e6

SCLK_TECHO = 20e6           # Hz. DECLARADO, no citado (ver cabecera).


def flujos(env_por_canal: int, paneo_render: int, paneo_evento: int) -> dict:
    """bits/s en el SPI privado de UN micro (una columna de 8 canales).

    env_por_canal -- CV escritos a tasa de render (corte, envolvente de VCA...)
    paneo_render  -- CV de paneo escritos a tasa de render (topologia A)
    paneo_evento  -- CV de paneo escritos al evento de nota (topologia B)
    """
    n = CANALES_POR_MICRO
    return {
        "envolventes": n * env_por_canal * F_RENDER * BITS_DAC,
        "paneo (render)": n * paneo_render * F_RENDER * BITS_DAC,
        "paneo (evento)": n * paneo_evento * F_EVENTOS * BITS_DAC,
        "tono": n * F_TONO * BITS_DAC,
        "parametros lentos": n * F_PARAM * BITS_DAC,
        "registros": BITS_REGISTROS * F_REGISTROS,
        "crosspoint": BITS_CROSSPOINT * F_CROSSPOINT,
        "enlace esclavo": BITS_ESCLAVO * F_ESCLAVO,
    }


def reloj_necesario(bits_s: float) -> float:
    return bits_s / EFICIENCIA


def ciclos_por_muestra(env_por_canal: int, paneo_render: int) -> float:
    """Ciclos de CPU disponibles por cada valor de envolvente calculado."""
    muestras_s = (CANALES_POR_MICRO * (env_por_canal + paneo_render) * F_RENDER)
    return RELOJ_MICRO / muestras_s


CASOS = (
    ("spec S3.1 (1 envolvente/canal, mono)", 1, 0, 0),
    ("lo que S2 implica (2 env/canal, mono)", 2, 0, 0),
    ("ESTEREO A (2 env + L/R a render)", 3, 0, 0),
    ("ESTEREO B (2 env + paneo al evento)", 2, 0, 2),
)


def demo() -> None:
    print("SPI privado del modulo de Voz -- caudal por micro (8 canales)\n")
    print(f"  render {F_RENDER/1e3:.0f} kHz | palabra AD5686R {BITS_DAC} bits"
          f" | eficiencia declarada {EFICIENCIA:.0%}\n")

    res = {}
    for nombre, env, pan_r, pan_e in CASOS:
        total = sum(flujos(env, pan_r, pan_e).values())
        sclk = reloj_necesario(total)
        res[nombre] = sclk
        estado = "OK" if sclk <= SCLK_TECHO else "<<< NO CABE"
        print(f"  {nombre:38s} {total/1e6:6.2f} Mbit/s  ->  SCLK "
              f"{sclk/1e6:5.2f} MHz  ({SCLK_TECHO/sclk:.1f}x)  {estado}")

    print(f"\n  techo declarado: SCLK {SCLK_TECHO/1e6:.0f} MHz\n")

    peor = flujos(3, 0, 0)
    suma = sum(peor.values())
    print("desglose del peor caso (estereo A):\n")
    for k, v in sorted(peor.items(), key=lambda kv: -kv[1]):
        if v:
            print(f"  {k:20s} {v/1e6:6.3f} Mbit/s  ({v/suma:5.1%})")

    sclk_a = res["ESTEREO A (2 env + L/R a render)"]
    sclk_b = res["ESTEREO B (2 env + paneo al evento)"]
    print(f"\nA contra B: {sclk_a/sclk_b:.2f}x de caudal, no 2x.")
    print("  El acta E-6 suponia que A duplicaba el trafico. No lo duplica:")
    print("  el CV de corte YA es un flujo a tasa de render en las dos, asi")
    print("  que A pasa de dos flujos por canal a tres, no de uno a dos.")

    assert sclk_b <= SCLK_TECHO, "B tiene que caber; si no, S3 cae entera"
    assert sclk_a <= SCLK_TECHO, (
        f"A necesita {sclk_a/1e6:.1f} MHz contra un techo de "
        f"{SCLK_TECHO/1e6:.0f} MHz: si esto salta, B deja de ser opcional")
    assert sclk_a / sclk_b < 1.6, (
        "si A pidiera 1.6x o mas, el argumento del acta se sostendria")

    print("\nlo que de verdad aprieta no es el bus, es el nucleo 1:")
    for nombre, env, pan_r in (("mono, 2 env/canal", 2, 0),
                               ("estereo A", 3, 0)):
        c = ciclos_por_muestra(env, pan_r)
        estado = "OK" if c >= 300 else "<<< APRETADO"
        print(f"  {nombre:20s} {c:5.0f} ciclos por valor de envolvente a "
              f"{RELOJ_MICRO/1e6:.0f} MHz  {estado}")
    assert ciclos_por_muestra(3, 0) >= 300, (
        "menos de 300 ciclos por muestra deja sin sitio al esclavo J2 y al "
        "drenaje de PIO que comparten ese micro (voz-total S3.4)")

    print(f"\n  y el modulo entero son {MICROS} micros con este mismo reparto:")
    print("  los buses son independientes, uno por columna.")

    print("\nVEREDICTO: el SPI privado NO es la restriccion que decide E-6.")
    print("  Las dos topologias caben con holgura. La decision se muda a")
    print("  cobre y corriente -- voz_total_budget.py y consumo_total.py --")
    print("  donde A gana por 8 chips menos. B deja de estar justificada.")
    print("\nOK: presupuesto cerrado.")


if __name__ == "__main__":
    demo()
