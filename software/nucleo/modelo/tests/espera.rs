//! La espera minima entre escaladas (candidata de la cuarta pasada, junto a K1): una escalada
//! pedida antes de `espera` desde la ultima concedida se aplaza, la ranura sigue en `Reiniciando`
//! con su cota, y el planificador la vuelve a pedir al cumplirse. Cada prueba imprime sus cifras
//! (`--nocapture`).

use sam17_nucleo_core::transporte_j2::Estado;
use sam17_nucleo_modelo::fuzz::{montar, Tasas};
use sam17_nucleo_modelo::motor::{ms, Cfg, Escaladas, HwEv, Inj, Sim, N};

fn muerta(sim: &Sim, n: usize) -> bool {
    sim.s[n].tic.estado() == Estado::Muerta
}

fn con_espera(espera_ns: u64) -> Cfg {
    let mut cfg = Cfg::base();
    cfg.espera_escalada_ns = espera_ns;
    cfg
}

/// El bloqueo transitorio del GPDMA1 de `v3a5`, de `d_us`, en sus cinco fases.
fn atasco(cfg: &Cfg, d_us: u64) -> Vec<Sim> {
    (0..125u64)
        .step_by(25)
        .map(|fase| {
            let mut sim = Sim::new(cfg.clone());
            let t_ini = ms(50) + fase * 1000 + 10_000;
            sim.hw_at(
                t_ini,
                HwEv::StallStart {
                    until: t_ini + d_us * 1000,
                },
            );
            sim.run_until(ms(250));
            sim
        })
        .collect()
}

#[test]
fn con_espera_de_2_ms_un_atasco_de_1_ms_gasta_una_escalada_y_no_reinicia() {
    // Sin espera, el mismo atasco gasta el presupuesto y reinicia el chip (v3a5).
    assert!(atasco(&Cfg::base(), 1_000)
        .iter()
        .any(|s| s.iwdg_reset_at.is_some()));
    for (fase, sim) in atasco(&con_espera(2_000_000), 1_000).iter().enumerate() {
        println!(
            "espera 2 ms, atasco 1 ms, fase {fase}: escaladas {} aplazadas {} denegadas {}",
            sim.escaladas, sim.aplazadas, sim.denegadas
        );
        assert!(sim.escaladas <= 1, "fase {fase}");
        assert_eq!(sim.denegadas, 0, "fase {fase}");
        assert!((0..N).all(|n| !muerta(sim, n)), "fase {fase}");
        assert!(sim.iwdg_reset_at.is_none(), "fase {fase}");
        assert!(sim.max_concurrent_esc <= 1);
    }
}

#[test]
fn con_espera_un_canal_incurable_gasta_e_escaladas_y_reinicia_el_chip() {
    // La espera no cambia la sentencia de K1: E escaladas, la siguiente negada, la ranura muere
    // por su cota y el supervisor reinicia el chip; cada vecina pierde como mucho E tramas.
    let mut sim = Sim::new(con_espera(2_000_000));
    sim.hw_at(
        ms(50),
        HwEv::Inject {
            slot: 2,
            kind: Inj::Stuck { persistente: true },
        },
    );
    sim.run_until(ms(400));
    println!(
        "espera 2 ms, canal incurable: escaladas {} aplazadas {} denegadas {} reinicio {:?}",
        sim.escaladas, sim.aplazadas, sim.denegadas, sim.iwdg_reset_at
    );
    assert_eq!(sim.escaladas, 3);
    assert!(sim.aplazadas >= 1);
    assert!(sim.denegadas >= 1);
    assert!(muerta(&sim, 2));
    assert!(sim.iwdg_reset_at.is_some());
    for n in (0..N).filter(|&n| n != 2) {
        assert!(!muerta(&sim, n), "vecina {n}");
        assert!(
            sim.s[n].colateral <= 3,
            "vecina {n}: {}",
            sim.s[n].colateral
        );
    }
}

/// Un bloqueo del GPDMA1 de 1 ms y una retencion de P2 de `l_us`, no atomica, que arranca en
/// cualquier punto de los 4 ms siguientes, cada 100 us (x1 de Halberg, cuarta pasada): cuantas de
/// las 41 corridas reinician el chip.
fn reinicios_con_retencion(cfg: &Cfg, l_us: u64) -> usize {
    let t_ini = ms(60) + 10_000;
    (0..=40u64)
        .filter(|k| {
            let mut sim = Sim::new(cfg.clone());
            sim.hw_at(
                t_ini,
                HwEv::StallStart {
                    until: t_ini + 1_000_000,
                },
            );
            sim.hw_at(
                t_ini + k * 100_000,
                HwEv::P2 {
                    dur: l_us * 1000,
                    atomic: false,
                },
            );
            sim.run_until(ms(250));
            sim.iwdg_reset_at.is_some()
        })
        .count()
}

#[test]
fn la_espera_cabe_en_reiniciando_junto_con_la_retencion_de_r_h1() {
    // La espera corre dentro de `Reiniciando`: la cota tiene que cubrir la espera, la ventana de
    // R-H1 (12 ms) y la recuperacion. Con 12,5 ms no la cubre y el chip reinicia; con la cota
    // que pide cada espera, no.
    for (espera_ms, cota_corta, cota_que_cabe) in [(1, 100, 112), (2, 100, 120)] {
        let mut cfg = con_espera(espera_ms * 1_000_000);
        cfg.escaladas = Escaladas::K1 {
            e: 6,
            ventana_ns: 1_000_000_000,
        };
        cfg.cotas = (200, cota_corta);
        let cortas = reinicios_con_retencion(&cfg, 12_000);
        cfg.cotas = (200, cota_que_cabe);
        let largas = reinicios_con_retencion(&cfg, 12_000);
        println!("espera {espera_ms} ms, P2 12 ms: reinicios {cortas}/41 con Reiniciando {cota_corta}, {largas}/41 con {cota_que_cabe}");
        assert!(cortas > 0, "espera {espera_ms} ms");
        assert_eq!(largas, 0, "espera {espera_ms} ms");
    }
}

/// El instante en que la escalada aplazada vuelve a pedirse (o el tic la despierta), en una
/// corrida sin retenciones: un bloqueo de 1 ms a `T_INI`.
const T_INI: u64 = 60_010_000;

fn instante_de_la_repeticion(cfg: &Cfg) -> u64 {
    let mut sim = Sim::new(cfg.clone());
    sim.hw_at(
        T_INI,
        HwEv::StallStart {
            until: T_INI + 1_000_000,
        },
    );
    sim.run_until(ms(250));
    sim.marks
        .iter()
        .find(|m| m.what == "plan_repide_rec" || m.what == "tic_despierta_rec")
        .map(|m| m.t)
        .expect("el bloqueo de 1 ms aplaza alguna escalada")
}

/// El bloqueo de 1 ms y dos retenciones de P2: `l1` desde 200 us antes del instante de la
/// repeticion (asi el planificador no llega a repedir hasta que acaba) y `l2` cuando la
/// recuperacion arranca la ranura `k` (x15 de Halberg, quinta pasada).
fn dos_retenciones(cfg: &Cfg, l1: u64, l2: u64, k: usize) -> Sim {
    let t = instante_de_la_repeticion(cfg);
    let mut sim = Sim::new(cfg.clone());
    sim.hw_at(
        T_INI,
        HwEv::StallStart {
            until: T_INI + 1_000_000,
        },
    );
    sim.hw_at(
        t - 200_000,
        HwEv::P2 {
            dur: l1,
            atomic: false,
        },
    );
    sim.run_until(t + 1_000);
    if l2 > 0 {
        sim.hold_on_rec = Some((k, vec![vec![(l2, false)]]));
    }
    sim.run_until(ms(250));
    sim
}

fn cfg_b(despierta_el_tic: bool) -> Cfg {
    let mut cfg = con_espera(1_000_000);
    cfg.escaladas = Escaladas::K1 {
        e: 6,
        ventana_ns: 1_000_000_000,
    };
    cfg.cotas = (200, 112);
    cfg.despierta_el_tic = despierta_el_tic;
    cfg
}

#[test]
fn con_el_tic_de_despertador_la_peor_retencion_legal_no_reinicia() {
    // R-H1 por nivel, desde que su trabajo queda pendiente hasta que termina: con el tic
    // despertando a la recuperacion, el trabajo de P4 queda pendiente al cumplirse la espera, y
    // todo lo que la retiene hasta terminar (antes de arrancar y en medio) cabe en una ventana.
    for (l1, l2) in [
        (11_800_000, 0),
        (8_000_000, 3_800_000),
        (4_000_000, 7_800_000),
        (0, 11_800_000),
    ] {
        for k in 0..N {
            let sim = dos_retenciones(&cfg_b(true), l1, l2, k);
            assert!(sim.iwdg_reset_at.is_none(), "l1 {l1}, l2 {l2}, k {k}");
        }
    }
}

#[test]
fn con_el_planificador_repidiendo_dos_retenciones_legales_reinician() {
    // Con el planificador como despertador, el trabajo de P4 no queda pendiente hasta que P3
    // corre: P3 tiene su ventana y P4 la suya, y las dos seguidas no caben en `Reiniciando`.
    assert!((0..N).any(|k| {
        dos_retenciones(&cfg_b(false), 11_500_000, 11_500_000, k)
            .iwdg_reset_at
            .is_some()
    }));
}

#[test]
fn con_el_tic_de_despertador_el_testigo_de_la_recuperacion_ve_la_retencion_que_mata() {
    // Las dos retenciones de 11,5 ms reinician el chip con los dos despertadores. Con el tic,
    // la latencia de la recuperacion, de debida a terminada, pasa de 12 ms: el hub rompio R-H1
    // y el testigo lo ve. Con el planificador, cada nivel queda dentro de su ventana y ningun
    // testigo lo ve.
    let peor = |tic: bool| {
        (0..N)
            .map(|k| dos_retenciones(&cfg_b(tic), 11_500_000, 11_500_000, k))
            .filter(|s| s.iwdg_reset_at.is_some())
            .map(|s| s.rec_debida_max)
            .max()
    };
    let con_tic = peor(true).expect("con el tic tambien reinicia");
    let con_plan = peor(false).expect("con el planificador reinicia");
    println!("latencia de la recuperacion hasta terminar: con el tic {con_tic} ns, con el planificador {con_plan} ns");
    assert!(con_tic > 12_000_000, "{con_tic}");
    assert!(con_plan <= 12_000_000, "{con_plan}");
}

const SEMILLAS: u64 = 30;

/// Las dos reglas de K1 que la junta pone una al lado de la otra, y la de `fw` hoy.
fn reglas() -> [(&'static str, Escaladas); 3] {
    [
        (
            "K1 3 en 1 s",
            Escaladas::K1 {
                e: 3,
                ventana_ns: 1_000_000_000,
            },
        ),
        (
            "K1 6 en 1 s",
            Escaladas::K1 {
                e: 6,
                ventana_ns: 1_000_000_000,
            },
        ),
        (
            "K1 2 en 100 ms",
            Escaladas::K1 {
                e: 2,
                ventana_ns: 100_000_000,
            },
        ),
    ]
}

const ESPERAS_MS: [u64; 4] = [0, 1, 2, 5];

/// `cargo test -p sam17-nucleo-modelo --release --test espera -- --ignored --nocapture`.
/// Imprime las tablas; no elige.
#[test]
#[ignore]
fn barrido_de_la_espera() {
    let duraciones = [270u64, 400, 1_000, 2_000, 3_000, 5_000, 10_000];
    println!("\nbloqueo transitorio del GPDMA1 (v3a5), 5 fases: escaladas max / reinicios del chip / plazos ajenos max por ranura");
    print!("  {:16} {:>6}", "regla", "espera");
    for d in duraciones {
        print!(" {:>11}", format!("{d} us"));
    }
    println!();
    for (nombre, regla) in reglas() {
        for espera in ESPERAS_MS {
            let mut cfg = con_espera(espera * 1_000_000);
            cfg.escaladas = regla;
            print!("  {nombre:16} {:>3} ms", espera);
            for d in duraciones {
                let sims = atasco(&cfg, d);
                let esc = sims.iter().map(|s| s.escaladas).max().unwrap();
                let rs = sims.iter().filter(|s| s.iwdg_reset_at.is_some()).count();
                let aj = sims
                    .iter()
                    .flat_map(|s| s.s.iter().map(|r| r.colateral))
                    .max()
                    .unwrap();
                assert!(sims.iter().all(|s| s.max_concurrent_esc <= 1));
                print!(" {:>11}", format!("{esc}/{rs}/{aj}"));
            }
            println!();
        }
    }

    println!("\ncanal que el reset no cura (ranura 2, a los 50 ms)");
    for (nombre, regla) in reglas() {
        for espera in ESPERAS_MS {
            let mut cfg = con_espera(espera * 1_000_000);
            cfg.escaladas = regla;
            let mut sim = Sim::new(cfg);
            sim.hw_at(
                ms(50),
                HwEv::Inject {
                    slot: 2,
                    kind: Inj::Stuck { persistente: true },
                },
            );
            sim.run_until(ms(400));
            let t0 = sim.primera("cstart_veneno", 2).unwrap();
            let ms_de =
                |t: Option<u64>| t.map_or("-".into(), |t| format!("{:.3}", (t - t0) as f64 / 1e6));
            let aj_max = (0..N)
                .filter(|&n| n != 2)
                .map(|n| sim.s[n].colateral)
                .max()
                .unwrap();
            println!(
                "  {nombre:16} {espera} ms: escaladas {} aplazadas {} tramas perdidas por vecina, max {aj_max}; denegada {} ms, reinicio {} ms",
                sim.escaladas,
                sim.aplazadas,
                ms_de(sim.primera("escalada_DENEGADA", 2)),
                ms_de(sim.iwdg_reset_at)
            );
        }
    }

    for (fuzz, stuck) in [("fuzz", 0.0), ("fuzz2", 0.8)] {
        let tasas = Tasas {
            hang: 15.0,
            stuck,
            p2: 30.0,
            late: 5.0,
        };
        println!("\n{fuzz}: cuelgues 15/s, atascos curables {stuck}/s, P2 30/s, tics tardios 5/s; {SEMILLAS} x 4 s");
        println!(
            "  {:16} {:>6} {:>9} {:>8} {:>10} {:>10} {:>10} {:>14} {:>9}",
            "regla",
            "espera",
            "reinicios",
            "muertas",
            "escaladas",
            "aplazadas",
            "denegadas",
            "ajenos/vecina",
            "max/rnr"
        );
        for (nombre, regla) in reglas() {
            for espera in ESPERAS_MS {
                let (mut rs, mut mu, mut esc, mut apl, mut den, mut aj, mut aj_max) =
                    (0, 0, 0, 0, 0, 0, 0);
                for seed in 1..=SEMILLAS {
                    let (mut sim, t_fin, _) = montar(seed, 4, tasas, 6_250_000, &|c: &mut Cfg| {
                        c.escaladas = regla;
                        c.espera_escalada_ns = espera * 1_000_000;
                        c.para_al_reiniciar = true;
                    });
                    sim.run_until(t_fin + ms(150));
                    rs += u32::from(sim.iwdg_reset_at.is_some());
                    mu += (0..N).filter(|&n| muerta(&sim, n)).count();
                    esc += sim.escaladas;
                    apl += sim.aplazadas;
                    den += sim.denegadas;
                    for s in &sim.s {
                        aj += s.colateral;
                        aj_max = aj_max.max(s.colateral);
                    }
                }
                println!(
                    "  {nombre:16} {espera:>3} ms {:>6}/{SEMILLAS} {mu:>8} {esc:>10} {apl:>10} {den:>10} {:>14.2} {aj_max:>9}",
                    rs,
                    f64::from(aj) / (SEMILLAS as f64 * N as f64)
                );
            }
        }
    }
}

/// Las tres candidatas de la ficha B tras la cuarta pasada, con la regla 6 en 1 s: sin espera y
/// las cotas de antes, y las dos esperas con la cota de `Reiniciando` que cada una pide.
fn propuestas() -> [(&'static str, u64, (u16, u16)); 3] {
    [
        ("sin espera, 200/100", 0, (200, 100)),
        ("1 ms, 200/112", 1, (200, 112)),
        ("2 ms, 200/120", 2, (200, 120)),
    ]
}

fn cfg_propuesta(espera_ms: u64, cotas: (u16, u16), msg: u16) -> Cfg {
    let mut cfg = con_espera(espera_ms * 1_000_000);
    cfg.escaladas = Escaladas::K1 {
        e: 6,
        ventana_ns: 1_000_000_000,
    };
    cfg.cotas = cotas;
    cfg.msg = [msg; N];
    cfg
}

/// `cargo test -p sam17-nucleo-modelo --release --test espera -- --ignored --nocapture propuesta`.
#[test]
#[ignore]
fn barrido_de_la_propuesta() {
    for msg in [25u16, 71] {
        let duraciones: &[u64] = if msg == 25 {
            &[
                1_000, 2_000, 3_000, 5_000, 7_000, 10_000, 12_000, 15_000, 20_000,
            ]
        } else {
            &[1_000, 3_000, 5_000, 10_000]
        };
        println!("\nbloqueo del GPDMA1, mensajes de {msg} B, 5 fases: escaladas max / reinicios / mayor hueco sin tramas validas (ms)");
        for (nombre, espera, cotas) in propuestas() {
            let cfg = cfg_propuesta(espera, cotas, msg);
            print!("  {nombre:20}");
            for &d in duraciones {
                let sims = atasco(&cfg, d);
                let esc = sims.iter().map(|s| s.escaladas).max().unwrap();
                let rs = sims.iter().filter(|s| s.iwdg_reset_at.is_some()).count();
                let hueco = sims
                    .iter()
                    .filter(|s| s.iwdg_reset_at.is_none())
                    .flat_map(|s| s.s.iter().map(|r| r.max_gap))
                    .max()
                    .map_or("-".to_string(), |g| format!("{:.2}", g as f64 / 1e6));
                print!(" {:>15}", format!("{} ms: {esc}/{rs}/{hueco}", d / 1000));
            }
            println!();
        }
    }

    println!("\nbloqueo de 1 ms y retencion de P2 no atomica de L en los 4 ms siguientes (41 arranques): reinicios");
    for (nombre, espera, cotas) in propuestas() {
        let cfg = cfg_propuesta(espera, cotas, 25);
        print!("  {nombre:20}");
        for l in [10_000u64, 11_000, 12_000] {
            print!(
                " L {} ms: {:>2}/41",
                l / 1000,
                reinicios_con_retencion(&cfg, l)
            );
        }
        println!();
    }

    println!("\ncanal que el reset no cura (ranura 2, a los 50 ms)");
    for (nombre, espera, cotas) in propuestas() {
        let mut sim = Sim::new(cfg_propuesta(espera, cotas, 25));
        sim.hw_at(
            ms(50),
            HwEv::Inject {
                slot: 2,
                kind: Inj::Stuck { persistente: true },
            },
        );
        sim.run_until(ms(400));
        let aj_max = (0..N)
            .filter(|&n| n != 2)
            .map(|n| sim.s[n].colateral)
            .max()
            .unwrap();
        println!(
            "  {nombre:20} escaladas {} tramas perdidas por vecina, max {aj_max}; reinicio a {:?} ms",
            sim.escaladas,
            sim.iwdg_reset_at.map(|t| (t - ms(50)) / 1_000_000)
        );
    }

    let tasas = Tasas {
        hang: 15.0,
        stuck: 0.8,
        p2: 30.0,
        late: 5.0,
    };
    println!("\nfuzz2 (atascos curables 0,8/s, una tasa inventada), {SEMILLAS} x 4 s: reinicios");
    for (nombre, espera, cotas) in propuestas() {
        let rs = (1..=SEMILLAS)
            .filter(|&seed| {
                let (mut sim, t_fin, _) = montar(seed, 4, tasas, 6_250_000, &|c: &mut Cfg| {
                    *c = Cfg {
                        para_al_reiniciar: true,
                        ..cfg_propuesta(espera, cotas, 25)
                    };
                });
                sim.run_until(t_fin + ms(150));
                sim.iwdg_reset_at.is_some()
            })
            .count();
        println!("  {nombre:20} {rs}/{SEMILLAS}");
    }
}
