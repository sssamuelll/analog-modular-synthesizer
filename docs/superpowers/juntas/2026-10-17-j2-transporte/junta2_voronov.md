# Voronov · lente ontológica · segunda pasada · `papel-v3.md` · 2026-10-17

*Informe de la segunda pasada sobre el `papel-v3.md` anterior a la absorción (commit `72d6e6f`). Texto del informe tal como lo entregó la lente.*

**Lectura y alcance.** Leí el brief, `papel-v3.md` y mi `junta_voronov.md` enteros. Leí también `acta-2026-10-17.md`, la spec firmada (D3, D4, D5, D7, §10), `transporte_j2.rs` con sus pruebas, `buzones_j2.rs`, `maestro_j2.rs`, `j2_tic.rs` (tic, planificador, recuperación y escalada), `carga_hub_budget.py`, EN-PLACA «El transporte por tic» y `junta_halberg_codigo.md`. Por búsqueda miré `junta_halberg.md` y `papel-v2.md`. No ejecuté nada ni escribí en el repo. Las referencias a v3 van por sección y las del código por `archivo:línea`.

No hay BLOCKER para firmar el diseño como candidato. Hay dos textos que no deben llegar a la firma tal como están: una frase de la ficha A y el presupuesto de la ficha B.

## Veredictos

1. **Tic, periodo, plazo.** Son tres objetos con un nombre: el escalón de la rejilla de TIM7, la entrada de la ISR y los 125 µs de la prosa. La máquina, la política y las cotas cuentan entradas. El módulo y el IWDG miden pared. La identidad entre ambos solo es cierta mientras el tic es isócrono, y esa hipótesis es la única de v3 que se mide y no se usa. El plazo cambió de especie: dejó de ser una cota del cable (D3) y es una cota de pasos del observador.
2. **Escalada.** El presupuesto la limita y no la arregla. La capa es correcta para contar y equivocada para sentenciar. El sujeto de la pena (quien pide la cuarta) no es el sujeto de la cuenta (el controlador). La unidad contada (escaladas) no es la protegida (averías).
3. **Dueños.** R-C8 sobrevive solo como autoría de contenido. La autoridad sobre el tiempo del enlace quedó repartida por verbo. «`Muerta` ⇒ IWDG» es política del hub ejecutada con un disparador del J2, y el hub no la ha escrito. No figura en R-H1 a R-H7 ni en §5.
4. **Censo.** «El censo decide el presupuesto, no el transporte» es un argumento, pero de dominancia en una sola moneda. Ordena bien ejecutor y tic en ciclos, y no autoriza la conclusión de separabilidad. Además contradice una frase firmada del acta sin decirlo. El censo no tiene columnas para lo que v3 le exige al hub.

## La restricción invisible de v3

**Isocronía.** Cada garantía de v3 está escrita en tics y se justifica en milisegundos. Las cotas (12,5 ms), la ventana de salud (1 s), el tope (8 000 tics), el plazo (N tics) y los 60 µs valen solo si una entrada de TIM7 equivale a 125 µs de pared. Es la clausura de la primera pasada expresada en unidades. El hub abierto entra en el J2 por el único canal que el diseño mide sin que nada dependa de la medida: el reloj.

- **Dónde v3 la reconoce.**
  - §0.3 (`Reloj64`).
  - §2.8: `retraso_max_us` se lee de `TIM7.CNT` al entrar (`j2_tic.rs:775`). Es la referencia al plan que la primera pasada exigía.
  - §1: «requisitos que este diseño exige y que hoy no están escritos».
  - §3: «Lo que la cifra no incluye».
  - §7: los números ESTIMADO que quedan.
- **Dónde la rodea.**
  - Ficha A: «El censo decide el *presupuesto*; no decide el *transporte*».
  - §2.8: «Un atraso no mueve `inestable` ni `muda`».
  - §2.8: «Lo que lo rompe no es el nivel 1…».
  - §5.4: «No bloquea el transporte».

## Hallazgos

### F1 · ALTA · «Un tic» designa tres objetos y el papel convierte entre ellos sin condición
- **Evidencia.**
  - `TICS` sube uno por entrada de la ISR (`j2_tic.rs:790-793`).
  - La política recibe `tics × PERIODO_US` (`j2_tic.rs:964-965`).
  - `edad`, `espera` y las cotas cuentan llamadas a `paso` (`transporte_j2.rs:225-275`).
  - El código lo declara: «el plazo y la rejilla son el mismo reloj» (`transporte_j2.rs:15-16`).
  - TIM7 funde dos actualizaciones en un pendiente (`transporte_j2.rs:46-50`).
  - v3 mide la diferencia (`tics_fusionados`, `j2_tic.rs:784-789`) y la descarta.
- **Qué lo rompe.**
  - Cualquier tic fundido o tardío atrasa a la vez las cotas, la ventana de D7.3, la ventana del presupuesto y la detección de plazo.
  - `ahora_us` queda n×125 µs por detrás de la pared sin recuperarse.
  - El error tiene un solo signo: ninguna fuente adelanta el conteo. Todo protector actúa tarde, justo cuando el sistema está más cargado.
  - La región donde tic ≠ periodo no tiene una sola medida. `retraso_max_us` fue 0 y los fundidos fueron 0 en las corridas (EN-PLACA.md:848). Los 12 y 14 ms de `tic_cota` se midieron contra una retención de P2, que no toca al tic (P1) (EN-PLACA.md:866).
  - El IWDG es de pared y no hereda el sesgo. Es la única red independiente del conteo, y es la que no está escrita (F8).
- **Ley.** Un contador de sucesos es un reloj solo mientras el suceso es isócrono. Si la isocronía es hipótesis, el sistema debe declarar qué hace fuera de ella.

### F2 · MEDIA · Las cotas llevan su unidad en la prosa y no en el tipo
- **Evidencia.**
  - `COTA_VENCIDA_TICS` y `COTA_REINICIANDO_TICS` solo aparecen en `transporte_j2.rs`. Ni `recuperacion_j2_budget.py` ni `Umbrales::nuevos` las leen.
  - La desigualdad que las justifica es un comentario: «Las dos cotas suman 25 ms, la mitad de lo que el modulo aguanta» (`transporte_j2.rs:27-29`).
  - Su hermana de `muda` sí está sellada: `umbral_muda * PERIODO_GIRO_US >= T_WATCHDOG_TRAMA_US` rechaza en construcción (`maestro_j2.rs:120`).
  - `lanzar` acepta cualquier `periodo_us ≥ 125` (`j2_tic.rs:641-645`) y `Transporte::nuevo()` fija 100/100.
- **Qué lo rompe.**
  - Con `tic_banco --features mil-hz` (1 ms, corrida citada en EN-PLACA.md:848) las cotas suman 200 ms, cuatro veces los ~50 ms del módulo.
  - La alternativa de la ficha D, un tic a 16 kHz, deja 100 tics en 6,25 ms. Eso es menos que los 12 ms de R-H1, y la ficha no lo cuenta como costo.
  - Todo lo denominado en tics (100, 100, 8 000, los N de plazo, los 60 µs) se re-deriva con el periodo, y nada lo impide ni lo avisa.

### F3 · ALTA · `PlazoVencido` cambió de especie y perdió la causa
- **Evidencia.** Un solo evento nombra cuatro causas:
  1. El plazo venció en el cable.
  2. El tic que armó llegó tarde y el que mira llegó a su hora: «todas las ranuras armadas en ese tic vencen a la vez» (§2.8).
  3. Un error del DMA (fila 2 de §2.2, `transporte_j2.rs:227-235`).
  4. La escalada de otra ranura (`declarar_vencida`, `transporte_j2.rs:282-289`).

  - La política las cuenta igual (`maestro_j2.rs:375-379`: suma, anota en la ventana y devuelve `Reiniciar`). §6 dice «D7 igual».
  - La información que separa la causa 2 existe en el instante del juicio: `retraso` se lee en `j2_tic.rs:775` y no es campo de `Entrada` (`transporte_j2.rs:116-127`).
  - Halberg pidió «una decisión de la junta sobre cómo cuenta la política (D7)» la transferencia que mató una escalada ajena. v3 respondió «La política no cambia» (§2.5) y registró H4 como resuelto con el presupuesto (§8).
- **Qué lo rompe.**
  - La regla del 16-10 («Un atraso es un fallo del presupuesto de CPU, no del módulo») es inalcanzable por construcción. Un tic tarde produce seis `PlazoVencido` en seis ventanas de salud. D7 queda «igual» en el código y distinta en su dominio de entrada.
  - Los 60 µs de §2.8 son el residuo del plazo de D3 y no un requisito independiente. D3 reservaba la latencia de la ISR dentro de `FACTOR_PLAZO`. Al redondear el plazo a la rejilla, esa holgura (84/98/64 µs) pasa a pagar el jitter del tic. La misma latencia se cuenta en dos libros.
- **Ley.** Una interfaz con la misma firma y otra distribución de entrada no es la misma interfaz.

### F4 · ALTA · La escalada: el presupuesto la acota y no la arregla, y lo que cruza es más ancho que «una transferencia»
- **Evidencia.**
  - H-1 está escrito en `core` con su cláusula de contabilidad: «un cuelgue en una no ensucie la ventana de las demas» (`maestro_j2.rs:460-462`; spec D5.1 punto 1).
  - `escala()` inserta un `PlazoVencido` en el anillo de cada vecina (`j2_tic.rs:1088-1092`).
  - Medido: «10 plazos vencidos en cada una de las tres ranuras» en 10 escaladas (EN-PLACA.md:850). §4.2 lo lista como resultado de una prueba que pasa («30 plazos»).
  - «En vuelo» para `declarar_vencida` es `Armada`. La ranura está `Armada` todo el periodo, porque se cierra y se rearma en el mismo tic. El cable está ocupado 35 a 60 µs de 125 (§2.6). Cada escalada alcanza a todo vecino con bajada, incluidas tramas ya completas en el cable.
  - La prueba de H-1 del host no puede fallar. `seis_ranuras_son_independientes` compara seis valores `Transporte` independientes (`transporte_j2.rs:953-980`). El acoplamiento vive en `fw::escala()`, fuera del modelo. Las dos propiedades al azar corren con `con_cotas(2, 4)` y sin `declarar_vencida` (`transporte_j2.rs:910, 934`).
- **Qué lo rompe.** Nada en v3 vuelve cierta la frase de H-1. La spec ya aceptó el cruce el 18-09 (D4.2), así que v3 lo hereda y lo raciona. Pero «independientes salvo ≤ 3 por segundo» es otra afirmación. La independencia es propiedad del dominio de fallo: un GPDMA1 con doce canales de seis ranuras, asignado entero al J2 por R-H3. No lo es de la frecuencia.
- **Ley.** Un dominio de fallo compartido hace condicional la independencia de sus miembros. Un tope cambia la condición y deja la dependencia.

### F5 · ALTA · La sentencia está en la capa que ejecuta, con el sujeto equivocado y la consecuencia mayor del sistema
- **Evidencia.**
  - Contar escaladas le toca a quien posee el recurso, y v3 acierta ahí (R-H3). La sentencia no: «no escala: da por muerta a la ranura que la pide» (§2.5) es una decisión de salud tomada por el actuador.
  - La política es «la única autoridad sobre reiniciar» (`j2_tic.rs:999`) y devuelve `Reiniciar` siempre que la ranura está activa (`maestro_j2.rs:375-379`). La autoridad nunca dice no. Si es telemetría por decreto, la etiqueta es vacía. El único condicional vive en el mecanismo.
  - El contador se decidió «no en la política»: spec D4.2, enmienda del 18-09, «Se cuenta aparte (`escaladas_gpdma`, en `fw`, no en la política)». Era telemetría y pasa a ser disparador de `Muerta` sin cambiar de sitio.
  - La forma de la regla (muchos reinicios, luego la ranura sale del lazo) es la de la v1 de D7, que «la junta lo tumbó cuatro veces». D7.1: «El planificador gira a 8 kHz por toda ranura activa, siempre». D7: «Aquí las marcas suben, nada más».
  - La consecuencia es la mayor del sistema. `Muerta` lleva al IWDG y reinicia el chip. Los demás módulos, sanos, callan el tiempo de arranque (HUECO S-10 del hub). D5.4 justifica `T_IWDG > 50 ms` «para que… el reinicio no añada silencio». Eso vale para el silencio total, no para una ranura mala entre buenas.
  - El evento nunca se ha observado: «La rama que escala porque un canal no para en 25 µs no ha corrido» (EN-PLACA.md:850; §7). La constante 3 se deriva de otra ESTIMADO (10 por 1 s) sobre una tasa base desconocida, posiblemente cero.
- **Qué lo rompe.**
  - Sin presupuesto, el peor caso ya lo acota D7.2 (un reinicio por giro por ranura). Si la CPU no alcanza, lo acota la red del 16-10: hilo hambriento, sin alimentar el IWDG, reinicio. Por eso «sin que nada diga basta» (ficha B) es inexacto.
  - Con presupuesto, la parada llega al cuarto pedido en un segundo. Es una elección entre degradar y reiniciar un instrumento en vivo. D7 se la delegó a «partes y voces» (política de otro papel), y v3 la decide en el actuador sin nombrarla como elección.
  - Ficha B presenta la primera opción como el riesgo que la segunda previene. Son dos fallos distintos.

### F6 · MEDIA · La unidad que se cuenta no es la que se protege, y v3 describe dos mundos
- **Evidencia.**
  - §2.5: «Una avería que toca varias ranuras a la vez produce **una** escalada». Lo verifiqué en el código: tras el reset, las demás recuperaciones ven `suspf() || idlef()` y no escalan (`j2_tic.rs:1046-1050`).
  - Ficha B, costo del tope de 1: una avería multi-ranura «se llevaría la ranura por una sola escalada legítima».
- **Qué lo rompe.**
  - Si lo primero es cierto, un tope de 1 no mata nada en ese evento y la ficha no tiene argumento para 3 sobre 1.
  - Si lo segundo, §2.5 es falso y un evento multi-ranura puede costar hasta tres escaladas, justo el tope [inferido: ocurre si la causa común sobrevive al reset].
  - El presupuesto cuenta actos y protege contra averías. La razón actos/avería no está medida ni es uniforme.
  - Halberg pidió el presupuesto «por ranura»; v3 lo hizo global, y §8 no lo dice.

### F7 · MEDIA · La máquina pura no es el estado de la ranura
- **Evidencia.**
  - §2.1 lo admite en una cláusula: el estado lo escribe el tic «salvo `ReinicioHecho` y la marca de escalada».
  - En el código, el estado de control de una ranura son ocho estáticos con escritores en los niveles 1, 3 y 4: `Transporte`, `REC_PEDIDA`, `REC_EN_CURSO`, `REC_HECHA`, `REC_T_HECHA`, `SUCIA`, el buzón e `IDENTIDAD` (`j2_tic.rs:384-409`).
  - `SUCIA` es un estado de espera fuera de la máquina. Con él puesto el tic hace `continue` y no llama a `paso` (`j2_tic.rs:801-803`). `Vencida{espera}` no avanza, y la frase «Todo estado de espera tiene una cota en tics» (§2.2) es falsa de él. Su ventana es el bucle `programa()` de `escala()` (`j2_tic.rs:1097-1103`), expuesto a P2 y P3.
  - `Transporte` tiene dos puertas (`paso`, `declarar_vencida`). La sentencia del presupuesto necesita una tercera o ejecutarse por omisión, y §2.5 no dice cuál.
- **Qué lo rompe.**
  - Los tres caminos dan silencios distintos y la contabilidad de ~50 ms depende de cuál se elija:
    - escribir `Muerta` desde el nivel 4: inmediato;
    - no publicar `HECHA` y dejar vencer la cota: hasta 12,5 ms más, sin escalar;
    - una marca que lee el tic: otro estático.
  - Los modelos de Halberg con dos ranuras sí cubrieron el protocolo lateral (§4.1). Lo que falla es el enunciado «pura y probada», no la prueba.

### F8 · ALTA · «`Muerta` ⇒ el IWDG reinicia el chip» no tiene dueño
- **Evidencia.**
  - Spec D5.4: «Este papel **no decide** quién alimenta el IWDG ni con qué plazo». El J2 aporta un sello. El supervisor (#291) figura «pendiente» en §10, con dos parches mandados y sin aplicar. El segundo dice: «El sello no puede ser «armé»» (spec líneas 588, 616, 619).
  - v2 §6 mandaba las filas del hub («los ejecutores», supervisor) a R-H1 a R-H6. v3 §6 las manda a R-H1 a R-H7. Ninguna R-H es el supervisor y v3 no cita #291.
  - El sello sube al armar (`j2_tic.rs:888`) y armar exige bajada fresca (`transporte_j2.rs:189-203`). «Sin sello» confunde cuatro causas: tic parado, planificador retenido, ranura en recuperación y `Muerta`. D5.4 decía «una ranura reiniciando también está viva». En v3 una ranura reiniciando no sella hasta 25 ms.
  - En el banco no hay supervisor. Lo ejercido es «deja de sellar (el sello del IWDG se queda quieto)» (EN-PLACA.md:850). §5.2 no exige que exista ni que se pruebe con una `Muerta` real.
- **Qué lo rompe.**
  - El estado terminal del argumento de seguridad del J2 (cotas, presupuesto, retenciones de P2) es una frase cuyo verificador no está escrito.
  - Si el hub no la escribe, `Muerta` es una muerte silenciosa con las marcas sanas (F9).
  - Respuesta a «¿J2 o hub?»: el J2 posee las condiciones del disparo y el hub posee el efecto. El mapeo entre ambos no lo posee nadie.
- **Ley.** Una red de seguridad que no tiene quien la escriba convierte en hipótesis todo estado terminal que dependa de ella.

### F9 · MEDIA · La muerte y el atraso no llegan al contrato del instrumento
- **Evidencia.**
  - `Cuentas`, lo que lee la pantalla, no tiene campo `muerta` (`j2_ejecutor.rs:146-157`).
  - La política sigue `Activa` y recibe `Tick` (`j2_tic.rs:1014-1016`). `inestable` decae a sano al deslizar la ventana.
  - `muertas`, `recuperaciones`, `escaladas_gpdma` y `tics_fusionados` viven en `Testigos`, la vista del banco (`j2_tic.rs:484-498`).
  - `atrasos` se publica con el literal `0` (`j2_tic.rs:1018`). Su documentación es «Cero en un instrumento sano» (`j2_ejecutor.rs:152-154`). Con `Calendario` derogado (§2.9) el campo es una constante.
- **Qué lo rompe.**
  - Hay dos libros de salud sin traductor: las marcas de la política (D7, «suben al instrumento») y los testigos del transporte (solo banco).
  - La frase del 16-10 («lo dice un contador») ahora la dice un contador que no sale del banco. «Partes y voces» no puede decidir sobre lo que no se publica.

### F10 · MEDIA · R-C8 sobrevive como autoría de contenido; la autoridad sobre el tiempo del enlace no la tiene nadie
- **Evidencia.**
  - D5.1 punto 2 ya definió el escritor como quien «decide qué baja» y dijo que las tareas «no deciden nada del protocolo». v3 es fiel a eso: el tic no compone.
  - Pero R-C8 dice tres cosas (cabecera:803-806): un solo escritor, cambio y refresco del mismo estado, y «`T_GAP` lo pone él». D3 asigna al planificador «el T_GAP entre mensajes y la cadencia del giro».
  - En v3 la cadencia es la rejilla de TIM7 (del transporte). El hueco tras recuperar lo impone el tic con `DWT` (`j2_tic.rs:826`). Ninguna fila de §6 enmienda esas dos frases.
  - Los verbos de la ranura quedan en tres dueños: arma (nivel 1), compone y juzga (nivel 3), reinicia y escala (nivel 4). Además sentencia (cotas en el nivel 1, presupuesto en el 4) y sella (nivel 1). En D5.1 una tarea los tenía todos en secuencia.
  - R-C8 asigna autoridad por objeto y v3 la reparte por verbo. El verbo que fija el tiempo del enlace no es el del planificador.
- **Qué lo rompe.** La ficha C acierta en «Nada», pero el motivo escrito («segundo escritor de la `secuencia`») es el débil. El fuerte no está en el papel:
  - Con «Nada» solo se arma lo que el planificador compuso, así que el sello es testigo del planificador.
  - Un relleno del tic haría del sello testigo del portador, y alimentaría el watchdog de trama del módulo (~50 ms).
  - Quedarían ciegos a la vez los dos testigos independientes de que el planificador vive.

### F11 · ALTA · «El censo decide el presupuesto, no el transporte» contradice el acta y su conclusión exige un pronóstico
- **Evidencia.**
  - Acta, «Lo que esta acta no decide»: «Si el transporte cambia o no. Eso lo decide el censo del hub junto con las medidas del prototipo». Ficha 2: «el transporte se decide cuando haya una tabla de CPU del resto del hub y medidas de los dos transportes».
  - v3 pide firmar la frase opuesta (ficha A) y la implementa en §5.4: «No bloquea el transporte; bloquea saber si 12,6 a 13,9 % cabe». El papel no dice que revoca esa frase del acta.
  - Es un argumento: 48 % contra 11,8 a 16,7 % es una desigualdad medida (8 000 contra 1 967 a 2 778 ciclos). Pero la separabilidad exige que no exista resultado del censo en que el ejecutor quepa, es decir, que ningún reparto dé al J2 cerca de media CPU.
  - Esa es una predicción sobre un censo de once filas sin cifra (`carga_hub_budget.py:101-118`). Tiene el mismo estatus que el 15 % que la ficha 2 volvió provisional, aplicado al otro extremo.
- **Qué lo rompe.**
  - Existe un resultado del censo (J2 con cerca del 50 % o más) que revierte la decisión.
  - Falta la tercera hoja del árbol: el censo da al J2 menos de 12,6 %. §5.4 admite que no se sabe si cabe, y ninguna ficha dice qué se hace si ni el ejecutor ni el tic caben.
  - Samuel firmaría la reversión de su propia frase sin que la ficha se lo diga.

### F12 · ALTA · El censo no tiene las columnas de lo que v3 exporta
- **Evidencia.**
  - `Fila` es `(nombre, dueño, estado, ciclos_por_s)` (`carga_hub_budget.py:59-65`): una cifra media por consumidor. La puerta solo falla por exceso de suma (`veredicto`, línea 78).
  - v3 compra CPU con obligaciones de otra moneda:
    - P2 ≤ 12 ms (≤ 1 ms pedido), R-H1;
    - máscara ≤ 5 µs y entrada del tic < 60 µs, R-H2;
    - texto y estáticos en RAM, R-H4;
    - D-cache sin vaciar entera entre tics: +41 %, 1 967 a 2 778 (§3);
    - arnés, R-H7.

    Ninguna cabe en una fila de ciclos por segundo.
  - Las R-H son obligaciones para un hub sin escribir. Los únicos hechos importados son de la hoja de reloj (800 MHz, `pclk2` 100 MHz, R-H5). Ninguno es de comportamiento: retenciones, máscara, huella de caché.
  - Los números se derivan al revés de la dependencia. R-H1 (12 ms) sale de la cota que se midió (100 tics) y no de una ISR de P2 censada. La cota y R-H1 se definen mutuamente (§0.2, §2.5, R-H1).
  - §2.8 excluye por decreto los niveles por encima del tic. Hoy están ocupados: el USB de embassy queda en el reset del NVIC, nivel 0, «por encima del tic» (`junta_halberg.md:96`; v2 R-H1), y el muestreo del banco usa P0 (`muestreo.rs:151`).
- **Qué lo rompe.** El censo puede salir verde en ciclos y el instrumento reiniciarse por una ISR de pantalla de 15 ms. El censo es condición necesaria, y v3 lo presenta como lo único pendiente y como asunto de otra decisión.

## Las fichas (qué falta y qué contestaría distinto)

- **A.** Contestaría «Sí, como candidato, con D5.1 en vigor». No firmaría la frase «el censo no decide el transporte»: contradice el acta (F11).
  - Su recomendación descansa en un supuesto no declarado: que el censo no puede dar al J2 la mitad de una CPU.
  - Falta la tercera hoja: ni el ejecutor ni el tic caben.
  - Falta decir qué frase del acta se revoca.
- **B.** Contestaría distinto, y es la ficha que más cambia. Son dos decisiones en una.
  - Las cotas de 100 y 100: sí, con su relación a la unidad dicha (F2). Están medidas y su necesidad es real.
  - El presupuesto: no tal como está (F4, F5, F6). Es una sentencia fatal, no construida, para un evento no observado, con un 3 derivado de otra ESTIMADO.
  - Faltan opciones: contar sin sentenciar (una marca, como manda D7, sin `Muerta`); el tope por ranura que pidió Halberg; y decidir antes cómo cuenta la política la transferencia que mató una escalada ajena.
  - Los costos de las otras opciones están mal contados: «sin presupuesto» ignora D7.2 y la red del 16-10, y el costo del tope de 1 contradice §2.5.
- **C.** «Nada»: de acuerdo, por la razón de F10 y no por la escrita.
- **D.** Sin objeción ontológica. Debe contarse como costo de la opción de 16 kHz que re-deriva todas las constantes en tics (F2).
- **E.** Sin objeción.
- **F.** Contestaría distinto: faltan condiciones del lado del hub. Hoy §5.2 vuelve a verificar el transporte aislado, que es la clausura otra vez.
  - Que el supervisor de vitalidad exista y se haya ejercitado con una `Muerta` real (F8).
  - Que el retraso del tic se mida con los residentes del hub en todos los niveles por encima y con sus máscaras reales (F12).
  - Que la retención máxima de P2 se mida contra R-H1.

## Puntos de presión

1. **El primer tic fundido en campo** (sonda, `defmt`, caché fría de la XSPI). Las cotas, la política y el tope van tarde, ninguna marca lo dice y la pantalla lee `atrasos = 0` (F1, F9).
2. **La primera escalada real.** Seis `PlazoVencido` ajenos en seis ventanas de salud. Si es la cuarta en un segundo, reinicio del chip con los demás módulos sanos en silencio, sin que la política ni «partes y voces» hayan sido consultadas (F4, F5).
3. **El primer hub escrito.** El censo sale verde en ciclos; R-H1 y R-H2 se verifican por primera vez contra ISR reales, y los 12 ms y las 100 cotas se redefinen mutuamente (F12).

## Lo que comprobé y está en pie

- La referencia al plan que la primera pasada exigía para un testigo de atraso está en `retraso_max_us` (`j2_tic.rs:775`).
- `Cerrando` ya no existe. Toda espera de la máquina tiene cota (salvo `SUCIA`, F7). `Muerta` es absorbente y está probada (`transporte_j2.rs:689-709`).
- La bajada tras un fallo ya no es ambigua: se consume al armar y la abortada no se repite (`j2_tic.rs:852`; §2.6).
- Hay un solo dueño de los doce canales en el diseño del instrumento: registros, sin `bind_interrupts!`, líneas enmascaradas (`j2_tic.rs:732-734`). El esclavo del banco sigue compartiendo el GPDMA1, y `tic_recupera` lo declara con «sin esclavo».
- La aritmética del presupuesto contra D7.3 es coherente: umbral 10 y ventana 1 s (`maestro_j2.rs:83-97`).
- El anillo de eventos no se desborda por una retención de P2: el planificador limita la producción de eventos a través del buzón (EN-PLACA.md:864, «no se pierde ningún evento»).

## Lo que no verifiqué

- No ejecuté ni medí nada. Las cifras de ciclos y microsegundos son las del papel y las de EN-PLACA.
- No leí el RM0486. «Tras el reset del GPDMA1 el canal tiene `IDLEF`» (F6) es el supuesto del código, no una lectura mía del manual.
- No leí `j2_spi.rs::resetear_por_rcc`, `junta_serrano.md` ni `junta_halberg.md` completos (este último solo por búsqueda).
- Marqué `[inferido]` lo que es razonamiento mío sobre el código y no un hecho leído.

## Cierre

Esto no es un problema de transporte ni de presupuesto. Es un problema de unidades. v3 promete un reloj y entrega un contador, y promete independencia y entrega un dominio de fallo con un tope. Mientras el tic sea isócrono y el hub se comporte como el papel supone, la diferencia no existe. El diseño entero vive dentro de ese «mientras».

El día que el hub deje de ser el hub que v3 supone, ninguna de sus garantías fallará: seguirán cumpliéndose en un tiempo que ya no es el de nadie. Ahí la arquitectura deja de ser un asunto de diseño y se convierte en física.

Archivos principales citados, todos bajo `D:\Desktop\projects\sam17\.claude\worktrees\papel-v3`:
- `docs\superpowers\juntas\2026-10-17-j2-transporte\papel-v3.md`
- `docs\superpowers\juntas\2026-10-17-j2-transporte\acta-2026-10-17.md`
- `docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md`
- `software\nucleo\core\src\transporte_j2.rs`
- `software\nucleo\core\src\maestro_j2.rs`
- `software\nucleo\fw\src\j2_tic.rs`
- `software\nucleo\fw\src\j2_ejecutor.rs`
- `software\nucleo\fw\EN-PLACA.md`
- `hardware\02-midi-cv\carga_hub_budget.py`
