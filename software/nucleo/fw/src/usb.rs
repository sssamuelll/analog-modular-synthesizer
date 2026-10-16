//! El borde del sistema: bytes que entran y salen por el USB.
//!
//! El lazo entero, y por que no lleva un solo test propio — **cada paso ya
//! vino verde en `core`**:
//!
//! ```text
//!   paquete USB  ->  Desempaquetador  ->  desenvolver  ->  decodificar
//!                                                               |
//!                                                      Instrumento::atender
//!                                                               |
//!      MidiClass  <-  empaquetar_sysex  <-  envolver  <-  codificar
//! ```

use defmt::{info, warn};
use embassy_futures::select::{select, Either};
use embassy_stm32::peripherals::USB1_OTG_HS;
use embassy_stm32::rcc::mux::{Otgphysel, Rtcsel};
use embassy_stm32::rcc::{
    CpuClk, Hse, HseMode, IcConfig, Icint, Icsel, Pll, Plldivm, Pllpdiv, Pllsel, SupplyConfig,
    SysClk, HSI_FREQ,
};
use embassy_stm32::time::Hertz;
use embassy_stm32::usb::{Driver, InterruptHandler};
use embassy_stm32::Peri;
use embassy_time::{Duration, Instant, Timer};
use embassy_usb::class::midi::MidiClass;
use embassy_usb::{Builder, Config, UsbDevice};
use sam17_nucleo_core::descriptor;
use sam17_nucleo_core::politica::Puerta;
use sam17_nucleo_core::protocolo::{codificar, decodificar, Mensaje};
use sam17_nucleo_core::servidor::{Instrumento, Respuesta};
use sam17_nucleo_core::sysex::{desenvolver, envolver, largo_empaquetado};
use sam17_nucleo_core::usbmidi::{empaquetar_sysex, Desempaquetador, Paquete, Trozo, MAX_SYSEX};
use static_cell::StaticCell;

embassy_stm32::bind_interrupts!(pub struct Irqs {
    USB1_OTG_HS => InterruptHandler<USB1_OTG_HS>;
});

/// La configuracion del reloj que el USB del N657 EXIGE, y que hay que tener
/// lista antes de `embassy_stm32::init`.
///
/// Dos cosas cuelgan el arranque si se dejan por defecto, y hay una tercera
/// que no lo cuelga pero arma una errata: `RTCSEL` (la ultima linea, con su
/// cita).
///
/// 1. **El reloj de referencia del PHY** tiene que ser 19,2, 20 o 24 MHz
///    exactos (RM0486 Rev 4, `USBPHYC_CR.FSEL`, p. 3929), y **sale del
///    cristal**: el HSE de 48 MHz de la Nucleo (X3, UM3417 Rev 3 §7.7.2,
///    p. 24) partido en dos, `hse_div2_ck` = 24 MHz, que es ademas el valor de
///    reset de `OTGPHY1SEL` (`00`, RM0486 Rev 4, p. 535).
///
///    Medido en placa el 2026-10-01: con la referencia de HSI -> PLL4 -> IC15
///    a 24 MHz (lo que habia aqui, «para no depender del cristal») el PHY no se
///    presenta nunca en el bus -- D+ y D- en SE0, Windows no ve nada --; con el
///    HSE ÷ 2 enumera a alta velocidad. Es lo que hace el ejemplo USB de ST
///    para esta placa. **Si la placa del hub lleva o no cristal es decision
///    abierta**: ver el comentario del 2026-10-01 en #150.
///
/// 2. **De donde sale el nucleo.** La Discovery lleva SMPS externo (UM3300
///    Tab. 6 segun el ejemplo de embassy) y con el interno el `init` se queda
///    colgado en `VOSRDY`. El SAM17 lleva el conmutado INTERNO del chip
///    (`2026-08-31-alimentacion-n657-design.md`, y es el que #256 no puede
///    dimensionar sin la columna de 85 C), que es ademas el defecto de
///    embassy: en la placa del instrumento esta linea se BORRA, no se cambia.
///
/// ponytail: una sola configuracion, la de la placa que existe. Cuando haya
/// dos placas de verdad, sera un parametro y no un `if`.
pub fn configuracion() -> embassy_stm32::Config {
    let mut config = embassy_stm32::Config::default();
    config.rcc.supply_config = SupplyConfig::External;
    config.rcc.hse = Some(Hse {
        freq: Hertz(48_000_000),
        mode: HseMode::Oscillator,
    });
    config.rcc.mux.otgphy1sel = Otgphysel::HseDiv2;

    // RTCSEL a su valor de reset, y no por gusto: sin esta linea el firmware
    // lo deja en `0x0` en operacion NORMAL y sale del `init` ya armado para la
    // errata ES0620 Rev 5 §2.2.22 (p. 12), que exige los diez selectores de
    // reloj en su defecto antes de un reset por software. RTCSEL es el unico
    // de los diez cuyo defecto no es cero, y lo confirma el reset de
    // `RCC_CCIPR7`: `0x0000_0200` (RM0486 Rev 4, p. 536) es el bit 9 puesto, y
    // RTCSEL son los bits [9:8] -- o sea `0b10`, lsi_ck (p. 537).
    //
    // Lo deja en `0x0` un fallo de embassy: `config.ls.init()`
    // (`rcc/n6.rs:1038`) escribe `RTCSEL = Lsi`, y despues `config.mux.init()`
    // (`rcc/n6.rs:1389`) lo pisa desde un `ClockMux` que por defecto es
    // `mem::zeroed()`. Con el chip asi, un `SYSRESETREQ` -- el de `probe-rs`
    // al cargar, sin ir mas lejos -- cae en la errata. Ver `reinicio.rs` y
    // ARRANQUE.md.
    //
    // `config.rcc.ls` NO hace falta tocarlo: su defecto ya es `default_lsi()`
    // (`rcc/bd.rs`), que enciende el LSI y espera `LSIRDY`, asi que lsi_ck
    // esta puesto.
    //
    // ponytail: es un parche a un fallo aguas arriba; se borra el dia que la
    // rama de embassy deje de pisar `ls.init` con `mux.init`.
    config.rcc.mux.rtcsel = Rtcsel::Lsi; // RTCSEL = 0x2 (ES0620 p. 12)

    config
}

/// La misma configuracion con el reloj de diseno del hub: **el nucleo a 800 MHz**,
/// el punto del papel de alimentacion (*«VOS high a 800 MHz»*).
///
/// El PLL1 sale del HSE de 48 MHz (el cristal, como en la placa del hub y como
/// el PHY del USB): `48 / 3 x 50 = 800 MHz`, sin divisores de salida. `IC1` es
/// el nucleo y `IC2` el reloj de sistema, a 200 MHz; `IC6` e `IC11` los pide el
/// ejemplo de embassy para el N6 (`examples/stm32n6/src/bin/eth_speedtest.rs`,
/// `rcc_config`) con el mismo divisor, y se copian sin entenderlos del todo.
/// Los divisores de bus son los de embassy (AHB /2, APB /1): hclk y pclk a
/// 100 MHz, asi que el kernel de los SPI sale de ahi y el `MBR` cae en /16
/// (6,25 MHz): no es el `f_sck` del hub, que no esta decidido (#380).
///
/// **Es solo para el banco de carga.** No cambia la tension: `VoltageScale::Scale0`
/// ya es el defecto de embassy y el que usa `configuracion`, con el SMPS
/// externo de la Nucleo.
pub fn configuracion_hub() -> embassy_stm32::Config {
    let mut config = configuracion();
    config.rcc.pll1 = Some(Pll::Oscillator {
        source: Pllsel::Hse,
        divm: Plldivm::Div3,
        fractional: 0,
        divn: 50,
        divp1: Pllpdiv::Div1,
        divp2: Pllpdiv::Div1,
    });
    config.rcc.ic1 = Some(IcConfig {
        source: Icsel::Pll1,
        divider: Icint::Div1,
    });
    let sys_ic = IcConfig {
        source: Icsel::Pll1,
        divider: Icint::Div4,
    };
    config.rcc.ic2 = Some(sys_ic);
    config.rcc.ic6 = Some(sys_ic);
    config.rcc.ic11 = Some(sys_ic);
    config.rcc.cpu = CpuClk::Ic1;
    config.rcc.sys = SysClk::Ic2;
    config
}

/// La unica puerta a `embassy_stm32::init`: la usan `main` y los cuatro
/// binarios del banco.
///
/// Existe por una linea que no es nuestra. probe-rs 0.32 carga el binario en
/// RAM y lo arranca con **`PRIMASK = 1`**: su secuencia del N6
/// (`reset_catch_clear`) escribe `EXTRA = 1` «since the NVIC state is
/// unknown» y nadie lo vuelve a bajar, porque entre esa escritura y nuestro
/// reset handler no hay reset (probe-rs/probe-rs#4390). Sin esta funcion no
/// llega ninguna interrupcion: medido en placa el 2026-10-01, el host reseteaba
/// el bus y el driver USB no se enteraba, y los cuatro binarios del J2 -- que
/// viven del `EOT`, del DMA, del `EXTI11` y del ejecutor de `GFXTIM` -- habrian
/// dado cada giro por plazo vencido.
///
/// Antes de desenmascarar se apagan y limpian todas las lineas del NVIC, que
/// es lo que probe-rs temia: la ROM pudo dejar alguna puesta -- su LPTIM4 sigue
/// vivo cuando arranca el codigo, ES0620 Rev 5 §2.9.4 -- y saltaria a un
/// manejador que no existe. Las que hacen falta las enciende `init` despues.
/// En un arranque de verdad `PRIMASK` ya vale 0 y esto no cambia nada.
pub fn iniciar(config: embassy_stm32::Config) -> embassy_stm32::Peripherals {
    // SAFETY: antes de `init` no hay ningun manejador de interrupcion vivo ni
    // seccion critica abierta; con todas las lineas apagadas, desenmascarar no
    // puede disparar nada.
    unsafe {
        let nvic = &*cortex_m::peripheral::NVIC::PTR;
        for i in 0..nvic.icer.len() {
            nvic.icer[i].write(u32::MAX);
            nvic.icpr[i].write(u32::MAX);
        }
        cortex_m::interrupt::enable();
    }
    embassy_stm32::init(config)
}

/// El reloj del **nucleo** en hercios, sacado de la MISMA `Config` que lo
/// construye.
///
/// Existe porque el `Clocks` que embassy publica no trae `cpuclk`: su
/// `set_clocks!` del N6 exporta `sys: Some(clocks.sysclk)` y deja `cpuclk`
/// dentro de `ClocksOutput` sin publicar (`rcc/n6.rs:1392` y `:244`). Y el
/// retardo de `j2_spi` se cuenta con `cortex_m::asm::delay`, que cuenta ciclos
/// del **nucleo**, no del bus: usar el sysclk ahi da un retardo corto en
/// silencio el dia que el CPU salga de IC1 por encima del sysclk.
///
/// La cuenta es la misma expresion de `rcc/n6.rs:409-414`
/// (`CpuClk::Hsi => unwrap!(input.hsi)`), y `input.hsi` es el `hsi_ck` **crudo**
/// de 64 MHz (`rcc/n6.rs:988`, `HSI_FREQ`): el prescaler `HSIDIV` NO entra
/// aqui, porque alimenta el `hsi_div_ck`, que es otra salida del bloque
/// (RM0486 Rev 4 sec.14.4.5; el propio comentario de embassy en `n6.rs:965-976`
/// lo explica). Los 64 MHz: DS14791 Rev 10, p. 2, *"Internal oscillators:
/// 64 MHz HSI"*.
///
/// **Por `IC1`** (el reloj del hub, [`configuracion_hub`]) la cuenta sale del
/// PLL1 y del divisor de `IC1`, y se niega a redondear: una division inexacta
/// seria un reloj que no es el que se cree. Cualquier otra fuente **cuelga a
/// la vista**: preferimos un panico en el arranque a un retardo corto que
/// nadie mide. Cuando embassy publique `cpuclk` en `Clocks` (una linea en el
/// `set_clocks!`, #376) esta funcion se retira.
pub fn f_cpu_hz(config: &embassy_stm32::Config) -> u32 {
    match config.rcc.cpu {
        CpuClk::Hsi => HSI_FREQ.0,
        CpuClk::Ic1 => f_ic1_hz(config),
        _ => defmt::panic!(
            "f_cpu_hz: la CPU no corre por HSI ni IC1; publica cpuclk (issue #376) antes de mover el reloj"
        ),
    }
}

/// `IC1 = PLL1 / divider`, con `PLL1 = f_in / divm x divn / (divp1 x divp2)`.
fn f_ic1_hz(config: &embassy_stm32::Config) -> u32 {
    let Some(Pll::Oscillator {
        source,
        divm,
        fractional,
        divn,
        divp1,
        divp2,
    }) = config.rcc.pll1
    else {
        defmt::panic!("f_cpu_hz: IC1 sin PLL1 en modo oscilador")
    };
    let Some(ic1) = config.rcc.ic1 else {
        defmt::panic!("f_cpu_hz: CpuClk::Ic1 sin IC1 configurado")
    };
    defmt::assert!(ic1.source == Icsel::Pll1, "f_cpu_hz: IC1 no sale del PLL1");
    defmt::assert!(fractional == 0, "f_cpu_hz: PLL1 fraccionario");
    let f_in = match source {
        Pllsel::Hsi => HSI_FREQ.0,
        Pllsel::Hse => match config.rcc.hse {
            Some(hse) => hse.freq.0,
            None => defmt::panic!("f_cpu_hz: PLL1 desde HSE con el HSE apagado"),
        },
        _ => defmt::panic!("f_cpu_hz: fuente de PLL1 que no es HSI ni HSE"),
    };
    // Los enums del PAC son `repr(u8)` y su valor es el divisor (`Div4 = 4`); el de
    // `Icint` va uno por debajo (`Div1 = 0`).
    let (m, n, p) = (divm as u32, divn as u32, divp1 as u32 * divp2 as u32);
    let ic = ic1.divider as u32 + 1;
    defmt::assert!(
        m != 0 && p != 0 && f_in % m == 0 && (f_in / m * n) % (p * ic) == 0,
        "f_cpu_hz: la cuenta del PLL1 y de IC1 no sale exacta"
    );
    f_in / m * n / (p * ic)
}

/// El driver de USB del cerebro.
///
/// Los dos OTG del N6 son **solo High Speed** y atacan un PHY UTMI+ integrado
/// por bolas dedicadas (`OTG1_HSDP` / `OTG1_HSDM`): el driver no toma pines de
/// D+/D-, y por eso el constructor es `new_hs_dedicated_pins`.
pub fn driver(p: Peri<'static, USB1_OTG_HS>) -> Driver<'static, USB1_OTG_HS> {
    // La FIFO de salida es una sola para todos los endpoints OUT. 1 KB es lo
    // que usa el ejemplo del N6, y con un solo endpoint OUT de 512 B sobra.
    static EP_OUT: StaticCell<[u8; 1024]> = StaticCell::new();

    let mut config = embassy_stm32::usb::Config::default();
    // El N657 NO TIENE deteccion de VBUS por hardware, y esto no es una
    // eleccion nuestra: RM0486 Rev 4, `OTG_GCCFG`, p. 3815 -- *«In this device,
    // the software override is always active (no hardware detection is
    // available)»*. El PHY va cableado en modo comparador externo y ni siquiera
    // llega a VBUS (p. 3756: *«forced in external comparator mode and not
    // connected to VBUS»*), y el encapsulado no publica bola de VBUS: el censo
    // de las tablas 18-20 de DS14791 Rev 10 (pp. 89-133) solo da `OTG1_ID` en
    // C3, que en modo periferico el manual ignora (p. 3766).
    //
    // Asi que `vbus_detection` se queda en `false` PARA SIEMPRE en este chip.
    // Lo que falta es lo otro, y es de la placa. El manual lo escribe entero,
    // p. 3766: *«External circuitry should be used to detect presence of a
    // voltage on the VBUS connector pin»*, *«The B-peripheral VBUS detection
    // should be overridden with OTG_GOTGCTL.BVALOEN = 1»*, y el resultado
    // *«should be maintained by writing the current value to
    // OTG_GOTGCTL.BVALOVAL»*.
    //
    // En embassy eso es `vbus_valid_override = true` (deja `BVALOEN = 1` y no
    // toca `BVALOVAL`, para que lo escriba la aplicacion). Hoy va en `false`,
    // y eso pone `BVALOVAL = 1` fijo: **el cerebro cree que el cable esta
    // siempre puesto**. Es la mentira conocida, y es del #350: pide divisor de
    // VBUS a un GPIO (el N657 tolera 3,6 V en una TT, no 5) y el esquematico
    // del hub, que no existe.
    config.vbus_detection = false;

    Driver::new_hs_dedicated_pins(p, Irqs, EP_OUT.init([0; 1024]), config)
}

/// `0x1209` es pid.codes, el rango libre para proyectos abiertos. El PID es de
/// pruebas: registrar uno de verdad es del dia que esto se distribuya, y esta
/// anotado en EN-PLACA.md.
const VID: u16 = 0x1209;
const PID: u16 = 0x0017;

/// 512 bytes, y no es una eleccion: es el UNICO valor legal para un endpoint
/// bulk a high speed (USB 2.0 sec.5.8.3 -- a full speed son 8, 16, 32 o 64).
///
/// El 64 que habia aqui venia del RP2350, que enumera a full speed. Este chip
/// no puede: los dos OTG del N6 son **solo High Speed** y atacan el PHY UTMI+
/// integrado -- esta escrito treinta lineas mas arriba, en `driver()`. Con 64
/// el descriptor que sale por el cable es invalido, y eso no lo descubre el
/// enlace: lo descubre el host al enumerar.
///
/// HUECO: sin placa (#231) nadie ha visto enumerar esto. Lo que se sabe es que
/// 64 esta mal; que 512 baste se comprueba en el bring-up.
const TAM_PAQUETE: u16 = 512;

// El buffer de lectura se DERIVA de esta constante (`[0u8; TAM_PAQUETE as
// usize]`), asi que la invariante "el buffer es al menos el tamano de endpoint"
// se cumple por construccion y no hay nada que aseverar. Aqui llego a haber un
// `const assert!(TAM_PAQUETE >= 4)`, que no comprobaba esa invariante sino otra
// trivial: un aval que se lee como puerta y no lo es.

/// Lo que ocupa UN descriptor ya metido en su sobre de SysEx.
///
/// Era `384`, un literal a ojo dentro de `mandar_descriptores`, justo al lado
/// de un `MAX_DESCRIPTOR_B` que si se leia de `core`. Sobraba, pero sobraba
/// por casualidad: nadie habia escrito la cuenta y nada la rehacia si
/// `MAX_DESCRIPTOR_B` subiera -- que es exactamente lo que una de las dos
/// ramas de N4 propone hacer.
///
/// La cuenta, con las dos piezas citadas de `core::sysex`:
///
/// ```text
///   empaquetado 7-a-8   largo_empaquetado(256) = 256 + ceil(256/7) = 293
///   sobre               F0 + 0x7D + ... + F7                       =   3
///                                                                    ---
///                                                                    296
/// ```
///
/// Ya no se escribe el 296: se deriva, para que la cuenta la rehaga el
/// compilador y no la memoria de nadie.
const MAX_SOBRE_B: usize = 3 + largo_empaquetado(descriptor::MAX_DESCRIPTOR_B);

pub type Sam17Usb = UsbDevice<'static, Driver<'static, USB1_OTG_HS>>;

pub struct Puertos {
    pub dispositivo: Sam17Usb,
    pub midi: MidiClass<'static, Driver<'static, USB1_OTG_HS>>,
}

pub fn montar(driver: Driver<'static, USB1_OTG_HS>) -> Puertos {
    let mut config = Config::new(VID, PID);
    config.manufacturer = Some("SAM17");
    config.product = Some("SAM17 nucleo");
    config.serial_number = Some("0001");
    config.max_power = 100;
    config.max_packet_size_0 = 64;

    static CONFIG_DESC: StaticCell<[u8; 256]> = StaticCell::new();
    static BOS_DESC: StaticCell<[u8; 256]> = StaticCell::new();
    static CONTROL_BUF: StaticCell<[u8; 64]> = StaticCell::new();

    let mut builder = Builder::new(
        driver,
        config,
        CONFIG_DESC.init([0; 256]),
        BOS_DESC.init([0; 256]),
        &mut [],
        CONTROL_BUF.init([0; 64]),
    );

    // Un jack de entrada y uno de salida: el instrumento habla y escucha.
    let midi = MidiClass::new(&mut builder, 1, 1, TAM_PAQUETE);

    Puertos {
        dispositivo: builder.build(),
        midi,
    }
}

#[embassy_executor::task]
pub async fn correr_usb(mut d: Sam17Usb) -> ! {
    d.run().await
}

/// Cada cuanto se le dice al instrumento que hora es.
///
/// A 120 BPM un pulso interno dura 5,2 ms (PPQN_INTERNO = 96), asi que 1 ms da
/// cinco tics por pulso; a 300 BPM, dos. Es resolucion de sobra para que el
/// planeo de una rampa no se vea escalonado, y el coste es un `select` que ya
/// estaba ahi.
///
/// DECLARADO, no medido: no hay medida del coste de CPU de este lazo ni del
/// jitter que mete el volcado de descriptores reteniendo el `await`. Sale de
/// `arranque_budget.py` el dia que exista (#180).
const PERIODO_TICK: Duration = Duration::from_millis(1);

/// Un tic: se le dice la hora al instrumento y se manda lo que conteste.
///
/// Son DOS llamadas a proposito. `avanzar_a` no caduca las retenidas porque
/// las aserciones `const` del buzon acotan los caminos por separado; meterlas
/// en el mismo `Respuestas` podria desbordarlo.
async fn correr_el_reloj(
    midi: &mut MidiClass<'static, Driver<'static, USB1_OTG_HS>>,
    instrumento: &mut Instrumento,
) -> Result<(), ()> {
    let ahora = Instant::now();
    for resp in instrumento.avanzar_a(ahora.as_micros()) {
        responder(midi, instrumento, resp).await?;
    }
    for resp in instrumento.caducar(ahora.as_millis()) {
        responder(midi, instrumento, resp).await?;
    }
    Ok(())
}

/// El lazo. Todo lo que hace es cablear piezas ya probadas.
#[embassy_executor::task]
pub async fn atender(
    mut midi: MidiClass<'static, Driver<'static, USB1_OTG_HS>>,
    instrumento: &'static mut Instrumento,
) -> ! {
    let mut desemp = Desempaquetador::nuevo();
    // `read_packet` EXIGE un buffer del tamano del endpoint. embassy-usb lo
    // dice textualmente (`class/midi.rs`): "read_packet must be called with a
    // buffer large enough to hold max_packet_size bytes".
    //
    // Aqui habia un `[0; 4]` contra un endpoint declarado de 64, y no fallaba
    // suave: embassy-rp devuelve `BufferOverflow` ANTES de re-armar el
    // endpoint, asi que el hardware no vuelve a aceptar un paquete nunca; el
    // `Err` de abajo lo leia como desconexion, `wait_connection` contestaba
    // listo al primer poll porque el endpoint sigue habilitado, y vuelta a
    // empezar. Ningun poll de ese ciclo devuelve `Pending`: la tarea gira para
    // siempre dentro de un solo `poll()` y se lleva por delante la pila USB y
    // el reloj. Bastaba con que el host agrupara eventos en una transferencia,
    // que es lo normal y es para lo que sirve declarar el tamano entero del
    // endpoint. (Aquel 64 era del RP2350, a full speed; aqui son 512.)
    let mut entrada = [0u8; TAM_PAQUETE as usize];
    let mut plano = [0u8; MAX_SYSEX];
    let mut proximo = Instant::now() + PERIODO_TICK;

    loop {
        // El reloj corre HAYA O NO cliente. Esto es un instrumento, no un
        // periferico: si nadie ha abierto el puerto MIDI, las rampas tienen
        // que seguir escribiendo igual y la posicion del compas tiene que
        // seguir siendo verdad. Por eso el tic tambien compite con la espera
        // de conexion, y no solo con la lectura.
        loop {
            match select(midi.wait_connection(), Timer::at(proximo)).await {
                Either::First(()) => break,
                Either::Second(()) => {
                    proximo += PERIODO_TICK;
                    // Sin cliente no hay a quien contestar: se deja correr el
                    // estado y se tiran las respuestas a proposito.
                    let _ = instrumento.avanzar_a(Instant::now().as_micros());
                    let _ = instrumento.caducar(Instant::now().as_millis());
                }
            }
        }
        info!("USB: un cliente se conecto");
        desemp.reiniciar();

        loop {
            let leido = match select(midi.read_packet(&mut entrada), Timer::at(proximo)).await {
                Either::First(r) => r,
                Either::Second(()) => {
                    proximo += PERIODO_TICK;
                    if correr_el_reloj(&mut midi, instrumento).await.is_err() {
                        break;
                    }
                    continue;
                }
            };
            let n = match leido {
                Ok(n) => n,
                Err(_) => break, // se desconecto; a esperar de nuevo
            };
            // Un bulk de 512 B trae HASTA CIENTO VEINTIOCHO paquetes USB-MIDI de 4, y
            // antes solo se miraba el caso de uno suelto: `Ok(4) => {}` y
            // cualquier otra cosa a la basura. O sea que en cuanto el host
            // agrupara, se tiraba la transferencia entera.
            if n % 4 != 0 {
                warn!("USB: transferencia de {} B, no es multiplo de 4", n);
            }
            let mut caido = false;
            for trozo in entrada[..n].chunks_exact(4) {
                let Ok(paquete) = <&Paquete>::try_from(trozo) else {
                    continue;
                };
                let bytes = match desemp.empujar(paquete) {
                    Some(Trozo::Midi(bytes)) => {
                        let _ = instrumento.midi(&bytes);
                        continue;
                    }
                    Some(Trozo::Sysex(bytes)) => bytes,
                    None => continue,
                };
                let Ok(largo) = desenvolver(bytes, &mut plano) else {
                    warn!("USB: sobre que no es nuestro, se ignora");
                    continue;
                };
                let Ok(m) = decodificar(&plano[..largo]) else {
                    warn!("USB: mensaje que no se entiende");
                    continue;
                };

                let ahora = embassy_time::Instant::now().as_millis();
                // N1. Aqui es donde se estampa: este lazo ES la puerta USB,
                // asi que lo sabe por construccion y el mensaje no tuvo que
                // decirlo. Cuando entre el puente inalambrico, su lazo
                // estampara `Inalambrica` y ninguno de los dos podra
                // equivocarse, porque ninguno lee el dato: lo pone.
                //
                // Lo que esto NO separa: el agente por MCP y una carcasa web
                // entran los dos por aqui y salen los dos como `Usb`. Se
                // separaran cuando se lea el nibble de cable (#182, fallo 7).
                for resp in instrumento.atender(m, ahora, Puerta::Usb) {
                    if responder(&mut midi, instrumento, resp).await.is_err() {
                        caido = true;
                        break;
                    }
                }
                if caido {
                    break;
                }
            }
            if caido {
                break;
            }
        }
    }
}

async fn responder(
    midi: &mut MidiClass<'static, Driver<'static, USB1_OTG_HS>>,
    instrumento: &Instrumento,
    resp: Respuesta,
) -> Result<(), ()> {
    match resp {
        Respuesta::Mensaje(m) => mandar_mensaje(midi, &m).await,
        Respuesta::Descriptores => mandar_descriptores(midi, instrumento).await,
    }
}

async fn mandar_mensaje(
    midi: &mut MidiClass<'static, Driver<'static, USB1_OTG_HS>>,
    m: &Mensaje,
) -> Result<(), ()> {
    let mut plano = [0u8; 64];
    let n = codificar(m, &mut plano).map_err(|_| ())?;
    let mut sobre = [0u8; 128];
    let s = envolver(&plano[..n], &mut sobre).map_err(|_| ())?;
    mandar_sysex(midi, &sobre[..s]).await
}

/// El volcado del descriptor: uno por sobre. Mandarlos de a uno mantiene los
/// buffers pequeños y deja que el cliente empiece a parsear antes de que
/// termine — que con 27 medidas ya se nota.
async fn mandar_descriptores(
    midi: &mut MidiClass<'static, Driver<'static, USB1_OTG_HS>>,
    instrumento: &Instrumento,
) -> Result<(), ()> {
    // B3, el contrato del volcado. La cabecera va ANTES del primer descriptor
    // y dice cuantos vienen; el cierre va al final y dice cuantos salieron de
    // verdad. Con las dos, el cliente distingue por fin las tres cosas que
    // hasta hoy le llegaban identicas: «termino», «se aborto» y «todavia
    // viene». Y si `enviados` no cuadra con `n`, alguno se salto -- que es un
    // caso REAL, dos lineas mas abajo, y era invisible desde el otro lado.
    let n = instrumento.modelo().descriptores().count() as u16;
    let huella = instrumento.modelo().huella();
    mandar_mensaje(midi, &Mensaje::VolcadoInicio { n, huella }).await?;

    let mut enviados: u16 = 0;
    let mut plano = [0u8; descriptor::MAX_DESCRIPTOR_B];
    let mut sobre = [0u8; MAX_SOBRE_B];
    for d in instrumento.modelo().descriptores() {
        // Antes esto era `?`, o sea que UN descriptor que no cupiera se
        // llevaba por delante el volcado ENTERO y el cliente se quedaba con un
        // modelo a medias sin saberlo (#182, fallo 5). Saltarselo tampoco es
        // bonito, pero mandar 300 descriptores menos uno es estrictamente
        // mejor que mandar los que dio tiempo antes de reventar.
        //
        // La puerta que impide llegar aqui vive en core (descriptor.rs,
        // `ningun_descriptor_compilado_se_acerca_al_techo_del_volcado`) y salta
        // al 75 % del techo. Esto es el cinturon, no el freno -- y hoy el freno
        // solo agarra los descriptores COMPILADOS: los de modulo llegan por
        // I2C y el peor caso declarado ya mide 250 B de 256 (N4).
        let Ok(n) = descriptor::escribir(d, &mut plano) else {
            warn!("USB: un descriptor no cabe en el volcado, se salta");
            continue;
        };
        // Y este era el MISMO fallo 5, una linea mas abajo y sin arreglar:
        // `escribir` ya no abortaba el volcado, pero `envolver` si. Un solo
        // sobre que no quepa no tiene por que llevarse los otros doscientos
        // noventa y nueve.
        //
        // Por construccion no puede fallar: `MAX_SOBRE_B` es exactamente lo
        // que ocupa envuelto un plano de `MAX_DESCRIPTOR_B`. Justamente por
        // eso el dia que falle sera porque alguien movio una de las dos
        // constantes, que es cuando menos falta hace que se caiga todo.
        let Ok(s) = envolver(&plano[..n], &mut sobre) else {
            warn!("USB: un sobre no cabe en el buffer, se salta");
            continue;
        };
        // Este `?` SI se queda: si el USB se cayo no hay volcado que salvar,
        // y el `warn` de arriba tampoco iba a salir por ningun lado.
        mandar_sysex(midi, &sobre[..s]).await?;
        enviados += 1;
    }
    // Aqui vivia una nota diciendo que el terminador era un cambio de FORMATO
    // y lo decidia N4 del pase del nucleo. N4 se cedio a B3, B3 se decidio el
    // 2026-08-24, y esto es la decision.
    //
    // El `?` se queda por lo mismo que el de arriba: si el USB se cayo no hay
    // volcado que cerrar. Un cliente que no recibe el cierre tiene que leerlo
    // como «se aborto», que es exactamente lo que paso.
    mandar_mensaje(midi, &Mensaje::VolcadoFin { enviados }).await?;
    Ok(())
}

async fn mandar_sysex(
    midi: &mut MidiClass<'static, Driver<'static, USB1_OTG_HS>>,
    sobre: &[u8],
) -> Result<(), ()> {
    let mut paquetes = [[0u8; 4]; MAX_SYSEX / 3 + 1];
    let np = empaquetar_sysex(sobre, &mut paquetes).map_err(|_| ())?;
    for p in &paquetes[..np] {
        midi.write_packet(p).await.map_err(|_| ())?;
    }
    Ok(())
}
