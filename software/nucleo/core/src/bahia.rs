//! La imagen sombra del crosspoint de la bahia y su barrera de conmutacion.
//!
//! Spec: `docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md`, §5.1
//! (8 entradas + 8 salidas ruteadas por **dos AD75019** de carga serie:
//! entradas -> los 16 nodos de suma; las 16 salidas post-VCA -> salidas), §5.3
//! (la ley de conmutacion contra el chip real) y §5.4 (la bahia nace
//! desconectada).
//!
//! El AD75019 es de **commit global**: carga la palabra entera y aplica todos
//! los cruces a la vez (H-CF2). Por eso conmutar no es tocar un cruce, sino
//! recargar la imagen entera y latchear. Este modulo es el modelo que
//! comparten los dos duenos de esa imagen (acta del 2026-09-02, #171): el
//! cerebro, que la mantiene y la manda por el J2, y el N657 de la Voz, que la
//! guarda como pendiente, decide el commit con la barrera y shiftea.
//!
//! **Aqui solo se habla de canal (0..15) x linea (0..15).** Que linea es que
//! jack, y si la boca del codec y los oidos caben en las 16x16, es el censo
//! mandado en `2026-08-26-motor-digital-design.md` §8.4, que **no esta hecho**.
//! Los ejes fisicos X/Y del chip y el orden de los 512 bits de la cadena
//! tampoco estan aqui: viven en `bahia_serie.rs`, contra la hoja del AD75019.

/// Los canales del instrumento. Uno por fila del crosspoint.
pub const CANALES: u8 = 16;
/// Las lineas de cada AD75019 (16x16). **Linea, no jack.**
pub const LINEAS: u8 = 16;

/// Cual de los dos AD75019 (§5.1). El de entrada lleva una linea al nodo de
/// suma de un canal; el de salida lleva la salida post-VCA de un canal a una
/// linea. El sentido es distinto, pero el indice de canal es el mismo, y por
/// eso los dos votan en la misma mascara.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum Chip {
    Entrada = 0,
    Salida = 1,
}

impl Chip {
    pub const TODOS: [Chip; 2] = [Chip::Entrada, Chip::Salida];
}

/// La imagen sombra: los cruces de los dos chips, enteros.
///
/// Fuera de rango no hace nada y `esta` responde `false`, como `partes.rs`
/// con sus voces: el rango lo valida quien deserializa, y un panico en el
/// N657 es un reset del instrumento.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Imagen {
    /// Por chip y canal, una mascara con las lineas cruzadas.
    filas: [[u16; CANALES as usize]; 2],
}

impl Imagen {
    /// Todo abierto. Es la imagen de arranque de §5.4: el AD75019 despierta
    /// con el registro aleatorio y el latch inhibido por hardware hasta que el
    /// micro shiftea ceros, asi que la bahia nace desconectada.
    pub const fn vacia() -> Self {
        Imagen {
            filas: [[0; CANALES as usize]; 2],
        }
    }

    pub fn poner(&mut self, chip: Chip, canal: u8, linea: u8) {
        if let (Some(bit), Some(fila)) = (Self::bit(linea), self.fila_mut(chip, canal)) {
            *fila |= bit;
        }
    }

    pub fn quitar(&mut self, chip: Chip, canal: u8, linea: u8) {
        if let (Some(bit), Some(fila)) = (Self::bit(linea), self.fila_mut(chip, canal)) {
            *fila &= !bit;
        }
    }

    pub fn esta(&self, chip: Chip, canal: u8, linea: u8) -> bool {
        match (
            Self::bit(linea),
            self.filas[chip as usize].get(canal as usize),
        ) {
            (Some(bit), Some(fila)) => fila & bit != 0,
            _ => false,
        }
    }

    /// Los canales con al menos un cruce distinto entre las dos imagenes, en
    /// cualquiera de los dos chips. **Es el padron de la barrera**: §5.3 dice
    /// que el commit espera a que esten en silencio todos los canales cuyos
    /// cruces cambian, y que los que no cambian no votan.
    pub fn canales_que_cambian(&self, otra: &Imagen) -> u16 {
        let mut mascara = 0u16;
        for (aqui, alla) in self.filas.iter().zip(otra.filas.iter()) {
            for (canal, (a, b)) in aqui.iter().zip(alla.iter()).enumerate() {
                if a != b {
                    mascara |= 1u16 << canal;
                }
            }
        }
        mascara
    }

    fn bit(linea: u8) -> Option<u16> {
        (linea < LINEAS).then(|| 1u16 << linea)
    }

    fn fila_mut(&mut self, chip: Chip, canal: u8) -> Option<&mut u16> {
        self.filas[chip as usize].get_mut(canal as usize)
    }
}

/// La politica de drones, configurable por preset (§5.3).
///
/// **`core` no trae un timeout por defecto**: el numero lo declara el preset.
/// Adivinarlo aqui seria decidir en silencio cuanto aguanta un drone antes de
/// que se le corte, que es justo la eleccion que §5.3 le devuelve al
/// interprete.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum PoliticaDrones {
    /// Espera al silencio, sin fondo. Un drone bajo `diferir` nunca se corta
    /// solo (H-OF3): la starvation deja de ser un bug y pasa a ser una
    /// eleccion del interprete, visible como «pendiente».
    Diferir,
    /// Al vencer el timeout, commit con mute breve de los que siguen sonando.
    Forzar { timeout_ms: u64 },
}

/// Lo que el descriptor ensena: «ruta activa» / «ruta pendiente» (§5.3).
///
/// **Sin TTL.** El commit no viaja por la maquina de retencion (H-RC1: el
/// buzon de 4 ranuras con TTL de 30 s no puede ser cerrojo de topologia), y
/// una pendiente bajo `diferir` puede durar toda la sesion.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Estado {
    Activa,
    Pendiente { desde_ms: u64 },
}

/// Se latchea: la imagen entera se recarga y se aplica a la vez. La imagen que
/// hay que shiftear es la `activa()` de despues del `tick`.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Commit {
    /// Los canales que cambian y NO estaban en silencio, para el mute breve de
    /// `forzar`. Bajo `diferir` es siempre 0, porque alli no se commitea sin
    /// silencio.
    ///
    /// **HUECO**: cuanto dura ese mute y como se mutea el VCA no se modela
    /// aqui. Es del generador de envolventes y del firmware.
    pub mutear: u16,
}

/// La barrera de cambiados-en-silencio (§5.3).
pub struct Barrera {
    activa: Imagen,
    pendiente: Option<Imagen>,
    desde_ms: u64,
    politica: PoliticaDrones,
}

impl Barrera {
    /// Arranca en la imagen vacia y sin pendiente: §5.4, la bahia nace
    /// desconectada.
    pub const fn nueva(politica: PoliticaDrones) -> Self {
        Barrera {
            activa: Imagen::vacia(),
            pendiente: None,
            desde_ms: 0,
            politica,
        }
    }

    /// La imagen que esta puesta en el chip -- la que el firmware shiftea.
    pub fn activa(&self) -> &Imagen {
        &self.activa
    }

    pub fn estado(&self) -> Estado {
        match self.pendiente {
            Some(_) => Estado::Pendiente {
                desde_ms: self.desde_ms,
            },
            None => Estado::Activa,
        }
    }

    /// Deja la imagen como pendiente. **La ultima manda**: si ya habia una
    /// pendiente, la nueva la sustituye y el reloj del timeout arranca de
    /// nuevo. Sin eso, una rafaga de propuestas heredaria el vencimiento de la
    /// primera y forzaria un mute que nadie pidio.
    pub fn proponer(&mut self, imagen: Imagen, ahora_ms: u64) {
        self.pendiente = Some(imagen);
        self.desde_ms = ahora_ms;
    }

    /// Un bit en 1 de `canales_en_silencio` es un canal callado.
    ///
    /// Commit cuando todos los canales que cambian estan callados; bajo
    /// `Forzar`, tambien al vencer el timeout desde `proponer`, y entonces el
    /// `Commit` dice a quien hay que mutear.
    pub fn tick(&mut self, canales_en_silencio: u16, ahora_ms: u64) -> Option<Commit> {
        let pendiente = self.pendiente?;
        // Los que no cambian no votan, suenen o no.
        let estorban = self.activa.canales_que_cambian(&pendiente) & !canales_en_silencio;
        if estorban != 0 {
            match self.politica {
                PoliticaDrones::Diferir => return None,
                PoliticaDrones::Forzar { timeout_ms } => {
                    if ahora_ms.saturating_sub(self.desde_ms) < timeout_ms {
                        return None;
                    }
                }
            }
        }
        self.activa = pendiente;
        self.pendiente = None;
        Some(Commit { mutear: estorban })
    }
}
