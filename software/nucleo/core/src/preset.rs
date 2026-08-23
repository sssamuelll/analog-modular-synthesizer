//! §6.1. Un modular no tiene presets porque el patch es fisico. Por eso aqui
//! el patch **es un dato**: el preset guarda los pares (jack origen -> jack
//! destino) y, gracias al motor de §7.6, tambien cuanto atenua cada cable.
//!
//! Un preset es **de una parte** (§3.6). Lo que en otros sintes se llama
//! *performance* o *combi* son los parametros de la ranura `0`, guardados
//! como cualquier otro preset: no necesita concepto nuevo.
//!
//! # El formato de cable
//!
//! ```text
//!   1 + n   nombre
//!   1 + n   autor
//!   1       numero de etiquetas, luego 1 + n cada una
//!   1       numero de modulos requeridos, luego por cada uno: u16 tipo + u8 rev
//!   1       numero de valores, luego por cada uno: u32 id + i32 valor
//!   1       numero de conexiones, luego por cada una:
//!             u8 ranura origen, u8 jack origen,
//!             u8 ranura destino, u8 jack destino,
//!             u16 atenuacion en milesimas
//! ```

use crate::descriptor::{ErrorCodec, Escritor, Lector};
use crate::descubrimiento::TipoPlaca;
use crate::param::{ParamId, Valor};

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct JackId {
    /// Plana a proposito **por ahora**: `ParamId` ya lleva ruta de tres
    /// niveles (§3.1) y esto no. Que un jack detras de un concentrador
    /// exista es una pregunta del patch bay, que es de cables analogicos y
    /// no del bus digital. Issue #157.
    pub ranura: u8,
    pub jack: u8,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Conexion {
    pub origen: JackId,
    pub destino: JackId,
    /// El premio que no se buscaba (§7.6): no solo la conexion, tambien
    /// cuanto atenua. 1000 = a plena escala.
    pub atenuacion_milesimas: u16,
}

/// Lo que el firmware declara al guardar.
#[derive(Clone, Copy, Debug)]
pub struct Preset<'a> {
    pub nombre: &'a str,
    pub autor: &'a str,
    pub etiquetas: &'a [&'a str],
    /// Para **fallar en voz alta**: si falta un modulo lo dice, en vez de
    /// sonar raro.
    pub requiere: &'a [(TipoPlaca, u8)],
    pub valores: &'a [(ParamId, Valor)],
    pub topologia: &'a [Conexion],
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorCarga {
    FaltaModulo { tipo: TipoPlaca, revision: u8 },
}

/// Lo que un parser recupera. Las secciones de largo variable quedan como
/// trozos crudos ya validados, y se recorren con iteradores.
#[derive(Clone, Copy, Debug)]
pub struct PresetLeido<'a> {
    pub nombre: &'a str,
    pub autor: &'a str,
    etiquetas: (&'a [u8], u8),
    requiere: &'a [u8],
    valores: &'a [u8],
    topologia: &'a [u8],
}

impl<'a> PresetLeido<'a> {
    pub fn etiquetas(&self) -> impl Iterator<Item = &'a str> {
        let (mut crudo, n) = self.etiquetas;
        (0..n).map_while(move |_| {
            let largo = *crudo.first()? as usize;
            let t = core::str::from_utf8(crudo.get(1..1 + largo)?).ok()?;
            crudo = &crudo[1 + largo..];
            Some(t)
        })
    }

    pub fn requiere(&self) -> impl Iterator<Item = (TipoPlaca, u8)> + 'a {
        self.requiere
            .chunks_exact(3)
            .map(|c| (TipoPlaca(u16::from_le_bytes([c[0], c[1]])), c[2]))
    }

    pub fn valores(&self) -> impl Iterator<Item = (ParamId, Valor)> + 'a {
        self.valores.chunks_exact(8).map(|c| {
            (
                ParamId(u32::from_le_bytes([c[0], c[1], c[2], c[3]])),
                i32::from_le_bytes([c[4], c[5], c[6], c[7]]),
            )
        })
    }

    pub fn topologia(&self) -> impl Iterator<Item = Conexion> + 'a {
        self.topologia.chunks_exact(6).map(|c| Conexion {
            origen: JackId {
                ranura: c[0],
                jack: c[1],
            },
            destino: JackId {
                ranura: c[2],
                jack: c[3],
            },
            atenuacion_milesimas: u16::from_le_bytes([c[4], c[5]]),
        })
    }

    /// §6.1: falla en voz alta y **nombra cual falta**. Un mensaje que no
    /// nombra el modulo no sirve para nada.
    pub fn comprobar(&self, presentes: &[(TipoPlaca, u8)]) -> Result<(), ErrorCarga> {
        for (tipo, revision) in self.requiere() {
            let hay = presentes.iter().any(|(t, r)| *t == tipo && *r >= revision);
            if !hay {
                return Err(ErrorCarga::FaltaModulo { tipo, revision });
            }
        }
        Ok(())
    }
}

pub fn escribir_preset(p: &Preset, buf: &mut [u8]) -> Result<usize, ErrorCodec> {
    let mut w = Escritor { buf, n: 0 };
    w.texto(p.nombre)?;
    w.texto(p.autor)?;
    w.u8(u8::try_from(p.etiquetas.len()).map_err(|_| ErrorCodec::Invalido)?)?;
    for e in p.etiquetas {
        w.texto(e)?;
    }
    w.u8(u8::try_from(p.requiere.len()).map_err(|_| ErrorCodec::Invalido)?)?;
    for (t, r) in p.requiere {
        w.u16(t.0)?;
        w.u8(*r)?;
    }
    w.u8(u8::try_from(p.valores.len()).map_err(|_| ErrorCodec::Invalido)?)?;
    for (id, v) in p.valores {
        w.u32(id.0)?;
        w.i32(*v)?;
    }
    w.u8(u8::try_from(p.topologia.len()).map_err(|_| ErrorCodec::Invalido)?)?;
    for c in p.topologia {
        w.crudo(&[
            c.origen.ranura,
            c.origen.jack,
            c.destino.ranura,
            c.destino.jack,
        ])?;
        w.u16(c.atenuacion_milesimas)?;
    }
    Ok(w.n)
}

pub fn leer_preset(buf: &[u8]) -> Result<PresetLeido<'_>, ErrorCodec> {
    let mut r = Lector { buf, n: 0 };
    let nombre = r.texto()?;
    let autor = r.texto()?;
    let n_etiquetas = r.u8()?;
    let ini = r.n;
    for _ in 0..n_etiquetas {
        r.texto()?;
    }
    let etiquetas = (&buf[ini..r.n], n_etiquetas);

    let n_req = r.u8()? as usize;
    let requiere = r.crudo(n_req * 3)?;
    let n_val = r.u8()? as usize;
    let valores = r.crudo(n_val * 8)?;
    let n_top = r.u8()? as usize;
    let topologia = r.crudo(n_top * 6)?;

    Ok(PresetLeido {
        nombre,
        autor,
        etiquetas,
        requiere,
        valores,
        topologia,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    const VCO: TipoPlaca = TipoPlaca(0x0003);
    const VCF: TipoPlaca = TipoPlaca(0x0005);

    const ETIQUETAS: &[&str] = &["bajo", "lento"];
    const REQUIERE: &[(TipoPlaca, u8)] = &[(VCO, 1), (VCF, 1)];
    const VALORES: &[(ParamId, Valor)] = &[
        (ParamId::nuevo(3, 0, 1), 24_000),
        (ParamId::nuevo(5, 0, 1), -300),
    ];
    const TOPOLOGIA: &[Conexion] = &[Conexion {
        origen: JackId { ranura: 3, jack: 4 },
        destino: JackId { ranura: 5, jack: 0 },
        atenuacion_milesimas: 400,
    }];

    fn preset() -> Preset<'static> {
        Preset {
            nombre: "bajo que respira",
            autor: "samuel",
            etiquetas: ETIQUETAS,
            requiere: REQUIERE,
            valores: VALORES,
            topologia: TOPOLOGIA,
        }
    }

    fn guardado() -> ([u8; 512], usize) {
        let mut buf = [0u8; 512];
        let n = escribir_preset(&preset(), &mut buf).unwrap();
        (buf, n)
    }

    #[test]
    fn un_preset_va_y_vuelve_entero() {
        let (buf, n) = guardado();
        let p = leer_preset(&buf[..n]).unwrap();
        assert_eq!(p.nombre, "bajo que respira");
        assert_eq!(p.autor, "samuel");
        let et: heapless::Vec<&str, 4> = p.etiquetas().collect();
        assert_eq!(et.as_slice(), &["bajo", "lento"]);
        let vals: heapless::Vec<(ParamId, Valor), 4> = p.valores().collect();
        assert_eq!(vals.as_slice(), preset().valores);
        let c = p.topologia().next().unwrap();
        assert_eq!(c.origen.ranura, 3);
        assert_eq!(c.destino.jack, 0);
        // §7.6 regala esto: no solo la conexion, tambien cuanto atenua.
        assert_eq!(c.atenuacion_milesimas, 400);
    }

    #[test]
    fn si_falta_un_modulo_lo_dice_y_nombra_cual() {
        // §6.1 fallar en voz alta, en vez de sonar raro.
        let (buf, n) = guardado();
        let p = leer_preset(&buf[..n]).unwrap();
        assert_eq!(p.comprobar(&[(VCO, 1), (VCF, 1)]), Ok(()));
        assert_eq!(
            p.comprobar(&[(VCO, 1)]),
            Err(ErrorCarga::FaltaModulo {
                tipo: VCF,
                revision: 1
            })
        );
    }

    #[test]
    fn una_revision_vieja_tambien_se_avisa_pero_una_nueva_sirve() {
        let (buf, n) = guardado();
        let p = leer_preset(&buf[..n]).unwrap();
        assert!(
            p.comprobar(&[(VCO, 0), (VCF, 1)]).is_err(),
            "rev 0 < la pedida"
        );
        assert!(
            p.comprobar(&[(VCO, 7), (VCF, 1)]).is_ok(),
            "una rev mas nueva vale"
        );
    }

    #[test]
    fn cualquier_truncamiento_se_rechaza_en_vez_de_leer_basura() {
        let (buf, n) = guardado();
        for corte in 0..n {
            assert!(
                leer_preset(&buf[..corte]).is_err(),
                "trunco en {corte} y no se quejo"
            );
        }
    }

    #[test]
    fn un_preset_vacio_tambien_va_y_vuelve() {
        let vacio = Preset {
            nombre: "",
            autor: "",
            etiquetas: &[],
            requiere: &[],
            valores: &[],
            topologia: &[],
        };
        let mut buf = [0u8; 64];
        let n = escribir_preset(&vacio, &mut buf).unwrap();
        let p = leer_preset(&buf[..n]).unwrap();
        assert_eq!(p.etiquetas().count(), 0);
        assert_eq!(p.valores().count(), 0);
        assert_eq!(p.comprobar(&[]), Ok(()));
    }
}
