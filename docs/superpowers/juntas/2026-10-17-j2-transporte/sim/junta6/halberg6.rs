//! Halberg, sexta pasada: x17 a x20, sobre la copia instrumentada del modelo (69754fe).
//! cargo test -p sam17-nucleo-modelo --release --test halberg6 -- --ignored --nocapture x17

use sam17_nucleo_core::transporte_j2::Estado;
use sam17_nucleo_modelo::motor::{ms, Cfg, Escaladas, HwEv, Inj, Sim, N};

const MS: u64 = 1_000_000;
const T_INI: u64 = 60_010_000;

fn cfg_b() -> Cfg {
    let mut c = Cfg::base();
    c.espera_escalada_ns = MS;
    c.escaladas = Escaladas::K1 {
        e: 6,
        ventana_ns: 1_000_000_000,
    };
    c.cotas = (200, 112);
    c.despierta_el_tic = true;
    c
}

fn muertas(sim: &Sim) -> Vec<usize> {
    (0..N)
        .filter(|&n| sim.s[n].tic.estado() == Estado::Muerta)
        .collect()
}

fn bloqueo(sim: &mut Sim, t: u64, d: u64) {
    sim.hw_at(t, HwEv::StallStart { until: t + d });
}

fn resumen(nombre: &str, sim: &Sim) {
    println!(
        "  {nombre:46} escaladas {} aplazadas {} denegadas {} muertas {:?} reinicio {:?} ms | P3 {:.2} ms, P4 {:.2} ms (de pendiente a terminado)",
        sim.escaladas,
        sim.aplazadas,
        sim.denegadas,
        muertas(sim),
        sim.iwdg_reset_at.map(|t| t as f64 / 1e6),
        sim.plan_term_max as f64 / 1e6,
        sim.rec_term_max as f64 / 1e6,
    );
}

/// x17: la vuelta del contador de 32 bits del tic. El tic vuelve a 0 a los ~100 ms.
#[test]
#[ignore]
fn x17_vuelta_del_contador() {
    let vuelta = 0u32.wrapping_sub(800);
    println!();
    println!("x17: dos bloqueos de 1 ms, a los 20 y a los 150 ms; el contador del tic da la vuelta a los ~100 ms");
    for (nombre, tics0, p64) in [
        ("sin vuelta", 0u32, false),
        ("con vuelta, modelo tal cual", vuelta, false),
        ("con vuelta, presupuesto en 64 bits (como fw)", vuelta, true),
    ] {
        let mut sim = Sim::new(cfg_b());
        sim.tics = tics0;
        sim.presupuesto_64 = p64;
        bloqueo(&mut sim, ms(20), MS);
        bloqueo(&mut sim, ms(150), MS);
        sim.run_until(ms(400));
        resumen(nombre, &sim);
        let apl: Vec<_> = sim
            .marks
            .iter()
            .filter(|m| m.what == "escalada_aplazada" && m.t > ms(150))
            .map(|m| (m.slot, m.t as f64 / 1e6, m.x))
            .take(3)
            .collect();
        let desp = sim
            .marks
            .iter()
            .filter(|m| m.what == "tic_despierta_rec" && m.t > ms(150))
            .count();
        println!("      aplazadas tras la vuelta (ranura, t ms, hasta_us): {apl:?}; despertares del tic tras 150 ms: {desp}");
    }
    println!("x17c: un solo bloqueo de 1 ms que empieza 0,3 ms antes de la vuelta");
    for (nombre, tics0) in [("sin vuelta", 0u32), ("con vuelta", vuelta)] {
        let mut sim = Sim::new(cfg_b());
        sim.tics = tics0;
        bloqueo(&mut sim, ms(100) - 300_000, MS);
        sim.run_until(ms(400));
        resumen(nombre, &sim);
    }
}

/// x18: P2 retiene a P4 entre la lectura del reloj y la decision del presupuesto.
fn retenida(stale: bool, l1: u64, l2: u64) -> (Sim, Option<i32>) {
    let mut base = Sim::new(cfg_b());
    base.paso_reloj = true;
    bloqueo(&mut base, T_INI, MS);
    base.run_until(ms(250));
    let te = base
        .marks
        .iter()
        .find(|m| m.what == "escalada")
        .map(|m| m.t)
        .expect("escala");
    let mut sim = Sim::new(cfg_b());
    sim.paso_reloj = true;
    sim.reloj_antes_de_decidir = stale;
    bloqueo(&mut sim, T_INI, MS);
    sim.run_until(te + 1_000);
    sim.hold_on_decide = Some((usize::MAX, vec![vec![(l1, false)]]));
    let mut x = None;
    let mut t = te + 1_000;
    while t < ms(250) {
        t += 10_000;
        sim.run_until(t);
        if let Some(m) = sim
            .marks
            .iter()
            .find(|m| m.what == "retencion_entre_reloj_y_decision")
        {
            x = Some(m.slot);
            break;
        }
    }
    if let (Some(k), true) = (x, l2 > 0) {
        sim.hold_on_rec = Some((k as usize, vec![vec![(l2, false)]]));
    }
    sim.run_until(ms(250));
    (sim, x)
}

#[test]
#[ignore]
fn x18_reloj_leido_antes_de_la_retencion() {
    println!();
    println!("x18: bloqueo de 1 ms; tras la primera escalada, P2 (L1) entre la lectura del reloj y la decision; L2 al arrancar la recuperacion despertada");
    for stale in [false, true] {
        if stale {
            println!(" reloj leido antes de la retencion (orden de recupera() en fw)");
        } else {
            println!(" reloj leido al decidir (el modelo)");
        }
        for l1 in [2u64, 6, 11] {
            for l2 in [0u64, 2, 3, 6, 11] {
                let (sim, x) = retenida(stale, l1 * MS + 500_000, l2 * MS);
                let legal = sim.plan_term_max <= 12 * MS && sim.rec_term_max <= 12 * MS;
                let k = x.unwrap_or(-1);
                let tl: Vec<(&str, f64)> = sim
                    .marks
                    .iter()
                    .filter(|m| {
                        m.slot == k
                            && m.t > T_INI
                            && matches!(
                                m.what,
                                "rec_inicio" | "escalada_aplazada" | "escalada" | "rec_hecha" | "muerta"
                            )
                    })
                    .map(|m| (m.what, (m.t - T_INI) as f64 / 1e6))
                    .take(6)
                    .collect();
                let desp = sim
                    .marks
                    .iter()
                    .find(|m| m.what == "tic_despierta_rec")
                    .map(|m| (m.t - T_INI) as f64 / 1e6);
                println!(
                    "  L1 {:>4.1} L2 {:>2} ms: legal {legal:5} reinicio {:5} ranura {k} | P3 {:.2} P4 {:.2} ms | despierta {desp:?} | {tl:?}",
                    (l1 * MS + 500_000) as f64 / 1e6,
                    l2,
                    sim.iwdg_reset_at.is_some(),
                    sim.plan_term_max as f64 / 1e6,
                    sim.rec_term_max as f64 / 1e6,
                );
            }
        }
    }
}

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 >> 12;
        self.0 ^= self.0 << 25;
        self.0 ^= self.0 >> 27;
        self.0.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }
    fn u(&mut self) -> f64 {
        (self.next() >> 11) as f64 / (1u64 << 53) as f64
    }
}

/// x19: fuzz. Un bloqueo de 0,3 a 5,5 ms, de 1 a 3 retenciones de P2 no atomicas de 1 a 11,95 ms
/// alrededor, y la mitad de las veces un SPI envenenado. Legal: P3 y P4, de pendiente a
/// terminado, como mucho 12 ms medidos en la corrida.
#[test]
#[ignore]
fn x19_fuzz_legal() {
    for tic in [true, false] {
        println!();
        println!("despertador: {}", if tic { "el tic" } else { "el planificador (quinta pasada)" });
        x19(tic);
    }
}

fn x19(tic: bool) {
    let semillas = 4000u64;
    let (mut leg, mut leg_r, mut ileg, mut ileg_r) = (0u32, 0u32, 0u32, 0u32);
    let mut gap_max = 0u64;
    let mut ejemplos = Vec::new();
    let (mut hechas, mut sin_trama) = (0u32, 0u32);
    for seed in 1..=semillas {
        let mut r = Rng(0x9E37_79B9_7F4A_7C15 ^ seed.wrapping_mul(0xD1B5_4A32_D192_ED03));
        let mut cfg = cfg_b();
        cfg.despierta_el_tic = tic;
        let mut sim = Sim::new(cfg);
        let t_b = T_INI + (r.u() * 1e6) as u64;
        let d = 300_000 + (r.u() * 5.2e6) as u64;
        bloqueo(&mut sim, t_b, d);
        let k = 1 + r.next() % 3;
        let mut ret = Vec::new();
        for _ in 0..k {
            let l = MS + (r.u() * 10.95e6) as u64;
            let t = t_b - MS + (r.u() * 21e6) as u64;
            sim.hw_at(t, HwEv::P2 { dur: l, atomic: false });
            ret.push(((t as i64 - t_b as i64) as f64 / 1e6, l as f64 / 1e6));
        }
        if r.next() % 2 == 0 {
            let slot = (r.next() % N as u64) as usize;
            let t = t_b + (r.u() * 20e6) as u64;
            sim.hw_at(t, HwEv::Inject { slot, kind: Inj::Hang });
        }
        sim.run_until(ms(250));
        let legal = sim.plan_term_max <= 12 * MS && sim.rec_term_max <= 12 * MS;
        let reinicia = sim.iwdg_reset_at.is_some();
        hechas += sim.hechas;
        sin_trama += sim.hecha_sin_trama;
        if legal {
            leg += 1;
            if reinicia {
                leg_r += 1;
                if ejemplos.len() < 5 {
                    ejemplos.push((
                        seed,
                        d as f64 / 1e6,
                        ret.clone(),
                        sim.plan_term_max as f64 / 1e6,
                        sim.rec_term_max as f64 / 1e6,
                        muertas(&sim),
                    ));
                }
            } else {
                gap_max = gap_max.max(sim.s.iter().map(|s| s.max_gap).max().unwrap());
            }
        } else {
            ileg += 1;
            ileg_r += u32::from(reinicia);
        }
    }
    println!();
    println!("x19: {semillas} corridas. Legales {leg}, de ellas reinician {leg_r}; ilegales {ileg}, reinician {ileg_r}. Mayor hueco sin tramas en las legales que sobreviven: {:.2} ms", gap_max as f64 / 1e6);
    for e in ejemplos {
        println!("  legal y reinicia: {e:?}");
    }
    println!("  recuperaciones terminadas {hechas}, sin trama fresca en el buzon al terminar {sin_trama}");
}

/// x20: un bloqueo largo con un tren de retenciones legales por nivel.
#[test]
#[ignore]
fn x20_tren() {
    println!();
    println!("x20: bloqueo de D a T_INI; P2 en tren: 11,4 ms de CPU cada 12,1 ms, 8 veces");
    for d in [6u64, 30, 60, 80] {
        for tren in [false, true] {
            let mut sim = Sim::new(cfg_b());
            bloqueo(&mut sim, T_INI, d * MS);
            if tren {
                for i in 0..8u64 {
                    sim.hw_at(
                        T_INI + i * 12_100_000,
                        HwEv::P2 {
                            dur: 11_400_000,
                            atomic: false,
                        },
                    );
                }
            }
            sim.run_until(ms(400));
            let gap = sim.s.iter().map(|s| s.max_gap).max().unwrap();
            resumen(
                &format!("D {d} ms, tren {tren}, hueco max {:.2} ms", gap as f64 / 1e6),
                &sim,
            );
        }
    }
}

/// x21: barrido anclado. Bloqueo de 1 ms; L1 empieza alrededor de la primera aplazada; L2 entra
/// cuando la recuperacion arranca la ranura k despues de esa aplazada. Legal: P3 y P4 de
/// pendiente a terminado <= 12 ms medidos.
#[test]
#[ignore]
fn x21_barrido_anclado() {
    for tic in [true, false] {
        let mut cfg = cfg_b();
        cfg.despierta_el_tic = tic;
        let mut base = Sim::new(cfg.clone());
        bloqueo(&mut base, T_INI, MS);
        base.run_until(ms(250));
        let a = base
            .marks
            .iter()
            .find(|m| m.what == "escalada_aplazada")
            .map(|m| m.t)
            .unwrap();
        let (mut n, mut leg, mut leg_r, mut ileg_r) = (0, 0, 0, 0);
        let mut peor = None;
        for off in (0..=16).map(|i| i as i64 * 100_000 - 400_000) {
            for l1 in [0u64, 6_000_000, 9_000_000, 11_000_000, 11_800_000] {
                for l2 in [0u64, 3_000_000, 6_000_000, 9_000_000, 11_800_000] {
                    for k in 0..N {
                        let mut sim = Sim::new(cfg.clone());
                        bloqueo(&mut sim, T_INI, MS);
                        if l1 > 0 {
                            sim.hw_at((a as i64 + off) as u64, HwEv::P2 { dur: l1, atomic: false });
                        }
                        sim.run_until(a + 1_000);
                        if l2 > 0 {
                            sim.hold_on_rec = Some((k, vec![vec![(l2, false)]]));
                        }
                        sim.run_until(ms(250));
                        n += 1;
                        let legal = sim.plan_term_max <= 12 * MS && sim.rec_term_max <= 12 * MS;
                        let r = sim.iwdg_reset_at.is_some();
                        if legal {
                            leg += 1;
                            if r {
                                leg_r += 1;
                                if peor.is_none() {
                                    peor = Some((off, l1, l2, k, sim.plan_term_max, sim.rec_term_max));
                                }
                            }
                        } else if r {
                            ileg_r += 1;
                        }
                    }
                }
            }
        }
        println!();
        println!(
            "x21 despertador {}: {n} corridas, legales {leg}, legales que reinician {leg_r}, ilegales que reinician {ileg_r}; primera legal que reinicia {peor:?}",
            if tic { "el tic" } else { "el planificador" }
        );
    }
}

#[test]
#[ignore]
fn x18b_traza() {
    let (sim, x) = retenida(true, 11_500_000, 3_000_000);
    let k = x.unwrap();
    println!();
    println!("x18b: ranura {k}, reloj leido antes de L1 = 11,5 ms, L2 = 3 ms; tiempos desde el bloqueo (ms)");
    for m in sim.marks.iter().filter(|m| (m.slot == k || m.slot == -1) && m.t > T_INI && m.t < T_INI + 200 * MS) {
        if matches!(m.what, "rec_inicio" | "escalada_aplazada" | "escalada" | "rec_hecha" | "muerta" | "tic_despierta_rec" | "retencion_entre_reloj_y_decision" | "iwdg_reset" | "tic_vencida" | "supervisor_deja_de_alimentar") {
            println!("  {:>9.3} {:34} x {}", (m.t - T_INI) as f64 / 1e6, m.what, m.x);
        }
    }
    let muertas_t: Vec<_> = sim.marks.iter().filter(|m| m.what == "muerta").map(|m| (m.slot, (m.t - T_INI) as f64 / 1e6)).collect();
    println!("  muertas {muertas_t:?}; P3 {:.3} ms, P4 {:.3} ms, rec_debida_max {:.3} ms, plan_lat_max {:.3} ms", sim.plan_term_max as f64 / 1e6, sim.rec_term_max as f64 / 1e6, sim.rec_debida_max as f64 / 1e6, sim.plan_lat_max as f64 / 1e6);
}
