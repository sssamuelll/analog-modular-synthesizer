//! El texto del J2 en ITCM y sus statics en DTCM (feature `j2-tcm`, solo banco).
//!
//! El guion `j2_tcm.x` (que `build.rs` pasa antes de `link.x`) lleva a la ITCM el texto del
//! tic, del planificador, de la recuperacion y de lo que llaman, y a la DTCM los statics
//! marcados con `.dtcm`. El depurador no escribe en las TCM, asi que la imagen viaja en la
//! AXISRAM2 (`IMG`) y `__pre_init` (ensamblador, al principio de este archivo) la pasa a su sitio. Las TCM las deja encendidas la ROM
//! (ITCM 64 KB, DTCM 128 KB, en su alias seguro): [`comprueba`] verifica que sigan encendidas.

use core::ptr::read_volatile;

extern "C" {
    static mut __sitcm: u32;
    static mut __eitcm: u32;
    static __siitcm: u32;
    static mut __sdtcm: u32;
    static mut __edtcm: u32;
    static __sidtcm: u32;
}

// `ITCMCR` y `DTCMCR` del nucleo (0xE001E010 y 0xE001E014): bit 0 `EN`, bits 6:3 el tamano.
const ITCMCR: *const u32 = 0xE001_E010 as *const u32;
const DTCMCR: *const u32 = 0xE001_E014 as *const u32;

/// Cuanto ocupan, en bytes, el texto en ITCM y los statics en DTCM.
pub fn tamanos() -> (u32, u32) {
    (
        core::ptr::addr_of!(__eitcm) as u32 - core::ptr::addr_of!(__sitcm) as u32,
        core::ptr::addr_of!(__edtcm) as u32 - core::ptr::addr_of!(__sdtcm) as u32,
    )
}

/// Los dos tramos que se copian: de la imagen en la AXISRAM2 al principio y al fin en la TCM.
fn tramos() -> [(*const u32, *mut u32, *mut u32); 2] {
    [
        (
            core::ptr::addr_of!(__siitcm),
            core::ptr::addr_of_mut!(__sitcm),
            core::ptr::addr_of_mut!(__eitcm),
        ),
        (
            core::ptr::addr_of!(__sidtcm),
            core::ptr::addr_of_mut!(__sdtcm),
            core::ptr::addr_of_mut!(__edtcm),
        ),
    ]
}

// Copia la imagen de `.itcm` y de `.dtcm` a las TCM, antes de inicializar `.data` y `.bss`
// (`__pre_init` de `cortex-m-rt`): hay texto de las TCM que corre desde el arranque (las
// rutinas de memoria de `compiler_builtins`), y `defmt` aun no esta listo. Va en ensamblador
// y sin pila: con `j2-tcm-pila` la pila esta en la DTCM y el primer paso la escribe entera.
//
// Un store de un byte (los `AtomicBool`, la pila) en una palabra de la DTCM no escrita desde
// el reset da un BusFault preciso, y escribir antes la palabra entera lo quita. Se sospecha
// del ECC de la TCM (el store parcial leeria la palabra), sin verificar contra el RM. Por
// eso se escribe entera, por palabras, antes de copiar nada.
core::arch::global_asm!(
    ".section .text.__pre_init,\"ax\"",
    ".global __pre_init",
    ".type __pre_init,%function",
    ".thumb_func",
    "__pre_init:",
    "    ldr r0, =0x30000000",
    "    ldr r1, =0x30020000",
    "    movs r2, #0",
    "1:  str r2, [r0], #4",
    "    cmp r0, r1",
    "    blo 1b",
    "    ldr r0, =__sitcm",
    "    ldr r1, =__eitcm",
    "    ldr r2, =__siitcm",
    "2:  cmp r0, r1",
    "    bhs 3f",
    "    ldr r3, [r2], #4",
    "    str r3, [r0], #4",
    "    b 2b",
    "3:  ldr r0, =__sdtcm",
    "    ldr r1, =__edtcm",
    "    ldr r2, =__sidtcm",
    "4:  cmp r0, r1",
    "    bhs 5f",
    "    ldr r3, [r2], #4",
    "    str r3, [r0], #4",
    "    b 4b",
    "5:  dsb",
    "    isb",
    "    bx lr",
);

/// Comprueba que las TCM estan encendidas y que la copia coincide con la imagen, palabra a
/// palabra. Al arrancar el binario, antes de lanzar el J2.
/// Asevera que la funcion de `f` esta en la ITCM. El J2 llama por puntero al juez y al reset de
/// cada ranura, y `tcm_cierre.py` solo sigue los saltos con direccion: una de esas
/// que se quede en la AXISRAM2 volveria a captar texto frio en cada giro sin que nada fallara.
pub fn asevera_en_itcm(f: usize, que: &str) {
    let a = f & !1;
    let ini = core::ptr::addr_of!(__sitcm) as usize;
    let fin = core::ptr::addr_of!(__eitcm) as usize;
    defmt::assert!(
        ini <= a && a < fin,
        "j2_tcm: {} ({:#x}) fuera de la ITCM",
        que,
        a
    );
}

pub fn comprueba() {
    // SAFETY: solo se leen las TCM, las imagenes y los registros de configuracion del nucleo.
    unsafe {
        defmt::assert!(
            read_volatile(ITCMCR) & 1 == 1 && read_volatile(DTCMCR) & 1 == 1,
            "j2_tcm: una TCM apagada: ITCMCR {:#x}, DTCMCR {:#x}",
            read_volatile(ITCMCR),
            read_volatile(DTCMCR)
        );
        for (src, dst, fin) in tramos() {
            let palabras = (fin as usize - dst as usize) / 4;
            // Los statics de la DTCM ya pueden haber cambiado: solo se compara la ITCM, que es
            // de solo lectura.
            if dst as usize >= 0x1000_0000 && (dst as usize) < 0x2000_0000 {
                for i in 0..palabras {
                    defmt::assert!(
                        read_volatile(dst.add(i)) == read_volatile(src.add(i)),
                        "j2_tcm: la ITCM no coincide con su imagen en la palabra {}",
                        i
                    );
                }
            }
        }
    }
}
