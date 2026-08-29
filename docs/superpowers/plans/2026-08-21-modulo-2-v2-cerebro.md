# Módulo 2 v2 «El cerebro» — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Esquemático + PCB de la placa del cerebro (RP2350B, ocho ranuras J2, mux I²C, USB de doble rol con aislador, MIDI DIN, clock/reset, pedal, cabeza local y puente inalámbrico), generados por script con todos los gates del repo en verde, más bring-up escrito y los docs sincronizados.

**Architecture:** El patrón del repo, sin excepciones: `build_schematic.py` escribe el `.kicad_sch` directamente vía `hardware/tools/symlib.py` (**sin** el servidor MCP — ya truncó una hoja una vez), con las dos guardias propias antes de escribir (vértice de cable exacto en cada pin, y `schcheck.py` contra redes fusionadas), y verifica con `kicad-cli`. El PCB va con `pcbnew` directo. Las ocho ranuras J2 son **un bucle** en el generador, no ocho copias. Los pines los toma de `pinout.rs`, que es la única fuente — y por eso la puerta de pines mide **capacidad**, no identidad.

**Tech Stack:** Python 3 + KiCad 10 (`kicad-cli`, `pcbnew`), `hardware/tools/{symlib,schcheck,gates,netdiff}.py`, Rust estable para `pinout.rs`, `gh` para el ciclo PR.

**Spec:** `docs/superpowers/specs/2026-08-21-modulo-2-v2-cerebro-design.md`

## Global Constraints

- **RP2350B en QFN-80**, no el A. El pinout se verifica contra la figura del datasheet **del encapsulado que se compra**, no contra un diagrama de familia.
- **Ninguna pieza entra al BOM sin su datasheet abierto.** Dato inventado nunca: verificado contra la hoja con documento y página citados, o **celda vacía**. Aplica a las once piezas que la spec deja con criterio y sin número de parte.
- **`pinout.rs` es la única fuente de pines.** `build_schematic.py` lo lee; nadie transcribe un GPIO a mano. Corolario: la puerta de pines mide capacidad (§11 de la spec), porque la identidad ya está garantizada por construcción.
- **La barrera del aislador USB no la cruza nada**: ni pista, ni plano, ni vía, en ninguna capa. Se mide sobre la placa ruteada.
- **`GNDD` es la masa de esta placa**; no hay `GNDA`. La unión con `GNDA` vive en la estrella del módulo 1 y aquí no se toca.
- **La corriente de la cadena WS2812 no cruza el plano del SPI**: vive en una isla de potencia en el canto. Se mide sobre el cobre final.
- **Los `TUNE_OUT` no llevan filtro.** Solo resistencia de serie. Todo el margen del afinado son 131 ns y un flanco redondeado se los come.
- **Estado de arranque obligado** (spec §4.3): `CS` ×8 desasertados por pull-up del cerebro, gates bajos, dato del WS2812 bajo, `EN` del host apagado, `CLOCK`/`RESET` out bajos. Nada de eso depende de lo que hagan los pads del micro tras reset.
- **Gates:** ERC 0, DRC 0, 0 sin conectar, `check_netlist.py`, `check_bom.py`, `check_pinout.py` y `check_aislamiento.py` verdes, y los cinco `*_budget.py` verdes. `hardware/tools/gates.py` los descubre por patrón; ninguno se añade a una lista.
- **Cada gate nuevo nace con su mutación corrida.** Escribirlo no basta: hay que verlo morder.
- Nombres: proyecto `sam17-cerebro`, ficheros en `hardware/02-midi-cv/kicad-v2/`. **La v1 no se toca** — su carpeta queda como está, marcada SUPERADA.
- Convención de commits del repo: mensaje en español que cuenta el porqué, con el trailer de coautoría.

## Tabla maestra de redes (todas las tareas la usan)

**Alimentación**

| Red | Qué es |
|---|---|
| `+5V_IN` | entra por `J6` (KK-254) desde la IRM-15-5 |
| `+5V_LED` | después del sensor de corriente, hacia la cadena — vive en la isla de potencia |
| `+3V3` | regulador local desde `+5V_IN` |
| `+12V`, `-12V` | peine Eurorack. `-12V` **sin usar**, declarado así |
| `+10V_GATE` | regulador local desde `+12V`, solo para los gates |
| `VBUS_HOST` | salida del interruptor de carga hacia el USB-A |
| `VBUS_DEV` | VBUS del USB-B — **solo** alimenta el lado alto del aislador |
| `GNDD` | la masa de la placa |
| `GND_ISO` | la masa del lado alto del aislador. **No toca `GNDD` en ninguna capa** |

**El enlace J2 (n = 1..8)**

| Red | Qué es |
|---|---|
| `SPI_SCLK`, `SPI_MOSI`, `SPI_MISO` | tronco, compartido por las ocho ranuras |
| `SPI_SCLK_n`, `SPI_MOSI_n`, `SPI_MISO_n` | después de la resistencia de serie de cada ranura, al pin 1/3/4 de su IDC |
| `SPI_CS_n` | un `CS` por ranura, con pull-up a `+3V3` |
| `I2C_SDA_T`, `I2C_SCL_T` | tronco: mux, EEPROM del cerebro y TMP1075 del cerebro |
| `I2C_SDA_n`, `I2C_SCL_n` | canal n del mux, con sus pull-ups, al pin 7/8 de su IDC |
| `MUX_RESET` | recuperación del tronco trabado |
| `TUNE_OUT_1..4` | pines 9-12, **solo de la ranura 1** |

**Gates y sincronía**

| Red | Qué es |
|---|---|
| `GATE_n_3V3` (n=1..4) | GPIO → puerta del primer MOSFET, con pull-down |
| `GATE_n` | salida de 0/10 V al conector `J_GATE` |
| `CLK_IN_J`, `RST_IN_J` | punta del jack, antes del divisor |
| `CLK_IN`, `RST_IN` | después del divisor y el recorte, al GPIO |
| `CLK_OUT_3V3`, `RST_OUT_3V3` | GPIO → entrada del buffer de 5 V |
| `CLK_OUT`, `RST_OUT` | salida de 0/5 V al jack |
| `LED_DATA_3V3` | GPIO → entrada del mismo buffer |
| `LED_DATA` | salida de 5 V hacia la cadena |
| `LED_SENSE` | salida del sensor de corriente → entrada de ADC |

**USB**

| Red | Qué es |
|---|---|
| `USB_DP_ISO`, `USB_DM_ISO` | del conector USB-B al lado alto del aislador |
| `USB_DP`, `USB_DM` | del lado bajo del aislador al RP2350B |
| `PIOUSB_DP`, `PIOUSB_DM` | del USB-A a los dos GPIO del PIO |
| `HOST_EN`, `HOST_FAULT` | mando y bandera del interruptor de carga |

**MIDI, pedal, cabeza y puente**

| Red | Qué es |
|---|---|
| `DIN_IN_4`, `DIN_IN_5` | pines 4 y 5 del DIN-5 de entrada, al LED del optoacoplador |
| `MIDI_RX` | salida del optoacoplador → GPIO |
| `MIDI_TX` | GPIO → driver de la salida DIN |
| `DIN_OUT_4`, `DIN_OUT_5` | pines 4 y 5 del DIN-5 de salida |
| `PEDAL_T`, `PEDAL_R` | punta y anillo del jack de 6,35 mm |
| `PEDAL_ADC` | después de la protección, a la entrada analógica |
| `LCD_SCLK`, `LCD_MOSI`, `LCD_CS`, `LCD_DC`, `LCD_BL` | la pantalla de 2,8", en el SPI1 (el SPI0 es del J2) |
| `ENC_A`, `ENC_B`, `ENC_SW` | encoder y su pulsador |
| `BRIDGE_TX`, `BRIDGE_RX`, `BRIDGE_EN`, `BRIDGE_BOOT` | el zócalo del puente |

**El micro**

| Red | Qué es |
|---|---|
| `QSPI_SCK`, `QSPI_CS`, `QSPI_SD0..3` | flash externa |
| `XIN`, `XOUT` | cristal |
| `RUN`, `BOOTSEL` | los dos botones |

---

### Task 1: Las once piezas, contra datasheet — y el reparto del +5 V

Ninguna línea de esquemático se escribe hasta que esta tarea cierre. La spec dejó once piezas con criterio escrito y celda vacía a propósito.

**Files:**
- Create: `hardware/02-midi-cv/bom-v2.csv`
- Create: `hardware/02-midi-cv/notes/piezas-v2.md`

**Interfaces:**
- Produce: los números de parte y los pinouts que consumen las tareas 4 a 9, y las constantes de corriente que consume `power_budget.py` (Task 2).

- [ ] **Step 1: Cerrar el issue #151 — de qué riel cuelga esta placa, y cuánto le toca.**

Primero lo que hay que tener claro, porque una versión anterior de este plan lo tenía mal: **este instrumento tiene tres rieles de 5 V y no son el mismo.**

```
+5V analogico   U3, el 7805 de la v1.  300 mA de diseno.  GNDA.  Sale por J6.
                Se dimensiono para el AD5686R y el backlight del LCD del
                modulo 2 DEL PI. Ninguna de las dos cosas existe ya.
+5V digital     IRM-15-5, 5 V / 3,00 A.  GNDD.  NO pasa por la placa de la
                fuente: se monta fuera y va directa al lado digital.
                <- ESTE es el riel de esta placa.
+12V            La cascada GOAT, 650 mA/riel, GNDA. Solo para los gates.
```

Colgar el cerebro de `J6` cruzaría `GNDA` con `GNDD` **y** le pediría amperios a un 7805 acotado a 300 mA. No se hace.

Y el reparto del riel digital, con los números del #104 y de la spec de la fuente:

```
IRM-15-5 nominal ....................... 3,00 A
piso duro del RP2350 (fuera del reparto) 0,20 A
tope del #104 para toda la luz ......... 2,50 A   (bajo de 2,80 el 2026-08-19)
uso REAL que el #104 documenta ......... 2,04 - 2,28 A
host USB en su limite .................. 0,50 A
```

**El tope no es una carga: es una política.** El #104 ya trae el mecanismo —estimar la corriente de cada cuadro antes de enviarlo y escalar **por clase**— con tres clases y sus prioridades: la guía de patcheo no se atenúa nunca, los LED de estado ceden si hace falta, el farol cede primero.

Lo que falta, y es lo que esta tarea cierra:

  1. **Añadir el puerto host como cuarta clase** de esa tabla, con la propiedad que lo hace distinto de las otras tres: **el firmware no lo puede atenuar**. Aparece cuando alguien enchufa un teclado y se va cuando lo saca. Va por encima del farol y por debajo de la guía.
  2. **Decidir el límite del interruptor de carga.** 500 mA es lo que reserva el estándar; lo que pide un controlador MIDI real es bastante menos, pero eso hay que **medirlo y citarlo**, no suponerlo. El límite elegido es la cuota que el árbitro reserva cuando `HOST_EN` está activo.
  3. Escribir las dos cosas en `piezas-v2.md` con su razón, para que `power_budget.py` (Task 2) las asevere.

Si al medir resulta que ni con el farol apagado cabe, entonces sí se sube la fuente digital — y la spec de la fuente ya reserva ese camino: *«si algún día algo pide ese riel en serio, la térmica del recinto se rehace antes»*. Es la salida, no la primera opción.

- [ ] **Step 2: Elegir las once piezas** contra su criterio de la spec, y **abrir la hoja de cada una**. La tabla va a `piezas-v2.md` con esta forma exacta, y **una fila sin las tres últimas columnas es una fila que no entra al BOM**:

```
| Función | Parte | Encapsulado | Datasheet (doc + pág. del pinout) | Stock LCSC | Verificado por |
```

Las once, con lo que hay que confirmar en cada una:

| Función | Qué hay que confirmar en la hoja |
|---|---|
| **Mux I²C 8 canales** (issue #81) | Que tenga pin de `RESET`, la tensión de los dos lados, y stock |
| **Aislador USB** | Que sea full-speed, **de qué lado va la pull-up de `D+`**, y qué pines de control necesita |
| **Optoacoplador DIN** | Tiempo de subida contra el bitrate de MIDI, y los valores de la variante de 3,3 V de la especificación de la MIDI Association |
| **Pantalla SPI de 2,8"** | Controlador con framebuffer propio, **entrada de PWM en la retroiluminación** (sin eso no entra en el árbitro del #104), lógica de 3,3 V sin traducción, y su consumo real de retroiluminación al 100 % — no el del datasheet del panel suelto |
| **Módulo del puente** | Que sea la variante con **U.FL**, su pico de corriente, y qué antenas cubre su certificado |
| **Interruptor de carga** | Límite, bandera, y **si se enclava en fallo** (de ahí el `EN` por GPIO) |
| **Sensor de corriente del +5 V** | Rango contra 2,50 A, y salida compatible con una entrada de ADC de 3,3 V |
| **Buffer de 5 V** | Umbral de entrada TTL (que 3,3 V lea como alto). **Cuatro canales fijos**: con los dígitos fuera ya no hay nada que pueda hacerlo crecer a seis |
| **MOSFET de gate ×2** | Umbral de puerta con 3,3 V, y que la cadena de dos sea **no inversora** |
| **Regulador de 10 V** | **Margen de caída** contra el peor caso de `+12V` (Task 2), no solo corriente |
| **Regulador de 3V3** | Corriente con el puente RF en pico, y su disipación — el TMP1075 va pegado a él |
| **Protección contra descargas** | Capacidad parásita contra los flancos que protege: la del USB y la del clock no pueden ser la misma pieza. **Nueve conectores de panel, nueve caminos que proteger** (spec §6) |

Más el RP2350B, la flash QSPI, el cristal, y los dos conectores USB.

Son **doce**, no once: la spec §6 declara la protección de panel en una línea
y no la lista entre las piezas con criterio. Aquí se lista, porque una pieza que
no está en el BOM no se compra.

- [ ] **Step 3: El pinout del RP2350B, contra la figura del QFN-80.** No contra un diagrama de la familia: dos pines desfasados entre encapsulados del mismo chip ya costó una tarde en este proyecto. Anotar en `piezas-v2.md` la página exacta de la figura.

- [ ] **Step 4: Escribir `bom-v2.csv`** con las filas verificadas, en el mismo formato que `hardware/03-vco/bom.csv` (mismas columnas, para que `check_bom.py` funcione igual).

- [ ] **Step 5: Commit.**

```bash
git add hardware/02-midi-cv/bom-v2.csv hardware/02-midi-cv/notes/piezas-v2.md
git commit
```

---

### Task 2: Los presupuestos que pueden vetar — potencia y PIO

Van **antes** del esquemático porque pueden tumbar una pieza o un pin, y corregir eso después de dibujar cuesta el doble.

**Files:**
- Create: `hardware/02-midi-cv/power_budget.py`
- Create: `hardware/02-midi-cv/pio_budget.py`

**Interfaces:**
- Consume: las corrientes de `piezas-v2.md` (Task 1) y `F_PIO` de `hardware/02-midi-cv/autotune_budget.py`.
- Produce: el veredicto sobre `+5V` y el reparto de PIO que la Task 3 escribe en `pinout.rs`.

- [ ] **Step 1: `power_budget.py`.** Sigue `hardware/03-vco/dac_local_budget.py` como plantilla de forma (constantes con unidad y fuente, autocomprobación, aserciones, bloque de lo que NO cubre). Y cumple estas cuatro cosas, que son la razón de que exista:

```python
# 1. IMPORTA el tope del #104 de la spec de la fuente, no lo transcribe.
#    Una version anterior de la spec transcribio 2.80 A y estaba caduco.
# 2. Suma la cadena WS2812 como carga de la MISMA IRM-15-5 que el resto.
#    Si no la suma, sale verde sobre un riel sobresuscrito.
# 3. Asevera MARGEN DE CAIDA, no solo corriente: la tension minima
#    garantizada en la entrada del regulador de 10 V, despues del PTC de
#    la bus board y del elemento de proteccion del #59.
# 4. Asevera el riel digital en DOS escenarios, no en uno:
#      a) los LED en su tope y el host apagado
#      b) el host en su limite y el arbitro habiendo cedido el farol
#    Falla si CUALQUIERA de los dos no cabe. Un solo escenario deja fuera
#    justo el caso que decide el diseno: alguien enchufa un teclado.
# 5. NO cuelga esta placa de J6. J6 es el 7805 de 300 mA en GNDA; el riel
#    de esta placa es la IRM-15-5 en GNDD. Si el guion los suma, esta
#    sumando dos fuentes distintas con dos masas distintas.
```

- [ ] **Step 2: Correr el escenario (b) sin la cuota del host reservada** y verlo fallar. `Expected: FALLO`. Si sale verde antes de que la Task 1 haya decidido el límite y la clase, el guion no está midiendo lo que dice.

- [ ] **Step 3: Aplicar la decisión de la Task 1 y verlo pasar** en los dos escenarios.

- [ ] **Step 4: `pio_budget.py`.** Cuenta lo que de verdad escasea:

```python
# - Maquinas de estado, memoria de instrucciones y canales de DMA que
#   piden: 4 contadores reciprocos, el host USB, la cadena WS2812.
# - El reparto de los dos nucleos, con el host USB DENTRO (la spec del
#   nucleo asigna el 0 a tiempo real y el 1 a atribucion, y no le dio
#   sitio al host).
# - LA ASERCION QUE IMPORTA: importa F_PIO de autotune_budget.py y falla
#   si el reloj que exige el host USB no es el que supone el afinado.
#   Si el host baja clk_sys a 120 MHz, el sellado pasa de 6.67 a 8.33 ns
#   y los 131 ns del 74HC14 se mueven sin que nadie toque el afinado.
#   Issue #150.
# - La ventana de 32 pines por bloque PIO (base 0 o 16), contra el mapa
#   de pinout.rs.
```

- [ ] **Step 5: La mutación del segundo.** Cambiar a mano el reloj que declara el host USB a un valor distinto de `F_PIO` y comprobar que **se pone rojo**. Un presupuesto de conflicto que nunca ha visto un conflicto no es un presupuesto.

- [ ] **Step 6: Commit.**

---

### Task 3: `pinout.rs` crece, y la puerta de pines deja de ser una tautología

**Files:**
- Modify: `software/nucleo/core/src/pinout.rs`
- Create: `hardware/02-midi-cv/kicad-v2/check_pinout.py`

**Interfaces:**
- Produce: los **diez** pines nuevos (cinco de placa + cinco de pantalla) que consumen las tareas 6, 8 y 9, la baja de los tres de dígitos, y la función `pines()` que `build_schematic.py` importa.

- [ ] **Step 1: Escribir los tests que fallan** en `pinout.rs`, antes de tocar el mapa:

```rust
/// Los pines que consume cada programa de PIO, por prefijo de su nombre.
/// El afinado y la cadena de LED comparten bloque; el host USB va aparte.
pub static GRUPOS_PIO: &[&[&str]] = &[
    &["TUNE_OUT 1", "TUNE_OUT 2", "TUNE_OUT 3", "TUNE_OUT 4", "WS2812 datos"],
    &["PIO-USB D+", "PIO-USB D-"],
];

#[test]
fn los_pines_de_un_mismo_bloque_pio_caben_en_una_ventana() {
    // Cada bloque PIO del RP2350 ve 32 pines desde una base (0 o 16), asi
    // que los pines de un mismo programa tienen que caber en 32 contando
    // desde el menor de ellos.
    for grupo in GRUPOS_PIO {
        let gpios: heapless::Vec<u8, 8> = grupo
            .iter()
            .map(|n| PINOUT.iter().find(|p| p.para == *n)
                 .unwrap_or_else(|| panic!("el grupo nombra un pin que no existe: {n}"))
                 .gpio)
            .collect();
        let min = gpios.iter().min().unwrap();
        let max = gpios.iter().max().unwrap();
        assert!(max - min < 32, "el grupo {grupo:?} no cabe en una ventana de PIO");
    }
}

#[test]
fn los_pines_nuevos_de_la_placa_existen() {
    for nombre in ["host EN", "host fallo", "puente EN", "puente arranque",
                   "mux RESET", "LCD SCLK", "LCD MOSI", "LCD CS", "LCD DC",
                   "LCD BL"] {
        assert!(PINOUT.iter().any(|p| p.para == nombre), "falta {nombre}");
    }
}

#[test]
fn los_digitos_ya_no_estan() {
    // La pantalla de 2,8" los sustituye (spec §7). Si vuelven, alguien esta
    // trabajando contra una version vieja del plan y se van a pelear un pin.
    for nombre in ["digitos: datos", "digitos: reloj", "digitos: latch"] {
        assert!(!PINOUT.iter().any(|p| p.para == nombre),
                "{nombre} deberia haberse ido con los digitos");
    }
}

#[test]
fn quedan_al_menos_dos_gpio_libres() {
    // Con la pantalla dentro el mapa ocupa 46 de 48 (spec §12.16). Este test
    // no prohibe gastar los dos que quedan: obliga a que gastarlos sea una
    // decision, y no un descubrimiento en la fase de ruteo.
    assert!(GPIO_MAX as usize - N_PINES_USADOS >= 2,
            "quedan {} GPIO libres de {GPIO_MAX}", GPIO_MAX as usize - N_PINES_USADOS);
}
```

- [ ] **Step 2: Verlo fallar.** `cargo test -p sam17-nucleo-core pinout`. Expected: FAIL en `los_pines_nuevos_de_la_placa_existen` y en `los_digitos_ya_no_estan`. Los otros dos pasan hoy y tienen que **seguir** pasando: son los que se pondrán rojos si el mapa se pasa de la raya más adelante.

- [ ] **Step 3: Dar de baja los tres de dígitos y añadir los diez nuevos.** El fondo disponible son los nueve GPIO libres (38, 39, 41-47) más los tres que devuelven los dígitos (33, 34, 35): **doce para diez**, y quedan dos.

  `LCD_SCLK` y `LCD_MOSI` **no se colocan a ojo**: el J2 ocupa el SPI0, así que van forzosamente en GPIO que expongan el **SPI1**, y `LCD_BL` en uno con PWM (spec §7 y §11.1). **Abre la tabla de funciones de GPIO del datasheet del RP2350B antes de escribir un número** — esta es exactamente la clase de dato que el plan no puede darte de memoria.

  Añade también los dos grupos de PIO. Correr `cargo test` hasta verde. **Los 183 tests anteriores siguen pasando** — si alguno se rompe, el mapa tenía un problema antes.

- [ ] **Step 4: `check_pinout.py`** — y **no** compara la netlist con `pinout.rs`. Si `build_schematic.py` lee `pinout.rs`, esa comparación compara la propuesta consigo misma: es el golden de netlist otra vez, un verde vacío. Mide **capacidad**:

```python
# 1. Cada funcion cae en un pin que la sabe hacer, contra la tabla del
#    datasheet del QFN-80 anotada en piezas-v2.md:
#    - el pedal en una entrada de ADC de las que EXISTEN
#    - SDA/SCL en pines con funcion I2C
#    - ninguna funcion encima de los pines del arranque por QSPI
# 2. Los pines de un mismo programa de PIO, en la misma ventana de 32.
# 3. El par del PIO-USB, adyacente.
```

- [ ] **Step 5: La mutación.** Mover un `TUNE_OUT` por encima del pin 31 y comprobar que `check_pinout.py` se pone **rojo**. Comprobar además que esa misma modificación **pasa** todos los tests viejos de `pinout.rs` — que es exactamente por qué esta puerta hace falta.

- [ ] **Step 6: Commit.**

---

### Task 4: `build_schematic.py` — esqueleto, alimentación, masas y la barrera

**Files:**
- Create: `hardware/02-midi-cv/kicad-v2/build_schematic.py`
- Create: `hardware/02-midi-cv/kicad-v2/sam17.kicad_sym`
- Create: `hardware/02-midi-cv/kicad-v2/sym-lib-table`

- [ ] **Step 1: Copiar de `hardware/03-vco/kicad/build_schematic.py`** la estructura: imports de `symlib` y `schcheck`, helpers de escritura, cajetín, y **las dos guardias antes de escribir nada** (vértice exacto <0,01 mm en cada pin; `schcheck.py` contra redes fusionadas). Docstring nuevo con las decisiones no obvias de **esta** placa: que los pines salen de `pinout.rs`, que `GND_ISO` no toca `GNDD`, y que la corriente del LED no cruza el plano del SPI.

- [ ] **Step 2: Los símbolos propios** que KiCad no trae, en `sam17.kicad_sym`: el mux I²C, el aislador, el módulo del puente y el sensor de corriente, con los pines **de la figura del datasheet**, no de memoria.

- [ ] **Step 3: Probar que `symlib` extrae todo lo que la hoja va a usar** antes de dibujar. Es la comprobación que va **antes** del paso destructivo: una hoja vacía de 711 bytes pasa el ERC con cero errores.

- [ ] **Step 4: Dibujar la alimentación:** `J6` (KK-254, `+5V_IN`/`GNDD`), el peine Eurorack (`+12V`/`GNDD`/`GNDD`/`-12V`, con `-12V` marcado NC deliberado y su cruz de no-conexión), la protección del issue #59 por riel, el regulador de `+3V3`, el de `+10V_GATE`, el sensor de corriente en el camino a `+5V_LED`, y el bulk por riel.

- [ ] **Step 5: La frontera del aislador**, dibujada como dos dominios: `+3V3`/`GNDD` de un lado y `VBUS_DEV`/`GND_ISO` del otro. **Ningún símbolo de masa compartido entre los dos.**

- [ ] **Step 6: Los test points con su rótulo en la serigrafía**: los cuatro rieles, `SPI_SCLK`/`MOSI`/`MISO`, los cuatro `TUNE_OUT`, `BRIDGE_TX`/`RX`, y **las dos caras del aislador**.

- [ ] **Step 7: Correr `python build_schematic.py`.** Expected: escribe `sam17-cerebro.kicad_sch`, las dos guardias pasan, y `kicad-cli sch erc` reporta **solo** pines sin conectar. El script imprime el conteo de componentes y redes.

- [ ] **Step 8: Commit.**

---

### Task 5: `build_schematic.py` — el micro y su arranque

**Files:**
- Modify: `hardware/02-midi-cv/kicad-v2/build_schematic.py`

- [ ] **Step 1: El RP2350B** con su desacoplo, la flash QSPI (`QSPI_SCK`/`CS`/`SD0..3`), el cristal (`XIN`/`XOUT`), y los dos botones `RUN` y `BOOTSEL`.

- [ ] **Step 2: Los pines desde `pinout.rs`.** El script **importa** el mapa y coloca cada red por su nombre. Nadie escribe un número de GPIO a mano en este archivo — si hiciera falta, la puerta de la Task 3 no serviría de nada.

- [ ] **Step 3: La tabla de estado de arranque, en cobre.** Pull-up en los ocho `SPI_CS_n`, pull-down en `GATE_n_3V3`, `LED_DATA_3V3`, `HOST_EN`, `CLK_OUT_3V3` y `RST_OUT_3V3`. Van aquí y no en las tareas de cada bloque porque son **una decisión sola** (spec §4.3) y así se revisan juntos.

- [ ] **Step 4: Correr el script.** Guardias verdes, ERC solo con pines aún sin pareja. Commit.

---

### Task 6: `build_schematic.py` — las ocho ranuras, el mux y la telemetría

**Files:**
- Modify: `hardware/02-midi-cv/kicad-v2/build_schematic.py`

- [ ] **Step 1: La función `dibujar_ranura(n, origen_xy)`**, llamada ocho veces. Una ranura es: IDC 2×6 con el pinout del contrato congelado, resistencias de serie en `SPI_SCLK_n`/`MOSI_n`/`MISO_n`, protección en `SPI_CS_n`/`I2C_SDA_n`/`I2C_SCL_n`, y los dos `GNDD`. **Los pines 9-12 solo se cablean con `n == 1`**; en las otras siete llevan su cruz de no-conexión.

El pinout del contrato va **comentado en el script como tabla**, igual que en el módulo 3, porque es el contrato de los módulos 4 a 9:

```
#  1 SCLK | 2 GNDD | 3 MOSI | 4 MISO | 5 CS_n  | 6 GNDD
#  7 SDA  | 8 SCL  | 9 TO_1 | 10 TO_2 | 11 TO_3 | 12 TO_4
#  SPI modo 1, <=10 MHz, CS abajo los 72 relojes de la trama.
#  Pines 9-12: SOLO ranura 1, rotulada VCO / TUNE en serigrafia.
```

- [ ] **Step 2: El mux I²C**: tronco `I2C_SDA_T`/`I2C_SCL_T` con sus pull-ups, `MUX_RESET` a su GPIO, y los ocho canales a sus ranuras **cada uno con sus propias pull-ups** dimensionadas por `enlace_budget.py` (Task 7).

- [ ] **Step 3: El pull-down de `SPI_MISO`** en el tronco, para que un `MISO` sin nadie lea cero y no ruido.

- [ ] **Step 4: La telemetría del cerebro**, aguas arriba del mux: la EEPROM de identidad y el TMP1075 **pegado al regulador de 3V3**, con su strap de dirección en una distinta de la que usan los módulos.

- [ ] **Step 5: Correr el script.** Guardias verdes. Commit.

---

### Task 7: Los presupuestos que dimensionan — enlace, sync y panel

**Files:**
- Create: `hardware/02-midi-cv/enlace_budget.py`
- Create: `hardware/02-midi-cv/sync_budget.py`
- Create: `hardware/02-midi-cv/panel_budget.py`

- [ ] **Step 1: Declarar la longitud máxima del mazo J2 por rama.** Ese número no existe hoy en ningún documento del repo, y sin él no hay presupuesto de flanco ni pull-ups de I²C. Se mide contra el case real y se anota con su fuente.

- [ ] **Step 2: `enlace_budget.py`** con **tres** aserciones separadas, no una:

```python
# 1. Terminacion: la serie de SCLK/MOSI contra el flanco de 10 MHz por
#    la longitud declarada, con ocho stubs.
# 2. Contencion: la serie de MISO limita la corriente de una pelea por
#    debajo de lo que aguantan los dos que se pelean.
#    OJO: 1 y 2 empujan la resistencia en direcciones OPUESTAS. Si se
#    escriben como una sola cuenta, la que gane deja la otra sin acotar.
# 3. V_IH: el divisor que forman la serie de MISO y su pull-down deja el
#    nivel alto dentro de lo que garantiza el datasheet del micro.
# 4. Tiempo de subida de I2C en las ocho ramas, contra la capacidad de
#    la cinta de la longitud declarada.
```

- [ ] **Step 3: `sync_budget.py`.** Evalúa **los dos casos** —fuente de 5 V y fuente de 10 V— y asevera qué umbral queda en cada uno. Si un divisor que salva los 10 V deja la de 5 por debajo del umbral, se pone rojo aquí y no con un módulo prestado enchufado.

- [ ] ~~**Step 4: `panel_budget.py`.**~~ **SIN SUJETO desde el 2026-08-27** — ver la enmienda de §10 de la spec: los nueve conectores se fueron a la trasera con D2, la cabeza local está derogada, y el censo del case (`ANCHOS_PISO_*`, `EXPANSION_MIN`) ya no existe. Este paso, tal como está escrito, suma piezas que no están en esa cara. Se reescribe cuando se decida qué lleva el panel del cerebro después de D2. Texto original:  Suma las huellas reales de los **once elementos** de §10 de la spec (nueve conectores, la cabeza local, los dos botones) más sus guardas; comprueba el alto contra el panel Eurorack 3U; e **importa** de `case/clearance_budget.py` para comprobar que el ancho cabe en la fila superior con el `EXPANSION_MIN` respetado, **sustituyendo** la clave `"MIDI/CV"` — sumar contaría el módulo 2 dos veces.

- [ ] **Step 5: Comprobar que el issue #152 aterrizó primero.** Si el censo del case sigue listando `VCO1`/`VCO2`/`VCO3`, este guion sale verde **porque tres VCO que no existen le prestan su sitio al cerebro**. Una verificación que solo funciona mientras sus entradas estén mal en direcciones opuestas no es una verificación.

- [ ] **Step 6: Correr los tres.** Commit.

---

### Task 8: `build_schematic.py` — gates, sincronía y la cadena de LED

**Files:**
- Modify: `hardware/02-midi-cv/kicad-v2/build_schematic.py`

- [ ] **Step 1: La función `dibujar_gate(n, origen_xy)`**, cuatro veces: cadena de dos MOSFET **no inversora**, con pull-down en la puerta de entrada, tirando de `+10V_GATE`. Reposo bajo al arrancar — la lección de la v1, que no se re-deriva.

- [ ] **Step 2: `J_GATE`**, KK-254 de 5 pines **con llave**: `GATE_1..4` + `GNDD`.

- [ ] **Step 3: Las cuatro entradas de sincronía**: jack → divisor → recorte a los rieles → GPIO, con los valores que salieron de `sync_budget.py`.

- [ ] **Step 4: El buffer de 5 V**, tres canales: `CLK_OUT_3V3`→`CLK_OUT`, `RST_OUT_3V3`→`RST_OUT`, `LED_DATA_3V3`→`LED_DATA`. Con resistencia de serie en las tres salidas.

- [ ] **Step 5: El conector de la cadena**, tres pines: `+5V_LED`, `LED_DATA`, `GNDD`. El `GNDD` **vuelve aquí**, y es la referencia contra la que el primer LED mide el nivel del dato.

- [ ] **Step 6: Correr el script.** Guardias verdes. Commit.

---

### Task 9: `build_schematic.py` — USB, MIDI, pedal, cabeza y puente

**Files:**
- Modify: `hardware/02-midi-cv/kicad-v2/build_schematic.py`

- [ ] **Step 1: USB device.** USB-B → `USB_DP_ISO`/`USB_DM_ISO` → aislador → `USB_DP`/`USB_DM` → micro. La pull-up de `D+` **del lado del instrumento**: con el instrumento apagado y el cable puesto, el host no ve nada — no un dispositivo defectuoso. Lado alto alimentado de `VBUS_DEV`, lado bajo de `+3V3`.

- [ ] **Step 2: USB host.** USB-A, interruptor de carga con `HOST_EN` y `HOST_FAULT` a sus GPIO, `VBUS_HOST` a la patilla de alimentación del conector, y `PIOUSB_DP`/`PIOUSB_DM` con las resistencias del circuito de referencia de Pico-PIO-USB **citadas en el BOM**.

- [ ] **Step 3: MIDI DIN.** Entrada: pines 4 y 5 al LED del optoacoplador con su resistencia limitadora y su diodo de protección, salida del opto a `MIDI_RX`. Salida: `MIDI_TX` → driver → pines 4 y 5, con los pines 2 a masa según manda la especificación. **Los valores, de la variante de 3,3 V de la especificación eléctrica de la MIDI Association**, con documento y página en el BOM.

- [ ] **Step 4: El pedal.** Jack de 6,35 mm, `PEDAL_R` con la referencia, `PEDAL_T` → protección → `PEDAL_ADC`. Y el sesgo que hace que **sin pedal enchufado la entrada lea «no pulsado»** — esto no es una preferencia, es la función de seguridad, y la Task 10 lo asevera.

- [ ] **Step 5: La cabeza local.** El conector de la pantalla de 2,8" con `LCD_SCLK`/`LCD_MOSI`/`LCD_CS`/`LCD_DC`/`LCD_BL`, su `RST` **atado al reset del sistema** (no lleva pin propio, spec §7), la resistencia de serie de la retroiluminación dimensionada al PWM, y el encoder con antirrebote en `ENC_A`/`ENC_B`/`ENC_SW`. **Sin LED de estado y sin driver de dígitos**: los dos se fueron con la pantalla — si el esquemático los trae, viene de una versión vieja del plan.

- [ ] **Step 6: El zócalo del puente**: `BRIDGE_TX`/`RX`/`EN`/`BOOT` y su alimentación de `+3V3`. Sin keepout: el módulo lleva U.FL y la antena sale por un pigtail.

- [ ] **Step 7: Correr el script hasta guardias verdes**, y después el gate de verdad: **ERC a cero**. Cada NC deliberado con su cruz de no-conexión.

- [ ] **Step 8: Generar la netlist.**

```bash
kicad-cli sch export netlist sam17-cerebro.kicad_sch -o sam17-cerebro.net
```

- [ ] **Step 9: Commit.**

---

### Task 10: `check_netlist.py` y `check_bom.py` — lo que el ERC no ve

**Files:**
- Create: `hardware/02-midi-cv/kicad-v2/check_netlist.py`
- Create: `hardware/02-midi-cv/kicad-v2/check_bom.py`

- [ ] **Step 1: `check_netlist.py`** con el parser del módulo 3 y **estas** aserciones, que son las que duelen en meses:

```python
# 1. GND_ISO y GNDD son redes DISTINTAS y ningun pin esta en las dos.
#    Es la asercion mas importante de esta placa: si estan unidas, el
#    aislador no aisla y todo lo demas sigue en verde.
# 2. Los ocho SPI_CS_n tienen pull-up a +3V3. Sin ellos, CS asertado al
#    encender mete relojes espurios en la cadena de DACs del modulo 3.
# 3. GATE_n_3V3 tiene pull-down, y la cadena de dos MOSFET es NO
#    inversora: un gate alto al arrancar abre las cuatro envolventes.
# 4. PEDAL_ADC esta sesgado a "no pulsado" con el jack vacio. Es la
#    funcion de seguridad del diseno; se asevera, no se espera.
# 5. TUNE_OUT_1..4 llegan SOLO a la ranura 1, y en las otras siete esos
#    pines estan sin conectar con su cruz.
# 6. Ninguna red de TUNE_OUT toca un condensador. Nada de filtro: los
#    131 ns de margen no admiten un flanco redondeado.
# 7. Cada I2C_SDA_n/SCL_n sale del canal n del mux y llega al pin 7/8 de
#    la ranura n. La rama 3 con las pull-ups de la 5 "casi funciona".
# 8. MUX_RESET llega al pin de reset del mux y a un GPIO. Sin el, un
#    modulo que trabe SDA se lleva por delante el descubrimiento, la
#    telemetria y la identidad del propio cerebro.
# 9. HOST_EN y HOST_FAULT llegan a GPIO, no a un riel. Con EN atado, el
#    puerto host queda muerto tras un fallo hasta apagar el instrumento.
# 10. La EEPROM y el TMP1075 del cerebro estan en el TRONCO, no en un
#     canal, y el strap del TMP1075 no repite la direccion de los modulos.
```

- [ ] **Step 2: La mutación de la aserción 1.** Unir `GND_ISO` y `GNDD` a mano en el script generador, regenerar, y comprobar que `check_netlist.py` se pone **rojo**. Después revertir. Sin ver morder esa aserción, no se sabe si mira.

- [ ] **Step 3: `check_bom.py`** con el patrón del módulo 3: cada referencia del `.net` está en `bom-v2.csv` y viceversa, y las cantidades cuadran.

- [ ] **Step 4: Congelar la netlist como golden.**

```bash
cp sam17-cerebro.net sam17-cerebro.netgold
```

Y comprobar que el golden **no está vacío de la cadena que importa**: un golden se dio por bueno una vez en este repo y la mutación no falló porque a la cadena de prueba le faltaba un pin.

- [ ] **Step 5: Commit.**

---

### Task 11: El render del esquemático, mirado por un humano

**Files:**
- Create: `hardware/02-midi-cv/schematics-v2/sam17-cerebro.pdf`, `.svg`

- [ ] **Step 1: Exportar.**

```bash
kicad-cli sch export pdf sam17-cerebro.kicad_sch -o ../schematics-v2/sam17-cerebro.pdf
kicad-cli sch export svg sam17-cerebro.kicad_sch -o ../schematics-v2/
```

- [ ] **Step 2: Mirarlo.** Esto es una puerta, no un trámite: hay una clase de defecto que ninguna medida numérica ve. Que la barrera del aislador se lea como barrera, que las ocho ranuras se lean como ocho iguales, y que los NC deliberados tengan su cruz visible.

- [ ] **Step 3: Que lo apruebe Samuel** antes de tocar el PCB.

- [ ] **Step 4: Commit de los renders.** Un gate cuyo resultado no queda en el repositorio no se puede volver a revisar.

---

### Task 12: `build_pcb.py` — contorno, colocación y las tres fronteras

**Files:**
- Create: `hardware/02-midi-cv/kicad-v2/build_pcb.py`

- [ ] **Step 1: Contorno y capas.** Ancho de `panel_budget.py`, alto del panel Eurorack 3U, cuatro capas con plano de `GNDD` entero.

- [ ] **Step 2: Colocación de los conectores de panel** en su fila, con las cotas que salieron de `panel_budget.py`. Los jacks soldados a la placa: sus posiciones son las del panel, no al revés.

- [ ] **Step 3: Las tres fronteras del cobre**, que son las que deciden si esta placa funciona:

```
1. La barrera del aislador: hueco despejado en las CUATRO capas.
2. La isla de potencia del +5V_LED en el canto, sin cruzar el plano
   que sostiene el SPI.
3. El retorno de los gates, que conmutan 10 V hacia otro modulo.
```

- [ ] **Step 4: Los ocho IDC 2×6 en el canto interior**, alcanzables con el instrumento montado — 96 pines de cabecera que alguien va a enchufar y desenchufar con las manos.

- [ ] **Step 5: Correr `check_placement_clearance` y `revisar_taladros`** — vía dentro del agujero de un jack es mecánica, y el DRC no la ve.

- [ ] **Step 6: Commit.**

---

### Task 13: `build_pcb.py` — ruteo, `check_aislamiento.py` y DRC

**Files:**
- Modify: `hardware/02-midi-cv/kicad-v2/build_pcb.py`
- Create: `hardware/02-midi-cv/kicad-v2/check_aislamiento.py`

- [ ] **Step 1: Rutear por rondas, y que cada ronda registre una medida** — incluidas las negativas. Un callejón sin salida commiteado con su medida es lo que impide volver a entrar en él. Si una ronda queda a medias, el commit lo dice (`BLOCKED en el paso N`), no lo disimula.

- [ ] **Step 2: `check_aislamiento.py`.** Mide el hueco real en **cada capa** a lo largo de toda la barrera del aislador, sobre la placa ya ruteada. El DRC no ve esto: es geometría, no electricidad.

- [ ] **Step 3: La mutación.** Acercar el plano al otro lado de la barrera y comprobar que **falla**. Sin esto, la decisión del aislador es decorativa y no hay forma de saberlo hasta que zumbe.

- [ ] **Step 4: Contar las islas del relleno real** de `GNDD`: más del 99 % en una. Un plano partido pasa el DRC en verde.

- [ ] **Step 5: DRC.** Cero infracciones y **cero sin conectar**. Y si el ruteo no cierra, se deja sin cerrar y se dice — ninguna regla de separación se afloja para que quepa.

- [ ] **Step 6: Commit.**

---

### Task 14: Los renders 3D, y el ojo como puerta

**Files:**
- Create: `hardware/02-midi-cv/pcb-v2/sam17-cerebro-3d-top.png`, `-3d-iso.png`, `-top.svg`, `-bottom.svg`

- [ ] **Step 1: Exportar vista 2D y render 3D.**

- [ ] **Step 2: Mirarlos.** Lo que se busca es lo que ninguna medida ve: un cuerpo montado sobre una ranura, un conector que choca con otro, un jack que no llega al panel. Los pads pueden estar perfectos y el DRC en cero.

- [ ] **Step 3: Que lo apruebe Samuel.**

- [ ] **Step 4: Commit de los renders.**

---

### Task 15: Fabricación

**Files:**
- Create: `hardware/02-midi-cv/pcb-v2/` (gerbers, drill, CPL, BOM de ensamblaje)

- [ ] **Step 1: Exportar** gerbers, taladros, posiciones y BOM de ensamblaje con el patrón de `hardware/03-vco/kicad/{bom_jlc,cpl_jlc}.py`.

- [ ] **Step 2: Probarlos contra el flujo REAL del fabricante**, no contra su documentación: el formato de CPL que su web acepta, y qué piezas rechaza su flujo de montaje por falta de stock.

- [ ] **Step 3: Re-verificar el stock fila por fila el día de mandar.** El matcher automático del fabricante metió cinco errores en seis filas la última vez: X7R por C0G, 220k por 20k, 0402 por 0805.

- [ ] **Step 4: Desactivar la auto-confirmación del fabricante.** Una puerta que se abre sola no es una puerta.

- [ ] **Step 5: Commit.** **El botón de pagar lo aprieta Samuel, siempre.**

---

### Task 16: Bring-up, docs y PR

**Files:**
- Create: `hardware/02-midi-cv/notes/bring-up-v2.md`
- Modify: `docs/modules/02-midi-cv.md`
- Modify: `hardware/02-midi-cv/README.md`
- Modify: `case/clearance_budget.py` (si el issue #152 no aterrizó antes)

- [ ] **Step 1: `bring-up-v2.md`**, en orden y con criterio de éxito por paso, más el bodge previsto si falla. Los que esta placa hereda con nombre y apellido:

```
- Jitter del 74HC14 contra los 131 ns (issue #80). Aprobado o suspenso.
- clk_sys real con el host USB activo, contra F_PIO (issue #150).
- MISO del modulo 3 con CS alto Y DCEN encendido. El unico modulo que
  hoy puede desmentir el contrato del enlace.
- Corriente de back-drive por cada linea del J2 con el modulo 3
  enchufado y SIN su +12.
- El zumbido por USB con y sin el aislador, que es el dato que dice si
  la decision valio la pena.
- Los 2,50 A del #104 medidos de verdad por el sensor nuevo.
- Que el host no vea un dispositivo defectuoso con el instrumento
  apagado y el cable puesto.
```

- [ ] **Step 2: Reescribir `docs/modules/02-midi-cv.md`**, que sigue describiendo el Raspberry Pi, el LCD 16×2 y los tres CV por AD5686R. Cierra el issue **#111**.

- [ ] **Step 3: Actualizar `hardware/02-midi-cv/README.md`** para que apunte a la v2 y diga **en voz alta lo que todavía no está medido**.

- [ ] **Step 4: Correr los gates completos.**

```bash
python hardware/tools/gates.py
```

Expected: todo verde, y los `HUECO` **con su motivo escrito** y contados en el resumen. Un `skip` silencioso consigue no correr y que no te enteres, las dos cosas a la vez.

- [ ] **Step 5: PR, merge, e issues de lo aplazado.** Con evidencia: el número que falta, cómo medirlo, y el criterio de cierre.

---

## Notas de consistencia

- **La tabla maestra de redes es la única fuente de nombres.** Las tareas la referencian; ninguna inventa un nombre nuevo.
- **`pinout.rs` es la única fuente de pines.** Ningún GPIO se escribe a mano en `build_schematic.py`.
- **Ninguna tarea avanza con la anterior en ámbar.** Las fases y sus puertas están en la skill `disenando-placas`.
- **Las tareas 1 y 2 son bloqueantes de verdad**: sin las piezas verificadas y sin el `+5V` resuelto (issue #151), lo que se dibuje después hay que rehacerlo.
- **Lo que este plan NO hace:** la PCB del panel y la mecánica de los jacks (van con el case), el firmware de aplicación (specs 2, 3 y 4 — issues #94, #95, #91), y los siete issues del contrato de software (#143 a #149), de los cuales el **#143** —la confirmación física sin cablear— bloquea el paso del pedal en el bring-up.
- **Y una decisión de firmware que esta placa provoca y no resuelve:** §4 de la spec exige que el instrumento **diga** que el VCO está en una ranura sin camino de afinado, y por §2.1 del núcleo eso tiene que salir por un mensaje del protocolo —un parámetro de medida o un `ERROR`—, no por una línea del bring-up. Elegir cuál y escribirlo en la tabla de §4.1 del núcleo es trabajo de la spec del núcleo, no de este plan. Si al llegar al Step 1 de la Task 16 sigue sin decidirse, se abre issue en vez de dejarlo como intención.
