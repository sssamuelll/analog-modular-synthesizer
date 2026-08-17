# La lista del bring-up

Esto se escribió **sin placa**. Todo lo que hay en `core` está probado con
`cargo test`, y el binario compila y enlaza para `thumbv8m.main-none-eabihf`
— pero eso no demuestra que arranque, ni que enumere, ni que conteste.

Esta es la lista del día que llegue la placa, **en orden**: cada línea supone
que la anterior salió bien.

## Antes de enchufar nada

**Comprobar `memory.x` contra la placa.** `LENGTH` de FLASH es de la placa, no
del chip: **2048K** es lo que trae una Pico 2, y el RP2350 soporta hasta 16 MB
por QSPI (§10 de la spec). La SRAM sí es del chip: 520 kB, de los que `memory.x`
declara 512K.

**Comprobar el chip contra la feature.** El crate va por defecto a `rp235xb`
—el que la spec §5.3 obliga por conteo de pines—. Si la placa lleva el A:

```bash
cargo build --release --no-default-features --features rp235xa
```

**Comprobar el pinout.** `core/src/pinout.rs` es una **propuesta**: los números
salieron de agrupar por periférico, no de ninguna placa. Cuando haya una, ese
es el único fichero que cambia — para eso está aislado y para eso tiene tests
que impiden repetir un pin o pedir uno que no existe.

## 1. Arranca

```bash
cargo run --release          # con probe-rs, o arrastrar el UF2
```

Por `defmt` tiene que salir:

```
SAM17: el cerebro arranco, protocolo v1
38 pines en el mapa
sin descubrimiento todavia: 27 parametros, todos de medida
```

**Si no sale nada**, el sospechoso número uno es el `ImageDef` de
`.start_block`: la ROM del RP2350 no ejecuta una imagen sin él, y tiene que
caer en los primeros 4 K de flash. Enlazar no es arrancar.

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

## Lo que queda anotado para más adelante

**VID/PID de verdad.** `0x1209` es pid.codes, el rango libre para proyectos
abiertos, y `0x0017` es un PID de pruebas que nadie asignó. Registrar uno es
del día que esto se distribuya.

**Todo lo demás de #86** — I²C, J2, PIO y el jitter del 74HC14 contra los
131 ns, WS2812, DIN, clock/reset, pedal, USB host — va en los planes 2 y 3.
