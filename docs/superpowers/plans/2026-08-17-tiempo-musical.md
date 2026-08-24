# El instrumento en tiempo musical — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el instrumento sepa dónde está en el compás y que las cosas puedan pedirle que ocurran ahí — reloj con cuatro fuentes, cuantización global, rampas que interpolan según la unidad, y anulado/reactivar.

**Architecture:** Cuatro módulos nuevos en `software/nucleo/core`, todos funciones puras del tiempo: el tiempo entra como argumento, nunca se lee de un reloj. Eso los deja verificables enteros con `cargo test` — igual que el resto del contrato, y por la misma razón: no hay placa.

**Tech Stack:** Rust 1.95 estable, `no_std`, `heapless` 0.8, `libm` 0.2, y **`wmidi` 4.0 con `default-features = false`** — ver «Qué se adopta y qué no».

**Spec:** `docs/superpowers/specs/2026-08-17-tiempo-musical-design.md`

## Global Constraints

Copiadas literales de la spec. Toda tarea las hereda.

- **`no_std` sin excepciones.** `heapless` con capacidad declarada.
- **Las etiquetas de los enumerados son las de Ableton, literales** (§2.1 de la
  spec). Es decisión de diseño, no comodidad: el agente ya conoce ese
  vocabulario y no conoce el nuestro.
- **`SET` es inmediato, siempre** (§5.1). No gana ningún campo. La cuantización
  es para lanzar cosas, no para mover perillas.
- **Nunca adivina en silencio** (§3.4): sin fase, el instrumento aterriza en el
  pulso y lo **dice** con `tiene fase`. No inventa un compás ni se niega a tocar.
- **La interpolación sale de la unidad del descriptor** (§5.2). Nadie la
  configura por parámetro.
- **La cinta sigue corriendo** (§6.2): una rampa anulada no se detiene, deja de
  escribir.
- **Ningún cliente se queda en silencio** salvo los dos silencios declarados en
  `servidor.rs`: `SUBSCRIBE`, y una escritura correcta sin suscriptor.
- **Resolución interna: `PPQN_INTERNO = 96`.** Divisible entre 3 y 4, así que
  tresillos y treintaidosavos caen exactos.
- **Gates:** `cargo test` verde y `cargo clippy --all-targets -- -D warnings`
  limpio en `software/nucleo`; `cargo build --release` en `fw`; y los seis
  `*_budget.py` del repo en verde, más el nuevo.
- **Nombres y comentarios en español.** Los que ve el agente se escriben para
  alguien que nunca ha visto el instrumento.
- Commits en español contando el porqué, con el trailer de coautoría del repo.

## Qué se adopta y qué no

Buscado en crates.io antes de escribir nada. **Un acierto, un apunte para
después, y tres rechazos con su razón** — porque «no reinventes» no significa
«mete cualquier cosa».

### Se adopta: `wmidi` 4.0

Para decodificar los mensajes de tiempo real de MIDI. Verificado: **`no_std`,
sin asignaciones al parsear o codificar, y realtime-safe**; es de RustAudio.
Trae exactamente lo que hace falta:

```rust
MidiMessage::{ TimingClock, Start, Stop, Continue, SongPositionPointer(SongPosition) }
MidiMessage::from_bytes(&[u8]) -> Result<Self, Error>
```

Y `SongPosition` **ya es el tipo de 14 bits** — los dos bytes de 7 bits
ensamblados. Hacerlo a mano son treinta líneas de emparejar bytes de estado y
armar enteros, que es justo donde se cuela un error silencioso.

En `core/Cargo.toml`:

```toml
wmidi = { version = "4.0", default-features = false }
```

`std` es su única feature y va por defecto: **hay que apagarla**.

### Se apunta para después: `ableton-link-rs`

Existe una implementación nativa de Link en Rust (0.1.2, temprana). **No entra
en este plan** —Link corre en el puente, no en el RP2350— pero se anota en
`EN-PLACA.md` para que nadie escriba el protocolo desde cero el día que el
puente exista. Y abre la puerta a que el puente también sea Rust.

### Se rechazan, con motivo

| Crate | Por qué no |
|---|---|
| `music-timer` | 0.1.6, basado en callbacks y casi seguro con `std`. Y `rejilla.rs` son cuarenta líneas de aritmética modular con semántica **propia**: los valores exactos de Ableton y la regla de la ventana de §5.3. Ninguna librería trae eso |
| `keyframe`, `simple-easing`, `interpolation` | La curva es `t^k`, **una línea** con `libm::powf`. Y lo que de verdad tiene chicha —interpolar en log o lineal **según la unidad del descriptor**— no lo hace ninguna, porque es de este modelo |
| `micromath` | Son aproximaciones rápidas, y `libm` es correcto. El test del barrido exige 400 Hz con ±2 de tolerancia, y el RP2350 tiene FPU por hardware: no hay nada que ganar cambiando precisión por velocidad |

## Estructura de ficheros

| Fichero | De qué responde |
|---|---|
| `core/src/rejilla.rs` | §4 — los valores de cuantización y el cálculo del siguiente borde |
| `core/src/reloj.rs` | §3 — las cuatro fuentes, el seguimiento de tempo, la fase, la rueda libre |
| `core/src/rampa.rs` | §5 y §6 — la interpolación por unidad, la curva, y el anulado |
| `core/src/tiempo_params.rs` | §7.2 — los descriptores del reloj y sus medidas |
| `core/src/protocolo.rs` | +3 mensajes (§7.1) |
| `core/src/descriptor.rs` | +1 marca: «acepta modulación» (§7.3) |
| `core/src/servidor.rs` | Atiende los tres y corre el tick |
| `hardware/02-midi-cv/tiempo_budget.py` | §9 — el presupuesto de aterrizaje |

---

### Task 1: La rejilla

**Files:**
- Create: `software/nucleo/core/src/rejilla.rs`
- Modify: `core/src/lib.rs`

**Interfaces:**
- Produces: `Rejilla` (enum), `PPQN_INTERNO`, `pulsos_por_compas(num, den)`,
  `Rejilla::en_pulsos(pulsos_por_compas)`,
  `siguiente_borde(posicion, rejilla, pulsos_por_compas, ventana) -> Option<u64>`.

**Los valores son los de Ableton, y no todos son compases.** `½`, `¼`, `⅛` y
`1⁄16` son **figuras**, no fracciones del compás: en 4/4 coinciden, en 3/4 no.
Una negra es una negra pase lo que pase.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    const CUATRO_CUARTOS: u32 = 4 * PPQN_INTERNO; // 384

    #[test]
    fn el_compas_sale_de_la_metrica() {
        assert_eq!(pulsos_por_compas(4, 4), CUATRO_CUARTOS);
        assert_eq!(pulsos_por_compas(3, 4), 3 * PPQN_INTERNO);
        assert_eq!(pulsos_por_compas(7, 8), 7 * PPQN_INTERNO / 2);
    }

    #[test]
    fn las_figuras_no_dependen_del_compas() {
        // Una negra es una negra en 4/4 y en 3/4. Solo los COMPASES cambian.
        for pxc in [pulsos_por_compas(4, 4), pulsos_por_compas(3, 4)] {
            assert_eq!(Rejilla::Cuarto.en_pulsos(pxc), PPQN_INTERNO);
            assert_eq!(Rejilla::Mitad.en_pulsos(pxc), 2 * PPQN_INTERNO);
            assert_eq!(Rejilla::Dieciseisavo.en_pulsos(pxc), PPQN_INTERNO / 4);
        }
        assert_eq!(Rejilla::Compas1.en_pulsos(CUATRO_CUARTOS), CUATRO_CUARTOS);
        assert_eq!(Rejilla::Compases4.en_pulsos(CUATRO_CUARTOS), 4 * CUATRO_CUARTOS);
    }

    #[test]
    fn sin_rejilla_no_hay_borde_que_esperar() {
        assert_eq!(siguiente_borde(100, Rejilla::Ninguna, CUATRO_CUARTOS, 0), None);
    }

    #[test]
    fn a_mitad_de_compas_espera_al_siguiente() {
        assert_eq!(
            siguiente_borde(200, Rejilla::Compas1, CUATRO_CUARTOS, 0),
            Some(384)
        );
    }

    #[test]
    fn justo_en_el_borde_cae_en_ese_borde() {
        // §5.3: esperar un compas entero por llegar clavado seria fallar.
        assert_eq!(
            siguiente_borde(384, Rejilla::Compas1, CUATRO_CUARTOS, 0),
            Some(384)
        );
    }

    #[test]
    fn dentro_de_la_ventana_cuenta_como_en_el_borde() {
        // §5.3: la ventana es el error de aterrizaje del sistema. Cualquier
        // cosa que llegue a menos de eso de un borde esta, para todo lo que se
        // puede oir, EN ese borde — aunque llegue tarde.
        let v = 5;
        assert_eq!(siguiente_borde(386, Rejilla::Compas1, CUATRO_CUARTOS, v), Some(386));
        assert_eq!(siguiente_borde(389, Rejilla::Compas1, CUATRO_CUARTOS, v), Some(389));
        // Un pulso mas alla ya es tarde: le toca el siguiente.
        assert_eq!(siguiente_borde(390, Rejilla::Compas1, CUATRO_CUARTOS, v), Some(768));
    }

    #[test]
    fn la_ventana_no_se_come_una_rejilla_corta() {
        // Con 1/16 (24 pulsos) y una ventana de 20, casi todo caeria "ya".
        // Se recorta a la mitad de la rejilla: nunca puede tragarse un borde.
        let g = Rejilla::Dieciseisavo.en_pulsos(CUATRO_CUARTOS);
        assert_eq!(g, 24);
        assert_eq!(siguiente_borde(37, Rejilla::Dieciseisavo, CUATRO_CUARTOS, 20), Some(48));
    }

    #[test]
    fn todas_las_rejillas_dan_un_numero_util() {
        for r in Rejilla::TODAS {
            if r == Rejilla::Ninguna {
                continue;
            }
            assert!(r.en_pulsos(CUATRO_CUARTOS) > 0, "{r:?} da cero pulsos");
        }
    }
}
```

- [ ] **Step 2: Verlo fallar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core rejilla`
Esperado: FAIL, `cannot find type Rejilla`.

- [ ] **Step 3: Implementar**

```rust
//! §4. La cuantizacion global, con los valores de Ableton.
//!
//! Ojo con una trampa del vocabulario: `1/2`, `1/4`, `1/8` y `1/16` son
//! **figuras**, no fracciones del compas. En 4/4 coinciden; en 3/4 no. Una
//! negra es una negra pase lo que pase.

/// Resolucion interna. Divisible entre 3 y 4, asi que tresillos y
/// treintaidosavos caen exactos.
pub const PPQN_INTERNO: u32 = 96;

pub fn pulsos_por_compas(numerador: u32, denominador: u32) -> u32 {
    // Una figura de 1/den dura PPQN*4/den pulsos.
    numerador * PPQN_INTERNO * 4 / denominador.max(1)
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Rejilla {
    Ninguna,
    Compases8,
    Compases4,
    Compases2,
    Compas1,
    Mitad,
    Cuarto,
    Octavo,
    Dieciseisavo,
}

impl Rejilla {
    pub const TODAS: [Rejilla; 9] = [
        Rejilla::Ninguna, Rejilla::Compases8, Rejilla::Compases4,
        Rejilla::Compases2, Rejilla::Compas1, Rejilla::Mitad,
        Rejilla::Cuarto, Rejilla::Octavo, Rejilla::Dieciseisavo,
    ];

    /// Las etiquetas que ve el agente. Son las de Ableton, literales (§2.1).
    pub const ETIQUETAS: &'static [&'static str] = &[
        "ninguna", "8 compases", "4 compases", "2 compases", "1 compas",
        "1/2", "1/4", "1/8", "1/16",
    ];

    pub fn en_pulsos(self, pulsos_por_compas: u32) -> u32 {
        match self {
            Rejilla::Ninguna => 0,
            Rejilla::Compases8 => 8 * pulsos_por_compas,
            Rejilla::Compases4 => 4 * pulsos_por_compas,
            Rejilla::Compases2 => 2 * pulsos_por_compas,
            Rejilla::Compas1 => pulsos_por_compas,
            Rejilla::Mitad => 2 * PPQN_INTERNO,
            Rejilla::Cuarto => PPQN_INTERNO,
            Rejilla::Octavo => PPQN_INTERNO / 2,
            Rejilla::Dieciseisavo => PPQN_INTERNO / 4,
        }
    }
}

/// Donde aterriza algo disparado en `posicion`.
///
/// `None` significa «ya, sin esperar». `ventana` es el error de aterrizaje del
/// sistema (§5.3): lo que llegue a menos de eso DESPUES de un borde se trata
/// como si hubiera llegado en el borde.
pub fn siguiente_borde(
    posicion: u64,
    rejilla: Rejilla,
    pulsos_por_compas: u32,
    ventana: u32,
) -> Option<u64> {
    let g = rejilla.en_pulsos(pulsos_por_compas) as u64;
    if g == 0 {
        return None;
    }
    // La ventana nunca puede tragarse un borde entero: con rejillas cortas se
    // recorta a la mitad, o «llegue tarde» acabaria significando «siempre».
    let ventana = (ventana as u64).min(g / 2);
    let resto = posicion % g;
    if resto <= ventana {
        Some(posicion)
    } else {
        Some(posicion + (g - resto))
    }
}
```

- [ ] **Step 4: Verlo pasar**

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy --all-targets -- -D warnings`
Esperado: 7 tests nuevos PASS.

- [ ] **Step 5: Commit**

```bash
git add -A software/nucleo
git commit -m "La rejilla, con la trampa del vocabulario resuelta: 1/4 es una negra, no un cuarto de compas"
```

---

### Task 2: El seguidor de tempo

**Files:**
- Create: `software/nucleo/core/src/reloj.rs` (solo el seguidor; el resto es Task 3)
- Modify: `core/src/lib.rs`

**Interfaces:**
- Produces: `SeguidorTempo` (`nuevo`, `pulso(t_us)`, `mbpm()`, `estable()`),
  `VENTANA_TEMPO`.

**El hallazgo que cambia esta tarea.** La spec §3.6 dice que el MIDI clock
*«necesita un lazo de enganche, y es trabajo real que hay que presupuestar»*.
**No lo necesita.** Se hizo la cuenta contra el objetivo de §9 —±2 ms de jitter,
la lectura no se mueve más de ±0.1 BPM— y da esto:

| Método | Error a 120 BPM | Coste |
|---|---|---|
| EMA, α = 0.05 | 1.506 BPM | τ = 0.4 s |
| EMA, α = 0.01 | 0.667 BPM | τ = 2.1 s |
| EMA, α = 0.001 | 0.210 BPM | **τ = 20.8 s** — y aún no llega |
| **Extremos, N = 96** | **0.098 BPM** | **ventana de 2.0 s** |

Un promedio móvil sobre intervalos consecutivos **no llega ni con una constante
de 21 segundos**, porque promediar reduce el ruido con `√α` mientras que alargar
la base lo reduce con `N`. Medir contra un pulso de hace 96 en vez de contra el
anterior es un búfer circular y una resta.

**N = 96 y a 24 PPQN son cuatro negras: un compás de 4/4.** No se eligió por
musical, salió del número — pero conviene.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    /// Genera marcas de tiempo de pulsos a un tempo dado, con jitter uniforme
    /// reproducible.
    struct Fuente { t_us: u64, intervalo_us: u64, r: u64 }
    impl Fuente {
        fn nueva(bpm: f64, ppqn: u32, semilla: u64) -> Self {
            Fuente {
                t_us: 1_000_000,
                intervalo_us: (60.0 / bpm / ppqn as f64 * 1e6) as u64,
                r: semilla | 1,
            }
        }
        /// Devuelve la marca del siguiente pulso, corrida +-jitter_us.
        fn siguiente(&mut self, jitter_us: u64) -> u64 {
            self.t_us += self.intervalo_us;
            if jitter_us == 0 {
                return self.t_us;
            }
            self.r ^= self.r << 13;
            self.r ^= self.r >> 7;
            self.r ^= self.r << 17;
            let d = (self.r >> 40) % (2 * jitter_us + 1);
            self.t_us + d - jitter_us
        }
    }

    fn correr(bpm: f64, jitter_us: u64, pulsos: usize) -> SeguidorTempo {
        let mut f = Fuente::nueva(bpm, 24, 7);
        let mut s = SeguidorTempo::nuevo();
        for _ in 0..pulsos {
            s.pulso(f.siguiente(jitter_us), 24);
        }
        s
    }

    #[test]
    fn con_pulsos_limpios_da_el_tempo_exacto() {
        let s = correr(120.0, 0, 200);
        assert!((s.mbpm() as i64 - 120_000).abs() < 50, "dio {}", s.mbpm());
    }

    #[test]
    fn dos_milisegundos_de_jitter_no_mueven_la_lectura_mas_de_una_decima() {
        // §9: el test que obliga a la base larga. Un EMA sobre intervalos
        // consecutivos cae aqui aunque le pongas una constante de 20 segundos.
        for semilla in 1..=8u64 {
            let mut f = Fuente::nueva(120.0, 24, semilla);
            let mut s = SeguidorTempo::nuevo();
            let mut peor = 0i64;
            for i in 0..600 {
                s.pulso(f.siguiente(2_000), 24);
                if i > VENTANA_TEMPO {
                    peor = peor.max((s.mbpm() as i64 - 120_000).abs());
                }
            }
            assert!(peor <= 100, "semilla {semilla}: se movio {peor} milesimas de BPM");
        }
    }

    #[test]
    fn no_dice_nada_hasta_tener_la_ventana_llena() {
        // Inventar un tempo con tres pulsos seria adivinar en silencio.
        let s = correr(120.0, 0, 10);
        assert!(!s.estable());
        assert!(correr(120.0, 0, VENTANA_TEMPO + 2).estable());
    }

    #[test]
    fn sigue_un_cambio_de_tempo_en_una_ventana() {
        let mut f = Fuente::nueva(120.0, 24, 3);
        let mut s = SeguidorTempo::nuevo();
        for _ in 0..200 { s.pulso(f.siguiente(0), 24); }
        let mut f2 = Fuente::nueva(140.0, 24, 3);
        f2.t_us = f.t_us;
        for _ in 0..(VENTANA_TEMPO + 4) { s.pulso(f2.siguiente(0), 24); }
        assert!((s.mbpm() as i64 - 140_000).abs() < 500, "dio {}", s.mbpm());
    }

    #[test]
    fn el_ppqn_de_la_fuente_cambia_la_lectura_no_el_pulso() {
        // Eurorack no estandarizo los pulsos por negra (§3.3): a 1 PPQN los
        // pulsos van 24 veces mas espaciados para el MISMO tempo.
        let mut f = Fuente::nueva(120.0, 1, 5);
        let mut s = SeguidorTempo::nuevo();
        for _ in 0..(VENTANA_TEMPO + 4) { s.pulso(f.siguiente(0), 1); }
        assert!((s.mbpm() as i64 - 120_000).abs() < 100, "dio {}", s.mbpm());
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

```rust
//! §3. El reloj: las cuatro fuentes, el tempo, la fase y la rueda libre.

use heapless::Deque;

/// Pulsos de base para estimar el tempo.
///
/// Sale de la cuenta de §9 y no del gusto: con +-2 ms de jitter, medir contra
/// el pulso de hace N deja el error en sigma*sqrt(2)/(N*intervalo). Para
/// +-0.1 BPM a 120 BPM y 24 PPQN hacen falta 96 — que ademas son cuatro
/// negras, un compas de 4/4.
pub const VENTANA_TEMPO: usize = 96;

pub struct SeguidorTempo {
    marcas: Deque<u64, { VENTANA_TEMPO + 1 }>,
    mbpm: u32,
}
```

`pulso(t_us, ppqn_fuente)` empuja la marca, tira la más vieja si la cola está
llena, y cuando hay `VENTANA_TEMPO + 1` marcas calcula:

```text
  us_por_pulso = (mas_nueva - mas_vieja) / VENTANA_TEMPO
  mbpm         = 60_000_000_000 / (us_por_pulso * ppqn_fuente)
```

En enteros de 64 bits, sin coma flotante. `estable()` es «la cola está llena».
`mbpm()` devuelve `0` mientras no lo esté — **nunca un tempo inventado**.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core reloj && cargo clippy --all-targets -- -D warnings`
Esperado: 5 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add -A software/nucleo
git commit -m "El tempo no pide un PLL, pide una base mas larga: un buffer y una resta"
```

---

### Task 3: El reloj, entero

**Files:**
- Modify: `software/nucleo/core/src/reloj.rs`

**Interfaces:**
- Consumes: `SeguidorTempo`, `rejilla::{pulsos_por_compas, PPQN_INTERNO}`, y
  **`wmidi::MidiMessage`** para decodificar el reloj de MIDI.
- Produces: `Fuente` (enum), `Reloj` (`nuevo`, `pulso_externo`, `reset`,
  `link`, `tic_interno`, `al_pasar_el_tiempo`, `avanzar_a_pulso`, `posicion`,
  `pulsos_por_compas`, `mbpm`, `tiene_fase`, `rodando_libre`, `fuente_activa`,
  `pedir_fuente`), `TIMEOUT_RUEDA_LIBRE_MS`.

`al_pasar_el_tiempo(t_us)` es el que detecta la caída del reloj sin que llegue
un pulso — porque justamente no llega. `avanzar_a_pulso` es para los tests y
para el reloj interno.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests_reloj {
    use super::*;

    #[test]
    fn la_precedencia_es_link_midi_clockin_interno() {
        // §3.1. Con las cuatro presentes gana Link; se van cayendo en orden.
        let mut r = Reloj::nuevo();
        r.tic_interno(0);
        assert_eq!(r.fuente_activa(), Fuente::Interno);
        r.pulso_externo(Fuente::ClockIn, 1_000, 24);
        assert_eq!(r.fuente_activa(), Fuente::ClockIn);
        r.pulso_externo(Fuente::Midi, 1_100, 24);
        assert_eq!(r.fuente_activa(), Fuente::Midi);
        r.link(1_200, 0, 120_000);
        assert_eq!(r.fuente_activa(), Fuente::Link);
    }

    #[test]
    fn clock_in_sin_reset_no_sabe_donde_esta_el_uno() {
        // §3.3, y es EL punto honesto de esta spec.
        let mut r = Reloj::nuevo();
        for i in 0..200u64 {
            r.pulso_externo(Fuente::ClockIn, 1_000_000 + i * 20_833, 24);
        }
        assert!(!r.tiene_fase(), "no le mandaron RESET: no puede saberlo");
    }

    #[test]
    fn el_reset_es_lo_que_pone_el_uno() {
        let mut r = Reloj::nuevo();
        for i in 0..200u64 {
            r.pulso_externo(Fuente::ClockIn, 1_000_000 + i * 20_833, 24);
        }
        r.reset();
        assert!(r.tiene_fase());
        assert_eq!(r.posicion() % r.pulsos_por_compas() as u64, 0);
    }

    #[test]
    fn link_trae_fase_sin_que_nadie_mande_reset() {
        // §3.2: es exactamente lo que Eurorack no puede dar.
        let mut r = Reloj::nuevo();
        r.link(1_000_000, 0, 120_000);
        assert!(r.tiene_fase());
    }

    #[test]
    fn el_interno_siempre_sabe_donde_esta() {
        let mut r = Reloj::nuevo();
        r.tic_interno(0);
        assert!(r.tiene_fase());
    }

    #[test]
    fn si_se_cae_el_reloj_la_musica_sigue_y_se_dice() {
        // §3.5: un cable flojo no puede matarte un set. Pero tampoco puede
        // mentirte diciendo que sigues sincronizado.
        let mut r = Reloj::nuevo();
        for i in 0..200u64 {
            r.pulso_externo(Fuente::ClockIn, 1_000_000 + i * 20_833, 24);
        }
        let antes = r.mbpm();
        let t = 1_000_000 + 200 * 20_833;
        r.al_pasar_el_tiempo(t + TIMEOUT_RUEDA_LIBRE_MS * 1_000 + 1);
        assert!(r.rodando_libre());
        assert_eq!(r.mbpm(), antes, "el tempo se mantiene");
        assert_ne!(r.posicion(), 0, "y la posicion sigue avanzando");
    }

    #[test]
    fn el_cambio_de_fuente_aterriza_en_un_borde() {
        // §3.1: cambiar a mitad de compas da un tiron audible.
        let mut r = Reloj::nuevo();
        r.link(1_000_000, 0, 120_000);
        r.avanzar_a_pulso(200); // a mitad de compas
        r.pedir_fuente(Fuente::Interno);
        assert_eq!(r.fuente_activa(), Fuente::Link, "todavia no toca");
        r.avanzar_a_pulso(384); // el borde
        assert_eq!(r.fuente_activa(), Fuente::Interno);
    }

    #[test]
    fn sin_fase_el_cambio_aterriza_en_el_pulso() {
        // §3.1: si no conoce el compas, usa lo mas fino que si conoce.
        let mut r = Reloj::nuevo();
        for i in 0..200u64 {
            r.pulso_externo(Fuente::ClockIn, 1_000_000 + i * 20_833, 24);
        }
        assert!(!r.tiene_fase());
        r.pedir_fuente(Fuente::Interno);
        r.pulso_externo(Fuente::ClockIn, 1_000_000 + 200 * 20_833, 24);
        assert_eq!(r.fuente_activa(), Fuente::Interno, "no espera un compas que no conoce");
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

`Fuente` con el orden de precedencia como valor: `Interno = 0`, `ClockIn = 1`,
`Midi = 2`, `Link = 3`. Cada fuente guarda la marca de su última señal; la
activa es la de mayor valor que no haya caducado. `pedir_fuente` guarda la
petición y la aplica en el siguiente borde de compás, o de pulso si
`!tiene_fase()`.

**El decodificado de MIDI lo hace `wmidi`, no nosotros.** `Reloj::midi(bytes,
t_us)` llama a `MidiMessage::from_bytes` y actúa según la variante:
`TimingClock` es un pulso a 24 PPQN, `Start` reinicia la posición a cero,
`Continue` sigue donde estaba, `Stop` para el transporte, y
`SongPositionPointer(p)` da la posición en **beats MIDI** —seis relojes cada
uno— de donde sale la fase sin necesitar RESET. Un `Err` se ignora en silencio:
en el cable llegan mensajes que no son nuestros.

`TIMEOUT_RUEDA_LIBRE_MS = 500` — dos negras a 120 BPM. Al vencer, la fuente se
da por caída y el reloj sigue avanzando solo al último tempo conocido.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core && cargo clippy --all-targets -- -D warnings`
Esperado: 8 tests nuevos PASS.

- [ ] **Step 3: Commit**

```bash
git add -A software/nucleo
git commit -m "Cuatro fuentes de reloj, y la unica que trae fase sin cable es Link"
```

---

### Task 4: Los parámetros del reloj

**Files:**
- Create: `software/nucleo/core/src/tiempo_params.rs`
- Modify: `core/src/lib.rs`

**Interfaces:**
- Consumes: `descriptor::Descriptor`, `rejilla::Rejilla`, `reloj::Fuente`.
- Produces: `TIEMPO` (`&'static [Descriptor]`), `registrar(&mut Modelo)`, y las
  constantes de id: `ID_FUENTE`, `ID_TEMPO`, `ID_COMPAS_NUM`, `ID_COMPAS_DEN`,
  `ID_PPQN_FUENTE`, `ID_RESET`, `ID_DIV_CLOCK_OUT`, `ID_CUANTIZACION`,
  `ID_TRANSPORTE`, `ID_TIENE_FASE`, `ID_POSICION`, `ID_COMPAS_ACTUAL`,
  `ID_TEMPO_MEDIDO`, `ID_RODANDO_LIBRE`, `ID_ANULADOS`.

Mismo patrón que `medidas.rs`: una tabla `static` construida en tiempo de
compilación, con `registrar` metiéndola en el modelo.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::Unidad;
    use crate::modelo::{ErrorSet, Modelo};

    fn instrumento() -> Modelo {
        let mut m = Modelo::nuevo();
        registrar(&mut m).unwrap();
        m
    }

    #[test]
    fn las_etiquetas_de_la_cuantizacion_son_las_de_ableton() {
        // §2.1: es decision de diseño. El agente ya conoce ese vocabulario.
        let d = TIEMPO.iter().find(|d| d.id == ID_CUANTIZACION).unwrap();
        assert_eq!(d.etiquetas, crate::rejilla::Rejilla::ETIQUETAS);
        assert!(d.etiquetas.contains(&"1 compas"));
        assert!(d.etiquetas.contains(&"1/16"));
    }

    #[test]
    fn el_transporte_es_un_parametro_no_un_mensaje() {
        // §7.2, con consecuencia: por §2.1 el agente puede arrancarlo.
        let mut m = instrumento();
        assert!(m.set(ID_TRANSPORTE, 1).is_ok());
        assert_eq!(m.get(ID_TRANSPORTE), Some(1));
    }

    #[test]
    fn las_medidas_no_las_escribe_nadie() {
        let mut m = instrumento();
        for id in [ID_TIENE_FASE, ID_POSICION, ID_COMPAS_ACTUAL, ID_TEMPO_MEDIDO,
                   ID_RODANDO_LIBRE, ID_ANULADOS] {
            assert_eq!(m.set(id, 1), Err(ErrorSet::SoloLectura), "{id:?}");
        }
    }

    #[test]
    fn todo_enumerado_trae_una_etiqueta_por_valor() {
        // Sin esto el agente ve un numero y no sabe que significa.
        use crate::descriptor::Tipo;
        for d in TIEMPO.iter().filter(|d| d.tipo == Tipo::Enumerado) {
            assert_eq!(
                d.etiquetas.len() as i32,
                d.max - d.min + 1,
                "{} tiene {} etiquetas para {} valores",
                d.nombre, d.etiquetas.len(), d.max - d.min + 1
            );
        }
    }

    #[test]
    fn el_tempo_trae_unidad_y_un_rango_que_se_puede_tocar() {
        let d = TIEMPO.iter().find(|d| d.id == ID_TEMPO).unwrap();
        assert_eq!(d.unidad, Unidad::Milesimas);
        assert!(d.min <= 20_000 && d.max >= 300_000, "de 20 a 300 BPM");
    }

    #[test]
    fn ningun_id_choca_con_las_medidas_de_audio() {
        let mut m = Modelo::nuevo();
        registrar(&mut m).unwrap();
        crate::medidas::registrar(&mut m).unwrap();
        assert_eq!(m.len(), TIEMPO.len() + crate::medidas::MEDIDAS.len());
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

Los ids van en la ranura `0` parte `0`, en el rango `0xC0..0xDF` — por encima
de las medidas de audio (`0x80..0xA2`) y por debajo de nada. Nombres escritos
para alguien que nunca vio el instrumento: `"tempo"`, `"fuente de sincronia"`,
`"cuantizacion global"`, `"sabe donde esta el 1"`.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core tiempo_params && cargo clippy --all-targets -- -D warnings`
Esperado: 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add -A software/nucleo
git commit -m "Los parametros del reloj, con las etiquetas de Ableton literales"
```

---

### Task 5: Las rampas

**Files:**
- Create: `software/nucleo/core/src/rampa.rs`
- Modify: `core/src/lib.rs`

**Interfaces:**
- Consumes: `descriptor::Unidad`, `param::{ParamId, Valor}`.
- Produces: `Rampa { id, origen, destino, inicio, duracion, curva, anulada }`,
  `Rampa::valor_en(pulso, unidad) -> Valor`, `Rampas` (`empujar`, `anular`,
  `reactivar`, `tick`, `activas`), `MAX_RAMPAS`.

**Aquí va el test que más manda de toda la spec.**

- [ ] **Step 1: Escribir los tests que fallan**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::Unidad;
    use crate::param::ParamId;

    fn r(origen: i32, destino: i32, duracion: u32) -> Rampa {
        Rampa {
            id: ParamId(0x0100),
            origen, destino,
            inicio: 1000,
            duracion,
            curva: 0,
            anulada: false,
        }
    }

    #[test]
    fn en_hercios_interpola_en_octavas_y_no_en_hercios() {
        // §5.2, y es EL test de esta spec. De 100 a 1600 Hz son 4 octavas;
        // a mitad de tiempo van 2, que son 400 Hz. Lineal en hercios daria
        // 850 — y ahi esta la diferencia entre un barrido que suena parejo y
        // uno que suena a maquina.
        let ra = r(100, 1600, 384);
        let mitad = ra.valor_en(1000 + 192, Unidad::Hz);
        assert!((mitad - 400).abs() <= 2, "dio {mitad}, y lineal daria 850");
    }

    #[test]
    fn en_las_demas_unidades_interpola_lineal() {
        // El dB ya es logaritmico, y los cents tambien. Volver a tomar
        // logaritmo seria aplicarlo dos veces.
        for u in [Unidad::MilidB, Unidad::Cents, Unidad::Milesimas, Unidad::Ninguna] {
            let ra = r(0, 1000, 384);
            assert_eq!(ra.valor_en(1000 + 192, u), 500, "{u:?}");
        }
    }

    #[test]
    fn aterriza_exactamente_en_el_destino() {
        // Ni 99.7 %. Un filtro que se queda a 1595 de 1600 se oye.
        for u in [Unidad::Hz, Unidad::MilidB] {
            let ra = r(100, 1600, 384);
            assert_eq!(ra.valor_en(1000 + 384, u), 1600, "{u:?}");
            assert_eq!(ra.valor_en(1000 + 9999, u), 1600, "{u:?} pasado el final");
        }
    }

    #[test]
    fn antes_de_empezar_vale_el_origen() {
        assert_eq!(r(100, 1600, 384).valor_en(999, Unidad::Hz), 100);
    }

    #[test]
    fn duracion_cero_es_un_salto() {
        // §5.4: no es un SET disfrazado — el inicio ya venia cuantizado.
        let ra = r(100, 1600, 0);
        assert_eq!(ra.valor_en(999, Unidad::Hz), 100);
        assert_eq!(ra.valor_en(1000, Unidad::Hz), 1600);
    }

    #[test]
    fn nunca_se_sale_del_rango_entre_origen_y_destino() {
        for curva in [-100i8, -50, 0, 50, 100] {
            let mut ra = r(200, 800, 384);
            ra.curva = curva;
            for p in 0..=384 {
                let v = ra.valor_en(1000 + p, Unidad::Hz);
                assert!((200..=800).contains(&v), "curva {curva}, pulso {p}: {v}");
            }
        }
    }

    #[test]
    fn la_curva_positiva_arranca_lento_y_la_negativa_cede_al_final() {
        let mut lenta = r(0, 1000, 384);
        lenta.curva = 100;
        let mut rapida = r(0, 1000, 384);
        rapida.curva = -100;
        let m = 1000 + 192;
        assert!(lenta.valor_en(m, Unidad::Ninguna) < 500);
        assert!(rapida.valor_en(m, Unidad::Ninguna) > 500);
    }

    #[test]
    fn una_rampa_que_baja_tambien_funciona() {
        let ra = r(1600, 100, 384);
        assert!((ra.valor_en(1000 + 192, Unidad::Hz) - 400).abs() <= 2);
    }

    #[test]
    fn con_origen_o_destino_no_positivo_cae_a_lineal_sin_reventar() {
        // ln(0) no existe. Un corte no llega a 0 Hz, pero el codec no puede
        // depender de eso.
        let ra = r(0, 1000, 384);
        assert_eq!(ra.valor_en(1000 + 192, Unidad::Hz), 500);
    }

    #[test]
    fn la_cinta_sigue_corriendo_cuando_se_anula() {
        // §6.2: una rampa anulada NO se detiene, deja de escribir. Reactivar
        // cae donde la funcion este AHORA, no donde estaba al anular.
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        let id = ParamId(0x0100);

        // Tick al cuarto del recorrido: escribe.
        assert_eq!(rs.tick(1000 + 96, |_| Unidad::Ninguna).as_slice(), &[(id, 250)]);
        // Se anula: deja de escribir.
        rs.anular(id);
        assert!(rs.tick(1000 + 192, |_| Unidad::Ninguna).is_empty());
        // Se reactiva a tres cuartos: cae en 750, no en 500.
        rs.reactivar(id);
        assert_eq!(rs.tick(1000 + 288, |_| Unidad::Ninguna).as_slice(), &[(id, 750)]);
    }

    #[test]
    fn una_rampa_terminada_se_quita_sola() {
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        rs.tick(1000 + 384, |_| Unidad::Ninguna);
        assert_eq!(rs.activas(), 0, "no puede quedarse ocupando sitio");
    }

    #[test]
    fn una_rampa_nueva_sobre_el_mismo_parametro_reemplaza_a_la_vieja() {
        // Dos rampas peleandose un parametro darian un valor sin definir.
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        rs.empujar(r(0, 500, 384)).unwrap();
        assert_eq!(rs.activas(), 1);
    }
}
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

`MAX_RAMPAS = 16`. La curva es `t^k` con `k = 2^(curva/50)`: `curva = 0` da
`k = 1` (lineal), positivo da `k > 1` (arranca lento). `libm::{powf, logf,
expf}`.

`tick(pulso, unidad_de)` recibe un cierre que resuelve la unidad de cada id
—para no acoplar `rampa.rs` al `Modelo`— y devuelve los pares `(id, valor)` que
hay que escribir.

Ejecuta: `cd software/nucleo && cargo test -p sam17-nucleo-core rampa && cargo clippy --all-targets -- -D warnings`
Esperado: 13 tests PASS.

- [ ] **Step 3: Comprobar que el test estrella muerde**

Cambia la interpolación de `Hz` a lineal a propósito y confirma que
`en_hercios_interpola_en_octavas_y_no_en_hercios` cae con «dio 850». Luego
restaura. **Si no cae, el test no vale.**

- [ ] **Step 4: Commit**

```bash
git add -A software/nucleo
git commit -m "Las rampas interpolan en octavas porque el oido oye octavas, y eso lo decide el descriptor"
```

---

### Task 6: Los tres mensajes

**Files:**
- Modify: `core/src/protocolo.rs`, `core/src/descriptor.rs`
- Modify: `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md` (§4.1),
  `software/nucleo/README.md`

**Interfaces:**
- Produces: `Mensaje::Rampa { id, destino, duracion, curva }` (`0x0E`),
  `Mensaje::Anulado { id, anulado }` (`0x89`),
  `Mensaje::Reactivar { id: Option<ParamId> }` (`0x0F`),
  `Descriptor::acepta_modulacion` (bit 6 de las banderas).

- [ ] **Step 1: Añadir los tests que fallan**, y **subir `todas()` de 21 a 24**:

```rust
    #[test]
    fn reactivar_viaja_con_y_sin_id() {
        // Sin id son todos (§7.1). Las dos formas tienen que distinguirse.
        let mut buf = [0u8; 64];
        for m in [
            Mensaje::Reactivar { id: None },
            Mensaje::Reactivar { id: Some(ParamId::nuevo(5, 0, 1)) },
        ] {
            let n = codificar(&m, &mut buf).unwrap();
            assert_eq!(decodificar(&buf[..n]).unwrap(), m);
        }
    }

    #[test]
    fn la_marca_de_modulacion_sobrevive_el_viaje() {
        // §7.3: un bit hoy contra reescribir el modelo en la spec 2.
        use crate::descriptor::*;
        static D: Descriptor = Descriptor {
            id: ParamId(0x1234), nombre: "x", tipo: Tipo::Continuo,
            ambito: Ambito::Compartido, solo_lectura: false, medida: false,
            confirmacion_fisica: false, acepta_modulacion: true,
            min: 0, max: 100, def: 0, unidad: Unidad::Hz, etiquetas: &[],
        };
        let mut buf = [0u8; 256];
        let n = escribir(&D, &mut buf).unwrap();
        assert!(leer(&buf[..n]).unwrap().0.acepta_modulacion);
    }
```

Y en `todas()`, tres entradas más:

```rust
            Mensaje::Rampa { id, destino: -5000, duracion: 384, curva: -40 },
            Mensaje::Anulado { id, anulado: true },
            Mensaje::Reactivar { id: None },
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

> **Ojo con el ripple.** Añadir un campo a `Descriptor` obliga a tocar **todos
> los literales que ya existen**: los 27 de `medidas.rs`, los del catálogo de
> `descubrimiento.rs`, y los de los tests de `modelo.rs`, `retencion.rs`,
> `servidor.rs`, `sysex.rs` y `usbmidi.rs`. Es mecánico y el compilador los
> nombra uno por uno — pero es la mitad del trabajo de esta tarea, así que no
> te sorprenda. **Todos van a `false`**: la única que acepta modulación hoy es
> ninguna, porque la modulación es de la spec 2.

Etiquetas: `T_RAMPA = 0x0E`, `T_REACTIVAR = 0x0F` (cliente →),
`T_ANULADO = 0x89` (→ cliente). `Reactivar` codifica el `Option` con un byte de
presencia. La bandera `acepta_modulacion` va en el **bit 6**, que está libre
(0-2 son las tres marcas, 3 el ámbito, 4-5 el tipo).

Los tests que ya existen —etiquetas sin repetir, dirección en el bit alto,
truncamiento rechazado, ida y vuelta— cubren los tres solos.

Ejecuta: `cd software/nucleo && cargo test && cargo clippy --all-targets -- -D warnings`
Esperado: 24 variantes, todo el protocolo PASS.

- [ ] **Step 3: Actualizar la spec del núcleo y el README**

En §4.1, tres filas más y una línea: *«`RAMPA`, `ANULADO` y `REACTIVAR` los
añade la spec del tiempo musical del 2026-08-17»*. Y la tabla de etiquetas del
README, que ahora llega a 24.

- [ ] **Step 4: Commit**

```bash
git add -A software/nucleo docs
git commit -m "Tres mensajes, y la tabla sigue cabiendo de un vistazo"
```

---

### Task 7: El servidor los atiende

**Files:**
- Modify: `core/src/servidor.rs`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: `Instrumento::{tick, reloj, avanzar_a}`, y el manejo de los tres
  mensajes nuevos en `atender`.

  > **Enmienda del 2026-08-24** (PR #181). Esta línea decía `reloj_mut`, y
  > eso ya no existe: se borró en `87e8310` (#182, fallo 6) porque entregaba
  > un `&mut Reloj` entero, era `pub`, y **no tenía un solo llamador** —ni
  > siquiera en los tests.
  >
  > Cerrarlo dejó al descubierto que el instrumento **no corría**: `tick`
  > pide un pulso, y el firmware no sabe en qué pulso está porque eso
  > depende del tempo, que vive dentro del `Reloj`. Ese hueco lo tapa
  > `avanzar_a(t_us)`: el firmware dice qué hora es, el instrumento decide
  > cuántos pulsos pasaron. La cuenta vive en `core`, donde hay tests.

Los tests usan un helper `instrumento_con_reloj()` —como el `instrumento()` que
ya existe en `servidor.rs`, más `tiempo_params::registrar` y el reloj arrancado
en interno a 120 BPM y 4/4— y un segundo descriptor `OTRO` junto a los tres que
el módulo ya tiene.

**La distinción que hay que respetar:** el `SET` de un cliente **anula** la
rampa que tenga ese parámetro; la escritura que hace el `tick` **no**. Y las dos
acaban en `modelo.set`. La diferencia vive aquí, no en el modelo — que no gana
ninguna puerta nueva.

- [ ] **Step 1: Escribir los tests que fallan**

```rust
    #[test]
    fn una_rampa_aceptada_arranca_en_el_borde_de_la_rejilla() {
        let mut i = instrumento_con_reloj();
        i.atender(Mensaje::Rampa { id: NORMAL.id, destino: 100, duracion: 384, curva: 0 }, 0);
        // A mitad de compas todavia no se movio: espera al borde.
        i.tick(200);
        assert_eq!(i.modelo().get(NORMAL.id), Some(0));
        i.tick(384);
        assert_eq!(i.modelo().get(NORMAL.id), Some(0), "arranca EN el borde, en el origen");
        i.tick(384 + 192);
        assert!(i.modelo().get(NORMAL.id).unwrap() > 0, "y de ahi se mueve");
    }

    #[test]
    fn un_set_del_cliente_anula_la_rampa_y_lo_avisa() {
        // §6.1. Este es el test de la seccion entera.
        let mut i = instrumento_con_reloj();
        i.atender(Mensaje::Rampa { id: NORMAL.id, destino: 100, duracion: 384, curva: 0 }, 0);
        i.tick(384 + 96);
        let r = mensajes(&i.atender(Mensaje::Set(NORMAL.id, 7), 0));
        assert!(r.contains(&Mensaje::Anulado { id: NORMAL.id, anulado: true }));
        assert_eq!(i.modelo().get(NORMAL.id), Some(7));
        // Y el tick ya no la pisa.
        i.tick(384 + 192);
        assert_eq!(i.modelo().get(NORMAL.id), Some(7), "la rampa dejo de escribir");
    }

    #[test]
    fn reactivar_la_devuelve_donde_la_cinta_este_ahora() {
        // §6.2.
        let mut i = instrumento_con_reloj();
        i.atender(Mensaje::Rampa { id: NORMAL.id, destino: 100, duracion: 384, curva: 0 }, 0);
        i.tick(384 + 96);
        i.atender(Mensaje::Set(NORMAL.id, 7), 0);
        let r = mensajes(&i.atender(Mensaje::Reactivar { id: Some(NORMAL.id) }, 0));
        assert!(r.contains(&Mensaje::Anulado { id: NORMAL.id, anulado: false }));
        i.tick(384 + 288);
        assert_eq!(i.modelo().get(NORMAL.id), Some(75), "tres cuartos, no la mitad");
    }

    #[test]
    fn reactivar_sin_id_los_devuelve_todos() {
        let mut i = instrumento_con_reloj();
        for id in [NORMAL.id, OTRO.id] {
            i.atender(Mensaje::Rampa { id, destino: 100, duracion: 384, curva: 0 }, 0);
            i.tick(384 + 96);
            i.atender(Mensaje::Set(id, 7), 0);
        }
        let r = mensajes(&i.atender(Mensaje::Reactivar { id: None }, 0));
        assert_eq!(r.iter().filter(|m| matches!(m, Mensaje::Anulado { anulado: false, .. })).count(), 2);
    }

    #[test]
    fn una_rampa_a_un_destino_fuera_de_rango_se_rechaza_al_aceptarla() {
        // Mejor ahora que descubrirlo a mitad del barrido.
        let mut i = instrumento_con_reloj();
        let r = mensajes(&i.atender(
            Mensaje::Rampa { id: NORMAL.id, destino: 99_999, duracion: 384, curva: 0 }, 0));
        assert_eq!(r.as_slice(), &[Mensaje::Error {
            etiqueta: 0x0E, codigo: CodigoError::FueraDeRango }]);
    }

    #[test]
    fn no_se_admite_una_rampa_sobre_algo_de_solo_lectura_ni_marcado() {
        let mut i = instrumento_con_reloj();
        for (id, codigo) in [(MEDIDA.id, CodigoError::SoloLectura),
                             (PELIGROSO.id, CodigoError::ExigeConfirmacion)] {
            let r = mensajes(&i.atender(
                Mensaje::Rampa { id, destino: 1, duracion: 384, curva: 0 }, 0));
            assert!(matches!(r.as_slice(), [Mensaje::Error { codigo: c, .. }] if *c == codigo));
        }
    }

    #[test]
    fn el_tick_solo_avisa_a_los_suscriptores() {
        let mut i = instrumento_con_reloj();
        i.atender(Mensaje::Rampa { id: NORMAL.id, destino: 100, duracion: 384, curva: 0 }, 0);
        assert!(i.tick(384 + 96).is_empty());
        i.atender(Mensaje::Subscribe { activo: true }, 0);
        assert!(!i.tick(384 + 192).is_empty());
    }

    #[test]
    fn el_contador_de_anulados_es_una_medida_de_verdad() {
        let mut i = instrumento_con_reloj();
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(0));
        i.atender(Mensaje::Rampa { id: NORMAL.id, destino: 100, duracion: 384, curva: 0 }, 0);
        i.tick(384 + 96);
        i.atender(Mensaje::Set(NORMAL.id, 7), 0);
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(1));
        i.atender(Mensaje::Reactivar { id: None }, 0);
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(0));
    }
```

- [ ] **Step 2: Verlo fallar, implementar, verlo pasar**

`tick(pulso)` publica las medidas del reloj (`posición`, `compás actual`,
`tempo medido`, `tiene fase`, `rodando libre`) y corre `Rampas::tick`,
escribiendo cada par por la ruta interna que **no** anula. Devuelve `Respuestas`
para los suscriptores.

Ejecuta: `cd software/nucleo && cargo test && cargo clippy --all-targets -- -D warnings`
Esperado: 8 tests nuevos PASS.

- [ ] **Step 3: Commit**

```bash
git add -A software/nucleo
git commit -m "El SET del cliente anula la rampa; el del tick no. La diferencia vive en el servidor"
```

---

### Task 8: El presupuesto de aterrizaje

**Files:**
- Create: `hardware/02-midi-cv/tiempo_budget.py`

Con la forma de `autotune_budget.py`, que es la que ya demostró servir: **se
deriva lo derivable y el término que queda se despeja en requisito.**

- [ ] **Step 1: Buscar la fuente del objetivo musical, ANTES de escribir nada**

§12 de la spec deja esto abierto a propósito: *«que la simultaneidad de un gate
se juzga en el orden del milisegundo es la referencia de partida, pero el número
exacto hay que decidirlo al escribirlo, y con fuente»*.

Busca el umbral de **asincronía perceptible entre dos ataques** en la
literatura de percepción auditiva, y **cítalo en el docstring con su fuente**.
Si lo que encuentras contradice el orden del milisegundo, **manda lo que
encuentres** y ajusta el presupuesto — no al revés.

- [ ] **Step 2: Escribir el guion**

Deriva y asevera:

```python
F_SYS = 150e6            # RP2350, dual Cortex-M33
BITS_TRAMA_J2 = 72       # contrato congelado del modulo 3
F_SPI = 10e6             # tope del mismo contrato

T_TRAMA_J2 = BITS_TRAMA_J2 / F_SPI          # 7.2 us, sale del contrato

def deteccion_max(objetivo_s: float) -> float:
    """Cuanto puede tardar la deteccion del flanco de CLOCK IN, en segundos.

    El termino que queda no se supone: se despeja. Igual que el 74HC14 de
    autotune_budget.py acabo siendo «puede temblar hasta 131 ns».
    """
    return objetivo_s - T_TRAMA_J2
```

Y en `demo()`, la aserción que hace que el guion valga:

```python
assert T_TRAMA_J2 < 0.1 * OBJETIVO_S, (
    "la trama del J2 tiene que ser despreciable frente al objetivo musical. "
    "Si no lo es, el cuello volvio a ser el enlace y hay que subir F_SPI o "
    "aflojar el objetivo")
```

**Y el número que sale es el que consume la spec:** `deteccion_max` es la
`ventana` de `siguiente_borde` de la Task 1. Imprímelo diciéndolo, para que
quien lo lea sepa que ese guion decide un parámetro del firmware.

- [ ] **Step 3: Correrlo y añadirlo a los gates**

```bash
python hardware/02-midi-cv/tiempo_budget.py
```
Esperado: salida con el objetivo citado, el desglose, y exit 0.

- [ ] **Step 4: Commit**

```bash
git add -A hardware/02-midi-cv
git commit -m "El presupuesto de aterrizaje: la ventana de la rejilla sale de aqui, no del gusto"
```

---

### Task 9: Cierre

**Files:**
- Modify: `software/nucleo/README.md`, `software/nucleo/fw/EN-PLACA.md`,
  `docs/architecture-poly.md`, la spec del tiempo musical (cabecera)

- [ ] **Step 1: README** — los cuatro módulos nuevos en la tabla, la tabla de
  etiquetas a 24, y una sección corta de «el tiempo musical» con la regla de
  oro: `SET` inmediato, `RAMPA` aterriza.

- [ ] **Step 2: `EN-PLACA.md`** — añadir lo que necesita hierro (§8 de la spec):
  umbrales reales del CLOCK IN contra lo que despeje `tiempo_budget.py`,
  niveles del CLOCK OUT, MIDI clock por USB de verdad, y **Link sobre el
  puente** (que necesita que el puente exista y esté elegido).

- [ ] **Step 3: `architecture-poly.md` §4** — la fila de `CLOCK`/`RESET` gana
  que el instrumento **también es fuente**, y que el puente inalámbrico es la
  cuarta fuente de sincronía por Link.

- [ ] **Step 4: La cabecera de la spec** — `pendiente de plan` → `en ejecución`.

- [ ] **Step 5: Gates completos**

```bash
cd software/nucleo && cargo test && cargo clippy --all-targets -- -D warnings
cd fw && cargo build --release
cd ../../.. && for f in $(git ls-files '*_budget.py'); do python "$f" >/dev/null && echo "OK $f"; done
```

- [ ] **Step 6: PR, merge, e issues de lo aplazado**

```bash
gh pr create --title "El instrumento en tiempo musical" --body "..."
gh issue create --title "Spec 2: patrones, p-locks y el motor de secuencia" --body "..."
gh issue create --title "Spec 3: escenas, Follow Actions, arpegiador y memoria de acordes" --body "..."
```

La 4 ya tiene issue (#91).

---

## Auto-revisión de este plan

**Cobertura de la spec.** §3.1 → T3 · §3.2 (Link como fuente) → T3 · §3.3 y
§3.4 → T3 · §3.5 → T3 · §3.6 → T2 · §4 → T1 · §5.1 y §5.4 → T5, T7 · §5.2 →
T5 · §5.3 → T1 y T8 · §6 → T5, T7 · §7.1 → T6 · §7.2 → T4 · §7.3 → T6 · §9 →
todas, más T8 · §10 → T9.

**Un hallazgo que corrige la spec, y va en la Task 2.** §3.6 dice que el MIDI
clock *«necesita un lazo de enganche»*. Se hizo la cuenta contra el objetivo de
§9 y **no lo necesita**: un promedio móvil no llega ni con una constante de 21
segundos, mientras que medir contra el pulso de hace 96 da 0.098 BPM en dos
segundos. Promediar reduce el ruido con `√α`; alargar la base lo reduce con `N`.
Un búfer circular y una resta. **La spec se corrige en el commit de esa tarea**,
no se deja en pie una afirmación que la aritmética contradice.

**Un cabo que la spec no ató y este plan sí.** La ventana de §5.3 puede ser
mayor que una rejilla corta —una ventana de 20 pulsos contra un 1⁄16 de 24
haría que «llegué tarde» significara «siempre»—. La Task 1 la recorta a la
mitad de la rejilla, y hay test.

**Lo que no se escribe de memoria.** El paso 1 de la Task 8 es «busca la fuente
antes de teclear»: el umbral de asincronía perceptible entre dos ataques. Es el
único número de todo el plan que no sale de un contrato del repo ni de una
derivación, y por eso lleva su paso propio.

**Dónde puede quedarse corto.** `TIMEOUT_RUEDA_LIBRE_MS = 500` son dos negras a
120 BPM, y a 60 BPM es una sola — o sea que a tempos lentos declara la caída
antes de lo que debería. Se deja fijo a propósito, porque hacerlo relativo al
tempo significa que un reloj que se cae mientras baja de tempo tarda cada vez
más en darse por caído. Si en placa molesta, es una constante.
