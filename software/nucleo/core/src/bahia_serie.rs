//! Los 512 bits que se shiftean a la cadena de dos AD75019.
//!
//! Hoja: `docs/reference/datasheets/ad75019-revf-2026-07.pdf` (Rev. F, 7/2026).
//! Papel: `docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md` §5.3
//! (imagen sombra y commit global), §5.4 (la bahia nace desconectada) y el acta
//! del 2026-09-02, que firma quien shiftea: «el N657 de la Voz shiftea los dos
//! AD75019, en cadena (512 bits), por un SPI propio (SCK + MOSI) con el strobe
//! `PCLK` en un GPIO».
//!
//! Este modulo es solo la traduccion de la imagen sombra de `bahia.rs` a esos
//! bits. No toca pines, no cuenta el tiempo y no decide cuando se latchea: eso
//! es del firmware.
//!
//! # Lo que manda la hoja
//!
//! - **El orden de los 256 bits de un chip** -- p. 8, «Loading data»: *«The
//!   rising edge of SCLK, the serial clock input, loads data into the shift
//!   register. The first bit loaded via SIN, the serial data input, controls
//!   the switch at the intersection of row Y15 and column X15. The next bits
//!   control the remaining columns (down to X0) of row Y15, and are followed by
//!   the bits for row Y14, and so on down to the data for the switch at the
//!   intersection of row Y0 and column X0.»* O sea, el cruce (X, Y) es el bit
//!   `(15 - Y) * 16 + (15 - X)` de los que entran por `SIN`, contando desde el
//!   primero.
//! - **El latch** -- p. 8: *«After the shift register is filled with the new
//!   256 bits of control data, PCLK is activated (pulsed low) to transfer the
//!   data to the parallel latches. [...] PCLK must be activated and brought back
//!   high within 5 ms after filling the shift register.»* `PCLK` es **activo en
//!   bajo**, y el plazo es de 5 ms porque el registro es dinamico y pierde el
//!   dato. Lo confirma la tabla 3 de p. 4: con `PCLK` = 0, *«Data in the serial
//!   shift register transfers into the parallel latches»*.
//! - **La cadena** -- p. 8: *«To extend the number of switches in the array, you
//!   may cascade multiple AD75019s. The SOUT output is the end of the shift
//!   register, and may be directly connected to the SIN input of the next
//!   AD75019.»*, con la cuenta en p. 4, tabla 3: con `PCLK` = 1 y flanco de
//!   `SCLK`, *«data clocked into the serial register 256 clocks ago appears at
//!   the SOUT output»*.
//!
//!   **Consecuencia, deducida:** llamemos **cercano** al chip cuyo `SIN` cuelga
//!   del `MOSI` del micro, y **lejano** al que cuelga del `SOUT` del cercano.
//!   Los 256 primeros bits que salen del micro atraviesan el cercano y acaban
//!   en el lejano; los 256 siguientes se quedan en el cercano. O sea: **el chip
//!   lejano va primero**. Y **un solo `PCLK` latchea los dos**, porque el chip
//!   no tiene chip select -- sus pines digitales son `SIN`, `SCLK`, `PCLK` y
//!   `SOUT`, y nada mas (p. 6-7, tabla 5).
//! - **El reloj** -- p. 1: *«The serial shift register is dynamic, so there is a
//!   minimum clock rate of 20 kHz. The maximum clock rate of 5 MHz allows
//!   loading times as short as 52 us.»* La tabla 2 de p. 4 repite el minimo y
//!   deja el resto de los tiempos del strobe: `t5` (de `SCLK` a `PCLK`) 65 ns
//!   min, `t6` (ancho de `PCLK`) 65 ns min, `t5 + t6` 5 ms max, y 70 ns max de
//!   propagacion de `PCLK` a la conmutacion.
//!
//! # Lo que la hoja NO dice, y por eso es parametro y no constante
//!
//! 1. **Que eje fisico es el canal.** Para el AD75019 X e Y son simetricos: en
//!    la tabla 5 de p. 6-7 cada X y cada Y es *«Analog Input (or Output)»*. Que
//!    los 16 nodos de suma vayan en Y y las 16 lineas en X, o al reves, lo
//!    decide el **esquematico**, que no existe. `core` no lo adivina: entra por
//!    `Orientacion`, y **sin `Default`**, para que nadie lo herede por descuido.
//! 2. **Cual de los dos chips esta lejos en la cadena**, o sea cual recibe los
//!    primeros 256 bits. Lo mismo: entra por `Cadena`, y **sin `Default`**.
//!
//! Los dos los declarara el firmware cuando el esquematico fije el cobre. Hasta
//! entonces lo que hay aqui es una funcion correcta para las cuatro
//! combinaciones, y un barrido que la vigila.
//!
//! **HUECO**: si el latch glitchea los cruces que no cambian, **la hoja no lo
//! dice**. Es el supuesto marcado de voz-total §11.2 --«El latch del AD75019 no
//! glitchea cruces que no cambian [...] contra datasheet y bring-up, con
//! mutacion»-- y su mutacion es de bring-up: un cruce sonando, recarga de otro,
//! se mide el primero. Aqui no se modela. Si el supuesto cae, lo que se rehace
//! es §5.3 y §8 del papel, no esta traduccion.

use crate::bahia::{Chip, Imagen, CANALES, LINEAS};

/// Los cruces de un AD75019, y los bits de su registro de desplazamiento. Hoja
/// p. 1: «256 switches in a 16 x 16 array» y «an on-board 256-bit shift
/// register».
pub const BITS_POR_CHIP: usize = 256;
/// El lado de ese cuadrado: 16 filas Y por 16 columnas X (hoja p. 1).
const LADO: usize = 16;
// El cuadrado del chip y el del modelo de `bahia.rs` son el mismo, y por eso
// esta traduccion es posible. Si alguien mueve `CANALES` o `LINEAS`, esto deja
// de compilar en vez de serializar cruces a bits que no son suyos.
const _: () =
    assert!(CANALES as usize == LADO && LINEAS as usize == LADO && LADO * LADO == BITS_POR_CHIP);
/// Acta del 2026-09-02: «los dos AD75019, en cadena (512 bits)».
pub const CHIPS_EN_CADENA: usize = 2;
/// Los bits que el micro shiftea de una vez, para los dos chips.
pub const BITS_CADENA: usize = BITS_POR_CHIP * CHIPS_EN_CADENA;
/// Los mismos bits en bytes: lo que ocupa la imagen entera en el J2 y en el
/// SPI.
pub const BYTES_CADENA: usize = BITS_CADENA / 8;

/// Hoja p. 1: «The serial shift register is dynamic, so there is a minimum
/// clock rate of 20 kHz». Por debajo, el registro pierde el dato **mientras se
/// carga**.
pub const SCLK_MIN_HZ: u32 = 20_000;
/// Hoja p. 1: «The maximum clock rate of 5 MHz allows loading times as short as
/// 52 us».
pub const SCLK_MAX_HZ: u32 = 5_000_000;
/// Hoja p. 8: «PCLK must be activated and brought back high within 5 ms after
/// filling the shift register». Es el mismo `t5 + t6` de la tabla 2 (p. 4).
pub const PCLK_PLAZO_MAX_MS: u32 = 5;
/// Hoja p. 8: «PCLK is activated (**pulsed low**) to transfer the data to the
/// parallel latches», y tabla 3 (p. 4): la transferencia a los latches es la
/// fila con `PCLK` = 0. El GPIO del strobe descansa en alto.
pub const PCLK_ACTIVO_EN_BAJO: bool = true;

/// Que eje fisico del chip es el canal del instrumento. **Lo decide el
/// esquematico**, no la hoja: sus X e Y son simetricos (p. 6-7). Sin `Default`
/// a proposito.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Orientacion {
    /// Los 16 canales son las filas Y; las 16 lineas, las columnas X.
    CanalEnY,
    /// Los 16 canales son las columnas X; las 16 lineas, las filas Y.
    CanalEnX,
}

impl Orientacion {
    pub const TODAS: [Orientacion; 2] = [Orientacion::CanalEnY, Orientacion::CanalEnX];

    /// El cruce (X, Y) del chip que corresponde a este (canal, linea).
    fn xy(self, canal: u8, linea: u8) -> (u8, u8) {
        match self {
            Orientacion::CanalEnY => (linea, canal),
            Orientacion::CanalEnX => (canal, linea),
        }
    }
}

/// Cual de los dos chips esta al final de la cadena. **Lo decide el
/// esquematico**: es donde se suelde el `SOUT` del otro. Sin `Default` a
/// proposito.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Cadena {
    /// El `SIN` del chip de entrada cuelga del `SOUT` del de salida, asi que
    /// los primeros 256 bits son los del chip de entrada.
    EntradaLejos,
    /// Al reves: el `SIN` del de salida cuelga del `SOUT` del de entrada.
    SalidaLejos,
}

impl Cadena {
    pub const TODAS: [Cadena; 2] = [Cadena::EntradaLejos, Cadena::SalidaLejos];

    /// El chip que recibe los **primeros** 256 bits, porque atraviesan al otro.
    pub const fn lejano(self) -> Chip {
        match self {
            Cadena::EntradaLejos => Chip::Entrada,
            Cadena::SalidaLejos => Chip::Salida,
        }
    }
}

/// Donde cae un cruce dentro de los `BITS_CADENA` que salen por `MOSI`,
/// contando desde el primero que entra por `SIN`.
fn indice(chip: Chip, canal: u8, linea: u8, orientacion: Orientacion, cadena: Cadena) -> usize {
    let (x, y) = orientacion.xy(canal, linea);
    // El lejano va primero: sus bits son los que atraviesan al cercano.
    let base = if chip == cadena.lejano() {
        0
    } else {
        BITS_POR_CHIP
    };
    base + (LADO - 1 - y as usize) * LADO + (LADO - 1 - x as usize)
}

/// El byte y la mascara del bit `g` de la trama, con la convencion del SPI:
/// **MSB primero dentro de cada byte**. El primer bit que sale por `MOSI` --el
/// que acaba en la esquina Y15/X15 del chip lejano-- es el bit 7 del byte 0.
fn byte_y_mascara(g: usize) -> (usize, u8) {
    (g / 8, 0x80u8 >> (g % 8))
}

impl Imagen {
    /// Los `BITS_CADENA` bits en el orden exacto en que salen por `MOSI`, MSB
    /// primero dentro de cada byte.
    ///
    /// La `vacia()` de §5.4 --la imagen de arranque-- sale como 64 bytes en
    /// cero: son los ceros que el micro shiftea antes de soltar la inhibicion
    /// del latch.
    pub fn bits(&self, orientacion: Orientacion, cadena: Cadena) -> [u8; BYTES_CADENA] {
        let mut trama = [0u8; BYTES_CADENA];
        for chip in Chip::TODOS {
            for canal in 0..CANALES {
                for linea in 0..LINEAS {
                    if self.esta(chip, canal, linea) {
                        let (byte, mascara) =
                            byte_y_mascara(indice(chip, canal, linea, orientacion, cadena));
                        trama[byte] |= mascara;
                    }
                }
            }
        }
        trama
    }

    /// La inversa de `bits`, con los mismos parametros.
    ///
    /// El firmware no la necesita para shiftear; existe porque hace que la ida
    /// y vuelta sea una propiedad comprobable, y porque es la que lee lo que
    /// salga por `SOUT` en el bring-up (hoja p. 4, tabla 3: lo que se metio
    /// «256 clocks ago» aparece alli).
    pub fn desde_bits(
        trama: &[u8; BYTES_CADENA],
        orientacion: Orientacion,
        cadena: Cadena,
    ) -> Imagen {
        let mut imagen = Imagen::vacia();
        for chip in Chip::TODOS {
            for canal in 0..CANALES {
                for linea in 0..LINEAS {
                    let (byte, mascara) =
                        byte_y_mascara(indice(chip, canal, linea, orientacion, cadena));
                    if trama[byte] & mascara != 0 {
                        imagen.poner(chip, canal, linea);
                    }
                }
            }
        }
        imagen
    }
}
