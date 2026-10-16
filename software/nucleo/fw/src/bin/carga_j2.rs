#![no_std]
#![no_main]

//! **Cuanta CPU gasta un giro del J2, y cuanta le deja al hilo.**
//!
//! Herramienta de medida del banco, no un punto del orden del dia: es la que
//! produce el numero que el papel del maestro pide como criterio de aceptacion
//! de la CPU (spec D5.1, enmienda del 2026-10-16) y la que hay que correr antes
//! y despues de tocar el camino caliente del driver.
//!
//! Gira **el maestro solo** -- sin el esclavo del banco, que en el mismo nucleo
//! le comeria la CPU y falsearia la cuenta -- al periodo del instrumento,
//! [`PERIODO_GIRO_US`] (125 us), que en esta placa no cabe: cada giro llega
//! tarde, el calendario deja un periodo de hueco (`core::maestro_j2::Calendario`)
//! y lo que se mide es el coste del giro y lo que sobra para el hilo. Dos
//! pasadas: sin cache y con la I-cache encendida; con `--features reloj-hub` (el
//! nucleo a 800 MHz) hay una tercera con tambien la D-cache, **sin la region MPU
//! de los buferes del DMA** (R-MJ7): es de exploracion, los datos de los buferes
//! salen incoherentes y esa fila no sirve para la puerta. Se marca
//! `icache+dcache-sin-mpu`.
//!
//! Por cada pasada, dos lineas:
//!
//! ```text
//! carga_j2,cache=<no|icache>,ciclo_us=,giros_en_5s=,hilo_libre_permil=,atrasos=,plazos_vencidos=
//! carga_j2,cache=<no|icache>,previo=,armado=,espera=,cierre=,posterior=,isr_spi=,ejecutor=
//! ```
//!
//! La segunda son **ciclos de CPU por giro** (`perfil`): hay que compilar con
//! `--features perfil`, o salen en cero y lo dice. `ejecutor` es todo el
//! manejador del ejecutor del J2, sin la ISR del SPI; `previo`, `armado`,
//! `cierre` y `posterior` son el codigo de la tarea, y la diferencia con
//! `ejecutor` es la maquinaria de futuros y el despacho. `espera` es tiempo de
//! reloj, no CPU. `hilo_libre_permil` es la CPU libre para el hilo, medida por
//! el propio hilo (`carga`).
//!
//! ```bash
//! cargo run --release --features perfil --bin carga_j2
//! cargo run --release --features perfil,reloj-hub --bin carga_j2   # a 800 MHz
//! ```
//!
//! La cabecera trae el reloj pedido (`f_cpu`) y el medido (`f_cpu_medido`, los
//! ciclos del `DWT` en 100 ms de `embassy_time`): si no coinciden, la cuenta de
//! ciclos por giro sale con un reloj que no es el que se cree.

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt;
use embassy_time::Timer;
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
use sam17_nucleo_fw::carga::{vueltas_del_hilo, Medidor};
use sam17_nucleo_fw::j2_banco::{
    bajada_del_banco, juez_del_banco, maestro_del_banco, RANURA_BANCO,
};
use sam17_nucleo_fw::j2_ejecutor::{cuentas, iniciar_ejecutor, lanzar_ranuras};
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::perfil::{self, Promedios};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Cuanto dura cada muestra.
const MUESTRA_S: u64 = 5;

#[embassy_executor::main]
async fn main(spawner: Spawner) {
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

    perfil::iniciar();
    let f_cpu_medido = perfil::f_cpu_medido_hz().await;
    spawner.spawn(defmt::unwrap!(vueltas_del_hilo()));
    // La base, con el J2 sin arrancar: la CPU entera.
    let mut medidor = Medidor::calibrar(500).await;
    info!(
        "carga_j2: firmware {}, f_cpu {} Hz, f_cpu_medido {} Hz, periodo {} us, base {} vueltas/s",
        env!("SAM17_GIT"),
        f_cpu,
        f_cpu_medido,
        PERIODO_GIRO_US,
        medidor.base_por_s()
    );

    lanzar_ranuras(
        iniciar_ejecutor(interrupt::GFXTIM),
        [Some(ranura), None, None, None, None, None],
        bajada_del_banco,
        juez_del_banco,
        PERIODO_GIRO_US,
    );

    let mut promedios = Promedios::nuevo();
    let mut giros_antes = 0u32;
    let pasadas: &[&str] = if cfg!(feature = "reloj-hub") {
        &["no", "icache", "icache+dcache-sin-mpu"]
    } else {
        &["no", "icache"]
    };
    for &cache in pasadas {
        // SAFETY: nadie mas toca el SCB. La D-cache solo se enciende en la pasada
        // de exploracion, con el J2 ya girando y sin la region MPU (R-MJ7): `nueva`
        // asevero que estaba apagada al construir la ranura.
        unsafe {
            let mut p = cortex_m::Peripherals::steal();
            match cache {
                "icache" => p.SCB.enable_icache(),
                "icache+dcache-sin-mpu" => p.SCB.enable_dcache(&mut p.CPUID),
                _ => {}
            }
        }
        // La primera muestra de cada pasada absorbe el arranque o el cambio de
        // cache; la segunda es la que vale.
        for muestra in 0..2 {
            Timer::after_secs(MUESTRA_S).await;
            let c = cuentas(RANURA_BANCO);
            let libre = medidor.libre_por_mil();
            let dg = c.giros.wrapping_sub(giros_antes);
            giros_antes = c.giros;
            let (m, _) = promedios.tomar(c.giros);
            if muestra == 0 {
                continue;
            }
            info!(
                "carga_j2,cache={=str},ciclo_us={},giros_en_5s={},hilo_libre_permil={},atrasos={},plazos_vencidos={}",
                cache,
                (MUESTRA_S * 1_000_000) as u32 / dg.max(1),
                dg,
                libre,
                c.atrasos,
                c.plazos_vencidos
            );
            if m.iter().all(|x| *x == 0) {
                info!("carga_j2,cache={=str}: compilado sin `--features perfil`, los tramos salen en cero", cache);
            } else {
                info!(
                    "carga_j2,cache={=str},previo={},armado={},espera={},cierre={},posterior={},isr_spi={},ejecutor={}",
                    cache, m[0], m[1], m[2], m[3], m[4], m[5], m[7]
                );
            }
        }
    }
    info!("carga_j2: fin");
    // Un `bkpt` para que `probe-rs run` termine solo y suelte la sonda.
    cortex_m::asm::bkpt();
    loop {
        Timer::after_secs(60).await;
    }
}
