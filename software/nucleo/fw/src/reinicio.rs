//! El reset por software, con los diez selectores de reloj puestos en su valor
//! por defecto antes de pulsarlo.
//!
//! **Nadie llama a esto todavia.** Hoy el firmware no se resetea a si mismo:
//! `panic-probe` se queda parado en el panico y no hay ningun otro camino que
//! pida reinicio. Esta funcion existe para que el PRIMERO que necesite
//! resetear llame aqui en vez de escribir `SCB::sys_reset()` a pelo -- porque a
//! pelo el chip puede no volver, y en el banco no se distingue de un binario
//! roto. El procedimiento de rescate esta en `ARRANQUE.md`.
//!
//! ES0620 Rev 5 §2.2.22 (p. 12), entera:
//!
//! > *«Upon a software reset, the RCC_CCIPRx registers duly revert to their
//! > default values, but the clock switches controlled by the PERxSEL bitfields
//! > in these registers may fail to output the corresponding clock signals.
//! > Consequently, the boot ROM code execution may fail if the clock switch
//! > states before the reset differ from their default states for peripherals
//! > used during the ROM boot sequence.»*
//!
//! Y su workaround, misma pagina:
//!
//! > *«Before performing a software reset, ensure that the following clock
//! > switch control bitfields are set to their default values and that the
//! > selected clocks are properly supplied to their corresponding
//! > peripherals»*
//!
//! Son **dos** obligaciones, no una: el valor por defecto Y el reloj puesto.
//! La segunda es §2.2.23 de la misma pagina, que ademas desmiente al manual:
//!
//! > *«switching from one clock (initial) to another (target) requires both
//! > clocks to be present at the clock switch inputs. If either clock is
//! > missing, the output provides no clock signal.»*
//!
//! Los diez bitfields, con el valor por defecto de la tabla de la p. 12
//! COTEJADO contra el valor de reset del registro en el RM0486 Rev 4 -- que es
//! lo que hace que la tabla aplanada del PDF se pueda leer sin adivinar:
//!
//! ```text
//!   registro      reset (RM0486)   bitfield             defecto   reloj que elige
//!   RCC_CCIPR6    0x0000_0000      XSPI1SEL[1:0]          0x0     hclk5
//!    p. 534                        OTGPHY1CKREFSEL        0x0     otgphy1_ker_ck
//!   RCC_CCIPR7    0x0000_0200      PERSEL[2:0]            0x0     hsi_ck
//!    p. 536                        RTCSEL[1:0]            0x2     lsi_ck
//!   RCC_CCIPR8    0x0000_0000      SDMMC1SEL[1:0]         0x0     hclku
//!    p. 538                        SDMMC2SEL[1:0]         0x0     hclku
//!   RCC_CCIPR13   0x0000_0000      USART1SEL[2:0]         0x0     pclk2
//!    p. 542                        USART2SEL[2:0]         0x0     pclk1
//!                                  UART4SEL[2:0]          0x0     pclk1
//!                                  UART5SEL[2:0]          0x0     pclk1
//! ```
//!
//! El unico defecto que no es cero es **RTCSEL = 0x2**, y el reset de
//! `RCC_CCIPR7` lo confirma solo: `0x0000_0200` es el bit 9 puesto, y RTCSEL
//! son los bits [9:8] (RM0486 Rev 4, p. 536-537). `0x2` es lsi_ck (p. 537).
//!
//! **El §2.2.23, reloj a reloj, tras `embassy_stm32::init(usb::configuracion())`:**
//! hclk5 y hclku son el AHB, pclk1 y pclk2 los APB, y los cuatro salen siempre
//! encendidos del `init` de embassy (`rcc/n6.rs`: `hclk5`, `hclku`, `pclk1` y
//! `pclk2` se publican como `Some(...)` incondicionalmente). hsi_ck tambien:
//! `Config::default()` lo deja encendido y ademas es la entrada de la PLL4 que
//! alimenta al PHY (`usb.rs`). otgphy1_ker_ck es ic15_ck, que `usb.rs`
//! enciende. Queda **lsi_ck**, el unico que depende de un campo de
//! configuracion que no se ve desde aqui (`config.rcc.ls`): hoy viene
//! encendido porque `LsConfig::default()` es `default_lsi()` (`rcc/bd.rs`,
//! `lsi: true`), pero el dia que alguien ponga `LsConfig::off()` o
//! `default_lse()` se apaga y este reset escribiria RTCSEL sin su reloj. Por
//! eso se enciende aqui antes de escribir, y asi la funcion no depende de una
//! decision que vive en otro crate.

use embassy_stm32::pac;
use embassy_stm32::pac::rcc::vals::{
    Persel, Rtcsel, Sdmmcsel, Uart16910sel, Uart234578sel, Xspisel,
};

/// Puerta de compilacion: los nombres de abajo son los del metapac, pero los
/// numeros son los de la tabla de la p. 12. Esto ata las dos cosas, y deja de
/// enlazar el dia que el metapac renumere o renombre un variante bajo nuestros
/// pies.
const _: () = {
    assert!(Xspisel::Hclk5.to_bits() == 0x0);
    assert!(Persel::Hsi.to_bits() == 0x0);
    assert!(Rtcsel::Lsi.to_bits() == 0x2);
    assert!(Sdmmcsel::Hclku.to_bits() == 0x0);
    assert!(Uart16910sel::Pclk2.to_bits() == 0x0);
    assert!(Uart234578sel::Pclk1.to_bits() == 0x0);
};

/// Resetea el chip por software dejando antes los diez selectores de la
/// p. 12 en su valor por defecto. No vuelve.
///
/// El orden es el del workaround y no se puede barajar: primero los relojes en
/// su sitio, luego la barrera, luego el reset.
#[allow(dead_code)] // Nadie resetea todavia; ver el `//!` de este modulo.
pub fn por_software() -> ! {
    let rcc = pac::RCC;

    // §2.2.23: RTCSEL va a lsi_ck, asi que lsi_ck tiene que estar. Misma
    // secuencia que usa embassy en su propio `init` (`rcc/bd.rs`, rama
    // `rcc_n6`): LSION en `RCC_CR` y esperar LSIRDY en `RCC_SR`. La espera es
    // sin cota, igual que la de embassy: si el LSI no arranca, el chip no
    // tiene de donde sacar el defecto de RTCSEL y resetear seria peor.
    if !rcc.sr().read().lsirdy() {
        rcc.cr().modify(|w| w.set_lsion(true));
        while !rcc.sr().read().lsirdy() {}
    }

    // RCC_CCIPR6 (RM0486 Rev 4, p. 534, reset 0x0000_0000).
    rcc.ccipr6().modify(|w| {
        w.set_xspi1sel(Xspisel::Hclk5); // XSPI1SEL = 0x0 (ES0620 p. 12)
        w.set_otgphy1ckrefsel(false); // OTGPHY1CKREFSEL = 0x0 (ES0620 p. 12)
    });

    // RCC_CCIPR7 (RM0486 Rev 4, p. 536, reset 0x0000_0200).
    //
    // RTCSEL esta protegido en escritura por `pwr_lock_backup_n` (RM0486
    // Rev 4, p. 537): con el dominio de respaldo bloqueado esta escritura se
    // pierde en silencio. Hoy no pasa -- el `init` de embassy hace `DBP = 1`
    // en `PWR_DBPCR` y NO lo vuelve a bloquear (`rcc/bd.rs`, `unlock()`) --,
    // pero quien algun dia lo bloquee tiene que acordarse de este renglon.
    rcc.ccipr7().modify(|w| {
        w.set_persel(Persel::Hsi); // PERSEL = 0x0 (ES0620 p. 12)
        w.set_rtcsel(Rtcsel::Lsi); // RTCSEL = 0x2 (ES0620 p. 12)
    });

    // RCC_CCIPR8 (RM0486 Rev 4, p. 538, reset 0x0000_0000).
    rcc.ccipr8().modify(|w| {
        w.set_sdmmc1sel(Sdmmcsel::Hclku); // SDMMC1SEL = 0x0 (ES0620 p. 12)
        w.set_sdmmc2sel(Sdmmcsel::Hclku); // SDMMC2SEL = 0x0 (ES0620 p. 12)
    });

    // RCC_CCIPR13 (RM0486 Rev 4, p. 542, reset 0x0000_0000). USART1 mira a
    // pclk2 y los otros tres a pclk1, y por eso el enum no es el mismo
    // (`Uart16910sel` contra `Uart234578sel`); el valor numerico si lo es.
    rcc.ccipr13().modify(|w| {
        w.set_usart1sel(Uart16910sel::Pclk2); // USART1SEL = 0x0 (ES0620 p. 12)
        w.set_usart2sel(Uart234578sel::Pclk1); // USART2SEL = 0x0 (ES0620 p. 12)
        w.set_uart4sel(Uart234578sel::Pclk1); // UART4SEL  = 0x0 (ES0620 p. 12)
        w.set_uart5sel(Uart234578sel::Pclk1); // UART5SEL  = 0x0 (ES0620 p. 12)
    });

    // Que las cuatro escrituras hayan llegado al RCC antes de pedir el reset.
    cortex_m::asm::dsb();
    cortex_m::peripheral::SCB::sys_reset()
}
