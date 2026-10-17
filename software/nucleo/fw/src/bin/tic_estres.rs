#![no_std]
#![no_main]

//! **El transporte por tic con marcos numerados, bajo preempcion al azar.**
//!
//! Revision de Halberg del 17-10, hallazgo 2: las corridas largas no podian ver una trama rota, repetida
//! o vieja, porque el contenido era fijo y el tic y el planificador caian siempre en la misma fase. Aqui
//! las dos cosas cambian:
//!
//! - **Marcos numerados** (`core::marcos_j2`). El cerebro numera cada bajada; el esclavo del banco clasifica
//!   la que recibe (rota, repetida, atrasada, o buena con los numeros que se saltaron) y devuelve el ultimo
//!   numero aceptado en la subida; el juez del cerebro clasifica la subida (rota, atrasada, futura).
//! - **Un golpe de P3 al azar.** Una interrupcion de la prioridad del planificador y de duracion y momento
//!   al azar le quita al planificador y a la recuperacion el sitio detras del tic: sus pasadas dejan de
//!   caer siempre justo despues de el y el tic pasa a interrumpirlas en puntos al azar (`compone`,
//!   `Subida::leer`, `recupera`). Va a P3 y no a P2 para no pegarle tambien al esclavo del banco, que es
//!   una tarea de P2.
//!
//! Cuatro fases, cada una de `FASE_S` segundos: sin nada; con golpes; con incidentes (cuelgues y errores del
//! DMA, uno de cada cuatro a cinco turnos); y con las dos cosas. Se publica una sola vez al final. Pasa si en
//! todas las fases `bajadas_rotas`, `bajadas_repetidas`, `bajadas_atrasadas`, `subidas_rotas`,
//! `subidas_atrasadas` y `subidas_futuras` son cero, ninguna ranura muere y cada plazo vencido acaba en una
//! recuperacion.
//!
//! ```bash
//! cargo run --release --features inyeccion,secuencia,reloj-hub,pines-medio --bin tic_estres
//! ```
//!
//! Va con los pines del J2 a `Medium`: con `VeryHigh` el cableado de puentes del banco rompe los marcos de
//! apariencia aleatoria (`tic_contenidos` y `EN-PLACA.md`) y el binario fallaria por el cable, no por el
//! transporte.

// Sin los bordes lentos el binario "falla" por el cable del banco, no por el transporte (ver arriba).
#[cfg(not(any(feature = "pines-medio", feature = "pines-bajo")))]
compile_error!(
    "tic_estres necesita `pines-medio` (o `pines-bajo`): con los bordes `VeryHigh` el cable del banco rompe los marcos"
);

use core::sync::atomic::Ordering;

use defmt::info;
use embassy_executor::Spawner;
use embassy_stm32::interrupt;
use embassy_stm32::interrupt::Priority;
use embassy_time::{Duration, Instant, Timer};
use sam17_nucleo_core::maestro_j2::PERIODO_GIRO_US;
use sam17_nucleo_fw::j2_banco::{esclavo_del_banco, maestro_del_banco, secuencia, RANURA_BANCO};
use sam17_nucleo_fw::j2_ejecutor::{cuentas, iniciar_ejecutor};
use sam17_nucleo_fw::j2_esclavo::{self, tarea_esclavo};
use sam17_nucleo_fw::j2_spi::Config;
use sam17_nucleo_fw::j2_tic::{self, acapara};
use sam17_nucleo_fw::usb;
use {defmt_rtt as _, panic_probe as _};

/// Cuanto dura cada fase, en segundos: 60, 5 con `--features corta` o 150 con `--features larga` (diez minutos).
const FASE_S: u64 = if cfg!(feature = "corta") {
    5
} else if cfg!(feature = "larga") {
    150
} else {
    60
};

/// Un generador de bolsillo. La semilla es fija: la corrida se puede repetir.
struct Azar(u32);

impl Azar {
    fn sig(&mut self) -> u32 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 17;
        self.0 ^= self.0 << 5;
        self.0
    }
}

/// Todo lo que se mira, antes y despues de cada fase.
#[derive(Clone, Copy, Default)]
struct Foto {
    giros: u32,
    subidas_malas: u32,
    plazos: u32,
    tramas_ok: u32,
    tramas_cortas: u32,
    bajadas_ok: u32,
    bajadas_rotas: u32,
    bajadas_repetidas: u32,
    bajadas_atrasadas: u32,
    bajadas_saltos: u32,
    subidas_buenas: u32,
    subidas_rotas: u32,
    subidas_atrasadas: u32,
    subidas_futuras: u32,
    subidas_repetidas: u32,
    subidas_saltos: u32,
    sin_bajada: u32,
    subidas_perdidas: u32,
    eventos_perdidos: u32,
    recuperaciones: u32,
    errores_dma: u32,
    muertas: u32,
    tics_tardios: u32,
}

fn foto() -> Foto {
    let c = cuentas(RANURA_BANCO);
    let t = j2_tic::testigos();
    let r = Ordering::Relaxed;
    Foto {
        giros: c.giros,
        subidas_malas: c.subidas_malas,
        plazos: c.plazos_vencidos,
        tramas_ok: j2_esclavo::TRAMAS_OK.load(r),
        tramas_cortas: j2_esclavo::TRAMAS_CORTAS.load(r),
        bajadas_ok: j2_esclavo::BAJADAS_OK.load(r),
        bajadas_rotas: j2_esclavo::BAJADAS_ROTAS.load(r),
        bajadas_repetidas: j2_esclavo::BAJADAS_REPETIDAS.load(r),
        bajadas_atrasadas: j2_esclavo::BAJADAS_ATRASADAS.load(r),
        bajadas_saltos: j2_esclavo::BAJADAS_SALTOS.load(r),
        subidas_buenas: secuencia::SUBIDAS_BUENAS.load(r),
        subidas_rotas: secuencia::SUBIDAS_ROTAS.load(r),
        subidas_atrasadas: secuencia::SUBIDAS_ATRASADAS.load(r),
        subidas_futuras: secuencia::SUBIDAS_FUTURAS.load(r),
        subidas_repetidas: secuencia::SUBIDAS_REPETIDAS.load(r),
        subidas_saltos: secuencia::SUBIDAS_SALTOS.load(r),
        sin_bajada: t.sin_bajada,
        subidas_perdidas: t.subidas_perdidas,
        eventos_perdidos: t.eventos_perdidos,
        recuperaciones: t.recuperaciones,
        errores_dma: t.errores_dma,
        muertas: t.ranuras_muertas,
        tics_tardios: t.tics_tardios,
    }
}

/// Una fase: `FASE_S` segundos de golpes y/o incidentes al azar. Devuelve cuantos golpes y cuantos
/// incidentes se pidieron (un incidente pedido dos veces antes de que el tic lo consuma cuenta una).
async fn fase(golpes: bool, incidentes: bool, azar: &mut Azar) -> (u32, u32, u32) {
    let fin = Instant::now() + Duration::from_secs(FASE_S);
    let (mut g, mut cuelgues, mut errores) = (0u32, 0u32, 0u32);
    while Instant::now() < fin {
        if golpes {
            // De 10 a 280 us: por debajo de lo que mata a una ranura y de sobra para que el
            // planificador pierda su sitio detras del tic.
            acapara::golpe(10 + azar.sig() % 271);
            g += 1;
        }
        if incidentes {
            let r = azar.sig() % 16;
            if r < 4 {
                j2_tic::envenena(0);
                cuelgues += 1;
            } else if r == 4 {
                j2_tic::envenena_dma(0);
                errores += 1;
            }
        }
        Timer::after_micros(500 + u64::from(azar.sig() % 4000)).await;
    }
    (g, cuelgues, errores)
}

fn informa(nombre: &'static str, k: usize, a: &Foto, d: &Foto, pedidos: (u32, u32, u32)) {
    info!(
        "tic_estres,{=usize},{=str},pedidos: golpes={},cuelgues={},errores_dma={}",
        k, nombre, pedidos.0, pedidos.1, pedidos.2
    );
    info!(
        "tic_estres,{=usize},maestro: giros={},subidas_malas={},plazos={},recuperaciones={},errores_dma={},muertas={},sin_bajada={},subidas_perdidas={},eventos_perdidos={},tics_tardios={}",
        k,
        d.giros - a.giros,
        d.subidas_malas - a.subidas_malas,
        d.plazos - a.plazos,
        d.recuperaciones - a.recuperaciones,
        d.errores_dma - a.errores_dma,
        d.muertas,
        d.sin_bajada - a.sin_bajada,
        d.subidas_perdidas - a.subidas_perdidas,
        d.eventos_perdidos - a.eventos_perdidos,
        d.tics_tardios - a.tics_tardios
    );
    info!(
        "tic_estres,{=usize},esclavo: tramas_ok={},tramas_cortas={},bajadas_buenas={},bajadas_rotas={},bajadas_repetidas={},bajadas_atrasadas={},numeros_saltados={}",
        k,
        d.tramas_ok - a.tramas_ok,
        d.tramas_cortas - a.tramas_cortas,
        d.bajadas_ok - a.bajadas_ok,
        d.bajadas_rotas - a.bajadas_rotas,
        d.bajadas_repetidas - a.bajadas_repetidas,
        d.bajadas_atrasadas - a.bajadas_atrasadas,
        d.bajadas_saltos - a.bajadas_saltos
    );
    info!(
        "tic_estres,{=usize},juez: subidas_buenas={},rotas={},atrasadas={},futuras={},repetidas={},numeros_saltados={}",
        k,
        d.subidas_buenas - a.subidas_buenas,
        d.subidas_rotas - a.subidas_rotas,
        d.subidas_atrasadas - a.subidas_atrasadas,
        d.subidas_futuras - a.subidas_futuras,
        d.subidas_repetidas - a.subidas_repetidas,
        d.subidas_saltos - a.subidas_saltos
    );
    let integra = d.bajadas_rotas == a.bajadas_rotas
        && d.bajadas_repetidas == a.bajadas_repetidas
        && d.bajadas_atrasadas == a.bajadas_atrasadas
        && d.subidas_rotas == a.subidas_rotas
        && d.subidas_atrasadas == a.subidas_atrasadas
        && d.subidas_futuras == a.subidas_futuras;
    let recupera = d.recuperaciones - a.recuperaciones == d.plazos - a.plazos;
    let viva = d.muertas == 0;
    if integra && recupera && viva {
        info!("tic_estres,{=usize},{=str},ok", k, nombre);
    } else {
        info!(
            "tic_estres,{=usize},{=str},FALLA: integridad={},cada_plazo_una_recuperacion={},ninguna_muerta={}",
            k, nombre, integra, recupera, viva
        );
    }
}

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
    let esclavo = esclavo_del_banco(p.PE2, p.PE14, p.PE13, p.PE11, p.GPDMA1_CH2, p.GPDMA1_CH3);
    let spawner_j2 = iniciar_ejecutor(interrupt::GFXTIM);
    spawner_j2.spawn(defmt::unwrap!(tarea_esclavo(esclavo)));
    let mut ranuras = [const { None }; 6];
    ranuras[RANURA_BANCO] = Some(ranura);
    j2_tic::lanzar(
        ranuras,
        p.TIM7,
        PERIODO_GIRO_US,
        f_cpu,
        secuencia::bajada,
        secuencia::juez,
    );
    // SAFETY: nadie mas toca el SCB en este binario.
    unsafe {
        let mut cp = cortex_m::Peripherals::steal();
        cp.SCB.enable_icache();
        cp.SCB.enable_dcache(&mut cp.CPUID);
    }
    acapara::arranca(Priority::P3);
    Timer::after_millis(500).await;

    let mut azar = Azar(0x2F6E_2B1D);
    let nombres = [
        "sin nada",
        "golpes de P3",
        "cuelgues y errores del DMA",
        "golpes, cuelgues y errores",
    ];
    let mut fotos = [Foto::default(); 5];
    let mut pedidos = [(0u32, 0u32, 0u32); 4];
    fotos[0] = foto();
    for (k, (golpes, incidentes)) in [(false, false), (true, false), (false, true), (true, true)]
        .into_iter()
        .enumerate()
    {
        pedidos[k] = fase(golpes, incidentes, &mut azar).await;
        // Un respiro para que lo pendiente se asiente antes de la foto.
        Timer::after_millis(50).await;
        fotos[k + 1] = foto();
    }

    info!(
        "tic_estres: firmware {}, f_cpu {} Hz, fase {} s, {} bytes por marco",
        env!("SAM17_GIT"),
        f_cpu,
        FASE_S,
        sam17_nucleo_fw::j2_banco::LARGO_BANCO
    );
    for k in 0..4 {
        informa(nombres[k], k, &fotos[k], &fotos[k + 1], pedidos[k]);
    }
    info!("tic_estres,total: {}", j2_tic::testigos());
    info!(
        "tic_estres,compuestas={}",
        secuencia::COMPUESTAS.load(Ordering::Relaxed)
    );
    info!("tic_estres: fin");
    // Un `bkpt` para que `probe-rs run` termine solo y suelte la sonda.
    cortex_m::asm::bkpt();
    loop {
        Timer::after_secs(60).await;
    }
}
