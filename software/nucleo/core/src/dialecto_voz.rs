//! El dialecto de la Voz, version 1: los mensajes de bajada.
//!
//! Papel: `docs/superpowers/specs/2026-09-02-cabecera-j2-design.md`, D4 (los
//! cinco mensajes y la tabla de indices), D8 (lo que el receptor rechaza) y
//! §3.2 (los bytes). Van con ellos los dos universales de bajada, `NADA` y
//! `HOLA`, para que todo tipo de bajada tenga respuesta.
//!
//! La traduccion a `envolvente::Entrada` (D9) cubre `HOLA`, `EVENTO`,
//! `COMPUERTA` y `SET`. El tono de arranque del `EVENTO` y el `TONO` son del
//! camino del tono, y `BAHIA` es de la barrera, que no estan en el generador.
//!
//! `Receptor` es el lado del modulo: la sesion (D5) y las cuentas de rechazo
//! (D8). Todavia no estan aqui los registros de subida (§3.3).

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

/// El lado del modulo: la sesion (D5) y las cuentas de rechazo (D8). Sin
/// sesion solo pasa `HOLA`.
#[derive(Clone, Copy, Debug, Default)]
pub struct Receptor {
    sesion: bool,
    sesiones: u8,
    esperada: u16,
    cuentas: Cuentas,
}

impl Receptor {
    /// La cabecera y el mensaje de una trama aceptada. Una rechazada suma en su
    /// causa y no cambia nada mas, salvo un `HOLA` que el modulo no habla, que
    /// cierra la sesion: asi el modulo publica su `HOLA` y el cerebro ve el
    /// desacuerdo (D5). Un `HOLA` con la version y el dialecto del modulo abre
    /// sesion, o la reabre.
    pub fn recibir(
        &mut self,
        tabla: &[u16; 256],
        trama: &[u8],
    ) -> Result<(Cabecera, Mensaje), ErrorTrama> {
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
                return Err(ErrorTrama::Tipo);
            }
            *self = Receptor {
                sesion: true,
                sesiones: self.sesiones.wrapping_add(1),
                esperada: 1,
                cuentas: Cuentas::default(),
            };
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
