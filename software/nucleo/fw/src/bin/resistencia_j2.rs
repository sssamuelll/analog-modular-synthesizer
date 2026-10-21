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
//! **Con `--features transporte-tic,reloj-hub`: el soak del instrumento.** El transporte por tic
//! de `j2_tic` a 8 kHz y el nucleo a 800 MHz con las dos caches, como `tic_banco`: es el lazo
//! que cuenta para el horizonte (`recuperacion_j2_budget.py` solo suma las filas con al menos
//! el 90 % de 8 kHz). La fila es la misma, de doce columnas; cambia lo que la rodea:
//!
//! * **Una fila por hora y nada mas.** Sin la linea de carga de cada minuto ni el medidor del
//!   hilo: no hacen falta para el lazo del hub.
//! * **Los `info!` no ensucian el tic.** Medido el 21-10 en la Nucleo: 375 impresiones a 8 kHz,
//!   sin sincronizarlas con el tic, y cero tics tardios y cero retraso de entrada. La linea
//!   `tic,` de cada fila deja el testigo a la vista por si cambiara.
//! * **`giros` va en 64 bits** ([`CuentaLarga`]): el contador de 32 da la vuelta a las 149 h.
//! * Con `--features corta` la fila sale cada 10 s y la columna `horas` queda en 0: para
//!   probar el montaje en la placa, y que la puerta no la cuente.
//!
//! ```bash
//! cargo run --release --bin resistencia_j2
//! cargo run --release --features transporte-tic,reloj-hub --bin resistencia_j2
//! ```

use core::sync::atomic::Ordering;

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt;
use embassy_time::{Duration, Ticker};
use sam17_nucleo_core::cuenta_larga::CuentaLarga;
#[cfg(feature = "transporte-tic")]
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
#[cfg(not(feature = "transporte-tic"))]
use sam17_nucleo_fw::carga::{vueltas_del_hilo, Medidor};
use sam17_nucleo_fw::j2_banco::{
    bajada_del_banco, esclavo_del_banco, juez_del_banco, maestro_del_banco, LARGO_BANCO,
    RANURA_BANCO,
};
#[cfg(not(feature = "transporte-tic"))]
use sam17_nucleo_fw::j2_ejecutor::lanzar_ranuras;
use sam17_nucleo_fw::j2_ejecutor::{cuentas, iniciar_ejecutor};
use sam17_nucleo_fw::j2_esclavo;
use sam17_nucleo_fw::j2_spi::{Config, ESCALADAS_GPDMA};
#[cfg(feature = "transporte-tic")]
use sam17_nucleo_fw::j2_tic;
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

#[cfg(all(feature = "transporte-tic", not(feature = "reloj-hub")))]
compile_error!(
    "transporte-tic a 8 kHz pide el nucleo a 800 MHz: --features transporte-tic,reloj-hub"
);

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

/// El periodo del giro **del banco**, 1 kHz, y no los 125 us del instrumento.
///
/// A 64 MHz y sin caches un giro del maestro cuesta unos 17 000 ciclos solo en
/// el ejecutor y el esclavo del banco, que va en el mismo nucleo, otros tantos:
/// a 125 us la CPU queda al 100 %, el hilo no corre y este binario no podria
/// publicar ni una fila (#428). A 1 ms el ejecutor trabaja al 45 % y al hilo le
/// queda el resto. La fila vale para **1 kHz**, no para 8; el instrumento de
/// verdad lo mide `carga_j2`.
///
/// Con `transporte-tic` es el del instrumento, 125 us: el tic gasta ~2 000 ciclos por giro y a
/// 800 MHz sobra CPU (`tic_banco`).
#[cfg(not(feature = "transporte-tic"))]
const PERIODO_BANCO_US: u32 = 1_000;
#[cfg(feature = "transporte-tic")]
const PERIODO_BANCO_US: u32 = PERIODO_GIRO_US;

/// Cada cuanto sale la fila, en segundos: la hora. Con `corta`, 10 s para probar el montaje.
#[cfg(feature = "transporte-tic")]
const FILA_CADA_S: u64 = if cfg!(feature = "corta") { 10 } else { 3_600 };

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
async fn main(spawner: Spawner) {
    #[cfg(feature = "transporte-tic")]
    let config = usb::configuracion_hub();
    #[cfg(not(feature = "transporte-tic"))]
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
        "resistencia_j2: firmware {}, transporte {}, f_sck {} Hz (pedido {}), retardo {} cuartos, f_cpu {} Hz, periodo {} us",
        env!("SAM17_GIT"),
        if cfg!(feature = "transporte-tic") {
            "tic"
        } else {
            "ejecutor"
        },
        f_sck_hz,
        F_SCK_HZ,
        RETARDO_CUARTOS,
        f_cpu,
        PERIODO_BANCO_US
    );

    let esclavo = esclavo_del_banco(p.PE2, p.PE14, p.PE13, p.PE11, p.GPDMA1_CH2, p.GPDMA1_CH3);

    // La CPU que le queda al hilo, medida por el hilo: la base se calibra ahora,
    // con el J2 sin arrancar (`carga`). Con el tic no se mide: el hilo no imprime
    // entre filas (cabecera).
    #[cfg(not(feature = "transporte-tic"))]
    let mut medidor = {
        spawner.spawn(defmt::unwrap!(vueltas_del_hilo()));
        let medidor = Medidor::calibrar(500).await;
        info!("carga: base {} vueltas/s", medidor.base_por_s());
        medidor
    };
    #[cfg(feature = "transporte-tic")]
    let _ = spawner;

    // El esclavo nace ANTES que el maestro: el maestro clocaria desde el primer
    // instante contra un esclavo que no existe y esos giros saldrian como
    // `subidas_malas` en la fila.
    let spawner_j2 = iniciar_ejecutor(interrupt::GFXTIM);
    spawner_j2.spawn(defmt::unwrap!(j2_esclavo::tarea_esclavo(esclavo)));
    #[cfg(not(feature = "transporte-tic"))]
    lanzar_ranuras(
        spawner_j2,
        [Some(ranura), None, None, None, None, None],
        bajada_del_banco,
        juez_del_banco,
        PERIODO_BANCO_US,
    );
    #[cfg(feature = "transporte-tic")]
    {
        let _ = spawner_j2;
        let mut ranuras = [const { None }; 6];
        ranuras[RANURA_BANCO] = Some(ranura);
        j2_tic::lanzar(
            ranuras,
            p.TIM7,
            PERIODO_BANCO_US,
            f_cpu,
            bajada_del_banco,
            juez_del_banco,
        );
        // La D-cache solo se enciende con la region de los bufferes ya en la MPU, y
        // `lanzar` la acaba de programar (como en `tic_banco`).
        // SAFETY: nadie mas toca el SCB en este binario.
        unsafe {
            let mut cp = cortex_m::Peripherals::steal();
            cp.SCB.enable_icache();
            cp.SCB.enable_dcache(&mut cp.CPUID);
        }
    }

    let mut giros = CuentaLarga::nueva();

    // Una fila con `horas=0` nada mas arrancar. No es una medida -- todo esta a
    // cero y el ejecutor lleva microsegundos corriendo -- y por eso lleva su
    // hora puesta: es para **validar el formato** delante de quien va a copiar
    // filas durante 24 h, en vez de descubrir a la hora que una columna baila.
    publicar(0, f_sck_hz, &mut giros);

    // Con el tic, solo la fila de cada hora (o de cada 10 s con `corta`).
    #[cfg(feature = "transporte-tic")]
    {
        let mut ticker = Ticker::every(Duration::from_secs(FILA_CADA_S));
        let mut filas = 0u32;
        loop {
            ticker.next().await;
            filas += 1;
            publicar(
                if cfg!(feature = "corta") { 0 } else { filas },
                f_sck_hz,
                &mut giros,
            );
        }
    }

    // Un minuto de tic, una linea de carga por tic y la fila de la hora cada 60.
    // La carga es la CPU libre para el hilo (`carga`): un instrumento sano la
    // deja casi entera; la Nucleo a 64 MHz sin caches no (#428).
    #[cfg(not(feature = "transporte-tic"))]
    {
        let mut ticker = Ticker::every(Duration::from_secs(60));
        let mut minutos = 0u32;
        loop {
            ticker.next().await;
            minutos += 1;
            info!(
                "carga,minuto={},hilo_libre_permil={}",
                minutos,
                medidor.libre_por_mil()
            );
            if minutos % 60 == 0 {
                publicar(minutos / 60, f_sck_hz, &mut giros);
            }
        }
    }
}

/// Las tres lineas de cada hora. Una sola funcion para la de `horas=0` y las de
/// verdad: dos copias de una fila de doce columnas es como se separan.
fn publicar(horas: u32, f_sck_hz: u32, giros: &mut CuentaLarga) {
    let c = cuentas(RANURA_BANCO);
    let giros = giros.anota(c.giros);

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
        "{=usize},{=str},{=usize},{=str},{},{=u32},{=u64},{=u32},{=u32},{=u32},,{=str}",
        RANURA_BANCO,
        INSTANCIA,
        LARGO_BANCO,
        NSS,
        Mhz(f_sck_hz),
        horas,
        giros,
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
        "maestro,escaladas_gpdma={},atrasos={},inestable={},muda={}",
        escaladas_del_maestro(),
        c.atrasos,
        c.inestable,
        c.muda,
    );
    // Los testigos del tic, en la propia fila de la hora: si un `info!` ensucio el tic, sale aqui.
    #[cfg(feature = "transporte-tic")]
    {
        info!("tic,{}", j2_tic::testigos());
    }
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
