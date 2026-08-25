# El pase del núcleo: por qué puerta entró, y qué se le permite

**Estado: v3 — PARTE APLICADA, PARTE PROPUESTA, PARTE PROBLEMA ABIERTO.**

La v2 decía en su tercera línea *«no toca cobre ni firmware todavía»* y ya era
falso cuando se escribió: cuatro commits de esta misma rama habían movido el
cobre. La v3 arranca diciendo qué existe.

| | Qué | Dónde |
|---|---|---|
| **Aplicado** | `MAX_PARAMS` 512 → 1024, derivado del único censo que existe | `c1b8df8` |
| **Aplicado** | El buzón deja de tragarse mensajes; un descriptor gordo ya no mata el volcado | `7e37203` |
| **Aplicado** | La tabla de offsets del descriptor decía `u16` y el codec escribía `u32` | `5fbed0d` |
| **Aplicado** | Las medidas del reloj por fin se anuncian; `modelo_mut` deja de estar abierto | `87e8310` |
| **Propuesta** | El campo `puerta` (§2), la política como tabla (§3), el punto fijo (§4) | este papel |
| **Problema abierto** | La autoría de un acto compuesto, la clave de la política, la identidad del acto, el suelo vacío, #144, #145, y que el instrumento no corre | §12 |

**Cómo leer las citas.** Todo número y toda línea de este papel se releyó del
árbol de trabajo de `nucleo-autoria` el 2026-08-24, con `HEAD` en `87e8310`.
Ninguna cita viene heredada de la v2: la v2 tenía **cinco citas vencidas**, y
cuatro de ellas apuntaban a cobre que este mismo pase había movido. Los
archivos `descriptor.rs`, `servidor.rs` y `usb.rs` tenían cambios sin commitear
cuando esto se escribió; los valores citados son los del árbol, y lo que hay
que re-verificar antes de implementar son los **números de línea**, no los
hechos.

**La lección transversal, otra vez y más cara:** *el archivo ya lo decía y
nadie lo leyó* — incluido este papel leyéndose a sí mismo.

**El encargo de Samuel, cita exacta (2026-08-23):**

> *«el tema del harness no lo compliquemos tanto ahorita, de verdad. […] si
> vamos a prepararnos para un escenario donde tengamos cosas que configurar
> pero que todo sea opcional, que por ejemplo yo pueda configurar modo de que
> permito hacer a que, y fuera cacho (una politica de seguridad de servicios
> y borralo) es simple, yo igual voy a terminar dando acceso total al agente
> pero para que te hagas una idea la opcion es que todo sea configurable»*

Eso fija el alcance: **el mecanismo es un campo; la ceremonia es una tabla, y
por defecto está vacía.** Un «modo» no es maquinaria: es una política guardada
con nombre. Lo que la v3 corrige no es el alcance — es que la v2 dio por
resuelto un montón de cosas que no lo están.

---

## 1. Por qué este pase existe

La junta del panel (2026-08-23, Voronov/Serrano/Halberg/Brandt) encontró que
el modelo **no sabe quién escribe**: `Set(id, valor)` no tiene un tercer campo
(`protocolo.rs:60`, `Set(ParamId, Valor)`). Sobre esa ausencia estaban
legisladas dos cosas inexpresables:

- La ley de capas — *«La mano gana por parámetro. Un gesto físico (perilla,
  cable en la bahía) captura ese parámetro o ruta»* (voz-total §0.2, cláusula 1).
- La premisa de modos del panel — *«Cada modo es una política nombrada de
  arbitraje sobre escrituras con autor. Consecuencia dura, dicha por la junta
  entera y asumida: esto exige que el modelo sepa quién escribe»*
  (`2026-08-23-panel-frontal-gramatica.md`, §5.1).

Ese mismo §5.1 declara este pase **prerrequisito** suyo, y cita a Voronov:
*«una cortesía que el agente puede retirar»*.

**Y no es una feature nueva: es formalizar lo que el código ya hace a
escondidas.** Hoy, en `servidor.rs`:

- `atender()` rechaza un `CHANGED` de cliente (`servidor.rs:155-159`): *«Un
  cliente no puede fabricar un `CHANGED` y mentirle a los demas»*. Ya hay una
  noción de quién puede decir qué, binaria e implícita.
- El `Set` distingue dos orígenes por **posición en la pila de llamadas**, y el
  comentario lo confiesa (`servidor.rs:176-178`): *«El SET de un CLIENTE anula
  la rampa que tenga ese parametro. El del tick no — y esa diferencia vive
  aqui, no en el modelo, que no gana ninguna puerta nueva»*.

La distinción existe. Este pase la convierte en **dato** en vez de convención.

> **Nota de nombres, y no es cosmética.** El núcleo ya tiene un módulo llamado
> `atribucion` (`core/src/atribucion.rs`, §7.2): es la atribución **espectral**
> de un pico de frecuencia a una voz, y no tiene nada que ver con quién escribe
> un parámetro. El día que esto aterrice, el concepto de este papel **no** se
> llama `atribucion`.

## 2. El mecanismo: `puerta`, no `origen`

El transporte no conoce *quién* escribe: conoce **por dónde entró**. Con un
solo par de jacks USB-MIDI declarado (`usb.rs:68`, `MidiClass::new(&mut
builder, 1, 1, TAM_PAQUETE)`), un agente por MCP y una carcasa web entran por
la misma puerta y son **indistinguibles hoy**. Llamarlo «origen» invitaba a
escribir políticas que el dato no puede sostener; llamarlo `puerta` dice
exactamente lo que hay. Ese nombre es lo único de la v2 que salió intacto de
la revisión, y se queda.

**El campo NO viaja en el mensaje. Lo estampa el transporte que lo recibió.**

- Un cliente **no puede mentir sobre por dónde entró**, por construcción — no
  hay campo que falsificar.
- **Cuesta cero bytes en el cable.** El formato del protocolo no cambia por
  esto.
- Es exactamente el patrón que `Mensaje::del_instrumento()` (`protocolo.rs:195`)
  ya usa para el bit alto de la etiqueta, generalizado.

Las puertas propuestas, cortas a propósito:

| `Puerta` | Qué entra por ahí | Transporte |
|---|---|---|
| `Mano` | panel de mandos, encoder de la cabeza, pulsador, pedal | J2 del módulo de mandos, GPIO de la cabeza |
| `Usb` | el agente por MCP **y** cualquier carcasa — hoy no se separan | USB |
| `Inalambrica` | carcasa por el puente inalámbrico | puente inalámbrico |
| `Interno` | el tick y las rampas | llamada interna |

**Esto no es una partición de «quién».** `Usb` mezcla dos actores y lo dice en
el nombre. El día que el nibble de cable de USB-MIDI se lea de verdad (#182,
fallo 7) se podrá separar sin rehacer nada: es añadir variantes. Hoy no se lee
— `usbmidi.rs:105` hace `let cin = p[0] & 0x0F;`, o sea que se queda con el
nibble bajo (el CIN) y **tira el alto, que es el número de cable**.

**[v3] `Inalambrica` pierde el `u8`.** La v2 le colgaba un `u8` y lo llamaba
*«la suscripción»*. Es un error de eje, y el papel hermano del mismo pase lo
dice con todas sus letras (`2026-08-23-autopista-el-pase-de-ancho-de-banda.md`,
§5): *«La puerta de entrada y el encaminamiento de salida son **dos ejes
distintos**; saber por dónde entró algo no dice a dónde va la respuesta»*. Y
el propio conjunto lo demuestra: `Mano` no tiene `u8` y escribe igual. La
identidad del suscriptor es otra cosa, es N5, y va con #145.

**The Cut:** ni criptografía, ni identidad fuerte del agente, ni tokens por
cliente. El emparejamiento ya existe (voz-total §0.2, cláusula 2) y basta.

### 2.1. `atender` no es la única puerta — son siete caminos

La v2 apoyaba todo el mecanismo en esta frase: *«`atender` es **la única
puerta** del instrumento»*, y la sostenía citando `modelo.rs`. La cita es real
y dice otra cosa. `modelo.rs:1-2`:

```
//! El estado vivo del instrumento. Por §2.1 esta es la UNICA puerta: si algo
//! muta el instrumento sin pasar por aqui, el agente no lo alcanza.
```

«Aquí» es el **`Modelo`**, no `atender`. El invariante es del estado, no de la
función. Y contado sobre el árbol, los caminos que escriben son siete:

| # | Camino | Firma | Nota |
|---|---|---|---|
| 1 | `Instrumento::atender` | `servidor.rs:153` | el del cable |
| 2 | `Instrumento::tick` | `servidor.rs:296` | lo llama un reloj |
| 3 | `Instrumento::confirmacion_fisica` | `servidor.rs:363` | el pulsador |
| 4 | `Instrumento::caducar` | `servidor.rs:380` | el TTL |
| 5 | `Instrumento::publicar_medida` | `servidor.rs:393`, **`pub`** | escribe el modelo desde fuera |
| 6 | `Instrumento::reloj_mut` | `servidor.rs:129`, **`pub`** | entrega un `&mut Reloj` entero |
| 7 | `medidas::ingerir` | `medidas.rs:190`, **`pub`** | escribe un `&mut Modelo` de frente |

Poner `puerta` en `atender` sella **uno de siete**. Los seis restantes no son
teóricos: los caminos 2, 3 y 4 son los que la ley de capas necesita distinguir,
y el 7 es la ruta por la que el módulo 4 mete sus medidas por el J2 (§7.4).

Dos matices que hay que decir para no exagerar en el otro sentido:

- El camino 7 **hoy no alcanza al instrumento vivo**: `Instrumento::modelo()`
  devuelve `&Modelo`, y `modelo_mut` pasó a `#[cfg(test)]` en `87e8310`
  (`servidor.rs:144-147`). O sea que `medidas::ingerir` es una función pública
  que escribe un `Modelo` que nadie puede sacarle a un `Instrumento`. Eso no es
  un cierre: es que la ruta de las medidas del J2 **no está cableada**.
- El camino 6 no escribe el `Modelo` — escribe el `Reloj`, que es el que
  alimenta las cinco medidas de `publicar_medidas_del_reloj`
  (`servidor.rs:320-343`). El efecto llega al modelo por el camino 2.

**Consecuencia para el diseño:** `puerta` no puede ser un argumento de
`atender`. Tiene que ser un argumento de **la escritura**, o sea de lo que hoy
son `Modelo::set` (`modelo.rs:110`), `Modelo::publicar_medida`
(`modelo.rs:128`) y `Modelo::aplicar_confirmado` (`modelo.rs:139`). Ese es el
único sitio por donde pasan los siete.

### 2.2. «El sello se arrastra» — **DEROGADO**

La v2 legislaba: *«un acto que nace de otro arrastra la puerta del que lo
originó»*. Se cae por dos razones independientes, y cualquiera de las dos
basta.

**Primera: destruye la ley que dice proteger.** Si la mano dispara la carga de
un preset de cuarenta parámetros, arrastrar el sello estampa `Mano` en las
cuarenta escrituras. Bajo la ley de capas (voz-total §0.2, cláusula 1) eso
**anula la automatización del agente en cuarenta parámetros** — treinta y nueve
que el humano no tocó ni sabe que existen. La autoría **no es distributiva
sobre la composición**, y la v2 la volvió distributiva por decreto.

**Segunda: no es implementable como está.** El trazado, verificado:

- `Rampa` no tiene campo de autoría (`rampa.rs:27-39`: `id`, `origen`,
  `destino`, `inicio`, `duracion`, `curva`, `anulada`).
- `Escrituras` es una tupla de dos (`rampa.rs:110`:
  `Vec<(ParamId, Valor), MAX_RAMPAS>`).
- `Rampas::tick` no recibe ni devuelve autoría (`rampa.rs:184`:
  `tick<F>(&mut self, pulso: u64, unidad_de: F) -> Escrituras`).
- `Instrumento::tick` recibe **solo** un pulso (`servidor.rs:296`:
  `tick(&mut self, pulso: u64)`). No hay nada en su cadena de llamada que tenga
  una puerta que darle: lo llama un reloj.

Y el remate, que es el más feo: **`Rampas::empujar` reemplaza la rampa vieja
del mismo id** (`rampa.rs:136-142`), con su test que lo clava
(`una_rampa_nueva_sobre_el_mismo_parametro_reemplaza_a_la_vieja`,
`rampa.rs:354`). O sea que la autoría de la rampa reemplazada desaparece sin
registro. El «acto continuado que lava a su autor» que §2.1 decía prevenir
ocurre **dentro del mecanismo**, hoy.

**Y el ejemplo que la motivaba no existe.** `Mensaje::PresetLoad(_)` contesta
`CodigoError::NoDisponible` (`servidor.rs:199-205`), y **nadie importa
`crate::preset`** en todo el árbol. El módulo `preset.rs` está escrito, probado
y desconectado.

**Lo que queda como problema abierto (P1), con sus requisitos:**

1. Un acto compuesto necesita **un identificador de acto**, no una puerta
   heredada: la escritura número 17 de una carga de preset tiene que poder
   decir «vengo del acto A», y el acto A dice «lo pidió `Mano`». Sin ese
   nivel de indirección, cualquier regla que mire la puerta de la escritura
   individual da la respuesta equivocada.
2. La ley de capas tiene que poder preguntar **«¿lo tocó una mano *este*
   parámetro?»**, no «¿la puerta de esta escritura es `Mano`?».
3. `Rampas::empujar` tiene que dejar de borrar en silencio: reemplazar una
   rampa es un evento con autor, y hoy no produce ni un `Anulado`.

**Además hay dos conceptos de autoría sin reconciliar, y hay que elegir uno.**
`Preset` ya tiene autor y **viaja en el cable**: `pub autor: &'a str`
(`preset.rs:50`), con su sitio en el formato (`preset.rs:13-14`: *«1 + n
autor»*). `puerta` explícitamente **no** viaja. Uno es «quién compuso esto»
—un dato de biblioteca, editable, humano— y el otro es «por dónde entró este
byte» —un dato de transporte, infalsificable, de máquina—. Que compartan la
palabra «autor» es cómo se llega a un papel que cree haber resuelto algo.

## 3. La política: el mecanismo se sostiene, la taxonomía no

La v2 partió la política en dos tablas —autoridad y comportamiento— para
resolver una contradicción de la v1. Voronov: **no la disolvió, la
factorizó.**

Porque §2.1 le dio puerta a *lo que ya había*, comportamiento es una función
de `(puerta_entrante, puerta_residente, clase)`, y autoridad es **esa misma
función con el segundo argumento cuantificado existencialmente**: «¿se le
permite a esta puerta?» es «¿existe alguna puerta residente para la que el
comportamiento no sea rechazar?». Es una tabla y una proyección suya, no dos
tablas. Presentarlas como dos hace que parezca que se pueden borrar por
separado, y no se puede.

Lo que **sí** se sostiene de la v2, y hay que salvarlo de la demolición:

- **Un modo es una política guardada con nombre.** «Live», «ejecución»,
  «exploración» son filas, no código. Cambiar de modo es cargar otra tabla.
  Firmware: cero máquinas de estado, cero transiciones que mantener.
- **Se borra.** Sin política, el instrumento se comporta como hoy.
- **Por defecto está vacía**, porque Samuel va a dar acceso total.
- **La ley de capas no es una fila de la política.** Es comportamiento del
  núcleo, siempre encendido, y borrarlo no restaura «la mano gana»: restaura
  «gana el último que escriba», que es otra cosa y peor.

### 3.1. La clave de la tabla no existe en el modelo de datos

La v2 dijo que el «qué» de la tabla son **clases** — `tocar`, `rutear`,
`preset`, `calibrar`, `firmware` — y que eso evita 536 filas. El problema es
que **no hay dónde poner la clase.**

- **`ParamId` no tiene campo de clase, y no le cabe uno.** Son 32 bits repartidos
  en 8 reservados + tres niveles de ruta de 4 + instancia de 4 + índice de 8
  (`param.rs:21-25`). Los 8 reservados están **cerrados por test**:
  `ParamId::valida()` devuelve `false` si `self.0 >> 24 != 0`
  (`param.rs:147-149`), y `los_bits_reservados_estan_a_cero` lo asevera
  (`param.rs:249`). Meter una clase ahí rompe una puerta verde y, de paso, la
  propiedad de que el subárbol de un módulo quede contiguo en el orden numérico
  (`el_orden_numerico_agrupa_por_modulo`, `param.rs:260`).
- **`Descriptor` no tiene campo de clase** (`descriptor.rs:91-111`: `id`,
  `nombre`, `tipo`, `ambito`, `solo_lectura`, `medida`, `confirmacion_fisica`,
  `acepta_modulacion`, `min`, `max`, `def`, `unidad`, `etiquetas`). En el byte
  de banderas del cable quedan usados los bits 0, 1, 2, 3, 4-5 y 6
  (`descriptor.rs:188-193`): **queda el bit 7 y nada más.** Un bit no codifica
  cinco clases.

Y las dos únicas formas de añadirlo están prohibidas por el propio §9 de este
papel:

1. **Campo del descriptor** — el módulo declararía **su propia jurisdicción**,
   desde una EEPROM que cualquiera reflashea. Eso no es una política del
   instrumento: es una política que el periférico se autoconcede.
2. **Tabla por `ParamId`** — eso es exactamente el ACL por parámetro que §9
   dice que este pase no construye.

### 3.2. Y hay filas que no coinciden con nada, y mensajes que no coinciden con ninguna fila

**`firmware` no tiene ningún mensaje.** El protocolo son 24 variantes
(`protocolo.rs:53-133`) y ninguna es de firmware ni de DFU. Es una fila que
nunca aplica. Viene de voz-total §0.2 cláusula 3 —*«borrar bancos, escribir
calibración, firmware — piden confirmación física»*— y ahí sí tiene sentido,
porque ahí es una **lista de actos irreversibles**, no una clase de mensaje.

**Y ocho de los quince mensajes de cliente no tienen clase.** Los mensajes de
cliente son las etiquetas con el bit alto en cero, `0x01..0x0F`
(`protocolo.rs:137-159`), quince exactas:

| Mensaje | Etiqueta | Clase v2 |
|---|---|---|
| `Set` | `0x04` | tocar |
| `Rampa` | `0x0E` | tocar |
| `PresetList` / `PresetLoad` / `PresetSave` | `0x06`-`0x08` | preset |
| `TuneStart` | `0x09` | calibrar |
| `PatchScan` | `0x0A` | rutear |
| `Hello` | `0x01` | **ninguna** |
| `Describe` | `0x02` | **ninguna** |
| `Get` | `0x03` | **ninguna** |
| `Subscribe` | `0x05` | **ninguna** |
| `Telemetry` | `0x0B` | **ninguna** |
| `Point` | `0x0C` | **ninguna** |
| `Memo` | `0x0D` | **ninguna** |
| `Reactivar` | `0x0F` | **ninguna** |

`Reactivar` no cae en `tocar` y no es un descuido: no escribe un parámetro,
**cambia quién puede escribirlo** (`servidor.rs:259-279`). Es comportamiento,
no autoridad — la distinción que §3 acaba de decir que no es una partición.

**Y `Memo` es el caso que obliga a decidir.** `Memo { segundos: u8 }`
(`protocolo.rs:76-79`) es *«§7.5: unos segundos de audio para que el agente los
analice»*: **graba el cuarto**. Es el único acto del protocolo con dimensión de
privacidad física, y bajo «tabla vacía = todo permitido» es **inlegislable**,
porque no hay ninguna clave que lo nombre. Hoy contesta `NoDisponible`
(`servidor.rs:205`) y eso lo tapa; el día que el micrófono exista, deja de
taparlo.

**Problema abierto (P2), con su requisito:** cualquier clave de política tiene
que ser **nombrable desde lo que llega**, y lo que llega es
`(etiqueta, ParamId, valor, puerta)`. La etiqueta es total sobre los quince
mensajes y no cuesta un byte nuevo — pero es demasiado gruesa para `Set`, que
es una sola etiqueta sobre 536 parámetros. Ese hueco es lo que N2b tiene que
decidir, y este papel **no lo resuelve por decreto**.

## 4. El punto fijo declarado, y su extensión es el conjunto vacío

Serrano y Halberg llegaron por caminos distintos a la misma pregunta: *si la
política es configurable, ¿qué impide que se configure la contención?* El #149
ya lo tenía nombrado — el agente puede redefinir qué significa «pulsado».

La respuesta no puede ser otra tabla, porque esa tabla también sería
configurable. Tiene que ser un **punto fijo declarado**, y el bit existe:
`pub confirmacion_fisica: bool` (`descriptor.rs:101`), con su sitio en el cable
(bit 2 del byte de banderas, `descriptor.rs:12` y `descriptor.rs:190`) y con
`Modelo::set` haciéndolo valer (`modelo.rs:119-121`, devuelve
`ErrorSet::ExigeConfirmacion`).

**Regla propuesta:** un parámetro con `confirmacion_fisica` no se puede
desactivar por política, y la bandera misma no es escribible por ninguna
puerta. Es el suelo. Todo lo demás es negociable; esto no.

**Y hoy el suelo no tiene a quién sostener.**

`confirmacion_fisica: true` aparece **exactamente dos veces en todo el
software**, y las dos están dentro de `#[cfg(test)]`:
`descriptor.rs:347` (el `MODO` de las pruebas del codec) y `retencion.rs:103`
(el `PELIGROSO` de las pruebas de la retención). **Ningún parámetro de
producción lleva la bandera.**

No es que se les haya olvidado: las dos únicas fábricas de descriptores que
existen la tienen **cableada a `false`** —`tiempo_params.rs:70` y
`tiempo_params.rs:95` para los quince parámetros del reloj, `medidas.rs:53` y
`medidas.rs:100/114/130` para las veintisiete medidas de audio—. Un parámetro
de tiempo **no puede** llevar la bandera sin cambiar el constructor.

Existe el bit; no existe el suelo. Y voz-total §0.2 cláusula 3 legisla
—*«borrar bancos, escribir calibración, firmware — piden confirmación
física»*— sobre una extensión vacía.

**Dos escapes verificados, que hay que cerrar en el mismo pase:**

1. **`publicar_medida` no mira rango ni `confirmacion_fisica`.**
   `modelo.rs:128-135` comprueba **solo** `descs[i].medida` y escribe. El
   recorte al rango vive en el llamador —`medidas.rs:199-202`, `publicar()`
   hace `v.clamp(d.min, d.max)`— o sea que es una **cortesía de un cliente**,
   no una regla del modelo. Y `Instrumento::publicar_medida` es `pub`
   (`servidor.rs:393`).
2. **La bandera deja de ser inmutable cuando los descriptores vengan de la
   EEPROM del módulo.** Hoy es inmutable por construcción:
   `Modelo::registrar(&mut self, d: &'static Descriptor)` (`modelo.rs:76`)
   exige `&'static`, y hoy eso significa «tabla en la flash del cerebro».
   `descubrimiento.rs:25-26` dice por qué: *«Son 256 bytes: alcanzan para
   identidad y calibracion, no para un descriptor»*. El día que el descriptor
   salga de la EEPROM del módulo (#175) —que es a donde apunta N4—, la bandera
   pasa a venir de un chip de treinta centavos que cualquiera reflashea.

**Problema abierto (P4), con sus requisitos:** el punto fijo necesita (a) al
menos un parámetro de producción que lo lleve, o deja de ser una regla y pasa a
ser una intención; (b) que `publicar_medida` deje de ser el hueco por donde
todo entra sin mirar; (c) que la inmutabilidad de la bandera se declare
**contra el origen del descriptor**, no contra `&'static`, porque `&'static`
va a dejar de significar «lo escribió el cerebro».

### 4.1. La confirmación física: el eje era el token, no la puerta — **#144 sigue abierto**

Verificado en el cobre (`servidor.rs:363`):

```rust
pub fn confirmacion_fisica(&mut self, ahora_ms: u64) -> Respuestas
```

**No recibe puerta, y no debe recibirla.** Esta parte de la v2 es correcta y se
mantiene: exigir que la puerta de la confirmación coincida con la del acto
retenido invertiría el mecanismo, porque el sentido de la confirmación física
es que **un humano en la sala** autorice lo que pidió algo remoto. Con esa
exigencia solo podrías confirmar lo que tú mismo mandaste.

**Pero el hueco de #144 nunca fue la puerta: era el token.** `retencion.rs:65`:

```rust
pub fn confirmar(&mut self, ahora_ms: u64) -> Option<Retenida> {
    let i = self.cola.iter().rposition(|r| ahora_ms < r.vence_ms)?;
    Some(self.cola.remove(i))
}
```

No recibe token. Agarra **la más reciente que siga viva**, sobre una cola de
cuatro (`MAX_RETENIDAS = 4`, `retencion.rs:9`) con un TTL de treinta segundos
(`TTL_MS = 30_000`, `retencion.rs:11`). Y no es un descuido: hay un test que lo
clava, `el_pulsador_confirma_la_mas_reciente` (`retencion.rs:150-155`).

Entre que el renglón pinta *«el agente pide calibrar el filtro 3 —
¿confirmas?»* y que el dedo baja hay hasta treinta segundos, y en esa ventana
caben tres retenciones más. El pulsador confirma la última, no la que el
renglón está mostrando.

**Mostrar sin comparar no vincula nada.** La v2 cerró #144 diciendo que la
retenida gana `puerta` para mostrarla; eso mejora el renglón y **no cierra el
issue**. El vínculo entre lo que se muestra y lo que se aplica no existe.

**#144 vuelve a abierto.** Requisito: `confirmar` tiene que recibir el token de
lo que se está mostrando, y devolver un fallo con nombre si ese token ya no
está vivo. Un `RESOLVED { confirmado: false }` por «se te adelantó otra cosa»
es información; confirmar lo equivocado en silencio, no.

## 5. Los techos: la mitad barata está hecha, y la partición se disolvió

### 5.1. `MAX_PARAMS` — **HECHO** (`c1b8df8`)

`modelo.rs:25` ya dice `pub const MAX_PARAMS: usize = 1024;`, y el comentario
de arriba (`modelo.rs:8-24`) deriva el número en vez de elegirlo: 536 de la Voz
total —contados por `hardware/03-vco/check_censo_voz.py`— más 256 **declarados**
de reserva para cerebro, bahía, mandos, telemetría e invitados. La cuenta de
RAM está en el mismo sitio: 8 B por ranura, 1024 ranuras, **8 KB de los 520 KB
del RP2350B**. Y el guion lo **lee** de esa línea en vez de copiarlo
(`check_censo_voz.py:38-57`).

La v2 proponía subir a 576 «+512 bytes». Se subió a 1024, y la razón por la que
576 estaba mal es la misma que el comentario ahora explica: `MAX_PARAMS` es del
**instrumento entero**, y el censo que existe es de **un módulo**.

> **Deuda menor, en `hardware/`, no en este papel:** el docstring de
> `check_censo_voz.py:9` sigue diciendo *«MAX_PARAMS = 512
> software/nucleo/core/src/modelo.rs:9»*. El código lee bien; el comentario
> quedó viejo. Que un guion cuyo propósito es cazar segundas fuentes de verdad
> tenga una en su propio encabezado es exactamente la ironía de este pase.

### 5.2. La partición «mitad barata / mitad cara» era del papel, no de los techos

La v1 metió tres techos en el mismo saco. La v2 los partió en dos mitades de
coste opuesto y argumentó que la mitad cara había que romperla junta **porque
uno de los techos exigía cambio de formato**. Ese argumento ya no es cierto, y
hay que decirlo porque cambia la planificación:

**El buzón se rompió sin tocar el formato.** `servidor.rs:46`:

```rust
pub const MAX_RESPUESTAS: usize = MAX_RAMPAS + MEDIDAS_POR_TICK + 2;
```

Son 23 (`MAX_RAMPAS = 16`, `rampa.rs:24`; `MEDIDAS_POR_TICK = 5`,
`servidor.rs:32`), derivados del peor caso real en vez de elegidos, con un
`trait Buzon` que `debug_assert`ea el desborde (`servidor.rs:67-79`) en lugar
de tragárselo con `let _ =`. Cero bytes de cable. Commit `7e37203`.

**El techo del descriptor tampoco necesitó formato.** `MAX_DESCRIPTOR_B = 256`
(`descriptor.rs:175`) ganó una puerta que salta al 75 % de ocupación
(`OCUPACION_MAX_B`, `descriptor.rs:183`, con el test
`ningun_descriptor_se_acerca_al_techo_del_volcado`), y el `?` que abortaba el
volcado entero pasó a `continue` (`usb.rs:171-173`). Medido el 2026-08-24 y
anotado en `descriptor.rs:179-182`: **el descriptor más gordo son 106 B, el
41 %** — «cuantización global», que es el enumerado de nueve etiquetas de
`tiempo_params.rs:163-170`.

**Lo que sí queda pendiente y sí es formato** es una sola cosa, y el cobre la
nombra solo. `usb.rs:177-179`:

```
// NO se manda terminador ni conteo: el cliente sigue sin poder distinguir
// "termino" de "se aborto". Eso es un cambio de FORMATO y lo decide N4 del
// pase del nucleo -- aqui no se inventa.
```

Conteo al principio, terminador al final y largo por entrada. Y eso es
exactamente lo que la autopista §3 ya legisla, junto con la huella del
descriptor (B3) y el canal binario crudo (B4). **No es de este papel.** N4 se
recorta a eso: reconocer que la decisión vive allá.

## 6. Qué issues toca de verdad este pase

La v2 cerró dos issues que no están cerrados. La v3 los devuelve.

| Issue | Qué le pasa |
|---|---|
| **#159** | **Lo encamina.** Es el campo que pidió — *«Origen — quién produjo este cambio. Un campo en `Changed` y en `Pending`»*, citado de la v1 y no verificable desde el árbol. Se le suma «último tocado, con su puerta», que es lo que el renglón del panel necesita. **NO** se construye el modelo de navegación (#156 sigue prohibido por el spec del cerebro) |
| **#144** | **SIGUE ABIERTO.** La retenida gana `puerta` para mostrarla, y eso es una mejora del renglón, no el cierre. `confirmar()` no recibe token (`retencion.rs:65`) y agarra la más reciente viva: mostrar sin comparar no vincula nada. Ver §4.1 |
| **#145** | **SIGUE ABIERTO.** La v2 lo cerraba «de regalo» con el `u8` de `Inalambrica`, y #145 es un problema de **salida**: hoy `suscrito: bool` (`servidor.rs:97`) y `Subscribe { activo }` lo pisa sin mirar quién habla (`servidor.rs:192`), así que **un `SUBSCRIBE {activo:false}` de un cliente calla al otro, sin error** — el silencio de `SUBSCRIBE` es a propósito y está en un test (`los_dos_unicos_silencios_son_a_proposito`, `servidor.rs:669`). Pasa a ser N5 |
| **#149** | **Lo encamina, condicionado a §4.** La polaridad del pedal como punto fijo declarado rompe la recursión sin sacar el parámetro del modelo, y además la mano tiene otra puerta: el encoder de la cabeza. Pero mientras ningún descriptor de producción lleve la bandera (§4), esto es una regla sin sujeto |
| **#172** | **Cerrado en su mitad medible** (`c1b8df8`, `7e37203`). Lo que queda del techo del volcado es contrato de formato y vive en la autopista |
| **#177** | Es este papel |

## 7. El contador de generación no resuelve lo que enuncia

La v2 lo presentaba como requisito del núcleo: con vista optimista en las
carcasas y escrituras entrando por varias puertas, una carcasa no puede saber
si el `CHANGED` que recibe es posterior o anterior a su propia escritura
pendiente.

Un contador monótono por parámetro da **orden total por parámetro**. No da
**identidad**. La carcasa no conoce el número que su propia escritura va a
recibir —lo asigna el instrumento al aceptarla—, así que al recibir
`CHANGED(id, v, gen=7)` sigue sin saber si es el eco de lo suyo o de otro.

Y no se arregla metiendo la puerta dentro del `CHANGED`, porque §2 de este
mismo papel dice que `Usb` **no separa agente de carcasa**. **§7 declaraba
resuelto un problema que §2 declara indistinguible, en el mismo documento.**

**Y el coste no es cero.** Un tercer `Vec<u32, MAX_PARAMS>` son 4 B × 1024 =
**+4 KB**. O sea **12 KB, no los 8 KB** que §5.1 usa como argumento de que
subir el techo era barato. Sigue siendo poco sobre 520 KB, pero el número que
el papel repite deja de ser el número.

**Y el ancho importa.** Si las medidas del reloj cuentan generaciones —y hoy
`publicar_medidas_del_reloj` escribe `ID_POSICION` en cada tick donde se
movió, `servidor.rs:327-342`—, un `u16` sobre `ID_POSICION` da la vuelta muy
rápido: `PPQN_INTERNO = 96` (`rejilla.rs:9`), a 120 BPM son 192 pulsos por
segundo, y 65.536 / 192 = **341 segundos, o sea menos de seis minutos**. Un
`u16` no sirve; un `u32` es el que cuesta los 4 KB.

**Problema abierto (P3), con sus requisitos:** lo que la vista optimista
necesita no es orden, es **poder reconocer su propio eco**. Eso se resuelve con
un **token de petición devuelto** —el cliente elige un número, el instrumento
lo devuelve en el `CHANGED` que causó esa petición, y lo que no lleva token es
de otro— y ese token va en el mismo eje que la identidad de suscriptor de N5.
El contador de generación es útil **además**, para ordenar, y por eso queda
sobre la mesa; pero no puede seguir presentándose como el que cierra el
problema.

## 8. El motor de aterrizaje (el salto suave de Samuel)

A3 del panel quedó firmada en la sensación y derogada en el mecanismo. La razón
es verificable: `rampa.rs` trabaja en **pulsos musicales cuantizados**
(`rampa.rs:31`, `inicio: u64` *«Pulso absoluto en que arranca. Ya viene
cuantizado por la rejilla»*; `rampa.rs:33`, `duracion: u32` *«En pulsos»*), así
que el mismo planeo duraría 3× más a 60 BPM que a 180.

Requisitos del motor nuevo, que es **otro objeto**, no una rampa:

- Milisegundos de pared, no pulsos. Sin cuantizar.
- **Umbral de gesto en LSB con histéresis, declarado y aseverado.** Sin él,
  1 LSB de ruido de ADC en 45 potes le quita el instrumento al agente en
  silencio (panel §5.2, requisito 2).
- Clase de aterrizaje **por parámetro**. Ojo: esto es exactamente el campo
  nuevo del descriptor que §3.1 acaba de decir que no cabe en el byte de
  banderas —queda el bit 7 y nada más—, así que **el motor de aterrizaje
  depende del mismo hueco que la política**. La v2 lo daba por resuelto vía
  §5.2; ya no lo está.
- **Cota mano→DAC en ms, aseverada por guion.** Ya existe:
  `hardware/02-midi-cv/latencia_mano_budget.py`, y la autopista §1 la publica:
  **0,654 ms** en el peor caso a 4 kHz.
- No colisiona con `MAX_RAMPAS = 16` (`rampa.rs:24`): es su propio recurso,
  dimensionado contra 45 potes.

La v2 añadía que sin umbral, con `puerta` puesta, el ruido *«queda registrado
como si la mano lo hubiera hecho»*. Eso venía de §2.2, que está derogado. Lo
que sigue siendo cierto y es peor: **sin umbral, el ruido anula la
automatización del agente**, y eso no necesita ninguna autoría para ocurrir.

## 9. Lo que este pase NO construye

- **Ninguna máquina de estados de modos.** Un modo es una tabla.
- **Ninguna identidad criptográfica.** El emparejamiento ya existe.
- **Ninguna separación agente/carcasa.** Hoy entran por la misma puerta y el
  papel lo dice; se separa cuando se lea el nibble de cable (#182, fallo 7).
- **Ningún editor de políticas en el instrumento.** Lo hacen las carcasas.
- **Ningún ACL por parámetro individual.** Y §3.1 explica que esa prohibición
  es justamente la que deja a la tabla de autoridad sin clave: es una
  restricción con precio, no gratis.
- **Ningún modelo de navegación.** Solo «último tocado». #156 sigue vivo.
- **Ningún cambio en el panel.** #178 espera a que esto aterrice.
- **Ningún cambio de formato del cable.** Lo que necesita formato —conteo,
  terminador, largo por entrada, huella del descriptor— se decide en el pase de
  la autopista (B3, B4).

## 10. El instrumento no corre — y eso cambia qué significan §8 y §12

Esto no es un fallo de este papel, pero lo condiciona entero, así que va
escrito aquí.

`fw/src/main.rs:29-52` arranca dos tareas:

```rust
spawner.spawn(usb::correr_usb(puertos.dispositivo)...);
spawner.spawn(usb::atender(puertos.midi, instrumento)...);
```

**Ninguna llama a `tick()`, a `caducar()` ni a `confirmacion_fisica()`.** En
placa, la consecuencia es:

- **Las rampas nunca escriben.** `Instrumento::tick` (`servidor.rs:296`) es el
  único que consume `Rampas::tick`, y nadie lo llama. Todo el §5 y §6 del spec
  del tiempo musical está probado y muerto.
- **La retención nunca caduca.** `caducar` (`servidor.rs:380`) es lo único que
  vacía la cola. Cuatro `SET` a un parámetro marcado dejan `MAX_RETENIDAS = 4`
  lleno **para siempre**, y el quinto contesta `ColaLlena`
  (`servidor.rs:355`). Hoy no se nota porque ningún descriptor de producción
  lleva la bandera (§4) — o sea que el bug está tapado por el otro bug.
- **Las medidas del reloj no se publican.** El fallo 4 del #182 se arregló en
  `87e8310` y sigue sin llegar a la placa, porque su llamador no existe.
- **La confirmación física no tiene quién la dispare.** #149 y #144 legislan
  sobre un pulsador que nada lee.

**Y no se arregla añadiendo una tarea.** `main.rs:42` hace
`INSTRUMENTO.init(Instrumento::con_medidas())` y la línea 51 **mueve** ese
único `&'static mut Instrumento` a la tarea USB. No queda nada que darle a una
segunda tarea: hace falta decidir cómo se comparte —una sección crítica, un
canal de mensajes hacia el lazo USB, o mover el lazo temporal dentro de la
misma tarea con un `select`— y eso es una decisión de arquitectura del
firmware, no una línea.

**Consecuencia para la planificación:** la v2 decía «recién ahí el firmware,
con TDD». El firmware que hay que hacer primero no es el de este papel: es el
que hace que el instrumento **corra**. Este pase no puede aterrizar sobre un
firmware donde el reloj no late.

## 11. Las decisiones de Samuel

> **TOMADAS el 2026-08-24.** Lo de abajo se queda como el razonamiento que las
> produjo; esto es lo que se decidio. Los apartados que cambiaron al
> verificarlos llevan la nota.

| # | Decision | |
|---|---|---|
| **N1** | `Puerta` son **cuatro variantes sin payload**: `Mano`, `Usb`, `Inalambrica`, `Interno`. Partir `Mano` despues es anadir variantes, no rehacer. | **EN EL COBRE**, y en la ESCRITURA como manda §2.1 |
| **N2a** | Se legisla **sobre la etiqueta del mensaje**. Es la unica clave que existe, cubre los quince mensajes de cliente y cuesta cero bytes. | |
| **N2b** | **Una sola regla por puerta para todo `Set`**, y la limitacion se dice en voz alta. La ranura queda anotada como la salida barata si un caso real la pide. | |
| **N3** | La politica vive en **la flash del cerebro**. No viaja: nadie cambia permisos mandando un preset. | |
| **N4** | **Cedida a B3** de la autopista, y alli ya esta recogida con la medicion que la vuelve bloqueante. | |
| **N5** | La identidad del suscriptor **la asigna el transporte** al aceptar la conexion. Mismo patron que `puerta`: infalsificable, cero bytes de cliente. Cierra #145. | |
| **N6** | Arranque **permisivo, pero DICHO**: el estado queda legible como parametro de medida, para que un CRC malo no se disfrace de fabrica. Es B5. | |
| **N7** | La negociacion de version **se arregla ANTES de romper ningun formato**. Como B3 es una ruptura de formato, esto es el primer PR. | **EN EL COBRE** |
| **N8** | **No vuelve a junta.** Lo que la segunda produjo no fueron correcciones sino problemas abiertos, y esos se cierran decidiendo. | |

> **Aterrizado el 2026-08-24, en este orden.** N7 primero por su propia regla,
> y N1 detras porque no dependia de nadie. Con N1 en el cobre entraron tambien
> N2a (se legisla sobre la etiqueta), N2b (una regla por puerta para todo
> `Set`, con la limitacion **aseverada** por un test que exige que dos `Set`
> distintos den el mismo veredicto) y la mitad DICHO de N6 (`politica()` deja
> leer si la tabla esta vacia).
>
> Lo que queda de N3 no es decision sino cableado: la tabla vive en `core` y
> arranca vacia; leerla de la flash del cerebro es firmware, y necesita el
> driver que todavia no existe.

> **La puerta bajo a la escritura el 2026-08-24, y §2.1 tenia razon.** La
> primera pasada de N1 puso `puerta` como argumento de `atender` -- que es
> exactamente lo que este papel dice con todas sus letras que **no** se puede
> hacer: *«tiene que ser un argumento de la escritura»*. Lo cazó la junta
> adversarial, y al bajarla salieron dos cosas que estaban tapadas debajo:
>
> **1. La ley de capas decia lo contrario de lo que dice.** El codigo anulaba
> la automatizacion con *cualquier* `SET` de cliente, y lo declaraba en un
> comentario: *«El SET de un CLIENTE anula la rampa que tenga ese
> parametro»*. Pero la ley es **«la MANO gana»** (voz-total §0.2, clausula 1),
> y por USB entra el agente. O sea que el agente que automatiza y manda un
> ajuste **se anulaba a si mismo**, justo al reves de lo que la ley protege:
> que la mano capture UN parametro mientras el agente sigue con los otros
> treinta y nueve. No era implementable arriba porque `atender` no distinguia,
> y el comentario de al lado cerraba la puerta a mano: *«esa diferencia vive
> aqui, no en el modelo, que no gana ninguna puerta nueva»*.
>
> **2. Un test se quedaba vacio y seguia en verde.** `el_peor_caso_real_no_
> desborda_el_buzon` armaba su peor caso anulando dieciseis rampas con `SET`
> por USB. Con la ley corregida eso ya no anula nada, asi que el `Reactivar`
> de despues no tenia que anunciar nada y el test pasaba **sin correr el caso
> que dice medir**. Lleva una asercion en medio para que no vuelva a pasar en
> silencio.
>
> `Modelo` gana la **puerta residente** por parametro (`puerta_de`), que es el
> segundo argumento de `(puerta_entrante, puerta_residente, clase)` de §3 y
> sin el la ley de capas no era legislable. `None` mientras nadie escriba: dar
> `Mano` por defecto haria leer «capturado» sobre algo que nadie toco.
>
> **Lo que NO bajo, y por que.** El corte de politica sigue en `atender`. La
> clave de la tabla es la **etiqueta** (N2a) y en el `Modelo` no hay etiqueta,
> solo `ParamId` -- que es literalmente el problema abierto P2 de §3.2. Bajar
> el corte sin resolver P2 obligaria a inventar una clave, que es lo que §9
> prohibe por las dos vias posibles. Dicho de otra forma: la puerta baja
> porque es un dato de la escritura; la politica se queda porque su clave es
> un dato del mensaje.
>
> **Y de paso.** `set` solo miraba `solo_lectura`, asi que un descriptor
> `medida: true` que no lo declarara ademas se dejaba escribir desde el cable,
> encima de lo que el sensor acaba de medir. Hoy no hay ninguno asi en el
> arbol -- la guardia entra antes de que lo haya, que es cuando sale gratis.

> **Lo que N7 ordena.** Al decidir que ninguna ruptura entra antes que la
> negociacion funcione, el orden de trabajo queda fijado solo: primero N7
> (barato, `servidor.rs:161`), despues N1 (la unica que no depende de nadie),
> y B3 detras. No hace falta un plan aparte para saberlo.


- **N1 — El conjunto de `Puerta`.** ¿`Mano`, `Usb`, `Inalambrica`, `Interno` —
  cuatro variantes, **sin payload**— o hace falta separar `Mano` en
  panel/cabeza/pedal desde ya? *Recomendado: las cuatro sin payload.* El `u8`
  de la v2 mezclaba el eje de entrada con el de salida y se lo lleva N5;
  separar `Mano` después es añadir variantes, no rehacer. **Esta es la única
  decisión de este papel que se puede implementar sin resolver antes un
  problema abierto.**

- **N2a — ¿Sobre qué se legisla?** La v2 dio por hecho que existían clases y
  §3.1 demuestra que no hay dónde ponerlas. Las opciones reales son:
  **(a)** legislar sobre la **etiqueta del mensaje**, que ya existe
  (`etiqueta_de`, `protocolo.rs:164`), es total sobre los quince mensajes de
  cliente, nombra `Memo` y `Describe`, y cuesta cero bytes; **(b)** inventarle
  sitio a una clase, que §9 prohíbe por las dos vías posibles; **(c)** no
  legislar todavía y dejar el campo `puerta` puesto sin tabla encima.
  *Recomendado: (a).* Es la única clave que existe hoy, y hace `Memo`
  legislable, que es el caso que obliga.

- **N2b — ¿Y `Set`, que es una etiqueta sobre 536 parámetros?** Ahí es donde
  la clase haría falta de verdad, y ahí es donde no la hay. Opciones:
  **(a)** una sola regla por puerta para todo `Set`, dicho en voz alta como
  limitación; **(b)** derivar la clase de algo que el `ParamId` ya lleva — la
  **ranura** (`ParamId::ranura()`, `param.rs:60`) distingue «el cerebro» de
  «este módulo» sin campo nuevo, y agrupa por módulo por construcción;
  **(c)** el ACL por parámetro, que §9 prohíbe.
  *Recomendado: (a) ahora, con (b) anotado como la salida barata si un caso
  real lo pide.* Lo que no vale es seguir escribiendo «clases» como si
  existieran.

- **N3 — Dónde vive la política.** La EEPROM de identidad del cerebro es una
  `24AA02E48` de 256 B (`descubrimiento.rs:1`), con cabecera de 12
  (`CABECERA = 0x0C`, `descubrimiento.rs:35`) y zona libre hasta `0xFA`
  (`FIN_ZONA_LIBRE`, `descubrimiento.rs:34`): **238 bytes útiles**, y el propio
  módulo ya avisaba de para qué alcanzan y para qué no. Así que la pregunta es:
  **¿en la flash del cerebro (sobrevive al apagón, cabe) o en el preset (viaja
  con el sonido)?** *Recomendado: flash.* Una política que viaja con el preset
  se la puede cambiar quien te mande un preset — y `Preset` ya viaja con
  `autor` en el cable (`preset.rs:50`), o sea que el vector es literal.

- **N4 — El contrato del volcado del descriptor: se cede a la autopista.** La
  v2 lo planteaba como «troceado vs largo ancho». El techo de 256 B ya tiene su
  puerta y el volcado ya no aborta (§5.2); lo que falta —conteo, terminador,
  largo por entrada— es lo mismo que la autopista §3 legisla junto con la
  huella (B3) y el canal crudo (B4). *Recomendado: decidirlo allá, y que este
  papel deje de reclamarlo.* Decidir formato aquí sin saber si el descriptor se
  va a mandar casi nunca es decidir a ciegas.

- **N5 — Cómo se identifica un suscriptor que entra por `Usb`.** Es #145 y es
  el eje de salida. Hoy `suscrito: bool` y un cliente puede callar a otro sin
  error (§6). Lo que hace falta es un conjunto de suscriptores con identidad,
  y la pregunta es de dónde sale esa identidad: **(a)** la asigna el
  transporte al aceptar la conexión, mismo patrón que `puerta` —infalsificable,
  cero bytes de cliente—; **(b)** la declara el cliente en el `Hello`, que hoy
  se descarta (§11, N7). *Recomendado: (a), decidido junto con B3/B4 de la
  autopista*, porque el encaminamiento de salida y el formato del volcado se
  tocan. Y este es el mismo eje del token de petición del §7: si un `CHANGED`
  sabe a quién va, también sabe reconocer su propio eco.

- **N6 — El estado de arranque: ¿la política se carga antes de aceptar el
  primer acto?** Hoy la ventana es cero —`main.rs:42` construye el instrumento
  **antes** de montar el USB (`main.rs:48-51`)—, así que la pregunta es
  teórica. Deja de serlo en cuanto el arranque gane el barrido I²C y la lectura
  de política: ahí la ventana pasa a ser de cientos de ms, y con «tabla vacía =
  todo permitido» un CRC malo o una ranura trabada dan **acceso total y
  silencioso, indistinguible del estado de fábrica**. Es exactamente B5 de la
  autopista. *Recomendado: permisivo, pero DICHO* — el estado de arranque
  legible como parámetro de medida, para que un fallo de EEPROM no pueda
  disfrazarse de fábrica.

- **N7 — La negociación de versión, que hoy está muerta.** `servidor.rs:161`
  hace `Mensaje::Hello { .. } =>` y **descarta la versión del cliente sin
  mirarla**, aunque el docstring de `Hola` diga (`protocolo.rs:99-100`):
  *«La respuesta a `Hello`: la version que el instrumento acepta hablar. Sin
  esto la negociacion es de un solo sentido y no negocia nada»*. Este papel y
  la autopista planifican rupturas de formato apoyándose en un mecanismo que no
  funciona. *Recomendado: arreglarlo antes que cualquier cambio de formato*, y
  es barato — comparar contra `VERSION_PROTOCOLO` (`servidor.rs:28`) y
  contestar un `ERROR` con nombre si no coincide. Sin esto, la primera ruptura
  la paga el cliente en forma de basura silenciosa.

- **N8 — ¿Este papel vuelve a junta antes de tocar Rust?** *Recomendado: no
  vuelve a junta, y tampoco va a Rust todavía.* Ya fue dos veces; la segunda
  volvió con este papel entero de demolición, y lo que produjo no son
  correcciones sino **siete problemas abiertos**. Lo que sigue no es una junta
  más: es §12.

## 12. Los problemas abiertos, y lo que sigue

| # | Problema | Requisito mínimo para cerrarlo |
|---|---|---|
| **P1** | La autoría de un acto compuesto (§2.2, derogado) | Identificador de acto, no puerta heredada; y que `Rampas::empujar` deje de borrar autoría en silencio |
| **P2** | La clave de la política para `Set` (§3.1, §3.2) | Una clave nombrable desde `(etiqueta, ParamId, valor, puerta)`. N2a/N2b |
| **P3** | La identidad del acto: reconocer el eco propio (§7) | Token de petición devuelto en el `CHANGED`. Mismo eje que N5 |
| **P4** | El punto fijo con extensión vacía (§4) | Un descriptor de producción con la bandera; cerrar `publicar_medida`; declarar la inmutabilidad contra el origen |
| **P5** | #144: confirmar sin token (§4.1) | `confirmar(token)`, con fallo con nombre si ya no está vivo |
| **P6** | #145: un solo suscriptor (§6) | Conjunto con identidad. N5 |
| **P7** | El instrumento no corre (§10) | Decidir cómo se comparte el `&'static mut Instrumento` entre el lazo USB y el reloj |

**El orden, y por qué:**

1. **P7 primero.** Nada de lo demás se puede probar en placa mientras el reloj
   no lata. Y es el único que no depende de ninguna decisión de este papel.
2. **N7** —la negociación de versión— porque es barato y porque todo lo que
   viene después rompe formato.
3. **N1**, que es implementable ya: el enumerado `Puerta` y estamparlo en el
   transporte, con `puerta` bajando hasta las tres escrituras del `Modelo`
   (§2.1) y no hasta `atender`. Con TDD, los tests primero.
4. **P5 y P4**, que son los dos que convierten reglas escritas en reglas con
   sujeto, y los dos son locales.
5. **N2a/N2b**, que es donde este papel deja de ser mecanismo y empieza a ser
   política. No antes: legislar sobre una clave que no existe fue el error de
   la v2.
6. **N5 con B3/B4 de la autopista**, en el mismo pase, porque es el mismo eje.
7. **P1, P2 y P3** siguen abiertos y **no tienen fecha**. Este papel los deja
   escritos con sus requisitos en vez de maquillarlos, que es la única forma de
   que la próxima versión no vuelva a cerrarlos por decreto.
8. Recién después, **#178** (el módulo de mandos) contra un contrato ya firme.
