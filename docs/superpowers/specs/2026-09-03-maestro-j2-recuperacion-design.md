# El maestro del J2: plazo, reinicio y cuenta, porque el silicio se cuelga

**Fecha**: 2026-09-03 · **Estado**: **v2 FIRMADA el 2026-09-10** · **Sujeto**: el cerebro (STM32N657, hub §S10) como maestro de las seis ranuras SPI del J2 · **Cierra**: #287 (puntos 1 a 3, cerrado) · **Cuelga de**: la cabecera del J2 (2026-09-02), el J2 punto a punto (2026-08-25), voz-total §9.2, el hub N657 (2026-08-30)

---

## 0. Qué es este papel, y qué no

Este papel decide **qué hace el cerebro cuando su propio periférico de SPI deja de responder**, y lo decide antes de escribir el driver, porque hay un defecto abierto en el silicio o en su driver que lo obliga: embassy-rs/embassy#5607, *«STM32N6 SPI Hanging»*, abierto desde 2026-03-05, sin diagnóstico, sin asignado, con la última actividad el 2026-06-24. El #287 trae la evidencia; aquí se diseña la respuesta.

Lo que el #287 destapó, en una línea: **el J2 tiene red de seguridad del lado del módulo y ninguna del lado del cerebro.** El módulo lleva watchdog de trama (voz-total §9.2), silencio por hardware sin CPU (motor-digital R-M5) y un receptor que rechaza entero y cuenta (cabecera D8). El cerebro, como maestro, no tiene nada: ni plazo, ni reinicio, ni cuenta. Un maestro colgado hoy se traduce en el módulo soltando las notas a los ~50 ms, y ahí se queda el instrumento.

Este papel lo arregla desde el marco de un fabricante, no desde el de un proyecto que espera a upstream: **el driver falla, se asume, y la recuperación es nuestra.** Lo que se pide del silicio es lo que el manual de referencia documenta; lo que se pide de embassy es lo que ya expone públicamente; y se dice cuál es la contribución que haría que el driver propio se retirara.

**Lo que NO es:**

- No diagnostica el defecto del N6. No hay Discovery (#231), y diagnosticar desde el sillón es fabricar.
- No rediseña la cabecera ni el punto a punto. El sobre, su CRC, la sesión, los registros de subida y `T_GAP` se quedan como están. Este papel les añade un cliente, y les manda dos enmiendas pequeñas (§10).
- No decide qué hace el instrumento con una ranura que reinicia mucho o que no contesta. Marca y sube; la política es de otro papel (§6).
- **Alcance: las seis ranuras SPI.** Las dos ranuras por USART síncrono con `CS` por GPIO que el censo del hub también sostiene (`micro_budget.py`, `HUB_RANURAS_USART = 2`; hub §10.3) son otro periférico con otra máquina de estados, y quedan fuera con su HUECO (§6, §9 riesgo 7). *(⚠ V-8)*
- No toca `pinout.rs`. El reparto de pines del hub es del censo y su reescritura es otra tanda.

---

## 1. Los clientes, con su fuente

| Cliente | Qué pide | Fuente |
|---|---|---|
| El músico | Que un fallo del bus no se oiga. Un cuelgue de 10-900 s de período no puede ser un release cada tanto | La regla del instrumento, y el #287 |
| El módulo de Voz | Que el maestro vuelva antes de que su watchdog de trama dispare | voz-total §9.2: *«sin trama válida en N ms (N del plan, ~50), todos los generadores van a release»* |
| La cabecera del J2 | Que la trama que llega, llegue entera o no llegue; que el CRC del sobre decida | D2: CRC-16/CCITT-FALSE *«de los PRIMEROS 4 + largo bytes»*, computado *«sobre el búfer al subir CS, con la unidad»*; D8: *«Un receptor que rechaza entero y cuenta»* |
| El censo del hub | Que el NSS lo maneje el periférico: `J2:SPI4_NSS=PE11` y equivalentes en SPI1-6 | `micro_budget.py`, hub §10.1 |
| El punto a punto | Que el reloj de cada enlace sea el sancionado, y que el maestro sea constante del cerebro por ranura | D2, D3 |
| El firmware del cerebro | Que la política se pruebe sin placa, en `core`, y que `fw` sea delgado | `fw/src/main.rs:6`: *«Capa DELGADA a propósito»* |
| El planificador del cerebro | Que siga siendo el único escritor del enlace | Cabecera R-C8: *«El enlace tiene un solo escritor en el cerebro: el planificador»* |
| Upstream | Que lo que aprendamos vuelva al hilo #5607 | El precedente de #911 y #6939 |

### 1.1 Lo que el issue dice, contra lo que tenemos *(⚠ filas 1 y 5 corregidas por S-2)*

| Hecho del hilo | Nuestro diseño | Consecuencia |
|---|---|---|
| En modo bloqueante, `RXP` no sube nunca: el maestro escribió, `TXC = 1`, y la recepción no vio nada. Con DMA se cuelga *«waiting for the end of transfer flag»* | El J2 es DMA en los dos extremos | El modo de fallo es **la recepción no termina** (H-1). Un plazo que solo cubra el fin de transferencia no lo ve: tiene que cubrir también la espera del DMA (D2) |
| Sale a 100 kHz y a alta frecuencia | 34,5 MHz (D8) | Bajar el reloj no es salida |
| Pasa con el bus al aire | 74 cm de cinta, sancionados | No es integridad de señal |
| Corrupción: el `CS` sube a mitad, un bit se duplica | CRC del sobre, receptor que rechaza entero | Se detecta; hay que absorberla sin que se oiga (D6) |
| El camino bloqueante y `write`/`transfer` con DMA van con `TSIZE = 0`; **`read` con DMA sí fija `TSIZE`** y también se cuelga | `TSIZE > 0` siempre (D1) | **`TSIZE` no es refugio.** Lo que sí es distinto: el `CS` lo mueve un GPIO en el hilo (`SSM = 1` en su volcado) y aquí lo mueve el periférico. Sin probar |
| Los dos reportantes usan `SPI5`; nadie probó otra instancia | Seis enlaces en `SPI1-6` | Pregunta upstream (§9, acción 1) |
| Escribir a `TXDR` desatasca el caso bloqueante; en DMA no | — | El reinicio es el del manual, no el paliativo |

> **Enmienda del 2026-09-08 (§1.1, alcance):** la premisa «nadie probó otra
> instancia» queda refutada. En [embassy-rs/embassy#5607](https://github.com/embassy-rs/embassy/issues/5607),
> jake-taf, uno de los reportantes originales, respondió el 2026-09-03:
> *«I have observed this problem on SPI1 as well»*. Hay cuelgues reportados en
> **dos instancias, SPI5 y SPI1**. El defecto no es exclusivo de SPI5; esta
> respuesta no demuestra que fallen todas las instancias del bloque ni
> identifica la causa. La pregunta de la fila ya tiene respuesta con ese alcance.

> **Enmienda del 2026-09-08 (§1.1, consecuencia de diseño):** cambiar de
> instancia no es una salida de esquemático acreditada por la evidencia. La
> recuperación es **obligatoria para las seis ranuras SPI**: el plazo de D3,
> los ocho pasos de D4 en su orden, la ventana deslizante y las dos marcas de
> salud de D7. La política vive en `software/nucleo/core/src/maestro_j2.rs` y
> el driver ejecuta la recuperación en `software/nucleo/fw/src/j2_spi.rs`
> (D8). Es un requisito del diseño aun sin diagnóstico, y ninguna ranura queda
> exenta por llevar una instancia distinta de SPI5.

### 1.2 Lo que embassy hace, leído en el código *(⚠ corregido por S-2)*

`embassy-stm32/src/spi/mod.rs`, `main` al 2026-09-03 (copia en el scratchpad de la sesión, 2130 líneas):

- **`read` con DMA** (`spi_v4`-`v6`) fija **`TSIZE = N`** por trozos (`:1332-1342`), arma el DMA de recepción, `SPE = 1`, `CSTART`, espera el futuro del DMA y luego `finish_dma`, que espera `EOT` en un bucle: `while !regs.sr().read().eot() {}` (`:1804-1808`). Al salir vuelve a `TSIZE = 0` (`:1372`).
- **`write` y `transfer`** no tocan `TSIZE`: heredan el `0` del constructor (`:488`) y `finish_dma` espera `TXC`. `transfer_inner` hace `join` de los dos futuros del DMA (`:1499`) y luego `finish_dma` (`:1501`).
- **Ese bucle es síncrono.** No cede al ejecutor. Un `embassy_time::with_timeout` alrededor de la llamada no puede vencerlo. Y el `join` de los futuros del DMA tampoco está bajo ningún plazo: si la recepción no termina (el modo del hilo), la tarea se queda ahí sin que exista siquiera un `TimeoutError` que recibir (H-1). Cuando el N6 se cuelga, **se congela la tarea y todo lo que comparta ejecutor con ella**.
- El SPI de embassy-stm32 **no usa su propia interrupción**: todo es DMA más sondeo. `EOTIE` no aparece en el archivo.
- **Sí maneja NSS por hardware**: `Spi` guarda `nss: CsPinType` (`:321`); `ssm = nss.is_none()` (`:390`); con pin de NSS y maestro, `SSOE = 1` (`:464`).
- **Sí apaga el SPI entre transferencias**: `set_spe(false)` al entrar a cada `write`/`read`/`transfer` y `set_spe(true)` antes de `CSTART`.

De aquí sigue: el driver de embassy tal cual **no sirve para el J2**, no por el defecto del N6, sino porque sus dos esperas no son cancelables. Eso contesta la fila 6 del §10 del hub para el SPI (§10, enmienda).

Lo que sí expone embassy, verificado en `main`, y que el driver propio usa sin tocar nada privado: `rcc::enable_and_reset::<T>()` (`rcc/mod.rs:622`), `dma::Channel::new` (`dma/mod.rs:80`) y `Channel::read`/`write(request, peri_addr, buf, opts) -> Transfer` (`gpdma/mod.rs:934`, `:1004`), el trait `spi::TxDma`/`RxDma` con `fn request(&self) -> Request` público (`macros.rs:162-173`), `embassy_time`, `InterruptExecutor` (`embassy-stm32/src/executor.rs:196`, `start(irq) -> SendSpawner`), y el `IWDG`, que el N657 sí trae (`stm32-data-generated/data/chips/STM32N657X0.json`).

---

## 2. Las decisiones

### D1. Toda transferencia del J2 lleva `TSIZE` y NSS por hardware, y son una sola decisión *(⚠ reescrita: la v1 ataba también el CRC de hardware, y la cabecera ya lo había descartado — S-1, V-1, H-4)*

El manual ata el NSS por hardware al contador. RM0486 Rev 4, §67.4.7, p. 3437:

> *«NSS output enable (SSOE = 1): this configuration is only used when the MCU is set as master. The NSS pin is managed by the hardware. The functionality is tied to CSTART and EOT control. As a consequence, the master must apply the proper TSIZE > 0 setting to control the NSS output correctly.»*

Y §67.4.12, p. 3447:

> *«If a hardware data counter is used (TSIZE bitfield of the SPI_CR2 register set to a nonzero value), the application software does not need to calculate the remaining number of data to be handled. The end of transfer automatically controls the CRC, as well as the hardware slave select management, when used.»*

O sea: el NSS por hardware que el censo ya reparte **no funciona sin `TSIZE`**. Los dos van juntos:

1. **`TSIZE = bytes clocados de la trama`**, la cuenta de la cabecera §4: `largo + 7` (sobre de 4, carga, CRC de 2, cola de 1), rellenada a la ventana del dialecto cuando toca (cabecera D6.3: en la Voz, ≥ `VENTANA_SUBIDA + 1 = 25`). Se conoce por construcción antes de cada transferencia. Nunca `0`. *(⚠ S-14, H-5: la v1 decía «sobre + cola» y omitía el CRC y el relleno)*
2. **`SSM = 0`, `SSOE = 1`, `SSOM = 0`**: el NSS baja con `CSTART` y sube con `EOT`. §67.4.7, p. 3438: *«When SSOM = 0 and SP = 000, the NSS signal is driven to the active level as soon as the master transfer starts (CSTART = 1) and it is kept active until its EOT flag is set or the transmission is suspended.»* El `CS` de la cabecera D3, *«el CS es la dirección»*, lo pone el periférico, no un GPIO.

**El CRC es el del sobre, y solo ese.** La cabecera D2 lo decidió: CRC-16/CCITT-FALSE sobre los primeros `4 + largo` bytes, dentro del sobre, computado con la unidad CRC del chip sobre el búfer, precisamente porque *«un receptor de largo variable no conoce `TSIZE`»*. El CRC del periférico SPI (`CRCEN`) viaja como trama aparte **después** de los `TSIZE` datos y se compara en el maestro contra lo que el esclavo shiftee en ese momento, que no es un CRC (§67.5.3, p. 3456: *«The length of the transfer must be defined by TSIZE. When the desired number of data is transferred, the TXCRC is transmitted and the data received on the line are compared to the RXCRC value.»*). Activarlo daría `CRCE` en cada giro y dos CRC en el cable. **`CRCEN = 0`.**

**Por qué importa contra el #5607, dicho sin exagerar:** el montaje del hilo mueve el `CS` con un GPIO. El nuestro lo mueve el periférico. Eso es lo único que separa los dos montajes, porque `TSIZE > 0` ya lo usa el `read` de embassy y también se cuelga (§1.1). No es prueba de nada; es una variable que el bring-up mueve (§9, riesgo 1).

> **Enmienda del 2026-09-08 (D1, NSS por hardware):** jake-taf respondió el
> 2026-09-03 en [#5607](https://github.com/embassy-rs/embassy/issues/5607):
> *«I haven't tried that mode.»*, sobre `SSM = 0, SSOE = 1`. No hay una prueba
> de ese modo documentada en la evidencia disponible. El bring-up (#231)
> aportará nuestro primer dato: si no se cuelga, será un hallazgo propio bajo
> las condiciones ensayadas; si se cuelga igual, el modo de NSS dejará de
> separar los casos con cuelgue. Sigue siendo **HUECO** el resultado con NSS
> por hardware; la recuperación de D4 sigue siendo requisito en ambos casos.

**Lo que trae de regalo:** con `TSIZE > 0` y `SSOM = 0`, el fin de la trama es un flanco de NSS generado por hardware al `EOT`, exacto al reloj. La cuenta de bytes en el flanco del esclavo (cabecera D6.4, H-14) recibe un flanco limpio.

### D2. Las dos esperas son cancelables, y el plazo abraza las dos *(⚠ reescrita: la v1 ponía el plazo solo sobre `EOT` — H-1, S-12, H-11)*

Una transferencia del J2 espera dos cosas: que el DMA termine (los dos canales, en full duplex) y que el periférico marque `EOT`. **Las dos esperas son futuros, y el plazo de D3 abraza las dos juntas:**

```
with_timeout(plazo, async {
    join(tx_dma, rx_dma).await;   // los Transfer de embassy, cancelables por Drop
    eot.await;                    // el futuro de la ISR
}).await
```

Si la recepción no termina nunca (el modo del hilo), el plazo vence en el `join`; si el DMA terminó y el periférico no marca `EOT`, vence en el segundo. En los dos casos la tarea recibe `TimeoutError` y ejecuta D4. Ninguna espera del J2 es un bucle sin cota (R-MJ2).

**El fin de transferencia es una interrupción.** El maestro habilita `EOTIE` y espera un futuro que resuelve la ISR. RM0486 §67.11.5, p. 3490: *«Bit 3 EOTIE: EOT, SUSP and TXC interrupt enable»*. Y §67.7, Tabla 661, p. 3458, la fila del evento:

| Interrupt event | Event flag | Enable control bit | Event clear method |
|---|---|---|---|
| End Of Transfer (full transfer sequence completed - based on TSIZE value) | EOT | EOTIE | Writing EOTC to 1 |

La ISR de `SPIn` hace lo mínimo: lee `SR`, guarda las banderas que importan (`EOT`, `SUSP`, `OVR`, `MODF`) junto con la **generación** de la transferencia en curso, limpia por `IFCR`, deshabilita `EOTIE`, y despierta (`AtomicWaker`). Solo `EOTIE` se habilita: con `TSIZE` y DMA no hay `OVR` en el maestro, `MODF` no aplica con un solo maestro por enlace (punto a punto D1), y el `CRCE` del periférico no se usa (D1). *(⚠ S-12c)*

**Tres reglas que cierran los huecos que la junta encontró en la espera** *(⚠ S-12, H-10, H-11)*:

1. **Cada transferencia tiene una generación** (`u32` por ranura, `+1` al armar). La tarea la escribe antes de armar y la ISR la copia junto a las banderas. La tarea acepta un resultado solo si la generación coincide; un `EOT` que llega después de vencido el plazo pertenece a una generación vieja, **se descarta y se cuenta** (`eot_tardios`), porque esa trama sí salió al cable y el módulo no la ve como perdida (§3.3, `perdidas ≥ rechazadas` cambia de lectura: ver §10).
2. **El resultado guardado se borra al armar**, antes de habilitar nada. Nunca se consume un búfer de la trama anterior.
3. **El `poll` del futuro de `EOT` registra el waker antes de mirar la bandera.** Al revés pierde el despertar y el plazo vence sobre una trama buena.

> **Enmienda del 2026-09-18 (D2 regla 1, lectura; revisión del driver, ruling R13):** el hardware no etiqueta el `EOT` con ninguna generación, así que lo único que la ISR puede copiar es la generación **armada en el instante en que corre**; la comparación de la regla 1 no puede fallar por sí sola. Lo que la regla 1 protege de verdad es un resultado guardado que la tarea no llegó a consumir: lo descarta y lo cuenta la regla 2 al armar (`Turno::armar`, en `core`). Y lo que protege a la generación es la disciplina de `EOTIE` (apagado en D4.1, encendido después de armar) más una cosa que faltaba: **una ISR ya pendiente en el NVIC cuando D4 apaga `EOTIE` corre después del reinicio**, y por eso D4 hace `NVIC::unpend` de la interrupción de la ranura tras el paso 1 y tras el paso 7.

**El orden de arranque, y por qué `EOTC` va donde va** *(⚠ S-12d, H-11)*: el manual dice en §67.11.6, p. 3492, que *«EOT is set by hardware as soon as a full transfer is complete, that is when SPI is re-enabled or when TSIZE number of data have been transmitted and/or received on the SPI. EOT is cleared when SPI is re-enabled or by writing 1 to the EOTC bit of the SPI_IFCR register optionally.»*, y en §67.11.6, p. 3490, que *«All the flags of this register are not cleared automatically when the SPI is reenabled.»* Las dos frases no encajan del todo, y este papel no elige cuál es la buena: **escribe `EOTC` después de `SPE = 1` y antes de `EOTIE = 1`**, con lo que da igual cuál sea. Es decisión propia por prudencia, no cita. El bring-up la mide (§9, riesgo 5). El orden completo:

```
SPE = 0 → TSIZE = N (CR2, solo con SPE = 0, p. 3484) → RXDMAEN → canales de DMA armados
→ TXDMAEN → SPE = 1 → EOTC → EOTIE = 1 → CSTART
```

Los pasos del DMA son los de §67.4.14, p. 3451: *«When starting communication using DMA, to prevent DMA channel management raising error events, these steps must be followed in order: 1. Enable the DMA Rx buffer in the RXDMAEN bit of the SPI_CFG1 register, if DMA Rx is used. 2. Enable DMA requests for Tx and Rx in DMA registers, if the DMA is used. 3. Enable the DMA Tx buffer in the TXDMAEN bit of the SPI_CFG1 register, if DMA Tx is used. 4. Enable the SPI by setting the SPE bit.»*

**El SPI está apagado entre transferencias, siempre.** El manual lo recomienda tres veces (p. 3448 *«it is recommended to disable the SPI and enable it again when the transfer is complete, even if the SPI configuration is not changed»*; p. 3492 *«SPI is strongly suggested to be disabled and re-enabled before next transfer starts despite its setting is not changed»*; y `TSIZE` solo se puede escribir con `SPE = 0`, p. 3484), embassy lo hace, y D4 lo necesita. *(⚠ S-4b)*

> **Enmienda del 2026-09-11 (D2, el hueco entre `SPE = 1` y `CSTART`; acta del 11-09, fichas 1 y 3):** el chip hermano tiene documentado un atasco del maestro que el orden de arriba no evita y, bajo una lectura del manual, provoca. ES0396 Rev 9 (STM32H750/H753, bloque `spi_v4`; el N657 es `spi_v5` y embassy los trata juntos), §2.14.2 «Master data transfer stall at system clock much faster than SCK», presente en todas las revisiones de silicio (A A A):
>
> *«With the system clock (spi_pclk) substantially faster than SCK (spi_ker_ck divided by a prescaler), SPI/I2S master data transfer can stall upon setting the CSTART bit within one SCK cycle after the EOT event (EOT flag raise) signaling the end of the previous transfer. Workaround. Apply one of the following measures: • Disable then enable SPI/I2S after each EOT event. • Upon EOT event, wait for at least one SCK cycle before setting CSTART. • Prevent EOT events from occurring, by setting transfer size to undefined (TSIZE = 0) and by triggering transmission exclusively by TXFIFO writes.»*
>
> Bajo la lectura literal de p. 3492 (*«EOT is set … when SPI is re-enabled»*), el `SPE = 1` del orden de arriba es él mismo un evento `EOT`, y `CSTART` llega tres escrituras APB después: **entre 15 y 60 ns** según pclk (cálculo de Halberg, junta del 11-09, H-1; no medido), contra **100 ns** de ciclo de SCK al piso de 10 MHz y 29 ns a los 34,5 MHz de D8. La solución 1 de la errata, apagar y encender, que D2 ya aplica, genera bajo esa lectura el evento que la solución 2 quiere evitar. Y ES0620 Rev 5 §2.2.1 (N657, #363) dice que el prescaler de APB no funciona y pclk replica siempre a hclk: la razón pclk/SCK no se puede bajar por ese camino.
>
> **Lo que cambia:** entre `SPE = 1` y `EOTC` el driver **lee de vuelta `CR1`** y **espera al menos un ciclo de SCK contado desde esa lectura**, en ciclos de CPU (80 a 800 MHz para 100 ns; 24 para 29 ns), no con `embassy_time`, cuyo grano de 1 µs es diez veces el ciclo. La lectura de vuelta es el anclaje: según Halberg, una escritura a memoria Device puede quedar en vuelo y el retardo transcurrir antes de que `SPE = 1` llegue al periférico; una lectura devuelve cuando el periférico contesta. Coste: 0,08 % del giro por ranura. El orden queda:
>
> ```
> SPE = 0 → TSIZE = N → RXDMAEN → canales de DMA armados → TXDMAEN
> → SPE = 1 → leer CR1 → esperar ≥ 1 T_SCK → EOTC → EOTIE = 1 → CSTART
> ```
>
> **Estado de la evidencia:** ES0620 Rev 5 (agosto 2026), la errata del N657, **no lista ningún ítem del periférico SPI**. La enmienda entra **por analogía** con el H7 y así queda marcada hasta que la placa la mida. La medida que dirime la lectura cuesta un acceso: con nada armado, escribir `SPE = 1` y leer `SR.EOT`. Si vuelve 1, la hipótesis está viva y todo armado cae dentro de la ventana al piso; si vuelve 0, el `EOT` anterior fue el de la trama del giro previo y D2 ya la cubría con más de 100 µs de sobra. Después, el barrido del retardo (§9, enmienda del 11-09, punto 3): una tasa de cuelgue que dependa del retardo es la firma de la errata; una que no, no lo es.

### D3. Toda espera tiene plazo, y el plazo sale de R-E1

El plazo es **por mensaje**, no global:

```
plazo(msg) = FACTOR_PLAZO × t_nominal(msg) + T_SUELO_PLAZO
t_nominal(msg) = bytes_clocados(msg) × 8 / f_reloj_sancionado(ranura)
```

- `bytes_clocados` es el de la cabecera §4 (sobre + carga + CRC + cola, con relleno), ya presupuestado en `trama_j2_budget.py`. Es el mismo número que `TSIZE` (D1).
- `f_reloj_sancionado` es el de la ranura (punto a punto D2, `sancion_j2.csv`), o el piso legado si no hay fila. Hoy no hay fila: el instrumento corre al piso.
- `FACTOR_PLAZO = 2` y `T_SUELO_PLAZO = 20 µs`: **ESTIMADO**, sin fuente. El factor cubre `T_GAP` (2 µs provisional), `MSSI`/`MIDI` si se usan, y la latencia de la ISR; el suelo evita que un `HOLA` de 9 bytes (cabecera §4) a 34,5 MHz, 2,1 µs, tenga un plazo de 4 µs. En el enlace de la Voz el `HOLA` va rellenado a 25 bytes, 5,8 µs. *(⚠ S-9: la v1 decía 7 bytes)* Los sella el bring-up con osciloscopio (§9, riesgo 2).
- **Cota:** por R-E1 ningún mensaje dura más de 100 µs al piso, así que `plazo ≤ 220 µs` para cualquier mensaje. El mensaje real más largo, `SET` de 16, son 82,4 µs al piso y 184,8 µs de plazo. El presupuesto asevera la cota.

**Lo que NO se pone bajo plazo:** el `T_GAP` entre mensajes y la cadencia del giro. Esos son del planificador (cabecera D8) y no tienen nada que colgarse.

### D4. Al expirar, el periférico se reinicia según el manual, entero y en orden, y el reinicio se cuenta *(⚠ reescrita: la v1 omitía un paso, encendía al final y dejaba `EOTIE` armado — S-4, S-12a, S-13, H-8)*

Un plazo vencido no se reintenta: se reinicia. La receta es la del RM0486, completa, y termina con el SPI **apagado**, que es como está siempre entre transferencias (D2).

1. **Silenciar la ISR.** `EOTIE = 0`. Si no, el `CSUSP` del paso 3 produce `SUSP`, `SUSP` dispara la ISR (`EOTIE` cubre `SUSP`, p. 3490), y la ISR limpia `SUSPC` antes de que el paso 3 lo vea. *(⚠ S-12a)*
2. **Soltar el DMA.** Los dos `Transfer` de embassy se sueltan: su `Drop` (`gpdma/mod.rs:1287-1295`) llama a `request_reset()` y espera a que el canal pare; `request_reset` (`:902-910`) hace `request_pause()`, espera `is_running() == false`, y resetea el canal. Esa espera es un bucle con cota práctica (la pausa actúa al fin de la ráfaga en curso) pero sin cota escrita: si el canal de GPDMA mismo no responde, ahí se queda, y eso lo cubre el IWDG del hub (D5), no este papel (§9, riesgo 6). Esto es el paso 1 del cierre del manual, §67.4.14, p. 3451: *«To close communication, it is mandatory to follow these steps in order: 1. Disable DMA requests for Tx and Rx in the DMA registers, if the DMA issued. 2. Disable the SPI by following the SPI disable procedure. 3. Disable DMA Tx and Rx buffers by clearing the TXDMAEN and RXDMAEN bits of the SPI_CFG1 register, if DMA Tx and/or DMA Rx are used.»*

   > **Enmienda del 2026-09-18 (D4 paso 2 y R-MJ2; #368, riesgo 6 de la junta del 11-09):**
   > la espera del `Drop` deja de ser «de embassy y declarada» y pasa a tener **cota
   > propia**. El driver no suelta ningún `Transfer` mientras su canal pueda estar
   > corriendo: pide `request_pause()` a los dos canales (una escritura de
   > `CxCR.SUSP`, sin bucle; `gpdma/mod.rs:882-887`), sondea `is_running()`
   > como máximo **`T_CANAL` (ESTIMADO 10 µs, de la clase de `T_SUSP`)** y solo
   > entonces los suelta: el `Drop` de embassy (`request_reset()` + su espera,
   > `gpdma/mod.rs:1287-1295`) entra y sale al instante con el canal ya suspendido.
   > Si un canal no para dentro de la cota, el driver **escala**: deja los dos
   > `Transfer` en su `ManuallyDrop` sin soltar (no se llama a `drop`; un
   > `mem::forget` sobre un `ManuallyDrop` no hace nada) y resetea el GPDMA1 entero por RCC
   > (`rcc::enable_and_reset::<GPDMA1>()`; el generador de embassy implementa
   > `RccPeripheral` para `GPDMA1`). Las otras cinco ranuras ven sus futuros de DMA
   > resolverse, no reciben `EOT`, vencen su plazo y ejecutan D4 cada una: un
   > reinicio de las seis ranuras **bajo control y dentro de los 50 ms del módulo**,
   > no un reinicio del chip. Se cuenta aparte (`escaladas_gpdma`, en `fw`, no en
   > la política). El IWDG del hub deja de ser la cobertura del riesgo 6: es la red
   > de lo que ni un reset de RCC arregla, que por construcción no existe. Por qué
   > no la otra salida del issue (correr el reinicio en una tarea fuera del
   > ejecutor): una espera sin cota bloquea al ejecutor donde gire, y todos tienen
   > algo debajo que no puede parar. Los pasos están en
   > `docs/superpowers/plans/2026-09-18-j2-fase-b.md`, tarea 7d.
   >
   > *Correccion del mismo 18-09:* la primera redaccion de esta enmienda mandaba
   > `request_reset()` y luego sondear con cota. `request_reset()` de embassy ya
   > contiene `request_pause(); while is_running() {}` sin cota (`gpdma/mod.rs:902-910`,
   > que este mismo paso cita arriba): la cota habria sido codigo muerto. Lo cazo
   > la revision del driver, no el plan. La forma que vale es la de arriba.

3. **Suspender, con cota.** `CSUSP = 1` y sondear `SUSP = 1` **como máximo `T_SUSP` (ESTIMADO 10 µs)**, contando con `embassy_time::Instant` (tick declarado en el plan; 1 MHz cubre esta cota) o con ciclos. §67.11.1, p. 3483: *«In master mode, when this bit is set by software, the CSTART bit is reset at the end of the current frame and communication is suspended. The user has to check SUSP flag to check end of the frame transfer.»* Es una espera síncrona **acotada**, que R-MJ2 permite: es el único sitio donde un sondeo con cota es la herramienta honesta, porque el periférico está mintiendo. *(⚠ S-13, V-11)*
4. **Limpiar `SUSP` incondicionalmente.** `SUSPC = 1`, haya llegado `SUSP` o no. §67.11.6, p. 3491: *«This bit must be cleared prior to disabling the SPI. This is done by setting the SUSPC bit of SPI_IFCR exclusively.»* Escribir `SUSPC` sin `SUSP` no hace nada, y escribirlo con `SUSP` recién llegado (entre la cota y el apagado) evita apagar con la suspensión a medio aceptar. *(⚠ S-4c)*
5. **Apagar.** `SPE = 0`. §67.11.1, p. 3484:

   > *«When SPE = 0 any SPI operation is stopped and disabled, all the pending requests of the events with enabled interrupt are blocked except the MODF interrupt request (but their pending still propagates the request of the spi_plck clock), the NSS output is deactivated at master, the RDY signal keeps not ready status at slave, the internal state machine is reseted, all the FIFOs content is flushed, CRC calculation initialized, receive data register is read zero.»*

   Se acepta la pérdida de la trama en curso. §67.4.12, p. 3449: *«Caution: If the SPE bit is cleared in master mode while the transfer is ongoing without any suspension, the clock is stopped even if the current frame transmission is not complete, and the content of the FIFOs is flushed and lost.»* Esa trama ya estaba perdida. *(⚠ S-3: la cita va entera; la v1 la había recortado)*
6. **Apagar los búferes de DMA del periférico.** `TXDMAEN = 0`, `RXDMAEN = 0` en `CFG1`, que solo se puede escribir con `SPE = 0` (p. 3484: *«The content of this register is write protected when SPI is enabled.»*). Es el paso 3 del cierre del manual, y la v1 no lo tenía. *(⚠ S-4a)*
7. **Limpiar banderas.** `IFCR`: `EOTC`, `TXTFC`, `OVRC`, `SUSPC`, `MODFC`. Las de `SR` no se limpian solas (p. 3490).
8. **Contar y seguir.** `plazos_vencidos[ranura] += 1`. La ranura queda como entre transferencias: apagada y limpia. El planificador sigue con el **siguiente giro**, no con la trama perdida: el registro de subida se muestrea (cabecera D6), y lo que baja se reafirma (D7), así que no hay nada que retransmitir. *Salvo* un `EVENTO`: ese no tiene red, y así lo dice la cabecera (D7 tabla: *«un `dispara` perdido es un golpe perdido»*). Ver D6 y §3.

**Lo que le pasa al esclavo, y lo que este papel le manda al papel del módulo** *(⚠ S-5, V-9: la v1 decía «el flanco lo realinea», y la cita que lo sostenía es del esclavo recién habilitado, no del interrumpido)*: el `SPE = 0` desactiva el NSS del maestro (p. 3484), así que el módulo ve el `CS` subir a mitad de trama. Por la cabecera D6.4 cuenta bytes en el flanco y ve una trama corta; por D8 la rechaza entera y cuenta. Lo que el manual dice del esclavo interrumpido es una sola frase, §67.4.13, p. 3450: *«In slave mode, any ongoing data are lost when disabling the SPI.»* De aquí sigue que la limpieza del esclavo es **apagar y encender su SPI**, y que un esclavo que solo rearme el DMA puede arrastrar medio byte en el registro de desplazamiento y rechazar también las tramas siguientes. **Enmienda mandada al papel del módulo (§10):** al contar corto en el flanco de `CS`, el módulo hace `SPE = 0` → `SPE = 1` en su SPI antes de rearmar el DMA de recepción. Es una línea en su ISR, y es la única forma que el manual documenta de dejar el esclavo limpio.

**La `secuencia` de la trama abortada se consumió.** El planificador la asignó y el módulo no la aceptó, así que el módulo verá un hueco y lo contará en `perdidas` (cabecera §3.3, R-C3). Es correcto y esperable: en el bring-up, `perdidas` del módulo se cruza con `plazos_vencidos + eot_tardios` del cerebro (D2 regla 1), y la diferencia es lo que de verdad se perdió por el cable.

**Lo que NO se hace:** escribir a `TXDR` para desatascar. Es el paliativo del hilo para el caso bloqueante, no funciona en DMA, y meter un byte en el bus a mitad de un estado desconocido es peor que apagar.

> **Enmienda del 2026-09-08 (D4, dato del mecanismo):** jake-taf confirmó el
> 2026-09-03 en [#5607](https://github.com/embassy-rs/embassy/issues/5607):
> *«Interesting. I stuck with blocking since I have a workaround when it gets stuck (`SPI1.txdr8().write_value(0)`), but both have the problem»*.
> Confirma que usa ese paliativo en el camino bloqueante y que el cuelgue
> ocurre tanto en el bloqueante como con DMA. La prohibición de escribir a
> `TXDR` para desatascar sigue en pie, tal cual (R-MJ3).

### D5. El J2 corre en su propio ejecutor, con una tarea por ranura; el IWDG es del hub *(⚠ reescrita entera: la v1 tenía un vigía y alimentaba el IWDG desde el J2 — V-4, V-5, V-6, S-7, S-8, H-1, H-2, H-6, H-9)*

La v1 ponía un vigía en un ejecutor de interrupción que reiniciaba ranuras estancadas. La junta lo tumbó por tres lados que no admiten parche: no cubre ningún fallo que D2-D4 no cubran (si la tarea está viva, el plazo gana; si el ejecutor está congelado, reiniciar el SPI no lo descongela); no puede soltar los `Transfer` que posee la tarea, así que corre otra receta y deja dos dueños del canal; y una sección crítica que no suelta lo congela con lo que vigila. Era otra mano en el mismo volante, y R-C8 dice un solo escritor. **Muere.** Lo que queda es más simple y es lo que corre:

1. **Seis tareas, una por ranura**, cada una con su plazo (D3), su reinicio (D4) y su máquina (D7). En serie no caben: seis `NADA` de 25 bytes al piso son 120 µs más seis `T_GAP`, 132 µs en un giro de 125 (S-8). Los seis periféricos y sus doce canales de DMA corren en paralelo por hardware; las tareas solo los atienden. Un plazo vencido en una ranura no retrasa a las otras cinco, y la cuenta de D7 es por ranura: un cuelgue en una no ensucia la ventana de las demás (H-1).
2. **El planificador sigue siendo el único escritor del enlace** (R-C8). Decide qué baja por cada ranura en cada giro; las seis tareas son el transporte, como lo son los canales de DMA. No deciden nada del protocolo.
3. **Las seis tareas viven en un `InterruptExecutor` propio** (`embassy-stm32/src/executor.rs:196`), a prioridad por encima del ejecutor de hilo donde viven la pantalla, el USB y el MIDI (`fw/src/main.rs`). Una tarea de pantalla que retenga la CPU 15 ms no retrasa un giro del J2 ni un microsegundo; sin esto, la simulación de Halberg da giros perdidos a partir de 6 ms de retención y el módulo soltando a 50 (H-9). El J2 es tiempo real a 8 kHz y la pantalla no; no comparten ejecutor.
4. **El IWDG es del chip, no del J2.** Alimentarlo desde el planificador del enlace definía la vida del instrumento como «el J2 dio un giro», y con una ranura sin módulo lo habría disparado diez veces por segundo (H-6). Este papel **no decide** quién alimenta el IWDG ni con qué plazo. Le manda al papel del hub (§10) un **supervisor de vitalidad**: cada subsistema con requisito de tiempo real (el J2, la pantalla, el USB, la radio) escribe un sello; el supervisor alimenta el IWDG solo si todos los que deben estar vivos lo están. Lo que el J2 aporta es **un sello por ranura activa**, escrito al armar cada transferencia (no al completarla: una ranura reiniciando también está viva). Y le manda una cota: **el plazo del IWDG es estrictamente mayor que la ventana del watchdog de trama del módulo (~50 ms)**, para que cuando el chip se reinicie el módulo ya esté en release por su cuenta y el reinicio no añada silencio: lo termina de ordenar. Cuánto silencio añade el arranque del cerebro (descubrimiento por I²C, `HOLA`, los 7,9 ms de refresco de la cabecera D5) no está cuantificado y es HUECO del hub (S-10).

> **Enmienda del 2026-09-18 (D5.1 y §3; revisión del ejecutor, ruling R15):** tras un plazo vencido la tarea de la ranura **se realinea** al periodo (`Ticker::reset()`), no recupera los tics perdidos. Sin esto el `Ticker` de embassy clocaría en ráfaga hasta reengancharse y dejaría fronteras de trama con gap ≈ 0, justo cuando el esclavo acaba de que le arranquen el `CS`: borraría el `T_GAP` de la cabecera D8 (2 µs provisional, HUECO). El techo de recuperación de §3 se mantiene: 220 + 20 + 125 = 365 µs < 490.

### D6. La corrupción la absorbe el CRC del sobre; lo que tiene red se repara solo, y lo que no la tiene se dice *(⚠ precisada: V-7, S-10, S-11, H-4)*

El segundo síntoma del hilo, el bit duplicado con el `CS` subiendo antes, **no necesita nada nuevo**:

- El CRC del sobre (cabecera D2, con la unidad) la caza en el maestro y en el esclavo (D8: rechaza entero y cuenta). El maestro cuenta `subidas_malas`.
- En bajada, `TONO` completo sale a ≥ 1 kHz aunque nada cambie (cabecera D4): una trama de deltas perdida se repara sola en ≤ 1 ms. `SET`, `BAHIA` y `COMPUERTA` se reafirman (D7). La simulación de Halberg (sim4) lo confirma: a la tasa de corrupción del hilo y a cien veces esa tasa, ningún tono viejo dura más de 1,0 ms; a diez mil veces, 2,0 ms; hasta una pérdida de una trama por cada cien, ninguno pasa de 5 ms.
- **`EVENTO` no tiene red**, y eso lo decidió la cabecera (D7: *«un `dispara` perdido es un golpe perdido»*), no este papel. Un cuelgue o una corrupción que caiga en un giro con `EVENTO` es un golpe perdido. Es una **probabilidad**, no un invariante: `P(golpe perdido por cuelgue) = giros_perdidos_por_cuelgue × P(EVENTO en un giro)`, y el segundo factor depende de lo que el músico toca. El presupuesto lo deja como función con sus dos parámetros (§8); no le pone cifra, porque la tasa de cuelgues es de la Discovery y la densidad de eventos es del músico.
- **En subida, una lectura corrupta se pierde hasta la próxima publicación de ese registro**, no 125 µs: el módulo avanza de registro cuando contó bytes suficientes (cabecera D6.2), no cuando el maestro validó. `SALUD` y `ESTADO_VOZ` se publican a 1 Hz, así que una muestra corrupta es un segundo sin esa muestra; como los contadores son totales desde la sesión (cabecera §3.3), la siguiente muestra los trae. *(⚠ S-11)*

**La tasa del hilo no se normaliza.** La v1 dividía *«una o dos veces por minuto»* de otro montaje entre nuestras tramas por segundo y llamaba a eso una tasa por trama. No lo es: reloj, largo y cadencia de aquel montaje no son los nuestros. Lo que el hilo aporta son dos órdenes de magnitud a medir en el nuestro: cuelgues con período de 10-900 s y corrupción de una o dos por minuto. La Discovery mide las nuestras (§9, riesgo 1).

### D7. La ranura nunca deja de girar: la salud es una marca que sube, no una cadencia que baja *(⚠ reescrita entera: la v1 tenía sondeo lento con `HOLA`, umbrales de vuelta y backoff — V-2, V-3, V-10, S-6, S-15, H-2, H-7, H-13)*

La v1 declaraba «enferma» una ranura con muchos reinicios y la pasaba a un sondeo cada 100 ms con `HOLA`. La junta lo tumbó cuatro veces: `HOLA` abre sesión y suelta las notas (cabecera D5, R-C7); 100 ms entre tramas garantiza el release del módulo a los 50; volver a sana costaba diez segundos de silencio; y la simulación de Halberg (sim3) dice que **sin ese mecanismo ningún hueco llega a 50 ms hasta que la mitad de las tramas se cuelgan**, mientras que con él la ranura oscila entre sana y enferma a partir de cuatro cuelgues por segundo y el módulo pasa la mayor parte del tiempo en release. Hacía daño y no aportaba. **Muere.**

Lo que queda:

1. **El planificador gira a 8 kHz por toda ranura activa, siempre.** Un plazo vencido se reinicia (D4) y el giro siguiente sale a su hora. No hay cadencia reducida, no hay backoff, no hay sondeo, no hay «vuelta a sana» y por tanto no hay refresco especial: el bloque completo a 1 kHz y las reafirmaciones de la cabecera D7 hacen ese trabajo solos, porque nunca dejaron de hacerlo.
2. **El coste de CPU está acotado por construcción**, no por umbral: como máximo un reinicio por giro por ranura, `8000 × T_REINICIO` por segundo. Con `T_REINICIO` ESTIMADO 20 µs son 16 % de un núcleo por ranura con **todas** sus tramas colgándose, 96 % con las seis. Eso es el instrumento roto, y se acepta que un instrumento roto gaste CPU en intentar no estarlo. El presupuesto lo asevera como cota (§8).
3. **La salud son dos marcas por ranura, calculadas sobre una ventana deslizante, y suben al instrumento:**
   - **`inestable`**: `plazos_vencidos` en la última `VENTANA_SALUD` (ESTIMADO 1 s) ≥ `UMBRAL_INESTABLE` (ESTIMADO 10). Es información, no acción: no cambia lo que la tarea hace.
   - **`muda`**: `subidas_malas` seguidas ≥ `UMBRAL_MUDA` (ESTIMADO 40, o sea 5 ms). Es el testigo que la v1 no tenía (V-10): la subida lleva el sobre con su CRC en cada giro (cabecera D6.1), así que el maestro sabe en cada giro si el módulo contestó bien. Un módulo muerto (MISO en pull-down, ceros) es `muda` en 5 ms aunque el periférico del cerebro dé `EOT` perfecto. `giros` mide *«mi periférico terminó»*; `subidas_ok` mide *«el módulo contestó»*; son dos cosas y se cuentan aparte.
   - Ninguna marca cambia la cadencia ni manda `HOLA`. `HOLA` se manda cuando la cabecera D5 dice: al muestrear `sesión = 0`. Una ranura `muda` no muestrea nada, así que no manda `HOLA`; sigue clocando lo que el planificador diga, y la marca sube.
4. **`Vacia`**: una ranura sin identidad por I²C (punto a punto D2: el descubrimiento precede a *«la primera palabra de SPI»*) no entra al lazo. No se cloca, no se cuenta, no tiene marcas. Sin esto, cada ranura vacía contaría `subidas_malas` a 8 kHz y daría la vuelta al `u32` en seis días de instrumento encendido (S-15). Entra al lazo cuando el descubrimiento le da identidad; sale cuando se la quita.
5. **Los contadores por ranura**, totales desde el arranque, `u32`: `giros`, `plazos_vencidos`, `eot_tardios`, `subidas_ok`, `subidas_malas`. No viajan por el J2: son del cerebro, los lee la pantalla y el registro de salud del cerebro, y se cruzan en el bring-up con `perdidas` y `rechazadas_*` del módulo (cabecera §3.3), que son la otra mitad de la misma historia.

**Lo que NO decide este papel:** qué hace el instrumento con una ranura `inestable` o `muda`. Retirar sus voces del reparto, avisar en pantalla, o seguir mandando: eso toca la política de partes y voces (`partes.rs`, `Repartidor`) y es decisión de otro papel (§6). Aquí las marcas **suben**, nada más.

### D8. Dónde vive el código, qué es cada pieza, y qué se contribuye upstream *(⚠ precisada: V-12, H-12)*

- **La política, en `core`**: `software/nucleo/core/src/maestro_j2.rs`. Una máquina por ranura, sin hardware, sin `async`: dos estados (`Vacia`, `Activa`), recibe eventos (`Identidad(Option<_>)`, `Armada`, `GiroOk`, `PlazoVencido`, `EotTardio`, `SubidaOk`, `SubidaMala`, `Tick`) y devuelve una acción (`Nada`, `Reiniciar`) y las marcas (`inestable`, `muda`). Los umbrales son un `struct Umbrales` con sus valores ESTIMADO y su fuente, parámetro del constructor. Se prueba entera en el host (§7).
- **El driver, en `fw`**: `software/nucleo/fw/src/j2_spi.rs`. Es lo que es: **un driver genérico de SPI maestro para `spi_v4`, con `TSIZE`, NSS por hardware, y las dos esperas cancelables**, escrito porque el de embassy no cancela. **No sabe nada del sobre.** Recibe un búfer de bajada, un búfer de subida y un largo; devuelve `Ok`, `PlazoVencido` o `EotTardio`. La v1 lo llamaba «el driver de nuestro bus propietario», y la junta señaló que eso era una etiqueta: cada rasgo del driver es del periférico, ninguno del J2. La frontera queda trazada: **`fw` cloca bytes; `core` sabe qué son.** Si la semántica del sobre alguna vez aparece en `j2_spi.rs`, es un defecto.
- **Los búferes de DMA viven en memoria no cacheable.** El Cortex-M55 del N657 tiene D-cache; un búfer de recepción cacheado da *«CRC bueno en el cable, basura en RAM»*, que es exactamente lo que el bring-up atribuiría al silicio (H-12). El plan de implementación elige entre región MPU no cacheable e invalidación explícita; este papel solo exige que sea una de las dos.
- **Upstream, dos cosas, en este orden:**
  1. **Un comentario en #5607** (§9, acción 1), ya redactado en el scratchpad de la sesión: que los dos reportes usan `SPI5` y nadie probó otra instancia; que el camino bloqueante y `write`/`transfer` van con `TSIZE = 0` y `read` no, así que `TSIZE` solo no discrimina; que p. 3492 dice que `EOT` se pone al rehabilitar y el driver no lo limpia tras `SPE = 1`, como hipótesis; y que ambos mueven el `CS` por GPIO, y si alguien lo vio con NSS por hardware. Y si la comparación con el HAL de C del 2026-06-24 se llegó a correr. Es una pregunta, no un parche. Sale con la cuenta de Samuel.
  2. **Un PR a embassy**, cuando haya Discovery: las dos esperas de `spi_v4`-`v6` como futuros (`EOTIE` para `EOT`; el `join` del DMA ya lo es) con un `with_timeout` opcional, y `TSIZE` en `write`/`transfer`. Si entra, `j2_spi.rs` se retira y el J2 vuelve a `embassy_stm32::spi`. No es tarea de este papel; es su cierre deseable.

---

## 3. Los números *(⚠ recalculados por S-9, S-10, H-3)*

Todo lo de esta sección lo asevera `recuperacion_j2_budget.py` (§8). Aquí, en prosa, con la fuente de cada cifra.

| Cifra | Valor | De dónde |
|---|---|---|
| Cadencia del lazo | 8 kHz, 125 µs por giro | `trama_j2_budget.F_LAZO_HZ` |
| Reloj del enlace, D8 | 34,5 MHz | `enlace_budget.F_PELDANO_2_HZ` |
| Reloj de hoy | 10 MHz, el piso | `sancion_j2.csv` vacío |
| Mensaje más largo | ≤ 100 µs al piso (cota); `SET` de 16 = 82,4 µs | `trama_j2_budget.T_MENSAJE_MAX_S` (R-E1); cabecera §4 |
| Plazo máximo por mensaje (D3) | 2 × 100 + 20 = **220 µs** (cota); 184,8 real | ESTIMADO (`FACTOR_PLAZO`, `T_SUELO_PLAZO`) |
| Reinicio del periférico (D4) | **20 µs**, ESTIMADO, sin «≤»: `T_SUSP` 10 más el reset del GPDMA (sin cifra) más registros | el bring-up lo mide |
| Recuperación, peor caso | plazo + reinicio + alineación al giro + un giro = 220 + 20 + 125 + 125 = **490 µs**, o sea **3 giros** | aritmética; la v1 decía 2 |
| Ventana del módulo | **~50 ms** = 400 giros | voz-total §9.2, ESTIMADO (*«N del plan»*) |
| **Margen** | 50 ms / 490 µs = **102×** | la cifra que este papel defiende; la v1 decía 200 |
| CPU por reinicios, peor caso | 8000 × 20 µs = **16 % de un núcleo por ranura**, 96 % con las seis colgándose siempre | D7.2, cota por construcción |
| Corrupción con red (D6) | `TONO` viejo ≤ 1,0 ms a la tasa del hilo y a 100×; ≤ 2,0 ms a 10 000×; ≤ 2,75 ms a 1 trama de cada 100 | sim4 de la junta |
| Corrupción sin red (D6) | `P(golpe perdido) = 3 × P(EVENTO en un giro)` por cuelgue | función, sin cifra: los dos parámetros son de la Discovery y del músico |
| `u32` | 2³² / 8000 = 6,2 días de un evento por giro | solo importa con ranuras vacías contando, y D7.4 lo evita |

**La lectura:** el peor caso de un reinicio le cuesta al músico **tres giros**, cuatro décimas de milisegundo, y el módulo no se entera porque su watchdog está cien veces más lejos. Si el giro perdido llevaba un `EVENTO`, ese golpe se perdió, y eso es de la cabecera. Lo que sí se entera es el contador. Si el defecto del hilo sale en nuestro montaje con su período de 10-900 s, el instrumento suena igual y el registro dice cuántas veces se recuperó. Eso es lo que un fabricante quiere: **el fallo existe, está contado, y lo que puede no cruzar al músico, no cruza; lo que sí puede, está dicho.**

**Los 50 ms tienen dos caras, y este papel escribe solo una** *(⚠ V-7)*: voz-total los quiere pequeños (*«trama perdida ≠ sustain infinito»*: es el techo del sustain fantasma) y este papel los quiere grandes (es el piso del margen). El presupuesto asevera `recuperación × 10 < T_WATCHDOG_TRAMA`; la cota de arriba, cuánto sustain fantasma es tolerable, no está escrita en ningún papel y queda como HUECO de voz-total (§10).

---

## 4. Las reglas

- **R-MJ1.** Ninguna transferencia del J2 en el cerebro corre con `TSIZE = 0`. Falla al compilar: `TSIZE` sale de un `NonZeroU16`. Y `TSIZE` es el largo clocado de la cabecera §4, con relleno.
- **R-MJ2.** Ninguna espera del J2 en el cerebro es un bucle síncrono **sin cota**. Las dos esperas de la transferencia son futuros bajo plazo (D2); el sondeo de `SUSP` en D4 tiene cota escrita (`T_SUSP`); la espera del `Drop` del GPDMA tiene cota escrita (`T_CANAL`, D4.2, enmienda del 18-09) y escalada al reset del GPDMA1 por RCC. *(⚠ V-11, S-13: la v1 decía «ningún bucle» y su grep no habría visto ni el `Drop` ni `T_SUSP`)*
- **R-MJ3.** El reinicio del periférico sigue los ocho pasos de D4 en ese orden, y cada paso cita su página. No se escribe a `TXDR` para desatascar.
- **R-MJ4.** Los umbrales de D3 y D7 son parámetros, no literales. Viven en un solo `struct Umbrales` con sus valores ESTIMADO y su fuente, y `recuperacion_j2_budget.py` los lee de `maestro_j2.rs`, no los copia.
- **R-MJ5.** Cada ranura activa tiene su tarea, y las seis viven en el ejecutor del J2, no en el de hilo. Ninguna tarea del ejecutor de hilo puede retrasar un giro.
- **R-MJ6.** Una ranura sin identidad no se cloca ni se cuenta.
- **R-MJ7.** Los búferes de DMA del J2 están en memoria no cacheable o se invalidan antes de leerse. Una de las dos, dicha en el plan.
- **R-MJ8.** El bring-up de la Discovery registra la prueba de resistencia en `software/nucleo/fw/resistencia_j2.csv` con las columnas de §8, y el presupuesto sale con `HUECO` hasta que haya fila.

---

## 5. Qué muere, qué sobrevive, qué nace

**Muere:**
- La idea de que el J2 del cerebro use `embassy_stm32::spi::Spi` tal cual. Vive hasta que embassy tenga las dos esperas cancelables (D8.2).
- *«El bring-up lo sella»* como única respuesta al cuelgue del SPI. Ahora hay diseño antes del bring-up.
- **De la v1, por la junta**: el CRC de hardware del SPI; el vigía; la ranura enferma con sondeo lento; el IWDG alimentado por el J2; «el flanco realinea al esclavo».

**Sobrevive intacto:**
- Toda la cabecera del J2: sobre y su CRC, sesión, registros, `T_GAP`, el byte de cola, `NADA`. Este papel es un cliente suyo y le manda dos enmiendas de una línea (§10).
- El watchdog de trama del módulo y R-M5. Siguen siendo la red del otro lado.
- El reparto de pines del censo: el NSS por hardware ya estaba.

**Nace:**
- `maestro_j2.rs` en `core`, con sus tests.
- `j2_spi.rs` en `fw`, el driver genérico con esperas cancelables.
- El ejecutor del J2, con seis tareas.
- Cinco contadores y dos marcas por ranura en el estado del cerebro.
- `recuperacion_j2_budget.py` y `resistencia_j2.csv`.
- Dos requisitos al hub: el supervisor de vitalidad y el ejecutor del J2 (§10).

---

## 6. Lo que este papel NO decide, con su dueño

| Qué | Dueño |
|---|---|
| Qué hace el instrumento con una ranura `inestable` o `muda` (voces, pantalla) | Papel de la política de partes y voces; toca `partes.rs` y `Repartidor` |
| Las dos ranuras por USART síncrono: plazo, reinicio y cuenta con otro periférico | Su propio papel, cuando esas ranuras tengan módulo (§9, riesgo 7) |
| Quién alimenta el IWDG, con qué plazo, y cuánto silencio añade un reinicio del cerebro | El papel del hub (§10) |
| Cómo el módulo deja limpio su SPI al contar corto en el flanco | El papel del módulo (§10) |
| Si el defecto del N6 es de instancia o del bloque | Upstream (#5607) y la Discovery (#231) |
| El valor real de cada ESTIMADO de §3 | El bring-up, con osciloscopio y horas |
| La cota superior de los 50 ms (cuánto sustain fantasma es tolerable) | voz-total (§10) |
| Región MPU no cacheable o invalidación explícita para los búferes | El plan de implementación |
| La contribución upstream de las esperas cancelables | Su propio PR, cuando haya Discovery |

> **Enmienda del 2026-09-08 (§6, fila del alcance):** **cerrada por upstream
> el 2026-09-03 la pregunta de si el cuelgue es exclusivo de SPI5**. jake-taf
> respondió en [#5607](https://github.com/embassy-rs/embassy/issues/5607):
> *«I have observed this problem on SPI1 as well»*. El alcance observado ya
> abarca SPI5 y SPI1 (§1.1). Lo que sigue abierto es la **causa: silicio o
> driver**. Este cierre no acredita una reproducción en las seis instancias;
> el resultado en nuestro montaje con NSS por hardware sigue siendo HUECO
> de #231 (D1, §9 riesgo 1).

---

## 7. Los tests *(⚠ reescritos: la máquina de la v2 es más chica)*

Todos en `core`, sin hardware, sobre `maestro_j2.rs`. La numeración es la del plan que sigue a este papel.

1. **`Vacia` no cloca ni cuenta**: cualquier evento distinto de `Identidad(Some)` devuelve `Nada` y deja los contadores en cero.
2. **`Identidad(Some)` activa; `Identidad(None)` vacía** y conserva los contadores (son totales desde el arranque, no desde la identidad).
3. **`GiroOk` cuenta `giros`**; **`SubidaOk`/`SubidaMala` cuentan lo suyo** y no cambian la acción.
4. **`PlazoVencido` devuelve `Reiniciar`** y cuenta `plazos_vencidos`; el siguiente `GiroOk` cuenta como siempre (no hay estado intermedio que salir).
5. **`EotTardio` cuenta y no reinicia.**
6. **`inestable` sube al décimo `PlazoVencido` en un segundo** (`≥ UMBRAL_INESTABLE`; el décimo cabe justo, el noveno no) **y baja cuando la ventana desliza** (diez repartidos en más de un segundo no la suben).
7. **`muda` sube a las cuarenta `SubidaMala` seguidas y baja con una `SubidaOk`.**
8. **Las marcas nunca cambian la acción**: con `inestable` y `muda` puestas, `PlazoVencido` sigue devolviendo `Reiniciar` y `GiroOk` sigue devolviendo `Nada`.
9. **Los contadores son monótonos**: ningún evento los baja.
10. **`Umbrales` rechaza en construcción** `TSIZE` cero (R-MJ1 en el tipo) y `UMBRAL_MUDA × 125 µs ≥ T_WATCHDOG_TRAMA` (la marca tiene que subir antes de que el módulo suelte, o no sirve para avisar).
11. **Mutación**: seis máquinas independientes; un `PlazoVencido` en la ranura 3 no toca ninguna cuenta de las otras cinco.
12. **El presupuesto lee los umbrales del artefacto**: `recuperacion_j2_budget.py` falla si `struct Umbrales` cambia de forma o de nombre (R-MJ4).

---

## 8. Los guiones

**`hardware/02-midi-cv/recuperacion_j2_budget.py`** (nuevo). Importa `F_LAZO_HZ` y `T_MENSAJE_MAX_S` de `trama_j2_budget`, `F_PELDANO_2_HZ` de `enlace_budget`, y lee `struct Umbrales` de `maestro_j2.rs` por regex (como `pio_budget.py` leía `pinout.rs`). Declara `T_WATCHDOG_TRAMA_S = 50e-3` con su fuente y ESTIMADO, y `T_REINICIO_S = 20e-6` ESTIMADO. Asevera:

- `plazo(msg) ≤ FACTOR × T_MENSAJE_MAX + SUELO` para cada mensaje de la cabecera §4, al piso y a D8.
- `t_recuperacion = plazo_max + T_REINICIO + 2/F_LAZO` (alineación más un giro) y `t_recuperacion × 10 < T_WATCHDOG_TRAMA` (margen ≥ 10×; hoy da 102×).
- `UMBRAL_MUDA / F_LAZO < T_WATCHDOG_TRAMA` (la marca `muda` sube antes de que el módulo suelte).
- CPU por reinicios, peor caso: `F_LAZO × T_REINICIO` por ranura, impreso, sin aserto (es cota, no presupuesto).
- `P(golpe perdido por cuelgue) = 3 × p_evento`, impresa como función para `p_evento` en `{1e-3, 1e-2, 1e-1}`, sin aserto: los dos parámetros no son de este guion.
- `T_IWDG > T_WATCHDOG_TRAMA` **como requisito mandado al hub**, leído de donde el hub lo declare cuando lo declare; hasta entonces, HUECO impreso.

Sale con `2` (HUECO) mientras `resistencia_j2.csv` no tenga fila o el hub no declare `T_IWDG`; con `0` cuando los dos existan y los ESTIMADO se hayan sustituido; con `1` si algún aserto falla.

**`software/nucleo/fw/resistencia_j2.csv`** (nuevo, vacío hasta la Discovery). Columnas: `ranura, instancia, tsize, nss, reloj_MHz, horas, giros, plazos_vencidos, eot_tardios, subidas_malas, fecha, placa`.

---

## 9. Riesgos, con su criterio de cierre

| # | Riesgo | Cierre |
|---|---|---|
| 1 | **El defecto del N6 sale igual con NSS por hardware.** No cambia el diseño (D4 lo cubre), pero sí la tasa y el desgaste | La Discovery, un enlace a 8 kHz durante ≥ 24 h, `resistencia_j2.csv` con fila. Si la tasa es del orden del hilo (período de minutos a horas), el diseño aguanta con margen de sobra; si es de varias por segundo, hay que mirar el driver de `fw` antes de culpar al silicio |
| 2 | **Los ESTIMADO de D3 se quedan cortos** y el plazo vence en tramas sanas (falsos reinicios) | Osciloscopio en el bring-up: `t_real(msg)` contra `t_nominal(msg)`; `FACTOR_PLAZO` se fija con ≥ 3× el peor exceso medido |
| 3 | **El módulo no limpia su SPI al contar corto** y arrastra medio byte: las tramas siguientes fallan CRC hasta que algo lo realinee | La enmienda al papel del módulo (§10) y su test: abortar una trama a mitad de byte desde el maestro y ver que la siguiente se acepta |
| 4 | ~~embassy-stm32 no expone lo que el driver propio necesita~~ | **Cerrado en la v2**: verificado en `main` (§1.2, último párrafo). Queda que compile, y eso es el primer paso del plan |
| 5 | **`EOT` se pone al rehabilitar** (p. 3492) y el orden `SPE = 1 → EOTC → EOTIE` de D2 no basta por alguna razón que el manual no dice | Bring-up: cien mil transferencias contando `eot_tardios` y `plazos_vencidos` con el bus al aire; si alguno sube sin cuelgue real, el orden se revisa |
| 6 | **El canal de GPDMA no responde al reset** y el `Drop` del `Transfer` de embassy se queda en su bucle | **Enmendado el 18-09:** cota `T_CANAL` al soltar y escalada al reset del GPDMA1 por RCC (D4.2), en vez de «lo cubre el IWDG». Cierra en la placa: inducir un canal trabado (pausarlo por registro desde otra tarea, con el bus al aire) y ver que las otras cinco ranuras siguen girando y que `escaladas_gpdma` sube en uno |
| 7 | **Las dos ranuras por USART síncrono** no tienen plazo, reinicio ni cuenta | Su propio papel antes de que lleven módulo; hasta entonces son repuesto sin módulo, y el planificador las trata como `Vacia` |
| 8 | **Un búfer de DMA cacheado** da datos viejos con CRC bueno | R-MJ7 en el plan; el test de bring-up compara el búfer contra el analizador lógico |

**Acciones que este papel manda, baratas:**

1. **Comentar en #5607** con el borrador de D8.1. Sale con la cuenta de Samuel; se pide en la conversación.
2. **Añadir a #231** la prueba de resistencia y el osciloscopio de D3 como cuarta y quinta razón de la Discovery.
3. **Cerrar #287** cuando este papel se firme: sus puntos 1 a 3 quedan decididos aquí.

> **Enmienda del 2026-09-08 (§9, acción 1; D8.1):** **hecha el 2026-09-03**.
> Samuel publicó la pregunta en [#5607](https://github.com/embassy-rs/embassy/issues/5607)
> y jake-taf respondió ese mismo día. Este intercambio también supera el
> corte de actividad del 2026-06-24 citado en §0. Sobre C, la respuesta fue:
> *«We wrote some small test firmware for C, but had issues getting probe-rs working on C.»*
> No aporta un resultado de la comparación contra el HAL de C; ese resultado
> sigue siendo **HUECO**, y **silicio contra driver sigue sin dirimir**. La
> hipótesis del `EOT` releído (punto 3 de la pregunta, D8.1) no fue contestada.

> **Enmienda del 2026-09-11 (§9; acta del 11-09, firmada por Samuel en el artifact «Acta del J2»):**
>
> 1. **Puerta de fabricación** (ficha 1). Ninguna PCB con N657 sale al taller sin una fila medida en `resistencia_j2.csv`. Antes era criterio de cierre del riesgo 1; desde hoy es prohibición. `recuperacion_j2_budget.py` la imprime como condición y deja de devolver 2 fijo (#369).
> 2. **El límite que descarta al chip** (ficha 2): **cero artefactos audibles atribuibles al bus.** Samuel lo eligió sobre la opción que la junta recomendaba (≤ 1 por 10 h de toque, que equivalía a un cuelgue cada 49 s en el instrumento). Para ser medible necesita un **horizonte**, cero en cuántas horas de instrumento, que queda **HUECO** y es suyo. La aritmética que lo convierte en puerta: con cero eventos en T horas de soak, la tasa queda por debajo de 3/T al 95 % (regla de tres, Poisson); «cero en H horas» exige del orden de 3·H horas limpias con el control positivo hecho. El riesgo 1 deja de cerrar «con fila»: cierra cuando la cota medida multiplicada por H queda por debajo de uno.
> 3. **El soak no va primero: va el control positivo.** Un soak limpio no ejecuta D4 y no distingue «no nos afecta» de «el banco no lo ve». Orden del día de la placa (Halberg, H-7): (0) `SPE = 1` sin armar nada y leer `SR.EOT`; (1) reproducir la configuración de jake-taf (embassy, 100 kHz, CS por GPIO, `TSIZE = 0`, `blocking_read`), donde 1 h da 98 % de potencia contra el extremo suave del hilo; (2) barrido del retardo entre `SPE = 1` y `CSTART` en {0, ¼, ½, 1, 2, 4} × T_SCK en esa configuración; (3) nuestra configuración con el driver de embassy; (4) el driver propio; (5) el HAL de C de ST solo si queda un cuelgue que el propio no limpia. Con la tasa por armado, 15 min en una ranura contestan p < 4,2e-7 al 95 %; 24 h contestan la hipótesis por tiempo (λ < 0,125/h).
>
>    *Lectura del 18-09 (fase B, rulings R4 y R22):* el barrido del retardo (2) corre sobre **la configuración con `EOT`** (`TSIZE > 0`, NSS por hardware, el driver propio), no sobre la de jake-taf: el mecanismo de ES0396 §2.14.2 necesita eventos `EOT`, y con `TSIZE = 0` no los hay (es el tercer workaround de esa misma errata). Y el control positivo (1) corre a **250 kHz**, no a 100: con el kernel del SPI en HSI 64 MHz el divisor máximo de `MBR` es /256; la hipótesis por tiempo (un cuelgue cada ~900 s) no cambia y la por armado gana potencia; si el banco no ve nada, la variante a 125 kHz (MSI 4 MHz por el selector del SPI4/5, /32) queda anotada en `EN-PLACA.md`.
> 4. **El criterio del riesgo 5 no discrimina.** Cien mil transferencias son 12,5 s a 8 kHz y acotan p < 3e-5 al 95 %, que no excluye ni el peor extremo del hilo (2e-5). El binario `eot_al_aire` de `EN-PLACA.md` pasa a ser el barrido del punto 3.
> 5. **Acción 1, segunda vez, hecha el 2026-09-11.** Samuel publicó en [#5607](https://github.com/embassy-rs/embassy/issues/5607#issuecomment-5636099116) que ES0620 Rev 5 no lista el SPI, la errata 2.14.2 del H7 como hipótesis con su cálculo, el §2.2.1 del N657, las dos comprobaciones baratas del punto 3, y la pregunta de si alguien abrió caso con ST por el canal formal. Sin respuesta al cierre de esta enmienda.
> 6. **ES0620 Rev 5 leída y versionada** (`docs/reference/datasheets/stm32n6-es0620-rev5.pdf`, PR #365): ningún ítem del SPI; tres que tocan este proyecto: §2.2.1 (#363), §2.2.22 (#364), §2.15.1 (#350). El riesgo «errata joven» de los papeles del motor se cerraba midiendo arranque, no leyendo la errata: #370.
> 7. **Lo que la junta encontró fuera del alcance de este papel**, con issue: el esclavo N657 sin recuperación (#366); los tres buses SPI del CV sin papel (#367); el `Drop` del GPDMA sin cota que congela las seis ranuras, riesgo 6 (#368); el `EVENTO` que sí tiene red y se repara tarde y a fuerza máxima, contra lo que dicen D4.8, D6 y §3 (#371, enmienda pendiente a este papel); y el sello de vitalidad al armar que ciega al IWDG ante una ranura que se rearma para siempre (comentario en #291).

---

## 10. El mapa de enmiendas

| Papel | Sección | Tipo | Qué | Vehículo | Estado |
|---|---|---|---|---|---|
| hub N657 | §10 fila 6 (*«Drivers de embassy-stm32 para el N6 (SPI, ...)»*) | Expand | Para el SPI: embassy lo tiene y expone lo necesario, pero sus dos esperas no son cancelables y `write`/`transfer` van con `TSIZE = 0`; el J2 lleva driver propio hasta D8.2 | este papel | pendiente |
| hub N657 | nueva: el supervisor de vitalidad | Add | Quién alimenta el IWDG, con qué sellos y con qué plazo; requisito del J2: `T_IWDG > T_WATCHDOG_TRAMA` y un sello por ranura activa al armar. Y el silencio que añade un reinicio del cerebro, cuantificado | papel del hub | pendiente |
| hub N657 | nueva: los ejecutores | Add | El J2 vive en un `InterruptExecutor` propio por encima del de hilo; qué más va ahí y qué se queda en el hilo | papel del hub | pendiente |
| cabecera J2 | D8 (*«el esclavo rearma el DMA de recepción antes de validar nada»*) | Patch | Antes de rearmar, al contar corto en el flanco: `SPE = 0 → SPE = 1` en el SPI del módulo (RM p. 3450: *«any ongoing data are lost when disabling the SPI»*). Una línea en la ISR | papel del módulo / cabecera | pendiente |
| cabecera J2 | §3.3 (`perdidas ≥ rechazadas`) | Clarify | Del lado del cerebro, `plazos_vencidos + eot_tardios` son las tramas que el cerebro abortó o dio por abortadas; `perdidas − rechazadas − plazos_vencidos` es lo que de verdad se perdió por el cable. Los `eot_tardios` sí llegaron al módulo | este papel | pendiente |
| voz-total | §9.2 (*«N del plan, ~50»*) | Patch | El watchdog de trama gana un cliente del otro lado: es la ventana de recuperación del maestro. `N` pasa a constante importable (`T_WATCHDOG_TRAMA_S`), hoy ESTIMADO 50 ms, **con dos cotas**: piso del margen (este papel, ≥ 10 × recuperación) y techo del sustain fantasma (voz-total, HUECO) | PR de nivelación | pendiente |
| J2 punto a punto | *«(oyentes, la recuperación): del papel que reemplace al #201»* | Sync | La recuperación del lado del maestro está aquí; la del #201 (la Voz sin maestro) sigue donde estaba | este papel | pendiente |
| `micro_budget.py` | censo del hub, `J2:SPIn_NSS` | Clarify | El NSS por hardware pasa de reparto a **requisito**: sin él, D1 no se sostiene. Y las dos ranuras USART quedan fuera de este papel | comentario en el guion | pendiente |
| #250 | «Lo que hay que tocar» | Sync | El puerto incluye `j2_spi.rs`, el ejecutor del J2, los búferes no cacheables (R-MJ7); y el primer paso es compilar un `j2_spi.rs` vacío contra las cuatro APIs de §1.2 | issue | pendiente |
| #231 | la lista de lo que la Discovery mide | Expand | La prueba de resistencia (riesgo 1), el osciloscopio de D3 (riesgo 2), y el conteo de `eot_tardios` con el bus al aire (riesgo 5) | issue | pendiente |
| #287 | — | Cierra | Puntos 1 a 3 decididos aquí | `gh issue close` al firmar | hecho |
| **este papel** (11-09) | D2, el orden de arranque | Patch | Espera anclada ≥ 1 T_SCK entre `SPE = 1` leído de vuelta y `CSTART`, por analogía con ES0396 §2.14.2 del H7; ES0620 no lista el SPI | enmienda del 11-09 en D2 | **aplicada** |
| **este papel** (11-09) | §9 riesgos 1 y 5, acción 1 | Expand | Puerta de fabricación; límite de cero artefactos audibles con horizonte HUECO; control positivo antes del soak; el criterio del riesgo 5 no discrimina; segundo comentario en #5607 | enmienda del 11-09 en §9 | **aplicada** |
| **este papel** (11-09) | D4.8, D6, §3 («`EVENTO` no tiene red») | Patch | La cabecera da red al `EVENTO` (`COMPUERTA`, R-E11) y el evento repara a `u16::MAX` sin tono de arranque: la degradación es otra y la función de §3 cambia | #371 | pendiente |
| **este papel** (11-09 → 18-09) | D4.2, R-MJ2, §9 riesgo 6 | Patch | Cota `T_CANAL` al soltar los canales (`request_pause` + sondeo; NO `request_reset`, que ya trae el bucle sin cota) y escalada al reset del GPDMA1 por RCC, en vez de «lo cubre el IWDG»; no un ejecutor aparte; #368 | enmienda del 18-09 en D4.2, corregida el mismo día | **aplicada** |
| **este papel** (18-09) | D2 regla 1 | Clarify | La generación no puede rechazar nada por sí sola (el EOT no viene etiquetado); la protege la regla 2 + EOTIE + `NVIC::unpend` en D4.1 y D4.7 | enmienda del 18-09 en D2 | **aplicada** |
| **este papel** (18-09) | D5.1, §3 | Patch | Tras un plazo vencido la ranura se realinea (`Ticker::reset`), no recupera tics: honra `T_GAP` (cabecera D8) y mantiene los 490 µs | enmienda del 18-09 en D5 | **aplicada** |
| **este papel** (18-09) | §9, enmienda del 11-09, punto 3 | Clarify | El barrido corre sobre la configuración con `EOT`; el control positivo a 250 kHz, no 100 | lectura del 18-09 en §9 | **aplicada** |
| papel del módulo | nueva: recuperación del esclavo | Add | Plazo, reinicio y cuenta del lado esclavo, espejo de D2-D4; y la política de `muda` en el cerebro | #366 | pendiente |
| motor-digital | §5, los tres buses SPI del CV | Add | Papel de recuperación de los buses del tono y censo de todos los maestros SPI con su consecuencia audible | #367 | pendiente |
| hub N657 | supervisor de vitalidad (D5.4) | Patch | El sello no puede ser «armé»: «armé y alguno de los últimos N terminó», o el supervisor lee `inestable`/`muda` | comentario del 11-09 en #291 | pendiente |
| `recuperacion_j2_budget.py` | `demo()` | Rewrite | `return` calculado, no fijo: lee la fila, cota 3/T, horizonte, puerta de fabricación impresa | #369 | pendiente |
| `EN-PLACA.md` | «El J2 en la Discovery» | Expand | Control positivo primero; `eot_al_aire` pasa a barrido del retardo; límite cero; prioridad de la ISR; método de reset de probe-rs | enmienda del 11-09 | **aplicada** |
| plan 2026-09-04 | Fase B | Sync | Desbloqueada el 08-09 (#349); enmiendas antes del driver; `spi_v5` | enmienda del 11-09 | **aplicada** |
| #231 | la lista de lo que la Discovery mide | Expand | Sexta razón: el soak es puerta de fabricación; la Nucleo ahora; control positivo primero; HUECOS: costo puesto en la puerta y los dos extremos en una placa | comentario del 11-09 | **hecho** |
| `references.md` y el árbol | erratas | Add | Regla: ningún papel se firma sobre un periférico sin su errata versionada; faltan RA8M1 y H750; barrido de ES0620 contra los papeles vivos | #370 | pendiente |

---

## 11. Registro de la junta

Tres lentes sobre la v1, el mismo día, antes de pedir la firma (memoria del 02-09: *«el orden bueno es brief → papel → junta → firma»*). Serrano (S), clínica, con la aritmética recalculada y las diecisiete citas del RM verificadas contra el volcado; Halberg (H), runtime con cinco simulaciones en Python (scratchpad de la sesión, `junta_halberg/sim1`, `sim1b`, `sim2`, `sim3`, `sim4`); Voronov (V), ontológica.

| Hallazgo | Qué cazó | Resolución |
|---|---|---|
| **S-1** BLOCKER, **V-1** BLOQUEANTE, **H-4** BLOCKER | El CRC de hardware del SPI rompía el sobre en las dos direcciones: trama CRC aparte tras `TSIZE`, y `CRCE` en cada giro de subida. La cabecera D2 ya lo había descartado | D1: `CRCEN = 0`; el CRC es el del sobre; «los tres van juntos» → los dos |
| **S-2** HIGH | §1.2 leía embassy al revés: `read` es la que fija `TSIZE`, `write` y `transfer` no; el cuelgue DMA del hilo fue en `read` con `TSIZE > 0` | §1.1 y §1.2 corregidos; D1 «por qué importa» reducido a lo que el código sostiene (NSS); comentario upstream reescrito |
| **S-3** BLOCKER de forma | La cita de p. 3484 llevaba «(...)» y el acta juraba citas enteras; la Tabla 661 iba como cita con guiones | D4.5: la cita entera; D2: la tabla como tabla |
| **S-4** HIGH | El reinicio omitía el paso 3 del manual (`TXDMAEN`/`RXDMAEN`), encendía al final sin poder armar, y el atajo de `SUSP` apagaba con la suspensión a medias | D4: ocho pasos en orden; termina apagado; `SUSPC` incondicional; D2: el SPI apagado entre transferencias |
| **S-5** HIGH, **V-9** MEDIA | «El flanco lo realinea» citaba al esclavo recién habilitado; nada decía qué pasa con medio byte en el esclavo interrumpido | D4: enmienda mandada al módulo (`SPE = 0 → 1` al contar corto, p. 3450); riesgo 3 |
| **S-6** HIGH, **V-2** BLOQUEANTE, **H-7** MEDIUM | Sondear con `HOLA` era abrir sesión: `SoltarTodo` y contadores a cero cada 100 ms, contra R-C7 | D7: muere el sondeo; nunca se deja de girar; `HOLA` solo cuando la cabecera D5 dice |
| **S-7** HIGH, **V-4** ALTA, **V-5** ALTA, **H-1** BLOCKER, **H-2** BLOCKER, **H-9** HIGH, **H-10** MEDIUM | El vigía: no cubría nada que D3 no cubriera; no podía soltar los `Transfer` de la tarea; una sección crítica lo congelaba con lo que vigilaba; contaminaba la ventana de las seis ranuras; hacía absorbente el estado enfermo; reiniciaba ranuras sanas con una pantalla de 6 ms | D5: muere el vigía. Seis tareas en un ejecutor propio del J2; el planificador único escritor |
| **S-8** HIGH | Seis enlaces sin modelo de concurrencia: en serie no caben al piso (132 > 125 µs); con `join` un plazo retrasa a las seis | D5.1: una tarea por ranura, en paralelo por hardware |
| **S-9** MEDIUM, **H-3** HIGH | 200× contra 137×; «≤ 2 giros» no era el peor caso; `HOLA` de 7 bytes | §3: 490 µs, 3 giros, 102×; `HOLA` 9/25 bytes |
| **S-10** MEDIUM, **V-7** ALTA | La tasa del hilo normalizada contra tramas nuestras; el 10⁻² sin derivación; «no cruza al músico» como invariante cuando `EVENTO` no tiene red; los 50 ms con dos caras | D6: no se normaliza; `P(golpe perdido)` como función; §3: las dos caras, la segunda HUECO de voz-total |
| **S-11** MEDIUM | «Se repite en 125 µs» contradecía la cabecera D6.2: el módulo avanza al contar bytes, no al validar el maestro | D6: la subida corrupta se pierde hasta la próxima publicación (1 Hz) |
| **S-12** MEDIUM, **H-11** MEDIUM | La ISR y el reinicio se pisaban por `EOTIE`; la bandera guardada sin dueño; solo `EOTIE`; p. 3492 contra p. 3490 sobre `EOT` al rehabilitar | D2: generación por transferencia, borrar al armar, `poll` registra antes de mirar, `EOTC` tras `SPE = 1` y antes de `EOTIE`; D4.1: `EOTIE = 0` primero; riesgo 5 |
| **S-13** MEDIUM, **V-11** MEDIA, **H-8** LOW | R-MJ2 prohibía el sondeo acotado que D4 necesita y su grep no veía ni el `Drop` del GPDMA ni `T_SUSP`; el `Drop` citado era del DMA clásico, y el N6 va por GPDMA | R-MJ2: «sin cota»; D4.2-4.3: las dos esperas acotadas declaradas; `gpdma/mod.rs:1287-1295` y `:902-910`; riesgo 6 |
| **S-14** MEDIUM, **H-5** MEDIUM | `TSIZE = sobre + cola` omitía el CRC del sobre y el relleno; «más de 10» contra «10» en el test | D1.1: `TSIZE` = bytes clocados de §4; D7 y test 6: `≥` |
| **S-15** LOW | Las ranuras vacías contaban CRC malo a 8 kHz y daban la vuelta al `u32` en seis días de instrumento encendido | D7.4: `Vacia`; R-MJ6 |
| **V-3** ALTA, **H-13** HIGH | La ranura enferma garantizaba el release (100 ms > 50) y tardaba 10 s en volver; sin ella, ningún hueco llega a 50 ms hasta p = 0,5 | D7: muere la cadencia reducida; la salud es una marca |
| **V-6** ALTA, **H-6** MEDIUM | El IWDG alimentado por el J2 definía la vida del chip como «el J2 giró»; con una ranura sin módulo disparaba diez veces por segundo | D5.4: el IWDG es del hub; supervisor de vitalidad mandado; sello por ranura al armar |
| **V-8** MEDIA | «Toda transferencia» eran seis de ocho: las dos ranuras USART no tienen `TSIZE` ni NSS ni SPI | §0: alcance seis SPI; riesgo 7 |
| **V-10** MEDIA, restricción invisible | El maestro no tenía testigo: «sana» significaba «mi periférico funciona» y excluía por diseño lo único que no produce el acusado | D7.3: la subida con su CRC es el testigo por giro; `muda`; `giros` y `subidas_ok` se cuentan aparte |
| **V-12** BAJA | «Driver de bus propietario» era etiqueta; la razón real es que embassy no cancela, y la cláusula de retiro lo desmentía | D8: driver genérico de SPI, honesto; frontera `fw`/`core` trazada |
| **H-12** LOW | Nada decía dónde viven los doce búferes de DMA en un chip con D-cache | D8, R-MJ7, riesgo 8 |
| S: la aritmética | Recalculó §3 entero: cadencia, reloj, cotas, `HOLA`, reinicio, giros, margen, tasa, `u32` | Cuadraban cadencia, reloj, cota de plazo, ventana, `u32`; no cuadraban `HOLA`, giros, margen y la tasa: §3 recalculado |
| H: lo que sí corre | sim1 modo A (1-2 giros, 200×/133×); sim4 (la red del bloque completo aguanta hasta 10⁻²); sim2 parte 2 (con bandera limpia, cero registros inconsistentes) | Se citan en D6 y §3 como evidencia, no como promesa |

**Lo que la junta no cambió:** el plazo por mensaje de R-E1 (D3), la receta de apagado como base del reinicio (D4), que la política viva en `core` y el driver en `fw` (D8), y que lo que se aprenda vuelva upstream.

---

## 12. Acta

- Samuel, 2026-09-03: *«bueno vamos a resolver esto pero como fabricantes de la nueva generación. el sam17 será el mejor sintetizador construido jamás»*, tras la conversación sobre cómo lo evitaría un fabricante establecido. La lectura de esa instrucción que este papel aplica: el silicio nuevo y el Rust se quedan; la disciplina de fabricante entra; no se espera a upstream para tener recuperación, y lo que se aprende vuelve upstream.
- Este papel se escribió leyendo, en este orden: el hilo #5607 entero con sus 24 comentarios y el volcado de registros; `embassy-stm32/src/spi/mod.rs` (`main`, 2130 líneas: `write`, `read`, `transfer_inner`, `finish_dma`, `Drop`, el constructor con NSS), `dma/gpdma/mod.rs` (`Channel::read`/`write`, `request_reset`, `Drop for Transfer`), `dma/mod.rs` (`Channel::new`, `Request`), `rcc/mod.rs` (`enable_and_reset`), `macros.rs` (`dma_trait!`), `executor.rs` (`InterruptExecutor`); `stm32-data-generated/data/chips/STM32N657X0.json` (IWDG, SPI1-6); el RM0486 Rev 4 cap. 67 en las páginas 3437-3440, 3445-3451, 3452-3456, 3457-3459, 3482-3484 y 3489-3493, sacadas del PDF versionado con `pypdf` y citadas enteras; la cabecera del J2 D2-D8, §3.1, §3.3, §4 y R-C1..R-C8; voz-total §9.2; `trama_j2_budget.py`, `enlace_budget.py`, `sancion_j2.csv`; `micro_budget.py` corrido; `fw/src/main.rs` y `core/src/j2.rs`.
- Cada cita del RM se pegó entera y textual con su página, y la interpretación va fuera de las comillas (memoria del 03-09: *«un corchete dentro de una cita es una interpretación disfrazada de fuente»*). La v1 tenía una recortada con «(...)»; Serrano la cazó y la v2 la lleva entera.
- La v1 pasó la junta **antes** de pedir la firma. Siete decisiones cambiaron de mecanismo o murieron (D1, D2, D4, D5, D6, D7, D8) y llevan ⚠; D3 sobrevivió con una cifra corregida. La v1 defendía 200× con un vigía; la v2 defiende 102× sin él, y lo que ejecuta es lo que dice.
- Lo que este papel no midió y dice que no midió: todo lo marcado ESTIMADO en §3, la tasa real del defecto en nuestro montaje, y cuánto sustain fantasma es tolerable. No hay Discovery.
- Samuel, 2026-09-10: *«firmo formalmente»*. Firma de contenido, no solo de dirección: las ocho decisiones (D1-D8) quedan en vigor tal como salieron de la junta del 2026-09-03, sin matiz. Firmar el papel no aplica el mapa de enmiendas (§10): sus filas siguen `pendiente` hasta que alguien las ejecute en el papel que corresponde — la fila «hub N657, los ejecutores» es, en concreto, lo que el censo de GPDMA y prioridades de interrupción (#150, punto 2) tiene que escribir.
- Samuel, 2026-09-11: frenó la tarea 7 con *«si el chip que usamos tiene un defecto reportado […] no podemos seleccionarlo. nunca podríamos confiar en él»* y pidió junta. El orquestador había dicho en la conversación «el chip tiene un defecto» donde este papel dice «en el silicio o en su driver»; la junta arrancó con esa corrección en la primera línea del brief. Seis lentes (Serrano, Halberg, Voronov, Richter, Lyra, Cassian) descartaron cambiar de chip por unanimidad y encontraron los huecos del punto 7 de la enmienda de §9; sus dictámenes, el brief, el extracto de ES0396 y el hilo #5607 quedan en `docs/superpowers/juntas/2026-09-11-j2/`. Después de la junta se leyó ES0620 Rev 5, que no lista el SPI.
- Samuel, 2026-09-11, 15:27 UTC: firmó el «Acta del J2» (artifact, documento `firmas/junta-2026-09-11`) marcando las cuatro fichas y sin palabras añadidas: **seguir con el N657, y nada se fabrica hasta medir** (ficha 1); **cero artefactos audibles** como límite (ficha 2, sobre la opción recomendada); **primero las enmiendas, después el driver** (ficha 3); **la Nucleo-N657X0-Q ahora** (ficha 4). Lo que la firma habilita está en las enmiendas del 11-09 a D2 y §9, en las filas nuevas de §10, y en #363, #364 y #366 a #371. Lo que la junta no cambió: D1, D3, D5 a D8, y la frontera `fw`/`core`.
