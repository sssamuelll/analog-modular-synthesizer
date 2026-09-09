#![no_std]
#![no_main]

//! El firmware del cerebro del SAM17 sobre STM32N657X0.
//!
//! Capa DELGADA a proposito: si una funcion de aqui merece un test, es que
//! vive en la caja equivocada y se muda a `sam17-nucleo-core`. Todo lo que se
//! puede probar sin placa ya viene probado de alla.

mod usb;

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::rcc::mux::Otgphysel;
use embassy_stm32::rcc::{IcConfig, Icint, Icsel, Pll, Plldivm, Pllpdiv, Pllsel, SupplyConfig};
use embassy_stm32::Config;
use sam17_nucleo_core::descubrimiento::{placa_de, voces_del_instrumento, TIPO_VCO4};
use sam17_nucleo_core::partes::{Parte, Partes, Repartidor};
use sam17_nucleo_core::pinout::{N_PINES_USADOS, PINOUT};
use sam17_nucleo_core::servidor::{Instrumento, VERSION_PROTOCOLO};
use static_cell::StaticCell;
use {defmt_rtt as _, panic_probe as _};

static INSTRUMENTO: StaticCell<Instrumento> = StaticCell::new();

/// HUECO: tabla mínima de partes mientras no existe el descubrimiento real.
/// `docs/architecture-poly.md:567` declara cuatro canales SSI2130 y el catálogo
/// de `core/src/descubrimiento.rs:111-138` los identifica con `TIPO_VCO4`; al
/// aplicar la regla del mínimo de la cadena, esa única placa da cuatro voces.
/// El papel no fija canal, rango ni preset, así que se declara una sola parte
/// operativa: canal 0, todo el rango MIDI y preset 0.
///
/// La sustituye el descubrimiento por EEPROM (#175). Borrar esta constante
/// cuando ese descubrimiento exista.
const TABLA_DE_PARTES_PROVISIONAL_HASTA_DESCUBRIMIENTO_EEPROM_175: [Parte; 1] = [Parte {
    canal: 0,
    nota_min: 0,
    nota_max: 127,
    voces: 4,
    primera_voz: 0,
    preset: 0,
}];

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let mut config = Config::default();
    // La Discovery usa alimentacion externa; la interna deja init() esperando
    // VOSRDY. Fuente: examples/stm32n6/src/bin/usb_serial.rs de embassy (rev dc6b716) (UM3300, tabla 6).
    config.rcc.supply_config = SupplyConfig::External;

    // Relojes copiados sin cambiar valores del mismo ejemplo: el PHY necesita
    // 19,2, 20 o 24 MHz (RM0486 Rev 4, USBPHYC_CR.FSEL, p. 3929, citado alli).
    // HSI 64 MHz / DIVM 4 * DIVN 60 = VCO 960 MHz; / DIVP1 2 / DIVP2 1
    // da PLL4 480 MHz; IC15 / 20 da 24 MHz sin depender del cristal de placa.
    config.rcc.pll4 = Some(Pll::Oscillator {
        source: Pllsel::Hsi,
        divm: Plldivm::Div4,
        fractional: 0,
        divn: 60,
        divp1: Pllpdiv::Div2,
        divp2: Pllpdiv::Div1,
    });
    config.rcc.ic15 = Some(IcConfig {
        source: Icsel::Pll4,
        divider: Icint::Div20,
    });
    config.rcc.mux.otgphy1sel = Otgphysel::Ic15;
    let p = embassy_stm32::init(config);

    info!("SAM17: el cerebro arranco, protocolo v{}", VERSION_PROTOCOLO);
    info!("{} pines en el mapa", N_PINES_USADOS);
    for pin in PINOUT.iter() {
        defmt::debug!("GPIO{}: {}", pin.gpio, pin.para);
    }

    let vco = placa_de(TIPO_VCO4).expect("TIPO_VCO4 no está en el catálogo");
    let n_voces = voces_del_instrumento(&[vco]);
    assert_eq!(
        n_voces, TABLA_DE_PARTES_PROVISIONAL_HASTA_DESCUBRIMIENTO_EEPROM_175[0].voces,
        "la tabla provisional y el catálogo discrepan"
    );
    let partes = Partes::from_slice(
        &TABLA_DE_PARTES_PROVISIONAL_HASTA_DESCUBRIMIENTO_EEPROM_175,
    )
    .expect("la tabla provisional de partes no cabe");
    info!(
        "HUECO: tabla de partes provisional declarada: {} parte, {} voces; la sustituye EEPROM #175",
        partes.len(),
        n_voces
    );

    let instrumento = INSTRUMENTO.init(
        Instrumento::con_medidas().con_partes(partes, Repartidor::nueva(n_voces)),
    );
    info!(
        "sin descubrimiento todavia: {} parametros, todos de medida",
        instrumento.modelo().len()
    );

    let puertos = usb::montar(p.USB1_OTG_HS);
    spawner.spawn(usb::correr_usb(puertos.dispositivo).unwrap());
    spawner.spawn(usb::atender(puertos.midi, instrumento).unwrap());
}
