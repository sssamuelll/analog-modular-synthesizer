//! El esclavo del banco en SPI4: cuenta bytes en el flanco de `CS`, rechaza
//! entero, y se limpia con la linea del #292.
//!
//! **Es el esclavo DEL BANCO, no el de la Voz.** El firmware del modulo de voz
//! no existe y ningun papel encargo este codigo: lo encarga el montaje del
//! 11-09 (`EN-PLACA.md`, seccion *«El J2 en la Nucleo»*), que puso los dos
//! extremos del J2 en la misma NUCLEO-N657X0-Q -- maestro en **SPI5**
//! ([`crate::j2_spi`]) y esclavo en **SPI4**, cuatro hilos de una fila a la
//! otra del CN15. Hace lo **minimo** que la cabecera del J2 dice del receptor y
//! nada mas: no conoce el sobre, no valida CRC, no tiene sesion ni dialecto y
//! no mira el contenido de ningun byte. Devuelve por MISO el patron fijo de
//! [`crate::j2_banco::PATRON_SUBIDA`], que es lo que el juez del banco espera.
//! Vive y muere con el banco, igual que [`crate::j2_banco`]: lo retira #267.
//!
//! **Lo que el banco gana con el** (EN-PLACA): un enlace contra el MISO al aire
//! solo mide `plazos_vencidos`. Con un esclavo que cuenta bytes se prueba
//! ademas la linea del #292 (`SPE = 0` → `SPE = 1` al contar corto) y el riesgo
//! 3 del papel del maestro -- abortar una trama a mitad de byte y ver que la
//! siguiente se acepta.
//!
//! # Las dos reglas que implementa, y de donde salen
//!
//! - **Contar bytes en el flanco de `CS`** (cabecera
//!   `2026-09-02-cabecera-j2-design.md`, D6.2 y D6.4): *«"Entero" se mide en
//!   bytes completos recibidos en ese giro -- un byte a medias no cuenta»*. Los
//!   bytes completos los cuenta el GPDMA, no nosotros: `CxBR1.BNDT` *«is
//!   decremented, indicating the remaining number of data items in the current
//!   source block to be transferred»* (RM0486 Rev 4, sec.19.8.12, p. 997), y su
//!   fuente es `RXDR`, asi que medio byte atrapado en el registro de
//!   desplazamiento no llega a contarse. El byte de cola de D6.4 existe justo
//!   para que esa cuenta no compita con el DMA por el ultimo byte
//!   (hallazgo H-14).
//! - **Rechazar entero y contar** (cabecera D8, punto 1): *«`CS` sube con menos
//!   bytes que `largo + 7`»* es trama corta. Aqui el umbral es `esperado`, que
//!   el binario pone en `j2_banco::LARGO_BANCO`; el `largo + 7` del sobre llega
//!   con #267.
//!
//! # Las tres causas de trama corta, y como se distinguen
//!
//! `TRAMAS_CORTAS` no dice **por que** fue corta. Son tres cosas distintas y el
//! banco tiene que poder separarlas; las tres se miran el dia de la placa con
//! el analizador logico (riesgo 8 del papel del maestro).
//!
//! 1. **El maestro abortó la trama** -- lo que este esclavo existe para probar.
//!    Firma: `TRAMAS_CORTAS` sube **a la vez que** `plazos_vencidos` del
//!    maestro, giro a giro.
//! 2. **El esclavo no llego a rearmar** (seccion siguiente). Firma:
//!    `TRAMAS_CORTAS` sube **sin** `plazos_vencidos`.
//! 3. **La carrera por el ultimo byte, y es nuestra.** El umbral `esperado`
//!    incluye el byte de cola de D6.4 -- D8 mide contra `largo + 7`, cola
//!    dentro --, o sea que el **ultimo** byte de datos tiene que estar contado
//!    cuando leemos `BNDT`. Los ocho relojes de cola son el margen que D6.4
//!    concede para el byte de datos anterior (hallazgo H-14), pero el byte de
//!    cola en si **no tiene margen**: entre el flanco de `CS` y nuestro `BNDT`
//!    hay la ISR, el despertar y un poll del ejecutor, y si el GPDMA pierde esa
//!    carrera salen 24 donde hubo 25 y la trama se cuenta corta sin serlo.
//!    Firma: `TRAMAS_CORTAS` subiendo con **una tasa baja y constante**, sin
//!    `plazos_vencidos` y sin que el analizador vea ninguna trama truncada en
//!    el cable. **El umbral no se toca por esto**: es D8 y es del papel. Lo que
//!    se mide en el banco es si la carrera se pierde alguna vez, y si se
//!    pierde, la respuesta vive en el papel (el byte de cola), no aqui.
//!
//! **La linea del #292.** Papel del maestro
//! `2026-09-03-maestro-j2-recuperacion-design.md`, D4, parrafo *«Lo que le pasa
//! al esclavo»*: el `SPE = 0` del reinicio del maestro desactiva su NSS, asi que
//! el esclavo ve el `CS` subir a mitad de trama. RM0486 Rev 4, sec.67.4.13,
//! p. 3450: *«In slave mode, any ongoing data are lost when disabling the
//! SPI.»* De ahi la enmienda mandada al papel del modulo: **al contar corto en
//! el flanco de `CS`, `SPE = 0` → `SPE = 1` antes de rearmar el DMA de
//! recepcion**, porque un esclavo que solo rearme el DMA arrastra medio byte y
//! rechaza tambien las tramas siguientes. Esta en [`Esclavo::correr`], en el
//! brazo corto y solo en el.
//!
//! # Ninguna espera sin cota, y la unica que no tiene plazo (R-MJ2)
//!
//! La unica espera de este modulo es [`flanco_de_cs`], y **no lleva plazo a
//! proposito**: el esclavo no manda en el enlace, espera al maestro, y un plazo
//! aqui seria inventar una cadencia que el otro extremo no prometio. No es un
//! bucle: es un futuro que despierta una ISR, asi que mientras espera no
//! retiene la CPU ni al ejecutor del J2. Los unicos sondeos con bucle viven en
//! [`crate::j2_spi::soltar_canales`], que trae su cota `T_CANAL`.
//!
//! # El hueco del rearme, que el banco tiene que medir
//!
//! Entre el flanco de `CS` y el `SPE = 1` de la vuelta siguiente hay un rato en
//! que el esclavo **no escucha**: `SPE = 0`, `CFG1`, los dos `Channel::read` y
//! `write`, `CFG1` otra vez y `SPE = 1`, mas los dos `request_pause` y el
//! sondeo de `is_running` de `soltar_canales`, mas el despertar de la ISR y un
//! poll del ejecutor. **Cuanto dura eso no esta acotado en ningun sitio** y no
//! lo inventamos aqui: se mide en el banco.
//!
//! **Lo que lo hace inocuo no es `T_GAP`, es la cadencia.** `T_GAP` son 2 us
//! provisionales (cabecera D8) y es el hueco **minimo** entre tramas, no el que
//! hay en regimen: el maestro gira cada `PERIODO_GIRO_US` = 125 us y al piso de
//! 10 MHz una trama de 25 bytes ocupa 25 x 8 / 10 MHz = 20 us, asi que el aire
//! real son 125 - 20 = **105 us**. Si el rearme cupiera en 2 us no haria falta
//! decir nada; lo que de verdad hay que comprobar es que cabe en 105.
//!
//! **Y los dos extremos comparten ejecutor.** El maestro y el esclavo del banco
//! corren los dos como tareas del `EJECUTOR_J2` a `P2`
//! (`j2_ejecutor::PRIORIDAD_EJECUTOR`), asi que el rearme del esclavo se
//! planifica **contra** la tarea del maestro, no en paralelo con ella. Es una
//! propiedad del banco -- en el instrumento de verdad el esclavo esta en otro
//! chip -- y hay que tenerla delante al leer los numeros.
//!
//! **La firma.** Si el rearme no cabe, `TRAMAS_CORTAS` sube en **todas** las
//! tramas, no de vez en cuando, y sin `plazos_vencidos` del maestro: es *«el
//! esclavo no llego»* y no *«el maestro se colgo»*. El flanco perdido en el
//! hueco no se descarta nunca -- la bandera de [`IsrCs`] se queda puesta y la
//! consume la espera siguiente, que cuenta cero bytes y suma a
//! `TRAMAS_CORTAS` --, porque borrarla al rearmar taparia justo lo que hay que
//! medir. El dia de la placa lo mide el analizador logico (riesgo 8 del papel
//! del maestro).
//!
//! # Quien lo construye, y donde estan sus interrupciones
//!
//! El `bind_interrupts!` **no** vive aqui, igual que en el driver del maestro:
//! vive **una sola vez** en [`crate::j2_banco::IrqsBanco`] (R23), junto a los
//! pines del montaje, y de ahi lo toman los cuatro binarios. Las tres ataduras
//! que este archivo necesita son `EXTI11 => IsrCs` y los dos canales:
//!
//! ```ignore
//! EXTI11 => sam17_nucleo_fw::j2_esclavo::IsrCs;
//! GPDMA1_CHANNEL2 => embassy_stm32::dma::InterruptHandler<peripherals::GPDMA1_CH2>;
//! GPDMA1_CHANNEL3 => embassy_stm32::dma::InterruptHandler<peripherals::GPDMA1_CH3>;
//! ```
//!
//! (los nombres de las lineas del N657 son `EXTI11`, `SPI4` y
//! `GPDMA1_CHANNELn`, no `GPDMA1_CHn`, que es el nombre del *periferico*).
//!
//! **El NVIC entero lo pone [`Esclavo::nuevo`]** (R21, igual que el maestro):
//! `EXTI11` con su `P1` y su `enable`, y `P1` tambien a las dos lineas de los
//! canales del GPDMA -- sin `enable`, porque esas las desenmascara
//! `embassy_stm32::init` por su cuenta. Los binarios no tocan el NVIC.
//!
//! No se construye a mano: se pide a [`crate::j2_banco::esclavo_del_banco`],
//! que tiene los cuatro pines como **tipos concretos** y no deja equivocarse.
//! La tarea se lanza con el spawner del ejecutor del J2 **despues** de
//! `j2_ejecutor::arrancar`:
//!
//! ```ignore
//! let esclavo = j2_banco::esclavo_del_banco(p.PE2, p.PE14, p.PE13, p.PE11,
//!                                           p.GPDMA1_CH2, p.GPDMA1_CH3);
//! // `#[embassy_executor::task]` devuelve `Result<SpawnToken, SpawnError>` y
//! // `SendSpawner::spawn` devuelve `()`: se desenvuelve el token, no el spawn
//! // (misma forma que `j2_ejecutor::arrancar`).
//! EJECUTOR_J2.spawner().spawn(defmt::unwrap!(j2_esclavo::tarea_esclavo(esclavo)));
//! ```
//!
//! La feature `exti` de embassy sigue **fuera** de `fw/Cargo.toml` a proposito:
//! con ella embassy define su propio manejador de `EXTI11` y chocaria con
//! [`IsrCs`].
//!
//! **Donde vive la linea del #292, y por que no donde dice la spec.** El papel
//! del maestro la describe como *«una linea en su ISR»*, y aqui vive en la
//! tarea ([`Esclavo::correr`]), no en [`IsrCs`]. La razon es la misma que en el
//! maestro (D2): la ISR hace lo minimo -- limpia el pendiente, pone la bandera
//! y despierta -- porque corre a `P1`, por encima del ejecutor del J2, y todo
//! lo que meta ahi se lo quita a las seis tareas de ranura. El sitio en el
//! **orden** es el que manda el papel, y ese se respeta: al contar corto, antes
//! de rearmar el DMA. Que sean dos escrituras en la tarea en vez de dos en la
//! ISR no cambia ni el orden ni lo que ve el cable. En un modulo de verdad, con
//! su propio chip y sin seis tareas compartiendo ejecutor, la ISR es el sitio
//! natural; aqui no.
//!
//! # Los dos HUECOS y el plan B, dichos aqui para no tener que buscarlos
//!
//! 1. **El modo del enlace queda en 0** (`CPOL = CPHA = 0`) en los dos
//!    extremos, como el maestro. La cabecera sec.11 (mapa de enmiendas, fila
//!    *«J2 punto a punto | D8»*) declara para el peldano 2 la variante
//!    *«maestro modo 0, esclavo modo 1»* con el byte de cola y el bufer de
//!    subida corrido un bit, y la deja **pendiente**: la sella el ojo del
//!    bring-up. Mientras tanto los dos extremos del banco van en modo 0, que es
//!    el valor de reset, y el dia que se selle se cambia el `CFG2` de
//!    [`Esclavo::nuevo`] y nada mas.
//! 2. **El flanco se detecta con `EXTI11` sobre PE11 con el pin en AF5.** Lo
//!    sostiene RM0486 Rev 4, sec.15.3.11 (*AF configuration*), p. 789: con el
//!    pin en funcion alterna *«the Schmitt trigger input is activated»* y
//!    *«data present on the I/O pin are sampled into the input data register
//!    every AHB clock cycle»*, asi que el EXTI sigue viendo la linea. **Si en
//!    la placa el flanco no dispara**, el plan B es un quinto hilo del NSS del
//!    maestro (PA3, CN15 pin 17) a **PE10** (CN15 pin 27, UM3417 Rev 3
//!    Tabla 13, p. 32) con ese pin en `Input` y la linea `EXTI10`. **No esta
//!    implementado**: es una casilla de EN-PLACA, y cambiarlo son dos
//!    constantes de este archivo y el `bind_interrupts!` del binario.

use core::future::poll_fn;
use core::mem::ManuallyDrop;
use core::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use core::task::Poll;

use cortex_m::peripheral::NVIC;
use embassy_stm32::dma::{self, TransferOptions};
use embassy_stm32::gpio::{AfType, Flex, OutputType, Pull, Speed};
use embassy_stm32::interrupt::typelevel::{Binding, Handler, Interrupt};
use embassy_stm32::interrupt::{InterruptExt, Priority};
use embassy_stm32::pac::spi::vals::{Cpha, Cpol, Master, Udrcfg};
use embassy_stm32::{gpio, interrupt, pac, rcc, spi, Peri};
use embassy_sync::waitqueue::AtomicWaker;

use crate::j2_banco::PATRON_SUBIDA;
use crate::j2_spi::{soltar_canales, CanalGpdma1, Soltado, LARGO_MAX};

/// La linea de EXTI del `CS`, que es el numero del pin: PE**11**.
const LINEA_CS: usize = 11;

/// El puerto que `EXTI_EXTICR3` selecciona para la linea 11. RM0486 Rev 4,
/// sec.25.7.24, p. 1156: *«0x04: PE11 pin»*. El 4 de `Pin::port()` de embassy
/// (puerto A = 0, B = 1, ...) coincide con este por casualidad, no por
/// contrato: son dos numeraciones distintas y por eso hay dos constantes.
const PUERTO_E_EXTICR: u8 = 0x04;

/// El `port()` de embassy para el puerto E (`AnyPin::steal`: *«`pin_port` is
/// `port_num * 16 + pin_num`, where `port_num` is 0 for port `A`»*).
const PUERTO_E_EMBASSY: u8 = 4;

/// Tramas en las que el flanco de `CS` llego con `esperado` bytes o mas.
pub static TRAMAS_OK: AtomicU32 = AtomicU32::new(0);

/// Tramas cortas: el flanco de `CS` llego con menos de `esperado` bytes
/// completos (cabecera D8, punto 1). Cada una lleva su `SPE = 0` → `SPE = 1`.
///
/// Subiendo **sin** `plazos_vencidos` del maestro, es el hueco del rearme de
/// este modulo, no un cuelgue del maestro. Ver la cabecera del modulo.
pub static TRAMAS_CORTAS: AtomicU32 = AtomicU32::new(0);

/// Cuantas veces soltar los canales del esclavo tuvo que escalar al reset del
/// GPDMA1 por RCC (`j2_spi::soltar_canales`, D4.2). Se cuenta aparte de
/// `j2_spi::ESCALADAS_GPDMA` para saber **quien** escalo, aunque el reset que
/// aplica sea el mismo controlador entero.
pub static REARMES_ESCALADOS: AtomicU32 = AtomicU32::new(0);

/// La bandera del flanco: la pone [`IsrCs`] y la consume [`flanco_de_cs`].
static FLANCO_CS: AtomicBool = AtomicBool::new(false);

/// A quien despertar cuando `CS` suba.
static WAKER_CS: AtomicWaker = AtomicWaker::new();

/// La ISR del flanco de subida de `CS`. La ata el binario:
/// `bind_interrupts!(struct IrqsEsclavo { EXTI11 => j2_esclavo::IsrCs; ... })`.
///
/// Hace lo minimo: limpia el pendiente, pone la bandera y despierta. Es
/// generica en la linea (`I: Interrupt`) como [`crate::j2_spi::Isr`], pero el
/// pendiente que limpia es el de [`LINEA_CS`]: atarla a otra linea limpiaria la
/// equivocada y la ISR volveria a entrar para siempre. Por eso [`Esclavo::nuevo`]
/// exige `EXTI11` en el tipo de la atadura.
pub struct IsrCs;

impl<I: Interrupt> Handler<I> for IsrCs {
    unsafe fn on_interrupt() {
        // RM0486 Rev 4, sec.25.7.4, p. 1137: `RPIFx` es `rc_w1` --
        // *«This bit is cleared by writing a 1 into the bit»*. `write` deja en
        // cero todo lo demas, o sea que no toca el pendiente de otras lineas.
        pac::EXTI.rpr(0).write(|w| w.set_line(LINEA_CS, true));
        FLANCO_CS.store(true, Ordering::Release);
        WAKER_CS.wake();
    }
}

/// Espera al flanco de subida de `CS`, que es el fin de la trama (cabecera
/// D6.4). **Sin plazo, a proposito**: ver la cabecera del modulo.
async fn flanco_de_cs() {
    poll_fn(|cx| {
        // El waker ANTES de mirar la bandera (misma regla que `EsperaEot` del
        // driver, D2 regla 3): al reves se pierde el despertar y la tarea se
        // queda dormida con la trama ya terminada.
        WAKER_CS.register(cx.waker());
        if FLANCO_CS.swap(false, Ordering::Acquire) {
            Poll::Ready(())
        } else {
            Poll::Pending
        }
    })
    .await
}

/// El esclavo del banco: los registros, los dos canales del GPDMA, sus numeros
/// de peticion, el bufer de recepcion y los cuatro pines. Los `Flex` viven aqui
/// porque su `Drop` desconfigura el pin.
pub struct Esclavo<'d> {
    regs: pac::spi::Spi,
    canal_tx: dma::Channel<'d>,
    canal_rx: dma::Channel<'d>,
    req_tx: dma::Request,
    req_rx: dma::Request,
    /// El minimo de bytes completos que una trama tiene que traer para no ser
    /// corta (cabecera D8). El banco pasa `j2_banco::LARGO_BANCO`.
    esperado: usize,
    /// El bufer de recepcion. El esclavo **no mira** lo que llega: solo cuenta
    /// cuantos bytes entraron, que es todo lo que D6.2 le pide al receptor para
    /// decidir si la trama vale.
    buf: [u8; LARGO_MAX],
    _sck: Flex<'d>,
    _mosi: Flex<'d>,
    _miso: Flex<'d>,
    _nss: Flex<'d>,
}

impl<'d> Esclavo<'d> {
    /// Configura los cuatro pines (AF5), el reloj del periferico, el `CFG2` de
    /// esclavo con NSS por hardware de entrada, el `CFG1` de 8 bits, y la linea
    /// `EXTI11` del flanco de `CS` con su prioridad en el NVIC. Deja el SPI
    /// **apagado**, que es como esta entre tramas.
    ///
    /// `T` es el tipo del periferico (`peripherals::SPI4`): de ahi salen el
    /// reset por RCC y los numeros de peticion del GPDMA. Los registros van
    /// aparte (`pac::SPI4`) porque el `Info` interno de embassy no es publico,
    /// y **se asevera que son los del montaje**: si `T` y `regs` no fueran el
    /// mismo bloque, se configuraria uno y se clocaria en el otro.
    ///
    /// **`T` hay que darselo**, igual que en `j2_spi::Ranura::nueva`: no sale
    /// de ningun argumento -- solo aparece en `Tx: spi::TxDma<T>` y
    /// `Rx: spi::RxDma<T>`, y un canal del GPDMA1 implementa `TxDma` para
    /// varios SPI a la vez, asi que el compilador no puede elegir. La llamada
    /// es `Esclavo::nuevo::<peripherals::SPI4, _, _, _, _, _, _>(...)`.
    ///
    /// Los dos canales tienen que ser del **GPDMA1** (`CanalGpdma1`), por la
    /// misma razon que en el maestro: la escalada de
    /// [`crate::j2_spi::soltar_canales`] resetea ese controlador y uno del
    /// HPDMA1 la dejaria muda. Es un error de compilacion.
    ///
    /// `irqs` es el `Irqs` del `bind_interrupts!` del binario, y prueba en el
    /// tipo las tres ataduras: los dos canales del GPDMA y `EXTI11 => IsrCs`.
    ///
    /// **Se construye en el arranque**, antes de `j2_ejecutor::arrancar`: los
    /// registros del EXTI se tocan con lectura-modificacion-escritura sin
    /// seccion critica, y eso solo vale porque nadie mas escribe el EXTI en
    /// `fw` (la feature `exti` de embassy esta fuera, `grep -rn "exti" src/`).
    #[allow(clippy::too_many_arguments)]
    pub fn nuevo<T, Sck, Mosi, Miso, Nss, Tx, Rx>(
        regs: pac::spi::Spi,
        sck: Peri<'d, Sck>,
        mosi: Peri<'d, Mosi>,
        miso: Peri<'d, Miso>,
        nss: Peri<'d, Nss>,
        tx: Peri<'d, Tx>,
        rx: Peri<'d, Rx>,
        irqs: impl Binding<Tx::Interrupt, dma::InterruptHandler<Tx>>
            + Binding<Rx::Interrupt, dma::InterruptHandler<Rx>>
            + Binding<interrupt::typelevel::EXTI11, IsrCs>
            + Copy
            + 'd,
        esperado: usize,
    ) -> Esclavo<'d>
    where
        T: spi::Instance,
        Sck: gpio::Pin,
        Mosi: gpio::Pin,
        Miso: gpio::Pin,
        Nss: gpio::Pin,
        Tx: CanalGpdma1 + spi::TxDma<T>,
        Rx: CanalGpdma1 + spi::RxDma<T>,
    {
        // El montaje del banco es SPI4 y el `CS` es PE11 (restricciones
        // globales, EN-PLACA seccion «El J2 en la Nucleo»). Las dos cosas estan
        // cableadas en este archivo -- `regs` para la ISR de nadie, `LINEA_CS`
        // para el EXTI --, asi que las dos se aseveran en vez de confiarse.
        defmt::assert!(
            regs == pac::SPI4,
            "J2 esclavo: los registros no son los de SPI4 (montaje del banco)"
        );
        defmt::assert!(
            nss.port() == PUERTO_E_EMBASSY && nss.pin() == LINEA_CS as u8,
            "J2 esclavo: el NSS no es PE11 y EXTI11 no veria su flanco"
        );
        defmt::assert!(
            esperado > 0 && esperado <= LARGO_MAX,
            "J2 esclavo: `esperado` fuera de [1, LARGO_MAX]"
        );
        // R-MJ7, igual que el maestro: los buferes de DMA van en memoria no
        // cacheable, y hoy toda la garantia es que la D-cache del M55 esta
        // apagada. `SCB::dcache_enabled` lee `CCR.DC`, bit 16 (cortex-m 0.7.9,
        // scb.rs:341 y :504).
        defmt::assert!(
            !cortex_m::peripheral::SCB::dcache_enabled(),
            "R-MJ7: la D-cache esta encendida y el bufer del esclavo no esta en region MPU"
        );

        rcc::enable_and_reset::<T>();

        // Los cuatro pines a AF5 (`STM32N657X0.json` y DS14791 Rev 10 Tabla 18;
        // el `_generated.rs` de este build lo repite: `pin_trait_impl!(
        // spi::SckPin, SPI4, PE2, 5u8)`, y lo mismo MOSI PE14, MISO PE13 y
        // CS PE11). Al reves que en el maestro: el esclavo **recibe** el reloj,
        // el MOSI y el `CS`, y solo **emite** el MISO.
        let entrada = AfType::input(Pull::None);
        let mut sck = Flex::new(sck);
        let mut mosi = Flex::new(mosi);
        let mut miso = Flex::new(miso);
        let mut nss = Flex::new(nss);
        sck.set_as_af_unchecked(5, entrada);
        mosi.set_as_af_unchecked(5, entrada);
        // El NSS va con **pull-up**, y es el unico de los cuatro que lo lleva:
        // el `CS` lo pone PA3 del maestro, que no existe hasta que el binario
        // construya su `Ranura`, y hasta entonces la linea **flota**. Un flanco
        // espurio en ese rato deja `FLANCO_CS` puesta y la primera vuelta de
        // `correr` contaria una trama corta que no existio. El reposo del `CS`
        // es el nivel alto (`SSIOP = 0`, activo a nivel bajo), asi que el
        // pull-up es el reposo, no una invencion. Vale en AF: sec.15.3.11,
        // p. 789 -- *«the weak pull-up and pull-down resistors are activated or
        // not, depending on the value in GPIOx_PUPDR»* --, y `PUPDR` codifica
        // *«01: Pull-up»* con reset `0x0000 0000` (sin pull) para el puerto E
        // (sec.15.4.4, p. 795-796).
        nss.set_as_af_unchecked(5, AfType::input(Pull::Up));
        // `VeryHigh` por la misma razon que en el maestro: el enlace sube a
        // 34,5 MHz en el peldano 2 (spec del maestro D8).
        miso.set_as_af_unchecked(5, AfType::output(OutputType::PushPull, Speed::VeryHigh));

        // CFG2 del esclavo. `write` deja en cero todo lo que no se nombra:
        // `COMM = 0` (full duplex), `LSBFRST = 0`, `IOSWP = 0`, `RDIOM = 0` (no
        // usamos la senal RDY) y `SSIOP = 0`, que es `ActiveLow` -- el `CS` del
        // maestro es activo a nivel bajo (sec.67.4.7, p. 3437: *«NSS level is
        // considered as active if it is equal to SSIOP»*).
        //
        // **`AFCNTR` se queda en 0 y no es un olvido**: el maestro lo pone a 1
        // y aqui esta prohibido. sec.67.11.4, p. 3487: *«The bit AFCNTR must
        // not be set, when the block is in slave mode.»* Con `write` cae a cero
        // solo; se dice aqui para que nadie lo copie del `CFG2` del maestro.
        //
        // - `MASTER = 0`: sec.67.11.4, p. 3488, bit 22.
        // - `SSM = 0` y `SSOE = 0`, o sea NSS por hardware de **entrada**:
        //   sec.67.4.7, p. 3437-3438 -- *«NSS output enable (SSOE = 1): this
        //   configuration is only used when the MCU is set as master»*, y con
        //   `SSM = 0, SSOE = 0` *«In slave mode, the NSS pin works as a
        //   standard "chip select" input and the slave is selected while the
        //   NSS line is at its active level»* (sec.67.11.4, p. 3487, bits 29
        //   y 26).
        // - `CPOL`/`CPHA` = 0, modo 0, explicitos porque son el HUECO 1 de la
        //   cabecera de este modulo y el dia que el peldano 2 se selle cambia
        //   aqui (sec.67.11.4, p. 3488, bits 25 y 24).
        //
        // Y la frase que hace seguro todo el rearme de `correr`, sec.67.4.7,
        // p. 3438: *«When the SPI slave is enabled in the hardware slave select
        // management mode, all the transfers are ignored even in case of the
        // NSS is found at active level. They are ignored until the slave
        // detects a start of the NSS signal (transition from nonactive to
        // active level) just synchronizing the slave with the master.»* Es
        // decir: rehabilitar el SPI con el `CS` ya bajo no engancha media
        // trama; el esclavo espera al flanco siguiente.
        regs.cfg2().write(|w| {
            w.set_master(Master::Slave);
            w.set_ssm(false);
            w.set_ssoe(false);
            w.set_cpol(Cpol::IdleLow);
            w.set_cpha(Cpha::FirstEdge);
        });

        // CFG1. `DSIZE = 7` son 8 bits (el campo es largo-1, sec.67.4.9
        // p. 3443). `CRCEN = 0` explicito: el CRC es el del sobre, no el del
        // periferico. Los dos `DMAEN` quedan en cero: los enciende `correr` en
        // su sitio del orden. `MBR` no se toca: es el divisor del **maestro** y
        // en modo esclavo el reloj lo pone el cable.
        //
        // `UDRCFG` queda en su valor de reset, `Constant` (sec.67.11.3,
        // p. 3486: *«0: slave sends a constant pattern defined by the user in
        // the SPI_UDRDR register»*), y `SPI_UDRDR` tambien en el suyo,
        // `0x0000 0000` (sec.67.11.13, p. 3497). Eso es lo que el maestro lee
        // en `subida` si cloca mas de los 25 bytes del patron: primero **un
        // byte accidental** y despues ceros -- sec.67.5.2, *«Underrun flag
        // (UDR)»*, p. 3453: *«single additional dummy (accidental) data is
        // always inserted between the last valid data and the constant pattern
        // defined at the UDRDR register»*. El juez del banco lo rechaza
        // entero, que es lo correcto: el maestro clocando de mas es un defecto.
        regs.cfg1().write(|w| {
            w.set_dsize(7);
            w.set_crcen(false);
            w.set_udrcfg(Udrcfg::Constant);
            w.set_txdmaen(false);
            w.set_rxdmaen(false);
        });

        // `TSIZE = 0` **a proposito**, y es la unica excepcion a R-MJ1, que
        // habla del maestro: el esclavo no sabe cuantos bytes va a clocar el
        // otro extremo. sec.67.4.10, p. 3444, paso 3 de la configuracion:
        // *«Write to the SPI_CR2 register to select the length of the transfer,
        // if it is not known TSIZE must be programmed to zero»*. Lo unico que
        // `TSIZE = 0` estropea en el esclavo es la logica de la senal `RDY`
        // (p. 3441), y no la usamos (`RDIOM = 0`). Explicito aunque sea el
        // valor de reset, porque la excepcion tiene que verse.
        regs.cr2().write(|w| w.set_tsize(0));

        // El flanco de `CS` por el `pac`, con el pin **en AF5**: `ExtiInput` de
        // embassy reconfiguraria el pin a entrada y el SPI se quedaria sin su
        // `CS`. Es la razon de hacerlo a mano.
        //
        // 1. La linea 11 al puerto E. `EXTI_EXTICR3` (offset 0x068) cubre las
        //    lineas 8 a 11, o sea `exticr(2)` del metapac, y la 11 es su campo
        //    3. sec.25.7.24, p. 1156.
        pac::EXTI
            .exticr(LINEA_CS / 4)
            .modify(|w| w.set_exti(LINEA_CS % 4, PUERTO_E_EXTICR));
        // 2. Flanco de **subida** y solo el: `CS` subiendo es el fin de la
        //    trama (cabecera D6.4). `EXTI_RTSR1`, sec.25.7.1, p. 1134.
        pac::EXTI.rtsr(0).modify(|w| w.set_line(LINEA_CS, true));
        // 3. Tirar lo que hubiera pendiente antes de desenmascarar, en el EXTI
        //    y en el NVIC: un pendiente de antes del arranque haria que la
        //    primera espera volviera al instante y contara una trama corta que
        //    no existio.
        pac::EXTI.rpr(0).write(|w| w.set_line(LINEA_CS, true));
        NVIC::unpend(interrupt::EXTI11);
        // 4. Desenmascarar. `EXTI_IMR1`, sec.25.7.27, p. 1161.
        pac::EXTI.imr(0).modify(|w| w.set_line(LINEA_CS, true));
        // 5. El NVIC. `P1` como las ISR del maestro, o sea por encima del
        //    ejecutor del J2 (`j2_ejecutor::PRIORIDAD_EJECUTOR`, `P2`): la ISR
        //    solo pone una bandera y despierta, y tiene que poder hacerlo
        //    aunque el ejecutor este corriendo otra tarea.
        interrupt::EXTI11.set_priority(Priority::P1);
        // SAFETY: la unica forma de habilitar la linea. El manejador existe
        // porque `irqs` prueba en el tipo la atadura `EXTI11 => IsrCs`.
        unsafe { interrupt::EXTI11.enable() };

        // 6. Y los dos canales del GPDMA, tambien a `P1`, por la misma razon y
        //    por simetria con `j2_spi::Ranura::nueva` (R21: el NVIC lo maneja
        //    quien arma la interrupcion). Sin `enable`: los dieciseis los
        //    desenmascara `embassy_stm32::init` por su cuenta
        //    (`embassy-stm32/src/dma/gpdma/mod.rs:526-534`), con la prioridad de
        //    su `Config`; lo unico que falta es subirlos por encima del ejecutor
        //    del J2. Van por tipo, no por valor: el canal ya se movio dentro de
        //    `Channel::new` unas lineas mas abajo.
        Tx::Interrupt::set_priority(Priority::P1);
        Rx::Interrupt::set_priority(Priority::P1);

        let req_tx = tx.request();
        let req_rx = rx.request();
        let canal_tx = dma::Channel::new(tx, irqs);
        let canal_rx = dma::Channel::new(rx, irqs);

        // Apagado al salir, que es el estado entre tramas (sec.67.4.12,
        // p. 3448).
        regs.cr1().modify(|w| w.set_spe(false));

        defmt::info!(
            "J2 esclavo en SPI4: modo 0, DSIZE 8, NSS por hardware en PE11, \
             EXTI11 a P1, esperado {} bytes",
            esperado
        );

        Esclavo {
            regs,
            canal_tx,
            canal_rx,
            req_tx,
            req_rx,
            esperado,
            buf: [0u8; LARGO_MAX],
            _sck: sck,
            _mosi: mosi,
            _miso: miso,
            _nss: nss,
        }
    }

    /// El lazo del esclavo: armar, esperar el flanco de `CS`, contar bytes,
    /// rechazar entero si vienen menos de `esperado`, soltar los canales y
    /// repetir. No vuelve nunca.
    ///
    /// El orden de arranque es el del maestro sin `TSIZE` ni `CSTART`, que son
    /// del que manda: `SPE = 0` → `RXDMAEN` → canales armados → `TXDMAEN` →
    /// `SPE = 1` (los cuatro pasos del arranque del DMA, sec.67.4.14, p. 3451).
    /// El cierre es el simetrico: `SPE = 0` y solo entonces los dos `DMAEN`,
    /// que estan protegidos con el SPI encendido (sec.67.11.1, p. 3484).
    pub async fn correr(mut self) -> ! {
        let regs = self.regs;
        let esperado = self.esperado;

        loop {
            // Los dos punteros a los registros de datos se calculan DENTRO del
            // lazo, igual que en `j2_spi::giro`, y no es estilo: si viven a
            // traves del `.await` de mas abajo, el generador de este futuro se
            // los queda, un `*mut u8` no es `Send` y el futuro deja de serlo.
            // `InterruptExecutor` solo da un `SendSpawner`, cuyo `spawn` exige
            // `S: Send` (`embassy-executor/src/spawner.rs:223`), asi que la
            // tarea no se podria lanzar. Lo vigila el aserto del final del
            // archivo, que mira EL FUTURO y no solo al `Esclavo`.
            let txdr = regs.txdr32().as_ptr() as *mut u8;
            let rxdr = regs.rxdr32().as_ptr() as *mut u8;

            regs.cr1().modify(|w| w.set_spe(false));
            // 1. `RXDMAEN`.
            regs.cfg1().modify(|w| w.set_rxdmaen(true));
            // 2. Los dos canales, bajo `ManuallyDrop` por R-MJ2: el `Drop` de
            //    embassy gira sin cota, asi que quien los suelta es
            //    `soltar_canales`, que trae la suya. La recepcion se arma al
            //    `LARGO_MAX` del enlace porque el esclavo no sabe cuanto va a
            //    clocar el maestro; lo que de verdad llego se lee luego del
            //    contador del canal.
            let rx = ManuallyDrop::new(unsafe {
                self.canal_rx
                    .read(self.req_rx, rxdr, &mut self.buf, TransferOptions::default())
            });
            let tx = ManuallyDrop::new(unsafe {
                self.canal_tx.write(
                    self.req_tx,
                    &PATRON_SUBIDA,
                    txdr,
                    TransferOptions::default(),
                )
            });
            // 3. `TXDMAEN`.
            regs.cfg1().modify(|w| w.set_txdmaen(true));
            // 4. `SPE = 1`. A partir de aqui el esclavo escucha -- y por
            //    p. 3438 no engancha nada hasta el proximo flanco de bajada
            //    del `CS`, aunque el `CS` ya estuviera bajo.
            regs.cr1().modify(|w| w.set_spe(true));

            // La unica espera, y sin plazo a proposito (R-MJ2, cabecera del
            // modulo). `CS` subiendo es el fin de la trama: cabecera D6.4.
            flanco_de_cs().await;

            // Bytes COMPLETOS recibidos (cabecera D6.2: *«un byte a medias no
            // cuenta»*). `get_remaining_transfers` lee `CxBR1.BNDT`, que es
            // *«block number of data bytes to transfer from the source … is
            // decremented, indicating the remaining number of data items in the
            // current source block to be transferred»* (RM0486 Rev 4,
            // sec.19.8.12, p. 997). Ojo con lo que eso significa: cuenta
            // **lecturas de `RXDR`**, no escrituras a memoria. La conclusion
            // que importa se sostiene igual -- medio byte atrapado en el
            // registro de desplazamiento no llega a `RXDR` y no suma --, pero
            // el ultimo byte de datos si es una carrera: ver la tercera causa
            // de trama corta espuria en la cabecera del modulo.
            let recibidos = LARGO_MAX - rx.get_remaining_transfers() as usize;

            if recibidos < esperado {
                // Cabecera D8, punto 1: trama corta, se rechaza entera y se
                // cuenta. No se mira ni un byte del bufer.
                TRAMAS_CORTAS.fetch_add(1, Ordering::Relaxed);
                // La linea del #292, aqui y solo aqui, ANTES de que la vuelta
                // siguiente rearme el DMA. RM0486 Rev 4, sec.67.4.13, p. 3450:
                // *«In slave mode, any ongoing data are lost when disabling the
                // SPI»* -- apagar vacia las FIFO y el registro de
                // desplazamiento, que es donde se queda el medio byte que si
                // no arrastraria y haria rechazar tambien las tramas
                // siguientes (papel del maestro D4, *«Lo que le pasa al
                // esclavo»*). El `SPE = 0` del cierre, tres lineas mas abajo,
                // no deshace esa limpieza: ya paso.
                regs.cr1().modify(|w| w.set_spe(false));
                regs.cr1().modify(|w| w.set_spe(true));
            } else {
                TRAMAS_OK.fetch_add(1, Ordering::Relaxed);
            }

            // D4.2 con su cota `T_CANAL`. Ningun `Transfer` se suelta con su
            // canal corriendo (R-MJ2); si uno no para, `soltar_canales` resetea
            // el GPDMA1 por RCC y lo dice.
            if let Soltado::Escalado = soltar_canales(tx, rx) {
                REARMES_ESCALADOS.fetch_add(1, Ordering::Relaxed);
            }

            // Cierre: apagar y solo entonces los dos `DMAEN` (sec.67.4.14,
            // p. 3451, paso 3 del cierre; `CFG1` esta protegido con `SPE = 1`,
            // sec.67.11.1, p. 3484).
            regs.cr1().modify(|w| w.set_spe(false));
            regs.cfg1().modify(|w| {
                w.set_txdmaen(false);
                w.set_rxdmaen(false);
            });
        }
    }
}

/// El esclavo como tarea del ejecutor del J2 (R-MJ5). La lanza el binario con
/// `EJECUTOR_J2.spawner()` despues de `j2_ejecutor::arrancar`.
///
/// Una sola: hay un esclavo, el del banco, en SPI4.
#[embassy_executor::task]
pub async fn tarea_esclavo(esclavo: Esclavo<'static>) -> ! {
    esclavo.correr().await
}

/// `SendSpawner::spawn` exige `S: Send` (`embassy-executor/src/spawner.rs:223`)
/// y el `InterruptExecutor` del J2 **solo** da un `SendSpawner`, asi que lo que
/// tiene que ser `Send` es **el futuro** de [`Esclavo::correr`], no el
/// `Esclavo`: el futuro se queda dentro todo lo que siga vivo a traves de un
/// `.await`, y ahi es donde entra un `*mut u8` que no lo es -- que es el
/// defecto que cazo la ronda de arreglo 1: los punteros a `TXDR`/`RXDR` vivian
/// fuera del lazo. Un aserto sobre `Esclavo<'static>` no lo habria visto.
///
/// Esta funcion no la llama nadie y no llega al binario: existe para que el
/// compilador tenga que construir el futuro y comprobarlo. `Esclavo: Send` va
/// implicito, porque `correr` se lo lleva por valor.
#[allow(dead_code)]
fn _el_futuro_de_la_tarea_es_send(e: Esclavo<'static>) {
    fn exige<F: Send>(_: F) {}
    exige(e.correr());
}

/// El bufer de recepcion tiene que caber en un bloque del GPDMA (`BNDT` es de
/// 16 bits) y el contador de `correr` resta sobre `LARGO_MAX`: si alguien
/// subiera `LARGO_MAX` por encima de 0xFFFF, `get_remaining_transfers` (u16) ya
/// no podria describir lo que falta y la cuenta de bytes mentiria en silencio.
const _: () = assert!(LARGO_MAX <= u16::MAX as usize);
