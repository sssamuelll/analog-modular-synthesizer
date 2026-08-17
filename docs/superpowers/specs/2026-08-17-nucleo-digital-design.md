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
                     │   RP2350    │   dueño del estado
                     │    Rust     │   núcleo 0: tiempo real
                     │             │   núcleo 1: análisis (§7)
                     └──────┬──────┘
        ┌──────────┬────────┼────────┬──────────┐
        │          │        │        │          │
    J2 (SPI+I²C)  cadena  4× TUNE  4× GATE   cabeza local
        │        WS2812    (PIO)
   ┌────┴───┬────────┬────────┐
 mód 3    mód 5    mód 6    mód 7
```

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

- **Ranura** — qué módulo. `0` está reservado para el propio cerebro
  (parámetros globales: tempo, canal MIDI, modo de voces, y las medidas de §7).
  `1..15` son ranuras físicas del mazo, **de las que hoy solo existen 8**: las
  del mux I²C de §3.5. El campo se deja de 4 bits a propósito, para que ampliar
  el mux no obligue a cambiar el direccionamiento.
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
(continuo / enumerado / booleano), mínimo, máximo, valor por defecto, unidad,
las marcas de §3.4 y §2.2, y —si es enumerado— las etiquetas.

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

### 4.4 MIDI 2.0 — verificado, con una tensión

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

**En el micro: existe, pero es C.** Hay
[`tusb_ump` de AmeNote](https://github.com/midi2-dev/tusb_ump) (driver de clase
UMP para TinyUSB) y un ejemplo de RP2350 en
[midi2cpp](https://github.com/sauloverissimo/midi2cpp). Están probados, pero son
C/C++, y **no aparece equivalente en Rust**. Eso choca con el «Rust bare-metal»
de `architecture-compute.md`.

Tres salidas, a decidir en el plan: FFI desde Rust a `tusb_ump`; escribir UMP en
Rust; o quedarse en MIDI 1.0 con los parámetros en SysEx, perdiendo resolución
en el canal y nada más.

**El modelo de §3 no depende de cuál gane.** Esa es la razón de haberlo definido
aparte del transporte.

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
| **ADC de análisis** | Toma de medida desde el mixer | §7.4 |

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
que exista un módulo con jacks de CV sensados (§10), pero el mensaje y el
formato se congelan aquí.

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

**Cabe.** El RP2350 tiene dos Cortex-M33 a 150 MHz con **FPU por hardware e
instrucciones DSP**, y CMSIS-DSP le da FFT y RMS ya hechos. El reparto es
limpio:

- **Núcleo 0** — tiempo real duro: notas, gates, tramas SPI, PIO.
- **Núcleo 1** — no hace otra cosa que escuchar.

El análisis nunca le roba un ciclo a una nota.

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

### 7.4 De dónde sale el audio

La mezcla existe en el **módulo 4**, que **no está dibujado** — su kicad,
esquemático y PCB están pendientes. Decidirlo ahora no cuesta nada; decidirlo
después es un respin.

**Una línea diferencial con buffer desde el mixer al ADC del cerebro.**
Diferencial porque rechaza entera la diferencia de masas, así que la frontera
`GNDA`/`GNDD` no se toca, y con buffer para que el ADC no cargue ni acople de
vuelta hacia el mixer.

> **Esto es una toma de medida, no un camino de audio.** Nada de lo que se oye
> pasa por aquí. Las reglas duras de masa existen para proteger el CV de tono y
> el audio; un ADC que mide tiene requisitos distintos y mucho más laxos.

**Límites, dichos ahora:** el ADC interno del RP2350 no es de grado
masterización — da medida **accionable**, no certificable, y es el intercambio
correcto. Y «tiempo real» aquí significa **tasa de análisis** (decenas de Hz),
no tasa de muestreo: «hay demasiado grave» no cambia 48 000 veces por segundo.
Si algún día hace falta más, un ADC de audio dedicado en el módulo 4 es el
camino de mejora, y no invalida nada de esto.

### 7.5 El memo del agente

Como el ADC ya está, grabar **unos segundos** en SRAM cuesta casi nada y sirve
de verdad: *«¿en qué tonalidad está esto que toqué?»*, *«imita este timbre»*. Es
el mensaje `MEMO` de §4.1.

**No es un sampler**, y la diferencia importa: es que el agente pueda oír una
frase. El sampler es el módulo 9 y §10 explica por qué no vive aquí.

---

## 8. Alcance del firmware de validación

Corre sobre **placa de desarrollo RP2350**, no sobre PCB propia.

**Dentro:**

- Descubrimiento por I²C a través del mux: EEPROM, identidad, calibración
- Trama SPI del J2 contra la cadena de DAC del módulo 3
- Captura de periodo con PIO, cuatro canales, **y la medida del jitter real**
- Modelo de parámetros y descriptor (§3), con medidas de solo lectura
- Protocolo sobre USB (§4), la tabla de mensajes completa
- Cadena WS2812 sobre una tira de desarrollo: valida `POINT` y el pintado del
  patcheo guiado sin esperar a que existan paneles
- Reparto de voces con robo de la más vieja
- Guardar y recuperar presets en flash
- **Retención de operaciones marcadas y confirmación física** (§2.2) — la regla
  la impone el micro, así que nace aquí, no en la app
- **Motor de análisis en el núcleo 1** (§7) contra una señal de entrada de
  prueba: bandas perceptuales, detección de resonancia, y las medidas
  publicadas como parámetros

**Fuera, y va en specs posteriores:** secuenciador, arpegiador, LFOs, memoria de
acordes; la UI web, el agente, el servidor MCP y el puente de §4.5; el puente
inalámbrico; la PCB; la atribución de §7.2 —que necesita módulos reales
sonando—; y la implementación, que no la definición, de `PATCH_SCAN`.

---

## 9. Cómo se verifica

Siguiendo la costumbre del repo —guiones ejecutables con aserciones, no prosa:

| Qué | Cómo |
|---|---|
| Códec del protocolo | Tests en host, Rust puro. Ida y vuelta de cada mensaje |
| Modelo y descriptor | Tests en host: un descriptor generado se parsea a lo mismo |
| Trama del J2 | Captura con analizador lógico: 72 bits, `CS` abajo entero, orden `[U7][U6][U5]` |
| Descubrimiento I²C | Con una EEPROM real en protoboard antes de que exista módulo 3 |
| **Jitter del PIO** | **Medido, y el número entra en `autotune_budget.py`** |
| Reparto de voces | Tests en host con secuencias de notas conocidas |
| Motor de análisis | Señales sintéticas de referencia: tono puro, ruido rosa, y una resonancia inyectada a frecuencia conocida. Se exige que la detecte donde está |
| Confirmación física | Test: una operación marcada llega por USB y **no** se ejecuta hasta el pulsador |
| Presupuestos existentes | Los cuatro siguen en verde: `ground_budget.py`, `tuning_budget.py`, `autotune_budget.py`, `dac_local_budget.py` |

---

## 10. Restricciones globales que esto impone a otros módulos

Se anotan **ahora** porque tocan módulos que aún no se dibujan, y lo que no
queda escrito se pierde.

**Módulo 4 (mixer) — no dibujado, gratis decidirlo:**

- **Salida diferencial con buffer hacia el ADC del cerebro** para el motor de
  análisis (§7.4)

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

**El cerebro (spec siguiente):**

- Mux I²C de 8 canales
- Líneas de `CS` con holgura: módulos 3, 5, 6, 7 **y los futuros 8 y 9**, más
  repuesto
- Un pin para la cadena WS2812
- Entrada de ADC para el análisis, con receptor diferencial
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
   voltajes»*, *«menos analógico en el cerebro = menos que rutear y menos que
   pueda ensuciarse»*.
2. **El núcleo 1 ya tiene dueño**: el motor de análisis de §7, que es la función
   diferencial del instrumento. Reproducir y resamplear competiría con ella.
3. **Como módulos son mejores.** Su salida cae en el patch bay, así que pasa por
   el VCF, el VCA y la envolvente **analógicos** — que es exactamente por qué se
   quiere un sampler de hardware y no un plugin. Y ese patch se guarda y se
   recupera con el resto (§6.2). Meterlos en el cerebro tiraría esa ventaja.

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

### Abiertos

1. **La pila UMP para RP2350 es C, no Rust** — el único punto que empeoró. Tres
   salidas en §4.4; se decide en el plan.
2. **El jitter del PIO sigue sin medir.** Es el entregable de §5.1: hasta que
   exista, el presupuesto del autoafinado se apoya en un número ajeno que ya no
   aplica.
3. **El barrido por inyección no se ha probado nunca**, y no hay hardware donde
   probarlo hasta que exista un módulo con jacks de CV sensados. Se congela el
   mensaje y el formato; la implementación puede descubrir que hace falta más
   hardware del previsto.
4. **El mux I²C concreto no está elegido** ni verificado contra stock de LCSC.
5. **La atribución de §7.2 no está probada.** El razonamiento es sólido —el
   cerebro tiene el estado y la medida— pero cruzar un pico espectral con la voz
   que lo causa no se ha hecho nunca aquí, y puede resultar más ambiguo de lo
   que parece con cuatro voces sonando a la vez.
6. **El invariante de §2.1 es una disciplina, y las disciplinas se rompen bajo
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
