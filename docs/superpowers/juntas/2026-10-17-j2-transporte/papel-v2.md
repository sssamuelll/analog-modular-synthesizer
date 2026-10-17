# Enmienda propuesta a D5.1 — el transporte del J2 «por tic» (v2)

**v2 · 2026-10-17 · PROPUESTA: sin firma, y sin pasar por la junta.** Absorbe los informes de Serrano, Halberg y Voronov sobre el papel-v1 (`junta_serrano.md`, `junta_halberg.md`, `junta_voronov.md`) y lo sustituye; el v1 queda como registro. **Lo que este papel propone es un diseño candidato, no una decisión:** lo que decide si hay que construirlo son tres respuestas de Samuel (§1) y las medidas de §4, y el diseño necesita una segunda pasada de la junta —la simulación de Halberg sobre la máquina de §2.2— antes de firmarse.

## 0. Qué cambió respecto a v1, y por qué

La junta refutó el v1 en sus mecanismos, no en sus parámetros. Lo comprobé contra el manual y el código donde citaba uno de los dos (RM0486 Rev 4 p. 3449 y §19.4.4 p. 943; `gpdma/mod.rs:561-613` del rev `697ec64`; el ID de cada hallazgo, en §8):

- **Cerraba en el EOT sin esperar al DMA.** El manual dice que al apagar el SPI el RxFIFO se vacía y que hay que leerlo antes (p. 3449). El v1 desaparecía la espera del DMA de D2 y dejaba la ranura muerta si perdía la carrera.
- **La recuperación omitía `CxCR.RESET`.** El aborto de un canal es suspender, esperar `SUSPF`, **resetear**, reprogramar `BR1/SAR/DAR` y habilitar (§19.4.4). Ese reset lo hacía el `Drop` de embassy, que el v1 borraba. Y un reset de canal no borra `TR1-TR3`; solo el del GPDMA1 por RCC lo hace.
- **Las doce líneas de IRQ de canal no tenían dueño.** El manejador de embassy hace `panic!` ante un error del DMA y, ante `SUSPF`, escribe `CR = 0`, que reanuda el canal a espaldas de la recuperación.
- **El tic y el EOT, al mismo nivel, se desempatan por número de IRQ**, y declarar «vencido» sin mirar el EOT convierte una sección enmascarada de 46 a 100 µs en seis reinicios de SPI con tramas buenas.
- **Tres estados esperaban sin plazo** (`Cerrando`, `Vencida`, `Reiniciando`), y la recuperación compartía cola con el planificador.
- **Medí además, por mi cuenta,** que un `info!` de `defmt` mantiene las interrupciones apagadas 174 µs sin cachés y 11 con las dos: el tic de la cota se retrasaba ~110 µs cada vez que el banco imprimía (PR #438).

**La respuesta del v2 es quitar la interrupción del SPI.** Una sola interrupción periódica, el tic, lee `SR` de cada ranura y decide: cerrar, esperar, vencer o armar. Con ella desaparecen la carrera tic/EOT, las seis ISR de SPI, la generación del EOT, `EOTIE`, `NVIC::unpend`, y —como el tic es la única que escribe el estado de la ranura— la exclusión mutua que antes daba el ejecutor. El costo es que la subida llega a la política con hasta un periodo de retraso (§2.6), y que el plazo de D3 pasa a vigilarse en tics (§2.4).

## 1. Lo que este papel necesita de los demás, y de Samuel

La junta de Voronov lo llama la restricción invisible: cada garantía del J2 está escrita para un sistema cerrado y se despliega en un hub abierto, cuyo censo de CPU no existe. Este papel no puede cerrarlo; **lo declara**.

**De Samuel (el acta):**
1. **Qué cuenta contra los 2 500 ciclos.** La firma dice «con sus ISR, el despacho del ejecutor y los DMA»; el medidor cuenta todo lo que preempte al hilo; el planificador (componer la trama, el CRC del sobre, la política) no figura en la firma y entra en el medidor. Sin esta respuesta, una misma fila pasa o falla según la lectura.
2. **Qué estatus tiene el 15 %:** límite duro, o primera fila de un censo que no existe y por tanto provisional.
3. **Si se construye el spike** de §4 (el transporte completo en el banco, con esclavo) para medir con la definición que se elija.

**Del papel del hub** (requisitos que este diseño exige y que hoy no están escritos; ninguno es mío):
- **R-H1, niveles de NVIC:** el tic en el nivel 1; USB, pantalla y MIDI en el 2 o por debajo; el planificador en el 3; la recuperación en el 4. Hoy ninguna línea fija el nivel del USB ni de la pantalla (el único `set_priority` fuera de `j2_*` es el del muestreo del banco), y el driver USB de embassy queda en el reset del NVIC, nivel 0, **por encima del tic**.
- **R-H2, máximo enmascarado:** ninguna sección crítica de más de 5 µs (con 2 µs no se pierde un tic; con 5 a 10, la ranura con un `SET` de dieciséis [SIM, Halberg]), y **nada de `defmt` con el J2 girando**: una llamada tarda ~11 µs con las dos cachés y más de un periodo sin ellas.
- **R-H3, el GPDMA1 es del J2:** los doce canales (y la escalada D4.2, que resetea el controlador entero) suponen que nadie más lo usa. El escritor de CV es HUECO (#367); si lo comparte, cada recuperación escalada del J2 es un artefacto audible, contra «cero artefactos audibles atribuibles al bus».
- **R-H4, la D-cache encendida con la región de R-MJ7.** Sin ella ningún transporte cabe (7 700 ciclos por ISR, 57 000 por ejecutor).
- **R-H5, el reloj del kernel del SPI (#380).** Con el reloj del hub, `pclk2` es 100 MHz y pedir 10 MHz da `/16 = 6,25 MHz`: un `SET` de dieciséis dura 131,8 µs, **más que el periodo**. A 8 MHz (la Nucleo a 64 MHz) son 103 µs.
- **R-H6, el censo de CPU del hub**, que es lo que convierte los 2 500 en un presupuesto.

## 2. El diseño candidato: el transporte «por tic»

### 2.1 Los recursos, sus dueños y los niveles

| Recurso | Dueño | Cómo |
|---|---|---|
| El tic (`TIM7`, un periodo de 125 µs) | el transporte | la única interrupción del J2; nivel 1 |
| Los seis SPI | el transporte, por registros | `EOTIE = 0` siempre. Sus seis líneas de IRQ, enmascaradas en el NVIC. `Ranura::nueva` solo configura pines, reloj y `CFG1/CFG2` |
| Los doce canales del GPDMA1 | el transporte, por registros | `TCIE`, `USEIE`, `DTEIE` y `SUSPIE` a cero. Sus doce líneas de IRQ, enmascaradas. Ningún `Transfer` ni `bind_interrupts!` de embassy sobre ellos |
| Los búferes de bajada y subida | sección `.j2_dma` | R-MJ7, §2.6 |
| La política (`core::Ranura`) | el planificador | **el único** que llama `paso` |
| El buzón de bajada (por ranura) | lo escribe el planificador, lo lee el tic | doble búfer, se consume al armar |
| El anillo de eventos (por ranura) | lo escribe el tic, lo lee el planificador | productor y consumidor únicos |
| El estado de una ranura | el tic | nadie más lo escribe, salvo `ReinicioHecho` y `canales_sucios` (§2.5) |

Los niveles: **tic (1)**, **planificador (3)**, **recuperación (4)**. La recuperación va por debajo del planificador para que un reinicio de 20 µs no retrase la composición de las tramas de las demás ranuras (B7 de Halberg: con la cola compartida, 4 a 6 % de los cuelgues cuestan un tic a un vecino con un `SET`; con la recuperación por debajo, cero).

Los seis periféricos y los doce canales siguen corriendo **en paralelo por hardware** (D5.1 (1), S-8). El tic arma las seis ranuras seguidas, y los seis armados duran en total unos 3,5 µs (450 ciclos por ranura, por los costes de bus medidos) y 8,5 µs como máximo (los 1 121 de la cota) [SIM, Halberg]; durante ese tiempo el tic tiene ocupado el nivel 1.

### 2.2 La máquina de una ranura

Vive en `core` (`Transporte`), pura y probada en el host. **Una sola entrada por tic**, calculada por `fw` leyendo registros:

```
Entrada del tic = { eot: bool, tcf_rx: bool, tcf_tx: bool, error_dma: bool }
```

| Estado | Entrada / suceso | Acción | Estado siguiente |
|---|---|---|---|
| `Libre` | tic, hay bajada fresca y la ranura tiene identidad | `Armar` (§2.3); emite `Armada` | `Armada(edad = 0)` |
| `Libre` | tic, sin bajada fresca | cuenta `sin_bajada`; no arma | `Libre` |
| `Armada(e)` | `eot ∧ tcf_rx ∧ tcf_tx ∧ ¬error_dma` | `Cerrar`; publica la subida; emite `GiroOk`; arma otra vez si hay bajada fresca | `Libre` o `Armada(0)` |
| `Armada(e)` | `error_dma` | `Cerrar`; cuenta `errores_dma`; emite `PlazoVencido` | `Vencida` |
| `Armada(e)` | ninguna de las anteriores, `e + 1 < N` | — | `Armada(e + 1)` |
| `Armada(e)` | ninguna de las anteriores, `e + 1 ≥ N` | emite `PlazoVencido` | `Vencida` |
| `Vencida` | el planificador devuelve `Accion::Reiniciar` | la recuperación (§2.5) | `Reiniciando(0)` |
| `Reiniciando(r)` | tic, `ReinicioHecho` hace ≥ `T_GAP_REARME` | — | `Libre` |
| `Reiniciando(r)` | tic, sin `ReinicioHecho` | — | `Reiniciando(r + 1)` |
| `Vencida`, `Reiniciando(r)` | `r` o el tiempo en `Vencida` pasa de la cota (§2.5) | emite `RanuraMuerta` | `Muerta` |
| `Muerta` | — | no arma y **no sella**: el IWDG del hub se queda sin sello | `Muerta` |

Dos cosas que el v1 no tenía y la junta pidió:
- **No hay estado `Cerrando`.** El cierre es inmediato porque la subida va a un doble búfer: el tic cierra, publica el índice y arma el búfer contrario; el planificador la lee cuando le toque. La ranura no espera al planificador para volver a `Libre`.
- **Todo estado de espera tiene una cota en tics** (`Armada`: `N`; `Vencida`, `Reiniciando`: §2.5). R-MJ2 se cumple con una frase distinta de la de D2: «ninguna espera es un bucle síncrono sin cota ni un estado sin salida».

### 2.3 El giro normal contra D2

**Arranque** (D2, con sus tres enmiendas, sin tocar), con los registros ya calculados: `SPE = 0 → TXTFC → TSIZE → CFG1(RXDMAEN) → canal RX (BR1, dirección, CR.EN) → canal TX (BR1, dirección, CR.EN) → CFG1(TXDMAEN) → SPE = 1 → leer CR1 → esperar ≥ 1 T_SCK → EOTC → CSTART`. Sin `EOTIE`. **El primer `SPE = 0` se conserva** (v1 lo había quitado apoyándose en un invariante de estado). Por giro solo se escriben `BR1`, la dirección de memoria y `CR.EN` de cada canal; el resto se programó una vez (§2.5, paso 4). Los canales se arman solo si sus `CR.EN` están en cero (RM: los registros de transferencia son de solo lectura con `EN = 1`).

**Cierre** (RM0486 p. 3449: *«the user must ensure that RxFIFO is empty when disabling the SPI»*; el procedimiento estándar sondea `EOT`): el tic lee `SR` del SPI y el `SR` de los dos canales; si `EOT ∧ TCF_RX ∧ TCF_TX` y ningún `DTEF/USEF/ULEF`, escribe las banderas por `FCR`/`IFCR`, `SPE = 0` y solo entonces los dos `DMAEN` a cero. Se cierra **un periodo después del armado** como mínimo (así lo hace la cota de 1 500, que es lo único medido), cuando el DMA de recepción ya vació la FIFO con mucho margen; la condición sobre `TCF` está para que un canal parado o con error no se dé por bueno.

### 2.4 El plazo (D3), en tics

`N(msg) = ceil(plazo_us(msg) / PERIODO_GIRO_US)`, con `plazo_us` de `core` sin tocar:

| Mensaje | a 8 MHz | a 6,25 MHz |
|---|---|---|
| `NADA` 25 B | 70 µs → 1 tic | 84 µs → 1 |
| `EVENTO` 14 B | 48 → 1 | 56 → 1 |
| `TONO` 41 B | 102 → 1 | 125 → 1 |
| `BAHIA` 71 B | 162 → 2 | 202 → 2 |
| `SET` de 16, 103 B | 226 → 2 | 284 → 3 |

**Qué cambia, dicho sin adornos** (Serrano 2, Voronov §2):
- El plazo deja de ser una frontera de µs y pasa a ser «terminar en `N` tics». La fórmula de D3 sobrevive como especificación del `N`; ya no hay un suceso «plazo» en el tiempo.
- `plazos_vencidos` cuenta «no terminó en `N` tics» y `eot_tardios` **es cero por construcción** (no hay EOT asíncrono: lo que el tic encuentra al leer es la verdad de ese instante). R-MJ8 conserva las dos columnas, con esa nota. **La fila del soak del 16-17 de octubre no se transfiere**, ni por el transporte ni por esta semántica.
- El margen real de un mensaje contra su plazo de µs lo mide `plazos_j2` con osciloscopio, no los contadores.
- **No se necesita un reloj de µs ni `DWT_CYCCNT` para el plazo:** la edad se cuenta en tics. La política recibe como reloj `tic × PERIODO_GIRO_US` (exacto y monótono, §2.7).

**El techo de recuperación** de §3 de la spec pasa de `plazo + reinicio + alineación + un giro` (490 µs) a `(N + 2) × periodo + T_REINICIO`: 395 µs para un `NADA` y **520 µs para el `SET`**, con 20 µs de reinicio. Halberg lo simuló con tics de hardware [SIM]: de armado a siguiente trama buena, 284 µs (`NADA`) a **487 µs** (`SET`), y 612 con un tic tarde más de ~24 µs; contra los ~50 ms del módulo son 82× a 103×, y el presupuesto exige ≥ 10×. Dos cifras del papel firmado se propagan: la función de golpe perdido de D6/§3 («3 giros», 490/125 = 3,92) pasa a **5 giros** en el peor caso, y la fórmula de `recuperacion_j2_budget.py` tiene que llevar `N`. Los números de Halberg son de una variante que cierra en el EOT; hay que repetir su simulación sobre esta máquina (§4).

### 2.5 La recuperación (D4)

La pide la política y la ejecuta el nivel 4: el tic emite `PlazoVencido`; el planificador lo pasa a `Ranura::paso`; **la política es la única autoridad sobre «reiniciar»** (`Accion::Reiniciar`) y la máquina de §2.2 no decide nada por su cuenta (Serrano 5, Voronov §4). Los pasos, con la cita del manual donde la hay:

*(No hay nada que silenciar ni que desanclar: `EOTIE` está siempre en cero y las IRQ de SPI y de canal están enmascaradas.)*

1. **Parar los dos canales** (RM0486 §19.4.4, p. 943): `CR.SUSP = 1`; sondear `SR.SUSPF` hasta `T_CANAL`; **`CR.RESET = 1`** (*«resets the FIFO, the channel internal state, the EN bit and the SUSP bit»*). Si un canal no llega a `SUSPF` en `T_CANAL`, **escalar** (D4.2, abajo). `T_CANAL` pasa de 10 a **25 µs, ESTIMADO**: es tiempo de pared, y el tic (hasta 8,5 µs) y el planificador pueden expropiar el sondeo; con 10 µs una expropiación basta para escalar una ranura cuyo canal habría parado.
2. **Resetear el SPI por RCC**, `rcc::disable` y `rcc::enable_and_reset` **en una sola sección crítica** (≤ 1 µs, ESTIMADO): dos secciones separadas dejan un hueco en que el tic podría escribir un periférico sin reloj, y el `CS` del módulo flota entre el reset y el paso 4.
3. **Reescribir `CFG2` y `CFG1`** como los dejó la construcción (D1).
4. **Reprogramar los dos canales por completo:** `FCR`, `LLR`, `TR1`, `TR2`, `TR3`, la dirección del lado periférico (`DAR` del TX, `SAR` del RX) y `CR` con todas las `IE` a cero. Es idempotente: sirve igual tras el `RESET` de un canal (que conserva `TR1-TR3`) que tras el reset del GPDMA1 por RCC (que lo borra todo).
5. **Publicar `ReinicioHecho`** con su marca de tiempo. El tic devuelve la ranura a `Libre` solo si han pasado `T_GAP_REARME` (ESTIMADO 2 µs, el `T_GAP` de la cabecera D8, HUECO); si no, espera un tic más.
6. **Contar:** `plazos_vencidos` ya subió cuando la política recibió `PlazoVencido`; aquí solo se cuenta la recuperación hecha.

**Cotas de los estados de recuperación:** `Vencida` más de 2 tics sin que arranque la recuperación, o `Reiniciando` más de 4, pasan la ranura a `Muerta`: deja de sellar y el IWDG del hub reinicia el chip. Es la red de lo que el planificador o la recuperación no hagan.

**La escalada D4.2** (un canal no responde): `rcc::disable` y `rcc::enable_and_reset::<GPDMA1>` **en una sola sección crítica, y dentro de ella se marcan `canales_sucios` en las seis ranuras** (la marca es atómica con el reset: un tic no puede ver el controlador reseteado y la marca sin poner). El tic salta las ranuras sucias; la recuperación reprograma los doce canales (paso 4 por ranura) antes de limpiarlas. Las ranuras que estaban en vuelo mueren con el reset: se declaran vencidas de una vez, sin esperar su `N`. Se cuenta aparte (`escaladas_gpdma`). Es la parte que más daño hace si el GPDMA1 no es del J2 (R-H3).

### 2.6 Los búferes, el buzón y la secuencia

- **Subida:** doble búfer por ranura en la región no cacheable de R-MJ7. El tic arma el búfer `i`, cierra publicando `i` y arma el `1 − i`. El planificador **copia la subida con `ldm` a un búfer local** y trabaja sobre la copia: un acceso suelto a la región cuesta 84 ciclos y un CRC a byte sobre 128 bytes, ~10 800 (`costes_dma`). Si el planificador no consumió `i` cuando llega el siguiente cierre, se cuenta `subidas_perdidas`.
- **Bajada:** el buzón se **consume al armar**. Tras una recuperación está vacío hasta que el planificador compone otra trama: la trama abortada y su `secuencia` quedan consumidas (D4), no se repiten (B5 de Halberg).
- **Sin bajada fresca,** el tic no arma y cuenta `sin_bajada`. El módulo aguanta 400 giros sin tramas (su ventana de ~50 ms); qué debe salir cuando el planificador se atrasa —un `NADA` de relleno con una `secuencia` que no es del planificador, o nada— es una pregunta de la cabecera (R-C8: un solo escritor), y se deja abierta (§7).
- **La latencia sube un periodo para la subida** (el cierre es en el tic siguiente) y no cambia para la bajada. Hay que comprobarla contra `latencia_mano_budget.py` (§7).

### 2.7 Quién llama a la política, y con qué reloj

El tic **no** llama a `Ranura::paso`: empuja un evento a un anillo de la ranura. El planificador (nivel 3) vacía los anillos y llama a `paso(evento, tic × PERIODO_GIRO_US)`, más un `Evento::Tick` por periodo y ranura activa para deslizar la ventana. Una sola base de tiempo para la política, el plazo y el calendario: el índice de tic. `DWT_CYCCNT` se usa solo para los testigos de §2.8 y para `T_GAP_REARME`.

La identidad (R-MJ6) la publica el planificador en un atómico por ranura; el tic lo lee. Si se retira con la ranura `Armada`, la transferencia termina o vence como cualquier otra y después la ranura deja de armarse.

### 2.8 Los testigos y los contadores

`Calendario` guardaba tres cosas que nadie escribió (Voronov §5): una referencia al plan, un hueco medido desde el fin del trabajo y una sola base de tiempo. Sus sustitutos:

- **Retraso del tic:** al entrar en la ISR se lee `TIM7.CNT` (µs desde el último suceso de actualización) y se guarda el máximo. `tics_tardios` cuenta los que pasan de 10 µs.
- **Tics fusionados:** se mide con `DWT_CYCCNT` el intervalo entre dos entradas; si pasa de 1,5 periodos se cuenta `tics_fusionados`. Un temporizador de hardware funde dos actualizaciones en una pendiente y sin este contador el giro perdido no deja rastro.
- **`atrasos` (enmienda del 16-10) se retira** y lo sustituyen estos dos, que miden CPU y enmascarado; `plazos_vencidos`, `errores_dma`, `sin_bajada` y `subidas_perdidas` miden E/S. Un atraso sigue sin mover `inestable` ni `muda`: los tics tardíos y fusionados tampoco.
- **El sello del IWDG** sube al armar (D5.4); en `Muerta`, no.

### 2.9 Qué desaparece

Las tareas y el `EJECUTOR_J2` (`fw/src/j2_ejecutor.rs`), `embassy_time::Timer` en el camino del J2, los `Transfer` y su `Drop`, **las seis ISR de SPI**, `Turno` y la generación del EOT, `EOTIE` y `NVIC::unpend`, `Calendario` y las enmiendas del 18-09 (`Ticker::reset`, R15) y del 16-10, y el `bind_interrupts!` de embassy sobre los doce canales.

## 3. La CPU

Lo único medido es la cota (`j2_isr`): **1 500 ciclos por giro** con las dos cachés a 800 MHz, un giro por tic en tres corridas (#438). Esta máquina se parece a ella más que el v1: cierra en el tic siguiente comprobando `TCF`, y no tiene la ISR del SPI (185 ciclos por giro) ni el medio ciclo de cada interrupción de EOT. Suma por ranura y giro, con las cachés calientes y la región no cacheable con `ldm` (**ESTIMADO** sobre `costes_bus` y `costes_dma`; Halberg §5.2):

| Mensaje | sin componer la trama | componiéndola (500 ciclos) |
|---|---|---|
| `NADA` 25 B | ~1 060 | ~1 560 |
| `TONO` 41 B | ~1 260 | ~1 760 |
| `BAHIA` 71 B | ~1 550 | ~2 050 |
| `SET` de 16, 103 B | ~1 860 | ~2 360 |

Cada fila lleva armar (~390), el tic (~20), cerrar con la lectura de `SR` y de `TCF` (~260), el anillo (~40), la copia de la subida con `ldm` (96 a 372), el CRC por tabla y la política. Las cifras son de Halberg, cuya suma cierra en una ISR de EOT de 314 ciclos; aquí el cierre está en el tic y la suma sale parecida (±15 ciclos). **Caben los 2 500 con margen si «el J2» no incluye componer la trama (§1, pregunta 1), y caben por poco si la incluye; el planificador real no está escrito ni medido.** Sobre esto:
- La caché fría come el margen: cada línea desalojada por el hilo cuesta 80 ciclos, y con ~158 líneas son +530 / +1 050 / +2 100 ciclos a 25 / 50 / 100 % frío. El banco no la ejerce (su hilo es un `yield_now`).
- La resolución del medidor es ~100 ciclos por ranura, y el ruido entre compilaciones, menos de un 1 % con D-cache.
- Seis `SET` de dieciséis coincidentes: si componer cuesta más de 2,5 a 3 µs por ranura, la sexta pierde un tic de cada dos [SIM]. A 6,25 MHz cada `SET` ocupa más de un periodo por sí mismo (R-H5).
- La cota mide una ranura. El banco tiene tres físicas; SPI3 y SPI6 piden otra función alterna que `Ranura::nueva` no soporta.

## 4. Lo que se prueba

**Host (`core`):** `Transporte` como función pura, todas las filas de §2.2 con sus bordes; una ranura nunca se arma sobre otra `Armada`; los contadores se conservan; la recuperación vuelve a `Libre` o a `Muerta`, nunca se queda; y **la simulación de seis ranuras de Halberg** (`scratchpad\halberg\`, `exp1`-`exp9`) rehecha sobre esta máquina, con la cola de nivel 3 compartida, el desempate, el EOT pendiente al tic, la escalada con vecinas en vuelo y los tics tardíos y fusionados.

**Banco, con esclavo** (en este orden; la 1 y la 2 son de Halberg §9.2 y §9.3; su §9.1, la carrera EOT/DMA, no aplica a este diseño porque no cierra en el EOT):
1. **Cota honesta** (hecho, #438).
2. **Recuperación en placa:** un SPI envenenado a propósito, con `SUSP → SUSPF → RESET`, leyendo `EN` y `BNDT` después; y una escalada forzada con cinco vecinas en vuelo, midiendo cuánto está el `CS` abajo sin reloj y qué hueco ve el módulo.
3. **El transporte completo** (`Transporte` en `core` más el tic y los registros en `fw`) contra el esclavo del banco, a 1 kHz y a 8 kHz con las cachés y la región MPU; con `plazos_vencidos`, `errores_dma`, `sin_bajada`, `tics_tardios` y `tics_fusionados` a cero.
4. **Una fila de `carga_j2.csv`** a ≥ 800 MHz con ese transporte, las cachés del hub y la región de R-MJ7.
5. **El máximo enmascarado:** el tiempo máximo con PRIMASK y con ISR por encima del tic, con `DWT`, en uso real del hub. No se puede hacer hasta que haya un hub; es R-H2.
6. **Seis ranuras reales** (extender `Ranura::nueva` a las otras funciones alternas de SPI3 y SPI6).

## 5. Condiciones

1. **Para firmar el diseño:** las respuestas de §1; las medidas 2 y 3 de §4 limpias; una segunda pasada de la junta sobre §2.2 con la simulación rehecha; y la medida 4 con la definición de «el J2» que Samuel haya elegido.
2. **Para que el código entre en `main`:** las pruebas de host y las medidas 2 y 3; un `carga_j2.csv` con una columna **`transporte`** (hoy no la hay, y la puerta toma el mínimo de cualquier fila a ≥ 800 MHz sin mirar cuál es el transporte, las ranuras ni la antigüedad); y `recuperacion_j2_budget.py` filtrando por ella.
3. **Para fabricar (R-MJ8):** el soak de 24 h con este transporte, a 8 kHz, y la cabecera de `resistencia_j2.csv` con la columna `transporte` (enmienda del §8). La fila del 16-17 de octubre es de otro transporte.

## 6. Censo de la spec: qué se toca y qué no

| Pieza | Estado | Qué |
|---|---|---|
| D1 | igual | |
| D2 | **reescrita** | las esperas son estados; el EOT se lee en el tic; sin `EOTIE`, sin generación ni `Turno`; el orden de arranque, igual con su primer `SPE = 0`; se añade el orden de cierre, que D2 no tenía (v1 lo citaba de D4) |
| D3 | fórmula igual; **vigilancia en tics** | cota, contadores y techo de recuperación (§2.4) |
| D4 | **reescrita** | `RESET` del canal con su cita, `T_CANAL` = 25 µs, secciones críticas, reprogramación (paso 4), escalada con marca atómica; **seis pasos en R-MJ3**, no los de la enmienda del 14-10 (el `RESET` cita la p. 943) |
| D5.1 (1) y (3) | **reescritas** | una máquina por ranura movida por un tic; niveles por interrupción |
| D5.1 (2) (R-C8), (4) (sello, IWDG) | igual | aclarado que la política tiene un solo llamador |
| Enmiendas 18-09 (R15) y 16-10 (`Calendario`) | **derogadas** | §2.8 |
| D6, D7 | igual | la política de `core` no cambia |
| D8 | **enmendada** | el driver deja de ser genérico: lleva el tic y los registros del GPDMA; la cláusula de retiro hacia `embassy_stm32::spi` (D8.2) pierde su sujeto, y con ella la contribución upstream |
| R-MJ2 | **reescrita** | §2.2 |
| R-MJ3 | **seis pasos, otros** | parar con `RESET`, reset del SPI, `CFG`, reprogramar, `ReinicioHecho`, contar |
| R-MJ4 | **constantes nuevas** | `T_CANAL`, `T_GAP_REARME`, cotas de `Vencida` y `Reiniciando`, umbrales de los testigos |
| R-MJ5 | **reescrita** | *«Cada ranura activa tiene su máquina, movida por el tic; ninguna tarea del hilo puede retrasar un giro.»* |
| R-MJ7 | igual, con una nota | la subida se copia con `ldm`; si se elige la forma cacheable, `invalidate` también **antes de armar** el RX |
| R-MJ8 | **columna `transporte`** | y la nota de §2.4 sobre `eot_tardios` |
| §3 (recuperación, golpe perdido) | **recalculada** | §2.4 |
| §5, §8 | **actualizadas** | muere/nace; el guion de la puerta |
| Riesgo 6 | **cerrado a medias** | el `Drop` sin cota desaparece; la escalada sobre canales con estado, no |
| Riesgo 9 | abierto | depende de §1 |
| §10, filas del hub («los ejecutores», supervisor) | **pasan a R-H1 a R-H6** | |

## 7. Lo que sigue abierto

- **Qué entra en «el J2» y qué estatus tiene el 15 %** (§1; Samuel).
- **Qué sale cuando el planificador se atrasa** (§2.6): la cabecera.
- **La latencia de la subida**, un periodo más (§2.6), contra `latencia_mano_budget.py`.
- **R-H1 a R-H6**, del papel del hub.
- **El planificador real,** su coste y su dueño.
- **Los números ESTIMADO:** `T_CANAL`, `T_GAP_REARME`, el reinicio de 20 µs (Halberg estima 1,3 a 3 µs por la suma de accesos), la cota de `Vencida`/`Reiniciando`.
- **Si la subida con retraso de un periodo tiene alguna consecuencia en D7** (las marcas de salud se alimentan de `SubidaOk`/`SubidaMala`).

## 8. Registro de la junta

`S` = Serrano, `H` = Halberg (`B`), `V` = Voronov (§).

| Hallazgo | Resolución en v2 |
|---|---|
| S1, V§1 «el J2» sin definir | **Acta, pregunta 1.** El papel no puede resolverlo |
| S2, H-B4, V§2 plazo y tic | plazo en tics (§2.4); el tic lee el EOT antes de vencer; sin dos relojes; contadores con su semántica dicha; techo recalculado |
| S3, H-B1 cierre sin esperar al DMA | cierre con `EOT ∧ TCF ∧ ¬error`, un periodo después (§2.3); un error del DMA va a D4 |
| S4, H-§3.2 exclusión mutua | tic único escritor del estado; secciones críticas únicas en D4.3 y D4.2; marca atómica; `T_CANAL` = 25 µs |
| S5, V§4 dueño de la política | el planificador es el único llamador; la política es la única autoridad sobre «reiniciar» (§2.5, §2.7) |
| S6, H-B5, V§4 buzón | se consume al armar; vacío tras recuperar; `sin_bajada` (§2.6); el relleno, abierto |
| S7, V§2 estados sin plazo | no hay `Cerrando`; `Vencida` y `Reiniciando` con cota en tics y `Muerta` (§2.2, §2.5) |
| S8, V§5 enmiendas que «desaparecen» | testigos de retraso y de tics fusionados; `T_GAP_REARME` (§2.8, §2.5) |
| S9, H-B2 recuperación sin `RESET` | `RESET` con su cita, reprogramación completa (§2.5) |
| S10, H-§5.2, V§8 suma de CPU | supuestos declarados (§3); D-cache como requisito (R-H4); resolución y ruido |
| S11 cota no auditable | **hecho: #438** (fallos publicados, ciclo comprobado, impresión diferida) |
| S12 opción D | **retirada la afirmación** de imposibilidad por aritmética (EN-PLACA y #436 corregidos); sigue sin medirse una configuración con un solo `Timer` |
| S13, V§8 puertas | columna `transporte` en los CSV y la puerta (§5) |
| S14, S15 censos | §6 |
| H-B3, V§3 dueño del GPDMA | el transporte; IRQ de canal y de SPI enmascaradas; R-H3 |
| H-B6 ISR del EOT | no hay ISR del EOT |
| H-B7 cola compartida | recuperación por debajo del planificador |
| H-§3.4 enmascarado, defmt | R-H2; el banco ya no imprime mientras mide (#438) |
| H-§6 SET a 6,25 MHz | R-H5 (#380) |
| V§1 clausura, censo | R-H6; acta, pregunta 2 |
| V§6 A' = A | A' se retira como opción: es un parámetro de A, y aquí la recuperación es un manejador a término |
| V§7 B y C no son transportes | B y C pasan al acta como cambios de requisito |
| V§7 E extremo de un eje | queda como el siguiente paso del eje; sin datos, sin spike |
| V§8 D8 | §6 |
