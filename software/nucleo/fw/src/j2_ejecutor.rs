//! El ejecutor del J2 y sus seis tareas: el transporte que une el driver de
//! [`crate::j2_spi`] con la politica de `core::maestro_j2` (spec D5).
//!
//! Spec: `docs/superpowers/specs/`
//! `2026-09-03-maestro-j2-recuperacion-design.md`, D5 (la reescritura que mato
//! al vigia) y D7 (la ranura nunca deja de girar).
//!
//! **Seis tareas, una por ranura** (D5.1). En serie no caben: seis `NADA` de 25
//! bytes al piso de 10 MHz son 120 us mas seis `T_GAP` dentro de un giro de 125
//! us. Los seis perifericos y sus doce canales de DMA corren en paralelo por
//! hardware; las tareas solo los atienden, y un plazo vencido en una no retrasa
//! a las otras cinco.
//!
//! **El planificador sigue siendo el unico escritor del enlace** (D5.2, R-C8).
//! Estas tareas son transporte, como lo son los canales de DMA: preguntan que
//! baja ([`Bajada`]), clocan, preguntan si lo que subio vale ([`Juez`]) y le
//! pasan el evento a la politica. **No deciden nada del protocolo** y no miran
//! el contenido de ningun byte.
//!
//! **Las seis viven en un `InterruptExecutor` propio** (D5.3, R-MJ5), no en el
//! ejecutor de hilo donde viven la pantalla, el USB y el MIDI (`main.rs`). Una
//! tarea de pantalla que retenga la CPU 15 ms no retrasa un giro del J2 ni un
//! microsegundo; sin esto, la simulacion de la junta da giros perdidos a partir
//! de 6 ms de retencion (H-9).
//!
//! **El vector que presta su linea es `GFXTIM`.** Los STM32 no tienen
//! interrupciones reservadas para software, asi que se toma un vector libre,
//! igual que el ejemplo de embassy toma `UART4`/`UART5`
//! (`examples/stm32h7/src/bin/multiprio.rs:108-145`). `GFXTIM` es el
//! temporizador del acelerador grafico: existe en el `Interrupt` del N657
//! (`_generated.rs` de este build, `interrupt_mod!` linea 755) y el hub no lo
//! usa (`grep -rn GFXTIM src/` fuera de este archivo da cero). Si algun dia el
//! cerebro dibuja con el GFXTIM, se cambia por otro periferico ausente y se
//! deja la razon aqui.
//!
//! **Las prioridades.** Lo que viene de EN-PLACA (casilla del 11-09) es la
//! **relacion**: las ISR del SPI y de los canales del GPDMA por encima del
//! ejecutor del J2, y este por encima del de hilo. Los dos numeros concretos
//! (`P1` y `P2`) los elige esta tarea y no hay papel que los fije.
//!
//! `embassy_stm32::interrupt` numera al reves que la urgencia:
//! `Priority::P0 = 0x0`, `P1 = 0x10`, `P2 = 0x20`...
//! (`embassy-hal-internal/src/interrupt.rs:324-341`, la variante `prio-bits-4`
//! que pide `embassy-stm32/Cargo.toml:164`; `P1` en `:331`, `P2` en `:332`), y
//! el NVIC atiende antes el numero mas bajo. Asi que:
//!
//! - las ISR del SPI y de los canales del GPDMA van a **`P1`**, por encima;
//! - el ejecutor del J2 va a **`P2`** ([`PRIORIDAD_EJECUTOR`]), y lo fija
//!   [`arrancar`];
//! - el ejecutor de hilo corre en modo hilo, que esta por debajo de cualquier
//!   interrupcion habilitada, asi que queda debajo por construccion.
//!
//! **Lo que ponen los binarios antes de llamar a [`arrancar`]:** nada del NVIC.
//! El `bind_interrupts!` vive una sola vez en [`crate::j2_banco::IrqsBanco`]
//! (R23) -- `SPI5 => j2_spi::Isr<0>`, los cuatro canales del GPDMA a
//! `embassy_stm32::dma::InterruptHandler` y `EXTI11 => j2_esclavo::IsrCs` --, y
//! las prioridades `P1` y el `enable` los pone quien arma cada interrupcion:
//! `j2_spi::Ranura::nueva` y `j2_esclavo::Esclavo::nuevo` (R21). Los binarios
//! solo piden la `Ranura` a `j2_banco::maestro_del_banco` y se la pasan a
//! [`arrancar`]. Los nombres exactos de las lineas del N657 son `SPI5`, `SPI4` y
//! `GPDMA1_CHANNEL0`, `GPDMA1_CHANNEL1`, ... (no `GPDMA1_CH0`, que es el nombre
//! del *periferico*).
//!
//! **`Bajada` y `Juez` son punteros a funcion, no un trait.** Hoy hay un solo
//! planificador -- el del banco, que vive aparte en [`crate::j2_banco`] porque
//! no sobrevive a la cabecera --; el real llega cuando exista la cabecera en
//! codigo (#267), y entonces se le pasan sus dos funciones sin tocar este
//! archivo. Un trait con una sola implementacion seria abstraccion de adorno.
//! Este modulo **no conoce** ningun patron ni ningun sobre.
//!
//! **El plazo sale del `f_sck` de cada ranura, y lo da la ranura.** D3 pide
//! `f_reloj_sancionado(ranura)`, que es el reloj al que de verdad se cloca, no
//! el que se pidio: el `MBR` solo da potencias de dos y redondea hacia abajo
//! (10 MHz pedidos con el kernel en HSI 64 son 8 reales). Por eso cada tarea
//! usa `ranura.f_sck_hz()` y [`arrancar`] **no** recibe ningun reloj: no hay
//! forma de pasarle uno equivocado ni de etiquetar el CSV de resistencia con un
//! reloj que no existe.
//!
//! **La identidad se decreta (HUECO).** Cada tarea manda
//! `Evento::Identidad(true)` al arrancar, porque el descubrimiento por I2C no
//! existe todavia (#175). Hasta entonces, "tiene identidad" es "el binario le
//! paso una `Ranura`": una ranura `None` no tiene tarea, no se cloca y no se
//! cuenta (R-MJ6, D7.4).
//!
//! El sello de vitalidad de [`SELLOS`] lo **lee** el supervisor del hub (#291),
//! que es quien alimenta el IWDG; aqui solo sube (D5.4).

use core::sync::atomic::{AtomicBool, AtomicU32, Ordering};

use cortex_m::interrupt::InterruptNumber;
use embassy_executor::InterruptExecutor;
use embassy_stm32::interrupt;
use embassy_stm32::interrupt::{InterruptExt, Priority};
use embassy_time::{Duration, Instant, Ticker};
use sam17_nucleo_core::maestro_j2::{
    plazo_us, Evento, Ranura as Politica, Tsize, Umbrales, PERIODO_GIRO_US, RANURAS_SPI,
};

use crate::j2_spi::{Ranura, Resultado, LARGO_MAX};

/// El ejecutor de interrupcion del J2 (D5.3). Lo arranca [`arrancar`] y corre
/// sobre el vector `GFXTIM`, a [`PRIORIDAD_EJECUTOR`].
pub static EJECUTOR_J2: InterruptExecutor = InterruptExecutor::new();

/// La prioridad del ejecutor del J2. Por **debajo** de las ISR del SPI y de los
/// canales del GPDMA (`P1`) y por encima del ejecutor de hilo, que no es una
/// interrupcion. Menor numero = mas urgente; ver la cabecera del modulo.
pub const PRIORIDAD_EJECUTOR: Priority = Priority::P2;

/// El vector que el ejecutor del J2 toma prestado.
const IRQ_EJECUTOR: interrupt::Interrupt = interrupt::GFXTIM;

#[interrupt]
unsafe fn GFXTIM() {
    unsafe { EJECUTOR_J2.on_interrupt() }
}

/// Rellena la bajada de la ranura `n` y dice cuantos bytes se clocan.
///
/// Puntero a funcion, no trait: hoy hay un solo planificador (el de
/// [`crate::j2_banco`]); el real lo sustituye cuando exista la cabecera en
/// codigo (#267).
///
/// **Contrato del planificador:** el `Tsize` que devuelve son los bytes que ha
/// dejado escritos en `buf`, y no pasa de `LARGO_MAX`. El segundo lo asevera el
/// driver (`j2_spi::Ranura::giro`, *"TSIZE no cabe en los buferes"*), asi que un
/// planificador que se pase muere ahi y no cloca basura en silencio.
pub type Bajada = fn(n: usize, buf: &mut [u8; LARGO_MAX]) -> Tsize;

/// Dice si la subida de la ranura `n` vale. `true` = `Evento::SubidaOk`.
///
/// El juez de verdad valida el sobre y su CRC (cabecera D6.1); el del banco
/// compara contra un patron fijo.
pub type Juez = fn(n: usize, subida: &[u8]) -> bool;

/// Los cinco contadores y las dos marcas de una ranura (D7.3 y D7.5).
///
/// `giros` mide *"mi periferico termino"*; `subidas_ok` mide *"el modulo
/// contesto"*. Son dos cosas y por eso se cuentan aparte: un modulo muerto con
/// el MISO en pull-down da `EOT` perfecto y ceros.
#[derive(Clone, Copy, Debug, defmt::Format)]
pub struct Cuentas {
    pub giros: u32,
    pub plazos_vencidos: u32,
    pub eot_tardios: u32,
    pub subidas_ok: u32,
    pub subidas_malas: u32,
    pub inestable: bool,
    pub muda: bool,
}

/// El sello de vitalidad por ranura (D5.4).
///
/// Sube **al armar** cada transferencia, no al completarla: una ranura
/// reiniciando tambien esta viva. El J2 no alimenta el IWDG -- eso definiria la
/// vida del instrumento como *"el J2 dio un giro"* y una ranura sin modulo lo
/// disparaba diez veces por segundo (H-6). Quien lee esto es el supervisor de
/// vitalidad del hub (#291).
pub static SELLOS: [AtomicU32; RANURAS_SPI] = [const { AtomicU32::new(0) }; RANURAS_SPI];

/// Lo que cada tarea publica tras su giro. Sin `Mutex`: cada ranura escribe
/// solo su casilla y los binarios la leen.
struct CuentasAtomicas {
    giros: AtomicU32,
    plazos_vencidos: AtomicU32,
    eot_tardios: AtomicU32,
    subidas_ok: AtomicU32,
    subidas_malas: AtomicU32,
    inestable: AtomicBool,
    muda: AtomicBool,
}

impl CuentasAtomicas {
    const fn nuevas() -> Self {
        Self {
            giros: AtomicU32::new(0),
            plazos_vencidos: AtomicU32::new(0),
            eot_tardios: AtomicU32::new(0),
            subidas_ok: AtomicU32::new(0),
            subidas_malas: AtomicU32::new(0),
            inestable: AtomicBool::new(false),
            muda: AtomicBool::new(false),
        }
    }
}

static CUENTAS: [CuentasAtomicas; RANURAS_SPI] = [const { CuentasAtomicas::nuevas() }; RANURAS_SPI];

/// Las cuentas de la ranura `n`, para los binarios y la pantalla.
///
/// Una ranura sin tarea (la que llego `None`) devuelve ceros y las dos marcas
/// en `false`: no se cloca y no se cuenta (R-MJ6). No son una foto coherente de
/// un instante -- son siete atomicos leidos seguidos --, y no hace falta que lo
/// sean: son totales desde el arranque y quien los lee los imprime o los resta.
pub fn cuentas(n: usize) -> Cuentas {
    defmt::assert!(n < RANURAS_SPI, "J2: ranura fuera de rango");
    let c = &CUENTAS[n];
    Cuentas {
        giros: c.giros.load(Ordering::Relaxed),
        plazos_vencidos: c.plazos_vencidos.load(Ordering::Relaxed),
        eot_tardios: c.eot_tardios.load(Ordering::Relaxed),
        subidas_ok: c.subidas_ok.load(Ordering::Relaxed),
        subidas_malas: c.subidas_malas.load(Ordering::Relaxed),
        inestable: c.inestable.load(Ordering::Relaxed),
        muda: c.muda.load(Ordering::Relaxed),
    }
}

/// Arranca el ejecutor del J2 y lanza una tarea por cada ranura con modulo.
///
/// `irq` es el vector que el ejecutor toma prestado, y tiene que ser el mismo
/// que atiende el `#[interrupt]` de este modulo: `embassy_stm32::interrupt::`
/// `GFXTIM`. Se asevera, porque pasarle otro deja el ejecutor sin quien lo
/// bombee y las seis tareas mudas en silencio.
///
/// `ranuras` llega ya construida (`j2_spi::Ranura::nueva` la llaman los
/// binarios, que son los que tienen los pines y los canales). Las `None` no
/// tienen tarea: R-MJ6 y D7.4.
///
/// No hay parametro de reloj: el plazo de D3 sale de `ranura.f_sck_hz()`, que
/// es el `f_sck` real de esa ranura -- ver la cabecera del modulo.
pub fn arrancar(
    irq: impl InterruptNumber,
    ranuras: [Option<Ranura<'static>>; RANURAS_SPI],
    bajada: Bajada,
    juez: Juez,
) {
    defmt::assert!(
        irq.number() == IRQ_EJECUTOR.number(),
        "J2: el ejecutor solo corre sobre el vector que atiende su #[interrupt]"
    );
    // La prioridad va ANTES de `start`, y no es gusto: `start` desenmascara el
    // vector el mismo (`NVIC::unmask`) y su doc lo dice con mayusculas --
    // *"You must set the interrupt priority before calling this method. You
    // MUST NOT do it after"* (`embassy-executor/src/platform/cortex_m.rs`
    // :202-204).
    irq.set_priority(PRIORIDAD_EJECUTOR);
    let spawner = EJECUTOR_J2.start(irq);
    for (n, ranura) in ranuras.into_iter().enumerate() {
        let Some(ranura) = ranura else {
            defmt::info!("J2 ranura {}: sin modulo, no entra al lazo (D7.4)", n);
            continue;
        };
        spawner.spawn(defmt::unwrap!(tarea_ranura(n, ranura, bajada, juez)));
    }
}

/// El lazo de una ranura: un giro cada `PERIODO_GIRO_US`, siempre (D7.1).
///
/// No hay cadencia reducida, ni backoff, ni sondeo, ni "vuelta a sana": la
/// junta tumbo las cuatro. Un plazo vencido se reinicia dentro de `giro` (D4) y
/// el giro siguiente sale a su hora.
#[embassy_executor::task(pool_size = RANURAS_SPI)]
async fn tarea_ranura(n: usize, mut ranura: Ranura<'static>, bajada_fn: Bajada, juez: Juez) {
    // R-MJ4: los umbrales son de `core`, no se copia ninguno aqui.
    let umbrales = Umbrales::POR_DEFECTO;
    // D3 pide `f_reloj_sancionado(ranura)`: el reloj REAL de esta ranura, el
    // que sale del `MBR`, no el que se pidio. Lo da la propia ranura.
    let f_sck_hz = ranura.f_sck_hz();
    let mut politica = Politica::nueva(umbrales);
    // HUECO: identidad por decreto hasta que exista el descubrimiento por I2C
    // (#175). Que el binario haya construido esta `Ranura` ES la identidad.
    let _ = politica.paso(Evento::Identidad(true), ahora_us());

    let mut bajada = [0u8; LARGO_MAX];
    let mut subida = [0u8; LARGO_MAX];
    // 8 kHz, spec sec.3 (`PERIODO_GIRO_US` = 125). El grano de `embassy_time`
    // es 1 us (`embassy-time-driver/src/tick.rs`, `TICK_HZ` por defecto
    // 1_000_000), asi que 125 us es exacto y no hay deriva por redondeo.
    //
    // El `Ticker` no se salta los tics perdidos por su cuenta: `next` suma
    // `duration` a `expires_at` y devuelve `Ready` mientras siga atrasado
    // (`embassy-time/src/timer.rs:470-480`). Tras un giro que se pasa del
    // periodo eso sacaria los dos giros siguientes pegados, y por eso el brazo
    // de `PlazoVencido` lo realinea -- ver alli.
    let mut ticker = Ticker::every(Duration::from_micros(PERIODO_GIRO_US as u64));

    loop {
        ticker.next().await;

        // El planificador decide que baja; la tarea solo lo cloca (D5.2).
        let tsize = bajada_fn(n, &mut bajada);

        // D5.4: el sello sube al ARMAR, antes del giro.
        SELLOS[n].fetch_add(1, Ordering::Relaxed);
        let _ = politica.paso(Evento::Armada, ahora_us());

        // D3: el plazo sale de la politica, con el `f_sck` real.
        let plazo = Duration::from_micros(plazo_us(tsize, f_sck_hz, &umbrales) as u64);
        let (res, tardios) = ranura.giro(&bajada, &mut subida, tsize, plazo).await;

        // D2 regla 1: los `EOT` que el armado descarto por venir de una
        // generacion vieja. No hay nada que reiniciar por ellos.
        for _ in 0..tardios {
            let _ = politica.paso(Evento::EotTardio, ahora_us());
        }

        match res {
            Resultado::Ok => {
                let _ = politica.paso(Evento::GiroOk, ahora_us());
                let ev = if juez(n, &subida[..tsize.get() as usize]) {
                    Evento::SubidaOk
                } else {
                    Evento::SubidaMala
                };
                let _ = politica.paso(ev, ahora_us());
            }
            Resultado::PlazoVencido => {
                // D4 ya corrio DENTRO de `giro`; aqui solo se cuenta. La
                // `Accion::Reiniciar` que devuelve la politica es redundante a
                // proposito y no se ejecuta otra vez.
                let _ = politica.paso(Evento::PlazoVencido, ahora_us());
                // Realinear el lazo a partir de AHORA, y perder los tics que
                // el giro largo se comio en vez de recuperarlos. Lo que honra
                // es `T_GAP`: sin esto los dos giros siguientes saldrian
                // pegados -- el NSS subiendo y bajando casi sin hueco -- justo
                // cuando al esclavo le acaban de arrancar el `CS` y esta en su
                // `SPE = 0` -> `SPE = 1` antes de rearmar el DMA de recepcion.
                // `T_GAP` existe para ese rearme y es una constante del
                // planificador del cerebro, HUECO con 2 us provisionales
                // (cabecera `2026-09-02-cabecera-j2-design.md`, D8: *"T_GAP es
                // una constante del planificador del cerebro, HUECO hasta el
                // bring-up, con valor provisional de 2 us"*); en regimen lo
                // aportan los 125 us de cadencia, y una rafaga lo borraria.
                //
                // Lo que NO rompe: el techo de recuperacion de la spec sec.3.
                // Realineado son 220 de plazo + 20 de reinicio + como mucho
                // 125 de alineacion = 365 us, por debajo de los 490 (tres
                // giros) que ese calculo publica.
                //
                // `Ticker::reset` es `expires_at = Instant::now() + duration`
                // (`embassy-time/src/timer.rs:402-404`).
                ticker.reset();
            }
        }

        // `Evento::Tick` no hace falta: `paso` pone su `ahora_us` en cada
        // evento y aqui pasa por lo menos uno por giro, asi que la ventana de
        // `inestable` (D7.3) desliza sola.
        publicar_cuentas(n, &politica);
    }
}

/// Publica los cinco contadores y las dos marcas de la ranura `n` (D7.3, D7.5).
fn publicar_cuentas(n: usize, politica: &Politica) {
    let c = &CUENTAS[n];
    c.giros.store(politica.giros(), Ordering::Relaxed);
    c.plazos_vencidos
        .store(politica.plazos_vencidos(), Ordering::Relaxed);
    c.eot_tardios
        .store(politica.eot_tardios(), Ordering::Relaxed);
    c.subidas_ok.store(politica.subidas_ok(), Ordering::Relaxed);
    c.subidas_malas
        .store(politica.subidas_malas(), Ordering::Relaxed);
    c.inestable.store(politica.inestable(), Ordering::Relaxed);
    c.muda.store(politica.muda(), Ordering::Relaxed);
}

fn ahora_us() -> u64 {
    Instant::now().as_micros()
}

/// `SendSpawner::spawn` exige `S: Send` (`embassy-executor/src/spawner.rs:223`),
/// asi que el futuro de [`tarea_ranura`] tiene que serlo, y con el todo lo que
/// se lleva dentro. Que la `Ranura` del driver lo sea queda comprobado por el
/// compilador aqui y no por lectura, que es lo que pidio la revision del driver.
const _: () = {
    const fn es_send<T: Send>() {}
    es_send::<Ranura<'static>>();
};

/// `pool_size` admite una expresion constante (`embassy-executor-macros/src/`
/// `macros/task.rs:15`, `pool_size: Option<syn::Expr>`), asi que la tarea usa
/// `RANURAS_SPI` directo y este aserto sobra. Queda como testigo de que el 6 de
/// D5.1 y el del pool son el mismo numero si alguien cambia uno.
const _: () = assert!(RANURAS_SPI == 6);
