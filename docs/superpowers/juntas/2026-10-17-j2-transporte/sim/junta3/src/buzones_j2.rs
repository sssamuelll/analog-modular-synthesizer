//! Los buzones del transporte «por tic»: lo que cruza entre el tic (nivel 1) y el
//! planificador (nivel 3) sin que ninguno espere al otro.
//!
//! Spec: `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v2.md`, §2.6 y
//! §2.7. **Prototipo de banco** (acta del 17-10, ficha 3), como `transporte_j2`.
//!
//! Aqui solo estan los **indices y los contadores**; los bufferes viven en `fw`,
//! en la region no cacheable de R-MJ7. Tres piezas, cada una con un escritor y un
//! lector fijos:
//!
//! - [`Anillo`]: los eventos de la politica. Los empuja el tic, los saca el
//!   planificador.
//! - [`Triple`]: la bajada. El planificador compone en un buffer, lo publica; el
//!   tic lo consume al armar. **Tres bufferes y no dos** (el papel decia doble): con
//!   dos, el planificador reescribe en sitio la trama fresca, y un tic que llegue a
//!   mitad de la escritura arma una trama a medias.
//! - [`Subida`]: la respuesta del modulo. El tic la publica al cerrar, el
//!   planificador la copia y comprueba que el tic no la haya pisado mientras tanto.
//!
//! Todo con atomicos de un solo nucleo: el tic es de mayor prioridad y puede
//! interrumpir al planificador en cualquier instruccion, nunca al reves.

use core::sync::atomic::{AtomicU32, AtomicU8, Ordering};

use crate::maestro_j2::Evento;

/// El codigo de un evento en el anillo. El cero queda libre: una casilla sin escribir.
pub const fn codigo(e: Evento) -> u8 {
    match e {
        Evento::Identidad(false) => 1,
        Evento::Identidad(true) => 2,
        Evento::Armada => 3,
        Evento::GiroOk => 4,
        Evento::PlazoVencido => 5,
        Evento::EotTardio => 6,
        Evento::SubidaOk => 7,
        Evento::SubidaMala => 8,
        Evento::Tick => 9,
    }
}

/// Al reves de [`codigo`]. `None` para el cero y para cualquier numero que no sea un codigo.
pub const fn evento_de(c: u8) -> Option<Evento> {
    match c {
        1 => Some(Evento::Identidad(false)),
        2 => Some(Evento::Identidad(true)),
        3 => Some(Evento::Armada),
        4 => Some(Evento::GiroOk),
        5 => Some(Evento::PlazoVencido),
        6 => Some(Evento::EotTardio),
        7 => Some(Evento::SubidaOk),
        8 => Some(Evento::SubidaMala),
        9 => Some(Evento::Tick),
        _ => None,
    }
}

/// El anillo de eventos de una ranura. `N` es potencia de dos y no pasa de 128, para
/// que los contadores de 8 bits den la vuelta sin ambiguedad.
///
/// Si esta lleno, el evento nuevo se **descarta y se cuenta** ([`Anillo::perdidos`]):
/// la politica pierde un evento, que es un fallo del planificador y tiene que verse.
pub struct Anillo<const N: usize> {
    datos: [AtomicU8; N],
    cabeza: AtomicU8,
    cola: AtomicU8,
    perdidos: AtomicU32,
}

impl<const N: usize> Anillo<N> {
    pub const fn nuevo() -> Anillo<N> {
        assert!(N.is_power_of_two() && N <= 128);
        Anillo {
            datos: [const { AtomicU8::new(0) }; N],
            cabeza: AtomicU8::new(0),
            cola: AtomicU8::new(0),
            perdidos: AtomicU32::new(0),
        }
    }

    /// Del productor. `false` si estaba lleno.
    pub fn empujar(&self, e: Evento) -> bool {
        let cabeza = self.cabeza.load(Ordering::Relaxed);
        let cola = self.cola.load(Ordering::Acquire);
        if cabeza.wrapping_sub(cola) as usize >= N {
            self.perdidos.fetch_add(1, Ordering::Relaxed);
            return false;
        }
        self.datos[cabeza as usize % N].store(codigo(e), Ordering::Relaxed);
        self.cabeza.store(cabeza.wrapping_add(1), Ordering::Release);
        true
    }

    /// Del consumidor.
    pub fn sacar(&self) -> Option<Evento> {
        let cola = self.cola.load(Ordering::Relaxed);
        if cola == self.cabeza.load(Ordering::Acquire) {
            return None;
        }
        let c = self.datos[cola as usize % N].load(Ordering::Relaxed);
        self.cola.store(cola.wrapping_add(1), Ordering::Release);
        evento_de(c)
    }

    /// Cuantos eventos se descartaron por estar lleno.
    pub fn perdidos(&self) -> u32 {
        self.perdidos.load(Ordering::Relaxed)
    }
}

/// El buzon de bajada: tres casillas y quien tiene cada una.
///
/// - `atras`: la del **escritor** (el planificador). Compone en ella.
/// - `medio`: la ultima publicada y aun no consumida, con el bit [`SUCIO`], o la que
///   dejo el lector al consumir, sin el bit.
/// - `frente`: la del **lector** (el tic): la que el DMA esta leyendo o leyo la ultima vez.
///
/// Las tres son siempre una permutacion de 0, 1 y 2: por eso el escritor nunca toca la
/// que lee el DMA ni la que el tic va a coger.
///
/// **El lector no puede ser interrumpido por el escritor** entre [`Triple::fresca`] y
/// [`Triple::consumir`] (en el banco, el tic es de mayor nivel que el planificador).
pub struct Triple {
    medio: AtomicU8,
    atras: AtomicU8,
    frente: AtomicU8,
    superadas: AtomicU32,
}

/// El bit de «publicada y sin consumir» de `medio`.
const SUCIO: u8 = 0x80;

impl Triple {
    pub const fn nuevo() -> Triple {
        Triple {
            medio: AtomicU8::new(1),
            atras: AtomicU8::new(0),
            frente: AtomicU8::new(2),
            superadas: AtomicU32::new(0),
        }
    }

    /// Del escritor: la casilla donde puede escribir ahora.
    pub fn casilla_escritura(&self) -> usize {
        self.atras.load(Ordering::Relaxed) as usize
    }

    /// Del escritor: publica lo escrito en [`Triple::casilla_escritura`]. Si habia una
    /// trama publicada que nadie consumio, la nueva la sustituye y se cuenta.
    pub fn publicar(&self) {
        let atras = self.atras.load(Ordering::Relaxed);
        let viejo = self.medio.swap(atras | SUCIO, Ordering::AcqRel);
        if viejo & SUCIO != 0 {
            self.superadas.fetch_add(1, Ordering::Relaxed);
        }
        self.atras.store(viejo & !SUCIO, Ordering::Relaxed);
    }

    /// Del lector: la casilla de la trama fresca, sin consumirla.
    pub fn fresca(&self) -> Option<usize> {
        let m = self.medio.load(Ordering::Acquire);
        (m & SUCIO != 0).then_some((m & !SUCIO) as usize)
    }

    /// Del lector: consume la trama fresca y devuelve su casilla. La que el lector
    /// tenia pasa a ser la del medio, libre para el escritor.
    pub fn consumir(&self) -> Option<usize> {
        if self.medio.load(Ordering::Relaxed) & SUCIO == 0 {
            return None;
        }
        let frente = self.frente.load(Ordering::Relaxed);
        let viejo = self.medio.swap(frente, Ordering::AcqRel);
        let nueva = viejo & !SUCIO;
        self.frente.store(nueva, Ordering::Relaxed);
        Some(nueva as usize)
    }

    /// Cuantas tramas publicadas se sustituyeron sin que el tic las armara.
    pub fn superadas(&self) -> u32 {
        self.superadas.load(Ordering::Relaxed)
    }

    #[cfg(test)]
    fn casillas(&self) -> [u8; 3] {
        [
            self.atras.load(Ordering::Relaxed),
            self.medio.load(Ordering::Relaxed) & !SUCIO,
            self.frente.load(Ordering::Relaxed),
        ]
    }
}

/// Lo que el planificador encuentra al leer una subida.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Lectura {
    /// No hay ningun cierre que no se haya leido ya.
    Nada,
    /// La copia es buena: salio de esta casilla y el tic no la piso.
    Nueva(usize),
    /// El tic cerro otra vez mientras se copiaba: la copia puede estar rota. Se descarta.
    Rota,
}

/// La publicacion de la subida de una ranura: cuantos cierres lleva el tic y en que
/// casilla dejo el ultimo.
///
/// El tic arma el DMA de recepcion en la casilla `i`, y al cerrar la publica y arma
/// la `1 - i`. La casilla publicada es **segura mientras el contador no cambie**: en
/// el siguiente cierre el tic arma otra vez la `i`, y el DMA empieza a escribir en ella
/// a los pocos microsegundos.
pub struct Subida {
    cierres: AtomicU32,
    ultima: AtomicU8,
    vistos: AtomicU32,
    perdidas: AtomicU32,
}

impl Subida {
    pub const fn nueva() -> Subida {
        Subida {
            cierres: AtomicU32::new(0),
            ultima: AtomicU8::new(0),
            vistos: AtomicU32::new(0),
            perdidas: AtomicU32::new(0),
        }
    }

    /// Del tic, al cerrar: la subida esta en `casilla`.
    pub fn publicar(&self, casilla: usize) {
        self.ultima.store(casilla as u8, Ordering::Relaxed);
        self.cierres.fetch_add(1, Ordering::Release);
    }

    /// Del planificador: copia la ultima subida con `copiar(casilla)` y comprueba que
    /// el tic no haya cerrado otra vez mientras tanto.
    pub fn leer(&self, copiar: impl FnOnce(usize)) -> Lectura {
        let antes = self.cierres.load(Ordering::Acquire);
        let vistos = self.vistos.load(Ordering::Relaxed);
        if antes == vistos {
            return Lectura::Nada;
        }
        let casilla = self.ultima.load(Ordering::Relaxed) as usize;
        copiar(casilla);
        // Los cierres que se saltaron sin leer: todos menos el que se acaba de copiar.
        let saltados = antes.wrapping_sub(vistos) - 1;
        self.vistos.store(antes, Ordering::Relaxed);
        self.perdidas.fetch_add(saltados, Ordering::Relaxed);
        if self.cierres.load(Ordering::Acquire) != antes {
            self.perdidas.fetch_add(1, Ordering::Relaxed);
            return Lectura::Rota;
        }
        Lectura::Nueva(casilla)
    }

    /// Subidas que el planificador no pudo entregar: cierres que nadie leyo y copias rotas.
    pub fn perdidas(&self) -> u32 {
        self.perdidas.load(Ordering::Relaxed)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::VecDeque;

    /// Un generador pseudoaleatorio de bolsillo, como el de `transporte_j2`.
    struct Xorshift(u64);
    impl Xorshift {
        fn sig(&mut self) -> u64 {
            self.0 ^= self.0 << 13;
            self.0 ^= self.0 >> 7;
            self.0 ^= self.0 << 17;
            self.0
        }
        fn azar(&mut self, de_cada: u64) -> bool {
            self.sig().is_multiple_of(de_cada)
        }
    }

    const TODOS: [Evento; 9] = [
        Evento::Identidad(false),
        Evento::Identidad(true),
        Evento::Armada,
        Evento::GiroOk,
        Evento::PlazoVencido,
        Evento::EotTardio,
        Evento::SubidaOk,
        Evento::SubidaMala,
        Evento::Tick,
    ];

    // --- codigo ---------------------------------------------------------------------

    #[test]
    fn todo_evento_vuelve_de_su_codigo_y_el_cero_no_es_ninguno() {
        for e in TODOS {
            assert_eq!(evento_de(codigo(e)), Some(e), "{e:?}");
            assert_ne!(codigo(e), 0);
        }
        assert_eq!(evento_de(0), None);
        assert_eq!(evento_de(10), None);
        assert_eq!(evento_de(255), None);
    }

    #[test]
    fn dos_eventos_distintos_no_comparten_codigo() {
        for (i, a) in TODOS.iter().enumerate() {
            for b in &TODOS[i + 1..] {
                assert_ne!(codigo(*a), codigo(*b), "{a:?} y {b:?}");
            }
        }
    }

    // --- Anillo ---------------------------------------------------------------------

    #[test]
    fn el_anillo_vacio_no_devuelve_nada() {
        let a: Anillo<8> = Anillo::nuevo();
        assert_eq!(a.sacar(), None);
        assert_eq!(a.perdidos(), 0);
    }

    #[test]
    fn el_anillo_entrega_en_el_orden_en_que_se_empujo() {
        let a: Anillo<8> = Anillo::nuevo();
        for e in [Evento::GiroOk, Evento::Armada, Evento::PlazoVencido] {
            assert!(a.empujar(e));
        }
        assert_eq!(a.sacar(), Some(Evento::GiroOk));
        assert_eq!(a.sacar(), Some(Evento::Armada));
        assert_eq!(a.sacar(), Some(Evento::PlazoVencido));
        assert_eq!(a.sacar(), None);
    }

    #[test]
    fn el_anillo_lleno_descarta_el_nuevo_lo_cuenta_y_conserva_los_viejos() {
        let a: Anillo<4> = Anillo::nuevo();
        for _ in 0..4 {
            assert!(a.empujar(Evento::GiroOk));
        }
        assert!(!a.empujar(Evento::PlazoVencido));
        assert!(!a.empujar(Evento::PlazoVencido));
        assert_eq!(a.perdidos(), 2);
        for _ in 0..4 {
            assert_eq!(a.sacar(), Some(Evento::GiroOk));
        }
        assert_eq!(a.sacar(), None);
        // Y vuelve a funcionar tras vaciarse.
        assert!(a.empujar(Evento::Tick));
        assert_eq!(a.sacar(), Some(Evento::Tick));
    }

    #[test]
    fn el_anillo_da_la_vuelta_a_los_contadores_de_ocho_bits_sin_perder_el_orden() {
        let a: Anillo<8> = Anillo::nuevo();
        // 3000 vueltas de empujar dos y sacar dos: los contadores pasan de 255 varias veces.
        for i in 0..3000usize {
            let x = TODOS[i % TODOS.len()];
            let y = TODOS[(i * 7 + 3) % TODOS.len()];
            assert!(a.empujar(x));
            assert!(a.empujar(y));
            assert_eq!(a.sacar(), Some(x), "vuelta {i}");
            assert_eq!(a.sacar(), Some(y), "vuelta {i}");
        }
        assert_eq!(a.perdidos(), 0);
    }

    #[test]
    fn el_anillo_se_comporta_como_una_cola_acotada_que_descarta_la_nueva() {
        for semilla in 1..=20u64 {
            let mut r = Xorshift(semilla.wrapping_mul(0x9E37_79B9_7F4A_7C15));
            let a: Anillo<8> = Anillo::nuevo();
            let mut modelo: VecDeque<Evento> = VecDeque::new();
            let mut perdidos = 0u32;
            for _ in 0..5000 {
                if r.azar(2) {
                    let e = TODOS[(r.sig() % 9) as usize];
                    let cabe = modelo.len() < 8;
                    assert_eq!(a.empujar(e), cabe);
                    if cabe {
                        modelo.push_back(e);
                    } else {
                        perdidos += 1;
                    }
                } else {
                    assert_eq!(a.sacar(), modelo.pop_front());
                }
            }
            assert_eq!(a.perdidos(), perdidos, "semilla {semilla}");
        }
    }

    // --- Triple ---------------------------------------------------------------------

    #[test]
    fn el_buzon_nuevo_no_tiene_trama_fresca() {
        let t = Triple::nuevo();
        assert_eq!(t.fresca(), None);
        assert_eq!(t.consumir(), None);
        assert_eq!(t.superadas(), 0);
        let mut c = t.casillas();
        c.sort();
        assert_eq!(c, [0, 1, 2]);
    }

    #[test]
    fn lo_publicado_se_consume_una_sola_vez() {
        let t = Triple::nuevo();
        let w = t.casilla_escritura();
        t.publicar();
        assert_eq!(t.fresca(), Some(w));
        assert_eq!(t.consumir(), Some(w));
        assert_eq!(t.fresca(), None);
        assert_eq!(t.consumir(), None);
        assert_eq!(t.superadas(), 0);
    }

    #[test]
    fn publicar_dos_veces_sin_consumir_deja_solo_la_ultima_y_cuenta_la_sustituida() {
        let t = Triple::nuevo();
        let primera = t.casilla_escritura();
        t.publicar();
        let segunda = t.casilla_escritura();
        assert_ne!(primera, segunda, "no se reescribe en sitio la trama fresca");
        t.publicar();
        assert_eq!(t.superadas(), 1);
        assert_eq!(t.consumir(), Some(segunda));
        assert_eq!(t.consumir(), None);
    }

    #[test]
    fn las_tres_casillas_son_siempre_una_permutacion() {
        let mut r = Xorshift(12345);
        let t = Triple::nuevo();
        for _ in 0..10_000 {
            match r.sig() % 3 {
                0 => t.publicar(),
                1 => {
                    let _ = t.consumir();
                }
                _ => {
                    let _ = t.fresca();
                }
            }
            let mut c = t.casillas();
            c.sort();
            assert_eq!(c, [0, 1, 2]);
        }
    }

    #[test]
    fn el_escritor_nunca_recibe_la_casilla_que_el_lector_tiene_ni_la_fresca() {
        // El modelo lleva una marca por casilla. El escritor escribe una marca nueva en
        // su casilla y publica; el lector consume y apunta la marca de lo que recibe.
        // Mientras el lector "tiene" su casilla (el DMA la lee), nadie debe escribirla.
        for semilla in 1..=20u64 {
            let mut r = Xorshift(semilla.wrapping_mul(0xD1B5_4A32_D192_ED03));
            let t = Triple::nuevo();
            let mut marca = [0u32; 3];
            let mut siguiente = 1u32;
            let mut ultima_publicada: Option<u32> = None;
            let mut lector: Option<(usize, u32)> = None; // casilla y marca que el DMA lee
            for _ in 0..20_000 {
                if r.azar(2) {
                    // Escritor: escribe y publica.
                    let w = t.casilla_escritura();
                    if let Some((c, m)) = lector {
                        assert_ne!(w, c, "el escritor pisa la casilla del lector");
                        assert_eq!(marca[c], m);
                    }
                    marca[w] = siguiente;
                    ultima_publicada = Some(siguiente);
                    siguiente += 1;
                    t.publicar();
                } else if let Some(c) = t.consumir() {
                    // Lector: tiene que recibir exactamente la ultima publicada.
                    assert_eq!(Some(marca[c]), ultima_publicada, "no es la ultima");
                    ultima_publicada = None;
                    lector = Some((c, marca[c]));
                }
                if let Some((c, m)) = lector {
                    assert_eq!(marca[c], m, "la casilla del lector cambio bajo sus pies");
                }
            }
        }
    }

    #[test]
    fn el_escritor_a_medias_no_deja_al_tic_armar_una_trama_rota() {
        // El caso que el doble buzon del papel v2 no resolvia: el tic llega con el
        // escritor a mitad de la composicion. Aqui la casilla del escritor aun no esta
        // publicada, asi que el tic ve lo que ya habia (o nada), nunca la rota.
        let t = Triple::nuevo();
        let primera = t.casilla_escritura();
        t.publicar();
        let a_medias = t.casilla_escritura(); // el escritor empieza a componer...
        assert_eq!(t.fresca(), Some(primera)); // ...y el tic llega ahora
        assert_eq!(t.consumir(), Some(primera));
        assert_ne!(primera, a_medias);
        // El escritor termina y publica: la proxima vez el tic coge esta.
        t.publicar();
        assert_eq!(t.fresca(), Some(a_medias));
    }

    // --- Subida ---------------------------------------------------------------------

    #[test]
    fn sin_cierres_no_hay_nada_que_leer() {
        let s = Subida::nueva();
        assert_eq!(s.leer(|_| panic!("no hay nada que copiar")), Lectura::Nada);
        assert_eq!(s.perdidas(), 0);
    }

    #[test]
    fn una_subida_se_lee_una_vez_y_de_la_casilla_publicada() {
        let s = Subida::nueva();
        s.publicar(1);
        let mut copiada = None;
        assert_eq!(s.leer(|c| copiada = Some(c)), Lectura::Nueva(1));
        assert_eq!(copiada, Some(1));
        assert_eq!(s.leer(|_| panic!("ya se leyo")), Lectura::Nada);
        assert_eq!(s.perdidas(), 0);
    }

    #[test]
    fn dos_cierres_sin_leer_entregan_el_ultimo_y_cuentan_el_otro_como_perdido() {
        let s = Subida::nueva();
        s.publicar(0);
        s.publicar(1);
        assert_eq!(s.leer(|_| {}), Lectura::Nueva(1));
        assert_eq!(s.perdidas(), 1);
        assert_eq!(s.leer(|_| {}), Lectura::Nada);
    }

    #[test]
    fn un_cierre_durante_la_copia_la_marca_rota_y_se_cuenta() {
        let s = Subida::nueva();
        s.publicar(0);
        // El tic cierra otra vez mientras el planificador copia.
        let r = s.leer(|_| s.publicar(1));
        assert_eq!(r, Lectura::Rota);
        assert_eq!(s.perdidas(), 1);
        // Lo que el tic publico durante la copia se lee en la vuelta siguiente.
        assert_eq!(s.leer(|_| {}), Lectura::Nueva(1));
        assert_eq!(s.perdidas(), 1);
    }

    #[test]
    fn cada_cierre_acaba_leido_perdido_o_pendiente() {
        // Conservacion: cierres = leidas buenas + perdidas + (1 si hay una sin leer).
        for semilla in 1..=20u64 {
            let mut r = Xorshift(semilla.wrapping_mul(0x2545_F491_4F6C_DD1D));
            let s = Subida::nueva();
            let (mut cierres, mut buenas) = (0u32, 0u32);
            for _ in 0..5000 {
                match r.sig() % 4 {
                    0 | 1 => {
                        s.publicar((cierres % 2) as usize);
                        cierres += 1;
                    }
                    2 => {
                        if let Lectura::Nueva(_) = s.leer(|_| {}) {
                            buenas += 1;
                        }
                    }
                    _ => {
                        // Lectura interrumpida por un cierre.
                        let antes = cierres;
                        let l = s.leer(|_| {
                            s.publicar((antes % 2) as usize);
                        });
                        if l != Lectura::Nada {
                            cierres += 1;
                        }
                        if let Lectura::Nueva(_) = l {
                            buenas += 1;
                        }
                    }
                }
            }
            let pendiente = u32::from(matches!(s.leer(|_| {}), Lectura::Nueva(_)));
            assert_eq!(
                cierres,
                buenas + s.perdidas() + pendiente,
                "semilla {semilla}"
            );
        }
    }
}
