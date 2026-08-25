# Hardware — Módulo 6: ADSR

> [!IMPORTANT]
> ## Este módulo DESAPARECE como placa separada — 2026-08-23
>
> Las envolventes dejan de ser un circuito. Son **generadores que corren en los micros del módulo de Voz**, con sus perillas en el panel de mandos de la fila B.
>
> No queda ICM7555, ni capacitor de rampa, ni placa. Lo que se pierde con el circuito son sus failsafes — un ADSR analógico se cae a cero solo — y por eso el spec les pone watchdogs explícitos en firmware.
>
> Lo de abajo queda como **diseño de referencia del circuito**: sigue siendo de
> donde sale el carácter, y el spec de Voz lo hereda. Lo que ya no vale es que
> esto sea una placa con su panel y su bajada de bus.
>
> Manda: [spec del módulo de Voz total, §3.1](../../docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md).


> Documentación funcional: [`docs/modules/06-adsr.md`](../../docs/modules/06-adsr.md).

## Resumen

Generador de envolvente ADSR con núcleo **ICM7555** (variante CMOS del 555)
en configuración monoestable y un capacitor cuya carga/descarga se rutea
por cuatro caminos diferentes según la etapa.

## Estructura del directorio

```
06-adsr/
├── README.md
├── bom.csv
├── kicad/      (pendiente)
├── schematics/ (pendiente)
├── pcb/        (pendiente)
└── notes/      (pendiente — capturas de la envolvente en osciloscopio)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Capturas de envolvente para distintos valores A/D/S/R
- [ ] Medición de tiempos mínimos y máximos por etapa
- [ ] Evaluar duplicar el módulo (la spec final pide 2 envolventes)
