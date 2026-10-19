# Voronov · lente ontológica · cuarta pasada · fichas B, C y H (`papel-v3.md`, commit 86b830c) · 2026-10-19

**Lectura y alcance.** Leí el brief completo. Del papel leí §0.4, la tabla de fichas de §1, R-H1 a R-H9, §2.1, §2.2 (K4), §2.5, §2.7 y §3. Leí también el acta del 19-10 y mi `junta3_voronov.md`. En código leí:

- `escaladas_j2.rs` y `modelo/tests/espera.rs`, completos.
- En `motor.rs`: `Cfg`, `RecDecide`, la escalada y `plan_drain`.
- En `transporte_j2.rs`: `Reloj64`, `avanza` y las pruebas de las cotas.
- En `fw/src/j2_tic.rs`: `recupera` y el presupuesto.
- En la rama `huella`: `j2_tcm.x`, `j2_tcm_pila.x`, `memory.x`, los `link_section` y las dos secciones de TCM de `EN-PLACA.md`.

No ejecuté nada: esta sesión no tenía shell. Las cifras nuevas son aritmética **(A)** o inferencia marcada. Las citas `papel:N` remiten a líneas de `papel-v3.md`.

## La restricción invisible de esta pasada

Las tres fichas tienen la misma forma: cada una mete un hecho de otro dueño en un recipiente que ya existía, y el recipiente le impone su contabilidad.

- **B:** la espera del controlador se aloja dentro de `Reiniciando`, un estado de ranura.
- **C:** el límite del módulo se escribe como una suma de cotas del J2.
- **H:** una obligación de memoria del hub se escribe con nombres de símbolo del binario del banco.

## Hallazgos

### H1 · BLOCKER · B contra C: `Reiniciando` ahora contiene una espera del planificador, y su cota no la contiene

**Evidencia**
- papel:174: «la ranura sigue en `Reiniciando` con su cota, y el planificador vuelve a pedir la recuperación del mismo incidente al cumplirse».
- papel:69, ficha C: «La espera de la ficha B corre dentro de `Reiniciando` y no mueve el mayor hueco de sello».
- papel:80, R-H1: «Se pide ≤ 12 ms y una ranura que venza dentro de una ventana que pase de su cota muere».
- `transporte_j2.rs:370-374`: la ranura muere cuando `espera + periodos > cota_reiniciando`, o sea a los 101 periodos (12,625 ms).
- `motor.rs:1128-1129` y `1178-1183`: `rec_en_curso` se pone al arrancar y la rama `Aplazada` no lo baja: «Ni RESET ni `HECHA`».
- `espera.rs:21-37`: el bloqueo corre sin P2. `espera.rs:186-192`: el fuzz lleva P2 a 30/s, y en él «la espera no actúa (0 aplazadas)» (brief:33).

**Qué rompe**
- **Antes**, `Reiniciando` empezaba con P4 ya corriendo y solo P2 podía retrasarlo: 12 ms (R-H1) < 12,625 ms (la cota). Sobrevive.
- **Ahora** caben dentro hasta 2 ms de espera, más la latencia de P3 para volver a pedir, que R-H1 permite hasta 12 ms: 2 + 12 > 12,625 (A).
- **El punto de presión.** En un bloqueo, las seis ranuras quedan aplazadas a la vez. Basta una cadena legal de P2 de más de ~10,5 ms que empiece al cumplirse la espera (A):
  - mueren las seis por su cota;
  - el supervisor deja de alimentar el IWDG y el chip se reinicia;
  - el presupuesto todavía tenía saldo y no se negó ninguna escalada.
- **La categoría.** `Reiniciando` nombra ahora dos estados: «la recuperación trabaja» y «la recuperación decidió no trabajar todavía». `REC_EN_CURSO` sigue puesto durante el segundo. Una sola cota cubre dos esperas que tienen dueños distintos.
- **La evidencia no llega a la combinación.** Donde la espera actúa no hay P2, y donde hay P2 la espera no actúa.

### H2 · ALTA · B: tres dueños para una decisión, y una muerte sin juez

**Evidencia**
- papel:134 (K4): «la ranura sin módulo sigue el camino de siempre y la política es el único peticionario».
- `motor.rs:1308-1316`: `plan_drain` pone `rec_pedida = true` sin pasar por `pol.paso`. En la misma función, `motor.rs:1336` dice: «La politica es la unica autoridad sobre «reiniciar»».
- papel:103 habla de «ocho elementos con escritores en tres niveles». `aplazada_hasta_us` es el noveno: lo escribe P4 (`motor.rs:1182`) y lo borra P3 (`motor.rs:1311`).
- `escaladas_j2.rs:66-68`: `hasta_us: self.ultima_us + self.espera_us`. Es un instante del controlador, el mismo para las seis ranuras.

**Qué rompe**
- **Quién es dueño de qué:**
  - P4 decide, con el presupuesto.
  - P3 decide cuándo se vuelve a preguntar. No tiene autoridad sobre «reiniciar» y actúa fuera de la política.
  - P1 ejecuta la muerte, con la cota.
- **Las sentencias que quedan:**
  - **La deliberada de K1**, intacta: `Denegada` → `RESET` por canal → cota → reinicio del chip.
  - **Una nueva, sin juez:** `Aplazada` + P3 tarde → cota → reinicio del chip (H1). Nadie la pronuncia: el presupuesto no negó, la política no se enteró y el planificador no decidió nada; simplemente no corrió.
- **K4** se escribió con un solo peticionario. La espera le devuelve el segundo.
- **La restricción de la tercera pasada, otra vez.** K1 le dio libro propio al controlador. La espera vuelve a copiar un hecho del controlador (su próximo instante disponible) en seis libros de ranura, con escritores en dos niveles.
- **No tiene testigo:** §2.8 no lista las aplazadas.

### H3 · MEDIA · B: el presupuesto sigue midiendo duración; la espera solo cambia la unidad

**Evidencia**
- papel:55: «El presupuesto de escaladas lo gasta la duración de un bloqueo, no el número de fallos».
- papel:181, fila de 6 en 1 s con espera de 2 ms: 1/0, 1/0, 1/0, 2/0, 3/0, 5/0.
- papel:185: «Nadie ha visto un bloqueo del GPDMA1 en el banco».

**Qué rompe**
- **Sigue siendo un reloj, con otro periodo.** Sin espera se gasta una escalada por cada ~270 µs de bloqueo. Con espera, una por cada 2 ms: 5 en 10 ms.
- **La decisión real es E × espera.** Lo que el instrumento decide ante un bloqueo es cuánto dura antes de reiniciarse, y eso lo fija el producto (A sobre la tabla):
  - 6 en 1 s con 2 ms: el umbral cae entre 10 y ~12 ms;
  - 3 en 1 s con 2 ms: entre 5 y 10 ms;
  - la ventana de 1 s no interviene.

  Esa cifra no aparece en ninguna celda de la ficha y no se barrió por encima de 10 ms.
- **La identidad del incidente se infiere por cercanía en el tiempo:** si llega a menos de 2 ms de la última, se trata como el mismo fallo. El controlador no tiene generación de incidente; la ranura sí la tiene (K4).
- **E carga dos sentidos:**
  - la tolerancia a averías curables que se repiten (el fuzz, donde la espera no actúa);
  - multiplicada por la espera, la tolerancia a un bloqueo.

  La ficha justifica E por el primero, y el segundo se firma sin nombre, contra una amenaza que no tiene tasa medida.

### H4 · MEDIA · B: un instante, dos relojes

**Evidencia**
- `transporte_j2.rs:136-137`: «Hay que llamarla al menos una vez por vuelta de 32 bits (6,2 dias a 8 kHz); el planificador la llama en cada tic.»
- `fw/src/j2_tic.rs:1238-1240`: el reloj de P4 (`RELOJ_REC`) solo se extiende dentro de `recupera`, cuando un canal no para.
- `motor.rs:1169`: el modelo pide la escalada con `u64::from(self.tics) * 125`, 32 bits sin extender. En cambio, `motor.rs:1092-1093`: P3 compara con `Reloj64`.

**Qué rompe**
- **El reloj de P4 se queda atrás.** `hasta_us` lo escribe el reloj de P4 y lo lee el de P3. El de P4 solo cambia de época cuando hay escaladas, que por diseño son raras. Tras 6,2 días o más sin una, queda al menos una vuelta por detrás, y no se recupera nunca (A).
- **El aplazamiento se vuelve el reintento por tic.** Desde entonces, cada `hasta_us` ya pasó para P3:
  - P3 vuelve a pedir en cada pasada durante toda la espera;
  - P4 vuelve a sondear `T_CANAL` y vuelve a aplazar.

  Es el reintento por tic que la tercera pasada rechazó (22,3 % de un núcleo por ranura, S). Con seis ranuras aplazadas, P4 ocupa más que el periodo [inferido].
- **En el modelo es peor.** Tras la vuelta de 32 bits, el reloj de P4 queda por debajo de `ultima_us`, `saturating_sub` da 0 y toda escalada se aplaza o se niega [inferido del código]. Las corridas de 4 s no pueden verlo.
- **En `fw`, K1 sin espera:** puede negar una escalada sin motivo si el silencio cae a menos de 1 s de un múltiplo de 6,2 días (~2·10⁻⁶ por silencio, A). Es raro. Lo que importa es la categoría: el reloj del presupuesto no es el del planificador.

### H5 · ALTA · C: el aserto no describe la máquina que acota

**Evidencia**
- papel:69: «con el plazo más largo (3 tics), 49,875 < 50 (A)».
- `transporte_j2.rs:1325-1326`: «muere en el tic `cota + 1` desde que entro en el estado».
- `transporte_j2.rs:355-361` y `371-373`: `reinicio_hecho` y `reinicio_en_curso` ganan a la cota en esa misma entrada.
- brief:34: la cota de 25 ms «vence entre 25,12 y 25,32 ms».
- El aserto no existe en el código. `T_WATCHDOG_TRAMA_US` solo aparece en `maestro_j2.rs:32,104,120`, que es el aserto de `umbral_muda`.

**Qué rompe**
- **La suma no cierra.** Una ranura que sobrevive puede pasar `cota + 1` periodos en cada estado: 0,375 + 25,125 + 12,625 + 12 = **50,125 ms ≥ 50 (A)**. El margen de 0,125 ms es un periodo, y la máquina se come dos.
- **Faltan dos términos más:**
  - la cuantización del rearme tras la espera de P3;
  - la trama siguiente, hasta que el módulo la recibe.
- **El aserto suma constantes**, cuando lo que tiene que acotar es lo que la máquina permite. Tal como se propone, el aserto pasaría y la propiedad que dice proteger sería falsa.

### H6 · MEDIA · C: las cotas se dimensionan contra una constante que no es del J2, en un reloj que no es el suyo

**Evidencia**
- spec:386: «la cota de arriba, cuánto sustain fantasma es tolerable, no está escrita en ningún papel».
- spec:592: «con dos cotas: piso del margen (este papel, ≥ 10 × recuperación) y techo del sustain fantasma (voz-total, HUECO)».
- papel:200: «los asertos que comparan los tres últimos no llevan término de tolerancia».

**Qué rompe**
- **El J2 ocupa todo el rango de N desde su lado.** El piso que el J2 le ponía a N era ~10 × recuperación. Con C, el piso pasa a ser toda la envolvente de supervivencia, a 0,25 % de un valor ESTIMADO. Si voz-total escribe su techo por debajo de 50 ms, las cotas de C quedan inválidas sin que cambie nada del J2.
- **Una desigualdad, tres relojes:** K2 (TIM7 y DWT), el planificador (R-H1, de pared) y el oscilador del módulo. No hay término de tolerancia. Si el módulo usa un RC interno (±1 % típico), su tolerancia sola es cuatro veces el margen [inferido: el papel no dice qué reloj tiene el módulo].

### H7 · ALTA · R-H4: la cifra de H es del enlazador del banco, no del J2

**Evidencia**
- `j2_tcm.x:30`: `*(.text._ZN17sam17_nucleo_core*)`, es decir, todo el crate `core`. Y `core/src/` contiene `usbmidi.rs`, `sysex.rs`, `preset.rs`, `partes.rs`, `servidor.rs`, `descubrimiento.rs` y más.
- `j2_tcm.x:25,28-29`: `.text.TIM7 .text.DMA2D .text.JPEG`, `j2_banco*` y `j2_ejecutor*`.
- `EN-PLACA.md:851`: «el texto de `core` no se toca (…): se elige por el nombre del símbolo».
- `EN-PLACA.md:888`: «las tres puertas estaban en la ITCM, pero sus cuerpos (…) se quedaban en la AXISRAM2». El primero de ellos había dado unos 150 ciclos «no diagnosticados» (`EN-PLACA.md:879`, `905`).

**Qué rompe**
- **Se midió otra cosa.** La ficha dice medir «el texto de las tres rutinas del J2 y lo que llaman». Lo medido es lo que capturan seis patrones de nombre en un binario donde casi solo se enlaza el J2. En el banco las dos cosas coinciden por accidente. En el hub, el patrón de `core` se lleva a la ITCM USB-MIDI, SysEx, presets y el resto del hub, y la cifra deja de ser del J2.
- **Los nombres son del banco:**
  - los vectores `DMA2D` y `JPEG`; en el hub serán «los que R-H1 fije» (papel:105);
  - `j2_banco`;
  - `j2_ejecutor.rs`, del que §2.9 retira `EJECUTOR_J2` y que hoy aloja `SELLOS` y `CUENTAS` en la DTCM (`j2_ejecutor.rs:168-169,201-202`).
- **La propiedad que compra H no tiene puerta.** H promete que nada de lo que el J2 ejecuta sale de la TCM. Eso se comprobó una sola vez, a mano y sobre el desensamblado, después de que se rompiera en tres cuerpos de biblioteca. La próxima llamada que salga (el CRC, el compositor) devuelve la caché fría a la fila del censo sin que falle nada.
- **(M) es el estatus de la cifra en el binario del banco.** Como obligación del hub, es (E).

### H8 · MEDIA · R-H4: la obligación arrastra dos de otra capa que no nombra

**Evidencia**
- `EN-PLACA.md:851`: la imagen se copia en `__pre_init`, «antes de inicializar `.data` y `.bss`: hay texto en la ITCM que corre desde `Config::new`».
- `EN-PLACA.md:884`: «La DTCM sale del reset sin escribir». Y: «Se sospecha ECC (…), pero no está verificado con el manual».
- `memory.x:8-9`: «El arranque firmado desde XSPI es del bring-up con placa (#231) y trae su propio mapa.»
- `EN-PLACA.md:879`: «Lo que queda fuera de la TCM son las constantes de `.rodata`».

**Qué rompe**
- **La secuencia de arranque es del hub y del #231, no del J2.** Exige tres cosas:
  - escribir la DTCM entera por palabras;
  - copiar la imagen antes que cualquier código de Rust;
  - que la imagen tenga dirección de carga en el mapa del FSBL.

  Afecta a todo lo que el hub ponga en la DTCM, incluida la pila de `j2-tcm-pila`. R-H4 lo resume en «copiados de su imagen al arrancar», como si fuera del J2.
- **«Estáticos» es una clase de almacenamiento de Rust.** La propiedad que H promete es «lo que el J2 lee no pasa por la D-cache», y la `.rodata` queda fuera. Hoy pesa poco (2 063 frente a 2 046 ciclos, M). Un CRC con tabla la haría pesar otra vez [inferido: el CRC no está escrito, #267].

## Veredictos

**B.** Firmaría 6 en 1 s. A la pregunta de Samuel: **sí**, durante un bloqueo de 1 ms los resets necesitan separación. El reset que llega ~270 µs después, con el controlador aún bloqueado, no es un fallo nuevo sino el mismo visto otra vez; contarlo convierte el presupuesto en un reloj. Pero la espera de 2 ms no se firma junto a `Reiniciando` 12,5 ms y R-H1 12 ms (2 + 12 > 12,5, H1), y su umbral real, E × espera, no está en la ficha (H3).

**C.** No se cierra. Faltan cuatro cosas:
- un aserto sobre lo que la máquina permite (cota + 1 periodo por estado, el rearme y la trama siguiente), que hoy da 50,125 ≥ 50 (H5);
- la cota inferior de `Reiniciando` frente a espera + R-H1, que B rompe (H1);
- `T_WATCHDOG_TRAMA`, con su techo y la tolerancia de su reloj, dicho por el dueño del módulo (H6);
- el barrido de las cotas en el modelo, que no existe.

**R-H4.** La cifra vale como medida del binario del banco, no como obligación del hub (H7). Le falta:
- el cierre de llamadas de las tres rutinas, medido en el binario del hub con el CRC y el compositor;
- una comprobación que falle cuando ese cierre se rompa;
- nombrar la copia, la DTCM escrita por palabras y la `.rodata` como obligaciones del arranque del hub (H8).

## Fuera de alcance, en una línea

- **K2:** `reloj_anomalo` salió 1 y 2 veces sin cachés y «la causa no está diagnosticada» (`EN-PLACA.md:907`). Las cotas de C solo son de pared si K2 lo es.

## Lo que no verifiqué

- No corrí el modelo. H1 y H5 son aritmética sobre el código.
- El modelo tiene `hold_on_rec` (P2 al arrancar la recuperación), pero no una retención al cumplirse la espera. La combinación de H1 no la ha corrido nadie.
- H4 es una predicción para `fw`, porque la espera no está en `fw`. La parte del modelo sale de leer el código, no de una corrida.
- No sé qué oscilador usa el módulo (H6) ni si el CRC llevará tabla (H8).
- No listé con `rust-nm` qué símbolos de `core` entran hoy en la ITCM del banco.

## Cierre

La espera dice la verdad sobre el controlador y la escribe en el estado de una ranura. El aserto dice la verdad sobre el módulo y la escribe con cotas del J2. La huella dice la verdad sobre el banco y la firma como obligación del hub. Ninguna de las tres cifras está mal medida; las tres viven en el sitio equivocado.

Un hecho mal asignado no falla cuando se mide. Falla cuando su dueño verdadero cambia de opinión.
