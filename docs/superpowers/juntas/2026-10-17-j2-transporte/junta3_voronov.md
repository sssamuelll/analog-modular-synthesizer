# Voronov · lente ontológica · tercera pasada · `papel-v3.md` (commit 4c639f0) · 2026-10-17

**Lectura y alcance.** Leí entero el brief, `papel-v3.md` y mi `junta2_voronov.md`. En `maestro_j2.rs` leí `Evento`, `Accion`, `Ranura` y `Maestro`. En `transporte_j2.rs` leí `tics_de_plazo`, `tics_fusionados`, `Entrada`, `paso` y `declarar_vencida`. En `j2_tic.rs` leí el tic, el planificador, `para_canales`, `escala`, `recupera` y el despachador del nivel 4. De la spec leí D5.4, D7 y §10. Leí también el acta y el H12 de `junta2_halberg.md`.

No ejecuté nada y no escribí en el repo. Los cuatro mecanismos no están construidos, así que juzgo el texto contra el código que van a modificar. Las referencias `papel:N` son líneas de `papel-v3.md`.

## Veredictos

1. **§2.5. La capa no es la correcta.** La política es por ranura y, por construcción, no ve ni el recurso ni el daño que el permiso acota. El permiso se paga con plazos de cualquier causa, y negarlo acaba en el mismo reinicio del chip que la sentencia retirada. `PlazoAjeno` es un hecho del enlace que se etiqueta según la fase de la ranura, no según la causa.
2. **§2.7. Tic, periodo, plazo y µs siguen siendo varios objetos.** La reconstrucción ata `edad`, `espera` y la ventana a la pared solo mientras se cumple R-H2. Fuera de R-H2 adelanta un periodo por cada entrada tardía y no lo devuelve. La entrada sigue siendo la unidad de giros, sello y `muda`.
3. **§2.2. Cada fila tiene dueño, pero las columnas tienen huecos.** `SUCIA` tiene fila en un solo estado de cinco. La limpieza por identidad no tiene fila. `HECHA` es un nivel y no lleva generación.
4. **§2.11 y R-H8. Es política del hub escrita con piezas internas del J2 y con la salud del módulo.** R-H8 contradice a §2.5 en cómo se relacionan las cotas con el reinicio. Frente al acta, la ficha A revoca la nota de «Lo que esta acta no decide», pero no la cláusula firmada de la ficha 2.

## La restricción invisible de esta pasada

**El diseño tiene un solo sustantivo: la ranura.** El controlador (GPDMA1), el reloj y la vida del chip no tienen libro propio, así que cada hecho suyo se escribe en el libro de una ranura. Los cuatro mecanismos nuevos son cuatro traducciones de esa clase:

- el permiso sobre el controlador, en la ventana de salud de la ranura que lo pide (N1);
- el reset del controlador, en seis anillos de eventos (N6) y en seis bits `SUCIA` (N5);
- el tiempo de pared, en el contador de entradas de la ranura (N2);
- la vida del chip, en el sello y la salud de cada ranura (N3, N4).

Cada traducción pierde lo mismo: el sujeto del hecho.

## Hallazgos nuevos

### N1 · ALTA · §2.5: una autoridad local da el permiso sobre un recurso común, y se paga en moneda de salud

**Evidencia**
- papel:149: «la política concede `escalar` mientras la ranura que pide no tenga más de `umbral_escalada` plazos vencidos propios en la ventana de salud».
- `maestro_j2.rs:458-462`: «Cada una con su maquina; ninguna sabe de las otras». Es la independencia de H-1.
- En ese libro entran el error del DMA (`transporte_j2.rs:227-235`), el plazo del cable y el tic tardío, que «sí puntúa en la salud» (papel:171).

**Qué rompe**
- **La capa.** La política no ve el GPDMA1. Tampoco ve el daño que el permiso acota: las tramas de las vecinas, que por diseño no puntúan. El dueño del recurso (R-H3, el transporte) ve las dos cosas y no tiene autoridad. Ninguna capa tiene a la vez la vista y la autoridad.
- **La moneda.** El permiso se gasta con plazos que nunca tocaron el GPDMA.
  - Cuatro tics fuera de presupuesto en un segundo son una falta del hub, y dejan sin permiso a las seis ranuras durante la ventana.
  - Si en ese segundo un canal ignora `SUSP`, no escala. La ranura muere por la cota de `Reiniciando` y el supervisor reinicia el chip.
  - Así, una falta de latencia del hub decide, a través del libro de salud del J2, si una avería del GPDMA se cura o reinicia el instrumento.
  - Con 4 plazos en 1 s la ranura está lejos de `inestable` (10): sana para D7 y sin derecho a curarse.
- **La sentencia cambió de capa, no desapareció.** El papel dice que el permiso «no es una marca de salud ni una salida del lazo», pero la denegación termina en `Muerta` y en el reinicio del chip. Es la consecuencia de la sentencia retirada (V-F5), 12,5 ms más tarde.

**Ley.** Un permiso sobre un recurso compartido que se da miembro por miembro acota a cada miembro; el tope común es la suma.

### N2 · ALTA · §2.7: el reloj reconstruido no está a ±1 periodo; adelanta uno por cada entrada que llega tarde más de medio periodo

**Evidencia**
- papel:165: «suma `max(1, round(Δciclos / ciclos_por_periodo))`». Y también: «sigue a la pared a ±1 periodo, y el error deja de tener un solo signo».
- Δ se mide entre dos entradas (`j2_tic.rs:786-788`). `tics_fusionados` redondea cada Δ por separado (`transporte_j2.rs:51-57`), y v3 convierte ese testigo en el incremento del reloj: «`tics_fusionados` pasa a ser `periodos_saltados`».
- Halberg ya vio el sesgo del testigo: «T7 con δ = 80 µs da `tics_fus` = 1, ningún UEV fundido» (`junta2_halberg.md:179`).

**Qué rompe**
- **La aritmética [A].** Una entrada con retraso L entre 62,5 y 125 µs da Δ = 125 + L, que redondea a 2. La siguiente llega a su hora con Δ = 125 − L, que redondea a 0, y el `max(1, ·)` lo sube a 1. Salen tres periodos por dos de pared.
  - El `max` solo actúa en la entrada que sigue a una tardía, y siempre suma.
  - Como cada Δ se redondea por separado, el error no se compensa después.
  - El error tiene un solo signo (adelanto) y se acumula. Pasa lo mismo con un tic fundido cuyo resto pase de 62,5 µs.
- **Exacto solo donde no hacía falta.** El reloj es exacto mientras el tic cumple R-H2 (entrada en menos de 60 µs). Fuera de R-H2, que es el régimen para el que existe, basta una interferencia periódica que empuje el tic más de medio periodo cada k periodos: el reloj corre 1/k más rápido.
  - Las cotas, los plazos y la ventana de D7.3 se acortan en pared en esa proporción.
  - Las cotas vencen antes, que son los falsos positivos que la ficha C quería quitar.
  - La ventana y el permiso de N1 se renuevan antes.
- **No es un objeto; son cinco:**
  - la entrada: giros, sello y `muda`, que cuenta giros y se asevera en µs (`maestro_j2.rs:120`);
  - el periodo reconstruido: `edad`, `espera` y la ventana;
  - el µs del `DWT`: las cotas;
  - el µs del LSI: `T_IWDG`;
  - el µs del oscilador del módulo: los 50 ms.

  El aserto de las cotas y R-H8(3) comparan entre los tres últimos sin término de tolerancia.

**Ley.** Un reloj hecho de diferencias cuantizadas no tiene un error acotado: suma un error por cada suceso.

### N3 · ALTA · §2.5 contra §2.11 y R-H8(3): las cotas sí retrasan el reinicio, y las cifras citadas salen de un supervisor que R-H8 prohíbe

**Evidencia**
- papel:154: «se rinde la ranura, no el instrumento […] así que alargarla no retrasa ese reinicio».
- papel:199, R-H8(3): la ventana del supervisor es «mayor que el mayor hueco de sello del diseño (Vencida + Reiniciando, 37,5 ms, más el periodo del supervisor)».
- papel:197 cita «62–65 ms» y «no depende de `Muerta` ni de las cotas». En esa simulación el supervisor deja de alimentar a «+7 a +10 ms» (`junta2_halberg.md:230`).

**Qué rompe**
- **El reinicio depende de las cotas.** Con R-H8(3), el reinicio llega a ventana + `T_IWDG` (± P_s) del último sello. Con P_s = 5 ms y los mínimos de R-H8(3), no llega antes de unos 92 ms [A].
  - Cada ms de cota es un ms más de reinicio.
  - Dentro del propio papel, es falso el argumento de la ficha C para pasar `Vencida` de 12,5 a 25 ms.
- **La simulación usa un supervisor prohibido.** El supervisor simulado tiene una ventana de unos P_s. Reiniciaría el chip con una `Vencida` de 10 ms, que cabe en la inanición de 12 ms que permite R-H1. Las cifras de §2.11 describen una cadena que el papel prohíbe.
- **El disparo no es `Muerta`.**
  - R-H8(2) lee el sello o las marcas `inestable` y `muda`; no lee `muerta`.
  - El mismo silencio de sello lo producen `Muerta`, una `Vencida` larga, una `Reiniciando` larga y un planificador retenido.
  - Por eso es falso «el J2 posee la condición del disparo» (papel:197). El J2 posee `Muerta`, y el hub dispara sobre otra cosa.
  - Para el supervisor, `Muerta` solo aporta que el silencio ya no se revoca.

### N4 · ALTA · R-H8(2) y §6 (D7): la salud del módulo entra en el predicado de vida del chip

**Evidencia**
- papel:199: «o las marcas `inestable`/`muda`, porque «armé» solo no ve una ranura que se rearma para siempre».
- papel:288, fila D7: «qué hace el instrumento con una ranura `inestable` o `muda`» «sigue siendo del supervisor».
- spec:350: eso «toca la política de partes y voces […] Aquí las marcas suben, nada más».
- `maestro_j2.rs:312-315`: «un modulo muerto con el MISO en pull-down da EOT perfecto y ceros».

**Qué rompe**
- **Cambia el dueño.** La decisión que D7 dejó a partes y voces pasa al supervisor, y el supervisor tiene una sola respuesta: reiniciar el chip.
- **Bucle de reinicios.** `muda` es un hecho del módulo, no del J2. Un módulo con la identidad I²C viva y el MCU caído o en su cargador da `muda` en 5 ms. El supervisor deja de alimentar, el chip se reinicia y el redescubrimiento encuentra el mismo módulo, que vuelve a dar `muda`. Un solo módulo mete al instrumento en un bucle de reinicios.
- **El desenchufe.** El maestro completa el giro sin esclavo. Quitar un módulo da `SubidaMala` en cada giro y `muda` en 5 ms. Si el descubrimiento I²C no retira la identidad antes de `T_IWDG`, el instrumento se reinicia por quitar un módulo, que es justo lo que §2.2 dice haber eliminado. v3 no escribe la latencia del descubrimiento.
- **Respuesta a la pregunta del brief.** R-H8 es política del hub parametrizada con piezas internas del J2 (la ventana por las cotas, el predicado por el sello al armar) y contaminada con la salud del módulo. Son tres capas en un solo predicado.

### N5 · ALTA · §2.2: `SUCIA` entra en la máquina por un solo estado de cinco, y la corrección de A8 reabre A8

**Evidencia**
- papel:99 es la única fila con `sucia`: «Vencida | sucia (escalada en curso) | espera += periodos; no se lee ni se arma».
- papel:105, la lista de precedencias, no menciona `sucia`.
- papel:108 retira la guarda que había: «Antes el tic saltaba la ranura entera mientras estaba marcada».
- `j2_tic.rs:1085-1105`: `escala()` marca sucias todas las ranuras con `HW` dentro de la sección crítica. Las reprograma y las limpia una a una fuera de ella, donde P2 y P3 pueden interrumpirla.
- `j2_tic.rs:864`: «El canal esta parado (EN = 0), asi que TR1 se puede escribir».

**Qué rompe**
- **Lo que significa `SUCIA`.** Quiere decir «mis canales aún no están reprogramados», y eso puede ser cierto en `Libre`, en `Vencida` y en `Reiniciando`. La tabla solo lo define en `Vencida`.
- **`Libre` + `sucia` + bajada fresca: la tabla dice `Armar`.**
  - La recuperación (P4) solo corre después del planificador (P3), y `compone()` llena todo buzón vacío. Por eso, cuando empieza la escalada, toda ranura `Libre` con identidad ya tiene su bajada.
  - Cualquier tic que caiga dentro del bucle de `escala()` arma esa ranura sobre canales que el reset por RCC dejó a cero. Una retención de P2 en ese bucle, que es el escenario A8, estira la ventana a milisegundos.
  - `arma()` solo escribe `BR1`, la dirección y `CR.EN` (§2.3).
  - Después `programa()` escribe `TR1` con `EN = 1`, contra lo que el código mismo supone.
- **`Reiniciando` + `sucia`.** Si había un `HECHA` publicado justo antes de la escalada, la precedencia «reinicio_hecho gana» devuelve la ranura a `Libre` y la arma con el controlador en el mismo estado.
- **La prueba no lo alcanza.** §5.2(i) pide probar `SUCIA` en `Transporte`. Lo que la vuelve peligrosa es la escritura de `escala()`, que está fuera del modelo.

### N6 · MEDIA · §2.5: `PlazoAjeno` es un hecho del controlador anotado como suceso de ranura, y la etiqueta la decide la fase, no la causa

**Evidencia**
- papel:151: la escalada «declara vencidas a las ranuras `Armada` […] emitiendo `Evento::PlazoAjeno` […] y no lo anota en la ventana de salud».
- `transporte_j2.rs:282-289`: solo se declara la ranura `Armada`; una `Vencida` ya puntuó.
- papel:152: «si no la cura, el permiso se agota a la tercera». papel:188: «≤ 3 seguidas por ranura que la pide».

**Qué rompe**
- **Un fallo, seis efectos.** La división entre propio y ajeno es la fase de cada ranura en el instante de la sección crítica.
  - La ranura que venció un tic antes puntúa y gasta permiso.
  - La que seguía `Armada` con el mismo canal colgado queda absuelta.
  - Es una carrera entre el plazo del nivel 1 y los 25 µs de `para_canales` del nivel 4.
- **El tope rota [inferido].** Con una avería común que el reset no cura y una ranura que va por delante:
  - la primera paga tres escaladas y pierde el permiso;
  - las demás, absueltas, llegan a su plazo propio con el permiso entero, y la escalada pasa a la siguiente;
  - el tope común es 6 × 3 = 18 por ventana, no 3;
  - cada vecina puede perder hasta 15 tramas, no 3. §2.10 cuenta por la ranura que pide, no por la que sufre.
- **Respuesta a la pregunta del brief.** `PlazoAjeno` es un hecho del enlace. Como suceso de ranura no tiene sujeto: la ranura que lo recibe no lo causó, y la que lo causó lo registra con otro nombre.

### N7 · MEDIA · §2.2: la limpieza por identidad tiene quien la pide, pero no tiene fila ni generación

**Evidencia**
- papel:111: la limpieza «la pide el planificador cuando la política pasa a `Vacia` con una transferencia en vuelo o vencida».
- papel:112 dice que el reinicio tras una escalada ajena va por «el mismo camino». En cambio, en papel:151 ese reinicio lo «manda» la política.
- papel:145, `j2_tic.rs:822-832` y `913-918`: `HECHA` solo se lee y se borra en `Vencida` y `Reiniciando`.
- `j2_tic.rs:1001`: «La politica es la unica autoridad sobre «reiniciar»».

**Qué rompe**
- **Tres peticionarios para un solo bit (`REC_PEDIDA`):**
  - la política, por salud;
  - la limpieza tras escalada ajena, que según el papel pide la política o el planificador (dice las dos cosas);
  - el planificador, por identidad y fuera de la política.

  El `escalar` de la limpieza por identidad no está definido: es una salida de la política, y esa limpieza no pasa por ella.
- **Un `HECHA` rancio.** La tabla no tiene fila para una limpieza desde `Armada` ni desde `Libre`.
  - El maestro completa sin esclavo, así que lo normal es que la ranura pedida en `Armada` ya esté en `Libre` cuando corre la recuperación. Su `HECHA` queda publicado y nadie lo borra.
  - Cuando vuelve el módulo, la primera `Vencida` lee ese `HECHA` y, como «reinicio_hecho gana», vuelve a `Libre` sin su recuperación.
  - El `Reiniciar` de ese incidente corre después, sobre lo que el tic haya vuelto a armar.
- **Mismo mecanismo, dos efectos.** Como `HECHA` es un nivel y no una generación, la limpieza desde `Armada` funciona: el bit espera a que la ranura caiga en `Vencida`. Ese mismo rasgo deja el bit rancio cuando la limpieza parte de `Libre`.
- **Reinicio al enchufar.** El papel dice que `Muerta` no tiene salida y que una ranura `Muerta` sin identidad no cuenta para el supervisor. Si una ranura muere sin identidad, el siguiente módulo que se conecte ahí la vuelve `Activa`; la ranura no sella y el supervisor reinicia el chip. §2.2 quita el reinicio por desenchufar y deja uno diferido al enchufar.

### N8 · MEDIA · §2.5: la denegación necesita un reloj que nadie posee

**Evidencia**
- papel:150: «no publica `HECHA`, reintenta parar cada tic […] ninguna transición nueva ni escritor nuevo».
- `j2_tic.rs:1165-1168`: el nivel 4 solo corre `recupera(n)` si `REC_PEDIDA` está puesto.
- `j2_tic.rs:1002-1008`: `REC_PEDIDA` solo lo pone el planificador ante `Accion::Reiniciar`, que solo nace de `PlazoVencido`.
- papel:101-102: `Reiniciando` no emite eventos.

**Qué rompe**
- **«Cada tic» exige una de dos cosas, y las dos fallan.**
  - Un escritor nuevo que vuelva a pedir el nivel 4 en cada tic (el tic o el planificador, leyendo `Reiniciando`). Eso contradice «ningún escritor nuevo».
  - Un bucle dentro de `recupera(n)` de hasta 12,5 ms. Eso serializa el nivel 4: cualquier otra recuperación espera detrás.
- **El coste.** A 25 µs de `T_CANAL` (E) por intento cada 125 µs, una ranura denegada gasta unos 20 % de un núcleo durante 12,5 ms [A]. No está en ninguna fila de §3.
- **La parada vive en otro nivel.** La condición de parada (la cota que lleva a `Muerta`) está en el nivel 1, y quien reintenta está en el nivel 4. La regla de H5 («un reinicio sobre una `Muerta` no se hace») se vuelve una lectura entre niveles dentro del bucle.
- **«Se cura solo» queda sin respaldo.** La frase «un bloqueo transitorio del bus que acabe antes de esa cota se cura solo» depende de un reintentador que no tiene dueño.

## Hallazgos de la segunda pasada que no quedaron resueltos

- **V-F1.** No resuelto. §2.7 cambia el signo del sesgo y lo vuelve acumulativo (N2). La entrada sigue siendo la unidad de giros, sello y `muda`.
- **V-F2.** Resuelto para las cotas. Queda la ficha E, que costea los 16 kHz con «100 tics serían 6,25 ms», una unidad que la ficha C acaba de abolir. Y `umbral_muda` sigue en giros.
- **V-F3.** A medias. La causa ajena quedó separada. Error del DMA, cable y tic tardío siguen en un solo evento, y ese evento es ahora la moneda del permiso (N1).
- **V-F5.** Desplazado, no resuelto. La sentencia pasó del actuador a la política, pero la denegación sigue acabando en `Muerta` y en el reinicio del chip, y partes y voces sigue sin ser consultada (N1, N4).
- **V-F6.** Transformado. La unidad contada pasó de escaladas a plazos propios, que tampoco es la que se protege. El tope por ranura hace el tope común seis veces mayor (N1, N6).
- **V-F7.** A medias. §2.1 nombra los ocho elementos, pero `SUCIA` entra por un solo estado (N5). El protocolo de la recuperación sigue fuera del modelo, ahora con tres peticionarios (N7).
- **V-F8.** El dueño ya tiene nombre (R-H8, §5.2 g), pero el requisito contradice a §2.5 y mete la salud del módulo en la vida del chip (N3, N4).
- **V-F11.** A medias. La ficha A revoca la nota de «Lo que esta acta no decide», pero no la cláusula firmada de la ficha 2: «el transporte se decide cuando haya una tabla de CPU del resto del hub» (acta:12). Además, la hoja «≥ 48 %» del árbol reabre la decisión que la ficha dice revocar.

## Comprobado y en pie

- **V-F4.** Resuelto. §6 D5.1(1) dice «se acota y no se elimina». §4.1 admite que la prueba de H-1 no puede fallar, y §5.2(h) pide el modelo con el acoplamiento.
- **V-F9.** Resuelto. `Cuentas` gana `muerta`, `plazos_ajenos`, `escaladas` y `tics_fuera_de_presupuesto`, y desaparece `atrasos`.
- **V-F10.** Resuelto. §2.7 y §6 enmiendan R-C8 en la cadencia y en el hueco tras recuperar. La ficha D da el argumento fuerte: el sello como testigo del planificador.
- **V-F12.** Resuelto en la forma: R-H6 con la tabla de obligaciones de tiempo y §5.2(k). Que el censo siga sin cifras está dicho.
- **§2.4.** `tics_de_plazo(126, 125)` da 2 por `div_ceil` (`transporte_j2.rs:35-44`); la corrección del `TONO` es correcta.
- **«Las ranuras `Armada`» de §2.5.** Es fiel al código: `declarar_vencida` solo actúa sobre `Armada` (`transporte_j2.rs:282-289`).
- **`Muerta`.** Es absorbente frente a un `HECHA` tardío (`transporte_j2.rs:223`, `689-709`), así que la precedencia «hecho gana a la cota» no la contradice.
- **§2.1.** Los ocho elementos que nombra son exactamente los estáticos de `j2_tic.rs:394-411`.
- **`Umbrales::nuevos`.** Ya es el sitio de los asertos (`maestro_j2.rs:110-131`); `umbral_escalada < umbral_inestable` tiene dónde vivir.
- **`PlazoAjeno` con una sola ranura en falla.** Dejarlo fuera de la ventana sí restituye la frase de H-1 en la contabilidad.

## Lo que no verifiqué

- No ejecuté nada ni abrí el simulador de Halberg.
- No leí el RM0486. El estado de los canales tras el reset por RCC y el efecto de escribir `TR1` con `EN = 1` son lo que supone el código (`j2_tic.rs:864`), no lecturas mías.
- No encontré la latencia del descubrimiento I²C ni la tolerancia del LSI del N657 en lo que leí. N4 y N2 las tratan como ausentes, no como valores.
- Lo marcado [inferido] es razonamiento sobre el código, no un hecho observado.

## Cierre

Ninguno de los cuatro mecanismos está mal hecho dentro de su capa. Los cuatro están mal ubicados, y en la misma dirección: hacia la ranura, porque es lo único que el diseño sabe nombrar. El controlador no tiene libro, el reloj no tiene libro y la vida del chip tampoco. Cada corrección de la junta se tradujo a la ranura, y cada traducción perdió el sujeto del hecho que traducía.

El papel ya no tiene un problema de mecanismos. Le faltan sustantivos.

Archivos citados, todos bajo `D:\Desktop\projects\sam17\.claude\worktrees\papel-v3`:
- `docs\superpowers\juntas\2026-10-17-j2-transporte\papel-v3.md`
- `docs\superpowers\juntas\2026-10-17-j2-transporte\junta3-brief.md`
- `docs\superpowers\juntas\2026-10-17-j2-transporte\junta2_voronov.md`
- `docs\superpowers\juntas\2026-10-17-j2-transporte\junta2_halberg.md`
- `docs\superpowers\juntas\2026-10-17-j2-transporte\acta-2026-10-17.md`
- `docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md`
- `software\nucleo\core\src\maestro_j2.rs`
- `software\nucleo\core\src\transporte_j2.rs`
- `software\nucleo\fw\src\j2_tic.rs`
