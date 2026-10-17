# Enmienda propuesta a D5.1 — el transporte del J2 «por tic» (v3)

**v3 · 2026-10-17 · PROPUESTA: sin firma.** Absorbe la segunda pasada de la junta (`junta2_serrano.md`, `junta2_halberg.md`, `junta2_voronov.md`, sobre el texto del commit `72d6e6f`) y sustituye al `papel-v2.md`, que queda como registro. El código del prototipo está en `main` detrás de features (PR #437–#440): la máquina en `core::transporte_j2`, los buzones en `core::buzones_j2`, los marcos de prueba en `core::marcos_j2`, el transporte en `fw/src/j2_tic.rs`. Lo medido, en `software/nucleo/fw/EN-PLACA.md`, «El transporte por tic»; la revisión del código, en `junta_halberg_codigo.md`; lo que quedó sin resolver, en #441. **Nada de esto es el transporte del instrumento: D5.1 sigue en vigor hasta la firma y hasta las condiciones de §5.2.**

Cada cifra lleva su estatus: **(M)** medida en el banco, **(A)** aritmética sobre lo medido, **(E)** estimada. **Los mecanismos de §2.2 (identidad y `SUCIA`), §2.5 (permiso de escalada y `PlazoAjeno`), §2.7 (tics reconstruidos) y §2.11 no están construidos, y la junta no los ha visto:** son la respuesta de este papel a la segunda pasada.

## Resumen, en llano

Con el transporte firmado (una tarea por ranura) el J2 del hub gasta **8 000 ciclos por giro y ranura (M)**: el 48 % de un núcleo con seis ranuras, tres veces el reparto provisional del 15 %. Esa cifra es de la estructura medida (una espera por ranura, sin la región MPU de los búferes); con un solo temporizador repartido entre las seis no se ha medido. El transporte «por tic» —una sola interrupción cada 125 µs que mira cada ranura y decide— gasta **1 967 (M)** con las cachés calientes, el 11,8 % de un núcleo con seis ranuras (A); con el CRC del sobre, que la ficha 1 del acta cuenta y aún no está escrito, **12,6 a 13,9 % (A, E)**. Si otra tarea vacía la caché de datos entera entre un tic y el siguiente, **2 778 (M)**: **17,4 a 18,8 % con el CRC (A, E)**, por encima del 15 %. **Cabe o no cabe según el régimen de caché del hub, y eso lo dice un censo que hoy no tiene una sola cifra.**

En el banco ha girado 600 s a 8 kHz sin un fallo, ha aguantado 4,7 millones de marcos numerados bajo golpes de P3, cuelgues y errores del DMA sin una trama rota, repetida ni vieja, y se recupera de un SPI colgado en 131 µs. **Fue con una ranura con esclavo, mensajes de 25 bytes y los pines a `Medium`** (con `VeryHigh` el cableado del banco rompe los marcos). **No se ha probado:** un cuelgue de verdad del GPDMA, seis ranuras reales, mensajes de varios tics con contenido, el CRC y el planificador reales, el supervisor del IWDG que cierra la cadena de seguridad, el hub y el arnés.

El papel propone adoptarlo como el diseño del transporte del J2 con las condiciones de §5, y pone siete decisiones delante de Samuel (§1). **Pedir que se firme esta adopción es pedir que se revoque una frase del acta del 17-10**, y la ficha A lo dice.

## 0. Qué cambió

### 0.1 Respecto a v2, por lo que enseñó el banco

1. **El buzón de bajada lleva tres casillas, no dos** (§2.6). Con dos, el planificador reescribe en sitio la trama fresca y un tic que llega a mitad de la escritura arma una trama a medias. Lo cazó una prueba de modelo (`core::buzones_j2::Triple`); tres mutaciones del buzón mueren con 4, 2 y 2 pruebas en rojo.
2. **Las cotas de espera de `Vencida` y `Reiniciando` pasan de 2 y 4 tics a 100 y 100 en el prototipo** (12,5 ms cada una; §2.5). Con las de v2, una retención de P2 que empieza en el instante en que el tic da por vencida la ranura la mata si dura **400 µs (M)** (sobrevive a 300); con las nuevas sobrevive a 12 ms y muere con 14 (M, `tic_cota`).
3. **El reloj de la política es de 64 bits** (§2.7): el contador de tics de 32 bits da la vuelta a los 6,2 días a 8 kHz (A).
4. **La recuperación, medida** (§2.5): vencida a los 123 µs, recuperación hecha a los 131, la siguiente trama **arranca** a los 249 (M; una sola muestra). El reinicio dura 6 µs, no los 20 estimados; el `CS` queda sin manejar 1,2 µs (1,5 con tres ranuras). Un error de ajuste de usuario del DMA (`USEF`) recorre la rama `error_dma` y se recupera.
5. **`Evento::Tick` solo a la ranura que en esa pasada no recibió otro evento** (§2.7).
6. **La CPU está medida** (§3); la estimación de v2 se quedó corta por ~900 ciclos.
7. **La integridad se probó con marcos numerados, y apareció el cable** (§4.2): con los pines del J2 a `VeryHigh`, el cableado de puentes rompe los marcos de apariencia aleatoria (llegan enteros 4 de 16 contenidos de prueba; con `Medium`, 16).

### 0.2 Respecto al v3 anterior a la junta, por lo que dijo la segunda pasada

8. **El presupuesto de escaladas con sentencia desaparece.** No tenía transición de muerte (Halberg H1), «3 por segundo» no era lo que la regla hacía (H6), sentenciaba desde la capa que ejecuta con la consecuencia mayor del sistema (Voronov F5) y acababa en un supervisor que no existe (H12, S3). Lo sustituye **un permiso que da la política** (§2.5, ficha B).
9. **`PlazoVencido` pierde la excusa de «la política no cambia»:** una escalada ajena ya no puntúa en la salud de las vecinas (`PlazoAjeno`, §2.5), y un tic tardío sí puntúa, porque pierde tramas de verdad (§2.8). Se retira la frase «un atraso no mueve `inestable`».
10. **El tic cuenta periodos, no entradas** (§2.7), y las cotas se escriben en µs con su aserto contra el módulo (§2.5, ficha C): v3 prometía un reloj y entregaba un contador (Voronov, Halberg H10).
11. **La tabla de plazos se corrige** (§2.4): a 6,25 MHz el `TONO` de 41 bytes tiene 126 µs de plazo, o sea **2 tics**, no 1.
12. **La máquina se escribe completa** (§2.2): identidad retirada, `SUCIA`, `Muerta` sin salida, precedencias.
13. **Aparecen las dos piezas que la junta echó en falta del lado del hub:** el supervisor del IWDG (R-H8, §2.11) y la unidad correcta de R-H1, la ventana de inanición del planificador (§1, §2.8).
14. **Se declara lo que cuesta el «Sí»** (ficha A) y la ficha A deja de decir que el censo no decide el transporte.

## 1. Lo que firmó el acta del 17-10, y lo que este papel pone delante de Samuel

**Firmado (acta del 17-10):** la ficha 1 (**A**) fijó que contra los 2 500 ciclos cuenta el trabajo propio del enlace —armar y cerrar cada transferencia, el tic o las interrupciones, el DMA, la comprobación de la subida (el CRC del sobre) y los contadores de salud— y no componer la trama; la ficha 2 (**A**) dejó el 15 % **provisional hasta que exista el censo de CPU del hub**, con D5.1 en vigor, y «el transporte se decide cuando haya una tabla de CPU del resto del hub y medidas de los dos transportes»; el acta dice además, en *Lo que esta acta no decide*: «Si el transporte cambia o no. Eso lo decide el censo del hub junto con las medidas del prototipo.» La ficha 3 (**A**) autorizó el prototipo, que es lo medido aquí. El censo (`hardware/02-midi-cv/carga_hub_budget.py`) tiene 11 filas y **ninguna con cifra**, tampoco la del J2.

**Siete fichas**, la opción recomendada primero. El orden es brief → papel → junta → firma.

| Ficha | Pregunta | Recomendación | Lo que cuesta, y lo que cuestan las otras |
|---|---|---|---|
| **A** | ¿Se adopta el transporte por tic como el diseño del J2, en lugar del de D5.1? | **Sí, como el diseño que se construye; D5.1 sigue en vigor hasta §5.2. Firmar esto revoca la frase del acta «si el transporte cambia o no lo decide el censo»:** el censo pasa a decidir si el transporte *cabe*. | **Costo del Sí:** (1) se pierde el aislamiento frente al hilo de D5.1 (H-9: una tarea de pantalla que retenga la CPU 15 ms no retrasa un giro) a cambio de promesas del hub que hoy no existen (R-H1, R-H2, R-H4, R-H8); (2) seis SPI y doce canales a mano para siempre, y la contribución upstream de D8.2 pierde su sujeto; (3) la evidencia del ejecutor (44,7 millones de transferencias, 24 h a 1 kHz) no se transfiere; (4) la premisa «el ejecutor no cabe» es de la estructura medida, y con un solo temporizador compartido no se ha medido. **Árbol del censo:** J2 ≥ 48 % → cabe el ejecutor y se decide por riesgo y evidencia; 14 a 48 % con cachés calientes → solo cabe el tic; menos de ~12 a 19 % según la caché → no cabe ninguno, y quedan las palancas de §3 y la cadencia. **Otras:** *Esperar al censo* (la frase del acta se mantiene; D5.1 sigue; el prototipo se queda en `main`; no avanza un J2 que quepa hasta que el censo exista). *Quedarse con el ejecutor* (#436, opciones 2 y 3): 48 % de un núcleo, o 24 % a 4 kHz con la cabecera y la latencia de la mano tocadas. |
| **B** | ¿Quién autoriza la escalada del GPDMA1, que resetea las seis ranuras? (§2.5) | **La política:** cada ranura puede pedirla mientras no pase de 3 plazos propios en la ventana de salud; sin permiso, la recuperación no escala y, si sus canales no paran, la ranura muere por su cota de siempre. Las vecinas no puntúan (`PlazoAjeno`). | *Costo:* toca `maestro_j2` (una variante de evento, un campo en la acción, un umbral) y D7; con un canal que el reset no cura, hasta 3 escaladas seguidas en ~1 ms (E) antes de perder el permiso. **Otras:** *Solo contar y publicar* (sin tope): un canal que el reset no cura da 4 000 escaladas por segundo, cada vecina pierde el 38 % de sus giros y el IWDG no salta nunca, porque la ranura atascada sigue sellando (Halberg A4, simulado); depende de que el supervisor lea las marcas. *El presupuesto con sentencia del v3 anterior:* retirado por la junta (H1, H6, H12, F5). |
| **C** | ¿Cuándo se rinde una ranura que no se recupera? (cotas, §2.5) | **En µs, no en tics:** `Vencida` 25 ms y `Reiniciando` 12,5 ms (E; hay que repetir `tic_cota`), con aserto «la suma menos 12 ms de margen es menor que la ventana del módulo (~50 ms)» y los tics reconstruidos del reloj. | *Costo:* cambia lo medido (12 y 14 ms valían para 100 y 100 tics). **Otra:** *12,5 + 12,5 ms como el prototipo* (M): la simulación de Halberg con 6 % de ocupación de P2 vio un máximo de 16,3 ms de inanición del planificador, que mataría la ranura. |
| **D** | Cuando el planificador se atrasa y no hay trama nueva, ¿qué sale? (R-C8) | **Nada.** El tic no arma, cuenta `sin_bajada`, y el sello al armar queda como testigo de que el planificador vive. | *Costo:* una ranura sin tramas ≥ 50 ms hace que el módulo suelte las notas, y el sello que no sube pone en juego al supervisor. **Otra:** *un `NADA` de relleno del tic* convertiría el sello en testigo del tic y alimentaría el watchdog de trama del módulo: quedarían ciegos a la vez los dos testigos de que el planificador vive. |
| **E** | La cadena subida → compone → bajada llega un periodo más tarde: de +65 a +90 µs en el peor caso y ~+140 de media (A), ¿se acepta? (§2.6) | **Sí.** Es el 6,5 al 9 % del objetivo de 1 ms mano→DAC en el peor caso; ese presupuesto no se puede cerrar todavía (HUECO del ADC en `latencia_mano_budget.py`). | **Otras:** *un tic a 16 kHz*: cierra antes, pero las cotas en tics y los plazos se re-derivan (100 tics serían 6,25 ms), y el tic cuesta el doble de entradas, sin medir. *Componer tarde en el periodo* (el planificador por un segundo temporizador): quita ~100 µs de frescura de la bajada; sin medir. |
| **F** | ¿Se exige que el primer arnés del J2 pase `tic_contenidos` (16 de 16) y un `tic_estres` limpio, al reloj de SCK que use y con sus bordes, **antes de fabricar en serie**? (R-H7) | **Sí.** Con los puentes de la Nucleo y `VeryHigh` se rompe el enlace; con `Medium` o el MISO quieto, no. | *Costo:* retrasa la serie hasta tener el prototipo del arnés. El reloj lo da el divisor de `pclk2` (50, 25, 12,5 o 6,25 MHz), no 34,5 MHz. **Otra:** *no exigirlo*: se descubre en el primer arnés, sin tiempo de rediseñarlo. |
| **G** | ¿Qué hace falta antes de que el transporte entre en el instrumento? (§5.2) | **Todo §5.2**, incluido el supervisor del IWDG probado con una ranura muerta de verdad. | **Otra:** *menos condiciones*: entra con menos evidencia que el ejecutor al que sustituye. |

### Lo que este diseño exige del hub (R-H1 a R-H9)

Ninguna es de este papel; hoy no está escrita ninguna.

- **R-H1, niveles y ventana de inanición.** El tic en el nivel 1; USB, pantalla y MIDI en el 2; el planificador en el 3; la recuperación en el 4. **Ninguna ISR por encima del tic** (una puerta que lea todos los `set_priority` del binario del instrumento; hoy el USB de embassy queda en el nivel 0 y el muestreo del banco usa P0). **La unidad es la ventana de inanición:** el mayor intervalo en que el planificador o la recuperación no pueden correr porque lo ocupa lo que está por encima (P2 encadenado más las secciones enmascaradas). Se pide **≤ 12 ms** y una ranura que venza dentro de una ventana que pase de su cota muere (Halberg C1: 13 ISR de P2 de 1 ms seguidas la matan con las cotas de 12,5 ms, aunque cada una cumple «≤ 1 ms»). Cada 125 µs de ventana por encima de los primeros 120 cuesta un giro por ranura (M).
- **R-H2, máximo enmascarado.** Ninguna sección crítica de más de 5 µs y nada de `defmt` con el J2 girando; **el tic entra dentro de 60 µs de su instante** (§2.8).
- **R-H3, el GPDMA1 es del J2:** los doce canales y la escalada. El escritor de CV es HUECO (#367); si lo comparte, cada escalada es un artefacto audible.
- **R-H4, la D-cache con la región de R-MJ7, el texto y los estáticos de las tres rutinas del J2 en RAM** (no en la XSPI) **y el régimen de caché que el hub declara** (caliente o fría), que es el que fija la fila del censo.
- **R-H5, el reloj del kernel del SPI (#380):** con `pclk2` a 100 MHz, 10 MHz pedidos dan 6,25 MHz.
- **R-H6, el censo de CPU del hub, con dos tablas:** la de ciclos por segundo (hoy 11 filas sin cifra) y una de **obligaciones de tiempo** —retención máxima de P2, máximo enmascarado, huella de caché, niveles ocupados— que es la moneda de R-H1 a R-H4.
- **R-H7, el arnés del J2** (ficha F).
- **R-H8, el supervisor de vitalidad (#291)** (§2.11).
- **R-H9, el contador de ciclos libre** (`DWT_CYCCNT`) lo habilita el hub al arrancar y no lo para sin sonda: el reloj reconstruido de §2.7 depende de él.

## 2. El diseño

### 2.1 Los recursos, sus dueños y los niveles

| Recurso | Dueño | Cómo |
|---|---|---|
| El tic (`TIM7`, 125 µs) | el transporte | la única interrupción del J2; nivel 1 |
| Los seis SPI | el transporte, por registros | `EOTIE = 0`; sus seis líneas de IRQ, enmascaradas |
| Los doce canales del GPDMA1 | el transporte, por registros | `TCIE`, `USEIE`, `DTEIE` y `SUSPIE` a cero; sus doce líneas de IRQ, enmascaradas; ningún `Transfer` ni `bind_interrupts!` de embassy |
| Los búferes | región no cacheable (R-MJ7) | por ranura: tres casillas de bajada y dos de subida, alineadas a la línea de caché |
| La política (`core::Ranura`) | el planificador | **el único** que llama `paso` |
| El buzón de bajada (`Triple`), el anillo (`Anillo<8>`), la subida (`Subida`) | planificador y tic, cada uno por su lado | ver `core::buzones_j2` |

**El estado de una ranura no es solo la máquina de §2.2:** son ocho elementos con escritores en tres niveles. `Transporte` (el tic); `REC_PEDIDA` (lo pone el planificador, lo limpia la recuperación); `REC_EN_CURSO`, `REC_HECHA` y su marca de tiempo (la recuperación); `SUCIA` (la escalada); el buzón (planificador y tic); `IDENTIDAD` (el planificador). Todo lo que el papel diga de «el estado» se refiere al conjunto.

Niveles: **tic (1)**, **planificador (3)**, **recuperación (4)**. En el banco el planificador y la recuperación van en dos vectores que ningún otro módulo atiende (`DMA2D` y `JPEG`); en el hub serán los que R-H1 fije. Los seis periféricos y los doce canales corren en paralelo por hardware. El tic mide **4,4 µs con tres ranuras (A: 3 × 1 175 ciclos, promedio con cachés calientes)**; extrapolado, **8,8 µs con seis en caliente y 11,5 µs en frío (E)**, ocupando el nivel 1 (1 175 ciclos por ranura: leer los tres `SR` 139, cerrar 10, armar 617, el resto —estado, banderas, buzón y anillo— unos 410).

### 2.2 La máquina de una ranura

Vive en `core::transporte_j2` (`Transporte`), pura y probada en el host. **Una entrada por tic**, calculada por `fw`: `Lectura { eot, tcf_rx, tcf_tx, error_dma }`, la identidad (R-MJ6), la bajada fresca con su plazo en tics, si la recuperación arrancó o terminó, **si la ranura está `SUCIA` y cuántos periodos pasaron desde la entrada anterior** (§2.7).

| Estado | Entrada | Acción | Siguiente |
|---|---|---|---|
| `Libre` | sin identidad | nada | `Libre` |
| `Libre` | identidad y bajada fresca | `Armar`; emite `Armada` | `Armada{0}` |
| `Libre` | identidad, sin bajada fresca | cuenta `sin_bajada` | `Libre` |
| `Armada` | `error_dma` | `Cerrar`; emite `PlazoVencido` | `Vencida` |
| `Armada` | `eot ∧ tcf_rx ∧ tcf_tx` | `Cerrar`; publica la subida; emite `GiroOk`; arma otra vez si puede | `Libre` o `Armada` |
| `Armada` | nada de lo anterior, `edad + periodos ≥ plazo` | emite `PlazoVencido` | `Vencida` |
| `Armada` | nada de lo anterior | `edad += periodos` | `Armada` |
| `Vencida` | `reinicio_hecho` | arma si puede | `Libre` o `Armada` |
| `Vencida` | `reinicio_en_curso` | — | `Reiniciando` |
| `Vencida` | `sucia` (escalada en curso) | `espera += periodos`; no se lee ni se arma | `Vencida` |
| `Vencida` | `espera ≥ cota` | emite `RanuraMuerta` | `Muerta` |
| `Reiniciando` | `reinicio_hecho` | arma si puede | `Libre` o `Armada` |
| `Reiniciando` | `espera ≥ cota` | emite `RanuraMuerta` | `Muerta` |
| `Muerta` | — | no arma y **no sella** | `Muerta` |

**Precedencias:** el error del DMA gana al `eot`; un giro completo gana al plazo en el mismo tic; en `Vencida` y `Reiniciando`, `reinicio_hecho` gana a `reinicio_en_curso` y los dos ganan a la cota (una recuperación que termina en el tic en que vence la cota salva la ranura).

**Lo que el v3 anterior no decía:**
- **`SUCIA` entra en la máquina.** Antes el tic saltaba la ranura entera mientras estaba marcada, y la escalada la limpia fuera de su sección crítica, expuesta a P2 y P3: una retención justo ahí dejaba seis ranuras congeladas sin cota (Halberg H2, A8). Ahora la espera sigue contando contra la cota.
- **`Muerta` no tiene salida; solo la da un reinicio del chip.** Es una enmienda a D7.1 («gira siempre»: «salvo ranura muerta») y a la frase de R-MJ2 («ni un estado sin salida»: el estado terminal lo cubre el supervisor, §2.11).
- **La espera de `Libre` sin bajada fresca no tiene cota en la máquina:** es la espera del planificador, y la vigila el sello (ficha D).
- **La identidad retirada no mata la ranura.** La política en `Vacia` responde `Nada` a todo, y si el módulo se desenchufa con la ranura `Armada` o `Vencida` nadie pediría el reinicio y la ranura moriría por la cota (el instrumento se reiniciaría por quitar un módulo). La limpieza de una ranura que pierde la identidad no es una decisión de salud: **la pide el planificador cuando la política pasa a `Vacia` con una transferencia en vuelo o vencida**; la ranura vuelve a `Libre` sin armar. Una ranura `Muerta` sin identidad no cuenta para el supervisor.
- **Reinicio de limpieza tras una escalada ajena** (§2.5): el mismo camino.
- Un reinicio pedido sobre una ranura que ya es `Muerta` no se hace (Halberg H5): se saltaría su recuperación y se gastaría una escalada por una ranura perdida.

`Transporte::con_cotas` deja elegir las cotas por máquina; `declarar_vencida` es lo que la escalada usa con las ranuras en vuelo.

### 2.3 El giro normal contra D2

**Arranque** (D2 con sus tres enmiendas): `SPE = 0 → TXTFC → TSIZE → CFG1(RXDMAEN) → canal RX (BR1, dirección, CR.EN) → canal TX → CFG1(TXDMAEN) → SPE = 1 → leer CR1 → esperar ≥ 1 T_SCK → EOTC → CSTART`. Sin `EOTIE`. Por giro solo se escriben `BR1`, la dirección de memoria y `CR.EN` de cada canal. `CR.EN` está en cero por construcción: la ranura llega a `Libre` con `TCF` de los dos canales o tras el `RESET` de la recuperación, y RM0486 Rev 4, GPDMA_CxCR bit 0 `EN`, lo baja en los dos casos.

**Cierre** (RM0486 p. 3449): con `EOT ∧ TCF_RX ∧ TCF_TX` y ningún `DTEF/USEF/ULEF`, el tic escribe las banderas, `SPE = 0` y solo entonces los dos `DMAEN` a cero, un periodo después del armado como mínimo.

### 2.4 El plazo (D3), en tics

`N(msg) = ceil(plazo_us(msg) / 125)`, con `plazo_us = 2 × ceil(bits / f_sck) + 20 µs` de `core` sin tocar. **La tabla depende del reloj de SCK, y el arranque la genera con `tics_de_plazo(plazo_us(tsize, f_sck))`; la de aquí es para dos relojes:**

| Mensaje | a 8 MHz | a 6,25 MHz |
|---|---|---|
| `HOLA` 9 B | 38 µs → 1 | 44 → 1 |
| `EVENTO` 14 B | 48 → 1 | 56 → 1 |
| `NADA`, `COMPUERTA`, `TONO_nada_cambio` 25 B | 70 → 1 | 84 → 1 |
| `TONO_dieciseis` 41 B | 102 → 1 | **126 → 2** |
| `BAHIA` 71 B | 162 → 2 | 202 → 2 |
| `SET_dieciseis` 103 B | 226 → 2 | 284 → 3 |

El plazo deja de ser una frontera de µs y pasa a ser «terminar en `N` tics»; la holgura de D3 (2× y 20 µs) ya reservaba la latencia de la ISR del EOT, y con la rejilla esa misma holgura paga el jitter del tic: **un solo libro** (§2.8). `eot_tardios` es cero por construcción. **La fila del soak del 16-17 de octubre no se transfiere.** El techo de recuperación pasa a `(N + 2) × periodo + T_REINICIO`; medido, de la trama envenenada al **arranque** de la siguiente buena, **249 µs (M)** para un `NADA`, o ~281 µs hasta que termina (A, +32 µs de trama; Halberg simuló 284 antes de construirla).

### 2.5 La recuperación (D4) y la escalada

La pide la política (`Accion::Reiniciar`) y la ejecuta el nivel 4. Pasos, medidos en el banco con un SPI envenenado a propósito:

1. **Parar los dos canales:** `CR.SUSP = 1`; sondear `SUSPF` **o `IDLEF`** (un canal que ya está parado, por ejemplo tras el reset de una escalada de otra ranura, no es un fallo) hasta `T_CANAL` = 25 µs **(E)**. La espera lleva dos cotas, el tiempo y un número máximo de lecturas, para que un contador de ciclos parado no deje a P4 girando para siempre. Antes de rendirse se vuelve a leer una vez. Después, `CR.RESET = 1`.
2. **Resetear el SPI por RCC y reescribir `CFG2` y `CFG1` en una sola sección crítica:** 1,2 µs con el `CS` sin manejar (M).
3. **Reprogramar los dos canales por completo** (idempotente).
4. **Publicar `ReinicioHecho`** con su marca de tiempo (`dsb` y `Release`; el tic lo lee con `Acquire` solo en `Vencida` y `Reiniciando`); el tic devuelve la ranura a `Libre` pasados `T_GAP_REARME` = 2 µs **(E)**.

**La escalada D4.2** —un canal no llega a `SUSPF` ni a `IDLEF` en `T_CANAL`— resetea el GPDMA1 por RCC en una sola sección crítica (**650 ns (M)**) y marca las ranuras sucias. **Es el único acto del transporte que cruza ranuras:** las seis comparten un controlador, y la independencia de H-1 es, por tanto, *condicional a que nadie escale*. Lo que el diseño puede hacer es acotar cuánto cruza:

- **El permiso lo da la política.** `Accion::Reiniciar { escalar: bool }`: la política concede `escalar` mientras la ranura que pide no tenga más de `umbral_escalada` plazos vencidos propios en la ventana de salud (D7.3, 1 s; `umbral_escalada` = 3 **(E)**, y `Umbrales::nuevos` lo rechaza si no es menor que `umbral_inestable` = 10). Es un permiso sobre un recurso compartido, no una marca de salud ni una salida del lazo: la ranura sigue reintentando con el reinicio por canal, y la política sigue girando por toda ranura activa.
- **Sin permiso, no se escala.** La recuperación hace el `RESET` por canal; si los canales no paran, **no publica `HECHA`, reintenta parar cada tic, y la ranura muere por la cota de `Reiniciando`** (transición que ya existe: ninguna transición nueva ni escritor nuevo, a diferencia del presupuesto retirado). Un bloqueo transitorio del bus que acabe antes de esa cota se cura solo.
- **Las vecinas no puntúan.** La escalada declara vencidas a las ranuras `Armada` (todas las que tienen bajada; Halberg A2) emitiendo **`Evento::PlazoAjeno`**: la política lo cuenta aparte (`plazos_ajenos`), manda el reinicio de limpieza con `escalar: false` y no lo anota en la ventana de salud. Así la frase de D5.1 (1) («un cuelgue en una no ensucia la ventana de las demás») vuelve a ser cierta. La mejora de **no declarar vencidas las vecinas cuyo giro ya estaba completo** (se cerrarían con su subida dentro de la misma sección) reduciría el daño a la mitad o menos, y cuesta ~1 µs más de enmascarado: se deja a la junta (§7).
- **Una avería común que el reset cura da una escalada** (Halberg A3: 1 escalada, 6 recuperaciones); si no la cura, el permiso se agota a la tercera.

**Cotas de los estados de recuperación (ficha C).** `Vencida` 25 ms y `Reiniciando` 12,5 ms **(E)**, escritas en µs y convertidas a tics en `lanzar` con aserto `cota_vencida + cota_reiniciando + 12 ms < T_WATCHDOG_TRAMA_US` (como `umbral_muda`); los contadores de espera son de 16 bits. La cota es lo último que queda de «el planificador y la recuperación no hicieron lo suyo»: **se rinde la ranura, no el instrumento** —el instrumento lo reinicia el supervisor (§2.11)—, así que alargarla no retrasa ese reinicio y acorta los falsos positivos de una ventana de inanición larga. **Medido con 100 y 100 tics (12,5 ms): sobrevive a una retención de P2 de 12 ms y muere con 14 (M)**; con 25 y 12,5 ms el umbral debería ser ~25 ms y hay que repetirlo.

### 2.6 Los búferes, el buzón, la secuencia y la latencia

- **Subida:** doble búfer por ranura en la región no cacheable. El tic cierra publicando el índice y arma el contrario; el planificador copia con `ldm` a un búfer local (96 ciclos por 32 bytes, M) y comprueba que el contador de cierres no cambió (`Rota` o copia limpia, en cualquier intercalación).
- **Bajada:** `Triple` (§0.1); se consume al armar. Tras una recuperación está vacío hasta que el planificador compone otra trama: la abortada no se repite.
- **Sin bajada fresca** el tic no arma y cuenta `sin_bajada` (ficha D). Medido: un planificador retenido 150 µs pierde 65 giros en 300 golpes; 1 ms, 2 102; 3 ms, 6 904 (23 por golpe) (M).
- **La latencia de la cadena mano → DAC** es subida (mandos) → compone → bajada (Voz). Con el tic: la subida se cierra en el tic `n+1`, el planificador compone justo después y la bajada solo puede armarse en el `n+2`, o sea **~250 µs fijos (A)** desde que se armó la trama de mandos hasta que se arma la de la Voz. Con el ejecutor: la subida se procesa al terminar (35 a 60 µs) y la Voz compone al armar, en su propia fase: **de 35 a ~185 µs, media ~110 (A)**. La diferencia es **+65 a +90 µs en el peor caso y ~+140 de media (A)**, no «un periodo» ni «65 a 90» a secas. `muda` (40 × 125 µs = 5 ms) sube un periodo más tarde (+2,5 %); `inestable` cuenta plazos y no depende de la subida. El presupuesto mano→DAC no se puede cerrar con esto (HUECO del ADC).

### 2.7 El reloj, y quién llama a la política

**Isocronía, declarada.** Cada garantía de este papel está escrita en tics y se justifica en milisegundos; vale si una entrada del tic equivale a 125 µs de pared. Lo que hace v3 es dejar de suponerlo: **el tic cuenta periodos, no entradas.** En cada entrada lee el contador de ciclos libre (R-H9) y suma `max(1, round(Δciclos / ciclos_por_periodo))` al contador de tics; la máquina recibe ese número como `periodos` y avanza `edad` y `espera` en él. Un tic fundido o tardío ya no atrasa las cotas, la ventana de D7.3 ni el plazo: `tics × 125 µs` sigue a la pared a ±1 periodo, y el error deja de tener un solo signo (Voronov F1; Halberg C2: con 61 % de tics perdidos la cota de 12,6 ms eran 32,8 ms). Si el contador de ciclos está parado o la diferencia es absurda, suma 1 y lo cuenta. `tics_fusionados` pasa a ser **`periodos_saltados`**, un testigo de lo que el reloj reconstruyó. Lo que queda como hipótesis es que el contador de ciclos corre, con su testigo, y el IWDG —de pared— es la red independiente (§2.11).

El tic **no** llama a la política: empuja un evento al anillo. El planificador vacía los anillos, llama a `paso(evento, tics × 125 µs)` con el contador extendido a 64 bits (`Reloj64`, al menos una vez por vuelta de 32 bits), y manda un `Evento::Tick` por periodo solo a la ranura que en esa pasada no recibió otro evento (todo evento lleva su `ahora_us` y desliza la ventana). La cadencia del giro y el hueco tras recuperar son del transporte, no del planificador: se enmienda R-C8 en ese punto (§6).

### 2.8 Los testigos, el retraso del tic y lo que sube al instrumento

**El presupuesto de retraso del tic.** Una transferencia armada en un tic se mira como pronto en el siguiente, así que un tic que arma con retraso `δ` la deja sin tiempo si `δ` más el armado más la trama pasan de 125 µs. Un tic tardío **sí** puntúa en la salud (pierde tramas de verdad: un `PlazoVencido` y una recuperación por ranura, y a 12 por segundo o más las seis quedan `inestable`); v3 retira la frase «un atraso no mueve `inestable`», que era la regla del 16-10 sin su condición. Umbrales de `δ` que hacen vencer a alguna ranura de un tic (simulación de Halberg sobre la máquina real, ε de arranque 0 a 6 µs, **A/E**): `HOLA` 9 B 107–112 µs; `EVENTO` 14 B 101–107; **25 B a 6,25 MHz 87–93**; 25 B a 8 MHz 94–100; **`TONO_dieciseis` a 8 MHz 78–84** (a 6,25 MHz tiene dos tics). **Presupuesto: el tic entra dentro de 60 µs de su instante, siempre** (R-H2): 18 µs de margen sobre el umbral más bajo, y la holgura de un tic con la D-cache fría baja 0–1 µs. Lo que lo rompe es el texto del tic fuera de caché (R-H4) y lo que viva en P0/P1 y en las secciones críticas del hub.

**Testigos del transporte:** `retraso_entrada_max_us`, **`tics_fuera_de_presupuesto`** (entradas con retraso > 60 µs; cuenta cuántas veces, el máximo solo no lo dice), `tics_tardios` (> 10 µs), `periodos_saltados`, **`latencia_plan_max_us`** (del instante en que el tic hace pendiente al planificador a que arranca: es lo que observa R-H1), `plazos_vencidos`, `plazos_ajenos`, `errores_dma`, `sin_bajada`, `subidas_perdidas`, `eventos_perdidos`, `recuperaciones`, `escaladas_gpdma`, `ranuras_muertas`.

**Lo que sube al instrumento (el contrato de `Cuentas`):** hoy son `giros`, `plazos_vencidos`, `eot_tardios`, `subidas_ok`, `subidas_malas`, `atrasos` (publicado como el literal 0), `inestable` y `muda`. Con este diseño: `eot_tardios` y `atrasos` desaparecen (el segundo, con `Calendario`); **se añaden `muerta`, `plazos_ajenos`, `escaladas` y `tics_fuera_de_presupuesto`**. Sin esto la política sigue `Activa` con una ranura muerta y «partes y voces» decide sobre lo que no se publica (Voronov F9).

### 2.9 Qué desaparece

Las tareas y el `EJECUTOR_J2` (`fw/src/j2_ejecutor.rs`), `embassy_time::Timer` en el camino del J2, los `Transfer` y su `Drop`, las seis ISR de SPI, `Turno` y la generación del EOT, `EOTIE` y `NVIC::unpend`, `Calendario` y los puntos de la enmienda del 16-10 que dependían de él (el límite de 15 % y el IWDG alimentado desde el hilo **no** desaparecen: viven en esa enmienda, y siguen), la enmienda del 18-09 (`Ticker::reset`, R15) y el `bind_interrupts!` de embassy sobre los doce canales.

### 2.10 Artefactos audibles

El límite del acta del 11-09 es «cero artefactos audibles atribuibles al bus». En funcionamiento normal v3 lo cumple en lo medido (4,8 millones de giros, ninguno perdido; M). Las exposiciones bajo fallo, que el límite no distingue de una avería:

| Fuente | Qué se pierde | Cuánto |
|---|---|---|
| Cuelgue de una ranura | su trama y un giro más (2 giros por recuperación, A sobre `tic_estres`; la función de D6 dice 3) | la tasa de cuelgues (la spec supone un periodo de 10 a 900 s, E) |
| Escalada (permiso, §2.5) | una trama por vecina con bajada | ≤ 3 seguidas por ranura que la pide |
| Tic tardío fuera del presupuesto | un giro por ranura | no medido: 0 en 4,7 millones |
| Planificador retenido | las tramas no salen (las notas llegan tarde, no se pierden) | un giro por cada 125 µs sobre los primeros 120 (M) |
| `Muerta` | todo el módulo de la ranura, y el reinicio del chip por el supervisor | — |

`EVENTO` no tiene red (D6): cualquiera de las tres primeras filas es audible si la trama perdida lleva un `EVENTO`. **Si el escritor de CV comparte el GPDMA1, cada escalada es audible** (R-H3).

### 2.11 El estado terminal: `Muerta`, el supervisor y el IWDG

El diseño termina en una frase: una ranura `Muerta` deja de sellar, y el supervisor del hub deja de alimentar el IWDG, que reinicia el chip. **El J2 posee la condición del disparo; el hub posee el efecto, y el mapeo entre las dos cosas no lo escribe nadie todavía** (#291). Lo que la simulación de Halberg dice de la cadena (supervisor cada 5 ms e IWDG de 60 ms, ambos supuestos): el reinicio llega a `T_IWDG + (0 a P_s)` del fallo y **no depende de `Muerta` ni de las cotas** —sale de que la ranura deja de armar—; con 5 ms y 60 ms, a los 62–65 ms; con otros valores plausibles, de 56 a 222 ms. El módulo de la ranura suelta a los 50 ms, antes del reinicio; los otros módulos, sanos, lo hacen cuando el arranque del cerebro dura más de 50 ms (HUECO S-10 de la spec). Nada queda escrito: los testigos son `static` en RAM, y un reinicio por el J2 es indistinguible de cualquier otro del IWDG.

**R-H8, el supervisor, entra como requisito:** (1) existe; (2) lee el sello por ranura activa con la regla «armé y alguno de los últimos N terminó» (spec §10, fila pendiente) o las marcas `inestable`/`muda`, porque «armé» solo no ve una ranura que se rearma para siempre; (3) su ventana es mayor que el mayor hueco de sello del diseño (`Vencida` + `Reiniciando`, 37,5 ms, más el periodo del supervisor) y `T_IWDG` mayor que la ventana del módulo más el periodo del supervisor; (4) guarda la causa del reinicio en memoria que sobreviva; (5) se prueba con una ranura muerta de verdad y con un planificador retenido, y esa prueba es condición de §5.2. Una ranura que se reinicia no sella durante la recuperación: es la diferencia con D5.4 («una ranura reiniciando también está viva»), y la ventana de (3) la absorbe.

## 3. La CPU, medida

Ciclos por giro y ranura a 800 MHz con I-cache, D-cache y la región MPU (medidor del hilo, una base por estado de caché, firmware `7bda894`; cuanto de medida: 33 ciclos con tres ranuras y 100 con una):

| | 1 ranura | 3 ranuras | % de un núcleo con 6 ranuras |
|---|---|---|---|
| el enlace solo (lo que cuenta la ficha 1, sin el CRC) **(M)** | 2 200 | **1 967** | 11,8 % |
| con una trama compuesta de mentira (unos 150 ciclos, M) | 2 400 | 2 100 | 12,6 % |
| el enlace solo, D-cache vaciada entera entre tic y tic **(M)** | — | 2 778 | 16,7 % |
| 41 y 71 bytes, el enlace solo **(M)** | — | 2 100 y 2 200 | 12,6 % y 13,2 % |
| solo la I-cache, sin D-cache **(M)** | 17 900 | 15 773 | 94 % |
| el ejecutor de D5.1 **(M)**, sin región MPU | 8 000 | 8 167 | 48 % |

(Con la D-cache vaciada, el desglose del `DWT` da 2 592; el medidor del hilo, 2 778 —el medidor tiene un artefacto que reconoce `EN-PLACA.md` en el barrido de 32 KB—. Un barrido de 8 o 16 KB entre tics no cuesta nada medible; de 32 KB, 2 699; de 64 KB, 2 592. **La columna de 6 ranuras es aritmética sobre las medidas de 1 y 3**, no una medida: el coste por ranura baja ~230 ciclos de una a tres, así que seis deberían costar algo menos. El `SET` de dieciséis (103 bytes) no está medido: ocupa más de un periodo a 6,25 MHz.)

**El CRC del sobre de la subida**, que la ficha 1 cuenta y no está escrito ni medido (#267): a unos 5 ciclos por byte **(E, sin fuente; la pendiente medida del enlace es 5,1 ciclos por byte, y no es un CRC)** suma de 125 a 350 ciclos. Entonces, con el régimen de caché del hub:

| | enlace + CRC (A, E) | % de un núcleo con 6 ranuras |
|---|---|---|
| caché caliente | 2 092 a 2 317 | **12,6 a 13,9 %** (margen de 183 a 408 ciclos bajo los 2 500) |
| caché fría, base del medidor | 2 903 a 3 128 | **17,4 a 18,8 %** |
| caché fría, base del `DWT` | 2 717 a 2 942 | 16,3 a 17,7 % |

**Todas las variantes con la caché fría pasan del 15 %.** Hay que decidir y declarar el régimen en el censo (R-H4, R-H6). **Palancas conocidas, sin gastar:** esperar **un** `T_SCK` para las seis ranuras en vez de uno por ranura (128 ciclos cada uno; ~107 por ranura y giro, E, ~5 %) y quitar atómicos del camino; poner el texto y los estáticos del J2 en TCM, que quita la dependencia de la caché fría y de la XSPI (no medido). Ninguna cambia por sí sola el veredicto de la caché fría.

## 4. Lo que se probó

### 4.1 Host (`core`)

`Transporte`: todas las filas de §2.2 con sus bordes, y propiedades al azar (una ranura nunca se arma sobre una `Armada`; los contadores se conservan; la recuperación vuelve a `Libre` o a `Muerta`, nunca se queda). `Triple`, `Anillo` y `Subida` con intercalaciones al azar y por mutación; `Reloj64` contra un contador verdadero; `marcos_j2`, nueve mutaciones, todas con una prueba en rojo (mensaje del commit `452313e`). 346 pruebas unitarias de `core` y 59 de integración.

**Lo que el host no cubre:** la independencia de las seis ranuras (H-1). La prueba `seis_ranuras_son_independientes` compara seis `Transporte` sin acoplamiento y no puede fallar: el acoplamiento está en `fw::escala()`, fuera del modelo, y las dos propiedades al azar corren sin `declarar_vencida`. **Hace falta un modelo con el acoplamiento** (§5.2). La revisión del código corrió modelos transliterados del Rust con dos ranuras (más de tres millones de estados, cero violaciones; según su informe), y la segunda pasada, con seis y la máquina real: 1 000 s simulados de fallos mezclados, 36 303 plazos y 36 303 recuperaciones, cero violaciones (Halberg).

### 4.2 Banco, con esclavo real (SPI5 maestro, SPI4 esclavo)

| Prueba | Resultado |
|---|---|
| Soak, 600 s a 8 kHz, patrón regular, pines a `VeryHigh` | 4 799 999 giros, subidas, tramas y bajadas buenas; cero plazos vencidos, subidas malas, tramas cortas, tics tardíos, eventos y subidas perdidos |
| `tic_estres`: marcos numerados en los dos sentidos, golpes de **P3** de 10 a 280 µs, cuelgues y errores del DMA al azar; **una ranura con esclavo, 25 bytes, pines a `Medium`** | 4 × 60 s: 1,9 millones de marcos, 11 570 cuelgues, 2 963 errores del DMA, 14 533 recuperaciones; 4 × 150 s: 4,7 millones de marcos, 29 209 cuelgues, 7 342 errores del DMA, 36 551 recuperaciones. Ninguna bajada rota, repetida ni atrasada, ninguna subida rota, atrasada ni futura, ninguna ranura muerta |
| `tic_recupera` | un SPI envenenado (123 / 131 / 249 µs); 1 000 incidentes seguidos (1 000 recuperaciones, 1 000 tramas cortas en el esclavo, ninguna bajada mala); un `USEF`; 10 escaladas **forzadas** del GPDMA1 con tres ranuras y sin esclavo, a 33 por segundo (30 plazos, 650 ns); la ranura muerta deja de sellar |
| `tic_cota` | una retención de P2 **a la hora exacta de vencer, con una ranura y sin contenido**: sobrevive a 12 ms, muere con 14 (cotas de 100 y 100) |
| Retención de P2 sin fallo | hasta ~100 µs no cuesta ninguna trama; 300 µs, 1,4 giros por golpe; 3 ms, 23 |
| `tic_contenidos` | 16 contenidos de 25 bytes, 2 500 tramas de cada uno: pines a `VeryHigh` y MISO conmutando, 4 llegan enteros; `Medium`, o MISO quieto, 16 |

**Lo que el banco no ejerce:** un canal del GPDMA que ignore `SUSP` (la escalada es solo forzada; el cierre de la spec «pausando un canal por registro» no lo produce); la **denegación** de la escalada; seis ranuras reales; **mensajes de varios tics con contenido** (`BAHIA` y `SET`, y el `TONO` de 41 B a 6,25 MHz, que son 2 y 3 tics, solo están en el host y en el modelo de Halberg); la duración de la trama con los doce canales activos; el tic fuera de caché o de la XSPI; el `DWT` sin sonda; el `CS` con analizador; el máximo enmascarado y la preempción del hub; el CRC y el compositor reales; un módulo real. **Y el cable:** las comprobaciones de contenido de las corridas anteriores (la de 24 h incluida, del otro transporte) solo valían para un patrón regular, y la causa física del fallo con `VeryHigh` no se midió con osciloscopio.

## 5. Condiciones

### 5.1 Para firmar el diseño (esta pasada)

Las siete fichas de §1. Hecho: la recuperación en placa; el transporte completo contra el esclavo a 8 kHz y con marcos numerados; la **medida** de `carga_j2` con las dos definiciones de la ficha 1 (1 967 sin componer, 2 100 componiendo de mentira); la segunda pasada de la junta. **La fila de `carga_j2.csv` no está hecha:** el CSV no tiene filas del tic y no las tendrá hasta §5.2(a).

### 5.2 Para que el transporte entre en el instrumento

| | Condición | Cómo se verifica |
|---|---|---|
| (a) | `carga_j2.csv` con columna **`transporte`** y una **`regimen_cache`** (`caliente`, `fria`), y `recuperacion_j2_budget.py` y `carga_hub_budget.py` filtrando por ellas. La puerta hoy toma **el mínimo** de cualquier fila a ≥ 800 MHz (el texto firmado dice «falla si una fila lo pasa»): con una fila caliente de 1 967 y otra fría de 2 778 pasa. Debe tomar el peor de los regímenes que el hub declare (R-H4) | la puerta |
| (b) | Una fila de **seis ranuras reales** (seis maestros, sin contenido que comprobar) | `carga_j2` en la Nucleo con SPI3 y SPI6 (hay que comprobar que la Nucleo saque sus pines; si no, el criterio se declara inalcanzable y se sustituye) |
| (c) | Una fila con el **CRC del sobre real** (#267) | `carga_j2` |
| (d) | `tic_estres` con **≥ 2 ranuras con esclavo** (tres pares maestro-esclavo usan los seis SPI; no es la configuración de (b)), con **mensajes de 1, 2 y 3 tics**, 3 × 150 s sin ninguna trama rota, repetida ni vieja | el banco |
| (e) | La **denegación de la escalada** forzada en banco (cuatro seguidas en menos de 1 s, con `umbral_escalada` real); la fase C de `tic_recupera` usa un umbral alto, porque hace 33 escaladas por segundo | el banco |
| (f) | La **duración de la trama con los doce canales activos** (de ella depende la holgura de §2.8) | el banco, con osciloscopio |
| (g) | **R-H8**: el supervisor existe y se prueba «ranura muerta → reinicio» y «planificador retenido → reinicio», con la causa guardada | el banco o el hub |
| (h) | Un **modelo de host con el acoplamiento de la escalada** (`declarar_vencida` entre máquinas, con `PlazoAjeno` y el permiso) que haga cierta o falsa «H-1 salvo escalada» | `cargo test` |
| (i) | Pruebas de la política: `PlazoAjeno` no puntúa, `Reiniciar{escalar}` respeta el umbral, `Umbrales::nuevos` rechaza `umbral_escalada` ≥ `umbral_inestable`; pruebas de la máquina: identidad retirada en cada estado, `SUCIA`, precedencias, periodos > 1 | `cargo test` |
| (j) | **Cotas en µs** con su aserto en `lanzar` y leídas por `recuperacion_j2_budget.py`; `para_canales` con la doble cota; el tic con el reloj reconstruido y su fallback | `cargo test`, el banco |
| (k) | El **censo con la tabla de obligaciones de tiempo** (R-H6) y una puerta que lea los `set_priority` del binario del instrumento (R-H1) | la puerta |

### 5.3 Para fabricar (R-MJ8)

El soak de 24 h a 8 kHz con este transporte, con **contenido numerado** (no un patrón regular), con `escaladas_gpdma = 0` y `ranuras_muertas = 0`; la columna `transporte` en `resistencia_j2.csv`; el primer **prototipo del arnés** pasando R-H7; el supervisor en su configuración de producción (R-H8).

### 5.4 El censo

R-H6 cierra o no el 15 %. **Ya no bloquea el transporte** —firmar la ficha A lo dice—, pero bloquea saber si 12,6 a 13,9 % (o el 17,4 a 18,8 % en frío) cabe, y las obligaciones de tiempo de R-H1 a R-H4 no caben en una fila de ciclos por segundo.

## 6. Censo de la spec: qué se toca y qué no

| Pieza | Estado | Qué |
|---|---|---|
| D2 | **reescrita** | las esperas son estados; el EOT se lee en el tic; orden de cierre; `CR.EN` en cero por construcción |
| D3 | fórmula igual; vigilancia en tics | **techo de recuperación medido**; el plazo efectivo en µs es `125 − posición − δ`, no la fórmula: el criterio «≥ 3× el peor exceso medido» (riesgo 2) lo sustituye el presupuesto de §2.8 |
| D4 | **reescrita** y **enmendada** | `T_CANAL` con doble cota; `SUSPF` o `IDLEF`; **permiso de escalada** (§2.5); la enmienda del 18-09 «el IWDG deja de ser la cobertura del riesgo 6»: **vuelve a serlo para el estado terminal** (§2.11) |
| D4.8, D6 (`P(golpe perdido) = 3 × P(EVENTO)`) | **a recalcular** | medido, un `NADA` pierde 2 giros por recuperación; circulan 3 (spec), 4 (`recuperacion_j2_budget.py`), 5 (v2) y 2 (M) |
| D5.1 (1) | **reescrita** | una máquina por ranura movida por un tic. «Un cuelgue en una no ensucia la ventana de las demás» vale otra vez con `PlazoAjeno`, **salvo el cruce de la escalada, que se acota y no se elimina** |
| D5.1 (3) | **reescrita** | niveles; el aislamiento de H-9 se cambia por R-H1 |
| D5.4 | enmendada | «una ranura reiniciando también está viva» deja de ser cierto hasta ~37,5 ms (la ventana del supervisor lo absorbe, R-H8) |
| D7 | **enmendada** | `PlazoAjeno`, `Reiniciar{escalar}`, `umbral_escalada`; «gira siempre» → «salvo ranura muerta»; «lo que NO decide: qué hace el instrumento con una ranura `inestable` o `muda`» sigue siendo del supervisor |
| D8 | **enmendada** | el driver deja de ser genérico; la salida upstream de D8.2 pierde su sujeto |
| R-C8 | **enmendada** | un solo escritor del *contenido*; la cadencia y el `T_GAP` tras recuperar son del transporte |
| R-MJ2 | reescrita | §2.2, con las excepciones de `Libre` sin bajada y `Muerta` |
| R-MJ3 | seis pasos, otros | |
| R-MJ4 | constantes nuevas | `T_CANAL`, `T_GAP_REARME`, las cotas en µs, `umbral_escalada`, el presupuesto de 60 µs: **en `Umbrales` o en una estructura con aserto** |
| Enmienda del 16-10 | acotada | `Calendario` y `atrasos` desaparecen; el reparto de 15 % y el IWDG desde el hilo siguen |
| Enmienda del 18-09 (R15, `Ticker::reset`) | derogada | §2.9 |
| Cierre del riesgo 6 | **a reescribir** | «pausarlo por registro desde otra tarea» no produce un canal que ignore `SUSP`; el criterio es inejecutable en banco |
| D2, D4 y D8 | firmadas «sin matiz» | **se reescriben**: no hay ficha por separado; la ficha A las arrastra |
| §10, filas del hub | pasan a **R-H1 a R-H9** | |

## 7. Lo que sigue abierto

- **Las siete fichas** (Samuel).
- **El CRC del sobre y el compositor reales** (#267): lo que decide si 12,6 a 13,9 % se mantiene.
- **El régimen de caché del hub y las otras diez filas del censo.**
- **Seis ranuras reales** y la concurrencia con contenido.
- **Una escalada de verdad:** nadie ha visto un canal del GPDMA que ignore `SUSP`. Sin esa tasa, `umbral_escalada` = 3 es ESTIMADO sin base.
- **Declarar vencidas solo a las vecinas en vuelo** (no a las que ya completaron): mejora opcional de §2.5.
- **Opciones D y E de la primera pasada** (un solo `Timer` para las seis; el hardware haciendo el giro): no se han medido ni se han cerrado.
- **`cierra()` en la rama `error_dma`** va contra el orden obligatorio del RM; la rama corre y se recupera.
- **`programa()` no reescribe el estado global del GPDMA** (`SECCFGR`, `PRIVCFGR`, `RCFGLOCKR`): inocuo con los valores de reset del banco.
- **Los ESTIMADO que quedan:** `T_CANAL` = 25 µs, `T_GAP_REARME` = 2 µs, las cotas de 25 y 12,5 ms, `umbral_escalada` = 3, el presupuesto de 60 µs, el CRC a 5 ciclos por byte, el supervisor (5 ms) y el IWDG (60 ms) de la simulación.
- **La causa física del fallo del cable** (R-H7) y la **ventana del arranque del cerebro** (S-10).

## 8. Registro: de v2 a v3 (revisión del código)

`H` = hallazgo de `junta_halberg_codigo.md`.

| Hallazgo | Resolución |
|---|---|
| H1, cotas de 2 y 4 tics | 100 y 100 medidas; en µs y 25 + 12,5 ms propuestas (§2.5, ficha C) |
| H2, evidencia con contenido fijo | marcos numerados, golpes y cuelgues al azar (§4.2) |
| H3, reloj de 32 bits | `Reloj64` y reloj reconstruido (§2.7) |
| H4, escaladas sin tope y daño colateral | **permiso de la política y `PlazoAjeno`** (§2.5, ficha B); el presupuesto con sentencia, retirado |
| H5, la escalada solo forzada | límite dicho (§4.2, §7); prueba de denegación (§5.2e) |
| H6, `para_canales` sobre una muestra vieja | una última lectura y doble cota (§2.5) |
| H7, un tic tarde y la XSPI | presupuesto de 60 µs y sus testigos (§2.8), R-H4 |
| H8, `CR.EN`, orden de acceso, `error_dma`, `TR3` | §2.3, §2.5, §7 |
| H9, acoplamientos del banco | §4.2, §7 |
| el cable del banco | R-H7, ficha F |

## 9. Registro de la segunda pasada de la junta

`S` = Serrano, `H` = Halberg, `V` = Voronov (`junta2_*.md`). Los cuatro mecanismos nuevos (§2.2, §2.5, §2.7, §2.11) responden a varios hallazgos a la vez.

| Hallazgo | Resolución en v3 |
|---|---|
| S1 (BLOCKER), V-F11: la ficha A contradice el acta | ficha A reescrita: **dice que revoca la frase**, con el árbol del censo y la tercera hoja; §5.4 |
| S2: el costo del «Sí» no figura; D y E sin cerrar | costos en la ficha A; D y E declaradas abiertas (§7) |
| S3, H12, V-F8: «`Muerta` ⇒ IWDG» sin dueño | R-H8 y §2.11; condición §5.2(g); la ventana del supervisor frente a los 37,5 ms |
| S4, H1, H6, H4, V-F4, V-F5, V-F6: el presupuesto de escaladas | **retirado**; permiso de la política, sin sentencia, muerte solo por la cota existente (§2.5); ficha B separada de las cotas (C) |
| S5: artefactos audibles | §2.10 |
| S6, H7, V-F3: el atraso, `TONO`, la causa de `PlazoVencido` | §2.8 (el tic tardío puntúa, por diseño); tabla de plazos corregida (§2.4); `PlazoAjeno` (§2.5) |
| S7: la cadena de latencia | ficha E; §2.6 con la aritmética |
| S8: la puerta y la fila «hecha» | §5.1; §5.2(a) con la estadística y el régimen de caché |
| S9: «12,6 a 13,9 %» | §3 con el CRC en frío y la nota de la fuente del 5 ciclos/byte |
| S10: cifras sin estatus | leyenda (M), (A), (E) en todo el papel; correcciones de `ldm`, 249 µs, 146 ciclos, `T_CANAL` |
| S11, H8, H10, V-F2: las cotas y su unidad | cotas en µs con aserto (§2.5); R-H1 con la ventana de inanición; tics reconstruidos (§2.7) |
| S12, H3, H13: condiciones imposibles o inverificables | §5.2 con configuraciones, criterio y verificador |
| S13: R-H7 circular, 34,5 MHz | ficha F: primer prototipo del arnés, divisores de `pclk2` |
| S14, H2, V-F7: la tabla incompleta, `SUCIA`, el estado de la ranura | §2.1 y §2.2 |
| S15, V-F10, V-F12: frases de la spec, R-C8, columnas del censo | §6 ampliado; R-H6 con la tabla de obligaciones de tiempo |
| H5: `recupera()` sobre una ranura muerta | §2.2 |
| H9: el testigo no mide el presupuesto | `tics_fuera_de_presupuesto`, `latencia_plan_max_us` (§2.8) |
| H11: el daño colateral | `PlazoAjeno`; la mejora opcional (§7) |
| H13: universalidad de la evidencia | §4.2, §5.2(d)(f) |
| V-F1: tic, periodo y plazo | §2.7 |
| V-F9: la muerte no llega al contrato | `Cuentas` con `muerta` (§2.8) |
