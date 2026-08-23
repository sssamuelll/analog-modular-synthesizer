//! §3.5 y §3.6. Cada modulo lleva una EEPROM 24AA02E48 en I2C con ID unico de
//! fabrica: treinta centavos, sin procesador, nada que actualizar y nada que
//! se cuelgue.
//!
//! # El mapa de la EEPROM
//!
//! ```text
//!   0x00  1  magia = 0x17
//!   0x01  1  version de la cabecera = 1
//!   0x02  2  tipo de placa (u16 LE)
//!   0x04  1  revision
//!   0x05  1  largo del blob de calibracion
//!   0x06  4  serial (u32 LE)
//!   0x0A  2  crc16 de 0x00..0x0A (CCITT-FALSE, poly 0x1021, init 0xFFFF)
//!   0x0C  n  blob de calibracion
//! ```
//!
//! El EUI-48 de fabrica vive arriba del todo y es de solo lectura: **no se
//! toca**. La direccion exacta esta sin verificar contra el PDF de Microchip;
//! `FIN_ZONA_LIBRE` es la cota conservadora mientras tanto.
//!
//! # El conteo de voces NO sale de aqui
//!
//! La EEPROM da tipo y revision. El numero de voces sale del catalogo, que
//! vive en el firmware del cerebro (§3.5 paso 3). Son 256 bytes: alcanzan para
//! identidad y calibracion, no para un descriptor.

use crate::descriptor::Descriptor;

pub const MAGIA: u8 = 0x17;
pub const VERSION_CABECERA: u8 = 1;
/// Hasta donde podemos escribir sin pisar el EUI-48 de fabrica.
/// **Sin verificar contra el datasheet de Microchip** — cota conservadora.
pub const FIN_ZONA_LIBRE: usize = 0xFA;
const CABECERA: usize = 0x0C;

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct TipoPlaca(pub u16);

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Identidad<'a> {
    pub tipo: TipoPlaca,
    pub revision: u8,
    pub serial: u32,
    /// La calibracion viaja con la placa.
    pub calibracion: &'a [u8],
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorEeprom {
    /// Ni virgen ni nuestra: no hay modulo aqui.
    Magia,
    /// Cabecera de una version que este firmware no sabe leer.
    Version,
    Crc,
    Truncada,
}

/// CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, sin reflejar.
pub fn crc16(datos: &[u8]) -> u16 {
    let mut crc: u16 = 0xFFFF;
    for b in datos {
        crc ^= (*b as u16) << 8;
        for _ in 0..8 {
            crc = if crc & 0x8000 != 0 {
                (crc << 1) ^ 0x1021
            } else {
                crc << 1
            };
        }
    }
    crc
}

pub fn leer_identidad(bytes: &[u8]) -> Result<Identidad<'_>, ErrorEeprom> {
    let cab = bytes.get(..CABECERA).ok_or(ErrorEeprom::Truncada)?;
    if cab[0] != MAGIA {
        return Err(ErrorEeprom::Magia);
    }
    if cab[1] != VERSION_CABECERA {
        return Err(ErrorEeprom::Version);
    }
    let esperado = u16::from_le_bytes([cab[10], cab[11]]);
    if crc16(&cab[..10]) != esperado {
        return Err(ErrorEeprom::Crc);
    }
    let largo = cab[5] as usize;
    let fin = CABECERA + largo;
    if fin > FIN_ZONA_LIBRE {
        return Err(ErrorEeprom::Truncada);
    }
    Ok(Identidad {
        tipo: TipoPlaca(u16::from_le_bytes([cab[2], cab[3]])),
        revision: cab[4],
        serial: u32::from_le_bytes([cab[6], cab[7], cab[8], cab[9]]),
        calibracion: bytes.get(CABECERA..fin).ok_or(ErrorEeprom::Truncada)?,
    })
}

/// Una entrada del catalogo: el descriptor de un tipo de placa, que vive en el
/// firmware del cerebro porque en 256 bytes de EEPROM no cabe.
#[derive(Clone, Copy, Debug)]
pub struct Placa {
    pub tipo: TipoPlaca,
    pub nombre: &'static str,
    /// Cuantas voces aporta esta placa. `0` = no aporta (mixer, utilidades).
    pub voces: u8,
    pub params: &'static [Descriptor],
}

pub const TIPO_VCO4: TipoPlaca = TipoPlaca(0x0003);

/// La tabla que convierte «tipo de placa» en mapa de parametros.
///
/// Estrenar un tipo de modulo pide actualizar el firmware del cerebro; la UI en
/// cambio no cambia nunca, porque renderiza lo que le llegue.
pub static CATALOGO: &[Placa] = &[Placa {
    tipo: TIPO_VCO4,
    nombre: "VCO x4 SSI2130",
    voces: 4,
    params: &[],
}];

pub fn placa_de(tipo: TipoPlaca) -> Option<&'static Placa> {
    CATALOGO.iter().find(|p| p.tipo == tipo)
}

/// §3.6: **las voces del instrumento son el minimo de la cadena.**
///
/// Con 8 VCO y 4 VCF tienes 4 voces, y el instrumento lo **dice** en vez de
/// sonar raro. Las placas que no aportan voces no bajan el conteo.
pub fn voces_del_instrumento(placas: &[&Placa]) -> u8 {
    placas
        .iter()
        .map(|p| p.voces)
        .filter(|v| *v > 0)
        .min()
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn eeprom(tipo: u16, rev: u8, serial: u32, calib: &[u8]) -> [u8; 256] {
        let mut e = [0xFFu8; 256];
        e[0] = MAGIA;
        e[1] = VERSION_CABECERA;
        e[2..4].copy_from_slice(&tipo.to_le_bytes());
        e[4] = rev;
        e[5] = calib.len() as u8;
        e[6..10].copy_from_slice(&serial.to_le_bytes());
        let c = crc16(&e[0..10]);
        e[10..12].copy_from_slice(&c.to_le_bytes());
        e[12..12 + calib.len()].copy_from_slice(calib);
        e
    }

    fn placa(voces: u8) -> Placa {
        Placa {
            tipo: TipoPlaca(0x9999),
            nombre: "x",
            voces,
            params: &[],
        }
    }

    #[test]
    fn el_crc_es_el_ccitt_false_de_verdad() {
        // Vector canonico del CRC-16/CCITT-FALSE: "123456789" -> 0x29B1.
        assert_eq!(crc16(b"123456789"), 0x29B1);
    }

    #[test]
    fn una_eeprom_buena_da_identidad_y_calibracion() {
        let e = eeprom(0x0003, 1, 0xDEAD_BEEF, &[1, 2, 3, 4]);
        let id = leer_identidad(&e).unwrap();
        assert_eq!(id.tipo, TIPO_VCO4);
        assert_eq!(id.revision, 1);
        assert_eq!(id.serial, 0xDEAD_BEEF);
        assert_eq!(id.calibracion, &[1, 2, 3, 4]);
    }

    #[test]
    fn una_eeprom_virgen_o_corrupta_no_se_confunde_con_un_modulo() {
        assert_eq!(leer_identidad(&[0xFF; 256]), Err(ErrorEeprom::Magia));
        let mut e = eeprom(3, 1, 1, &[]);
        e[4] = 99; // revision cambiada sin recalcular el crc
        assert_eq!(leer_identidad(&e), Err(ErrorEeprom::Crc));
    }

    #[test]
    fn una_cabecera_de_otra_version_se_rechaza_en_vez_de_malinterpretarse() {
        let mut e = eeprom(3, 1, 1, &[]);
        e[1] = 2;
        let c = crc16(&e[0..10]);
        e[10..12].copy_from_slice(&c.to_le_bytes());
        assert_eq!(leer_identidad(&e), Err(ErrorEeprom::Version));
    }

    #[test]
    fn un_blob_que_invadiria_el_eui48_se_rechaza() {
        let mut e = eeprom(3, 1, 1, &[]);
        e[5] = 0xFF;
        let c = crc16(&e[0..10]);
        e[10..12].copy_from_slice(&c.to_le_bytes());
        assert_eq!(leer_identidad(&e), Err(ErrorEeprom::Truncada));
    }

    #[test]
    fn el_catalogo_conoce_al_modulo_3() {
        assert_eq!(placa_de(TIPO_VCO4).unwrap().voces, 4);
        assert!(placa_de(TipoPlaca(0xFFFF)).is_none());
    }

    #[test]
    fn ocho_vco_y_cuatro_vcf_dan_cuatro_voces() {
        // §9, fila "Conteo de voces". La regla del minimo de la cadena.
        let vco8 = placa(8);
        let vcf4 = placa(4);
        assert_eq!(voces_del_instrumento(&[&vco8, &vcf4]), 4);
    }

    #[test]
    fn los_modulos_sin_voces_no_bajan_el_conteo() {
        let vco = placa(4);
        let mixer = placa(0);
        assert_eq!(voces_del_instrumento(&[&vco, &mixer]), 4);
    }

    #[test]
    fn sin_modulos_no_hay_voces_y_se_dice() {
        assert_eq!(voces_del_instrumento(&[]), 0);
        assert_eq!(voces_del_instrumento(&[&placa(0)]), 0);
    }

    #[test]
    fn el_conteo_no_es_una_constante_disfrazada() {
        // Si alguien escribe un 4 en el camino, uno de estos falla.
        for n in 1..=16u8 {
            assert_eq!(voces_del_instrumento(&[&placa(n)]), n);
        }
    }
}
