//! El estado vivo del instrumento. Por §2.1 esta es la UNICA puerta: si algo
//! muta el instrumento sin pasar por aqui, el agente no lo alcanza.

use crate::descriptor::Descriptor;
use crate::param::{ParamId, Valor};
use heapless::Vec;

/// Capacidad, no conteo. Cinco modulos poblados con sus voces caben de sobra.
pub const MAX_PARAMS: usize = 512;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Cambio {
    pub id: ParamId,
    pub valor: Valor,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorSet {
    NoExiste,
    SoloLectura,
    FueraDeRango,
    /// §2.2: retenida hasta la confirmacion fisica.
    ExigeConfirmacion,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorRegistro {
    Duplicado,
    Lleno,
}

pub struct Modelo {
    descs: Vec<&'static Descriptor, MAX_PARAMS>,
    vals: Vec<Valor, MAX_PARAMS>,
}

impl Default for Modelo {
    fn default() -> Self {
        Self::nuevo()
    }
}

impl Modelo {
    pub const fn nuevo() -> Self {
        Modelo {
            descs: Vec::new(),
            vals: Vec::new(),
        }
    }

    pub fn len(&self) -> usize {
        self.descs.len()
    }

    pub fn is_empty(&self) -> bool {
        self.descs.is_empty()
    }

    /// Inserta ordenado por id para que la busqueda sea binaria.
    pub fn registrar(&mut self, d: &'static Descriptor) -> Result<(), ErrorRegistro> {
        match self.descs.binary_search_by_key(&d.id, |x| x.id) {
            Ok(_) => Err(ErrorRegistro::Duplicado),
            Err(pos) => {
                self.descs.insert(pos, d).map_err(|_| ErrorRegistro::Lleno)?;
                // Si esta segunda insercion fallara, las dos tablas quedarian
                // descuadradas; como comparten capacidad, no puede pasar.
                self.vals
                    .insert(pos, d.def)
                    .map_err(|_| ErrorRegistro::Lleno)?;
                Ok(())
            }
        }
    }

    fn pos(&self, id: ParamId) -> Option<usize> {
        self.descs.binary_search_by_key(&id, |x| x.id).ok()
    }

    pub fn descriptor_de(&self, id: ParamId) -> Option<&'static Descriptor> {
        self.pos(id).map(|i| self.descs[i])
    }

    pub fn descriptores(&self) -> impl Iterator<Item = &'static Descriptor> + '_ {
        self.descs.iter().copied()
    }

    pub fn get(&self, id: ParamId) -> Option<Valor> {
        self.pos(id).map(|i| self.vals[i])
    }

    /// La escritura de un cliente. Aplica las tres reglas del descriptor.
    pub fn set(&mut self, id: ParamId, v: Valor) -> Result<Cambio, ErrorSet> {
        let i = self.pos(id).ok_or(ErrorSet::NoExiste)?;
        let d = self.descs[i];
        if d.solo_lectura {
            return Err(ErrorSet::SoloLectura);
        }
        if v < d.min || v > d.max {
            return Err(ErrorSet::FueraDeRango);
        }
        if d.confirmacion_fisica {
            return Err(ErrorSet::ExigeConfirmacion);
        }
        self.vals[i] = v;
        Ok(Cambio { id, valor: v })
    }

    /// El unico camino que escribe una medida (§3.4). Lo llama el instrumento,
    /// nunca un cliente.
    pub fn publicar_medida(&mut self, id: ParamId, v: Valor) -> Result<Cambio, ErrorSet> {
        let i = self.pos(id).ok_or(ErrorSet::NoExiste)?;
        if !self.descs[i].medida {
            return Err(ErrorSet::SoloLectura);
        }
        self.vals[i] = v;
        Ok(Cambio { id, valor: v })
    }

    /// La puerta que abre la confirmacion fisica (§2.2). Salta el veto de
    /// `confirmacion_fisica` y NADA MAS: rango y solo-lectura siguen mandando.
    pub fn aplicar_confirmado(&mut self, id: ParamId, v: Valor) -> Result<Cambio, ErrorSet> {
        let i = self.pos(id).ok_or(ErrorSet::NoExiste)?;
        let d = self.descs[i];
        if d.solo_lectura {
            return Err(ErrorSet::SoloLectura);
        }
        if v < d.min || v > d.max {
            return Err(ErrorSet::FueraDeRango);
        }
        self.vals[i] = v;
        Ok(Cambio { id, valor: v })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::{Ambito, Tipo, Unidad};

    const fn d(id: u16, solo_lectura: bool, medida: bool, confirma: bool) -> Descriptor {
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

    fn modelo() -> Modelo {
        let mut m = Modelo::nuevo();
        // A proposito en desorden: registrar tiene que dejarlo ordenado.
        m.registrar(&PELIGROSO).unwrap();
        m.registrar(&NORMAL).unwrap();
        m.registrar(&MEDIDA).unwrap();
        m
    }

    #[test]
    fn arranca_en_los_valores_por_defecto() {
        assert_eq!(modelo().get(NORMAL.id), Some(0));
    }

    #[test]
    fn un_set_devuelve_el_cambio_que_alimenta_a_changed() {
        // §4.1: CHANGED va a todos los suscriptores venga de donde venga el SET.
        let mut m = modelo();
        assert_eq!(m.set(NORMAL.id, 42), Ok(Cambio { id: NORMAL.id, valor: 42 }));
        assert_eq!(m.get(NORMAL.id), Some(42));
    }

    #[test]
    fn una_medida_no_se_escribe_desde_un_cliente() {
        // §3.4: el unico camino que la escribe es publicar_medida.
        let mut m = modelo();
        assert_eq!(m.set(MEDIDA.id, 5), Err(ErrorSet::SoloLectura));
        assert_eq!(m.get(MEDIDA.id), Some(0));
        assert!(m.publicar_medida(MEDIDA.id, -1200).is_ok());
        assert_eq!(m.get(MEDIDA.id), Some(-1200));
    }

    #[test]
    fn fuera_de_rango_se_rechaza_en_vez_de_recortarse() {
        // §6.1 fallar en voz alta: recortar en silencio le miente al agente,
        // que creeria haber puesto 500.
        let mut m = modelo();
        assert_eq!(m.set(NORMAL.id, 500), Err(ErrorSet::FueraDeRango));
        assert_eq!(m.get(NORMAL.id), Some(0));
    }

    #[test]
    fn lo_marcado_no_se_ejecuta_de_una() {
        // §2.2: la regla la impone el instrumento, no el cliente.
        let mut m = modelo();
        assert_eq!(m.set(PELIGROSO.id, 7), Err(ErrorSet::ExigeConfirmacion));
        assert_eq!(m.get(PELIGROSO.id), Some(0));
        // Solo la retencion (Task 4) puede aplicarlo, y por otra puerta.
        assert!(m.aplicar_confirmado(PELIGROSO.id, 7).is_ok());
        assert_eq!(m.get(PELIGROSO.id), Some(7));
    }

    #[test]
    fn un_parametro_que_no_existe_lo_dice() {
        let mut m = modelo();
        assert_eq!(m.set(ParamId(0xBEEF), 1), Err(ErrorSet::NoExiste));
        assert_eq!(m.get(ParamId(0xBEEF)), None);
    }

    #[test]
    fn no_se_registra_dos_veces_el_mismo_id() {
        let mut m = modelo();
        assert_eq!(m.registrar(&NORMAL), Err(ErrorRegistro::Duplicado));
    }

    #[test]
    fn registrar_en_desorden_deja_la_tabla_ordenada() {
        let m = modelo();
        let ids: heapless::Vec<u16, 8> = m.descriptores().map(|d| d.id.0).collect();
        assert_eq!(ids.as_slice(), &[0x1000, 0x1001, 0x1002]);
    }
}
