//! El descriptor (§3.3), sus marcas de medida (§3.4) y su ambito (§3.6),
//! con el codec binario que el micro emite y la carcasa expande a JSON.
//!
//! El formato es de ancho fijo y little-endian a proposito: lo van a parsear
//! el puente inalambrico y JavaScript en la UI web, y un `DataView` tiene que
//! poder leerlo sin librerias.
//!
//! ```text
//!   off  tam  campo
//!    0    2   id (u16)
//!    2    1   banderas
//!               bit0 solo_lectura   bit1 medida   bit2 confirmacion_fisica
//!               bit3 ambito (0 = compartido, 1 = por-voz)
//!               bits 4-5 tipo (0 continuo, 1 enumerado, 2 booleano)
//!    3    4   min (i32)
//!    7    4   max (i32)
//!   11    4   def (i32)
//!   15    1   unidad
//!   16    1   largo del nombre
//!   17    n   nombre en UTF-8
//!        1   numero de etiquetas
//!        por etiqueta: 1 byte de largo + los bytes UTF-8
//! ```

use crate::param::ParamId;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Tipo {
    Continuo = 0,
    Enumerado = 1,
    Booleano = 2,
}

/// §3.6. Sin esta marca ni la UI sabe dibujarlo, ni el agente sabe que puede
/// mover por nota, ni un preset sabe que guardar una vez y que guardar N.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Ambito {
    Compartido = 0,
    PorVoz = 1,
}

/// Las unidades son documentacion del agente (§2.1), no cosmetica: son lo que
/// un LLM lee para deducir que hace un parametro.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum Unidad {
    Ninguna = 0,
    Hz = 1,
    Cents = 2,
    Milivoltios = 3,
    Milisegundos = 4,
    /// Milesimas de 1.0 — porcentajes, atenuaciones, resonancia.
    Milesimas = 5,
    MilidB = 6,
    Semitonos = 7,
    Grados = 8,
    /// Para tiempos largos que no caben comodos en milisegundos cortos.
    Segundos = 9,
}

impl Unidad {
    pub fn de_byte(b: u8) -> Option<Self> {
        use Unidad::*;
        Some(match b {
            0 => Ninguna,
            1 => Hz,
            2 => Cents,
            3 => Milivoltios,
            4 => Milisegundos,
            5 => Milesimas,
            6 => MilidB,
            7 => Semitonos,
            8 => Grados,
            9 => Segundos,
            _ => return None,
        })
    }
}

/// Lo que el firmware declara.
#[derive(Clone, Copy, Debug)]
pub struct Descriptor {
    pub id: ParamId,
    pub nombre: &'static str,
    pub tipo: Tipo,
    pub ambito: Ambito,
    /// §3.4: no se escribe desde un cliente.
    pub solo_lectura: bool,
    /// §3.4: lo publica el instrumento a partir de lo que mide (§7).
    pub medida: bool,
    /// §2.2: el micro RETIENE la operacion hasta la confirmacion fisica.
    pub confirmacion_fisica: bool,
    pub min: i32,
    pub max: i32,
    pub def: i32,
    pub unidad: Unidad,
    pub etiquetas: &'static [&'static str],
}

/// Lo que un parser recupera, prestado del propio buffer: en `no_std` no hay
/// donde copiarlo.
#[derive(Clone, Copy, Debug)]
pub struct DescriptorLeido<'a> {
    pub id: ParamId,
    pub nombre: &'a str,
    pub tipo: Tipo,
    pub ambito: Ambito,
    pub solo_lectura: bool,
    pub medida: bool,
    pub confirmacion_fisica: bool,
    pub min: i32,
    pub max: i32,
    pub def: i32,
    pub unidad: Unidad,
    pub etiquetas: Etiquetas<'a>,
}

/// Las etiquetas del parser, validadas de una en `leer`: por eso el iterador
/// puede quedarse callado en vez de devolver `Result`.
#[derive(Clone, Copy, Debug)]
pub struct Etiquetas<'a> {
    crudo: &'a [u8],
    quedan: u8,
}

impl<'a> Iterator for Etiquetas<'a> {
    type Item = &'a str;
    fn next(&mut self) -> Option<&'a str> {
        if self.quedan == 0 {
            return None;
        }
        let largo = *self.crudo.first()? as usize;
        let txt = core::str::from_utf8(self.crudo.get(1..1 + largo)?).ok()?;
        self.crudo = &self.crudo[1 + largo..];
        self.quedan -= 1;
        Some(txt)
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorCodec {
    /// El buffer de salida no da.
    SinSitio,
    /// El buffer de entrada se acaba antes de tiempo.
    Truncado,
    /// Los bytes estan ahi pero no significan nada valido.
    Invalido,
    /// Etiqueta de mensaje que no esta en la tabla de §4.1 (lo usa `protocolo`).
    Desconocido,
}

pub fn escribir(d: &Descriptor, buf: &mut [u8]) -> Result<usize, ErrorCodec> {
    let mut w = Escritor { buf, n: 0 };
    w.u16(d.id.0)?;
    let banderas = (d.solo_lectura as u8)
        | ((d.medida as u8) << 1)
        | ((d.confirmacion_fisica as u8) << 2)
        | ((d.ambito as u8) << 3)
        | ((d.tipo as u8) << 4);
    w.u8(banderas)?;
    w.i32(d.min)?;
    w.i32(d.max)?;
    w.i32(d.def)?;
    w.u8(d.unidad as u8)?;
    w.texto(d.nombre)?;
    w.u8(u8::try_from(d.etiquetas.len()).map_err(|_| ErrorCodec::Invalido)?)?;
    for e in d.etiquetas {
        w.texto(e)?;
    }
    Ok(w.n)
}

pub fn leer(buf: &[u8]) -> Result<(DescriptorLeido<'_>, usize), ErrorCodec> {
    let mut r = Lector { buf, n: 0 };
    let id = ParamId(r.u16()?);
    let banderas = r.u8()?;
    let tipo = match (banderas >> 4) & 0b11 {
        0 => Tipo::Continuo,
        1 => Tipo::Enumerado,
        2 => Tipo::Booleano,
        _ => return Err(ErrorCodec::Invalido),
    };
    let min = r.i32()?;
    let max = r.i32()?;
    let def = r.i32()?;
    let unidad = Unidad::de_byte(r.u8()?).ok_or(ErrorCodec::Invalido)?;
    let nombre = r.texto()?;
    let n_etiquetas = r.u8()?;
    // Se validan aqui para que el iterador no pueda fallar a medio camino.
    let inicio = r.n;
    for _ in 0..n_etiquetas {
        r.texto()?;
    }
    Ok((
        DescriptorLeido {
            id,
            nombre,
            tipo,
            ambito: if banderas & 0b1000 != 0 {
                Ambito::PorVoz
            } else {
                Ambito::Compartido
            },
            solo_lectura: banderas & 0b1 != 0,
            medida: banderas & 0b10 != 0,
            confirmacion_fisica: banderas & 0b100 != 0,
            min,
            max,
            def,
            unidad,
            etiquetas: Etiquetas {
                crudo: &buf[inicio..r.n],
                quedan: n_etiquetas,
            },
        },
        r.n,
    ))
}

pub(crate) struct Escritor<'a> {
    pub buf: &'a mut [u8],
    pub n: usize,
}

impl Escritor<'_> {
    pub fn crudo(&mut self, bytes: &[u8]) -> Result<(), ErrorCodec> {
        let fin = self.n + bytes.len();
        self.buf
            .get_mut(self.n..fin)
            .ok_or(ErrorCodec::SinSitio)?
            .copy_from_slice(bytes);
        self.n = fin;
        Ok(())
    }
    pub fn u8(&mut self, v: u8) -> Result<(), ErrorCodec> {
        self.crudo(&[v])
    }
    pub fn u16(&mut self, v: u16) -> Result<(), ErrorCodec> {
        self.crudo(&v.to_le_bytes())
    }
    pub fn i32(&mut self, v: i32) -> Result<(), ErrorCodec> {
        self.crudo(&v.to_le_bytes())
    }
    pub fn texto(&mut self, s: &str) -> Result<(), ErrorCodec> {
        self.u8(u8::try_from(s.len()).map_err(|_| ErrorCodec::Invalido)?)?;
        self.crudo(s.as_bytes())
    }
}

pub(crate) struct Lector<'a> {
    pub buf: &'a [u8],
    pub n: usize,
}

impl<'a> Lector<'a> {
    pub fn crudo(&mut self, largo: usize) -> Result<&'a [u8], ErrorCodec> {
        let t = self
            .buf
            .get(self.n..self.n.checked_add(largo).ok_or(ErrorCodec::Truncado)?)
            .ok_or(ErrorCodec::Truncado)?;
        self.n += largo;
        Ok(t)
    }
    pub fn u8(&mut self) -> Result<u8, ErrorCodec> {
        Ok(self.crudo(1)?[0])
    }
    pub fn u16(&mut self) -> Result<u16, ErrorCodec> {
        Ok(u16::from_le_bytes(self.crudo(2)?.try_into().unwrap()))
    }
    pub fn i32(&mut self) -> Result<i32, ErrorCodec> {
        Ok(i32::from_le_bytes(self.crudo(4)?.try_into().unwrap()))
    }
    pub fn texto(&mut self) -> Result<&'a str, ErrorCodec> {
        let largo = self.u8()? as usize;
        core::str::from_utf8(self.crudo(largo)?).map_err(|_| ErrorCodec::Invalido)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const CUTOFF: Descriptor = Descriptor {
        id: ParamId::nuevo(5, 0, 1),
        nombre: "corte del filtro",
        tipo: Tipo::Continuo,
        ambito: Ambito::PorVoz,
        solo_lectura: false,
        medida: false,
        confirmacion_fisica: false,
        min: 0,
        max: 65535,
        def: 32768,
        unidad: Unidad::Hz,
        etiquetas: &[],
    };

    const MODO: Descriptor = Descriptor {
        id: ParamId::nuevo(0, 0, 7),
        nombre: "modo de voces",
        tipo: Tipo::Enumerado,
        ambito: Ambito::Compartido,
        solo_lectura: false,
        medida: false,
        confirmacion_fisica: true,
        min: 0,
        max: 3,
        def: 1,
        unidad: Unidad::Ninguna,
        etiquetas: &["mono", "unisono", "poly", "parafonico"],
    };

    const BRILLO: Descriptor = Descriptor {
        id: ParamId::nuevo(0, 0, 200),
        nombre: "brillo percibido",
        tipo: Tipo::Continuo,
        ambito: Ambito::Compartido,
        solo_lectura: true,
        medida: true,
        confirmacion_fisica: false,
        min: -6000,
        max: 0,
        def: 0,
        unidad: Unidad::MilidB,
        etiquetas: &[],
    };

    fn ida_y_vuelta(d: &Descriptor) {
        let mut buf = [0u8; 256];
        let n = escribir(d, &mut buf).unwrap();
        let (leido, consumido) = leer(&buf[..n]).unwrap();
        assert_eq!(consumido, n, "el parser tiene que consumir lo que se escribio");
        assert_eq!(leido.id, d.id);
        assert_eq!(leido.nombre, d.nombre);
        assert_eq!(leido.tipo, d.tipo);
        assert_eq!(leido.ambito, d.ambito);
        assert_eq!(leido.solo_lectura, d.solo_lectura);
        assert_eq!(leido.medida, d.medida);
        assert_eq!(leido.confirmacion_fisica, d.confirmacion_fisica);
        assert_eq!((leido.min, leido.max, leido.def), (d.min, d.max, d.def));
        assert_eq!(leido.unidad, d.unidad);
        let recuperadas: heapless::Vec<&str, 16> = leido.etiquetas.collect();
        assert_eq!(recuperadas.as_slice(), d.etiquetas);
    }

    #[test]
    fn un_descriptor_generado_se_parsea_a_lo_mismo() {
        // §9, fila "Modelo y descriptor".
        ida_y_vuelta(&CUTOFF);
        ida_y_vuelta(&MODO);
        ida_y_vuelta(&BRILLO);
    }

    #[test]
    fn el_buffer_corto_no_desborda_ni_entra_en_panico() {
        let mut buf = [0u8; 4];
        assert!(matches!(escribir(&MODO, &mut buf), Err(ErrorCodec::SinSitio)));
        let mut ok = [0u8; 256];
        let n = escribir(&MODO, &mut ok).unwrap();
        for corte in 0..n {
            // Cualquier truncamiento tiene que dar error, jamas un parse a medias.
            assert!(leer(&ok[..corte]).is_err(), "trunco en {corte} y no se quejo");
        }
    }

    #[test]
    fn las_banderas_de_medida_sobreviven_el_viaje() {
        // §3.4: si esto se pierde, un cliente escribiria sobre una medida.
        let mut buf = [0u8; 256];
        let n = escribir(&BRILLO, &mut buf).unwrap();
        let (leido, _) = leer(&buf[..n]).unwrap();
        assert!(leido.solo_lectura && leido.medida);
    }
}
