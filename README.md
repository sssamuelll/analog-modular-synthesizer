# SAM17 — Sintetizador Analógico Modular

Reproducción y evolución de código abierto del **Sintetizador Analógico Modular
SAM17**, presentado como Trabajo de Grado por *Samuel Ballesteros García* en la
Universidad Yacambú (Barquisimeto, 2020). La tesis original se conserva en
[`docs/thesis.pdf`](docs/thesis.pdf).

El objetivo de este repositorio es construir, a partir de la tesis, un
**esqueleto de proyecto vivo**: un lugar donde las ideas originales puedan
reproducirse fielmente, documentarse con detalle y, sobre todo, mejorarse con
aportes de la comunidad.

## Filosofía del proyecto

- **Modularidad**: cada uno de los 7 módulos del sintetizador vive en su propio
  directorio dentro de `hardware/`, con su propio README, BOM y esquemáticos.
- **Hardware y software por separado**: la electrónica analógica está en
  `hardware/`, las simulaciones SPICE en `simulations/`, y el firmware del
  conversor MIDI/CV (único módulo digital) en `software/midi-cv/`.
- **Reproducible**: todo lo necesario para construir el instrumento (BOM,
  planos, código, manual) está versionado.
- **Mejorable**: cada módulo lista explícitamente las mejoras propuestas sobre
  el diseño original (ver la sección *Mejoras propuestas* de cada README).

## Módulos del sintetizador

| # | Módulo | Tipo | Tecnología clave | Directorio |
|---|--------|------|-----------------|-----------|
| 1 | Alimentación | Analógico | 7805, 7812, 7912 | [`hardware/01-power-supply`](hardware/01-power-supply) |
| 2 | MIDI/CV | Digital | Raspberry Pi 3B+ + AD5686R | [`hardware/02-midi-cv`](hardware/02-midi-cv) + [`software/midi-cv`](software/midi-cv) |
| 3 | VCO (×3) | Analógico | CEM3340 | [`hardware/03-vco`](hardware/03-vco) |
| 4 | Mixer | Analógico | TL074 | [`hardware/04-mixer`](hardware/04-mixer) |
| 5 | VCF | Analógico | LM13700 (OTA tipo MS-20) | [`hardware/05-vcf`](hardware/05-vcf) |
| 6 | ADSR | Analógico | ICM7555 | [`hardware/06-adsr`](hardware/06-adsr) |
| 7 | VCA | Analógico | LM13700 / CA3080 | [`hardware/07-vca`](hardware/07-vca) |
| — | Cajón y paneles | Mecánico | Madera + lámina galv. | [`case/`](case) |

Arquitectura global y diagrama de bloques: [`docs/architecture.md`](docs/architecture.md).

## Especificaciones generales

- **Polifonía**: monofónica
- **Fuentes de sonido**: 3 VCOs (sierra, triangular, cuadrada con PWM)
- **Filtro**: VCF pasa-bajo con resonancia auto-oscilante (24 dB/oct)
- **Envolvente**: ADSR (2 generadores en el diseño final)
- **Entrada MIDI**: USB (controladores MIDI clase USB)
- **Salidas**: 3 CV (1 V/octava, 84 notas) + 1 GATE (10 V)
- **Puntos de conexión**: ~40 jacks de 3.5 mm (15 in / 25 out)
- **Dimensiones cajón**: 950 × 440 × 100–200 mm
- **Alimentación**: 110 VAC 60 Hz → 5 V / +12 V / −12 V

## Estructura del repositorio

```
analog-modular-synthesizer/
├── docs/              Tesis original, resumen, referencias, manual de usuario,
│                      arquitectura y documentación detallada por módulo.
├── hardware/          Un subdirectorio por módulo con esquemáticos KiCad, PCB,
│                      BOM y notas de diseño.
├── software/          Firmware Python para el módulo MIDI/CV (Raspberry Pi).
├── simulations/       Simulaciones SPICE / LTspice para validar diseños.
├── case/              Planos mecánicos del cajón y paneles frontales.
└── .github/           CI y plantillas.
```

## Cómo empezar

1. Lee el [resumen de la tesis](docs/summary.md) y la [arquitectura](docs/architecture.md).
2. Elige un módulo: cada `hardware/NN-<módulo>/README.md` explica el objetivo,
   componentes, parámetros de diseño y mejoras pendientes.
3. Para el firmware: `cd software/midi-cv && cat README.md`.
4. Para contribuir: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licencia

Ver [`LICENSE`](LICENSE). La tesis original se incluye con fines documentales.
