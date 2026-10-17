# Enmienda propuesta a D5.1 — el transporte del J2 «por tic» (v3)

**v3 · 2026-10-17 · PROPUESTA: sin firma, y antes de la segunda pasada de la junta.** Sustituye al `papel-v2.md` (que queda como registro) con lo que el prototipo de banco enseñó. El código está en `main` detrás de features (PR #440): la máquina en `core::transporte_j2`, los buzones en `core::buzones_j2`, los marcos de prueba en `core::marcos_j2`, el transporte en `fw/src/j2_tic.rs`. Lo medido, en `software/nucleo/fw/EN-PLACA.md`, «El transporte por tic»; la revisión del código, hallazgo por hallazgo, en `junta_halberg_codigo.md`; lo que el prototipo dejó sin resolver, en #441. **Nada de esto es el transporte del instrumento: D5.1 sigue en vigor hasta la firma** (acta del 17-10, fichas 2 y 3).

## Resumen, en llano

El J2 del hub gasta hoy, con el transporte firmado (una tarea por ranura), **8 000 ciclos por giro y ranura: el 48 % de un núcleo con seis ranuras**, tres veces el reparto firmado. El transporte «por tic» —una sola interrupción cada 125 µs que mira el estado de cada ranura y decide— gasta **1 967** (el enlace solo), **2 100** con una trama compuesta de mentira, y **2 778** si otra tarea le vacía la caché de datos entre un tic y el siguiente: de **11,8 % a 16,7 % de un núcleo**, contra un límite provisional de 15 %. En el banco ha girado 600 s a 8 kHz sin un fallo, ha aguantado 4,7 millones de marcos numerados bajo cuelgues, errores del DMA y retenciones de la CPU sin una trama rota, repetida ni vieja, y se recupera de un SPI colgado en 131 µs. **Lo que no se ha probado:** un cuelgue de verdad en el GPDMA, seis ranuras reales, el código del planificador y del CRC del sobre, el hub entero y el arnés real. El papel propone adoptarlo como el transporte del J2 con unas condiciones antes de que entre en el instrumento (§5), y pone seis decisiones delante de Samuel (§1).

## 0. Qué cambió respecto a v2, y por qué

Cada punto lleva su evidencia; los números son del banco (NUCLEO-N657X0-Q, 800 MHz, las dos cachés y la región MPU, mensaje de 25 bytes) salvo que se diga.

1. **El buzón de bajada lleva tres casillas, no dos** (§2.6). Con dos, el planificador reescribe en sitio la trama fresca y un tic que llega a mitad de la escritura arma una trama a medias. Lo cazó una prueba de modelo antes de tocar la placa (`core::buzones_j2::Triple`; tres mutaciones del buzón mueren con 4, 2 y 2 pruebas en rojo).
2. **Las cotas de espera de `Vencida` y `Reiniciando` pasan de 2 y 4 tics a 100 y 100** (12,5 ms cada una; §2.5). Con las de v2, una retención de P2 que empieza en el instante en que el tic da por vencida la ranura la mata si dura **400 µs** (sobrevive a 300); con las nuevas sobrevive a 12 ms y muere con 14 (`tic_cota`). Una ranura muerta deja de sellar y el IWDG reinicia el chip: con las cotas de v2 un USB o una pantalla en P2 podían parar el instrumento.
3. **El reloj de la política es de 64 bits** (§2.7). El contador de tics de 32 bits da la vuelta a los **6,2 días** a 8 kHz y la política recibía un reloj que daba un paso atrás y dejaba `inestable()` en `true` otros 6,2 días.
4. **La recuperación, medida** (§2.5): vencida a los 123 µs, recuperación hecha a los 131, primera trama buena a los **249** (v2 estimaba 395 µs de techo para un `NADA`). El reinicio dura **6 µs**, no los 20 estimados; el `CS` queda sin manejar 1,2 µs (1,5 con tres ranuras). Un error de ajuste de usuario del DMA (`USEF`) recorre la rama `error_dma` del tic y se recupera. Detalles de orden que el papel no decía y el código necesita: el sondeo de `SUSPF` mira una última vez antes de rendirse y escalar, y el apretón de manos tic–recuperación lleva `dsb` y `Release`/`Acquire`.
5. **`Evento::Tick` solo a la ranura que en esa pasada no recibió otro evento** (§2.7): todo evento lleva su `ahora_us` y desliza la ventana de la política.
6. **La CPU está medida** (§3), y la estimación de v2 se quedó corta por ~900 ciclos: 1 060 estimado contra 1 967 medido el enlace solo. La caché fría cuesta +600 a +700 ciclos si otra tarea vacía la D-cache entera entre dos tics, y nada si desaloja la mitad.
7. **La integridad del contenido se probó con marcos numerados, y apareció el cable** (§4.2). Las comprobaciones de contenido anteriores solo valían para un patrón regular: con los pines del J2 a `VeryHigh`, el cableado de puentes de la Nucleo rompe los marcos de apariencia aleatoria (llegan enteros 4 de 16 contenidos de prueba); con `Medium`, o con el MISO quieto, llegan los 16. Es un requisito nuevo para el hub (R-H7).
8. **Dos propuestas nuevas, sin construir:** un presupuesto de escaladas del GPDMA1 (§2.5) y un presupuesto de retraso del tic (§2.8). Son el resto de la revisión del código.

## 1. Lo que firmó el acta del 17-10, y lo que este papel pone delante de Samuel

**Firmado (acta del 17-10):** la ficha 1 (**A**) fijó que contra los 2 500 ciclos cuenta el trabajo propio del enlace —armar y cerrar cada transferencia, el tic o las interrupciones, el DMA, la comprobación de la subida (el CRC del sobre) y los contadores de salud— y **no** componer la trama; la ficha 2 (**A**) dejó el 15 % **provisional hasta que exista el censo de CPU del hub**, con D5.1 en vigor; la ficha 3 (**A**) autorizó el prototipo, que es lo que está medido aquí. El censo (`hardware/02-midi-cv/carga_hub_budget.py`) tiene hoy 11 filas y **ninguna con cifra**, también la del J2: la fila de `carga_j2.csv` espera a que el CSV tenga la columna `transporte` (§5).

**Lo que este papel pide ahora**, seis fichas con la opción recomendada primero. El orden es brief → papel → junta → firma; la firma va después de esta pasada.

| Ficha | Pregunta | Recomendación | Lo que cuestan las otras |
|---|---|---|---|
| **A** | ¿Se adopta el transporte por tic como el transporte del J2, en lugar del de D5.1? | **Sí**, con las condiciones de §5 antes de que entre en el binario del instrumento o se fabrique. El censo decide el *presupuesto*; no decide el *transporte*: el ejecutor gasta el 48 % de un núcleo y no baja con más ranuras, así que no cabe en ningún reparto plausible. | *Esperar al censo:* D5.1 sigue, el prototipo se queda en `main` detrás de sus features y el cerebro no puede tener un J2 que quepa hasta que el censo exista. *Quedarse con el ejecutor y subir el límite o bajar la cadencia* (#436, opciones 2 y 3): 48 % de un núcleo, o 24 % a 4 kHz con la latencia de la mano y la cabecera tocadas. |
| **B** | ¿Se aceptan las cotas de 100 y 100 tics y un presupuesto de **3 escaladas por segundo**, pasado el cual la ranura que pide la cuarta se da por muerta? (§2.5) | **Sí.** El tope sale de D7.3: cada escalada le cuesta un plazo vencido a todas las demás ranuras, y 3 por segundo no llegan al umbral de `inestable` (10 por segundo) por sí solas. | *Sin presupuesto:* una escalada que se repite degrada las seis ranuras sin que nada diga basta. *Tope de 1:* una avería que toca a varias ranuras a la vez (una descarga en el fondo del bus) se llevaría la ranura por una sola escalada legítima. |
| **C** | Cuando el planificador se atrasa y no hay trama nueva, ¿qué sale? (R-C8) | **Nada**: el tic no arma, cuenta `sin_bajada`, y el módulo aguanta 400 giros (~50 ms) sin tramas. Un solo escritor del enlace. | *Un `NADA` de relleno del tic:* segundo escritor de la `secuencia`, rompe R-C8. |
| **D** | La subida llega a la política un periodo después (el cierre es en el tic siguiente): de 65 a 90 µs más que con la ISR del EOT, ¿se acepta? (§2.6) | **Sí.** Es el 6,5 al 9 % del objetivo de 1 ms mano→DAC, y ese presupuesto no se puede cerrar todavía (HUECO del ADC en `latencia_mano_budget.py`). | *Un tic a 16 kHz:* el cierre llega como mucho 62,5 µs después de completarse la trama; el tic cuesta el doble de entradas, sin medir. |
| **E** | ¿Se declara requisito del hub que el enlace del arnés real, con sus bordes y su reloj, pase `tic_contenidos` (16 de 16) y un `tic_estres` limpio antes de fabricarlo? (R-H7) | **Sí.** El paso 2 del J2 (34,5 MHz) necesita bordes rápidos y con los puentes de la Nucleo se rompe el enlace. | *No exigirlo:* se descubre en el primer arnés, sin tiempo de rediseñarlo. |
| **F** | ¿Qué condiciones se exigen antes de que el transporte entre en el instrumento? (§5) | Las cuatro de §5.2: columna `transporte` en los CSV y en la puerta; seis ranuras reales; una fila de `carga_j2` con el CRC del sobre real; y un `tic_estres` con tres o más ranuras con esclavo. | *Menos:* entra con menos evidencia que el ejecutor al que sustituye (44,7 millones de transferencias y 24 h). |

**Del papel del hub** (requisitos que este diseño exige y que hoy no están escritos; ninguno es de este papel): R-H1 a R-H6 como en v2 §1, con cambios en R-H1, R-H2 y R-H4 (abajo) y uno nuevo (R-H7).

- **R-H1, niveles de NVIC:** el tic en el nivel 1; USB, pantalla y MIDI en el 2; el planificador en el 3; la recuperación en el 4. **Nuevo:** ninguna ISR de P2 retiene al planificador más de 12 ms (más, y una ranura que venza en ese rato muere: §0.2); se pide que sea ≤ 1 ms, porque cada 125 µs por encima de los primeros 120 µs cuesta un giro en cada ranura (medido: 150 µs → 0,22 giros por golpe, 1 ms → 7, 3 ms → 23).
- **R-H2, máximo enmascarado:** ninguna sección crítica de más de 5 µs y nada de `defmt` con el J2 girando. **Nuevo:** el retraso del tic al entrar queda por debajo de 60 µs (§2.8).
- **R-H3, el GPDMA1 es del J2:** los doce canales y la escalada. El escritor de CV es HUECO (#367).
- **R-H4, la D-cache encendida con la región de R-MJ7** y, **nuevo**, el texto y los estáticos de las tres rutinas del J2 (tic, planificador, recuperación) **en RAM**, no en la XSPI: el banco corre desde la RAM y el instrumento puede arrancar de la XSPI, donde una I-cache fría añade decenas de µs al tic (sin medir).
- **R-H5, el reloj del kernel del SPI (#380):** con `pclk2` a 100 MHz, 10 MHz pedidos dan 6,25 MHz y un `SET` de dieciséis dura 131,8 µs, más que el periodo.
- **R-H6, el censo de CPU del hub.**
- **R-H7 (nuevo), el arnés del J2:** bordes y terminación con los que el enlace pasa `tic_contenidos` con contenido que no sea un patrón regular, a su reloj de diseño (ficha E).

## 2. El diseño

### 2.1 Los recursos, sus dueños y los niveles

| Recurso | Dueño | Cómo |
|---|---|---|
| El tic (`TIM7`, 125 µs) | el transporte | la única interrupción del J2; nivel 1 |
| Los seis SPI | el transporte, por registros | `EOTIE = 0`. Sus seis líneas de IRQ, enmascaradas. `Ranura::nueva` solo configura pines, reloj y `CFG1/CFG2` |
| Los doce canales del GPDMA1 | el transporte, por registros | `TCIE`, `USEIE`, `DTEIE` y `SUSPIE` a cero; sus doce líneas de IRQ, enmascaradas; ningún `Transfer` ni `bind_interrupts!` de embassy |
| Los búferes | región no cacheable (R-MJ7) | **por ranura: tres casillas de bajada y dos de subida**, alineadas a la línea de caché |
| La política (`core::Ranura`) | el planificador | **el único** que llama `paso` |
| El buzón de bajada (`Triple`) | lo escribe el planificador, lo lee el tic | tres casillas, una siempre del escritor, una del lector y una en medio con el bit de «fresca» |
| El anillo de eventos (`Anillo<8>`) | lo escribe el tic, lo lee el planificador | productor y consumidor únicos; lleno, descarta lo nuevo y cuenta |
| La subida (`Subida`) | la escribe el tic, la lee el planificador | contador de cierres y casilla; el planificador copia y comprueba que el contador no cambió |
| El estado de una ranura | el tic | nadie más lo escribe, salvo `ReinicioHecho` y la marca de escalada (§2.5) |

Niveles: **tic (1)**, **planificador (3)**, **recuperación (4)**. En el banco el planificador y la recuperación van en dos vectores que ningún otro módulo atiende (`DMA2D` y `JPEG`), que el tic y el planificador hacen pendientes; en el hub serán los que R-H1 fije. Los seis periféricos y los doce canales corren en paralelo por hardware. El tic **mide 4,4 µs con tres ranuras armadas** (1 175 ciclos por ranura: leer los tres `SR` 139, cerrar 10, armar 617, el resto —estado, banderas, buzón y anillo— unos 410); extrapolado linealmente a seis ranuras son **≤ 8,8 µs** ocupando el nivel 1, no medido.

### 2.2 La máquina de una ranura

Vive en `core::transporte_j2` (`Transporte`), pura y probada en el host. **Una entrada por tic**, calculada por `fw` leyendo registros: `Lectura { eot, tcf_rx, tcf_tx, error_dma }` más la identidad (R-MJ6), la bajada fresca con su plazo en tics, y si la recuperación arrancó o terminó.

| Estado | Entrada | Acción | Siguiente |
|---|---|---|---|
| `Libre` | identidad y bajada fresca | `Armar`; emite `Armada` | `Armada{edad 0}` |
| `Libre` | identidad, sin bajada fresca | cuenta `sin_bajada`; no arma | `Libre` |
| `Armada` | `error_dma` | `Cerrar`; cuenta `errores_dma`; emite `PlazoVencido` | `Vencida` |
| `Armada` | `eot ∧ tcf_rx ∧ tcf_tx` | `Cerrar`; publica la subida; emite `GiroOk`; arma otra vez si hay bajada fresca | `Libre` o `Armada` |
| `Armada` | nada de lo anterior, `edad + 1 ≥ plazo` | emite `PlazoVencido` | `Vencida` |
| `Armada` | nada de lo anterior | — | `Armada{edad + 1}` |
| `Vencida` | `reinicio_hecho` | arma si puede | `Libre` o `Armada` |
| `Vencida` | `reinicio_en_curso` | — | `Reiniciando` |
| `Vencida` | `espera ≥ 100` | emite `RanuraMuerta` | `Muerta` |
| `Reiniciando` | `reinicio_hecho` | arma si puede | `Libre` o `Armada` |
| `Reiniciando` | `espera ≥ 100` | emite `RanuraMuerta` | `Muerta` |
| `Muerta` | — | no arma y **no sella** | `Muerta` |

El orden entre filas importa: el error del DMA gana al `eot` (un canal parado o con error no se da por bueno), y un giro completo gana al plazo en el mismo tic. Sin estado `Cerrando`: el cierre es inmediato, porque la subida va a un doble búfer. **Todo estado de espera tiene una cota en tics** (`Armada`: el plazo; `Vencida` y `Reiniciando`: 100 cada una; `Muerta` es absorbente), y R-MJ2 se cumple con la frase «ninguna espera es un bucle síncrono sin cota ni un estado sin salida». `Transporte::con_cotas(vencida, reiniciando)` deja elegir las cotas por máquina; `declarar_vencida` es lo que la escalada usa con las ranuras en vuelo.

### 2.3 El giro normal contra D2

**Arranque** (D2 con sus tres enmiendas, sin tocar): `SPE = 0 → TXTFC → TSIZE → CFG1(RXDMAEN) → canal RX (BR1, dirección, CR.EN) → canal TX → CFG1(TXDMAEN) → SPE = 1 → leer CR1 → esperar ≥ 1 T_SCK → EOTC → CSTART`. Sin `EOTIE`. El primer `SPE = 0` se conserva. Por giro solo se escriben `BR1`, la dirección de memoria y `CR.EN` de cada canal; el resto se programó una vez. `CR.EN` está en cero por construcción cuando se arma: la ranura llega a `Libre` con `TCF` de los dos canales o tras el `RESET` de la recuperación, y el RM dice que el hardware baja `EN` en los dos casos (GPDMA_CxCR, bit 0 `EN`, RM0486 Rev 4).

**Cierre** (RM0486 p. 3449): el tic lee `SR` del SPI y de los dos canales; con `EOT ∧ TCF_RX ∧ TCF_TX` y ningún `DTEF/USEF/ULEF`, escribe las banderas, `SPE = 0` y solo entonces los dos `DMAEN` a cero. Es un periodo después del armado, como mínimo.

### 2.4 El plazo (D3), en tics

`N(msg) = ceil(plazo_us(msg) / 125)`, con `plazo_us` de `core` sin tocar: `NADA` 1, `EVENTO` 1, `TONO` 1, `BAHIA` 2, `SET` de dieciséis 2 a 8 MHz y 3 a 6,25 MHz. El plazo pasa de frontera en µs a «terminar en `N` tics»; `eot_tardios` es cero por construcción; `plazos_vencidos` cuenta «no terminó en `N` tics». **La fila del soak del 16-17 de octubre no se transfiere.** El techo de recuperación pasa a `(N + 2) × periodo + T_REINICIO`; **medido**, de la trama envenenada a la primera buena: 249 µs para un `NADA` (123 µs hasta vencer, 6 µs de recuperación, el resto esperando al tic y al armado), contra los ~50 ms del módulo (200×).

### 2.5 La recuperación (D4) y la escalada

La pide la política (`Accion::Reiniciar`) y la ejecuta el nivel 4. Los pasos, medidos en el banco con un SPI envenenado a propósito:

1. **Parar los dos canales:** `CR.SUSP = 1`, sondear `SUSPF` hasta `T_CANAL` = 25 µs, `CR.RESET = 1`. Antes de rendirse y escalar, se vuelve a leer una vez (una interrupción entre la lectura y la comparación podía comerse los 25 µs).
2. **Resetear el SPI por RCC** (`disable` y `enable_and_reset`) **y reescribir `CFG2` y `CFG1` en una sola sección crítica**: 1,2 µs con el `CS` sin manejar.
3. **Reprogramar los dos canales por completo** (idempotente: sirve tras el `RESET` de un canal y tras el reset del GPDMA1).
4. **Publicar `ReinicioHecho`** con su marca de tiempo (con `dsb` y `Release`; el tic lo lee con `Acquire` solo en `Vencida` y `Reiniciando`); el tic devuelve la ranura a `Libre` pasados `T_GAP_REARME` = 2 µs, ESTIMADO.

**La escalada D4.2** (un canal no llega a `SUSPF` en `T_CANAL`): `rcc::disable` y `rcc::enable_and_reset::<GPDMA1>` **en una sola sección crítica** —**650 ns** medidos—, y dentro de ella se marcan las ranuras sucias y se declaran vencidas las que estaban en vuelo; la recuperación reprograma los canales de todas las ranuras activas antes de limpiarlas. Es el **único acto del transporte que cruza ranuras**: una avería de una ranura le cuesta una transferencia a las otras cinco.

**Presupuesto de escaladas (propuesta nueva, sin construir):** la recuperación guarda los tics de las últimas **3** escaladas; si una cuarta se pide dentro de **8 000 tics (1 s, la ventana de D7.3)**, no escala: da por muerta a la ranura que la pide (`Muerta`: deja de sellar, el IWDG del hub reinicia el chip). Los números salen de D7.3: cada escalada le carga un `PlazoVencido` a cada ranura en vuelo, y con ≤ 3 por segundo una ranura sana recibe ≤ 3 de los 10 que ponen `inestable`. Una avería que toca varias ranuras a la vez produce **una** escalada (la primera reinicia el controlador y las demás recuperaciones encuentran los canales ya parados); varias seguidas indican un canal que no se arregla con un reset. La política no cambia.

**Cotas de los estados de recuperación: 100 tics en `Vencida` y 100 en `Reiniciando`** (12,5 ms cada una, 25 ms entre las dos): menos que los ~50 ms que el módulo aguanta sin tramas y que el plazo del IWDG (estrictamente mayor, D5.4). Medido: la ranura sobrevive a una retención de P2 de 12 ms justo en el instante en que vence y muere con 14.

### 2.6 Los búferes, el buzón y la secuencia

- **Subida:** doble búfer por ranura en la región no cacheable. El tic cierra publicando el índice y arma el contrario; el planificador copia con `ldm` a un búfer local y comprueba que el contador de cierres no cambió (`Rota` o copia limpia, en cualquier intercalación). Un acceso suelto a la región cuesta 84 ciclos; copiar 25 bytes con `ldm`, unas decenas.
- **Bajada:** `Triple` (§0.1); se consume al armar. Tras una recuperación está vacío hasta que el planificador compone otra trama: la abortada no se repite.
- **Sin bajada fresca** el tic no arma y cuenta `sin_bajada`. Medido: un planificador retenido 150 µs pierde 65 giros en 300 golpes; 1 ms, 2 102; 3 ms, 6 904 (23 giros por golpe). La ficha C propone que no salga nada, sin relleno del tic.
- **La subida llega un periodo después**: la política ve la subida en el tic siguiente a la transferencia, o sea **125 − c µs** más tarde que con la ISR del EOT, con `c` lo que tarda la trama en completarse (35 a 60 µs para las de 25 y 41 bytes): de 65 a 90 µs. Si tiene consecuencia en D7 (las marcas de salud se alimentan de `SubidaOk`/`SubidaMala`, y esas marcas llegan un periodo después) lo dice la junta.

### 2.7 Quién llama a la política, y con qué reloj

El tic empuja un evento a un anillo de la ranura. El planificador vacía los anillos, llama a `paso(evento, tics × 125 µs)` con el contador **extendido a 64 bits** (`Reloj64`, que hay que llamar al menos una vez por vuelta de 32 bits: el planificador lo hace en cada pasada), y manda un `Evento::Tick` por periodo y ranura activa **solo a la que no recibió otro evento en esa pasada**. Una sola base de tiempo para la política, el plazo y el calendario. `DWT_CYCCNT` se usa solo para los testigos y para `T_GAP_REARME`.

### 2.8 Los testigos, y el presupuesto de retraso del tic

`retraso_max_us` (al entrar, lee `TIM7.CNT`), `tics_tardios` (más de 10 µs) y `tics_fusionados` (el intervalo entre dos entradas pasa de 1,5 periodos); `plazos_vencidos`, `errores_dma`, `sin_bajada`, `subidas_perdidas`, `eventos_perdidos`, `recuperaciones`, `escaladas_gpdma`. Un atraso no mueve `inestable` ni `muda`.

**El presupuesto de retraso del tic (propuesta nueva):** una transferencia armada en un tic se mira como pronto en el siguiente, así que un tic que arma con retraso `δ` la deja sin tiempo si `δ` + lo que ocupa su armado + lo que dura la trama pasan de 125 µs. A 6,25 MHz, con el armado de seis ranuras en 8,8 µs, la holgura de los mensajes de una sola espera es **84 µs para un `NADA`, 98 para un `EVENTO` y 64 para un `TONO`**; `BAHIA` y `SET` tienen dos y tres tics. **Presupuesto: el retraso del tic al entrar, siempre por debajo de 60 µs** (R-H2). Lo que lo rompe no es el nivel 1 sino el texto del tic fuera de caché (R-H4) y las secciones críticas del hub. Si lo rompe, todas las ranuras armadas en ese tic vencen a la vez: cuesta un giro por ranura y una recuperación, no el instrumento.

### 2.9 Qué desaparece

Las tareas y el `EJECUTOR_J2` (`fw/src/j2_ejecutor.rs`), `embassy_time::Timer` en el camino del J2, los `Transfer` y su `Drop`, las seis ISR de SPI, `Turno` y la generación del EOT, `EOTIE` y `NVIC::unpend`, `Calendario` y las enmiendas del 18-09 (`Ticker::reset`, R15) y del 16-10, y el `bind_interrupts!` de embassy sobre los doce canales.

## 3. La CPU, medida

Ciclos por giro y ranura a 800 MHz con I-cache, D-cache y la región MPU (medidor del hilo, una base por estado de caché, firmware `7bda894`; cuanto de medida: 33 ciclos con tres ranuras y 100 con una):

| | 1 ranura | 3 ranuras | % de un núcleo con 6 ranuras |
|---|---|---|---|
| el enlace solo (lo que cuenta la ficha 1, sin el CRC) | 2 200 | **1 967** | 11,8 % |
| con una trama compuesta de mentira (146 ciclos) | 2 400 | 2 100 | 12,6 % |
| el enlace solo, la D-cache vaciada entera entre tic y tic | — | 2 778 | 16,7 % |
| 41 y 71 bytes, el enlace solo | — | 2 100 y 2 200 | 12,6 % y 13,2 % |
| solo la I-cache, sin D-cache | 17 900 | 15 773 | 94 % |
| el ejecutor de D5.1 (con las mismas cachés) | 8 000 | 8 167 | 48 % |

(Con la D-cache vaciada, el desglose del `DWT` da 2 592; el medidor del hilo, 2 778. Un barrido de 8 o 16 KB entre tics no cuesta nada medible; de 32 KB, 2 699; de 64 KB, 2 592. **La columna de 6 ranuras es aritmética sobre las medidas de 1 y 3**, no una medida: el coste por ranura baja unos 230 ciclos de una a tres, así que seis deberían costar algo menos.) El `SET` de dieciséis (103 bytes) no está medido: ocupa más de un periodo a 6,25 MHz (R-H5).

**Lo que la cifra no incluye**, que es lo que decide si cabe:

- **El CRC del sobre de la subida**, que la ficha 1 cuenta como trabajo del enlace y no está escrito ni medido (#267). Un CRC por tabla a unos 5 ciclos por byte suma de 125 a 350 ciclos según el mensaje: el enlace solo pasaría a **2 092 – 2 317 ciclos, 12,6 a 13,9 %**, con un margen de 183 a 408 ciclos (7 a 16 %) bajo el límite provisional.
- **La caché fría.** Si otra tarea del hub (pantalla, USB) vacía la D-cache entera entre dos tics, el J2 pasa de 15 % (+ 600 a 700 ciclos, y con el CRC, más). Es lo que el censo del hub tiene que decir.
- **Seis ranuras reales** y el hub entero.

**Palancas conocidas, sin gastar:** esperar **un** `T_SCK` para las seis ranuras en vez de uno por ranura (128 ciclos cada uno; unos 107 por ranura y giro) y quitar atómicos del camino; poner el texto y los estáticos del J2 en TCM, que quita de un golpe la dependencia de la caché fría y de la XSPI (no medido). Ninguna es necesaria si el censo deja el 15 %.

## 4. Lo que se probó

### 4.1 Host (`core`)

`Transporte`: todas las filas de §2.2 con sus bordes, y propiedades al azar (una ranura nunca se arma sobre una `Armada`; los contadores se conservan; la recuperación vuelve a `Libre` o a `Muerta`, nunca se queda). `Triple`, `Anillo` y `Subida` con intercalaciones al azar y por mutación. `Reloj64` contra un contador verdadero con pasos de casi una vuelta. `marcos_j2`: nueve mutaciones, todas con una prueba en rojo. 346 pruebas unitarias de `core` y 59 de integración. **La simulación de seis ranuras de Halberg no se ha rehecho sobre la máquina; su revisión del código corrió modelos transliterados del Rust con dos ranuras** (más de tres millones de estados, cero violaciones, `junta_halberg_codigo.md`).

### 4.2 Banco, con esclavo real (SPI5 maestro, SPI4 esclavo)

| Prueba | Resultado |
|---|---|
| Soak, 600 s a 8 kHz, patrón regular | 4 799 999 giros, subidas, tramas y bajadas buenas; cero plazos vencidos, subidas malas, tramas cortas, tics tardíos, eventos y subidas perdidos |
| `tic_estres`, marcos numerados en los dos sentidos, golpes de P3 de 10 a 280 µs, cuelgues y errores del DMA al azar | 4 × 60 s: 1,9 millones de marcos, 11 570 cuelgues, 2 963 errores del DMA, 14 533 recuperaciones; 4 × 150 s: 4,7 millones de marcos, 29 209 cuelgues, 7 342 errores del DMA, 36 551 recuperaciones. Ninguna bajada rota, repetida ni atrasada, ninguna subida rota, atrasada ni futura, ninguna ranura muerta |
| `tic_recupera` | un SPI envenenado (123 / 131 / 249 µs); 1 000 incidentes seguidos (1 000 recuperaciones, 1 000 tramas cortas en el esclavo, ninguna bajada mala); un `USEF`; 10 escaladas **forzadas** del GPDMA1 con tres ranuras (30 plazos, 650 ns de sección crítica); la ranura muerta deja de sellar y las vecinas siguen |
| `tic_cota` | la cota contra una retención de P2 (§2.5) |
| Una retención de P2 sin fallo | hasta ~100 µs no cuesta ninguna trama; 300 µs, 1,4 giros por golpe; 3 ms, 23 |
| `tic_contenidos` | 16 contenidos de 25 bytes, 2 500 tramas de cada uno: con los pines a `VeryHigh` y el MISO conmutando llegan enteros 4; con `Medium`, o con el MISO quieto, 16 |

**Lo que el banco no ejerce:** el cuelgue de verdad de un canal del GPDMA (solo la escalada forzada); seis ranuras reales (el banco tiene tres, y SPI3 y SPI6 piden otra función alterna que `Ranura::nueva` no soporta; con los dos esclavos de relleno la concurrencia solo se ejerce sin contenido que comprobar); el tic fuera de caché o de la XSPI; el `DWT` sin sonda (tres plazos de seguridad lo leen); el máximo enmascarado y la preempción del hub; el CRC y el compositor reales; la cabecera. **Y el cable:** las comprobaciones de contenido de las corridas de antes (la de 24 h incluida, que era del otro transporte) solo valían para un patrón regular; la causa física del fallo con `VeryHigh` no se midió con osciloscopio (la hipótesis es acople entre hilos adyacentes).

## 5. Condiciones

1. **Para firmar el diseño (esta pasada):** las fichas de §1; las medidas 2 y 3 de v2 §4 **limpias, hechas** (recuperación en placa; el transporte completo contra el esclavo a 8 kHz y con marcos numerados); la fila de `carga_j2` con la definición de la ficha 1, **hecha** (1 967 sin componer, 2 100 componiendo de mentira); y la segunda pasada de la junta sobre §2 y §2.5 y §2.8, que son lo nuevo.
2. **Para que el transporte entre en el instrumento** (ficha F): (a) `carga_j2.csv` con una columna **`transporte`** y `recuperacion_j2_budget.py` filtrando por ella (hoy la puerta toma el mínimo de cualquier fila a ≥ 800 MHz y una fila del tic taparía los 8 000 del ejecutor); (b) **seis ranuras reales** (la función alterna de SPI3 y SPI6) con la fila de `carga_j2`; (c) la fila con el **CRC del sobre real** (#267), porque la ficha 1 lo cuenta; (d) un `tic_estres` con tres o más ranuras con esclavo (hoy el banco tiene un solo esclavo).
3. **Para fabricar (R-MJ8):** el soak de 24 h a 8 kHz con este transporte, con `escaladas_gpdma = 0`; la columna `transporte` en la cabecera de `resistencia_j2.csv`; y el arnés del J2 con R-H7.
4. **Para que el censo cierre el 15 %:** las otras diez filas del censo (R-H6). No bloquea el transporte; bloquea saber si 12,6 a 13,9 % cabe.

## 6. Censo de la spec: qué se toca y qué no

La misma tabla que v2 §6, con estas filas cambiadas o añadidas; las que no aparecen siguen como v2.

| Pieza | Estado | Qué |
|---|---|---|
| D2 | **reescrita** (v2) | las esperas son estados; el EOT se lee en el tic; orden de cierre; `CR.EN` en cero por construcción |
| D3 | fórmula igual; vigilancia en tics | techo de recuperación **medido** (§2.4) |
| D4 | **reescrita** (v2) y **enmendada** (v3) | `T_CANAL` 25 µs con una última lectura; reinicio en una sola sección crítica; **presupuesto de escaladas** (§2.5) |
| D5.1 (1) y (3) | **reescritas** | una máquina por ranura movida por un tic; niveles |
| D5.4 | igual | el sello al armar; una ranura `Muerta` no sella; el IWDG, mayor que 50 ms |
| D7 | igual | la política de `core` no cambia; `Evento::Tick` solo a la ranura sin otros eventos |
| R-MJ2 | reescrita (v2) | §2.2 |
| R-MJ3 | seis pasos, otros (v2) | |
| R-MJ4 | constantes nuevas | `T_CANAL`, `T_GAP_REARME`, **cotas 100 y 100**, **3 escaladas por 8 000 tics**, umbrales de los testigos, **60 µs de retraso del tic** |
| R-MJ7 | igual | la subida se copia con `ldm`; tres casillas de bajada |
| R-MJ8 | columna `transporte` | |
| Enmiendas 18-09 (R15) y 16-10 (`Calendario`) | **derogadas** | §2.9 |
| §10, filas del hub | pasan a **R-H1 a R-H7** | |

## 7. Lo que sigue abierto

- **Las fichas de §1** (Samuel).
- **El CRC del sobre y el compositor reales** (#267, la cabecera): lo que decide si 12,6 a 13,9 % se mantiene.
- **Seis ranuras reales** y la concurrencia con contenido.
- **El censo del hub** (R-H6) y R-H1 a R-H7.
- **Una escalada de verdad:** no hay forma de atascar un canal del GPDMA en el banco.
- **`cierra()` en la rama `error_dma`** va contra el orden obligatorio del RM; la rama corre y se recupera, y el orden se arregla en el código cuando el papel se firme.
- **`programa()` no reescribe el estado global del GPDMA** (`SECCFGR`, `PRIVCFGR`, `RCFGLOCKR`): inocuo con los valores de reset del banco; hay que decidirlo con el hub (R-H3).
- **El `DWT` sin sonda**, tres plazos de seguridad.
- **Los números ESTIMADO que quedan:** `T_GAP_REARME` y las cotas de §2.5 (medidas contra una retención, no contra el hub).
- **La causa física del fallo del cable** (R-H7).

## 8. Registro: de v2 a v3

`H` = hallazgo de `junta_halberg_codigo.md`.

| Hallazgo | Resolución en v3 |
|---|---|
| H1, cotas de 2 y 4 tics | 100 y 100; medido el umbral (§0.2, §2.5) |
| H2, evidencia con contenido fijo | marcos numerados, golpes y cuelgues al azar (§4.2) |
| H3, reloj de 32 bits | `Reloj64` (§2.7) |
| H4, escaladas sin tope y daño colateral | presupuesto de 3 por segundo (§2.5), ficha B |
| H5, la escalada solo forzada | dicho como límite (§4.2, §7) |
| H6, `para_canales` sobre una muestra vieja | una última lectura (§2.5) |
| H7, un tic tarde y la XSPI | presupuesto de 60 µs (§2.8), R-H4 |
| H8, `CR.EN`, orden de acceso, `error_dma`, `TR3` | §2.3, §2.5, §7 |
| H9, acoplamientos del banco | dicho en §4.2 y §7 |
| el cable del banco | R-H7, ficha E (§0.7, §4.2) |

## 9. Registro de la segunda pasada de la junta

*(Se llena al absorber los informes de Serrano, Halberg y Voronov sobre este papel.)*
