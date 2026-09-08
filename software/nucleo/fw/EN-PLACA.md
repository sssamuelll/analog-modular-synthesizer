# La lista del bring-up

Esto se escribió **sin placa**. Todo lo que hay en `core` está probado con
`cargo test`, y el binario compila y enlaza para `thumbv8m.main-none-eabihf`
—el target del Cortex-M55 del N657, el mismo que traía el RP2350— pero eso no
demuestra que arranque, ni que enumere, ni que conteste.

Esta es la lista del día que llegue la placa, **en orden**: cada línea supone
que la anterior salió bien.

## Antes de enchufar nada

**Cuál placa.** La STM32N6570-DK (#231). Lleva el mismo
STM32N657X0H3Q en VFBGA264 que eligió el censo, y además la pantalla de
800×480 en el LTDC y la PSRAM, que es por lo que se pidió ésa y no la Nucleo.

**Comprobar `memory.x` contra la placa.** El N657 **no tiene flash interna**:
`FLASH` y `RAM` son dos tramos de la misma AXISRAM2 y el binario se carga ahí
por el USB serial de la ROM. El arranque de verdad —FSBL y binario firmado
desde la XSPI— es el riesgo 2 del papel del hub y **no está hecho**: enlazar
aquí no demuestra que arranque de la flash.

**Comprobar de dónde sale el núcleo.** `usb::configuracion()` pone
`SupplyConfig::External` porque la DK lleva SMPS externo; con el interno el
`init` se queda colgado en `VOSRDY`. **La placa del SAM17 lleva el conmutado
interno** (papel de alimentación del N657), así que esa línea se borra el día
que exista placa propia. Si el arranque se cuelga sin decir nada, éste es el
sospechoso número uno.

**Comprobar el pinout.** `core/src/pinout.rs` es una **propuesta**: los números
salieron de agrupar por periférico, no de ninguna placa. Cuando haya una, ese
es el único fichero que cambia — para eso está aislado y para eso tiene tests
que impiden repetir un pin o pedir uno que no existe.

## 1. Arranca

```bash
cargo run --release          # probe-rs con el STLINK-V3EC de la placa
```

**`--release` no es una preferencia: es la unica que enlaza.** Con
`defmt` y embassy, el binario de depuracion se pasa **48 KB** de los 256 K que
`memory.x` reserva para el codigo, y `rust-lld` lo dice con tres secciones que
se solapan. Si hace falta depurar sin optimizar, se sube `FLASH` en
`memory.x` — pero entonces los 768 KB de abajo dejan de ser contiguos y el
framebuffer de 800x480 pierde su banco.

Por `defmt` tiene que salir:

```
SAM17: el cerebro arranco, protocolo v1
39 pines en el mapa
sin descubrimiento todavia: 27 parametros, todos de medida
```

**Si no sale nada**, en orden: la configuración de alimentación (arriba), y
después el reloj de referencia del PHY de USB, que tiene que ser 24 MHz
exactos y sale de PLL4 → IC15 (`usb::configuracion()`, con la cuenta y su
página). Enlazar no es arrancar.

## 2. Enumera

El sistema operativo lo ve como dispositivo MIDI con nombre **SAM17 nucleo**,
VID `0x1209` y PID `0x0017`.

## 3. `HELLO` da la vuelta

**Este es el momento en que el instrumento contesta de verdad por primera vez.**
Manda el SysEx de `HELLO` y espera `HOLA { version: 1 }`.

El sobre es `F0 7D <datos empaquetados a 7 bits> F7`, y el mensaje son la
etiqueta `0x01` más la versión en `u16` little-endian. El troceo en paquetes
de 4 bytes lo hace el driver MIDI del sistema.

## 4. `DESCRIBE` vuelve entero

Tienen que llegar **27 sobres**, uno por parámetro: las 24 bandas de Bark, el
pico, su exceso y la sonoridad. Con sus nombres y sus unidades.

Si llegan menos, sospecha del troceo largo antes que del servidor: 27 sobres
seguidos es lo primero que ejercita el buffer de verdad.

## 5. Un `SET` sobre una medida contesta `ERROR`

Manda `SET` a cualquier banda. Tiene que volver
`ERROR { etiqueta: 0x04, codigo: SoloLectura }`.

**Este es el test del hallazgo**: antes de añadir `ERROR` a la tabla, esto
dejaba al cliente esperando en silencio para siempre.

## 6. `SUBSCRIBE` y luego un `SET` que sí valga

Con `SUBSCRIBE` activo, un `SET` correcto tiene que devolver su `CHANGED`.
Sin `SUBSCRIBE`, **no** devuelve nada, y eso es a propósito: si no, girar una
perilla dispararía cientos de acks por segundo.

## El tiempo musical, cuando haya reloj que enchufar

**Umbrales del CLOCK IN.** `tiempo_budget.py` despeja **993 µs** de holgura
para detectar el flanco. Es muchísimo, así que lo raro sería fallarlo — pero
hay que medirlo, no suponerlo.

**Niveles del CLOCK OUT.** TTL, 0 V / ~+5 V (§5.3 del núcleo).

**MIDI clock por USB de verdad.** El seguidor está probado contra ±2 ms de
jitter inyectado; falta ver cuánto tiembla el transporte real.

**Link sobre el puente**, que necesita que el puente exista y esté elegido. Y
cuando toque: **no escribir el protocolo desde cero** — existe
`ableton-link-rs`, y hay precedente de la topología exacta (Link en un ESP32
pasándole la sesión a un RP2350 por SPI).

## Lo que queda anotado para más adelante

**VID/PID de verdad.** `0x1209` es pid.codes, el rango libre para proyectos
abiertos, y `0x0017` es un PID de pruebas que nadie asignó. Registrar uno es
del día que esto se distribuya.

**Todo lo demás de #86** — I²C, J2, el jitter del 74HC14 contra los 131 ns
(que en el N657 mide captura de TIM, no PIO), DIN, clock/reset, pedal, USB
host — va en los planes 2 y 3. Ese issue está escrito contra el RP2350 y hay
que reescribirlo contra esta placa.

**El J2 no está aquí.** El driver `j2_spi.rs` y su ejecutor son la fase B del
plan del maestro del J2, y lo que los bloqueaba era este pase (#250). La
política ya vive en `core/src/maestro_j2.rs`, probada en el host.
