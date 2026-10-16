//! Perfilador por muestreo del PC, dentro del firmware.
//!
//! Una interrupcion periodica de la maxima prioridad (`TIM6` a `P0`, por encima
//! de las ISR del J2 a `P1` y del ejecutor a `P2`) anota **donde estaba la CPU**:
//! lee el PC apilado en la excepcion y suma uno al cubo de 2 bytes que lo
//! contiene. Al terminar, el histograma se lee por el depurador y
//! `perfil_pc.py` lo cruza con los simbolos del ELF.
//!
//! Existe porque no habia otra forma: `probe-rs profile` 0.32 no arranca (pide
//! un argumento `reset` que no deja pasar) y `DWT_PCSR` lee `0xFFFFFFFF` en el
//! M55 de esta placa. Lo que da, y lo que no:
//!
//! - **Da el reparto completo**, no el de los tramos que alguien acoto: el
//!   despacho del ejecutor, los futuros, las ISR del DMA y del reloj de embassy,
//!   la division de 64 bits, la CPU ociosa del hilo (`Executor::run`) y las
//!   vueltas del medidor (`carga`).
//! - **Un sesgo conocido:** una seccion critica (`PRIMASK = 1`) retrasa la
//!   muestra hasta el `cpsie` que la cierra, y esa se anota en la instruccion de
//!   despues, en la misma funcion que la tomo. A nivel de funcion no cambia nada.
//! - **Perturba**: la ISR cuesta unos 150 ciclos y a 21 kHz son un 5 % de la CPU
//!   a 64 MHz. Los ciclos por giro que da `carga_j2` se miden SIN esto; el
//!   perfilador dice como se reparten, no cuantos son.
//!
//! La ISR no se escribe en Rust: necesita el `MSP` tal como lo dejo la entrada
//! de la excepcion, antes de cualquier `push` del compilador, y por eso es un
//! trampolin en ensamblador que salta a [`muestrear`].
//!
//! Solo para el banco, detras de la feature `muestreo`.

use core::sync::atomic::{AtomicU16, AtomicU32, Ordering};

use embassy_stm32::interrupt::{self, InterruptExt, Priority};
use embassy_stm32::{pac, peripherals, rcc, Peri};

/// Donde empieza el codigo: el `FLASH` de `memory.x`, que es AXISRAM2.
pub const BASE: u32 = 0x341A_0000;
/// Bytes de codigo por cubo: media palabra, que es donde empieza cualquier
/// instruccion Thumb. Con cubos de 4 bytes, una funcion que empieza en una
/// direccion `2 mod 4` tendria su primera instruccion en un cubo que arranca
/// dentro de la funcion anterior, y esas muestras se le atribuirian al vecino.
pub const CUBO: u32 = 2;
/// Cubos: 32 KB de codigo, que son 16 384 cubos de 2 B de RAM, de
/// sobra para un binario de unos 30 KB.
pub const CUBOS: usize = 16384;

/// El histograma, alineado a 4 bytes para que el depurador lo lea de a palabras.
#[repr(align(4))]
pub struct Histograma(pub [AtomicU16; CUBOS]);

/// Lo lee el depurador por su direccion (`perfil_pc.py`).
pub static HISTOGRAMA: Histograma = Histograma([const { AtomicU16::new(0) }; CUBOS]);
/// Muestras tomadas, y las que cayeron fuera de la region de codigo.
pub static MUESTRAS: AtomicU32 = AtomicU32::new(0);
pub static FUERA: AtomicU32 = AtomicU32::new(0);

unsafe extern "C" {
    /// El final del codigo, de `link.x` de `cortex-m-rt`.
    static __etext: u32;
}

core::arch::global_asm!(
    ".section .text.TIM6,\"ax\",%progbits",
    ".global TIM6",
    ".type TIM6,%function",
    ".thumb_func",
    "TIM6:",
    "    mrs r0, msp",
    "    b {muestrear}",
    muestrear = sym muestrear,
);

/// Lo que hace la ISR. `marco` es el marco de la excepcion: `r0-r3`, `r12`,
/// `lr`, `pc`, `xpsr`. Con la FPU activa el marco se extiende **despues** de
/// esos ocho, asi que el PC apilado esta siempre en la posicion 6.
extern "C" fn muestrear(marco: *const u32) {
    // SAFETY: `marco` es el `MSP` en la entrada de la excepcion y apunta al marco
    // que acaba de apilar el hardware.
    let pc = unsafe { core::ptr::read_volatile(marco.add(6)) };
    // Se baja `UIF` antes de nada: el contador sigue corriendo.
    pac::TIM6.sr().write(|w| w.set_uif(false));
    MUESTRAS.store(
        MUESTRAS.load(Ordering::Relaxed).wrapping_add(1),
        Ordering::Relaxed,
    );
    let desde_base = (pc & !1).wrapping_sub(BASE);
    let cubo = (desde_base / CUBO) as usize;
    if cubo < CUBOS {
        let c = &HISTOGRAMA.0[cubo];
        c.store(
            c.load(Ordering::Relaxed).saturating_add(1),
            Ordering::Relaxed,
        );
    } else {
        FUERA.store(
            FUERA.load(Ordering::Relaxed).wrapping_add(1),
            Ordering::Relaxed,
        );
    }
}

/// Arranca el muestreo a `hz` muestras por segundo. Devuelve el periodo real, en
/// ciclos del reloj del timer.
///
/// `hz` no debe dividir al periodo del giro: con `21 000` y giros de 125 o
/// 1 000 us las muestras no caen siempre en el mismo punto del ciclo.
pub fn iniciar(_tim6: Peri<'static, peripherals::TIM6>, hz: u32) -> u32 {
    // El histograma tiene que cubrir el codigo entero, o el final saldria como
    // `FUERA` sin que nadie lo notara.
    let fin = core::ptr::addr_of!(__etext) as u32;
    defmt::assert!(
        fin <= BASE + CUBOS as u32 * CUBO,
        "muestreo: el codigo pasa de los {} KB del histograma",
        CUBOS as u32 * CUBO / 1024
    );

    rcc::enable_and_reset::<peripherals::TIM6>();
    let f_timer = rcc::frequency::<peripherals::TIM6>().0;
    let ciclos = f_timer / hz;
    defmt::assert!(
        (2..=0x1_0000).contains(&ciclos),
        "muestreo: {} ciclos de timer no caben en `ARR` de 16 bits",
        ciclos
    );
    let tim = pac::TIM6;
    tim.psc().write_value(0);
    tim.arr().write(|w| w.set_arr((ciclos - 1) as u16));
    // `UG` carga `ARR` y levanta `UIF`: se baja antes de habilitar la interrupcion.
    tim.egr().write(|w| w.set_ug(true));
    tim.sr().write(|w| w.set_uif(false));
    tim.dier().modify(|w| w.set_uie(true));
    interrupt::TIM6.set_priority(Priority::P0);
    // SAFETY: el vector `TIM6` es el trampolin de arriba.
    unsafe { interrupt::TIM6.enable() };
    tim.cr1().modify(|w| w.set_cen(true));
    ciclos
}

/// Para el muestreo. Lo que quede en el histograma es lo que se lee.
pub fn parar() {
    pac::TIM6.cr1().modify(|w| w.set_cen(false));
    pac::TIM6.dier().modify(|w| w.set_uie(false));
}
