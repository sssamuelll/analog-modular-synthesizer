#![no_std]
#![no_main]

//! **El barrido del retardo: el punto (2) del orden del dia.**
//!
//! Enmienda del 11-09 a la sec.9 del papel del maestro, punto 4: *«El binario
//! `eot_al_aire` de `EN-PLACA.md` pasa a ser el barrido del punto 3»*. Cien mil
//! transferencias eran 12,5 s a 8 kHz y acotaban p < 3e-5 al 95 %, que no
//! excluye ni el peor extremo del hilo (2e-5): no discriminaba nada. Lo que si
//! discrimina es **como depende la tasa del retardo**: una tasa que dependa de
//! el es la firma de ES0396 sec.2.14.2; una que no, no lo es.
//!
//! Se barren los seis puntos de la enmienda -- `{0, ¼, ½, 1, 2, 4} x T_SCK`, o
//! sea `retardo_tsck_cuartos` en `{0, 1, 2, 4, 8, 16}` -- a **15 min por
//! punto**, que es lo que el acta pide: *«Con la tasa por armado, 15 min en una
//! ranura contestan p < 4,2e-7 al 95 %»*. Al terminar los seis se queda en 4,
//! el de produccion, para siempre, imprimiendo un punto mas cada 15 min.
//!
//! **En que configuracion corre, y por que es la nuestra y no la de jake-taf.**
//! El acta dice *«en esa configuracion»*, apuntando al punto (1). Este plan lo
//! lee al reves y lo dice: el tercer workaround de la errata es *«Prevent EOT
//! events from occurring, by setting transfer size to undefined (TSIZE = 0)»*,
//! o sea que **con `TSIZE = 0` no hay eventos `EOT`** -- y el mecanismo de
//! sec.2.14.2 es *«stall upon setting the CSTART bit within one SCK cycle after
//! the EOT event»*. Un retardo medido desde un evento que no ocurre no barre
//! nada. Asi que el barrido corre sobre la configuracion **con `EOT`**: el
//! driver propio, `TSIZE > 0` y NSS por hardware ([`j2_spi`]), que es ademas la
//! que el instrumento va a usar. El punto (1), con `TSIZE = 0`, es el otro
//! binario (`control_positivo`).
//!
//! **El maestro NO va por `j2_ejecutor::arrancar`.** El barrido cambia el
//! retardo entre punto y punto, y para eso necesita la `Ranura` en la mano:
//! `arrancar` se la lleva a una tarea del ejecutor y no vuelve a soltarla. Asi
//! que el lazo del maestro vive en el ejecutor de **hilo** (el cuerpo de
//! `main`), con su propio `Ticker` de 125 us, y `arrancar` se llama con las seis
//! ranuras en `None` solo para poner el `EJECUTOR_J2` en marcha y colgar de el
//! al esclavo. Es una desviacion de R-MJ5 acotada a este binario y **no es el
//! lazo del instrumento**: este no vigila salud, no marca `inestable` ni `muda`
//! y no cuenta con la politica de `core`, porque es un experimento de
//! **transporte** -- lo unico que se mide es como depende del retardo la tasa de
//! plazos vencidos.
//!
//! **El esclavo si corre**, en SPI4 y en el `EJECUTOR_J2`, porque `tramas_cortas`
//! separa *«el maestro abortó»* de *«el esclavo no llego»* (las tres causas, en
//! la cabecera de [`j2_esclavo`]).
//!
//! ```bash
//! cargo run --release --bin barrido_retardo
//! ```

use core::sync::atomic::Ordering;

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt::{InterruptExt, Priority};
use embassy_stm32::{dma, interrupt, pac, peripherals};
use embassy_time::{Duration, Instant, Ticker};
use sam17_nucleo_core::maestro_j2::{plazo_us, Umbrales, PERIODO_GIRO_US};
use sam17_nucleo_fw::j2_banco::{bajada_del_banco, juez_del_banco, LARGO_BANCO};
use sam17_nucleo_fw::j2_ejecutor::{arrancar, EJECUTOR_J2};
use sam17_nucleo_fw::j2_esclavo::{self, Esclavo};
use sam17_nucleo_fw::j2_spi::{self, Config, Ranura, Resultado, ESCALADAS_GPDMA, LARGO_MAX};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

embassy_stm32::bind_interrupts!(struct Irqs {
    SPI5 => j2_spi::Isr<0>;
    GPDMA1_CHANNEL0 => dma::InterruptHandler<peripherals::GPDMA1_CH0>;
    GPDMA1_CHANNEL1 => dma::InterruptHandler<peripherals::GPDMA1_CH1>;
    GPDMA1_CHANNEL2 => dma::InterruptHandler<peripherals::GPDMA1_CH2>;
    GPDMA1_CHANNEL3 => dma::InterruptHandler<peripherals::GPDMA1_CH3>;
    EXTI11 => j2_esclavo::IsrCs;
});

/// Los seis puntos de la enmienda del 11-09, en cuartos de `T_SCK`:
/// `{0, ¼, ½, 1, 2, 4} x T_SCK`.
const RETARDOS: [u8; 6] = [0, 1, 2, 4, 8, 16];

/// El de produccion, `>= 1 T_SCK` (D2, enmienda del 11-09). Es donde se queda.
const RETARDO_PRODUCCION: u8 = 4;

/// 15 min por punto: *«15 min en una ranura contestan p < 4,2e-7 al 95 %»*
/// (acta del 11-09, punto 3 del orden del dia).
const SEGUNDOS_POR_PUNTO: u64 = 15 * 60;

/// El piso legado del enlace, 10 MHz (J2 punto a punto D2; `F_CONTRATO_HZ` de
/// `hardware/02-midi-cv/trama_j2_budget.py:89`). Es donde la errata muerde:
/// su condicion es *«system clock much faster than SCK»*.
const F_SCK_PISO_HZ: u32 = 10_000_000;

/// Lo que se cuenta en un punto del barrido.
struct Punto {
    giros: u32,
    plazos_vencidos: u32,
    eot_tardios: u32,
    subidas_malas: u32,
}

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = embassy_stm32::init(config);

    // Las ISR del SPI y de los canales del GPDMA a `P1`, por encima del
    // `EJECUTOR_J2` (`P2`), y ANTES de construir la ranura (EN-PLACA, casilla
    // del 11-09: sin esto un `EOT` tardio no se pierde, pero no se cuenta).
    //
    // Los canales del GPDMA ya estan **habilitados** en el NVIC: lo hace
    // `embassy_stm32::init` para todos (`dma/gpdma/mod.rs:526-534`), con la
    // prioridad de la `Config`; aqui solo se sube la suya. La del SPI5 no la
    // habilita nadie -- ni `init`, ni `Ranura::nueva`, que solo arma `EOTIE` en
    // el periferico --, y sin ella el `EOT` no llega al NVIC y **todos** los
    // giros vencerian plazo. Por eso esta la linea de `enable`.
    interrupt::SPI5.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL0.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL1.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL2.set_priority(Priority::P1);
    interrupt::GPDMA1_CHANNEL3.set_priority(Priority::P1);
    // SAFETY: la unica forma de desenmascarar la linea. El manejador existe
    // porque `Irqs` ata `SPI5 => j2_spi::Isr<0>`.
    unsafe { interrupt::SPI5.enable() };

    let mut ranura = Ranura::nueva::<peripherals::SPI5, _, _, _, _, _, _>(
        0,
        pac::SPI5,
        p.PE15,
        p.PG2,
        p.PG1,
        p.PA3,
        p.GPDMA1_CH0,
        p.GPDMA1_CH1,
        Irqs,
        Irqs,
        &p.RCC,
        Config {
            f_sck_hz: F_SCK_PISO_HZ,
            f_cpu_hz: f_cpu,
            retardo_tsck_cuartos: RETARDOS[0],
        },
    );
    info!(
        "barrido_retardo: f_sck {} Hz (pedido {}), retardo inicial {} cuartos, f_cpu {} Hz",
        ranura.f_sck_hz(),
        F_SCK_PISO_HZ,
        RETARDOS[0],
        f_cpu
    );

    let esclavo = Esclavo::nuevo::<peripherals::SPI4, _, _, _, _, _, _>(
        pac::SPI4,
        p.PE2,
        p.PE14,
        p.PE13,
        p.PE11,
        p.GPDMA1_CH2,
        p.GPDMA1_CH3,
        Irqs,
        LARGO_BANCO,
    );

    // Seis `None`: el maestro de este binario no vive en el ejecutor (ver la
    // cabecera). Lo unico que `arrancar` hace aqui es poner el `EJECUTOR_J2` en
    // marcha para que el esclavo tenga donde correr.
    arrancar(
        interrupt::GFXTIM,
        [None, None, None, None, None, None],
        bajada_del_banco,
        juez_del_banco,
    );
    EJECUTOR_J2
        .spawner()
        .spawn(defmt::unwrap!(j2_esclavo::tarea_esclavo(esclavo)));

    for retardo in RETARDOS {
        correr_punto(&mut ranura, retardo).await;
    }
    // Los seis puntos estan medidos: se queda en el de produccion para siempre,
    // publicando un punto mas cada 15 min.
    loop {
        correr_punto(&mut ranura, RETARDO_PRODUCCION).await;
    }
}

/// Un punto del barrido: fija el retardo, gira 15 min a 8 kHz y publica.
async fn correr_punto(ranura: &mut Ranura<'static>, retardo: u8) {
    ranura.fijar_retardo_cuartos(retardo);

    // Los dos contadores globales son acumulados desde el arranque; lo que este
    // punto publica es su **delta**, para que los seis puntos se comparen entre
    // si y no con la suma de los anteriores.
    let escaladas_antes = ESCALADAS_GPDMA.load(Ordering::Relaxed);
    let cortas_antes = j2_esclavo::TRAMAS_CORTAS.load(Ordering::Relaxed);

    let c = girar(ranura, Duration::from_secs(SEGUNDOS_POR_PUNTO)).await;

    info!(
        "barrido,retardo_cuartos={},giros={},plazos_vencidos={},eot_tardios={},\
         subidas_malas={},escaladas={},tramas_cortas={}",
        retardo,
        c.giros,
        c.plazos_vencidos,
        c.eot_tardios,
        c.subidas_malas,
        ESCALADAS_GPDMA.load(Ordering::Relaxed) - escaladas_antes,
        j2_esclavo::TRAMAS_CORTAS.load(Ordering::Relaxed) - cortas_antes,
    );
}

/// El lazo del maestro durante `cuanto`: un giro cada `PERIODO_GIRO_US`, con la
/// bajada y el juez del banco. Sin politica de `core`: es transporte.
async fn girar(ranura: &mut Ranura<'static>, cuanto: Duration) -> Punto {
    let umbrales = Umbrales::POR_DEFECTO;
    let f_sck_hz = ranura.f_sck_hz();
    let mut bajada = [0u8; LARGO_MAX];
    let mut subida = [0u8; LARGO_MAX];
    let mut c = Punto {
        giros: 0,
        plazos_vencidos: 0,
        eot_tardios: 0,
        subidas_malas: 0,
    };

    let fin = Instant::now() + cuanto;
    let mut ticker = Ticker::every(Duration::from_micros(PERIODO_GIRO_US as u64));
    while Instant::now() < fin {
        ticker.next().await;

        let tsize = bajada_del_banco(0, &mut bajada);
        let plazo = Duration::from_micros(plazo_us(tsize, f_sck_hz, &umbrales) as u64);
        let (res, tardios) = ranura.giro(&bajada, &mut subida, tsize, plazo).await;

        c.giros += 1;
        c.eot_tardios += tardios;
        match res {
            Resultado::Ok => {
                if !juez_del_banco(0, &subida[..tsize.get() as usize]) {
                    c.subidas_malas += 1;
                }
            }
            Resultado::PlazoVencido => {
                c.plazos_vencidos += 1;
                // Realinear, por la misma razon que `j2_ejecutor::tarea_ranura`:
                // el `Ticker` devuelve `Ready` mientras siga atrasado, y tras un
                // giro largo sacaria los dos siguientes pegados, borrando el
                // `T_GAP` que el esclavo necesita para su rearme.
                ticker.reset();
            }
        }
    }
    c
}
