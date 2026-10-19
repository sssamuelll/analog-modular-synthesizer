//! Halberg, cuarta pasada: la espera contra R-H1 y contra la cota de `Reiniciando`.
use sam17_nucleo_core::transporte_j2::{Entrada, Estado, Lectura, Transporte};
use sam17_nucleo_modelo::motor::{ms, Cfg, Escaladas, HwEv, Inj, Sim, N, PERIODO_NS};

fn cfg(e: usize, ventana_ms: u64, espera_ms_x10: u64) -> Cfg {
    let mut c = Cfg::base();
    c.escaladas = Escaladas::K1 { e, ventana_ns: ventana_ms * 1_000_000 };
    c.espera_escalada_ns = espera_ms_x10 * 100_000;
    c
}

fn muertas(sim: &Sim) -> usize {
    (0..N).filter(|&n| sim.s[n].tic.estado() == Estado::Muerta).count()
}

/// Corre en pasos de un periodo y devuelve (max periodos en Reiniciando, max en Vencida).
fn corre_midiendo(sim: &mut Sim, hasta: u64) -> (u16, u16) {
    let (mut r, mut v) = (0u16, 0u16);
    let mut t = sim.now;
    while t < hasta {
        t += PERIODO_NS / 5;
        sim.run_until(t);
        for n in 0..N {
            match sim.s[n].tic.estado() {
                Estado::Reiniciando { espera } => r = r.max(espera),
                Estado::Vencida { espera } => v = v.max(espera),
                _ => {}
            }
        }
    }
    (r, v)
}

/// Bloqueo del GPDMA1 de `d_us` en `t_ini`, y una retencion de P2 (no atomica) de `l_us` en `t_p2`.
fn bloqueo_con_p2(c: &Cfg, t_ini: u64, d_us: u64, t_p2: Option<u64>, l_us: u64) -> Sim {
    let mut sim = Sim::new(c.clone());
    sim.hw_at(t_ini, HwEv::StallStart { until: t_ini + d_us * 1000 });
    if let Some(t) = t_p2 {
        sim.hw_at(t, HwEv::P2 { dur: l_us * 1000, atomic: false });
    }
    sim
}

#[test]
#[ignore]
fn x1_espera_contra_r_h1() {
    let t_ini = ms(60) + 10_000;
    for (nombre, e, v) in [("6 en 1 s", 6, 1000), ("3 en 1 s", 3, 1000), ("2 en 100 ms", 2, 100)] {
        for espera in [0u64, 10, 20] {
            let c = cfg(e, v, espera);
            // sin P2: donde cae la aplazada
            let mut s0 = bloqueo_con_p2(&c, t_ini, 1_000, None, 0);
            s0.run_until(ms(250));
            let apl = s0.marks.iter().find(|m| m.what == "escalada_aplazada").map(|m| (m.t, m.slot, m.x));
            print!("{nombre:12} espera {:>3.1} ms, bloqueo 1 ms: escaladas {} aplazadas {} reinicio {:?}; primera aplazada {:?}",
                espera as f64 / 10.0, s0.escaladas, s0.aplazadas, s0.iwdg_reset_at.is_some(), apl.map(|(t, s, x)| ((t - t_ini) / 1000, s, x as u64 * 1000 - t_ini)));
            println!();
            for l_us in [8_000u64, 9_000, 10_000, 10_500, 11_000, 11_500, 12_000] {
                let (mut n, mut rs, mut mu, mut rmax) = (0, 0, 0, 0u16);
                let mut primer_mata: Option<u64> = None;
                // la P2 arranca en cualquier punto de los primeros 4 ms desde el bloqueo, cada 25 us
                let mut off = 0u64;
                while off <= 4_000_000 {
                    let mut sim = bloqueo_con_p2(&c, t_ini, 1_000, Some(t_ini + off), l_us);
                    let (r, _) = corre_midiendo(&mut sim, ms(250));
                    n += 1;
                    rmax = rmax.max(r);
                    if sim.iwdg_reset_at.is_some() { rs += 1; }
                    if muertas(&sim) > 0 {
                        mu += 1;
                        primer_mata.get_or_insert(off / 1000);
                    }
                    off += 25_000;
                }
                println!("    P2 {:>6} us desde bloqueo+[0,4] ms: {rs:>3}/{n} reinicios, {mu:>3} con ranura muerta, max Reiniciando {rmax} periodos; primer arranque que mata +{:?} us", l_us, primer_mata);
            }
        }
    }
}

/// La cota cuenta `>`: cada estado aguanta cota + 1 periodos.
#[test]
fn x2_hueco_maximo_de_la_maquina() {
    let mut t = Transporte::con_cotas(200, 100);
    let lib = Entrada { identidad: true, bajada: Some(3), ..Entrada::default() };
    t.paso(lib);
    assert!(matches!(t.estado(), Estado::Armada { .. }));
    let mut tics = 0u32;
    // sin EOT hasta vencer
    loop {
        tics += 1;
        t.paso(Entrada { identidad: true, lectura: Lectura::default(), incidente: 0, ..Entrada::default() });
        if matches!(t.estado(), Estado::Vencida { .. }) { break; }
    }
    let inc = t.incidente();
    // Vencida hasta el ultimo tic que no la mata
    loop {
        let mut u = t;
        u.paso(Entrada { identidad: true, incidente: inc, ..Entrada::default() });
        if u.estado() == Estado::Muerta { break; }
        t = u;
        tics += 1;
    }
    // en ese tic llega `reinicio_en_curso`
    tics += 1;
    t.paso(Entrada { identidad: true, incidente: inc, reinicio_en_curso: true, ..Entrada::default() });
    assert!(matches!(t.estado(), Estado::Reiniciando { .. }));
    loop {
        let mut u = t;
        u.paso(Entrada { identidad: true, incidente: inc, reinicio_en_curso: true, ..Entrada::default() });
        if u.estado() == Estado::Muerta { break; }
        t = u;
        tics += 1;
    }
    tics += 1;
    t.paso(Entrada { identidad: true, incidente: inc, reinicio_hecho: true, bajada: Some(3), ..Entrada::default() });
    assert!(matches!(t.estado(), Estado::Armada { .. }));
    println!("x2: de sello a sello, con plazo 3 y cotas 200/100 sin morir: {tics} periodos = {:.3} ms", tics as f64 * 0.125);
}

/// Lo que cuesta un bloqueo de 1 ms en tramas, con y sin espera (6 en 1 s), en las cinco fases.
#[test]
#[ignore]
fn x3_coste_del_bloqueo_de_1_ms() {
    for d in [1_000u64, 3_000] {
    for espera in [0u64, 20] {
        let c = cfg(6, 1000, espera);
        for fase in (0..125u64).step_by(25) {
            let t_ini = ms(50) + fase * 1000 + 10_000;
            let mut sim = Sim::new(c.clone());
            sim.hw_at(t_ini, HwEv::StallStart { until: t_ini + d * 1000 });
            let (r, v) = corre_midiendo(&mut sim, ms(250));
            let propios: Vec<usize> = (0..N).map(|n| sim.cuenta_desde("tic_vencida", n as i32, t_ini)).collect();
            let ajenos: Vec<usize> = (0..N).map(|n| sim.cuenta_desde("plazo_ajeno", n as i32, t_ini)).collect();
            let gap: Vec<u64> = (0..N).map(|n| sim.s[n].max_gap / 1000).collect();
            println!("bloqueo {d} us, espera {:.1} ms, fase {fase}: escaladas {} aplazadas {}; propios {propios:?} ajenos {ajenos:?}; mayor hueco de tramas validas (us) {gap:?}; max Reiniciando {r} / Vencida {v} periodos",
                espera as f64 / 10.0, sim.escaladas, sim.aplazadas);
        }
    }
    }
}

/// Un canal incurable en una ranura y otro atasco curable en otra, dentro de la espera.
#[test]
#[ignore]
fn x4_incurable_y_curable_en_la_espera() {
    for espera in [0u64, 20] {
        for dt_us in [100u64, 500, 1_000, 1_900, 2_500] {
            let c = cfg(6, 1000, espera);
            let mut sim = Sim::new(c);
            sim.hw_at(ms(50), HwEv::Inject { slot: 2, kind: Inj::Stuck { persistente: true } });
            sim.hw_at(ms(50) + dt_us * 1000, HwEv::Inject { slot: 4, kind: Inj::Stuck { persistente: false } });
            let (r, _) = corre_midiendo(&mut sim, ms(300));
            println!("espera {:.1} ms, curable en r4 a +{dt_us} us: escaladas {} aplazadas {} denegadas {}; muertas {:?}; reinicio {:?}; max Reiniciando {r}",
                espera as f64 / 10.0, sim.escaladas, sim.aplazadas, sim.denegadas,
                (0..N).filter(|&n| sim.s[n].tic.estado() == Estado::Muerta).collect::<Vec<_>>(),
                sim.iwdg_reset_at.map(|t| (t - ms(50)) / 1000));
        }
    }
}

/// Variante: el reloj que mira la aplazada (P3) va una vuelta de 32 bits por delante del que la
/// fecha (P4), como RELOJ_PLAN frente a RELOJ_REC de `fw` tras dias sin escaladas.
#[test]
#[ignore]
fn x5_reloj_de_p3_por_delante_del_de_p4() {
    for desfase in [0u64, (1u64 << 32) * 125] {
        for d in [1_000u64, 3_000] {
            let mut c = cfg(6, 1000, 20);
            c.desfase_plan_us = desfase;
            let t_ini = ms(60) + 10_000;
            let mut sim = Sim::new(c);
            sim.hw_at(t_ini, HwEv::StallStart { until: t_ini + d * 1000 });
            sim.run_until(ms(250));
            let repide = sim.cuenta_desde("plan_repide_rec", -1, 0);
            let rec_ini = sim.cuenta_desde("rec_inicio", -1, 0);
            let no_para = sim.cuenta_desde("rec_canal_no_para", -1, 0);
            println!("desfase {} vueltas, bloqueo {d} us: escaladas {} aplazadas {} repeticiones del planificador {repide} recuperaciones arrancadas {rec_ini} (T_CANAL agotado {no_para}); P4 ocupada {:.0} us; muertas {}; reinicio {}",
                desfase / ((1u64 << 32) * 125), sim.escaladas, sim.aplazadas, sim.busy[4] / 1000, muertas(&sim), sim.iwdg_reset_at.is_some());
        }
    }
}

/// La traza de un caso de x1: 6 en 1 s, bloqueo de 1 ms, P2 de 12 ms a +850 us del bloqueo.
#[test]
#[ignore]
fn x6_traza() {
    let t_ini = ms(60) + 10_000;
    for espera in [0u64, 20] {
        let c = cfg(6, 1000, espera);
        let mut sim = bloqueo_con_p2(&c, t_ini, 1_000, Some(t_ini + 850_000), 12_000);
        sim.run_until(ms(250));
        println!("espera {:.1} ms: escaladas {} aplazadas {} reinicio {:?}", espera as f64 / 10.0, sim.escaladas, sim.aplazadas, sim.iwdg_reset_at.map(|t| (t - t_ini) / 1000));
        for m in sim.marks.iter().filter(|m| m.t >= t_ini && m.t < t_ini + ms(20) && ["escalada", "escalada_aplazada", "plan_repide_rec", "muerta", "rec_hecha"].contains(&m.what)) {
            let x = if m.what == "escalada_aplazada" { format!(" hasta +{} us", (m.x as u64 * 1000 - t_ini) / 1000) } else { String::new() };
            println!("  +{:>6} us r{} {}{}", (m.t - t_ini) / 1000, m.slot, m.what, x);
        }
    }
}
