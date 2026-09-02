//! La memoria del modulo de Voz: el `24AA1025` y su costura.
//!
//! Lo decide el acta **E-7** del papel de la Voz total
//! (`docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md`, «La memoria
//! del modulo pasa a 128 KB») y lo pide el **issue #175**. Cada conducta de
//! aqui esta contra la hoja, que vive en el repo:
//! `docs/reference/datasheets/24aa1025-ds21941h-2011.pdf`.
//!
//! - Byte de control `1010 B0 A1 A0`, y **`B0` hace de A16** — p. 8, §5: *«the
//!   block select bit (B0). This bit acts as the A16 address bit for accessing
//!   the entire array»*. La direccion de 17 bits no cabe en los dos bytes de
//!   palabra, asi que el bit alto viaja en la direccion del dispositivo.
//! - `A2` no es direccion sino habilitador — p. 7, §2.2: *«non-configurable
//!   Chip Select. This pin must be tied to VCC in order for this device to
//!   operate»*.
//! - Cableado decidido por el acta: **`A0` = 1**. Bloque bajo en 0x51, alto en
//!   0x55. Con `A0` = 0 el bajo caeria en 0x50, que es donde vive el
//!   `24AA02E48` de identidad (`descubrimiento.rs`): colision.
//! - **Los dos bytes de palabra van con el alto primero** — p. 8, §5: *«The
//!   upper address bits are transferred first, followed by the Least
//!   Significant bits»*, y p. 9, §6.1 lo repite byte a byte.
//! - **Dos limites distintos**, y este modulo conoce los dos. La pagina de
//!   escritura es de 128 B (p. 1: *«128-Byte Page Write Buffer»*) y lo que la
//!   pasa **se enrolla dentro de esa misma pagina** — p. 9, §6.2: *«the data
//!   wraps around to the beginning of the current page (overwriting data
//!   previously stored there), instead of being written to the next page as
//!   might be expected»*. El bloque es de 64 KB (p. 8, §5: *«two segments of
//!   512K bits»*) y la lectura secuencial **no lo cruza** — p. 8, §5.1: *«It is
//!   not possible to sequentially read across device boundaries»*, con el
//!   enrollado exacto en p. 12, §8.3 (FFFFh -> 0000h, 1FFFFh -> 10000h).
//!
//! # Lo que NO esta aqui, y por que
//!
//! - **Ni Twc ni sondeo de ACK.** La hoja da el tiempo de ciclo de escritura
//!   —p. 4, parametro 16, *«Write cycle time (byte or page)»*: **5 ms**
//!   maximo— pero esperarlo es del firmware y de su reloj, no de un modulo que
//!   no tiene ninguno. El bus de aqui no lo modela.
//! - **Que se guarda dentro es de otro**: donde vive el descriptor es el issue
//!   #226, abierto. Este driver mueve bytes.

/// TMP1075, `docs/modules/03-vco.md`: «TMP1075 (I²C, direccion 0x48)».
pub const DIR_TEMPERATURA: u8 = 0x48;
/// El `24AA02E48` de identidad de `descubrimiento.rs`. Es el que obliga a
/// cablear `A0` a uno (acta E-7, consecuencia 1).
pub const DIR_IDENTIDAD: u8 = 0x50;
/// `1010 B0 A1 A0` con `B0` = 0, `A1` = 0, `A0` = 1.
pub const DIR_BLOQUE_BAJO: u8 = 0x51;
/// El mismo chip con `B0` = 1. **Es la direccion nueva que el #175 reserva.**
pub const DIR_BLOQUE_ALTO: u8 = 0x55;
/// Pagina de escritura. Hoja p. 1: «128-Byte Page Write Buffer».
pub const PAGINA: usize = 128;
/// Cada mitad de chip con su propia direccion. Hoja p. 8, §5: «two segments of
/// 512K bits».
pub const BLOQUE: usize = 65_536;
pub const TAMANO: usize = 2 * BLOQUE;

/// El dispositivo que responde por este byte. Solo tiene sentido dentro de
/// `0..TAMANO`; de eso se encarga `en_rango`.
pub const fn direccion(offset: usize) -> u8 {
    DIR_BLOQUE_BAJO | (((offset >> 16) & 1) << 2) as u8
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ErrorMemoria {
    /// `offset + largo` se sale de los 128 KB. No se enrolla: se falla.
    FueraDeRango,
    /// La transaccion no se completo: NACK, arbitraje perdido, lo que sea. El
    /// porque lo sabe el HAL; el driver solo sabe que no paso.
    Bus,
}

/// Un pedazo de transferencia que cabe en una sola transaccion del chip.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Tramo {
    pub dir: u8,
    pub palabra: u16,
    /// Donde empieza este tramo dentro del buffer del llamador.
    pub desde: usize,
    pub largo: usize,
}

/// Corta una transferencia en tramos cada `corte` bytes contados desde el
/// principio del chip. Escribir corta cada pagina, leer cada bloque, y como
/// `BLOQUE` es multiplo de `PAGINA` la costura de los 64 KB cae en los dos.
pub struct Tramos {
    offset: usize,
    desde: usize,
    resto: usize,
    corte: usize,
}

impl Iterator for Tramos {
    type Item = Tramo;

    fn next(&mut self) -> Option<Tramo> {
        if self.resto == 0 {
            return None;
        }
        let largo = self.resto.min(self.corte - self.offset % self.corte);
        let tramo = Tramo {
            dir: direccion(self.offset),
            palabra: (self.offset % BLOQUE) as u16,
            desde: self.desde,
            largo,
        };
        self.offset += largo;
        self.desde += largo;
        self.resto -= largo;
        Some(tramo)
    }
}

/// Los tramos de una escritura: cortada en CADA pagina, y de paso en el bloque.
pub fn tramos_escritura(offset: usize, largo: usize) -> Tramos {
    Tramos {
        offset,
        desde: 0,
        resto: largo,
        corte: PAGINA,
    }
}

/// Los tramos de una lectura: la lectura secuencial recorre el bloque entero,
/// asi que solo se corta en la costura.
pub fn tramos_lectura(offset: usize, largo: usize) -> Tramos {
    Tramos {
        offset,
        desde: 0,
        resto: largo,
        corte: BLOQUE,
    }
}

/// Lo minimo que el driver le pide al hierro. Sin esperas: el `Twc` es del
/// firmware (ver la cabecera de este modulo).
pub trait Bus {
    /// Escribe bytes crudos en `dir`. Los dos primeros son la palabra.
    fn escribir(&mut self, dir: u8, bytes: &[u8]) -> Result<(), ErrorMemoria>;
    /// Pone el puntero en `palabra` y lee `salida.len()` bytes seguidos.
    fn escribir_y_leer(
        &mut self,
        dir: u8,
        palabra: &[u8; 2],
        salida: &mut [u8],
    ) -> Result<(), ErrorMemoria>;
}

fn en_rango(offset: usize, largo: usize) -> Result<(), ErrorMemoria> {
    match offset.checked_add(largo) {
        Some(fin) if fin <= TAMANO => Ok(()),
        _ => Err(ErrorMemoria::FueraDeRango),
    }
}

pub fn escribir<B: Bus>(bus: &mut B, offset: usize, datos: &[u8]) -> Result<(), ErrorMemoria> {
    en_rango(offset, datos.len())?;
    let mut marco = [0u8; 2 + PAGINA];
    for t in tramos_escritura(offset, datos.len()) {
        marco[..2].copy_from_slice(&t.palabra.to_be_bytes());
        marco[2..2 + t.largo].copy_from_slice(&datos[t.desde..t.desde + t.largo]);
        bus.escribir(t.dir, &marco[..2 + t.largo])?;
    }
    Ok(())
}

pub fn leer<B: Bus>(bus: &mut B, offset: usize, salida: &mut [u8]) -> Result<(), ErrorMemoria> {
    en_rango(offset, salida.len())?;
    for t in tramos_lectura(offset, salida.len()) {
        bus.escribir_y_leer(
            t.dir,
            &t.palabra.to_be_bytes(),
            &mut salida[t.desde..t.desde + t.largo],
        )?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// La falsa: un `24AA1025` de mentira que se enrolla donde se enrolla el de
    /// verdad. Sin sus dos enrollados la costura pasaria con un driver roto.
    /// Cada conducta sale de la hoja DS21941H, citada arriba: el bloque por
    /// `B0` (p. 8, §5), el enrollado de escritura dentro de la pagina (p. 9,
    /// §6.2), el de la lectura secuencial dentro del bloque (p. 8, §5.1 y
    /// p. 12, §8.3). Lo que NO modela es el `Twc`: escribir vuelve al momento.
    struct Falsa24AA1025 {
        celdas: [u8; TAMANO],
    }

    impl Falsa24AA1025 {
        fn nueva() -> Self {
            Falsa24AA1025 {
                celdas: [0xFF; TAMANO],
            }
        }

        /// `B0` del byte de control elige el bloque. A cualquier otra direccion
        /// este chip no contesta: eso es un NACK.
        fn bloque(&self, dir: u8) -> Result<usize, ErrorMemoria> {
            match dir {
                DIR_BLOQUE_BAJO => Ok(0),
                DIR_BLOQUE_ALTO => Ok(BLOQUE),
                _ => Err(ErrorMemoria::Bus),
            }
        }
    }

    impl Bus for Falsa24AA1025 {
        fn escribir(&mut self, dir: u8, bytes: &[u8]) -> Result<(), ErrorMemoria> {
            let base = self.bloque(dir)?;
            let palabra = u16::from_be_bytes([bytes[0], bytes[1]]) as usize;
            let pagina = palabra / PAGINA * PAGINA;
            for (i, b) in bytes[2..].iter().enumerate() {
                // Lo que pasa del final de la pagina se enrolla al principio de
                // ESA pagina; no sigue hacia la siguiente.
                self.celdas[base + pagina + (palabra - pagina + i) % PAGINA] = *b;
            }
            Ok(())
        }

        fn escribir_y_leer(
            &mut self,
            dir: u8,
            palabra: &[u8; 2],
            salida: &mut [u8],
        ) -> Result<(), ErrorMemoria> {
            let base = self.bloque(dir)?;
            let inicio = u16::from_be_bytes(*palabra) as usize;
            for (i, b) in salida.iter_mut().enumerate() {
                // La lectura secuencial se enrolla dentro del bloque de 64 KB:
                // nunca cruza al otro.
                *b = self.celdas[base + (inicio + i) % BLOQUE];
            }
            Ok(())
        }
    }

    // ---- la falsa, primero: un doble que miente no prueba nada ----

    #[test]
    fn la_falsa_se_enrolla_dentro_de_la_pagina_como_el_chip_de_verdad() {
        let mut falsa = Falsa24AA1025::nueva();
        let mut marco = [0u8; 2 + 60];
        marco[..2].copy_from_slice(&100u16.to_be_bytes());
        for (i, b) in marco[2..].iter_mut().enumerate() {
            *b = i as u8;
        }
        Bus::escribir(&mut falsa, DIR_BLOQUE_BAJO, &marco).unwrap();
        // La pagina es 0..128: los 28 primeros bytes caen en 100..128 y los 32
        // que sobran se enrollan al principio de ESA pagina.
        assert_eq!(falsa.celdas[100], 0);
        assert_eq!(falsa.celdas[127], 27);
        assert_eq!(falsa.celdas[0], 28);
        assert_eq!(falsa.celdas[31], 59);
        assert_eq!(falsa.celdas[32], 0xFF, "no escribe mas de lo que se manda");
        assert_eq!(falsa.celdas[128], 0xFF, "la pagina siguiente no se toca");
    }

    #[test]
    fn la_lectura_secuencial_de_la_falsa_se_enrolla_dentro_del_bloque() {
        let mut falsa = Falsa24AA1025::nueva();
        falsa.celdas[0] = 0xAA;
        falsa.celdas[BLOQUE] = 0xBB;
        let mut vuelta = [0u8; 2];
        Bus::escribir_y_leer(
            &mut falsa,
            DIR_BLOQUE_BAJO,
            &0xFFFFu16.to_be_bytes(),
            &mut vuelta,
        )
        .unwrap();
        assert_eq!(vuelta[1], 0xAA, "la lectura no salta al bloque alto");
    }

    #[test]
    fn la_falsa_no_contesta_en_ninguna_otra_direccion() {
        let mut falsa = Falsa24AA1025::nueva();
        assert_eq!(
            Bus::escribir(&mut falsa, DIR_IDENTIDAD, &[0, 0, 1]),
            Err(ErrorMemoria::Bus)
        );
        assert_eq!(
            Bus::escribir_y_leer(&mut falsa, 0x54, &[0, 0], &mut [0u8; 1]),
            Err(ErrorMemoria::Bus)
        );
    }

    // ---- el mapa del canal del mux ----

    #[test]
    fn el_bit_alto_de_la_direccion_de_17_bits_viaja_en_el_byte_de_control() {
        assert_eq!(direccion(0), 0x51);
        assert_eq!(direccion(65_535), 0x51);
        assert_eq!(direccion(65_536), 0x55);
        assert_eq!(direccion(131_071), 0x55);
    }

    #[test]
    fn cada_byte_del_chip_cae_en_el_bloque_que_le_toca() {
        // Dos fronteras a mano pasan con la formula escrita a mano: se barre.
        for offset in (0..TAMANO).step_by(97) {
            let esperado = if offset < BLOQUE {
                DIR_BLOQUE_BAJO
            } else {
                DIR_BLOQUE_ALTO
            };
            assert_eq!(direccion(offset), esperado, "offset {offset}");
        }
    }

    #[test]
    fn el_canal_del_mux_no_tiene_dos_chips_en_la_misma_direccion() {
        let mapa = [
            DIR_TEMPERATURA,
            DIR_IDENTIDAD,
            DIR_BLOQUE_BAJO,
            DIR_BLOQUE_ALTO,
        ];
        for (i, a) in mapa.iter().enumerate() {
            for b in &mapa[i + 1..] {
                assert_ne!(a, b, "dos chips en la misma direccion");
            }
        }
    }

    #[test]
    fn con_a0_a_cero_la_memoria_pisaria_la_identidad() {
        // `1010 B0 A1 A0`: apagar `A0` baja las dos direcciones en uno, y la
        // baja aterriza justo encima del 24AA02E48.
        assert_eq!(DIR_BLOQUE_BAJO & !1, DIR_IDENTIDAD);
        assert_eq!(DIR_BLOQUE_ALTO & !1, 0x54);
    }

    // ---- la costura, como aritmetica ----

    #[test]
    fn una_escritura_que_cabe_en_una_pagina_no_se_parte() {
        let t: Vec<_> = tramos_escritura(1_000, 20).collect();
        assert_eq!(
            t,
            [Tramo {
                dir: DIR_BLOQUE_BAJO,
                palabra: 1_000,
                desde: 0,
                largo: 20,
            }]
        );
    }

    #[test]
    fn una_escritura_a_caballo_de_una_pagina_se_parte_en_cada_pagina() {
        let t: Vec<_> = tramos_escritura(100, 200).collect();
        assert_eq!(
            t,
            [
                Tramo {
                    dir: DIR_BLOQUE_BAJO,
                    palabra: 100,
                    desde: 0,
                    largo: 28,
                },
                Tramo {
                    dir: DIR_BLOQUE_BAJO,
                    palabra: 128,
                    desde: 28,
                    largo: 128,
                },
                Tramo {
                    dir: DIR_BLOQUE_BAJO,
                    palabra: 256,
                    desde: 156,
                    largo: 44,
                },
            ]
        );
    }

    #[test]
    fn una_escritura_a_caballo_del_bloque_cambia_de_chip_y_vuelve_a_la_palabra_cero() {
        let t: Vec<_> = tramos_escritura(BLOQUE - 8, 16).collect();
        assert_eq!(
            t,
            [
                Tramo {
                    dir: DIR_BLOQUE_BAJO,
                    palabra: 65_528,
                    desde: 0,
                    largo: 8,
                },
                Tramo {
                    dir: DIR_BLOQUE_ALTO,
                    palabra: 0,
                    desde: 8,
                    largo: 8,
                },
            ]
        );
    }

    #[test]
    fn una_lectura_no_se_parte_por_pagina_pero_si_por_bloque() {
        assert_eq!(tramos_lectura(100, 500).count(), 1);
        let t: Vec<_> = tramos_lectura(BLOQUE - 8, 16).collect();
        assert_eq!(
            t,
            [
                Tramo {
                    dir: DIR_BLOQUE_BAJO,
                    palabra: 65_528,
                    desde: 0,
                    largo: 8,
                },
                Tramo {
                    dir: DIR_BLOQUE_ALTO,
                    palabra: 0,
                    desde: 8,
                    largo: 8,
                },
            ]
        );
    }

    // ---- el driver contra la falsa ----

    #[test]
    fn una_escritura_a_caballo_del_byte_65536_llega_entera_y_no_pisa_la_cabecera() {
        let mut falsa = Falsa24AA1025::nueva();
        let datos: [u8; 128] = core::array::from_fn(|i| (i as u8) ^ 0xA5);
        escribir(&mut falsa, BLOQUE - 64, &datos).unwrap();

        let mut vuelta = [0u8; 128];
        leer(&mut falsa, BLOQUE - 64, &mut vuelta).unwrap();
        assert_eq!(vuelta, datos);

        // Un driver que partiera solo por paginas y se quedara en 0x51 habria
        // puesto el segundo tramo en la palabra 0x0000 del bloque BAJO, encima
        // de la cabecera.
        assert_eq!(falsa.celdas[0], 0xFF, "piso el byte 0");
        assert_eq!(falsa.celdas[BLOQUE - 64], datos[0]);
        assert_eq!(falsa.celdas[BLOQUE], datos[64]);
    }

    #[test]
    fn la_costura_aguanta_todo_el_vecindario_del_byte_65536() {
        let mut falsa = Falsa24AA1025::nueva();
        let datos: [u8; 300] = core::array::from_fn(|i| (i as u8).wrapping_mul(31).wrapping_add(7));
        for offset in (BLOQUE - 200)..=(BLOQUE + 200) {
            for largo in [1usize, 3, 64, 127, 128, 129, 300] {
                falsa.celdas.fill(0xFF);
                escribir(&mut falsa, offset, &datos[..largo]).unwrap();
                let mut vuelta = [0u8; 300];
                leer(&mut falsa, offset, &mut vuelta[..largo]).unwrap();
                assert_eq!(
                    &vuelta[..largo],
                    &datos[..largo],
                    "offset {offset}, largo {largo}"
                );
                assert_eq!(
                    falsa.celdas[0], 0xFF,
                    "offset {offset}, largo {largo}: piso el byte 0"
                );
            }
        }
    }

    #[test]
    fn una_lectura_a_caballo_del_byte_65536_vuelve_entera() {
        let mut falsa = Falsa24AA1025::nueva();
        // Se siembra a mano: este test mide la lectura, no la escritura.
        for (i, c) in falsa.celdas[BLOQUE - 4..BLOQUE + 4].iter_mut().enumerate() {
            *c = 0x10 + i as u8;
        }
        let mut vuelta = [0u8; 8];
        leer(&mut falsa, BLOQUE - 4, &mut vuelta).unwrap();
        assert_eq!(vuelta, [0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17]);
    }

    /// Hoja p. 8, §5: *«The upper address bits are transferred first, followed
    /// by the Least Significant bits»*. La falsa decodifica igual que el driver
    /// codifica, asi que ese acuerdo no lo prueba ninguno de los tests de
    /// arriba: si los dos se dieran vuelta a la vez, seguirian en verde y el
    /// chip de verdad escribiria en otro sitio. Se mira el bus crudo.
    #[test]
    fn la_palabra_sale_al_bus_con_el_byte_alto_primero() {
        struct Grabadora([u8; 3]);
        impl Bus for Grabadora {
            fn escribir(&mut self, _dir: u8, bytes: &[u8]) -> Result<(), ErrorMemoria> {
                self.0.copy_from_slice(bytes);
                Ok(())
            }
            fn escribir_y_leer(
                &mut self,
                _dir: u8,
                palabra: &[u8; 2],
                _salida: &mut [u8],
            ) -> Result<(), ErrorMemoria> {
                self.0[..2].copy_from_slice(palabra);
                Ok(())
            }
        }

        let mut bus = Grabadora([0; 3]);
        escribir(&mut bus, 0x1234, &[0xAA]).unwrap();
        assert_eq!(bus.0, [0x12, 0x34, 0xAA]);

        leer(&mut bus, 0x1234, &mut [0u8; 1]).unwrap();
        assert_eq!(bus.0[..2], [0x12, 0x34]);
    }

    #[test]
    fn fuera_de_rango_es_error_y_la_memoria_queda_intacta() {
        let mut falsa = Falsa24AA1025::nueva();
        assert_eq!(
            escribir(&mut falsa, TAMANO - 4, &[1, 2, 3, 4, 5]),
            Err(ErrorMemoria::FueraDeRango)
        );
        assert_eq!(
            leer(&mut falsa, TAMANO, &mut [0u8; 1]),
            Err(ErrorMemoria::FueraDeRango)
        );
        assert_eq!(
            escribir(&mut falsa, usize::MAX, &[1]),
            Err(ErrorMemoria::FueraDeRango)
        );
        assert!(falsa.celdas.iter().all(|c| *c == 0xFF));

        // Y el ultimo byte del chip si es escribible: el limite es inclusivo.
        escribir(&mut falsa, TAMANO - 1, &[0x5A]).unwrap();
        assert_eq!(falsa.celdas[TAMANO - 1], 0x5A);
    }
}
