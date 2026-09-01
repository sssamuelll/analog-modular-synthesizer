//! El tono de arranque que sale con la asignacion de una voz.

use sam17_nucleo_core::fuerza::Fuerza;
use sam17_nucleo_core::partes::{Parte, Repartidor};

/// `M2-115-U MIDI 2.0 Bit Scaling and Resolution v1.0.2`, seccion 4,
/// pagina 17, lineas 432-436: `Pitch 7.9 127.0 (0xFE00)`; aplicar
/// Min-Center-Max lo convierte en 127.00385, aproximadamente 1/3 de cent.
/// La Tabla 9, pagina 18, linea 476, da el par exacto 127 -> 65024 (0xFE00).
#[test]
fn el_tono_de_arranque_extiende_con_ceros_todo_el_rango_midi1() {
    let partes = [Parte {
        canal: 0,
        nota_min: 0,
        nota_max: 127,
        voces: 1,
        primera_voz: 0,
        preset: 0,
    }];
    let mut repartidor = Repartidor::nueva(1);

    let maximo = repartidor
        .nota_on(&partes, 0, 127, Fuerza::desde_midi1(100))
        .unwrap();
    assert_eq!(maximo.tono, 65_024);

    // El barrido NO repite la formula: si la comprobacion fuera
    // `tono == nota << 9`, cambiar la implementacion a `<< 8` la dejaria
    // pasando igual. Se comprueban las propiedades que DEFINEN la extension
    // con ceros de UQ7.9, que un desplazamiento equivocado rompe.
    let mut anterior: Option<u16> = None;
    for nota in 0u8..=127 {
        let t = repartidor
            .nota_on(&partes, 0, nota, Fuerza::desde_midi1(100))
            .unwrap()
            .tono;

        // La parte fraccionaria son los 9 bits bajos y nace en cero.
        assert_eq!(t & 0x01FF, 0, "la nota {nota} ensucia la fraccion");
        // La parte entera son los 7 bits altos y vale la nota MIDI.
        assert_eq!(t >> 9, u16::from(nota), "la nota {nota} pierde su entero");
        // Y el recorrido es estrictamente creciente, sin mesetas ni saltos.
        if let Some(previo) = anterior {
            assert_eq!(t - previo, 512, "el paso de semitono no es 512");
        }
        anterior = Some(t);
    }

    // Los dos extremos, anclados a la Tabla 9 y no a la formula.
    assert_eq!(anterior, Some(65_024));
}
