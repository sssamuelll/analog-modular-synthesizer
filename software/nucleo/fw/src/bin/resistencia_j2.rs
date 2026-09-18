#![no_std]
#![no_main]

//! **El soak del J2: el punto (3) del orden del dia, y la puerta de
//! fabricacion.**
//!
//! Enmienda del 11-09 a la sec.9 del papel del maestro, punto 1 (ficha 1 del
//! acta): *«Ninguna PCB con N657 sale al taller sin una fila medida en
//! `resistencia_j2.csv`. Antes era criterio de cierre del riesgo 1; desde hoy es
//! prohibicion»*. Este binario es lo que produce esa fila.
//!
//! El montaje del banco entero, tal como lo usara el instrumento: la ranura 0 en
//! **SPI5** con `TSIZE > 0` y NSS por hardware, en el `EJECUTOR_J2` con la
//! politica de `core` detras ([`j2_ejecutor::arrancar`]), y el esclavo del banco
//! en **SPI4** como tarea del mismo ejecutor. Retardo de produccion, 4 cuartos
//! de `T_SCK` (D2, enmienda del 11-09). Cada hora publica su fila.
//!
//! **Como se juzga la fila, que no es *«tiene fila»*.** Ficha 2 del acta: el
//! limite es **cero artefactos audibles** atribuibles al bus, y para ser medible
//! necesita un horizonte -- cero en cuantas horas de instrumento -- que es HUECO
//! de Samuel. La aritmetica que lo convierte en puerta: con cero eventos en `T`
//! horas de soak, la tasa queda por debajo de `3/T` al 95 % (regla de tres,
//! Poisson), y *«cero en H horas»* exige del orden de `3·H` horas limpias **con
//! el control positivo hecho**. Un soak verde sin control positivo no distingue
//! *«no nos afecta»* de *«el banco no lo ve»*: por eso este binario es el
//! tercero y no el primero.
//!
//! **Las dos tandas.** Primero el piso legado, 10 MHz; despues, si hay sancion,
//! el peldano 2 (34,5 MHz, `enlace_budget.py:71`). Se cambia [`F_SCK_HZ`] y se
//! vuelve a correr: la columna `reloj_MHz` de la fila lleva el **real**, el que
//! sale del `MBR`, no el pedido.
//!
//! **Lo que no dice la fila.** `subidas_malas` cuenta contra el esclavo del
//! banco, que devuelve un patron fijo; no es el CRC del sobre, que llega con
//! #267. Y `tramas_cortas` del esclavo tiene tres causas distintas que solo el
//! analizador logico separa: estan en la cabecera de [`j2_esclavo`], y por eso
//! se publican en su propia linea junto a `plazos_vencidos`, que es la que las
//! discrimina.
//!
//! ```bash
//! cargo run --release --bin resistencia_j2
//! ```

use core::sync::atomic::Ordering;

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt::{InterruptExt, Priority};
use embassy_stm32::{dma, interrupt, pac, peripherals};
use embassy_time::{Duration, Ticker};
use sam17_nucleo_fw::j2_banco::{bajada_del_banco, juez_del_banco, LARGO_BANCO};
use sam17_nucleo_fw::j2_ejecutor::{arrancar, cuentas, EJECUTOR_J2};
use sam17_nucleo_fw::j2_esclavo::{self, Esclavo};
use sam17_nucleo_fw::j2_spi::{self, Config, Ranura, ESCALADAS_GPDMA};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

embassy_stm32::bind_interrupts!(struct Irqs {
    SPI5 => j2_spi::Isr<0>;
    GPDMA1_CHANNEL0 => dma::InterruptHandler<peripherals::GPDMA1_CH0>;
    GPDMA1_CHANNEL1 => dma::InterruptHandler<peripherals::GPDMA1_CH1>;
    GPDMA1_CHANNEL2 => dma::InterruptHandler<peripherals::GPDMA1_CH2>;
    GPDMA1_CHANNEL3 => dma::InterruptHandler<peripherals::GPDMA1_CH3>;
    EXTI11 => j2_esclavo::IsrCs;
});

/// El reloj del enlace para esta tanda. **Piso legado, 10 MHz** (J2 punto a
/// punto D2; `F_CONTRATO_HZ` de `hardware/02-midi-cv/trama_j2_budget.py:89`).
/// La segunda tanda es el peldano 2, `34_480_000` (D8;
/// `hardware/02-midi-cv/enlace_budget.py:71`, `F_PELDANO_2_HZ`), y se dice sola
/// en la columna `reloj_MHz` de la fila.
const F_SCK_HZ: u32 = 10_000_000;

/// El retardo de produccion: 4 cuartos, o sea `>= 1 T_SCK` (D2, enmienda del
/// 11-09). El barrido de los otros cinco valores es `barrido_retardo`.
const RETARDO_CUARTOS: u8 = 4;

/// La ranura del banco. Va en el sitio 0 de la fila y del arreglo de `arrancar`.
const RANURA: usize = 0;

/// La columna `instancia` de la fila: el SPI del maestro. SPI5 a proposito, que
/// es la instancia del repro original de jake-taf (EN-PLACA, montaje del 11-09).
const INSTANCIA: &str = "SPI5";

/// La columna `nss`: `hw` = NSS por hardware del periferico (D1), no un GPIO.
const NSS: &str = "hw";

/// La columna `placa`. La `fecha` va vacia: la pone quien copia la fila.
const PLACA: &str = "NUCLEO-N657X0-Q";

/// El `f_sck` real en MHz, tal como tiene que quedar en la columna `reloj_MHz`:
/// entero cuando lo es (`8`), y con tres decimales cuando no (`0.500`).
///
/// Existe para que la fila entera salga en **un solo** `info!`: partirla en dos
/// ramas con la misma lista de doce columnas seria la forma mas facil de que una
/// de las dos se quedara atras.
struct Mhz(u32);

impl defmt::Format for Mhz {
    fn format(&self, f: defmt::Formatter) {
        let ent = self.0 / 1_000_000;
        let frac = self.0 % 1_000_000;
        if frac == 0 {
            defmt::write!(f, "{=u32}", ent)
        } else {
            // El `MBR` solo divide por potencias de dos (sec.67.11.3), asi que
            // tres decimales cubren hasta `f_ker/256` con f_ker de 64 MHz.
            defmt::write!(f, "{=u32}.{=u32:03}", ent, frac / 1_000)
        }
    }
}

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = embassy_stm32::init(config);

    // Las ISR del SPI y de los canales del GPDMA a `P1`, por encima del
    // `EJECUTOR_J2` (`P2`), y ANTES de construir la ranura (EN-PLACA, casilla
    // del 11-09). Los canales ya estan habilitados en el NVIC por
    // `embassy_stm32::init` (`dma/gpdma/mod.rs:526-534`); la linea del SPI5 no
    // la habilita nadie, y sin ella el `EOT` no llega y todos los giros
    // venceria plazo.
    interrupt::SPI5.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL0.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL1.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL2.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL3.set_priority(Priority::P1);
    // SAFETY: la unica forma de desenmascarar la linea. El manejador existe
    // porque `Irqs` ata `SPI5 => j2_spi::Isr<0>`.
    unsafe { interrupt::SPI5.enable() };

    let ranura = Ranura::nueva::<peripherals::SPI5, _, _, _, _, _, _>(
        RANURA,
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
    // El `f_sck` REAL se lee **antes** de entregar la ranura al ejecutor: a
    // partir de `arrancar` la `Ranura` vive dentro de su tarea y no hay forma de
    // preguntarle. Y es el real, no el pedido: el `MBR` redondea hacia abajo, y
    // una fila etiquetada con el pedido mentiria sobre a que reloj se midio.
    let f_sck_hz = ranura.f_sck_hz();
    info!(
        "resistencia_j2: f_sck {} Hz (pedido {}), retardo {} cuartos, f_cpu {} Hz",
        f_sck_hz, F_SCK_HZ, RETARDO_CUARTOS, f_cpu
    );

    let esclavo = Esclavo::nuevo::<peripherals::SPI4, _, _, _, _, _, _>(
        pac::SPI4,
        p.PE2,
        p.PE14,
        p.PE13,
        p.PE11,
        p.GPDMA1_CH2,
        p.GPDMA1_CH3,
        Irqs,
        LARGO_BANCO,
    );

    arrancar(
        interrupt::GFXTIM,
        [Some(ranura), None, None, None, None, None],
        bajada_del_banco,
        juez_del_banco,
    );
    EJECUTOR_J2
        .spawner()
        .spawn(defmt::unwrap!(j2_esclavo::tarea_esclavo(esclavo)));

    let mut ticker = Ticker::every(Duration::from_secs(3600));
    let mut horas = 0u32;
    loop {
        ticker.next().await;
        horas += 1;
        let c = cuentas(RANURA);

        // La fila de `resistencia_j2.csv`, con sus doce columnas en el orden de
        // R-MJ8: `ranura,instancia,tsize,nss,reloj_MHz,horas,giros,
        // plazos_vencidos,eot_tardios,subidas_malas,fecha,placa`. `fecha` va
        // vacia -- la pone quien copia la fila --, y por eso hay dos comas
        // seguidas antes de `placa`.
        info!(
            "{=usize},{=str},{=usize},{=str},{},{=u32},{=u32},{=u32},{=u32},{=u32},,{=str}",
            RANURA,
            INSTANCIA,
            LARGO_BANCO,
            NSS,
            Mhz(f_sck_hz),
            horas,
            c.giros,
            c.plazos_vencidos,
            c.eot_tardios,
            c.subidas_malas,
            PLACA
        );
        info!(
            "esclavo,tramas_ok={},tramas_cortas={},rearmes_escalados={}",
            j2_esclavo::TRAMAS_OK.load(Ordering::Relaxed),
            j2_esclavo::TRAMAS_CORTAS.load(Ordering::Relaxed),
            j2_esclavo::REARMES_ESCALADOS.load(Ordering::Relaxed),
        );
        info!(
            "maestro,escaladas_gpdma={},inestable={},muda={}",
            ESCALADAS_GPDMA.load(Ordering::Relaxed),
            c.inestable,
            c.muda,
        );
    }
}
