use crate::esc::*;
use crate::motor::*;
use crate::transporte_j2::Estado;

/// C1: cada ISR de P2 cumple R-H1 (<= 12 ms; la v3 pide <= 1 ms), pero van una tras otra.
pub fn c1() {
    println!("== C1: R-H1 dice «ninguna ISR de P2 retiene al planificador mas de 12 ms» (y pide <= 1 ms). Pero varias seguidas suman. Ranura 2 se cuelga, seis ranuras activas ==");
    for &(d_us, ks) in &[(1000u64, &[5u64, 10, 12, 13, 14, 20][..]), (100, &[100, 120, 124, 126, 130, 200][..]), (5000, &[2, 3][..])] {
        for &k in ks {
            let mut cfg = Cfg::base();
            cfg.budget = Budget::Ninguno;
            let mut sim = Sim::new(cfg);
            let jobs: Vec<Vec<(u64, bool)>> = (0..k).map(|_| vec![(d_us * 1000, false)]).collect();
            sim.hold_on_vencida = Some((2, jobs));
            sim.hw_at(ms(30), HwEv::Inject { slot: 2, kind: Inj::Hang });
            sim.run_until(ms(200));
            let t0 = first(&sim, "cstart_veneno", 2).unwrap();
            let viva = sim.s[2].tic.estado() != Estado::Muerta;
            println!(
                "   {:3} ISR de P2 de {:5} us seguidas (cada una dentro de R-H1; total {:6.1} ms) -> ranura 2 {}   {}",
                k, d_us, (k * d_us) as f64 / 1000.0,
                if viva { "VIVA" } else { "MUERTA" },
                if viva { String::new() } else { format!("(muerta a t={:.1} ms; el supervisor deja de alimentar a t={:.1} ms; IWDG reinicia a t={:.1} ms)",
                    us(first(&sim, "muerta", 2).unwrap() - t0) / 1000.0,
                    sim.first_refusal.map_or(f64::NAN, |t| us(t - t0) / 1000.0),
                    sim.iwdg_reset_at.map_or(f64::NAN, |t| us(t - t0) / 1000.0)) }
            );
        }
    }
}

/// C2: tics fundidos y el tiempo real de la cota.
pub fn c2() {
    println!("== C2: la cota son 100 tics; ¿cuantos ms son si P2 toma secciones criticas (PRIMASK) durante la retencion? ==");
    println!("   retencion de P2 de 60 ms formada por [400 us abierto + L us PRIMASK] repetido; ranura 2 colgada; cota Vencida 100 tics (nominal 12,6 ms)");
    println!("   {:>6} | {:>10} {:>9} {:>11} | {:>16}", "L us", "tics_fus", "UEV/tic", "perdida f", "vencida->muerta ms");
    for &l in &[0u64, 20, 60, 100, 130, 200, 300, 500, 1000] {
        let mut cfg = Cfg::base();
        let mut sim = Sim::new(cfg);
        let mut seq: Vec<(u64, bool)> = Vec::new();
        let mut t = 0u64;
        while t < 60_000 {
            seq.push((400_000, false));
            if l > 0 {
                seq.push((l * 1000, true));
            }
            t += 400 + l;
        }
        sim.hold_on_vencida = Some((2, vec![seq]));
        sim.hw_at(ms(30), HwEv::Inject { slot: 2, kind: Inj::Hang });
        sim.run_until(ms(160));
        let tv = first(&sim, "tic_vencida", 2);
        let tm = first(&sim, "muerta", 2);
        let tics_total_ventana = match (tv, tm) { (Some(a), Some(b)) => (b - a) as f64 / 125_000.0, _ => f64::NAN };
        let ms_real = match (tv, tm) { (Some(a), Some(b)) => (b - a) as f64 / 1e6, _ => f64::NAN };
        let f = 1.0 - 101.0 / tics_total_ventana;
        println!("   {:>6} | {:>10} {:>9.2} {:>10.1}% | {:>16.2}", l, sim.tics_fus, tics_total_ventana / 101.0, 100.0 * f, ms_real);
    }
}

/// C3: el anillo de 8 bajo retenciones de P2 largas (seis ranuras), y un cuelgue que cae dentro.
pub fn c3() {
    println!("== C3: ocupacion maxima del anillo de eventos (cap. 8) con seis ranuras y retenciones de P2 de D ms cada 50 ms, 500 ms ==");
    for &d_us in &[100u64, 500, 1000, 3000, 12000, 30000] {
        let cfg = Cfg::base();
        let mut sim = Sim::new(cfg);
        let mut t = ms(20);
        while t < ms(500) {
            sim.hw_at(t, HwEv::P2 { dur: d_us * 1000, atomic: false });
            t += ms(50);
        }
        sim.run_until(ms(520));
        let plazos: u32 = sim.s.iter().map(|s| s.plazos).sum();
        let sinb: u32 = sim.s.iter().map(|s| s.sin_bajada).sum();
        let lost: u32 = sim.s.iter().map(|s| s.ring_lost).sum();
        println!("   D = {:6} us: anillo_max {} eventos_perdidos {} plazos {} tramas_sin_bajada(total) {} tics_fus {}", d_us, sim.ring_hist_max, lost, plazos, sinb, sim.tics_fus);
    }
    println!("   y un cuelgue de la ranura 2 que cae a distintas fases DENTRO de una retencion de 12 ms:");
    let mut peor = 0;
    let mut vivas = 0;
    let mut muertas = 0;
    for fase in 0..96u64 {
        let cfg = Cfg::base();
        let mut sim = Sim::new(cfg);
        sim.hw_at(ms(30), HwEv::P2 { dur: 12_000_000, atomic: false });
        sim.hw_at(ms(30) + fase * 125_000 + 7_000, HwEv::Inject { slot: 2, kind: Inj::Hang });
        sim.run_until(ms(120));
        let lost: u32 = sim.s.iter().map(|s| s.ring_lost).sum();
        if lost > peor { peor = lost; }
        if sim.s[2].tic.estado() == Estado::Muerta { muertas += 1 } else { vivas += 1 }
    }
    println!("   96 fases: eventos perdidos (peor caso) {} ; ranura 2 viva en {} y muerta en {}", peor, vivas, muertas);
}
