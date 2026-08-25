# Hardware — Módulo 4: Mixer

> [!IMPORTANT]
> ## Este módulo DESAPARECE como placa separada — 2026-08-23
>
> La suma de los dieciséis canales, el volumen general, la salida principal **y los oídos** (el códec de 24 bits con el que el instrumento se escucha a sí mismo) se mudan a la placa del módulo de Voz.
>
> El motivo, dicho por Samuel: *un mixer solo tiene sentido si es independiente de su fuente y de sus salidas.* El de aquí estaba soldado a las voces, así que no era un módulo — era una parte. El mixer que viva en la fila de abajo es un invitado Eurorack cualquiera y no tiene relación con esta suma.
>
> Lo de abajo queda como **diseño de referencia del circuito**: sigue siendo de
> donde sale el carácter, y el spec de Voz lo hereda. Lo que ya no vale es que
> esto sea una placa con su panel y su bajada de bus.
>
> Manda: [spec del módulo de Voz total, §13, acta E-5](../../docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md).


> Documentación funcional: [`docs/modules/04-mixer.md`](../../docs/modules/04-mixer.md).

## Resumen

Sumador inversor de 3 canales (TL074) con control de nivel por canal, salida
acoplada en DC (permite sumar CV además de audio).

## Estructura del directorio

```
04-mixer/
├── README.md
├── bom.csv
├── kicad/      (pendiente)
├── schematics/ (pendiente)
├── pcb/        (pendiente)
└── notes/      (pendiente — pruebas de crosstalk y ruido)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Medición de SNR
- [ ] Evaluar variante AC-coupled seleccionable
