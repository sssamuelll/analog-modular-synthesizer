//! El dialecto de la Voz, version 1: los mensajes de bajada y los registros de
//! subida.
//!
//! Papel: `docs/superpowers/specs/2026-09-02-cabecera-j2-design.md`, D4 (los
//! cinco mensajes y la tabla de indices), D6 (la subida), D8 (lo que el
//! receptor rechaza), §3.2 y §3.3 (los bytes). Van con ellos los universales,
//! `NADA` y `HOLA` en los dos sentidos y `SALUD`, para que todo tipo tenga
//! respuesta. `JACKS`, `MEDIDA` y `LOG` no: su carga es de otros papeles (§7).
//!
//! La traduccion a `envolvente::Entrada` (D9) cubre `HOLA`, `EVENTO`,
//! `COMPUERTA` y `SET`. El tono de arranque del `EVENTO` y el `TONO` son del
//! camino del tono, y `BAHIA` es de la barrera, que no estan en el generador.
//!
//! `Receptor` es el lado del modulo: la sesion (D5), las cuentas de rechazo
//! (D8) y el registro que publica (D6).

use crate::bahia::{Imagen, CANALES};
use crate::envolvente::{Borde, Entrada};
use crate::fuerza::Fuerza;
use crate::j2::{self, Cabecera, ErrorTrama};

/// El numero del dialecto en `HOLA` (D5): `0` es el legado, `1` la Voz v1.
pub const DIALECTO: u8 = 1;

/// Tuplas por `SET` (D4): los once parametros de una voz, o uno de las
/// dieciseis, en una trama.
pub const MAX_ESCRITURAS: usize = 16;

/// La carga mas larga del dialecto: un `SET` lleno.
const CARGA_MAX: usize = 6 * MAX_ESCRITURAS;

/// Los bytes de registro, con sobre, que el cerebro muestrea en cada giro a
/// `F_SUBIDA` (D6.3). Ningun registro de la Voz v1 la pasa (R-C5).
pub const VENTANA_SUBIDA: usize = 24;

/// La carga de subida mas larga: `SALUD`.
const CARGA_SUBIDA: usize = 12;

/// La tabla de indices de D4: el rango firme de cada parametro, por indice
/// (generador §7, decision 11; el paneo, D4). Un indice fuera de la tabla o un
/// valor fuera de su rango rechazan la trama entera.
pub const RANGOS: [(i32, i32); 11] = [
    (1, 10_000),     // 0  vca.ataque_ms
    (1, 10_000),     // 1  vca.decaimiento_ms
    (1, 20_000),     // 2  vca.relajacion_ms
    (0, 1_000),      // 3  vca_sostenido
    (1, 10_000),     // 4  filtro.ataque_ms
    (1, 10_000),     // 5  filtro.decaimiento_ms
    (1, 20_000),     // 6  filtro.relajacion_ms
    (0, 1_000),      // 7  filtro_sostenido
    (0, 1_000),      // 8  sensibilidad_fuerza
    (-4_800, 4_800), // 9  filtro_cantidad, cents
    (0, 1_000),      // 10 paneo
];

// Los tipos de bajada (§3.1).
const NADA: u8 = 0x00;
const HOLA: u8 = 0x01;
const EVENTO: u8 = 0x10;
const TONO: u8 = 0x11;
const COMPUERTA: u8 = 0x12;
const BAHIA: u8 = 0x13;
const SET: u8 = 0x14;

// Los tipos de subida (§3.1): el bit alto puesto.
const NADA_SUBE: u8 = 0x80;
const HOLA_SUBE: u8 = 0x81;
const SALUD: u8 = 0x82;
const ESTADO_VOZ: u8 = 0x93;

/// Una escritura de `SET`: el parametro `indice` de la instancia, con el valor
/// en los 32 bits con signo del modelo (`param.rs`).
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub struct Escritura {
    pub instancia: u8,
    pub indice: u8,
    pub valor: i32,
}

/// Un mensaje de bajada.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Mensaje {
    /// Un giro sin mensaje, para muestrear la subida.
    Nada,
    /// Solo la forma: si la version y el dialecto valen lo decide la sesion
    /// (D5).
    Hola {
        version: u8,
        dialecto: u8,
    },
    /// `destino` son los bits 23..8 de `ParamId`: el modulo usa la instancia,
    /// los cuatro bits bajos, y la ruta le es opaca (D3).
    Evento {
        destino: u16,
        borde: Borde,
        fuerza: u16,
        tono: u16,
    },
    /// Los tonos por instancia. Solo viajan los que marca la mascara, y los
    /// demas vuelven a cero; `0xFFFF` es el bloque completo, la red de las
    /// deltas.
    Tono {
        mascara: u16,
        tonos: [u16; CANALES as usize],
    },
    /// `contador` es la secuencia del ultimo `EVENTO` que el cerebro emitio
    /// antes de armar el bloque.
    Compuerta {
        mascara: u16,
        contador: u16,
    },
    Bahia(Imagen),
    /// Las primeras `n` escrituras, de 1 a 16; las demas vuelven a cero.
    Set {
        n: u8,
        escrituras: [Escritura; MAX_ESCRITURAS],
    },
}

impl Mensaje {
    /// Escribe la trama con su sobre y devuelve cuantos bytes ocupa. `None`,
    /// sin tocar `out`, si el receptor la rechazaria o no cabe en `out`.
    pub fn codificar(&self, tabla: &[u16; 256], secuencia: u16, out: &mut [u8]) -> Option<usize> {
        let mut carga = [0u8; CARGA_MAX];
        let (tipo, n) = self.carga(&mut carga)?;
        leer(tipo, &carga[..n]).ok()?;
        j2::codificar(tabla, tipo, secuencia, &carga[..n], out)
    }

    /// Lo que un mensaje aceptado deja en la cola del generador (D8), con
    /// `secuencia`, la del sobre de su trama. Un `SET` da una entrada por tupla,
    /// en orden; un `HOLA` aceptado es una sesion nueva (D5).
    pub fn entradas(&self, secuencia: u16) -> impl Iterator<Item = Entrada> + '_ {
        let una = match *self {
            Mensaje::Hola { .. } => Some(Entrada::Sesion),
            Mensaje::Evento {
                destino,
                borde,
                fuerza,
                ..
            } => Some(Entrada::Evento {
                canal: (destino & 0xF) as u8,
                borde,
                fuerza: Fuerza(fuerza),
                secuencia,
            }),
            Mensaje::Compuerta { mascara, contador } => {
                Some(Entrada::Compuerta { mascara, contador })
            }
            _ => None,
        };
        let tuplas = match self {
            Mensaje::Set { n, escrituras } => escrituras.get(..usize::from(*n)).unwrap_or(&[]),
            _ => &[],
        };
        una.into_iter()
            .chain(tuplas.iter().map(|e| Entrada::Parametro {
                canal: e.instancia,
                indice: e.indice,
                valor: e.valor,
            }))
    }

    fn carga(&self, b: &mut [u8; CARGA_MAX]) -> Option<(u8, usize)> {
        Some(match *self {
            Mensaje::Nada => (NADA, 0),
            Mensaje::Hola { version, dialecto } => {
                b[0] = version;
                b[1] = dialecto;
                (HOLA, 2)
            }
            Mensaje::Evento {
                destino,
                borde,
                fuerza,
                tono,
            } => {
                b[0..2].copy_from_slice(&destino.to_le_bytes());
                b[2] = match borde {
                    Borde::Abre => 0,
                    Borde::Cierra => 1,
                    Borde::Dispara => 2,
                };
                b[3..5].copy_from_slice(&fuerza.to_le_bytes());
                b[5..7].copy_from_slice(&tono.to_le_bytes());
                (EVENTO, 7)
            }
            Mensaje::Tono { mascara, tonos } => {
                b[0..2].copy_from_slice(&mascara.to_le_bytes());
                let mut n = 2;
                for (i, tono) in tonos.iter().enumerate() {
                    if mascara & (1 << i) != 0 {
                        b[n..n + 2].copy_from_slice(&tono.to_le_bytes());
                        n += 2;
                    }
                }
                (TONO, n)
            }
            Mensaje::Compuerta { mascara, contador } => {
                b[0..2].copy_from_slice(&mascara.to_le_bytes());
                b[2..4].copy_from_slice(&contador.to_le_bytes());
                (COMPUERTA, 4)
            }
            Mensaje::Bahia(imagen) => {
                for (b, fila) in b.chunks_exact_mut(2).zip(imagen.filas().iter().flatten()) {
                    b.copy_from_slice(&fila.to_le_bytes());
                }
                (BAHIA, 64)
            }
            Mensaje::Set { n, escrituras } => {
                let n = usize::from(n);
                for (b, e) in b.chunks_exact_mut(6).zip(escrituras.get(..n)?) {
                    b[0] = e.instancia;
                    b[1] = e.indice;
                    b[2..6].copy_from_slice(&e.valor.to_le_bytes());
                }
                (SET, 6 * n)
            }
        })
    }
}

/// Lee el sobre de `trama` y el mensaje de su carga. El receptor nunca aplica
/// media trama (D8): una tupla mala de un `SET` lo rechaza entero.
pub fn decodificar(tabla: &[u16; 256], trama: &[u8]) -> Result<(Cabecera, Mensaje), ErrorTrama> {
    let (cabecera, carga) = j2::decodificar(tabla, trama)?;
    Ok((cabecera, leer(cabecera.tipo, carga)?))
}

/// Las cuentas del receptor que sube `SALUD` (§3.3): totales desde la sesion,
/// en 16 bits con vuelta.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub struct Cuentas {
    /// Causa 2 de D8.
    pub rechazadas_crc: u16,
    /// Causas 1 y 4: trama corta o carga sin la forma de su tipo.
    pub rechazadas_forma: u16,
    /// Causa 3: tipo ajeno, sin sesion, o `HOLA` de otra version o dialecto.
    pub rechazadas_tipo: u16,
    /// Huecos de secuencia entre tramas aceptadas (R-C3).
    pub perdidas: u16,
}

/// Un registro de subida (§3.3): estado que el modulo publica y el maestro
/// muestrea (D6).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Registro {
    /// El modulo no tiene nada que publicar.
    Nada,
    /// Lo que el modulo habla y si tiene sesion (D5). El cerebro computa la
    /// compatibilidad; el modulo no la juzga.
    Hola {
        version: u8,
        dialecto: u8,
        sesion: bool,
        /// Las sesiones abiertas desde el arranque, con vuelta.
        sesiones: u8,
    },
    /// Universal, de todo modulo. La temperatura es la del 0x48 de
    /// `memoria.rs`.
    Salud {
        temperatura_centesimas: i16,
        vref_milivoltios: u16,
        cuentas: Cuentas,
    },
    /// `ultimo_evento` y `bahia_aplicada` son secuencias del cerebro, no
    /// contadores; los otros dos son totales desde la sesion.
    EstadoVoz {
        cola_desbordada: u16,
        ultimo_evento: u16,
        bahia_aplicada: u16,
        watchdogs: u16,
    },
}

impl Registro {
    /// Escribe el registro con su sobre y devuelve cuantos bytes ocupa. `None`,
    /// sin tocar `out`, si no cabe en `out`.
    pub fn codificar(&self, tabla: &[u16; 256], secuencia: u16, out: &mut [u8]) -> Option<usize> {
        let mut carga = [0u8; CARGA_SUBIDA];
        let (tipo, n) = self.carga(&mut carga);
        j2::codificar(tabla, tipo, secuencia, &carga[..n], out)
    }

    fn largo(&self) -> usize {
        self.carga(&mut [0; CARGA_SUBIDA]).1
    }

    fn carga(&self, b: &mut [u8; CARGA_SUBIDA]) -> (u8, usize) {
        let mut n = 0;
        let mut poner = |bytes: &[u8]| {
            b[n..n + bytes.len()].copy_from_slice(bytes);
            n += bytes.len();
        };
        let tipo = match *self {
            Registro::Nada => NADA_SUBE,
            Registro::Hola {
                version,
                dialecto,
                sesion,
                sesiones,
            } => {
                poner(&[version, dialecto, u8::from(sesion), sesiones]);
                HOLA_SUBE
            }
            Registro::Salud {
                temperatura_centesimas,
                vref_milivoltios,
                cuentas: c,
            } => {
                poner(&temperatura_centesimas.to_le_bytes());
                for v in [
                    vref_milivoltios,
                    c.rechazadas_crc,
                    c.rechazadas_forma,
                    c.rechazadas_tipo,
                    c.perdidas,
                ] {
                    poner(&v.to_le_bytes());
                }
                SALUD
            }
            Registro::EstadoVoz {
                cola_desbordada,
                ultimo_evento,
                bahia_aplicada,
                watchdogs,
            } => {
                for v in [cola_desbordada, ultimo_evento, bahia_aplicada, watchdogs] {
                    poner(&v.to_le_bytes());
                }
                ESTADO_VOZ
            }
        };
        (tipo, n)
    }
}

/// Lee el sobre de un registro muestreado y el registro de su carga: el lado
/// del cerebro. Como en la bajada, uno sin la forma de su tipo se rechaza
/// entero.
pub fn decodificar_registro(
    tabla: &[u16; 256],
    trama: &[u8],
) -> Result<(Cabecera, Registro), ErrorTrama> {
    let (cabecera, c) = j2::decodificar(tabla, trama)?;
    let forma = |largo: usize| {
        if c.len() == largo {
            Ok(())
        } else {
            Err(ErrorTrama::Forma)
        }
    };
    // Solo se llama con el largo ya comprobado.
    let u16_en = |i: usize| u16::from_le_bytes([c[i], c[i + 1]]);
    let r = match cabecera.tipo {
        NADA_SUBE => forma(0).map(|_| Registro::Nada)?,
        HOLA_SUBE => {
            forma(4)?;
            let sesion = match c[2] {
                0 => false,
                1 => true,
                _ => return Err(ErrorTrama::Forma),
            };
            Registro::Hola {
                version: c[0],
                dialecto: c[1],
                sesion,
                sesiones: c[3],
            }
        }
        SALUD => forma(12).map(|_| Registro::Salud {
            temperatura_centesimas: i16::from_le_bytes([c[0], c[1]]),
            vref_milivoltios: u16_en(2),
            cuentas: Cuentas {
                rechazadas_crc: u16_en(4),
                rechazadas_forma: u16_en(6),
                rechazadas_tipo: u16_en(8),
                perdidas: u16_en(10),
            },
        })?,
        ESTADO_VOZ => forma(8).map(|_| Registro::EstadoVoz {
            cola_desbordada: u16_en(0),
            ultimo_evento: u16_en(2),
            bahia_aplicada: u16_en(4),
            watchdogs: u16_en(6),
        })?,
        _ => return Err(ErrorTrama::Tipo),
    };
    Ok((cabecera, r))
}

/// El lado del modulo: la sesion (D5), las cuentas de rechazo (D8) y el
/// registro que publica (D6). Sin sesion solo pasa `HOLA`, y solo sale su
/// `HOLA`.
#[derive(Clone, Copy, Debug)]
pub struct Receptor {
    sesion: bool,
    sesiones: u8,
    esperada: u16,
    cuentas: Cuentas,
    /// La secuencia del registro publicado: +1 por publicacion (D6.1).
    subida: u16,
    publicado: Registro,
    /// `SALUD` y `ESTADO_VOZ`, lo ultimo pedido de cada uno.
    pedidos: [Option<Registro>; 2],
}

impl Default for Receptor {
    /// Un modulo que acaba de arrancar: sin sesion, publicando su `HOLA`.
    fn default() -> Self {
        let mut r = Receptor {
            sesion: false,
            sesiones: 0,
            esperada: 0,
            cuentas: Cuentas::default(),
            subida: 0,
            publicado: Registro::Nada,
            pedidos: [None; 2],
        };
        r.publicado = r.hola();
        r
    }
}

impl Receptor {
    /// Un giro: `trama` son todos los bytes que el maestro cloco, con relleno y
    /// byte de cola. Devuelve la cabecera y el mensaje de una trama aceptada.
    /// Una rechazada suma en su causa y no cambia nada mas, salvo un `HOLA` que
    /// el modulo no habla, que cierra la sesion: asi el modulo publica su
    /// `HOLA` y el cerebro ve el desacuerdo (D5). Un `HOLA` con la version y el
    /// dialecto del modulo abre sesion, o la reabre.
    ///
    /// Si el giro cloco entero el registro publicado, publica el siguiente
    /// (D6.2); si no, el mismo sigue en el giro que viene. Abrir o cerrar la
    /// sesion abandona lo publicado y publica el `HOLA`.
    pub fn recibir(
        &mut self,
        tabla: &[u16; 256],
        trama: &[u8],
    ) -> Result<(Cabecera, Mensaje), ErrorTrama> {
        // `bytes - 1 >= largo + 6`: el byte de cola no cuenta (D6.4).
        if trama.len() > j2::SOBRE + self.publicado.largo() {
            let siguiente = self.siguiente();
            self.publicar(siguiente);
        }
        let leida = self.aceptar(tabla, trama);
        if let Err(e) = leida {
            let c = &mut self.cuentas;
            let n = match e {
                ErrorTrama::Crc => &mut c.rechazadas_crc,
                ErrorTrama::Corta | ErrorTrama::Forma => &mut c.rechazadas_forma,
                ErrorTrama::Tipo | ErrorTrama::SinSesion => &mut c.rechazadas_tipo,
            };
            *n = n.wrapping_add(1);
        }
        leida
    }

    fn aceptar(
        &mut self,
        tabla: &[u16; 256],
        trama: &[u8],
    ) -> Result<(Cabecera, Mensaje), ErrorTrama> {
        let (cabecera, carga) = j2::decodificar(tabla, trama)?;
        if !self.sesion && cabecera.tipo != HOLA {
            return Err(ErrorTrama::SinSesion);
        }
        let m = leer(cabecera.tipo, carga)?;
        if let Mensaje::Hola { version, dialecto } = m {
            if version != j2::VERSION || dialecto != DIALECTO {
                self.sesion = false;
                self.publicar(self.hola());
                return Err(ErrorTrama::Tipo);
            }
            // Las cuentas a cero, la secuencia de subida a cero, lo publicado y
            // lo pedido abandonados (eran de la sesion vieja), y su `HOLA`.
            *self = Receptor {
                sesion: true,
                sesiones: self.sesiones.wrapping_add(1),
                esperada: 1,
                ..Receptor::default()
            };
            self.publicado = self.hola();
        } else {
            let c = &mut self.cuentas;
            c.perdidas = c
                .perdidas
                .wrapping_add(j2::perdidas(self.esperada, cabecera.secuencia));
            self.esperada = cabecera.secuencia.wrapping_add(1);
        }
        Ok((cabecera, m))
    }

    /// El campo `sesion` del `HOLA` de subida (§3.3).
    pub fn sesion(&self) -> bool {
        self.sesion
    }

    /// Las sesiones abiertas desde el arranque, con vuelta (§3.3).
    pub fn sesiones(&self) -> u8 {
        self.sesiones
    }

    pub fn cuentas(&self) -> Cuentas {
        self.cuentas
    }

    /// El registro que el modulo deja en el bufer de transmision antes de que
    /// `CS` baje, con su secuencia (D6.1).
    pub fn publicado(&self) -> (u16, Registro) {
        (self.subida, self.publicado)
    }

    /// La cola de publicacion de §3.3: `SALUD` y `ESTADO_VOZ`, a la cadencia
    /// que lleve quien llama. Salen en ese orden, uno por muestreo, con lo
    /// ultimo pedido de cada uno. Sin sesion no sale nada pedido, y abrir
    /// sesion lo descarta. `HOLA` y `NADA` no se piden: los pone el receptor.
    pub fn pedir(&mut self, r: Registro) {
        let i = match r {
            Registro::Salud { .. } => 0,
            Registro::EstadoVoz { .. } => 1,
            _ => return,
        };
        self.pedidos[i] = Some(r);
    }

    fn hola(&self) -> Registro {
        Registro::Hola {
            version: j2::VERSION,
            dialecto: DIALECTO,
            sesion: self.sesion,
            sesiones: self.sesiones,
        }
    }

    fn siguiente(&mut self) -> Registro {
        if !self.sesion {
            return self.hola();
        }
        self.pedidos
            .iter_mut()
            .find_map(Option::take)
            .unwrap_or(Registro::Nada)
    }

    fn publicar(&mut self, r: Registro) {
        self.subida = self.subida.wrapping_add(1);
        self.publicado = r;
    }
}

fn leer(tipo: u8, c: &[u8]) -> Result<Mensaje, ErrorTrama> {
    let forma = |largo: usize| {
        if c.len() == largo {
            Ok(())
        } else {
            Err(ErrorTrama::Forma)
        }
    };
    // Solo se llama con el largo ya comprobado.
    let u16_en = |i: usize| u16::from_le_bytes([c[i], c[i + 1]]);
    match tipo {
        NADA => forma(0).map(|_| Mensaje::Nada),
        HOLA => forma(2).map(|_| Mensaje::Hola {
            version: c[0],
            dialecto: c[1],
        }),
        EVENTO => {
            forma(7)?;
            let borde = match c[2] {
                0 => Borde::Abre,
                1 => Borde::Cierra,
                2 => Borde::Dispara,
                _ => return Err(ErrorTrama::Forma),
            };
            Ok(Mensaje::Evento {
                destino: u16_en(0),
                borde,
                fuerza: u16_en(3),
                tono: u16_en(5),
            })
        }
        TONO => {
            if c.len() < 2 {
                return Err(ErrorTrama::Forma);
            }
            let mascara = u16_en(0);
            forma(2 + 2 * mascara.count_ones() as usize)?;
            let mut tonos = [0; CANALES as usize];
            let mut i = 2;
            for (instancia, tono) in tonos.iter_mut().enumerate() {
                if mascara & (1 << instancia) != 0 {
                    *tono = u16_en(i);
                    i += 2;
                }
            }
            Ok(Mensaje::Tono { mascara, tonos })
        }
        COMPUERTA => forma(4).map(|_| Mensaje::Compuerta {
            mascara: u16_en(0),
            contador: u16_en(2),
        }),
        BAHIA => {
            forma(64)?;
            let mut filas = [[0; CANALES as usize]; 2];
            for (i, fila) in filas.iter_mut().flatten().enumerate() {
                *fila = u16_en(2 * i);
            }
            Ok(Mensaje::Bahia(Imagen::desde_filas(filas)))
        }
        SET => {
            let n = c.len() / 6;
            if !c.len().is_multiple_of(6) || n == 0 || n > MAX_ESCRITURAS {
                return Err(ErrorTrama::Forma);
            }
            let mut escrituras = [Escritura::default(); MAX_ESCRITURAS];
            for (e, b) in escrituras.iter_mut().zip(c.chunks_exact(6)) {
                let valor = i32::from_le_bytes([b[2], b[3], b[4], b[5]]);
                let &(min, max) = RANGOS.get(usize::from(b[1])).ok_or(ErrorTrama::Forma)?;
                if b[0] >= CANALES || !(min..=max).contains(&valor) {
                    return Err(ErrorTrama::Forma);
                }
                *e = Escritura {
                    instancia: b[0],
                    indice: b[1],
                    valor,
                };
            }
            Ok(Mensaje::Set {
                n: n as u8,
                escrituras,
            })
        }
        _ => Err(ErrorTrama::Tipo),
    }
}
