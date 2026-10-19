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
///
/// v2 decia 2: el planificador y la recuperacion van por debajo de USB y pantalla (P2), y una
/// retencion de 350 us de P2 coincidiendo con un cuelgue bastaba para matar la ranura y, con
/// ella, el instrumento (revision de Halberg del 17-10, hallazgo 1). 100 tics son 12,5 ms.
pub const COTA_VENCIDA_TICS: u16 = 100;
/// Tics que `Reiniciando` espera a que la recuperacion acabe (v2: 4). ESTIMADO. Las dos cotas
/// suman 25 ms, la mitad de lo que el modulo aguanta sin tramas (400 giros, ~50 ms): una
/// ranura se da por muerta antes de que el modulo se rinda solo.
pub const COTA_REINICIANDO_TICS: u16 = 100;

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

/// Lo que una entrada del tic dice del tiempo: cuantos periodos van desde la anterior, y si
/// la cuenta no salio limpia.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Periodos {
    pub n: u32,
    /// El contador de ciclos esta parado, o la diferencia entre dos eventos no es un multiplo
    /// del periodo dentro de la tolerancia: se cuenta uno.
    pub anomalo: bool,
}

/// El reloj del tic contado desde el instante del evento de actualizacion, no desde la entrada
/// (papel v3, §2.7, candidata K2).
///
/// En cada entrada el tic lee el contador de su temporizador (lo que lleva contado desde la
/// ultima actualizacion) y despues el contador libre de ciclos. Restar lo primero de lo segundo
/// da el instante de la actualizacion, y la diferencia entre dos de esos instantes es un
/// multiplo exacto del periodo por tarde que llegue la entrada: su redondeo no se equivoca, y
/// la suma de periodos es la de la pared aunque se fundan actualizaciones.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct RelojDelTic {
    periodo: u32,
    ciclos_por_cuenta: u32,
    tolerancia: u32,
    anterior: Option<(u32, u32)>,
}

impl RelojDelTic {
    /// `periodo` y `tolerancia` en ciclos del contador libre; `ciclos_por_cuenta`, los ciclos de
    /// una cuenta del temporizador del tic.
    pub const fn nuevo(periodo: u32, ciclos_por_cuenta: u32, tolerancia: u32) -> RelojDelTic {
        RelojDelTic {
            periodo,
            ciclos_por_cuenta,
            tolerancia,
            anterior: None,
        }
    }

    /// Una entrada del tic: `cnt` es el contador del temporizador y `ciclos` el contador libre,
    /// leidos en ese orden.
    pub fn entrada(&mut self, cnt: u32, ciclos: u32) -> Periodos {
        let act = ciclos.wrapping_sub(cnt.wrapping_mul(self.ciclos_por_cuenta));
        let anomalo = Periodos {
            n: 1,
            anomalo: true,
        };
        let Some((ciclos_ant, act_ant)) = self.anterior.replace((ciclos, act)) else {
            return Periodos {
                n: 1,
                anomalo: false,
            };
        };
        if ciclos == ciclos_ant || self.periodo == 0 {
            // El contador libre no avanza: nadie lo habilito, o el nucleo duerme y lo para.
            return anomalo;
        }
        // Con signo: una reentrada por la misma actualizacion puede dar unos ciclos de menos.
        let d = i64::from(act.wrapping_sub(act_ant) as i32);
        let p = i64::from(self.periodo);
        let n = (d + p / 2).div_euclid(p);
        if n < 0 || (d - n * p).unsigned_abs() > u64::from(self.tolerancia) {
            return anomalo;
        }
        Periodos {
            n: n as u32,
            anomalo: false,
        }
    }
}

/// El contador de tics de 32 bits del tic, extendido a 64 por quien lo lee (el planificador).
///
/// A 8 kHz el contador de 32 bits da la vuelta a los 6,2 dias, y la politica recibe como
/// reloj `tics x periodo`: sin extenderlo, ese reloj da un paso atras de 6,2 dias y
/// `inestable()` (que resta con `saturating_sub`) se queda en `true` hasta que el reloj
/// alcance otra vez sus marcas viejas (revision de Halberg del 17-10, hallazgo 3).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Reloj64 {
    epoca: u32,
    ultimo: u32,
}

impl Reloj64 {
    pub const fn nuevo() -> Reloj64 {
        Reloj64 {
            epoca: 0,
            ultimo: 0,
        }
    }

    /// `bajo` es el contador de 32 bits. Hay que llamarla al menos una vez por vuelta de 32 bits
    /// (6,2 dias a 8 kHz); el planificador la llama en cada tic.
    pub fn extiende(&mut self, bajo: u32) -> u64 {
        if bajo < self.ultimo {
            self.epoca = self.epoca.wrapping_add(1);
        }
        self.ultimo = bajo;
        (u64::from(self.epoca) << 32) | u64::from(bajo)
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Estado {
    /// El SPI esta apagado y la ranura espera una bajada.
    Libre,
    /// Una transferencia en vuelo: lleva `edad` periodos del tic y tiene `plazo_tics`.
    Armada { edad: u16, plazo_tics: u8 },
    /// El plazo vencio; espera a que la politica pida el reinicio y arranque.
    Vencida { espera: u16 },
    /// La recuperacion esta en curso.
    Reiniciando { espera: u16 },
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
    /// La escalada reseteo el GPDMA1 y los canales de esta ranura aun no estan reprogramados.
    pub sucia: bool,
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
    cota_vencida: u16,
    cota_reiniciando: u16,
}

impl Transporte {
    pub const fn nuevo() -> Transporte {
        Transporte::con_cotas(COTA_VENCIDA_TICS, COTA_REINICIANDO_TICS)
    }

    /// Como [`Transporte::nuevo`], con otras cotas de espera para `Vencida` y `Reiniciando`.
    pub const fn con_cotas(vencida: u16, reiniciando: u16) -> Transporte {
        Transporte {
            estado: Estado::Libre,
            cota_vencida: vencida,
            cota_reiniciando: reiniciando,
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

    /// Un tic de un periodo. Lee `entrada`, cambia de estado y dice que hacer.
    pub fn paso(&mut self, e: Entrada) -> Salida {
        self.avanza(e, 1)
    }

    /// Un tic que trae `periodos` periodos del reloj del tic ([`RelojDelTic`]): la edad y las
    /// esperas avanzan en periodos, no en entradas (papel v3, §2.7). Una espera muere en la
    /// entrada que la lleva mas alla de su cota.
    pub fn avanza(&mut self, e: Entrada, periodos: u16) -> Salida {
        // Papel v3, §2.2 (K3): con la marca puesta no se lee ni se arma, y la marca gana a la
        // recuperacion; solo cuentan el plazo y las cotas. Sin identidad, `Libre` espera sin
        // avisar.
        let e = if e.sucia {
            Entrada {
                sucia: true,
                ..Entrada::default()
            }
        } else {
            e
        };
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
                } else if edad.saturating_add(periodos) >= u16::from(plazo_tics) {
                    // El SPI se deja como esta: la recuperacion lo resetea.
                    self.estado = Estado::Vencida { espera: 0 };
                    s.con_evento(Evento::PlazoVencido)
                } else {
                    self.estado = Estado::Armada {
                        edad: edad + periodos,
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
                } else if espera.saturating_add(periodos) > self.cota_vencida {
                    self.muerta(s)
                } else {
                    self.estado = Estado::Vencida {
                        espera: espera + periodos,
                    };
                    s
                }
            }
            Estado::Reiniciando { espera } => {
                if e.reinicio_hecho {
                    self.desde_libre(&e, s)
                } else if espera.saturating_add(periodos) > self.cota_reiniciando {
                    self.muerta(s)
                } else {
                    self.estado = Estado::Reiniciando {
                        espera: espera + periodos,
                    };
                    s
                }
            }
        }
    }

    /// La escalada de D4.2 mato las transferencias en vuelo: la ranura que estaba
    /// `Armada` pasa a `Vencida` de una vez, sin esperar su plazo. Devuelve el
    /// `PlazoAjeno` para la politica, o `None` si no estaba en vuelo.
    pub fn declarar_vencida(&mut self) -> Option<Evento> {
        if matches!(self.estado, Estado::Armada { .. }) {
            self.estado = Estado::Vencida { espera: 0 };
            Some(Evento::PlazoAjeno)
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

    // --- RelojDelTic (K2) ---------------------------------------------------------------

    /// 125 us a 800 MHz; el temporizador cuenta cada 4 ciclos.
    const P_CICLOS: u32 = 100_000;
    const CPC: u32 = 4;
    const TOL: u32 = 64;
    /// Ciclos entre leer el contador del temporizador y leer el contador libre.
    const LECTURA: u32 = 12;

    /// Las entradas del tic con estos retrasos, uno por actualizacion, sobre una pared que
    /// empieza en `t0` ciclos: una entrada que llega despues de la actualizacion siguiente
    /// funde a esa en ella, como el `UIF` de un temporizador. Devuelve, por entrada, la suma
    /// de periodos del reloj y la de la pared desde la primera.
    fn corre(t0: u32, retrasos: &[u32]) -> (Vec<(u64, u64)>, u32) {
        let mut r = RelojDelTic::nuevo(P_CICLOS, CPC, TOL);
        let mut out = Vec::new();
        let mut anomalos = 0;
        let (mut suma, mut primera) = (0u64, None);
        let mut k = 0usize;
        while k < retrasos.len() {
            let t_act = u64::from(t0) + k as u64 * u64::from(P_CICLOS);
            let t_cnt = t_act + u64::from(retrasos[k]);
            // La actualizacion mas reciente antes de leer el contador.
            let ultima = k + (retrasos[k] / P_CICLOS) as usize;
            let desde = t_cnt - (u64::from(t0) + ultima as u64 * u64::from(P_CICLOS));
            let cnt = (desde / u64::from(CPC)) as u32;
            let ciclos = (t_cnt + u64::from(LECTURA)) as u32;
            let p = r.entrada(cnt, ciclos);
            anomalos += u32::from(p.anomalo);
            let base = *primera.get_or_insert(ultima);
            suma += u64::from(p.n);
            out.push((suma, (ultima - base) as u64 + 1));
            k = ultima + 1;
        }
        (out, anomalos)
    }

    #[test]
    fn el_reloj_del_tic_cuenta_la_pared_por_tarde_que_lleguen_las_entradas() {
        // Retrasos de 0 a 1,9 periodos con un generador fijo, y sobre la vuelta de 32 bits del
        // contador libre (5,4 s a 800 MHz).
        let mut x: u32 = 0x1234_5678;
        let retrasos: Vec<u32> = (0..20_000)
            .map(|_| {
                x = x.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
                (x >> 8) % (P_CICLOS * 19 / 10)
            })
            .collect();
        let (out, anomalos) = corre(u32::MAX - 5 * P_CICLOS, &retrasos);
        assert_eq!(anomalos, 0);
        for (i, (reloj, pared)) in out.iter().enumerate() {
            assert_eq!(reloj, pared, "entrada {i}");
        }
    }

    #[test]
    fn uno_de_cada_dos_tics_tarde_no_hace_correr_al_reloj() {
        // Tercera pasada de la junta (Halberg N2): con uno de cada dos tics entre 63 y 124 us
        // tarde, sumar el redondeo de cada intervalo entre entradas corre x1,5 y la cota de
        // 25 ms vence a los 16,75 ms de pared. 25 ms son 200 periodos.
        let retrasos: Vec<u32> = (0..200u32)
            .map(|k| {
                if k % 2 == 0 {
                    0
                } else {
                    50_400 + (k % 31) * 1_600
                }
            })
            .collect();
        let (out, _) = corre(1_000, &retrasos);
        assert_eq!(out.last().copied(), Some((200, 200)));
    }

    #[test]
    fn una_reentrada_por_la_misma_actualizacion_no_cuenta_periodos() {
        // La ISR vuelve a entrar porque la escritura que borra `UIF` no llego a tiempo: el
        // temporizador sigue contando desde la misma actualizacion.
        let mut r = RelojDelTic::nuevo(P_CICLOS, CPC, TOL);
        r.entrada(250, 1_000 + 250 * CPC);
        assert_eq!(
            r.entrada(300, 1_000 + 300 * CPC),
            Periodos {
                n: 0,
                anomalo: false
            }
        );
    }

    #[test]
    fn una_reentrada_que_lee_unos_ciclos_antes_tampoco_cuenta_periodos() {
        // El contador del temporizador redondea hacia abajo: el instante sale hasta una cuenta
        // antes o despues, y la diferencia puede ser negativa.
        let mut r = RelojDelTic::nuevo(P_CICLOS, CPC, TOL);
        r.entrada(250, 1_000 + 250 * CPC + 3);
        assert_eq!(
            r.entrada(300, 1_000 + 300 * CPC),
            Periodos {
                n: 0,
                anomalo: false
            }
        );
    }

    #[test]
    fn un_evento_anterior_al_ultimo_cuenta_uno_y_lo_marca() {
        let mut r = RelojDelTic::nuevo(P_CICLOS, CPC, TOL);
        r.entrada(0, 10 * P_CICLOS);
        assert_eq!(
            r.entrada(0, 9 * P_CICLOS),
            Periodos {
                n: 1,
                anomalo: true
            }
        );
    }

    #[test]
    fn con_el_contador_de_ciclos_parado_cuenta_uno_y_lo_marca() {
        // Sin sonda, nadie habilita `DWT_CYCCNT` (R-H9): el contador libre lee siempre lo mismo.
        let mut r = RelojDelTic::nuevo(P_CICLOS, CPC, TOL);
        r.entrada(10, 0);
        for cnt in [12, 9, 15, 10] {
            assert_eq!(
                r.entrada(cnt, 0),
                Periodos {
                    n: 1,
                    anomalo: true
                }
            );
        }
    }

    #[test]
    fn una_diferencia_que_no_es_un_multiplo_del_periodo_cuenta_uno_y_lo_marca() {
        let mut r = RelojDelTic::nuevo(P_CICLOS, CPC, TOL);
        r.entrada(0, 0);
        assert_eq!(
            r.entrada(0, P_CICLOS * 3 / 2),
            Periodos {
                n: 1,
                anomalo: true
            }
        );
        // Y la siguiente cuenta otra vez desde esa, sin arrastrar el error.
        assert_eq!(
            r.entrada(0, P_CICLOS * 3 / 2 + 2 * P_CICLOS + TOL - 1),
            Periodos {
                n: 2,
                anomalo: false
            }
        );
    }

    #[test]
    fn la_primera_entrada_cuenta_un_periodo() {
        let mut r = RelojDelTic::nuevo(P_CICLOS, CPC, TOL);
        assert_eq!(
            r.entrada(40, 7_777),
            Periodos {
                n: 1,
                anomalo: false
            }
        );
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
            sucia: false,
        };
        for _ in 0..50 {
            assert_eq!(t.paso(todo), Salida::default());
            assert_eq!(t.estado(), Estado::Muerta);
        }
    }

    #[test]
    fn la_escalada_declara_vencida_solo_a_la_que_estaba_en_vuelo() {
        let mut t = armada(2);
        assert_eq!(t.declarar_vencida(), Some(Evento::PlazoAjeno));
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
        // Ya vencida, o libre, o muerta: no hay nada que declarar.
        assert_eq!(t.declarar_vencida(), None);
        let mut libre = Transporte::nuevo();
        assert_eq!(libre.declarar_vencida(), None);
        assert_eq!(libre.estado(), Estado::Libre);
    }

    // --- cotas ---------------------------------------------------------------------------

    #[test]
    fn nuevo_lleva_las_cotas_por_defecto() {
        assert_eq!(
            Transporte::nuevo(),
            Transporte::con_cotas(COTA_VENCIDA_TICS, COTA_REINICIANDO_TICS)
        );
    }

    #[test]
    fn la_cota_por_defecto_aguanta_una_retencion_larga_del_planificador() {
        // Un planificador retenido 5 ms (40 tics) por debajo de USB y pantalla: la ranura espera
        // y la recuperacion arranca en cuanto el planificador corre; no muere.
        let mut t = vencida();
        for _ in 0..40 {
            let s = t.paso(Entrada {
                identidad: true,
                ..Entrada::default()
            });
            assert_eq!(s.aviso, None);
        }
        let s = t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        assert_eq!(s, Salida::default());
        assert_eq!(t.estado(), Estado::Reiniciando { espera: 0 });
    }

    #[test]
    fn reiniciando_con_la_cota_por_defecto_aguanta_una_retencion_larga_de_la_recuperacion() {
        let mut t = vencida();
        t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        for _ in 0..40 {
            let s = t.paso(Entrada {
                identidad: true,
                reinicio_en_curso: true,
                ..Entrada::default()
            });
            assert_eq!(s.aviso, None);
        }
        let s = t.paso(Entrada {
            reinicio_en_curso: true,
            reinicio_hecho: true,
            ..con_bajada(1)
        });
        assert!(s.armar);
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 0,
                plazo_tics: 1
            }
        );
    }

    fn vencida_con(mut t: Transporte) -> Transporte {
        t.paso(con_bajada(1));
        t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
        t
    }

    #[test]
    fn con_cotas_propias_vencida_muere_a_su_hora() {
        let mut t = vencida_con(Transporte::con_cotas(1, 9));
        let s = t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert_eq!(s.aviso, None);
        assert_eq!(t.estado(), Estado::Vencida { espera: 1 });
        let s = t.paso(Entrada {
            identidad: true,
            ..Entrada::default()
        });
        assert_eq!(s.aviso, Some(Aviso::RanuraMuerta));
        assert_eq!(t.estado(), Estado::Muerta);
    }

    #[test]
    fn con_cotas_propias_reiniciando_muere_a_su_hora() {
        let mut t = vencida_con(Transporte::con_cotas(9, 1));
        t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        assert_eq!(t.estado(), Estado::Reiniciando { espera: 0 });
        let s = t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        assert_eq!(s.aviso, None);
        let s = t.paso(Entrada {
            identidad: true,
            reinicio_en_curso: true,
            ..Entrada::default()
        });
        assert_eq!(s.aviso, Some(Aviso::RanuraMuerta));
        assert_eq!(t.estado(), Estado::Muerta);
    }

    // --- sucia (K3) -------------------------------------------------------------------------

    /// Todo lo que haria salir a la ranura de su estado, con la marca puesta.
    fn sucia_con_todo() -> Entrada {
        Entrada {
            lectura: bien(),
            identidad: true,
            bajada: Some(1),
            reinicio_en_curso: true,
            reinicio_hecho: true,
            sucia: true,
        }
    }

    #[test]
    fn libre_y_sucia_espera_sin_armar_ni_avisar() {
        let mut t = Transporte::nuevo();
        for _ in 0..1000 {
            assert_eq!(t.avanza(sucia_con_todo(), 3), Salida::default());
            assert_eq!(t.estado(), Estado::Libre);
        }
    }

    #[test]
    fn armada_y_sucia_no_lee_y_el_plazo_sigue_contando() {
        let mut t = armada(3);
        assert_eq!(t.avanza(sucia_con_todo(), 1), Salida::default());
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 1,
                plazo_tics: 3
            }
        );
        let s = t.avanza(sucia_con_todo(), 2);
        assert!(!s.cerrar && !s.armar);
        assert_eq!(s.eventos[0], Some(Evento::PlazoVencido));
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
    }

    #[test]
    fn vencida_y_sucia_no_vuelve_ni_reinicia_y_la_cota_sigue() {
        let mut t = vencida_con(Transporte::con_cotas(5, 9));
        assert_eq!(t.avanza(sucia_con_todo(), 3), Salida::default());
        assert_eq!(t.estado(), Estado::Vencida { espera: 3 });
        let s = t.avanza(sucia_con_todo(), 3);
        assert_eq!(s.aviso, Some(Aviso::RanuraMuerta));
        assert_eq!(t.estado(), Estado::Muerta);
    }

    #[test]
    fn reiniciando_y_sucia_no_vuelve_y_la_cota_sigue() {
        let mut t = vencida_con(Transporte::con_cotas(9, 5));
        t.paso(Entrada {
            reinicio_en_curso: true,
            ..sin_nada()
        });
        assert_eq!(t.estado(), Estado::Reiniciando { espera: 0 });
        assert_eq!(t.avanza(sucia_con_todo(), 5), Salida::default());
        assert_eq!(t.estado(), Estado::Reiniciando { espera: 5 });
        let s = t.avanza(sucia_con_todo(), 1);
        assert_eq!(s.aviso, Some(Aviso::RanuraMuerta));
        assert_eq!(t.estado(), Estado::Muerta);
    }

    #[test]
    fn al_quitar_la_marca_la_ranura_sigue_como_siempre() {
        let mut t = vencida_con(Transporte::nuevo());
        t.avanza(sucia_con_todo(), 1);
        let s = t.avanza(
            Entrada {
                sucia: false,
                ..sucia_con_todo()
            },
            1,
        );
        assert!(
            s.armar,
            "con la marca quitada, la HECHA devuelve la ranura y arma"
        );
    }

    // --- periodos (K2) ---------------------------------------------------------------------

    fn sin_nada() -> Entrada {
        Entrada {
            identidad: true,
            ..Entrada::default()
        }
    }

    #[test]
    fn una_entrada_de_varios_periodos_envejece_la_transferencia_en_todos() {
        let mut t = armada(5);
        t.avanza(sin_nada(), 3);
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 3,
                plazo_tics: 5
            }
        );
        let s = t.avanza(sin_nada(), 2);
        assert_eq!(s.eventos[0], Some(Evento::PlazoVencido));
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
    }

    #[test]
    fn una_entrada_sin_periodos_no_envejece_nada() {
        let mut t = armada(1);
        assert_eq!(t.avanza(sin_nada(), 0), Salida::default());
        assert_eq!(
            t.estado(),
            Estado::Armada {
                edad: 0,
                plazo_tics: 1
            }
        );
        let mut t = vencida_con(Transporte::con_cotas(0, 0));
        t.avanza(sin_nada(), 0);
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
    }

    #[test]
    fn un_salto_enorme_de_periodos_no_desborda() {
        let mut t = armada(255);
        t.avanza(sin_nada(), u16::MAX);
        assert_eq!(t.estado(), Estado::Vencida { espera: 0 });
        t.avanza(sin_nada(), COTA_VENCIDA_TICS);
        assert_eq!(
            t.estado(),
            Estado::Vencida {
                espera: COTA_VENCIDA_TICS
            }
        );
        t.avanza(sin_nada(), u16::MAX);
        assert_eq!(t.estado(), Estado::Muerta);
    }

    #[test]
    fn las_cotas_cuentan_periodos_y_no_entradas() {
        // La misma cota, partida en entradas de 1 a 7 periodos al azar: la ranura muere en la
        // entrada que pasa de la cota, ni antes ni despues. Con un periodo por entrada es la
        // cuenta de siempre: muere en el tic `cota + 1` desde que entro en el estado.
        let mut r = Xorshift(0x9E37_79B9_7F4A_7C15);
        for _ in 0..400 {
            let cota = (r.sig() % 400) as u16;
            for reiniciando in [false, true] {
                let (cv, cr) = if reiniciando {
                    (400, cota)
                } else {
                    (cota, 400)
                };
                let mut t = vencida_con(Transporte::con_cotas(cv, cr));
                let e = Entrada {
                    reinicio_en_curso: reiniciando,
                    ..sin_nada()
                };
                if reiniciando {
                    t.avanza(e, 1);
                    assert_eq!(t.estado(), Estado::Reiniciando { espera: 0 });
                }
                let mut total = 0u32;
                loop {
                    let n = 1 + (r.sig() % 7) as u16;
                    let s = t.avanza(e, n);
                    let antes = total;
                    total += u32::from(n);
                    if t.estado() == Estado::Muerta {
                        assert_eq!(s.aviso, Some(Aviso::RanuraMuerta));
                        assert!(
                            antes <= u32::from(cota) && total > u32::from(cota),
                            "cota {cota}"
                        );
                        break;
                    }
                    assert!(total <= u32::from(cota), "cota {cota}: vive con {total}");
                }
            }
        }
    }

    // --- Reloj64 ---------------------------------------------------------------------------

    #[test]
    fn el_reloj_de_64_bits_empieza_en_cero_y_sigue_al_de_32() {
        let mut r = Reloj64::nuevo();
        assert_eq!(r.extiende(0), 0);
        assert_eq!(r.extiende(1), 1);
        assert_eq!(r.extiende(1000), 1000);
        assert_eq!(r.extiende(1000), 1000);
    }

    #[test]
    fn el_reloj_de_64_bits_no_da_marcha_atras_cuando_el_de_32_da_la_vuelta() {
        let mut r = Reloj64::nuevo();
        assert_eq!(r.extiende(u32::MAX - 1), u64::from(u32::MAX) - 1);
        assert_eq!(r.extiende(u32::MAX), u64::from(u32::MAX));
        assert_eq!(r.extiende(0), 1 << 32);
        assert_eq!(r.extiende(1), (1 << 32) + 1);
    }

    #[test]
    fn el_reloj_de_64_bits_sigue_a_un_contador_verdadero_con_pasos_de_casi_una_vuelta() {
        for semilla in 1..=20u64 {
            let mut azar = Xorshift(semilla.wrapping_mul(0x9E37_79B9_7F4A_7C15));
            let mut r = Reloj64::nuevo();
            let mut verdadero = 0u64;
            for _ in 0..2000 {
                // Pasos de 0 a 2^32 - 1: lo mas que el reloj puede pedir entre dos llamadas.
                verdadero += azar.sig() & u64::from(u32::MAX);
                assert_eq!(r.extiende(verdadero as u32), verdadero, "semilla {semilla}");
            }
        }
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
            sucia: r.azar(10),
        }
    }

    #[test]
    fn nunca_se_arma_sobre_una_transferencia_en_vuelo() {
        for semilla in 1..=20u64 {
            let mut r = Xorshift(semilla.wrapping_mul(0x9E37_79B9_7F4A_7C15));
            // Las cotas de v2: con las de hoy las secuencias al azar casi nunca llegan a `Muerta`.
            let mut t = Transporte::con_cotas(2, 4);
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
            let mut t = Transporte::con_cotas(2, 4);
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
