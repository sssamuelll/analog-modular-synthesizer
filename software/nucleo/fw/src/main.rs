#![no_std]
#![no_main]

//! El firmware del cerebro del SAM17 sobre RP2350.
//!
//! Capa DELGADA a proposito: si una funcion de aqui merece un test, es que
//! vive en la caja equivocada y se muda a `sam17-nucleo-core`. Todo lo que se
//! puede probar sin placa ya viene probado de alla.

use defmt::info;
use embassy_executor::Spawner;
use embassy_rp::block::ImageDef;
use embassy_time::{Duration, Timer};
use sam17_nucleo_core::pinout::{N_PINES_USADOS, PINOUT};
use {defmt_rtt as _, panic_probe as _};

/// El bootloader de la ROM del RP2350 solo ejecuta una imagen que traiga un
/// IMAGE_DEF valido. Sin esto el chip no arranca, aunque el binario enlace.
#[link_section = ".start_block"]
#[used]
static IMAGE_DEF: ImageDef = ImageDef::secure_exe();

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let _p = embassy_rp::init(Default::default());

    info!("SAM17: el cerebro arranco");
    info!("{} pines en el mapa", N_PINES_USADOS);
    for pin in PINOUT.iter() {
        defmt::debug!("GPIO{}: {}", pin.gpio, pin.para);
    }

    loop {
        Timer::after(Duration::from_secs(1)).await;
    }
}
