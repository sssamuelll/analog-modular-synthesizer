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

Lo que sí cumple, clase **Intel N100 / N150** (Alder Lake-N):

| | |
|---|---|
| RAM | **DDR5-4800 SO-DIMM**, ampliable |
| Disco | **2× M.2 NVMe** PCIe 3.0 |
| Alimentación | **12 V DC**, entrada ancha 12–19 V |
| TDP | **6 W**, disipación pasiva |
| CPU | 4 núcleos, hasta 3.4–3.6 GHz |

Lo pasivo no es un detalle: **un ventilador dentro de un instrumento es ruido**,
acústico y eléctrico. Era el problema que traía el Pi 5 bajo carga sostenida.

Y x86 abre lo que en un Pi nunca fue realista: **DAWs de verdad** — Reaper,
Bitwig, Ardour corren nativos en Linux x86.

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

## 4. El agente de IA

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

## 5. Qué placa hacemos nosotros

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

## 6. Lo que NO está confirmado

1. **La placa x86 concreta no está elegida.** Los números de arriba son de la
   clase N100/N150 en general. Hay que fijar modelo, y comprobar que su entrada
   de 12 V y su disipación pasiva aguantan **dentro de una caja cerrada** con el
   calor de los reguladores lineales al lado.
2. **El consumo real bajo carga de audio** no está medido. 6 W es el TDP del
   chip, no el del sistema con NVMe y DDR5 trabajando.
3. **La latencia del audio por USB** no está medida y decide si los efectos
   sobre las voces analógicas son usables.
4. **El protocolo micro ↔ máquina** no está definido. MIDI es lo obvio para
   notas y reloj; para el resto (patches, calibración, agente) hace falta algo
   más y no está decidido si es MIDI SysEx, serie con un protocolo propio, o USB.
5. Nada de esto está medido. Son hojas de datos y arquitectura.
