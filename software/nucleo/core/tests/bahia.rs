//! La ley de conmutacion de la bahia asignable, contra el chip real.
//!
//! Papel: `docs/superpowers/specs/2026-08-23-modulo-voz-total-design.md`,
//! §5.1 (dos AD75019 de carga serie: entradas -> los 16 nodos de suma; las 16
//! salidas post-VCA -> salidas), §5.3 (imagen sombra, barrera de
//! cambiados-en-silencio, politica de drones, sin TTL) y §5.4 (la bahia nace
//! desconectada).
//!
//! Estos tests hablan de **canal (0..15) x linea (0..15)**, nunca de jacks:
//! el censo de que linea es que jack esta mandado en motor-digital §8.4 y
//! **no esta hecho**. Los ejes fisicos X/Y del AD75019 y el orden de los 512
//! bits de la cadena tampoco estan aqui: viven en `bahia_serie.rs` y sus
//! tests, contra la hoja del AD75019.

use sam17_nucleo_core::bahia::{Barrera, Chip, Estado, Imagen, PoliticaDrones, CANALES, LINEAS};

fn imagen_con(chip: Chip, canal: u8, linea: u8) -> Imagen {
    let mut i = Imagen::vacia();
    i.poner(chip, canal, linea);
    i
}

/// La mascara que espera `tick`: un bit en 1 es un canal callado. Se nombra
/// lo que SUENA porque es lo escaso.
fn silencio_menos(sonando: &[u8]) -> u16 {
    let mut m = u16::MAX;
    for c in sonando {
        m &= !(1u16 << c);
    }
    m
}

/// §5.4: «el AD75019 despierta con el registro aleatorio y sin reset a
/// abierto. El driver del latch arranca inhibido por hardware hasta que el
/// micro shiftea ceros: la bahia nace desconectada». La imagen de arranque es
/// la vacia, y la barrera arranca con ella: si `nueva()` naciera con algun
/// cruce, el modelo estaria afirmando una conexion que el hardware tiene
/// prohibido tener al encender.
#[test]
fn la_bahia_nace_desconectada() {
    let vacia = Imagen::vacia();
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            for linea in 0..LINEAS {
                assert!(!vacia.esta(chip, canal, linea), "{chip:?} {canal} {linea}");
            }
        }
    }

    let b = Barrera::nueva(PoliticaDrones::Diferir);
    assert_eq!(*b.activa(), vacia);
    assert_eq!(b.estado(), Estado::Activa);
}

/// Poner, quitar, y que poner dos veces sea lo mismo que ponerlo una. La
/// idempotencia no es cosmetica: el cerebro recarga la imagen entera en cada
/// conmutacion (§5.3), asi que el mismo cruce se escribe muchas veces y no
/// puede acumular estado.
#[test]
fn poner_y_quitar_un_cruce_y_ponerlo_dos_veces_es_ponerlo_una() {
    let mut i = Imagen::vacia();
    i.poner(Chip::Entrada, 3, 9);
    assert!(i.esta(Chip::Entrada, 3, 9));
    // el mismo par de indices en el otro chip es OTRO cruce: uno lleva la
    // linea al nodo de suma del canal, el otro la salida post-VCA a la linea.
    assert!(!i.esta(Chip::Salida, 3, 9));

    let una_vez = i;
    i.poner(Chip::Entrada, 3, 9);
    assert_eq!(i, una_vez, "poner dos veces no dio lo mismo que poner una");

    i.quitar(Chip::Entrada, 3, 9);
    assert_eq!(i, Imagen::vacia());
    i.quitar(Chip::Entrada, 3, 9);
    assert_eq!(i, Imagen::vacia(), "quitar lo que no esta movio la imagen");
}

/// Un nodo de suma existe justamente para sumar: un canal recibe varias
/// lineas a la vez, y las 8 entradas de §5.1 no servirian de nada si un cruce
/// pisara al anterior. Se barren los dos chips y los 16 canales, y dentro de
/// cada fila se comprueban las 16 lineas.
///
/// **Este test entro por una mutacion**, no por la lista: con los once
/// primeros en verde, hacer que `poner` pisara la fila (`=` en vez de `|=`) y
/// que la linea se ignorara (bit fijo) seguia dando verde. Los dos cambios
/// borran cruces de verdad y ninguno se veia.
#[test]
fn dos_lineas_del_mismo_canal_son_dos_cruces_distintos() {
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            let mut i = Imagen::vacia();
            i.poner(chip, canal, 5);
            i.poner(chip, canal, 9);
            for linea in 0..LINEAS {
                assert_eq!(
                    i.esta(chip, canal, linea),
                    linea == 5 || linea == 9,
                    "{chip:?} canal {canal} linea {linea}"
                );
            }

            i.quitar(chip, canal, 5);
            assert!(!i.esta(chip, canal, 5), "{chip:?} canal {canal}");
            assert!(
                i.esta(chip, canal, 9),
                "{chip:?} canal {canal}: quitar una linea se llevo a la otra"
            );
        }
    }
}

/// §5.3: «el commit espera a que **todos los canales cuyos cruces cambian**
/// esten en silencio». Quien decide quien vota es esta mascara, asi que se
/// barre entera: 2 chips x 16 canales x 16 lineas = 512 cruces, uno a uno.
/// Dos casos elegidos a mano dejan pasar un desplazamiento equivocado que
/// acierta justo en los dos elegidos.
#[test]
fn cada_cruce_suelto_marca_exactamente_su_canal() {
    let vacia = Imagen::vacia();
    let mut n = 0;
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            for linea in 0..LINEAS {
                let i = imagen_con(chip, canal, linea);
                assert_eq!(
                    i.canales_que_cambian(&vacia),
                    1u16 << canal,
                    "{chip:?} canal {canal} linea {linea}"
                );
                assert_eq!(
                    vacia.canales_que_cambian(&i),
                    1u16 << canal,
                    "la mascara cambio al dar vuelta los argumentos"
                );
                n += 1;
            }
        }
    }
    assert_eq!(n, 512, "el barrido no cubrio los dos chips enteros");
}

/// Un canal puede cambiar por el chip de entrada, por el de salida o por los
/// dos: es el mismo canal del instrumento y vota una sola vez.
#[test]
fn los_cambios_de_los_dos_chips_se_suman_en_la_misma_mascara() {
    let base = Imagen::vacia();
    let mut otra = base;
    otra.poner(Chip::Entrada, 2, 5);
    otra.poner(Chip::Salida, 7, 1);
    otra.poner(Chip::Entrada, 7, 13);
    assert_eq!(base.canales_que_cambian(&otra), (1 << 2) | (1 << 7));
}

/// Dos imagenes iguales no hacen cambiar a nadie: recargar la misma imagen no
/// puede pedirle silencio a ningun canal.
#[test]
fn dos_imagenes_iguales_no_hacen_cambiar_a_nadie() {
    let mut i = Imagen::vacia();
    i.poner(Chip::Entrada, 0, 0);
    i.poner(Chip::Salida, 15, 15);
    assert_eq!(i.canales_que_cambian(&i), 0);
    assert_eq!(Imagen::vacia().canales_que_cambian(&Imagen::vacia()), 0);
}

/// §5.3, `diferir`: «espera al silencio; la interfaz y el LED del jack
/// muestran pendiente». H-OF3: un drone bajo `diferir` nunca se corta solo —
/// la starvation deja de ser un bug y pasa a ser una eleccion del interprete.
/// Mil ticks son la prueba de que la espera no tiene fondo: sin TTL (H-RC1).
#[test]
fn diferir_espera_para_siempre_al_canal_que_cambia_y_suena() {
    let mut b = Barrera::nueva(PoliticaDrones::Diferir);
    let propuesta = imagen_con(Chip::Entrada, 4, 11);
    b.proponer(propuesta, 1_000);
    assert_eq!(b.estado(), Estado::Pendiente { desde_ms: 1_000 });

    for t in 0..1_000u64 {
        assert!(
            b.tick(silencio_menos(&[4]), 1_000 + t).is_none(),
            "commit con el canal 4 sonando, en el tick {t}"
        );
    }
    assert_eq!(b.estado(), Estado::Pendiente { desde_ms: 1_000 });
    assert_eq!(*b.activa(), Imagen::vacia(), "conmuto sin silencio");

    let c = b
        .tick(silencio_menos(&[]), 9_999)
        .expect("el canal 4 callo");
    assert_eq!(c.mutear, 0, "`diferir` no mutea a nadie, nunca");
    assert_eq!(*b.activa(), propuesta);
    assert_eq!(b.estado(), Estado::Activa);
}

/// §5.3: «Los que no cambian no votan». Un drone en otro canal no puede
/// retrasar una conmutacion que no lo toca — si votara, la bahia quedaria
/// trabada mientras suene cualquier cosa.
#[test]
fn un_canal_que_suena_y_no_cambia_no_retrasa_el_commit() {
    let mut b = Barrera::nueva(PoliticaDrones::Diferir);
    let propuesta = imagen_con(Chip::Salida, 6, 2);
    b.proponer(propuesta, 0);

    // el 6 es el unico que cambia, y esta callado; el 0, el 9 y el 15 suenan.
    let c = b
        .tick(silencio_menos(&[0, 9, 15]), 5)
        .expect("nadie que vote");
    assert_eq!(c.mutear, 0);
    assert_eq!(*b.activa(), propuesta);
    assert_eq!(b.estado(), Estado::Activa);
}

/// §5.3, `forzar`: «timeout declarado y mute breve del canal». El timeout lo
/// declara el preset — `core` no trae uno por defecto —, asi que se barre en
/// vez de fijar uno: un solo valor deja pasar un `>` puesto donde va `>=`, y
/// tambien una constante escondida que ignore lo que dice el preset.
///
/// El `mutear` que sale son **exactamente** los canales que cambian y siguen
/// sonando: ni el que suena sin cambiar, ni el que cambia estando callado.
#[test]
fn forzar_espera_su_timeout_y_al_vencer_mutea_solo_a_los_que_siguen_sonando() {
    for timeout_ms in [0u64, 1, 2, 50, 1_000, 30_000] {
        let mut b = Barrera::nueva(PoliticaDrones::Forzar { timeout_ms });
        let mut propuesta = Imagen::vacia();
        propuesta.poner(Chip::Entrada, 3, 0);
        propuesta.poner(Chip::Salida, 12, 7);
        propuesta.poner(Chip::Entrada, 5, 4);
        let t0 = 700u64;
        b.proponer(propuesta, t0);

        // cambian el 3, el 5 y el 12. Suenan el 3, el 8 y el 12: el 5 cambia
        // callado y el 8 suena sin cambiar.
        let sonando = silencio_menos(&[3, 8, 12]);
        for t in t0..t0 + timeout_ms {
            assert!(
                b.tick(sonando, t).is_none(),
                "commit antes de tiempo en {t}, con timeout {timeout_ms}"
            );
            assert_eq!(b.estado(), Estado::Pendiente { desde_ms: t0 });
        }

        let c = b
            .tick(sonando, t0 + timeout_ms)
            .expect("no vencio el timeout de `forzar`");
        assert_eq!(
            c.mutear,
            (1 << 3) | (1 << 12),
            "timeout {timeout_ms}: el mute no son los que cambian y suenan"
        );
        assert_eq!(*b.activa(), propuesta);
        assert_eq!(b.estado(), Estado::Activa);
    }
}

/// `forzar` no es «conmutar al vencer»: es «conmutar al silencio, y al vencer
/// aunque no lo haya». Con todos callados pasa en el acto y no mutea a nadie.
#[test]
fn forzar_conmuta_en_silencio_sin_esperar_al_timeout() {
    let mut b = Barrera::nueva(PoliticaDrones::Forzar { timeout_ms: 10_000 });
    let propuesta = imagen_con(Chip::Entrada, 1, 1);
    b.proponer(propuesta, 0);

    let c = b.tick(u16::MAX, 1).expect("estaba todo callado");
    assert_eq!(c.mutear, 0, "muteo a quien ya estaba callado");
    assert_eq!(*b.activa(), propuesta);
}

/// La ultima propuesta manda: sustituye a la pendiente y su reloj arranca de
/// nuevo. Si el reloj no reiniciara, una rafaga de propuestas heredaria el
/// vencimiento de la primera y forzaria un mute que nadie pidio.
#[test]
fn una_propuesta_nueva_sustituye_a_la_pendiente_y_reinicia_el_reloj() {
    let mut b = Barrera::nueva(PoliticaDrones::Forzar { timeout_ms: 100 });
    let primera = imagen_con(Chip::Entrada, 2, 2);
    let segunda = imagen_con(Chip::Salida, 10, 3);
    let sonando = silencio_menos(&[2, 10]);

    b.proponer(primera, 0);
    assert!(b.tick(sonando, 99).is_none());

    b.proponer(segunda, 50);
    assert_eq!(b.estado(), Estado::Pendiente { desde_ms: 50 });
    assert!(
        b.tick(sonando, 149).is_none(),
        "vencio con el reloj de la primera: no reinicio"
    );

    let c = b
        .tick(sonando, 150)
        .expect("no vencio el reloj de la segunda");
    assert_eq!(*b.activa(), segunda, "gano la propuesta vieja");
    assert_eq!(
        c.mutear,
        1 << 10,
        "el canal 2 ya no cambia: la primera propuesta murio al ser sustituida"
    );
}

/// Sin pendiente no hay nada que conmutar, ni siquiera con un timeout de cero
/// y todo el instrumento sonando. Un `tick` no puede fabricar una conmutacion.
#[test]
fn un_tick_sin_pendiente_no_hace_nada() {
    let mut b = Barrera::nueva(PoliticaDrones::Forzar { timeout_ms: 0 });
    assert_eq!(b.estado(), Estado::Activa);

    for t in 0..10u64 {
        assert!(b.tick(0, t).is_none(), "commit sin propuesta en {t}");
    }
    assert_eq!(*b.activa(), Imagen::vacia());
    assert_eq!(b.estado(), Estado::Activa);
}
