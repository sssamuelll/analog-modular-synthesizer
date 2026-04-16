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
- [x] Decisiones arquitectónicas resueltas (+5 V incluido, NTC soft-start, MOV en primario)
- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Verificación de tensiones bajo carga
- [ ] Medición de rizado en cada riel
- [ ] Procedimiento de bring-up documentado

## Decisiones clave (ver [`notes/design-notes.md`](notes/design-notes.md))

- **Arquitectura**: *Opción A* — transformador 12 VAC/2 A para los rieles
  ±12 V **y +5 V** del módulo + adaptador USB 5 V independiente para el
  Raspberry Pi (evita contaminación del plano analógico con el ruido del Pi).
- **Riel +5 V incluido**: alimenta AD5686R (DAC del MIDI/CV) y LCD 16×2.
  ~150 mA con backlight; el Pi sigue alimentado aparte.
- **Reguladores**: LM7805 + LM7812 + LM7912 en TO-220 con disipador
  estándar (Tj < 70 °C en el peor caso).
- **Protección AC**: fusible 500 mA lento + **MOV V150LA20A** (sobretensión
  transitoria de red) + **NTC SL10-5R020** (limitador de inrush al
  arranque).
- **Protección DC**: diodos anti-backfeed (1N4001) en salida de cada
  regulador + LEDs indicadores por riel.
- **Distribución**: bus board PCB (no daisy-chain) con tierra en estrella
  desde los condensadores bulk.

## Mejoras propuestas

Ver la sección *Mejoras propuestas* en
[`docs/modules/01-power-supply.md`](../../docs/modules/01-power-supply.md).
