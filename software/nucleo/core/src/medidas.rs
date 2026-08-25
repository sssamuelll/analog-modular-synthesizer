//! §7.3. Una FFT cruda **no puede contestar «hay muchos graves»**: en
//! cualquier espectro crudo la energia de graves es siempre mayor, asi es la
//! musica. La pregunta es perceptual, no espectral.
//!
//! | El objetivo | Lo que lo contesta |
//! |---|---|
//! | «demasiado grave» | bandas ponderadas perceptualmente (Bark) con sonoridad estilo ITU-R BS.1770 |
//! | «una frecuencia por encima de las demas» | deteccion de resonancia contra la envolvente espectral suavizada |
//!
//! Todo esto son **parametros de medida** en el sentido de §3.4: solo lectura,
//! con unidad y rango, leidos con `GET` y seguidos con `SUBSCRIBE`. El agente
//! no necesita saber que existe un motor de analisis; solo lee parametros.
//!
//! Los numeros llegan del **modulo 4** por el J2 (§7.4). Por el cableado
//! viajan numeros, no voltajes: el cerebro no tiene entrada de audio.

use crate::descriptor::{Ambito, Descriptor, Tipo, Unidad};
use crate::modelo::Modelo;
use crate::param::ParamId;
use crate::politica::Puerta;

/// Las 24 bandas criticas de Bark.
pub const N_BANDAS: usize = 24;

const IDX_BANDA_0: u8 = 0x80;
const IDX_PICO_HZ: u8 = 0xA0;
const IDX_PICO_EXCESO: u8 = 0xA1;
const IDX_SONORIDAD: u8 = 0xA2;

/// Las medidas son del instrumento entero, asi que viven en la parte `0` de la
/// ranura del cerebro.
pub const fn id_banda(n: usize) -> ParamId {
    ParamId::nuevo(0, 0, IDX_BANDA_0 + n as u8)
}
pub const ID_PICO_HZ: ParamId = ParamId::nuevo(0, 0, IDX_PICO_HZ);
pub const ID_PICO_EXCESO: ParamId = ParamId::nuevo(0, 0, IDX_PICO_EXCESO);
pub const ID_SONORIDAD: ParamId = ParamId::nuevo(0, 0, IDX_SONORIDAD);

/// Bordes superiores de las bandas de Bark, en Hz. Solo se usan para escribir
/// nombres que un LLM pueda entender sin haber visto el instrumento (§2.1).
const BORDES_BARK: [u16; N_BANDAS] = [
    100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480, 1720, 2000, 2320, 2700, 3150, 3700,
    4400, 5300, 6400, 7700, 9500, 12000, 15500,
];

const fn banda(n: usize) -> Descriptor {
    Descriptor {
        id: id_banda(n),
        nombre: NOMBRES_BANDA[n],
        tipo: Tipo::Continuo,
        ambito: Ambito::Compartido,
        solo_lectura: true,
        medida: true,
        confirmacion_fisica: false,
        acepta_modulacion: false,
        min: -60_000,
        max: 0,
        def: -60_000,
        unidad: Unidad::MilidB,
        etiquetas: &[],
    }
}

/// Un nombre por banda, escrito para alguien que nunca ha visto el
/// instrumento. Se generan a mano porque `format!` no existe en `no_std`.
const NOMBRES_BANDA: [&str; N_BANDAS] = [
    "sonoridad 0-100 Hz (sub)",
    "sonoridad 100-200 Hz (grave)",
    "sonoridad 200-300 Hz (grave)",
    "sonoridad 300-400 Hz (grave-medio)",
    "sonoridad 400-510 Hz (grave-medio)",
    "sonoridad 510-630 Hz (medio)",
    "sonoridad 630-770 Hz (medio)",
    "sonoridad 770-920 Hz (medio)",
    "sonoridad 920-1080 Hz (medio)",
    "sonoridad 1080-1270 Hz (medio)",
    "sonoridad 1270-1480 Hz (medio-agudo)",
    "sonoridad 1480-1720 Hz (medio-agudo)",
    "sonoridad 1720-2000 Hz (presencia)",
    "sonoridad 2000-2320 Hz (presencia)",
    "sonoridad 2320-2700 Hz (presencia)",
    "sonoridad 2700-3150 Hz (presencia)",
    "sonoridad 3150-3700 Hz (brillo)",
    "sonoridad 3700-4400 Hz (brillo)",
    "sonoridad 4400-5300 Hz (brillo)",
    "sonoridad 5300-6400 Hz (brillo)",
    "sonoridad 6400-7700 Hz (aire)",
    "sonoridad 7700-9500 Hz (aire)",
    "sonoridad 9500-12000 Hz (aire)",
    "sonoridad 12000-15500 Hz (aire)",
];

const OTRAS: [Descriptor; 3] = [
    Descriptor {
        id: ID_PICO_HZ,
        nombre: "frecuencia del pico que sobresale",
        tipo: Tipo::Continuo,
        ambito: Ambito::Compartido,
        solo_lectura: true,
        medida: true,
        confirmacion_fisica: false,
        acepta_modulacion: false,
        min: 0,
        max: 20_000,
        def: 0,
        unidad: Unidad::Hz,
        etiquetas: &[],
    },
    Descriptor {
        id: ID_PICO_EXCESO,
        nombre: "cuanto sobresale ese pico de la envolvente",
        tipo: Tipo::Continuo,
        ambito: Ambito::Compartido,
        solo_lectura: true,
        medida: true,
        confirmacion_fisica: false,
        acepta_modulacion: false,
        min: 0,
        max: 40_000,
        def: 0,
        unidad: Unidad::MilidB,
        etiquetas: &[],
    },
    Descriptor {
        id: ID_SONORIDAD,
        nombre: "sonoridad percibida de la mezcla",
        tipo: Tipo::Continuo,
        ambito: Ambito::Compartido,
        solo_lectura: true,
        medida: true,
        confirmacion_fisica: false,
        acepta_modulacion: false,
        min: -60_000,
        max: 0,
        def: -60_000,
        unidad: Unidad::MilidB,
        etiquetas: &[],
    },
];

/// Construye la tabla completa en tiempo de compilacion.
const fn tabla() -> [Descriptor; N_BANDAS + 3] {
    let mut t = [OTRAS[0]; N_BANDAS + 3];
    let mut i = 0;
    while i < N_BANDAS {
        t[i] = banda(i);
        i += 1;
    }
    t[N_BANDAS] = OTRAS[0];
    t[N_BANDAS + 1] = OTRAS[1];
    t[N_BANDAS + 2] = OTRAS[2];
    t
}

pub static MEDIDAS: [Descriptor; N_BANDAS + 3] = tabla();

/// Lo que el modulo 4 manda por el J2. Numeros, nunca audio (§5.0).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct TramaMedida {
    pub bandas: [i32; N_BANDAS],
    pub pico_hz: i32,
    pub pico_exceso_mdb: i32,
    pub sonoridad_mdb: i32,
}

impl Default for TramaMedida {
    fn default() -> Self {
        TramaMedida {
            bandas: [-60_000; N_BANDAS],
            pico_hz: 0,
            pico_exceso_mdb: 0,
            sonoridad_mdb: -60_000,
        }
    }
}

/// Registra las medidas en un modelo. Se llama una vez al descubrir.
pub fn registrar(m: &mut Modelo) -> Result<(), crate::modelo::ErrorRegistro> {
    for d in MEDIDAS.iter() {
        m.registrar(d)?;
    }
    Ok(())
}

/// Mete la trama del modulo 4 en el modelo, por el unico camino que escribe
/// una medida (§3.4).
///
/// Aqui **si** se recorta al rango, y por eso es distinto de un `SET`: no es
/// la intencion de nadie, es un sensor. Tirar la trama entera porque un
/// sensor se salio de escala seria peor que recortar.
pub fn ingerir(m: &mut Modelo, t: &TramaMedida, puerta: Puerta) {
    for (n, v) in t.bandas.iter().enumerate() {
        publicar(m, id_banda(n), *v, puerta);
    }
    publicar(m, ID_PICO_HZ, t.pico_hz, puerta);
    publicar(m, ID_PICO_EXCESO, t.pico_exceso_mdb, puerta);
    publicar(m, ID_SONORIDAD, t.sonoridad_mdb, puerta);
}

fn publicar(m: &mut Modelo, id: ParamId, v: i32, puerta: Puerta) {
    let Some(d) = m.descriptor_de(id) else { return };
    let _ = m.publicar_medida(id, v.clamp(d.min, d.max), puerta);
}

/// El borde superior de la banda `n`, en Hz. Para quien tenga que dibujarlas.
pub const fn borde_bark(n: usize) -> u16 {
    BORDES_BARK[n]
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::modelo::{ErrorSet, Modelo};

    fn instrumento() -> Modelo {
        let mut m = Modelo::nuevo();
        registrar(&mut m).unwrap();
        m
    }

    #[test]
    fn lo_que_manda_el_modulo_4_sale_por_get() {
        // §9, fila "Medidas por el J2": bandas y picos sinteticos, como si
        // vinieran de la placa que aun no existe.
        let mut m = instrumento();
        let t = TramaMedida {
            bandas: {
                let mut b = [-60_000; N_BANDAS];
                b[0] = -3_000;
                b[23] = -41_000;
                b
            },
            pico_hz: 1_240,
            pico_exceso_mdb: 9_500,
            sonoridad_mdb: -14_000,
        };
        ingerir(&mut m, &t, Puerta::Interno);

        assert_eq!(m.get(id_banda(0)), Some(-3_000));
        assert_eq!(m.get(id_banda(23)), Some(-41_000));
        assert_eq!(m.get(ID_PICO_HZ), Some(1_240));
        assert_eq!(m.get(ID_PICO_EXCESO), Some(9_500));
        assert_eq!(m.get(ID_SONORIDAD), Some(-14_000));
    }

    #[test]
    fn ningun_cliente_puede_escribirlas() {
        let mut m = instrumento();
        assert_eq!(
            m.set(ID_PICO_HZ, 100, Puerta::Usb),
            Err(ErrorSet::SoloLectura)
        );
        assert_eq!(
            m.set(id_banda(5), 0, Puerta::Usb),
            Err(ErrorSet::SoloLectura)
        );
    }

    #[test]
    fn todas_traen_unidad_y_rango_para_que_el_agente_las_entienda() {
        // §2.1: nombres y unidades son documentacion, no cosmetica.
        let m = instrumento();
        for d in MEDIDAS.iter() {
            assert!(d.medida && d.solo_lectura, "{}", d.nombre);
            assert_ne!(d.unidad, Unidad::Ninguna, "{} sin unidad", d.nombre);
            assert!(d.max > d.min, "{} sin rango", d.nombre);
            assert!(!d.nombre.is_empty());
            assert!(m.get(d.id).is_some(), "{} no quedo registrada", d.nombre);
        }
        assert_eq!(MEDIDAS.len(), N_BANDAS + 3);
        assert_eq!(m.len(), N_BANDAS + 3);
    }

    #[test]
    fn ningun_id_se_repite() {
        // Si dos medidas compartieran id, `registrar` daria Duplicado y una
        // de las dos no existiria — el agente leeria la equivocada.
        let mut ids: heapless::Vec<u32, { N_BANDAS + 3 }> =
            MEDIDAS.iter().map(|d| d.id.0).collect();
        ids.sort_unstable();
        assert!(
            ids.windows(2).all(|p| p[0] != p[1]),
            "hay dos medidas con el mismo id: {ids:?}"
        );
    }

    #[test]
    fn una_medida_fuera_de_rango_se_recorta_en_vez_de_tirar_la_trama() {
        // Aqui SI se recorta, y por eso es distinto de un SET: no es la
        // intencion de nadie, es un sensor.
        let mut m = instrumento();
        let t = TramaMedida {
            pico_hz: 999_999,
            ..Default::default()
        };
        ingerir(&mut m, &t, Puerta::Interno);
        let d = MEDIDAS.iter().find(|d| d.id == ID_PICO_HZ).unwrap();
        assert_eq!(m.get(ID_PICO_HZ), Some(d.max));
    }

    #[test]
    fn los_nombres_le_dicen_al_agente_donde_esta_cada_banda() {
        // "sonoridad 100-200 Hz (grave)" es legible sin haber visto el sinte;
        // "banda 1" no lo seria.
        for (n, d) in MEDIDAS.iter().take(N_BANDAS).enumerate() {
            assert!(d.nombre.contains("Hz"), "banda {n}: {}", d.nombre);
        }
        assert_eq!(borde_bark(0), 100);
        assert_eq!(borde_bark(N_BANDAS - 1), 15_500);
    }
}
