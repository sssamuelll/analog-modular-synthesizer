//! §7.6. La sonda causal de la atribucion (§7.2): observo un efecto, cual de
//! las N causas que controlo lo produjo. Se responde **perturbando y
//! correlacionando**.
//!
//! Nacio sirviendo a dos problemas —este y la topologia del patch (§6.2)—
//! porque los dos preguntan lo mismo. **§6.2 se derogo el 2026-09-03** (spec
//! del instrumento entero, D3): el patch interior lo recuerda el crosspoint
//! desde el 23-08, asi que la guia que lo reconstruia a mano se quedo sin
//! trabajo. La pieza se queda entera por el problema que sobrevive, que esta
//! implementado y con tests, y `PATCH_SCAN` sigue congelado en el protocolo
//! por si el otro vuelve por la puerta del exterior (D10).
//!
//! Correlacion, NO deteccion de escalon. El escalon se rompe con atenuadores,
//! se ahoga en el ruido, y obliga a barrer las fuentes de una en una. Esto es
//! lo que usan el GPS, CDMA y la medida de salas: un codigo distinto por
//! fuente y correlacion en cada punto de observacion.
//!
//! Un `Correlador` por **punto de observacion** (cada entrada de CV legible
//! por ADC). Todas las fuentes se perturban a la vez.
//!
//! # El algoritmo
//!
//! 1. La fuente `k` toma la **fila `k+1`** de Walsh-Hadamard. La fila `0` es
//!    continua y se salta: un camino acoplado en AC no la pasaria.
//! 2. Durante `LARGO_CODIGO` marcos, la fuente `k` se perturba en
//!    `±amplitud` segun su codigo.
//! 3. En cada marco se muestrea la entrada.
//! 4. `g[k] = (1/L)·Σ codigo[k][t]·y[t] / amplitud`. Las demas fuentes se
//!    cancelan por ortogonalidad; el ruido se divide por `√L`.
//! 5. `|g₁| < GANANCIA_MINIMA` → no hay cable.
//! 6. `confianza = sep · snr/(snr+1)`, con `sep = (|g₁|−|g₂|)/|g₁|`.
//! 7. Por debajo de `CONFIANZA_MINIMA` es **ambiguo**. Nunca una respuesta
//!    segura y equivocada.

use heapless::Vec;

/// Marcos de analisis por barrido. Potencia de dos: Walsh-Hadamard lo exige, y
/// la ganancia de correlacion contra el ruido es sqrt(LARGO_CODIGO) = 8.
pub const LARGO_CODIGO: usize = 64;
/// Cuantas fuentes caben a la vez. Menos que `LARGO_CODIGO`, que es el techo
/// de codigos ortogonales disponibles descontando la fila continua.
pub const MAX_FUENTES: usize = 32;

/// Por debajo de esto no hay cable, solo diafonia.
pub const GANANCIA_MINIMA: f32 = 0.02;
/// Por debajo de esto se declara ambiguo y se pregunta.
pub const CONFIANZA_MINIMA: f32 = 0.5;

/// Walsh-Hadamard de Sylvester: el signo es (-1)^popcount(fila & t).
///
/// La fila 0 es todo +1 —continua— y por eso las fuentes toman 1..
pub const fn walsh(fila: usize, t: usize) -> i8 {
    if (fila & t).count_ones().is_multiple_of(2) {
        1
    } else {
        -1
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Veredicto {
    Conectado {
        fuente: usize,
        /// La atenuacion medida: 1.0 = a plena escala.
        ganancia: f32,
        confianza: f32,
    },
    /// §7.6 regla 2: se cae a la ocupacion —que si es un hecho binario y
    /// fiable— y la app pide confirmar la pareja.
    Ambiguo {
        a: usize,
        b: usize,
    },
    Desconectado,
}

pub struct Correlador {
    n_fuentes: usize,
    muestras: Vec<f32, LARGO_CODIGO>,
}

impl Correlador {
    pub fn nuevo(n_fuentes: usize) -> Self {
        Correlador {
            n_fuentes: n_fuentes.min(MAX_FUENTES),
            muestras: Vec::new(),
        }
    }

    /// Cuanto hay que sumarle a la fuente `k` en el marco `t`, en unidades de
    /// amplitud: `+1` o `-1`.
    pub fn inyeccion(&self, fuente: usize, t: usize) -> i8 {
        walsh(fuente + 1, t)
    }

    /// Lo que se leyo en este punto de observacion durante el marco `t`.
    pub fn muestra(&mut self, _t: usize, y: f32) {
        let _ = self.muestras.push(y);
    }

    pub fn listo(&self) -> bool {
        self.muestras.len() == LARGO_CODIGO
    }

    pub fn veredicto(&self, amplitud: f32) -> Veredicto {
        let l = self.muestras.len();
        if l == 0 || self.n_fuentes == 0 || amplitud == 0.0 {
            return Veredicto::Desconectado;
        }

        // Paso 4: correlacionar contra cada codigo.
        let mut mejor = (0usize, 0.0f32); // (fuente, g con signo)
        let mut segundo_abs = 0.0f32;
        for k in 0..self.n_fuentes {
            let acc: f32 = self
                .muestras
                .iter()
                .enumerate()
                .map(|(t, y)| walsh(k + 1, t) as f32 * y)
                .sum();
            let g = acc / (l as f32 * amplitud);
            if libm::fabsf(g) > libm::fabsf(mejor.1) {
                segundo_abs = libm::fabsf(mejor.1);
                mejor = (k, g);
            } else if libm::fabsf(g) > segundo_abs {
                segundo_abs = libm::fabsf(g);
            }
        }

        let (fuente, g1) = mejor;
        let g1_abs = libm::fabsf(g1);
        // Paso 5: por debajo del suelo no hay cable.
        if g1_abs < GANANCIA_MINIMA {
            return Veredicto::Desconectado;
        }

        // Paso 6: separacion contra el segundo, y relacion señal/ruido contra
        // lo que queda sin explicar.
        let sep = (g1_abs - segundo_abs) / g1_abs;
        let residuo: f32 = self
            .muestras
            .iter()
            .enumerate()
            .map(|(t, y)| {
                let esperado = g1 * amplitud * walsh(fuente + 1, t) as f32;
                let e = y - esperado;
                e * e
            })
            .sum();
        let ruido = libm::sqrtf(residuo / l as f32);
        let snr = if ruido > f32::EPSILON {
            g1_abs * amplitud / ruido
        } else {
            f32::INFINITY
        };
        let factor_snr = if snr.is_finite() {
            snr / (snr + 1.0)
        } else {
            1.0
        };
        let confianza = sep * factor_snr;

        // Paso 7: si no alcanza, se dice. Nunca se inventa.
        if confianza < CONFIANZA_MINIMA {
            let otra = (0..self.n_fuentes)
                .filter(|k| *k != fuente)
                .max_by(|a, b| {
                    let ga = self.correlacion(*a, amplitud);
                    let gb = self.correlacion(*b, amplitud);
                    ga.partial_cmp(&gb).unwrap_or(core::cmp::Ordering::Equal)
                })
                .unwrap_or(fuente);
            return Veredicto::Ambiguo { a: fuente, b: otra };
        }

        Veredicto::Conectado {
            fuente,
            ganancia: g1,
            confianza,
        }
    }

    fn correlacion(&self, k: usize, amplitud: f32) -> f32 {
        let l = self.muestras.len().max(1) as f32;
        let acc: f32 = self
            .muestras
            .iter()
            .enumerate()
            .map(|(t, y)| walsh(k + 1, t) as f32 * y)
            .sum();
        libm::fabsf(acc / (l * amplitud))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Ruido reproducible sin dependencias: xorshift con semilla fija.
    struct Ruido(u64);
    impl Ruido {
        fn nuevo(semilla: u64) -> Self {
            Ruido(semilla | 1)
        }
        /// Uniforme en [-1, 1), escalado por sigma.
        fn muestra(&mut self, sigma: f32) -> f32 {
            self.0 ^= self.0 << 13;
            self.0 ^= self.0 >> 7;
            self.0 ^= self.0 << 17;
            // 12 bits: 0..4095 -> /2048 da 0..2 -> menos 1 da [-1, 1).
            // Sin la mascara salen 24 bits y el "ruido" llega a 8192.
            let u = ((self.0 >> 40) & 0xFFF) as f32;
            (u / 2048.0 - 1.0) * sigma
        }
    }

    const N: usize = 8;
    const AMPLITUD: f32 = 1.0;

    /// Simula un punto de observacion: `enlaces` son (fuente, ganancia).
    fn correr(enlaces: &[(usize, f32)], sigma: f32, semilla: u64) -> Veredicto {
        let mut c = Correlador::nuevo(N);
        let mut r = Ruido::nuevo(semilla);
        for t in 0..LARGO_CODIGO {
            let mut y = r.muestra(sigma);
            for (fuente, g) in enlaces {
                y += g * AMPLITUD * c.inyeccion(*fuente, t) as f32;
            }
            c.muestra(t, y);
        }
        assert!(c.listo());
        c.veredicto(AMPLITUD)
    }

    #[test]
    fn ninguna_fuente_lleva_continua() {
        // §7.6: un camino acoplado en AC no pasa DC. La fila 0 no se usa.
        for k in 0..MAX_FUENTES {
            let suma: i32 = (0..LARGO_CODIGO).map(|t| walsh(k + 1, t) as i32).sum();
            assert_eq!(suma, 0, "la fuente {k} lleva continua");
        }
        // Y la fila 0, que es la que se salta, si la lleva entera.
        let fila0: i32 = (0..LARGO_CODIGO).map(|t| walsh(0, t) as i32).sum();
        assert_eq!(fila0, LARGO_CODIGO as i32);
    }

    #[test]
    fn los_codigos_son_ortogonales_entre_si() {
        for i in 0..N {
            for j in 0..N {
                let p: i32 = (0..LARGO_CODIGO)
                    .map(|t| walsh(i + 1, t) as i32 * walsh(j + 1, t) as i32)
                    .sum();
                assert_eq!(p, if i == j { LARGO_CODIGO as i32 } else { 0 });
            }
        }
    }

    #[test]
    fn recupera_la_conexion_y_ademas_cuanto_atenua() {
        match correr(&[(3, 0.4)], 0.01, 1) {
            Veredicto::Conectado {
                fuente,
                ganancia,
                confianza,
            } => {
                assert_eq!(fuente, 3);
                assert!((ganancia - 0.4).abs() < 0.02, "ganancia {ganancia}");
                assert!(confianza > CONFIANZA_MINIMA, "confianza {confianza}");
            }
            otro => panic!("tenia que encontrarlo: {otro:?}"),
        }
    }

    #[test]
    fn un_atenuador_fuerte_no_lo_esconde() {
        // El detector de escalon fallaba justo aqui (§7.6).
        match correr(&[(5, 0.05)], 0.01, 2) {
            Veredicto::Conectado {
                fuente, ganancia, ..
            } => {
                assert_eq!(fuente, 5);
                assert!((ganancia - 0.05).abs() < 0.01, "ganancia {ganancia}");
            }
            otro => panic!("un atenuador al 5 % sigue siendo un cable: {otro:?}"),
        }
    }

    #[test]
    fn una_entrada_sin_cable_se_declara_desconectada() {
        assert!(matches!(correr(&[], 0.03, 3), Veredicto::Desconectado));
    }

    #[test]
    fn dos_fuentes_acopladas_por_igual_se_declaran_ambiguas() {
        // §7.6 regla 2: se cae a la ocupacion y la app pregunta.
        match correr(&[(1, 0.30), (6, 0.29)], 0.01, 4) {
            Veredicto::Ambiguo { a, b } => {
                assert_eq!([a.min(b), a.max(b)], [1, 6]);
            }
            otro => panic!("con dos empatadas no puede haber certeza: {otro:?}"),
        }
    }

    #[test]
    fn poca_senal_y_mucho_ruido_es_ambiguo_no_una_respuesta_segura() {
        // Este es EL test de §9: se exige que lo declare ambiguo en vez de
        // inventar. Una respuesta confiada y equivocada seria el fallo peor.
        assert!(!matches!(
            correr(&[(2, 0.06)], 0.15, 5),
            Veredicto::Conectado { .. }
        ));
    }

    #[test]
    fn una_fuente_a_dos_destinos_da_positivo_en_los_dos() {
        // 1-a-muchos sale correcto: son dos correladores independientes, y
        // ninguno sabe del otro.
        for semilla in [7, 8] {
            assert!(matches!(
                correr(&[(4, 0.5)], 0.01, semilla),
                Veredicto::Conectado { fuente: 4, .. }
            ));
        }
    }

    #[test]
    fn el_signo_de_la_ganancia_sobrevive_una_inversion() {
        // Un camino inversor es un camino: la topologia es la misma y el
        // preset tiene que poder guardar el signo.
        match correr(&[(2, -0.35)], 0.01, 9) {
            Veredicto::Conectado {
                fuente, ganancia, ..
            } => {
                assert_eq!(fuente, 2);
                assert!(ganancia < 0.0, "se perdio el signo: {ganancia}");
            }
            otro => panic!("{otro:?}"),
        }
    }
}
