# Hardware — Módulo 5: VCF (filtro pasa-bajo OTA)

> [!IMPORTANT]
> ## Este módulo DESAPARECE como placa separada — 2026-08-23
>
> Hay **un filtro por canal, dentro de la placa del módulo de Voz**: dieciséis, no cuatro, y no en placa propia.
>
> Sigue siendo el MS-20 (LM13700 en dos celdas, LP 24 dB/oct, LEDs en el lazo), elegido por carácter. Dos cosas cambian: la **resonancia se controla por VCA** (¼ de SSI2164 en el lazo), nunca por digipot; y el problema de apareamiento que esta página daba por incalibrable **sí se calibra** — un tap de caracterización lleva la señal post-filtro de cada canal a un mux 16:1 y a un contador del micro, que es la ruta por la que la auto-oscilación se mide con el VCA de voz cerrado.
>
> Lo de abajo queda como **diseño de referencia del circuito**: sigue siendo de
> donde sale el carácter, y el spec de Voz lo hereda. Lo que ya no vale es que
> esto sea una placa con su panel y su bajada de bus.
>
> Manda: [spec del módulo de Voz total, §2 y §4](../../docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md).


> Documentación funcional: [`docs/modules/05-vcf.md`](../../docs/modules/05-vcf.md).

## Resumen

Filtro pasa-bajo 24 dB/oct con resonancia auto-oscilante, basado en el
diseño OTA del Korg MS-20 (LM13700 + TL074). Incluye LEDs en el lazo de
resonancia para añadir saturación armónica controlada.

## Estructura del directorio

```
05-vcf/
├── README.md
├── bom.csv
├── kicad/      (pendiente)
├── schematics/ (pendiente)
├── pcb/        (pendiente)
└── notes/      (pendiente — barridos de respuesta en frecuencia)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Medición de respuesta en frecuencia (Bode)
- [ ] Verificación de tracking 1 V/oct en CV-IN
- [ ] Caracterización de la auto-oscilación
- [ ] Documentar offset/simetría del LM13700
