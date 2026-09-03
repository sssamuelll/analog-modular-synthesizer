//! La asignación de pines del cerebro, en un solo sitio.
//!
//! El cerebro es un STM32N657 (hub §S10, 2026-08-30; VFBGA264 por el censo,
//! `hardware/02-midi-cv/micro_budget.py`). Está aquí y no en `fw` porque es un
//! dato con invariantes que se prueban: que ningún pin esté asignado dos
//! veces, que el J2 sean ocho enlaces y no un bus, y que no quede nada del
//! chip que se fue. Probarlo en `fw` obligaría a correr tests en el micro.
//!
//! **Los `gpio` son índices de propuesta, no pines del N657.** El N657 no
//! numera GPIO: tiene puertos y pines (`PA9`, `PO3`), y cuál va con qué señal
//! lo decide el esquemático del hub, que hoy no existe. Cuando exista, este
//! fichero pasa a puerto y pin y nada más cambia: esa es la razón de que
//! exista. El censo (`micro_budget.py`) demuestra que el reparto cabe y
//! propone uno de muestra; no se lee desde aquí, porque una puerta que compara
//! la propuesta consigo misma no es una puerta (#139). La hoja que manda es la
//! DS14791 Rev 10, y la lee el censo.
//!
//! Lo que se fue con el RP2350 (hub D1, 2026-08-30): el PIO y sus tres
//! programas (los cronómetros de afinación son capturas de TIM en el N657 de
//! la Voz desde el 26-08; el host USB va por el OTG nativo; el mecanismo de la
//! cadena WS2812 lo decide su propio papel), y los dígitos de la cabeza local
//! (derogada el 27-08). El bus del J2 se fue antes, con el punto a punto
//! (25-08): eran un SPI y ocho CS, y son ocho enlaces.

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Pin {
    pub gpio: u8,
    pub para: &'static str,
    /// Si tiene que caer en una entrada del ADC (§5.3: el pedal de expresión).
    pub analogico: bool,
}

const fn d(gpio: u8, para: &'static str) -> Pin {
    Pin {
        gpio,
        para,
        analogico: false,
    }
}
const fn a(gpio: u8, para: &'static str) -> Pin {
    Pin {
        gpio,
        para,
        analogico: true,
    }
}

pub static PINOUT: &[Pin] = &[
    // --- J2: ocho enlaces punto a punto (2026-08-25, D1 y D3) ---
    //
    // Seis en SPI de hardware con el NSS del periférico. El maestro del J2
    // (2026-09-03, D1) lo exige: el NSS por hardware no funciona sin TSIZE, y
    // viceversa (RM0486 p. 3437). Cada ranura es un enlace con su propio
    // maestro, su propio reloj sancionado y su propia tarea.
    d(0, "J2 r1 SCK"),
    d(1, "J2 r1 MOSI"),
    d(2, "J2 r1 MISO"),
    d(3, "J2 r1 NSS"),
    d(4, "J2 r2 SCK"),
    d(5, "J2 r2 MOSI"),
    d(6, "J2 r2 MISO"),
    d(7, "J2 r2 NSS"),
    d(8, "J2 r3 SCK"),
    d(9, "J2 r3 MOSI"),
    d(10, "J2 r3 MISO"),
    d(11, "J2 r3 NSS"),
    d(12, "J2 r4 SCK"),
    d(13, "J2 r4 MOSI"),
    d(14, "J2 r4 MISO"),
    d(15, "J2 r4 NSS"),
    d(16, "J2 r5 SCK"),
    d(17, "J2 r5 MOSI"),
    d(18, "J2 r5 MISO"),
    d(19, "J2 r5 NSS"),
    d(20, "J2 r6 SCK"),
    d(21, "J2 r6 MOSI"),
    d(22, "J2 r6 MISO"),
    d(23, "J2 r6 NSS"),
    // Dos más en USART síncrono, con el CS por GPIO: el USART como maestro no
    // trae NSS por hardware (punto a punto D3). Son repuesto sin módulo hasta
    // que tengan su propio papel (maestro del J2, riesgo 7).
    d(24, "J2 r7 CK"),
    d(25, "J2 r7 TX"),
    d(26, "J2 r7 RX"),
    d(27, "J2 r7 CS"),
    d(28, "J2 r8 CK"),
    d(29, "J2 r8 TX"),
    d(30, "J2 r8 RX"),
    d(31, "J2 r8 CS"),
    // --- I²C hacia el mux de 8 canales (§3.5): el tronco del descubrimiento ---
    d(32, "I2C SDA"),
    d(33, "I2C SCL"),
    // --- La cadena de LED direccionables: un solo pin de datos (cerebro §6.2).
    //     Sin PIO, su mecanismo lo decide su propio papel. ---
    d(34, "WS2812 datos"),
    // --- MIDI DIN, con su optoacoplador (§5.3) ---
    d(35, "DIN in"),
    d(36, "DIN out"),
    // --- Sync analógico. El reset va como parámetro, no cableado (§5.3) ---
    d(37, "CLOCK in"),
    d(38, "CLOCK out"),
    d(39, "RESET in"),
    d(40, "RESET out"),
    // --- El zócalo del puente inalámbrico (§4.2) ---
    d(41, "UART puente TX"),
    d(42, "UART puente RX"),
    // --- El encoder de la cabeza local (§5.2). La cabeza está DEROGADA desde
    //     el 27-08 (cerebro §7): sus dígitos se fueron. El encoder se queda
    //     porque ningún papel lo retira y su pulsador es la confirmación física
    //     (#143, #144). HUECO: sin cabeza, no tiene sitio decidido. ---
    d(43, "encoder A"),
    d(44, "encoder B"),
    d(45, "encoder pulsador"),
    // --- El pedal. Analógico para que sirva también de expresión (§5.3) ---
    a(46, "pedal"),
];

pub const N_PINES_USADOS: usize = PINOUT.len();

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
                assert_ne!(
                    a.gpio, b.gpio,
                    "{} y {} comparten GPIO{}",
                    a.para, b.para, a.gpio
                );
            }
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

    /// Las seis ranuras SPI, con sus cuatro señales cada una.
    const J2_SPI: &[&str] = &[
        "J2 r1 SCK",
        "J2 r1 MOSI",
        "J2 r1 MISO",
        "J2 r1 NSS",
        "J2 r2 SCK",
        "J2 r2 MOSI",
        "J2 r2 MISO",
        "J2 r2 NSS",
        "J2 r3 SCK",
        "J2 r3 MOSI",
        "J2 r3 MISO",
        "J2 r3 NSS",
        "J2 r4 SCK",
        "J2 r4 MOSI",
        "J2 r4 MISO",
        "J2 r4 NSS",
        "J2 r5 SCK",
        "J2 r5 MOSI",
        "J2 r5 MISO",
        "J2 r5 NSS",
        "J2 r6 SCK",
        "J2 r6 MOSI",
        "J2 r6 MISO",
        "J2 r6 NSS",
    ];
    /// Las dos ranuras por USART sincrono, con su CS por GPIO.
    const J2_USART: &[&str] = &[
        "J2 r7 CK", "J2 r7 TX", "J2 r7 RX", "J2 r7 CS", "J2 r8 CK", "J2 r8 TX", "J2 r8 RX",
        "J2 r8 CS",
    ];

    #[test]
    fn el_j2_son_ocho_enlaces_punto_a_punto() {
        // El J2 punto a punto (2026-08-25, D1 y D3) mato el bus de un SPI mas
        // ocho CS: cada ranura es un enlace con su propio maestro. Seis van en
        // SPI de hardware con NSS del periferico (el maestro del J2, D1, lo
        // exige: el NSS por hardware no funciona sin TSIZE, y viceversa), y
        // las dos restantes en USART sincrono con CS por GPIO (punto a punto
        // D3: «el USART sincrono como maestro no trae NSS por hardware»).
        let tiene = |n: &str| PINOUT.iter().any(|p| p.para == n);
        for n in J2_SPI.iter().chain(J2_USART) {
            assert!(
                tiene(n),
                "falta «{n}»: cada ranura del J2 lleva sus cuatro señales"
            );
        }
        // Y el bus viejo no vuelve por la puerta de atras.
        assert!(
            !tiene("J2 SCLK"),
            "«J2 SCLK» es el bus compartido que el punto a punto mato"
        );
        assert!(
            !PINOUT.iter().any(|p| p.para.starts_with("J2 CS ranura")),
            "«J2 CS ranura N» era el CS del bus compartido; hoy cada ranura tiene su NSS o su CS"
        );
    }

    #[test]
    fn no_queda_nada_del_chip_que_se_fue() {
        // El cerebro es un STM32N657 desde el 2026-08-30 (hub, D1). Lo que
        // solo tenia sentido en el RP2350 se fue con el: el PIO (no existe en
        // el N657), los cronometros de afinacion (capturas de TIM en el N657
        // de la Voz desde el 26-08), el host USB por PIO (el N657 trae dos OTG
        // nativos), y los digitos de la cabeza local (derogada el 27-08).
        for p in PINOUT.iter() {
            for muerto in ["PIO", "TUNE_OUT", "digitos"] {
                assert!(
                    !p.para.contains(muerto),
                    "«{}» nombra «{muerto}», que se fue con el RP2350",
                    p.para
                );
            }
        }
    }

    #[test]
    fn el_pedal_es_la_unica_entrada_analogica() {
        // Si alguien anade otra entrada analogica tiene que venir a decirlo
        // aqui: el pedal (§5.3) es hoy la unica, y el ADC del N657 va por
        // pines concretos que el esquematico del hub elige.
        let n = PINOUT.iter().filter(|p| p.analogico).count();
        assert_eq!(
            n, 1,
            "hay {n} entradas analogicas y se esperaba solo el pedal"
        );
        let unica = PINOUT.iter().find(|p| p.analogico).unwrap();
        assert_eq!(unica.para, "pedal");
    }

    #[test]
    fn para_que_encuentra_lo_asignado_y_no_inventa_lo_libre() {
        let sck_r1 = PINOUT
            .iter()
            .find(|p| p.para == "J2 r1 SCK")
            .expect("J2 r1 SCK existe");
        assert_eq!(para_que(sck_r1.gpio), Some("J2 r1 SCK"));
        assert_eq!(para_que(u8::MAX), None);
    }
}
