# Hardware — Módulo 3: VCO (×3)

> [!IMPORTANT]
> **El SAM17 pasa a polifónico de 4 voces.** Este módulo deja de ser tres
> osciladores independientes y pasa a ser **4 canales idénticos con un solo juego
> de mandos** — el panel no crece con las voces, la PCB sí.
>
> Y necesita algo que la tesis no tiene: una **salida `TUNE_OUT` dedicada por
> oscilador** hacia el multiplexor de escucha del módulo 2. Sin ella el autoafinado
> exige patchear cables a mano y deja de ser automático.
>
> Arquitectura completa: [`docs/architecture-poly.md`](../../docs/architecture-poly.md)


> Documentación funcional: [`docs/modules/03-vco.md`](../../docs/modules/03-vco.md).

## Resumen

Tres osciladores **CEM3340** idénticos, cada uno generando simultáneamente
sierra, triangular y cuadrada con PWM. Estándar 1 V/octava.

## Componentes principales

| Función | Componente |
|---------|------------|
| Núcleo VCO | CEM3340 (×3) |
| Buffer de salidas | TL074 |
| PWM y CV-IN | resistencias 1 % película metálica |

## Estructura del directorio

```
03-vco/
├── README.md
├── bom.csv
├── kicad/      (pendiente)
├── schematics/ (pendiente)
├── pcb/        (pendiente)
└── notes/      (pendiente — procedimiento de calibración 1V/oct)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Calibración 1 V/oct sobre 7 octavas (objetivo: < ±1 % por VCO)
- [ ] Procedimiento de afinación documentado
- [ ] Ecualizar amplitudes de las tres formas de onda
