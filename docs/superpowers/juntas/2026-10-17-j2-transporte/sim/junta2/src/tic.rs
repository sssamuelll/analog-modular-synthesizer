use crate::esc::*;
use crate::motor::*;

/// Un tic tarde `delta_us` (secciones PRIMASK de la CPU antes del tic K): devuelve (plazos totales, primera ranura que vence).
pub fn un_tic_tarde(cfg: &Cfg, delta_ns: u64) -> (u32, Option<usize>) {
    let mut sim = Sim::new(cfg.clone());
    let k = 60u64;
    let t = k * PERIODO_NS;
    sim.hw_at(t - 500, HwEv::P2 { dur: delta_ns + 500, atomic: true });
    sim.run_until(t + 3_000_000);
    let total: u32 = sim.s.iter().map(|s| s.plazos).sum();
    let primera = sim.marks.iter().find(|m| m.what == "tic_vencida").map(|m| m.slot as usize);
    (total, primera)
}

pub fn delta_star(cfg: &Cfg) -> Option<(u64, usize, u32)> {
    let mut d = 1u64;
    while d <= 140 {
        let (tot, prim) = un_tic_tarde(cfg, d * 1000);
        if tot > 0 {
            return Some((d, prim.unwrap_or(99), tot));
        }
        d += 1;
    }
    None
}

pub fn t1() {
    println!("== T1: tic tarde delta (us) -> menor retraso que hace vencer ALGUNA ranura armada, seis ranuras, mensaje fijo ==");
    println!("   (plazo en tics sale de maestro_j2::plazo_us + transporte_j2::tics_de_plazo con el f_sck dado)");
    println!("   {:>9} {:>8} {:>6} {:>5} | {:>6} | {:>9} {:>11} {:>16}", "f_sck MHz", "bytes", "eps us", "frio", "tics", "delta* us", "1a ranura", "ranuras vencidas");
    let cases: &[(u64, u16)] = &[
        (6_250_000, 9), (6_250_000, 14), (6_250_000, 25), (6_250_000, 41), (6_250_000, 71), (6_250_000, 103),
        (8_000_000, 25), (8_000_000, 41), (8_000_000, 71), (8_000_000, 103),
    ];
    for &(f, b) in cases {
        for &(eps, cold) in &[(0u64, false), (1_500, false), (3_000, false), (6_000, false), (1_500, true)] {
            let mut cfg = Cfg::base();
            cfg.f_sck = f;
            cfg.msg = [b; N];
            cfg.eps_ns = eps;
            cfg.cold = cold;
            let probe = Sim::new(cfg.clone());
            let tics = probe.plazo_tics(b);
            match delta_star(&cfg) {
                Some((d, s, tot)) => println!("   {:>9.3} {:>8} {:>6.1} {:>5} | {:>6} | {:>9} {:>11} {:>16}", f as f64 / 1e6, b, eps as f64 / 1000.0, if cold { "si" } else { "no" }, tics, d, s, tot),
                None => println!("   {:>9.3} {:>8} {:>6.1} {:>5} | {:>6} | {:>9} {:>11} {:>16}", f as f64 / 1e6, b, eps as f64 / 1000.0, if cold { "si" } else { "no" }, tics, ">140", "-", 0),
            }
        }
    }
}

/// T2: la duracion del tic con seis ranuras armando, calida y fria, contra «<= 8,8 us».
pub fn t2() {
    println!("== T2: duracion del tic con las seis ranuras cerrando y armando (media del modelo, 100 ms) ==");
    for cold in [false, true] {
        let mut cfg = Cfg::base();
        cfg.cold = cold;
        let mut sim = Sim::new(cfg);
        sim.run_until(ms(100));
        println!("   caches {}: tic {:.2} us de media por periodo ({} tics)  -> aritmetica EN-PLACA: 6 x {} ciclos / 800 MHz = {:.2} us",
            if cold { "frias (D-cache desalojada)" } else { "calientes" },
            sim.busy[1] as f64 / sim.tics as f64 / 1000.0, sim.tics,
            if cold { 1528 } else { 1175 }, 6.0 * if cold { 1528.0 } else { 1175.0 } / 800.0);
    }
}

/// T3: seis SET de dieciseis coincidentes.
pub fn t3() {
    println!("== T3: SET16 (103 B) coincidentes en las seis ranuras (1 de cada 8 tramas), NADA 25 B el resto; 6,25 MHz; 300 ms ==");
    for (nombre, f) in [("SET16 1 de cada 8, las seis a la vez", (|_n, k| if k % 8 == 7 { 103u16 } else { 25u16 }) as fn(usize, u64) -> u16),
                        ("SET16 siempre en las seis", (|_n, _k| 103u16) as fn(usize, u64) -> u16)] {
        let mut cfg = Cfg::base();
        cfg.pat = Some(f);
        let mut sim = Sim::new(cfg);
        sim.run_until(ms(300));
        println!("  {nombre}");
        resumen(&sim, ms(300));
    }
}

pub fn resumen(sim: &Sim, t_ns: u64) {
    let tot = t_ns as f64;
    println!(
        "    CPU: tic {:.1}%  plan {:.1}%  rec {:.2}% | tics {} fus {} tard {} retraso_max {} us | preempciones {} | anillo_max_global {}",
        100.0 * sim.busy[1] as f64 / tot, 100.0 * sim.busy[3] as f64 / tot, 100.0 * sim.busy[4] as f64 / tot,
        sim.tics, sim.tics_fus, sim.tics_tard, sim.retraso_max_us, sim.preempt_count, sim.ring_hist_max
    );
    let plazos: Vec<u32> = sim.s.iter().map(|s| s.plazos).collect();
    let giros: Vec<u32> = sim.s.iter().map(|s| s.giros).collect();
    let sinb: Vec<u32> = sim.s.iter().map(|s| s.sin_bajada).collect();
    println!("    plazos {:?} giros {:?} sin_bajada {:?}", plazos, giros, sinb);
}

/// T4: tics tardios por encima de la holgura (delta = 100 us con NADA 25 B a 6,25 MHz) a una tasa r por segundo.
pub fn t4() {
    println!("== T4: un tic tarde de 100 us (por encima de los ~90 us de holgura de NADA a 6,25 MHz) r veces por segundo; seis ranuras; 2,5 s ==");
    for &r in &[1u64, 5, 9, 10, 12, 20] {
        let cfg = Cfg::base();
        let mut sim = Sim::new(cfg);
        let periodo_ms = 1000 / r;
        let mut t = ms(100);
        while t < ms(2400) {
            // alinear a un UEV
            let k = t / PERIODO_NS;
            let tk = k * PERIODO_NS;
            sim.hw_at(tk - 500, HwEv::P2 { dur: 100_000 + 500, atomic: true });
            t += ms(periodo_ms);
        }
        sim.run_until(ms(2500));
        let plazos: Vec<u32> = sim.s.iter().map(|s| s.plazos).collect();
        let inest: Vec<bool> = sim.s.iter().map(|s| s.pol.inestable()).collect();
        let rec: u32 = sim.s.iter().map(|s| s.recuperaciones).sum();
        let sells: u64 = 0;
        println!("   r = {:2}/s -> plazos por ranura {:?}  recuperaciones totales {}  inestable {:?}  retraso_max {} us  tics_tardios {} tics_fus {} escaladas {}",
            r, plazos, rec, inest.iter().map(|b| if *b {'S'} else {'n'}).collect::<String>(), sim.retraso_max_us, sim.tics_tard, sim.tics_fus, sim.escaladas);
    }
}

/// T5: el planificador (P3) no es preemptible por la recuperacion (P4) ni por el hilo; su coste por ranura no cuenta en los 2 500 ciclos.
pub fn t5() {
    println!("== T5: coste extra de componer la trama en el planificador (P3), por ranura y por periodo; seis ranuras; ranura 2 se cuelga ==");
    println!("   {:>10} {:>9} {:>9} | {:>14} {:>14} {:>12} | {:>8}", "extra us", "P1 %", "P3 %", "plan->corre us", "rec->corre us", "vencida->rec us", "ranura 2");
    for &x in &[0u64, 5, 10, 15, 17, 18, 19, 20, 25] {
        let mut cfg = Cfg::base();
        cfg.plan_extra_ns = x * 1000;
        let mut sim = Sim::new(cfg);
        sim.hw_at(ms(60), HwEv::Inject { slot: 2, kind: Inj::Hang });
        sim.run_until(ms(200));
        let tot = ms(200) as f64;
        let tv = first_after(&sim, "tic_vencida", 2, ms(60));
        let tr = first_after(&sim, "rec_inicio", 2, ms(60));
        let lat = match (tv, tr) { (Some(a), Some(b)) => format!("{:.0}", us(b - a)), _ => "-".into() };
        println!("   {:>10} {:>8.1}% {:>8.1}% | {:>14.1} {:>14.1} {:>12} | {:>8}",
            x, 100.0 * sim.busy[1] as f64 / tot, 100.0 * sim.busy[3] as f64 / tot,
            us(sim.plan_lat_max), us(sim.rec_lat_max), lat,
            match sim.s[2].tic.estado() { crate::transporte_j2::Estado::Muerta => "MUERTA".to_string(), e => format!("{:?}", e).chars().take(10).collect() });
    }
}

/// T6: sin ningun fallo, la recuperacion es preemptible por todo menos por el nivel 4; ¿un P2 que cae justo despues de SUSP escala por nada?
pub fn t6() {
    println!("== T6: un P2 de D us cae justo tras escribir SUSP en una recuperacion NORMAL (SPI envenenado, canal sano): ¿escala por nada? ==");
    for &d in &[10u64, 30, 100, 1000, 5000] {
        let mut cfg = Cfg::base();
        cfg.active = [true, false, false, false, false, false];
        let mut sim = Sim::new(cfg);
        sim.hw_at(ms(20), HwEv::Inject { slot: 0, kind: Inj::Hang });
        sim.hw_at(ms(20) + 125_000 + 700 + (cy(100) + cy(100)), HwEv::P2 { dur: d * 1000, atomic: false });
        sim.run_until(ms(60));
        println!("   P2 de {:5} us -> escaladas {} recuperaciones {} ranura {:?}", d, sim.escaladas, sim.s[0].recuperaciones, sim.s[0].tic.estado());
    }
}

/// T7: lo que ve el modulo cuando un tic llega tarde por encima de la holgura.
pub fn t7() {
    println!("== T7: un tic tarde delta us (NADA 25 B, 6,25 MHz, seis ranuras): plazos, recuperaciones y hueco entre tramas validas que ve cada modulo ==");
    for &d in &[80u64, 90, 95, 100, 110, 120] {
        let cfg = Cfg::base();
        let mut sim = Sim::new(cfg);
        let t = 60 * PERIODO_NS;
        sim.hw_at(t - 500, HwEv::P2 { dur: d * 1000 + 500, atomic: true });
        sim.run_until(t + 3_000_000);
        let plazos: u32 = sim.s.iter().map(|s| s.plazos).sum();
        let rec: u32 = sim.s.iter().map(|s| s.recuperaciones).sum();
        let gaps: Vec<String> = sim.s.iter().map(|s| format!("{:.0}", us(s.max_gap))).collect();
        println!("   delta {:3} us -> plazos {} recuperaciones {} ; hueco max por modulo (us) {:?} ; tics_fus {} fundidos_reales {}", d, plazos, rec, gaps, sim.tics_fus, sim.uev_merged);
    }
}
