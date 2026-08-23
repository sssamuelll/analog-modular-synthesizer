//! §2.2. El micro RETIENE la operacion marcada hasta que llegue la
//! confirmacion fisica. Si lo decidiera el cliente, bastaria con un cliente
//! que no pregunte.

use crate::param::{ParamId, Valor};
use heapless::Vec;

/// En escena hay una operacion pendiente, no una cola.
pub const MAX_RETENIDAS: usize = 4;
/// Portado de la capa de autoridad de `projects/aurelius`: mandatos con TTL.
pub const TTL_MS: u64 = 30_000;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Retenida {
    pub token: u16,
    pub id: ParamId,
    pub valor: Valor,
    pub vence_ms: u64,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct ColaLlena;

pub struct Retenidas {
    cola: Vec<Retenida, MAX_RETENIDAS>,
    siguiente_token: u16,
}

impl Default for Retenidas {
    fn default() -> Self {
        Self::nueva()
    }
}

impl Retenidas {
    pub const fn nueva() -> Self {
        Retenidas {
            cola: Vec::new(),
            siguiente_token: 1,
        }
    }

    /// Devuelve el token que viaja en el mensaje `PENDING` (§4.1).
    pub fn retener(&mut self, id: ParamId, valor: Valor, ahora_ms: u64) -> Result<u16, ColaLlena> {
        let token = self.siguiente_token;
        self.cola
            .push(Retenida {
                token,
                id,
                valor,
                vence_ms: ahora_ms + TTL_MS,
            })
            .map_err(|_| ColaLlena)?;
        // El 0 se reserva para "ningun token", asi que la vuelta salta de 0 a 1.
        self.siguiente_token = self.siguiente_token.wrapping_add(1).max(1);
        Ok(token)
    }

    /// El pulsador de la cabeza local o el pedal (§5.2, §5.3). Confirma la mas
    /// reciente que siga viva.
    ///
    /// Lo vencido NO se descarta aqui: se queda para que `caducar` lo anuncie
    /// con `RESOLVED { confirmado: false }`. Si esta funcion lo tirara, un
    /// token desapareceria sin que ningun cliente se entere de que murio.
    pub fn confirmar(&mut self, ahora_ms: u64) -> Option<Retenida> {
        let i = self.cola.iter().rposition(|r| ahora_ms < r.vence_ms)?;
        Some(self.cola.remove(i))
    }

    /// Los tokens que hay que anunciar con `RESOLVED { confirmado: false }`.
    pub fn caducar(&mut self, ahora_ms: u64) -> Vec<u16, MAX_RETENIDAS> {
        let mut muertos = Vec::new();
        let mut vivos = Vec::new();
        for r in self.cola.iter() {
            if ahora_ms >= r.vence_ms {
                let _ = muertos.push(r.token);
            } else {
                let _ = vivos.push(*r);
            }
        }
        self.cola = vivos;
        muertos
    }

    pub fn pendientes(&self) -> &[Retenida] {
        &self.cola
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::{Ambito, Descriptor, Tipo, Unidad};
    use crate::modelo::{ErrorSet, Modelo};

    static PELIGROSO: Descriptor = Descriptor {
        id: ParamId(0x0055),
        nombre: "borrar la libreria de presets",
        tipo: Tipo::Booleano,
        ambito: Ambito::Compartido,
        solo_lectura: false,
        medida: false,
        confirmacion_fisica: true,
        acepta_modulacion: false,
        min: 0,
        max: 1,
        def: 0,
        unidad: Unidad::Ninguna,
        etiquetas: &[],
    };

    fn escena() -> (Modelo, Retenidas) {
        let mut m = Modelo::nuevo();
        m.registrar(&PELIGROSO).unwrap();
        (m, Retenidas::nueva())
    }

    #[test]
    fn llega_por_usb_y_no_se_ejecuta_hasta_el_pulsador() {
        // §9, fila "Confirmacion fisica". Este es EL test de §2.2.
        let (mut m, mut r) = escena();
        assert_eq!(m.set(PELIGROSO.id, 1), Err(ErrorSet::ExigeConfirmacion));
        let token = r.retener(PELIGROSO.id, 1, 0).unwrap();
        assert_eq!(
            m.get(PELIGROSO.id),
            Some(0),
            "no puede haberse aplicado todavia"
        );

        let pendiente = r
            .confirmar(1_000)
            .expect("el pulsador tenia algo que confirmar");
        assert_eq!(pendiente.token, token);
        m.aplicar_confirmado(pendiente.id, pendiente.valor).unwrap();
        assert_eq!(m.get(PELIGROSO.id), Some(1));
        assert!(r.confirmar(1_001).is_none(), "no puede quedar residuo");
    }

    #[test]
    fn si_nadie_confirma_caduca_y_no_pasa_nada() {
        let (m, mut r) = escena();
        let token = r.retener(PELIGROSO.id, 1, 0).unwrap();
        assert!(r.caducar(TTL_MS - 1).is_empty());
        assert_eq!(r.caducar(TTL_MS).as_slice(), &[token]);
        assert!(r.confirmar(TTL_MS + 1).is_none());
        assert_eq!(m.get(PELIGROSO.id), Some(0));
    }

    #[test]
    fn el_pulsador_confirma_la_mas_reciente() {
        let (_, mut r) = escena();
        r.retener(PELIGROSO.id, 1, 0).unwrap();
        let segunda = r.retener(PELIGROSO.id, 0, 10).unwrap();
        assert_eq!(r.confirmar(20).unwrap().token, segunda);
    }

    #[test]
    fn la_cola_llena_se_queja_en_vez_de_tirar_lo_viejo() {
        let (_, mut r) = escena();
        for i in 0..MAX_RETENIDAS {
            r.retener(PELIGROSO.id, 1, i as u64).unwrap();
        }
        assert!(r.retener(PELIGROSO.id, 1, 99).is_err());
    }

    #[test]
    fn los_tokens_no_se_repiten_entre_operaciones_vivas() {
        let (_, mut r) = escena();
        let a = r.retener(PELIGROSO.id, 1, 0).unwrap();
        let b = r.retener(PELIGROSO.id, 0, 1).unwrap();
        assert_ne!(a, b);
    }

    #[test]
    fn confirmar_salta_lo_vencido_pero_no_lo_desaparece() {
        // El caso feo: la vieja ya vencio y la nueva sigue viva. El pulsador
        // tiene que agarrar la viva — y la vencida tiene que seguir ahi para
        // que `caducar` la anuncie. Si `confirmar` la tirara, ese token
        // moriria sin que ningun cliente se entere.
        let (_, mut r) = escena();
        let vieja = r.retener(PELIGROSO.id, 1, 0).unwrap();
        r.retener(PELIGROSO.id, 0, TTL_MS).unwrap();

        assert_eq!(r.confirmar(TTL_MS + 1).unwrap().valor, 0, "agarro la viva");
        assert!(
            r.confirmar(TTL_MS + 1).is_none(),
            "no puede confirmar una vencida"
        );
        assert_eq!(
            r.caducar(TTL_MS + 1).as_slice(),
            &[vieja],
            "y la vencida se anuncia"
        );
        assert!(r.pendientes().is_empty());
    }
}
