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
   │  · 8 CV por SPI (2x DAC)       │         │  · efectos, sampler   │
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
   bits y lo manda por SPI al DAC.
4. **El DAC da 0–2.5 V**, el amplificador lo lleva a **0–7 V** con ganancia 2.8,
   y sale por el bus al VCO de esa voz.
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

### Con qué

**`nih-plug` (Rust)** — exporta CLAP y VST3, con GUI por egui/iced/VIZIA. El
plugin es casi todo interfaz y MIDI, **casi nada de DSP**, que es justo donde
Rust está cómodo y donde el ecosistema de C++ no compra tanto. Y deja el
proyecto en **un solo lenguaje: Rust en el micro, Rust en el plugin**.

JUCE (C++) queda como alternativa si algún día hace falta DSP pesado o AU en Mac.

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

## 7. Qué placa hacemos nosotros

**Una: la del instrumento.**

RP2350 · 2× AD5686R encadenados (8 CV: 4 de tono + 4 de velocity) · 4 gates ·
4 entradas de afinado digitales · MIDI DIN in/out con optoacoplador · USB ·
pantalla pequeña con encoders · las dos masas separadas

Consecuencia buena que no se buscaba: cambiar la cabecera de 40 pines del Pi, el
LCD de 16×2 y los cuatro pulsadores por **un QFN pequeño** deshace el atasco de
ruteo que dejó 17 redes al aire en el módulo 2 (issue #22).

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

1. **La pantalla del instrumento** — se propone pantallita con encoders, para
   poder afinar y elegir patch sin depender de ninguna computadora. **Sin
   confirmar**: modelo, tamaño, y si lleva encoders o pulsadores.
2. **El protocolo por encima del MIDI.** Notas y reloj son MIDI estándar; para
   patches, tabla de afinación y agente hace falta algo más, y no está decidido
   si es SysEx o serie propia por USB.
3. **`nih-plug`** no se ha probado en este proyecto. Existe, exporta CLAP y VST3
   y tiene plugins en uso real, pero eso es lo que dice su documentación, no una
   medición nuestra.
4. **El aislamiento del USB** no está medido. Que el DIN esté aislado por norma
   es un hecho; cuánto ruido mete el USB en la práctica, no.
5. Nada de esto está medido. Son hojas de datos y arquitectura.
