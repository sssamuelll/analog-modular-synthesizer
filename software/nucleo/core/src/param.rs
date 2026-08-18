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
