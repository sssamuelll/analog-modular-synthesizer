//! El contrato de la fuerza — la velocity que el instrumento no tenia.
//!
//! Aterriza en el modelo antes que en el mensaje por el invariante del nucleo
//! §2.1 (*«si no esta en el modelo, no existe»*), que es lo que manda la
//! condicion C10 del papel del evento
//! (`docs/superpowers/specs/2026-08-25-evento-de-nota-design.md`).
//!
//! **El ancho es 16 bits y es derivado, no elegido.** Toda la cadena ya lo es:
//! el DAC que fabrica `CV_VEL_n` (candidatos AD5686R y LTC2668-16, los dos de
//! 16 bits), el campo hermano del propio evento (*«Tono de arranque, el mismo
//! ancho que un valor del bloque de tono»*, evento §3) y el UMP de MIDI 2.0.
//! El unico eslabon de 7 bits es MIDI 1.0.
//!
//! **La conversion de 7 a 16 bits NO es un desplazamiento.** MIDI 2.0 la
//! define como *Min-Center-Max Scaling* en
//! `M2-115-U MIDI 2.0 Bit Scaling and Resolution v1.0.2 (2023-12-18)`, y su
//! §3.1 lista *«Note On/Off Velocity»* entre los valores que la usan. El
//! algoritmo verbatim esta en su §3.3.1. Estos tests fijan las tres reglas de
//! su §3.2 mas la monotonia, que es lo que se oye.

use sam17_nucleo_core::fuerza::Fuerza;
use sam17_nucleo_core::partes::{Parte, Repartidor};

/// §3.2, regla 1: *«Minimum/Lowest value is scaled to Minimum/Lowest»*.
#[test]
fn el_minimo_se_conserva() {
    assert_eq!(Fuerza::desde_midi1(0), Fuerza(0));
}

/// §3.2, regla 3 y Tabla 4: el centro de 7 bits (0x40) va al centro de 16
/// (0x8000). Es lo que mantiene "medio fuerte" en el mismo sitio al subir de
/// resolucion.
#[test]
fn el_centro_se_conserva() {
    assert_eq!(Fuerza::desde_midi1(0x40), Fuerza(0x8000));
}

/// §3.2, regla 2: *«a 7-bit value of 127 is translated to a 16-bit value of
/// 65535»*.
///
/// **Este es el test que caza el atajo.** Con el desplazamiento ingenuo
/// (`v << 9`) el 127 da 0xFE00 = 65024: el golpe mas fuerte del teclado nunca
/// alcanza el fondo de escala y el instrumento suena con el techo cortado.
#[test]
fn el_maximo_llega_al_fondo_de_escala_y_no_al_atajo() {
    let f = Fuerza::desde_midi1(127);
    assert_ne!(
        f,
        Fuerza(0xFE00),
        "0xFE00 es `127 << 9`: el desplazamiento ingenuo, prohibido por M2-115-U §3.2"
    );
    assert_eq!(f, Fuerza(0xFFFF));
}

/// Lo que de verdad se oye: mas fuerte en MIDI nunca puede sonar igual o mas
/// flojo. Una tabla no monotona produce escalones audibles en un crescendo.
#[test]
fn mas_fuerte_entra_siempre_mas_fuerte() {
    for v in 0u8..127 {
        let a = Fuerza::desde_midi1(v).0;
        let b = Fuerza::desde_midi1(v + 1).0;
        assert!(a < b, "{v} dio {a} y {} dio {b}: no crece", v + 1);
    }
}

/// §3.2, regla 4: *«Scaling down a previously upscaled value yields the
/// original value»*. Sin esto el instrumento no puede hablarle de vuelta a un
/// host de MIDI 1.0 sin desafinar la dinamica.
#[test]
fn bajar_de_nuevo_a_siete_bits_devuelve_el_original() {
    for v in 0u8..=127 {
        assert_eq!(
            Fuerza::desde_midi1(v).0 >> 9,
            v as u16,
            "no cierra el viaje de ida y vuelta en {v}"
        );
    }
}

/// Frontera de confianza: el byte llega de fuera. MIDI 1.0 solo define 7 bits,
/// asi que el octavo no puede colarse ni hacer entrar al escalado por una rama
/// que su precondicion no cubre.
#[test]
fn el_octavo_bit_de_un_byte_ajeno_no_se_cuela() {
    // Barrido entero, no dos casos sueltos. Probar solo 0xFF y 0x80 NO sirve:
    // los dos coinciden con su version enmascarada por accidente del truncado
    // a u16, y dejan pasar una implementacion sin mascara. Medido con una
    // mutacion: quitar el `& 0x7F` dejaba los once tests en verde.
    //
    // Quien lo caza es 0xA0. Enmascarado es 32, que es <= centro y sale por el
    // desplazamiento simple: 0x4000. Sin enmascarar es 160, que es > centro,
    // entra por el esquema de repeticion y da 0x4104.
    for v in 0u8..=127 {
        assert_eq!(
            Fuerza::desde_midi1(v | 0x80),
            Fuerza::desde_midi1(v),
            "el octavo bit cambio el resultado en {v}"
        );
    }
}

fn una_parte() -> [Parte; 1] {
    [Parte {
        canal: 0,
        nota_min: 0,
        nota_max: 127,
        voces: 2,
        primera_voz: 0,
        preset: 0,
    }]
}

/// C10: la fuerza tiene que salir del reparto, no quedarse en la puerta.
#[test]
fn la_asignacion_lleva_la_fuerza_con_la_que_se_toco() {
    let partes = una_parte();
    let mut r = Repartidor::nueva(2);
    let a = r.nota_on(&partes, 0, 60, Fuerza::desde_midi1(100)).unwrap();
    assert_eq!(a.fuerza, Fuerza::desde_midi1(100));
}

/// §2.1: si no esta en el modelo, no existe. La voz que suena tiene que poder
/// decir con que fuerza suena — es lo que el evento y el VCA leen.
#[test]
fn la_voz_recuerda_con_que_fuerza_esta_sonando() {
    let partes = una_parte();
    let mut r = Repartidor::nueva(2);
    let a = r.nota_on(&partes, 0, 60, Fuerza::desde_midi1(90)).unwrap();
    assert_eq!(r.fuerza(a.voz), Some(Fuerza::desde_midi1(90)));
}

/// Dos voces, dos fuerzas distintas, a la vez. Si el modelo guardara una sola,
/// este test lo dice: es la diferencia entre un acorde con dinamica y un
/// acorde plano.
#[test]
fn dos_voces_sostienen_fuerzas_distintas_a_la_vez() {
    let partes = una_parte();
    let mut r = Repartidor::nueva(2);
    let a = r.nota_on(&partes, 0, 60, Fuerza::desde_midi1(20)).unwrap();
    let b = r.nota_on(&partes, 0, 64, Fuerza::desde_midi1(120)).unwrap();
    assert_ne!(a.voz, b.voz);
    assert_eq!(r.fuerza(a.voz), Some(Fuerza::desde_midi1(20)));
    assert_eq!(r.fuerza(b.voz), Some(Fuerza::desde_midi1(120)));
}

/// La velocity de suelta: el otro flanco. Es lo que hace que un Rhodes suelte
/// como un Rhodes. Va ahora y no despues porque R-E10 avisa que un campo
/// añadido mas tarde **nace sin reparacion**.
#[test]
fn la_suelta_registra_su_propia_fuerza() {
    let partes = una_parte();
    let mut r = Repartidor::nueva(2);
    let a = r.nota_on(&partes, 0, 60, Fuerza::desde_midi1(100)).unwrap();
    let voz = r.nota_off(0, 60, Fuerza::desde_midi1(30)).unwrap();
    assert_eq!(voz, a.voz);
    assert_eq!(
        r.fuerza(voz),
        Some(Fuerza::desde_midi1(30)),
        "tras soltar, la voz guarda la fuerza de SUELTA, no la de ataque"
    );
}

/// Robar una voz tiene que traer la fuerza nueva, no dejar la del difunto.
#[test]
fn al_robar_la_voz_manda_la_fuerza_de_la_nota_nueva() {
    let partes = una_parte();
    let mut r = Repartidor::nueva(1);
    r.nota_on(&partes, 0, 60, Fuerza::desde_midi1(10)).unwrap();
    let b = r.nota_on(&partes, 0, 67, Fuerza::desde_midi1(127)).unwrap();
    assert_eq!(b.robada, Some(60));
    assert_eq!(r.fuerza(b.voz), Some(Fuerza(0xFFFF)));
}
