# La cabecera del J2: una trama, un mensaje, y la verdad se reafirma

**Fecha**: 2026-09-02 · **Estado**: **propuesto, v1 antes de la junta** ·
**Cierra**: la segunda mitad del #267 · **Cuelga de**: el J2 punto a punto
(`2026-08-25-j2-punto-a-punto-design.md`, D1-D8), el evento de nota
(`2026-08-25-evento-de-nota-design.md`, §3, D4-D7 con la enmienda del
2026-09-02) y el generador de envolvente
(`2026-09-02-generador-de-envolvente-design.md`, §3.4, §3.5, §14)

---

## 0. Qué es este papel, y qué no

El J2 punto a punto abrió el enlace (D1-D9) y el evento fijó qué campos lleva
una nota (§3). Entre los dos hay un hueco que el #267 nombra sin rodeos: *«el
J2 no tiene cabecera de mensaje»*. Ningún byte de `main` sabe decir qué
mensaje viene ni cuánto mide; `core/src/j2.rs` solo habla el dialecto legado
de 72 bits del módulo 3 v1, y el receptor de largo variable que R-E5 exige no
tiene una sola línea.

Este papel decide **el sobre**: la cabecera común de toda trama del J2, en las
dos direcciones, y las reglas del receptor. Y decide **los mensajes del
dialecto de la Voz** en su versión 1, que son los cuatro clientes que el #267
tiene en fila —el evento, la imagen del crosspoint, el `SET` de parámetros y
el bloque de compuerta con su contador— más los dos que faltaban para que el
enlace arranque y no se muera: el `HOLA` y el bloque de tono agrupado que
R-M4 manda y nadie había puesto en bytes.

Lo que este papel **no** es, dicho de frente como lo dice el generador en su
§0: **el firmware del N657 no existe** (#250). Todo lo que sigue es formato y
contrato; lo ejecutable que sale de aquí vive en `core`, `no_std`, probado en
el host, y el firmware de cada extremo lo llamará cuando exista. Las cifras de
tiempo son cotas derivadas de las hojas y de los papeles, no medidas.

Tampoco decide el reloj (D2 del J2), el peldaño 2 (D8), la autopista (D9), el
formato interno de los mensajes de subida que otros papeles reparten (R-J4,
telemetría, `TuneProgress`), ni el dialecto del módulo de mandos (#178). §7
los lista uno por uno.

---

## 1. Los clientes, con su fuente

| Mensaje | Dirección | Quién lo pide | Qué dice la fuente |
|---|---|---|---|
| Evento de nota | baja | evento §3 | *«Cuatro campos y nada más»*: destino 16, borde 2, fuerza (16, `fuerza.rs`), tono de arranque 16 |
| Bloque de tono | baja | orquestación R-M4; evento D3 | *«16 × 16 bits + cabecera»*, 288 bits; D3: *«manda solo lo que cambió»*, deltas + cabecera |
| Bloque de compuerta | baja | evento R-E10/R-E11; generador §3.4 | 16 bits de compuertas, *«nunca de disparos»*, más *«el contador de eventos emitidos»*; cadencia reservada |
| Imagen del crosspoint | baja | voz-total §5.4 (acta del #171); `bahia.rs` | *«el cerebro manda la imagen entera por el J2 (64 bytes)»*; el N657 aplica la barrera y shiftea |
| `SET` de parámetros | baja | generador §9 y §14; #267 comentario | *«No hay flujo de escritura de parámetros»*; 160 parámetros del generador por módulo sin camino |
| Soltar todo | baja | generador §3.5 (`Entrada::SoltarTodo`) | *«Todo lo demás encola: eventos, reafirmaciones, escrituras de parámetros, `soltar_todo()`»* |
| Estado del patch (jacks) | sube | orquestación §7.1 | *«Sondeo cada 50 ms, notificación al cambiar»*; sin tamaño declarado |
| Salud | sube | orquestación §7.1 | *«Temperatura de cada placa, tensión de la referencia, estado del esclavo, identidad»*, 1 Hz; sin tamaño declarado |
| Medida de calibración | sube | orquestación §7.1 y §9 punto 3 | *«A petición»*; el formato de los números *«qué manda el módulo para "el oscilador 3 mide 440,12 Hz"»* está abierto |
| Sondeo del panel | sube | latencia_mano, #178 | *«deltas + cabecera»*, 256 bits a 8 kHz — del módulo de mandos, no de la Voz |

Y una regla que los gobierna a todos, la ley del largo: **R-E1, ningún
mensaje del J2 dura más de 100 µs**. Al piso legado de 10 MHz son 1000 bits,
125 bytes; a los 34,5 MHz de D8 son 3450 bits. `trama_j2_budget.py` la
asevera contra cada fila declarada, y hoy sus filas no llevan cabecera porque
no había cabecera que sumar (`BITS_EVENTO` lleva el comentario *«SIN cabecera
declarada: la pone el códec del cambio 1 cuando exista»*). Este papel es ese
códec.

---

## 2. Las decisiones

### D1. Una trama, un mensaje

**Cada bajada de `CS` lleva exactamente un mensaje.** Nada de empaquetar
varios en una trama.

Por qué: D1 del evento dice que el evento *«sale sin esperar turno»* y que su
peor caso es *«lo que le quede al mensaje en curso»*. Si una trama pudiera
llevar tres mensajes, el mensaje en curso mediría tres y la cota de R-E1 se
mediría contra la trama, no contra el mensaje. Con una trama por mensaje, la
ley del largo y el framing por `CS` (D5 del J2: *«la trama es lo que cabe
entre bajada y subida de CS»*) miden lo mismo, y R-E5 (*«la cabecera dice
qué viene y cuánto»*) tiene un solo «qué».

Consecuencia que se declara: el largo que dice la cabecera y el largo que
delimita `CS` **tienen que coincidir o sobrar por el lado de `CS`**; §5 dice
qué pasa si no.

### D2. El sobre: cuatro bytes delante, dos detrás

Toda trama del J2, en las dos direcciones, es:

```
 byte 0        tipo        u8      qué mensaje (§3.1)
 byte 1        largo       u8      bytes de carga que siguen, 0..=255
 bytes 2-3     secuencia   u16 LE  contador de tramas emitidas en ESTE enlace y
                                   en ESTA dirección; +1 por trama, da la vuelta
 bytes 4..4+largo           carga  lo que el tipo diga (§3)
 2 bytes        crc16       u16 LE  CRC-16/CCITT-FALSE de los bytes 0..4+largo
 [relleno]                  0x00    solo si el giro es más largo que la trama (D6)
```

Seis bytes de sobre. Cada campo tiene un porqué y ninguno es «por si acaso»:

- **`tipo` en un byte**, con el bit alto como dirección —puesto, sube; quitado,
  baja—, que es la convención que `protocolo.rs` ya usa para sus etiquetas
  (*«El bit alto de la etiqueta dice la dirección»*). Los tipos `0x00-0x0F` y
  `0x80-0x8F` son universales, de todo enlace; del `0x10` y del `0x90` en
  adelante son del dialecto que la identidad EEPROM declare. Se hereda de D2
  del J2: el esclavo ya declara reloj y tasa en su EEPROM; declarar dialecto
  es una fila más de la misma especie.
- **`largo` en un byte** porque R-E1 no deja que haga falta más: al piso
  legado caben 125 bytes de trama y a D8 431; el byte alcanza para los dos y
  el mensaje más gordo de este papel mide 102 (§4).
- **`secuencia` de 16 bits** para que los dos extremos vean los huecos: una
  trama perdida es un salto en la cuenta, y el salto se cuenta y sube por
  salud (§6) en vez de callarse. Con 8 bits, a 8 kHz la cuenta daría la vuelta
  cada 32 ms y una ráfaga perdida de 256 tramas —justo el orden del watchdog
  de §9.2 de la Voz total— se confundiría con cero. Con 16 son 8 s.
- **CRC-16/CCITT-FALSE, poly `0x1021`, init `0xFFFF`**, el mismo de
  `descubrimiento.rs:59` (*«CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, sin
  reflejar»*, vector canónico `"123456789" → 0x29B1`). No se inventa un
  segundo CRC en el repo. El N657 lo calcula en hardware: la unidad CRC admite
  *«fully programmable polynomial with programmable size (7, 8, 16, 32
  bits)»* y *«Programmable CRC initial value»* (DS14791 Rev 10, §3.19, p.
  41-42), *«CRC computation done in four AHB clock cycles (HCLK) for the
  32-bit data size»*. El SPI también trae *«Hardware CRC feature can verify
  the integrity of the communication at the end of transaction»* (p. 74), pero
  atado a `TSIZE`, el número de datos de la transacción, que un receptor de
  largo variable no conoce de antemano; por eso el CRC se computa sobre el
  búfer al subir `CS`, con la unidad, y no con el del SPI. Es un detalle del
  firmware y se dice aquí para que nadie descubra `TSIZE` ruteando.
- **Little-endian** en todo campo de más de un byte: es la convención de
  `descubrimiento.rs` (`u16 LE`, `u32 LE`), de `descriptor.rs` y de
  `preset.rs`, y es el orden nativo del Cortex-M55: el búfer del DMA se lee sin
  dar la vuelta a nada. El big-endian de `j2.rs:132` y `memoria.rs:159` no es
  una convención del enlace: es la palabra del AD5686R y la dirección del
  24AA1025, que van así porque sus hojas lo mandan.
- **MSB primero dentro de cada byte**, la convención del SPI que
  `bahia_serie.rs` ya declara (*«MSB primero dentro de cada byte»*).

**Por qué CRC, cuando el evento decía «sin CRC».** El evento D6 escribió *«ni
acuse, ni número de secuencia, ni CRC, ni comparación cruzada — y R-S5
prohíbe inventarlos»*. Ese párrafo está tachado en el papel y su enmienda del
2026-08-27 lo declara **SIN SUJETO**: R-S5 nunca entró a `main`. Lo que sí
sobrevive de aquel argumento es la doctrina, y este papel la respeta: **no hay
acuse ni retransmisión**. El CRC no es un acuse: es la diferencia entre
**rechazar** una trama corrupta y **ejecutarla**. Un `cierra` con un bit
volteado en la instancia cierra otra voz; un `SET` corrupto escribe un
parámetro que ningún flujo repara hasta la reafirmación de D7. R-E10 repara
lo perdido; el CRC convierte lo corrupto en perdido, que es lo único que R-E10
sabe reparar. A 34,5 MHz por 74 cm de cinta al lado de audio de 24 bits, y con
la marca *«nada de chips baratos»*, dos bytes por trama son el precio de que
el enlace no ejecute basura.

### D3. El destino no viaja en el sobre: viaja en el mensaje que lo necesita

El enlace es punto a punto: el módulo **es** el enlace, y un sobre que dijera
«para la Voz» diría lo que el `CS` ya dice. Por eso la cabecera no lleva
dirección de módulo.

Lo que sí lleva cada mensaje que direcciona dentro del módulo es **la
instancia**, y el evento además lleva **el destino de 16 bits que su §3 fijó**
—*«ruta de tres niveles + instancia, como `ParamId` sin índice»*—, que son los
bits 23..8 de `ParamId` (`param.rs:17-24`: nivel 1, nivel 2, nivel 3,
instancia, cuatro bits cada uno). En un enlace directo el nivel 1 es la ranura
del cerebro y los niveles 2 y 3 van a cero; el módulo **comprueba que el nivel
1 es el suyo** —lo aprende en el `HOLA`, D5— y rechaza el evento si no lo es.
Es una comprobación gratis contra una trama que llegue a la ranura
equivocada, y es R-E3 hecha ejecutable: *«el destino de un evento es una ruta
y una instancia, nunca una columna ni un micro»*.

Los concentradores (niveles 2 y 3, `param.rs:29-31`) no existen todavía y este
papel no inventa cómo reenvían; §7 lo declara.

### D4. Los mensajes de bajada del dialecto de la Voz, versión 1

Seis mensajes, que son los seis clientes de §1 que bajan. Sus bytes están en
§3.2. Lo que se decide aquí es qué lleva cada uno y qué no:

- **`EVENTO`**: los cuatro campos de evento §3 y nada más, en 7 bytes: destino
  16, borde en un byte entero (`0` abre, `1` cierra, `2` dispara, `3`
  reservado y **rechazado**), fuerza 16 y tono de arranque 16. El borde no se
  empaqueta con otro campo porque dos bits sueltos no le ahorran un byte a
  nadie y le cuestan una máscara a todo el mundo.
- **`TONO`**: el bloque agrupado de R-M4 con las deltas de D3 del evento:
  **una máscara de 16 bits de qué instancias vienen, y a continuación un tono
  de 16 bits por cada bit alto, en orden de instancia**. Dieciséis moviéndose
  son 2 + 32 = 34 bytes; cuatro son 10; ninguno son 2. Es más compacto que
  «instancia + valor» por delta (3 bytes cada una) y queda alineado a byte. El
  bloque completo sube de los 288 bits que `trama_j2_budget.py` cuenta a
  **320 con el sobre** (§4): el guion cambia de cifra y de fuente.
- **`COMPUERTA`**: la máscara de compuertas de 16 bits y el contador de
  eventos de 16 bits, tal como el generador §3.4 los definió y la enmienda a
  evento D6 los mandó: *«la máscara es de compuertas, nunca de disparos»*; el
  contador es *«de eventos emitidos por el cerebro para ese módulo»* al armar
  el bloque; el módulo *«ignora los bloques con contador menor»* que su cuenta
  de eventos recibidos. Su cadencia sigue reservada (R-E11: la elige el oído).
- **`BAHIA`**: la imagen sombra del crosspoint **en la forma del modelo**, no
  en los bits del chip: dos chips × dieciséis canales × una máscara de 16
  líneas, 64 bytes, exactamente `Imagen.filas` de `bahia.rs`. El módulo es
  quien aplica la barrera de cambiados-en-silencio y la política de drones
  (voz-total §5.4: *«el N657 la guarda como "ruta pendiente", aplica la
  barrera…, shiftea y latchea»*), y la barrera razona en canales, no en bits.
  La serialización a los 512 bits (`bahia_serie.rs`) la hace el módulo con su
  orientación y su orden de cadena, que son constantes de **su** firmware
  cuando el esquemático las fije: el cerebro no tiene por qué saberlas.
- **`SET`**: escrituras de parámetros, **N tuplas de (instancia u8, índice u8,
  valor i32 LE)**, 6 bytes cada una, N = largo / 6; un largo que no sea
  múltiplo de 6 se rechaza. El valor va en los 32 bits con signo que el
  modelo declara para **todo** parámetro (`param.rs:13-15`: *«Entero con signo
  de 32 bits, siempre: la escala y la unidad viven en el descriptor»*): un
  `SET` de 16 bits ahorraría dos bytes por parámetro y crearía un segundo
  tipo de valor en el instrumento, y el núcleo §2.1 solo tiene uno. Dieciséis
  tuplas son 96 bytes: los diez parámetros de una voz o un parámetro de las
  dieciséis, en una trama. La instancia es el canal, y es la ranura del canal
  donde el generador §3.5 dice que la escritura *«termina»*: *«los parámetros
  se empujan, no se buscan»*.
- **`SOLTAR_TODO`**: sin carga. Es `Entrada::SoltarTodo` del generador: todo a
  relajación, las compuertas a cero, y el módulo adopta el contador del
  primer `COMPUERTA` válido que llegue después (generador §3.4).

### D5. El enlace arranca con `HOLA`, y `HOLA` es universal

Antes de la primera palabra de un dialecto, el cerebro manda **`HOLA`**, tipo
universal, con la secuencia a **cero**: versión de la cabecera (`1`), la
ranura que ese enlace ocupa (el nivel 1 que el módulo comprobará en cada
evento, D3), el dialecto que el cerebro va a hablar (el que el catálogo asocia
al tipo de placa leído por I²C, R-A1) y la ventana de subida de D6.

`HOLA` **reinicia** en el módulo la secuencia esperada, la cuenta de eventos
recibidos y la de tramas rechazadas; y el módulo responde con su propio `HOLA`
en la subida (§3.3): versión, dialecto que **él** habla, y un estado. Si la
versión o el dialecto no cuadran, el módulo no aplica ninguna trama del
dialecto —las cuenta como rechazadas por versión— y su `HOLA` de subida lo
dice. No es un acuse: es el mismo patrón de `CodigoError::VersionIncompatible`
de `protocolo.rs:34-38`, que *«va SIEMPRE acompañado de un `Hola` con la
nuestra»*.

La versión **no viaja en cada trama**. Viaja en `HOLA` y en la EEPROM: una
cabecera que cambie de forma es un dialecto nuevo, y el catálogo del cerebro
es quien sabe qué tipo de placa habla cuál. Un byte de versión por trama a
8 kHz sería 64 kbit/s para decir siempre `1`.

### D6. La subida viaja en el giro, y el módulo repite hasta que le den sitio

D4 del J2 abrió el canal: *«cada trama de bajada puede traer simultáneamente
su subida: las medidas de R-J4 viajan en el mismo giro, en vez de robarle aire
al tono»*. Lo que faltaba era decir **cómo cabe** algo de subida en un giro
cuyo largo lo decide el otro extremo. Tres reglas:

1. **La trama de subida tiene el mismo sobre** (D2), con el bit alto del tipo
   puesto, y el módulo la tiene lista en su búfer de transmisión **antes** de
   que el `CS` baje: el esclavo SPI la shiftea byte a byte al ritmo que el
   maestro le dé. Su secuencia es la del módulo, aparte de la del cerebro.
2. **El módulo repite la misma trama de subida hasta que un giro la haya
   clocado entera.** El módulo sabe cuántos bytes tuvo cada giro (son los que
   recibió); si fueron menos que su trama de subida, la deja puesta para el
   giro siguiente; si fueron los suficientes, avanza a la siguiente. Es local,
   determinista y no necesita acuse: el cerebro, por su parte, sabe cuántos
   bytes clocó y solo intenta leer una subida cuando clocó por lo menos
   `largo + 6`.
3. **El cerebro rellena las tramas periódicas hasta la ventana de subida.** Un
   `TONO` con nada que mandar mide 8 bytes, y con eso una subida de 24 no
   saldría nunca en un silencio. Por eso todo mensaje **periódico** de bajada
   (`TONO`, `COMPUERTA`) se cloca con largo de giro ≥ `VENTANA_SUBIDA`, con
   relleno a `0x00` **después del CRC** —el CRC no lo cubre y el receptor no lo
   mira—; los mensajes que no son periódicos (`EVENTO`, `SET`, `BAHIA`) van
   con su largo justo. La ventana es **una constante del dialecto**, no del
   enlace universal (R-P1: nada de un enlace gobierna a otro): la de la Voz es
   **24 bytes**, que es lo que mide `SALUD` con su sobre (§3.3); el módulo de
   mandos declarará la suya con su papel (#178: su sondeo del panel son 32
   bytes de deltas, que no caben en 24).

Lo que cuesta, con el número: al piso legado, un giro de `TONO` en silencio
pasa de 8 a 24 bytes; a 8 kHz son 16 × 8 × 8000 = 1,02 Mbit/s = **10,2 %** del
enlace, 3,0 % a D8. Es el precio de que la subida no dependa de que suene
algo. El mensaje más largo de la Voz, `TONO` con dieciséis, ya mide 40 y no
paga relleno.

Lo que **no** se decide: el formato de la carga de `JACKS`, `MEDIDA` y `LOG`
—son de otros papeles (§7)—, y el troceo de una subida más larga que la
ventana: en v1 **ningún mensaje de subida de la Voz supera los 24 bytes**, y el
que lo necesite (el log de telemetría) trae su troceo en su papel.

**El corrimiento de un ciclo de D8** (*«el maestro lee la subida corrida un
ciclo»*) **lo absorbe el driver del maestro**: los bytes que este papel
describe son los que el parser recibe ya alineados. Cómo se alinean —modo del
esclavo, o corrimiento en el maestro— es el D8 del J2 y su criterio de ojo en
bring-up, no este papel.

### D7. La verdad de todo lo que baja se reafirma

R-E12 del evento: *«todo lo que viaje solo en el evento y no lo reafirme un
flujo periódico queda sin red»*. Con D2 la trama corrupta se rechaza en vez de
ejecutarse, y eso convierte cada mensaje en un mensaje **que puede perderse**.
Este papel decide que **ninguno de los que bajan queda sin red**, y dice
cuál es la red de cada uno:

| Mensaje | Su red | Cadencia | De dónde |
|---|---|---|---|
| `EVENTO` | el bloque `COMPUERTA` (R-E10) | reservada, R-E11 | evento D6 |
| `TONO` | él mismo, periódico | 8 kHz (lazo) | latencia_mano |
| `COMPUERTA` | él mismo, periódico | reservada, R-E11 | evento R-E11 |
| `BAHIA` | **reafirmación**: el cerebro reenvía la imagen vigente | **1 Hz** | este papel |
| `SET` | **reafirmación**: el cerebro reenvía todos los parámetros del módulo, en tramas de 16 | **1 Hz** | este papel |
| `SOLTAR_TODO` | ninguna: si se pierde, el siguiente `COMPUERTA` cierra lo que haya abierto | — | R-E10 |
| `dispara` (dentro de `EVENTO`) | **ninguna, declarada** | — | evento D6 enmienda 1: *«un `dispara` perdido es un golpe perdido»* |

Por qué reafirmar en vez de acusar: es la doctrina del evento, y además es más
barato. Reafirmar la bahía es una trama de 70 bytes por segundo; reafirmar
mil parámetros son 63 tramas de 102 bytes por segundo, 51 kbit/s, **0,5 %**
del enlace al piso, **0,15 %** a D8. Un acuse pediría estado en los dos
extremos y una máquina de reintento, y la lección del #201 es que la
fiabilidad que no se puede verificar no se optimiza: se repara.

Una reafirmación **idéntica** es gratis para el receptor: `Barrera::proponer`
con la misma imagen da `cambian = 0` y queda activa sin conmutar nada; un
`SET` con el mismo valor escribe lo que ya estaba. Y una reafirmación después
de un `SOLTAR_TODO` o de un watchdog es exactamente lo que devuelve al módulo
al estado del cerebro sin que nadie lleve la cuenta de qué se perdió.

El 1 Hz es la cadencia de la salud (orquestación §7.1) y se elige por la
misma razón que R-E11 eligió la suya: **lo fija la tolerancia, no el
presupuesto**. Un parámetro perdido es un mando que no responde hasta un
segundo; una bahía perdida es un cable que no suena hasta un segundo. Si el
bring-up mide una tasa de rechazo que lo haga oír, la cadencia sube en el
guion, que es donde vive.

### D8. Un receptor que rechaza entero y cuenta

El receptor **nunca aplica media trama**. Rechaza la trama completa —y suma
uno al contador de la causa, que sube por `SALUD`— cuando:

1. `CS` sube con menos bytes que `largo + 6` (trama corta);
2. el CRC no cuadra;
3. el `tipo` no es de su dialecto ni universal;
4. la carga no tiene la forma del tipo: `SET` con largo no múltiplo de 6,
   `EVENTO` con borde `3` o nivel 1 distinto del suyo, `BAHIA` con largo
   distinto de 64, instancia ≥ 16 donde haya instancia;
5. no ha recibido `HOLA` desde el arranque, o el `HOLA` no cuadró de versión o
   dialecto (todo lo que no sea `HOLA` se rechaza).

Y **no rechaza** por secuencia: un salto de secuencia se cuenta como tramas
perdidas y la trama que llegó se aplica. El orden en el enlace es el del
cable; el único orden que el modelo defiende es el del contador de eventos
frente al bloque de compuerta (D4), que no es de la cabecera.

Lo que el receptor hace con una trama buena lo dijo el generador §3.5: **la
ISR del esclavo encola y vuelve**; el tick drena. Este papel le da a esa ISR
su lista de trabajo: contar los bytes, CRC, despachar por tipo a la cola del
generador (`EVENTO`, `COMPUERTA`, `SET`, `SOLTAR_TODO`), al camino del tono
(`TONO` y el tono de arranque del `EVENTO`) o a la barrera (`BAHIA`), y
volver a armar el DMA. Cuánto tarda eso es **el gap mínimo entre tramas**, que
motor-digital §7 hizo *«cláusula del contrato del enlace»* y que sigue siendo
un hueco hasta el bring-up (§7 de aquí). El maestro lo respeta con los
retardos mínimos que su SPI trae por hardware —*«Adjustable minimum delays
between data and between SS and data flow»* (DS14791 Rev 10, p. 74)— y
`R-E2` del evento (el evento puede salir entre dos tramas) se lee con ese gap
dentro.

### D9. Dónde vive el código, y qué le pasa al dialecto legado

- **`core/src/j2.rs`** gana el sobre universal: las constantes con cita, el
  `tipo` universal, `Cabecera`, `codificar` y `decodificar` con su
  `ErrorTrama` (una variante por causa de D8), y el CRC reutilizado de
  `descubrimiento::crc16`. Deja de decir *«Contrato CONGELADO»* en su cabecera:
  el contrato del enlace es este.
- **`core/src/dialecto_voz.rs`** (nuevo): los seis mensajes de D4 y los de
  subida de §3.3 como un `enum Mensaje`, con su codificación a carga y su
  decodificación, y la traducción a `envolvente::Entrada` para los que van al
  generador. Es el «códec nuevo con su test de ida y vuelta» que orquestación
  cambio 1 pidió el 2026-08-22.
- **El dialecto legado no se borra**: `tramas_vco4` y su test de 72 bits se
  quedan en `j2.rs` bajo un rótulo *dialecto legado del módulo 3 v1*, tal como
  orquestación cambio 1 mandó (*«El test de 72 bits no se borra: se convierte
  en el caso "módulo con tres AD5686R en cadena"»*). Un módulo cuyo tipo de
  placa el catálogo asocie al dialecto legado se habla sin sobre; su enlace
  corre al piso legado (D2 del J2).

---

## 3. Los bytes

### 3.1 Los tipos

| Tipo | Nombre | Dirección | Universal o dialecto |
|---|---|---|---|
| `0x00` | `NADA` | baja | universal: un giro sin mensaje, para clocar una subida |
| `0x01` | `HOLA` | baja | universal (D5) |
| `0x02-0x0F` | reservados | baja | universal |
| `0x10` | `EVENTO` | baja | dialecto de la Voz, v1 |
| `0x11` | `TONO` | baja | ídem |
| `0x12` | `COMPUERTA` | baja | ídem |
| `0x13` | `BAHIA` | baja | ídem |
| `0x14` | `SET` | baja | ídem |
| `0x15` | `SOLTAR_TODO` | baja | ídem |
| `0x80` | `NADA` | sube | universal: el módulo no tiene nada que decir |
| `0x81` | `HOLA` | sube | universal (D5) |
| `0x82` | `SALUD` | sube | universal en el sobre; la carga de §3.3 es la mínima de todo módulo |
| `0x83-0x8F` | reservados | sube | universal |
| `0x90` | `JACKS` | sube | dialecto de la Voz; carga de otro papel |
| `0x91` | `MEDIDA` | sube | ídem |
| `0x92` | `LOG` | sube | ídem |

### 3.2 Las cargas de bajada

```
HOLA        largo 4    [version=1 u8][ranura u8][dialecto u8][ventana_subida u8]
NADA        largo 0
EVENTO      largo 7    [destino u16 LE][borde u8][fuerza u16 LE][tono u16 LE]
                       destino = bits 23..8 de ParamId: nivel1<<12 | nivel2<<8 | nivel3<<4 | instancia
                       borde   = 0 abre · 1 cierra · 2 dispara · 3 rechazado
TONO        largo 2+2n [mascara u16 LE][tono u16 LE × n], n = bits altos de la máscara,
                       en orden de instancia ascendente
COMPUERTA   largo 4    [mascara u16 LE][contador u16 LE]
BAHIA       largo 64   [entrada: 16 × u16 LE][salida: 16 × u16 LE]
                       = Imagen.filas[chip][canal], bit i = línea i, chip 0 = Entrada
SET         largo 6n   [instancia u8][indice u8][valor i32 LE] × n, 1 ≤ n ≤ 16
SOLTAR_TODO largo 0
```

### 3.3 Las cargas de subida

```
NADA        largo 0
HOLA        largo 3    [version u8][dialecto u8][estado u8]
                       estado = 0 listo · 1 versión incompatible · 2 dialecto incompatible
SALUD       largo 18   [temperatura_centesimas i16 LE]   del 0x48 de memoria.rs
                       [vref_milivoltios u16 LE]
                       [tramas_recibidas u16 LE]         válidas, desde HOLA
                       [rechazadas_crc u16 LE]
                       [rechazadas_largo u16 LE]         cortas o de forma mala (D8 1 y 4)
                       [rechazadas_tipo u16 LE]          tipo desconocido o sin HOLA (D8 3 y 5)
                       [perdidas u16 LE]                 saltos de secuencia acumulados
                       [eventos_recibidos u16 LE]        la cuenta que COMPUERTA compara
                       [bahia_aplicada u16 LE]           secuencia de la última BAHIA activa
JACKS       largo ?    otro papel (orquestación §7.1: «qué jacks tienen cable; el valor de cada entrada»)
MEDIDA      largo ?    otro papel (orquestación §9 punto 3: unidad, resolución, crudo o cents)
LOG         largo ?    otro papel; en v1 no se emite
```

`SALUD` con su sobre son 24 bytes: **esa es la ventana de subida de la Voz**
(D6). Sus contadores son de 16 bits y dan la vuelta; el cerebro los lee como
deltas entre lecturas, no como totales.

El planificador de subida del módulo es una cola por cadencia: `HOLA` al
recibir `HOLA`, `SALUD` a 1 Hz, `JACKS` a 20 Hz o al cambiar, `MEDIDA` cuando
haya barrido, y `NADA` cuando no toque nada. Una sola trama por giro (D1 vale
en las dos direcciones).

---

## 4. Los largos contra R-E1

Sobre de 6 bytes en todo. Piso legado 10 MHz (`trama_j2_budget.py`,
`F_CONTRATO_HZ`); D8 34,5 MHz (`enlace_budget.py`, `F_PELDANO_2_HZ`).

| Mensaje | carga | trama (bytes) | bits | µs a 10 MHz | µs a 34,5 MHz |
|---|---:|---:|---:|---:|---:|
| `HOLA` | 4 | 10 | 80 | 8,0 | 2,3 |
| `EVENTO` | 7 | 13 | 104 | 10,4 | 3,0 |
| `TONO`, nada cambió | 2 | 8 → **24** con relleno (D6) | 192 | 19,2 | 5,6 |
| `TONO`, dieciséis | 34 | 40 | 320 | 32,0 | 9,3 |
| `COMPUERTA` | 4 | 10 → **24** con relleno | 192 | 19,2 | 5,6 |
| `BAHIA` | 64 | 70 | 560 | 56,0 | 16,2 |
| `SET`, dieciséis | 96 | 102 | 816 | 81,6 | 23,7 |
| `SOLTAR_TODO` | 0 | 6 | 48 | 4,8 | 1,4 |
| `NADA` para clocar subida | 0 | 6 → 24 | 192 | 19,2 | 5,6 |

Todos por debajo de los 100 µs al piso; el más largo, `SET` con dieciséis,
usa el 82 %. **El techo de `largo` que R-E1 permite al piso es 119 bytes de
carga**, y este papel lo declara como constante (`CARGA_MAX_PISO`) para que un
mensaje futuro se tope con él en un test, no en la placa.

Ocupación del enlace de la Voz, bajada, con las cadencias declaradas:

| Flujo | bits | cadencia | bit/s | % a 10 MHz | % a 34,5 MHz |
|---|---:|---:|---:|---:|---:|
| `TONO` peor caso | 320 | 8 kHz | 2 560 000 | 25,6 | 7,4 |
| `TONO` en silencio (relleno) | 192 | 8 kHz | 1 536 000 | 15,4 | 4,5 |
| `COMPUERTA` a 200 Hz (la más alta de R-E11) | 192 | 200 Hz | 38 400 | 0,4 | 0,1 |
| reafirmación `BAHIA` | 560 | 1 Hz | 560 | 0,006 | 0,002 |
| reafirmación `SET` (1000 parámetros, 63 tramas) | 816 | 63 Hz | 51 408 | 0,5 | 0,15 |
| **peor caso sumado** | | | **2 650 368** | **26,5** | **7,7** |

Contra el techo del 50 % por enlace (D6 del J2), cabe con el doble de margen
al piso. La cifra de `trama_j2_budget.py` para el bloque de tono (288 bits, 23
%) sube a 320 (25,6 %): §9 lo manda.

---

## 5. Las reglas

> **R-C1. Una trama, un mensaje, y el largo lo dicen dos veces.** La cabecera
> dice `largo`; `CS` delimita la trama. Si `CS` trae menos que `largo + 6`, la
> trama se rechaza entera; si trae más, lo que sobra es relleno y no se mira.
> Vigila: el test de trama corta y el de relleno (§8).

> **R-C2. Ninguna trama se aplica sin CRC bueno.** La corrupción se rechaza y
> se cuenta; nunca se ejecuta y nunca se «corrige». Vigila: el test de
> mutación byte a byte (§8).

> **R-C3. La secuencia cuenta, no rechaza.** Un salto es tramas perdidas y sube
> por `SALUD`; la trama que llegó se aplica. El único orden que el modelo
> defiende es el del contador de eventos de `COMPUERTA` (generador §3.4).

> **R-C4. Lo que baja tiene red, y la red está en la tabla de D7.** Un mensaje
> nuevo de bajada entra con su fila en esa tabla o entra declarado sin red,
> como `dispara`. Vigila: `trama_j2_budget.py`, que lista cada mensaje con su
> red y falla si uno nuevo no la declara.

> **R-C5. La subida vive dentro de la ventana del dialecto.** Un mensaje de
> subida más largo que `VENTANA_SUBIDA` no existe en v1; el que lo necesite
> trae su troceo. Vigila: el test que asevera cada carga de subida ≤ ventana
> − 6.

> **R-C6. La versión viaja en `HOLA` y en la EEPROM, nunca en la trama.** Una
> cabecera de otra forma es otro dialecto, y el catálogo decide quién lo
> habla.

---

## 6. Qué muere, qué sobrevive, qué nace

| | Qué | Nota |
|---|---|---|
| **Muere** | *«Contrato CONGELADO por el módulo 3»* en `j2.rs:1` | D9: el contrato del enlace es el sobre |
| **Muere** | `BITS_EVENTO` *«SIN cabecera declarada»* en `trama_j2_budget.py` | §4: 104 bits con sobre |
| **Muere** | El 288 del bloque de tono como cifra de guion | §4: 320 con sobre y máscara |
| **Muere** | El «~50» del watchdog de trama como número sin dueño (voz-total §9.2) | §7: sigue siendo del plan del firmware, pero este papel le da lo que vigila: tramas válidas, no bytes |
| **Sobrevive** | Los cuatro campos del evento (§3 del evento) | D4: mismos campos, ahora con bytes |
| **Sobrevive** | R-E1, R-E4, R-E5, R-E10, R-E11, R-E12 | Todas ejecutables ahora |
| **Sobrevive** | El dialecto legado de 72 bits y su test | D9 |
| **Sobrevive** | `crc16` de `descubrimiento.rs` | D2: un solo CRC en el repo |
| **Nace** | El sobre de 6 bytes, en las dos direcciones | D2 |
| **Nace** | `HOLA` y el reinicio de cuentas | D5 |
| **Nace** | La ventana de subida y la regla de repetir hasta que quepa | D6 |
| **Nace** | La reafirmación de `BAHIA` y `SET` a 1 Hz | D7 |
| **Nace** | `SALUD` con sus contadores de rechazo | §3.3 |
| **Nace** | `CARGA_MAX_PISO = 119` | §4 |
| **Nace** | `dialecto_voz.rs` | D9 |

---

## 7. Lo que este papel NO decide, con su dueño

1. **El gap mínimo entre tramas**, en microsegundos. Es la latencia de la ISR
   del esclavo bajo las capturas y el DMA de audio (motor-digital §7) y se
   mide en bring-up (#250, #231). Hasta entonces el maestro no manda dos
   tramas con menos de **un hueco declarado en el guion como HUECO**, y
   `ataque_budget.py` ya lleva la fila «parse del evento y encolado en el
   N657: HUECO».
2. **El mecanismo del corrimiento de D8** (esclavo en otro modo, o el maestro
   corrido un ciclo). Del J2 punto a punto y de su criterio de ojo.
3. **Las cargas de `JACKS`, `MEDIDA` y `LOG`.** R-J4 dice que las medidas son
   *«parámetros de primera clase»*; orquestación §9 punto 3 deja abierto su
   formato; el log es de otro papel (J2 §9). Este papel les da tipo y ventana.
4. **El dialecto del módulo de mandos** (#178): su ventana de subida, su
   sondeo del panel de 32 bytes, y si el cerebro le baja algo (LEDs). Con el
   sobre de D2 ya tiene con qué escribirse.
5. **Los concentradores** (niveles 2 y 3 de `ParamId`): cómo un módulo
   reenvía a los que cuelgan de él. No existen; cuando existan, el evento ya
   lleva la ruta entera (D3).
6. **La cadencia de `COMPUERTA`** (R-E11: la elige el oído) y **la del
   `TONO`** (latencia_mano, 8 kHz hoy).
7. **La autopista diferencial** (D9 del J2): el sobre no depende del medio;
   si el día que exista pide tramas más largas que 255 de carga, `largo`
   pasa a dos bytes en un dialecto nuevo, que es exactamente para lo que R-C6
   existe.
8. **Qué hace el cerebro con los contadores de `SALUD`**: umbrales, alarma,
   si cambia la cadencia de reafirmación. Es de la salud del instrumento
   (orquestación §7.1) y del bring-up.
9. **El `HOLA` tras un reinicio del módulo en sesión**: el módulo que
   arranca solo rechaza todo hasta el próximo `HOLA` (D8 punto 5), y el
   cerebro **no** lo sabe hasta ver `rechazadas_tipo` subir en la siguiente
   `SALUD`… que el módulo no manda porque no tiene `HOLA`. Ese cerrojo lo
   abre una regla que este papel propone y no sella: **`HOLA` de subida se
   emite siempre que el módulo no haya recibido `HOLA`, en cada giro**, así
   el cerebro lo ve en el primer giro y reenvía el suyo. Queda marcado para
   la junta.

---

## 8. Los tests

En `core/tests/j2.rs` (nuevo) y `core/tests/dialecto_voz.rs` (nuevo), todos
en el host, con la cita del papel en cada uno:

1. **Ida y vuelta de cada mensaje**: `codificar` seguido de `decodificar` da
   el mismo `Mensaje`, para los seis de bajada y los tres de subida con carga,
   con valores de borde (todo cero, todo `0xFF`, máscaras con un bit,
   `SET` de 1 y de 16).
2. **El sobre, byte a byte**: un `EVENTO` conocido produce exactamente los 13
   bytes de §3.2, en ese orden, LE, con el CRC que da `crc16` de
   `descubrimiento.rs` sobre los primeros 11.
3. **Mutación byte a byte**: para cada trama de (1), voltear un bit de cada
   byte de cabecera y carga hace que `decodificar` devuelva `ErrorTrama::Crc`
   y nunca un mensaje. Voltear un bit del CRC, ídem. Es R-C2 con dientes.
4. **Trama corta**: quitar el último byte de una trama válida da
   `ErrorTrama::Corta`; añadir relleno de 0x00, de 1 a 32 bytes, sigue
   decodificando el mismo mensaje (R-C1).
5. **Forma mala**: `SET` de 7 bytes de carga, `EVENTO` con borde 3, `BAHIA` de
   63, instancia 16 en `SET`, nivel 1 ajeno en `EVENTO`: cada uno con su
   variante de `ErrorTrama`, y ninguno con `Crc` (el CRC es correcto: la
   forma es lo que falla).
6. **Tipo desconocido**: `0x02` y `0x16` dan `ErrorTrama::Tipo`.
7. **R-E1 al piso**: para cada mensaje, la trama más larga que su tipo admite
   mide ≤ 125 bytes; y `CARGA_MAX_PISO == 119`, con la aritmética en el
   aserto (1000 bits / 8 − 6).
8. **La ventana de la Voz**: cada carga de subida de §3.3 con su sobre ≤ 24, y
   `SALUD` mide exactamente 24 (R-C5).
9. **`TONO` con máscara**: máscara `0b1000_0000_0000_0101` con tres tonos da
   largo 8 y los tonos en las instancias 0, 2 y 15; máscara con n bits y
   largo distinto de 2 + 2n es `ErrorTrama::Forma`.
10. **`BAHIA` es `Imagen.filas`**: una `Imagen` con un cruce en (Entrada, canal
    3, línea 9) codifica con el bit 9 del `u16` número 3 alto y todo lo demás
    a cero; y `decodificar` devuelve una `Imagen` igual. Y las 64 bytes de la
    imagen de arranque de voz-total §5.4 son ceros.
11. **La traducción al generador**: `EVENTO` con instancia 5 y borde 1 da
    `Entrada::Evento { canal: 5, borde: Borde::Cierra, .. }`; `COMPUERTA` da
    `Entrada::Compuerta { mascara, contador }`; `SET` de tres tuplas da tres
    escrituras en orden; `SOLTAR_TODO` da `Entrada::SoltarTodo`.
12. **La secuencia no rechaza**: dos tramas con secuencias 7 y 12 decodifican
    las dos, y una función `perdidas(esperada, llegada)` da 4 y da la vuelta
    bien en `u16`.
13. **El dialecto legado sigue**: el test de 72 bits de `j2.rs` no se toca y
    pasa.

---

## 9. Los guiones

| Guion | Qué cambia | Estado |
|---|---|---|
| `hardware/02-midi-cv/trama_j2_budget.py` | `BITS_BLOQUE_TONO` 288 → **320** (máscara + 16 tonos + sobre), fuente este papel §4; `BITS_EVENTO` gana el sobre: **104**; `BITS_ESTADO_COMPUERTA` 16 → **192** (con sobre y relleno a la ventana); `BITS_CROSSPOINT` 256 → **560** (la imagen del modelo con sobre, no los bits del chip); filas nuevas: **reafirmación `SET`** (816 bits × 63 Hz) y **reafirmación `BAHIA`** (560 × 1 Hz); `SALUD` y `JACKS` con tamaño (**192** cada uno, la ventana) en la subida; y la aserción de R-C4: cada fila de bajada nombra su red o se declara sin ella | pendiente |
| `hardware/02-midi-cv/latencia_mano_budget.py` | Hereda `BITS_BLOQUE_TONO` del anterior; nada más | se mueve solo |
| `hardware/03-vco/ataque_budget.py` | La fila «Turno del J2 ≤ 100 µs» gana la cifra del `EVENTO` con sobre: **10,4 µs al piso, 3,0 a D8**, sin que la cota de R-E1 se mueva | pendiente |
| `hardware/02-midi-cv/tiempo_budget.py` | Su `BITS_TRAMA_J2 = 72` está caduco desde el cambio 1 (evento §5 lo dice); pasa a leer el largo máximo del enlace de la Voz de `trama_j2_budget.py` | pendiente, y es deuda del #214 |

---

## 10. Riesgos, con su criterio de cierre

1. **El gap mínimo resulta mayor que el hueco entre un `TONO` y el evento que
   D1 quiere colar.** *Cierre*: bring-up mide la ISR del esclavo bajo carga
   (motor-digital §7); si no cabe, R-E2 pierde su holgura y el evento espera
   al final del giro: 24 bytes al piso son 19,2 µs, dentro de R-E1 igual.
2. **La tasa de rechazo por CRC a 34,5 MHz hace que la reafirmación a 1 Hz se
   oiga.** *Cierre*: los contadores de `SALUD` en bring-up con el reloj
   sancionado (R-P4); la cadencia vive en el guion y sube si hace falta.
3. **El relleno a la ventana cuesta el 10 % del piso en silencio.** No es un
   riesgo de corrección sino de presupuesto; si el módulo de mandos pide una
   ventana de 40, su enlace paga lo suyo (R-P1). *Cierre*: `trama_j2_budget.py`
   por enlace.
4. **El `HOLA` no llega y el módulo enmudece** (§7 punto 9). *Cierre*: la
   regla propuesta ahí, sellada o sustituida por la junta.
5. **La unidad CRC del N657 no reproduce CCITT-FALSE tal cual** (reflejo,
   init). *Cierre*: el test del vector canónico `"123456789" → 0x29B1` corrido
   en la placa contra `descubrimiento::crc16`; si no cuadra, se computa en
   software: 255 bytes son ~2 000 ciclos a 800 MHz, 2,5 µs, y el gap lo paga.
6. **`largo` de un byte se queda corto el día de la autopista.** *Cierre*:
   R-C6; es un dialecto nuevo, no una enmienda a este.

---

## 11. El mapa de enmiendas

| Documento | Sección | Tipo | Qué | Estado |
|---|---|---|---|---|
| evento de nota | §3 (tabla del formato) | Expand | Los cuatro campos ganan sus bytes y su orden (§3.2 de aquí); la fuerza queda en 16 (`fuerza.rs`, #230) | pendiente |
| evento de nota | §5 (`evento_budget.py`, «no existe») | Sync | R-E1 la asevera `trama_j2_budget.py` con el sobre; `evento_budget.py` sigue sin existir y se dice | pendiente |
| evento de nota | §8 («la cabecera concreta del bloque de deltas de D3») | Sync | Decidida aquí: máscara + tonos (D4) | pendiente |
| generador de envolvente | §3.4, §9 (H-B2), §14 fila #267 | Sync | El `SET` y el contador tienen bytes; H-B2 cerrado | pendiente |
| J2 punto a punto | D5 («la trama es lo que cabe entre bajada y subida de CS») | Clarify | Y lleva exactamente un mensaje con este sobre (D1 de aquí) | pendiente |
| voz-total | §5.4 (acta del #171: «64 bytes, ~15 µs a 34,5 MHz») | Patch | Son 70 con sobre: 16,2 µs a D8, 56 al piso | pendiente |
| voz-total | §9.2 (watchdog de trama, «N del plan, ~50») | Clarify | Lo que cuenta son tramas **válidas** de este sobre, no bytes | pendiente |
| orquestación | cambio 1 («el códec nuevo con su test de ida y vuelta») | Sync | Es `dialecto_voz.rs` y el test 1 de §8 | pendiente |
| `core/src/j2.rs` | :1-3 | Rewrite | El sobre; el legado a rótulo | el PR de código |
| `trama_j2_budget.py` | constantes y filas | Expand | §9 | el PR de guiones |
| issue #267 | criterio de cierre | Comentar | Cabecera con evento, imagen, `SET` y compuerta; test de R-E1 al piso | al mergear |
| issue #178 | — | Comentar | El módulo de mandos ya tiene sobre; le falta dialecto y ventana | al mergear |

---

## 12. Registro de la junta

*(v1: vacío. La junta de tres lentes corre sobre esta versión y sus hallazgos
entran aquí con su resolución, antes de pedir la firma.)*

---

## 13. Acta

- Samuel, 2026-09-02: *«Dale pues vamos con eso»* sobre el orden propuesto:
  el J2 primero, como protocolo con tests, porque destraba el firmware; el
  esquemático de la Voz total en paralelo; la Discovery cuando haya plata.
- Este papel se escribió leyendo, en este orden: el J2 punto a punto entero,
  el evento §3-§4 y §8-§9 con las enmiendas del 2026-09-02, el generador
  §3.4-§3.5 y §14, `trama_j2_budget.py`, `param.rs`, `descubrimiento.rs`,
  `protocolo.rs`, `j2.rs`, y la hoja del N657 Rev 10 (§3.19 CRC, §3.46 SPI y
  su Tabla 14).
- Un hallazgo de hoja que no mueve nada pero se anota por el patrón del #206:
  el §3.46 del DS14791 Rev 10 abre diciendo *«The devices embed three serial
  peripheral interfaces (SPI)»*, y la portada dice *«6x SPI, of which four
  I2S-capable»* y la Tabla 14 lista SPI1-6. Manda la tabla; el «three» es
  texto heredado de otra hoja. El censo del hub (seis ranuras en SPI1-6)
  sigue en pie.
- Las decisiones que Samuel tiene que firmar, en cristiano, van en la
  conversación cuando la junta haya pasado, con las marcas de lo que la junta
  cambió.
