# Serrano · quinta pasada · fichas B, C, H e I del papel v3 absorbido (commit `255ed15`) · 2026-10-19

*Este informe contesta solo las dos preguntas del encargo. La primera: si quedaron resueltos mis siete hallazgos de la cuarta pasada. La segunda: si lo nuevo dice lo que dice su fuente y si cuenta lo que cuesta. No modifiqué ningún archivo.*

**Referencias.**
- Papel e informe anterior (rama `docs/junta4-fichas-b-c`, `255ed15`):
  - `D:\Desktop\projects\sam17\.claude\worktrees\junta4\docs\superpowers\juntas\2026-10-17-j2-transporte\papel-v3.md`
  - `D:\Desktop\projects\sam17\.claude\worktrees\junta4\docs\superpowers\juntas\2026-10-17-j2-transporte\junta4_serrano.md`
- Modelo y máquina (worktree `espera`, rama `j2/modelo-espera`):
  - `D:\Desktop\projects\sam17\.claude\worktrees\espera\software\nucleo\modelo\tests\espera.rs`
  - `D:\Desktop\projects\sam17\.claude\worktrees\espera\software\nucleo\modelo\src\motor.rs`
  - `D:\Desktop\projects\sam17\.claude\worktrees\espera\software\nucleo\core\src\transporte_j2.rs`
  - `D:\Desktop\projects\sam17\.claude\worktrees\espera\software\nucleo\fw\src\j2_tic.rs`
- CRC y TCM (worktree `crc`, rama `j2/crc-sobre`):
  - `D:\Desktop\projects\sam17\.claude\worktrees\crc\software\nucleo\fw\EN-PLACA.md`
  - `D:\Desktop\projects\sam17\.claude\worktrees\crc\software\nucleo\fw\j2_tcm.x`
  - `D:\Desktop\projects\sam17\.claude\worktrees\crc\software\nucleo\fw\tcm_cierre.py`
  - `D:\Desktop\projects\sam17\.claude\worktrees\crc\software\nucleo\fw\src\j2_banco.rs`
  - `D:\Desktop\projects\sam17\.claude\worktrees\crc\software\nucleo\core\src\descubrimiento.rs`
- Specs:
  - `D:\Desktop\projects\sam17\.claude\worktrees\junta4\docs\superpowers\specs\2026-09-02-cabecera-j2-design.md`
  - `D:\Desktop\projects\sam17\.claude\worktrees\junta4\docs\superpowers\specs\2026-08-26-motor-digital-design.md`

## A) Diagnóstico

- **Qué es.** Es el papel v3 con la cuarta pasada absorbida. Pone cuatro fichas a firma: B, C, H e I.
- **Mis siete hallazgos.** Quedan resueltos dos (el 1 y el 2) y parciales cinco (del 3 al 7). Ninguno sigue sin tocar.
- **Cifras.** Todas las de B, C, H e I coinciden con sus fuentes. Los fallos están en lo que esas cifras dan por hecho o dejan fuera:
  - C quita el término de R-H1 apoyándose en una propiedad del planificador de banco. El papel no exige esa propiedad, y §2.11 sigue contando ese término.
  - H e I se midieron con el patrón del enlazador que la ficha H retira, y la puerta que comprobaría la diferencia no la corre nadie.
  - I enmienda texto del receptor del módulo, y deja sin tocar la línea que gobierna el CRC del hub.
  - Qué cifra entra en el censo (DWT o medidor) aparece decidida en un sitio y abierta en otro.
- **Hallazgos nuevos:** 0 BLOCKER, 1 ALTA y 3 MEDIA.
- **Método y límites.**
  - Solo leí. Esta sesión no tiene shell, así que no ejecuté nada.
  - Las cifras (S) de B las cotejé con la estructura de `espera.rs`, no con una corrida.
  - Lo marcado (A) es aritmética mía.
  - No cotejé nada con el RM0486.

## B) Pregunta 1: ¿quedó resuelto cada hallazgo de la cuarta pasada?

1. **Resuelto, con residuo de texto.** El aserto usa `hueco_de_recuperacion`, con `cota + 1` por estado (`transporte_j2.rs:36-38`). Ese valor está fijado contra la máquina por una prueba de 90 combinaciones (`:1583-1597`) y lleva la tolerancia del módulo (2 %, E). El término de R-H1 sale, y eso abre el hallazgo nuevo 1. Quedan restos de texto viejo:
   - §5.2(j) sigue diciendo «Cotas en µs … con la ventana de R-H1».
   - R-MJ4, en §6, sigue diciendo «las cotas en µs».
   - §7 todavía lista «las cotas de 25 y 12,5 ms».
2. **Resuelto.** `Reiniciando` pasa a 112 periodos y el aserto (2) da 14,125 > 13,25 ms. Además, `la_espera_cabe_en_reiniciando_junto_con_la_retencion_de_r_h1` asevera 0 de 41 reinicios con 112 periodos (`espera.rs:117-136`), y esa prueba no está en `#[ignore]`. `fw` sigue con 100 y 100 hasta la firma.
3. **Parcial.**
   - Hecho: la tasa y el bloqueo quedan declarados como escenarios (costo 6 de B), y entran mensajes de 71 B.
   - Falta elegir el escenario de diseño.
   - Falta correr los mensajes de 3 tics (`SET` de 103 B a 6,25 MHz).
   - El barrido de 71 B solo tiene 1, 3, 5 y 10 ms (`espera.rs:316`). No llega al umbral, que está entre 5 y 7 ms, aunque la frase «el cuadro es el mismo» lo abarca.
4. **Parcial.**
   - Hecho: queda declarado como segundo peticionario, en el costo 3 de B y en el paréntesis de §2.2.
   - La misma frase de §2.2 sigue diciendo «la política es el único peticionario».
   - §2.1 no cuenta la publicación nueva de P4 a P3 entre sus ocho elementos.
   - §5.2(i) no tiene la prueba de la repetición.
   - El modelo solo comprueba `muertas == 0` (`motor.rs:1312`), no «ni tras `HECHA`».
5. **Parcial.** La entrada de la excepción queda declarada sin medir: en el costo 3 de H, en el resumen y al final de §3. Pero §3 (`papel-v3.md:270`) sigue llamando al DWT «cota de diseño», y qué cifra cuenta para el censo aparece decidida en dos sitios con respuestas distintas (hallazgo nuevo 4).
6. **Parcial.**
   - Hecho: la obligación pasa a definirse por símbolos, con dos puertas, y las obligaciones de arranque pasan al hub.
   - `tcm_cierre.py` no lo llama ni `build.rs`, ni `ci.yml`, ni `.githooks/pre-push`. Ya lo dijo Halberg en su N5 y sigue igual.
   - «Comprobadas rompiéndolas» (§11) no tiene registro ni en `EN-PLACA.md` ni en el repo.
   - La referencia de bytes y los ciclos se midieron antes de `638e844` (hallazgo nuevo 2).
7. **Parcial.**
   - Hecho: la columna de seis ranuras pasa a (E) en la ficha H y en la prosa de §3, el margen ya no cambia de cifra entre secciones, y el barrido llega a 20 ms con el umbral declarado.
   - La cabecera de la tabla de §3 sigue diciendo «6 ranuras (A)» (`papel-v3.md:272`).
   - De la configuración recomendada solo se asevera la combinación con R-H1. El resto del cuadro de B se imprime en pruebas `#[ignore]`.

## B) Pregunta 2: ¿lo nuevo dice lo que dice su fuente, y cuenta lo que cuesta?

### Lo que coincide con la fuente

- **B.**
  - Candidatas y cotas: 12,5, 14 y 15 ms son 100, 112 y 120 periodos (`espera.rs:287-293`).
  - Las columnas del cuadro salen de las duraciones de `espera.rs:312-314`.
  - El «0 de 41» está aseverado. El «3 y 13 de 41» solo se imprime, y la prueba solo asevera que sea `> 0`.
  - Los reinicios a 115, 120 y 125 ms se cuentan desde la inyección a los 50 ms (`:371`). El modelo los corre con `W` = 55 ms (`motor.rs:93`).
- **C.**
  - 318 = 3 + 200 + 112 + 2 + 1.
  - 90 combinaciones = 3 × 5 × 6.
  - 305 periodos con (3, 200, 100).
  - 14,125 = 113 × 0,125.
  - 49 = 50 × 0,98.
- **H.**
  - 2 303 y 2 600 ciclos, 13,8 y 15,6 % (`EN-PLACA.md:917`).
  - 2 063 y 2 400 (`:897`).
  - «Unos 300 ciclos»: son 297 con el CRC y 337 sin él.
  - Mover la pila ahorra 100 ciclos: de 2 400 a 2 300 (`:897`, `:900`).
  - 8 120 y 4 616 B (`:908`) y 5 128 B (`:922`, A).
  - Los «12,7 KB» de su costo (12 736 B) no suman los 512 B de la ficha I. Con ellos son 13 248 B.
- **I.**
  - +238 y +648, +358 y +814, +1 565 y +4 660 (`EN-PLACA.md:916-920`).
  - 120 ciclos y 0,7 % de diferencia con 25 B. Con 71 B son 166 ciclos y 1,0 % (A), y la ficha no lo dice.
  - La unidad se comprobó contra `crc16` en placa (`j2_banco.rs:673-695`) y `crc16_con` contra `crc16` en el host (`descubrimiento.rs:211-223`).

### Los dos asertos de la ficha C, con sus ESTIMADOS

| Aserto | Cuenta | Términos y estatus | Margen | Lo que no entra |
|---|---|---|---|---|
| (1) del módulo | 318 × 125 µs = 39,75 ms < 49 ms | hueco: el de la máquina, fijado por prueba; +1 periodo (A); `T_WATCHDOG_TRAMA_US` = 50 ms (E, del módulo); tolerancia del 2 % (E; depende del reloj de cada módulo —la Voz es un N657—, así que es una decisión pendiente, no algo que no se pueda saber) | 9,25 ms | (a) la propiedad del planificador (hallazgo nuevo 1); (b) la recepción antes del armado que se cuelga y después del rearme: ≤ 1 periodo más con mensajes de 3 tics (A); (c) el retraso de entrada del tic, ≤ 60 µs por transición (R-H2). (b) y (c) caben de sobra en el margen. |
| (2) de la ficha B | 113 × 125 µs = 14,125 > 1 + 12 + 0,25 = 13,25 ms | espera de 1 ms (decisión); R-H1 = 12 ms (requisito del hub, sin escribir; testigo `latencia_plan_max_us`); recuperación de las seis ≤ 0,25 ms (E) | 0,875 ms | La repetición sale en la primera pasada de P3 en `hasta_us` o después: como mucho 1 periodo. La estimación de 0,25 ms de recuperación sobra: la medida es de 8 µs por ranura (123 → 131 µs, M), y con un canal que no para son 25 µs de `T_CANAL` (E) más 2 µs de escalada (M). El modelo asevera el caso (0 de 41). |

**Lectura.** El aserto (2) se sostiene con sus estimaciones. El aserto (1) solo se sostiene si el término de R-H1 no se suma, y eso depende de lo que señala el hallazgo nuevo 1.

### Hallazgos nuevos

**1. [ALTA] [CONTRA, ASSUMP] El término de R-H1 sale del aserto de C gracias a una propiedad del planificador de banco que el papel no exige, y el propio papel sigue contando ese término en el mayor hueco**
- **Evidencia.**
  - Ficha C: «el planificador compone la trama en la misma pasada en que pide la recuperación, y con `HECHA` ya está en el buzón».
  - §2.11: «más la espera de `Libre` al planificador que R-H1 admite (12 ms). Con las cotas candidatas son ~50 ms (A)». Lo repiten R-H8(3), la ficha D («forma parte del mayor hueco de sello») y §6, D5.4.
  - §2.6: «Tras una recuperación está vacío hasta que el planificador compone otra trama».
  - La propiedad sale del código de banco: `fw/src/j2_tic.rs:1032-1035` y `modelo/src/motor.rs:1357-1369`. La prueba de 90 combinaciones la da por supuesta, porque inyecta `bajada: Some(plazo)` junto con `reinicio_hecho` (`transporte_j2.rs:1569-1573`).
  - `motor.rs:93`: `sup_w_ns: 55_000_000, // mayor que el mayor hueco de sello, ~50 ms (papel v3, §2.11)`.
- **Problema.**
  - El hueco de sello y el hueco entre tramas empiezan en el mismo armado y acaban en el mismo rearme. El papel les da dos valores: 39,6–39,75 ms en C, y ~50 ms en §2.11 (51,6 ms con `Reiniciando` a 14 ms, A).
  - Lo que separa los dos valores es un requisito sobre el planificador del hub: dejar trama en el buzón en la misma pasada en que pide la recuperación, antes de que corra P4. Ese requisito no está en R-C8, ni en R-H1 a R-H9, ni en §5.2. Y el compositor real (#267) todavía no existe.
  - Si el requisito no se cumple, con `Vencida` a 25 ms el aserto da 39,75 + 12 = **51,75 > 49 ms (A)**. La otra opción de C, `Vencida` a 20 ms, cabe en los dos casos: 34,75 + 12 = 46,75 < 49 ms (A).
- **Qué rompe.**
  - Si vale la cuenta de C, la `W` del supervisor y los reinicios de B (115 a 125 ms con `W` = 55 ms) llevan unos 10 ms de más.
  - Si vale la cuenta de §2.11, el aserto pasa y el módulo suelta las notas de una ranura que el hub da por recuperada. Es el mismo fallo de mi hallazgo 1 de la cuarta pasada, que solo se movió del aserto al planificador.
- **Falta decidir.** ¿Dejar trama en el buzón en la pasada que pide la recuperación es un requisito del planificador del hub? Si lo es: ¿en qué requisito queda escrito y con qué prueba? Y ¿cuál es el mayor hueco de sello, el que dimensiona `W`?

**2. [MEDIA] [OPS, ASSUMP] Las cifras de H e I se midieron con el patrón ancho que la ficha H retira, y nada comprueba que el CRC siga en la ITCM con el patrón estrecho**
- **Evidencia.**
  - `EN-PLACA.md:911` (worktree `crc`): «el árbol de este cambio sin commitear, sobre `52f0521`».
  - Reflog del worktree `huella`: `638e844` («de core solo los módulos del J2, y la comprobación del cierre») es hijo de `52f0521` y posterior a él. Después, `j2/crc-sobre` se rebasó sobre `ae69911` y quedó en `488c778`. Halberg, en la cuarta pasada (`junta4_halberg.md:135`), ya dijo que `638e844` quitó «el patrón de todo `sam17_nucleo_core`».
  - `j2_tcm.x:30-34`: de `core` entran cinco módulos `*_j2`, y `descubrimiento` no está entre ellos. `crc16_con` vive en `core/src/descubrimiento.rs:98` y la llama `j2_banco.rs:657-660`.
  - `fw/Cargo.toml:59`: `lto = true`. Ni `build.rs`, ni `ci.yml`, ni `.githooks/pre-push` llaman a `tcm_cierre.py`.
- **Problema.**
  - El binario medido metía todo `core` en la ITCM. El que describe la ficha H no nombra el módulo del CRC, así que su cuerpo solo acaba en la ITCM si LTO lo inserta en línea dentro del juez. Es probable, pero nadie lo ha comprobado.
  - La aseveración de `lanzar` mira el puntero del juez (`juez_crc_tabla`, en `j2_banco`, que sí está dentro), no lo que el juez llama. `tcm_cierre.py` sí lo vería, pero nadie lo ejecuta.
  - Los 8 120 B de referencia son de `a1f6623`, también anterior al estrechamiento.
- **Qué rompe.**
  - Si `crc16_con` no se inserta en línea, el CRC se lee de la AXISRAM2 con la I-cache fría. Es justo el fallo que H existe para evitar, y el mismo de §0.4, punto 26.
  - En ese caso, la fila que decide si el J2 cabe (13,8 % frente a 15,6 %) y el orden de las opciones de la ficha I describirían otro binario.
- **Falta decidir.** ¿Qué binario sostiene las cifras de H e I que se firman? ¿Quién corre `tcm_cierre.py` sobre ese binario, y lo deja conectado a algo que pueda fallar?

**3. [MEDIA] [SCOPE, CONTRA] La ficha I enmienda texto del receptor del módulo con una medida del planificador del hub, y deja sin tocar la línea que gobierna el CRC del hub**
- **Evidencia.**
  - Ficha I: enmendar «por eso el CRC se computa sobre el búfer al subir `CS`, con la unidad» y «su §10, riesgo 5».
  - Cabecera, D2 (`2026-09-02-cabecera-j2-design.md:151-155`): el CRC del SPI está atado a `TSIZE`, «que un receptor de largo variable no conoce de antemano». Quien no conoce `TSIZE` es el esclavo, y en esa spec «el N657» es el de la Voz (`:40`, `:59`). La ficha cita «D1», pero la frase está en D2: D1 es «Una trama, un tipo» (`:84`).
  - Riesgo 5 (`:981-990`): «El receptor no cabe en la fila del libro del motor», con «47 ciclos por muestra de costo fijo (… EXTI …)». El libro del motor cuenta «~8 333 ciclos/muestra» (`motor-digital-design.md:274`), es decir, 96 kHz.
  - D9 (`cabecera:605-608`): el `decodificar` de `core`, que llamarán los dos extremos (`:41-42`), usa «el CRC reutilizado de `descubrimiento::crc16`», que es el CRC por bits: +1 565 ciclos y 21,8 %.
  - `EN-PLACA.md:923` traduce el riesgo 5 como «82 a 92 ciclos por trama». La cabecera dice «por muestra».
- **Problema.**
  - La pregunta de la ficha es sobre el CRC de la subida en el hub. La frase y el riesgo que enmienda son del oyente de la Voz: otra CPU, otro presupuesto (por muestra) y ninguna medida de ese lado.
  - «Se quedó corta unas cuatro veces» compara cosas distintas: el incremento por giro en el hub (358 ciclos, 23 B) con un total por muestra en el módulo (82–92 ciclos, de los que 47 son fijos).
  - Por palabra, la unidad costó en placa de ~47 a ~62 ciclos, frente a los 16 que supone el riesgo 5 (A). Esa diferencia cae sobre la fila del oyente de motor-digital §7, y nadie la recuenta.
  - D9, la línea que sí fija el CRC del hub, no está en la lista de enmiendas.
- **Qué rompe.** Firmada así, la ficha I cambia el diseño del receptor del módulo sin evidencia de ese lado, y deja el códec del hub con el CRC por bits. El 13,8 % de la ficha H supone una tabla que D9 no pide.
- **Falta decidir.** ¿La ficha I decide solo el CRC de la subida en el hub, o también el del receptor de la Voz? Si es solo el del hub: ¿cómo queda D9, y quién recuenta la fila del oyente con el costo por palabra medido?

**4. [MEDIA] [CONTRA, SCOPE] Qué cifra entra en el censo, la del DWT o la del medidor, aparece decidida en el costo de H y abierta en §3, y de eso depende que el J2 quepa en el 15 %**
- **Evidencia.**
  - Ficha H, costo 3: «hasta medirlas, la cifra del censo es la del medidor».
  - §3 (`papel-v3.md:278`): «Qué cota cuenta, y con ella si hace falta la pasada de optimización (~300 ciclos), lo decide Samuel».
  - §3 (`:270`): «el `DWT` (cota de diseño) / el medidor del hilo (techo…)».
  - §11, fila S5: «la cifra del censo es la del medidor hasta separarla (ficha H, §3)».
  - `EN-PLACA.md:881`: el medidor cuenta como J2 la I-cache vaciada del hilo medidor.
- **Problema.**
  - Con el CRC por tabla, el J2 cuesta el 13,8 % según el DWT o el 15,6 % según el medidor, frente a un 15 % provisional. Según el párrafo que se lea, el J2 no cabe, o cabe y la decisión es de Samuel.
  - Ninguna ficha hace la pregunta, así que firmar H la contesta a través de una línea de costo.
  - Ninguna de las dos cifras es el costo real del J2. Al DWT le falta la entrada de la excepción, y el medidor arrastra un artefacto propio. La que se firme tiene que decir hacia qué lado se equivoca.
- **Qué rompe.** Samuel puede firmar H creyendo que la cifra queda abierta y encontrarse un censo que arranca con el J2 por encima del 15 %, o al revés. Que haga falta o no la pasada de optimización dependería de una línea de costo.
- **Falta decidir.** Mientras la entrada de la excepción no esté separada, ¿qué cifra lleva la fila del J2 en el censo, y en qué ficha se firma?

## C) Preguntas que el papel evita

1. ¿El planificador del hub está obligado a dejar trama en el buzón en la misma pasada en que pide la recuperación, y con qué prueba se comprueba? (hallazgo nuevo 1)
2. ¿El mayor hueco de sello, el que dimensiona `W`, es de 39,6 ms o de 51,6 ms? (hallazgo nuevo 1)

## D) Riesgos por categoría

- **Técnico:** hallazgos nuevos 1 y 2.
- **Producto:** el 1 (notas soltadas en una ranura que el hub da por recuperada) y el 4 (el veredicto de «cabe en el 15 %»).
- **Ejecución y operaciones:** el 2 (una puerta sin conectar a nada) y el 3 (una enmienda que cae en la spec del otro extremo).

## E) Aclaraciones inmediatas

No hay BLOCKER. La única ALTA, el hallazgo nuevo 1, impide firmar la ficha C tal como está.

## Fuera de alcance, una línea cada uno

- `reloj_anomalo` volvió a salir con TCM y las cachés apagadas (`EN-PLACA.md:926`). La ficha C sigue afirmando «Con K2 las cotas son de pared (S)», y R-H9 sigue sin comprobarse.
- La rama que escala porque un canal no para en `T_CANAL` sigue sin correr en placa (`EN-PLACA.md:932`). Toda la ficha B descansa en el modelo.

## Veredictos

- **B: sí.** Se firman 6 escaladas en 1 s y la espera de 1 ms, junto con `Reiniciando` a 14 ms y el aserto (2), que se pueden firmar con B aunque C espere. Lo pendiente (§2.1, §2.2, §5.2(i) y la frase de los 71 B) es texto y no cambia la decisión.
- **C: todavía no.** Falta decidir si el planificador del hub debe dejar trama en la pasada que pide la recuperación, escribirlo con su prueba, y dejar un solo valor del mayor hueco en C, §2.11, R-H8, D y §6. Sin eso, `Vencida` a 25 ms solo cabe gracias a esa propiedad; 20 ms cabe en los dos casos.
- **H: no tal como está.** La obligación por símbolos y sus dos puertas se pueden firmar. Antes hay que sacar del costo 3 la frase que fija la cifra del censo (hallazgo nuevo 4) y conectar `tcm_cierre.py` a algo que pueda fallar sobre el binario con el patrón estrecho (hallazgo nuevo 2).
- **I: no tal como está.** La tabla gana en el hub con datos medidos. Falta limitar la enmienda a la subida del hub (D9, no D1 ni el riesgo 5 del receptor de la Voz) y comprobar con `tcm_cierre.py` que `crc16_con` queda en la ITCM con el patrón estrecho.
