//! La region MPU de los buferes del DMA del J2 (R-MJ7, #380).
//!
//! R-MJ7 deja dos formas: los buferes en memoria no cacheable, o invalidarlos antes
//! de leerlos. Esta es la primera: una region de la MPU del Cortex-M55 con el atributo
//! *Normal, no cacheable*, para que la D-cache no guarde copia de lo que el DMA
//! escribe ni de lo que va a leer.
//!
//! **Precio:** una lectura de la region cuesta lo que una de SRAM sin D-cache -- 80
//! ciclos a 800 MHz, `costes_bus` --, y a byte cuesta lo mismo que a palabra. Leer una
//! trama con un `ldm` de ocho palabras es una sola transaccion. `costes_dma` mide las
//! dos formas de R-MJ7 para una trama de 32 y de 128 bytes.

use cortex_m::asm::{dsb, isb};
use cortex_m::peripheral::MPU;

/// Una linea de la D-cache del Cortex-M55: 32 bytes. La region y los buferes se
/// alinean a ella, y la longitud de la region es un multiplo suyo.
pub const LINEA: u32 = 32;

/// `MAIR0`, indice 0: Normal, Outer y Inner no cacheable.
const MAIR_NORMAL_NC: u32 = 0x44;

/// Pone la region 0 de la MPU sobre `[base, base + len)` como *Normal, no cacheable*
/// y sin ejecucion, y enciende la MPU con el mapa por defecto de fondo
/// (`PRIVDEFENA`): todo lo demas queda como estaba.
///
/// Hay que llamarla **antes** de encender la D-cache, o con la D-cache limpiada e
/// invalidada: una linea que ya estuviera en la cache seguiria alli.
pub fn region_no_cacheable(mpu: &mut MPU, base: u32, len: u32) {
    defmt::assert!(
        len > 0 && base % LINEA == 0 && len % LINEA == 0,
        "mpu: base {:#x} y longitud {} tienen que ser multiplos de {} bytes",
        base,
        len,
        LINEA
    );
    // `RLAR.LIMIT` es la direccion de la ultima linea incluida.
    let limite = (base + len - 1) & !(LINEA - 1);
    // SAFETY: nadie mas configura la MPU. La region es la RAM de este firmware y
    // solo cambia su atributo.
    unsafe {
        dsb();
        isb();
        mpu.ctrl.write(0);
        mpu.mair[0].write(MAIR_NORMAL_NC);
        mpu.rnr.write(0);
        // RBAR: BASE | SH = 0b10 (outer shareable) | AP = 0b00 (RW, privilegiado) | XN.
        mpu.rbar.write(base | (0b10 << 3) | 1);
        // RLAR: LIMIT | AttrIndx = 0 | EN.
        mpu.rlar.write(limite | 1);
        // ENABLE | PRIVDEFENA.
        mpu.ctrl.write(0b101);
        dsb();
        isb();
    }
}
