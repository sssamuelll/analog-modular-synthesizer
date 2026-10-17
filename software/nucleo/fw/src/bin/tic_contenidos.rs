#![no_std]
#![no_main]

//! **Que contenidos maltrata el enlace del banco.**
//!
//! `tic_estres` descubrio que los marcos numerados, de apariencia aleatoria, llegan rotos de forma
//! determinista por el cable del banco, y que los patrones regulares viejos (`0x5A ^ i`, `0xA5 ^ i`) no.
//! Este binario lo acota: la bajada recorre una tabla de 16 contenidos de prueba (todo ceros, todo unos,
//! `0xAA`, `0x55`, los patrones viejos, una rampa, un solo byte distinto, un marco numerado, ruido...) y
//! el esclavo del banco comprueba cada trama recibida contra el mismo contenido y cuenta cuales llegan
//! enteros. Publica, por contenido, cuantas llegaron bien y mal, y los bytes de la primera que no.
//!
//! ```bash
//! cargo run --release --features transporte-tic,tabla,reloj-hub,corta --bin tic_contenidos
//! ```

use core::sync::atomic::Ordering;

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt;
use embassy_time::Timer;
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
use sam17_nucleo_fw::j2_banco::{
    esclavo_del_banco, juez_del_banco, maestro_del_banco, tabla, LARGO_BANCO, RANURA_BANCO,
};
use sam17_nucleo_fw::j2_ejecutor::iniciar_ejecutor;
use sam17_nucleo_fw::j2_esclavo::{self, tarea_esclavo};
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::j2_tic;
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Cuanto dura la corrida, en segundos.
const DURACION_S: u64 = if cfg!(feature = "corta") { 5 } else { 30 };

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
    let esclavo = esclavo_del_banco(p.PE2, p.PE14, p.PE13, p.PE11, p.GPDMA1_CH2, p.GPDMA1_CH3);
    let spawner_j2 = iniciar_ejecutor(interrupt::GFXTIM);
    spawner_j2.spawn(defmt::unwrap!(tarea_esclavo(esclavo)));
    let mut ranuras = [const { None }; 6];
    ranuras[RANURA_BANCO] = Some(ranura);
    j2_tic::lanzar(
        ranuras,
        p.TIM7,
        PERIODO_GIRO_US,
        f_cpu,
        tabla::bajada,
        juez_del_banco,
    );
    // SAFETY: nadie mas toca el SCB en este binario.
    unsafe {
        let mut cp = cortex_m::Peripherals::steal();
        cp.SCB.enable_icache();
        cp.SCB.enable_dcache(&mut cp.CPUID);
    }
    Timer::after_secs(DURACION_S).await;

    info!(
        "tic_contenidos: firmware {}, {} bytes por trama, {} s",
        env!("SAM17_GIT"),
        LARGO_BANCO,
        DURACION_S
    );
    for id in 0..tabla::N {
        let ok = j2_esclavo::TABLA_OK[id].load(Ordering::Relaxed);
        let mal = j2_esclavo::TABLA_MAL[id].load(Ordering::Relaxed);
        info!(
            "tic_contenidos,contenido={},llegan_bien={},llegan_mal={}",
            id, ok, mal
        );
        if mal != 0 {
            let mut b = [0u8; 32];
            for (d, o) in b.iter_mut().zip(j2_esclavo::TABLA_PRIMERA[id].iter()) {
                *d = o.load(Ordering::Relaxed);
            }
            let mut e = [0u8; LARGO_BANCO];
            tabla::marco(id as u8, &mut e);
            info!("tic_contenidos,contenido={},esperado={=[u8]:x}", id, e);
            info!("tic_contenidos,contenido={},primera_mala={=[u8]:x}", id, b);
        }
    }
    info!("tic_contenidos: fin");
    // Un `bkpt` para que `probe-rs run` termine solo y suelte la sonda.
    cortex_m::asm::bkpt();
    loop {
        Timer::after_secs(60).await;
    }
}
