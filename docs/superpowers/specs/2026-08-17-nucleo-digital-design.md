# El núcleo digital del SAM17 — modelo de parámetros y firmware de validación

**Fecha:** 2026-08-17
**Estado:** aprobado en brainstorming, pendiente de plan
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
| Módulos 5, 6 y 7 | Sus specs. Aquí solo quedan **anotadas sus restricciones** (§9) |
| Módulo 8 de efectos digitales | Proyecto aparte, mucho después |

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
| LCD 16×2, cuatro pulsadores, cabecera de 40 pines | Cabeza mínima y pantalla inalámbrica — §5 de esta spec |

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
                     │   RP2350    │   dueño del estado
                     │    Rust     │   tiempo real, nunca bloquea
                     └──────┬──────┘
        ┌──────────┬────────┼────────┬──────────┐
        │          │        │        │          │
    J2 (SPI+I²C)  cadena  4× TUNE  4× GATE   cabeza local
        │        WS2812    (PIO)
   ┌────┴───┬────────┬────────┐
 mód 3    mód 5    mód 6    mód 7
```

**El corolario que hace barato todo lo demás:** «control por MCP» deja de ser un
subsistema y pasa a ser un adaptador. El agente no necesita saber de sintes:
necesita saber leer un descriptor.

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

- **Ranura** — qué módulo. `0` está reservado para el propio cerebro
  (parámetros globales: tempo, canal MIDI, modo de voces). `1..15` son ranuras
  físicas del mazo, **de las que hoy solo existen 8**: las del mux I²C de §3.4.
  El campo se deja de 4 bits a propósito, para que ampliar el mux no obligue a
  cambiar el direccionamiento.
- **Instancia** — qué voz o qué copia dentro del módulo. El módulo 3 tiene
  cuatro; un módulo de una sola instancia usa `0`.
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
(continuo / enumerado / booleano), mínimo, máximo, valor por defecto, unidad, y
—si es enumerado— las etiquetas.

**El micro emite binario compacto; la carcasa lo expande a JSON.** El RP2350 no
serializa JSON: emite una tabla empaquetada, y el VST, la app standalone o el
puente inalámbrico —que corren en máquinas de verdad— la convierten a lo que la
UI web consume. Así el micro se queda pequeño y la UI se queda cómoda.

### 3.4 Descubrimiento: qué módulos hay conectados

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

**El mux I²C es obligatorio, y es una consecuencia, no una preferencia.** El
24AA02E48 en SOT-23-5 no tiene pines de dirección, así que **todas las EEPROM
responden en 0x50** y cinco módulos en un bus compartido chocan. Un mux de 8
canales en el cerebro (clase TCA9548A) le da a cada cable su canal y convierte
la colisión en comodidad: todos los módulos son idénticos vistos desde el bus.

Esto confirma que **el mazo es en estrella, un cable por módulo**. Tenía que
serlo igualmente: el J2 lleva un solo `CS`, así que nunca pudo ser un listón
compartido.

*(El encapsulado y la dirección fija del 24AA02E48 se verifican contra el
datasheet antes de implementar — §10.)*

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
| `CHANGED` | → cliente | un parámetro se movió (venga de donde venga) |
| `MODULES` | → cliente | apareció o desapareció un módulo |
| `TUNE_PROGRESS` | → cliente | avance y resultado por voz |
| `JACKS` | → cliente | cambió la ocupación de los jacks |
| `PENDING` | → cliente | una operación quedó **retenida** esperando confirmación física (§2.2) |
| `RESOLVED` | → cliente | la operación retenida se confirmó o expiró |

**`CHANGED` va a todos los suscriptores, sin importar quién movió el
parámetro** — una perilla física, el VST, el teléfono o el agente. Es lo que
mantiene las tres pieles en sincronía sin que ninguna sea la fuente de verdad.

**Esta tabla es la superficie completa del instrumento.** Por §2.1 no puede
haber capacidad fuera de ella: si algo no se puede hacer con estos mensajes, el
agente no lo alcanza, y entonces no está terminado. Añadir una función es
añadir aquí.

### 4.2 Los transportes

| Transporte | Quién lo usa | Notas |
|---|---|---|
| **USB** | VST, app standalone | Notas y timing por MIDI; parámetros y estado por el mismo enlace |
| **UART** | El puente inalámbrico | El puente sirve la UI web al teléfono y traduce |
| *(futuro)* | Lo que se enchufe al zócalo | El micro no cambia |

El micro solo implementa **dos**: USB y UART. El teléfono habla con el puente,
no con el micro.

### 4.3 El audio NO va por aquí, y es a propósito

El plugin transporta **datos, no audio**. El audio del SAM17 sale analógico por
sus jacks, entra a tu interfaz y llega al DAW por el dispositivo de instrumento
externo que ya traen todos (**External Instrument** en Ableton y Logic, **HW
Instrument** en Bitwig, **ReaInsert** en Reaper), que además **compensa la
latencia solo**.

Meter el audio por el plugin no aportaría calidad —para cuando el plugin
pudiera verlo, tu interfaz ya lo digitalizó— y sí añadiría una copia. El
analógico hasta tu conversor *es* el producto.

### 4.4 MIDI 2.0 — el objetivo, sujeto a verificación

MIDI 2.0 trae **Property Exchange**, que es la versión estandarizada de §3.3: el
dispositivo publica su lista de parámetros al host. Trae además resolución de 32
bits y sellos de tiempo para reducir jitter.

**Si el spike de §10 confirma que está maduro, es el transporte de §4.2 para
USB.** Si no lo está, el diseño funciona igual sobre MIDI 1.0 con los
parámetros en SysEx: se pierde resolución en el canal y se gana nada más.

El modelo de §3 **no depende de cuál gane**. Esa es la razón de definirlo
aparte del transporte.

---

## 5. Lo que el firmware maneja del hardware

| Bloque | Qué hace | Contrato |
|---|---|---|
| **J2 / SPI** | Trama de **72 bits** con `CS` abajo de punta a punta, modo 1, ≤10 MHz; orden `[U7][U6][U5]` | Congelado por el módulo 3, no se toca |
| **I²C** | Mux de 8 canales → EEPROM (0x50) y TMP1075 (0x48) por módulo | §3.4 |
| **PIO de afinado** | Conteo recíproco de las **4 voces a la vez**, por hardware | §5.1 |
| **Gates** | 4 salidas, activo alto | `architecture-poly.md` §4 |
| **Cadena WS2812** | Un pin de datos, encadena todos los paneles | §6.2 |
| **Cabeza local** | 4 dígitos + un encoder con pulsador + LEDs de estado | §5.2 |

### 5.1 El autoafinado y el número más flojo del diseño

`hardware/02-midi-cv/autotune_budget.py` cierra hoy con `JITTER = 5e-6` s, y su
propio comentario dice: *«ES EL PARAMETRO MAS FLOJO: hay que medirlo antes de
fiarse»*. Ese número es del Pi con `pigpio`, que ya no existe en este diseño.

**Medir el jitter real del PIO y actualizar `autotune_budget.py` con el número
medido es un entregable de esta spec**, no una nota al pie. Es lo único que
convierte el autoafinado de promesa en presupuesto.

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

---

## 6. Presets: el patch es un dato de primera clase

### 6.1 Qué guarda un preset

| Campo | Por qué |
|---|---|
| Nombre, autor, etiquetas | Librería |
| Valores de parámetros | Lo obvio |
| **Módulos requeridos** (tipo y revisión) | Para **fallar en voz alta**: si falta un módulo lo dice, en vez de sonar raro |
| **Topología del patch**: pares (jack origen → jack destino) | §6.2 |

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
que exista un módulo con jacks de CV sensados (§9), pero el mensaje y el formato
se congelan aquí.

**Nada de esto toca el J2 ni el módulo 3.** La cadena de LED es su propio mazo
de tres hilos (+5 V, dato, `GNDD`), ya planeada. Las lecturas vuelven por el
`MISO` que el J2 ya lleva. El contrato congelado aguanta todo esto sin cambiar
un pin — que era exactamente para lo que se diseñó.

---

## 7. Alcance del firmware de validación

Corre sobre **placa de desarrollo RP2350**, no sobre PCB propia.

**Dentro:**

- Descubrimiento por I²C a través del mux: EEPROM, identidad, calibración
- Trama SPI del J2 contra la cadena de DAC del módulo 3
- Captura de periodo con PIO, cuatro canales, **y la medida del jitter real**
- Modelo de parámetros y descriptor (§3)
- Protocolo sobre USB (§4), la tabla de mensajes completa
- Cadena WS2812 sobre una tira de desarrollo: valida `POINT` y el pintado del
  patcheo guiado sin esperar a que existan paneles
- Reparto de voces con robo de la más vieja
- Guardar y recuperar presets en flash
- **Retención de operaciones marcadas y confirmación física** (§2.2) — la regla
  la impone el micro, así que nace aquí, no en la app

**Fuera, y va en specs posteriores:** secuenciador, arpegiador, LFOs, memoria de
acordes; la UI web, el agente y el MCP; el puente inalámbrico; la PCB; y la
implementación —que no la definición— de `PATCH_SCAN`.

---

## 8. Cómo se verifica

Siguiendo la costumbre del repo —guiones ejecutables con aserciones, no prosa:

| Qué | Cómo |
|---|---|
| Códec del protocolo | Tests en host, Rust puro. Ida y vuelta de cada mensaje |
| Modelo y descriptor | Tests en host: un descriptor generado se parsea a lo mismo |
| Trama del J2 | Captura con analizador lógico: 72 bits, `CS` abajo entero, orden `[U7][U6][U5]` |
| Descubrimiento I²C | Con una EEPROM real en protoboard antes de que exista módulo 3 |
| **Jitter del PIO** | **Medido, y el número entra en `autotune_budget.py`** |
| Reparto de voces | Tests en host con secuencias de notas conocidas |
| Presupuestos existentes | Los cuatro siguen en verde: `ground_budget.py`, `tuning_budget.py`, `autotune_budget.py`, `dac_local_budget.py` |

---

## 9. Restricciones globales que esto impone a otros módulos

Se anotan **ahora** porque tocan módulos que aún no se dibujan, y lo que no
queda escrito se pierde.

**Módulos 5, 6 y 7:**

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

**El cerebro (spec siguiente):**

- Mux I²C de 8 canales
- Líneas de `CS` con holgura: módulos 3, 5, 6, 7 **y el 8 de efectos**, más
  repuesto
- Un pin para la cadena WS2812
- Zócalo para el puente inalámbrico — **módulo pre-certificado, no chip de RF
  soldado**: no se diseña antena, el núcleo de tiempo real nunca ve una pila
  TCP, es reemplazable, y se puede omitir para una versión más barata

**Queda aplazado a propósito**, con el mismo criterio que funcionó en el issue
#34: si los módulos 5/6/7 llevan **micro propio** o se resuelven con registro de
desplazamiento y ADC en la cadena SPI. Se cierra al dibujar el módulo 5. **Se
puede aplazar sin riesgo porque las dos opciones caben en el J2 ya congelado**,
así que el cerebro no cambia según cuál gane.

---

## 10. Riesgos y lo que NO está confirmado

Nada de esta sección está medido por nosotros. Son datasheets, documentación
ajena y arquitectura.

1. **MIDI 2.0 no está verificado.** Ni su soporte real en los DAW de hoy, ni que
   exista una pila USB MIDI 2.0 usable para RP2350 en Rust. **Spike bloqueante
   antes de comprometer el transporte.** El plan B (SysEx sobre MIDI 1.0) está
   descrito y no cambia el modelo.
2. **`embassy-rp` sobre RP2350** no se ha probado en este proyecto.
3. **El encapsulado y la dirección fija del 24AA02E48** se infirieron de que
   SOT-23-5 no tiene pines para direccionar. Hay que confirmarlo contra el
   datasheet: si resultara direccionable, el mux I²C dejaría de ser obligatorio.
4. **El jitter del PIO está sin medir** — es precisamente el entregable de §5.1,
   y hasta que exista, el presupuesto del autoafinado sigue apoyado en un número
   ajeno que ya no aplica.
5. **El barrido por inyección no se ha probado nunca**, y no existe hardware
   donde probarlo hasta que haya un módulo con jacks de CV sensados. Se congela
   el mensaje y el formato; la implementación puede descubrir que hace falta más
   hardware del previsto.
6. **El mux I²C concreto no está elegido** ni verificado contra stock.
7. **El webview dentro de un plugin** —que la spec de la app heredará de esta
   decisión— tiene fama de pesado y de dar guerra entre plataformas. Hay que
   medirlo antes de comprometer las tres carcasas a una sola UI web.
8. **El invariante de §2.1 es una disciplina, y las disciplinas se rompen bajo
   presión.** El riesgo real no es que sea imposible: es que aparezca un camino
   rápido —una perilla que escribe directo al DAC «porque es más simple»— y con
   él un rincón del instrumento que el agente no alcanza. La defensa es que la
   tabla de mensajes de §4.1 sea revisable de un vistazo, y que toda función
   nueva se juzgue contra ella.

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
  precedente de congelar contratos al construir), **#41** (plugin compañero)
