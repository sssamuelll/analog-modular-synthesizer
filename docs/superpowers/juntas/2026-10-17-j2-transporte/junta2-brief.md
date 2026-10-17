# Brief de junta — segunda pasada — 2026-10-17 — el transporte «por tic» (papel v3)

## 1. La pregunta

El 2026-10-17 Samuel firmó el acta de la primera pasada (`acta-2026-10-17.md`): el trabajo propio del enlace cuenta contra los 2 500 ciclos por giro (ficha 1, **A**), el 15 % es provisional hasta que exista el censo del hub (ficha 2, **A**) y se construye un prototipo del transporte «por tic» (ficha 3, **A**). El prototipo está construido, medido y en `main` detrás de features (PR #437–#440, `main` en `ef73a85`). Nada de él entra en el binario del instrumento; **D5.1 sigue en vigor**.

`papel-v3.md` absorbe lo que el prototipo y la revisión del código enseñaron y **propone adoptarlo como el transporte del J2**, con seis fichas para Samuel (§1) y unas condiciones antes de que entre en el instrumento (§5). Lo único que se firma después de esta pasada es eso. La junta contesta cuatro cosas:

1. **¿Sobrevive v3 a un intento serio de romperlo?** Sobre todo en lo nuevo: el presupuesto de escaladas (§2.5), el presupuesto de retraso del tic (§2.8), las cotas de 100 y 100 tics (§2.5), «nada» cuando el planificador se atrasa (ficha C) y la subida un periodo más tarde (ficha D).
2. **¿Alguno de esos mecanismos tiene el mecanismo equivocado?** La primera pasada tumbó siete de ocho; esta pregunta es la misma.
3. **¿Las seis fichas están bien planteadas?** Opciones, costo de cada una, recomendación. ¿Falta una opción? ¿La recomendación de la ficha A descansa en un supuesto que v3 no declara?
4. **¿Qué evidencia falta antes de firmar, y cuál de las condiciones de §5 sobra, falta o no se puede verificar tal como está escrita?**

## 2. Lo que ya está resuelto y no se reabre

- Las decisiones de la primera pasada (`junta_serrano.md`, `junta_halberg.md`, `junta_voronov.md`, `papel-v2.md` §8): el tic único, el estado de la ranura con un solo escritor, el cierre con `EOT ∧ TCF`, la recuperación con `RESET`, la política como única autoridad sobre «reiniciar». Se puede atacar su **ejecución** en v3, no la decisión.
- Las tres fichas del acta del 17-10.
- La revisión del código (`junta_halberg_codigo.md`): nueve hallazgos, seis cerrados en el código y tres abiertos, que v3 recoge en §0, §2 y §7.

## 3. Qué hay de nuevo desde v2 (resumen; el detalle está en v3 §0 y §8)

Buzón de tres casillas; cotas de 2 y 4 tics a 100 y 100; reloj de la política de 64 bits; recuperación medida (123 / 131 / 249 µs); la CPU medida (1 967 el enlace solo, 2 100 con una trama compuesta de mentira, 2 778 con la D-cache vaciada entre tics, contra 8 000 del ejecutor y un límite provisional de 2 500); integridad con marcos numerados bajo golpes de P3, cuelgues y errores del DMA (4 × 60 s y 4 × 150 s, sin una trama rota, repetida ni vieja); el cable del banco rompe los marcos de apariencia aleatoria con los pines a `VeryHigh` (llegan enteros 4 de 16 contenidos de prueba; con `Medium`, 16); y **dos mecanismos propuestos y sin construir**: el presupuesto de escaladas y el de retraso del tic.

## 4. Lo que se le pide a cada lente

**Serrano (análisis de spec: incertidumbre peligrosa, supuestos sin declarar, contradicciones).**
- Cruza v3 contra la spec firmada (`docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`: D2 a D5.4, D7, R-MJ, §3, §9 y sus enmiendas) y contra el acta del 17-10: ¿qué frase de la spec queda falsa o ambigua con v3 y no figura en §6?
- ¿Cada número de v3 dice si es medido, estimado o aritmética sobre lo medido? Busca los que no lo dicen (por ejemplo «≤ 8,8 µs», «84 / 98 / 64 µs», «6,5 a 9 %», «3 por segundo», la columna de seis ranuras de §3).
- ¿La recomendación de la ficha A descansa en un supuesto no declarado («el ejecutor no cabe en ningún reparto plausible»)? ¿Las seis fichas se pueden contestar sin leer el resto? ¿Algún costo mal contado, alguna opción que falte?
- ¿De qué definición de la ficha 1 sale «12,6 a 13,9 %» y qué le falta? ¿Hay doble contabilidad entre el tic y el planificador?
- ¿Alguna condición de §5 es imposible o inverificable como está escrita (por ejemplo 5.2(d): el banco tiene un solo esclavo)?

**Halberg (viabilidad de ejecución: concurrencia, modos de fallo, simulación).**
- **§2.5, el presupuesto de escaladas:** ¿funciona bajo concurrencia real? La recuperación (nivel 4) es la única que escala; ¿puede haber dos escaladas solapadas?, ¿qué pasa si la ranura que se da por muerta por presupuesto estaba en vuelo?, ¿en qué orden se mira el contador y se declara la muerte, y quién la ve (el tic)? Cadena temporal completa de un fallo: tic → plazo vencido → recuperación → escalada denegada → `Muerta` → el IWDG; ¿cuánto silencio le llega al módulo (~50 ms) y cuánto al instrumento?
- **§2.8, el presupuesto de retraso del tic (60 µs):** ¿es alcanzable dados R-H1/R-H2 y el hub real (tic en el nivel 1, USB y pantalla en el 2, secciones críticas ≤ 5 µs)? ¿Qué le hace al tic el armado de seis ranuras seguidas (8,8 µs, extrapolación lineal de tres) si llega tarde?
- **Las cotas de 100 tics = 12,5 ms** solo si los tics no se funden (`tics_fusionados`). ¿Cuántos pueden fundirse sin que la cota deje de proteger?
- Seis ranuras: el máximo enmascarado, seis `SET` de dieciséis coincidentes (R-H5), la cola compartida del planificador.
- ¿Qué de lo que v3 afirma no lo cubre la evidencia de §4.2? (Una sola ranura con esclavo, 25 bytes, la escalada solo forzada.) Simula lo que haga falta en el host; no escribas dentro del repo.

**Voronov (arquitectura ontológica: errores de categoría, rupturas de abstracción, composabilidad).**
- ¿Qué es «un tic», «un periodo» y «un plazo» ahora? Las cotas y los plazos se cuentan en tics; el módulo (~50 ms) y el IWDG, en µs. ¿Es el mismo objeto visto dos veces o dos objetos?
- **La escalada es el único acto que cruza ranuras** en una arquitectura de ranuras independientes (H-1 de la primera pasada: un plazo vencido en una ranura no retrasa a las otras). ¿El presupuesto la arregla o la deja? ¿Es una regla de la capa correcta (recuperación, política, supervisor del hub)?
- ¿Quién es el dueño de qué? R-C8 (un solo escritor del enlace) con «el tic arma, el planificador compone, la recuperación reinicia». «`Muerta` ⇒ el IWDG reinicia el chip»: ¿es política de salud del J2 o del hub?
- La restricción invisible de la primera pasada era la clausura (el censo de CPU del hub no existe). v3 dice «el censo decide el presupuesto, no el transporte» (ficha A). ¿Es un argumento o evita la pregunta?

**Las tres:** ¿falta una opción en las fichas de v3 §1? ¿Cuál de las seis habría que contestar distinto de lo recomendado, y por qué?

## 5. Cómo responder

Informe en Markdown, en español, con las referencias a v3 por sección. Cada hallazgo con evidencia (cita de ≤ 25 palabras o `archivo:línea`), gravedad (BLOCKER / ALTA / MEDIA / BAJA) y qué lo rompe en concreto. No reescribas el papel ni propongas el texto: di dónde falla y por qué. Si algo está bien y lo comprobaste, dilo en una línea. Máximo 15 hallazgos por lente.

## 6. Archivos que la junta puede leer (rutas absolutas)

Repo `D:\Desktop\projects\sam17\.claude\worktrees\papel-v3` (rama `docs/papel-v3-transporte-tic`, sobre `main` en `ef73a85`):

- `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v3.md` (**el papel a juzgar**), `papel-v2.md`, `papel-v1.md`, `acta-2026-10-17.md`, `junta-2026-10-17-brief.md`, los tres informes de la primera pasada y `junta_halberg_codigo.md` (la revisión del código).
- `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md` (la spec firmada, con sus enmiendas).
- `software/nucleo/core/src/transporte_j2.rs` (la máquina, con sus pruebas), `buzones_j2.rs`, `marcos_j2.rs`, `maestro_j2.rs` (la política y `Umbrales`).
- `software/nucleo/fw/src/j2_tic.rs` (el transporte), `j2_spi.rs`, `j2_esclavo.rs`, `j2_banco.rs`, `j2_ejecutor.rs` (el transporte firmado), y los binarios `software/nucleo/fw/src/bin/tic_*.rs`.
- `software/nucleo/fw/EN-PLACA.md`, sección «El transporte por tic» (todo lo medido, con el firmware y la fecha de cada cifra).
- `hardware/02-midi-cv/carga_hub_budget.py` (el censo, 11 filas sin cifra), `recuperacion_j2_budget.py`, `latencia_mano_budget.py`.
- Manual: `D:\Desktop\projects\sam17\docs\reference\datasheets\stm32n6-rm0486-rev4.pdf` (en el árbol principal; no está en este worktree).
