//! El dialecto de la Voz v1, contra el papel de la cabecera: los mensajes de
//! bajada, la sesion y los registros de subida.
//!
//! Papel: `docs/superpowers/specs/2026-09-02-cabecera-j2-design.md`, D4 (los
//! cinco mensajes y la tabla de indices), D5 (la sesion), D6 (la subida), D8
//! (las causas de rechazo), §3.2 y §3.3 (los bytes) y §4 (los largos contra
//! R-E1). Los numeros de los tests son los de su §8.
//!
//! Los bytes esperados y los rangos se escriben a mano desde el papel: un test
//! que lea la tabla que prueba no prueba nada.

use sam17_nucleo_core::bahia::{Chip, Imagen, CANALES, LINEAS};
use sam17_nucleo_core::descubrimiento::{crc16, TABLA_CRC16};
use sam17_nucleo_core::dialecto_voz::{
    decodificar, decodificar_registro, Cuentas, Escritura, Mensaje, Receptor, Registro, DIALECTO,
    MAX_ESCRITURAS, VENTANA_SUBIDA,
};
use sam17_nucleo_core::envolvente::{Borde, Entrada, Generadores, Parametros, Tiempos};
use sam17_nucleo_core::fuerza::Fuerza;
use sam17_nucleo_core::j2::{self, carga_max, Cabecera, ErrorTrama, SOBRE};

fn trama(m: &Mensaje, secuencia: u16) -> Vec<u8> {
    let mut out = [0u8; 256];
    let n = m
        .codificar(&TABLA_CRC16, secuencia, &mut out)
        .expect("se codifica");
    out[..n].to_vec()
}

/// Una trama con el sobre bueno y la carga que se quiera, para probar la forma.
fn cruda(tipo: u8, carga: &[u8]) -> Vec<u8> {
    let mut out = vec![0u8; SOBRE + carga.len()];
    j2::codificar(&TABLA_CRC16, tipo, 1, carga, &mut out).expect("cabe");
    out
}

fn set(tuplas: &[(u8, u8, i32)]) -> Mensaje {
    let mut escrituras = [Escritura::default(); MAX_ESCRITURAS];
    for (e, &(instancia, indice, valor)) in escrituras.iter_mut().zip(tuplas) {
        *e = Escritura {
            instancia,
            indice,
            valor,
        };
    }
    Mensaje::Set {
        n: tuplas.len() as u8,
        escrituras,
    }
}

/// La tabla de indices de D4, copiada a mano: (minimo, maximo) por indice.
const RANGOS_D4: [(i32, i32); 11] = [
    (1, 10_000),
    (1, 10_000),
    (1, 20_000),
    (0, 1_000),
    (1, 10_000),
    (1, 10_000),
    (1, 20_000),
    (0, 1_000),
    (0, 1_000),
    (-4_800, 4_800),
    (0, 1_000),
];

fn set_lleno() -> Mensaje {
    let tuplas: Vec<_> = (0..16u8)
        .map(|i| (15 - i, i % 11, RANGOS_D4[usize::from(i % 11)].1))
        .collect();
    set(&tuplas)
}

fn bahia_llena() -> Imagen {
    let mut im = Imagen::vacia();
    for chip in Chip::TODOS {
        for canal in 0..CANALES {
            for linea in 0..LINEAS {
                im.poner(chip, canal, linea);
            }
        }
    }
    im
}

/// Los mensajes de borde de §8.1: todo cero, todo `0xFF`, mascaras con un bit,
/// `SET` de 1 y de 16.
fn casos() -> Vec<Mensaje> {
    let mut un_cruce = Imagen::vacia();
    un_cruce.poner(Chip::Salida, 15, 0);
    let mut un_tono = [0u16; 16];
    un_tono[15] = 0x8001;
    vec![
        Mensaje::Nada,
        Mensaje::Hola {
            version: 1,
            dialecto: 1,
        },
        // La forma de `HOLA` no juzga la version: eso es de la sesion (D5).
        Mensaje::Hola {
            version: 2,
            dialecto: 0,
        },
        Mensaje::Evento {
            destino: 0,
            borde: Borde::Abre,
            fuerza: 0,
            tono: 0,
        },
        Mensaje::Evento {
            destino: 0xFFFF,
            borde: Borde::Dispara,
            fuerza: 0xFFFF,
            tono: 0xFFFF,
        },
        Mensaje::Tono {
            mascara: 0,
            tonos: [0; 16],
        },
        Mensaje::Tono {
            mascara: 1 << 15,
            tonos: un_tono,
        },
        Mensaje::Tono {
            mascara: 0xFFFF,
            tonos: [0xFFFF; 16],
        },
        Mensaje::Compuerta {
            mascara: 0,
            contador: 0,
        },
        Mensaje::Compuerta {
            mascara: 0xFFFF,
            contador: 0xFFFF,
        },
        Mensaje::Bahia(Imagen::vacia()),
        Mensaje::Bahia(un_cruce),
        Mensaje::Bahia(bahia_llena()),
        set(&[(0, 0, 1)]),
        set_lleno(),
        // Campos distintos entre si, para que uno cruzado con otro no vuelva
        // igual.
        Mensaje::Evento {
            destino: 0x1234,
            borde: Borde::Cierra,
            fuerza: 0x5678,
            tono: 0x9ABC,
        },
        Mensaje::Compuerta {
            mascara: 0x1234,
            contador: 0xABCD,
        },
    ]
}

/// §8.1 y §8.4: cada mensaje vuelve igual, con las dos secuencias extremas y
/// con relleno y byte de cola detras (R-C1).
#[test]
fn ida_y_vuelta_de_cada_mensaje() {
    for m in casos() {
        for secuencia in [0, 0xFFFF] {
            let mut t = trama(&m, secuencia);
            let largo = (t.len() - SOBRE) as u8;
            t.extend_from_slice(&[0; 33]);
            assert_eq!(
                decodificar(&TABLA_CRC16, &t),
                Ok((
                    Cabecera {
                        tipo: t[0],
                        largo,
                        secuencia
                    },
                    m
                )),
                "{m:?}"
            );
        }
    }
}

/// §3.1: el byte `tipo` de cada mensaje de bajada.
#[test]
fn los_tipos_de_bajada() {
    let tipos = [
        (Mensaje::Nada, 0x00),
        (
            Mensaje::Hola {
                version: 1,
                dialecto: 1,
            },
            0x01,
        ),
        (casos()[3], 0x10),
        (casos()[5], 0x11),
        (casos()[8], 0x12),
        (casos()[10], 0x13),
        (casos()[13], 0x14),
    ];
    for (m, tipo) in tipos {
        assert_eq!(trama(&m, 0)[0], tipo, "{m:?}");
    }
}

/// §8.2: un `EVENTO` conocido son exactamente estos 13 bytes, con el CRC de
/// `crc16` sobre los once primeros.
#[test]
fn el_evento_byte_a_byte() {
    let m = Mensaje::Evento {
        destino: 0x1234,
        borde: Borde::Cierra,
        fuerza: 0x5678,
        tono: 0x9ABC,
    };
    let cuerpo = [
        0x10, 7, 0x02, 0x01, 0x34, 0x12, 0x01, 0x78, 0x56, 0xBC, 0x9A,
    ];
    let crc = crc16(&cuerpo);
    let mut esperado = cuerpo.to_vec();
    esperado.extend_from_slice(&crc.to_le_bytes());
    assert_eq!(trama(&m, 0x0102), esperado);
}

/// §3.2: las cargas de `HOLA`, `COMPUERTA` y `SET`, byte a byte.
#[test]
fn las_cargas_byte_a_byte() {
    let carga = |m: &Mensaje| {
        let t = trama(m, 0);
        t[4..t.len() - 2].to_vec()
    };
    assert_eq!(carga(&Mensaje::Nada), [0u8; 0]);
    assert_eq!(
        carga(&Mensaje::Hola {
            version: 1,
            dialecto: 1
        }),
        [1, 1]
    );
    assert_eq!(
        carga(&Mensaje::Compuerta {
            mascara: 0x1234,
            contador: 0xABCD
        }),
        [0x34, 0x12, 0xCD, 0xAB]
    );
    // -4 800 = 0xFFFF_ED40, en LE.
    assert_eq!(
        carga(&set(&[(3, 9, -4_800), (15, 2, 20_000)])),
        [3, 9, 0x40, 0xED, 0xFF, 0xFF, 15, 2, 0x20, 0x4E, 0x00, 0x00]
    );
}

/// §8.9: la mascara dice que tonos vienen, en orden de instancia.
#[test]
fn el_tono_con_mascara() {
    let mut tonos = [0u16; 16];
    tonos[0] = 0x1111;
    tonos[2] = 0x2222;
    tonos[15] = 0xF0F0;
    let t = trama(
        &Mensaje::Tono {
            mascara: 0b1000_0000_0000_0101,
            tonos,
        },
        0,
    );
    assert_eq!(t[1], 8);
    assert_eq!(&t[4..12], [0x05, 0x80, 0x11, 0x11, 0x22, 0x22, 0xF0, 0xF0]);
    // Dieciseis moviendose son 2 + 32 = 34 bytes (D4).
    assert_eq!(trama(&casos()[7], 0)[1], 34);
    // Una mascara con n bits y largo distinto de 2 + 2n es forma mala.
    for carga in [
        &[0x05, 0x80, 0, 0, 0, 0][..],
        &[0x05, 0x80, 0, 0, 0, 0, 0, 0, 0, 0],
    ] {
        assert_eq!(
            decodificar(&TABLA_CRC16, &cruda(0x11, carga)),
            Err(ErrorTrama::Forma)
        );
    }
}

/// §8.10: `BAHIA` es `Imagen.filas`, chip de entrada primero.
#[test]
fn la_bahia_es_la_imagen() {
    let mut im = Imagen::vacia();
    im.poner(Chip::Entrada, 3, 9);
    let mut esperado = [0u8; 64];
    esperado[2 * 3 + 1] = 0x02; // bit 9 del u16 numero 3, LE
    assert_eq!(&trama(&Mensaje::Bahia(im), 0)[4..68], esperado);

    let mut im = Imagen::vacia();
    im.poner(Chip::Salida, 0, 0);
    let mut esperado = [0u8; 64];
    esperado[32] = 0x01;
    assert_eq!(&trama(&Mensaje::Bahia(im), 0)[4..68], esperado);

    // La imagen de arranque de voz-total §5.4 son 64 ceros.
    assert_eq!(&trama(&Mensaje::Bahia(Imagen::vacia()), 0)[4..68], [0; 64]);
}

/// §8.5: la forma mala se rechaza como `Forma`, nunca como `Crc`.
#[test]
fn la_forma_mala_se_rechaza() {
    let tupla = |instancia: u8, indice: u8, valor: i32| {
        let mut b = vec![instancia, indice];
        b.extend_from_slice(&valor.to_le_bytes());
        b
    };
    let malas: Vec<(u8, Vec<u8>)> = vec![
        // Una tupla buena y un byte de mas.
        (0x14, [tupla(0, 3, 0), vec![0]].concat()),
        (0x14, vec![]),
        (0x14, tupla(0, 3, 0).repeat(17)),
        (0x14, tupla(0, 11, 0)),
        (0x14, tupla(0, 255, 0)),
        (0x14, tupla(0, 0, 0)),
        (0x14, tupla(0, 0, 10_001)),
        (0x14, tupla(0, 10, 1_001)),
        (0x14, tupla(16, 3, 0)),
        // Una tupla buena no salva a la mala que la sigue: se rechaza entera.
        (0x14, [tupla(0, 3, 0), tupla(0, 2, 20_001)].concat()),
        (0x10, vec![0, 0, 3, 0, 0, 0, 0]),
        (0x10, vec![0; 6]),
        (0x10, vec![0; 8]),
        (0x13, vec![0; 63]),
        (0x13, vec![0; 65]),
        (0x01, vec![1, 1, 0]),
        (0x01, vec![1]),
        (0x00, vec![0]),
        (0x12, vec![0; 3]),
        (0x12, vec![0; 5]),
        (0x11, vec![]),
        (0x11, vec![0]),
    ];
    for (tipo, carga) in malas {
        assert_eq!(
            decodificar(&TABLA_CRC16, &cruda(tipo, &carga)),
            Err(ErrorTrama::Forma),
            "tipo {tipo:#04x}, carga {carga:?}"
        );
    }
}

/// §8.5: los once indices pasan con su minimo y su maximo, y caen un paso
/// fuera.
#[test]
fn los_once_indices_en_sus_bordes() {
    for (indice, &(min, max)) in RANGOS_D4.iter().enumerate() {
        let indice = indice as u8;
        for valor in [min, max] {
            assert!(
                decodificar(&TABLA_CRC16, &trama(&set(&[(0, indice, valor)]), 0)).is_ok(),
                "indice {indice}, valor {valor}"
            );
        }
        for valor in [min - 1, max + 1] {
            let mut carga = vec![0, indice];
            carga.extend_from_slice(&valor.to_le_bytes());
            assert_eq!(
                decodificar(&TABLA_CRC16, &cruda(0x14, &carga)),
                Err(ErrorTrama::Forma),
                "indice {indice}, valor {valor}"
            );
        }
    }
}

/// §8.6: un tipo que no es de la Voz ni universal de bajada se rechaza como
/// `Tipo`. Los de subida tampoco bajan.
#[test]
fn el_tipo_desconocido_se_rechaza() {
    for tipo in [0x02, 0x0F, 0x15, 0x16, 0x7F, 0x80, 0x81, 0x90, 0xFF] {
        assert_eq!(
            decodificar(&TABLA_CRC16, &cruda(tipo, &[])),
            Err(ErrorTrama::Tipo),
            "tipo {tipo:#04x}"
        );
    }
}

/// `codificar` no escribe lo que el receptor rechazaria, y no toca `out`.
#[test]
fn codificar_no_escribe_lo_que_se_rechaza() {
    let mut n_17 = set_lleno();
    if let Mensaje::Set { n, .. } = &mut n_17 {
        *n = 17;
    }
    for m in [
        set(&[]),
        n_17,
        set(&[(0, 0, 0)]),
        set(&[(16, 3, 0)]),
        set(&[(0, 11, 0)]),
    ] {
        let mut out = [0xEE; 256];
        assert_eq!(m.codificar(&TABLA_CRC16, 1, &mut out), None, "{m:?}");
        assert_eq!(out, [0xEE; 256]);
    }
    let mut corto = [0xEE; 12];
    assert_eq!(casos()[3].codificar(&TABLA_CRC16, 1, &mut corto), None);
    assert_eq!(corto, [0xEE; 12]);
}

/// El mensaje mas largo que admite cada tipo (§4).
fn mas_largos() -> [Mensaje; 7] {
    [
        Mensaje::Nada,
        casos()[1],
        casos()[4],
        casos()[7],
        casos()[9],
        Mensaje::Bahia(bahia_llena()),
        set_lleno(),
    ]
}

/// §8.7: el techo de carga que R-E1 deja, `reloj x 100 us / 8 - 7` (el sobre y
/// el byte de cola), con el `largo` de un byte recortando a 255.
#[test]
fn la_carga_max_por_reloj() {
    assert_eq!(carga_max(10_000_000), 10_000_000 / 10_000 / 8 - 7);
    assert_eq!(carga_max(10_000_000), 118);
    assert_eq!(carga_max(34_500_000), 255); // 431 - 7 = 424, recortado
    assert_eq!(carga_max(21_040_000), 255); // 263 - 7 = 256: el primero que se recorta
    assert_eq!(carga_max(8_000_000), 93);
    assert_eq!(carga_max(6_250_000), 71); // 78,125 bytes: el ultimo no cabe
    assert_eq!(carga_max(0), 0);
}

/// §8.7: al piso legado de 10 MHz cabe el mas largo de cada tipo.
#[test]
fn todo_mensaje_cabe_en_r_e1_al_piso() {
    for m in mas_largos() {
        assert!(trama(&m, 0).len() - SOBRE <= carga_max(10_000_000), "{m:?}");
    }
    assert_eq!(trama(&set_lleno(), 0).len() - SOBRE, 96);
}

/// R-E1 al reloj que el enlace tiene hoy: el kernel de los SPI sale de `pclk`
/// a 100 MHz con el arbol del hub y el `MBR` cae en /16, 6,25 MHz
/// (`fw/src/usb.rs`, `configuracion_hub`). Ahi el `SET` de dieciseis son
/// 824 bits, 131,8 us, y no cabe: el techo es de 71 bytes de carga, once
/// tuplas.
#[test]
#[ignore = "#380: a 6,25 MHz el SET de dieciseis (96 bytes) pasa del techo de 71"]
fn todo_mensaje_cabe_en_r_e1_al_reloj_de_hoy() {
    for m in mas_largos() {
        assert!(trama(&m, 0).len() - SOBRE <= carga_max(6_250_000), "{m:?}");
    }
}

/// §8.11: la traduccion al generador. El `EVENTO` entra entero con la
/// secuencia de su sobre y la instancia de los cuatro bits bajos del destino;
/// `COMPUERTA` lleva su contador; un `SET` de tres tuplas da tres
/// `Entrada::Parametro` en orden, y aplicadas, cada una deja su campo.
#[test]
fn la_traduccion_al_generador() {
    let evento = Mensaje::Evento {
        destino: 0x7A35,
        borde: Borde::Cierra,
        fuerza: 0x1234,
        tono: 0x4000,
    };
    assert_eq!(
        evento.entradas(77).collect::<Vec<_>>(),
        [Entrada::Evento {
            canal: 5,
            borde: Borde::Cierra,
            fuerza: Fuerza(0x1234),
            secuencia: 77,
        }]
    );
    let compuerta = Mensaje::Compuerta {
        mascara: 0x00F0,
        contador: 76,
    };
    assert_eq!(
        compuerta.entradas(78).collect::<Vec<_>>(),
        [Entrada::Compuerta {
            mascara: 0x00F0,
            contador: 76,
        }]
    );
    let entradas: Vec<_> = set(&[(2, 0, 5), (2, 9, -1_200), (15, 10, 1_000)])
        .entradas(79)
        .collect();
    assert_eq!(
        entradas,
        [
            Entrada::Parametro {
                canal: 2,
                indice: 0,
                valor: 5,
            },
            Entrada::Parametro {
                canal: 2,
                indice: 9,
                valor: -1_200,
            },
            Entrada::Parametro {
                canal: 15,
                indice: 10,
                valor: 1_000,
            },
        ]
    );
    let base = Parametros {
        vca: Tiempos {
            ataque_ms: 10,
            decaimiento_ms: 20,
            relajacion_ms: 30,
        },
        vca_sostenido: 700,
        filtro: Tiempos {
            ataque_ms: 5,
            decaimiento_ms: 30,
            relajacion_ms: 30,
        },
        filtro_sostenido: 300,
        sensibilidad_fuerza: 500,
        filtro_cantidad: 0,
        paneo: 500,
    };
    let mut g = Generadores::nuevos(base);
    g.tick(&entradas);
    let dos = g.parametros(2).unwrap();
    assert_eq!((dos.vca.ataque_ms, dos.filtro_cantidad), (5, -1_200));
    assert_eq!(g.parametros(15).unwrap().paneo, 1_000);
    // TONO y BAHIA esperan a sus duenos, que no son el generador; NADA no lleva
    // nada para el. HOLA lleva la sesion: su test es el 14.
    for m in [Mensaje::Nada, casos()[7], Mensaje::Bahia(bahia_llena())] {
        assert_eq!(m.entradas(1).count(), 0, "{m:?}");
    }
}

fn hola(version: u8, dialecto: u8) -> Vec<u8> {
    trama(&Mensaje::Hola { version, dialecto }, 0)
}

/// §8.14, D5 y R-C7: sin `HOLA` no hay dialecto. Todo lo demas da `SinSesion` y
/// cuenta en `rechazadas_tipo` (§3.3). Un `HOLA` con version 2 o con un
/// dialecto que el modulo no habla tampoco abre sesion, y cuenta en
/// `rechazadas_tipo`, no en forma (decidido el 2026-10-20).
#[test]
fn sin_hola_no_hay_dialecto() {
    assert_eq!(DIALECTO, 1, "D5: 0 legado, 1 Voz v1");
    let mut r = Receptor::default();
    let otros: Vec<_> = casos()
        .into_iter()
        .filter(|m| !matches!(m, Mensaje::Hola { .. }))
        .collect();
    for (s, m) in (1..).zip(&otros) {
        assert_eq!(
            r.recibir(&TABLA_CRC16, &trama(m, s)),
            Err(ErrorTrama::SinSesion),
            "{m:?}"
        );
    }
    assert_eq!(
        r.recibir(&TABLA_CRC16, &cruda(0x02, &[])),
        Err(ErrorTrama::SinSesion),
        "un tipo desconocido tampoco pasa sin sesion"
    );
    for (version, dialecto) in [(2, 1), (0, 1), (1, 0), (1, 2)] {
        assert_eq!(
            r.recibir(&TABLA_CRC16, &hola(version, dialecto)),
            Err(ErrorTrama::Tipo),
            "version {version}, dialecto {dialecto}"
        );
        assert_eq!(
            r.publicado().1,
            hola_de_subida(false, 0),
            "su HOLA sigue diciendo sesion 0 con lo que habla"
        );
    }
    // el sobre y la forma se juzgan antes, como con sesion
    assert_eq!(
        r.recibir(&TABLA_CRC16, &cruda(0x01, &[1, 1, 0])),
        Err(ErrorTrama::Forma)
    );
    let mut mala = hola(1, 1);
    mala[4] ^= 1;
    assert_eq!(r.recibir(&TABLA_CRC16, &mala), Err(ErrorTrama::Crc));
    assert!(!r.sesion());
    assert_eq!(r.sesiones(), 0);
    assert_eq!(
        r.cuentas(),
        Cuentas {
            rechazadas_crc: 1,
            rechazadas_forma: 1,
            rechazadas_tipo: otros.len() as u16 + 5,
            perdidas: 0,
        }
    );
}

/// §8.14, D5: un `HOLA` valido abre sesion. `sesiones` sube uno, los
/// contadores vuelven a cero (son totales desde la sesion, §3.3), se espera la
/// secuencia 1, y el generador recibe la sesion: todo suelto y `ultimo_evento`
/// a cero.
#[test]
fn hola_abre_la_sesion() {
    let mut r = Receptor::default();
    assert_eq!(
        r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 5)),
        Err(ErrorTrama::SinSesion)
    );
    let (cab, m) = r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("abre");
    assert_eq!(
        m.entradas(cab.secuencia).collect::<Vec<_>>(),
        [Entrada::Sesion]
    );
    assert!(r.sesion());
    assert_eq!(r.sesiones(), 1);
    assert_eq!(r.cuentas(), Cuentas::default());
    r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 1))
        .expect("con sesion pasa");
    assert_eq!(r.cuentas().perdidas, 0, "tras HOLA se espera la 1");
    r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 4))
        .expect("la secuencia no rechaza");
    assert_eq!(r.cuentas().perdidas, 2, "faltaron la 2 y la 3");
}

/// D8 y §3.3: con sesion, cada rechazo suma en su causa (la trama corta va con
/// la forma) y no mueve la secuencia esperada, asi que el hueco que deja lo
/// cuenta `perdidas` y perdidas >= rechazadas.
#[test]
fn con_sesion_cada_rechazo_cuenta_en_su_causa() {
    let mut r = Receptor::default();
    r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("abre");
    let mut mala = trama(&Mensaje::Nada, 1);
    mala[4] ^= 1;
    assert_eq!(r.recibir(&TABLA_CRC16, &mala), Err(ErrorTrama::Crc));
    let t = trama(&Mensaje::Nada, 2);
    assert_eq!(
        r.recibir(&TABLA_CRC16, &t[..t.len() - 1]),
        Err(ErrorTrama::Corta)
    );
    assert_eq!(
        r.recibir(&TABLA_CRC16, &cruda(0x10, &[0; 6])),
        Err(ErrorTrama::Forma)
    );
    assert_eq!(
        r.recibir(&TABLA_CRC16, &cruda(0x02, &[])),
        Err(ErrorTrama::Tipo)
    );
    r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 6))
        .expect("pasa");
    assert_eq!(
        r.cuentas(),
        Cuentas {
            rechazadas_crc: 1,
            rechazadas_forma: 2,
            rechazadas_tipo: 1,
            perdidas: 5,
        }
    );
}

/// D5, «no abre sesion y su `HOLA` lo dice»: un `HOLA` que el modulo no habla
/// cierra la sesion que hubiera. Sin sesion el modulo publica su `HOLA`, y asi
/// el cerebro ve el desacuerdo; con la sesion abierta seguiria leyendo con el
/// dialecto viejo lo que el cerebro escribe en el nuevo.
#[test]
fn un_hola_que_no_se_habla_cierra_la_sesion() {
    let mut r = Receptor::default();
    r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("abre");
    assert_eq!(r.recibir(&TABLA_CRC16, &hola(1, 2)), Err(ErrorTrama::Tipo));
    assert!(!r.sesion());
    assert_eq!(r.sesiones(), 1, "cerrar no cuenta como sesion");
    assert_eq!(r.cuentas().rechazadas_tipo, 1);
    assert_eq!(
        r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 1)),
        Err(ErrorTrama::SinSesion)
    );
}

/// D5: el cerebro reabre sesion sobre un modulo vivo. `sesiones` sube otra
/// vez, los contadores vuelven a cero y se espera otra vez la 1; `sesiones`
/// da la vuelta en un byte (§3.3).
#[test]
fn hola_en_sesion_la_reabre() {
    let mut r = Receptor::default();
    r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("abre");
    r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 900))
        .expect("pasa");
    assert_eq!(r.cuentas().perdidas, 899);
    r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("reabre");
    assert_eq!((r.sesion(), r.sesiones()), (true, 2));
    assert_eq!(r.cuentas(), Cuentas::default());
    r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 1))
        .expect("pasa");
    assert_eq!(r.cuentas().perdidas, 0);
    for _ in 3..=256 {
        r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("reabre");
    }
    assert_eq!(r.sesiones(), 0, "la sesion 256 da la vuelta");
}

fn hola_de_subida(sesion: bool, sesiones: u8) -> Registro {
    Registro::Hola {
        version: 1,
        dialecto: 1,
        sesion,
        sesiones,
    }
}

fn registro(r: &Registro, secuencia: u16) -> Vec<u8> {
    let mut out = [0u8; 64];
    let n = r
        .codificar(&TABLA_CRC16, secuencia, &mut out)
        .expect("se codifica");
    out[..n].to_vec()
}

fn salud() -> Registro {
    Registro::Salud {
        temperatura_centesimas: -2_550,
        vref_milivoltios: 3_300,
        cuentas: Cuentas {
            rechazadas_crc: 1,
            rechazadas_forma: 2,
            rechazadas_tipo: 3,
            perdidas: 0x1234,
        },
    }
}

fn estado() -> Registro {
    Registro::EstadoVoz {
        cola_desbordada: 0x0102,
        ultimo_evento: 0x0304,
        bahia_aplicada: 0x0506,
        watchdogs: 0x0708,
    }
}

/// Los registros de borde de §8.1: todo cero, todo `0xFF`, `HOLA` con
/// `sesion` 0 y 1, y campos distintos entre si.
fn registros() -> Vec<Registro> {
    let todo = Cuentas {
        rechazadas_crc: 0xFFFF,
        rechazadas_forma: 0xFFFF,
        rechazadas_tipo: 0xFFFF,
        perdidas: 0xFFFF,
    };
    vec![
        Registro::Nada,
        hola_de_subida(false, 0),
        hola_de_subida(true, 0xFF),
        Registro::Salud {
            temperatura_centesimas: 0,
            vref_milivoltios: 0,
            cuentas: Cuentas::default(),
        },
        Registro::Salud {
            temperatura_centesimas: i16::MIN,
            vref_milivoltios: 0xFFFF,
            cuentas: todo,
        },
        salud(),
        Registro::EstadoVoz {
            cola_desbordada: 0,
            ultimo_evento: 0,
            bahia_aplicada: 0,
            watchdogs: 0,
        },
        Registro::EstadoVoz {
            cola_desbordada: 0xFFFF,
            ultimo_evento: 0xFFFF,
            bahia_aplicada: 0xFFFF,
            watchdogs: 0xFFFF,
        },
        estado(),
    ]
}

/// §8.1 y §8.4 para la subida: cada registro vuelve igual, con las dos
/// secuencias extremas y con lo que el maestro cloco detras.
#[test]
fn ida_y_vuelta_de_cada_registro() {
    for r in registros() {
        for secuencia in [0, 0xFFFF] {
            let mut t = registro(&r, secuencia);
            let cabecera = Cabecera {
                tipo: t[0],
                largo: (t.len() - SOBRE) as u8,
                secuencia,
            };
            t.extend_from_slice(&[0; 33]);
            assert_eq!(
                decodificar_registro(&TABLA_CRC16, &t),
                Ok((cabecera, r)),
                "{r:?}"
            );
        }
    }
}

/// §3.1 y §3.3: el tipo y la carga de cada registro, byte a byte.
#[test]
fn los_registros_byte_a_byte() {
    let bytes = |r: &Registro| {
        let t = registro(r, 0);
        (t[0], t[4..t.len() - 2].to_vec())
    };
    assert_eq!(bytes(&Registro::Nada), (0x80, vec![]));
    assert_eq!(bytes(&hola_de_subida(false, 0)), (0x81, vec![1, 1, 0, 0]));
    assert_eq!(bytes(&hola_de_subida(true, 7)), (0x81, vec![1, 1, 1, 7]));
    // -25,50 grados son -2 550 = 0xF60A; 3 300 mV son 0x0CE4.
    assert_eq!(
        bytes(&salud()),
        (
            0x82,
            vec![0x0A, 0xF6, 0xE4, 0x0C, 1, 0, 2, 0, 3, 0, 0x34, 0x12]
        )
    );
    assert_eq!(
        bytes(&estado()),
        (0x93, vec![0x02, 0x01, 0x04, 0x03, 0x06, 0x05, 0x08, 0x07])
    );
}

/// §8.8, R-C5: cada registro de §3.3 cabe con su sobre en la ventana de la
/// Voz, y `SALUD`, el piso universal, mide exactamente 18 (D6.3).
#[test]
fn la_ventana_de_la_voz() {
    assert_eq!(VENTANA_SUBIDA, 24);
    for r in registros() {
        assert!(registro(&r, 0).len() <= VENTANA_SUBIDA, "{r:?}");
    }
    assert_eq!(registro(&salud(), 0).len(), 18);
    assert_eq!(registro(&estado(), 0).len(), 14);
    assert_eq!(registro(&hola_de_subida(true, 1), 0).len(), 10);
}

/// D8 del lado del cerebro: un registro sin la forma de su tipo se rechaza
/// entero; un tipo que no es de subida, o sin carga en v1 (`JACKS`, `MEDIDA`,
/// `LOG`), por tipo.
#[test]
fn la_forma_mala_de_un_registro() {
    let malas: [(u8, &[u8]); 9] = [
        (0x80, &[0]),
        (0x81, &[1, 1, 0]),
        (0x81, &[1, 1, 0, 0, 0]),
        (0x81, &[1, 1, 2, 0]),
        (0x82, &[0; 11]),
        (0x82, &[0; 13]),
        (0x93, &[0; 7]),
        (0x93, &[0; 9]),
        (0x93, &[]),
    ];
    for (tipo, carga) in malas {
        assert_eq!(
            decodificar_registro(&TABLA_CRC16, &cruda(tipo, carga)),
            Err(ErrorTrama::Forma),
            "{tipo:#04x} {carga:?}"
        );
    }
    for tipo in [0x00, 0x01, 0x83, 0x90, 0x91, 0x92, 0x94] {
        assert_eq!(
            decodificar_registro(&TABLA_CRC16, &cruda(tipo, &[])),
            Err(ErrorTrama::Tipo),
            "{tipo:#04x}"
        );
    }
}

/// Un giro que muestrea la subida entera: el cerebro cloca la trama con
/// relleno hasta la ventana y el byte de cola (D6.3, D6.4).
fn giro(m: &Mensaje, secuencia: u16) -> Vec<u8> {
    let mut t = trama(m, secuencia);
    t.resize(t.len().max(VENTANA_SUBIDA + 1), 0);
    t
}

/// Un giro entero, y lo que queda publicado para el siguiente.
fn tras_giro(r: &mut Receptor) -> (u16, Registro) {
    let _ = r.recibir(&TABLA_CRC16, &giro(&Mensaje::Nada, 0));
    r.publicado()
}

/// D5 y D6.2: sin sesion el modulo publica solo su `HOLA`, desde que arranca,
/// y la secuencia del registro sube uno por publicacion. Un registro se queda
/// publicado hasta que un giro lo cloca entero con el byte de cola
/// (`bytes - 1 >= largo + 6`); lo que se pida sin sesion no sale.
#[test]
fn sin_sesion_solo_sale_su_hola() {
    let mut r = Receptor::default();
    assert_eq!(r.publicado(), (0, hola_de_subida(false, 0)));
    r.pedir(salud());
    r.pedir(estado());
    let mut t = trama(
        &Mensaje::Compuerta {
            mascara: 0,
            contador: 0,
        },
        1,
    );
    assert_eq!(t.len(), 10, "el HOLA de subida entero, sin el byte de cola");
    let _ = r.recibir(&TABLA_CRC16, &t);
    assert_eq!(r.publicado(), (0, hola_de_subida(false, 0)));
    t.push(0);
    let _ = r.recibir(&TABLA_CRC16, &t);
    assert_eq!(r.publicado(), (1, hola_de_subida(false, 0)));
    for s in 2..6 {
        assert_eq!(tras_giro(&mut r), (s, hola_de_subida(false, 0)));
    }
}

/// D5: abrir sesion pone a cero la secuencia de subida, abandona el registro a
/// medio muestrear y publica el `HOLA` con `sesion = 1`, que sale con la
/// secuencia 0. Despues (§3.3), lo pedido, en orden y uno por muestreo, con lo
/// ultimo que se pidio de cada tipo; y `NADA` cuando no toca nada.
#[test]
fn la_sesion_publica_su_hola_y_despues_lo_pedido() {
    let mut r = Receptor::default();
    for _ in 0..3 {
        tras_giro(&mut r);
    }
    assert_eq!(r.publicado().0, 3);
    // el giro del HOLA son 8 bytes: el HOLA de subida queda a medias
    r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("abre");
    assert_eq!(r.publicado(), (0, hola_de_subida(true, 1)));
    r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 1))
        .expect("pasa");
    assert_eq!(r.publicado(), (0, hola_de_subida(true, 1)), "giro corto");
    let otro = Registro::EstadoVoz {
        cola_desbordada: 9,
        ultimo_evento: 8,
        bahia_aplicada: 7,
        watchdogs: 6,
    };
    r.pedir(estado());
    r.pedir(salud());
    r.pedir(otro);
    assert_eq!(tras_giro(&mut r), (1, salud()));
    r.recibir(&TABLA_CRC16, &trama(&Mensaje::Nada, 3))
        .expect("pasa");
    assert_eq!(
        r.publicado(),
        (1, salud()),
        "SALUD sigue hasta salir entera"
    );
    assert_eq!(tras_giro(&mut r), (2, otro));
    assert_eq!(tras_giro(&mut r), (3, Registro::Nada));
    assert_eq!(tras_giro(&mut r), (4, Registro::Nada));
}

/// D5: reabrir abandona el registro a medias y lo pedido, que era de la sesion
/// vieja (sus cuentas lo son). Cerrarla con un `HOLA` que no se habla tambien
/// abandona lo publicado: sin sesion solo sale el `HOLA`.
#[test]
fn reabrir_o_cerrar_abandona_lo_publicado() {
    let mut r = Receptor::default();
    r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("abre");
    r.pedir(salud());
    r.pedir(estado());
    assert_eq!(tras_giro(&mut r), (1, salud()));
    r.recibir(&TABLA_CRC16, &hola(1, 1)).expect("reabre");
    assert_eq!(r.publicado(), (0, hola_de_subida(true, 2)));
    assert_eq!(
        tras_giro(&mut r),
        (1, Registro::Nada),
        "lo pedido se descarta"
    );
    r.pedir(salud());
    assert_eq!(tras_giro(&mut r), (2, salud()));
    assert_eq!(r.recibir(&TABLA_CRC16, &hola(1, 2)), Err(ErrorTrama::Tipo));
    assert_eq!(r.publicado(), (3, hola_de_subida(false, 2)));
    r.pedir(estado());
    assert_eq!(tras_giro(&mut r), (4, hola_de_subida(false, 2)));
}
