//! §5 y §6. Las rampas: interpolación por unidad, curva, y el anulado.
//!
//! # Por qué la unidad decide la interpolación
//!
//! Una rampa de corte lineal en hercios suena a máquina. **El oído oye
//! octavas.** De 100 a 1600 Hz son cuatro octavas; a mitad de tiempo van dos,
//! que son 400 Hz — lineal en hercios daría 850.
//!
//! Y nadie lo configura: el descriptor ya lleva la unidad, puesta para que el
//! agente entienda qué hace el parámetro (§2.1 del núcleo). Segundo pago del
//! mismo campo.
//!
//! # La cinta sigue corriendo (§6.2)
//!
//! Una rampa anulada **no se detiene: deja de escribir**. Sigue siendo una
//! función del tiempo, corriendo por dentro. Reactivar es volver a escribir
//! desde donde la función esté *ahora* — que es lo que el oído espera de una
//! automatización.

use crate::descriptor::Unidad;
use crate::param::{ParamId, Valor};
use heapless::Vec;

pub const MAX_RAMPAS: usize = 16;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Rampa {
    pub id: ParamId,
    pub origen: Valor,
    pub destino: Valor,
    /// Pulso absoluto en que arranca. Ya viene cuantizado por la rejilla.
    pub inicio: u64,
    /// En pulsos. **Cero es un salto** que cae en la rejilla (§5.4).
    pub duracion: u32,
    /// `0` lineal, positivo arranca lento, negativo cede al final.
    pub curva: i8,
    /// §6: tocaste el parámetro, así que la rampa dejó de escribir.
    pub anulada: bool,
}

/// Si la unidad ya es logarítmica —o no tiene sentido serlo— se interpola
/// lineal. El dB y los cents ya son logaritmos: volver a tomarlo sería
/// aplicarlo dos veces.
fn interpola_en_octavas(u: Unidad) -> bool {
    matches!(u, Unidad::Hz)
}

/// `t^k` con `k = 2^(curva/50)`. Con `curva = 0` sale `k = 1`, que es lineal.
fn aplicar_curva(t: f32, curva: i8) -> f32 {
    if curva == 0 {
        return t;
    }
    let k = libm::powf(2.0, curva as f32 / 50.0);
    libm::powf(t, k)
}

impl Rampa {
    pub fn nueva(id: ParamId, origen: Valor, destino: Valor, inicio: u64, duracion: u32) -> Self {
        Rampa {
            id,
            origen,
            destino,
            inicio,
            duracion,
            curva: 0,
            anulada: false,
        }
    }

    pub fn termina_en(&self) -> u64 {
        self.inicio + self.duracion as u64
    }

    pub fn terminada_en(&self, pulso: u64) -> bool {
        pulso >= self.termina_en()
    }

    /// Cuánto vale la rampa en ese pulso. **Es una función pura del tiempo**:
    /// da igual si está anulada, la cinta corre igual (§6.2).
    pub fn valor_en(&self, pulso: u64, unidad: Unidad) -> Valor {
        // Estrictamente MENOR: en el pulso de inicio ya cuenta, que es lo que
        // hace que una duracion cero salte justo EN el borde de la rejilla.
        if pulso < self.inicio {
            return self.origen;
        }
        if self.duracion == 0 || pulso >= self.termina_en() {
            return self.destino;
        }
        let t = (pulso - self.inicio) as f32 / self.duracion as f32;
        let t = aplicar_curva(t, self.curva);

        // ln(0) no existe, y un corte no llega a 0 Hz — pero el codigo no
        // puede depender de eso.
        if interpola_en_octavas(unidad) && self.origen > 0 && self.destino > 0 {
            let a = libm::logf(self.origen as f32);
            let b = libm::logf(self.destino as f32);
            let v = libm::expf(a + (b - a) * t);
            return libm::roundf(v) as Valor;
        }
        let d = self.destino as f32 - self.origen as f32;
        self.origen + libm::roundf(d * t) as Valor
    }
}

pub struct Rampas {
    rampas: Vec<Rampa, MAX_RAMPAS>,
}

/// Los pares `(id, valor)` que hay que escribir en este tick.
pub type Escrituras = Vec<(ParamId, Valor), MAX_RAMPAS>;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct SinSitio;

impl Default for Rampas {
    fn default() -> Self {
        Self::nueva()
    }
}

impl Rampas {
    pub const fn nueva() -> Self {
        Rampas { rampas: Vec::new() }
    }

    pub fn activas(&self) -> usize {
        self.rampas.len()
    }

    pub fn de(&self, id: ParamId) -> Option<&Rampa> {
        self.rampas.iter().find(|r| r.id == id)
    }

    /// Una rampa nueva sobre el mismo parámetro **reemplaza a la vieja**: dos
    /// peleándose un parámetro darían un valor sin definir.
    pub fn empujar(&mut self, r: Rampa) -> Result<(), SinSitio> {
        if let Some(vieja) = self.rampas.iter_mut().find(|x| x.id == r.id) {
            *vieja = r;
            return Ok(());
        }
        self.rampas.push(r).map_err(|_| SinSitio)
    }

    /// Devuelve `true` si de verdad había algo que anular.
    pub fn anular(&mut self, id: ParamId) -> bool {
        match self.rampas.iter_mut().find(|r| r.id == id) {
            Some(r) if !r.anulada => {
                r.anulada = true;
                true
            }
            _ => false,
        }
    }

    pub fn reactivar(&mut self, id: ParamId) -> bool {
        match self.rampas.iter_mut().find(|r| r.id == id) {
            Some(r) if r.anulada => {
                r.anulada = false;
                true
            }
            _ => false,
        }
    }

    /// Reactiva todas y devuelve cuáles.
    pub fn reactivar_todas(&mut self) -> Vec<ParamId, MAX_RAMPAS> {
        let mut ids = Vec::new();
        for r in self.rampas.iter_mut().filter(|r| r.anulada) {
            r.anulada = false;
            let _ = ids.push(r.id);
        }
        ids
    }

    pub fn anuladas(&self) -> usize {
        self.rampas.iter().filter(|r| r.anulada).count()
    }

    /// Lo que hay que escribir en este pulso.
    ///
    /// `unidad_de` resuelve la unidad de cada id — así `rampa.rs` no queda
    /// acoplado al `Modelo`. Las rampas terminadas se quitan solas: si no,
    /// ocuparían sitio para siempre.
    pub fn tick<F>(&mut self, pulso: u64, unidad_de: F) -> Escrituras
    where
        F: Fn(ParamId) -> Unidad,
    {
        let mut salida = Escrituras::new();
        for r in self.rampas.iter() {
            if r.anulada || pulso < r.inicio {
                continue;
            }
            let _ = salida.push((r.id, r.valor_en(pulso, unidad_de(r.id))));
        }
        // Una rampa anulada tambien se retira al terminar: la cinta llego al
        // final aunque nadie la estuviera escuchando.
        self.rampas.retain(|r| !r.terminada_en(pulso));
        salida
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn r(origen: Valor, destino: Valor, duracion: u32) -> Rampa {
        Rampa::nueva(ParamId(0x0100), origen, destino, 1000, duracion)
    }

    #[test]
    fn en_hercios_interpola_en_octavas_y_no_en_hercios() {
        // §5.2, y es EL test de esta spec. De 100 a 1600 Hz son 4 octavas;
        // a mitad de tiempo van 2, que son 400 Hz. Lineal en hercios daria
        // 850 — y ahi esta la diferencia entre un barrido que suena parejo y
        // uno que suena a maquina.
        let ra = r(100, 1600, 384);
        let mitad = ra.valor_en(1000 + 192, Unidad::Hz);
        assert!((mitad - 400).abs() <= 2, "dio {mitad}, y lineal daria 850");
    }

    #[test]
    fn en_las_demas_unidades_interpola_lineal() {
        // El dB ya es logaritmico, y los cents tambien. Volver a tomar
        // logaritmo seria aplicarlo dos veces.
        for u in [
            Unidad::MilidB,
            Unidad::Cents,
            Unidad::Milesimas,
            Unidad::Ninguna,
        ] {
            let ra = r(0, 1000, 384);
            assert_eq!(ra.valor_en(1000 + 192, u), 500, "{u:?}");
        }
    }

    #[test]
    fn aterriza_exactamente_en_el_destino() {
        // Ni 99.7 %. Un filtro que se queda a 1595 de 1600 se oye.
        for u in [Unidad::Hz, Unidad::MilidB] {
            let ra = r(100, 1600, 384);
            assert_eq!(ra.valor_en(1000 + 384, u), 1600, "{u:?}");
            assert_eq!(ra.valor_en(1000 + 9999, u), 1600, "{u:?} pasado el final");
        }
    }

    #[test]
    fn antes_de_empezar_vale_el_origen() {
        assert_eq!(r(100, 1600, 384).valor_en(999, Unidad::Hz), 100);
    }

    #[test]
    fn duracion_cero_es_un_salto() {
        // §5.4: no es un SET disfrazado — el inicio ya venia cuantizado.
        let ra = r(100, 1600, 0);
        assert_eq!(ra.valor_en(999, Unidad::Hz), 100);
        assert_eq!(ra.valor_en(1000, Unidad::Hz), 1600);
    }

    #[test]
    fn nunca_se_sale_del_rango_entre_origen_y_destino() {
        for curva in [-100i8, -50, 0, 50, 100] {
            let mut ra = r(200, 800, 384);
            ra.curva = curva;
            for p in 0..=384 {
                let v = ra.valor_en(1000 + p, Unidad::Hz);
                assert!((200..=800).contains(&v), "curva {curva}, pulso {p}: {v}");
            }
        }
    }

    #[test]
    fn la_curva_positiva_arranca_lento_y_la_negativa_cede_al_final() {
        let mut lenta = r(0, 1000, 384);
        lenta.curva = 100;
        let mut rapida = r(0, 1000, 384);
        rapida.curva = -100;
        let m = 1000 + 192;
        assert!(lenta.valor_en(m, Unidad::Ninguna) < 500);
        assert!(rapida.valor_en(m, Unidad::Ninguna) > 500);
    }

    #[test]
    fn una_rampa_que_baja_tambien_funciona() {
        let ra = r(1600, 100, 384);
        assert!((ra.valor_en(1000 + 192, Unidad::Hz) - 400).abs() <= 2);
    }

    #[test]
    fn con_origen_o_destino_no_positivo_cae_a_lineal_sin_reventar() {
        // ln(0) no existe. Un corte no llega a 0 Hz, pero el codigo no puede
        // depender de eso.
        let ra = r(0, 1000, 384);
        assert_eq!(ra.valor_en(1000 + 192, Unidad::Hz), 500);
        let neg = r(-500, 500, 384);
        assert_eq!(neg.valor_en(1000 + 192, Unidad::Hz), 0);
    }

    #[test]
    fn la_cinta_sigue_corriendo_cuando_se_anula() {
        // §6.2: una rampa anulada NO se detiene, deja de escribir. Reactivar
        // cae donde la funcion este AHORA, no donde estaba al anular.
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        let id = ParamId(0x0100);

        // Tick al cuarto del recorrido: escribe.
        assert_eq!(rs.tick(1000 + 96, |_| Unidad::Ninguna).as_slice(), &[(id, 250)]);
        // Se anula: deja de escribir.
        assert!(rs.anular(id));
        assert!(rs.tick(1000 + 192, |_| Unidad::Ninguna).is_empty());
        // Se reactiva a tres cuartos: cae en 750, no en 500.
        assert!(rs.reactivar(id));
        assert_eq!(rs.tick(1000 + 288, |_| Unidad::Ninguna).as_slice(), &[(id, 750)]);
    }

    #[test]
    fn anular_lo_ya_anulado_no_cuenta_dos_veces() {
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        let id = ParamId(0x0100);
        assert!(rs.anular(id));
        assert!(!rs.anular(id), "ya estaba anulada");
        assert_eq!(rs.anuladas(), 1);
        assert!(rs.reactivar(id));
        assert!(!rs.reactivar(id), "ya estaba activa");
    }

    #[test]
    fn una_rampa_terminada_se_quita_sola() {
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        rs.tick(1000 + 384, |_| Unidad::Ninguna);
        assert_eq!(rs.activas(), 0, "no puede quedarse ocupando sitio");
    }

    #[test]
    fn una_rampa_anulada_tambien_se_retira_al_terminar() {
        // Si no, ocuparia sitio para siempre esperando un reactivar que
        // quizas no llegue nunca.
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        rs.anular(ParamId(0x0100));
        rs.tick(1000 + 384, |_| Unidad::Ninguna);
        assert_eq!(rs.activas(), 0);
    }

    #[test]
    fn una_rampa_nueva_sobre_el_mismo_parametro_reemplaza_a_la_vieja() {
        // Dos rampas peleandose un parametro darian un valor sin definir.
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        rs.empujar(r(0, 500, 384)).unwrap();
        assert_eq!(rs.activas(), 1);
        assert_eq!(rs.de(ParamId(0x0100)).unwrap().destino, 500);
    }

    #[test]
    fn una_rampa_que_todavia_no_arranco_no_escribe() {
        // El inicio viene cuantizado a la rejilla: hasta ese pulso, nada.
        let mut rs = Rampas::nueva();
        rs.empujar(r(0, 1000, 384)).unwrap();
        assert!(rs.tick(999, |_| Unidad::Ninguna).is_empty());
        assert!(!rs.tick(1000, |_| Unidad::Ninguna).is_empty());
    }

    #[test]
    fn reactivar_todas_dice_cuales_devolvio() {
        let mut rs = Rampas::nueva();
        rs.empujar(Rampa::nueva(ParamId(1), 0, 100, 0, 384)).unwrap();
        rs.empujar(Rampa::nueva(ParamId(2), 0, 100, 0, 384)).unwrap();
        rs.anular(ParamId(1));
        rs.anular(ParamId(2));
        let ids = rs.reactivar_todas();
        assert_eq!(ids.len(), 2);
        assert_eq!(rs.anuladas(), 0);
        assert!(rs.reactivar_todas().is_empty(), "no queda nada que devolver");
    }

    #[test]
    fn cuando_no_caben_mas_se_dice() {
        let mut rs = Rampas::nueva();
        for i in 0..MAX_RAMPAS {
            rs.empujar(Rampa::nueva(ParamId(i as u32), 0, 100, 0, 384)).unwrap();
        }
        assert_eq!(
            rs.empujar(Rampa::nueva(ParamId(999), 0, 100, 0, 384)),
            Err(SinSitio)
        );
    }
}
