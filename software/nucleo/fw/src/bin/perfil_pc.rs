#![no_std]
#![no_main]

//! **Donde se va la CPU de un giro, funcion por funcion.**
//!
//! El perfilador por muestreo ([`sam17_nucleo_fw::muestreo`]) sobre el maestro
//! solo, igual que `carga_j2` pero con `TIM6` anotando el PC a 21 kHz. Es lo que
//! dice **que funciones** se comen los ~21 600 ciclos de un giro: el reparto de
//! `carga_j2` solo los separa en tramos que alguien acoto, y mas de la mitad
//! caia en «maquinaria de futuros y despacho».
//!
//! Corre 20 s con el J2 ya estable, para el muestreo y se detiene en un `bkpt`
//! con el histograma en la RAM. Quien lo lee es `perfil_pc.py`, que ademas lanza
//! el binario y lo cruza con los simbolos:
//!
//! ```bash
//! cargo build --release --features muestreo --bin perfil_pc
//! python perfil_pc.py target/thumbv8m.main-none-eabihf/release/perfil_pc
//! ```
//!
//! **Perturba** (la ISR cuesta ~5 % de la CPU): los ciclos por giro salen de
//! `carga_j2`, esto da solo como se reparten.

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt;
use embassy_time::Timer;
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
use sam17_nucleo_fw::carga::{vueltas_del_hilo, Medidor};
use sam17_nucleo_fw::j2_banco::{
    bajada_del_banco, juez_del_banco, maestro_del_banco, RANURA_BANCO,
};
use sam17_nucleo_fw::j2_ejecutor::{cuentas, iniciar_ejecutor, lanzar_ranuras};
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::muestreo;
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Muestras por segundo. Primo con los periodos del giro (125 us, 1 ms): no
/// cae siempre en el mismo punto del ciclo.
const MUESTRAS_POR_S: u32 = 21_000;
/// Cuanto muestrea.
const SEGUNDOS: u64 = 20;

#[embassy_executor::main]
async fn main(spawner: Spawner) {
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

    spawner.spawn(defmt::unwrap!(vueltas_del_hilo()));
    let mut medidor = Medidor::calibrar(500).await;
    lanzar_ranuras(
        iniciar_ejecutor(interrupt::GFXTIM),
        [Some(ranura), None, None, None, None, None],
        bajada_del_banco,
        juez_del_banco,
        PERIODO_GIRO_US,
    );
    // El J2 a regimen antes de muestrear.
    Timer::after_secs(2).await;
    let _ = medidor.libre_por_mil();

    let giros_antes = cuentas(RANURA_BANCO).giros;
    let ciclos_timer = muestreo::iniciar(p.TIM6, MUESTRAS_POR_S);
    Timer::after_secs(SEGUNDOS).await;
    muestreo::parar();
    let giros = cuentas(RANURA_BANCO).giros.wrapping_sub(giros_antes);
    let libre = medidor.libre_por_mil();

    info!(
        "perfil_pc: firmware {}, f_cpu {} Hz, segundos {}, giros {}, muestras {}, fuera {}, ciclos_timer {}, hilo_libre_permil {}, base {:#x}, cubo {}, cubos {}, histograma {:#x}",
        env!("SAM17_GIT"),
        f_cpu,
        SEGUNDOS,
        giros,
        muestreo::MUESTRAS.load(core::sync::atomic::Ordering::Relaxed),
        muestreo::FUERA.load(core::sync::atomic::Ordering::Relaxed),
        ciclos_timer,
        libre,
        muestreo::BASE,
        muestreo::CUBO,
        muestreo::CUBOS as u32,
        core::ptr::addr_of!(muestreo::HISTOGRAMA) as u32
    );
    // Un `bkpt` para que `probe-rs run` termine solo y el histograma se pueda
    // leer con el nucleo parado.
    cortex_m::asm::bkpt();
    loop {
        Timer::after_secs(60).await;
    }
}
