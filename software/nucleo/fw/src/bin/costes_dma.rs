#![no_std]
#![no_main]

//! **Cuanto cuesta leer y escribir un bufer de DMA segun la forma de R-MJ7.**
//!
//! R-MJ7 deja dos formas de que la CPU y el DMA vean lo mismo: los buferes en una
//! region de la MPU *no cacheable*, o cacheables y con mantenimiento de la D-cache por
//! direccion (`clean` antes de que el DMA lea, `invalidate` antes de que la CPU lea
//! lo que el DMA escribio). Este banco mide el precio de cada una para lo que hace
//! un giro del J2: escribir una bajada y leer una subida de 32 o de 128 bytes.
//!
//! Dos pasadas, con la I-cache siempre encendida: **sin D-cache** (todo es sin cache) y
//! **con D-cache**. La region MPU esta puesta en las dos. Una linea por operacion, en
//! centesimas de ciclo **por operacion entera** (no por acceso):
//!
//! ```text
//! costes_dma,f_cpu=,cache=,operacion=,ciclos_x100=
//! ```
//!
//! - `nc_*`: el bufer de la region no cacheable. `ldm8` y `ldm32` son lecturas en
//!   rafaga (un `ldm` de ocho palabras por linea); `words`, `bytes` y `escribe`, un
//!   acceso por palabra o por byte.
//! - `cache_*`: el bufer cacheable. `caliente` es la lectura sin mantenimiento (la
//!   cota inferior); `invalN` es `invalidate` de N lineas y despues leer; `cleanN`,
//!   escribir y despues `clean` de N lineas.
//!
//! ```bash
//! cargo run --release --features perfil --bin costes_dma
//! cargo run --release --features perfil,reloj-hub --bin costes_dma   # a 800 MHz
//! ```

use core::arch::asm;
use core::cell::UnsafeCell;
use core::hint::black_box;
use core::ptr::{read_volatile, write_volatile};

use cortex_m::peripheral::DWT;
use defmt::info;
use sam17_nucleo_fw::{mpu, usb};
use {defmt_rtt as _, panic_probe as _};

/// 128 bytes -- cuatro lineas de D-cache -- alineados a una linea.
#[repr(C, align(32))]
struct Bufer(UnsafeCell<[u32; 32]>);
// SAFETY: solo `main` los toca, y no hay otro hilo ni ISR que los use.
unsafe impl Sync for Bufer {}

/// El de la region no cacheable.
static NC: Bufer = Bufer(UnsafeCell::new([0; 32]));
/// El cacheable, para el mantenimiento por direccion.
static CACHEABLE: Bufer = Bufer(UnsafeCell::new([0; 32]));

/// Veces que se repite cada operacion.
const VECES: u32 = 256;

/// Centesimas de ciclo por llamada a `f`, tras una de calentamiento.
#[inline(never)]
fn mide<F: FnMut()>(mut f: F) -> u32 {
    f();
    let antes = DWT::cycle_count();
    for _ in 0..VECES {
        f();
    }
    let ciclos = DWT::cycle_count().wrapping_sub(antes);
    (ciclos as u64 * 100 / VECES as u64) as u32
}

/// Obliga a que el valor leido se use, para que la lectura no se optimice fuera.
#[inline(always)]
fn usa(x: u32) {
    let _ = black_box(x);
}

/// Lee `n` palabras sueltas.
#[inline(always)]
fn lee_palabras(p: *const u32, n: usize) -> u32 {
    let mut s = 0u32;
    for i in 0..n {
        // SAFETY: `p` apunta a un bufer de 32 palabras y `n <= 32`.
        s = s.wrapping_add(unsafe { read_volatile(p.add(i)) });
    }
    s
}

/// Lee `n` bytes sueltos.
#[inline(always)]
fn lee_bytes(p: *const u8, n: usize) -> u32 {
    let mut s = 0u32;
    for i in 0..n {
        // SAFETY: `p` apunta a un bufer de 128 bytes y `n <= 128`.
        s = s.wrapping_add(u32::from(unsafe { read_volatile(p.add(i)) }));
    }
    s
}

/// Escribe `n` palabras sueltas.
#[inline(always)]
fn escribe_palabras(p: *mut u32, n: usize) {
    for i in 0..n {
        // SAFETY: `p` apunta a un bufer de 32 palabras y `n <= 32`.
        unsafe { write_volatile(p.add(i), i as u32) };
    }
}

/// Una rafaga de cuatro `ldm` de ocho palabras: 128 bytes.
#[inline(always)]
fn ldm_128(p: *const u32) {
    // SAFETY: lee 32 palabras desde `p`, que es un bufer de 128 bytes.
    unsafe {
        asm!(
            "ldm {p}!, {{r0-r5, r8, r10}}",
            "ldm {p}!, {{r0-r5, r8, r10}}",
            "ldm {p}!, {{r0-r5, r8, r10}}",
            "ldm {p}!, {{r0-r5, r8, r10}}",
            p = inout(reg) p => _,
            out("r0") _, out("r1") _, out("r2") _, out("r3") _,
            out("r4") _, out("r5") _, out("r8") _, out("r10") _,
            options(nostack, readonly),
        );
    }
}

/// Una rafaga de un `ldm` de ocho palabras: 32 bytes.
#[inline(always)]
fn ldm_32(p: *const u32) {
    // SAFETY: lee 8 palabras desde `p`.
    unsafe {
        asm!(
            "ldm {p}, {{r0-r5, r8, r10}}",
            p = in(reg) p,
            out("r0") _, out("r1") _, out("r2") _, out("r3") _,
            out("r4") _, out("r5") _, out("r8") _, out("r10") _,
            options(nostack, readonly),
        );
    }
}

#[cortex_m_rt::entry]
fn main() -> ! {
    #[cfg(feature = "reloj-hub")]
    let config = usb::configuracion_hub();
    #[cfg(not(feature = "reloj-hub"))]
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let _p = usb::iniciar(config);

    // SAFETY: nadie mas toca el DWT, el SCB ni la MPU en este binario.
    let mut cp = unsafe { cortex_m::Peripherals::steal() };
    cp.DCB.enable_trace();
    cp.DWT.enable_cycle_counter();
    cp.SCB.enable_icache();
    // La region antes de la D-cache: una linea que ya estuviera dentro seguiria alli.
    mpu::region_no_cacheable(&mut cp.MPU, NC.0.get() as u32, 128);

    let nc = NC.0.get() as *mut u32;
    let nc8 = NC.0.get() as *const u8;
    let ca = CACHEABLE.0.get() as *mut u32;
    let ca8 = CACHEABLE.0.get() as *const u8;
    let ca_dir = CACHEABLE.0.get() as usize;

    for cache in ["icache", "icache+dcache"] {
        if cache == "icache+dcache" {
            cp.SCB.enable_dcache(&mut cp.CPUID);
        }
        let ops: [(&str, u32); 17] = [
            ("nc_ldm8", mide(|| ldm_32(nc))),
            ("nc_ldm32", mide(|| ldm_128(nc))),
            ("nc_words8", mide(|| usa(lee_palabras(nc, 8)))),
            ("nc_words32", mide(|| usa(lee_palabras(nc, 32)))),
            ("nc_bytes32", mide(|| usa(lee_bytes(nc8, 32)))),
            ("nc_bytes128", mide(|| usa(lee_bytes(nc8, 128)))),
            ("nc_escribe8", mide(|| escribe_palabras(nc, 8))),
            ("nc_escribe32", mide(|| escribe_palabras(nc, 32))),
            ("cache_caliente_words32", mide(|| usa(lee_palabras(ca, 32)))),
            ("cache_caliente_bytes128", mide(|| usa(lee_bytes(ca8, 128)))),
            (
                "cache_inval1_words8",
                mide(|| {
                    // SAFETY: el bufer esta alineado a una linea y es solo suyo.
                    unsafe { cp.SCB.invalidate_dcache_by_address(ca_dir, 32) };
                    usa(lee_palabras(ca, 8));
                }),
            ),
            (
                "cache_inval4_words32",
                mide(|| {
                    // SAFETY: igual.
                    unsafe { cp.SCB.invalidate_dcache_by_address(ca_dir, 128) };
                    usa(lee_palabras(ca, 32));
                }),
            ),
            (
                "cache_inval4_bytes128",
                mide(|| {
                    // SAFETY: igual.
                    unsafe { cp.SCB.invalidate_dcache_by_address(ca_dir, 128) };
                    usa(lee_bytes(ca8, 128));
                }),
            ),
            (
                "cache_clean1_escribe8",
                mide(|| {
                    escribe_palabras(ca, 8);
                    cp.SCB.clean_dcache_by_address(ca_dir, 32);
                }),
            ),
            (
                "cache_clean4_escribe32",
                mide(|| {
                    escribe_palabras(ca, 32);
                    cp.SCB.clean_dcache_by_address(ca_dir, 128);
                }),
            ),
            (
                "cache_clean1_solo",
                mide(|| cp.SCB.clean_dcache_by_address(ca_dir, 32)),
            ),
            (
                "cache_inval1_solo",
                mide(|| {
                    // SAFETY: igual.
                    unsafe { cp.SCB.invalidate_dcache_by_address(ca_dir, 32) };
                }),
            ),
        ];
        for (nombre, c) in ops {
            info!(
                "costes_dma,f_cpu={},cache={=str},operacion={=str},ciclos_x100={}",
                f_cpu, cache, nombre, c
            );
        }
    }
    info!("costes_dma: fin");
    cortex_m::asm::bkpt();
    loop {
        cortex_m::asm::wfi();
    }
}
