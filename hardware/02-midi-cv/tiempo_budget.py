#!/usr/bin/env python3
"""Presupuesto de aterrizaje: cuanto puede desviarse «cae en el 1».

Spec: `docs/superpowers/specs/2026-08-17-tiempo-musical-design.md` par.9.

Tiene la forma de `autotune_budget.py`, que es la que ya demostro servir en
este repo: **se deriva lo derivable, y el termino que queda se despeja en
requisito** en vez de suponerle un valor.

    derivado   la trama del J2, que sale del contrato congelado del modulo 3
    despejado  cuanto puede tardar la deteccion del flanco de CLOCK IN

EL OBJETIVO MUSICAL, CON FUENTE
-------------------------------
El unico numero de todo esto que no sale de un contrato del repo ni de una
cuenta. Buscado en la literatura de percepcion auditiva:

  «Thresholds for judging two auditory events as asynchronous range between
   2 and 60 milliseconds»

Ese rango es tan ancho porque el *tiempo de ataque percibido* depende del
instrumento: unos pocos milisegundos en un hi-hat cerrado, entre 50 y 100 ms
en una nota de violin con arco lento.

  https://en.wikipedia.org/wiki/Perceptual_attack_time
  https://link.springer.com/article/10.3758/BF03207341

Un sinte con gates rapidos vive en el extremo apretado, asi que se diseña
contra los **2 ms** — y con la mitad de margen, porque diseñar justo en el
umbral significa que el oyente mas fino si lo nota.
"""

# --- La trama del J2: por el enlace que la lleva (#210 D2/D5, S7: "patch") ---
#
# Era «72 bits a 10 MHz», el contrato congelado del modulo 3. Ese contrato
# paso a dialecto legado: el evento viaja por el enlace privado de la Voz, y
# lo que puede tener delante en ese enlace es su trama mas larga declarada
# (hoy el SET de dieciseis, 824 bits) al reloj al que ESE enlace corre. Las
# dos cosas las da trama_j2_budget.py; aqui no se declara ninguna.
import trama_j2_budget as tj

_VOZ = tj.enlace("Voz total")
BITS_TRAMA_J2 = _VOZ.trama_mas_larga_bits()
T_TRAMA_J2 = _VOZ.t_trama_mas_larga_s()

# F_SYS era el reloj del RP2350; se retiro al nivelar al N657 porque no se usaba.

# --- El objetivo musical, con fuente ---
UMBRAL_ASINCRONIA_S = 2e-3  # el extremo apretado del rango documentado
MARGEN = 0.5                # se diseña a la mitad del umbral, no justo en el
OBJETIVO_S = UMBRAL_ASINCRONIA_S * MARGEN

# --- Lo que la spec del tiempo musical ya fijo ---
PPQN_INTERNO = 96           # rejilla.rs
TIMEOUT_RUEDA_LIBRE_S = 0.5  # reloj.rs
BPM_MIN, BPM_MAX = 20.0, 300.0  # el rango del parametro `tempo`


def deteccion_max(objetivo_s: float = OBJETIVO_S) -> float:
    """Cuanto puede tardar la deteccion del flanco de CLOCK IN, en segundos.

    El termino que queda no se supone: se despeja. Igual que el 74HC14 de
    `autotune_budget.py` acabo siendo «puede temblar hasta 131 ns».
    """
    return objetivo_s - T_TRAMA_J2


def pulso_interno_s(bpm: float) -> float:
    """Cuanto dura un pulso de la rejilla interna."""
    return 60.0 / bpm / PPQN_INTERNO


def ventana_aterrizaje_en_pulsos(bpm: float, objetivo_s: float = OBJETIVO_S) -> float:
    """La `ventana` de `siguiente_borde`, en pulsos internos.

    Es lo que consume `servidor.rs::VENTANA_ATERRIZAJE`: si el sistema no
    puede colocar nada con mas precision que esto, cualquier cosa que llegue a
    menos de esta distancia de un borde esta, para todo lo que se puede oir,
    EN ese borde.
    """
    return objetivo_s / pulso_interno_s(bpm)


def error_tempo_max_mbpm(bpm: float, objetivo_s: float = OBJETIVO_S) -> float:
    """Cuanto puede errar la lectura de tempo, en milesimas de BPM.

    Mientras llegan pulsos la fase la manda el pulso, no la estimacion: el
    tempo estimado solo desvia la fase mientras se rueda libre. Asi que el
    error tolerable sale de ahi, no del gusto.
    """
    eps = objetivo_s / TIMEOUT_RUEDA_LIBRE_S
    return eps * bpm * 1000.0


def demo() -> None:
    print("Presupuesto de aterrizaje del tiempo musical")
    print("=" * 62)
    print(f"  umbral de asincronia (literatura) : {UMBRAL_ASINCRONIA_S*1e3:.1f} ms")
    print(f"  objetivo de diseño (mitad)        : {OBJETIVO_S*1e3:.1f} ms")
    print()
    print(f"  trama mas larga del enlace Voz    : {BITS_TRAMA_J2} bits a "
          f"{_VOZ.reloj_operacion_hz()/1e6:.0f} MHz = {T_TRAMA_J2*1e6:.1f} us")
    print(f"  deteccion del flanco (despejada)  : {deteccion_max()*1e6:.0f} us maximo")
    print()

    # El enlace no puede ser un termino real del presupuesto: si lo fuera, el
    # cuello de botella habria vuelto al cable y habria que sancionar mas
    # reloj en ese enlace (R-P4) o partir la trama.
    assert T_TRAMA_J2 < 0.1 * OBJETIVO_S, (
        "la trama del J2 tiene que ser despreciable frente al objetivo musical. "
        "Si no lo es, el cuello volvio a ser el enlace: hay que sancionar mas "
        "reloj en el enlace de la Voz o aflojar el objetivo"
    )
    # R-E1 (evento D4) es este mismo 10 %, y vive como constante en
    # trama_j2_budget.py para que el arbitro por enlace la aplique a todo
    # mensaje declarado. Que no se desincronicen:
    assert abs(tj.T_MENSAJE_MAX_S - 0.1 * OBJETIVO_S) < 1e-12, (
        "R-E1 en trama_j2_budget.py ya no es el 10 % del objetivo musical")
    # Y que lo que se toma sea la trama MAS LARGA: el bloque de tono viaja
    # por este enlace, asi que ninguna cota puede ser mas corta que el. Sin
    # esto, tomar la mas corta (el evento, 50 bits) pasaria el 10 % igual y
    # nadie se enteraria.
    assert BITS_TRAMA_J2 >= tj.BITS_BLOQUE_TONO, (
        f"la trama mas larga del enlace mide {BITS_TRAMA_J2} bits y el bloque "
        f"de tono que viaja por el mide {tj.BITS_BLOQUE_TONO}: no es la mas larga")
    print(f"  la trama se lleva el {T_TRAMA_J2/OBJETIVO_S*100:.1f} % del presupuesto")
    print()

    print("La ventana de aterrizaje, en pulsos de la rejilla interna:")
    peor = 0.0
    for bpm in (BPM_MIN, 60.0, 120.0, 174.0, BPM_MAX):
        v = ventana_aterrizaje_en_pulsos(bpm)
        peor = max(peor, v)
        print(f"  {bpm:5.0f} BPM : 1 pulso = {pulso_interno_s(bpm)*1e3:5.2f} ms"
              f"  ->  ventana = {v:.3f} pulsos")
    print()

    # EL RESULTADO QUE IMPORTA: la rejilla interna es MAS GRUESA que el error
    # de tiempo a cualquier tempo del rango. Asi que la ventana correcta es
    # cero, y no por conservadurismo: por aritmetica.
    assert peor < 1.0, (
        "si la ventana pasara de un pulso, `siguiente_borde` tendria que "
        "empezar a tratar llegadas tardias como puntuales — y hoy no hace "
        "falta porque la rejilla es mas gruesa que el error"
    )
    print(f"  VENTANA_ATERRIZAJE = 0 pulsos  (el peor caso son {peor:.3f})")
    print("  -> la rejilla interna es MAS GRUESA que el error de tiempo a")
    print("     cualquier tempo del rango. No es conservadurismo: es la cuenta.")
    print()

    print("El techo del error de tempo (reloj.rs::ERROR_TEMPO_MAX_MBPM):")
    e120 = error_tempo_max_mbpm(120.0)
    print(f"  a 120 BPM : {e120:.0f} milesimas de BPM")
    assert abs(e120 - 240.0) < 1.0, (
        "reloj.rs::ERROR_TEMPO_MAX_MBPM vale 240 y sale de esta misma cuenta. "
        "Si este numero cambia, esa constante hay que cambiarla con el"
    )
    print("  cuadra con la constante de reloj.rs, que sale de aqui")
    print()
    print("OK")


if __name__ == "__main__":
    demo()
