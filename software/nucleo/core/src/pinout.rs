//! La asignación de pines del cerebro (§5.3), en un solo sitio.
//!
//! Está aquí y no en `fw` porque es un dato con invariantes que se prueban:
//! que ningún pin esté asignado dos veces, y que todos existan en el chip.
//! Probarlo en `fw` obligaría a correr tests en el micro.
//!
//! **Estos números son una propuesta.** No hay placa contra la que
//! verificarlos; cuando la haya, se cambia este fichero y nada más. Esa es la
//! razón de que exista.

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Pin {
    pub gpio: u8,
    pub para: &'static str,
    /// Si tiene que caer en una entrada del ADC (§5.3: el pedal de expresión).
    pub analogico: bool,
}

const fn d(gpio: u8, para: &'static str) -> Pin {
    Pin { gpio, para, analogico: false }
}
const fn a(gpio: u8, para: &'static str) -> Pin {
    Pin { gpio, para, analogico: true }
}

/// El RP2350B: 48 GPIO (§5.3). El A tiene 30 y por eso no daba.
pub const GPIO_MAX: u8 = 48;
/// Las entradas analógicas del B viven arriba del todo.
pub const ANALOGICOS: core::ops::Range<u8> = 40..48;

pub static PINOUT: &[Pin] = &[
    // --- J2, el mazo digital. Contrato congelado por el módulo 3 ---
    d(2, "J2 SCLK"),
    d(3, "J2 MOSI"),
    d(4, "J2 MISO"),
    // Un CS por ranura: módulos 3, 4, 5, 6, 7 y los futuros 8 y 9, más repuesto.
    d(5, "J2 CS ranura 1"),
    d(6, "J2 CS ranura 2"),
    d(7, "J2 CS ranura 3"),
    d(8, "J2 CS ranura 4"),
    d(9, "J2 CS ranura 5"),
    d(10, "J2 CS ranura 6"),
    d(11, "J2 CS ranura 7"),
    d(12, "J2 CS ranura 8"),
    // --- I²C hacia el mux de 8 canales (§3.5) ---
    d(0, "I2C SDA"),
    d(1, "I2C SCL"),
    // --- Afinado: los cuatro TUNE_OUT al PIO (§5.1) ---
    d(13, "TUNE_OUT 1"),
    d(14, "TUNE_OUT 2"),
    d(15, "TUNE_OUT 3"),
    d(16, "TUNE_OUT 4"),
    // --- Gates al ADSR ---
    d(17, "GATE 1"),
    d(18, "GATE 2"),
    d(19, "GATE 3"),
    d(20, "GATE 4"),
    // --- La cadena de LED direccionables: un solo pin de datos (§6.2) ---
    d(21, "WS2812 datos"),
    // --- MIDI DIN, con su optoacoplador (§5.3) ---
    d(22, "DIN in"),
    d(23, "DIN out"),
    // --- Sync analógico. El reset va como parámetro, no cableado (§5.3) ---
    d(24, "CLOCK in"),
    d(25, "CLOCK out"),
    d(26, "RESET in"),
    d(27, "RESET out"),
    // --- El zócalo del puente inalámbrico (§4.2) ---
    d(28, "UART puente TX"),
    d(29, "UART puente RX"),
    // --- La cabeza local (§5.2). Su pulsador ES la confirmación física ---
    d(30, "encoder A"),
    d(31, "encoder B"),
    d(32, "encoder pulsador"),
    d(33, "digitos: datos"),
    d(34, "digitos: reloj"),
    d(35, "digitos: latch"),
    // --- USB host sobre PIO (§5.3). Los dos van juntos y consecutivos ---
    d(36, "PIO-USB D+"),
    d(37, "PIO-USB D-"),
    // --- El pedal. Analógico para que sirva también de expresión (§5.3) ---
    a(40, "pedal"),
];

pub const N_PINES_USADOS: usize = PINOUT.len();

// §5.3 cuenta ~37 GPIO y de ahi sale la obligacion del RP2350B, que da 48
// contra los 30 del A. Si este numero bajara de 31 la obligacion dejaria de
// sostenerse y habria que revisar la spec. Falla al COMPILAR, no al testear.
const _: () = assert!(N_PINES_USADOS > 30);

/// Para qué sirve un GPIO, si es que se usa. Lo consume `fw` al inicializar.
pub fn para_que(gpio: u8) -> Option<&'static str> {
    PINOUT.iter().find(|p| p.gpio == gpio).map(|p| p.para)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ningun_gpio_esta_asignado_dos_veces() {
        // El fallo mas caro y mas silencioso del firmware embebido: dos
        // perifericos peleandose un pin. Aqui cuesta un test.
        for (i, a) in PINOUT.iter().enumerate() {
            for b in PINOUT.iter().skip(i + 1) {
                assert_ne!(a.gpio, b.gpio, "{} y {} comparten GPIO{}", a.para, b.para, a.gpio);
            }
        }
    }

    #[test]
    fn todos_caben_en_el_rp2350b() {
        // §5.3: el B da 48 GPIO. El A da 30 y por eso no sirve.
        for p in PINOUT.iter() {
            assert!(p.gpio < GPIO_MAX, "{} pide GPIO{} y el B llega a 47", p.para, p.gpio);
        }
    }

    #[test]
    fn las_entradas_analogicas_son_de_las_que_existen() {
        // El B trae 8 (GPIO40..47). Pedir una que no existe no compila en
        // `fw`, pero falla aqui antes y con un mensaje que se entiende.
        for p in PINOUT.iter().filter(|p| p.analogico) {
            assert!(ANALOGICOS.contains(&p.gpio), "{} no es una entrada analogica", p.para);
        }
    }

    #[test]
    fn ningun_nombre_se_repite() {
        // Dos pines con el mismo nombre hacen inutil el mensaje de error del
        // primer test, que es el que de verdad importa.
        for (i, a) in PINOUT.iter().enumerate() {
            for b in PINOUT.iter().skip(i + 1) {
                assert_ne!(a.para, b.para, "dos pines se llaman «{}»", a.para);
            }
        }
    }

    #[test]
    fn los_dos_pines_del_pio_usb_van_consecutivos() {
        // Pico-PIO-USB los quiere asi: D+ y D- adyacentes.
        let mas = PINOUT.iter().find(|p| p.para == "PIO-USB D+").unwrap();
        let menos = PINOUT.iter().find(|p| p.para == "PIO-USB D-").unwrap();
        assert_eq!(menos.gpio, mas.gpio + 1, "PIO-USB los quiere adyacentes");
    }

    #[test]
    fn para_que_encuentra_lo_asignado_y_no_inventa_lo_libre() {
        assert_eq!(para_que(21), Some("WS2812 datos"));
        assert_eq!(para_que(47), None);
    }
}
