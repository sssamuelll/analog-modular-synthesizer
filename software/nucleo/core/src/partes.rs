//! §3.6. Una **parte** es lo que habilita multitimbrico, split de teclado y
//! capas: un canal MIDI, un rango de teclas, una reserva de voces y un preset
//! propio. Encaja sin tocar el direccionamiento: en la ranura `0` el campo
//! *instancia* es el numero de parte.
//!
//! `MAX_VOCES` es **capacidad, no conteo**. El repartidor se construye con el
//! numero que dio el descubrimiento y no conoce ningun otro.

use heapless::Vec;

pub const MAX_PARTES: usize = 16;
/// Capacidad del pool, no el conteo del instrumento (§3.6).
pub const MAX_VOCES: usize = 16;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Parte {
    pub canal: u8,
    pub nota_min: u8,
    pub nota_max: u8,
    /// Cuantas voces del pool tiene reservadas.
    pub voces: u8,
    /// Desde cual empieza. Con esto sale gratis el poly-chain entre dos
    /// instrumentos: cada uno atiende su tramo del mismo pool.
    pub primera_voz: u8,
    pub preset: u8,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Asignacion {
    pub parte: u8,
    pub voz: u8,
    pub nota: u8,
    /// Que nota se tuvo que robar, si hubo que robar.
    pub robada: Option<u8>,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
struct EstadoVoz {
    nota: Option<u8>,
    canal: u8,
    /// Cuanto mas viejo, mas pequeño. Es a quien se le roba.
    sello: u32,
}

/// La **primera** parte cuyo canal coincide y cuyo rango contiene la nota.
///
/// El orden importa y es del usuario: con rangos solapados manda la que
/// aparezca antes.
pub fn parte_de(partes: &[Parte], canal: u8, nota: u8) -> Option<u8> {
    partes
        .iter()
        .position(|p| p.canal == canal && (p.nota_min..=p.nota_max).contains(&nota))
        .map(|i| i as u8)
}

pub struct Repartidor {
    voces: Vec<EstadoVoz, MAX_VOCES>,
    reloj: u32,
}

impl Repartidor {
    /// `n_voces` sale del descubrimiento (§3.6), nunca de una constante.
    pub fn nueva(n_voces: u8) -> Self {
        let mut voces = Vec::new();
        for _ in 0..n_voces.min(MAX_VOCES as u8) {
            let _ = voces.push(EstadoVoz::default());
        }
        Repartidor { voces, reloj: 0 }
    }

    pub fn n_voces(&self) -> u8 {
        self.voces.len() as u8
    }

    pub fn voz(&self, i: u8) -> Option<u8> {
        self.voces.get(i as usize).and_then(|v| v.nota)
    }

    /// El tramo del pool que le toca a esta parte, recortado a las voces que
    /// el instrumento realmente tiene.
    fn tramo(&self, p: &Parte) -> core::ops::Range<usize> {
        let ini = (p.primera_voz as usize).min(self.voces.len());
        let fin = (ini + p.voces as usize).min(self.voces.len());
        ini..fin
    }

    pub fn nota_on(&mut self, partes: &[Parte], canal: u8, nota: u8) -> Option<Asignacion> {
        let i_parte = parte_de(partes, canal, nota)?;
        let p = partes[i_parte as usize];
        let tramo = self.tramo(&p);
        if tramo.is_empty() {
            return None;
        }
        self.reloj += 1;

        // Primero una libre; si no hay, la mas vieja — pero SIEMPRE dentro del
        // tramo de esta parte. Robar cruzando partes le comeria las voces a
        // otro canal.
        let elegida = tramo
            .clone()
            .find(|i| self.voces[*i].nota.is_none())
            .unwrap_or_else(|| {
                tramo
                    .clone()
                    .min_by_key(|i| self.voces[*i].sello)
                    .expect("el tramo no esta vacio")
            });

        let robada = self.voces[elegida].nota;
        self.voces[elegida] = EstadoVoz {
            nota: Some(nota),
            canal,
            sello: self.reloj,
        };
        Some(Asignacion {
            parte: i_parte,
            voz: elegida as u8,
            nota,
            robada,
        })
    }

    pub fn nota_off(&mut self, canal: u8, nota: u8) -> Option<u8> {
        let i = self
            .voces
            .iter()
            .position(|v| v.nota == Some(nota) && v.canal == canal)?;
        self.voces[i].nota = None;
        Some(i as u8)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn dos_partes() -> [Parte; 2] {
        [
            // Rangos SOLAPADOS a proposito: §9 pide justo eso.
            Parte {
                canal: 0,
                nota_min: 21,
                nota_max: 72,
                voces: 2,
                primera_voz: 0,
                preset: 0,
            },
            Parte {
                canal: 1,
                nota_min: 48,
                nota_max: 108,
                voces: 2,
                primera_voz: 2,
                preset: 1,
            },
        ]
    }

    #[test]
    fn cada_nota_va_a_la_parte_que_le_toca_y_a_su_reserva() {
        // §9, fila "Partes".
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);

        let a = r.nota_on(&partes, 0, 60).unwrap(); // solapada, pero canal 0
        let b = r.nota_on(&partes, 1, 60).unwrap(); // misma nota, canal 1
        assert_eq!(a.parte, 0);
        assert_eq!(b.parte, 1);
        assert!(a.voz < 2, "la parte 0 tiene las voces 0 y 1");
        assert!((2..4).contains(&b.voz), "la parte 1 arranca en la voz 2");
    }

    #[test]
    fn una_nota_fuera_de_todo_rango_no_asigna_nada() {
        assert!(Repartidor::nueva(4)
            .nota_on(&dos_partes(), 0, 100)
            .is_none());
        assert!(Repartidor::nueva(4).nota_on(&dos_partes(), 9, 60).is_none());
    }

    #[test]
    fn cuando_se_acaban_las_voces_roba_la_mas_vieja() {
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);
        let primera = r.nota_on(&partes, 0, 60).unwrap();
        let _ = r.nota_on(&partes, 0, 62).unwrap();
        let tercera = r.nota_on(&partes, 0, 64).unwrap();
        assert_eq!(tercera.voz, primera.voz, "roba la mas vieja");
        assert_eq!(tercera.robada, Some(60));
    }

    #[test]
    fn robar_no_cruza_de_una_parte_a_otra() {
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);
        r.nota_on(&partes, 1, 60).unwrap();
        r.nota_on(&partes, 1, 62).unwrap();
        let tercera = r.nota_on(&partes, 1, 64).unwrap();
        assert!(
            (2..4).contains(&tercera.voz),
            "la parte 1 no puede tocar las voces de la 0"
        );
        // Y las de la parte 0 siguen libres.
        assert!(r.voz(0).is_none() && r.voz(1).is_none());
    }

    #[test]
    fn soltar_una_nota_libera_su_voz() {
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);
        let a = r.nota_on(&partes, 0, 60).unwrap();
        assert_eq!(r.nota_off(0, 60), Some(a.voz));
        let b = r.nota_on(&partes, 0, 65).unwrap();
        assert_eq!(b.robada, None, "habia una voz libre: no hacia falta robar");
    }

    #[test]
    fn soltar_la_misma_nota_de_otro_canal_no_apaga_la_ajena() {
        let partes = dos_partes();
        let mut r = Repartidor::nueva(4);
        let a = r.nota_on(&partes, 0, 60).unwrap();
        r.nota_on(&partes, 1, 60).unwrap();
        r.nota_off(1, 60);
        assert_eq!(r.voz(a.voz), Some(60), "la del canal 0 sigue sonando");
    }

    #[test]
    fn funciona_con_cualquier_conteo_de_voces() {
        // El anti-`4` de verdad: si alguien lo escribiera, esto revienta.
        for n in 1..=MAX_VOCES as u8 {
            let partes = [Parte {
                canal: 0,
                nota_min: 0,
                nota_max: 127,
                voces: n,
                primera_voz: 0,
                preset: 0,
            }];
            let mut r = Repartidor::nueva(n);
            assert_eq!(r.n_voces(), n);
            let mut vistas = Vec::<u8, MAX_VOCES>::new();
            for nota in 0..n {
                let a = r.nota_on(&partes, 0, 60 + nota).unwrap();
                assert!(
                    !vistas.contains(&a.voz),
                    "repitio la voz {} con n={n}",
                    a.voz
                );
                assert!(a.robada.is_none(), "robo teniendo libres, n={n}");
                vistas.push(a.voz).unwrap();
                assert!(a.voz < n);
            }
            // La siguiente ya no cabe: tiene que robar, no fallar.
            assert!(r.nota_on(&partes, 0, 100).unwrap().robada.is_some());
        }
    }

    #[test]
    fn primera_voz_es_lo_que_hace_posible_el_poly_chain() {
        // §3.6: dos instrumentos encadenados, cada uno con su tramo del pool.
        let partes = [Parte {
            canal: 0,
            nota_min: 0,
            nota_max: 127,
            voces: 2,
            primera_voz: 6,
            preset: 0,
        }];
        let mut r = Repartidor::nueva(8);
        for nota in 0..2 {
            assert!((6..8).contains(&r.nota_on(&partes, 0, 60 + nota).unwrap().voz));
        }
    }

    #[test]
    fn una_parte_que_pide_mas_voces_de_las_que_hay_se_recorta_sin_reventar() {
        // El caso real: preset guardado con 8 voces, instrumento con 4.
        let partes = [Parte {
            canal: 0,
            nota_min: 0,
            nota_max: 127,
            voces: 8,
            primera_voz: 0,
            preset: 0,
        }];
        let mut r = Repartidor::nueva(4);
        for nota in 0..4 {
            assert!(r.nota_on(&partes, 0, 60 + nota).unwrap().voz < 4);
        }
        assert!(r.nota_on(&partes, 0, 70).unwrap().robada.is_some());
    }

    #[test]
    fn una_parte_cuyo_tramo_cae_fuera_del_pool_no_asigna() {
        let partes = [Parte {
            canal: 0,
            nota_min: 0,
            nota_max: 127,
            voces: 2,
            primera_voz: 9,
            preset: 0,
        }];
        assert!(Repartidor::nueva(4).nota_on(&partes, 0, 60).is_none());
    }
}
