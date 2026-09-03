'''Las curvas publicadas que dimensionan la fuente v4, leidas una sola vez.

    python hardware/01-power-supply/v4/curvas.py

## Por que existe

El derating y el PSRR no aparecen como tablas en las hojas: son trazos. La v1
del papel de la fuente dejo como HUECO cifras que estaban dibujadas y razono el
liston con una curva incompleta. Este modulo conserva la lectura ocular hecha
el 2026-09-03, junto a la pagina, figura y condicion que permiten repetirla.

Las polilineas de los IRM terminan en el ultimo punto publicado, a 85 C. En ese
punto todavia queda la fraccion que dibuja la hoja; por encima, el modulo queda
fuera de su rango y la funcion devuelve cero. El PSRR solo se interpola dentro
del intervalo realmente dibujado: los LM llegan a 1 MHz y los LT a 10 MHz.

## Como se leyo

Los puntos de derating siguen las lineas auxiliares de las figuras. Los puntos
de PSRR se leyeron sobre el eje logaritmico; 65 kHz cae entre las marcas de
10 kHz y 100 kHz y por eso cada lectura a esa frecuencia se marca con ~. No son
especificaciones garantizadas: las hojas las publican como curvas tipicas y el
presupuesto de rizado debe conservar esa distincion.
'''
from __future__ import annotations

import math
import os
import sys


# --- derating de los modulos IRM -------------------------------------------
# Cada tupla es (temperatura del aire en C, fraccion de potencia de placa).
DERATING: dict[str, tuple[tuple[float, float], ...]] = {
    'IRM-20': (
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo OTHERS: codo visible a 100 %.
        (50.0, 1.00),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo OTHERS: cruce de 60 C y 75 %.
        (60.0, 0.75),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo OTHERS: cruce de 70 C y 50 %.
        (70.0, 0.50),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo OTHERS: cruce de 80 C y 20 %.
        (80.0, 0.20),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo OTHERS: ultimo punto, 85 C y 5 %.
        (85.0, 0.05),
    ),
    'IRM-20/5V': (
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo 3.3V,5V: codo visible a 100 %.
        (45.0, 1.00),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo 3.3V,5V: cruce de 50 C y ~80 %.
        (50.0, 0.80),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo 3.3V,5V: cruce de 60 C y 70 %.
        (60.0, 0.70),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo 3.3V,5V: cruce de 70 C y 50 %.
        (70.0, 0.50),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo 3.3V,5V: cruce de 80 C y 20 %.
        (80.0, 0.20),
        # meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo 3.3V,5V: ultimo punto, 85 C y 5 %.
        (85.0, 0.05),
    ),
    'IRM-45': (
        # meanwell-irm-45-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo unico: codo visible a 100 %.
        (50.0, 1.00),
        # meanwell-irm-45-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo unico: cruce de 60 C y 75 %.
        (60.0, 0.75),
        # meanwell-irm-45-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo unico: cruce de 70 C y 50 %.
        (70.0, 0.50),
        # meanwell-irm-45-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo unico: ~33 %, entre 25 y 50 %.
        (80.0, 0.33),
        # meanwell-irm-45-spec-2025-11-21.pdf, p. 3, Derating Curve,
        # 230 Vac, trazo unico: ultimo punto, 85 C y 25 %.
        (85.0, 0.25),
    ),
}


def derating(t_amb_c: float, curva: str) -> float:
    '''Interpola la fraccion de placa a la temperatura del aire circundante.'''
    try:
        puntos = DERATING[curva]
    except KeyError as exc:
        raise ValueError(f'curva de derating desconocida: {curva}') from exc

    if t_amb_c <= puntos[0][0]:
        return 1.0
    if t_amb_c > puntos[-1][0]:
        return 0.0
    for (t0, f0), (t1, f1) in zip(puntos, puntos[1:]):
        if t0 <= t_amb_c <= t1:
            k = (t_amb_c - t0) / (t1 - t0)
            return f0 + k * (f1 - f0)
    return puntos[-1][1]


def codo_c(curva: str) -> float:
    '''Temperatura mas alta publicada todavia a potencia de placa completa.'''
    try:
        puntos = DERATING[curva]
    except KeyError as exc:
        raise ValueError(f'curva de derating desconocida: {curva}') from exc
    return max(t for t, fraccion in puntos if fraccion == 1.0)


# --- rechazo de rizado de la cascada --------------------------------------
PSRR_DB: dict[tuple[str, float], float] = {
    # lm2941-snvs770i-2015-01.pdf, p. 8, Figure 9, VIN=10 V,
    # COUT=22 uF, IO=10 mA, VO=5 V: ~74.5 dB a 1 kHz.
    ('LM2941', 1e3): 74.5,
    # lm2941-snvs770i-2015-01.pdf, p. 8, Figure 9, VIN=10 V,
    # COUT=22 uF, IO=10 mA, VO=5 V: ~74 dB a 10 kHz.
    ('LM2941', 10e3): 74.0,
    # lm2941-snvs770i-2015-01.pdf, p. 8, Figure 9, VIN=10 V,
    # COUT=22 uF, IO=10 mA, VO=5 V: ~69 dB a 65 kHz, entre rejillas.
    ('LM2941', 65e3): 69.0,
    # lm2941-snvs770i-2015-01.pdf, p. 8, Figure 9, VIN=10 V,
    # COUT=22 uF, IO=10 mA, VO=5 V: ~65-66 dB a 100 kHz.
    ('LM2941', 100e3): 65.5,
    # lm2941-snvs770i-2015-01.pdf, p. 8, Figure 9, VIN=10 V,
    # COUT=22 uF, IO=10 mA, VO=5 V: ~70 dB a 1 MHz, ultimo punto.
    ('LM2941', 1e6): 70.0,

    # lm2991-snvs099i-2016-10.pdf, p. 7, Figure 8, C0=47 uF,
    # IO=5 mA, VO=-5 V: ~59 dB a 1 kHz.
    ('LM2991', 1e3): 59.0,
    # lm2991-snvs099i-2016-10.pdf, p. 7, Figure 8, C0=47 uF,
    # IO=5 mA, VO=-5 V: ~40 dB a 10 kHz.
    ('LM2991', 10e3): 40.0,
    # lm2991-snvs099i-2016-10.pdf, p. 7, Figure 8, C0=47 uF,
    # IO=5 mA, VO=-5 V: ~24-25 dB a 65 kHz, entre rejillas.
    ('LM2991', 65e3): 24.5,
    # lm2991-snvs099i-2016-10.pdf, p. 7, Figure 8, C0=47 uF,
    # IO=5 mA, VO=-5 V: ~22 dB a 100 kHz.
    ('LM2991', 100e3): 22.0,
    # lm2991-snvs099i-2016-10.pdf, p. 7, Figure 8, C0=47 uF,
    # IO=5 mA, VO=-5 V: ~20 dB a 1 MHz, ultimo punto.
    ('LM2991', 1e6): 20.0,

    # lt3045-rev-d.pdf, p. 10, G43, traza roja IL=500 mA, VIN=5 V,
    # RSET=30.1k, COUT=10 uF, CSET=0.47 uF: ~109 dB a 1 kHz.
    ('LT3045', 1e3): 109.0,
    # lt3045-rev-d.pdf, p. 10, G43, traza roja IL=500 mA, VIN=5 V,
    # RSET=30.1k, COUT=10 uF, CSET=0.47 uF: ~91 dB a 10 kHz.
    ('LT3045', 10e3): 91.0,
    # lt3045-rev-d.pdf, p. 10, G43, traza roja IL=500 mA, VIN=5 V,
    # RSET=30.1k, COUT=10 uF, CSET=0.47 uF: ~79.5 dB a 65 kHz.
    ('LT3045', 65e3): 79.5,
    # lt3045-rev-d.pdf, p. 10, G43, traza roja IL=500 mA, VIN=5 V,
    # RSET=30.1k, COUT=10 uF, CSET=0.47 uF: ~77.5 dB a 100 kHz.
    ('LT3045', 100e3): 77.5,
    # lt3045-rev-d.pdf, p. 10, G43, traza roja IL=500 mA, VIN=5 V,
    # RSET=30.1k, COUT=10 uF, CSET=0.47 uF: ~76 dB a 1 MHz.
    ('LT3045', 1e6): 76.0,
    # lt3045-rev-d.pdf, p. 10, G43, traza roja IL=500 mA, VIN=5 V,
    # RSET=30.1k, COUT=10 uF, CSET=0.47 uF: ~88 dB cerca de 2 MHz.
    ('LT3045', 2e6): 88.0,
    # lt3045-rev-d.pdf, p. 10, G43, traza roja IL=500 mA, VIN=5 V,
    # RSET=30.1k, COUT=10 uF, CSET=0.47 uF: ~54 dB a 10 MHz.
    ('LT3045', 10e6): 54.0,

    # lt3094-rev-b.pdf, p. 11, G43, traza roja IL=-500 mA, CSET=4.7 uF,
    # VIN=-5 V, RSET=33.2k, COUT=10 uF: ~107 dB a 1 kHz.
    ('LT3094', 1e3): 107.0,
    # lt3094-rev-b.pdf, p. 11, G43, traza roja IL=-500 mA, CSET=4.7 uF,
    # VIN=-5 V, RSET=33.2k, COUT=10 uF: ~94 dB a 10 kHz.
    ('LT3094', 10e3): 94.0,
    # lt3094-rev-b.pdf, p. 11, G43, traza roja IL=-500 mA, CSET=4.7 uF,
    # VIN=-5 V, RSET=33.2k, COUT=10 uF: ~78 dB a 65 kHz.
    ('LT3094', 65e3): 78.0,
    # lt3094-rev-b.pdf, p. 11, G43, traza roja IL=-500 mA, CSET=4.7 uF,
    # VIN=-5 V, RSET=33.2k, COUT=10 uF: ~75 dB a 100 kHz.
    ('LT3094', 100e3): 75.0,
    # lt3094-rev-b.pdf, p. 11, G43, traza roja IL=-500 mA, CSET=4.7 uF,
    # VIN=-5 V, RSET=33.2k, COUT=10 uF: ~72 dB a 1 MHz.
    ('LT3094', 1e6): 72.0,
    # lt3094-rev-b.pdf, p. 11, G43, traza roja IL=-500 mA, CSET=4.7 uF,
    # VIN=-5 V, RSET=33.2k, COUT=10 uF: ~81 dB cerca de 2 MHz.
    ('LT3094', 2e6): 81.0,
    # lt3094-rev-b.pdf, p. 11, G43, traza roja IL=-500 mA, CSET=4.7 uF,
    # VIN=-5 V, RSET=33.2k, COUT=10 uF: ~27 dB a 10 MHz.
    ('LT3094', 10e6): 27.0,
}


# Citas completas de las siete series anteriores. La fecha es la lectura de
# las paginas adjuntas, no la fecha editorial de la hoja.
FUENTE: dict[str, str] = {
    'IRM-20': (
        'meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve OTHERS, '
        '230 Vac; lectura ocular 2026-09-03'
    ),
    'IRM-20/5V': (
        'meanwell-irm-20-spec-2025-11-21.pdf, p. 3, Derating Curve '
        '3.3V,5V, 230 Vac; lectura ocular 2026-09-03'
    ),
    'IRM-45': (
        'meanwell-irm-45-spec-2025-11-21.pdf, p. 3, Derating Curve unica, '
        '230 Vac; lectura ocular 2026-09-03'
    ),
    'LM2941': (
        'lm2941-snvs770i-2015-01.pdf, p. 8, Figure 9 Ripple Rejection, '
        'IO = 10 mA, VO = 5 V; lectura ocular 2026-09-03'
    ),
    'LM2991': (
        'lm2991-snvs099i-2016-10.pdf, p. 7, Figure 8 Ripple Rejection, '
        'IO = 5 mA, VO = -5 V; lectura ocular 2026-09-03'
    ),
    'LT3045': (
        'lt3045-rev-d.pdf, p. 10, G43 Power Supply Ripple Rejection, '
        'IL = 500 mA, COUT = 10 uF, CSET = 0.47 uF; lectura ocular 2026-09-03'
    ),
    'LT3094': (
        'lt3094-rev-b.pdf, p. 11, G43 Power Supply Ripple Rejection, '
        'IL = -500 mA, COUT = 10 uF, CSET = 4.7 uF; lectura ocular 2026-09-03'
    ),
}


def psrr_db(pieza: str, f_hz: float) -> float:
    '''Interpola PSRR en log(f); fuera de la figura no fabrica una cifra.'''
    puntos = sorted((f, db) for (p, f), db in PSRR_DB.items() if p == pieza)
    if not puntos:
        raise ValueError(f'pieza sin curva de PSRR leida: {pieza}')
    if f_hz < puntos[0][0] or f_hz > puntos[-1][0]:
        raise ValueError(
            f'{pieza}: {f_hz:.3g} Hz fuera de la grafica leida '
            f'({puntos[0][0]:.3g}-{puntos[-1][0]:.3g} Hz)'
        )
    for (f0, d0), (f1, d1) in zip(puntos, puntos[1:]):
        if f0 <= f_hz <= f1:
            k = ((math.log10(f_hz) - math.log10(f0)) /
                 (math.log10(f1) - math.log10(f0)))
            return d0 + k * (d1 - d0)
    return puntos[-1][1]


def demo() -> None:
    '''Imprime las lecturas y corre el contrato del modulo.'''
    print('Curvas leidas para la fuente v4\n')
    print('Derating a 230 Vac:')
    for curva, puntos in DERATING.items():
        texto = ', '.join(f'{t:g} C:{fraccion:.0%}' for t, fraccion in puntos)
        print(f'  {curva:10s} codo {codo_c(curva):g} C; {texto}')

    print('\nPSRR tipico leido:')
    for pieza in ('LM2941', 'LM2991', 'LT3045', 'LT3094'):
        puntos = sorted((f, db) for (p, f), db in PSRR_DB.items() if p == pieza)
        texto = ', '.join(f'{f/1e3:g} kHz:{db:g} dB' for f, db in puntos)
        print(f'  {pieza:7s} {texto}')

    print('\nDudas de lectura:')
    print('  IRM-45 a 80 C: ~33 %, entre las rejillas de 25 y 50 %.')
    print('  Los PSRR a 65 kHz caen entre marcas del eje logaritmico.')
    print('  LT3045 G43 y LT3094 G43: pico estrecho ~2 MHz; frecuencia')
    print('  y altura son lecturas visuales aproximadas del trazo grueso.')

    # test_curvas importa curvas con su nombre de modulo y prueba esa copia.
    # Eso evita duplicar aqui el contrato que manda sobre estas lecturas.
    directorio = os.path.dirname(os.path.abspath(__file__))
    if directorio not in sys.path:
        sys.path.insert(0, directorio)
    import test_curvas  # noqa: E402, PLC0415

    for nombre, fn in sorted(vars(test_curvas).items()):
        if nombre.startswith('test_') and callable(fn):
            fn()
    print('\nOK: curvas.py y test_curvas.py')


if __name__ == '__main__':
    demo()
