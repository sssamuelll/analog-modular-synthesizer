//! El presupuesto de escaladas del GPDMA1 (papel v3, §2.5, candidata K1): puro.
//!
//! Es del controlador, no de la ranura: lo lleva la recuperacion, que es el unico escritor que
//! escala, y concede como mucho `E` escaladas en una ventana deslizante contada en el reloj del
//! tic (los periodos de `RelojDelTic` pasados a us). Con el presupuesto gastado la recuperacion
//! hace el `RESET` por canal, no publica `HECHA` y no reintenta: la ranura muere por la cota de
//! `Reiniciando` y el supervisor reinicia el chip. Es una sentencia de reinicio deliberada: un
//! controlador que no para tras `E` resets en la ventana no tiene otra cura. `E` y la ventana son
//! ESTIMADOS.

/// El mayor `E` que cabe.
pub const E_MAX: usize = 8;

#[derive(Clone, Copy, Debug)]
pub struct Presupuesto {
    e: usize,
    ventana_us: u64,
    /// Los instantes de las ultimas `e` concesiones, en anillo.
    concesiones: [u64; E_MAX],
    concedidas: u32,
    denegadas: u32,
}

impl Presupuesto {
    /// `e` escaladas como mucho en cualquier ventana de `ventana_us`.
    pub const fn nuevo(e: usize, ventana_us: u64) -> Presupuesto {
        assert!(e <= E_MAX);
        Presupuesto {
            e,
            ventana_us,
            concesiones: [0; E_MAX],
            concedidas: 0,
            denegadas: 0,
        }
    }

    /// Pide una escalada en `ahora_us`. `true` si se concede, y entonces se gasta.
    pub fn pide(&mut self, ahora_us: u64) -> bool {
        let n = self.concedidas as usize;
        // La casilla del anillo guarda la `e`-esima concesion mas reciente: la que sale primero
        // de la ventana.
        let cabe = self.e > 0
            && (n < self.e
                || ahora_us.saturating_sub(self.concesiones[n % self.e]) >= self.ventana_us);
        if cabe {
            self.concesiones[n % self.e] = ahora_us;
            self.concedidas += 1;
        } else {
            self.denegadas += 1;
        }
        cabe
    }

    pub const fn concedidas(&self) -> u32 {
        self.concedidas
    }

    pub const fn denegadas(&self) -> u32 {
        self.denegadas
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const MS: u64 = 1000;

    #[test]
    fn concede_e_en_la_ventana_y_niega_la_siguiente() {
        let mut p = Presupuesto::nuevo(3, 1000 * MS);
        assert!(p.pide(0));
        assert!(p.pide(10 * MS));
        assert!(p.pide(20 * MS));
        assert!(!p.pide(30 * MS));
        assert!(!p.pide(999 * MS));
        assert_eq!((p.concedidas(), p.denegadas()), (3, 2));
    }

    #[test]
    fn la_ventana_desliza_y_una_negada_no_gasta() {
        let mut p = Presupuesto::nuevo(3, 1000 * MS);
        for t in [0, 10, 20] {
            assert!(p.pide(t * MS));
        }
        assert!(!p.pide(30 * MS));
        // La de 0 sale de la ventana a los 1000 ms: cabe una, y no dos.
        assert!(p.pide(1000 * MS));
        assert!(!p.pide(1005 * MS));
        // La de 10 sale a los 1010, la de 20 a los 1020.
        assert!(p.pide(1010 * MS));
        assert!(p.pide(1020 * MS));
        assert!(!p.pide(1021 * MS));
    }

    #[test]
    fn la_frontera_de_la_ventana_es_abierta_por_detras() {
        let mut p = Presupuesto::nuevo(1, 100);
        assert!(p.pide(0));
        assert!(!p.pide(99));
        assert!(p.pide(100));
    }

    #[test]
    fn con_e_cero_nunca_concede() {
        let mut p = Presupuesto::nuevo(0, 100);
        for t in [0, 1_000, 1_000_000] {
            assert!(!p.pide(t));
        }
    }

    #[test]
    fn con_e_maximo_concede_e_seguidas() {
        let mut p = Presupuesto::nuevo(E_MAX, 1000);
        for k in 0..E_MAX as u64 {
            assert!(p.pide(k), "la {k}");
        }
        assert!(!p.pide(E_MAX as u64));
        assert!(p.pide(1000));
    }
}
