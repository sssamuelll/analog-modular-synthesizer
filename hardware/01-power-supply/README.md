# Hardware — Módulo 1: Alimentación

> Documentación funcional: [`docs/modules/01-power-supply.md`](../../docs/modules/01-power-supply.md).

## Resumen

Convierte 12 VAC del transformador externo en **+5 V**, **+12 V** y **−12 V**
regulados que distribuye al resto del sintetizador a través del bus interno.

## Componentes principales

| Función | Componente |
|---------|------------|
| Rectificación | Puente de diodos (4 × 1N4007 o equivalente) |
| Regulador +5 V | LM7805 |
| Regulador +12 V | LM7812 |
| Regulador −12 V | LM7912 |
| Filtrado | Electrolíticos 4700 µF / 25 V + cerámicos 100 nF |

## Estructura del directorio

```
01-power-supply/
├── README.md
├── bom.csv
├── kicad/      (pendiente — proyecto KiCad por capturar)
├── schematics/ (pendiente — exportados PDF)
├── pcb/        (pendiente — renderizados)
└── notes/      (pendiente — mediciones de tensión y rizado)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Verificación de tensiones bajo carga
- [ ] Medición de rizado en cada riel
- [ ] Cálculo de disipación térmica de los reguladores

## Mejoras propuestas

Ver la sección *Mejoras propuestas* en
[`docs/modules/01-power-supply.md`](../../docs/modules/01-power-supply.md).
