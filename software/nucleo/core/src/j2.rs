//! El mazo digital J2: el sobre de la cabecera y, debajo, el dialecto legado
//! del modulo 3 v1.
//!
//! # El sobre
//!
//! Papel: `docs/superpowers/specs/2026-09-02-cabecera-j2-design.md`, D2 y D9.
//! El contrato del enlace es este: toda trama de bajada y todo registro de
//! subida llevan seis bytes de sobre.
//!
//! ```text
//!  byte 0      tipo       u8      bit alto puesto: sube
//!  byte 1      largo      u8      bytes de carga
//!  bytes 2-3   secuencia  u16 LE
//!  bytes 4..   carga      largo bytes
//!  2 bytes     crc16      u16 LE  CRC-16/CCITT-FALSE de los 4 + largo primeros
//!  [relleno y byte de cola: el CRC no los cubre y el receptor no los mira]
//! ```
//!
//! El CRC es el de `descubrimiento`, con la tabla que pase quien llama
//! (enmienda del 2026-10-19 a D2 y D9, ficha I): en el cerebro, una copia en la
//! DTCM. Los mensajes de cada dialecto, sus tipos y la forma de su carga no
//! viven aqui.
//!
//! # El dialecto legado del modulo 3 v1
//!
//! Sin sobre (D9). El contrato del modulo 3 v1 (`hardware/03-vco/README.md`):
//! 72 bits, `CS` abajo durante los 72 relojes, SPI modo 1, <=10 MHz, orden de
//! transmision `[U7][U6][U5]`.
//!
//! # De donde salen los numeros del AD5686R
//!
//! - **24 bits = 4 de comando + 4 de direccion + 16 de dato.** Confirmado en
//!   el propio repo: el docstring de `software/midi-cv/sam17/hardware/dac.py`
//!   lo escribe bit a bit (`DB23..DB20` comando, `DB19..DB16` direccion,
//!   `DB15..DB0` dato), y coincide con la descripcion del datasheet.
//! - **Direccion one-hot.** Confirmado por las constantes de
//!   `software/midi-cv/sam17/settings.py`, que llevan la placa real:
//!   `0x11`->A, `0x12`->B, `0x14`->C, `0x18`->D, o sea `0001/0010/0100/1000`.
//! - **Comando `0011` = «write to and update DAC channel n»**: el comando que
//!   escribe el registro Y mueve la salida sin depender de `LDAC`.
//!
//! # Lo que sigue SIN verificar contra el PDF primario
//!
//! El datasheet de Analog Devices no se pudo abrir desde aqui (tres intentos,
//! todos con timeout). Falta contrastar la tabla de comandos entera contra el
//! PDF antes del bring-up — issue abierto para eso.
//!
//! Y hay una contradiccion viva en el firmware moribundo del modulo 2 que
//! conviene no heredar: su `DacChannelMap` dice en el docstring «write-and-update
//! command (0011 nnnn)» pero sus constantes valen `0x11`, o sea comando `0001`
//! («write to input register n»), que solo mueve la salida si `LDAC` esta
//! cableado abajo. Aqui se usa `0011` a proposito.

use crate::descubrimiento::crc16_con;

/// Bytes de sobre: cuatro delante (tipo, largo, secuencia) y el CRC detras (D2).
pub const SOBRE: usize = 6;

/// Lo que dice el sobre de una trama o de un registro (D2).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Cabecera {
    pub tipo: u8,
    pub largo: u8,
    pub secuencia: u16,
}

/// Por que se rechaza una trama entera (D8). Las dos primeras las ve el sobre;
/// las otras dos, el dialecto.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorTrama {
    /// Menos bytes que `largo + 6` (causa 1, R-C1).
    Corta,
    /// El CRC no cuadra (causa 2, R-C2).
    Crc,
    /// El tipo no es del dialecto ni universal (causa 3).
    Tipo,
    /// La carga no tiene la forma del tipo (causa 4).
    Forma,
}

/// El techo de carga que R-E1 deja a un reloj del enlace (§4): los bytes que
/// caben en 100 us, menos el sobre y el byte de cola, y el `largo` de un byte
/// recorta a 255.
pub const fn carga_max(reloj_hz: u32) -> usize {
    let bytes = (reloj_hz / 80_000) as usize;
    let carga = bytes.saturating_sub(SOBRE + 1);
    if carga > 255 {
        255
    } else {
        carga
    }
}

/// Escribe el sobre con `carga` en `out` y devuelve cuantos bytes ocupa,
/// `SOBRE + carga.len()`. `None`, sin tocar `out`, si la carga no cabe en
/// `largo` o la trama no cabe en `out`.
pub fn codificar(
    tabla: &[u16; 256],
    tipo: u8,
    secuencia: u16,
    carga: &[u8],
    out: &mut [u8],
) -> Option<usize> {
    let largo = u8::try_from(carga.len()).ok()?;
    let n = 4 + carga.len();
    let out = out.get_mut(..n + 2)?;
    out[0] = tipo;
    out[1] = largo;
    out[2..4].copy_from_slice(&secuencia.to_le_bytes());
    out[4..n].copy_from_slice(carga);
    let crc = crc16_con(tabla, &out[..n]);
    out[n..].copy_from_slice(&crc.to_le_bytes());
    Some(n + 2)
}

/// Lee el sobre de `trama` y devuelve la cabecera y la carga. Lo que sigue al
/// CRC no se mira (R-C1) y la secuencia no rechaza (R-C3).
pub fn decodificar<'a>(
    tabla: &[u16; 256],
    trama: &'a [u8],
) -> Result<(Cabecera, &'a [u8]), ErrorTrama> {
    let largo = *trama.get(1).ok_or(ErrorTrama::Corta)?;
    let n = 4 + usize::from(largo);
    let (Some(cuerpo), Some(crc)) = (trama.get(..n), trama.get(n..n + 2)) else {
        return Err(ErrorTrama::Corta);
    };
    if crc16_con(tabla, cuerpo) != u16::from_le_bytes([crc[0], crc[1]]) {
        return Err(ErrorTrama::Crc);
    }
    let cab = Cabecera {
        tipo: cuerpo[0],
        largo,
        secuencia: u16::from_le_bytes([cuerpo[2], cuerpo[3]]),
    };
    Ok((cab, &cuerpo[4..]))
}

/// «Write to and update DAC channel n».
pub const CMD_ESCRIBIR_Y_ACTUALIZAR: u8 = 0b0011;

/// Cuantos DAC hay en la cadena del modulo 3.
pub const N_DACS: usize = 3;
/// 3 chips x 24 bits.
pub const BITS_TRAMA: usize = N_DACS * 24;
pub const BYTES_TRAMA: usize = BITS_TRAMA / 8;

/// Direccion one-hot del AD5686R.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum Canal {
    A = 0b0001,
    B = 0b0010,
    C = 0b0100,
    D = 0b1000,
}

impl Canal {
    /// El canal `i`-esimo, 0..=3. Fuera de rango cae en `A`, que es el unico
    /// valor seguro: escribir un canal equivocado es peor que repetir el primero.
    pub const fn de_indice(i: usize) -> Canal {
        match i {
            0 => Canal::A,
            1 => Canal::B,
            2 => Canal::C,
            _ => Canal::D,
        }
    }
}

/// Los cuatro CV de mezcla, compartidos por las cuatro voces (§7 de
/// `architecture-poly.md`: los mandos se comparten, los circuitos se replican).
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub struct Mezcla {
    pub sierra: u16,
    pub triangular: u16,
    pub pulso: u16,
    pub seno: u16,
}

/// Una palabra de 24 bits del AD5686R.
pub const fn palabra(cmd: u8, canal: Canal, dato: u16) -> u32 {
    (((cmd & 0xF) as u32) << 20) | ((canal as u32) << 16) | dato as u32
}

/// Los 72 bits, en el orden en que salen por `MOSI`.
///
/// El primer word que sale acaba en U7 y el ultimo se queda en U5.
pub const fn trama(u7: u32, u6: u32, u5: u32) -> [u8; BYTES_TRAMA] {
    [
        (u7 >> 16) as u8,
        (u7 >> 8) as u8,
        u7 as u8,
        (u6 >> 16) as u8,
        (u6 >> 8) as u8,
        u6 as u8,
        (u5 >> 16) as u8,
        (u5 >> 8) as u8,
        u5 as u8,
    ]
}

/// Refrescar la placa del modulo 3 entera.
///
/// **Una trama lleva UNA palabra por chip**, y una palabra escribe UN canal.
/// Asi que son cuatro tramas, y encajan exactas: la trama `i` escribe el canal
/// `i` de los tres chips a la vez.
///
/// | Trama | U7 | U6 | U5 |
/// |---|---|---|---|
/// | 0 | A — mezcla de seno | A — PWM compartido | A — tono voz 1 |
/// | 1 | B — reserva | B — mezcla sierra | B — tono voz 2 |
/// | 2 | C — reserva | C — mezcla triangular | C — tono voz 3 |
/// | 3 | D — reserva | D — mezcla pulso | D — tono voz 4 |
///
/// El `4` de esta funcion es un hecho del **tipo de placa** —el modulo 3 tiene
/// cuatro voces y doce canales de DAC—, no del instrumento. El conteo de voces
/// del instrumento sale del descubrimiento y no aparece por aqui.
pub fn tramas_vco4(tono: &[u16; 4], pwm: u16, mezcla: Mezcla) -> [[u8; BYTES_TRAMA]; 4] {
    // U7: A = mezcla de seno, B/C/D de reserva.
    let u7 = [mezcla.seno, 0, 0, 0];
    // U6: A = PWM (compartido), B/C/D = sierra / triangular / pulso.
    let u6 = [pwm, mezcla.sierra, mezcla.triangular, mezcla.pulso];
    // U5: A-D = tono de las voces 1-4.
    let mut salida = [[0u8; BYTES_TRAMA]; 4];
    for (i, t) in salida.iter_mut().enumerate() {
        let c = Canal::de_indice(i);
        *t = trama(
            palabra(CMD_ESCRIBIR_Y_ACTUALIZAR, c, u7[i]),
            palabra(CMD_ESCRIBIR_Y_ACTUALIZAR, c, u6[i]),
            palabra(CMD_ESCRIBIR_Y_ACTUALIZAR, c, tono[i]),
        );
    }
    salida
}

#[cfg(test)]
mod tests {
    use super::*;

    fn word(t: &[u8; BYTES_TRAMA], chip: usize) -> u32 {
        u32::from_be_bytes([0, t[chip * 3], t[chip * 3 + 1], t[chip * 3 + 2]])
    }
    const U7: usize = 0;
    const U6: usize = 1;
    const U5: usize = 2;

    #[test]
    fn la_trama_son_nueve_bytes_en_el_orden_congelado() {
        // hardware/03-vco/README.md: 72 bits = 3 chips x 24, orden [U7][U6][U5].
        let t = trama(0x311111, 0x322222, 0x333333);
        assert_eq!(t.len(), 9);
        assert_eq!(BITS_TRAMA, 72);
        assert_eq!(
            word(&t, U7) & 0xFFFF,
            0x1111,
            "el primer word que sale acaba en U7"
        );
        assert_eq!(word(&t, U5) & 0xFFFF, 0x3333, "el ultimo se queda en U5");
    }

    #[test]
    fn cada_palabra_lleva_comando_y_canal_donde_toca() {
        let p = palabra(CMD_ESCRIBIR_Y_ACTUALIZAR, Canal::C, 0xBEEF);
        assert_eq!(p >> 20, CMD_ESCRIBIR_Y_ACTUALIZAR as u32);
        assert_eq!((p >> 16) & 0xF, Canal::C as u32);
        assert_eq!(p & 0xFFFF, 0xBEEF);
        assert_eq!(p >> 24, 0, "una palabra son 24 bits, no mas");
    }

    #[test]
    fn los_canales_son_one_hot_y_distintos() {
        let cs = [
            Canal::A as u32,
            Canal::B as u32,
            Canal::C as u32,
            Canal::D as u32,
        ];
        for c in cs {
            assert_eq!(c.count_ones(), 1, "direccionamiento one-hot del AD5686R");
        }
        assert_eq!(cs.iter().fold(0, |a, b| a | b).count_ones(), 4);
    }

    #[test]
    fn el_tono_de_cada_voz_cae_en_su_canal_de_u5() {
        let tono = [0xAAAAu16, 0xBBBB, 0xCCCC, 0xDDDD];
        let ts = tramas_vco4(&tono, 0x1234, Mezcla::default());
        assert_eq!(ts.len(), 4, "cuatro canales son cuatro tramas");
        for (i, t) in ts.iter().enumerate() {
            let u5 = word(t, U5);
            assert_eq!(
                u5 & 0xFFFF,
                tono[i] as u32,
                "trama {i}: tono de la voz {}",
                i + 1
            );
            assert_eq!(
                (u5 >> 16) & 0xF,
                Canal::de_indice(i) as u32,
                "trama {i}: canal"
            );
        }
    }

    #[test]
    fn el_pwm_compartido_va_en_el_canal_a_de_u6() {
        let ts = tramas_vco4(&[0; 4], 0x1234, Mezcla::default());
        let u6 = word(&ts[0], U6);
        assert_eq!(u6 & 0xFFFF, 0x1234);
        assert_eq!((u6 >> 16) & 0xF, Canal::A as u32);
    }

    #[test]
    fn la_mezcla_cae_en_los_canales_b_c_y_d_de_u6() {
        let m = Mezcla {
            sierra: 0x1111,
            triangular: 0x2222,
            pulso: 0x3333,
            seno: 0x4444,
        };
        let ts = tramas_vco4(&[0; 4], 0, m);
        assert_eq!(word(&ts[1], U6) & 0xFFFF, 0x1111, "sierra en B");
        assert_eq!(word(&ts[2], U6) & 0xFFFF, 0x2222, "triangular en C");
        assert_eq!(word(&ts[3], U6) & 0xFFFF, 0x3333, "pulso en D");
        assert_eq!(word(&ts[0], U7) & 0xFFFF, 0x4444, "seno en el A de U7");
    }

    #[test]
    fn los_canales_de_reserva_de_u7_salen_en_cero() {
        let m = Mezcla {
            sierra: 0xFFFF,
            triangular: 0xFFFF,
            pulso: 0xFFFF,
            seno: 0xFFFF,
        };
        let ts = tramas_vco4(&[0xFFFF; 4], 0xFFFF, m);
        for (i, t) in ts.iter().enumerate().skip(1) {
            assert_eq!(word(t, U7) & 0xFFFF, 0, "U7 canal {i} es de reserva");
        }
    }
}
