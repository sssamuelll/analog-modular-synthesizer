//! §3. El reloj: las cuatro fuentes, el tempo, la fase y la rueda libre.

use heapless::Deque;

/// Pulsos de base para estimar el tempo.
///
/// **Sale de una cuenta, no del gusto.** Con ±2 ms de jitter hay una trampa:
/// promediar intervalos consecutivos reduce el ruido con `sqrt(alfa)`,
/// mientras que alargar la base lo reduce con `N`. Medido a 120 BPM y 24 PPQN,
/// en desviacion tipica:
///
/// | Metodo | Error | Coste |
/// |---|---|---|
/// | EMA alfa=0.05 | 1.506 BPM | tau = 0.4 s |
/// | EMA alfa=0.01 | 0.667 BPM | tau = 2.1 s |
/// | EMA alfa=0.001 | 0.210 BPM | tau = 20.8 s — y aun no llega |
/// | **Extremos, N=96** | **0.098 BPM** | ventana de 2.0 s |
///
/// Un promedio movil **no llega ni con una constante de 21 segundos**. Medir
/// contra el pulso de hace 96 es un buffer circular y una resta. La spec §3.6
/// decia que hacia falta un lazo de enganche; la aritmetica dice que no.
///
/// **Ojo con esos numeros: son desviaciones tipicas, y el peor caso se lleva
/// un factor de tres.** La spec §9 pedia ±0.1 BPM confundiendo las dos cosas.
/// El techo de verdad es `ERROR_TEMPO_MAX_MBPM`, que sale de lo que el error
/// cuesta, y contra el N=96 pasa con margen (227 de 240 en el peor de ocho
/// semillas).
///
/// Y 96 pulsos a 24 PPQN son cuatro negras: un compas de 4/4. No se eligio por
/// musical, salio del numero — pero conviene.
pub const VENTANA_TEMPO: usize = 96;

/// Cuanto tiempo sin pulsos antes de dar la fuente por caida y rodar libre
/// (§3.5). Dos negras a 120 BPM.
pub const TIMEOUT_RUEDA_LIBRE_MS: u64 = 500;

/// Cuanto puede errar la lectura de tempo, en milesimas de BPM.
///
/// **No sale del gusto: sale de lo que ese error CUESTA.** Mientras llegan
/// pulsos la fase la manda el pulso, no la estimacion — asi que el tempo
/// estimado solo mueve la fase mientras el reloj esta caido y el instrumento
/// rueda libre. Con `TIMEOUT_RUEDA_LIBRE_MS` de rueda libre, un error relativo
/// `eps` desplaza la fase `eps * 500 ms`. Para que ese desplazamiento no pase
/// de 1 ms: `eps <= 0.2 %`, que a 120 BPM son 240 milesimas.
///
/// El 1 ms viene de la simultaneidad percibida entre dos ataques, que es el
/// numero que `tiempo_budget.py` tiene que ir a buscar con fuente. **Cuando
/// ese guion lo fije, esta constante se revisa contra el.**
pub const ERROR_TEMPO_MAX_MBPM: i64 = 240;

/// Milesimas de BPM, que es como viaja el tempo en el modelo.
pub type MilesimasBpm = u32;

pub struct SeguidorTempo {
    marcas: Deque<u64, { VENTANA_TEMPO + 1 }>,
    mbpm: MilesimasBpm,
}

impl Default for SeguidorTempo {
    fn default() -> Self {
        Self::nuevo()
    }
}

impl SeguidorTempo {
    pub const fn nuevo() -> Self {
        SeguidorTempo {
            marcas: Deque::new(),
            mbpm: 0,
        }
    }

    /// Un pulso llegó en `t_us`. `ppqn_fuente` son los pulsos por negra que
    /// manda esa fuente — Eurorack no lo estandarizó (§3.3).
    pub fn pulso(&mut self, t_us: u64, ppqn_fuente: u32) {
        if self.marcas.is_full() {
            self.marcas.pop_front();
        }
        let _ = self.marcas.push_back(t_us);
        self.recalcular(ppqn_fuente);
    }

    fn recalcular(&mut self, ppqn_fuente: u32) {
        if !self.estable() || ppqn_fuente == 0 {
            return;
        }
        let (Some(vieja), Some(nueva)) = (self.marcas.front(), self.marcas.back()) else {
            return;
        };
        let span_us = nueva.saturating_sub(*vieja);
        if span_us == 0 {
            return;
        }
        // us por pulso × VENTANA_TEMPO = span. El tempo sale de:
        //   mbpm = 60e6 us/min / (us_por_negra) × 1000
        //   us_por_negra = span / VENTANA_TEMPO × ppqn
        // Todo en enteros de 64 bits para no meter coma flotante en el camino.
        let num = 60_000_000_u64 * 1000 * VENTANA_TEMPO as u64;
        let den = span_us * ppqn_fuente as u64;
        self.mbpm = (num / den) as MilesimasBpm;
    }

    /// Hay base suficiente para dar un número.
    pub fn estable(&self) -> bool {
        self.marcas.is_full()
    }

    /// Milésimas de BPM, o **`0` mientras no sea estable**. Nunca un tempo
    /// inventado: inventarlo con tres pulsos sería adivinar en silencio.
    pub fn mbpm(&self) -> MilesimasBpm {
        if self.estable() {
            self.mbpm
        } else {
            0
        }
    }

    /// Cuándo llegó el último pulso, para detectar la caída de la fuente.
    pub fn ultimo_us(&self) -> Option<u64> {
        self.marcas.back().copied()
    }

    pub fn reiniciar(&mut self) {
        self.marcas.clear();
        self.mbpm = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Genera marcas de tiempo de pulsos a un tempo dado, con jitter uniforme
    /// reproducible.
    struct Fuente {
        t_us: u64,
        intervalo_us: u64,
        r: u64,
    }

    impl Fuente {
        fn nueva(bpm: f64, ppqn: u32, semilla: u64) -> Self {
            Fuente {
                t_us: 1_000_000,
                intervalo_us: (60.0 / bpm / ppqn as f64 * 1e6) as u64,
                r: semilla | 1,
            }
        }
        /// La marca del siguiente pulso, corrida ±jitter_us.
        fn siguiente(&mut self, jitter_us: u64) -> u64 {
            self.t_us += self.intervalo_us;
            if jitter_us == 0 {
                return self.t_us;
            }
            self.r ^= self.r << 13;
            self.r ^= self.r >> 7;
            self.r ^= self.r << 17;
            let d = (self.r >> 40) % (2 * jitter_us + 1);
            self.t_us + d - jitter_us
        }
    }

    fn correr(bpm: f64, jitter_us: u64, pulsos: usize) -> SeguidorTempo {
        let mut f = Fuente::nueva(bpm, 24, 7);
        let mut s = SeguidorTempo::nuevo();
        for _ in 0..pulsos {
            s.pulso(f.siguiente(jitter_us), 24);
        }
        s
    }

    #[test]
    fn con_pulsos_limpios_da_el_tempo_exacto() {
        let s = correr(120.0, 0, 200);
        assert!((s.mbpm() as i64 - 120_000).abs() < 50, "dio {}", s.mbpm());
    }

    #[test]
    fn dos_milisegundos_de_jitter_no_sacan_al_tempo_de_lo_que_cuesta() {
        // §9: el test que obliga a la base larga. Un EMA sobre intervalos
        // consecutivos cae aqui aunque le pongas una constante de 20 segundos.
        //
        // El umbral es ERROR_TEMPO_MAX_MBPM, que sale de lo que el error
        // CUESTA en deriva de fase — no de lo que la ventana casualmente da.
        // La spec pedia 100 y estaba mal: ese numero era una desviacion tipica
        // y esto mide el PEOR caso, que se lleva un factor de tres.
        for semilla in 1..=8u64 {
            let mut f = Fuente::nueva(120.0, 24, semilla);
            let mut s = SeguidorTempo::nuevo();
            let mut peor = 0i64;
            for i in 0..600 {
                s.pulso(f.siguiente(2_000), 24);
                if i > VENTANA_TEMPO {
                    peor = peor.max((s.mbpm() as i64 - 120_000).abs());
                }
            }
            assert!(
                peor <= ERROR_TEMPO_MAX_MBPM,
                "semilla {semilla}: se movio {peor} milesimas, y el techo son {ERROR_TEMPO_MAX_MBPM}"
            );
        }
    }

    #[test]
    fn no_dice_nada_hasta_tener_la_ventana_llena() {
        // Inventar un tempo con tres pulsos seria adivinar en silencio.
        let s = correr(120.0, 0, 10);
        assert!(!s.estable());
        assert_eq!(s.mbpm(), 0);
        assert!(correr(120.0, 0, VENTANA_TEMPO + 2).estable());
    }

    #[test]
    fn sigue_un_cambio_de_tempo_en_una_ventana() {
        let mut f = Fuente::nueva(120.0, 24, 3);
        let mut s = SeguidorTempo::nuevo();
        for _ in 0..200 {
            s.pulso(f.siguiente(0), 24);
        }
        let mut f2 = Fuente::nueva(140.0, 24, 3);
        f2.t_us = f.t_us;
        for _ in 0..(VENTANA_TEMPO + 4) {
            s.pulso(f2.siguiente(0), 24);
        }
        assert!((s.mbpm() as i64 - 140_000).abs() < 500, "dio {}", s.mbpm());
    }

    #[test]
    fn el_ppqn_de_la_fuente_cambia_la_lectura_no_el_pulso() {
        // Eurorack no estandarizo los pulsos por negra (§3.3): a 1 PPQN los
        // pulsos van 24 veces mas espaciados para el MISMO tempo.
        let mut f = Fuente::nueva(120.0, 1, 5);
        let mut s = SeguidorTempo::nuevo();
        for _ in 0..(VENTANA_TEMPO + 4) {
            s.pulso(f.siguiente(0), 1);
        }
        assert!((s.mbpm() as i64 - 120_000).abs() < 100, "dio {}", s.mbpm());
    }

    #[test]
    fn reiniciar_lo_deja_como_recien_hecho() {
        let mut s = correr(120.0, 0, 200);
        assert!(s.estable());
        s.reiniciar();
        assert!(!s.estable());
        assert_eq!(s.mbpm(), 0);
        assert_eq!(s.ultimo_us(), None);
    }
}
