# El núcleo digital del SAM17 — modelo de parámetros y firmware de validación

**Fecha:** 2026-08-17
**Estado:** en ejecución — el contrato en `software/nucleo/` (verde), el bring-up sobre placa en su plan
**Sustituye a:** el módulo 2 tal como está construido (Raspberry Pi 3B+ con DAC
a bordo, LCD 16×2 y cuatro pulsadores). Esa placa quedó obsoleta por tres
decisiones posteriores; ver §1.

---

## 0. Qué es esto, y sobre todo qué no es

Esta spec cubre **dos cosas y solo dos**:

1. **El modelo de parámetros y su protocolo** — el contrato público del
   instrumento, del que cuelgan la app, el agente, el MCP y la pantalla.
2. **El firmware mínimo que lo implementa y lo valida**, corriendo sobre una
   **placa de desarrollo RP2350**, no sobre una PCB propia.

Lo que **no** cubre, y tiene spec propia después:

| Fuera de alcance | Dónde va |
|---|---|
| La placa del cerebro (módulo 2 v2) | Spec siguiente, ya con el firmware sabiendo qué pide |
| La app: UI web, tres carcasas, agente, servidor MCP | Spec propia, consume ésta |
| Secuenciador, arpegiador, LFOs, memoria de acordes | Después del firmware de validación |
| Módulos 4, 5, 6 y 7 | Sus specs. Aquí solo quedan **anotadas sus restricciones** (§10) |
| Módulo 8 (efectos digitales) y módulo 9 (sampler) | Proyectos aparte, mucho después. §10 dice por qué **no** van en el cerebro |

**Por qué el firmware va antes que la placa.** Se puede empezar hoy sin esperar
hierro; es el precedente del propio repo (el issue #34 congeló el J2 *«al
dibujar el módulo 3»* — el contrato lo cierra su primer implementador); y
equivocarse en firmware cuesta un commit, mientras que equivocarse en cobre
cuesta semanas y dólares.

---

## 1. El problema

`hardware/02-midi-cv/` está construido contra supuestos que tres decisiones
posteriores invalidaron:

| Lo que esa placa asume | Lo que se decidió después |
|---|---|
| Raspberry Pi 3B+ dentro del instrumento | La computadora se queda **fuera** — `architecture-compute.md` §1 |
| AD5686R en el cerebro, un cable por CV | Los DAC **viven en cada módulo**; del cerebro sale un enlace serie — `architecture-poly.md` §8 |
| LCD 16×2, cuatro pulsadores, cabecera de 40 pines | Cabeza mínima y pantalla inalámbrica — §5.2 |

Su PCB además nunca llegó a ser fabricable: quedan **17 redes sin rutear** y
`build_pcb.py` sale con error a propósito (issue #22). La congestión la causaban
justo las seis líneas del LCD, los cuatro botones y la cabecera del Pi — o sea,
**el respin en RP2350 disuelve el issue #22 en vez de resolverlo**.

Lo que de esa placa **sí sobrevive** y no se re-deriva: el presupuesto de
afinación (`tuning_budget.py`), la lección de las masas partidas, y el gate de
dos MOSFET para que el reposo al arrancar sea bajo.

---

## 2. La decisión de fondo: un modelo, N pieles

El instrumento tiene que atender a una pantalla inalámbrica, un plugin VST, una
app standalone, un cliente MCP y un agente de IA. Construir un subsistema por
cada uno es el error caro y evitable.

**Los cinco piden lo mismo: ver y cambiar el estado del instrumento.**

Así que el instrumento expone **una sola cosa** — un espacio de parámetros
direccionable y auto-descriptivo — y todos los demás son clientes de él.
Ninguno privilegiado, ninguno especial.

```
                        UNA UI WEB
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   VST / standalone      teléfono          cliente MCP
   (USB, en tu DAW)      (WiFi)            (Claude, lo que sea)
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                 EL MODELO DE PARÁMETROS
              auto-descriptivo · una sola verdad
                            │
                     ┌──────┴──────┐
                     │  RP2350B    │   dueño del estado
                     │    Rust     │   núcleo 0: tiempo real
                     │             │   núcleo 1: atribución (§7)
                     └──────┬──────┘
   ┌────────┬────────┬──────┴──┬────────┬────────┬────────┐
   │        │        │         │        │        │        │
  J2      cadena  4× TUNE   4× GATE   DIN in  clock/    pedal
(SPI+I²C) WS2812   (PIO)              /out    reset
   │
   ├── mód 3 (VCO) ── mód 5 (VCF) ── mód 6 (ADSR) ── mód 7 (VCA)
   │
   └── mód 4 (mixer) ── OYE por él: códec 24 bits + FFT, y manda
                        números por el mismo J2 (§7.4)
```

*(Puertos completos y el porqué de cada uno: §5. El audio **no** entra al
cerebro — §5.0.)*

**El corolario que hace barato todo lo demás:** «control por MCP» deja de ser un
subsistema y pasa a ser un adaptador (§4.5). El agente no necesita saber de
sintes: necesita saber leer un descriptor.

**El RP2350 es el dueño del estado, no el periférico de nadie.** Los clientes
proponen; el micro decide y ejecuta. Si desenchufas todo, el instrumento sigue
tocando con lo que tiene cargado.

### 2.1 El invariante: si no está en el modelo, no existe

El agente es una de las pieles, y **la más exigente**: no ve el panel, no gira
una perilla, no lee la pantalla. Todo lo que puede hacer lo hace a través del
modelo.

Eso deja de ser una preferencia de arquitectura y pasa a ser una regla que
obliga:

> **Ninguna capacidad del instrumento puede existir fuera del modelo de
> parámetros y su protocolo.**

Con consecuencias que muerden:

- **La cabeza local no tiene menú privado.** Su encoder hace `SET` igual que
  cualquier otro cliente. No hay «esto solo desde el panel» ni «esto solo desde
  el VST».
- **Toda función nueva nace con su parámetro o su mensaje.** Si no se puede
  expresar en el modelo, no está diseñada todavía — está a medias.

Y dos corolarios que valen la pena por sí solos:

**El descriptor es la documentación del agente.** Los nombres y las unidades
dejan de ser cosmética: son lo que un LLM lee para deducir qué hace un
parámetro. Se escriben para alguien que **nunca ha visto el instrumento**.

**El agente puede señalar.** Como la cadena WS2812 es direccionable y se alcanza
por el modelo, *«¿dónde está el cutoff?»* enciende el LED de esa perilla.
Señalar y el patcheo guiado son el mismo mecanismo — el segundo sale gratis del
primero.

### 2.2 Alcance total exige contención real, y la impone el instrumento

Un agente que alcanza todo puede romper todo, y en escena. La capa de autoridad
de `projects/aurelius` —mandatos con TTL, denylist de irreversibles— es
portable, pero **su confirmación era hablada y aquí tiene que ser física**: un
botón o un pedal.

Lo que no puede quedar en la app:

> **Qué operaciones exigen confirmación física lo declara el instrumento, no el
> cliente.**

Si lo decidiera el cliente, bastaría con un cliente que no pregunte. Así que el
micro **retiene** la operación hasta que llegue la confirmación física, y
publica en el descriptor qué está marcado como tal. La app implementa la
experiencia; el instrumento impone la regla.

---

## 3. El modelo de parámetros

### 3.1 Direccionamiento

Un parámetro se identifica con **16 bits**:

```
  15        12 11         8 7                    0
 ┌────────────┬────────────┬──────────────────────┐
 │   ranura   │  instancia │        índice        │
 │   4 bits   │   4 bits   │        8 bits        │
 └────────────┴────────────┴──────────────────────┘
```

- **Ranura** — qué módulo. `0` está reservado para el propio cerebro.
  `1..15` son ranuras físicas del mazo, **de las que hoy solo existen 8**: las
  del mux I²C de §3.5. El campo se deja de 4 bits a propósito, para que ampliar
  el mux no obligue a cambiar el direccionamiento.
- **Instancia** — qué voz o qué copia dentro del módulo. El módulo 3 tiene
  cuatro; un módulo de una sola instancia usa `0`. **En la ranura 0 significa
  otra cosa: el número de parte** (§3.6).
- **Índice** — qué parámetro dentro de esa instancia.

16 bits caben en tres septetos de SysEx y en un campo de MIDI 2.0 sin pelear.

### 3.2 Valores

**Entero con signo de 32 bits**, siempre. La escala, las unidades y el rango
viven en el descriptor, no en el valor.

Esto no es capricho: con DAC de 16 bits y `tuning.json` de por medio, mandar
parámetros en los 7 bits del CC clásico tiraría a la basura la resolución que
costó dinero conseguir. MIDI 2.0 usa 32 bits por la misma razón.

### 3.3 El descriptor

Por cada parámetro el instrumento publica: identificador, nombre corto, tipo
(continuo / enumerado / booleano), mínimo, máximo, valor por defecto, unidad,
**el ámbito** (`por-voz` o `compartido`, §3.6), las marcas de §3.4 y §2.2, y
—si es enumerado— las etiquetas.

**El micro emite binario compacto; la carcasa lo expande a JSON.** El RP2350 no
serializa JSON: emite una tabla empaquetada, y el VST, la app standalone o el
puente inalámbrico —que corren en máquinas de verdad— la convierten a lo que la
UI web consume. Así el micro se queda pequeño y la UI se queda cómoda.

### 3.4 Los parámetros de medida son ciudadanos de primera

El descriptor lleva una marca de **solo lectura** y una categoría de **medida**.
Un parámetro de medida no se escribe: lo publica el instrumento a partir de lo
que mide (§7).

**Esto es barato ahora y carísimo después.** Si el modelo nace suponiendo que
todo parámetro se escribe, meter medidas más tarde obliga a tocar el descriptor,
las tres carcasas y el servidor MCP a la vez.

Y es lo que hace que el agente pueda **cerrar el lazo**: lee `brillo` con el
mismo `GET` con que lee `cutoff`, sin protocolo nuevo y sin excepción al
invariante de §2.1.

### 3.5 Descubrimiento: qué módulos hay conectados

Cada módulo lleva una **EEPROM 24AA02E48 en I²C con ID único de fábrica**, que
guarda tipo de placa, revisión, serial y el blob de calibración. Eso ya está
especificado en el módulo 3 y declarado allí como *«patrón para los módulos 5,
6 y 7»* (`docs/modules/03-vco.md`).

Es la cantidad justa de inteligencia: **treinta centavos, sin procesador**.
Nada que actualizar, nada que se cuelgue.

El arranque del cerebro:

1. Barre las ranuras del mux I²C.
2. En cada una lee la EEPROM y saca tipo, revisión, serial y calibración.
3. Monta el mapa de parámetros buscando el **tipo de placa** en una tabla que
   vive **en el firmware del cerebro**.
4. Publica el descriptor resultante a quien pregunte.

> **Lo que esto sí compra y lo que no.** La UI no cambia nunca: renderiza lo
> que le llegue, así que un módulo nuevo aparece solo. Pero el descriptor de un
> tipo de placa nuevo vive en el firmware del cerebro, así que **estrenar un
> tipo de módulo sí pide actualizar el firmware**. La EEPROM del 24AA02 son 256
> bytes: alcanzan para identidad y calibración, no para un descriptor completo.

**El mux I²C es obligatorio, y es una consecuencia, no una preferencia.**
Verificado contra el datasheet: el 24AA02E48 en SOT-23-5 usa pin 1 `SCL`, pin 2
`Vcc`, pin 3 `SDA`, pin 4 sin conexión y pin 5 `Vss`, y **sus entradas de
dirección A0/A1/A2 no están conectadas** — dirección fija. Cinco módulos en un
bus compartido chocan. Un mux de 8 canales en el cerebro (clase TCA9548A) le da
a cada cable su canal y convierte la colisión en comodidad: todos los módulos
son idénticos vistos desde el bus.

*(De paso, la misma verificación confirma el módulo 3: su `check_netlist.py`
exige `U14-1` en `I2C_SCL` y `U14-3` en `I2C_SDA`, que coincide con el datasheet
pin por pin.)*

Esto confirma que **el mazo es en estrella, un cable por módulo**. Tenía que
serlo igualmente: el J2 lleva un solo `CS`, así que nunca pudo ser un listón
compartido.

### 3.6 Partes: dejar preparada la polifonía que el mercado ya conoce

Hoy son cuatro voces en un solo timbre. El instrumento tiene que poder crecer a
los modos que cualquier sinte poli del mercado ofrece **sin reestructurar el
modelo**, porque eso último se paga una sola vez y se paga caro.

**Lo que NO necesita nada del modelo.** Son estrategias de reparto de voces, o
sea firmware puro, y se escriben el día que se quieran sin tocar una línea de
esta spec:

> mono con prioridad de nota (última / grave / aguda) · legato y glide ·
> unísono 2/4/8 con desafinado y apertura · poly con estrategia de robo
> (más vieja, más suave, grave, aguda, round-robin) · parafónico —que aquí es un
> **modo**, no un accidente, porque el mixer va al final— · memoria de acordes ·
> ciclado de voces para promediar las diferencias entre voces analógicas

**Lo que SÍ hay que poner ahora, porque después es reescritura**, son tres
cosas.

#### La parte

Una **parte** es lo que habilita **multitímbrico, split de teclado y capas**:
un canal MIDI, un rango de teclas, una reserva de voces y un preset propio.

Encaja sin tocar el direccionamiento de §3.1: **en la ranura `0`, el campo
*instancia* es el número de parte.** Dieciséis partes, y los parámetros
globales de siempre —tempo, modo de voces, las medidas de §7— viven en la
parte `0`.

| Parámetro de parte | Para qué |
|---|---|
| Canal MIDI | Multitímbrico |
| Nota más grave / más aguda | Split de teclado |
| Voces asignadas y desde cuál empieza | Reparto, capas, y **poly-chain** entre dos instrumentos |
| Preset | Que cada parte suene distinto |
| Modo de voces y estrategia de robo | Los de la lista de arriba, por parte |

Con un solo parámetro extra —**desde qué voz empieza esta parte**— queda
resuelto también el *poly-chaining*: dos instrumentos encadenados, cada uno
atendiendo su tramo del mismo pool.

#### Por voz contra compartido, declarado

El descriptor gana una marca de **ámbito**: `por-voz` o `compartido`. Hoy eso es
implícito y ambiguo —el módulo 3 tiene el tono por voz pero el PWM compartido—
y sin la marca ni la UI sabe dibujarlo, ni el agente sabe qué puede mover **por
nota**, ni un preset sabe qué guardar una vez y qué guardar cuatro.

#### El conteo de voces sale del descubrimiento, jamás de una constante

**Ningún `4` escrito en el firmware.** El número de voces sale de los
descriptores, con una regla explícita:

> **Las voces del instrumento son el mínimo de la cadena.** Con 8 VCO y 4 VCF
> tienes 4 voces, y el instrumento lo **dice** en vez de sonar raro.

Es el mismo principio de §6.1 —fallar en voz alta— aplicado al conteo.

#### MPE, y la restricción que impone aguas abajo

**MPE** (*MIDI Polyphonic Expression*) pide tres dimensiones **por nota**: bend,
timbre y presión. Es el estándar moderno de expresión y encaja entero en este
modelo — son escrituras a parámetros marcados `por-voz` de la voz que toca esa
nota.

El bend ya funciona: el tono es por voz. Pero el timbre choca con un plan
existente, y conviene decirlo antes de que se dibuje:

> `architecture-poly.md` §3 describe el módulo 5 como *«VCF ×4, corte y
> resonancia **comunes a las 4**»*.

**Con el corte compartido, el timbre por nota es imposible**: hay cuatro filtros
y un solo control. Así que los módulos 5, 6 y 7 —**ninguno dibujado**— necesitan
**al menos un destino de timbre `por-voz`**: corte con CV propio por voz, aunque
las perillas del panel sigan siendo comunes. Gratis hoy, respin mañana (§10).

**El enlace aguanta:** 16 voces × 3 dimensiones × 100 Hz sobre tramas de 72 bits
a 10 MHz salen a ~3.5 % de ocupación del SPI. El cuello de botella no está aquí.

---

## 4. El protocolo

### 4.1 Independiente del transporte

El mismo juego de mensajes viaja por USB, por el UART del puente inalámbrico, o
por lo que venga después. El micro no sabe quién está del otro lado — igual que
el módulo 3 no sabe qué hay del otro lado del J2.

| Mensaje | Dirección | Para qué |
|---|---|---|
| `HELLO` | cliente → | identificarse y negociar versión |
| `DESCRIBE` | cliente → | pedir el descriptor completo |
| `GET` / `SET` | cliente → | leer o escribir un parámetro |
| `SUBSCRIBE` | cliente → | pedir notificación de cambios |
| `PRESET_LIST` / `LOAD` / `SAVE` | cliente → | la librería |
| `TUNE_START` | cliente → | disparar el autoafinado |
| `PATCH_SCAN` | cliente → | pedir el barrido de topología (§6.2) |
| `TELEMETRY` | cliente → | temperatura, correcciones por pasada, salud por voz |
| `POINT` | cliente → | encender el LED de un parámetro o un jack (§2.1) |
| `MEMO` | cliente → | grabar unos segundos de audio para el agente (§7.5) |
| `CHANGED` | → cliente | un parámetro se movió (venga de donde venga) |
| `MODULES` | → cliente | apareció o desapareció un módulo |
| `TUNE_PROGRESS` | → cliente | avance y resultado por voz |
| `JACKS` | → cliente | cambió la ocupación de los jacks |
| `PENDING` | → cliente | una operación quedó **retenida** esperando confirmación física (§2.2) |
| `RESOLVED` | → cliente | la operación retenida se confirmó o expiró |
| `HOLA` | → cliente | la versión que el instrumento acepta hablar |
| `ERROR` | → cliente | qué etiqueta falló y por qué |

> **`HOLA` y `ERROR` se añadieron el 2026-08-17, al escribir el servidor.** La
> tabla original dejaba al cliente **en silencio** en tres casos: `HELLO` —que
> la propia tabla describe como *«negociar versión»*— no tenía respuesta;
> `DESCRIBE` no tenía forma de contestar; y **todo `SET` rechazado** —solo
> lectura, fuera de rango, no existe— se quedaba dentro del micro. El tercero
> es el peor modo de fallo del diseño entero: el agente escribe, no pasa nada,
> y no sabe por qué. §2.1 dice que eso se arregla creciendo la tabla, no
> inventando una convención por fuera, y esto es hacerle caso.
>
> El volcado del descriptor **no** es un mensaje: es de largo variable y
> grande, y meterlo en la enumeración obligaría a darle vida (`Mensaje<'a>`) y
> a que eso rippleara por todo el códec. El servidor lo pide como respuesta
> aparte y la capa de transporte lo sirve en su propio sobre.

**`CHANGED` va a todos los suscriptores, sin importar quién movió el
parámetro** — una perilla física, el VST, el teléfono o el agente. Es lo que
mantiene las tres pieles en sincronía sin que ninguna sea la fuente de verdad.

**Esta tabla es la superficie completa del instrumento.** Por §2.1 no puede
haber capacidad fuera de ella: si algo no se puede hacer con estos mensajes, el
agente no lo alcanza, y entonces no está terminado. Añadir una función es
añadir aquí.

*(Las medidas de §7 no necesitan mensaje propio: son parámetros de solo lectura,
y se leen con `GET` y se siguen con `SUBSCRIBE` como cualquier otro.)*

### 4.2 Los transportes

| Transporte | Quién lo usa | Notas |
|---|---|---|
| **USB** | VST, app standalone | Notas y timing por MIDI; parámetros y estado por el mismo enlace |
| **UART** | El puente inalámbrico | El puente sirve la UI web al teléfono y traduce |
| *(futuro)* | Lo que se enchufe al zócalo | El micro no cambia |

El micro solo implementa **dos**: USB y UART. El teléfono habla con el puente,
no con el micro.

### 4.3 El audio NO va por el enlace de control, y es a propósito

El plugin transporta **datos, no audio**. El audio del SAM17 sale analógico por
sus jacks, entra a tu interfaz y llega al DAW por el dispositivo de instrumento
externo que ya traen todos (**External Instrument** en Ableton y Logic, **HW
Instrument** en Bitwig, **ReaInsert** en Reaper), que además **compensa la
latencia solo**.

Meter el audio por el plugin no aportaría calidad —para cuando el plugin
pudiera verlo, tu interfaz ya lo digitalizó— y sí añadiría una copia. El
analógico hasta tu conversor *es* el producto.

> **Ojo con la lectura equivocada:** esto dice que el *camino de control* no
> carga audio. **No** dice que el agente sea sordo. El instrumento se escucha a
> sí mismo por otra vía (§7), y el plugin puede analizar la pista que le
> enrutes. Lo que nunca viaja por el enlace de control es la forma de onda.

### 4.4 MIDI 2.0 — resuelto: es una escalera, no una bifurcación

**En el host: maduro.** [NAMM 2026 fue el punto de
inflexión](https://blog.imseankim.com/midi-2-0-daw-hardware-support-2026-update/):
Microsoft envió **Windows MIDI Services** (KB5074105), que reemplaza la pila
MIDI vieja entera e instala driver de clase USB MIDI 2.0 con UMP nativo a nivel
de sistema operativo. Todos los DAW grandes tienen implementación en producción
o beta.

Y **Property Exchange regala una función que este proyecto quería**: Logic 10.6+
muestra automáticamente los controles específicos del instrumento y **guarda su
configuración en el fichero de proyecto**. Eso es el «recall total con el
proyecto» que motivaba el VST compañero — gratis, del estándar.

**En el micro había una fricción aparente: la pila UMP existe pero es C.** Hay
[`tusb_ump` de AmeNote](https://github.com/midi2-dev/tusb_ump) (driver de clase
UMP para TinyUSB) y un ejemplo de RP2350 en
[midi2cpp](https://github.com/sauloverissimo/midi2cpp), probados los dos, pero
en C/C++ y sin equivalente en Rust. Eso parecía chocar con el «Rust bare-metal»
de `architecture-compute.md`.

**Dos hechos verificados la disuelven.**

**Primero: Property Exchange no necesita UMP.** *«Property Exchange usa SysEx
estilo MIDI 1.0, **por MIDI 1.0 o por MIDI 2.0**»*, y los mensajes MIDI-CI
*«son retrocompatibles con MIDI v1; técnicamente son solo mensajes System
Exclusive»*. Fue diseñado así a propósito, para que los aparatos MIDI 1.0
existentes pudieran negociar.

O sea: **el descriptor, el auto-descubrimiento y el puente MCP de §4.5 funcionan
enteros sobre MIDI 1.0.** UMP no compra nada de eso. Compra otra cosa —
resolución de 32 bits en datos de *interpretación* y sellos de reducción de
jitter— que es valiosa, pero no está en el camino crítico de nada.

**Segundo: el propio estándar USB define la escalera.** Un dispositivo USB MIDI
2.0 declara **dos alternate settings** en la misma interfaz: el `0` con
`bcdMSC = 0x0100` (MIDI 1.0) y el `1` con `0x0200` (MIDI 2.0). Los hosts que no
soportan 2.0 usan el `0`; los que sí, buscan el `1`.

**Añadir el alternate setting 1 más tarde no es reescribir: es lo que la
especificación espera que hagas.**

Y una vez visto así, el trabajo en Rust se reduce a lo que de verdad es. «La
pila UMP» son dos cosas muy distintas: los **descriptores de clase USB** —la
parte tediosa, y para la que existe
[`usbMIDI2DescriptorBuilder`](https://github.com/midi2-dev/usbMIDI2DescriptorBuilder)—
y la **codificación de paquetes de 32 bits**, que es manipulación de bits y en
Rust es trivial. No hay pila de red aquí.

**Decisión:**

| Etapa | Qué | Cuándo |
|---|---|---|
| **1** | USB MIDI 1.0 (alt setting 0) sobre `embassy-usb` + MIDI-CI/Property Exchange en SysEx. Descriptor, descubrimiento y puente MCP completos | El firmware de validación |
| **2** | Añadir alt setting 1 con UMP | Cuando compre algo medible |

**El criterio para subir el escalón, escrito ahora para no discutirlo después:**
que los 7 bits del canal MIDI 1.0 se demuestren insuficientes en una medida
real, o que el jitter de notas por USB se mida y moleste. Antes de eso, subir es
gasto sin retorno.

Los proyectos en C quedan como **referencia e implementación de contraste**, no
como dependencia. Si la etapa 2 llega y escribir los descriptores en Rust
resulta más caro de lo previsto, el FFI a `tusb_ump` sigue disponible — pero
como plan B de una etapa opcional, no como fricción en el camino crítico.

**El modelo de §3 no depende de ninguna de las dos etapas.** Esa es la razón de
haberlo definido aparte del transporte, y aquí es donde se cobra.

### 4.5 El puente MCP ↔ Property Exchange

MCP y MIDI-CI Property Exchange **resuelven el mismo problema en dos mundos**, y
la correspondencia es casi literal:

| MCP | MIDI-CI Property Exchange |
|---|---|
| `tools/list` | **`ResourceList`** — la meta-propiedad que se consulta primero |
| `tools/call` | `Get` / `Set Property Data` |
| JSON por herramienta | JSON por Resource |
| *resources* | *Resources* |

Property Exchange es un método bidireccional para que dispositivo y host se
pregunten capacidades e intercambien configuración **en JSON estructurado**. Es
la definición de MCP con otro nombre.

**El hueco encontrado:** los servidores MCP para MIDI que existen hoy son de dos
tipos, y ninguno cierra esto. Los **genéricos** —como
[MCP MIDI Control](https://lobehub.com/mcp/theandrewstaker-mcp-midi-control),
con trece primitivas MIDI contra cualquier dispositivo USB— funcionan con todo
pero el LLM no sabe qué *significa* un CC en tu sinte. Los **específicos** —como
[MIDICtrl](https://github.com/nanassound/midi_ctrl) para el Arturia
MicroFreak— traen el mapa de parámetros escrito a mano, dispositivo por
dispositivo.

**No se encontró evidencia de que nadie haya puenteado `ResourceList` →
`tools/list`.** Ausencia de resultados no es prueba de ausencia, pero se buscó
por cuatro ángulos distintos.

La consecuencia de diseño, que es lo que importa aquí: **un instrumento que
hable Property Exchange se gana un servidor MCP genérico**, sin mapa escrito a
mano, y funcionando también con módulos que no existían cuando se escribió el
agente. Por eso §2.1 insiste en que nombres y unidades son documentación, no
cosmética: son literalmente lo que el LLM va a leer.

*(La implementación del puente vive en la spec de la app. Aquí solo se fija que
el descriptor tiene que ser suficiente para generarlo.)*

---

## 5. Lo que el firmware maneja del hardware

| Bloque | Qué hace | Contrato |
|---|---|---|
| **J2 / SPI** | Trama de **72 bits** con `CS` abajo de punta a punta, modo 1, ≤10 MHz; orden `[U7][U6][U5]` | Congelado por el módulo 3, no se toca |
| **I²C** | Mux de 8 canales → EEPROM (0x50) y TMP1075 (0x48) por módulo | §3.5 |
| **PIO de afinado** | Conteo recíproco de las **4 voces a la vez**, por hardware | §5.1 |
| **Gates** | 4 salidas, activo alto | `architecture-poly.md` §4 |
| **Cadena WS2812** | Un pin de datos, encadena todos los paneles | §6.2 |
| **Cabeza local** | 4 dígitos + un encoder con pulsador + LEDs de estado | §5.2 |
| **USB device** | Puerto nativo: hacia tu computadora | §4.2 |
| **USB host** | PIO-USB: tu controlador enchufado al instrumento | §5.3 |
| **MIDI DIN in/out** | UART + optoacoplador | §5.3 |
| **Clock / reset** | Sync analógico, entrada y salida | §5.3 |
| **Pedal** | Confirmación física y expresión | §5.3 |
| **UART** | Zócalo del puente inalámbrico | §4.2 |

### 5.0 Qué NO entra por aquí: el audio

**El cerebro no tiene entrada de audio.** No es una carencia: es la regla que el
resto del instrumento cumple —*«por el cableado viajan números, no
voltajes»*— aplicada también aquí. La medida del sonido la hace el módulo 4,
donde el audio ya está, y llega al cerebro convertida en números por el J2.

El porqué completo, y la corrección de una versión anterior de esta spec que
sí metía una línea analógica hasta el cerebro, están en §7.4.

### 5.1 El autoafinado: el número más flojo del diseño, resuelto

`autotune_budget.py` colgaba de `JITTER = 5e-6` s, con un comentario que decía
*«ES EL PARAMETRO MAS FLOJO: hay que medirlo antes de fiarse»*. Lo era: venía
del Pi con `pigpio`, un aparato que este diseño ya no usa, y **todo el
presupuesto era proporcional a él**.

**No se sustituyó por otra estimación. Se derivó, y el resto se despejó.**

**El sellado de tiempos ya no se estima.** El PIO muestrea el pin de forma
síncrona con el reloj de sistema, así que un flanco queda resuelto dentro de un
ciclo; en conteo recíproco se sellan dos flancos y se restan, luego el error de
la diferencia está acotado por **un tick**. A 150 MHz eso son **6.67 ns**, y no
sale de un manual ajeno: sale del reloj.

**El término que quedaba no se supuso: se invirtió en requisito.** El que de
verdad manda ahora es el disparador Schmitt (74HC14), cuyo cruce de umbral
tiembla con el ruido de la onda del VCO, y que sigue sin medir. En vez de
inventarle un valor, el guion **despeja cuánto puede temblar como máximo** sin
romper el objetivo, evaluado en la ventana más corta del barrido —la nota más
aguda, que es la que menos perdona.

Lo que sale, con las dos fuentes sumadas linealmente (pesimista a propósito:
son independientes y sumarían en cuadratura):

| | Antes (Pi + pigpio) | Ahora (PIO derivado) |
|---|---|---|
| Sellado de tiempos | 5 µs, de manual | **6.67 ns, derivado** — 750× mejor |
| Peor precisión de las 84 notas | 0.5 cents (justo en el objetivo) | **0.024 cents** — 20× por debajo |
| Barrido completo | 3.5 s | **2.7 s** |
| Suelo de afinación con autoafinado | 1.68 cents | **1.23 cents** |
| Carga de CPU por flanco | Real; hacía falta un 74HC4040 dividiendo por 16 | **Ninguna** — el PIO cronometra por hardware. El divisor sobra |
| El 74HC14 | Sin acotar | **Puede temblar hasta 131 ns** y aún se cumple |

**Ese último número es el resultado que importa.** «Medir el jitter del
comparador» deja de ser una incógnita abierta y pasa a ser **un aprobado o
suspenso contra 131 ns**. Y el sellado del PIO se lleva solo el **5 %** del
error permitido, con lo que el micro deja de ser un término del presupuesto y
pasa a ser ruido de redondeo.

El guion lo **asevera**, no lo narra: falla si el sellado dejara de ser
despreciable (por encima del 10 % de lo permitido), porque eso significaría que
el cuello de botella volvió a ser el micro y habría que subir `F_PIO` o alargar
la ventana.

> **Lo que sigue sin confirmar, y ahora es concreto:** el jitter real del 74HC14
> en placa. Y que `F_PIO` sean de verdad 150 MHz sin dividir para el PIO — si el
> firmware lo divide, el sellado sube en la misma proporción y hay que
> recalcular. El guion lo dice en su salida.

### 5.2 La cabeza local: qué muestra y por qué tan poca

Cuatro dígitos, un encoder con pulsador, y LEDs de estado. Cubre lo único que no
puede esperar a que aparezca un teléfono: **número de preset, canal MIDI, y si
el autoafinado está corriendo o si una voz se salió de rango.**

No lleva menús. Escribir nombres de preset con un encoder es tortura, y el
teléfono lo hace mejor. La cabeza local hace lo que el teléfono hace **peor**:
estar siempre ahí, encendida, sin batería ni red.

**Y no es especial: es un cliente más.** Su encoder emite `SET` como el VST o el
agente (§2.1), y sus dígitos muestran lo que el modelo publica. Ningún camino
privado.

**Su pulsador es el botón de confirmación física de §2.2.** La contención del
agente no cuesta hardware extra: ya estaba ahí.

**Y el panel entero es la pantalla de verdad**: la cadena de LED direccionables
—que ya estaba planeada para el soft-takeover de las perillas
(`architecture-poly.md` §7)— dice más de un vistazo que cualquier OLED.

### 5.3 Las conexiones al mundo, y por qué cada una

#### USB de doble rol: es lo que hace verdad el «toca sin nada más»

`architecture-compute.md` §1 promete un instrumento completo sin computadora.
Con solo USB *device*, esa promesa es falsa en 2026: las notas solo entrarían
por DIN o desde una máquina, y **casi todo controlador moderno es USB-only**.

Verificado que se puede tener las dos cosas: [Pico-PIO-USB](https://github.com/sekigon-gonnoc/Pico-PIO-USB)
implementa host sobre PIO en RP2350 **funcionando a la vez que el USB nativo
hace de device** — confirmado con TinyUSB en enero de 2026.

```
  controlador USB ──► [PIO-USB host]  RP2350  [USB nativo] ──► tu DAW
                                         │
                                  su propio secuenciador
```

Y sale gratis un tercer papel: **el instrumento es un hub MIDI.** Tu teclado
entra, se mezcla con lo que el secuenciador esté generando, y sale hacia la
computadora.

*(Riesgo: Pico-PIO-USB es C, misma escalera que §4.4, y hay reportes de que
costó estabilizarlo en alguna placa. El instrumento funciona sin host; es
degradación, no fallo.)*

#### MIDI DIN: el que está aislado

`architecture-compute.md` §7 ya lo pedía y una versión anterior de esta spec lo
perdió. No es nostalgia: el DIN exige **optoacoplador desde 1983**, y es la
razón por la que el propio documento concluye *«USB para comodidad, DIN para
grabar en serio»*. Sin él vuelve entero el lazo de tierra del USB, que ese
mismo documento marca como trampa conocida.

#### Clock y reset: sin esto el secuenciador no toca con nadie

Un secuenciador que solo sincroniza por MIDI no puede tocar con un rack modular
ni con la mayoría del hardware. El estándar es viejo y estable: **TTL, 0 V /
~+5 V, 24 PPQN** típico; entradas con Schmitt de umbral bajo ~0.1 V y alto
1-2 V, y las fuentes dan pulsos de 10 V de ~1 ms.

Y hay un detalle que **no** está estandarizado, y por eso importa:

> **No existe comportamiento unificado de reset en Eurorack.** Unos módulos
> miran el estado actual del reloj al recibirlo; otros esperan el siguiente
> flanco de subida.

Por eso **el comportamiento de reset va como parámetro, no como decisión
cableada**. Y al ser parámetro, por §2.1 lo alcanza el agente: *«mi secuenciador
externo entra corrido un paso, arréglalo»* pasa a ser algo que el instrumento
puede resolver hablando. Una incompatibilidad clásica del formato, tratada como
lo que es — una preferencia, no una verdad.

#### El pedal: la spec lo pedía y no lo tenía

§2.2 dice que la confirmación del agente es física, *«un botón o un pedal»*, y
ninguna versión anterior definió el jack. Es la función de seguridad más crítica
del diseño y colgaba de hardware inexistente.

El pulsador del encoder sirve de respaldo, pero **en escena tienes las manos
ocupadas**. Y si la entrada es analógica, el mismo jack da **expresión**, que
por el mapeo universal se enruta a cualquier parámetro.

#### La consecuencia de sumar pines: va el RP2350**B**

Contando todo lo anterior —SPI, `CS` con holgura, I²C, 4× TUNE, 4× GATE, DIN
in/out, UART del puente, WS2812, cabeza local, clock/reset in/out, pedal y los
dos pines del PIO-USB— salen **~37 GPIO**.

| | GPIO | Entradas analógicas | Encapsulado |
|---|---|---|---|
| RP2350**A** | 30 | 4 | QFN-60, 7×7 mm |
| **RP2350B** | **48** | **8** | QFN-80, 10×10 mm |

**No cabe en el A.** El B además da 8 entradas analógicas en vez de 4, que hacen
falta para el pedal de expresión y dejan margen.

Y el argumento de `architecture-compute.md` §7 sigue en pie: un QFN-80 de
10×10 mm sigue siendo minúsculo al lado de la cabecera de 40 pines del Pi, así
que el atasco de ruteo del issue #22 se disuelve igual.

*(La elección final del encapsulado es de la spec de la placa. Aquí queda el
conteo que la obliga.)*

#### Y una función que no cuesta hardware: mapeo universal

Cualquier CC de MIDI entrante, el pedal, o cualquier entrada de CV de cualquier
módulo → **cualquier parámetro**. Es firmware sobre el modelo de §3, no un
puerto más. Con el agente encima, *«mapea mi pedal de expresión al cutoff»*
funciona sin que nadie programe nada.

Actualización de firmware: **UF2 por USB**, arrastrar y soltar. Sale gratis del
RP2350 y no hay que diseñar nada.

#### Dónde está el techo de voces, y por dónde se sale

El modelo escala a 16 voces por módulo y 16 ranuras (§3.1), el descubrimiento
se adapta solo, y el autoafinado **no tarda más** porque mide en paralelo. El
techo real está en un solo sitio, y son **ocho cables dedicados**:

```
  4× GATE      del cerebro al ADSR
  4× TUNE_OUT  del VCO al cerebro, por los pines 9-12 del J2
```

Y la trampa que hay que ver: **ponerle más pines no escala**. Serían cuatro
líneas de afinado **por cada ranura capaz de llevar un VCO** — con 8 ranuras,
32 pines solo para eso.

**La salida es el movimiento que este diseño ya hizo dos veces:** que el módulo
mida sus propios osciladores y **mande los números**, igual que el mux de
perillas, el sensado de jacks y las medidas del módulo 4. Vuelven por el `MISO`
que el J2 ya lleva, y el coste en pines del cerebro es **cero**.

**El contrato del J2 no cambia ni un pin.** El README del módulo 3 ya lo
permite: *«cada uno usa las señales que le tocan»* — un módulo de más voces
simplemente no usaría los pines 9-12 y reportaría por `MISO`.

Lo mismo con los gates: mandarlos **dentro de la trama SPI**, junto al tono, no
solo escala — **sincroniza mejor**, porque tono y gate salen en el mismo
instante en vez de por dos caminos distintos.

> **Qué se hace hoy:** nada de hardware. El módulo 3 sale como está, con sus
> cuatro líneas por J2. Lo que se hace es **no escribir el 4 en ninguna parte**
> (§3.6) y dejar el camino escrito, para que quien diseñe ese módulo lo tome en
> vez de inventar otro.

---

## 6. Presets: el patch es un dato de primera clase

### 6.1 Qué guarda un preset

| Campo | Por qué |
|---|---|
| Nombre, autor, etiquetas | Librería |
| Valores de parámetros | Lo obvio |
| **Módulos requeridos** (tipo y revisión) | Para **fallar en voz alta**: si falta un módulo lo dice, en vez de sonar raro |
| **Topología del patch**: pares (jack origen → jack destino) | §6.2 |

**Un preset es de una parte** (§3.6). Y lo que en otros sintes se llama
*performance* o *combi* —qué preset carga cada parte, con sus canales y sus
rangos de teclas— **no necesita concepto nuevo**: son los parámetros de la
ranura `0`, guardados como cualquier otro preset. Sale del modelo sin añadirle
nada.

### 6.2 El patcheo guiado, que es la razón de que los presets existan de verdad

**Un modular no tiene presets porque el patch es físico.** «Recall total» es
mentira en cualquier modular del mundo. Esto lo resuelve.

Al cargar un preset, la cadena WS2812 enciende **cada pareja de jacks en un
color**, para que pongas el cable que toca — varios a la vez, en colores
distintos, y el color puede escogerse contra los cables que realmente tienes.

Y hay dos niveles, con costes muy distintos:

**Ocupación (sensado simple).** Un registro de desplazamiento por módulo lee qué
jacks tienen cable. Da **verificación**: el LED se pone verde cuando enchufas
donde toca. Da también un guardado mucho más rápido: en vez de buscar ocho jacks
en la app, te muestra los ocho ocupados y confirmas cuatro parejas.

**Topología (barrido por inyección).** La ocupación *no* dice qué jack está
unido a cuál — con cuatro cables sabes que hay ocho jacks ocupados y cero
parejas. Para la captura automática de verdad hace falta que el cerebro mueva
una fuente a un valor único y vea **qué entrada se movió**. Eso exige que cada
entrada de CV patcheable sea **legible por ADC**, lo que a su vez fija que el
mux de perillas viva **en el módulo** y devuelva por el `MISO` del J2.

**Decisión: la topología por inyección es requisito, no aspiración** — y por eso
`PATCH_SCAN` existe en el protocolo desde el día uno. Su implementación espera a
que exista un módulo con jacks de CV sensados (§10), pero el mensaje y el
formato se congelan aquí.

**Cómo se hace sin que sea frágil: §7.6.** Mover una fuente y buscar un salto se
rompe con atenuadores, se ahoga en ruido y obliga a barrer de una en una. La
versión que va en la spec es **códigos ortogonales y correlación**: todas las
fuentes a la vez, inmune al ruido por ganancia de correlación, y **midiendo la
atenuación además de la conexión** — así el preset guarda «VCO1 → CV del VCF1,
atenuado al 40 %», que es más de lo que se pedía.

Y cuando la correlación no es concluyente **no adivina**: cae a la ocupación,
que es un hecho binario y fiable, y la app te pide confirmar la pareja.

**Se descartó el cable con canal de sensado.** Un tercer conductor que una
origen y destino daría la topología directa, sin ADC ni barrido, y es mucho más
simple. Pero obliga a jacks TRS y **cables especiales**: un modularista tiene
gavetas de cables normales que dejarían de servir. Un estándar que exige cables
propietarios es un peor estándar, y la meta declarada de este diseño es que se
adopte. Queda anotado como camino de escape si la inyección resulta frágil.

**Nada de esto toca el J2 ni el módulo 3.** La cadena de LED es su propio mazo
de tres hilos (+5 V, dato, `GNDD`), ya planeada. Las lecturas vuelven por el
`MISO` que el J2 ya lleva. El contrato congelado aguanta todo esto sin cambiar
un pin — que era exactamente para lo que se diseñó.

### 6.3 Existe arte previo, y está patentado

**US 10418013 y 10770052** — *«Analog recall synthesizer having patch and knob
recall»*, inventor Steven G. Shaw, asignadas a **Lafayette College**. Cubren
sensado de conexiones en los jacks, LEDs que indican tanto el estado actual como
el deseado de cada conexión, color e intensidad para posición actual contra
deseada de perillas, y todos los módulos en un bus digital común para el recall.

Se anota aquí para que la decisión sea consciente y no un descubrimiento tardío:

- **Valida la idea** — alguien la consideró lo bastante buena como para
  patentarla.
- El titular es una **universidad**, no una empresa defendiendo producto.
- Para uso personal el riesgo práctico es bajo; **para comercializar, importa**.
- El repositorio está **privado** a fecha de esta spec, así que no hay
  divulgación pública y las opciones siguen abiertas. En EE.UU. hay un año de
  gracia tras divulgar; en casi todo el resto del mundo la divulgación pública
  destruye la novedad de inmediato. **El día que este repo se haga público es el
  día que esa puerta se cierra fuera de EE.UU.**

> **Esto no es asesoría legal y quien lo escribe no es abogado.** Si el proyecto
> va a comercializarse, esta sección es el recordatorio de consultar a alguien
> que sí lo sea, no un sustituto de hacerlo.

Nota aparte: el puente de §4.5 es una invención **distinta** y esas patentes no
lo tocan.

---

## 7. El motor de análisis: el instrumento se escucha a sí mismo

El objetivo, en palabras del brief: que el agente pueda saber que **está
saliendo demasiado grave**, o que **hay una frecuencia que sobresale de las
demás**, y actuar en consecuencia.

**Medir y atribuir son dos trabajos distintos, y cada uno quiere vivir en un
sitio distinto.** Esa es la decisión que ordena toda esta sección:

```
  MÓDULO 4 (mixer)                          CEREBRO (RP2350B)
  ┌────────────────────────┐                ┌──────────────────────┐
  │ suma las 4 voces       │                │ sabe qué nota toca   │
  │ códec de audio 24 bits │   J2: números  │ cada voz y dónde     │
  │ FFT, bandas, picos     │ ─────────────► │ está cada filtro     │
  │                        │                │          ↓           │
  │        MIDE            │                │      ATRIBUYE        │
  └────────────────────────┘                └──────────────────────┘
```

**El módulo 4 tiene el audio. El cerebro tiene el estado.** Ninguno puede hacer
el trabajo del otro, y juntarlos obligaría a mover audio analógico a un sitio
donde no tiene por qué estar.

En el cerebro, el reparto entre núcleos sigue en pie:

- **Núcleo 0** — tiempo real duro: notas, gates, tramas SPI, PIO.
- **Núcleo 1** — atribución (§7.2) y el motor de perturbación (§7.6).

Nada de eso le roba un ciclo a una nota, y ninguna de las dos cosas es pesada:
lo caro —la FFT— ya vino resuelto y convertido en números.

### 7.1 Tres lazos a tres velocidades

| Lazo | Velocidad | Quién | Qué hace |
|---|---|---|---|
| **Análisis** | milisegundos | Núcleo 1, siempre | Mide y publica. **Nunca decide** |
| **Automático** | ms – s | Firmware, reglas fijas | *«si esta banda pasa de X, haz Y»*. Determinista, sin IA |
| **Agente** | segundos | El LLM | Razona, atribuye, diseña sonido |

> **El agente jamás está en el camino de audio.** Si algo necesita responder en
> milisegundos, eso es un compresor, no un LLM. Confundir esas dos capas es el
> error clásico, y aquí queda cerrado por diseño.

### 7.2 Atribución: lo que ninguna herramienta de masterización puede hacer

Un analizador en un sinte no es nuevo. Esto sí.

Un plugin de masterización ve una mezcla terminada. Detecta una resonancia y
**solo puede adivinar** de dónde viene, así que lo único que sabe hacer es
atenuar esa frecuencia para todo por igual.

**El SAM17 sabe.** Conoce sus cuatro voces, qué nota toca cada una en este
instante, dónde está el cutoff y la resonancia de cada filtro, y cómo está la
mezcla de formas de onda. Así que cuando el núcleo 1 reporta un pico por encima
de la envolvente, el cerebro puede cruzarlo con su propio estado y atribuirlo a
**una voz y un parámetro concretos**.

Y entonces el arreglo no es un notch en la salida: es la perilla de resonancia
de esa voz. **Se corrige la causa, no el síntoma.**

Ninguna herramienta de masterización puede hacerlo porque ninguna tiene la
fuente. Ningún sinte lo hace porque ninguno se escucha y razona sobre lo que
oye. **Esta es la función que justifica el motor entero.**

#### El algoritmo, porque «cruzarlo» a mano ondeada no es un diseño

Con cuatro voces sonando, un pico a una frecuencia dada puede ser el fundamental
de una voz, un armónico de cualquiera, la resonancia de cualquier filtro, un
producto de intermodulación, o dos voces coincidiendo. **La ambigüedad es real y
hay que tratarla, no ignorarla.** Va en dos niveles:

**Nivel 1 — inferencia. Gratis, continua, sin cambiar nada de lo que suena.**
El cerebro conoce el tono exacto de cada voz —lo mandó él, y el autoafinado lo
midió— así que calcula la serie armónica esperada de cada una y la frecuencia
resonante de cada filtro, y puntúa contra el pico observado. Sale una
**hipótesis ordenada con su confianza**.

**Nivel 2 — sonda causal. Solo cuando el nivel 1 queda ambiguo, y solo si se
permite.** Se perturba mínimamente el parámetro sospechoso y se correlaciona el
movimiento del pico. Si al mover la resonancia de la voz 2 el pico se mueve, es
de la voz 2. **Eso es causalidad, no correlación de estado** — y es exactamente
el motor de §7.6, la misma pieza que resuelve la topología del patch.

**«Ambiguo» tiene definición, no criterio de barra:** si la primera hipótesis no
se separa de la segunda por un margen dado, es ambigua. Punto.

Y lo que se le entrega al agente es **la hipótesis con su confianza**, nunca una
certeza fabricada. Un agente que recibe «probablemente la voz 2, 0.7» puede
pedir la sonda, preguntarte, o abstenerse. Uno que recibe «la voz 2» a secas
tarde o temprano te arregla el sonido equivocado con total aplomo.

### 7.3 Qué se mide de verdad — y por qué una FFT cruda no basta

**Una FFT cruda no puede contestar «hay muchos graves».** En cualquier espectro
crudo la energía de graves es siempre mayor; así es la música. La pregunta es
perceptual, no espectral.

| El objetivo | Lo que lo contesta |
|---|---|
| «demasiado grave» | **Bandas ponderadas perceptualmente** (Bark/Mel) con sonoridad estilo ITU-R BS.1770 — el estándar de broadcast para «cuánto se siente» |
| «una frecuencia por encima de las demás» | **Detección de resonancia contra la envolvente espectral suavizada** — lo mismo que hacen los supresores dinámicos de resonancia |

Todas las salidas del motor son **parámetros de medida** en el sentido de §3.4:
solo lectura, con unidad y rango, leídos con `GET` y seguidos con `SUBSCRIBE`.
El agente no necesita saber que existe un motor de análisis; solo lee
parámetros.

### 7.4 Dónde vive la medida — y la corrección de una versión anterior

**Una versión anterior de esta spec mandaba una línea analógica diferencial
desde el mixer hasta un ADC en el cerebro. Estaba mal, y merece decirse por qué.**

Rompía la regla que el resto del instrumento cumple sin excepción —*«por el
cableado viajan números, no voltajes»* (`architecture-poly.md` §8)— y era el
único sitio de todo el diseño donde eso pasaba. La defensa que traía —«es una
toma de medida, no un camino de audio»— es **cierta pero es una
racionalización, no un argumento**: explicaba por qué el daño sería pequeño, no
por qué había que hacerlo.

**La versión correcta: la medida vive donde vive el audio.**

El módulo 4 lleva un **submódulo de DSP de clase Daisy** —
[Daisy Patch Submodule](https://electro-smith.com/products/patch-submodule),
STM32H750 Cortex-M7 a 480 MHz, códec AKM de **24 bits hasta 192 kHz**, 64 MB de
SDRAM, con acondicionamiento de señal Eurorack ya incorporado, ~£35 — que hace
la FFT, las bandas perceptuales y la detección de resonancia **sobre la mezcla
que ya tiene delante**, y publica **números** por el J2.

No es una plataforma exótica: mueve el Qubit Surface y **toda la serie Versio de
Noise Engineering**. Es hardware probado en módulos comerciales.

**Lo que se gana, y no lo compraba un cerebro más rápido:**

| | ADC en el cerebro (lo anterior) | Códec en el módulo 4 |
|---|---|---|
| Resolución | **12 bits** (~72 dB) | **24 bits** (~144 dB) |
| Líneas analógicas cruzando a lo digital | una | **ninguna** |
| Frontera `GNDA`/`GNDD` | hay que defenderla | no se toca |
| Margen de cómputo | a tasa de análisis, justo | 480 MHz con SDRAM |

**Oídos de 24 bits en vez de 12 no se consiguen con un micro más rápido: se
consiguen poniendo el conversor donde está el sonido.** Ese es el punto entero.

**Consecuencia de segundo orden, anotada para el módulo 4:** el mismo submódulo
que analiza puede **procesar**. Es decir, el módulo 4 (mixer) y el módulo 8
(efectos digitales) podrían acabar siendo la misma placa. No se decide aquí —
es de su spec— pero conviene que quien la escriba lo sepa antes de empezar.

**Lo que sigue igual:** «tiempo real» significa **tasa de análisis** (decenas de
Hz), no tasa de muestreo. «Hay demasiado grave» no cambia 48 000 veces por
segundo, y el lazo del agente sigue midiéndose en segundos (§7.1).

**Y el momento es gratis:** el módulo 4 **no está dibujado** — kicad,
esquemático y PCB pendientes. Decidirlo hoy no cuesta nada; decidirlo después es
un respin.

### 7.5 El memo del agente

Con el códec y la SDRAM ya en el módulo 4 (§7.4), grabar unos segundos para que
el agente los analice **no cuesta hardware nuevo**: *«¿en qué tonalidad está
esto que toqué?»*, *«imita este timbre»*. El mensaje `MEMO` de §4.1 lo pide, el
cerebro lo enruta y el módulo 4 lo graba.

**Y sigue sin ser un sampler**, aunque ahora la memoria dé para mucho más que
unos segundos. La diferencia no es la duración, es el trabajo:

| | Memo | Sampler (módulo 9) |
|---|---|---|
| Para qué | Que el agente **analice** una frase | **Tocar** notas |
| Necesita | Grabar y medir | Afinado por nota, polifonía, bucles, envolventes |
| A dónde sale | A números, para el modelo | Al patch bay, y de ahí al VCF y al VCA analógicos |

Grabar no es samplear. §10 explica por qué el sampler tampoco vive en el
cerebro.

### 7.6 El motor de perturbación: una sola pieza para dos problemas

Los dos puntos más frágiles de esta spec —el barrido de topología de §6.2 y la
atribución de §7.2— parecían problemas distintos. **No lo son.** Los dos
preguntan lo mismo:

> Observo un efecto. ¿Cuál de las N causas que controlo lo produjo?

Y los dos se responden igual: **perturbar una magnitud controlada y correlacionar
el cambio observado.** Una sola pieza de firmware sirve a ambos, y eso convierte
dos funciones sin probar en **un componente con un test**.

#### Correlación, no detección de escalón

El planteamiento ingenuo —mover una fuente a un valor y buscar un salto en las
entradas— es exactamente donde estaba la fragilidad: se rompe con atenuadores en
el camino, se ahoga en el ruido, y obliga a barrer las fuentes de una en una.

La versión robusta es la que usan el GPS, CDMA y la medida de salas con
secuencias de longitud máxima: **darle a cada fuente un código distinto y
correlacionar en cada punto de observación.**

| Fragilidad del escalón | Lo que hace la correlación |
|---|---|
| Un atenuador deja el salto casi en cero | La ganancia de correlación lo encuentra igual — **y mide cuánto atenúa** |
| El ruido de la entrada tapa el salto | La correlación integra: el ruido no correlaciona, la señal sí |
| Un camino acoplado en AC no pasa DC | Se usa un código **sin componente de continua** |
| Hay que barrer las fuentes una por una | Códigos ortogonales → **todas a la vez** |
| Una fuente que va a dos destinos | Las dos correlaciones dan positivo; es 1-a-muchos y sale correcto |

**Y el premio que no se buscaba: se aprende la atenuación, no solo la conexión.**
El preset deja de guardar «VCO1 → CV del VCF1» y pasa a guardar «VCO1 → CV del
VCF1, atenuado al 40 %». Es más información de la que el problema original pedía.

#### Nunca adivina en silencio

Toda correlación devuelve **una hipótesis y una confianza**, nunca una certeza.
La regla de degradación, escrita para que no se improvise:

1. **Confianza alta** — se acepta y se publica.
2. **Confianza baja o dos hipótesis empatadas** — se marca como ambigua, **se
   cae a la ocupación de §6.2** (que sí es un hecho binario y fiable), y la app
   le pide al usuario que confirme la pareja.
3. **Nunca** se publica una topología o una atribución inventada.

El invariante de §2.1 obliga a lo mismo hacia el agente: **la confianza es parte
del dato**. El agente recibe «probablemente la voz 2, confianza 0.7», no una
afirmación. Con eso puede pedir una sonda, preguntarte, o abstenerse — que es lo
que un buen ingeniero haría.

#### Se prueba antes de que exista el hardware

Esto es lo que saca a las dos funciones de la lista de riesgos: **el motor es
código puro y se valida en simulación.**

Se generan señales sintéticas con topología conocida, atenuaciones conocidas y
ruido inyectado, y se exige que el motor recupere lo que se puso. Y —más
importante— se le dan casos que **debe** declarar ambiguos, y se exige que los
declare en vez de inventarse una respuesta.

Así, cuando llegue el hardware, lo que se estará probando es el acoplo eléctrico
real, no el algoritmo. **El algoritmo ya vino verde.**

---

## 8. Alcance del firmware de validación

Corre sobre **placa de desarrollo RP2350**, no sobre PCB propia.

**Dentro:**

- Descubrimiento por I²C a través del mux: EEPROM, identidad, calibración
- Trama SPI del J2 contra la cadena de DAC del módulo 3
- Captura de periodo con PIO, cuatro canales, **y la medida del jitter real**
- Modelo de parámetros y descriptor (§3), con medidas de solo lectura
- Protocolo sobre USB (§4): **USB MIDI 1.0 en alt setting 0 + MIDI-CI/Property
  Exchange en SysEx**, con la tabla de mensajes completa. UMP es la etapa 2 y
  no entra aquí (§4.4)
- **Motor de perturbación (§7.6) validado en simulación**: códigos ortogonales,
  correlación, y los casos que debe declarar ambiguos
- Cadena WS2812 sobre una tira de desarrollo: valida `POINT` y el pintado del
  patcheo guiado sin esperar a que existan paneles
- **Partes** (§3.6): la estructura entera —canal, rango de teclas, reserva de
  voces y preset por parte— aunque el firmware de validación solo estrene una.
  Ponerla ahora es barato; retrofitearla es reestructurar el modelo
- **Conteo de voces desde el descubrimiento**, con la regla del mínimo de la
  cadena. **Ningún `4` escrito en el firmware**, y un test que lo demuestre
- Reparto de voces con robo de la más vieja
- Guardar y recuperar presets en flash
- **Retención de operaciones marcadas y confirmación física** (§2.2) — la regla
  la impone el micro, así que nace aquí, no en la app
- **Atribución en el núcleo 1** (§7.2): recibir medidas por el J2 —simuladas
  mientras no exista módulo 4— publicarlas como parámetros de solo lectura, y
  cruzarlas con el estado de las voces para producir hipótesis con confianza
- **USB de doble rol** (§5.3): device y host a la vez sobre placa de
  desarrollo, con un controlador MIDI real enchufado
- **MIDI DIN, clock/reset y pedal** sobre protoboard: el DIN con su
  optoacoplador, el reset **como parámetro** con sus dos comportamientos, y el
  pedal reteniendo una operación marcada

**Fuera, y va en specs posteriores:** secuenciador, arpegiador, LFOs, memoria de
acordes; la UI web, el agente, el servidor MCP y el puente de §4.5; el puente
inalámbrico; la PCB; el alternate setting 1 con UMP (§4.4); y el **acoplo
eléctrico real** de §6.2 y §7.2 — o sea, `PATCH_SCAN` y la atribución contra
hardware que suena. Sus algoritmos sí entran, validados en simulación: cuando
llegue el hardware se estará probando la electrónica, no la matemática.

---

## 9. Cómo se verifica

Siguiendo la costumbre del repo —guiones ejecutables con aserciones, no prosa:

| Qué | Cómo |
|---|---|
| Códec del protocolo | Tests en host, Rust puro. Ida y vuelta de cada mensaje |
| Modelo y descriptor | Tests en host: un descriptor generado se parsea a lo mismo |
| Trama del J2 | Captura con analizador lógico: 72 bits, `CS` abajo entero, orden `[U7][U6][U5]` |
| Descubrimiento I²C | Con una EEPROM real en protoboard antes de que exista módulo 3 |
| **Jitter del comparador** | Medido en placa y contrastado contra los **131 ns** que `autotune_budget.py` despeja. Aprobado o suspenso, no una incógnita |
| `F_PIO` sin dividir | Comprobar que el PIO corre al reloj de sistema; si el firmware lo divide, `autotune_budget.py` hay que recalcularlo |
| Reparto de voces | Tests en host con secuencias de notas conocidas |
| **Conteo de voces** | Descriptores sintéticos de 8 VCO y 4 VCF: se exige que el instrumento reporte **4** y lo diga, no que asuma nada. Y un test que falle si aparece un `4` constante en el camino |
| **Partes** | Dos partes en canales distintos con rangos de teclas solapados: cada nota va a la parte que le toca y a su reserva de voces |
| Medidas por el J2 | Se inyectan bandas y picos sintéticos como si vinieran del módulo 4, y se exige que salgan por `GET`/`SUBSCRIBE` como parámetros de solo lectura, con unidad y rango |
| USB doble rol | Un controlador MIDI real enchufado al host **mientras** un DAW ve el instrumento como device. Notas de los dos caminos, mezcladas |
| Reset como parámetro | Los dos comportamientos —mirar el estado del reloj y esperar el flanco— producen resultados distintos y reproducibles con el mismo pulso de entrada |
| Pedal | Retiene una operación marcada y la libera. Mismo test que la confirmación física, por el otro camino |
| **Motor de perturbación** | Simulación con topología y atenuaciones conocidas más ruido: se exige que recupere lo que se puso. **Y casos deliberadamente ambiguos: se exige que los declare ambiguos en vez de inventar** |
| **Atribución** | Espectro sintético donde dos voces comparten un armónico: se exige confianza baja, no una respuesta segura y equivocada |
| Confirmación física | Test: una operación marcada llega por USB y **no** se ejecuta hasta el pulsador |
| Property Exchange sobre MIDI 1.0 | El descriptor completo viaja en SysEx y vuelve idéntico, sin UMP de por medio |
| Presupuestos existentes | Los cuatro siguen en verde: `ground_budget.py`, `tuning_budget.py`, `autotune_budget.py`, `dac_local_budget.py` |

---

## 10. Restricciones globales que esto impone a otros módulos

Se anotan **ahora** porque tocan módulos que aún no se dibujan, y lo que no
queda escrito se pierde.

**Módulo 4 (mixer) — no dibujado, gratis decidirlo:**

- **Lleva el motor de análisis entero** (§7.4): submódulo de clase Daisy
  (STM32H750, códec de 24 bits, SDRAM), FFT, bandas perceptuales y detección de
  resonancia sobre la mezcla que ya tiene delante
- **Publica números por el J2**, nunca audio. Ninguna línea analógica cruza
  hacia el cerebro
- Graba el `MEMO` de §7.5 cuando se lo piden
- EEPROM de identidad y TMP1075, como todos
- **Anotado para quien escriba su spec:** el mismo submódulo que analiza puede
  procesar, así que el módulo 4 y el módulo 8 podrían ser una sola placa.
  Decisión suya, no de aquí

**Módulos 5, 6 y 7 — no dibujados, gratis decidirlo:**

- EEPROM **24AA02E48 en 0x50** con tipo, revisión, serial y calibración — el
  patrón ya declarado por el módulo 3
- TMP1075 de telemetría, dirección por straps
- **El mux de perillas vive en el módulo**, no en el cerebro (esto cierra una
  ambigüedad de `architecture-poly.md` §7)
- **Sensado de ocupación** en los jacks
- **Toda entrada de CV patcheable tiene que ser legible por ADC** — es lo que
  hace posible el barrido por inyección
- Las lecturas vuelven por el **`MISO` del J2**, sin hilos nuevos
- Un LED de la cadena WS2812 por perilla y por jack
- **Al menos un destino de timbre `por-voz`** — corte con CV propio por voz en
  el módulo 5, aunque las perillas del panel sigan siendo comunes. Sin eso
  **MPE es imposible** (§3.6), y `architecture-poly.md` §3 hoy los describe con
  *«corte y resonancia comunes a las 4»*
- **Declarar el ámbito de cada parámetro** en su descriptor: `por-voz` o
  `compartido`. Sin la marca, ni la UI sabe dibujarlo ni el agente sabe qué
  puede mover por nota

**El cerebro (spec siguiente):**

- **RP2350B (QFN-80)**, no el A: el conteo de §5.3 da ~37 GPIO y el A solo
  tiene 30. El B da 48 y 8 entradas analógicas
- Mux I²C de 8 canales
- Líneas de `CS` con holgura: módulos 3, **4**, 5, 6, 7 **y los futuros 8 y 9**,
  más repuesto
- Un pin para la cadena WS2812
- **Sin entrada de audio.** La medida llega como números por el J2 (§5.0, §7.4)
- **USB de doble rol**: puerto nativo como device, PIO-USB como host
- **MIDI DIN in/out** con optoacoplador
- **Clock y reset**, entrada y salida, niveles TTL con Schmitt
- **Jack de pedal**, a entrada analógica para que sirva también de expresión
- Zócalo para el puente inalámbrico — **módulo pre-certificado, no chip de RF
  soldado**: no se diseña antena, el núcleo de tiempo real nunca ve una pila
  TCP, es reemplazable, y se puede omitir para una versión más barata

**Módulo 8 (efectos digitales) y módulo 9 (sampler) — por qué NO van en el
cerebro:**

Los dos son técnicamente posibles ahí: el RP2350 tiene 520 kB de SRAM y soporta
hasta 16 MB de flash/PSRAM externa por QSPI con un segundo chip-select, que da
para un sampler de verdad. Se descartan igual, por tres razones:

1. **Convertirían al cerebro en fuente de audio**, que es justo lo que todas las
   decisiones anteriores sacaron de esa caja: *«el cerebro manda números, no
   voltajes»* — la regla que §5.0 y §7.4 dejan sin excepciones.
2. **Existe una plataforma hecha para esto y les gana en todo.** La clase Daisy
   —STM32H750 a 480 MHz, códec de 24 bits hasta 192 kHz, **64 MB de SDRAM** que
   son diez minutos de audio, acondicionamiento Eurorack incluido, ~£35— no es
   un compromiso: es lo que mueve el Qubit Surface y toda la serie Versio de
   Noise Engineering. Contra eso, 16 MB de PSRAM en el cerebro es la versión
   pobre de algo que ya se puede comprar hecho.
3. **Como módulos son mejores.** Su salida cae en el patch bay, así que pasa por
   el VCF, el VCA y la envolvente **analógicos** — que es exactamente por qué se
   quiere un sampler de hardware y no un plugin. Y ese patch se guarda y se
   recupera con el resto (§6.2). Meterlos en el cerebro tiraría esa ventaja.

> **La conclusión que ordena todo esto:** «un cerebro más potente» no es lo que
> hace al instrumento más capaz, porque **el cerebro no tiene camino de audio a
> propósito**. Los MHz que valen la pena viven donde vive el sonido — en el
> módulo 4 para oír, y en el 8 y el 9 para producirlo. El cerebro se queda
> pequeño, y esa es su función.

**Lo que queda aplazado a propósito:**

Si los módulos 5/6/7 llevan **micro propio** o se resuelven con registro de
desplazamiento y ADC en la cadena SPI. Se cierra al dibujar el módulo 5, con el
mismo criterio que funcionó en el issue #34. **Se puede aplazar sin riesgo
porque las dos opciones caben en el J2 ya congelado**, así que el cerebro no
cambia según cuál gane.

---

## 11. Estado de verificación

Los ocho puntos abiertos de la revisión inicial, verificados el **2026-08-17**.

### Resueltos a favor

| | Hallazgo |
|---|---|
| **MIDI 2.0 en el host** | Maduro. Windows MIDI Services enviado (KB5074105) con driver de clase USB MIDI 2.0 y UMP nativo; todos los DAW grandes con implementación en producción o beta; **Logic 10.6+ ya renderiza controles desde Property Exchange y guarda la configuración en el proyecto** |
| **`embassy-rp` sobre RP2350** | Maduro. Feature `rp235xa`, paridad completa desde principios de 2025; el RP2350 tuvo soporte Rust de fábrica desde el lanzamiento |
| **Webview en plugin** | Resuelto, y en Rust. [WRAC](https://www.kvraudio.com/forum/viewtopic.php?p=9248726) (NovoNotes, mayo 2026): WebView + Rust Audio + CLAP, **15 000+ usuarios en producción**, VST3/AU/Standalone vía `clap-wrapper`, crate `wxp` sobre `wry` con IPC bidireccional. CLAP tiene además extensión webview en borrador |
| **24AA02E48** | Confirmado contra datasheet: SOT-23-5, A0/A1/A2 no conectadas → **dirección fija**, el mux I²C es obligatorio. Y el `check_netlist.py` del módulo 3 coincide con el pinout, pin por pin |
| **RP2350 para DSP** | Confirmado: dual Cortex-M33 a 150 MHz con **FPU por hardware e instrucciones DSP**, CMSIS-DSP con FFT y RMS, 2-4× el RP2040 |
| **USB de doble rol** | Confirmado: [Pico-PIO-USB](https://github.com/sekigon-gonnoc/Pico-PIO-USB) hace host sobre PIO en RP2350 **a la vez** que el USB nativo hace de device; funcionando con TinyUSB en enero de 2026 |
| **Clock/reset Eurorack** | Confirmado: TTL 0 V / ~+5 V, 24 PPQN típico, Schmitt con umbrales ~0.1 V y 1-2 V. **Y que NO hay estándar de reset** — de ahí que vaya como parámetro (§5.3) |
| **RP2350A contra B** | Confirmado: A = 30 GPIO / 4 analógicas / QFN-60; **B = 48 GPIO / 8 analógicas / QFN-80**. El conteo obliga al B |
| **Plataforma para oír y para el audio digital** | Confirmada la clase Daisy: STM32H750 a 480 MHz, códec 24 bits/192 kHz, 64 MB SDRAM, acondicionamiento Eurorack, ~£35, probada en el Qubit Surface y la serie Versio de Noise Engineering |

### Las cuatro fricciones, resueltas en esta revisión

| Fricción | Cómo se resolvió |
|---|---|
| **Pila UMP en C, no en Rust** (§4.4) | Se disolvió con dos hechos: **Property Exchange corre sobre SysEx de MIDI 1.0** —así que el descriptor y el puente MCP no necesitan UMP— y el estándar USB define **alternate settings** para subir a MIDI 2.0 después. No es bifurcación: es escalera, con criterio escrito para cuándo subir |
| **Jitter del PIO** (§5.1) | Se **derivó** en vez de estimarse: un tick a 150 MHz = **6.67 ns**, 750× mejor que el número prestado del Pi. Y el término que quedaba —el 74HC14— se **invirtió en requisito**: puede temblar hasta **131 ns**. `autotune_budget.py` lo asevera |
| **Fragilidad del barrido por inyección** (§6.2) | **Códigos ortogonales y correlación** en vez de detección de escalón: inmune al ruido, atraviesa atenuadores —y **mide** la atenuación—, todas las fuentes a la vez. Con degradación explícita: si no es concluyente, cae a ocupación y pregunta |
| **Ambigüedad de la atribución** (§7.2) | Algoritmo en **dos niveles**: inferencia contra la serie armónica conocida, y **sonda causal** cuando queda ambiguo. Se entrega hipótesis **con confianza**, nunca certeza fabricada |

Y las dos últimas resultaron ser **la misma pieza**: el motor de perturbación de
§7.6. Dos funciones sin probar se volvieron **un componente con un test**, y ese
test corre en simulación, sin hardware.

### Abiertos

1. **El acoplo eléctrico real del barrido de §6.2.** El algoritmo se valida en
   simulación, así que lo que queda por probar es la electrónica: si la señal
   inyectada sobrevive el camino analógico real con margen suficiente. No hay
   dónde medirlo hasta que exista un módulo con jacks de CV sensados.
2. **La atribución (§7.2) contra un instrumento sonando.** Ahora depende de dos
   piezas en dos placas —el módulo 4 midiendo y el cerebro cruzando— así que
   hasta que exista el módulo 4 solo se puede probar con medidas simuladas.
3. **Pico-PIO-USB en Rust.** Está verificado que funciona, pero en C con
   TinyUSB. Aplica la misma escalera de §4.4: se resuelve en el plan, y el
   instrumento funciona sin host — es degradación, no fallo.
2. **El jitter real del 74HC14 en placa.** Ya no es una incógnita abierta —hay
   131 ns contra los que contrastarlo— pero sigue sin medirse.
3. **`F_PIO` = 150 MHz supone el reloj de sistema sin dividir para el PIO.** Si
   el firmware lo divide, el sellado sube en la misma proporción y
   `autotune_budget.py` hay que recalcularlo.
4. **El mux I²C concreto no está elegido** ni verificado contra stock de LCSC.
5. **El invariante de §2.1 es una disciplina, y las disciplinas se rompen bajo
   presión.** El riesgo no es que sea imposible: es que aparezca un camino
   rápido —una perilla que escribe directo al DAC «porque es más simple»— y con
   él un rincón que el agente no alcanza. La defensa es que la tabla de mensajes
   de §4.1 sea revisable de un vistazo, y que toda función nueva se juzgue
   contra ella.

---

## Referencias

- `docs/architecture-compute.md` — el cerebro partido, la computadora fuera
- `docs/architecture-poly.md` §4, §7, §8 — convenciones eléctricas, mandos
  digitales, los DAC en los módulos
- `hardware/03-vco/README.md` — el contrato J2, congelado
- `docs/modules/03-vco.md` — telemetría de serie, patrón para 5/6/7
- `hardware/02-midi-cv/autotune_budget.py` — el presupuesto que esta spec debe
  actualizar con datos medidos
- Issues **#22** (ruteo del módulo 2, se disuelve con el respin), **#29** (epic
  del lado digital, desactualizado), **#34** (direccionamiento, cerrado — el
  precedente de congelar contratos al construir), **#41** (plugin compañero),
  **#42** (WS2812)
