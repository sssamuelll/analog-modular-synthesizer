//! El supervisor de vitalidad del hub para el J2 (papel v3, §2.11, R-H8, candidata K5): puro.
//!
//! Cada `P_s` mira, por ranura activa, el instante de su ultimo sello (el sello sube al armar) y
//! deja de alimentar el IWDG en cuanto uno es mas viejo que su ventana `W`; el IWDG reinicia el
//! chip `T_IWDG` despues. **Solo lee el sello**: nunca `inestable` ni `muda`, que son de partes y
//! voces, y como disparo harian que desenchufar un modulo reinicie el instrumento (H-6).
//!
//! Activa es con identidad. Una ranura que recibe un modulo cuenta desde ese instante: si esta
//! `Muerta` no sella nunca y, pasada la ventana, el supervisor reinicia el chip, que es la unica
//! cura de `Muerta` (papel v3, §2.10). Una vez que deja de alimentar no vuelve a hacerlo: la
//! ventana es mayor que el mayor hueco de sello del diseno, y pasarla es una averia, no un
//! retraso. El supervisor es del hub (#291); `fw` no lo usa todavia.

/// Lo que el supervisor ve de una ranura.
#[derive(Clone, Copy, Default, PartialEq, Eq, Debug)]
pub struct Vista {
    pub identidad: bool,
    /// El instante del ultimo sello, en us del reloj del supervisor.
    pub ultimo_sello_us: u64,
}

#[derive(Clone, Copy, Debug)]
pub struct Supervisor<const N: usize> {
    ventana_us: u64,
    /// Desde cuando ve el supervisor a cada ranura con identidad.
    desde: [Option<u64>; N],
    /// La ranura que hizo dejar de alimentar.
    causa: Option<usize>,
}

impl<const N: usize> Supervisor<N> {
    /// `ventana_us` es `W`: mayor que el mayor hueco de sello del diseno (ESTIMADO).
    pub const fn nuevo(ventana_us: u64) -> Supervisor<N> {
        Supervisor {
            ventana_us,
            desde: [None; N],
            causa: None,
        }
    }

    /// Una mirada. `true` si alimenta el IWDG.
    pub fn mira(&mut self, ahora_us: u64, ranuras: &[Vista; N]) -> bool {
        for (n, v) in ranuras.iter().enumerate() {
            if !v.identidad {
                self.desde[n] = None;
                continue;
            }
            // Cuenta desde su ultimo sello, o desde que tiene modulo si es mas reciente.
            let desde = *self.desde[n].get_or_insert(ahora_us);
            let referencia = desde.max(v.ultimo_sello_us);
            if self.causa.is_none() && ahora_us.saturating_sub(referencia) > self.ventana_us {
                self.causa = Some(n);
            }
        }
        self.causa.is_none()
    }

    /// La ranura que hizo dejar de alimentar, si alguna.
    pub const fn causa(&self) -> Option<usize> {
        self.causa
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const W: u64 = 55_000;
    const P_S: u64 = 5_000;

    fn activas(sello: u64) -> [Vista; 6] {
        [Vista {
            identidad: true,
            ultimo_sello_us: sello,
        }; 6]
    }

    #[test]
    fn alimenta_mientras_las_ranuras_activas_sellan() {
        let mut s = Supervisor::<6>::nuevo(W);
        let mut t = 0;
        while t < 1_000_000 {
            // El ultimo sello, en la rejilla de 125 us.
            assert!(s.mira(t, &activas(t / 125 * 125)), "a los {t} us");
            t += P_S;
        }
        assert_eq!(s.causa(), None);
    }

    #[test]
    fn deja_de_alimentar_cuando_un_sello_pasa_de_la_ventana_y_no_vuelve() {
        let mut s = Supervisor::<6>::nuevo(W);
        let mut v = activas(0);
        assert!(s.mira(0, &v));
        // La ranura 3 sella por ultima vez a los 10 ms; las demas siguen.
        v[3].ultimo_sello_us = 10_000;
        for (k, x) in v.iter_mut().enumerate() {
            if k != 3 {
                x.ultimo_sello_us = 10_000 + W;
            }
        }
        assert!(
            s.mira(10_000 + W, &v),
            "en la ventana justa todavia alimenta"
        );
        assert!(!s.mira(10_000 + W + 1, &v));
        assert_eq!(s.causa(), Some(3));
        // Aunque vuelva a sellar: pasar la ventana es una averia.
        let al_dia = activas(200_000);
        assert!(!s.mira(200_000, &al_dia));
        assert_eq!(s.causa(), Some(3));
        // Y la causa es la primera: las que pasan despues no la pisan.
        assert!(!s.mira(300_000, &al_dia));
        assert_eq!(s.causa(), Some(3));
    }

    #[test]
    fn una_ranura_sin_identidad_no_cuenta() {
        // Nunca sella y nunca tuvo modulo; la ranura 0 tuvo uno, sello y se desenchufo.
        let mut s = Supervisor::<6>::nuevo(W);
        let mut v = activas(0);
        v[5].identidad = false;
        let mut t = 0;
        while t < 1_000_000 {
            for x in &mut v[1..5] {
                x.ultimo_sello_us = t;
            }
            if t == 300_000 {
                v[0].identidad = false;
            }
            if t < 300_000 {
                v[0].ultimo_sello_us = t;
            }
            assert!(s.mira(t, &v), "a los {t} us");
            t += P_S;
        }
    }

    #[test]
    fn un_modulo_que_vuelve_cuenta_desde_que_vuelve() {
        // La ranura 2 sella hasta los 100 ms, se desenchufa a los 120 y vuelve a los 400; sella
        // otra vez desde los 401. Su ultimo sello viejo no la hace contar como muda de 300 ms.
        let mut s = Supervisor::<6>::nuevo(W);
        let mut v = activas(0);
        let mut t = 0;
        while t <= 1_000_000 {
            for k in [0, 1, 3, 4, 5] {
                v[k].ultimo_sello_us = t;
            }
            v[2].identidad = !(120_000..400_000).contains(&t);
            if t <= 100_000 || t > 401_000 {
                v[2].ultimo_sello_us = t;
            }
            assert!(s.mira(t, &v), "a los {t} us");
            t += P_S;
        }
    }

    #[test]
    fn el_modulo_que_llega_a_una_ranura_muerta_reinicia_el_chip() {
        let mut s = Supervisor::<6>::nuevo(W);
        let mut v = activas(0);
        v[2].identidad = false;
        let mut t = 0;
        let mut primera_negativa = None;
        while t <= 600_000 {
            for k in [0, 1, 3, 4, 5] {
                v[k].ultimo_sello_us = t;
            }
            // Llega el modulo a los 400 ms; la ranura no sella (esta `Muerta`).
            v[2].identidad = t >= 400_000;
            if !s.mira(t, &v) && primera_negativa.is_none() {
                primera_negativa = Some(t);
            }
            t += P_S;
        }
        assert_eq!(primera_negativa, Some(400_000 + W + P_S));
        assert_eq!(s.causa(), Some(2));
    }
}
