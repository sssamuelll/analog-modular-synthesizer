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

/// Los largos **clocados** de los mensajes de la cabecera, en bytes, con su
/// nombre. Es `TSIZE` (D1): sobre de 6 bytes + carga + CRC + el byte de cola de
/// D6.4, con el relleno a la ventana donde toca.
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
