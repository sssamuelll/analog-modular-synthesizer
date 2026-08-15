# Arquitectura de cómputo del SAM17

Cómo se reparte el trabajo digital del instrumento. Complementa a
[`architecture-poly.md`](architecture-poly.md), que describe la parte analógica.

---

## 1. El cerebro va partido en dos, y no es una preferencia

Le estábamos pidiendo a un solo chip dos trabajos con requisitos **opuestos**:

| | Necesita | Un Linux es… |
|---|---|---|
| CV, gates, autoafinado | temporización determinista de microsegundos | **malo** — no hay tiempo real duro |
| Secuenciador, efectos, UI, agente | CPU, RAM, disco, pantalla | **bueno** — y un micro es malísimo |

Así que van separados y hablan por MIDI/serie:

```
   ┌──────────────────────────────┐        ┌───────────────────────────┐
   │  TIEMPO REAL — RP2350        │  MIDI  │  LA MÁQUINA — x86         │
   │  Rust bare-metal, sin SO     │◄──────►│  Linux, DDR5, NVMe        │
   │                              │  serie │                           │
   │  · reparto de voces          │        │  · secuenciador, patrones │
   │  · 8 CV por SPI (2x DAC)     │        │  · efectos y sampler      │
   │  · 4 gates                   │        │  · UI táctil              │
   │  · medida de afinado x4      │        │  · AGENTE DE IA (API      │
   │  · reloj y sync              │        │    remota, no local)      │
   │  · secuenciador básico       │        │  · grabación a NVMe       │
   └──────────────────────────────┘        └───────────────────────────┘
            │  arranca en ms                        │  arranca en ~20 s
            ▼                                       ▼
      el instrumento TOCA                     la máquina llega después
```

Tres cosas que compra el corte, y las tres importan:

**El instrumento toca aunque el Linux esté arrancando o colgado.** Enciendes y
das una nota. No esperas medio minuto. Para un instrumento esto es lo que más
pesa de todo este documento.

**Desaparece el número más flojo del autoafinado.** Todo el presupuesto colgaba
de un jitter de 5 µs anotado como *«de manual, no medido»*. El PIO del RP2350
hace captura de periodo por hardware: determinista y sub-microsegundo.

**La elección de la máquina pasa a ser reversible.** Con el corte hecho puedes
cambiar el x86, meter otro, o pilotarlo desde un portátil, **sin tocar el
instrumento**. Esa es la propiedad que hay que proteger.

## 2. El lado de tiempo real: RP2350 en Rust

**Rust bare-metal, sin sistema operativo.** El HAL está estable (`embassy-rp` /
`rp235x-hal`), implementa `embedded-hal` 1.0 y soporta async y bloqueante.
Raspberry Pi publicó ella misma sobre Rust en RP2350: no es terreno
experimental.

Por qué Rust y no C aquí: el núcleo de un instrumento **no puede fallar a mitad
de una actuación**, y Rust elimina por construcción la clase de fallo que en C
aparece a las tres horas de concierto.

Lo que corre aquí es el **nivel 0** completo — todo lo que hace falta para que
esto sea un instrumento sin ninguna máquina detrás:

secuenciador por pasos polifónico · arpegiador · quantizador de escala · memoria
de acordes · reloj MIDI maestro y esclavo · LFOs y envolventes extra como CV ·
matriz de modulación · memoria de patches · autoafinado

## 3. El lado máquina: x86, no Raspberry

**Ningún Raspberry tiene DDR5.** El Pi 5 y el CM5 usan **LPDDR4X-4267**, soldada
y no ampliable. Con DDR5 y NVMe como requisitos, la familia entera queda fuera —
no por opinión, por hoja de datos.

Lo elegido: **Ryzen 9 móvil de última generación**, clase
**Ryzen AI 9 HX 470** (Gorgon Point, Zen 5):

| | Ryzen 9 5900X (la máquina de desarrollo) | **Ryzen AI 9 HX 470** |
|---|---|---|
| Núcleos / hilos | 12 / 24 | **12 / 24** (4 Zen 5 + 8 Zen 5c) |
| Reloj | 3.7 → ~4.8 GHz | 2.0 → **5.2 GHz** |
| TDP | **105 W** | **15–54 W configurable**, base 28 |
| RAM | DDR4-2666 | **DDR5-5600 SO-DIMM**, hasta 128 GB |
| Disco | — | PCIe 4, **2× M.2 NVMe** |

Mismo número de núcleos que el 5900X, dos generaciones de arquitectura por
delante, y **a una cuarta parte del consumo**.

### El calor es el enemigo de la afinación

Este es el criterio que manda al elegir el procesador, y no es el consumo por el
consumo.

Todo el sistema de autoafinado existe porque el convertidor exponencial del VCO
se desvía **−0.33 % por cada grado centígrado**. Un procesador de escritorio de
105 W dentro de la misma caja **no es que no quepa: sabotea el instrumento**,
peleando justo contra lo que se diseñó para corregirlo.

Por eso la regla es: **el cómputo va abajo, con su propio camino térmico hacia
fuera, y lo más lejos posible de las placas analógicas.** El case de dos pisos
da exactamente ese sitio.

### El TDP configurable es una perilla, no una decisión

Los **15–54 W** del HX 470 se ajustan por firmware. Eso convierte
«prepararlo para que sea potente» en algo literal:

- **15 W** → silencioso, para tocar
- **54 W** → toda la potencia, para renderizar o procesar

**La envolvente se diseña para 54 W y se corre a 15 mientras se toca.** No es un
compromiso, es un ajuste.

### La envolvente que hay que reservar

| | |
|---|---|
| Potencia | 54 W de CPU + NVMe + RAM ≈ **75–90 W de sistema**. Fuente propia |
| Térmica | camino de disipación al exterior, en el piso inferior |
| Espacio | placa formato mini-PC, del orden de 105 × 105 a 130 × 130 mm |

Reservando eso entra cualquier cosa desde un N100 hasta el HX 470, así que la
elección concreta del chip **deja de ser irreversible**.

Sobre el ventilador: **uno dentro de un instrumento es ruido**, acústico y
eléctrico. A 15 W se puede llevar en pasivo o con un ventilador grande y lento,
que es prácticamente inaudible — los que se oyen son los pequeños a muchas
revoluciones. A 54 W hace falta activo, y por eso ese modo es para renderizar,
no para tocar.

Y x86 abre lo que en un Pi nunca fue realista: **DAWs de verdad** — Reaper,
Bitwig, Ardour corren nativos en Linux x86.

Un apunte para no comprar de más: **la latencia de audio en Linux la decide
sobre todo el kernel** (compilado con `PREEMPT_RT`), no el procesador. Una
máquina modesta bien configurada late mejor que una bestia mal configurada.

### Lo que el cambio a x86 obliga a mover

| | Con Pi | **Con x86** |
|---|---|---|
| Pantalla | DSI | **HDMI + táctil por USB** — más barato y sin límite de tamaño |
| Audio | códec I2S | **interfaz USB** class-compliant, o tarjeta M.2 |
| GPIO | 40 pines | **ninguno** — y da igual: los tiene el micro |
| Alimentación | 5 V | **12 V propios**, ~1.5 A |

Lo del GPIO merece decirse al derecho: x86 no tiene, y eso **no es una pérdida**
porque el corte del §1 ya había puesto todo lo de tiempo real en el micro. La
máquina no necesita tocar un solo pin.

### Alimentación: separada, y no es negociable

El x86 va con **su propia fuente de 12 V**, nunca colgado de los rieles de
audio. Un ordenador es una carga conmutada de 15–20 W: metida en los ±12 V del
instrumento inyectaría ruido justo donde el presupuesto de masa dice que no
puede haberlo (1.21 cents es el suelo del instrumento). Misma regla que ya
aplicaba al Pi (módulo 1 §3).

## 4. Rust en el kernel: dónde sí y dónde no

El instrumento se maneja **a nivel de kernel con Rust**. Pero hay una frontera
real y conviene tenerla clara antes de escribir una línea.

### Lo que está maduro (finales de 2026)

| Abstracción | Estado |
|---|---|
| **misc device** | dentro. Greg Kroah-Hartman las llamó *«el punto de inflexión»* |
| **char device** con `ioctl` | dentro |
| registro de dispositivos **USB** | dentro |
| drivers **HID** | desde marzo de 2026 |
| PCI, plataforma, DMA, DRM | dentro o en curso |

### Lo que NO existe

**ALSA no tiene abstracción en Rust.** El subsistema de sonido sigue siendo C, y
no hay nada en curso que lo cambie a corto plazo.

Eso no es un obstáculo, es una señal de dónde poner el esfuerzo.

### Dónde va nuestro módulo: el enlace del instrumento

**`/dev/sam17` — un char device en Rust para el canal micro ↔ máquina.**

Es el sitio correcto por tres razones, y ninguna es «porque mola»:

1. **Es exactamente la abstracción que está madura.** Char device con `ioctl` es
   de lo primero que se estabilizó en Rust for Linux.
2. **Es la frontera del sistema.** Todo lo que quiera hablar con el instrumento
   —el secuenciador, la DAW, el agente de IA— pasa por ahí. Un solo driver
   contra media docena de programas reimplementando manejo de puerto serie cada
   uno.
3. **Se beneficia de vivir en el kernel.** El transporte deja de sufrir el
   jitter del planificador de espacio de usuario, y con `PREEMPT_RT` se integra
   con la planificación de tiempo real como corresponde.

Lo que el módulo expone: apertura de canal, envío y recepción de mensajes hacia
el micro, y `ioctl` para lo que no es flujo — estado de calibración, patches,
modo. El formato de esos mensajes es el protocolo del §7, que sigue sin definir.

### El audio NO va en el kernel

Va con el **driver USB audio class que ya existe** (en C, probado, y funciona),
y el DSP en **espacio de usuario** con prioridad de tiempo real sobre un kernel
compilado con `PREEMPT_RT`.

Escribir un driver de audio en Rust hoy significaría crear la abstracción de
ALSA entera antes de escribir una sola línea útil. Eso es un proyecto de kernel,
no un proyecto de instrumento.

### Lo que cuesta, dicho por delante

- **Un módulo va atado a la versión del kernel.** Cada actualización puede pedir
  ajustes. Es mantenimiento permanente, no un «se escribe y ya».
- **Las abstracciones incompletas se pagan en `unsafe`.** Donde no llega el
  binding hay que bajar a FFI a mano, y ahí Rust deja de protegerte.
- **Depurar en el kernel es mucho más duro** que en espacio de usuario, y un
  fallo se lleva la máquina entera por delante — aunque Rust reduce mucho esa
  clase de fallo, que es justamente el argumento para usarlo.

## 5. El agente de IA

**El LLM es remoto.** El instrumento no corre modelos: llama a una API. Eso
mantiene el cómputo local en lo que de verdad necesita — red, un runtime
decente y disco.

La arquitectura ya está resuelta en `projects/aurelius` y se reutiliza. Lo que
se toma **tal cual**:

| Pieza | Qué aporta |
|---|---|
| `brain/openai_compat.py` | cliente HTTP compatible con OpenAI, streaming SSE, bucle de herramientas con tope de 5 rondas, timeouts |
| `brain/factory.py` `FallbackBrain` | *latch* a un segundo proveedor: si el primero falla, no vuelve en ese turno. En un escenario sin red esto es infraestructura, no lujo |
| `organism/capability.py` | contrato declarativo de herramientas |
| `events.py` | audit en JSONL con elisión de contenido: los textos largos se guardan como puntero con hash |
| patrón `modo.state` / `modo.request` | fichero JSON atómico como bus de estado **entre procesos** — sirve tal cual para el canal micro ↔ máquina |

Lo que hay que **adaptar**: la capa de autoridad (`authority_core.py`, mandatos
con TTL, denylist de irreversibles). El modelo por origen es portable, pero
aurelius confirma **de viva voz** — un «dale» hablado. En un instrumento eso no
vale: **la confirmación pasa a ser física**, un botón o un pedal.

Y merece decirse por qué esa capa importa aquí: un agente que puede reconfigurar
tu instrumento necesita exactamente la misma contención que uno que puede borrar
ficheros.

Dos cosas que **no** están y hay que construir:

1. **Cliente MCP.** Aurelius es servidor MCP, no cliente (verificado: cero
   `ClientSession` en su código). Si el agente del instrumento debe consumir
   servidores MCP externos, esa pieza se escribe.
2. **STT remoto.** `speechtotext` transcribe por CLI local con faster-whisper y
   su API solo hace `/health` y `/score`. Si el instrumento responde a voz, la
   ruta HTTP hay que crearla.

## 6. Qué placa hacemos nosotros

**La del micro, y solo la del micro.**

Una placa base para DDR5 son ocho capas o más, con pares diferenciales,
adaptación de longitudes y control de impedancia. Eso no se diseña como
extensión de un proyecto de sintetizador: **el x86 se compra montado**.

La placa del cerebro en cambio es abordable y es lo siguiente que toca:

RP2350 · 2× AD5686R encadenados (8 CV) · 4 salidas de gate · 4 entradas de
afinado (ahora digitales, sin mux ni acondicionado) · MIDI DIN in/out · USB ·
serie hacia la máquina · las dos masas separadas

Y trae una consecuencia buena que no se buscaba: sustituir la cabecera de 40
pines del Pi, el LCD y los cuatro pulsadores por **un QFN pequeño** deshace el
atasco de ruteo que dejó 17 redes al aire en el módulo 2 (issue #22). El lado
digital estaba congestionado precisamente por esas piezas.

## 7. Lo que NO está confirmado

1. **La placa concreta no está elegida**, solo la clase. Hay que fijar modelo y
   comprobar la entrada de continua, y sobre todo **medir la temperatura dentro
   de la caja cerrada** con los reguladores lineales al lado.
2. **El consumo real bajo carga de audio** no está medido, y el TDP es del chip,
   no del sistema con NVMe y DDR5 trabajando.
3. **A qué TDP se puede correr en pasivo** dentro de la caja: es lo que decide
   si tocar es silencioso. Hay que medirlo, no suponerlo.
3. **La latencia del audio por USB** no está medida y decide si los efectos
   sobre las voces analógicas son usables.
4. **El protocolo micro ↔ máquina** no está definido. MIDI es lo obvio para
   notas y reloj; para el resto (patches, calibración, agente) hace falta algo
   más y no está decidido si es MIDI SysEx, serie con un protocolo propio, o USB.
   Es lo que expone `/dev/sam17` (§4), así que bloquea al módulo de kernel.
5. **Contra qué versión de kernel se fija el módulo** no está decidido, y no es
   menor: un módulo fuera del árbol se rompe con las actualizaciones.
6. Nada de esto está medido. Son hojas de datos y arquitectura.
