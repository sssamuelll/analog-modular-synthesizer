//! Marcos de banco con número de secuencia: lo que las pruebas de estrés del transporte por
//! tic ponen en cada bajada y en cada subida para poder ver si una trama llegó rota, repetida
//! o vieja.
//!
//! Con un contenido fijo (`0x5A ^ i`) una trama a medias, una repetida y una buena son el mismo
//! contenido; la revisión de Halberg del 17-10 (hallazgo 2) lo señaló. Un marco lleva el valor
//! (`u32`, little endian) al principio y al final, y en medio bytes que dependen del valor y de
//! la posición: mezclar dos marcos, o leer uno a medias, deja de dar un marco.
//!
//! Solo para el banco: no es la cabecera del enlace.

/// El marco más corto: la cabeza y la cola de cuatro bytes.
pub const MINIMO: usize = 8;

/// La base de las bajadas (del cerebro al módulo) y la de las subidas: distintas, para que un marco de un
/// sentido no pase por uno del otro.
pub const BASE_BAJADA: u8 = 0x5A;
pub const BASE_SUBIDA: u8 = 0xA5;

/// El byte de `posicion` en el medio de un marco de `valor`, con la `base` de su sentido.
const fn byte_medio(valor: u32, posicion: usize, base: u8) -> u8 {
    let h = (valor ^ (posicion as u32).wrapping_mul(0x9E37_79B1)).wrapping_mul(0x85EB_CA6B);
    ((h >> 24) as u8) ^ base
}

/// Escribe en todo `buf` un marco de `valor`. `base` distingue un sentido de otro (la bajada y
/// la subida usan una distinta).
///
/// # Panics
/// Si `buf` tiene menos de [`MINIMO`] bytes.
pub fn escribe(buf: &mut [u8], base: u8, valor: u32) {
    assert!(
        buf.len() >= MINIMO,
        "un marco necesita al menos {MINIMO} bytes"
    );
    let n = buf.len();
    buf[..4].copy_from_slice(&valor.to_le_bytes());
    buf[n - 4..].copy_from_slice(&valor.to_le_bytes());
    for (i, b) in buf[4..n - 4].iter_mut().enumerate() {
        *b = byte_medio(valor, i + 4, base);
    }
}

/// El valor de `buf` si es un marco entero escrito con `base`; `None` si está roto.
pub fn lee(buf: &[u8], base: u8) -> Option<u32> {
    let n = buf.len();
    if n < MINIMO {
        return None;
    }
    let cabeza = u32::from_le_bytes(buf[..4].try_into().ok()?);
    let cola = u32::from_le_bytes(buf[n - 4..].try_into().ok()?);
    if cabeza != cola {
        return None;
    }
    for (i, b) in buf[4..n - 4].iter().enumerate() {
        if *b != byte_medio(cabeza, i + 4, base) {
            return None;
        }
    }
    Some(cabeza)
}

/// Lo que dice [`Seguimiento::ve`] de un valor nuevo.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Veredicto {
    /// Más nuevo que el último: `saltos` valores intermedios no se vieron.
    Nuevo { saltos: u32 },
    /// El mismo que el último.
    Repetido,
    /// Más viejo que el último.
    Atrasado,
}

/// Sigue los valores que llegan en orden y dice si cada uno es nuevo, repetido o atrasado.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Seguimiento {
    ultimo: Option<u32>,
}

impl Seguimiento {
    pub const fn nuevo() -> Seguimiento {
        Seguimiento { ultimo: None }
    }

    /// El primero que llega es siempre nuevo y sin saltos. El último que se recuerda es el
    /// mayor visto: un atrasado o un repetido no lo mueven. El valor no da la vuelta de 32 bits.
    pub fn ve(&mut self, valor: u32) -> Veredicto {
        match self.ultimo {
            None => {
                self.ultimo = Some(valor);
                Veredicto::Nuevo { saltos: 0 }
            }
            Some(u) if valor > u => {
                self.ultimo = Some(valor);
                Veredicto::Nuevo {
                    saltos: valor - u - 1,
                }
            }
            Some(u) if valor == u => Veredicto::Repetido,
            Some(_) => Veredicto::Atrasado,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct Xorshift(u64);
    impl Xorshift {
        fn sig(&mut self) -> u64 {
            self.0 ^= self.0 << 13;
            self.0 ^= self.0 >> 7;
            self.0 ^= self.0 << 17;
            self.0
        }
    }

    const LARGOS: [usize; 7] = [8, 9, 25, 41, 71, 103, 128];
    const VALORES: [u32; 7] = [0, 1, 255, 256, 65_535, 0xDEAD_BEEF, u32::MAX];

    fn marco(largo: usize, base: u8, valor: u32) -> Vec<u8> {
        let mut v = vec![0u8; largo];
        escribe(&mut v, base, valor);
        v
    }

    #[test]
    fn un_marco_escrito_se_lee_igual() {
        for largo in LARGOS {
            for valor in VALORES {
                for base in [0x5A, 0xA5] {
                    assert_eq!(
                        lee(&marco(largo, base, valor), base),
                        Some(valor),
                        "largo {largo} valor {valor:#x} base {base:#x}"
                    );
                }
            }
        }
    }

    #[test]
    fn las_bases_de_los_dos_sentidos_se_distinguen() {
        assert_ne!(BASE_BAJADA, BASE_SUBIDA);
        assert_eq!(lee(&marco(25, BASE_BAJADA, 7), BASE_SUBIDA), None);
    }

    #[test]
    fn menos_de_ocho_bytes_no_es_un_marco() {
        assert_eq!(lee(&[0u8; 7], 0x5A), None);
        assert_eq!(lee(&[], 0x5A), None);
    }

    #[test]
    #[should_panic]
    fn escribir_menos_de_ocho_bytes_es_un_error_del_banco() {
        escribe(&mut [0u8; 7], 0x5A, 1);
    }

    #[test]
    fn cualquier_byte_cambiado_lo_rompe() {
        for largo in [25, 71] {
            for valor in [1u32, 0x0102_0304, u32::MAX] {
                let bueno = marco(largo, 0x5A, valor);
                for posicion in 0..largo {
                    for delta in [1u8, 0x80, 0xFF] {
                        let mut roto = bueno.clone();
                        roto[posicion] ^= delta;
                        assert_eq!(
                            lee(&roto, 0x5A),
                            None,
                            "largo {largo} valor {valor:#x} byte {posicion} ^ {delta:#x}"
                        );
                    }
                }
            }
        }
    }

    #[test]
    fn el_medio_de_un_marco_varia_con_la_posicion() {
        // Sin esto, intercambiar dos bytes del medio no cambiaria nada y la prueba de abajo
        // pasaria sin mirar.
        for valor in [1u32, 0x0102_0304, 0xDEAD_BEEF] {
            let m = marco(41, 0x5A, valor);
            let mut distintos = m[4..37].to_vec();
            distintos.sort_unstable();
            distintos.dedup();
            assert!(
                distintos.len() >= 16,
                "valor {valor:#x}: {} valores distintos",
                distintos.len()
            );
        }
    }

    #[test]
    fn dos_bytes_del_medio_intercambiados_lo_rompen() {
        // Un byte que cambia de sitio (un FIFO desalineado) no cambia ningun valor, solo el orden.
        for valor in [1u32, 0x0102_0304, 0xDEAD_BEEF] {
            let bueno = marco(41, 0x5A, valor);
            for i in 4..37 {
                for j in i + 1..37 {
                    if bueno[i] == bueno[j] {
                        continue;
                    }
                    let mut roto = bueno.clone();
                    roto.swap(i, j);
                    assert_eq!(lee(&roto, 0x5A), None, "valor {valor:#x} bytes {i} y {j}");
                }
            }
        }
    }

    #[test]
    fn un_marco_corrido_un_byte_no_es_un_marco() {
        for valor in [1u32, 0x0102_0304, 0xDEAD_BEEF] {
            let bueno = marco(25, 0x5A, valor);
            let mut corrido = bueno[1..].to_vec();
            corrido.push(bueno[0]);
            assert_eq!(lee(&corrido, 0x5A), None, "valor {valor:#x}");
        }
    }

    #[test]
    fn un_marco_mezclado_de_dos_se_detecta() {
        let mut azar = Xorshift(0x1234_5678_9ABC_DEF1);
        for _ in 0..2000 {
            let a = azar.sig() as u32;
            let b = azar.sig() as u32;
            if a == b {
                continue;
            }
            let (ma, mb) = (marco(25, 0x5A, a), marco(25, 0x5A, b));
            for corte in 1..25 {
                let mut mezcla = ma[..corte].to_vec();
                mezcla.extend_from_slice(&mb[corte..]);
                if mezcla == ma || mezcla == mb {
                    continue; // los bytes coinciden: no hay mezcla que ver
                }
                assert_eq!(lee(&mezcla, 0x5A), None, "a {a:#x} b {b:#x} corte {corte}");
            }
        }
    }

    #[test]
    fn la_base_distingue_un_sentido_de_otro() {
        for valor in VALORES {
            assert_eq!(lee(&marco(25, 0x5A, valor), 0xA5), None, "valor {valor:#x}");
            assert_eq!(lee(&marco(25, 0xA5, valor), 0x5A), None, "valor {valor:#x}");
        }
    }

    #[test]
    fn el_seguimiento_distingue_nuevo_repetido_y_atrasado() {
        let mut s = Seguimiento::nuevo();
        assert_eq!(s.ve(5), Veredicto::Nuevo { saltos: 0 });
        assert_eq!(s.ve(6), Veredicto::Nuevo { saltos: 0 });
        assert_eq!(s.ve(9), Veredicto::Nuevo { saltos: 2 });
        assert_eq!(s.ve(9), Veredicto::Repetido);
        assert_eq!(s.ve(8), Veredicto::Atrasado);
        // Un repetido y un atrasado no mueven el último que se recuerda.
        assert_eq!(s.ve(10), Veredicto::Nuevo { saltos: 0 });
        assert_eq!(s.ve(1), Veredicto::Atrasado);
        assert_eq!(s.ve(12), Veredicto::Nuevo { saltos: 1 });
    }
}
