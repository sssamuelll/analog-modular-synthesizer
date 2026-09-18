//! El driver del J2 del lado del maestro: `TSIZE`, NSS por hardware y las dos
//! esperas cancelables.
//!
//! Existe porque el SPI de embassy **no cancela**. Su `finish_dma` espera
//! `EOT` en un bucle sincrono (`spi/mod.rs:1804-1808`, `while
//! !regs.sr().read().eot() {}`) que ningun `with_timeout` de fuera puede
//! vencer, y el `join` de los dos futuros del DMA (`:1499`) no esta bajo
//! ningun plazo. Con el defecto del N6 abierto (embassy-rs/embassy#5607) eso
//! no es un detalle: cuando el periferico se cuelga se congela la tarea y todo
//! lo que comparta ejecutor con ella, y el instrumento se queda callado en
//! mitad de un concierto. Spec: `docs/superpowers/specs/`
//! `2026-09-03-maestro-j2-recuperacion-design.md`, sec.1.2.
//!
//! Lo que el driver hace y embassy no hace (D1-D4):
//!
//! - `TSIZE = N` y NSS por hardware en cada transferencia (D1), con `CRCEN =
//!   0`: el CRC es el del sobre, no el del periferico;
//! - las DOS esperas (los dos DMA y el `EOT` por `EOTIE`) bajo UN solo plazo
//!   (D2, D3), con el orden de arranque enmendado el 11-09 -- la espera de al
//!   menos un `T_SCK` anclada entre `SPE = 1` y `CSTART`;
//! - los ocho pasos del reinicio de D4, en orden, con su pagina del RM0486, y
//!   `soltar_canales` con cota `T_CANAL` (enmienda del 18-09, #368);
//! - ningun bucle sincrono sin cota (R-MJ2), y nunca una escritura a `TXDR`
//!   para desatascar (R-MJ3).
//!
//! **No sabe nada del sobre** (D8): recibe un bufer de bajada, uno de subida y
//! un largo, y devuelve `Ok` o `PlazoVencido`. `fw` cloca bytes; `core` sabe
//! que son. Si la semantica del sobre aparece aqui, es un defecto.
//!
//! **Que protege la generacion de D2, dicho sin adornos:** protege que la tarea
//! no consuma un resultado que quedo guardado de un giro anterior (regla 2,
//! `armar` borra). **No** puede protegerte de un `EOT` viejo bajo una
//! generacion nueva, porque el hardware no etiqueta el `EOT` y la ISR solo
//! puede leer la generacion armada en ese instante. De eso se encargan dos
//! cosas temporales: `EOTIE` armado solo entre `CSTART` y la ISR, y el
//! `NVIC::unpend` de D4 (pasos 1 y 7). Detalle en el doc de [`Isr`].
//!
//! `bind_interrupts!` **no** vive aqui: lo pone quien arma la placa (tareas 8 y
//! 10), atando `SPI5 => Isr<0>` y los dos canales del GPDMA a
//! `embassy_stm32::dma::InterruptHandler`.
//!
//! **Los dos HUECOS que este archivo arrastra, dichos aqui para que no haya que
//! encontrarlos leyendo:**
//!
//! 1. **`CPOL`/`CPHA` quedan en 0 (modo 0), que es el valor de reset.** Ningun
//!    papel del J2 decide el modo del enlace. El dia que la cabecera o el punto
//!    a punto lo fijen, se escribe en el `CFG2` de `nueva`.
//! 2. **El reloj de la CPU no sale de `Clocks`.** El `set_clocks!` del N6
//!    publica `sys` y no `cpuclk` (`rcc/n6.rs:1392`), y `asm::delay` cuenta
//!    ciclos del nucleo. Mientras tanto lo pone el llamador en
//!    `Config::f_cpu_hz` (lo calcula `usb::f_cpu_hz` de la misma `Config` del
//!    reloj, y **cuelga** si la CPU deja de correr por HSI), y `nueva` asevera
//!    `f_cpu_hz >= sys`. Se cierra cuando embassy publique `cpuclk` (#376).
//!
//! Ojo con el nombre: el plan dice `spi_v4`; el cfg que embassy pone para el
//! N657 es `spi_v5` (su `build.rs`, de `STM32N657X0.json`: `spi` version
//! `v5`), y el driver de embassy trata `spi_v4`, `spi_v5` y `spi_v6` juntos.
//! Los registros son los del cap. 67 del RM0486 Rev 4 igual.

use core::future::Future;
use core::mem::ManuallyDrop;
use core::pin::Pin;
use core::sync::atomic::{AtomicU32, Ordering};
use core::task::{Context, Poll};

use cortex_m::peripheral::NVIC;
use embassy_futures::join::join;
use embassy_stm32::dma::{self, Transfer, TransferOptions};
use embassy_stm32::gpio::{AfType, Flex, OutputType, Pull, Speed};
use embassy_stm32::interrupt::typelevel::{Binding, Handler, Interrupt};
use embassy_stm32::pac::spi::vals::{Master, Mbr, Ssom};
use embassy_stm32::{gpio, interrupt, pac, peripherals, rcc, spi, Peri};
use embassy_sync::waitqueue::AtomicWaker;
use embassy_time::{with_timeout, Duration, Instant};
use sam17_nucleo_core::maestro_j2::{
    ciclos_por_cuarto_tsck, mbr_y_f_sck, Banderas, Tsize, Turno, RANURAS_SPI,
};

/// Las ranuras del J2 por SPI. El numero no se copia: es el de la politica.
pub const RANURAS: usize = RANURAS_SPI;

/// El mensaje mas largo que el driver acepta clocar, en bytes.
///
/// El `SET` de 16 son 103 bytes clocados (cabecera sec.4; spec D3: 82,4 us al
/// piso de 10 MHz). 128 lo cubre con margen y es potencia de dos.
pub const LARGO_MAX: usize = 128;

/// Cota del sondeo de `SUSP` en el paso 3 de D4, en microsegundos.
/// **ESTIMADO** (D4.3): no hay cifra en el manual; la sella el bring-up.
pub const T_SUSP_US: u64 = 10;

/// Cota del sondeo de `is_running()` al soltar los canales del GPDMA, en
/// microsegundos. **ESTIMADO** (D4.2, enmienda del 18-09, #368), de la misma
/// clase que `T_SUSP`: RM0486 Rev 4, sec.19.4.3 p. 942 y sec.19.4.4 p. 943
/// -- la suspension y el reset de un canal solo se completan al terminar la
/// rafaga en curso (*"Wait for the channel to be effectively in suspended
/// state means wait for the completion of any ongoing GPDMA transfer over its
/// master port"*), y esa rafaga es de bytes, no de bloques.
pub const T_CANAL_US: u64 = 10;

/// Cuantas veces D4.2 tuvo que escalar al reset del GPDMA1 por RCC porque un
/// canal no paro dentro de `T_CANAL`. Vive en `fw`, no en la politica.
pub static ESCALADAS_GPDMA: AtomicU32 = AtomicU32::new(0);

/// Lo que comparten la ISR de una ranura y su tarea (D2, reglas 1-3).
pub struct EstadoRanura {
    /// La generacion y el resultado guardado. La ISR `registra`, la tarea
    /// `arma` y `toma`.
    pub turno: Turno,
    /// A quien despertar cuando llegue el `EOT`.
    pub waker: AtomicWaker,
}

impl EstadoRanura {
    const fn nuevo() -> Self {
        Self {
            turno: Turno::nuevo(),
            waker: AtomicWaker::new(),
        }
    }
}

/// Uno por ranura, en `static`: la ISR no tiene otra forma de alcanzarlo.
pub static ESTADOS: [EstadoRanura; RANURAS] = [const { EstadoRanura::nuevo() }; RANURAS];

/// Que SPI atiende cada ranura. HUECO: el reparto definitivo lo trae el
/// esquematico del hub (`pinout.rs` es propuesta). El banco usa la ranura 0 en
/// SPI5, la instancia del repro de jake-taf (EN-PLACA, montaje del 11-09).
pub const SPI_DE_RANURA: [pac::spi::Spi; RANURAS] = [
    pac::SPI5,
    pac::SPI4,
    pac::SPI1,
    pac::SPI2,
    pac::SPI3,
    pac::SPI6,
];

/// La interrupcion de cada ranura, en paralelo a `SPI_DE_RANURA`. La necesita
/// D4 paso 1: apagar `EOTIE` no borra una ISR que el NVIC ya tenia PENDIENTE,
/// y esa correria despues del reinicio sobre una ranura ya rearmada.
pub const IRQ_DE_RANURA: [interrupt::Interrupt; RANURAS] = [
    interrupt::SPI5,
    interrupt::SPI4,
    interrupt::SPI1,
    interrupt::SPI2,
    interrupt::SPI3,
    interrupt::SPI6,
];

/// Los dieciseis canales del **GPDMA1**, y solo esos.
///
/// `spi::TxDma<SPI5>` lo implementan tambien los canales del HPDMA1
/// (`_generated.rs`: 16 impls de cada controlador para SPI5). Si una ranura se
/// armara con un canal del HPDMA1, la escalada de `soltar_canales` resetearia
/// el GPDMA1 -- el controlador **equivocado** -- y devolveria `Escalado`
/// creyendo que recupero. Esta marca lo vuelve un error de compilacion.
pub trait CanalGpdma1: dma::ChannelInstance {}

macro_rules! canales_gpdma1 {
    ($($ch:ident),* $(,)?) => {
        $( impl CanalGpdma1 for peripherals::$ch {} )*
    };
}

canales_gpdma1!(
    GPDMA1_CH0,
    GPDMA1_CH1,
    GPDMA1_CH2,
    GPDMA1_CH3,
    GPDMA1_CH4,
    GPDMA1_CH5,
    GPDMA1_CH6,
    GPDMA1_CH7,
    GPDMA1_CH8,
    GPDMA1_CH9,
    GPDMA1_CH10,
    GPDMA1_CH11,
    GPDMA1_CH12,
    GPDMA1_CH13,
    GPDMA1_CH14,
    GPDMA1_CH15,
);

/// Lo que devuelve un giro. Un `EOT` tardio no sale por aqui: lo cuenta
/// `Turno::armar` y `giro` lo devuelve como numero (D2, regla 1).
#[derive(Clone, Copy, PartialEq, Eq, Debug, defmt::Format)]
pub enum Resultado {
    /// Los dos DMA terminaron y llego `EOT` dentro del plazo.
    Ok,
    /// El plazo vencio antes: el periferico se reinicio (D4).
    PlazoVencido,
}

/// Como quedaron los dos canales del GPDMA al soltarlos (D4.2).
#[derive(Clone, Copy, PartialEq, Eq, Debug, defmt::Format)]
pub enum Soltado {
    /// Los dos pararon dentro de `T_CANAL` y su `Drop` entro y salio.
    Limpio,
    /// Uno no paro: se olvidaron los dos y se reseteo el GPDMA1 por RCC.
    Escalado,
}

/// Lo que se elige por enlace al construir la ranura.
#[derive(Clone, Copy)]
pub struct Config {
    /// El reloj sancionado del enlace (punto a punto D2, `sancion_j2.csv`).
    /// El `MBR` real se redondea hacia abajo y se imprime por `defmt`.
    pub f_sck_hz: u32,
    /// El reloj del **nucleo**, que es el que cuenta `cortex_m::asm::delay`.
    /// Lo pone el llamador porque el `Clocks` de embassy no publica `cpuclk`
    /// (HUECO 2 de la cabecera): en el cerebro sale de `usb::f_cpu_hz`, que lo
    /// calcula de la misma `Config` con la que se construye el reloj. `nueva`
    /// asevera que no es menor que el `sys` que embassy si publica.
    pub f_cpu_hz: u32,
    /// El retardo entre `SPE = 1` y `CSTART`, en cuartos de `T_SCK`
    /// (D2, enmienda del 11-09). Produccion = 4, o sea >= 1 `T_SCK`; el
    /// barrido del bring-up usa 0, 1, 2, 4, 8 y 16.
    pub retardo_tsck_cuartos: u8,
}

/// El maestro de una ranura: los registros, los dos canales del GPDMA, sus
/// numeros de peticion y los cuatro pines. Los `Flex` viven aqui porque su
/// `Drop` desconfigura el pin.
pub struct Ranura<'d> {
    indice: usize,
    regs: pac::spi::Spi,
    canal_tx: dma::Channel<'d>,
    canal_rx: dma::Channel<'d>,
    req_tx: dma::Request,
    req_rx: dma::Request,
    ciclos_por_cuarto_tsck: u32,
    retardo_cuartos: u8,
    _sck: Flex<'d>,
    _mosi: Flex<'d>,
    _miso: Flex<'d>,
    _nss: Flex<'d>,
}

impl<'d> Ranura<'d> {
    /// Configura los pines (AF5), el reloj del periferico, los `CFG1`/`CFG2`
    /// fijos de D1, y deja el SPI **apagado**, que es como esta siempre entre
    /// transferencias (D2).
    ///
    /// `T` es el tipo del periferico (`peripherals::SPI5`): de ahi salen el
    /// reset por RCC, el reloj de kernel para el `MBR` y los numeros de
    /// peticion del GPDMA. Los registros van aparte (`pac::SPI5`) porque el
    /// `Info` interno de embassy no es publico. Si el compilador no infiere
    /// `T`, se le da: `Ranura::nueva::<peripherals::SPI5, _, _, _, _, _, _>`.
    ///
    /// Los dos canales tienen que ser del **GPDMA1** (`CanalGpdma1`): la
    /// escalada de `soltar_canales` resetea ese controlador, y uno del HPDMA1
    /// dejaria el reinicio mudo. Es un error de compilacion, no un comentario.
    ///
    /// `rcc_peri` es `&p.RCC`: `rcc::clocks` (rcc/mod.rs:154) es la unica via
    /// publica al `Clocks` de embassy, y con el se asevera que el `f_cpu_hz`
    /// que trae la `Config` no es menor que el `sys`. Se usa aqui y no se
    /// guarda.
    #[allow(clippy::too_many_arguments)]
    pub fn nueva<T, Sck, Mosi, Miso, Nss, Tx, Rx>(
        indice: usize,
        regs: pac::spi::Spi,
        sck: Peri<'d, Sck>,
        mosi: Peri<'d, Mosi>,
        miso: Peri<'d, Miso>,
        nss: Peri<'d, Nss>,
        tx: Peri<'d, Tx>,
        rx: Peri<'d, Rx>,
        irq_tx: impl Binding<Tx::Interrupt, dma::InterruptHandler<Tx>> + 'd,
        irq_rx: impl Binding<Rx::Interrupt, dma::InterruptHandler<Rx>> + 'd,
        rcc_peri: &Peri<'_, peripherals::RCC>,
        cfg: Config,
    ) -> Ranura<'d>
    where
        T: spi::Instance,
        Sck: gpio::Pin,
        Mosi: gpio::Pin,
        Miso: gpio::Pin,
        Nss: gpio::Pin,
        Tx: CanalGpdma1 + spi::TxDma<T>,
        Rx: CanalGpdma1 + spi::RxDma<T>,
    {
        defmt::assert!(indice < RANURAS, "J2: ranura fuera de rango");
        // La ISR alcanza los registros por `SPI_DE_RANURA[R]` y `giro` por
        // `self.regs`. Si los dos no son el mismo bloque, la ISR limpiaria las
        // banderas de otro periferico y el `EOT` no llegaria nunca.
        defmt::assert!(
            regs == SPI_DE_RANURA[indice],
            "J2: los registros no son los de SPI_DE_RANURA[ranura]"
        );

        // R-MJ7: los buferes de DMA van en memoria no cacheable. Hoy la
        // D-cache del M55 esta apagada (embassy no la enciende) y esa es toda
        // la garantia; el dia que alguien la encienda hace falta la region MPU
        // (HUECO declarado). `SCB::dcache_enabled` lee `CCR.DC`, bit 16
        // (cortex-m 0.7.9, scb.rs:341 y :504).
        defmt::assert!(
            !cortex_m::peripheral::SCB::dcache_enabled(),
            "R-MJ7: la D-cache esta encendida y los buferes del J2 no estan en region MPU"
        );

        // Paso 0 de D4: el reloj y el reset del periferico.
        rcc::enable_and_reset::<T>();

        // Los cuatro pines a AF5. Los ocho del montaje son AF5:
        // `stm32-data-generated/data/chips/STM32N657X0.json` (verificado el
        // 18-09, y el `_generated.rs` de este build lo repite:
        // `pin_trait_impl!(spi::SckPin, SPI5, PE15, 5u8)`), y DS14791 Rev 10
        // Tabla 18. `VeryHigh` porque el enlace sube a 34,5 MHz (spec D8).
        let salida = AfType::output(OutputType::PushPull, Speed::VeryHigh);
        let mut sck = Flex::new(sck);
        let mut mosi = Flex::new(mosi);
        let mut miso = Flex::new(miso);
        let mut nss = Flex::new(nss);
        sck.set_as_af_unchecked(5, salida);
        mosi.set_as_af_unchecked(5, salida);
        nss.set_as_af_unchecked(5, salida);
        miso.set_as_af_unchecked(5, AfType::input(Pull::None));

        // CFG2, la configuracion fija de D1. `write` deja en cero todo lo que
        // no se nombra: `SSM = 0` (el NSS es del periferico), `COMM = 0` (full
        // duplex), `LSBFRST = 0`, `MIDI`/`MSSI = 0`, `IOSWP = 0`, y
        // `CPOL = CPHA = 0` (modo 0, el valor de reset; ningun papel decide
        // otro, HUECO de la cabecera).
        //
        // - `MASTER = 1`, `SSOE = 1`: sec.67.4.7, p. 3437 -- *"the master must
        //   apply the proper TSIZE > 0 setting to control the NSS output
        //   correctly"*.
        // - `SSOM = 0` (`Asserted`): sec.67.4.7, p. 3438 -- el NSS baja con
        //   `CSTART` y no sube hasta `EOT`.
        // - `AFCNTR = 1`: sec.67.4.10, p. 3444 (*"all the SPI outputs start to
        //   be propagated onto the associated GPIO pins regardless of the
        //   peripheral enable"*) y sec.67.4.13, p. 3450 -- con `AFCNTR = 1` y
        //   `SPE = 0`, NSS y SCK se van a su nivel inactivo en vez de quedar
        //   sueltos. El SPI vive apagado entre transferencias (D2), asi que
        //   ese es el estado normal del cable.
        regs.cfg2().write(|w| {
            w.set_master(Master::Master);
            w.set_ssm(false);
            w.set_ssoe(true);
            w.set_ssom(Ssom::Asserted);
            w.set_afcntr(true);
        });

        // MBR: la cuenta vive en `core` y esta probada en el host (R14). Aqui
        // solo se asevera el contrato de su frontera: si ni `/256` baja del
        // sancionado, `mbr_y_f_sck` devuelve `/256` y el que asevera es este
        // llamador. No se supone que salga exacto, asi que se imprime.
        let f_ker = rcc::frequency::<T>().0;
        let (mbr, f_sck) = mbr_y_f_sck(f_ker, cfg.f_sck_hz);
        let divisor = 1u32 << (mbr + 1);
        defmt::assert!(
            f_sck > 0 && f_sck <= cfg.f_sck_hz,
            "J2: el reloj de kernel no da un f_sck util dentro del sancionado"
        );

        // CFG1: `DSIZE = 7` son 8 bits (el campo es largo-1, sec.67.4.9
        // p. 3443: *"The data frame size is configured through the DSIZE
        // bitfield"*). `CRCEN = 0` explicito: el CRC es el del sobre
        // (cabecera D2), y el del periferico viajaria como trama aparte
        // despues de los `TSIZE` datos (sec.67.5.3, p. 3456). Los dos
        // `DMAEN` quedan en cero: los enciende `giro` en su sitio del orden.
        regs.cfg1().write(|w| {
            w.set_dsize(7);
            w.set_mbr(Mbr::from_bits(mbr));
            w.set_crcen(false);
            w.set_txdmaen(false);
            w.set_rxdmaen(false);
        });

        // Los ciclos de CPU de un cuarto de `T_SCK` (D2, enmienda del 11-09:
        // la espera va en ciclos, no con `embassy_time`, cuyo grano de 1 us es
        // diez veces el ciclo de SCK). La cuenta esta en `core`, probada en el
        // host (R14).
        //
        // `f_cpu` lo trae la `Config` porque `Clocks` no publica `cpuclk`
        // (HUECO 2 de la cabecera). Lo unico que se puede comprobar contra
        // embassy es que no sea MENOR que el `sys`: en el N6 el nucleo cuelga
        // de IC1 y el bus de IC2, y el nucleo nunca va por debajo del bus. Si
        // esta asercion salta, el llamador puso el reloj del bus donde va el
        // del nucleo, y el retardo saldria corto en silencio.
        let f_sys = defmt::unwrap!(rcc::clocks(rcc_peri).sys.to_hertz()).0;
        let f_cpu = cfg.f_cpu_hz;
        defmt::assert!(
            f_cpu >= f_sys,
            "J2: Config.f_cpu_hz ({} Hz) es menor que el sysclk ({} Hz); no es el reloj del nucleo",
            f_cpu,
            f_sys
        );
        let ciclos_cuarto = ciclos_por_cuarto_tsck(f_cpu, f_sck);

        let req_tx = tx.request();
        let req_rx = rx.request();
        let canal_tx = dma::Channel::new(tx, irq_tx);
        let canal_rx = dma::Channel::new(rx, irq_rx);

        // Apagado al salir: `SPE = 0` es el estado entre transferencias
        // (sec.67.4.12, p. 3448 y sec.67.11.6, p. 3492), y `TSIZE` solo se
        // puede escribir asi (sec.67.11.1, p. 3484).
        regs.cr1().modify(|w| w.set_spe(false));

        defmt::info!(
            "J2 ranura {}: f_ker {} Hz, MBR /{}, f_sck {} Hz (pedido {}), \
             f_cpu {} Hz, {} ciclos por cuarto de T_SCK, retardo {} cuartos",
            indice,
            f_ker,
            divisor,
            f_sck,
            cfg.f_sck_hz,
            f_cpu,
            ciclos_cuarto,
            cfg.retardo_tsck_cuartos
        );

        Ranura {
            indice,
            regs,
            canal_tx,
            canal_rx,
            req_tx,
            req_rx,
            ciclos_por_cuarto_tsck: ciclos_cuarto,
            retardo_cuartos: cfg.retardo_tsck_cuartos,
            _sck: sck,
            _mosi: mosi,
            _miso: miso,
            _nss: nss,
        }
    }

    /// Una transferencia entera: el orden de arranque de D2 (enmendado el
    /// 11-09) y las DOS esperas bajo UN plazo (D2, D3). Devuelve el resultado
    /// y cuantos `EOT` tardios descarto el armado (D2, regla 1).
    pub async fn giro(
        &mut self,
        bajada: &[u8],
        subida: &mut [u8],
        tsize: Tsize,
        plazo: Duration,
    ) -> (Resultado, u32) {
        let n = tsize.get() as usize;
        defmt::assert!(
            n <= bajada.len() && n <= subida.len() && n <= LARGO_MAX,
            "J2: TSIZE no cabe en los buferes"
        );
        let estado = &ESTADOS[self.indice];
        let regs = self.regs;
        let txdr = regs.txdr32().as_ptr() as *mut u8;
        let rxdr = regs.rxdr32().as_ptr() as *mut u8;

        // D2, reglas 1 y 2: generacion nueva y resultado guardado a cero,
        // antes de habilitar nada.
        let (_generacion, tardios) = estado.turno.armar();

        // sec.67.11.1, p. 3484: `CR2` esta protegido con el SPI encendido.
        regs.cr1().modify(|w| w.set_spe(false));
        // D1: `TSIZE` son los bytes clocados de la trama. Nunca cero (R-MJ1,
        // y `Tsize` es un `NonZeroU16`). sec.67.4.7, p. 3437.
        regs.cr2().write(|w| w.set_tsize(tsize.get()));
        // Los cuatro pasos de arranque del DMA, sec.67.4.14, p. 3451.
        // 1. `RXDMAEN`.
        regs.cfg1().modify(|w| w.set_rxdmaen(true));
        // 2. Los dos canales armados. Bajo `ManuallyDrop` porque el `Drop` de
        //    embassy (gpdma/mod.rs:1287) gira sin cota: quien los suelte lo
        //    hace cuando sabe que el canal esta parado (R-MJ2).
        let mut rx = ManuallyDrop::new(unsafe {
            self.canal_rx.read(
                self.req_rx,
                rxdr,
                &mut subida[..n],
                TransferOptions::default(),
            )
        });
        let mut tx = ManuallyDrop::new(unsafe {
            self.canal_tx
                .write(self.req_tx, &bajada[..n], txdr, TransferOptions::default())
        });
        // 3. `TXDMAEN`.
        regs.cfg1().modify(|w| w.set_txdmaen(true));
        // 4. `SPE = 1`.
        regs.cr1().modify(|w| w.set_spe(true));
        // El anclaje de la enmienda del 11-09: una escritura a memoria Device
        // puede quedar en vuelo; una lectura vuelve cuando el periferico
        // contesto, y el retardo se cuenta desde ahi.
        let _ = regs.cr1().read();
        // >= 1 `T_SCK` antes de `CSTART`, en ciclos de CPU. ES0396 Rev 9
        // sec.2.14.2 (H750/H753, `spi_v4`) por analogia: *"wait for at least
        // one SCK cycle before setting CSTART"*. ES0620 Rev 5 no lista ningun
        // item del SPI del N657; la enmienda entra por analogia y asi queda
        // marcada hasta que la placa la mida.
        cortex_m::asm::delay(self.ciclos_por_cuarto_tsck * u32::from(self.retardo_cuartos));
        // `EOTC` va aqui a proposito (D2): sec.67.11.6, p. 3492 dice que `EOT`
        // se pone al rehabilitar el SPI, y p. 3490 que las banderas no se
        // limpian solas al rehabilitarlo. Limpiar despues de `SPE = 1` y antes
        // de `EOTIE = 1` hace que de igual cual de las dos frases sea la buena.
        regs.ifcr().write(|w| w.set_eotc(true));
        // sec.67.11.5, p. 3490: *"EOTIE: EOT, SUSP and TXC interrupt enable"*.
        regs.ier().modify(|w| w.set_eotie(true));
        // sec.67.4.7, p. 3438: el NSS baja en cuanto `CSTART = 1`.
        regs.cr1().modify(|w| w.set_cstart(true));

        // D2: el plazo abraza las dos esperas. Si la recepcion no termina
        // nunca (el modo del #5607) vence en el `join`; si el DMA termino y el
        // periferico no marca `EOT`, vence en el futuro de la ISR.
        let esperas = async {
            join(&mut *tx, &mut *rx).await;
            EsperaEot { estado }.await
        };
        match with_timeout(plazo, esperas).await {
            Ok(_banderas) => {
                // Los dos futuros del DMA resolvieron, y solo resuelven con
                // `is_running() == false` (gpdma/mod.rs:1298-1313): el `Drop`
                // de embassy entra y sale.
                unsafe {
                    ManuallyDrop::drop(&mut tx);
                    ManuallyDrop::drop(&mut rx);
                }
                // Cierre ordenado: apagar (p. 3448, p. 3492) y solo entonces
                // los dos `DMAEN` (paso 3 del cierre, p. 3451; `CFG1` esta
                // protegido con `SPE = 1`, p. 3484).
                regs.cr1().modify(|w| w.set_spe(false));
                regs.cfg1().modify(|w| {
                    w.set_txdmaen(false);
                    w.set_rxdmaen(false);
                });
                (Resultado::Ok, tardios)
            }
            Err(_) => {
                Self::reiniciar(self.indice, regs, tx, rx);
                (Resultado::PlazoVencido, tardios)
            }
        }
    }

    /// Los ocho pasos de D4, en ese orden, cada uno con su pagina (R-MJ3).
    /// Termina con el SPI **apagado y limpio**, que es como esta entre
    /// transferencias (D2). **Nunca** escribe a `TXDR`.
    ///
    /// No toma `&mut self` (el brief lo dibujaba asi) porque los dos
    /// `Transfer` que recibe ya tienen prestados `self.canal_tx` y
    /// `self.canal_rx`; lo unico que necesita de la `Ranura` son los
    /// registros, que son `Copy`.
    fn reiniciar(
        indice: usize,
        regs: pac::spi::Spi,
        tx: ManuallyDrop<Transfer<'_>>,
        rx: ManuallyDrop<Transfer<'_>>,
    ) {
        // 1. Silenciar la ISR. Sin esto el `CSUSP` del paso 3 produce `SUSP`,
        //    `SUSP` dispara la ISR (`EOTIE` la cubre, sec.67.11.5, p. 3490) y
        //    la ISR limpia `SUSPC` antes de que el paso 3 lo vea.
        //
        //    Apagar `EOTIE` no basta: una ISR que el NVIC ya tenia PENDIENTE
        //    cuando llegamos aqui corre igual, y correria DESPUES del reinicio,
        //    sobre una ranura que la tarea ya rearmo -- registrando un
        //    resultado que no es suyo. Por eso se borra el pendiente. ARM
        //    v8-M, DDI0553, `NVIC_ICPR<n>`: escribir 1 en el bit limpia el
        //    estado pendiente de esa excepcion sin afectar a la que se este
        //    ejecutando (`cortex_m::peripheral::NVIC::unpend`).
        regs.ier().modify(|w| w.set_eotie(false));
        NVIC::unpend(IRQ_DE_RANURA[indice]);
        // 2. Soltar el DMA, con cota. Es el paso 1 del cierre del manual,
        //    sec.67.4.14, p. 3451: *"Disable DMA requests for Tx and Rx in the
        //    DMA registers"*.
        let _ = soltar_canales(tx, rx);
        // 3. Suspender, con cota `T_SUSP`. sec.67.11.1, p. 3483: *"the CSTART
        //    bit is reset at the end of the current frame and communication is
        //    suspended. The user has to check SUSP flag"*.
        regs.cr1().modify(|w| w.set_csusp(true));
        let limite = Instant::now() + Duration::from_micros(T_SUSP_US);
        while !regs.sr().read().susp() && Instant::now() < limite {}
        // 4. `SUSPC` incondicional, haya llegado `SUSP` o no. sec.67.11.6,
        //    p. 3491: *"This bit must be cleared prior to disabling the SPI"*.
        regs.ifcr().write(|w| w.set_suspc(true));
        // 5. Apagar. sec.67.11.1, p. 3484: con `SPE = 0` se para todo, se
        //    desactiva el NSS del maestro, se resetea la maquina de estados y
        //    se vacian las FIFO. Se acepta perder la trama en curso
        //    (sec.67.4.12, p. 3449); ya estaba perdida.
        regs.cr1().modify(|w| w.set_spe(false));
        // 6. Los dos `DMAEN` del periferico, que solo se pueden escribir con
        //    `SPE = 0` (p. 3484). Es el paso 3 del cierre del manual (p. 3451).
        regs.cfg1().modify(|w| {
            w.set_txdmaen(false);
            w.set_rxdmaen(false);
        });
        // 7. Limpiar banderas: no se limpian solas (sec.67.11.6, p. 3490).
        regs.ifcr().write(|w| {
            w.set_eotc(true);
            w.set_txtfc(true);
            w.set_ovrc(true);
            w.set_suspc(true);
            w.set_modfc(true);
        });
        // ...y otra vez el pendiente: entre el paso 1 y este, `CSUSP` y el
        //    apagado pudieron levantar una bandera y dejar una ISR nueva
        //    encolada. Ahora `SR` esta limpio, asi que esta es la ultima.
        NVIC::unpend(IRQ_DE_RANURA[indice]);
        // 8. Contar y seguir: lo hace la tarea con `Evento::PlazoVencido`
        //    (`core::maestro_j2`). Aqui, nada.
    }
}

/// D4 paso 2 con cota (enmienda del 18-09, #368). Nunca gira sin cota.
///
/// **Pide `request_pause()`, no `request_reset()`**, y la diferencia es todo el
/// punto: `Channel::request_reset` (gpdma/mod.rs:901-910) es
/// `self.request_pause(); while self.is_running() {}` **y luego** el
/// `CxCR.RESET`. Ese `while` de la linea 907 es justo el bucle sin cota que
/// esta funcion existe para evitar; llamarlo aqui dejaba la cota de abajo como
/// codigo muerto y `Soltado::Escalado` inalcanzable. `request_pause`
/// (gpdma/mod.rs:882-887) es una sola escritura, `CxCR.SUSP = 1`, y vuelve.
///
/// Asi que: `SUSP` a los dos canales, sondear `is_running()` -- que es
/// `!suspf && !idlef` (gpdma/mod.rs:912-919) -- como maximo `T_CANAL`, y solo
/// entonces soltarlos. El `Drop` de embassy (gpdma/mod.rs:1287-1294) hace
/// `request_reset()` y su propio `while`: los dos salen al instante porque el
/// canal ya esta suspendido, y el `CxCR.RESET` que aplica es el que de verdad
/// deja el canal reconfigurable.
///
/// Si un canal no para dentro de la cota, escala: **no** suelta ninguno de los
/// dos `Transfer` (soltarlos meteria el `Drop` en su bucle) y resetea el
/// **GPDMA1 entero** por RCC. El radio de esa escalada no son las seis ranuras:
/// es todo el controlador, con los canales de quien sea. Hoy en `fw` no hay
/// otro usuario (`grep -rn GPDMA1_CH src/` fuera de este archivo da cero), y
/// `nueva` exige `CanalGpdma1` para que ninguna ranura llegue aqui con un canal
/// del HPDMA1, que este reset no tocaria. Las otras ranuras veran sus futuros
/// de DMA resolverse, no recibiran `EOT`, venceran su plazo y ejecutaran D4
/// cada una: un reinicio bajo control y dentro de los 50 ms del modulo, no un
/// reinicio del chip.
///
/// Que 10 us sea una cota y no un numero suelto lo sostiene RM0486 Rev 4,
/// sec.19.4.3 p. 942 -- es la **suspension** la que espera la rafaga:
/// *"Wait for the channel to be effectively in suspended state means wait for
/// the completion of any ongoing GPDMA transfer over its master ports"* -- y la
/// misma frase esta en el paso 2 del abort, sec.19.4.4 p. 943. Lo que se espera
/// es una rafaga, no un bloque.
///
/// Lo usa tambien el esclavo (tarea 9).
pub fn soltar_canales(
    mut tx: ManuallyDrop<Transfer<'_>>,
    mut rx: ManuallyDrop<Transfer<'_>>,
) -> Soltado {
    tx.request_pause();
    rx.request_pause();
    let limite = Instant::now() + Duration::from_micros(T_CANAL_US);
    while tx.is_running() || rx.is_running() {
        if Instant::now() >= limite {
            // Los dos `Transfer` se quedan SIN soltar a proposito: el
            // envoltorio `ManuallyDrop` no ejecuta el `Drop` de embassy, que
            // es el bucle sin cota que estamos evitando. (`core::mem::forget`
            // seria un no-op sobre el envoltorio, y el lint `forget_non_drop`
            // lo diria.) Quien para los canales es el reset de RCC.
            rcc::enable_and_reset::<peripherals::GPDMA1>();
            ESCALADAS_GPDMA.fetch_add(1, Ordering::Relaxed);
            defmt::error!(
                "D4.2: un canal del GPDMA no paro en {} us; GPDMA1 reseteado por RCC",
                T_CANAL_US
            );
            return Soltado::Escalado;
        }
    }
    unsafe {
        ManuallyDrop::drop(&mut tx);
        ManuallyDrop::drop(&mut rx);
    }
    Soltado::Limpio
}

/// El futuro del `EOT`, que resuelve la ISR (D2).
struct EsperaEot<'a> {
    estado: &'a EstadoRanura,
}

impl Future for EsperaEot<'_> {
    type Output = Banderas;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Banderas> {
        // D2, regla 3: el waker ANTES de mirar la bandera. Al reves se pierde
        // el despertar y el plazo vence sobre una trama buena.
        self.estado.waker.register(cx.waker());
        match self.estado.turno.tomar() {
            Some(b) => Poll::Ready(b),
            None => Poll::Pending,
        }
    }
}

/// La ISR de la ranura `R`. Se ata en quien arma la placa:
/// `bind_interrupts!(struct IrqsJ2 { SPI5 => Isr<0>; ... })`, y con prioridad
/// por encima del ejecutor del J2 (EN-PLACA, casilla del 11-09).
///
/// **Que protege la generacion y que la protege a ella.** La generacion que la
/// ISR pasa a `registrar` es la que esta armada en ese instante, porque el
/// hardware no etiqueta el `EOT`: no hay otra cosa que leer. Asi que esa
/// comparacion **no es la guarda** contra un `EOT` tardio, y no puede serlo. Lo
/// que la generacion protege de verdad es lo otro: que la tarea no consuma un
/// resultado que quedo guardado de un giro anterior (D2, regla 2, `armar`
/// borra). De que no llegue un `EOT` viejo bajo una generacion nueva se
/// encargan dos cosas, las dos temporales: `EOTIE` solo esta armado entre
/// `CSTART` y la ISR (la propia ISR lo apaga, y D4 paso 1 tambien), y el
/// `NVIC::unpend` de D4 tira la ISR que ya estuviera encolada. Si algun dia se
/// arma `EOTIE` fuera de esa ventana, esta guarda deja de existir.
pub struct Isr<const R: usize>;

impl<const R: usize, I: Interrupt> Handler<I> for Isr<R> {
    unsafe fn on_interrupt() {
        // D2: la ISR hace lo minimo. Lee `SR`, copia las banderas que
        // importan, limpia por `IFCR`, deshabilita `EOTIE` y despierta.
        let regs = SPI_DE_RANURA[R];
        let sr = regs.sr().read();
        let mut b = Banderas::NINGUNA;
        if sr.eot() {
            b = b.con(Banderas::EOT);
        }
        if sr.susp() {
            b = b.con(Banderas::SUSP);
        }
        if sr.ovr() {
            b = b.con(Banderas::OVR);
        }
        if sr.modf() {
            b = b.con(Banderas::MODF);
        }
        // sec.67.7, Tabla 661, p. 3458: el metodo de limpieza del `EOT` es
        // *"Writing EOTC to 1"*.
        regs.ifcr().write(|w| {
            w.set_eotc(true);
            w.set_suspc(true);
            w.set_ovrc(true);
            w.set_modfc(true);
        });
        // Solo `EOTIE` se habilita, y se deshabilita aqui: sin esto la ISR
        // vuelve a entrar sobre una ranura que ya no espera nada.
        regs.ier().modify(|w| w.set_eotie(false));
        let e = &ESTADOS[R];
        // La generacion es la armada en este instante: el `EOT` no viene
        // etiquetado y no hay otra cosa que leer, asi que `registrar` no puede
        // fallar por aqui. Lo que cuenta los tardios de verdad es `armar`, al
        // encontrarse un resultado guardado que la tarea no consumio. Ver la
        // nota de `Isr`: quien cierra la ventana es `EOTIE` mas el `unpend`.
        let _ = e.turno.registrar(e.turno.generacion(), b);
        e.waker.wake();
    }
}
