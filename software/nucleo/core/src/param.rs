//! Direccionamiento (§3.1) y valores (§3.2).

/// La ranura del propio cerebro. Ahi viven las partes (§3.6), el tempo y las
/// medidas de §7.
pub const RANURA_CEREBRO: u8 = 0;
/// Cada nivel de la ruta es de 4 bits. Hoy solo existen 8 canales de mux
/// (§3.5) y un solo nivel; el hueco esta a proposito.
pub const MAX_RANURAS: usize = 16;
pub const MAX_INSTANCIAS: usize = 16;
/// Cuantos niveles de concentrador admite la direccion (§3.1).
pub const MAX_PROFUNDIDAD: u8 = 3;

/// El valor de cualquier parametro (§3.2). Entero con signo de 32 bits,
/// siempre: la escala y la unidad viven en el descriptor.
pub type Valor = i32;

/// 32 bits: 8 reservados, 3 niveles de ruta de 4, instancia de 4, indice de 8
/// (§3.1).
///
/// ```text
///  31      24 23    20 19    16 15    12 11     8 7            0
/// ┌──────────┬────────┬────────┬────────┬────────┬──────────────┐
/// │reservado │nivel 1 │nivel 2 │nivel 3 │instanc.│    indice    │
/// └──────────┴────────┴────────┴────────┴────────┴──────────────┘
/// ```
///
/// Un modulo enchufado directo al cerebro usa solo el nivel 1 y los otros dos
/// van a cero: es exactamente la direccion plana de antes, corrida de sitio.
/// Los niveles 2 y 3 existen para que un **concentrador** —un modulo que
/// cuelga mas modulos de si mismo— quepa en la direccion sin inventar una
/// tabla de traduccion aparte. 3615 modulos direccionables.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug, Hash)]
pub struct ParamId(pub u32);

const fn nib(v: u8) -> u32 {
    (v & 0xF) as u32
}

impl ParamId {
    /// Un modulo enchufado directo al cerebro: profundidad 1.
    pub const fn nuevo(ranura: u8, instancia: u8, indice: u8) -> Self {
        ParamId::nuevo_ruta(ranura, 0, 0, instancia, indice)
    }

    /// La forma completa. `nivel2` y `nivel3` a `0` significan «no hay».
    pub const fn nuevo_ruta(
        nivel1: u8,
        nivel2: u8,
        nivel3: u8,
        instancia: u8,
        indice: u8,
    ) -> Self {
        ParamId(
            (nib(nivel1) << 20)
                | (nib(nivel2) << 16)
                | (nib(nivel3) << 12)
                | (nib(instancia) << 8)
                | indice as u32,
        )
    }

    /// Que modulo, contando desde el cerebro. `0` es el cerebro.
    ///
    /// Para un modulo directo esto es toda la direccion; si cuelga de un
    /// concentrador, esto es **el concentrador** y hace falta [`Self::ruta`].
    pub const fn ranura(self) -> u8 {
        ((self.0 >> 20) & 0xF) as u8
    }

    /// Los tres niveles. Los que no se usan son `0`.
    pub const fn ruta(self) -> (u8, u8, u8) {
        (
            ((self.0 >> 20) & 0xF) as u8,
            ((self.0 >> 16) & 0xF) as u8,
            ((self.0 >> 12) & 0xF) as u8,
        )
    }

    /// Cuantos saltos hay hasta el modulo. El cerebro y un modulo directo
    /// valen `1`.
    pub const fn profundidad(self) -> u8 {
        let (_, n2, n3) = self.ruta();
        if n3 != 0 {
            3
        } else if n2 != 0 {
            2
        } else {
            1
        }
    }

    /// Que voz o que copia dentro del modulo.
    pub const fn instancia(self) -> u8 {
        ((self.0 >> 8) & 0xF) as u8
    }

    /// Que parametro dentro de esa instancia.
    pub const fn indice(self) -> u8 {
        self.0 as u8
    }

    /// En la ranura 0 el campo instancia significa otra cosa: el numero de
    /// parte (§3.6). Fuera de la ranura 0 no hay partes.
    pub const fn parte(self) -> Option<u8> {
        if self.ranura() == RANURA_CEREBRO {
            Some(self.instancia())
        } else {
            None
        }
    }

    /// El mismo parametro en otra ranura directa. El catalogo (§3.5) declara
    /// sus parametros sin saber donde lo van a enchufar; el descubrimiento los
    /// reubica con esto.
    pub const fn en_ranura(self, ranura: u8) -> Self {
        ParamId::nuevo(ranura, self.instancia(), self.indice())
    }

    /// El mismo parametro en una ruta cualquiera.
    pub const fn en_ruta(self, nivel1: u8, nivel2: u8, nivel3: u8) -> Self {
        ParamId::nuevo_ruta(nivel1, nivel2, nivel3, self.instancia(), self.indice())
    }

    /// Cuelga esta direccion **debajo** de un concentrador: lo que era el
    /// nivel 1 pasa a ser el 2, y el concentrador ocupa el 1.
    ///
    /// Es la operacion del descubrimiento cuando el que contesta es un
    /// concentrador: el reporta a sus hijos como si estuvieran enchufados
    /// directo —no sabe donde esta el— y el cerebro les pone su prefijo.
    ///
    /// `None` si la ruta ya usa los tres niveles: no cabe otro salto.
    pub const fn bajo(self, concentrador: u8) -> Option<Self> {
        let (n1, n2, n3) = self.ruta();
        if n3 != 0 {
            return None;
        }
        Some(ParamId::nuevo_ruta(
            concentrador,
            n1,
            n2,
            self.instancia(),
            self.indice(),
        ))
    }

    /// Si esta direccion cuelga de ese concentrador, en cualquier nivel.
    pub const fn cuelga_de(self, concentrador: u8) -> bool {
        self.profundidad() > 1 && self.ranura() == concentrador
    }

    /// Que la direccion no mienta: sin bits reservados puestos, y sin huecos
    /// en la ruta. Un `(2, 0, 5)` no significa nada — no se cuelga de nada.
    pub const fn valida(self) -> bool {
        if self.0 >> 24 != 0 {
            return false;
        }
        let (n1, n2, n3) = self.ruta();
        if n1 == 0 {
            // El cerebro no cuelga modulos de si mismo por la ruta: sus
            // parametros son suyos (§3.6).
            return n2 == 0 && n3 == 0;
        }
        if n2 == 0 {
            return n3 == 0;
        }
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn los_tres_campos_van_y_vuelven() {
        for ranura in 0..16u8 {
            for instancia in 0..16u8 {
                for indice in [0u8, 1, 42, 127, 255] {
                    let id = ParamId::nuevo(ranura, instancia, indice);
                    assert_eq!(id.ranura(), ranura);
                    assert_eq!(id.instancia(), instancia);
                    assert_eq!(id.indice(), indice);
                }
            }
        }
    }

    #[test]
    fn la_ruta_entera_va_y_vuelve() {
        for n1 in 0..16u8 {
            for n2 in 0..16u8 {
                for n3 in 0..16u8 {
                    let id = ParamId::nuevo_ruta(n1, n2, n3, 7, 42);
                    assert_eq!(id.ruta(), (n1, n2, n3));
                    assert_eq!(id.instancia(), 7);
                    assert_eq!(id.indice(), 42);
                }
            }
        }
    }

    #[test]
    fn un_modulo_directo_es_de_profundidad_uno() {
        // La compatibilidad que hace que este cambio no toque 11 archivos:
        // `nuevo` sigue significando «enchufado al cerebro».
        let id = ParamId::nuevo(3, 0, 1);
        assert_eq!(id.profundidad(), 1);
        assert_eq!(id.ruta(), (3, 0, 0));
        assert_eq!(id.ranura(), 3);
    }

    #[test]
    fn colgar_de_un_concentrador_corre_la_ruta() {
        // El concentrador 2 reporta un modulo que el ve como su ranura 5.
        let hijo = ParamId::nuevo(5, 1, 9);
        let colgado = hijo.bajo(2).unwrap();
        assert_eq!(colgado.ruta(), (2, 5, 0));
        assert_eq!(colgado.profundidad(), 2);
        // Y no pierde nada por el camino.
        assert_eq!(colgado.instancia(), 1);
        assert_eq!(colgado.indice(), 9);
        assert!(colgado.cuelga_de(2));

        // Otro salto mas: tres niveles.
        let nieto = colgado.bajo(4).unwrap();
        assert_eq!(nieto.ruta(), (4, 2, 5));
        assert_eq!(nieto.profundidad(), 3);

        // Y el cuarto no cabe. Que devuelva `None` y no que trunque en
        // silencio es la diferencia entre un limite y un bug.
        assert_eq!(nieto.bajo(1), None);
    }

    #[test]
    fn una_ruta_con_hueco_no_es_valida() {
        // `(2, 0, 5)`: el 5 cuelga de nada. Si esto se aceptara, dos modulos
        // distintos podrian compartir direccion segun quien la construya.
        assert!(!ParamId::nuevo_ruta(2, 0, 5, 0, 0).valida());
        assert!(!ParamId::nuevo_ruta(0, 3, 0, 0, 0).valida());
        assert!(ParamId::nuevo_ruta(2, 5, 0, 0, 0).valida());
        assert!(ParamId::nuevo_ruta(2, 5, 1, 0, 0).valida());
        assert!(ParamId::nuevo(0, 3, 12).valida());
    }

    #[test]
    fn los_bits_reservados_estan_a_cero() {
        // Si algun dia se usan, esta puerta obliga a decidirlo a proposito.
        // Desde 1: el nivel 1 a cero es el cerebro, y el cerebro no lleva
        // ruta (lo prueba `una_ruta_con_hueco_no_es_valida`).
        for n1 in 1..16u8 {
            for i in [0u8, 15] {
                assert!(ParamId::nuevo_ruta(n1, 15, 15, i, 255).valida());
            }
        }
        assert!(!ParamId(0x0100_0000).valida());
    }

    #[test]
    fn en_la_ranura_cero_la_instancia_es_la_parte() {
        // §3.6: es la unica reinterpretacion del campo, y es a proposito.
        assert_eq!(ParamId::nuevo(0, 3, 12).parte(), Some(3));
        assert_eq!(ParamId::nuevo(1, 3, 12).parte(), None);
    }

    #[test]
    fn el_orden_numerico_agrupa_por_modulo() {
        // El modelo hace busqueda binaria sobre el u32 crudo: los parametros
        // de un modulo tienen que quedar contiguos.
        let a = ParamId::nuevo(1, 0, 255);
        let b = ParamId::nuevo(1, 1, 0);
        let c = ParamId::nuevo(2, 0, 0);
        assert!(a.0 < b.0 && b.0 < c.0);
    }

    #[test]
    fn el_orden_numerico_agrupa_tambien_el_arbol_de_un_concentrador() {
        // Consecuencia de poner los niveles en los bits altos, y no es
        // decorativa: el subarbol entero de un concentrador queda contiguo,
        // asi que barrerlo es un rango y no una busqueda.
        let antes = ParamId::nuevo(2, 15, 255); // el concentrador 2, directo
        let hijo_1 = ParamId::nuevo_ruta(2, 1, 0, 0, 0);
        let hijo_15 = ParamId::nuevo_ruta(2, 15, 15, 15, 255);
        let vecino = ParamId::nuevo(3, 0, 0); // ya es otro modulo
        assert!(antes.0 < hijo_1.0);
        assert!(hijo_1.0 < hijo_15.0);
        assert!(hijo_15.0 < vecino.0);
    }

    #[test]
    fn en_ranura_deja_la_ruta_en_un_solo_nivel() {
        // El catalogo reubica un parametro a una ranura directa; si arrastrara
        // niveles viejos, un modulo movido de sitio heredaria un padre que ya
        // no existe.
        let colgado = ParamId::nuevo(5, 1, 9).bajo(2).unwrap();
        let movido = colgado.en_ranura(7);
        assert_eq!(movido.ruta(), (7, 0, 0));
        assert_eq!(movido.profundidad(), 1);
        assert_eq!(movido.indice(), 9);
    }
}
