//! El generador de envolvente del modulo de Voz: la maquina de cuatro etapas,
//! cerrada entre dos bordes. Papel:
//! `docs/superpowers/specs/2026-09-02-generador-de-envolvente-design.md`.
//!
//! - La forma es la del circuito de la tesis (`docs/modules/06-adsr.md`): un
//!   condensador que carga y descarga. Cada etapa es `y += k * (destino - y)`
//!   con `k = 1 - exp(-dt / tau)`, calculada UNA vez al capturar (§2).
//! - Las etapas de duracion conocida terminan POR CUENTA DE TICKS y ajustan el
//!   nivel exacto al terminar. La junta corrio el fin por umbral en `f32` y no
//!   terminaba en 11 de 36 casillas del barrido (§2, §12).
//! - El ataque es una carga RC truncada: apunta a 1,5 (el pico es 2/3 del
//!   destino, el umbral del 555 de la tesis) y se corta al llegar (§2.1).
//! - Decaimiento y relajacion se miden en RT60: el tiempo en que el recorrido
//!   cae a la milesima (§2.2). La relajacion se cuenta desde el nivel de
//!   partida, porque su duracion depende de el.
//! - El sostenido NO se captura y aplica en el tick, sin filtro: S-12 lo hizo
//!   vivo y R-M1 prohibe suavizar dentro del modulo (§2.3).
//! - El tick de `Generadores` es el UNICO dueno del estado: drena la cola en
//!   orden y luego avanza los treinta y dos generadores (§3.5, decision 14).

use crate::escritor::{amplitud, factores_paneo, ganancia_fuerza};
use crate::fuerza::Fuerza;

/// voz-total §3.1: la tasa de render de la clase lenta.
pub const F_RENDER_HZ: u32 = 10_000;
/// Un milisegundo son diez ticks, exactos.
pub const TICKS_POR_MS: u32 = 10;
/// Papel §6: el nivel por debajo del cual una envolvente se declara terminada.
/// Constante del MODELO: hoy coincide con el LSB de 16 bits; si el DAC cambia
/// de ancho, esta no lo sigue.
pub const NIVEL_OCIOSO: f32 = 1.0 / 65_536.0;
/// Papel §2.1: el ataque apunta a 1,5 y se trunca en 1.
pub const DESTINO_ATAQUE: f32 = 1.5;

const DT_MS: f32 = 0.1;
const LN_3: f32 = 1.098_612_3;
const LN_1000: f32 = 6.907_755_3;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Etapa {
    Ocioso,
    Ataque,
    Decaimiento,
    Sostenido,
    Relajacion,
}

/// Los tres tiempos que se capturan al borde (papel §3.3). Rangos firmados en
/// §7: ataque y decaimiento 1..=10 000 ms, relajacion 1..=20 000 ms; el modulo
/// no los valida, los valida el descriptor.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Tiempos {
    pub ataque_ms: u32,
    pub decaimiento_ms: u32,
    pub relajacion_ms: u32,
}

fn k(tau_ms: f32) -> f32 {
    1.0 - libm::expf(-DT_MS / tau_ms)
}

pub struct Generador {
    etapa: Etapa,
    y: f32,
    k: f32,
    restantes: u32,
    disparo: bool,
    tiempos: Tiempos,
}

impl Generador {
    pub const fn nuevo() -> Self {
        Generador {
            etapa: Etapa::Ocioso,
            y: 0.0,
            k: 0.0,
            restantes: 0,
            disparo: false,
            tiempos: Tiempos {
                ataque_ms: 0,
                decaimiento_ms: 0,
                relajacion_ms: 0,
            },
        }
    }

    pub fn etapa(&self) -> Etapa {
        self.etapa
    }

    pub fn nivel(&self) -> f32 {
        self.y
    }

    /// Captura `tiempos` y arranca el ataque desde `desde` (§2.1, §3.2). Con
    /// `desde >= 1` no hay ataque: entra en decaimiento. `disparo` es el borde
    /// `dispara` (§3.1).
    pub fn abrir(&mut self, tiempos: Tiempos, desde: f32, disparo: bool) {
        self.tiempos = tiempos;
        self.disparo = disparo;
        let desde = desde.clamp(0.0, 1.0);
        if desde >= 1.0 {
            self.y = 1.0;
            self.entrar_en_decaimiento(None);
            return;
        }
        self.y = desde;
        // Los rangos firmados (§7) empiezan en 1 ms y los valida el descriptor;
        // un cero que se cuele no tiene que desbordar la cuenta de ticks. Vale
        // como 1 ms, igual que en bahia.rs lo fuera de rango no entra en panico.
        let ataque_ms = tiempos.ataque_ms.max(1);
        let tau = ataque_ms as f32 / LN_3;
        self.k = k(tau);
        let ticks = ataque_ms as f32
            * TICKS_POR_MS as f32
            * libm::logf((DESTINO_ATAQUE - desde) / (DESTINO_ATAQUE - 1.0))
            / LN_3;
        self.restantes = (libm::roundf(ticks) as u32).max(1);
        self.etapa = Etapa::Ataque;
    }

    /// Relajacion desde el nivel actual (§2.2). Sobre un ocioso no hace nada.
    pub fn cerrar(&mut self) {
        if self.etapa == Etapa::Ocioso {
            return;
        }
        if self.y <= NIVEL_OCIOSO {
            self.y = 0.0;
            self.etapa = Etapa::Ocioso;
            return;
        }
        let relajacion_ms = self.tiempos.relajacion_ms.max(1);
        let tau = relajacion_ms as f32 / LN_1000;
        self.k = k(tau);
        let ticks = relajacion_ms as f32 * TICKS_POR_MS as f32 * libm::logf(self.y / NIVEL_OCIOSO)
            / LN_1000;
        self.restantes = (libm::ceilf(ticks) as u32).max(1);
        self.etapa = Etapa::Relajacion;
    }

    /// `sostenido` es el parametro vivo, en milesimas; `None` significa
    /// «todavia no lo se» (solo lo usa `abrir` desde >= 1, que no puede saltar
    /// el decaimiento sin conocerlo): entra en decaimiento y el primer tick
    /// decide.
    fn entrar_en_decaimiento(&mut self, sostenido: Option<f32>) {
        if let Some(s) = sostenido {
            if s >= 1.0 {
                self.y = 1.0;
                self.terminar_decaimiento(s);
                return;
            }
        }
        let decaimiento_ms = self.tiempos.decaimiento_ms.max(1);
        let tau = decaimiento_ms as f32 / LN_1000;
        self.k = k(tau);
        self.restantes = decaimiento_ms * TICKS_POR_MS;
        self.etapa = Etapa::Decaimiento;
    }

    fn terminar_decaimiento(&mut self, s: f32) {
        self.y = s;
        self.etapa = Etapa::Sostenido;
        if self.disparo {
            self.cerrar();
        }
    }

    /// Un tick de 100 us con el sostenido vivo. Devuelve el nivel tras el tick.
    pub fn tick(&mut self, sostenido_milesimas: u16) -> f32 {
        let s = sostenido_milesimas.min(1000) as f32 / 1000.0;
        match self.etapa {
            Etapa::Ocioso => {}
            Etapa::Ataque => {
                self.y += self.k * (DESTINO_ATAQUE - self.y);
                self.restantes -= 1;
                if self.restantes == 0 {
                    self.y = 1.0;
                    self.entrar_en_decaimiento(Some(s));
                }
            }
            Etapa::Decaimiento => {
                if s >= 1.0 {
                    // el sostenido vivo subio a 1: no queda distancia que caer
                    self.y = 1.0;
                    self.terminar_decaimiento(s);
                } else {
                    self.y += self.k * (s - self.y);
                    self.restantes -= 1;
                    if self.restantes == 0 {
                        self.terminar_decaimiento(s);
                    }
                }
            }
            Etapa::Sostenido => {
                self.y = s;
            }
            Etapa::Relajacion => {
                self.y -= self.k * self.y;
                self.restantes -= 1;
                if self.restantes == 0 {
                    self.y = 0.0;
                    self.etapa = Etapa::Ocioso;
                }
            }
        }
        self.y
    }
}

/// Papel §1: dieciseis canales.
pub const CANALES: usize = 16;
/// Papel §3.5: un acorde de dieciseis voces abriendose y cerrandose dos veces
/// dentro de un tick. La cola misma (SPSC, un productor en la ISR del J2 y un
/// consumidor en el tick) la construye el firmware con `heapless::spsc::Queue`;
/// aqui solo se declara su capacidad y lo que transporta.
pub const CAPACIDAD_COLA: usize = 64;
/// Papel §3.4, decision 12: una nota reparada por la red de R-E10 entra con
/// fuerza plena. Constante, no memoria: el modelo no publica ningun otro valor.
pub const FUERZA_REPARACION: Fuerza = Fuerza(u16::MAX);

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Borde {
    Abre,
    Cierra,
    Dispara,
}

/// Los parametros por voz del papel §7. Los tiempos se capturan al borde; el
/// sostenido, el paneo y la cantidad son vivos (§3.3).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Parametros {
    pub vca: Tiempos,
    pub vca_sostenido: u16,
    pub filtro: Tiempos,
    pub filtro_sostenido: u16,
    pub sensibilidad_fuerza: u16,
    pub filtro_cantidad: i16,
    pub paneo: u16,
}

/// Lo que entra por la cola (§3.5). Lo encola la ISR del J2; lo drena el tick.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Entrada {
    /// `secuencia` es la del sobre de su trama (cabecera del J2, D4).
    Evento {
        canal: u8,
        borde: Borde,
        fuerza: Fuerza,
        secuencia: u16,
    },
    Parametros {
        canal: u8,
        parametros: Parametros,
    },
    /// Una tupla de `SET` (cabecera del J2, D4): el campo que nombra el indice
    /// de la tabla del dialecto. El rango lo valida el dialecto.
    Parametro {
        canal: u8,
        indice: u8,
        valor: i32,
    },
    /// R-E10: la mascara de compuertas (`abre`/`cierra`, nunca disparos) y la
    /// secuencia del ultimo `EVENTO` que el cerebro emitio antes de armarla
    /// (cabecera del J2, D4).
    Compuerta {
        mascara: u16,
        contador: u16,
    },
    /// El watchdog de trama (voz-total §9.2). No toca `ultimo_evento`.
    SoltarTodo,
    /// El firmware latcheo el crosspoint: los canales en conmutacion se sueltan.
    Conmutado,
}

/// Lo que sale por tick: por canal, las dos amplitudes del VCA (L, R) y el
/// nivel de la envolvente del filtro, en 16 bits.
pub struct Salida {
    pub vca: [[u16; 2]; CANALES],
    pub filtro: [u16; CANALES],
}

struct Canal {
    vca: Generador,
    filtro: Generador,
    compuerta: bool,
    g_v: f32,
    l: f32,
    r: f32,
    parametros: Parametros,
    diferido: Option<(Borde, Fuerza)>,
}

impl Canal {
    fn nuevo(parametros: Parametros) -> Self {
        let (l, r) = factores_paneo(parametros.paneo);
        Canal {
            vca: Generador::nuevo(),
            filtro: Generador::nuevo(),
            compuerta: false,
            g_v: 0.0,
            l,
            r,
            parametros,
            diferido: None,
        }
    }

    /// Papel §3.1-3.3: captura, continuidad en la amplitud, compuerta propia.
    fn aplicar(&mut self, borde: Borde, fuerza: Fuerza) {
        match borde {
            Borde::Cierra => {
                self.vca.cerrar();
                self.filtro.cerrar();
                self.compuerta = false;
            }
            Borde::Abre | Borde::Dispara => {
                let p = self.parametros;
                let g_nueva = ganancia_fuerza(fuerza, p.sensibilidad_fuerza);
                let desde = if self.vca.etapa() == Etapa::Ocioso {
                    0.0
                } else {
                    let a0 = self.vca.nivel() * self.g_v;
                    if g_nueva <= 0.0 {
                        if a0 > 0.0 {
                            1.0
                        } else {
                            0.0
                        }
                    } else {
                        (a0 / g_nueva).min(1.0)
                    }
                };
                let disparo = borde == Borde::Dispara;
                self.vca.abrir(p.vca, desde, disparo);
                let desde_f = self.filtro.nivel();
                self.filtro.abrir(p.filtro, desde_f, disparo);
                self.g_v = g_nueva;
                self.compuerta = borde == Borde::Abre;
            }
        }
    }
}

pub struct Generadores {
    canales: [Canal; CANALES],
    /// La mayor secuencia de `EVENTO` aceptada (cabecera del J2, D4).
    ultimo_evento: u16,
    en_conmutacion: u16,
}

/// `a` es anterior a `b` en la aritmetica de 16 bits con vuelta.
fn anterior(a: u16, b: u16) -> bool {
    (a.wrapping_sub(b) as i16) < 0
}

impl Generadores {
    /// Todos los canales con `parametros`; ningun valor por defecto en core.
    pub fn nuevos(parametros: Parametros) -> Self {
        Generadores {
            canales: core::array::from_fn(|_| Canal::nuevo(parametros)),
            ultimo_evento: 0,
            en_conmutacion: 0,
        }
    }

    /// Un borde sobre un canal: se difiere si el canal esta en conmutacion y el
    /// borde abre (papel §6); un `cierra` aplica siempre y borra lo diferido.
    fn borde(&mut self, canal: u8, borde: Borde, fuerza: Fuerza) {
        let i = canal as usize;
        if i >= CANALES {
            return;
        }
        let c = &mut self.canales[i];
        match borde {
            Borde::Cierra => {
                c.diferido = None;
                c.aplicar(Borde::Cierra, fuerza);
            }
            _ if self.en_conmutacion & (1 << i) != 0 => c.diferido = Some((borde, fuerza)),
            _ => c.aplicar(borde, fuerza),
        }
    }

    fn aplicar_entrada(&mut self, e: Entrada) {
        match e {
            Entrada::Evento {
                canal,
                borde,
                fuerza,
                secuencia,
            } => {
                if anterior(self.ultimo_evento, secuencia) {
                    self.ultimo_evento = secuencia;
                }
                self.borde(canal, borde, fuerza);
            }
            Entrada::Parametros { canal, parametros } => {
                if let Some(c) = self.canales.get_mut(canal as usize) {
                    c.parametros = parametros;
                    let (l, r) = factores_paneo(parametros.paneo);
                    c.l = l;
                    c.r = r;
                }
            }
            Entrada::Parametro {
                canal,
                indice,
                valor,
            } => {
                let Some(c) = self.canales.get_mut(canal as usize) else {
                    return;
                };
                let p = &mut c.parametros;
                match indice {
                    0 => p.vca.ataque_ms = valor as u32,
                    1 => p.vca.decaimiento_ms = valor as u32,
                    2 => p.vca.relajacion_ms = valor as u32,
                    3 => p.vca_sostenido = valor as u16,
                    4 => p.filtro.ataque_ms = valor as u32,
                    5 => p.filtro.decaimiento_ms = valor as u32,
                    6 => p.filtro.relajacion_ms = valor as u32,
                    7 => p.filtro_sostenido = valor as u16,
                    8 => p.sensibilidad_fuerza = valor as u16,
                    9 => p.filtro_cantidad = valor as i16,
                    10 => {
                        p.paneo = valor as u16;
                        (c.l, c.r) = factores_paneo(p.paneo);
                    }
                    _ => {}
                }
            }
            Entrada::Compuerta { mascara, contador } => {
                if anterior(contador, self.ultimo_evento) {
                    return; // un bloque viejo no hace nada (cabecera del J2, D4)
                }
                for i in 0..CANALES {
                    let bit = mascara & (1 << i) != 0;
                    let propia = self.canales[i].compuerta;
                    if bit && !propia {
                        self.borde(i as u8, Borde::Abre, FUERZA_REPARACION);
                    } else if !bit && propia {
                        self.borde(i as u8, Borde::Cierra, Fuerza(0));
                    }
                }
            }
            Entrada::SoltarTodo => {
                for c in self.canales.iter_mut() {
                    c.diferido = None;
                    c.aplicar(Borde::Cierra, Fuerza(0));
                }
            }
            Entrada::Conmutado => {
                self.en_conmutacion = 0;
                for c in self.canales.iter_mut() {
                    if let Some((borde, fuerza)) = c.diferido.take() {
                        c.aplicar(borde, fuerza);
                    }
                }
            }
        }
    }

    /// Papel §3.5: drena en orden, avanza, escribe. El unico dueno del estado.
    pub fn tick(&mut self, entradas: &[Entrada]) -> Salida {
        for e in entradas {
            self.aplicar_entrada(*e);
        }
        let mut salida = Salida {
            vca: [[0; 2]; CANALES],
            filtro: [0; CANALES],
        };
        for (i, c) in self.canales.iter_mut().enumerate() {
            let y = c.vca.tick(c.parametros.vca_sostenido);
            let y_f = c.filtro.tick(c.parametros.filtro_sostenido);
            salida.vca[i] = [amplitud(y, c.g_v, c.l), amplitud(y, c.g_v, c.r)];
            salida.filtro[i] = libm::roundf(y_f.clamp(0.0, 1.0) * 65535.0) as u16;
        }
        salida
    }

    /// Papel §6: bit en 1 = el generador de VCA del canal esta ocioso.
    pub fn en_silencio(&self) -> u16 {
        let mut m = 0u16;
        for (i, c) in self.canales.iter().enumerate() {
            if c.vca.etapa() == Etapa::Ocioso {
                m |= 1 << i;
            }
        }
        m
    }

    /// Papel §6: `Commit.cambian`. Un `abre`/`dispara` sobre esos canales espera
    /// en su ranura hasta `Entrada::Conmutado`; un `cierra` aplica en el acto.
    pub fn bloquear_apertura(&mut self, cambian: u16) {
        self.en_conmutacion |= cambian;
    }

    /// La compuerta propia de cada canal (§3.4), para el descriptor y los tests.
    pub fn compuertas(&self) -> u16 {
        let mut m = 0u16;
        for (i, c) in self.canales.iter().enumerate() {
            if c.compuerta {
                m |= 1 << i;
            }
        }
        m
    }

    /// La etapa del generador de VCA, que es la que define el estado del canal
    /// (§3.1).
    pub fn etapa(&self, canal: u8) -> Etapa {
        self.canales
            .get(canal as usize)
            .map_or(Etapa::Ocioso, |c| c.vca.etapa())
    }

    /// La secuencia que `COMPUERTA` compara; sube por `ESTADO_VOZ`.
    pub fn ultimo_evento(&self) -> u16 {
        self.ultimo_evento
    }

    /// Los parametros del canal, para el descriptor y los tests.
    pub fn parametros(&self, canal: u8) -> Option<Parametros> {
        self.canales.get(canal as usize).map(|c| c.parametros)
    }
}
