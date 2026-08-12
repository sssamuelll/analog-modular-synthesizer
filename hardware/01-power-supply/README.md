# Hardware — Módulo 1: Alimentación

> Documentación funcional: [`docs/modules/01-power-supply.md`](../../docs/modules/01-power-supply.md).

## Resumen

Convierte 12 VAC del transformador externo en **+5 V**, **+12 V** y **−12 V**
regulados que distribuye al resto del sintetizador a través del bus interno.

> **Variante Europa (230 VAC / 50 Hz).** La tesis original (§1 de
> [`notes/design-notes.md`](notes/design-notes.md)) asume la red eléctrica de
> Venezuela (110 VAC / 60 Hz); esta build cambia el objetivo a mains europeo
> — ver [`notes/design-notes.md` §12](notes/design-notes.md#12-variante-europa-230-vac--50-hz)
> para qué cambió (MOV, fusible, transformador) y qué se mantuvo igual (NTC,
> verificado contra datasheet).

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
├── kicad/
│   ├── build_schematic.py   Genera sam17-power.kicad_sch (ver hardware/tools/README.md)
│   └── sam17-power.kicad_sch
├── schematics/
│   └── sam17-power.{svg,pdf}
├── pcb/        (pendiente — renderizados)
└── notes/
    └── design-notes.md   Presupuesto de corriente, topología, cálculo
                          térmico y checklist de bring-up.
```

## Estado

- [x] Nota de diseño con presupuesto de corriente y cálculo térmico ([`notes/design-notes.md`](notes/design-notes.md))
- [x] Decisiones arquitectónicas resueltas (+5 V incluido, NTC soft-start, MOV en primario)
- [x] Esquemático en KiCad — rieles **±12 V y +5 V aux** (rectificación,
      7812/7912/7805, protecciones DC, indicadores) **y** lado primario
      **230 V/50 Hz** (fusible 250 mA + MOV S20K275 + NTC de soft-start,
      [`notes/design-notes.md`](notes/design-notes.md) §10/§12). ERC limpio,
      netlist verificado. Dos huecos reales encontrados al cruzar contra
      `bom.csv` (no resueltos, ver abajo).
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
- **Protección AC** (variante Europa): fusible **250 mA** lento + **MOV
  S20K275** (275 VAC, sobretensión transitoria de red) + **NTC SL10-5R020**
  (limitador de inrush al arranque, mismo componente que la variante
  110 V — rated 265 VAC, sirve igual). Valores originales de 110 V
  (500 mA / V150LA20A) documentados en design-notes.md §10 como referencia
  histórica.
- **Protección DC**: diodos anti-backfeed (1N4001) en salida de cada
  regulador + LEDs indicadores por riel.
- **Distribución**: bus board PCB (no daisy-chain) con tierra en estrella
  desde los condensadores bulk.

## Discrepancias esquemático ↔ BOM sin resolver

Encontradas al cruzar `sam17-power.kicad_sch` contra `bom.csv`, ninguna
corregida a criterio propio porque las dos tocan la entrada de red:

- **Falta tierra de seguridad**: `bom.csv` pide `J_AC_IN` como *"Barrier
  block 3 pos... con tierra de seguridad"*, pero el esquemático dibuja `J3`
  con solo 2 pines (L/N), sin PE. `design-notes.md` §7 tampoco cierra cómo
  debe conectarse el chasis ("con cuidado ante ground loops") — hace falta
  decidir el esquema de puesta a tierra antes de dibujar el tercer pin, no
  solo agregarlo. Con la variante Europa esto pesa más: equipo Clase I con
  marcado CE normalmente exige PE por norma.
- **Conector de entrada del transformador no coincide**: `bom.csv` especifica
  `J_IN` como *"Barrier block 2 pos"*, pero el esquemático usa `J1` de 3
  pines (dos AC + toma central a GND). Uno de los dos está desactualizado —
  no está claro cuál.

## Mejoras propuestas

Ver la sección *Mejoras propuestas* en
[`docs/modules/01-power-supply.md`](../../docs/modules/01-power-supply.md).
