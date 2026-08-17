# El contrato del núcleo digital — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El contrato público del SAM17 —modelo de parámetros, descriptor, protocolo, descubrimiento, partes, presets y los dos motores de §7— como una biblioteca Rust `no_std` con toda su verificación corriendo en `cargo test` de escritorio, sin una sola placa de por medio.

**Architecture:** Un workspace en `software/nucleo/` con un solo miembro hoy: `core/`, biblioteca `no_std` + `heapless`, cero dependencias fuera de `heapless` y `libm`. Todo lo que la spec §8 pide y que **no toca hierro** vive aquí. El binario de la placa de desarrollo (USB, PIO, I²C, SPI, WS2812, DIN, pedal) es el **plan siguiente** y entra como segundo miembro del workspace consumiendo esta biblioteca.

**Tech Stack:** Rust 1.95 estable, `no_std`, `heapless` 0.8, `libm` 0.2. Sin `serde`, sin `postcard`, sin dependencias de desarrollo.

**Spec:** `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md`

---

## Por qué este plan no cubre la spec entera

La spec §8 lista el alcance del firmware de validación, y ese alcance se parte
solo en dos mitades que **no se ejecutan igual**:

| | Este plan | El plan siguiente |
|---|---|---|
| Qué es | El contrato y sus motores | El bring-up sobre placa de desarrollo |
| Cómo se verifica | `cargo test` en tu máquina, hoy | Analizador lógico, EEPROM en protoboard, controlador MIDI enchufado |
| Necesita | Nada | Una placa RP2350, y hierro que aún no existe |
| Qué entrega | La biblioteca que el binario va a consumir | El binario |

Partirlo no es diluir el alcance: es que **la mitad de arriba se puede terminar
y dejar verde esta semana**, y §9 ya la había escrito así — casi todas sus filas
dicen *«tests en host, Rust puro»*. Lo que se queda para el plan siguiente son
exactamente las filas que dicen analizador lógico, protoboard o DAW.

**Lo que este plan NO hace, y va al siguiente:** trama del J2 contra silicio
real, I²C contra una EEPROM real, captura con PIO y la medida del jitter del
74HC14 contra los 131 ns, USB de doble rol, WS2812 sobre tira, MIDI DIN,
clock/reset, pedal, y la conformidad MIDI-CI de verdad (§4.5 — ver la
resolución en la Task 6).

---

## Global Constraints

Copiadas literales de la spec. Toda tarea las hereda.

- **`no_std` sin excepciones.** `#![cfg_attr(not(test), no_std)]`. Nada de `Vec`,
  `String`, `Box` ni `HashMap`: `heapless` con capacidad declarada. El destino
  es un micro con 520 kB de SRAM.
- **Un parámetro son 16 bits**: 4 de ranura, 4 de instancia, 8 de índice (§3.1).
  **En la ranura `0` la instancia es el número de parte** (§3.6).
- **Un valor es `i32` con signo, siempre** (§3.2). La escala y la unidad viven
  en el descriptor, nunca en el valor.
- **El invariante de §2.1**: ninguna capacidad existe fuera del modelo y su
  protocolo. En código eso quiere decir: **ninguna función pública muta estado
  del instrumento sin pasar por `Modelo::set` o `Modelo::publicar_medida`.** Si
  una tarea necesita un atajo, el atajo es el defecto.
- **Ningún `4` escrito como número de voces** (§3.6). El conteo sale del
  descubrimiento, con la regla del **mínimo de la cadena**. `MAX_VOCES = 16` es
  una **capacidad**, no un conteo, y así se documenta.
- **Nunca se adivina en silencio** (§7.6): toda inferencia devuelve hipótesis
  **con confianza**. Cuando no alcanza, se declara ambigua. Jamás una certeza
  fabricada.
- **Fallar en voz alta** (§6.1): un preset al que le falta un módulo lo **dice y
  nombra cuál**, no suena raro.
- **Quién exige confirmación física lo declara el instrumento** (§2.2), en el
  descriptor. El cliente no puede saltárselo.
- **El contrato J2 está congelado** (`hardware/03-vco/README.md`): 72 bits,
  `CS` abajo de punta a punta, modo 1, ≤10 MHz, orden de transmisión
  `[U7][U6][U5]`. No se toca.
- **Formato de cable de ancho fijo y little-endian.** Nada de varints ni de
  formatos del ecosistema Rust: este binario lo van a parsear el puente
  inalámbrico y JavaScript en la UI web. Un `DataView` tiene que poder leerlo.
- **Gates:** `cargo test` verde, `cargo clippy -- -D warnings` limpio,
  `cargo build --release` sin avisos, y los cuatro presupuestos del repo en
  verde (`ground_budget.py`, `tuning_budget.py`, `autotune_budget.py`,
  `dac_local_budget.py`).
- **Nombres y comentarios en español**, como el resto del repo. Los nombres de
  parámetro que ve el agente se escriben **para alguien que nunca ha visto el
  instrumento** (§2.1).
- **Datasheets primarios, obligatorio consultarlos y no citarlos de memoria:**
  AD5686R en `https://www.analog.com/media/en/technical-documentation/data-sheets/ad5686r_5685r_5684r.pdf`
  y 24AA02E48 en `https://ww1.microchip.com/downloads/en/DeviceDoc/20002124G.pdf`.
- Commits en español contando el porqué, con el trailer de coautoría del repo.

---

## Estructura de ficheros

| Fichero | De qué responde |
|---|---|
| `software/nucleo/Cargo.toml` | El workspace. Hoy un miembro; el binario de la placa entra después |
| `software/nucleo/core/src/lib.rs` | La raíz `no_std` y los `pub mod` |
| `…/param.rs` | §3.1 direccionamiento, §3.2 valores |
| `…/descriptor.rs` | §3.3 descriptor, §3.4 marcas de medida, §3.6 ámbito, y su códec binario |
| `…/modelo.rs` | El estado vivo: tabla, `GET`/`SET`, `CHANGED` |
| `…/retencion.rs` | §2.2 operaciones retenidas y confirmación física |
| `…/protocolo.rs` | §4.1 la tabla de mensajes y su códec |
| `…/sysex.rs` | Empaquetado de 7 bits y sobre SysEx (§4.4) |
| `…/j2.rs` | La trama de 72 bits del contrato congelado |
| `…/descubrimiento.rs` | §3.5 EEPROM y catálogo de placas, §3.6 conteo de voces |
| `…/partes.rs` | §3.6 partes y reparto de voces |
| `…/preset.rs` | §6.1 presets y topología del patch |
| `…/perturbacion.rs` | §7.6 el motor: códigos ortogonales y correlación |
| `…/atribucion.rs` | §7.2 los dos niveles |
| `…/medidas.rs` | §7.3 el juego de parámetros de medida y su ingesta |

---

### Task 1: El andamio y el direccionamiento

**Files:**
- Create: `software/nucleo/Cargo.toml`, `software/nucleo/core/Cargo.toml`,
  `software/nucleo/core/src/lib.rs`, `software/nucleo/core/src/param.rs`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `ParamId` (`nuevo`, `ranura`, `instancia`, `indice`, `parte`), el
  alias `Valor = i32`, y las constantes `RANURA_CEREBRO`, `MAX_RANURAS`,
  `MAX_INSTANCIAS`. Todas las tareas siguientes cuelgan de esto.

- [ ] **Step 1: Crear el workspace**

`software/nucleo/Cargo.toml`:

```toml
[workspace]
resolver = "2"
members = ["core"]
```

`software/nucleo/core/Cargo.toml`:

```toml
[package]
name = "sam17-nucleo-core"
version = "0.1.0"
edition = "2021"
description = "El contrato del SAM17: modelo de parametros, protocolo y los motores que no necesitan hierro"

[dependencies]
heapless = "0.8"
libm = "0.2"
```

`software/nucleo/core/src/lib.rs`:

```rust
#![cfg_attr(not(test), no_std)]
//! El contrato publico del SAM17.
//!
//! Spec: `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md`.
//!
//! El invariante de §2.1 manda aqui: si una capacidad del instrumento no se
//! puede expresar con estos tipos y estos mensajes, no esta terminada.

pub mod param;
```

- [ ] **Step 2: Añadir a `.gitignore`** al final del fichero:

```gitignore
# Rust
target/
```

- [ ] **Step 3: Escribir el test que falla**, en `core/src/param.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn los_tres_campos_van_y_vuelven() {
        for ranura in 0..16u8 {
            for instancia in 0..16u8 {
                for indice in [0u8, 1, 42, 127, 255] {
                    let id = ParamId::nuevo(ranura, instancia, indice);
                    assert_eq!(id.ranura(), ranura);
                    assert_eq!(id.instancia(), instancia);
                    assert_eq!(id.indice(), indice);
                }
            }
        }
    }

    #[test]
    fn en_la_ranura_cero_la_instancia_es_la_parte() {
        // §3.6: es la unica reinterpretacion del campo, y es a proposito.
        assert_eq!(ParamId::nuevo(0, 3, 12).parte(), Some(3));
        assert_eq!(ParamId::nuevo(1, 3, 12).parte(), None);
    }

    #[test]
    fn el_orden_numerico_agrupa_por_modulo() {
        // El modelo hace busqueda binaria sobre el u16 crudo: los parametros
        // de un modulo tienen que quedar contiguos.
        let a = ParamId::nuevo(1, 0, 255);
        let b = ParamId::nuevo(1, 1, 0);
        let c = ParamId::nuevo(2, 0, 0);
        assert!(a.0 < b.0 && b.0 < c.0);
    }
}
```

- [ ] **Step 4: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core`
Esperado: FAIL, `cannot find type ParamId`.

- [ ] **Step 5: Implementar**, arriba en el mismo `param.rs`:

```rust
//! Direccionamiento (§3.1) y valores (§3.2).

/// La ranura del propio cerebro. Ahi viven las partes (§3.6), el tempo y las
/// medidas de §7.
pub const RANURA_CEREBRO: u8 = 0;
/// El campo es de 4 bits. Hoy solo existen 8 canales de mux (§3.5); el hueco
/// esta a proposito, para que ampliar el mux no mueva el direccionamiento.
pub const MAX_RANURAS: usize = 16;
pub const MAX_INSTANCIAS: usize = 16;

/// El valor de cualquier parametro (§3.2). Entero con signo de 32 bits,
/// siempre: la escala y la unidad viven en el descriptor.
pub type Valor = i32;

/// 16 bits: 4 de ranura, 4 de instancia, 8 de indice (§3.1).
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug, Hash)]
pub struct ParamId(pub u16);

impl ParamId {
    pub const fn nuevo(ranura: u8, instancia: u8, indice: u8) -> Self {
        ParamId((((ranura & 0xF) as u16) << 12) | (((instancia & 0xF) as u16) << 8) | indice as u16)
    }

    /// Que modulo. `0` es el cerebro.
    pub const fn ranura(self) -> u8 {
        (self.0 >> 12) as u8
    }

    /// Que voz o que copia dentro del modulo.
    pub const fn instancia(self) -> u8 {
        ((self.0 >> 8) & 0xF) as u8
    }

    /// Que parametro dentro de esa instancia.
    pub const fn indice(self) -> u8 {
        self.0 as u8
    }

    /// En la ranura 0 el campo instancia significa otra cosa: el numero de
    /// parte (§3.6). Fuera de la ranura 0 no hay partes.
    pub const fn parte(self) -> Option<u8> {
        if self.ranura() == RANURA_CEREBRO {
            Some(self.instancia())
        } else {
            None
        }
    }

    /// El mismo parametro en otra ranura. El catalogo (§3.5) declara sus
    /// parametros sin saber donde lo van a enchufar; el descubrimiento los
    /// reubica con esto.
    pub const fn en_ranura(self, ranura: u8) -> Self {
        ParamId::nuevo(ranura, self.instancia(), self.indice())
    }
}
```

- [ ] **Step 6: Verlo pasar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy -- -D warnings`
Esperado: 3 tests PASS, clippy limpio.

- [ ] **Step 7: Commit**

```bash
git add software/nucleo .gitignore
git commit -m "El nucleo arranca por donde manda: 16 bits que direccionan todo"
```

---

### Task 2: El descriptor y su códec binario

**Files:**
- Create: `software/nucleo/core/src/descriptor.rs`
- Modify: `software/nucleo/core/src/lib.rs` (añadir `pub mod descriptor;`)

**Interfaces:**
- Consumes: `param::{ParamId, Valor}`.
- Produces: `Descriptor` (lado emisor, `&'static str`), `DescriptorLeido<'a>`
  (lado parser, prestado del buffer), `Tipo`, `Ambito`, `Unidad`,
  `escribir(&Descriptor, &mut [u8]) -> Result<usize, ErrorCodec>`,
  `leer(&[u8]) -> Result<(DescriptorLeido, usize), ErrorCodec>`.

**El formato de cable, que es contrato público** (little-endian, ancho fijo):

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

- [ ] **Step 1: Escribir los tests que fallan**, en `descriptor.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    const CUTOFF: Descriptor = Descriptor {
        id: ParamId::nuevo(5, 0, 1),
        nombre: "corte del filtro",
        tipo: Tipo::Continuo,
        ambito: Ambito::PorVoz,
        solo_lectura: false,
        medida: false,
        confirmacion_fisica: false,
        min: 0,
        max: 65535,
        def: 32768,
        unidad: Unidad::Hz,
        etiquetas: &[],
    };

    const MODO: Descriptor = Descriptor {
        id: ParamId::nuevo(0, 0, 7),
        nombre: "modo de voces",
        tipo: Tipo::Enumerado,
        ambito: Ambito::Compartido,
        solo_lectura: false,
        medida: false,
        confirmacion_fisica: true,
        min: 0,
        max: 3,
        def: 1,
        unidad: Unidad::Ninguna,
        etiquetas: &["mono", "unisono", "poly", "parafonico"],
    };

    const BRILLO: Descriptor = Descriptor {
        id: ParamId::nuevo(0, 0, 200),
        nombre: "brillo percibido",
        tipo: Tipo::Continuo,
        ambito: Ambito::Compartido,
        solo_lectura: true,
        medida: true,
        confirmacion_fisica: false,
        min: -6000,
        max: 0,
        def: 0,
        unidad: Unidad::MilidB,
        etiquetas: &[],
    };

    fn ida_y_vuelta(d: &Descriptor) {
        let mut buf = [0u8; 256];
        let n = escribir(d, &mut buf).unwrap();
        let (leido, consumido) = leer(&buf[..n]).unwrap();
        assert_eq!(consumido, n, "el parser tiene que consumir lo que se escribio");
        assert_eq!(leido.id, d.id);
        assert_eq!(leido.nombre, d.nombre);
        assert_eq!(leido.tipo, d.tipo);
        assert_eq!(leido.ambito, d.ambito);
        assert_eq!(leido.solo_lectura, d.solo_lectura);
        assert_eq!(leido.medida, d.medida);
        assert_eq!(leido.confirmacion_fisica, d.confirmacion_fisica);
        assert_eq!((leido.min, leido.max, leido.def), (d.min, d.max, d.def));
        assert_eq!(leido.unidad, d.unidad);
        let recuperadas: heapless::Vec<&str, 16> = leido.etiquetas.collect();
        assert_eq!(recuperadas.as_slice(), d.etiquetas);
    }

    #[test]
    fn un_descriptor_generado_se_parsea_a_lo_mismo() {
        // §9, fila "Modelo y descriptor".
        ida_y_vuelta(&CUTOFF);
        ida_y_vuelta(&MODO);
        ida_y_vuelta(&BRILLO);
    }

    #[test]
    fn el_buffer_corto_no_desborda_ni_entra_en_panico() {
        let mut buf = [0u8; 4];
        assert!(matches!(escribir(&MODO, &mut buf), Err(ErrorCodec::SinSitio)));
        let mut ok = [0u8; 256];
        let n = escribir(&MODO, &mut ok).unwrap();
        for corte in 0..n {
            // Cualquier truncamiento tiene que dar error, jamas un parse a medias.
            assert!(leer(&ok[..corte]).is_err(), "trunco en {corte} y no se quejo");
        }
    }

    #[test]
    fn las_banderas_de_medida_sobreviven_el_viaje() {
        // §3.4: si esto se pierde, un cliente escribiria sobre una medida.
        let mut buf = [0u8; 256];
        let n = escribir(&BRILLO, &mut buf).unwrap();
        let (leido, _) = leer(&buf[..n]).unwrap();
        assert!(leido.solo_lectura && leido.medida);
    }
}
```

- [ ] **Step 2: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core descriptor`
Esperado: FAIL, no compila.

- [ ] **Step 3: Implementar**, arriba en `descriptor.rs`:

```rust
//! El descriptor (§3.3), sus marcas de medida (§3.4) y su ambito (§3.6),
//! con el codec binario que el micro emite y la carcasa expande a JSON.

use crate::param::ParamId;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Tipo {
    Continuo = 0,
    Enumerado = 1,
    Booleano = 2,
}

/// §3.6. Sin esta marca ni la UI sabe dibujarlo, ni el agente sabe que puede
/// mover por nota, ni un preset sabe que guardar una vez y que guardar N.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Ambito {
    Compartido = 0,
    PorVoz = 1,
}

/// Las unidades son documentacion del agente (§2.1), no cosmetica: son lo que
/// un LLM lee para deducir que hace un parametro.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum Unidad {
    Ninguna = 0,
    Hz = 1,
    Cents = 2,
    Milivoltios = 3,
    Milisegundos = 4,
    /// Milesimas de 1.0 — porcentajes, atenuaciones, resonancia.
    Milesimas = 5,
    MilidB = 6,
    Semitonos = 7,
    Grados = 8,
    Milisegundos64 = 9,
}

impl Unidad {
    pub fn de_byte(b: u8) -> Option<Self> {
        use Unidad::*;
        Some(match b {
            0 => Ninguna, 1 => Hz, 2 => Cents, 3 => Milivoltios, 4 => Milisegundos,
            5 => Milesimas, 6 => MilidB, 7 => Semitonos, 8 => Grados, 9 => Milisegundos64,
            _ => return None,
        })
    }
}

/// Lo que el firmware declara.
#[derive(Clone, Copy, Debug)]
pub struct Descriptor {
    pub id: ParamId,
    pub nombre: &'static str,
    pub tipo: Tipo,
    pub ambito: Ambito,
    /// §3.4: no se escribe desde un cliente.
    pub solo_lectura: bool,
    /// §3.4: lo publica el instrumento a partir de lo que mide (§7).
    pub medida: bool,
    /// §2.2: el micro RETIENE la operacion hasta la confirmacion fisica.
    pub confirmacion_fisica: bool,
    pub min: i32,
    pub max: i32,
    pub def: i32,
    pub unidad: Unidad,
    pub etiquetas: &'static [&'static str],
}

/// Lo que un parser recupera, prestado del propio buffer: en `no_std` no hay
/// donde copiarlo.
#[derive(Clone, Copy, Debug)]
pub struct DescriptorLeido<'a> {
    pub id: ParamId,
    pub nombre: &'a str,
    pub tipo: Tipo,
    pub ambito: Ambito,
    pub solo_lectura: bool,
    pub medida: bool,
    pub confirmacion_fisica: bool,
    pub min: i32,
    pub max: i32,
    pub def: i32,
    pub unidad: Unidad,
    pub etiquetas: Etiquetas<'a>,
}

#[derive(Clone, Copy, Debug)]
pub struct Etiquetas<'a> {
    crudo: &'a [u8],
    quedan: u8,
}

impl<'a> Iterator for Etiquetas<'a> {
    type Item = &'a str;
    fn next(&mut self) -> Option<&'a str> {
        if self.quedan == 0 {
            return None;
        }
        let largo = *self.crudo.first()? as usize;
        let txt = core::str::from_utf8(self.crudo.get(1..1 + largo)?).ok()?;
        self.crudo = &self.crudo[1 + largo..];
        self.quedan -= 1;
        Some(txt)
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorCodec {
    /// El buffer de salida no da.
    SinSitio,
    /// El buffer de entrada se acaba antes de tiempo.
    Truncado,
    /// Los bytes estan ahi pero no significan nada valido.
    Invalido,
    /// Etiqueta de mensaje que no esta en la tabla de §4.1 (lo usa `protocolo`).
    Desconocido,
}

pub fn escribir(d: &Descriptor, buf: &mut [u8]) -> Result<usize, ErrorCodec> {
    let mut w = Escritor { buf, n: 0 };
    w.u16(d.id.0)?;
    let banderas = (d.solo_lectura as u8)
        | ((d.medida as u8) << 1)
        | ((d.confirmacion_fisica as u8) << 2)
        | ((d.ambito as u8) << 3)
        | ((d.tipo as u8) << 4);
    w.u8(banderas)?;
    w.i32(d.min)?;
    w.i32(d.max)?;
    w.i32(d.def)?;
    w.u8(d.unidad as u8)?;
    w.texto(d.nombre)?;
    w.u8(u8::try_from(d.etiquetas.len()).map_err(|_| ErrorCodec::Invalido)?)?;
    for e in d.etiquetas {
        w.texto(e)?;
    }
    Ok(w.n)
}

pub fn leer(buf: &[u8]) -> Result<(DescriptorLeido<'_>, usize), ErrorCodec> {
    let mut r = Lector { buf, n: 0 };
    let id = ParamId(r.u16()?);
    let banderas = r.u8()?;
    let tipo = match (banderas >> 4) & 0b11 {
        0 => Tipo::Continuo,
        1 => Tipo::Enumerado,
        2 => Tipo::Booleano,
        _ => return Err(ErrorCodec::Invalido),
    };
    let min = r.i32()?;
    let max = r.i32()?;
    let def = r.i32()?;
    let unidad = Unidad::de_byte(r.u8()?).ok_or(ErrorCodec::Invalido)?;
    let nombre = r.texto()?;
    let n_etiquetas = r.u8()?;
    // Se validan aqui para que el iterador no pueda fallar a medio camino.
    let inicio = r.n;
    for _ in 0..n_etiquetas {
        r.texto()?;
    }
    Ok((
        DescriptorLeido {
            id,
            nombre,
            tipo,
            ambito: if banderas & 0b1000 != 0 { Ambito::PorVoz } else { Ambito::Compartido },
            solo_lectura: banderas & 0b1 != 0,
            medida: banderas & 0b10 != 0,
            confirmacion_fisica: banderas & 0b100 != 0,
            min,
            max,
            def,
            unidad,
            etiquetas: Etiquetas { crudo: &buf[inicio..r.n], quedan: n_etiquetas },
        },
        r.n,
    ))
}

struct Escritor<'a> {
    buf: &'a mut [u8],
    n: usize,
}

impl Escritor<'_> {
    fn crudo(&mut self, bytes: &[u8]) -> Result<(), ErrorCodec> {
        let fin = self.n + bytes.len();
        self.buf.get_mut(self.n..fin).ok_or(ErrorCodec::SinSitio)?.copy_from_slice(bytes);
        self.n = fin;
        Ok(())
    }
    fn u8(&mut self, v: u8) -> Result<(), ErrorCodec> { self.crudo(&[v]) }
    fn u16(&mut self, v: u16) -> Result<(), ErrorCodec> { self.crudo(&v.to_le_bytes()) }
    fn i32(&mut self, v: i32) -> Result<(), ErrorCodec> { self.crudo(&v.to_le_bytes()) }
    fn texto(&mut self, s: &str) -> Result<(), ErrorCodec> {
        self.u8(u8::try_from(s.len()).map_err(|_| ErrorCodec::Invalido)?)?;
        self.crudo(s.as_bytes())
    }
}

struct Lector<'a> {
    buf: &'a [u8],
    n: usize,
}

impl<'a> Lector<'a> {
    fn crudo(&mut self, largo: usize) -> Result<&'a [u8], ErrorCodec> {
        let t = self.buf.get(self.n..self.n + largo).ok_or(ErrorCodec::Truncado)?;
        self.n += largo;
        Ok(t)
    }
    fn u8(&mut self) -> Result<u8, ErrorCodec> { Ok(self.crudo(1)?[0]) }
    fn u16(&mut self) -> Result<u16, ErrorCodec> {
        Ok(u16::from_le_bytes(self.crudo(2)?.try_into().unwrap()))
    }
    fn i32(&mut self) -> Result<i32, ErrorCodec> {
        Ok(i32::from_le_bytes(self.crudo(4)?.try_into().unwrap()))
    }
    fn texto(&mut self) -> Result<&'a str, ErrorCodec> {
        let largo = self.u8()? as usize;
        core::str::from_utf8(self.crudo(largo)?).map_err(|_| ErrorCodec::Invalido)
    }
}
```

- [ ] **Step 4: Verlo pasar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy -- -D warnings`
Esperado: PASS. Si el test de truncamiento falla en algún corte, es un bug real
del parser, no del test: arregla el parser.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo
git commit -m "El descriptor sale en binario porque el micro no serializa JSON"
```

---

### Task 3: El modelo — la única puerta al estado

**Files:**
- Create: `software/nucleo/core/src/modelo.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `param::{ParamId, Valor}`, `descriptor::Descriptor`.
- Produces: `Modelo` (`registrar`, `get`, `set`, `publicar_medida`,
  `descriptor_de`, `len`), `Cambio { id, valor }`, `ErrorSet`.
  **Toda tarea posterior que mueva estado del instrumento pasa por aquí.**

- [ ] **Step 1: Escribir los tests que fallan**, en `modelo.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::{Ambito, Tipo, Unidad};

    const fn d(id: u16, solo_lectura: bool, medida: bool, confirma: bool) -> Descriptor {
        Descriptor {
            id: ParamId(id),
            nombre: "prueba",
            tipo: Tipo::Continuo,
            ambito: Ambito::Compartido,
            solo_lectura,
            medida,
            confirmacion_fisica: confirma,
            min: -100,
            max: 100,
            def: 0,
            unidad: Unidad::Ninguna,
            etiquetas: &[],
        }
    }

    static NORMAL: Descriptor = d(0x1000, false, false, false);
    static MEDIDA: Descriptor = d(0x1001, true, true, false);
    static PELIGROSO: Descriptor = d(0x1002, false, false, true);

    fn modelo() -> Modelo {
        let mut m = Modelo::nuevo();
        // A proposito en desorden: registrar tiene que dejarlo ordenado.
        m.registrar(&PELIGROSO).unwrap();
        m.registrar(&NORMAL).unwrap();
        m.registrar(&MEDIDA).unwrap();
        m
    }

    #[test]
    fn arranca_en_los_valores_por_defecto() {
        assert_eq!(modelo().get(NORMAL.id), Some(0));
    }

    #[test]
    fn un_set_devuelve_el_cambio_que_alimenta_a_changed() {
        // §4.1: CHANGED va a todos los suscriptores venga de donde venga el SET.
        let mut m = modelo();
        assert_eq!(m.set(NORMAL.id, 42), Ok(Cambio { id: NORMAL.id, valor: 42 }));
        assert_eq!(m.get(NORMAL.id), Some(42));
    }

    #[test]
    fn una_medida_no_se_escribe_desde_un_cliente() {
        // §3.4: el unico camino que la escribe es publicar_medida.
        let mut m = modelo();
        assert_eq!(m.set(MEDIDA.id, 5), Err(ErrorSet::SoloLectura));
        assert_eq!(m.get(MEDIDA.id), Some(0));
        assert!(m.publicar_medida(MEDIDA.id, -1200).is_ok());
        assert_eq!(m.get(MEDIDA.id), Some(-1200));
    }

    #[test]
    fn fuera_de_rango_se_rechaza_en_vez_de_recortarse() {
        // §6.1 fallar en voz alta: recortar en silencio le miente al agente,
        // que creeria haber puesto 500.
        let mut m = modelo();
        assert_eq!(m.set(NORMAL.id, 500), Err(ErrorSet::FueraDeRango));
        assert_eq!(m.get(NORMAL.id), Some(0));
    }

    #[test]
    fn lo_marcado_no_se_ejecuta_de_una() {
        // §2.2: la regla la impone el instrumento, no el cliente.
        let mut m = modelo();
        assert_eq!(m.set(PELIGROSO.id, 7), Err(ErrorSet::ExigeConfirmacion));
        assert_eq!(m.get(PELIGROSO.id), Some(0));
        // Solo la retencion (Task 4) puede aplicarlo, y por otra puerta.
        assert!(m.aplicar_confirmado(PELIGROSO.id, 7).is_ok());
        assert_eq!(m.get(PELIGROSO.id), Some(7));
    }

    #[test]
    fn un_parametro_que_no_existe_lo_dice() {
        let mut m = modelo();
        assert_eq!(m.set(ParamId(0xBEEF), 1), Err(ErrorSet::NoExiste));
        assert_eq!(m.get(ParamId(0xBEEF)), None);
    }

    #[test]
    fn no_se_registra_dos_veces_el_mismo_id() {
        let mut m = modelo();
        assert_eq!(m.registrar(&NORMAL), Err(ErrorRegistro::Duplicado));
    }
}
```

- [ ] **Step 2: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core modelo`
Esperado: FAIL, no compila.

- [ ] **Step 3: Implementar**

```rust
//! El estado vivo del instrumento. Por §2.1 esta es la UNICA puerta: si algo
//! muta el instrumento sin pasar por aqui, el agente no lo alcanza.

use crate::descriptor::Descriptor;
use crate::param::{ParamId, Valor};
use heapless::Vec;

/// Capacidad, no conteo. Cinco modulos poblados con sus voces caben de sobra.
pub const MAX_PARAMS: usize = 512;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Cambio {
    pub id: ParamId,
    pub valor: Valor,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorSet {
    NoExiste,
    SoloLectura,
    FueraDeRango,
    /// §2.2: retenida hasta la confirmacion fisica.
    ExigeConfirmacion,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorRegistro {
    Duplicado,
    Lleno,
}

pub struct Modelo {
    descs: Vec<&'static Descriptor, MAX_PARAMS>,
    vals: Vec<Valor, MAX_PARAMS>,
}

impl Default for Modelo {
    fn default() -> Self {
        Self::nuevo()
    }
}

impl Modelo {
    pub const fn nuevo() -> Self {
        Modelo { descs: Vec::new(), vals: Vec::new() }
    }

    pub fn len(&self) -> usize { self.descs.len() }
    pub fn is_empty(&self) -> bool { self.descs.is_empty() }

    /// Inserta ordenado por id para que la busqueda sea binaria.
    pub fn registrar(&mut self, d: &'static Descriptor) -> Result<(), ErrorRegistro> {
        match self.descs.binary_search_by_key(&d.id, |x| x.id) {
            Ok(_) => Err(ErrorRegistro::Duplicado),
            Err(pos) => {
                self.descs.insert(pos, d).map_err(|_| ErrorRegistro::Lleno)?;
                self.vals.insert(pos, d.def).map_err(|_| ErrorRegistro::Lleno)?;
                Ok(())
            }
        }
    }

    fn pos(&self, id: ParamId) -> Option<usize> {
        self.descs.binary_search_by_key(&id, |x| x.id).ok()
    }

    pub fn descriptor_de(&self, id: ParamId) -> Option<&'static Descriptor> {
        self.pos(id).map(|i| self.descs[i])
    }

    pub fn descriptores(&self) -> impl Iterator<Item = &'static Descriptor> + '_ {
        self.descs.iter().copied()
    }

    pub fn get(&self, id: ParamId) -> Option<Valor> {
        self.pos(id).map(|i| self.vals[i])
    }

    /// La escritura de un cliente. Aplica las tres reglas del descriptor.
    pub fn set(&mut self, id: ParamId, v: Valor) -> Result<Cambio, ErrorSet> {
        let i = self.pos(id).ok_or(ErrorSet::NoExiste)?;
        let d = self.descs[i];
        if d.solo_lectura {
            return Err(ErrorSet::SoloLectura);
        }
        if v < d.min || v > d.max {
            return Err(ErrorSet::FueraDeRango);
        }
        if d.confirmacion_fisica {
            return Err(ErrorSet::ExigeConfirmacion);
        }
        self.vals[i] = v;
        Ok(Cambio { id, valor: v })
    }

    /// El unico camino que escribe una medida (§3.4). Lo llama el instrumento,
    /// nunca un cliente.
    pub fn publicar_medida(&mut self, id: ParamId, v: Valor) -> Result<Cambio, ErrorSet> {
        let i = self.pos(id).ok_or(ErrorSet::NoExiste)?;
        if !self.descs[i].medida {
            return Err(ErrorSet::SoloLectura);
        }
        self.vals[i] = v;
        Ok(Cambio { id, valor: v })
    }

    /// La puerta que abre la confirmacion fisica (§2.2). Salta el veto de
    /// `confirmacion_fisica` y NADA MAS: rango y solo-lectura siguen mandando.
    pub fn aplicar_confirmado(&mut self, id: ParamId, v: Valor) -> Result<Cambio, ErrorSet> {
        let i = self.pos(id).ok_or(ErrorSet::NoExiste)?;
        let d = self.descs[i];
        if d.solo_lectura {
            return Err(ErrorSet::SoloLectura);
        }
        if v < d.min || v > d.max {
            return Err(ErrorSet::FueraDeRango);
        }
        self.vals[i] = v;
        Ok(Cambio { id, valor: v })
    }
}
```

- [ ] **Step 4: Verlo pasar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy -- -D warnings`
Esperado: 7 tests nuevos PASS.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo
git commit -m "Una sola puerta al estado, o el agente se queda sin la mitad del sinte"
```

---

### Task 4: Retención y confirmación física

**Files:**
- Create: `software/nucleo/core/src/retencion.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `modelo::{Modelo, ErrorSet, Cambio}`, `param::ParamId`.
- Produces: `Retenidas` (`retener`, `confirmar`, `caducar`, `pendientes`),
  `Retenida { token, id, valor, vence_ms }`, `TTL_MS`.

**Decisión de diseño que el plan cierra:** el pulsador confirma **la más
reciente** (LIFO). En escena hay una operación pendiente, no una cola; si
hubiera dos, la última es la que el usuario acaba de pedir. Los cuatro dígitos
de la cabeza local (§5.2) muestran cuál está esperando.

- [ ] **Step 1: Escribir los tests que fallan**, en `retencion.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::{Ambito, Descriptor, Tipo, Unidad};
    use crate::modelo::{ErrorSet, Modelo};

    static PELIGROSO: Descriptor = Descriptor {
        id: ParamId(0x0055),
        nombre: "borrar la libreria de presets",
        tipo: Tipo::Booleano,
        ambito: Ambito::Compartido,
        solo_lectura: false,
        medida: false,
        confirmacion_fisica: true,
        min: 0,
        max: 1,
        def: 0,
        unidad: Unidad::Ninguna,
        etiquetas: &[],
    };

    fn escena() -> (Modelo, Retenidas) {
        let mut m = Modelo::nuevo();
        m.registrar(&PELIGROSO).unwrap();
        (m, Retenidas::nueva())
    }

    #[test]
    fn llega_por_usb_y_no_se_ejecuta_hasta_el_pulsador() {
        // §9, fila "Confirmacion fisica". Este es EL test de §2.2.
        let (mut m, mut r) = escena();
        assert_eq!(m.set(PELIGROSO.id, 1), Err(ErrorSet::ExigeConfirmacion));
        let token = r.retener(PELIGROSO.id, 1, 0).unwrap();
        assert_eq!(m.get(PELIGROSO.id), Some(0), "no puede haberse aplicado todavia");

        let pendiente = r.confirmar(1_000).expect("el pulsador tenia algo que confirmar");
        assert_eq!(pendiente.token, token);
        m.aplicar_confirmado(pendiente.id, pendiente.valor).unwrap();
        assert_eq!(m.get(PELIGROSO.id), Some(1));
        assert!(r.confirmar(1_001).is_none(), "no puede quedar residuo");
    }

    #[test]
    fn si_nadie_confirma_caduca_y_no_pasa_nada() {
        let (m, mut r) = escena();
        let token = r.retener(PELIGROSO.id, 1, 0).unwrap();
        assert!(r.caducar(TTL_MS - 1).is_empty());
        assert_eq!(r.caducar(TTL_MS).as_slice(), &[token]);
        assert!(r.confirmar(TTL_MS + 1).is_none());
        assert_eq!(m.get(PELIGROSO.id), Some(0));
    }

    #[test]
    fn el_pulsador_confirma_la_mas_reciente() {
        let (_, mut r) = escena();
        r.retener(PELIGROSO.id, 1, 0).unwrap();
        let segunda = r.retener(PELIGROSO.id, 0, 10).unwrap();
        assert_eq!(r.confirmar(20).unwrap().token, segunda);
    }

    #[test]
    fn la_cola_llena_se_queja_en_vez_de_tirar_lo_viejo() {
        let (_, mut r) = escena();
        for i in 0..MAX_RETENIDAS {
            r.retener(PELIGROSO.id, 1, i as u64).unwrap();
        }
        assert!(r.retener(PELIGROSO.id, 1, 99).is_err());
    }

    #[test]
    fn los_tokens_no_se_repiten_entre_operaciones_vivas() {
        let (_, mut r) = escena();
        let a = r.retener(PELIGROSO.id, 1, 0).unwrap();
        let b = r.retener(PELIGROSO.id, 0, 1).unwrap();
        assert_ne!(a, b);
    }
}
```

- [ ] **Step 2: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core retencion`
Esperado: FAIL.

- [ ] **Step 3: Implementar**

```rust
//! §2.2. El micro RETIENE la operacion marcada hasta que llegue la
//! confirmacion fisica. Si lo decidiera el cliente, bastaria con un cliente
//! que no pregunte.

use crate::param::{ParamId, Valor};
use heapless::Vec;

/// En escena hay una operacion pendiente, no una cola.
pub const MAX_RETENIDAS: usize = 4;
/// Portado de la capa de autoridad de `projects/aurelius`: mandatos con TTL.
pub const TTL_MS: u64 = 30_000;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Retenida {
    pub token: u16,
    pub id: ParamId,
    pub valor: Valor,
    pub vence_ms: u64,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct ColaLlena;

pub struct Retenidas {
    cola: Vec<Retenida, MAX_RETENIDAS>,
    siguiente_token: u16,
}

impl Default for Retenidas {
    fn default() -> Self { Self::nueva() }
}

impl Retenidas {
    pub const fn nueva() -> Self {
        Retenidas { cola: Vec::new(), siguiente_token: 1 }
    }

    /// Devuelve el token que viaja en el mensaje `PENDING` (§4.1).
    pub fn retener(&mut self, id: ParamId, valor: Valor, ahora_ms: u64) -> Result<u16, ColaLlena> {
        let token = self.siguiente_token;
        self.cola
            .push(Retenida { token, id, valor, vence_ms: ahora_ms + TTL_MS })
            .map_err(|_| ColaLlena)?;
        self.siguiente_token = self.siguiente_token.wrapping_add(1).max(1);
        Ok(token)
    }

    /// El pulsador de la cabeza local o el pedal (§5.2, §5.3). Confirma la mas
    /// reciente; lo caducado no se confirma.
    pub fn confirmar(&mut self, ahora_ms: u64) -> Option<Retenida> {
        while let Some(ultima) = self.cola.pop() {
            if ahora_ms < ultima.vence_ms {
                return Some(ultima);
            }
        }
        None
    }

    /// Los tokens que hay que anunciar con `RESOLVED { confirmado: false }`.
    pub fn caducar(&mut self, ahora_ms: u64) -> Vec<u16, MAX_RETENIDAS> {
        let mut muertos = Vec::new();
        let mut vivos = Vec::new();
        for r in self.cola.iter() {
            if ahora_ms >= r.vence_ms {
                let _ = muertos.push(r.token);
            } else {
                let _ = vivos.push(*r);
            }
        }
        self.cola = vivos;
        muertos
    }

    pub fn pendientes(&self) -> &[Retenida] {
        &self.cola
    }
}
```

- [ ] **Step 4: Verlo pasar y comprobar clippy**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy -- -D warnings`
Esperado: 5 tests nuevos PASS.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo
git commit -m "Alcance total exige contencion real, y la impone el micro"
```

---

### Task 5: El protocolo

**Files:**
- Create: `software/nucleo/core/src/protocolo.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `param::{ParamId, Valor}`.
- Produces: `Mensaje` (enum con las 19 variantes de §4.1), `Rgb`,
  `codificar(&Mensaje, &mut [u8]) -> Result<usize, ErrorProto>`,
  `decodificar(&[u8]) -> Result<Mensaje, ErrorProto>`.

**Tabla de etiquetas** (bit alto puesto = va del instrumento al cliente):

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

- [ ] **Step 1: Escribir el test que falla**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    /// Una de cada variante. El `match` del codec es exhaustivo, asi que
    /// añadir un mensaje sin codificarlo rompe la compilacion — que es la
    /// guardia de verdad de §4.1.
    fn todas() -> [Mensaje; 19] {
        let id = ParamId::nuevo(3, 2, 17);
        [
            Mensaje::Hello { version: 1 },
            Mensaje::Describe,
            Mensaje::Get(id),
            Mensaje::Set(id, -123_456),
            Mensaje::Subscribe { activo: true },
            Mensaje::PresetList,
            Mensaje::PresetLoad(9),
            Mensaje::PresetSave(9),
            Mensaje::TuneStart,
            Mensaje::PatchScan,
            Mensaje::Telemetry,
            Mensaje::Point { id, color: Rgb { r: 255, g: 0, b: 128 } },
            Mensaje::Memo { segundos: 8 },
            Mensaje::Changed(id, i32::MIN),
            Mensaje::Modules,
            Mensaje::TuneProgress { voz: 3, cents_x100: -1750, hecho: false },
            Mensaje::Jacks,
            Mensaje::Pending { token: 4242, id },
            Mensaje::Resolved { token: 4242, confirmado: true },
        ]
    }

    #[test]
    fn cada_mensaje_va_y_vuelve_identico() {
        let mut buf = [0u8; 64];
        for m in todas() {
            let n = codificar(&m, &mut buf).unwrap();
            assert_eq!(decodificar(&buf[..n]).unwrap(), m, "se rompio {m:?}");
        }
    }

    #[test]
    fn la_direccion_va_en_el_bit_alto_de_la_etiqueta() {
        let mut buf = [0u8; 64];
        for m in todas() {
            codificar(&m, &mut buf).unwrap();
            assert_eq!(buf[0] & 0x80 != 0, m.del_instrumento(), "{m:?}");
        }
    }

    #[test]
    fn una_etiqueta_desconocida_se_rechaza() {
        assert_eq!(decodificar(&[0x7F]), Err(ErrorProto::Desconocido));
        assert_eq!(decodificar(&[]), Err(ErrorProto::Truncado));
        assert_eq!(decodificar(&[0x03, 0x11]), Err(ErrorProto::Truncado));
    }
}
```

- [ ] **Step 2: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core protocolo`
Esperado: FAIL.

- [ ] **Step 3: Implementar.** El códec reutiliza el patrón `Escritor`/`Lector`
de `descriptor.rs`: **hazlos `pub(crate)` allí y úsalos aquí**, no los copies.

```rust
//! §4.1. Esta enumeracion es la superficie COMPLETA del instrumento: por §2.1
//! no puede haber capacidad fuera de ella. Añadir una funcion es añadir aqui.

use crate::descriptor::ErrorCodec;
use crate::param::{ParamId, Valor};

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Rgb { pub r: u8, pub g: u8, pub b: u8 }

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Mensaje {
    // --- del cliente al instrumento ---
    Hello { version: u16 },
    Describe,
    Get(ParamId),
    Set(ParamId, Valor),
    Subscribe { activo: bool },
    PresetList,
    PresetLoad(u8),
    PresetSave(u8),
    TuneStart,
    PatchScan,
    Telemetry,
    /// §2.1: enciende el LED de un parametro o de un jack. Señalar y el
    /// patcheo guiado son el mismo mecanismo.
    Point { id: ParamId, color: Rgb },
    /// §7.5: unos segundos de audio para que el agente los analice.
    Memo { segundos: u8 },

    // --- del instrumento al cliente ---
    /// Va a TODOS los suscriptores, sin importar quien movio el parametro.
    Changed(ParamId, Valor),
    Modules,
    TuneProgress { voz: u8, cents_x100: i16, hecho: bool },
    Jacks,
    Pending { token: u16, id: ParamId },
    Resolved { token: u16, confirmado: bool },
}

pub type ErrorProto = ErrorCodec;

impl Mensaje {
    pub fn del_instrumento(&self) -> bool {
        etiqueta(self) & 0x80 != 0
    }
}
```

Escribe `etiqueta()`, `codificar()` y `decodificar()` con un `match` exhaustivo
sobre cada variante, siguiendo la tabla de etiquetas de arriba y las mismas
convenciones little-endian del descriptor (`ParamId` como `u16`, `Valor` como
`i32`, `bool` como `0`/`1`, `Rgb` como tres bytes). `decodificar` devuelve
`ErrorCodec::Truncado` si faltan bytes y `ErrorCodec::Desconocido` si la
etiqueta no está en la tabla (las dos ya existen desde la Task 2).

- [ ] **Step 4: Verlo pasar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy -- -D warnings`
Esperado: 3 tests nuevos PASS, 19 variantes cubiertas.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo
git commit -m "Diecinueve mensajes: la superficie entera del instrumento, de un vistazo"
```

---

### Task 6: Empaquetado de 7 bits y sobre SysEx

**Files:**
- Create: `software/nucleo/core/src/sysex.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `descriptor::{escribir, leer, ErrorCodec}`.
- Produces: `empaquetar`, `desempaquetar`, `largo_empaquetado`, `envolver`,
  `desenvolver`, `ID_FABRICANTE_NO_COMERCIAL`.

**Resolución de una ambigüedad de la spec, escrita aquí para no discutirla
después.** §3.3 dice que *«el micro emite binario compacto; la carcasa lo
expande a JSON»*, y §4.5 pide Property Exchange, que es JSON. Las dos cosas se
sostienen porque en Property Exchange la **cabecera** es JSON pequeño y el
**cuerpo** lleva su `mediaType` declarado: la cabecera la emite el micro como
texto casi fijo, y el cuerpo va como binario compacto. La carcasa expande.

**Y lo que esta tarea NO hace:** la conformidad MIDI-CI de verdad —MUID,
`ResourceList`, los nombres exactos de la cabecera— se resuelve en el plan del
binario, y su **primer paso es leer el documento M2-103-UM de la MIDI
Association**, no escribirlo de memoria. Aquí se usa el ID de fabricante **no
comercial `0x7D`**, que es exactamente para lo que existe, y así el transporte
queda probado sin inventarse un estándar ajeno.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn patron(n: usize) -> heapless::Vec<u8, 512> {
        (0..n).map(|i| (i as u8).wrapping_mul(37).wrapping_add(0x80)).collect()
    }

    #[test]
    fn ida_y_vuelta_para_todo_largo_que_nos_importa() {
        let mut emp = [0u8; 640];
        let mut des = [0u8; 512];
        for n in 0..=256usize {
            let datos = patron(n);
            let e = empaquetar(&datos, &mut emp).unwrap();
            assert_eq!(e, largo_empaquetado(n));
            assert!(emp[..e].iter().all(|b| *b < 0x80), "un byte de SysEx con el bit alto, n={n}");
            let d = desempaquetar(&emp[..e], &mut des).unwrap();
            assert_eq!(&des[..d], datos.as_slice(), "no volvio igual con n={n}");
        }
    }

    #[test]
    fn el_descriptor_completo_viaja_en_sysex_y_vuelve_identico() {
        // §9, fila "Property Exchange sobre MIDI 1.0". Sin UMP de por medio.
        use crate::descriptor::*;
        use crate::param::ParamId;
        static D: Descriptor = Descriptor {
            id: ParamId::nuevo(5, 1, 3),
            nombre: "resonancia del filtro",
            tipo: Tipo::Continuo,
            ambito: Ambito::PorVoz,
            solo_lectura: false,
            medida: false,
            confirmacion_fisica: false,
            min: 0,
            max: 65535,
            def: 0,
            unidad: Unidad::Milesimas,
            etiquetas: &[],
        };
        let mut plano = [0u8; 256];
        let n = escribir(&D, &mut plano).unwrap();

        let mut sobre = [0u8; 512];
        let s = envolver(&plano[..n], &mut sobre).unwrap();
        assert_eq!(sobre[0], 0xF0);
        assert_eq!(sobre[1], ID_FABRICANTE_NO_COMERCIAL);
        assert_eq!(sobre[s - 1], 0xF7);
        assert!(sobre[1..s - 1].iter().all(|b| *b < 0x80));

        let mut vuelta = [0u8; 256];
        let v = desenvolver(&sobre[..s], &mut vuelta).unwrap();
        assert_eq!(&vuelta[..v], &plano[..n]);
        let (leido, _) = leer(&vuelta[..v]).unwrap();
        assert_eq!(leido.nombre, D.nombre);
        assert_eq!(leido.ambito, D.ambito);
    }

    #[test]
    fn un_sobre_roto_se_rechaza() {
        let mut buf = [0u8; 64];
        assert!(desenvolver(&[0xF0, 0x7D, 0x00], &mut buf).is_err()); // sin F7
        assert!(desenvolver(&[0x00, 0x7D, 0xF7], &mut buf).is_err()); // sin F0
    }
}
```

- [ ] **Step 2: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core sysex`
Esperado: FAIL.

- [ ] **Step 3: Implementar**

```rust
//! §4.4. Property Exchange usa SysEx estilo MIDI 1.0, y en SysEx todo byte de
//! datos tiene que ser menor que 0x80. De ahi el empaquetado 7-a-8: por cada
//! grupo de 7 bytes sale uno con los bits altos y siete con los bajos.

use crate::descriptor::ErrorCodec;

/// ID de fabricante no comercial. Es lo que la MIDI Association reserva para
/// prototipos y uso privado: nada que registrar y nada que chocar.
pub const ID_FABRICANTE_NO_COMERCIAL: u8 = 0x7D;

pub const fn largo_empaquetado(n: usize) -> usize {
    n + n.div_ceil(7)
}

pub fn empaquetar(entrada: &[u8], salida: &mut [u8]) -> Result<usize, ErrorCodec> {
    let necesita = largo_empaquetado(entrada.len());
    if salida.len() < necesita {
        return Err(ErrorCodec::SinSitio);
    }
    let mut o = 0;
    for grupo in entrada.chunks(7) {
        let altos = grupo
            .iter()
            .enumerate()
            .fold(0u8, |acc, (i, b)| acc | ((b >> 7) << i));
        salida[o] = altos;
        o += 1;
        for b in grupo {
            salida[o] = b & 0x7F;
            o += 1;
        }
    }
    Ok(o)
}

pub fn desempaquetar(entrada: &[u8], salida: &mut [u8]) -> Result<usize, ErrorCodec> {
    let mut o = 0;
    for grupo in entrada.chunks(8) {
        let altos = grupo[0];
        if altos & 0x80 != 0 {
            return Err(ErrorCodec::Invalido);
        }
        for (i, b) in grupo[1..].iter().enumerate() {
            if b & 0x80 != 0 {
                return Err(ErrorCodec::Invalido);
            }
            *salida.get_mut(o).ok_or(ErrorCodec::SinSitio)? = b | ((altos >> i) & 1) << 7;
            o += 1;
        }
    }
    Ok(o)
}

/// `F0 7D <datos empaquetados> F7`.
pub fn envolver(datos: &[u8], salida: &mut [u8]) -> Result<usize, ErrorCodec> {
    *salida.first_mut().ok_or(ErrorCodec::SinSitio)? = 0xF0;
    *salida.get_mut(1).ok_or(ErrorCodec::SinSitio)? = ID_FABRICANTE_NO_COMERCIAL;
    let n = empaquetar(datos, salida.get_mut(2..).ok_or(ErrorCodec::SinSitio)?)?;
    *salida.get_mut(2 + n).ok_or(ErrorCodec::SinSitio)? = 0xF7;
    Ok(3 + n)
}

pub fn desenvolver(sobre: &[u8], salida: &mut [u8]) -> Result<usize, ErrorCodec> {
    if sobre.len() < 3 || sobre[0] != 0xF0 || sobre[sobre.len() - 1] != 0xF7 {
        return Err(ErrorCodec::Invalido);
    }
    if sobre[1] != ID_FABRICANTE_NO_COMERCIAL {
        return Err(ErrorCodec::Invalido);
    }
    desempaquetar(&sobre[2..sobre.len() - 1], salida)
}
```

- [ ] **Step 4: Verlo pasar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy -- -D warnings`
Esperado: 3 tests nuevos PASS.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo
git commit -m "El descriptor entero cabe en SysEx: UMP no compraba nada de esto"
```

---

### Task 7: La trama del J2

**Files:**
- Create: `software/nucleo/core/src/j2.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Produces: `palabra(cmd, canal, dato) -> u32`, `trama(u7, u6, u5) -> [u8; 9]`,
  `tramas_vco4(tono: &[u16; 4], pwm, mezcla: Mezcla) -> [[u8; 9]; 4]`,
  `Mezcla`, `Canal`, `CMD_ESCRIBIR_Y_ACTUALIZAR`.

**El contrato, literal de `hardware/03-vco/README.md` — no se toca:** 72 bits,
`CS` abajo durante los 72 relojes, orden de transmisión `[U7][U6][U5]`. Canales:
**U5** A-D = tono de las voces 1-4; **U6** A = PWM compartido, B/C/D = mezcla
sierra/tri/pulso; **U7** A = mezcla de seno, B/C/D de reserva.

**Una trama lleva UNA palabra por chip, y de ahí sale toda la forma de esta
tarea.** 72 bits son 3 × 24, y una palabra del AD5686R escribe **un canal**. Así
que refrescar la placa entera son **cuatro tramas**, y encajan exactas: la trama
`i` escribe el canal `i` de los tres chips a la vez.

| Trama | U7 | U6 | U5 |
|---|---|---|---|
| 0 | A — mezcla de seno | A — PWM compartido | A — tono voz 1 |
| 1 | B — reserva | B — mezcla sierra | B — tono voz 2 |
| 2 | C — reserva | C — mezcla triangular | C — tono voz 3 |
| 3 | D — reserva | D — mezcla pulso | D — tono voz 4 |

**El `4` de esta tarea es legítimo y hay que decir por qué:** es un hecho del
**tipo de placa** módulo 3 —tiene cuatro voces y doce canales de DAC—, no del
instrumento. Por eso la función se llama `tramas_vco4` y vive junto al catálogo,
no en el reparto de voces (Task 9), que sigue sin saber cuántas voces hay hasta
que se lo diga el descubrimiento.

- [ ] **Step 1: Verificar el datasheet ANTES de escribir nada**

Abre `https://www.analog.com/media/en/technical-documentation/data-sheets/ad5686r_5685r_5684r.pdf`
y confirma, sin fiarte de la memoria de nadie:

1. Que la palabra de entrada son **24 bits**: 4 de comando, 4 de dirección,
   16 de dato.
2. El código del comando **«write to and update DAC channel n»**.
3. Que la dirección de canal es **one-hot** (A, B, C, D) y cuál es cuál.

Anota los tres en un comentario de cabecera del fichero con el número de página
del PDF. **Si alguno no coincide con lo que este plan escribe, manda el
datasheet y arregla el plan**, no al revés.

- [ ] **Step 2: Escribir el test que falla**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn la_trama_son_nueve_bytes_en_el_orden_congelado() {
        // hardware/03-vco/README.md: 72 bits = 3 chips x 24, orden [U7][U6][U5].
        let t = trama([0x1111, 0, 0, 0], [0x2222, 0, 0, 0], [0x3333, 0, 0, 0]);
        assert_eq!(t.len(), 9);
        let u7 = u32::from_be_bytes([0, t[0], t[1], t[2]]);
        let u5 = u32::from_be_bytes([0, t[6], t[7], t[8]]);
        assert_eq!(u7 & 0xFFFF, 0x1111, "el primer word que sale acaba en U7");
        assert_eq!(u5 & 0xFFFF, 0x3333, "el ultimo se queda en U5");
    }

    #[test]
    fn cada_palabra_lleva_comando_y_canal_donde_toca() {
        let p = palabra(CMD_ESCRIBIR_Y_ACTUALIZAR, Canal::C, 0xBEEF);
        assert_eq!(p >> 20, CMD_ESCRIBIR_Y_ACTUALIZAR as u32);
        assert_eq!((p >> 16) & 0xF, Canal::C as u32);
        assert_eq!(p & 0xFFFF, 0xBEEF);
        assert_eq!(p >> 24, 0, "una palabra son 24 bits, no mas");
    }

    #[test]
    fn los_canales_son_one_hot_y_distintos() {
        let cs = [Canal::A as u32, Canal::B as u32, Canal::C as u32, Canal::D as u32];
        for c in cs {
            assert_eq!(c.count_ones(), 1, "direccionamiento one-hot del AD5686R");
        }
        assert_eq!(cs.iter().fold(0, |a, b| a | b).count_ones(), 4);
    }

    #[test]
    fn el_tono_de_cada_voz_cae_en_su_canal_de_u5() {
        let tono = [0xAAAAu16, 0xBBBB, 0xCCCC, 0xDDDD];
        let ts = tramas_vco4(&tono, 0x1234, Mezcla::default());
        assert_eq!(ts.len(), 4, "cuatro canales son cuatro tramas");
        for (i, t) in ts.iter().enumerate() {
            let u5 = u32::from_be_bytes([0, t[6], t[7], t[8]]);
            assert_eq!(u5 & 0xFFFF, tono[i] as u32, "trama {i}: tono de la voz {}", i + 1);
            assert_eq!((u5 >> 16) & 0xF, Canal::de_indice(i) as u32, "trama {i}: canal");
        }
    }

    #[test]
    fn el_pwm_compartido_va_en_el_canal_a_de_u6() {
        let ts = tramas_vco4(&[0; 4], 0x1234, Mezcla::default());
        let u6 = u32::from_be_bytes([0, ts[0][3], ts[0][4], ts[0][5]]);
        assert_eq!(u6 & 0xFFFF, 0x1234);
        assert_eq!((u6 >> 16) & 0xF, Canal::A as u32);
    }
}
```

- [ ] **Step 3: Verlo fallar, implementar, y verlo pasar**

`Mezcla { sierra: u16, triangular: u16, pulso: u16, seno: u16 }` con `Default`.
`Canal::de_indice(0..3) -> Canal`. `tramas_vco4` sigue la tabla de arriba:
para cada `i`, `trama(palabra(CMD, c_i, u7_i), palabra(CMD, c_i, u6_i),
palabra(CMD, c_i, tono[i]))`.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core j2 && cargo clippy -- -D warnings`
Esperado: FAIL primero, luego los cinco tests PASS.

- [ ] **Step 4: Commit**

```bash
git add software/nucleo
git commit -m "La trama del J2 en Rust: el contrato del modulo 3 no se toca, se obedece"
```

---

### Task 8: Descubrimiento y conteo de voces

**Files:**
- Create: `software/nucleo/core/src/descubrimiento.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `descriptor::Descriptor`, `param::ParamId`.
- Produces: `TipoPlaca`, `Identidad<'a>`, `leer_identidad(&[u8])`,
  `Placa`, `CATALOGO`, `placa_de(TipoPlaca)`,
  `voces_del_instrumento(&[&Placa]) -> u8`, `crc16`.

**El mapa de la EEPROM, que este plan define porque nadie lo había definido.**
El 24AA02E48 son 256 bytes y los últimos seis traen el EUI-48 de fábrica
(**verificar la dirección exacta en el datasheet antes de escribir**), así que
lo nuestro vive abajo:

```text
  0x00  1  magia = 0x17
  0x01  1  version de la cabecera = 1
  0x02  2  tipo de placa (u16 LE)
  0x04  1  revision
  0x05  1  largo del blob de calibracion
  0x06  4  serial (u32 LE)
  0x0A  2  crc16 de 0x00..0x0A (CCITT-FALSE, poly 0x1021, init 0xFFFF)
  0x0C  n  blob de calibracion
```

**Y el conteo de voces NO sale de aquí.** La EEPROM da tipo y revisión; el
número de voces sale de la tabla del catálogo, que vive en el firmware del
cerebro (§3.5 paso 3). Son 256 bytes: alcanzan para identidad y calibración, no
para un descriptor.

- [ ] **Step 1: Verificar el datasheet**

Abre `https://ww1.microchip.com/downloads/en/DeviceDoc/20002124G.pdf` y confirma
en qué direcciones vive el EUI-48 de fábrica y si son de solo lectura. Anótalo
en el comentario de cabecera con la página. Ajusta la constante `FIN_ZONA_LIBRE`
a lo que diga el PDF.

- [ ] **Step 2: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn eeprom(tipo: u16, rev: u8, serial: u32, calib: &[u8]) -> [u8; 256] {
        let mut e = [0xFFu8; 256];
        e[0] = 0x17;
        e[1] = 1;
        e[2..4].copy_from_slice(&tipo.to_le_bytes());
        e[4] = rev;
        e[5] = calib.len() as u8;
        e[6..10].copy_from_slice(&serial.to_le_bytes());
        let c = crc16(&e[0..10]);
        e[10..12].copy_from_slice(&c.to_le_bytes());
        e[12..12 + calib.len()].copy_from_slice(calib);
        e
    }

    #[test]
    fn una_eeprom_buena_da_identidad_y_calibracion() {
        let e = eeprom(0x0003, 1, 0xDEADBEEF, &[1, 2, 3, 4]);
        let id = leer_identidad(&e).unwrap();
        assert_eq!(id.tipo, TipoPlaca(0x0003));
        assert_eq!(id.revision, 1);
        assert_eq!(id.serial, 0xDEAD_BEEF);
        assert_eq!(id.calibracion, &[1, 2, 3, 4]);
    }

    #[test]
    fn una_eeprom_virgen_o_corrupta_no_se_confunde_con_un_modulo() {
        assert!(leer_identidad(&[0xFF; 256]).is_err());
        let mut e = eeprom(3, 1, 1, &[]);
        e[4] = 99; // revision cambiada sin recalcular el crc
        assert!(matches!(leer_identidad(&e), Err(ErrorEeprom::Crc)));
    }

    #[test]
    fn ocho_vco_y_cuatro_vcf_dan_cuatro_voces() {
        // §9, fila "Conteo de voces". La regla del minimo de la cadena.
        let vco8 = Placa { tipo: TipoPlaca(0x9003), nombre: "vco x8", voces: 8, params: &[] };
        let vcf4 = Placa { tipo: TipoPlaca(0x0005), nombre: "vcf x4", voces: 4, params: &[] };
        assert_eq!(voces_del_instrumento(&[&vco8, &vcf4]), 4);
    }

    #[test]
    fn los_modulos_sin_voces_no_bajan_el_conteo() {
        let vco = Placa { tipo: TipoPlaca(0x0003), nombre: "vco", voces: 4, params: &[] };
        let mixer = Placa { tipo: TipoPlaca(0x0004), nombre: "mixer", voces: 0, params: &[] };
        assert_eq!(voces_del_instrumento(&[&vco, &mixer]), 4);
    }

    #[test]
    fn sin_modulos_no_hay_voces_y_se_dice() {
        assert_eq!(voces_del_instrumento(&[]), 0);
    }

    #[test]
    fn el_conteo_no_es_una_constante_disfrazada() {
        // Si alguien escribe un 4 en el camino, uno de estos falla.
        for n in 1..=16u8 {
            let p = Placa { tipo: TipoPlaca(0x0003), nombre: "x", voces: n, params: &[] };
            assert_eq!(voces_del_instrumento(&[&p]), n);
        }
    }
}
```

- [ ] **Step 3: Verlo fallar, implementar, verlo pasar**

Implementa `crc16` (CCITT-FALSE), `leer_identidad` con las tres validaciones
(magia, versión, CRC) más el recorte del blob al largo declarado, `Placa`,
`CATALOGO` con la entrada del módulo 3 (`TipoPlaca(0x0003)`, 4 voces) y
`voces_del_instrumento` como el mínimo de los `voces > 0`.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core descubrimiento && cargo clippy -- -D warnings`
Esperado: 6 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add software/nucleo
git commit -m "Treinta centavos de EEPROM y el conteo de voces deja de ser una suposicion"
```

---

### Task 9: Partes y reparto de voces

**Files:**
- Create: `software/nucleo/core/src/partes.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `param::ParamId`.
- Produces: `Parte`, `MAX_PARTES`, `MAX_VOCES`, `parte_de(&[Parte], canal, nota)`,
  `Repartidor` (`nueva(n_voces)`, `nota_on`, `nota_off`, `voz`), `Asignacion`.

**`MAX_VOCES = 16` es capacidad, no conteo.** El `Repartidor` se construye con
el número que dio el descubrimiento (Task 8) y no conoce ningún otro.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn dos_partes() -> [Parte; 2] {
        [
            // Rangos SOLAPADOS a proposito: §9 pide justo eso.
            Parte { canal: 0, nota_min: 21, nota_max: 72, voces: 2, primera_voz: 0, preset: 0 },
            Parte { canal: 1, nota_min: 48, nota_max: 108, voces: 2, primera_voz: 2, preset: 1 },
        ]
    }

    #[test]
    fn cada_nota_va_a_la_parte_que_le_toca_y_a_su_reserva() {
        // §9, fila "Partes".
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);

        let a = r.nota_on(&partes, 0, 60).unwrap(); // solapada, pero canal 0
        let b = r.nota_on(&partes, 1, 60).unwrap(); // misma nota, canal 1
        assert_eq!(a.parte, 0);
        assert_eq!(b.parte, 1);
        assert!(a.voz < 2, "la parte 0 tiene las voces 0 y 1");
        assert!((2..4).contains(&b.voz), "la parte 1 arranca en la voz 2");
    }

    #[test]
    fn una_nota_fuera_de_todo_rango_no_asigna_nada() {
        assert!(Repartidor::nueva(4).nota_on(&dos_partes(), 0, 100).is_none());
    }

    #[test]
    fn cuando_se_acaban_las_voces_roba_la_mas_vieja_de_SU_parte() {
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);
        let primera = r.nota_on(&partes, 0, 60).unwrap();
        let _ = r.nota_on(&partes, 0, 62).unwrap();
        let tercera = r.nota_on(&partes, 0, 64).unwrap();
        assert_eq!(tercera.voz, primera.voz, "roba la mas vieja");
        assert_eq!(tercera.robada, Some(60));
    }

    #[test]
    fn robar_no_cruza_de_una_parte_a_otra() {
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);
        r.nota_on(&partes, 1, 60).unwrap();
        r.nota_on(&partes, 1, 62).unwrap();
        let tercera = r.nota_on(&partes, 1, 64).unwrap();
        assert!((2..4).contains(&tercera.voz), "la parte 1 no puede tocar las voces de la 0");
    }

    #[test]
    fn soltar_una_nota_libera_su_voz() {
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);
        let a = r.nota_on(&partes, 0, 60).unwrap();
        assert_eq!(r.nota_off(0, 60), Some(a.voz));
        let b = r.nota_on(&partes, 0, 65).unwrap();
        assert_eq!(b.robada, None, "habia una voz libre: no hacia falta robar");
    }

    #[test]
    fn funciona_con_cualquier_conteo_de_voces() {
        // El anti-`4` de verdad: si alguien lo escribiera, esto revienta.
        for n in 1..=MAX_VOCES as u8 {
            let partes = [Parte { canal: 0, nota_min: 0, nota_max: 127, voces: n, primera_voz: 0, preset: 0 }];
            let mut r = Repartidor::nueva(n);
            let mut vistas = heapless::Vec::<u8, { MAX_VOCES }>::new();
            for nota in 0..n {
                let a = r.nota_on(&partes, 0, 60 + nota).unwrap();
                assert!(!vistas.contains(&a.voz), "repitio la voz {} con n={n}", a.voz);
                vistas.push(a.voz).unwrap();
                assert!(a.voz < n);
            }
            // La siguiente ya no cabe: tiene que robar, no fallar.
            assert!(r.nota_on(&partes, 0, 100).unwrap().robada.is_some());
        }
    }

    #[test]
    fn primera_voz_es_lo_que_hace_posible_el_poly_chain() {
        // §3.6: dos instrumentos encadenados, cada uno con su tramo del pool.
        let partes = [Parte { canal: 0, nota_min: 0, nota_max: 127, voces: 2, primera_voz: 6, preset: 0 }];
        let mut r = Repartidor::nueva(8);
        for nota in 0..2 {
            assert!((6..8).contains(&r.nota_on(&partes, 0, 60 + nota).unwrap().voz));
        }
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

`Asignacion { parte: u8, voz: u8, nota: u8, robada: Option<u8> }`. `parte_de`
devuelve la **primera** parte cuyo canal coincide y cuyo rango contiene la nota.
El robo elige el `sello` más pequeño **dentro del tramo
`primera_voz..primera_voz + voces`**, nunca fuera.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core partes && cargo clippy -- -D warnings`
Esperado: 7 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add software/nucleo
git commit -m "Partes y reparto: multitimbrico, splits y poly-chain sin tocar el modelo"
```

---

### Task 10: Presets y topología del patch

**Files:**
- Create: `software/nucleo/core/src/preset.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `descubrimiento::TipoPlaca`, `param::{ParamId, Valor}`,
  `descriptor::ErrorCodec`.
- Produces: `Preset`, `JackId`, `Conexion`, `escribir_preset`, `leer_preset`,
  `comprobar(&PresetLeido, &[(TipoPlaca, u8)]) -> Result<(), ErrorCarga>`.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::descubrimiento::TipoPlaca;
    use crate::param::ParamId;

    fn preset() -> Preset<'static> {
        Preset {
            nombre: "bajo que respira",
            autor: "samuel",
            etiquetas: &["bajo", "lento"],
            requiere: &[(TipoPlaca(0x0003), 1), (TipoPlaca(0x0005), 1)],
            valores: &[(ParamId::nuevo(3, 0, 1), 24_000), (ParamId::nuevo(5, 0, 1), -300)],
            topologia: &[Conexion {
                origen: JackId { ranura: 3, jack: 4 },
                destino: JackId { ranura: 5, jack: 0 },
                atenuacion_milesimas: 400,
            }],
        }
    }

    #[test]
    fn un_preset_va_y_vuelve_entero() {
        let mut buf = [0u8; 512];
        let n = escribir_preset(&preset(), &mut buf).unwrap();
        let p = leer_preset(&buf[..n]).unwrap();
        assert_eq!(p.nombre, "bajo que respira");
        assert_eq!(p.valores().count(), 2);
        let c = p.topologia().next().unwrap();
        assert_eq!(c.origen.ranura, 3);
        assert_eq!(c.destino.jack, 0);
        // §7.6 regala esto: no solo la conexion, tambien cuanto atenua.
        assert_eq!(c.atenuacion_milesimas, 400);
    }

    #[test]
    fn si_falta_un_modulo_lo_dice_y_nombra_cual() {
        // §6.1 fallar en voz alta, en vez de sonar raro.
        let mut buf = [0u8; 512];
        let n = escribir_preset(&preset(), &mut buf).unwrap();
        let p = leer_preset(&buf[..n]).unwrap();

        assert_eq!(p.comprobar(&[(TipoPlaca(0x0003), 1), (TipoPlaca(0x0005), 1)]), Ok(()));
        assert_eq!(
            p.comprobar(&[(TipoPlaca(0x0003), 1)]),
            Err(ErrorCarga::FaltaModulo { tipo: TipoPlaca(0x0005), revision: 1 })
        );
    }

    #[test]
    fn una_revision_vieja_tambien_se_avisa() {
        let mut buf = [0u8; 512];
        let n = escribir_preset(&preset(), &mut buf).unwrap();
        let p = leer_preset(&buf[..n]).unwrap();
        assert!(p.comprobar(&[(TipoPlaca(0x0003), 0), (TipoPlaca(0x0005), 1)]).is_err());
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

Mismo estilo de códec que Task 2 (`Escritor`/`Lector` compartidos, ancho fijo,
little-endian). `comprobar` recorre `requiere` y devuelve el **primero** que
falte, con su tipo y revisión dentro del error — el mensaje al usuario tiene que
poder nombrarlo.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core preset && cargo clippy -- -D warnings`
Esperado: 3 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add software/nucleo
git commit -m "El patch es un dato: el preset guarda hasta cuanto atenua cada cable"
```

---

### Task 11: El motor de perturbación

**Files:**
- Create: `software/nucleo/core/src/perturbacion.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Produces: `walsh(fila, t) -> i8`, `LARGO_CODIGO`, `Correlador`
  (`nuevo(n_fuentes)`, `inyeccion(fuente, t)`, `muestra(t, y)`, `veredicto`),
  `Veredicto`, `GANANCIA_MINIMA`, `CONFIANZA_MINIMA`.

**Esta es la pieza que resuelve dos problemas** (§7.6): el barrido de topología
de §6.2 y la sonda causal de §7.2. Un `Correlador` por **punto de observación**
(una entrada de CV legible por ADC); todas las fuentes se perturban a la vez.

**El algoritmo, escrito para que no se improvise:**

1. Cada fuente `k` toma la **fila `k+1`** de Walsh-Hadamard. La fila `0` es
   continua y se salta: un camino acoplado en AC no la pasaría.
2. Durante `LARGO_CODIGO` marcos de análisis, la fuente `k` se perturba en
   `±amplitud` según `walsh(k+1, t)`.
3. En cada marco se muestrea la entrada: `y[t]`.
4. `g[k] = (1/L) · Σ_t walsh(k+1, t) · y[t] / amplitud` — la ganancia del camino
   de `k` a esta entrada. Las demás fuentes se cancelan por ortogonalidad; el
   ruido se divide por `√L`.
5. Se ordena por `|g|`. Si `|g₁| < GANANCIA_MINIMA` → `Desconectado`.
6. `sep = (|g₁| − |g₂|) / |g₁|`;
   `ruido = rms(y[t] − g₁·amplitud·walsh(k₁+1, t))`;
   `snr = |g₁|·amplitud / ruido`;
   `confianza = sep · snr/(snr+1)`.
7. `confianza < CONFIANZA_MINIMA` → `Ambiguo` con las dos primeras. Nunca una
   respuesta segura y equivocada.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    /// Ruido reproducible sin dependencias: xorshift con semilla fija.
    struct Ruido(u64);
    impl Ruido {
        fn nuevo(semilla: u64) -> Self { Ruido(semilla | 1) }
        /// Uniforme en [-1, 1), escalado por sigma.
        fn muestra(&mut self, sigma: f32) -> f32 {
            self.0 ^= self.0 << 13;
            self.0 ^= self.0 >> 7;
            self.0 ^= self.0 << 17;
            ((self.0 >> 40) as f32 / 2048.0 - 1.0) * sigma
        }
    }

    const N: usize = 8;
    const AMPLITUD: f32 = 1.0;

    /// Simula un punto de observacion: `enlaces` son (fuente, ganancia).
    fn correr(enlaces: &[(usize, f32)], sigma: f32, semilla: u64) -> Veredicto {
        let mut c = Correlador::nuevo(N);
        let mut r = Ruido::nuevo(semilla);
        for t in 0..LARGO_CODIGO {
            let mut y = r.muestra(sigma);
            for (fuente, g) in enlaces {
                y += g * AMPLITUD * c.inyeccion(*fuente, t) as f32;
            }
            c.muestra(t, y);
        }
        c.veredicto(AMPLITUD)
    }

    #[test]
    fn ninguna_fuente_lleva_continua() {
        // §7.6: un camino acoplado en AC no pasa DC. La fila 0 no se usa.
        for k in 0..N {
            let suma: i32 = (0..LARGO_CODIGO).map(|t| walsh(k + 1, t) as i32).sum();
            assert_eq!(suma, 0, "la fuente {k} lleva continua");
        }
    }

    #[test]
    fn los_codigos_son_ortogonales_entre_si() {
        for i in 0..N {
            for j in 0..N {
                let p: i32 = (0..LARGO_CODIGO)
                    .map(|t| walsh(i + 1, t) as i32 * walsh(j + 1, t) as i32)
                    .sum();
                assert_eq!(p, if i == j { LARGO_CODIGO as i32 } else { 0 });
            }
        }
    }

    #[test]
    fn recupera_la_conexion_y_ademas_cuanto_atenua() {
        match correr(&[(3, 0.4)], 0.01, 1) {
            Veredicto::Conectado { fuente, ganancia, confianza } => {
                assert_eq!(fuente, 3);
                assert!((ganancia - 0.4).abs() < 0.02, "ganancia {ganancia}");
                assert!(confianza > CONFIANZA_MINIMA);
            }
            otro => panic!("tenia que encontrarlo: {otro:?}"),
        }
    }

    #[test]
    fn un_atenuador_fuerte_no_lo_esconde() {
        // El detector de escalon fallaba justo aqui (§7.6).
        match correr(&[(5, 0.05)], 0.01, 2) {
            Veredicto::Conectado { fuente, ganancia, .. } => {
                assert_eq!(fuente, 5);
                assert!((ganancia - 0.05).abs() < 0.01);
            }
            otro => panic!("un atenuador al 5 % sigue siendo un cable: {otro:?}"),
        }
    }

    #[test]
    fn una_entrada_sin_cable_se_declara_desconectada() {
        assert!(matches!(correr(&[], 0.03, 3), Veredicto::Desconectado));
    }

    #[test]
    fn dos_fuentes_acopladas_por_igual_se_declaran_ambiguas() {
        // §7.6 regla 2: se cae a la ocupacion y la app pregunta.
        match correr(&[(1, 0.30), (6, 0.29)], 0.01, 4) {
            Veredicto::Ambiguo { a, b } => {
                let par = [a.min(b), a.max(b)];
                assert_eq!(par, [1, 6]);
            }
            otro => panic!("con dos empatadas no puede haber certeza: {otro:?}"),
        }
    }

    #[test]
    fn poca_senal_y_mucho_ruido_es_ambiguo_no_una_respuesta_segura() {
        // Este es EL test de §9: se exige que lo declare ambiguo en vez de
        // inventar. Una respuesta confiada y equivocada seria el fallo peor.
        assert!(!matches!(correr(&[(2, 0.06)], 0.15, 5), Veredicto::Conectado { .. }));
    }

    #[test]
    fn una_fuente_a_dos_destinos_da_positivo_en_los_dos() {
        // 1-a-muchos sale correcto: son dos correladores independientes.
        for semilla in [7, 8] {
            assert!(matches!(
                correr(&[(4, 0.5)], 0.01, semilla),
                Veredicto::Conectado { fuente: 4, .. }
            ));
        }
    }
}
```

- [ ] **Step 2: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core perturbacion`
Esperado: FAIL.

- [ ] **Step 3: Implementar**

```rust
//! §7.6. Una sola pieza para dos problemas: la topologia del patch (§6.2) y la
//! sonda causal de la atribucion (§7.2). Los dos preguntan lo mismo — observo
//! un efecto, cual de las N causas que controlo lo produjo — y los dos se
//! responden igual: perturbar y correlacionar.
//!
//! Correlacion, NO deteccion de escalon: el escalon se rompe con atenuadores,
//! se ahoga en ruido, y obliga a barrer de una en una.

use heapless::Vec;

/// Marcos de analisis por barrido. Potencia de dos: Walsh-Hadamard lo exige, y
/// la ganancia de correlacion contra el ruido es sqrt(LARGO_CODIGO) = 8.
pub const LARGO_CODIGO: usize = 64;
pub const MAX_FUENTES: usize = 32;

/// Por debajo de esto no hay cable, solo diafonia.
pub const GANANCIA_MINIMA: f32 = 0.02;
/// Por debajo de esto se declara ambiguo y se pregunta.
pub const CONFIANZA_MINIMA: f32 = 0.5;

/// Walsh-Hadamard de Sylvester: el signo es (-1)^popcount(fila & t).
/// La fila 0 es todo +1 — continua — y por eso las fuentes toman 1..
pub const fn walsh(fila: usize, t: usize) -> i8 {
    if (fila & t).count_ones() % 2 == 0 { 1 } else { -1 }
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Veredicto {
    Conectado { fuente: usize, ganancia: f32, confianza: f32 },
    /// §7.6 regla 2: se cae a la ocupacion y la app pide confirmar la pareja.
    Ambiguo { a: usize, b: usize },
    Desconectado,
}

pub struct Correlador {
    n_fuentes: usize,
    muestras: Vec<f32, LARGO_CODIGO>,
}
```

Implementa `nuevo`, `inyeccion(fuente, t) -> i8` (que es `walsh(fuente + 1, t)`),
`muestra(t, y)` (empuja a `muestras`) y `veredicto(amplitud)` siguiendo los
siete pasos de arriba, con `libm::sqrtf` para el rms. `veredicto` **no puede
entrar en pánico** con menos muestras de las esperadas: devuelve `Desconectado`.

- [ ] **Step 4: Verlo pasar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy -- -D warnings`
Esperado: 8 tests PASS. **Si alguno de los dos tests de ambigüedad pasa por los
pelos, no toques el test para que cuadre: ajusta `CONFIANZA_MINIMA` y deja
escrito en el commit por qué.** El valor de la constante es la decisión; los
casos son el contrato.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo
git commit -m "Dos funciones sin probar se vuelven un componente con un test"
```

---

### Task 12: Atribución en dos niveles

**Files:**
- Create: `software/nucleo/core/src/atribucion.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `perturbacion` (para la sonda de nivel 2).
- Produces: `EstadoVozAudio`, `Causa`, `Hipotesis`, `Atribucion`,
  `atribuir(pico_hz, &[EstadoVozAudio]) -> Atribucion`,
  `sonda_sugerida(&Atribucion) -> Option<[u8; 2]>`.

**El algoritmo** (§7.2), porque *«cruzarlo»* a mano ondeada no es un diseño:

- **Nivel 1, gratis y continuo.** Para cada voz que suena: `n = round(pico/f)`
  acotado a `1..=N_ARMONICOS`; `err = 1200·log2(pico / (n·f))` en cents;
  `puntaje = exp(−(err/TOL_CENTS)²) · decaimiento(n)`, con
  `decaimiento(n) = 1/(1 + 0.05·(n−1))`. Para cada filtro:
  `err` contra `f_corte` y `puntaje = exp(−(err/TOL_CENTS)²) · resonancia`.
- **Ambiguo tiene definición, no criterio de barra:** `sep = (p₁−p₂)/p₁`, y
  `sep < MARGEN` es ambiguo. Punto.
- **Nivel 2** solo cuando el 1 queda ambiguo: `sonda_sugerida` dice qué dos
  voces perturbar, y de ahí en adelante es el motor de Task 11.

**El decaimiento es suave a propósito.** Con 110 Hz y 220 Hz sonando, un pico en
440 es el 4.º armónico de una y el 2.º de la otra: musicalmente **no se puede
distinguir**, y un decaimiento agresivo daría una respuesta segura y falsa.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn voz(f: f32) -> EstadoVozAudio {
        EstadoVozAudio { sonando: true, f_hz: f, f_corte_hz: 20_000.0, resonancia: 0.0 }
    }

    #[test]
    fn el_fundamental_de_una_voz_sola_es_una_respuesta_clara() {
        match atribuir(440.0, &[voz(440.0), voz(113.0)]) {
            Atribucion::Probable { h: Hipotesis { causa: Causa::Armonico { voz, n }, .. }, confianza } => {
                assert_eq!((voz, n), (0, 1));
                assert!(confianza > 0.5, "confianza {confianza}");
            }
            otro => panic!("esto no tenia por que ser dudoso: {otro:?}"),
        }
    }

    #[test]
    fn dos_voces_que_comparten_un_armonico_dan_confianza_baja() {
        // §9, fila "Atribucion". 440 es el 4.o de 110 y el 2.o de 220: nadie
        // puede saberlo, y el motor tampoco puede fingir que si.
        let a = atribuir(440.0, &[voz(110.0), voz(220.0)]);
        assert!(matches!(a, Atribucion::Ambigua(_, _)), "dio una certeza fabricada: {a:?}");
        let sonda = sonda_sugerida(&a).expect("si es ambigua, hay algo que sondear");
        assert_eq!([sonda[0].min(sonda[1]), sonda[0].max(sonda[1])], [0, 1]);
    }

    #[test]
    fn una_resonancia_marcada_gana_al_armonico_lejano() {
        let voces = [
            EstadoVozAudio { sonando: true, f_hz: 110.0, f_corte_hz: 1_500.0, resonancia: 0.95 },
            voz(97.0),
        ];
        assert!(matches!(
            atribuir(1_500.0, &voces),
            Atribucion::Probable { h: Hipotesis { causa: Causa::Resonancia { voz: 0 }, .. }, .. }
        ));
    }

    #[test]
    fn un_filtro_sin_resonancia_no_se_lleva_el_merito() {
        let voces = [EstadoVozAudio { sonando: true, f_hz: 110.0, f_corte_hz: 1_500.0, resonancia: 0.0 }];
        assert!(!matches!(
            atribuir(1_500.0, &voces),
            Atribucion::Probable { h: Hipotesis { causa: Causa::Resonancia { .. }, .. }, .. }
        ));
    }

    #[test]
    fn sin_voces_sonando_no_se_atribuye_nada() {
        assert!(matches!(atribuir(440.0, &[]), Atribucion::Desconocida));
    }

    #[test]
    fn un_pico_que_no_encaja_con_nada_se_declara_desconocido() {
        assert!(matches!(atribuir(7_331.0, &[voz(110.0)]), Atribucion::Desconocida));
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

Usa `libm::{log2f, expf, roundf}`. `N_ARMONICOS = 16`, `TOL_CENTS = 35.0`,
`MARGEN = 0.20`, `PUNTAJE_MINIMO = 0.10` (por debajo, `Desconocida`).

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core atribucion && cargo clippy -- -D warnings`
Esperado: 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add software/nucleo
git commit -m "Atribuir con confianza: un agente que recibe certezas fabricadas arregla el sonido equivocado"
```

---

### Task 13: Las medidas como parámetros de primera

**Files:**
- Create: `software/nucleo/core/src/medidas.rs`
- Modify: `software/nucleo/core/src/lib.rs`

**Interfaces:**
- Consumes: `modelo::Modelo`, `descriptor::Descriptor`, `param::ParamId`.
- Produces: `N_BANDAS`, `MEDIDAS` (el juego de descriptores),
  `id_banda(n)`, `ID_PICO_HZ`, `ID_PICO_EXCESO`, `ID_SONORIDAD`,
  `ingerir(&mut Modelo, &TramaMedida)`, `TramaMedida`.

**El juego de parámetros** (§7.3 — una FFT cruda no contesta *«hay muchos
graves»*, la pregunta es perceptual):

| Parámetro | Unidad | Rango | Contesta |
|---|---|---|---|
| `banda 0..23` | `MilidB` | −60000..0 | «demasiado grave»: 24 bandas Bark con sonoridad estilo BS.1770 |
| `pico (Hz)` | `Hz` | 0..20000 | «una frecuencia por encima de las demás» |
| `exceso del pico` | `MilidB` | 0..40000 | cuánto sobresale de la envolvente suavizada |
| `sonoridad` | `MilidB` | −60000..0 | el nivel percibido de la mezcla |

Todos con `solo_lectura: true`, `medida: true`, `ambito: Compartido`, en la
ranura `0` parte `0`. El agente no necesita saber que existe un motor de
análisis: solo lee parámetros.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::modelo::{ErrorSet, Modelo};

    fn instrumento() -> Modelo {
        let mut m = Modelo::nuevo();
        for d in MEDIDAS {
            m.registrar(d).unwrap();
        }
        m
    }

    #[test]
    fn lo_que_manda_el_modulo_4_sale_por_get() {
        // §9, fila "Medidas por el J2": bandas y picos sinteticos, como si
        // vinieran de la placa que aun no existe.
        let mut m = instrumento();
        let mut t = TramaMedida::default();
        t.bandas[0] = -3_000;
        t.bandas[23] = -41_000;
        t.pico_hz = 1_240;
        t.pico_exceso_mdb = 9_500;
        t.sonoridad_mdb = -14_000;
        ingerir(&mut m, &t);

        assert_eq!(m.get(id_banda(0)), Some(-3_000));
        assert_eq!(m.get(id_banda(23)), Some(-41_000));
        assert_eq!(m.get(ID_PICO_HZ), Some(1_240));
        assert_eq!(m.get(ID_PICO_EXCESO), Some(9_500));
        assert_eq!(m.get(ID_SONORIDAD), Some(-14_000));
    }

    #[test]
    fn ningun_cliente_puede_escribirlas() {
        let mut m = instrumento();
        assert_eq!(m.set(ID_PICO_HZ, 100), Err(ErrorSet::SoloLectura));
        assert_eq!(m.set(id_banda(5), 0), Err(ErrorSet::SoloLectura));
    }

    #[test]
    fn todas_traen_unidad_y_rango_para_que_el_agente_las_entienda() {
        // §2.1: nombres y unidades son documentacion, no cosmetica.
        use crate::descriptor::Unidad;
        let m = instrumento();
        for d in MEDIDAS {
            assert!(d.medida && d.solo_lectura, "{}", d.nombre);
            assert_ne!(d.unidad, Unidad::Ninguna, "{} sin unidad", d.nombre);
            assert!(d.max > d.min, "{} sin rango", d.nombre);
            assert!(!d.nombre.is_empty());
            assert!(m.get(d.id).is_some());
        }
        assert_eq!(MEDIDAS.len(), N_BANDAS + 3);
    }

    #[test]
    fn una_medida_fuera_de_rango_se_recorta_en_vez_de_tirar_la_trama() {
        // Aqui SI se recorta, y por eso es distinto de un SET: no es la
        // intencion de nadie, es un sensor. Perder la trama entera seria peor.
        let mut m = instrumento();
        let mut t = TramaMedida::default();
        t.pico_hz = 999_999;
        ingerir(&mut m, &t);
        let d = MEDIDAS.iter().find(|d| d.id == ID_PICO_HZ).unwrap();
        assert_eq!(m.get(ID_PICO_HZ), Some(d.max));
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

`MEDIDAS` es un `static [Descriptor; N_BANDAS + 3]` construido a mano con
nombres que se leen solos (`"banda 1 (20-100 Hz)"` … o el borde real de cada
banda Bark). `ingerir` recorta a `[min, max]` y llama a
`Modelo::publicar_medida` para cada campo — **ese es el único camino**, por §2.1.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core medidas && cargo clippy -- -D warnings`
Esperado: 4 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add software/nucleo
git commit -m "El agente lee brillo con el mismo GET con que lee cutoff"
```

---

### Task 14: Cierre — README, docs sincronizados y PR

**Files:**
- Create: `software/nucleo/README.md`
- Modify: `docs/architecture-compute.md`, `hardware/02-midi-cv/README.md`,
  `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md`

- [ ] **Step 1: Escribir `software/nucleo/README.md`**

Con: qué es (el contrato, no el firmware), por qué está partido en dos planes,
la tabla de módulos del apartado «Estructura de ficheros» de este plan, el
formato de cable del descriptor byte a byte, la tabla de etiquetas del
protocolo, el mapa de la EEPROM, y **cómo correrlo**:

```bash
cd software/nucleo
cargo test
cargo clippy -- -D warnings
```

- [ ] **Step 2: Sincronizar los documentos que este trabajo deja desfasados**

- `docs/architecture-compute.md` §9: mover a «Cerrado» lo que este plan cierra
  (el descriptor y el protocolo dejan de ser diseño y pasan a ser código con
  tests) y apuntar a `software/nucleo/`.
- `hardware/02-midi-cv/README.md`: en el banner de «SUPERADO», añadir que el
  sucesor **ya tiene su contrato escrito y verde**, con la ruta.
- La spec, cabecera: `**Estado:** aprobado en brainstorming, pendiente de plan`
  → `**Estado:** en ejecución — el contrato en `software/nucleo/`, el bring-up
  en su plan`.

- [ ] **Step 3: Correr los gates completos**

```bash
cd software/nucleo && cargo test && cargo clippy -- -D warnings && cargo build --release
cd ../.. && python hardware/01-psu/ground_budget.py && python hardware/02-midi-cv/tuning_budget.py && python hardware/02-midi-cv/autotune_budget.py && python hardware/03-vco/dac_local_budget.py
```

Esperado: todo verde. Si `ground_budget.py` o `dac_local_budget.py` no están en
esas rutas, búscalos con `git ls-files '*_budget.py'` y usa las reales.

- [ ] **Step 4: Rama, commit y PR**

```bash
git checkout -b feat/nucleo-contrato
git add -A
git commit -m "El contrato del nucleo, entero y verde, sin haber tocado una placa"
git push -u origin feat/nucleo-contrato
gh pr create --title "El contrato del nucleo digital: 14 modulos, todo verificado en cargo test" --body "..."
```

- [ ] **Step 5: Abrir el issue del plan siguiente**

```bash
gh issue create --title "Bring-up del nucleo sobre placa RP2350: lo que este plan dejo fuera" --body "..."
```

En el cuerpo, la lista de §8 que este plan **no** cubre: trama del J2 contra
silicio, I²C contra EEPROM real, PIO y el jitter del 74HC14 contra los 131 ns,
USB de doble rol, WS2812, MIDI DIN, clock/reset, pedal, y la conformidad MIDI-CI
(cuyo primer paso es leer el M2-103-UM).

---

## Auto-revisión de este plan

**Cobertura de la spec.** Cada punto de §8 tiene tarea o está declarado fuera
de alcance arriba con su destino: descubrimiento → T8; J2 → T7 (bits) y plan
siguiente (silicio); PIO → plan siguiente; modelo y descriptor → T2, T3;
protocolo y Property Exchange → T5, T6; motor de perturbación → T11; WS2812 →
plan siguiente; partes → T9; conteo de voces → T8, T9; reparto → T9; presets →
T10; retención → T4; atribución → T12, T13; USB doble rol, DIN, clock/reset,
pedal → plan siguiente.

**Tres cosas que este plan decide y la spec dejaba abiertas**, para que se
puedan discutir en la revisión y no aparezcan como sorpresa:

1. **Fuera de rango se rechaza, no se recorta** (T3) — salvo en las medidas
   (T13), donde recortar es correcto porque no es la intención de nadie: es un
   sensor.
2. **El pulsador confirma la más reciente** (T4), no una cola.
3. **Property Exchange se parte**: el transporte (empaquetado + sobre) va aquí
   con ID de fabricante no comercial; la conformidad MIDI-CI va al plan
   siguiente y empieza leyendo el documento, no la memoria (T6).

**Lo que hay que verificar contra fuente primaria antes de escribir código**, y
que ninguna tarea puede resolver de memoria: la palabra de 24 bits y el
direccionamiento one-hot del AD5686R (T7, paso 1) y la zona del EUI-48 del
24AA02E48 (T8, paso 1). Si el PDF contradice a este plan, manda el PDF.

**Dónde este plan puede quedarse corto.** Las constantes del motor de
perturbación (`GANANCIA_MINIMA`, `CONFIANZA_MINIMA`) y de la atribución
(`TOL_CENTS`, `MARGEN`, el decaimiento armónico) salen de razonar los casos,
no de medir hardware. Los tests fijan **el comportamiento exigido** —recupera lo
que se puso, declara ambiguo lo que no se puede saber— y las constantes son la
perilla para cumplirlos. Cuando llegue el hierro, se vuelven a mirar contra
señales reales; los tests no.
