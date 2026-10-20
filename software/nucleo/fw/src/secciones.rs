//! R-H2 en el banco: cuanto dura cada seccion critica y quien la abre.
//!
//! Es la seccion critica de `cortex-m` (`critical-section-single-core`: guardar PRIMASK y
//! enmascarar) con dos cosas mas: al abrir la mas externa apunta el ciclo y la direccion de
//! vuelta de quien llamo, y al cerrarla anota la duracion en una [`Tabla`] por sitio, todavia
//! enmascarada. Eso alarga cada seccion lo que tarda en buscar su fila, unos cientos de ciclos
//! como mucho, y no entra en la cifra.
//!
//! Solo ve lo que pasa por el crate `critical-section` (embassy, `defmt-rtt` y lo nuestro que lo
//! use). `cortex_m::interrupt::free` enmascara por su cuenta y no sale aqui.
//!
//! Las dos funciones son las que `critical_section::set_impl!` generaria, escritas a mano para
//! poder ponerles `#[inline(never)]`: con LTO se inlinarian en quien llama, y la direccion de
//! vuelta dejaria de ser la suya.

use core::arch::asm;
use core::ptr::addr_of_mut;

use cortex_m::peripheral::DWT;
use cortex_m::register::primask;
use defmt::info;
use sam17_nucleo_core::secciones::Tabla;

#[cfg(feature = "seccion-cortex-m")]
compile_error!(
    "`secciones` cambia la seccion critica de `cortex-m`: compilar con --no-default-features"
);

static mut TABLA: Tabla = Tabla::nueva();
static mut TOPE: u32 = u32::MAX;
static mut ABIERTA_EN: u32 = 0;
static mut ABIERTA_POR: u32 = 0;

#[no_mangle]
#[inline(never)]
unsafe fn _critical_section_1_0_acquire() -> critical_section::RawRestoreState {
    let quien: u32;
    // SAFETY: solo lee LR, que aqui es la vuelta a quien llamo: no ha habido ninguna llamada.
    unsafe { asm!("mov {}, lr", out(reg) quien, options(nomem, nostack, preserves_flags)) };
    let antes = primask::read_raw();
    cortex_m::interrupt::disable();
    // PRIMASK estaba a cero: esta es la mas externa.
    if antes & 1 == 0 {
        // SAFETY: enmascarado, y solo la mas externa escribe.
        unsafe {
            ABIERTA_EN = DWT::cycle_count();
            ABIERTA_POR = quien;
        }
    }
    antes
}

#[no_mangle]
#[inline(never)]
unsafe fn _critical_section_1_0_release(antes: critical_section::RawRestoreState) {
    if antes & 1 == 0 {
        // SAFETY: seguimos enmascarados; la tabla solo se toca aqui y en `reinicia`/`toma`,
        // que la toman dentro de una seccion.
        unsafe {
            let ciclos = DWT::cycle_count().wrapping_sub(ABIERTA_EN);
            (*addr_of_mut!(TABLA)).anota(ABIERTA_POR, ciclos, TOPE);
        }
    }
    // SAFETY: PRIMASK vuelve a como estaba, como en la de `cortex-m`.
    unsafe { primask::write_raw(antes) };
}

/// Vacia la tabla. `tope` en ciclos: lo que cuenta como `largas` (R-H2, 5 us).
pub fn reinicia(tope: u32) {
    critical_section::with(|_| unsafe {
        *addr_of_mut!(TABLA) = Tabla::nueva();
        TOPE = tope;
    });
    // La de `with` de arriba ya entra en la tabla nueva; da igual, es una.
}

/// Una copia de la tabla tal como esta.
pub fn toma() -> Tabla {
    critical_section::with(|_| unsafe { *addr_of_mut!(TABLA) })
}

/// Imprime una copia: una linea por sitio, con la direccion para `rust-objdump -l`.
pub fn imprime(t: &Tabla, etiqueta: &str, ciclos_por_us: u32) {
    let d = ciclos_por_us.max(1);
    for f in &t.filas[..t.usadas] {
        info!(
            "secciones,cache={=str}: quien={:#010x} veces={} max={} ciclos ({} us) largas={}",
            etiqueta,
            f.quien,
            f.veces,
            f.max,
            f.max / d,
            f.largas
        );
    }
    info!(
        "secciones,cache={=str}: {} sitios, {} sin sitio",
        etiqueta, t.usadas, t.sin_sitio
    );
}
