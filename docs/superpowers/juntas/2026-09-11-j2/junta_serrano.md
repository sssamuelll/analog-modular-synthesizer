# Junta del SAM17 — 2026-09-11 · Dictamen clínico (Serrano)

## A) Resumen diagnóstico

Documento: brief de junta (decisión de plataforma) apoyado en una spec firmada de recuperación, un hilo de issue abierto y una errata de **otro** chip. Mezcla tres géneros: evidencia externa, diseño firmado y cuatro opciones de negocio.

Implementabilidad hoy: la spec firmada es implementable (su fase A ya corre); **la pregunta de la junta no es decidible con lo que hay escrito**, porque en ningún papel del repo existe una cota de tasa que convierta «el chip se cuelga» en aceptable o inaceptable. Sin esa cota, ni A ni B pueden aprobar ni reprobar, y C/D se deciden por sensación.

**5 BLOCKERS, 7 HIGH, 3 MEDIUM.** Los dos agujeros más grandes no son del N657: son (1) que el criterio de cierre no mide lo que dice medir y (2) que la red de seguridad cubre 6 de los enlaces SPI del instrumento y el resto del SPI —incluidos los 3 buses de CV a velocidad de audio— no tiene ni plazo ni reinicio ni cuenta.

---

## B) Hallazgos

### 1. [BLOCKER] [GAP · AMB · OPS] No existe la cota que haría falsable la frase «no podemos confiar en él»
**Evidencia:** brief §1: *«no podemos seleccionarlo. nunca podríamos confiar en él»*. Spec §9 riesgo 1: *«si es de varias por segundo, hay que mirar el driver de `fw` antes de culpar al silicio»*. Spec §3: *«`P(golpe perdido) = 3 × P(EVENTO en un giro)` por cuelgue | función, sin cifra»*.
**Problema:** ningún papel escribe una tasa de cuelgue ni de corrupción por encima de la cual el N657 queda descartado. Lo único con cota escrita es el margen temporal de UNA recuperación (`recuperación × 10 < T_WATCHDOG_TRAMA`) y los umbrales de reporte (`UMBRAL_INESTABLE = 10` en 1 s), que la propia spec declara *«información, no acción»* (D7.3).
**Impacto:** el soak no puede reprobar: cualquier número es «el número». La pregunta de hoy no tiene criterio, así que la respuesta será una preferencia, no una decisión. Aplica igual a A, B, C y D.
**Qué hay que decidir/definir:** ¿cuál es la tasa máxima de cuelgues/hora y de tramas corruptas/hora, medida en nuestro montaje, con la que el instrumento se fabrica — y cuál es la que lo descarta?

### 2. [BLOCKER] [GAP · OPS · ASSUMP] La errata del chip elegido nunca se leyó, y el riesgo «errata joven» se cierra midiendo otra cosa
**Evidencia:** benchmark §6: *«silicio con errata joven (12/2024)»*. Motor-digital §11 riesgo 6: *«Errata joven / boot firmado / Rust vivo | FSBL + binario Rust corriendo en Nucleo-N657»*. Brief §3.4: *«NO LEÍDA. HUECO: pedirle el PDF a Samuel.»* `docs/references.md` indexa DS14791 Rev 10, AN5967 y RM0486: **ninguna errata**.
**Problema:** el proyecto selló en agosto «errata joven» como precio aceptado sin leer el documento que la enumera, y el criterio de cierre de ese riesgo mide arranque (FSBL+Rust), no erratas. `grep -ri errata` en el repo no devuelve ES0620 ni una vez.
**Impacto:** se está discutiendo si el defecto es del silicio con el documento del fabricante sobre los defectos del silicio sin abrir. Es el dato más barato del tablero (coste: cero) y es el único disponible hoy sin placa.
**Qué hay que decidir/definir:** ¿quién pone ES0620 Rev 1 en `docs/reference/datasheets/` y en `references.md`, y qué decisión cambia según si lista o no el gemelo del 2.14.2?

### 3. [BLOCKER] [SCOPE · GAP] La red cubre 6 ranuras; el resto del SPI del instrumento no tiene plazo, reinicio ni cuenta
**Evidencia:** spec §0: *«Alcance: las seis ranuras SPI»*. Motor-digital §5: *«La topología: 3 buses SPI maestros punto a punto, a 50 MHz nominales»*, *«en DMA puro (lista enlazada, cero CPU)»*. Motor-digital §11 riesgo 9 cubre *«El N657 colgado deja 48 VCAs sin gobierno»* con R-M5, que es silencio **por muerte de CPU**.
**Problema:** si el defecto es del bloque SPI (`spi_v5`), los tres buses de CV a 48 kHz, el enlace del DAC y el resto de los SPI del instrumento están expuestos y no tienen ni plazo, ni reinicio, ni contador, ni marca de salud. Un cuelgue ahí es un corte de filtro congelado con la CPU viva: R-M5 no dispara porque la CPU no murió.
**Impacto:** «recuperación + medición = confianza» es verdadera para el J2 y no está escrita para el camino que sí cruza al audio. La premisa de A y B se defiende sobre una fracción de la superficie expuesta.
**Qué hay que decidir/definir:** ¿qué papel le debe plazo/reinicio/cuenta a los 3 buses de CV y al enlace del DAC, y se decide antes o después de fabricar?

### 4. [BLOCKER] [ASSUMP · OPS] El soak de ≥ 24 h no declara potencia ni aprobado, y el propio hilo ya produjo un falso «resuelto» a esa escala
**Evidencia:** `5607-comments.md`: *«Seems resolved on the latest build, but we'll see»* (10-03) → dos meses después *«Not resolved, just less likely it seems (anywhere from several minutes to two hours…)»*. `EN-PLACA.md`: *«sin módulo `subidas_malas` cuenta todo y no importa, lo que se mide es `plazos_vencidos`»*.
**Problema:** con período de 30-120 min, 24 h dan ~12-48 eventos: no distingue «curado» de «más raro», y nadie escribió cuántos eventos ni qué confianza hacen falta. Y el procedimiento, tal como está redactado, mide cuelgues con el MISO al aire: **no mide corrupción**, que es el síntoma sin red para `EVENTO`.
**Impacto:** la «puerta dura» de la opción A puede dar verde con el defecto intacto, y da verde sin haber medido el segundo síntoma.
**Qué hay que decidir/definir:** ¿cuántas horas, cuántos eventos y con qué otro extremo (módulo real con CRC o aire) constituyen un soak aprobado, y qué valor de `plazos_vencidos`/`subidas_malas` lo reprueba?

### 5. [BLOCKER] [ASSUMP · GAP · SCOPE] La opción C no tiene destino acreditado: el retorno declarado no pasa el censo que el N657 ya pasa
**Evidencia:** `docs/references.md:76`: RA8M1, *«El retorno declarado»*. Benchmark: *«RA8M1: SPI ×2 «up to 60 Mbps» + SCI síncrono ×6 (p1) — timing de esclavo pendiente»*. Hub E-1: *«el hub necesita los 6 SPI del chip para las ocho ranuras de D3 y la Voz gasta 3 en el CV»*.
**Problema:** C se enuncia como «cambiar de chip» sin nombrar chip. El único destino que el repo declara tiene 2 SPI contra 6 requeridos y su tabla eléctrica de esclavo nunca se leyó. Segunda premisa no declarada: hub §2.2 apoya el reloj del enlace en *«con los dos extremos de la misma clase, C5 del evento se sostiene sin medir sesgos entre chips distintos»* — cambiar un extremo reabre el peldaño 2 (34,5 MHz) y C5 del evento de nota, que el brief no cuenta entre lo que arrastra.
**Impacto:** C cambia un defecto con tasa desconocida por una plataforma con censo reprobado y timing sin leer, y es la única opción irreversible (respin BGA→LQFP, benchmark §6).
**Qué hay que decidir/definir:** ¿qué chip concreto, con qué censo de 6 SPI corrido y qué tabla eléctrica leída, y quién paga el recálculo de D8 y de C5?

### 6. [HIGH] [CONTRA · ASSUMP · AMB] La premisa «es del silicio» se apoya en dos reportes y el brief se contradice sobre el único dato que los discriminaría
**Evidencia:** brief §3.1: *«**Dos reportantes**, los dos con embassy (Rust)»* y nueve líneas después, del segundo: *«No se sabe si usa embassy o C»*. Los volcados difieren: jake-taf `SR=0x1002` (`RXP=0`), stefkoriz `SR=0x12017` (*«CTSIZE≠0, RXP=1»*). Spec §0 mantiene la forma honesta: *«hay un defecto abierto en el silicio o en su driver»*.
**Problema:** la afirmación «hoy no existe ninguna evidencia fuera de embassy» y la afirmación «los dos son embassy» no pueden ser las dos ciertas si la atribución del segundo reporte está abierta. Además, dos estados de registro distintos se tratan como un modo de fallo único (H-1 de la spec).
**Impacto:** la frase de Samuel («defecto del chip») y la frase del papel («silicio o driver») se apoyan en la misma evidencia leída de dos maneras. Si stefkoriz no usa embassy, hay una reproducción fuera del driver y el peso cambia de lado; si usa embassy, la muestra es n=2 con un solo driver.
**Qué hay que decidir/definir:** ¿se le pregunta a stefkoriz qué SDK usa, y se admite que mientras no se sepa, «silicio» es hipótesis y no hecho?

### 7. [HIGH] [CONTRA · OPS] El presupuesto que debe cerrar el HUECO no puede cerrar nunca, y la fila que lo cierra no se lee
**Evidencia:** spec §8: *«Sale con `2` (HUECO) … con `0` cuando los dos existan y los ESTIMADO se hayan sustituido»*. `recuperacion_j2_budget.py:212`: `return 2` incondicional; `:197-201` añade el HUECO de `T_IWDG` sin comprobar si el hub lo declaró; `:104-108` `csv_tiene_fila` solo cuenta líneas no vacías.
**Problema:** el artefacto afirma su estado en vez de evaluarlo: ninguna combinación de evidencia futura lo pone en 0. Y una fila con 700 000 `plazos_vencidos` cierra el HUECO de R-MJ8 igual que una fila con cero.
**Impacto:** «medición = confianza» no tiene cierre mecánico. El día que llegue la placa, el guion seguirá diciendo lo mismo que hoy.
**Qué hay que decidir/definir:** ¿qué condición, verificable en el guion, define «el N657 pasó», y quién la escribe antes de que haya fila?

### 8. [HIGH] [AMB · ASSUMP · GAP] La hipótesis de la errata 2.14.2 no está cuantificada y la evidencia del hilo la debilita
**Evidencia:** ES0396 §2.14.2: *«With the system clock (spi_pclk) substantially faster than SCK … can stall upon setting the CSTART bit within one SCK cycle after the EOT event»*. Hilo: *«I tried different SPI speeds and it doesn't seem to matter (captures were for 100kHz)»*. Volcado: `MBR 0x7 // SPI master clock/256`.
**Problema:** *«substantially faster»* no tiene número, así que no se puede saber si nuestro montaje (10-34,5 MHz, razón de relojes ~1-2 órdenes menor que los ~10³-10⁴ del repro) cae dentro de la condición. El mecanismo predice dependencia fuerte con esa razón; el reportante dice que la velocidad no cambia nada. Y la errata describe un **stall**: no describe el bit duplicado ni el `CS` subiendo a mitad, que es el síntoma sin red para `EVENTO`.
**Impacto:** la hipótesis se usa para bajar la alarma sobre los dos síntomas explicando uno, y no hay escrita ninguna predicción que la pueda matar.
**Qué hay que decidir/definir:** ¿qué predicción numérica (tasa contra razón spi_pclk/SCK, con y sin el retardo de 1 SCK) se declara ANTES de medir, de modo que un resultado la falsee?

### 9. [HIGH] [ASSUMP · STATE] «El reinicio de D4 cura el periférico» no tiene evidencia para el N6, y no hay estado terminal para la ranura que no vuelve
**Evidencia:** spec §3: *«Margen: 50 ms / 490 µs = 102×»*. D7.2: *«16 % de un núcleo por ranura con todas sus tramas colgándose, 96 % con las seis … se acepta que un instrumento roto gaste CPU»*. La única evidencia de recuperación por reinicio es de otro montaje: *«Exit from this only to restart SPI engine»* (stefkoriz, SDK desconocido) y `HAL_SPI_Abort()` en el hilo del H743, en C.
**Problema:** el 102× mide el tiempo de UNA recuperación exitosa. Si el reinicio de ocho pasos (que termina en `SPE=0`, sin reset por RCC) no levanta el bloque, el lazo reinicia a 8 kHz para siempre: la máquina de D7 tiene dos estados (`Vacia`, `Activa`) y las marcas *«no cambian lo que la tarea hace»*. Quién declara el instrumento roto está delegado a un papel que no existe (§6, fila 1).
**Impacto:** el margen publicado es el mejor caso del fallo, no su cota. El peor caso no tiene estado, ni dueño, ni aviso al músico.
**Qué hay que decidir/definir:** ¿qué evidencia demuestra que el reinicio de D4 cura el cuelgue del N6, y qué pasa con una ranura que no vuelve tras N reinicios?

### 10. [HIGH] [ASSUMP · GAP] La opción B promete dirimir silicio contra driver «en un día» presumiendo aislamiento de una sola variable
**Evidencia:** brief §5 B: *«el primer experimento es el soak con el **HAL de C de ST** (dirime silicio vs driver en un día)»*. Hilo: *«We wrote some small test firmware for C, but had issues getting probe-rs working on C»*. Comentario de xoviat sobre el HAL de C: *«the ST code sets tsize»*, *«the ST code does not read/write to the tx registers»*.
**Problema:** el HAL de C difiere de embassy en varias variables a la vez (TSIZE, escrituras a TXDR, manejo de CS, orden de arranque). Un soak en C que no cuelgue no dice «el silicio está bien»: dice «esta combinación no cuelga». El repo no tiene una línea de C ni toolchain de ST declarada, y el reportante original no logró depurarlo.
**Impacto:** B vende un veredicto binario que su experimento no puede entregar, y lo vende como el camino más rápido.
**Qué hay que decidir/definir:** ¿cuál es la matriz de variables del experimento (framework × TSIZE × NSS × razón de relojes) y qué resultado concreto se acepta como «es el driver»?

### 11. [HIGH] [CONTRA · SCOPE · OPS] La opción A contradice el plan en vigor, y la «puerta dura» que invoca no está escrita en ningún papel firmado
**Evidencia:** brief §5 A: *«Escribir el driver hoy (tarea 7)»* y *«Puerta dura: soak ≥ 24 h … **antes de fabricar cualquier PCB** con N657»*. Plan: *«### Task 7 (bloqueada)»*; tabla: *«**B** (tareas 7-8) … **#250**, y la Discovery (#231) para medir»*. Spec R-MJ8 solo dice: *«el presupuesto sale con `HUECO` hasta que haya fila»*.
**Problema:** la tarea 7 está declarada bloqueada por #250 en el plan que la spec firmada engendró (el brief afirma aparte que #250 fase A cerró el 08-09: el estado real no está reconciliado en ningún documento). Y ninguna regla del repo ata la fabricación al soak: la única puerta escrita sobre compra de silicio es el censo de pines (*«No se compra silicio hasta su verde»*, motor-digital §1).
**Impacto:** A se presenta como «seguir el plan» cuando cambia el plan en dos puntos, uno de ellos una puerta nueva que nadie firmó.
**Qué hay que decidir/definir:** ¿está #250 cerrado al punto de poder compilar `j2_spi.rs` hoy, y la puerta «ningún PCB con N657 sin fila de resistencia» se escribe como regla o se queda como intención del brief?

### 12. [HIGH] [SCOPE · GAP · STATE] La opción D aterriza el J2 en el único periférico que la spec firmada dejó fuera de la recuperación, y cuyo modo maestro no está verificado
**Evidencia:** spec §0: las ranuras USART *«quedan fuera con su HUECO»*. §9 riesgo 7: *«Las dos ranuras por USART síncrono no tienen plazo, reinicio ni cuenta»*. Hub §2.2: *«Que sus USART tengan el modo síncrono como maestro queda por verificar en la hoja»*; hub §10.3 lo repite como pendiente.
**Problema:** D mueve el enlace crítico a un periférico sin diseño de recuperación, sin papel dueño, con capacidad de maestro síncrono **no verificada en la hoja** y con techo de 12,5 Mb/s contra los 34,5 MHz del peldaño 2. El brief menciona el techo de reloj pero no que la red de seguridad desaparece entera.
**Impacto:** D cambia un defecto conocido y con recuperación diseñada por un periférico sin defecto conocido **porque nadie lo ha corrido**, y sin recuperación.
**Qué hay que decidir/definir:** ¿quién verifica el modo síncrono maestro en la hoja y quién escribe plazo/reinicio/cuenta del USART antes de que D sea opción?

### 13. [MEDIUM] [CONTRA] Contradicciones entre la pregunta de hoy, el acta del 03-09, la firma del 10-09 y D6 — enunciadas como hechos
**Evidencia:** acta 03-09: *«vamos a resolver esto pero como fabricantes de la nueva generación»*. Firma 10-09: *«las ocho decisiones (D1-D8) quedan en vigor tal como salieron de la junta del 2026-09-03, sin matiz»*, sobre un papel cuyo sujeto es *«el cerebro (STM32N657…)»*. Hoy: *«no podemos seleccionarlo»*. D6: *«La tasa del hilo no se normaliza»*; hoy se cita esa tasa (*«cada varios minutos o cada varias horas»*) como propiedad de nuestro montaje. Brief §2: Discovery *«aplazada el 28-08 por decisión de Samuel: no hay plata»*.
**Problema:** cuatro hechos en tensión: se firmó el contenido hace 24 h con el N657 como sujeto; se descartó hace 14 días el único instrumento que puede medir ($223,67); se prohibió normalizar la tasa ajena y hoy se usa como propia; y el marco firmado era «resolver como fabricantes», no «descartar».
**Impacto:** sin reconciliar esto, cualquier decisión de hoy deja dos arquitecturas vivas en `main` y una firma de 24 h sin sujeto.
**Qué hay que decidir/definir:** ¿la firma del 10-09 sigue en vigor mientras se discute C, o queda suspendida; y se desbloquea la compra de la Discovery o la pregunta se contesta sin medir?

### 14. [MEDIUM] [AMB · ASSUMP] «Lo único que separa los dos montajes» no resiste el volcado
**Evidencia:** spec D1: *«Eso es lo único que separa los dos montajes»* (el CS por GPIO). Volcado de #5607: `SSM 1`, `SSOE 1`, `SSIOP 1`, `AFCNTR 1`, `MBR 0x7`, `FTHLV 0x0`, `CRCSIZE 0x7`.
**Problema:** los montajes difieren en más de un bit: polaridad/salida de NSS, control de AF, umbral de FIFO y, sobre todo, la razón de relojes (divisor /256 a 100 kHz contra 10-34,5 MHz nuestros), que es exactamente la variable que nombra la errata 2.14.2.
**Impacto:** el bring-up piensa que mueve una variable y mueve cuatro; un «no se cuelga» con NSS por hardware no sería atribuible al NSS.
**Qué hay que decidir/definir:** ¿qué configuración exacta, bit a bit, se declara como «el montaje del hilo» para poder decir qué cambió en el nuestro?

### 15. [MEDIUM] [CONTRA] El artefacto ya se separó de los ocho pasos firmados
**Evidencia:** `software/nucleo/fw/src/j2_spi.rs:62-64`: *«`rcc::enable_and_reset::<T>()`: el reloj y el reset del periferico, que es el paso 0 de los ocho del reinicio de D4»*. D4 lista ocho pasos que empiezan en *«Silenciar la ISR. `EOTIE = 0`»* y ninguno es un reset por RCC. R-MJ3: *«sigue los ocho pasos de D4 en ese orden, y cada paso cita su página»*.
**Problema:** hay un «paso 0» que la spec no tiene. O al reinicio le falta el reset del periférico (y entonces D4 puede no curar, ver hallazgo 9), o la cabecera del driver inventa un paso sin página.
**Impacto:** la única pieza de código de la fase B que existe ya contradice la regla que la gobierna, antes de tener cuerpo.
**Qué hay que decidir/definir:** ¿el reinicio de D4 incluye reset por RCC o no, y cuál es su página del RM0486?

---

## C) Preguntas que el brief evita

1. ¿Cuál es la tasa de cuelgue y de corrupción, medida en nuestro montaje, que descarta el N657? (sostiene 1, 4, 7)
2. ¿Qué dice ES0620 Rev 1 sobre el SPI del N6? (sostiene 2, 6, 8)
3. ¿Quién le debe recuperación a los 3 buses de CV a 48 kHz y al enlace del DAC, si el defecto es del bloque? (sostiene 3)
4. ¿Qué demuestra que el reinicio de D4 cura el cuelgue del N6 — y qué pasa con la ranura que no vuelve? (sostiene 9)
5. Si C se elige: ¿qué chip, con qué censo de 6 SPI corrido y qué tabla eléctrica leída? (sostiene 5)
6. ¿Se desbloquea la compra de la Discovery, o la decisión de hoy se toma declarando que se toma sin medir? (sostiene 1, 4, 10, 13)
7. ¿La firma del 10-09 sigue en vigor mientras C está sobre la mesa? (sostiene 13)

---

## D) Riesgos por categoría

**Técnicos**
- Superficie expuesta mayor que la cubierta: el SPI del CV a velocidad de audio sin plazo ni reinicio → **3**, **9**.
- Diagnóstico inexistente tratado como diagnóstico, con la errata del chip sin leer y la hipótesis sin predicción falsable → **2**, **6**, **8**, **14**.
- El reinicio como supuesto curativo no demostrado; sin estado terminal → **9**, **15**.

**Producto**
- La decisión de plataforma no tiene criterio de aceptación escrito: cualquier veredicto de hoy es preferencia → **1**, **7**, **13**.
- Corrupción con `EVENTO` sin red, cuantificada como función sin cifra y no medida por el soak tal como está redactado → **1**, **4**.
- C y D cambian el perfil de riesgo por otro no censado (2 SPI contra 6; USART sin verificar ni recuperación) → **5**, **12**.

**Ejecución / Operaciones**
- El soak de 24 h puede dar un falso verde con precedente documentado en el propio hilo → **4**.
- El presupuesto no puede cerrar nunca; la fila del CSV no se lee → **7**.
- A contradice el estado del plan (#250, tarea 7 bloqueada) e invoca una puerta que ningún papel firmó → **11**.
- El dato decisivo cuesta $0 (ES0620) y el instrumento de medida cuesta $223,67, aplazado; C cuesta un respin y 70 archivos → **2**, **5**, **13**.

---

## E) Requieren aclaración inmediata (solo BLOCKERS, por severidad)

1. **La cota de tasa aceptable** (cuelgues/hora y corrupciones/hora) no existe en ningún papel. Sin ella no se puede decidir ni hoy ni con placa. *(Hallazgo 1)*
2. **ES0620 Rev 1 sin leer y sin indexar**, con el riesgo «errata joven» cerrado por un criterio que mide arranque. *(Hallazgo 2)*
3. **Alcance de la recuperación**: 6 ranuras cubiertas; 3 buses de CV a 48 kHz y el enlace del DAC sin plazo, reinicio ni cuenta. *(Hallazgo 3)*
4. **El soak de ≥ 24 h** sin potencia estadística, sin criterio de aprobado y sin medir corrupción. *(Hallazgo 4)*
5. **La opción C no nombra chip**; el único destino declarado (RA8M1) tiene 2 SPI contra 6 y su timing de esclavo sin leer, y arrastra D8/C5 por la premisa «dos extremos de la misma clase». *(Hallazgo 5)*

---

**Cierre:** la opción **C** carga la incertidumbre más peligrosa hoy — es la única irreversible y la única cuyo destino declarado reprueba un censo que el N657 ya pasó (2 SPI contra 6, tabla eléctrica sin leer), así que cambia un defecto con tasa desconocida por una plataforma con requisitos conocidos incumplidos; el dato único que más reduce la incertidumbre del tablero completo es la **sección SPI de ES0620 Rev 1**, que cuesta cero y decide si la premisa sobre la que C se apoya («defecto de silicio no documentado») es cierta o si es una limitación documentada con solución documentada.

**Rutas leídas:** brief `junta-2026-09-11-brief.md`, `5607-body.md`, `5607-comments.md`, `es0396-h7-spi-2.14.2.md`; `docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md`; `docs\superpowers\plans\2026-09-04-maestro-j2-recuperacion.md`; `docs\superpowers\specs\2026-08-30-hub-n657-y-radios-design.md`; `docs\superpowers\specs\2026-08-26-motor-digital-design.md`; `docs\superpowers\specs\2026-08-26-motor-digital-benchmark.md`; `docs\references.md`; `hardware\02-midi-cv\recuperacion_j2_budget.py`; `software\nucleo\core\src\maestro_j2.rs`; `software\nucleo\fw\src\j2_spi.rs`, `software\nucleo\fw\EN-PLACA.md`, `software\nucleo\fw\resistencia_j2.csv` (una línea: solo cabecera).
