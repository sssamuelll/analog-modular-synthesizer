# Módulo 3 — la Voz (SSI2130)

> [!IMPORTANT]
> **Esta página describe la v1, de cuatro osciladores, y está superada —
> 2026-08-22/23.** El módulo pasa a **dieciséis canales completos** (oscilador →
> filtro → VCA en el mismo cobre) más la bahía asignable, con dos RP2350B a
> bordo y una matriz de modulación FM de 16 líneas. Dieciséis y no ocho porque
> **en FM cada voz necesita dos osciladores**: una moduladora compartida entre
> ocho notas no da FM tonal, da campanas disonantes.
>
> Lo de abajo sigue siendo la mejor descripción del canal individual. Mandan el
> [spec de Voz total](../superpowers/specs/2026-08-23-modulo-voz-total-design.md)
> y el [spec de los dieciséis](../superpowers/specs/2026-08-22-modulo-3-vco-dieciseis-design.md).

> Diseño y decisiones de la v1: [spec del módulo](../superpowers/specs/2026-08-16-modulo-3-vco-design.md).
> Hardware: [`hardware/03-vco/`](../../hardware/03-vco/).
> Bring-up: [`hardware/03-vco/notes/bring-up.md`](../../hardware/03-vco/notes/bring-up.md).
>
> **Este módulo ya no es el de la tesis.** El SAM17 pasó a polifónico de 4
> voces y el módulo VCO se rediseñó entero alrededor del SSI2130. La
> descripción de la tesis (3× CEM3340 con mandos por voz) y sus resultados
> medidos se conservan abajo, en [Historia](#historia-el-vco-de-la-tesis-cem3340),
> porque son el punto de partida contra el que se mide todo lo demás.

## Objetivo

Generar el sonido crudo de las cuatro voces. Cuatro canales idénticos con **un
solo juego de mandos** — que no viven en esta placa: son sensores del panel, y
lo que llega aquí son números por el enlace serie. Sale audio ya mezclado por
voz, más cuatro pulsos digitales de afinación.

Objetivo medible: **las 7 octavas de cada voz dentro del rango del DAC, sin
trimmers.**

## Por qué el SSI2130 y no el CEM3340

| | CEM3340 (tesis) | **SSI2130** |
|---|---|---|
| Deriva del expo | −0.33 %/°C crudo, compensador **que hay que ajustar** | **200 ppm/°C típ, compensada en chip** — sin resistencia de tempco |
| Mezcla de ondas | externa, con amplitudes desiguales (defecto medido) | **mezclador VCA de 5 canales dentro del chip**, niveles ya igualados |
| Seno | no lo tiene | **shaper en el chip**, 0.76 % THD, entra por AUX 1 |
| CV de tono | amplificador ×2.8 + trimmers de escala y offset | **nodo de suma de corrientes**, 20 µA/octava, sin amplificador |
| Latentes a coste cero | — | sync y FM through-zero (no expuestos, ver [Fuera de alcance](#fuera-de-alcance)) |
| Encapsulado | DIP-16 | QFN-32 de 4×4 mm — estrena el ensamblaje SMD de fábrica |
| Suministro | re-fabricado, varias fuentes | **proveedor único** (Sound Semiconductor) |

Lo que se acepta a sabiendas: carácter **triangle-core**, distinto del saw-core
del Prophet-5, y depender de un solo proveedor. El plan B, si desaparece del
mercado, es el respin CEM3340 que vive en el historial de git.

## Cómo funciona, bloque por bloque

```
  enlace serie ──┐                          ┌── TUNE_OUT 1-4 (3.3 V)
  (SPI+CS3+I²C)  ▼                          │
     ┌───────────────────────┐         ┌────┴─────┐
     │ 3x AD5686R en cadena  │         │  74HC14  │
     │ ch1-4: PITCH  ch5: PWM│         └────▲─────┘
     │ ch6-9: MIX saw/tri/   │              │ SQUARE OUT (colector abierto,
     │        pulso/seno     │              │  pullup a 3.3 V, por voz)
     │ ch10-12: reserva      │              │
     └──┬──────┬─────────────┘              │
 pitch×4 ▼      ▼ pwm, mix×4 (compartidos)  │
  ┌─────────────────────────────────────────┴───┐
  │  POR VOZ (×4):  SSI2130                     │
  │  expo in (nodo de corriente) ← R ← DAC      │
  │                              ← R ← jack CV-IN│
  │  tri/saw/pulso + seno→AUX1 → mezclador      │
  │  MIX OUT (corriente) → op-amp I/V → jack OUT│
  └─────────────────────────────────────────────┘
  VREF 2.5 V única → DAC y los 4 SSI2130 (los errores escalan juntos)
  telemetría I²C: TMP1075 (pegado a U2) + EEPROM de identidad
  alimentación local: +12 V → 5 V (chips y DAC) → 3.3 V (lógica)
```

### El tono: suma de corrientes, sin trimmers

La entrada del expo es un nodo a tierra virtual que pide **20 µA por octava**.
Ahí entran dos corrientes:

- **del DAC**, por `R_PITCH` de 16.5 kΩ: 2.5 V a fondo de escala son 151.5 µA,
  o sea **7.576 octavas de span** sobre las 7 que hacen falta. Ese **7.6 % de
  margen es el diseño trimless entero**.
- **del jack CV-IN**, por 49.9 kΩ: 1 V/octava exacto. El TN del jack lo ata a
  masa, así que sin cable suma 0 V y el cerebro manda solo.

No hay trimmer de escala ni de offset. Lo que un trimmer arreglaría lo arregla
mejor la tabla de 84 notas de `tuning.json`, incluida la no conformidad del
expo (0.3 %, ~3.6 cents) que un trimmer **no** puede tocar. Y lo que un trimmer
no arregla —la deriva— lo absorbe el autoafinado.

- 1 LSB del DAC = **0.139 cents**. El suelo de medida del autoafinado es 0.5.
- Suelo de afinación del instrumento con el DAC en esta placa: **0.58 cents**
  ([`dac_local_budget.py`](../../hardware/03-vco/dac_local_budget.py)), contra
  1.71 con el DAC en el cerebro.

### La mezcla: dentro del chip

El mezclador de 5 canales del SSI2130 recibe triangular, sierra y pulso ya
escalados internamente —**el problema de amplitudes desiguales de la tesis
muere solo**— y el seno entra por AUX 1 desde el shaper del propio chip. AUX 2
queda de reserva.

Cuatro CV de nivel (sierra / tri / pulso / seno) salen del DAC y son
**compartidos por las cuatro voces**: 0-2.5 V sobre 49.9 kΩ = 0-50 µA de
control lineal, el máximo recomendado. Un 1 % de desparejo entre voces es
amplitud, no tono.

`MIX OUT` es una salida de corriente (500 µA máx): un op-amp en transimpedancia
por voz la convierte a ±5 V y sale por el jack, normalizado hacia el VCF.

**Las ondas crudas no se exponen al patch bay**: la mezcla da cualquier onda
pura desde el preset, así que exponerlas costaría cuatro jacks por voz para no
añadir nada.

### El camino de afinación es digital

El `SQUARE OUT` de cada SSI2130 es de colector abierto con pullup a 3.3 V; un
74HC14 en esta placa limpia el flanco RC antes de que salga por el mazo →
`TUNE_OUT 1-4`.

Esto es instrumentación, no sonido: va antes del filtro, es permanente y no se
patchea nunca. Al ser cuatro líneas lógicas independientes, **las cuatro voces
se miden a la vez**: un barrido completo de 84 notas × 4 voces tarda ~3.5 s
([`autotune_budget.py`](../../hardware/02-midi-cv/autotune_budget.py)).

### Telemetría de serie (patrón para los módulos 5, 6 y 7)

- **TMP1075** (I²C, dirección 0x48) **a 2.12 mm del cuerpo de U2**, dentro del
  área analógica, con un vertido térmico aislado hacia el racimo de
  osciladores. Mide la temperatura **que desafina**, no la del aire.
- **24AA02E48** (I²C, 0x50) con ID único de fábrica: tipo de placa, revisión,
  serial y el blob de calibración de sus 4 voces — **la calibración viaja con
  la placa**.
- **15 test points**: ±12, +5 local, 3.3 local, VREF, CV de tono ×4, nodo I/V
  ×4, GNDA, GNDD.

El lazo que compra mejoras: el cerebro registra (temperatura, correcciones del
autoafinado) por voz y por pasada. Con eso se mide en cents/°C reales si un
cambio térmico o de layout funcionó. Y es la red de seguridad del diseño
trimless.

## Entradas / salidas (por voz)

| Señal | Tipo | Notas |
|---|---|---|
| `CV-IN` | Jack de entrada | 1 V/octava, suma al CV del cerebro. TN a masa: sin cable, 0 V |
| `OUT` | Jack de salida | Mezcla de las 4 ondas, ±5 V. Normalizado al VCF en el jack de entrada del módulo 5 |
| `TUNE_OUT` | Digital, al mazo | Onda cuadrada a 3.3 V. Nunca sale al panel |

Todo lo demás —tono, PWM, y los cuatro niveles de mezcla— llega por el enlace
serie desde el cerebro. **No hay un solo potenciómetro en esta placa.**

## Enlace serie (contrato para los módulos 5, 6 y 7)

IDC 2×6, niveles 3.3 V, SPI modo 1 a ≤10 MHz.

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `SCLK` | `GNDD` | `MOSI` | `MISO` | `CS3` | `GNDD` | `SDA` | `SCL` | `TUNE_OUT_1` | `TUNE_OUT_2` | `TUNE_OUT_3` | `TUNE_OUT_4` |

Los tres AD5686R van en **cadena soldada** (DCEN): `MOSI → U5 → U6 → U7 →
MISO`. Trama de **72 bits** con CS3 abajo de punta a punta; el primer word que
sale por MOSI acaba en U7. El firmware verifica la integridad del enlace
comparando lo que manda con lo que vuelve.

Las **tres referencias internas de los DAC se apagan por firmware** (registro
`0111`) en cada arranque: la referencia de la placa es la ADR4525B externa, y
que todos —DAC y los cuatro osciladores— cuelguen de la misma es lo que hace
que sus errores escalen juntos y se cancelen en el lazo DAC→expo.

## Consumo

**~35 mA en +12 V y ~15 mA en −12 V**, contra los ~120 mA que pedía la versión
CEM3340 + LM13700. Menos calor en el cajón es menos deriva para todos.

## Fuera de alcance

- **FM lineal, hard sync y TZFM**: el chip los trae latentes a coste cero, pero
  los jacks no. La FM exponencial ya la da el CV-IN, y el sync sin pareja por
  voz no aporta. Exponerlos es un respin de panel con dato de uso real.
- **Ondas crudas al patch bay** — descartado, ver [La mezcla](#la-mezcla-dentro-del-chip).
- **El firmware del cerebro** — esta placa define su contrato, no su código.

---

## Historia: el VCO de la tesis (CEM3340)

> Referencia: tesis, *Módulo VCO* (Gráficos 25, 26, 62–66, Tabla 11).
>
> **Esto ya no describe el módulo.** Era el diseño anterior: **tres** VCO
> CEM3340 independientes, cada uno con sus mandos de afinación y PWM en el
> panel y sus trimmers de escala y offset. Se conserva porque sus resultados
> medidos son la razón de casi todas las decisiones del diseño actual.

Tres osciladores idénticos basados en **CEM3340** (el chip del Sequential
Prophet-5), cada uno generando sierra, triangular y cuadrada con PWM
simultáneamente, con `TUNE` y `PWM-CTL` como potenciómetros de panel por voz.

### Resultados medidos del prototipo

| VCO | Variación de la escala 1 V/oct | Lectura |
|---|---|---|
| VCO1 | **+0.45 %** | excelente |
| VCO2 | **−3.32 %** | aceptable |
| VCO3 | **−18.62 %** | mal afinado — solo 5 octavas utilizables |

Y un cuarto defecto, transversal: **la triangular sale con menor amplitud** que
la sierra y la cuadrada.

### Qué hizo el rediseño con cada uno de esos cuatro números

| Defecto medido en la tesis | Qué lo arregla ahora |
|---|---|
| VCO3 a −18.62 % (≈350 cents) — **calibración manual mala**, no deriva | **Se quitan los trimmers.** No hay nada que ajustar mal: el autoafinado mide la frecuencia real y corrige la tabla de 84 notas |
| Las tres voces con escalas distintas entre sí | **Una sola referencia** para los cuatro osciladores y el DAC: los errores escalan juntos |
| Deriva térmica del expo, con compensador que hay que ajustar | **Compensación en chip del SSI2130** (200 ppm/°C típ) + registro temperatura↔correcciones para medir el residuo real |
| Triangular más floja que sierra y cuadrada | **Mezclador interno**, con las tres ondas ya escaladas dentro del chip |

Las mejoras que la tesis proponía y que el rediseño **no** recoge, con su
motivo: entrada de FM lineal y sync (el chip los trae latentes, los jacks no
— decisión de alcance, no de capacidad) y buffer de salida con la misma
ganancia para las tres ondas (innecesario: la mezcla ocurre dentro del chip).
