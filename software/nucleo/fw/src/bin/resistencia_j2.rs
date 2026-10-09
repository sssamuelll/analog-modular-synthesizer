#![no_std]
#![no_main]

//! **El soak del J2: el punto (3) del orden del dia, y la puerta de
//! fabricacion.**
//!
//! Enmienda del 11-09 a la sec.9 del papel del maestro, punto 1 (ficha 1 del
//! acta): *«Ninguna PCB con N657 sale al taller sin una fila medida en
//! `resistencia_j2.csv`. Antes era criterio de cierre del riesgo 1; desde hoy es
//! prohibicion»*. Este binario es lo que produce esa fila.
//!
//! El montaje del banco entero, tal como lo usara el instrumento: la ranura 0 en
//! **SPI5** con `TSIZE > 0` y NSS por hardware, en el `EJECUTOR_J2` con la
//! politica de `core` detras ([`j2_ejecutor::arrancar`]), y el esclavo del banco
//! en **SPI4** como tarea del mismo ejecutor. Retardo de produccion, 4 cuartos
//! de `T_SCK` (D2, enmienda del 11-09). Cada hora publica su fila.
//!
//! **Como se juzga la fila, que no es *«tiene fila»*.** Ficha 2 del acta: el
//! limite es **cero artefactos audibles** atribuibles al bus, y para ser medible
//! necesita un horizonte -- cero en cuantas horas de instrumento -- que es HUECO
//! de Samuel. La aritmetica que lo convierte en puerta: con cero eventos en `T`
//! horas de soak, la tasa queda por debajo de `3/T` al 95 % (regla de tres,
//! Poisson), y *«cero en H horas»* exige del orden de `3·H` horas limpias **con
//! el control positivo hecho**. Un soak verde sin control positivo no distingue
//! *«no nos afecta»* de *«el banco no lo ve»*: por eso este binario es el
//! tercero y no el primero.
//!
//! **Las dos tandas.** Primero el piso legado, 10 MHz; despues, si hay sancion,
//! el peldano 2 (34,5 MHz, `enlace_budget.py:71`). Se cambia [`F_SCK_HZ`] y se
//! vuelve a correr: la columna `reloj_MHz` de la fila lleva el **real**, el que
//! sale del `MBR`, no el pedido.
//!
//! **HUECO declarado (R24, #380): el peldano 2 no es alcanzable hoy.** El kernel
//! del SPI5 es `pclk2`, 32 MHz (`j2_spi::Ranura::f_sck_hz` trae de donde sale), y
//! el `MBR` mas pequeno es `/2`: `mbr_y_f_sck(32e6, 34_480_000)` devuelve **16
//! MHz**, no 34,5. Para clavar 34,5 haria falta un kernel de 69 MHz -- o 138, o
//! 276: solo 69 x 2^k lo da exacto --, y eso es elegir otra fuente del mux, que
//! es el #150 y se decide en el **#380**. Mientras tanto la segunda tanda mide
//! **16 MHz** y la columna `reloj_MHz` lo dice sola: el binario no falsea nada,
//! pero quien lea la fila tiene que saber que ese 16 no es el peldano 2. No se
//! arregla aqui.
//!
//! **Lo que no dice la fila.** `subidas_malas` cuenta contra el esclavo del
//! banco, que devuelve un patron fijo; no es el CRC del sobre, que llega con
//! #267. Y `tramas_cortas` del esclavo tiene tres causas distintas que solo el
//! analizador logico separa: estan en la cabecera de [`j2_esclavo`], y por eso
//! se publican en su propia linea junto a `plazos_vencidos`, que es la que las
//! discrimina.
//!
//! ```bash
//! cargo run --release --bin resistencia_j2
//! ```

use core::sync::atomic::Ordering;

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt;
use embassy_time::{Duration, Ticker};
use sam17_nucleo_fw::j2_banco::{
    bajada_del_banco, esclavo_del_banco, juez_del_banco, maestro_del_banco, LARGO_BANCO,
    RANURA_BANCO,
};
use sam17_nucleo_fw::j2_ejecutor::{arrancar, cuentas, EJECUTOR_J2};
use sam17_nucleo_fw::j2_esclavo;
use sam17_nucleo_fw::j2_spi::{Config, ESCALADAS_GPDMA};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// El reloj del enlace para esta tanda. **Piso legado, 10 MHz** (J2 punto a
/// punto D2; `F_CONTRATO_HZ` de `hardware/02-midi-cv/trama_j2_budget.py:89`).
/// Real: **8 MHz**, que es `32 / 4`.
///
/// La segunda tanda pide el peldano 2, `34_480_000` (D8;
/// `hardware/02-midi-cv/enlace_budget.py:71`, `F_PELDANO_2_HZ`), y **lo que va a
/// medir son 16 MHz**: el kernel es `pclk2` a 32 MHz y el `MBR` mas pequeno es
/// `/2`, asi que 34,5 esta fuera de alcance hasta el #380 (ver la cabecera del
/// modulo). Lo dice sola la columna `reloj_MHz` de la fila -- y, desde la ronda
/// de arreglo 1, la linea `firmware=` que la acompana dice con que binario.
const F_SCK_HZ: u32 = 10_000_000;

/// El retardo de produccion: 4 cuartos, o sea `>= 1 T_SCK` (D2, enmienda del
/// 11-09). El barrido de los otros cinco valores es `barrido_retardo`.
const RETARDO_CUARTOS: u8 = 4;

/// La columna `instancia` de la fila: el SPI del maestro. SPI5 a proposito, que
/// es la instancia del repro original de jake-taf (EN-PLACA, montaje del 11-09).
const INSTANCIA: &str = "SPI5";

/// La columna `nss`: `hw` = NSS por hardware del periferico (D1), no un GPIO.
const NSS: &str = "hw";

/// La columna `placa`. La `fecha` va vacia: la pone quien copia la fila.
const PLACA: &str = "NUCLEO-N657X0-Q";

/// El `f_sck` real en MHz, tal como tiene que quedar en la columna `reloj_MHz`:
/// entero cuando lo es (`8`), y con tres decimales cuando no (`0.500`).
///
/// Existe para que la fila entera salga en **un solo** `info!`: partirla en dos
/// ramas con la misma lista de doce columnas seria la forma mas facil de que una
/// de las dos se quedara atras.
struct Mhz(u32);

impl defmt::Format for Mhz {
    fn format(&self, f: defmt::Formatter) {
        let ent = self.0 / 1_000_000;
        let frac = self.0 % 1_000_000;
        if frac == 0 {
            defmt::write!(f, "{=u32}", ent)
        } else {
            // El `MBR` solo divide por potencias de dos (sec.67.11.3), asi que
            // tres decimales cubren hasta `f_ker/256` con el kernel del SPI5 en
            // `pclk2`, 32 MHz (`j2_spi::Ranura::f_sck_hz` trae de donde sale).
            defmt::write!(f, "{=u32}.{=u32:03}", ent, frac / 1_000)
        }
    }
}

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = usb::iniciar(config);

    // El montaje entero vive en `j2_banco` (R23): los pines y los canales van
    // ahi como tipos concretos, asi que un pin cambiado no compila. El NVIC lo
    // pone `Ranura::nueva` (R21): aqui no se toca ninguna prioridad.
    let ranura = maestro_del_banco(
        p.PE15,
        p.PG2,
        p.PG1,
        p.PA3,
        p.GPDMA1_CH0,
        p.GPDMA1_CH1,
        &p.RCC,
        Config {
            f_sck_hz: F_SCK_HZ,
            f_cpu_hz: f_cpu,
            retardo_tsck_cuartos: RETARDO_CUARTOS,
        },
    );
    // El `f_sck` REAL se lee **antes** de entregar la ranura al ejecutor: a
    // partir de `arrancar` la `Ranura` vive dentro de su tarea y no hay forma de
    // preguntarle. Y es el real, no el pedido: el `MBR` redondea hacia abajo, y
    // una fila etiquetada con el pedido mentiria sobre a que reloj se midio.
    let f_sck_hz = ranura.f_sck_hz();
    info!(
        "resistencia_j2: firmware {}, f_sck {} Hz (pedido {}), retardo {} cuartos, f_cpu {} Hz",
        env!("SAM17_GIT"),
        f_sck_hz,
        F_SCK_HZ,
        RETARDO_CUARTOS,
        f_cpu
    );

    let esclavo = esclavo_del_banco(p.PE2, p.PE14, p.PE13, p.PE11, p.GPDMA1_CH2, p.GPDMA1_CH3);

    arrancar(
        interrupt::GFXTIM,
        [Some(ranura), None, None, None, None, None],
        bajada_del_banco,
        juez_del_banco,
    );
    EJECUTOR_J2
        .spawner()
        .spawn(defmt::unwrap!(j2_esclavo::tarea_esclavo(esclavo)));

    // Una fila con `horas=0` nada mas arrancar. No es una medida -- todo esta a
    // cero y el ejecutor lleva microsegundos corriendo -- y por eso lleva su
    // hora puesta: es para **validar el formato** delante de quien va a copiar
    // filas durante 24 h, en vez de descubrir a la hora que una columna baila.
    publicar(0, f_sck_hz);

    let mut ticker = Ticker::every(Duration::from_secs(3600));
    let mut horas = 0u32;
    loop {
        ticker.next().await;
        horas += 1;
        publicar(horas, f_sck_hz);
    }
}

/// Las tres lineas de cada hora. Una sola funcion para la de `horas=0` y las de
/// verdad: dos copias de una fila de doce columnas es como se separan.
fn publicar(horas: u32, f_sck_hz: u32) {
    let c = cuentas(RANURA_BANCO);

    // El firmware con el que se midio, en su propia linea y **fuera** de las
    // doce columnas: la cabecera de `resistencia_j2.csv` es de R-MJ8 y no se
    // toca desde aqui. Va delante de la fila para que al copiar se vea a cual
    // pertenece.
    info!("firmware={=str}", env!("SAM17_GIT"));
    // La fila de `resistencia_j2.csv`, con sus doce columnas en el orden de
    // R-MJ8: `ranura,instancia,tsize,nss,reloj_MHz,horas,giros,
    // plazos_vencidos,eot_tardios,subidas_malas,fecha,placa`. `fecha` va
    // vacia -- la pone quien copia la fila --, y por eso hay dos comas
    // seguidas antes de `placa`.
    info!(
        "{=usize},{=str},{=usize},{=str},{},{=u32},{=u32},{=u32},{=u32},{=u32},,{=str}",
        RANURA_BANCO,
        INSTANCIA,
        LARGO_BANCO,
        NSS,
        Mhz(f_sck_hz),
        horas,
        c.giros,
        c.plazos_vencidos,
        c.eot_tardios,
        c.subidas_malas,
        PLACA
    );
    info!(
        "esclavo,tramas_ok={},tramas_cortas={},rearmes_escalados={}",
        j2_esclavo::TRAMAS_OK.load(Ordering::Relaxed),
        j2_esclavo::TRAMAS_CORTAS.load(Ordering::Relaxed),
        j2_esclavo::REARMES_ESCALADOS.load(Ordering::Relaxed),
    );
    // `escaladas_gpdma` de esta linea son **solo las del maestro**: ver
    // `escaladas_del_maestro`. Las del esclavo ya salen arriba, en
    // `rearmes_escalados`.
    info!(
        "maestro,escaladas_gpdma={},inestable={},muda={}",
        escaladas_del_maestro(),
        c.inestable,
        c.muda,
    );
}

/// Las escaladas del GPDMA que son **del maestro**.
///
/// `ESCALADAS_GPDMA` lo sube `j2_spi::soltar_canales`, y a esa la llaman los dos
/// extremos: cada escalada del esclavo entra tambien ahi, asi que publicar el
/// total bajo `maestro,` contaria las suyas dos veces -- una aqui y otra en
/// `rearmes_escalados`. Quien las separa es `j2_esclavo::REARMES_ESCALADOS`, que
/// solo cuenta las del esclavo, y la resta deja las del maestro.
///
/// `saturating_sub` porque los dos atomicos se leen por separado y el esclavo
/// puede escalar entre una lectura y la otra: preferimos un cero de mas a un
/// contador que envuelve y publica cuatro mil millones.
fn escaladas_del_maestro() -> u32 {
    ESCALADAS_GPDMA
        .load(Ordering::Relaxed)
        .saturating_sub(j2_esclavo::REARMES_ESCALADOS.load(Ordering::Relaxed))
}
