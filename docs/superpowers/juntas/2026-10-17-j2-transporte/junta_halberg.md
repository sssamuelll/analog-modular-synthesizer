# Halberg · junta del J2 · 2026-10-17 · papel-v1 (transporte por interrupciones)

Notación. «Comparador» y «cuantizado» son las dos formas del plazo (§2.4 del papel, que las llama P1 y P2). «Nivel N» es prioridad de NVIC (0 = más urgente; el N657 tiene 4 bits). Etiquetas de evidencia: [COD] código con archivo:línea, [RM] RM0486 Rev 4 con página, [SIM] mis simulaciones, [EST] estimado mío o del papel sin fuente. No toqué ningún archivo del repo.

## Veredicto por adelantado

El mecanismo (tic de hardware, EOT por ranura, máquina de estados) es ejecutable. **papel-v1 no lo es tal como está escrito.**
- Tiene dos transiciones que dejan una ranura muerta para siempre sin que ningún contador lo diga (B1, B2).
- Tiene una combinación de IRQ de canal que nadie atiende (B3).
- Tiene una decisión de «vencido» que convierte una sección enmascarada de 46 a 100 µs en seis reinicios de SPI simultáneos (B4).
- La cifra de CPU no incluye el planificador, que es más de la mitad del coste de un giro (§5.2).
- El techo de recuperación de §3 **no** es lo que rompe: 487 µs nominal con cualquiera de los dos plazos, 612 µs con un tic tarde. Contra 50 ms son 103× y 82×.

## 0. La cifra de 1 500: qué mide y qué no

1. **Cuenta giros completados.** `carga_j2.rs:208` calcula `ciclo_us = 5 s · ranuras / Δgiros`. `giros` es `Ranura::giros()` de la política, que solo sube con `GiroOk` (`maestro_j2.rs:371`). El guion convierte `(1000 − hilo_libre)/1000 · ciclo_us · f_cpu / ranuras`. Son ciclos por giro cerrado, no por tic.
2. **El volcado crudo lo confirma.** `scratchpad\carga800isr.txt`, firmware `d33dcac-sucio`: `ciclo_us` = 125 / 124 / 125 y `hilo_libre` = 898 / 921 / 985 permil. Eso es Δgiros ≥ 40 000 en 5 s en las tres pasadas: cada tic cerró un giro. Para una ranura, SPI5 y cachés calientes, el 1 500 mide giros que se completan.
3. **La guarda del banco está ciega para este transporte.**
   - `plazos_vencidos` y `atrasos` salen en 0 por construcción: `publicar_cuentas(N, &g.politica, 0)` en `j2_isr.rs:304`, y nunca se manda `PlazoVencido` a la política.
   - El contador real `g.plazos` solo sale por `fallos()` (`j2_isr.rs:350`) y ningún binario lo llama.
   - El «plazos > 0 ⇒ la medida no vale» de `carga_j2.py::parsea` no puede saltar con `transporte-isr`. El único testigo de los giros es `ciclo_us`.
4. **Qué hace `j2_isr.rs` cuando el giro anterior no acabó (:316-337).** Cuenta `g.plazos`, no arma y sale. Si `tomar()` ya entregó un resultado sin EOT, o `cierra()` falla por TCF, el resultado queda consumido y `en_vuelo` sigue en true: el tic siguiente no encuentra nada, para siempre. No hay plazo ni D4. Solo se vería como `hilo_libre` saturado.
5. **Qué hay dentro de los 1 500.** 1 306 en las dos ISR (1 121 + 185) y 194 que el hilo pierde al volver. Los 1 121 incluyen el cierre del giro anterior, el planificador de juguete (155 + 12 ciclos) y un `Instant::now()` (48). Armar una ranura cuesta **~390-450 ciclos** por los costes de bus medidos, no 1 100.
6. **Es la medida de otro programa.**
   - Cierra en el tic siguiente, ≥ 100 µs después del EOT, y comprueba TCF de los dos canales. El papel cierra en la ISR del EOT sin TCF.
   - El tic va a nivel 2 y el EOT a nivel 1 (`j2_isr.rs:296`). El papel pone los dos en nivel 1.
   - Una ranura, MISO al aire, 25 B a 6,25 MHz. El volcado de `Clocks` (`dma800.txt`) da pclk2 = 100 MHz con el reloj del hub, y pedir 10 MHz da /16.
   - Buffers cacheables sin región MPU.
   - Un hilo que solo hace `yield_now` y nunca desaloja cachés.

## 1. Execution Breakpoints Detected

**B1. El cierre en el EOT descarta la espera del DMA. [ROMPE si pierde la carrera, y no hay guardia]**
- El papel (§1, fila D2) dice que las dos esperas «son dos estados con un plazo». §2.2 tiene un solo estado `Armada` con una sola salida (`Eot`). La ISR del EOT (§2.3) escribe IFCR, `SPE = 0` y `DMAEN = 0` sin leer `SR.TCF` de los canales.
- [RM p. 3449-3450] «When SPI is disabled, RxFIFO is flushed. To prevent losing unread data, the user must ensure that RxFIFO is empty when disabling the SPI». El procedimiento de maestro full-duplex es: esperar EOT, leer todo el RxFIFO, `SPE = 0`.
- [RM p. 3450] «When EOT is set at the end of the transfer and the last data packet is incomplete, then DMA request is activated automatically … to read the rest of data». El RM modela el EOT como anterior al vaciado del RX.
- D5.1 lo evita con `join(tx, rx)` antes de `EsperaEot` (`j2_spi.rs:653-656`). La cota lo evita cerrando 100 µs después.
- La ventana es del mismo orden que la latencia del DMA [EST]. De la señal EOT al `SPE = 0` llegando al SPI hay ~102 ciclos de CPU (127 ns) más propagación. El DMA RX, con hclk1 = 100 MHz según el volcado de `Clocks`, necesita 12-17 ciclos de 10 ns (120-170 ns) sin contención. No se decide con aritmética.
- Si pierde: el canal RX queda con `EN = 1` y `BNDT ≠ 0`. [RM pp. 989-1006] `TR1/TR2/TR3/BR1/SAR/DAR/LLR` «must be written when EN = 0 … read-only when EN = 1». Los armados siguientes no escriben nada, cada giro vence plazo y D4 no repara el canal (B2).

**B2. La recuperación nunca hace `CxCR.RESET`. [ROMPE, determinista]**
- Papel §2.5 paso 2: `CR.SUSP` más sondeo. §1: «Riesgo 6 se cierra por construcción: no hay `Transfer`, ni `Drop`».
- [RM p. 943, §19.4.4] El aborto es SUSP, esperar SUSPF, **RESET**, reprogramar BR1/SAR/DAR, EN. [RM p. 943] «A suspend and resume sequence does not impact the GPDMA_CxCR.EN bit». [RM p. 988] «Writing 0 into this EN bit is ignored».
- Ese RESET lo hacía el `Drop` de embassy (`request_reset`, `gpdma/mod.rs:902-910`; `configure` lo repite en :662-669). El papel borra el `Drop` y con él el RESET.
- Sin RESET el canal queda `EN = 1, SUSP = 1`. El armado siguiente escribe `CR` con `SUSP = 0, EN = 1`, reanuda el bloque viejo, y las escrituras de BR1/SAR/DAR se ignoran.
- §2.5 paso 6 y §2.3 dicen que un reset deja `TR1-TR3/CR` «en valores de reset». [RM p. 988] El RESET de canal conserva la configuración; solo el reset por RCC del GPDMA1 la borra.
- La lista «(TR1, TR2, TR3, CR)» omite el puntero del lado periférico (DAR del canal TX, SAR del RX) y LLR. `Canal::nuevo` los escribe una sola vez (`j2_isr.rs:108-114`).

**B3. Las doce IRQ de canal del GPDMA no tienen dueño en el papel. [ROMPE]**
- `Canal::nuevo` deja `USEIE|DTEIE|SUSPIE` puestos (`j2_isr.rs:115-119`). Mientras la `Ranura` se construya como hoy, las líneas siguen atadas al `dma::InterruptHandler` de embassy, a nivel 1 (`j2_spi.rs:459-460`).
- Ese manejador hace `panic!` ante DTEF, USEF y ULEF (`gpdma/mod.rs:561-581`). Ante SUSPF escribe `ch.cr().write(|_| {})` (:610-613), que pone SUSP = 0, es decir **reanuda el canal**, y no limpia SUSPF.
- El `CR.SUSP` del paso 2 de D4 levanta exactamente esa IRQ, un nivel por encima de la recuperación. El canal se reanuda a espaldas de D4 y `is_running()` (que lee SUSPF) dice «parado».
- Si el papel desata los canales, una IRQ de canal sin handler cae en `DefaultHandler`, un bucle infinito.
- §2.1 no lista estas doce líneas en ninguna fila.

**B4. Desempate por número de IRQ y vencido decidido sin leer el EOT. [ROMPE bajo máscara]**
- [COD] metapac N657: TIM2 = 116, TIM5 = 119, TIM7 = 121, SPI1-6 = 153-158, GPDMA1_CHANNEL0-15 = 84-99, USB1_OTG_HS = 177. A igual nivel gana el menor número.
- Con tic (o comparador) y EOT pendientes, el tic corre primero. §2.2 manda `Armada + Tic + plazo cumplido → Vencida` sin mirar `SR.EOT` ni el resultado guardado.
- D5.1 no tiene este fallo: `TimeoutFuture::poll` mira el futuro interno antes que el temporizador (`embassy-time/src/timer.rs:114-119`).
- **Umbrales [SIM].** Una sección PRIMASK (o una cadena de ISR de nivel ≤ 1) que cubra el EOT hasta el tic o el comparador. Las seis ranuras caen 2-8 µs después de que caiga la primera.

| Mensaje (plazo) | Comparador: 1 falsa / seis | Cuantizado: 1 falsa / seis |
|---|---|---|
| NADA (70 µs) | 46 / 48 µs | 96 / 100 µs |
| TONO 41 B (102) | 62 / 64 | 80 / 84 |
| BAHIA (162) | 92 / 94 | 92 / 100 |
| SET16 (226) | 122 | 124 |

- Con ≥ 126 µs el UIF de TIM7 no cuenta: un tic desaparece y **no hay contador** (`tics_fusionados` no existe).
- Seis falsas son seis resets de SPI por RCC con tramas buenas, seis `plazos_vencidos` en `inestable` y en `resistencia_j2.csv`.

**B5. `Reiniciando → Libre` sin pasar por el planificador. [ROMPE el contrato]**
- Papel §2.2: tras `ReinicioHecho` la ranura vuelve a `Libre`, y el tic toma «del buzón la bajada que dejó el planificador». El buzón conserva la trama que se acaba de abortar.
- [SIM] `armados_con_trama_vieja` = número de recuperaciones (164 de 164). Esa trama repite la `secuencia` abortada.
- Eso contradice D4 («la secuencia de la trama abortada se consumió»), contradice R-C8 (el planificador es el único escritor) y descuadra en uno por recuperación el cruce `perdidas − rechazadas − plazos_vencidos` de §3.3.

**B6. La ISR del EOT: sin lectura de vuelta y sin test de `SR.EOT`. [CONDICIONAL]**
- El papel manda escribir cada registro entero, sin RMW. La ISR actual tiene un `ier().modify` (`j2_spi.rs:931`) cuya lectura drena la escritura posteada de IFCR. Sin ella la línea puede seguir levantada al volver y la ISR reentra, se cuenta un `eot_tardios` falso y se ensucia el cruce de D4.
- La regla «`Armada` + generación vigente ⇒ cerrar» ignora que `EOTIE` cubre también SUSP y TXC. Una IRQ sin EOT cierra a mitad de trama.
- La generación no discrimina nada (enmienda del 18-09; `j2_spi.rs:933-938`): la ISR lee la generación armada en ese instante. Lo único que separa un EOT viejo de uno nuevo es el estado, el orden de `EOTIE` y el `unpend`.

## 2. Runtime Contradictions Across Layers

- §1 dice que las dos esperas de D2 pasan a «dos estados»; §2.2 tiene uno (B1).
- §2.5 y §2.3 dicen que un reset de canal borra TR/CR; el RM dice que no (B2).
- §2.7 define `tics_perdidos` como «sin acabar y todavía en plazo». La tabla §2.2 lo asigna también a `Cerrando + Tic`. Un contador para dos causas (ISR lenta contra planificador lento) no distingue ninguna.
- §2.4 estima el comparador en «~50 ciclos». La sola lectura de `CNT` cuesta 48 (`costes_bus`); más `CCR`, `DIER` y el cierre son ~96.
- §2.1 llama P1/P3 a niveles de NVIC y §2.4 llama P1/P2 a los plazos; en `j2_isr.rs` el tic es «P2». Tres significados del mismo rótulo.
- §3 acierta al decir «sin el planificador», pero el planificador es el 55-60 % del giro (§5.2).
- Spec D2, «el plazo abraza las dos esperas», contra §2.4, donde el plazo cuantizado pasa a ser frontera de detección. Con el cuantizado, `plazos_j2` con osciloscopio ya no ve el plazo.

## 3. Concurrency Failure Risks

### 3.1 Niveles y retrasos

- **Hoy ninguna línea fija el nivel del USB ni de la pantalla.** Solo `muestreo.rs:151` toca un nivel (TIM6 a nivel 0). El driver USB de embassy no llama a `set_priority`, así que queda en el reset del NVIC, nivel 0, **por encima del tic**. Si el papel del hub no lo cambia, el retraso va al revés: el USB expropia al tic y a los EOT.
- **Bloqueo del tic [SIM].** Seis armados seguidos duran 3,50 µs con 450 ciclos por ranura (suma de accesos) y 8,53 µs con 1 121 (la cota). La cifra «~8 µs» del brief es la pesimista. El racimo de seis EOT (360 a 600 ciclos cada uno) suma 2,7 a 4,5 µs, separado del tic por ≥ 14 µs. Peor encadenado tras una máscara: ~13 µs. Una ISR de nivel inferior sufre como máximo 3,5 a 8,5 µs por periodo en régimen.
- **EOT de las otras cinco con una ranura reiniciándose [SIM].** Espera hasta su ISR ≤ 0,09 µs (comparador) y ≤ 0,94 µs (cuantizado). La recuperación está en nivel 3. Lo único que corta a los EOT son dos secciones PRIMASK de `rcc::disable` y `enable_and_reset` (`rcc/mod.rs:427-434`), ~0,6 µs [EST], y el `defmt::error!` de la escalada.
- **Lo que sí se retrasa es el planificador.** De EOT a `Libre`: 29,6 µs contra 15,5 sin cuelgues con el comparador y R = 20 µs. Con el cuantizado, 18,0 contra 15,5.
- **H-1 se cumple en el nivel de ISR y no se cumple en el planificador:** ver B7 y 3.3.
- **R realista de D4 sin escalar.** Suma de accesos de los seis pasos: ~1 000 ciclos ≈ 1,3-3 µs [EST]. El «20 µs» del papel es 7-13× conservador. Las simulaciones brackean con R = 2 y R = 20.

**B7. Planificador y recuperación comparten cola (§2.1: ambos nivel 3). [DEGRADA]**

Tics perdidos por ranuras que no colgaron, 4 semillas × 20 000 tics, 162-194 cuelgues cada una [SIM]:

| Configuración | Tics perdidos por vecinas sanas |
|---|---|
| Comparador, cola compartida | 7, 9, 11, 11 (4-6 % de los cuelgues cuestan un tic a un vecino con SET16) |
| Cuantizado | 0, 0, 0, 0 |
| Comparador con la recuperación por debajo del planificador | 0 |

- El cuantizado lo esconde por fase: sus recuperaciones arrancan unos 4 µs después del tic y acaban antes de la ventana del SET16 (105-125 µs). Es coincidencia de fase, no garantía. Aguanta incluso una tormenta de 2 369 cuelgues sin colaterales, pero se pierde con R ≥ 30 µs, con ≥ 5 recuperaciones en serie o con ISR de nivel 2 largas.

### 3.2 Carreras del tic y el EOT de la misma ranura

- **Generación.** Ver B6.
- **EOT tardío [SIM].** Un EOT que llega plazo + 20 µs después:
  - con el cuantizado se acepta, con 0 vencidas, 0 tardíos y 189,5 µs de hueco visible;
  - con el comparador vence, el SPI se resetea antes de que llegue, el EOT de hardware ya no ocurre y **nunca se cuenta** como `eot_tardios`: 250 µs de hueco.
- **`NVIC::unpend`.** D4 paso 1 hace `ier().modify` (con lectura) y luego `unpend`. El papel dice «`EOTIE = 0` y `unpend`». Sin una lectura en medio, el `unpend` puede correr antes de que la escritura de `IER` llegue al SPI, y una línea que sigue asertada se vuelve a pender.
- **Sello del IWDG al armar.** Sin carrera nueva. Persiste el punto ciego de que una ranura que se rearma para siempre sigue sellando. Si el planificador se muere, el tic no arma y los sellos se paran: reinicio, que es correcto.
- **`Cerrando + Tic`.** No arma y cuesta un periodo. Un EOT que llega antes del tic no basta: el planificador (nivel 3) no puede correr hasta que el tic termine.
- **EOT justo en el tic [SIM].** El tic corre primero (121 < 153-158).
  - Mensajes de ≤ 123 B: el tic ve `Cerrando`.
  - Mensajes de ≥ 124 B: el tic ve `Armada`.
  - En ambos casos no hay falso vencido (plazo ≥ 268 µs), pero la ranura queda en **alternancia ARM/pierde, cadencia a la mitad, de forma persistente**.
  - La ventana útil del EOT es ~121 µs, no 125.
- **GPDMA1 por RCC (D4.2).** `resetear_por_rcc` son dos secciones críticas separadas (`j2_spi.rs:792-795`). Entre `disable` y `enable_and_reset` un tic puede escribir el GPDMA1 con su reloj apagado: ventana de decenas de ns, sin garantía en el RM. Con una sola sección crítica no ocurre; el papel no lo dice.
- **`T_CANAL` es cota de pared.** Un tic o un racimo de EOT de 3,5-8,5 µs en medio del sondeo de 10 µs puede escalar una ranura cuyo canal habría parado.

### 3.3 La escalada D4.2

**Qué pierde cada ranura:**
- Los doce canales: TR1, TR2, TR3, CR (prioridad e IE), LLR, el puntero del lado periférico, BR1 y el estado (EN, SUSP, FIFO).
- SECCFGR, PRIVCFGR y CIDCFGR vuelven a 0. El firmware nunca los promueve (`promote_gpdma1_*` no se llama en `fw/src`), así que es el estado del arranque.
- Los SPI no se resetean: sus `DMAEN` siguen puestos y piden servicio a canales en blanco.
- Todo lo demás que viva en GPDMA1 muere. El esclavo del banco usa CH2/CH3 y el escritor de CV es HUECO (#367).

**Qué ve cada ranura [SIM, ESC-1/3/3d]** (hung en la ranura 2, escalada forzada, cinco vecinas con NADA):

| Plazo | Resultado |
|---|---|
| Cuantizado | La detección cae en el tic, justo cuando las seis acaban de armarse. El reset llega 11-17 µs después de armar las vecinas: **cinco tramas sanas mueren en vuelo**. |
| Cuantizado, efecto visible | CS abajo sin reloj 110 a 190 µs (R = 20, cinco recuperaciones en serie; 110-118 con R = 2). Trama corta rechazada. Luego hueco de **375 µs** (tres periodos) en las seis. |
| Cuantizado, R = 30 µs | Cinco recuperaciones en serie suman 150 µs > 125: la última vecina pierde otro tic y el hueco sube a **500 µs**. |
| Comparador | La detección cae a mitad de periodo, con las vecinas ya `Libre`: **cero tics perdidos** de las otras cinco. |
| Con 5 % de escaladas entre las recuperaciones (cuantizado) | 4-5,5 tics de vecinas muertas por escalada (31, 48, 71, 36 con 7, 9, 13, 9 escaladas). |

**`canales_sucios` es obligatoria y su orden importa [SIM, IDLE-1 a 5, EXP3c]:**
- Con ella, las vecinas ociosas reprograman en el tic y no pierden nada.
- Sin ella (comparador), cinco armados en blanco, seis recuperaciones y 376 µs de hueco en las cinco vecinas.
- Marcarla al terminar la recuperación en vez de al resetear el GPDMA basta, si un tic cae en medio (cuelgue de TONO41, tic a +125 µs, reset a +116,5, fin a +143,6), para repetir ese mismo daño. El papel no fija dónde va la marca.

**Qué rehace quién:**
- Las vecinas que estaban en vuelo: su propio D4, paso 6, en nivel 3.
- Las que estaban `Libre` o `Cerrando`: el tic, en nivel 1, con la marca (+150 ciclos por ranura [EST]).
- Nadie reescribe el puntero periférico (B2) ni cubre el ciclo de vida del canal.

### 3.4 Qué parte de la ISR del tic puede quedar enmascarada

- Lo enmascarable es **el arranque**, no el cuerpo. `critical-section-single-core` usa PRIMASK, **no BASEPRI**: ningún nivel protege de una sección crítica.
- Fuentes y duraciones:
  - `Timer::after` en el hilo: `schedule_wake` (`gp16.rs:349-360`) vale 1 457 ciclos ≈ 1,8 µs por llamada (`perfil_pc`).
  - `rcc::*`: ~0,1-0,5 µs por sección.
  - `defmt-rtt` 1.3.0: `acquire()` toma la sección crítica y la mantiene toda la trama (`lib.rs:165-188`). Con la sonda conectada, probe-rs pone RTT en bloqueante, y con el buffer lleno `blocking_write` gira **dentro de PRIMASK sin cota** (`channel.rs:29-62`). Una trama normal pesa 0,3-1 µs.
  - La sonda: arranca el binario con PRIMASK = 1 (lo baja `usb::iniciar`). Parar el núcleo congela todo.

Consecuencias de un tic que llega tarde L µs [SIM]:

| L | Efecto |
|---|---|
| ≤ 2 µs | Ninguno. |
| 5-10 µs | La ranura con SET16 pierde el tic (ver abajo). |
| 46-62 µs (comparador) / 80-100 µs (cuantizado) | Seis recuperaciones falsas en las ranuras de mensajes cortos. |
| ≥ 126 µs | Tic fusionado sin rastro. |

- **SET16.** Su holgura en la peor ranura es 7,6-16,6 µs con 450 ciclos por armado y 2,2-11,2 µs con 1 121, según el planificador (10-1 µs).
- **ISR periódica sobre el tic de D µs** (nivel 0, 7 994 tics): con una ranura de SET16 permanente, D = 2 y 5 no pierden nada; D = 10 pierde 9 %, D = 20 el 12,8 %, D = 30 el 16,8 %. Con todas TONO41, D = 60 pierde 5,6 %.
- **Rachas de nivel 2 de D µs cada ~500 µs** (inanición del planificador, nivel 3): D = 20 → el SET16 pierde el 2,8 %; D = 60 → 2,1-2,9 % en todas; D = 100 → 10-13 %; D = 150 → 22-24 %.
- **Con el cuantizado y un tic de armado tarde más de ~24 µs**, el techo de SET16 salta de 487 a 612 µs. Eso es el 620 del papel: una cota válida bajo ese retraso, no el caso nominal.
- **Techo de recuperación nominal [SIM]** (R = 20 µs, c_arm 1 121 ciclos), de armado a siguiente trama buena:

| Mensaje | Comparador | Cuantizado |
|---|---|---|
| NADA | 159 µs | 284 µs |
| EVENTO | 148 | 273 |
| TONO41 | 300 | 300 |
| BAHIA | 330 | 455 |
| SET16 | **487** | **487** |

El cuantizado cuesta hasta un periodo de más en mensajes cortos, pero esos son los de plazo corto: el techo lo fijan los largos y ahí es idéntico. Hueco máximo que ve el módulo: 578 µs. Con R = 2: 357 y 482 µs.

## 4. Context Integrity Violations

- **Ciclo de vida del canal DMA fuera de la máquina.** `EN`, `SUSP` y `BNDT` determinan si el armado tiene algún efecto (los registros son solo lectura con `EN = 1`). La máquina de §2.2 no tiene un estado para eso (B1, B2).
- **Buzón con trama vieja tras recuperación** (B5).
- **`canales_sucios` es un flag por ranura.** Se marca en un bucle que un tic puede partir por la mitad; en `fw` no existe todavía.
- **Dos relojes sin conversión declarada.** `t_arm` con `DWT_CYCCNT` (32 bits, da la vuelta a 5,37 s a 800 MHz) contra `ahora_us` de la política en `u64` de `Instant`. Una parada de más de 5,37 s del tic da `ahora − t_arm` ambiguo.
- **R-MJ7.** La forma (ii) exige invalidar también antes de armar el RX: un `invalidate` solo antes de leer deja líneas sucias que pueden reescribir el buffer durante el DMA. La forma (i) cuesta de 96 (25 B) a 372 (128 B) ciclos con `ldm` y **~84 por palabra** con lectura suelta; una CRC byte a byte sobre un SET16 no cacheable son ~8 700 ciclos [`costes_dma`, scratchpad].
- **Contadores.** El cuantizado cambia el significado de `plazos_vencidos` (acepta EOT tarde). Los 44,7 M de transferencias y las 24 h a 1 kHz del transporte actual no transfieren esa fila, como ya dice el papel. Además `tics_perdidos` mezcla dos causas y no cuenta los tics fusionados.

## 5. Orchestration Failure Modes

### 5.1 Paradas y bucles

- **Ranura muerta permanente** si el RX pierde la carrera de B1, o por la omisión de B2.
- **Parada permanente de la cota** descrita en §0.4.
- **`DefaultHandler`** si una IRQ de canal queda sin handler.
- **defmt bloqueante dentro de PRIMASK** con la sonda parada: congela el núcleo hasta que se vacíe el buffer; luego, seis recuperaciones falsas por B4.
- **Tormenta correlacionada** (escalada, glitch de reloj): 6 × R ocupa casi todo el nivel 3. La ranura sigue «girando» solo en el sentido de que sella al armar.

### 5.2 CPU: lo que cabe y lo que no (suma de abajo arriba, 800 MHz, cachés calientes, MPU no cacheable con `ldm`) [EST sobre `costes_bus` y `costes_dma`]

Por ranura y giro: armar ~393, tic fijo 17, ISR del EOT 202 (314 con TCF y lectura), planificador (leer subida + CRC por tabla + política + componer).

| Mensaje | componer = 500 ciclos | = 1 000 | = 2 000 |
|---|---|---|---|
| NADA 25 B | 1 563 (0,63×) | 2 063 (0,83×) | 3 063 (1,23×) |
| TONO 41 B | 1 764 | 2 264 | 3 264 |
| BAHIA 71 B | 2 052 | 2 552 | 3 552 |
| SET16 103 B | 2 357 | 2 857 | 3 857 |

- **Con el planificador en la cuenta, los 2 500 caben solo si juzgar y componer cuesta ≲ 1 000 ciclos por ranura y giro y las cachés están calientes.** El planificador no está escrito ni medido.
- **Caché fría.** Si el hilo (pantalla, USB) desaloja el camino del J2 entre tics, cada línea fría cuesta 80 ciclos (`costes_bus`). Con ~158 líneas, a 25 / 50 / 100 % frío son **+527 / +1 053 / +2 107 ciclos por giro**. El banco no lo ejerce.
- **Comparador:** ~96 ciclos por giro, no ~50.
- **Seis SET16 a la vez** (calendarios de refresco de SET coincidentes, un hueco del planificador): si el planificador cuesta más de **2,5-3 µs** por ranura, la sexta ranura pierde **un tic de cada dos, de forma persistente**. Se evita con 1 a 2,5 µs.
- **Consistencia con la cota.** Armar + cerrar + juguete + `now()` ≈ 1 050-1 150, que es el 1 121 medido.

### 5.3 Trazabilidad

- Un contador, `tics_perdidos`, para ISR lenta y planificador lento.
- Un tic fusionado no deja rastro.
- `eot_tardios` falso con la ISR sin lectura (B6).
- `plazos_vencidos` cambia de semántica con el cuantizado.
- El rótulo P1/P2/P3 con tres sentidos.
- El guion de CPU no puede ver un fallo del transporte ISR (§0.3).

## 6. Universality Collapse Points

- **Una ranura de seis.** Las ranuras 2 y 3 son relleno al aire. SPI3 y SPI6 piden otra función alterna que `Ranura::nueva` no soporta (brief §3.3.4). Nada se ha medido con seis SPI, 12 canales y los seis EOT activos.
- **El reloj del enlace decide el cálculo de cadencia.** Con 8 MHz, SET16 dura 103 µs (holgura 22). Con el kernel de 100 MHz del reloj del hub, pedir 10 MHz da /16 = **6,25 MHz** y SET16 dura **131,8 µs > 125 µs**: pierde el siguiente tic por construcción. A 12,5 MHz son 59 µs de holgura; a 16, 73. «Un mensaje normal (≤ 103 µs) no puede provocarlo» (§2.7) es falso a 6,25 MHz y frágil a 8 (#380 abierto).
- **Dos ranuras USART** fuera (riesgo 7). El esclavo nunca corrió contra la cota.
- **Opción C (4 kHz) [SIM].**
  - Umbral de máscara del cuantizado para NADA: de 96 a **224 µs**; el del comparador no cambia (48), porque depende del plazo y no del periodo.
  - Holgura de SET16: 22 a 147 µs; seis SET16 coincidentes dejan de ser un problema.
  - Relaja todas las ventanas de cadencia.

## 7. Simulaciones: parámetros y de dónde salen

Motor de eventos propio, un núcleo con prioridades de NVIC, secciones PRIMASK y las seis ranuras del papel (§2.2). Código en `scratchpad\halberg\` (`motor.py`, `harness.py`, `exp1.py` a `exp9.py`). `autocheck.py` pasa: régimen sin carga con 125,000 µs exactos, conservación de contadores, geometría de un cuelgue calculada a mano, desempate de IRQ y el falso vencido de la prueba de máscaras. `salida.txt` es la salida completa.

| Parámetro | Valor | Fuente |
|---|---|---|
| f_cpu, periodo | 800,1 MHz, 125 µs | EN-PLACA; `maestro_j2.rs` |
| Mensajes (bytes) | NADA 25, EVENTO 14, TONO 41, BAHIA 71, SET16 103 | cabecera §4 |
| f_sck | 8 MHz (spec D3, nota 19-09); 6,25 MHz como sensibilidad | `mbr_y_f_sck` con el kernel de 100 MHz (`dma800.txt`) |
| Plazo | 2·t_nominal + 20 µs: 70 / 48 / 102 / 162 / 226 | D3; `plazo_us` |
| Armar una ranura | 450 ciclos (suma de accesos) y 1 121 (la cota) | `costes_bus`, `j2_isr.rs`, `perfil800.txt` [EST] |
| ISR del EOT con cierre | 360 y 600 ciclos | 185 medidos + cierre [EST] |
| Planificador | 3 µs por ranura (barrido 1-10) | HUECO |
| Recuperación R | 20 µs (papel); 2 µs (suma de accesos); 30 | spec §3; D4 |
| `T_CANAL` | 10 µs | `j2_spi.rs:105` |
| Dos secciones RCC | 0,6 µs | `rcc/mod.rs:427-434` [EST] |
| Números de IRQ | TIM2 116, TIM5 119, TIM7 121, SPI 153-158 | metapac del N657 |
| Mezcla de mensajes | NADA 50 %, TONO 38 %, EVENTO 5 %, BAHIA 2 %, SET16 5 % | [EST] cargada a propósito |
| Tasa de cuelgue | 1,5e-3 por armado | ~10^4× la tasa de campo: expone mecanismos, no predice |

- **Límites del modelo:** un solo núcleo, sin contención de bus ni efectos de caché, PRIMASK solo desde el hilo, un cuelgue es «ningún EOT jamás».
- **No simulado:** la carrera EOT/DMA (B1), porque no hay datos de latencia. Se cierra con una medida (§9).

## 8. Las opciones, desde la ejecución real

- **A.** No sobrevive como v1: B1-B6 son transiciones, no parámetros. Cerrada la ruta normal y la recuperación, el mecanismo es el único que cabe en 2 500 en papel (1,6-2,4 k en caliente con planificador ≤ 1 000 ciclos). Sin evidencia: el 1 500 es una cota de otro programa. Sobrevive a carga solo con tres condiciones del hub que el papel no escribe: nivel del USB/pantalla, máximo enmascarado y planificador acotado.
- **A'.** Hereda todos los puntos de la ruta normal (B1, B3, B4, B6). Resuelve B7 (la recuperación sale de la cola del planificador). Añade un traspaso ISR→tarea y un segundo modelo por ranura. Si la tarea vive en el hilo, el techo depende de la pantalla: 15 ms de retención (H-9) dan 50/15 = 3,3× < 10×. Solo gana si la tarea corre en un ejecutor de interrupción por encima del hilo.
- **B.** Sobrevive a fallos: el `join` antes del EOT, el sondeo con el futuro primero, el `Drop` que resetea el canal y las tareas independientes son lo que A tiene que reconstruir. Tiene 44,7 M de transferencias y 24 h, a 1 kHz, sin ejercer D4. Corre; no cumple el límite por 3,2×. Los 8 000 ciclos son de una ranura con cachés calientes y sin MPU ni planificador; con seis, MPU y caché fría son más de la mitad de un núcleo.
- **C.** Sobrevive a la carga mejor que ninguna (§6): ventanas ×2, SET16 con 147 µs de holgura, umbral de máscara 224 µs. Por sí sola deja el 24 % (1,6× el límite). Toca la cabecera.
- **D.** El piso por aritmética es 3 600-4 400 ciclos: mi cuenta independiente (tarea ~900, maquinaria ~1 450, ISR del SPI 244, resto ~1 000) da ~3 600. No cumple.
- **E.** Sin un solo dato. No hay forma de juzgar el hueco `SPE → CSTART ≥ 1 T_SCK` anclado por lectura que impone D2 dentro de una lista, ni cómo se aborta un canal en medio de una lista. Un spike de un día (una lista de 3 ítems, un analizador) decide si deja de ser una hipótesis. Hoy no es candidata.

**Ninguna cumple a la vez el límite y la evidencia.** B tiene la evidencia y no el límite; A tiene el límite en papel y no la ejecutabilidad de v1 ni evidencia. No falta una opción de diseño: faltan tres medidas.

## 9. Evidencia que cambiaría el veredicto (orden de coste y poder)

1. **Carrera EOT/DMA.** En la ISR del SPI de la cota, leer `RX.SR.TCF` y `RXPLVL/RXWNE` al entrar, durante ≥ 1e8 giros con USB y pantalla. Si alguna vez TCF = 0, el cierre en el EOT no es ejecutable sin esa espera. Si siempre 1, la ventana queda acotada, no cerrada.
2. **Cota honesta.** Hacer que `carga_j2` con `transporte-isr` imprima `g.plazos` y `errores_dma` y falle si ≠ 0.
3. **Recuperación en placa.** SPI envenenado con `CxCR.RESET`, leyendo `EN/BNDT` después; y una escalada forzada con cinco vecinas en vuelo, midiendo CS abajo y hueco.
4. **Presupuesto de enmascarado del hub.** Máximo tiempo de PRIMASK y de ISR por encima del tic, con DWT, en horas de uso real. Los umbrales de este informe: ≤ 5-10 µs con SET16; 46-62 µs (comparador) / 80-100 µs (cuantizado) para falsos vencidos.
5. **Una fila a ≥ 800 MHz** con seis SPI, planificador real, MPU, cierre en el EOT, un hilo que desaloje cachés, y `giros_en_5s` y `tics_perdidos` impresos.
6. **El host test del papel §4,** con cola de nivel 3 compartida, desempate por IRQ, EOT pendiente al tic y escalada con vecinas en vuelo.
7. **Soak a 8 kHz** (no 1 kHz) con D4 ejercida.

## 10. Execution Feasibility Verdict

papel-v1, tal como está escrito: **no ejecutable.** B1, B2 y B3 paran o corrompen una ranura sin contador. B4 convierte una sección enmascarada de 46 a 100 µs en seis resets de SPI y una de 126 en un tic perdido sin rastro. B5 viola R-C8 en cada recuperación. Los 2 500 dependen de un planificador que no existe y de una caché que el banco no ejerce.

Lo que sí aguanta: el techo de recuperación (487 / 612 µs, 82-103×), el cumplimiento de H-1 para cuelgues independientes con el plazo cuantizado, y la cota como medida de coste de un giro en caliente.

El plazo cuantizado gana al comparador en ejecución (el doble de tolerancia a máscaras, sin colaterales con la cola compartida). Su coste es que la escalada cae en la peor fase y que cambia la semántica de los contadores.

No firmar v1. Firmar cualquier variante sin las medidas 1 a 3 de §9 es firmar una ranura que puede morir en silencio.

**La realidad rechaza este diseño tal como está escrito. La ejecución ha hablado.**

## Archivos

- Simulación: `C:\Users\simon\AppData\Local\Temp\claude\D--Desktop-projects-sam17\97597003-c1ef-4ca9-97e1-b0199192ff5f\scratchpad\halberg\` (`motor.py`, `harness.py`, `exp1.py` … `exp9.py`, `autocheck.py`, `todo.sh`, `salida.txt`).
- Medidas crudas usadas, del scratchpad de la sesión: `...\scratchpad\carga800isr.txt`, `carga800.txt`, `perfil800.txt`, `costes800.txt`, `dma800.txt`.
- Repo, solo lectura: `D:\Desktop\projects\sam17\.claude\worktrees\banco2\` (`software\nucleo\fw\src\j2_isr.rs`, `j2_spi.rs`, `j2_ejecutor.rs`, `software\nucleo\core\src\maestro_j2.rs`, `software\nucleo\fw\carga_j2.py`, `src\bin\carga_j2.rs`, `EN-PLACA.md`).
- RM0486 Rev 4: `D:\Desktop\projects\sam17\docs\reference\datasheets\stm32n6-rm0486-rev4.pdf`.
- embassy (rev `697ec64`): `C:\Users\simon\.cargo\git\checkouts\embassy-21ab002d3f42f557\697ec64\`.
- defmt-rtt 1.3.0: `C:\Users\simon\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\defmt-rtt-1.3.0\`.
