# Serrano · cuarta pasada · fichas B, C y H del papel v3 (commit `86b830c`) · 2026-10-19

*Informe acotado a lo que pide `junta4-brief.md`: la ficha B (§1, §2.5), la ficha C (§1, §2.5) y la ficha H (§1, R-H4, §3), con §0.4 como contexto. No modifiqué ningún archivo.*

**Referencias.**
- Papel y brief, rama `docs/junta4-fichas-b-c`: `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v3.md`, `junta4-brief.md`, `acta-2026-10-19.md`.
- Modelo, rama `j2/modelo-espera`: `software/nucleo/modelo/tests/espera.rs`, `barrido.rs`, `junta.rs`, `modelo/src/motor.rs`, `core/src/escaladas_j2.rs`, `core/src/transporte_j2.rs`, `core/src/maestro_j2.rs`.
- TCM, rama `j2/huella-tcm`: `software/nucleo/fw/j2_tcm.x`, `fw/src/j2_tcm.rs`, `fw/src/j2_tic.rs`, `fw/src/j2_banco.rs`, `fw/EN-PLACA.md`.

## A) Diagnóstico

- **Qué es.** Tres fichas puestas a firma. B y C se apoyan en el modelo de seis ranuras y H en medidas de placa.
- **Cifras.** Las de B y H coinciden con sus fuentes. Lo que falla está en lo que no cuentan:
  - C no cumple su propio aserto si las cotas se cuentan como las vence la máquina.
  - La espera de B se come el margen de `Reiniciando` frente a R-H1, y esa combinación nadie la ha corrido.
  - La cota en frío de H deja fuera justo la parte que sigue dependiendo de la caché.
- **Hallazgos.** 0 BLOCKER, 3 ALTA, 3 MEDIA y 1 BAJA.
- **Método y límites.**
  - Leí el código y los textos. No ejecuté nada, porque esta sesión no tiene shell.
  - Las cifras (S) las cotejé con el código que las imprime y con el brief, no con una corrida.
  - Lo que digo del modelo sin haberlo corrido va marcado como aritmética (A) sobre el código.
  - No cotejé nada con el RM0486.

## B) Hallazgos

**1. [ALTA] [CONTRA, ASSUMP] Ficha C: el aserto suma las cotas nominales, pero la máquina las vence un periodo después. Con las cifras de la propia ficha, 25 + 12,5 ms no cabe**
- **Evidencia.**
  - Ficha C: «con el plazo más largo (3 tics), 49,875 < 50 (A)». En los costos: «0,125 ms de margen sobre `T_WATCHDOG_TRAMA_US` = 50 ms, que es ESTIMADO».
  - Ficha C: «la de 25 ms vence entre 25,12 y 25,32 ms (S)». Brief, `v3a4`: «la cuarta negada a los 0,91 ms, la ranura muere a los 13,62 ms». Eso son 12,71 ms en `Reiniciando`.
  - `core/src/transporte_j2.rs:361,373` (`espera + periodos > cota`) y `:1325-1326`: «muere en el tic `cota + 1` desde que entro en el estado».
  - `maestro_j2.rs:28`: «sin trama valida en N ms (N del plan, ~50)».
- **Problema.**
  - Con `>` y la precedencia de §2.2 («una recuperación que termina en el tic en que vence la cota salva la ranura»), una ranura que sobrevive puede pasar 201 periodos en `Vencida` y 101 en `Reiniciando`.
  - La suma da 0,375 + 25,125 + 12,625 + 12 = **50,125 ms (A)**. Con el tic que arma después de componer, 50,25. Con las cifras (S) de la ficha y de `v3a4`, unos 50,2 ms.
  - El margen declarado es de 0,125 ms (0,25 %). Es menor que cada uno de estos desvíos:
    - el redondeo de µs a periodos en `lanzar`, que no está especificado;
    - la tolerancia entre el reloj de K2 y el oscilador del módulo. §2.7 la reconoce («los asertos que comparan los tres últimos no llevan término de tolerancia»), pero la celda no la lleva.
  - Contada igual, la «Otra» (20 ms) da 45,25 ms y cabe. La ficha no lo dice. Tampoco dice cuánto retrasa cada opción el reinicio y la `W` del supervisor (§2.5: «Alargarla sí retrasa ese reinicio»).
- **Qué rompe.**
  - Escrito con las constantes en µs, el aserto pasa (49 875 < 50 000) y la máquina lo incumple. Es una puerta que no puede fallar por la razón que la justifica.
  - En el peor caso que dice acotar, el módulo suelta las notas de una ranura que el hub da por recuperada.
- **Falta decidir.** ¿El aserto cuenta las cotas nominales o como las vence la máquina? ¿Con qué tolerancia entre relojes? ¿Hacia dónde redondea `lanzar`?

**2. [ALTA] [GAP, STATE] La espera de B vive dentro de la cota de `Reiniciando` y se come su margen sobre R-H1. Nadie ha corrido las dos juntas**
- **Evidencia.**
  - Ficha B: «la ranura sigue en `Reiniciando` con su cota y el planificador la vuelve a pedir al cumplirse».
  - Ficha C: «La espera de la ficha B corre dentro de `Reiniciando` y no mueve el mayor hueco de sello».
  - R-H1: «el planificador en el 3; la recuperación en el 4» y «Se pide **≤ 12 ms**». §2.5: «sobrevive a una retención de P2 de 12 ms y muere con 14 (M)».
  - `modelo/src/motor.rs:1305-1317`: la repetición la pide `plan_drain`, en P3.
  - `core/src/transporte_j2.rs:370-380`: la espera de `Reiniciando` solo vuelve a cero con `HECHA`.
  - `modelo/tests/espera.rs:21-37`: el bloqueo se corre sin P2. Brief: «En los dos fuzz la espera no actúa (0 aplazadas)».
- **Problema.**
  - Sin espera, `Reiniciando` solo espera a P4. Su cota de 101 periodos (12,625 ms) cubre una ventana de R-H1 de 12 ms con unos 0,6 ms de margen.
  - Con espera, la ranura aplazada pasa hasta 2 ms sin que nada corra para ella, y después necesita una pasada del planificador. Si una ventana legal de R-H1 empieza en `hasta_us`, la ranura queda en `Reiniciando` unos 1,7 + 12 ≈ 13,7 ms (A). Muere, y el supervisor reinicia el chip.
  - La tolerancia de `Reiniciando` a R-H1 baja de ~12,6 a ~10,6 ms.
  - Pasa en dos casos:
    - en el escenario que motiva la espera, porque durante un bloqueo las seis ranuras se aplazan en cada ciclo (`motor.rs:617-621`: tras el reset todas pasan a IDLEF, se recuperan, rearman y vuelven a colgarse);
    - con dos atascos independientes a menos de 2 ms.
  - Ningún aserto ata la espera, R-H1 y la cota de `Reiniciando`. La frase de C es cierta para el hueco de sello y calla esto.
  - Los costos de B tampoco cuentan lo que pierde la ranura aplazada: hasta 16 tramas propias por aplazamiento.
- **Qué rompe.** Un hub que cumple R-H1 reinicia el instrumento con un bloqueo de 1 ms que, sin retención, la ficha da por resuelto con una escalada.
- **Falta decidir.** ¿Cuánta ventana de R-H1 tiene que aguantar una ranura con la escalada aplazada? ¿Qué desigualdad liga espera, R-H1 y `cota_reiniciando`, y quién la asevera?

**3. [MEDIA] [ASSUMP] Lo que separa las reglas de B depende de dos supuestos que la celda no declara**
- **Evidencia.**
  - Ficha B: «En el fuzz de la junta con atascos curables, 0 reinicios de 30 (S; con los 3 en 1 s de `fw` hoy, 4 de 30)».
  - Brief: «atascos curables 0,8/s». §5.3: «con `escaladas_gpdma = 0`» en 24 h.
  - `motor.rs:84,87`: `msg: [25; N]`, `t_canal_ns: 25_000`.
  - `EN-PLACA.md:915`: «Sigue sin correr la rama que escala porque un canal no para en 25 µs».
- **Problema.**
  - El 4 de 30 contra 0 de 30 sale de la tasa de atascos, no del diseño. Con una escalada por atasco, la probabilidad de ver ≥ 4 atascos en un segundo dentro de una corrida de 4 s a 0,8/s ronda el 14 % (A).
  - Esa tasa es inventada. §5.3 solo deja pasar a fabricación cero escaladas en 24 h, y por debajo de ~0,1/s el fuzz ya no separa 3 de 6.
  - Lo que sí separa las reglas es un precio fijo: con un canal incurable, cada vecina pierde 6 tramas en vez de 3.
  - Las filas «sin espera» del bloqueo valen para tramas de 25 B (plazo de 1 tic) en las seis ranuras y para `T_CANAL` = 25 µs (E). De ahí sale la cadencia de ~275 µs entre escaladas. Con mensajes de 3 tics cambian la cadencia y el «1 ms gasta 4 escaladas».
  - La rama que dispara la escalada nunca ha corrido en placa.
- **Qué rompe.** Samuel elegiría 6 en 1 s por una diferencia que depende de una tasa que nadie ha medido y de un tamaño de trama que no es el del instrumento. La celda presenta las dos cosas como evidencia.
- **Falta decidir.** ¿Qué tasa de atascos y qué mezcla de mensajes son el escenario de diseño de B?

**4. [MEDIA] [CONTRA, STATE] La espera añade un peticionario fuera de la política, que K4 había dejado como el único**
- **Evidencia.**
  - §2.2 (K4): «así que la ranura sin módulo sigue el camino de siempre y la política es el único peticionario».
  - `motor.rs:1308-1316`: pone `rec_pedida = true` sin pasar por `pol.paso`. Compárese con `:1335-1346`.
  - §2.1: «son ocho elementos con escritores en tres niveles». `fw/src/j2_tic.rs:413-448` ya tiene más.
- **Problema.**
  - El planificador repite la petición por su cuenta, con el incidente viejo. Vuelve a haber dos caminos que encienden `REC_PEDIDA`, y eso es lo que rompió la tercera pasada.
  - El instante aplazado es un elemento compartido nuevo: lo escribe P4 y lo lee P3. No está en `fw` ni en §2.1.
  - §5.2(e) pide la denegación en banco «con la regla que firme la ficha B».
- **Qué rompe.** Firmar B deja falsa una frase de §2.2. Además, (e) obliga a construir la espera en `fw` antes de poder cumplirse.
- **Falta decidir.** ¿La repetición pasa por la política, o se declara como segundo peticionario con su prueba en §5.2(i)?

**5. [ALTA] [CONTRA, GAP] Ficha H: la cifra en frío deja fuera la entrada y la salida de la excepción, que es lo que la caché fría sigue tocando**
- **Evidencia.**
  - Ficha H: «La caché fría deja de decidir la fila del J2 en el censo.» §3: «el `DWT` (cota de diseño)».
  - `EN-PLACA.md:881`: «Como cota de diseño vale el DWT más lo que cueste apilar y desapilar la excepción (no medido); el medidor es el techo.»
  - `EN-PLACA.md:861` (el DWT «no incluye el apilado ni el desapilado») y `:886` («La tabla de vectores sigue en la AXISRAM2»).
  - `j2_tcm.x` no mueve ni la pila ni los vectores.
- **Problema.**
  - Con `j2-tcm`, la pila de excepciones y la tabla de vectores siguen detrás de la D-cache. Lo único del J2 que todavía depende de la caché fría es el apilado (marcos de hasta 104 B, `EN-PLACA.md:908`) y la captación del vector en cada entrada del tic y del planificador. El DWT empieza a contar después.
  - El papel toma el DWT como «cota de diseño» y omite lo que su fuente dice que le falta.
  - Entre el DWT (2 063) y el techo del medidor (2 400) hay 337 ciclos sin repartir entre esa entrada y el artefacto del medidor.
  - Con el CRC alto (350, E), el margen del DWT bajo 2 500 es de **87 ciclos** (A). Por el medidor ya se pasa (16,5 %). No está demostrado que la caché fría «deje de decidir»: lo decide lo que no se midió.
  - La «Otra» se cuesta solo con la invalidación total (35–37 %), que `EN-PLACA.md:886` llama «la cota, no un caso». Con solo la D fría y sin TCM sale 16,4–17,4 % (`:893`).
- **Qué rompe.**
  - R-H4 enmendada saca al J2 del régimen de caché que declara el hub, y R-H6 recibe 12,4 % como obligación en frío.
  - El acta del 19-10 pidió precisamente el peor caso de caché antes de las puertas de banco.
- **Falta decidir.** ¿La cota de diseño en frío incluye la entrada de la excepción? ¿R-H4 dice dónde van la pila y los vectores?

**6. [MEDIA] [AMB, OPS] Ficha H: 8 120 y 4 616 B miden lo que los patrones del guion de enlazado arrastran de un binario de banco, no la obligación que escribe R-H4. Y nada comprueba la residencia**
- **Evidencia.**
  - Ficha H: «el texto de las tres rutinas del J2 y lo que llaman, en la ITCM … 8 120 B».
  - `j2_tcm.x:26-30`: mete módulos enteros por nombre (`j2_tic`, `j2_spi`, `j2_banco`, `j2_ejecutor`) y todo `sam17_nucleo_core`.
  - `j2_banco.rs:124, 321, 402, 632`.
  - `EN-PLACA.md:879`: «queda fuera de la TCM … `.rodata`».
  - `j2_tcm.rs:92-116`: `comprueba` mira `EN` y la copia.
  - §0.4, punto 26: la división de K2 ya se quedó fuera una vez.
- **Problema.**
  - **Dentro de la cifra hay cosas que no son la obligación:** código que corre una sola vez (el montaje, `lanzar`); el banco entero, no solo los 154 B del juez (también `bajada_del_banco`, el compositor de mentira); el ejecutor que §2.9 retira; y, en el instrumento, cualquier función de `core` que use otro módulo del hub.
  - **Fuera de la cifra quedan cosas que sí lo son:**
    - `.rodata`: si el CRC real usa tabla, irá ahí, detrás de la D-cache;
    - la tabla de vectores;
    - la pila (~0,85 KB, E);
    - la obligación de escribir la DTCM entera por palabras antes de cualquier store de un byte (`EN-PLACA.md:884`, `j2_tcm.rs:53-56`).
  - Los 64 y 128 KB se leyeron de registros en development boot, no del RM (`EN-PLACA.md:885`).
  - El error no tiene signo conocido. Si un símbolo cambia de nombre o de crate, vuelve a la AXISRAM2 en silencio, y ninguna puerta falla.
- **Qué rompe.** R-H6 recibe una cifra que no es ni cota superior ni cota inferior del J2 del instrumento, y una obligación que no se puede verificar.
- **Falta decidir.** ¿La obligación se define por símbolos (cuáles) o por los bytes de un binario (cuál)? ¿Qué puerta asevera la residencia?

**7. [BAJA] [AMB] Etiquetas, redondeos y bordes del barrido**
- **Evidencia.**
  - Ficha H y §3: «12,4 % … (A)». `EN-PLACA.md:877,890` dice «(E)».
  - Ficha C: «49,875 < 50» y «0,125 ms». §2.5: «49,9 < 50 (A): 0,1 ms».
  - Ficha B: «hasta 10 ms». `espera.rs:126` termina el barrido en 10 ms. `junta.rs:157-159` (`v3a5`) llegaba a 12, 13, 14 y 20 ms.
  - `espera.rs:39-88` solo asevera con 3 en 1 s.
- **Problema.**
  - La columna de seis ranuras es estimada (E) en su fuente.
  - El margen del aserto cambia de cifra entre la ficha y §2.5.
  - «Hasta 10 ms» es el final del barrido, no una frontera. Por aritmética, con 6 en 1 s la frontera cae hacia 11–13 ms (A, sin correr).
  - La configuración recomendada (6 en 1 s con 2 ms) solo se imprime en una prueba `#[ignore]`; no hay aserción que la vigile.
- **Qué rompe.** Hay cifras que se leen como fronteras y como hechos sin serlo. Una regresión del modelo movería B sin poner nada en rojo.
- **Falta decidir.** ¿Qué estatus lleva la columna de seis ranuras? ¿Qué afirma B más allá de 10 ms?

## Veredictos

**B.**
- Firmaría 6 en 1 s y no 2 en 100 ms, que reinicia con 5 ms y cuesta hasta 20 tramas por segundo y vecina. La espera no se firma hasta correrla con una retención de R-H1 dentro de `Reiniciando` (hallazgo 2) y hasta que la celda declare la tasa del fuzz (hallazgo 3).
- **A la pregunta de Samuel: sí, durante un bloqueo de 1 ms hace falta una espera entre reset y reset.**
- Sin espera, las escaladas de un mismo bloqueo no son pruebas independientes de un controlador incurable. Miden la duración del bloqueo en pasos de ~275 µs, una cadencia que nadie eligió (sale de las tramas de 25 B, del plazo y de `T_CANAL`). Con 6 en 1 s, eso fija por accidente entre 1 y 2 ms el umbral que reinicia el instrumento. Con espera, el umbral es un parámetro declarado (≈ E × espera), aunque todavía sin fuente.

**C.**
- No se cierra.
- Falta que el aserto cuente las cotas como las vence la máquina: cota + 1 periodo, el tic de armado, el redondeo de `lanzar` y una tolerancia entre el reloj de K2 y el módulo. Contado así, 25 + 12,5 ms da ≥ 50,1 ms y no cabe; 20 + 12,5 ms sí cabe.
- Faltan también el barrido de las cotas y la cota de `Reiniciando` frente a la espera de B más R-H1.

**R-H4.**
- No vale como está.
- Los ciclos son una cota inferior, no una cota de diseño: les falta la entrada y la salida de la excepción, con la pila y los vectores en la AXISRAM2.
- Los bytes miden lo que arrastran los patrones del guion en un binario de banco. Les faltan `.rodata`, los vectores, la pila, el CRC y el compositor reales, la obligación de escribir la DTCM entera al arrancar y una puerta que compruebe la residencia.

## Fuera de alcance, una línea cada uno

- K2: `reloj_anomalo` salió 1 y 2 veces en corridas sin cachés y está sin diagnosticar (`EN-PLACA.md:907`). La ficha C afirma «Con K2 las cotas son de pared», y R-H9 sigue sin comprobar.
- La rama de la escalada por `T_CANAL` nunca ha corrido en placa (`EN-PLACA.md:915`). Todo B descansa en el modelo.

## Comprobado y correcto

- **Ficha B.** Cada cifra de la celda coincide con la tabla del brief y con la de §2.5. La tabla coincide en columnas y filas con lo que imprime `espera.rs:125-152` (no la corrí).
- **Ficha H.** Coinciden con `EN-PLACA.md:888-908` y con la aritmética: 8 120; 4 616; 154 (38 + 116); 2 063 / 2 400 / 2 046; 5 860; 35,2 / 37,4 %; 12 736; los 21 ciclos de la pila; ~0,85 KB (836 B); 13,1–14,5 / 15,2–16,5 %.
- **`Presupuesto::con_espera`.** Hace lo que dice la ficha: aplaza sin gastar ni negar, y una negada no mueve la espera (`escaladas_j2.rs:62-84, 124-136`).
- **Cotas.** El modelo corre C con 200 y 100 periodos (`motor.rs:88`). `core` y `fw` siguen en 100 y 100 (`transporte_j2.rs:26,30`), como dice la celda.

## C) Preguntas que el documento evita

1. ¿El aserto de C cuenta las cotas nominales o como las vence la máquina, y con qué tolerancia entre relojes? (1)
2. ¿Cuánta ventana de R-H1 aguanta una ranura con la escalada aplazada, y qué aserto lo ata? Para Halberg: correr `atasco` con un P2 de 12 ms en `hasta_us`, y bloqueos de 11 a 14 ms con espera. (2)
3. ¿La cota de diseño en frío incluye la entrada de la excepción? ¿Dónde viven la pila y los vectores del J2? (5)

## D) Riesgos por categoría

- **Técnico:** 1, 2, 5 y 6.
- **Producto:** 2 (reinicio del instrumento con un hub que cumple R-H1) y 3 (una regla elegida por una tasa inventada).
- **Ejecución y operaciones:** 4, 6 (residencia sin puerta) y 7.

## E) Aclaraciones inmediatas

No hay BLOCKER. Aun así, tres ALTA impiden firmar tal como están: la 1 bloquea la ficha C, la 2 bloquea la espera de la ficha B y la 5 bloquea la frase «la caché fría deja de decidir» de R-H4.
