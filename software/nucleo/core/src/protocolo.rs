//! §4.1. Esta enumeracion es la superficie COMPLETA del instrumento: por §2.1
//! no puede haber capacidad fuera de ella. Añadir una funcion es añadir aqui.
//!
//! El bit alto de la etiqueta dice la direccion: puesto, va del instrumento al
//! cliente. El `match` de `etiqueta` es exhaustivo, asi que un mensaje nuevo
//! sin codificar rompe la compilacion — esa es la guardia de verdad.

use crate::descriptor::{ErrorCodec, Escritor, Lector};
use crate::param::{ParamId, Valor};

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Rgb {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Mensaje {
    // --- del cliente al instrumento ---
    Hello { version: u16 },
    Describe,
    Get(ParamId),
    Set(ParamId, Valor),
    Subscribe { activo: bool },
    PresetList,
    PresetLoad(u8),
    PresetSave(u8),
    TuneStart,
    PatchScan,
    Telemetry,
    /// §2.1: enciende el LED de un parametro o de un jack. Señalar y el
    /// patcheo guiado son el mismo mecanismo.
    Point { id: ParamId, color: Rgb },
    /// §7.5: unos segundos de audio para que el agente los analice.
    Memo { segundos: u8 },

    // --- del instrumento al cliente ---
    /// Va a TODOS los suscriptores, sin importar quien movio el parametro.
    Changed(ParamId, Valor),
    Modules,
    TuneProgress { voz: u8, cents_x100: i16, hecho: bool },
    Jacks,
    Pending { token: u16, id: ParamId },
    Resolved { token: u16, confirmado: bool },
}

pub type ErrorProto = ErrorCodec;

const T_HELLO: u8 = 0x01;
const T_DESCRIBE: u8 = 0x02;
const T_GET: u8 = 0x03;
const T_SET: u8 = 0x04;
const T_SUBSCRIBE: u8 = 0x05;
const T_PRESET_LIST: u8 = 0x06;
const T_PRESET_LOAD: u8 = 0x07;
const T_PRESET_SAVE: u8 = 0x08;
const T_TUNE_START: u8 = 0x09;
const T_PATCH_SCAN: u8 = 0x0A;
const T_TELEMETRY: u8 = 0x0B;
const T_POINT: u8 = 0x0C;
const T_MEMO: u8 = 0x0D;
const T_CHANGED: u8 = 0x81;
const T_MODULES: u8 = 0x82;
const T_TUNE_PROGRESS: u8 = 0x83;
const T_JACKS: u8 = 0x84;
const T_PENDING: u8 = 0x85;
const T_RESOLVED: u8 = 0x86;

fn etiqueta(m: &Mensaje) -> u8 {
    use Mensaje::*;
    match m {
        Hello { .. } => T_HELLO,
        Describe => T_DESCRIBE,
        Get(..) => T_GET,
        Set(..) => T_SET,
        Subscribe { .. } => T_SUBSCRIBE,
        PresetList => T_PRESET_LIST,
        PresetLoad(..) => T_PRESET_LOAD,
        PresetSave(..) => T_PRESET_SAVE,
        TuneStart => T_TUNE_START,
        PatchScan => T_PATCH_SCAN,
        Telemetry => T_TELEMETRY,
        Point { .. } => T_POINT,
        Memo { .. } => T_MEMO,
        Changed(..) => T_CHANGED,
        Modules => T_MODULES,
        TuneProgress { .. } => T_TUNE_PROGRESS,
        Jacks => T_JACKS,
        Pending { .. } => T_PENDING,
        Resolved { .. } => T_RESOLVED,
    }
}

impl Mensaje {
    pub fn del_instrumento(&self) -> bool {
        etiqueta(self) & 0x80 != 0
    }
}

pub fn codificar(m: &Mensaje, buf: &mut [u8]) -> Result<usize, ErrorProto> {
    use Mensaje::*;
    let mut w = Escritor { buf, n: 0 };
    w.u8(etiqueta(m))?;
    match m {
        Hello { version } => w.u16(*version)?,
        Describe | PresetList | TuneStart | PatchScan | Telemetry | Modules | Jacks => {}
        Get(id) => w.u16(id.0)?,
        Set(id, v) | Changed(id, v) => {
            w.u16(id.0)?;
            w.i32(*v)?;
        }
        Subscribe { activo } => w.u8(*activo as u8)?,
        PresetLoad(n) | PresetSave(n) | Memo { segundos: n } => w.u8(*n)?,
        Point { id, color } => {
            w.u16(id.0)?;
            w.crudo(&[color.r, color.g, color.b])?;
        }
        TuneProgress { voz, cents_x100, hecho } => {
            w.u8(*voz)?;
            w.crudo(&cents_x100.to_le_bytes())?;
            w.u8(*hecho as u8)?;
        }
        Pending { token, id } => {
            w.u16(*token)?;
            w.u16(id.0)?;
        }
        Resolved { token, confirmado } => {
            w.u16(*token)?;
            w.u8(*confirmado as u8)?;
        }
    }
    Ok(w.n)
}

pub fn decodificar(buf: &[u8]) -> Result<Mensaje, ErrorProto> {
    use Mensaje::*;
    let mut r = Lector { buf, n: 0 };
    let t = r.u8().map_err(|_| ErrorCodec::Truncado)?;
    Ok(match t {
        T_HELLO => Hello { version: r.u16()? },
        T_DESCRIBE => Describe,
        T_GET => Get(ParamId(r.u16()?)),
        T_SET => Set(ParamId(r.u16()?), r.i32()?),
        T_SUBSCRIBE => Subscribe { activo: r.u8()? != 0 },
        T_PRESET_LIST => PresetList,
        T_PRESET_LOAD => PresetLoad(r.u8()?),
        T_PRESET_SAVE => PresetSave(r.u8()?),
        T_TUNE_START => TuneStart,
        T_PATCH_SCAN => PatchScan,
        T_TELEMETRY => Telemetry,
        T_POINT => {
            let id = ParamId(r.u16()?);
            let c = r.crudo(3)?;
            Point { id, color: Rgb { r: c[0], g: c[1], b: c[2] } }
        }
        T_MEMO => Memo { segundos: r.u8()? },
        T_CHANGED => Changed(ParamId(r.u16()?), r.i32()?),
        T_MODULES => Modules,
        T_TUNE_PROGRESS => {
            let voz = r.u8()?;
            let cents_x100 = i16::from_le_bytes(r.crudo(2)?.try_into().unwrap());
            TuneProgress { voz, cents_x100, hecho: r.u8()? != 0 }
        }
        T_JACKS => Jacks,
        T_PENDING => Pending { token: r.u16()?, id: ParamId(r.u16()?) },
        T_RESOLVED => Resolved { token: r.u16()?, confirmado: r.u8()? != 0 },
        _ => return Err(ErrorCodec::Desconocido),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Una de cada variante. El `match` del codec es exhaustivo, asi que
    /// añadir un mensaje sin codificarlo rompe la compilacion — que es la
    /// guardia de verdad de §4.1.
    fn todas() -> [Mensaje; 19] {
        let id = ParamId::nuevo(3, 2, 17);
        [
            Mensaje::Hello { version: 1 },
            Mensaje::Describe,
            Mensaje::Get(id),
            Mensaje::Set(id, -123_456),
            Mensaje::Subscribe { activo: true },
            Mensaje::PresetList,
            Mensaje::PresetLoad(9),
            Mensaje::PresetSave(9),
            Mensaje::TuneStart,
            Mensaje::PatchScan,
            Mensaje::Telemetry,
            Mensaje::Point { id, color: Rgb { r: 255, g: 0, b: 128 } },
            Mensaje::Memo { segundos: 8 },
            Mensaje::Changed(id, i32::MIN),
            Mensaje::Modules,
            Mensaje::TuneProgress { voz: 3, cents_x100: -1750, hecho: false },
            Mensaje::Jacks,
            Mensaje::Pending { token: 4242, id },
            Mensaje::Resolved { token: 4242, confirmado: true },
        ]
    }

    #[test]
    fn cada_mensaje_va_y_vuelve_identico() {
        let mut buf = [0u8; 64];
        for m in todas() {
            let n = codificar(&m, &mut buf).unwrap();
            assert_eq!(decodificar(&buf[..n]).unwrap(), m, "se rompio {m:?}");
        }
    }

    #[test]
    fn ninguna_etiqueta_se_repite() {
        let mut vistas = heapless::Vec::<u8, 19>::new();
        for m in todas() {
            let e = etiqueta(&m);
            assert!(!vistas.contains(&e), "la etiqueta {e:#04x} esta duplicada");
            vistas.push(e).unwrap();
        }
    }

    #[test]
    fn la_direccion_va_en_el_bit_alto_de_la_etiqueta() {
        let mut buf = [0u8; 64];
        for m in todas() {
            codificar(&m, &mut buf).unwrap();
            assert_eq!(buf[0] & 0x80 != 0, m.del_instrumento(), "{m:?}");
        }
    }

    #[test]
    fn una_etiqueta_desconocida_se_rechaza() {
        assert_eq!(decodificar(&[0x7F]), Err(ErrorCodec::Desconocido));
        assert_eq!(decodificar(&[]), Err(ErrorCodec::Truncado));
        assert_eq!(decodificar(&[T_GET, 0x11]), Err(ErrorCodec::Truncado));
    }

    #[test]
    fn cualquier_truncamiento_se_rechaza_en_vez_de_inventar() {
        let mut buf = [0u8; 64];
        for m in todas() {
            let n = codificar(&m, &mut buf).unwrap();
            for corte in 1..n {
                assert!(decodificar(&buf[..corte]).is_err(), "{m:?} trunco en {corte}");
            }
        }
    }
}
