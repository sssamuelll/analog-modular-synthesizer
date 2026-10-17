//! El maestro del J2: plazo, reinicio y cuenta, porque el silicio se cuelga.
//!
//! Spec: `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`.
//! Plan: `docs/superpowers/plans/2026-09-04-maestro-j2-recuperacion.md`.
//!
//! Aqui vive la POLITICA y nada mas: que hace el cerebro cuando una
//! transferencia del J2 no termina. El driver que cloca los bytes vive en
//! `fw/src/j2_spi.rs` y no sabe nada del sobre; la frontera es de D8 y es
//! dura: **`fw` cloca bytes; `core` sabe que son.** Si la semantica del sobre
//! aparece en `j2_spi.rs`, es un defecto.
//!
//! Por que existe: hay un defecto abierto en el SPI del STM32N6 o en su driver
//! (embassy-rs/embassy#5607, sin diagnostico desde 2026-03-05). El J2 tenia red
//! de seguridad del lado del modulo -- watchdog de trama, silencio por hardware
//! sin CPU, un receptor que rechaza entero y cuenta -- y NINGUNA del lado del
//! cerebro. Un maestro colgado se traduce en el modulo soltando las notas a los
//! ~50 ms, y ahi se queda el instrumento.
//!
//! Nada de este modulo toca hardware ni usa `async`. Se prueba entero en el
//! host, que es lo que pedia `fw/src/main.rs:6` ("Capa DELGADA a proposito").

use core::num::NonZeroU16;

/// Periodo de un giro del lazo. `trama_j2_budget.F_LAZO_HZ` = 8 kHz.
pub const PERIODO_GIRO_US: u32 = 125;

/// Ventana del watchdog de trama del modulo. voz-total sec.9.2, y es
/// **ESTIMADO**: aquel papel dice "sin trama valida en N ms (N del plan, ~50),
/// todos los generadores van a release". Su cota superior -- cuanto sustain
/// fantasma es tolerable -- no esta escrita en ningun papel y es HUECO de
/// voz-total (spec sec.3).
pub const T_WATCHDOG_TRAMA_US: u32 = 50_000;

/// Cuantos instantes de plazo vencido guarda el anillo de la ventana. Acota
/// `umbral_inestable` por construccion; 16 sobra para el 10 ESTIMADO.
pub const VENTANA_MAX: usize = 16;

/// Las ranuras del J2 por SPI.
///
/// Las dos por USART sincrono que el censo del hub tambien sostiene
/// (`micro_budget.py`, `HUB_RANURAS_USART = 2`) quedan fuera: son otro
/// periferico con otra maquina de estados, y el planificador las trata como
/// `Vacia` hasta que tengan papel propio (spec sec.0 y riesgo 7).
pub const RANURAS_SPI: usize = 6;

/// El largo clocado de una trama, que es `TSIZE` (spec D1).
///
/// R-MJ1 vive en este tipo: no hay forma de construir un cero, asi que no hay
/// forma de armar una transferencia con `TSIZE = 0`. El manual ata el NSS por
/// hardware al contador -- RM0486 Rev 4, sec.67.4.7, p. 3437: "the master must
/// apply the proper TSIZE > 0 setting to control the NSS output correctly" --
/// asi que un cero no seria una transferencia lenta: seria un NSS que no baja.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Tsize(NonZeroU16);

impl Tsize {
    pub const fn nuevo(bytes: u16) -> Option<Tsize> {
        match NonZeroU16::new(bytes) {
            Some(n) => Some(Tsize(n)),
            None => None,
        }
    }

    pub const fn get(self) -> u16 {
        self.0.get()
    }
}

/// Los umbrales de D3 y D7.
///
/// R-MJ4: son parametros, no literales, y viven todos aqui para que
/// `recuperacion_j2_budget.py` los LEA en vez de copiarlos. Todos los valores
/// por defecto son ESTIMADO y el bring-up los sella (spec sec.9, riesgo 2).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Umbrales {
    /// D3. Multiplica el tiempo nominal de la trama. ESTIMADO = 2.
    pub factor_plazo: u32,
    /// D3. Suelo del plazo, para que un mensaje corto no tenga un plazo tan
    /// apretado que un retraso de ISR lo venza. ESTIMADO = 20 us.
    pub t_suelo_plazo_us: u32,
    /// D7.3. Ventana deslizante de `inestable`. ESTIMADO = 1 s.
    pub ventana_salud_us: u32,
    /// D7.3. Plazos vencidos en la ventana que ponen `inestable`. ESTIMADO = 10.
    pub umbral_inestable: u32,
    /// D7.3. Subidas malas SEGUIDAS que ponen `muda`. ESTIMADO = 40 (5 ms).
    pub umbral_muda: u32,
}

impl Umbrales {
    /// Los ESTIMADO de la spec sec.3. No es `Default` a proposito: que se lea
    /// el nombre en el sitio de uso.
    pub const POR_DEFECTO: Umbrales = Umbrales {
        factor_plazo: 2,
        t_suelo_plazo_us: 20,
        ventana_salud_us: 1_000_000,
        umbral_inestable: 10,
        umbral_muda: 40,
    };

    /// Devuelve `None` si los umbrales no pueden hacer su trabajo.
    ///
    /// Las dos cotas no son gusto:
    ///
    /// * `umbral_muda` x `PERIODO_GIRO_US` < `T_WATCHDOG_TRAMA_US`. La marca
    ///   `muda` existe para avisar de un modulo que no contesta. Si tarda mas
    ///   que el propio watchdog del modulo, el modulo ya solto las notas y la
    ///   marca llega de luto.
    /// * `umbral_inestable` <= `VENTANA_MAX`, porque el anillo que mide la
    ///   ventana tiene ese tamano.
    pub const fn nuevos(
        factor_plazo: u32,
        t_suelo_plazo_us: u32,
        ventana_salud_us: u32,
        umbral_inestable: u32,
        umbral_muda: u32,
    ) -> Option<Umbrales> {
        if umbral_muda == 0 || umbral_inestable == 0 || factor_plazo == 0 {
            return None;
        }
        if umbral_muda * PERIODO_GIRO_US >= T_WATCHDOG_TRAMA_US {
            return None;
        }
        if umbral_inestable > VENTANA_MAX as u32 {
            return None;
        }
        Some(Umbrales {
            factor_plazo,
            t_suelo_plazo_us,
            ventana_salud_us,
            umbral_inestable,
            umbral_muda,
        })
    }
}

/// El plazo de una transferencia, en microsegundos (spec D3).
///
/// ```text
/// plazo(msg) = FACTOR_PLAZO x t_nominal(msg) + T_SUELO_PLAZO
/// t_nominal(msg) = bytes_clocados(msg) x 8 / f_reloj_sancionado(ranura)
/// ```
///
/// `bytes_clocados` es el mismo numero que `TSIZE` (D1): sobre + carga + CRC +
/// cola, con el relleno de la ventana del dialecto. Por eso el argumento es un
/// `Tsize` y no un `u16` suelto -- si fueran dos numeros distintos, uno estaria
/// mal.
///
/// El redondeo es hacia arriba a proposito: un plazo corto por truncamiento
/// produce reinicios de tramas sanas, que es el riesgo 2 de la spec.
pub fn plazo_us(tsize: Tsize, f_reloj_hz: u32, u: &Umbrales) -> u32 {
    let bits = tsize.get() as u64 * 8;
    let t_nominal_us = (bits * 1_000_000).div_ceil(f_reloj_hz as u64);
    (u.factor_plazo as u64 * t_nominal_us + u.t_suelo_plazo_us as u64) as u32
}

/// El `MBR` de `SPI_CFG1` y el `f_sck` real que sale de el (spec D1).
///
/// El divisor del maestro es `2^(MBR+1)`, de `/2` a `/256` (RM0486 Rev 4,
/// `SPI_CFG1.MBR`, sec.67.11.3). Se elige **el divisor mas pequeno cuyo `f_sck`
/// no pase del reloj sancionado**, o sea el reloj mas alto que cabe dentro de
/// la sancion. La comparacion va en `u64` sin dividir (`f_ker <= f_sck_max *
/// div`) para que el truncamiento de la division entera no deje pasar un reloj
/// por encima del sancionado.
///
/// **Contrato de la frontera:** si ni `/256` baja del sancionado -- incluido el
/// caso `f_sck_max_hz = 0` --, devuelve `(7, f_ker/256)`. No es un `Option`: la
/// funcion es total, y **el llamador asevera** que el `f_sck` devuelto cabe en
/// la sancion. Asi el driver imprime siempre el reloj real antes de morir.
pub fn mbr_y_f_sck(f_ker_hz: u32, f_sck_max_hz: u32) -> (u8, u32) {
    let mut mbr = 7u8;
    for n in 0..8u8 {
        if f_ker_hz as u64 <= (f_sck_max_hz as u64) << (n + 1) {
            mbr = n;
            break;
        }
    }
    (mbr, f_ker_hz / (1u32 << (mbr + 1)))
}

/// Cuantos ciclos de CPU dura un cuarto de `T_SCK` (spec D2, enmienda del
/// 11-09).
///
/// La espera entre `SPE = 1` y `CSTART` va en ciclos de CPU y no con
/// `embassy_time`, cuyo grano de 1 us es diez veces el ciclo de SCK. El
/// redondeo es **hacia arriba** y el minimo es 1: un retardo corto por
/// truncamiento es exactamente lo que la enmienda quiere evitar.
///
/// **Contrato de la frontera:** con `f_sck_hz = 0` no hay `T_SCK`, asi que el
/// cuarto es infinito y devuelve `u32::MAX` en vez de dividir entre cero. El
/// llamador asevera `f_sck > 0` antes de llegar aqui.
pub fn ciclos_por_cuarto_tsck(f_cpu_hz: u32, f_sck_hz: u32) -> u32 {
    let cuarto = 4u64 * f_sck_hz as u64;
    if cuarto == 0 {
        return u32::MAX;
    }
    ((f_cpu_hz as u64).div_ceil(cuarto) as u32).max(1)
}

/// El calendario de los giros de una ranura (spec D5.1, enmienda del 2026-10-16).
///
/// Dice cuando toca el proximo giro. Con el giro a tiempo sigue la rejilla de
/// `periodo_us` exacta. Con un giro que se pasa del periodo **no recupera los
/// tics perdidos**: deja un periodo entero de hueco y cuenta un atraso.
///
/// Por que existe: el `Ticker` de embassy si los recupera (`embassy-time`,
/// `timer.rs:470-480`: `next` suma `duration` a `expires_at` y devuelve `Ready`
/// mientras siga atrasado). Con un giro mas largo que el periodo eso encadena
/// giros sin parar, el ejecutor del J2 no se queda nunca sin trabajo y el hilo
/// no corre jamas. Medido el 2026-10-15 en la NUCLEO-N657X0-Q, con giros de unos
/// 335 us contra 125: la CPU al 100 % dentro de excepciones, `main` sin
/// ejecutarse y el esclavo sin lanzar (#428). El hueco es ademas lo que el
/// esclavo necesita para rearmar (cabecera D8, `T_GAP`).
///
/// No degrada por salud (D7.1: la salud es una marca que sube, no una cadencia
/// que baja): degrada por **carga**, y lo dice con un contador. Un atraso es un
/// fallo del presupuesto de CPU, no del modulo.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Calendario {
    periodo_us: u64,
    proximo_us: u64,
    atrasos: u32,
}

impl Calendario {
    /// El primer giro toca un periodo despues de `ahora_us`, como el `Ticker`.
    pub const fn nuevo(periodo_us: u32, ahora_us: u64) -> Calendario {
        Calendario {
            periodo_us: periodo_us as u64,
            proximo_us: ahora_us + periodo_us as u64,
            atrasos: 0,
        }
    }

    /// Cuando toca el proximo giro, en microsegundos del reloj de la tarea.
    pub const fn proximo_us(&self) -> u64 {
        self.proximo_us
    }

    /// Giros que acabaron cuando ya tocaba el siguiente. Se satura: dar la
    /// vuelta a cero borraria la evidencia de una sobrecarga.
    pub const fn atrasos(&self) -> u32 {
        self.atrasos
    }

    /// Se llama al terminar un giro **y todo lo que la tarea hace con el**,
    /// justo antes de esperar: lo que cuenta es cuando queda libre la CPU. Si
    /// el siguiente hueco de la rejilla ya paso (o es ahora mismo) el giro no
    /// dejo respiro: cuenta un atraso y el proximo toca un periodo despues de
    /// `ahora_us`. Despues de la llamada `proximo_us > ahora_us` siempre, y
    /// nunca por mas de un periodo.
    pub fn giro_terminado(&mut self, ahora_us: u64) {
        self.proximo_us += self.periodo_us;
        if self.proximo_us <= ahora_us {
            self.atrasos = self.atrasos.saturating_add(1);
            self.proximo_us = ahora_us + self.periodo_us;
        }
    }

    /// Tras un plazo vencido (D4): un periodo de hueco desde `ahora_us`, para
    /// el rearme del esclavo, y sin contar atraso, que ya esta contado como
    /// plazo vencido. Es el `Ticker::reset` de la enmienda del 2026-09-18.
    pub fn reanclar(&mut self, ahora_us: u64) {
        self.proximo_us = ahora_us + self.periodo_us;
    }
}

/// Los dos estados de una ranura (spec D7.4).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Estado {
    /// Sin identidad por I2C. No se cloca, no se cuenta, no tiene marcas.
    /// Sin esto, cada ranura vacia contaria `subidas_malas` a 8 kHz y daria la
    /// vuelta al `u32` en seis dias de instrumento encendido (S-15).
    Vacia,
    Activa,
}

/// Lo que le pasa a una ranura. Los nombres son los de la spec D8.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Evento {
    /// El descubrimiento por I2C le dio (`true`) o le quito (`false`)
    /// identidad. El punto a punto D2 manda que el descubrimiento preceda a
    /// "la primera palabra de SPI".
    Identidad(bool),
    /// Se armo una transferencia. Es el sello de vitalidad que el J2 le aporta
    /// al supervisor del hub (D5.4): se escribe al ARMAR, no al completar,
    /// porque una ranura reiniciando tambien esta viva.
    Armada,
    /// Mi periferico termino la transferencia.
    GiroOk,
    /// El plazo vencio sin que terminara.
    PlazoVencido,
    /// Llego un `EOT` de una generacion vieja, despues de vencido el plazo.
    EotTardio,
    /// El sobre que subio el modulo tenia CRC bueno.
    SubidaOk,
    /// El sobre que subio el modulo tenia CRC malo, o el modulo no contesto.
    SubidaMala,
    /// Pasa el tiempo sin que ocurra nada. Deja deslizar la ventana.
    Tick,
}

/// Lo unico que la politica puede mandar hacer.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Accion {
    Nada,
    /// El reinicio de D4, en su orden. Lo ejecuta `fw`, no `core`.
    Reiniciar,
}

/// Una ranura del J2, con su politica y sus cinco contadores.
///
/// `giros` mide "mi periferico termino"; `subidas_ok` mide "el modulo
/// contesto". Son dos cosas distintas y por eso se cuentan aparte (D7.3): un
/// modulo muerto con el MISO en pull-down da `EOT` perfecto y ceros, asi que
/// `giros` no lo ve y `subidas_malas` si.
#[derive(Clone, Copy, Debug)]
pub struct Ranura {
    umbrales: Umbrales,
    estado: Estado,
    giros: u32,
    plazos_vencidos: u32,
    eot_tardios: u32,
    subidas_ok: u32,
    subidas_malas: u32,
    malas_seguidas: u32,
    /// Anillo con los instantes de los ultimos plazos vencidos. Solo hacen
    /// falta `umbral_inestable`, y `VENTANA_MAX` los acota.
    ultimos: [u64; VENTANA_MAX],
    n_ultimos: usize,
    ahora_us: u64,
}

impl Ranura {
    pub const fn nueva(umbrales: Umbrales) -> Ranura {
        Ranura {
            umbrales,
            estado: Estado::Vacia,
            giros: 0,
            plazos_vencidos: 0,
            eot_tardios: 0,
            subidas_ok: 0,
            subidas_malas: 0,
            malas_seguidas: 0,
            ultimos: [0; VENTANA_MAX],
            n_ultimos: 0,
            ahora_us: 0,
        }
    }

    pub fn paso(&mut self, ev: Evento, ahora_us: u64) -> Accion {
        self.ahora_us = ahora_us;

        // La identidad se atiende siempre: es lo unico que saca de `Vacia`.
        // Los contadores NO se borran: son totales desde el arranque, no desde
        // la identidad (spec sec.7 test 2).
        if let Evento::Identidad(presente) = ev {
            self.estado = if presente {
                Estado::Activa
            } else {
                Estado::Vacia
            };
            return Accion::Nada;
        }

        // R-MJ6: una ranura sin identidad no se cloca ni se cuenta.
        if matches!(self.estado, Estado::Vacia) {
            return Accion::Nada;
        }

        match ev {
            Evento::GiroOk => {
                self.giros += 1;
                Accion::Nada
            }
            Evento::PlazoVencido => {
                self.plazos_vencidos += 1;
                self.anota_plazo(ahora_us);
                Accion::Reiniciar
            }
            // Ese EOT pertenece a una generacion vieja: se descarta y se
            // cuenta, pero la trama SI salio al cable y el modulo no la ve
            // como perdida (spec D2, regla 1). No hay nada que reiniciar.
            Evento::EotTardio => {
                self.eot_tardios += 1;
                Accion::Nada
            }
            Evento::SubidaOk => {
                self.subidas_ok += 1;
                self.malas_seguidas = 0;
                Accion::Nada
            }
            Evento::SubidaMala => {
                self.subidas_malas += 1;
                self.malas_seguidas += 1;
                Accion::Nada
            }
            Evento::Armada | Evento::Tick => Accion::Nada,
            Evento::Identidad(_) => Accion::Nada,
        }
    }

    fn anota_plazo(&mut self, ahora_us: u64) {
        if self.n_ultimos < VENTANA_MAX {
            self.ultimos[self.n_ultimos] = ahora_us;
            self.n_ultimos += 1;
        } else {
            self.ultimos.rotate_left(1);
            self.ultimos[VENTANA_MAX - 1] = ahora_us;
        }
    }

    /// Muchos plazos vencidos en poco tiempo.
    ///
    /// **Es informacion, no accion**: no cambia lo que la tarea hace (spec
    /// D7.3). La v1 de la spec la usaba para bajar la cadencia y la junta lo
    /// tumbo: bajar la cadencia garantiza el release del modulo, que es justo
    /// lo que se queria evitar.
    pub fn inestable(&self) -> bool {
        let n = self.umbrales.umbral_inestable as usize;
        if self.n_ultimos < n {
            return false;
        }
        // El n-esimo mas reciente. Si cabe en la ventana, hay n dentro.
        let mas_viejo = self.ultimos[self.n_ultimos - n];
        self.ahora_us.saturating_sub(mas_viejo) <= self.umbrales.ventana_salud_us as u64
    }

    /// El modulo lleva muchas subidas SEGUIDAS sin contestar bien.
    ///
    /// Es el testigo que la v1 no tenia (V-10): la subida lleva el sobre con su
    /// CRC en cada giro (cabecera D6.1), asi que el maestro sabe en cada giro
    /// si el modulo contesto. Un modulo muerto es `muda` en 5 ms aunque el
    /// periferico del cerebro de `EOT` perfecto.
    pub fn muda(&self) -> bool {
        self.malas_seguidas >= self.umbrales.umbral_muda
    }

    pub fn estado(&self) -> Estado {
        self.estado
    }
    pub fn giros(&self) -> u32 {
        self.giros
    }
    pub fn plazos_vencidos(&self) -> u32 {
        self.plazos_vencidos
    }
    pub fn eot_tardios(&self) -> u32 {
        self.eot_tardios
    }
    pub fn subidas_ok(&self) -> u32 {
        self.subidas_ok
    }
    pub fn subidas_malas(&self) -> u32 {
        self.subidas_malas
    }
}

/// Las seis ranuras. Cada una con su maquina; ninguna sabe de las otras.
///
/// La independencia no es elegancia: un plazo vencido en una ranura no puede
/// retrasar a las otras cinco (spec D5.1), y la cuenta de salud es por ranura
/// para que un cuelgue en una no ensucie la ventana de las demas (H-1).
#[derive(Clone, Copy, Debug)]
pub struct Maestro {
    ranuras: [Ranura; RANURAS_SPI],
}

impl Maestro {
    pub const fn nuevo(umbrales: Umbrales) -> Maestro {
        Maestro {
            ranuras: [Ranura::nueva(umbrales); RANURAS_SPI],
        }
    }

    /// Fuera de rango no hace nada, como `bahia.rs` y `partes.rs`: el rango lo
    /// valida quien despacha, y un panico en el N657 es un reset del
    /// instrumento.
    pub fn paso(&mut self, ranura: usize, ev: Evento, ahora_us: u64) -> Accion {
        match self.ranuras.get_mut(ranura) {
            Some(r) => r.paso(ev, ahora_us),
            None => Accion::Nada,
        }
    }

    pub fn ranura(&self, ranura: usize) -> Option<&Ranura> {
        self.ranuras.get(ranura)
    }
}

use core::sync::atomic::{AtomicU32, Ordering};

/// Las banderas de `SR` que la ISR copia (D2): `EOT`, `SUSP`, `OVR`, `MODF`.
/// Un `u8` para que quepan en la palabra guardada del `Turno`.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Banderas(u8);

impl Banderas {
    pub const NINGUNA: Banderas = Banderas(0);
    pub const EOT: Banderas = Banderas(1);
    pub const SUSP: Banderas = Banderas(2);
    pub const OVR: Banderas = Banderas(4);
    pub const MODF: Banderas = Banderas(8);
    pub const fn con(self, otra: Banderas) -> Banderas {
        Banderas(self.0 | otra.0)
    }
    pub const fn bits(self) -> u8 {
        self.0
    }
    pub const fn de_bits(bits: u8) -> Banderas {
        Banderas(bits)
    }
    pub const fn eot(self) -> bool {
        self.0 & Self::EOT.0 != 0
    }
    pub const fn susp(self) -> bool {
        self.0 & Self::SUSP.0 != 0
    }
}

/// El turno de una transferencia: la generacion y el resultado guardado
/// (spec D2, reglas 1 y 2). Lo comparten la ISR y la tarea, por eso va con
/// atomicos y vive en un `static` de `fw`: la ISR `registra`, la tarea `arma`
/// y `toma`. La generacion 0 es "nunca armada".
///
/// `guardado` empaqueta en una palabra `VALIDO | generacion[22:0] << 8 |
/// banderas`, para que registrar y tomar sean un solo acceso atomico y no
/// haya lectura rota entre dos palabras.
pub struct Turno {
    generacion: AtomicU32,
    guardado: AtomicU32,
    tardios: AtomicU32,
}

const VALIDO: u32 = 1 << 31;
const MASCARA_GEN: u32 = (1 << 23) - 1;

impl Turno {
    pub const fn nuevo() -> Turno {
        Turno {
            generacion: AtomicU32::new(0),
            guardado: AtomicU32::new(0),
            tardios: AtomicU32::new(0),
        }
    }

    /// Nueva generacion (nunca 0) y borra lo guardado (regla 2). Devuelve la
    /// generacion y cuantos resultados se descartaron por tardios desde el
    /// armado anterior (regla 1): los que la ISR registro con una generacion
    /// que ya no era la armada, mas el que quedo guardado sin que la tarea
    /// lo tomara.
    pub fn armar(&self) -> (u32, u32) {
        let mut g = self.generacion.load(Ordering::Relaxed).wrapping_add(1);
        if g == 0 {
            g = 1;
        }
        self.generacion.store(g, Ordering::Release);
        let viejo = self.guardado.swap(0, Ordering::AcqRel);
        let sobrante = (viejo & VALIDO != 0) as u32;
        (g, self.tardios.swap(0, Ordering::AcqRel) + sobrante)
    }

    /// Desde la ISR. Guarda solo si `generacion` es la armada (regla 1); si
    /// no, lo cuenta como tardio y devuelve `false`.
    pub fn registrar(&self, generacion: u32, banderas: Banderas) -> bool {
        if generacion == 0 || generacion != self.generacion.load(Ordering::Acquire) {
            self.tardios.fetch_add(1, Ordering::AcqRel);
            return false;
        }
        let palabra = VALIDO | ((generacion & MASCARA_GEN) << 8) | banderas.bits() as u32;
        self.guardado.store(palabra, Ordering::Release);
        true
    }

    /// Desde la tarea. Devuelve y borra el resultado de la generacion armada.
    pub fn tomar(&self) -> Option<Banderas> {
        let armada = self.generacion.load(Ordering::Acquire) & MASCARA_GEN;
        let v = self.guardado.load(Ordering::Acquire);
        if v & VALIDO == 0 || (v >> 8) & MASCARA_GEN != armada {
            return None;
        }
        self.guardado.store(0, Ordering::Release);
        Some(Banderas::de_bits(v as u8))
    }

    pub fn generacion(&self) -> u32 {
        self.generacion.load(Ordering::Acquire)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn activa() -> Ranura {
        let mut r = Ranura::nueva(Umbrales::POR_DEFECTO);
        r.paso(Evento::Identidad(true), 0);
        r
    }

    // --- el calendario: un giro que se pasa del periodo no encadena al siguiente

    #[test]
    fn a_tiempo_el_calendario_sigue_la_rejilla_sin_importar_cuanto_dure_el_giro() {
        // Primer giro a las 125; cada uno termina antes de su siguiente hueco.
        // (duracion del giro, fin del giro, proximo esperado) -- a mano.
        let tabla: [(u64, u64); 4] = [(40, 250), (124, 375), (1, 500), (0, 625)];
        let mut c = Calendario::nuevo(125, 0);
        assert_eq!(c.proximo_us(), 125);
        let mut inicio = 125u64;
        for (duracion, proximo) in tabla {
            c.giro_terminado(inicio + duracion);
            assert_eq!(c.proximo_us(), proximo, "giro de {duracion} us");
            inicio = proximo;
        }
        assert_eq!(c.atrasos(), 0);
    }

    #[test]
    fn un_giro_mas_largo_que_el_periodo_deja_un_periodo_entero_de_hueco() {
        // El caso de la placa del 15-10: giros de 335 us con periodo de 125.
        // Empieza a las 1000, termina a las 1335. Con el comportamiento del
        // Ticker el proximo seria 1125, que ya paso: giros pegados, CPU al 100 %.
        let mut c = Calendario::nuevo(125, 875);
        assert_eq!(c.proximo_us(), 1000);
        c.giro_terminado(1335);
        assert_eq!(c.proximo_us(), 1460);
        assert_eq!(c.atrasos(), 1);
    }

    #[test]
    fn saturado_el_hueco_entre_giros_se_mantiene_en_un_periodo() {
        // 100 giros de 335 us. Cada ciclo son 335 de giro y 125 de hueco: 460.
        // El primero arranca a las 125, asi que el proximo tras el giro 100 es
        // 125 + 100 x 460 = 46125.
        let mut c = Calendario::nuevo(125, 0);
        let mut inicio = c.proximo_us();
        for _ in 0..100 {
            let fin = inicio + 335;
            c.giro_terminado(fin);
            assert_eq!(
                c.proximo_us() - fin,
                125,
                "hueco tras el giro que acaba en {fin}"
            );
            inicio = c.proximo_us();
        }
        assert_eq!(c.proximo_us(), 46_125);
        assert_eq!(c.atrasos(), 100);
    }

    #[test]
    fn el_atraso_empieza_justo_en_el_siguiente_hueco() {
        // Termina a 1 us del siguiente hueco: a tiempo. En el hueco: tarde,
        // porque un giro que acaba cuando ya toca otro no deja ningun respiro.
        let mut a_tiempo = Calendario::nuevo(125, 875);
        a_tiempo.giro_terminado(1124);
        assert_eq!((a_tiempo.proximo_us(), a_tiempo.atrasos()), (1125, 0));

        let mut justo = Calendario::nuevo(125, 875);
        justo.giro_terminado(1125);
        assert_eq!((justo.proximo_us(), justo.atrasos()), (1250, 1));
    }

    #[test]
    fn para_cualquier_duracion_el_proximo_giro_queda_en_el_futuro_a_lo_sumo_un_periodo() {
        // Se barre la duracion entera, de 0 a tres periodos: dos valores a mano
        // coincidirian con y sin la politica. Lo que se afirma no sale del codigo.
        for duracion in 0..=375u64 {
            let mut c = Calendario::nuevo(125, 0);
            let ahora = c.proximo_us() + duracion;
            c.giro_terminado(ahora);
            assert!(
                c.proximo_us() > ahora,
                "duracion {duracion}: el proximo ya paso"
            );
            assert!(
                c.proximo_us() - ahora <= 125,
                "duracion {duracion}: espera de mas"
            );
            let tarde = duracion >= 125;
            assert_eq!(c.atrasos(), tarde as u32, "duracion {duracion}");
            if !tarde {
                assert_eq!(
                    c.proximo_us(),
                    250,
                    "duracion {duracion}: se salio de la rejilla"
                );
            }
        }
    }

    #[test]
    fn tras_un_plazo_vencido_se_reancla_a_un_periodo_y_no_cuenta_atraso() {
        // D4/D5.1: el giro vencio su plazo y acabo a las 1300. Hueco de un
        // periodo para el rearme del esclavo, y el atraso no se cuenta: ya
        // esta contado como plazo vencido.
        let mut c = Calendario::nuevo(125, 875);
        c.reanclar(1300);
        assert_eq!(c.proximo_us(), 1425);
        assert_eq!(c.atrasos(), 0);
    }

    #[test]
    fn el_contador_de_atrasos_se_satura_y_no_da_la_vuelta() {
        // Dar la vuelta a cero borraria la evidencia de una sobrecarga. Se
        // empieza a uno del maximo: el primer atraso tiene que llegar al
        // maximo y el segundo quedarse ahi.
        let mut c = Calendario::nuevo(125, 0);
        c.atrasos = u32::MAX - 1;
        c.giro_terminado(10_000);
        assert_eq!(c.atrasos(), u32::MAX);
        c.giro_terminado(20_000);
        assert_eq!(c.atrasos(), u32::MAX);
    }

    // --- 10: los tipos rechazan lo que no sirve -------------------------

    #[test]
    fn umbrales_rechazan_lo_que_no_sirve_para_avisar() {
        assert!(Umbrales::nuevos(2, 20, 1_000_000, 10, 40).is_some());

        // 400 giros x 125 us = 50 ms = la ventana del modulo, justo. No vale:
        // la marca subiria a la vez que el release, no antes.
        assert!(Umbrales::nuevos(2, 20, 1_000_000, 10, 400).is_none());
        // Y uno menos tampoco, porque la cota es estricta por un motivo: la
        // marca tiene que llegar ANTES.
        assert!(Umbrales::nuevos(2, 20, 1_000_000, 10, 399).is_some());

        // Un umbral_inestable que no cabe en el anillo de la ventana.
        assert!(Umbrales::nuevos(2, 20, 1_000_000, VENTANA_MAX as u32 + 1, 40).is_none());
        assert!(Umbrales::nuevos(2, 20, 1_000_000, VENTANA_MAX as u32, 40).is_some());

        // Ceros que dejarian una marca que nunca sube o un plazo nulo.
        assert!(Umbrales::nuevos(0, 20, 1_000_000, 10, 40).is_none());
        assert!(Umbrales::nuevos(2, 20, 1_000_000, 0, 40).is_none());
        assert!(Umbrales::nuevos(2, 20, 1_000_000, 10, 0).is_none());

        // R-MJ1 en el tipo: TSIZE cero no se puede construir.
        assert!(Tsize::nuevo(0).is_none());
        assert!(Tsize::nuevo(25).is_some());
    }

    #[test]
    fn el_por_defecto_cumple_sus_propias_cotas() {
        let d = Umbrales::POR_DEFECTO;
        assert_eq!(
            Umbrales::nuevos(
                d.factor_plazo,
                d.t_suelo_plazo_us,
                d.ventana_salud_us,
                d.umbral_inestable,
                d.umbral_muda
            ),
            Some(d),
            "POR_DEFECTO no pasa el constructor que valida: uno de los dos miente"
        );
    }

    // --- el plazo ------------------------------------------------------

    #[test]
    fn el_plazo_sale_de_la_trama_y_respeta_su_cota() {
        let u = Umbrales::POR_DEFECTO;

        // Un HOLA de 9 bytes al piso de 10 MHz son 7,2 us nominales -> 8 al
        // redondear arriba; con factor 2 serian 16, por debajo del suelo mas
        // el suelo. La cuenta entera: 2*8 + 20 = 36.
        let hola = Tsize::nuevo(9).unwrap();
        assert_eq!(plazo_us(hola, 10_000_000, &u), 36);

        // 125 B x 8 / 10 MHz = 100 us, la cota de R-E1. Plazo = 2*100 + 20.
        let largo = Tsize::nuevo(125).unwrap();
        assert_eq!(plazo_us(largo, 10_000_000, &u), 220);

        // La cota de R-E1, barrida entera: NINGUN tsize que respete los 100 us
        // nominales al piso puede pedir mas de 220 us de plazo.
        for bytes in 1..=125u16 {
            let t = Tsize::nuevo(bytes).unwrap();
            assert!(
                plazo_us(t, 10_000_000, &u) <= 220,
                "tsize {bytes} pide mas de 220 us"
            );
        }

        // Mas reloj, menos plazo -- pero nunca por debajo del suelo.
        let a_34_5 = plazo_us(largo, 34_500_000, &u);
        assert!(a_34_5 < 220 && a_34_5 >= u.t_suelo_plazo_us);

        // El redondeo es hacia ARRIBA: 1 byte a 34,5 MHz son 0,23 us, y un
        // plazo truncado a cero mas suelo seria 20; con techo, 22.
        assert_eq!(plazo_us(Tsize::nuevo(1).unwrap(), 34_500_000, &u), 22);
    }

    // --- 1..5, 9: la maquina -------------------------------------------

    #[test]
    fn vacia_no_cloca_ni_cuenta() {
        let mut r = Ranura::nueva(Umbrales::POR_DEFECTO);
        assert_eq!(r.estado(), Estado::Vacia);
        for ev in [
            Evento::Armada,
            Evento::GiroOk,
            Evento::PlazoVencido,
            Evento::EotTardio,
            Evento::SubidaOk,
            Evento::SubidaMala,
            Evento::Tick,
        ] {
            assert_eq!(r.paso(ev, 0), Accion::Nada, "{ev:?} hizo algo en Vacia");
        }
        assert_eq!(r.giros(), 0);
        assert_eq!(r.plazos_vencidos(), 0);
        assert_eq!(r.eot_tardios(), 0);
        assert_eq!(r.subidas_ok(), 0);
        assert_eq!(r.subidas_malas(), 0);
        assert!(!r.inestable() && !r.muda());
        assert_eq!(r.estado(), Estado::Vacia);
    }

    #[test]
    fn la_identidad_activa_y_vacia_sin_borrar_la_cuenta() {
        let mut r = activa();
        assert_eq!(r.estado(), Estado::Activa);
        r.paso(Evento::GiroOk, 0);
        assert_eq!(r.giros(), 1);

        r.paso(Evento::Identidad(false), 0);
        assert_eq!(r.estado(), Estado::Vacia);
        assert_eq!(r.giros(), 1, "los contadores son totales desde el arranque");

        r.paso(Evento::Identidad(true), 0);
        assert_eq!(r.estado(), Estado::Activa);
        assert_eq!(r.giros(), 1);
    }

    #[test]
    fn cada_evento_cuenta_lo_suyo() {
        let mut r = activa();
        r.paso(Evento::GiroOk, 0);
        r.paso(Evento::SubidaOk, 0);
        r.paso(Evento::SubidaMala, 0);
        assert_eq!((r.giros(), r.subidas_ok(), r.subidas_malas()), (1, 1, 1));
        // Armada y Tick no cuentan nada: son sello y tiempo.
        r.paso(Evento::Armada, 0);
        r.paso(Evento::Tick, 0);
        assert_eq!((r.giros(), r.subidas_ok(), r.subidas_malas()), (1, 1, 1));
    }

    #[test]
    fn plazo_vencido_reinicia_y_eot_tardio_no() {
        let mut r = activa();

        assert_eq!(r.paso(Evento::PlazoVencido, 0), Accion::Reiniciar);
        assert_eq!(r.plazos_vencidos(), 1);

        // No hay estado intermedio del que salir: el giro siguiente cuenta
        // como siempre (spec sec.7 test 4).
        assert_eq!(r.paso(Evento::GiroOk, PERIODO_GIRO_US as u64), Accion::Nada);
        assert_eq!(r.giros(), 1);

        assert_eq!(r.paso(Evento::EotTardio, 0), Accion::Nada);
        assert_eq!(r.eot_tardios(), 1);
        assert_eq!(r.plazos_vencidos(), 1, "un EOT tardio no es un plazo mas");
    }

    #[test]
    fn los_contadores_no_bajan_nunca() {
        let mut r = activa();
        let evs = [
            Evento::GiroOk,
            Evento::PlazoVencido,
            Evento::EotTardio,
            Evento::SubidaOk,
            Evento::SubidaMala,
            Evento::Armada,
            Evento::Tick,
            Evento::Identidad(false),
            Evento::Identidad(true),
        ];
        let mut previo = (0u32, 0u32, 0u32, 0u32, 0u32);
        let mut t = 0u64;
        for vuelta in 0..90 {
            r.paso(evs[vuelta % evs.len()], t);
            t += PERIODO_GIRO_US as u64;
            let ahora = (
                r.giros(),
                r.plazos_vencidos(),
                r.eot_tardios(),
                r.subidas_ok(),
                r.subidas_malas(),
            );
            assert!(
                ahora.0 >= previo.0
                    && ahora.1 >= previo.1
                    && ahora.2 >= previo.2
                    && ahora.3 >= previo.3
                    && ahora.4 >= previo.4,
                "un contador bajo en la vuelta {vuelta}"
            );
            previo = ahora;
        }
    }

    // --- 6, 7, 8: las marcas -------------------------------------------

    #[test]
    fn inestable_sube_al_decimo_en_un_segundo_y_baja_al_deslizar() {
        let mut r = activa();
        let u = Umbrales::POR_DEFECTO;

        for i in 0..(u.umbral_inestable - 1) {
            r.paso(Evento::PlazoVencido, i as u64 * 1000);
            assert!(!r.inestable(), "subio con {}", i + 1);
        }
        r.paso(Evento::PlazoVencido, (u.umbral_inestable - 1) as u64 * 1000);
        assert!(r.inestable(), "el decimo cabe justo y tiene que subir");

        // Y baja cuando la ventana desliza mas alla del mas viejo.
        r.paso(Evento::Tick, u.ventana_salud_us as u64 + 1);
        assert!(!r.inestable());
    }

    #[test]
    fn inestable_no_sube_si_estan_repartidos_en_mas_de_un_segundo() {
        let mut r = activa();
        let u = Umbrales::POR_DEFECTO;
        // Diez, pero uno cada 200 ms: nunca hay diez dentro de la ventana.
        for i in 0..u.umbral_inestable {
            r.paso(Evento::PlazoVencido, i as u64 * 200_000);
            assert!(!r.inestable(), "subio en el {}", i + 1);
        }
        assert_eq!(r.plazos_vencidos(), u.umbral_inestable);
    }

    #[test]
    fn muda_sube_a_las_cuarenta_seguidas_y_baja_con_una_buena() {
        let mut r = activa();
        let u = Umbrales::POR_DEFECTO;
        for i in 0..(u.umbral_muda - 1) {
            r.paso(Evento::SubidaMala, i as u64 * PERIODO_GIRO_US as u64);
            assert!(!r.muda(), "subio con {}", i + 1);
        }
        r.paso(Evento::SubidaMala, 0);
        assert!(r.muda());

        r.paso(Evento::SubidaOk, 0);
        assert!(!r.muda(), "una subida buena la baja: son SEGUIDAS");
    }

    #[test]
    fn las_marcas_nunca_cambian_la_accion() {
        let mut r = activa();
        let u = Umbrales::POR_DEFECTO;
        for i in 0..u.umbral_muda {
            r.paso(Evento::SubidaMala, i as u64 * 10);
        }
        for i in 0..u.umbral_inestable {
            r.paso(Evento::PlazoVencido, i as u64 * 10);
        }
        assert!(r.inestable() && r.muda());

        assert_eq!(r.paso(Evento::PlazoVencido, 0), Accion::Reiniciar);
        assert_eq!(r.paso(Evento::GiroOk, 0), Accion::Nada);
        assert_eq!(r.paso(Evento::EotTardio, 0), Accion::Nada);
    }

    // --- 11: mutacion ---------------------------------------------------

    #[test]
    fn las_seis_ranuras_son_independientes() {
        let mut m = Maestro::nuevo(Umbrales::POR_DEFECTO);
        for r in 0..RANURAS_SPI {
            m.paso(r, Evento::Identidad(true), 0);
        }

        assert_eq!(m.paso(3, Evento::PlazoVencido, 0), Accion::Reiniciar);
        for r in 0..RANURAS_SPI {
            let esperado = if r == 3 { 1 } else { 0 };
            assert_eq!(
                m.ranura(r).unwrap().plazos_vencidos(),
                esperado,
                "la ranura {r} se entero de un plazo ajeno"
            );
        }

        // Y las marcas tampoco se contagian.
        for i in 0..Umbrales::POR_DEFECTO.umbral_muda {
            m.paso(3, Evento::SubidaMala, i as u64 * 10);
        }
        assert!(m.ranura(3).unwrap().muda());
        for r in 0..RANURAS_SPI {
            if r != 3 {
                assert!(!m.ranura(r).unwrap().muda(), "la ranura {r} se contagio");
            }
        }
    }

    #[test]
    fn una_ranura_fuera_de_rango_no_existe_ni_panica() {
        let mut m = Maestro::nuevo(Umbrales::POR_DEFECTO);
        assert_eq!(m.paso(RANURAS_SPI, Evento::GiroOk, 0), Accion::Nada);
        assert_eq!(m.paso(usize::MAX, Evento::PlazoVencido, 0), Accion::Nada);
        assert!(m.ranura(RANURAS_SPI).is_none());
    }

    // --- Turno (D2, reglas 1 y 2) ---

    #[test]
    fn turno_arma_generaciones_crecientes_y_nunca_cero() {
        let t = Turno::nuevo();
        assert_eq!(
            t.generacion(),
            0,
            "sin armar, la generacion es 0: nunca armada"
        );
        let (g1, tardios1) = t.armar();
        let (g2, tardios2) = t.armar();
        assert_ne!(g1, 0);
        assert_eq!(g2, g1 + 1);
        assert_eq!((tardios1, tardios2), (0, 0));
    }

    #[test]
    fn registrar_solo_acepta_la_generacion_armada() {
        let t = Turno::nuevo();
        let (g, _) = t.armar();
        assert!(t.registrar(g, Banderas::EOT));
        assert!(
            !t.registrar(g + 1, Banderas::EOT),
            "una generacion que no es la armada se descarta"
        );
        assert!(
            !t.registrar(0, Banderas::EOT),
            "la generacion 0 nunca esta armada"
        );
    }

    #[test]
    fn tomar_devuelve_una_vez_y_borra() {
        let t = Turno::nuevo();
        let (g, _) = t.armar();
        assert_eq!(t.tomar(), None, "antes de la ISR no hay nada");
        t.registrar(g, Banderas::EOT);
        assert_eq!(t.tomar(), Some(Banderas::EOT));
        assert_eq!(t.tomar(), None, "el resultado se consume una sola vez");
    }

    #[test]
    fn armar_borra_lo_guardado_y_lo_cuenta_como_tardio() {
        // La ISR llego despues de vencido el plazo: la tarea no lo tomo. Al
        // armar la siguiente se descarta y se cuenta (D2 regla 1, `eot_tardios`).
        let t = Turno::nuevo();
        let (g, _) = t.armar();
        t.registrar(g, Banderas::EOT);
        let (_, tardios) = t.armar();
        assert_eq!(tardios, 1);
        assert_eq!(
            t.tomar(),
            None,
            "la generacion nueva no hereda el resultado viejo (regla 2)"
        );
    }

    #[test]
    fn registrar_una_generacion_vieja_cuenta_tardio_al_siguiente_armar() {
        let t = Turno::nuevo();
        let (g, _) = t.armar();
        let _ = t.armar();
        assert!(!t.registrar(g, Banderas::EOT));
        let (_, tardios) = t.armar();
        assert_eq!(tardios, 1);
    }

    #[test]
    fn los_tardios_se_entregan_una_sola_vez() {
        let t = Turno::nuevo();
        let (g, _) = t.armar();
        t.registrar(g, Banderas::EOT);
        assert_eq!(t.armar().1, 1);
        assert_eq!(t.armar().1, 0);
    }

    #[test]
    fn las_banderas_viajan_enteras() {
        let t = Turno::nuevo();
        let (g, _) = t.armar();
        t.registrar(g, Banderas::EOT.con(Banderas::SUSP));
        let b = t.tomar().unwrap();
        assert!(b.eot() && b.susp());
        assert_eq!(b.bits(), Banderas::EOT.bits() | Banderas::SUSP.bits());
        assert_eq!(Banderas::de_bits(b.bits()), b);
    }

    // --- El MBR y los ciclos del retardo (spec D1, D2 enmienda del 11-09) ---

    #[test]
    fn el_mbr_divide_exacto_cuando_puede() {
        // 64 MHz de kernel, 32 MHz pedidos: /2, que es MBR = 0, y clava.
        assert_eq!(mbr_y_f_sck(64_000_000, 32_000_000), (0, 32_000_000));
        // 64 MHz y 8 MHz: /8, que es MBR = 2.
        assert_eq!(mbr_y_f_sck(64_000_000, 8_000_000), (2, 8_000_000));
        // El piso legado del J2, 10 MHz, desde 64: /8 da 8 MHz y /4 daria 16,
        // que pasa del sancionado. Gana /8, y el reloj real NO es el pedido.
        assert_eq!(mbr_y_f_sck(64_000_000, 10_000_000), (2, 8_000_000));
    }

    #[test]
    fn el_mbr_nunca_pasa_del_sancionado_por_truncamiento() {
        // 10_000_001 / 2 = 5_000_000,5: la division entera daria 5_000_000 y
        // "cumple", pero el reloj real pasaria del sancionado por medio hercio.
        // Con la cuenta en u64 el divisor elegido es el siguiente.
        let (mbr, f_sck) = mbr_y_f_sck(10_000_001, 5_000_000);
        assert!(f_sck <= 5_000_000, "f_sck {} pasa del sancionado", f_sck);
        assert_eq!(mbr, 1);
    }

    #[test]
    fn el_mbr_se_queda_en_256_cuando_ni_asi_baja() {
        // Contrato: si ni /256 baja del sancionado, se devuelve MBR = 7 y el
        // f_sck que sale de /256. NO es un Option: el llamador asevera.
        let (mbr, f_sck) = mbr_y_f_sck(64_000_000, 100_000);
        assert_eq!(mbr, 7);
        assert_eq!(f_sck, 64_000_000 / 256);
        assert!(f_sck > 100_000);
    }

    #[test]
    fn el_mbr_con_sancionado_cero_cae_en_la_misma_rama() {
        // Mismo contrato que arriba: MBR = 7, f_sck = f_ker / 256, y el
        // llamador asevera. Asi `mbr_y_f_sck` es total y no entra en panico.
        assert_eq!(mbr_y_f_sck(64_000_000, 0), (7, 64_000_000 / 256));
    }

    #[test]
    fn los_ciclos_del_cuarto_redondean_hacia_arriba() {
        // Multiplo exacto: 64 MHz de CPU, 8 MHz de SCK -> 4 * 8 = 32 MHz,
        // 64/32 = 2 ciclos clavados.
        assert_eq!(ciclos_por_cuarto_tsck(64_000_000, 8_000_000), 2);
        // Sin multiplo exacto: 800 MHz y 10 MHz -> 800/40 = 20.
        assert_eq!(ciclos_por_cuarto_tsck(800_000_000, 10_000_000), 20);
        // 800 MHz y 34,5 MHz -> 800/138 = 5,79... -> 6, nunca 5: el retardo
        // corto es el que la enmienda del 11-09 quiere evitar.
        assert_eq!(ciclos_por_cuarto_tsck(800_000_000, 34_500_000), 6);
    }

    #[test]
    fn los_ciclos_del_cuarto_nunca_son_cero() {
        // CPU mas lenta que 4 * SCK: la cuenta da 0 y el retardo desapareceria.
        assert_eq!(ciclos_por_cuarto_tsck(64_000_000, 64_000_000), 1);
        assert_eq!(ciclos_por_cuarto_tsck(1, 64_000_000), 1);
    }

    #[test]
    fn sin_reloj_el_cuarto_es_infinito() {
        // Contrato de la frontera: `f_sck = 0` devuelve `u32::MAX` en vez de
        // dividir entre cero. El llamador asevera `f_sck > 0` antes de llegar.
        assert_eq!(ciclos_por_cuarto_tsck(64_000_000, 0), u32::MAX);
    }
}
