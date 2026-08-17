//! El borde del sistema: bytes que entran y salen por el USB.
//!
//! El lazo entero, y por que no lleva un solo test propio — **cada paso ya
//! vino verde en `core`**:
//!
//! ```text
//!   paquete USB  ->  Desempaquetador  ->  desenvolver  ->  decodificar
//!                                                               |
//!                                                      Instrumento::atender
//!                                                               |
//!      MidiClass  <-  empaquetar_sysex  <-  envolver  <-  codificar
//! ```

use defmt::{info, warn};
use embassy_rp::peripherals::USB;
use embassy_rp::usb::{Driver, InterruptHandler};
use embassy_usb::class::midi::MidiClass;
use embassy_usb::{Builder, Config, UsbDevice};
use sam17_nucleo_core::descriptor;
use sam17_nucleo_core::protocolo::{codificar, decodificar, Mensaje};
use sam17_nucleo_core::servidor::{Instrumento, Respuesta};
use sam17_nucleo_core::sysex::{desenvolver, envolver};
use sam17_nucleo_core::usbmidi::{empaquetar_sysex, Desempaquetador, Paquete, Trozo, MAX_SYSEX};
use static_cell::StaticCell;

embassy_rp::bind_interrupts!(pub struct Irqs {
    USBCTRL_IRQ => InterruptHandler<USB>;
});

/// `0x1209` es pid.codes, el rango libre para proyectos abiertos. El PID es de
/// pruebas: registrar uno de verdad es del dia que esto se distribuya, y esta
/// anotado en EN-PLACA.md.
const VID: u16 = 0x1209;
const PID: u16 = 0x0017;

/// 64 bytes es el maximo de un endpoint bulk a full speed.
const TAM_PAQUETE: u16 = 64;

pub type Sam17Usb = UsbDevice<'static, Driver<'static, USB>>;

pub struct Puertos {
    pub dispositivo: Sam17Usb,
    pub midi: MidiClass<'static, Driver<'static, USB>>,
}

pub fn montar(driver: Driver<'static, USB>) -> Puertos {
    let mut config = Config::new(VID, PID);
    config.manufacturer = Some("SAM17");
    config.product = Some("SAM17 nucleo");
    config.serial_number = Some("0001");
    config.max_power = 100;
    config.max_packet_size_0 = 64;

    static CONFIG_DESC: StaticCell<[u8; 256]> = StaticCell::new();
    static BOS_DESC: StaticCell<[u8; 256]> = StaticCell::new();
    static CONTROL_BUF: StaticCell<[u8; 64]> = StaticCell::new();

    let mut builder = Builder::new(
        driver,
        config,
        CONFIG_DESC.init([0; 256]),
        BOS_DESC.init([0; 256]),
        &mut [],
        CONTROL_BUF.init([0; 64]),
    );

    // Un jack de entrada y uno de salida: el instrumento habla y escucha.
    let midi = MidiClass::new(&mut builder, 1, 1, TAM_PAQUETE);

    Puertos { dispositivo: builder.build(), midi }
}

#[embassy_executor::task]
pub async fn correr_usb(mut d: Sam17Usb) -> ! {
    d.run().await
}

/// El lazo. Todo lo que hace es cablear piezas ya probadas.
#[embassy_executor::task]
pub async fn atender(
    mut midi: MidiClass<'static, Driver<'static, USB>>,
    instrumento: &'static mut Instrumento,
) -> ! {
    let mut desemp = Desempaquetador::nuevo();
    let mut entrada: Paquete = [0; 4];
    let mut plano = [0u8; MAX_SYSEX];

    loop {
        midi.wait_connection().await;
        info!("USB: un cliente se conecto");
        desemp.reiniciar();

        loop {
            match midi.read_packet(&mut entrada).await {
                Ok(4) => {}
                Ok(n) => {
                    // USB-MIDI son paquetes de cuatro bytes. Otra cosa no es
                    // nuestra: se tira sin tocar el mensaje en curso.
                    warn!("USB: paquete de {} bytes, se ignora", n);
                    continue;
                }
                Err(_) => break, // se desconecto; a esperar de nuevo
            }

            let Some(Trozo::Sysex(bytes)) = desemp.empujar(&entrada) else {
                // Notas y CC son del plan de los perifericos: todavia no hay
                // gates ni J2 a donde mandarlas.
                continue;
            };

            let Ok(n) = desenvolver(bytes, &mut plano) else {
                warn!("USB: sobre que no es nuestro, se ignora");
                continue;
            };
            let Ok(m) = decodificar(&plano[..n]) else {
                warn!("USB: mensaje que no se entiende");
                continue;
            };

            let ahora = embassy_time::Instant::now().as_millis();
            for resp in instrumento.atender(m, ahora) {
                if responder(&mut midi, instrumento, resp).await.is_err() {
                    break;
                }
            }
        }
    }
}

async fn responder(
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
    instrumento: &Instrumento,
    resp: Respuesta,
) -> Result<(), ()> {
    match resp {
        Respuesta::Mensaje(m) => mandar_mensaje(midi, &m).await,
        Respuesta::Descriptores => mandar_descriptores(midi, instrumento).await,
    }
}

async fn mandar_mensaje(
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
    m: &Mensaje,
) -> Result<(), ()> {
    let mut plano = [0u8; 64];
    let n = codificar(m, &mut plano).map_err(|_| ())?;
    let mut sobre = [0u8; 128];
    let s = envolver(&plano[..n], &mut sobre).map_err(|_| ())?;
    mandar_sysex(midi, &sobre[..s]).await
}

/// El volcado del descriptor: uno por sobre. Mandarlos de a uno mantiene los
/// buffers pequeños y deja que el cliente empiece a parsear antes de que
/// termine — que con 27 medidas ya se nota.
async fn mandar_descriptores(
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
    instrumento: &Instrumento,
) -> Result<(), ()> {
    let mut plano = [0u8; 256];
    let mut sobre = [0u8; 384];
    for d in instrumento.modelo().descriptores() {
        let n = descriptor::escribir(d, &mut plano).map_err(|_| ())?;
        let s = envolver(&plano[..n], &mut sobre).map_err(|_| ())?;
        mandar_sysex(midi, &sobre[..s]).await?;
    }
    Ok(())
}

async fn mandar_sysex(
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
    sobre: &[u8],
) -> Result<(), ()> {
    let mut paquetes = [[0u8; 4]; MAX_SYSEX / 3 + 1];
    let np = empaquetar_sysex(sobre, &mut paquetes).map_err(|_| ())?;
    for p in &paquetes[..np] {
        midi.write_packet(p).await.map_err(|_| ())?;
    }
    Ok(())
}
