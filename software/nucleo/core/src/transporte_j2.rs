//! El transporte del J2 «por tic»: la maquina de una ranura, pura.
//!
//! Spec: `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v2.md`, §2.2.
//! **Es un prototipo de banco** (acta del 17-10, ficha 3): nada de esto es el
//! transporte firmado de D5.1 ni entra en el binario del instrumento.
//!
//! Una interrupcion periodica, el tic, lee el estado de cada ranura y le pregunta
//! a esta maquina que hacer: cerrar la transferencia en vuelo, esperar, darla por
//! vencida, o armar la siguiente. `fw` solo traduce la [`Salida`] a registros; la
//! politica de salud (`maestro_j2::Ranura`) sigue siendo de otro, que es el unico
//! que la llama (papel v2, §2.7).
//!
//! **El tiempo se cuenta en tics**, no en microsegundos: la edad de una
//! transferencia es cuantos tics lleva armada, y su plazo (D3) es
//! [`tics_de_plazo`] de los microsegundos que da `maestro_j2::plazo_us`. Con eso
//! el plazo y la rejilla son el mismo reloj (papel v2, §2.4).

use crate::maestro_j2::Evento;

/// Tics que `Vencida` espera a que arranque la recuperacion antes de dar la
/// ranura por muerta (papel v2, §2.5). ESTIMADO.
pub const COTA_VENCIDA_TICS: u8 = 2;
/// Tics que `Reiniciando` espera a que la recuperacion acabe. ESTIMADO.
pub const COTA_REINICIANDO_TICS: u8 = 4;

/// Cuantos tics dura un plazo de `plazo_us` microsegundos: el entero hacia
/// arriba, y nunca menos de uno (una transferencia armada en un tic se mira como
/// pronto en el siguiente). Satura en 255.
pub const fn tics_de_plazo(plazo_us: u32, periodo_us: u32) -> u8 {
    let n = plazo_us.div_ceil(periodo_us);
    if n == 0 {
        1
    } else if n > 255 {
        255
    } else {
        n as u8
    }
}

/// Cuantos tics se fundieron entre dos entradas de la ISR del tic (papel v2, §2.8): el
/// intervalo `delta` en ciclos contra el `periodo` en ciclos. Un temporizador de hardware
/// funde dos actualizaciones en una pendiente, y sin este testigo el giro perdido no deja
/// rastro. Cuenta cuando el intervalo pasa de 1,5 periodos: entonces faltan `redondeo(delta /
/// periodo) - 1` tics.
pub const fn tics_fusionados(delta: u32, periodo: u32) -> u32 {
    let (d, p) = (delta as u64, periodo as u64);
    if p == 0 || d * 2 < p * 3 {
        return 0;
    }
    ((d + p / 2) / p - 1) as u32
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Estado {
    /// El SPI esta apagado y la ranura espera una bajada.
    Libre,
    /// Una transferencia en vuelo: lleva `edad` tics y tiene `plazo_tics`.
    Armada { edad: u8, plazo_tics: u8 },
    /// El plazo vencio; espera a que la politica pida el reinicio y arranque.
    Vencida { espera: u8 },
    /// La recuperacion esta en curso.
    Reiniciando { espera: u8 },
    /// Se paso de las cotas: ya no arma ni sella. El IWDG del hub se queda sin sello.
    Muerta,
}

/// Lo que el tic lee de los registros de una ranura armada: `EOT` del SPI, y de
/// los dos canales del GPDMA el `TCF` y si hay algun error (`DTEF`, `USEF`, `ULEF`).
#[derive(Clone, Copy, Default, PartialEq, Eq, Debug)]
pub struct Lectura {
    pub eot: bool,
    pub tcf_rx: bool,
    pub tcf_tx: bool,
    pub error_dma: bool,
}

/// Lo que el tic sabe de una ranura en este instante.
#[derive(Clone, Copy, Default, PartialEq, Eq, Debug)]
pub struct Entrada {
    /// Solo cuenta si la ranura esta `Armada`.
    pub lectura: Lectura,
    /// R-MJ6: una ranura sin identidad no se arma.
    pub identidad: bool,
    /// Hay una bajada fresca en el buzon, y los tics del plazo de su mensaje.
    pub bajada: Option<u8>,
    /// La recuperacion (nivel 4) ya arranco.
    pub reinicio_en_curso: bool,
    /// La recuperacion termino y han pasado `T_GAP_REARME`.
    pub reinicio_hecho: bool,
}

/// Lo que la maquina cuenta sin que sea un evento de la politica.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Aviso {
    /// El tic no encontro bajada fresca y no armo.
    SinBajada,
    /// Un canal del GPDMA marco un error.
    ErrorDma,
    /// La ranura se paso de una cota y esta muerta.
    RanuraMuerta,
}

/// Lo que `fw` tiene que hacer. **`armar` implica sellar** (D5.4): el sello sube al
/// armar y solo entonces.
#[derive(Clone, Copy, Default, PartialEq, Eq, Debug)]
pub struct Salida {
    /// Cerrar la transferencia en vuelo (banderas, `SPE = 0`, `DMAEN` a cero) y
    /// publicar la subida.
    pub cerrar: bool,
    /// Armar con la bajada del buzon.
    pub armar: bool,
    /// Para la politica, en este orden.
    pub eventos: [Option<Evento>; 2],
    pub aviso: Option<Aviso>,
}

impl Salida {
    fn con_evento(mut self, e: Evento) -> Salida {
        let hueco = if self.eventos[0].is_none() { 0 } else { 1 };
        self.eventos[hueco] = Some(e);
        self
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Transporte {
    estado: Estado,
}

impl Transporte {
    pub const fn nuevo() -> Transporte {
        Transporte {
            estado: Estado::Libre,
        }
    }

    pub const fn estado(&self) -> Estado {
        self.estado
    }

    /// La ranura esta libre, o acaba de quedar libre en este tic: arma si puede.
    fn desde_libre(&mut self, e: &Entrada, s: Salida) -> Salida {
        match (e.identidad, e.bajada) {
            (true, Some(plazo_tics)) => {
                self.estado = Estado::Armada {
                    edad: 0,
                    plazo_tics,
                };
                Salida { armar: true, ..s }.con_evento(Evento::Armada)
            }
            (true, None) => {
                self.estado = Estado::Libre;
                Salida {
                    aviso: Some(Aviso::SinBajada),
                    ..s
                }
            }
            (false, _) => {
                self.estado = Estado::Libre;
                s
            }
        }
    }

    fn muerta(&mut self, s: Salida) -> Salida {
        self.estado = Estado::Muerta;
        Salida {
            aviso: Some(Aviso::RanuraMuerta),
            ..s
        }
    }

    /// Un tic. Lee `entrada`, cambia de estado y dice que hacer.
    pub fn paso(&mut self, e: Entrada) -> Salida {
        let s = Salida::default();
        match self.estado {
            Estado::Muerta => s,
            Estado::Libre => self.desde_libre(&e, s),
            Estado::Armada { edad, plazo_tics } => {
                let l = e.lectura;
                if l.error_dma {
                    // Un canal parado o con error no se da por bueno aunque haya EOT.
                    self.estado = Estado::Vencida { espera: 0 };
                    Salida {
                        cerrar: true,
                        aviso: Some(Aviso::ErrorDma),
                        ..s
                    }
                    .con_evento(Evento::PlazoVencido)
                } else if l.eot && l.tcf_rx && l.tcf_tx {
                    // El EOT y los dos canales acabados: lo que el tic encuentra es la
                    // verdad de este instante, tambien en el tic del vencimiento.
                    self.desde_libre(&e, Salida { cerrar: true, ..s }.con_evento(Evento::GiroOk))
                } else if edad.saturating_add(1) >= plazo_tics {
                    // El SPI se deja como esta: la recuperacion lo resetea.
                    self.estado = Estado::Vencida { espera: 0 };
                    s.con_evento(Evento::PlazoVencido)
                } else {
                    self.estado = Estado::Armada {
                        edad: edad + 1,
                        plazo_tics,
                    };
                    s
                }
            }
            Estado::Vencida { espera } => {
                if e.reinicio_hecho {
                    // La recuperacion dura unos 20 us: cuando llega el tic ya acabo.
                    self.desde_libre(&e, s)
                } else if e.reinicio_en_curso {
                    self.estado = Estado::Reiniciando { espera: 0 };
                    s
                } else if espera >= COTA_VENCIDA_TICS {
                    self.muerta(s)
                } else {
                    self.estado = Estado::Vencida { espera: espera + 1 };
                    s
                }
            }
            Estado::Reiniciando { espera } => {
                if e.reinicio_hecho {
                    self.desde_libre(&e, s)
                } else if espera >= COTA_REINICIANDO_TICS {
                    self.muerta(s)
                } else {
                    self.estado = Estado::Reiniciando { espera: espera + 1 };
                    s
                }
            }
        }
    }

    /// La escalada de D4.2 mato las transferencias en vuelo: la ranura que estaba
    /// `Armada` pasa a `Vencida` de una vez, sin esperar su plazo. Devuelve el evento
    /// para la politica, o `None` si no estaba en vuelo.
    pub fn declarar_vencida(&mut self) -> Option<Evento> {
        if matches!(self.estado, Estado::Armada { .. }) {
            self.estado = Estado::Vencida { espera: 0 };
            Some(Evento::PlazoVencido)
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const PERIODO: u32 = 125;

    fn bien() -> Lectura {
        Lectura {
            eot: true,
            tcf_rx: true,
            tcf_tx: true,
            error_dma: false,
        }
    }

    fn con_bajada(n: u8) -> Entrada {
        Entrada {
            identidad: true,
            bajada: Some(n),
            ..Entrada::default()
        }
    }

    fn armada(n: u8) -> Transporte {
        let mut t = Transporte::nuevo();
        let s = t.paso(con_bajada(n));
        assert!(s.armar, "el arranque de la prueba tiene que armar");
        t
    }

    // --- tics_de_plazo -----------------------------------------------------------

    #[test]
    fn un_plazo_es_el_entero_de_tics_hacia_arriba_y_nunca_menos_de_uno() {
        assert_eq!(tics_de_plazo(70, PERIODO), 1);
        assert_eq!(tics_de_plazo(125, PERIODO), 1);
        assert_eq!(tics_de_plazo(126, PERIODO), 2);
        assert_eq!(tics_de_plazo(226, PERIODO), 2);
        assert_eq!(tics_de_plazo(284, PERIODO), 3);
        assert_eq!(tics_de_plazo(0, PERIODO), 1);
        assert_eq!(tics_de_plazo(u32::MAX, PERIODO), 255);
    }

    // --- tics_fusionados -----------------------------------------------------------

    #[test]
    fn un_intervalo_normal_no_funde_ningun_tic() {
        // 125 us a 800 MHz son 100 000 ciclos.
        for delta in [0, 99_000, 100_000, 101_000, 149_999] {
            assert_eq!(tics_fusionados(delta, 100_000), 0, "delta {delta}");
        }
    }

    #[test]
    fn un_intervalo_de_mas_de_uno_y_medio_periodos_cuenta_los_que_faltan() {
        assert_eq!(tics_fusionados(150_000, 100_000), 1);
        assert_eq!(tics_fusionados(200_000, 100_000), 1);
        assert_eq!(tics_fusionados(249_999, 100_000), 1);
        assert_eq!(tics_fusionados(250_000, 100_000), 2);
        assert_eq!(tics_fusionados(300_000, 100_000), 2);
        assert_eq!(tics_fusionados(1_000_000, 100_000), 9);
    }

    #[test]
    fn el_periodo_cero_no_divide_por_cero() {
        assert_eq!(tics_fusionados(1_000, 0), 0);
    }

    // --- Libre -------------------------------------------------------------------

    #[test]
    fn libre_con_bajada_arma_y_lo_dice_a_la_politica() {
        let mut t = Transporte::nuevo();
        let s = t.paso(con_bajada(1));
        assert!(s.armar && !s.cerrar);
        assert_eq!(s.eventos, [Some(Evento::Armada), None]);
        assert_eq!(s.aviso, None);
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 0,
                plazo_tics: 1
            }
        );
    }

    #[test]
    fn libre_sin_bajada_cuenta_y_espera() {
        let mut t = Transporte::nuevo();
        let s = t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert!(!s.armar && !s.cerrar);
        assert_eq!(s.aviso, Some(Aviso::SinBajada));
        assert_eq!(s.eventos, [None, None]);
        assert_eq!(t.estado(), Estado::Libre);
    }

    #[test]
    fn una_ranura_sin_identidad_no_arma_ni_avisa() {
        let mut t = Transporte::nuevo();
        let s = t.paso(Entrada {
            identidad: false,
            bajada: Some(1),
            ..Entrada::default()
        });
        assert_eq!(s, Salida::default());
        assert_eq!(t.estado(), Estado::Libre);
    }

    // --- Armada ------------------------------------------------------------------

    #[test]
    fn el_giro_normal_cierra_y_rearma_en_el_mismo_tic() {
        let mut t = armada(1);
        let s = t.paso(Entrada {
            lectura: bien(),
            ..con_bajada(1)
        });
        assert!(s.cerrar && s.armar);
        assert_eq!(s.eventos, [Some(Evento::GiroOk), Some(Evento::Armada)]);
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 0,
                plazo_tics: 1
            }
        );
    }

    #[test]
    fn al_cerrar_sin_bajada_nueva_la_ranura_queda_libre_y_lo_cuenta() {
        let mut t = armada(1);
        let s = t.paso(Entrada {
            lectura: bien(),
            identidad: true,
            ..Entrada::default()
        });
        assert!(s.cerrar && !s.armar);
        assert_eq!(s.eventos, [Some(Evento::GiroOk), None]);
        assert_eq!(s.aviso, Some(Aviso::SinBajada));
        assert_eq!(t.estado(), Estado::Libre);
    }

    #[test]
    fn eot_sin_los_dos_tcf_no_cierra() {
        for (rx, tx) in [(false, false), (true, false), (false, true)] {
            let mut t = armada(2);
            let lectura = Lectura {
                eot: true,
                tcf_rx: rx,
                tcf_tx: tx,
                error_dma: false,
            };
            let s = t.paso(Entrada {
                lectura,
                ..con_bajada(1)
            });
            assert!(
                !s.cerrar && !s.armar,
                "rx={rx} tx={tx}: no puede cerrar un canal sin acabar"
            );
            assert_eq!(
                t.estado(),
                Estado::Armada {
                    edad: 1,
                    plazo_tics: 2
                }
            );
        }
    }

    #[test]
    fn los_dos_tcf_sin_eot_no_cierra() {
        let mut t = armada(2);
        let lectura = Lectura {
            eot: false,
            tcf_rx: true,
            tcf_tx: true,
            error_dma: false,
        };
        let s = t.paso(Entrada {
            lectura,
            ..con_bajada(1)
        });
        assert!(!s.cerrar);
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 1,
                plazo_tics: 2
            }
        );
    }

    #[test]
    fn un_plazo_de_un_tic_vence_en_el_primer_tic_sin_eot() {
        let mut t = armada(1);
        let s = t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert!(
            !s.cerrar && !s.armar,
            "el SPI se deja como esta, para la recuperacion"
        );
        assert_eq!(s.eventos, [Some(Evento::PlazoVencido), None]);
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
    }

    #[test]
    fn un_plazo_de_dos_tics_vence_en_el_segundo() {
        let mut t = armada(2);
        let s = t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert_eq!(s.eventos, [None, None]);
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 1,
                plazo_tics: 2
            }
        );
        let s = t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert_eq!(s.eventos, [Some(Evento::PlazoVencido), None]);
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
    }

    #[test]
    fn un_eot_en_el_tic_del_vencimiento_se_acepta() {
        // Papel v2, §2.4: el plazo es "terminar en N tics"; lo que el tic encuentra al
        // leer es la verdad de ese instante, y una trama buena no se da por vencida.
        let mut t = armada(1);
        let s = t.paso(Entrada {
            lectura: bien(),
            ..con_bajada(1)
        });
        assert!(s.cerrar);
        assert_eq!(s.eventos[0], Some(Evento::GiroOk));
    }

    #[test]
    fn un_error_del_dma_cierra_lo_cuenta_y_vence_aunque_haya_eot() {
        let mut t = armada(2);
        let lectura = Lectura {
            error_dma: true,
            ..bien()
        };
        let s = t.paso(Entrada {
            lectura,
            ..con_bajada(1)
        });
        assert!(s.cerrar && !s.armar);
        assert_eq!(s.aviso, Some(Aviso::ErrorDma));
        assert_eq!(s.eventos, [Some(Evento::PlazoVencido), None]);
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
    }

    // --- Vencida y Reiniciando -------------------------------------------------------

    fn vencida() -> Transporte {
        let mut t = armada(1);
        t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
        t
    }

    #[test]
    fn vencida_pasa_a_reiniciando_cuando_la_recuperacion_arranca() {
        let mut t = vencida();
        let s = t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        assert_eq!(s, Salida::default());
        assert_eq!(t.estado(), Estado::Reiniciando { espera: 0 });
    }

    #[test]
    fn vencida_con_la_recuperacion_ya_hecha_vuelve_y_arma_en_el_mismo_tic() {
        // La recuperacion dura unos 20 us: cuando llega el tic siguiente ya acabo.
        let mut t = vencida();
        let entrada = Entrada {
            reinicio_en_curso: true,
            reinicio_hecho: true,
            ..con_bajada(1)
        };
        let s = t.paso(entrada);
        assert!(s.armar && !s.cerrar);
        assert_eq!(s.eventos, [Some(Evento::Armada), None]);
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 0,
                plazo_tics: 1
            }
        );
    }

    #[test]
    fn vencida_sin_que_arranque_la_recuperacion_pasa_a_muerta_pasada_la_cota() {
        let mut t = vencida();
        for _ in 0..COTA_VENCIDA_TICS {
            let s = t.paso(Entrada {
                identidad: true,
                ..Entrada::default()
            });
            assert_eq!(s.aviso, None);
        }
        let s = t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert_eq!(s.aviso, Some(Aviso::RanuraMuerta));
        assert_eq!(t.estado(), Estado::Muerta);
    }

    #[test]
    fn reiniciando_acabado_devuelve_la_ranura_y_arma_si_hay_bajada() {
        let mut t = vencida();
        t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        let s = t.paso(Entrada {
            reinicio_en_curso: true,
            reinicio_hecho: true,
            ..con_bajada(2)
        });
        assert!(s.armar);
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 0,
                plazo_tics: 2
            }
        );
    }

    #[test]
    fn reiniciando_acabado_sin_bajada_queda_libre_y_lo_cuenta() {
        let mut t = vencida();
        t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        let s = t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            reinicio_hecho: true,
            ..Entrada::default()
        });
        assert!(!s.armar);
        assert_eq!(s.aviso, Some(Aviso::SinBajada));
        assert_eq!(t.estado(), Estado::Libre);
    }

    #[test]
    fn reiniciando_que_no_acaba_pasa_a_muerta_pasada_la_cota() {
        let mut t = vencida();
        t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        for _ in 0..COTA_REINICIANDO_TICS {
            let s = t.paso(Entrada {
                identidad: true,
                reinicio_en_curso: true,
                ..Entrada::default()
            });
            assert_eq!(s.aviso, None);
        }
        let s = t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        assert_eq!(s.aviso, Some(Aviso::RanuraMuerta));
        assert_eq!(t.estado(), Estado::Muerta);
    }

    // --- Muerta y la escalada -----------------------------------------------------------

    #[test]
    fn una_ranura_muerta_no_arma_ni_cierra_ni_avisa_nunca() {
        let mut t = vencida();
        for _ in 0..=COTA_VENCIDA_TICS {
            t.paso(Entrada {
                identidad: true,
                ..Entrada::default()
            });
        }
        assert_eq!(t.estado(), Estado::Muerta);
        let todo = Entrada {
            lectura: bien(),
            identidad: true,
            bajada: Some(1),
            reinicio_en_curso: true,
            reinicio_hecho: true,
        };
        for _ in 0..50 {
            assert_eq!(t.paso(todo), Salida::default());
            assert_eq!(t.estado(), Estado::Muerta);
        }
    }

    #[test]
    fn la_escalada_declara_vencida_solo_a_la_que_estaba_en_vuelo() {
        let mut t = armada(2);
        assert_eq!(t.declarar_vencida(), Some(Evento::PlazoVencido));
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
        // Ya vencida, o libre, o muerta: no hay nada que declarar.
        assert_eq!(t.declarar_vencida(), None);
        let mut libre = Transporte::nuevo();
        assert_eq!(libre.declarar_vencida(), None);
        assert_eq!(libre.estado(), Estado::Libre);
    }

    // --- propiedades --------------------------------------------------------------------

    /// Un generador pseudoaleatorio de bolsillo: el contrato no necesita un crate.
    struct Xorshift(u64);
    impl Xorshift {
        fn sig(&mut self) -> u64 {
            self.0 ^= self.0 << 13;
            self.0 ^= self.0 >> 7;
            self.0 ^= self.0 << 17;
            self.0
        }
        fn azar(&mut self, de_cada: u64) -> bool {
            self.sig().is_multiple_of(de_cada)
        }
    }

    fn entrada_al_azar(r: &mut Xorshift) -> Entrada {
        Entrada {
            lectura: Lectura {
                eot: r.azar(2),
                tcf_rx: !r.azar(5),
                tcf_tx: !r.azar(5),
                error_dma: r.azar(40),
            },
            identidad: !r.azar(30),
            bajada: if r.azar(8) {
                None
            } else {
                Some(1 + (r.sig() % 3) as u8)
            },
            reinicio_en_curso: r.azar(3),
            reinicio_hecho: r.azar(4),
        }
    }

    #[test]
    fn nunca_se_arma_sobre_una_transferencia_en_vuelo() {
        for semilla in 1..=20u64 {
            let mut r = Xorshift(semilla.wrapping_mul(0x9E37_79B9_7F4A_7C15));
            let mut t = Transporte::nuevo();
            for _ in 0..5000 {
                let antes = t.estado();
                let s = t.paso(entrada_al_azar(&mut r));
                if s.armar {
                    let libre_o_cerrando = matches!(
                        antes,
                        Estado::Libre | Estado::Vencida { .. } | Estado::Reiniciando { .. }
                    ) || (matches!(antes, Estado::Armada { .. })
                        && s.cerrar);
                    assert!(libre_o_cerrando, "armo desde {antes:?} sin cerrar: {s:?}");
                }
                if matches!(antes, Estado::Muerta) {
                    assert_eq!(s, Salida::default());
                }
            }
        }
    }

    #[test]
    fn cada_armado_acaba_en_un_giro_bueno_o_en_un_plazo_vencido() {
        // Conservacion: Armada = GiroOk + PlazoVencido + (1 si hay una en vuelo al final).
        for semilla in 1..=20u64 {
            let mut r = Xorshift(semilla.wrapping_mul(0xD1B5_4A32_D192_ED03));
            let mut t = Transporte::nuevo();
            let (mut armadas, mut buenos, mut vencidos) = (0u32, 0u32, 0u32);
            for _ in 0..5000 {
                let s = t.paso(entrada_al_azar(&mut r));
                for e in s.eventos.into_iter().flatten() {
                    match e {
                        Evento::Armada => armadas += 1,
                        Evento::GiroOk => buenos += 1,
                        Evento::PlazoVencido => vencidos += 1,
                        otro => panic!("evento que el transporte no emite: {otro:?}"),
                    }
                }
            }
            let en_vuelo = matches!(t.estado(), Estado::Armada { .. }) as u32;
            assert_eq!(armadas, buenos + vencidos + en_vuelo, "semilla {semilla}");
        }
    }

    #[test]
    fn seis_ranuras_son_independientes() {
        // H-1: una ranura colgada no cambia lo que hacen las otras cinco.
        let mut r_ref = Xorshift(77);
        let mut r_mix = Xorshift(77);
        let mut a: [Transporte; 6] = [Transporte::nuevo(); 6];
        let mut b: [Transporte; 6] = [Transporte::nuevo(); 6];
        for _ in 0..2000 {
            for k in 0..6 {
                let e = entrada_al_azar(&mut r_ref);
                let e2 = entrada_al_azar(&mut r_mix);
                assert_eq!(e, e2);
                let sa = a[k].paso(e);
                // En la segunda corrida, la ranura 2 nunca recibe lectura buena: se cuelga.
                let e_b = if k == 2 {
                    Entrada {
                        lectura: Lectura::default(),
                        ..e2
                    }
                } else {
                    e2
                };
                let sb = b[k].paso(e_b);
                if k != 2 {
                    assert_eq!(sa, sb, "la ranura {k} cambio por la colgada");
                }
            }
        }
    }
}
