# Brief de junta — 2026-10-17 — ¿Con qué transporte cabe el J2 en su reparto de CPU?

## 1. La pregunta

El 2026-10-16 Samuel firmó el reparto de CPU del J2 (*«firmamos el reparto de CPU del J2»*): el J2 del hub —seis ranuras a 8 kHz, **con sus ISR, el despacho del ejecutor y los DMA**— gasta como máximo el **15 % de un núcleo del N657 a 800 MHz**, o sea **2 500 ciclos por giro**.

El 2026-10-17 se midió en la NUCLEO-N657X0-Q, a 800,1 MHz y con las dos cachés, lo que cuesta hoy el transporte firmado en D5.1 (una tarea por ranura en un `InterruptExecutor`): **8 000 ciclos por giro, 3,2 veces el límite**, y no baja al sumar ranuras (8 167 con tres). Seis ranuras a 8 kHz serían el 48 % de un núcleo. El mismo giro hecho por interrupciones, sin ejecutor ni futuros, mide **1 500**, pero esa cifra es una cota inferior: le faltan el plazo, el reinicio y el planificador reales.

La junta contesta tres cosas, en este orden:

1. **¿Se puede llegar a 2 500 con D5.1 tal como está firmada**, sin cambiar de transporte? La evidencia de §3 dice que no. Se pide romper ese argumento, no darlo por bueno.
2. **Si no se puede: ¿cuál es la forma correcta de salir?** Las opciones de §5 (A, A', B, C, D, E) o una que falte. Y, para la que se elija, qué de D2-D5.4, D7 y las reglas R-MJ sobrevive tal cual, qué cambia, y qué se rompe sin que nadie lo vea.
3. **¿Qué evidencia hay que tener en la mano antes de que Samuel firme el cambio**, y en qué orden se consigue? La fila de 24 h del 16-17 de octubre valió para el transporte de D5.1; si el transporte cambia, esa fila no se transfiere.

## 2. Lo que está firmado y lo que arrastra

- Spec `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`, firmada el 2026-09-10; D5.1 reescrita por la junta del 11-09 (V-4, V-5, V-6, S-7, S-8, H-1, H-2, H-6, H-9) y enmendada el 18-09 (ruling R15, `Ticker::reset`) y el 16-10 (el calendario, el reparto de CPU).
- **D5.1, lo que se firmó y por qué:**
  1. *Seis tareas, una por ranura*, cada una con su plazo (D3), su reinicio (D4) y su máquina (D7). En serie no caben: seis `NADA` de 25 bytes al piso son 120 µs más seis `T_GAP`, 132 µs en un giro de 125 (S-8). Los seis periféricos y sus doce canales de DMA corren en paralelo por hardware; un plazo vencido en una ranura no retrasa a las otras cinco (H-1).
  2. *El planificador es el único escritor del enlace* (R-C8). Las tareas son el transporte, no deciden nada del protocolo.
  3. *Un `InterruptExecutor` propio* por encima del de hilo: una tarea de pantalla que retenga la CPU 15 ms no retrasa un giro del J2 (H-9).
  4. *El IWDG es del hub*: el J2 aporta un sello por ranura activa, escrito **al armar** (no al completar).
- **Lo que D2 exige del transporte, sea cual sea:** el orden de arranque (`SPE = 0 → TXTFC → TSIZE → RXDMAEN → canales de DMA armados → TXDMAEN → SPE = 1 → leer CR1 → esperar ≥ 1 T_SCK → EOTC → EOTIE → CSTART`); una **generación** por transferencia y el `EOT` tardío descartado y contado (`eot_tardios`); el resultado guardado se borra al armar; el SPI apagado entre transferencias; `NVIC::unpend` tras silenciar la ISR en D4.
- **D3:** el plazo es por mensaje, `2 × t_nominal + 20 µs`, y llega a 220 µs en la cota (226 µs para el `SET` de dieciséis a 8 MHz, declarado y no cumplido, #380). Es **mayor que el periodo de 125 µs**.
- **D4 (enmienda del 14-10):** seis pasos —silenciar la ISR, soltar el DMA con cota `T_CANAL`, **reset del SPI por RCC**, reescribir `CFG2`/`CFG1`, desanclar la ISR, contar—. La escalada D4.2, si un canal del GPDMA no para, **resetea el GPDMA1 entero por RCC**, o sea las seis ranuras.
- **D7 y la política de `core`:** `Ranura::paso(Evento, ahora_us)` es puro y está probado en el host (`software/nucleo/core/src/maestro_j2.rs`): salud, `inestable`, `muda`, ventana deslizante, `Turno` (generación), `Calendario` (enmienda del 16-10, hueco de un periodo y `atrasos`).
- **R-MJ5:** *«Cada ranura activa tiene su tarea, y las seis viven en el ejecutor del J2»*. **R-MJ2:** ninguna espera sin cota; las dos esperas de la transferencia son futuros bajo plazo. **R-MJ7:** los búferes de DMA en memoria no cacheable o se invalidan antes de leerse, una de las dos, dicha en el plan. **R-MJ8:** la fila de `resistencia_j2.csv` es puerta de fabricación.
- **La evidencia que ya existe sobre el transporte actual** (con el driver de embassy y el `EJECUTOR_J2`): el barrido del retardo, seis puntos y 44 681 083 transferencias sin un fallo (14-10); el soak de 24 h, 86 399 999 giros a **1 kHz** sin un fallo (16-17 de octubre, fila en `resistencia_j2.csv`); `plazos_j2` (osciloscopio) sin hacer. Ninguna ejerció D4 en el camino normal: el soak tuvo cero plazos vencidos.
- **Lo que depende del transporte actual:** `fw/src/j2_ejecutor.rs` (las tareas), `fw/src/j2_spi.rs` (el driver sobre los `Transfer` de embassy), los binarios `resistencia_j2`, `barrido_retardo`, `plazos_j2`, `control_positivo`, y las puertas que leen sus filas.

## 3. La evidencia, medida el 17-10 en la NUCLEO-N657X0-Q

Todo está en `software/nucleo/fw/EN-PLACA.md` (sección `carga_j2`) y en el PR #435. Ciclos por giro, **J2 entero** (lo que el hilo no usa en un ciclo, que lleva las ISR, el DMA, el reloj de embassy y el despacho), a 800,1 MHz y 125 µs de periodo:

| transporte | ranuras | sin caché | I-cache | I-cache + D-cache, sin región MPU |
|---|---|---|---|---|
| ejecutor (D5.1) | 1 | 82 435 | 57 900 | **8 000** |
| ejecutor | 3 | 70 063 | 49 048 | **8 167** |
| ISR sin ejecutor (`j2_isr`) | 1 | 10 200 | 7 837 | **1 500** |

A 64 MHz y 1 kHz, el transporte actual cuesta 20 160 (sin cachés) y 16 112 (I-cache) ciclos por giro.

### 3.1 En qué se va
- De los 8 000 (una ranura, con cachés): el manejador del ejecutor son 5 810, de los cuales **2 706 son código de la tarea** (previo 333, armado 1 479, cierre 549, posterior 345) y 3 104 la maquinaria de futuros y el despacho; la ISR del SPI, 244; el resto, ~1 950, no cae en esos dos manejadores. **Lo que no es código de la tarea son 5 300 ciclos: más del doble del límite.**
- Perfil por función a 800 MHz con cachés (`perfil_pc`, 6 278 ciclos por giro en ISR): `TaskStorage::poll` 2 065, `_embassy_time_schedule_wake` 1 457, driver del GPDMA (`is_running`, `drop`, `configure`, `on_irq`, `start`) 1 281, waker + `Timer::poll` + `poll` de `&mut F` + entrada del ejecutor 971, `SPI5` 195. Quitar por completo el reloj de embassy y la maquinaria de wakers y ejecutor (2 428) deja unos 3 850.
- **No baja con más ranuras:** cada ranura espera en su propio `Timer` y registra su propio waker; lo que se reparte entre ranuras es casi nada.

### 3.2 Por qué: accesos, no instrucciones
`costes_bus` (ciclos por acceso): a 800 MHz una lectura de un registro de periférico cuesta **32 a 48** (12 a 16 a 64 MHz); una lectura de SRAM sin D-cache, **80** (26 a 64 MHz), y con ella 1,1. Las escrituras seguidas se acumulan en el búfer de escritura (8 a 16 ciclos por acceso al SPI y al GPDMA a 800 MHz). Un giro del transporte actual hace del orden de un centenar de accesos. La D-cache es lo que decide casi todo: sin ella son 58 000.

### 3.3 Lo que las cifras NO incluyen (HUECOS que la junta debe tener a la vista)
1. **La región MPU de los búferes del DMA (R-MJ7).** La pasada con D-cache va **sin** ella: los búferes están en memoria cacheable y el DMA y la CPU no son coherentes. Con la región (no cacheable), cada lectura del búfer de subida cuesta ~80 ciclos por palabra; con mantenimiento por dirección, unas decenas por línea. **No medido.** Es lo que impide anotar una fila a 800 MHz en `carga_j2.csv`.
2. **El planificador real.** El banco usa dos funciones de juguete (`bajada_del_banco`, `juez_del_banco`: 155 y ~12 ciclos). El planificador de verdad compone la trama (eventos, `SET`, `BAHIA`, secuencia) y verifica el CRC del sobre de la subida sobre 25 a 103 bytes. **No está medido y no está escrito.** Si es parte del «J2» del límite firmado es una pregunta de la junta (§6).
3. **El esclavo.** Todas las medidas son del maestro solo, con el MISO al aire; el esclavo en el mismo ejecutor lo mata todo (ver la enmienda del 16-10).
4. **La cadencia real de seis ranuras.** Hay dos ranuras de relleno (SPI1, SPI2) además de la ranura 0; no hay seis. SPI3 y SPI6 piden otra función alterna que `Ranura::nueva` no soporta.
5. **El censo de CPU del hub no existe.** El 15 % es la primera fila de un libro que está por escribir (`carga_motor_budget.py` es del motor). Pantalla, USB, MIDI y escritor de CV no tienen reparto.
6. **La pila en DTCM** no se midió.
7. **El mismo binario repite a ±1 ciclo; entre compilaciones distintas del código varía hasta un 10 %** (el 17-10 el manejador del ejecutor pasó de 19 065 a 17 416 sin cambiar la lógica, por la colocación del código en AXISRAM).

### 3.4 Dos errores de medida que se cazaron y cuyo origen hay que tener presente
- El medidor de CPU libre del hilo se calibraba una vez, sin cachés; con la I-cache el hilo da más vueltas por sí solo y el J2 salía de menos (7 104 de total contra 14 011 en el manejador del ejecutor). Desde #435 hay una base por estado y el guion invalida una pasada cuyo total sale menor que su parte. La fila de I-cache del 16-10 (14 752) se retiró.
- `SAM17_GIT` no se recalculaba al editar el código sin mover `HEAD`. Arreglado en #435.

## 4. La cota por interrupciones (`j2_isr`): qué hace y qué le falta

`software/nucleo/fw/src/j2_isr.rs` (PR #435, detrás de la feature `transporte-isr`, solo ranura 0, solo para el banco):

- **Un temporizador (`TIM7`, `P2`)** marca el periodo. Su ISR cierra el giro anterior —lee `SR` de los dos canales del GPDMA, borra `TCF`, `SPE = 0`, `CFG1` sin `DMAEN`, el juez, los eventos de la política, las cuentas— y arma el siguiente.
- **La ISR del SPI (`P1`)** es la de siempre: guarda el `EOT` en el `Turno` de la ranura. Nadie la espera.
- **Los dos canales del GPDMA se programan una vez** (`TR1`, `TR2`, `TR3`, `LLR`, `CR`); por giro solo se escriben `BR1`, la dirección de memoria y `CR.EN`. Sin `TCIE`.
- **Cada registro se escribe entero, con el valor ya calculado**, sin leer-modificar-escribir.
- Mide **1 121 ciclos** en la ISR del tic y 185 en la del SPI, y **1 500** por el medidor del hilo (el J2 entero).

**Lo que NO hace** (y por eso es una cota inferior): el plazo (D3: si el giro anterior no acabó, solo lo cuenta y no arma), el reinicio (D4), la generación y el `EOT` tardío (D2 regla 1), el calendario, el sello del IWDG por ranura (sí lo incrementa), el planificador real, la región MPU, ni las seis ranuras. **No se ha corrido contra el esclavo.**

**Estimación de lo que le falta, ESTIMADO y sin fuente:** el plazo exacto por ranura con un comparador (una escritura al armar y una al cerrar: ~50 ciclos); la generación y el descarte del `EOT` tardío (decenas); la región MPU o el mantenimiento por dirección (100 a 600). Con eso, **1 700 a 2 200 ciclos por giro, sin el planificador**, o sea cerca del límite, no holgado. El planificador real puede romperlo.

## 5. Las opciones

- **A. Transporte por interrupciones.** Una máquina de estados por ranura (`Libre → Armada → Cerrando → Libre`, y `Vencida → Reiniciando`) movida por un tic periódico y por el `EOT` de cada SPI; la política, el planificador y la recuperación a un nivel más bajo; sin `Transfer`, ni `Timer`, ni wakers en el camino normal. Cambia D5.1 (1 y 3), R-MJ5 y la forma de D2 («las esperas son futuros»); `Calendario` deja de existir (el tic de hardware no recupera tics perdidos); el `Drop` del GPDMA sin cota (riesgo 6) deja de existir porque no hay `Transfer`. **Costo:** código nuevo en la parte más delicada del driver —el barrido del 14-10 cazó tres defectos del driver propio en registros—, y **hay que repetir el barrido y el soak con el transporte nuevo**.
- **A'. Híbrido:** el camino normal por interrupciones, y la recuperación (D4), la salud (D7) y lo raro en una tarea de baja prioridad con `Timer`. Menos código a mano que A, la misma cota en el giro normal, y D4 sigue siendo un futuro. El costo es que hay dos modelos de ejecución en una ranura.
- **B. Subir el límite y quedarse con D5.1 como está.** 8 000 por giro son el 48 % de un núcleo con seis ranuras. **Lo que tiene a favor:** el transporte actual ya pasó 44,7 millones de transferencias y 24 h; no hay código nuevo en lo delicado; es el límite el que es de partida —la primera fila de un censo que no existe— y no una necesidad medida. **Lo que tiene en contra:** deja el hilo (pantalla, USB, MIDI, escritor de CV, supervisor) con la mitad de un núcleo, sin censo que diga si basta, y con el planificador real todavía sin contar.
- **C. Bajar la cadencia o las ranuras.** A 4 kHz, seis ranuras con 8 000 ciclos por giro siguen en el 24 %. Toca la cabecera (la cadencia de 8 kHz es de la cabecera del J2) y la latencia de la mano.
- **D. Optimizar el camino de embassy** (hoist de `Instant::now()`, `plazo_us` en `u32`, un solo `Timer` para las seis, un driver propio de DMA sin `Transfer`). **La aritmética lo descarta:** quitando el reloj de embassy y la maquinaria de wakers y ejecutor quedan 3 850; con un driver de DMA propio y el código de las tareas más magro, 3 900 a 4 400 (ESTIMADO, de sumar las partes del perfil). El piso está por encima de 2 500 antes de contar el planificador. Se incluye para que la junta lo rompa.
- **E. Que el hardware haga el giro.** Un canal del GPDMA en modo lista enlazada, disparado por un temporizador, escribe `CR1` del SPI y cuanto haga falta, y la CPU solo prepara la bajada y lee la subida. Costo de CPU mínimo; el riesgo de D2 (el orden de cinco o seis escrituras con un retardo de ≥ 1 `T_SCK` entre dos de ellas) y de D4 (recuperar un SPI y un canal que ejecutan una lista) es alto. **No explorada.** Se incluye para que la junta diga si merece un spike.

## 6. Lo que se le pide a cada lente

**Serrano (análisis de spec: incertidumbre peligrosa, supuestos sin declarar, contradicciones).**
- Recorre D2, D3, D4, D5, D7, §3, §4, §9 y las enmiendas del 18-09, 14-10 y 16-10 buscando cada frase que dice «tarea», «futuro», «ejecutor», `with_timeout`, `Ticker` o `Calendario`, y dice cuáles se vuelven falsas o ambiguas con A y con A'.
- ¿La cifra de 1 500 oculta algún supuesto? En particular: **¿qué entra en «el J2» del límite firmado?** El texto dice *«con sus ISR, el despacho del ejecutor y los DMA»*. El planificador (componer la trama, el CRC del sobre, los eventos) ¿es el J2 o es el motor/hub? Si es el J2, el límite se rompe antes de empezar.
- ¿Qué afirma la spec sobre el plazo (≤ 220 µs, mayor que el periodo) que un tic de 125 µs no puede cumplir tal cual?

**Halberg (viabilidad de ejecución: concurrencia, modos de fallo, simulación).**
- Prioridades: el tic y los seis `EOT` en un nivel, el planificador y la recuperación debajo. ¿Qué retraso máximo le imponen a la ISR del USB y a la de la pantalla seis armados seguidos (unos 8 µs a 800 MHz, de ~1 100 ciclos cada uno según la cota) cada 125 µs? ¿Y a los `EOT` de las otras cinco ranuras mientras una se reinicia (20 µs ESTIMADO)? H-1 pide que un plazo vencido en una ranura no retrase a las otras.
- Carreras entre el tic y el `EOT` de la misma ranura: la generación, el `EOT` tardío, `NVIC::unpend` (D2 enmienda del 18-09, D4 pasos 1 y 5), el sello del IWDG al armar.
- La escalada D4.2 resetea el GPDMA1 entero: con los canales **preprogramados una vez**, se pierde la configuración de las doce. ¿Qué rehace quién, y qué ve cada ranura mientras tanto?
- Simula (en el host, con `core`) el peor caso de recuperación con el tic de 125 µs: el plazo cuantizado al tic (detección a 125 o 250 µs) contra el plazo exacto por comparador, y el techo de recuperación de §3 (490 µs contra los 50 ms del módulo).
- ¿Cuánta de la ISR del tic puede estar enmascarada por una sección crítica de `defmt`/RTT o de la sonda?

**Voronov (arquitectura ontológica: errores de categoría, rupturas de abstracción, composabilidad).**
- ¿Qué es «un giro», «un tic», «un periodo» y «un plazo» en A? El plazo es por mensaje y puede superar el periodo; el tic es de hardware y no. ¿Son la misma cosa vista dos veces, como la nota del 19-09 en D3, o dos cosas?
- ¿Quién es el dueño del canal del GPDMA? Hoy, el `Transfer` de embassy; en A, el transporte por registros. ¿Qué pasa con el otro uso de GPDMA1 (el escritor de CV, el esclavo del banco) en el mismo controlador?
- ¿La frontera transporte/planificador/política está en el sitio correcto? R-C8 dice un solo escritor del enlace; en A, ¿quién escribe qué, en qué nivel de prioridad?
- ¿Es A' una sola cosa o dos? ¿Y qué rompe `Calendario` al desaparecer, además de lo que el 16-10 dijo que arreglaba?

**Las tres:** ¿falta una opción en §5? ¿Cuál de A, A', B, C, D, E es la que habría que firmar, con qué orden de trabajo, y qué evidencia (§1.3) habría que tener antes de la firma?

## 7. Archivos que la junta puede leer (rutas absolutas)

- Repo `D:\Desktop\projects\sam17\.claude\worktrees\banco2` (rama `j2/junta-transporte`, con `main` en `a5d4882`):
  - `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md` (la spec firmada; D2-D5.4, D7, §3, §4, §9, enmiendas)
  - `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v1.md` (la propuesta de enmienda, sin firmar)
  - `docs/superpowers/juntas/2026-09-11-j2/` (la junta anterior: lo que la junta tumbó en D5)
  - `software/nucleo/core/src/maestro_j2.rs` (la política, con tests: `Ranura`, `Turno`, `Calendario`, `plazo_us`)
  - `software/nucleo/fw/src/j2_ejecutor.rs` (las tareas de hoy), `j2_spi.rs` (el driver), `j2_isr.rs` (la cota), `j2_banco.rs`, `carga.rs`, `perfil.rs`, `muestreo.rs`
  - `software/nucleo/fw/EN-PLACA.md` (sección `carga_j2`: las cifras, el perfil, la tabla de `costes_bus`), `carga_j2.csv`, `resistencia_j2.csv`
  - `hardware/02-midi-cv/recuperacion_j2_budget.py` (la puerta)
- Manual: `docs/reference/datasheets/stm32n6-rm0486-rev4.pdf`.
