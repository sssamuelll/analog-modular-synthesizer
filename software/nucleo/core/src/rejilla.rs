//! §4. La cuantizacion global, con los valores de Ableton.
//!
//! Ojo con una trampa del vocabulario: `1/2`, `1/4`, `1/8` y `1/16` son
//! **figuras**, no fracciones del compas. En 4/4 coinciden; en 3/4 no. Una
//! negra es una negra pase lo que pase.

/// Resolucion interna. Divisible entre 3 y 4, asi que tresillos y
/// treintaidosavos caen exactos.
pub const PPQN_INTERNO: u32 = 96;

/// Cuantos pulsos internos dura un compas de `numerador/denominador`.
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
        Rejilla::Ninguna,
        Rejilla::Compases8,
        Rejilla::Compases4,
        Rejilla::Compases2,
        Rejilla::Compas1,
        Rejilla::Mitad,
        Rejilla::Cuarto,
        Rejilla::Octavo,
        Rejilla::Dieciseisavo,
    ];

    /// Las etiquetas que ve el agente. Son las de Ableton, literales (§2.1 de
    /// la spec): el agente ya conoce ese vocabulario y no conoce el nuestro.
    pub const ETIQUETAS: &'static [&'static str] = &[
        "ninguna",
        "8 compases",
        "4 compases",
        "2 compases",
        "1 compas",
        "1/2",
        "1/4",
        "1/8",
        "1/16",
    ];

    pub fn de_indice(i: i32) -> Option<Rejilla> {
        Self::TODAS.get(usize::try_from(i).ok()?).copied()
    }

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
/// sistema (§5.3 de la spec): lo que llegue a menos de eso DESPUES de un borde
/// se trata como si hubiera llegado en el borde — porque a efectos de todo lo
/// que se puede oir, llego ahi.
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

    #[test]
    fn hay_una_etiqueta_por_valor() {
        // Sin esto el agente ve un numero y no sabe que significa.
        assert_eq!(Rejilla::ETIQUETAS.len(), Rejilla::TODAS.len());
        for (i, _) in Rejilla::TODAS.iter().enumerate() {
            assert_eq!(Rejilla::de_indice(i as i32), Some(Rejilla::TODAS[i]));
        }
        assert_eq!(Rejilla::de_indice(99), None);
        assert_eq!(Rejilla::de_indice(-1), None);
    }
}
