//! Cuanta CPU le queda al hilo mientras el J2 gira.
//!
//! El J2 corre en interrupciones (SPI, DMA, EXTI) y en un ejecutor a `P2`; el
//! hilo -- USB, MIDI, pantalla y quien alimente el IWDG -- solo corre cuando
//! ellos no tienen nada que hacer. Medirlo con el depurador no vale: muestrear
//! `ICSR` despierta un nucleo dormido justo en la interrupcion y casi siempre lo
//! ve en excepcion. Aqui el hilo se mide a si mismo: una tarea da vueltas al
//! ejecutor de hilo sin dormirlo (`yield_now`) y cuenta cuantas. Con la CPU
//! libre da muchas; con el J2 girando da las que le dejan. La razon entre las
//! dos es la fraccion libre.
//!
//! **Lo que mide y lo que no.** Mide todo lo que no es hilo: el J2, el esclavo
//! del banco si va en el mismo nucleo, el reloj de `embassy_time` y cualquier
//! otra interrupcion. No separa a quien se la come; eso es el desglose por
//! tramos del giro. Para el hilo es lo unico que importa: cuanto le queda.
//!
//! **Solo para los binarios del banco.** La tarea mantiene despierto al
//! ejecutor de hilo, asi que el instrumento no la lanza.

use core::sync::atomic::{AtomicU32, Ordering};

use embassy_futures::yield_now;
use embassy_time::{Instant, Timer};

static VUELTAS: AtomicU32 = AtomicU32::new(0);

/// La tarea que da vueltas. Se lanza una vez, en el ejecutor de hilo, antes de
/// [`Medidor::calibrar`].
#[embassy_executor::task]
pub async fn vueltas_del_hilo() -> ! {
    loop {
        yield_now().await;
        VUELTAS.fetch_add(1, Ordering::Relaxed);
    }
}

/// Cuantas vueltas por segundo da el hilo con la CPU libre, y desde cuando se
/// mira.
pub struct Medidor {
    base_por_s: u64,
    vueltas_antes: u32,
    instante_antes: Instant,
}

impl Medidor {
    /// Calibra durante `ms` milisegundos. Hay que llamarla con el J2 **sin
    /// arrancar**: la base es la CPU entera.
    pub async fn calibrar(ms: u32) -> Medidor {
        let v0 = VUELTAS.load(Ordering::Relaxed);
        let t0 = Instant::now();
        Timer::after_millis(ms as u64).await;
        let dv = VUELTAS.load(Ordering::Relaxed).wrapping_sub(v0) as u64;
        let dt_us = t0.elapsed().as_micros().max(1);
        Medidor {
            base_por_s: dv * 1_000_000 / dt_us,
            vueltas_antes: VUELTAS.load(Ordering::Relaxed),
            instante_antes: Instant::now(),
        }
    }

    /// Las vueltas por segundo de la calibracion, para publicarlas: una base
    /// distinta entre dos corridas dice que no se midio lo mismo.
    pub fn base_por_s(&self) -> u32 {
        self.base_por_s as u32
    }

    /// La CPU libre para el hilo desde la llamada anterior, en milesimas.
    /// `1000` es toda la CPU; `0`, nada.
    pub fn libre_por_mil(&mut self) -> u32 {
        let v = VUELTAS.load(Ordering::Relaxed);
        let t = Instant::now();
        let dv = v.wrapping_sub(self.vueltas_antes) as u64;
        let dt_us = (t - self.instante_antes).as_micros();
        self.vueltas_antes = v;
        self.instante_antes = t;
        let esperadas = self.base_por_s * dt_us / 1_000_000;
        if esperadas == 0 {
            return 0;
        }
        (dv * 1000 / esperadas).min(1000) as u32
    }
}
