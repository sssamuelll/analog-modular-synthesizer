//! El barrido del presupuesto de escaladas (K1) con los dos fuzz de la junta (30 semillas de 4 s):
//! `cargo test -p sam17-nucleo-modelo --release --test barrido -- --ignored --nocapture`.
//! Imprime la tabla; no elige `E`.

use sam17_nucleo_core::transporte_j2::Estado;
use sam17_nucleo_modelo::fuzz::{montar, Tasas};
use sam17_nucleo_modelo::motor::{ms, Cfg, Escaladas, HwEv, Inj, Sim, N};

const SEMILLAS: u64 = 30;

fn reglas() -> Vec<(String, Escaladas)> {
    let mut r = vec![
        ("siempre".to_string(), Escaladas::Siempre),
        (
            "v2 (3 en 8000 tics)".to_string(),
            Escaladas::V2 {
                e: 3,
                ventana: 8000,
            },
        ),
    ];
    for (nombre, ventana_ns) in [
        ("100 ms", 100_000_000u64),
        ("1 s", 1_000_000_000),
        ("10 s", 10_000_000_000),
    ] {
        for e in [1usize, 2, 3, 4, 6] {
            r.push((
                format!("K1 E={e} {nombre}"),
                Escaladas::K1 { e, ventana_ns },
            ));
        }
    }
    r
}

#[test]
#[ignore]
fn barrido_del_presupuesto_con_el_fuzz_de_la_junta() {
    for (fuzz, stuck) in [("fuzz", 0.0), ("fuzz2", 0.8)] {
        let tasas = Tasas {
            hang: 15.0,
            stuck,
            p2: 30.0,
            late: 5.0,
        };
        println!("\n{fuzz}: cuelgues 15/s, atascos curables {stuck}/s, P2 30/s, tics tardios 5/s; {SEMILLAS} x 4 s");
        println!(
            "  {:24} {:>9} {:>8} {:>10} {:>10} {:>9} {:>14} {:>9}",
            "regla",
            "reinicios",
            "muertas",
            "escaladas",
            "denegadas",
            "ajenos",
            "ajenos/vecina",
            "max/rnr"
        );
        for (nombre, regla) in reglas() {
            let (mut rs, mut mu, mut esc, mut den, mut aj, mut aj_max) = (0, 0, 0, 0, 0, 0);
            for seed in 1..=SEMILLAS {
                let (mut sim, t_fin, _) = montar(seed, 4, tasas, 6_250_000, &|c: &mut Cfg| {
                    c.escaladas = regla;
                    c.para_al_reiniciar = true;
                });
                // Lo que muere al final tiene W + T_IWDG para reiniciar el chip.
                sim.run_until(t_fin + ms(150));
                rs += u32::from(sim.iwdg_reset_at.is_some());
                mu += sim
                    .s
                    .iter()
                    .filter(|s| s.tic.estado() == Estado::Muerta)
                    .count();
                esc += sim.escaladas;
                den += sim.denegadas;
                for s in &sim.s {
                    aj += s.colateral;
                    aj_max = aj_max.max(s.colateral);
                }
            }
            println!(
                "  {nombre:24} {:>6}/{SEMILLAS} {mu:>8} {esc:>10} {den:>10} {aj:>9} {:>14.2} {aj_max:>9}",
                rs,
                f64::from(aj) / (SEMILLAS as f64 * N as f64)
            );
        }
    }
}

#[test]
#[ignore]
fn barrido_un_canal_que_el_reset_no_cura() {
    // Tramas perdidas por vecina hasta que se acaba el presupuesto, y cuando reinicia el chip.
    println!("\ncanal que el reset no cura (ranura 2, a los 50 ms)");
    for (nombre, regla) in reglas() {
        let mut cfg = Cfg::base();
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
        let fin = sim.primera("escalada_DENEGADA", 2).unwrap_or(u64::MAX);
        let perdidas: Vec<usize> = (0..N)
            .filter(|&n| n != 2)
            .map(|n| {
                sim.marks
                    .iter()
                    .filter(|m| m.what == "plazo_ajeno" && m.slot == n as i32 && m.t < fin)
                    .count()
            })
            .collect();
        let ms_de =
            |t: Option<u64>| t.map_or("-".into(), |t| format!("{:.3}", (t - t0) as f64 / 1e6));
        println!(
            "  {nombre:24} escaladas {:2} tramas perdidas por vecina {perdidas:?} denegada {} ms reinicio {} ms",
            sim.escaladas,
            ms_de(sim.primera("escalada_DENEGADA", 2)),
            ms_de(sim.iwdg_reset_at)
        );
    }
}
