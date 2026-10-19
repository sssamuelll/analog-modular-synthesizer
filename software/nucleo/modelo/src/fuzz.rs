//! El fuzz de la junta (`sim/junta3/src/fuzz.rs`): fallos y retenciones al azar con tasas de
//! Poisson sobre las seis ranuras, con mensajes de 9 a 103 bytes mezclados.

use crate::motor::{ms, Cfg, HwEv, Inj, Sim, PERIODO_NS};

struct Rng(u64);

impl Rng {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 >> 12;
        self.0 ^= self.0 << 25;
        self.0 ^= self.0 >> 27;
        self.0.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }
    fn unif(&mut self) -> f64 {
        (self.next() >> 11) as f64 / (1u64 << 53) as f64
    }
    fn exp(&mut self, rate: f64) -> f64 {
        -(1.0 - self.unif()).ln() / rate
    }
}

fn mezcla(n: usize, k: u64) -> u16 {
    match (n as u64 * 7919 + k * 104_729) % 10 {
        0 => 9,
        1 => 14,
        2..=5 => 25,
        6 | 7 => 41,
        8 => 71,
        _ => 103,
    }
}

/// Las tasas, por segundo: SPI envenenados, canales atascados que el reset del GPDMA1 cura,
/// retenciones de P2 de 20 us a 6 ms, y tics tardios de hasta 120 us (P2 atomico).
#[derive(Clone, Copy)]
pub struct Tasas {
    pub hang: f64,
    pub stuck: f64,
    pub p2: f64,
    pub late: f64,
}

/// Monta una corrida de `t_s` segundos con la semilla `seed`. Devuelve el modelo, el final y
/// cuantos fallos de cada clase se inyectaron.
pub fn montar(
    seed: u64,
    t_s: u64,
    tasas: Tasas,
    f_sck: u64,
    tweak: &dyn Fn(&mut Cfg),
) -> (Sim, u64, [u64; 4]) {
    let mut r = Rng(0x9E37_79B9_7F4A_7C15 ^ seed.wrapping_mul(0xD1B5_4A32_D192_ED03));
    let mut cfg = Cfg::base();
    cfg.f_sck = f_sck;
    cfg.pat = Some(mezcla);
    tweak(&mut cfg);
    let mut sim = Sim::new(cfg);
    let t_fin = ms(t_s * 1000);
    let mut inj = [0u64; 4];
    // Un tren de Poisson desde los 10 ms: llama a `pon` en cada instante.
    let tren = |r: &mut Rng, tasa: f64, pon: &mut dyn FnMut(&mut Rng, u64)| {
        if tasa <= 0.0 {
            return;
        }
        let mut t = ms(10) as f64;
        loop {
            t += r.exp(tasa) * 1e9;
            if t >= t_fin as f64 {
                break;
            }
            pon(r, t as u64);
        }
    };
    let mut ev = Vec::new();
    tren(&mut r, tasas.hang, &mut |r, t| {
        let n = (r.next() % 6) as usize;
        ev.push((
            t,
            HwEv::Inject {
                slot: n,
                kind: Inj::Hang,
            },
        ));
        inj[0] += 1;
    });
    tren(&mut r, tasas.stuck, &mut |r, t| {
        let n = (r.next() % 6) as usize;
        let kind = Inj::Stuck { persistente: false };
        ev.push((t, HwEv::Inject { slot: n, kind }));
        inj[1] += 1;
    });
    tren(&mut r, tasas.p2, &mut |r, t| {
        let d = 20.0f64 * 300.0f64.powf(r.unif()) * 1000.0; // 20 us .. 6 ms
        ev.push((
            t,
            HwEv::P2 {
                dur: d as u64,
                atomic: false,
            },
        ));
        inj[2] += 1;
    });
    tren(&mut r, tasas.late, &mut |r, t| {
        let k = t / PERIODO_NS + 1;
        let d = (r.unif() * 120.0 * 1000.0) as u64;
        ev.push((
            k * PERIODO_NS - 500,
            HwEv::P2 {
                dur: d + 500,
                atomic: true,
            },
        ));
        inj[3] += 1;
    });
    // Secciones criticas cortas del hilo: 1 a 5 us, 500 por segundo.
    tren(&mut r, 500.0, &mut |r, t| {
        let d = (1.0 + 4.0 * r.unif()) * 1000.0;
        ev.push((
            t,
            HwEv::P2 {
                dur: d as u64,
                atomic: true,
            },
        ));
    });
    for (t, e) in ev {
        sim.hw_at(t, e);
    }
    (sim, t_fin, inj)
}
