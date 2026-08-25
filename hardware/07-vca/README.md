# Hardware — Módulo 7: VCA

> [!IMPORTANT]
> ## Este módulo DESAPARECE como placa separada — 2026-08-23
>
> Hay **dos VCA por canal** —uno de voz y uno de resonancia— dentro de la placa del módulo de Voz. Son 32 en total.
>
> Y cambia la pieza: ya no es LM13700 sin diodos de linealización, sino **¼ de SSI2164** por VCA, o sea 8 encapsulados. El «soft drive» que esta página describe era carácter del LM13700; el carácter del instrumento ahora lo pone el filtro.
>
> Lo de abajo queda como **diseño de referencia del circuito**: sigue siendo de
> donde sale el carácter, y el spec de Voz lo hereda. Lo que ya no vale es que
> esto sea una placa con su panel y su bajada de bus.
>
> Manda: [spec del módulo de Voz total, §2](../../docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md).


> Documentación funcional: [`docs/modules/07-vca.md`](../../docs/modules/07-vca.md).

## Resumen

Etapa final del sintetizador. VCA basado en **LM13700** sin diodos de
linealización (carácter "soft drive"). Incluye atenuador de entrada,
conversor I→V (transimpedancia) y conversor V→I (op-amp + transistor PNP).

## Estructura del directorio

```
07-vca/
├── README.md
├── bom.csv
├── kicad/      (pendiente)
├── schematics/ (pendiente)
├── pcb/        (pendiente)
└── notes/      (pendiente — caracterización THD y feed-through del CV)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Medición de THD vs nivel de entrada
- [ ] Verificar feed-through del CV en silencio
- [ ] Evaluar variante con diodos de linealización conmutables
