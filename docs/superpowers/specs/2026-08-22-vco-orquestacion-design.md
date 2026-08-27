# Módulo 3 v2 — orquestación: cómo se comporta en el tiempo y qué le exige al núcleo

> Hermano de
> [`2026-08-22-modulo-3-vco-dieciseis-design.md`](2026-08-22-modulo-3-vco-dieciseis-design.md),
> que es el cobre. Aquí no hay ni una pieza: hay arranque, ciclo de vida,
> protocolo, cadencias, modelo de parámetros y **la lista de cambios que el
> núcleo digital necesita para que este módulo sea implementable**.
>
> Origen: [`2026-08-22-junta-vco-hallazgos.md`](2026-08-22-junta-vco-hallazgos.md)
> §4. Ese documento verificó contra el código que ya corre en `software/nucleo/`
> que **el módulo de dieciséis no es implementable contra el firmware que hoy
> existe**, y ese trabajo no estaba contabilizado en ningún sitio.
>
> Sustituye, junto con el spec del cobre, al contrato de módulo de voz, que se
> disolvió en la misma junta:
> [`2026-08-22-contrato-modulo-voz-design.md`](2026-08-22-contrato-modulo-voz-design.md).

## 0. Qué es esto, y sobre todo qué no es

**Dentro:** el arranque del módulo y su handshake, el barrido de afinado y su
transacción, los modos de fallo y cómo se hacen visibles, el modelo de
parámetros de este módulo con sus ámbitos y sus exclusiones, las cadencias, la
regla de bus que sobrevive del contrato disuelto, y **§8: los catorce cambios que
el núcleo digital necesita, en orden de dependencia, cada uno con el archivo y la
línea que lo contradice hoy.**

**Fuera:** piezas, geometría, presupuestos eléctricos y bring-up de placa — eso
es el spec del cobre. Y el código: aquí está lo que el firmware tiene que
cumplir, no cómo se escribe.

## 1. La consecuencia que ningún documento contabilizaba

El módulo de dieciséis no es un proyecto de hardware. Es un proyecto de hardware
**más una revisión del núcleo digital**. Siete supuestos del spec original chocan
con el código que ya está verde en `software/nucleo/`:

| Lo que el spec asumía | Lo que dice el código hoy | Archivo |
|---|---|---|
| «La trama de 72 bits deja de estar clavada» | `N_DACS = 3`, `BITS_TRAMA = N_DACS * 24`, y un test asevera `BITS_TRAMA == 72`. El cerebro **compone palabras de AD5686R él mismo** | `software/nucleo/core/src/j2.rs:33-36`, test en `:137` |
| «Lo que no se pudo medir se reporta como hueco» | `TuneProgress { voz: u8, cents_x100: i16, hecho: bool }` — **no existe representación de hueco**. Cero significa «afinado perfecto» | `software/nucleo/core/src/protocolo.rs:76` |
| Dieciséis osciladores direccionables, más sensores y salud | `MAX_INSTANCIAS = 16`. Consumido **exacto** por los osciladores | `software/nucleo/core/src/param.rs:9` |
| Un preset carga cientos de parámetros | `MAX_RESPUESTAS = 4` | `software/nucleo/core/src/servidor.rs:31` |
| «El cerebro se entera» cuando entra un cable | El mensaje `Jacks` tiene **carga útil cero**, y no existe ningún parámetro de ocupación | `software/nucleo/core/src/protocolo.rs:77`; `medidas.rs` no define ninguno |
| El conteo de voces sale del descubrimiento | `Placa.voces` es **constante de catálogo**, fijada en compilación e indexada por tipo de placa | `software/nucleo/core/src/descubrimiento.rs:106-107`, `:117-122`, `:132` |
| El blob de calibración son 2688 B | El largo del blob es un `u8` en la cabecera: techo absoluto 255 B, y `FIN_ZONA_LIBRE = 0xFA` lo baja a 238 | `software/nucleo/core/src/descubrimiento.rs:87`, `:34`, `:89` |

Y hay una raíz debajo de todas, que la revisión ontológica de la junta enunció
así:

> **Un sistema que quiere ser gobernable por un agente tiene que alojar el
> esquema en el mismo objeto cuyo ciclo de vida el esquema describe.**

Hoy el módulo **se identifica pero no se describe**: el núcleo §3.5 monta el mapa
de parámetros buscando el tipo de placa en una tabla que vive en el firmware del
cerebro (`descubrimiento.rs:117-122`), la escribe una persona a mano, y **no hay
mecanismo que detecte que divergió**. Cada juguete que este módulo añade es una
línea más de ese mantenimiento. La memoria de 32 KB del cobre §13 existe para
atacar eso, y el cambio 4 de §8 es lo que la usa.

## 2. Arranque: el handshake maestro-esclavo

### 2.1 El problema, en dos frases

**El descubrimiento prueba que existe una memoria, no que exista un procesador.**
El cerebro barre el mux I²C, lee la EEPROM y publica dieciséis voces — y todo eso
funciona igual si ningún micro del módulo ha ejecutado una sola instrucción.

Y hoy **no hay línea de reset ni de arranque-OK al esclavo**: un esclavo colgado
solo se recupera apagando la caja con la mano.

### 2.2 La secuencia

El cobre pone dos señales con reposo garantizado por hardware (cobre §9):
`RESET_ESCLAVO` (maestro → esclavo, en reposo **afirmado**) y `OK_ESCLAVO`
(esclavo → maestro, en reposo **no arrancado**). Encima corre esto:

| Paso | Quién | Qué pasa | Estado audible |
|---|---|---|---|
| 0 | Hardware | `OE` de los registros en alta impedancia por pull-up; pulls por línea al estado seguro | **Silencio**, sin firmware |
| 1 | Maestro | Arranca, se comprueba, baja `OE` de su columna | Sus 8 osciladores gobernables |
| 2 | Maestro | Suelta `RESET_ESCLAVO` | — |
| 3 | Esclavo | Arranca, se comprueba, afirma `OK_ESCLAVO`, baja `OE` de su columna | Sus 8 osciladores gobernables |
| 4 | Maestro | Publica `estado del esclavo = arrancado` | El módulo entero |

Y las reglas que hacen que eso valga de algo:

> **R-A1. Sin descriptor no hay capacidades.** El cerebro publica la **identidad**
> del módulo en cuanto la EEPROM responde, pero **no publica ni un parámetro**
> hasta que el módulo le sirva su descriptor (cambio 4 de §8). Un módulo con
> identidad y sin descriptor aparece como presente y mudo, que es la verdad.

> **R-A2. Los parámetros del esclavo no existen mientras el esclavo no arranque.**
> Los ocho osciladores de su columna se publican con `hueco: esclavo no
> arrancado` en sus medidas y **rechazan escritura** con `ERROR`, en vez de
> aceptarla y no hacer nada.

> **R-A3. El reset es alcanzable desde el modelo.** Existe una operación
> `reiniciar el esclavo` como parámetro de solo escritura del módulo. Por §2.1
> del núcleo, lo que no está en el modelo no existe — y un esclavo que solo se
> recupera apagando la caja no está en el modelo.

> **R-A4. Reiniciar el esclavo silencia su columna primero.** El maestro afirma
> `RESET_ESCLAVO`, lo que devuelve `OE` a alta impedancia y con él los pulls al
> estado seguro. No hay ventana en la que ocho osciladores queden sonando con la
> ruta a medio escribir.

> **ENMENDADA el 2026-08-27** — rescatada del PR #201, que se cierra sin
> mergear porque su premisa (dos micros en la Voz) murió con el N657. Y
> **corregida en la propia tanda**: la primera redacción decía que el silencio
> de R-A4 «era del encendido», y eso confunde dos cosas distintas.
>
> **No hay `RESET_ESCLAVO` y no hay maestro**: la Voz lleva un solo micro. Pero
> la garantía de R-A4 sobre el **camino audible** se sostiene igual, y por su
> propio mecanismo: soltar el reset devuelve `OE` a alta impedancia y los pulls
> por línea fuerzan el estado seguro. Eso silencia, retenga el DAC lo que
> retenga.
>
> **Lo que sí falta, y no estaba en ningún papel de `main`:** en un reinicio
> **en caliente** los códigos del DAC **se quedan como estaban**. El
> cero-escala lo da `RSTSEL` al encender, y el cobre lo dice sin ambigüedad —
> `hardware/03-vco/kicad/build_schematic.py` declara que `RESET` está
> **permanentemente inactivo porque el J2 no lleva esa línea**, y
> `notes/bring-up.md` solo comprueba el cero «al arrancar» y confirma que las
> únicas salidas son el comando `0110` o ciclar la alimentación.
>
> O sea que el invariante que hay que verificar **no es «el DAC está a cero»
> sino el ORDEN**: escribir el estado de reposo en DAC y registros **antes** de
> soltar la inhibición atada a reset o `OE`. Si se suelta primero, hay una
> ventana con códigos viejos sonando — y esa ventana es justo la que R-A4 daba
> por cerrada sin decir en qué orden.
>
> El sucesor vigente es **R-M5** (`2026-08-26-motor-digital-design.md` §7):
> «el silencio no depende del software», con inhibición atada a reset. Esta
> enmienda no lo sustituye: le añade el **requisito de orden** que ni R-A4 ni
> R-M5 escriben, y que el «reset caliente» —caso que no existía declarado en
> ningún papel antes de hoy— es el único que lo saca a la luz.

### 2.3 Y el maestro, quién lo vigila

~~Nadie desde dentro, y por eso el mecanismo es el mismo de R-A1: **si el
maestro no arranca, no hay descriptor**, y el cerebro publica el módulo como
identidad sin capacidades. Es un modo de fallo declarado, no silencioso.~~

> **DEROGADA el 2026-08-27** — rescatada del PR #201, que la cazó y se cierra
> sin mergear.
>
> **Esa vigilancia nunca funcionó, y no por el cambio de chip.** El mecanismo
> se apoyaba en «si el maestro no arranca, no hay descriptor», y el **cambio 4
> de este mismo papel** (§8) ya había mudado el descriptor a la memoria del
> módulo, que **el cerebro lee sin ayuda de ningún procesador** (§2.1 de aquí
> mismo lo dice: lee la EEPROM aunque ningún procesador del módulo haya
> arrancado). Así que un módulo con el micro muerto publicaba sus capacidades
> igual: la ausencia de descriptor no era señal de nada.
>
> **Lo que hace falta en su lugar**, y hoy no existe en `main`: un detector de
> **presente y mudo** visible para el cerebro — identidad que responde, EEPROM
> que se lee, y micro que no habla. R-A1 ya nombra el estado; lo que falta es
> quién lo declara y cómo.
>
> Y con él, la política que ningún papel tenía y el #201 escribió: **el cerebro
> sigue emitiendo trama a un módulo presente y mudo mientras su identidad
> responda.** Sin esa política, el silencio del cerebro mata de rebote a un
> módulo que solo estaba callado.
>
> **Contradicción viva que este rescate deja señalada, no resuelta:** la spec
> dice que el descriptor vive en la memoria del módulo (cambio 4), y
> `software/nucleo/core/src/descubrimiento.rs` dice lo contrario — que la
> EEPROM pequeña solo lleva identidad y calibración, y que el descriptor sale
> del catálogo del firmware del cerebro. Dos artefactos vivos, dos respuestas.
> Se abre como issue en esta misma tanda.

## 3. El barrido de afinado

### 3.1 Lo que ya está resuelto y no se toca

El conteo recíproco vive en los micros del módulo (cobre §7.3), con los 6,67 ns
de sellado derivados del reloj y los 131 ns de jitter máximo del 74HC14 (núcleo
§5.1). **El cerebro conserva el criterio**: cuándo afinar, qué hacer con los
números, cuándo dar un oscilador por malo. El módulo aporta **la medida**, no el
juicio.

Del presupuesto del núcleo se puede derivar cuántos periodos mide por nota, y
conviene tenerlo escrito porque el timeout cuelga de ahí:

> 84 notas de C1 (32,703 Hz) a C8, midiendo *k* periodos cada una:
> Σ 1/f = 0,5406 s. Con el barrido completo en **2,7 s**, *k* = **5 periodos por
> nota**.

### 3.2 El barrido no se degrada: se cuelga. Timeout y hueco

`autotune_budget.py` calcula el tiempo de medida desde la frecuencia **esperada**
y **no tiene timeout**. Un oscilador con el sync alto está parado —el datasheet
lo dice: *«if held high it stops the oscillator»*— y no da flancos nunca. Hoy eso
no es una medida mala: es un barrido que no termina.

**La regla:**

> **R-B1.** Cada nota tiene un timeout de `3 × ventana esperada`, con un **suelo
> de 300 ms**. El suelo cubre cinco periodos de cualquier cosa que oscile por
> encima de 16,7 Hz; por debajo de eso el oscilador está fuera de cualquier rango
> usable y «sin flancos» es el veredicto correcto.

> **R-B2.** Tras **tres huecos consecutivos** en un mismo oscilador, se abandona
> ese oscilador para el resto del barrido y se reporta entero como hueco. Sin
> esto, un módulo muerto tarda 25 s en decirlo.

Lo que eso hace al peor caso, que es lo que `autotune_budget.py` tiene que
asever al mudarse:

| | Tiempo |
|---|---|
| Barrido normal, 16 osciladores en paralelo | **2,70 s** |
| Timeout de la nota más grave (3 × 5/32,703 Hz) | 0,459 s |
| Timeout de cualquier nota por encima de 50 Hz (suelo) | 0,300 s |
| **Peor caso: barrido + tres timeouts del oscilador afectado** | **≤ 4,08 s** |

### 3.3 El hueco tiene motivo, y el motivo es la lista de fallos

`TuneProgress` gana un resultado que no es un número (cambio 5 de §8), y sus
motivos son cerrados:

| Motivo | Cuándo |
|---|---|
| `sin flancos` | Venció el timeout de R-B1 |
| `fuera de rango` | Midió, pero fuera de lo que la tabla puede corregir |
| `oscilador silenciado` | Su silencio estaba afirmado por política o por fallo |
| `sync retenido` | El enrutado de sync lo tenía parado y la transacción no pudo desmontarlo |
| `esclavo no arrancado` | R-A2 |
| `placa muda` | El sensor o el convertidor de esa placa no responde |

**Cero deja de significar «afinado perfecto» por omisión.** Hoy sí lo significa,
y esa es la razón por la que nueve modos de fallo son invisibles (§4).

### 3.4 El barrido vuelve a ser silencioso, y es una decisión

`architecture-poly.md` §5 justificaba el barrido silencioso porque el VCA está
cerrado. Con dieciséis salidas a jacks, cualquier cable patcheado hace audible un
barrido de 2,7 s de notas cromáticas.

El cobre §9 devuelve la propiedad —silenciador por oscilador, con el camino de
afinación **antes** del silenciador— y aquí se decide cómo se usa:

> **R-B3.** El barrido afirma el silencio de los dieciséis osciladores durante
> toda su duración y lo levanta al terminar. La política es un parámetro
> compartido, `silenciar durante el barrido`, por defecto **activo**.

> **R-B4.** El barrido no arranca solo mientras haya notas sonando. `TUNE_START`
> lo pide un cliente, y si hay voces activas el instrumento responde `ERROR` en
> vez de silenciar el instrumento en medio de una frase.

### 3.5 La deriva contamina la medida, y ya se sabe quién la congela

El corolario que el spec del cobre escribe —«el autoafinado corrige la afinación,
no el desafinado pedido»— gobierna la **escritura**. La contaminación está en la
**lectura**: el autoafinado mide frecuencia, y la deriva *es* una divagación de
frecuencia. Ningún documento decía quién la congela.

Como la deriva la genera el cerebro (§5.2), la respuesta es directa:

> **R-B5.** El cerebro congela la deriva de los dieciséis osciladores al abrir la
> transacción de barrido y la reanuda al cerrarla. El desafinado fijo **no** se
> congela: es un corrimiento constante durante toda la medida y la tabla lo
> absorbe igual que absorbe cualquier otro término estático.

### 3.6 La transacción: sin ella hay actualización perdida

El barrido tiene que desmontar el enrutado —sync a ninguno, modulación a ninguno,
índices a cero— y restaurarlo al terminar. Sin primitiva de transacción, un `SET`
del agente durante esos 2,7 s lo pisa la restauración, y **el cliente no puede
distinguir una restauración interna de una escritura suya**.

**No hace falta un mensaje nuevo.** El núcleo ya tiene la máquina de retención
(`software/nucleo/core/src/retencion.rs`, con `PENDING` y `RESOLVED`) para la
confirmación física de §2.2. Se reutiliza:

> **R-B6.** Al abrir la transacción, el cerebro toma un **cerrojo** sobre el
> conjunto declarado de parámetros: enrutado de sync, enrutado de modulación,
> índices de FM y de anillo, deriva y silencio de los dieciséis.

> **R-B7.** Un `SET` sobre un parámetro con cerrojo **se retiene**, no se
> rechaza: el cliente recibe `PENDING{token}` y, al cerrar la transacción,
> `RESOLVED{token, confirmado: true}`. Así sabe exactamente cuándo aterrizó su
> escritura.

> **R-B8. El orden al cerrar es restaurar primero y aplicar lo retenido
> después**, en orden de llegada. Al revés, la restauración se comería la
> escritura del cliente, que es justo el fallo que esto evita.

> **R-B9.** Si la retención se desborda, el excedente se rechaza con `ERROR`.
> **Nunca se descarta en silencio.** La capacidad se declara y se asevera en el
> códec, no se deja al azar.

Y una medida para que el cerrojo sea visible sin tener que chocar contra él:
`barrido en curso`, solo lectura, en el ámbito de módulo.

## 4. Fallar en voz alta: los once modos de fallo

El instrumento tiene como principio declarado fallar en voz alta (núcleo §6.1).
De los once modos de fallo de este módulo, **nueve son hoy invisibles para el
resto del instrumento**.

| # | Modo de fallo | Hoy | Cómo se hace visible |
|---|---|---|---|
| 1 | El módulo entero desenchufado | **visible** | Barrido I²C, mensaje `MODULES` |
| 2 | Un oscilador fuera del span | **visible** | Barrido, y la cabeza local ya lo muestra (núcleo §5.2) |
| 3 | El maestro no arranca | invisible | R-A1: identidad sin descriptor, publicada como tal |
| 4 | El esclavo no arranca | invisible | R-A2 + medida `estado del esclavo` + hueco en sus ocho |
| 5 | Un oscilador que no oscila | invisible | Hueco `sin flancos` (R-B1) |
| 6 | Un oscilador con sync retenido | invisible | Hueco `sync retenido` + timeout (§3.3) |
| 7 | Un conversor mudo en el SPI privado | invisible | El micro verifica lectura de retorno y publica hueco en los parámetros de ese conversor |
| 8 | La referencia caída o fuera de tolerancia | invisible | Medida `tensión de la referencia`, leída por el ADC del maestro a través del mux del cobre §7.1 |
| 9 | Un sensor de temperatura mudo | invisible | Hueco en esa medida, no un valor por defecto |
| 10 | Una placa de voces ausente o muerta | invisible | Cada placa tiene sensor propio; sin respuesta, hueco en sus cuatro osciladores |
| 11 | Descriptor o calibración corruptos | invisible | Se rechaza con `ERROR` declarado y el módulo queda como identidad sin capacidades. Hoy el blob que invade el EUI-48 se rechaza **en silencio** (`descubrimiento.rs:89`) |

La regla que los unifica, y que es la Regla 6 del contrato disuelto, ahora con un
sitio donde vivir:

> **R-F1. Lo que no se pudo medir se reporta como hueco, con su motivo. Nunca un
> valor por defecto que parezca una medida.** Un cero silencioso consigue no
> medir *y* que nadie se entere.

## 5. El modelo de parámetros de este módulo

### 5.1 El censo

| Bloque | Ámbito | Entradas | Escribibles |
|---|---|---|---|
| Desafinado, mezcla de formas, índice de FM/PM, índice de anillo | `por-voz` | 4 × 16 = 64 | 64 |
| Fuente de sync, tipo de sync, fuente de modulación, modo de modulación | `por-voz` | 4 × 16 = 64 | 64 |
| Dirección de la sierra, carácter del PWM, modo del oscilador, silencio | `por-voz` | 4 × 16 = 64 | 64 |
| Amplitud de deriva, velocidad de deriva | `por-voz` | 2 × 16 = 32 | 32 |
| Ancho de pulso; silenciar durante el barrido | `compartido` | 2 | 2 |
| Frecuencia medida, ocupación de entrada, ocupación de salida, valor de la entrada | `por-voz`, medida | 4 × 16 = 64 | 0 |
| Temperatura de cada placa | por placa, medida | 4 | 0 |
| Estado del esclavo, barrido en curso, voces aportadas, tensión de la referencia | módulo, medida | 4 | 0 |
| **Total** | | **298** | **226** |

Dos consecuencias que salen de ahí y que están en §8:

- **Un preset de este módulo son 226 valores.** Contra `MAX_RESPUESTAS = 4`
  (`servidor.rs:31`), el desbordamiento es de **cincuenta y seis veces**, y no es
  un margen que se ajuste: es una estructura que no aguanta la operación.
- **Setenta y dos entradas del censo no son voces** (medidas de placa, de módulo
  y compartidas), y `MAX_INSTANCIAS = 16` (`param.rs:9`) está consumido exacto
  por los dieciséis osciladores. No tienen dónde vivir.

### 5.2 Quién genera qué: un solo interpolador

El contrato disuelto autorizaba al módulo a *«interpolar, suavizar un salto,
sostener un portamento»*, y el cerebro **ya tiene rampas implementadas**
(`software/nucleo/core/src/rampa.rs`). Con los dos encendidos, el tiempo de glide
no es parámetro de nada — y **una rampa de duración cero, que el núcleo §4.1
define como salto deliberado, la destruye un suavizado que vive fuera del
modelo**.

> **R-M1. El módulo no interpola.** Aplica lo que recibe, cuando lo recibe. El
> glide, el portamento y todo suavizado viven en el cerebro y en un solo sitio.

> **R-M2. La deriva y el desafinado los genera el cerebro** y llegan ya sumados
> al tono. Es lo que hace que congelarlos durante el barrido (R-B5) sea una línea
> y no una negociación entre dos firmwares.

> **R-M3. El orden de suma es: corrección del autoafinado, luego desafinado,
> luego deriva.** Son tres capas distintas —la primera quita el error que nadie
> quiso, las otras dos añaden el que sí— y el firmware las suma en ese orden,
> nunca dejando que la primera se coma a las otras.

### 5.3 La cadencia de la trama, y por qué 100 Hz no alcanza

R-M1 tiene un precio: si el módulo no suaviza, el cerebro tiene que mandar los
pasos lo bastante juntos como para que no se oigan. El núcleo §3.6 presupuesta
100 Hz por parámetro, y a 100 Hz un portamento de una octava en un segundo son
**12 cents por paso**, que se oyen como escalones.

Con la trama desacoplada del AD5686R (cambio 1 de §8), el módulo puede recibir
**los dieciséis tonos en una sola trama**, y eso cambia la cuenta entera:

| | Trama | Tasa | Ocupación del SPI a 10 MHz |
|---|---|---|---|
| Hoy (núcleo §3.6): 16 voces × 3 dimensiones, trama de 72 bits | 72 bits | 100 Hz | 3,46 % |
| **Bloque de tono del módulo: 16 × 16 bits + cabecera** | 288 bits | **1 kHz** | **2,88 %** |

> **R-M4. La tasa mínima del bloque de tono es 1 kHz por módulo.** A esa tasa, un
> portamento de una octava en 400 ms da 3 cents por paso, que es el suelo
> conservador de audibilidad para un tono en movimiento. Y **cuesta menos ancho
> de banda que el esquema de hoy**, porque agrupa.

`trama_j2_budget.py` (§10) lo asevera con todos los módulos declarando su tasa a
la vez.

### 5.4 Cuándo se puede cambiar una ruta

Cambiar un selector de la matriz hace clic, por inyección de carga del
multiplexor (cobre §8).

> **R-M5.** Un cambio de fuente de sync o de fuente de modulación se aplica en el
> siguiente `note off` de ese oscilador, o inmediatamente si el oscilador está
> silenciado o en reposo. Un cliente que quiera el cambio inmediato lo pide con
> el silencio afirmado y asume el clic.

Esto **no** aplica a los índices ni al ancho de pulso, que son continuos y se
mueven cuando se quiera.

### 5.5 El conteo de voces depende del preset, y hoy las dos salidas son malas

`Placa.voces` es constante de catálogo (`descubrimiento.rs:106-107`, `:117-122`),
así que hoy el módulo solo puede declarar un número fijo. **Los dos números
posibles son incorrectos y silenciosos**:

- Declarar **dieciséis** manda notas a osciladores que el preset está usando de
  moduladoras.
- Declarar **ocho** deja la mitad del hardware inalcanzable en modo limpio.

> **R-M6. Las voces que este módulo aporta salen del estado, no del catálogo.**
> Un oscilador cuenta como voz si no está en modo lento **y** no es la fuente de
> modulación de ningún otro. El módulo publica `voces aportadas` como medida.

> **R-M7. `voces aportadas` emite `CHANGED` cuando cambia**, y el cerebro rehace
> el reparto de voces. La regla del mínimo de la cadena del núcleo §3.6 sigue
> valiendo tal cual: con 16 osciladores en pares de FM y 4 filtros, el
> instrumento tiene 4 voces y **lo dice**.

> **R-M8.** Un cambio de conteo por carga de preset libera las notas que estén
> sonando en osciladores que pasan a ser moduladores. Se hace en la carga, no a
> mitad de una nota.

## 6. Las veintiséis relaciones entre parámetros

El spec original escribía una —la sierra contra la FM que cruza el cero— y **el
descriptor no tiene campo para expresar ninguna** (`descriptor.rs:83-102`: id,
nombre, tipo, ámbito, cuatro banderas, mín/máx/def, unidad y etiquetas; nada
más).

Aquí está el censo entero, en cuatro clases.

### 6.1 Excluyentes por hardware — el modelo las impide

| # | Relación | Por qué |
|---|---|---|
| E1 | `dirección de la sierra` ↔ `modo de modulación = TZFM/TZPM` | Mismo pin `TIME REVERSE`, gobernado por el LM311 (cobre §10.2) |
| E2 | `fuente de sync ≠ ninguna` ↔ medir esa voz en el barrido | El sync alto para el oscilador (datasheet); es el hueco `sync retenido` |
| E3 | `modo del oscilador = lento` ↔ que ese oscilador reciba notas | Es un modulador, no una voz (R-M6) |
| E4 | `silencio afirmado` ↔ que ese oscilador suene | Es la condición de arranque de R-A2 y del barrido de R-B3 |
| E5 | `estado del esclavo ≠ arrancado` ↔ los parámetros de sus ocho osciladores | R-A2 |
| E6 | `barrido en curso` ↔ escritura directa sobre los parámetros con cerrojo | R-B6, y se retiene en vez de rechazarse |

### 6.2 Valores ilegales — el modelo los rechaza con `ERROR`

| # | Relación |
|---|---|
| I1 | `fuente de sync[v] = v` — autosincronía |
| I2 | `fuente de modulación[v] = v` — automodulación |
| I3 | Ciclo en el grafo de sync (A sincroniza a B y B a A, directa o indirectamente) |
| I4 | Ciclo en el grafo de modulación |
| I5 | `fuente de sync` apuntando a un oscilador con el silencio afirmado |
| I6 | `fuente de modulación` apuntando a un oscilador con el silencio afirmado |

### 6.3 Degradaciones — el modelo las declara, no las impide

| # | Relación | Qué pasa |
|---|---|---|
| D1 | `fuente de sync ≠ ninguna` → afinación de esa voz | Deja de ser tono y pasa a ser timbre |
| D2 | `fuente de sync ≠ ninguna` → desafinado y deriva de esa voz | Dejan de oírse: la frecuencia la manda el maestro de sync |
| D3 | `tipo de sync = suave` + índice de FM alto | El sync suave pierde agarre |
| D4 | `modo de modulación = FM` (no cruza el cero) con índice alto | Desafina la nota. Con PM no (cobre §10.4) |
| D5 | `carácter del PWM = sierra` + `dirección de la sierra` | El vibrato propio del efecto cambia de signo |
| D6 | `ancho de pulso` (compartido) + `carácter del PWM` (por voz) | El mismo CV significa cosas distintas en cada oscilador |
| D7 | `amplitud de deriva > 0` → `frecuencia medida` | Contamina la medida; por eso R-B5 la congela |
| D8 | `modo del oscilador` de la **fuente** = lento → la modulación | Se oye como vibrato, no como timbre |
| D9 | Cable en la entrada de control → tono que manda el cerebro | Se **suman**, no se sustituyen: el cerebro no pierde el control, lo comparte |
| D10 | `modo del oscilador = lento` → la tabla de 84 notas | No aplica a ese oscilador |
| D11 | `índice de anillo` alto → `mezcla de formas` de esa voz | Deja de oírse como tal |

### 6.4 Relaciones de orden — el modelo declara la secuencia

| # | Relación |
|---|---|
| O1 | Corrección del autoafinado **antes** de `desafinado` (R-M3) |
| O2 | `desafinado` **antes** de `deriva` (R-M3) |
| O3 | `silencio` **por encima** de todo lo demás (cobre §9) |

**Veintiséis.** El campo que el descriptor necesita para expresarlas es el cambio
13 de §8, y su forma está ahí: una tabla por ranura, no un campo por instancia,
porque estas veintiséis son relaciones **entre tipos de parámetro** y multiplicar
por dieciséis instancias sería guardar dieciséis veces lo mismo.

## 7. El bus J2: lo que sobrevive del contrato disuelto

El contrato de módulo de voz se disolvió (ver su documento). Dos de sus reglas
eran interfaz real y siguen valiendo, con una corrección de alcance en la
segunda.

> **R-J1. El `MISO` del J2 lo suelta quien hable en esa ranura, y en alta
> impedancia siempre que su `CS` esté alto, sin excepciones de modo.** Se mide en
> el bring-up: `CS` alto, `MISO` sondado, aprobado o suspenso.

Esto cierra el hueco que el spec del cerebro §4.1 daba por perdido —*«una
resistencia de serie no evita la pelea, la hace sobrevivible; lo que evita la
pelea vive en placas que todavía no se han dibujado»*—. Y está enunciado **sin
presuponer un micro**, a propósito: un registro de desplazamiento que suelte bien
la línea también cumple.

> **R-J2. Qué cuelga del J2 en cada ranura lo decide el diseño de esa placa.** En
> el módulo 3 v2 cuelga un micro y los conversores viven en un SPI privado (cobre
> §2, decisión 3). **Eso es una decisión del módulo 3 v2, no una ley.**

La corrección importa: el contrato disuelto convertía R-J2 en obligación
universal y con eso **cerraba por decreto una decisión que el núcleo §10 dejó
abierta a propósito** —si los módulos 5/6/7 llevan micro propio o se resuelven
con registro de desplazamiento y ADC en la cadena SPI—. Esa decisión **sigue
abierta**, se cierra al dibujar el módulo 5, y el núcleo ya explicó por qué se
puede aplazar sin riesgo: **las dos opciones caben en el J2 congelado**.

Lo que R-J2 sí compra en este módulo, y hay que decirlo porque es la razón del
cambio 1 de §8:

- La pelea del `MISO` se acaba de raíz en esta ranura.
- **La trama de 72 bits deja de estar clavada.** Era el tamaño de la cadena de
  tres conversores de la v1: un número de una placa concreta metido en una
  interfaz común.
- **Cuántos conversores lleva el módulo deja de ser asunto del cerebro.**

Y lo que cuesta: **una etapa más de latencia** entre lo que el cerebro manda y lo
que el chip recibe. Irrelevante para el tono; **no irrelevante para un disparo**.
Riesgo 1 de §9.

Del contrato disuelto también sobreviven, ya sin envoltorio de «contrato», estas
cuatro reglas de cadencia, que pasan a ser de este módulo:

> **R-J3. El módulo nunca habla sin que le pregunten.** El J2 es un bus con ocho
> ranuras; un módulo que hable por su cuenta se pelea con otro.

> **R-J4. Las medidas son parámetros de primera clase, no un canal aparte.**
> Entran por el mismo camino que cualquier otro parámetro, con su descriptor
> (núcleo §3.4).

> **R-J5. El conteo de voces lo dice el descriptor, nunca una constante.**
> Refinado por R-M6: en este módulo, además, sale del estado y cambia con el
> preset.

> **R-J6.** Es R-F1: lo que no se pudo medir se reporta como hueco, con su
> motivo.

### 7.1 Qué reporta el módulo, y con qué cadencia

| Clase | Qué | Cuándo | Cadencia |
|---|---|---|---|
| **Medida de calibración** | La frecuencia real de cada oscilador | Solo durante un barrido, y lo pide el cerebro | A petición |
| **Estado del patch** | Qué jacks tienen cable; el valor de cada entrada de control | Al cambiar, y en el barrido de arranque | **Sondeo cada 50 ms**, notificación al cambiar |
| **Salud** | Temperatura de cada placa, tensión de la referencia, estado del esclavo, identidad | Lento y periódico | **1 Hz** |

Los 50 ms del sondeo de jacks salen del tacto: es el orden de lo que una persona
percibe como inmediato al enchufar un cable, y son 20 lecturas por segundo del
mux del cobre §7.1, que corre a cientos de hercios. La cadencia se **declara en
el descriptor**, no se deja implícita (cambio 6 de §8).

## 8. Los catorce cambios que el núcleo necesita, en orden de dependencia

Esta es la sección que importa. Cada cambio dice qué hay que hacer, por qué, **la
línea del firmware de hoy que lo contradice**, y cómo se cierra.

El orden es de dependencia: los del bloque 0 bloquean a todos los demás.

### Bloque 0 — sin esto el módulo no se puede ni direccionar ni hablar

**1. Desacoplar la trama del J2 del AD5686R.**
Hoy el cerebro compone palabras de AD5686R él mismo: `N_DACS = 3`,
`BITS_TRAMA = N_DACS * 24`, `CMD_ESCRIBIR_Y_ACTUALIZAR`, `Canal` one-hot.
Contradice: `software/nucleo/core/src/j2.rs:33-36`, y el test
`la_trama_son_nueve_bytes_en_el_orden_congelado` asevera `BITS_TRAMA == 72` en
`:137`.
Qué hace falta: la trama pasa a llevar **parámetros con su identificador**, no
palabras de un chip concreto; el largo lo declara el módulo en su descriptor. El
bloque de tono va agrupado, para cumplir R-M4.
Cierra: el códec nuevo con su test de ida y vuelta, y `trama_j2_budget.py`
aseverando la ocupación con todos los módulos a su tasa declarada. **El test de
72 bits no se borra: se convierte en el caso «módulo con tres AD5686R en
cadena», que es la v1 y sigue siendo válido.**

**2. Espacio de direcciones para lo que no es una voz.**
`MAX_INSTANCIAS = 16` y este módulo lo consume exacto con sus dieciséis
osciladores; las 72 entradas de censo que no son voces (§5.1) no tienen dónde
vivir.
Contradice: `software/nucleo/core/src/param.rs:9`.
Qué hace falta: **desacoplar la ranura lógica del canal físico del mux**. El
campo de ranura ya tiene 4 bits y solo existen 8 canales físicos (núcleo §3.1, y
el hueco está ahí a propósito). Un módulo declara cuántas ranuras lógicas publica:
el módulo 3 v2 toma dos —una para los dieciséis osciladores, otra para lo de
placa y lo de módulo—. Con seis módulos y el cerebro, son 8 de 16 ranuras
lógicas.
Cierra: un test que monte el módulo 3 v2 completo y exija que las 298 entradas
del censo sean direccionables y distintas.

**3. Ampliar el techo del blob y quitarlo de la EEPROM de identidad.**
El largo del blob es un `u8` en la cabecera: techo 255 B, y `FIN_ZONA_LIBRE` lo
baja a 238. La calibración de este módulo son 2688 B.
Contradice: `software/nucleo/core/src/descubrimiento.rs:87` (`cab[5] as usize`),
`:34` (`FIN_ZONA_LIBRE = 0xFA`), `:89` (el rechazo).
Qué hace falta: el largo pasa a 16 bits y la calibración se lee de la memoria de
32 KB del cobre §13, en otra dirección I²C del mismo canal. **El `24AA02E48` de
identidad no se toca**, así que el camino de descubrimiento que hoy funciona
sigue funcionando.
Cierra: test con una cabecera de blob de 2688 B, y test de que el rechazo por
invasión del EUI-48 emite `ERROR` en vez de fallar callado (modo de fallo 11 de
§4).

**4. El descriptor lo sirve el módulo, no el catálogo del cerebro.**
Hoy el mapa de parámetros sale de una tabla en el firmware del cerebro, escrita a
mano, sin mecanismo que detecte que divergió de la placa (§1).
Contradice: `software/nucleo/core/src/descubrimiento.rs:117-122` (`CATALOGO`) y
`:100-109` (`Placa.params`).
Qué hace falta: el cerebro lee el descriptor de la memoria del módulo y solo cae
al catálogo si el módulo no tiene descriptor —que es el caso de la v1 y de
cualquier placa vieja—. Esto es lo que ataca la raíz enunciada en §1.
Cierra: test con dos módulos, uno con descriptor propio y otro sin él, exigiendo
que los dos se publiquen y que el segundo se marque como descrito por catálogo.
**Y R-A1**: identidad sin descriptor se publica como presente y mudo.

### Bloque 1 — sin esto el módulo arranca pero miente

**5. Representación de hueco en `TuneProgress`, con su motivo.**
Hoy `cents_x100: i16` no tiene forma de decir «no medí», y cero significa
«afinado perfecto».
Contradice: `software/nucleo/core/src/protocolo.rs:76`.
Qué hace falta: el resultado pasa a ser medida **o** hueco con uno de los seis
motivos de §3.3.
Cierra: test de ida y vuelta del códec para cada motivo, y un test que exija que
un oscilador sin flancos **no** produzca un cero.

**6. Carga útil y parámetro de ocupación para `Jacks`, con cadencia declarada.**
`Jacks` tiene carga útil cero, y no existe ningún parámetro de ocupación en
`medidas.rs`.
Contradice: `software/nucleo/core/src/protocolo.rs:77`.
Qué hace falta: `Jacks` lleva qué módulo y qué cambió; la ocupación de cada jack
es un **parámetro de medida** por voz, para que el agente la lea con `GET` sin
protocolo nuevo (R-J4); y la cadencia de sondeo se declara en el descriptor (los
50 ms de §7.1).
Cierra: test que inyecte cambios de ocupación y exija que salgan por
`GET`/`SUBSCRIBE`, y que la cadencia esté en el descriptor y no escrita a mano en
la app.

**7. Timeout del barrido, con abandono acotado.**
No existe hoy: `autotune_budget.py` calcula desde la frecuencia esperada y no
tiene salida por tiempo.
Qué hace falta: R-B1 y R-B2, con el peor caso de 4,08 s.
Cierra: `autotune_budget.py`, ya mudado al módulo, lo asevera; y un test que
simule un oscilador que no da flancos y exija que el barrido termine con huecos
en vez de colgarse.

**8. Handshake maestro-esclavo, con actuador.**
Hoy no hay reset ni arranque-OK, y el descubrimiento prueba que hay memoria, no
que haya procesador.
Qué hace falta: R-A1 a R-A4, más las medidas `estado del esclavo` y la operación
`reiniciar el esclavo`.
Cierra: test de arranque con el esclavo simulado sin responder, exigiendo que sus
ocho osciladores se publiquen con hueco y rechacen escritura; y el bring-up de
placa con `RESET_ESCLAVO` de verdad.

### Bloque 2 — sin esto el módulo se puede gobernar pero se pisa a sí mismo

**9. Primitiva de transacción para el barrido.**
Sin ella hay actualización perdida y el cliente no distingue una restauración
interna de una escritura suya.
Contradice: nada por línea, y eso es el problema — **no existe**. La máquina que
lo resuelve sí existe: `software/nucleo/core/src/retencion.rs`.
Qué hace falta: R-B6 a R-B9, reutilizando `PENDING`/`RESOLVED`. **Sin mensajes
nuevos.**
Cierra: test que escriba durante un barrido simulado y exija que el valor
sobreviva a la restauración y llegue con su `RESOLVED`.

**10. Congelar la deriva durante el barrido.**
Hoy ningún documento decía quién. Con R-M2 la deriva la genera el cerebro, así
que es suya.
Qué hace falta: R-B5.
Cierra: test que corra un barrido con deriva activa y exija que las 84 medidas de
una voz no lleven su componente.

**11. Un solo interpolador.**
El contrato disuelto autorizaba al módulo a interpolar y el cerebro ya tiene
rampas.
Contradice: `software/nucleo/core/src/rampa.rs` existe y funciona; el conflicto
era con el contrato, no con el código.
Qué hace falta: R-M1 y R-M4 — el módulo no suaviza, y el bloque de tono va a
1 kHz.
Cierra: `trama_j2_budget.py` asevera la ocupación; y un test que exija que una
`Rampa` de duración cero produzca un salto en una sola trama.

**12. El camino de respuesta deja de tener cota constante.**
`MAX_RESPUESTAS = 4` contra los 226 `CHANGED` que emite cargar un preset de este
módulo: desbordamiento de cincuenta y seis veces.
Contradice: `software/nucleo/core/src/servidor.rs:31`.
Qué hace falta: dos caminos, y el segundo es el que se prefiere por barato:
(a) subir la cota a un valor **derivado del censo** y no elegido a ojo; (b) un
`CAMBIADOS` en lote que lleve un tramo contiguo de parámetros, con lo que una
carga de preset emite del orden de una docena de mensajes en vez de 226.
Cierra: test que cargue un preset del módulo 3 v2 completo y exija que ni un
`CHANGED` se pierda, con la cota aseverada contra el censo.

**13. Campo de relación entre parámetros en el descriptor.**
El descriptor lleva id, nombre, tipo, ámbito, cuatro banderas, mín/máx/def,
unidad y etiquetas. **No hay dónde poner ninguna de las 26 relaciones de §6.**
Contradice: `software/nucleo/core/src/descriptor.rs:83-102`.
Qué hace falta: una **tabla de relaciones por ranura** —no un campo por
instancia—, con las cuatro clases de §6 (excluye, ilegal, degrada, ordena) y una
nota en texto escrita para alguien que nunca ha visto el instrumento, porque es
lo que el agente lee (núcleo §2.1).
Cierra: test que intente escribir cada uno de los seis valores ilegales de §6.2
y exija `ERROR`; y test que exija que las 26 estén en el volcado del descriptor.

**14. La cadena de LED tiene un solo dueño.**
El núcleo §5.1 y `architecture-poly.md` §4 la declaran un mazo del cerebro que
encadena todos los paneles; el spec del módulo se la asignaba a sus micros. De
eso depende el patcheo guiado.
Qué hace falta: **gana el cerebro** (cobre §14). El módulo la atraviesa y no la
escribe nunca. En el núcleo no hay cambio de código; hay que **quitar la
ambigüedad de la documentación** y que `POINT` alcance los 32 jacks de este
módulo con el direccionamiento del cambio 2.
Cierra: test de que `POINT` sobre un jack de la ranura del módulo 3 v2 se traduce
a una posición de la cadena, y que ningún camino del firmware del módulo escribe
en ella.

## 9. Riesgos y decisiones abiertas

### Riesgos

1. **La latencia del reenvío maestro → esclavo.** El segundo micro recibe sus
   órdenes reenviadas, no directas. Irrelevante para el tono; no irrelevante para
   un disparo. Cierra: un presupuesto de temporización de evento —que hoy no
   existe en el repositorio— con su criterio de aprobado y suspenso **declarado
   antes de medir**, igual que se hizo con los 131 ns del 74HC14. Es la misma
   pieza que pide el #160 para el disparo de percusión, y **debe diseñarse una
   sola vez** para los dos: `evento_budget.py`.
2. **Los gates dentro de la trama.** El #158 obliga a mudarlos porque cuatro
   cables no dan para ocho voces, y el núcleo §5.3 ya dijo que además sincroniza
   mejor, porque tono y gate salen en el mismo instante. Este documento **no lo
   resuelve**: el cambio 1 de §8 lo hace posible al desacoplar la trama, pero qué
   mensaje lleva el gate y con qué sello de tiempo se diseña junto al riesgo 1.
3. **El formato de los números de la medida.** Qué manda el módulo para «el
   oscilador 3 mide 440,12 Hz»: unidad, resolución y si va crudo o ya en cents.
   Cierra: con el cambio 5 de §8, con el firmware del cerebro delante, porque
   quien consume decide el formato. **Criterio ya fijado**: la resolución tiene
   que bajar del paso de desafinado del módulo, 0,139 cents, o la medida no
   distingue lo que el módulo puede pedir.
4. **La longitud máxima del mazo por rama** no existe en ningún documento del
   repositorio, y sin ese número no hay presupuesto de flanco — y el cambio 1
   sube la tasa de trama, así que importa más que antes. Cierra: se declara en el
   plan y entra como constante citada en `trama_j2_budget.py`.
5. **La capacidad de la máquina de retención bajo carga de barrido.** R-B9 dice
   qué pasa al desbordar, pero no cuánto aguanta. Cierra: derivarlo del peor caso
   —un cliente escribiendo a la tasa máxima durante 4,08 s— y aseverarlo en el
   test del cambio 9.
6. **Que el motor de perturbación sirva para la ocupación de las entradas de
   control** (cobre §6.3, camino B). El algoritmo está validado en simulación
   (`software/nucleo/core/src/perturbacion.rs`), pero corriendo en el cerebro
   sobre entradas de módulo, no dentro de un micro de módulo sobre su propia
   cadena. Cierra: reusar el mismo test de simulación con la topología de la
   cadena de dieciséis, y medirlo en el bring-up. **Si falla, gana el camino A**
   (el jack con contacto independiente) y esto deja de existir.

### Decisiones abiertas

1. ~~**Cuántas ranuras lógicas publica el módulo** (cambio 2 de §8): dos, o una
   con el campo de índice repartido.~~ **CERRADA el 2026-08-27: DOS.**

   > Rescatada del PR #201 al cerrarlo, y **corregida en la propia tanda**: la
   > primera redacción de esta enmienda la cerró en «una» apoyándose en la
   > decisión de Samuel de que las ranuras son *funcionales, nunca por micro*.
   > Eso fue leer mal la pregunta. **«Dos ranuras» nunca fue «una por micro»**:
   > el cambio 2 de §8 pide dos por **espacio de direcciones** — `MAX_INSTANCIAS
   > = 16` lo consumen exacto los dieciséis osciladores, y las 72 entradas del
   > censo que no son voces no tienen dónde vivir. Las dos opciones que estaban
   > sobre la mesa eran funcionales las dos; el chip no entraba en la pregunta.
   >
   > Cierra en **dos** porque es lo que §8 ya dice que el módulo toma: «una para
   > los dieciséis osciladores, otra para lo de placa y lo de módulo». Con seis
   > módulos y el cerebro son 8 de 16 ranuras lógicas.
   >
   > **Lo que sí aporta la decisión de Samuel, y se queda como regla aparte y
   > más ancha:** una ranura **jamás** refleja anatomía de hardware. Desde
   > fuera nadie sabe cuántos procesadores hay dentro de un módulo. Esa regla
   > no elegía entre una y dos —las dos la cumplen— pero prohíbe una tercera
   > opción que nadie proponía y que habría vuelto por la puerta de atrás: una
   > ranura por micro. Si mañana un módulo lleva dos micros, publica las
   > ranuras que su censo pida, no las que su silicio tenga.
   >
   > **Criterio de cierre, corregido al contrato de hoy.** La versión anterior
   > de esta enmienda copió el criterio original tal cual —«sin tocar los 16
   > bits del identificador, porque esos 16 bits caben en tres septetos de
   > SysEx»— y ese criterio **caducó el 2026-08-21**: `ParamId` es de **32
   > bits** (8 reservados, tres niveles de ruta de 4, instancia de 4, índice de
   > 8) y el núcleo §3.1 dice que el id pasó de tres septetos a cinco. El
   > criterio vigente es el que §8 ya escribe: **un test que monte el módulo 3
   > v2 completo y exija que las 298 entradas del censo sean direccionables y
   > distintas**, dentro del `u32` de hoy y sin tocar el formato persistido —
   > `preset.rs` escribe el id tal cual al fichero.

2. **Cota fija o mensaje en lote** para el camino de respuesta (cambio 12).
   Cierra: medir cuánta pila cuesta la cota derivada del censo. Si cabe sin
   apretar, gana la cota, que es menos código. Si no, gana el lote.
3. **Si el barrido silencia el módulo entero o solo la columna que mide** (R-B3).
   Cierra: con el bring-up, midiendo si medir una columna mientras la otra suena
   contamina por diafonía en el bus de la matriz (cobre, riesgo 6). Por defecto,
   el módulo entero, que es lo conservador.
4. **Qué se hace con las notas sonando cuando `voces aportadas` baja** (R-M8).
   Cierra: es una decisión musical, no técnica; se toma con Samuel al escribir el
   reparto de voces. Las dos salidas —soltar las notas afectadas, o terminar la
   nota y aplicar el cambio después— son implementables y ninguna bloquea el
   spec.

## 10. Verificación

Todo lo de este documento se verifica con tests en host, Rust puro, y con dos
presupuestos ejecutables. Ninguna aserción es prosa.

| Qué | Cómo | Estado |
|---|---|---|
| Cada uno de los catorce cambios de §8 | Su test, descrito en la ficha del cambio | **nuevo** |
| `autotune_budget.py` | Mudado al módulo. Asevera el timeout de R-B1, el abandono de R-B2 y el peor caso de 4,08 s. Y los cinco periodos por nota de §3.1 contra los 2,7 s del núcleo §5.1 | **mudar y ampliar** |
| `trama_j2_budget.py` | Ocupación del SPI con todos los módulos a su tasa declarada, incluido el bloque de tono de este a 1 kHz. Asevera que la suma queda por debajo de un techo declarado, y **falla si un módulo no declara su tasa** | **nuevo** |
| `evento_budget.py` | La cadena entera desde el `note on` del cerebro hasta el CV en el pin del chip, incluida la etapa maestro → esclavo. Criterio de aprobado declarado **antes** de medir. Sirve a este módulo y al #160 | **nuevo** |
| Las 26 relaciones de §6 | Test que intenta cada valor ilegal y exige `ERROR`; test que exige que las 26 aparezcan en el volcado del descriptor | **nuevo** |
| Los once modos de fallo de §4 | Test por modo: se provoca y se exige que produzca hueco con su motivo, o `ERROR`, nunca un valor por defecto | **nuevo** |
| El censo de §5.1 | Test que monta el módulo completo y exige 298 entradas direccionables y distintas, 226 escribibles | **nuevo** |

## 11. Fuera de alcance

- **El cobre**: piezas, geometría, presupuestos eléctricos y bring-up de placa.
  Está en
  [`2026-08-22-modulo-3-vco-dieciseis-design.md`](2026-08-22-modulo-3-vco-dieciseis-design.md).
- **Si los módulos 5, 6 y 7 llevan micro propio.** El núcleo §10 lo dejó abierto
  a propósito y **aquí no se cierra** (R-J2). Se cierra al dibujar el módulo 5.
- **El enrutado de audio del instrumento** — matriz en el módulo 4, topología en
  estrella. Sigue aplazado a su propio ciclo.
- **El catálogo general de mensajes del protocolo**, que es del núcleo §4.1. Aquí
  se pide crecerlo en los puntos concretos de §8 y se dice por qué; el resto no
  se toca.
- **El código.** Aquí está lo que el firmware tiene que cumplir y contra qué se
  mide.
