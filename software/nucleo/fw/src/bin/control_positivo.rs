#![no_std]
#![no_main]

//! **El control positivo del banco: los puntos (0) y (1) del orden del dia.**
//!
//! Acta del J2 del 2026-09-11, ficha 3, recogida en la enmienda del 11-09 a la
//! sec.9 del papel del maestro (`docs/superpowers/specs/`
//! `2026-09-03-maestro-j2-recuperacion-design.md`): *«El soak no va primero: va
//! el control positivo. Un soak limpio no ejecuta D4 y no distingue "no nos
//! afecta" de "el banco no lo ve"»*. Este binario es ese primer dia.
//!
//! **(0) La medida que dirime la lectura de p. 3492.** Con el SPI5 encendido por
//! RCC y **nada armado** -- sin `TSIZE`, sin DMA, sin `CSTART` --, `SPE = 1` y
//! leer `SR.EOT`. RM0486 Rev 4, sec.67.11.6, p. 3492: *«EOT is set by hardware
//! as soon as a full transfer is complete, that is when SPI is re-enabled or
//! when TSIZE number of data have been transmitted and/or received»*. Si vuelve
//! 1, prender **es** un evento `EOT`, la hipotesis de ES0396 sec.2.14.2 esta
//! viva y todo armado del driver cae dentro de la ventana de la errata al piso
//! (enmienda del 11-09 a D2). Si vuelve 0, el `EOT` anterior era el de la trama
//! del giro previo y D2 ya lo cubria con mas de 100 us de sobra.
//!
//! Se lee **dos veces** y las dos se imprimen. La frase del manual no dice modo,
//! y el periferico recien reseteado esta en **esclavo** (`CFG2.MASTER = 0` es su
//! valor de reset, sec.67.11.4, p. 3488): un 0 leido ahi no distinguiria *«no
//! pasa»* de *«en esclavo no pasa»*, y lo que D2 describe es el maestro. Asi que
//! la segunda lectura pone `MASTER = 1` -- que sigue siendo *nada armado*, es
//! una configuracion, no una transferencia -- y se publica aparte.
//!
//! **(1) La configuracion de jake-taf, sin el driver propio.** embassy tal cual:
//! `Spi::new_blocking` a 100 kHz en modo 0, `CS` por GPIO en PA3, `TSIZE = 0` --
//! que es lo que hace `blocking_read` -- y lecturas de 8 bytes en bucle. **No es
//! el repro tal como lo publico su autor**: el del primer reporte de
//! embassy-rs/embassy#5607 hace `write` de 2 bytes + `read` de 1 por vuelta. El
//! acta del 11-09 (punto 3) le daba a una hora 98 % de potencia contra los
//! ~900 s de ese reporte; jake-taf dio despues 30-120 min con builds mas
//! nuevos, y contra eso una hora no contesta. Medido el 2026-10-01: 64 min,
//! 0 cuelgues (EN-PLACA.md, punto (1)).
//!
//! **El vigia no comparte ejecutor con el bucle.** `blocking_read` de embassy es
//! sincrono y cuando el periferico se cuelga **no vuelve nunca**
//! (`spi/mod.rs`, `transfer_words`): quien lo vigile desde el mismo ejecutor se
//! cuelga con el. Por eso el bucle vive en el ejecutor de **hilo** (el cuerpo de
//! `main`) y el vigia en el `EJECUTOR_J2`, que es de **interrupcion** a `P2` y
//! desaloja al hilo. `arrancar` se llama con las seis ranuras en `None`: aqui no
//! se usa ninguna, solo se necesita el ejecutor en marcha.
//!
//! **El paliativo del `TXDR` esta aqui y solo aqui.** R-MJ3 lo prohibe en el
//! driver -- *«Nunca se escribe a `TXDR` para desatascar»* --, y el propio papel
//! dice por que: no funciona en DMA y mete un byte en el bus a mitad de un
//! estado desconocido (sec.D4). En el control positivo **es la medida**: es el
//! paliativo que jake-taf usa en su repro bloqueante, y aplicarlo es lo que
//! convierte un cuelgue en un evento contado en vez de en una placa muerta.
//! Enmienda del 08-09 a D4: *«I stuck with blocking since I have a workaround
//! when it gets stuck (`SPI1.txdr8().write_value(0)`), but both have the
//! problem»*.
//!
//! **El esclavo NO se arranca aqui.** El MISO (PG1) se queda **al aire**: lo que
//! se mide es el maestro, y un esclavo contando bytes solo anadiria tramas
//! cortas que no significan nada con `TSIZE = 0` y `CS` por software.
//!
//! ```bash
//! cargo run --release --bin control_positivo
//! ```

use core::sync::atomic::{AtomicU32, Ordering};

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::gpio::{Level, Output, Speed};
use embassy_stm32::interrupt;
use embassy_stm32::pac::spi::vals::Master;
use embassy_stm32::time::Hertz;
use embassy_stm32::{pac, peripherals, rcc, spi};
use embassy_time::{Duration, Ticker};
use sam17_nucleo_fw::j2_banco::{bajada_del_banco, juez_del_banco};
use sam17_nucleo_fw::j2_ejecutor::{arrancar, EJECUTOR_J2};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// El reloj de jake-taf: 100 kHz (acta del 11-09, punto 1 del orden del dia).
const F_SCK_JAKE_HZ: u32 = 100_000;

/// Los bytes por lectura del repro: `blocking_read(&mut [0u8; 8])`.
const BYTES_POR_LECTURA: usize = 8;

/// El bucle del primer reporte de embassy-rs/embassy#5607: bajo `CS`, `write` de
/// `[0x03, 0x2c]` y `read` de 1 byte. Lo pide `--features bucle-del-reporte`
/// (decision del 2026-10-01, EN-PLACA punto (1)). Arma el periferico dos veces
/// por cada 3 bytes, contra una por cada 8 del bucle de siempre. Las dos `info!`
/// por vuelta del reporte NO estan: serian del orden de 10^8 lineas en 6 h.
/// `lecturas` cuenta vueltas.
const BUCLE_DEL_REPORTE: bool = cfg!(feature = "bucle-del-reporte");

/// Lo que escribe el reporte antes de leer.
const ESCRITURA_DEL_REPORTE: [u8; 2] = [0x03, 0x2c];

/// Cadencia del vigia. Tres tics sin avanzar son el umbral de cuelgue, o sea
/// 300 ms: **mas de quinientas veces** una lectura sana de 8 bytes al `f_sck`
/// **real** de este binario, 125 kHz -- 8 x 8 / 125 kHz = **512 us**; ver la nota
/// del `MBR` mas abajo --, asi que no hay falso positivo por lentitud.
const TIC_VIGIA_MS: u64 = 100;

/// Tics seguidos sin que `PROGRESO` avance que cuentan como cuelgue.
const TICS_PARA_CUELGUE: u32 = 3;

/// Tics entre informes. 600 x 100 ms = 60 s.
const TICS_POR_INFORME: u32 = 600;

/// Lecturas completadas. La sube el bucle del hilo y la lee el vigia: es la
/// unica senal de vida que tiene, porque el bucle no vuelve a ceder la CPU.
static PROGRESO: AtomicU32 = AtomicU32::new(0);

/// Cuelgues detectados y paliados.
static CUELGUES: AtomicU32 = AtomicU32::new(0);

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = usb::iniciar(config);

    // --- (0) El experimento de un acceso -------------------------------------
    // El reloj y el reset del periferico, que es el paso 0 de D4. Despues de
    // esto `Spi::new_blocking` vuelve a hacerlo por su cuenta
    // (`spi/mod.rs`, `enable_and_init`: *"self.info.rcc.enable_and_reset()"*),
    // asi que este experimento no deja nada puesto.
    rcc::enable_and_reset::<peripherals::SPI5>();

    // Primera lectura: el periferico tal como sale del reset. Nada armado, y
    // `CFG2` en su valor de reset, o sea esclavo.
    pac::SPI5.cr1().modify(|w| w.set_spe(true));
    let eot_reset = pac::SPI5.sr().read().eot();
    pac::SPI5.cr1().modify(|w| w.set_spe(false));

    // Segunda lectura: lo mismo en **maestro**, que es el modo del que habla D2.
    // Sigue sin haber nada armado: `MASTER` es configuracion, no transferencia.
    // `CFG2` solo se puede escribir con `SPE = 0` (sec.67.11.1, p. 3484), y aqui
    // lo esta.
    pac::SPI5.cfg2().write(|w| w.set_master(Master::Master));
    pac::SPI5.ifcr().write(|w| w.set_eotc(true));
    pac::SPI5.cr1().modify(|w| w.set_spe(true));
    let eot_maestro = pac::SPI5.sr().read().eot();
    pac::SPI5.cr1().modify(|w| w.set_spe(false));

    info!("experimento_0,eot_al_encender={}", eot_reset as u8);
    info!(
        "experimento_0,eot_al_encender_maestro={}",
        eot_maestro as u8
    );

    // --- (1) La configuracion de jake-taf ------------------------------------
    // 100 kHz, modo 0, sin DMA y sin NSS del periferico: `new_blocking` no toma
    // pin de `CS`, asi que el `CS` es un GPIO nuestro. `TSIZE = 0` no se escribe
    // aqui: es lo que deja `blocking_read`, que cloca palabra a palabra.
    let mut cfg = spi::Config::default();
    cfg.frequency = Hertz(F_SCK_JAKE_HZ);
    cfg.mode = spi::MODE_0;
    let mut spi = spi::Spi::new_blocking(p.SPI5, p.PE15, p.PG2, p.PG1, cfg);

    // El `CS` en PA3 (CN15 pin 17). `High` de salida porque el reposo del `CS`
    // es el nivel alto: baja antes de la lectura y sube despues.
    let mut cs = Output::new(p.PA3, Level::High, Speed::VeryHigh);

    // El `f_sck` que de verdad quedo: el `MBR` que embassy calculo, leido del
    // registro. El divisor es `2^(MBR+1)` (sec.67.11.3, `SPI_CFG1.MBR`).
    //
    // **Ojo con este numero el dia de la placa: no van a ser 100 kHz.**
    //
    // El kernel del SPI5 **no es el HSI de 64 MHz**: es `pclk2`, y son 32 MHz.
    // `ClockMux::default()` es `mem::zeroed()` (`_generated.rs:5317-5319`) e
    // `init()` escribe `set_spi5sel(self.spi5sel)` **incondicionalmente**
    // (`:5327`, `:5397`), asi que el cero manda; y el cero de este campo es
    // `Spisel45::Pclk2` (metapac `rcc_n6.rs:43346-43348`). `pclk2` sale de
    // `sys / hpre / ppre2` (embassy `rcc/n6.rs:462`, publicado en `:1413`), y con
    // los defectos que `usb::configuracion()` no toca -- `sys: SysClk::Hsi`
    // (`:196`), `ahb: Div2` (`:225`), `apb2: Div1` (`:227`) -- eso es
    // 64 / 2 / 1 = **32 MHz**. (ES0620 sec.2.2.1 dice que el prescaler de APB no
    // funciona y `pclk` replica siempre a `hclk`: da el mismo numero, 32.)
    //
    // Con eso, el `compute_baud_rate` de embassy (`spi/mod.rs:1532-1546`), que
    // reparte por tramos: 32e6/100e3 = 320 cae en el ultimo tramo y da `/256`,
    // o sea **125 kHz**. Es el divisor mas grande que hay, asi que no se puede
    // bajar mas por ahi. No invalida el repro -- la condicion de ES0396
    // sec.2.14.2 es *«system clock much faster than SCK»* y 125 kHz esta aun mas
    // lejos del nucleo que los 100 kHz de jake-taf --, pero la tasa de cuelgue
    // que se mida no es comparable byte a byte con la suya. Por eso se imprime:
    // es el reloj real del control positivo.
    let f_ker = rcc::frequency::<peripherals::SPI5>().0;
    let mbr = pac::SPI5.cfg1().read().mbr().to_bits();
    let f_sck = f_ker / (1u32 << (mbr + 1));
    info!(
        "control_positivo: firmware {}, f_ker {} Hz, MBR /{}, f_sck {} Hz (pedido {}), \
         retardo: ninguno (no hay driver propio en este binario), f_cpu {} Hz, bucle: {}",
        env!("SAM17_GIT"),
        f_ker,
        1u32 << (mbr + 1),
        f_sck,
        F_SCK_JAKE_HZ,
        f_cpu,
        if BUCLE_DEL_REPORTE {
            "reporte (write 2 + read 1, sin info!)"
        } else {
            "read de 8"
        }
    );

    // El ejecutor del J2 arranca sin ninguna ranura: lo unico que se le pide es
    // que corra el vigia por encima del hilo.
    arrancar(
        interrupt::GFXTIM,
        [None, None, None, None, None, None],
        bajada_del_banco,
        juez_del_banco,
    );
    EJECUTOR_J2.spawner().spawn(defmt::unwrap!(vigia()));

    // El bucle del repro. No vuelve nunca, y eso es a proposito: es el ejecutor
    // de hilo entero, que es justo lo que el cuelgue congela.
    let mut buf = [0u8; BYTES_POR_LECTURA];
    let mut uno = [0u8; 1];
    loop {
        cs.set_low();
        // El `Err` no se distingue del `Ok` a proposito: lo que se cuenta es
        // *«volvio»*, y el modo del #5607 es que no vuelve. Un `Overrun` con el
        // MISO al aire no es el suceso que se mide.
        if BUCLE_DEL_REPORTE {
            let _ = spi.blocking_write(&ESCRITURA_DEL_REPORTE);
            let _ = spi.blocking_read(&mut uno);
        } else {
            let _ = spi.blocking_read(&mut buf);
        }
        cs.set_high();
        PROGRESO.fetch_add(1, Ordering::Relaxed);
    }
}

/// El vigia, en el ejecutor del J2 (interrupcion, `P2`): mira si `PROGRESO`
/// avanza, cuenta los cuelgues, aplica el paliativo del hilo e informa cada
/// minuto.
#[embassy_executor::task]
async fn vigia() {
    let mut ticker = Ticker::every(Duration::from_millis(TIC_VIGIA_MS));
    let mut ultimo = 0u32;
    let mut quietos = 0u32;
    let mut tics = 0u32;

    loop {
        ticker.next().await;
        tics += 1;

        let ahora = PROGRESO.load(Ordering::Relaxed);
        if ahora == ultimo {
            quietos += 1;
        } else {
            quietos = 0;
            ultimo = ahora;
        }

        if quietos >= TICS_PARA_CUELGUE {
            let n = CUELGUES.fetch_add(1, Ordering::Relaxed) + 1;
            defmt::error!(
                "control_positivo: cuelgue {} en el segundo {}, lecturas {}; \
                 paliativo del hilo (TXDR)",
                n,
                tics as u64 * TIC_VIGIA_MS / 1000,
                ahora
            );
            // El paliativo, aqui y solo aqui (R-MJ3 lo prohibe en el driver).
            // `txdr8` es el acceso de 8 bits al registro de datos de salida
            // (metapac `spi_v5.rs:69`); escribir por `txdr32` empujaria cuatro
            // bytes donde jake-taf empuja uno.
            pac::SPI5.txdr8().write_value(0);
            // A cero para no contar el mismo cuelgue una vez por tic: si el
            // paliativo no sirvio, vuelven a pasar tres tics y sube otra vez.
            quietos = 0;
        }

        if tics % TICS_POR_INFORME == 0 {
            info!(
                "control_positivo,minutos={},lecturas={},cuelgues={}",
                tics / TICS_POR_INFORME,
                ahora,
                CUELGUES.load(Ordering::Relaxed)
            );
        }
    }
}
