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
    /// Los ocho pasos de D4, en orden. Los ejecuta `fw`, no `core`.
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

#[cfg(test)]
mod tests {
    use super::*;

    fn activa() -> Ranura {
        let mut r = Ranura::nueva(Umbrales::POR_DEFECTO);
        r.paso(Evento::Identidad(true), 0);
        r
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
}
