# Voronov · lente ontológica · quinta pasada · fichas B, C, H e I (`papel-v3.md`, commit 255ed15) · 2026-10-19

**Lectura y alcance.** Leí mi `junta4_voronov.md` y, del papel:

- §0.5;
- las fichas B, C, H e I de §1;
- R-H1 y R-H4;
- §2.1, §2.2 (K4), §2.5, §2.8, §3 y §11.

En código y specs leí lo que sigue. Los prefijos de las citas remiten a estos árboles:

- **`espera:`**, `D:\Desktop\projects\sam17\.claude\worktrees\espera\software\nucleo`:
  - `core/src/escaladas_j2.rs`;
  - `core/src/transporte_j2.rs` (`hueco_de_recuperacion` y su prueba);
  - `core/src/maestro_j2.rs:32`;
  - `modelo/src/motor.rs` (P3, P4 y la escalada) y `modelo/tests/espera.rs`;
  - los dos `Reloj64` de `fw/src/j2_tic.rs`.
- **`huella:`**, `D:\Desktop\projects\sam17\.claude\worktrees\huella\software\nucleo\fw`:
  - `j2_tcm.x`, `tcm_cierre.py` y `src/j2_tcm.rs`;
  - `src/j2_tic.rs` (`lanzar`, `PlanRanura`);
  - los tipos `Bajada` y `Juez` de `src/j2_ejecutor.rs`.
- **`crc:`**, `D:\Desktop\projects\sam17\.claude\worktrees\crc\software\nucleo`:
  - `core/src/descubrimiento.rs` (`crc16_con`);
  - `fw/src/j2_banco.rs` (los tres jueces);
  - `fw/Cargo.toml` y `fw/EN-PLACA.md:905-926`.
- **Cabecera:** `D:\Desktop\projects\sam17\.claude\worktrees\junta4\docs\superpowers\specs\2026-09-02-cabecera-j2-design.md`: D2, §7.11 y §10, riesgo 5.
- **Motor-digital:** `...\specs\2026-08-26-motor-digital-design.md`: §2 y §7.

No ejecuté nada, porque esta sesión no tiene shell. Las cifras nuevas son aritmética **(A)** o inferencias marcadas como tales. `papel:N` remite a líneas de `papel-v3.md` en 255ed15.

## La restricción invisible de esta pasada

La cuarta pasada encontró que cada ficha metía un hecho de otro dueño en un recipiente del J2. El papel absorbido responde con declaraciones y con puertas. Las declaraciones son correctas. Las puertas, en cambio, se evalúan todas dentro del crate o del binario del J2:

- **B y C.** El aserto que las ata compara constantes del J2 con copias, hechas por el J2, de números que son del hub y del módulo.
- **H.** Las dos puertas comprueban que un conjunto elegido con nombres del banco esté cerrado. No comprueban que contenga las raíces ni que deje fuera lo que no es del J2.
- **I.** Lleva una medida del maestro, contada por trama, al libro del esclavo, que cuenta por muestra.

La frontera de verificación no se movió; se movió la prosa.

## 1. Mis hallazgos de la cuarta pasada

- **H1 (BLOCKER) · Resuelto.**
  - **Lo que cambió:** espera de 1 ms, `Reiniciando` de 14 ms y un aserto que las ata (papel:63, 79).
  - **La prueba que faltaba ya corre:** tras un bloqueo de 1 ms, una retención de 12 ms reinicia el chip en 0 de 41 arranques (`espera:modelo/tests/espera.rs:117-136`).
  - **Lo que queda:** la categoría (`Reiniciando` con dos esperas de dueños distintos) está declarada, no disuelta. La reserva va en N1.
- **H2 (ALTA) · Resuelto en parte.**
  - **Resuelto:** el segundo peticionario está declarado (papel:78, costo 3; papel:145) y tiene testigo. La muerte sin juez ahora exige romper R-H1.
  - **Pendiente:** §2.1 sigue contando «ocho elementos con escritores en tres niveles» (papel:114) y no nombra `hasta`, que escribe P4 y borra P3 (`motor.rs:1182`, `1311`). Ver N4.
- **H3 (MEDIA) · Resuelto.**
  - El umbral E × espera está en la ficha: «unos 6 ms» (papel:78).
  - El barrido llega a 15 ms en la tabla y a 20 ms en la prueba (`espera.rs:311-315`).
  - El bloqueo figura como escenario, no como tasa.
- **H4 (MEDIA) · Resuelto en parte.**
  - **En el papel:** quedó como condición de `fw` (papel:78, costo 4). Pero `fw` no tiene la espera.
  - **En el modelo que sostiene la ficha:** la espera se fecha con el reloj de 32 bits de P4 (`motor.rs:1169`) y se compara con el `Reloj64` de P3 (`motor.rs:1092`). En corridas de 4 s no hace daño.
  - **Lo que queda:** el reloj único que pide la condición no tiene dueño (N4).
- **H5 (ALTA) · Resuelto.**
  - `hueco_de_recuperacion` cuenta `cota + 1` por estado (`transporte_j2.rs:36-38`). Una prueba lo fija contra la máquina en 90 combinaciones (`:1582-1597`).
  - Entra la trama siguiente, y sale el término de R-H1 con su razón.
  - El aserto en `lanzar` todavía no existe (§5.2 j); el papel lo dice.
- **H6 (MEDIA) · Resuelto en parte.**
  - **Escrito:** dueño, estatus ESTIMADO, tolerancia del 2 % y umbral de revisión de ~41 ms (papel:79).
  - **Pendiente:** `T_WATCHDOG_TRAMA_US` sigue siendo una constante de `core::maestro_j2` (`maestro_j2.rs:32`), y de ahí la leerá el aserto (N1).
- **H7 (ALTA) · Resuelto en parte.**
  - **Corregido:** el estatus de la cifra (M en el banco, E en el hub). De `core` entran solo cinco módulos (`j2_tcm.x:30-34`). Las puertas existen (`tcm_cierre.py`; `j2_tcm.rs:95-105`).
  - **Pendiente:**
    - la selección sigue hecha con nombres del banco: `TIM7 DMA2D JPEG`, `j2_banco`, `j2_ejecutor`, `marcos_j2`, `embassy_stm32::rcc::RccInfo` (`j2_tcm.x:25-35`);
    - las raíces no tienen puerta;
    - la obligación ahora arrastra al compositor (N2).
- **H8 (MEDIA) · Resuelto.**
  - Las obligaciones de arranque quedan del hub (#231) para todo lo que viva en la DTCM (papel:80, costo 2; papel:94).
  - Los datos de solo lectura tienen su puerta, que es la medida.

## 2. Lo nuevo

### N1 · ALTA · B×C: el aserto que ata B y C suma un solo R-H1 a un camino que cruza dos niveles, y compara contra copias

**Evidencia**
- papel:79, ficha C (2): «`(cota_reiniciando + 1) × T > espera + R-H1 + la recuperación de las seis` (≤ 0,25 ms, E): 14,125 > 13,25 ms».
- papel:91, R-H1:
  - «el planificador en el 3; la recuperación en el 4»;
  - la ventana es «el mayor intervalo en que el planificador **o** la recuperación no pueden correr».
- papel:216: `latencia_plan_max_us` va «del instante en que el tic hace pendiente al planificador a que arranca: es lo que observa R-H1». La latencia de P4 no tiene testigo.
- `motor.rs:1305-1316`: al cumplirse la espera, P3 pone `rec_pedida` y deja pendiente a P4. `motor.rs:1108-1121`: P4, que está en otro nivel, la recoge después.
- `espera.rs:93-115`: la prueba que respalda el aserto aplica **una** retención de P2.
- R-H1 no tiene constante en ningún crate (busqué `R_H1` y `VENTANA`: nada). `T_WATCHDOG_TRAMA_US = 50_000` vive en `core::maestro_j2.rs:32`, que es el crate del J2.

**Qué rompe**
- **Los dos niveles.** Para salir de una `Reiniciando` aplazada hacen falta dos niveles en serie: P3 vuelve a pedir y P4 ejecuta. R-H1 está escrito en disyunción.
- **Con la lectura que mide su testigo** (latencia desde que cada nivel queda pendiente, ≤ 12 ms por nivel):
  - dos ventanas legales seguidas dan 1 + 12 + 12 + 0,25 = **25,25 ms > 14,125** (A);
  - las seis ranuras aplazadas vencen juntas y el supervisor reinicia el chip, con saldo en el presupuesto;
  - es H1 otra vez, por otro camino.
- **Con la lectura de ocupación** (todo lo que corre por encima de P4, P3 incluido, ≤ 12 ms seguidos), un término basta. Pero entonces R-H1 no tiene quien lo observe, porque `latencia_plan_max_us` mide P3 desde el tic.
- **La asimetría lo delata.** `Vencida` recorre el mismo camino de dos niveles: P3 decide y P4 arranca. Sus 25,125 ms cubren 2 × 12 = 24 (A) con cualquiera de las dos lecturas. `Reiniciando` con espera solo sobrevive con una de ellas.
- **Los términos ajenos del aserto son copias del J2.** R-H1 tendrá que escribirse como constante del J2, y `T_WATCHDOG_TRAMA_US` ya lo es.
  - El aserto solo puede fallar si el J2 edita sus propias constantes.
  - Cuando voz-total escriba su watchdog, o cuando el hub mida su ventana, el J2 seguirá compilando en verde.
  - «Un aserto las ata» es cierto entre B y C. Hacia el módulo y hacia el hub, el aserto es un espejo.

### N2 · ALTA · H: el J2 de la obligación (el alcance), el de la selección (los nombres) y el de la cuenta (la función) no son el mismo

**Evidencia**
- papel:80, ficha H (1): «el texto de los tres manejadores del J2 [...] y todo lo que alcanzan, también por los punteros del juez, la bajada y el reset de cada ranura, en la ITCM».
- **El compositor y el juez entran por puntero:**
  - `huella:src/j2_tic.rs:684-689`: `PlanRanura` guarda «la politica, el compositor y los bufferes locales», con `bajada_fn: Bajada`, que el hub le pasa a `lanzar`.
  - `j2_ejecutor.rs:132` y `:352`: `Bajada = fn(n, buf) -> Tsize`, y «El planificador decide que baja».
  - `j2_ejecutor.rs:136-138`: «El juez de verdad valida el sobre y su CRC (cabecera D6.1)».
  - `j2_tic.rs:732-733`: `asevera_en_itcm(juez)` y `asevera_en_itcm(bajada_fn)`.
- **La cuenta excluye componer:**
  - papel:71, ficha 1 del acta: contra los 2 500 ciclos cuenta el enlace, «y no componer la trama».
  - papel:270 y `EN-PLACA.md:908, 911`: la huella de 8 120 B y las filas con TCM se midieron sin componer o con el compositor de mentira.
- **Las puertas no ven las raíces:**
  - `tcm_cierre.py:26-38` solo recorre los saltos que **salen** de `.itcm`.
  - `j2_tcm.x:25`: las raíces entran por el nombre de vector del banco.
  - Ninguna de las dos puertas lee la tabla de vectores.
- **El CRC vive fuera de los módulos del J2:**
  - `crc:core/src/descubrimiento.rs:96-104`: `crc16_con` está en `descubrimiento`, y el guion no selecciona ese módulo (`j2_tcm.x:30-34`).
  - Con TCM y las dos cachés frías, el planificador con CRC cuesta 19 ciclos más que en caliente (`EN-PLACA.md:917`). Eso quiere decir que su cuerpo corrió desde la TCM.
  - Con `lto = true` (`Cargo.toml:59`), la única vía es que se haya inlinado en `juez_crc_tabla`, que sí entra por `j2_banco*` [inferido: no lo comprobé con `rust-objdump`].

**Qué rompe**
- **Hay tres J2 distintos:**
  - el de la obligación: todo lo alcanzable, incluidas la capa de contenido (el compositor) y la de protocolo (el juez y el CRC);
  - el de la cuenta de CPU: el enlace sin componer;
  - el del guion: cinco módulos de `core` más nombres del banco.

  La huella de referencia mide el tercero, y la ficha hace firmar el primero.
- **El punto de presión es el primer compositor real.** Con las puertas como están:
  - su texto y todo lo que llama tienen que vivir en la ITCM;
  - sus datos de solo lectura caen en la medida en frío, que se toma sobre una fila sin componer.

  Pasa una de dos cosas: o la puerta del J2 falla por código cuyos ciclos el J2 no cuenta, o el guion de enlace del J2 decide dónde vive la capa de contenido del hub. En los dos casos, quien decide no es el dueño.
- **El conjunto puede estar cerrado sin contener las raíces.** En el hub, los vectores los fija R-H1 (papel:116). Si el del planificador no se llama `DMA2D`, su manejador, con lo que LTO haya inlinado en él, se queda en la AXISRAM2:
  - `tcm_cierre.py` no ve nada, porque nada sale de la ITCM;
  - las aseveraciones miran tres punteros, y ninguno es un vector;
  - solo lo atraparía la medida en frío, que es una medida, no una puerta.
- **El CRC ya cruzó la frontera.** El cierre del J2 alcanza `descubrimiento`, que no es un módulo del J2, y hoy lo tapa una decisión del optimizador. Si el CRC deja de inlinarse, chocan dos reglas firmadas:
  - «de `core`, solo los módulos del J2» (R-H4);
  - «un solo CRC, el de `descubrimiento`» (cabecera, D2).

### N3 · ALTA · I: el «cuatro veces» compara ciclos por muestra del motor con ciclos por trama del hub, y la enmienda cae en el libro de otro dueño

**Evidencia**
- papel:81, ficha I:
  - «la cuenta de la cabecera (82 a 92 ciclos) se quedó corta unas cuatro veces»;
  - costo: «enmendar la frase de la cabecera [...] y su §10, riesgo 5».
- `crc:fw/EN-PLACA.md:923`: «(§10, riesgo 5: 82 a 92 ciclos **por trama** con la unidad)».
- Cabecera:982-986: «47 ciclos **por muestra** de costo fijo (entrar y salir de la ISR, EXTI, contar, encolar, rearmar el DMA, reiniciar el TX) a 8 kHz de tramas, y 82-92 con la unidad CRC [...], 101 con una tabla [...], 262 bit a bit». En 874-876, 1014 y 1062 la unidad es también por muestra.
- Motor-digital:111: «~8 300 ciclos por muestra a 48 kHz». Motor-digital:283: la fila «Oyente J2 amortizado».
- Cabecera:986-990: el riesgo 5 se cierra con la enmienda al libro del motor, que «sobrevive por el ×3 del guion `carga_motor`», y lo mide el bring-up. La tabla era la salida solo si la unidad no reproducía CCITT-FALSE.

**Qué rompe**
- **La cifra.** A 48 kHz de muestras y 8 kHz de tramas hay 6 muestras por trama (A). La parte CRC de la cuenta de la cabecera, pasada a ciclos por trama, da:

  | Implementación | Cabecera, por trama (A) | Medido en el hub (M) |
  |---|---|---|
  | Unidad | (82 a 92 − 47) × 6 = **210 a 270** | +358 |
  | Tabla | 324 | +238 |
  | Bits | 1 290 | +1 565 |

  - **La unidad** se quedó corta entre 1,3 y 1,7 veces, no cuatro.
  - **La tabla** estaba sobrestimada.
  - **Lo que de verdad enseña la medida:** el orden se invirtió. La cabecera ponía la unidad por debajo de la tabla, y la placa pone la tabla por debajo de la unidad.
  - **De dónde sale «cuatro veces»:** de comparar 358 por trama con 82 a 92 por muestra (A). Supongo el mismo largo de trama que usó H-3, sin haberlo verificado.
- **El dueño.**
  - El riesgo 5 trata del receptor del módulo, que es el esclavo: EXTI, rearme del DMA y TX. Su libro cuenta en ciclos por muestra y vive de un margen ×3.
  - La ficha I mide el maestro: el CRC de la subida en P3, con TCM, a 800 MHz.
  - La frase de D2 («por eso el CRC se computa sobre el búfer al subir `CS`, con la unidad») vale para los dos extremos. Enmendarla con la medida de uno decide la implementación del otro.
- **El punto de presión.** Si la enmienda se aplica tal como está escrita, alguien multiplicará por cuatro la fila del oyente, de ~100 a ~400 ciclos por muestra, en un libro que solo cabe gracias al ×3. La cifra sale bien de la placa y se estropea al copiarse.
- **El criterio cambió sin decirlo.**
  - La cabecera cerraba con la tabla solo por corrección, y la unidad reproduce el CRC en la placa (`crc:fw/src/j2_banco.rs:673-696`).
  - La ficha cambia el criterio a costo. Es legítimo, pero eso es una decisión nueva, no una corrección de la cabecera.

### N4 · MEDIA · B: el segundo peticionario es P3 haciendo de temporizador de P4, y trae dos estados entre niveles que nadie cuenta

**Evidencia**
- papel:145 (K4): «la política es el único peticionario (con la espera de la ficha B, el planificador repite la petición [...]: es la misma petición entregada tarde [...])».
- `motor.rs:1112-1113`: P4 consume `rec_pedida`. En `:1178-1183` contesta `Aplazada`. O sea, la petición de la política llegó a tiempo y tuvo respuesta; lo que llega tarde es la continuación de P4.
- papel:78, ficha B, costo (4): «la espera se fecha y se compara con un solo reloj, el del tic extendido a 64 bits».
- **Los dos relojes de `fw` tienen un solo escritor por construcción:**
  - `espera:fw/src/j2_tic.rs:452-454`: `RELOJ_PLAN`, «Dueno: el planificador»;
  - `:1238-1239`: `RELOJ_REC`, «la recuperacion es la unica que toca»;
  - `Reloj64::extiende(&mut self, ...)` (`transporte_j2.rs:146`).
- papel:114: el estado de la ranura sigue siendo de «ocho elementos».

**Qué rompe**
- **La categoría.** No existe una segunda petición de la política. Existe una decisión de P4 («todavía no») que P4 no puede retomar por su cuenta, porque es una interrupción pendiente sin reloj propio, y P3 le hace de temporizador. Llamar a eso «la misma petición entregada tarde» salva la frase de K4 a costa de cambiar lo que significa «peticionario».
- **El reloj único no tiene dueño.**
  - Un reloj compartido sería un valor de 64 bits escrito en un nivel y leído en otro que lo interrumpe, porque P3 desaloja a P4.
  - Nadie dice quién lo extiende ni cómo lo lee P4 sin leerlo partido.
  - Si cada nivel conserva el suyo, como hoy, vuelve H4. Si P4 lee el de P3, aparece una publicación nueva entre niveles.
- **El censo.** §2.1 dice que todo lo que el papel diga de «el estado» se refiere al conjunto. El conjunto ganó `hasta` (de P4 a P3) y ese reloj, y el censo no cambió. El modelo es secuencial y lee un `self.tics` global, así que no puede ver una lectura partida.

## Veredictos

- **B.** No se firma tal como está.
  - La regla (6 en 1 s, espera de 1 ms) se sostiene.
  - El acoplamiento depende de una lectura de R-H1 que el papel no fija ni observa (N1).
  - El reloj único no tiene dueño (N4).
- **C.** No se firma tal como está.
  - Las cotas y el aserto del módulo se sostienen.
  - El aserto de B hereda N1, porque B y C son un solo número.
  - Los dos asertos comparan contra copias del J2, no contra sus dueños.
- **H.** No se firma. Falta decidir si el cierre que imponen las puertas incluye el compositor y el juez, que no son del J2, y falta alguna verificación de las raíces (N2).
- **I.** La tabla en el hub, sí se firma. La enmienda a la cabecera, tal como está escrita, no:
  - su «cuatro veces» compara ciclos por muestra con ciclos por trama;
  - alcanza el riesgo 5 del módulo con una medida del maestro (N3).

## Lo que no verifiqué

- No corrí nada: ni las pruebas del modelo, ni `tcm_cierre.py`, ni `rust-objdump` o `rust-nm`.
- Que `crc16_con` esté inlinado en `juez_crc_tabla` (N2) lo infiero de la medida en frío y del guion de enlace.
- No comprobé que las dos puertas de H se hayan «comprobado rompiéndolas» (papel:462).
- No sé qué largo de trama supuso H-3 (N3), ni qué vectores fijará R-H1 en el hub.
- Nadie ha corrido la lectura por nivel de R-H1 (N1): la prueba del modelo aplica una sola retención.
- No leí los informes de Halberg y Serrano de la cuarta pasada.

## Cierre

La cuarta pasada encontró hechos guardados en el recipiente equivocado. En esta, el papel ya les escribe el dueño correcto en la prosa, pero los verifica contra la copia que guarda el J2. Un aserto contra tu propia copia de la constante de otro no puede fallar cuando el otro cambia. Una puerta que mira si tu conjunto está cerrado no ve lo que nunca entró en él.

La declaración ya está hecha. Falta que la verificación cruce la misma frontera que ya cruzó la prosa.
