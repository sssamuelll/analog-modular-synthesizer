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
│   ├── check_bom.py         Cruza bom.csv contra los designadores del esquemático
│   ├── build_pcb.py         Genera sam17-power.kicad_pcb — usa pcbnew DIRECTO,
│   │                        va con el Python de KiCad, no con el del sistema
│   ├── sam17.pretty/        Huellas propias: varistor D20, NTC de disco, faston (§14.3)
│   ├── fp-lib-table         Registra sam17.pretty en el proyecto
│   ├── sam17-power.kicad_sch
│   └── sam17-power.kicad_pcb
├── schematics/
│   └── sam17-power.{svg,pdf}
├── pcb/        sam17-power-{top,bottom}.svg y .pdf
└── notes/
    └── design-notes.md   Presupuesto de corriente, topología, cálculo
                          térmico y checklist de bring-up.
```

## Estado

- [x] Nota de diseño con presupuesto de corriente y cálculo térmico ([`notes/design-notes.md`](notes/design-notes.md))
- [x] Decisiones arquitectónicas resueltas (+5 V incluido, NTC soft-start, MOV en primario)
- [x] Esquemático en KiCad — rieles **±12 V y +5 V aux** (rectificación,
      7812/7912/7805, protecciones DC, indicadores), lado primario
      **230 V/50 Hz** (fusible 250 mA + MOV S20K275 + NTC de soft-start,
      [`notes/design-notes.md`](notes/design-notes.md) §10/§12) y **tierra de
      protección** con puente de chasis en punto único (§13). ERC sin errores
      ni avisos, netlist verificado, y `bom.csv` cuadra con el esquemático
      designador a designador (`python kicad/check_bom.py`).
- [x] **Salida de +5 V** — resuelto en issue #8 (opción C): el riel sale por
      `J6`, un conector de 2 posiciones aparte del bus, con retorno dedicado
      al punto de estrella (ver abajo)
- [x] **Huellas asignadas** — los 33 componentes con footprint, verificado
      contra disco en cada build. Tres huellas propias en `kicad/sam17.pretty`
      porque KiCad no las trae ([§14.3](notes/design-notes.md))
- [x] **Placa colocada** — 100 × 150 mm, dos capas, franja de red aislada por
      ranura fresada. Separación red↔SELV **medida en 12.4 mm** (mínimo 6), DRC
      de KiCad sin infracciones ([§14.4](notes/design-notes.md))
- [x] **PCB ruteada** — dos capas, una sola vía, sin plano de masa: GND es un
      árbol con cero bucles, verificado por union-find, y el retorno del +5 V
      llega a la estrella sin tocar ninguna otra rama
      ([§14.5](notes/design-notes.md)). DRC de KiCad **0 infracciones, 0 pads
      sin conectar**. Renders en [`pcb/`](pcb/)
- [ ] **Antes de fabricar**: verificar el orden de patillas de `BR1` contra el
      datasheet de la pieza comprada ([§14.6](notes/design-notes.md))
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
- **Tierra de protección** ([§13](notes/design-notes.md)): puente **duro** entre
  chasis y GND, en un **punto único** (espárrago M4 dedicado). No se usa red de
  *ground lift* porque los paneles son lámina galvanizada y los ~40 jacks de
  3.5 mm ya unen chasis y GND por el casquillo — una red de lift estaría
  cortocircuitada 40 veces. El PE **no lleva pista en la PCB**: va del bornero
  `J3.3` al espárrago por cable, y el 0 V sube al mismo espárrago por el faston
  `J5`. La corriente de falla nunca pasa por la placa.
- **Interfaz del bus** ([§10.4](notes/design-notes.md), issue #8): `J2` lleva
  solo lo analógico (`+12/GND/GND/−12`, igual para los módulos 2-7) y el +5 V
  sale por `J6`, un conector de 2 posiciones físicamente distinto. Así ningún
  módulo recibe un +5 V que no usa, el feed digital no se puede cruzar con
  ±12, y el retorno del +5 V — que §10.1 exige dedicado hasta el punto de
  estrella porque el backlight del LCD va conmutado — queda separado por
  construcción, no por convención de layout.
- **Distribución**: bus board PCB (no daisy-chain) con tierra en estrella
  desde los condensadores bulk.

## Cruce esquemático ↔ BOM

`bom.csv` lleva ahora una columna `refs` con los designadores reales del
esquemático, y `kicad/check_bom.py` verifica el cruce en los dos sentidos. Hoy
cuadra: 32 componentes en la hoja, ninguno sin línea de compra, ninguna línea
apuntando a un designador que no existe.

Resuelto en esa pasada, además de los dos huecos que la motivaron:

- **`J1` de 3 posiciones, no 2.** El secundario es de toma central: son tres
  hilos (12 VAC / CT / 12 VAC). El esquemático tenía razón y el BOM estaba
  viejo.
- **`R3` es de 680 Ω, no de 2.2 kΩ.** El BOM pedía tres resistencias iguales
  para los tres LED. A 5 V, 2.2 kΩ dan ~1.3 mA y el indicador de +5 V queda
  apagado; 680 Ω dan los mismos ~4.5 mA que los otros dos rieles.
- **Designadores alineados.** El BOM llamaba `MOV1`/`NTC1` a lo que la hoja
  llama `RV1`/`NT1`, y sus `C3`/`C4`/`C5` eran condensadores distintos de los
  `C3`/`C4`/`C5` del esquemático. Eso hacía el cruce imposible de automatizar.
- **Faltaban `J4` y `J5`** en la lista de compra.

## Resuelto: la salida de +5 V y la interfaz del bus (issue #8)

El riel de +5 V no salía de la placa (netlist sin ningún pin de `J2` en la red
`+5V`), y arreglarlo era fijar la **interfaz del bus** de la que dependen los
módulos 2-7. Se decidió la **opción C** del issue:

- `J2` intacto — `+12 / GND / GND / −12`, el mismo bus analógico para todos.
- `J6` nuevo — 2 posiciones, solo el feed de +5 V al módulo 2. Netlist ahora:
  `+5V: C10/1, C11/1, D5/2, J6/1, R3/1, U3/3`.

El porqué (contra el header 2×5 que pedía el BOM viejo) está en
[`notes/design-notes.md` §10.4](notes/design-notes.md): retorno del +5 V
dedicado por construcción (§10.1, el backlight va conmutado), ningún +5 V vivo
en módulos que no lo usan, y la tesis nunca tuvo un bus formal que respetar.
Las líneas de `J2` y `J6` en `bom.csv` vuelven a ser comprables.

## Mejoras propuestas

Ver la sección *Mejoras propuestas* en
[`docs/modules/01-power-supply.md`](../../docs/modules/01-power-supply.md).
