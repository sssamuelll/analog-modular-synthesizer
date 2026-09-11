//! El driver del J2 del lado del maestro. Hoy, solo la CABECERA.
//!
//! El cuerpo es la tarea 7 de
//! `docs/superpowers/plans/2026-09-04-maestro-j2-recuperacion.md` (fase B) y
//! se escribe con TDD en su propio PR. Lo que vive aqui es lo que ese plan
//! manda como primer paso: *«compilar un `j2_spi.rs` vacio contra las cuatro
//! APIs de §1.2»* de la spec. La puerta (`cargo build --release`) vuelve a
//! comprobar en cada push que embassy, en la rev que fija `Cargo.lock`, sigue
//! exponiendo lo que el driver necesita. Si embassy renombra una, rompe aqui y
//! no el dia de la placa.
//!
//! Lo que el driver tiene que hacer y embassy no hace (spec D1-D4):
//!
//! - `TSIZE = N` y NSS por hardware en cada transferencia (D1);
//! - las DOS esperas (los dos DMA y el `EOT` por `EOTIE`) bajo UN solo plazo
//!   (D2, D3): el `finish_dma` de embassy espera `EOT` en un bucle sincrono
//!   que un `with_timeout` por fuera no puede vencer;
//! - los ocho pasos del reinicio de D4, en orden, con su pagina del RM0486;
//! - buferes de DMA en region MPU no cacheable (R-MJ7).
//!
//! Ojo con el nombre: el plan dice `spi_v4`; el cfg que embassy pone para el
//! N657 es `spi_v5` (su `build.rs`, de `STM32N657X0.json`: `spi` version
//! `v5`), y el driver de embassy trata `spi_v4`, `spi_v5` y `spi_v6` juntos.
//! Los registros son los del cap. 67 del RM0486 igual.

#![allow(dead_code)] // cabecera sin cuerpo: nada de esto se llama todavia

use embassy_stm32::dma::{self, InterruptHandler, TransferOptions};
use embassy_stm32::interrupt::typelevel::Binding;
use embassy_stm32::{rcc, spi, Peri};

/// Lo que devuelve un giro. Los tres nombres son los de la spec (D2, D3), y
/// son los que `core::maestro_j2::Evento` espera del otro lado.
#[derive(Clone, Copy, PartialEq, Eq, Debug, defmt::Format)]
pub enum Resultado {
    /// Los dos DMA terminaron y llego `EOT` dentro del plazo.
    Ok,
    /// El plazo vencio antes: el periferico se reinicia (D4).
    PlazoVencido,
    /// Llego un `EOT` de una generacion vieja, despues de vencido el plazo.
    EotTardio,
}

/// Las cuatro piezas publicas de embassy que el driver necesita (spec §1.2),
/// puestas en posicion de tipo para que el compilador las verifique. No se
/// llama nunca: existe para que compile, y para que deje de compilar el dia
/// que embassy cambie una firma.
async fn las_cuatro_apis<'d, T, Tx, Rx>(
    tx: Peri<'d, Tx>,
    rx: Peri<'d, Rx>,
    irq_tx: impl Binding<Tx::Interrupt, InterruptHandler<Tx>> + 'd,
    irq_rx: impl Binding<Rx::Interrupt, InterruptHandler<Rx>> + 'd,
    txdr: *mut u8,
    rxdr: *mut u8,
    bajada: &'d [u8],
    subida: &'d mut [u8],
) where
    T: spi::Instance,
    Tx: spi::TxDma<T>,
    Rx: spi::RxDma<T>,
{
    // 1. `rcc::enable_and_reset::<T>()`: el reloj y el reset del periferico,
    //    que es el paso 0 de los ocho del reinicio de D4.
    rcc::enable_and_reset::<T>();
    // 4. `spi::TxDma::request()` y su gemelo `RxDma`: el numero de peticion
    //    del GPDMA para este SPI (RM0486 Tabla 86).
    let req_tx = tx.request();
    let req_rx = rx.request();
    // 2. `dma::Channel::new`: un canal del GPDMA con su interrupcion.
    let mut canal_tx = dma::Channel::new(tx, irq_tx);
    let mut canal_rx = dma::Channel::new(rx, irq_rx);
    // 3. `Channel::write` / `Channel::read` (peticion, bufer, registro,
    //    opciones): las dos transferencias que D2 espera con `join`.
    let escribe = unsafe { canal_tx.write(req_tx, bajada, txdr, TransferOptions::default()) };
    let lee = unsafe { canal_rx.read(req_rx, rxdr, subida, TransferOptions::default()) };
    embassy_futures::join::join(escribe, lee).await;
}
