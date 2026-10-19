//! **El transporte del J2 «por tic»**: un temporizador, una maquina por ranura y registros.
//!
//! Spec: `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v2.md`, §2. **Prototipo
//! de banco** (acta del 17-10, ficha 3): no es el transporte firmado de D5.1 y no entra en
//! el binario del instrumento. Detras de la feature `transporte-tic`.
//!
//! Tres niveles de interrupcion, y ninguna mas:
//!
//! - **El tic (`TIM7`, P1)** cada periodo, para cada ranura: si hay una transferencia
//!   armada lee `SR` del SPI y de los dos canales, se lo da a [`Transporte`] (la maquina
//!   pura de `core`) y ejecuta lo que ella diga -- cerrar, armar, nada --. Es el unico
//!   que escribe el estado de una ranura. **No hay interrupcion de SPI ni de DMA**:
//!   `EOTIE` y todas las `IE` de los canales a cero y sus lineas del NVIC enmascaradas.
//! - **El planificador (`DMA2D`, P3)**, que el tic hace pendiente: vacia el anillo de
//!   eventos de cada ranura, es el unico que llama a la politica (`maestro_j2::Ranura`)
//!   con el reloj `tic x periodo`, lee la subida, la juzga y compone la trama siguiente.
//! - **La recuperacion (`JPEG`, P4)**, por debajo del planificador: D4 con `RESET` del
//!   canal, reset del SPI por RCC, reprogramacion completa y, si un canal no para, la
//!   escalada que resetea el GPDMA1 entero. Las dos lineas son vectores que ningun otro
//!   modulo atiende (`DMA2D` y `JPEG`); `GFXTIM` es del ejecutor.
//!
//! **Los bufferes** (`REGION`) van en una region no cacheable (R-MJ7): tres casillas de
//! bajada por ranura (el buzon de [`Triple`]) y dos de subida. La region la programa
//! [`lanzar`]; la D-cache se enciende despues, desde el binario.
//!
//! Lo que el prototipo quiere medir: los ciclos por giro con y sin componer la trama, si
//! sostiene 8 kHz contra el esclavo real sin un plazo vencido, y si la recuperacion
//! funciona en placa. Lo que NO es: el planificador real, la identidad por I2C, ni la
//! cabecera. Desviaciones del papel, dichas aqui y no en silencio: el buzon es de **tres**
//! casillas (ver `core::buzones_j2`); la reinicializacion del SPI (RCC, `CFG2`, `CFG1`)
//! va en una sola seccion critica y no solo el reset; y el planificador manda un
//! `Evento::Tick` solo a la ranura que en esa pasada no recibio ningun otro evento, porque
//! todo evento lleva ya su `ahora_us` y desliza la ventana de la politica; `Vencida` y
//! `Reiniciando` dan la ranura por muerta a los 100 tics y no a los 2 y 4 (revision de Halberg
//! del 17-10, hallazgo 1: una retencion de P2 de 350 us coincidiendo con un cuelgue la mataba);
//! y el reloj de la politica es de 64 bits (`Reloj64`), porque el contador de 32 bits del tic da la
//! vuelta a los 6,2 dias.

use core::cell::UnsafeCell;
use core::ptr::addr_of_mut;
use core::sync::atomic::{AtomicBool, AtomicU16, AtomicU32, AtomicU8, Ordering};

use cortex_m::peripheral::{DWT, NVIC};
use embassy_stm32::interrupt;
use embassy_stm32::interrupt::{InterruptExt, Priority};
use embassy_stm32::pac::gpdma::vals as dma;
use embassy_stm32::{pac, peripherals, rcc, Peri};
use sam17_nucleo_core::buzones_j2::{Anillo, Lectura as LecturaSubida, Subida, Triple};
use sam17_nucleo_core::escaladas_j2::Presupuesto;
use sam17_nucleo_core::maestro_j2::{
    plazo_us, Accion, Evento, Ranura as Politica, Umbrales, RANURAS_SPI,
};
use sam17_nucleo_core::transporte_j2::{
    tics_de_plazo, Aviso, Entrada, Estado, Lectura, Reloj64, RelojDelTic, Transporte,
};

use crate::j2_ejecutor::{publicar_cuentas, Bajada, Juez, SELLOS};
use crate::j2_spi::{Partes, Ranura, ESCALADAS_GPDMA, IRQ_DE_RANURA, LARGO_MAX};
use crate::mpu;

const N: usize = RANURAS_SPI;

/// Los niveles del papel v2 (§2.1): el tic en el 1, el planificador en el 3 y la
/// recuperacion en el 4. `embassy_stm32::interrupt` numera al reves que la urgencia.
const PRIO_TIC: Priority = Priority::P1;
const PRIO_PLAN: Priority = Priority::P3;
const PRIO_REC: Priority = Priority::P4;
const IRQ_PLAN: interrupt::Interrupt = interrupt::DMA2D;
const IRQ_REC: interrupt::Interrupt = interrupt::JPEG;

/// Cota de la espera a `SUSPF` al parar un canal, en microsegundos (papel v2, §2.5, paso 1).
/// ESTIMADO: es tiempo de pared y el tic puede expropiar el sondeo.
pub const T_CANAL_US: u32 = 25;
/// Hueco entre el fin de la recuperacion y el primer armado (`T_GAP`, D8). ESTIMADO.
pub const T_GAP_REARME_US: u32 = 2;
/// Un tic que entra con el contador del temporizador por encima de esto va tarde (§2.8).
const TARDIO_US: u16 = 10;

/// Los canales del GPDMA1 de la ranura `n` son `2n` y `2n + 1` (los de `j2_banco`).
const IRQ_CANAL: [interrupt::Interrupt; 12] = [
    interrupt::GPDMA1_CHANNEL0,
    interrupt::GPDMA1_CHANNEL1,
    interrupt::GPDMA1_CHANNEL2,
    interrupt::GPDMA1_CHANNEL3,
    interrupt::GPDMA1_CHANNEL4,
    interrupt::GPDMA1_CHANNEL5,
    interrupt::GPDMA1_CHANNEL6,
    interrupt::GPDMA1_CHANNEL7,
    interrupt::GPDMA1_CHANNEL8,
    interrupt::GPDMA1_CHANNEL9,
    interrupt::GPDMA1_CHANNEL10,
    interrupt::GPDMA1_CHANNEL11,
];

// ---------------------------------------------------------------------------------------
// Memoria compartida
// ---------------------------------------------------------------------------------------

struct Celda<T>(UnsafeCell<T>);
// SAFETY: cada celda tiene un dueno por nivel de interrupcion, dicho en su documentacion;
// los accesos cruzados son atomicos o van dentro de una seccion critica.
unsafe impl<T> Sync for Celda<T> {}

impl<T> Celda<T> {
    const fn nueva(v: T) -> Celda<T> {
        Celda(UnsafeCell::new(v))
    }
}

/// Una casilla de bufer: una linea de D-cache por cada 32 bytes, para que la region no
/// comparta lineas con nada.
#[repr(C, align(32))]
struct Casilla([u8; LARGO_MAX]);

#[repr(C, align(32))]
struct PorRanura {
    bajada: [Casilla; 3],
    subida: [Casilla; 2],
}

#[repr(C, align(32))]
struct Region([PorRanura; N]);

static REGION: Celda<Region> = Celda::nueva(Region(
    [const {
        PorRanura {
            bajada: [const { Casilla([0; LARGO_MAX]) }; 3],
            subida: [const { Casilla([0; LARGO_MAX]) }; 2],
        }
    }; N],
));

/// La base y el largo de la region de los bufferes del DMA. [`lanzar`] la programa en la
/// MPU; esto es para que el binario la pueda imprimir.
pub fn region() -> (u32, u32) {
    (REGION.0.get() as u32, core::mem::size_of::<Region>() as u32)
}

fn ptr_bajada(n: usize, c: usize) -> *mut u8 {
    // SAFETY: solo se calcula una direccion.
    unsafe { addr_of_mut!((*REGION.0.get()).0[n].bajada[c].0) as *mut u8 }
}

fn ptr_subida(n: usize, c: usize) -> *mut u8 {
    // SAFETY: solo se calcula una direccion.
    unsafe { addr_of_mut!((*REGION.0.get()).0[n].subida[c].0) as *mut u8 }
}

/// Copia `bloques` bloques de 32 bytes con `ldm`/`stm` de ocho palabras: la forma barata
/// de leer y de escribir la region no cacheable (`costes_dma`: un acceso suelto cuesta 84
/// ciclos, un `ldm` de ocho palabras, 96).
///
/// # Safety
/// `dst` y `src` alineados a palabra y validos para `bloques * 32` bytes.
#[inline(always)]
unsafe fn copia_bloques(dst: *mut u32, src: *const u32, bloques: usize) {
    if bloques == 0 {
        return;
    }
    // SAFETY: lo pide el contrato de arriba. r6 y r7 no se usan (el compilador los reserva).
    unsafe {
        core::arch::asm!(
            "2:",
            "ldm {s}!, {{r0-r5, r8, r10}}",
            "stm {d}!, {{r0-r5, r8, r10}}",
            "subs {n}, {n}, #1",
            "bne 2b",
            s = inout(reg) src => _,
            d = inout(reg) dst => _,
            n = inout(reg) bloques => _,
            out("r0") _, out("r1") _, out("r2") _, out("r3") _,
            out("r4") _, out("r5") _, out("r8") _, out("r10") _,
            options(nostack),
        );
    }
}

const fn bloques(largo: usize) -> usize {
    largo.div_ceil(32)
}

/// Un bufer local del planificador, alineado para el `ldm`.
#[repr(C, align(32))]
struct Local([u8; LARGO_MAX]);

// ---------------------------------------------------------------------------------------
// El hardware de una ranura
// ---------------------------------------------------------------------------------------

/// Un canal del GPDMA con su programacion entera, para escribirla de nuevo cuando haga falta.
struct Canal {
    ch: pac::gpdma::Channel,
    peticion: u8,
    a_periferico: bool,
    periferico: u32,
    /// `CR` con `EN` puesto y todas las `IE` a cero: lo unico que se escribe por giro.
    cr_en: pac::gpdma::regs::ChCr,
}

impl Canal {
    fn nuevo(num: usize, peticion: u8, a_periferico: bool, periferico: u32) -> Canal {
        let ch = pac::GPDMA1.ch(num);
        let mut c = Canal {
            ch,
            peticion,
            a_periferico,
            periferico,
            cr_en: ch.cr().read(),
        };
        c.programa();
        let mut cr_en = ch.cr().read();
        cr_en.set_en(true);
        c.cr_en = cr_en;
        c
    }

    /// Papel v2, §2.5 paso 4: `FCR`, `LLR`, `TR1`, `TR2`, `TR3`, la direccion del lado
    /// periferico y `CR` con todas las `IE` a cero. Idempotente: sirve igual tras el
    /// `RESET` de un canal (que conserva `TR1`-`TR3`) que tras el reset del GPDMA1 por RCC
    /// (que lo borra todo).
    fn programa(&self) {
        let ch = self.ch;
        let a_periferico = self.a_periferico;
        ch.cr().write(|w| w.set_reset(true));
        ch.fcr().write(banderas);
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
            w.set_reqsel(self.peticion);
            w.set_tcem(dma::Tcem::EachBlock);
        });
        ch.tr3().write(|_| {});
        if a_periferico {
            ch.dar().write_value(self.periferico);
        } else {
            ch.sar().write_value(self.periferico);
        }
        ch.cr().write(|w| w.set_prio(dma::Prio::High));
    }
}

/// Todas las banderas de `FCR`: escribir uno las borra.
fn banderas(w: &mut pac::gpdma::regs::ChFcr) {
    w.set_tcf(true);
    w.set_htf(true);
    w.set_dtef(true);
    w.set_ulef(true);
    w.set_usef(true);
    w.set_suspf(true);
    w.set_tof(true);
}

/// Lo que el tic y la recuperacion necesitan de una ranura. Todo de solo lectura una vez
/// construido: los registros son manejadores `Copy`.
struct Hw {
    regs: pac::spi::Spi,
    tx: Canal,
    rx: Canal,
    cfg1: pac::spi::regs::Cfg1,
    cfg1_rx: pac::spi::regs::Cfg1,
    cfg1_ambos: pac::spi::regs::Cfg1,
    cfg1_apagado: pac::spi::regs::Cfg1,
    cfg2: pac::spi::regs::Cfg2,
    cr1_apagado: pac::spi::regs::Cr1,
    cr1_spe: pac::spi::regs::Cr1,
    cr1_arranque: pac::spi::regs::Cr1,
    ciclos_retardo: u32,
    resetear: fn(),
    /// La ranura se guarda viva: sus `Flex` desconfiguran los pines al caer.
    _ranura: Ranura<'static>,
}

impl Hw {
    /// Lo que el tic lee de una ranura armada: `EOT` del SPI y `TCF` y errores de los dos canales.
    #[inline(always)]
    fn lee(&self) -> Lectura {
        let sr = self.regs.sr().read();
        let rx = self.rx.ch.sr().read();
        let tx = self.tx.ch.sr().read();
        Lectura {
            eot: sr.eot(),
            tcf_rx: rx.tcf(),
            tcf_tx: tx.tcf(),
            error_dma: rx.dtef() || rx.usef() || rx.ulef() || tx.dtef() || tx.usef() || tx.ulef(),
        }
    }

    /// El cierre del papel v2, §2.3: banderas, `SPE = 0` y solo entonces los dos `DMAEN`.
    #[inline(always)]
    fn cierra(&self) {
        self.rx.ch.fcr().write(banderas);
        self.tx.ch.fcr().write(banderas);
        self.regs.cr1().write_value(self.cr1_apagado);
        self.regs.cfg1().write_value(self.cfg1_apagado);
    }

    /// El arranque de D2 con sus tres enmiendas, sin `EOTIE`, con el DMA ya programado
    /// (`bndt_tx` es `n` salvo cuando el banco envenena la ranura):
    /// `SPE = 0 -> TXTFC -> TSIZE -> CFG1(RXDMAEN) -> canal RX -> canal TX -> CFG1(TXDMAEN)
    /// -> SPE = 1 -> leer CR1 -> esperar >= 1 T_SCK -> EOTC -> CSTART`.
    #[inline(always)]
    fn arma(&self, n: u16, bndt_tx: u16, bajada: u32, subida: u32) {
        let regs = self.regs;
        // El primer `SPE = 0` se conserva (papel v2, §2.3).
        regs.cr1().write_value(self.cr1_apagado);
        regs.ifcr().write(|w| w.set_txtfc(true));
        regs.cr2().write(|w| w.set_tsize(n));
        regs.cfg1().write_value(self.cfg1_rx);
        // `BR1`, `DAR` y `SAR` solo se escriben con `EN = 0`. No se lee `CR.EN`: la ranura llega aqui `Libre`,
        // y a `Libre` se llega con `TCF` de los dos canales o tras el `RESET` de la recuperacion. En los dos
        // casos `EN` ya esta en cero: GPDMA_CxCR.EN *"is deasserted by hardware when there is a transfer
        // error [...] or when there is a channel transfer complete"* y `RESET` lo baja siempre (RM0486 Rev 4,
        // bit 0 EN; hallazgo 8a).
        self.rx.ch.br1().write(|w| w.set_bndt(n));
        self.rx.ch.dar().write_value(subida);
        self.rx.ch.cr().write_value(self.rx.cr_en);
        self.tx.ch.br1().write(|w| w.set_bndt(bndt_tx));
        self.tx.ch.sar().write_value(bajada);
        self.tx.ch.cr().write_value(self.tx.cr_en);
        regs.cfg1().write_value(self.cfg1_ambos);
        regs.cr1().write_value(self.cr1_spe);
        // El anclaje de la enmienda del 11-09 y el retardo de >= 1 `T_SCK`.
        let _ = regs.cr1().read();
        cortex_m::asm::delay(self.ciclos_retardo);
        regs.ifcr().write(|w| w.set_eotc(true));
        regs.cr1().write_value(self.cr1_arranque);
    }
}

/// El estado que escribe el tic. Dueno: el tic; la recuperacion solo lo toca dentro de la
/// seccion critica de la escalada.
struct Tic {
    transporte: Transporte,
    /// La casilla de subida donde escribe el DMA de la transferencia en vuelo.
    rx_actual: u8,
    /// El largo de la transferencia en vuelo.
    largo: u8,
}

/// Los contadores de una ranura que no son de la politica.
struct Cont {
    sin_bajada: AtomicU32,
    errores_dma: AtomicU32,
    muertas: AtomicU32,
    recuperaciones: AtomicU32,
}

impl Cont {
    const fn nuevo() -> Cont {
        Cont {
            sin_bajada: AtomicU32::new(0),
            errores_dma: AtomicU32::new(0),
            muertas: AtomicU32::new(0),
            recuperaciones: AtomicU32::new(0),
        }
    }
}

#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static HW: [Celda<Option<Hw>>; N] = [const { Celda::nueva(None) }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static TIC: [Celda<Tic>; N] = [const {
    Celda::nueva(Tic {
        transporte: Transporte::nuevo(),
        rx_actual: 0,
        largo: 0,
    })
}; N];

#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static IDENTIDAD: [AtomicBool; N] = [const { AtomicBool::new(false) }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static BUZON: [Triple; N] = [const { Triple::nuevo() }; N];
/// Por casilla de bajada, el mensaje que contiene: `plazo en tics << 8 | largo`. Lo escribe
/// el planificador antes de publicar y lo lee el tic.
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static META: [[AtomicU16; 3]; N] = [const { [const { AtomicU16::new(0) }; 3] }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static SUBIDA: [Subida; N] = [const { Subida::nueva() }; N];
/// El largo de la transferencia que produjo la ultima subida publicada.
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static LARGO_SUBIDA: [AtomicU8; N] = [const { AtomicU8::new(0) }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static ANILLO: [Anillo<8>; N] = [const { Anillo::nuevo() }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static CONT: [Cont; N] = [const { Cont::nuevo() }; N];

/// El apreton de manos de la recuperacion (papel v2, §2.5).
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static REC_PEDIDA: [AtomicBool; N] = [const { AtomicBool::new(false) }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static REC_EN_CURSO: [AtomicBool; N] = [const { AtomicBool::new(false) }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static REC_HECHA: [AtomicBool; N] = [const { AtomicBool::new(false) }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static REC_T_HECHA: [AtomicU32; N] = [const { AtomicU32::new(0) }; N];
/// El incidente de cada ranura (papel v3, K4): el tic publica el suyo, el planificador lo pone
/// en la peticion y la recuperacion lo devuelve con `EN_CURSO` y `HECHA`.
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static INCIDENTE: [AtomicU32; N] = [const { AtomicU32::new(0) }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static REC_INCIDENTE_PEDIDO: [AtomicU32; N] = [const { AtomicU32::new(0) }; N];
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static REC_INCIDENTE: [AtomicU32; N] = [const { AtomicU32::new(0) }; N];
/// El presupuesto de escaladas del GPDMA1 (papel v3, §2.5, K1): como mucho `E_ESCALADAS` en
/// `VENTANA_ESCALADAS_US` del reloj del tic. ESTIMADOS. Dueno: la recuperacion, con su propio
/// reloj de 64 bits.
const E_ESCALADAS: usize = 3;
const VENTANA_ESCALADAS_US: u64 = 1_000_000;
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static PRESUPUESTO: Celda<Presupuesto> =
    Celda::nueva(Presupuesto::nuevo(E_ESCALADAS, VENTANA_ESCALADAS_US));
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static RELOJ_REC: Celda<Reloj64> = Celda::nueva(Reloj64::nuevo());
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static ESCALADAS_DENEGADAS: AtomicU32 = AtomicU32::new(0);
/// La ranura esta `Muerta`: lo publica el tic, y ni el planificador ni la recuperacion la tocan
/// (papel v3, §2.2, Halberg H5).
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static MUERTA: [AtomicBool; N] = [const { AtomicBool::new(false) }; N];
/// `canales_sucios`: la escalada reseteo el GPDMA1 y esta ranura aun no esta reprogramada.
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static SUCIA: [AtomicBool; N] = [const { AtomicBool::new(false) }; N];

#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static TICS: AtomicU32 = AtomicU32::new(0);
/// El contador de arriba extendido a 64 bits. Dueno: el planificador.
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static RELOJ_PLAN: Celda<Reloj64> = Celda::nueva(Reloj64::nuevo());
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static CICLOS_POR_US: AtomicU32 = AtomicU32::new(0);
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static TICS_TARDIOS: AtomicU32 = AtomicU32::new(0);
/// Periodos que una entrada del tic trajo de mas: actualizaciones fundidas en una (§2.8).
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static PERIODOS_SALTADOS: AtomicU32 = AtomicU32::new(0);
/// Entradas en las que el reloj del tic no pudo contar limpio y conto uno (§2.7).
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static RELOJ_ANOMALO: AtomicU32 = AtomicU32::new(0);
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static RETRASO_MAX_US: AtomicU32 = AtomicU32::new(0);
/// El reloj del tic (candidata K2). Dueno: el tic.
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static RELOJ_TIC: Celda<RelojDelTic> = Celda::nueva(RelojDelTic::nuevo(0, 0, 0));

#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static PERIODO_US: AtomicU32 = AtomicU32::new(0);
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static GAP_CICLOS: AtomicU32 = AtomicU32::new(0);
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static T_CANAL_CICLOS: AtomicU32 = AtomicU32::new(0);

/// Ciclos de CPU acumulados por nivel (con `--features perfil`): tic, planificador sin el
/// tic, recuperacion sin los otros dos, y dentro del planificador lo que gasta componer;
/// y dentro del tic, leer los registros de estado, cerrar y armar.
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static CICLOS: [AtomicU32; 7] = [const { AtomicU32::new(0) }; 7];

/// El tic mas largo desde la ultima lectura, en ciclos propios (sin la entrada ni la salida
/// de la excepcion). Con `--features perfil`.
#[cfg(feature = "perfil")]
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static TIC_MAX: AtomicU32 = AtomicU32::new(0);

/// El tic mas largo desde la llamada anterior, en ciclos, y lo pone a cero. Sin `perfil`, cero.
pub fn tic_max_ciclos() -> u32 {
    #[cfg(feature = "perfil")]
    return TIC_MAX.swap(0, Ordering::Relaxed);
    #[cfg(not(feature = "perfil"))]
    0
}

#[cfg(feature = "inyeccion")]
static ENVENENAR: [AtomicBool; N] = [const { AtomicBool::new(false) }; N];
#[cfg(feature = "inyeccion")]
static FORZAR_ESCALADA: AtomicBool = AtomicBool::new(false);
/// La proxima armada de la ranura lleva un error de ajuste de usuario del DMA (`USEF`).
#[cfg(feature = "inyeccion")]
static ENVENENAR_DMA: [AtomicBool; N] = [const { AtomicBool::new(false) }; N];
/// El planificador no pide la recuperacion: la ranura se queda en `Vencida` hasta `Muerta`.
#[cfg(feature = "inyeccion")]
static SIN_RECUPERACION: AtomicBool = AtomicBool::new(false);

/// Las marcas de tiempo (`DWT_CYCCNT`) del ultimo incidente de la ranura 0, en el orden de
/// [`Marca`]. Cero = aun no ocurrio.
#[cfg(feature = "inyeccion")]
static MARCAS: [AtomicU32; 10] = [const { AtomicU32::new(0) }; 10];

/// Los instantes de un incidente de la ranura 0: de un armado envenenado a la trama buena
/// siguiente.
#[cfg(feature = "inyeccion")]
#[derive(Clone, Copy)]
#[repr(usize)]
pub enum Marca {
    /// `CSTART` de la transferencia envenenada: el `CS` baja.
    CstartVeneno,
    /// El tic que dio la transferencia por vencida.
    Vencida,
    /// La recuperacion entra.
    RecInicio,
    /// Justo antes del reset del SPI por RCC: desde aqui el `CS` flota.
    ResetIni,
    /// Justo despues de reescribir `CFG2` y `CFG1`: el SPI vuelve a manejar el `CS`.
    ResetFin,
    /// La recuperacion publica `ReinicioHecho`.
    RecHecha,
    /// `CSTART` de la primera transferencia tras la recuperacion: el `CS` vuelve a bajar.
    CstartSiguiente,
    /// Entra la escalada del GPDMA1 (de la ultima escalada, de cualquier ranura).
    EscalaIni,
    /// Empieza la seccion critica de la escalada: desde aqui el tic no corre.
    SeccionIni,
    /// Acaba la seccion critica: el GPDMA1 ya esta reseteado y las ranuras, marcadas.
    SeccionFin,
}

#[cfg(feature = "inyeccion")]
fn marca(m: Marca, ciclos: u32) {
    MARCAS[m as usize].store(ciclos, Ordering::Relaxed);
}

// ---------------------------------------------------------------------------------------
// Lo que ve el banco
// ---------------------------------------------------------------------------------------

/// Los testigos y contadores del transporte, sumados sobre las ranuras activas (§2.8).
#[derive(Clone, Copy, defmt::Format)]
pub struct Testigos {
    pub tics: u32,
    pub tics_tardios: u32,
    pub periodos_saltados: u32,
    pub reloj_anomalo: u32,
    pub retraso_max_us: u32,
    pub sin_bajada: u32,
    pub errores_dma: u32,
    pub subidas_perdidas: u32,
    pub tramas_superadas: u32,
    pub eventos_perdidos: u32,
    pub ranuras_muertas: u32,
    pub recuperaciones: u32,
    pub escaladas_gpdma: u32,
    pub escaladas_denegadas: u32,
}

pub fn testigos() -> Testigos {
    let mut t = Testigos {
        tics: TICS.load(Ordering::Relaxed),
        tics_tardios: TICS_TARDIOS.load(Ordering::Relaxed),
        periodos_saltados: PERIODOS_SALTADOS.load(Ordering::Relaxed),
        reloj_anomalo: RELOJ_ANOMALO.load(Ordering::Relaxed),
        retraso_max_us: RETRASO_MAX_US.load(Ordering::Relaxed),
        sin_bajada: 0,
        errores_dma: 0,
        subidas_perdidas: 0,
        tramas_superadas: 0,
        eventos_perdidos: 0,
        ranuras_muertas: 0,
        recuperaciones: 0,
        escaladas_gpdma: ESCALADAS_GPDMA.load(Ordering::Relaxed),
        escaladas_denegadas: ESCALADAS_DENEGADAS.load(Ordering::Relaxed),
    };
    for n in 0..N {
        if !IDENTIDAD[n].load(Ordering::Relaxed) {
            continue;
        }
        let c = &CONT[n];
        t.sin_bajada += c.sin_bajada.load(Ordering::Relaxed);
        t.errores_dma += c.errores_dma.load(Ordering::Relaxed);
        t.subidas_perdidas += SUBIDA[n].perdidas();
        t.tramas_superadas += BUZON[n].superadas();
        t.eventos_perdidos += ANILLO[n].perdidos();
        t.ranuras_muertas += c.muertas.load(Ordering::Relaxed);
        t.recuperaciones += c.recuperaciones.load(Ordering::Relaxed);
    }
    t
}

/// Los ciclos acumulados desde el arranque, con la vuelta de 32 bits: tic, planificador,
/// recuperacion, componer la trama (dentro del planificador) y, dentro del tic, leer,
/// cerrar y armar. Con `--features perfil`; sin ella salen en cero.
pub fn ciclos() -> [u32; 7] {
    let mut v = [0u32; 7];
    for (d, s) in v.iter_mut().zip(CICLOS.iter()) {
        *d = s.load(Ordering::Relaxed);
    }
    v
}

#[inline(always)]
fn suma(nivel: usize, ciclos: u32) {
    #[cfg(feature = "perfil")]
    CICLOS[nivel].fetch_add(ciclos, Ordering::Relaxed);
    #[cfg(not(feature = "perfil"))]
    let _ = (nivel, ciclos);
}

/// Hace que la proxima armada de la ranura `n` salga mal a proposito: el canal de
/// transmision cuenta un byte menos que el `TSIZE`, y el maestro se queda sin dato a mitad
/// de trama con el `CS` abajo -- el cuelgue del repro original.
#[cfg(feature = "inyeccion")]
pub fn envenena(n: usize) {
    ENVENENAR[n].store(true, Ordering::Relaxed);
}

/// Hace que la proxima armada de la ranura `n` lleve un error del DMA: el canal de recepcion con
/// palabras de origen y un `BNDT` que no es multiplo de cuatro (RM0486, sec. 19.4.17: el tamano
/// del bloque tiene que ser multiplo del ancho de origen), que el DMA marca como error de ajuste
/// de usuario (`USEF`) y no arranca. Prueba la rama `error_dma` de la maquina, que el
/// reset por RCC de la recuperacion esconde.
#[cfg(feature = "inyeccion")]
pub fn envenena_dma(n: usize) {
    ENVENENAR_DMA[n].store(true, Ordering::Relaxed);
}

/// Hace que la proxima recuperacion trate el sondeo de `SUSPF` como vencido y escale.
#[cfg(feature = "inyeccion")]
pub fn fuerza_escalada() {
    FORZAR_ESCALADA.store(true, Ordering::Relaxed);
}

/// Con `true`, el planificador deja de pedir la recuperacion: lo que pase despues es la red
/// de las cotas de `Vencida` y `Reiniciando` (papel v2, par. 2.5).
#[cfg(feature = "inyeccion")]
pub fn sin_recuperacion(si: bool) {
    SIN_RECUPERACION.store(si, Ordering::Relaxed);
}

/// El estado de la maquina de la ranura `n`, para el banco. Lectura sin exclusion: vale
/// para mirar, no para decidir.
#[cfg(feature = "inyeccion")]
pub fn estado(n: usize) -> Estado {
    // SAFETY: lectura de un valor `Copy` que solo escribe el tic; un valor a medias solo
    // mueve la lectura de un tic.
    unsafe { (*TIC[n].0.get()).transporte.estado() }
}

/// Borra las marcas antes de provocar un incidente.
#[cfg(feature = "inyeccion")]
pub fn borra_marcas() {
    for m in MARCAS.iter() {
        m.store(0, Ordering::Relaxed);
    }
}

/// Las marcas del ultimo incidente de la ranura 0, en ciclos de CPU.
#[cfg(feature = "inyeccion")]
pub fn marcas() -> [u32; 10] {
    let mut v = [0u32; 10];
    for (d, s) in v.iter_mut().zip(MARCAS.iter()) {
        *d = s.load(Ordering::Relaxed);
    }
    v
}

// ---------------------------------------------------------------------------------------
// Arranque
// ---------------------------------------------------------------------------------------

/// Los datos del planificador por ranura: la politica, el compositor y los bufferes locales.
struct PlanRanura {
    politica: Politica,
    f_sck_hz: u32,
    umbrales: Umbrales,
    bajada_fn: Bajada,
    juez: Juez,
    local_bajada: Local,
    local_subida: Local,
}

#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static PLAN: [Celda<Option<PlanRanura>>; N] = [const { Celda::nueva(None) }; N];

/// Pone en marcha el transporte: construye el estado de cada ranura, programa la region
/// no cacheable, enmascara las lineas de SPI y de DMA que ya no atiende nadie, y arranca
/// el tic.
///
/// `ranuras` llega ya construida (`ranuras_de_medida!`); el D-cache tiene que seguir
/// apagado hasta que esta funcion vuelva (`Ranura::nueva` lo asevera), y despues se puede
/// encender: la region de los bufferes ya esta en la MPU. `f_cpu_hz` es el reloj del
/// nucleo, y `periodo_us` el del giro (no menor que el del instrumento).
pub fn lanzar(
    ranuras: [Option<Ranura<'static>>; N],
    _tim: Peri<'static, peripherals::TIM7>,
    periodo_us: u32,
    f_cpu_hz: u32,
    bajada_fn: Bajada,
    juez: Juez,
) {
    defmt::assert!(
        periodo_us >= sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US,
        "j2_tic: periodo de {} us, menor que el del instrumento",
        periodo_us
    );
    // SAFETY: nadie mas toca el DWT, el DEMCR ni la MPU en el banco.
    let mut cp = unsafe { cortex_m::Peripherals::steal() };
    cp.DCB.enable_trace();
    cp.DWT.enable_cycle_counter();

    PERIODO_US.store(periodo_us, Ordering::Relaxed);
    let ciclos_us = f_cpu_hz / 1_000_000;
    CICLOS_POR_US.store(ciclos_us, Ordering::Relaxed);
    GAP_CICLOS.store(T_GAP_REARME_US * ciclos_us, Ordering::Relaxed);
    T_CANAL_CICLOS.store(T_CANAL_US * ciclos_us, Ordering::Relaxed);

    #[cfg(feature = "j2-tcm")]
    {
        crate::j2_tcm::asevera_en_itcm(juez as usize, "el juez");
        crate::j2_tcm::asevera_en_itcm(bajada_fn as usize, "la bajada");
    }
    for (n, ranura) in ranuras.into_iter().enumerate() {
        let Some(ranura) = ranura else { continue };
        let f_sck_hz = ranura.f_sck_hz();
        let Partes {
            regs,
            req_tx,
            req_rx,
            cfg1,
            cfg2,
            ciclos_retardo,
            resetear,
        } = ranura.partes();
        #[cfg(feature = "j2-tcm")]
        crate::j2_tcm::asevera_en_itcm(resetear as usize, "el reset de la ranura");

        let mut cfg1_rx = cfg1;
        cfg1_rx.set_rxdmaen(true);
        let mut cfg1_ambos = cfg1_rx;
        cfg1_ambos.set_txdmaen(true);
        let mut cfg1_apagado = cfg1;
        cfg1_apagado.set_rxdmaen(false);
        cfg1_apagado.set_txdmaen(false);
        regs.cr1().modify(|w| w.set_spe(false));
        let cr1_apagado = regs.cr1().read();
        let mut cr1_spe = cr1_apagado;
        cr1_spe.set_spe(true);
        let mut cr1_arranque = cr1_spe;
        cr1_arranque.set_cstart(true);

        let txdr = regs.txdr32().as_ptr() as u32;
        let rxdr = regs.rxdr32().as_ptr() as u32;
        let hw = Hw {
            regs,
            tx: Canal::nuevo(2 * n, req_tx, true, txdr),
            rx: Canal::nuevo(2 * n + 1, req_rx, false, rxdr),
            cfg1,
            cfg1_rx,
            cfg1_ambos,
            cfg1_apagado,
            cfg2,
            cr1_apagado,
            cr1_spe,
            cr1_arranque,
            ciclos_retardo,
            resetear,
            _ranura: ranura,
        };
        let mut politica = Politica::nueva(Umbrales::POR_DEFECTO);
        let _ = politica.paso(Evento::Identidad(true), 0);
        // SAFETY: las interrupciones del transporte siguen apagadas.
        unsafe {
            *HW[n].0.get() = Some(hw);
            *PLAN[n].0.get() = Some(PlanRanura {
                politica,
                f_sck_hz,
                umbrales: Umbrales::POR_DEFECTO,
                bajada_fn,
                juez,
                local_bajada: Local([0; LARGO_MAX]),
                local_subida: Local([0; LARGO_MAX]),
            });
        }
        // Con `cotas-v2`, las cotas del papel v2 (2 y 4 tics) en vez de las de hoy: para medir
        // en placa lo que cambia la revision de Halberg del 17-10 (hallazgo 1).
        #[cfg(feature = "cotas-v2")]
        // SAFETY: las interrupciones del transporte siguen apagadas.
        unsafe {
            (*TIC[n].0.get()).transporte = Transporte::con_cotas(2, 4);
        }
        // La primera trama ya esta en el buzon cuando llega el primer tic.
        // SAFETY: las interrupciones del transporte siguen apagadas.
        if let Some(p) = unsafe { &mut *PLAN[n].0.get() }.as_mut() {
            compone(n, p);
        }
        // Nadie atiende las lineas de este SPI ni de sus dos canales: EOTIE y las IE de
        // los canales estan en cero, y `Ranura::nueva` los habia desenmascarado.
        IRQ_DE_RANURA[n].disable();
        IRQ_CANAL[2 * n].disable();
        IRQ_CANAL[2 * n + 1].disable();
        IDENTIDAD[n].store(true, Ordering::Relaxed);
    }

    let (base, largo) = region();
    mpu::region_no_cacheable(&mut cp.MPU, base, largo);

    rcc::enable_and_reset::<peripherals::TIM7>();
    let f_timer = rcc::frequency::<peripherals::TIM7>().0;
    let psc = f_timer / 1_000_000 - 1;
    defmt::assert!(psc <= 0xFFFF && periodo_us <= 0x1_0000);
    let t = pac::TIM7;
    t.psc().write_value(psc as u16);
    // El reloj del tic resta cuentas del temporizador de los ciclos del contador libre: los dos
    // relojes tienen que guardar una razon entera (R-H9). Tolerancia: dos cuentas. ESTIMADO.
    let num = u64::from(psc + 1) * u64::from(f_cpu_hz);
    defmt::assert!(
        num % u64::from(f_timer) == 0,
        "j2_tic: el TIM7 y el nucleo sin razon entera"
    );
    let ciclos_por_cuenta = (num / u64::from(f_timer)) as u32;
    // SAFETY: el tic todavia no corre; es el unico dueno del reloj despues.
    unsafe {
        *RELOJ_TIC.0.get() = RelojDelTic::nuevo(
            periodo_us * ciclos_us,
            ciclos_por_cuenta,
            2 * ciclos_por_cuenta,
        );
    }
    t.arr().write(|w| w.set_arr((periodo_us - 1) as u16));
    t.egr().write(|w| w.set_ug(true));
    t.sr().write(|w| w.set_uif(false));
    t.dier().modify(|w| w.set_uie(true));

    // La prioridad antes del `enable`, siempre.
    interrupt::TIM7.set_priority(PRIO_TIC);
    IRQ_PLAN.set_priority(PRIO_PLAN);
    IRQ_REC.set_priority(PRIO_REC);
    // SAFETY: los tres vectores son las ISR de abajo, y todo su estado esta construido.
    unsafe {
        IRQ_PLAN.enable();
        IRQ_REC.enable();
        interrupt::TIM7.enable();
    }
    t.cr1().modify(|w| w.set_cen(true));
}

// ---------------------------------------------------------------------------------------
// El tic (nivel 1)
// ---------------------------------------------------------------------------------------

#[interrupt]
unsafe fn TIM7() {
    let t0 = DWT::cycle_count();
    let tim = pac::TIM7;
    // Testigo de retraso: microsegundos desde el ultimo suceso de actualizacion (§2.8).
    let retraso = tim.cnt().read().cnt();
    tim.sr().write(|w| w.set_uif(false));
    if retraso > TARDIO_US {
        TICS_TARDIOS.fetch_add(1, Ordering::Relaxed);
    }
    if u32::from(retraso) > RETRASO_MAX_US.load(Ordering::Relaxed) {
        RETRASO_MAX_US.store(u32::from(retraso), Ordering::Relaxed);
    }
    // El reloj del tic cuenta periodos desde la actualizacion, no entradas (§2.7, K2).
    // SAFETY: el tic es el unico dueno de `RELOJ_TIC`.
    let p = unsafe { &mut *RELOJ_TIC.0.get() }.entrada(u32::from(retraso), t0);
    if p.anomalo {
        RELOJ_ANOMALO.fetch_add(1, Ordering::Relaxed);
    }
    if p.n == 0 {
        // Una reentrada por la misma actualizacion: no ha pasado ningun periodo.
        return;
    }
    if p.n > 1 {
        PERIODOS_SALTADOS.fetch_add(p.n - 1, Ordering::Relaxed);
    }
    let periodos = p.n.min(u32::from(u16::MAX)) as u16;
    TICS.store(
        TICS.load(Ordering::Relaxed).wrapping_add(p.n),
        Ordering::Relaxed,
    );

    let gap = GAP_CICLOS.load(Ordering::Relaxed);
    for n in 0..N {
        // SAFETY: el tic es el unico que toca `HW` y `TIC` de una ranura en marcha.
        let Some(hw) = (unsafe { &*HW[n].0.get() }).as_ref() else {
            continue;
        };
        // La marca entra en la maquina (papel v3, §2.2, K3): no se lee ni se arma, y las
        // esperas siguen contando contra sus cotas.
        let sucia = SUCIA[n].load(Ordering::Relaxed);
        let t = unsafe { &mut *TIC[n].0.get() };
        let antes = t.transporte.estado();
        #[cfg(feature = "perfil")]
        let a0 = DWT::cycle_count();
        let lectura = if matches!(antes, Estado::Armada { .. }) && !sucia {
            hw.lee()
        } else {
            Lectura::default()
        };
        #[cfg(feature = "perfil")]
        suma(4, DWT::cycle_count().wrapping_sub(a0));
        let bz = &BUZON[n];
        let bajada = bz
            .fresca()
            .map(|c| (META[n][c].load(Ordering::Relaxed) >> 8) as u8);
        // La recuperacion solo le importa a la maquina en `Vencida` y `Reiniciando`.
        let (en_curso, hecho) =
            if matches!(antes, Estado::Vencida { .. } | Estado::Reiniciando { .. }) {
                // `Acquire`: lo que la recuperacion reprogramo antes de publicar `HECHA` ya esta escrito.
                let hecha = REC_HECHA[n].load(Ordering::Acquire);
                (
                    REC_EN_CURSO[n].load(Ordering::Relaxed),
                    hecha && t0.wrapping_sub(REC_T_HECHA[n].load(Ordering::Relaxed)) >= gap,
                )
            } else {
                (false, false)
            };
        let s = t.transporte.avanza(
            Entrada {
                lectura,
                identidad: IDENTIDAD[n].load(Ordering::Relaxed),
                bajada,
                reinicio_en_curso: en_curso,
                reinicio_hecho: hecho,
                sucia,
                incidente: REC_INCIDENTE[n].load(Ordering::Relaxed),
            },
            periodos,
        );
        INCIDENTE[n].store(t.transporte.incidente(), Ordering::Relaxed);

        if s.cerrar {
            #[cfg(feature = "perfil")]
            let c0 = DWT::cycle_count();
            hw.cierra();
            #[cfg(feature = "perfil")]
            suma(5, DWT::cycle_count().wrapping_sub(c0));
            if s.eventos[0] == Some(Evento::GiroOk) {
                LARGO_SUBIDA[n].store(t.largo, Ordering::Relaxed);
                SUBIDA[n].publicar(t.rx_actual as usize);
                t.rx_actual ^= 1;
            }
        }
        if s.armar {
            if let Some(c) = bz.consumir() {
                let largo = (META[n][c].load(Ordering::Relaxed) & 0xFF) as u8;
                t.largo = largo;
                // Envenenada, el canal de transmision cuenta un byte menos que el `TSIZE`.
                #[cfg(feature = "inyeccion")]
                let envenenada = ENVENENAR[n].swap(false, Ordering::Relaxed);
                #[cfg(feature = "inyeccion")]
                let bndt_tx = u16::from(largo) - u16::from(envenenada);
                #[cfg(feature = "inyeccion")]
                if ENVENENAR_DMA[n].swap(false, Ordering::Relaxed) {
                    // El canal esta parado (EN = 0), asi que `TR1` se puede escribir.
                    hw.rx.ch.tr1().modify(|w| w.set_sdw(dma::Dw::Word));
                }
                #[cfg(not(feature = "inyeccion"))]
                let bndt_tx = u16::from(largo);
                #[cfg(feature = "perfil")]
                let r0 = DWT::cycle_count();
                hw.arma(
                    u16::from(largo),
                    bndt_tx,
                    ptr_bajada(n, c) as u32,
                    ptr_subida(n, t.rx_actual as usize) as u32,
                );
                #[cfg(feature = "perfil")]
                suma(6, DWT::cycle_count().wrapping_sub(r0));
                #[cfg(feature = "inyeccion")]
                if n == 0 {
                    let ahora = DWT::cycle_count();
                    if envenenada {
                        marca(Marca::CstartVeneno, ahora);
                    } else if MARCAS[Marca::RecHecha as usize].load(Ordering::Relaxed) != 0
                        && MARCAS[Marca::CstartSiguiente as usize].load(Ordering::Relaxed) == 0
                    {
                        marca(Marca::CstartSiguiente, ahora);
                    }
                }
                SELLOS[n].fetch_add(1, Ordering::Relaxed);
            }
        }
        for e in s.eventos.into_iter().flatten() {
            ANILLO[n].empujar(e);
            #[cfg(feature = "inyeccion")]
            if n == 0 && e == Evento::PlazoVencido {
                marca(Marca::Vencida, t0);
                acapara::si_toca_en_vencida();
            }
        }
        match s.aviso {
            Some(Aviso::SinBajada) => {
                CONT[n].sin_bajada.fetch_add(1, Ordering::Relaxed);
            }
            Some(Aviso::ErrorDma) => {
                CONT[n].errores_dma.fetch_add(1, Ordering::Relaxed);
            }
            Some(Aviso::RanuraMuerta) => {
                MUERTA[n].store(true, Ordering::Relaxed);
                CONT[n].muertas.fetch_add(1, Ordering::Relaxed);
            }
            None => {}
        }
        // El apreton de manos termina cuando la ranura sale de la recuperacion.
        let fuera = |e: Estado| matches!(e, Estado::Vencida { .. } | Estado::Reiniciando { .. });
        if fuera(antes) && !fuera(t.transporte.estado()) {
            REC_HECHA[n].store(false, Ordering::Relaxed);
            REC_EN_CURSO[n].store(false, Ordering::Relaxed);
        }
    }
    NVIC::pend(IRQ_PLAN);
    let dur = DWT::cycle_count().wrapping_sub(t0);
    suma(0, dur);
    #[cfg(feature = "perfil")]
    TIC_MAX.fetch_max(dur, Ordering::Relaxed);
}

// ---------------------------------------------------------------------------------------
// El planificador (nivel 3)
// ---------------------------------------------------------------------------------------

/// La trama siguiente: si el buzon no tiene una fresca, la compone en un bufer local
/// (cacheable) y la copia a la casilla de escritura con `stm`.
fn compone(n: usize, p: &mut PlanRanura) {
    if BUZON[n].fresca().is_some() {
        return;
    }
    #[cfg(feature = "perfil")]
    let t0 = DWT::cycle_count();
    let tsize = (p.bajada_fn)(n, &mut p.local_bajada.0);
    let largo = tsize.get() as usize;
    defmt::assert!(largo <= LARGO_MAX, "j2_tic: TSIZE no cabe en los buferes");
    let plazo = tics_de_plazo(
        plazo_us(tsize, p.f_sck_hz, &p.umbrales),
        PERIODO_US.load(Ordering::Relaxed),
    );
    let c = BUZON[n].casilla_escritura();
    // SAFETY: la casilla `c` es del escritor (`Triple`), y el bufer local tiene 128 bytes.
    unsafe {
        copia_bloques(
            ptr_bajada(n, c) as *mut u32,
            p.local_bajada.0.as_ptr() as *const u32,
            bloques(largo),
        );
    }
    META[n][c].store((u16::from(plazo) << 8) | largo as u16, Ordering::Relaxed);
    // Los stores a la region tienen que estar en el bus antes de publicar la casilla.
    cortex_m::asm::dsb();
    BUZON[n].publicar();
    #[cfg(feature = "perfil")]
    suma(3, DWT::cycle_count().wrapping_sub(t0));
}

#[interrupt]
unsafe fn DMA2D() {
    #[cfg(feature = "contaminador-icache")]
    crate::perfil::invalida_icache();
    let t0 = DWT::cycle_count();
    #[cfg(feature = "perfil")]
    let tic0 = CICLOS[0].load(Ordering::Relaxed);
    // SAFETY: el planificador es el unico que toca `RELOJ_PLAN`.
    let tics = unsafe { &mut *RELOJ_PLAN.0.get() }.extiende(TICS.load(Ordering::Relaxed));
    let ahora_us = tics * u64::from(PERIODO_US.load(Ordering::Relaxed));
    for n in 0..N {
        // SAFETY: el planificador es el unico que toca `PLAN`.
        let Some(p) = (unsafe { &mut *PLAN[n].0.get() }).as_mut() else {
            continue;
        };
        let mut hubo = false;
        while let Some(ev) = ANILLO[n].sacar() {
            hubo = true;
            match ev {
                Evento::GiroOk => {
                    let _ = p.politica.paso(Evento::GiroOk, ahora_us);
                    let mut largo = 0usize;
                    let lectura = SUBIDA[n].leer(|c| {
                        largo = LARGO_SUBIDA[n].load(Ordering::Relaxed) as usize;
                        // SAFETY: la casilla `c` es de la region y el local tiene 128 bytes.
                        unsafe {
                            copia_bloques(
                                p.local_subida.0.as_mut_ptr() as *mut u32,
                                ptr_subida(n, c) as *const u32,
                                bloques(largo),
                            );
                        }
                    });
                    if let LecturaSubida::Nueva(_) = lectura {
                        let ev = if (p.juez)(n, &p.local_subida.0[..largo]) {
                            Evento::SubidaOk
                        } else {
                            Evento::SubidaMala
                        };
                        let _ = p.politica.paso(ev, ahora_us);
                    }
                }
                Evento::PlazoVencido | Evento::PlazoAjeno => {
                    // La politica es la unica autoridad sobre «reiniciar» (papel v2, §2.5); un
                    // plazo ajeno pide la limpieza sin puntuar (papel v3, §2.5).
                    if p.politica.paso(ev, ahora_us) == Accion::Reiniciar
                        && !MUERTA[n].load(Ordering::Relaxed)
                    {
                        #[cfg(feature = "inyeccion")]
                        if SIN_RECUPERACION.load(Ordering::Relaxed) {
                            continue;
                        }
                        REC_INCIDENTE_PEDIDO[n]
                            .store(INCIDENTE[n].load(Ordering::Relaxed), Ordering::Relaxed);
                        REC_PEDIDA[n].store(true, Ordering::Relaxed);
                        NVIC::pend(IRQ_REC);
                    }
                }
                otro => {
                    let _ = p.politica.paso(otro, ahora_us);
                }
            }
        }
        if !hubo {
            let _ = p.politica.paso(Evento::Tick, ahora_us);
        }
        compone(n, p);
        publicar_cuentas(n, &p.politica, 0);
    }
    #[cfg(feature = "perfil")]
    {
        // Lo que gasto el planificador sin el tic que lo haya interrumpido.
        let bruto = DWT::cycle_count().wrapping_sub(t0);
        let tic = CICLOS[0].load(Ordering::Relaxed).wrapping_sub(tic0);
        suma(1, bruto.wrapping_sub(tic));
    }
    #[cfg(not(feature = "perfil"))]
    let _ = t0;
}

// ---------------------------------------------------------------------------------------
// La recuperacion (nivel 4)
// ---------------------------------------------------------------------------------------

/// Papel v2, §2.5 paso 1: `SUSP` a los dos canales, sondear `SUSPF` (o `IDLEF`, si el
/// canal ya estaba parado) hasta `T_CANAL`, y `RESET`. `false` si algun canal no paro.
fn para_canales(hw: &Hw) -> bool {
    hw.tx.ch.cr().modify(|w| w.set_susp(true));
    hw.rx.ch.cr().modify(|w| w.set_susp(true));
    let limite = T_CANAL_CICLOS.load(Ordering::Relaxed);
    let inicio = DWT::cycle_count();
    #[cfg(feature = "inyeccion")]
    if FORZAR_ESCALADA.swap(false, Ordering::Relaxed) {
        return false;
    }
    let paradas = || {
        let tx = hw.tx.ch.sr().read();
        let rx = hw.rx.ch.sr().read();
        (tx.suspf() || tx.idlef()) && (rx.suspf() || rx.idlef())
    };
    loop {
        if paradas() {
            break;
        }
        if DWT::cycle_count().wrapping_sub(inicio) >= limite {
            // Una interrupcion pudo caer entre la lectura y esta comparacion y comerse el plazo
            // entero: los canales pudieron parar mientras tanto. Se mira una vez mas antes de
            // rendirse, que rendirse es resetear el GPDMA1 de las seis ranuras (revision de
            // Halberg del 17-10, hallazgo 6).
            if paradas() {
                break;
            }
            return false;
        }
    }
    hw.tx.ch.cr().write(|w| w.set_reset(true));
    hw.rx.ch.cr().write(|w| w.set_reset(true));
    true
}

/// Papel v2, §2.5, escalada: el GPDMA1 entero se resetea por RCC **en una sola seccion
/// critica**, y dentro de ella se marcan las ranuras sucias y se declaran vencidas las que
/// estaban en vuelo, de modo que el tic no pueda ver el controlador reseteado sin la marca.
/// Despues se reprograman los canales de todas las ranuras activas y se limpian.
fn escala() {
    ESCALADAS_GPDMA.fetch_add(1, Ordering::Relaxed);
    #[cfg(feature = "inyeccion")]
    marca(Marca::EscalaIni, DWT::cycle_count());
    cortex_m::interrupt::free(|_| {
        #[cfg(feature = "inyeccion")]
        marca(Marca::SeccionIni, DWT::cycle_count());
        crate::j2_spi::resetear_por_rcc::<peripherals::GPDMA1>();
        for k in 0..N {
            // SAFETY: con las interrupciones enmascaradas el tic no corre.
            if unsafe { &*HW[k].0.get() }.is_none() {
                continue;
            }
            SUCIA[k].store(true, Ordering::Relaxed);
            let t = unsafe { &mut *TIC[k].0.get() };
            if let Some(ev) = t.transporte.declarar_vencida() {
                INCIDENTE[k].store(t.transporte.incidente(), Ordering::Relaxed);
                ANILLO[k].empujar(ev);
            }
        }
        #[cfg(feature = "inyeccion")]
        marca(Marca::SeccionFin, DWT::cycle_count());
    });
    for k in 0..N {
        if let Some(hw) = unsafe { &*HW[k].0.get() }.as_ref() {
            hw.tx.programa();
            hw.rx.programa();
            SUCIA[k].store(false, Ordering::Relaxed);
        }
    }
    NVIC::pend(IRQ_PLAN);
}

fn recupera(n: usize) {
    // SAFETY: solo se lee; los campos de `Hw` no cambian despues de `lanzar`.
    let Some(hw) = (unsafe { &*HW[n].0.get() }).as_ref() else {
        return;
    };
    if MUERTA[n].load(Ordering::Relaxed) {
        // La pidio viva y murio antes de que la recuperacion corriera.
        return;
    }
    REC_INCIDENTE[n].store(
        REC_INCIDENTE_PEDIDO[n].load(Ordering::Relaxed),
        Ordering::Relaxed,
    );
    REC_EN_CURSO[n].store(true, Ordering::Relaxed);
    #[cfg(feature = "inyeccion")]
    if n == 0 {
        marca(Marca::RecInicio, DWT::cycle_count());
    }
    if !para_canales(hw) {
        // SAFETY: la recuperacion es la unica que toca `RELOJ_REC` y `PRESUPUESTO`.
        let tics = unsafe { &mut *RELOJ_REC.0.get() }.extiende(TICS.load(Ordering::Relaxed));
        let ahora_us = tics * u64::from(PERIODO_US.load(Ordering::Relaxed));
        if unsafe { &mut *PRESUPUESTO.0.get() }.pide(ahora_us) {
            escala();
        } else {
            // K1: sin presupuesto, el RESET por canal y nada mas: ni HECHA ni reintento. La
            // ranura muere por la cota de `Reiniciando` y el supervisor reinicia el chip.
            hw.tx.ch.cr().write(|w| w.set_reset(true));
            hw.rx.ch.cr().write(|w| w.set_reset(true));
            ESCALADAS_DENEGADAS.fetch_add(1, Ordering::Relaxed);
            return;
        }
    }
    // Pasos 2 y 3 en una sola seccion critica: el reset del SPI deja `CFG2 = 0`, con
    // `AFCNTR = 0` el `CS` y el reloj flotan, y cuanto menos dure, mejor.
    #[cfg(feature = "inyeccion")]
    if n == 0 {
        marca(Marca::ResetIni, DWT::cycle_count());
    }
    cortex_m::interrupt::free(|_| {
        (hw.resetear)();
        hw.regs.cfg2().write_value(hw.cfg2);
        hw.regs.cfg1().write_value(hw.cfg1);
    });
    #[cfg(feature = "inyeccion")]
    if n == 0 {
        marca(Marca::ResetFin, DWT::cycle_count());
    }
    // Paso 4: los dos canales por completo.
    hw.tx.programa();
    hw.rx.programa();
    // Paso 5: publicar `ReinicioHecho` con su marca de tiempo. El tic devuelve la ranura
    // a `Libre` solo cuando han pasado `T_GAP_REARME`. Los registros de arriba tienen que haber
    // salido antes: ni el compilador ni el bus pueden dejarlos detras de `HECHA` (revision de
    // Halberg del 17-10, hallazgo 8b).
    cortex_m::asm::dsb();
    core::sync::atomic::compiler_fence(Ordering::SeqCst);
    let hecha = DWT::cycle_count();
    #[cfg(feature = "inyeccion")]
    if n == 0 {
        marca(Marca::RecHecha, hecha);
    }
    REC_T_HECHA[n].store(hecha, Ordering::Relaxed);
    REC_HECHA[n].store(true, Ordering::Release);
    // Paso 6: contar.
    CONT[n].recuperaciones.fetch_add(1, Ordering::Relaxed);
}

#[interrupt]
unsafe fn JPEG() {
    let t0 = DWT::cycle_count();
    #[cfg(feature = "perfil")]
    let (tic0, plan0) = (
        CICLOS[0].load(Ordering::Relaxed),
        CICLOS[1].load(Ordering::Relaxed),
    );
    for (n, pedida) in REC_PEDIDA.iter().enumerate() {
        if pedida.swap(false, Ordering::Relaxed) {
            recupera(n);
        }
    }
    #[cfg(feature = "perfil")]
    {
        let bruto = DWT::cycle_count().wrapping_sub(t0);
        let otros = CICLOS[0]
            .load(Ordering::Relaxed)
            .wrapping_sub(tic0)
            .wrapping_add(CICLOS[1].load(Ordering::Relaxed).wrapping_sub(plan0));
        suma(2, bruto.wrapping_sub(otros));
    }
    #[cfg(not(feature = "perfil"))]
    let _ = t0;
}

/// Una interrupcion que acapara la CPU un rato, para los binarios de estres: `VENC`, que ningun otro
/// modulo atiende, con la prioridad que se le pida. A P2 es un USB o una pantalla que retiene al
/// planificador (P3) y a la recuperacion (P4); a P3, trabajo del planificador que no pega al
/// resto del banco (el esclavo del banco es una tarea de P2).
#[cfg(feature = "inyeccion")]
pub mod acapara {
    use core::sync::atomic::{AtomicU32, Ordering};

    use cortex_m::peripheral::{DWT, NVIC};
    use embassy_stm32::interrupt;
    use embassy_stm32::interrupt::{InterruptExt, Priority};

    static CICLOS: AtomicU32 = AtomicU32::new(0);
    static EN_VENCIDA: AtomicU32 = AtomicU32::new(0);

    #[interrupt]
    unsafe fn VENC() {
        let t0 = DWT::cycle_count();
        let n = CICLOS.load(Ordering::Relaxed);
        while DWT::cycle_count().wrapping_sub(t0) < n {}
    }

    /// Pone la prioridad y desenmascara la linea. Una vez, despues de `lanzar`.
    pub fn arranca(prioridad: Priority) {
        interrupt::VENC.set_priority(prioridad);
        // SAFETY: el vector `VENC` es la ISR de arriba.
        unsafe { interrupt::VENC.enable() };
    }

    /// Hace pendiente un golpe de `us` microsegundos.
    pub fn golpe(us: u32) {
        CICLOS.store(
            us * super::CICLOS_POR_US.load(Ordering::Relaxed),
            Ordering::Relaxed,
        );
        NVIC::pend(interrupt::VENC);
    }

    /// El proximo `PlazoVencido` de la ranura 0 hace pendiente un golpe de `us` microsegundos,
    /// en el mismo instante en que el tic lo emite: el planificador queda retenido justo cuando
    /// tiene que pedir la recuperacion. Con 0 se apaga.
    pub fn en_vencida(us: u32) {
        EN_VENCIDA.store(
            us * super::CICLOS_POR_US.load(Ordering::Relaxed),
            Ordering::Relaxed,
        );
    }

    pub(super) fn si_toca_en_vencida() {
        let c = EN_VENCIDA.swap(0, Ordering::Relaxed);
        if c != 0 {
            CICLOS.store(c, Ordering::Relaxed);
            NVIC::pend(interrupt::VENC);
        }
    }
}
