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
            assert!(
                (g - esperado).abs() < 1e-6,
                "s={s} v={v}: {g} vs {esperado}"
            );
        }
        assert!(
            (ganancia_fuerza(Fuerza(65535), s) - 1.0).abs() < 1e-6,
            "fuerza plena da 1"
        );
    }
    assert_eq!(
        ganancia_fuerza(Fuerza(0), 1000),
        0.0,
        "s = 1 y v = 0: no suena"
    );
    assert_eq!(
        ganancia_fuerza(Fuerza(0), 0),
        1.0,
        "s = 0: la fuerza no hace nada"
    );
}

/// §4.2: potencia constante, L² + R² = 1 en todo el recorrido; p = 500 da −3 dB
/// en cada rama; 0 es izquierda dura y 1000 derecha dura.
#[test]
fn el_paneo_es_a_potencia_constante_en_todo_el_recorrido() {
    for p in (0..=1000u16).step_by(25) {
        let (l, r) = factores_paneo(p);
        assert!(
            (l * l + r * r - 1.0).abs() < 1e-5,
            "p={p}: L²+R² = {}",
            l * l + r * r
        );
        assert!(l >= 0.0 && r >= 0.0);
    }
    let (l, r) = factores_paneo(500);
    let menos_3_db = 10f32.powf(-3.0 / 20.0);
    assert!(
        (l - menos_3_db).abs() < 2e-3 && (r - menos_3_db).abs() < 2e-3,
        "centro a −3 dB"
    );
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
        assert!(
            (z - esperado).abs() < 1e-4,
            "muestra {n}: {z} vs {esperado}"
        );
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
        assert!(
            (corte_hz(440.0, c, 0.0) - 440.0).abs() < 1e-3,
            "y_f = 0 no mueve, c={c}"
        );
    }
    // a mitad de envolvente, media cantidad: 1200 cents con y_f = 0,5 es medio octava
    assert!((corte_hz(440.0, 1200, 0.5) - 440.0 * libm::sqrtf(2.0)).abs() < 1e-2);
}
