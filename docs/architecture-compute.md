# Arquitectura de cómputo del SAM17

Cómo se reparte el trabajo digital del instrumento. Complementa a
[`architecture-poly.md`](architecture-poly.md), que describe la parte analógica.

---

## 1. El cerebro va partido, y la computadora se queda FUERA

El instrumento entero vive en un **microcontrolador**. La computadora es
**opcional, externa, y puede ser cualquiera**.

```
   ┌────────────────────────────────┐         ┌───────────────────────┐
   │  EL INSTRUMENTO — RP2350       │   USB   │ CUALQUIER COMPUTADORA │
   │  Rust bare-metal, sin SO       │◄───────►│ la tuya, con TU DAW   │
   │                                │  MIDI   │ y TUS plugins         │
   │  · reparto de 4 voces          │   DIN   │                       │
   │  · CV en serie a cada módulo   │         │  · efectos, sampler   │
   │  · 4 gates                     │         │  · el VST compañero   │
   │  · autoafinado                 │         │  · el agente de IA    │
   │  · secuenciador, arpegiador    │         │                       │
   │  · reloj y sync                │         │  OPCIONAL             │
   └────────────────────────────────┘         └───────────────────────┘
        arranca en milisegundos                  enchúfala si quieres
        TOCA SIN NADA MÁS
```

**El instrumento está completo sin computadora.** Cuatro voces, secuenciador,
arpegiador, afinado automático y USB. Todo lo demás es lujo, no requisito.

Y si mañana enchufas una y esa se cae en mitad de un concierto, **el instrumento
sigue sonando** — porque nunca dependió de ella.

### Lo que esta decisión resuelve de un plumazo

- **El problema de los plugins.** En Linux hay poquísimo soporte comercial: u-he,
  Bitwig, Reaper y poco más. Con la computadora fuera usas la tuya, con Windows
  si quieres, y tienes **todos** tus plugins sin pelear con Wine ni con iLok.
- **Todo el trabajo de cómputo embebido.** Elegir procesador, envolvente
  térmica, fuente aparte, ventilador, imagen mínima de Linux: nada de eso hace
  falta hoy.
- **El instrumento se puede fabricar mucho antes.**

## 2. El camino de una nota

1. **Entra MIDI** por USB o DIN al micro.
2. **El micro reparte la voz**: la que esté libre, o roba la más vieja. Ahí vive
   la polifonía, en software.
3. **Nota → voltaje.** No hay fórmula: **busca en una tabla, y hay una por
   voz**, porque cada VCO tiene su propia personalidad. Saca el código de 16
   bits y lo manda por el enlace serie al DAC — **que vive en la placa del
   VCO**, no aquí (architecture-poly §8).
4. **El DAC da 0–2.5 V**, el amplificador lo lleva a **0–7 V** con ganancia
   2.8, y llega al VCO de esa voz **sin salir de la placa** — por eso el
   suelo de afinación baja de 1.71 a 0.58 cents.
5. **En paralelo sube el gate** — 10 V a la envolvente de esa voz.
6. **VCO → su filtro → su VCA** (que abre según envolvente y velocity) → mixer
   con las otras tres.

El **mixer va al final**. Sumar antes del filtro sería parafónico, no
polifónico, y esa es literalmente la diferencia entre los dos.

## 3. El autoafinado, que corre por debajo

Cada VCO lleva un **74HC14** que recorta su onda y manda un **pulso lógico** al
micro. El **PIO del RP2350** mide el periodo **por hardware** de los cuatro a la
vez, compara con la frecuencia que debería tener esa nota y corrige la tabla.

**84 notas × 4 voces en 3.5 s**, en silencio — el VCO siempre oscila y el gate
está cerrado.

Esto mata el problema de fondo del analógico: el conversor exponencial se corre
**−0.33 % por grado**. Sin esto calientas la caja y te desafinas; con esto se
corrige solo.

## 4. La interfaz: USB estándar, y DIN cuando importa

Como la computadora puede ser **cualquiera**, el enlace tiene que ser
**class-compliant**: MIDI USB sin drivers, en Windows, Mac, Linux o un iPad.
Igual que cualquier sinte de hardware, y por eso todos funcionan con la DAW de
todo el mundo. El RP2350 hace USB nativo.

**Y también hace de host, a la vez.** Sin eso, el «toca sin nada más» del §1
sería mentira en 2026: casi todo controlador moderno es USB-only, así que un
instrumento que solo es *device* necesita una computadora para que le toques.
Con `Pico-PIO-USB` sobre PIO —verificado funcionando en paralelo con el USB
nativo— le enchufas el teclado directo. De paso el instrumento se vuelve un
**hub MIDI**: tu teclado entra, se mezcla con su secuenciador, y sale hacia el
DAW.

**MIDI 2.0 ya no es futuro**: Windows MIDI Services salió con driver de clase y
UMP nativo, y todos los DAW grandes tienen implementación. Aquí se sube por
escalones —MIDI 1.0 primero, el alternate setting de 2.0 después— porque
**Property Exchange, que es lo que de verdad hace falta, funciona igual en los
dos**.

> Esto **sustituye** al módulo de kernel en Rust (`/dev/sam17`) que figuraba en
> la versión anterior. Un módulo de kernel solo sirve en Linux; si la
> computadora puede ser cualquiera, la interfaz tiene que ser estándar. La idea
> no muere: es lo que se escribe **el día que se meta una computadora dentro**.

**Y una trampa que hay que decir:** el USB trae la masa de la computadora —una
fuente conmutada, con su ruido— metida en el instrumento. Lazo de tierra de
manual.

**El MIDI DIN no tiene ese problema**: el estándar exige optoacoplador desde
1983, precisamente por eso. Está aislado galvánicamente por diseño.

Así que **USB para comodidad, DIN para grabar en serio**, o un aislador USB en
medio.

## 5. El VST compañero

Un plugin propio (CLAP + VST3) que vive dentro de tu DAW:

- **Editor y librería**: patches, la tabla de afinación a la vista, diagnóstico
  voz por voz
- **Botón de afinar**: dispara el autoafinado sin salir de la sesión
- **El agente de IA**

### Por qué plugin y no aplicación aparte

**Los patches se guardan CON el proyecto.** Abres una sesión de hace seis meses
y el instrumento se reconfigura solo. Eso los sintes de hardware no lo hacen, y
es la diferencia entre tener un sinte y tenerlo integrado.

Además el host ya te da el MIDI enrutado al instrumento: sin drivers y sin
pelear puertos.

### Y algo del estándar que lo regala a medias

**Property Exchange ya hace parte de esto sin que escribamos nada.** Logic 10.6+
muestra automáticamente los controles del instrumento que le publica su
descriptor **y guarda esa configuración en el fichero de proyecto**. O sea, el
argumento de arriba —«los patches se guardan con el proyecto»— lo cumple el
estándar. El plugin propio sirve para lo que el estándar no cubre: la librería,
el diagnóstico voz por voz, el patcheo guiado y el agente.

### Con qué: una sola UI en tres carcasas

Hay tres sitios donde mostrar lo mismo —el VST, la app standalone y el teléfono—
y escribirlos tres veces sería meses de trabajo duplicado. Así que **la interfaz
se escribe una vez, como aplicación web**, y las tres carcasas la montan:

```
              UI WEB (una sola)
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
   VST (USB)   standalone      teléfono (WiFi)
```

La pila existe y está probada: **WRAC** (WebView + Rust Audio + CLAP), liberada
por NovoNotes en mayo de 2026 con más de 15 000 usuarios en producción, con
`clap-wrapper` para salir también como VST3/AU y el crate `wxp` sobre `wry` para
el IPC. Sigue dejando el proyecto en **Rust en el micro y Rust en la carcasa**.

`nih-plug` y JUCE quedan como alternativas si WRAC no aguanta la prueba.

### La trampa técnica

**El hilo de audio no puede bloquearse.** El MIDI está bien —el host pasa un
buffer por bloque— pero **la llamada al LLM tarda segundos**: va en un hilo
aparte, con una cola sin locks hacia el hilo de audio. Es práctica estándar y es
justo donde la gente se estrella.

## 6. El agente de IA

**El LLM es remoto**: el instrumento no corre modelos, se llama a una API. Corre
en la computadora que haya, así que **puede cambiar sin tocar un tornillo**.

Se reutiliza lo ya resuelto en `projects/aurelius`:

| Pieza | Qué aporta |
|---|---|
| `brain/openai_compat.py` | cliente HTTP compatible con OpenAI, streaming SSE, bucle de herramientas, timeouts |
| `brain/factory.py` `FallbackBrain` | *latch* a un segundo proveedor si el primero falla |
| `organism/capability.py` | contrato declarativo de herramientas |
| `events.py` | audit en JSONL con elisión de contenido |

Se **adapta** la capa de autoridad (`authority_core.py`, mandatos con TTL,
denylist de irreversibles): el modelo por origen es portable, pero aurelius
confirma **de viva voz** y aquí la confirmación tiene que ser **física** — un
botón o un pedal. Esa capa importa porque **un agente que puede reconfigurar tu
instrumento necesita la misma contención que uno que puede borrar ficheros**.

Falta por escribir: **cliente MCP** (aurelius es servidor, no cliente —
verificado, cero `ClientSession`) y, si se quiere voz, **la ruta HTTP de STT**,
que `speechtotext` no tiene.

### El puente que hace barato todo esto

**MCP y MIDI-CI Property Exchange resuelven el mismo problema en dos mundos**, y
la correspondencia es casi literal: `ResourceList` es `tools/list`, y
`Get`/`Set Property Data` es `tools/call`. Los dos son JSON auto-descriptivo.

Hoy los servidores MCP para sintes son de dos tipos, y ninguno cierra esto: los
genéricos mandan números de CC que el modelo no sabe interpretar, y los
específicos traen el mapa de parámetros escrito a mano, aparato por aparato
(hay uno para el MicroFreak, otro para el Axe-Fx…). **No se encontró evidencia
de que nadie haya puenteado los dos estándares.**

Un instrumento que hable Property Exchange **se gana un servidor MCP genérico**,
sin mapa a mano, y que además funciona con módulos que no existían cuando se
escribió el agente. Por eso los nombres y las unidades de cada parámetro no son
cosmética: son la documentación que el modelo va a leer.

Y la contraparte obligatoria: si el agente alcanza todo, la contención tiene que
ser real. **Qué operaciones exigen confirmación física lo declara el
instrumento, no el cliente** — si lo decidiera el cliente, bastaría con un
cliente que no pregunte.

## 7. Qué placa hacemos nosotros

**Una: la del instrumento.**

**RP2350B** (QFN-80, 48 GPIO — el A de 30 no da: el conteo sale a ~37) con:

| | |
|---|---|
| Enlace serie | Un **J2 por módulo, en estrella** hacia sus DAC, digipots, mux de perillas y sensado de jacks (architecture-poly §8; direccionamiento cerrado en el issue #34) |
| Mux I²C de 8 canales | Todas las EEPROM de identidad responden en 0x50 y chocarían en un bus compartido |
| 4 gates · 4 entradas de afinado | Las voces. El afinado por **PIO**, las cuatro a la vez |
| **USB de doble rol** | Puerto nativo como *device* hacia tu computadora, **y host por PIO-USB** para enchufarle un controlador. A la vez |
| **MIDI DIN in/out** | Con optoacoplador. Es el único aislado por norma |
| **Clock y reset**, in/out | Sync analógico. Sin esto el secuenciador no toca con nadie |
| **Jack de pedal** | Confirmación física del agente, y expresión |
| Cadena WS2812 | Un pin de datos encadena los LEDs de todos los paneles |
| Cabeza local | 4 dígitos + un encoder con pulsador + LEDs de estado |
| Zócalo del puente inalámbrico | Módulo pre-certificado por UART, no chip de RF soldado |
| Las dos masas separadas | Como siempre |

**Y no lleva entrada de audio.** Esta placa manda números, no voltajes — los DAC
viven en el módulo que los consume, y **la medida del sonido también**: el
módulo 4 oye por ella con un códec de 24 bits y le manda números por el mismo
J2. Menos analógico en el cerebro = menos que rutear y menos que pueda
ensuciarse.

Consecuencia buena que no se buscaba: cambiar la cabecera de 40 pines del Pi, el
LCD de 16×2 y los cuatro pulsadores por **un QFN** deshace el atasco de ruteo
que dejó 17 redes al aire en el módulo 2 (issue #22) — un QFN-80 de 10×10 mm
sigue siendo minúsculo al lado de aquello.

> Detalle completo y los porqués:
> [`superpowers/specs/2026-08-17-nucleo-digital-design.md`](superpowers/specs/2026-08-17-nucleo-digital-design.md).

## 8. Lo que se consideró y se descartó

Se deja escrito para no volver a discutirlo, y por qué:

| Idea | Por qué no |
|---|---|
| **Raspberry Pi / CM5 dentro** | Sin DDR5 (usa LPDDR4X soldada). Y arranca en 30 s |
| **x86 Ryzen dentro** | Un Ryzen 9 de escritorio son 105 W dentro de la caja, y **el calor es el enemigo de la afinación**: el conversor exponencial se corre −0.33 %/°C. No es que no quepa, es que sabotea el instrumento |
| **Módulo de kernel en Rust** | Solo sirve en Linux. Si la computadora puede ser cualquiera, la interfaz tiene que ser estándar |
| **Sistema operativo propio** | Reimplementar USB, ficheros, pantalla y red. Años, y ni una nota de música |
| **Un DAW propio** | Décadas de trabajo para competir con lo que ya usas — y no produce una canción que no pudieras hacer ya |

Ninguna está muerta para siempre: el día que se meta una computadora dentro,
vuelven a la mesa el x86 y el módulo de kernel. Pero **hoy no hacen falta**, y el
corte del cerebro es lo que permite decidirlo después.

## 9. Lo que NO está confirmado

### Cerrado el 2026-08-17

Tres de los cinco puntos que vivían aquí ya están decididos, con la evidencia en
la [spec del núcleo digital](superpowers/specs/2026-08-17-nucleo-digital-design.md):

1. **La pantalla.** Va **cabeza mínima local** —4 dígitos, un encoder con
   pulsador, LEDs de estado— más la **pantalla inalámbrica** en tu teléfono. Sin
   menús: escribir nombres con un encoder es tortura y el teléfono lo hace
   mejor; la cabeza local hace lo que el teléfono hace peor, que es estar
   siempre ahí sin batería ni red. Y el pulsador del encoder resultó ser el
   botón de confirmación física que el agente necesitaba.
2. **El protocolo por encima del MIDI.** Va **MIDI-CI / Property Exchange sobre
   SysEx**, que funciona igual en MIDI 1.0 y en MIDI 2.0 — verificado. Con eso
   el instrumento publica su propia lista de parámetros en JSON, y **el servidor
   MCP sale casi gratis** porque `ResourceList` es `tools/list`. MIDI 2.0 queda
   como segundo escalón (alternate setting 1), no como bifurcación.
3. **El plugin.** Se escribe **una sola UI web en tres carcasas** —VST,
   standalone y teléfono— en vez de tres interfaces. La pila existe y está
   probada: **WRAC** (WebView + Rust Audio + CLAP), liberada en mayo de 2026 con
   15 000+ usuarios en producción. `nih-plug` deja de ser la elección por
   defecto.

Y desde el **2026-08-17** los tres dejaron de ser diseño y pasaron a ser código
con tests: el modelo de parámetros, el descriptor, el protocolo y el
empaquetado SysEx viven en [`software/nucleo/`](../software/nucleo), `no_std` y
verificados con `cargo test` — sin una placa de por medio. El descriptor
completo viaja en SysEx y vuelve idéntico, que era justo lo que el punto 2
prometía.

Y desde el mismo día **el instrumento contesta**: el servidor del protocolo
está escrito y el binario compila para RP2350 hablando USB-MIDI. Al escribirlo
salió que la tabla de §4.1 dejaba al cliente en silencio ante un `HELLO`, ante
un `DESCRIBE` y ante **todo `SET` rechazado** — así que la tabla creció con
`HOLA` y `ERROR`. Falta placa para comprobarlo: la lista está en
`software/nucleo/fw/EN-PLACA.md`.

### Sigue abierto

1. **El aislamiento del USB** no está medido. Que el DIN esté aislado por norma
   es un hecho; cuánto ruido mete el USB en la práctica, no.
2. **La escalera de C a Rust.** Las pilas probadas de USB MIDI 2.0 (`tusb_ump`)
   y de USB host (`Pico-PIO-USB`) son C. Ninguna de las dos está en el camino
   crítico —el instrumento funciona sin ellas— pero hay que decidir si se hace
   FFI o se escribe en Rust.
3. Lo demás sigue siendo hojas de datos y arquitectura, no medidas nuestras.
