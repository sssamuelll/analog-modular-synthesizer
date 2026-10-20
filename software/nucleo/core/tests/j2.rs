//! El sobre del J2, contra el papel de la cabecera.
//!
//! Papel: `docs/superpowers/specs/2026-09-02-cabecera-j2-design.md`, D2 (el
//! sobre de seis bytes), D8 (el receptor rechaza entero) y D9 con su enmienda
//! del 2026-10-19 (el CRC va con la tabla que pase quien llama). Los numeros de
//! los tests son los de su §8.
//!
//! Los bytes esperados se escriben a mano desde D2, y el CRC con
//! `descubrimiento::crc16`, el de bits: un test que llame a la misma cuenta que
//! prueba no prueba nada.

use sam17_nucleo_core::descubrimiento::{crc16, TABLA_CRC16};
use sam17_nucleo_core::j2::{codificar, decodificar, Cabecera, ErrorTrama, SOBRE};

fn trama(tipo: u8, secuencia: u16, carga: &[u8]) -> Vec<u8> {
    let mut out = vec![0u8; SOBRE + carga.len()];
    let n = codificar(&TABLA_CRC16, tipo, secuencia, carga, &mut out).expect("cabe");
    assert_eq!(n, out.len());
    out
}

/// Tramas de borde: sin carga, la carga mas larga que cabe en `largo`, todo
/// cero, todo `0xFF`, y las secuencias de los dos extremos.
fn casos() -> Vec<(u8, u16, Vec<u8>)> {
    vec![
        (0x00, 0, vec![]),
        (0x01, 0, vec![1, 0]),
        (0x10, 77, vec![0x05, 0x00, 0x01, 0xFF, 0x7F, 0x00, 0x40]),
        (0x13, 0xFFFF, vec![0x00; 64]),
        (0x14, 0x8000, vec![0xFF; 96]),
        (0x90, 1, (0..18u8).collect()),
        (0xFF, 0x1234, vec![0xFF; 255]),
    ]
}

/// §8.2: un `EVENTO` conocido son exactamente estos 13 bytes, en este orden,
/// little-endian, con el CRC de `crc16` sobre los once primeros.
#[test]
fn el_sobre_byte_a_byte() {
    // destino 0x1234, borde 1 (cierra), fuerza 0x5678, tono 0x9ABC (§3.2).
    let carga = [0x34, 0x12, 0x01, 0x78, 0x56, 0xBC, 0x9A];
    let t = trama(0x10, 0x0102, &carga);
    let crc = crc16(&[
        0x10, 7, 0x02, 0x01, 0x34, 0x12, 0x01, 0x78, 0x56, 0xBC, 0x9A,
    ]);
    assert_eq!(
        t,
        [
            0x10,
            7,
            0x02,
            0x01,
            0x34,
            0x12,
            0x01,
            0x78,
            0x56,
            0xBC,
            0x9A,
            crc as u8,
            (crc >> 8) as u8
        ]
    );
}

/// §8.1, del lado del sobre: lo que se codifica se decodifica igual.
#[test]
fn ida_y_vuelta() {
    for (tipo, secuencia, carga) in casos() {
        let t = trama(tipo, secuencia, &carga);
        let (cab, c) = decodificar(&TABLA_CRC16, &t).expect("trama buena");
        assert_eq!(
            cab,
            Cabecera {
                tipo,
                largo: carga.len() as u8,
                secuencia
            }
        );
        assert_eq!(c, &carga[..]);
    }
}

/// §8.3, R-C2: ningun bit volteado de ninguna trama da un mensaje. En la
/// cabecera, la carga y el CRC sale `Crc`; en el byte de `largo` puede salir
/// `Corta`, porque un `largo` mayor que la trama la deja corta antes de que
/// haya CRC que mirar. Los dos son rechazo entero (D8).
#[test]
fn ningun_bit_volteado_da_un_mensaje() {
    for (tipo, secuencia, carga) in casos() {
        let t = trama(tipo, secuencia, &carga);
        for i in 0..t.len() {
            for bit in 0..8 {
                let mut m = t.clone();
                m[i] ^= 1 << bit;
                match decodificar(&TABLA_CRC16, &m) {
                    Err(ErrorTrama::Crc) => {}
                    Err(ErrorTrama::Corta) if i == 1 => {}
                    otro => panic!("tipo {tipo:#04x}, byte {i}, bit {bit}: {otro:?}"),
                }
            }
        }
    }
}

/// §8.4, R-C1: con un byte menos la trama es corta, y cualquier prefijo
/// tambien; lo que sobra detras del CRC (relleno y cola, D6) no se mira.
#[test]
fn trama_corta_y_lo_que_sobra() {
    for (tipo, secuencia, carga) in casos() {
        let t = trama(tipo, secuencia, &carga);
        for largo in 0..t.len() {
            assert_eq!(
                decodificar(&TABLA_CRC16, &t[..largo]),
                Err(ErrorTrama::Corta),
                "tipo {tipo:#04x} con {largo} de {} bytes",
                t.len()
            );
        }
        for relleno in 1..=33 {
            for b in [0x00, 0xA5] {
                let mut m = t.clone();
                m.resize(t.len() + relleno, b);
                let (cab, c) = decodificar(&TABLA_CRC16, &m).expect("relleno y cola no cuentan");
                assert_eq!((cab.tipo, cab.secuencia), (tipo, secuencia));
                assert_eq!(c, &carga[..]);
            }
        }
    }
}

/// D9 con la enmienda del 19-10 (ficha I): el CRC es el de la tabla que pasa
/// quien llama. Una copia de `TABLA_CRC16` da lo mismo; una tabla de ceros no
/// reconoce una trama buena.
#[test]
fn el_crc_va_con_la_tabla_de_quien_llama() {
    let copia: [u16; 256] = TABLA_CRC16;
    let ceros = [0u16; 256];
    for (tipo, secuencia, carga) in casos() {
        let t = trama(tipo, secuencia, &carga);
        assert!(decodificar(&copia, &t).is_ok());
        assert_eq!(decodificar(&ceros, &t), Err(ErrorTrama::Crc));
    }
}

/// §8.12, R-C3: la secuencia no rechaza. Un salto de 7 a 12 decodifica las dos.
#[test]
fn la_secuencia_no_rechaza() {
    for s in [7, 12] {
        let t = trama(0x11, s, &[0x01, 0x00, 0x00, 0x40]);
        assert_eq!(decodificar(&TABLA_CRC16, &t).unwrap().0.secuencia, s);
    }
}

/// `largo` es un byte: una carga de 256 no tiene sobre, y un bufer pequeno no
/// recibe media trama.
#[test]
fn codificar_no_escribe_lo_que_no_cabe() {
    let mut out = [0u8; 300];
    assert_eq!(codificar(&TABLA_CRC16, 0x14, 0, &[0; 256], &mut out), None);
    let mut corto = [0u8; SOBRE + 6];
    assert_eq!(codificar(&TABLA_CRC16, 0x14, 0, &[0; 7], &mut corto), None);
    assert_eq!(corto, [0u8; SOBRE + 6]);
}

/// §8.15, R-C6: el sobre esta congelado. Cambiarlo es editar este test a mano.
#[test]
fn el_sobre_son_seis_bytes() {
    assert_eq!(SOBRE, 6);
}
