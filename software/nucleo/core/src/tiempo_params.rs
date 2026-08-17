//! §7.2. Los parametros del reloj y sus medidas.
//!
//! **Las etiquetas de los enumerados son las de Ableton, literales** (§2.1 de
//! la spec del tiempo musical). Es decision de diseño, no comodidad: el agente
//! ya conoce ese vocabulario —leyo todos los manuales de DAW que existen— y no
//! conoce el nuestro.
//!
//! Los ids van en la ranura `0` parte `0`, en `0xC0..0xDF` — por encima de las
//! medidas de audio de `medidas.rs`, que ocupan `0x80..0xA2`.

use crate::descriptor::{Ambito, Descriptor, Tipo, Unidad};
use crate::modelo::{ErrorRegistro, Modelo};
use crate::param::ParamId;
use crate::rejilla::Rejilla;

const fn id(indice: u8) -> ParamId {
    ParamId::nuevo(0, 0, indice)
}

// --- Se escriben ---
pub const ID_FUENTE: ParamId = id(0xC0);
pub const ID_TEMPO: ParamId = id(0xC1);
pub const ID_COMPAS_NUM: ParamId = id(0xC2);
pub const ID_COMPAS_DEN: ParamId = id(0xC3);
pub const ID_PPQN_FUENTE: ParamId = id(0xC4);
pub const ID_RESET: ParamId = id(0xC5);
pub const ID_DIV_CLOCK_OUT: ParamId = id(0xC6);
pub const ID_CUANTIZACION: ParamId = id(0xC7);
pub const ID_TRANSPORTE: ParamId = id(0xC8);

// --- Se leen (§3.4: medidas) ---
pub const ID_TIENE_FASE: ParamId = id(0xD0);
pub const ID_POSICION: ParamId = id(0xD1);
pub const ID_COMPAS_ACTUAL: ParamId = id(0xD2);
pub const ID_TEMPO_MEDIDO: ParamId = id(0xD3);
pub const ID_RODANDO_LIBRE: ParamId = id(0xD4);
pub const ID_ANULADOS: ParamId = id(0xD5);

/// `automatica` primero, luego las cuatro fuentes en orden de precedencia.
pub const ETIQUETAS_FUENTE: &[&str] = &["automatica", "interno", "clock in", "midi", "link"];

/// Los divisores de `PPQN_INTERNO` que Eurorack usa de verdad (§3.3). Tienen
/// que dividir a 96 exacto, o la posicion se iria acumulando error.
pub const ETIQUETAS_PPQN: &[&str] = &["1", "2", "4", "24", "48"];

/// §5.3 del nucleo: el formato no unifico el comportamiento del reset, asi que
/// va como parametro. Unos modulos miran el estado del reloj al recibirlo,
/// otros esperan el siguiente flanco.
pub const ETIQUETAS_RESET: &[&str] = &["mira el reloj", "espera el flanco"];

pub const ETIQUETAS_DIV_CLOCK_OUT: &[&str] = &["1", "2", "4", "24", "48"];

/// `rango` son `(min, max, por_defecto)` — que es una cosa, no tres.
const fn escribible(
    id: ParamId,
    nombre: &'static str,
    tipo: Tipo,
    rango: (i32, i32, i32),
    unidad: Unidad,
    etiquetas: &'static [&'static str],
) -> Descriptor {
    let (min, max, def) = rango;
    Descriptor {
        id,
        nombre,
        tipo,
        ambito: Ambito::Compartido,
        solo_lectura: false,
        medida: false,
        confirmacion_fisica: false,
        acepta_modulacion: false,
        min,
        max,
        def,
        unidad,
        etiquetas,
    }
}

const fn medida(
    id: ParamId,
    nombre: &'static str,
    tipo: Tipo,
    rango: (i32, i32),
    unidad: Unidad,
) -> Descriptor {
    let (min, max) = rango;
    Descriptor {
        id,
        nombre,
        tipo,
        ambito: Ambito::Compartido,
        solo_lectura: true,
        medida: true,
        confirmacion_fisica: false,
        acepta_modulacion: false,
        min,
        max,
        def: 0,
        unidad,
        etiquetas: &[],
    }
}

/// Nombres escritos para alguien que nunca ha visto el instrumento.
pub static TIEMPO: [Descriptor; 15] = [
    escribible(
        ID_FUENTE,
        "fuente de sincronia",
        Tipo::Enumerado,
        (0, 4, 0),
        Unidad::Ninguna,
        ETIQUETAS_FUENTE,
    ),
    escribible(
        ID_TEMPO,
        "tempo",
        Tipo::Continuo,
        (20_000, 300_000, 120_000),
        Unidad::Milesimas,
        &[],
    ),
    escribible(
        ID_COMPAS_NUM,
        "compas: cuantos tiempos",
        Tipo::Continuo,
        (1, 16, 4),
        Unidad::Ninguna,
        &[],
    ),
    escribible(
        ID_COMPAS_DEN,
        "compas: que figura",
        Tipo::Enumerado,
        (0, 3, 1),
        Unidad::Ninguna,
        &["1/2", "1/4", "1/8", "1/16"],
    ),
    escribible(
        ID_PPQN_FUENTE,
        "pulsos por negra del clock in",
        Tipo::Enumerado,
        (0, 4, 3),
        Unidad::Ninguna,
        ETIQUETAS_PPQN,
    ),
    escribible(
        ID_RESET,
        "que hace el reset al llegar",
        Tipo::Enumerado,
        (0, 1, 0),
        Unidad::Ninguna,
        ETIQUETAS_RESET,
    ),
    escribible(
        ID_DIV_CLOCK_OUT,
        "pulsos por negra del clock out",
        Tipo::Enumerado,
        (0, 4, 3),
        Unidad::Ninguna,
        ETIQUETAS_DIV_CLOCK_OUT,
    ),
    escribible(
        ID_CUANTIZACION,
        "cuantizacion global",
        Tipo::Enumerado,
        (0, 8, 4),
        Unidad::Ninguna,
        Rejilla::ETIQUETAS,
    ),
    escribible(
        ID_TRANSPORTE,
        "transporte en marcha",
        Tipo::Booleano,
        (0, 1, 0),
        Unidad::Ninguna,
        &["parado", "corriendo"],
    ),
    medida(
        ID_TIENE_FASE,
        "sabe donde esta el 1",
        Tipo::Booleano,
        (0, 1),
        Unidad::Ninguna,
    ),
    medida(
        ID_POSICION,
        "pulsos desde el arranque",
        Tipo::Continuo,
        (0, i32::MAX),
        Unidad::Ninguna,
    ),
    medida(
        ID_COMPAS_ACTUAL,
        "compas actual",
        Tipo::Continuo,
        (0, i32::MAX),
        Unidad::Ninguna,
    ),
    medida(
        ID_TEMPO_MEDIDO,
        "tempo que se esta siguiendo",
        Tipo::Continuo,
        (0, 300_000),
        Unidad::Milesimas,
    ),
    medida(
        ID_RODANDO_LIBRE,
        "se cayo el reloj y va solo",
        Tipo::Booleano,
        (0, 1),
        Unidad::Ninguna,
    ),
    medida(
        ID_ANULADOS,
        "parametros con la automatizacion anulada",
        Tipo::Continuo,
        (0, 512),
        Unidad::Ninguna,
    ),
];

pub fn registrar(m: &mut Modelo) -> Result<(), ErrorRegistro> {
    for d in TIEMPO.iter() {
        m.registrar(d)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::modelo::ErrorSet;

    fn instrumento() -> Modelo {
        let mut m = Modelo::nuevo();
        registrar(&mut m).unwrap();
        m
    }

    #[test]
    fn las_etiquetas_de_la_cuantizacion_son_las_de_ableton() {
        // §2.1: es decision de diseño. El agente ya conoce ese vocabulario.
        let d = TIEMPO.iter().find(|d| d.id == ID_CUANTIZACION).unwrap();
        assert_eq!(d.etiquetas, Rejilla::ETIQUETAS);
        assert!(d.etiquetas.contains(&"1 compas"));
        assert!(d.etiquetas.contains(&"1/16"));
    }

    #[test]
    fn el_transporte_es_un_parametro_no_un_mensaje() {
        // §7.2, con consecuencia: por §2.1 el agente puede arrancarlo.
        let mut m = instrumento();
        assert!(m.set(ID_TRANSPORTE, 1).is_ok());
        assert_eq!(m.get(ID_TRANSPORTE), Some(1));
    }

    #[test]
    fn las_medidas_no_las_escribe_nadie() {
        let mut m = instrumento();
        for id in [
            ID_TIENE_FASE,
            ID_POSICION,
            ID_COMPAS_ACTUAL,
            ID_TEMPO_MEDIDO,
            ID_RODANDO_LIBRE,
            ID_ANULADOS,
        ] {
            assert_eq!(m.set(id, 1), Err(ErrorSet::SoloLectura), "{id:?}");
        }
    }

    #[test]
    fn todo_enumerado_trae_una_etiqueta_por_valor() {
        // Sin esto el agente ve un numero y no sabe que significa.
        for d in TIEMPO.iter().filter(|d| d.tipo == Tipo::Enumerado) {
            assert_eq!(
                d.etiquetas.len() as i32,
                d.max - d.min + 1,
                "{} tiene {} etiquetas para {} valores",
                d.nombre,
                d.etiquetas.len(),
                d.max - d.min + 1
            );
        }
    }

    #[test]
    fn el_tempo_trae_unidad_y_un_rango_que_se_puede_tocar() {
        let d = TIEMPO.iter().find(|d| d.id == ID_TEMPO).unwrap();
        assert_eq!(d.unidad, Unidad::Milesimas);
        assert!(d.min <= 20_000 && d.max >= 300_000, "de 20 a 300 BPM");
    }

    #[test]
    fn los_ppqn_dividen_a_la_resolucion_interna() {
        // Si no dividieran exacto, la posicion iria acumulando error pulso a
        // pulso — y la fase se iria corriendo sola.
        for e in ETIQUETAS_PPQN {
            let n: u32 = e.parse().unwrap();
            assert!(
                crate::rejilla::PPQN_INTERNO.is_multiple_of(n),
                "{n} no divide a {}",
                crate::rejilla::PPQN_INTERNO
            );
        }
    }

    #[test]
    fn ningun_id_choca_con_las_medidas_de_audio() {
        let mut m = Modelo::nuevo();
        registrar(&mut m).unwrap();
        crate::medidas::registrar(&mut m).unwrap();
        assert_eq!(m.len(), TIEMPO.len() + crate::medidas::MEDIDAS.len());
    }

    #[test]
    fn los_nombres_se_leen_sin_haber_visto_el_instrumento() {
        // §2.1: el descriptor es la documentacion del agente. "sabe donde esta
        // el 1" se entiende; "flag_phase_valid" no.
        //
        // El test pedia un espacio y estaba mal: «tempo» es un nombre perfecto
        // y no lo tiene. Lo que de verdad delata a un identificador disfrazado
        // es el guion bajo y las mayusculas.
        for d in TIEMPO.iter() {
            assert!(!d.nombre.is_empty());
            assert!(
                !d.nombre.contains('_'),
                "«{}» parece un identificador, no un nombre",
                d.nombre
            );
            assert!(
                d.nombre.chars().all(|c| !c.is_uppercase()),
                "«{}» lleva mayusculas: no se escribio para leerse",
                d.nombre
            );
            assert!(d.max > d.min, "{} sin rango", d.nombre);
        }
    }
}
