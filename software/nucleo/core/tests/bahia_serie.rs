//! El orden de los 512 bits de la cadena de dos AD75019, contra la hoja.
//!
//! Hoja: `docs/reference/datasheets/ad75019-revf-2026-07.pdf` (Rev. F, 7/2026).
//! Papel: `docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md` §5.3
//! (imagen sombra y commit global), §5.4 (la bahia nace desconectada) y el acta
//! del 2026-09-02 (el N657 shiftea los dos chips por un SPI propio).
//!
//! El orden que se prueba aqui **se reescribe a mano** desde la cita de la
//! hoja, no se le pregunta al modulo: un test que llame a la misma cuenta que
//! prueba no prueba nada.
//!
//! Las dos cosas que la hoja NO dice --que eje fisico es el canal, y cual de
//! los dos chips esta lejos en la cadena-- son parametros, y por eso cada
//! barrido corre las **cuatro** combinaciones.

use sam17_nucleo_core::bahia::{Chip, Imagen, CANALES, LINEAS};
use sam17_nucleo_core::bahia_serie::{
    Cadena, Orientacion, BITS_CADENA, BITS_POR_CHIP, BYTES_CADENA, CHIPS_EN_CADENA,
    PCLK_ACTIVO_EN_BAJO, PCLK_PLAZO_MAX_MS, SCLK_MAX_HZ, SCLK_MIN_HZ,
};

/// El chip que recibe los **primeros** 256 bits: el que cuelga del `SOUT` del
/// otro. Escrito aparte del modulo, contra p. 8 de la hoja: *«The SOUT output
/// is the end of the shift register, and may be directly connected to the SIN
/// input of the next AD75019»*.
fn lejano_de_la_hoja(cadena: Cadena) -> Chip {
    match cadena {
        Cadena::EntradaLejos => Chip::Entrada,
        Cadena::SalidaLejos => Chip::Salida,
    }
}

fn el_otro(chip: Chip) -> Chip {
    match chip {
        Chip::Entrada => Chip::Salida,
        Chip::Salida => Chip::Entrada,
    }
}

/// Donde cae un cruce dentro de los 512 bits que salen por `MOSI`, deducido de
/// la hoja y escrito a mano.
///
/// Hoja p. 8: *«The first bit loaded via SIN [...] controls the switch at the
/// intersection of row Y15 and column X15. The next bits control the remaining
/// columns (down to X0) of row Y15, and are followed by the bits for row Y14,
/// and so on down to the data for the switch at the intersection of row Y0 and
/// column X0.»* -- o sea `(15 - Y) * 16 + (15 - X)` dentro del chip. Y el chip
/// lejano va primero, porque sus bits son los que atraviesan al cercano.
fn indice_de_la_hoja(
    chip: Chip,
    canal: u8,
    linea: u8,
    orientacion: Orientacion,
    cadena: Cadena,
) -> usize {
    let (x, y) = match orientacion {
        Orientacion::CanalEnY => (linea, canal),
        Orientacion::CanalEnX => (canal, linea),
    };
    let base = if chip == lejano_de_la_hoja(cadena) {
        0
    } else {
        256
    };
    base + (15 - y as usize) * 16 + (15 - x as usize)
}

/// El bit `g` de la trama, con la convencion del SPI: **MSB primero dentro de
/// cada byte**, asi que el primer bit que sale es el bit 7 del byte 0.
fn bit_de_la_trama(bytes: &[u8; BYTES_CADENA], g: usize) -> bool {
    bytes[g / 8] & (0x80u8 >> (g % 8)) != 0
}

fn con_un_cruce(chip: Chip, canal: u8, linea: u8) -> Imagen {
    let mut i = Imagen::vacia();
    i.poner(chip, canal, linea);
    i
}

/// El cruce (canal, linea) pasa a (linea, canal): es lo que se ve al leer la
/// misma trama con la otra orientacion, porque cambiar de orientacion es
/// cambiar X por Y.
fn transpuesta(i: &Imagen) -> Imagen {
    let mut t = Imagen::vacia();
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            for linea in 0..LINEAS {
                if i.esta(chip, canal, linea) {
                    t.poner(chip, linea, canal);
                }
            }
        }
    }
    t
}

/// Los cruces de un chip pasan al otro: es lo que se ve al leer la misma trama
/// con el otro orden de cadena, porque cambiar el orden es cambiar de dueno las
/// dos mitades de los 512 bits.
fn chips_cambiados(i: &Imagen) -> Imagen {
    let mut c = Imagen::vacia();
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            for linea in 0..LINEAS {
                if i.esta(chip, canal, linea) {
                    c.poner(el_otro(chip), canal, linea);
                }
            }
        }
    }
    c
}

/// Los patrones del barrido de ida y vuelta. La vacia, la llena, la diagonal y
/// el tablero son simetricos bajo los dos parametros a proposito --son los que
/// harian pasar por simetria a un test perezoso--, y por eso van acompanados de
/// dos asimetricos y de uno pseudoaleatorio.
fn patrones() -> [(&'static str, Imagen); 7] {
    let vacia = Imagen::vacia();

    let mut llena = Imagen::vacia();
    let mut diagonal = Imagen::vacia();
    let mut tablero = Imagen::vacia();
    let mut corrida = Imagen::vacia();
    let mut por_chip = Imagen::vacia();
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            for linea in 0..LINEAS {
                llena.poner(chip, canal, linea);
                if canal == linea {
                    diagonal.poner(chip, canal, linea);
                }
                if (canal + linea) % 2 == 0 {
                    tablero.poner(chip, canal, linea);
                }
                // (canal, canal + 1) no es su propia transpuesta, y los dos
                // chips no llevan lo mismo: distingue los dos parametros.
                if linea == (canal + 1) % LINEAS && chip == Chip::Entrada {
                    corrida.poner(chip, canal, linea);
                }
                if linea == (canal + 3) % LINEAS && chip == Chip::Salida {
                    corrida.poner(chip, canal, linea);
                }
                if chip == Chip::Entrada && canal < 4 && linea < 7 {
                    por_chip.poner(chip, canal, linea);
                }
            }
        }
    }

    // LCG sembrado (Numerical Recipes): el mismo barrido en cada corrida, y
    // ningun patron regular que pueda ser simetrico por casualidad.
    let mut semilla: u32 = 0x1234_5678;
    let mut aleatoria = Imagen::vacia();
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            for linea in 0..LINEAS {
                semilla = semilla.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
                if semilla >> 31 == 1 {
                    aleatoria.poner(chip, canal, linea);
                }
            }
        }
    }

    [
        ("vacia", vacia),
        ("llena", llena),
        ("diagonal", diagonal),
        ("tablero", tablero),
        ("corrida", corrida),
        ("por_chip", por_chip),
        ("aleatoria", aleatoria),
    ]
}

/// Hoja p. 8: el primer bit que entra por `SIN` gobierna Y15/X15, los
/// siguientes bajan de columna hasta X0, luego la fila Y14, y asi hasta Y0/X0.
/// Con la cadena, los primeros 256 bits acaban en el chip lejano.
///
/// Se barren los **512 cruces por las cuatro combinaciones** de orientacion y
/// orden de cadena: 2 048 casos. Dos cruces elegidos a mano dejan pasar un
/// espejo, un desplazamiento de fila o un intercambio de mitades que acierte
/// justo en los dos elegidos.
#[test]
fn cada_cruce_enciende_el_bit_que_manda_la_hoja() {
    let mut casos = 0;
    for orientacion in Orientacion::TODAS {
        for cadena in Cadena::TODAS {
            for chip in Chip::TODOS {
                for canal in 0..CANALES {
                    for linea in 0..LINEAS {
                        let bytes = con_un_cruce(chip, canal, linea).bits(orientacion, cadena);
                        let encendidos: u32 = bytes.iter().map(|b| b.count_ones()).sum();
                        assert_eq!(
                            encendidos, 1,
                            "{orientacion:?} {cadena:?} {chip:?} canal {canal} linea {linea}: \
                             un cruce solo no encendio exactamente un bit"
                        );

                        let g = indice_de_la_hoja(chip, canal, linea, orientacion, cadena);
                        assert!(
                            bit_de_la_trama(&bytes, g),
                            "{orientacion:?} {cadena:?} {chip:?} canal {canal} linea {linea}: \
                             el bit encendido no es el {g} que manda la hoja"
                        );
                        casos += 1;
                    }
                }
            }
        }
    }
    assert_eq!(
        casos, 2_048,
        "el barrido no cubrio los 512 cruces por las cuatro combinaciones"
    );
}

/// Las dos esquinas que la hoja nombra con nombre y apellido: Y15/X15 del chip
/// lejano es el **primer** bit que sale (bit 7 del byte 0, MSB primero), y
/// Y0/X0 del cercano es el **ultimo** (bit 0 del byte 63).
///
/// Las esquinas caen en (canal 15, linea 15) y (canal 0, linea 0) con
/// cualquiera de las dos orientaciones, porque son los cruces de la diagonal
/// que la transposicion no mueve.
#[test]
fn las_dos_esquinas_de_la_hoja() {
    for orientacion in Orientacion::TODAS {
        for cadena in Cadena::TODAS {
            let lejano = lejano_de_la_hoja(cadena);
            let cercano = el_otro(lejano);

            let primero = con_un_cruce(lejano, 15, 15).bits(orientacion, cadena);
            assert_eq!(
                primero[0], 0x80,
                "{orientacion:?} {cadena:?}: Y15/X15 del chip lejano no es el primer bit"
            );
            assert!(
                primero[1..].iter().all(|b| *b == 0),
                "{orientacion:?} {cadena:?}: Y15/X15 encendio algo mas"
            );

            let ultimo = con_un_cruce(cercano, 0, 0).bits(orientacion, cadena);
            assert_eq!(
                ultimo[BYTES_CADENA - 1],
                0x01,
                "{orientacion:?} {cadena:?}: Y0/X0 del chip cercano no es el ultimo bit"
            );
            assert!(
                ultimo[..BYTES_CADENA - 1].iter().all(|b| *b == 0),
                "{orientacion:?} {cadena:?}: Y0/X0 encendio algo mas"
            );
        }
    }
}

/// Ida y vuelta con los mismos parametros, y **con los otros**.
///
/// Leer la trama con la otra orientacion da la transpuesta; con el otro orden
/// de cadena, los chips cambiados. Se asevera esa igualdad exacta --que es mas
/// fuerte que un `!=`-- y ademas se cuenta cuantas veces el `!=` de verdad
/// dispara, para que el test no pueda pasar por simetria sin que se note.
#[test]
fn la_ida_y_vuelta_sobrevive_con_los_mismos_parametros_y_no_con_los_otros() {
    let mut distinguidos = 0;
    for (nombre, imagen) in patrones() {
        for o1 in Orientacion::TODAS {
            for c1 in Cadena::TODAS {
                let bytes = imagen.bits(o1, c1);
                for o2 in Orientacion::TODAS {
                    for c2 in Cadena::TODAS {
                        let leida = Imagen::desde_bits(&bytes, o2, c2);

                        let mut esperada = imagen;
                        if o1 != o2 {
                            esperada = transpuesta(&esperada);
                        }
                        if c1 != c2 {
                            esperada = chips_cambiados(&esperada);
                        }
                        assert_eq!(
                            leida, esperada,
                            "{nombre}: escrita con {o1:?}/{c1:?} y leida con {o2:?}/{c2:?}"
                        );

                        if (o1, c1) == (o2, c2) {
                            assert_eq!(leida, imagen, "{nombre}: la ida y vuelta perdio cruces");
                        } else if esperada != imagen {
                            assert_ne!(
                                leida, imagen,
                                "{nombre}: leer con {o2:?}/{c2:?} devolvio la imagen escrita \
                                 con {o1:?}/{c1:?}"
                            );
                            distinguidos += 1;
                        }
                    }
                }
            }
        }
    }
    assert!(
        distinguidos > 0,
        "ningun patron distinguio los parametros: el barrido pasaria por simetria"
    );
}

/// §5.4: «el AD75019 despierta con el registro aleatorio y sin reset a abierto.
/// El driver del latch arranca inhibido por hardware hasta que el micro
/// shiftea ceros». Esos ceros son estos: la imagen de arranque son 64 bytes en
/// cero, con cualquier orientacion y cualquier orden de cadena, porque un solo
/// bit en uno seria un cruce cerrado al encender.
///
/// Y la llena son 64 `0xFF`: los 512 bits gobiernan 512 cruces distintos, sin
/// hueco ni bit de relleno.
#[test]
fn la_imagen_de_arranque_son_64_ceros_y_la_llena_64_unos() {
    let mut llena = Imagen::vacia();
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            for linea in 0..LINEAS {
                llena.poner(chip, canal, linea);
            }
        }
    }

    for orientacion in Orientacion::TODAS {
        for cadena in Cadena::TODAS {
            assert_eq!(
                Imagen::vacia().bits(orientacion, cadena),
                [0u8; BYTES_CADENA],
                "{orientacion:?} {cadena:?}: la bahia no nace desconectada"
            );
            assert_eq!(
                llena.bits(orientacion, cadena),
                [0xFFu8; BYTES_CADENA],
                "{orientacion:?} {cadena:?}: los 512 cruces no llenan los 512 bits"
            );
        }
    }
}

/// La prueba de que la orientacion hace algo: un cruce **asimetrico**
/// (canal != linea) cae en dos sitios distintos segun que eje sea el canal, y
/// uno de la diagonal (canal == linea) cae en el mismo, porque transponerlo no
/// lo mueve.
///
/// Lo mismo con el orden de la cadena: un cruce cualquiera cambia de mitad.
#[test]
fn las_dos_orientaciones_no_son_la_misma_funcion() {
    for cadena in Cadena::TODAS {
        for chip in Chip::TODOS {
            let asimetrico = con_un_cruce(chip, 3, 9);
            assert_ne!(
                asimetrico.bits(Orientacion::CanalEnY, cadena),
                asimetrico.bits(Orientacion::CanalEnX, cadena),
                "{chip:?} {cadena:?}: canal 3 x linea 9 dio la misma trama en los dos ejes"
            );

            let simetrico = con_un_cruce(chip, 9, 9);
            assert_eq!(
                simetrico.bits(Orientacion::CanalEnY, cadena),
                simetrico.bits(Orientacion::CanalEnX, cadena),
                "{chip:?} {cadena:?}: canal 9 x linea 9 esta en la diagonal y no debia moverse"
            );
        }

        for orientacion in Orientacion::TODAS {
            let cruce = con_un_cruce(Chip::Entrada, 3, 9);
            assert_ne!(
                cruce.bits(orientacion, Cadena::EntradaLejos),
                cruce.bits(orientacion, Cadena::SalidaLejos),
                "{orientacion:?}: el orden de la cadena no movio el cruce de mitad"
            );
        }
    }
}

/// Los numeros de la hoja, tal cual. No es aritmetica: es que nadie los mueva
/// sin que grite.
///
/// - p. 1: «256 switches in a 16 x 16 array» y «an on-board 256-bit shift
///   register»; la cadena de dos es del acta del 2026-09-02 («los dos AD75019,
///   en cadena (512 bits)»).
/// - p. 1 y p. 4: «there is a minimum clock rate of 20 kHz» y «The maximum
///   clock rate of 5 MHz».
/// - p. 8: «PCLK is activated (pulsed low)» y «PCLK must be activated and
///   brought back high within 5 ms after filling the shift register»; p. 4,
///   tabla 2, `t5 + t6` = 5 ms max.
#[test]
fn las_constantes_son_las_de_la_hoja() {
    assert_eq!(BITS_POR_CHIP, 256);
    assert_eq!(CHIPS_EN_CADENA, 2);
    assert_eq!(BITS_CADENA, 512);
    assert_eq!(BYTES_CADENA, 64);
    assert_eq!(SCLK_MIN_HZ, 20_000);
    assert_eq!(SCLK_MAX_HZ, 5_000_000);
    assert_eq!(PCLK_PLAZO_MAX_MS, 5);
    // Por el `let`: `assert!` sobre una constante suelta lo rechaza clippy.
    let pulso_bajo = PCLK_ACTIVO_EN_BAJO;
    assert!(pulso_bajo, "PCLK se pulsa BAJO para latchear");
}
