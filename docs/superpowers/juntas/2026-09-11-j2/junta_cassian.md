## Cassian — qué se hace esta semana, junta del 2026-09-11

Leí el brief, la errata del H7, §9 de la spec firmada, la fase B del plan y la sección de la Discovery de `EN-PLACA.md`. Antes de la triage, dos hechos del repo que cambian el tablero de hoy:

- **La fase B ya no está bloqueada.** `software/nucleo/fw/Cargo.toml` apunta a `embassy-stm32` con `stm32n657x0` (fork `n6-usb`), `j2_spi.rs` existe como cabecera y `.githooks/pre-push` lo **enlaza** (`cargo build --release`) en cada push. El plan todavía dice *«no hay dónde ponerlo»*: eso es papel atrasado, no un bloqueo.
- **La puerta de fabricación no está escrita en ningún sitio.** Grepeé las tres specs: el soak de 24 h aparece como *criterio de cierre de un riesgo*, nunca como prohibición de fabricar. Ahí está el agujero real de esta junta, y es gratis taparlo.

---

## 1. El núcleo entregable (una frase)

**El banco que mide, no el diagnóstico:** `j2_spi.rs` con la solución 2 de la errata escrita dentro, los tres binarios de `src/bin/` listos para enchufar, y una puerta firmada que prohíbe fabricar cualquier PCB con N657 hasta que `resistencia_j2.csv` tenga su primera fila.

La pregunta «¿confiamos en el chip?» no se contesta esta semana. Lo que se entrega esta semana es que **no se pueda apostar el instrumento mientras esté sin contestar**.

## 2. Triage

| Bloqueo | Clase | Razón |
|---|---|---|
| **Discovery sin comprar** | **HARD — de FABRICAR, no de escribir** | Es la única puerta de un solo sentido del asunto. Bloquea gerbers de cualquier placa con N657. No bloquea ni una línea de Rust: el código es reversible, el respin no. |
| **Solución 2 de la errata fuera de la spec** | **SOFT — bloquea el PR, no el día** | Si entra después, el driver se reescribe. Enmienda de dos líneas a D2, **hoy, antes del código**. Y ojo al detalle: el retardo cuenta desde `SPE=1` (RM0486 p. 3492: `EOT` se levanta al rehabilitar), no desde `EOTC`. 100 ns al piso de 10 MHz, 29 ns al peldaño 2. Retardo de N nops: cota por construcción, no viola R-MJ2. |
| **ES0620 sin leer** | **SOFT — DELEGATE a Samuel, hoy** | st.com no contesta a curl y no tengo WebFetch. Sin ella, la enmienda entra marcada *«por analogía con ES0396 §2.14.2 del H7 (`spi_v4`); sin confirmar en ES0620»*. Bloquea la firma limpia, no el driver. Coste de resolverlo: un mensaje. |
| **Comparación con el HAL de C sin correr** | **POST-SHIP** | Dirime silicio contra driver, y necesita placa. Seis meses y 28 comentarios no la produjeron; jake-taf se trancó con probe-rs en C. No es trabajo de escritorio. Se pide en #5607 y se programa como experimento 1 del día de la placa. |
| **Driver de la tarea 7 sin escribir** | **NO es bloqueo: es el trabajo** | Y está desbloqueado. Escribirlo hoy es lo que convierte la hipótesis de la errata en algo medible el día 1 de la placa. |
| **Esclavo de la Voz sin recuperación propia** | **POST-SHIP** | ES0396 §2.14.2 es **«Master** data transfer stall»: el esclavo no cae dentro de esa errata, y los dos reportantes de #5607 son maestros. Y el módulo ya tiene red: watchdog de trama (voz-total §9.2) y silencio por hardware sin CPU (R-M5). Un esclavo colgado suena a release, no a nota pegada. Su línea `SPE=0 → SPE=1` es #292, hito 4. |

## 3. Plan hasta el viernes 18-09

**Variante (a) — sin plata para la Discovery.** Hoy es jueves 11-09.

| # | Cuándo | Horas | Qué |
|---|---|---|---|
| 1 | Hoy 11-09 | 0,25 | Pedirle el **ES0620 Rev 1** a Samuel (PDF al Desktop). Es un mensaje, no una tarea. |
| 2 | Hoy 11-09 | 1 | **Enmienda a D2**: solución 2 de la errata, con la cita íntegra y las dos cifras. Aplicada en el cuerpo de §D2 **y** anotada en §10, en el mismo commit. Pide su firma: la spec está firmada, esto no se edita en silencio. |
| 3 | Hoy 11-09 | 0,5 | **Enmienda a §9 riesgo 1**: *ninguna PCB con N657 se fabrica sin una fila en `resistencia_j2.csv`*. Tres líneas más en el HUECO de `recuperacion_j2_budget.py` para que la puerta se imprima sola. Issue nuevo que la guarde. |
| 4 | Hoy 11-09 → vie 12-09 | 5 | **Tarea 7**, cuerpo de `j2_spi.rs`. Host-testeable lo que se puede: los ocho pasos de D4 y el retardo de la errata como secuencia de datos con un test; el transporte no. Un PR. |
| 5 | Lun 15 → mar 16-09 | 6 | **Tarea 8**, ejecutor del J2 y las seis tareas. Un PR. |
| 6 | Mié 17-09 | 2 | Los tres binarios que `EN-PLACA.md` ya especificó: `resistencia_j2`, `plazos_j2`, `eot_al_aire`. Compilan, no corren. El día de la placa es enchufar, no decidir. |
| 7 | Jue 17 → vie 18-09 | 1 | Comentar en **#5607** con lo que aporta un fabricante: la errata 2.14.2 nombrada como hipótesis, el cálculo de que el repro de jake-taf (100 kHz → 10 µs de ciclo) cae **dentro** de su condición en cada transferencia, y que nadie ha probado NSS por hardware. |
| 8 | Vie 18-09 | 0,5 | PRs mergeados, sexta razón añadida a #231 (*el soak es ahora puerta de fabricación*), issues cerrados **a mano** con `gh issue close`. |

**Total: ~16 h de escritorio. Cierre: viernes 18-09.**

**Variante (b) — Discovery comprada hoy ($223,67, DigiKey; mira el precio al pagar, no el del buscador).** Añade 0,35 h hoy (pedido) y **no cambia nada más de esta semana**: la placa llega ~18-09, o sea entra en la puerta el día que esta semana cierra. Lo que (b) cambia es la semana del 21-09: experimento 1 = soak con el **HAL de C de ST** por ST-LINK + CubeProgrammer (fuera del camino de probe-rs, que es donde se trancó jake-taf), un día, y dirime silicio contra driver. Experimento 2 = `resistencia_j2` con el driver propio.

Consecuencia que vale decir en voz alta: **la decisión de comprar no bloquea una sola hora de esta semana.** Por eso no se debate hoy.

## 4. Lo que se corta, sin más debate

| Opción | Corte | Por qué |
|---|---|---|
| **C — cambiar de chip** | **DELETE** | 70 archivos, 43 commits, tres papeles firmados, y el candidato «maduro» obvio trae la **misma** errata documentada y **sin corregir en ninguna revisión de silicio** (A A A en ES0396). Cambiar un defecto sin diagnóstico por uno documentado no es prudencia. Se reabre solo con un dato: si el soak da plazos vencidos de orden segundos en vez de minutos-horas. |
| **D — J2 por USART síncrono** | **DELETE** | El peldaño 2 de 34,5 MHz no lo alcanza un USART, y arrastra cabecera, punto a punto y censo de pines. Te saca de una errata medida a cambio de otras sin medir. |
| **B — Discovery a prioridad 1** | **DEFER a la plata, no a un debate** | Es el mismo trabajo de A esta semana. Lo único que aportaba era el orden de los experimentos del día 1, y este papel ya lo fija. |
| **Más lectura de escritorio** (RM0486 buscando pistas del EOT, releer los 28 comentarios, más hilos del foro) | **DELETE del día** | §3.5 ya dice «no hay». Más lectura hoy no produce un dato; produce otra junta. |
| **Recuperación propia del esclavo de la Voz** | **DEFER a #292, hito 4** | Fuera de la errata de maestro, y con red propia ya firmada. |

## 5. Permiso

> **Permiso de liberación — 2026-09-11.** Samuel: escribe `j2_spi.rs` hoy. No estás apostando el instrumento, porque el instrumento no se apuesta en código: se apuesta cuando sale un gerber con un N657 encima, y eso queda **prohibido por escrito** hasta que `resistencia_j2.csv` tenga su primera fila. El driver es reversible; el respin no. Aceptas, explícitamente: **(1)** la solución 2 de la errata entra por analogía con el H7, sin ES0620 confirmándola; **(2)** al 18-09 «silicio o driver» sigue sin dirimirse, y eso no se compra con horas de escritorio; **(3)** `EVENTO` no tiene red y un golpe perdido por cuelgue sigue siendo posible con la tasa sin medir. Si rechazas, rechaza por escrito y con el motivo — el defecto no puede ser «seguimos puliendo papel».

Si lo honesto fuera parar, el permiso diría lo contrario, y este es el único dato que lo haría decir eso: que el soak diera cuelgues de varios por segundo con NSS por hardware y `TSIZE > 0`. Ese dato no existe hoy, y no va a existir sin placa. Parar ahora no es prudencia: es pagar el precio de la incertidumbre sin comprar la medición.

**Rastro que queda** (rutas absolutas):
- `D:\Desktop\projects\sam17\docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md` — enmiendas a D2 (errata, solución 2) y a §9 riesgo 1 (puerta de fabricación), aplicadas en el cuerpo **y** en el mapa de §10.
- `D:\Desktop\projects\sam17\docs\superpowers\plans\2026-09-04-maestro-j2-recuperacion.md` — una línea: la fase B ya no está bloqueada por #250; el `Cargo.toml` de `fw` lo desmiente.
- `D:\Desktop\projects\sam17\hardware\02-midi-cv\recuperacion_j2_budget.py` — la puerta de fabricación impresa en el HUECO (exit 2 = HUECO en `hardware\tools\gates.py`; esta puerta se declara, no se automatiza: no hay PCB de N657 todavía que vigilar).
- `D:\Desktop\projects\sam17\software\nucleo\fw\src\j2_spi.rs` y `D:\Desktop\projects\sam17\software\nucleo\fw\EN-PLACA.md` — tarea 7 y los tres binarios.
- Issues: #231 (sexta razón), #250 (anotar que el enlace ya pasa), uno nuevo para la puerta de fabricación.

---

**Se ejecuta la opción A. Primer paso mañana viernes 12-09: el cuerpo de `j2_spi.rs`, empezando por los ocho pasos de D4 con el retardo de un ciclo de SCK entre `SPE=1` y `CSTART` ya dentro — con la enmienda a D2 firmada anoche, no después.**

Ship the version that earns the next lesson.
