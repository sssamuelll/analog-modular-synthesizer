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
use crate::rampa::{Rampa, Rampas};
use crate::rejilla::{siguiente_borde, Rejilla};
use crate::reloj::Reloj;
use crate::retencion::Retenidas;
use crate::tiempo_params;
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

/// La ventana de aterrizaje, en pulsos (§5.3 de la spec del tiempo musical).
///
/// **Cero, y no por conservadurismo: por aritmetica.**
/// `hardware/02-midi-cv/tiempo_budget.py` lo demuestra — el error de tiempo
/// del sistema es de 1 ms, y un pulso de la rejilla interna dura entre 2.08 ms
/// (a 300 BPM) y 31.25 ms (a 20 BPM). La rejilla es **mas gruesa que el error**
/// a cualquier tempo del rango, asi que no hay ninguna llegada tarde que
/// redondear. El peor caso son 0.48 pulsos, y el guion asevera que no pase de
/// uno.
pub const VENTANA_ATERRIZAJE: u32 = 0;

pub struct Instrumento {
    modelo: Modelo,
    retenidas: Retenidas,
    rampas: Rampas,
    reloj: Reloj,
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
            rampas: Rampas::nueva(),
            reloj: Reloj::nuevo(),
            suscrito: false,
        }
    }

    /// Un instrumento con lo unico que hoy existe sin periféricos: las medidas
    /// de §7.3. El descubrimiento por I²C llega con el plan de los periféricos.
    pub fn con_medidas() -> Self {
        let mut i = Self::nuevo();
        let _ = medidas::registrar(&mut i.modelo);
        let _ = tiempo_params::registrar(&mut i.modelo);
        i
    }

    pub fn reloj(&self) -> &Reloj {
        &self.reloj
    }
    pub fn reloj_mut(&mut self) -> &mut Reloj {
        &mut self.reloj
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
            Mensaje::Set(id, v) => {
                // El SET de un CLIENTE anula la rampa que tenga ese parametro.
                // El del tick no — y esa diferencia vive aqui, no en el
                // modelo, que no gana ninguna puerta nueva.
                if self.rampas.anular(id) {
                    let _ = r.push(Respuesta::Mensaje(Mensaje::Anulado { id, anulado: true }));
                    self.publicar_anulados();
                }
                self.escribir(&mut r, &m, id, v, ahora_ms);
            }
            Mensaje::Rampa {
                id,
                destino,
                duracion,
                curva,
            } => self.arrancar_rampa(&mut r, &m, id, destino, duracion, curva),
            Mensaje::Reactivar { id } => self.reactivar(&mut r, id),
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

    /// Acepta una rampa, o dice por que no.
    ///
    /// El destino se valida **al aceptarla**: mejor ahora que descubrirlo a
    /// mitad del barrido.
    fn arrancar_rampa(
        &mut self,
        r: &mut Respuestas,
        m: &Mensaje,
        id: ParamId,
        destino: Valor,
        duracion: u32,
        curva: i8,
    ) {
        let Some(d) = self.modelo.descriptor_de(id) else {
            return self.error(r, m, CodigoError::NoExiste);
        };
        if d.solo_lectura {
            return self.error(r, m, CodigoError::SoloLectura);
        }
        if d.confirmacion_fisica {
            return self.error(r, m, CodigoError::ExigeConfirmacion);
        }
        if destino < d.min || destino > d.max {
            return self.error(r, m, CodigoError::FueraDeRango);
        }
        let inicio = siguiente_borde(
            self.reloj.posicion(),
            self.rejilla(),
            self.reloj.pulsos_por_compas(),
            VENTANA_ATERRIZAJE,
        )
        .unwrap_or_else(|| self.reloj.posicion());
        let origen = self.modelo.get(id).unwrap_or(d.def);
        let rampa = Rampa {
            id,
            origen,
            destino,
            inicio,
            duracion,
            curva,
            anulada: false,
        };
        if self.rampas.empujar(rampa).is_err() {
            self.error(r, m, CodigoError::ColaLlena);
        }
    }

    fn reactivar(&mut self, r: &mut Respuestas, id: Option<ParamId>) {
        match id {
            Some(p) => {
                if self.rampas.reactivar(p) {
                    let _ = r.push(Respuesta::Mensaje(Mensaje::Anulado {
                        id: p,
                        anulado: false,
                    }));
                }
            }
            None => {
                for p in self.rampas.reactivar_todas() {
                    let _ = r.push(Respuesta::Mensaje(Mensaje::Anulado {
                        id: p,
                        anulado: false,
                    }));
                }
            }
        }
        self.publicar_anulados();
    }

    fn rejilla(&self) -> Rejilla {
        self.modelo
            .get(tiempo_params::ID_CUANTIZACION)
            .and_then(Rejilla::de_indice)
            .unwrap_or(Rejilla::Compas1)
    }

    fn publicar_anulados(&mut self) {
        let n = self.rampas.anuladas() as Valor;
        let _ = self.modelo.publicar_medida(tiempo_params::ID_ANULADOS, n);
    }

    /// Corre el tiempo. Publica las medidas del reloj y escribe lo que las
    /// rampas dicten — **por la ruta que NO anula**, que es la diferencia con
    /// un `SET` de cliente.
    pub fn tick(&mut self, pulso: u64) -> Respuestas {
        let mut r = Respuestas::new();
        self.reloj.avanzar_a_pulso(pulso);

        let unidad_de = |id: ParamId| {
            self.modelo
                .descriptor_de(id)
                .map(|d| d.unidad)
                .unwrap_or(crate::descriptor::Unidad::Ninguna)
        };
        let escrituras = self.rampas.tick(pulso, unidad_de);
        for (id, v) in escrituras {
            if let Ok(c) = self.modelo.set(id, v) {
                self.anunciar(&mut r, c.id, c.valor);
            }
        }
        self.publicar_medidas_del_reloj();
        r
    }

    fn publicar_medidas_del_reloj(&mut self) {
        use tiempo_params as tp;
        let pos = self.reloj.posicion().min(i32::MAX as u64) as Valor;
        let compas = self.reloj.compas().min(i32::MAX as u64) as Valor;
        let mbpm = self.reloj.mbpm() as Valor;
        let fase = self.reloj.tiene_fase() as Valor;
        let libre = self.reloj.rodando_libre() as Valor;
        for (id, v) in [
            (tp::ID_POSICION, pos),
            (tp::ID_COMPAS_ACTUAL, compas),
            (tp::ID_TEMPO_MEDIDO, mbpm),
            (tp::ID_TIENE_FASE, fase),
            (tp::ID_RODANDO_LIBRE, libre),
        ] {
            let _ = self.modelo.publicar_medida(id, v);
        }
    }

    fn escribir(&mut self, r: &mut Respuestas, m: &Mensaje, id: ParamId, v: Valor, ahora_ms: u64) {
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

    const fn d(id: u32, solo_lectura: bool, medida: bool, confirma: bool) -> Descriptor {
        Descriptor {
            id: ParamId(id),
            nombre: "prueba",
            tipo: Tipo::Continuo,
            ambito: Ambito::Compartido,
            solo_lectura,
            medida,
            confirmacion_fisica: confirma,
            acepta_modulacion: false,
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
            &[Mensaje::Hola {
                version: VERSION_PROTOCOLO
            }]
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
                &[Mensaje::Error {
                    etiqueta: 0x04,
                    codigo
                }],
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
            &[Mensaje::Error {
                etiqueta: 0x03,
                codigo: CodigoError::NoExiste
            }]
        );
    }

    #[test]
    fn lo_marcado_queda_pendiente_y_solo_el_pulsador_lo_suelta() {
        // §2.2 de punta a punta, por el protocolo.
        let mut i = instrumento();
        let r = mensajes(&i.atender(Mensaje::Set(PELIGROSO.id, 1), 0));
        let token = match r.as_slice() {
            [Mensaje::Error {
                codigo: CodigoError::ExigeConfirmacion,
                ..
            }, Mensaje::Pending { token, id }] => {
                assert_eq!(*id, PELIGROSO.id);
                *token
            }
            otro => panic!("tenia que retener y avisar: {otro:?}"),
        };
        assert_eq!(
            i.modelo().get(PELIGROSO.id),
            Some(0),
            "no puede haberse aplicado"
        );

        let r = mensajes(&i.confirmacion_fisica(1_000));
        assert!(r.contains(&Mensaje::Resolved {
            token,
            confirmado: true
        }));
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(1));
    }

    #[test]
    fn si_nadie_confirma_el_cliente_se_entera_de_que_expiro() {
        let mut i = instrumento();
        i.atender(Mensaje::Set(PELIGROSO.id, 1), 0);
        let r = mensajes(&i.caducar(TTL_MS));
        assert!(matches!(
            r.as_slice(),
            [Mensaje::Resolved {
                confirmado: false,
                ..
            }]
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
            Mensaje::Point {
                id: NORMAL.id,
                color: crate::protocolo::Rgb { r: 1, g: 2, b: 3 },
            },
        ] {
            let r = mensajes(&i.atender(m, 0));
            assert!(
                matches!(
                    r.as_slice(),
                    [Mensaje::Error {
                        codigo: CodigoError::NoDisponible,
                        ..
                    }]
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
            &[Mensaje::Error {
                etiqueta: 0x81,
                codigo: CodigoError::Desconocido
            }]
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
    fn el_instrumento_de_arranque_trae_las_medidas_y_el_reloj() {
        let i = Instrumento::con_medidas();
        assert_eq!(
            i.modelo().len(),
            medidas::MEDIDAS.len() + tiempo_params::TIEMPO.len()
        );
        assert!(i.modelo().get(medidas::ID_PICO_HZ).is_some());
        assert!(i.modelo().get(tiempo_params::ID_CUANTIZACION).is_some());
    }

    // --- El tiempo musical ---

    static OTRO: Descriptor = d(0x1003, false, false, false);
    const PXC: u64 = 384; // 4/4 a 96 PPQN

    fn con_reloj() -> Instrumento {
        let mut i = Instrumento::nuevo();
        tiempo_params::registrar(i.modelo_mut()).unwrap();
        i.modelo_mut().registrar(&NORMAL).unwrap();
        i.modelo_mut().registrar(&MEDIDA).unwrap();
        i.modelo_mut().registrar(&PELIGROSO).unwrap();
        i.modelo_mut().registrar(&OTRO).unwrap();
        i
    }

    /// El reloj a mitad de compas, que es donde llegan las cosas en la vida
    /// real. **En el pulso 0 estas EN un borde**, asi que una rampa pedida ahi
    /// arranca ya — correcto por §5.3, pero no es lo que estos tests miran.
    fn con_reloj_a_mitad() -> Instrumento {
        let mut i = con_reloj();
        i.tick(200);
        i
    }

    fn rampa(id: ParamId, destino: Valor) -> Mensaje {
        Mensaje::Rampa {
            id,
            destino,
            duracion: 384,
            curva: 0,
        }
    }

    #[test]
    fn una_rampa_aceptada_arranca_en_el_borde_de_la_rejilla() {
        let mut i = con_reloj_a_mitad();
        i.atender(rampa(NORMAL.id, 100), 0);
        // Todavia no se movio: espera al borde.
        i.tick(300);
        assert_eq!(i.modelo().get(NORMAL.id), Some(0));
        i.tick(PXC);
        assert_eq!(
            i.modelo().get(NORMAL.id),
            Some(0),
            "arranca EN el borde, en el origen"
        );
        i.tick(PXC + 192);
        assert!(i.modelo().get(NORMAL.id).unwrap() > 0, "y de ahi se mueve");
    }

    #[test]
    fn un_set_del_cliente_anula_la_rampa_y_lo_avisa() {
        // §6.1. Este es el test de la seccion entera.
        let mut i = con_reloj_a_mitad();
        i.atender(rampa(NORMAL.id, 100), 0);
        i.tick(PXC + 96);
        let r = mensajes(&i.atender(Mensaje::Set(NORMAL.id, 7), 0));
        assert!(r.contains(&Mensaje::Anulado {
            id: NORMAL.id,
            anulado: true
        }));
        assert_eq!(i.modelo().get(NORMAL.id), Some(7));
        // Y el tick ya no la pisa.
        i.tick(PXC + 192);
        assert_eq!(
            i.modelo().get(NORMAL.id),
            Some(7),
            "la rampa dejo de escribir"
        );
    }

    #[test]
    fn reactivar_la_devuelve_donde_la_cinta_este_ahora() {
        // §6.2: la cinta siguio corriendo mientras estuvo anulada.
        let mut i = con_reloj_a_mitad();
        i.atender(rampa(NORMAL.id, 100), 0);
        i.tick(PXC + 96);
        i.atender(Mensaje::Set(NORMAL.id, 7), 0);
        let r = mensajes(&i.atender(
            Mensaje::Reactivar {
                id: Some(NORMAL.id),
            },
            0,
        ));
        assert!(r.contains(&Mensaje::Anulado {
            id: NORMAL.id,
            anulado: false
        }));
        i.tick(PXC + 288);
        assert_eq!(
            i.modelo().get(NORMAL.id),
            Some(75),
            "tres cuartos, no la mitad"
        );
    }

    #[test]
    fn reactivar_sin_id_los_devuelve_todos() {
        let mut i = con_reloj_a_mitad();
        for id in [NORMAL.id, OTRO.id] {
            i.atender(rampa(id, 100), 0);
        }
        i.tick(PXC + 96);
        for id in [NORMAL.id, OTRO.id] {
            i.atender(Mensaje::Set(id, 7), 0);
        }
        let r = mensajes(&i.atender(Mensaje::Reactivar { id: None }, 0));
        assert_eq!(
            r.iter()
                .filter(|m| matches!(m, Mensaje::Anulado { anulado: false, .. }))
                .count(),
            2
        );
    }

    #[test]
    fn una_rampa_a_un_destino_fuera_de_rango_se_rechaza_al_aceptarla() {
        // Mejor ahora que descubrirlo a mitad del barrido.
        let mut i = con_reloj();
        let r = mensajes(&i.atender(rampa(NORMAL.id, 99_999), 0));
        assert_eq!(
            r.as_slice(),
            &[Mensaje::Error {
                etiqueta: 0x0E,
                codigo: CodigoError::FueraDeRango
            }]
        );
    }

    #[test]
    fn no_se_admite_una_rampa_sobre_algo_de_solo_lectura_ni_marcado() {
        let mut i = con_reloj();
        for (id, codigo) in [
            (MEDIDA.id, CodigoError::SoloLectura),
            (PELIGROSO.id, CodigoError::ExigeConfirmacion),
            (ParamId(0xBEEF), CodigoError::NoExiste),
        ] {
            let r = mensajes(&i.atender(rampa(id, 1), 0));
            assert!(
                matches!(r.as_slice(), [Mensaje::Error { codigo: c, .. }] if *c == codigo),
                "{id:?} tenia que dar {codigo:?}, dio {r:?}"
            );
        }
    }

    #[test]
    fn el_tick_solo_avisa_a_los_suscriptores() {
        let mut i = con_reloj_a_mitad();
        i.atender(rampa(NORMAL.id, 100), 0);
        assert!(i.tick(PXC + 96).is_empty());
        i.atender(Mensaje::Subscribe { activo: true }, 0);
        assert!(!i.tick(PXC + 192).is_empty());
    }

    #[test]
    fn el_contador_de_anulados_es_una_medida_de_verdad() {
        let mut i = con_reloj_a_mitad();
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(0));
        i.atender(rampa(NORMAL.id, 100), 0);
        i.tick(PXC + 96);
        i.atender(Mensaje::Set(NORMAL.id, 7), 0);
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(1));
        i.atender(Mensaje::Reactivar { id: None }, 0);
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(0));
    }

    #[test]
    fn el_tick_publica_donde_esta_el_reloj() {
        let mut i = con_reloj();
        i.tick(PXC * 2 + 50);
        assert_eq!(
            i.modelo().get(tiempo_params::ID_POSICION),
            Some((PXC * 2 + 50) as i32)
        );
        assert_eq!(i.modelo().get(tiempo_params::ID_COMPAS_ACTUAL), Some(2));
        assert_eq!(i.modelo().get(tiempo_params::ID_TIENE_FASE), Some(1));
    }

    #[test]
    fn un_set_sobre_algo_sin_rampa_no_avisa_de_ningun_anulado() {
        // Solo se anula lo que de verdad tenia automatizacion corriendo.
        let mut i = con_reloj();
        i.atender(Mensaje::Subscribe { activo: true }, 0);
        let r = mensajes(&i.atender(Mensaje::Set(NORMAL.id, 5), 0));
        assert!(!r.iter().any(|m| matches!(m, Mensaje::Anulado { .. })));
    }
}
