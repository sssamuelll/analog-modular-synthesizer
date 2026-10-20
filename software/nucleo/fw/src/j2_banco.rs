//! El banco: **el montaje del 11-09 en un solo sitio**, mas el planificador de
//! mentira de 25 bytes que bajan y 25 que tienen que subir.
//!
//! # El montaje, una vez (R23)
//!
//! [`maestro_del_banco`], [`esclavo_del_banco`] e [`IrqsBanco`] son el montaje
//! de la NUCLEO-N657X0-Q escrito **una sola vez**. Antes vivia copiado en cada
//! binario -- los once argumentos de `Ranura::nueva`, los nueve de
//! `Esclavo::nuevo` y el `bind_interrupts!`, tres y dos y dos veces -- y esa
//! copia no era solo fea: **un pin equivocado compilaba igual**. Los limites de
//! `Ranura::nueva` son `Sck: gpio::Pin` y los del `_generated.rs` son
//! `SckPin<SPI5>`/`MosiPin<SPI5>`, que aceptan varios pines cada uno, asi que
//! cambiar PG2 por PG1 en una sola de las tres copias pasaba la puerta y salia
//! en la placa como un enlace mudo.
//!
//! Aqui los pines y los canales van como **tipos concretos**
//! (`Peri<'static, peripherals::PE15>`, no `impl SckPin<SPI5>`), asi que el
//! montaje esta clavado en la firma y equivocarse es un error de compilacion.
//!
//! Los binarios se quedan con tres o cuatro lineas de construccion y **sin
//! `bind_interrupts!` propio**.
//!
//! **Efecto de tener el `bind_interrupts!` en la biblioteca, dicho:** sus
//! manejadores se enlazan en **todos** los binarios que usen esta biblioteca,
//! tambien donde no hay esclavo (`plazos_j2`), donde no hay driver del J2
//! (`control_positivo`) y en el instrumento (`main.rs`). Es inofensivo: una ISR
//! solo corre si alguien desenmascara su linea en el NVIC, y eso lo hacen
//! `Ranura::nueva` (la del SPI) y `Esclavo::nuevo` (la del `EXTI11`), que en
//! esos binarios no se llaman. Las cuatro del GPDMA si quedan desenmascaradas --
//! las desenmascara `embassy_stm32::init` para los dieciseis canales --, y ahi
//! el cambio es a mejor: antes caian en el `DefaultHandler` de `cortex-m-rt`,
//! que es un bucle infinito, y ahora caen en el manejador de embassy, que es el
//! que sabe que hacer con un canal ocioso.
//!
//! # El planificador de mentira
//!
//! **Es el sustituto de bench del CRC del sobre**, no el juez de verdad. La
//! cabecera del J2 pone un sobre con su CRC en cada giro y el maestro lo
//! valida (`2026-09-02-cabecera-j2-design.md`, D6.1); antes de que el sobre
//! estuviera en codigo el banco necesitaba algo que distinguiera *"el modulo
//! contesto bien"* de *"el modulo devolvio basura"*, y esto era lo mas simple
//! que lo hacia. El juez de verdad es [`juez_sobre`], con el sobre de
//! `core::j2`; el patron se queda porque el esclavo del banco lo publica y las
//! pruebas del cable lo leen.
//!
//! Vive aparte de [`crate::j2_ejecutor`] a proposito: el ejecutor sobrevive a
//! la cabecera y el banco no. El ejecutor no conoce este modulo -- toma
//! `Bajada` y `Juez` como punteros a funcion y los binarios le pasan estos dos.
//!
//! El patron cambia con el indice (`0x5A ^ i` abajo, `0xA5 ^ i` arriba) porque
//! un relleno constante no veria un desplazamiento de un byte, que es justo el
//! sintoma que deja un esclavo al que le arrancaron el `CS` a mitad de trama
//! (spec del maestro D4, y la enmienda al papel del modulo: `SPE = 0` →
//! `SPE = 1` antes de rearmar el DMA).

use core::cell::UnsafeCell;

use embassy_stm32::{dma, pac, peripherals, Peri};
use sam17_nucleo_core::j2;
use sam17_nucleo_core::maestro_j2::{Tsize, PERIODO_GIRO_US};

use crate::j2_esclavo::{Esclavo, IsrCs};
use crate::j2_spi::{Config, Isr, Ranura, LARGO_MAX};

// El doc va DENTRO de la invocacion: el `bind_interrupts!` de embassy lo acepta
// como `$(#[$outer:meta])*` y se lo pasa a la `struct` que genera
// (`embassy-stm32/src/lib.rs:310` y `:321`). Fuera, rustdoc avisa de que no
// documenta invocaciones de macro y la puerta cae por el warning.
embassy_stm32::bind_interrupts!(
    /// Las seis ataduras del banco, en un solo sitio (R23).
    ///
    /// `bind_interrupts!` deriva `Copy`, asi que el mismo valor sirve de
    /// `irq_tx`, de `irq_rx` y del `irqs` compuesto que pide `Esclavo::nuevo`
    /// -- que exige en el **tipo** las tres suyas: los dos canales y
    /// `EXTI11 => IsrCs`.
    ///
    /// Los nombres son los de las lineas del N657, verificados en el
    /// `_generated.rs` de este build: `SPI5`, `EXTI11` y `GPDMA1_CHANNELn` --
    /// **no** `GPDMA1_CHn`, que es el nombre del *periferico*
    /// (`dma_channel_impl!(GPDMA1_CH0, ...::GPDMA1_CHANNEL0)`).
    pub struct IrqsBanco {
        SPI5 => Isr<0>;
        SPI1 => Isr<2>;
        SPI2 => Isr<3>;
        GPDMA1_CHANNEL0 => dma::InterruptHandler<peripherals::GPDMA1_CH0>;
        GPDMA1_CHANNEL1 => dma::InterruptHandler<peripherals::GPDMA1_CH1>;
        GPDMA1_CHANNEL2 => dma::InterruptHandler<peripherals::GPDMA1_CH2>;
        GPDMA1_CHANNEL3 => dma::InterruptHandler<peripherals::GPDMA1_CH3>;
        GPDMA1_CHANNEL4 => dma::InterruptHandler<peripherals::GPDMA1_CH4>;
        GPDMA1_CHANNEL5 => dma::InterruptHandler<peripherals::GPDMA1_CH5>;
        GPDMA1_CHANNEL6 => dma::InterruptHandler<peripherals::GPDMA1_CH6>;
        GPDMA1_CHANNEL7 => dma::InterruptHandler<peripherals::GPDMA1_CH7>;
        EXTI11 => IsrCs;
    }
);

/// La ranura del banco. Es la 0 en todas partes: en `arrancar`, en `cuentas` y
/// en la primera columna de la fila de `resistencia_j2.csv`.
///
/// El maestro va en **SPI5** a proposito: es la instancia del repro original de
/// jake-taf, que despues confirmo el cuelgue tambien en SPI1 (2026-09-03).
pub const RANURA_BANCO: usize = 0;

/// El maestro del banco: SPI5 con los cuatro pines del montaje y los dos
/// primeros canales del GPDMA1.
///
/// **Los pines van por tipo concreto, no por `impl SckPin<SPI5>`**, y esa es
/// toda la gracia de esta funcion: el montaje queda clavado en la firma y un
/// pin cambiado no compila. Ver la cabecera del modulo.
///
/// El montaje, citado **una sola vez** (UM3417 Rev 3, Tabla 13, p. 32; y
/// `EN-PLACA.md`, seccion *«El J2 en la Nucleo»*). Los ocho pines llevan la nota
/// (1) de la Tabla 18 de DS14791 Rev 10 -- *«Power supply is VDD»* -- y
/// estructura `TT`, asi que el cable entre las dos filas es directo:
///
/// | Senal | Pin | CN15 |
/// |---|---|---|
/// | SCK | PE15 | 11 |
/// | MOSI | PG2 | 15 |
/// | MISO | PG1 | 13 |
/// | NSS | PA3 | 17 |
///
/// Los dos canales son `GPDMA1_CH0` (Tx) y `GPDMA1_CH1` (Rx), que son los que el
/// `_generated.rs` implementa para SPI5 (`:10443` y `:10412`). Tienen que ser
/// del GPDMA1: lo exige `CanalGpdma1`, porque la escalada de `soltar_canales`
/// resetea ese controlador.
///
/// El NVIC lo pone `Ranura::nueva` (R21): aqui no se toca.
pub fn maestro_del_banco(
    sck: Peri<'static, peripherals::PE15>,
    mosi: Peri<'static, peripherals::PG2>,
    miso: Peri<'static, peripherals::PG1>,
    nss: Peri<'static, peripherals::PA3>,
    tx: Peri<'static, peripherals::GPDMA1_CH0>,
    rx: Peri<'static, peripherals::GPDMA1_CH1>,
    rcc: &Peri<'_, peripherals::RCC>,
    cfg: Config,
) -> Ranura<'static> {
    Ranura::nueva::<peripherals::SPI5, _, _, _, _, _, _>(
        RANURA_BANCO,
        pac::SPI5,
        sck,
        mosi,
        miso,
        nss,
        tx,
        rx,
        IrqsBanco,
        IrqsBanco,
        rcc,
        cfg,
    )
}

/// Una ranura **de relleno** para medir la CPU con varias a la vez (`carga_j2`,
/// `ranuras-2`): SPI1, la ranura 2 de `SPI_DE_RANURA`, con sus cuatro pines al aire
/// y los canales 4 y 5 del GPDMA1. Cloca de verdad, pero no hay modulo detras: la
/// subida sale mala y no importa, porque lo que se mide es el coste del transporte.
///
/// Los pines son los de las cabeceras morpho de la Nucleo que el N657 puede dar a
/// SPI1 en AF5 (`SckPin`, `MosiPin`, `MisoPin`, `CsPin` del `_generated.rs`) y que
/// UM3417 Rev 3 (Tabla 13, p. 32) saca a un conector sin otra funcion en la placa:
///
/// | Senal | Pin | Conector |
/// |---|---|---|
/// | SCK | PB9 | CN15-16 |
/// | MOSI | PC3 | CN3-25 |
/// | MISO | PB8 | CN15-14 |
/// | NSS | PC5 | CN3-15 |
///
/// Es solo para el banco de carga: no hay nada cableado ahi.
#[allow(clippy::too_many_arguments)]
pub fn maestro_de_relleno_2(
    sck: Peri<'static, peripherals::PB9>,
    mosi: Peri<'static, peripherals::PC3>,
    miso: Peri<'static, peripherals::PB8>,
    nss: Peri<'static, peripherals::PC5>,
    tx: Peri<'static, peripherals::GPDMA1_CH4>,
    rx: Peri<'static, peripherals::GPDMA1_CH5>,
    rcc: &Peri<'_, peripherals::RCC>,
    cfg: Config,
) -> Ranura<'static> {
    Ranura::nueva::<peripherals::SPI1, _, _, _, _, _, _>(
        2,
        pac::SPI1,
        sck,
        mosi,
        miso,
        nss,
        tx,
        rx,
        IrqsBanco,
        IrqsBanco,
        rcc,
        cfg,
    )
}

/// La otra ranura de relleno: SPI2, la ranura 3, con los canales 6 y 7. Igual que
/// [`maestro_de_relleno_2`], con los pines de SPI2 en AF5 que salen a un conector:
///
/// | Senal | Pin | Conector |
/// |---|---|---|
/// | SCK | PF2 | CN2-4 |
/// | MOSI | PD7 | CN15-19 |
/// | MISO | PD6 | CN15-6 |
/// | NSS | PC1 | CN15-5 |
#[allow(clippy::too_many_arguments)]
pub fn maestro_de_relleno_3(
    sck: Peri<'static, peripherals::PF2>,
    mosi: Peri<'static, peripherals::PD7>,
    miso: Peri<'static, peripherals::PD6>,
    nss: Peri<'static, peripherals::PC1>,
    tx: Peri<'static, peripherals::GPDMA1_CH6>,
    rx: Peri<'static, peripherals::GPDMA1_CH7>,
    rcc: &Peri<'_, peripherals::RCC>,
    cfg: Config,
) -> Ranura<'static> {
    Ranura::nueva::<peripherals::SPI2, _, _, _, _, _, _>(
        3,
        pac::SPI2,
        sck,
        mosi,
        miso,
        nss,
        tx,
        rx,
        IrqsBanco,
        IrqsBanco,
        rcc,
        cfg,
    )
}

/// Cuantas ranuras giran en los binarios de medida (`carga_j2`, `perfil_pc`): la
/// del banco y, con `ranuras-2` y `ranuras-3`, las de relleno.
pub const RANURAS_DE_MEDIDA: u32 = if cfg!(feature = "ranuras-3") {
    3
} else if cfg!(feature = "ranuras-2") {
    2
} else {
    1
};

/// El periodo del giro de los binarios de medida. A 800 MHz (`reloj-hub`) es el
/// del instrumento; a 64 MHz uno en que todas las ranuras caben sin llegar
/// tarde, porque un lazo saturado no se parece al del hub (el calendario deja un
/// periodo de hueco tras cada giro tardio y casi nunca duerme al reloj).
pub const PERIODO_DE_MEDIDA_US: u32 = if cfg!(feature = "reloj-hub") {
    PERIODO_GIRO_US
} else if RANURAS_DE_MEDIDA >= 3 {
    2_000
} else {
    1_000
};

/// Las ranuras de los binarios de medida, ya construidas: la del banco y las de
/// relleno que pida [`RANURAS_DE_MEDIDA`], en el arreglo que espera
/// `j2_ejecutor::lanzar_ranuras` (la ranura `n` en el indice `n`).
///
/// Es una macro y no una funcion porque saca los pines y los canales de `$p`, el
/// `Peripherals` del llamador, **campo a campo**: el que llama conserva el resto
/// (`perfil_pc` se queda con `TIM6`).
#[macro_export]
macro_rules! ranuras_de_medida {
    ($p:ident, $cfg:expr) => {{
        let cfg = $cfg;
        let mut ranuras: [Option<$crate::j2_spi::Ranura<'static>>; $crate::j2_spi::RANURAS] =
            [const { None }; $crate::j2_spi::RANURAS];
        ranuras[0] = Some($crate::j2_banco::maestro_del_banco(
            $p.PE15,
            $p.PG2,
            $p.PG1,
            $p.PA3,
            $p.GPDMA1_CH0,
            $p.GPDMA1_CH1,
            &$p.RCC,
            cfg,
        ));
        if $crate::j2_banco::RANURAS_DE_MEDIDA >= 2 {
            ranuras[2] = Some($crate::j2_banco::maestro_de_relleno_2(
                $p.PB9,
                $p.PC3,
                $p.PB8,
                $p.PC5,
                $p.GPDMA1_CH4,
                $p.GPDMA1_CH5,
                &$p.RCC,
                cfg,
            ));
        }
        if $crate::j2_banco::RANURAS_DE_MEDIDA >= 3 {
            ranuras[3] = Some($crate::j2_banco::maestro_de_relleno_3(
                $p.PF2,
                $p.PD7,
                $p.PD6,
                $p.PC1,
                $p.GPDMA1_CH6,
                $p.GPDMA1_CH7,
                &$p.RCC,
                cfg,
            ));
        }
        ranuras
    }};
}

/// El esclavo del banco: SPI4 con los otros cuatro pines del montaje y los
/// canales 2 y 3 del GPDMA1, esperando [`LARGO_BANCO`] bytes por trama.
///
/// Mismo trato que [`maestro_del_banco`]: pines por tipo concreto para que el
/// montaje no se pueda escribir mal. La otra mitad de la tabla de la Tabla 13:
///
/// | Senal | Pin | CN15 |
/// |---|---|---|
/// | SCK | PE2 | 30 |
/// | MOSI | PE14 | 26 |
/// | MISO | PE13 | 28 |
/// | NSS | PE11 | 23 |
///
/// Los canales son `GPDMA1_CH2` (Tx) y `GPDMA1_CH3` (Rx), los que el
/// `_generated.rs` implementa para SPI4 (`:10381` y `:10350`).
///
/// El NVIC -- `EXTI11` con su `enable` y `P1` a las tres lineas -- lo pone
/// `Esclavo::nuevo` (R21).
pub fn esclavo_del_banco(
    sck: Peri<'static, peripherals::PE2>,
    mosi: Peri<'static, peripherals::PE14>,
    miso: Peri<'static, peripherals::PE13>,
    nss: Peri<'static, peripherals::PE11>,
    tx: Peri<'static, peripherals::GPDMA1_CH2>,
    rx: Peri<'static, peripherals::GPDMA1_CH3>,
) -> Esclavo<'static> {
    Esclavo::nuevo::<peripherals::SPI4, _, _, _, _, _, _>(
        pac::SPI4,
        sck,
        mosi,
        miso,
        nss,
        tx,
        rx,
        IrqsBanco,
        LARGO_BANCO,
    )
}

/// El largo clocado del patron del banco, en bytes. Con `largo-41`, `largo-71` o
/// `largo-103` es el de `TONO`, `BAHIA` o el `SET` de dieciseis (los de `LARGOS_MENSAJES`),
/// para medir lo que cuesta el transporte con mensajes mas largos; el esclavo y el patron
/// cambian con el.
///
/// 25 = `VENTANA_SUBIDA + 1`, el minimo que la Voz cloca para muestrear un
/// registro entero (cabecera `2026-09-02-cabecera-j2-design.md`, D6.3: la
/// ventana de la Voz son 24 bytes de registro, y el maestro cloca siempre un
/// byte mas por la cola de la regla 4).
pub const LARGO_BANCO: usize = if cfg!(feature = "largo-103") {
    103
} else if cfg!(feature = "largo-71") {
    71
} else if cfg!(feature = "largo-41") {
    41
} else {
    25
};

/// Lo que el maestro del banco manda, byte a byte: `0x5A ^ i`. Es lo que la feature
/// `verifica-bajada` del esclavo comprueba que le llega.
pub const PATRON_BAJADA: [u8; LARGO_BANCO] = {
    let mut p = [0u8; LARGO_BANCO];
    let mut i = 0;
    while i < LARGO_BANCO {
        p[i] = 0x5A ^ (i as u8);
        i += 1;
    }
    p
};

/// Lo que el esclavo del banco tiene que devolver, byte a byte: `0xA5 ^ i`.
pub const PATRON_SUBIDA: [u8; LARGO_BANCO] = {
    let mut p = [0u8; LARGO_BANCO];
    let mut i = 0;
    while i < LARGO_BANCO {
        p[i] = 0xA5 ^ (i as u8);
        i += 1;
    }
    p
};

// `fw` es `no_std` para thumbv8m y su puerta es el enlace: aqui no hay `cargo
// test`. Estos dos asertos son el test que si cabe -- los evalua el compilador
// y fallan la puerta -- y cazan lo unico que el bucle de arriba puede hacer
// mal: arrancar en el byte equivocado o quedarse corto.
const _: () = assert!(PATRON_BAJADA[0] == 0x5A);
const _: () = assert!(PATRON_SUBIDA[0] == 0xA5);
const _: () = assert!(PATRON_SUBIDA[LARGO_BANCO - 1] == 0xA5 ^ (LARGO_BANCO as u8 - 1));

const TSIZE_BANCO: Tsize = match Tsize::nuevo(LARGO_BANCO as u16) {
    Some(t) => t,
    None => panic!("LARGO_BANCO no puede ser cero (R-MJ1)"),
};

/// La bajada del banco: 25 bytes `0x5A ^ i`, iguales en las seis ranuras.
///
/// Encaja en `j2_ejecutor::Bajada`. Lo unico que tiene que hacer bien es
/// clocar un largo realista y un contenido que el esclavo pueda comprobar; el
/// planificador de verdad arma el sobre de la cabecera (#267).
pub fn bajada_del_banco(_n: usize, buf: &mut [u8; LARGO_MAX]) -> Tsize {
    for (i, b) in buf[..LARGO_BANCO].iter_mut().enumerate() {
        *b = 0x5A ^ (i as u8);
    }
    TSIZE_BANCO
}

/// La bajada que **no compone nada**: el mismo mensaje del banco, rellenado una sola vez.
///
/// Es la mitad de la medida que pide la ficha 1 del acta del 17-10: lo que cuesta el
/// enlace sin lo que cuesta componer la trama (notas, CV, pantalla). El bufer que
/// recibe es el del planificador y sobrevive entre llamadas, asi que el patron se
/// escribe la primera vez y despues basta con devolver el largo.
pub fn bajada_quieta(n: usize, buf: &mut [u8; LARGO_MAX]) -> Tsize {
    if buf[0] != 0x5A {
        bajada_del_banco(n, buf);
    }
    TSIZE_BANCO
}

/// Los marcos numerados de `tic_estres` (feature `secuencia`): la bajada lleva un numero que sube de
/// uno en uno, el esclavo lo devuelve en la subida, y el juez comprueba que la subida llega entera,
/// ni vieja ni del futuro. Con el contenido fijo de `bajada_del_banco`, una trama a medias, una repetida
/// y una buena son el mismo contenido (revision de Halberg del 17-10, hallazgo 2).
#[cfg(feature = "secuencia")]
pub mod secuencia {
    use core::cell::UnsafeCell;
    use core::sync::atomic::{AtomicU32, Ordering};

    use sam17_nucleo_core::maestro_j2::Tsize;
    use sam17_nucleo_core::marcos_j2::{
        escribe, lee, Seguimiento, Veredicto, BASE_BAJADA, BASE_SUBIDA,
    };

    use super::{LARGO_BANCO, TSIZE_BANCO};
    use crate::j2_spi::LARGO_MAX;

    /// La ultima secuencia compuesta.
    pub static COMPUESTAS: AtomicU32 = AtomicU32::new(0);
    pub static SUBIDAS_BUENAS: AtomicU32 = AtomicU32::new(0);
    /// Subidas con la cabeza distinta de la cola, o con un byte del medio que no es el suyo.
    pub static SUBIDAS_ROTAS: AtomicU32 = AtomicU32::new(0);
    /// Subidas con un numero menor que el de una anterior.
    pub static SUBIDAS_ATRASADAS: AtomicU32 = AtomicU32::new(0);
    /// Subidas con un numero que el cerebro todavia no ha compuesto.
    pub static SUBIDAS_FUTURAS: AtomicU32 = AtomicU32::new(0);
    /// Subidas con el mismo numero que la anterior: legitimo si el esclavo no acepto la bajada de en medio.
    pub static SUBIDAS_REPETIDAS: AtomicU32 = AtomicU32::new(0);
    /// Numeros que no se vieron entre dos subidas.
    pub static SUBIDAS_SALTOS: AtomicU32 = AtomicU32::new(0);

    struct Seg(UnsafeCell<Seguimiento>);
    // SAFETY: solo lo toca el juez, y al juez lo llama el planificador (un solo nivel).
    unsafe impl Sync for Seg {}
    static SEG: Seg = Seg(UnsafeCell::new(Seguimiento::nuevo()));

    /// Encaja en `j2_ejecutor::Bajada`.
    pub fn bajada(_n: usize, buf: &mut [u8; LARGO_MAX]) -> Tsize {
        let v = COMPUESTAS.fetch_add(1, Ordering::Relaxed) + 1;
        escribe(&mut buf[..LARGO_BANCO], BASE_BAJADA, v);
        TSIZE_BANCO
    }

    /// Encaja en `j2_ejecutor::Juez`. Rechaza la subida rota, la atrasada y la futura.
    pub fn juez(_n: usize, subida: &[u8]) -> bool {
        let Some(eco) = lee(subida, BASE_SUBIDA) else {
            SUBIDAS_ROTAS.fetch_add(1, Ordering::Relaxed);
            return false;
        };
        if eco > COMPUESTAS.load(Ordering::Relaxed) {
            SUBIDAS_FUTURAS.fetch_add(1, Ordering::Relaxed);
            return false;
        }
        // SAFETY: ver `Seg`.
        match unsafe { &mut *SEG.0.get() }.ve(eco) {
            Veredicto::Nuevo { saltos } => {
                SUBIDAS_BUENAS.fetch_add(1, Ordering::Relaxed);
                SUBIDAS_SALTOS.fetch_add(saltos, Ordering::Relaxed);
                true
            }
            Veredicto::Repetido => {
                SUBIDAS_REPETIDAS.fetch_add(1, Ordering::Relaxed);
                true
            }
            Veredicto::Atrasado => {
                SUBIDAS_ATRASADAS.fetch_add(1, Ordering::Relaxed);
                false
            }
        }
    }
}

/// Una tabla de contenidos de prueba (feature `tabla`): la bajada recorre los 16, de uno en uno, y el
/// esclavo comprueba cada trama recibida contra el mismo contenido (el primer byte lleva el numero).
#[cfg(feature = "tabla")]
pub mod tabla {
    use core::sync::atomic::{AtomicU32, Ordering};

    use sam17_nucleo_core::maestro_j2::Tsize;

    use super::{LARGO_BANCO, TSIZE_BANCO};
    use crate::j2_spi::LARGO_MAX;

    pub const N: usize = 16;
    pub static COMPUESTAS: AtomicU32 = AtomicU32::new(0);

    /// El contenido numero `id`. El byte 0 es siempre `id`.
    pub fn marco(id: u8, out: &mut [u8]) {
        let n = out.len();
        let mut x: u32 = 0x1234_5678;
        for (i, b) in out.iter_mut().enumerate() {
            *b = match id {
                0 => 0x00,
                1 => 0xFF,
                2 => 0xAA,
                3 => 0x55,
                4 => 0x5A ^ (i as u8),
                5 => i as u8,
                6 => 0x96,
                7 => {
                    // el contenido del marco numero 1 de `core::marcos_j2`
                    0
                }
                8 => {
                    if i % 2 == 0 {
                        0x00
                    } else {
                        0xFF
                    }
                }
                9 => 0x80,
                10 => 0x01,
                11 => {
                    x ^= x << 13;
                    x ^= x >> 17;
                    x ^= x << 5;
                    (x >> 8) as u8
                }
                12 => {
                    if i == 12 {
                        0x5A
                    } else {
                        0x00
                    }
                }
                13 => {
                    if i == 4 {
                        0x5A
                    } else {
                        0x00
                    }
                }
                14 => 0xA5 ^ (i as u8),
                _ => (i as u8).wrapping_mul(37),
            };
        }
        if id == 7 {
            sam17_nucleo_core::marcos_j2::escribe(out, 0x5A, 1);
        }
        out[0] = id;
        let _ = n;
    }

    /// Encaja en `j2_ejecutor::Bajada`.
    pub fn bajada(_n: usize, buf: &mut [u8; LARGO_MAX]) -> Tsize {
        let id = (COMPUESTAS.fetch_add(1, Ordering::Relaxed) % N as u32) as u8;
        marco(id, &mut buf[..LARGO_BANCO]);
        TSIZE_BANCO
    }
}

/// Los largos **clocados** de los mensajes de la cabecera, en bytes, con su
/// nombre. Es `TSIZE` (D1): **sobre de 6 bytes, CRC dentro**, mas la carga, mas
/// el byte de cola de D6.4, con el relleno a la ventana donde toca. O sea
/// `carga + 7`, que es lo que da la tabla de la cabecera. (El CRC **no** se suma
/// aparte: sec.4 dice *«Sobre de 6 bytes en todo»* y ese «en todo» lo incluye.)
///
/// Fuente, numero a numero: `docs/superpowers/specs/`
/// `2026-09-02-cabecera-j2-design.md`, sec.4 *«Los largos contra R-E1»*, la
/// tabla de `:718-727` (columna *«clocados (bytes)»*). Las tres filas con
/// relleno son las que la tabla escribe con flecha -- `TONO` nada cambio
/// `9 → 25`, `COMPUERTA` `11 → 25` y `NADA` `7 → 25` --, y el numero que entra
/// aqui es el de la derecha, que es el que se cloca.
///
/// La usa `src/bin/plazos_j2.rs`: un pulso de GPIO por mensaje contra el
/// osciloscopio, para sellar `FACTOR_PLAZO` y `T_SUELO_PLAZO` (spec del maestro
/// sec.9, riesgo 2).
///
/// **La otra fuente es `hardware/02-midi-cv/trama_j2_budget.py`, y hoy no dice
/// lo mismo.** Ese guion declara el trafico en **bits de carga por flujo**, sin
/// sobre ni cola: `BITS_BLOQUE_TONO = 288` (`:104`),
/// `BITS_ESTADO_COMPUERTA = 16` (`:105`), `BITS_EVENTO = 16+2+16+16` (`:106`) y
/// `BITS_CROSSPOINT = 256` (`:110`). La cabecera ya mando la enmienda que los
/// junta -- su mapa de enmiendas, `:956`: 288 → **328**, 16 → **200**,
/// 50 → **112**, 256 → **568** -- y esta **pendiente**. Mientras no se aplique,
/// esta tabla y el guion son **dos cuentas de lo mismo**; esta copia la del
/// papel, que es el que manda. El dia que el guion se enmiende, deberian ser
/// una sola: el guion las exporta y esto las lee.
pub const LARGOS_MENSAJES: [(&str, u16); 8] = [
    ("HOLA", 9),
    ("EVENTO", 14),
    ("TONO_nada_cambio", 25),
    ("TONO_dieciseis", 41),
    ("COMPUERTA", 25),
    ("BAHIA", 71),
    ("SET_dieciseis", 103),
    ("NADA", 25),
];

// El mismo test que los dos de arriba -- lo evalua el compilador y falla la
// puerta -- contra lo unico que esta tabla puede tener mal y no se veria hasta
// la placa: un largo de cero (R-MJ1, y `Tsize::nuevo` devolveria `None`) o uno
// que no cabe en los buferes del driver (`giro` aseveraria en la placa).
const _: () = {
    let mut i = 0;
    while i < LARGOS_MENSAJES.len() {
        let (_, largo) = LARGOS_MENSAJES[i];
        assert!(largo > 0, "R-MJ1: ningun mensaje se cloca con TSIZE = 0");
        assert!(
            largo as usize <= LARGO_MAX,
            "un mensaje no cabe en LARGO_MAX"
        );
        i += 1;
    }
};

/// El juez del banco: la subida vale si es exactamente [`PATRON_SUBIDA`].
///
/// Encaja en `j2_ejecutor::Juez`. Rechaza entero, como D8 del maestro: un solo
/// byte fuera de sitio es `SubidaMala`, y 40 seguidas ponen `muda` (D7.3).
pub fn juez_del_banco(_n: usize, subida: &[u8]) -> bool {
    subida == PATRON_JUEZ
}

/// El patron donde lo lee el juez: con `j2-tcm`, en la DTCM, como los statics del J2 (ficha H).
/// Como `const` se quedaba en el `.rodata` de la AXISRAM2.
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static PATRON_JUEZ: [u8; LARGO_BANCO] = PATRON_SUBIDA;

/// Los jueces con el CRC del sobre de la subida (cabecera del J2, D1: CRC-16/CCITT-FALSE de
/// todo menos los dos ultimos bytes, que lo llevan en little-endian), para medir en `carga_j2`
/// lo que cuesta: por bits (`descubrimiento::crc16`, el que reutiliza `core`), por tabla y con
/// la unidad CRC. El patron del banco no lleva un CRC valido, asi que el veredicto sigue siendo
/// el de [`juez_del_banco`]: el CRC se calcula y se compara igual, y la politica recorre el
/// mismo camino que sin el.
fn crc_del_sobre(subida: &[u8], crc: impl FnOnce(&[u8]) -> u16) {
    let (cuerpo, cola) = subida.split_at(subida.len().saturating_sub(2));
    let ok = cola.len() == 2 && crc(cuerpo) == u16::from_le_bytes([cola[0], cola[1]]);
    core::hint::black_box(ok);
}

pub fn juez_crc_bits(n: usize, subida: &[u8]) -> bool {
    crc_del_sobre(subida, sam17_nucleo_core::descubrimiento::crc16);
    juez_del_banco(n, subida)
}

/// La tabla del CRC donde la lee el planificador: con `j2-tcm`, en la DTCM (512 B).
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static TABLA_CRC: [u16; 256] = sam17_nucleo_core::descubrimiento::TABLA_CRC16;

pub fn juez_crc_tabla(n: usize, subida: &[u8]) -> bool {
    crc_del_sobre(subida, |d| {
        sam17_nucleo_core::descubrimiento::crc16_con(&TABLA_CRC, d)
    });
    juez_del_banco(n, subida)
}

pub fn juez_crc_unidad(n: usize, subida: &[u8]) -> bool {
    crc_del_sobre(subida, crc_unidad);
    juez_del_banco(n, subida)
}

/// El juez de verdad (cabecera del J2, D2 y D8): la subida vale si su sobre lo dice, con el CRC
/// por la tabla de la DTCM (ficha I). El ultimo byte clocado es la cola de D6.4 y no entra, asi
/// que el registro tiene que caber en lo de antes: es el `largo + 7` que el cerebro exige para
/// leerlo (D6.2).
pub fn juez_sobre(_n: usize, subida: &[u8]) -> bool {
    j2::decodificar(&TABLA_CRC, &subida[..subida.len().saturating_sub(1)]).is_ok()
}

/// La ventana de subida de la Voz, sobre incluido (cabecera, D6.3).
const VENTANA_VOZ: usize = 24;

/// Lo que publicaria el modulo en `carga_j2`, donde no hay modulo: un registro que llena la
/// ventana de la Voz, y despues relleno. El tipo es `JACKS` (`0x90`), cuya carga es de otro
/// papel; aqui son 18 bytes de prueba. Vive en la DTCM, como `local_subida`, donde el
/// planificador copia cada subida antes de pasarsela al juez.
struct Registro(UnsafeCell<[u8; LARGO_BANCO]>);
// SAFETY: lo escribe `prepara_registro_banco` antes de `lanzar`; despues solo se lee.
unsafe impl Sync for Registro {}
#[cfg_attr(feature = "j2-tcm", link_section = ".dtcm")]
static REGISTRO_BANCO: Registro = Registro(UnsafeCell::new([0; LARGO_BANCO]));

/// Escribe [`REGISTRO_BANCO`] con `j2::codificar` y comprueba que [`juez_sobre`] lo acepta.
pub fn prepara_registro_banco() {
    let carga: [u8; VENTANA_VOZ - j2::SOBRE] = core::array::from_fn(|i| i as u8);
    // SAFETY: ver `Registro`.
    let r = unsafe { &mut *REGISTRO_BANCO.0.get() };
    assert_eq!(
        j2::codificar(&TABLA_CRC, 0x90, 1, &carga, r),
        Some(VENTANA_VOZ)
    );
    assert!(juez_sobre(RANURA_BANCO, r));
}

/// [`juez_sobre`] sobre [`REGISTRO_BANCO`], con el largo clocado, en vez de sobre lo que trajo el
/// cable: sin modulo, el ruido del `MISO` se rechaza en los dos primeros bytes, sin llegar al CRC,
/// y la medida saldria corta.
pub fn juez_sobre_sin_modulo(n: usize, subida: &[u8]) -> bool {
    // SAFETY: ver `Registro`.
    let r = unsafe { &*REGISTRO_BANCO.0.get() };
    r.get(..subida.len()).is_some_and(|r| juez_sobre(n, r))
}

/// Enciende la unidad CRC con el CRC-16/CCITT-FALSE (polinomio de 16 bits `0x1021`, inicial
/// `0xFFFF`, sin reflejar) y comprueba que da lo mismo que `descubrimiento::crc16` con el vector
/// canonico (`"123456789"` -> `0x29B1`) y con todos los largos hasta 71 de un contenido
/// pseudoaleatorio. Si no, el CRC del sobre no puede ir en la unidad (cabecera, §10, riesgo 5).
pub fn prepara_crc_unidad() {
    use embassy_stm32::pac::crc::vals;
    embassy_stm32::rcc::enable_and_reset::<peripherals::CRC>();
    pac::CRC.pol().write_value(0x1021);
    pac::CRC.init().write_value(0xFFFF);
    pac::CRC.cr().write(|w| {
        w.set_polysize(vals::Polysize::Polysize16);
        w.set_rev_in(vals::RevIn::Normal);
        w.set_rev_out(vals::RevOut::Normal);
    });
    assert_eq!(crc_unidad(b"123456789"), 0x29B1);
    let mut datos = [0u8; 71];
    let mut x: u32 = 1;
    for b in datos.iter_mut() {
        x = x.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        *b = (x >> 24) as u8;
    }
    for largo in 0..=datos.len() {
        assert_eq!(
            crc_unidad(&datos[..largo]),
            sam17_nucleo_core::descubrimiento::crc16(&datos[..largo])
        );
    }
}

/// El CRC con la unidad. La unidad mete primero el bit mas alto de lo que se le escribe y el
/// sobre va byte a byte desde el primero, asi que cada palabra va con sus bytes dados la vuelta
/// (`REV`); la cola, por media palabra y por byte.
pub fn crc_unidad(datos: &[u8]) -> u16 {
    let crc = pac::CRC;
    crc.cr().modify(|w| w.set_reset(true));
    let mut palabras = datos.chunks_exact(4);
    for p in &mut palabras {
        crc.dr32()
            .write_value(u32::from_be_bytes([p[0], p[1], p[2], p[3]]));
    }
    let resto = palabras.remainder();
    let mut i = 0;
    if resto.len() >= 2 {
        crc.dr16()
            .write_value(u16::from_be_bytes([resto[0], resto[1]]));
        i = 2;
    }
    if resto.len() > i {
        crc.dr8().write_value(resto[i]);
    }
    crc.dr32().read() as u16
}
