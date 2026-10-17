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
//! valida (`2026-09-02-cabecera-j2-design.md`, D6.1); mientras esa cabecera no
//! este en codigo (#267) el banco necesita algo que distinga *"el modulo
//! contesto bien"* de *"el modulo devolvio basura"*, y esto es lo mas simple
//! que lo hace. **Lo retira #267**, y con el se va este archivo entero.
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

use embassy_stm32::{dma, pac, peripherals, Peri};
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
    subida == PATRON_SUBIDA
}
