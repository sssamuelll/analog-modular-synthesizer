# El generador de envolvente: plan de implementación

> **Para quien lo ejecute:** SUB-SKILL REQUERIDA: `superpowers:subagent-driven-development`
> (recomendada) o `superpowers:executing-plans`, tarea por tarea. Los pasos llevan
> casillas (`- [ ]`) para el seguimiento. **Cada tarea es TDD: el test primero, en
> rojo, pegado en el informe; después el código.**

**Objetivo:** que la fuerza tenga a quién multiplicar: los generadores de envolvente
y los escritores del módulo de Voz en `core`, probados en el host, más los dos
guiones que el papel manda y las enmiendas a los papeles que legisla.

**Arquitectura:** dos objetos separados (papel §1): el **generador**, una máquina de
cuatro etapas cerrada entre bordes que solo consume su copia capturada y el
sostenido vivo, y el **escritor**, que multiplica niveles por parámetros vivos del
modelo. Un solo dueño del estado —el tick— que drena una cola FIFO en orden y avanza
(papel §3.5). Todo en `core`, `no_std`; el firmware del N657 no existe (#250) y no
se toca.

**Tech stack:** Rust `no_std` (`software/nucleo/core`: `heapless`, `libm`, `wmidi`),
tests de integración en `core/tests/`, Python 3 para los guiones de `hardware/`,
las siete puertas de `.githooks/pre-push`.

**Papel:** `docs/superpowers/specs/2026-09-02-generador-de-envolvente-design.md`
(v2, tras la junta). El plan argumenta desde el papel; quien ejecute lee los dos.

## Restricciones globales

- `F_RENDER = 10 000 Hz`, `dt = 100 µs` (papel §1; voz-total §3.1). Un milisegundo
  son **10 ticks**, exactos.
- Las etapas de duración conocida **terminan por cuenta de ticks** y ajustan el
  nivel exacto al terminar (papel §2). Ningún fin por umbral relativo en `f32`.
- El sostenido **no se captura** y aplica en el tick, sin filtro (papel §2.3, R-M1).
- Se captura al borde: los tres tiempos de cada envolvente y la fuerza (papel §3.3).
- El modelo habla de **amplitud** `a ∈ [0, 1]`; la ley palabra → ganancia del VCA es
  un hueco con contrato y **no se escribe** (papel §4.3, decisión 15).
- `NIVEL_OCIOSO = 2⁻¹⁶` es constante del modelo, no del DAC (papel §6).
- `FUERZA_REPARACION = u16::MAX` (papel §3.4, decisión 12).
- El tick es el único dueño del estado; todo lo demás encola (papel §3.5, decisión 14).
- `core` **no trae valores por defecto** de parámetros: quien construye pasa los suyos.
- Acentos: `core` está escrito sin acentos en identificadores y casi sin acentos en
  comentarios; mira el archivo vecino y sigue su costumbre. Español, sin emoji.
- Cambio mínimo: sin traits de una implementación, sin abstracciones para el futuro,
  sin reformateos ni reordenar imports de paso. No se ablanda ni se borra ningún test
  existente.
- Cada número de diseño se cita al papel (sección) o a la hoja; lo que no esté
  citable se declara HUECO en el informe, no se inventa.

## Mapa de archivos

| Archivo | Responsabilidad | Tarea |
|---|---|---|
| `software/nucleo/core/src/escritor.rs` (nuevo) | Los escritores: ganancia de fuerza, factores de paneo, amplitud a palabra de 16 bits, y el contrato del escritor de corte (el polo de un tick y la ley de octavas) | 1 |
| `software/nucleo/core/tests/escritor.rs` (nuevo) | Sus tests | 1 |
| `software/nucleo/core/src/envolvente.rs` (nuevo) | El `Generador` (una envolvente), el `Canal` (dos generadores + escritor del VCA) y `Generadores` (los dieciséis, la cola, la compuerta, el silencio) | 2, 3 |
| `software/nucleo/core/tests/envolvente.rs` (nuevo) | Sus tests | 2, 3 |
| `software/nucleo/core/src/lib.rs` | `pub mod envolvente; pub mod escritor;` | 1, 2 |
| `software/nucleo/core/src/bahia.rs` | `Commit` gana `cambian`; `forzar` documentada como no ejecutable en v1 | 4 |
| `software/nucleo/core/tests/bahia.rs` | Un test para `cambian` | 4 |
| `hardware/03-vco/ataque_budget.py` (nuevo) | El presupuesto nota → VCA con sus huecos; lo recoge `gates.py` por el glob `hardware/**/*_budget.py` y acepta el código 2 | 5 |
| `hardware/03-vco/check_censo_voz.py` | La fila `ENVOLVENTE_POR_CANAL = 10` | 6 |
| `docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md` §3.2, `2026-08-26-motor-digital-design.md` §5 y §7, `2026-08-25-evento-de-nota-design.md` D6/D7 | Las enmiendas del papel §14 | 7 |

Las tareas 1-3 van juntas (un ejecutor, un worktree), las 4-6 juntas (otro), la 7 la
hace quien coordina. Las dos ramas tocan `lib.rs` en líneas distintas.

---

### Tarea 1: `escritor.rs` — las multiplicaciones del escritor

**Archivos:**
- Crear: `software/nucleo/core/src/escritor.rs`
- Crear: `software/nucleo/core/tests/escritor.rs`
- Modificar: `software/nucleo/core/src/lib.rs` (añadir `pub mod escritor;` en orden alfabético)

**Interfaces:**
- Consume: `crate::fuerza::Fuerza` (`pub struct Fuerza(pub u16)`).
- Produce (las usa la tarea 3, con estos nombres exactos):

```rust
pub const K48: f32;                                                 // 1 − e^(−1/4,8)
pub fn ganancia_fuerza(fuerza: Fuerza, sensibilidad_milesimas: u16) -> f32;
pub fn factores_paneo(paneo_milesimas: u16) -> (f32, f32);          // (L, R)
pub fn amplitud(y: f32, g_v: f32, factor: f32) -> u16;              // round(65 535·y·g_v·factor)
pub fn polo_48k(z: f32, y_f: f32) -> f32;                           // z + K48·(y_f − z)
pub fn corte_hz(f_base_hz: f32, cantidad_cents: i16, y_f: f32) -> f32;  // f_base·2^(c·y_f/1200)
```

- [ ] **Paso 1: escribir los tests, que fallan**

`software/nucleo/core/tests/escritor.rs`:

```rust
//! El escritor del VCA y el contrato del escritor de corte.
//! Papel: `docs/superpowers/specs/2026-09-02-generador-de-envolvente-design.md`,
//! §4.1 (la fuerza multiplica la amplitud), §4.2 (paneo a potencia constante),
//! §4.3 (la salida es amplitud), §5 (el polo de un tick y la ley de octavas).

use sam17_nucleo_core::escritor::{
    amplitud, corte_hz, factores_paneo, ganancia_fuerza, polo_48k, K48,
};
use sam17_nucleo_core::fuerza::Fuerza;

/// §4.1: `g_v = (1 − s) + s·v`. Con s = 0 la fuerza no hace nada; con s = 1 una
/// nota a fuerza cero no suena. Se barre s y v: dos puntos a mano dejan pasar
/// una formula equivocada que acierte en ellos.
#[test]
fn la_ganancia_de_fuerza_es_lineal_en_v_y_s_cero_la_anula() {
    for s in [0u16, 100, 250, 500, 750, 1000] {
        for v in [0u16, 1, 4096, 16384, 32768, 49152, 65535] {
            let g = ganancia_fuerza(Fuerza(v), s);
            let esperado = (1.0 - s as f32 / 1000.0) + (s as f32 / 1000.0) * (v as f32 / 65535.0);
            assert!((g - esperado).abs() < 1e-6, "s={s} v={v}: {g} vs {esperado}");
        }
        assert!((ganancia_fuerza(Fuerza(65535), s) - 1.0).abs() < 1e-6, "fuerza plena da 1");
    }
    assert_eq!(ganancia_fuerza(Fuerza(0), 1000), 0.0, "s = 1 y v = 0: no suena");
    assert_eq!(ganancia_fuerza(Fuerza(0), 0), 1.0, "s = 0: la fuerza no hace nada");
}

/// §4.2: potencia constante, L² + R² = 1 en todo el recorrido; p = 500 da −3 dB
/// en cada rama; 0 es izquierda dura y 1000 derecha dura.
#[test]
fn el_paneo_es_a_potencia_constante_en_todo_el_recorrido() {
    for p in (0..=1000u16).step_by(25) {
        let (l, r) = factores_paneo(p);
        assert!((l * l + r * r - 1.0).abs() < 1e-5, "p={p}: L²+R² = {}", l * l + r * r);
        assert!(l >= 0.0 && r >= 0.0);
    }
    let (l, r) = factores_paneo(500);
    let menos_3_db = 10f32.powf(-3.0 / 20.0);
    assert!((l - menos_3_db).abs() < 2e-3 && (r - menos_3_db).abs() < 2e-3, "centro a −3 dB");
    assert_eq!(factores_paneo(0), (1.0, 0.0));
    let (l, r) = factores_paneo(1000);
    assert!(l.abs() < 1e-6 && (r - 1.0).abs() < 1e-6);
}

/// §4.3: la palabra es la amplitud redondeada a 16 bits; cero es exactamente cero
/// y uno es exactamente 65 535. Monotona en y.
#[test]
fn la_amplitud_se_redondea_a_dieciseis_bits_y_es_monotona() {
    assert_eq!(amplitud(0.0, 1.0, 1.0), 0);
    assert_eq!(amplitud(1.0, 1.0, 1.0), 65535);
    assert_eq!(amplitud(1.0, 0.5, 1.0), 32768, "round(32767,5) sube");
    assert_eq!(amplitud(0.5, 1.0, 0.5), 16384);
    let mut anterior = 0u16;
    for i in 0..=1000u32 {
        let a = amplitud(i as f32 / 1000.0, 1.0, 1.0);
        assert!(a >= anterior, "no monotona en {i}");
        anterior = a;
    }
    assert_eq!(amplitud(2.0, 1.0, 1.0), 65535, "se recorta por arriba");
    assert_eq!(amplitud(-0.5, 1.0, 1.0), 0, "se recorta por abajo");
}

/// §5: el polo de un tick a 48 kHz. Responde a un escalon como 1 − e^(−n/4,8)
/// por muestra, sin mirar el tick siguiente (es causal: solo usa z e y_f), y su
/// constante es la de la hoja: K48 = 1 − e^(−1/4,8).
#[test]
fn el_polo_del_escritor_de_corte_responde_al_escalon_como_un_polo_de_un_tick() {
    assert!((K48 - (1.0 - libm::expf(-1.0 / 4.8))).abs() < 1e-6);
    let mut z = 0.0f32;
    for n in 1..=48 {
        z = polo_48k(z, 1.0);
        let esperado = 1.0 - libm::expf(-(n as f32) / 4.8);
        assert!((z - esperado).abs() < 1e-4, "muestra {n}: {z} vs {esperado}");
    }
    // sirve con 4, 5 o 6 muestras por tick: la respuesta no depende de la razon
    // de relojes, solo de cuantas muestras han pasado.
    let mut z = 0.0f32;
    for _ in 0..5 {
        z = polo_48k(z, 1.0);
    }
    assert!((z - (1.0 - libm::expf(-5.0 / 4.8))).abs() < 1e-4);
}

/// §5: `f = f_base · 2^(cantidad · y_f / 1200)`, cantidad en cents, bipolar.
/// Con y_f = 1 y cantidad = 1200 sube una octava; con −1200 baja una; con y_f = 0
/// no mueve nada; ±4 800 son cuatro octavas.
#[test]
fn la_cantidad_del_filtro_se_aplica_en_octavas() {
    assert!((corte_hz(440.0, 1200, 1.0) - 880.0).abs() < 1e-2);
    assert!((corte_hz(440.0, -1200, 1.0) - 220.0).abs() < 1e-2);
    assert!((corte_hz(440.0, 4800, 1.0) - 7040.0).abs() < 0.1);
    assert!((corte_hz(440.0, -4800, 1.0) - 27.5).abs() < 1e-2);
    for c in [-4800i16, -1200, 0, 700, 1200, 4800] {
        assert!((corte_hz(440.0, c, 0.0) - 440.0).abs() < 1e-3, "y_f = 0 no mueve, c={c}");
    }
    // a mitad de envolvente, media cantidad: 1200 cents con y_f = 0,5 es medio octava
    assert!((corte_hz(440.0, 1200, 0.5) - 440.0 * libm::sqrtf(2.0)).abs() < 1e-2);
}
```

- [ ] **Paso 2: correr y ver el rojo**

Correr: `cd software/nucleo/core && cargo test --test escritor`
Esperado: FALLA en compilación, `could not find escritor in sam17_nucleo_core`.
Pegar el rojo en el informe.

- [ ] **Paso 3: la implementación mínima**

`software/nucleo/core/src/escritor.rs`:

```rust
//! Los escritores del modulo de Voz (papel §1): lo que convierte niveles de los
//! generadores en palabras de DAC, consumiendo parametros VIVOS del modelo.
//! Un escritor no es un generador: no se dispara y no tiene etapas. Por S-9
//! (voz-total §2) el micro es el unico escritor de sus CV.
//!
//! Papel: `docs/superpowers/specs/2026-09-02-generador-de-envolvente-design.md`,
//! §4 (el escritor del VCA) y §5 (el contrato del escritor de corte).
//!
//! **HUECO (decision 15):** aqui la salida del VCA es AMPLITUD lineal en 16
//! bits. La ley palabra -> ganancia del SSI2164 (control exponencial, de
//! catalogo) no esta en ningun papel ni su hoja en el arbol; `ley_vca` se
//! escribe cuando entre, en este archivo, y `ley_vca(0)` tiene que cerrar el
//! VCA (voz-total §9.1).

use crate::fuerza::Fuerza;

/// Papel §5: el polo de un tick del escritor de corte, a 48 kHz. Un tick de
/// 10 kHz son 4,8 muestras: `K48 = 1 - e^(-1/4,8) = 0,18807`. Causal y sin
/// mirar el tick siguiente; el gemelo digital de la RC del DAC del VCA.
pub const K48: f32 = 0.188_069_97;

/// Papel §4.1: `g_v = (1 - s) + s * v`. Lineal a proposito: la curva ya la puso
/// MIDI 2.0 al escalar los 7 bits (`fuerza.rs`).
pub fn ganancia_fuerza(fuerza: Fuerza, sensibilidad_milesimas: u16) -> f32 {
    let s = sensibilidad_milesimas.min(1000) as f32 / 1000.0;
    let v = fuerza.0 as f32 / 65535.0;
    (1.0 - s) + s * v
}

/// Papel §4.2: potencia constante. `p = paneo / 1000`; `L = cos(p * pi/2)`,
/// `R = sin(p * pi/2)`; el centro queda a -3 dB en cada rama.
pub fn factores_paneo(paneo_milesimas: u16) -> (f32, f32) {
    let p = paneo_milesimas.min(1000) as f32 / 1000.0;
    let angulo = p * core::f32::consts::FRAC_PI_2;
    (libm::cosf(angulo), libm::sinf(angulo))
}

/// Papel §4.3: la amplitud `y * g_v * factor`, redondeada a 16 bits y recortada
/// a [0, 65 535]. Con `y = 0` la palabra es cero (voz-total §9.1).
pub fn amplitud(y: f32, g_v: f32, factor: f32) -> u16 {
    let a = (y * g_v * factor).clamp(0.0, 1.0);
    libm::roundf(a * 65535.0) as u16
}

/// Papel §5: un paso del polo a 48 kHz sobre la envolvente del filtro.
pub fn polo_48k(z: f32, y_f: f32) -> f32 {
    z + K48 * (y_f - z)
}

/// Papel §5: la cantidad se aplica en octavas, `f = f_base * 2^(c * y_f / 1200)`.
pub fn corte_hz(f_base_hz: f32, cantidad_cents: i16, y_f: f32) -> f32 {
    f_base_hz * libm::exp2f(cantidad_cents as f32 * y_f / 1200.0)
}
```

Y en `lib.rs`, en orden alfabético: `pub mod escritor;` (entre `descubrimiento` y
`fuerza`).

- [ ] **Paso 4: correr y ver el verde**

Correr: `cargo test --test escritor`
Esperado: 5 tests, `ok`. Si `amplitud(1.0, 0.5, 1.0)` no da 32 768 por el redondeo
de `libm::roundf` (que redondea medios hacia fuera de cero), el test tiene razón y
la implementación no: no ablandar el test.

- [ ] **Paso 5: clippy, fmt, y seguir**

Correr: `cargo clippy --all-targets -- -D warnings && cargo fmt --check`.
No hay commit por tarea: el ejecutor **no hace commit ni push** (regla dura del
worktree); deja el árbol sucio y pasa a la tarea 2.

---

### Tarea 2: `envolvente.rs` — el `Generador`, una envolvente

**Archivos:**
- Crear: `software/nucleo/core/src/envolvente.rs`
- Crear: `software/nucleo/core/tests/envolvente.rs`
- Modificar: `software/nucleo/core/src/lib.rs` (añadir `pub mod envolvente;` entre
  `descubrimiento` y `escritor`)

**Interfaces:**
- Consume: nada de otras tareas (la tarea 3 le añade el `Canal` encima).
- Produce (los usa la tarea 3, nombres exactos):

```rust
pub const F_RENDER_HZ: u32 = 10_000;
pub const TICKS_POR_MS: u32 = 10;
pub const NIVEL_OCIOSO: f32 = 1.0 / 65_536.0;
pub const DESTINO_ATAQUE: f32 = 1.5;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Etapa { Ocioso, Ataque, Decaimiento, Sostenido, Relajacion }

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Tiempos { pub ataque_ms: u32, pub decaimiento_ms: u32, pub relajacion_ms: u32 }

pub struct Generador { /* privado */ }
impl Generador {
    pub const fn nuevo() -> Self;                       // Ocioso, nivel 0
    pub fn etapa(&self) -> Etapa;
    pub fn nivel(&self) -> f32;
    /// Captura `tiempos`, arranca el ataque desde `desde` (0..=1). Con
    /// `desde >= 1` no hay ataque: entra en decaimiento. `disparo` es el
    /// borde `dispara`: al terminar el decaimiento pasa a relajacion.
    pub fn abrir(&mut self, tiempos: Tiempos, desde: f32, disparo: bool);
    /// Relajacion desde el nivel actual. Sobre un ocioso no hace nada.
    pub fn cerrar(&mut self);
    /// Un tick de 100 us. `sostenido_milesimas` es el parametro VIVO.
    /// Devuelve el nivel tras el tick.
    pub fn tick(&mut self, sostenido_milesimas: u16) -> f32;
}
```

**La aritmética, del papel §2, para que no se derive dos veces:**

```
k(tau_ms) = 1 - exp(-0,1 / tau_ms)                 (dt = 0,1 ms)
Ataque:      tau_A = T_A / ln 3;  destino 1,5;
             desde y0: N_A = round(T_A * 10 * ln((1,5 - y0) / 0,5) / ln 3) ticks
             (desde 0 sale N_A = T_A * 10 exacto). Al tick N_A: y := 1.
Decaimiento: tau_D = T_D / ln 1000; destino S (vivo); N_D = T_D * 10 ticks.
             Al tick N_D: y := S. Si al entrar S >= 1: sin decaimiento.
             Despues: Sostenido, o Relajacion si `disparo`.
Sostenido:   y := S en cada tick.
Relajacion:  tau_R = T_R / ln 1000; destino 0; se calcula AL CERRAR desde y0:
             N_R = ceil(T_R * 10 * ln(y0 / NIVEL_OCIOSO) / ln 1000) ticks
             (si y0 <= NIVEL_OCIOSO, N_R = 0). Al tick N_R: y := 0, Ocioso.
```

Todas las etapas terminan **por cuenta**; la forma dentro de la etapa es la
recurrencia `y += k * (destino - y)`. La relajación se cuenta desde el nivel de
partida porque su duración depende de él (papel §2.2): 1,61·T_R desde 1, 1,27·T_R
desde 100 ‰.

- [ ] **Paso 1: escribir los tests, que fallan**

`software/nucleo/core/tests/envolvente.rs` (primera mitad; la tarea 3 añade la
segunda):

```rust
//! El generador de envolvente: la maquina de cuatro etapas, cerrada entre bordes.
//! Papel: `docs/superpowers/specs/2026-09-02-generador-de-envolvente-design.md`,
//! §2 (las etapas terminan por cuenta de ticks), §2.1 (ataque RC truncado),
//! §2.2 (decaimiento y relajacion a -60 dB), §2.3 (sostenido vivo, sin filtro),
//! §3.1 (los tres bordes).

use sam17_nucleo_core::envolvente::{Etapa, Generador, Tiempos, NIVEL_OCIOSO, TICKS_POR_MS};

const T: Tiempos = Tiempos { ataque_ms: 10, decaimiento_ms: 20, relajacion_ms: 30 };

fn tiempos(a: u32, d: u32, r: u32) -> Tiempos {
    Tiempos { ataque_ms: a, decaimiento_ms: d, relajacion_ms: r }
}

/// Avanza `n` ticks con el sostenido dado y devuelve el nivel final.
fn avanzar(g: &mut Generador, n: u32, sostenido: u16) -> f32 {
    let mut y = g.nivel();
    for _ in 0..n {
        y = g.tick(sostenido);
    }
    y
}

/// §2.1: desde cero el ataque es monotono, vale exactamente 1 en el tick T_A y
/// a mitad de camino vale 1,5·(1 − 3^(−1/2)) = 0,634 (la forma RC truncada, no
/// solo el fin). Se barre T_A por todo el rango firmado (§7).
#[test]
fn el_ataque_llega_al_pico_en_su_tiempo_y_tiene_la_forma_rc_truncada() {
    for t_a in [1u32, 3, 10, 100, 1_000, 10_000] {
        let mut g = Generador::nuevo();
        g.abrir(tiempos(t_a, 10, 10), 0.0, false);
        assert_eq!(g.etapa(), Etapa::Ataque);
        let n = t_a * TICKS_POR_MS;
        let mut anterior = 0.0f32;
        for i in 1..n {
            let y = g.tick(700);
            assert!(y >= anterior, "T_A={t_a}: no monotono en el tick {i}");
            assert!(y < 1.0, "T_A={t_a}: llego al pico antes de tiempo, tick {i}");
            if i == n / 2 && n >= 2 {
                let esperado = 1.5 * (1.0 - 1.0 / libm::sqrtf(3.0));
                assert!((y - esperado).abs() < 1e-3, "T_A={t_a}: a mitad {y} vs {esperado}");
            }
            anterior = y;
        }
        let y = g.tick(700);
        assert_eq!(y, 1.0, "T_A={t_a}: en el tick N_A el nivel es exactamente 1");
        assert_eq!(g.etapa(), Etapa::Decaimiento);
    }
}

/// §2.2: el decaimiento cae monotono hacia S, vale exactamente S en el tick T_D
/// y a mitad de camino la distancia a S es 1000^(−1/2) = 3,2 % de (1 − S).
/// Con S = 1000 no hay decaimiento. Se barren S y T_D.
#[test]
fn el_decaimiento_llega_al_sostenido_en_su_tiempo_con_forma_exponencial() {
    for s in [0u16, 100, 500, 700, 900, 999] {
        for t_d in [1u32, 3, 10, 100, 1_000, 10_000] {
            let mut g = Generador::nuevo();
            g.abrir(tiempos(1, t_d, 10), 0.0, false);
            avanzar(&mut g, 10, s); // el ataque de 1 ms entero
            assert_eq!(g.etapa(), Etapa::Decaimiento, "S={s} T_D={t_d}");
            let n = t_d * TICKS_POR_MS;
            let s_f = s as f32 / 1000.0;
            let mut anterior = 1.0f32;
            for i in 1..n {
                let y = g.tick(s);
                assert!(y <= anterior, "S={s} T_D={t_d}: subio en el tick {i}");
                if i == n / 2 && n >= 2 {
                    let esperado = s_f + (1.0 - s_f) / libm::sqrtf(1000.0);
                    assert!((y - esperado).abs() < 1e-3, "S={s} T_D={t_d}: a mitad {y} vs {esperado}");
                }
                anterior = y;
            }
            let y = g.tick(s);
            assert_eq!(y, s_f, "S={s} T_D={t_d}: en el tick N_D el nivel es exactamente S");
            assert_eq!(g.etapa(), Etapa::Sostenido);
        }
    }
    let mut g = Generador::nuevo();
    g.abrir(tiempos(1, 100, 10), 0.0, false);
    avanzar(&mut g, 10, 1000);
    assert_eq!(g.etapa(), Etapa::Sostenido, "con S = 1000 no hay decaimiento");
    assert_eq!(g.nivel(), 1.0);
}

/// §2.3: en sostenido el nivel ES el parametro, en el mismo tick y sin filtro
/// (R-M1: el modulo no suaviza). Y el decaimiento apunta al S vivo.
#[test]
fn el_sostenido_sigue_al_parametro_en_el_acto_y_sin_filtro() {
    let mut g = Generador::nuevo();
    g.abrir(tiempos(1, 1, 10), 0.0, false);
    avanzar(&mut g, 20, 500);
    assert_eq!(g.etapa(), Etapa::Sostenido);
    assert_eq!(g.tick(500), 0.5);
    assert_eq!(g.tick(900), 0.9, "sube en el acto");
    assert_eq!(g.tick(100), 0.1, "baja en el acto");
    assert_eq!(g.tick(0), 0.0, "un sostenido a cero es cero, y la etapa sigue siendo sostenido");
    assert_eq!(g.etapa(), Etapa::Sostenido);
}

/// §2.2: la relajacion arranca desde el nivel de partida y termina en el tick
/// en que la curva cruza NIVEL_OCIOSO: `ceil(T_R·10·ln(y0/NIVEL_OCIOSO)/ln 1000)`.
/// Desde 1 son 1,61·T_R; desde 100 ‰, 1,27·T_R. Se barren T_R y y0 (§8, test 3).
#[test]
fn la_relajacion_termina_donde_cruza_el_nivel_ocioso_desde_cualquier_partida() {
    for t_r in [1u32, 10, 100, 1_000, 20_000] {
        for s in [1000u16, 700, 300, 100] {
            let mut g = Generador::nuevo();
            g.abrir(tiempos(1, 1, t_r), 0.0, false);
            avanzar(&mut g, 20, s);
            assert_eq!(g.etapa(), Etapa::Sostenido);
            let y0 = g.nivel();
            g.cerrar();
            assert_eq!(g.etapa(), Etapa::Relajacion);
            let esperado = libm::ceilf(
                t_r as f32 * TICKS_POR_MS as f32 * libm::logf(y0 / NIVEL_OCIOSO) / libm::logf(1000.0),
            ) as u32;
            let mut n = 0u32;
            let mut anterior = y0;
            while g.etapa() == Etapa::Relajacion {
                let y = g.tick(s);
                assert!(y <= anterior, "T_R={t_r} S={s}: subio en relajacion");
                anterior = y;
                n += 1;
                assert!(n <= esperado + 1, "T_R={t_r} S={s}: no termina");
            }
            assert_eq!(n, esperado, "T_R={t_r} S={s}: termino en otro tick");
            assert_eq!(g.nivel(), 0.0, "al terminar el nivel es exactamente cero");
            assert_eq!(g.etapa(), Etapa::Ocioso);
        }
    }
    // desde el pico, la relacion del papel: 1,61 * T_R
    let mut g = Generador::nuevo();
    g.abrir(tiempos(1, 1, 300), 0.0, false);
    avanzar(&mut g, 20, 1000);
    g.cerrar();
    let mut n = 0;
    while g.etapa() == Etapa::Relajacion {
        g.tick(1000);
        n += 1;
    }
    assert!((n as f32 / 3000.0 - 1.605).abs() < 0.002, "1,6 x T_R desde el pico: {n}");
}

/// §3.1: `dispara` recorre ataque -> decaimiento -> relajacion sin sostener; con
/// S = 0 la relajacion arranca en cero y termina en el acto.
#[test]
fn dispara_recorre_sus_etapas_sin_sostener() {
    let mut g = Generador::nuevo();
    g.abrir(tiempos(2, 3, 5), 0.0, true);
    assert_eq!(g.etapa(), Etapa::Ataque);
    avanzar(&mut g, 20, 500);
    assert_eq!(g.etapa(), Etapa::Decaimiento);
    avanzar(&mut g, 29, 500);
    assert_eq!(g.etapa(), Etapa::Decaimiento);
    g.tick(500);
    assert_eq!(g.etapa(), Etapa::Relajacion, "al llegar al sostenido, relajacion");
    assert_eq!(g.nivel(), 0.5);
    let mut n = 0;
    while g.etapa() == Etapa::Relajacion {
        g.tick(500);
        n += 1;
        assert!(n < 1000);
    }
    assert_eq!(g.etapa(), Etapa::Ocioso);

    let mut g = Generador::nuevo();
    g.abrir(tiempos(1, 1, 100), 0.0, true);
    avanzar(&mut g, 20, 0);
    assert_eq!(g.etapa(), Etapa::Ocioso, "con S = 0 la relajacion arranca en cero y ya esta");
}

/// §3.1 y §3.2: `cerrar` en cualquier etapa lleva a relajacion desde el nivel
/// actual; sobre un ocioso no hace nada; `abrir` desde un nivel > 0 llega al
/// pico antes (tau_A * ln((1,5 - y0)/0,5)), y desde >= 1 entra directo en
/// decaimiento.
#[test]
fn cerrar_y_reabrir_continuan_desde_el_nivel_actual() {
    let mut g = Generador::nuevo();
    g.cerrar();
    assert_eq!(g.etapa(), Etapa::Ocioso, "cerrar un ocioso no hace nada");

    g.abrir(T, 0.0, false);
    avanzar(&mut g, 50, 700);
    assert_eq!(g.etapa(), Etapa::Ataque);
    let y = g.nivel();
    g.cerrar();
    assert_eq!(g.etapa(), Etapa::Relajacion);
    assert_eq!(g.nivel(), y, "la relajacion arranca donde estaba");

    let mut g = Generador::nuevo();
    g.abrir(tiempos(100, 10, 10), 0.5, false);
    let esperado = libm::roundf(1000.0 * libm::logf((1.5 - 0.5) / 0.5) / libm::logf(3.0)) as u32;
    let mut n = 0;
    while g.etapa() == Etapa::Ataque {
        g.tick(700);
        n += 1;
    }
    assert_eq!(n, esperado, "desde 0,5 el ataque de 100 ms dura tau_A*ln 2");
    assert_eq!(g.nivel(), 1.0);

    let mut g = Generador::nuevo();
    g.abrir(T, 1.0, false);
    assert_eq!(g.etapa(), Etapa::Decaimiento, "desde 1 no hay ataque");
    assert_eq!(g.nivel(), 1.0);
}

/// §3.3: la captura. Los tiempos son los del borde; cambiarlos con la nota
/// abierta no cambia esa nota. (El sostenido no se captura: test de arriba.)
#[test]
fn los_tiempos_se_capturan_al_borde_y_la_nota_corre_con_su_copia() {
    // Dos generadores identicos abiertos con T_A = 10 ms; el segundo "cambia" el
    // parametro despues de abrir, pero `abrir` ya copio: no hay como cambiarlo
    // sin un borde nuevo, y eso es exactamente la captura. Se prueba que dos
    // aperturas con tiempos distintos dan dos notas distintas y que la copia es
    // de cada borde.
    let mut corta = Generador::nuevo();
    let mut larga = Generador::nuevo();
    corta.abrir(tiempos(10, 10, 10), 0.0, false);
    larga.abrir(tiempos(100, 10, 10), 0.0, false);
    avanzar(&mut corta, 100, 700);
    avanzar(&mut larga, 100, 700);
    assert_eq!(corta.etapa(), Etapa::Decaimiento);
    assert_eq!(larga.etapa(), Etapa::Ataque);
    // reabrir con otros tiempos captura los nuevos
    larga.abrir(tiempos(1, 1, 1), larga.nivel(), false);
    avanzar(&mut larga, 30, 700);
    assert_eq!(larga.etapa(), Etapa::Sostenido, "la segunda nota corre con su propia copia");
}
```

- [ ] **Paso 2: correr y ver el rojo**

Correr: `cargo test --test envolvente`
Esperado: FALLA en compilación, `could not find envolvente`. Pegar el rojo.

- [ ] **Paso 3: la implementación mínima**

`software/nucleo/core/src/envolvente.rs` (primera mitad):

```rust
//! El generador de envolvente del modulo de Voz: la maquina de cuatro etapas,
//! cerrada entre dos bordes. Papel:
//! `docs/superpowers/specs/2026-09-02-generador-de-envolvente-design.md`.
//!
//! - La forma es la del circuito de la tesis (`docs/modules/06-adsr.md`): un
//!   condensador que carga y descarga. Cada etapa es `y += k * (destino - y)`
//!   con `k = 1 - exp(-dt / tau)`, calculada UNA vez al capturar (§2).
//! - Las etapas de duracion conocida terminan POR CUENTA DE TICKS y ajustan el
//!   nivel exacto al terminar. La junta corrio el fin por umbral en `f32` y no
//!   terminaba en 11 de 36 casillas del barrido (§2, §12).
//! - El ataque es una carga RC truncada: apunta a 1,5 (el pico es 2/3 del
//!   destino, el umbral del 555 de la tesis) y se corta al llegar (§2.1).
//! - Decaimiento y relajacion se miden en RT60: el tiempo en que el recorrido
//!   cae a la milesima (§2.2). La relajacion se cuenta desde el nivel de
//!   partida, porque su duracion depende de el.
//! - El sostenido NO se captura y aplica en el tick, sin filtro: S-12 lo hizo
//!   vivo y R-M1 prohibe suavizar dentro del modulo (§2.3).

/// voz-total §3.1: la tasa de render de la clase lenta.
pub const F_RENDER_HZ: u32 = 10_000;
/// Un milisegundo son diez ticks, exactos.
pub const TICKS_POR_MS: u32 = 10;
/// Papel §6: el nivel por debajo del cual una envolvente se declara terminada.
/// Constante del MODELO: hoy coincide con el LSB de 16 bits; si el DAC cambia
/// de ancho, esta no lo sigue.
pub const NIVEL_OCIOSO: f32 = 1.0 / 65_536.0;
/// Papel §2.1: el ataque apunta a 1,5 y se trunca en 1.
pub const DESTINO_ATAQUE: f32 = 1.5;

const DT_MS: f32 = 0.1;
const LN_3: f32 = 1.098_612_3;
const LN_1000: f32 = 6.907_755_3;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Etapa {
    Ocioso,
    Ataque,
    Decaimiento,
    Sostenido,
    Relajacion,
}

/// Los tres tiempos que se capturan al borde (papel §3.3). Rangos firmados en
/// §7: ataque y decaimiento 1..=10 000 ms, relajacion 1..=20 000 ms; el modulo
/// no los valida, los valida el descriptor.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Tiempos {
    pub ataque_ms: u32,
    pub decaimiento_ms: u32,
    pub relajacion_ms: u32,
}

fn k(tau_ms: f32) -> f32 {
    1.0 - libm::expf(-DT_MS / tau_ms)
}

pub struct Generador {
    etapa: Etapa,
    y: f32,
    k: f32,
    restantes: u32,
    disparo: bool,
    tiempos: Tiempos,
}

impl Generador {
    pub const fn nuevo() -> Self {
        Generador {
            etapa: Etapa::Ocioso,
            y: 0.0,
            k: 0.0,
            restantes: 0,
            disparo: false,
            tiempos: Tiempos { ataque_ms: 0, decaimiento_ms: 0, relajacion_ms: 0 },
        }
    }

    pub fn etapa(&self) -> Etapa {
        self.etapa
    }

    pub fn nivel(&self) -> f32 {
        self.y
    }

    /// Captura `tiempos` y arranca el ataque desde `desde` (§2.1, §3.2). Con
    /// `desde >= 1` no hay ataque: entra en decaimiento. `disparo` es el borde
    /// `dispara` (§3.1).
    pub fn abrir(&mut self, tiempos: Tiempos, desde: f32, disparo: bool) {
        self.tiempos = tiempos;
        self.disparo = disparo;
        let desde = desde.clamp(0.0, 1.0);
        if desde >= 1.0 {
            self.y = 1.0;
            self.entrar_en_decaimiento(None);
            return;
        }
        self.y = desde;
        let tau = tiempos.ataque_ms as f32 / LN_3;
        self.k = k(tau);
        let ticks = tiempos.ataque_ms as f32 * TICKS_POR_MS as f32
            * libm::logf((DESTINO_ATAQUE - desde) / (DESTINO_ATAQUE - 1.0))
            / LN_3;
        self.restantes = (libm::roundf(ticks) as u32).max(1);
        self.etapa = Etapa::Ataque;
    }

    /// Relajacion desde el nivel actual (§2.2). Sobre un ocioso no hace nada.
    pub fn cerrar(&mut self) {
        if self.etapa == Etapa::Ocioso {
            return;
        }
        if self.y <= NIVEL_OCIOSO {
            self.y = 0.0;
            self.etapa = Etapa::Ocioso;
            return;
        }
        let tau = self.tiempos.relajacion_ms as f32 / LN_1000;
        self.k = k(tau);
        let ticks = self.tiempos.relajacion_ms as f32 * TICKS_POR_MS as f32
            * libm::logf(self.y / NIVEL_OCIOSO)
            / LN_1000;
        self.restantes = (libm::ceilf(ticks) as u32).max(1);
        self.etapa = Etapa::Relajacion;
    }

    /// `sostenido` es el parametro vivo, en milesimas; `None` significa
    /// «todavia no lo se» (solo lo usa `abrir` desde >= 1, que no puede saltar
    /// el decaimiento sin conocerlo): entra en decaimiento y el primer tick
    /// decide.
    fn entrar_en_decaimiento(&mut self, sostenido: Option<f32>) {
        if let Some(s) = sostenido {
            if s >= 1.0 {
                self.y = 1.0;
                self.terminar_decaimiento(s);
                return;
            }
        }
        let tau = self.tiempos.decaimiento_ms as f32 / LN_1000;
        self.k = k(tau);
        self.restantes = self.tiempos.decaimiento_ms * TICKS_POR_MS;
        self.etapa = Etapa::Decaimiento;
    }

    fn terminar_decaimiento(&mut self, s: f32) {
        self.y = s;
        if self.disparo {
            self.etapa = Etapa::Sostenido;
            self.cerrar();
        } else {
            self.etapa = Etapa::Sostenido;
        }
    }

    /// Un tick de 100 us con el sostenido vivo. Devuelve el nivel tras el tick.
    pub fn tick(&mut self, sostenido_milesimas: u16) -> f32 {
        let s = sostenido_milesimas.min(1000) as f32 / 1000.0;
        match self.etapa {
            Etapa::Ocioso => {}
            Etapa::Ataque => {
                self.y += self.k * (DESTINO_ATAQUE - self.y);
                self.restantes -= 1;
                if self.restantes == 0 {
                    self.y = 1.0;
                    self.entrar_en_decaimiento(Some(s));
                }
            }
            Etapa::Decaimiento => {
                if s >= 1.0 {
                    // el sostenido vivo subio a 1: no queda distancia que caer
                    self.y = 1.0;
                    self.terminar_decaimiento(s);
                } else {
                    self.y += self.k * (s - self.y);
                    self.restantes -= 1;
                    if self.restantes == 0 {
                        self.terminar_decaimiento(s);
                    }
                }
            }
            Etapa::Sostenido => {
                self.y = s;
            }
            Etapa::Relajacion => {
                self.y -= self.k * self.y;
                self.restantes -= 1;
                if self.restantes == 0 {
                    self.y = 0.0;
                    self.etapa = Etapa::Ocioso;
                }
            }
        }
        self.y
    }
}
```

Y en `lib.rs`: `pub mod envolvente;`.

Dos avisos al ejecutor: (1) `abrir` con `desde >= 1` no conoce el sostenido y no
puede decidir si salta el decaimiento; por eso entra en decaimiento y el primer
tick, que sí lo conoce, lo resuelve. Si el test 2 («con S = 1000 no hay
decaimiento») exige que la etapa sea `Sostenido` **inmediatamente** tras el ataque,
la transición del ataque pasa `Some(s)` y ya lo hace. (2) El test 3 pide
`g.tick(0) == 0.0` **sin salir de sostenido**: un sostenido a cero no es silencio;
solo `cerrar` lleva a relajación.

- [ ] **Paso 4: correr y ver el verde**

Correr: `cargo test --test envolvente`
Esperado: 7 tests, `ok`. Si alguna casilla del barrido no cuadra con ±1e-3 en la
forma, o con la cuenta exacta de ticks, **es información**: pegar la casilla en el
informe con los números, no ablandar la tolerancia. La junta ya corrió esta
aritmética en `f32` y la relajación y el ataque cerraban; el decaimiento cierra
por construcción con la cuenta.

- [ ] **Paso 5: clippy y fmt, y a la tarea 3**

Correr: `cargo clippy --all-targets -- -D warnings && cargo fmt --check`.

---

### Tarea 3: `envolvente.rs` — el `Canal`, los `Generadores` y el tick

**Archivos:**
- Modificar: `software/nucleo/core/src/envolvente.rs` (añadir la segunda mitad)
- Modificar: `software/nucleo/core/tests/envolvente.rs` (añadir la segunda mitad)

**Interfaces:**
- Consume: la tarea 1 (`escritor::{ganancia_fuerza, factores_paneo, amplitud}`) y
  la tarea 2 (`Generador`, `Tiempos`, `Etapa`, `NIVEL_OCIOSO`).
- Produce (los usará el firmware del N657 y, un día, el descriptor):

```rust
pub const CANALES: usize = 16;
pub const CAPACIDAD_COLA: usize = 64;                 // papel §3.5
pub const FUERZA_REPARACION: Fuerza = Fuerza(u16::MAX); // papel §3.4, decision 12

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Borde { Abre, Cierra, Dispara }

/// Los parametros por voz del papel §7. Los tiempos se capturan al borde; el
/// sostenido, el paneo y la cantidad son vivos (§3.3).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Parametros {
    pub vca: Tiempos,
    pub vca_sostenido: u16,        // milesimas
    pub filtro: Tiempos,
    pub filtro_sostenido: u16,     // milesimas
    pub sensibilidad_fuerza: u16,  // milesimas
    pub filtro_cantidad: i16,      // cents, bipolar
    pub paneo: u16,                // milesimas, 0 = izquierda
}

/// Lo que entra por la cola (§3.5). Lo encola la ISR del J2; lo drena el tick.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Entrada {
    Evento { canal: u8, borde: Borde, fuerza: Fuerza },
    Parametros { canal: u8, parametros: Parametros },
    /// R-E10: la mascara de compuertas (`abre`/`cierra`, nunca disparos) y el
    /// contador de eventos emitidos por el cerebro (§3.4).
    Compuerta { mascara: u16, contador: u16 },
    /// El watchdog de trama (voz-total §9.2).
    SoltarTodo,
    /// El firmware latcheo el crosspoint: los canales en conmutacion se sueltan.
    Conmutado,
}

/// Lo que sale por tick: por canal, las dos amplitudes del VCA (L, R) y el
/// nivel de la envolvente del filtro, en 16 bits.
pub struct Salida {
    pub vca: [[u16; 2]; CANALES],
    pub filtro: [u16; CANALES],
}

pub struct Generadores { /* privado */ }
impl Generadores {
    /// Todos los canales con `parametros`; ningun valor por defecto en core.
    pub fn nuevos(parametros: Parametros) -> Self;
    /// Drena `entradas` EN ORDEN y avanza un tick. El unico que muta el estado.
    pub fn tick(&mut self, entradas: &[Entrada]) -> Salida;
    /// Papel §6: bit en 1 = el generador de VCA del canal esta ocioso.
    pub fn en_silencio(&self) -> u16;
    /// Papel §6: `Commit.cambian`. Un `abre`/`dispara` sobre esos canales espera
    /// en su ranura hasta `Entrada::Conmutado`; un `cierra` aplica en el acto.
    pub fn bloquear_apertura(&mut self, cambian: u16);
    /// La compuerta propia de cada canal (§3.4), para el descriptor y los tests.
    pub fn compuertas(&self) -> u16;
    pub fn etapa(&self, canal: u8) -> Etapa;      // la del VCA
    pub fn eventos_recibidos(&self) -> u16;
}
```

**Las reglas, del papel, que la implementación tiene que cumplir:**

1. **Orden del tick** (§3.5): drenar `entradas` en orden, aplicando cada una; luego
   avanzar los 32 generadores un tick; luego calcular la `Salida`.
2. **`Evento`** (§3.1): `recibidos += 1` (wrapping). `Abre`/`Dispara` sobre un canal
   en conmutación se guarda en la ranura `diferido` del canal (la última manda) y
   no aplica; si no, aplica. `Cierra` aplica siempre y borra el diferido.
3. **Aplicar `Abre`/`Dispara`** (§3.2, §3.3): `g_nueva = ganancia_fuerza(fuerza,
   p.sensibilidad_fuerza)`. Si el VCA está ocioso, `desde = 0`. Si no:
   `a0 = vca.nivel() * g_v`; `desde = if g_nueva <= 0 { if a0 > 0 {1} else {0} }
   else { min(1, a0 / g_nueva) }`. Luego `vca.abrir(p.vca, desde, disparo)`,
   `filtro.abrir(p.filtro, filtro.nivel(), disparo)`, `g_v = g_nueva`,
   `compuerta = (borde == Abre)`.
4. **Aplicar `Cierra`**: `vca.cerrar()`, `filtro.cerrar()`, `compuerta = false`.
5. **`Parametros`**: se copian a la ranura del canal; se recalculan `(l, r)` con
   `factores_paneo(p.paneo)`. Los generadores en vuelo no se tocan (captura).
6. **`Compuerta { mascara, contador }`** (§3.4): si `resincronizar`, `recibidos =
   contador` y se apaga la bandera; si no, si `(contador.wrapping_sub(recibidos) as
   i16) < 0` el bloque es viejo y **no hace nada**. Luego, por canal: bit en 1 y
   compuerta propia baja → aplicar `Abre` con `FUERZA_REPARACION` (respetando la
   conmutación: se difiere igual que un evento); bit en 0 y compuerta propia alta →
   aplicar `Cierra`; en otro caso nada.
7. **`SoltarTodo`** (§3.4): todos los canales `Cierra`, diferidos borrados,
   `resincronizar = true`.
8. **`Conmutado`**: `en_conmutacion = 0` y se aplican los diferidos, en orden de
   canal.
9. **Salida**: `y = vca.tick(p.vca_sostenido)`, `y_f = filtro.tick(p.filtro_sostenido)`,
   `vca[i] = [amplitud(y, g_v, l), amplitud(y, g_v, r)]`,
   `filtro[i] = round(y_f * 65535)`.
10. **`en_silencio`**: bit `i` en 1 si `vca.etapa() == Ocioso`.

- [ ] **Paso 1: escribir los tests, que fallan**

Añadir a `software/nucleo/core/tests/envolvente.rs`:

```rust
use sam17_nucleo_core::envolvente::{
    Borde, Entrada, Generadores, Parametros, Salida, CANALES, FUERZA_REPARACION,
};
use sam17_nucleo_core::escritor::{amplitud, factores_paneo, ganancia_fuerza};
use sam17_nucleo_core::fuerza::Fuerza;

fn parametros() -> Parametros {
    Parametros {
        vca: tiempos(10, 20, 30),
        vca_sostenido: 700,
        filtro: tiempos(5, 30, 30),
        filtro_sostenido: 300,
        sensibilidad_fuerza: 500,
        filtro_cantidad: 1200,
        paneo: 500,
    }
}

fn abre(canal: u8, fuerza: u16) -> Entrada {
    Entrada::Evento { canal, borde: Borde::Abre, fuerza: Fuerza(fuerza) }
}
fn cierra(canal: u8) -> Entrada {
    Entrada::Evento { canal, borde: Borde::Cierra, fuerza: Fuerza(0) }
}
fn dispara(canal: u8, fuerza: u16) -> Entrada {
    Entrada::Evento { canal, borde: Borde::Dispara, fuerza: Fuerza(fuerza) }
}
fn ticks(g: &mut Generadores, n: u32) -> Salida {
    let mut s = g.tick(&[]);
    for _ in 1..n {
        s = g.tick(&[]);
    }
    s
}

/// §3.2 y §8 test 5: la continuidad del re-disparo se mide en la AMPLITUD, no en
/// el nivel interno. Con fuerza mayor o igual, ningun salto mayor que un paso
/// del ataque mas corto; con fuerza menor, baja al techo nuevo en un tick y entra
/// en decaimiento.
#[test]
fn el_redisparo_es_continuo_en_la_amplitud_hacia_arriba_y_declara_el_escalon_hacia_abajo() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(0, 30000)]);
    let antes = ticks(&mut g, 60).vca[0][0]; // en mitad del ataque de 10 ms
    // re-disparo con MAS fuerza: continuo
    let despues = g.tick(&[abre(0, 65535)]).vca[0][0];
    let paso_maximo = amplitud(1.5 * (1.0 - libm::expf(-0.1 / (1.0 / 1.0986))), 1.0, 1.0);
    assert!(
        despues >= antes && despues - antes <= paso_maximo,
        "hacia arriba: {antes} -> {despues}, paso maximo {paso_maximo}"
    );
    assert_eq!(g.etapa(0), Etapa::Ataque);
    // re-disparo con MENOS fuerza que la amplitud que sonaba: baja al techo nuevo
    // en un tick y entra en decaimiento
    ticks(&mut g, 200);
    let sonaba = g.tick(&[]).vca[0][0];
    let (l, _) = factores_paneo(500);
    let techo = amplitud(1.0, ganancia_fuerza(Fuerza(0), 500), l);
    assert!(sonaba > techo, "el caso solo existe si lo que sonaba supera el techo nuevo");
    let tras = g.tick(&[abre(0, 0)]).vca[0][0];
    assert!(tras <= techo && techo - tras <= 1, "baja al techo nuevo en un tick: {tras} vs {techo}");
    assert_eq!(g.etapa(0), Etapa::Decaimiento, "desde >= 1: sin ataque");
}

/// §3.3: cambiar los tiempos con la nota abierta no cambia esa nota; cambiar el
/// sostenido si, en el mismo tick. §4.2: cambiar el paneo aplica en el tick
/// siguiente, sin rampa.
#[test]
fn los_parametros_vivos_aplican_en_el_acto_y_los_capturados_no() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(3, 65535)]);
    ticks(&mut g, 400); // ataque 10 ms + decaimiento 20 ms: en sostenido
    assert_eq!(g.etapa(3), Etapa::Sostenido);
    let mut p = parametros();
    p.vca = tiempos(1000, 1000, 1000);
    p.vca_sostenido = 200;
    p.paneo = 0;
    let s = g.tick(&[Entrada::Parametros { canal: 3, parametros: p }]);
    let (l, r) = factores_paneo(0);
    let g_v = ganancia_fuerza(Fuerza(65535), 500);
    assert_eq!(s.vca[3], [amplitud(0.2, g_v, l), amplitud(0.2, g_v, r)], "sostenido y paneo en el acto");
    // los tiempos nuevos NO tocan la nota en vuelo: al cerrar, la relajacion es
    // la capturada (30 ms), no la nueva (1000 ms)
    g.tick(&[cierra(3)]);
    let mut n = 0;
    while g.etapa(3) == Etapa::Relajacion {
        g.tick(&[]);
        n += 1;
        assert!(n < 2000, "la relajacion usa los 1000 ms nuevos: la captura fallo");
    }
}

/// §6: silencio = el generador de VCA esta ocioso. Sube exactamente en el tick en
/// que la relajacion termina; con dieciseis canales en etapas distintas la
/// mascara es correcta bit a bit; una nota a fuerza cero NO esta en silencio.
#[test]
fn la_mascara_de_silencio_es_el_generador_ocioso_y_no_la_palabra() {
    let mut g = Generadores::nuevos(parametros());
    assert_eq!(g.en_silencio(), 0xFFFF, "nace toda en silencio");
    let mut entradas = [abre(0, 65535); 8];
    for (i, e) in entradas.iter_mut().enumerate() {
        *e = abre(i as u8, 65535);
    }
    g.tick(&entradas);
    assert_eq!(g.en_silencio(), 0xFF00);
    g.tick(&[cierra(2), cierra(5)]);
    assert_eq!(g.en_silencio(), 0xFF00, "en relajacion no esta en silencio");
    let mut n = 0;
    while g.en_silencio() & 0b100 == 0 {
        g.tick(&[]);
        n += 1;
        assert!(n < 1000);
    }
    assert_eq!(g.en_silencio(), 0xFF24, "los canales 2 y 5 terminan a la vez");
    assert_eq!(g.etapa(2), Etapa::Ocioso);
    // una nota a fuerza cero con s = 1: la palabra es cero y el canal NO esta en silencio
    let mut p = parametros();
    p.sensibilidad_fuerza = 1000;
    let mut g = Generadores::nuevos(p);
    let s = g.tick(&[abre(9, 0)]);
    assert_eq!(s.vca[9], [0, 0]);
    assert_eq!(g.en_silencio() & (1 << 9), 0, "la envolvente corre aunque no se oiga");
}

/// §3.4: la red de R-E10 compara el bit contra la compuerta propia. Bit alto
/// sobre compuerta baja abre con FUERZA_REPARACION, tambien desde la relajacion;
/// bit bajo sobre compuerta alta cierra; `dispara` es invisible en las dos
/// direcciones; un bloque con contador viejo no hace nada.
#[test]
fn la_reafirmacion_compara_contra_la_compuerta_propia_y_dispara_es_invisible() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(0, 30000), dispara(1, 30000)]);
    assert_eq!(g.compuertas(), 0b01, "dispara no levanta la compuerta");
    assert_eq!(g.eventos_recibidos(), 2);
    ticks(&mut g, 50);
    // un bloque VIEJO (contador 1 < 2 recibidos) no hace nada
    g.tick(&[Entrada::Compuerta { mascara: 0, contador: 1 }]);
    assert_eq!(g.etapa(0), Etapa::Ataque, "un bloque viejo no cierra");
    // un bloque al dia que dice canal 0 cerrado y canal 4 abierto
    g.tick(&[Entrada::Compuerta { mascara: 0b10000, contador: 2 }]);
    assert_eq!(g.etapa(0), Etapa::Relajacion, "cerrada y compuerta alta: cierra");
    assert_eq!(g.etapa(1), Etapa::Ataque, "el tambor sigue: invisible con el bit bajo");
    assert_eq!(g.etapa(4), Etapa::Ataque, "abierta y compuerta baja: abre");
    assert_eq!(g.compuertas(), 0b10000);
    // el tambor termina y con el bit bajo NO resucita
    ticks(&mut g, 2000);
    assert_eq!(g.etapa(1), Etapa::Ocioso);
    g.tick(&[Entrada::Compuerta { mascara: 0b10000, contador: 2 }]);
    assert_eq!(g.etapa(1), Etapa::Ocioso, "dispara no resucita");
    // abierta sobre un canal en relajacion (compuerta baja) abre: el caso normal
    g.tick(&[cierra(4)]);
    assert_eq!(g.etapa(4), Etapa::Relajacion);
    g.tick(&[Entrada::Compuerta { mascara: 0b10000, contador: 3 }]);
    assert_eq!(g.etapa(4), Etapa::Ataque, "un abre perdido en relajacion se repara");
    // la fuerza de reparacion es la constante: la amplitud al pico es la de fuerza plena
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[Entrada::Compuerta { mascara: 1, contador: 0 }]);
    let s = ticks(&mut g, 100);
    let (l, _) = factores_paneo(500);
    assert_eq!(s.vca[0][0], amplitud(1.0, ganancia_fuerza(FUERZA_REPARACION, 500), l));
}

/// §3.5: la cola se drena en orden. `abre` y `cierra` en el mismo tick abren y
/// liberan desde el primer paso del ataque. Un `abre` sobre un canal en
/// conmutacion espera a `Conmutado` y no antes; un `cierra` aplica en el acto.
#[test]
fn la_cola_se_aplica_en_orden_y_la_conmutacion_retiene_solo_las_aperturas() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(7, 65535), cierra(7)]);
    assert_eq!(g.etapa(7), Etapa::Relajacion, "abre y cierra en orden: libera desde el primer paso");
    assert!(g.tick(&[]).vca[7][0] < 200, "apenas alcanzo a sonar");

    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(2, 65535)]);
    g.bloquear_apertura(0b0110);
    g.tick(&[abre(1, 65535), cierra(2)]);
    assert_eq!(g.etapa(1), Etapa::Ocioso, "el abre sobre un canal en conmutacion espera");
    assert_eq!(g.etapa(2), Etapa::Relajacion, "el cierra aplica en el acto");
    ticks(&mut g, 5);
    assert_eq!(g.etapa(1), Etapa::Ocioso);
    g.tick(&[Entrada::Conmutado]);
    assert_eq!(g.etapa(1), Etapa::Ataque, "al latchear, el abre diferido aplica");
    // fuera de la conmutacion los demas canales no esperan
    g.bloquear_apertura(0b0110);
    g.tick(&[abre(9, 65535)]);
    assert_eq!(g.etapa(9), Etapa::Ataque);
    // un cierra sobre un abre diferido lo cancela: la nota nunca abrio
    g.tick(&[abre(2, 65535), cierra(2)]);
    g.tick(&[Entrada::Conmutado]);
    assert_eq!(g.etapa(2), Etapa::Ocioso, "abre diferido y cierra: no abrio");
}

/// §3.4 y voz-total §9.2: `SoltarTodo` lleva todo a relajacion y baja todas las
/// compuertas; el primer bloque valido despues reabre lo que el cerebro
/// sostiene, con la fuerza de reparacion, y resincroniza el contador.
#[test]
fn soltar_todo_libera_y_el_primer_bloque_valido_reabre_lo_que_el_cerebro_sostiene() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(0, 65535), abre(1, 65535), dispara(2, 65535)]);
    ticks(&mut g, 100);
    g.tick(&[Entrada::SoltarTodo]);
    for c in 0..3 {
        assert_eq!(g.etapa(c), Etapa::Relajacion, "canal {c}");
    }
    assert_eq!(g.compuertas(), 0);
    // un bloque con contador cualquiera (el cerebro va por 900) se adopta
    g.tick(&[Entrada::Compuerta { mascara: 0b11, contador: 900 }]);
    assert_eq!(g.eventos_recibidos(), 900);
    assert_eq!(g.etapa(0), Etapa::Ataque);
    assert_eq!(g.etapa(1), Etapa::Ataque);
    assert_eq!(g.etapa(2), Etapa::Relajacion, "el tambor no se reabre: no era compuerta");
    // y desde ahi los bloques viejos vuelven a ignorarse
    g.tick(&[Entrada::Compuerta { mascara: 0, contador: 899 }]);
    assert_eq!(g.etapa(0), Etapa::Ataque);
}

/// §5 y §4.3: la salida del filtro es el nivel de su propia envolvente, con sus
/// propios tiempos, y la del VCA son dos amplitudes con el paneo puesto.
#[test]
fn la_salida_lleva_las_dos_ramas_del_vca_y_la_envolvente_del_filtro() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(5, 65535)]);
    let s = ticks(&mut g, 50); // filtro: ataque 5 ms ya en decaimiento; VCA: en ataque
    assert_eq!(g.etapa(5), Etapa::Ataque);
    assert!(s.filtro[5] > 60000, "el filtro ya paso su pico de 5 ms: {}", s.filtro[5]);
    let (l, r) = factores_paneo(500);
    assert_eq!(s.vca[5][0], s.vca[5][1], "al centro las dos ramas son iguales");
    assert!(s.vca[5][0] > 0);
    let _ = (l, r);
    for c in 0..CANALES {
        if c != 5 {
            assert_eq!(s.vca[c], [0, 0]);
            assert_eq!(s.filtro[c], 0);
        }
    }
}
```

- [ ] **Paso 2: correr y ver el rojo**

Correr: `cargo test --test envolvente`
Esperado: FALLA en compilación (`Generadores`, `Entrada`, … no existen). Pegar.

- [ ] **Paso 3: la implementación mínima**

Añadir a `envolvente.rs` (segunda mitad), con `use crate::escritor::{amplitud,
factores_paneo, ganancia_fuerza}; use crate::fuerza::Fuerza;` arriba:

```rust
/// Papel §1: dieciseis canales.
pub const CANALES: usize = 16;
/// Papel §3.5: un acorde de dieciseis voces abriendose y cerrandose dos veces
/// dentro de un tick. La cola misma (SPSC, un productor en la ISR del J2 y un
/// consumidor en el tick) la construye el firmware con `heapless::spsc::Queue`;
/// aqui solo se declara su capacidad y lo que transporta.
pub const CAPACIDAD_COLA: usize = 64;
/// Papel §3.4, decision 12: una nota reparada por la red de R-E10 entra con
/// fuerza plena. Constante, no memoria: el modelo no publica ningun otro valor.
pub const FUERZA_REPARACION: Fuerza = Fuerza(u16::MAX);

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Borde {
    Abre,
    Cierra,
    Dispara,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Parametros {
    pub vca: Tiempos,
    pub vca_sostenido: u16,
    pub filtro: Tiempos,
    pub filtro_sostenido: u16,
    pub sensibilidad_fuerza: u16,
    pub filtro_cantidad: i16,
    pub paneo: u16,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Entrada {
    Evento { canal: u8, borde: Borde, fuerza: Fuerza },
    Parametros { canal: u8, parametros: Parametros },
    Compuerta { mascara: u16, contador: u16 },
    SoltarTodo,
    Conmutado,
}

pub struct Salida {
    pub vca: [[u16; 2]; CANALES],
    pub filtro: [u16; CANALES],
}

struct Canal {
    vca: Generador,
    filtro: Generador,
    compuerta: bool,
    g_v: f32,
    l: f32,
    r: f32,
    parametros: Parametros,
    diferido: Option<(Borde, Fuerza)>,
}

impl Canal {
    fn nuevo(parametros: Parametros) -> Self {
        let (l, r) = factores_paneo(parametros.paneo);
        Canal {
            vca: Generador::nuevo(),
            filtro: Generador::nuevo(),
            compuerta: false,
            g_v: 0.0,
            l,
            r,
            parametros,
            diferido: None,
        }
    }

    /// Papel §3.1-3.3: captura, continuidad en la amplitud, compuerta propia.
    fn aplicar(&mut self, borde: Borde, fuerza: Fuerza) {
        match borde {
            Borde::Cierra => {
                self.vca.cerrar();
                self.filtro.cerrar();
                self.compuerta = false;
            }
            Borde::Abre | Borde::Dispara => {
                let p = self.parametros;
                let g_nueva = ganancia_fuerza(fuerza, p.sensibilidad_fuerza);
                let desde = if self.vca.etapa() == Etapa::Ocioso {
                    0.0
                } else {
                    let a0 = self.vca.nivel() * self.g_v;
                    if g_nueva <= 0.0 {
                        if a0 > 0.0 { 1.0 } else { 0.0 }
                    } else {
                        (a0 / g_nueva).min(1.0)
                    }
                };
                let disparo = borde == Borde::Dispara;
                self.vca.abrir(p.vca, desde, disparo);
                let desde_f = self.filtro.nivel();
                self.filtro.abrir(p.filtro, desde_f, disparo);
                self.g_v = g_nueva;
                self.compuerta = borde == Borde::Abre;
            }
        }
    }
}

pub struct Generadores {
    canales: [Canal; CANALES],
    recibidos: u16,
    resincronizar: bool,
    en_conmutacion: u16,
}

impl Generadores {
    pub fn nuevos(parametros: Parametros) -> Self {
        Generadores {
            canales: core::array::from_fn(|_| Canal::nuevo(parametros)),
            recibidos: 0,
            resincronizar: false,
            en_conmutacion: 0,
        }
    }

    /// Un borde sobre un canal: se difiere si el canal esta en conmutacion y el
    /// borde abre (papel §6); un `cierra` aplica siempre y borra lo diferido.
    fn borde(&mut self, canal: u8, borde: Borde, fuerza: Fuerza) {
        let i = canal as usize;
        if i >= CANALES {
            return;
        }
        let c = &mut self.canales[i];
        match borde {
            Borde::Cierra => {
                c.diferido = None;
                c.aplicar(Borde::Cierra, fuerza);
            }
            _ if self.en_conmutacion & (1 << i) != 0 => c.diferido = Some((borde, fuerza)),
            _ => c.aplicar(borde, fuerza),
        }
    }

    fn aplicar_entrada(&mut self, e: Entrada) {
        match e {
            Entrada::Evento { canal, borde, fuerza } => {
                self.recibidos = self.recibidos.wrapping_add(1);
                self.borde(canal, borde, fuerza);
            }
            Entrada::Parametros { canal, parametros } => {
                if let Some(c) = self.canales.get_mut(canal as usize) {
                    c.parametros = parametros;
                    let (l, r) = factores_paneo(parametros.paneo);
                    c.l = l;
                    c.r = r;
                }
            }
            Entrada::Compuerta { mascara, contador } => {
                if self.resincronizar {
                    self.recibidos = contador;
                    self.resincronizar = false;
                } else if (contador.wrapping_sub(self.recibidos) as i16) < 0 {
                    return; // un bloque viejo no hace nada (papel §3.4)
                }
                for i in 0..CANALES {
                    let bit = mascara & (1 << i) != 0;
                    let propia = self.canales[i].compuerta;
                    if bit && !propia {
                        self.borde(i as u8, Borde::Abre, FUERZA_REPARACION);
                    } else if !bit && propia {
                        self.borde(i as u8, Borde::Cierra, Fuerza(0));
                    }
                }
            }
            Entrada::SoltarTodo => {
                for c in self.canales.iter_mut() {
                    c.diferido = None;
                    c.aplicar(Borde::Cierra, Fuerza(0));
                }
                self.resincronizar = true;
            }
            Entrada::Conmutado => {
                self.en_conmutacion = 0;
                for c in self.canales.iter_mut() {
                    if let Some((borde, fuerza)) = c.diferido.take() {
                        c.aplicar(borde, fuerza);
                    }
                }
            }
        }
    }

    /// Papel §3.5: drena en orden, avanza, escribe. El unico dueño del estado.
    pub fn tick(&mut self, entradas: &[Entrada]) -> Salida {
        for e in entradas {
            self.aplicar_entrada(*e);
        }
        let mut salida = Salida {
            vca: [[0; 2]; CANALES],
            filtro: [0; CANALES],
        };
        for (i, c) in self.canales.iter_mut().enumerate() {
            let y = c.vca.tick(c.parametros.vca_sostenido);
            let y_f = c.filtro.tick(c.parametros.filtro_sostenido);
            salida.vca[i] = [amplitud(y, c.g_v, c.l), amplitud(y, c.g_v, c.r)];
            salida.filtro[i] = libm::roundf(y_f.clamp(0.0, 1.0) * 65535.0) as u16;
        }
        salida
    }

    pub fn en_silencio(&self) -> u16 {
        let mut m = 0u16;
        for (i, c) in self.canales.iter().enumerate() {
            if c.vca.etapa() == Etapa::Ocioso {
                m |= 1 << i;
            }
        }
        m
    }

    pub fn bloquear_apertura(&mut self, cambian: u16) {
        self.en_conmutacion |= cambian;
    }

    pub fn compuertas(&self) -> u16 {
        let mut m = 0u16;
        for (i, c) in self.canales.iter().enumerate() {
            if c.compuerta {
                m |= 1 << i;
            }
        }
        m
    }

    pub fn etapa(&self, canal: u8) -> Etapa {
        self.canales.get(canal as usize).map_or(Etapa::Ocioso, |c| c.vca.etapa())
    }

    pub fn eventos_recibidos(&self) -> u16 {
        self.recibidos
    }
}
```

Aviso al ejecutor sobre el test del re-disparo: `paso_maximo` en el test se calcula
con `k` del ataque **más corto del rango** (1 ms: `tau = 1/ln 3`), que es la cota
del papel §8 (*«ningún salto mayor que un paso del ataque más corto»*); los
parámetros del test tienen un ataque de 10 ms, así que la cota sobra. Si el
`min(1, a0/g_nueva)` da una amplitud un LSB **por debajo** de `antes` por el
redondeo, el test lo acepta solo si `despues >= antes`; en ese caso ajusta el
redondeo en `aplicar` (calcula `desde` con la amplitud sin redondear, que es lo
que hace el código de arriba), no el test.

- [ ] **Paso 4: correr y ver el verde**

Correr: `cargo test --test envolvente` y luego `cargo test` entero.
Esperado: 14 tests de `envolvente`, y todo lo demás como estaba (248 unitarios +
12 `bahia` + 6 `bahia_serie` + 17 `fuerza` + 1 `tono` + 5 `escritor`).

- [ ] **Paso 5: muta cada guardia**

Como en las tareas anteriores de este repo: prueba a mano al menos estas
mutaciones y anota cuál test mata cada una: (a) el fin del decaimiento un tick
antes; (b) `dispara` levantando la compuerta; (c) el bloque viejo aplicándose;
(d) el `abre` diferido aplicándose en el acto; (e) el sostenido con un filtro
(`y += 0,5·(S − y)`); (f) el re-disparo desde `y` en vez de desde la amplitud;
(g) `en_silencio` mirando la palabra en vez de la etapa. Si alguna sobrevive,
añade el test que la mate.

- [ ] **Paso 6: clippy, fmt, las siete puertas**

Correr: `cargo clippy --all-targets -- -D warnings && cargo fmt --check`, y desde
la raíz del worktree `sh .githooks/pre-push < /dev/null`. Informe con los rojos,
el API, los archivos, las mutaciones, el verde y las puertas. Sin commit.

---

### Tarea 4: `bahia.rs` — `Commit.cambian` y `forzar` no ejecutable

**Archivos:**
- Modificar: `software/nucleo/core/src/bahia.rs` (`Commit`, `PoliticaDrones::Forzar`, `Barrera::tick`)
- Modificar: `software/nucleo/core/tests/bahia.rs` (un test)

**Interfaces:**
- Produce: `Commit { pub mutear: u16, pub cambian: u16 }`. El firmware pasa
  `commit.cambian` a `Generadores::bloquear_apertura` (tarea 3) antes de shiftear.

- [ ] **Paso 1: el test, que falla**

Añadir a `software/nucleo/core/tests/bahia.rs`:

```rust
/// Papel del generador §6: la barrera decide con la mascara de un tick y el latch
/// tarda mas de un tick (512 bits a 5 MHz son 102 us). `Commit` dice que canales
/// cambian para que el firmware los bloquee hasta `Conmutado`. Es exactamente
/// `canales_que_cambian(activa, pendiente)` en el instante del commit.
#[test]
fn el_commit_dice_que_canales_cambian_para_retener_sus_aperturas() {
    let mut b = Barrera::nueva(PoliticaDrones::Diferir);
    let mut propuesta = Imagen::vacia();
    propuesta.poner(Chip::Entrada, 3, 1);
    propuesta.poner(Chip::Salida, 11, 2);
    b.proponer(propuesta, 0);
    let c = b.tick(u16::MAX, 1).expect("todo callado");
    assert_eq!(c.cambian, (1 << 3) | (1 << 11));
    assert_eq!(c.mutear, 0);
    // recargar la misma imagen: nadie cambia, nadie se retiene
    b.proponer(propuesta, 2);
    let c = b.tick(0, 3).expect("nadie cambia: commit aunque todo suene");
    assert_eq!(c.cambian, 0);
}
```

- [ ] **Paso 2: correr y ver el rojo**

Correr: `cargo test --test bahia`
Esperado: FALLA, `no field cambian on type Commit`.

- [ ] **Paso 3: la implementación mínima**

En `bahia.rs`:

```rust
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Commit {
    /// ... (doc existente)
    pub mutear: u16,
    /// Los canales cuyos cruces cambian con este commit. El latch tarda mas de
    /// un tick (512 bits a 5 MHz son 102 us, hoja del AD75019) y un `abre` en
    /// esa ventana abriria un canal a medio conmutar: el firmware los pasa a
    /// `Generadores::bloquear_apertura` antes de shiftear y los suelta con
    /// `Entrada::Conmutado` tras `PCLK` (papel del generador §6).
    pub cambian: u16,
}
```

En `Barrera::tick`, calcular `let cambian = self.activa.canales_que_cambian(&pendiente);`
antes de `estorban` (que es `cambian & !canales_en_silencio`) y devolver
`Some(Commit { mutear: estorban, cambian })`.

Y en el doc de `PoliticaDrones::Forzar`, añadir: *«**No ejecutable en v1**: el mute
breve (`Commit::mutear`) no tiene número hasta que el bring-up mida el glitch del
AD75019 (voz-total §11.2). Un preset solo puede declarar `Diferir` hasta entonces
(papel del generador §6).»*

- [ ] **Paso 4: correr y ver el verde**

Correr: `cargo test --test bahia` — 13 tests, `ok`. Los 12 existentes no se tocan.

---

### Tarea 5: `ataque_budget.py` — el presupuesto nota → VCA, con sus huecos

**Archivos:**
- Crear: `hardware/03-vco/ataque_budget.py`

**Interfaces:**
- Lo recoge `hardware/tools/gates.py` por el glob `hardware/**/*_budget.py`; el
  código de salida **2 es HUECO** (aceptado por la puerta), 0 es OK, 1 es rojo.
- Filas y fuentes: papel §9 (tabla), evento §5, voz-total §3.3 (≤ 3 ms).

- [ ] **Paso 1: el guion, con su aserción y sus huecos**

```python
"""El camino de la nota al VCA, contra los 3 ms de voz-total S3.3.

    python ataque_budget.py

Lo manda el papel del evento (S5: "no existe") y lo llena el del generador de
envolvente (S9). Asevera lo CONOCIDO y declara HUECO lo que no se puede derivar
de ningun papel ni hoja (R-F1/R-J6): un presupuesto que rellenara los huecos con
supuestos daria un total y no diria nada.

--- Codigos de salida (convencion del repo, gates.py) ------------------------

  0  VERDE: no queda ningun hueco y la suma cabe.
  2  HUECO: lo conocido cabe con margen, pero faltan terminos por medir.
  1  ROJO: lo conocido ya no cabe.
"""
from __future__ import annotations

import sys

OBJETIVO_US = 3_000.0          # voz-total S3.3: <= 3 ms de nota a VCA
T_TICK_US = 100.0              # generador S1: F_RENDER = 10 kHz
T_ATAQUE_MIN_MS = 1.0          # generador S7: el ataque mas corto del rango
RC_MAX_US = T_ATAQUE_MIN_MS * 1000.0 / 10.0   # generador S9: un decimo del ataque minimo

# (termino, microsegundos o None si es HUECO, fuente)
FILAS = [
    ("reaccion del cerebro", None,
     "evento S5: depende de en que nucleo viva el host USB (C2)"),
    ("turno del J2", 100.0,
     "R-E1: ningun mensaje dura mas de 100 us (la cota viva; la cifra vieja del bus compartido no)"),
    ("parse del evento y encolado en el N657", None,
     "bring-up: ISR del esclavo SPI bajo carga plena (motor-digital S7)"),
    ("latencia de la ISR del tick", None,
     "bring-up: el tick en el escalon del DMA de audio/CV, debajo de capturas y J2"),
    ("primer tick del generador", T_TICK_US,
     "generador S3.5: el evento se drena al principio del tick siguiente"),
    ("latencia de bloque del DMA de CV lento", None,
     "motor-digital S5 no declara el tamano de bloque"),
    ("escritura y asentamiento del DAC", None,
     "hoja del DAC que R-M3 nombre"),
    ("RC de reconstruccion", RC_MAX_US,
     "generador S9: RC <= un decimo del ataque minimo"),
]


def main() -> int:
    conocido = sum(v for _, v, _ in FILAS if v is not None)
    huecos = [n for n, v, _ in FILAS if v is None]
    print(f"nota -> VCA contra {OBJETIVO_US:.0f} us (voz-total S3.3)\n")
    for nombre, valor, fuente in FILAS:
        cifra = f"{valor:7.1f} us" if valor is not None else "   HUECO  "
        print(f"  {nombre:42s} {cifra}   {fuente}")
    print(f"\n  conocido: {conocido:.0f} us de {OBJETIVO_US:.0f} "
          f"({conocido / OBJETIVO_US:.0%}); {len(huecos)} huecos se reparten "
          f"{OBJETIVO_US - conocido:.0f} us")
    assert conocido < OBJETIVO_US, (
        f"lo conocido ({conocido:.0f} us) ya no cabe en {OBJETIVO_US:.0f}")
    # la RC y el tick son cotas de diseno, no medidas: si alguien las mueve, aqui grita
    assert RC_MAX_US <= T_TICK_US, "la RC no puede ser mas lenta que un tick"
    if huecos:
        print("\nHUECO: faltan " + ", ".join(huecos) + ". Se miden en bring-up.")
        return 2
    print("\nOK: presupuesto cerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Paso 2: correrlo**

Correr: `python hardware/03-vco/ataque_budget.py; echo exit=$?`
Esperado: imprime la tabla, `exit=2` (cinco huecos). Y `python hardware/tools/gates.py`
(o la función `g_hardware` del hook) lo recoge y lo acepta como HUECO. Verificar que
`ruff check .` desde la raíz no se queja (la puerta de lint mira todo el repo).

- [ ] **Paso 3: la mutación**

Cambiar `OBJETIVO_US` a 250 y comprobar que sale 1 (rojo) por el `assert`; volver
a dejarlo. Anotarlo en el informe.

---

### Tarea 6: `check_censo_voz.py` — la fila de los 160

**Archivos:**
- Modificar: `hardware/03-vco/check_censo_voz.py` (constantes del censo, `params()`, la impresión)

- [ ] **Paso 1: leer el guion entero** y localizar `POR_CANAL`, `PANEO_POR_CANAL`,
  `params()` y la impresión de las filas (líneas ~103-150), y las aserciones contra
  `MAX_PARAMS` y la reserva.

- [ ] **Paso 2: añadir la fila**

Junto a `PANEO_POR_CANAL`:

```python
ENVOLVENTE_POR_CANAL = 10   # generador de envolvente S7: dos ADSR (3 tiempos + sostenido)
                            # + sensibilidad a la fuerza + cantidad del filtro, POR VOZ.
                            # OJO: los "+9/canal" de voz-total S7 no estan desglosados
                            # en ningun papel; si ya contenian perillas de ADSR, esta
                            # fila duplica (riesgo 3 del papel; se sabe con el cambio 15).
```

En `params()`, sumar `ENVOLVENTE_POR_CANAL * CANALES` siempre (no depende del
estéreo). En la impresión, una fila `+ envolvente, 10 por canal (generador S7)  160`.

- [ ] **Paso 3: correrlo y leer lo que dice**

Correr: `python hardware/03-vco/check_censo_voz.py; echo exit=$?`
Esperado: 696 parámetros (952 con la reserva de 256), memoria al ~59 %, y el guion
**sigue en el mismo código de salida que antes** (2, por los inquilinos sin censar,
o 0 si hoy da 0: anotar cuál). Si alguna aserción salta (techo de `MAX_PARAMS` con
reserva, margen del 30 %), **no ablandarla**: pegar el rojo en el informe, que es
exactamente lo que el papel dijo que podía pasar (riesgo 3).

- [ ] **Paso 4: la puerta entera**

Desde la raíz del worktree: `sh .githooks/pre-push < /dev/null`. Informe con lo
que imprimió el censo antes y después, y las siete puertas. Sin commit.

---

### Tarea 7: las enmiendas del papel §14 (la hace quien coordina)

**Archivos:**
- Modificar: `docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md` §3.2
- Modificar: `docs/superpowers/specs/2026-08-26-motor-digital-design.md` §5 y §7
- Modificar: `docs/superpowers/specs/2026-08-25-evento-de-nota-design.md` D6, D7

Cada una es un bloque de cita (`> **Enmienda del 2026-09-02** …`) con el texto que
§14 del papel del generador manda, y el estado de la fila de §14 pasa a
«aplicada» en el mismo PR.

---

## Autorrevisión del plan

**Cobertura del papel:** §1 (dos objetos) → tareas 1 y 3; §2 (etapas por cuenta,
RC truncada, RT60, sostenido vivo) → tarea 2; §3.1-3.3 (bordes, re-disparo en la
amplitud, captura) → tareas 2 y 3; §3.4 (tres fuentes, compuerta propia, `dispara`
irreparable, `FUERZA_REPARACION`, contador) → tarea 3; §3.5 (dueño único, cola) →
tarea 3 (la cola SPSC misma es del firmware, declarado); §4 (fuerza, paneo,
amplitud, `ley_vca` HUECO) → tarea 1; §5 (polo, octavas) → tarea 1; §6 (silencio,
`cambian`, `forzar` no ejecutable) → tareas 3 y 4; §7 (parámetros, censo) → tareas
3 y 6; §8 (los 14 tests) → 1, 2, 3 (el 14, «costo», se declara no probable); §9
(`ataque_budget`, censo, NVIC) → tareas 5, 6, 7; §14 → tarea 7.

**Lo que el plan NO hace, a propósito:** el firmware del N657 (#250), la cola SPSC
en `fw`, los descriptores de los 10 parámetros (el modelo de la Voz total no es
direccionable hasta los cambios 2 y 12; el tipo de placa de la Voz total no está
en el catálogo), `ley_vca` (sin hoja), el escritor de corte entero (solo su
contrato), la cabecera del J2 (#267).

**Consistencia de tipos:** `Tiempos`, `Etapa`, `Generador::{nuevo, etapa, nivel,
abrir, cerrar, tick}` (tarea 2) se usan con esas firmas en la tarea 3;
`escritor::{ganancia_fuerza, factores_paneo, amplitud}` (tarea 1) con esas firmas
en la tarea 3; `Commit.cambian` (tarea 4) es lo que el firmware pasa a
`Generadores::bloquear_apertura(u16)` (tarea 3).
