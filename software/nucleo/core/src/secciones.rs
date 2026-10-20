//! R-H2 en el banco: las secciones criticas, medidas. Por cada sitio que abre una (la direccion
//! de vuelta de quien llamo a `acquire`): cuantas veces, cuantos ciclos la mas larga y cuantas
//! pasan del tope de R-H2. La tabla es fija; lo que no cabe se cuenta aparte, sin sitio.

pub const FILAS: usize = 32;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Fila {
    pub quien: u32,
    pub veces: u32,
    pub max: u32,
    pub largas: u32,
}

#[derive(Clone, Copy)]
pub struct Tabla {
    pub filas: [Fila; FILAS],
    pub usadas: usize,
    pub sin_sitio: u32,
}

impl Tabla {
    pub const fn nueva() -> Self {
        Tabla {
            filas: [Fila {
                quien: 0,
                veces: 0,
                max: 0,
                largas: 0,
            }; FILAS],
            usadas: 0,
            sin_sitio: 0,
        }
    }

    /// Una seccion de `ciclos` abierta desde `quien`; pasa del tope si dura mas de `tope`.
    pub fn anota(&mut self, quien: u32, ciclos: u32, tope: u32) {
        let i = match self.filas[..self.usadas]
            .iter()
            .position(|f| f.quien == quien)
        {
            Some(i) => i,
            None if self.usadas < FILAS => {
                self.filas[self.usadas].quien = quien;
                self.usadas += 1;
                self.usadas - 1
            }
            None => {
                self.sin_sitio += 1;
                return;
            }
        };
        let f = &mut self.filas[i];
        f.veces += 1;
        f.max = f.max.max(ciclos);
        f.largas += u32::from(ciclos > tope);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cada_sitio_lleva_su_cuenta_su_maximo_y_las_que_pasan_del_tope() {
        let mut t = Tabla::nueva();
        t.anota(0x100, 50, 100);
        t.anota(0x200, 300, 100);
        t.anota(0x100, 100, 100);
        t.anota(0x100, 101, 100);
        t.anota(0x100, 80, 100);
        assert_eq!(t.usadas, 2);
        assert_eq!(
            t.filas[0],
            Fila {
                quien: 0x100,
                veces: 4,
                max: 101,
                largas: 1
            }
        );
        assert_eq!(
            t.filas[1],
            Fila {
                quien: 0x200,
                veces: 1,
                max: 300,
                largas: 1
            }
        );
        assert_eq!(t.sin_sitio, 0);
    }

    #[test]
    fn con_la_tabla_llena_un_sitio_nuevo_se_cuenta_sin_sitio() {
        let mut t = Tabla::nueva();
        for i in 0..FILAS as u32 {
            t.anota(i + 1, 10, 100);
        }
        t.anota(0xFFFF, 10, 100);
        t.anota(1, 10, 100);
        assert_eq!(t.usadas, FILAS);
        assert_eq!(t.sin_sitio, 1);
        assert_eq!(t.filas[0].veces, 2);
    }
}
