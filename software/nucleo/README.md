# `nucleo` — el contrato del SAM17

Esto **no es el firmware**. Es el contrato del que cuelgan la app, el agente,
el MCP y la pantalla: el modelo de parámetros, su protocolo, y los dos motores
de análisis. Todo `no_std`, todo verificable con `cargo test` en tu máquina,
sin una sola placa de por medio.

```bash
cd software/nucleo
cargo test
cargo clippy --all-targets -- -D warnings
```

Spec: [`docs/superpowers/specs/2026-08-17-nucleo-digital-design.md`](../../docs/superpowers/specs/2026-08-17-nucleo-digital-design.md).
Plan: [`docs/superpowers/plans/2026-08-17-nucleo-contrato.md`](../../docs/superpowers/plans/2026-08-17-nucleo-contrato.md).

## Por qué está partido en dos

El alcance del firmware de validación (§8 de la spec) se parte solo:

| | Este crate | El plan siguiente |
|---|---|---|
| Qué es | El contrato y sus motores | El bring-up sobre placa |
| Se verifica con | `cargo test`, hoy | Analizador lógico, EEPROM en protoboard, DAW |
| Necesita | Nada | Una RP2350, y hierro que aún no existe |

§9 ya lo tenía escrito así: casi todas sus filas dicen *«tests en host, Rust
puro»*. Las que dicen protoboard o analizador se van al siguiente.

El binario vive en [`fw/`](fw) y **es un workspace aparte**, no un segundo
miembro de este. Una versión anterior de este README decía lo contrario y
estaba mal: los dos compilan para targets distintos, y en Rust estable no hay
forma de decir «este paquete siempre va a este target» (`forced-target` es de
nightly). Con los dos en el mismo workspace, `cargo test` aquí intentaría
compilar el firmware para tu máquina. De ahí el `exclude = ["fw"]`.

```bash
cd software/nucleo/fw
cargo build --release          # thumbv8m.main-none-eabihf, ya en .cargo/config.toml
```

## Los módulos

| Módulo | De qué responde |
|---|---|
| `param` | §3.1 direccionamiento, §3.2 valores |
| `descriptor` | §3.3 descriptor, §3.4 marcas de medida, §3.6 ámbito, y su códec |
| `modelo` | El estado vivo: la única puerta |
| `retencion` | §2.2 operaciones retenidas y confirmación física |
| `protocolo` | §4.1 los 19 mensajes y su códec |
| `sysex` | Empaquetado de 7 bits y sobre SysEx (§4.4) |
| `j2` | La trama de 72 bits del contrato congelado |
| `descubrimiento` | §3.5 EEPROM y catálogo, §3.6 conteo de voces |
| `partes` | §3.6 partes y reparto de voces |
| `preset` | §6.1 presets y topología del patch |
| `perturbacion` | §7.6 códigos ortogonales y correlación |
| `atribucion` | §7.2 los dos niveles |
| `medidas` | §7.3 las bandas perceptuales como parámetros |

## Los tres formatos de cable

Todos de **ancho fijo y little-endian**, a propósito: los va a parsear el
puente inalámbrico y JavaScript en la UI web, y un `DataView` tiene que poder
leerlos sin librerías. Por eso no hay `serde` ni varints.

### El descriptor

```text
  off  tam  campo
   0    2   id (u16)
   2    1   banderas
              bit0 solo_lectura   bit1 medida   bit2 confirmacion_fisica
              bit3 ambito (0 = compartido, 1 = por-voz)
              bits 4-5 tipo (0 continuo, 1 enumerado, 2 booleano)
   3    4   min (i32)
   7    4   max (i32)
  11    4   def (i32)
  15    1   unidad
  16    1   largo del nombre
  17    n   nombre en UTF-8
       1   numero de etiquetas
       por etiqueta: 1 byte de largo + los bytes UTF-8
```

### El protocolo

Bit alto de la etiqueta puesto = va del instrumento al cliente.

| Byte | Mensaje | | Byte | Mensaje |
|---|---|---|---|---|
| `0x01` | `HELLO` | | `0x81` | `CHANGED` |
| `0x02` | `DESCRIBE` | | `0x82` | `MODULES` |
| `0x03` | `GET` | | `0x83` | `TUNE_PROGRESS` |
| `0x04` | `SET` | | `0x84` | `JACKS` |
| `0x05` | `SUBSCRIBE` | | `0x85` | `PENDING` |
| `0x06` | `PRESET_LIST` | | `0x86` | `RESOLVED` |
| `0x07` | `PRESET_LOAD` | | | |
| `0x08` | `PRESET_SAVE` | | | |
| `0x09` | `TUNE_START` | | | |
| `0x0A` | `PATCH_SCAN` | | | |
| `0x0B` | `TELEMETRY` | | | |
| `0x0C` | `POINT` | | | |
| `0x0D` | `MEMO` | | | |

**Esta tabla es la superficie completa del instrumento.** Por §2.1 no puede
haber capacidad fuera de ella, y la guardia no es un test: el `match` de
`etiqueta()` es exhaustivo, así que un mensaje nuevo sin codificar no compila.

### La EEPROM de identidad

```text
  0x00  1  magia = 0x17
  0x01  1  version de la cabecera = 1
  0x02  2  tipo de placa (u16 LE)
  0x04  1  revision
  0x05  1  largo del blob de calibracion
  0x06  4  serial (u32 LE)
  0x0A  2  crc16 de 0x00..0x0A (CCITT-FALSE)
  0x0C  n  blob de calibracion
```

## Tres decisiones que la spec dejaba abiertas

1. **Fuera de rango se rechaza, no se recorta.** Recortar en silencio le miente
   al agente, que creería haber puesto 500. La excepción son las medidas, donde
   recortar es correcto porque no es la intención de nadie: es un sensor, y
   tirar la trama entera sería peor.
2. **El pulsador confirma la más reciente**, no una cola. En escena hay una
   operación pendiente. Y `confirmar()` **salta** lo vencido sin tirarlo, para
   que `caducar()` pueda anunciarlo: si lo descartara, un token moriría sin que
   ningún cliente se entere.
3. **Property Exchange está partido.** El transporte —empaquetado de 7 bits y
   sobre SysEx con el ID de fabricante no comercial `0x7D`— vive aquí y está
   probado. La conformidad MIDI-CI (MUID, `ResourceList`, los nombres exactos
   de la cabecera) va en el plan del binario, y su primer paso es leer el
   M2-103-UM de la MIDI Association, no escribirlo de memoria.

## Lo que sigue sin verificar contra fuente primaria

Dos cosas, y las dos están marcadas en el código donde tocan:

- **La tabla de comandos del AD5686R** (`j2.rs`). El PDF de Analog no abre
  desde el entorno de desarrollo. Lo que sí está confirmado va citado con su
  fuente en la cabecera del módulo. De paso: el firmware moribundo del módulo 2
  se contradice —su docstring dice comando `0011` y sus constantes valen
  `0001`— y aquí se usa `0011` a propósito.
- **La zona del EUI-48 del 24AA02E48** (`descubrimiento.rs`). `FIN_ZONA_LIBRE`
  es una cota conservadora mientras tanto.

Las constantes de los dos motores (`GANANCIA_MINIMA`, `CONFIANZA_MINIMA`,
`TOL_CENTS`, `MARGEN`) salen de razonar los casos, no de medir hardware. Los
tests fijan **el comportamiento exigido** —recupera lo que se puso, declara
ambiguo lo que no se puede saber— y las constantes son la perilla para
cumplirlo. Cuando llegue el hierro se vuelven a mirar contra señales reales;
los tests no.
