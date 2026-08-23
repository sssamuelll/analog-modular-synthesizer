//! §4.4. Property Exchange usa SysEx estilo MIDI 1.0, y en SysEx todo byte de
//! datos tiene que ser menor que 0x80. De ahi el empaquetado 7-a-8: por cada
//! grupo de 7 bytes sale uno con los bits altos y siete con los bajos.
//!
//! **Lo que este modulo NO hace.** La conformidad MIDI-CI de verdad —MUID,
//! `ResourceList`, los nombres exactos de la cabecera— va en el plan del
//! binario, y su primer paso es leer el M2-103-UM de la MIDI Association, no
//! escribirlo de memoria. Aqui se usa el ID de fabricante no comercial, que es
//! exactamente para lo que existe, y asi el transporte queda probado sin
//! inventarse un estandar ajeno.

use crate::descriptor::ErrorCodec;

/// ID de fabricante no comercial. Es lo que la MIDI Association reserva para
/// prototipos y uso privado: nada que registrar y nada que chocar.
pub const ID_FABRICANTE_NO_COMERCIAL: u8 = 0x7D;

pub const fn largo_empaquetado(n: usize) -> usize {
    n + n.div_ceil(7)
}

pub fn empaquetar(entrada: &[u8], salida: &mut [u8]) -> Result<usize, ErrorCodec> {
    if salida.len() < largo_empaquetado(entrada.len()) {
        return Err(ErrorCodec::SinSitio);
    }
    let mut o = 0;
    for grupo in entrada.chunks(7) {
        let altos = grupo
            .iter()
            .enumerate()
            .fold(0u8, |acc, (i, b)| acc | ((b >> 7) << i));
        salida[o] = altos;
        o += 1;
        for b in grupo {
            salida[o] = b & 0x7F;
            o += 1;
        }
    }
    Ok(o)
}

pub fn desempaquetar(entrada: &[u8], salida: &mut [u8]) -> Result<usize, ErrorCodec> {
    let mut o = 0;
    for grupo in entrada.chunks(8) {
        // Un grupo de un solo byte es basura: hay cabecera de bits altos y
        // ningun dato al que pertenezca.
        if grupo.len() < 2 {
            return Err(ErrorCodec::Invalido);
        }
        let altos = grupo[0];
        if altos & 0x80 != 0 {
            return Err(ErrorCodec::Invalido);
        }
        for (i, b) in grupo[1..].iter().enumerate() {
            if b & 0x80 != 0 {
                return Err(ErrorCodec::Invalido);
            }
            *salida.get_mut(o).ok_or(ErrorCodec::SinSitio)? = b | (((altos >> i) & 1) << 7);
            o += 1;
        }
    }
    Ok(o)
}

/// `F0 7D <datos empaquetados> F7`.
pub fn envolver(datos: &[u8], salida: &mut [u8]) -> Result<usize, ErrorCodec> {
    *salida.first_mut().ok_or(ErrorCodec::SinSitio)? = 0xF0;
    *salida.get_mut(1).ok_or(ErrorCodec::SinSitio)? = ID_FABRICANTE_NO_COMERCIAL;
    let n = empaquetar(datos, salida.get_mut(2..).ok_or(ErrorCodec::SinSitio)?)?;
    *salida.get_mut(2 + n).ok_or(ErrorCodec::SinSitio)? = 0xF7;
    Ok(3 + n)
}

pub fn desenvolver(sobre: &[u8], salida: &mut [u8]) -> Result<usize, ErrorCodec> {
    if sobre.len() < 3 || sobre[0] != 0xF0 || sobre[sobre.len() - 1] != 0xF7 {
        return Err(ErrorCodec::Invalido);
    }
    if sobre[1] != ID_FABRICANTE_NO_COMERCIAL {
        return Err(ErrorCodec::Invalido);
    }
    desempaquetar(&sobre[2..sobre.len() - 1], salida)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn patron(n: usize) -> heapless::Vec<u8, 512> {
        (0..n)
            .map(|i| (i as u8).wrapping_mul(37).wrapping_add(0x80))
            .collect()
    }

    #[test]
    fn ida_y_vuelta_para_todo_largo_que_nos_importa() {
        let mut emp = [0u8; 640];
        let mut des = [0u8; 512];
        for n in 0..=256usize {
            let datos = patron(n);
            let e = empaquetar(&datos, &mut emp).unwrap();
            assert_eq!(e, largo_empaquetado(n));
            assert!(
                emp[..e].iter().all(|b| *b < 0x80),
                "un byte de SysEx con el bit alto, n={n}"
            );
            let d = desempaquetar(&emp[..e], &mut des).unwrap();
            assert_eq!(&des[..d], datos.as_slice(), "no volvio igual con n={n}");
        }
    }

    #[test]
    fn el_descriptor_completo_viaja_en_sysex_y_vuelve_identico() {
        // §9, fila "Property Exchange sobre MIDI 1.0". Sin UMP de por medio.
        use crate::descriptor::*;
        use crate::param::ParamId;
        static D: Descriptor = Descriptor {
            id: ParamId::nuevo(5, 1, 3),
            nombre: "resonancia del filtro",
            tipo: Tipo::Continuo,
            ambito: Ambito::PorVoz,
            solo_lectura: false,
            medida: false,
            confirmacion_fisica: false,
            acepta_modulacion: false,
            min: 0,
            max: 65535,
            def: 0,
            unidad: Unidad::Milesimas,
            etiquetas: &[],
        };
        let mut plano = [0u8; 256];
        let n = escribir(&D, &mut plano).unwrap();

        let mut sobre = [0u8; 512];
        let s = envolver(&plano[..n], &mut sobre).unwrap();
        assert_eq!(sobre[0], 0xF0);
        assert_eq!(sobre[1], ID_FABRICANTE_NO_COMERCIAL);
        assert_eq!(sobre[s - 1], 0xF7);
        assert!(sobre[1..s - 1].iter().all(|b| *b < 0x80));

        let mut vuelta = [0u8; 256];
        let v = desenvolver(&sobre[..s], &mut vuelta).unwrap();
        assert_eq!(&vuelta[..v], &plano[..n]);
        let (leido, _) = leer(&vuelta[..v]).unwrap();
        assert_eq!(leido.nombre, D.nombre);
        assert_eq!(leido.ambito, D.ambito);
    }

    #[test]
    fn un_sobre_roto_se_rechaza() {
        let mut buf = [0u8; 64];
        assert!(desenvolver(&[0xF0, 0x7D, 0x00], &mut buf).is_err()); // sin F7
        assert!(desenvolver(&[0x00, 0x7D, 0xF7], &mut buf).is_err()); // sin F0
        assert!(desenvolver(&[0xF0, 0x01, 0x00, 0xF7], &mut buf).is_err()); // otro fabricante
    }

    #[test]
    fn un_byte_con_el_bit_alto_dentro_del_sobre_no_se_traga() {
        // Si esto pasara, un byte de estado de MIDI se colaria como dato.
        let mut buf = [0u8; 64];
        assert_eq!(
            desempaquetar(&[0x00, 0x41, 0xC0], &mut buf),
            Err(ErrorCodec::Invalido)
        );
        assert_eq!(
            desempaquetar(&[0x80, 0x41], &mut buf),
            Err(ErrorCodec::Invalido)
        );
    }

    #[test]
    fn el_buffer_de_salida_corto_se_queja() {
        let mut corto = [0u8; 4];
        assert_eq!(
            empaquetar(&patron(32), &mut corto),
            Err(ErrorCodec::SinSitio)
        );
    }
}
