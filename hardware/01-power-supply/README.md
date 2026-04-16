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
└── notes/
    └── design-notes.md   Presupuesto de corriente, topología, cálculo
                          térmico y checklist de bring-up.
```

## Estado

- [x] Nota de diseño con presupuesto de corriente y cálculo térmico ([`notes/design-notes.md`](notes/design-notes.md))
- [ ] Resolver preguntas abiertas (§10 de la nota de diseño)
- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Verificación de tensiones bajo carga
- [ ] Medición de rizado en cada riel
- [ ] Procedimiento de bring-up documentado

## Decisiones clave (ver [`notes/design-notes.md`](notes/design-notes.md))

- **Arquitectura**: *Opción A* — transformador 12 VAC/2 A para los rieles
  analógicos ±12 V + adaptador USB 5 V independiente para el Raspberry Pi
  (evita contaminación del plano analógico con el ruido del Pi).
- **Reguladores**: LM7812 + LM7912 en TO-220 con disipador estándar
  (T<sub>junction</sub> ≈ 60 °C a 300 mA).
- **Protección**: fusible 500 mA lento en primario + diodos anti-backfeed +
  LEDs indicadores por riel.
- **Distribución**: bus board PCB (no daisy-chain) con tierra en estrella
  desde los condensadores bulk.

## Mejoras propuestas

Ver la sección *Mejoras propuestas* en
[`docs/modules/01-power-supply.md`](../../docs/modules/01-power-supply.md).
