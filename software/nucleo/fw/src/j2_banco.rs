//! El planificador de mentira del banco: 25 bytes que bajan y 25 que tienen
//! que subir.
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

use sam17_nucleo_core::maestro_j2::Tsize;

use crate::j2_spi::LARGO_MAX;

/// El largo clocado del patron del banco, en bytes.
///
/// 25 = `VENTANA_SUBIDA + 1`, el minimo que la Voz cloca para muestrear un
/// registro entero (cabecera `2026-09-02-cabecera-j2-design.md`, D6.3: la
/// ventana de la Voz son 24 bytes de registro, y el maestro cloca siempre un
/// byte mas por la cola de la regla 4).
pub const LARGO_BANCO: usize = 25;

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
const _: () = assert!(PATRON_SUBIDA[0] == 0xA5);
const _: () = assert!(PATRON_SUBIDA[LARGO_BANCO - 1] == 0xA5 ^ 24);

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

/// El juez del banco: la subida vale si es exactamente [`PATRON_SUBIDA`].
///
/// Encaja en `j2_ejecutor::Juez`. Rechaza entero, como D8 del maestro: un solo
/// byte fuera de sitio es `SubidaMala`, y 40 seguidas ponen `muda` (D7.3).
pub fn juez_del_banco(_n: usize, subida: &[u8]) -> bool {
    subida == PATRON_SUBIDA
}
