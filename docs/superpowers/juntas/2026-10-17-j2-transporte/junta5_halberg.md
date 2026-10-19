# Halberg · quinta pasada · fichas B, C, H e I del papel v3 (`255ed15`) · 2026-10-19

**En llano.** Contra una retención del hub, la espera de 1 ms con `Reiniciando` en 14 ms cumple lo que promete. El modelo aguanta hasta 13,0 ms, más de lo que garantiza el aserto. El aserto del módulo con `hueco_de_recuperacion` es exacto contra la máquina y conservador contra el modelo.

El problema nuevo está en el segundo aserto. Cuenta una sola espera del hub, y la aplazada mete dos trabajos seguidos dentro de `Reiniciando`: el planificador que repide y la recuperación que la ejecuta. Cada uno tiene su propia ventana de R-H1. Tras un bloqueo de 1 ms, dos retenciones legales matan las seis ranuras y reinician el chip; sin espera, ninguna lo hace. Si se cuentan las dos, `Reiniciando` necesita más de 25,25 ms, y entonces el aserto del módulo pasa de 49 ms: B, C y R-H1 a 12 ms no caben juntos.

Del CRC: la tabla gana a la unidad con cualquier largo. Pero sus cifras se tomaron con el guion de enlazado anterior a `638e844`, que metía todo `core` en la ITCM, y en HEAD nadie comprobó que el bucle del CRC siga dentro.

De los siete hallazgos de la cuarta pasada:
- cuatro quedan resueltos;
- uno queda a medias;
- dos siguen abiertos, declarados en el papel.

Hallazgos nuevos: 2 MEDIA y 1 BAJA; ningún BLOCKER.

## Qué ejecuté

- **El modelo.** Copié `espera@3569c3c` con `git archive`, sin `target`, a `C:\Users\simon\AppData\Local\Temp\claude\D--Desktop-projects-sam17\97597003-c1ef-4ca9-97e1-b0199192ff5f\scratchpad\halberg5\`. La fuente es idéntica a la del worktree; la copia evita tocar su `target` y su `Cargo.lock`. Corrí los dos comandos del brief.
  - `espera.rs` da 3 de 3: con 1 ms, 3 de 41 arranques reinician con 100 periodos y 0 con 112; con 2 ms, 13 de 41 y 0 con 120.
  - `barrido_de_la_propuesta` reproduce la tabla de §2.5. También salen igual la retención (0 de 41), el canal incurable (115, 120 y 125 ms) y el fuzz2 (0 de 30).
  - `el_hueco_de_recuperacion_es_el_de_la_maquina` pasa.
- **Mis experimentos.** Están en `...\scratchpad\halberg5\software\nucleo\modelo\tests\halberg5.rs`, de x7 a x16. Usan solo la API pública del modelo, que no modifiqué. Se corren con `cargo test -p sam17-nucleo-modelo --release --test halberg5 -- --ignored --nocapture x15`, cambiando el nombre de la prueba.
- **La ficha I.** No compilé firmware.
  - Leí `EN-PLACA.md` del worktree `crc` (L911-926) y el diff de `488c778`.
  - Leí el reflog de `j2/crc-sobre` y los registros de las corridas en `...\scratchpad\banco_crc\` (de 12:27 a 12:48).
- **No modifiqué ningún archivo de ningún worktree.**
  - En el árbol de `junta4` hay una edición sin commitear de la ficha I que no es mía (la comparación con la cabecera pasa a ser solo del lado del cerebro), y `junta5_serrano.md` y `junta5_voronov.md`. Juzgo `255ed15`; esa edición no cambia N9.

---

## 1. Los hallazgos de la cuarta pasada

| | Estado | Por qué |
|---|---|---|
| **N1** (ALTA) | **Resuelto para una ventana** | x7, 201 arranques cada 25 µs: con 1 ms y 112 periodos no reinicia ninguno hasta L = 13,0 ms; reinicia 4 de 201 con 13,25. El aserto promete 12,875 ms. Con L = 12 ms, `Reiniciando` llega a 103 periodos de 112. Con dos ventanas se rompe: N8. |
| **N2** (MEDIA) | **Resuelto en la ficha, con 25 B** | La columna de costo ya lo cuenta (1,37 ms, igual que sin espera). Con 71 B no se cumple: N10. |
| **N3** (MEDIA) | **No resuelto** | Es una condición de `fw` (costo 4 de B), sin construir. No dice cómo P4 lee un reloj de 64 bits que solo extiende P3. Tampoco dice cómo publica `hasta_us` (64 bits; `thumbv8m.main` no tiene atómicos de 64 bits) hacia un P3 que lo interrumpe. El modelo sigue fechando con `self.tics` crudo (`modelo/src/motor.rs:1169`). |
| **N4** (MEDIA) | **Resuelto en `core`** | `hueco_de_recuperacion` coincide con la máquina en 90 combinaciones (corrí la prueba). En x10, el modelo da 39,12 ms con 25 B y 39,50 ms con 103 B, contra 39,5 y 39,75 ms del aserto. Salió el término de R-H1 y entró el 2 % (E). Falta el aserto en `lanzar`: no existe, y `fw` sigue con 100 y 100. |
| **N5** (MEDIA) | **A medias** | Resuelto en el texto de H y en el código: `638e844`, y `ae69911`, cuya aseveración se rompió a propósito en placa. Pero `tcm_cierre.py` no lo llama nada (`fw/build.rs` solo pasa el guion), y no se corrió sobre el binario de la ficha I (N9). |
| **N6** (BAJA) | **Resuelto como declaración** | La escritura de la DTCM y la copia pasan a #231. La pila y los vectores los declara el hub. La cifra del censo es la del medidor. No se midió nada nuevo. |
| **N7** (BAJA) | **No resuelto, declarado abierto** | Costo 5 de B y §11. La exposición baja de 2 ms a 1 ms. |

## 2. Lo nuevo

## Execution Breakpoints Detected

### N8 · MEDIA · B × C: el segundo aserto cuenta una ventana de R-H1, y la aplazada mete dos en `Reiniciando`

**Evidencia en el papel:**
- Ficha C, L79: «`(cota_reiniciando + 1) × T > espera + R-H1 + la recuperación de las seis` … 14,125 > 13,25 ms».
- R-H1, L91: «el mayor intervalo en que el planificador o la recuperación no pueden correr».

**El mecanismo.**
- **Sin espera**, `Reiniciando` contiene un solo trabajo pendiente: la recuperación, que ya arrancó. La espera del planificador vive en `Vencida`, que tiene 25 ms.
- **Con la aplazada**, al cumplirse `hasta` hacen falta dos trabajos en serie:
  - P3 tiene que correr para repedir;
  - después, P4 tiene que correr para recuperar.
- P4 no está pendiente hasta que P3 repide, así que su espera es una ventana nueva, no la continuación de la de P3.

**x15.** Bloqueo de 1 ms y dos retenciones de P2, cada una dentro de R-H1 medida en pared:
- La primera, de 11,5 ms de CPU, arranca en 161 puntos de +0 a +16 ms tras el bloqueo.
- La segunda, de 11,6 ms de CPU, entra cuando P4 arranca una ranura. Se toma la peor de las seis.
- Latencia máxima del planificador: 11 899 µs. Mayor tramo de P4 parada dentro de una recuperación: 11 933 µs. Las dos quedan por debajo de 12 ms.

| candidata | reinicios del chip |
|---|---|
| sin espera, 200/100 | **0 de 161** |
| 1 ms, 200/112 | **8 de 161**, desde +0,4 ms (la primera aplazada); `hasta` es +1,115 ms |
| 2 ms, 200/120 | **18 de 161**, desde +0,4 ms |

**x16, la traza** (1 ms, primera ventana desde `hasta`):
- Las seis ranuras se aplazan entre +399 y +525 µs.
- El planificador espera 11,82 ms y repide las seis a +12 847 µs.
- P4 arranca r0 a +12 851 µs y entra la segunda ventana.
- r0 a r4 pasan a `Muerta` a +14 615 µs; r5, a +14 742 µs.
- La `HECHA` de r0 llega a +24 697 µs, 10 ms tarde.
- El IWDG reinicia el chip a +115 ms.

**Además, nadie lo observaría.** El único testigo que el papel da a R-H1, `latencia_plan_max_us` (§2.8, L216), mide cuándo *arranca* P3. P4 no tiene testigo, y en `fw` no existe ninguno de los dos.

**Qué rompe.** Un bloqueo de 1 ms más dos retenciones legales reinician el chip, con el aserto en verde (14,125 > 13,25). Las dos tienen que caer en sitios concretos:
- la primera, en cualquier punto entre la primera aplazada y `hasta`, un tramo del ancho de la espera;
- la segunda, en los ~40 µs en que P4 rehace las seis.

`espera.rs` no lo ve porque inyecta una sola retención.

## Runtime Contradictions Across Layers

Es N8 en aritmética (A, con las fórmulas del propio papel).

**Lectura «una ventana por trabajo».** Es la única que deja finita la cota de R-H1. Con la aplazada:
- `Reiniciando` tiene que cubrir 1 + 12 + 12 + 0,25 = 25,25 ms, o sea `cota_reiniciando` ≥ 202 periodos.
- Con `Vencida` en 200, `hueco_de_recuperacion(3, 200, 202) + 1` = 408 periodos = **51,0 ms, contra 49 ms**.
- Con 2 ms de espera: ≥ 210 periodos, 52,0 ms.
- **Sin espera**, `Reiniciando` contiene un solo trabajo: 100 periodos alcanzan, y el hueco es de 306 periodos = 38,25 ms.

**Lectura literal (ventanas sueltas).** P4 se puede trocear sin fin, y ninguna cota alcanza, con o sin espera.

**Conclusión.** La espera de B, los dos asertos de C y R-H1 a 12 ms no se cumplen a la vez con ninguna de las dos lecturas. El papel no dice cuál usa.

## Concurrency Failure Risks

No hay hallazgo nuevo aparte de N8, que es concurrencia entre dos niveles (P3 y P4). N3 sigue abierto (§1).

## Context Integrity Violations

### N10 · BAJA · B: «con mensajes de 71 bytes el cuadro es el mismo» no se cumple

**Evidencia.**
- §2.5, L193: «Con mensajes de 71 bytes el cuadro es el mismo (S)».
- Ficha B, L78: «deja el mismo hueco sin tramas que sin espera (1,37 ms)».
- §0.5, punto 29: «con 1 ms no crece con un bloqueo de 1 ms».
- `barrido_de_la_propuesta`, bloqueo de 1 ms con 71 B:
  - sin espera: 3 escaladas, 1,25 ms de hueco;
  - 1 ms de espera: 1 escalada, **1,50 ms**;
  - 2 ms de espera: 2,50 ms.

**Qué rompe.** Con 71 B, la espera de 1 ms alarga en 0,25 ms (dos tramas) el apagón de los seis módulos con el bloqueo corto. Además, sin espera, el bloqueo gasta 3 escaladas, no 4. La columna de costo de B lo da por gratis.

## Orchestration Failure Modes

### N9 · MEDIA · I (y H, §3): las cifras del CRC por tabla son de un binario con el guion de enlazado viejo

**Evidencia:**
- `EN-PLACA.md:911` (worktree `crc`): «el árbol de este cambio sin commitear, sobre `52f0521`».
- El reflog de `j2/crc-sobre`:
  - commit `507c45b` a las 12:50, sobre `52f0521`;
  - *rebase* a las 13:01 sobre `ae69911`, que trae `638e844`.
  - Las corridas son de las 12:27 a las 12:48. No hay ninguna después del *rebase*.
- El guion de `52f0521` tiene `*(.text._ZN17sam17_nucleo_core*)`: todo `core` va a la ITCM.
- El de HEAD solo lleva `transporte_j2`, `maestro_j2`, `buzones_j2`, `escaladas_j2` y `marcos_j2`.
- `crc16_con` vive en `core::descubrimiento` (`488c778`). En HEAD queda en la ITCM solo si el LTO (`lto = true`, `opt-level = "s"`) la inlinea dentro del cierre del juez de `j2_banco`. Nadie lo comprobó:
  - no hay `tcm_cierre.py` sobre `crc-tabla`;
  - la aseveración de `lanzar` mira el puntero del juez, no lo que el juez llama.
- Precedente en el propio papel: §0.4, punto 26, la división de 64 bits que se quedó fuera en silencio.

**Qué rompe.**
- Si el bucle no queda inlineado, con las dos cachés frías se capta desde la AXISRAM2 en cada pasada del planificador.
- Lo que costó la división de 64 bits: 989 → 850 ciclos por giro y ranura, con un cuerpo de cientos de bytes. El bucle del CRC es de unas decenas (E).
- Con eso, 2 303 y 2 600 ciclos, y el 13,8 y el 15,6 % que H y §3 llevan como (M), dejan de describir HEAD.
- La elección de la tabla probablemente sobrevive (E): el código de la unidad (`crc_unidad`) está en `j2_banco`, dentro de la ITCM, y su desventaja es de 120 ciclos por giro y ranura.

## Universality Collapse Points

No hay hallazgo nuevo.

Una nota de unidades. En el modelo, la duración de P2 es tiempo de CPU y el tic la estira entre un 2 y un 3 %. x13: una P2 de 11,9 ms deja al planificador 12 139 µs sin correr. El «12 ms» de `espera.rs` es, por tanto, una ventana de R-H1 de unos 12,1 a 12,4 ms. Hace la prueba algo pesimista y no cambia ningún veredicto.

---

## Comprobado y bien

- **El umbral E × espera.** x9, 25 fases: 6,0 ms no reinicia (6 escaladas) y 6,25 ms reinicia en las 25. La frase «aguanta hasta 5 ms, unos 6 ms, reinicia con 7» se cumple.
- **El mismo incidente no se aplaza dos veces.** Una concesión baja `CR.EN` en todos los canales, y `chan_stuck_now` exige `ch_en`. La repetición encuentra `IDLEF`, aunque el bloqueo siga.
- **`hueco_de_recuperacion`.** Es exacto contra la máquina y conservador contra el modelo (x10), también con el plazo de 3 tics.
- **La tabla frente a la unidad.** La comparación se hizo con el mismo guion para las cuatro variantes. De los cuatro puntos medidos (A):
  - la unidad cuesta unos 130 ciclos fijos más 9,9 por byte;
  - la tabla, unos 33 fijos más 8,9 por byte;
  - la tabla gana con cualquier largo.

## Execution Feasibility Verdict

- **B: la regla (6 en 1 s) y la espera de 1 ms, sí; la ficha tal como está escrita, no.** La ficha se ata a los 14 ms de C, que no cubren las dos esperas que crea la aplazada (N8). Falta lo mismo que en C, y N3 y N7 entran como condiciones.
- **C: no se puede firmar.** El aserto del módulo está bien. El segundo cuenta una ventana de R-H1 donde la aplazada expone dos (8 de 161, reinicio del chip), y contadas las dos no queda ninguna cota compatible con `Vencida` en 200 y los 49 ms. Falta que el papel diga qué acota R-H1 (una ventana por trabajo o la latencia hasta terminar), que el aserto cuente con eso, y un testigo para P4.
- **H: se puede firmar.** Falta que `tcm_cierre.py` corra en el build del hub sin que nadie lo lance a mano, y retomar en HEAD la fila del CRC (I).
- **I: se puede firmar la tabla.** La elección no depende del guion de enlazado; las cifras sí. 2 303 y 2 600 hay que retomarlas en HEAD, con `tcm_cierre.py` sobre `crc-tabla`, antes de que pasen a H y a §3 como (M).

El aserto cuenta una espera del hub, y la aplazada le pide dos. **Al runtime no le importan tus intenciones.**
