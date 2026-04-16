# Arquitectura del SAM17

Este documento describe el sistema completo a nivel de bloques, las
interfaces entre módulos y las convenciones eléctricas que comparten.

## Diagrama de bloques

```
                  ┌──────────────────────┐
       USB ─────▶ │   MIDI/CV (digital)  │
                  │   Raspberry Pi 3B+   │
                  │   + AD5686R DAC      │
                  └──┬───┬───┬────────┬──┘
              CV1 ──┘   │   │        │ GATE
              CV2 ──────┘   │        │
              CV3 ──────────┘        │
                                     ▼
   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
   │  VCO1  │   │  VCO2  │   │  VCO3  │   │  ADSR  │
   │CEM3340 │   │CEM3340 │   │CEM3340 │   │ICM7555 │
   └───┬────┘   └───┬────┘   └───┬────┘   └───┬────┘
       │            │            │            │
       ▼            ▼            ▼            │
       └─────► MIXER (TL074) ◄───┘            │
                    │                         │
                    ▼                         │
               VCF (LM13700 OTA, MS-20)       │
                    │                         │
                    ▼                         │
                  VCA (LM13700) ◄─────────────┘ (env)
                    │
                    ▼
                AUDIO OUT (1/8" mono)


   ┌──────────────────────────────────────────┐
   │  Alimentación: 110 VAC → +5V / +12V / -12V│
   └──────────────────────────────────────────┘
                  bus de alimentación común
```

(Reproduce el Gráfico 12 de la tesis. Versión vectorial: ver
`docs/images/architecture.svg` *— pendiente*.)

## Convenciones eléctricas

| Señal | Rango | Notas |
|-------|-------|-------|
| `+5V`  | 5 V regulada | Para Raspberry Pi y lógica digital |
| `+12V` | 12 V regulada | Op-amps, OTAs, CEM3340 |
| `-12V` | −12 V regulada | Op-amps, OTAs |
| `GND`  | Referencia común | Tierra analógica y digital unidas en un solo punto del módulo de alimentación |
| `CV_NOTE` | 0 – ~10 V | 1 V/octava; 84 notas (C1 – C8) |
| `GATE` | 0 / 10 V | Activo en alto mientras se sostiene una tecla MIDI |
| `ENV_OUT` | 0 – ~10 V | Salida del ADSR |
| `AUDIO` | ±5 V (10 Vpp) | Entre módulos analógicos |

> El estándar **1 V/oct** es el corazón de la interoperabilidad: un voltio en
> la entrada CV de un VCO sube su frecuencia exactamente una octava.

## Bus de alimentación

Cada módulo recibe alimentación a través del bus interno del cajón. Conectores
sugeridos: pin header de 6 vías (2×3) con el siguiente pinout, replicando la
convención de Eurorack para facilitar futura compatibilidad:

```
-12V  -12V
 GND   GND
+12V  +12V
```

> El proyecto original usa pin headers genéricos. La transición a un conector
> tipo Eurorack (IDC 16) es una de las mejoras propuestas.

## Bus de señal (paneles frontales)

Todas las interconexiones de panel son **jacks mono 3.5 mm** (TS). Los cables
de paciente deben ser blindados de baja capacitancia. La impedancia de salida
típica de cada módulo es de 1 kΩ; la de entrada, ≥ 100 kΩ.

## Numeración de módulos

Los módulos se numeran por su orden lógico en la cadena de síntesis (no por
posición física en el panel):

1. Alimentación
2. MIDI/CV
3. VCO
4. Mixer
5. VCF
6. ADSR
7. VCA

Los directorios de `hardware/` siguen esta numeración.

## Diferencias respecto a la tesis

Esta sección listará, a medida que el proyecto evolucione, las desviaciones
intencionales del diseño de 2020 (sustitución de componentes obsoletos,
módulos nuevos, mejoras de PCB, etc.). Por ahora, ninguna.
