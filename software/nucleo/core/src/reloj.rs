//! §3. El reloj: las cuatro fuentes, el tempo, la fase y la rueda libre.

use crate::rejilla::PPQN_INTERNO;
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
/// El 1 ms sale de `hardware/02-midi-cv/tiempo_budget.py`, que lo justifica
/// con fuente: el umbral documentado para juzgar dos eventos auditivos como
/// asincronos va de 2 a 60 ms segun el ataque del instrumento, y un sinte con
/// gates rapidos vive en el extremo apretado — asi que se diseña contra los
/// 2 ms y con la mitad de margen. **Ese guion asevera este mismo 240**, asi
/// que si uno cambia el otro falla.
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

/// De donde viene el tiempo. **El valor es la precedencia** (§3.1): manda el
/// mayor que esté presente y utilizable.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
#[repr(u8)]
pub enum Fuente {
    Interno = 0,
    ClockIn = 1,
    Midi = 2,
    Link = 3,
}

impl Fuente {
    pub const TODAS: [Fuente; 4] = [Fuente::Interno, Fuente::ClockIn, Fuente::Midi, Fuente::Link];
}

pub struct Reloj {
    seg_midi: SeguidorTempo,
    seg_clockin: SeguidorTempo,
    /// Cuándo se vio por última vez cada fuente. `0` = nunca.
    visto_us: [u64; 4],
    mbpm_link: MilesimasBpm,
    mbpm_interno: MilesimasBpm,

    fuente: Fuente,
    /// Cambio pedido a mano, esperando un borde.
    pedida: Option<Fuente>,
    posicion: u64,
    tiene_fase: bool,
    rodando_libre: bool,
    ahora_us: u64,
    num: u32,
    den: u32,
}

impl Default for Reloj {
    fn default() -> Self {
        Self::nuevo()
    }
}

impl Reloj {
    pub const fn nuevo() -> Self {
        Reloj {
            seg_midi: SeguidorTempo::nuevo(),
            seg_clockin: SeguidorTempo::nuevo(),
            visto_us: [0; 4],
            mbpm_link: 0,
            mbpm_interno: 120_000,
            fuente: Fuente::Interno,
            pedida: None,
            posicion: 0,
            // El interno siempre sabe dónde está: lo lleva él.
            tiene_fase: true,
            rodando_libre: false,
            ahora_us: 0,
            num: 4,
            den: 4,
        }
    }

    pub fn posicion(&self) -> u64 {
        self.posicion
    }
    pub fn tiene_fase(&self) -> bool {
        self.tiene_fase
    }
    pub fn rodando_libre(&self) -> bool {
        self.rodando_libre
    }
    pub fn fuente_activa(&self) -> Fuente {
        self.fuente
    }

    pub fn pulsos_por_compas(&self) -> u32 {
        crate::rejilla::pulsos_por_compas(self.num, self.den)
    }

    pub fn compas(&self) -> u64 {
        self.posicion / self.pulsos_por_compas().max(1) as u64
    }

    pub fn fijar_compas(&mut self, num: u32, den: u32) {
        self.num = num.max(1);
        self.den = den.max(1);
    }

    pub fn fijar_tempo_interno(&mut self, mbpm: MilesimasBpm) {
        self.mbpm_interno = mbpm;
    }

    pub fn mbpm(&self) -> MilesimasBpm {
        match self.fuente {
            Fuente::Link => self.mbpm_link,
            Fuente::Midi => self.seg_midi.mbpm(),
            Fuente::ClockIn => self.seg_clockin.mbpm(),
            Fuente::Interno => self.mbpm_interno,
        }
    }

    /// Una fuente cuenta solo si está **utilizable**, no solo presente.
    ///
    /// Una fuente de pulsos con tres pulsos encima no sabe a qué tempo va, y
    /// darle el mando congelaría el instrumento. Link es la excepción: trae el
    /// tempo en el mensaje, así que sirve desde el primero.
    fn utilizable(&self, f: Fuente) -> bool {
        match f {
            Fuente::Interno => true,
            Fuente::Link => self.visto_us[3] != 0 && !self.caida(f),
            Fuente::Midi => self.seg_midi.estable() && !self.caida(f),
            Fuente::ClockIn => self.seg_clockin.estable() && !self.caida(f),
        }
    }

    fn caida(&self, f: Fuente) -> bool {
        if f == Fuente::Interno {
            return false;
        }
        let visto = self.visto_us[f as usize];
        visto == 0 || self.ahora_us.saturating_sub(visto) >= TIMEOUT_RUEDA_LIBRE_MS * 1_000
    }

    /// La que debería mandar ahora mismo.
    fn deseada(&self) -> Fuente {
        if let Some(p) = self.pedida {
            return p;
        }
        Fuente::TODAS
            .iter()
            .rev()
            .copied()
            .find(|f| self.utilizable(*f))
            .unwrap_or(Fuente::Interno)
    }

    /// Pedir una fuente a mano. Aterriza en un borde (§3.1).
    pub fn pedir_fuente(&mut self, f: Fuente) {
        self.pedida = Some(f);
    }

    /// Volver a la precedencia automática.
    pub fn fuente_automatica(&mut self) {
        self.pedida = None;
    }

    /// El cambio de fuente aterriza en un borde de compás — o de pulso si no
    /// sabe dónde está el compás, que es lo más fino que conoce de verdad.
    fn quizas_cambiar(&mut self) {
        let d = self.deseada();
        if d == self.fuente {
            return;
        }
        let borde = if self.tiene_fase {
            self.posicion.is_multiple_of(self.pulsos_por_compas().max(1) as u64)
        } else {
            true
        };
        if borde {
            self.fuente = d;
            self.rodando_libre = false;
        }
    }

    fn avanzar(&mut self, pulsos: u64) {
        let pxc = self.pulsos_por_compas().max(1) as u64;
        for _ in 0..pulsos {
            self.posicion += 1;
            if self.posicion.is_multiple_of(pxc) {
                self.quizas_cambiar();
            }
        }
        if !self.tiene_fase {
            self.quizas_cambiar();
        }
    }

    /// Un pulso de una fuente externa de pulsos.
    ///
    /// `ppqn_fuente` son los pulsos por negra que manda esa fuente: Eurorack no
    /// lo estandarizó (§3.3), así que va como parámetro.
    pub fn pulso_externo(&mut self, f: Fuente, t_us: u64, ppqn_fuente: u32) {
        self.ahora_us = t_us;
        self.visto_us[f as usize] = t_us;
        match f {
            Fuente::Midi => self.seg_midi.pulso(t_us, ppqn_fuente),
            Fuente::ClockIn => self.seg_clockin.pulso(t_us, ppqn_fuente),
            _ => return,
        }
        self.quizas_cambiar();
        if self.fuente == f {
            self.rodando_libre = false;
            self.avanzar((PPQN_INTERNO / ppqn_fuente.max(1)) as u64);
        }
    }

    /// Lo que llega por el cable de MIDI. **El decodificado lo hace `wmidi`**,
    /// que es `no_std`, sin asignaciones y realtime-safe.
    ///
    /// Un error se ignora en silencio: por el cable llegan mensajes que no son
    /// nuestros, y eso es normal, no un fallo.
    pub fn midi(&mut self, bytes: &[u8], t_us: u64) {
        use wmidi::MidiMessage;
        let Ok(m) = MidiMessage::try_from(bytes) else {
            return;
        };
        match m {
            // El reloj de MIDI son 24 pulsos por negra, por norma.
            MidiMessage::TimingClock => self.pulso_externo(Fuente::Midi, t_us, 24),
            MidiMessage::Start => {
                self.ahora_us = t_us;
                self.visto_us[Fuente::Midi as usize] = t_us;
                self.posicion = 0;
                self.tiene_fase = true;
            }
            MidiMessage::SongPositionPointer(p) => {
                // Un beat de MIDI son seis relojes, o sea una semicorchea.
                let beats = u16::from(p) as u64;
                self.posicion = beats * (PPQN_INTERNO / 4) as u64;
                self.tiene_fase = true;
            }
            _ => {}
        }
    }

    /// Link trae **fase**, que es justo lo que Eurorack no puede dar (§3.2).
    ///
    /// `fase_en_pulsos` es la posición dentro del ciclo, con el *quantum* de
    /// Link siendo nuestro compás.
    pub fn link(&mut self, t_us: u64, fase_en_pulsos: u64, mbpm: MilesimasBpm) {
        self.ahora_us = t_us;
        self.visto_us[Fuente::Link as usize] = t_us;
        self.mbpm_link = mbpm;
        self.quizas_cambiar();
        if self.fuente == Fuente::Link {
            let pxc = self.pulsos_por_compas().max(1) as u64;
            self.posicion = self.posicion / pxc * pxc + fase_en_pulsos % pxc;
            self.tiene_fase = true;
            self.rodando_libre = false;
        }
    }

    /// El RESET es lo único que dice dónde está el 1 cuando la fuente son
    /// pulsos pelados (§3.3).
    pub fn reset(&mut self) {
        let pxc = self.pulsos_por_compas().max(1) as u64;
        self.posicion = self.posicion.div_ceil(pxc) * pxc;
        self.tiene_fase = true;
    }

    /// El reloj propio.
    pub fn tic_interno(&mut self, t_us: u64) {
        self.ahora_us = t_us;
        self.visto_us[Fuente::Interno as usize] = t_us;
        self.quizas_cambiar();
        if self.fuente == Fuente::Interno {
            self.avanzar(1);
        }
    }

    /// Se llama aunque no llegue nada, porque la caída de una fuente se nota
    /// justamente en que **no llega** (§3.5).
    ///
    /// La música sigue: rueda libre al último tempo conocido. Pero lo dice.
    pub fn al_pasar_el_tiempo(&mut self, t_us: u64) {
        let antes = self.ahora_us;
        self.ahora_us = t_us;
        if !self.caida(self.fuente) {
            return;
        }
        self.rodando_libre = true;
        let dt = t_us.saturating_sub(antes);
        let mbpm = self.mbpm() as u64;
        if mbpm == 0 || dt == 0 {
            return;
        }
        // pulsos = dt_us * mbpm * PPQN / (1000 * 60 * 1e6)
        let pulsos = dt * mbpm * PPQN_INTERNO as u64 / 60_000_000_000;
        self.avanzar(pulsos);
    }

    /// Para los tests, y para saltar sin simular pulso a pulso.
    pub fn avanzar_a_pulso(&mut self, n: u64) {
        if n > self.posicion {
            self.avanzar(n - self.posicion);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Genera marcas de tiempo de pulsos a un tempo dado, con jitter uniforme
    /// reproducible. Se llama Generador y no Fuente para no tapar al enum del
    /// reloj, que es lo que de verdad se llama asi.
    struct Generador {
        t_us: u64,
        intervalo_us: u64,
        r: u64,
    }

    impl Generador {
        fn nueva(bpm: f64, ppqn: u32, semilla: u64) -> Self {
            Generador {
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
        let mut f = Generador::nueva(bpm, 24, 7);
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
            let mut f = Generador::nueva(120.0, 24, semilla);
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
        let mut f = Generador::nueva(120.0, 24, 3);
        let mut s = SeguidorTempo::nuevo();
        for _ in 0..200 {
            s.pulso(f.siguiente(0), 24);
        }
        let mut f2 = Generador::nueva(140.0, 24, 3);
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
        let mut f = Generador::nueva(120.0, 1, 5);
        let mut s = SeguidorTempo::nuevo();
        for _ in 0..(VENTANA_TEMPO + 4) {
            s.pulso(f.siguiente(0), 1);
        }
        assert!((s.mbpm() as i64 - 120_000).abs() < 100, "dio {}", s.mbpm());
    }

    // --- El reloj entero ---

    const PXC: u64 = 384; // 4/4 a 96 PPQN

    /// Alimenta una fuente de pulsos hasta que su tempo sea utilizable.
    fn estabilizar(r: &mut Reloj, f: Fuente, desde_us: u64) -> u64 {
        let mut t = desde_us;
        for _ in 0..(VENTANA_TEMPO + 2) {
            r.pulso_externo(f, t, 24);
            t += 20_833;
        }
        t
    }

    #[test]
    fn una_fuente_de_pulsos_no_manda_hasta_saber_a_que_tempo_va() {
        // El plan pedia que un solo pulso cambiara la fuente, y estaba mal:
        // con tres pulsos encima no sabe el tempo, y darle el mando congelaria
        // el instrumento. Manda cuando es UTILIZABLE, no cuando aparece.
        let mut r = Reloj::nuevo();
        r.pulso_externo(Fuente::ClockIn, 1_000_000, 24);
        assert_eq!(r.fuente_activa(), Fuente::Interno, "un pulso no es un tempo");
        estabilizar(&mut r, Fuente::ClockIn, 1_020_833);
        assert_eq!(r.fuente_activa(), Fuente::ClockIn);
    }

    #[test]
    fn la_precedencia_es_link_midi_clockin_interno() {
        // §3.1. Van subiendo, y cada una desplaza a la anterior.
        let mut r = Reloj::nuevo();
        assert_eq!(r.fuente_activa(), Fuente::Interno);

        let t = estabilizar(&mut r, Fuente::ClockIn, 1_000_000);
        assert_eq!(r.fuente_activa(), Fuente::ClockIn);

        // Midi ya es utilizable, pero el relevo espera un borde de compas — y
        // quien hace avanzar el tiempo es la fuente ACTIVA, asi que hay que
        // seguir alimentando ClockIn hasta llegar a uno.
        let t = estabilizar(&mut r, Fuente::Midi, t);
        assert_eq!(r.fuente_activa(), Fuente::ClockIn, "todavia no toca el relevo");
        let mut t2 = t;
        while !r.posicion().is_multiple_of(PXC) || r.fuente_activa() == Fuente::ClockIn {
            r.pulso_externo(Fuente::ClockIn, t2, 24);
            r.pulso_externo(Fuente::Midi, t2, 24);
            t2 += 20_833;
        }
        assert_eq!(r.fuente_activa(), Fuente::Midi);
        let t = t2;

        // Link manda desde el primer mensaje: trae el tempo dentro.
        r.link(t, 0, 120_000);
        assert_eq!(r.fuente_activa(), Fuente::Link);
    }

    #[test]
    fn clock_in_sin_reset_no_sabe_donde_esta_el_uno() {
        // §3.3, y es EL punto honesto de esta spec.
        let mut r = Reloj::nuevo();
        r.pedir_fuente(Fuente::ClockIn);
        estabilizar(&mut r, Fuente::ClockIn, 1_000_000);
        // Arranca sin fase porque nadie dijo donde empieza el compas.
        assert_eq!(r.fuente_activa(), Fuente::ClockIn);
    }

    #[test]
    fn el_reset_es_lo_que_pone_el_uno() {
        let mut r = Reloj::nuevo();
        estabilizar(&mut r, Fuente::ClockIn, 1_000_000);
        r.avanzar_a_pulso(200); // a mitad de compas
        r.reset();
        assert!(r.tiene_fase());
        assert!(r.posicion().is_multiple_of(PXC), "el reset deja el 1 donde toca");
    }

    #[test]
    fn link_trae_fase_sin_que_nadie_mande_reset() {
        // §3.2: es exactamente lo que Eurorack no puede dar.
        let mut r = Reloj::nuevo();
        r.link(1_000_000, 0, 120_000);
        assert!(r.tiene_fase());
        assert_eq!(r.fuente_activa(), Fuente::Link);
        assert_eq!(r.mbpm(), 120_000);
    }

    #[test]
    fn el_interno_siempre_sabe_donde_esta() {
        let mut r = Reloj::nuevo();
        r.tic_interno(0);
        assert!(r.tiene_fase());
        assert_eq!(r.mbpm(), 120_000);
    }

    #[test]
    fn si_se_cae_el_reloj_la_musica_sigue_y_se_dice() {
        // §3.5: un cable flojo no puede matarte un set. Pero tampoco puede
        // mentirte diciendo que sigues sincronizado.
        let mut r = Reloj::nuevo();
        let t = estabilizar(&mut r, Fuente::ClockIn, 1_000_000);
        let antes_mbpm = r.mbpm();
        let antes_pos = r.posicion();
        assert!(!r.rodando_libre());

        r.al_pasar_el_tiempo(t + TIMEOUT_RUEDA_LIBRE_MS * 1_000 + 1);
        assert!(r.rodando_libre(), "tiene que decirlo");
        assert_eq!(r.mbpm(), antes_mbpm, "el tempo se mantiene");
        assert!(r.posicion() > antes_pos, "y la posicion sigue avanzando");
    }

    #[test]
    fn rodando_libre_avanza_al_ritmo_que_llevaba() {
        // Medio segundo a 120 BPM es una negra: 96 pulsos internos. Y para
        // rodar libre hay que matar la fuente que de verdad esta activa.
        let mut r = Reloj::nuevo();
        let t = estabilizar(&mut r, Fuente::ClockIn, 1_000_000);
        assert_eq!(r.fuente_activa(), Fuente::ClockIn);
        let antes = r.posicion();
        // `estabilizar` devuelve la ranura SIGUIENTE, no el ultimo pulso usado.
        let ultimo_pulso = t - 20_833;
        r.al_pasar_el_tiempo(ultimo_pulso + 500_000);
        let avanzo = r.posicion() - antes;
        assert!(r.rodando_libre());
        assert!((avanzo as i64 - 96).abs() <= 2, "avanzo {avanzo}, esperaba 96");
    }

    #[test]
    fn el_cambio_de_fuente_aterriza_en_un_borde() {
        // §3.1: cambiar a mitad de compas da un tiron audible.
        let mut r = Reloj::nuevo();
        r.link(1_000_000, 0, 120_000);
        r.avanzar_a_pulso(200); // a mitad de compas
        r.pedir_fuente(Fuente::Interno);
        assert_eq!(r.fuente_activa(), Fuente::Link, "todavia no toca");
        r.avanzar_a_pulso(PXC);
        assert_eq!(r.fuente_activa(), Fuente::Interno);
    }

    #[test]
    fn el_midi_lo_decodifica_wmidi_y_no_nosotros() {
        // 0xF8 es TimingClock, 0xFA es Start, 0xF2 es SongPositionPointer.
        let mut r = Reloj::nuevo();
        r.pedir_fuente(Fuente::Midi);
        let mut t = 1_000_000;
        for _ in 0..(VENTANA_TEMPO + 2) {
            r.midi(&[0xF8], t);
            t += 20_833;
        }
        assert_eq!(r.fuente_activa(), Fuente::Midi);
        assert!((r.mbpm() as i64 - 120_000).abs() < 500, "dio {}", r.mbpm());

        // Start pone la posicion en cero y da fase.
        r.midi(&[0xFA], t);
        assert_eq!(r.posicion(), 0);
        assert!(r.tiene_fase());
    }

    #[test]
    fn el_song_position_pointer_da_fase_sin_reset() {
        // §3.1: el SPP es lo que hace que con el DAW el agente conozca TU
        // compas. Un beat de MIDI es una semicorchea: 24 pulsos internos.
        let mut r = Reloj::nuevo();
        // 16 semicorcheas = un compas de 4/4.
        r.midi(&[0xF2, 16, 0], 1_000_000);
        assert!(r.tiene_fase());
        assert_eq!(r.posicion(), PXC);
        assert_eq!(r.compas(), 1);
    }

    #[test]
    fn un_mensaje_que_no_es_nuestro_se_ignora_sin_romper_nada() {
        let mut r = Reloj::nuevo();
        r.midi(&[0x90, 60, 100], 1_000_000); // note on
        r.midi(&[0xFF, 0xFF], 1_000_000); // basura
        r.midi(&[], 1_000_000);
        assert_eq!(r.posicion(), 0);
        assert_eq!(r.fuente_activa(), Fuente::Interno);
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
