# Halberg · sexta pasada · el tic de despertador, R-H1 por nivel y el buzón (modelo `69754fe`, papel `f0736c8`) · 2026-10-19

**En llano.**
- **El tic de despertador cierra N8 en el modelo.** Puse dos retenciones legales ancladas en la escalada aplazada:
  - con el planificador como despertador, el chip se reinicia en 108 de 1 191 corridas legales;
  - con el tic, en 0 de 1 071.

  En un fuzz de 4 000 corridas, ninguna de las 2 517 legales reinicia el chip. Dentro del modelo no hay carreras entre el tic, el planificador y la recuperación: dos aplazadas no pueden tener instantes distintos a la vez, y una ranura muerta no gasta escalada.
- **Se rompe en dos sitios que el modelo no ve:**
  - **La vuelta del contador del tic.** El modelo compara el instante sin contar con que el contador de 32 bits vuelve a 0. Con un bloqueo después de la vuelta, mueren las seis ranuras y el chip se reinicia.
  - **La cota de 13,25 ms.** Supone que la recuperación lee el reloj y decide en el mismo instante. El modelo lo da por hecho; `recupera()` de `fw` lee el reloj fuera de cualquier sección crítica. Si una tarea de nivel 2 entra justo ahí, dos retenciones legales reinician el chip, y ningún testigo pasa de 12 ms.
- **Con R-H1 por nivel caben a la vez las cotas 200/112 y sus dos asertos.** Pero el aserto del módulo vale para un solo incidente. Un bloqueo largo con un tren de retenciones legales deja vivas las seis ranuras con 60 a 85 ms sin trama.
- **La propiedad de §2.6 se sostiene en `fw/src/j2_tic.rs`.**

Hallazgos nuevos: 2 MEDIA y 1 BAJA; ningún BLOCKER.

## Qué ejecuté

- **La copia.** `espera@69754fe` con `git archive`, sin `target`, en una copia de trabajo. Comparada con el worktree, sin diferencias.
- **La instrumentación de la copia.** El diff está en `sim/junta6/motor_instrumentado.diff` (83 líneas). Añade:
  - los testigos de P3 y P4 de pendiente a terminado, contando también la ventana que acaba en aplazada y la que acaba en ranura muerta;
  - un paso opcional que separa la lectura del reloj de la decisión del presupuesto;
  - el presupuesto opcional con el reloj de 64 bits de `fw`;
  - un contador de `HECHA` sin trama en el buzón.

  Con los valores por defecto el comportamiento no cambia: `espera.rs` da 7 de 7 sobre la copia.
- **Los experimentos.** Son x17 a x21 y x18b, en `sim/junta6/halberg6.rs`. Se corren sobre la copia instrumentada con `cargo test -p sam17-nucleo-modelo --release --test halberg6 -- --ignored --nocapture x17`, cambiando el nombre de la prueba.
- **Qué llamo «legal».** Lo mido en la propia corrida: P3 y P4, de pendiente a terminado, ≤ 12 ms.
- **`fw`.** Leí `fw/src/j2_tic.rs`: el tic, `DMA2D`, `JPEG`, `recupera()` y `compone()`. No compilé firmware.
- **No modifiqué ningún archivo de ningún worktree.** `espera` y `junta4` siguen limpios.

## Las tres preguntas

**1. ¿El tic de despertador hace lo que dice?** Sí en el modelo, salvo en la vuelta del contador (N11). En `fw` hay además una carrera que el modelo no puede representar (N12).
- **Una aplazada que muere.** `RecScan` la recoge al despertar y `RecStart` la salta (`motor.rs:1157`): no gasta escalada (H5).
- **Otra escalada mientras tanto.** Antes del instante no puede haberla: el presupuesto aplaza la petición con el mismo instante. Al despertar, la primera ranura escala; las demás encuentran `IDLEF` y se recuperan sin escalar.
- **Una aplazada cuyo instante el tic ya pasó.** En el modelo es imposible: `hasta > ahora`, y leer el reloj, decidir y publicar son el mismo paso. En `fw` sí puede pasar (N12).
- **Varias aplazadas con instantes distintos.** No pueden coexistir.
  - Un instante nuevo exige una concesión nueva.
  - Esa concesión exige que el contador haya llegado al instante pendiente.
  - Para entonces el tic ya lo despertó y lo borró.

  Por eso el `min` y el borrado entero de `rec_despierta_us` (`motor.rs:984-988`, `:1219-1220`) son seguros. Si el tic despierta con P4 corriendo, `pend_rec` vuelve a lanzarla al terminar.
- **La vuelta del contador de 32 bits.** No: N11.

**2. Con R-H1 por nivel, ¿caben a la vez las cotas, los asertos y los 49 ms?** Sí por incidente, con la condición de N12. No a lo largo de una cadena de incidentes (N13).
- **La aritmética, por nivel:**
  - `Vencida`: 2 × 12 = 24 < 25,125 ms.
  - `Reiniciando`: 1 + 12 + 0,25 = 13,25 < 14,125 ms. El «1» se cumple porque la concesión que aplaza ocurre antes del `RecStart` de la ranura (P4 trabaja en serie), así que la espera dentro de `Reiniciando` es menor de 1 ms.
  - El módulo: 39,75 < 49 ms.
- **x19, fuzz.** 4 000 corridas: bloqueo de 0,3 a 5,5 ms, de 1 a 3 retenciones de 1 a 11,95 ms y, la mitad de las veces, un SPI envenenado.
  - Legales: 2 517, ningún reinicio del chip.
  - Ilegales: 1 483, de las que 219 reinician.
  - Mayor hueco sin tramas entre las legales que sobreviven: 23,75 ms.
- **x21, barrido anclado en la aplazada.** Con el tic, 0 de 1 071 legales reinician; con el planificador, 108 de 1 191.
- **La retención legal que reinicia** solo aparece con el reloj leído antes de decidir: N12, con sus cifras.

**3. ¿La propiedad de §2.6 se sostiene en `fw/src/j2_tic.rs`?** Sí, por construcción:
- **Un solo peticionario, que compone antes de soltar la CPU.** `DMA2D` pide la recuperación (L1104-1118) y, en la misma vuelta del bucle, llama a `compone(n, p)` (L1128).
- **La recuperación no puede adelantarse.** `JPEG` está en `PRIO_REC = P4`, por debajo de `PRIO_PLAN = P3` (L66-67). Cuando `recupera(n)` arranca, la trama ya está publicada.
- **Nadie la consume mientras tanto.** El tic solo consume con `s.armar` (L951-952), y en `Vencida` y `Reiniciando` eso pide `reinicio_hecho`. `recupera()` y `escala()` no tocan `BUZON`.
- **Con el despertador del tic** (aún no está en `fw`), la trama compuesta en la pasada que pidió el primer intento sigue en el buzón.
- **En el modelo:** de 83 672 recuperaciones del fuzz, ninguna termina sin trama fresca.
- **Lo que se sostiene es la presencia, no la frescura.** La trama que sale tras `HECHA` es la compuesta en la pasada que pidió la recuperación: `compone()` no la sustituye mientras siga fresca (L1033).
- **La propiedad depende de que R-H1 mantenga P4 por debajo de P3.**

---

## Execution Breakpoints Detected

### N11 · MEDIA · B: el instante de 32 bits se compara sin contar la vuelta, y en la vuelta mueren las seis ranuras

**Evidencia en el papel.** Ficha B, costo (4): «el tic compara un instante de 32 bits en cada entrada»; lo mismo en §2.1 y en §0.6, punto 34. No dice cómo se compara cuando el contador vuelve a 0: 2^32 × 125 µs = 6,2 días.

**Evidencia en el modelo.** Las tres comparaciones usan el contador crudo `u64::from(self.tics) * 125`, que vuelve a 0, con `>=`:
- el tic (`motor.rs:983-984`);
- `RecScan` (`:1140-1142`);
- el presupuesto (`:1203`), que además resta con `saturating_sub` (`escaladas_j2.rs:64`).

**x17.** Dos bloqueos de 1 ms, a los 20 y a los 150 ms; el contador da la vuelta a los ~100 ms.

| caso | escaladas | ranuras muertas | reinicio del chip |
|---|---|---|---|
| sin vuelta | 2 | ninguna | no |
| con vuelta, el modelo tal cual | 1 | las seis | a los 260 ms |
| con vuelta, el presupuesto con el reloj de 64 bits de `fw` | 2 | las seis | a los 265 ms |
| un solo bloqueo que empieza 0,3 ms antes de la vuelta | 1 | las seis | a los 210 ms (sin vuelta, ninguno) |

- **El modelo tal cual.** Tras la vuelta, `saturating_sub` da 0, y toda escalada pedida se aplaza hasta `hasta_us` = 536 870 833 125 µs, un instante que el contador no alcanza en 6,2 días. Despertares del tic tras los 150 ms: 0.
- **Con el reloj de `fw` (`RELOJ_REC`).** La primera escalada se concede, pero las aplazadas llevan un instante de 64 bits (536 870 963 125 µs) que el tic compara contra el contador crudo. Tampoco despierta ninguna.

**Qué rompe.** Pasados 6,2 días encendido, las ranuras aplazadas se quedan en `Reiniciando` sin despertador, mueren por la cota y el supervisor reinicia el chip. Con el modelo pasa en la primera escalada tras la vuelta, si hubo alguna antes. Con el reloj de `fw`, en la primera aplazada tras la vuelta. Las corridas de la junta duran menos de un segundo y no lo ven. El modelo es la única implementación del dato nuevo y la fuente de las cifras (S) de B.

## Concurrency Failure Risks

### N12 · MEDIA · B × C: la cota de 13,25 ms supone que la recuperación lee el reloj y decide en el mismo instante

**Evidencia.**
- **El papel.** La ficha C da «1 + 12 + 0,25 = 13,25 < 14,125». El «1» supone algo que no está escrito: que el instante con que P4 decide aplazar es el mismo en que publica.
- **El modelo.** `RecDecide` es un solo paso: lee el contador, pregunta al presupuesto y publica `rec_despierta_us` (`motor.rs:1199-1222`). Si P2 lo retiene, lee el reloj después; para entonces la espera ya pasó y la escalada se concede.
- **`fw`.** `recupera()` lee `TICS` (L1239), lo extiende y después llama a `pide()` (L1241), fuera de cualquier sección crítica. Con la espera, P2 puede entrar entre la lectura y la publicación del instante.

**x18b, la traza.** Variante de la copia: un paso lee el reloj y otro decide, y P2 entra entre los dos. Bloqueo de 1 ms, ranura 0, tiempos desde el bloqueo:
- +0,374 ms: arranca la recuperación del segundo cuelgue.
- +0,399 ms: lee el reloj y entra P2 (L1 = 11,5 ms).
- +12,135 ms: decide con el reloj viejo y aplaza hasta +1,115 ms, un instante que pasó hace 11 ms.
- +12,240 ms: el tic la despierta.
- +12,253 ms: arranca otra vez y entra P2 (L2 = 3 ms).
- +14,616 ms: `Muerta`, por la cota de `Reiniciando`.
- +15,351 ms: `HECHA`, tarde.
- +115 ms: el IWDG reinicia el chip.

Las ventanas, todas legales:
- P3, 11,64 ms;
- P4 hasta la aplazada, 11,79 ms;
- P4 despertada, unos 3,1 ms.

Ningún testigo pasa de 12 ms.

**x18, el barrido** (L1 de 2,5, 6,5 y 11,5 ms × L2 de 0, 2, 3, 6 y 11 ms; las 30 corridas son legales):
- con el reloj leído al decidir (el modelo), 0 de 15 reinician;
- con el reloj leído antes, 4 de 15: L1 6,5 con L2 11, y L1 11,5 con L2 3, 6 y 11.

El umbral está en L1 + L2 por encima de unos 14 ms.

**Qué rompe.** Es N8 otra vez, ahora dentro de P4: dos trabajos en serie, cada uno con su ventana de R-H1, y el testigo no lo ve.
- En el orden actual de `recupera()`, la ventana mide unas decenas de instrucciones: es improbable, pero no imposible.
- Se ensancha a toda la pasada de P4 si `fw` lee el reloj una vez al entrar. Eso es lo natural ahora que P4 tiene que mirar qué aplazadas se cumplieron.
- El papel no lo exige, y el modelo no lo puede representar.

## Runtime Contradictions Across Layers

### N13 · BAJA · C: el aserto del módulo vale por incidente; una cadena de incidentes dentro de un mismo bloqueo pasa de 49 ms sin reiniciar el chip

**Evidencia en el papel.**
- Ficha C (2): «el mayor hueco entre tramas de una ranura que sobrevive … 39,75 ms».
- Ficha B: «aguanta bloqueos de hasta 6 ms (E × espera) y reinicia el chip con 6,25».

**El mecanismo.** Un bloqueo encadena incidentes. Sin retenciones, cada incidente dura una espera y seis escaladas cubren unos 6 ms. Con R-H1 por nivel, cada incidente puede durar una ventana de 12 ms, y seis escaladas cubren unos 80 ms.

**x20.** Bloqueo de D ms y un tren de P2: 11,4 ms de CPU cada 12,1 ms, ocho veces. Medido en la corrida: P3 11,73 ms y P4 11,28 ms, legal por nivel.

| D | sin tren | con tren |
|---|---|---|
| 6 ms | 6 escaladas, vive, hueco 6,37 ms | vive, hueco 11,87 ms |
| 30 ms | reinicio del chip | 2 escaladas, vive, hueco 36,12 ms |
| 60 ms | reinicio del chip | 4 escaladas, vive, **hueco 60,25 ms** |
| 80 ms | reinicio del chip | 6 escaladas, vive, **hueco 84,50 ms** |

**Qué rompe.**
- **Las ranuras viven, los módulos no reciben nada.** Las seis sobreviven y sus seis módulos pasan 60 a 85 ms sin trama. El watchdog de trama suelta las notas con el aserto en verde. El supervisor sigue alimentado, porque el sello se renueva en cada rearme.
- **La frase de B tampoco se cumple.** «Reinicia con 6,25» deja de ser cierta.
- **Hace falta un hub extremo.** El hub tiene que tener P2 al 94 % durante unos 100 ms. R-H1 por nivel lo permite; el censo (R-H6) debería impedirlo.
- **Lo que falla es la frase, no el instrumento.** El resultado es más suave que el reinicio que habría sin retenciones; lo que no se cumple es la frase del aserto.

## Context Integrity Violations

No hay hallazgo nuevo. La propiedad de §2.6 se sostiene en `fw`: la trama está presente al terminar la recuperación, aunque no es fresca (pregunta 3).

## Orchestration Failure Modes

No hay hallazgo aparte de N11 y N12. En los dos, el chip se reinicia sin que ningún testigo de R-H1 pase de 12 ms.

## Universality Collapse Points

No hay hallazgo nuevo.

---

## Comprobado y bien

- **N8 queda cerrado en el modelo.** x21: 0 de 1 071 con el tic, 108 de 1 191 con el planificador. `con_el_tic_de_despertador_el_testigo_de_la_recuperacion_ve_la_retencion_que_mata` pasa.
- **La aplazada que muere no gasta escalada**, y el despertar con P4 en marcha no se pierde.
- **Dos aplazadas no pueden tener instantes distintos a la vez**, así que el `min` y el borrado entero de `rec_despierta_us` son seguros.
- **R-H1 por nivel sostiene 200/112 y los dos asertos en cada incidente.** Ninguna de las 3 588 corridas legales de x19 y x21 reinicia el chip.
- **La propiedad de §2.6** se sostiene en `fw` por el orden de `DMA2D` y las prioridades, y en el modelo con 83 672 recuperaciones.

## Execution Feasibility Verdict

- **B: no se puede firmar tal como está escrita.** El tic de despertador cierra N8, sin carreras con el planificador ni con la recuperación dentro del modelo. Faltan dos condiciones por escrito: cómo compara el tic el instante cuando el contador da la vuelta (N11), y que P4 lea el reloj, decida y publique como un solo instante para P2 (N12).
- **C: se puede firmar.** 200/112 y los dos asertos se sostienen por nivel, y §2.6 se sostiene en `fw`. Su cota de 13,25 ms depende de la condición de N12, que va en B, y el aserto del módulo vale por incidente, no por bloqueo (N13).

Dos trabajos en serie siguen siendo dos ventanas, aunque los dos sean de la recuperación. **La ejecución ha hablado.**
