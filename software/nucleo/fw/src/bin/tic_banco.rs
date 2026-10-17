#![no_std]
#![no_main]

//! **El transporte por tic contra el esclavo del banco.**
//!
//! Medida 3 de `papel-v2.md` §4 (acta del 17-10, ficha 3): el maestro de `j2_tic` en SPI5
//! y el esclavo del banco en SPI4, cableados, con las caches y la region MPU de los
//! bufferes del DMA (R-MJ7). Corre [`DURACION_S`] segundos a 8 kHz (o a 1 kHz con
//! `--features mil-hz`) y publica **al final**, una sola vez: un `info!` mantiene las
//! interrupciones apagadas ~11 us con las dos caches (PR #438), mas que el umbral de un
//! tic tardio, y ensuciaria justo los testigos que esta corrida quiere dejar en cero.
//!
//! Lo que se lee: `giros` y `subidas_ok` del maestro contra `tramas_ok` del esclavo (si el
//! enlace no pierde nada, el esclavo ve un giro por cada giro del maestro, menos el que va
//! en vuelo); `plazos_vencidos`, `subidas_malas` y los testigos del tic a cero.
//!
//! ```bash
//! cargo run --release --features transporte-tic,reloj-hub --bin tic_banco
//! ```

use core::sync::atomic::Ordering;

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt;
use embassy_time::Timer;
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
use sam17_nucleo_fw::j2_banco::{
    bajada_del_banco, esclavo_del_banco, juez_del_banco, maestro_del_banco, LARGO_BANCO,
    RANURA_BANCO,
};
use sam17_nucleo_fw::j2_ejecutor::{cuentas, iniciar_ejecutor};
use sam17_nucleo_fw::j2_esclavo::{self, tarea_esclavo};
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::j2_tic;
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Cuanto dura la corrida, en segundos: 600, o 20 con `--features corta` para una prueba de humo.
const DURACION_S: u64 = if cfg!(feature = "corta") { 20 } else { 600 };

/// El periodo del giro: el del instrumento, o 1 kHz con `mil-hz`.
const PERIODO_US: u32 = if cfg!(feature = "mil-hz") {
    1_000
} else {
    PERIODO_GIRO_US
};

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let _ = spawner;
    #[cfg(feature = "reloj-hub")]
    let config = usb::configuracion_hub();
    #[cfg(not(feature = "reloj-hub"))]
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = usb::iniciar(config);

    let ranura = maestro_del_banco(
        p.PE15,
        p.PG2,
        p.PG1,
        p.PA3,
        p.GPDMA1_CH0,
        p.GPDMA1_CH1,
        &p.RCC,
        Config {
            f_sck_hz: 10_000_000,
            f_cpu_hz: f_cpu,
            retardo_tsck_cuartos: 4,
        },
    );
    let f_sck_hz = ranura.f_sck_hz();
    let esclavo = esclavo_del_banco(p.PE2, p.PE14, p.PE13, p.PE11, p.GPDMA1_CH2, p.GPDMA1_CH3);
    info!(
        "tic_banco: firmware {}, f_sck {} Hz, f_cpu {} Hz, periodo {} us, mensaje {} B, duracion {} s",
        env!("SAM17_GIT"),
        f_sck_hz,
        f_cpu,
        PERIODO_US,
        LARGO_BANCO,
        DURACION_S
    );

    // El esclavo nace ANTES que el maestro, como en `resistencia_j2`: si no, los primeros
    // giros irian contra un esclavo que no existe y saldrian como subidas malas.
    let spawner_j2 = iniciar_ejecutor(interrupt::GFXTIM);
    spawner_j2.spawn(defmt::unwrap!(tarea_esclavo(esclavo)));
    let mut ranuras = [const { None }; 6];
    ranuras[RANURA_BANCO] = Some(ranura);
    j2_tic::lanzar(
        ranuras,
        p.TIM7,
        PERIODO_US,
        f_cpu,
        bajada_del_banco,
        juez_del_banco,
    );
    // La D-cache solo se puede encender con la region de los bufferes ya en la MPU, y
    // `lanzar` la acaba de programar. El esclavo no lee su bufer de recepcion, asi que su
    // bufer no necesita region.
    // SAFETY: nadie mas toca el SCB en este binario.
    unsafe {
        let mut cp = cortex_m::Peripherals::steal();
        cp.SCB.enable_icache();
        cp.SCB.enable_dcache(&mut cp.CPUID);
    }

    Timer::after_secs(DURACION_S).await;

    // Se lee todo seguido y se imprime despues.
    let c = cuentas(RANURA_BANCO);
    let t = j2_tic::testigos();
    let ok = j2_esclavo::TRAMAS_OK.load(Ordering::Relaxed);
    let cortas = j2_esclavo::TRAMAS_CORTAS.load(Ordering::Relaxed);
    let rearmes = j2_esclavo::REARMES_ESCALADOS.load(Ordering::Relaxed);
    info!(
        "tic_banco,maestro,giros={},subidas_ok={},subidas_malas={},plazos_vencidos={},muda={},inestable={}",
        c.giros, c.subidas_ok, c.subidas_malas, c.plazos_vencidos, c.muda, c.inestable
    );
    info!(
        "tic_banco,esclavo,tramas_ok={},tramas_cortas={},rearmes_escalados={}",
        ok, cortas, rearmes
    );
    #[cfg(feature = "verifica-bajada")]
    info!(
        "tic_banco,esclavo,bajadas_ok={},bajadas_malas={}",
        j2_esclavo::BAJADAS_OK.load(Ordering::Relaxed),
        j2_esclavo::BAJADAS_MALAS.load(Ordering::Relaxed)
    );
    info!("tic_banco,tic,{}", t);
    info!("tic_banco: fin");
    // Un `bkpt` para que `probe-rs run` termine solo y suelte la sonda.
    cortex_m::asm::bkpt();
    loop {
        Timer::after_secs(60).await;
    }
}
