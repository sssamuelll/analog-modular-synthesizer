# El enlace sin jefe: los dos micros oyen el J2 y el arranque pierde el orden

**Fecha:** 2026-08-25 · **Estado:** diseño aprobado en conversación con Samuel
(las decisiones de la sesión están en el acta, §12) · **Ámbito:** el módulo de
Voz total y los dos papeles que hoy prohíben lo que aquí se decide.

Cadena de herencia: spec de los dieciséis (#164) → spec del módulo de Voz total
→ **este papel**. Este papel **levanta la decisión 3 del #164**, enmienda la
prohibición del cerebro §7, reescribe el arranque de la orquestación §2 y
**cierra la decisión abierta 1** de orquestación §9. No dibuja cobre ni escribe
firmware: reescribe el contrato interno del módulo y deja cada papel afectado
enmendado o con su enmienda mandada (§8).

---

## 0. Qué es este papel, y por qué existe

El módulo de Voz lleva dos RP2350B porque dieciséis osciladores necesitan
dieciséis cronómetros de PIO y un micro trae doce (dieciséis §3, riesgo 4).
Hasta hoy, uno de los dos era **el maestro** y el otro recibía sus órdenes
**reenviadas** por el SPI privado — más tarde, siempre, y con un jitter
sistemático y asimétrico entre columnas (voz-total §3.3, H-BP2).

Samuel decidió (2026-08-24) eliminar esa asimetría en su origen: *«no quiero
que haya un microcontrolador al que le lleguen más tarde los mensajes»*. El
guion que podía matar la idea se escribió primero — `enlace_budget.py`,
PR #198 — y no la mató: el segundo oyente en T interna cuesta **4,2 % de la
capacidad de la red**, tres veces menos que una novena rama. Este papel es la
arquitectura que ese presupuesto habilita, con sus condiciones (§7).

Lo que este papel deja claro desde el título: **no hay jefe ni subordinado en
las órdenes**. Las asimetrías que sobreviven (§2, D2) son de cobre — un
cristal, un MISO, una referencia — y ninguna de ellas vuelve a significar
jerarquía de protocolo.

---

## 1. Lo que se levanta, citado

### 1.1 La decisión 3 del #164, partida en sus dos mitades

Texto vigente (dieciséis §2, decisión 3):

> *«Del J2 cuelga un micro, no los chips. El cerebro le habla al micro maestro;
> los conversores cuelgan de un SPI privado, dentro del módulo.»*

La decisión mezcla dos cosas que nunca fueron la misma:

1. **Que del J2 no cuelgan los chips** — los conversores viven en buses
   privados. Esto **sobrevive intacto**. Su justificación original era el
   tri-state del MISO con CS alto — el hueco que el cerebro §4.1 destapó y
   convirtió en contrato de módulo medible en bring-up (pieza 4) —, y esa
   justificación no depende de cuántos micros escuchen: depende de que el MISO
   lo maneje **uno**.
2. **«El cerebro le habla al micro maestro»** — la exclusividad de escucha.
   Esto **se levanta**. Ningún argumento del papel original la sostenía por sí
   misma: era un corolario gratis de la primera mitad, y su costo (el reenvío)
   quedó registrado como riesgo 7 del propio spec: *«El segundo micro recibe
   sus órdenes reenviadas, no directas. Irrelevante para el tono; no
   irrelevante para un disparo.»*

También sobrevive, palabra por palabra, el alcance: *«Esto es una decisión de
este módulo, no una ley para los demás»*. El doble oyente **tampoco** es ley
para los módulos 5/6/7 — el núcleo §10 sigue teniendo esa pregunta abierta, y
R-J2 de orquestación §7 (*«lo decide el diseño de esa placa»*) es la regla que
ampara este cambio sin necesidad de tocar la regla misma (su formulación
local, *«en el módulo 3 v2 cuelga un micro»*, sí se parcha — §8).

### 1.2 La prohibición del cerebro, y la cifra que la condiciona

Texto vigente (cerebro §7):

> *«el J2 es contrato congelado a 10 MHz con ocho stubs colgando y no admite un
> cliente más (§4).»*

La prohibición era **eléctrica**, no de rol — y por eso se enmienda con una
cifra, no con un argumento. `enlace_budget.py` (PR #198) le puso número al «no
admite»:

| Caso | Costo de capacidad | Límite de flanco al peor caso (738 mm) |
|---|---|---|
| Hoy: 8 ramas, un oyente por rama | — | 8,90 MHz |
| **T dentro del módulo de Voz** | **+4,2 %** | **8,54 MHz** |
| Novena rama | +12,5 % | 7,91 MHz |

El tráfico declarado exige 8,70 MHz (43,5 % de ocupación contra el techo del
50 %, `latencia_mano_budget.py`). El umbral **continuo** de mazo para el caso
adoptado — 8 ramas más la T, resuelto sobre las funciones del guion, no sobre
su rejilla — es **≈ 721 mm**: al peor caso geométrico de hoy (738 mm) le
sobran ~17 mm, no los 138 que sugería la rejilla del barrido (que exigía pasar
también la novena rama, un caso que este papel rechaza). La condición vive en
§7 y en el issue #199. La enmienda al cerebro §7 queda así: el bus no admite
un cliente más **gratis**; admite lo que `enlace_budget.py` apruebe, y ese
guion es la puerta (issue #199, punto 3: *«Un cliente de J2 deja de ser
gratis»*).

### 1.3 Por qué no va por el puente UART

El cerebro §7 sanciona una vía para clientes nuevos con micro propio: *«va en
el case como otro cliente del protocolo, con su propio micro y su propia
alimentación, hablando por el UART del puente (§6.6)»*. Ese patrón no aplica
aquí, y la razón cabe en una frase: **el segundo micro no es un cliente nuevo
del protocolo**. Es el mismo módulo, la misma ranura, la misma identidad y el
mismo CS, oyendo el tráfico que ya era suyo — hasta hoy, de segunda mano. No
añade superficie al protocolo (§3, R-S5), no añade identidad al descubrimiento,
no añade ranura al mux. Un cliente del puente es otra *piel* del modelo; esto
es la misma *mano*, con los dos guantes puestos a la vez. Y la vía del puente
es UART a ritmo de piel — un oyente de tiempo real que debe capturar el mismo
flanco que su gemelo no puede llegar por ahí.

---

## 2. Las decisiones

### D1. Del J2 cuelgan los dos micros de escucha; los chips siguen sin colgar

`SCLK`, `MOSI` y `CS` de la ranura del módulo llegan a las dos columnas por una
**T interna de tres líneas**, por el mismo salto de ~150 mm que ya cruzan el
SPI privado y el I²C (dieciséis §3, tabla «Qué cruza los conectores»;
`enlace_budget.py`, `LARGO_STUB_INTERNO`). El `MISO` lo conserva **una sola
placa** (D2), con su obligación intacta: alta impedancia siempre que su CS esté
alto, sin excepciones de modo (contrato de módulo, cerebro §4.1 pieza 4).

Tres líneas y no dos, y esto ninguna fuente lo decía: **el framing del
contrato ES el CS**. La trama se delimita por CS, no por un campo — hoy con el
caso vigente de `j2.rs` (72 bits, tres AD5686R) y mañana con el largo variable
del cambio 1 de orquestación §8 (*«el largo lo declara el módulo»*), que este
papel hereda. Sin ver el CS de su ranura, el segundo micro no sabe dónde
empieza una trama. El costo es trivial — el CS carga una rama, no ocho como
SCLK/MOSI — pero se escribe: `enlace_budget.py` gana la línea del CS en T (§9).

La electrónica del MISO **no se toca**: la ventana común de resistencias de
serie está vacía (`enlace_budget.py`: MISO no baja de 220 Ω sin que la pelea
pase de 12 mA, y a 220 Ω el flanco se muere) — MISO y SCLK/MOSI llevan piezas
distintas por diseño, y el segundo oyente cuelga **solo** de SCLK/MOSI/CS.

Reparto de periféricos **esperado, POR_CONFIRMAR hasta que exista
`pines_budget.py`** (§9): la columna B tendría sus dos SPI de hardware
ocupados (esclava del bus privado de la cabecera, ama de su propio bus de
DACs), así que su escucha del J2 iría por PIO — 8 de sus 12 máquinas están en
cronómetros. El mismo guion tiene que contar además el códec que el acta E-5
mudó a este módulo (los oídos: el RP2350 no trae I²S — come PIO o un SPI de
alguien) antes de dar el reparto por bueno.

### D2. La cabecera: la placa que concentra lo que no puede duplicarse

La placa hoy llamada «maestra» concentra las cosas de las que solo hay una: el
**cristal** (decisión 17: una sola base de tiempo, 0,087 cents de sesgo si
hubiera dos), la **referencia ADR4525**, la **EEPROM de identidad** (0x50) y
el **punto de medida de la referencia** — la medida de ámbito módulo la lee el
ADC de esta placa; mux hay uno por micro (decisión 18), lo irrepetible es la
medida, no la pieza. Y conserva el **MISO**: quien tiene la boca del módulo es
quien concentra lo que el módulo dice.

Se renombra: **la cabecera**. El nombre nuevo no es cosmético — es la mitad
del cambio. «Maestra» decía *manda*; «cabecera» dice *dónde está la boca y el
reloj*. La cabecera **no ordena nada**: consolida y contesta. Sus deberes:

- Hablar por MISO por todas las ranuras lógicas del módulo (D4) — R-J1 se lee
  por ranura **física** (§8: R-J1 gana esa palabra).
- Consolidar las medidas de ámbito módulo (`voces aportadas`, `tensión de la
  referencia`) y publicar el estado de **ambas** columnas (§4.3).
- Escribir el canal compartido de ancho de pulso — es **un** canal físico de
  convertidor para el módulo entero (dieciséis §11), no uno por columna.
- Ser ama del bus privado inter-columna y **preguntar** (D5).
- Distribuir el reloj: *«la línea cruza el conector como una señal digital
  más»* (dieciséis §7.2) — sin cambio, salvo el vocabulario: dueño de reloj ya
  no significa jefe de protocolo.

La otra columna se llama **columna B**. En el papel viejo: maestro → cabecera
(columna A); esclavo → columna B.

### D3. Perro propio, orden por el bus *(decisión de Samuel, 2026-08-25)*

Cada micro lleva su **watchdog de silicio** armado — el del propio RP2350
(datasheet 2024-08, §12.9 *Watchdog*, pág. 1193) — con una regla de
alimentación de **dos condiciones**: se acaricia solo cuando (a) el lazo que
procesa trama del J2 avanza **y** (b) el núcleo 1 demuestra progreso con un
contador cruzado (el render de envolventes y el drenaje de PIO viven allí,
voz-total §3.4 — un perro que solo mira el núcleo 0 dejaría una envolvente
congelada sonando para siempre, exactamente el sustain infinito que voz-total
§9.2 juró matar). Un firmware colgado en cualquiera de los dos lazos deja de
acariciar y el chip se reinicia solo; el silencio durante el reinicio lo
garantiza el camino de OE (R-A4).

La operación `reiniciar columna` (§5.2) viaja por el broadcast como cualquier
escritura, y **cada micro se reinicia a sí mismo** cuando la orden trae su
columna. Cubre lo *vivo-pero-loco* (procesa órdenes pero hace ruido malo); lo
*muerto* lo cubre el perro. Entre los dos, por primera vez **ambos** micros
tienen quién los recupere — el maestro del diseño viejo no tenía a nadie
(orquestación §2.3: *«Nadie desde dentro»*).

Los hilos `RESET_ESCLAVO` y `OK_ESCLAVO` **salen del conector**: dos pines
menos cruzando columnas, cero protocolo de arbitraje, cero abrazo mortal. La
fila correspondiente de la tabla «Qué cruza los conectores» se retira (§8).

Alternativas rechazadas, para que el papel diga qué no hacer: *llave en la
cabecera* (conserva un hilo asimétrico y deja a la cabecera otra vez sin quién
la reinicie) y *reset cruzado bidireccional* (dos hilos más, arbitraje, y el
perro cubre casi todo lo que cubriría). Acta en §12.

### D4. Ranuras lógicas funcionales, nunca por micro *(decisión de Samuel, 2026-08-25 — cierra la decisión abierta 1 de orquestación §9)*

Lo que se cierra es el **criterio de partición**: las ranuras lógicas del
módulo (cambio 2 de orquestación §8) se parten por **función**, jamás por
micro. Nacen ya las dos que este papel necesita:

- **Ranura V** — los dieciséis osciladores. `instancia` = oscilador, 0–15,
  exacta contra `MAX_INSTANCIAS = 16` (`param.rs`); los índices por instancia
  crecieron con voz-total §7 (los 18 del censo de orquestación más los 9 por
  canal de filtro y envolvente: 27).
- **Ranura M** — lo de placa y lo de módulo, 13 entradas (§5.2). En M la
  `instancia` tiene **una sola semántica**: enumera *sitios* declarados en el
  descriptor — el módulo (0), las placas, las columnas. Ningún índice
  reinterpreta la instancia; qué pares (índice, instancia) existen lo declara
  el descriptor, como todo lo demás. Esto responde a la objeción obvia: no es
  el patrón de JackId (#157) — allí un mismo campo cambiaba de significado
  según el rango; aquí el campo significa siempre lo mismo (un sitio).

Los bloques que las actas mudaron a este módulo — las aristas y vínculos del
relator (E-3, ~150), el mixer, el volumen y los oídos (E-5), el paneo (E-6) —
toman ranura funcional según su ámbito **cuando su censo aterrice en el
descriptor**; cuántas ranuras exactas quedan lo fija el descriptor con el
censo vivo delante, que es lo que la decisión abierta siempre pidió. Lo
decidido aquí es la regla y la prohibición.

La alternativa «una ranura con el campo de índice repartido» se rechaza porque
carga dos semánticas en un campo según el rango — el patrón de JackId. Y la
tercera opción, la que la simetría ponía sobre la mesa y ningún papel había
escrito, **se prohíbe** (R-S1): una ranura por micro chocaría con la decisión
4 del cobre (*«un solo módulo: una identidad, un CS […]»*), con el acta E-3
(una sola bajada, una identidad) y con el mux del cerebro (canal = EEPROM =
módulo), y no compra nada — el broadcast ya le llega a los dos micros igual.

**El criterio de cabida, contra el `param.rs` vigente.** El criterio literal
de la decisión abierta («los 16 bits del identificador») quedó viejo: desde el
commit `82e2d0d` el `ParamId` es de 32 bits — ruta de 3×4 + instancia 4 +
índice 8. Para un módulo directo los niveles 2–3 van a cero y la dirección
efectiva sigue siendo ranura + instancia + índice = 16 bits, así que la
propiedad que el criterio protegía (caber en tres septetos de SysEx, núcleo
§3.1) se conserva. Con el censo vivo (536 entradas escribibles con estéreo,
`check_censo_voz.py`; 538 con el delta de §5.2): V usa 16 instancias × 27
índices, M usa 13 entradas, el bloque del relator son ≤256 aristas — **cada
bloque cabe en instancia de 4 bits e índice de 8**. Nada del identificador se
toca.

El eslabón que faltaba entre descubrimiento y direccionamiento: **una
identidad anuncia N ranuras lógicas en su descriptor**. El canal físico del
mux sigue siendo unívoco (canal → identidad → sus ranuras), así que el
diagnóstico del cerebro («cuál módulo lo trabó», cerebro §8) no se vuelve
ambiguo. La asignación de números de ranura lógica la hace el cerebro al leer
el descriptor; el mapa es parte del modelo publicado. El mecanismo es del
cambio 2 y ahí se implementa — este papel fija el requisito.

### D5. El enlace interno se invierte: muere la ida, nace la vuelta

El flujo `enlace esclavo` (64 bits por evento y por trama,
`spi_privado_budget.py`) **muere**: era el reenvío, y era apenas el 1,2 % del
caudal del peor caso del bus (estéreo A, el desglose del propio guion) — su
costo real nunca fueron los bits, fue la tardanza.

El bus privado inter-columna **no muere**: cambia de sentido. La columna B
necesita entregarle a la cabecera lo que el cerebro le pida por MISO — sus
medidas, su progreso de afinación (los números de la decisión 2 del #164
vuelven por MISO), sus CHANGED y su **latido** (§4.3). La cabecera es ama de
ese bus y **pregunta**; B contesta como esclava, igual que hoy, solo que ahora
lo que viaja son respuestas y no órdenes.

Esta asimetría es inherente a MISO-en-uno y no es jerarquía: **a B no le llega
nada tarde porque a B ya no le llega nada** — las órdenes entran por el
broadcast, a las dos columnas, en el mismo flanco. La vuelta es reparto de
trabajo de oficina: quien tiene la boca junta los papeles antes de hablar.

El caudal de la vuelta se presupuesta al recorrer `spi_privado_budget.py` (§9):
medidas de 8 canales a cadencia de telemetría, TuneProgress a cadencia de
barrido, latido — órdenes de magnitud por debajo del flujo que sale.

### D6. El reparto del broadcast, declarado

Los dos micros oyen **todo**. Quién obedece qué:

| Ámbito | Quién actúa |
|---|---|
| Ranura V, instancias 0–7 | La cabecera (sus ocho osciladores) |
| Ranura V, instancias 8–15 | La columna B (los suyos) |
| `silenciar durante el barrido` (compartido) | **Ambos**, cada uno sobre su columna, en la misma trama |
| `ancho de pulso` (compartido) | **La cabecera**: es un solo canal físico de convertidor para el módulo entero (dieciséis §11) y el CV cruza el conector como línea analógica (dieciséis §3) — compartido de cobre, no de código |
| Ranura M, ámbito módulo | La cabecera consolida; escrituras a `reiniciar columna` las ejecuta la columna nombrada (D3) |
| Ranura M, por placa | El micro de cuya columna cuelga la placa |

Nota sobre lo compartido: en el diseño viejo estos parámetros también viajaban
reenviados. Con el broadcast, la **coordinación entre columnas viaja en la
propia trama** — silenciar para el barrido ya no necesita que nadie se lo
ordene a nadie (la decisión abierta 3 de orquestación sigue abierta con su
criterio de bring-up; lo que cambia es que cualquiera de sus dos salidas se
implementa sin mensajero).

### D7. Una sola imagen de firmware; la columna se decide por strap

Las dos columnas corren **el mismo binario**. Qué columna es cada una lo dice
un pin de strap cableado en la placa que porte cada micro (cuál placa es esa
depende de la partición física de voz-total §8, hoy reabierta; el precedente
del mecanismo es del propio cobre: *«mismo diseño, poblado con micro»*,
dieciséis §3). El strap decide: instancias 0–7 u 8–15, cabecera o no (MISO,
consolidación, ama del bus interno). Dos binarios divergiendo en silencio son
una familia entera de bugs que no vale la pena poseer; un strap es un bit.

### D8. El crosspoint cuelga del bus privado, y el deber sigue al bus

E-3 fundió la bahía en este módulo y dejó abierto *«quién shiftea los 256 bits
del AD75019»*. El #171 lo recogió con tres opciones de bus. Este papel decide
el bus y deja la columna:

- **Muere la opción del CS pasado** («colgarlos del SPI del instrumento con un
  CS que el maestro pase»): con el broadcast no hay maestro que pase nada.
- **Muere la opción de la bajada propia** («dejarles su propio CS en la
  bajada»): sería colgar chips del J2, exactamente la mitad de la decisión 3
  que sobrevive (D1).
- **Queda la del bus privado** — que era el supuesto con el que
  `spi_privado_budget.py` ya presupuestaba (su glosa «desde el acta E-3» le
  atribuía al acta lo que era una decisión pendiente; este papel la toma de
  verdad, y el guion queda citándolo a él).

Al #171 le queda **solo elegir la columna**, por geometría, al dibujar. Y el
deber de arranque sigue al bus: **shiftea ceros al arrancar el micro de cuya
columna cuelgue el crosspoint** (H-OF4, voz-total §5.4: la bahía nace
desconectada), como parte de su §4.1 paso 2, antes de bajar su OE.

---

## 3. Las prohibiciones

Los dientes de este papel. Cada una existe porque su violación es el camino de
vuelta a lo que se acaba de matar.

> **R-S1. Las columnas no son ranuras.** La simetría es invisible al modelo:
> ninguna piel, preset ni cliente sabe que hay dos micros. Una ranura por micro
> reintroduciría en el direccionamiento la anatomía que este papel saca del
> protocolo.

> **R-S2. La columna B jamás toca el MISO.** Ni en fallo, ni en bring-up, ni
> «temporalmente». La obligación de alta impedancia con CS alto (cerebro §4.1
> pieza 4) la cumple la cabecera; la columna B ni siquiera tiene el pin
> conectado. Es la mitad de la decisión 3 que sobrevive, y es la que evita la
> pelea de buses que el cerebro §4.1 documenta.

> **R-S3. Nadie resetea a nadie por cobre.** No hay hilo de reset entre
> columnas en ninguna dirección. El reset ajeno es una orden del modelo
> (`reiniciar columna`); el reset propio es del perro. Un hilo de reset cruzado
> es un jefe con otro nombre.

> **R-S4. El bus interno no lleva órdenes del instrumento.** Solo vuelta:
> medidas, progreso, latido. Si una orden viajara por dentro «porque quedaba
> cómodo», la asimetría de latencia vuelve por la puerta de atrás y el jitter
> entre columnas deja de ser por construcción. Las órdenes entran por el J2 o
> no entran.

> **R-S5. Cero tipos de mensaje nuevos.** El protocolo (`protocolo.rs`: *«la
> superficie COMPLETA del instrumento»*) no gana variantes por este cambio.
> Todo lo nuevo son parámetros: estado de columna, reiniciar columna. Es la
> regla de superficie constante del #159 aplicada aquí.

---

## 4. El arranque, reescrito

Reemplaza la orquestación §2.2–§2.3 y el cambio 8 de §8. La secuencia vieja era
un guion dirigido (*maestro arranca → suelta el reset → esclavo arranca →
maestro publica*); la nueva no tiene guion porque no hace falta: el estado
seguro no depende del orden.

### 4.1 La secuencia, por micro y sin orden

| Paso | Quién | Qué pasa | Estado audible |
|---|---|---|---|
| 0 | Hardware | OE de los caminos de silencio en alta impedancia por pull-up; pulls por línea al estado seguro; el driver del latch de la bahía inhibido por pull (H-OF4) | **Silencio**, sin firmware, para las 16 voces y los 48 VCAs |
| 1 | Cada micro, cuando arranca | Se comprueba, arma su perro (D3), lee su strap (D7) | — |
| 2 | Cada micro | Escribe **todos sus conversores a reposo** — los DACs de su columna a cero-escala, y el dueño del crosspoint (D8) shiftea los 256 bits a ceros | — |
| 3 | Cada micro | Solo entonces baja el OE de **su** columna | Sus 8 osciladores gobernables |
| 4 | La cabecera | Publica `estado de columna` de la suya en cuanto arranca, y de la B en cuanto el latido interno aparece (§4.3) | El módulo dice la verdad de lo que hay |

El orden 2-antes-que-3 no es estilo: es lo que hace verdad a R-A4 en un reset
caliente (§4.2).

No hay paso «esperar al otro». Si una columna arranca y la otra no, la que
arrancó suena y la que no, calla por hardware y **se dice** (§4.3). El
invariante que la junta compró — *«estado de reposo garantizado por hardware
—pull, no firmware— como condición de arranque»* — sobrevive entero; lo que
muere es la cláusula *«hasta que el esclavo confirme»*, que ataba la condición
a un testigo. La condición nunca necesitó testigo: la sostienen los pulls.

### 4.2 Las reglas, con texto nuevo

**R-A1 queda intacta**, palabra por palabra: sin descriptor no hay capacidades.
Ya estaba enunciada sin presuponer rol.

> **R-A2 (texto nuevo). Los parámetros de una columna no existen mientras esa
> columna no arranque.** Sus ocho osciladores se publican con `hueco: columna
> no arrancada` y rechazan escritura con `ERROR`. Quién lo publica depende de
> cuál columna falte: si falta la B, lo publica la cabecera; si falta la
> cabecera, no hay boca — el módulo queda **presente y mudo** y el juicio pasa
> al cerebro (§4.3, §4.4).

> **R-A3 (texto nuevo). El reset es alcanzable desde el modelo, por columna.**
> Existe `reiniciar columna` como parámetro de solo escritura de la ranura M,
> instancia = columna, **contado en el censo** (§5.2 — la versión vieja exigía
> la operación y el censo no la contaba; ese agujero se cierra de paso). La
> ejecuta el micro nombrado, sobre sí mismo.

> **R-A4 (texto nuevo). Reiniciarse silencia primero, por el camino de OE.**
> El reset — del perro o de la orden — suelta los GPIO, el pull-up sube OE y
> los pulls devuelven cada oscilador al reposo: el silencio audible no depende
> del firmware ni de los DACs. Lo que el reset caliente **se supone que no**
> hace es borrar los DACs: el cero-escala de RSTSEL es del encendido según el
> supuesto que voz-total §9.1 dejó marcado contra la hoja del AD5686R — nunca
> leída (§7, condición 4) — y ningún papel sostiene que se re-aplique en un
> reboot mientras el /RESET de los conversores no esté cableado (§10, riesgo
> 6: atarlo al estado RUN del micro es la decisión de cobre pendiente). Por
> eso el paso 2 de §4.1 escribe reposo **antes** de bajar OE — conservador
> bajo cualquier lectura de la hoja. La mutación de verificación mide el
> **tiempo hasta el silencio** contra una cota declarada en el plan, no «que
> llega solo».

### 4.3 La vida por columna, y quién la ve

La vigilancia vieja del maestro era una mentira estructural que este rediseño
destapó: la orquestación §2.3 dice *«si el maestro no arranca, no hay
descriptor»*, pero el cambio 4 puso el descriptor en la memoria del módulo —
128 KB desde el acta E-7 (24AA1025; la identidad 24AA02E48 en 0x50, aparte) —
que el cerebro lee por I²C **sin ayuda de ningún micro**. Un micro muerto no
suprime nada: el mecanismo nunca pudo funcionar como está escrito. Se
reemplaza por vida dicha en voz alta, que es la doctrina que el repo ya sentó
para el arranque del cerebro (B5: *«permisivo, pero DICHO»*):

- **`estado de columna`** (ranura M, medida, instancia = columna, ×2): la
  cabecera publica el suyo al arrancar y el de B según su latido en el bus
  interno (D5). Cadencia de salud de 1 Hz (orquestación §7.1, donde sustituye
  a `estado del esclavo`). Su enumerado de valores se fija en el descriptor;
  los umbrales (latidos perdidos para declarar `colgada`, timeout del perro)
  se fijan en el plan, con su derivación — este papel solo exige que existan
  como cifras declaradas, no adivinadas.
- **El latido**: un contador que B incrementa y la cabecera lee al preguntar
  (D5). Latido parado → `estado de columna B = colgada`, huecos en las
  instancias 8–15, y el cerebro decide si ordena `reiniciar columna B` — que B
  ejecutará si está viva-pero-loca, y que el perro ejecutará por ella si está
  muerta.
- **La cabecera muda**: si la cabecera muere, el módulo deja de contestar,
  pero **no** parece desenchufado: la EEPROM sigue contestando por I²C. El
  estado es **presente y mudo** — el que R-A1 ya nombra — y es el cerebro
  quien lo sintetiza: publica las instancias 0–7 con hueco y rechaza
  escrituras hacia ese módulo, **sin dejar de emitir trama a la ranura
  mientras la identidad responda** (regla nueva, con su fila en §8: sin ella,
  el silencio del cerebro mataría de rebote a la columna B por watchdog de
  trama). Mientras el perro reinicia la cabecera, la columna B sigue
  obedeciendo órdenes — el broadcast no pasa por la cabecera. El diseño viejo
  aquí perdía el módulo entero; el nuevo pierde la mitad del sonido y toda la
  telemetría, temporalmente, y nada queda sonando descontrolado.

### 4.4 La tabla de fallos, revisada

Los modos 3 y 4 de orquestación §4 (*el maestro no arranca* / *el esclavo no
arranca*) se reescriben así:

| # | Modo de fallo | Cómo se hace visible |
|---|---|---|
| 3'A | La columna B no arranca (o se cuelga) | R-A2 vía la cabecera: `estado de columna B` + hueco en sus ocho + `ERROR` a escritura |
| 3'B | La cabecera no arranca (o se cuelga) | **Presente y mudo**: la identidad contesta, el módulo no; el cerebro sintetiza los huecos de 0–7 y sigue emitiendo trama (§4.3); el perro la reinicia |
| 7 | Conversor mudo en un SPI privado | Igual que hoy; «el micro» es el de esa columna |
| 8 | Referencia caída | Igual; el ADC es el de **la cabecera** (era «del maestro») |
| 10 | Placa de voces ausente | Igual; el hueco lo publica el micro de su columna |

El watchdog de trama (voz-total §9.2) pasa a ser **por micro**: cada columna
juzga «trama válida» por sí misma — ambas ven el bus — y silencia lo suyo. Los
watchdogs cruzados del §9.2 viejo (heartbeat del esclavo, «el esclavo vigila
al maestro») se retiran: los reemplazan el perro propio (D3), el latido (§4.3)
y el watchdog de trama que ya cubría la muerte del cerebro. La mutación de
matar cada micro a mitad de nota sobrevive, con el criterio de R-A4: tiempo
hasta el silencio contra cota declarada.

### 4.5 Las cotas del evento, re-fundadas

Las cotas de voz-total §3.3 estaban escritas sobre la etapa que desaparece
(*«peor caso nota-a-VCA incluyendo la etapa maestro→esclavo»*). Quedan así:

- **≤ 3 ms nota-a-VCA se mantiene** como criterio de aceptación del evento
  (pase siguiente), ahora sobre la cadena real: cerebro → trama → parse → DAC.
- **La uniformidad ±0,5 ms entre columnas deja de ser una cota a perseguir y
  pasa a ser una propiedad a medir**: ambos micros capturan el mismo flanco de
  SCLK; el sesgo residual es diferencia de cómputo local entre dos copias del
  mismo binario (D7) — esperable en microsegundos. `evento_budget.py` (§9) la
  asevera en vez de compensarla; el jitter «sistemático y asimétrico» de H-BP2
  muere aquí.

---

## 5. El modelo

### 5.1 Las ranuras que nacen ya

V (osciladores): 16 instancias × 27 índices (los 18 del censo de orquestación
§5.1 más los 9 por canal de voz-total §7). M (placa-y-módulo): 13 entradas
(§5.2), instancia = sitio (D4). Los bloques de E-3/E-5/E-6 (aristas del
relator, mixer y oídos, paneo) toman su ranura funcional al aterrizar su censo
en el descriptor (D4). R-J1 se lee por ranura física: **todas las ranuras
lógicas del módulo hablan por el mismo MISO**, el de la cabecera.

### 5.2 El censo: el delta, y dónde aterriza cada número

El delta de este papel es uno solo: sale `estado del esclavo` (1 medida),
entran `estado de columna` (2 medidas) y `reiniciar columna` (2 escribibles de
solo escritura). Neto: **+3 entradas, +2 escribibles, +1 medidas.** Dónde
aterriza — porque el mismo delta vive en tres artefactos con bases distintas,
y confundirlos es el patrón del «−15» que este repo ya pagó:

| Artefacto | Base vigente | Con el delta |
|---|---|---|
| Orquestación §5.1, censo golden del bloque VCO | 298 entradas / 226 escribibles | **301 / 228** |
| Voz-total §7, tabla del re-censo (columna #164) | 226 escribibles / ~520 con los bloques nuevos | **228 / ~522** |
| `check_censo_voz.py` (`BASE_V2`) | 226 → 536 con estéreo → 792 de 1024 | **228 → 538 → 794 de 1024** |

Dos salvedades que el parche literal rompería:

- **El preset sigue siendo de 226 valores.** `reiniciar columna` es operación,
  no estado: no entra al preset ni a los «226 CHANGED» del cambio 12 de
  orquestación. Solo los escribibles suben a 228.
- **El par 301/228 completo no vive en `check_censo_voz.py`** — ese guion
  cuenta escribibles y memoria, no medidas. Lo asevera el test de cierre del
  cambio 2, que monta el módulo completo; su enmienda (§8) lo apunta al censo
  vivo **importado** del guion, no transcrito.

### 5.3 Las relaciones

E5 (orquestación §6.1) se re-escribe parametrizada por columna: **`estado de
columna X ≠ arrancada` ↔ los parámetros de sus ocho osciladores** (X ∈ {A, B},
instancias 0–7 / 8–15). Sigue cruzando ranuras (la medida vive en M, los
parámetros en V); la regla de casa que este papel fija: **una relación que
cruza ranuras vive en la ranura del lado dependiente** — aquí V, que es donde
el hueco aparece. La tabla de relaciones del cambio 13 gana esa regla.

### 5.4 Renombres que tocan códec, descriptor y tests

No es prosa. El motivo de hueco `esclavo no arrancado` vive en la **lista
cerrada** de motivos de orquestación §3.3 (y la arrastra el cambio 5): pasa a
`columna no arrancada` — un renombre, no un motivo nuevo. La medida `estado
del esclavo` vive en el censo golden (§5.1), en la fila de salud de la
cadencia de §7.1 (1 Hz) y en la ficha del cambio 8, y su condición está atada
en E5: pasa a `estado de columna` ×2. Cada sitio tiene su fila en §8.

---

## 6. Qué muere, qué sobrevive, qué nace

| | |
|---|---|
| **Muere** | El reenvío (`enlace esclavo`, 64 bits — 1,2 % del caudal del peor caso; el costo era la tardanza). El arranque serializado. `RESET_ESCLAVO`/`OK_ESCLAVO` y su fila del conector. Los watchdogs cruzados de voz-total §9.2. El riesgo 7 del #164 (disuelto: ambos oyen el mismo flanco). El jitter sistemático entre columnas de H-BP2. Los modos de fallo 3/4 como pareja asimétrica. El vocabulario maestro/esclavo en los cuatro papeles. Dos de las tres opciones del #171 (D8). |
| **Sobrevive** | MISO en un solo micro y su obligación de tri-state (la mitad buena de la decisión 3). La base de tiempo única con su dueño físico (decisión 17; el plan B de la constante de razón, intacto). La referencia, la EEPROM y la medida de salud en la cabecera. El silencio por pulls antes del firmware (decisión 15, sin la cláusula del testigo). R-A1. R-J1/R-J2/R-J3. El SPI privado como bus local de conversores de cada columna. El camino I²C de identidad y descriptor. La cota ≤ 3 ms. El preset de 226 valores. |
| **Nace** | La T de tres líneas (con el CS, que ninguna fuente contaba). La vuelta B→cabecera con su presupuesto. La vida por columna dicha en voz alta — incluida la política del cerebro ante un módulo presente y mudo, que ningún papel tenía. El perro propio en ambos micros, con alimentación de dos condiciones. `estado de columna` ×2 y `reiniciar columna` ×2 en el censo. La regla de relaciones que cruzan ranuras. El strap de columna y la imagen única. La resiliencia nueva: cabecera muerta ya no significa módulo muerto. |

---

## 7. Condiciones de cierre — nada de esto está probado

Este papel se sella **condicionado**, y las enmiendas de §8 se redactan igual:
como decisión sellada-condicionada que cita esta sección, nunca como hecho
medido (la del cerebro §7 ya tiene esa forma; las demás la adoptan). Las
condiciones no son adornos: cada una puede tumbar el diseño, y el issue #199
las rastrea.

1. **El mazo baja del umbral del caso adoptado: ≈ 721 mm.** Hoy el peor caso
   geométrico son 738 mm — faltan ~17 mm, no los 138 de la rejilla vieja
   (§1.2). El número que manda no es este papel: es `enlace_budget.py` con su
   puerta rehecha a umbral continuo (§9). Acortar el mazo es una decisión de
   layout de fila — territorio del case, propuesta aparte, y el case no se
   toca al vuelo.
2. **Drive de 12 mA en SCLK/MOSI confirmado en el firmware del cerebro.** El
   presupuesto entero lo supone y nadie lo ha verificado.
3. **El flanco real, con osciloscopio**, en el extremo de la rama más larga,
   contra el VIH de 2,0 V a IOVDD = 3,3 V (Tabla 1436, §14.9.4, pág. 1339 del
   datasheet RP2350 2024-08) — en el bring-up del cerebro. El margen es
   demasiado fino para sellarlo con aritmética; el propio guion se declara
   *puerta, no prueba*.
4. **Los POR_CONFIRMAR de `enlace_budget.py`**: Z0 y velocidad de la cinta
   (catálogo genérico), capacidad de pin y de conector (declaradas — el
   datasheet no las publica). Aparte, y en su guion: la hoja del AD5686R
   **nunca se leyó** (`j2.rs`: tres intentos con timeout; pedírsela a Samuel),
   y de ella cuelgan dos deudas: el techo real de SCLK
   (`spi_privado_budget.py`) y la semántica exacta de RSTSEL que R-A4 usa como
   supuesto. No condicionan la T — los DACs no cuelgan del J2 — pero sí la
   renegociación del reloj y el riesgo 6.
5. **La línea del CS en T** entra a `enlace_budget.py` (§9) — pendiente de
   escribirse, aunque su costo se espera trivial.

---

## 8. El mapa de enmiendas, papel por papel

Lo que este diseño obliga a tocar. Cada fila es trabajo del plan de
implementación; ninguna está hecha. Todas se redactan en forma
sellada-condicionada (§7).

**dieciséis (#164):**

| Sitio | Tipo | Qué |
|---|---|---|
| §2 decisión 3 | Reescribir | El texto de §1.1: cuelgan los dos de la escucha, chips no, MISO en la cabecera |
| §2 decisión 15 | Parchar | Cae «hasta que el esclavo confirme»; la condición la sostienen los pulls |
| §2 decisión 23 | Parchar | La primera columna montada es **la cabecera** (única que puede hablar); B se prueba después oyendo el mismo bus |
| §3 completo | Reescribir | El diagrama pierde los rótulos «(maestro)»/«(esclavo)»; «Uno es el maestro…» → §1.1; «en la placa maestra» → la cabecera; la tabla de conectores gana la fila de la T (SCLK/MOSI/CS), pierde la de RESET/OK y el «ojo» de la fila del SPI privado se reescribe |
| §7.2 | Parchar | «dueño del reloj» sí, «maestro» no |
| §7.3 | Reescribir | «El esclavo no toca el J2 en ningún caso» → R-S2 (solo MISO); la escucha sí la toca |
| §9 | Reescribir | Señales RESET/OK fuera; queda OE + pulls + perro; el protocolo remite a este papel |
| §11 | Parchar | «la maestra» / «placas no maestras» → la cabecera / las placas sin micro; el canal compartido queda en la cabecera (D6) |
| §13, §14 | Parchar | «placa maestra» → cabecera; «ni el maestro ni el esclavo» → ningún micro |
| §18 riesgo 7 | Retirar | Disuelto; su vía de cierre pasa a `evento_budget.py` re-especificado |
| §18 decisión abierta 2 | Parchar | «las tres placas no maestras» → las tres placas sin micro |

**orquestación:**

| Sitio | Tipo | Qué |
|---|---|---|
| §2 completo | Reescribir | El arranque de §4 de este papel |
| §3.3 lista de motivos | Parchar | `esclavo no arrancado` → `columna no arrancada` (arrastra el cambio 5) |
| §4 tabla de fallos | Reescribir | §4.4 de este papel, **más la regla nueva**: el cerebro sigue emitiendo trama a un módulo presente-y-mudo mientras su identidad responda |
| §5.1 censo | Parchar | 301/228; entra `reiniciar columna`; **el preset sigue en 226** (el 226 del cambio 12 no se toca) |
| §6.1 E5, §7.1 salud | Parchar | Por columna; regla del lado dependiente; `estado de columna` en la fila de salud |
| §7 R-J1 y R-J2 | Parchar | R-J1 gana «física» (las ranuras lógicas de D4 comparten el MISO de su ranura física); R-J2 actualiza su formulación local, la regla queda |
| §8 cambio 2 | Sincronizar | Cerrado por D4; su «72 entradas que no son voces» se corrige (eran 10 — confundía no-escribibles con no-voces — y con el delta son las 13 de la ranura M); el test de cierre monta el módulo contra el censo vivo **importado** de `check_censo_voz.py` |
| §8 cambio 8 | Reescribir | R-A2/R-A3/R-A4 texto nuevo; test: columna simulada sin arrancar, y cabecera simulada muda; bring-up sin hilos de reset. Lleva además el registro de que el punto §4.1 del acta de la junta queda superado por este papel |
| §9 riesgo 1 | Reescribir | El reenvío desaparece; `evento_budget.py` re-especificado (§9); el riesgo 2 (#158) hereda el contexto broadcast |
| §9 decisión abierta 1 | Cerrar | D4, con acta — y con la nota de que su criterio literal («16 bits») quedó viejo tras `82e2d0d` |
| §10 verificación | Parchar | La fila de `evento_budget.py` pierde «la etapa maestro → esclavo»; la fila del censo pasa del 298/226 al censo vivo importado |

**voz-total:**

| Sitio | Tipo | Qué |
|---|---|---|
| §1 herencia | Parchar | La línea «de #164 se conserva» apunta a la decisión 3 nueva |
| §3.1 | Sincronizar | «Eventos» sale de la lista de flujos del SPI privado; de paso, la cifra base que E-6 declaró errónea se corrige |
| §3.3 | Reescribir | Prerrequisito sin «entrega al esclavo»; cotas de §4.5 |
| §3.4 | Reescribir | El reparto de núcleos, **por micro**: ambos corren esclavo J2 en núcleo 0; la ventana de MISO solo en la cabecera; el contador cruzado del perro (D3) entra al reparto |
| §7 re-censo | Parchar | La columna #164 de su tabla: 226 → 228 escribibles (~520 → ~522); `check_censo_voz.py` la cita vía `BASE_V2` |
| §9.2 | Reescribir | Watchdog de trama por micro; cruzados fuera; perro de dos condiciones + latido; la mutación mide tiempo-hasta-silencio contra cota |
| §9.3 | Parchar | «la maestra» → la cabecera; la segunda puerta valida dos oyentes en un J2 real, no un handshake |
| §12 registro | Parchar | S-2, S-5 y H-OF1/OF2 ganan nota de supersesión por este papel (sus resoluciones apuntaban al §9.2 y a la cota que aquí cambian) |
| §13 E-1 y E-3 | Sincronizar | E-1: «El maestro de la Voz» → la cabecera; E-3: nota de que el bus del crosspoint lo decidió D8 y al #171 le queda la columna |

**cerebro:**

| Sitio | Tipo | Qué |
|---|---|---|
| §4.1 pieza 1 | Parchar | «ocho cintas con sus ocho stubs» → ocho ramas más la T del noveno oyente en SCLK/MOSI/CS |
| §4.1 pieza 4 | Parchar | El contrato de módulo nombra: en la Voz lo cumple la cabecera; B no tiene el pin |
| §4.3 | Parchar | El criterio de back-drive de esa rama se relee con dos receptores por línea (la corriente total se duplica; el límite por receptor no cambia) |
| §7 | Parchar | «no admite un cliente más» → «no admite clientes gratis; `enlace_budget.py` es la puerta» |
| §11 tabla de budgets | Sincronizar | El alcance de `enlace_budget.py` ya no dice «ocho stubs»: dice ocho ramas + la T del noveno oyente (y el docstring del guion, que lo cita palabra por palabra, se re-sincroniza — §9) |

**junta-vco-hallazgos:** no se reescribe — es acta. El registro de que su punto
§4.1 queda superado viaja en la fila del cambio 8 de orquestación, arriba.

**issues:** #171 se reformula (D8: el bus decidido, dos opciones muertas en voz
alta, queda la columna). #199 gana la nota del umbral continuo (~721 mm para
el caso adoptado; la rejilla de 600 era el caso triple) y la de que la T está
sellada en papel pendiente de sus condiciones. #160 hereda la
re-especificación de `evento_budget.py`. #180 gana el contexto para
`arranque_budget.py` y `trama_j2_budget.py`. #178 gana la nota de que el MISO
de la Voz lo contesta la cabecera.

---

## 9. Los guiones

Re-especificación; se escriben en sus pases, no en este.

| Guion | Estado | Qué cambia o qué nace |
|---|---|---|
| `enlace_budget.py` | existe (PR #198) | +la línea del CS en T; **la puerta del caso adoptado pasa a umbral continuo** (resolver la longitud, no muestrear la rejilla — el 600 escondía el 721); la cabecera del guion pasa de «hoy lo prohíbe la decisión 3» a sellado-condicionado citando §7; el docstring re-sincroniza su cita del alcance con el cerebro §11 nuevo |
| `spi_privado_budget.py` | existe | −`enlace esclavo`; +`vuelta` con cifra (medidas, TuneProgress, latido); renombres (`MICROS = 2 # cabecera + columna B`; la glosa de E-3 pasa a citar D8); el assert de ciclos vale para **ambos** micros contra voz-total §3.4; conserva su deuda del `SCLK_TECHO` (hoja del AD5686R, nunca leída) |
| `check_censo_voz.py` | existe | `BASE_V2` 226 → 228, y su cascada (536 → 538 con estéreo; 792 → 794 de 1024) |
| `pines_budget.py` | **no existe** — sigue siendo «antes que ninguna otra cosa del bloque digital» | Cuenta lo nuevo: columna B +3 entradas (SCLK/MOSI/CS) +1 strap +1 SM de PIO para la escucha (contra el framing del cambio 1, no contra 72 bits fijos); cabecera +1 strap; el códec de E-5 (los oídos — PIO o SPI); los dos hilos RESET/OK que se recuperan; cita el watchdog (§12.9, pág. 1193) |
| `evento_budget.py` | no existe | La cadena sin etapa de reenvío; asevera el sesgo residual entre columnas (§4.5) en vez de compensarlo; sigue sirviendo al #160 |
| `arranque_budget.py` | no existe | Presupuesta §4.1: EEPROM + descriptor por I²C con la cifra **importada** de `check_censo_voz.py` (hoy 22 512 B) y el peor caso del objetivo E-7 (100 B/entrada), contra instrumento listo < 3 s |
| `trama_j2_budget.py` | no existe | El árbitro de R-M4: la Voz declara sus bloques como **un** módulo de 16 (D4/R-S1); el largo máximo de mazo entra como constante citada |

---

## 10. Riesgos, con criterio de cierre

1. **El perro no caza un cuelgue que sigue acariciándolo.** Mitigado por la
   alimentación de dos condiciones de D3 (trama + progreso del núcleo 1) y por
   `reiniciar columna` para lo vivo-pero-loco. Cierra: test que cuelga cada
   lazo por separado — incluido el render del núcleo 1 — y asevera que el
   perro dispara; más la mutación de §4.4.
2. **La vuelta interna sin presupuesto.** Un caudal de vuelta mayor del
   esperado podría apretar el bus privado. Cierra: la cifra en
   `spi_privado_budget.py` recorrido, antes de dibujar.
3. **El mazo no baja de ~721 mm.** Entonces la T no cabe con el lazo declarado.
   El plan B existe pero no es gratis: bajar el reloj es legal por contrato,
   pero con el lazo de 8 kHz el piso es 8,70 MHz — pagarlo exige bajar la
   cadencia del lazo, o sea renegociar `latencia_mano_budget.py`, no girar una
   perilla suelta. Cierra: la decisión de layout de fila, en el case, con su
   propuesta — negociada contra el 721 real, no contra el 600 de la rejilla.
4. **Dos micros interpretando la misma trama pueden divergir** (versiones,
   parse). Mitigado por D7 (una imagen). Cierra: test de que el binario es
   idéntico y el comportamiento difiere solo por strap; puerta local, porque
   CI no hay.
5. **La escucha de la columna B es firmware nuevo**: receptor de solo-escucha
   delimitado por CS y de largo variable (cambio 1 de orquestación §8), con
   `j2.rs` como caso legado de 72 bits. Un oyente clavado a 72 bits quedaría
   sordo al bloque de tono de 288 bits (R-M4) que este mismo papel asevera en
   `trama_j2_budget.py`. Cierra: se escribe contra el framing del cambio 1 y
   su test; el bring-up la sonda con la trama real.
6. **El reset caliente no borra los DACs** (§4.2): entre el reboot y el paso 2
   del rearranque, los CV retienen su último valor con el sonido ya cortado
   por OE. Queda una decisión de cobre nombrada: atar el /RESET de los
   conversores al estado RUN de su micro, o aceptar la ventana con su cota.
   Cierra: la decisión en el pase de cobre del módulo, y la mutación de
   tiempo-hasta-silencio con la cota declarada.

---

## 11. Lo que este papel NO decide

- **El formato del evento de nota.** Pase siguiente, ya desbloqueado: sus tres
  decisiones de requisito están tomadas (destino direccionable; campo de borde
  abre/cierra/dispara; solo lo instantáneo) y su riesgo 1 acaba de cambiar de
  forma. Con él, `ataque_budget.py`/`evento_budget.py`.
- **El layout de fila** que compra los ~17 mm. Case, propuesta aparte.
- **De qué columna cuelga el crosspoint.** #171, por geometría. D8 fijó el bus
  y el deber; la columna no.
- **Si los módulos 5/6/7 llevan micro propio.** Sigue abierto en núcleo §10;
  este papel conserva el alcance local de su antecesor.
- **La decisión abierta 3 de orquestación** (silencio de barrido: módulo o
  columna). Sigue con su criterio de bring-up; D6 solo constata que ya no
  necesita mensajero.
- **Las decisiones abiertas 2 y 4 de orquestación.** Intactas.
- **Las cifras de los umbrales** (latidos, perro, cota de silencio) y el
  enumerado de `estado de columna`: se fijan en el plan y el descriptor, con
  derivación — este papel solo exige que existan.
- **La ranura funcional de los bloques E-3/E-5/E-6** (relator, mixer y oídos,
  paneo): al escribir el descriptor, con el censo vivo delante (D4).

---

## 12. Acta de la sesión (2026-08-25)

Decisiones tomadas por Samuel en conversación, con las alternativas a la vista:

1. **Recuperación: perro propio, orden por el bus.** Rechazadas: «llave en la
   cabecera» (conservaba un hilo asimétrico y dejaba a la cabecera sin quién
   la reiniciara) y «reset cruzado» (más cobre, arbitraje, abrazo mortal).
2. **Ranuras: funcionales, nunca por micro.** Rechazadas: «una con índice
   repartido» (dos semánticas en un campo, el patrón de JackId #157) y «una
   por micro» (prohibida además por R-S1).

Decisiones de diseño del operador, presentadas en la conversación o derivadas
en la junta de verificación de este papel, todas vetables:

- El nombre «cabecera» (D2).
- El crosspoint al bus privado, con dos opciones del #171 muertas en voz alta
  (D8 — la conversación lo atribuyó primero a E-3; la junta lo corrigió: E-3
  no lo decidía, lo decidió este papel).
- La vuelta por sondeo de la cabecera (D5).
- La imagen única con strap (D7).
- El dueño único del canal de ancho de pulso: la cabecera (D6 — corrige el
  borrador, que lo repartía entre ambos contra el cobre de dieciséis §11).
- La instancia de la ranura M como *sitio* declarado (D4).
- La alimentación del perro con dos condiciones (D3 — corrige el borrador, que
  solo miraba el lazo de trama y dejaba el núcleo 1 sin vigilar).
- La política del cerebro ante un módulo presente-y-mudo (§4.3).

Origen del encargo: decisión de Samuel del 2026-08-24 — *«prefiero cambiar
toda la arquitectura, no quiero que haya un microcontrolador al que le lleguen
más tarde los mensajes»* — tras el veredicto de `enlace_budget.py` (PR #198,
issue #199).
