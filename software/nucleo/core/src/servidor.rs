//! Donde el contrato deja de ser piezas y contesta.
//!
//! El modelo, la retencion, el protocolo y el descriptor existian por separado
//! y **nada los unia**. `atender` es la funcion que hace que un `SET` que llega
//! por el cable mueva un parametro, avise a los suscriptores y responda.
//!
//! Es pura —el tiempo entra como argumento, no se lee de ningun reloj— asi que
//! se prueba entera sin placa.
//!
//! # La regla que la gobierna
//!
//! **Ningun cliente se queda en silencio.** Toda peticion produce respuesta: la
//! que pedia, o un `ERROR` que dice por que no. Un agente que escribe y no
//! recibe nada no sabe si llego, si se aplico, o si el instrumento se colgo.

use crate::medidas;
use crate::modelo::{ErrorSet, Modelo};
use crate::param::{ParamId, Valor};
use crate::protocolo::{CodigoError, Mensaje};
use crate::retencion::Retenidas;
use heapless::Vec;

/// La version que este firmware sabe hablar.
pub const VERSION_PROTOCOLO: u16 = 1;
/// Lo mas que produce una sola peticion: `ERROR` + `PENDING` son dos, y el
/// margen sobra.
pub const MAX_RESPUESTAS: usize = 4;

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Respuesta {
    Mensaje(Mensaje),
    /// El volcado del descriptor. No es un `Mensaje` porque es de largo
    /// variable y grande: meterlo en la enumeracion obligaria a darle vida
    /// (`Mensaje<'a>`) y a que eso rippleara por todo el codec. La capa de
    /// transporte lo sirve en su propio sobre.
    Descriptores,
}

pub type Respuestas = Vec<Respuesta, MAX_RESPUESTAS>;

pub struct Instrumento {
    modelo: Modelo,
    retenidas: Retenidas,
    suscrito: bool,
}

impl Default for Instrumento {
    fn default() -> Self {
        Self::nuevo()
    }
}

impl Instrumento {
    pub const fn nuevo() -> Self {
        Instrumento {
            modelo: Modelo::nuevo(),
            retenidas: Retenidas::nueva(),
            suscrito: false,
        }
    }

    /// Un instrumento con lo unico que hoy existe sin periféricos: las medidas
    /// de §7.3. El descubrimiento por I²C llega con el plan de los periféricos.
    pub fn con_medidas() -> Self {
        let mut i = Self::nuevo();
        let _ = medidas::registrar(&mut i.modelo);
        i
    }

    pub fn modelo(&self) -> &Modelo {
        &self.modelo
    }
    pub fn modelo_mut(&mut self) -> &mut Modelo {
        &mut self.modelo
    }
    pub fn suscrito(&self) -> bool {
        self.suscrito
    }

    /// Lo que llega por el cable.
    pub fn atender(&mut self, m: Mensaje, ahora_ms: u64) -> Respuestas {
        let mut r = Respuestas::new();
        // Un cliente no puede fabricar un `CHANGED` y mentirle a los demas.
        if m.del_instrumento() {
            self.error(&mut r, &m, CodigoError::Desconocido);
            return r;
        }
        match m {
            Mensaje::Hello { .. } => {
                let _ = r.push(Respuesta::Mensaje(Mensaje::Hola {
                    version: VERSION_PROTOCOLO,
                }));
            }
            Mensaje::Describe => {
                let _ = r.push(Respuesta::Descriptores);
            }
            Mensaje::Get(id) => match self.modelo.get(id) {
                Some(v) => {
                    let _ = r.push(Respuesta::Mensaje(Mensaje::Changed(id, v)));
                }
                None => self.error(&mut r, &m, CodigoError::NoExiste),
            },
            Mensaje::Set(id, v) => self.escribir(&mut r, &m, id, v, ahora_ms),
            Mensaje::Subscribe { activo } => self.suscrito = activo,
            Mensaje::Point { .. } => {
                // La cadena WS2812 llega con el plan de los perifericos.
                self.error(&mut r, &m, CodigoError::NoDisponible);
            }
            // Todo esto necesita perifericos o almacenamiento que aun no
            // existen. Callarse seria peor que decir que no.
            Mensaje::PresetList
            | Mensaje::PresetLoad(_)
            | Mensaje::PresetSave(_)
            | Mensaje::TuneStart
            | Mensaje::PatchScan
            | Mensaje::Telemetry
            | Mensaje::Memo { .. } => self.error(&mut r, &m, CodigoError::NoDisponible),
            // Los del instrumento ya se rechazaron arriba.
            _ => self.error(&mut r, &m, CodigoError::Desconocido),
        }
        r
    }

    fn escribir(
        &mut self,
        r: &mut Respuestas,
        m: &Mensaje,
        id: ParamId,
        v: Valor,
        ahora_ms: u64,
    ) {
        match self.modelo.set(id, v) {
            Ok(c) => self.anunciar(r, c.id, c.valor),
            Err(ErrorSet::ExigeConfirmacion) => {
                // §2.2: el micro RETIENE. La regla la impone el instrumento.
                self.error(r, m, CodigoError::ExigeConfirmacion);
                match self.retenidas.retener(id, v, ahora_ms) {
                    Ok(token) => {
                        let _ = r.push(Respuesta::Mensaje(Mensaje::Pending { token, id }));
                    }
                    Err(_) => self.error(r, m, CodigoError::ColaLlena),
                }
            }
            Err(e) => self.error(r, m, codigo_de(e)),
        }
    }

    /// El pulsador de la cabeza local o el pedal (§5.2, §5.3).
    pub fn confirmacion_fisica(&mut self, ahora_ms: u64) -> Respuestas {
        let mut r = Respuestas::new();
        let Some(p) = self.retenidas.confirmar(ahora_ms) else {
            return r;
        };
        let _ = r.push(Respuesta::Mensaje(Mensaje::Resolved {
            token: p.token,
            confirmado: true,
        }));
        if let Ok(c) = self.modelo.aplicar_confirmado(p.id, p.valor) {
            self.anunciar(&mut r, c.id, c.valor);
        }
        r
    }

    /// Se llama periodicamente. Lo que vencio se anuncia: si no, un token
    /// moriria sin que ningun cliente se entere.
    pub fn caducar(&mut self, ahora_ms: u64) -> Respuestas {
        let mut r = Respuestas::new();
        for token in self.retenidas.caducar(ahora_ms) {
            let _ = r.push(Respuesta::Mensaje(Mensaje::Resolved {
                token,
                confirmado: false,
            }));
        }
        r
    }

    /// Lo que mide el instrumento (§3.4). No viene del cable, pero lo que
    /// produce tambien hay que mandarlo.
    pub fn publicar_medida(&mut self, id: ParamId, v: Valor) -> Respuestas {
        let mut r = Respuestas::new();
        if let Ok(c) = self.modelo.publicar_medida(id, v) {
            self.anunciar(&mut r, c.id, c.valor);
        }
        r
    }

    /// §4.1: `CHANGED` va a los SUSCRIPTORES, venga de donde venga el cambio.
    /// Mandarselo a quien no pidio nada llena el cable de trafico que nadie lee.
    fn anunciar(&self, r: &mut Respuestas, id: ParamId, v: Valor) {
        if self.suscrito {
            let _ = r.push(Respuesta::Mensaje(Mensaje::Changed(id, v)));
        }
    }

    fn error(&self, r: &mut Respuestas, m: &Mensaje, codigo: CodigoError) {
        let _ = r.push(Respuesta::Mensaje(Mensaje::Error {
            etiqueta: crate::protocolo::etiqueta_de(m),
            codigo,
        }));
    }
}

fn codigo_de(e: ErrorSet) -> CodigoError {
    match e {
        ErrorSet::NoExiste => CodigoError::NoExiste,
        ErrorSet::SoloLectura => CodigoError::SoloLectura,
        ErrorSet::FueraDeRango => CodigoError::FueraDeRango,
        ErrorSet::ExigeConfirmacion => CodigoError::ExigeConfirmacion,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::{Ambito, Descriptor, Tipo, Unidad};
    use crate::retencion::TTL_MS;

    const fn d(id: u16, solo_lectura: bool, medida: bool, confirma: bool) -> Descriptor {
        Descriptor {
            id: ParamId(id),
            nombre: "prueba",
            tipo: Tipo::Continuo,
            ambito: Ambito::Compartido,
            solo_lectura,
            medida,
            confirmacion_fisica: confirma,
            min: -100,
            max: 100,
            def: 0,
            unidad: Unidad::Ninguna,
            etiquetas: &[],
        }
    }

    static NORMAL: Descriptor = d(0x1000, false, false, false);
    static MEDIDA: Descriptor = d(0x1001, true, true, false);
    static PELIGROSO: Descriptor = d(0x1002, false, false, true);

    fn instrumento() -> Instrumento {
        let mut i = Instrumento::nuevo();
        i.modelo_mut().registrar(&NORMAL).unwrap();
        i.modelo_mut().registrar(&MEDIDA).unwrap();
        i.modelo_mut().registrar(&PELIGROSO).unwrap();
        i
    }

    fn mensajes(r: &Respuestas) -> Vec<Mensaje, MAX_RESPUESTAS> {
        r.iter()
            .filter_map(|x| match x {
                Respuesta::Mensaje(m) => Some(*m),
                _ => None,
            })
            .collect()
    }

    #[test]
    fn hello_se_contesta_con_la_version_acordada() {
        let r = instrumento().atender(Mensaje::Hello { version: 1 }, 0);
        assert_eq!(
            mensajes(&r).as_slice(),
            &[Mensaje::Hola { version: VERSION_PROTOCOLO }]
        );
    }

    #[test]
    fn describe_pide_el_volcado_del_descriptor() {
        let r = instrumento().atender(Mensaje::Describe, 0);
        assert!(r.iter().any(|x| matches!(x, Respuesta::Descriptores)));
    }

    #[test]
    fn un_get_devuelve_el_valor_y_un_set_lo_mueve() {
        let mut i = instrumento();
        assert_eq!(
            mensajes(&i.atender(Mensaje::Get(NORMAL.id), 0)).as_slice(),
            &[Mensaje::Changed(NORMAL.id, 0)]
        );
        i.atender(Mensaje::Set(NORMAL.id, 42), 0);
        assert_eq!(i.modelo().get(NORMAL.id), Some(42));
    }

    #[test]
    fn changed_solo_sale_hacia_quien_se_suscribio() {
        // §4.1: CHANGED va a los SUSCRIPTORES. Mandarselo a quien no pidio
        // nada llena el cable de trafico que nadie lee.
        let mut i = instrumento();
        assert!(mensajes(&i.atender(Mensaje::Set(NORMAL.id, 1), 0)).is_empty());
        i.atender(Mensaje::Subscribe { activo: true }, 0);
        assert_eq!(
            mensajes(&i.atender(Mensaje::Set(NORMAL.id, 2), 0)).as_slice(),
            &[Mensaje::Changed(NORMAL.id, 2)]
        );
    }

    #[test]
    fn un_set_rechazado_dice_por_que_en_vez_de_callarse() {
        // El hallazgo que motivo la Task 2. Sin esto el agente escribe, no
        // pasa nada, y se queda esperando para siempre.
        let mut i = instrumento();
        for (id, valor, codigo) in [
            (MEDIDA.id, 5, CodigoError::SoloLectura),
            (NORMAL.id, 99_999, CodigoError::FueraDeRango),
            (ParamId(0xBEEF), 1, CodigoError::NoExiste),
        ] {
            let r = mensajes(&i.atender(Mensaje::Set(id, valor), 0));
            assert_eq!(
                r.as_slice(),
                &[Mensaje::Error { etiqueta: 0x04, codigo }],
                "{id:?} tenia que quejarse con {codigo:?}"
            );
        }
    }

    #[test]
    fn un_get_de_lo_que_no_existe_tambien_se_queja() {
        let mut i = instrumento();
        let r = mensajes(&i.atender(Mensaje::Get(ParamId(0xBEEF)), 0));
        assert_eq!(
            r.as_slice(),
            &[Mensaje::Error { etiqueta: 0x03, codigo: CodigoError::NoExiste }]
        );
    }

    #[test]
    fn lo_marcado_queda_pendiente_y_solo_el_pulsador_lo_suelta() {
        // §2.2 de punta a punta, por el protocolo.
        let mut i = instrumento();
        let r = mensajes(&i.atender(Mensaje::Set(PELIGROSO.id, 1), 0));
        let token = match r.as_slice() {
            [Mensaje::Error { codigo: CodigoError::ExigeConfirmacion, .. }, Mensaje::Pending { token, id }] =>
            {
                assert_eq!(*id, PELIGROSO.id);
                *token
            }
            otro => panic!("tenia que retener y avisar: {otro:?}"),
        };
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(0), "no puede haberse aplicado");

        let r = mensajes(&i.confirmacion_fisica(1_000));
        assert!(r.contains(&Mensaje::Resolved { token, confirmado: true }));
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(1));
    }

    #[test]
    fn si_nadie_confirma_el_cliente_se_entera_de_que_expiro() {
        let mut i = instrumento();
        i.atender(Mensaje::Set(PELIGROSO.id, 1), 0);
        let r = mensajes(&i.caducar(TTL_MS));
        assert!(matches!(
            r.as_slice(),
            [Mensaje::Resolved { confirmado: false, .. }]
        ));
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(0));
    }

    #[test]
    fn lo_que_todavia_no_sabemos_hacer_se_dice_claro() {
        // Presets, autoafinado, barrido, memo y los LED necesitan perifericos
        // que aun no existen. Callarse seria peor que decir que no.
        let mut i = instrumento();
        for m in [
            Mensaje::PresetList,
            Mensaje::PresetLoad(0),
            Mensaje::PresetSave(0),
            Mensaje::TuneStart,
            Mensaje::PatchScan,
            Mensaje::Telemetry,
            Mensaje::Memo { segundos: 2 },
            Mensaje::Point { id: NORMAL.id, color: crate::protocolo::Rgb { r: 1, g: 2, b: 3 } },
        ] {
            let r = mensajes(&i.atender(m, 0));
            assert!(
                matches!(
                    r.as_slice(),
                    [Mensaje::Error { codigo: CodigoError::NoDisponible, .. }]
                ),
                "{m:?} se quedo callado"
            );
        }
    }

    #[test]
    fn una_medida_publicada_llega_a_los_suscriptores() {
        let mut i = instrumento();
        i.atender(Mensaje::Subscribe { activo: true }, 0);
        let r = mensajes(&i.publicar_medida(MEDIDA.id, -100));
        assert_eq!(r.as_slice(), &[Mensaje::Changed(MEDIDA.id, -100)]);
    }

    #[test]
    fn un_mensaje_del_instrumento_que_llega_de_fuera_se_rechaza() {
        // Un cliente no puede fabricar un CHANGED y mentirle a los demas.
        let mut i = instrumento();
        let r = mensajes(&i.atender(Mensaje::Changed(NORMAL.id, 7), 0));
        assert_eq!(
            r.as_slice(),
            &[Mensaje::Error { etiqueta: 0x81, codigo: CodigoError::Desconocido }]
        );
        assert_eq!(i.modelo().get(NORMAL.id), Some(0));
    }

    #[test]
    fn los_dos_unicos_silencios_son_a_proposito() {
        // La regla del modulo, barrida de una. Este test se escribio como
        // «ninguna peticion se queda sin respuesta» y fallo — lo cual estuvo
        // bien, porque obligo a decirla con precision:
        //
        //   1. `SUBSCRIBE` calla porque su efecto ES el silencio.
        //   2. Un `SET` que sale bien y sin suscriptor calla A PROPOSITO. Si
        //      no, girar una perilla dispararia cientos de acks por segundo.
        //      La confirmacion de un SET es el `CHANGED`, y para eso el
        //      cliente se suscribe — que es justo lo que hace el agente.
        //
        // Todo lo demas que llegue del cable produce algo.
        let mut i = instrumento();
        for m in mensajes_de_cliente(&NORMAL.id) {
            let callar_esta_bien = matches!(m, Mensaje::Subscribe { .. })
                || matches!(m, Mensaje::Set(id, v) if i.modelo().descriptor_de(id)
                    .is_some_and(|d| !d.solo_lectura && !d.confirmacion_fisica
                                     && v >= d.min && v <= d.max));
            let r = i.atender(m, 0);
            if callar_esta_bien {
                continue;
            }
            assert!(!r.is_empty(), "{m:?} dejo al cliente en silencio");
        }
    }

    #[test]
    fn el_suscriptor_si_recibe_la_confirmacion_de_su_propio_set() {
        // El otro lado de la regla de arriba: quien quiere saber que su
        // escritura llego, se suscribe. El agente lo hace.
        let mut i = instrumento();
        i.atender(Mensaje::Subscribe { activo: true }, 0);
        for m in mensajes_de_cliente(&NORMAL.id) {
            if matches!(m, Mensaje::Subscribe { .. }) {
                continue;
            }
            assert!(
                !i.atender(m, 0).is_empty(),
                "suscrito, {m:?} no puede dejar silencio"
            );
        }
    }

    fn mensajes_de_cliente(id: &ParamId) -> [Mensaje; 12] {
        [
            Mensaje::Hello { version: 1 },
            Mensaje::Describe,
            Mensaje::Get(*id),
            Mensaje::Set(*id, 1),
            Mensaje::Subscribe { activo: true },
            Mensaje::PresetList,
            Mensaje::PresetLoad(0),
            Mensaje::PresetSave(0),
            Mensaje::TuneStart,
            Mensaje::PatchScan,
            Mensaje::Telemetry,
            Mensaje::Memo { segundos: 1 },
        ]
    }

    #[test]
    fn el_instrumento_de_arranque_ya_trae_las_medidas() {
        let i = Instrumento::con_medidas();
        assert_eq!(i.modelo().len(), medidas::MEDIDAS.len());
        assert!(i.modelo().get(medidas::ID_PICO_HZ).is_some());
    }
}
