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

- **Modularidad, en dos regímenes**: por dentro del instrumento es
  programática — la matriz de modulación, los roles y el crosspoint **son** el
  patch, y un preset es un patch completo. En la frontera es física: cable y
  jack. *Por dentro el patch es un preset; por fuera es un cable.*
- **Un directorio por módulo** dentro de `hardware/`, con su README, BOM y
  esquemáticos. La numeración de siete viene de la tesis y se conserva aunque el
  diseño vigente ya no tenga siete placas.
- **Hardware y software por separado**: la electrónica analógica está en
  `hardware/`, las simulaciones SPICE en `simulations/`, y el firmware en
  `software/nucleo/` (Rust, STM32N657). `software/midi-cv/` es el firmware Python
  de la v1 de Raspberry Pi, superada.
- **Reproducible**: todo lo necesario para construir el instrumento (BOM,
  planos, código, manual) está versionado.
- **Mejorable**: cada módulo lista explícitamente las mejoras propuestas sobre
  el diseño original (ver la sección *Mejoras propuestas* de cada README).

## Módulos del sintetizador

La numeración de siete módulos viene de la tesis y se conserva como índice.
**El diseño vigente ya no son siete placas**: el módulo de Voz absorbió cuatro
de ellas, por la razón de la §1 del
[spec de Voz total](docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md)
— un canal es oscilador → filtro → VCA soldado de punta a punta, y partirlo en
tres placas era cablear dieciséis veces lo que cabe en una pista.

| # | Módulo | Estado en el diseño vigente | Tecnología clave | Directorio |
|---|--------|------|-----------------|-----------|
| 1 | Alimentación | **Vigente**; la v1 queda como diseño cerrado que no se construye | LM7805 en +5 V, parejas LT3045/LT3094 en ±12 V | [`hardware/01-power-supply`](hardware/01-power-supply) |
| 2 | Cerebro | **Vigente**; la v1 de Raspberry Pi está superada por la v2 sobre STM32N657 | STM32N657 (Rust bare-metal) | [`hardware/02-midi-cv`](hardware/02-midi-cv) + [`software/nucleo`](software/nucleo) |
| 3 | **Voz** (era «VCO») | **Vigente, y creció**: 16 canales completos + la bahía asignable | 16× SSI2130, 16× LM13700, 8× SSI2164, 1× STM32N657, 2× AD75019 | [`hardware/03-vco`](hardware/03-vco) |
| 4 | Mixer | **Desaparece como placa**: suma, volumen, salida y los oídos se mudan al módulo de Voz | — | [`hardware/04-mixer`](hardware/04-mixer) |
| 5 | VCF | **Desaparece como placa**: un filtro por canal, dentro del módulo de Voz | LM13700 (OTA tipo MS-20) | [`hardware/05-vcf`](hardware/05-vcf) |
| 6 | ADSR | **Desaparece como circuito**: las envolventes son generadores en los micros del módulo de Voz | firmware | [`hardware/06-adsr`](hardware/06-adsr) |
| 7 | VCA | **Desaparece como placa**: dos VCA por canal (voz y resonancia), dentro del módulo de Voz | SSI2164 | [`hardware/07-vca`](hardware/07-vca) |
| — | Bus board | Vigente | plano de masa sólido, 6 slots por segmento | [`hardware/bus-board`](hardware/bus-board) |
| — | Cajón y paneles | Vigente | Acrílico naranja, Eurorack 3U en las dos filas | [`case/`](case) |

Arquitectura global y diagrama de bloques: [`docs/architecture.md`](docs/architecture.md).

## Especificaciones generales

- **Canales**: **16 canales analógicos completos**, cada uno oscilador → filtro
  → VCA, soldados de punta a punta en la misma placa. El módulo suelda canales;
  **el preset reparte los roles**.
- **Polifonía**: 16 voces limpias, u **8 voces de FM** (2 osciladores por voz:
  portadora + moduladora), o cualquier mezcla. Lo decide el preset, no el cobre.
  La tesis original era monofónica.
- **Por qué dieciséis y no ocho**: en FM cada voz necesita dos osciladores,
  porque la moduladora tiene que seguir a su portadora en frecuencia. Una
  moduladora compartida entre ocho notas distintas no da FM tonal, da campanas
  disonantes.
- **Osciladores**: SSI2130 (sierra, triangular, cuadrada/pulso, seno por el
  shaper del chip), con matriz de modulación FM de 16 líneas — cualquiera de los
  dieciséis puede modular a cualquiera, y por eso van en **un solo módulo**: en
  dos, la matriz se parte por la mitad.
- **Filtro**: uno por canal. Pasa-bajo 24 dB/oct tipo MS-20 (LM13700 + TL074)
  con LEDs en el lazo. **Resonancia controlada por VCA**, nunca digipot.
- **VCA**: dos por canal (voz y resonancia) — 32 en total, sobre 8× SSI2164.
- **Envolventes**: ya no son un circuito. Son **generadores que corren en los
  micros del módulo de Voz**, con sus perillas en el panel de mandos.
- **Bahía asignable**: 8 entradas + 8 salidas en jacks Thonkiconn con sensado de
  ocupación y LED por jack, ruteadas por dos AD75019 (crosspoint 16×16). Por
  dentro el patch es un preset; por fuera es un cable.
- **Entrada MIDI**: USB y DIN. Los conectores del mundo van **a la trasera** del
  cajón, no al frente.
- **Salida**: **estéreo**, con sitio por voz en el campo.
- **Formato**: Eurorack 3U en las dos filas. Arriba el instrumento; abajo, rack
  de verdad para módulos invitados intercambiables.
- **Dimensiones del cajón**: las manda [`case/clearance_budget.py`](case/clearance_budget.py);
  la cifra vigente vive en [`case/README.md`](case/README.md) y no se copia aquí
  para que no envejezca.
- **Alimentación**: 230 VAC 50 Hz (variante Europa; tesis original: 110 VAC
  60 Hz Venezuela, ver [`hardware/01-power-supply`](hardware/01-power-supply))
  → +5 V / +12 V / −12 V. El envelope es de 650 mA por riel.

## Estructura del repositorio

```
analog-modular-synthesizer/
├── docs/              Tesis original, resumen, referencias, manual de usuario,
│                      arquitectura y documentación detallada por módulo.
├── hardware/          Un subdirectorio por módulo con esquemáticos KiCad, PCB,
│                      BOM y notas de diseño.
├── software/          nucleo/  — contrato y firmware en Rust para STM32N657.
│                      midi-cv/ — firmware Python de la v1 (superada).
├── simulations/       Simulaciones SPICE / LTspice para validar diseños.
├── case/              Planos mecánicos del cajón y paneles frontales.
└── .github/           CI y plantillas.
```

## Cómo empezar

1. Lee el [resumen de la tesis](docs/summary.md) para saber de dónde sale esto.
2. **El diseño vigente vive en las specs fechadas de
   [`docs/superpowers/specs/`](docs/superpowers/specs), y la más reciente manda.**
   Las dos que gobiernan hoy el instrumento son
   [Voz total](docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md)
   (los 16 canales y la doctrina) y
   [el cerebro v2](docs/superpowers/specs/2026-08-21-modulo-2-v2-cerebro-design.md).
   [`docs/architecture-poly.md`](docs/architecture-poly.md) está pendiente de
   reescritura contra ellas y **lleva aviso**.
3. Elige un módulo: cada `hardware/NN-<módulo>/README.md` explica el objetivo,
   componentes, parámetros de diseño y mejoras pendientes.
4. Para el firmware: `cd software/nucleo && cargo test`.
5. Para contribuir: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licencia

Ver [`LICENSE`](LICENSE). La tesis original se incluye con fines documentales.
