#![no_std]
#![no_main]

//! **La cota de espera de una ranura contra una retencion de P2.**
//!
//! Revision de Halberg del 17-10, hallazgo 1: el planificador (P3) y la recuperacion (P4) van por
//! debajo de USB y pantalla (P2), y `Vencida` y `Reiniciando` dan la ranura por muerta si pasan sus
//! cotas sin que la recuperacion arranque o acabe. Una retencion de P2 que coincida con un cuelgue
//! puede, entonces, matar la ranura y, con ella, parar el instrumento (la ranura muerta deja de sellar
//! y el IWDG del hub se queda sin sello).
//!
//! Aqui se provoca a proposito. Para cada duracion `D` de una lista creciente, se envenena la ranura
//! 0 y, **en el mismo instante en que el tic la da por vencida**, una interrupcion de P2 retiene la
//! CPU `D` microsegundos: el planificador no puede pedir la recuperacion hasta que acabe. Se mira si
//! la ranura sigue viva. El primer `D` que la mata es el umbral; las que sobreviven, no se repiten.
//!
//! ```bash
//! cargo run --release --features inyeccion,reloj-hub --bin tic_cota                # las cotas de hoy
//! cargo run --release --features inyeccion,reloj-hub,cotas-v2 --bin tic_cota       # las del papel v2
//! ```

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt::Priority;
use embassy_time::Timer;
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
use sam17_nucleo_core::transporte_j2::Estado;
use sam17_nucleo_fw::j2_banco::{bajada_del_banco, juez_del_banco, maestro_del_banco};
use sam17_nucleo_fw::j2_ejecutor::cuentas;
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::j2_tic::{self, acapara};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Las retenciones que se prueban, en microsegundos, de menor a mayor.
const GOLPES_US: [u32; 15] = [
    100, 200, 300, 400, 500, 800, 1_500, 3_000, 6_000, 10_000, 12_000, 14_000, 20_000, 30_000,
    60_000,
];

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let _ = spawner;
    #[cfg(feature = "reloj-hub")]
    let config = usb::configuracion_hub();
    #[cfg(not(feature = "reloj-hub"))]
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = usb::iniciar(config);
    let ranura = maestro_del_banco(
        p.PE15,
        p.PG2,
        p.PG1,
        p.PA3,
        p.GPDMA1_CH0,
        p.GPDMA1_CH1,
        &p.RCC,
        Config {
            f_sck_hz: 10_000_000,
            f_cpu_hz: f_cpu,
            retardo_tsck_cuartos: 4,
        },
    );
    let mut ranuras = [const { None }; 6];
    ranuras[0] = Some(ranura);
    j2_tic::lanzar(
        ranuras,
        p.TIM7,
        PERIODO_GIRO_US,
        f_cpu,
        bajada_del_banco,
        juez_del_banco,
    );
    // SAFETY: nadie mas toca el SCB en este binario.
    unsafe {
        let mut cp = cortex_m::Peripherals::steal();
        cp.SCB.enable_icache();
        cp.SCB.enable_dcache(&mut cp.CPUID);
    }
    acapara::arranca(Priority::P2);
    Timer::after_millis(300).await;

    // (D, vive despues, recuperaciones)
    let mut filas = [(0u32, true, 0u32); GOLPES_US.len()];
    let mut hechas = 0;
    for (k, &us) in GOLPES_US.iter().enumerate() {
        let antes = j2_tic::testigos().recuperaciones;
        acapara::en_vencida(us);
        j2_tic::envenena(0);
        // La retencion mas larga son 60 ms; despues, la recuperacion y un margen.
        Timer::after_millis(150).await;
        let viva = j2_tic::estado(0) != Estado::Muerta;
        filas[k] = (us, viva, j2_tic::testigos().recuperaciones - antes);
        hechas = k + 1;
        if !viva {
            break;
        }
    }
    let c = cuentas(0);

    info!(
        "tic_cota: firmware {}, cotas {=str}, f_cpu {} Hz",
        env!("SAM17_GIT"),
        if cfg!(feature = "cotas-v2") {
            "de v2 (2 y 4 tics)"
        } else {
            "de hoy (100 y 100 tics)"
        },
        f_cpu
    );
    for &(us, viva, recuperaciones) in &filas[..hechas] {
        if viva {
            info!(
                "tic_cota,golpe_us={},viva,recuperaciones={}",
                us, recuperaciones
            );
        } else {
            info!("tic_cota,golpe_us={},MUERTA", us);
        }
    }
    info!(
        "tic_cota,plazos_vencidos={},{}",
        c.plazos_vencidos,
        j2_tic::testigos()
    );
    info!("tic_cota: fin");
    // Un `bkpt` para que `probe-rs run` termine solo y suelte la sonda.
    cortex_m::asm::bkpt();
    loop {
        Timer::after_secs(60).await;
    }
}
