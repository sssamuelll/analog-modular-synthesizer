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
//! `bind_interrupts!` **no** vive aqui: lo pone quien arma la placa (tareas 8 y
//! 10), atando `SPI5 => Isr<0>` y los dos canales del GPDMA a
//! `embassy_stm32::dma::InterruptHandler`.
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

use embassy_futures::join::join;
use embassy_stm32::dma::{self, Transfer, TransferOptions};
use embassy_stm32::gpio::{AfType, Flex, OutputType, Pull, Speed};
use embassy_stm32::interrupt::typelevel::{Binding, Handler, Interrupt};
use embassy_stm32::pac::spi::vals::{Master, Mbr, Ssom};
use embassy_stm32::{gpio, pac, peripherals, rcc, spi, Peri};
use embassy_sync::waitqueue::AtomicWaker;
use embassy_time::{with_timeout, Duration, Instant};
use sam17_nucleo_core::maestro_j2::{Banderas, Tsize, Turno, RANURAS_SPI};

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
    /// `rcc_peri` es `&p.RCC`: `rcc::clocks` (rcc/mod.rs:154) es la unica via
    /// publica al reloj de CPU, y pide una referencia al periferico. Se usa
    /// aqui y no se guarda.
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
        Tx: spi::TxDma<T>,
        Rx: spi::RxDma<T>,
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

        // MBR: el divisor mas pequeno `2^(n+1)` cuyo `f_sck` no pase del reloj
        // sancionado. No se supone que salga exacto, asi que se imprime.
        let f_ker = rcc::frequency::<T>().0;
        let mut mbr = 7u8;
        for n in 0..8u8 {
            if u64::from(f_ker) <= u64::from(cfg.f_sck_hz) << (n + 1) {
                mbr = n;
                break;
            }
        }
        let divisor = 1u32 << (mbr + 1);
        let f_sck = f_ker / divisor;
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
        // diez veces el ciclo de SCK).
        //
        // HUECO: `Clocks` de este build no publica `cpuclk` (es IC1); el campo
        // mas cercano es `sys`, el sysclk (`rcc/n6.rs:1392`). En el N6 el M55
        // puede correr por encima del sysclk, y entonces el retardo real sale
        // corto. Por eso el retardo es un parametro y no una constante: el
        // barrido de sec.9 lo mide y `retardo_tsck_cuartos` lo sube.
        let f_cpu = defmt::unwrap!(rcc::clocks(rcc_peri).sys.to_hertz()).0;
        let cuarto = 4u64 * u64::from(f_sck);
        let ciclos_por_cuarto_tsck = ((u64::from(f_cpu) + cuarto - 1) / cuarto).max(1) as u32;

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
            ciclos_por_cuarto_tsck,
            cfg.retardo_tsck_cuartos
        );

        Ranura {
            indice,
            regs,
            canal_tx,
            canal_rx,
            req_tx,
            req_rx,
            ciclos_por_cuarto_tsck,
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
                Self::reiniciar(regs, tx, rx);
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
        regs: pac::spi::Spi,
        tx: ManuallyDrop<Transfer<'_>>,
        rx: ManuallyDrop<Transfer<'_>>,
    ) {
        // 1. Silenciar la ISR. Sin esto el `CSUSP` del paso 3 produce `SUSP`,
        //    `SUSP` dispara la ISR (`EOTIE` la cubre, sec.67.11.5, p. 3490) y
        //    la ISR limpia `SUSPC` antes de que el paso 3 lo vea.
        regs.ier().modify(|w| w.set_eotie(false));
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
        // 8. Contar y seguir: lo hace la tarea con `Evento::PlazoVencido`
        //    (`core::maestro_j2`). Aqui, nada.
    }
}

/// D4 paso 2 con cota (enmienda del 18-09, #368). Nunca gira sin cota: pide el
/// reset a los dos canales, sondea `is_running()` como maximo `T_CANAL` y solo
/// entonces los suelta, con lo que el `Drop` de embassy (gpdma/mod.rs:1287,
/// `request_reset()` y luego `while self.is_running() {}`) entra y sale.
///
/// Si un canal no para dentro de la cota, escala: **no** suelta los dos
/// `Transfer` y resetea el GPDMA1 entero por RCC. Las otras ranuras veran sus
/// futuros de DMA resolverse, no recibiran `EOT`, venceran su plazo y
/// ejecutaran D4 cada una: un reinicio de las seis bajo control y dentro de los
/// 50 ms del modulo, no un reinicio del chip.
///
/// Que 10 us sea una cota y no un numero suelto lo sostiene RM0486 Rev 4,
/// sec.19.4.4 p. 943 (y sec.19.4.3 p. 942 para la suspension): el paso 2 del
/// abort dice *"Wait for the channel to be effectively in suspended state means
/// wait for the completion of any ongoing GPDMA transfer over its master
/// port"*, y el paso 3 resetea. Lo que se espera es una rafaga, no un bloque.
///
/// Lo usa tambien el esclavo (tarea 9).
pub fn soltar_canales(
    mut tx: ManuallyDrop<Transfer<'_>>,
    mut rx: ManuallyDrop<Transfer<'_>>,
) -> Soltado {
    tx.request_reset();
    rx.request_reset();
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
        // `false` = tardio; `Turno` ya lo conto (D2, regla 1).
        let _ = e.turno.registrar(e.turno.generacion(), b);
        e.waker.wake();
    }
}
