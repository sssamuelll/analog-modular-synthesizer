# Hardware — Módulo 7: VCA

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
