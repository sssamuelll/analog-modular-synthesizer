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
      7812/7912/7805, protecciones DC, indicadores), lado primario
      **230 V/50 Hz** (fusible 250 mA + MOV S20K275 + NTC de soft-start,
      [`notes/design-notes.md`](notes/design-notes.md) §10/§12) y **tierra de
      protección** con puente de chasis en punto único (§13). ERC sin errores
      ni avisos, netlist verificado, y `bom.csv` cuadra con el esquemático
      designador a designador (`python kicad/check_bom.py`).
- [ ] **Salida de +5 V al bus** — el riel se genera pero no sale de la placa
      (ver abajo)
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
- **Tierra de protección** ([§13](notes/design-notes.md)): puente **duro** entre
  chasis y GND, en un **punto único** (espárrago M4 dedicado). No se usa red de
  *ground lift* porque los paneles son lámina galvanizada y los ~40 jacks de
  3.5 mm ya unen chasis y GND por el casquillo — una red de lift estaría
  cortocircuitada 40 veces. El PE **no lleva pista en la PCB**: va del bornero
  `J3.3` al espárrago por cable, y el 0 V sube al mismo espárrago por el faston
  `J5`. La corriente de falla nunca pasa por la placa.
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

## Pendiente: el riel de +5 V no sale de la placa

Encontrado en el mismo cruce, y es más gordo que los dos anteriores:

- El netlist dice `+5V: C10/1, C11/1, D5/2, R3/1, U3/3`. **Ningún pin de `J2`.**
  El 7805 alimenta su propio LED indicador y nada más.
- `J2` está dibujado con 4 pines: `+12 / GND / GND / −12`.
- `bom.csv` pedía para el bus un *pin header 2×5* con
  `-12/-12/GND/GND/+12/+12/+5/+5`, es decir, con +5 V.

Pero el riel de +5 V existe justamente para alimentar el **AD5686R y el LCD**
del módulo MIDI/CV ([`notes/design-notes.md`](notes/design-notes.md) §10.1), que
están en otra placa. Tal como está dibujado, no puede llegar.

No se ha corregido a criterio propio porque cambiar `J2` es cambiar la
**interfaz del bus**, y de eso dependen todos los demás módulos: hay que decidir
conector y orden de pines una vez, no improvisarlo aquí. La línea de `J2` en
`bom.csv` queda marcada como *no comprar*.

## Mejoras propuestas

Ver la sección *Mejoras propuestas* en
[`docs/modules/01-power-supply.md`](../../docs/modules/01-power-supply.md).
