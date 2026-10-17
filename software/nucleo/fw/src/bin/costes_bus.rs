#![no_std]
#![no_main]

//! **Cuanto cuesta, en ciclos de CPU, un acceso a un registro de periferico.**
//!
//! A 64 MHz el bus y el nucleo van casi a la par; a 800 MHz el nucleo lleva el
//! bus de periferico a una octava parte o menos, y cada lectura **espera** al
//! periferico. Un giro del J2 hace cerca de un centenar de accesos (`SPI`,
//! `GPDMA`, el reloj de embassy), asi que a 800 MHz lo que decide si caben en el
//! limite de 2 500 ciclos (spec del maestro, D5.1) puede no ser el codigo sino
//! el numero de accesos. Este banco mide el precio de uno.
//!
//! Por cada destino, tres pasadas -- sin cache, con la I-cache, con I y D-cache --
//! y dos lineas (lectura y escritura), en centesimas de ciclo por acceso:
//!
//! ```text
//! costes_bus,f_cpu=,cache=,destino=,lee_x100=,escribe_x100=
//! ```
//!
//! Los destinos son registros que no hacen nada con lo que se les escribe: el
//! `CRCPOLY` del SPI5 apagado, el `BR1` del canal 15 del GPDMA1 (parado y sin
//! uso), el contador del reloj de embassy y una variable en la SRAM como
//! referencia. Cada acceso es un `read_volatile` o `write_volatile` en un bucle
//! desenrollado de a ocho, asi que el bucle suma menos de medio ciclo por acceso.
//!
//! ```bash
//! cargo run --release --features perfil --bin costes_bus
//! cargo run --release --features perfil,reloj-hub --bin costes_bus   # a 800 MHz
//! ```

use core::ptr::{read_volatile, write_volatile};
use core::sync::atomic::AtomicU32;

use defmt::info;
use embassy_stm32::{pac, peripherals, rcc};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Accesos por medida, multiplo de 8.
const N: u32 = 8192;

/// Una variable en la SRAM, de referencia.
static SRAM: AtomicU32 = AtomicU32::new(0);

/// Centesimas de ciclo por lectura de `dir`.
#[inline(never)]
fn lee(dir: *const u32) -> u32 {
    let antes = cortex_m::peripheral::DWT::cycle_count();
    for _ in 0..N / 8 {
        // SAFETY: `dir` es un registro de lectura sin efectos o la SRAM.
        unsafe {
            read_volatile(dir);
            read_volatile(dir);
            read_volatile(dir);
            read_volatile(dir);
            read_volatile(dir);
            read_volatile(dir);
            read_volatile(dir);
            read_volatile(dir);
        }
    }
    let ciclos = cortex_m::peripheral::DWT::cycle_count().wrapping_sub(antes);
    (ciclos as u64 * 100 / N as u64) as u32
}

/// Centesimas de ciclo por escritura de `valor` en `dir`.
#[inline(never)]
fn escribe(dir: *mut u32, valor: u32) -> u32 {
    let antes = cortex_m::peripheral::DWT::cycle_count();
    for _ in 0..N / 8 {
        // SAFETY: `dir` es un registro cuyo valor da igual o la SRAM.
        unsafe {
            write_volatile(dir, valor);
            write_volatile(dir, valor);
            write_volatile(dir, valor);
            write_volatile(dir, valor);
            write_volatile(dir, valor);
            write_volatile(dir, valor);
            write_volatile(dir, valor);
            write_volatile(dir, valor);
        }
    }
    let ciclos = cortex_m::peripheral::DWT::cycle_count().wrapping_sub(antes);
    (ciclos as u64 * 100 / N as u64) as u32
}

#[cortex_m_rt::entry]
fn main() -> ! {
    #[cfg(feature = "reloj-hub")]
    let config = usb::configuracion_hub();
    #[cfg(not(feature = "reloj-hub"))]
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let _p = usb::iniciar(config);

    // SAFETY: nadie mas toca el DWT ni el SCB en este binario.
    let mut cp = unsafe { cortex_m::Peripherals::steal() };
    cp.DCB.enable_trace();
    cp.DWT.enable_cycle_counter();
    // El SPI5 con su reloj puesto, para que sus registros contesten.
    rcc::enable_and_reset::<peripherals::SPI5>();

    // El valor que se escribe es el que ya hay: no cambia nada.
    let crcpoly = pac::SPI5.crcpoly().as_ptr() as *mut u32;
    // SAFETY: `CRCPOLY` es un registro de datos con el SPI apagado.
    let crcpoly_valor = unsafe { read_volatile(crcpoly) };
    let spi5_sr = pac::SPI5.sr().as_ptr() as *const u32;
    // El canal 15 del GPDMA1 no se usa: parado, con su `BR1` libre.
    let c15_sr = pac::GPDMA1.ch(15).sr().as_ptr() as *const u32;
    let c15_br1 = pac::GPDMA1.ch(15).br1().as_ptr() as *mut u32;
    // SAFETY: el canal esta parado y sin configurar.
    let c15_br1_valor = unsafe { read_volatile(c15_br1) };
    let tim12_cnt = pac::TIM12.cnt().as_ptr() as *const u32;
    let sram = SRAM.as_ptr();

    for cache in ["no", "icache", "icache+dcache"] {
        // SAFETY: `cp` es nuestro y no hay nada en vuelo.
        match cache {
            "icache" => cp.SCB.enable_icache(),
            "icache+dcache" => cp.SCB.enable_dcache(&mut cp.CPUID),
            _ => {}
        }
        // Una vuelta de calentamiento: las dos primeras lecturas traen el codigo.
        let _ = lee(sram);
        let _ = escribe(sram, 0);
        let destinos: [(&str, u32, u32); 5] = [
            ("sram", lee(sram), escribe(sram, 0)),
            ("spi5_sr", lee(spi5_sr), 0),
            (
                "spi5_crcpoly",
                lee(crcpoly),
                escribe(crcpoly, crcpoly_valor),
            ),
            ("gpdma1_c15", lee(c15_sr), escribe(c15_br1, c15_br1_valor)),
            ("tim12_cnt", lee(tim12_cnt), 0),
        ];
        for (nombre, l, e) in destinos {
            info!(
                "costes_bus,f_cpu={},cache={=str},destino={=str},lee_x100={},escribe_x100={}",
                f_cpu, cache, nombre, l, e
            );
        }
    }
    info!("costes_bus: fin");
    cortex_m::asm::bkpt();
    loop {
        cortex_m::asm::wfi();
    }
}
