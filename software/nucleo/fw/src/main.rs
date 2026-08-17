#![no_std]
#![no_main]

//! El firmware del cerebro del SAM17 sobre RP2350.
//!
//! Capa DELGADA a proposito: si una funcion de aqui merece un test, es que
//! vive en la caja equivocada y se muda a `sam17-nucleo-core`. Todo lo que se
//! puede probar sin placa ya viene probado de alla.

mod usb;

use defmt::info;
use embassy_executor::Spawner;
use embassy_rp::block::ImageDef;
use sam17_nucleo_core::pinout::{N_PINES_USADOS, PINOUT};
use sam17_nucleo_core::servidor::{Instrumento, VERSION_PROTOCOLO};
use static_cell::StaticCell;
use {defmt_rtt as _, panic_probe as _};

/// El bootloader de la ROM del RP2350 solo ejecuta una imagen que traiga un
/// IMAGE_DEF valido, y tiene que caer en los primeros 4 K de flash. Sin esto
/// el chip no arranca, aunque el binario enlace.
#[link_section = ".start_block"]
#[used]
static IMAGE_DEF: ImageDef = ImageDef::secure_exe();

static INSTRUMENTO: StaticCell<Instrumento> = StaticCell::new();

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let p = embassy_rp::init(Default::default());

    info!("SAM17: el cerebro arranco, protocolo v{}", VERSION_PROTOCOLO);
    info!("{} pines en el mapa", N_PINES_USADOS);
    for pin in PINOUT.iter() {
        defmt::debug!("GPIO{}: {}", pin.gpio, pin.para);
    }

    // Hoy el instrumento arranca solo con las medidas de §7.3. El
    // descubrimiento por I²C llega con el plan de los perifericos, y hasta
    // entonces esto lo DICE en vez de fingir que tiene modulos.
    let instrumento = INSTRUMENTO.init(Instrumento::con_medidas());
    info!(
        "sin descubrimiento todavia: {} parametros, todos de medida",
        instrumento.modelo().len()
    );

    let driver = embassy_rp::usb::Driver::new(p.USB, usb::Irqs);
    let puertos = usb::montar(driver);
    spawner.spawn(usb::correr_usb(puertos.dispositivo).unwrap());
    spawner.spawn(usb::atender(puertos.midi, instrumento).unwrap());
}
