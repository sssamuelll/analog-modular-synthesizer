# El pase del núcleo: por qué puerta entró, y qué se le permite

**Estado: PROPUESTA v2.** No toca cobre ni firmware todavía. Cierra —o
encamina— seis issues que resultaron ser el mismo paciente: #172, #177, #159,
#145, #144 y #149.

**v2 (2026-08-23).** La v1 fue a junta con Voronov y Halberg y volvió con seis
correcciones, cuatro de ellas a números o a nombres que la v1 había puesto mal.
Van marcadas **[v2]** donde cambian algo que ya estaba escrito. La lección
transversal es la de siempre en este repo: *el archivo ya lo decía y nadie lo
leyó.*

**El encargo de Samuel, cita exacta (2026-08-23):**

> *«el tema del harness no lo compliquemos tanto ahorita, de verdad. […] si
> vamos a prepararnos para un escenario donde tengamos cosas que configurar
> pero que todo sea opcional, que por ejemplo yo pueda configurar modo de que
> permito hacer a que, y fuera cacho (una politica de seguridad de servicios
> y borralo) es simple, yo igual voy a terminar dando acceso total al agente
> pero para que te hagas una idea la opcion es que todo sea configurable»*

Eso fija el alcance y borra la mitad de lo que la junta del panel insinuaba:
**el mecanismo es un campo; la ceremonia es una tabla, y por defecto está
vacía.** Un «modo» no es maquinaria: es una política guardada con nombre.

---

## 1. Por qué este pase existe

La junta del panel (2026-08-23, Voronov/Serrano/Halberg/Brandt) encontró que
el modelo **no sabe quién escribe**: `Set(id, valor)` no tiene un tercer
campo. Sobre esa ausencia estaban legisladas dos cosas inexpresables — la
ley de capas («la mano gana por parámetro», voz-total §0.2) y la premisa de
modos configurables del panel (principio 4).

Y el tracker ya lo sabía **antes** de la junta. El #159 lo nombra literal
entre los campos que faltan:

> *«**Origen** — quién produjo este cambio. Un campo en `Changed` y en
> `Pending`.»*

Dos investigaciones independientes —una ontológica desde arriba, una de
sesión desde abajo— chocaron con la misma pared. Eso es lo que hace este el
siguiente paso y no otro.

**Y no es una feature nueva: es formalizar lo que el código ya hace a
escondidas.** Hoy, en `servidor.rs`:

- `atender()` rechaza un `CHANGED` de cliente: *«Un cliente no puede fabricar
  un `CHANGED` y mentirle a los demás»* — ya hay una noción de quién puede
  decir qué, binaria e implícita.
- El `Set` distingue dos orígenes por **posición en la pila de llamadas**, y
  el comentario lo confiesa: *«El SET de un CLIENTE anula la rampa que tenga
  ese parámetro. El del tick no — y esa diferencia vive aquí, no en el
  modelo»*.

La distinción existe. Este pase la convierte en **dato** en vez de
convención.

## 2. El mecanismo: `puerta`, no `origen` **[v2]**

`atender(&mut self, m: Mensaje, ahora_ms: u64) -> Respuestas` es **la única
puerta** del instrumento (`modelo.rs`: *«si algo muta el instrumento sin pasar
por aquí, el agente no lo alcanza»*). Ahí entra el campo:

```rust
atender(&mut self, m: Mensaje, puerta: Puerta, ahora_ms: u64) -> Respuestas
```

**La v1 lo llamó `origen`, y era un nombre que prometía más de lo que el dato
sabe.** El transporte no conoce *quién* escribe: conoce **por dónde entró**. Con
un solo cable USB declarado (`usb.rs:68`), un agente por MCP y una carcasa web
entran por la misma puerta y son **indistinguibles hoy**. Llamarlo «origen»
invitaba a escribir políticas que el dato no puede sostener; llamarlo `puerta`
dice exactamente lo que hay.

**El campo NO viaja en el mensaje. Lo estampa el transporte que lo recibió.**
Esa es la decisión de diseño que hace todo lo demás barato:

- Un cliente **no puede mentir sobre por dónde entró**, por construcción — no
  hay campo que falsificar.
- **Cuesta cero bytes en el cable.** El formato del protocolo no cambia por
  esto (sí cambia por §5, que es otra cosa).
- Es exactamente el patrón que `del_instrumento()` ya usa, generalizado.

Las puertas propuestas, cortas a propósito:

| `Puerta` | Qué entra por ahí | Transporte |
|---|---|---|
| `Mano` | panel de mandos, encoder de la cabeza, pulsador, pedal | J2 del módulo de mandos, GPIO de la cabeza |
| `Usb` | el agente por MCP **y** cualquier carcasa — hoy no se separan | USB |
| `Inalambrica(u8)` | carcasa por el puente; el `u8` es la suscripción, no una identidad criptográfica | puente inalámbrico |
| `Interno` | el tick, las rampas, la carga de preset | llamada interna |

**[v2] Esto no es una partición de «quién».** `Usb` mezcla dos actores y lo
dice en el nombre. El día que el nibble de cable de USB-MIDI se lea de verdad
(#182, fallo 7 — hoy `usbmidi.rs:105` lo descarta) se podrá separar sin
rehacer nada: es añadir variantes, no cambiar el mecanismo.

**The Cut:** ni criptografía, ni identidad fuerte del agente, ni tokens por
cliente. El emparejamiento ya existe (voz-total §0.2, cláusula 2) y basta.

### 2.1. El sello se arrastra **[v2]**

Halberg: un acto **continuado** lavaría a su autor. Si la mano dispara la carga
de un preset y el preset escribe cuarenta parámetros, esas cuarenta escrituras
entran por `Interno` y la mano desaparece del registro — cuando en realidad
todas son consecuencia de un gesto físico.

Regla, y es del núcleo, no de la política: **un acto que nace de otro arrastra
la puerta del que lo originó.** La carga de preset, el afinado y las rampas no
estampan `Interno` a secas: propagan la puerta del acto que las lanzó.
`Interno` queda **solo** para lo que nace del reloj sin que nadie lo pida.

Sin esta regla, la ley de capas se puede evadir sin querer: basta que algo pase
por un preset.

## 3. Dos tablas, no una **[v2]**

La v1 se contradijo sola en seis líneas: decía *«tabla vacía = todo permitido»*
y seis líneas después *«la ley de capas pasa a ser la fila por defecto»*. Una
fila por defecto **es** una tabla no vacía. Voronov lo cazó, y al mirarlo de
cerca resultó que el error era más hondo: **estaban mezcladas dos cosas
distintas.**

| | **Autoridad** | **Comportamiento** |
|---|---|---|
| Pregunta | ¿se le permite a esta puerta? | ¿qué le pasa a lo que ya había? |
| Ejemplo | «la puerta `Usb` no calibra» | «si escribe la mano, la automatización de ese parámetro queda `ANULADO`» |
| Por defecto | **vacía = todo permitido** | **la ley de capas, encendida** |
| Si se borra | todo permitido | la última escritura gana, venga de donde venga |

**Esa distinción es la que arregla la contradicción.** La tabla de autoridad
nace vacía porque Samuel va a dar acceso total. La ley de capas no es una fila
de autoridad: es comportamiento, siempre estuvo encendida, y borrarla **no**
restaura «la mano gana» — restaura «gana el último que escriba». Que es otra
cosa, y peor.

Sobre la tabla de autoridad:

- El «qué» son **clases**, no 536 filas: `tocar` (parámetros de
  interpretación), `rutear` (aristas de la bahía), `preset`, `calibrar`,
  `firmware`. Empezar por clases y bajar a parámetro **solo si algún día hace
  falta** — hoy no hace falta.
- **Un modo es una política guardada con nombre.** «Live», «ejecución»,
  «exploración» son filas, no código. Cambiar de modo es cargar otra tabla.
  Firmware: cero máquinas de estado, cero transiciones que mantener.
- **Se borra.** Sin política, el instrumento se comporta como hoy.

Voronov, sobre por qué esto importa: *«mientras la autoría no sea un objeto de
primera clase, "la mano gana" no es una ley: es una cortesía»*. Con esto es una
fila, y una fila sí es una ley.

## 4. El punto fijo declarado **[v2]**

Serrano y Halberg llegaron por caminos distintos a la misma pregunta: *si la
política es configurable, ¿qué impide que se configure la contención?* El #149
ya lo tenía nombrado — el agente puede redefinir qué significa «pulsado».

La respuesta no puede ser otra tabla, porque esa tabla también sería
configurable. Tiene que ser un **punto fijo declarado**, y ya existe en el
cobre: `descriptor.confirmacion_fisica` (`descriptor.rs:93`, bandera bit 2).

Regla: **un parámetro con `confirmacion_fisica` no se puede desactivar por
política, y la bandera misma no es escribible por ninguna puerta.** Es el
suelo. Todo lo demás es negociable; esto no.

### 4.1. Y la confirmación física no tiene puerta **[v2]**

Verificado en el cobre: `servidor.rs:307` es

```rust
pub fn confirmacion_fisica(&mut self, ahora_ms: u64) -> Respuestas
```

**No recibe puerta, y no debe recibirla.** La v1 insinuaba que la confirmación
debía exigir que la puerta coincidiera con la del acto retenido. Sería un
error: invertiría §2.2, porque el sentido de la confirmación física es que **un
humano en la sala** autorice lo que pidió algo remoto. Exigir que coincidan
haría que solo puedas confirmar lo que tú mismo mandaste, que es justo lo
contrario del mecanismo.

Lo que sí gana la retenida es el campo `puerta` **para mostrarlo**, no para
compararlo: el renglón puede decir *«el agente pide calibrar el filtro 3 —
¿confirmas?»*. El #144 se cierra así, y no como decía la v1.

## 5. Los techos, que hay que romper igual (#172) **[v2: se parten en dos]**

Nada de lo anterior sirve si el modelo no puede publicarse, y hoy no puede.
Halberg: *«hoy ninguna carcasa puede renderizar este módulo»*.

**La v1 metió tres techos en el mismo saco y eso hizo que todo pareciera caro.
No lo es: son dos mitades de costo opuesto.**

### 5.1. La mitad barata — va sola, hoy

| Cota | Hoy | Cuesta |
|---|---|---|
| `modelo.rs:9: MAX_PARAMS = 512` | 536 censados (`check_censo_voz.py`) | **una constante** |

`Modelo` guarda `descs: Vec<&'static Descriptor, MAX_PARAMS>` y `vals:
Vec<Valor, MAX_PARAMS>`, con `Valor = i32` (`param.rs:15`). Son **8 bytes por
parámetro** en ARM32. Subir a 576 son **+512 bytes** sobre los 520 KB de SRAM
del RP2350B: 0,1 %.

No necesita romper ningún formato, ni ninguna decisión de Samuel. Y el
comentario que tiene al lado —*«Capacidad, no conteo. Cinco módulos poblados
con sus voces caben de sobra»*— **hoy es falso**, y el censo es quien lo cazó.

### 5.2. La mitad cara — necesita N4

| Cota | Hoy | Cuesta |
|---|---|---|
| `fw/src/usb.rs:159`: `[0u8; 256]` por descriptor | un enumerado de 16 posiciones con etiquetas de 12 caracteres ya son 248 B | romper el formato |
| `servidor.rs:31: MAX_RESPUESTAS = 4` | un giro de perilla «por programa» son 16 `CHANGED` | dimensionar contra el gesto real |

**[v2] La v1 dijo que el techo era el largo de blob en 1 byte de
`descubrimiento.rs`, «107× el techo». Es falso, y compara dos magnitudes sin
relación.** Ese byte es el largo del **blob de calibración** en la EEPROM de
identidad del módulo; el descriptor no pasa por ahí, sale por SysEx. El techo
real es el buffer de 256 B de `usb.rs:159`, y el `?` de la línea 162 **aborta
el volcado entero, en silencio**, si un solo descriptor se pasa (#182, fallo 5).

**Se rompe una sola vez, y por eso conviene hacerlo con §2 y §4 encima:** el
formato hay que abrirlo para el descriptor, y los campos nuevos viven en el
mismo formato. Abrir al paciente dos veces sería tonto.

## 6. Lo que `puerta` cierra de regalo

| Issue | Qué le pasa |
|---|---|
| **#159** | Es el campo que pidió. Y se le suma **«último tocado, con su puerta»** — lo que el renglón del panel necesita para escribir nombre y valor. **NO** se construye el modelo de navegación completo (eso es #156 y sigue prohibido por el spec del cerebro) |
| **#144** | `Retenida` gana `puerta` **para mostrarla**, no para compararla — ver §4.1. Deja de ser *«un consentimiento a lo que sea que esté encima de la pila»* porque el renglón puede decir qué se está confirmando |
| **#149** | Se cierra por §4, no por una fila: la polaridad del pedal es un punto fijo declarado. La recursión se rompe sin sacar el parámetro del modelo, y además **la mano tiene otra puerta**: el encoder de la cabeza. Se arregla el pedal sin el pedal |
| **#145** | `suscrito: bool` pasa a conjunto con identidad. Es prerrequisito de `CHANGED` con destinatario, y `Inalambrica(u8)` ya trae el índice |
| **#177** | Es este papel |

## 7. El motor de aterrizaje (el salto suave de Samuel)

A3 del panel quedó firmada en la sensación y derogada en el mecanismo:
`rampa.rs` trabaja en **pulsos musicales cuantizados** (`inicio: u64` *«ya
viene cuantizado por la rejilla»*, `duracion: u32` *«en pulsos»*), así que el
mismo planeo duraría 3× más a 60 BPM que a 180. Requisitos del motor nuevo,
que es **otro objeto**, no una rampa:

- Milisegundos de pared, no pulsos. Sin cuantizar.
- **Umbral de gesto en LSB con histéresis, declarado y aseverado.** Sin él,
  1 LSB de ruido de ADC en 45 potes le quita el instrumento al agente en
  silencio — y con `puerta` puesta, encima queda registrado como si la mano
  lo hubiera hecho.
- Clase de aterrizaje **por parámetro** (campo nuevo del descriptor, §5.2) y
  por comportamiento (§3).
- **Cota mano→DAC en ms, aseverada por guion.** Ya existe:
  `hardware/02-midi-cv/latencia_mano_budget.py`, 0,654 ms en el peor caso.
- No colisiona con `MAX_RAMPAS = 16`: es su propio recurso, dimensionado
  contra 45 potes.

## 8. El contador de generación **[v2]**

Halberg, y es requisito del núcleo, no adorno: con vista optimista en las
carcasas y escrituras entrando por varias puertas a la vez, **una carcasa no
puede saber si el `CHANGED` que recibe es posterior o anterior a su propia
escritura pendiente.** Hoy no hay forma de ordenarlos.

Un contador monótono por parámetro, que sube en cada escritura aceptada y viaja
en el `CHANGED`, lo resuelve sin relojes ni marcas de tiempo. Cabe en el mismo
formato que ya hay que romper (§5.2), así que su costo marginal es cero si se
hace ahora y es otra ruptura si se hace después.

## 9. Lo que este pase NO construye

- **Ninguna máquina de estados de modos.** Un modo es una tabla.
- **Ninguna identidad criptográfica.** El emparejamiento ya existe.
- **Ninguna separación agente/carcasa.** Hoy entran por la misma puerta y el
  papel lo dice; se separa cuando se lea el nibble de cable (#182, fallo 7).
- **Ningún editor de políticas en el instrumento.** Lo hacen las carcasas.
- **Ningún ACL por parámetro individual.** Clases; se baja de granularidad
  el día que un caso real lo pida.
- **Ningún modelo de navegación.** Solo «último tocado». #156 sigue vivo.
- **Ningún cambio en el panel.** #178 espera a que esto aterrice, justamente
  para no escribirse contra un contrato que va a cambiar.

## 10. Las decisiones de Samuel

- **N1 — El conjunto de `Puerta`:** ¿las cuatro de §2, o hace falta separar
  `Mano` en panel/cabeza/pedal desde ya? (Recomendado: cuatro. Separar
  después es añadir variantes, no rehacer.)
- **N2 — Las clases de autoridad:** ¿tocar / rutear / preset / calibrar /
  firmware, o otro corte?
- **N3 — Dónde vive la política [v2: corregido]:** la v1 dijo *«en la EEPROM
  del cerebro, y ya hay 128 KB»*. **Falso.** Esos 128 KB son el `24AA1025` del
  módulo de Voz (#175). La EEPROM de identidad del cerebro es una
  `24AA02E48` de 256 B, con cabecera de 12 y zona libre hasta `0xFA`:
  **238 bytes útiles**, y `descubrimiento.rs` ya lo decía —*«Son 256 bytes:
  alcanzan para identidad y calibración, no para un descriptor»*. Así que la
  pregunta real es: **¿en la flash del cerebro (sobrevive al apagón, cabe) o en
  el preset (viaja con el sonido)?** Recomendado: **flash** — una política que
  viaja con el preset se la puede cambiar quien te mande un preset.
- **N4 — El descriptor troceado vs largo ancho** (§5.2): decide cuánto duele
  el arranque. Se decide junto con **B3 del pase de la autopista** (la huella
  del descriptor), porque no tiene sentido elegir formato sin saber si se va a
  mandar casi nunca.
- **N5 — ¿Este papel vuelve a junta antes de tocar Rust?** Recomendado: **no**.
  Ya fue, volvió con seis correcciones y están incorporadas. Lo siguiente es
  código con TDD.

## 11. Lo que sigue

1. **§5.1 ya**, sin esperar nada: `MAX_PARAMS`, con su test y su cuenta de RAM.
2. Los fallos 1, 3 y 5 del **#182**, que viven en los mismos archivos y son TDD
   puro.
3. Decididos N1–N4: el spec del núcleo v2 con el formato nuevo (§2, §4, §5.2,
   §8 en la misma ruptura) y los tests que lo cierran.
4. El firmware, con TDD — los tests primero.
5. Recién ahí, **#178** (el módulo de mandos) contra un contrato ya firme.
