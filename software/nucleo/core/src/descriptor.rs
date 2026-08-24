//! El descriptor (§3.3), sus marcas de medida (§3.4) y su ambito (§3.6),
//! con el codec binario que el micro emite y la carcasa expande a JSON.
//!
//! El formato es de ancho fijo y little-endian a proposito: lo van a parsear
//! el puente inalambrico y JavaScript en la UI web, y un `DataView` tiene que
//! poder leerlo sin librerias.
//!
//! ```text
//!   off  tam  campo
//!    0    4   id (u32)
//!    4    1   banderas
//!               bit0 solo_lectura   bit1 medida   bit2 confirmacion_fisica
//!               bit3 ambito (0 = compartido, 1 = por-voz)
//!               bits 4-5 tipo (0 continuo, 1 enumerado, 2 booleano)
//!               bit6 acepta_modulacion
//!    5    4   min (i32)
//!    9    4   max (i32)
//!   13    4   def (i32)
//!   17    1   unidad
//!   18    1   largo del nombre
//!   19    n   nombre en UTF-8
//!   19+n  1   numero de etiquetas
//!        por etiqueta: 1 byte de largo + los bytes UTF-8
//! ```
//!
//! Esta tabla decia `0 2 id (u16)` y el codec siempre escribio `w.u32`, asi
//! que TODOS los offsets estaban corridos por 2 -- y quien implementara el
//! parser desde este comentario, que es exactamente lo que hara quien escriba
//! la carcasa web, sacaba basura en todos los campos. Es el #182, fallo 2.
//!
//! Ahora la tabla no se cree: la clava `la_tabla_de_arriba_es_la_de_verdad`,
//! que asevera cada offset contra bytes de verdad.

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
    /// §7.3 de la spec del tiempo musical. **Hoy no la usa nadie**: la
    /// modulacion es de la spec 2. Esta puesta porque es un bit ahora contra
    /// reescribir el modelo entero despues.
    pub acepta_modulacion: bool,
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
    pub acepta_modulacion: bool,
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

/// Lo mas que puede ocupar UN descriptor en el cable.
///
/// No es un techo del formato: es el tamano del buffer del volcado en
/// `fw/src/usb.rs`, que lo LEE de aqui en vez de repetir el 256 por su cuenta.
///
/// Y no es un techo blando. `mandar_descriptores` hacia `?` sobre `escribir`,
/// asi que UN solo descriptor pasado se llevaba por delante el volcado ENTERO
/// -- en silencio, y sin que el cliente pudiera distinguir "termino" de "se
/// aborto". Es el #182, fallo 5.
pub const MAX_DESCRIPTOR_B: usize = 256;

/// Cuanto de ese techo se deja ocupar antes de dar la alarma.
///
/// MEDIDO el 2026-08-24, y hay que leer las DOS medidas juntas porque miden
/// poblaciones distintas:
///
/// ```text
///   peor de los 42 COMPILADOS ("cuantizacion global"):  106 B   41 %
///   peor caso DECLARADO (selector de 17 fuentes):       250 B   98 %
/// ```
///
/// El 41 % es cierto y no dice nada: los compilados son los del cerebro, y los
/// que engordan son los de MODULO, que llegan por I2C en tiempo de ejecucion
/// (§3.5) y por definicion ningun test de compilacion los ve. El 250 esta
/// medido con `escribir` en `el_peor_caso_declarado_cabe_en_el_volcado`, y ya
/// pasa esta alarma con cincuenta y ocho bytes de sobra.
///
/// O sea que el 75 % ya no es "mucho antes del acantilado": es un aviso que el
/// caso realista se salto hace rato. Cerrarlo es la decision N4 del pase del
/// nucleo (descriptor troceado contra largo ancho); subir el techo no es el
/// arreglo, es una de las dos ramas de esa decision.
pub const OCUPACION_MAX_B: usize = MAX_DESCRIPTOR_B * 3 / 4;

pub fn escribir(d: &Descriptor, buf: &mut [u8]) -> Result<usize, ErrorCodec> {
    let mut w = Escritor { buf, n: 0 };
    w.u32(d.id.0)?;
    let banderas = (d.solo_lectura as u8)
        | ((d.medida as u8) << 1)
        | ((d.confirmacion_fisica as u8) << 2)
        | ((d.ambito as u8) << 3)
        | ((d.tipo as u8) << 4)
        | ((d.acepta_modulacion as u8) << 6);
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
    let id = ParamId(r.u32()?);
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
            acepta_modulacion: banderas & 0b0100_0000 != 0,
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
    pub fn u32(&mut self, v: u32) -> Result<(), ErrorCodec> {
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
    pub fn u32(&mut self) -> Result<u32, ErrorCodec> {
        Ok(u32::from_le_bytes(self.crudo(4)?.try_into().unwrap()))
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
        acepta_modulacion: false,
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
        acepta_modulacion: false,
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
        acepta_modulacion: false,
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
        assert_eq!(
            consumido, n,
            "el parser tiene que consumir lo que se escribio"
        );
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
        assert!(matches!(
            escribir(&MODO, &mut buf),
            Err(ErrorCodec::SinSitio)
        ));
        let mut ok = [0u8; 256];
        let n = escribir(&MODO, &mut ok).unwrap();
        for corte in 0..n {
            // Cualquier truncamiento tiene que dar error, jamas un parse a medias.
            assert!(
                leer(&ok[..corte]).is_err(),
                "trunco en {corte} y no se quejo"
            );
        }
    }

    #[test]
    fn la_marca_de_modulacion_sobrevive_el_viaje() {
        // §7.3 de la spec del tiempo musical: un bit hoy contra reescribir el
        // modelo en la spec 2. Si se perdiera, no nos enterariamos hasta que
        // la modulacion existiera — y ahi ya seria tarde.
        static D: Descriptor = Descriptor {
            id: ParamId(0x1234),
            nombre: "x",
            tipo: Tipo::Continuo,
            ambito: Ambito::Compartido,
            solo_lectura: false,
            medida: false,
            confirmacion_fisica: false,
            acepta_modulacion: true,
            min: 0,
            max: 100,
            def: 0,
            unidad: Unidad::Hz,
            etiquetas: &[],
        };
        let mut buf = [0u8; 256];
        let n = escribir(&D, &mut buf).unwrap();
        assert!(leer(&buf[..n]).unwrap().0.acepta_modulacion);
        // Y que no se cuele sola en los que no la piden.
        let n = escribir(&CUTOFF, &mut buf).unwrap();
        assert!(!leer(&buf[..n]).unwrap().0.acepta_modulacion);
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

#[cfg(test)]
mod techo_del_volcado {
    use super::{escribir, Ambito, Descriptor, Tipo, Unidad, MAX_DESCRIPTOR_B, OCUPACION_MAX_B};
    use crate::param::ParamId;

    /// Mide un descriptor SIN el techo de por medio.
    ///
    /// El buffer es holgado a proposito. Con uno de `MAX_DESCRIPTOR_B`, el que
    /// no cabe devuelve `SinSitio` y ya: no dice por CUANTO se pasa, que es
    /// justo el numero con el que se decide si se recorta el nombre o si hay
    /// que trocear el descriptor (N4). Un fallo que solo dice "no" no sirve
    /// para tomar la decision que el propio fallo obliga a tomar.
    fn tam(d: &Descriptor) -> usize {
        let mut buf = [0u8; MAX_DESCRIPTOR_B * 4];
        escribir(d, &mut buf)
            .unwrap_or_else(|_| panic!("\"{}\" no cabe ni en 4x el techo", d.nombre))
    }

    /// #182, fallo 5, **y solo sobre los descriptores COMPILADOS**.
    ///
    /// Un descriptor que no quepa en el buffer del volcado no se pierde solo:
    /// se llevaba por delante TODO el volcado, porque `mandar_descriptores`
    /// abortaba el bucle entero. Y como no hay conteo ni terminador en el
    /// protocolo, el cliente no puede distinguir "termino" de "se aborto".
    ///
    /// Lo que esta puerta NO ve, y hay que decirlo aqui porque su nombre viejo
    /// (`ningun_descriptor_...`) prometia lo contrario: los descriptores de
    /// MODULO llegan por I2C en tiempo de ejecucion (§3.5), asi que este
    /// bucle no los tiene delante y no puede tenerlos. Son ademas los gordos,
    /// porque son los de las matrices de 16. Ese caso lo mide
    /// `el_peor_caso_declarado_cabe_en_el_volcado`, aqui abajo, y NO pasa.
    #[test]
    fn ningun_descriptor_compilado_se_acerca_al_techo_del_volcado() {
        for d in crate::tiempo_params::TIEMPO
            .iter()
            .chain(crate::medidas::MEDIDAS.iter())
        {
            let n = tam(d);
            assert!(
                n <= OCUPACION_MAX_B,
                "\"{}\" ocupa {n} B de {MAX_DESCRIPTOR_B} ({:.0}%), y la alarma                  esta en {OCUPACION_MAX_B}. Todavia cabe, pero lo que engorda un                  descriptor son las etiquetas de los enumerados y crecen sin que                  nadie mire: o se recorta, o se decide el troceado (N4)",
                d.nombre,
                n as f32 / MAX_DESCRIPTOR_B as f32 * 100.0
            );
        }
    }

    /// Las 17 fuentes del selector de modulacion del modulo de dieciseis: las
    /// dieciseis del bus mas "sin fuente".
    ///
    /// El 17 no es mio. `hardware/03-vco/check_censo_voz.py:91` lo cita
    /// textualmente de la spec del modulo ("los selectores de fuente son
    /// enumerados de 17"), y §8 de esa spec dice de donde salen: "cada
    /// oscilador elige de cual de los dieciseis come", 16 selectores por
    /// matriz.
    ///
    /// Los nombres son del largo que este repo se exige a si mismo, no cortos
    /// para que la cuenta salga: `tiempo_params.rs` encabeza su tabla con
    /// "Nombres escritos para alguien que nunca ha visto el instrumento", y
    /// §2.1 dice para quien son de verdad -- son la documentacion que lee el
    /// agente. "osc 1" ahorra bytes y le quita al LLM lo unico que tenia.
    const FUENTES: &[&str] = &[
        "sin fuente",
        "oscilador 1",
        "oscilador 2",
        "oscilador 3",
        "oscilador 4",
        "oscilador 5",
        "oscilador 6",
        "oscilador 7",
        "oscilador 8",
        "oscilador 9",
        "oscilador 10",
        "oscilador 11",
        "oscilador 12",
        "oscilador 13",
        "oscilador 14",
        "oscilador 15",
        "oscilador 16",
    ];

    /// El peor caso REALISTA, y es el barato: el nombre no repite de que
    /// oscilador es porque eso ya va en la instancia del `ParamId` (§3.1), y
    /// las etiquetas son las cortas que siguen siendo legibles. Si el diseno
    /// acaba metiendo el numero de oscilador en el nombre, esto crece.
    static SELECTOR_DE_FUENTE: Descriptor = Descriptor {
        // Ranura 3 (el modulo), instancia 5 (el oscilador), indice cualquiera.
        id: ParamId::nuevo(3, 5, 0x20),
        nombre: "fuente de modulacion",
        tipo: Tipo::Enumerado,
        ambito: Ambito::PorVoz,
        solo_lectura: false,
        medida: false,
        confirmacion_fisica: false,
        acepta_modulacion: false,
        min: 0,
        max: 16,
        def: 0,
        unidad: Unidad::Ninguna,
        etiquetas: FUENTES,
    };

    /// **Esta puerta esta en ROJO a proposito y por eso esta `ignore`.** No es
    /// un test a medio escribir: es el resultado, y el resultado es que el
    /// formato de hoy no aguanta el peor caso que el propio repo ya declara.
    ///
    /// MEDIDO el 2026-08-24 con `escribir`, no calculado a mano: el selector
    /// de arriba ocupa **250 B**. El techo del volcado son 256 y la alarma
    /// esta en 192. O sea: entra por seis bytes y revienta la alarma por
    /// cincuenta y ocho. Para comparar, el mas gordo de los 42 compilados son
    /// 106 B ("cuantizacion global") -- el test de arriba mide una poblacion
    /// que nunca iba a tener el problema.
    ///
    /// Seis bytes de margen no son margen: son un nombre un poco mas largo, o
    /// una etiqueta decimoctava, o que el diseno decida poner el numero de
    /// oscilador en el nombre -- " del oscilador 3" son 16 B mas, o sea 266, y
    /// entonces ni `escribir` termina.
    ///
    /// **Que lo desbloquea:** la decision N4 del pase del nucleo, descriptor
    /// troceado contra largo ancho. Mientras N4 no exista no hay nada que
    /// arreglar aqui: subir `MAX_DESCRIPTOR_B` es *elegir* "largo ancho", y
    /// eso es la decision, no el arreglo. Tomada N4, se quita el `ignore` y
    /// esto pasa a verde o se cambia el peor caso que mide.
    #[test]
    #[ignore = "ROJO real, no pendiente: el peor caso declarado (selector de 17 \
                fuentes) mide 250 B contra una alarma de 192. Lo desbloquea la \
                decision N4 del pase del nucleo (descriptor troceado vs largo \
                ancho), no un cambio de codigo."]
    fn el_peor_caso_declarado_cabe_en_el_volcado() {
        let n = tam(&SELECTOR_DE_FUENTE);
        assert!(
            n <= OCUPACION_MAX_B,
            "el selector de {} fuentes ocupa {n} B de {MAX_DESCRIPTOR_B} ({:.0}%),              y la alarma esta en {OCUPACION_MAX_B}. Este descriptor no esta              compilado en el cerebro: llega por I2C desde el modulo, asi que la              otra puerta jamas lo vera. Lo decide N4",
            FUENTES.len(),
            n as f32 / MAX_DESCRIPTOR_B as f32 * 100.0
        );
    }
}

#[cfg(test)]
mod forma_del_cable {
    use super::*;

    /// Un descriptor con TODOS los campos distintos entre si, para que un
    /// offset corrido no pueda pasar desapercibido por casualidad.
    static PIN: Descriptor = Descriptor {
        id: ParamId(0x0A0B_0C0D),
        nombre: "ab",
        tipo: Tipo::Enumerado,
        ambito: Ambito::PorVoz,
        solo_lectura: true,
        medida: false,
        confirmacion_fisica: false,
        acepta_modulacion: true,
        min: -2,
        max: 3,
        def: 1,
        unidad: Unidad::Ninguna,
        etiquetas: &["x"],
    };

    /// La tabla del encabezado de este modulo es la UNICA especificacion
    /// publicada del formato, y su propio texto dice para quien: "lo van a
    /// parsear el puente inalambrico y JavaScript en la UI web, y un
    /// `DataView` tiene que poder leerlo sin librerias".
    ///
    /// Un `DataView` lee por OFFSET. Si la tabla miente, el parser no falla:
    /// devuelve numeros plausibles y equivocados, que es peor. Por eso esto se
    /// asevera byte a byte y NO con un ida y vuelta -- un `escribir` + `leer`
    /// pasa igual de bien con la tabla mintiendo, porque los dos lados
    /// comparten el error. Eso es justo lo que dejo pasar el fallo 2.
    #[test]
    fn la_tabla_de_arriba_es_la_de_verdad() {
        let mut b = [0u8; 64];
        let n = escribir(&PIN, &mut b).unwrap();

        //  0  4  id (u32 LE)
        assert_eq!(
            &b[0..4],
            &[0x0D, 0x0C, 0x0B, 0x0A],
            "id: off 0, cuatro bytes"
        );
        //  4  1  banderas
        //          bit6 modulacion --+
        //   bits 4-5 tipo = 01 enumerado |
        //          bit3 ambito por-voz | |
        //          bit0 solo_lectura | | |
        //                            v v v
        let esperadas = 0b0101_1001; // 1 + 8 + 16 + 64 = 89
        assert_eq!(b[4], esperadas, "banderas: off 4");
        //  5  4  min      9  4  max     13  4  def
        assert_eq!(&b[5..9], &(-2i32).to_le_bytes(), "min: off 5");
        assert_eq!(&b[9..13], &3i32.to_le_bytes(), "max: off 9");
        assert_eq!(&b[13..17], &1i32.to_le_bytes(), "def: off 13");
        // 17  1  unidad
        assert_eq!(b[17], Unidad::Ninguna as u8, "unidad: off 17");
        // 18  1  largo del nombre   19  n  nombre
        assert_eq!(b[18], 2, "largo del nombre: off 18");
        assert_eq!(&b[19..21], b"ab", "nombre: off 19");
        // 19+n  1  numero de etiquetas, y luego largo + bytes
        assert_eq!(b[21], 1, "numero de etiquetas: off 19+n");
        assert_eq!(b[22], 1, "largo de la etiqueta");
        assert_eq!(&b[23..24], b"x", "la etiqueta");
        assert_eq!(n, 24, "el total, que es lo que avanza el sobre");
    }
}
