//! Los escritores del modulo de Voz (papel §1): lo que convierte niveles de los
//! generadores en palabras de DAC, consumiendo parametros VIVOS del modelo.
//! Un escritor no es un generador: no se dispara y no tiene etapas. Por S-9
//! (voz-total §2) el micro es el unico escritor de sus CV.
//!
//! Papel: `docs/superpowers/specs/2026-09-02-generador-de-envolvente-design.md`,
//! §4 (el escritor del VCA) y §5 (el contrato del escritor de corte).
//!
//! **Decision 15:** aqui la salida del VCA es AMPLITUD lineal en 16 bits. La
//! ley del SSI2164 ya esta en el arbol (`docs/reference/datasheets/
//! ssi2164-rev3.4-2023-02.pdf`, p. 4 «Control Port»): control exponencial
//! referido a masa, -33 mV por dB, ganancia unidad a 0 V y -100 dB a +3,3 V;
//! o sea `V_C(a) = -0,66 V * log10(a)`. **HUECO que queda:** la escala y el
//! desplazamiento del DAC al puerto (esquematico, con el DAC que R-M3 nombre)
//! y si el puerto se compensa en temperatura (la constante es PTAT, 0,33 %/C;
//! la Figura 2 de la hoja da un puerto compensado a -50 mV/dB). `ley_vca` se
//! escribe aqui cuando eso exista, con la regla de que `ley_vca(0)` cierra el
//! VCA (voz-total §9.1): como mas voltaje es menos ganancia, la palabra cero
//! del DAC no puede ir directa al puerto.

use crate::fuerza::Fuerza;

/// Papel §5: el polo de un tick del escritor de corte, a 48 kHz. Un tick de
/// 10 kHz son 4,8 muestras: `K48 = 1 - e^(-1/4,8) = 0,1880636`. Causal y sin
/// mirar el tick siguiente; el gemelo digital de la RC del DAC del VCA.
///
/// El papel imprime «0,18807» y el plan de implementacion «0,18806997»; las dos
/// son la misma cifra mal redondeada. Manda la formula, que es la que el papel
/// define y la que el test compara contra `libm::expf`.
pub const K48: f32 = 0.188_063_65;

/// Papel §4.1: `g_v = (1 - s) + s * v`. Lineal a proposito: la curva ya la puso
/// MIDI 2.0 al escalar los 7 bits (`fuerza.rs`).
pub fn ganancia_fuerza(fuerza: Fuerza, sensibilidad_milesimas: u16) -> f32 {
    let s = sensibilidad_milesimas.min(1000) as f32 / 1000.0;
    let v = fuerza.0 as f32 / 65535.0;
    (1.0 - s) + s * v
}

/// Papel §4.2: potencia constante. `p = paneo / 1000`; `L = cos(p * pi/2)`,
/// `R = sin(p * pi/2)`; el centro queda a -3 dB en cada rama.
///
/// El `max(0)` no es cosmetico: `cosf(pi/2)` en `f32` da -4,4e-8, y un factor
/// NEGATIVO en una rama del VCA es una inversion de fase, no un silencio. El
/// papel dice amplitud en [0, 1] (§4.3), asi que la rama muda vale cero.
pub fn factores_paneo(paneo_milesimas: u16) -> (f32, f32) {
    let p = paneo_milesimas.min(1000) as f32 / 1000.0;
    let angulo = p * core::f32::consts::FRAC_PI_2;
    (libm::cosf(angulo).max(0.0), libm::sinf(angulo).max(0.0))
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
