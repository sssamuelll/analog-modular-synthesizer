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
//! le comeria la CPU y falsearia la cuenta. El periodo depende del reloj: a 800
//! MHz (`reloj-hub`) es el del instrumento, [`PERIODO_GIRO_US`] (125 us); a 64
//! MHz son 1 ms, porque a 125 us el giro llega siempre tarde, el calendario
//! (`core::maestro_j2::Calendario`) deja un periodo de hueco y la medida es la
//! de un lazo saturado, que no se parece al del hub. Lo que se mide es el coste
//! del giro y lo que sobra para el hilo.
//!
//! Con `--features ranuras-2` o `ranuras-3` giran ademas una o dos ranuras de
//! relleno (SPI1 y SPI2, sin modulo detras; pines en `j2_banco`): el coste por
//! giro es el total entre todos los giros de todas las ranuras, y asi se ve que
//! parte es de cada ranura y cual se reparte (la ISR del reloj, la entrada del
//! ejecutor). Con `ranuras-3` a 64 MHz el periodo sube a 2 ms para que ninguna
//! ranura llegue tarde. Dos
//! pasadas: sin cache y con la I-cache encendida; con `--features reloj-hub` (el
//! nucleo a 800 MHz) hay una tercera con tambien la D-cache, **sin la region MPU
//! de los buferes del DMA** (R-MJ7): es de exploracion, los datos de los buferes
//! salen incoherentes y esa fila no sirve para la puerta. Se marca
//! `icache+dcache-sin-mpu`.
//!
//! **Una base por estado de cache.** El medidor del hilo cuenta vueltas y las compara
//! con las de la CPU entera, y con la I-cache el hilo da mas vueltas por segundo que
//! sin ella. Antes de arrancar el J2 se calibra una base con cada estado (encendiendo
//! las caches de a una y apagandolas al final); la pasada compara contra la suya. Con
//! una sola base, la de sin cache, el 17-10 salio 889 permil libres con un ejecutor
//! que ya gastaba el 22 % de la CPU: el J2 salia menor que su propio manejador.
//!
//! Por cada pasada, dos lineas:
//!
//! ```text
//! carga_j2,cache=<no|icache>,ranuras=,periodo_us=,ciclo_us=,giros_en_5s=,hilo_libre_permil=,atrasos=,plazos_vencidos=,base_por_s=
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
#[cfg(not(feature = "transporte-isr"))]
use embassy_stm32::interrupt;
use embassy_time::Timer;
use sam17_nucleo_core::maestro_j2::RANURAS_SPI;
use sam17_nucleo_fw::carga::{vueltas_del_hilo, Medidor};
use sam17_nucleo_fw::j2_banco::{
    bajada_del_banco, juez_del_banco, PERIODO_DE_MEDIDA_US, RANURAS_DE_MEDIDA,
};
use sam17_nucleo_fw::j2_ejecutor::cuentas;
#[cfg(not(feature = "transporte-isr"))]
use sam17_nucleo_fw::j2_ejecutor::{iniciar_ejecutor, lanzar_ranuras};
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::perfil::{self, Promedios};
use sam17_nucleo_fw::ranuras_de_medida;
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Cuanto dura cada muestra.
const MUESTRA_S: u64 = 5;

#[cfg(all(feature = "transporte-isr", feature = "ranuras-2"))]
compile_error!("transporte-isr solo mueve la ranura 0: sin ranuras-2 ni ranuras-3");

const RANURAS_ACTIVAS: u32 = RANURAS_DE_MEDIDA;
const PERIODO_US: u32 = PERIODO_DE_MEDIDA_US;

/// Enciende las caches que pide la pasada, sin apagar las de la anterior: `icache` la
/// I-cache; `icache+dcache-sin-mpu`, ademas la D-cache.
fn encender_cache(cache: &str) {
    // SAFETY: nadie mas toca el SCB. La D-cache solo se enciende en la pasada de
    // exploracion, sin la region MPU (R-MJ7): `nueva` asevera que estaba apagada al
    // construir la ranura, y las ranuras ya estan construidas.
    unsafe {
        let mut p = cortex_m::Peripherals::steal();
        match cache {
            "icache" => p.SCB.enable_icache(),
            "icache+dcache-sin-mpu" => p.SCB.enable_dcache(&mut p.CPUID),
            _ => {}
        }
    }
}

/// Deja las caches apagadas, como las encuentra el J2 al arrancar.
fn apagar_caches() {
    // SAFETY: igual, y sin DMA en vuelo: el J2 todavia no ha arrancado.
    unsafe {
        let mut p = cortex_m::Peripherals::steal();
        p.SCB.disable_dcache(&mut p.CPUID);
        p.SCB.disable_icache();
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    #[cfg(feature = "reloj-hub")]
    let config = usb::configuracion_hub();
    #[cfg(not(feature = "reloj-hub"))]
    let config = usb::configuracion();
    let f_cpu = usb::f_cpu_hz(&config);
    let p = usb::iniciar(config);
    let cfg = Config {
        f_sck_hz: 10_000_000,
        f_cpu_hz: f_cpu,
        retardo_tsck_cuartos: 4,
    };
    let ranuras = ranuras_de_medida!(p, cfg);

    perfil::iniciar();
    let f_cpu_medido = perfil::f_cpu_medido_hz().await;
    spawner.spawn(defmt::unwrap!(vueltas_del_hilo()));
    let pasadas: &[&str] = if cfg!(feature = "reloj-hub") {
        &["no", "icache", "icache+dcache-sin-mpu"]
    } else {
        &["no", "icache"]
    };
    // Una base por estado de cache, con el J2 sin arrancar: la CPU entera en cada uno.
    let mut medidores: [Option<Medidor>; 3] = [None, None, None];
    for (i, &cache) in pasadas.iter().enumerate() {
        encender_cache(cache);
        medidores[i] = Some(Medidor::calibrar(500).await);
    }
    apagar_caches();
    info!(
        "carga_j2: firmware {}, f_cpu {} Hz, f_cpu_medido {} Hz, periodo {} us, base {} vueltas/s, transporte {=str}",
        env!("SAM17_GIT"),
        f_cpu,
        f_cpu_medido,
        PERIODO_US,
        medidores[0].as_ref().map_or(0, |m| m.base_por_s()),
        if cfg!(feature = "transporte-isr") {
            "isr"
        } else {
            "ejecutor"
        }
    );

    #[cfg(not(feature = "transporte-isr"))]
    lanzar_ranuras(
        iniciar_ejecutor(interrupt::GFXTIM),
        ranuras,
        bajada_del_banco,
        juez_del_banco,
        PERIODO_US,
    );
    #[cfg(feature = "transporte-isr")]
    {
        let [r0, ..] = ranuras;
        sam17_nucleo_fw::j2_isr::lanzar(
            defmt::unwrap!(r0),
            p.TIM7,
            PERIODO_US,
            bajada_del_banco,
            juez_del_banco,
        );
    }

    let mut promedios = Promedios::nuevo();
    let mut giros_antes = 0u32;
    for (i, &cache) in pasadas.iter().enumerate() {
        encender_cache(cache);
        let medidor = defmt::unwrap!(medidores[i].as_mut());
        // La primera muestra de cada pasada absorbe el arranque o el cambio de
        // cache; la segunda es la que vale.
        for muestra in 0..2 {
            Timer::after_secs(MUESTRA_S).await;
            let (mut giros, mut atrasos, mut plazos) = (0u32, 0u32, 0u32);
            for n in 0..RANURAS_SPI {
                let c = cuentas(n);
                giros = giros.wrapping_add(c.giros);
                atrasos = atrasos.wrapping_add(c.atrasos);
                plazos = plazos.wrapping_add(c.plazos_vencidos);
            }
            let libre = medidor.libre_por_mil();
            let dg = giros.wrapping_sub(giros_antes);
            giros_antes = giros;
            let (m, _) = promedios.tomar(giros);
            if muestra == 0 {
                continue;
            }
            info!(
                "carga_j2,cache={=str},ranuras={},periodo_us={},ciclo_us={},giros_en_5s={},hilo_libre_permil={},atrasos={},plazos_vencidos={},base_por_s={}",
                cache,
                RANURAS_ACTIVAS,
                PERIODO_US,
                (MUESTRA_S * 1_000_000) as u32 * RANURAS_ACTIVAS / dg.max(1),
                dg,
                libre,
                atrasos,
                plazos,
                medidor.base_por_s()
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
