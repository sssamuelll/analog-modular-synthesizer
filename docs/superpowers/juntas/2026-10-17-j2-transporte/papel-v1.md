# Enmienda propuesta a D5.1 — el transporte del J2 por interrupciones

**v1 · 2026-10-17 · PROPUESTA: sin junta, sin firma.** Si Samuel firma, §1-§3 pasan a la spec del maestro (`2026-09-03-maestro-j2-recuperacion-design.md`) como enmienda de D5.1, D2, D3, D4, R-MJ5 y §3, y §5 es la condición para que el código entre. El brief con la evidencia y las otras opciones está en `junta-2026-10-17-brief.md`.

## 0. Qué decide y qué no

**Decide** la forma del transporte: cómo se arma, se espera y se cierra una transferencia de una ranura, para que el J2 entero —ISR, DMA y lo que haga falta para despachar— quepa en los **2 500 ciclos por giro** firmados el 2026-10-16 (el 15 % de un núcleo a 800 MHz con seis ranuras a 8 kHz).

**No decide:** el protocolo (la cabecera), la política de salud (D7, `core::maestro_j2::Ranura`), quién alimenta el IWDG (D5.4, del hub), el reloj del enlace (#380), el límite (firmado), ni si el planificador entra en él (HUECO, §6).

## 1. Qué cambia y qué no

| Pieza de la spec | Hoy | Con esta propuesta |
|---|---|---|
| D1 (`TSIZE > 0`, NSS por hardware) | firmada | **igual** |
| D2: el orden de arranque, la generación, el `EOT` tardío descartado y contado, el resultado borrado al armar, el SPI apagado entre transferencias, `NVIC::unpend` | firmada | **igual**, escrita en términos de estados y no de futuros |
| D2: *«las dos esperas son futuros bajo `with_timeout`»* | firmada | **cambia**: son dos estados con un plazo (§2.2) |
| D3: la fórmula del plazo y su cota | firmada | **igual** la fórmula; **cambia cómo se vigila** (§2.4, decisión abierta) |
| D4: los seis pasos y la escalada D4.2 | firmada | **igual el contenido**; se ejecutan por registros, a nivel bajo, y se añade un paso: reprogramar los canales (§2.5) |
| D5.1 (1): seis tareas, una por ranura | firmada | **cambia**: seis máquinas de estados, una por ranura |
| D5.1 (2): el planificador es el único escritor (R-C8) | firmada | **igual** |
| D5.1 (3): un `InterruptExecutor` propio | firmada | **cambia**: prioridades de interrupción por encima del hilo (§2.1) |
| D5.1 (4) / D5.4: un sello por ranura al armar; el IWDG es del hub | firmada | **igual** |
| Enmiendas del 18-09 (R15, `Ticker::reset`) y del 16-10 (`Calendario`, `atrasos`) | firmadas | **desaparecen**: un tic de hardware no recupera tics perdidos (§2.7) |
| D7 y `core::Ranura` | firmada | **igual** |
| R-MJ2 (ninguna espera sin cota) | firmada | **igual**: cada estado de espera tiene su plazo |
| R-MJ5 (una tarea por ranura, en el ejecutor del J2) | firmada | **se reescribe**: *«cada ranura activa tiene su máquina, movida por interrupciones por encima del hilo; ninguna tarea del hilo puede retrasar un giro»* |
| R-MJ7 (búferes no cacheables o invalidados) | firmada | **igual**; la forma se decide con la medida (§2.6) |
| Riesgo 6 (el `Drop` del GPDMA sin cota) | abierto | **se cierra por construcción**: no hay `Transfer`, ni `Drop` |

## 2. El diseño

### 2.1 Las piezas y sus niveles de interrupción

| Pieza | Qué hace | Nivel |
|---|---|---|
| **Tic del J2** (`TIM7`, un periodo = 125 µs) | arma, en una pasada, las ranuras `Libre` | alto (`P1`) |
| **`EOT` de cada SPI** (SPI1-6) | cierra el SPI de esa ranura, marca el resultado, avisa al planificador | alto (`P1`) |
| **Planificador + política** (`core::Ranura`) | compone la bajada de cada ranura para el tic siguiente; juzga la subida (CRC del sobre); actualiza cuentas y salud | bajo (`P3`, interrupción de software) |
| **Recuperación D4** | ejecuta la receta de la ranura vencida | bajo (`P3`) |
| **Hilo** | pantalla, USB, MIDI, supervisor del IWDG | hilo |

Los seis periféricos y sus doce canales de DMA siguen corriendo **en paralelo por hardware**: es lo que D5.1 (1) conserva y por lo que las seis ranuras caben (S-8: en serie, 132 µs en un giro de 125). El tic arma las seis seguidas; la sexta empieza unos 8 µs después de la primera (ESTIMADO: ~1 100 ciclos por ranura a 800 MHz, de la cota), contra los 125 µs del periodo y los 25 µs de un `NADA`.

Un plazo vencido en una ranura no retrasa a las otras cinco (H-1): la recuperación corre en `P3`, por debajo del tic y de los `EOT`; mientras dura (20 µs ESTIMADO) los demás giros se arman y se cierran.

### 2.2 La máquina de estados de una ranura

Vive en `core` (`Transporte`), pura y probada en el host, como la política. `fw` solo traduce sus acciones a registros.

| Estado | Evento | Acción | Estado siguiente |
|---|---|---|---|
| `Libre` | `Tic` | `Armar` (D2, §2.3): generación +1, sello +1 | `Armada` |
| `Armada` | `Eot` (generación vigente) | `Cerrar` (D2, orden de cierre) | `Cerrando` |
| `Armada` | `Tic`, plazo cumplido | pedir D4 | `Vencida` |
| `Armada` | `Tic`, plazo no cumplido | contar `tics_perdidos` | `Armada` |
| `Cerrando` | `Consumida` (el planificador juzgó) | — | `Libre` |
| `Vencida` | — | recuperación D4 (§2.5) | `Reiniciando` |
| `Reiniciando` | `ReinicioHecho` | contar `plazos_vencidos` | `Libre` (la ranura se rearma en el **siguiente** tic: el hueco de un periodo sale solo) |
| `Vencida`, `Reiniciando`, `Libre` | `Eot` | descartar y contar `eot_tardios` (D2 regla 1) | sin cambio |
| `Cerrando` | `Tic` | contar `tics_perdidos`; no se arma | `Cerrando` |

Una ranura sin identidad no se arma ni se cuenta (R-MJ6): el tic la salta.

### 2.3 El giro normal, contra el orden de D2

**Tic (`P1`)**, por cada ranura `Libre` y con identidad:
1. toma del buzón la bajada que dejó el planificador y su `TSIZE` (un `NonZeroU16`, R-MJ1);
2. borra el resultado guardado y sube la generación (D2 reglas 1 y 2);
3. `SELLOS[n] += 1` (D5.4);
4. ejecuta el orden de D2 **con los registros ya calculados** (`SPE` ya está en 0): `TXTFC → TSIZE → CFG1(RXDMAEN) → canal RX (BR1, dirección, CR.EN) → canal TX (BR1, dirección, CR.EN) → CFG1(TXDMAEN) → CR1(SPE) → leer CR1 → esperar ≥ 1 T_SCK → EOTC → EOTIE → CR1(CSTART)`. Los canales del GPDMA se programan **una vez** (`TR1`, `TR2`, `TR3`, `CR`); por giro solo se escriben `BR1`, la dirección de memoria y `CR.EN`. Cada registro se escribe entero, sin leer-modificar-escribir;
5. anota `t_arm` y el plazo del mensaje (§2.4).

**`EOT` (`P1`)**: lee `SR`. Con la ranura `Armada` y la generación vigente: borra las banderas por `IFCR`, `SPE = 0` y solo entonces los dos `DMAEN` a cero (D2, cierre del manual §67.4.14), marca la subida como lista y levanta la interrupción de software del planificador. En cualquier otro estado: `eot_tardios += 1` y borra las banderas.

**Planificador (`P3`)**: por cada ranura `Cerrando`, juzga la subida (el CRC del sobre, cabecera D6), pasa a la política `GiroOk` y `SubidaOk` o `SubidaMala` con la hora del cierre, publica las cuentas, compone la bajada del tic siguiente y deja la ranura `Libre`. Es el único escritor del enlace (R-C8): el transporte no decide nada del protocolo.

### 2.4 El plazo (D3): decisión abierta entre dos formas

La fórmula no cambia: `plazo(msg) = 2 × t_nominal(msg) + 20 µs`, ≤ 220 µs en la cota. Lo que cambia es **quién se entera de que venció**:

- **P1 — comparador por ranura.** Un canal de comparación de un temporizador de 32 bits (`TIM2`/`TIM5`, 4 canales cada uno; a verificar en el RM del N657) por ranura: una escritura al armar, una al cerrar, y una ISR que solo corre cuando algo se cuelga. Exacto, ~50 ciclos por giro.
- **P2 — cuantizado al tic.** El tic mira, por cada ranura `Armada`, si `ahora − t_arm ≥ plazo`. Cero hardware nuevo y cero ciclos extra, con `DWT_CYCCNT` como reloj (sin acceso al bus). La detección llega **hasta un periodo tarde**: un `NADA` (plazo 70 µs) se da por vencido en el tic siguiente (125 µs), un `SET` de dieciséis (226 µs) en el segundo (250 µs).

Con P2 un `EOT` que llega pasado el plazo y antes del tic siguiente **se acepta como bueno**: el plazo deja de ser una frontera del giro y pasa a ser una frontera de detección de cuelgue, y `plazos_vencidos` cuenta menos que con P1. El margen real del plazo lo mide `plazos_j2` con osciloscopio, no este contador.

Con P2, el techo de recuperación de §3 pasa de 220 + 20 + 125 + 125 = **490 µs** a unos 226 + 125 + 20 + 125 + 125 = **620 µs**; el margen contra los ~50 ms del módulo baja de 102× a ~80×, y el presupuesto exige ≥ 10×. **Recomendación v1: P2**, por ser la que menos código nuevo trae; P1 si la junta quiere el plazo exacto de D3.

### 2.5 La recuperación (D4), por registros, a `P3`

Los seis pasos de la enmienda del 14-10, **en el mismo orden**, con uno nuevo (el 6):

1. `EOTIE = 0` y `NVIC::unpend` de la interrupción de la ranura.
2. Soltar el DMA con cota `T_CANAL` (ESTIMADO 10 µs): `CR.SUSP` a los dos canales, sondear `SR` hasta `T_CANAL`; si un canal no para, **escalar**.
3. Resetear el SPI por RCC (`rcc::disable` y después `rcc::enable_and_reset`).
4. Reescribir `CFG2` y `CFG1` como los dejó la construcción (D1).
5. `NVIC::unpend` otra vez.
6. **Reprogramar los dos canales** (`TR1`, `TR2`, `TR3`, `CR`). *Paso nuevo:* hoy lo hace implícitamente el `configure` de embassy en cada transferencia; con los canales programados una vez, un reset los deja en valores de reset.
7. Contar y seguir (`plazos_vencidos += 1`).

**La escalada D4.2** (un canal no para): resetear el GPDMA1 entero por RCC borra la configuración de **los doce canales**. Las otras cinco ranuras ven morir sus transferencias, no reciben `EOT`, vencen y ejecutan D4 cada una (como dice la enmienda del 18-09), y el D4 de cada una reprograma sus canales. Pero una ranura que estuviera `Libre` entre dos giros se armaría en el tic siguiente con los canales vacíos: la escalada marca todas las ranuras con `canales_sucios` y el tic las reprograma antes de armar. Se cuenta aparte (`escaladas_gpdma`).

### 2.6 Los búferes (R-MJ7)

Los búferes de bajada y subida de las seis ranuras (25 a 103 bytes cada uno) viven en una sección propia (`.j2_dma`), alineados a 32 bytes, con las dos formas permitidas por R-MJ7:

- **(i) Región MPU no cacheable.** Sin mantenimiento; el precio es que cada lectura del búfer de subida cuesta ~80 ciclos por palabra a 800 MHz (`costes_bus`), así que el CRC lee con una ráfaga (`ldm`) a una copia local.
- **(ii) Cacheable con mantenimiento por dirección.** `clean` de la bajada antes de armar, `invalidate` de la subida antes de leer; unas decenas de ciclos por línea de 32 bytes, y los búferes ocupan líneas enteras.

**No se decide aquí: se mide las dos** en el banco (§4) y se elige la que deje el giro más corto. HUECO.

### 2.7 Los contadores, el sello y lo que desaparece

- `plazos_vencidos`, `eot_tardios`, `subidas_malas`, `escaladas_gpdma`: la misma semántica.
- **`atrasos` (enmienda del 16-10) pasa a `tics_perdidos`:** el tic encontró la ranura sin acabar y todavía en plazo. Un mensaje normal (≤ 103 µs) no puede provocarlo; si ocurre, es una ISR que llegó tarde, y se cuenta.
- El sello del IWDG sube al armar, como hoy.
- **Desaparecen:** las tareas y el `EJECUTOR_J2` de `fw/src/j2_ejecutor.rs`, `Calendario` (con sus tests) y las enmiendas R15 y del 16-10 de D5.1, `embassy_time::Timer` en el camino del J2, y el uso de los `Transfer` de embassy para el J2.

## 3. La CPU

La cota medida, `j2_isr` en la Nucleo a 800 MHz con las dos cachés y sin región MPU, es **1 500 ciclos por giro** (1 121 en la ISR del tic y 185 en la del SPI; el resto, lo que el hilo pierde al volver). Lo que esta propuesta añade, ESTIMADO y sin fuente:

| Parte | Ciclos por giro |
|---|---|
| la cota | 1 500 |
| plazo (P2: cero; P1: ~50) | 0 a 50 |
| generación, `EOT` tardío, estados | ~50 |
| búferes: región o mantenimiento (§2.6) | 100 a 600 |
| **suma, sin el planificador** | **1 700 a 2 200** |
| planificador real (la trama, el CRC del sobre, los eventos) | **HUECO** |

El límite es 2 500. **La propuesta cabe en el papel; que quepa en la placa lo dice una fila de `carga_j2.csv`** (§5).

## 4. Lo que se prueba

- **Host (`core`).** `Transporte` como función pura: todas las filas de la tabla de §2.2 con sus bordes; ningún armado sobre una ranura `Armada`, `Cerrando` o `Vencida`; el `EOT` tardío siempre se cuenta y nunca se consume; la recuperación vuelve a `Libre`; y una simulación de seis ranuras con cuelgues aleatorios que comprueba H-1 (las otras cinco no pierden ni un tic) y el techo de recuperación.
- **Banco, con esclavo.** `resistencia_j2` con el transporte nuevo, a 1 kHz y a 8 kHz; un SPI envenenado a propósito, que vence su primer giro y se recupera con los dos siguientes bien (como el 14-10); el barrido del retardo con el transporte nuevo; `plazos_j2` con osciloscopio; `carga_j2` con las dos formas de §2.6.

## 5. Condiciones para que el código entre y para fabricar

1. **Una fila de `carga_j2.csv` a ≥ 800 MHz**, con las cachés del hub, la forma de R-MJ7 elegida y **el transporte completo** (todo lo de §2 compilado, el planificador real o su coste medido), con ≤ 2 500 ciclos por giro. Sin ella, esta propuesta no cierra el riesgo 9.
2. Las pruebas de §4 en verde, con la recuperación ejercida en placa.
3. **Antes de fabricar (R-MJ8): el soak de 24 h con el transporte nuevo.** La fila del 16-17 de octubre es del transporte de D5.1 y no se transfiere. La puerta (`recuperacion_j2_budget.py`) lo sigue marcando HUECO hasta que haya una fila a la cadencia del lazo.

## 6. Qué queda abierto

- **Si el planificador entra en el límite de 2 500** y cuánto cuesta (la trama, el CRC del sobre, los eventos). Sin esa respuesta, la suma de §3 no cierra.
- P1 contra P2 (§2.4).
- Región MPU contra mantenimiento por dirección (§2.6).
- Los otros usos de `GPDMA1` en el hub (si el escritor de CV comparte el controlador, la escalada D4.2 también lo reinicia).
- La fuente del tic (`TIM7`) y los niveles contra las ISR del USB y la pantalla, que son del papel del hub.
- Qué hace el tic con una ranura sin módulo (R-MJ6) y con una que acaba de recuperarse.
- Si la recuperación a `P3` se queda en una interrupción de software o pasa a una tarea de baja prioridad con `Timer` (la opción A' del brief).
