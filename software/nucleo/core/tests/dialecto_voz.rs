//! Los mensajes de bajada del dialecto de la Voz v1, contra el papel de la
//! cabecera.
//!
//! Papel: `docs/superpowers/specs/2026-09-02-cabecera-j2-design.md`, D4 (los
//! cinco mensajes y la tabla de indices), D8 (las causas de rechazo), §3.2 (los
//! bytes) y §4 (los largos contra R-E1). Los numeros de los tests son los de
//! su §8.
//!
//! Los bytes esperados y los rangos se escriben a mano desde el papel: un test
//! que lea la tabla que prueba no prueba nada.

use sam17_nucleo_core::bahia::{Chip, Imagen, CANALES, LINEAS};
use sam17_nucleo_core::descubrimiento::{crc16, TABLA_CRC16};
use sam17_nucleo_core::dialecto_voz::{decodificar, Escritura, Mensaje, MAX_ESCRITURAS};
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
    // TONO y BAHIA esperan a sus duenos, que no son el generador; NADA y HOLA
    // no llevan nada para el.
    for m in [
        Mensaje::Nada,
        casos()[1],
        casos()[7],
        Mensaje::Bahia(bahia_llena()),
    ] {
        assert_eq!(m.entradas(1).count(), 0, "{m:?}");
    }
}
