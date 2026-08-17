# El binario arranca y habla — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el contrato deje de ser piezas sueltas y pase a ser un instrumento que contesta: un servidor de protocolo completo, el empaquetador USB-MIDI que lo lleva por el cable, y el binario que los envuelve — compilando para RP2350 y con toda la lógica verificada en `cargo test`, sin placa.

**Architecture:** Todo lo que se pueda probar sin hierro vive en `software/nucleo/core` (la biblioteca que ya existe). El binario `software/nucleo/fw` es una **capa delgada**: `embassy-rp` + `embassy-usb` bombeando bytes hacia funciones puras que ya vinieron verdes. Es un workspace aparte porque compila para otro target.

**Tech Stack:** Rust 1.95 estable, `embassy-rp` 0.10 (`rp235xb`), `embassy-usb` 0.6, `embassy-executor` 0.10, `embassy-time` 0.5, `defmt` 1.1, target `thumbv8m.main-none-eabihf`.

**Spec:** `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md`
**Plan anterior:** `docs/superpowers/plans/2026-08-17-nucleo-contrato.md` (mergeado, #85)
**Issue:** #86

---

## El hallazgo que hay que decidir antes de escribir código

Al ir a escribir el servidor apareció esto, y es más grande que una tarea:

> **La tabla de mensajes de §4.1 deja al cliente en silencio en tres casos, y
> uno de ellos es un fallo de verdad.**

| Situación | Qué recibe el cliente hoy | Por qué importa |
|---|---|---|
| `HELLO` — *«identificarse y negociar versión»* | **Nada.** No hay respuesta en la tabla | Una negociación de un solo sentido no negocia. Un cliente v2 contra un instrumento v1 no sabe que tiene que bajar |
| `DESCRIBE` | **Nada.** El descriptor no cabe en ningún mensaje de la tabla | Es el mensaje del que cuelga todo lo demás |
| `SET` sobre solo-lectura, fuera de rango, o inexistente | **Nada.** `ErrorSet` se queda dentro del micro | El agente escribe, no pasa nada, y no sabe por qué. Ese es el peor modo de fallo del diseño entero |

Por §2.1 —*«ninguna capacidad puede existir fuera del modelo y su protocolo»*—
esto no se arregla con una convención: se arregla **añadiendo a la tabla**, que
es literalmente lo que esa sección dice que hay que hacer.

**Lo mínimo que lo cierra son dos mensajes y una respuesta que no es mensaje:**

| | Qué | Por qué así |
|---|---|---|
| `HOLA` (`0x87`) | instrumento → cliente, lleva la versión acordada | Misma forma que `HELLO`, tag propio para no romper el invariante de «bit alto = dirección» |
| `ERROR` (`0x88`) | instrumento → cliente: qué etiqueta falló y por qué | Un protocolo sin mensaje de error está roto, y este ya tenía los códigos escritos (`ErrorSet`) sin manera de mandarlos |
| `Respuesta::Descriptores` | no es un mensaje: es la orden de volcar la tabla empaquetada en su propio sobre | El descriptor es de largo variable y grande. Meterlo en `Mensaje` obligaría a darle vida (`Mensaje<'a>`) y eso ripplea a todo el códec |

**Task 2 lo implementa y actualiza la spec.** Si prefieres otra forma, es el
momento — después son tres carcasas y un servidor MCP.

---

## Global Constraints

- **`no_std` sin excepciones**, en las dos cajas.
- **El invariante de §2.1**: nada fuera de la tabla de mensajes. Si una tarea
  necesita una capacidad nueva, primero crece la tabla.
- **Ningún cliente se queda en silencio.** Toda petición produce respuesta:
  la que pedía, o un `ERROR` que dice por qué no.
- **El agente jamás en el camino de audio** (§7.1). Aquí ni aparece, pero la
  capa de IO no puede bloquear esperando a nadie.
- **`fw` es delgado a propósito.** Si una función del binario merece un test,
  es que vive en la caja equivocada: se muda a `core`.
- **`MAX_VOCES` es capacidad, ningún `4` de voces** (§3.6). Vale también aquí.
- **Gates:** en `software/nucleo` → `cargo test` verde y
  `cargo clippy --all-targets -- -D warnings` limpio. En `software/nucleo/fw` →
  `cargo build --release --target thumbv8m.main-none-eabihf` sin avisos y
  `cargo clippy --target thumbv8m.main-none-eabihf -- -D warnings` limpio.
  Y los cinco `*_budget.py` del repo siguen verdes.
- **Nombres y comentarios en español.** Los nombres que ve el agente se
  escriben para alguien que nunca ha visto el instrumento.
- Commits en español contando el porqué, con el trailer de coautoría del repo.

## Lo que este plan NO hace

Nada que necesite tocar un periférico de verdad: I²C, SPI del J2, PIO de
afinado, WS2812, MIDI DIN, clock/reset, pedal y USB host van al **plan 2** (los
periféricos) y al **plan 3** (los puertos al mundo y el USB de doble rol). Las
filas de #86 que dicen «analizador lógico» o «protoboard» son de esos.

Y **no hay placa todavía**, así que ninguna tarea cierra en «funciona en
hardware». Cierran en dos cosas que sí son verificables hoy: *la lógica pasa sus
tests* y *el binario compila y enlaza para el target*. Cada tarea que además
tenga algo que comprobar en placa lo deja escrito en `fw/EN-PLACA.md` (Task 6),
que es la lista con la que se hace el bring-up el día que llegue.

---

### Task 1: El andamio del binario y el pinout

**Files:**
- Create: `software/nucleo/fw/Cargo.toml`, `fw/.cargo/config.toml`,
  `fw/rust-toolchain.toml`, `fw/build.rs`, `fw/memory.x`, `fw/src/main.rs`
- Create: `software/nucleo/core/src/pinout.rs`
- Modify: `software/nucleo/Cargo.toml`, `core/src/lib.rs`, `README.md`

**Interfaces:**
- Produces: `pinout::{Pin, PINOUT, N_PINES_USADOS}` en `core` — la tabla que
  `fw` consume. Y un binario que enlaza para `thumbv8m.main-none-eabihf`.

**Por qué `fw` es un workspace aparte, y la corrección que trae.** El README
del contrato dice que el binario entra *«como segundo miembro del mismo
workspace»*. **Está mal y hay que arreglarlo**: los dos miembros compilan para
targets distintos, y en Rust estable no hay forma de decir «este paquete
siempre va a este target» (`forced-target` es de nightly). Con los dos en el
mismo workspace, `cargo test` en la raíz intentaría compilar el firmware para
Windows y reventaría. Así que `fw` lleva su propio `[workspace]` y el padre lo
excluye. El README se corrige en esta tarea.

**El pinout vive en `core` y no en `fw`, y también tiene su razón:** es un dato
con invariantes que se pueden probar —que ningún pin esté asignado dos veces—
y probarlo en `fw` obligaría a tests en el target. Es exactamente el criterio
de la constraint: *si merece un test, vive en `core`*.

- [ ] **Step 1: Instalar el target y comprobar que existe**

```bash
rustup target add thumbv8m.main-none-eabihf
rustup target list --installed
```
Esperado: `thumbv8m.main-none-eabihf` en la lista. Es el de Cortex-M33 con FPU,
que es lo que lleva el RP2350.

- [ ] **Step 2: Excluir `fw` del workspace del contrato**

`software/nucleo/Cargo.toml`:

```toml
[workspace]
resolver = "2"
members = ["core"]
# `fw` compila para thumbv8m y `core` para el host. En estable no hay
# `forced-target`, asi que compartir workspace haria que `cargo test` en la
# raiz intentara compilar el firmware para tu maquina.
exclude = ["fw"]
```

- [ ] **Step 3: Escribir el test del pinout, que falla**

En `core/src/pinout.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ningun_gpio_esta_asignado_dos_veces() {
        // El fallo mas caro y mas silencioso del firmware embebido: dos
        // perifericos peleandose un pin. Aqui cuesta un test.
        for (i, a) in PINOUT.iter().enumerate() {
            for b in PINOUT.iter().skip(i + 1) {
                assert_ne!(a.gpio, b.gpio, "{} y {} comparten GPIO{}", a.para, b.para, a.gpio);
            }
        }
    }

    #[test]
    fn todos_caben_en_el_rp2350b() {
        // §5.3: el B da 48 GPIO. El A da 30 y por eso no sirve.
        for p in PINOUT.iter() {
            assert!(p.gpio < 48, "{} pide GPIO{}, y el B llega a 47", p.para, p.gpio);
        }
    }

    #[test]
    fn el_conteo_confirma_por_que_no_cabia_en_el_a() {
        // §5.3 cuenta ~37 GPIO y de ahi sale la obligacion del B. Si este
        // numero bajara de 31, la spec habria que revisarla.
        assert_eq!(N_PINES_USADOS, PINOUT.len());
        assert!(N_PINES_USADOS > 30, "con {N_PINES_USADOS} pines el A habria bastado");
    }

    #[test]
    fn las_entradas_analogicas_son_de_las_que_existen() {
        // El B trae 8 (GPIO40..47). Pedir una que no existe no compila en
        // `fw`, pero falla aqui antes y con un mensaje que se entiende.
        for p in PINOUT.iter().filter(|p| p.analogico) {
            assert!((40..48).contains(&p.gpio), "{} no es una entrada analogica", p.para);
        }
    }
}
```

- [ ] **Step 4: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core pinout`
Esperado: FAIL, `cannot find value PINOUT`.

- [ ] **Step 5: Escribir el pinout**

Arriba en `core/src/pinout.rs`. Los números son **una propuesta**, no un dato
verificado contra ninguna placa —no hay placa— pero respetan lo que sí manda:
`SPI0` y `I2C0` en pines donde el RP2350 los tiene, y las analógicas en 40-47.

```rust
//! La asignación de pines del cerebro (§5.3), en un solo sitio.
//!
//! Está aquí y no en `fw` porque es un dato con invariantes que se prueban:
//! que ningún pin esté asignado dos veces, y que todos existan en el chip.
//! Probarlo en `fw` obligaría a correr tests en el micro.
//!
//! **Estos números son una propuesta.** No hay placa contra la que
//! verificarlos; cuando la haya, se cambia este fichero y nada más. Esa es la
//! razón de que exista.

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Pin {
    pub gpio: u8,
    pub para: &'static str,
    /// Si tiene que caer en una entrada del ADC (§5.3: el pedal de expresión).
    pub analogico: bool,
}

const fn d(gpio: u8, para: &'static str) -> Pin {
    Pin { gpio, para, analogico: false }
}
const fn a(gpio: u8, para: &'static str) -> Pin {
    Pin { gpio, para, analogico: true }
}

pub static PINOUT: &[Pin] = &[
    // J2 — el mazo digital. Contrato congelado por el módulo 3.
    d(2, "J2 SCLK"),
    d(3, "J2 MOSI"),
    d(4, "J2 MISO"),
    // Un CS por ranura: módulos 3, 4, 5, 6, 7 y los futuros 8 y 9, más repuesto.
    d(5, "J2 CS ranura 1"),
    d(6, "J2 CS ranura 2"),
    d(7, "J2 CS ranura 3"),
    d(8, "J2 CS ranura 4"),
    d(9, "J2 CS ranura 5"),
    d(10, "J2 CS ranura 6"),
    d(11, "J2 CS ranura 7"),
    d(12, "J2 CS ranura 8"),
    // I²C hacia el mux de 8 canales (§3.5).
    d(0, "I2C SDA"),
    d(1, "I2C SCL"),
    // Afinado: los cuatro TUNE_OUT al PIO (§5.1).
    d(13, "TUNE_OUT 1"),
    d(14, "TUNE_OUT 2"),
    d(15, "TUNE_OUT 3"),
    d(16, "TUNE_OUT 4"),
    // Gates al ADSR.
    d(17, "GATE 1"),
    d(18, "GATE 2"),
    d(19, "GATE 3"),
    d(20, "GATE 4"),
    // La cadena de LED direccionables: un solo pin de datos (§6.2).
    d(21, "WS2812 datos"),
    // MIDI DIN, con su optoacoplador (§5.3).
    d(22, "DIN in"),
    d(23, "DIN out"),
    // Sync analógico. El reset va como parámetro, no cableado (§5.3).
    d(24, "CLOCK in"),
    d(25, "CLOCK out"),
    d(26, "RESET in"),
    d(27, "RESET out"),
    // El zócalo del puente inalámbrico (§4.2).
    d(28, "UART puente TX"),
    d(29, "UART puente RX"),
    // La cabeza local (§5.2). Su pulsador ES la confirmación física de §2.2.
    d(30, "encoder A"),
    d(31, "encoder B"),
    d(32, "encoder pulsador"),
    d(33, "dígitos: datos"),
    d(34, "dígitos: reloj"),
    d(35, "dígitos: latch"),
    // USB host sobre PIO (§5.3). Los dos pines van juntos y consecutivos.
    d(36, "PIO-USB D+"),
    d(37, "PIO-USB D-"),
    // El pedal. Analógico para que sirva también de expresión (§5.3).
    a(40, "pedal"),
];

pub const N_PINES_USADOS: usize = 38;
```

- [ ] **Step 6: Verlo pasar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy --all-targets -- -D warnings`
Esperado: 4 tests nuevos PASS. Añade `pub mod pinout;` a `core/src/lib.rs`.

- [ ] **Step 7: El crate del firmware**

`software/nucleo/fw/Cargo.toml`:

```toml
[package]
name = "sam17-nucleo-fw"
version = "0.1.0"
edition = "2021"
description = "El firmware del cerebro del SAM17 sobre RP2350"

[workspace]

[dependencies]
sam17-nucleo-core = { path = "../core" }
embassy-rp = { version = "0.10", features = ["rp235xb", "time-driver", "critical-section-impl", "defmt"] }
embassy-executor = { version = "0.10", features = ["arch-cortex-m", "executor-thread", "defmt"] }
embassy-time = { version = "0.5", features = ["defmt"] }
embassy-usb = { version = "0.6", features = ["defmt"] }
embassy-futures = "0.1"
defmt = "1.1"
defmt-rtt = "1.0"
panic-probe = { version = "1.0", features = ["print-defmt"] }
cortex-m = { version = "0.7", features = ["inline-asm"] }
cortex-m-rt = "0.7"
static_cell = "2"

[features]
default = ["rp235xb"]
rp235xb = ["embassy-rp/rp235xb"]
# Para validar sobre una Pico 2, que lleva el A. Cambia el chip, no el codigo.
rp235xa = ["embassy-rp/rp235xa"]

[profile.release]
debug = 2
lto = true
opt-level = "s"
```

> **Al escribirlo, comprueba los nombres de las features contra
> `https://docs.rs/embassy-rp/0.10.0/` y `https://docs.rs/embassy-usb/0.6.0/`.**
> Están tomadas de la documentación publicada, no de memoria, pero una feature
> mal escrita da un error de resolución raro y es mejor cazarla aquí.
> Y `default = ["rp235xb"]` con `rp235xa` como alternativa **no es
> especulación**: no hay placa comprada todavía, así que la elección de chip es
> justo la perilla que hay que dejar puesta.

`fw/.cargo/config.toml`:

```toml
[build]
target = "thumbv8m.main-none-eabihf"

[target.thumbv8m.main-none-eabihf]
rustflags = ["-C", "link-arg=--nmagic", "-C", "link-arg=-Tlink.x", "-C", "link-arg=-Tdefmt.x"]

[env]
DEFMT_LOG = "debug"
```

`fw/rust-toolchain.toml`:

```toml
[toolchain]
channel = "stable"
targets = ["thumbv8m.main-none-eabihf"]
```

- [ ] **Step 8: `memory.x`, `build.rs` y un `main` que enlace**

`fw/memory.x` — el mapa del RP2350: 2 MB de flash externa y 520 kB de SRAM.

```text
MEMORY {
    FLASH : ORIGIN = 0x10000000, LENGTH = 2048K
    RAM   : ORIGIN = 0x20000000, LENGTH = 520K
}
```

> **Comprueba `LENGTH` de FLASH contra la placa que acabes comprando.** 2 MB es
> lo que trae la Pico 2; el chip soporta hasta 16 MB por QSPI (§10). La SRAM sí
> es del chip y son 520 kB.

`fw/build.rs`:

```rust
fn main() {
    println!("cargo:rustc-link-arg-bins=--nmagic");
    println!("cargo:rustc-link-arg-bins=-Tlink.x");
    println!("cargo:rustc-link-arg-bins=-Tdefmt.x");
    println!("cargo:rerun-if-changed=memory.x");
}
```

`fw/src/main.rs` — lo mínimo que demuestra que la cadena entera enlaza:

```rust
#![no_std]
#![no_main]

//! El firmware del cerebro. Capa DELGADA a proposito: si una funcion de aqui
//! merece un test, es que vive en la caja equivocada y se muda a `core`.

use defmt::info;
use embassy_executor::Spawner;
use embassy_time::{Duration, Timer};
use sam17_nucleo_core::pinout::N_PINES_USADOS;
use {defmt_rtt as _, panic_probe as _};

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let _p = embassy_rp::init(Default::default());
    info!("SAM17: el cerebro arranco. {} pines en el mapa", N_PINES_USADOS);
    loop {
        Timer::after(Duration::from_secs(1)).await;
    }
}
```

- [ ] **Step 9: Comprobar que enlaza**

```bash
cd software/nucleo/fw && cargo build --release
cd .. && cargo test && cargo clippy --all-targets -- -D warnings
```
Esperado: el firmware **enlaza** (que es lo verificable sin placa) y el
contrato sigue verde. Si el enlazado se queja de `link.x`, es el `build.rs` o
el `.cargo/config.toml` — no lo tapes con `--nmagic` extra.

- [ ] **Step 10: Corregir el README del contrato**

En `software/nucleo/README.md`, donde dice *«el binario de la placa entra como
segundo miembro del mismo workspace»*, sustituir por la razón real: dos targets
distintos, `exclude` en el padre, `[workspace]` propio en `fw`.

- [ ] **Step 11: Commit**

```bash
git add -A software/nucleo
git commit -m "El binario enlaza para el RP2350, y el pinout deja de estar en la cabeza de nadie"
```

---

### Task 2: Los tres huecos del protocolo

**Files:**
- Modify: `core/src/protocolo.rs`, `core/src/lib.rs`
- Modify: `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md` (§4.1)
- Modify: `software/nucleo/README.md` (la tabla de etiquetas)

**Interfaces:**
- Produces: `Mensaje::Hola { version }` (tag `0x87`),
  `Mensaje::Error { etiqueta, codigo }` (tag `0x88`), `CodigoError`.

Ver el apartado del principio: sin esto, un `SET` sobre un parámetro de solo
lectura deja al agente esperando para siempre.

- [ ] **Step 1: Añadir los tests que fallan** en `protocolo.rs`, y **subir el
  array de `todas()` de 19 a 21**:

```rust
    #[test]
    fn los_dos_mensajes_nuevos_tambien_van_y_vuelven() {
        let mut buf = [0u8; 64];
        for m in [
            Mensaje::Hola { version: 1 },
            Mensaje::Error { etiqueta: 0x04, codigo: CodigoError::SoloLectura },
        ] {
            let n = codificar(&m, &mut buf).unwrap();
            assert_eq!(decodificar(&buf[..n]).unwrap(), m);
            assert!(m.del_instrumento(), "los dos van hacia el cliente");
        }
    }

    #[test]
    fn todo_codigo_de_error_sobrevive_el_viaje() {
        // Si uno se perdiera, el cliente sabria que fallo pero no por que.
        let mut buf = [0u8; 64];
        for c in CodigoError::TODOS {
            let m = Mensaje::Error { etiqueta: 0x04, codigo: c };
            let n = codificar(&m, &mut buf).unwrap();
            assert_eq!(decodificar(&buf[..n]).unwrap(), m, "se perdio {c:?}");
        }
    }
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

```rust
/// Por que fallo. Son los `ErrorSet` del modelo mas los que solo existen en
/// el cable.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum CodigoError {
    NoExiste = 1,
    SoloLectura = 2,
    FueraDeRango = 3,
    /// §2.2: quedo retenida. Llega ademas un `Pending` con su token.
    ExigeConfirmacion = 4,
    /// El instrumento entiende la etiqueta pero todavia no la sirve.
    NoDisponible = 5,
    ColaLlena = 6,
    /// La etiqueta no esta en la tabla de §4.1.
    Desconocido = 7,
}

impl CodigoError {
    pub const TODOS: [CodigoError; 7] = [ /* … las siete … */ ];
    pub fn de_byte(b: u8) -> Option<Self> { /* … */ }
}
```

Y en `Mensaje`, dos variantes nuevas del lado instrumento → cliente:

```rust
    /// La respuesta a `Hello`: la version que el instrumento acepta hablar.
    /// Sin esto la negociacion es de un solo sentido y no negocia nada.
    Hola { version: u16 },
    /// Que etiqueta fallo y por que. Un protocolo sin mensaje de error deja
    /// al cliente esperando en silencio, que es el peor modo de fallo posible.
    Error { etiqueta: u8, codigo: CodigoError },
```

Con `T_HOLA: u8 = 0x87` y `T_ERROR: u8 = 0x88`. Los tests que ya existen
—etiquetas sin repetir, dirección en el bit alto, truncamiento rechazado— los
cubren solos en cuanto entren en `todas()`.

Ejecuta: `cd software/nucleo && cargo test && cargo clippy --all-targets -- -D warnings`
Esperado: 21 variantes, todos los tests del protocolo PASS.

- [ ] **Step 3: Actualizar la spec, que es lo que hace legítimo el cambio**

En §4.1, añadir las dos filas a la tabla de mensajes y, debajo, el porqué:

> `HOLA` y `ERROR` se añadieron el 2026-08-17, al escribir el servidor. La
> tabla original dejaba al cliente en silencio en tres casos —`HELLO` sin
> respuesta, `DESCRIBE` sin forma de contestar, y todo `SET` rechazado— y §2.1
> dice que la manera de arreglar eso es crecer la tabla, no inventar una
> convención por fuera.

Y actualizar la tabla de etiquetas de `software/nucleo/README.md`.

- [ ] **Step 4: Commit**

```bash
git add -A software/nucleo docs
git commit -m "Un protocolo sin mensaje de error deja al agente esperando en silencio"
```

---

### Task 3: El empaquetador USB-MIDI

**Files:**
- Create: `core/src/usbmidi.rs`
- Modify: `core/src/lib.rs`

**Interfaces:**
- Consumes: nada de `core`; es puro formato.
- Produces: `empaquetar_sysex(&[u8], &mut [[u8;4]]) -> Result<usize, _>`,
  `Desempaquetador` (`nuevo`, `empujar(paquete) -> Option<Trozo>`), `Trozo`.

**Por qué existe esta pieza.** `embassy_usb::class::midi` es *«packet level»*:
mueve **paquetes de 4 bytes**, no bytes sueltos. Así que el SysEx que el
contrato ya sabe construir (Task 6 del plan anterior) hay que trocearlo con los
códigos que manda USB-MIDI 1.0, y recomponerlo al volver. Es formato puro:
**se prueba entero sin placa**, y es justo la pieza que si se hace a ojo se
descubre rota con un analizador.

| CIN | Qué es | Bytes útiles |
|---|---|---|
| `0x4` | SysEx empieza o continúa | 3 |
| `0x5` | SysEx acaba con **un** byte | 1 |
| `0x6` | SysEx acaba con **dos** | 2 |
| `0x7` | SysEx acaba con **tres** | 3 |

El byte 0 del paquete es `(cable << 4) | CIN`.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn sysex(n: usize) -> heapless::Vec<u8, 512> {
        let mut v = heapless::Vec::new();
        v.push(0xF0).unwrap();
        for i in 0..n {
            v.push((i as u8) & 0x7F).unwrap();
        }
        v.push(0xF7).unwrap();
        v
    }

    #[test]
    fn todo_sysex_se_trocea_y_se_recompone_igual() {
        // El largo importa: el ultimo paquete cambia de CIN segun cuantos
        // bytes sobren, y ahi es donde se rompen las implementaciones a ojo.
        let mut paquetes = [[0u8; 4]; 200];
        for n in 0..=180usize {
            let msg = sysex(n);
            let np = empaquetar_sysex(&msg, &mut paquetes).unwrap();
            let mut d = Desempaquetador::nuevo();
            let mut salida = None;
            for p in &paquetes[..np] {
                if let Some(Trozo::Sysex(bytes)) = d.empujar(p) {
                    salida = Some(heapless::Vec::<u8, 512>::from_slice(bytes).unwrap());
                }
            }
            assert_eq!(salida.as_deref(), Some(msg.as_slice()), "se rompio con n={n}");
        }
    }

    #[test]
    fn el_ultimo_paquete_lleva_el_cin_que_toca() {
        let mut p = [[0u8; 4]; 16];
        // 3 bytes en total (F0 xx F7): un solo paquete, acaba con tres.
        let n = empaquetar_sysex(&sysex(1), &mut p).unwrap();
        assert_eq!(n, 1);
        assert_eq!(p[0][0] & 0x0F, 0x7);
        // 4 bytes: uno de continuacion y uno que acaba con uno.
        let n = empaquetar_sysex(&sysex(2), &mut p).unwrap();
        assert_eq!(n, 2);
        assert_eq!(p[0][0] & 0x0F, 0x4);
        assert_eq!(p[1][0] & 0x0F, 0x5);
        // 5 bytes: continuacion y acaba con dos.
        let n = empaquetar_sysex(&sysex(3), &mut p).unwrap();
        assert_eq!(p[n - 1][0] & 0x0F, 0x6);
    }

    #[test]
    fn el_relleno_de_los_paquetes_cortos_va_a_cero() {
        // Un byte de basura ahi es un byte de MIDI inventado en el cable.
        let mut p = [[0u8; 4]; 16];
        let n = empaquetar_sysex(&sysex(2), &mut p).unwrap();
        assert_eq!(p[n - 1][2..], [0, 0]);
    }

    #[test]
    fn una_nota_no_se_confunde_con_un_sysex() {
        let mut d = Desempaquetador::nuevo();
        // CIN 0x9 = note on.
        match d.empujar(&[0x09, 0x90, 60, 100]) {
            Some(Trozo::Midi(m)) => assert_eq!(m, [0x90, 60, 100]),
            otro => panic!("una nota tiene que salir como nota: {otro:?}"),
        }
    }

    #[test]
    fn un_sysex_a_medias_no_entrega_nada() {
        let mut d = Desempaquetador::nuevo();
        assert!(d.empujar(&[0x04, 0xF0, 0x7D, 0x01]).is_none());
        assert!(d.empujar(&[0x04, 0x02, 0x03, 0x04]).is_none());
    }

    #[test]
    fn un_sysex_mas_largo_que_el_buffer_se_tira_entero_y_se_sigue() {
        // No puede quedar medio mensaje envenenando el siguiente.
        let mut d = Desempaquetador::nuevo();
        for _ in 0..(MAX_SYSEX / 3 + 4) {
            d.empujar(&[0x04, 1, 2, 3]);
        }
        assert!(d.empujar(&[0x05, 0xF7, 0, 0]).is_none(), "no puede entregar basura");
        // Y despues de eso el siguiente mensaje bueno tiene que salir bien.
        let mut p = [[0u8; 4]; 16];
        let msg = sysex(4);
        let n = empaquetar_sysex(&msg, &mut p).unwrap();
        let mut ok = None;
        for q in &p[..n] {
            if let Some(Trozo::Sysex(b)) = d.empujar(q) {
                ok = Some(heapless::Vec::<u8, 512>::from_slice(b).unwrap());
            }
        }
        assert_eq!(ok.as_deref(), Some(msg.as_slice()));
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

`MAX_SYSEX = 512` (el descriptor más gordo cabe de sobra). `Trozo` es
`Sysex(&[u8])` o `Midi([u8; 3])`. El desempaquetador guarda un `heapless::Vec`
y una bandera de desbordado que se limpia al empezar el siguiente `0xF0`.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core usbmidi && cargo clippy --all-targets -- -D warnings`
Esperado: 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add -A software/nucleo
git commit -m "USB-MIDI mueve paquetes de cuatro bytes, no mensajes: el troceo se prueba sin placa"
```

---

### Task 4: El servidor — donde el contrato se vuelve instrumento

**Files:**
- Create: `core/src/servidor.rs`
- Modify: `core/src/lib.rs`

**Interfaces:**
- Consumes: `modelo::Modelo`, `retencion::Retenidas`, `protocolo::*`.
- Produces: `Instrumento` (`nuevo`, `atender`, `modelo`, `modelo_mut`,
  `caducar`), `Respuesta`, `Respuestas`, `VERSION_PROTOCOLO`.

**Esta es la pieza que falta de verdad.** El contrato tiene modelo, retención,
protocolo y descriptor, y **nada los une**. `atender` es la función que hace que
un `SET` que llega por el cable mueva un parámetro, avise a los suscriptores y
conteste. Es pura, así que se prueba entera sin placa.

```rust
pub enum Respuesta {
    Mensaje(Mensaje),
    /// El volcado del descriptor: es de largo variable y grande, asi que no
    /// cabe en un `Mensaje` sin darle vida (`Mensaje<'a>`) y hacer ripplear
    /// eso por todo el codec. La capa de IO lo sirve en su propio sobre.
    Descriptores,
}
pub type Respuestas = heapless::Vec<Respuesta, MAX_RESPUESTAS>;
```

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::{Ambito, Descriptor, Tipo, Unidad};
    use crate::param::ParamId;

    const fn d(id: u16, solo_lectura: bool, medida: bool, confirma: bool) -> Descriptor { /* como en modelo.rs */ }
    static NORMAL: Descriptor = d(0x1000, false, false, false);
    static MEDIDA: Descriptor = d(0x1001, true, true, false);
    static PELIGROSO: Descriptor = d(0x1002, false, false, true);

    fn instrumento() -> Instrumento {
        let mut i = Instrumento::nuevo();
        i.modelo_mut().registrar(&NORMAL).unwrap();
        i.modelo_mut().registrar(&MEDIDA).unwrap();
        i.modelo_mut().registrar(&PELIGROSO).unwrap();
        i
    }

    fn mensajes(r: &Respuestas) -> heapless::Vec<Mensaje, MAX_RESPUESTAS> {
        r.iter().filter_map(|x| match x {
            Respuesta::Mensaje(m) => Some(*m),
            _ => None,
        }).collect()
    }

    #[test]
    fn hello_se_contesta_con_la_version_acordada() {
        let r = instrumento().atender(Mensaje::Hello { version: 1 }, 0);
        assert_eq!(
            mensajes(&r).as_slice(),
            &[Mensaje::Hola { version: VERSION_PROTOCOLO }]
        );
    }

    #[test]
    fn describe_pide_el_volcado_del_descriptor() {
        let r = instrumento().atender(Mensaje::Describe, 0);
        assert!(r.iter().any(|x| matches!(x, Respuesta::Descriptores)));
    }

    #[test]
    fn un_get_devuelve_el_valor_y_un_set_lo_mueve() {
        let mut i = instrumento();
        assert_eq!(
            mensajes(&i.atender(Mensaje::Get(NORMAL.id), 0)).as_slice(),
            &[Mensaje::Changed(NORMAL.id, 0)]
        );
        i.atender(Mensaje::Set(NORMAL.id, 42), 0);
        assert_eq!(i.modelo().get(NORMAL.id), Some(42));
    }

    #[test]
    fn changed_solo_sale_hacia_quien_se_suscribio() {
        // §4.1: CHANGED va a los SUSCRIPTORES. Mandarselo a quien no pidio
        // nada llena el cable de trafico que nadie lee.
        let mut i = instrumento();
        assert!(mensajes(&i.atender(Mensaje::Set(NORMAL.id, 1), 0)).is_empty());
        i.atender(Mensaje::Subscribe { activo: true }, 0);
        assert_eq!(
            mensajes(&i.atender(Mensaje::Set(NORMAL.id, 2), 0)).as_slice(),
            &[Mensaje::Changed(NORMAL.id, 2)]
        );
    }

    #[test]
    fn un_set_rechazado_dice_por_que_en_vez_de_callarse() {
        // El hallazgo que motivo la Task 2. Sin esto el agente escribe, no
        // pasa nada, y se queda esperando para siempre.
        let mut i = instrumento();
        for (id, valor, codigo) in [
            (MEDIDA.id, 5, CodigoError::SoloLectura),
            (NORMAL.id, 99_999, CodigoError::FueraDeRango),
            (ParamId(0xBEEF), 1, CodigoError::NoExiste),
        ] {
            let r = mensajes(&i.atender(Mensaje::Set(id, valor), 0));
            assert_eq!(
                r.as_slice(),
                &[Mensaje::Error { etiqueta: 0x04, codigo }],
                "{id:?} tenia que quejarse con {codigo:?}"
            );
        }
    }

    #[test]
    fn lo_marcado_queda_pendiente_y_solo_el_pulsador_lo_suelta() {
        // §2.2 de punta a punta, por el protocolo.
        let mut i = instrumento();
        let r = mensajes(&i.atender(Mensaje::Set(PELIGROSO.id, 1), 0));
        let token = match r.as_slice() {
            [Mensaje::Error { codigo: CodigoError::ExigeConfirmacion, .. },
             Mensaje::Pending { token, id }] => {
                assert_eq!(*id, PELIGROSO.id);
                *token
            }
            otro => panic!("tenia que retener y avisar: {otro:?}"),
        };
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(0), "no puede haberse aplicado");

        let r = mensajes(&i.confirmacion_fisica(1_000));
        assert!(r.contains(&Mensaje::Resolved { token, confirmado: true }));
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(1));
    }

    #[test]
    fn si_nadie_confirma_el_cliente_se_entera_de_que_expiro() {
        let mut i = instrumento();
        i.atender(Mensaje::Set(PELIGROSO.id, 1), 0);
        let r = mensajes(&i.caducar(crate::retencion::TTL_MS));
        assert!(matches!(r.as_slice(), [Mensaje::Resolved { confirmado: false, .. }]));
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(0));
    }

    #[test]
    fn lo_que_todavia_no_sabemos_hacer_se_dice_claro() {
        // Presets, autoafinado, barrido y memo necesitan perifericos que aun
        // no existen. Callarse seria peor que decir que no.
        let mut i = instrumento();
        for m in [
            Mensaje::PresetList,
            Mensaje::PresetLoad(0),
            Mensaje::TuneStart,
            Mensaje::PatchScan,
            Mensaje::Memo { segundos: 2 },
        ] {
            let r = mensajes(&i.atender(m, 0));
            assert!(
                matches!(r.as_slice(), [Mensaje::Error { codigo: CodigoError::NoDisponible, .. }]),
                "{m:?} se quedo callado"
            );
        }
    }

    #[test]
    fn una_medida_publicada_llega_a_los_suscriptores() {
        let mut i = instrumento();
        i.atender(Mensaje::Subscribe { activo: true }, 0);
        let r = mensajes(&i.publicar_medida(MEDIDA.id, -1200));
        assert_eq!(r.as_slice(), &[Mensaje::Changed(MEDIDA.id, -1200)]);
    }

    #[test]
    fn un_mensaje_del_instrumento_que_llega_de_fuera_se_rechaza() {
        // Un cliente no puede fabricar un CHANGED y mentirle a los demas.
        let mut i = instrumento();
        let r = mensajes(&i.atender(Mensaje::Changed(NORMAL.id, 7), 0));
        assert!(matches!(r.as_slice(), [Mensaje::Error { codigo: CodigoError::Desconocido, .. }]));
        assert_eq!(i.modelo().get(NORMAL.id), Some(0));
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

`VERSION_PROTOCOLO: u16 = 1`. `MAX_RESPUESTAS: usize = 4`. `atender` empieza
rechazando todo lo que traiga el bit alto puesto (`m.del_instrumento()`), y de
ahí baja por la tabla. Los métodos que no vienen del cable —
`confirmacion_fisica`, `caducar`, `publicar_medida`— devuelven `Respuestas`
igual, porque lo que producen también hay que mandarlo.

Ejecuta: `cd software/nucleo && cargo test && cargo clippy --all-targets -- -D warnings`
Esperado: 10 tests nuevos PASS.

- [ ] **Step 3: Commit**

```bash
git add -A software/nucleo
git commit -m "El servidor: aqui es donde el contrato deja de ser piezas y contesta"
```

---

### Task 5: La capa de IO — delgada a propósito

**Files:**
- Modify: `fw/src/main.rs`
- Create: `fw/src/usb.rs`

**Interfaces:**
- Consumes: `usbmidi::{empaquetar_sysex, Desempaquetador, Trozo}`,
  `servidor::{Instrumento, Respuesta}`, `sysex::{envolver, desenvolver}`,
  `protocolo::{codificar, decodificar}`.
- Produces: nada que otro consuma. Es el borde del sistema.

El lazo entero, y por qué no lleva un solo test propio: **cada paso de este
bucle ya vino verde en `core`.** Lo único que añade `fw` es el cableado.

```text
  paquete USB  →  Desempaquetador  →  desenvolver  →  decodificar
                                                            ↓
                                                   Instrumento::atender
                                                            ↓
     MidiClass  ←  empaquetar_sysex  ←  envolver  ←  codificar
```

- [ ] **Step 1: Escribir `fw/src/usb.rs`**

Descriptores de dispositivo (VID/PID de prototipo, fabricante «SAM17»),
`MidiClass::new` con un `StaticCell` por buffer, y dos tareas: una que corre
`UsbDevice::run` y otra con el bucle de arriba.

> **Comprueba la firma de `MidiClass::new` y de los métodos de `Sender` /
> `Receiver` en `https://docs.rs/embassy-usb/0.6.0/embassy_usb/class/midi/`
> antes de escribirla.** Lo confirmado es que el módulo existe y expone
> `MidiClass`, `Sender` y `Receiver`, y que es *packet level* — de ahí la
> Task 3. La firma exacta no se escribe de memoria.

**Y el VID/PID:** usa `0x1209` (pid.codes, el rango libre para proyectos
abiertos) con un PID de pruebas. **Registrar uno de verdad es del día que esto
se distribuya**, no de hoy; queda anotado en `EN-PLACA.md`.

- [ ] **Step 2: Reescribir `fw/src/main.rs`** para levantar el USB y arrancar
  las dos tareas, con el `Instrumento` en un `StaticCell`.

Registra en el modelo lo que ya existe: las medidas de `medidas::registrar`.
El descubrimiento por I²C es del plan 2, así que de momento el instrumento
arranca con las medidas y nada más — y **lo dice por `defmt`** en vez de
fingir que tiene módulos.

- [ ] **Step 3: Comprobar que compila y enlaza**

```bash
cd software/nucleo/fw && cargo build --release && cargo clippy -- -D warnings
cd .. && cargo test && cargo clippy --all-targets -- -D warnings
```
Esperado: enlaza limpio y el contrato sigue verde.

**Lo que este paso NO demuestra**, y hay que decirlo: que enumere, que un DAW
lo vea, ni que el `HELLO` dé la vuelta. Eso necesita placa y es la primera
línea de `EN-PLACA.md`.

- [ ] **Step 4: Commit**

```bash
git add -A software/nucleo
git commit -m "El bucle de USB: cuatro pasos, y los cuatro ya venian probados"
```

---

### Task 6: Cierre — la lista del bring-up, docs y PR

**Files:**
- Create: `software/nucleo/fw/EN-PLACA.md`
- Modify: `software/nucleo/README.md`, `docs/architecture-compute.md`

- [ ] **Step 1: Escribir `fw/EN-PLACA.md`**

La lista con la que se hace el bring-up el día que llegue la placa. Por cada
línea: qué se comprueba, cómo, y **contra qué número**.

1. **Enumera.** El sistema operativo lo ve como dispositivo MIDI. Nombre y
   VID/PID los que dice `usb.rs`.
2. **`HELLO` da la vuelta.** Un script que mande el SysEx y espere `HOLA`.
   Es el primer momento en que el instrumento contesta de verdad.
3. **`DESCRIBE` vuelve entero.** Las 27 medidas, con sus nombres y unidades.
4. **`SET` sobre una medida contesta `ERROR`**, no silencio.
5. **El pinout contra la placa real.** Si la que compras no es RP2350B,
   `pinout.rs` es el único fichero que cambia — esa era su razón de ser.
6. **`memory.x`** contra la flash que traiga.
7. **VID/PID de verdad** si esto llega a distribuirse.

- [ ] **Step 2: Sincronizar los documentos**

- `software/nucleo/README.md`: los módulos nuevos (`pinout`, `usbmidi`,
  `servidor`), la tabla de etiquetas con `HOLA` y `ERROR`, y cómo compilar el
  firmware.
- `docs/architecture-compute.md` §9: el protocolo pasa de «decidido» a
  «implementado y contestando», con la nota de los dos mensajes que faltaban.

- [ ] **Step 3: Gates completos**

```bash
cd software/nucleo && cargo test && cargo clippy --all-targets -- -D warnings
cd fw && cargo build --release && cargo clippy -- -D warnings
cd ../../.. && for f in $(git ls-files '*_budget.py'); do python "$f" >/dev/null && echo "OK $f"; done
```

- [ ] **Step 4: PR, merge, e issue del plan siguiente**

```bash
git push -u origin feat/nucleo-arranca-y-habla
gh pr create --title "El binario arranca y habla" --body "..."
gh issue create --title "Plan 2 del bring-up: los perifericos (I2C, J2, PIO, WS2812)" --body "..."
```

---

## Auto-revisión de este plan

**Cobertura.** De las once filas de #86 este plan cubre una y media: el USB
device con su protocolo, y el andamio del que cuelgan las otras diez. El resto
va explícitamente a los planes 2 y 3, con su issue al cerrar. **Eso es a
propósito** y está declarado arriba: once filas que van desde «enumera» hasta
«mide el jitter del 74HC14» no son un entregable.

**Lo que no se escribe de memoria.** Tres pasos son «abre la documentación
antes de teclear»: las features de `embassy-rp` 0.10 y `embassy-usb` 0.6
(Task 1), la firma de `MidiClass::new` y sus `Sender`/`Receiver` (Task 5), y
`LENGTH` de la flash en `memory.x` contra la placa que se compre (Task 1).
Confirmado con fuente: el target `thumbv8m.main-none-eabihf` existe en rustup,
`embassy_usb::class::midi` expone `MidiClass`/`Sender`/`Receiver` y es *packet
level*, y las versiones publicadas son embassy-rp 0.10, embassy-usb 0.6,
embassy-executor 0.10, embassy-time 0.5.1, defmt 1.1.

**Lo que este plan cambia del anterior, y hay que decirlo.** El README del
contrato afirma que el firmware entra como segundo miembro del workspace.
Es falso —dos targets distintos, y `forced-target` es de nightly— y la Task 1
lo corrige. Mejor eso que dejar una instrucción que no compila.

**Dónde puede quedarse corto.** Los números del pinout son una propuesta sin
placa contra la que contrastarlos. Los tests garantizan lo que sí es
garantizable sin hierro —que ninguno se repita, que todos existan en el chip,
que las analógicas caigan en el ADC— y el fichero está aislado justo para que
estrenar placa cueste un solo cambio.
