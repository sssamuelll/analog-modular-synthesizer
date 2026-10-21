//! Un contador de 32 bits que da la vuelta, visto como uno de 64.
//!
//! El soak del J2 a 8 kHz cuenta giros en un `u32` (`maestro_j2::giros`): da la vuelta a las
//! 149 h (2^32 / 8000 / 3600), y la corrida de una ranura dura 144 h. Quien publica la fila
//! suma aqui la diferencia desde la ultima lectura, y mientras se lea mas de una vez por
//! vuelta el total no se pierde.

/// El total de 64 bits de un contador de 32 que solo sube y da la vuelta.
#[derive(Clone, Copy, Debug, Default)]
pub struct CuentaLarga {
    ultimo: u32,
    total: u64,
}

impl CuentaLarga {
    pub const fn nueva() -> Self {
        Self {
            ultimo: 0,
            total: 0,
        }
    }

    /// Anota la lectura `actual` del contador de 32 bits y devuelve el total acumulado.
    ///
    /// Vale mientras entre dos lecturas el contador no de mas de una vuelta; la fila sale cada
    /// hora y la vuelta tarda 149.
    pub fn anota(&mut self, actual: u32) -> u64 {
        self.total += u64::from(actual.wrapping_sub(self.ultimo));
        self.ultimo = actual;
        self.total
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sin_vuelta_el_total_es_la_lectura() {
        let mut c = CuentaLarga::nueva();
        assert_eq!(c.anota(28_800_000), 28_800_000);
        assert_eq!(c.anota(57_600_000), 57_600_000);
    }

    #[test]
    fn la_vuelta_no_se_pierde() {
        let mut c = CuentaLarga::nueva();
        c.anota(u32::MAX - 10);
        // Quince giros despues el contador de 32 bits marca 4.
        assert_eq!(c.anota(4), u64::from(u32::MAX) - 10 + 15);
    }

    #[test]
    fn seis_dias_a_8_khz_pasan_de_los_32_bits() {
        let mut c = CuentaLarga::nueva();
        let por_hora: u64 = 8_000 * 3_600;
        let mut real: u64 = 0;
        for _ in 0..150 {
            real += por_hora;
            // Lo que publicaria el u32 de la firmware: el real, truncado.
            assert_eq!(c.anota(real as u32), real);
        }
        assert!(real > u64::from(u32::MAX));
    }

    #[test]
    fn la_primera_lectura_cuenta_desde_cero() {
        // El contador de la firmware nace en cero: la primera fila ya trae giros.
        let mut c = CuentaLarga::nueva();
        assert_eq!(c.anota(7), 7);
    }
}
