//! El desglose de un giro del J2 por tramos, en ciclos de CPU.
//!
//! Detras de la feature `perfil`: sin ella `marca` devuelve ceros y `cierra` no
//! hace nada, asi que el instrumento no paga ni un ciclo. Los binarios del
//! banco la encienden (`--features perfil`) y publican el promedio por giro.
//!
//! Cada tramo se mide con `DWT_CYCCNT` (32 bits, ciclos del nucleo) y **se le
//! resta lo que gastaron dentro nuestras ISR** (`IsrSpi`, `IsrCs`) mientras
//! corria: una ISR a `P1` interrumpe al ejecutor a `P2` y, sin la resta, el
//! tramo interrumpido cargaria con tiempo que no es suyo. Las ISR del GPDMA son
//! de embassy y no se miden; caen en el tramo que interrumpen.
//!
//! La suma de cada tramo da la vuelta a los 2^32 ciclos, 67 s a 64 MHz: quien
//! publica tiene que leerla al menos una vez por minuto y restar con
//! `wrapping_sub`.

use core::sync::atomic::{AtomicU32, Ordering};

/// Los tramos de un giro.
#[derive(Clone, Copy)]
#[repr(usize)]
pub enum Fase {
    /// Desde que despierta la tarea hasta llamar a `giro`: lo que baja, el
    /// sello, el plazo y el evento `Armada`.
    Previo,
    /// Dentro de `giro`, hasta antes de esperar: `TXTFC`, `TSIZE`, los dos
    /// canales de DMA, `SPE`, el retardo, `EOTIE` y `CSTART`.
    Armado,
    /// La espera de los dos DMA y del `EOT`. Es tiempo de reloj: incluye lo que
    /// corra mientras tanto (otras tareas, ISR de DMA) y la CPU ociosa.
    Espera,
    /// Dentro de `giro`, tras la espera: soltar los canales, `SPE = 0`, `CFG1`.
    Cierre,
    /// Lo que la tarea hace con el giro: el juez, los eventos de la politica,
    /// el calendario y las cuentas.
    Posterior,
    /// La ISR del SPI del maestro.
    IsrSpi,
    /// La ISR del flanco de `CS` del esclavo del banco.
    IsrCs,
    /// Todo el manejador del ejecutor del J2 (`GFXTIM`): el despacho de las
    /// tareas mas lo que ellas hacen, sin las ISR nuestras que lo interrumpen.
    Ejecutor,
}

pub const FASES: usize = 8;

static SUMAS: [AtomicU32; FASES] = [const { AtomicU32::new(0) }; FASES];

/// Ciclos acumulados dentro de nuestras ISR, para restarlos de los tramos.
#[cfg(feature = "perfil")]
static EN_ISR: AtomicU32 = AtomicU32::new(0);

/// El principio de un tramo.
#[derive(Clone, Copy)]
#[cfg_attr(not(feature = "perfil"), allow(dead_code))]
pub struct Marca {
    ciclos: u32,
    en_isr: u32,
}

/// Enciende el contador de ciclos. Una vez, al arrancar el binario.
#[cfg(feature = "perfil")]
pub fn iniciar() {
    // SAFETY: nadie mas toca el DWT ni el DEMCR en `fw`.
    unsafe {
        let mut p = cortex_m::Peripherals::steal();
        p.DCB.enable_trace();
        p.DWT.enable_cycle_counter();
    }
}

#[cfg(not(feature = "perfil"))]
pub fn iniciar() {}

#[cfg(feature = "perfil")]
#[inline(always)]
pub fn marca() -> Marca {
    Marca {
        ciclos: cortex_m::peripheral::DWT::cycle_count(),
        en_isr: EN_ISR.load(Ordering::Relaxed),
    }
}

#[cfg(not(feature = "perfil"))]
#[inline(always)]
pub fn marca() -> Marca {
    Marca {
        ciclos: 0,
        en_isr: 0,
    }
}

/// Cierra un tramo de tarea: suma sus ciclos menos los de las ISR que lo
/// interrumpieron.
#[inline(always)]
pub fn cierra(fase: Fase, desde: Marca) {
    #[cfg(feature = "perfil")]
    {
        let bruto = cortex_m::peripheral::DWT::cycle_count().wrapping_sub(desde.ciclos);
        let isr = EN_ISR.load(Ordering::Relaxed).wrapping_sub(desde.en_isr);
        SUMAS[fase as usize].fetch_add(bruto.wrapping_sub(isr), Ordering::Relaxed);
    }
    #[cfg(not(feature = "perfil"))]
    let _ = (fase, desde);
}

/// Cierra una ISR nuestra: suma sus ciclos a su tramo y al total de ISR.
#[inline(always)]
pub fn cierra_isr(fase: Fase, desde: Marca) {
    #[cfg(feature = "perfil")]
    {
        let ciclos = cortex_m::peripheral::DWT::cycle_count().wrapping_sub(desde.ciclos);
        SUMAS[fase as usize].fetch_add(ciclos, Ordering::Relaxed);
        EN_ISR.fetch_add(ciclos, Ordering::Relaxed);
    }
    #[cfg(not(feature = "perfil"))]
    let _ = (fase, desde);
}

/// Las sumas de todos los tramos, desde el arranque, con la vuelta de 32 bits.
pub fn leer() -> [u32; FASES] {
    let mut v = [0u32; FASES];
    for (d, s) in v.iter_mut().zip(SUMAS.iter()) {
        *d = s.load(Ordering::Relaxed);
    }
    v
}

/// El promedio por giro de cada tramo desde la llamada anterior.
pub struct Promedios {
    antes: [u32; FASES],
    giros_antes: u32,
}

impl Promedios {
    pub fn nuevo() -> Promedios {
        Promedios {
            antes: leer(),
            giros_antes: 0,
        }
    }

    /// Ciclos por giro de cada tramo, en el orden de [`Fase`], y los giros del
    /// intervalo. `giros` es el total acumulado de la ranura; con ninguno nuevo
    /// devuelve ceros.
    pub fn tomar(&mut self, giros: u32) -> ([u32; FASES], u32) {
        let ahora = leer();
        let dg = giros.wrapping_sub(self.giros_antes);
        let mut medias = [0u32; FASES];
        if dg > 0 {
            for ((m, a), d) in medias.iter_mut().zip(ahora.iter()).zip(self.antes.iter()) {
                *m = a.wrapping_sub(*d) / dg;
            }
        }
        self.antes = ahora;
        self.giros_antes = giros;
        (medias, dg)
    }
}
