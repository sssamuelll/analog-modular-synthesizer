//! Los escenarios del modelo de seis ranuras (#444): primero la calibracion contra el banco,
//! despues el reloj del tic (acta del 2026-10-19: el reloj antes que la escalada).

use sam17_nucleo_core::transporte_j2::Estado;
use sam17_nucleo_modelo::motor::{ms, Cfg, HwEv, Inj, Sim, PERIODO_NS};

fn una_ranura() -> Cfg {
    let mut cfg = Cfg::base();
    cfg.active = [true, false, false, false, false, false];
    cfg
}

// --- calibracion ----------------------------------------------------------------------

#[test]
fn la_recuperacion_de_un_spi_envenenado_calibra_contra_el_banco() {
    // `tic_recupera`, fase A (EN-PLACA.md): desde el CSTART envenenado, vencida a los 123 us,
    // la recuperacion arranca a los 125, el SPI se resetea a los 126, HECHA a los 131 y el
    // siguiente CSTART a los 249. El simulador de la junta daba 124,5 / 125,5 / 127,6 / 131,5 /
    // 249,9: el modelo los reproduce a 0,15 us, y queda a 2 us del banco.
    let mut sim = Sim::new(una_ranura());
    sim.trace_arm = Some(0);
    sim.hw_at(
        ms(20),
        HwEv::Inject {
            slot: 0,
            kind: Inj::Hang,
        },
    );
    sim.run_until(ms(30));
    let t0 = sim
        .primera("cstart_veneno", 0)
        .expect("el veneno tiene que armarse");
    for (que, junta, banco) in [
        ("tic_vencida", 124.5, 123.0),
        ("rec_inicio", 125.5, 125.0),
        ("spi_reset", 127.6, 126.0),
        ("rec_hecha", 131.5, 131.0),
        ("cstart", 249.9, 249.0),
    ] {
        let t = sim.primera_desde(que, 0, t0 + 1).expect(que);
        let us = (t - t0) as f64 / 1000.0;
        assert!(
            (us - junta).abs() <= 0.15,
            "{que}: {us:.2} us contra {junta} de la junta"
        );
        assert!(
            (us - banco).abs() <= 2.0,
            "{que}: {us:.2} us contra {banco} del banco"
        );
    }
    assert_eq!(sim.s[0].recuperaciones, 1);
    assert_eq!(sim.s[0].muertas, 0);
}

#[test]
fn una_retencion_del_planificador_calibra_contra_tic_cota() {
    // `tic_cota` (EN-PLACA.md), cotas de 100 y 100 tics: la ranura sobrevive a una retencion de
    // P2 de 12 ms justo cuando vence, y muere con una de 14 ms.
    for (d_us, viva) in [(12_000u64, true), (14_000, false)] {
        let mut cfg = una_ranura();
        cfg.cotas = (100, 100);
        let mut sim = Sim::new(cfg);
        sim.hold_on_vencida = Some((0, vec![vec![(d_us * 1000, false)]]));
        sim.hw_at(
            ms(20),
            HwEv::Inject {
                slot: 0,
                kind: Inj::Hang,
            },
        );
        sim.run_until(ms(120));
        assert_eq!(
            sim.s[0].tic.estado() != Estado::Muerta,
            viva,
            "retencion de {d_us} us"
        );
    }
}

// --- el reloj del tic ------------------------------------------------------------------

/// Un P0 que retiene `delta_us` el tic de uno de cada `cada` periodos, entre `desde` y `hasta`.
fn tics_tarde(sim: &mut Sim, desde: u64, hasta: u64, cada: u64, delta_us: u64) {
    let mut k = desde / PERIODO_NS + 1;
    while k * PERIODO_NS < hasta {
        sim.hw_at(
            k * PERIODO_NS - 100,
            HwEv::P0 {
                dur: delta_us * 1000 + 100,
            },
        );
        k += cada;
    }
}

#[test]
fn con_tics_tardios_el_reloj_cuenta_los_periodos_de_la_pared() {
    // V3-LATE (a): sin fallos, un segundo de tics tardios. Tras cada entrada el reloj del tic
    // tiene que llevar contadas las actualizaciones del TIM7 que han pasado, ni una mas ni una
    // menos: un segundo de pared son 8 000 periodos, lleguen como lleguen las entradas. Con el
    // reloj del v3 anterior, uno de cada dos tics entre 63 y 124 us tarde daba x1,5; contando
    // entradas, los fundidos (130 y 200 us) dan menos.
    for cada in [2u64, 4] {
        for d in [40u64, 63, 100, 124, 130, 200] {
            let mut sim = Sim::new(Cfg::base());
            tics_tarde(&mut sim, ms(10), ms(1010), cada, d);
            let mut t = ms(10);
            while t <= ms(1010) {
                sim.run_until(t);
                assert_eq!(
                    sim.tics, sim.uevs_en_entrada,
                    "uno de cada {cada}, {d} us tarde, a los {t} ns"
                );
                t += 37_000;
            }
            assert!(
                sim.uevs_en_entrada >= 8_078,
                "el tic se paro: {}",
                sim.uevs_en_entrada
            );
            assert_eq!(sim.reloj_anomalo, 0);
        }
    }
}

#[test]
fn con_tics_tardios_la_cota_de_vencida_vence_en_tiempo_de_pared() {
    // V3-LATE (b): la ranura 2 se cuelga, P2 retiene al planificador y a la recuperacion 120 ms,
    // y uno de cada dos tics llega `d` us tarde. La cota de `Vencida` son 200 periodos (25 ms):
    // la ranura muere en la entrada que la pasa, ni antes (el reloj del v3 anterior la mataba a
    // los 16,75 ms con 63 a 124 us) ni mucho despues (con 130 y 200 us las actualizaciones se
    // funden, y contando entradas moriria a los ~50 ms).
    for d in [0u64, 60, 63, 70, 100, 124, 130, 200] {
        let mut sim = Sim::new(Cfg::base());
        sim.hold_on_vencida = Some((2, vec![vec![(120_000_000, false)]]));
        sim.hw_at(
            ms(30),
            HwEv::Inject {
                slot: 2,
                kind: Inj::Hang,
            },
        );
        if d > 0 {
            tics_tarde(&mut sim, ms(30) + 200_000, ms(170), 2, d);
        }
        sim.run_until(ms(200));
        let tv = sim.primera("tic_vencida", 2).expect("vence");
        let tm = sim.primera("muerta", 2).expect("muere");
        let muere_ms = (tm - tv) as f64 / 1e6;
        assert!(
            (25.0..=25.5).contains(&muere_ms),
            "{d} us tarde: muere a los {muere_ms:.3} ms de vencer"
        );
    }
}

// --- H5 ----------------------------------------------------------------------------------

#[test]
fn una_ranura_muerta_no_se_recupera() {
    // Papel v3, §2.2 (Halberg H5): la ranura 2 se cuelga y P2 retiene al planificador y a la
    // recuperacion 40 ms, mas que la cota de `Vencida` (25 ms). Cuando el planificador corre, el
    // `PlazoVencido` sigue en el anillo; la ranura ya esta `Muerta` y nadie la recupera.
    let mut sim = Sim::new(Cfg::base());
    sim.hold_on_vencida = Some((2, vec![vec![(40_000_000, false)]]));
    sim.hw_at(
        ms(30),
        HwEv::Inject {
            slot: 2,
            kind: Inj::Hang,
        },
    );
    sim.run_until(ms(100));
    assert_eq!(sim.s[2].tic.estado(), Estado::Muerta);
    assert_eq!(
        sim.primera("plan_pide_rec", 2),
        None,
        "el planificador no la pide"
    );
    assert_eq!(sim.primera("rec_inicio", 2), None);
    assert_eq!(sim.s[2].recuperaciones, 0);
}

#[test]
fn una_recuperacion_pedida_antes_de_morir_no_se_ejecuta() {
    // El planificador pide la recuperacion con la ranura viva, y una retencion de P2 que entra
    // justo despues la aplaza mas que la cota: cuando la recuperacion corre, la ranura ya esta
    // `Muerta` y no se toca.
    let mut sim = Sim::new(Cfg::base());
    sim.hw_at(
        ms(30),
        HwEv::Inject {
            slot: 2,
            kind: Inj::Hang,
        },
    );
    let mut t = ms(30);
    while sim.primera("plan_pide_rec", 2).is_none() {
        t += 200;
        sim.run_until(t);
        assert!(t < ms(31), "el planificador no pidio la recuperacion");
    }
    assert_eq!(sim.primera("rec_inicio", 2), None, "todavia no arranco");
    sim.hw_at(
        t,
        HwEv::P2 {
            dur: 40_000_000,
            atomic: false,
        },
    );
    sim.run_until(ms(100));
    assert_eq!(sim.s[2].tic.estado(), Estado::Muerta);
    assert_eq!(sim.primera("rec_inicio", 2), None);
    assert_eq!(sim.s[2].recuperaciones, 0);
}

// --- corridas largas -------------------------------------------------------------------

/// El fuzz de la junta, 30 semillas de 4 s: `cargo test -p sam17-nucleo-modelo --release --
/// --ignored --nocapture`. Sin presupuesto de escaladas ni supervisor: cuenta, y comprueba que
/// el reloj del tic sigue a la pared.
#[test]
#[ignore]
fn fuzz_de_la_junta() {
    use sam17_nucleo_modelo::fuzz::{montar, Tasas};
    for (nombre, stuck) in [("fuzz", 0.0), ("fuzz2", 0.8)] {
        let tasas = Tasas {
            hang: 15.0,
            stuck,
            p2: 30.0,
            late: 5.0,
        };
        let (mut muertas, mut escaladas, mut colateral) = (0u32, 0u32, 0u32);
        for seed in 1..=30 {
            let (mut sim, t_fin, _) = montar(seed, 4, tasas, 6_250_000, &|_| {});
            sim.run_until(t_fin);
            assert_eq!(sim.tics, sim.uevs_en_entrada, "{nombre} semilla {seed}");
            assert_eq!(sim.reloj_anomalo, 0, "{nombre} semilla {seed}");
            let m: u32 = sim.s.iter().map(|s| s.muertas).sum();
            let c: u32 = sim.s.iter().map(|s| s.colateral).sum();
            println!(
                "{nombre} semilla {seed:2}: muertas {m} escaladas {} colaterales {c} saltados {}",
                sim.escaladas, sim.periodos_saltados
            );
            muertas += m;
            escaladas += sim.escaladas;
            colateral += c;
        }
        println!("{nombre}: muertas {muertas} escaladas {escaladas} colaterales {colateral}");
    }
}
