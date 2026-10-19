//! Los escenarios de la tercera pasada de la junta (`sim/junta3/src/v3.rs`) con K1 a K5 puestos,
//! contra lo que el papel v3 dice en §2.2, §2.5, §2.10 y §2.11. Cada uno imprime sus cifras
//! (`--nocapture`).

use sam17_nucleo_core::transporte_j2::Estado;
use sam17_nucleo_modelo::motor::{ms, Cfg, HwEv, Inj, Sim, N, PERIODO_NS};

fn muerta(sim: &Sim, n: usize) -> bool {
    sim.s[n].tic.estado() == Estado::Muerta
}

fn ms_desde(t: Option<u64>, t0: u64) -> String {
    t.map_or("-".into(), |t| {
        format!("{:.3}", (t as f64 - t0 as f64) / 1e6)
    })
}

/// Plazos propios y ajenos de cada ranura desde `t0`.
fn plazos_desde(sim: &Sim, t0: u64) -> [(usize, usize); N] {
    let mut r = [(0, 0); N];
    for (n, x) in r.iter_mut().enumerate() {
        *x = (
            sim.cuenta_desde("tic_vencida", n as i32, t0),
            sim.cuenta_desde("plazo_ajeno", n as i32, t0),
        );
    }
    r
}

#[test]
fn v3perm_los_tics_tardios_no_niegan_la_escalada_que_cura() {
    // §2.5: una averia comun que el reset cura da una escalada. Con el permiso del v3 anterior,
    // tres tics tardios la negaban; con K1, el presupuesto es del controlador.
    for k in [0u64, 3, 4] {
        let mut sim = Sim::new(Cfg::base());
        for i in 0..k {
            let t = ms(50 + 100 * i);
            sim.hw_at(t / PERIODO_NS * PERIODO_NS - 100, HwEv::P0 { dur: 110_100 });
        }
        sim.hw_at(
            ms(600),
            HwEv::Inject {
                slot: 2,
                kind: Inj::Stuck { persistente: false },
            },
        );
        sim.run_until(ms(800));
        let t0 = sim.primera("cstart_veneno", 2).unwrap();
        let p = plazos_desde(&sim, t0);
        println!(
            "v3perm K={k}: escaladas {} denegadas {} plazos (propios, ajenos) desde el atasco {p:?} reinicio {}",
            sim.escaladas,
            sim.denegadas,
            ms_desde(sim.iwdg_reset_at, t0)
        );
        assert_eq!((sim.escaladas, sim.denegadas), (1, 0), "K = {k}");
        assert_eq!(sim.iwdg_reset_at, None, "K = {k}");
        for (n, &(propios, _)) in p.iter().enumerate() {
            assert!(!muerta(&sim, n), "K = {k}: ranura {n}");
            if n != 2 {
                assert_eq!(propios, 0, "K = {k}: la vecina {n} puntua la escalada");
            }
        }
    }
}

#[test]
fn v3a4_un_canal_que_el_reset_no_cura_gasta_e_escaladas_y_reinicia_el_chip() {
    // §2.5 y §2.10: con K1, E escaladas son E tramas perdidas por vecina con bajada; despues la
    // ranura muere por la cota de `Reiniciando` y el supervisor reinicia el chip (§2.11).
    let cfg = Cfg::base();
    let (w, p_s, t_iwdg) = (cfg.sup_w_ns, cfg.feed_period_ns, cfg.iwdg_ns);
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
    let p = plazos_desde(&sim, t0);
    let reinicio = sim.iwdg_reset_at.expect("reinicia el chip");
    println!(
        "v3a4: escaladas {} denegadas {} (primera {} ms) Muerta {} ms deja de alimentar {} ms reinicio {} ms; CPU de P4 {:.3} ms; plazos {p:?}",
        sim.escaladas,
        sim.denegadas,
        ms_desde(sim.primera("escalada_DENEGADA", 2), t0),
        ms_desde(sim.primera("muerta", 2), t0),
        ms_desde(sim.first_refusal, t0),
        ms_desde(Some(reinicio), t0),
        sim.busy[4] as f64 / 1e6
    );
    assert_eq!(sim.escaladas, 3);
    assert!(sim.denegadas >= 1);
    assert_eq!(sim.max_concurrent_esc, 1);
    assert!(muerta(&sim, 2));
    assert_eq!(sim.supervisor.causa(), Some(2));
    for (n, &(propios, ajenos)) in p.iter().enumerate() {
        if n != 2 {
            assert!(!muerta(&sim, n), "vecina {n}");
            assert_eq!(propios, 0, "la vecina {n} puntua la escalada");
            assert!(ajenos <= 3, "vecina {n}: {ajenos} tramas perdidas");
        }
    }
    let sello = sim.s[2].last_seal_t;
    assert!(reinicio - sello + p_s >= w + t_iwdg && reinicio - sello <= w + t_iwdg + p_s);
}

#[test]
fn v3a4x2_dos_canales_incurables_y_un_cuelgue_ordinario() {
    // Los dos atascos gastan el presupuesto y mueren; el cuelgue ordinario de la ranura 5 no
    // necesita escalar y se recupera.
    let mut sim = Sim::new(Cfg::base());
    for slot in [1, 4] {
        sim.hw_at(
            ms(50),
            HwEv::Inject {
                slot,
                kind: Inj::Stuck { persistente: true },
            },
        );
    }
    sim.hw_at(
        ms(51),
        HwEv::Inject {
            slot: 5,
            kind: Inj::Hang,
        },
    );
    sim.run_until(ms(400));
    let t0 = sim.primera("cstart_veneno", -1).unwrap();
    println!(
        "v3a4x2: escaladas {} denegadas {} Muerta r1 {} r4 {} r5 {} ms; reinicio {} ms (causa {:?}); recuperaciones r5 {}; latencia max de la recuperacion {:.3} ms",
        sim.escaladas,
        sim.denegadas,
        ms_desde(sim.primera("muerta", 1), t0),
        ms_desde(sim.primera("muerta", 4), t0),
        ms_desde(sim.primera("muerta", 5), t0),
        ms_desde(sim.iwdg_reset_at, t0),
        sim.supervisor.causa(),
        sim.s[5].recuperaciones,
        sim.rec_lat_max as f64 / 1e6
    );
    assert!(sim.escaladas <= 3);
    assert_eq!(sim.max_concurrent_esc, 1);
    assert!(muerta(&sim, 1) && muerta(&sim, 4));
    assert!(!muerta(&sim, 5), "el cuelgue ordinario se recupera");
    assert!(sim.iwdg_reset_at.is_some());
}

#[test]
fn v3a5_un_bloqueo_transitorio_del_gpdma1() {
    // Sin afirmacion propia en el papel salvo «no hay escaladas solapadas» (§2.5): se imprime la
    // tabla y se comprueba eso.
    for d in [
        100u64, 270, 400, 1_000, 2_000, 5_000, 10_000, 12_000, 13_000, 14_000, 20_000,
    ] {
        let (mut esc, mut den, mut mu, mut rs) = (0u32, 0u32, 0usize, 0u32);
        for fase in (0..125u64).step_by(25) {
            let mut sim = Sim::new(Cfg::base());
            let t_ini = ms(50) + fase * 1000 + 10_000;
            sim.hw_at(
                t_ini,
                HwEv::StallStart {
                    until: t_ini + d * 1000,
                },
            );
            sim.run_until(ms(250));
            assert!(sim.max_concurrent_esc <= 1, "D = {d} us, fase {fase}");
            esc = esc.max(sim.escaladas);
            den = den.max(sim.denegadas);
            mu = mu.max((0..N).filter(|&n| muerta(&sim, n)).count());
            rs += u32::from(sim.iwdg_reset_at.is_some());
        }
        println!(
            "v3a5 D = {d:6} us: escaladas max {esc} denegadas max {den} muertas max {mu} reinicios {rs}/5"
        );
    }
}

#[test]
fn v3a8_una_retencion_mientras_escala_reprograma_no_congela_sin_cota() {
    // §2.2 (K3): con la marca en la maquina, una retencion de P2 justo tras la seccion critica
    // de la escalada ya no deja ranuras congeladas sin cota: las `Vencida` siguen contando, y si
    // la retencion pasa de la ventana del supervisor, el chip se reinicia.
    for d in [5u64, 14, 30, 100] {
        let mut sim = Sim::new(Cfg::base());
        sim.hold_on_escalada = Some(vec![vec![(d * 1_000_000, false)]]);
        sim.hw_at(
            ms(50),
            HwEv::Inject {
                slot: 2,
                kind: Inj::Stuck { persistente: false },
            },
        );
        sim.run_until(ms(50) + ms(d) / 2);
        let mitad: Vec<String> = sim
            .s
            .iter()
            .map(|s| format!("{}{:?}", if s.sucia { "S:" } else { "" }, s.tic.estado()))
            .collect();
        sim.run_until(ms(50 + d + 150));
        let t0 = sim.primera("cstart_veneno", 2).unwrap();
        let muertas = (0..N).filter(|&n| muerta(&sim, n)).count();
        println!(
            "v3a8 D = {d:3} ms: a mitad {mitad:?}; muertas {muertas} (primera {} ms) reinicio {} ms",
            ms_desde(sim.primera("muerta", -1), t0),
            ms_desde(sim.iwdg_reset_at, t0)
        );
        if d <= 14 {
            assert_eq!(muertas, 0, "D = {d} ms");
            assert_eq!(sim.iwdg_reset_at, None, "D = {d} ms");
        }
        if d == 100 {
            assert!(
                sim.iwdg_reset_at.is_some(),
                "D = 100 ms: nada queda congelado"
            );
        }
    }
}

#[test]
fn v3sucia2_ninguna_ranura_arma_sobre_canales_sin_programar() {
    // §2.2 (K3): 0 de 126 desfases arman sobre los canales que el reset por RCC dejo a cero, y
    // las vecinas no se apuntan plazos propios.
    let (mut casos, mut propios) = (0, 0);
    for d in 500..626u64 {
        let mut sim = Sim::new(Cfg::base());
        sim.hw_at(
            ms(50),
            HwEv::Inject {
                slot: 5,
                kind: Inj::Stuck { persistente: false },
            },
        );
        sim.hw_at(
            ms(50) + 130_000,
            HwEv::P2 {
                dur: d * 1000,
                atomic: false,
            },
        );
        sim.run_until(ms(70));
        casos += u32::from(sim.s.iter().any(|s| s.arm_sin_prog > 0));
        propios += sim.s[..5].iter().map(|s| s.plazos).sum::<u32>();
    }
    println!("v3sucia2: armados sobre canal sin programar en {casos} de 126; plazos propios de r0..r4 {propios}");
    assert_eq!(casos, 0);
    assert_eq!(propios, 0);
}

#[test]
fn v3ident2_ninguna_hecha_rancia_rearma_y_desenchufar_no_reinicia() {
    // §2.2 (K4): la ranura 3 pierde la identidad; vuelve a los 70 ms; a los 110 ms se cuelga.
    // Ninguna HECHA de antes rearma, el cuelgue da un plazo propio y se recupera, y quitar el
    // modulo no reinicia el chip.
    for (d, ini) in [
        (0u64, 12_000u64),
        (150, 12_000),
        (150, 13_000),
        (150, 14_000),
        (150, 15_000),
        (150, 16_000),
        (150, 17_000),
        (150, 18_000),
        (150, 20_000),
        (400, 15_000),
    ] {
        let mut cfg = Cfg::base();
        cfg.msg = [25, 25, 25, 9, 25, 25];
        let mut sim = Sim::new(cfg);
        sim.hw_at(
            ms(50) - 1_000,
            HwEv::Ident {
                slot: 3,
                present: false,
            },
        );
        if d > 0 {
            sim.hw_at(
                ms(50) + ini,
                HwEv::P2 {
                    dur: d * 1000,
                    atomic: false,
                },
            );
        }
        sim.run_until(ms(65));
        let (h, c, e) = (
            sim.s[3].rec_hecha,
            sim.s[3].rec_en_curso,
            sim.s[3].tic.estado(),
        );
        sim.hw_at(
            ms(70),
            HwEv::Ident {
                slot: 3,
                present: true,
            },
        );
        sim.run_until(ms(100));
        let p_antes = sim.s[3].plazos;
        sim.hold_on_vencida = Some((3, vec![vec![(300_000, false)]]));
        sim.hw_at(
            ms(110),
            HwEv::Inject {
                slot: 3,
                kind: Inj::Hang,
            },
        );
        sim.run_until(ms(250));
        let rancias = sim.cuenta_desde("HECHA_RANCIA_rearma", 3, 0);
        println!(
            "v3ident2 P2 {d} us a 50,{:03} ms: a 65 ms {e:?} HECHA {h} EN_CURSO {c} | cuelgue: plazos propios {} rearmes rancios {rancias} estado {:?} reinicio {:?}",
            ini / 1000,
            sim.s[3].plazos - p_antes,
            sim.s[3].tic.estado(),
            sim.iwdg_reset_at
        );
        assert_eq!(rancias, 0);
        assert_eq!(sim.s[3].plazos - p_antes, 1);
        assert!(!muerta(&sim, 3));
        assert_eq!(sim.iwdg_reset_at, None);
    }
}

#[test]
fn desenchufar_en_cualquier_fase_no_reinicia_el_chip() {
    // §2.11 y R-H8: el supervisor solo lee el sello de las ranuras con modulo. La ranura 3 se
    // desenchufa en 25 fases del periodo y no vuelve.
    for f in (0..125u64).step_by(5) {
        let mut sim = Sim::new(Cfg::base());
        sim.hw_at(
            ms(50) + f * 1000,
            HwEv::Ident {
                slot: 3,
                present: false,
            },
        );
        sim.run_until(ms(400));
        assert_eq!(sim.iwdg_reset_at, None, "fase {f} us");
        assert!(!muerta(&sim, 3), "fase {f} us");
    }
}
