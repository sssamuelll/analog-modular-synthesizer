# La cabecera del J2: un sobre, una sesión, y la verdad con su número del mismo lado

**Fecha**: 2026-09-02 · **Estado**: **propuesto, v2 tras la junta de tres
lentes** (v1 del mismo día, sin firma) · **Cierra**: la segunda mitad del
#267 · **Cuelga de**: el J2 punto a punto
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
dos direcciones, y las reglas del receptor. Decide **la sesión** del enlace,
que la v1 no sabía que estaba decidiendo. Y decide **los mensajes del
dialecto de la Voz** en su versión 1: los cuatro clientes que el #267 tiene
en fila —el evento, la imagen del crosspoint, el `SET` de parámetros y el
bloque de compuerta con su contador— más los dos que faltaban para que el
enlace arranque y no se muera: el `HOLA` y el bloque de tono agrupado que
R-M4 manda y nadie había puesto en bytes.

Lo que este papel **es**, dicho con el nombre que la junta le puso y la v1
evitaba: **un protocolo de réplica**. El cerebro es la única fuente de
verdad; el módulo guarda una copia; la copia se refresca por flujo (`TONO`),
por comando con versión (`EVENTO` contra `COMPUERTA`), por reenvío periódico
del estado (`BAHIA`, `SET`), y el módulo publica su estado para que el
cerebro lo muestree (la subida). Cada mecanismo tiene su nombre en §2, y
ninguno se disfraza de otro.

Lo que este papel **no** es, dicho de frente como lo dice el generador en su
§0: **el firmware del N657 no existe** (#250). Todo lo que sigue es formato y
contrato; lo ejecutable que sale de aquí vive en `core`, `no_std`, probado en
el host, y el firmware de cada extremo lo llamará cuando exista. Las cifras de
tiempo son cotas derivadas de las hojas, de los papeles y de cuatro
simulaciones de la junta (§12), no medidas.

Tampoco decide el reloj (D2 del J2), la autopista (D9), el formato interno de
los registros de subida que otros papeles reparten (R-J4, telemetría,
`TuneProgress`), ni el dialecto del módulo de mandos (#178). §7 los lista.

---

## 1. Los clientes, con su fuente

| Mensaje | Dirección | Quién lo pide | Qué dice la fuente |
|---|---|---|---|
| Evento de nota | baja | evento §3 | *«Cuatro campos y nada más»*: destino 16, borde 2, fuerza (16, `fuerza.rs`), tono de arranque 16 |
| Bloque de tono | baja | orquestación R-M4; evento D3 | *«16 × 16 bits + cabecera»*, 288 bits; D3: *«manda solo lo que cambió»*, deltas + cabecera |
| Bloque de compuerta | baja | evento R-E10/R-E11; generador §3.4 | 16 bits de compuertas, *«nunca de disparos»*, más *«el contador de eventos emitidos»*; cadencia reservada |
| Imagen del crosspoint | baja | voz-total §5.4 (acta del #171); `bahia.rs` | *«el cerebro manda la imagen entera por el J2 (64 bytes)»*; el N657 aplica la barrera y shiftea |
| `SET` de parámetros | baja | generador §9 y §14; #267 comentario | *«No hay flujo de escritura de parámetros»*; los parámetros por voz del generador sin camino |
| Estado del patch (jacks) | sube | orquestación §7.1 | *«Sondeo cada 50 ms, notificación al cambiar»*; sin tamaño declarado |
| Salud | sube | orquestación §7.1 | *«Temperatura de cada placa, tensión de la referencia, estado del esclavo, identidad»*, 1 Hz; sin tamaño declarado |
| Medida de calibración | sube | orquestación §7.1 y §9 punto 3 | *«A petición»*; el formato de los números *«qué manda el módulo para "el oscilador 3 mide 440,12 Hz"»* está abierto |
| Sondeo del panel | sube | latencia_mano, #178 | *«deltas + cabecera»*, 256 bits a 8 kHz — del módulo de mandos, no de la Voz |

Y una regla que los gobierna a todos, la ley del largo: **R-E1, ningún
mensaje del J2 dura más de 100 µs**, y su compañera R-E9: *«Ningún mensaje
nuevo del J2 se declara sin pasar por R-E1»*. Los 100 µs no son bits: el
propio papel del evento declaró **muerta** la equivalencia *«1000 bits a 10
MHz»* (§0.1, 2026-08-27: *«no hay reloj global de 10 MHz»*). Lo que hay es un
reloj **por enlace** (D2 del J2), y hoy todo enlace corre al piso legado
porque `sancion_j2.csv` no tiene una sola fila: al piso, 100 µs son 1000
bits, 125 bytes; a los 34,5 MHz de D8 son 3450 bits. Este papel mide contra
los dos y dice cuál manda en cada cifra. `trama_j2_budget.py` asevera R-E1
contra cada fila declarada, y hoy sus filas no llevan cabecera porque no
había cabecera que sumar (`BITS_EVENTO` lleva el comentario *«SIN cabecera
declarada: la pone el códec del cambio 1 cuando exista»*). Este papel es ese
códec.

---

## 2. Las decisiones

### D1. Una trama, un tipo *(⚠ reescrita por la junta)*

**Cada bajada de `CS` lleva exactamente un mensaje de un tipo.** Nada de
empaquetar varios en una trama.

La v1 lo justificaba por latencia —*«si una trama pudiera llevar tres
mensajes, el mensaje en curso mediría tres»*— y la junta lo desmontó: el
propio `SET` de dieciséis escrituras (D4) es el mensaje más largo del enlace.
Lo que la regla compra de verdad es **una propiedad del parser**: un `tipo`
por trama, R-E5 con un solo «qué» (*«la cabecera dice qué viene y cuánto»*),
y una sola cola de despacho. La latencia la acota **R-E1 por trama**, no esta
regla; el peor caso en vuelo lo fija D4 y lo declara con su número.

Consecuencia que se declara: el largo que dice la cabecera y el largo que
delimita `CS` (D5 del J2: *«la trama es lo que cabe entre bajada y subida de
CS»*) **tienen que coincidir o sobrar por el lado de `CS`**; §5 dice qué pasa
si no.

Y en la subida la regla es otra, porque la subida es otra cosa (D6): **un
registro publicado a la vez**, que el maestro muestrea entero o no muestrea.

### D2. El sobre: cuatro bytes delante, dos detrás

Toda trama de bajada y todo registro de subida llevan el mismo sobre:

```
 byte 0        tipo        u8      qué mensaje (§3.1)
 byte 1        largo       u8      bytes de carga que siguen, 0..=255
 bytes 2-3     secuencia   u16 LE  bajada: contador de tramas emitidas en ESTE
                                   enlace, +1 por trama, da la vuelta (D5 lo
                                   pone a cero). subida: versión del registro
                                   publicado, +1 por publicación
 bytes 4..     carga       largo bytes, lo que el tipo diga (§3)
 2 bytes       crc16       u16 LE  CRC-16/CCITT-FALSE de los PRIMEROS 4 + largo
                                   bytes (cabecera y carga; ni el CRC ni lo que
                                   sigue)
 [relleno]     0x00        solo en bajada, si el giro es más largo (D6)
 [byte de cola] 0x00       solo en bajada, siempre el último byte clocado (D6.4)
```

Seis bytes de sobre. Cada campo tiene un porqué y ninguno es «por si acaso»:

- **`tipo` en un byte**, con el bit alto como dirección —puesto, sube; quitado,
  baja—, que es la convención que `protocolo.rs` ya usa para sus etiquetas
  (*«El bit alto de la etiqueta dice la dirección»*). Los tipos `0x00-0x0F` y
  `0x80-0x8F` son universales, de todo enlace; del `0x10` y del `0x90` en
  adelante son del dialecto que el catálogo del cerebro asocie al tipo de
  placa (D5). Lo universal es **un espacio de nombres y una carga fija**; no
  garantiza semántica de la Voz, y por eso `SALUD` es universal y el estado de
  la Voz va aparte (§3.3, hallazgo V-8).
- **`largo` en un byte** porque R-E1 no deja que haga falta más: al piso
  legado caben 125 bytes de trama y a D8 431; el byte alcanza para los dos y
  el mensaje más gordo de este papel mide 102 (§4).
- **`secuencia` de 16 bits**, que en la bajada es **el reloj lógico del
  enlace**: lo asigna el emisor, una trama perdida deja un hueco y el hueco
  no mueve el número de la siguiente. Es el número del que D4 cuelga el orden
  del bloque de compuerta (hallazgo V-1: *«la verdad y su número de versión
  salen del mismo lado»*). Con 8 bits, a 8 kHz la cuenta daría la vuelta cada
  32 ms y una ráfaga perdida de 256 tramas —el orden del watchdog de §9.2 de
  la Voz total— se confundiría con cero. Con 16 son 7 s a la tasa de tramas
  más alta de §4.
- **CRC-16/CCITT-FALSE, poly `0x1021`, init `0xFFFF`**, el mismo de
  `descubrimiento.rs:59` (*«CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, sin
  reflejar»*, vector canónico `"123456789" → 0x29B1`). No se inventa un
  segundo CRC en el repo. El N657 lo calcula en hardware: la unidad CRC admite
  *«fully programmable polynomial with programmable size (7, 8, 16, 32
  bits)»* y *«Programmable CRC initial value»* (DS14791 Rev 10, §3.19, p.
  41-42). El SPI también trae *«Hardware CRC feature can verify the integrity
  of the communication at the end of transaction»* (p. 74), pero atado a
  `TSIZE`, el número de datos de la transacción, que un receptor de largo
  variable no conoce de antemano; por eso el CRC se computa sobre el búfer al
  subir `CS`, con la unidad. Lo que eso cuesta en ciclos está en §10, riesgo
  5, con la cuenta de la junta.

  > **Enmienda del 2026-10-19 (D2 y D9, del lado del cerebro; tercera firma
  > del transporte del J2, ficha I,
  > `docs/superpowers/juntas/2026-10-17-j2-transporte/acta-2026-10-19-tercera.md`):**
  > en el cerebro el CRC del sobre de la subida se calcula con una tabla de
  > 256 entradas en la DTCM, no con la unidad. Medido en la NUCLEO-N657X0-Q
  > con el J2 en TCM y las dos cachés frías: +236 ciclos por giro y ranura
  > con 25 bytes, contra +361 con la unidad y +1 567 bit a bit (M,
  > `software/nucleo/fw/EN-PLACA.md`, «El CRC del sobre de la subida,
  > medido»). La unidad reproduce el CRC de `crc16`, pero cada escritura en el
  > periférico se paga. Es el mismo CRC-16/CCITT-FALSE: `crc16_con` con
  > `TABLA_CRC16`, probada contra `crc16` en todos los largos de 0 a 130
  > bytes; no es un segundo CRC. En D9, `decodificar` deja de usar `crc16`
  > (bit a bit) y usa `crc16_con` con la tabla donde la ponga quien llama.
  > «Con la unidad» queda para el receptor del módulo, que decide con su
  > propia medida; §10, riesgo 5, no se toca.
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
2026-08-27 lo declara **SIN SUJETO**: R-S5 nunca entró a `main`. Y el
dialecto legado **sí** verificaba integridad, a su manera: *«El firmware
verifica la integridad del enlace comparando lo que manda con lo que vuelve»*
(`docs/modules/03-vco.md:162-165`, el passthrough de la cadena de tres
AD5686R). Esa comparación muere con la cadena —en el dialecto nuevo lo que
vuelve es la subida del módulo, no el eco de la bajada— y el CRC ocupa su
sitio.

Lo que sí sobrevive de aquel argumento, con la precisión que la junta exigió
(hallazgo V-6, V-7): **no hay acuse por mensaje ni retransmisión selectiva en
el dialecto**. El CRC no es un acuse: es la diferencia entre **rechazar** una
trama corrupta y **ejecutarla**. Un `cierra` con un bit volteado en la
instancia cierra otra voz; un `SET` corrupto escribe un parámetro. R-E10
repara lo perdido; el CRC convierte lo corrupto en perdido, que es lo único
que la red sabe reparar. A 34,5 MHz por 74 cm de cinta al lado de audio de 24
bits, y con la marca *«nada de chips baratos»*, dos bytes por trama son el
precio de que el enlace no ejecute basura.

### D3. El sobre no lleva dirección: el `CS` es la dirección *(⚠ la comprobación de ranura de la v1 muere)*

El enlace es punto a punto: el módulo **es** el enlace, y un sobre que dijera
«para la Voz» diría lo que el `CS` ya dice. Es **identidad por cable**, y es
el modelo del periférico, consistente consigo mismo.

Lo que sí lleva cada mensaje que direcciona dentro del módulo es **la
instancia** (el canal, 0-15). Y el `EVENTO` lleva además **el destino de 16
bits que su §3 fijó** —*«ruta de tres niveles + instancia, como `ParamId` sin
índice»*—, que son los bits 23..8 de `ParamId` (`param.rs:17-24`). El módulo
**usa la instancia y trata la ruta como opaca**: no la comprueba. La v1
proponía que el módulo comprobara «que el nivel 1 es el suyo», y la junta lo
tumbó con `param.rs:121-123`: un módulo colgado de un concentrador *«no sabe
dónde está él»*, así que la comprobación rechazaría todo evento a profundidad
2. Se retira, y con ella la `ranura` que `HOLA` llevaba para enseñársela.

Lo que este papel deja dicho y no diseña: **los concentradores** (niveles 2
y 3, `param.rs:29-31`) no existen, y cuando existan el sobre tendrá que
decidir si reenvía por un tipo universal de túnel —una dirección en el sobre,
contra esta D3— o si cada dialecto lleva ruta en todo mensaje —otro dialecto,
R-C6—. Cualquiera de los dos cambia el J2. Y la premisa con la que el núcleo
§3.1.1 justificó la ruta de 32 bits —*«desde el cerebro es un módulo más, así
que el contrato J2 sigue congelado»*— murió con el J2 punto a punto y este
papel la hereda como enmienda pendiente (§11), no como hecho.

### D4. Los mensajes de bajada del dialecto de la Voz, versión 1 *(⚠ `TONO`, `SET` y `COMPUERTA` cambian de mecanismo; `SOLTAR_TODO` se retira)*

Cinco mensajes, y antes de sus bytes, **de qué clase es cada uno**, porque la
junta cazó que la v1 llamaba «mensaje» a tres animales distintos (hallazgo
V-9) y citaba el cambio 1 de orquestación como cumplido por todos:

| Mensaje | Clase de réplica | Clave | Versión | Su red (D7) |
|---|---|---|---|---|
| `EVENTO` | comando con versión | instancia | la `secuencia` del sobre | `COMPUERTA` (R-E10) |
| `TONO` | flujo con deltas, clave implícita en la máscara | instancia | la cadencia | el bloque completo a ≥ 1 kHz |
| `COMPUERTA` | réplica de objeto entero, con versión propia | — | `contador` | ella misma, periódica |
| `BAHIA` | réplica de objeto entero | — | la `secuencia` del sobre | reenvío a 1 Hz |
| `SET` | escritura con clave | (instancia, índice) | ninguna: la última manda | reenvío a 1 Hz |

El cambio 1 de orquestación (*«la trama pasa a llevar parámetros con su
identificador»*) lo cumple `SET`; `TONO` lo cumple con la clave implícita;
`COMPUERTA` y `BAHIA` **no son parámetros con identificador**: son objetos
del modelo replicados enteros, y este papel lo dice en vez de citarlos como
si lo fueran. El byte `tipo` codifica, además de la forma de la carga, la
**clase de réplica**, que es lo que de verdad separa a `TONO` de `SET`
(dieciséis valores por instancia los dos): la clase la decide el planificador
del cerebro, no el módulo.

- **`EVENTO`**: los cuatro campos de evento §3 y nada más, en 7 bytes: destino
  16, borde en un byte entero (`0` abre, `1` cierra, `2` dispara, `3`
  reservado y **rechazado**), fuerza 16 y tono de arranque 16. El borde no se
  empaqueta con otro campo porque dos bits sueltos no le ahorran un byte a
  nadie y le cuestan una máscara a todo el mundo. **Su versión es la
  `secuencia` del sobre**, y el módulo la guarda (D4, `COMPUERTA`).
- **`TONO`**: el bloque agrupado de R-M4 con las deltas de D3 del evento:
  **una máscara de 16 bits de qué instancias vienen, y a continuación un tono
  de 16 bits por cada bit alto, en orden de instancia**. Dieciséis moviéndose
  son 2 + 32 = 34 bytes; cuatro son 10; ninguno son 2. Es más compacto que
  «instancia + valor» por delta y queda alineado a byte. **Y el bloque
  completo —máscara `0xFFFF`— sale por lo menos a 1 kHz aunque nada se
  mueva**: la junta cazó (hallazgo S-3) que la auto-reparación del tono que el
  evento D6 daba por hecha —*«si una trama se pierde, la siguiente trae el
  valor otra vez»*— era del bloque completo, y con deltas una trama rechazada
  dejaba esa voz en el tono viejo hasta que volviera a moverse. R-M4 ya
  mandaba *«la tasa mínima del bloque de tono es 1 kHz por módulo»*; este
  papel le da a esa tasa mínima su segundo oficio: es **la red de las
  deltas**. Entre bloques completos, deltas a la cadencia del lazo.
- **`COMPUERTA`** *(⚠ mecanismo nuevo; enmienda al generador §3.4)*: la
  máscara de compuertas de 16 bits y **el contador**, que ya no es una cuenta
  sino **un número del sobre**: la `secuencia` del último `EVENTO` que el
  cerebro emitió por este enlace antes de armar el bloque (`0` si ninguno
  desde `HOLA`). El módulo guarda `ultimo_evento`, la `secuencia` del último
  `EVENTO` que **aceptó**, y la regla es la de siempre con otro sujeto: **un
  bloque con `contador` menor que `ultimo_evento` es viejo y se ignora; igual
  o mayor, se aplica**, comparando en aritmética de 16 bits con vuelta
  (`wrapping_sub as i16 < 0`, la que `envolvente.rs:392` ya usa).

  Por qué cambia, con el número de la junta: el generador §3.4 hacía que el
  módulo **contara** los eventos recibidos y comparara esa cuenta con la del
  cerebro. Una sola trama de evento rechazada por CRC —la clase de fallo que
  D2 crea a propósito— desplaza la cuenta del módulo en uno **para siempre**,
  y desde ese momento cada bloque armado antes de un evento que lo adelantó
  (D1 del evento) se lee como «igual» en vez de «viejo» y **revierte la nota
  recién abierta o resucita la recién cerrada**. Halberg lo corrió: con una
  pérdida por mil, **1802 bloques dañinos en 60 s**; con dos pérdidas en
  total, 1432 (§12, H-1). Voronov le puso el nombre: el incremento de la
  cuenta viajaba solo en el evento, y por R-E12 *«lo que viaja solo en el
  evento y no lo reafirma un flujo queda sin red»*; el contador que decidía
  si la red se aplica no tenía red. Con la `secuencia` del sobre, el número
  lo asigna el cerebro, la pérdida no lo desplaza, y el invariante que une
  los dos relojes del enlace queda escrito: **el módulo guarda el máximo que
  vio; el cerebro dice cuál era el último al armar**. Ni `resincronizar` ni
  adopción del primer bloque hacen falta: tras `HOLA` los dos números
  arrancan de cero (D5), y tras un watchdog el módulo conserva el suyo y el
  siguiente bloque, con `contador ≥ ultimo_evento`, aplica. La máscara sigue
  siendo *«de compuertas, nunca de disparos»*, y su cadencia sigue reservada
  (R-E11: la elige el oído).
- **`BAHIA`**: la imagen sombra del crosspoint **en la forma del modelo**, no
  en los bits del chip: dos chips × dieciséis canales × una máscara de 16
  líneas, 64 bytes, exactamente `Imagen.filas` de `bahia.rs`. El módulo es
  quien aplica la barrera de cambiados-en-silencio y la política de drones
  (voz-total §5.4: *«el N657 la guarda como "ruta pendiente", aplica la
  barrera…, shiftea y latchea»*), y la barrera razona en canales, no en bits.
  La serialización a los 512 bits (`bahia_serie.rs`) la hace el módulo con su
  orientación y su orden de cadena, constantes de **su** firmware cuando el
  esquemático las fije. **Entra por la misma cola que todo lo demás** (D8): la
  v1 la mandaba «a la barrera» desde la ISR mientras el tick llamaba
  `Barrera::tick`, dos dueños de una copia de 64 bytes que la ISR podía
  rasgar a mitad (hallazgo H-6).
- **`SET`** *(⚠ aterriza distinto; enmienda al generador §3.5)*: escrituras
  de parámetros, **N tuplas de (instancia u8, índice u8, valor i32 LE)**, 6
  bytes cada una, **1 ≤ N ≤ 16**; un largo que no sea múltiplo de 6, N = 0 o
  N > 16 se rechazan. El valor va en los 32 bits con signo que el modelo
  declara para **todo** parámetro (`param.rs:13-15`: *«Entero con signo de 32
  bits, siempre: la escala y la unidad viven en el descriptor»*). La junta
  señaló (V-5) que el enlace ya lleva dos anchos: **16 bits en los flujos**
  (tono, fuerza, máscaras: el ancho de la palabra del DAC y de la velocidad de
  MIDI 2.0) y **32 en las escrituras del modelo**; se declara así en vez de
  llamar «un solo tipo» a lo que son dos. Dieciséis tuplas son 96 bytes: los
  once parámetros de una voz o un parámetro de las dieciséis, en una trama.

  **Dónde aterriza, que la v1 no decía** (hallazgos S-5, V-5, H-7): el cable
  escribe **un parámetro**; `envolvente::Entrada::Parametros` reemplaza **el
  bloque entero del canal**, y traducir tuplas a bloques exige una sombra por
  canal fuera del tick —contra «un solo dueño del estado»— que además pierde
  nueve de diez escrituras por trama. Así que `Entrada` gana **una variante
  por tupla**, `Parametro { canal, indice, valor }`, que el tick aplica al
  campo que el índice nombre; y el dialecto de la Voz lleva **la tabla de
  índices**, con el rango firme de cada uno (generador §7, decisión 11):

  | Índice | Campo de `Parametros` | Unidad | Rango firme |
  |---:|---|---|---|
  | 0 | `vca.ataque_ms` | ms | 1 – 10 000 |
  | 1 | `vca.decaimiento_ms` | ms | 1 – 10 000 |
  | 2 | `vca.relajacion_ms` | ms | 1 – 20 000 |
  | 3 | `vca_sostenido` | ‰ | 0 – 1 000 |
  | 4 | `filtro.ataque_ms` | ms | 1 – 10 000 |
  | 5 | `filtro.decaimiento_ms` | ms | 1 – 10 000 |
  | 6 | `filtro.relajacion_ms` | ms | 1 – 20 000 |
  | 7 | `filtro_sostenido` | ‰ | 0 – 1 000 |
  | 8 | `sensibilidad_fuerza` | ‰ | 0 – 1 000 |
  | 9 | `filtro_cantidad` | cents | −4 800 – +4 800 |
  | 10 | `paneo` | ‰ | 0 – 1 000 |
  | 11-255 | reservados | — | rechazados |

  **Un valor fuera de su rango, o un índice reservado, rechaza la trama
  entera** (D8): el módulo no tiene descriptor y no puede validar con él; la
  tabla es su descriptor parcial, versionado por el byte `dialecto`. La v1
  confiaba el `i32` sin rango, y un `ataque_ms` negativo se convertía en 49
  días. Cuando el descriptor de la Voz exista (voz-total cambios 2 y 12,
  #148), sus índices para estos once parámetros **son estos**; este papel
  los fija primero porque el enlace los necesita antes.

  **Lo que cuesta el 16, dicho con el número.** El evento D1 mide su peor
  caso contra *«lo que le quede al mensaje en curso»*, y el mensaje en curso
  más largo del enlace de la Voz pasa de los 288 bits del bloque de tono
  (28,8 µs al piso) a los 816 de un `SET` lleno: **81,6 µs al piso, 23,7 a
  D8**. Cabe en R-E1 con el 18 % de margen al piso, y a D8 —que es donde la
  Voz va a correr— queda por debajo del peor caso de hoy. Con `SET` de ocho
  tuplas serían 54 bytes y 43,2 µs al piso, a cambio del doble de tramas para
  reafirmar. Este papel elige 16 y lo deja marcado como el único número de
  D4 que mueve una latencia declarada; `tiempo_budget.py` lo hereda solo
  (§9). Y **el cerebro no manda más de un `SET` por giro del lazo (125 µs)**:
  la cola del tick tiene 64 entradas y a D8 cuatro `SET` seguidos la llenan
  en un tick sin dejar sitio a un evento (hallazgo H-8); espaciados, la
  reafirmación de mil parámetros ocupa 63 giros, 7,9 ms, y el tono jitterea
  hasta 66 µs al piso mientras tanto (H-13), 20 a D8. No hay tartamudeo de
  5 ms porque no hay ráfaga.
- **`SOLTAR_TODO` se retira del cable.** La junta (S-15, V-12) cazó que
  ningún papel lo pedía como mensaje: el generador lo lista como algo que
  *«el firmware llama»* por el watchdog, local. Como mensaje su información
  es la de `COMPUERTA` con máscara `0`, que ya cierra todo por R-E10. Así que
  el pánico remoto es `COMPUERTA(0)`, y `Entrada::SoltarTodo` lo produce el
  firmware del módulo en dos casos locales: el watchdog de trama (voz-total
  §9.2) y la sesión nueva (D5). El tipo `0x15` queda reservado.

### D5. El enlace tiene sesión, y `HOLA` es su único mensaje *(⚠ reescrita: la v1 tenía una sesión sin saberlo)*

La junta lo dijo con todas las letras (V-6): *«Una réplica necesita sesión;
la doctrina la prohíbe; el papel la construye en la capa universal y la
nombra de otra forma»*. Se nombra. **`HOLA` es el establecimiento de sesión
del enlace**, y es el único sitio del J2 donde hay un intercambio de dos
pasos. La doctrina del evento queda, con su alcance dicho, en **«sin acuse
por mensaje ni retransmisión selectiva en el dialecto»** (D2).

**Lo que baja.** Antes de la primera palabra de un dialecto, el cerebro manda
`HOLA`, tipo universal, con la `secuencia` a **cero**, y dos bytes: la versión
de la cabecera (`1`) y el dialecto que va a hablar. El dialecto **sale del
catálogo del cerebro, por el tipo de placa** que la identidad EEPROM ya
declara (`descubrimiento.rs:8-15`: magia, versión de cabecera `1`, tipo,
revisión, serial, CRC): la v1 decía que la EEPROM «declara dialecto» y la
junta (S-10) cazó que no hay tal campo y que añadirlo obliga a subir la
versión que `leer_identidad` rechaza. El catálogo es la fuente única; la
EEPROM se queda en su versión 1. Lo mismo vale, y se dice para el papel del
J2, para el *«reloj declarado»* de su D2, que tampoco está en la EEPROM:
**catálogo por tipo de placa hasta que la identidad gane versión 2**. Los
dialectos con número: `0` legado (72 bits, sin sobre), `1` Voz v1.

**Lo que hace el módulo al recibirlo.** Si versión y dialecto son los suyos:
abre sesión. Y abrir sesión es, en orden: encolar `Entrada::SoltarTodo`
(todo a relajación, compuertas a cero; si el módulo acaba de arrancar no
cuesta nada, y si el cerebro reabre sesión sobre un módulo vivo, cierra lo
que el cerebro ya no sostiene), poner `ultimo_evento` a `0`, esperar la
`secuencia` `1`, poner a cero los contadores de `SALUD`, poner a cero su
propia `secuencia` de subida, abandonar el registro que estuviera publicando
y publicar **su `HOLA`** con `sesión = 1`. Si versión o dialecto no cuadran,
no abre sesión y su `HOLA` lo dice.

**Lo que sube, y por qué no es un acuse** (V-6): el `HOLA` de subida es un
**registro de estado**, no un veredicto: *versión que hablo, dialecto que
hablo, tengo sesión sí/no, cuántas sesiones he abierto desde que arranqué*.
El cerebro computa la compatibilidad; el módulo no la juzga. Y ese registro
es **lo único que el módulo publica mientras no tiene sesión**, en todos los
giros: un módulo que arranca o que el watchdog independiente de R-M5 reinicia
en sesión (motor-digital §7: *«los VCAs y el crosspoint caen a silencio sin
CPU»*) aparece en el siguiente muestreo del cerebro diciendo «sin sesión», y
el cerebro le manda `HOLA`. Es el mismo patrón de reafirmación de D7 aplicado
a la sesión: el estado se publica, el cerebro lo compara con lo que cree, y
repara. La v1 lo tenía como «regla propuesta y no sellada» (§7.9) y la junta
lo hizo BLOCKER dos veces (S-1, H-11); se sella, con las dos precisiones que
faltaban:

1. **El cerebro reenvía `HOLA` solo al muestrear `sesión = 0`**, nunca al ver
   `sesión = 1`. Los dos son el mismo tipo `0x81`; los distingue el campo. Sin
   eso, la respuesta al `HOLA` disparaba otro `HOLA` y el enlace entraba en un
   ping-pong que ponía las cuentas a cero cada dos giros (H-11).
2. **Tras `HOLA`, el cerebro manda la reafirmación completa antes del primer
   `COMPUERTA` y del primer `EVENTO`**: `SET` de todo (espaciado, D4), `BAHIA`,
   y solo entonces la cadencia normal. Sin ese orden, el `COMPUERTA` a 5-50 ms
   llegaba antes que los parámetros y las notas sostenidas volvían con los
   tiempos semilla del firmware hasta su siguiente redisparo (H-12). Cuesta
   7,9 ms de notas retenidas tras un reinicio, que es un módulo que acaba de
   estar muerto.

`HOLA` **no** hace que el módulo diga nada en el mismo giro: el registro de
subida se prepara antes de que `CS` baje (D6), así que la respuesta va en el
giro siguiente. Y `HOLA` con versión `≠ 1` o dialecto desconocido se rechaza
por forma como cualquier otra trama; el `HOLA` de subida seguirá diciendo
`sesión = 0` con lo que el módulo habla, que es toda la información que el
cerebro necesita para saber qué pasa.

> **Enmienda del 2026-10-20:** un `HOLA` con versión `≠ 1` o con un dialecto
> que el módulo no habla se rechaza **por tipo**, no por forma: la carga tiene
> la forma de `HOLA`, y lo que falla es que el módulo no habla esa versión. Da
> `ErrorTrama::Tipo` y cuenta en `rechazadas_tipo`, como ya decía §3.3. Si el
> módulo tenía sesión, ese `HOLA` **la cierra**: el módulo solo publica su
> `HOLA` sin sesión, así que con la sesión abierta el cerebro no vería el
> desacuerdo y seguiría escribiendo en un dialecto que el módulo lee con el
> viejo. Lo que estuviera sonando lo suelta el watchdog de trama (voz-total
> §9.2), porque sin sesión ninguna trama es válida. Abrir sesión llega al
> generador como **una sola entrada, `Entrada::Sesion`**, que suelta todo como
> `SoltarTodo` y pone `ultimo_evento` a cero; `SoltarTodo` queda para el
> watchdog, y lo que D4 dice de la sesión nueva pasa a `Entrada::Sesion`. El
> lado del módulo es `dialecto_voz::Receptor` (`core/src/dialecto_voz.rs`),
> con el test 14 de §8. Lo que toca a la subida (su `secuencia` a cero, el
> registro a medias abandonado y el `HOLA` con `sesión = 1`) llega con los
> registros de §3.3.

La versión **no viaja en cada trama**. Viaja en `HOLA` y en el catálogo: una
cabecera que cambie de forma es un dialecto nuevo. Un byte de versión por
trama a 8 kHz sería 64 kbit/s para decir siempre `1`.

### D6. La subida es un registro que el maestro muestrea *(⚠ reescrita: era «trama» en la v1 y no lo es)*

D4 del J2 abrió el canal: *«cada trama de bajada puede traer simultáneamente
su subida»*. La v1 llamó «trama» a lo que sube y la junta (V-2, V-10) mostró
que por la definición de D5 del J2 no lo es: una trama es lo que cabe en un
giro, y la subida se prepara antes del `CS`, se cloca a trozos y sobrevive a
giros cortos. La ontología honesta la dio R-J3 —*«El módulo nunca habla sin
que le pregunten»*— y R-E7 —*«El módulo no genera eventos… el evento que
resulte lo emite el cerebro»*—: **la subida es estado que el módulo publica y
el maestro muestrea**. Con eso, las reglas:

1. **El registro lleva el sobre de D2** (mismos bytes, bit alto del tipo
   puesto), con `secuencia` = versión del registro (+1 por publicación) y CRC
   sobre el registro. El módulo lo deja en su búfer de transmisión **antes**
   de que el `CS` baje, y el esclavo SPI lo shiftea al ritmo que el maestro
   dé.
2. **El módulo mantiene publicado el mismo registro hasta que un giro lo
   haya muestreado entero**, y solo entonces publica el siguiente. «Entero»
   se mide en bytes completos recibidos en ese giro —un byte a medias no
   cuenta—, **descontando el byte de cola** (regla 4): `bytes_recibidos − 1 ≥
   largo + 6`. Es local, determinista y no necesita acuse. El cerebro, por su
   lado, sabe cuántos bytes clocó y solo intenta leer un registro cuando clocó
   por lo menos `largo + 7`.
3. **La cadencia de muestreo es del maestro, no del módulo** (V-10). Cada
   enlace declara **`F_SUBIDA`**: la cadencia a la que el cerebro garantiza un
   giro de por lo menos `VENTANA_SUBIDA + 1` bytes clocados. Para la Voz,
   `F_SUBIDA` es el giro del lazo (8 kHz): el `TONO` se cloca con relleno a
   `0x00` **después del CRC** —el CRC no lo cubre y el receptor no lo mira—
   hasta la ventana. Para un dialecto sin bajada periódica, el cerebro cloca
   `NADA` a su `F_SUBIDA`. Las «cadencias» del módulo (`SALUD` a 1 Hz, `JACKS`
   a 20 Hz) son cadencias de **publicación**: el registro sale en el siguiente
   muestreo. La ventana es **una constante del dialecto** (R-P1: nada de un
   enlace gobierna a otro), y la de la Voz es **24 bytes de registro**, con
   sobre: cabe `SALUD` (18), `ESTADO_VOZ` (14) y `HOLA` (10) con holgura; el
   módulo de mandos declarará la suya con su papel (#178: su sondeo del panel
   son 32 bytes de deltas). El piso universal es `|SALUD| = 18`.
4. **El byte de cola** *(⚠ nuevo; hallazgos S-4, V-11, H-5)*: **el maestro
   cloca siempre un byte más que la trama de bajada**, relleno incluido. D8
   del J2 —*«el maestro lee la subida corrida un ciclo»*— corre la subida **un
   bit**, no un byte: la junta lo derivó con los flancos (H-5): la única
   variante con hardware SPI en los dos extremos que deja la bajada alineada
   es maestro en modo 0 y esclavo en modo 1, y en ella el primer muestreo del
   maestro es la línea en reposo y **el último bit del registro cae en un
   reloj que un giro exacto no da**. Con el byte de cola el maestro recibe
   todos los bits y corre el búfer de subida un bit a la izquierda; sin él,
   el registro que llena exactamente la ventana se perdía **en cada giro**:
   Halberg midió `SALUD` saliendo una vez por segundo, en el giro de la
   reafirmación de `BAHIA`, y nunca sin ella. En el peldaño 1 (respuesta en el
   mismo ciclo) el byte sobra y no estorba. Cuesta 8 bits por giro: 64 kbit/s
   a 8 kHz, 0,6 % del piso. Y de paso cierra otro hallazgo (H-14): con ocho
   relojes de cola, el último byte de datos ya salió de la FIFO y del DMA
   cuando `CS` sube, y contar los bytes en el flanco no compite con el DMA.

Lo que cuesta, con el número: al piso legado, un giro de `TONO` en silencio
pasa de 9 a 25 bytes clocados; a 8 kHz son 16 × 8 × 8000 = 1,02 Mbit/s =
**10,2 %** del enlace, 3,0 % a D8. Es el precio de que la subida no dependa
de que suene algo. Con eso, la simulación de vivacidad de la junta (§12,
H-vivacidad) da `SALUD` en ≤ 55 µs y `JACKS` en ≤ 54 µs al piso, y `HOLA` en
≤ 10 µs.

Lo que **no** se decide: el formato de la carga de `JACKS`, `MEDIDA` y `LOG`
—son de otros papeles (§7)—, y el troceo de un registro más largo que la
ventana: en v1 **ningún registro de la Voz supera los 24 bytes**, y el que lo
necesite (el log de telemetría) trae su troceo en su papel.

### D7. La verdad de todo lo que baja se reafirma, y «reafirmar» tiene nombre *(⚠ precisada)*

R-E12 del evento: *«todo lo que viaje solo en el evento y no lo reafirme un
flujo periódico queda sin red»*. Con D2 la trama corrupta se rechaza en vez
de ejecutarse, y eso convierte cada mensaje en un mensaje **que puede
perderse**. Este papel decide que **ninguno de los que bajan queda sin red**,
y dice cuál es la red de cada uno y **de qué clase es**:

| Mensaje | Su red | Clase | Cadencia | De dónde |
|---|---|---|---|---|
| `HOLA` | el registro `HOLA` de subida con `sesión = 0` | sesión | cada muestreo sin sesión | D5 |
| `EVENTO` | el bloque `COMPUERTA` (R-E10) | flujo | reservada, R-E11 | evento D6 |
| `TONO` | el bloque completo | flujo | ≥ 1 kHz (R-M4) | D4 |
| `COMPUERTA` | ella misma, periódica | flujo | reservada, R-E11 | evento R-E11 |
| `BAHIA` | **refresco**: el cerebro reenvía la imagen vigente | refresco | **1 Hz** | este papel |
| `SET` | **refresco**: el cerebro reenvía todos los parámetros del módulo, un `SET` por giro | refresco | **1 Hz** | este papel |
| `dispara` (dentro de `EVENTO`) | **ninguna, declarada** | — | — | evento D6 enmienda 1: *«un `dispara` perdido es un golpe perdido»* |

La junta (V-7) marcó que la v1 llamaba «flujo» a dos cosas: **un flujo lleva
la evolución** (evento D2) y su reparación es un efecto lateral gratis; **un
refresco reenvía periódicamente un estado que no cambió**, sin selección. Son
dos mecanismos; la tabla los rotula. Con eso, la doctrina del evento queda en
lo que de verdad sobrevive: sin acuse por mensaje, sin retransmisión
selectiva. El refresco es retransmisión ciega, y se llama así.

Por qué refresco en vez de acuse: es la doctrina del evento, y además es más
barato. Refrescar la bahía es una trama de 70 bytes por segundo; refrescar
mil parámetros son 63 tramas de 102 bytes por segundo, 51 kbit/s, **0,5 %**
del enlace al piso, **0,15 %** a D8. Un acuse pediría estado en los dos
extremos y una máquina de reintento, y la lección del #201 es que la
fiabilidad que no se puede verificar no se optimiza: se repara.

**Un refresco idéntico tiene que ser inocuo, y en `bahia.rs` hoy no lo es**
(hallazgos S-6, H-10): `Barrera::proponer` reinicia `desde_ms` siempre
—*«La última manda: … el reloj del timeout arranca de nuevo»*, `bahia.rs:
195-198`— así que con refresco a 1 Hz un `Forzar{timeout ≥ 1 s}` no vencería
jamás; y devuelve `Some(Commit{cambian: 0})` para la imagen ya activa, que el
firmware latchearía una vez por segundo sobre el supuesto **sin verificar**
de que el latch no glitchea (voz-total §11.2). Así que la reafirmación de
`BAHIA` no entra por `proponer`: entra por **`Barrera::reafirmar(&Imagen)`**,
que no hace nada si la imagen es la activa o la pendiente —ni `Commit`, ni
reloj— y solo si es distinta de las dos la trata como propuesta. Un `SET`
refrescado escribe lo que ya estaba, que es inocuo por construcción.

**«Vigente» es lo que el modelo del cerebro tiene ahora**, y el enlace tiene
**un solo escritor** en el cerebro (R-C8): el planificador de esa ranura
genera el cambio y el refresco desde el mismo estado. La carrera que la
junta planteó —un refresco de la imagen anterior pisando una pendiente— no
tiene dónde nacer si nadie más escribe el enlace.

> **Enmienda del 2026-10-20:** reafirmar la imagen **activa** no deja la
> pendiente donde está: la descarta. El cable no distingue el refresco del
> cambio, así que todo `BAHIA` entra por `reafirmar`, y la activa es también
> lo que manda el cerebro cuando la mano deshace una ruta que todavía espera
> el silencio. Con «no hace nada» la ruta deshecha se quedaba pendiente, el
> refresco de la activa la ignoraba cada segundo, y se latcheaba en el
> siguiente silencio; bajo `diferir` con un drone, eso puede ser minutos
> después. Descartarla no da `Commit` ni toca el chip. La pendiente
> reafirmada sigue sin mover el reloj, y una imagen distinta de las dos sigue
> siendo propuesta. Código: `Barrera::reafirmar` en `core/src/bahia.rs`, con
> el test 16 de §8 y el de la ruta deshecha.

El 1 Hz es la cadencia de la salud (orquestación §7.1) y se elige por la
misma razón que R-E11 eligió la suya: **lo fija la tolerancia, no el
presupuesto**. Un parámetro perdido es un mando que no responde hasta un
segundo; una bahía perdida es un cable que no suena hasta un segundo. Si el
bring-up mide una tasa de rechazo que lo haga oír, la cadencia sube en el
guion, que es donde vive.

### D8. Un receptor que rechaza entero y cuenta, y encola todo

El receptor **nunca aplica media trama**. Rechaza la trama completa —y suma
uno al contador de la causa, que sube por `SALUD`— cuando:

1. `CS` sube con menos bytes que `largo + 7` (trama corta; el byte de cola
   cuenta);
2. el CRC no cuadra;
3. el `tipo` no es de su dialecto ni universal, **o no hay sesión y no es
   `HOLA`**;
4. la carga no tiene la forma del tipo: `SET` con largo no múltiplo de 6, N
   = 0 o N > 16, índice reservado o valor fuera de rango; `EVENTO` con borde
   `3`; `BAHIA` con largo distinto de 64; instancia ≥ 16 donde haya
   instancia; `HOLA` con largo distinto de 2.

Y **no rechaza** por secuencia: un salto de secuencia se cuenta como tramas
perdidas y la trama que llegó se aplica. El orden en el enlace es el del
cable; el único orden que el modelo defiende es el del `contador` de
`COMPUERTA` frente a `ultimo_evento` (D4), y los dos son números del cerebro.

Lo que el receptor hace con una trama buena: **la ISR del esclavo encola y
vuelve; el tick drena** (generador §3.5). Todo lo que llega entra a la misma
cola: `EVENTO`, `COMPUERTA`, cada tupla del `SET`, y también `BAHIA`, porque
**el tick es el único dueño de los generadores y de la barrera** (H-6). El
`EVENTO` entra **entero** —borde, fuerza y tono de arranque en una sola
entrada— y el tick aplica el tono de arranque al camino del tono y el borde
al generador **en la misma pasada de drenado**: el evento llega indivisible
por el cable (evento D2: *«son el mismo mensaje, indivisible»*) y la v1 lo
partía en dos dueños, con hasta un tick entre las mitades (H-9). El `TONO`
va al camino del tono desde el tick también, por la misma cola.

**El gap mínimo entre tramas**, que motor-digital §7 hizo *«cláusula del
contrato del enlace»*, tiene ahora dos mitades con dueño (hallazgo H-4):

- **La ISR del módulo rearma el DMA de recepción antes de validar nada**
  (contar, CRC, despachar): así el gap que exige es el del rearme, 0,56 µs en
  la cuenta de la junta con sus hipótesis (§12), no los 1,51 del orden de la
  v1.
- **El cerebro lo respeta con un temporizador de su planificador**, no con
  el hardware: la v1 decía que el SPI del maestro lo imponía con sus *«retardos
  mínimos»*, y la junta leyó la hoja: esos retardos (MIDI/MSSI, 0-15 SCK)
  viven **dentro** de la transacción; no hay mínimo de `CS` inactivo entre
  transacciones. Así que **`T_GAP`** es una constante del planificador del
  cerebro, **HUECO hasta el bring-up**, con valor provisional de **2 µs**, y
  R-E2 del evento (el evento puede salir entre dos tramas) se lee con `T_GAP`
  dentro. A 34,5 MHz son 69 relojes; a D8 un `EVENTO` pegado a un `SET` sin
  gap clocaba 6,5 de sus 13 bytes con el esclavo todavía en la ISR y se
  perdía.

### D9. Dónde vive el código, y qué le pasa al dialecto legado

- **`core/src/j2.rs`** gana el sobre universal: las constantes con cita, el
  `tipo` universal, `Cabecera`, `codificar` y `decodificar` con su
  `ErrorTrama` (una variante por causa de D8), el CRC reutilizado de
  `descubrimiento::crc16`, y `carga_max(reloj_hz)`. Deja de decir *«Contrato
  CONGELADO»* en su cabecera: el contrato del enlace es este.
- **`core/src/dialecto_voz.rs`** (nuevo): los cinco mensajes de bajada de D4
  y los registros de subida de §3.3 como un `enum Mensaje`, con su
  codificación a carga y su decodificación, la tabla de índices con sus
  rangos, y la traducción a `envolvente::Entrada`. Es el «códec nuevo con su
  test de ida y vuelta» que orquestación cambio 1 pidió el 2026-08-22.
- **`core/src/envolvente.rs`** cambia en dos sitios, y son enmiendas al
  generador que §11 manda: `Entrada::Evento` gana `secuencia: u16` y
  `Generadores` guarda `ultimo_evento` en vez de contar `recibidos` (D4);
  `Entrada` gana `Parametro { canal, indice, valor }` (D4). `resincronizar`
  muere: no hace falta.
- **`core/src/bahia.rs`** gana `Barrera::reafirmar` (D7).
- **El dialecto legado no se borra**: `tramas_vco4` y su test de 72 bits se
  quedan en `j2.rs` bajo un rótulo *dialecto legado del módulo 3 v1*, tal como
  orquestación cambio 1 mandó (*«El test de 72 bits no se borra: se convierte
  en el caso "módulo con tres AD5686R en cadena"»*). Un módulo cuyo tipo de
  placa el catálogo asocie al dialecto `0` se habla sin sobre; su enlace corre
  al piso legado (D2 del J2).

---

## 3. Los bytes

### 3.1 Los tipos

| Tipo | Nombre | Dirección | Universal o dialecto |
|---|---|---|---|
| `0x00` | `NADA` | baja | universal: un giro sin mensaje, para muestrear la subida |
| `0x01` | `HOLA` | baja | universal (D5) |
| `0x02-0x0F` | reservados | baja | universal |
| `0x10` | `EVENTO` | baja | dialecto de la Voz, v1 |
| `0x11` | `TONO` | baja | ídem |
| `0x12` | `COMPUERTA` | baja | ídem |
| `0x13` | `BAHIA` | baja | ídem |
| `0x14` | `SET` | baja | ídem |
| `0x15` | reservado (fue `SOLTAR_TODO`) | baja | ídem |
| `0x80` | `NADA` | sube | universal: el módulo no tiene nada que publicar |
| `0x81` | `HOLA` | sube | universal (D5) |
| `0x82` | `SALUD` | sube | universal: carga fija, de todo módulo |
| `0x83-0x8F` | reservados | sube | universal |
| `0x90` | `JACKS` | sube | dialecto de la Voz; carga de otro papel |
| `0x91` | `MEDIDA` | sube | ídem |
| `0x92` | `LOG` | sube | ídem |
| `0x93` | `ESTADO_VOZ` | sube | dialecto de la Voz (§3.3) |

### 3.2 Las cargas de bajada

```
HOLA        largo 2    [version=1 u8][dialecto u8]           secuencia = 0
NADA        largo 0
EVENTO      largo 7    [destino u16 LE][borde u8][fuerza u16 LE][tono u16 LE]
                       destino = bits 23..8 de ParamId: nivel1<<12 | nivel2<<8 | nivel3<<4 | instancia
                       borde   = 0 abre · 1 cierra · 2 dispara · 3 rechazado
                       la ruta (niveles) es opaca para el módulo; usa la instancia
TONO        largo 2+2n [mascara u16 LE][tono u16 LE × n], n = bits altos de la máscara,
                       en orden de instancia ascendente; mascara 0xFFFF = bloque completo
COMPUERTA   largo 4    [mascara u16 LE][contador u16 LE]
                       contador = secuencia del último EVENTO emitido antes de armar (0 si ninguno)
BAHIA       largo 64   [entrada: 16 × u16 LE][salida: 16 × u16 LE]
                       = Imagen.filas[chip][canal], bit i = línea i, chip 0 = Entrada
SET         largo 6n   [instancia u8][indice u8][valor i32 LE] × n, 1 ≤ n ≤ 16
```

### 3.3 Los registros de subida

```
NADA        largo 0
HOLA        largo 4    [version u8][dialecto u8][sesion u8][sesiones u8]
                       sesion   = 0 sin sesión · 1 en sesión
                       sesiones = cuántas ha abierto desde que arrancó (da la vuelta)
SALUD       largo 12   [temperatura_centesimas i16 LE]   del 0x48 de memoria.rs
                       [vref_milivoltios u16 LE]
                       [rechazadas_crc u16 LE]           D8 causa 2
                       [rechazadas_forma u16 LE]         D8 causas 1 y 4
                       [rechazadas_tipo u16 LE]          D8 causa 3 (tipo, sin sesión, versión)
                       [perdidas u16 LE]                 huecos de secuencia entre tramas ACEPTADAS
ESTADO_VOZ  largo 8    [cola_desbordada u16 LE]          entradas descartadas (generador §3.5)
                       [ultimo_evento u16 LE]            la secuencia que COMPUERTA compara (D4)
                       [bahia_aplicada u16 LE]           secuencia de la última BAHIA activa
                       [watchdogs u16 LE]                disparos del watchdog de trama
JACKS       largo ?    otro papel (orquestación §7.1: «qué jacks tienen cable; el valor de cada entrada»)
MEDIDA      largo ?    otro papel (orquestación §9 punto 3: unidad, resolución, crudo o cents)
LOG         largo ?    otro papel; en v1 no se emite
```

Semántica de los contadores, que la v1 dejaba doble (S-14, H-15): todos son
**totales desde la sesión** en `u16` con vuelta, y el cerebro los lee como
**deltas entre muestreos**; a la tasa de tramas más alta de §4 dan la vuelta
en 7 s, así que el delta es unívoco mientras no se pierdan más de seis
`SALUD` seguidas a 1 Hz. Una trama rechazada también deja hueco de
secuencia, así que **`perdidas ≥ rechazadas`** y las perdidas de verdad son
`perdidas − (rechazadas_crc + rechazadas_forma + rechazadas_tipo)`.
`ultimo_evento` y `bahia_aplicada` no son contadores: son valores de
secuencia, y el cerebro los compara con los suyos con la misma aritmética de
vuelta.

La cola de publicación del módulo: `HOLA` en cada muestreo mientras no haya
sesión y una vez al abrirla; con sesión, `SALUD` a 1 Hz, `ESTADO_VOZ` a 1 Hz,
`JACKS` a 20 Hz o al cambiar, `MEDIDA` cuando haya barrido, y `NADA` cuando
no toque nada. Un registro a la vez (D1).

> **Enmienda del 2026-10-20 (la subida en código):** los registros son
> `dialecto_voz::Registro`, con `codificar` del lado del módulo y
> `decodificar_registro` del lado del cerebro, y `VENTANA_SUBIDA = 24`
> (tests 1 y 8 de §8). Un `HOLA` de subida con `sesion` distinto de 0 y de 1
> se rechaza por forma. La publicación vive en `dialecto_voz::Receptor`, y lo
> que este papel no fijaba queda así:
>
> - `Receptor::recibir` recibe todos los bytes que el maestro clocó en el
>   giro, relleno y cola incluidos, y con ellos mide si el registro salió
>   entero (D6.2).
> - El `HOLA` de la sesión nueva sale con la `secuencia` **0**, como el `HOLA`
>   de bajada; la publicación siguiente es la 1.
> - Abrir sesión descarta también lo pedido que aún no salió: era de la
>   sesión vieja, y sus cuentas también.
> - Cerrar la sesión (el `HOLA` que el módulo no habla, enmienda de D5)
>   abandona el registro a medias y publica el `HOLA` con `sesión = 0`: sin
>   sesión no sale otra cosa.
> - Lo pedido sale en orden fijo, `SALUD` y después `ESTADO_VOZ`, uno por
>   muestreo, y de cada uno sale lo último pedido. La cadencia de 1 Hz la
>   lleva quien pide (`Receptor::pedir`), no el receptor.

---

## 4. Los largos contra R-E1

Sobre de 6 bytes en todo, y en la bajada el byte de cola de D6.4. Piso
legado 10 MHz (`trama_j2_budget.py`, `F_CONTRATO_HZ`); D8 34,5 MHz
(`enlace_budget.py`, `F_PELDANO_2_HZ`).

| Mensaje | carga | clocados (bytes) | bits | µs a 10 MHz | µs a 34,5 MHz |
|---|---:|---:|---:|---:|---:|
| `HOLA` | 2 | 9 | 72 | 7,2 | 2,1 |
| `EVENTO` | 7 | 14 | 112 | 11,2 | 3,2 |
| `TONO`, nada cambió | 2 | 9 → **25** con relleno (D6) | 200 | 20,0 | 5,8 |
| `TONO`, dieciséis | 34 | 41 | 328 | 32,8 | 9,5 |
| `COMPUERTA` | 4 | 11 → **25** con relleno | 200 | 20,0 | 5,8 |
| `BAHIA` | 64 | 71 | 568 | 56,8 | 16,5 |
| `SET`, dieciséis | 96 | 103 | 824 | 82,4 | 23,9 |
| `NADA` para muestrear | 0 | 7 → 25 | 200 | 20,0 | 5,8 |

Todos por debajo de los 100 µs al piso; el más largo, `SET` con dieciséis,
usa el 82 %. **El techo de carga que R-E1 permite depende del reloj del
enlace**, y este papel lo declara como función y no como número, para no
resucitar la equivalencia que el evento §0.1 mató: `carga_max(reloj) =
reloj × 100 µs / 8 − 7`, que al piso da **118 bytes** y a D8 daría 424, donde
el `largo` de un byte recorta a 255. Un test la asevera en los dos relojes
(§8), para que un mensaje futuro se tope con ella en el host, no en la placa.
Y con eso queda dicho lo del «mañana» de 512 bits por chip del crosspoint
(H-15): 128 bytes de carga son 135 clocados, 108 µs al piso, **fuera de R-E1
mientras no haya sanción**; es un dialecto nuevo (R-C6) o una ranura
sancionada, no una enmienda a este.

**Lo que se mueve en los guiones al pasar de 288 a 824 bits de trama más
larga**: `tiempo_budget.py` ya deriva `BITS_TRAMA_J2` y `T_TRAMA_J2` del
enlace de la Voz (`:43-44`: *«BITS_TRAMA_J2 = _VOZ.trama_mas_larga_bits()»*)
y asevera `T_TRAMA_J2 < 0.1 × OBJETIVO_S` (`:109-113`); con `SET` pasa de
28,8 a 82,4 µs al piso y sigue verde. Su otra aserción, `BITS_TRAMA_J2 >=
BITS_BLOQUE_TONO` (`:123-125`), también.

Ocupación del enlace de la Voz, bajada, con las cadencias declaradas:

| Flujo | bits | cadencia | bit/s | % a 10 MHz | % a 34,5 MHz |
|---|---:|---:|---:|---:|---:|
| `TONO` peor caso (todo delta, dieciséis) | 328 | 8 kHz | 2 624 000 | 26,2 | 7,6 |
| `TONO` en silencio (relleno) | 200 | 8 kHz | 1 600 000 | 16,0 | 4,6 |
| `TONO` completo (la red, dentro del peor caso) | 328 | 1 kHz | 328 000 | 3,3 | 1,0 |
| `COMPUERTA` a 200 Hz (la más alta de R-E11) | 200 | 200 Hz | 40 000 | 0,4 | 0,1 |
| refresco `BAHIA` | 568 | 1 Hz | 568 | 0,006 | 0,002 |
| refresco `SET` (1000 parámetros, 63 tramas) | 824 | 63 Hz | 51 912 | 0,5 | 0,15 |
| **peor caso sumado** | | | **2 716 480** | **27,2** | **7,9** |

Contra el techo del 50 % por enlace (D6 del J2), cabe con margen al piso. La
ocupación es un promedio, y la junta (H-13) recordó que la ranura de 125 µs
al piso no aguanta `SET` + `TONO` + `EVENTO` + gaps (82,4 + 32,8 + 11,2 + 3 ×
2 = 132 µs): por eso el `SET` va uno por giro y el tono jitterea hasta 66 µs
al piso durante el refresco, 20 a D8. La cifra de `trama_j2_budget.py` para
el bloque de tono (288 bits, 23 %) sube a 328 (26,2 %): §9 lo manda.

---

## 5. Las reglas

> **R-C1. Una trama, un tipo, y el largo lo dicen dos veces.** La cabecera
> dice `largo`; `CS` delimita la trama. Si `CS` trae menos que `largo + 7`,
> la trama se rechaza entera; si trae más, lo que sobra es relleno y cola y
> no se mira. Vigila: los tests de trama corta y de relleno (§8).

> **R-C2. Ninguna trama se aplica sin CRC bueno.** La corrupción se rechaza y
> se cuenta; nunca se ejecuta y nunca se «corrige». Vigila: el test de
> mutación byte a byte (§8).

> **R-C3. La secuencia cuenta, no rechaza.** Un salto es tramas perdidas y sube
> por `SALUD`; la trama que llegó se aplica. Vigila: el test 12 (§8).

> **R-C4. Lo que baja tiene red, y la red está en la tabla de D7 con su
> clase.** Un mensaje nuevo de bajada entra con su fila —flujo, refresco o
> sesión— o entra declarado sin red, como `dispara`. Vigila:
> `trama_j2_budget.py`, cuya `Fila` gana el campo `red` y cuyo juez falla si
> una fila de bajada no lo declara ni está en la lista `SIN_RED` (§9).

> **R-C5. La subida vive dentro de la ventana del dialecto.** Un registro más
> largo que `VENTANA_SUBIDA` no existe en v1; el que lo necesite trae su
> troceo. Vigila: el test que asevera cada registro de §3.3 ≤ ventana (§8).

> **R-C6. La versión viaja en `HOLA` y en el catálogo, nunca en la trama.** Una
> cabecera de otra forma es otro dialecto. Vigila: el test que congela el
> sobre (§8, test 15): seis bytes, los tipos universales, `VERSION = 1`.

> **R-C7. Sin sesión no hay dialecto.** El módulo rechaza todo lo que no sea
> `HOLA` mientras no tenga sesión, y publica solo su `HOLA`; el cerebro
> reenvía `HOLA` al muestrear `sesión = 0` y nunca al muestrear `sesión = 1`;
> y tras `HOLA` refresca todo antes del primer `COMPUERTA` o `EVENTO`.
> Vigila: los tests 13 y 14 (§8).

> **R-C8. El enlace tiene un solo escritor en el cerebro**: el planificador de
> la ranura. Cambio y refresco salen del mismo estado, `T_GAP` lo pone él, y
> el `SET` va uno por giro. Vigila: es doctrina del firmware del cerebro
> (#250); sin puerta hasta que exista, y se dice.

---

## 6. Qué muere, qué sobrevive, qué nace

| | Qué | Nota |
|---|---|---|
| **Muere** | *«Contrato CONGELADO por el módulo 3»* en `j2.rs:1` | D9: el contrato del enlace es el sobre |
| **Muere** | `BITS_EVENTO` *«SIN cabecera declarada»* en `trama_j2_budget.py` | §4: 112 bits clocados |
| **Muere** | El 288 del bloque de tono como cifra de guion | §4: 328 con sobre, máscara y cola |
| **Muere** | La cuenta local de eventos recibidos del generador §3.4 | D4: el contador es la secuencia del sobre |
| **Muere** | `SOLTAR_TODO` como mensaje del cable | D4: `COMPUERTA(0)` es el pánico; `SoltarTodo` es local |
| **Muere** | La comprobación de ranura del evento (v1 D3) y la `ranura` de `HOLA` | D3: el `CS` es la dirección |
| **Muere** | «Sin acuse ni retransmisión» como doctrina del enlace entero | D2/D5: sin acuse por mensaje en el dialecto; `HOLA` es sesión |
| **Sobrevive** | Los cuatro campos del evento (§3 del evento) | D4: mismos campos, ahora con bytes |
| **Sobrevive** | R-E1, R-E4, R-E5, R-E7, R-E9, R-E10, R-E11, R-E12, R-J3, R-M4 | Todas ejecutables ahora; R-M4 con segundo oficio |
| **Sobrevive** | El dialecto legado de 72 bits y su test | D9 |
| **Sobrevive** | `crc16` de `descubrimiento.rs` | D2: un solo CRC en el repo |
| **Nace** | El sobre de 6 bytes, en las dos direcciones | D2 |
| **Nace** | La sesión del enlace y `HOLA` con `sesión`/`sesiones` | D5 |
| **Nace** | El registro de subida, `F_SUBIDA`, la ventana por dialecto y el byte de cola | D6 |
| **Nace** | El refresco de `BAHIA` y `SET` a 1 Hz, con su nombre | D7 |
| **Nace** | `SALUD` universal y `ESTADO_VOZ` | §3.3 |
| **Nace** | `ultimo_evento`, `Entrada::Parametro`, `Barrera::reafirmar`, la tabla de índices | D4, D7, D9 |
| **Nace** | `T_GAP` con dueño (el planificador del cerebro) | D8 |
| **Nace** | `carga_max(reloj)` | §4 |
| **Nace** | `dialecto_voz.rs` | D9 |

---

## 7. Lo que este papel NO decide, con su dueño

1. **`T_GAP`**, en microsegundos. Es la latencia del rearme del DMA del
   esclavo bajo las capturas y el DMA de audio (motor-digital §7) y se mide
   en bring-up (#250, #231). Provisional 2 µs (D8), HUECO en el guion.
2. **El mecanismo de D8** (maestro en modo 0 y esclavo en modo 1 es la
   variante compatible con este sobre, H-5; el criterio de ojo lo sella). Del
   J2 punto a punto.
3. **Las cargas de `JACKS`, `MEDIDA` y `LOG`.** R-J4 dice que las medidas son
   *«parámetros de primera clase»*; orquestación §9 punto 3 deja abierto su
   formato; el log es de otro papel (J2 §9). Este papel les da tipo y ventana.
4. **El dialecto del módulo de mandos** (#178): su ventana, su `F_SUBIDA`, su
   sondeo del panel de 32 bytes, y si el cerebro le baja algo (LEDs). Con el
   sobre de D2 ya tiene con qué escribirse.
5. **Los concentradores** (niveles 2 y 3 de `ParamId`): túnel universal o
   ruta en todo mensaje (D3). No existen; cuando existan, cambian el J2 y lo
   dicen.
6. **La cadencia de `COMPUERTA`** (R-E11: la elige el oído) y **la del
   `TONO`** (latencia_mano, 8 kHz hoy).
7. **La autopista diferencial** (D9 del J2): el sobre no depende del medio;
   si pide tramas más largas que 255 de carga, `largo` pasa a dos bytes en un
   dialecto nuevo (R-C6).
8. **Qué hace el cerebro con los contadores de `SALUD` y con `sesiones`**:
   umbrales, alarma, si cambia la cadencia de refresco. De la salud del
   instrumento (orquestación §7.1) y del bring-up.
9. **La cadencia del `SET` cuando la mano mueve un mando.** No tiene tope
   propio: lo acotan R-E1 por trama, el «uno por giro» de D4 y el 50 % por
   enlace. El plan del panel (`2026-08-23-panel-frontal-gramatica.md:187-188`)
   ya avisó que *«la entrega J2 de parámetros no-tono va a 100 Hz — tasa que
   el propio spec declaró "se oyen como escalones"»*; a qué tasa el cerebro
   convierte deltas del panel en `SET` es de la gramática del panel y del
   suavizado de un tick del generador (§5 de aquel papel), no del sobre.
10. **Los dialectos que vienen**: el «mago» (hub §D3', *«CSI dedicado más J2
    esclavo»*) y el MIDI reenviado por J2 del dispositivo compuesto
    (interfaz-audio :301-302, *«con su presupuesto de trama»*). El sobre les
    sirve; sus tipos son suyos.
11. **La fila del oyente del J2 en el libro del motor** (motor-digital §7:
    *«Oyente J2 amortizado ~20-50»* ciclos por muestra). La junta la recontó
    (H-3): 47 de costo fijo a 8 kHz de tramas, **82-92 con la unidad CRC**,
    101 con tabla, 262 bit a bit. Cabe por el ×3 del guion, no por la fila;
    la enmienda va en §11 y la cifra final la pone el bring-up.

---

## 8. Los tests

En `core/tests/j2.rs` (nuevo) y `core/tests/dialecto_voz.rs` (nuevo), todos
en el host, con la cita del papel en cada uno:

1. **Ida y vuelta de cada mensaje**: `codificar` seguido de `decodificar` da
   el mismo `Mensaje`, para los cinco de bajada y los cuatro registros de
   subida con carga, con valores de borde (todo cero, todo `0xFF`, máscaras
   con un bit, `SET` de 1 y de 16, `HOLA` con `sesión` 0 y 1).
2. **El sobre, byte a byte**: un `EVENTO` conocido produce exactamente los 13
   bytes de §3.2, en ese orden, LE, con el CRC que da `crc16` de
   `descubrimiento.rs` sobre los primeros 11.
3. **Mutación byte a byte**: para cada trama de (1), voltear un bit de cada
   byte de cabecera y carga hace que `decodificar` devuelva `ErrorTrama::Crc`
   y nunca un mensaje. Voltear un bit del CRC, ídem. Es R-C2 con dientes.
4. **Trama corta y cola**: quitar el último byte de una trama válida da
   `ErrorTrama::Corta`; añadir relleno de 0x00, de 1 a 32 bytes, y el byte de
   cola, sigue decodificando el mismo mensaje (R-C1).
5. **Forma mala**: `SET` de 7 bytes de carga, de 0 tuplas, de 17 tuplas, con
   índice 11, con `ataque_ms` 0 y con 10 001, con `paneo` 1 001; `EVENTO` con
   borde 3; `BAHIA` de 63; instancia 16 en `SET`; `HOLA` de 3 bytes: cada uno
   con su variante de `ErrorTrama`, y ninguno con `Crc` (el CRC es correcto:
   la forma es lo que falla). Y los once índices con su mínimo y su máximo
   **pasan**.
6. **Tipo desconocido**: `0x02`, `0x15` y `0x16` dan `ErrorTrama::Tipo`.
7. **R-E1 por reloj**: `carga_max(10 MHz) == 118` y `carga_max(34,5 MHz) ==
   255` con la aritmética en el aserto; y para cada mensaje, la trama más
   larga que su tipo admite cabe en `carga_max` al piso.
8. **La ventana de la Voz**: cada registro de §3.3 con su sobre ≤ 24
   (R-C5), y `SALUD` mide exactamente 18.
9. **`TONO` con máscara**: máscara `0b1000_0000_0000_0101` con tres tonos da
   largo 8 y los tonos en las instancias 0, 2 y 15; máscara con n bits y
   largo distinto de 2 + 2n es `ErrorTrama::Forma`; máscara `0xFFFF` con 16
   tonos es el bloque completo.
10. **`BAHIA` es `Imagen.filas`**: una `Imagen` con un cruce en (Entrada, canal
    3, línea 9) codifica con el bit 9 del `u16` número 3 alto y todo lo demás
    a cero; y `decodificar` devuelve una `Imagen` igual. Y los 64 bytes de la
    imagen de arranque de voz-total §5.4 son ceros.
11. **La traducción al generador**: `EVENTO` con instancia 5, borde 1 y
    secuencia 77 da `Entrada::Evento { canal: 5, borde: Borde::Cierra,
    secuencia: 77, .. }`; `COMPUERTA` da `Entrada::Compuerta { mascara,
    contador }`; `SET` de tres tuplas da tres `Entrada::Parametro` en orden,
    con el valor ya convertido al campo.
12. **La secuencia no rechaza**: dos tramas con secuencias 7 y 12 decodifican
    las dos, y `perdidas(esperada, llegada)` da 4 y da la vuelta bien en
    `u16` (R-C3).
13. **El contador no deriva** *(la simulación de la junta, hecha test)*: un
    `Generadores` recibe eventos con secuencias del cerebro y bloques armados
    con «último emitido»; se pierden eventos al azar (un LCG sembrado, una
    pérdida por mil sobre 60 000 eventos); se asevera que **ningún bloque
    armado antes de un evento aceptado revierte ese evento**, y que **todo
    evento perdido queda reparado por el siguiente bloque**. Con la cuenta
    local de la v1 este test falla a los 2,4 s simulados (H-1: 1802
    reversiones); con `ultimo_evento` pasa por construcción.
14. **La sesión**: sin `HOLA`, todo lo demás da `ErrorTrama::SinSesion`; tras
    `HOLA` válido el estado del dialecto arranca con `ultimo_evento = 0` y
    secuencia esperada 1; `HOLA` con versión 2 no abre sesión y el registro
    de subida sigue diciendo `sesión = 0` con `version = 1`; al abrir
    sesión, `sesiones` sube uno.
15. **El sobre está congelado** (R-C6): `SOBRE == 6`, `VERSION == 1`, los
    tipos universales y sus largos de carga son los de §3, en un test que
    haya que editar a mano para cambiarlos.
16. **`Barrera::reafirmar`**: la imagen activa no produce `Commit` ni mueve
    `desde_ms`; la pendiente tampoco; una tercera imagen distinta se
    convierte en pendiente. Y un `Forzar{1500 ms}` con reafirmación cada
    1000 ms **vence a los 1500** (con `proponer` no vencía nunca, H-10 caso 3).
17. **El dialecto legado sigue**: el test de 72 bits de `j2.rs` no se toca y
    pasa.

---

## 9. Los guiones

| Guion | Qué cambia | Estado |
|---|---|---|
| `hardware/02-midi-cv/trama_j2_budget.py` | `BITS_BLOQUE_TONO` 288 → **328** (máscara + 16 tonos + sobre + cola), fuente §4; `BITS_EVENTO` gana sobre y cola: **112**; `BITS_ESTADO_COMPUERTA` 16 → **200** (con relleno a la ventana); `BITS_CROSSPOINT` 256 → **568** (la imagen del modelo con sobre, no los bits del chip); filas nuevas: **`TONO` completo a 1 kHz** (328), **refresco `SET`** (824 × 63 Hz), **refresco `BAHIA`** (568 × 1 Hz); `SALUD`, `ESTADO_VOZ` y `JACKS` con tamaño en la subida (**200**, la ventana clocada); `Fila` gana `red: str \| None` y `evaluar` falla si una fila de bajada no lo declara ni está en `SIN_RED = ("dispara",)` (R-C4); `T_GAP = 2e-6  # HUECO` como constante citada | pendiente |
| `hardware/02-midi-cv/latencia_mano_budget.py` | Hereda `BITS_BLOQUE_TONO` del anterior; nada más | se mueve solo |
| `hardware/03-vco/ataque_budget.py` | La fila «Turno del J2 ≤ 100 µs» se parte en dos, porque la v1 fundía dos términos (S-9): **espera al mensaje en curso** (82,4 µs al piso, 23,9 a D8, más `T_GAP`) y **aire del propio `EVENTO`** (11,2 / 3,2). Suman 95,6 al piso y siguen bajo la cota | pendiente |
| `hardware/02-midi-cv/tiempo_budget.py` | Ya lee la trama más larga del enlace de la Voz (`:43-44`); con `SET` pasa de 288 a 824 bits y sus dos aserciones siguen verdes (§4) | se mueve solo |

---

## 10. Riesgos, con su criterio de cierre

1. **`T_GAP` provisional resulta corto.** *Cierre*: bring-up mide el rearme
   del DMA del esclavo bajo carga (motor-digital §7); si es mayor, sube en el
   guion y R-E2 pierde holgura: el evento espera al final del giro, 25 bytes
   al piso son 20 µs, dentro de R-E1 igual.
2. **La tasa de rechazo por CRC a 34,5 MHz hace que el refresco a 1 Hz se
   oiga.** *Cierre*: los contadores de `SALUD` en bring-up con el reloj
   sancionado (R-P4); la cadencia vive en el guion y sube si hace falta.
3. **El relleno a la ventana cuesta el 10 % del piso en silencio.** No es un
   riesgo de corrección sino de presupuesto; si el módulo de mandos pide una
   ventana de 40, su enlace paga lo suyo (R-P1). *Cierre*: `trama_j2_budget.py`
   por enlace.
4. **El módulo reinicia y el cerebro tarda en verlo.** Ya no enmudece (D5),
   pero entre el reinicio y el `HOLA` pasan por lo menos un muestreo y `T_GAP`,
   y hasta el refresco completo 7,9 ms. *Cierre*: bring-up mata el N657 a
   mitad de nota (la mutación de voz-total §9.2) y mide cuánto tarda en volver
   con sus parámetros.
5. **El receptor no cabe en la fila del libro del motor.** La junta (H-3)
   recontó el oyente: 47 ciclos por muestra de costo fijo (entrar y salir de
   la ISR, EXTI, contar, encolar, rearmar el DMA, reiniciar el TX) a 8 kHz de
   tramas, y **82-92 con la unidad CRC** —que va a HCLK, 4 ciclos de bus son
   16 del M55 por palabra—, 101 con una tabla de 256 entradas, 262 bit a bit.
   La fila dice *«~20-50»*. *Cierre*: la enmienda a motor-digital §7 (§11)
   sube la fila a ~100 con su cuenta, y sobrevive por el ×3 del guion
   `carga_motor`; el bring-up la mide. Si la unidad no reproduce
   CCITT-FALSE (reflejo, init), la salida es la tabla, no un CRC más débil:
   el test del vector canónico `"123456789" → 0x29B1` lo decide en la placa.
6. **`largo` de un byte se queda corto el día de la autopista, o el día de
   los 512 bits por chip.** *Cierre*: R-C6; es un dialecto nuevo, no una
   enmienda a este.
7. **El byte de cola sobra si D8 se resuelve de otra forma.** No estorba y
   cuesta el 0,6 %; *cierre*: el criterio de ojo de D8 en bring-up dice cuál
   variante corre, y el papel del J2 lo anota.

---

## 11. El mapa de enmiendas

| Documento | Sección | Tipo | Qué | Estado |
|---|---|---|---|---|
| evento de nota | §3 (tabla del formato) | Expand | Los cuatro campos ganan sus bytes y su orden (§3.2 de aquí); la fuerza queda en 16 (`fuerza.rs`, #230); la ruta es opaca para el módulo (D3) | pendiente |
| evento de nota | §5 (`evento_budget.py`, «no existe») | Sync | R-E1 la asevera `trama_j2_budget.py` con el sobre; `evento_budget.py` sigue sin existir y se dice | pendiente |
| evento de nota | §8 («la cabecera concreta del bloque de deltas de D3») | Sync | Decidida aquí: máscara + tonos, y el bloque completo a ≥ 1 kHz como red (D4) | pendiente |
| evento de nota | §10 («Gana los 16 bits de estado de compuerta… No es mensaje nuevo: es campo en un bloque») | Clarify | R-E11 lo sacó de la cadencia del tono, y `trama_j2_budget.py` y el generador ya lo tratan como flujo propio: aquí es **mensaje propio** (`COMPUERTA`), con su contador | pendiente |
| evento de nota | D6 enmienda del 2026-09-02, punto 2 («El módulo lleva su cuenta de eventos recibidos e ignora los bloques con contador menor») | **Rewrite** ⚠ | El contador es la `secuencia` del sobre del último `EVENTO` emitido; el módulo guarda la del último aceptado (D4, hallazgos V-1/H-1) | **aplicada** 2026-10-20 |
| generador de envolvente | §3.4 (el contador de eventos), §3.5 (`Entrada`), §13 decisión del contador, §14 fila #267 | **Rewrite** ⚠ | `ultimo_evento` en vez de `recibidos`; muere `resincronizar`; `Entrada::Evento` gana `secuencia`; nace `Entrada::Parametro`; `SoltarTodo` solo para el watchdog, y la sesión nueva como `Entrada::Sesion` (D5); H-B2 cerrado | **aplicada** en §3.4 y §3.5, 2026-10-20 |
| generador de envolvente | §7 (la tabla de parámetros) | Sync | Los once índices del dialecto v1 (D4) son los índices de esa tabla | pendiente |
| J2 punto a punto | D5 («la trama es lo que cabe entre bajada y subida de CS») | Clarify | Y lleva exactamente un mensaje con este sobre (D1 de aquí); la subida es un registro muestreado (D6) | pendiente |
| J2 punto a punto | D2 («El esclavo lo declara en su EEPROM de identidad») | Clarify | Hasta que la identidad gane versión 2, el reloj declarado y el dialecto viven en el catálogo del cerebro por tipo de placa (D5, hallazgo S-10) | pendiente |
| J2 punto a punto | D8 (el mecanismo del ciclo siguiente) | Expand | La variante compatible con el sobre: maestro modo 0, esclavo modo 1, un byte de cola por giro y el búfer de subida corrido un bit (D6.4, H-5); el ojo de bring-up lo sella | pendiente |
| motor-digital | §7, libro de la mitad heredada, fila «Oyente J2 amortizado ~20-50» | **Patch** ⚠ | ~100 ciclos por muestra con la unidad CRC (H-3); sobrevive por el ×3 de `carga_motor` | pendiente |
| motor-digital | §7, arquitectura de tiempo real («el gap mínimo entre tramas pasa a cláusula del contrato») | Sync | El gap tiene dueño: el planificador del cerebro (`T_GAP`, D8), y el esclavo rearma antes de validar | pendiente |
| voz-total | §3.3 («el formato del mensaje, su sello de tiempo y la entrega al esclavo no están diseñados… prerrequisito bloqueante») | Sync | Diseñado aquí; sin sello de tiempo (evento §3: *«Ni sello de hora»*) | pendiente |
| voz-total | §5.4 (acta del #171: «64 bytes, ~15 µs a 34,5 MHz»; :552-553 «Pendiente: la cabecera del J2») | Patch | Son 71 clocados: 16,5 µs a D8, 56,8 al piso; la cabecera es esta | pendiente |
| voz-total | §9.2 (watchdog de trama, «N del plan, ~50») | Clarify | Lo que cuenta son tramas **válidas** de este sobre, no bytes; y su disparo produce `SoltarTodo` local y sube por `ESTADO_VOZ` | pendiente |
| orquestación | cambio 1 («el códec nuevo con su test de ida y vuelta») | Sync | Es `dialecto_voz.rs` y el test 1 de §8; y el cambio 1 lo cumplen `SET` y `TONO`, no `BAHIA` ni `COMPUERTA`, que son réplicas de objeto (D4) | pendiente |
| núcleo | §3.1.1 («desde el cerebro es un módulo más — así que el contrato J2 sigue congelado») | Comentar | La premisa murió con el J2 punto a punto; el concentrador exigirá túnel o ruta en todo mensaje (D3) | pendiente |
| núcleo | §5 tabla de bloques :597 («72 bits… Congelado por el módulo 3, no se toca») y `software/nucleo/README.md:56` («j2 = la trama de 72 bits») | Rewrite | Deuda heredada del mapa del J2 punto a punto (§6 de aquel papel) y del #214; este papel la hereda, no la salda | pendiente (#214) |
| `core/src/j2.rs` | :1-3 | Rewrite | El sobre; el legado a rótulo | el PR de código |
| `core/src/envolvente.rs`, `core/src/bahia.rs` | `Entrada`, `Generadores`, `Barrera` | Expand | D9 | hechos el 2026-10-20 |
| `trama_j2_budget.py`, `ataque_budget.py` | constantes y filas | Expand | §9 | el PR de guiones |
| issue #267 | criterio de cierre | Comentar | Cabecera con evento, imagen, `SET` y compuerta; test de R-E1 al piso; la sesión y el contador que el issue no sabía que pedía | al mergear |
| issue #178 | — | Comentar | El módulo de mandos ya tiene sobre y sesión; le falta dialecto, ventana y `F_SUBIDA` | al mergear |
| issue #148 / #226 | — | Comentar | Los once índices de la Voz v1 quedan fijados por el enlace; el descriptor, cuando exista, los hereda | al mergear |

---

## 12. Registro de la junta

Tres lentes sobre la v1, el mismo día, antes de pedir la firma (memoria del
02-09: *«el orden bueno es brief → papel → junta → firma»*). Serrano (S),
clínica; Halberg (H), runtime con cuatro simulaciones en Python (en el
scratchpad de la sesión, `junta_halberg/sim1..sim4`; la tercera pasa a ser el
test 13 de §8); Voronov (V), ontológica.

| Hallazgo | Qué cazó | Resolución |
|---|---|---|
| **S-1** BLOCKER, **H-2**, **H-11** | El módulo que se reinicia en sesión enmudece; `HOLA` reinicia un lado solo; la regla propuesta de §7.9 hacía ping-pong | D5: sesión con nombre; `HOLA` de subida con `sesión` y `sesiones`; el cerebro reenvía solo al muestrear `sesión = 0`; ambos relojes arrancan de cero; refresco completo antes del primer `COMPUERTA` (H-12) |
| **S-2** HIGH, **V-1** BLOQUEANTE, **H-1** BLOCKER | El contador de `COMPUERTA` era una cuenta local que una pérdida desplazaba para siempre: 1802 reversiones en 60 s con p = 10⁻³ | D4: el contador es la `secuencia` del sobre del último `EVENTO`; el módulo guarda el máximo aceptado; muere `resincronizar`; test 13 |
| **S-3** HIGH | `TONO` con deltas perdió la red del bloque completo | D4: bloque completo a ≥ 1 kHz (R-M4 con segundo oficio) |
| **S-4** HIGH, **V-11**, **H-5** HIGH | «Clocado entera» en bytes contra el corrimiento de un bit de D8: `SALUD` se perdía en cada giro exacto | D6.4: byte de cola; `largo + 7`; la variante de D8 compatible declarada; enmienda al J2 D8 |
| **S-5** HIGH, **V-5**, **H-7** HIGH | `SET` no aterrizaba: tuplas contra un `Entrada` de bloque entero, sin índices, sin rango | D4: tabla de índices con rangos firmes; `Entrada::Parametro`; fuera de rango es forma; dos anchos declarados |
| **S-6** HIGH, **V-7**, **H-10** MEDIUM | El refresco de `BAHIA` por `proponer` reiniciaba el timeout de `Forzar` y latcheaba a 1 Hz | D7: `Barrera::reafirmar`; refresco nombrado como tal; test 16 |
| **S-7** MEDIUM | `SET` con N = 0 o N > 16 sin rechazo | D8 causa 4; test 5 |
| **S-8** MEDIUM, **H-8** HIGH, **H-13** MEDIUM | 63 `SET` seguidos llenaban la cola de 64 a D8 y apagaban el tono 5 ms | D4: un `SET` por giro del lazo; `cola_desbordada` en `ESTADO_VOZ`; jitter del tono declarado |
| **S-9** MEDIUM | §9 fundía «espera al mensaje en curso» con «aire del evento» | §9: dos filas en `ataque_budget.py` |
| **S-10** MEDIUM | El dialecto «en la EEPROM» no tiene campo y subir la versión de cabecera la rechaza | D5: catálogo por tipo de placa; dialectos `0` y `1`; enmienda al J2 D2 |
| **S-11** MEDIUM | Bordes de `HOLA`: mismo giro, registro a medias, `ventana` y `ranura` en `HOLA`, ranura ≥ 16 | D5: respuesta al giro siguiente; se abandona el registro; `ventana` y `ranura` fuera de `HOLA` |
| **S-12** MEDIUM | R-C4 sin campo en el guion; R-C3 y R-C6 sin puerta | §5, §9: `Fila.red` y `SIN_RED`; tests 12 y 15; R-C8 declarada sin puerta |
| **S-13** LOW | «0..4+largo» ambiguo entre lenguajes | D2: «los primeros 4 + largo bytes» |
| **S-14** LOW, **H-15** LOW | Contadores de `SALUD` con doble semántica; vuelta de 7 s; 512 bits por chip fuera de R-E1 al piso | §3.3: totales desde la sesión, deltas, `perdidas ≥ rechazadas`; §4: dialecto nuevo o sanción |
| **S-15** LOW, **V-12** BAJA | `SOLTAR_TODO` sin cliente | D4: se retira; `COMPUERTA(0)` es el pánico; `SoltarTodo` local |
| **V-2** ALTA, **V-10** MEDIA | La subida no es una trama por D5; «periódico» es del planificador; el relleno es un sondeo | D6: registro muestreado, `F_SUBIDA` por enlace, R-J3 nombrada |
| **V-3** MEDIA | D1 justificado por una latencia que D4 derrota | D1: una trama, un tipo, propiedad del parser; R-E1 acota |
| **V-4** ALTA | Dos modelos de dirección; la comprobación de ranura rechazaría todo evento bajo un concentrador; núcleo §3.1.1 citado como vigente | D3: el `CS` es la dirección, la ruta es opaca, la comprobación muere; núcleo §3.1.1 a enmienda |
| **V-6** ALTA | `HOLA` era un handshake con otro nombre y §7.9 un NAK con retransmisión | D5: sesión con nombre; doctrina acotada a «sin acuse por mensaje en el dialecto» |
| **V-8** MEDIA | `SALUD` «universal» con campos de la Voz; la ventana de la Voz imponía piso a todos | §3.3: `SALUD` universal de 12 y `ESTADO_VOZ` de la Voz; piso universal 18 |
| **V-9** MEDIA | Tres clases de réplica bajo una palabra; cambio 1 citado como cumplido por todos | D4: tabla de clases; cambio 1 lo cumplen `SET` y `TONO` |
| **H-3** HIGH | El receptor no cabe en «20-50 ciclos por muestra»: 82-92 con la unidad, 262 bit a bit | §7.11, §10 riesgo 5, enmienda a motor-digital §7 |
| **H-4** HIGH | El gap no lo impone el hardware del maestro; un `EVENTO` pegado a un `SET` a D8 se perdía | D8: `T_GAP` del planificador (2 µs provisional, HUECO); el esclavo rearma antes de validar |
| **H-6** HIGH | `BAHIA` a la barrera desde la ISR: dos dueños y una copia de 64 bytes rasgable | D8: todo por la cola; el tick es el dueño de la barrera |
| **H-9** MEDIUM | El evento llegaba indivisible y el módulo lo partía en dos dueños | D8: entra entero a la cola y se aplica en la misma pasada |
| **H-12** MEDIUM | Tras un reinicio, `COMPUERTA` llegaba antes que el refresco de `SET` y las notas volvían con parámetros semilla | D5 regla 2: refresco completo antes del primer `COMPUERTA` |
| **H-14** MEDIUM | Contar bytes al subir `CS` competía con el DMA por el último byte | D6.4: el byte de cola da ocho relojes de margen; bring-up lo mide |
| S: la aritmética | Recalculó §4, D6 y D7 (bytes, bits, µs, %, la suma, `carga_max`) | Cuadraba; las tablas de la v2 se recalcularon con el byte de cola |

---

## 13. Acta

- Samuel, 2026-09-02: *«Dale pues vamos con eso»* sobre el orden propuesto:
  el J2 primero, como protocolo con tests, porque destraba el firmware; el
  esquemático de la Voz total en paralelo; la Discovery cuando haya plata.
- Este papel se escribió leyendo, en este orden: el J2 punto a punto entero,
  el evento §3-§4 y §8-§9 con las enmiendas del 2026-09-02, el generador
  §3.4-§3.5 y §14, `trama_j2_budget.py`, `param.rs`, `descubrimiento.rs`,
  `protocolo.rs`, `j2.rs`, la hoja del N657 Rev 10 (§3.19 CRC, §3.46 SPI y
  su Tabla 14), y un digest de 337 citas de diecisiete documentos sacado
  aparte y verificado por muestra.
- La v1 pasó la junta **antes** de pedir la firma. Seis decisiones cambiaron
  de mecanismo (D1, D3, D4, D5, D6, D7) y llevan ⚠; el sobre de D2, los
  tipos de §3.1 y los bytes del `EVENTO` sobrevivieron intactos.
- Un hallazgo de hoja que no mueve nada pero se anota por el patrón del #206:
  el §3.46 del DS14791 Rev 10 abre diciendo *«The devices embed three serial
  peripheral interfaces (SPI)»*, y la portada dice *«6x SPI, of which four
  I2S-capable»* y la Tabla 14 lista SPI1-6. Manda la tabla; el «three» es
  texto heredado de otra hoja. El censo del hub (seis ranuras en SPI1-6)
  sigue en pie.
- Las decisiones que Samuel tiene que firmar, en cristiano, van en la
  conversación, con las marcas de lo que la junta cambió.
