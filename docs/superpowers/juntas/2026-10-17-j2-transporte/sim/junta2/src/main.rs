#![allow(dead_code, unused_variables, unused_mut, unused_imports)]
mod buzones_j2;
mod esc;
mod fuzz;
mod cot;
mod tic;
mod maestro_j2;
mod motor;
mod transporte_j2;

use motor::*;
use transporte_j2::Estado;

fn us(ns: u64) -> f64 {
    ns as f64 / 1000.0
}

fn ms(x: u64) -> u64 {
    x * 1_000_000
}

fn us_to_ns(x: u64) -> u64 {
    x * 1000
}

fn first(sim: &Sim, what: &str, slot: i32) -> Option<u64> {
    sim.marks.iter().find(|m| m.what == what && (slot < 0 || m.slot == slot)).map(|m| m.t)
}

fn first_after(sim: &Sim, what: &str, slot: i32, t: u64) -> Option<u64> {
    sim.marks.iter().find(|m| m.what == what && (slot < 0 || m.slot == slot) && m.t >= t).map(|m| m.t)
}

fn resumen_basico(sim: &Sim, t_ns: u64) {
    let tot = t_ns as f64;
    println!(
        "  CPU: tic {:.1}%  p2 {:.1}%  plan {:.1}%  rec {:.2}%  | tics {} fus {} tard {} retraso_max {} us | uev_fundidos {} | preempciones {}",
        100.0 * sim.busy[1] as f64 / tot,
        100.0 * sim.busy[2] as f64 / tot,
        100.0 * sim.busy[3] as f64 / tot,
        100.0 * sim.busy[4] as f64 / tot,
        sim.tics, sim.tics_fus, sim.tics_tard, sim.retraso_max_us, sim.uev_merged, sim.preempt_count
    );
    for n in 0..N {
        let s = &sim.s[n];
        if !s.on {
            continue;
        }
        println!(
            "  ranura {}: giros {:5} plazos {:3} colat {:3} rec {:3} muertas {} sin_bajada {:4} anillo_max {} anillo_perdidos {} estado {:?}",
            n, s.giros, s.plazos, s.colateral, s.recuperaciones, s.muertas, s.sin_bajada, s.ring_max, s.ring_lost, s.tic.estado()
        );
    }
}

fn autocheck() {
    println!("== AUTOCHECK 1: seis ranuras, NADA 25 B a 6,25 MHz, 400 ms, sin fallos ==");
    let cfg = Cfg::base();
    let mut sim = Sim::new(cfg);
    sim.run_until(ms(400));
    resumen_basico(&sim, ms(400));
    let tics = sim.tics;
    for n in 0..N {
        assert_eq!(sim.s[n].plazos, 0, "plazos en ranura {n}");
        assert_eq!(sim.s[n].ring_lost, 0);
        assert!(sim.s[n].giros >= tics - 3, "giros {} vs tics {}", sim.s[n].giros, tics);
    }
    assert_eq!(sim.tics_fus, 0);
    assert_eq!(sim.escaladas, 0);
    assert!(sim.iwdg_reset_at.is_none());
    // ciclos por giro y ranura medidos por la CPU del modelo: (tic + plan) / (tics * 6)
    let ns_giro = (sim.busy[1] + sim.busy[3]) as f64 / (sim.tics as f64 * 6.0);
    println!("  coste del enlace por giro y ranura en el modelo: {:.0} ciclos (EN-PLACA: 1967 enlace solo, 2100 con compositor de mentira)", ns_giro * 0.8);
}

fn main() {
    let arg = std::env::args().nth(1).unwrap_or_default();
    match arg.as_str() {
        "auto" | "" => autocheck(),
        "a2" => esc::a2_a3(),
        "fuzzx" => {
            let a: Vec<f64> = std::env::args().skip(2).map(|x| x.parse().unwrap()).collect();
            fuzz::fuzz(a[0] as u64, a[1] as u64, a[2], a[3], a[4], a[5], a[6] as u64);
        }
        "dbg12" => fuzz::dbg12(),
        "fuzz" => fuzz::fuzz(30, 4, 15.0, 0.0, 30.0, 5.0, 6_250_000),
        "fuzz2" => fuzz::fuzz(30, 4, 15.0, 0.8, 30.0, 5.0, 6_250_000),
        "c1" => cot::c1(),
        "c2" => cot::c2(),
        "c3" => cot::c3(),
        "t1" => tic::t1(),
        "t2" => tic::t2(),
        "t3" => tic::t3(),
        "t4" => tic::t4(),
        "t5" => tic::t5(),
        "t6" => tic::t6(),
        "t7" => tic::t7(),
        "a4" => esc::a4(),
        "a5" => esc::a5(),
        "a5b" => esc::a5b(),
        "a6" => esc::a6(),
        "a7" => esc::a7(),
        "a8" => esc::a8(),
        "a9" => esc::a9(),
        "calib" => { esc::calib_hang(); esc::calib_cota(); }
        _ => {}
    }
}
