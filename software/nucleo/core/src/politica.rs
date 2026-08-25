//! N1 y N2: por donde entro una escritura, y la tabla que decide si pasa.
//!
//! **El campo NO viaja en el mensaje. Lo estampa el transporte que lo
//! recibio.** Un cliente no puede mentir sobre por donde entro porque no hay
//! campo que falsificar, y cuesta cero bytes en el cable: el formato del
//! protocolo no cambia por esto.
//!
//! Y no es una particion de «quien». `Usb` mezcla al agente por MCP con
//! cualquier carcasa web, y lo dice en el nombre: hoy entran por el mismo par
//! de jacks (`usb.rs`, `MidiClass::new(.., 1, 1, ..)`) y son indistinguibles.
//! El dia que el nibble de cable de USB-MIDI se lea de verdad (#182, fallo 7)
//! se separan sin rehacer nada -- es anadir variantes.

use crate::protocolo::etiqueta_de;
use crate::protocolo::Mensaje;
use heapless::Vec;

/// Por donde entro. Sin payload a proposito: la v2 le colgaba un `u8` a
/// `Inalambrica` llamandolo «la suscripcion», y es un error de eje. La puerta
/// de entrada y el encaminamiento de salida son dos ejes distintos: saber por
/// donde entro algo no dice a donde va la respuesta. Esa es N5, y va con #145.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum Puerta {
    /// Panel de mandos, encoder de la cabeza, pulsador, pedal.
    Mano = 0,
    /// El agente por MCP **y** cualquier carcasa. Hoy no se separan.
    Usb = 1,
    /// Carcasa por el puente inalambrico.
    Inalambrica = 2,
    /// El tick y las rampas. Llamada interna, no entra por ningun cable.
    Interno = 3,
}

impl Puerta {
    pub const TODAS: [Puerta; 4] = [
        Puerta::Mano,
        Puerta::Usb,
        Puerta::Inalambrica,
        Puerta::Interno,
    ];
}

/// Cuatro puertas por las quince etiquetas de cliente (`0x01..=0x0F`). Una
/// tabla llena es el techo, y el techo es chico a proposito: si hiciera falta
/// mas es que alguien esta escribiendo un ACL por parametro, que es justo lo
/// que este pase NO construye.
pub const MAX_REGLAS: usize = 60;

/// Una fila. La clave es `(puerta, etiqueta)` -- N2a: se legisla sobre la
/// **etiqueta del mensaje**, que es la unica clave que existe hoy.
///
/// N2b, dicho en voz alta porque es una limitacion de verdad: `Set` es UNA
/// etiqueta sobre los 536 parametros, asi que una regla sobre `Set` no
/// distingue afinar un VCO de borrar la configuracion del cerebro. La salida
/// barata, si algun caso real la pide, es derivar de `ParamId::ranura()`.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Regla {
    pub puerta: Puerta,
    pub etiqueta: u8,
    pub permitido: bool,
}

/// La tabla. **Vacia por defecto, y vacia significa todo abierto.**
#[derive(Default)]
pub struct Politica {
    reglas: Vec<Regla, MAX_REGLAS>,
}

impl Politica {
    pub const fn nueva() -> Self {
        Self { reglas: Vec::new() }
    }

    /// Mete una fila. Si ya habia una para la misma `(puerta, etiqueta)`, la
    /// **reemplaza**: una tabla que llega de la flash con la clave repetida
    /// se aplicaria a medias segun el orden, y eso es un modo que hace una
    /// cosa distinta cada vez que se guarda.
    ///
    /// Devuelve la regla que NO cupo, en vez de tragarsela en silencio.
    pub fn cargar(&mut self, r: Regla) -> Result<(), Regla> {
        match self
            .reglas
            .iter_mut()
            .find(|x| x.puerta == r.puerta && x.etiqueta == r.etiqueta)
        {
            Some(x) => {
                *x = r;
                Ok(())
            }
            None => self.reglas.push(r),
        }
    }

    pub fn vacia(&self) -> bool {
        self.reglas.is_empty()
    }

    /// Sin fila, pasa. **Vacia = todo abierto**, que es lo que Samuel
    /// decidio: por defecto va a dar acceso total, y una tabla vacia que
    /// negara seria un ladrillo la primera vez que arranca.
    ///
    /// Y por eso mismo el estado de la tabla tiene que ser LEGIBLE desde
    /// fuera (N6): si no, un CRC malo o una ranura trabada dan acceso total
    /// y silencioso, indistinguible del estado de fabrica.
    pub fn permite(&self, puerta: Puerta, etiqueta: u8) -> bool {
        match self
            .reglas
            .iter()
            .find(|r| r.puerta == puerta && r.etiqueta == etiqueta)
        {
            Some(r) => r.permitido,
            None => true,
        }
    }

    pub fn permite_mensaje(&self, puerta: Puerta, m: &Mensaje) -> bool {
        self.permite(puerta, etiqueta_de(m))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::param::ParamId;

    const T_SET: u8 = 0x04;
    const T_MEMO: u8 = 0x0D;

    /// Lo que Samuel decidio: por defecto esta vacia, porque va a dar acceso
    /// total. Una tabla vacia que negara seria un instrumento de ladrillo la
    /// primera vez que arranca.
    #[test]
    fn la_tabla_vacia_deja_pasar_todo() {
        let p = Politica::nueva();
        assert!(p.vacia());
        for puerta in Puerta::TODAS {
            for etiqueta in 0x01..=0x0F {
                assert!(p.permite(puerta, etiqueta), "{puerta:?} {etiqueta:#04x}");
            }
        }
    }

    /// Una regla tapa SU casilla y ninguna mas. Si negar `Set` por `Usb`
    /// negara tambien `Get`, la tabla no seria una politica: seria un
    /// interruptor con nombre largo.
    #[test]
    fn una_regla_solo_tapa_su_casilla() {
        let mut p = Politica::nueva();
        p.cargar(Regla {
            puerta: Puerta::Usb,
            etiqueta: T_SET,
            permitido: false,
        })
        .unwrap();

        assert!(!p.permite(Puerta::Usb, T_SET));
        // la misma etiqueta por otra puerta
        assert!(p.permite(Puerta::Mano, T_SET));
        // la misma puerta con otra etiqueta
        assert!(p.permite(Puerta::Usb, T_MEMO));
        assert!(!p.vacia());
    }

    /// N2a: se legisla sobre la etiqueta, y `Memo` es el caso que obliga --
    /// es el mensaje que la v2 no podia nombrar porque no tenia clase.
    #[test]
    fn se_legisla_sobre_el_mensaje_entero_no_solo_sobre_su_numero() {
        let mut p = Politica::nueva();
        p.cargar(Regla {
            puerta: Puerta::Inalambrica,
            etiqueta: T_MEMO,
            permitido: false,
        })
        .unwrap();
        // `Memo` pide unos segundos de AUDIO para que el agente los
        // analice. Es justo el mensaje que uno querria poder negarle a
        // una carcasa remota, y el que la v2 no podia nombrar porque no
        // tenia clase.
        let memo = Mensaje::Memo { segundos: 3 };
        assert!(!p.permite_mensaje(Puerta::Inalambrica, &memo));
        assert!(p.permite_mensaje(Puerta::Usb, &memo));
    }

    /// N2b, la limitacion aseverada en vez de solo escrita: `Set` es UNA
    /// etiqueta sobre los 536 parametros. Negarlo por una puerta niega
    /// afinar un VCO y borrar la configuracion del cerebro por igual, y no
    /// hay forma de pedir una cosa sin la otra.
    #[test]
    fn una_regla_sobre_set_no_distingue_parametros() {
        let mut p = Politica::nueva();
        p.cargar(Regla {
            puerta: Puerta::Usb,
            etiqueta: T_SET,
            permitido: false,
        })
        .unwrap();
        let afinar = Mensaje::Set(ParamId(0x0100_0001), 100);
        let borrar_el_cerebro = Mensaje::Set(ParamId(0x0200_0002), 0);
        assert_eq!(
            p.permite_mensaje(Puerta::Usb, &afinar),
            p.permite_mensaje(Puerta::Usb, &borrar_el_cerebro),
            "si algun dia difieren, N2b dejo de ser una limitacion y hay que \
             actualizar el papel"
        );
    }

    /// Reemplazar en vez de apilar no es cosmetico: sin eso, cargar dos
    /// veces la misma clave deja la tabla decidiendo por orden de insercion.
    #[test]
    fn cargar_la_misma_clave_reemplaza_en_vez_de_apilar() {
        let mut p = Politica::nueva();
        let clave = |permitido| Regla {
            puerta: Puerta::Usb,
            etiqueta: T_SET,
            permitido,
        };
        p.cargar(clave(false)).unwrap();
        p.cargar(clave(true)).unwrap();
        assert!(p.permite(Puerta::Usb, T_SET), "gano la vieja");
    }

    /// El techo son las 60 casillas de verdad -- cuatro puertas por las
    /// quince etiquetas de cliente. Que quepan justo y ni una mas es la
    /// comprobacion de que MAX_REGLAS no se puso a ojo.
    #[test]
    fn la_tabla_llena_son_las_sesenta_casillas_y_ni_una_mas() {
        let mut p = Politica::nueva();
        let mut n = 0;
        for puerta in Puerta::TODAS {
            for etiqueta in 0x01..=0x0F {
                p.cargar(Regla {
                    puerta,
                    etiqueta,
                    permitido: false,
                })
                .unwrap();
                n += 1;
            }
        }
        assert_eq!(n, MAX_REGLAS, "el techo no es 4 puertas x 15 etiquetas");

        // y la 61 no cabe: se devuelve, no se traga.
        let sobrante = Regla {
            puerta: Puerta::Mano,
            etiqueta: 0x7F,
            permitido: false,
        };
        assert_eq!(p.cargar(sobrante), Err(sobrante));
    }
}
