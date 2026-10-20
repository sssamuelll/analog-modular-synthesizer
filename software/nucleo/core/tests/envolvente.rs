//! El generador de envolvente: la maquina de cuatro etapas, cerrada entre bordes.
//! Papel: `docs/superpowers/specs/2026-09-02-generador-de-envolvente-design.md`,
//! §2 (las etapas terminan por cuenta de ticks), §2.1 (ataque RC truncado),
//! §2.2 (decaimiento y relajacion a -60 dB), §2.3 (sostenido vivo, sin filtro),
//! §3.1 (los tres bordes).

use sam17_nucleo_core::envolvente::{
    Borde, Entrada, Generadores, Parametros, Salida, CANALES, FUERZA_REPARACION,
};
use sam17_nucleo_core::envolvente::{Etapa, Generador, Tiempos, NIVEL_OCIOSO, TICKS_POR_MS};
use sam17_nucleo_core::escritor::{amplitud, factores_paneo, ganancia_fuerza};
use sam17_nucleo_core::fuerza::Fuerza;

const T: Tiempos = Tiempos {
    ataque_ms: 10,
    decaimiento_ms: 20,
    relajacion_ms: 30,
};

fn tiempos(a: u32, d: u32, r: u32) -> Tiempos {
    Tiempos {
        ataque_ms: a,
        decaimiento_ms: d,
        relajacion_ms: r,
    }
}

/// Avanza `n` ticks con el sostenido dado y devuelve el nivel final.
fn avanzar(g: &mut Generador, n: u32, sostenido: u16) -> f32 {
    let mut y = g.nivel();
    for _ in 0..n {
        y = g.tick(sostenido);
    }
    y
}

/// §2.1: desde cero el ataque es monotono, vale exactamente 1 en el tick T_A y
/// a mitad de camino vale 1,5·(1 − 3^(−1/2)) = 0,634 (la forma RC truncada, no
/// solo el fin). Se barre T_A por todo el rango firmado (§7).
#[test]
fn el_ataque_llega_al_pico_en_su_tiempo_y_tiene_la_forma_rc_truncada() {
    for t_a in [1u32, 3, 10, 100, 1_000, 10_000] {
        let mut g = Generador::nuevo();
        g.abrir(tiempos(t_a, 10, 10), 0.0, false);
        assert_eq!(g.etapa(), Etapa::Ataque);
        let n = t_a * TICKS_POR_MS;
        let mut anterior = 0.0f32;
        for i in 1..n {
            let y = g.tick(700);
            assert!(y >= anterior, "T_A={t_a}: no monotono en el tick {i}");
            assert!(
                y < 1.0,
                "T_A={t_a}: llego al pico antes de tiempo, tick {i}"
            );
            if i == n / 2 && n >= 2 {
                let esperado = 1.5 * (1.0 - 1.0 / libm::sqrtf(3.0));
                assert!(
                    (y - esperado).abs() < 1e-3,
                    "T_A={t_a}: a mitad {y} vs {esperado}"
                );
            }
            anterior = y;
        }
        let y = g.tick(700);
        assert_eq!(
            y, 1.0,
            "T_A={t_a}: en el tick N_A el nivel es exactamente 1"
        );
        assert_eq!(g.etapa(), Etapa::Decaimiento);
    }
}

/// §2.2: el decaimiento cae monotono hacia S, vale exactamente S en el tick T_D
/// y a mitad de camino la distancia a S es 1000^(−1/2) = 3,2 % de (1 − S).
/// Con S = 1000 no hay decaimiento. Se barren S y T_D.
#[test]
fn el_decaimiento_llega_al_sostenido_en_su_tiempo_con_forma_exponencial() {
    for s in [0u16, 100, 500, 700, 900, 999] {
        for t_d in [1u32, 3, 10, 100, 1_000, 10_000] {
            let mut g = Generador::nuevo();
            g.abrir(tiempos(1, t_d, 10), 0.0, false);
            avanzar(&mut g, 10, s); // el ataque de 1 ms entero
            assert_eq!(g.etapa(), Etapa::Decaimiento, "S={s} T_D={t_d}");
            let n = t_d * TICKS_POR_MS;
            let s_f = s as f32 / 1000.0;
            let mut anterior = 1.0f32;
            for i in 1..n {
                let y = g.tick(s);
                assert!(y <= anterior, "S={s} T_D={t_d}: subio en el tick {i}");
                if i == n / 2 && n >= 2 {
                    let esperado = s_f + (1.0 - s_f) / libm::sqrtf(1000.0);
                    assert!(
                        (y - esperado).abs() < 1e-3,
                        "S={s} T_D={t_d}: a mitad {y} vs {esperado}"
                    );
                }
                anterior = y;
            }
            let y = g.tick(s);
            assert_eq!(
                y, s_f,
                "S={s} T_D={t_d}: en el tick N_D el nivel es exactamente S"
            );
            assert_eq!(g.etapa(), Etapa::Sostenido);
        }
    }
    let mut g = Generador::nuevo();
    g.abrir(tiempos(1, 100, 10), 0.0, false);
    avanzar(&mut g, 10, 1000);
    assert_eq!(
        g.etapa(),
        Etapa::Sostenido,
        "con S = 1000 no hay decaimiento"
    );
    assert_eq!(g.nivel(), 1.0);
}

/// §2.3: en sostenido el nivel ES el parametro, en el mismo tick y sin filtro
/// (R-M1: el modulo no suaviza). Y el decaimiento apunta al S vivo.
#[test]
fn el_sostenido_sigue_al_parametro_en_el_acto_y_sin_filtro() {
    let mut g = Generador::nuevo();
    g.abrir(tiempos(1, 1, 10), 0.0, false);
    avanzar(&mut g, 20, 500);
    assert_eq!(g.etapa(), Etapa::Sostenido);
    assert_eq!(g.tick(500), 0.5);
    assert_eq!(g.tick(900), 0.9, "sube en el acto");
    assert_eq!(g.tick(100), 0.1, "baja en el acto");
    assert_eq!(
        g.tick(0),
        0.0,
        "un sostenido a cero es cero, y la etapa sigue siendo sostenido"
    );
    assert_eq!(g.etapa(), Etapa::Sostenido);
}

/// §2.2: la relajacion arranca desde el nivel de partida y termina en el tick
/// en que la curva cruza NIVEL_OCIOSO: `ceil(T_R·10·ln(y0/NIVEL_OCIOSO)/ln 1000)`.
/// Desde 1 son 1,61·T_R; desde 100 ‰, 1,27·T_R. Se barren T_R y y0 (§8, test 3).
#[test]
fn la_relajacion_termina_donde_cruza_el_nivel_ocioso_desde_cualquier_partida() {
    for t_r in [1u32, 10, 100, 1_000, 20_000] {
        for s in [1000u16, 700, 300, 100] {
            let mut g = Generador::nuevo();
            g.abrir(tiempos(1, 1, t_r), 0.0, false);
            avanzar(&mut g, 20, s);
            assert_eq!(g.etapa(), Etapa::Sostenido);
            let y0 = g.nivel();
            g.cerrar();
            assert_eq!(g.etapa(), Etapa::Relajacion);
            let esperado = libm::ceilf(
                t_r as f32 * TICKS_POR_MS as f32 * libm::logf(y0 / NIVEL_OCIOSO)
                    / libm::logf(1000.0),
            ) as u32;
            let mut n = 0u32;
            let mut anterior = y0;
            while g.etapa() == Etapa::Relajacion {
                let y = g.tick(s);
                assert!(y <= anterior, "T_R={t_r} S={s}: subio en relajacion");
                anterior = y;
                n += 1;
                assert!(n <= esperado + 1, "T_R={t_r} S={s}: no termina");
            }
            assert_eq!(n, esperado, "T_R={t_r} S={s}: termino en otro tick");
            assert_eq!(g.nivel(), 0.0, "al terminar el nivel es exactamente cero");
            assert_eq!(g.etapa(), Etapa::Ocioso);
        }
    }
    // desde el pico, la relacion del papel: 1,61 * T_R
    let mut g = Generador::nuevo();
    g.abrir(tiempos(1, 1, 300), 0.0, false);
    avanzar(&mut g, 20, 1000);
    g.cerrar();
    let mut n = 0;
    while g.etapa() == Etapa::Relajacion {
        g.tick(1000);
        n += 1;
    }
    assert!(
        (n as f32 / 3000.0 - 1.605).abs() < 0.002,
        "1,6 x T_R desde el pico: {n}"
    );
}

/// §3.1: `dispara` recorre ataque -> decaimiento -> relajacion sin sostener; con
/// S = 0 la relajacion arranca en cero y termina en el acto.
#[test]
fn dispara_recorre_sus_etapas_sin_sostener() {
    let mut g = Generador::nuevo();
    g.abrir(tiempos(2, 3, 5), 0.0, true);
    assert_eq!(g.etapa(), Etapa::Ataque);
    avanzar(&mut g, 20, 500);
    assert_eq!(g.etapa(), Etapa::Decaimiento);
    avanzar(&mut g, 29, 500);
    assert_eq!(g.etapa(), Etapa::Decaimiento);
    g.tick(500);
    assert_eq!(
        g.etapa(),
        Etapa::Relajacion,
        "al llegar al sostenido, relajacion"
    );
    assert_eq!(g.nivel(), 0.5);
    let mut n = 0;
    while g.etapa() == Etapa::Relajacion {
        g.tick(500);
        n += 1;
        assert!(n < 1000);
    }
    assert_eq!(g.etapa(), Etapa::Ocioso);

    let mut g = Generador::nuevo();
    g.abrir(tiempos(1, 1, 100), 0.0, true);
    avanzar(&mut g, 20, 0);
    assert_eq!(
        g.etapa(),
        Etapa::Ocioso,
        "con S = 0 la relajacion arranca en cero y ya esta"
    );
}

/// §3.1 y §3.2: `cerrar` en cualquier etapa lleva a relajacion desde el nivel
/// actual; sobre un ocioso no hace nada; `abrir` desde un nivel > 0 llega al
/// pico antes (tau_A * ln((1,5 - y0)/0,5)), y desde >= 1 entra directo en
/// decaimiento.
#[test]
fn cerrar_y_reabrir_continuan_desde_el_nivel_actual() {
    let mut g = Generador::nuevo();
    g.cerrar();
    assert_eq!(g.etapa(), Etapa::Ocioso, "cerrar un ocioso no hace nada");

    g.abrir(T, 0.0, false);
    avanzar(&mut g, 50, 700);
    assert_eq!(g.etapa(), Etapa::Ataque);
    let y = g.nivel();
    g.cerrar();
    assert_eq!(g.etapa(), Etapa::Relajacion);
    assert_eq!(g.nivel(), y, "la relajacion arranca donde estaba");

    let mut g = Generador::nuevo();
    g.abrir(tiempos(100, 10, 10), 0.5, false);
    let esperado = libm::roundf(1000.0 * libm::logf((1.5 - 0.5) / 0.5) / libm::logf(3.0)) as u32;
    let mut n = 0;
    while g.etapa() == Etapa::Ataque {
        g.tick(700);
        n += 1;
    }
    assert_eq!(n, esperado, "desde 0,5 el ataque de 100 ms dura tau_A*ln 2");
    assert_eq!(g.nivel(), 1.0);

    let mut g = Generador::nuevo();
    g.abrir(T, 1.0, false);
    assert_eq!(g.etapa(), Etapa::Decaimiento, "desde 1 no hay ataque");
    assert_eq!(g.nivel(), 1.0);
}

/// §3.3: la captura. Los tiempos son los del borde; cambiarlos con la nota
/// abierta no cambia esa nota. (El sostenido no se captura: test de arriba.)
#[test]
fn los_tiempos_se_capturan_al_borde_y_la_nota_corre_con_su_copia() {
    // Dos generadores identicos abiertos con T_A = 10 ms; el segundo "cambia" el
    // parametro despues de abrir, pero `abrir` ya copio: no hay como cambiarlo
    // sin un borde nuevo, y eso es exactamente la captura. Se prueba que dos
    // aperturas con tiempos distintos dan dos notas distintas y que la copia es
    // de cada borde.
    let mut corta = Generador::nuevo();
    let mut larga = Generador::nuevo();
    corta.abrir(tiempos(10, 10, 10), 0.0, false);
    larga.abrir(tiempos(100, 10, 10), 0.0, false);
    avanzar(&mut corta, 100, 700);
    avanzar(&mut larga, 100, 700);
    assert_eq!(corta.etapa(), Etapa::Decaimiento);
    assert_eq!(larga.etapa(), Etapa::Ataque);
    // reabrir con otros tiempos captura los nuevos
    larga.abrir(tiempos(1, 1, 1), larga.nivel(), false);
    avanzar(&mut larga, 30, 700);
    assert_eq!(
        larga.etapa(),
        Etapa::Sostenido,
        "la segunda nota corre con su propia copia"
    );
}

fn parametros() -> Parametros {
    Parametros {
        vca: tiempos(10, 20, 30),
        vca_sostenido: 700,
        filtro: tiempos(5, 30, 30),
        filtro_sostenido: 300,
        sensibilidad_fuerza: 500,
        filtro_cantidad: 1200,
        paneo: 500,
    }
}

fn evento(canal: u8, borde: Borde, fuerza: u16, secuencia: u16) -> Entrada {
    Entrada::Evento {
        canal,
        borde,
        fuerza: Fuerza(fuerza),
        secuencia,
    }
}
// Los tests que no miran el contador de `COMPUERTA` mandan la secuencia 0.
fn abre(canal: u8, fuerza: u16) -> Entrada {
    evento(canal, Borde::Abre, fuerza, 0)
}
fn cierra(canal: u8) -> Entrada {
    evento(canal, Borde::Cierra, 0, 0)
}
fn ticks(g: &mut Generadores, n: u32) -> Salida {
    let mut s = g.tick(&[]);
    for _ in 1..n {
        s = g.tick(&[]);
    }
    s
}

/// §3.2 y §8 test 5: la continuidad del re-disparo se mide en la AMPLITUD, no en
/// el nivel interno. Con fuerza mayor o igual, ningun salto mayor que un paso
/// del ataque mas corto; con fuerza menor, baja al techo nuevo en un tick y entra
/// en decaimiento.
#[test]
fn el_redisparo_es_continuo_en_la_amplitud_hacia_arriba_y_declara_el_escalon_hacia_abajo() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(0, 30000)]);
    let antes = ticks(&mut g, 60).vca[0][0]; // en mitad del ataque de 10 ms
                                             // re-disparo con MAS fuerza: continuo
    let despues = g.tick(&[abre(0, 65535)]).vca[0][0];
    let paso_maximo = amplitud(1.5 * (1.0 - libm::expf(-0.1 / (1.0 / 1.0986))), 1.0, 1.0);
    assert!(
        despues >= antes && despues - antes <= paso_maximo,
        "hacia arriba: {antes} -> {despues}, paso maximo {paso_maximo}"
    );
    assert_eq!(g.etapa(0), Etapa::Ataque);
    // re-disparo con MENOS fuerza que la amplitud que sonaba: baja al techo nuevo
    // en un tick y entra en decaimiento
    ticks(&mut g, 200);
    let sonaba = g.tick(&[]).vca[0][0];
    let (l, _) = factores_paneo(500);
    let techo = amplitud(1.0, ganancia_fuerza(Fuerza(0), 500), l);
    assert!(
        sonaba > techo,
        "el caso solo existe si lo que sonaba supera el techo nuevo"
    );
    let tras = g.tick(&[abre(0, 0)]).vca[0][0];
    // §3.2 y §3.5: y0 = 1 y entra directo en decaimiento, y el mismo tick que
    // drena el borde avanza un paso: la amplitud es el techo menos UN paso del
    // decaimiento capturado (20 ms hacia S = 700 permil), no el techo exacto.
    let k_d = 1.0 - libm::expf(-0.1 / (20.0 / libm::logf(1000.0)));
    let esperado = amplitud(1.0 - k_d * 0.3, ganancia_fuerza(Fuerza(0), 500), l);
    assert!(
        tras <= techo && (tras as i32 - esperado as i32).abs() <= 1,
        "baja al techo nuevo en un tick: {tras} vs {esperado} (techo {techo})"
    );
    assert_eq!(g.etapa(0), Etapa::Decaimiento, "desde >= 1: sin ataque");
}

/// §3.3: cambiar los tiempos con la nota abierta no cambia esa nota; cambiar el
/// sostenido si, en el mismo tick. §4.2: cambiar el paneo aplica en el tick
/// siguiente, sin rampa.
#[test]
fn los_parametros_vivos_aplican_en_el_acto_y_los_capturados_no() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(3, 65535)]);
    ticks(&mut g, 400); // ataque 10 ms + decaimiento 20 ms: en sostenido
    assert_eq!(g.etapa(3), Etapa::Sostenido);
    let mut p = parametros();
    p.vca = tiempos(1000, 1000, 1000);
    p.vca_sostenido = 200;
    p.paneo = 0;
    let s = g.tick(&[Entrada::Parametros {
        canal: 3,
        parametros: p,
    }]);
    let (l, r) = factores_paneo(0);
    let g_v = ganancia_fuerza(Fuerza(65535), 500);
    assert_eq!(
        s.vca[3],
        [amplitud(0.2, g_v, l), amplitud(0.2, g_v, r)],
        "sostenido y paneo en el acto"
    );
    // los tiempos nuevos NO tocan la nota en vuelo: al cerrar, la relajacion es
    // la capturada (30 ms), no la nueva (1000 ms)
    g.tick(&[cierra(3)]);
    let mut n = 0;
    while g.etapa(3) == Etapa::Relajacion {
        g.tick(&[]);
        n += 1;
        assert!(
            n < 2000,
            "la relajacion usa los 1000 ms nuevos: la captura fallo"
        );
    }
}

/// §6: silencio = el generador de VCA esta ocioso. Sube exactamente en el tick en
/// que la relajacion termina; con dieciseis canales en etapas distintas la
/// mascara es correcta bit a bit; una nota a fuerza cero NO esta en silencio.
#[test]
fn la_mascara_de_silencio_es_el_generador_ocioso_y_no_la_palabra() {
    let mut g = Generadores::nuevos(parametros());
    assert_eq!(g.en_silencio(), 0xFFFF, "nace toda en silencio");
    let mut entradas = [abre(0, 65535); 8];
    for (i, e) in entradas.iter_mut().enumerate() {
        *e = abre(i as u8, 65535);
    }
    g.tick(&entradas);
    assert_eq!(g.en_silencio(), 0xFF00);
    g.tick(&[cierra(2), cierra(5)]);
    assert_eq!(g.en_silencio(), 0xFF00, "en relajacion no esta en silencio");
    let mut n = 0;
    while g.en_silencio() & 0b100 == 0 {
        g.tick(&[]);
        n += 1;
        assert!(n < 1000);
    }
    assert_eq!(
        g.en_silencio(),
        0xFF24,
        "los canales 2 y 5 terminan a la vez"
    );
    assert_eq!(g.etapa(2), Etapa::Ocioso);
    // una nota a fuerza cero con s = 1: la palabra es cero y el canal NO esta en silencio
    let mut p = parametros();
    p.sensibilidad_fuerza = 1000;
    let mut g = Generadores::nuevos(p);
    let s = g.tick(&[abre(9, 0)]);
    assert_eq!(s.vca[9], [0, 0]);
    assert_eq!(
        g.en_silencio() & (1 << 9),
        0,
        "la envolvente corre aunque no se oiga"
    );
}

/// §3.4: la red de R-E10 compara el bit contra la compuerta propia. Bit alto
/// sobre compuerta baja abre con FUERZA_REPARACION, tambien desde la relajacion;
/// bit bajo sobre compuerta alta cierra; `dispara` es invisible en las dos
/// direcciones; un bloque con contador viejo no hace nada.
#[test]
fn la_reafirmacion_compara_contra_la_compuerta_propia_y_dispara_es_invisible() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[
        evento(0, Borde::Abre, 30000, 1),
        evento(1, Borde::Dispara, 30000, 2),
    ]);
    assert_eq!(g.compuertas(), 0b01, "dispara no levanta la compuerta");
    assert_eq!(g.ultimo_evento(), 2);
    ticks(&mut g, 50);
    // un bloque VIEJO (contador 1 < ultimo evento 2) no hace nada
    g.tick(&[Entrada::Compuerta {
        mascara: 0,
        contador: 1,
    }]);
    assert_eq!(g.etapa(0), Etapa::Ataque, "un bloque viejo no cierra");
    // un bloque al dia que dice canal 0 cerrado y canal 4 abierto
    g.tick(&[Entrada::Compuerta {
        mascara: 0b10000,
        contador: 2,
    }]);
    assert_eq!(
        g.etapa(0),
        Etapa::Relajacion,
        "cerrada y compuerta alta: cierra"
    );
    assert_eq!(
        g.etapa(1),
        Etapa::Ataque,
        "el tambor sigue: invisible con el bit bajo"
    );
    assert_eq!(g.etapa(4), Etapa::Ataque, "abierta y compuerta baja: abre");
    assert_eq!(g.compuertas(), 0b10000);
    // el tambor termina y con el bit bajo NO resucita
    ticks(&mut g, 2000);
    assert_eq!(g.etapa(1), Etapa::Ocioso);
    g.tick(&[Entrada::Compuerta {
        mascara: 0b10000,
        contador: 2,
    }]);
    assert_eq!(g.etapa(1), Etapa::Ocioso, "dispara no resucita");
    // abierta sobre un canal en relajacion (compuerta baja) abre: el caso normal
    g.tick(&[evento(4, Borde::Cierra, 0, 3)]);
    assert_eq!(g.etapa(4), Etapa::Relajacion);
    g.tick(&[Entrada::Compuerta {
        mascara: 0b10000,
        contador: 3,
    }]);
    assert_eq!(
        g.etapa(4),
        Etapa::Ataque,
        "un abre perdido en relajacion se repara"
    );
    // la fuerza de reparacion es la constante: la amplitud al pico es la de fuerza plena
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[Entrada::Compuerta {
        mascara: 1,
        contador: 0,
    }]);
    // el tick de la compuerta ya avanzo uno: 99 mas completan el ataque de 10 ms
    let s = ticks(&mut g, 99);
    let (l, _) = factores_paneo(500);
    assert_eq!(
        s.vca[0][0],
        amplitud(1.0, ganancia_fuerza(FUERZA_REPARACION, 500), l)
    );
}

/// §3.5: la cola se drena en orden. `abre` y `cierra` en el mismo tick abren y
/// liberan desde el primer paso del ataque. Un `abre` sobre un canal en
/// conmutacion espera a `Conmutado` y no antes; un `cierra` aplica en el acto.
#[test]
fn la_cola_se_aplica_en_orden_y_la_conmutacion_retiene_solo_las_aperturas() {
    let mut g = Generadores::nuevos(parametros());
    let s = g.tick(&[abre(7, 65535), cierra(7)]);
    // §3.5: se drena en orden ANTES de avanzar, asi que el cierra ve y = 0 y no
    // hay nada que relajar (§2.2: N_R = 0 desde el nivel ocioso). La nota de
    // cero ticks no suena y deja la compuerta baja.
    assert_eq!(
        g.etapa(7),
        Etapa::Ocioso,
        "abre y cierra en orden: libera desde cero y queda ocioso"
    );
    assert_eq!(s.vca[7], [0, 0], "una nota de cero ticks no suena");
    assert_eq!(g.compuertas() & (1 << 7), 0, "la compuerta quedo baja");

    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(2, 65535)]);
    g.bloquear_apertura(0b0110);
    g.tick(&[abre(1, 65535), cierra(2)]);
    assert_eq!(
        g.etapa(1),
        Etapa::Ocioso,
        "el abre sobre un canal en conmutacion espera"
    );
    assert_eq!(g.etapa(2), Etapa::Relajacion, "el cierra aplica en el acto");
    ticks(&mut g, 5);
    assert_eq!(g.etapa(1), Etapa::Ocioso);
    g.tick(&[Entrada::Conmutado]);
    assert_eq!(
        g.etapa(1),
        Etapa::Ataque,
        "al latchear, el abre diferido aplica"
    );
    // fuera de la conmutacion los demas canales no esperan
    g.bloquear_apertura(0b0110);
    g.tick(&[abre(9, 65535)]);
    assert_eq!(g.etapa(9), Etapa::Ataque);
    // un cierra sobre un abre diferido lo cancela: la nota nueva nunca abre. El
    // canal 2 sigue en la relajacion de su nota anterior (30 ms), asi que «no
    // abrio» es «sigue relajando y su compuerta esta baja», no «ocioso».
    g.tick(&[abre(2, 65535), cierra(2)]);
    g.tick(&[Entrada::Conmutado]);
    assert_eq!(
        g.etapa(2),
        Etapa::Relajacion,
        "abre diferido y cierra: no abrio, sigue la relajacion anterior"
    );
    assert_eq!(
        g.compuertas() & (1 << 2),
        0,
        "la compuerta del canal 2 esta baja"
    );
}

/// §3.4 y voz-total §9.2, con la enmienda de la cabecera del J2 (D4):
/// `SoltarTodo` lleva todo a relajacion y baja todas las compuertas, y el
/// modulo conserva su `ultimo_evento`. El siguiente bloque al dia reabre lo que
/// el cerebro sostiene, con la fuerza de reparacion; uno viejo sigue sin hacer
/// nada.
#[test]
fn soltar_todo_libera_y_el_siguiente_bloque_al_dia_reabre_lo_que_el_cerebro_sostiene() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[
        evento(0, Borde::Abre, 65535, 898),
        evento(1, Borde::Abre, 65535, 899),
        evento(2, Borde::Dispara, 65535, 900),
    ]);
    ticks(&mut g, 100);
    g.tick(&[Entrada::SoltarTodo]);
    for c in 0..3 {
        assert_eq!(g.etapa(c), Etapa::Relajacion, "canal {c}");
    }
    assert_eq!(g.compuertas(), 0);
    assert_eq!(g.ultimo_evento(), 900, "el watchdog no toca el contador");
    // un bloque armado antes del ultimo evento sigue siendo viejo
    g.tick(&[Entrada::Compuerta {
        mascara: 0b11,
        contador: 899,
    }]);
    assert_eq!(g.compuertas(), 0, "un bloque viejo no reabre");
    g.tick(&[Entrada::Compuerta {
        mascara: 0b11,
        contador: 900,
    }]);
    assert_eq!(g.etapa(0), Etapa::Ataque);
    assert_eq!(g.etapa(1), Etapa::Ataque);
    assert_eq!(
        g.etapa(2),
        Etapa::Relajacion,
        "el tambor no se reabre: no era compuerta"
    );
}

/// Cabecera del J2, D5: abrir sesion suelta todo, como el watchdog, y ademas
/// pone `ultimo_evento` a cero. El cerebro tambien arranca de cero, y su primer
/// bloque sin eventos lleva contador 0: con el contador viejo seria viejo.
#[test]
fn la_sesion_suelta_todo_y_el_contador_vuelve_a_cero() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[
        evento(0, Borde::Abre, 65535, 900),
        evento(1, Borde::Abre, 65535, 901),
    ]);
    ticks(&mut g, 100);
    g.tick(&[Entrada::Sesion]);
    assert_eq!(g.etapa(0), Etapa::Relajacion);
    assert_eq!(g.etapa(1), Etapa::Relajacion);
    assert_eq!(g.compuertas(), 0);
    assert_eq!(g.ultimo_evento(), 0);
    g.tick(&[Entrada::Compuerta {
        mascara: 0b10,
        contador: 0,
    }]);
    assert_eq!(g.compuertas(), 0b10, "el primer bloque de la sesion aplica");
    assert_eq!(g.etapa(1), Etapa::Ataque);
}

/// Cabecera del J2, D4: `ultimo_evento` es el mayor que el modulo acepto,
/// comparado con vuelta en 16 bits. Tras 0xFFFF viene 1, y un bloque armado en
/// 0xFFFF es viejo frente a 1.
#[test]
fn el_ultimo_evento_da_la_vuelta_en_16_bits() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[evento(0, Borde::Abre, 65535, 0xFFFF)]);
    g.tick(&[evento(0, Borde::Cierra, 0, 1)]);
    assert_eq!(g.ultimo_evento(), 1);
    g.tick(&[Entrada::Compuerta {
        mascara: 1,
        contador: 0xFFFF,
    }]);
    assert_eq!(g.compuertas(), 0, "0xFFFF es anterior a 1");
    // un evento con una secuencia anterior no baja el maximo
    g.tick(&[evento(3, Borde::Abre, 65535, 0xFFFE)]);
    assert_eq!(g.ultimo_evento(), 1);
}

/// Cabecera del J2, §8 test 13 (la simulacion H-1 de la junta, hecha test).
/// El cerebro arma un bloque de compuerta con su estado y la secuencia del
/// ultimo `EVENTO` emitido; antes de que el bloque salga, de cero a tres
/// eventos lo adelantan (evento D1). Se pierde un evento de cada mil, al azar,
/// sobre 60 000. Ningun bloque armado antes de un evento aceptado lo revierte,
/// y un bloque al que nada adelanto deja el modulo igual que el cerebro: todo
/// evento perdido queda reparado. Con la cuenta local de eventos recibidos
/// (generador §3.4, v1) el primer evento perdido la desplaza para siempre y
/// los bloques viejos pasan por buenos.
#[test]
fn el_contador_no_deriva_con_eventos_perdidos() {
    let mut lcg: u64 = 0x5A17_2026_1020;
    let mut azar = move |n: u64| {
        lcg = lcg
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        (lcg >> 33) % n
    };
    let mut g = Generadores::nuevos(parametros());
    let mut cerebro = 0u16; // las compuertas que el cerebro sostiene
    let mut secuencia = 0u16; // la del ultimo EVENTO emitido
    let mut aceptado: [Option<(u16, bool)>; CANALES] = [None; CANALES];
    let (mut eventos, mut perdidos, mut reversiones, mut sin_reparar) = (0, 0, 0, 0);
    while eventos < 60_000 {
        let bloque = (cerebro, secuencia);
        let adelantan = azar(4);
        for _ in 0..adelantan {
            let canal = azar(16) as u8;
            let abre = cerebro & (1 << canal) == 0;
            cerebro ^= 1 << canal;
            secuencia = secuencia.wrapping_add(1);
            eventos += 1;
            if azar(1000) == 0 {
                perdidos += 1;
                continue;
            }
            let borde = if abre { Borde::Abre } else { Borde::Cierra };
            g.tick(&[evento(canal, borde, 30000, secuencia)]);
            aceptado[canal as usize] = Some((secuencia, abre));
        }
        g.tick(&[Entrada::Compuerta {
            mascara: bloque.0,
            contador: bloque.1,
        }]);
        let compuertas = g.compuertas();
        for (canal, a) in aceptado.iter().enumerate() {
            if let Some((s, abre)) = *a {
                let posterior = (s.wrapping_sub(bloque.1) as i16) > 0;
                if posterior && (compuertas & (1 << canal) != 0) != abre {
                    reversiones += 1;
                }
            }
        }
        if adelantan == 0 && compuertas != cerebro {
            sin_reparar += 1;
        }
    }
    assert!(
        perdidos > 30,
        "la simulacion tiene que perder eventos: {perdidos}"
    );
    assert_eq!(reversiones, 0, "bloques viejos que revierten un evento");
    assert_eq!(sin_reparar, 0, "bloques al dia que no reparan");
}

/// Cabecera del J2, D4: cada indice de la tabla escribe su campo y ningun otro.
#[test]
fn cada_indice_escribe_su_campo() {
    let base = parametros();
    type Poner = fn(&mut Parametros, i32);
    let campos: [(u8, i32, Poner); 11] = [
        (0, 7_001, |p, v| p.vca.ataque_ms = v as u32),
        (1, 7_002, |p, v| p.vca.decaimiento_ms = v as u32),
        (2, 17_003, |p, v| p.vca.relajacion_ms = v as u32),
        (3, 404, |p, v| p.vca_sostenido = v as u16),
        (4, 7_005, |p, v| p.filtro.ataque_ms = v as u32),
        (5, 7_006, |p, v| p.filtro.decaimiento_ms = v as u32),
        (6, 17_007, |p, v| p.filtro.relajacion_ms = v as u32),
        (7, 808, |p, v| p.filtro_sostenido = v as u16),
        (8, 909, |p, v| p.sensibilidad_fuerza = v as u16),
        (9, -4_321, |p, v| p.filtro_cantidad = v as i16),
        (10, 111, |p, v| p.paneo = v as u16),
    ];
    for (indice, valor, poner) in campos {
        let mut g = Generadores::nuevos(base);
        g.tick(&[Entrada::Parametro {
            canal: 6,
            indice,
            valor,
        }]);
        let mut esperado = base;
        poner(&mut esperado, valor);
        assert_eq!(g.parametros(6), Some(esperado), "indice {indice}");
        assert_eq!(g.parametros(5), Some(base), "indice {indice}: otro canal");
    }
    // un indice fuera de la tabla o un canal fuera de rango no hacen nada
    let mut g = Generadores::nuevos(base);
    g.tick(&[
        Entrada::Parametro {
            canal: 6,
            indice: 11,
            valor: 1,
        },
        Entrada::Parametro {
            canal: 16,
            indice: 0,
            valor: 1,
        },
    ]);
    for canal in 0..CANALES as u8 {
        assert_eq!(g.parametros(canal), Some(base));
    }
    assert_eq!(g.parametros(16), None);
}

/// §4.2: el paneo es vivo tambien por indice, y aplica en el mismo tick.
#[test]
fn el_paneo_por_indice_aplica_en_el_acto() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(3, 65535)]);
    ticks(&mut g, 400);
    assert_eq!(g.etapa(3), Etapa::Sostenido);
    let s = g.tick(&[Entrada::Parametro {
        canal: 3,
        indice: 10,
        valor: 0,
    }]);
    let (l, r) = factores_paneo(0);
    let g_v = ganancia_fuerza(Fuerza(65535), 500);
    assert_eq!(s.vca[3], [amplitud(0.7, g_v, l), amplitud(0.7, g_v, r)]);
}

/// §5 y §4.3: la salida del filtro es el nivel de su propia envolvente, con sus
/// propios tiempos, y la del VCA son dos amplitudes con el paneo puesto.
#[test]
fn la_salida_lleva_las_dos_ramas_del_vca_y_la_envolvente_del_filtro() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(5, 65535)]);
    let s = ticks(&mut g, 50); // filtro: ataque 5 ms ya en decaimiento; VCA: en ataque
    assert_eq!(g.etapa(5), Etapa::Ataque);
    assert!(
        s.filtro[5] > 60000,
        "el filtro ya paso su pico de 5 ms: {}",
        s.filtro[5]
    );
    let (l, r) = factores_paneo(500);
    assert_eq!(
        s.vca[5][0], s.vca[5][1],
        "al centro las dos ramas son iguales"
    );
    assert!(s.vca[5][0] > 0);
    let _ = (l, r);
    for c in 0..CANALES {
        if c != 5 {
            assert_eq!(s.vca[c], [0, 0]);
            assert_eq!(s.filtro[c], 0);
        }
    }
}

// Los dos tests de abajo NO estan en el plan: los pide su paso 5 («si alguna
// mutacion sobrevive, anade el test que la mate»). Las mutaciones (d) «el abre
// diferido aplica en el acto» y (f) «el re-disparo desde y en vez de desde la
// amplitud» sobrevivian al barrido: la (d) porque el test de la cola panica en
// su primera asercion y nunca llega a la conmutacion, y la (f) porque la cota
// del re-disparo es la del ataque MAS CORTO (1 ms) mientras el caso corre con
// uno de 10 ms, asi que le sobran 10 000 LSB de holgura.

/// §3.2: la continuidad del re-disparo se mide en la AMPLITUD. Este caso la
/// distingue del nivel interno porque `g_v` cambia de 0,5 a 1: si el generador
/// reabriera desde `y` en vez de desde `a0 / g_v_nueva`, la amplitud DOBLARIA
/// en un tick. La cota es un paso del ataque CAPTURADO (10 ms, §2.1), no la del
/// ataque mas corto del rango.
#[test]
fn el_redisparo_conserva_la_amplitud_cuando_la_ganancia_de_fuerza_cambia() {
    let mut g = Generadores::nuevos(parametros());
    g.tick(&[abre(0, 0)]); // sensibilidad 500 y fuerza 0: g_v = 0,5
    let antes = ticks(&mut g, 60).vca[0][0];
    let despues = g.tick(&[abre(0, 65535)]).vca[0][0]; // g_v = 1
    let (l, _) = factores_paneo(500);
    let k_a = 1.0 - libm::expf(-0.1 / (10.0 / libm::logf(3.0)));
    let paso = amplitud(1.5 * k_a, 1.0, l);
    assert!(
        despues >= antes && despues - antes <= paso,
        "la amplitud tiene que seguir: {antes} -> {despues}, un paso del ataque son {paso}"
    );
}

/// §6: un `abre` sobre un canal en conmutacion espera en su ranura hasta que el
/// firmware latchea el crosspoint, y no antes: mientras se shiftean los 512 bits
/// del AD75019 (102 us, mas de un tick) abrir el canal seria abrirlo a medio
/// conmutar, que es lo que la barrera existe para impedir.
#[test]
fn el_abre_diferido_no_aplica_hasta_el_latch() {
    let mut g = Generadores::nuevos(parametros());
    g.bloquear_apertura(1 << 4);
    g.tick(&[abre(4, 65535)]);
    assert_eq!(g.etapa(4), Etapa::Ocioso, "el abre espera al latch");
    assert_eq!(
        g.compuertas() & (1 << 4),
        0,
        "y su compuerta propia sigue baja"
    );
    ticks(&mut g, 20);
    assert_eq!(
        g.etapa(4),
        Etapa::Ocioso,
        "sigue esperando mientras se shiftea"
    );
    g.tick(&[Entrada::Conmutado]);
    assert_eq!(g.etapa(4), Etapa::Ataque, "al latchear, el diferido aplica");
}

/// Los rangos firmados (§7) empiezan en 1 ms y los valida el descriptor, pero un
/// cero que se cuele no puede desbordar la cuenta de ticks: vale como 1 ms y el
/// generador recorre sus etapas sin entrar en panico.
#[test]
fn un_tiempo_a_cero_vale_como_un_milisegundo_y_no_desborda() {
    let mut g = Generador::nuevo();
    g.abrir(tiempos(0, 0, 0), 0.0, false);
    assert_eq!(g.etapa(), Etapa::Ataque);
    avanzar(&mut g, 10, 500);
    assert_eq!(g.etapa(), Etapa::Decaimiento, "el ataque de cero duro 1 ms");
    avanzar(&mut g, 10, 500);
    assert_eq!(
        g.etapa(),
        Etapa::Sostenido,
        "el decaimiento de cero duro 1 ms"
    );
    g.cerrar();
    let mut n = 0;
    while g.etapa() == Etapa::Relajacion {
        g.tick(500);
        n += 1;
        assert!(n < 100, "la relajacion de cero no termina");
    }
    assert_eq!(g.etapa(), Etapa::Ocioso);
}
