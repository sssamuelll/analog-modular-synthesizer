# Voronov, lente ontológica, junta del 2026-10-17 (transporte del J2)

**Lectura.** Leí el brief, el papel-v1, la spec del 09-03 completa (D1-D8, §9-§12), la cabecera (R-C8, D6, §4, §7), `maestro_j2.rs`, `j2_isr.rs`, `j2_ejecutor.rs`, `j2_spi.rs`, `j2_esclavo.rs`, `carga.rs`, EN-PLACA (`carga_j2`), `recuperacion_j2_budget.py`, los dos CSV y `embassy-stm32/src/dma/gpdma/mod.rs` en el rev del `Cargo.lock` (697ec64). No ejecuté nada ni toqué la placa. Cada hecho lleva archivo:línea. Lo que es inferencia lo marca [inferido].

**Antes de demoler.** El papel acierta en tres cosas que aquí no se discuten: el coste está en los accesos y no en las instrucciones, la recuperación va por debajo del tic y de los EOT, y sus HUECOS están dichos. Lo que sigue no juzga si A cabe en 2 500 ciclos. Lee qué es lo que A intenta caber, y qué palabras del papel designan dos cosas.

## Veredictos

1. Periodo y tic son una cosa vista dos veces. Plazo y tic son dos relojes que P2 obliga a ser uno. «Giro» ya no es un instante sino un proceso repartido entre tres manejadores, y nombra cuatro objetos distintos en el corpus.
2. El canal del GPDMA pasa de un dueño que dice el tipo a tres sin protocolo: el token, el manejador de embassy y el transporte. La escalada D4.2 solo era aceptable bajo una clausura que el banco ya rompió: el esclavo comparte el controlador y usa la misma escalada.
3. El transporte depende del planificador para vivir (`Cerrando → Libre`), y el planificador no existe. `Transporte` no es una abstracción nueva: es la reificación de una máquina que ya existía como futuro, y al repartirla crea tres estados que esperan sin plazo. La frontera escrita en D8 no es la que el código practica.
4. `Calendario` sostenía tres cosas que nadie escribió: una referencia al plan, un hueco medido desde el fin del trabajo y una sola base de tiempo.
5. A' no es una opción sino un parámetro de A. La bifurcación real es si queda una continuación implícita en la vida de la ranura.
6. La restricción invisible es la clausura. Cada garantía del J2 está escrita para un sistema cerrado y se despliega en uno abierto, cuyo censo está debido desde el 10-09.

## 1. La restricción invisible: la clausura

Cada garantía del J2 está escrita como propiedad de un sistema cerrado: seis ranuras independientes (H-1), un presupuesto propio (2 500 ciclos), canales de DMA propios (D4.2). Valen solo en el sistema abierto que el hub todavía no es: un núcleo, una caché, un NVIC, un GPDMA1, una puerta de reloj y un PRIMASK, compartidos con un censo que se debe desde la firma del 10-09.

El brief lo nombra como hueco de presupuesto (§3.3.5, «el censo de CPU del hub no existe»). No lo nombra como hueco de *definición*: sin censo, «el coste del J2» no es una propiedad del J2.

Cinco caras, todas verificadas en el repo:

1. **El medidor define al J2 por su sombra.** `carga.rs:12-15`: el «J2 entero» es lo que el hilo no usa, y el hilo es un contador que da vueltas con `yield_now`. El medidor «no separa a quien se la come». El vecino contra el que se mide es el menos exigente que se podía escoger. EN-PLACA:705-710 ya ve la costura: unos 1 700 de los 8 000 ciclos no caen en ninguna función, y se atribuyen (sin medir) a «cachés frías» del hilo al volver, con un hilo que no toca nada. Con la SRAM a 80 ciclos el fallo y 1,1 el acierto (`costes_bus`), el número depende de qué desaloje el vecino y no de lo que escriba el J2.
2. **El controlador es suyo por un `grep`.** `j2_spi.rs:816-819` acota el radio de la escalada con «`grep -rn GPDMA1_CH src/` fuera de este archivo da cero». Hoy no da cero: lo contienen `j2_banco.rs`, `j2_esclavo.rs` y cuatro binarios. Lo que sigue cierto es que todos son del J2: el banco, no el instrumento.
3. **El NVIC no tiene registro.** `j2_ejecutor.rs:36-39`: «Los dos números concretos (`P1` y `P2`) los elige esta tarea y no hay papel que los fije». Fuera de `j2_*`, el único `set_priority` de `fw/src` es el del muestreo (`muestreo.rs:151`, P0). El vector del ejecutor, GFXTIM, está prestado. El papel-v1 añade un P3 y otro vector software al mismo espacio. La fila «hub N657, los ejecutores» sigue `pendiente` (spec §10, línea 581; §12, línea 660): es lo que el censo de GPDMA y prioridades (#150, punto 2) tenía que escribir.
4. **La puerta de reloj no reconoce inquilinos.** `j2_spi.rs:788-791`: la escalada resetea porque GPDMA1 no lleva cuenta de referencias y `disable` «apaga el reloj sin preguntar». El controlador es reseteable precisamente porque no sabe que tiene más de un usuario.
5. **Debajo de las prioridades hay un mutex global.** `j2_spi.rs:762-767`: `resetear_por_rcc` corre en sección crítica. La recuperación de una ranura enmascara las seis, y H-1 está dicho un nivel por encima de donde eso ocurre.

**El error de categoría que lo oculta.** «El J2» designa tres objetos:

- la lista de mecanismos de la firma («ISR, despacho del ejecutor y DMA»);
- el complemento del hilo que mide `carga.rs`;
- la función «mover 48 000 tramas por segundo».

A cambia el mecanismo y deja la función. Con el ejecutor fuera, la primera lectura se cumple vaciando un término. La segunda cuenta el planificador de P3. La tercera no tiene censo. La pregunta del brief (¿entra el planificador?) no tiene respuesta porque el sujeto de la frase firmada no está definido.

**Las dos posiciones.** Quien lleva A hasta 2 500 trata el número como propiedad del J2. Quien propone B lo trata como propiedad de la asignación. Ninguna cuestiona que esté definido.

**Ley.** Un presupuesto es componible solo sobre un recurso particionado o con censo escrito. Sobre uno compartido y sin censo, el coste de cada inquilino es función de los demás, y el límite no es un límite: es una opinión con unidades.

**Presión.** El día que el primer vecino real toque la caché (la pantalla, el USB), el número medido dejará de pertenecerle al J2 sin que cambie una línea suya. El límite se habrá violado sin que nadie lo incumpla.

## 2. «Giro», «tic», «periodo», «plazo»

- **Periodo** es una duración (125 µs), propiedad del calendario. **Tic** es el suceso con que esa duración se realiza en TIM7. Son una cosa vista dos veces, la cantidad y el suceso, y es legítimo.
- **Plazo** es la cota de *una fase* (`Armada`) de un mensaje: 70 µs un `NADA`, 162 un `BAHIA`, 226 un `SET` (D3 con el SCK real de 8 MHz). Es un reloj causal, relativo al armado, no de calendario.
- **Giro** es un proceso, no un instante ni una duración. En A es la traza `Libre → Armada → Cerrando → Libre`, repartida en tres manejadores y dos niveles, con dos cotas distintas: el plazo sobre el cable y el periodo, implícito, sobre el ciclo entero. El corpus lo usa para cuatro objetos:
  - la trama que se cloca a `F_SUBIDA` (cabecera D6.3);
  - una vuelta de tarea «y todo lo que la tarea hace con él» (`Calendario`, D5.1);
  - solo el cable (`Ranura::giro`);
  - la traza de A.

  El límite lo cobra por ranura (6 × 8 kHz = 48 000/s) y el medidor lo mide por manejador más la pérdida del hilo.

**Plazo y tic no son la misma cosa vista dos veces.** La nota del 19-09 eran dos desigualdades de una misma premisa falsa (103 > 100 y 226 > 220). Aquí son dos relojes que P2 obliga a ser uno. El plazo deja de ser un suceso y pasa a ser un predicado evaluado en el tic, y se redondea a la rejilla: 125 µs para un `NADA`, 250 para un `BAHIA` o un `SET`. La fórmula de D3 sobrevive como especificación y desaparece como mecanismo; «por mensaje, no global» queda en dos valores.

El papel presenta P1/P2 como una decisión de coste de código (§2.4). Es una decisión de categoría: si el plazo pertenece al mensaje o a la rejilla. Con P2, `plazos_vencidos` (la columna que certificó el soak) cambia de significado (§2.4: «cuenta menos que con P1»).

**El tic carga cinco oficios:** instante de armado, muestreo del plazo (P2), detector de pérdida, liberador de las ranuras recuperadas y barrera de las seis. Tres son de control y dos de medida. Una ISR que controla y mide a la vez no puede ser testigo de su propio retraso (ver §5).

**`tics_perdidos` cuenta dos causas con culpables opuestos.** `Armada + Tic + plazo no cumplido` es lentitud del módulo o del cable. `Cerrando + Tic` es que el planificador no llegó. El 16-10 firmó que un atraso «es un fallo del presupuesto de CPU, no del módulo» y que no mueve `inestable` ni `muda`. §2.7 del papel dice que `atrasos` «pasa a» `tics_perdidos` y describe solo la primera causa. La distinción que costó una enmienda se pierde en un contador.

**Tres estados esperan sin plazo.** §1 del papel dice que R-MJ2 queda «igual: cada estado de espera tiene su plazo». La tabla de §2.2 tiene tres estados que esperan a otro nivel:

- `Cerrando`, que espera a `Consumida`;
- `Vencida`, que espera a que P3 corra D4;
- `Reiniciando`, que espera a `ReinicioHecho`.

Ninguno tiene plazo ni salida de fallo, y `Cerrando + Tic` cuenta y se queda. Es el estado absorbente por el que la junta del 09-03 mató al vigía (spec §11, fila del vigía), y contradice el título de D3 («Toda espera tiene plazo»). La espera cambió de dueño y de nombre: la frase de R-MJ2 sigue cierta de su referente original y es falsa del nuevo.

**Ley.** Un plazo y una rejilla son relojes distintos. Fundirlos convierte la detección en muestreo y el contador de fallos en contador de rejilla.

**Presión.** Un mensaje de más de 52 bytes a 8 MHz (`BAHIA`, `SET`) tiene un plazo que cruza un tic. Un `SET` en la sexta ranura deja unos 14 µs entre su EOT y el tic siguiente (125 − 8 − 103, cifras del propio papel) para todo lo que P3 tenga que hacer por las seis ranuras. Cualquier retraso mayor deja la ranura `Cerrando` y sube `tics_perdidos`, y el instrumento no puede decir si falló el módulo o la CPU.

## 3. El dueño de cada canal del GPDMA

**Hoy** el dueño es uno y lo dice el tipo. `Ranura` posee un `dma::Channel` (el `Peri` de `GPDMA1_CHn`, atado a su IRQ por `bind_interrupts!`). Un `Transfer` lo toma prestado por giro, y su `configure` reescribe el canal entero cada vez. El canal no tiene estado entre giros.

**En A tiene tres dueños** (verificado en la cota y en embassy 697ec64):

- **El token.** La cota conserva `Ranura::nueva`, con su `Channel::new` y su `Binding<…, dma::InterruptHandler<…>>` (`j2_spi.rs:299-300`, `j2_banco.rs:80-87`). Guarda la ranura viva «para sus pines» y le toma `partes()` (`j2_isr.rs:149-150`). Es un cascarón.
- **El manejador de embassy.** `embassy_stm32::init` desenmascara los dieciséis canales (`gpdma/mod.rs:526-534`) y el manejador sigue atado.
- **El transporte.** Escribe `pac::GPDMA1.ch(num)` con `num` literal (`CANAL_TX = 0`, `CANAL_RX = 1`, `j2_isr.rs:49-50`). El enlace entre token y registro pasa a ser una convención en un `usize`. Lo que el compilador comprobaba (un canal, un dueño; `CanalGpdma1` contra el HPDMA1) deja de comprobarse.

**Se pisan en cuatro sitios:**

1. La cota enciende `USEIE`, `DTEIE` y `SUSPIE` (`j2_isr.rs:115-120`) mientras su cabecera dice «no hay ISR del DMA».
   - El manejador de embassy hace `panic!` ante `DTEF`, `USEF` y `ULEF` (`gpdma/mod.rs:561-581`). El primer error de un canal es un reset del chip, que es lo que D4 existe para evitar, y el `errores_dma` de la cota no puede contar nunca.
   - Ante `SUSPF` escribe `ch.cr().write(|_| {})` (`:610-613`). La primera suspensión de D4 borra el `CR` «programado una vez». El paso 6 de §2.5 lo rehace, pero entonces «programado una vez» no es el estado del canal sino su estado *entre* recuperaciones.
2. El inventario de interrupciones de §2.1 (tic, EOT, P3) omite las doce líneas de canal. Sin `bind_interrupts!` serían el `DefaultHandler` de `cortex-m-rt`, que `j2_spi.rs:467-470` describe como un bucle infinito. Con él, el dueño es embassy. No hay tercera opción escrita.
3. Un canal programado una vez es un **caché de la intención**. Su invalidación está escrita para un solo escritor: la escalada propia (`canales_sucios`).
   - Cualquier otro que resetee GPDMA1 no la activa. `soltar_canales` la usa también el esclavo del banco (`j2_esclavo.rs:666`), cuya escalada resetea el controlador de las seis ranuras del maestro. Es el segundo inquilino, y está en el banco donde se prueba A.
   - El banco ya tuvo que escribir una resta para saber quién resetea a quién (`j2_esclavo.rs:229-249`). Es la contabilidad de un recurso sin dueño.
4. Para los vecinos que usan `Transfer` de embassy, el reset es una finalización falsa. `Transfer::poll` resuelve cuando `is_running()` es falso (`!suspf && !idlef`, `gpdma/mod.rs:912-919`, `1298-1313`) y tras el reset el canal está `IDLE`. La transferencia ajena se da por hecha sin haberse hecho.

**La escalada es un cruce de jurisdicción.** D4.2 es una acción autorizada por una ranura cuyos efectos caen sobre todos los usuarios del controlador. Su radio solo era aceptable bajo la clausura de §1.

Choca además con la regla firmada el 11-09, «cero artefactos audibles atribuibles al bus» (spec §9, enmienda del 11-09, punto 2). Si el escritor de CV comparte el controlador, cada recuperación escalada del J2 es un artefacto audible por construcción. El papel lo deja como pregunta (§6, cuarta viñeta).

«El riesgo 6 se cierra por construcción» (papel §1) es falso tal como está escrito. Se cierra el `Drop` sin cota, que la enmienda del 18-09 ya había acotado con `T_CANAL`. Queda la escalada, ahora sobre canales con estado.

**Ley.** Todo sistema que reclame recuperación sobre un recurso compartido debe responder, para ese recurso, tres preguntas: quién lo posee, quién puede invalidarlo y qué ve cada inquilino al invalidarse. El J2 responde la primera en el sistema de tipos y las otras dos en un comentario.

**Presión.** El primer reset de GPDMA1 por un inquilino que no sea el maestro dejará los doce canales en valores de reset sin que ningún bit lo diga. El tic siguiente armará seis ranuras sobre canales vacíos. El síntoma serán seis `plazos_vencidos` simultáneos, sumados a las marcas de salud de seis módulos sanos; o, si el DMA toca una dirección que el reset dejó en cero, un `DTEF` que embassy convierte en panic [inferido]. Después D4, ranura a ranura y seriada en P3, lo repara.

## 4. La frontera transporte / planificador / política

**Quién escribe qué, según el papel-v1:**

| Escritor | Nivel | Escribe |
|---|---|---|
| Tic | P1 | SPI y GPDMA de las seis; `Libre→Armada`; sello; lee el buzón y la identidad |
| EOT (×6) | P1 | SPI de su ranura; `Armada→Cerrando`; `eot_tardios`; el pendiente de P3 |
| Planificador | P3 | buzón de bajada; `Cerrando→Libre`; `core::Ranura`; cuentas |
| Recuperación | P3 | SPI, GPDMA, RCC; `Vencida→Reiniciando→Libre`; `canales_sucios` |

El estado de una ranura tiene cuatro escritores en dos niveles. El cable lo escriben tres: el tic (`CSTART`), el EOT (`SPE = 0`) y la recuperación, que rompe el `CS` a mitad de trama y consume una `secuencia`. El único que R-C8 nombra, el planificador, no escribe el cable: escribe un buzón.

**R-C8 dice tres cosas** (cabecera:803-806) y el papel dice «igual»:

- *un solo escritor*, «el planificador **de la ranura**». En A es un lazo de P3 sobre las seis, no uno por ranura.
- «Cambio y refresco salen del mismo estado». El buzón es una segunda copia del estado, con una ventana de validez de hasta un periodo.
- «`T_GAP` lo pone él». Desde el 18-09 lo ponía el `Calendario` (`j2_ejecutor.rs:380-392`); en A lo pone la rejilla. En ningún caso el planificador.

R-C8 es «doctrina… sin puerta» (cabecera:805) y sigue siéndolo.

**El planificador no existe.** `Bajada` y `Juez` son dos punteros a función, y «el real llega cuando exista la cabecera en código (#267)» (`j2_ejecutor.rs:64-69`). La frontera que el papel traza, lo que sube a P3 y lo que queda en P1, se dibuja alrededor de un habitante sin implementación, sin coste medido (HUECO, §6) y sin puerta.

**La inversión.** En D5.1 el planificador es un *callee*. La tarea llama a `bajada_fn` al armar y a `juez` al cerrar, en su contexto, y el `Calendario` cobra ese tiempo al giro. En A pasa a ser un *productor con reloj y prioridad propios* que empuja a un buzón. Y el transporte depende de él para su vivacidad: `Cerrando → Libre` solo sale con `Consumida`.

Cambiar de llamada a evento no elimina la dependencia, elimina su contabilidad. «Lo que va a P3» se define por forma («lo que no cabe en P1»), no por clase. P3 es un complemento, no una categoría. El CRC del sobre y el reinicio del SPI comparten nivel porque ambos son lo que sobra, y se serializan: un CRC de 103 bytes retrasa la recuperación de otra ranura, y viceversa.

**El buzón no tiene semántica tras un fallo.** La tabla de §2.2 no tiene fila que lleve a una ranura de `Reiniciando` por el planificador. Tras un plazo vencido, la ranura vuelve a `Libre` sin que nadie componga la bajada siguiente, y el tic «toma del buzón la bajada que dejó el planificador» (§2.3). La tabla no dice si el buzón conserva la bajada abortada o está vacío.

- Si la conserva [inferido de cabecera §3.3 y D4]: misma `secuencia`, un `EVENTO` que sale dos veces, y `perdidas < rechazadas`, que la cabecera declara imposible (`perdidas ≥ rechazadas`, cabecera:698-700).
- Si está vacío: el tic no tiene qué armar.

En D5.1 la pregunta no existía: cada armado iba precedido, por estructura de código, de una llamada a `bajada_fn`.

**¿`Transporte` es una abstracción real?** Es real, pero no es nueva. `tarea_ranura` más `giro` ya eran una máquina de estados con dos puntos de espera (el calendario y el cable), escrita como futuro. A la reifica en un `enum`, y al reificar no conserva la máquina: la subdivide.

`Cerrando`, `Vencida` y `Reiniciando` no existían en D5.1 porque cerrar, juzgar y recuperar eran código síncrono de la misma tarea, entre dos `await`. A los parte entre niveles. Por eso son estados, y por eso esperan (§2).

Hay una segunda consecuencia. Un futuro tiene un solo escritor, porque nadie sondea una tarea que no sea ella misma. Un `enum` en `static` tiene los cuatro de arriba. La exclusión mutua que el generador daba por construcción tiene que salir de otro sitio:

- En el papel sale de que tic y EOT comparten nivel (P1), que es una propiedad del NVIC y no del tipo.
- En la cota, que es lo único medido, el tic va a P2 y el SPI a P1 (`j2_isr.rs:296`, `j2_spi.rs:453`). Es decir, con apropiación.
- «Pura y probada en el host» describe una función secuencial. Los escritores concurrentes no están en el modelo que se va a probar.

**Frente a la política.** La política (`Ranura::paso`) recibe como entradas exactamente las salidas del `Transporte` (`Armada`, `GiroOk`, `PlazoVencido`, `EotTardio`). Es un cociente suyo, una vista. El sistema tendría dos respuestas a «¿reiniciar?»: `Accion::Reiniciar` y `Vencida → Reiniciando`.

Hoy coinciden porque la política devuelve `Reiniciar` siempre (D7.1, test 8), y `tarea_ranura` ya la ignora, «redundante a propósito» (`j2_ejecutor.rs:376-378`). La política es, por decreto, telemetría: cinco contadores y dos predicados. El día que otro papel le dé una decisión real (qué hacer con una ranura `muda`, que la spec delega a «partes y voces»), el transporte reiniciará igual.

**La frontera escrita y la practicada no son la misma.**

- D8 escribe: «`fw` cloca bytes; `core` sabe qué son».
- El código practica: lo puro va a `core`. `maestro_j2.rs` ya contiene `mbr_y_f_sck` y `ciclos_por_cuarto_tsck`, que son aritmética de campos de registro y no saben qué es un sobre.

Bajo la frontera escrita, `Transporte` no cabe en `core`. Bajo la practicada, cabe, y cabe todo lo puro que venga. El papel elige la segunda sin decirlo.

**Lo que se prueba en el host no es lo que falló.** El 14-10 el banco cazó tres defectos del driver (`TXTF`, `CSUSP` seguido de `SPE = 0`, `enable_and_reset` que no resetea). Los tres estaban en registros y en el tiempo entre escrituras, y ninguno es visible a una máquina pura que emite `Armar`. «`fw` solo traduce acciones a registros» deja en `fw` toda la parte que ha fallado, y en `core` la que nunca falló.

Tampoco `fw` adelgaza. La cota guarda imágenes de registro precalculadas (`cfg1_*`, `cr1_*`, `cr_en`, `j2_isr.rs:128-151`) y el papel añade `canales_sucios`. Es estado sombra que hay que mantener coherente con el hardware.

**Ley.** Una capa inferior cuya transición de vivacidad espera un evento de la superior no es independiente de ella. Cruzar un nivel de prioridad cambia cómo se contabiliza la dependencia, no su existencia.

## 5. Lo que `Calendario` sostenía sin que nadie lo escribiera

El 16-10 dijo que arreglaba el `Ticker` que recuperaba tics en ráfaga. Un temporizador de hardware no puede hacerlo, porque un periodo atrasado es un solo pendiente, así que esa razón desaparece gratis. Las que no estaban dichas:

1. **Una referencia al plan, y con ella el testigo del atraso.** `Calendario` guarda `proximo_us`. Sabe cuándo debía ocurrir el giro, y por eso `atrasos` cuenta una vuelta tardía aunque la ranura estuviera libre.
   - El tic de hardware no guarda cuándo debía correr. Si su ISR se retrasa dos periodos, TIM7 funde las dos actualizaciones en un pendiente. Las ranuras `Libre` se arman tarde, el instrumento pierde un giro por ranura y ningún contador sube, porque `tics_perdidos` solo cuenta ranuras ocupadas.
   - Quien elimina la referencia elimina el testigo, no el atraso.
   - La única anomalía del soak fueron cuatro atrasos entre las 10:18 y las 15:20 del 16-10, «no se conoce la causa» (spec §9, enmienda del 11-09, punto 3).
   - A contaría algunas de sus manifestaciones como `tics_perdidos` (las que dejan una ranura ocupada) y ninguna de las que retrasan el propio tic [inferido].
2. **El hueco se medía desde el fin del trabajo, no desde la rejilla.** `giro_terminado(ahora)` y `reanclar(ahora)` ponen el siguiente giro a un periodo de CPU libre. El tic mide desde la rejilla. Tras un reinicio, el hueco para el rearme del esclavo, que `reanclar` garantizaba exacto, pasa a ser lo que reste hasta el tic siguiente.
   - El papel dice que «el hueco de un periodo sale solo» (§2.2).
   - Con P2 sale, porque la detección nace en la rejilla (~100 µs de hueco).
   - Con P1 y un `SET` (plazo 226, reinicio de 20, tic a 250) la ranura 1 se re-arma unos 3 µs después de acabar el reinicio. Según la ranura y el mensaje, el hueco queda entre ~3 µs y un periodo (cifras ESTIMADO del propio papel).
   - `T_GAP` es la latencia de rearme del esclavo bajo carga de audio (cabecera:839-841), sin medir.
   - Que el hueco «salga solo» en una opción y no en la otra es la señal de que no sale solo.
3. **Una sola base de tiempo.** Plazo, calendario y política usaban el mismo `Instant` de embassy. A pone el tic en TIM7, el plazo en `DWT_CYCCNT` (P2) o en un comparador de TIM2/TIM5 (P1), y la política en el `Instant` de TIM12. Son cuatro bases, y nada dice que sean coherentes. Convertir ciclos a µs exige `f_cpu`, que «no sale de `Clocks`» (`j2_spi.rs:55-60`, HUECO 2).

**Ley.** Un testigo de atraso exige una referencia al plan.

**Presión.** Cualquier enmascaramiento del tic de uno o más periodos (la sonda, `defmt`/RTT) producirá un giro perdido por ranura que nadie contará.

## 6. A' es un parámetro de A

El brief lista A' como par de A. El papel-v1 ya lo reduce, sin decirlo, a su última viñeta de §6: «si la recuperación a P3 se queda en una interrupción de software o pasa a una tarea de baja prioridad con `Timer`». El brief define A con «la política, el planificador y la recuperación a un nivel más bajo». A' difiere solo en el contenedor de ese nivel: manejador a término o `async fn`.

Dos precisiones:

- **A ya son dos modelos en una ranura.** Hay un reactivo a término en P1 (tic, EOT) y manejadores con esperas síncronas acotadas en P3 (el sondeo de `T_CANAL`, 10 µs; las compuertas del RCC). «Un modelo contra dos» no separa A de A'.
- **Lo que sí las separa es si existe una continuación implícita.** En A el estado de la ranura *es* su continuación, un `enum`. En A' la parte rara vive en un generador que fabrica el compilador y la común en un `enum`.
  - El estado de la ranura queda partido entre un valor explícito y un punto de `await` implícito.
  - Las reglas 1-3 de D2 (registrar el waker antes de mirar la bandera, `unpend`, generación) nacieron para cerrar justamente esa costura ISR-tarea.
  - A' la reabre en el camino menos ejercido: el soak tuvo cero plazos vencidos, o sea cero pasadas por D4.
  - «D4 sigue siendo un futuro» no es literal. Los `ManuallyDrop<Transfer>` de `reiniciar` (`j2_spi.rs:717-725`) no existen sin `Transfer`. Del futuro sobrevive el envoltorio, y con él el ejecutor, su vector y el reloj de embassy, fuera del camino medido.

**Ley.** Dos modelos de ejecución sobre un mismo estado son un tercer modelo, y sus invariantes viven en la costura.

## 7. Las opciones, reclasificadas

- **A' = A** con un parámetro (§6).
- **D.** El veredicto numérico es coherente: los intervalos 1 700-2 200 contra 3 900-4 400 no se tocan, aunque los dos son sumas ESTIMADO de partes de perfil, del mismo método. Lo que el brief no escribe es la razón de categoría de por qué no se tocan.
  - D conserva una continuación por ranura. Su coste (registrar el waker, encolar, despachar, leer el reloj de embassy a 48 ciclos por acceso) es intrínseco a hacer de la *suspensión* un objeto de primera clase.
  - Quitadas una a una las capas que D conserva (el `Timer`, los wakers, el ejecutor, `Transfer`), lo que queda es la cota. D no es otra arquitectura: es el mismo camino de A recorrido al revés.
- **B y C no son opciones de transporte.** B cambia el requisito (el límite). C cambia la cabecera (8 kHz, `latencia_mano`) o el alcance. El brief las pone en la misma columna que A, D y E y las compara en ciclos. Mezcla dos categorías: qué se construye y qué se pide.
- **E no es «no explorada»: es el extremo de un eje.** D5.1, A y E son tres posiciones sobre quién ejecuta el calendario del J2: el planificador cooperativo, el NVIC o el tejido DMA/temporizador. El J2 es un sistema *disparado por tiempo* (D7.1: nunca deja de girar, sin cadencia reducida, sin backoff) implementado con maquinaria *disparada por eventos*. Lo que se discute es el precio de esa discrepancia, y cada paso del eje la reduce. Ninguna opción pregunta en qué punto del eje deja de ser expresable la recuperación: un calendario puede bajar al hardware, una receta con condicional (D4) no [inferido].
- **Premisa compartida.** Todas salvo E conservan que el núcleo arma cada giro, y que las 48 000 atenciones por segundo son dato. La cota ya consume el 60 % del límite (1 500 de 2 500).

## 8. Evidencia y cifras que no resisten

- **El sujeto del certificado no está nombrado.** `resistencia_j2.csv` tiene `placa`, `instancia` y `reloj`, pero no transporte ni firmware. `carga_j2.csv` tiene `firmware`, pero no transporte, MPU ni planificador. La puerta toma el `min` sobre las filas a ≥ 800 MHz (`recuperacion_j2_budget.py:236-252`).
  - Una sola fila por debajo de 2 500 la pone en verde, y «el transporte completo» (papel §5.1) está solo en prosa.
  - La cota (`j2_isr`) con región MPU, anotada con `--anota`, sería una fila válida para la puerta [inferido].
  - Puerta verde, sujeto incompleto. Un certificado que no nombra a su sujeto no caduca cuando el sujeto cambia.
- **La fila de 24 h no valía para el objetivo ni antes.** Es de 1 kHz, 64 MHz y `pclk`/SCK = 4, con cero pasadas por D4. El brief contabiliza su pérdida como costo de A, pero B también necesita un soak nuevo (8 kHz, 800 MHz, MPU), así que la pérdida es común, no diferencial. Y el sujeto escogió su propio punto de operación: el 1 kHz se fijó porque el transporte no daba para más (spec D5.1, enmienda del 16-10, punto 3).
- **El banco no puede ejercer lo que A afirma.** «La sexta empieza 8 µs después» no tiene banco: hay tres ranuras físicas (brief §3.3.4) y la cota gira una (`GIRO` es un `Option<Giro>`, `j2_isr.rs:153-156`). Todo lo medido es un `NADA` de 25 bytes (`LARGO_BANCO`, `j2_banco.rs:348`); el `SET` es de 103. El «por giro» del límite es un promedio sobre una mezcla de mensajes que ningún papel declara.
- **La cota no mide lo que el papel cita.**
  - En la cota el tic va a P2 y el SPI a P1; en §2.1 ambos van a P1.
  - En la cota el cierre ocurre en el tic (`j2_isr.rs:316-337`); en el papel ocurre en el EOT.
  - Los «~1 100 ciclos por ranura» que fijan los 8 µs de §2.1 incluyen cerrar, juzgar y contar, que en A ya no ocurren en el tic.
- **Aritmética de §3.** 1 500 + 0 + 50 + 100 = 1 650, no 1 700.
- **Contradicciones internas del papel:**
  - §1 dice que las dos esperas de D2 pasan a «dos estados con un plazo», pero §2.2 tiene un solo estado de espera de cable (`Armada`) y ningún evento de «DMA completo». D2 las exigía juntas, y el cierre del manual (§67.4.14) empieza por el lado del DMA. En D5.1 lo garantizaba la estructura (`join` de los DMA, luego `EOT`). En la tabla de A el cierre ocurre en el EOT sin condición sobre el DMA. La cota lo resuelve leyendo `TCF` un periodo después, en el tic.
  - §1 dice «R-C8 igual», y el texto de R-C8 asigna la ranura y `T_GAP`.
  - §1 dice que el riesgo 6 se cierra «por construcción», y §2.5 mantiene la escalada.
  - La fila `Armada | Eot (generación vigente)` evalúa una guarda que la enmienda del 18-09 declaró vacía (el hardware no etiqueta el EOT).
- **Omisiones en la tabla de §1.**
  - **D8.** `j2_spi.rs` es allí un driver *genérico* de SPI, con cláusula de retiro hacia embassy (D8.2: «es su cierre deseable»), y la junta del 09-03 (V-12) lo dejó honesto para que dejara de ser «driver de bus propietario». La cota guarda dentro de `Giro` la política, `bajada_fn` y `juez`: es un transporte *específico del J2*. Con A, la contribución upstream deja de retirar nada.
  - **R-MJ3.** Los seis pasos pasan a siete.

## 9. Lo que no verifiqué

- No compilé ni medí nada. Los ciclos, los ~10/20 µs y los 8 µs son los del propio papel.
- No leí el RM0486. Dejo como pregunta para Halberg qué hace la FIFO de recepción al apagar `SPE` con una petición de DMA pendiente (orden EOT contra finalización del DMA en el cierre).
- No leí la cabecera entera (solo R-C8, D6, §4, §7), ni `j2_banco.rs` ni `perfil.rs` completos.
- Las marcas [inferido] son lecturas mías de tablas y código, sin prueba en placa.

## Cierre

El invariante, para firmar o rechazar: *un límite de recurso se firma sobre un censo, no sobre un inquilino. Mientras el censo no exista, los 2 500 ciclos no son un presupuesto: son la medida del J2 en ausencia de sus vecinos.*

Esto no es un problema de transporte. Es un problema de clausura: el J2 se midió como la sombra que proyecta sobre un hilo ocioso, se presupuestó como una parte de un núcleo que nadie ha repartido y se rediseña como si sus vecinos no fueran a llegar. Mientras «el J2» designe una sombra y no una función, cada transporte cabrá o no cabrá según la luz.

## Archivos citados (rutas absolutas)

Base: `D:\Desktop\projects\sam17\.claude\worktrees\banco2\`

- `docs\superpowers\juntas\2026-10-17-j2-transporte\junta-2026-10-17-brief.md`
- `docs\superpowers\juntas\2026-10-17-j2-transporte\papel-v1.md`
- `docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md`
- `docs\superpowers\specs\2026-09-02-cabecera-j2-design.md`
- `docs\superpowers\juntas\2026-09-11-j2\junta_voronov.md`
- `software\nucleo\core\src\maestro_j2.rs`
- `software\nucleo\fw\src\j2_isr.rs`
- `software\nucleo\fw\src\j2_ejecutor.rs`
- `software\nucleo\fw\src\j2_spi.rs`
- `software\nucleo\fw\src\j2_esclavo.rs`
- `software\nucleo\fw\src\j2_banco.rs`
- `software\nucleo\fw\src\carga.rs`
- `software\nucleo\fw\src\muestreo.rs`
- `software\nucleo\fw\EN-PLACA.md`
- `software\nucleo\fw\resistencia_j2.csv`
- `software\nucleo\fw\carga_j2.csv`
- `hardware\02-midi-cv\recuperacion_j2_budget.py`
- `C:\Users\simon\.cargo\git\checkouts\embassy-21ab002d3f42f557\697ec64\embassy-stm32\src\dma\gpdma\mod.rs`
