# Hardware — Módulo 5: VCF (filtro pasa-bajo OTA)

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
