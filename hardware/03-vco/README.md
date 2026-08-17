# Hardware — Módulo 3: VCO ×4 (SSI2130)

> Documentación funcional: [`docs/modules/03-vco.md`](../../docs/modules/03-vco.md).
> Diseño y decisiones: [spec del módulo](../../docs/superpowers/specs/2026-08-16-modulo-3-vco-design.md).
> Arquitectura polifónica: [`docs/architecture-poly.md`](../../docs/architecture-poly.md).
> **Bring-up de la placa física: [`notes/bring-up.md`](notes/bring-up.md).**

## Resumen

**Cuatro voces idénticas en una sola placa**, con un solo juego de mandos —
que no viven aquí: son sensores del panel, y lo que llega a esta placa son
números por el enlace serie. Sustituye a los tres osciladores independientes de
la tesis (Gráficos 25-26).

El núcleo es el **SSI2130** (Sound Semiconductor, 2020), no el CEM3340 de la
tesis. Lo que ese cambio se lleva por delante: la resistencia de compensación
térmica (la lleva el chip), el amplificador de ×2.8 del CV de tono (la entrada
del expo es un nodo de corriente), el mezclador externo y el problema de
amplitudes desiguales (el chip trae un mezclador VCA de 5 canales), y el
generador de seno (lo trae el shaper del propio chip).

Y una cosa que la tesis no tiene: **una salida `TUNE_OUT` digital por voz** —
la onda recortada a nivel lógico con un 74HC14 **en esta placa**. El camino de
afinación es instrumentación, no sonido: va antes del filtro, es permanente, no
se patchea nunca, y al ser cuatro líneas lógicas independientes **las cuatro
voces se miden a la vez**.

## Qué decide este módulo

| | |
|---|---|
| Núcleo | **SSI2130 ×4**, QFN-32. Proveedor único: comprar 6 (4 + 2 repuestos) |
| Afinación | **Trimless**: cero trimmers. La escala la fijan una ADR4525B (2 ppm/°C) y resistencias del 1 % |
| Span nominal | **7.576 octavas** (2.5 V / 16.5 k / 20 µA por octava) sobre las 7 que pide el instrumento: **7.6 % de margen** |
| Resolución | 1 LSB = **0.139 cents**, contra un suelo de medida de 0.5 |
| Suelo de afinación | **0.58 cents** ([`dac_local_budget.py`](dac_local_budget.py)), 3× mejor que con el DAC en el cerebro |
| Mezcla | **dentro del chip**: sierra/tri/pulso/seno con 4 CV compartidos, control lineal 0-50 µA |
| Referencia | **UNA** para toda la placa (ADR4525BRZ). Las tres internas de los DAC **se apagan por firmware** (registro `0111`) |
| Digital | 3× AD5686R en **cadena soldada** (DCEN): 9 canales usados + 3 de reserva |
| Telemetría | TMP1075 a **2.12 mm del cuerpo de U2**, EEPROM 24AA02E48 con ID único, 15 test points |
| Consumo | **~35 mA en +12 V, ~15 mA en −12 V** — contra los ~120 mA de la versión CEM3340+LM13700 |
| Patch bay | 8 jacks: CV-IN ×4 (normalizados a 0 V) y salida de voz ×4 (normalizadas al VCF en el módulo 5) |

**La apuesta que hay que cobrar en la placa**: el margen del 7.6 % de span
existe para no llevar trimmers. Nadie garantiza la dispersión chip a chip del
convertidor exponencial del SSI2130, así que **hasta que no se mida no está
demostrado**. El bodge previsto si una voz cae fuera es cambiar **su**
`R_PITCH` — una resistencia, no un re-spin. Procedimiento y valores en el
**Paso 5** de [`notes/bring-up.md`](notes/bring-up.md).

## Componentes principales

| Función | Componente | Ref |
|---------|------------|-----|
| Núcleo VCO + mezclador + seno | **SSI2130**, QFN-32 | U1-U4 |
| DAC 16 bits ×4, en cadena | **AD5686RBRUZ** ×3 | U5-U7 |
| La referencia de la placa | **ADR4525BRZ**, 2.5 V, 2 ppm/°C | U8 |
| Transimpedancia MIX OUT → jack | **TL074H** (el H por deriva) | U9 |
| `TUNE_OUT` ×4 a 3.3 V | **74HC14** Schmitt | U10 |
| Alimentación local +5 V / +3.3 V | L78L05 → LD1117S33 | U11, U12 |
| Telemetría | TMP1075 (I²C 0x48), 24AA02E48 (0x50) | U13, U14 |

BOM completo, con los porqués: [`bom.csv`](bom.csv).

## El mazo digital J2 — contrato del enlace

IDC 2×6, niveles 3.3 V. **Mismo conector y mismas posiciones en los módulos 5,
6 y 7**; cada uno usa las señales que le tocan y recibe su propio CS.

| 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| `SCLK` | `GNDD` | `MOSI` | `MISO` | `CS3` | `GNDD` |

| 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|
| `SDA` | `SCL` | `TUNE_OUT_1` | `TUNE_OUT_2` | `TUNE_OUT_3` | `TUNE_OUT_4`|

SPI modo 1, ≤10 MHz. **CS3 abajo durante los 72 relojes de la trama entera** (3
chips × 24 bits); el flanco de subida carga los tres. **El primer word que sale
por MOSI acaba en U7 y el último se queda en U5**: orden de transmisión
`[U7][U6][U5]`.

Canales del DAC: **U5** A-D = tono de las voces 1-4. **U6** A = PWM (compartido),
B/C/D = mezcla sierra/tri/pulso. **U7** A = mezcla de seno, B/C/D de reserva.

## La placa

114 × 124 mm, **4 capas**. `In1` es un plano GNDA sólido, en una sola isla al
100 % — por ahí no pasa ni una pista, solo vías. La masa digital es una **isla**
en la esquina de J2, con 3.00 mm de hueco.

Colocación en **cuadro 2×2**, no en fila: los 3 DAC y la referencia caben en el
hueco central y las 4 voces quedan a la misma distancia del DAC (peor par
**43.2 mm**, dentro de la cota de `dac_local_budget.py`). En fila el peor par se
iba a 85 mm.

El **EP de cada SSI2130 queda aislado a propósito** — sin red, sin vía, sin unión
al plano. Lo prohíbe el datasheet (pág. 6): unirlo a masa convierte el land en
una antena de acoplo entre las cuatro voces.

Los porqués completos viven en los docstrings de
[`kicad/build_schematic.py`](kicad/build_schematic.py) y
[`kicad/build_pcb.py`](kicad/build_pcb.py). El ruteo lo hace Freerouting, no un
ruteador casero.

## Estructura del directorio

```
03-vco/
├── README.md
├── bom.csv                     30 líneas, cada una con su porqué
├── dac_local_budget.py         Qué gana el DAC viviendo en esta placa
├── kicad/
│   ├── build_schematic.py      Genera sam17-vco.kicad_sch (s-expr + kicad-cli)
│   ├── build_pcb.py            Genera sam17-vco.kicad_pcb (pcbnew + Freerouting)
│   ├── check_netlist.py        Conectividad contra el diseño declarado
│   ├── check_bom.py            Cruce esquemático <-> bom.csv
│   ├── sam17.kicad_sym         Símbolos propios: SSI2130 y AD5686RBRUZ
│   ├── sam17-vco-erc.rpt       0 errores, 0 avisos (regenerado por build_schematic.py — *.rpt gitignorado, no vive en el repo)
│   └── sam17-vco-drc.rpt       0 infracciones (regenerado por build_pcb.py — *.rpt gitignorado, no vive en el repo)
├── pcb/                        Gerbers, taladros, posiciones, BOM de ensamblaje
│   └── README.md               Qué pedir, qué va consignado, qué se suelda a mano
├── schematics/                 (vacío — el PDF se exporta al pedir)
└── notes/
    └── bring-up.md             El procedimiento con la placa en la mano
```

## Estado

- [x] **Spec cerrado** con las decisiones y sus porqués — SSI2130, trimless,
      referencia única, telemetría de serie
- [x] **Presupuesto de afinación en verde**: suelo de **0.58 cents**, y la
      condición que impone (referencia grado B) queda como aserción ejecutable
- [x] **Esquemático en KiCad** — **ERC 0 errores, 0 avisos**. 136 componentes,
      152 redes. Pinout del SSI2130 y del AD5686R verificados contra la Figure 1
      y las tablas de sus datasheets, no copiados de un diagrama
- [x] **PCB ruteada y cerrada** — 4 capas, 114×124 mm, 136 huellas + 4 taladros
      de montaje, **0 conexiones abiertas y DRC 0**. `In1` en una sola isla al 100.00 %,
      los 4 EP aislados, frontera GNDA/GNDD de 3.00 mm medida, desacoplos a
      1.80 mm, reglas afinadas a la capacidad estándar de JLCPCB (sin recargo)
- [x] **Salidas de fabricación generadas** — gerbers, Excellon, posiciones SMD
      (111 huellas) y BOM de ensamblaje. Ver [`pcb/README.md`](pcb/README.md)
- [x] **Procedimiento de bring-up escrito** — [`notes/bring-up.md`](notes/bring-up.md)
- [ ] **Pedido a fábrica** — falta cotizar, rellenar los LCSC Part# y decidir si
      los SSI2130 van consignados o se sueldan a mano (los dos caminos están
      documentados; el bring-up recomienda uno)
- [ ] **Comprar los SSI2130** — proveedor único (Cabintech / Amplified Parts),
      **6 unidades**, en la misma orden
- [ ] **Bring-up sobre placa física** — nada de lo de arriba está medido. Los
      tres que mandan:
  - [ ] **DCEN con tres chips reales** (bloqueante, spec §11.7)
  - [ ] **Span ≥ 7.0 octavas por voz** — la apuesta trimless (spec §11.2)
  - [ ] Diafonía del mazo digital (spec §11.8)
- [ ] **Autoafinado** poblando `tuning.json` y el blob de calibración en la
      EEPROM
- [ ] **Primer registro temperatura ↔ correcciones** — el punto de partida de la
      telemetría del instrumento
- [ ] Firmware del cerebro: esta placa define su contrato (enlace, telemetría,
      `TUNE_OUT`), no su código
