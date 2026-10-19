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
