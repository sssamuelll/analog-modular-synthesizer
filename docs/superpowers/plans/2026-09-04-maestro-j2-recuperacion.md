# El maestro del J2: plazo, reinicio y cuenta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el cerebro deje de poder colgarse callado en el J2: toda espera con plazo, todo plazo vencido con reinicio, y todo reinicio contado.

**Architecture:** La política vive en `core` como una máquina de estados por ranura, sin hardware y sin `async`, probada entera en el host. El driver vive en `fw` y solo cloca bytes. La frontera es dura: **`fw` cloca bytes; `core` sabe qué son.** Si la semántica del sobre aparece en `j2_spi.rs`, es un defecto (spec D8).

**Tech Stack:** Rust `no_std` (`sam17-nucleo-core`), `embassy-stm32` / `embassy-time` / `embassy-executor` (`sam17-nucleo-fw`), Python 3 para el presupuesto.

**Spec:** [`docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`](../specs/2026-09-03-maestro-j2-recuperacion-design.md)

---

## El bloqueo que la spec no nombra, y que parte este plan en dos

La spec §9 riesgo 4 dice: *«Queda que compile, y eso es el primer paso del plan»*.
**No puede compilar.** `software/nucleo/fw/Cargo.toml` declara hoy:

```toml
description = "El firmware del cerebro del SAM17 sobre RP2350"
embassy-rp = { version = "0.10", features = ["rp235xb", ...] }
```

El firmware entero apunta a `embassy-rp` y al `thumbv8m.main-none-eabihf` del
RP2350. `j2_spi.rs` es un driver de `spi_v4` de STM32; **no hay dónde ponerlo**
hasta que el pase a `embassy-stm32` ocurra, y ese pase es **#250**, que ya está
abierto y declarado como *«no es nivelacion, es trabajo con tests»*.

Consecuencia para este plan, y es buena: **la fase A no depende de nada.**

| Fase | Qué | Bloqueo |
|---|---|---|
| **A** (tareas 1-6) | `maestro_j2.rs` en `core`, sus 12 tests, el presupuesto y el CSV | **ninguno** — se hace hoy |
| **B** (tareas 7-8) | `j2_spi.rs` y el ejecutor en `fw` | ~~**#250**~~ cerrado el 08-09 (#349); las enmiendas del acta del 11-09 van antes del driver; la Nucleo (#231) para medir |

La fase A es donde vive toda la política y todos los tests que la spec §7
enumera. La fase B es transporte, y sin placa no se puede verificar de todos
modos (spec §9, riesgos 1, 2, 5 y 8 cierran todos «en el bring-up»).

**Este plan cubre la fase A entera y deja la B escrita hasta donde se puede
escribir sin chip.**

---

## Global Constraints

Copiadas literalmente de la spec §4. Los requisitos de cada tarea las incluyen
implícitamente.

- **R-MJ1.** Ninguna transferencia del J2 en el cerebro corre con `TSIZE = 0`.
  Falla al compilar: `TSIZE` sale de un `NonZeroU16`. Y `TSIZE` es el largo
  clocado de la cabecera §4, con relleno.
- **R-MJ2.** Ninguna espera del J2 en el cerebro es un bucle síncrono **sin
  cota**.
- **R-MJ3.** El reinicio del periférico sigue los ocho pasos de D4 en ese orden,
  y cada paso cita su página. No se escribe a `TXDR` para desatascar.
- **R-MJ4.** Los umbrales de D3 y D7 son parámetros, no literales. Viven en un
  solo `struct Umbrales` con sus valores ESTIMADO y su fuente, y
  `recuperacion_j2_budget.py` los **lee** de `maestro_j2.rs`, no los copia.
- **R-MJ5.** Cada ranura activa tiene su tarea, y las seis viven en el ejecutor
  del J2, no en el de hilo.
- **R-MJ6.** Una ranura sin identidad no se cloca ni se cuenta.
- **R-MJ7.** Los búferes de DMA del J2 están en memoria no cacheable o se
  invalidan antes de leerse. **Este plan elige: región MPU no cacheable**
  (tarea 7), porque la invalidación explícita hay que acertarla en cada camino
  de error y el reinicio de D4 tiene ocho.
- **R-MJ8.** El bring-up registra la resistencia en
  `software/nucleo/fw/resistencia_j2.csv`, y el presupuesto sale con `HUECO`
  hasta que haya fila.

**Cifras que este plan NO inventa** (todas ESTIMADO en la spec §3, y así van
marcadas en el código):

| Constante | Valor | Fuente |
|---|---|---|
| `FACTOR_PLAZO` | 2 | ESTIMADO, spec D3 |
| `T_SUELO_PLAZO_US` | 20 | ESTIMADO, spec D3 |
| `VENTANA_SALUD_US` | 1 000 000 | ESTIMADO, spec D7.3 |
| `UMBRAL_INESTABLE` | 10 | ESTIMADO, spec D7.3 |
| `UMBRAL_MUDA` | 40 | ESTIMADO, spec D7.3 (5 ms a 8 kHz) |
| `PERIODO_GIRO_US` | 125 | `trama_j2_budget.F_LAZO_HZ` = 8 kHz |
| `T_WATCHDOG_TRAMA_US` | 50 000 | voz-total §9.2, ESTIMADO (*«N del plan»*) |
| `T_REINICIO_US` | 20 | ESTIMADO, spec §3 |

---

## File Structure

| Archivo | Responsabilidad |
|---|---|
| `software/nucleo/core/src/maestro_j2.rs` | **Nuevo.** Umbrales, `Tsize`, la máquina por ranura, el banco de seis. Todo `no_std`, sin `async`, sin hardware |
| `software/nucleo/core/src/lib.rs` | **Modificar.** `pub mod maestro_j2;` |
| `hardware/02-midi-cv/recuperacion_j2_budget.py` | **Nuevo.** Lee `Umbrales` de `maestro_j2.rs` por regex; asevera plazo, recuperación y margen |
| `software/nucleo/fw/resistencia_j2.csv` | **Nuevo.** Cabecera sola hasta la Discovery |
| `software/nucleo/fw/src/j2_spi.rs` | **Fase B, bloqueado por #250** |

Todos los tests de `maestro_j2.rs` van **en el mismo archivo**, en `#[cfg(test)]
mod tests`, que es como lo hacen `pinout.rs`, `bahia.rs` y el resto de `core`.

---

### Task 1: `Umbrales` y `Tsize` — los tipos que hacen imposible lo prohibido

**Files:**
- Create: `software/nucleo/core/src/maestro_j2.rs`
- Modify: `software/nucleo/core/src/lib.rs` (una línea)

**Interfaces:**
- Produces: `Umbrales`, `Umbrales::nuevos(...) -> Option<Umbrales>`, `Umbrales::POR_DEFECTO`, `Tsize`, `Tsize::nuevo(u16) -> Option<Tsize>`, y las constantes `PERIODO_GIRO_US`, `T_WATCHDOG_TRAMA_US`, `VENTANA_MAX`.

- [ ] **Step 1: Escribir el test que falla** (spec §7 test 10)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn umbrales_rechazan_lo_que_no_sirve_para_avisar() {
        // La marca `muda` tiene que subir ANTES de que el modulo suelte las
        // notas, o no sirve de aviso: es todo su trabajo (spec D7.3).
        assert!(Umbrales::nuevos(2, 20, 1_000_000, 10, 40).is_some());

        // 400 giros x 125 us = 50 ms = la ventana del modulo, justo. No vale:
        // la marca subiria a la vez que el release, no antes.
        assert!(Umbrales::nuevos(2, 20, 1_000_000, 10, 400).is_none());

        // Un umbral_inestable que no cabe en el anillo de la ventana.
        assert!(Umbrales::nuevos(2, 20, 1_000_000, VENTANA_MAX as u32 + 1, 40)
            .is_none());

        // R-MJ1 en el tipo: TSIZE cero no se puede construir.
        assert!(Tsize::nuevo(0).is_none());
        assert!(Tsize::nuevo(25).is_some());
    }
}
```

- [ ] **Step 2: Correr el test y verlo fallar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: FAIL — `maestro_j2` no existe.

- [ ] **Step 3: Escribir los tipos**

```rust
//! El maestro del J2: plazo, reinicio y cuenta, porque el silicio se cuelga.
//!
//! Spec: `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`.
//!
//! Aqui vive la POLITICA y nada mas: que hace el cerebro cuando una
//! transferencia del J2 no termina. El driver que cloca los bytes vive en
//! `fw/src/j2_spi.rs` y no sabe nada del sobre; esta frontera es de D8 y es
//! dura: si la semantica del sobre aparece alli, es un defecto.
//!
//! Nada de este modulo toca hardware ni usa `async`. Se prueba entero en el
//! host, que es lo que pedia `fw/src/main.rs:6` ("Capa DELGADA a proposito").

use core::num::NonZeroU16;

/// Periodo de un giro del lazo. `trama_j2_budget.F_LAZO_HZ` = 8 kHz.
pub const PERIODO_GIRO_US: u32 = 125;

/// Ventana del watchdog de trama del modulo. voz-total sec.9.2, y es
/// **ESTIMADO**: el papel dice "sin trama valida en N ms (N del plan, ~50)".
/// Su cota superior -- cuanto sustain fantasma es tolerable -- no esta escrita
/// en ningun papel y es HUECO de voz-total (spec sec.3).
pub const T_WATCHDOG_TRAMA_US: u32 = 50_000;

/// Cuantos instantes de plazo vencido guarda el anillo de la ventana. Acota
/// `umbral_inestable` por construccion; 16 sobra para el 10 ESTIMADO.
pub const VENTANA_MAX: usize = 16;

/// El largo clocado de una trama, que es `TSIZE` (spec D1).
///
/// R-MJ1 vive en este tipo: no hay forma de construir un cero, asi que no hay
/// forma de armar una transferencia con `TSIZE = 0`. El manual ata el NSS por
/// hardware al contador (RM0486 sec.67.4.7, p. 3437), asi que un cero no seria
/// una transferencia lenta: seria un NSS que no baja.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Tsize(NonZeroU16);

impl Tsize {
    pub const fn nuevo(bytes: u16) -> Option<Tsize> {
        match NonZeroU16::new(bytes) {
            Some(n) => Some(Tsize(n)),
            None => None,
        }
    }

    pub const fn get(self) -> u16 {
        self.0.get()
    }
}

/// Los umbrales de D3 y D7. R-MJ4: son parametros, no literales, y viven todos
/// aqui para que `recuperacion_j2_budget.py` los LEA en vez de copiarlos.
///
/// Todos los valores por defecto son ESTIMADO y el bring-up los sella
/// (spec sec.9, riesgo 2).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Umbrales {
    /// D3. Multiplica el tiempo nominal de la trama. ESTIMADO = 2.
    pub factor_plazo: u32,
    /// D3. Suelo del plazo, para que un `HOLA` corto no tenga un plazo de 4 us.
    /// ESTIMADO = 20 us.
    pub t_suelo_plazo_us: u32,
    /// D7.3. Ventana deslizante de `inestable`. ESTIMADO = 1 s.
    pub ventana_salud_us: u32,
    /// D7.3. Plazos vencidos en la ventana que ponen `inestable`. ESTIMADO = 10.
    pub umbral_inestable: u32,
    /// D7.3. Subidas malas SEGUIDAS que ponen `muda`. ESTIMADO = 40 (5 ms).
    pub umbral_muda: u32,
}

impl Umbrales {
    /// Los ESTIMADO de la spec sec.3. No es `Default` a proposito: que se lea
    /// el nombre en el sitio de uso.
    pub const POR_DEFECTO: Umbrales = Umbrales {
        factor_plazo: 2,
        t_suelo_plazo_us: 20,
        ventana_salud_us: 1_000_000,
        umbral_inestable: 10,
        umbral_muda: 40,
    };

    /// Devuelve `None` si los umbrales no pueden hacer su trabajo.
    ///
    /// Las dos cotas no son gusto:
    ///
    /// * `umbral_muda` x `PERIODO_GIRO_US` < `T_WATCHDOG_TRAMA_US`. La marca
    ///   `muda` existe para avisar de un modulo que no contesta. Si tarda mas
    ///   que el propio watchdog del modulo, el modulo ya solto las notas y la
    ///   marca llega de luto.
    /// * `umbral_inestable` <= `VENTANA_MAX`, porque el anillo que mide la
    ///   ventana tiene ese tamano.
    pub const fn nuevos(
        factor_plazo: u32,
        t_suelo_plazo_us: u32,
        ventana_salud_us: u32,
        umbral_inestable: u32,
        umbral_muda: u32,
    ) -> Option<Umbrales> {
        if umbral_muda == 0 || umbral_inestable == 0 || factor_plazo == 0 {
            return None;
        }
        if umbral_muda * PERIODO_GIRO_US >= T_WATCHDOG_TRAMA_US {
            return None;
        }
        if umbral_inestable > VENTANA_MAX as u32 {
            return None;
        }
        Some(Umbrales {
            factor_plazo,
            t_suelo_plazo_us,
            ventana_salud_us,
            umbral_inestable,
            umbral_muda,
        })
    }
}
```

Y en `lib.rs`, en orden alfabético entre `j2` y `medidas`:

```rust
pub mod maestro_j2;
```

- [ ] **Step 4: Correr el test y verlo pasar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: PASS, 1 test.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo/core/src/maestro_j2.rs software/nucleo/core/src/lib.rs
git commit -m "El maestro del J2 tiene tipos que hacen imposible TSIZE cero y una marca que avisa tarde"
```

---

### Task 2: El plazo, que sale de la trama y no de un número redondo

**Files:**
- Modify: `software/nucleo/core/src/maestro_j2.rs`

**Interfaces:**
- Consumes: `Umbrales`, `Tsize` (tarea 1).
- Produces: `plazo_us(tsize: Tsize, f_reloj_hz: u32, u: &Umbrales) -> u32`.

- [ ] **Step 1: Escribir el test que falla**

```rust
#[test]
fn el_plazo_sale_de_la_trama_y_respeta_su_cota() {
    let u = Umbrales::POR_DEFECTO;

    // Un HOLA de 9 bytes al piso de 10 MHz son 7.2 us nominales; con factor 2
    // serian 14.4, por debajo del suelo. El suelo manda (spec D3).
    let hola = Tsize::nuevo(9).unwrap();
    assert_eq!(plazo_us(hola, 10_000_000, &u), 20);

    // El mensaje mas largo de la cabecera al piso: R-E1 dice que ningun
    // mensaje pasa de 100 us, asi que el plazo no pasa de 2x100 + 20 = 220.
    let largo = Tsize::nuevo(125).unwrap(); // 125 B x 8 / 10 MHz = 100 us
    assert_eq!(plazo_us(largo, 10_000_000, &u), 220);

    // La cota de R-E1, aseverada: NINGUN tsize que respete los 100 us
    // nominales al piso puede pedir mas de 220 us de plazo.
    for bytes in 1..=125u16 {
        let t = Tsize::nuevo(bytes).unwrap();
        assert!(plazo_us(t, 10_000_000, &u) <= 220);
    }

    // Mas reloj, menos plazo -- pero nunca por debajo del suelo.
    let a_34_5 = plazo_us(largo, 34_500_000, &u);
    assert!(a_34_5 < 220 && a_34_5 >= u.t_suelo_plazo_us);
}
```

- [ ] **Step 2: Correr el test y verlo fallar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: FAIL — `plazo_us` no existe.

- [ ] **Step 3: Escribir la función**

```rust
/// El plazo de una transferencia, en microsegundos (spec D3).
///
/// ```text
/// plazo(msg) = FACTOR_PLAZO x t_nominal(msg) + T_SUELO_PLAZO
/// t_nominal(msg) = bytes_clocados(msg) x 8 / f_reloj_sancionado(ranura)
/// ```
///
/// `bytes_clocados` es el mismo numero que `TSIZE` (D1): sobre + carga + CRC +
/// cola, con el relleno de la ventana del dialecto. Por eso el argumento es un
/// `Tsize` y no un `u16` suelto -- si son dos numeros distintos, uno esta mal.
///
/// El suelo evita que un mensaje corto tenga un plazo tan apretado que un
/// retraso de ISR lo venza: sin el, un `HOLA` de 9 bytes a 34,5 MHz (2,1 us)
/// tendria 4 us de plazo.
pub fn plazo_us(tsize: Tsize, f_reloj_hz: u32, u: &Umbrales) -> u32 {
    // Redondeo hacia arriba: un plazo corto por truncamiento produce
    // reinicios de tramas sanas, que es el riesgo 2 de la spec.
    let bits = tsize.get() as u64 * 8;
    let mhz = f_reloj_hz as u64;
    let t_nominal_us = (bits * 1_000_000).div_ceil(mhz);
    (u.factor_plazo as u64 * t_nominal_us + u.t_suelo_plazo_us as u64) as u32
}
```

- [ ] **Step 4: Correr el test y verlo pasar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: PASS, 2 tests.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo/core/src/maestro_j2.rs
git commit -m "El plazo del J2 sale del largo clocado y del reloj sancionado, con su suelo"
```

---

### Task 3: La máquina por ranura — estados, eventos y contadores

**Files:**
- Modify: `software/nucleo/core/src/maestro_j2.rs`

**Interfaces:**
- Consumes: `Umbrales` (tarea 1).
- Produces: `Estado`, `Evento`, `Accion`, `Ranura`, `Ranura::nueva(Umbrales)`, `Ranura::paso(&mut self, Evento, ahora_us: u64) -> Accion`, y los getters `giros()`, `plazos_vencidos()`, `eot_tardios()`, `subidas_ok()`, `subidas_malas()`, `estado()`.

Cubre los tests 1, 2, 3, 4, 5 y 9 de la spec §7.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
fn activa() -> Ranura {
    let mut r = Ranura::nueva(Umbrales::POR_DEFECTO);
    r.paso(Evento::Identidad(true), 0);
    r
}

#[test]
fn vacia_no_cloca_ni_cuenta() {
    let mut r = Ranura::nueva(Umbrales::POR_DEFECTO);
    assert_eq!(r.estado(), Estado::Vacia);
    for ev in [Evento::Armada, Evento::GiroOk, Evento::PlazoVencido,
               Evento::EotTardio, Evento::SubidaOk, Evento::SubidaMala] {
        assert_eq!(r.paso(ev, 0), Accion::Nada);
    }
    assert_eq!(r.giros(), 0);
    assert_eq!(r.plazos_vencidos(), 0);
    assert_eq!(r.subidas_malas(), 0);
    assert_eq!(r.estado(), Estado::Vacia);
}

#[test]
fn la_identidad_activa_y_vacia_sin_borrar_la_cuenta() {
    let mut r = activa();
    assert_eq!(r.estado(), Estado::Activa);
    r.paso(Evento::GiroOk, 0);
    assert_eq!(r.giros(), 1);

    // Los contadores son totales DESDE EL ARRANQUE, no desde la identidad
    // (spec sec.7 test 2).
    r.paso(Evento::Identidad(false), 0);
    assert_eq!(r.estado(), Estado::Vacia);
    assert_eq!(r.giros(), 1);

    r.paso(Evento::Identidad(true), 0);
    assert_eq!(r.estado(), Estado::Activa);
    assert_eq!(r.giros(), 1);
}

#[test]
fn cada_evento_cuenta_lo_suyo() {
    let mut r = activa();
    r.paso(Evento::GiroOk, 0);
    r.paso(Evento::SubidaOk, 0);
    r.paso(Evento::SubidaMala, 0);
    assert_eq!((r.giros(), r.subidas_ok(), r.subidas_malas()), (1, 1, 1));
}

#[test]
fn plazo_vencido_reinicia_y_eot_tardio_no() {
    let mut r = activa();

    assert_eq!(r.paso(Evento::PlazoVencido, 0), Accion::Reiniciar);
    assert_eq!(r.plazos_vencidos(), 1);

    // No hay estado intermedio del que salir: el giro siguiente cuenta como
    // siempre (spec sec.7 test 4).
    assert_eq!(r.paso(Evento::GiroOk, PERIODO_GIRO_US as u64), Accion::Nada);
    assert_eq!(r.giros(), 1);

    // Un EOT que llega tarde pertenece a una generacion vieja: se descarta y
    // se cuenta, pero esa trama SI salio al cable, asi que no se reinicia
    // nada (spec D2 regla 1).
    assert_eq!(r.paso(Evento::EotTardio, 0), Accion::Nada);
    assert_eq!(r.eot_tardios(), 1);
}

#[test]
fn los_contadores_no_bajan_nunca() {
    let mut r = activa();
    let evs = [Evento::GiroOk, Evento::PlazoVencido, Evento::EotTardio,
               Evento::SubidaOk, Evento::SubidaMala, Evento::Armada,
               Evento::Identidad(false), Evento::Identidad(true)];
    let mut previo = (0u32, 0u32, 0u32, 0u32, 0u32);
    let mut t = 0u64;
    for vuelta in 0..40 {
        let ev = evs[vuelta % evs.len()];
        r.paso(ev, t);
        t += PERIODO_GIRO_US as u64;
        let ahora = (r.giros(), r.plazos_vencidos(), r.eot_tardios(),
                     r.subidas_ok(), r.subidas_malas());
        assert!(ahora.0 >= previo.0 && ahora.1 >= previo.1
                && ahora.2 >= previo.2 && ahora.3 >= previo.3
                && ahora.4 >= previo.4,
                "un contador bajo en la vuelta {vuelta}");
        previo = ahora;
    }
}
```

- [ ] **Step 2: Correr los tests y verlos fallar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: FAIL — `Ranura` no existe.

- [ ] **Step 3: Escribir la máquina**

```rust
/// Los dos estados de una ranura (spec D7.4).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Estado {
    /// Sin identidad por I2C. No se cloca, no se cuenta, no tiene marcas.
    /// Sin esto, cada ranura vacia contaria `subidas_malas` a 8 kHz y daria
    /// la vuelta al `u32` en seis dias de instrumento encendido (S-15).
    Vacia,
    Activa,
}

/// Lo que le pasa a una ranura. Los nombres son los de la spec D8.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Evento {
    /// El descubrimiento por I2C le dio o le quito identidad.
    Identidad(bool),
    /// Se armo una transferencia. Es el sello de vitalidad que el J2 le
    /// aporta al supervisor del hub (D5.4): se escribe al ARMAR, no al
    /// completar, porque una ranura reiniciando tambien esta viva.
    Armada,
    /// Mi periferico termino la transferencia.
    GiroOk,
    /// El plazo vencio sin que terminara.
    PlazoVencido,
    /// Llego un `EOT` de una generacion vieja, despues de vencido el plazo.
    EotTardio,
    /// El sobre que subio el modulo tenia CRC bueno.
    SubidaOk,
    /// El sobre que subio el modulo tenia CRC malo, o el modulo no contesto.
    SubidaMala,
    /// Pasa el tiempo sin que ocurra nada. Deja deslizar la ventana.
    Tick,
}

/// Lo unico que la politica puede mandar hacer.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Accion {
    Nada,
    /// Los ocho pasos de D4, en orden. Los ejecuta `fw`, no `core`.
    Reiniciar,
}

/// Una ranura del J2, con su politica y sus cinco contadores.
///
/// `giros` mide "mi periferico termino"; `subidas_ok` mide "el modulo
/// contesto". Son dos cosas distintas y por eso se cuentan aparte (D7.3): un
/// modulo muerto con el MISO en pull-down da `EOT` perfecto y ceros.
#[derive(Clone, Copy, Debug)]
pub struct Ranura {
    umbrales: Umbrales,
    estado: Estado,
    giros: u32,
    plazos_vencidos: u32,
    eot_tardios: u32,
    subidas_ok: u32,
    subidas_malas: u32,
    malas_seguidas: u32,
    /// Anillo con los instantes de los ultimos plazos vencidos. Solo hacen
    /// falta `umbral_inestable`, y `VENTANA_MAX` los acota.
    ultimos: [u64; VENTANA_MAX],
    n_ultimos: usize,
    ahora_us: u64,
}

impl Ranura {
    pub const fn nueva(umbrales: Umbrales) -> Ranura {
        Ranura {
            umbrales,
            estado: Estado::Vacia,
            giros: 0,
            plazos_vencidos: 0,
            eot_tardios: 0,
            subidas_ok: 0,
            subidas_malas: 0,
            malas_seguidas: 0,
            ultimos: [0; VENTANA_MAX],
            n_ultimos: 0,
            ahora_us: 0,
        }
    }

    pub fn paso(&mut self, ev: Evento, ahora_us: u64) -> Accion {
        self.ahora_us = ahora_us;

        // La identidad se atiende siempre: es lo unico que saca de `Vacia`.
        if let Evento::Identidad(presente) = ev {
            self.estado = if presente { Estado::Activa } else { Estado::Vacia };
            return Accion::Nada;
        }

        // R-MJ6: una ranura sin identidad no se cloca ni se cuenta.
        if self.estado == Estado::Vacia {
            return Accion::Nada;
        }

        match ev {
            Evento::GiroOk => {
                self.giros += 1;
                Accion::Nada
            }
            Evento::PlazoVencido => {
                self.plazos_vencidos += 1;
                self.anota_plazo(ahora_us);
                Accion::Reiniciar
            }
            Evento::EotTardio => {
                self.eot_tardios += 1;
                Accion::Nada
            }
            Evento::SubidaOk => {
                self.subidas_ok += 1;
                self.malas_seguidas = 0;
                Accion::Nada
            }
            Evento::SubidaMala => {
                self.subidas_malas += 1;
                self.malas_seguidas += 1;
                Accion::Nada
            }
            Evento::Armada | Evento::Tick => Accion::Nada,
            Evento::Identidad(_) => unreachable!("atendido arriba"),
        }
    }

    fn anota_plazo(&mut self, ahora_us: u64) {
        if self.n_ultimos < VENTANA_MAX {
            self.ultimos[self.n_ultimos] = ahora_us;
            self.n_ultimos += 1;
        } else {
            self.ultimos.rotate_left(1);
            self.ultimos[VENTANA_MAX - 1] = ahora_us;
        }
    }

    pub fn estado(&self) -> Estado { self.estado }
    pub fn giros(&self) -> u32 { self.giros }
    pub fn plazos_vencidos(&self) -> u32 { self.plazos_vencidos }
    pub fn eot_tardios(&self) -> u32 { self.eot_tardios }
    pub fn subidas_ok(&self) -> u32 { self.subidas_ok }
    pub fn subidas_malas(&self) -> u32 { self.subidas_malas }
}
```

- [ ] **Step 4: Correr los tests y verlos pasar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: PASS, 7 tests.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo/core/src/maestro_j2.rs
git commit -m "La ranura del J2 cuenta cinco cosas y solo sabe reiniciar"
```

---

### Task 4: Las dos marcas — `inestable` y `muda`

**Files:**
- Modify: `software/nucleo/core/src/maestro_j2.rs`

**Interfaces:**
- Consumes: `Ranura` (tarea 3).
- Produces: `Ranura::inestable(&self) -> bool`, `Ranura::muda(&self) -> bool`.

Cubre los tests 6, 7 y 8 de la spec §7.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[test]
fn inestable_sube_al_decimo_en_un_segundo_y_baja_al_deslizar() {
    let mut r = activa();
    let u = Umbrales::POR_DEFECTO;

    // Nueve juntos no la suben; el decimo si (spec sec.7 test 6: "el decimo
    // cabe justo, el noveno no").
    for i in 0..(u.umbral_inestable - 1) {
        r.paso(Evento::PlazoVencido, i as u64 * 1000);
        assert!(!r.inestable(), "subio con {}", i + 1);
    }
    r.paso(Evento::PlazoVencido, (u.umbral_inestable - 1) as u64 * 1000);
    assert!(r.inestable());

    // Y baja cuando la ventana desliza mas alla del mas viejo.
    r.paso(Evento::Tick, u.ventana_salud_us as u64 + 1);
    assert!(!r.inestable());
}

#[test]
fn inestable_no_sube_si_estan_repartidos_en_mas_de_un_segundo() {
    let mut r = activa();
    let u = Umbrales::POR_DEFECTO;
    // Diez, pero uno cada 200 ms: nunca hay diez dentro de la misma ventana.
    for i in 0..u.umbral_inestable {
        r.paso(Evento::PlazoVencido, i as u64 * 200_000);
        assert!(!r.inestable(), "subio en el {}", i + 1);
    }
}

#[test]
fn muda_sube_a_las_cuarenta_seguidas_y_baja_con_una_buena() {
    let mut r = activa();
    let u = Umbrales::POR_DEFECTO;
    for i in 0..(u.umbral_muda - 1) {
        r.paso(Evento::SubidaMala, i as u64 * PERIODO_GIRO_US as u64);
        assert!(!r.muda());
    }
    r.paso(Evento::SubidaMala, 0);
    assert!(r.muda());

    r.paso(Evento::SubidaOk, 0);
    assert!(!r.muda(), "una subida buena la baja: son SEGUIDAS");
}

#[test]
fn las_marcas_nunca_cambian_la_accion() {
    let mut r = activa();
    let u = Umbrales::POR_DEFECTO;
    for i in 0..u.umbral_muda {
        r.paso(Evento::SubidaMala, i as u64 * 10);
    }
    for i in 0..u.umbral_inestable {
        r.paso(Evento::PlazoVencido, i as u64 * 10);
    }
    assert!(r.inestable() && r.muda());

    // Con las dos marcas puestas, la accion es la de siempre (spec sec.7
    // test 8): las marcas son informacion, no politica.
    assert_eq!(r.paso(Evento::PlazoVencido, 0), Accion::Reiniciar);
    assert_eq!(r.paso(Evento::GiroOk, 0), Accion::Nada);
}
```

- [ ] **Step 2: Correr los tests y verlos fallar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: FAIL — `inestable` y `muda` no existen.

- [ ] **Step 3: Escribir las marcas**

```rust
impl Ranura {
    /// Muchos plazos vencidos en poco tiempo. **Es informacion, no accion**:
    /// no cambia lo que la tarea hace (spec D7.3). La v1 de la spec la usaba
    /// para bajar la cadencia y la junta lo tumbo: bajar la cadencia garantiza
    /// el release del modulo, que es justo lo que se queria evitar.
    pub fn inestable(&self) -> bool {
        let n = self.umbrales.umbral_inestable as usize;
        if self.n_ultimos < n {
            return false;
        }
        // El n-esimo mas reciente. Si cabe en la ventana, hay n dentro.
        let mas_viejo = self.ultimos[self.n_ultimos - n];
        self.ahora_us.saturating_sub(mas_viejo)
            <= self.umbrales.ventana_salud_us as u64
    }

    /// El modulo lleva muchas subidas seguidas sin contestar bien. Es el
    /// testigo que la v1 no tenia (V-10): un modulo muerto da `EOT` perfecto
    /// en el maestro y ceros en el MISO, asi que `giros` no lo ve y esto si.
    pub fn muda(&self) -> bool {
        self.malas_seguidas >= self.umbrales.umbral_muda
    }
}
```

- [ ] **Step 4: Correr los tests y verlos pasar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: PASS, 11 tests.

- [ ] **Step 5: Commit**

```bash
git add software/nucleo/core/src/maestro_j2.rs
git commit -m "Las dos marcas de salud del J2 suben y no mandan nada"
```

---

### Task 5: El banco de seis ranuras independientes

**Files:**
- Modify: `software/nucleo/core/src/maestro_j2.rs`

**Interfaces:**
- Consumes: `Ranura` (tareas 3-4).
- Produces: `RANURAS_SPI: usize = 6`, `Maestro`, `Maestro::nuevo(Umbrales)`, `Maestro::paso(&mut self, usize, Evento, u64) -> Accion`, `Maestro::ranura(&self, usize) -> Option<&Ranura>`.

Cubre el test 11 de la spec §7 (mutación).

- [ ] **Step 1: Escribir el test que falla**

```rust
#[test]
fn las_seis_ranuras_son_independientes() {
    let mut m = Maestro::nuevo(Umbrales::POR_DEFECTO);
    for r in 0..RANURAS_SPI {
        m.paso(r, Evento::Identidad(true), 0);
    }

    // Un plazo vencido en la 3 no toca ninguna cuenta de las otras cinco.
    assert_eq!(m.paso(3, Evento::PlazoVencido, 0), Accion::Reiniciar);
    for r in 0..RANURAS_SPI {
        let esperado = if r == 3 { 1 } else { 0 };
        assert_eq!(m.ranura(r).unwrap().plazos_vencidos(), esperado,
                   "la ranura {r} se entero de un plazo ajeno");
    }

    // Y una ranura fuera de rango no existe ni panica.
    assert_eq!(m.paso(RANURAS_SPI, Evento::GiroOk, 0), Accion::Nada);
    assert!(m.ranura(RANURAS_SPI).is_none());
}
```

- [ ] **Step 2: Correr el test y verlo fallar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: FAIL — `Maestro` no existe.

- [ ] **Step 3: Escribir el banco**

```rust
/// Las ranuras del J2 por SPI. Las dos por USART sincrono quedan fuera con su
/// HUECO (spec sec.0): son otro periferico con otra maquina de estados, y el
/// planificador las trata como `Vacia` hasta que tengan papel (riesgo 7).
pub const RANURAS_SPI: usize = 6;

/// Las seis ranuras. Cada una con su maquina; ninguna sabe de las otras.
///
/// La independencia no es elegancia: un plazo vencido en una ranura no puede
/// retrasar a las otras cinco (spec D5.1), y la cuenta de salud es por ranura
/// para que un cuelgue en una no ensucie la ventana de las demas (H-1).
#[derive(Clone, Copy, Debug)]
pub struct Maestro {
    ranuras: [Ranura; RANURAS_SPI],
}

impl Maestro {
    pub const fn nuevo(umbrales: Umbrales) -> Maestro {
        Maestro { ranuras: [Ranura::nueva(umbrales); RANURAS_SPI] }
    }

    /// Fuera de rango no hace nada, como `bahia.rs` y `partes.rs`: el rango lo
    /// valida quien despacha, y un panico en el N657 es un reset del
    /// instrumento.
    pub fn paso(&mut self, ranura: usize, ev: Evento, ahora_us: u64) -> Accion {
        match self.ranuras.get_mut(ranura) {
            Some(r) => r.paso(ev, ahora_us),
            None => Accion::Nada,
        }
    }

    pub fn ranura(&self, ranura: usize) -> Option<&Ranura> {
        self.ranuras.get(ranura)
    }
}
```

- [ ] **Step 4: Correr el test y verlo pasar**

Run: `cargo test -p sam17-nucleo-core maestro_j2`
Expected: PASS, 12 tests.

- [ ] **Step 5: Correr la suite entera y las puertas**

```bash
cargo test -p sam17-nucleo-core
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
```
Expected: todo verde.

- [ ] **Step 6: Commit**

```bash
git add software/nucleo/core/src/maestro_j2.rs
git commit -m "Seis ranuras del J2, cada una con su propia cuenta"
```

---

### Task 6: El presupuesto que lee los umbrales del artefacto

**Files:**
- Create: `hardware/02-midi-cv/recuperacion_j2_budget.py`
- Create: `software/nucleo/fw/resistencia_j2.csv`

**Interfaces:**
- Consumes: `struct Umbrales` de `maestro_j2.rs` (por regex, R-MJ4), `trama_j2_budget.F_LAZO_HZ` y `T_MENSAJE_MAX_S`, `enlace_budget.F_PELDANO_2_HZ`.

Cubre el test 12 de la spec §7.

- [ ] **Step 1: Escribir el CSV vacío**

```
ranura,instancia,tsize,nss,reloj_MHz,horas,giros,plazos_vencidos,eot_tardios,subidas_malas,fecha,placa
```

- [ ] **Step 2: Escribir el presupuesto**

Estructura obligatoria (spec §8):

```python
"""Que le cuesta al musico un cuelgue del SPI, y cuanto margen queda.

    python recuperacion_j2_budget.py

R-MJ4: los umbrales NO se copian, se LEEN de maestro_j2.rs. Si alguien cambia
un ESTIMADO en el Rust y no aqui, este guion se entera. Si alguien renombra el
struct, este guion falla en vez de aseverar sobre aire.
"""
import os
import re
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _AQUI)
import enlace_budget as eb       # noqa: E402
import trama_j2_budget as tb     # noqa: E402

_RS = os.path.join(_AQUI, "..", "..", "software", "nucleo", "core", "src",
                   "maestro_j2.rs")

# ESTIMADO, voz-total sec.9.2 ("N del plan, ~50"). Su cota superior no esta
# escrita en ningun papel: HUECO de voz-total.
T_WATCHDOG_TRAMA_S = 50e-3
# ESTIMADO, spec sec.3: T_SUSP (10 us) + reset del GPDMA (sin cifra) +
# registros. Lo mide el bring-up.
T_REINICIO_S = 20e-6


def umbrales_del_rust(ruta=_RS):
    """Lee POR_DEFECTO de maestro_j2.rs. R-MJ4."""
    with open(ruta, encoding="utf-8") as f:
        txt = f.read()
    m = re.search(r"pub const POR_DEFECTO: Umbrales = Umbrales \{(.+?)\}",
                  txt, re.S)
    if not m:
        raise SystemExit(
            "maestro_j2.rs no expone `POR_DEFECTO: Umbrales`. R-MJ4 dice que "
            "los umbrales viven en un solo sitio y que este guion los LEE: si "
            "el struct cambio de nombre o de forma, arregla el guion, no lo "
            "esquives copiando los numeros.")
    campos = dict(re.findall(r"(\w+):\s*([\d_]+)", m.group(1)))
    return {k: int(v.replace("_", "")) for k, v in campos.items()}
```

Y las aserciones de la spec §8, en este orden:

1. `plazo(msg) <= FACTOR × T_MENSAJE_MAX + SUELO` para cada mensaje, al piso y a D8.
2. `t_recuperacion = plazo_max + T_REINICIO + 2/F_LAZO`, y `t_recuperacion × 10 < T_WATCHDOG_TRAMA` (hoy da 102×).
3. `UMBRAL_MUDA / F_LAZO < T_WATCHDOG_TRAMA`.
4. CPU por reinicios, **impreso sin aserto** (es cota, no presupuesto).
5. `P(golpe perdido) = 3 × p_evento` para `p_evento` en `{1e-3, 1e-2, 1e-1}`, **impresa sin aserto**.
6. `T_IWDG > T_WATCHDOG_TRAMA` como **HUECO impreso**, hasta que el hub lo declare.

Salida: `2` mientras `resistencia_j2.csv` no tenga fila o el hub no declare `T_IWDG`; `0` cuando los dos existan; `1` si algún aserto falla.

- [ ] **Step 3: Correr el guion**

Run: `python hardware/02-midi-cv/recuperacion_j2_budget.py`
Expected: imprime el margen (≈102×) y **sale con código 2** — es correcto, no es un fallo: `resistencia_j2.csv` no tiene fila y el hub no declara `T_IWDG`.

- [ ] **Step 4: Verificar que R-MJ4 muerde**

Cambia a mano `umbral_muda: 40` por `41` en `maestro_j2.rs`, corre el guion y comprueba que la cifra impresa cambia. Deshaz el cambio.

- [ ] **Step 5: Commit**

```bash
git add hardware/02-midi-cv/recuperacion_j2_budget.py software/nucleo/fw/resistencia_j2.csv
git commit -m "El presupuesto de recuperacion del J2 lee los umbrales del Rust y no los copia"
```

---

## Fase B — ~~bloqueada por #250~~ desbloqueada el 2026-09-08

> **Enmienda del 2026-09-11 (acta del J2).** El bloqueo murió el 08-09 (#349):
> `fw` compila contra `embassy-stm32` para el N657 y `j2_spi.rs` existe como
> cabecera desde el #362. La tarea 7 se escribe **después** de las enmiendas del
> acta del 11-09 a la spec (D2: la espera anclada entre `SPE = 1` y `CSTART`;
> §9: la puerta de fabricación y el límite de cero artefactos audibles), con la
> secuencia de D2 enmendada y no con la que cita el contrato de abajo. Orden
> firmado (ficha 3): enmiendas, driver, tarea 8, los tres binarios de
> `EN-PLACA.md`. Sin placa sigue sin poder verificarse: la Nucleo-N657X0-Q se
> compra ahora (ficha 4, #231). Ojo: el cfg del N657 es `spi_v5`, no `spi_v4`.

No se escribieron aquí como tareas con pasos porque **no había dónde compilarlas**.
Quedan enunciadas con su contrato:

### Task 7 (bloqueada): `j2_spi.rs`, el driver con las dos esperas cancelables

Un driver de SPI maestro para `spi_v4`, **genérico**, que no sabe nada del
sobre: recibe búfer de bajada, búfer de subida y largo; devuelve `Ok`,
`PlazoVencido` o `EotTardio`. Lo que tiene que hacer y embassy no hace:

- `TSIZE = N` en cada transferencia y NSS por hardware (`SSM=0`, `SSOE=1`,
  `SSOM=0`), que son una sola decisión (spec D1);
- las **dos** esperas bajo un solo plazo: `join(tx_dma, rx_dma)` y luego el
  futuro de `EOT` por `EOTIE` (spec D2);
- generación por transferencia, resultado borrado al armar, y waker registrado
  antes de mirar la bandera (spec D2, las tres reglas);
- los ocho pasos del reinicio de D4, en orden, cada uno con su página;
- búferes en región MPU no cacheable (R-MJ7, elegido arriba).

Piezas públicas de embassy verificadas en `main` (spec §1.2): `rcc::enable_and_reset`,
`dma::Channel::new`, `Channel::read`/`write`, `spi::TxDma`/`RxDma::request()`,
`embassy_time`, `InterruptExecutor`.

### Task 8 (bloqueada): el ejecutor del J2 y las seis tareas

Seis tareas, una por ranura, en un `InterruptExecutor` propio a prioridad por
encima del ejecutor de hilo donde viven pantalla, USB y MIDI (spec D5.3). Cada
tarea: arma (y escribe su sello de vitalidad), espera bajo plazo, y le pasa el
resultado a su `Ranura` de `core`; si la acción es `Reiniciar`, ejecuta D4.

**El planificador sigue siendo el único escritor del enlace** (R-C8). Las seis
tareas son transporte, como los canales de DMA: no deciden nada del protocolo.

---

## Lo que este plan NO hace, con su dueño

| Qué | Dueño |
|---|---|
| El pase de `fw` a `embassy-stm32` | **#250** |
| Medir los ESTIMADO con osciloscopio | **#231**, la Discovery |
| El supervisor de vitalidad y el ejecutor del hub | **#291** |
| La línea del `SPE=0 → SPE=1` en la ISR del módulo | **#292** |
| Las dos cotas de los 50 ms | **#293** |
| Qué hace el instrumento con una ranura `inestable` o `muda` | El papel de partes y voces |
| El comentario en el hilo #5607 | Sale con la cuenta de Samuel (spec §9, acción 1) |
