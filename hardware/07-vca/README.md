# Hardware — Módulo 7: VCA

> [!IMPORTANT]
> **El SAM17 pasa a polifónico de 4 voces.** Cuatro VCA, cada uno con la
> envolvente de su voz y su propia velocity.
>
> Arquitectura completa: [`docs/architecture-poly.md`](../../docs/architecture-poly.md)


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
