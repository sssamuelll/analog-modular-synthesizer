//! §7.2. Lo que ninguna herramienta de masterizacion puede hacer.
//!
//! Un plugin de masterizacion ve una mezcla terminada: detecta una resonancia
//! y solo puede **adivinar** de donde viene, asi que lo unico que sabe hacer es
//! atenuar esa frecuencia para todo por igual. El SAM17 **sabe**: conoce sus
//! voces, que nota toca cada una en este instante, y donde esta el corte y la
//! resonancia de cada filtro. Asi que el arreglo no es un notch en la salida,
//! es la perilla de resonancia de esa voz.
//!
//! # Dos niveles
//!
//! - **Nivel 1 — inferencia.** Gratis, continua, sin cambiar nada de lo que
//!   suena. Se calcula la serie armonica esperada de cada voz y la frecuencia
//!   resonante de cada filtro, y se puntua contra el pico observado.
//! - **Nivel 2 — sonda causal.** Solo cuando el nivel 1 queda ambiguo:
//!   `sonda_sugerida` dice que dos voces perturbar, y de ahi en adelante es el
//!   motor de §7.6.
//!
//! # El decaimiento armonico es suave a proposito
//!
//! Con 110 Hz y 220 Hz sonando, un pico en 440 es el 4.º armonico de una y el
//! 2.º de la otra. Musicalmente **no se puede distinguir**, asi que un
//! decaimiento agresivo daria una respuesta segura y falsa. Lo que se entrega
//! es la hipotesis **con su confianza**, nunca una certeza fabricada: un
//! agente que recibe «probablemente la voz 2, 0.7» puede pedir la sonda,
//! preguntarte, o abstenerse. Uno que recibe «la voz 2» a secas tarde o
//! temprano te arregla el sonido equivocado con total aplomo.

/// Hasta que armonico se busca. Mas arriba no queda energia util.
pub const N_ARMONICOS: u8 = 16;
/// Cuanto puede desviarse un candidato antes de dejar de puntuar, en cents.
pub const TOL_CENTS: f32 = 35.0;
/// «Ambiguo» tiene definicion, no criterio de barra: si la primera hipotesis
/// no se separa de la segunda por este margen, es ambigua. Punto.
pub const MARGEN: f32 = 0.20;
/// Por debajo de esto el pico no encaja con nada que conozcamos.
pub const PUNTAJE_MINIMO: f32 = 0.10;

#[derive(Clone, Copy, PartialEq, Debug)]
pub struct EstadoVozAudio {
    pub sonando: bool,
    pub f_hz: f32,
    pub f_corte_hz: f32,
    /// 0.0 = plano, 1.0 = a punto de oscilar.
    pub resonancia: f32,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Causa {
    Armonico { voz: u8, n: u8 },
    Resonancia { voz: u8 },
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub struct Hipotesis {
    pub causa: Causa,
    pub puntaje: f32,
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Atribucion {
    Probable {
        h: Hipotesis,
        confianza: f32,
    },
    /// Las dos mejores, empatadas dentro del margen.
    Ambigua(Hipotesis, Hipotesis),
    Desconocida,
}

/// Cuanto se castiga un armonico alto. Suave: ver la nota del modulo.
fn decaimiento(n: u8) -> f32 {
    1.0 / (1.0 + 0.05 * (n as f32 - 1.0))
}

/// Que tan cerca esta `f` de `objetivo`, en la escala de cents.
fn cercania(f: f32, objetivo: f32) -> f32 {
    if f <= 0.0 || objetivo <= 0.0 {
        return 0.0;
    }
    let cents = 1200.0 * libm::log2f(f / objetivo);
    let x = cents / TOL_CENTS;
    libm::expf(-(x * x))
}

pub fn atribuir(pico_hz: f32, voces: &[EstadoVozAudio]) -> Atribucion {
    let mut mejor: Option<Hipotesis> = None;
    let mut segunda: Option<Hipotesis> = None;

    let mut considerar = |h: Hipotesis| {
        if h.puntaje < PUNTAJE_MINIMO {
            return;
        }
        match mejor {
            Some(m) if h.puntaje <= m.puntaje => {
                if segunda.is_none_or(|s| h.puntaje > s.puntaje) {
                    segunda = Some(h);
                }
            }
            _ => {
                segunda = mejor;
                mejor = Some(h);
            }
        }
    };

    for (i, v) in voces.iter().enumerate() {
        if !v.sonando {
            continue;
        }
        let voz = i as u8;

        // Nivel 1a: el pico como armonico de esta voz.
        if v.f_hz > 0.0 {
            let n = libm::roundf(pico_hz / v.f_hz).clamp(1.0, N_ARMONICOS as f32);
            considerar(Hipotesis {
                causa: Causa::Armonico { voz, n: n as u8 },
                puntaje: cercania(pico_hz, n * v.f_hz) * decaimiento(n as u8),
            });
        }

        // Nivel 1b: el pico como resonancia del filtro de esta voz. Un filtro
        // sin resonancia no se lleva el merito.
        considerar(Hipotesis {
            causa: Causa::Resonancia { voz },
            puntaje: cercania(pico_hz, v.f_corte_hz) * v.resonancia,
        });
    }

    let Some(m) = mejor else {
        return Atribucion::Desconocida;
    };
    let Some(s) = segunda else {
        return Atribucion::Probable {
            h: m,
            confianza: 1.0,
        };
    };

    let sep = (m.puntaje - s.puntaje) / m.puntaje;
    if sep < MARGEN {
        Atribucion::Ambigua(m, s)
    } else {
        Atribucion::Probable {
            h: m,
            confianza: sep,
        }
    }
}

/// Que dos voces perturbar para desempatar (nivel 2). Es la entrada al motor
/// de §7.6: si al mover la voz 2 el pico se mueve, es de la voz 2 — y eso ya
/// es causalidad, no correlacion de estado.
pub fn sonda_sugerida(a: &Atribucion) -> Option<[u8; 2]> {
    match a {
        Atribucion::Ambigua(x, y) => Some([voz_de(&x.causa), voz_de(&y.causa)]),
        _ => None,
    }
}

fn voz_de(c: &Causa) -> u8 {
    match c {
        Causa::Armonico { voz, .. } | Causa::Resonancia { voz } => *voz,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn voz(f: f32) -> EstadoVozAudio {
        EstadoVozAudio {
            sonando: true,
            f_hz: f,
            f_corte_hz: 20_000.0,
            resonancia: 0.0,
        }
    }

    #[test]
    fn el_fundamental_de_una_voz_sola_es_una_respuesta_clara() {
        match atribuir(440.0, &[voz(440.0), voz(113.0)]) {
            Atribucion::Probable {
                h:
                    Hipotesis {
                        causa: Causa::Armonico { voz, n },
                        ..
                    },
                confianza,
            } => {
                assert_eq!((voz, n), (0, 1));
                assert!(confianza > 0.5, "confianza {confianza}");
            }
            otro => panic!("esto no tenia por que ser dudoso: {otro:?}"),
        }
    }

    #[test]
    fn dos_voces_que_comparten_un_armonico_dan_confianza_baja() {
        // §9, fila "Atribucion". 440 es el 4.o de 110 y el 2.o de 220: nadie
        // puede saberlo, y el motor tampoco puede fingir que si.
        let a = atribuir(440.0, &[voz(110.0), voz(220.0)]);
        assert!(
            matches!(a, Atribucion::Ambigua(_, _)),
            "dio una certeza fabricada: {a:?}"
        );
        let sonda = sonda_sugerida(&a).expect("si es ambigua, hay algo que sondear");
        assert_eq!([sonda[0].min(sonda[1]), sonda[0].max(sonda[1])], [0, 1]);
    }

    #[test]
    fn una_resonancia_marcada_gana_al_armonico_lejano() {
        let voces = [
            EstadoVozAudio {
                sonando: true,
                f_hz: 110.0,
                f_corte_hz: 1_500.0,
                resonancia: 0.95,
            },
            voz(97.0),
        ];
        assert!(matches!(
            atribuir(1_500.0, &voces),
            Atribucion::Probable {
                h: Hipotesis {
                    causa: Causa::Resonancia { voz: 0 },
                    ..
                },
                ..
            }
        ));
    }

    #[test]
    fn un_filtro_sin_resonancia_no_se_lleva_el_merito() {
        let voces = [EstadoVozAudio {
            sonando: true,
            f_hz: 110.0,
            f_corte_hz: 1_500.0,
            resonancia: 0.0,
        }];
        assert!(!matches!(
            atribuir(1_500.0, &voces),
            Atribucion::Probable {
                h: Hipotesis {
                    causa: Causa::Resonancia { .. },
                    ..
                },
                ..
            }
        ));
    }

    #[test]
    fn una_voz_callada_no_se_atribuye() {
        let mut v = voz(440.0);
        v.sonando = false;
        assert!(matches!(atribuir(440.0, &[v]), Atribucion::Desconocida));
    }

    #[test]
    fn sin_voces_sonando_no_se_atribuye_nada() {
        assert!(matches!(atribuir(440.0, &[]), Atribucion::Desconocida));
    }

    #[test]
    fn un_pico_que_no_encaja_con_nada_se_declara_desconocido() {
        // 7331 Hz contra una voz de 110: el armonico mas cercano es el 16.o
        // (1760) y se queda cortisimo. No hay nada que reportar.
        assert!(matches!(
            atribuir(7_331.0, &[voz(110.0)]),
            Atribucion::Desconocida
        ));
    }

    #[test]
    fn la_sonda_solo_se_sugiere_cuando_hay_empate() {
        assert!(sonda_sugerida(&atribuir(440.0, &[voz(440.0)])).is_none());
        assert!(sonda_sugerida(&Atribucion::Desconocida).is_none());
    }

    #[test]
    fn dos_voces_al_unisono_desafinado_son_indistinguibles() {
        // El caso mas comun de todos, y el que mas facil daria una respuesta
        // segura y equivocada.
        let a = atribuir(440.0, &[voz(110.0), voz(110.4)]);
        assert!(matches!(a, Atribucion::Ambigua(_, _)), "{a:?}");
    }
}
