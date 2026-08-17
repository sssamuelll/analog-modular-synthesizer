//! El troceo de USB-MIDI 1.0.
//!
//! `embassy_usb::class::midi` es *packet level*: mueve **paquetes de 4 bytes**,
//! no bytes sueltos. Asi que el SysEx que `crate::sysex` sabe construir hay que
//! trocearlo con los codigos que manda USB-MIDI, y recomponerlo al volver.
//!
//! Es formato puro, asi que **se prueba entero sin placa** — y es justo la
//! pieza que si se hace a ojo se descubre rota con un analizador logico.
//!
//! El byte 0 del paquete es `(cable << 4) | CIN`:
//!
//! | CIN | Que es | Bytes utiles |
//! |---|---|---|
//! | `0x4` | SysEx empieza o continua | 3 |
//! | `0x5` | SysEx acaba con **un** byte | 1 |
//! | `0x6` | SysEx acaba con **dos** | 2 |
//! | `0x7` | SysEx acaba con **tres** | 3 |

use crate::descriptor::ErrorCodec;
use heapless::Vec;

/// El SysEx mas gordo que esperamos: el volcado del descriptor cabe de sobra.
pub const MAX_SYSEX: usize = 512;

pub const CIN_SYSEX_SIGUE: u8 = 0x4;
pub const CIN_SYSEX_FIN_1: u8 = 0x5;
pub const CIN_SYSEX_FIN_2: u8 = 0x6;
pub const CIN_SYSEX_FIN_3: u8 = 0x7;

/// Un paquete de USB-MIDI: siempre cuatro bytes.
pub type Paquete = [u8; 4];

/// Lo que sale del cable, ya clasificado.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Trozo<'a> {
    /// Un SysEx completo, del `F0` al `F7`.
    Sysex(&'a [u8]),
    /// Un mensaje de canal o de sistema de tres bytes: notas, CC, pitch bend.
    Midi([u8; 3]),
}

/// Trocea un SysEx en paquetes. Devuelve cuantos escribio.
pub fn empaquetar_sysex(msg: &[u8], salida: &mut [Paquete]) -> Result<usize, ErrorCodec> {
    empaquetar_sysex_en_cable(msg, 0, salida)
}

pub fn empaquetar_sysex_en_cable(
    msg: &[u8],
    cable: u8,
    salida: &mut [Paquete],
) -> Result<usize, ErrorCodec> {
    let alto = (cable & 0x0F) << 4;
    let mut o = 0;
    let mut resto = msg;
    while !resto.is_empty() {
        let hueco = salida.get_mut(o).ok_or(ErrorCodec::SinSitio)?;
        // Mas de tres: es continuacion. Exactamente tres o menos: es el final,
        // y el CIN dice cuantos bytes valen. Aqui es donde se rompen las
        // implementaciones hechas a ojo.
        let (cin, n) = match resto.len() {
            1 => (CIN_SYSEX_FIN_1, 1),
            2 => (CIN_SYSEX_FIN_2, 2),
            3 => (CIN_SYSEX_FIN_3, 3),
            _ => (CIN_SYSEX_SIGUE, 3),
        };
        // El relleno va a cero: un byte de basura ahi es un byte de MIDI
        // inventado en el cable.
        *hueco = [alto | cin, 0, 0, 0];
        hueco[1..1 + n].copy_from_slice(&resto[..n]);
        resto = &resto[n..];
        o += 1;
    }
    Ok(o)
}

/// Cuantos paquetes hacen falta para un SysEx de `n` bytes.
pub const fn paquetes_para(n: usize) -> usize {
    n.div_ceil(3)
}

/// Recompone lo que llega del cable.
pub struct Desempaquetador {
    buf: Vec<u8, MAX_SYSEX>,
    /// El mensaje en curso no cabe. Se sigue leyendo para no envenenar el
    /// siguiente, pero no se entrega nada.
    desbordado: bool,
}

impl Default for Desempaquetador {
    fn default() -> Self {
        Self::nuevo()
    }
}

impl Desempaquetador {
    pub const fn nuevo() -> Self {
        Desempaquetador { buf: Vec::new(), desbordado: false }
    }

    /// Mete un paquete. Devuelve algo solo cuando se completa un mensaje.
    pub fn empujar(&mut self, p: &Paquete) -> Option<Trozo<'_>> {
        let cin = p[0] & 0x0F;
        let n = match cin {
            CIN_SYSEX_SIGUE => 3,
            CIN_SYSEX_FIN_1 => 1,
            CIN_SYSEX_FIN_2 => 2,
            CIN_SYSEX_FIN_3 => 3,
            // Todo lo demas es un mensaje de canal o de sistema. No toca el
            // buffer de SysEx: un CC en medio de un volcado es legal.
            0x8..=0xE => return Some(Trozo::Midi([p[1], p[2], p[3]])),
            _ => return None,
        };

        for b in &p[1..1 + n] {
            // Un F0 arranca mensaje: limpia lo que hubiera a medias.
            if *b == 0xF0 {
                self.buf.clear();
                self.desbordado = false;
            }
            if self.buf.push(*b).is_err() {
                self.desbordado = true;
            }
        }

        if cin == CIN_SYSEX_SIGUE {
            return None;
        }
        // Se acabo el mensaje. Si no cupo, se tira entero: medio mensaje
        // envenenaria el siguiente.
        if self.desbordado {
            self.buf.clear();
            self.desbordado = false;
            return None;
        }
        Some(Trozo::Sysex(&self.buf))
    }

    /// Tirar lo que haya a medias, por ejemplo al reconectar el USB.
    pub fn reiniciar(&mut self) {
        self.buf.clear();
        self.desbordado = false;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sysex(n: usize) -> Vec<u8, MAX_SYSEX> {
        let mut v = Vec::new();
        v.push(0xF0).unwrap();
        for i in 0..n {
            v.push((i as u8) & 0x7F).unwrap();
        }
        v.push(0xF7).unwrap();
        v
    }

    /// Manda un mensaje entero por el cable y devuelve lo que salio del otro lado.
    fn ida_y_vuelta(msg: &[u8]) -> Option<Vec<u8, MAX_SYSEX>> {
        let mut paquetes = [[0u8; 4]; 200];
        let np = empaquetar_sysex(msg, &mut paquetes).unwrap();
        assert_eq!(np, paquetes_para(msg.len()));
        let mut d = Desempaquetador::nuevo();
        let mut salida = None;
        for p in &paquetes[..np] {
            if let Some(Trozo::Sysex(bytes)) = d.empujar(p) {
                salida = Some(Vec::from_slice(bytes).unwrap());
            }
        }
        salida
    }

    #[test]
    fn todo_sysex_se_trocea_y_se_recompone_igual() {
        // El largo importa: el ultimo paquete cambia de CIN segun cuantos
        // bytes sobren, y ahi es donde se rompen las implementaciones a ojo.
        for n in 0..=180usize {
            let msg = sysex(n);
            assert_eq!(
                ida_y_vuelta(&msg).as_deref(),
                Some(msg.as_slice()),
                "se rompio con n={n}"
            );
        }
    }

    #[test]
    fn el_ultimo_paquete_lleva_el_cin_que_toca() {
        let mut p = [[0u8; 4]; 16];
        // 3 bytes en total (F0 xx F7): un solo paquete, acaba con tres.
        let n = empaquetar_sysex(&sysex(1), &mut p).unwrap();
        assert_eq!(n, 1);
        assert_eq!(p[0][0] & 0x0F, CIN_SYSEX_FIN_3);
        // 4 bytes: uno de continuacion y uno que acaba con uno.
        let n = empaquetar_sysex(&sysex(2), &mut p).unwrap();
        assert_eq!(n, 2);
        assert_eq!(p[0][0] & 0x0F, CIN_SYSEX_SIGUE);
        assert_eq!(p[1][0] & 0x0F, CIN_SYSEX_FIN_1);
        // 5 bytes: continuacion y acaba con dos.
        let n = empaquetar_sysex(&sysex(3), &mut p).unwrap();
        assert_eq!(p[n - 1][0] & 0x0F, CIN_SYSEX_FIN_2);
    }

    #[test]
    fn el_relleno_de_los_paquetes_cortos_va_a_cero() {
        // Un byte de basura ahi es un byte de MIDI inventado en el cable.
        let mut p = [[0u8; 4]; 16];
        let n = empaquetar_sysex(&sysex(2), &mut p).unwrap();
        assert_eq!(p[n - 1][2..], [0, 0]);
    }

    #[test]
    fn el_numero_de_cable_va_en_el_nibble_alto() {
        let mut p = [[0u8; 4]; 16];
        let n = empaquetar_sysex_en_cable(&sysex(7), 3, &mut p).unwrap();
        for q in &p[..n] {
            assert_eq!(q[0] >> 4, 3);
        }
    }

    #[test]
    fn una_nota_no_se_confunde_con_un_sysex() {
        let mut d = Desempaquetador::nuevo();
        // CIN 0x9 = note on.
        match d.empujar(&[0x09, 0x90, 60, 100]) {
            Some(Trozo::Midi(m)) => assert_eq!(m, [0x90, 60, 100]),
            otro => panic!("una nota tiene que salir como nota: {otro:?}"),
        }
    }

    #[test]
    fn una_nota_en_medio_de_un_volcado_no_lo_rompe() {
        // Es legal y pasa: el DAW manda notas mientras el descriptor viaja.
        let msg = sysex(10);
        let mut paquetes = [[0u8; 4]; 16];
        let np = empaquetar_sysex(&msg, &mut paquetes).unwrap();
        let mut d = Desempaquetador::nuevo();
        let mut salida = None;
        for (i, p) in paquetes[..np].iter().enumerate() {
            if i == 1 {
                assert!(matches!(d.empujar(&[0x09, 0x90, 64, 90]), Some(Trozo::Midi(_))));
            }
            if let Some(Trozo::Sysex(b)) = d.empujar(p) {
                salida = Some(Vec::<u8, MAX_SYSEX>::from_slice(b).unwrap());
            }
        }
        assert_eq!(salida.as_deref(), Some(msg.as_slice()));
    }

    #[test]
    fn un_sysex_a_medias_no_entrega_nada() {
        let mut d = Desempaquetador::nuevo();
        assert!(d.empujar(&[0x04, 0xF0, 0x7D, 0x01]).is_none());
        assert!(d.empujar(&[0x04, 0x02, 0x03, 0x04]).is_none());
    }

    #[test]
    fn un_sysex_mas_largo_que_el_buffer_se_tira_entero_y_se_sigue() {
        // No puede quedar medio mensaje envenenando el siguiente.
        let mut d = Desempaquetador::nuevo();
        d.empujar(&[0x04, 0xF0, 1, 2]);
        for _ in 0..(MAX_SYSEX / 3 + 4) {
            d.empujar(&[0x04, 1, 2, 3]);
        }
        assert!(d.empujar(&[0x05, 0xF7, 0, 0]).is_none(), "no puede entregar basura");

        // Y despues de eso el siguiente mensaje bueno tiene que salir bien.
        let msg = sysex(4);
        let mut p = [[0u8; 4]; 16];
        let n = empaquetar_sysex(&msg, &mut p).unwrap();
        let mut ok = None;
        for q in &p[..n] {
            if let Some(Trozo::Sysex(b)) = d.empujar(q) {
                ok = Some(Vec::<u8, MAX_SYSEX>::from_slice(b).unwrap());
            }
        }
        assert_eq!(ok.as_deref(), Some(msg.as_slice()));
    }

    #[test]
    fn si_no_caben_los_paquetes_se_dice_en_vez_de_truncar() {
        let mut p = [[0u8; 4]; 2];
        assert_eq!(empaquetar_sysex(&sysex(40), &mut p), Err(ErrorCodec::SinSitio));
    }

    #[test]
    fn el_sobre_de_verdad_da_la_vuelta_entero() {
        // El camino completo: descriptor -> binario -> 7 bits -> sobre ->
        // paquetes USB -> y de vuelta. Es lo que va a pasar en el cable.
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
            min: 0,
            max: 65535,
            def: 0,
            unidad: Unidad::Milesimas,
            etiquetas: &[],
        };
        let mut plano = [0u8; 256];
        let n = escribir(&D, &mut plano).unwrap();
        let mut sobre = [0u8; 512];
        let s = crate::sysex::envolver(&plano[..n], &mut sobre).unwrap();

        let vuelta = ida_y_vuelta(&sobre[..s]).expect("tenia que llegar entero");
        let mut plano2 = [0u8; 256];
        let n2 = crate::sysex::desenvolver(&vuelta, &mut plano2).unwrap();
        let (leido, _) = leer(&plano2[..n2]).unwrap();
        assert_eq!(leido.nombre, D.nombre);
        assert_eq!(leido.ambito, D.ambito);
    }
}
