//! Halberg, quinta pasada: la espera de 1 ms con `Reiniciando` 112 y su aserto.
use sam17_nucleo_core::transporte_j2::{hueco_de_recuperacion, Estado};
use sam17_nucleo_modelo::motor::{ms, Cfg, Escaladas, HwEv, Inj, Sim, N, PERIODO_NS};

fn cfg(espera_us: u64, cotas: (u16, u16)) -> Cfg {
    let mut c = Cfg::base();
    c.escaladas = Escaladas::K1 { e: 6, ventana_ns: 1_000_000_000 };
    c.espera_escalada_ns = espera_us * 1000;
    c.cotas = cotas;
    c
}

fn muertas(sim: &Sim) -> Vec<usize> {
    (0..N).filter(|&n| sim.s[n].tic.estado() == Estado::Muerta).collect()
}

/// Corre hasta `hasta` en pasos de 25 us y devuelve el mayor `espera` visto en `Reiniciando`.
fn max_reiniciando(sim: &mut Sim, hasta: u64) -> u16 {
    let mut r = 0u16;
    let mut t = sim.now;
    while t < hasta {
        t += PERIODO_NS / 5;
        sim.run_until(t);
        for n in 0..N {
            if let Estado::Reiniciando { espera } = sim.s[n].tic.estado() {
                r = r.max(espera);
            }
        }
    }
    r
}

const T_INI: u64 = 60_000_000 + 10_000;

fn bloqueo(sim: &mut Sim, d_us: u64) {
    sim.hw_at(T_INI, HwEv::StallStart { until: T_INI + d_us * 1000 });
}

fn p2(sim: &mut Sim, t: u64, dur: u64) {
    sim.hw_at(t, HwEv::P2 { dur, atomic: false });
}

/// x7: el x1 de la cuarta pasada, fino: bloqueo de 1 ms y una P2 no atomica de L que arranca
/// desde 1 ms antes hasta 4 ms despues del bloqueo, cada 25 us (201 arranques).
#[test]
#[ignore]
fn x7_umbral_de_l_contra_el_aserto() {
    for (espera_us, cr) in [(1_000u64, 112u16), (2_000, 120)] {
        let c = cfg(espera_us, (200, cr));
        let pred = (u64::from(cr) + 1) * 125 - espera_us - 250;
        println!("espera {espera_us} us, Reiniciando {cr}: el aserto deja L < {pred} us");
        for l_us in [12_000u64, 12_250, 12_500, 12_750, 12_875, 13_000, 13_250, 13_500] {
            let (mut n, mut rs, mut rmax) = (0, 0, 0u16);
            let mut primero: Option<i64> = None;
            let mut off: i64 = -1_000_000;
            while off <= 4_000_000 {
                let mut sim = Sim::new(c.clone());
                bloqueo(&mut sim, 1_000);
                p2(&mut sim, (T_INI as i64 + off) as u64, l_us * 1000);
                rmax = rmax.max(max_reiniciando(&mut sim, T_INI + ms(25)));
                sim.run_until(ms(250));
                n += 1;
                if sim.iwdg_reset_at.is_some() {
                    rs += 1;
                    primero.get_or_insert(off / 1000);
                }
                off += 25_000;
            }
            println!("  L {l_us:>6} us: {rs:>3}/{n} reinicios, max Reiniciando {rmax} periodos, primer arranque que reinicia {primero:?} us");
        }
    }
}

/// La referencia sin P2: el `hasta` de la primera aplazada y la ranura mas baja aplazada.
fn referencia(c: &Cfg) -> (u64, usize) {
    let mut s = Sim::new(c.clone());
    bloqueo(&mut s, 1_000);
    s.run_until(ms(250));
    let apl: Vec<_> = s.marks.iter().filter(|m| m.what == "escalada_aplazada").collect();
    let hasta_ns = apl[0].x as u64 * 1000;
    let k = apl.iter().filter(|m| m.x == apl[0].x).map(|m| m.slot as usize).min().unwrap();
    (hasta_ns, k)
}

/// x8: dos ventanas de R-H1, cada una legal. La primera retiene al planificador (P3) sobre el
/// instante en que vence la espera (11,9 ms); la segunda (12 ms) entra cuando la recuperacion
/// (P4) ya arranco la ranura repedida. Contra lo mismo sin espera.
#[test]
#[ignore]
fn x8_dos_ventanas_legales() {
    let c = cfg(1_000, (200, 112));
    let (hasta, k) = referencia(&c);
    println!("espera 1 ms, 200/112: hasta = bloqueo + {} us, ranura {k}", (hasta - T_INI) / 1000);
    let l1 = 11_900_000u64;
    let mut mata = 0;
    let mut n = 0;
    for d in (0..=20u64).map(|i| i * 100_000) {
        let mut sim = Sim::new(c.clone());
        bloqueo(&mut sim, 1_000);
        p2(&mut sim, hasta - d, l1);
        sim.run_until(hasta - d - 1_000);
        sim.hold_on_rec = Some((k, vec![vec![(12_000_000, false)]]));
        sim.run_until(ms(250));
        n += 1;
        let m = muertas(&sim);
        if sim.iwdg_reset_at.is_some() {
            mata += 1;
        }
        if d == 0 || d == 1_000_000 || d == 2_000_000 {
            let rec = sim.marks.iter()
                .filter(|m| m.what == "rec_inicio" && m.slot == k as i32 && m.t > hasta)
                .map(|m| (m.t - T_INI) / 1000).next();
            let rr = sim.iwdg_reset_at.map(|t| (t - T_INI) / 1_000_000);
            println!("  P2 de 11,9 ms a hasta-{} us: muertas {m:?}, reinicio {rr:?} ms tras el bloqueo, P4 rearranca la ranura {k} a +{rec:?} us", d / 1000);
        }
    }
    println!("  -> {mata}/{n} reinicios con espera 1 ms");

    for (nombre, c) in [("sin espera 200/100", cfg(0, (200, 100))), ("espera 1 ms 200/112", cfg(1_000, (200, 112)))] {
        let mut sim = Sim::new(c.clone());
        sim.hw_at(T_INI, HwEv::Inject { slot: 2, kind: Inj::Hang });
        sim.hold_on_vencida = Some((2, vec![vec![(l1, false)]]));
        sim.hold_on_rec = Some((2, vec![vec![(12_000_000, false)]]));
        sim.run_until(ms(250));
        println!("  {nombre}: cuelgue, P2 11,9 ms en Vencida y 12 ms al arrancar P4: muertas {:?}, reinicio {:?}", muertas(&sim), sim.iwdg_reset_at.is_some());
    }

    let c0 = cfg(0, (200, 100));
    let mut a = Sim::new(c0.clone());
    a.hw_at(T_INI, HwEv::Inject { slot: 2, kind: Inj::Hang });
    a.hold_on_rec = Some((2, vec![vec![(12_000_000, false)]]));
    a.run_until(ms(250));
    let ts = a.primera_desde("spi_reset", 2, T_INI).unwrap();
    println!("  sin espera, una ventana al arrancar P4: muertas {:?}; spi_reset a +{} us", muertas(&a), (ts - T_INI) / 1000);
    let mut b = Sim::new(c0);
    b.hw_at(T_INI, HwEv::Inject { slot: 2, kind: Inj::Hang });
    b.hold_on_rec = Some((2, vec![vec![(12_000_000, false)]]));
    p2(&mut b, ts + 1_000, 12_000_000);
    b.run_until(ms(250));
    println!("  sin espera, y otra de 12 ms 1 us despues del reset del SPI (P4 a medias): muertas {:?}, reinicio {:?}", muertas(&b), b.iwdg_reset_at.is_some());
}

/// x9: el umbral E x espera, fino.
#[test]
#[ignore]
fn x9_umbral_del_bloqueo() {
    let c = cfg(1_000, (200, 112));
    for d in [5_000u64, 5_250, 5_500, 5_750, 6_000, 6_250, 6_500, 7_000] {
        let mut rs = 0;
        let mut esc = 0;
        for fase in (0..125u64).step_by(5) {
            let mut sim = Sim::new(c.clone());
            let t = ms(50) + fase * 1000 + 10_000;
            sim.hw_at(t, HwEv::StallStart { until: t + d * 1000 });
            sim.run_until(ms(250));
            rs += usize::from(sim.iwdg_reset_at.is_some());
            esc = esc.max(sim.escaladas);
        }
        println!("  bloqueo {d:>5} us: {rs}/25 fases reinician, escaladas max {esc}");
    }
}

/// x10: el hueco de la ficha C contra el modelo, con 25 y con 103 bytes.
#[test]
#[ignore]
fn x10_hueco_del_modulo() {
    for msg in [25u16, 103] {
        let mut c = cfg(1_000, (200, 112));
        c.msg = [msg; N];
        let sim0 = Sim::new(c.clone());
        let plazo = sim0.plazo_tics(msg);
        let h = hueco_de_recuperacion(plazo, 200, 112) + 1;
        let mut mejor = (0u64, 0u64, 0u64);
        for l1 in [24_000u64, 24_500, 24_750, 24_875, 25_000] {
            for l2 in [13_000u64, 13_500, 13_750, 13_875, 14_000] {
                let mut sim = Sim::new(c.clone());
                sim.hw_at(T_INI, HwEv::Inject { slot: 2, kind: Inj::Hang });
                sim.hold_on_vencida = Some((2, vec![vec![(l1 * 1000, false)]]));
                sim.hold_on_rec = Some((2, vec![vec![(l2 * 1000, false)]]));
                sim.run_until(ms(250));
                if muertas(&sim).is_empty() && sim.s[2].max_gap > mejor.0 {
                    mejor = (sim.s[2].max_gap, l1, l2);
                }
            }
        }
        println!("  {msg} B (plazo {plazo}): aserto {h} periodos = {} us; modelo, mayor hueco sin tramas de una ranura que sobrevive {} us (P2 {} y {} us)",
            u64::from(h) * 125, mejor.0 / 1000, mejor.1, mejor.2);
    }
}

/// x11: dos ventanas legales tras un bloqueo de 1 ms. La primera, una P2 de 11,9 ms que arranca
/// en `s` (de 0 a 16 ms tras el bloqueo, cada 100 us); la segunda, 12 ms, entra en el primer
/// arranque de P4 (`rec_inicio`) de la ranura `k` despues de que empiece la primera. Se toma la
/// peor `k`. Con espera de 1 ms y 200/112, contra sin espera y 200/100.
#[test]
#[ignore]
fn x11_dos_ventanas_barrido() {
    for (nombre, c) in [("sin espera 200/100", cfg(0, (200, 100))), ("espera 1 ms 200/112", cfg(1_000, (200, 112))), ("espera 2 ms 200/120", cfg(2_000, (200, 120)))] {
        let (mut mata, mut n) = (0, 0);
        let mut primeros = Vec::new();
        let mut s = 0u64;
        while s <= 16_000_000 {
            let mut alguna = false;
            for k in 0..N {
                let mut sim = Sim::new(c.clone());
                bloqueo(&mut sim, 1_000);
                p2(&mut sim, T_INI + s, 11_900_000);
                sim.run_until(T_INI + s + 1_000);
                sim.hold_on_rec = Some((k, vec![vec![(12_000_000, false)]]));
                sim.run_until(ms(250));
                if sim.iwdg_reset_at.is_some() {
                    alguna = true;
                    break;
                }
            }
            n += 1;
            if alguna {
                mata += 1;
                if primeros.len() < 6 {
                    primeros.push(s / 1000);
                }
            }
            s += 100_000;
        }
        println!("  {nombre}: {mata}/{n} arranques de la primera ventana reinician el chip; los primeros, a +{primeros:?} us del bloqueo");
    }
}

/// x12: la traza del peor caso de x8 (la primera ventana arranca en `hasta`).
#[test]
#[ignore]
fn x12_traza() {
    let c = cfg(1_000, (200, 112));
    let (hasta, k) = referencia(&c);
    let mut sim = Sim::new(c.clone());
    bloqueo(&mut sim, 1_000);
    p2(&mut sim, hasta, 11_900_000);
    sim.run_until(hasta + 1_000);
    sim.hold_on_rec = Some((k, vec![vec![(12_000_000, false)]]));
    sim.run_until(ms(250));
    for m in sim.marks.iter().filter(|m| m.t >= T_INI && m.t < T_INI + ms(30)) {
        if ["escalada", "escalada_aplazada", "plan_repide_rec", "rec_inicio", "rec_hecha", "muerta", "stall_inicio", "tic_vencida"].contains(&m.what) {
            println!("  +{:>6} us  r{:>2}  {}", (m.t - T_INI) / 1000, m.slot, m.what);
        }
    }
    println!("  reinicio del chip a +{:?} us", sim.iwdg_reset_at.map(|t| (t - T_INI) / 1000));
}

#[test]
#[ignore]
fn x13_hueco_de_p3() {
    let c = cfg(1_000, (200, 112));
    let (hasta, _k) = referencia(&c);
    let mut sim = Sim::new(c.clone());
    bloqueo(&mut sim, 1_000);
    p2(&mut sim, hasta, 11_900_000);
    sim.run_until(ms(250));
    println!("  hasta +{} us, P2 hasta +{} us", (hasta - T_INI) / 1000, (hasta + 11_900_000 - T_INI) / 1000);
    for m in sim.marks.iter().filter(|m| m.t >= hasta + 11_800_000 && m.t < hasta + 12_300_000) {
        println!("  +{:>6} us  r{:>2}  {} {}", (m.t - T_INI) / 1000, m.slot, m.what, m.x);
    }
    println!("  plan_lat_max {} us, rec_lat_max {} us", sim.plan_lat_max / 1000, sim.rec_lat_max / 1000);
}

/// x14: x11 con ventanas de pared por debajo de 12 ms: P2 de 11,65 y 11,75 ms de CPU (el tic
/// las estira un 2 %). Mide la mayor latencia del planificador y el mayor tramo de P4 parado.
#[test]
#[ignore]
fn x14_dos_ventanas_de_pared() {
    for (nombre, c) in [("sin espera 200/100", cfg(0, (200, 100))), ("espera 1 ms 200/112", cfg(1_000, (200, 112))), ("espera 2 ms 200/120", cfg(2_000, (200, 120)))] {
        let (mut mata, mut n, mut plan_max, mut p4_max) = (0, 0, 0u64, 0u64);
        let mut primeros = Vec::new();
        let mut s = 0u64;
        while s <= 16_000_000 {
            let mut alguna = false;
            for k in 0..N {
                let mut sim = Sim::new(c.clone());
                bloqueo(&mut sim, 1_000);
                p2(&mut sim, T_INI + s, 11_650_000);
                sim.run_until(T_INI + s + 1_000);
                sim.hold_on_rec = Some((k, vec![vec![(11_750_000, false)]]));
                sim.run_until(ms(250));
                plan_max = plan_max.max(sim.plan_lat_max);
                // el tramo de P4 parado: de su `rec_inicio` a su `spi_reset` (sin bloqueo, unos 2 us)
                for m in sim.marks.iter().filter(|m| m.what == "rec_inicio" && m.t > T_INI) {
                    if let Some(t) = sim.primera_desde("spi_reset", m.slot, m.t) {
                        p4_max = p4_max.max(t - m.t);
                    }
                }
                if sim.iwdg_reset_at.is_some() {
                    alguna = true;
                    break;
                }
            }
            n += 1;
            if alguna {
                mata += 1;
                if primeros.len() < 3 {
                    primeros.push(s / 1000);
                }
            }
            s += 100_000;
        }
        println!("  {nombre}: {mata}/{n} reinician; primeros +{primeros:?} us; mayor latencia del planificador {} us; mayor rec_inicio->spi_reset {} us", plan_max / 1000, p4_max / 1000);
    }
}

/// x15: lo mismo que x14 con P2 de 11,5 y 11,6 ms de CPU, y el tramo de P4 parado medido sin la
/// espera (de un `rec_inicio` al `spi_reset` siguiente, si no hubo aplazada entre medias).
#[test]
#[ignore]
fn x15_dos_ventanas_de_pared() {
    for (nombre, c) in [("sin espera 200/100", cfg(0, (200, 100))), ("espera 1 ms 200/112", cfg(1_000, (200, 112))), ("espera 2 ms 200/120", cfg(2_000, (200, 120)))] {
        let (mut mata, mut n, mut plan_max, mut p4_max) = (0, 0, 0u64, 0u64);
        let mut primeros = Vec::new();
        let mut s = 0u64;
        while s <= 16_000_000 {
            let mut alguna = false;
            for k in 0..N {
                let mut sim = Sim::new(c.clone());
                bloqueo(&mut sim, 1_000);
                p2(&mut sim, T_INI + s, 11_500_000);
                sim.run_until(T_INI + s + 1_000);
                sim.hold_on_rec = Some((k, vec![vec![(11_600_000, false)]]));
                sim.run_until(ms(250));
                plan_max = plan_max.max(sim.plan_lat_max);
                for m in sim.marks.iter().filter(|m| m.what == "rec_inicio" && m.t > T_INI) {
                    let sig = sim.marks.iter().find(|x| x.slot == m.slot && x.t >= m.t && (x.what == "spi_reset" || x.what == "escalada_aplazada"));
                    if let Some(x) = sig {
                        if x.what == "spi_reset" {
                            p4_max = p4_max.max(x.t - m.t);
                        }
                    }
                }
                if sim.iwdg_reset_at.is_some() {
                    alguna = true;
                    break;
                }
            }
            n += 1;
            if alguna {
                mata += 1;
                if primeros.len() < 3 {
                    primeros.push(s / 1000);
                }
            }
            s += 100_000;
        }
        println!("  {nombre}: {mata}/{n} reinician; primeros +{primeros:?} us; mayor latencia del planificador {} us; mayor P4 parada en una recuperacion {} us", plan_max / 1000, p4_max / 1000);
    }
}

/// x16: la traza de x15 en el peor arranque (la primera ventana en `hasta` - 300 us).
#[test]
#[ignore]
fn x16_traza_legal() {
    let c = cfg(1_000, (200, 112));
    let (hasta, k) = referencia(&c);
    for d in [700_000u64, 300_000, 0] {
        let mut sim = Sim::new(c.clone());
        bloqueo(&mut sim, 1_000);
        p2(&mut sim, hasta - d, 11_500_000);
        sim.run_until(hasta - d + 1_000);
        sim.hold_on_rec = Some((k, vec![vec![(11_600_000, false)]]));
        sim.run_until(ms(250));
        println!("primera ventana a hasta-{} us: reinicio {:?} us, latencia del planificador {} us", d / 1000, sim.iwdg_reset_at.map(|t| (t - T_INI) / 1000), sim.plan_lat_max / 1000);
        for m in sim.marks.iter().filter(|m| m.t >= T_INI + 300_000 && m.t < T_INI + ms(30)) {
            if ["escalada_aplazada", "plan_repide_rec", "rec_inicio", "rec_hecha", "muerta", "spi_reset"].contains(&m.what) && (m.slot == 0 || m.slot == 5) {
                println!("  +{:>6} us  r{}  {}", (m.t - T_INI) / 1000, m.slot, m.what);
            }
        }
    }
}
