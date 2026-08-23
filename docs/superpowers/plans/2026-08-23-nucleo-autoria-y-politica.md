# El pase del núcleo: quién escribe, y qué se le permite

**Estado: PROPUESTA.** No toca cobre ni firmware todavía. Cierra —o encamina—
seis issues que resultaron ser el mismo paciente: #172, #177, #159, #145,
#144 y #149.

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

## 2. El mecanismo: `origen` en la puerta, no en el cable

`atender(&mut self, m: Mensaje, ahora_ms: u64) -> Respuestas` es **la única
puerta** del instrumento (modelo.rs: *«si algo muta el instrumento sin pasar
por aquí, el agente no lo alcanza»*). Ahí entra el campo:

```
atender(&mut self, m: Mensaje, origen: Origen, ahora_ms: u64) -> Respuestas
```

**`origen` NO viaja en el mensaje. Lo estampa el transporte que lo recibió.**
Esa es la decisión de diseño que hace todo lo demás barato:

- Un cliente **no puede mentir sobre quién es**, por construcción — no hay
  campo que falsificar; su origen es la puerta por la que entró.
- **Cuesta cero bytes en el cable.** El formato del protocolo no cambia por
  esto (sí cambia por §5, que es otra cosa).
- Es exactamente el patrón que `del_instrumento()` ya usa, generalizado.

Los orígenes propuestos, cortos a propósito:

| `Origen` | Quién es | Puerta |
|---|---|---|
| `Mano` | panel de mandos, encoder de la cabeza, pulsador, pedal | J2 del módulo de mandos, GPIO de la cabeza |
| `Agente` | el agente por MCP | transporte emparejado |
| `Carcasa(u8)` | app, VST, web — el `u8` es la suscripción, no una identidad criptográfica | USB, puente inalámbrico |
| `Interno` | el tick, las rampas, la carga de preset | llamada interna |

**The Cut:** ni criptografía, ni identidad fuerte del agente, ni tokens por
cliente. El emparejamiento ya existe (voz-total §0.2, cláusula 2) y basta.

## 3. La política: una tabla, y vacía por defecto

Reglas `(origen, qué)` → permitido. **Tabla vacía = todo permitido.** Ese es
el estado de fábrica, y es el que Samuel dice que va a usar: *«yo igual voy a
terminar dando acceso total al agente»*.

- El «qué» son **clases**, no 536 filas: `tocar` (parámetros de
  interpretación), `rutear` (aristas de la bahía), `preset`, `calibrar`,
  `firmware`. Empezar por clases y bajar a parámetro **solo si algún día hace
  falta** — hoy no hace falta.
- **Un modo es una política guardada con nombre.** «Live», «ejecución»,
  «exploración» son filas, no código. Cambiar de modo es cargar otra tabla.
  Firmware: cero máquinas de estado, cero transiciones que mantener.
- **Se borra.** Sin política, el instrumento se comporta como hoy.

Y aquí la consecuencia bonita: **la ley de capas deja de ser doctrina
inexpresable y pasa a ser la fila por defecto** — «`Mano` escribe un
parámetro ⇒ la automatización sobre ese parámetro queda `ANULADO`». Escrita
como dato, se puede leer, se puede apagar, y se puede discutir. Voronov:
*«mientras la autoría no sea un objeto de primera clase, "la mano gana" no es
una ley: es una cortesía»*. Con esto es una fila, y una fila sí es una ley.

## 4. Lo que `origen` cierra de regalo

| Issue | Qué le pasa |
|---|---|
| **#159** | Es el campo que pidió. Y se le suma **«último tocado, con su origen»** — lo que el renglón del panel necesita para escribir nombre y valor. **NO** se construye el modelo de navegación completo (eso es #156 y sigue prohibido por el spec del cerebro) |
| **#144** | `Retenida { token, id, valor, vence_ms }` gana `origen`, y `confirmar()` deja de ser «la más reciente que siga viva» para exigir que coincida. Una confirmación física deja de ser *«un consentimiento a lo que sea que esté encima de la pila»* |
| **#149** | La polaridad del pedal gana una fila: solo la escribe `Mano`. La recursión se rompe sin sacar el parámetro del modelo, porque **la mano tiene otra puerta**: el encoder de la cabeza. Se arregla el pedal sin el pedal |
| **#145** | `suscrito: bool` pasa a conjunto con identidad. Es prerrequisito de `CHANGED` con destinatario, y `Carcasa(u8)` ya trae el índice |
| **#177** | Es este papel |

## 5. Los techos, que hay que romper igual (#172)

Nada de lo anterior sirve si el modelo no puede publicarse, y hoy no puede.
Halberg: *«hoy ninguna carcasa puede renderizar este módulo»*. Tres cotas
verificadas en cobre:

| Cota | Hoy | Necesita | Cambio |
|---|---|---|---|
| `modelo.rs: MAX_PARAMS = 512` | 536 parámetros censados | subir, con su cuenta de RAM | 2 |
| `descubrimiento.rs`: largo de blob en **1 byte**, techo efectivo por `FIN_ZONA_LIBRE = 0xFA` | descriptor de ~25 KB | largo ancho, o troceado declarado | 18 |
| `servidor.rs: MAX_RESPUESTAS = 4` | un giro de perilla «por programa» son 16 `CHANGED` | dimensionar contra el gesto real | nuevo |

**Se hacen en el mismo pase, y no por comodidad:** el formato hay que
romperlo para el cambio 18, y los campos nuevos de §2 y §6 viven en el mismo
formato. Abrir al paciente dos veces sería tonto.

## 6. El motor de aterrizaje (el salto suave de Samuel)

A3 del panel quedó firmada en la sensación y derogada en el mecanismo:
`rampa.rs` trabaja en **pulsos musicales cuantizados** (`inicio: u64` *«ya
viene cuantizado por la rejilla»*, `duracion: u32` *«en pulsos»*), así que el
mismo planeo duraría 3× más a 60 BPM que a 180. Requisitos del motor nuevo,
que es **otro objeto**, no una rampa:

- Milisegundos de pared, no pulsos. Sin cuantizar.
- **Umbral de gesto en LSB con histéresis, declarado y aseverado.** Sin él,
  1 LSB de ruido de ADC en 45 potes le quita el instrumento al agente en
  silencio — y con `origen` puesto, encima queda registrado como si la mano
  lo hubiera hecho.
- Clase de aterrizaje **por parámetro** (campo nuevo del descriptor, §5) y
  por política (§3).
- **Cota mano→DAC en ms, aseverada por guion.** Hoy no existe ninguna en el
  repo; «inmediato» sin número no es falsable.
- No colisiona con `MAX_RAMPAS = 16`: es su propio recurso, dimensionado
  contra 45 potes.

## 7. Lo que este pase NO construye

- **Ninguna máquina de estados de modos.** Un modo es una tabla.
- **Ninguna identidad criptográfica.** El emparejamiento ya existe.
- **Ningún editor de políticas en el instrumento.** Lo hacen las carcasas.
- **Ningún ACL por parámetro individual.** Clases; se baja de granularidad
  el día que un caso real lo pida.
- **Ningún modelo de navegación.** Solo «último tocado». #156 sigue vivo.
- **Ningún cambio en el panel.** #178 espera a que esto aterrice, justamente
  para no escribirse contra un contrato que va a cambiar.

## 8. Las decisiones de Samuel

- **N1 — El conjunto de `Origen`:** ¿los cuatro de §2, o hace falta separar
  `Mano` en panel/cabeza/pedal desde ya? (Recomendado: cuatro. Separar
  después es añadir variantes, no rehacer.)
- **N2 — Las clases de la política:** ¿tocar / rutear / preset / calibrar /
  firmware, o otro corte?
- **N3 — Dónde vive la política:** ¿en la EEPROM del cerebro (sobrevive al
  apagón, y ya hay 128 KB) o en el preset (viaja con el sonido)? Recomendado:
  **EEPROM** — una política que viaja con el preset se la puede cambiar quien
  te mande un preset.
- **N4 — El descriptor troceado vs largo ancho** (cambio 18): decide cuánto
  duele el arranque (`arranque_budget.py`, que tampoco existe todavía).
- **N5 — ¿Este papel va a junta antes de tocar Rust?** Recomendado: sí, con
  Halberg y Voronov — Halberg porque los techos son suyos, Voronov porque él
  cazó el hueco.

## 9. Lo que sigue

Aprobado esto: (1) junta; (2) el spec del núcleo v2 con el formato nuevo y
los tests que lo cierran; (3) el firmware, con TDD — los tests primero, y
`check_censo_voz.py` volviendo a verde como criterio de aceptación; (4)
recién ahí, #178 (el módulo de mandos) contra un contrato ya firme.
