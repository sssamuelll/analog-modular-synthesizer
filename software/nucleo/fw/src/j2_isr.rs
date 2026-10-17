//! **El transporte del J2 sin ejecutor: un reloj, un `EOT` y registros.**
//!
//! Una prueba de coste, no el transporte del instrumento. La spec (D5.1) pone
//! una tarea por ranura en un `InterruptExecutor`; medido, ese camino gasta unos
//! 21 600 ciclos por giro a 64 MHz y el limite firmado son 2 500 a 800 MHz
//! (spec D5.1, enmienda del 16-10). Aqui esta lo que costaria **el mismo giro**
//! sin futuros, sin cola de temporizadores y sin las ISR del DMA:
//!
//! - **Un temporizador (`TIM7`)** marca el periodo y su ISR (`P2`, como el
//!   ejecutor) hace dos cosas seguidas: cierra el giro anterior -- juez, eventos
//!   de la politica, cuentas -- y arma el siguiente.
//! - **La ISR del SPI** (`P1`) es la de siempre ([`crate::j2_spi::Isr`]): guarda
//!   el `EOT` en el `Turno` de la ranura. Nadie la espera: el `Turno` lo lee la
//!   ISR del periodo.
//! - **Los dos canales del GPDMA se programan una vez** (`TR1`, `TR2`, `TR3`,
//!   `LLR`, `CR`) y por giro solo se escriben `BR1`, la direccion de memoria y
//!   `CR.EN`. Sin `TCIE`: no hay ISR del DMA, el cierre mira `SR`.
//! - **Cada registro se escribe entero**, con el valor ya calculado, en vez de
//!   leer-modificar-escribir: a 800 MHz cada lectura de un periferico espera al
//!   bus, y un giro con ~100 accesos ya no cabe en 2 500 ciclos sea cual sea el
//!   codigo (`costes_bus`).
//!
//! **Lo que NO hace, y por eso es una cota inferior:** el plazo (D3) y el
//! reinicio (D4) -- si el giro anterior no acabo, solo lo cuenta y no arma --, el
//! calendario con su hueco de atraso, ni el `EOT` tardio. Cada uno es un camino
//! raro que no entra en el coste de un giro normal, pero hay que escribirlo
//! antes de que esto sea un transporte. Los canales y los bufferes van sin
//! region MPU (R-MJ7), igual que la pasada `-sin-mpu` de `carga_j2`.
//!
//! Solo para el banco, detras de la feature `transporte-isr`.

use core::cell::UnsafeCell;
use core::sync::atomic::Ordering;

use embassy_stm32::interrupt;
use embassy_stm32::interrupt::{InterruptExt, Priority};
use embassy_stm32::pac::gpdma::vals as dma;
use embassy_stm32::{pac, peripherals, rcc, Peri};
use embassy_time::Instant;
use sam17_nucleo_core::maestro_j2::{
    Evento, Ranura as Politica, Tsize, Umbrales, PERIODO_GIRO_US,
};

use crate::j2_ejecutor::{publicar_cuentas, Bajada, Juez, SELLOS};
use crate::j2_spi::{Partes, Ranura, ESTADOS, LARGO_MAX};
use crate::perfil::{self, Fase};

/// La ranura del banco, igual que en el ejecutor.
const N: usize = 0;
/// Los canales del GPDMA1 de esta ranura: los de `maestro_del_banco`.
const CANAL_TX: usize = 0;
const CANAL_RX: usize = 1;

/// Un canal del GPDMA ya programado: lo que se escribe por giro.
struct Canal {
    ch: pac::gpdma::Channel,
    /// `CR` con `EN` puesto, calculado una vez.
    cr_en: pac::gpdma::regs::ChCr,
}

impl Canal {
    /// Programa el canal **una vez**: lo mismo que `configure` de embassy
    /// (`dma/gpdma/mod.rs:633`) con `TransferOptions::default()` en el N6 --
    /// prioridad alta, canal seguro --, sin `TCIE`.
    fn nuevo(num: usize, peticion: u8, a_periferico: bool, periferico: u32) -> Canal {
        let ch = pac::GPDMA1.ch(num);
        // Parado y limpio, como lo deja el reset de embassy.
        ch.cr().write(|w| w.set_reset(true));
        ch.fcr().write(|w| {
            w.set_dtef(true);
            w.set_htf(true);
            w.set_suspf(true);
            w.set_tcf(true);
            w.set_tof(true);
            w.set_ulef(true);
            w.set_usef(true);
        });
        ch.llr().write(|_| {});
        ch.tr1().write(|w| {
            w.set_sdw(dma::Dw::Byte);
            w.set_ddw(dma::Dw::Byte);
            w.set_sinc(a_periferico);
            w.set_dinc(!a_periferico);
            w.set_dap(if a_periferico {
                dma::Ap::Port1
            } else {
                dma::Ap::Port0
            });
            w.set_sap(if a_periferico {
                dma::Ap::Port0
            } else {
                dma::Ap::Port1
            });
            w.set_sbl_1(0);
            w.set_dbl_1(0);
            w.set_ssec(true);
            w.set_dsec(true);
        });
        ch.tr2().write(|w| {
            w.set_dreq(if a_periferico {
                dma::Dreq::DestinationPeripheral
            } else {
                dma::Dreq::SourcePeripheral
            });
            w.set_breq(dma::Breq::Burst);
            w.set_reqsel(peticion);
            w.set_tcem(dma::Tcem::EachBlock);
        });
        ch.tr3().write(|_| {});
        // El lado del periferico no cambia entre giros: la direccion de `TXDR` o
        // `RXDR` se escribe aqui y no se vuelve a tocar.
        if a_periferico {
            ch.dar().write_value(periferico);
        } else {
            ch.sar().write_value(periferico);
        }
        ch.cr().write(|w| {
            w.set_prio(dma::Prio::High);
            w.set_useie(true);
            w.set_dteie(true);
            w.set_suspie(true);
        });
        let mut cr_en = ch.cr().read();
        cr_en.set_en(true);
        Canal { ch, cr_en }
    }
}

/// Todo lo que el temporizador necesita: la ranura, la politica y los bufferes.
struct Giro {
    regs: pac::spi::Spi,
    tx: Canal,
    rx: Canal,
    /// Las tres palabras de `CFG1` que se escriben, calculadas una vez.
    cfg1_apagado: pac::spi::regs::Cfg1,
    cfg1_rx: pac::spi::regs::Cfg1,
    cfg1_ambos: pac::spi::regs::Cfg1,
    /// `CR1` con `SPE` y con `SPE` y `CSTART`.
    cr1_spe: pac::spi::regs::Cr1,
    cr1_arranque: pac::spi::regs::Cr1,
    ciclos_retardo: u32,
    politica: Politica,
    bajada_fn: Bajada,
    juez: Juez,
    bajada: [u8; LARGO_MAX],
    subida: [u8; LARGO_MAX],
    tsize: Tsize,
    en_vuelo: bool,
    plazos: u32,
    errores_dma: u32,
    // La ranura se guarda viva: sus `Flex` desconfiguran los pines al caer.
    _ranura: Ranura<'static>,
}

struct Celda(UnsafeCell<Option<Giro>>);
// SAFETY: solo la ISR de `TIM7` la toca, y `lanzar` antes de habilitarla.
unsafe impl Sync for Celda {}
static GIRO: Celda = Celda(UnsafeCell::new(None));

fn ahora_us() -> u64 {
    Instant::now().as_micros()
}

impl Giro {
    /// El cierre del giro anterior: `true` si acabo bien. Lee `SR` de los dos
    /// canales, borra sus banderas y apaga el SPI.
    fn cierra(&mut self) -> bool {
        let sr_rx = self.rx.ch.sr().read();
        let sr_tx = self.tx.ch.sr().read();
        let bien = sr_rx.tcf() && sr_tx.tcf();
        if sr_rx.dtef()
            || sr_rx.usef()
            || sr_rx.ulef()
            || sr_tx.dtef()
            || sr_tx.usef()
            || sr_tx.ulef()
        {
            self.errores_dma += 1;
        }
        self.rx.ch.fcr().write(|w| w.set_tcf(true));
        self.tx.ch.fcr().write(|w| w.set_tcf(true));
        // Cierre ordenado: `SPE = 0` y solo entonces los dos `DMAEN` (spec D2).
        self.regs.cr1().write_value(self.cr1_spe_apagado());
        self.regs.cfg1().write_value(self.cfg1_apagado);
        bien
    }

    fn cr1_spe_apagado(&self) -> pac::spi::regs::Cr1 {
        let mut v = self.cr1_spe;
        v.set_spe(false);
        v
    }

    /// El arranque de D2 (enmendado el 11-09), con el DMA ya programado.
    fn arma(&mut self, n: u16) {
        let regs = self.regs;
        regs.ifcr().write(|w| w.set_txtfc(true));
        regs.cr2().write(|w| w.set_tsize(n));
        regs.cfg1().write_value(self.cfg1_rx);
        // El receptor primero, como en `giro`.
        self.rx.ch.br1().write(|w| w.set_bndt(n));
        self.rx
            .ch
            .dar()
            .write_value(self.subida.as_mut_ptr() as u32);
        self.rx.ch.cr().write_value(self.rx.cr_en);
        self.tx.ch.br1().write(|w| w.set_bndt(n));
        self.tx.ch.sar().write_value(self.bajada.as_ptr() as u32);
        self.tx.ch.cr().write_value(self.tx.cr_en);
        regs.cfg1().write_value(self.cfg1_ambos);
        regs.cr1().write_value(self.cr1_spe);
        // El anclaje de la enmienda del 11-09 y el retardo de >= 1 `T_SCK`.
        let _ = regs.cr1().read();
        cortex_m::asm::delay(self.ciclos_retardo);
        regs.ifcr().write(|w| w.set_eotc(true));
        regs.ier().write(|w| w.set_eotie(true));
        regs.cr1().write_value(self.cr1_arranque);
    }
}

/// Pone en marcha el periodo: construye el estado y arranca `TIM7`.
///
/// `ranura` es la ya construida (`j2_banco::maestro_del_banco`); sus canales se
/// reprograman aqui por registros, asi que no hay que haberlos usado. El `tim`
/// es el `TIM7`, y `periodo_us` el del giro.
pub fn lanzar(
    ranura: Ranura<'static>,
    tim: Peri<'static, peripherals::TIM7>,
    periodo_us: u32,
    bajada_fn: Bajada,
    juez: Juez,
) {
    let _ = tim;
    let Partes {
        regs,
        req_tx,
        req_rx,
        cfg1,
        ciclos_retardo,
    } = ranura.partes();
    let mut politica = Politica::nueva(Umbrales::POR_DEFECTO);
    let _ = politica.paso(Evento::Identidad(true), ahora_us());

    let mut cfg1_rx = cfg1;
    cfg1_rx.set_rxdmaen(true);
    let mut cfg1_ambos = cfg1_rx;
    cfg1_ambos.set_txdmaen(true);
    let mut cfg1_apagado = cfg1;
    cfg1_apagado.set_rxdmaen(false);
    cfg1_apagado.set_txdmaen(false);
    // `CR1` leido una vez, con el SPI apagado: lo demas (`SSI`, `CRC`...) queda
    // como lo dejo `nueva`.
    regs.cr1().modify(|w| w.set_spe(false));
    let mut cr1_spe = regs.cr1().read();
    cr1_spe.set_spe(true);
    let mut cr1_arranque = cr1_spe;
    cr1_arranque.set_cstart(true);

    let txdr = regs.txdr32().as_ptr() as u32;
    let rxdr = regs.rxdr32().as_ptr() as u32;
    let giro = Giro {
        regs,
        tx: Canal::nuevo(CANAL_TX, req_tx, true, txdr),
        rx: Canal::nuevo(CANAL_RX, req_rx, false, rxdr),
        cfg1_apagado,
        cfg1_rx,
        cfg1_ambos,
        cr1_spe,
        cr1_arranque,
        ciclos_retardo,
        politica,
        bajada_fn,
        juez,
        bajada: [0; LARGO_MAX],
        subida: [0; LARGO_MAX],
        tsize: match Tsize::nuevo(1) {
            Some(t) => t,
            None => defmt::panic!("Tsize(1)"),
        },
        en_vuelo: false,
        plazos: 0,
        errores_dma: 0,
        _ranura: ranura,
    };
    // SAFETY: la ISR de `TIM7` aun esta apagada.
    unsafe { *GIRO.0.get() = Some(giro) };

    rcc::enable_and_reset::<peripherals::TIM7>();
    let f_timer = rcc::frequency::<peripherals::TIM7>().0;
    let psc = f_timer / 1_000_000 - 1;
    defmt::assert!(psc <= 0xFFFF && periodo_us <= 0x1_0000);
    // El periodo del banco puede ser mayor que el del instrumento, nunca menor
    // (spec D5.1, enmienda del 16-10): lo mismo que exige `lanzar_ranuras`.
    defmt::assert!(
        periodo_us >= PERIODO_GIRO_US,
        "j2_isr: periodo de {} us, menor que el del instrumento ({} us)",
        periodo_us,
        PERIODO_GIRO_US
    );
    let t = pac::TIM7;
    t.psc().write_value(psc as u16);
    t.arr().write(|w| w.set_arr((periodo_us - 1) as u16));
    t.egr().write(|w| w.set_ug(true));
    t.sr().write(|w| w.set_uif(false));
    t.dier().modify(|w| w.set_uie(true));
    interrupt::TIM7.set_priority(Priority::P2);
    // SAFETY: el vector `TIM7` es la ISR de abajo.
    unsafe { interrupt::TIM7.enable() };
    t.cr1().modify(|w| w.set_cen(true));
}

/// Las cuentas de la ranura, por las mismas casillas que el ejecutor.
fn publica(g: &Giro) {
    publicar_cuentas(N, &g.politica, 0);
}

#[interrupt]
unsafe fn TIM7() {
    let inicio = perfil::marca();
    pac::TIM7.sr().write(|w| w.set_uif(false));
    // SAFETY: es la unica que toca `GIRO` una vez habilitada.
    let g = unsafe { (*GIRO.0.get()).as_mut() };
    let Some(g) = g else { return };
    let ahora = ahora_us();

    if g.en_vuelo {
        // El `EOT` que guardo la ISR del SPI. Sin el, el giro no acabo: se
        // cuenta y no se arma (el plazo y D4 no estan escritos, ver la cabecera).
        let eot = ESTADOS[N].turno.tomar().is_some_and(|b| b.eot());
        if !eot {
            g.plazos += 1;
            perfil::cierra_isr(Fase::Ejecutor, inicio);
            return;
        }
        if g.cierra() {
            let largo = g.tsize.get() as usize;
            let _ = g.politica.paso(Evento::GiroOk, ahora);
            let ev = if (g.juez)(N, &g.subida[..largo]) {
                Evento::SubidaOk
            } else {
                Evento::SubidaMala
            };
            let _ = g.politica.paso(ev, ahora);
            publica(g);
        } else {
            // El `EOT` llego pero el DMA no acabo bien: `cierra` ya apago el SPI.
            // Se cuenta y se rearma; antes se quedaba `en_vuelo` para siempre.
            g.plazos += 1;
        }
        g.en_vuelo = false;
    }

    g.tsize = (g.bajada_fn)(N, &mut g.bajada);
    SELLOS[N].fetch_add(1, Ordering::Relaxed);
    let _ = g.politica.paso(Evento::Armada, ahora);
    let _ = ESTADOS[N].turno.armar();
    g.arma(g.tsize.get());
    g.en_vuelo = true;
    perfil::cierra_isr(Fase::Ejecutor, inicio);
}

/// Los fallos que no son un giro normal, para el banco: plazos y errores del DMA.
pub fn fallos() -> (u32, u32) {
    // SAFETY: lectura de dos enteros; el banco la usa con el periodo corriendo y
    // un valor a medias solo mueve la cuenta de un giro.
    match unsafe { (*GIRO.0.get()).as_ref() } {
        Some(g) => (g.plazos, g.errores_dma),
        None => (0, 0),
    }
}
