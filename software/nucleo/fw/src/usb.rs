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
use embassy_time::{Duration, Instant, Timer};
use embassy_rp::peripherals::USB;
use embassy_rp::usb::{Driver, InterruptHandler};
use embassy_usb::class::midi::MidiClass;
use embassy_usb::{Builder, Config, UsbDevice};
use sam17_nucleo_core::descriptor;
use sam17_nucleo_core::protocolo::{codificar, decodificar, Mensaje};
use sam17_nucleo_core::servidor::{Instrumento, Respuesta};
use sam17_nucleo_core::sysex::{desenvolver, envolver, largo_empaquetado};
use sam17_nucleo_core::usbmidi::{empaquetar_sysex, Desempaquetador, Paquete, Trozo, MAX_SYSEX};
use static_cell::StaticCell;

embassy_rp::bind_interrupts!(pub struct Irqs {
    USBCTRL_IRQ => InterruptHandler<USB>;
});

/// `0x1209` es pid.codes, el rango libre para proyectos abiertos. El PID es de
/// pruebas: registrar uno de verdad es del dia que esto se distribuya, y esta
/// anotado en EN-PLACA.md.
const VID: u16 = 0x1209;
const PID: u16 = 0x0017;

/// 64 bytes es el maximo de un endpoint bulk a full speed.
const TAM_PAQUETE: u16 = 64;

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

pub type Sam17Usb = UsbDevice<'static, Driver<'static, USB>>;

pub struct Puertos {
    pub dispositivo: Sam17Usb,
    pub midi: MidiClass<'static, Driver<'static, USB>>,
}

pub fn montar(driver: Driver<'static, USB>) -> Puertos {
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

    Puertos { dispositivo: builder.build(), midi }
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
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
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
    mut midi: MidiClass<'static, Driver<'static, USB>>,
    instrumento: &'static mut Instrumento,
) -> ! {
    let mut desemp = Desempaquetador::nuevo();
    let mut entrada: Paquete = [0; 4];
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
            match leido {
                Ok(4) => {}
                Ok(n) => {
                    // USB-MIDI son paquetes de cuatro bytes. Otra cosa no es
                    // nuestra: se tira sin tocar el mensaje en curso.
                    warn!("USB: paquete de {} bytes, se ignora", n);
                    continue;
                }
                Err(_) => break, // se desconecto; a esperar de nuevo
            }

            let Some(Trozo::Sysex(bytes)) = desemp.empujar(&entrada) else {
                // Notas y CC son del plan de los perifericos: todavia no hay
                // gates ni J2 a donde mandarlas.
                continue;
            };

            let Ok(n) = desenvolver(bytes, &mut plano) else {
                warn!("USB: sobre que no es nuestro, se ignora");
                continue;
            };
            let Ok(m) = decodificar(&plano[..n]) else {
                warn!("USB: mensaje que no se entiende");
                continue;
            };

            let ahora = embassy_time::Instant::now().as_millis();
            for resp in instrumento.atender(m, ahora) {
                if responder(&mut midi, instrumento, resp).await.is_err() {
                    break;
                }
            }
        }
    }
}

async fn responder(
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
    instrumento: &Instrumento,
    resp: Respuesta,
) -> Result<(), ()> {
    match resp {
        Respuesta::Mensaje(m) => mandar_mensaje(midi, &m).await,
        Respuesta::Descriptores => mandar_descriptores(midi, instrumento).await,
    }
}

async fn mandar_mensaje(
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
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
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
    instrumento: &Instrumento,
) -> Result<(), ()> {
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
    }
    // NO se manda terminador ni conteo: el cliente sigue sin poder distinguir
    // "termino" de "falto uno", y ahora hay DOS sitios que se saltan uno en
    // silencio. Eso es correcto y es lo que hay: el terminador es un cambio de
    // FORMATO y lo decide N4 del pase del nucleo -- aqui no se inventa. Lo
    // unico que se puede hacer sin tocar el formato es lo de arriba: dejar
    // rastro en el log del propio instrumento.
    Ok(())
}

async fn mandar_sysex(
    midi: &mut MidiClass<'static, Driver<'static, USB>>,
    sobre: &[u8],
) -> Result<(), ()> {
    let mut paquetes = [[0u8; 4]; MAX_SYSEX / 3 + 1];
    let np = empaquetar_sysex(sobre, &mut paquetes).map_err(|_| ())?;
    for p in &paquetes[..np] {
        midi.write_packet(p).await.map_err(|_| ())?;
    }
    Ok(())
}
