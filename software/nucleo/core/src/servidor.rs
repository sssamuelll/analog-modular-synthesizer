//! Donde el contrato deja de ser piezas y contesta.
//!
//! El modelo, la retencion, el protocolo y el descriptor existian por separado
//! y **nada los unia**. `atender` es la funcion que hace que un `SET` que llega
//! por el cable mueva un parametro, avise a los suscriptores y responda.
//!
//! Es pura —el tiempo entra como argumento, no se lee de ningun reloj— asi que
//! se prueba entera sin placa.
//!
//! # La regla que la gobierna
//!
//! **Ningun cliente se queda en silencio.** Toda peticion produce respuesta: la
//! que pedia, o un `ERROR` que dice por que no. Un agente que escribe y no
//! recibe nada no sabe si llego, si se aplico, o si el instrumento se colgo.

// El #182 fue, entero, la misma linea escrita seis veces: `let _ = algo()`
// donde `algo()` devolvia un `Result` que importaba. `unused_must_use` no lo
// ve -- `let _ =` es justo su valvula de escape -- asi que aqui la clase
// entera es un error de compilacion. Si algun dia hace falta descartar un
// `Result` a proposito, que sea con un `#[allow]` y su razon escrita al lado,
// no con un `let _` que no se distingue de un olvido.
#![deny(clippy::let_underscore_must_use)]

use crate::medidas;
use crate::modelo::{ErrorSet, Modelo};
use crate::param::{ParamId, Valor};
use crate::politica::{Politica, Puerta, Regla};
use crate::protocolo::{etiqueta_de, CodigoError, Mensaje};
use crate::rampa::{Rampa, Rampas, MAX_RAMPAS};
use crate::rejilla::PPQN_INTERNO;
use crate::rejilla::{siguiente_borde, Rejilla};
use crate::reloj::{Fuente, Reloj};
use crate::retencion::Retenidas;
use crate::tiempo_params;
use heapless::Vec;

/// La version que este firmware sabe hablar.
pub const VERSION_PROTOCOLO: u16 = 1;
/// Las cinco medidas del reloj que `publicar_medidas_del_reloj` publica en
/// cada tick, y que desde el #182 fallo 4 SI producen `CHANGED`.
const MEDIDAS_POR_TICK: usize = 5;

/// Los suscriptores que el instrumento puede tener HOY: **uno**.
///
/// No es una eleccion, es una lectura: `suscrito` es un `bool`, no un
/// conjunto. Esta constante existe para que el termino aparezca en la formula
/// del buzon en vez de estar escondido dentro de un `1` implicito. El #145
/// vuelve `suscrito` un conjunto; quien lo haga sube este numero, y las
/// aserciones de abajo dicen si el buzon aguanta o hay que rederivarlo.
const MAX_SUSCRIPTORES: usize = 1;

/// DERIVADO del peor caso real, no elegido.
///
/// Estuvo en 4, con el comentario "lo mas que produce una sola peticion:
/// `ERROR` + `PENDING` son dos, y el margen sobra". Era cierto cuando se
/// escribio y dejo de serlo sin que nadie lo notara: despues llegaron
/// `Reactivar { id: None }`, que empuja un `Anulado` por rampa reactivada
/// (hasta `MAX_RAMPAS`), y `tick()`, que anuncia hasta `MAX_RAMPAS` valores.
/// Los dos desbordaban EN SILENCIO, porque todos los push eran `let _ =`.
/// Es el #182, fallos 1 y 3.
///
/// **Y estuvo en `MAX_RAMPAS + MEDIDAS_POR_TICK + 2` con el comentario "al
/// derivarlo de `MAX_RAMPAS` deja de poder quedarse viejo", que era falso.**
/// El fan-out de un tick tiene TRES factores -- `(rampas + medidas) x
/// suscriptores` -- y la formula solo seguia a uno. Hoy no reventaba porque
/// `MAX_SUSCRIPTORES` es 1 y multiplicar por uno no se nota; con dos pieles
/// abiertas, un tick produce `(16 + 5) * 2 = 42` en un buzon de 23.
///
/// Ahora el termino esta escrito, y las aserciones de abajo cubren los
/// caminos que la formula sola no puede cubrir -- entre ellos `caducar()`,
/// que esta acotado por `MAX_RETENIDAS` y no aparecia por ningun lado.
pub const MAX_RESPUESTAS: usize = (MAX_RAMPAS + MEDIDAS_POR_TICK) * MAX_SUSCRIPTORES + 2;

/// Lo mas que el reloj recupera de un solo golpe, en pulsos internos.
///
/// Si el firmware se atasca -- un volcado de descriptores largo, un cliente
/// que no drena su endpoint -- al volver puede haber miles de pulsos debidos.
/// Generarlos todos seria un lazo sin cota DENTRO de un tick, y ademas
/// dispararia miles de escrituras de rampa de golpe.
///
/// **Pasado el tope el reloj NO salta: se atrasa.** Aqui decia "salta", y no
/// es lo mismo -- saltar seria adelantar la posicion perdiendo la generacion
/// intermedia; lo que pasa es que la hora de pared avanza entera y la posicion
/// no, asi que el compas queda corrido contra el reloj para siempre.
///
/// Acumular la deuda tampoco vale: soltar diez mil pulsos de golpe es una
/// rafaga de escrituras, que musicalmente es peor que el atraso. Asi que se
/// descarta -- y por eso se CUENTA, en `pulsos_perdidos()`. Lo inaceptable no
/// era perder tiempo musical en un atasco: era que no se notara.
///
/// POR_CONFIRMAR: 960 sale de "cinco segundos a 120 BPM con PPQN_INTERNO=96",
/// no de una medida del peor atasco real. Sale de `arranque_budget.py` el dia
/// que exista (declarado BLOQUEANTE en voz-total S9.4, issue #180).
pub const MAX_PULSOS_POR_AVANCE: u32 = 960;

/// El denominador de la cuenta de pulsos, en unidades de `us x mbpm x PPQN`.
/// Sesenta segundos en microsegundos, por mil (las milesimas del BPM). Se le
/// da nombre porque `avanzar_a` lo usa dos veces y un 60_000_000_000 suelto
/// escrito dos veces es dos sitios donde equivocarse.
const US_MBPM_PPQN_POR_PULSO: u64 = 60_000_000_000;

/// El peor caso de CADA camino que empuja al buzon, aseverado en tiempo de
/// compilacion. Si alguno se pasa, esto **no compila** -- que es la unica
/// forma de que la derivacion no vuelva a quedarse vieja en silencio (#182,
/// fallos 1 y 3). Un test no sirve: `MAX_RESPUESTAS` es el tamaño del `Vec`,
/// asi que para cuando un test corre, el buzon ya se dimensiono.
///
/// Si añades un camino que empuje, añade su renglon aqui.
const _: () = {
    /// `tick()`: hasta `MAX_RAMPAS` escrituras de rampa mas las cinco medidas
    /// del reloj, y cada una se anuncia a cada suscriptor.
    const TICK: usize = (MAX_RAMPAS + MEDIDAS_POR_TICK) * MAX_SUSCRIPTORES;
    /// `Reactivar { id: None }`: un `Anulado` por rampa reactivada -- que es
    /// respuesta al que pidio, no fan-out -- mas el `CHANGED` del contador de
    /// anulados, que si va a cada suscriptor.
    const REACTIVAR_TODAS: usize = MAX_RAMPAS + MAX_SUSCRIPTORES;
    /// `caducar()`: un `Resolved` por retenida vencida. Este era el otro
    /// termino que no aparecia en ninguna parte de la formula vieja.
    const CADUCAR: usize = crate::retencion::MAX_RETENIDAS;
    /// Un `SET` que anula: `Anulado`, `CHANGED` del contador de anulados y
    /// `CHANGED` del parametro. Los dos ultimos van a cada suscriptor.
    const SET_QUE_ANULA: usize = 1 + 2 * MAX_SUSCRIPTORES;
    /// Un `SET` sobre algo que exige confirmacion fisica: `ERROR` + `PENDING`.
    const SET_RETENIDO: usize = 2;
    /// Un `HELLO` de otra version: `HOLA` con la nuestra + `ERROR` con nombre
    /// (N7). Los dos van al que pregunto, no a los suscriptores.
    const HELLO_INCOMPATIBLE: usize = 2;

    assert!(TICK <= MAX_RESPUESTAS);
    assert!(REACTIVAR_TODAS <= MAX_RESPUESTAS);
    assert!(CADUCAR <= MAX_RESPUESTAS);
    assert!(SET_QUE_ANULA <= MAX_RESPUESTAS);
    assert!(SET_RETENIDO <= MAX_RESPUESTAS);
    assert!(HELLO_INCOMPATIBLE <= MAX_RESPUESTAS);
};

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Respuesta {
    Mensaje(Mensaje),
    /// El volcado del descriptor. No es un `Mensaje` porque es de largo
    /// variable y grande: meterlo en la enumeracion obligaria a darle vida
    /// (`Mensaje<'a>`) y a que eso rippleara por todo el codec. La capa de
    /// transporte lo sirve en su propio sobre.
    Descriptores,
}

pub type Respuestas = Vec<Respuesta, MAX_RESPUESTAS>;

/// La ventana de aterrizaje, en pulsos (§5.3 de la spec del tiempo musical).
///
/// **Cero, y no por conservadurismo: por aritmetica.**
/// `hardware/02-midi-cv/tiempo_budget.py` lo demuestra — el error de tiempo
/// del sistema es de 1 ms, y un pulso de la rejilla interna dura entre 2.08 ms
/// (a 300 BPM) y 31.25 ms (a 20 BPM). La rejilla es **mas gruesa que el error**
/// a cualquier tempo del rango, asi que no hay ninguna llegada tarde que
/// redondear. El peor caso son 0.48 pulsos, y el guion asevera que no pase de
/// uno.
pub const VENTANA_ATERRIZAJE: u32 = 0;

pub struct Instrumento {
    modelo: Modelo,
    retenidas: Retenidas,
    rampas: Rampas,
    reloj: Reloj,
    suscrito: bool,
    /// Cuantos mensajes NO cupieron en un buzon, desde el arranque. Ver
    /// `empujar`: es el rastro que el `debug_assert!` no dejaba en release.
    desbordes: u16,
    /// La ultima hora de pared que entro por `avanzar_a`. `0` = nunca.
    ultimo_us: u64,
    /// Lo que sobro del ultimo reparto, sin llegar a un pulso entero.
    resto_pulso: u64,
    /// Pulsos que `MAX_PULSOS_POR_AVANCE` no dejo emitir, desde el arranque.
    pulsos_perdidos: u32,
    /// N1-N3. Vacia por defecto, y vacia significa TODO ABIERTO.
    politica: Politica,
}

impl Default for Instrumento {
    fn default() -> Self {
        Self::nuevo()
    }
}

impl Instrumento {
    pub const fn nuevo() -> Self {
        Instrumento {
            modelo: Modelo::nuevo(),
            retenidas: Retenidas::nueva(),
            rampas: Rampas::nueva(),
            reloj: Reloj::nuevo(),
            suscrito: false,
            desbordes: 0,
            ultimo_us: 0,
            resto_pulso: 0,
            pulsos_perdidos: 0,
            politica: Politica::nueva(),
        }
    }

    /// Un instrumento con lo unico que hoy existe sin periféricos: las medidas
    /// de §7.3. El descubrimiento por I²C llega con el plan de los periféricos.
    ///
    /// #182, fallo 5 de la junta. Los dos registros eran `let _ =`, o sea que
    /// `ErrorRegistro::Lleno` y `Duplicado` se tragaban enteros y la placa
    /// arrancaba con un modelo PARCIAL **en silencio**: el agente pediria un
    /// parametro que el descriptor promete y le contestarian `NoExiste`, sin
    /// nada que explique por que.
    ///
    /// No puede devolver `Result`: `fw/src/main.rs` la llama dentro de
    /// `INSTRUMENTO.init(..)`, que quiere un `Instrumento` y no un `Result`.
    /// Y no hace falta que lo devuelva. Las dos tablas son `static` y suman
    /// mucho menos que `MAX_PARAMS`, asi que esto no puede fallar por nada que
    /// pase en marcha: solo si alguien edita las tablas y mete un id repetido
    /// o se pasa del techo. Eso es un fallo de PROGRAMACION, y el sitio de un
    /// fallo de programacion es el arranque, a gritos -- no un instrumento a
    /// medias que parece sano. En el host lo caza antes el test
    /// `el_instrumento_de_arranque_trae_las_medidas_y_el_reloj`, que cuenta
    /// los parametros; esto es la red por si nadie corrio el test.
    pub fn con_medidas() -> Self {
        let mut i = Self::nuevo();
        medidas::registrar(&mut i.modelo).expect("las medidas de S7.3 no entraron en el modelo");
        tiempo_params::registrar(&mut i.modelo)
            .expect("los parametros de tiempo no entraron en el modelo");
        i
    }

    /// Solo de lectura, y a proposito.
    ///
    /// Al lado vivia `reloj_mut() -> &mut Reloj`, `pub`, con CERO llamadores
    /// en todo el repo -- ni el firmware, ni los tests. Era la misma puerta
    /// que `modelo_mut` (#182, fallo 6) tres lineas mas abajo: abierta para el
    /// primer periferico apurado. Y esta pesa mas, porque el reloj gobierna la
    /// cuantizacion de las rampas y las cinco medidas de §7.3: quien lo mueva
    /// por fuera desplaza los bordes de la rejilla sin que `tick` se entere.
    /// No se cierra a `#[cfg(test)]` como `modelo_mut` porque ningun test lo
    /// usa tampoco, y un `#[cfg(test)]` muerto es una advertencia. El dia que
    /// un periferico necesite mover el reloj, que llegue con su metodo y su
    /// razon escrita.
    pub fn reloj(&self) -> &Reloj {
        &self.reloj
    }

    pub fn modelo(&self) -> &Modelo {
        &self.modelo
    }
    /// SOLO en tests (#182, fallo 6).
    ///
    /// Estuvo `pub`, o sea que exportaba `&mut Modelo` a cualquiera desde el
    /// modulo cuyo docstring dice "si algo muta el instrumento sin pasar por
    /// aqui, el agente no lo alcanza". Nadie de produccion lo usaba: el
    /// firmware arranca con `con_medidas()`, que toca el campo directamente.
    /// Estaba abierto para el primer periferico apurado, y S2.1 se habria
    /// roto sin que nadie lo notara.
    #[cfg(test)]
    fn modelo_mut(&mut self) -> &mut Modelo {
        &mut self.modelo
    }
    pub fn suscrito(&self) -> bool {
        self.suscrito
    }

    /// Cuantos mensajes se perdieron por no caber en un buzon, desde el
    /// arranque. Satura en `u16::MAX`: dar la vuelta a cero despues de 65 536
    /// perdidas seria peor que no contarlas.
    ///
    /// Existe para que el desbordamiento sea DETECTABLE en release. Ver
    /// `empujar` (#182, fallo 2 de la junta).
    /// Pulsos que el tope de `avanzar_a` descarto, desde el arranque. Misma
    /// razon que `desbordes`: si el instrumento pierde tiempo musical, tiene
    /// que poder decirlo en vez de que se note solo en que el compas no cuadra.
    pub fn pulsos_perdidos(&self) -> u32 {
        self.pulsos_perdidos
    }

    pub fn desbordes(&self) -> u16 {
        self.desbordes
    }

    /// Mete una fila en la politica. Estrecho a proposito: un
    /// `politica_mut() -> &mut Politica` seria el `modelo_mut` de #182 otra
    /// vez -- entregar el objeto entero para que cualquiera lo reescriba.
    pub fn cargar_regla(&mut self, r: Regla) -> Result<(), Regla> {
        self.politica.cargar(r)
    }

    /// N6, la mitad «DICHO». El arranque es permisivo, asi que el estado de
    /// la tabla tiene que ser legible desde fuera: sin esto, un CRC malo o una
    /// ranura trabada dan acceso total y silencioso, indistinguible del estado
    /// de fabrica.
    pub fn politica(&self) -> &Politica {
        &self.politica
    }

    /// Lo que llega por el cable, **con la puerta por la que entro**.
    ///
    /// N1. La puerta NO viaja en el mensaje: la estampa el transporte que lo
    /// recibio. Por eso es un parametro y no un campo -- un cliente no puede
    /// mentir sobre por donde entro porque no hay campo que falsificar, y
    /// cuesta cero bytes en el cable.
    ///
    /// Y por eso NO tiene valor por defecto: si `atender` pudiera llamarse sin
    /// decir la puerta, el primer transporte apurado la omitiria y la politica
    /// legislaria sobre un dato que nadie estampo. Que el compilador lo exija
    /// ES la guardia.
    pub fn atender(&mut self, m: Mensaje, ahora_ms: u64, puerta: Puerta) -> Respuestas {
        let mut r = Respuestas::new();
        // Un cliente no puede fabricar un `CHANGED` y mentirle a los demas.
        if m.del_instrumento() {
            self.error(&mut r, &m, CodigoError::Desconocido);
            return r;
        }
        // N2a. La politica se consulta ANTES de tocar nada: un rechazo que
        // igual escribe no es una politica, es un aviso. Y va DESPUES de la
        // guardia de arriba a proposito -- un `CHANGED` fabricado se rechaza
        // venga por donde venga, sin que ninguna tabla pueda permitirlo.
        if !self.politica.permite_mensaje(puerta, &m) {
            self.error(&mut r, &m, CodigoError::PuertaSinPermiso);
            return r;
        }
        match m {
            // N7. Esto era `Hello { .. }`: la version del cliente se leia del
            // cable y se tiraba, y se contestaba `Hola` a cualquiera. El
            // docstring de `Hola` ya lo denunciaba -- "sin esto la negociacion
            // es de un solo sentido y no negocia nada" -- y encima el papel del
            // nucleo y el de la autopista PLANIFICAN rupturas de formato
            // apoyandose en un mecanismo que no funcionaba.
            //
            // El `Hola` sale igual y sale primero, coincida o no: el otro lado
            // necesita saber QUE hablamos para decidir que hacer. Negarse sin
            // decir la version deja al cliente tan a ciegas como el silencio.
            Mensaje::Hello { version } => {
                self.empujar(
                    &mut r,
                    Respuesta::Mensaje(Mensaje::Hola {
                        version: VERSION_PROTOCOLO,
                    }),
                );
                if version != VERSION_PROTOCOLO {
                    self.empujar(
                        &mut r,
                        Respuesta::Mensaje(Mensaje::Error {
                            etiqueta: etiqueta_de(&m),
                            codigo: CodigoError::VersionIncompatible,
                        }),
                    );
                }
            }
            Mensaje::Describe => {
                self.empujar(&mut r, Respuesta::Descriptores);
            }
            Mensaje::Get(id) => match self.modelo.get(id) {
                Some(v) => {
                    self.empujar(&mut r, Respuesta::Mensaje(Mensaje::Changed(id, v)));
                }
                None => self.error(&mut r, &m, CodigoError::NoExiste),
            },
            Mensaje::Set(id, v) => {
                // El SET de un CLIENTE anula la rampa que tenga ese parametro.
                // El del tick no — y esa diferencia vive aqui, no en el
                // modelo, que no gana ninguna puerta nueva.
                if self.rampas.anular(id) {
                    self.empujar(
                        &mut r,
                        Respuesta::Mensaje(Mensaje::Anulado { id, anulado: true }),
                    );
                    self.publicar_anulados(&mut r);
                }
                self.escribir(&mut r, &m, id, v, ahora_ms);
            }
            Mensaje::Rampa {
                id,
                destino,
                duracion,
                curva,
            } => self.arrancar_rampa(&mut r, &m, id, destino, duracion, curva),
            Mensaje::Reactivar { id } => self.reactivar(&mut r, id),
            Mensaje::Subscribe { activo } => self.suscrito = activo,
            Mensaje::Point { .. } => {
                // La cadena WS2812 llega con el plan de los perifericos.
                self.error(&mut r, &m, CodigoError::NoDisponible);
            }
            // Todo esto necesita perifericos o almacenamiento que aun no
            // existen. Callarse seria peor que decir que no.
            Mensaje::PresetList
            | Mensaje::PresetLoad(_)
            | Mensaje::PresetSave(_)
            | Mensaje::TuneStart
            | Mensaje::PatchScan
            | Mensaje::Telemetry
            | Mensaje::Memo { .. } => self.error(&mut r, &m, CodigoError::NoDisponible),
            // Los del instrumento ya se rechazaron arriba.
            _ => self.error(&mut r, &m, CodigoError::Desconocido),
        }
        r
    }

    /// Acepta una rampa, o dice por que no.
    ///
    /// El destino se valida **al aceptarla**: mejor ahora que descubrirlo a
    /// mitad del barrido.
    fn arrancar_rampa(
        &mut self,
        r: &mut Respuestas,
        m: &Mensaje,
        id: ParamId,
        destino: Valor,
        duracion: u32,
        curva: i8,
    ) {
        let Some(d) = self.modelo.descriptor_de(id) else {
            return self.error(r, m, CodigoError::NoExiste);
        };
        if d.solo_lectura {
            return self.error(r, m, CodigoError::SoloLectura);
        }
        if d.confirmacion_fisica {
            return self.error(r, m, CodigoError::ExigeConfirmacion);
        }
        if destino < d.min || destino > d.max {
            return self.error(r, m, CodigoError::FueraDeRango);
        }
        let inicio = siguiente_borde(
            self.reloj.posicion(),
            self.rejilla(),
            self.reloj.pulsos_por_compas(),
            VENTANA_ATERRIZAJE,
        )
        .unwrap_or_else(|| self.reloj.posicion());
        let origen = self.modelo.get(id).unwrap_or(d.def);
        let rampa = Rampa {
            id,
            origen,
            destino,
            inicio,
            duracion,
            curva,
            anulada: false,
        };
        if self.rampas.empujar(rampa).is_err() {
            self.error(r, m, CodigoError::ColaLlena);
        }
    }

    fn reactivar(&mut self, r: &mut Respuestas, id: Option<ParamId>) {
        match id {
            Some(p) => {
                if self.rampas.reactivar(p) {
                    self.empujar(
                        r,
                        Respuesta::Mensaje(Mensaje::Anulado {
                            id: p,
                            anulado: false,
                        }),
                    );
                }
            }
            None => {
                for p in self.rampas.reactivar_todas() {
                    self.empujar(
                        r,
                        Respuesta::Mensaje(Mensaje::Anulado {
                            id: p,
                            anulado: false,
                        }),
                    );
                }
            }
        }
        self.publicar_anulados(r);
    }

    fn rejilla(&self) -> Rejilla {
        self.modelo
            .get(tiempo_params::ID_CUANTIZACION)
            .and_then(Rejilla::de_indice)
            .unwrap_or(Rejilla::Compas1)
    }

    /// #182, fallo 4, la SEXTA medida. Esto tiraba el `Cambio` con `let _` y
    /// no llamaba a `anunciar`, igual que hacian las cinco del reloj antes de
    /// arreglarse -- y `ID_ANULADOS` esta declarado `medida: true` en
    /// `tiempo_params`, con el nucleo S4.1 prometiendo que las medidas se
    /// siguen con `SUBSCRIBE`.
    ///
    /// Se quedo viva porque el test que la cubria aseveraba contra el MODELO
    /// (`i.modelo().get(..)`) y no contra el CABLE: el modelo si se escribia.
    fn publicar_anulados(&mut self, r: &mut Respuestas) {
        let id = tiempo_params::ID_ANULADOS;
        let n = self.rampas.anuladas() as Valor;
        // El mismo filtro que las cinco del reloj, por la misma razon:
        // `publicar_medida` NO filtra, devuelve `Ok` aunque el valor sea
        // identico. `reactivar` llama aqui aunque no haya reactivado nada, asi
        // que sin comparar antes esto anunciaria el mismo cero cada vez.
        let se_movio = self.modelo.get(id) != Some(n);
        if self.modelo.publicar_medida(id, n).is_ok() && se_movio {
            self.anunciar(r, id, n);
        }
    }

    /// Corre el tiempo. Publica las medidas del reloj y escribe lo que las
    /// rampas dicten — **por la ruta que NO anula**, que es la diferencia con
    /// un `SET` de cliente.
    /// El tiempo de pared entra por aqui. Es la contraparte de `atender` para
    /// el reloj.
    ///
    /// EL INSTRUMENTO NO CORRIA. `fw/src/main.rs` arranca dos tareas y ninguna
    /// llamaba a `tick()`, asi que en la placa una rampa aceptada nunca
    /// escribia un valor, las medidas del reloj no se publicaban y la
    /// retencion no caducaba. Lo caza la junta adversarial del 2026-08-24.
    ///
    /// Y no bastaba con llamar a `tick(pulso)` desde el firmware, porque el
    /// firmware NO SABE en que pulso esta: depende del tempo, que vive dentro
    /// del `Reloj`, y `reloj_mut` esta cerrado (#182, fallo 6) y no se
    /// reabre. La cuenta vive aqui, en `core`, que es lo que `fw/src/main.rs`
    /// promete de si mismo: *"capa DELGADA a proposito: si una funcion de aqui
    /// merece un test, es que vive en la caja equivocada"*.
    ///
    /// NO caduca las retenidas: `caducar()` es su propia llamada a proposito.
    /// Meterla aqui sumaria hasta `MAX_RETENIDAS` respuestas a las del tick en
    /// el mismo buzon, y las aserciones `const` de arriba acotan los caminos
    /// POR SEPARADO. El firmware llama a las dos.
    pub fn avanzar_a(&mut self, t_us: u64) -> Respuestas {
        // 1. SIEMPRE, aunque no llegue nada: la caida de una fuente se nota
        //    justamente en que NO llega (reloj.rs, `al_pasar_el_tiempo`).
        self.reloj.al_pasar_el_tiempo(t_us);

        // 2. Con la fuente interna, los pulsos los pone el instrumento: nadie
        //    externo los manda. `tic_interno` avanza UNO por llamada, asi que
        //    hay que emitir los que se deban desde la ultima vez.
        // `ultimo_us == 0` no es un caso especial: el instrumento arranco en
        // t=0, asi que la primera llamada tiene dt legitimo. Lo patologico -- un
        // arranque tardio, un atasco largo -- lo acota MAX_PULSOS_POR_AVANCE,
        // no una guarda que se comeria el primer avance siempre.
        if self.reloj.fuente_activa() == Fuente::Interno {
            let dt = t_us.saturating_sub(self.ultimo_us);
            let mbpm = self.reloj.mbpm() as u64;
            // EL RESTO SE ACUMULA. Antes esto era una division suelta y
            // `ultimo_us` se adelantaba igual, asi que lo que no llegaba a un
            // pulso entero se tiraba en CADA llamada. A la cadencia de los
            // tests (500 ms) no se notaba, porque 500 000 us son exactamente
            // 96 pulsos a 120 BPM: cero resto. A la cadencia del firmware
            // (`PERIODO_TICK`, 1 ms) el cociente es CERO -- hacen falta 5209 us
            // para un solo pulso -- y el reloj no avanzaba nunca en la placa.
            //
            // Se acumula en unidades del numerador (us x mbpm x PPQN) y no en
            // microsegundos por pulso: `60e9 / (120000 x 96)` son 5208,33 us,
            // y redondear eso a 5208 corre el compas ~5 s al dia. Sin
            // division no hay redondeo que arrastrar.
            self.resto_pulso += dt * mbpm * PPQN_INTERNO as u64;
            let debidos = self.resto_pulso / US_MBPM_PPQN_POR_PULSO;
            self.resto_pulso %= US_MBPM_PPQN_POR_PULSO;

            let emitidos = debidos.min(MAX_PULSOS_POR_AVANCE as u64);
            for _ in 0..emitidos {
                self.reloj.tic_interno(t_us);
            }
            // Lo que el tope no emitio se DESCARTA, y por eso se cuenta. El
            // docstring del tope decia que el reloj "salta"; no salta, se
            // atrasa, y el compas queda corrido contra el tiempo de pared para
            // siempre. Acumular la deuda tampoco sirve: soltar diez mil pulsos
            // de golpe es una rafaga de escrituras que musicalmente es peor que
            // el atraso. Lo unico inaceptable era que no se notara.
            self.pulsos_perdidos = self
                .pulsos_perdidos
                .saturating_add((debidos - emitidos) as u32);
        }
        self.ultimo_us = t_us;

        let pulso = self.reloj.posicion();
        self.tick(pulso)
    }

    pub fn tick(&mut self, pulso: u64) -> Respuestas {
        let mut r = Respuestas::new();
        self.reloj.avanzar_a_pulso(pulso);

        let unidad_de = |id: ParamId| {
            self.modelo
                .descriptor_de(id)
                .map(|d| d.unidad)
                .unwrap_or(crate::descriptor::Unidad::Ninguna)
        };
        let escrituras = self.rampas.tick(pulso, unidad_de);
        for (id, v) in escrituras {
            if let Ok(c) = self.modelo.set(id, v) {
                self.anunciar(&mut r, c.id, c.valor);
            }
        }
        self.publicar_medidas_del_reloj(&mut r);
        r
    }

    /// #182, fallo 4. Esto tiraba el `Cambio` con `let _`, asi que las cinco
    /// medidas del reloj no llegaban a nadie, aunque las cinco tienen
    /// `medida: true` y el nucleo S4.1 promete que las medidas se siguen con
    /// `SUBSCRIBE`.
    fn publicar_medidas_del_reloj(&mut self, r: &mut Respuestas) {
        use tiempo_params as tp;
        let pos = self.reloj.posicion().min(i32::MAX as u64) as Valor;
        let compas = self.reloj.compas().min(i32::MAX as u64) as Valor;
        let mbpm = self.reloj.mbpm() as Valor;
        let fase = self.reloj.tiene_fase() as Valor;
        let libre = self.reloj.rodando_libre() as Valor;
        for (id, v) in [
            (tp::ID_POSICION, pos),
            (tp::ID_COMPAS_ACTUAL, compas),
            (tp::ID_TEMPO_MEDIDO, mbpm),
            (tp::ID_TIENE_FASE, fase),
            (tp::ID_RODANDO_LIBRE, libre),
        ] {
            // `publicar_medida` NO filtra: devuelve `Ok` aunque el valor sea
            // identico. Anunciar sin comparar cambiaria un silencio por una
            // inundacion -- cinco `CHANGED` en cada tick, para siempre. Se
            // mira ANTES de escribir, que es la unica forma de saberlo.
            let se_movio = self.modelo.get(id) != Some(v);
            if self.modelo.publicar_medida(id, v).is_ok() && se_movio {
                self.anunciar(r, id, v);
            }
        }
    }

    fn escribir(&mut self, r: &mut Respuestas, m: &Mensaje, id: ParamId, v: Valor, ahora_ms: u64) {
        match self.modelo.set(id, v) {
            Ok(c) => self.anunciar(r, c.id, c.valor),
            Err(ErrorSet::ExigeConfirmacion) => {
                // §2.2: el micro RETIENE. La regla la impone el instrumento.
                self.error(r, m, CodigoError::ExigeConfirmacion);
                match self.retenidas.retener(id, v, ahora_ms) {
                    Ok(token) => {
                        self.empujar(r, Respuesta::Mensaje(Mensaje::Pending { token, id }));
                    }
                    Err(_) => self.error(r, m, CodigoError::ColaLlena),
                }
            }
            Err(e) => self.error(r, m, codigo_de(e)),
        }
    }

    /// El pulsador de la cabeza local o el pedal (§5.2, §5.3).
    pub fn confirmacion_fisica(&mut self, ahora_ms: u64) -> Respuestas {
        let mut r = Respuestas::new();
        let Some(p) = self.retenidas.confirmar(ahora_ms) else {
            return r;
        };
        self.empujar(
            &mut r,
            Respuesta::Mensaje(Mensaje::Resolved {
                token: p.token,
                confirmado: true,
            }),
        );
        if let Ok(c) = self.modelo.aplicar_confirmado(p.id, p.valor) {
            self.anunciar(&mut r, c.id, c.valor);
        }
        r
    }

    /// Se llama periodicamente. Lo que vencio se anuncia: si no, un token
    /// moriria sin que ningun cliente se entere.
    pub fn caducar(&mut self, ahora_ms: u64) -> Respuestas {
        let mut r = Respuestas::new();
        for token in self.retenidas.caducar(ahora_ms) {
            self.empujar(
                &mut r,
                Respuesta::Mensaje(Mensaje::Resolved {
                    token,
                    confirmado: false,
                }),
            );
        }
        r
    }

    /// Lo que mide el instrumento (§3.4). No viene del cable, pero lo que
    /// produce tambien hay que mandarlo.
    pub fn publicar_medida(&mut self, id: ParamId, v: Valor) -> Respuestas {
        let mut r = Respuestas::new();
        if let Ok(c) = self.modelo.publicar_medida(id, v) {
            self.anunciar(&mut r, c.id, c.valor);
        }
        r
    }

    /// Empujar al buzon SIN tragarse el desbordamiento.
    ///
    /// #182, fallo 2 de la junta. Esto era un `debug_assert!` seguido de
    /// `let _ = self.push(x)`, bajo un docstring que decia justo lo
    /// contrario de lo que hacia. `debug_assert!` **se compila fuera en
    /// release** y `fw/Cargo.toml` no declara `debug-assertions`, asi que lo
    /// que se flashea a la placa era el `let _`: el fallo entero, intacto.
    /// El papel de la autopista lo prohibe con todas las letras -- «un envio
    /// que no cabe es un error con nombre, nunca un `let _`».
    ///
    /// El nombre es un contador, no un mensaje. Un `ERROR` nuevo por
    /// desbordamiento cambiaria el formato del protocolo, y esa es la
    /// decision N4, que NO esta tomada. Un contador saturante que la
    /// telemetria lee (`desbordes()`) cabe entero dentro de esa restriccion:
    /// no es tan bueno como avisarle al cliente en el momento, pero es la
    /// diferencia entre una perdida invisible y una medible.
    ///
    /// El contador vive en el `Instrumento` y no en `Respuestas` a proposito:
    /// el buzon se crea y se tira en cada `atender`/`tick`, asi que un
    /// contador dentro de el se iria con la basura antes de que nadie lo
    /// leyera. Por eso `empujar` es un metodo del instrumento y no del `Vec`.
    fn empujar(&mut self, r: &mut Respuestas, x: Respuesta) {
        if r.push(x).is_err() {
            self.desbordes = self.desbordes.saturating_add(1);
        }
    }

    /// §4.1: `CHANGED` va a los SUSCRIPTORES, venga de donde venga el cambio.
    /// Mandarselo a quien no pidio nada llena el cable de trafico que nadie lee.
    fn anunciar(&mut self, r: &mut Respuestas, id: ParamId, v: Valor) {
        if self.suscrito {
            self.empujar(r, Respuesta::Mensaje(Mensaje::Changed(id, v)));
        }
    }

    fn error(&mut self, r: &mut Respuestas, m: &Mensaje, codigo: CodigoError) {
        self.empujar(
            r,
            Respuesta::Mensaje(Mensaje::Error {
                etiqueta: etiqueta_de(m),
                codigo,
            }),
        );
    }
}

fn codigo_de(e: ErrorSet) -> CodigoError {
    match e {
        ErrorSet::NoExiste => CodigoError::NoExiste,
        ErrorSet::SoloLectura => CodigoError::SoloLectura,
        ErrorSet::FueraDeRango => CodigoError::FueraDeRango,
        ErrorSet::ExigeConfirmacion => CodigoError::ExigeConfirmacion,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::descriptor::{Ambito, Descriptor, Tipo, Unidad};
    use crate::retencion::TTL_MS;

    const fn d(id: u32, solo_lectura: bool, medida: bool, confirma: bool) -> Descriptor {
        Descriptor {
            id: ParamId(id),
            nombre: "prueba",
            tipo: Tipo::Continuo,
            ambito: Ambito::Compartido,
            solo_lectura,
            medida,
            confirmacion_fisica: confirma,
            acepta_modulacion: false,
            min: -100,
            max: 100,
            def: 0,
            unidad: Unidad::Ninguna,
            etiquetas: &[],
        }
    }

    static NORMAL: Descriptor = d(0x1000, false, false, false);
    static MEDIDA: Descriptor = d(0x1001, true, true, false);
    static PELIGROSO: Descriptor = d(0x1002, false, false, true);

    /// Dieciseis, que es `MAX_RAMPAS`: el peor caso REAL de una reactivacion
    /// o de un tick, no un numero bonito.
    static MUCHOS: [Descriptor; crate::rampa::MAX_RAMPAS] = {
        let mut a = [d(0x2000, false, false, false); crate::rampa::MAX_RAMPAS];
        let mut k = 0;
        while k < crate::rampa::MAX_RAMPAS {
            a[k] = d(0x2000 + k as u32, false, false, false);
            k += 1;
        }
        a
    };

    fn con_reloj_y_muchos() -> Instrumento {
        let mut i = Instrumento::nuevo();
        tiempo_params::registrar(i.modelo_mut()).unwrap();
        for desc in MUCHOS.iter() {
            i.modelo_mut().registrar(desc).unwrap();
        }
        i.tick(200);
        i
    }

    fn instrumento() -> Instrumento {
        let mut i = Instrumento::nuevo();
        i.modelo_mut().registrar(&NORMAL).unwrap();
        i.modelo_mut().registrar(&MEDIDA).unwrap();
        i.modelo_mut().registrar(&PELIGROSO).unwrap();
        i
    }

    impl Instrumento {
        /// Atajo de los tests que no legislan sobre la puerta: `Usb` es por
        /// donde entra un cliente hoy. Los que SI legislan llaman a `atender`
        /// entera y dicen cual, que es lo que lo hace visible cuando importa.
        fn atender_usb(&mut self, m: Mensaje, ahora_ms: u64) -> Respuestas {
            self.atender(m, ahora_ms, Puerta::Usb)
        }
    }

    fn mensajes(r: &Respuestas) -> Vec<Mensaje, MAX_RESPUESTAS> {
        r.iter()
            .filter_map(|x| match x {
                Respuesta::Mensaje(m) => Some(*m),
                _ => None,
            })
            .collect()
    }

    /// N1 + N2a. La politica legisla sobre `(puerta, etiqueta)`, y negar una
    /// casilla tiene que hacer DOS cosas: contestar un error con nombre, y no
    /// escribir. Un rechazo que igual escribe no es una politica.
    #[test]
    fn una_puerta_sin_permiso_no_escribe_y_lo_dice() {
        let mut i = instrumento();
        let set = Mensaje::Set(NORMAL.id, 7);
        i.cargar_regla(Regla {
            puerta: Puerta::Usb,
            etiqueta: etiqueta_de(&set),
            permitido: false,
        })
        .unwrap();

        let antes = i.modelo().get(NORMAL.id);
        let r = i.atender(set, 0, Puerta::Usb);
        assert_eq!(
            mensajes(&r).as_slice(),
            &[Mensaje::Error {
                etiqueta: etiqueta_de(&set),
                codigo: CodigoError::PuertaSinPermiso,
            }]
        );
        assert_eq!(i.modelo().get(NORMAL.id), antes, "nego y escribio igual");
    }

    /// La misma escritura, por otra puerta, pasa. Es lo que separa una
    /// politica de un interruptor general.
    #[test]
    fn la_regla_de_una_puerta_no_toca_a_las_otras() {
        let mut i = instrumento();
        let set = Mensaje::Set(NORMAL.id, 7);
        i.cargar_regla(Regla {
            puerta: Puerta::Usb,
            etiqueta: etiqueta_de(&set),
            permitido: false,
        })
        .unwrap();
        i.atender(set, 0, Puerta::Mano);
        assert_eq!(i.modelo().get(NORMAL.id), Some(7));
    }

    /// N6, la mitad «DICHO». Sin esto, un CRC malo o una ranura trabada dan
    /// acceso total y silencioso, **indistinguible del estado de fabrica**.
    /// La unica defensa barata es que el estado se pueda LEER.
    #[test]
    fn el_arranque_permisivo_se_puede_distinguir_de_la_fabrica() {
        let mut i = instrumento();
        assert!(i.politica().vacia(), "arranca vacia = todo abierto");
        i.cargar_regla(Regla {
            puerta: Puerta::Usb,
            etiqueta: 0x04,
            permitido: false,
        })
        .unwrap();
        assert!(
            !i.politica().vacia(),
            "con politica cargada tiene que notarse"
        );
    }

    /// N7. `Hello` descartaba la version del cliente con `{ .. }` y contestaba
    /// `Hola` a cualquiera, aunque el docstring de `Hola` (`protocolo.rs`) diga
    /// que sin mirarla "la negociacion es de un solo sentido y no negocia
    /// nada". Y tanto el papel del nucleo como el de la autopista planifican
    /// rupturas de formato apoyandose en este mecanismo.
    ///
    /// Un cliente que habla otra version tiene que enterarse AQUI, con un
    /// codigo que se pueda nombrar -- no tres mensajes despues, en forma de
    /// basura silenciosa que el no sabe leer.
    #[test]
    fn un_cliente_de_otra_version_recibe_un_error_con_nombre() {
        let ajena = VERSION_PROTOCOLO + 1;
        let r = instrumento().atender_usb(Mensaje::Hello { version: ajena }, 0);
        assert_eq!(
            mensajes(&r).as_slice(),
            &[
                // El `Hola` va PRIMERO y va igual: el cliente necesita saber
                // QUE hablamos para decidir que hacer, no solo que no nos
                // entendemos. Decirle "no" sin decirle "esto es lo que hay"
                // lo deja tan a ciegas como el silencio de antes.
                Mensaje::Hola {
                    version: VERSION_PROTOCOLO
                },
                Mensaje::Error {
                    etiqueta: etiqueta_de(&Mensaje::Hello { version: ajena }),
                    codigo: CodigoError::VersionIncompatible,
                },
            ]
        );
    }

    #[test]
    fn hello_se_contesta_con_la_version_acordada() {
        let r = instrumento().atender_usb(Mensaje::Hello { version: 1 }, 0);
        assert_eq!(
            mensajes(&r).as_slice(),
            &[Mensaje::Hola {
                version: VERSION_PROTOCOLO
            }]
        );
    }

    #[test]
    fn describe_pide_el_volcado_del_descriptor() {
        let r = instrumento().atender_usb(Mensaje::Describe, 0);
        assert!(r.iter().any(|x| matches!(x, Respuesta::Descriptores)));
    }

    #[test]
    fn un_get_devuelve_el_valor_y_un_set_lo_mueve() {
        let mut i = instrumento();
        assert_eq!(
            mensajes(&i.atender_usb(Mensaje::Get(NORMAL.id), 0)).as_slice(),
            &[Mensaje::Changed(NORMAL.id, 0)]
        );
        i.atender_usb(Mensaje::Set(NORMAL.id, 42), 0);
        assert_eq!(i.modelo().get(NORMAL.id), Some(42));
    }

    #[test]
    fn changed_solo_sale_hacia_quien_se_suscribio() {
        // §4.1: CHANGED va a los SUSCRIPTORES. Mandarselo a quien no pidio
        // nada llena el cable de trafico que nadie lee.
        let mut i = instrumento();
        assert!(mensajes(&i.atender_usb(Mensaje::Set(NORMAL.id, 1), 0)).is_empty());
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        assert_eq!(
            mensajes(&i.atender_usb(Mensaje::Set(NORMAL.id, 2), 0)).as_slice(),
            &[Mensaje::Changed(NORMAL.id, 2)]
        );
    }

    #[test]
    fn un_set_rechazado_dice_por_que_en_vez_de_callarse() {
        // El hallazgo que motivo la Task 2. Sin esto el agente escribe, no
        // pasa nada, y se queda esperando para siempre.
        let mut i = instrumento();
        for (id, valor, codigo) in [
            (MEDIDA.id, 5, CodigoError::SoloLectura),
            (NORMAL.id, 99_999, CodigoError::FueraDeRango),
            (ParamId(0xBEEF), 1, CodigoError::NoExiste),
        ] {
            let r = mensajes(&i.atender_usb(Mensaje::Set(id, valor), 0));
            assert_eq!(
                r.as_slice(),
                &[Mensaje::Error {
                    etiqueta: 0x04,
                    codigo
                }],
                "{id:?} tenia que quejarse con {codigo:?}"
            );
        }
    }

    #[test]
    fn un_get_de_lo_que_no_existe_tambien_se_queja() {
        let mut i = instrumento();
        let r = mensajes(&i.atender_usb(Mensaje::Get(ParamId(0xBEEF)), 0));
        assert_eq!(
            r.as_slice(),
            &[Mensaje::Error {
                etiqueta: 0x03,
                codigo: CodigoError::NoExiste
            }]
        );
    }

    #[test]
    fn lo_marcado_queda_pendiente_y_solo_el_pulsador_lo_suelta() {
        // §2.2 de punta a punta, por el protocolo.
        let mut i = instrumento();
        let r = mensajes(&i.atender_usb(Mensaje::Set(PELIGROSO.id, 1), 0));
        let token = match r.as_slice() {
            [Mensaje::Error {
                codigo: CodigoError::ExigeConfirmacion,
                ..
            }, Mensaje::Pending { token, id }] => {
                assert_eq!(*id, PELIGROSO.id);
                *token
            }
            otro => panic!("tenia que retener y avisar: {otro:?}"),
        };
        assert_eq!(
            i.modelo().get(PELIGROSO.id),
            Some(0),
            "no puede haberse aplicado"
        );

        let r = mensajes(&i.confirmacion_fisica(1_000));
        assert!(r.contains(&Mensaje::Resolved {
            token,
            confirmado: true
        }));
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(1));
    }

    #[test]
    fn si_nadie_confirma_el_cliente_se_entera_de_que_expiro() {
        let mut i = instrumento();
        i.atender_usb(Mensaje::Set(PELIGROSO.id, 1), 0);
        let r = mensajes(&i.caducar(TTL_MS));
        assert!(matches!(
            r.as_slice(),
            [Mensaje::Resolved {
                confirmado: false,
                ..
            }]
        ));
        assert_eq!(i.modelo().get(PELIGROSO.id), Some(0));
    }

    #[test]
    fn lo_que_todavia_no_sabemos_hacer_se_dice_claro() {
        // Presets, autoafinado, barrido, memo y los LED necesitan perifericos
        // que aun no existen. Callarse seria peor que decir que no.
        let mut i = instrumento();
        for m in [
            Mensaje::PresetList,
            Mensaje::PresetLoad(0),
            Mensaje::PresetSave(0),
            Mensaje::TuneStart,
            Mensaje::PatchScan,
            Mensaje::Telemetry,
            Mensaje::Memo { segundos: 2 },
            Mensaje::Point {
                id: NORMAL.id,
                color: crate::protocolo::Rgb { r: 1, g: 2, b: 3 },
            },
        ] {
            let r = mensajes(&i.atender_usb(m, 0));
            assert!(
                matches!(
                    r.as_slice(),
                    [Mensaje::Error {
                        codigo: CodigoError::NoDisponible,
                        ..
                    }]
                ),
                "{m:?} se quedo callado"
            );
        }
    }

    #[test]
    fn una_medida_publicada_llega_a_los_suscriptores() {
        let mut i = instrumento();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        let r = mensajes(&i.publicar_medida(MEDIDA.id, -100));
        assert_eq!(r.as_slice(), &[Mensaje::Changed(MEDIDA.id, -100)]);
    }

    #[test]
    fn un_mensaje_del_instrumento_que_llega_de_fuera_se_rechaza() {
        // Un cliente no puede fabricar un CHANGED y mentirle a los demas.
        let mut i = instrumento();
        let r = mensajes(&i.atender_usb(Mensaje::Changed(NORMAL.id, 7), 0));
        assert_eq!(
            r.as_slice(),
            &[Mensaje::Error {
                etiqueta: 0x81,
                codigo: CodigoError::Desconocido
            }]
        );
        assert_eq!(i.modelo().get(NORMAL.id), Some(0));
    }

    #[test]
    fn los_dos_unicos_silencios_son_a_proposito() {
        // La regla del modulo, barrida de una. Este test se escribio como
        // «ninguna peticion se queda sin respuesta» y fallo — lo cual estuvo
        // bien, porque obligo a decirla con precision:
        //
        //   1. `SUBSCRIBE` calla porque su efecto ES el silencio.
        //   2. Un `SET` que sale bien y sin suscriptor calla A PROPOSITO. Si
        //      no, girar una perilla dispararia cientos de acks por segundo.
        //      La confirmacion de un SET es el `CHANGED`, y para eso el
        //      cliente se suscribe — que es justo lo que hace el agente.
        //
        // Todo lo demas que llegue del cable produce algo.
        let mut i = instrumento();
        for m in mensajes_de_cliente(&NORMAL.id) {
            let callar_esta_bien = matches!(m, Mensaje::Subscribe { .. })
                || matches!(m, Mensaje::Set(id, v) if i.modelo().descriptor_de(id)
                    .is_some_and(|d| !d.solo_lectura && !d.confirmacion_fisica
                                     && v >= d.min && v <= d.max));
            let r = i.atender_usb(m, 0);
            if callar_esta_bien {
                continue;
            }
            assert!(!r.is_empty(), "{m:?} dejo al cliente en silencio");
        }
    }

    #[test]
    fn el_suscriptor_si_recibe_la_confirmacion_de_su_propio_set() {
        // El otro lado de la regla de arriba: quien quiere saber que su
        // escritura llego, se suscribe. El agente lo hace.
        let mut i = instrumento();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        for m in mensajes_de_cliente(&NORMAL.id) {
            if matches!(m, Mensaje::Subscribe { .. }) {
                continue;
            }
            assert!(
                !i.atender_usb(m, 0).is_empty(),
                "suscrito, {m:?} no puede dejar silencio"
            );
        }
    }

    fn mensajes_de_cliente(id: &ParamId) -> [Mensaje; 12] {
        [
            Mensaje::Hello { version: 1 },
            Mensaje::Describe,
            Mensaje::Get(*id),
            Mensaje::Set(*id, 1),
            Mensaje::Subscribe { activo: true },
            Mensaje::PresetList,
            Mensaje::PresetLoad(0),
            Mensaje::PresetSave(0),
            Mensaje::TuneStart,
            Mensaje::PatchScan,
            Mensaje::Telemetry,
            Mensaje::Memo { segundos: 1 },
        ]
    }

    #[test]
    fn el_instrumento_de_arranque_trae_las_medidas_y_el_reloj() {
        let i = Instrumento::con_medidas();
        assert_eq!(
            i.modelo().len(),
            medidas::MEDIDAS.len() + tiempo_params::TIEMPO.len()
        );
        assert!(i.modelo().get(medidas::ID_PICO_HZ).is_some());
        assert!(i.modelo().get(tiempo_params::ID_CUANTIZACION).is_some());
    }

    // --- El tiempo musical ---

    static OTRO: Descriptor = d(0x1003, false, false, false);
    const PXC: u64 = 384; // 4/4 a 96 PPQN

    fn con_reloj() -> Instrumento {
        let mut i = Instrumento::nuevo();
        tiempo_params::registrar(i.modelo_mut()).unwrap();
        i.modelo_mut().registrar(&NORMAL).unwrap();
        i.modelo_mut().registrar(&MEDIDA).unwrap();
        i.modelo_mut().registrar(&PELIGROSO).unwrap();
        i.modelo_mut().registrar(&OTRO).unwrap();
        i
    }

    /// El reloj a mitad de compas, que es donde llegan las cosas en la vida
    /// real. **En el pulso 0 estas EN un borde**, asi que una rampa pedida ahi
    /// arranca ya — correcto por §5.3, pero no es lo que estos tests miran.
    fn con_reloj_a_mitad() -> Instrumento {
        let mut i = con_reloj();
        i.tick(200);
        i
    }

    fn rampa(id: ParamId, destino: Valor) -> Mensaje {
        Mensaje::Rampa {
            id,
            destino,
            duracion: 384,
            curva: 0,
        }
    }

    #[test]
    fn una_rampa_aceptada_arranca_en_el_borde_de_la_rejilla() {
        let mut i = con_reloj_a_mitad();
        i.atender_usb(rampa(NORMAL.id, 100), 0);
        // Todavia no se movio: espera al borde.
        i.tick(300);
        assert_eq!(i.modelo().get(NORMAL.id), Some(0));
        i.tick(PXC);
        assert_eq!(
            i.modelo().get(NORMAL.id),
            Some(0),
            "arranca EN el borde, en el origen"
        );
        i.tick(PXC + 192);
        assert!(i.modelo().get(NORMAL.id).unwrap() > 0, "y de ahi se mueve");
    }

    #[test]
    fn un_set_del_cliente_anula_la_rampa_y_lo_avisa() {
        // §6.1. Este es el test de la seccion entera.
        let mut i = con_reloj_a_mitad();
        i.atender_usb(rampa(NORMAL.id, 100), 0);
        i.tick(PXC + 96);
        let r = mensajes(&i.atender_usb(Mensaje::Set(NORMAL.id, 7), 0));
        assert!(r.contains(&Mensaje::Anulado {
            id: NORMAL.id,
            anulado: true
        }));
        assert_eq!(i.modelo().get(NORMAL.id), Some(7));
        // Y el tick ya no la pisa.
        i.tick(PXC + 192);
        assert_eq!(
            i.modelo().get(NORMAL.id),
            Some(7),
            "la rampa dejo de escribir"
        );
    }

    #[test]
    fn reactivar_la_devuelve_donde_la_cinta_este_ahora() {
        // §6.2: la cinta siguio corriendo mientras estuvo anulada.
        let mut i = con_reloj_a_mitad();
        i.atender_usb(rampa(NORMAL.id, 100), 0);
        i.tick(PXC + 96);
        i.atender_usb(Mensaje::Set(NORMAL.id, 7), 0);
        let r = mensajes(&i.atender_usb(
            Mensaje::Reactivar {
                id: Some(NORMAL.id),
            },
            0,
        ));
        assert!(r.contains(&Mensaje::Anulado {
            id: NORMAL.id,
            anulado: false
        }));
        i.tick(PXC + 288);
        assert_eq!(
            i.modelo().get(NORMAL.id),
            Some(75),
            "tres cuartos, no la mitad"
        );
    }

    #[test]
    fn reactivar_sin_id_los_devuelve_todos() {
        let mut i = con_reloj_a_mitad();
        for id in [NORMAL.id, OTRO.id] {
            i.atender_usb(rampa(id, 100), 0);
        }
        i.tick(PXC + 96);
        for id in [NORMAL.id, OTRO.id] {
            i.atender_usb(Mensaje::Set(id, 7), 0);
        }
        let r = mensajes(&i.atender_usb(Mensaje::Reactivar { id: None }, 0));
        assert_eq!(
            r.iter()
                .filter(|m| matches!(m, Mensaje::Anulado { anulado: false, .. }))
                .count(),
            2
        );
    }

    /// #182, fallo 1. `Reactivar { id: None }` empuja un `Anulado` por rampa
    /// reactivada -- hasta `MAX_RAMPAS` = 16 -- dentro de un buzon que tenia
    /// cuatro huecos, y TODOS los push eran `let _ =`: descarte SILENCIOSO,
    /// sin error y sin contador.
    ///
    /// La consecuencia no es perder un mensaje: es que el cliente sigue
    /// pintando esos parametros como anulados PARA SIEMPRE, mientras el
    /// instrumento cree que estan vivos.
    ///
    /// Y el test de arriba usaba exactamente DOS rampas y aseveraba 2, asi que
    /// pasaba en verde con el fallo puesto. Este usa el peor caso real.
    #[test]
    fn reactivar_sin_id_no_pierde_ninguno_cuando_pasan_de_cuatro() {
        let mut i = con_reloj_y_muchos();
        for desc in MUCHOS.iter() {
            i.atender_usb(rampa(desc.id, 100), 0);
        }
        i.tick(PXC + 96);
        for desc in MUCHOS.iter() {
            i.atender_usb(Mensaje::Set(desc.id, 7), 0);
        }
        let r = mensajes(&i.atender_usb(Mensaje::Reactivar { id: None }, 0));
        assert_eq!(
            r.iter()
                .filter(|m| matches!(m, Mensaje::Anulado { anulado: false, .. }))
                .count(),
            crate::rampa::MAX_RAMPAS,
            "el buzon se comio reactivaciones en silencio"
        );
    }

    /// #182, fallo 3. El mismo buzon, desbordado por el `tick()`: escribe
    /// hasta `MAX_RAMPAS` valores y anuncia cada uno. Con un suscriptor, los
    /// que no caben se van al vacio.
    ///
    /// Aqui la consecuencia es peor que en el fallo 1: la automatizacion
    /// escribio el modelo y la vista no se entero, o sea DIVERGENCIA
    /// PERMANENTE de la vista optimista -- justo lo que voz-total S0.2 dice
    /// que este mecanismo impide.
    #[test]
    fn el_tick_no_se_come_los_changed_de_las_rampas() {
        let mut i = con_reloj_y_muchos();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        for desc in MUCHOS.iter() {
            i.atender_usb(rampa(desc.id, 100), 0);
        }
        let r = mensajes(&i.tick(PXC + 96));
        // Solo los de las RAMPAS: desde que el fallo 4 esta arreglado, el tick
        // anuncia ademas las medidas del reloj que se movieron.
        assert_eq!(
            r.iter()
                .filter(|m| matches!(
                    m,
                    Mensaje::Changed(id, _) if MUCHOS.iter().any(|d| d.id == *id)
                ))
                .count(),
            crate::rampa::MAX_RAMPAS,
            "la automatizacion escribio y la vista no se entero"
        );
    }

    /// #182, fallo 3 de la junta: `MAX_RESPUESTAS` se habia derivado de UNO
    /// de los tres factores del fan-out. Las aserciones `const` de arriba son
    /// la guardia de verdad -- se disparan antes de que exista un `Vec` que
    /// probar -- y esto es el otro lado: los dos peores casos REALES,
    /// corridos, con un suscriptor mirando, sin perder un solo mensaje.
    ///
    /// Se apoya en el contador del fallo 2: sin `desbordes()` no habia forma
    /// de aseverar esto, porque el descarte era mudo.
    #[test]
    fn el_peor_caso_real_no_desborda_el_buzon() {
        let mut i = con_reloj_y_muchos();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        for desc in MUCHOS.iter() {
            i.atender_usb(rampa(desc.id, 100), 0);
        }
        // `tick()`: MAX_RAMPAS escrituras de rampa + las cinco del reloj.
        i.tick(PXC + 96);
        assert_eq!(i.desbordes(), 0, "el tick se comio mensajes");

        // `Reactivar { id: None }`: un `Anulado` por rampa + el contador.
        for desc in MUCHOS.iter() {
            i.atender_usb(Mensaje::Set(desc.id, 7), 0);
        }
        i.atender_usb(Mensaje::Reactivar { id: None }, 0);
        assert_eq!(
            i.desbordes(),
            0,
            "la reactivacion en bloque se comio mensajes"
        );
    }

    /// #182, fallo 4. `publicar_medidas_del_reloj` tiraba el `Cambio` con
    /// `let _`, asi que las cinco medidas del reloj NUNCA producian `CHANGED`
    /// -- y las cinco tienen `medida: true`, con el nucleo S4.1 prometiendo
    /// que las medidas se siguen con `SUBSCRIBE`. Para esas cinco, no.
    #[test]
    fn las_medidas_del_reloj_se_anuncian_a_quien_se_suscribio() {
        let mut i = con_reloj();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        let r = mensajes(&i.tick(384));
        assert!(
            r.iter().any(|m| matches!(
                m,
                Mensaje::Changed(id, _) if *id == tiempo_params::ID_POSICION
            )),
            "el reloj avanzo y el suscriptor no se entero"
        );
    }

    /// El instrumento NO CORRIA. `fw/src/main.rs` arranca dos tareas y ninguna
    /// llama a `tick()`, asi que en la placa una rampa aceptada nunca escribia
    /// un valor y las medidas del reloj no se publicaban nunca. Lo caza la
    /// junta adversarial del 2026-08-24 (Halberg, punto 1).
    ///
    /// Y no se arregla llamando a `tick(pulso)` desde el firmware, porque el
    /// firmware no sabe en que pulso esta: eso depende del tempo, que vive
    /// dentro del `Reloj`, y `reloj_mut` esta cerrado. La cuenta tiene que
    /// vivir aqui, en core, donde hay tests.
    ///
    /// Media negra a 120 BPM son 96 pulsos internos (PPQN_INTERNO = 96).
    #[test]
    fn el_tiempo_de_pared_mueve_el_reloj() {
        let mut i = con_reloj();
        i.avanzar_a(500_000);
        let p = i.reloj().posicion();
        assert!(
            (p as i64 - 96).abs() <= 2,
            "medio segundo a 120 BPM son 96 pulsos, y avanzo {p}"
        );
    }

    /// Y con el reloj andando, una rampa por fin escribe.
    #[test]
    fn con_el_tiempo_andando_una_rampa_escribe_de_verdad() {
        let mut i = con_reloj();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        i.atender_usb(rampa(NORMAL.id, 100), 0);
        let antes = i.modelo().get(NORMAL.id);
        // Un compas entero: la rampa arranca en el borde y corre 384 pulsos.
        for paso in 1..=8 {
            i.avanzar_a(paso * 500_000);
        }
        let despues = i.modelo().get(NORMAL.id);
        assert_ne!(
            antes, despues,
            "la rampa no escribio nada: el reloj no esta moviendo el instrumento"
        );
    }

    /// El tope de recuperacion existe y esta declarado: si el firmware se
    /// atasca, el reloj NO se pone a generar pulsos sin fin.
    /// DICTAMEN HALBERG, BLOCKER 2. `avanzar_a` se probaba con pasos de
    /// 500_000 us, que a 120 BPM son EXACTAMENTE 96 pulsos: cero resto. El
    /// firmware tica cada 1000 us (`PERIODO_TICK`), o sea 500 veces mas fino,
    /// y ahi la division entera da CERO -- el umbral para un solo pulso son
    /// 5209 us. Como `ultimo_us` se adelantaba igual, el resto se tiraba en
    /// cada llamada y el reloj no avanzaba NUNCA en la placa.
    ///
    /// El commit que introdujo esto se titulaba "El instrumento por fin
    /// corre". No corria. Este test tica como tica el firmware.
    #[test]
    fn el_reloj_avanza_a_la_cadencia_de_verdad_del_firmware() {
        let mut i = instrumento();
        // Un segundo, en pasos de 1 ms, que es lo que hace `PERIODO_TICK`.
        for ms in 1..=1000u64 {
            i.avanzar_a(ms * 1_000);
        }
        // 120 BPM y PPQN 96 -> 192 pulsos por segundo.
        let esperados = 120 * PPQN_INTERNO as u64 / 60;
        assert_eq!(
            i.reloj().posicion(),
            esperados,
            "un segundo de tics de 1 ms tiene que dar {esperados} pulsos"
        );
    }

    /// Y el resto no se puede tirar. En pasos que NO son multiplo del pulso,
    /// la cuenta tiene que cuadrar igual: si se tira, el compas se corre
    /// contra el tiempo de pared para siempre.
    ///
    /// Cuatro segundos y no diez, a proposito: diez segundos son 1920 pulsos
    /// y el tope es 960, asi que el salto de un golpe saldria topado y esto
    /// estaria midiendo el tope en vez del resto. La primera version de este
    /// test cometia justo ese error.
    #[test]
    fn el_resto_no_se_tira_entre_llamadas() {
        let mut i = instrumento();
        // 7 ms no es multiplo de 5208,33 us: cada paso deja resto.
        let mut t = 0u64;
        while t < 4_000_000 {
            t += 7_000;
            i.avanzar_a(t);
        }
        let a_pasitos = i.reloj().posicion();

        let mut j = instrumento();
        j.avanzar_a(t);
        assert_eq!(
            a_pasitos,
            j.reloj().posicion(),
            "el resto se perdio por el camino"
        );
        assert_eq!(i.pulsos_perdidos(), 0, "nada deberia haberse topado aqui");
    }

    /// El tope descarta, y descartar en silencio era el problema. Antes el
    /// docstring decia que el reloj "salta"; no salta, se atrasa, y no habia
    /// forma de saberlo.
    #[test]
    fn lo_que_el_tope_no_emite_se_cuenta() {
        let mut i = instrumento();
        i.avanzar_a(60_000_000); // un minuto de golpe: 11 520 pulsos debidos
        assert_eq!(i.reloj().posicion(), MAX_PULSOS_POR_AVANCE as u64);
        let debidos = 60_000_000u64 * 120_000 * PPQN_INTERNO as u64 / 60_000_000_000;
        assert_eq!(
            i.pulsos_perdidos() as u64,
            debidos - MAX_PULSOS_POR_AVANCE as u64,
            "el instrumento tiene que poder decir cuanto tiempo musical perdio"
        );
    }
    #[test]
    fn un_atasco_largo_no_genera_pulsos_sin_fin() {
        let mut i = con_reloj();
        i.avanzar_a(60_000_000); // un minuto de golpe
        let p = i.reloj().posicion();
        assert!(
            p <= MAX_PULSOS_POR_AVANCE as u64,
            "genero {p} pulsos de un golpe, y el tope declarado es              {MAX_PULSOS_POR_AVANCE}"
        );
    }

    /// La otra mitad del fallo 4, y la razon por la que no basta con anunciar
    /// a lo bruto: `publicar_medida` NO filtra, devuelve `Ok` aunque el valor
    /// sea el mismo. Anunciar sin comparar convertiria cada tick en cinco
    /// `CHANGED` para siempre, o sea cambiar un silencio por una inundacion.
    #[test]
    fn una_medida_del_reloj_que_no_se_movio_no_se_reanuncia() {
        let mut i = con_reloj();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        i.tick(384);
        let r = mensajes(&i.tick(384));
        assert!(
            !r.iter().any(|m| matches!(m, Mensaje::Changed(..))),
            "mismo pulso, nada se movio, y aun asi se anuncio: {r:?}"
        );
    }

    #[test]
    fn una_rampa_a_un_destino_fuera_de_rango_se_rechaza_al_aceptarla() {
        // Mejor ahora que descubrirlo a mitad del barrido.
        let mut i = con_reloj();
        let r = mensajes(&i.atender_usb(rampa(NORMAL.id, 99_999), 0));
        assert_eq!(
            r.as_slice(),
            &[Mensaje::Error {
                etiqueta: 0x0E,
                codigo: CodigoError::FueraDeRango
            }]
        );
    }

    #[test]
    fn no_se_admite_una_rampa_sobre_algo_de_solo_lectura_ni_marcado() {
        let mut i = con_reloj();
        for (id, codigo) in [
            (MEDIDA.id, CodigoError::SoloLectura),
            (PELIGROSO.id, CodigoError::ExigeConfirmacion),
            (ParamId(0xBEEF), CodigoError::NoExiste),
        ] {
            let r = mensajes(&i.atender_usb(rampa(id, 1), 0));
            assert!(
                matches!(r.as_slice(), [Mensaje::Error { codigo: c, .. }] if *c == codigo),
                "{id:?} tenia que dar {codigo:?}, dio {r:?}"
            );
        }
    }

    #[test]
    fn el_tick_solo_avisa_a_los_suscriptores() {
        let mut i = con_reloj_a_mitad();
        i.atender_usb(rampa(NORMAL.id, 100), 0);
        assert!(i.tick(PXC + 96).is_empty());
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        assert!(!i.tick(PXC + 192).is_empty());
    }

    /// #182, fallo 4, la SEXTA medida -- la que quedo viva cuando se
    /// arreglaron las cinco del reloj. `publicar_anulados` tiraba el `Cambio`
    /// con `let _` y nunca llamaba a `anunciar`, aunque `ID_ANULADOS` esta
    /// declarado `medida: true` y el nucleo S4.1 promete que las medidas se
    /// siguen con `SUBSCRIBE`.
    ///
    /// El test que la cubria -- `el_contador_de_anulados_es_una_medida_de_verdad`
    /// -- aseveraba contra `i.modelo().get(..)`, o sea contra el MODELO y no
    /// contra el CABLE, y por eso pasaba en verde con el fallo puesto. Este
    /// mira lo que le llega al suscriptor.
    #[test]
    fn el_contador_de_anulados_se_anuncia_a_quien_se_suscribio() {
        let mut i = con_reloj_a_mitad();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        i.atender_usb(rampa(NORMAL.id, 100), 0);
        i.tick(PXC + 96);

        let r = mensajes(&i.atender_usb(Mensaje::Set(NORMAL.id, 7), 0));
        assert!(
            r.contains(&Mensaje::Changed(tiempo_params::ID_ANULADOS, 1)),
            "el contador subio y el suscriptor no se entero: {r:?}"
        );

        let r = mensajes(&i.atender_usb(Mensaje::Reactivar { id: None }, 0));
        assert!(
            r.contains(&Mensaje::Changed(tiempo_params::ID_ANULADOS, 0)),
            "el contador bajo y el suscriptor no se entero: {r:?}"
        );
    }

    /// La otra mitad, igual que en las cinco del reloj: `publicar_medida` NO
    /// filtra, devuelve `Ok` aunque el valor sea identico. Un `Reactivar` que
    /// no reactiva nada reescribe el mismo cero, y anunciar sin comparar
    /// cambiaria el silencio del fallo por una inundacion.
    #[test]
    fn un_contador_de_anulados_que_no_se_movio_no_se_reanuncia() {
        let mut i = con_reloj_a_mitad();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        let r = mensajes(&i.atender_usb(Mensaje::Reactivar { id: None }, 0));
        assert!(
            !r.iter()
                .any(|m| matches!(m, Mensaje::Changed(id, _) if *id == tiempo_params::ID_ANULADOS)),
            "nadie estaba anulado, nada se movio, y aun asi se anuncio: {r:?}"
        );
    }

    #[test]
    fn el_contador_de_anulados_es_una_medida_de_verdad() {
        let mut i = con_reloj_a_mitad();
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(0));
        i.atender_usb(rampa(NORMAL.id, 100), 0);
        i.tick(PXC + 96);
        i.atender_usb(Mensaje::Set(NORMAL.id, 7), 0);
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(1));
        i.atender_usb(Mensaje::Reactivar { id: None }, 0);
        assert_eq!(i.modelo().get(tiempo_params::ID_ANULADOS), Some(0));
    }

    /// #182, fallo 2 de la junta. El guardia del buzon era un `debug_assert!`
    /// seguido de `let _ = self.push(x)`. `debug_assert!` se compila FUERA en
    /// release, y `fw/Cargo.toml` no declara `debug-assertions`: lo que se
    /// flashea a la placa era, literalmente, el `let _`.
    ///
    /// Este test tiene que pasar en **release**, que es donde el fallo vivia:
    ///
    /// ```text
    /// cargo test --release un_empujon_que_no_cabe
    /// ```
    ///
    /// El papel de la autopista del mismo PR lo prohibe con todas las letras:
    /// «un envio que no cabe es un error con nombre, nunca un `let _`». El
    /// nombre no puede ser un mensaje nuevo -- eso cambia el protocolo y es la
    /// decision N4, sin tomar -- asi que es un contador que la telemetria lee.
    #[test]
    fn un_empujon_que_no_cabe_deja_rastro_en_release() {
        let mut i = instrumento();
        let mut r = Respuestas::new();
        while r.len() < MAX_RESPUESTAS {
            i.empujar(&mut r, Respuesta::Descriptores);
        }
        assert_eq!(i.desbordes(), 0, "todavia cabian todos");

        i.empujar(&mut r, Respuesta::Descriptores);
        assert_eq!(
            i.desbordes(),
            1,
            "el buzon se comio un mensaje y no dejo rastro que la telemetria pueda leer"
        );
        assert_eq!(r.len(), MAX_RESPUESTAS, "y el buzon sigue sin desbordarse");
    }

    /// El contador satura en vez de dar la vuelta: un `0` despues de 65 536
    /// mensajes perdidos seria peor que no contarlos.
    #[test]
    fn el_contador_de_desbordes_satura_en_vez_de_dar_la_vuelta() {
        let mut i = instrumento();
        let mut r = Respuestas::new();
        while r.len() < MAX_RESPUESTAS {
            i.empujar(&mut r, Respuesta::Descriptores);
        }
        for _ in 0..(u16::MAX as u32 + 8) {
            i.empujar(&mut r, Respuesta::Descriptores);
        }
        assert_eq!(i.desbordes(), u16::MAX);
    }

    #[test]
    fn el_tick_publica_donde_esta_el_reloj() {
        let mut i = con_reloj();
        i.tick(PXC * 2 + 50);
        assert_eq!(
            i.modelo().get(tiempo_params::ID_POSICION),
            Some((PXC * 2 + 50) as i32)
        );
        assert_eq!(i.modelo().get(tiempo_params::ID_COMPAS_ACTUAL), Some(2));
        assert_eq!(i.modelo().get(tiempo_params::ID_TIENE_FASE), Some(1));
    }

    #[test]
    fn un_set_sobre_algo_sin_rampa_no_avisa_de_ningun_anulado() {
        // Solo se anula lo que de verdad tenia automatizacion corriendo.
        let mut i = con_reloj();
        i.atender_usb(Mensaje::Subscribe { activo: true }, 0);
        let r = mensajes(&i.atender_usb(Mensaje::Set(NORMAL.id, 5), 0));
        assert!(!r.iter().any(|m| matches!(m, Mensaje::Anulado { .. })));
    }
}
