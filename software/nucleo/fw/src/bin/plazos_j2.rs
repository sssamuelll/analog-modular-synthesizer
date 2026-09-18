#![no_std]
#![no_main]

//! **Los plazos contra el osciloscopio: el punto (4) del orden del dia.**
//!
//! Riesgo 2 del papel del maestro (`docs/superpowers/specs/`
//! `2026-09-03-maestro-j2-recuperacion-design.md`, sec.9): *«Los ESTIMADO de D3
//! se quedan cortos y el plazo vence en tramas sanas (falsos reinicios)»*.
//! `FACTOR_PLAZO = 2` y `T_SUELO_PLAZO = 20 us` no tienen fuente: los sella esta
//! medida.
//!
//! Por cada mensaje de la cabecera ([`j2_banco::LARGOS_MENSAJES`]) se clocan
//! [`GIROS_POR_MENSAJE`] tramas de su largo, con un GPIO que **sube justo antes
//! de `giro` y baja al volver**. En el osciloscopio, el ancho del pulso es
//! `t_real(msg)`; el `defmt` da `t_nominal(msg)` y el `plazo(msg)` que la
//! politica calcularia. Con eso:
//!
//! - `FACTOR_PLAZO` se fija con **>= 3x el peor exceso medido**
//!   (`t_real / t_nominal`);
//! - `T_SUELO_PLAZO` con el retraso de ISR que se vea en el mensaje mas corto,
//!   `HOLA`, donde el termino nominal casi no pesa.
//!
//! Los dos se cambian en **un solo sitio**, `core::maestro_j2::Umbrales::`
//! `POR_DEFECTO` (R-MJ4). Este binario no copia ninguno: los lee de ahi, y hasta
//! el `t_nominal` que imprime sale de despejar `plazo_us`, para que no haya dos
//! cuentas de lo mismo.
//!
//! **El esclavo esta apagado a proposito, y el MISO (PG1) va al aire.** El
//! esclavo del banco compara contra un `esperado` **fijo** de 25 bytes
//! ([`j2_banco::LARGO_BANCO`]), asi que los siete largos que no son 25 -- `HOLA`
//! con 9, `SET` con 103 -- le contarian `TRAMAS_CORTAS` por construccion, y las
//! cortas de verdad, que son las tres causas de la cabecera de
//! [`sam17_nucleo_fw::j2_esclavo`], quedarian enterradas. Lo que aqui se mide es
//! el **maestro**: cuanto tarda de verdad su giro. Con el MISO al aire la subida
//! es basura y no se juzga.
//!
//! **El pin del osciloscopio: PE7, CN15 pin 22.** UM3417 Rev 3, Tabla 13, p. 32.
//! Se eligio porque es el unico del CN15, junto a PE1, que **no aparece en
//! ninguna otra tabla del manual**: no esta en el mapa Arduino (Tabla 12, p.
//! 30), no es ninguno de los ocho del J2 (SPI5 PE15/PG2/PG1/PA3, SPI4
//! PE2/PE14/PE13/PE11), no es PE10 -- el plan B del `CS` del esclavo --, no es
//! PE12, el SCK alternativo de SPI4, y no toca nada del bring-up: los LED son
//! PG10 (LD5), PG0 (LD6), PG8 (LD7) y PB15 (LD3), el boton es PC13, y el ST-LINK
//! se lleva PB14/PB15 y PC3/PC4 (UM3417 sec.7.5, sec.7.6 y Tabla 16).
//!
//! **La bajada.** El mismo patron del banco, `0x5A ^ i`, rellenado hasta el
//! largo del mensaje. No es el sobre de la cabecera -- no existe todavia
//! (#267) -- y no hace falta que lo sea: lo que se mide es el **transporte**, y
//! al cable le da igual que byte viaja.
//!
//! ```bash
//! cargo run --release --bin plazos_j2
//! ```

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::gpio::{Level, Output, Speed};
use embassy_stm32::interrupt::{InterruptExt, Priority};
use embassy_stm32::{dma, interrupt, pac, peripherals};
use embassy_time::{Duration, Timer};
use sam17_nucleo_core::maestro_j2::{plazo_us, Tsize, Umbrales};
use sam17_nucleo_fw::j2_banco::LARGOS_MENSAJES;
use sam17_nucleo_fw::j2_spi::{self, Config, Ranura, LARGO_MAX};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

embassy_stm32::bind_interrupts!(struct Irqs {
    SPI5 => j2_spi::Isr<0>;
    GPDMA1_CHANNEL0 => dma::InterruptHandler<peripherals::GPDMA1_CH0>;
    GPDMA1_CHANNEL1 => dma::InterruptHandler<peripherals::GPDMA1_CH1>;
});

/// El piso legado del enlace, 10 MHz (J2 punto a punto D2; `F_CONTRATO_HZ` de
/// `hardware/02-midi-cv/trama_j2_budget.py:89`). Es donde los plazos aprietan:
/// `t_nominal` es maximo y el peor mensaje, `SET` de dieciseis, gasta el 82 % de
/// los 100 us de R-E1.
const F_SCK_HZ: u32 = 10_000_000;

/// El retardo de produccion, 4 cuartos (D2, enmienda del 11-09). Se mide con el
/// que el instrumento va a llevar; barrerlo es `barrido_retardo`.
const RETARDO_CUARTOS: u8 = 4;

/// Giros por mensaje. Aqui **no hay cadencia**: los giros salen pegados, uno
/// detras de otro, porque lo que se mide es el ancho del pulso y no el periodo.
/// Mil giros son entonces mil veces `t_real`, que al piso real de 8 MHz va de
/// unos **9 ms** (`HOLA`, 9 bytes) a unos **103 ms** (`SET` de dieciseis, 103
/// bytes): sobra para que el osciloscopio capture el peor pulso con persistencia
/// infinita, y cabe en un disparo unico de pantalla.
const GIROS_POR_MENSAJE: u32 = 1000;

/// Silencio entre rafagas, para que los ocho grupos de pulsos se distingan en la
/// pantalla y se sepa cual es cual sin contar. **No es una cifra fisica**: es de
/// comodidad, y si estorba se cambia.
const SILENCIO_MS: u64 = 500;

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = embassy_stm32::init(config);

    // Las ISR del SPI y de los dos canales del GPDMA a `P1`, ANTES de construir
    // la ranura. Aqui no hay `EJECUTOR_J2` -- el lazo vive en el ejecutor de
    // hilo --, pero la relacion que EN-PLACA fija es de las ISR contra el
    // ejecutor que corra el lazo, y el de hilo esta por debajo de cualquier
    // interrupcion por construccion. Los canales ya los habilito
    // `embassy_stm32::init` (`dma/gpdma/mod.rs:526-534`); la linea del SPI5 no la
    // habilita nadie, y sin ella el `EOT` no llega al NVIC y todos los giros
    // venceria plazo.
    interrupt::SPI5.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL0.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL1.set_priority(Priority::P1);
    // SAFETY: la unica forma de desenmascarar la linea. El manejador existe
    // porque `Irqs` ata `SPI5 => j2_spi::Isr<0>`.
    unsafe { interrupt::SPI5.enable() };

    let mut ranura = Ranura::nueva::<peripherals::SPI5, _, _, _, _, _, _>(
        0,
        pac::SPI5,
        p.PE15,
        p.PG2,
        p.PG1,
        p.PA3,
        p.GPDMA1_CH0,
        p.GPDMA1_CH1,
        Irqs,
        Irqs,
        &p.RCC,
        Config {
            f_sck_hz: F_SCK_HZ,
            f_cpu_hz: f_cpu,
            retardo_tsck_cuartos: RETARDO_CUARTOS,
        },
    );

    // El testigo del osciloscopio. `Low` en reposo, `VeryHigh` para que el
    // flanco no sea lo que se mide.
    let mut testigo = Output::new(p.PE7, Level::Low, Speed::VeryHigh);

    let umbrales = Umbrales::POR_DEFECTO;
    let f_sck_hz = ranura.f_sck_hz();
    info!(
        "plazos_j2: f_sck {} Hz (pedido {}), retardo {} cuartos, f_cpu {} Hz, \
         testigo en PE7 (CN15 pin 22), esclavo apagado y MISO al aire",
        f_sck_hz, F_SCK_HZ, RETARDO_CUARTOS, f_cpu
    );

    let mut bajada = [0u8; LARGO_MAX];
    let mut subida = [0u8; LARGO_MAX];

    // El barrido entero se repite para siempre: el dia de la placa nadie quiere
    // reprogramar entre captura y captura.
    loop {
        for (nombre, largo) in LARGOS_MENSAJES {
            // `Tsize` es `NonZeroU16` y la tabla lo asevera en tiempo de
            // compilacion (`j2_banco`), asi que este `unwrap` no puede saltar.
            let tsize = defmt::unwrap!(Tsize::nuevo(largo));
            let n = largo as usize;

            // El patron del banco rellenado hasta el largo del mensaje. Para
            // `largo = 25` es byte a byte lo que da `j2_banco::bajada_del_banco`.
            for (i, b) in bajada[..n].iter_mut().enumerate() {
                *b = 0x5A ^ (i as u8);
            }

            // El plazo sale de la politica (R-MJ4). `t_nominal` se **despeja** de
            // el en vez de recalcularse: `plazo = FACTOR_PLAZO x t_nominal +
            // T_SUELO_PLAZO` (D3), asi que la resta y la division devuelven el
            // mismo `t_nominal` exacto que uso `plazo_us`, redondeo incluido.
            // Recalcularlo aqui seria una segunda cuenta de lo mismo, y las dos
            // se separan el dia que una cambie.
            let plazo = plazo_us(tsize, f_sck_hz, &umbrales);
            let t_nominal = (plazo - umbrales.t_suelo_plazo_us) / umbrales.factor_plazo;
            info!(
                "plazos,mensaje={=str},tsize={=u16},t_nominal_us={=u32},plazo_us={=u32}",
                nombre, largo, t_nominal, plazo
            );

            let plazo = Duration::from_micros(plazo as u64);
            for _ in 0..GIROS_POR_MENSAJE {
                testigo.set_high();
                let (res, _tardios) = ranura.giro(&bajada, &mut subida, tsize, plazo).await;
                testigo.set_low();
                if let j2_spi::Resultado::PlazoVencido = res {
                    // Un plazo vencido aqui no es ruido de fondo: es el riesgo 2
                    // pasando delante del osciloscopio. El pulso de ese giro
                    // mide el plazo, no la trama, y hay que descartarlo al leer.
                    defmt::warn!(
                        "plazos: {=str} vencio plazo; ese pulso no es t_real",
                        nombre
                    );
                }
            }

            Timer::after(Duration::from_millis(SILENCIO_MS)).await;
        }
    }
}
