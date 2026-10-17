use crate::esc::*;
use crate::motor::*;
use crate::transporte_j2::Estado;

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 >> 12;
        self.0 ^= self.0 << 25;
        self.0 ^= self.0 >> 27;
        self.0.wrapping_mul(0x2545F4914F6CDD1D)
    }
    fn unif(&mut self) -> f64 {
        (self.next() >> 11) as f64 / (1u64 << 53) as f64
    }
    fn exp(&mut self, rate: f64) -> f64 {
        -(1.0 - self.unif()).ln() / rate
    }
}

fn mezcla(n: usize, k: u64) -> u16 {
    let h = (n as u64 * 7919 + k * 104729) % 10;
    match h {
        0 => 9,
        1 => 14,
        2 | 3 | 4 | 5 => 25,
        6 | 7 => 41,
        8 => 71,
        _ => 103,
    }
}

pub fn montar(seed: u64, t_s: u64, lam_hang: f64, lam_stuck: f64, lam_p2: f64, lam_late: f64, f_sck: u64) -> (Sim, u64, (u64, u64, u64, u64)) {
        let mut r = Rng(0x9E3779B97F4A7C15 ^ (seed * 0xD1B54A32D192ED03));
        let mut cfg = Cfg::base();
        cfg.f_sck = f_sck;
        cfg.pat = Some(mezcla);
        cfg.budget = Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false };
        let mut sim = Sim::new(cfg);
        let t_fin = ms(t_s * 1000);
        // eventos
        let mut inj = (0u64, 0u64, 0u64, 0u64);
        let mut t = ms(10) as f64;
        while t < (t_fin as f64) {
            t += r.exp(lam_hang) * 1e9;
            if t >= t_fin as f64 {
                break;
            }
            let n = (r.next() % 6) as usize;
            sim.hw_at(t as u64, HwEv::Inject { slot: n, kind: Inj::Hang });
            inj.0 += 1;
        }
        let mut t = ms(10) as f64;
        while lam_stuck > 0.0 && t < (t_fin as f64) {
            t += r.exp(lam_stuck) * 1e9;
            if t >= t_fin as f64 {
                break;
            }
            let n = (r.next() % 6) as usize;
            sim.hw_at(t as u64, HwEv::Inject { slot: n, kind: Inj::Stuck { persistente: false } });
            inj.1 += 1;
        }
        let mut t = ms(10) as f64;
        while t < (t_fin as f64) {
            t += r.exp(lam_p2) * 1e9;
            if t >= t_fin as f64 {
                break;
            }
            let d = (20.0f64 * (300.0f64).powf(r.unif())) * 1000.0; // 20 us .. 6 ms
            sim.hw_at(t as u64, HwEv::P2 { dur: d as u64, atomic: false });
            inj.2 += 1;
        }
        let mut t = ms(10) as f64;
        while lam_late > 0.0 && t < (t_fin as f64) {
            t += r.exp(lam_late) * 1e9;
            if t >= t_fin as f64 {
                break;
            }
            let k = (t as u64) / PERIODO_NS + 1;
            let d = (r.unif() * 120.0 * 1000.0) as u64;
            sim.hw_at(k * PERIODO_NS - 500, HwEv::P2 { dur: d + 500, atomic: true });
            inj.3 += 1;
        }
        let mut t = ms(10) as f64;
        while t < (t_fin as f64) {
            t += r.exp(500.0) * 1e9;
            if t >= t_fin as f64 {
                break;
            }
            let d = (1.0 + 4.0 * r.unif()) * 1000.0;
            sim.hw_at(t as u64, HwEv::P2 { dur: d as u64, atomic: true });
        }
        (sim, t_fin, inj)
}

pub fn fuzz(seeds: u64, t_s: u64, lam_hang: f64, lam_stuck: f64, lam_p2: f64, lam_late: f64, f_sck: u64) {
    println!("== FUZZ en la maquina real: {seeds} semillas x {t_s} s, seis ranuras, mensajes mezclados (9/14/25/41/71/103 B) a {} MHz ==", f_sck as f64 / 1e6);
    println!("   por segundo: cuelgues {lam_hang}, canal atascado (curable) {lam_stuck}, retenciones de P2 {lam_p2} (20 us..6 ms, log-uniforme), tics tardios {lam_late} (0..120 us) + secciones PRIMASK de 1-5 us a 500/s");
    let mut tot = (0u64, 0u64, 0u64, 0u64, 0u64, 0u64);
    let mut viol = 0;
    let mut muertes = 0;
    let mut resets = 0;
    let mut peor_gap = 0u64;
    let mut max_anillo = 0usize;
    let mut max_conc = 0u32;
    let mut plan_lat = 0u64;
    let mut rec_lat = 0u64;
    for seed in 1..=seeds {
        let (mut sim, t_fin, inj) = montar(seed, t_s, lam_hang, lam_stuck, lam_p2, lam_late, f_sck);
        sim.run_until(t_fin + ms(30));
        // invariantes
        let mut mal: Vec<String> = Vec::new();
        for n in 0..N {
            let s = &sim.s[n];
            let pol = s.pol.plazos_vencidos();
            if pol != s.plazos {
                mal.push(format!("ranura {n}: politica vio {pol} plazos y el tic emitio {}", s.plazos));
            }
            let viva = s.tic.estado() != Estado::Muerta;
            if viva && s.recuperaciones != s.plazos {
                mal.push(format!("ranura {n}: {} plazos y {} recuperaciones (viva)", s.plazos, s.recuperaciones));
            }
            if viva && matches!(s.tic.estado(), Estado::Vencida { .. } | Estado::Reiniciando { .. }) {
                mal.push(format!("ranura {n}: se quedo en {:?}", s.tic.estado()));
            }
            if s.ring_lost != 0 {
                mal.push(format!("ranura {n}: perdio {} eventos del anillo", s.ring_lost));
            }
            if s.sucia {
                mal.push(format!("ranura {n}: SUCIA al final"));
            }
            if !viva {
                muertes += 1;
            }
            if s.max_gap > peor_gap {
                peor_gap = s.max_gap;
            }
            if s.ring_max > max_anillo {
                max_anillo = s.ring_max;
            }
        }
        plan_lat = plan_lat.max(sim.plan_lat_max);
        rec_lat = rec_lat.max(sim.rec_lat_max);
        if sim.max_concurrent_esc > max_conc {
            max_conc = sim.max_concurrent_esc;
        }
        if sim.iwdg_reset_at.is_some() {
            resets += 1;
        }
        let plazos: u32 = sim.s.iter().map(|s| s.plazos).sum();
        let rec: u32 = sim.s.iter().map(|s| s.recuperaciones).sum();
        tot.0 += plazos as u64;
        tot.1 += rec as u64;
        tot.2 += sim.escaladas as u64;
        tot.3 += sim.denegadas as u64;
        tot.4 += sim.tics_fus as u64;
        tot.5 += inj.0 + inj.1;
        if !mal.is_empty() {
            viol += 1;
            println!("   semilla {seed}: VIOLACION {:?}", &mal[..mal.len().min(3)]);
        }
    }
    println!("   total: plazos {} recuperaciones {} escaladas {} denegadas {} tics_fundidos {} ; ranuras muertas {} ; resets del chip {} ; semillas con violacion de invariante {}/{}",
        tot.0, tot.1, tot.2, tot.3, tot.4, muertes, resets, viol, seeds);
    println!("   anillo_max {} (cap. 8) ; escaladas concurrentes max {} ; hueco maximo entre tramas validas en el modulo {:.1} us", max_anillo, max_conc, us(peor_gap));
    println!("   latencia maxima desde que el tic hace pendiente al planificador hasta que corre: {:.1} us ; desde que se pide la recuperacion hasta que corre: {:.1} us", us(plan_lat), us(rec_lat));
}

pub fn dbg12() {
    let (mut sim, t_fin, _) = montar(12, 4, 15.0, 0.0, 30.0, 5.0, 6_250_000);
    sim.run_until(t_fin + ms(30));
    let s = &sim.s[2];
    println!("estado final ranura 2: {:?} plazos {} rec {} sucia {} rec_pedida {} en_curso {} hecha {} denied {} t_fin {} ms ahora {} ms", s.tic.estado(), s.plazos, s.recuperaciones, s.sucia, s.rec_pedida, s.rec_en_curso, s.rec_hecha, s.denied, t_fin / 1_000_000, sim.now / 1_000_000);
    let ult: Vec<_> = sim.marks.iter().filter(|m| m.slot == 2 && m.t + ms(50) > t_fin).collect();
    for m in ult.iter().rev().take(14).rev() {
        println!("   t={:.3} ms {} {}", m.t as f64 / 1e6, m.what, m.x);
    }
    println!("   pend: tic {} plan {} rec {} p2 {} ; running {:?} ; stack {}", sim.pend_tic, sim.pend_plan, sim.pend_rec, sim.pend_p2.len(), sim.running.as_ref().map(|j| j.name), sim.stack.len());
}
