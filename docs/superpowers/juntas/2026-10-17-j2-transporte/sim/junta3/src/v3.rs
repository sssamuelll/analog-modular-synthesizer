//! Tercera pasada: los mecanismos nuevos del papel v3 absorbido (commit 4c639f0), sobre la maquina real.
use crate::esc::*;
use crate::motor::*;
use crate::transporte_j2::Estado;

fn muertas(sim: &Sim) -> u32 {
    sim.s.iter().map(|s| s.muertas).sum()
}

fn ms_opt(t: Option<u64>, t0: u64) -> String {
    match t {
        Some(t) if t >= t0 => format!("{:.3}", us(t - t0) / 1000.0),
        _ => "-".into(),
    }
}

pub fn linea(sim: &Sim, t0: u64) {
    for n in 0..N {
        let s = &sim.s[n];
        if !s.on {
            continue;
        }
        println!(
            "     r{n}: propios {:3} ajenos {:3} rec {:3} deneg {} muerta {} arma_sin_programa {} hecha_rancia {} giros {:6} hueco_modulo_max {:8.1} us {:?}",
            s.plazos, s.ajenos, s.recuperaciones, s.denegadas, s.muertas, s.arm_sin_prog, s.hecho_rancio, s.giros, us(s.max_gap), s.tic.estado()
        );
    }
    let esc = all(sim, "escalada", -1);
    println!(
        "     escaladas {} (ms: {:?}) denegadas {} concurrentes_max {} | latencia max del hilo {:.2} ms | supervisor deja de alimentar {} ms | IWDG {} ms",
        sim.escaladas,
        esc.iter().take(8).map(|t| ((*t as f64 - t0 as f64) / 1e3).round() / 1e3).collect::<Vec<_>>(),
        sim.denegadas,
        sim.max_concurrent_esc,
        sim.feed_lat_max as f64 / 1e6,
        ms_opt(sim.first_refusal, t0),
        ms_opt(sim.iwdg_reset_at, t0)
    );
}

pub fn cota() {
    println!("== V3-COTA: tic_cota con las cotas del papel (Vencida 200 tics = 25 ms, Reiniciando 100 = 12,5 ms), una ranura ==");
    for &d in &[24_000u64, 24_800, 25_000, 25_200, 26_000] {
        let mut cfg = Cfg::base();
        cfg.active = [true, false, false, false, false, false];
        let mut sim = Sim::new(cfg);
        sim.hold_on_vencida = Some((0, vec![vec![(d * 1000, false)]]));
        sim.hw_at(ms(20), HwEv::Inject { slot: 0, kind: Inj::Hang });
        sim.run_until(ms(120));
        println!("   P2 de {:6} us al vencer -> {:?}", d, sim.s[0].tic.estado());
    }
    for &d in &[12_000u64, 12_400, 12_600, 13_000] {
        let mut cfg = Cfg::base();
        cfg.active = [true, false, false, false, false, false];
        let mut sim = Sim::new(cfg);
        sim.hold_on_rec = Some((0, vec![vec![(d * 1000, false)]]));
        sim.hw_at(ms(20), HwEv::Inject { slot: 0, kind: Inj::Hang });
        sim.run_until(ms(120));
        println!("   P2 de {:6} us al arrancar la recuperacion -> {:?}", d, sim.s[0].tic.estado());
    }
}

pub fn a4() {
    println!("== V3-A4: canal que el reset NO cura (ranura 2), seis ranuras, permiso de la politica (umbral 3), supervisor R-H8 ventana 45 ms / P_s 5 ms / IWDG 60 ms ==");
    for retry in [Retry::CadaTic, Retry::EnSitio] {
        let mut cfg = Cfg::base();
        cfg.retry = retry;
        let mut sim = Sim::new(cfg);
        sim.hw_at(ms(50), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: true } });
        sim.run_until(ms(300));
        let t0 = first(&sim, "cstart_veneno", 2).unwrap();
        let td = first(&sim, "escalada_DENEGADA", 2);
        let tm = first(&sim, "muerta", 2);
        println!("  reintento {:?}: desde el CSTART atascado: denegada {} ms, Muerta {} ms, modulo 2 suelta {:.3} ms",
            retry, ms_opt(td, t0), ms_opt(tm, t0), us(sim.s[2].last_valid + 50_000_000 - t0) / 1000.0);
        if let (Some(a), Some(b)) = (td, tm) {
            println!("     CPU de P4 en todo el ensayo {:.3} ms, sobre {:.3} ms de pared de denegacion = {:.1} %",
                sim.busy[4] as f64 / 1e6, (b - a) as f64 / 1e6, 100.0 * sim.busy[4] as f64 / (b - a) as f64);
        }
        linea(&sim, t0);
    }
}

pub fn a4x2() {
    println!("== V3-A4x2: dos canales que el reset NO cura (ranuras 1 y 4, mismo tic) y un cuelgue ordinario en la ranura 5 a +1 ms ==");
    for retry in [Retry::CadaTic, Retry::EnSitio] {
        let mut cfg = Cfg::base();
        cfg.retry = retry;
        let mut sim = Sim::new(cfg);
        sim.hw_at(ms(50), HwEv::Inject { slot: 1, kind: Inj::Stuck { persistente: true } });
        sim.hw_at(ms(50), HwEv::Inject { slot: 4, kind: Inj::Stuck { persistente: true } });
        sim.hw_at(ms(51), HwEv::Inject { slot: 5, kind: Inj::Hang });
        sim.run_until(ms(300));
        let t0 = first(&sim, "cstart_veneno", -1).unwrap();
        println!("  reintento {:?}: Muerta r1 {} ms, r4 {} ms, r5 {} ms; latencia max de la recuperacion {:.3} ms",
            retry, ms_opt(first(&sim, "muerta", 1), t0), ms_opt(first(&sim, "muerta", 4), t0), ms_opt(first(&sim, "muerta", 5), t0), sim.rec_lat_max as f64 / 1e6);
        linea(&sim, t0);
    }
}

pub fn a5() {
    println!("== V3-A5: bloqueo TRANSITORIO comun del GPDMA1 de D us (las transferencias en vuelo no paran mientras dura), fases 0..125 us ==");
    for retry in [Retry::CadaTic, Retry::EnSitio] {
        println!("  reintento {:?}", retry);
        for &d in &[100u64, 270, 400, 1_000, 2_000, 5_000, 10_000, 12_000, 13_000, 14_000, 20_000] {
            let (mut esc, mut den, mut mu, mut rs, mut hilo, mut p4) = (0u32, 0u32, 0u32, 0u32, 0f64, 0f64);
            for fase in (0..125u64).step_by(25) {
                let mut cfg = Cfg::base();
                cfg.retry = retry;
                let mut sim = Sim::new(cfg);
                let t_ini = ms(50) + fase * 1000 + 10_000;
                sim.hw_at(t_ini, HwEv::StallStart { until: t_ini + d * 1000 });
                sim.run_until(ms(250));
                esc = esc.max(sim.escaladas);
                den = den.max(sim.denegadas);
                mu = mu.max(muertas(&sim));
                if sim.iwdg_reset_at.is_some() { rs += 1; }
                hilo = hilo.max(sim.feed_lat_max as f64 / 1e6);
                p4 = p4.max(sim.busy[4] as f64 / 1e6);
            }
            println!("   D = {:6} us -> escaladas max {:2} denegadas max {} ranuras_muertas max {} reinicios {}/5 | hilo sin correr max {:.2} ms | CPU de P4 max {:.2} ms",
                d, esc, den, mu, rs, hilo, p4);
        }
    }
}

pub fn c1() {
    println!("== V3-C1: ISR de P2 encadenadas al vencer la ranura 2 (cotas 25 + 12,5 ms; R-H1 pide ventana <= 12 ms) ==");
    for &(d_us, ks) in &[(1000u64, &[12u64, 24, 25, 26][..]), (5000, &[4, 5, 6][..])] {
        for &k in ks {
            let cfg = Cfg::base();
            let mut sim = Sim::new(cfg);
            let jobs: Vec<Vec<(u64, bool)>> = (0..k).map(|_| vec![(d_us * 1000, false)]).collect();
            sim.hold_on_vencida = Some((2, jobs));
            sim.hw_at(ms(30), HwEv::Inject { slot: 2, kind: Inj::Hang });
            sim.run_until(ms(250));
            let t0 = first(&sim, "cstart_veneno", 2).unwrap();
            println!("   {:3} x {:5} us ({:6.1} ms) -> ranura 2 {:?}  Muerta {} ms  IWDG {} ms  hueco del modulo {:.1} ms",
                k, d_us, (k * d_us) as f64 / 1000.0, sim.s[2].tic.estado(), ms_opt(first(&sim, "muerta", 2), t0), ms_opt(sim.iwdg_reset_at, t0), us(sim.s[2].max_gap) / 1000.0);
        }
    }
}

pub fn c2() {
    println!("== V3-C2: retencion de P2 de 120 ms hecha de [400 us abierto + L us PRIMASK], ranura 2 colgada; cota Vencida 200 tics (25 ms nominal) ==");
    println!("   {:>6} | {:>14} {:>14} | {:>16}", "L us", "sin reconstr.", "reconstruido", "periodos_saltados");
    for &l in &[0u64, 60, 70, 90, 110, 130, 200, 300, 500, 1000] {
        let mut res = Vec::new();
        let mut salt = 0;
        for recon in [false, true] {
            let mut cfg = Cfg::base();
            cfg.recon = recon;
            let mut sim = Sim::new(cfg);
            let mut seq: Vec<(u64, bool)> = Vec::new();
            let mut t = 0u64;
            while t < 120_000 {
                seq.push((400_000, false));
                if l > 0 {
                    seq.push((l * 1000, true));
                }
                t += 400 + l;
            }
            sim.hold_on_vencida = Some((2, vec![seq]));
            sim.hw_at(ms(30), HwEv::Inject { slot: 2, kind: Inj::Hang });
            sim.run_until(ms(200));
            let tv = first(&sim, "tic_vencida", 2);
            let tm = first(&sim, "muerta", 2);
            res.push(match (tv, tm) { (Some(a), Some(b)) => format!("{:.2} ms", (b - a) as f64 / 1e6), _ => "VIVA".into() });
            if recon { salt = sim.periodos_saltados; }
        }
        println!("   {:>6} | {:>14} {:>14} | {:>16}", l, res[0], res[1], salt);
    }
}

fn p0_cada(sim: &mut Sim, desde: u64, hasta: u64, cada: u64, delta_us: u64) {
    let mut k = desde / PERIODO_NS + 1;
    while k * PERIODO_NS < hasta {
        sim.hw_at(k * PERIODO_NS - 100, HwEv::P0 { dur: delta_us * 1000 + 100 });
        k += cada;
    }
}

pub fn late() {
    println!("== V3-LATE (a): tics retrasados delta us por una ISR por encima del tic (P0), uno de cada K, 1 s, sin fallos; 8 000 periodos reales ==");
    println!("   {:>3} {:>6} | {:>9} {:>8} {:>10} {:>8} {:>8}", "K", "delta", "periodos", "x pared", "saltados", "plazos", "fusion.");
    for &cada in &[2u64, 4] {
        for &d in &[40u64, 60, 63, 70, 80, 100, 124, 130, 200] {
            let cfg = Cfg::base();
            let mut sim = Sim::new(cfg);
            p0_cada(&mut sim, ms(10), ms(1010), cada, d);
            sim.run_until(ms(10) + 1000);
            let a = sim.tics;
            sim.run_until(ms(1010) + 1000);
            let b = sim.tics;
            let plazos: u32 = sim.s.iter().map(|s| s.plazos).sum();
            println!("   {:>3} {:>6} | {:>9} {:>8.3} {:>10} {:>8} {:>8}", cada, d, b - a, (b - a) as f64 / 8000.0, sim.periodos_saltados, plazos, sim.tics_fus);
        }
    }
    println!("== V3-LATE (b): ranura 2 colgada, planificador y recuperacion retenidos 120 ms por P2; tics retrasados delta us uno de cada 2. Cota Vencida 25 ms ==");
    for &d in &[0u64, 60, 63, 70, 100, 124, 130, 200] {
        let cfg = Cfg::base();
        let mut sim = Sim::new(cfg);
        sim.hold_on_vencida = Some((2, vec![vec![(120_000_000, false)]]));
        sim.hw_at(ms(30), HwEv::Inject { slot: 2, kind: Inj::Hang });
        if d > 0 {
            p0_cada(&mut sim, ms(30) + 200_000, ms(170), 2, d);
        }
        sim.run_until(ms(200));
        let tv = first(&sim, "tic_vencida", 2);
        let tm = first(&sim, "muerta", 2);
        println!("   delta {:4} us -> de Vencida a Muerta {} ms de pared (nominal 25,0)", d,
            match (tv, tm) { (Some(a), Some(b)) => format!("{:.2}", (b - a) as f64 / 1e6), _ => "VIVA".into() });
    }
}

pub fn perm() {
    println!("== V3-PERM: K tics tardios de 110 us (P0) separados 100 ms y, a 600 ms, un canal atascado que el reset del GPDMA1 SI cura (ranura 2) ==");
    for &k in &[0usize, 3, 4] {
        let cfg = Cfg::base();
        let mut sim = Sim::new(cfg);
        for i in 0..k {
            let t = ms(50 + 100 * i as u64);
            let kk = t / PERIODO_NS;
            sim.hw_at(kk * PERIODO_NS - 100, HwEv::P0 { dur: 110_100 });
        }
        sim.hw_at(ms(600), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: false } });
        sim.run_until(ms(800));
        let t0 = first(&sim, "cstart_veneno", 2).unwrap();
        let antes = all(&sim, "tic_vencida", 2).iter().filter(|t| **t < t0).count();
        println!("  K = {k}: plazos propios de la ranura 2 antes del atasco {antes}; ranura 2 queda {:?}; denegada {} ms, Muerta {} ms desde el CSTART atascado", sim.s[2].tic.estado(), ms_opt(first(&sim, "escalada_DENEGADA", 2), t0), ms_opt(first(&sim, "muerta", 2), t0));
        linea(&sim, t0);
    }
}

pub fn sucia() {
    println!("== V3-SUCIA: cuelgue ordinario en r4 y canal atascado curable en r5 en el mismo tic; P2 retiene D us al vencer (desplaza la escalada respecto al tic) ==");
    for todo in [false, true] {
        let mut casos = Vec::new();
        let mut abort = 0;
        for d in 0..130u64 {
            let mut cfg = Cfg::base();
            cfg.sucia_todo = todo;
            let mut sim = Sim::new(cfg);
            sim.hold_on_vencida = Some((4, vec![vec![(d * 1000, false)]]));
            sim.hw_at(ms(50), HwEv::Inject { slot: 4, kind: Inj::Hang });
            sim.hw_at(ms(50), HwEv::Inject { slot: 5, kind: Inj::Stuck { persistente: false } });
            sim.run_until(ms(80));
            let a: u32 = sim.s.iter().map(|s| s.arm_sin_prog).sum();
            if a > 0 {
                casos.push(d);
                abort += all(&sim, "programa_aborta_en_vuelo", -1).len();
                if casos.len() == 1 {
                    println!("   primer caso D = {d} us:");
                    linea(&sim, ms(50));
                }
            }
        }
        println!("  {}: armados sobre un canal sin programar en {} de 130 desfases (D = {:?}); transferencias que programa() aborto en vuelo {}",
            if todo { "SUCIA bloquea armar en todo estado" } else { "tabla de 2.2 literal (SUCIA solo en Vencida)" }, casos.len(), casos, abort);
    }
}

pub fn ident() {
    println!("== V3-IDENT: la ranura 3 (HOLA 9 B) pierde la identidad a fase F tras un tic; vuelve a 70 ms; a 110 ms se cuelga con P2 de 300 us al vencer ==");
    let (mut rancias, mut banderas, mut casos) = (0, 0, 0);
    for f in (0..125u64).step_by(5) {
        let mut cfg = Cfg::base();
        cfg.msg = [25, 25, 25, 9, 25, 25];
        let mut sim = Sim::new(cfg);
        let t = ms(50) + f * 1000;
        sim.hw_at(t, HwEv::Ident { slot: 3, present: false });
        sim.run_until(ms(65));
        let s = &sim.s[3];
        let colgadas = (s.rec_hecha || s.rec_en_curso) && !matches!(s.tic.estado(), Estado::Vencida { .. } | Estado::Reiniciando { .. });
        if colgadas { banderas += 1; }
        sim.hw_at(ms(70), HwEv::Ident { slot: 3, present: true });
        sim.hold_on_vencida = Some((3, vec![vec![(300_000, false)]]));
        sim.hw_at(ms(110), HwEv::Inject { slot: 3, kind: Inj::Hang });
        sim.run_until(ms(200));
        let s = &sim.s[3];
        rancias += s.hecho_rancio;
        casos += 1;
        if f == 0 || (s.hecho_rancio > 0 && rancias == s.hecho_rancio) {
            println!("   F = {f} us: banderas REC colgadas tras la limpieza = {colgadas}; despues del cuelgue:");
            linea(&sim, ms(50));
        }
    }
    println!("  {casos} fases: limpiezas que dejan REC_HECHA/REC_EN_CURSO puestas con la ranura fuera de la recuperacion: {banderas}; rearmes por una HECHA rancia: {rancias}");
}

pub fn fuzz(seeds: u64, t_s: u64, lh: f64, ls: f64, lp: f64, ll: f64, f: u64, retry: Retry) {
    println!("== V3-FUZZ {seeds} x {t_s} s a {} MHz, reintento {:?}: cuelgues {lh}/s, atascos curables {ls}/s, P2 {lp}/s (20 us..6 ms), tics tardios {ll}/s (0..120 us) ==", f as f64 / 1e6, retry);
    let (mut pl, mut aj, mut rec, mut esc, mut den, mut mu, mut rs, mut asp, mut ran, mut viol) = (0u64, 0u64, 0u64, 0u64, 0u64, 0u64, 0u64, 0u64, 0u64, 0u64);
    let (mut hilo, mut planl, mut conc, mut salt) = (0u64, 0u64, 0u32, 0u64);
    for seed in 1..=seeds {
        let (mut sim, t_fin, _inj) = crate::fuzz::montar_con(seed, t_s, lh, ls, lp, ll, f, &|c: &mut Cfg| { c.retry = retry; });
        sim.run_until(t_fin + ms(40));
        let mut mal = Vec::new();
        for n in 0..N {
            let s = &sim.s[n];
            let viva = s.tic.estado() != Estado::Muerta;
            if s.pol.plazos_vencidos() != s.plazos { mal.push(format!("r{n} politica {} tic {}", s.pol.plazos_vencidos(), s.plazos)); }
            if viva && matches!(s.tic.estado(), Estado::Vencida { .. } | Estado::Reiniciando { .. }) { mal.push(format!("r{n} quieta en {:?}", s.tic.estado())); }
            if s.ring_lost != 0 { mal.push(format!("r{n} anillo perdio {}", s.ring_lost)); }
            if !viva { mu += 1; }
            pl += s.plazos as u64; aj += s.ajenos as u64; rec += s.recuperaciones as u64;
            asp += s.arm_sin_prog as u64; ran += s.hecho_rancio as u64;
        }
        esc += sim.escaladas as u64; den += sim.denegadas as u64;
        if sim.iwdg_reset_at.is_some() { rs += 1; }
        hilo = hilo.max(sim.feed_lat_max); planl = planl.max(sim.plan_lat_max); conc = conc.max(sim.max_concurrent_esc);
        salt += sim.periodos_saltados;
        if !mal.is_empty() { viol += 1; if viol <= 3 { println!("   semilla {seed}: {:?}", &mal[..mal.len().min(3)]); } }
    }
    println!("   plazos propios {pl} ajenos {aj} recuperaciones {rec} | escaladas {esc} denegadas {den} concurrentes_max {conc} | ranuras muertas {mu} reinicios del chip {rs}/{seeds}");
    println!("   armados sobre canal sin programar {asp} | rearmes con HECHA rancia {ran} | periodos saltados {salt} | semillas con violacion {viol} | hilo sin correr max {:.2} ms | planificador sin correr max {:.2} ms", hilo as f64 / 1e6, planl as f64 / 1e6);
}

pub fn run(x: &str) {
    match x {
        "v3cota" => cota(),
        "v3a4" => a4(),
        "v3a4x2" => a4x2(),
        "v3a5" => a5(),
        "v3c1" => c1(),
        "v3c2" => c2(),
        "v3late" => late(),
        "v3perm" => perm(),
        "v3sucia" => sucia(),
        "v3ident" => ident(),
        "v3dbgident" => dbg_ident(),
        "v3ident2" => ident2(),
        "v3sucia2" => sucia2(),
        "v3a8" => a8(),
        "v3fuzz" => {
            fuzz(30, 4, 15.0, 0.8, 30.0, 5.0, 6_250_000, Retry::CadaTic);
            fuzz(30, 4, 15.0, 0.8, 30.0, 5.0, 6_250_000, Retry::EnSitio);
        }
        "v3fuzzx" => {
            let a: Vec<f64> = std::env::args().skip(2).map(|x| x.parse().unwrap()).collect();
            let r = if a[7] > 0.5 { Retry::EnSitio } else { Retry::CadaTic };
            fuzz(a[0] as u64, a[1] as u64, a[2], a[3], a[4], a[5], a[6] as u64, r);
        }
        _ => println!("?"),
    }
}

pub fn dbg_ident() {
    let mut cfg = Cfg::base();
    cfg.msg = [25, 25, 25, 9, 25, 25];
    let mut sim = Sim::new(cfg);
    sim.hw_at(ms(50), HwEv::Ident { slot: 3, present: false });
    sim.hw_at(ms(70), HwEv::Ident { slot: 3, present: true });
    sim.hold_on_vencida = Some((3, vec![vec![(300_000, false)]]));
    sim.hw_at(ms(110), HwEv::Inject { slot: 3, kind: Inj::Hang });
    sim.run_until(ms(52));
    let s = &sim.s[3];
    println!("a 52 ms: {:?} hecha {} en_curso {} t_hecha {:.3} ms t_venc {:.3}", s.tic.estado(), s.rec_hecha, s.rec_en_curso, s.rec_t_hecha as f64 / 1e6, s.t_venc as f64 / 1e6);
    sim.run_until(ms(112));
    for m in sim.marks.iter().filter(|m| m.slot == 3 || m.slot == -1) {
        println!("   t={:.4} ms {} {}", m.t as f64 / 1e6, m.what, m.x);
    }
}

pub fn ident2() {
    println!("== V3-IDENT2: r3 (HOLA 9 B) pierde la identidad; el planificador la procesa tras el tic de 50,000 ms y una ISR de P2 de D us entra a 50,012 ms (retrasa P4). Vuelve a 70 ms; a 110 ms un cuelgue con P2 de 300 us al vencer ==");
    for &(d, ini) in &[(0u64, 12_000u64), (150, 12_000), (150, 13_000), (150, 14_000), (150, 15_000), (150, 16_000), (150, 17_000), (150, 18_000), (150, 20_000), (400, 15_000)] {
        let mut cfg = Cfg::base();
        cfg.msg = [25, 25, 25, 9, 25, 25];
        let mut sim = Sim::new(cfg);
        sim.hw_at(ms(50) - 1_000, HwEv::Ident { slot: 3, present: false });
        if d > 0 {
            sim.hw_at(ms(50) + ini, HwEv::P2 { dur: d * 1000, atomic: false });
        }
        sim.run_until(ms(65));
        let s = &sim.s[3];
        let (h, c, e) = (s.rec_hecha, s.rec_en_curso, s.tic.estado());
        let p_antes = s.plazos;
        sim.hw_at(ms(70), HwEv::Ident { slot: 3, present: true });
        sim.run_until(ms(100));
        sim.hold_on_vencida = Some((3, vec![vec![(300_000, false)]]));
        sim.hw_at(ms(110), HwEv::Inject { slot: 3, kind: Inj::Hang });
        sim.run_until(ms(150));
        let s = &sim.s[3];
        let rearmes = all(&sim, "HECHA_RANCIA_rearma", 3).iter().filter(|t| **t > ms(100)).count();
        let arm_rancio: Vec<f64> = all(&sim, "HECHA_RANCIA_rearma", 3).iter().filter(|t| **t > ms(100)).map(|t| *t as f64 / 1e6).collect();
        println!("   P2 de {:4} us a 50,0{:02} ms: a 65 ms {:?} REC_HECHA {} REC_EN_CURSO {} | cuelgue de 110 ms: plazos propios {} (1 esperado), rearmes con HECHA rancia {} {:?}",
            d, ini / 1000, e, h, c, s.plazos - p_antes, rearmes, arm_rancio);
    }
}

pub fn sucia2() {
    println!("== V3-SUCIA2: canal atascado curable en r5; P2 retiene D us desde 50,130 ms (planificador sin correr: r0..r4 quedan Libre sin bajada); al acabar, el planificador compone y P4 escala ==");
    for todo in [false, true] {
        let mut casos = Vec::new();
        let mut propios_extra = 0u32;
        let mut ejemplo = None;
        for d in 500..626u64 {
            let mut cfg = Cfg::base();
            cfg.sucia_todo = todo;
            let mut sim = Sim::new(cfg);
            sim.hw_at(ms(50), HwEv::Inject { slot: 5, kind: Inj::Stuck { persistente: false } });
            sim.hw_at(ms(50) + 130_000, HwEv::P2 { dur: d * 1000, atomic: false });
            sim.run_until(ms(70));
            let a: u32 = sim.s.iter().map(|s| s.arm_sin_prog).sum();
            if a > 0 {
                casos.push(d);
                propios_extra += sim.s[..5].iter().map(|s| s.plazos).sum::<u32>();
                if ejemplo.is_none() {
                    ejemplo = Some(d);
                    println!("   primer caso D = {d} us; marcas:");
                    for m in sim.marks.iter().filter(|m| m.what == "ARMA_SIN_PROGRAMA" || m.what == "programa_aborta_en_vuelo" || m.what == "escalada" || m.what == "tic_vencida") {
                        println!("      t={:.4} ms r{} {}", m.t as f64 / 1e6, m.slot, m.what);
                    }
                    linea(&sim, ms(50));
                }
            }
        }
        println!("  {}: armados sobre canal sin programar en {} de 126 desfases {:?}; plazos PROPIOS de r0..r4 en esos casos: {}",
            if todo { "SUCIA bloquea armar en todo estado" } else { "tabla de 2.2 literal (SUCIA solo en Vencida)" }, casos.len(), casos, propios_extra);
    }
}

pub fn a8() {
    println!("== V3-A8: escalada (atasco curable en r2) y retencion de P2 de D ms justo tras la seccion critica, mientras escala() reprograma ==");
    for &d in &[5u64, 14, 30, 100] {
        let cfg = Cfg::base();
        let mut sim = Sim::new(cfg);
        sim.hold_on_escalada = Some(vec![vec![(d * 1_000_000, false)]]);
        sim.hw_at(ms(50), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: false } });
        sim.run_until(ms(50) + ms(d) / 2);
        let mitad: Vec<String> = sim.s.iter().map(|s| format!("{}{:?}", if s.sucia { "S:" } else { "" }, s.tic.estado())).collect();
        sim.run_until(ms(50 + d + 150));
        let t0 = first(&sim, "cstart_veneno", 2).unwrap();
        println!("   D = {d:3} ms: a mitad de la retencion {:?}", mitad);
        println!("            al final: muertas {} (Muerta a {} ms), IWDG {} ms", muertas(&sim), ms_opt(first(&sim, "muerta", -1), t0), ms_opt(sim.iwdg_reset_at, t0));
    }
}
