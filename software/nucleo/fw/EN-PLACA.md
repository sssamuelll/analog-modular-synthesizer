# La lista del bring-up

Esto se escribió **sin placa**. Todo lo que hay en `core` está probado con
`cargo test`, y el binario compila y enlaza para `thumbv8m.main-none-eabihf`
—el target del Cortex-M55 del N657, el mismo que traía el RP2350— pero eso no
demuestra que arranque, ni que enumere, ni que conteste.

Esta es la lista del día que llegue la placa, **en orden**: cada línea supone
que la anterior salió bien.

> **Estado al 2026-10-01: la Nucleo está en el banco y los pasos 1 y 2 salieron**
> —arranca y Windows la enumera como «SAM17 nucleo» a alta velocidad—. Hicieron
> falta cinco cosas que esta lista no sabía; están en §«El primer día en
> placa», al final, y las correcciones van en su sitio abajo. Los pasos 3 a 6
> esperan un cliente MIDI del lado del PC, que el repo todavía no tiene.

## Antes de enchufar nada

**Cuál placa.** La **NUCLEO-N657X0-Q**, firmada en el acta del J2 del
2026-09-11 (#231): el mismo STM32N657X0H3Q en VFBGA264 que eligió el censo,
a un tercio del precio de la Discovery, y con los dos extremos del J2 en un
solo conector (§«El J2 en la Nucleo», abajo). La STM32N6570-DK entra el día
que haya fecha de pedido de PCB con N657 a menos de ocho semanas, por la
pantalla de 800×480 en el LTDC, la PSRAM y la cámara.

**Comprobar `memory.x` contra la placa.** El N657 **no tiene flash interna**:
`FLASH` y `RAM` son dos tramos de la misma AXISRAM2 y el binario lo carga ahí
el depurador, con la placa en *development boot* (BOOT1 = 1: en la Nucleo,
**el puente JP2 movido** de su [1-2] de fábrica, UM3417 Rev 3 Tabla 4, p. 8 y
§7.13, p. 26; «BOOT1 arriba» es el interruptor de la DK). El arranque
de verdad —FSBL y binario con cabecera desde la XSPI— es el riesgo 2 del papel
del hub y está en `ARRANQUE.md`: existe en Rust (lo trae embassy), compila en
esta máquina y **no está probado en placa**. Enlazar aquí no demuestra que
arranque de la flash.

**Comprobar de dónde sale el núcleo.** `usb::configuracion()` pone
`SupplyConfig::External` porque la DK lleva SMPS externo; con el interno el
`init` se queda colgado en `VOSRDY`. **La placa del SAM17 lleva el conmutado
interno** (papel de alimentación del N657), así que esa línea se borra el día
que exista placa propia. Si el arranque se cuelga sin decir nada, éste es el
sospechoso número uno.

**En la Nucleo, `External` también es lo correcto.** Llega en configuración
de SMPS externo por defecto (UM3417 Rev 3 §7.4.3, p. 20: *«External SMPS
default configuration»*); los puentes de soldadura para pasar al SMPS interno
están en esa misma sección y **no se tocan en el bring-up**. Medir la corriente
del SMPS interno (#256) pediría moverlos; se aparca.

**Comprobar el pinout.** `core/src/pinout.rs` es una **propuesta**: los números
salieron de agrupar por periférico, no de ninguna placa. Cuando haya una, ese
es el único fichero que cambia — para eso está aislado y para eso tiene tests
que impiden repetir un pin o pedir uno que no existe.

## 1. Arranca

```bash
cargo run --release --bin sam17-nucleo-fw   # probe-rs con el STLINK-V3EC (CN10)
```

El `--bin` hace falta desde que existen los cuatro binarios del J2: sin él
`cargo` no sabe cuál cargar.

**JP2 movido antes de nada.** Con BOOT1 abajo la ROM se va a flash boot o a
serial boot y `probe-rs` no encuentra a nadie escuchando. En development boot
el LED rojo LD5 (PG10) se queda fijo (AN5967 §11.2); en la Nucleo, el 01-10,
fijo y sin cambiar al pulsar B2. `ARRANQUE.md` tiene los tres caminos con su
página.

**`--release` no es una preferencia: es la unica que enlaza.** Con
`defmt` y embassy, el binario de depuracion se pasa **48 KB** de los 256 K que
`memory.x` reserva para el codigo, y `rust-lld` lo dice con tres secciones que
se solapan. Si hace falta depurar sin optimizar, se sube `FLASH` en
`memory.x` — pero entonces se come lo que queda abajo, que son **640 KiB**
y no los 768 KB que dice el comentario heredado de embassy. Ojo con lo que
eso arrastra: el framebuffer de 800x480 RGB565 son 750 KiB y **ya no cabe
ahi hoy**, se toque o no `FLASH`. Es del #296.

Por `defmt` tiene que salir (lo que salió el 2026-10-01; cuando se escribió
esta lista eran protocolo v1, 39 pines y 27 parámetros):

```
SAM17: el cerebro arranco, protocolo v2
46 pines en el mapa
HUECO: tabla de partes provisional declarada: 1 parte, 4 voces; la sustituye EEPROM #175
sin descubrimiento todavia: 42 parametros, todos de medida
USB: un cliente se conecto            ← cuando el PC abre el puerto MIDI
```

Las dos primeras pueden no verse: con `DEFMT_LOG=debug` las 46 líneas de
pines llenan el búfer RTT de 1 KB antes de que probe-rs se enganche.
`DEFMT_RTT_BUFFER_SIZE=16384` al compilar las conserva.

**Si no sale nada**, en orden: la configuración de alimentación (arriba), y
después el reloj de referencia del PHY de USB, que tiene que ser 24 MHz
exactos y sale del **cristal HSE ÷ 2** (`usb::configuracion()`, con su
página; con HSI → PLL4 → IC15 el PHY no se presenta, medido el 01-10).
Enlazar no es arrancar.

**Si se cuelga, se corta la corriente, no se pulsa B2.** Tras un cuelgue del
bus el depurador vuelve con NRST, pero cualquier firmware muere a ~0,9 s
hasta que se desconecta CN10 unos segundos (ES0620 Rev 5 §2.2.18, *«might
require a full power cycle»*; medido el 01-10: el mismo binario murió a
0,85 s antes del corte y corrió 60 s después).

## 2. Enumera

El sistema operativo lo ve como dispositivo MIDI con nombre **SAM17 nucleo**,
VID `0x1209` y PID `0x0017`. **Hecho el 2026-10-01** en Windows 11: dispositivo
compuesto USB, clase MEDIA y endpoint MIDI, todos `OK`, a alta velocidad.

Dos condiciones de banco. El cable de **CN8** tiene que pasar datos: el
primero que se probó unía D+ y D− (estado SE1 en `GCCFG`, de puerto o cable de
carga) y Windows no veía nada. Y el firmware tiene que bajar `PRIMASK`, que
probe-rs deja en 1 (§«El primer día en placa»): sin eso el PC resetea el bus,
el driver no se entera y Windows dice *«Error de solicitud de descriptor de
dispositivo»*.

## 3. `HELLO` da la vuelta

**Este es el momento en que el instrumento contesta de verdad por primera vez.**
Manda el SysEx de `HELLO` y espera `HOLA` con la versión que imprime la línea
de arranque (2 el 2026-10-01).

El sobre es `F0 7D <datos empaquetados a 7 bits> F7`, y el mensaje son la
etiqueta `0x01` más la versión en `u16` little-endian. El troceo en paquetes
de 4 bytes lo hace el driver MIDI del sistema.

## 4. `DESCRIBE` vuelve entero

Tiene que llegar **un sobre por parámetro**, tantos como dice la línea de
arranque: 42 el 2026-10-01. Cuando se escribió esto eran 27, las 24 bandas de
Bark, el pico, su exceso y la sonoridad. Con sus nombres y sus unidades.

Si llegan menos, sospecha del troceo largo antes que del servidor: decenas de
sobres seguidos es lo primero que ejercita el buffer de verdad.

## 5. Un `SET` sobre una medida contesta `ERROR`

Manda `SET` a cualquier banda. Tiene que volver
`ERROR { etiqueta: 0x04, codigo: SoloLectura }`.

**Este es el test del hallazgo**: antes de añadir `ERROR` a la tabla, esto
dejaba al cliente esperando en silencio para siempre.

## 6. `SUBSCRIBE` y luego un `SET` que sí valga

Con `SUBSCRIBE` activo, un `SET` correcto tiene que devolver su `CHANGED`.
Sin `SUBSCRIBE`, **no** devuelve nada, y eso es a propósito: si no, girar una
perilla dispararía cientos de acks por segundo.

## El tiempo musical, cuando haya reloj que enchufar

**Umbrales del CLOCK IN.** `tiempo_budget.py` despeja **993 µs** de holgura
para detectar el flanco. Es muchísimo, así que lo raro sería fallarlo — pero
hay que medirlo, no suponerlo.

**Niveles del CLOCK OUT.** TTL, 0 V / ~+5 V (§5.3 del núcleo).

**MIDI clock por USB de verdad.** El seguidor está probado contra ±2 ms de
jitter inyectado; falta ver cuánto tiembla el transporte real.

**Link sobre el puente**, que necesita que el puente exista y esté elegido. Y
cuando toque: **no escribir el protocolo desde cero** — existe
`ableton-link-rs`, y hay precedente de la topología exacta (Link en un ESP32
pasándole la sesión a un RP2350 por SPI).

## Lo que queda anotado para más adelante

**VID/PID de verdad.** `0x1209` es pid.codes, el rango libre para proyectos
abiertos, y `0x0017` es un PID de pruebas que nadie asignó. Registrar uno es
del día que esto se distribuya.

**Todo lo demás de #86** — I²C, J2, el jitter del 74HC14 contra los 131 ns
(que en el N657 mide captura de TIM, no PIO), DIN, clock/reset, pedal, USB
host — va en los planes 2 y 3. Ese issue está escrito contra el RP2350 y hay
que reescribirlo contra esta placa.

## El J2 en la Nucleo: el montaje, con sus pines

*(Sección del 2026-09-11. La placa firmada en el acta del J2 es la
**NUCLEO-N657X0-Q**, no la Discovery: mismo STM32N657X0H3Q en VFBGA264 y tres
veces más barata. La Discovery entra el día que haya fecha de pedido de PCB con
N657 a menos de ocho semanas, por la pantalla, la PSRAM y la cámara.)*

**Los dos extremos del J2 caben en una sola placa**, y el maestro cae en una de
las instancias que se cuelgan en el hilo. Sale de cruzar el morpho soldado de
fábrica (UM3417 Rev 3, Tabla 13: CN3 y CN15; **CN2 y CN16 no vienen soldados**,
§8.2) contra las funciones alternas de SPI1-6 (DS14791 Rev 10, Tabla 18):

| Señal | Maestro: **SPI5** | CN15 | Esclavo: **SPI4** | CN15 |
|---|---|---|---|---|
| SCK | PE15 | 11 | PE2 | 30 |
| MOSI | PG2 | 15 | PE14 | 26 |
| MISO | PG1 | 13 | PE13 | 28 |
| NSS | PA3 | 17 | PE11 | 23 |

Cuatro hilos de una fila a la otra del **mismo conector**. Los ocho pines llevan
la nota (1) de la Tabla 18 —*«Power supply is VDD»* (DS14791 p. 112)— y
estructura `TT`, así que van al mismo dominio y el cable es directo, sin
traslación de nivel. SPI5 alternativamente sale al Arduino (D13, D11, D12, D10);
SPI4 tiene PE12 (CN15 pin 1) como SCK alternativo a PE2.

**El maestro va en SPI5 a propósito:** es la instancia del repro original de
jake-taf, que después confirmó el cuelgue también en SPI1 (2026-09-03).

**SPI1 no se puede usar en esta placa.** Su único MOSI en el morpho es PC3, que
la Nucleo cablea a `STLK_UCPD_CC1_C` del ST-LINK (UM3417 Tabla 16), y la Tabla
19 de puentes no ofrece forma de liberarlo: clocar ahí sería clocar sobre las
líneas CC del USB-C del depurador. SPI2, SPI3 y SPI6 quedan incompletas en el
morpho (a SPI2 le falta el SCK, a SPI3 el MISO, a SPI6 el MOSI y el NSS).

**Con esclavo real, el soak deja de ser media medida.** Un enlace contra el MISO
al aire mide `plazos_vencidos` y nada más; contra un esclavo que cuenta bytes en
el flanco de `CS` se puede probar además la línea del #292 (`SPE = 0 → SPE = 1`
al contar corto) y ver si la trama siguiente se acepta, que es el riesgo 3 del
papel del maestro.

**Un aviso del propio manual:** §7.5 dice que el LED verde LD3 va a «PB15
(ARDUINO D13)», la Tabla 12 da D13 = PE15 y la Tabla 16 da PB15 = `STLK_USB_P`.
Las tres no pueden ser ciertas. No toca a SPI4 ni a SPI5, pero antes de usar
PB15 o LD3 hay que mirar el esquemático del MB1940.

## Las tres medidas del maestro

*(Cuerpo reescrito el 2026-09-18. Hoy son **cuatro binarios**, escritos y
enlazando; el título se queda como está porque el plan de la fase B y la spec
del maestro apuntan a él por ese nombre. La enmienda del 11-09, al final de la
sección, sigue vigente entera.)*

El papel del maestro del J2 (§9) y el acta del 11-09 le encargan a esta placa un
**orden del día**, no una lista de medidas sueltas: cada una supone que la
anterior salió. Ya no hay nada que decidir el día de la placa —los cuatro
binarios viven en `src/bin/`, compilan y enlazan—, solo que enchufar y leer.

| # | Binario | Qué contesta |
|---|---|---|
| (0) (1) | `control_positivo` | ¿prender el SPI levanta `EOT`? ¿nos pasa a nosotros el cuelgue del #5607? |
| (2) | `barrido_retardo` | ¿la tasa de cuelgue depende del retardo `SPE = 1 → CSTART`? |
| (3) | `resistencia_j2` | la fila del soak: **la puerta de fabricación** |
| (4) | `plazos_j2` | `t_real` contra `t_nominal` en el osciloscopio: `FACTOR_PLAZO` y `T_SUELO_PLAZO` |

**El orden no es negociable**, y la razón es la ficha 3 del acta: un soak verde
no ejecuta D4 y no distingue «no nos afecta» de «el banco no lo ve». El control
positivo va primero porque es el que demuestra que el banco *sabe ver* un
cuelgue.

**Si hay que cambiar un pin o un canal, se cambia en un solo sitio:**
`src/j2_banco.rs`, en `maestro_del_banco` / `esclavo_del_banco` y el
`bind_interrupts!` `IrqsBanco`. Ahí los pines van como **tipos concretos**
(`Peri<'static, peripherals::PE15>`), así que un pin equivocado no compila —antes
sí compilaba: los límites del driver aceptan varios pines por señal y PG2 y PG1
son intercambiables por tipo—. Los binarios solo piden la ranura y el esclavo.

### (0) y (1) `control_positivo`

```bash
cargo run --release --bin control_positivo
```

Imprime, en este orden:

```
experimento_0,eot_al_encender=<0|1>
experimento_0,eot_al_encender_maestro=<0|1>
control_positivo: firmware <rev>, f_ker <Hz>, MBR /<n>, f_sck <Hz> (pedido 100000), retardo: ninguno ..., f_cpu <Hz>
control_positivo,minutos=M,lecturas=N,cuelgues=K          ← cada 60 s
```

**`firmware <rev>` sale en la línea de arranque de los cuatro**, y es la revisión
de git con la que se compiló: `<sha corto>`, o `<sha corto>-sucio` si el árbol
tenía cambios sin commitear, o `sin-git` si `git` no contestó. Lo pone `build.rs`
en `SAM17_GIT`. **Anótalo con cada medida**: sin él, una fila del CSV o una
captura del osciloscopio no se puede repetir.

Y, cuando lo haya, una línea de error por cuelgue con su segundo y su cuenta.

- **Las dos primeras líneas son el experimento de un acceso** (spec D2, enmienda
  del 11-09): con el SPI5 encendido por RCC y **nada armado**, `SPE = 1` y leer
  `SR.EOT`. Si vuelve **1**, prender *es* un evento `EOT`, y la hipótesis de
  ES0396 §2.14.2 está viva. Se lee dos veces a propósito: la primera con el
  periférico recién reseteado, que está en **esclavo** (`CFG2.MASTER = 0` es su
  valor de reset), y la segunda con `MASTER = 1`, que es el modo del que habla
  D2. Un 0 en la primera y un 1 en la segunda no sería una contradicción: sería
  el dato.
  **Medido el 2026-10-01** (firmware `259bc91`, y antes el mismo código sin
  commitear): `0` y `0`.
  Prender no levanta `EOT`; según la spec del maestro («Estado de la
  evidencia», bajo D2), D2 ya cubría este caso. Lo que dice si la tasa de
  cuelgue depende del retardo es el barrido, punto (2).
- **(1) es la configuración de jake-taf, no su bucle**: embassy sin driver propio, 100 kHz,
  modo 0, `CS` por GPIO en PA3, `TSIZE = 0` y `blocking_read` de 8 bytes en
  bucle. Una hora da 98 % de potencia contra el extremo suave del hilo (un
  cuelgue cada ~900 s).
  **Medido el 2026-10-01** (firmware `ca07f94`): 64 min, 6 643 199 lecturas,
  **0 cuelgues**, 103 800 lecturas en cada minuto. **No dio positivo.** El
  98 % está calculado contra los 900 s del primer reporte del hilo; jake-taf
  dio después 30-120 min con builds más nuevos, y contra eso una hora no
  contesta (hacen falta unas 6 h). El repro tampoco fue tal cual: lectura de
  8 bytes contra `write` de 2 + `read` de 1, y un driver de embassy más nuevo.
  La lectura entera está en la spec del maestro, §9, enmienda del 11-09,
  punto 3.
  **Decidido el mismo día** (las tres cosas): (A) el mismo binario, 6 h, **hecha**;
  (B) el bucle del primer reporte, 6 h, **hecha el 02-10**; (C) preguntarle a
  jake-taf en #5607 ([hecho](https://github.com/embassy-rs/embassy/issues/5607#issuecomment-5931298173), él respondió que repite con su embassy
  actual y avisa). B es:

  ```bash
  cargo run --release --bin control_positivo --features bucle-del-reporte
  ```

  Bajo `CS`, `write` de `[0x03, 0x2c]` y `read` de 1 byte, como el reporte; la
  línea de arranque termina en `bucle: reporte (...)` y `lecturas` cuenta
  vueltas. Arma el periférico dos veces por cada 3 bytes, contra una por cada
  8. Las dos `info!` por vuelta del reporte no están: serían del orden de 10^8
  líneas en 6 h.

  **A, medida el 2026-10-01** (firmware `4d2d6f2`): 358 min, 37 160 399
  lecturas, **0 cuelgues**, 103 800 lecturas en cada minuto. Un cuelgue cada
  2 h o menos queda descartado al 95 % en esta configuración; no dice que el
  defecto no exista. Faltan las filas 359 y 360 del log por el reloj lento de
  la placa (ver más abajo). Las cuentas, en la spec del maestro, §9, enmienda
  del 11-09, punto 3.

  **B, medida el 2026-10-02** (firmware `7a01671`): 358 min, 78 174 777
  vueltas, **0 cuelgues**.

  **El eco** se decidió el 02-10, después de que jake-taf reportara que con
  `main` se le sigue colgando y que ve errores de CRC «regularmente». Lleva un
  puente de **D12 a D11** en la tira de enchufes CN14: son el 6.º y el 7.º
  desde arriba (ojo: el 4.º y el 5.º son GND y D13, el reloj del SPI). También
  sirve de CN15 pin 13 a CN15 pin 15 (UM3417 Rev 3, Tablas 12 y 13). Se corre
  con:

  ```bash
  cargo run --release --bin control_positivo --features eco
  ```

  Pide 16 MHz y manda 8 bytes de prueba; si no vuelven iguales, se para con
  `panic!`, porque sin puente no hay medida. Después hace `blocking_transfer`
  de 8 bytes con un patrón distinto por vuelta. La fila de cada minuto suma
  `corrupciones` (el driver dijo `Ok` y los datos no coinciden) y `errores`
  (el driver dijo `Err`). **Medido el 2026-10-03 y 04** (firmware `fea2a17`):
  una hora más una noche de 798 minutos, 812 millones de vueltas, **0
  corrupciones, 0 errores y 0 cuelgues**. Las cuentas, en la spec del maestro.

  **El reloj de la placa va lento.** En las cuatro corridas, la última fila
  de cada log se escribe más tarde de lo que dice su minuto: 358 minutos de
  placa son 361 reales. El HSI de esta Nucleo va entre un 0,82 % y un 0,85 %
  lento contra el reloj de la PC, dentro de los ±5 % de la hoja (DS14791 Rev
  10, p. 165). Por eso «faltan» filas al final de cada log: no se pierden,
  simplemente no llegan a imprimirse antes del corte.
- **Pero el `f_sck` no van a ser 100 kHz, y la tercera línea lo dice.** El
  kernel del SPI5 **no es el HSI de 64 MHz**: es `pclk2`, y son **32 MHz**. El
  mux se queda en su cero (`ClockMux::default()` es `mem::zeroed()`,
  `_generated.rs:5317-5319`, e `init()` escribe `set_spi5sel` incondicionalmente,
  `:5397`), y ese cero es `Spisel45::Pclk2` (metapac `rcc_n6.rs:43346-43348`);
  `pclk2` es `sys / hpre / ppre2` (embassy `rcc/n6.rs:462`, publicado en `:1413`)
  y con los defectos que `usb::configuracion()` no toca —`sys: Hsi`, `ahb: Div2`,
  `apb2: Div1` (`:196`, `:225`, `:227`)— eso es 64 / 2 / 1 = 32. Con eso,
  `compute_baud_rate` reparte por tramos y la razón 320 cae en el último, `/256`
  → **125 kHz**, que es el divisor más grande que hay. No invalida el repro —la
  condición de la errata es «system clock much faster than SCK» y 125 kHz está
  aún más lejos del núcleo que los 100 kHz de jake-taf— pero la tasa que se mida
  **no es comparable byte a byte** con la suya. Anótalo con la medida.
- **El bucle vive en el ejecutor de hilo y el vigía en el del J2.** El
  `blocking_read` colgado no vuelve nunca; un vigía en su mismo ejecutor se
  colgaría con él. El vigía mira cada 100 ms; tres tics sin avanzar son un
  cuelgue.
- **El paliativo del `TXDR` está en este binario y en ningún otro.** R-MJ3 lo
  prohíbe en el driver; aquí *es* la medida, porque es lo que jake-taf usa para
  desatascar su repro (`SPI1.txdr8().write_value(0)`, enmienda del 08-09 a D4).
- **El MISO (PG1) va al aire y el esclavo no se arranca.** Lo que se mide es el
  maestro.

### (2) `barrido_retardo`

```bash
cargo run --release --bin barrido_retardo
```

Seis puntos, `retardo_tsck_cuartos` ∈ {0, 1, 2, 4, 8, 16} = {0, ¼, ½, 1, 2, 4} ×
T_SCK, **45 min cada uno**: la cota del acta, p < 4,2e-7 al 95 % para la tasa
por armado, a la cadencia real del banco (~2,6 kHz, #428; el acta contaba 15 min
a 8 kHz). Tramas de 25 bytes, al piso de 10 MHz, con el esclavo activo. Por
punto:

```
barrido,retardo_cuartos=R,armados=A,plazos_vencidos=P,eot_tardios=E,subidas_malas=S,escaladas=X,tramas_cortas=C
```

`armados` son transferencias **armadas**, no terminadas: sube una por vuelta del
lazo, pase lo que pase, y `armados = ok + plazos_vencidos`. **No es el `giros` de
`core`** (D7.3), que mide «mi periférico terminó» y no cuenta las que vencen
plazo; por eso se llama distinto. `escaladas` son solo las del **maestro**
(`ESCALADAS_GPDMA − REARMES_ESCALADOS`: `soltar_canales` la llaman los dos
extremos). `escaladas` y `tramas_cortas` son **deltas del punto**, no totales,
para que los seis se comparen entre sí. Al terminar los seis se queda en 4 —el de
producción— para siempre, publicando un punto más cada 45 min.

**La lectura, dicha, porque el acta no la fija.** El acta dice «en esa
configuración» apuntando al punto (1), el de `TSIZE = 0`. Este binario corre
sobre la **configuración con `EOT`** —el driver propio, `TSIZE > 0`, NSS por
hardware— y la razón es el propio texto de la errata: su tercer workaround es
*«Prevent EOT events from occurring, by setting transfer size to undefined
(TSIZE = 0)»*, o sea que con `TSIZE = 0` **no hay eventos `EOT`**, y el mecanismo
de §2.14.2 es *«stall upon setting the CSTART bit within one SCK cycle after the
EOT event»*. Un retardo medido desde un evento que no ocurre no barre nada.

**Una tasa que dependa del retardo es la firma de la errata; una que no, no lo
es.** Y el maestro de este binario corre en el ejecutor de **hilo**, no por
`j2_ejecutor::arrancar`: hay que cambiarle el retardo entre punto y punto y
`arrancar` se lleva la `Ranura`. No vigila salud ni cuenta con la política de
`core`: es un experimento de transporte. El esclavo sí va en el `EJECUTOR_J2`.

**Primer intento, el 2026-10-14: medida inválida.** El primer punto dio
`armados=2132419, plazos_vencidos=2132418` y ceros en lo demás: vencieron plazo
todos los giros menos el primero. Eran dos defectos del driver, no el silicio:
`TXTF` sin limpiar entre transferencias (el GPDMA no pedía datos) y el reinicio
de D4 con `CSUSP`, que dejaba el SPI sin poder arrancar. Los dos están
arreglados (spec del maestro, enmiendas del 14-10 en D2 y D4), y 20 000 giros
seguidos salen bien.

**La cadencia real del banco es de unos 2,6 kHz, no 8.** Cada giro tarda unos
335 µs con el reloj de hoy (HSI a 64 MHz, sin cachés), así que en 15 minutos
salen unos 2,4 millones de armados y la cota por punto es p < 1,3e-6 al 95 %,
no 4,2e-7. Para la potencia del acta hacen falta 45 minutos por punto, y así
quedó el 2026-10-14.

### (3) `resistencia_j2` — la puerta de fabricación

```bash
cargo run --release --bin resistencia_j2
```

El montaje entero y tal como lo usará el instrumento: ranura 0 en SPI5 dentro
del `EJECUTOR_J2` con la política de `core` detrás, esclavo del banco en SPI4
como tarea del mismo ejecutor, retardo de producción (4 cuartos). Cada hora,
cuatro líneas:

```
firmware=<rev>
0,SPI5,25,hw,<reloj_MHz>,<horas>,<giros>,<plazos_vencidos>,<eot_tardios>,<subidas_malas>,,NUCLEO-N657X0-Q
esclavo,tramas_ok=,tramas_cortas=,rearmes_escalados=
maestro,escaladas_gpdma=,inestable=,muda=
```

**Y una tanda entera con `horas=0` nada más arrancar**, antes de la primera hora.
No es una medida —todo está a cero— y por eso lleva su hora puesta: sirve para
ver el formato delante de quien va a copiar filas durante 24 h, en vez de
descubrir a la hora que una columna baila.

`firmware=` va **fuera** de las doce columnas a propósito: la cabecera de
`resistencia_j2.csv` es de R-MJ8 y no se toca. Va delante de su fila, y hay que
anotarlo junto a ella —las dos tandas, al piso y al peldaño 2, son binarios
distintos.

La segunda línea son las doce columnas de `resistencia_j2.csv` en el orden de
R-MJ8, y se copia tal cual al CSV: `fecha` va vacía —las dos comas seguidas—
porque la pone quien copia. `reloj_MHz` lleva el **real**, el que sale del `MBR`,
no el pedido: con 10 MHz pedidos y el kernel del SPI5 en `pclk2` a 32 MHz son
**8** (`/4`).

**HUECO declarado (#380): la segunda tanda no va a medir 34,5 MHz.** Con el
kernel de hoy, 32 MHz, y el `MBR` más pequeño, `/2`, el techo del enlace es
**16 MHz**: pedir 34,5 devuelve 16. Para clavar 34,5 haría falta un kernel de
69 MHz —o 138, o 276: solo 69 × 2^k lo da exacto—, y eso es elegir otra fuente
del mux, que se decide en el #380. Hasta entonces la segunda tanda cambia
`F_SCK_HZ` en el binario y mide **16 MHz**; la columna `reloj_MHz` lo dice sola,
pero quien lea la fila tiene que saber que ese 16 **no es el peldaño 2**.

**Cómo se juzga la fila, que no es «tiene fila».** Ficha 1 del acta: ninguna PCB
con N657 sale al taller sin una fila medida. Ficha 2: el límite es **cero
artefactos audibles** atribuibles al bus, y para ser medible necesita un
**horizonte** —cero en cuántas horas de instrumento— que sigue siendo **HUECO de
Samuel**. Con cero eventos en `T` horas la tasa queda por debajo de `3/T` al
95 % (regla de tres, Poisson), así que «cero en H horas» pide del orden de
`3·H` horas limpias **con el control positivo ya hecho**.

### (4) `plazos_j2` — el osciloscopio

```bash
cargo run --release --bin plazos_j2
```

Por cada mensaje de la cabecera §4 (`j2_banco::LARGOS_MENSAJES`), mil giros de su
largo con un testigo que sube justo antes de `giro` y baja al volver, y medio
segundo de silencio entre ráfagas para que los ocho grupos se distingan. Antes de
cada ráfaga:

```
plazos,mensaje=<nombre>,tsize=<N>,t_nominal_us=<N×8/f_sck>,plazo_us=<el de core>
```

En la pantalla, el ancho del pulso es `t_real`. `FACTOR_PLAZO` se fija con **≥ 3×
el peor exceso** (`t_real / t_nominal`) y `T_SUELO_PLAZO` con el retraso de ISR
que se vea en `HOLA`, que es el mensaje donde el término nominal casi no pesa.
Los dos se cambian en **un solo sitio**, `Umbrales::POR_DEFECTO` de
`core/src/maestro_j2.rs` (R-MJ4). El binario no copia ninguno: hasta el
`t_nominal` que imprime sale de despejar `plazo_us`, para no tener dos cuentas de
lo mismo.

**El pin del testigo: PE7, CN15 pin 22.** UM3417 Rev 3, Tabla 13, p. 32. Se
eligió porque es —junto a PE1— el único del CN15 que **no aparece en ninguna otra
tabla del manual**: no está en el mapa Arduino (Tabla 12, p. 30), no es ninguno
de los ocho del J2, no es PE10 (el plan B de abajo), no es PE12 (el SCK
alternativo de SPI4) y no toca nada del bring-up —LED LD5 PG10, LD6 PG0, LD7 PG8,
LD3 PB15; botón B1 PC13; ST-LINK PB14/PB15 y PC3/PC4 (§7.5, §7.6 y Tabla 16)—.

**El esclavo va apagado en esta medida, y el MISO al aire.** El esclavo del banco
compara contra un `esperado` fijo de 25 bytes, así que los siete largos que no
son 25 —`HOLA` con 9, `SET` con 103— le contarían tramas cortas por construcción
y taparían las de verdad. Aquí se mide el maestro.

### Antes de dar por bueno cualquiera de los cuatro: que el ejecutor exista

El `#[interrupt] unsafe fn GFXTIM()` que bombea el `EJECUTOR_J2` vive en la
**biblioteca** (`src/j2_ejecutor.rs`), no en los binarios. Si el enlazador se
quedara con el `DefaultHandler` débil de `cortex-m-rt`, el ejecutor no correría
nunca y las tareas quedarían mudas **en silencio**. Se comprueba sin placa, con
`cargo-binutils`:

```bash
rust-nm -C target/thumbv8m.main-none-eabihf/release/resistencia_j2 \
  | grep -iE "gfxtim|exti11|spi5|gpdma1_channel|DefaultHandler"
```

`GFXTIM` tiene que salir con **dirección propia**, distinta de la de
`DefaultHandler`. Medido en los cuatro: sale propia, y la entrada del vector
apunta ahí (`rust-objdump -s -j .vector_table`).

**Y `SPI5`, `EXTI11` y `GPDMA1_CHANNEL0..3` también salen propias en los cuatro**,
incluido `control_positivo`, que no usa ninguna de esas ISR: desde R23 el
`bind_interrupts!` vive en la biblioteca (`IrqsBanco`), así que sus manejadores se
enlazan en todo el que use la biblioteca. Es inofensivo —una ISR solo corre si su
línea está desenmascarada— pero hay que saberlo al leer la salida: **el único
negativo esperado es `SPI4`**, que sí cae en `DefaultHandler` porque el esclavo
se despierta por `EXTI11` y por DMA, nunca por la interrupción de SPI4. Ejemplo
real, `control_positivo`:

```
341a1952 T DefaultHandler
341a54d8 T EXTI11
341a5a60 T GFXTIM
341a5522 T GPDMA1_CHANNEL0
341a1952 T SPI4          ← el único que comparte dirección con DefaultHandler
341a555a T SPI5
```

(las direcciones cambian con cada compilación; lo que se mira es **cuáles
coinciden** con la de `DefaultHandler`, no sus valores).

### Las tres causas de trama corta, y cómo se separan

`TRAMAS_CORTAS` del esclavo no dice **por qué** fue corta. Son tres cosas y el
banco tiene que poder distinguirlas; las tres se miran con el analizador lógico
(riesgo 8 del papel del maestro):

| Causa | Firma |
|---|---|
| **El maestro abortó la trama** (lo que el esclavo existe para probar) | sube **a la vez que** `plazos_vencidos` del maestro, giro a giro |
| **El esclavo no llegó a rearmar** (el hueco entre el flanco de `CS` y el `SPE = 1` siguiente, sin cota en ningún papel) | sube **sin** `plazos_vencidos`, y sube en **todas** las tramas, no de vez en cuando |
| **La carrera por el último byte, y es nuestra** (entre el flanco y la lectura de `BNDT` hay ISR, despertar y un poll) | tasa **baja y constante**, sin `plazos_vencidos` y **sin ninguna trama truncada en el cable** |

El umbral no se toca por la tercera: es D8 de la cabecera y es del papel. Lo que
el banco mide es si la carrera se pierde alguna vez.

### El plan B del `CS` del esclavo

El flanco se detecta con **`EXTI11` sobre PE11 con el pin en AF5**, que el RM
sostiene (§15.3.11, p. 789: en función alterna *«the Schmitt trigger input is
activated»*). **Si en la placa el flanco no dispara**, el plan B es un **quinto
hilo** del NSS del maestro —PA3, CN15 pin 17— a **PE10, CN15 pin 27** (UM3417
Rev 3, Tabla 13, p. 32), con ese pin en `Input` y la línea `EXTI10`. **No está
implementado**: son dos constantes de `src/j2_esclavo.rs` y la línea `EXTI11`
del `bind_interrupts!` `IrqsBanco` de `src/j2_banco.rs`.

### Cuatro cosas que embassy no decide por nosotros

- **La línea del SPI5 en el NVIC no la habilita `embassy_stm32::init`.** Sí
  habilita los dieciséis canales del GPDMA por su cuenta
  (`dma/gpdma/mod.rs:526-534`), pero la del SPI no la toca nadie de embassy. Sin
  `enable()` el `EOT` no llega al núcleo y **todos** los giros vencen plazo —un
  banco entero en rojo por una línea que falta—. Desde la ronda de arreglo 1 esa
  línea la pone **`j2_spi::Ranura::nueva`** (regla R21: el NVIC lo maneja quien
  arma la interrupción, y quien arma `EOTIE` es el driver), junto con la
  prioridad `P1` suya y la de sus dos canales; `j2_esclavo::Esclavo::nuevo` hace
  lo propio con su `EXTI11` y sus dos canales. **Los binarios no tocan el
  NVIC**, y por eso no pueden olvidarlo.
- **La D-cache del M55 está apagada.** embassy no la enciende en ningún sitio
  (`grep enable_dcache` en la rev fijada: nada), y el driver lo asevera al
  arrancar. R-MJ7 (búferes de DMA en región no cacheable) solo muerde el día que
  alguien la encienda para el sampler; ese día los búferes del J2 van a una
  región MPU propia, y el test del riesgo 8 (búfer contra analizador lógico) es
  obligatorio.
- **`rcc::enable_and_reset` no resetea un periférico con el reloj
  encendido**: se salta el pulso (`rcc/mod.rs`, rama `skip reset`). Al
  construir da igual, porque el reloj está apagado; en el reinicio de D4 y en la
  escalada del GPDMA1, no. El driver usa `j2_spi::resetear_por_rcc`, que apaga
  el reloj antes. Medido el 2026-10-14.
- **El SPI del N657 es `spi_v5` para embassy**, no `spi_v4` como dice el plan;
  el driver de embassy los trata juntos y los registros son los del cap. 67
  del RM0486 igual.

> **Enmienda del 2026-09-11 (acta del J2).** Tres cosas cambian en estas medidas:
>
> 1. **El primer experimento es el control positivo, no el soak.** Antes de
>    `resistencia_j2`: reproducir la configuración de jake-taf (embassy,
>    100 kHz, CS por GPIO, `TSIZE = 0`, `blocking_read`) en nuestra placa.
>    1 h da 98 % de potencia contra el extremo suave del hilo, un cuelgue cada
>    900 s. Sin esto, un soak verde no distingue «no nos afecta» de «el banco
>    no lo ve». Y antes que eso, un acceso: `SPE = 1` sin armar nada y leer
>    `SR.EOT`. Si vuelve 1, prender levanta la bandera (RM0486 p. 3492) y la
>    hipótesis de la errata 2.14.2 del H7 (spec D2, enmienda del 11-09) está
>    viva.
> 2. **`eot_al_aire` deja de ser cien mil transferencias.** 12,5 s a 8 kHz
>    acotan p < 3e-5 al 95 %, que no excluye ni el peor extremo del hilo
>    (2e-5): no discrimina nada. Pasa a ser el **barrido del retardo** entre
>    `SPE = 1` (con lectura de vuelta de `CR1`) y `CSTART`, en
>    {0, ¼, ½, 1, 2, 4} × T_SCK, en la configuración mala. Una tasa que dependa
>    del retardo es la firma de la errata; una que no, no lo es.
> 3. **El límite es cero artefactos audibles** (ficha 2 del acta), no una
>    tasa tolerable. `resistencia_j2` sigue igual, pero su fila se juzga con
>    3/T contra el horizonte que Samuel fije (HUECO), no con «tiene fila».
>
> Dos casillas más: la **prioridad de la interrupción del SPI** por encima del
> ejecutor del J2 (si no, un `EOT` tardío no se pierde, pero no se cuenta); y
> el **método de reset de `probe-rs`**, porque un SYSRESETREQ con los selectores
> de reloj fuera de su valor por defecto puede dejar al chip sin arrancar
> (ES0620 §2.2.22, #364), y en el banco parecería un binario roto.
>
> **Esa segunda casilla, con su orden (#364).** `probe-rs run` resetea el core
> al cargar; si lo hace por `SYSRESETREQ` cae bajo la errata, y si tira de NRST
> no. El `init` de embassy dejaba `RTCSEL` en `0x0` en vez de su defecto `0x2`,
> y eso **ya está arreglado** en `usb::configuracion()` (ARRANQUE.md, «El reset
> por software y el ES0620 §2.2.22»); pero hay que medirlo igual, porque el
> aviso vale para cualquier driver futuro que mueva uno de los diez.
>
> 1. Lo gratis primero: `probe-rs run --help` — ver qué mandos de reset ofrece
>    la 0.32.0 instalada, y con cuál arranca `cargo run --release`.
> 2. La medida: carga el firmware, y **sin tocar NRST ni la alimentación**,
>    vuelve a cargarlo. Si la segunda carga sube y habla por `defmt`, el reset
>    de `probe-rs` no muerde. Si se queda muda antes de la primera línea y solo
>    vuelve con NRST o con un ciclo de alimentación, muerde: anótalo y a partir
>    de ahí toda carga va con NRST.
>
> La salida cuando pase, siempre: **NRST o quitar y poner la alimentación.**

## El primer día en placa (2026-10-01)

La Nucleo llegó el 01-10 y en el mismo día salieron los pasos 1 y 2. Lo que
la lista no sabía, en el orden en que apareció:

1. **La casilla del reset de `probe-rs` (#364) queda cerrada: no muerde.**
   Más de diez cargas seguidas sin tocar NRST arrancaron y hablaron por
   `defmt`, con `RTCSEL` en su defecto y los dos selectores del PHY también
   (`OTGPHY1SEL = 00`, `OTGPHY1CKREFSEL = 0`). Las muertes de ese día eran del
   punto 2, no del reset.

2. **El bring-up del PHY USB que aportamos a embassy colgaba el bus.**
   `phy_init()` tocaba `USBPHYC_CR` con el reloj del OTG apagado y con el bit
   23 de `AHB5RSTR` puesto. El chip se colgaba a los ~0,12 s de arrancar `main`
   y el depurador respondía `SwdApFault`. Medido paso a paso: así como estaba
   se cuelga, soltando solo el bit 23 también, y con la secuencia del ejemplo
   de ST para esta placa lee `0x0001_0015` (el valor de reset del RM) y sigue.
   Arreglo en embassy-rs/embassy#7146; el fork `n6-usb` lo lleva desde
   `697ec64` y `Cargo.lock` apunta ahí.

3. **probe-rs arranca el binario con `PRIMASK = 1`** y nada lo baja: ninguna
   interrupción llega (probe-rs/probe-rs#4390). Lo resuelve `usb::iniciar()`,
   la única puerta a `embassy_stm32::init`, que apaga y limpia el NVIC y
   desenmascara. Sin ella, los cuatro binarios del J2 —que viven del `EOT`, del
   DMA, del `EXTI11` y del ejecutor de `GFXTIM`— habrían dado cada giro por
   plazo vencido, y el soak habría salido rojo por el cargador.

4. **El PHY USB quiere el cristal.** Con la referencia HSI → PLL4 → IC15 a
   24 MHz el PHY no se presenta: D+ y D− quedan en SE0 y Windows no ve nada.
   Con el HSE de 48 MHz ÷ 2 enumera. Es una corrida de cada lado, y contradice
   el «para no depender del cristal» que había en `usb.rs`: para la placa del
   hub es decisión abierta, en #150.

5. **Tras un cuelgue, NRST no basta** (ES0620 Rev 5 §2.2.18): se corta la
   corriente. Y el primer cable de CN8 era de carga (D+ y D− unidos).

6. **La primera corrida de la (1) no midió nada.** El árbol principal estaba
   8 commits detrás de `origin/main`, y cargó el firmware de antes de
   `usb::iniciar()`: el vigía no corrió y en 30 minutos no salió ni una
   fila. Lo delató la línea de arranque (`firmware 16145a6-sucio`). Antes
   de medir: `git pull`, y comparar esa revisión con `git log -1`.

De la errata salió además §2.9.4: en development mode el LPTIM4 de la ROM sigue
vivo cuando arranca el código. Por eso `iniciar()` limpia el NVIC antes de
desenmascarar.
