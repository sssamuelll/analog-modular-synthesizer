use crate::motor::*;
use crate::transporte_j2::Estado;

pub fn us(ns: u64) -> f64 {
    ns as f64 / 1000.0
}
pub fn ms(x: u64) -> u64 {
    x * 1_000_000
}
pub fn first(sim: &Sim, what: &str, slot: i32) -> Option<u64> {
    sim.marks.iter().find(|m| m.what == what && (slot < 0 || m.slot == slot)).map(|m| m.t)
}
pub fn first_after(sim: &Sim, what: &str, slot: i32, t: u64) -> Option<u64> {
    sim.marks.iter().find(|m| m.what == what && (slot < 0 || m.slot == slot) && m.t >= t).map(|m| m.t)
}
pub fn all(sim: &Sim, what: &str, slot: i32) -> Vec<u64> {
    sim.marks.iter().filter(|m| m.what == what && (slot < 0 || m.slot == slot)).map(|m| m.t).collect()
}
pub fn rel(t: Option<u64>, t0: u64) -> String {
    match t {
        Some(t) => format!("{:9.1}", us(t - t0)),
        None => "        -".to_string(),
    }
}

/// Calibracion contra `tic_recupera` fase A (una ranura, SPI envenenado): 123 / 125 / 126 / 127 / 131 / 249 us.
pub fn calib_hang() {
    println!("== CALIBRACION: un SPI envenenado, una ranura (EN-PLACA: vencida 123, rec 125, reset SPI 126, configurado 127, HECHA 131, siguiente CSTART 249 us desde el CSTART envenenado) ==");
    let mut cfg = Cfg::base();
    cfg.active = [true, false, false, false, false, false];
    let mut sim = Sim::new(cfg);
    sim.trace_arm = Some(0);
    sim.hw_at(ms(20), HwEv::Inject { slot: 0, kind: Inj::Hang });
    sim.run_until(ms(30));
    let t0 = first(&sim, "cstart_veneno", 0).unwrap();
    println!("  desde CSTART veneno (us): vencida {}  plan_pide {}  rec_inicio {}  spi_reset {}  rec_hecha {}  siguiente_cstart {}",
        rel(first_after(&sim, "tic_vencida", 0, t0), t0),
        rel(first_after(&sim, "plan_pide_rec", 0, t0), t0),
        rel(first_after(&sim, "rec_inicio", 0, t0), t0),
        rel(first_after(&sim, "spi_reset", 0, t0), t0),
        rel(first_after(&sim, "rec_hecha", 0, t0), t0),
        rel(sim.marks.iter().filter(|m| m.what == "cstart" && m.t > t0).map(|m| m.t).next(), t0));
    println!("  plazos {} recuperaciones {} muertas {}", sim.s[0].plazos, sim.s[0].recuperaciones, sim.s[0].muertas);
}

/// Calibracion contra `tic_cota`: P2 retiene D us justo cuando el tic da por vencida la ranura 0.
pub fn calib_cota() {
    println!("== CALIBRACION: tic_cota (EN-PLACA: sobrevive a 12 ms, muere con 14 ms; cotas 100+100) ==");
    for &d in &[100u64, 1_000, 3_000, 6_000, 10_000, 12_000, 12_400, 12_600, 12_800, 13_000, 14_000, 20_000] {
        let mut cfg = Cfg::base();
        cfg.active = [true, false, false, false, false, false];
        let mut sim = Sim::new(cfg);
        sim.hold_on_vencida = Some((0, vec![vec![(d * 1000, false)]]));
        sim.hw_at(ms(20), HwEv::Inject { slot: 0, kind: Inj::Hang });
        sim.run_until(ms(120));
        let viva = sim.s[0].tic.estado() != Estado::Muerta;
        println!("  golpe de P2 de {:6} us -> {}  (recuperaciones {})", d, if viva { "VIVA " } else { "MUERTA" }, sim.s[0].recuperaciones);
    }
}

pub fn informe(sim: &Sim, t0: u64, titulo: &str) {
    println!("  -- {titulo}");
    let esc = all(sim, "escalada", -1);
    let den = all(sim, "escalada_DENEGADA", -1);
    println!(
        "     escaladas {} (primeras t = {:?} us)   denegadas {} (t = {:?} us)   concurrentes_max {}",
        sim.escaladas,
        esc.iter().take(6).map(|t| (us(*t - t0) * 10.0).round() / 10.0).collect::<Vec<_>>(),
        sim.denegadas,
        den.iter().take(6).map(|t| (us(*t - t0) * 10.0).round() / 10.0).collect::<Vec<_>>(),
        sim.max_concurrent_esc
    );
    for n in 0..N {
        let s = &sim.s[n];
        if !s.on {
            continue;
        }
        println!(
            "     ranura {n}: plazos {:3} (colaterales {:3}) rec {:3} muertas {} giros {:6} gap_max_modulo {:8.1} us estado {:?}",
            s.plazos, s.colateral, s.recuperaciones, s.muertas, s.giros, us(s.max_gap), s.tic.estado()
        );
    }
    println!(
        "     supervisor: deja de alimentar a t={} us   IWDG reinicia el chip a t={} us (feed cada {} ms, IWDG {} ms)",
        rel(sim.first_refusal, t0),
        rel(sim.iwdg_reset_at, t0),
        sim.cfg.feed_period_ns / 1_000_000,
        sim.cfg.iwdg_ns / 1_000_000
    );
}

fn base6() -> Cfg {
    Cfg::base()
}

/// A2/A3: un canal atascado que el reset del GPDMA1 cura (una ranura, o las seis a la vez).
pub fn a2_a3() {
    println!("== A2: UN canal atascado (ranura 2) que el reset del GPDMA1 cura; seis ranuras con NADA ==");
    for budget in [Budget::Ninguno, Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false }] {
        let mut cfg = base6();
        cfg.budget = budget;
        let mut sim = Sim::new(cfg);
        sim.trace_arm = Some(2);
        sim.hw_at(ms(50), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: false } });
        sim.run_until(ms(150));
        let t0 = first(&sim, "cstart_veneno", 2).unwrap();
        println!("  presupuesto {:?}", budget);
        println!("     ranura 2 desde el CSTART atascado (us): vencida {} plan_pide {} rec_inicio {} canal_no_para {} escalada {} spi_reset {} rec_hecha {} siguiente_cstart {}",
            rel(first_after(&sim, "tic_vencida", 2, t0), t0),
            rel(first_after(&sim, "plan_pide_rec", 2, t0), t0),
            rel(first_after(&sim, "rec_inicio", 2, t0), t0),
            rel(first_after(&sim, "rec_canal_no_para", 2, t0), t0),
            rel(first_after(&sim, "escalada", 2, t0), t0),
            rel(first_after(&sim, "spi_reset", 2, t0), t0),
            rel(first_after(&sim, "rec_hecha", 2, t0), t0),
            rel(sim.marks.iter().filter(|m| m.what == "cstart" && m.t > t0).map(|m| m.t).next(), t0));
        informe(&sim, t0, "resultado");
    }
    println!("== A3: las SEIS ranuras atascadas a la vez (mismo tic), el reset del GPDMA1 las cura ==");
    for budget in [Budget::Ninguno, Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false }] {
        let mut cfg = base6();
        cfg.budget = budget;
        let mut sim = Sim::new(cfg);
        for n in 0..N {
            sim.hw_at(ms(50), HwEv::Inject { slot: n, kind: Inj::Stuck { persistente: false } });
        }
        sim.run_until(ms(150));
        let t0 = first(&sim, "cstart_veneno", -1).unwrap();
        println!("  presupuesto {:?}", budget);
        informe(&sim, t0, "resultado");
    }
}

/// A4: un canal que el reset NO cura (ranura 2): el bucle de escaladas, con y sin presupuesto.
pub fn a4() {
    println!("== A4: canal atascado que el reset NO cura (ranura 2); seis ranuras; 400 ms ==");
    for (budget, deny) in [
        (Budget::Ninguno, Deny::Retener),
        (Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false }, Deny::Retener),
        (Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false }, Deny::Directo),
    ] {
        let mut cfg = base6();
        cfg.budget = budget;
        cfg.deny = deny;
        let mut sim = Sim::new(cfg);
        sim.hw_at(ms(50), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: true } });
        sim.run_until(ms(450));
        let t0 = first(&sim, "cstart_veneno", 2).unwrap();
        println!("  presupuesto {:?} / muerte {:?}", budget, deny);
        informe(&sim, t0, "resultado");
        let tm = first(&sim, "muerta", 2).or(first(&sim, "muerta_por_presupuesto", 2));
        println!("     ranura 2 pasa a Muerta a t = {} us; la tasa de escaladas sin presupuesto es {:.0}/s",
            rel(tm, t0), sim.escaladas as f64 / 0.4);
    }
}

/// A5: un bloqueo transitorio del bus (todas las ranuras en vuelo se atascan mientras dura): ¿cuanto aguanta?
pub fn a5() {
    println!("== A5: bloqueo TRANSITORIO del bus de T us (cualquier maestro que acapare AXI/AHB del GPDMA1), seis ranuras ==");
    println!("   con presupuesto V3 (3 por 8000 tics), muerte por Retener; escaladas / denegadas / ranuras muertas / reset del chip");
    for &t_us in &[20u64, 50, 100, 200, 300, 400, 500, 700, 1000, 2000, 5000, 20000] {
        let mut cfg = base6();
        cfg.budget = Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false };
        let mut sim = Sim::new(cfg);
        let t_ini = ms(50) + 10_000; // 10 us despues de un tic: las seis acaban de armarse
        sim.hw_at(t_ini, HwEv::StallStart { until: t_ini + t_us * 1000 });
        sim.run_until(ms(250));
        let muertas: u32 = sim.s.iter().map(|s| s.muertas).sum();
        println!(
            "   T = {:6} us -> escaladas {:3} denegadas {:3} ranuras_muertas {} reset_del_chip {}  (plazos por ranura: {})",
            t_us, sim.escaladas, sim.denegadas, muertas,
            match sim.iwdg_reset_at { Some(t) => format!("SI a t={:.1} ms tras el bloqueo", us(t - t_ini) / 1000.0), None => "no".into() },
            sim.s[0].plazos
        );
    }
}

/// A6: escaladas independientes (cada una curada por el reset) a una tasa r por segundo.
pub fn a6() {
    println!("== A6: canal atascado que el reset cura, repetido cada P ms en la ranura 2; presupuesto V3 (3 por 8000 tics); 3 s ==");
    for &p_ms in &[30u64, 100, 250, 300, 330, 340, 400, 500, 1000] {
        let mut cfg = base6();
        cfg.budget = Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false };
        let mut sim = Sim::new(cfg);
        let mut t = ms(50);
        while t < ms(3000) {
            sim.hw_at(t, HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: false } });
            t += ms(p_ms);
        }
        sim.run_until(ms(3200));
        println!(
            "   cada {:4} ms ({:5.2}/s) -> escaladas {:2} denegadas {:2} ranura2 {:?} reset_del_chip {}",
            p_ms, 1000.0 / p_ms as f64, sim.escaladas, sim.denegadas, sim.s[2].tic.estado(),
            match sim.iwdg_reset_at { Some(t) => format!("SI a t={:.0} ms", us(t) / 1000.0), None => "no".into() }
        );
    }
    println!("   (la fase C de tic_recupera hace diez escaladas forzadas cada 30 ms = 33/s)");
}

/// A7: estampas a cero al arrancar.
pub fn a7() {
    println!("== A7: primera escalada 0,5 s despues de lanzar el tic, estampas iniciales [0,0,0] vs vacias ==");
    for init_cero in [false, true] {
        let mut cfg = base6();
        cfg.budget = Budget::V3 { max: 3, ventana_tics: 8000, init_cero };
        let mut sim = Sim::new(cfg);
        sim.hw_at(ms(500), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: false } });
        sim.run_until(ms(700));
        println!("   init_cero={} -> escaladas {} denegadas {} ranura2 {:?}", init_cero, sim.escaladas, sim.denegadas, sim.s[2].tic.estado());
    }
}

/// A8: una retencion de P2 que cae DENTRO de la reprogramacion de la escalada (las ranuras estan `SUCIA`).
pub fn a8() {
    println!("== A8: escalada (canal atascado que el reset cura, ranura 2) y una retencion de P2 de D ms justo despues de la seccion critica, mientras `escala()` reprograma ==");
    println!("   sin escalada, una ranura en Vencida muere a los 12,6 ms de retencion (C1); aqui las seis estan SUCIA, que el tic salta entero");
    for &d_ms in &[5u64, 14, 30, 100] {
        let mut cfg = base6();
        cfg.budget = Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false };
        let mut sim = Sim::new(cfg);
        sim.hold_on_escalada = Some(vec![vec![(d_ms * 1_000_000, false)]]);
        sim.hw_at(ms(50), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: false } });
        sim.run_until(ms(50 + d_ms + 90));
        let t0 = first(&sim, "cstart_veneno", 2).unwrap();
        let muertas: u32 = sim.s.iter().map(|s| s.muertas).sum();
        let congeladas: Vec<bool> = sim.s.iter().map(|s| s.sucia).collect();
        println!("   D = {:3} ms -> ranuras muertas {}  ranuras SUCIA al acabar la retencion+1ms: ver abajo; reset del chip {}  plazos {:?}",
            d_ms, muertas,
            match sim.iwdg_reset_at { Some(t) => format!("SI a t={:.1} ms", us(t - t0) / 1000.0), None => "no".into() },
            sim.s.iter().map(|s| s.plazos).collect::<Vec<_>>());
    }
    // el instante a mitad de la retencion de 100 ms
    let mut cfg = base6();
    let mut sim = Sim::new(cfg);
    sim.hold_on_escalada = Some(vec![vec![(100_000_000, false)]]);
    sim.hw_at(ms(50), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: false } });
    sim.run_until(ms(50) + 60_000_000);
    println!("   a +60 ms dentro de la retencion de 100 ms: SUCIA = {:?}, estados = {:?}, muertas = {}",
        sim.s.iter().map(|s| s.sucia).collect::<Vec<_>>(),
        sim.s.iter().map(|s| format!("{:?}", s.tic.estado())).collect::<Vec<_>>(),
        sim.s.iter().map(|s| s.muertas).sum::<u32>());
}

/// A9: la cadena hasta el IWDG segun lo que el papel no fija: periodo del supervisor y plazo del IWDG.
pub fn a9() {
    println!("== A9: canal atascado que el reset NO cura (ranura 2), presupuesto V3 con denegacion: cuando reinicia el chip segun el supervisor (#291, no existe) y el IWDG ==");
    println!("   {:>12} {:>9} | {:>12} {:>14} {:>16} {:>18}", "feed cada ms", "IWDG ms", "Muerta (us)", "deja de alim.", "IWDG reinicia ms", "modulo ranura 2 suelta (ms)");
    for &p in &[1u64, 5, 10, 25] {
        for &w in &[55u64, 60, 100, 200] {
            let mut cfg = base6();
            cfg.budget = Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false };
            cfg.deny = Deny::Retener;
            cfg.feed_period_ns = p * 1_000_000;
            cfg.iwdg_ns = w * 1_000_000;
            let mut sim = Sim::new(cfg);
            sim.hw_at(ms(53), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: true } });
            sim.run_until(ms(53) + ms(w) + ms(p) + ms(60));
            let t0 = first(&sim, "cstart_veneno", 2).unwrap();
            let tm = first(&sim, "muerta", 2);
            // ultimo cuadro valido del modulo 2 antes del fallo: t0 - 125 us + c; suelta a +50 ms de ese instante
            let ultimo = sim.s[2].last_valid;
            println!("   {:>12} {:>9} | {:>12} {:>14} {:>16} {:>18.1}",
                p, w, rel(tm, t0).trim(), rel(sim.first_refusal, t0).trim(),
                sim.iwdg_reset_at.map_or("-".to_string(), |t| format!("{:.1}", us(t - t0) / 1000.0)),
                us(ultimo + 50_000_000 - t0) / 1000.0);
        }
    }
}

/// A5b: el menor bloqueo del bus que agota el presupuesto, barriendo la fase respecto al tic.
pub fn a5b() {
    println!("== A5b: menor bloqueo transitorio del bus T (us) que lleva al reinicio del chip, segun la fase de inicio respecto al tic (seis ranuras en vuelo) ==");
    let mut peor = u64::MAX;
    let mut fase_peor = 0;
    for fase_us in (0..125).step_by(5) {
        let mut tmin = None;
        for t_us in (20..2000).step_by(10) {
            let mut cfg = base6();
            cfg.budget = Budget::V3 { max: 3, ventana_tics: 8000, init_cero: false };
            let mut sim = Sim::new(cfg);
            let t_ini = ms(50) + fase_us as u64 * 1000 + 10_000;
            sim.hw_at(t_ini, HwEv::StallStart { until: t_ini + t_us as u64 * 1000 });
            sim.run_until(ms(190));
            let muertas: u32 = sim.s.iter().map(|s| s.muertas).sum();
            if sim.denegadas > 0 || muertas > 0 {
                tmin = Some(t_us);
                break;
            }
        }
        if let Some(t) = tmin {
            if t < peor { peor = t; fase_peor = fase_us; }
        }
    }
    println!("   el menor T que agota el presupuesto en alguna fase: {} us (fase {} us tras el tic)", peor, fase_peor);
}
