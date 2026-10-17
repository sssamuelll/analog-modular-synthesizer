#![no_std]
#![no_main]

//! **La recuperacion del transporte por tic, en placa.**
//!
//! Medida 2 de `papel-v2.md` §4 (acta del 17-10, ficha 3). Cuatro fases, cada una con sus
//! comprobaciones al final -- no se imprime nada mientras el transporte corre, por la
//! misma razon que en `tic_banco`:
//!
//! - **A, un incidente.** `envenena(0)`: el canal de transmision de la ranura 0 cuenta un
//!   byte menos que el `TSIZE`, el maestro se queda sin dato a mitad de trama con el `CS`
//!   abajo -- el cuelgue del repro original --, el tic lo da por vencido, la politica pide
//!   el reinicio y el nivel 4 lo ejecuta. Se publican los instantes del incidente en
//!   microsegundos desde el `CSTART` envenenado: cuando vence, cuando entra la
//!   recuperacion, cuanto tiempo flota el `CS` (el reset del SPI por RCC), y cuando sale la
//!   primera trama buena.
//! - **B, una rafaga** de 1 000 incidentes, uno cada 4 ms: nada se acumula, nada se queda.
//! - **C, la escalada del GPDMA1** (`--features escalada`, con `ranuras-3` y
//!   `sin-esclavo`): `fuerza_escalada()` mas un veneno, diez veces, con las vecinas en
//!   vuelo. El esclavo del banco comparte el GPDMA1 y moriria con el reset, por eso esta
//!   fase va sin el.
//! - **D, la ranura muerta:** el planificador deja de pedir la recuperacion y la ranura 0
//!   tiene que pasar a `Muerta` y dejar de sellar; las vecinas, no.
//! - **F, un error del DMA:** el canal de recepcion con un ajuste de usuario invalido (`USEF`):
//!   prueba la rama `error_dma` de la maquina, que el reset por RCC de la recuperacion esconde.
//!
//! ```bash
//! cargo run --release --features inyeccion,reloj-hub --bin tic_recupera
//! cargo run --release --features inyeccion,reloj-hub,ranuras-3,sin-esclavo,escalada --bin tic_recupera
//! ```

use core::sync::atomic::Ordering;

use defmt::info;
use embassy_executor::Spawner;
#[cfg(not(feature = "sin-esclavo"))]
use embassy_stm32::interrupt;
use embassy_time::Timer;
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
use sam17_nucleo_core::transporte_j2::Estado;
use sam17_nucleo_fw::j2_banco::{bajada_del_banco, juez_del_banco, RANURAS_DE_MEDIDA};
#[cfg(not(feature = "sin-esclavo"))]
use sam17_nucleo_fw::j2_ejecutor::iniciar_ejecutor;
use sam17_nucleo_fw::j2_ejecutor::{cuentas, SELLOS};
use sam17_nucleo_fw::j2_esclavo;
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::j2_tic::{self, Marca};
use sam17_nucleo_fw::ranuras_de_medida;
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Lo que se lee antes y despues de cada fase.
#[derive(Clone, Copy, Default)]
struct Foto {
    giros: [u32; 4],
    plazos: [u32; 4],
    subidas_ok: u32,
    subidas_malas: u32,
    recuperaciones: u32,
    errores_dma: u32,
    escaladas: u32,
    muertas: u32,
    cortas_esclavo: u32,
    ok_esclavo: u32,
    #[cfg_attr(not(feature = "verifica-bajada"), allow(dead_code))]
    bajadas_malas: u32,
    #[cfg_attr(not(feature = "verifica-bajada"), allow(dead_code))]
    bajadas_ok: u32,
    sellos: [u32; 4],
}

/// Las ranuras que el banco puede tener activas: la 0 y las de relleno 2 y 3.
const ACTIVAS: [usize; 3] = [0, 2, 3];

fn foto() -> Foto {
    let mut f = Foto::default();
    for (k, &n) in ACTIVAS.iter().enumerate() {
        let c = cuentas(n);
        f.giros[k] = c.giros;
        f.plazos[k] = c.plazos_vencidos;
        f.sellos[k] = SELLOS[n].load(Ordering::Relaxed);
        if n == 0 {
            f.subidas_ok = c.subidas_ok;
            f.subidas_malas = c.subidas_malas;
        }
    }
    let t = j2_tic::testigos();
    f.recuperaciones = t.recuperaciones;
    f.errores_dma = t.errores_dma;
    f.escaladas = t.escaladas_gpdma;
    f.muertas = t.ranuras_muertas;
    f.cortas_esclavo = j2_esclavo::TRAMAS_CORTAS.load(Ordering::Relaxed);
    f.ok_esclavo = j2_esclavo::TRAMAS_OK.load(Ordering::Relaxed);
    #[cfg(feature = "verifica-bajada")]
    {
        f.bajadas_ok = j2_esclavo::BAJADAS_OK.load(Ordering::Relaxed);
        f.bajadas_malas = j2_esclavo::BAJADAS_MALAS.load(Ordering::Relaxed);
    }
    f
}

fn veredicto(nombre: &'static str, bien: bool) {
    if bien {
        info!("tic_recupera,{=str},ok", nombre);
    } else {
        info!("tic_recupera,{=str},FALLA", nombre);
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let _ = spawner;
    #[cfg(feature = "reloj-hub")]
    let config = usb::configuracion_hub();
    #[cfg(not(feature = "reloj-hub"))]
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = usb::iniciar(config);
    let cfg = Config {
        f_sck_hz: 10_000_000,
        f_cpu_hz: f_cpu,
        retardo_tsck_cuartos: 4,
    };
    let ranuras = ranuras_de_medida!(p, cfg);
    #[cfg(not(feature = "sin-esclavo"))]
    {
        let esclavo = sam17_nucleo_fw::j2_banco::esclavo_del_banco(
            p.PE2,
            p.PE14,
            p.PE13,
            p.PE11,
            p.GPDMA1_CH2,
            p.GPDMA1_CH3,
        );
        let spawner_j2 = iniciar_ejecutor(interrupt::GFXTIM);
        spawner_j2.spawn(defmt::unwrap!(j2_esclavo::tarea_esclavo(esclavo)));
    }
    let ciclos_us = f_cpu / 1_000_000;
    j2_tic::lanzar(
        ranuras,
        p.TIM7,
        PERIODO_GIRO_US,
        f_cpu,
        bajada_del_banco,
        juez_del_banco,
    );
    // SAFETY: nadie mas toca el SCB en este binario.
    unsafe {
        let mut cp = cortex_m::Peripherals::steal();
        cp.SCB.enable_icache();
        cp.SCB.enable_dcache(&mut cp.CPUID);
    }
    Timer::after_millis(500).await;

    // ---- A: un incidente ------------------------------------------------------------
    let antes_a = foto();
    j2_tic::borra_marcas();
    j2_tic::envenena(0);
    Timer::after_millis(20).await;
    let despues_a = foto();
    let m = j2_tic::marcas();

    // ---- B: una rafaga ----------------------------------------------------------------
    let antes_b = foto();
    for _ in 0..1000 {
        j2_tic::envenena(0);
        Timer::after_millis(4).await;
    }
    Timer::after_millis(50).await;
    let despues_b = foto();

    // ---- C: la escalada del GPDMA1, con las vecinas en vuelo -------------------------
    #[cfg(feature = "escalada")]
    let (antes_c, despues_c, marcas_c) = {
        let antes = foto();
        for _ in 0..10 {
            j2_tic::fuerza_escalada();
            j2_tic::envenena(0);
            Timer::after_millis(30).await;
        }
        Timer::after_millis(50).await;
        // Las marcas, ahora: la fase F recupera la ranura 0 otra vez y las pisa.
        (antes, foto(), j2_tic::marcas())
    };

    // ---- F: un error del DMA --------------------------------------------------------------
    let antes_f = foto();
    j2_tic::envenena_dma(0);
    Timer::after_millis(20).await;
    let despues_f = foto();

    // ---- D: la ranura muerta ------------------------------------------------------------
    // Con las cotas de hoy (100 tics, 12,5 ms) la muerte tarda; con `cotas-v2`, 3 tics.
    j2_tic::sin_recuperacion(true);
    j2_tic::envenena(0);
    Timer::after_millis(30).await;
    let sello_0 = SELLOS[0].load(Ordering::Relaxed);
    let sello_vecina = SELLOS[2].load(Ordering::Relaxed);
    Timer::after_millis(5).await;
    let estado_d = j2_tic::estado(0);
    let sello_0_despues = SELLOS[0].load(Ordering::Relaxed);
    let sello_vecina_despues = SELLOS[2].load(Ordering::Relaxed);
    let despues_d = foto();
    j2_tic::sin_recuperacion(false);

    // ---- Se imprime todo seguido -----------------------------------------------------
    info!(
        "tic_recupera: firmware {}, f_cpu {} Hz, ranuras {}",
        env!("SAM17_GIT"),
        f_cpu,
        RANURAS_DE_MEDIDA
    );

    // A
    let us = |ciclos: u32| ciclos.wrapping_sub(m[Marca::CstartVeneno as usize]) / ciclos_us;
    info!(
        "tic_recupera,A,desde_cstart_veneno_us: vencida={},rec_inicio={},reset_ini={},reset_fin={},rec_hecha={},cstart_siguiente={}",
        us(m[Marca::Vencida as usize]),
        us(m[Marca::RecInicio as usize]),
        us(m[Marca::ResetIni as usize]),
        us(m[Marca::ResetFin as usize]),
        us(m[Marca::RecHecha as usize]),
        us(m[Marca::CstartSiguiente as usize]),
    );
    let cs_flota_ciclos = m[Marca::ResetFin as usize].wrapping_sub(m[Marca::ResetIni as usize]);
    let hueco_ciclos = m[Marca::CstartSiguiente as usize].wrapping_sub(m[Marca::ResetFin as usize]);
    info!(
        "tic_recupera,A,cs_sin_manejar_ns={},hueco_hasta_el_siguiente_cstart_us={}",
        cs_flota_ciclos * 1000 / ciclos_us,
        hueco_ciclos / ciclos_us
    );
    veredicto(
        "A.un_plazo_vencido",
        despues_a.plazos[0] == antes_a.plazos[0] + 1,
    );
    veredicto(
        "A.una_recuperacion",
        despues_a.recuperaciones == antes_a.recuperaciones + 1,
    );
    veredicto("A.ninguna_muerta", despues_a.muertas == 0);
    veredicto(
        "A.los_giros_siguen",
        despues_a.giros[0] >= antes_a.giros[0] + 100,
    );
    #[cfg(not(feature = "sin-esclavo"))]
    veredicto(
        "A.las_subidas_siguen",
        despues_a.subidas_ok >= antes_a.subidas_ok + 100,
    );
    #[cfg(not(feature = "sin-esclavo"))]
    veredicto(
        "A.ninguna_subida_mala",
        despues_a.subidas_malas == antes_a.subidas_malas,
    );
    #[cfg(not(feature = "sin-esclavo"))]
    veredicto(
        "A.el_esclavo_ve_una_trama_corta",
        despues_a.cortas_esclavo == antes_a.cortas_esclavo + 1,
    );

    // B
    info!(
        "tic_recupera,B,incidentes=1000,plazos={},recuperaciones={},muertas={},subidas_ok={},subidas_malas={},cortas_esclavo={},giros={}",
        despues_b.plazos[0] - antes_b.plazos[0],
        despues_b.recuperaciones - antes_b.recuperaciones,
        despues_b.muertas,
        despues_b.subidas_ok - antes_b.subidas_ok,
        despues_b.subidas_malas - antes_b.subidas_malas,
        despues_b.cortas_esclavo - antes_b.cortas_esclavo,
        despues_b.giros[0] - antes_b.giros[0],
    );
    veredicto(
        "B.mil_plazos",
        despues_b.plazos[0] - antes_b.plazos[0] == 1000,
    );
    veredicto(
        "B.mil_recuperaciones",
        despues_b.recuperaciones - antes_b.recuperaciones == 1000,
    );
    veredicto("B.ninguna_muerta", despues_b.muertas == 0);
    #[cfg(not(feature = "sin-esclavo"))]
    veredicto(
        "B.ninguna_subida_mala",
        despues_b.subidas_malas == antes_b.subidas_malas,
    );
    #[cfg(not(feature = "sin-esclavo"))]
    veredicto(
        "B.el_esclavo_ve_mil_tramas_cortas",
        despues_b.cortas_esclavo - antes_b.cortas_esclavo == 1000,
    );

    // La bajada que el esclavo recibio, antes y despues de las rafagas de incidentes.
    #[cfg(feature = "verifica-bajada")]
    {
        info!(
            "tic_recupera,bajada,ok={},malas={}",
            despues_b.bajadas_ok - antes_a.bajadas_ok,
            despues_b.bajadas_malas - antes_a.bajadas_malas
        );
        veredicto(
            "B.la_bajada_siempre_buena",
            despues_b.bajadas_malas == antes_a.bajadas_malas
                && despues_b.bajadas_ok > antes_a.bajadas_ok,
        );
    }

    // C
    #[cfg(feature = "escalada")]
    {
        info!(
            "tic_recupera,C,escaladas={},plazos_ranura0={},plazos_ranura2={},plazos_ranura3={},recuperaciones={},muertas={}",
            despues_c.escaladas - antes_c.escaladas,
            despues_c.plazos[0] - antes_c.plazos[0],
            despues_c.plazos[1] - antes_c.plazos[1],
            despues_c.plazos[2] - antes_c.plazos[2],
            despues_c.recuperaciones - antes_c.recuperaciones,
            despues_c.muertas,
        );
        let m = marcas_c;
        info!(
            "tic_recupera,C,ultima_escalada: seccion_critica_ns={},escalada_entera_us={}",
            m[Marca::SeccionFin as usize].wrapping_sub(m[Marca::SeccionIni as usize]) * 1000
                / ciclos_us,
            m[Marca::RecHecha as usize].wrapping_sub(m[Marca::EscalaIni as usize]) / ciclos_us
        );
        veredicto(
            "C.diez_escaladas",
            despues_c.escaladas - antes_c.escaladas == 10,
        );
        veredicto(
            "C.las_vecinas_en_vuelo_vencen",
            despues_c.plazos[1] > antes_c.plazos[1] && despues_c.plazos[2] > antes_c.plazos[2],
        );
        veredicto("C.ninguna_muerta", despues_c.muertas == 0);
        veredicto(
            "C.las_tres_siguen_girando",
            despues_c.giros[0] > antes_c.giros[0] + 1000
                && despues_c.giros[1] > antes_c.giros[1] + 1000
                && despues_c.giros[2] > antes_c.giros[2] + 1000,
        );
    }

    // F
    info!(
        "tic_recupera,F,errores_dma={},plazos={},recuperaciones={},muertas={}",
        despues_f.errores_dma - antes_f.errores_dma,
        despues_f.plazos[0] - antes_f.plazos[0],
        despues_f.recuperaciones - antes_f.recuperaciones,
        despues_f.muertas,
    );
    veredicto(
        "F.un_error_del_dma",
        despues_f.errores_dma == antes_f.errores_dma + 1,
    );
    veredicto(
        "F.un_plazo_vencido",
        despues_f.plazos[0] == antes_f.plazos[0] + 1,
    );
    veredicto(
        "F.una_recuperacion",
        despues_f.recuperaciones == antes_f.recuperaciones + 1,
    );
    veredicto("F.ninguna_muerta", despues_f.muertas == 0);
    veredicto(
        "F.los_giros_siguen",
        despues_f.giros[0] >= antes_f.giros[0] + 100,
    );

    // D
    info!(
        "tic_recupera,D,muertas={},sello_ranura0: {}->{},sello_ranura2: {}->{}",
        despues_d.muertas, sello_0, sello_0_despues, sello_vecina, sello_vecina_despues
    );
    veredicto("D.la_ranura_pasa_a_muerta", estado_d == Estado::Muerta);
    veredicto("D.una_muerta", despues_d.muertas == 1);
    veredicto("D.deja_de_sellar", sello_0 == sello_0_despues);
    if RANURAS_DE_MEDIDA >= 2 {
        veredicto(
            "D.las_vecinas_siguen_sellando",
            sello_vecina_despues > sello_vecina,
        );
    }
    let t = j2_tic::testigos();
    info!("tic_recupera,tic,{}", t);
    info!("tic_recupera: fin");
    // Un `bkpt` para que `probe-rs run` termine solo y suelte la sonda.
    cortex_m::asm::bkpt();
    loop {
        Timer::after_secs(60).await;
    }
}
