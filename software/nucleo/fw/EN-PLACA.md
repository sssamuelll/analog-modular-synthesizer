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

**Medido el 2026-10-14** (firmware `c88c1bb`, de 12:03:50 a 16:36:52, un solo
`probe-rs` sin reenganches): **los seis puntos, 0 fallas de cualquier tipo.**

| Retardo (cuartos de T_SCK) | Armados | Plazos vencidos | EOT tardíos | Subidas malas | Escaladas | Tramas cortas |
|---|---|---|---|---|---|---|
| 0 | 7 454 090 | 0 | 0 | 0 | 0 | 0 |
| 1 | 7 455 622 | 0 | 0 | 0 | 0 | 0 |
| 2 | 7 455 615 | 0 | 0 | 0 | 0 | 0 |
| 4 | 7 431 075 | 0 | 0 | 0 | 0 | 0 |
| 8 | 7 452 480 | 0 | 0 | 0 | 0 | 0 |
| 16 | 7 432 201 | 0 | 0 | 0 | 0 | 0 |

Son 44 681 083 transferencias con `TSIZE > 0`, DMA y NSS por hardware. Cada
punto acota la tasa por armado por debajo de 4,1e-7 al 95 %, y no hay tasa que
dependa del retardo porque no hubo ningún fallo. Lo que este banco no ejercita
es la razón de relojes del instrumento: aquí `pclk` va a 32 MHz y el SCK a 8, y
la errata habla de un reloj de sistema *mucho* más rápido que el SCK. La lectura
completa, en la spec del maestro (§9, enmienda del 11-09, punto 3).

### (3) `resistencia_j2` — la puerta de fabricación

```bash
cargo run --release --bin resistencia_j2
```

El montaje entero y tal como lo usará el instrumento, salvo el periodo: ranura 0
en SPI5 dentro del `EJECUTOR_J2` con la política de `core` detrás, esclavo del
banco en SPI4 como tarea del mismo ejecutor (lanzado **antes** que el maestro),
retardo de producción (4 cuartos). **Corre a 1 kHz, no a los 8 del
instrumento:** a 125 µs la CPU de la Nucleo (64 MHz, sin cachés) no da para el
maestro y el esclavo juntos, el hilo se queda sin CPU y el binario no puede
publicar ni una fila (#428, spec D5.1, enmienda del 16-10). A 1 ms el hilo
conserva más de la mitad de la CPU y `atrasos` casi no sube (uno en 316 000
giros el 16-10). **La fila vale para 1 kHz.** Cada hora, cuatro líneas, y una de carga cada minuto:

```
firmware=<rev>
0,SPI5,25,hw,<reloj_MHz>,<horas>,<giros>,<plazos_vencidos>,<eot_tardios>,<subidas_malas>,,NUCLEO-N657X0-Q
esclavo,tramas_ok=,tramas_cortas=,rearmes_escalados=
maestro,escaladas_gpdma=,atrasos=,inestable=,muda=
carga,minuto=<n>,hilo_libre_permil=<0..1000>
```

`atrasos` son los giros que acabaron cuando ya tocaba el siguiente: en un
instrumento sano, cero. `hilo_libre_permil` es la CPU que le queda al hilo,
medida por el propio hilo (`carga`): a 1 kHz sale en torno a 540 (el 54 %), y
una caída sostenida es una sobrecarga que ningún otro contador diría. Si las
líneas de carga dejan de salir, el hilo se quedó sin CPU.

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

**Medido: el soak de 24 h, del 2026-10-16 al 17** (firmware `b9f6d7d`, de 09:17:53 a
09:31:14, un solo `probe-rs` sin reenganches; ranura 0 en SPI5, el esclavo en SPI4, SCK a
8 MHz, a 1 kHz). La fila de `resistencia_j2.csv`:

```
0,SPI5,25,hw,8,24,86399999,0,0,0,2026-10-17,NUCLEO-N657X0-Q
```

El esclavo recibió 86 400 001 tramas, ninguna corta y sin rearmes escalados; el maestro,
cero escaladas del GPDMA, `inestable = false` y `muda = false`. **Cero plazos vencidos,
cero EOT tardíos y cero subidas malas en 86,4 millones de giros.** Por la regla de tres,
la tasa queda por debajo de 3,5e-8 por transferencia y de 0,125 por hora al 95 %. Contra el
ritmo de jake-taf (5 bloqueos en 14,1 h) cero en 24 h tendría una probabilidad de 2e-4, si
su tasa dependiera del tiempo y no de la cadencia.

**Lo que la fila no dice.** (1) Es de 1 kHz, no de 8: a 125 µs la CPU de la Nucleo a
64 MHz no da para el maestro y el esclavo del banco juntos (D5.1, enmienda del 16-10).
(2) `pclk` va a 32 MHz y el SCK a 8, cuatro veces; el hub los separa más, y la errata
habla de un reloj de sistema «mucho más rápido» que el SCK. (3) No ejerció D4: sin un solo
plazo vencido el reinicio no corrió ni una vez, así que la fila no distingue «no nos afecta»
de «el banco no lo ve». (4) El horizonte de «cero artefactos audibles» sigue siendo HUECO
de Samuel.

**Los cuatro atrasos** (giros que acabaron cuando ya tocaba el siguiente: un fallo del
presupuesto de CPU, no del módulo) cayeron todos entre las 10:18 y las 15:20 del 16-10, y
las 18 horas siguientes no tuvieron ninguno. No se conoce la causa; no se trazó.
`hilo_libre_permil` se quedó en 540 todos los minutos.

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

### `carga_j2` — cuánta CPU gasta un giro (herramienta, fuera del orden del día)

```bash
python carga_j2.py            # corre las dos pasadas y saca la fila de carga_j2.csv
python carga_j2.py --anota    # ademas la anade (se niega si el firmware sale -sucio)
cargo run --release --features perfil --bin carga_j2   # lo mismo, sin la cuenta de la fila
```

Gira **el maestro solo**, sin el esclavo del banco (en el mismo núcleo le comería
la CPU y falsearía la cuenta), una pasada sin caché y otra con la I-cache
encendida (la D-cache sigue apagada, R-MJ7). El periodo es el del reloj: 1 ms a
64 MHz y 125 µs a 800 MHz (`--hub`).

**Cada estado de caché tiene su base.** El medidor del hilo compara sus vueltas
con las de la CPU entera, y con la I-cache el hilo da más vueltas por segundo que
sin ella: contra la base de sin caché, la CPU libre salía de más y el J2 de
menos (a 1 kHz salió un total de 7 104 ciclos por giro con un manejador del
ejecutor que ya gastaba 14 011). Se calibra una base por estado antes de
arrancar el J2, y
`carga_j2.py` marca como **inválida**, y no anota, la pasada cuyo total sale
menor que el manejador del ejecutor o cuyo `hilo_libre` satura en 1000, o cuyo ciclo se
aparta más de un 5 % del periodo sin que un atraso lo explique (el transporte por ISR no
tiene calendario: un ciclo de tres periodos son tics saltados). Con `--isr` cuenta como
plazos los giros sin cerrar y los errores del DMA del propio transporte.

Cada pasada imprime dos líneas:

```
carga_j2,cache=<no|icache>,ranuras=,periodo_us=,ciclo_us=,giros_en_5s=,hilo_libre_permil=,atrasos=,plazos_vencidos=,base_por_s=
carga_j2,cache=<no|icache>,previo=,armado=,espera=,cierre=,posterior=,isr_spi=,ejecutor=
```

La segunda son **ciclos de CPU por giro**, y pide `--features perfil`; sin ella
salen en cero y lo dice. `ejecutor` es todo el manejador del ejecutor del J2
sin la ISR del SPI; `previo`, `armado`, `cierre` y `posterior` son el código de
la tarea, y la diferencia con `ejecutor` es la maquinaria de futuros y el
despacho. `espera` es tiempo de reloj, no CPU. El mismo binario repite a menos del
0,1 %. Entre dos compilaciones distintas del código, con la D-cache puesta las cifras
repiten a menos del 1 % (8 000, 8 167 y 1 500 salieron iguales en tres compilaciones) y con
la I-cache a un 2 %; **sin cachés varían hasta un 40 %** (el giro por ISR dio 10 200 y
14 400 ciclos): la colocación del código en la AXISRAM sin caché decide cuánto cuesta cada
captación. Una cifra sin cachés no vale como evidencia de diseño.

**Medido el 2026-10-17 a 64 MHz** (firmware `4b97dcf`, una ranura a 1 kHz; repetido,
sale igual a ±1 ciclo):

| | `hilo_libre_permil` | **J2 entero** | `ejecutor` | código de la tarea | el resto del ejecutor | `isr_spi` |
|---|---|---|---|---|---|---|
| sin caché | 685 | **20 160** | 17 415 | 6 625 | 10 790 | 508 |
| I-cache | 748 | **16 112** | 14 004 | 5 236 | 8 768 | 429 |

La fila de sin caché del 16-10 (21 558 a 125 µs, saturado) sigue en `carga_j2.csv`;
la de I-cache de ese día (14 752) salió con la base de sin caché y se retiró.

**El número que se compara con el límite es el «J2 entero»**: lo que el hilo no usa
en un ciclo, `(1000 - hilo_libre_permil) / 1000 × ciclo_us × f_cpu`. Lleva la ISR
del SPI, las del DMA y la del reloj de embassy, que el `ejecutor` no cuenta (el
`ejecutor` y los tramos son el desglose). `carga_j2.py` hace la cuenta y escribe
la fila.

Es el número que el papel pide como criterio de aceptación de la CPU (riesgo 9
de la spec del maestro), contra el límite que Samuel firmó el 2026-10-16: **2 500
ciclos por giro**, el 15 % de un núcleo a 800 MHz. Cada corrida se anota como una
fila de `carga_j2.csv`; `recuperacion_j2_budget.py` la lee y falla si la fila que
cuenta pasa del límite. Desde el papel v3 (§5.2 a), la que cuenta es la del peor
régimen de caché del tic (ver «Las filas del tic en `carga_j2.csv`»).

**Opciones y herramientas para acercar el banco al hub** (`reloj-hub`, `ranuras-N` y
`muestreo` son features de `fw`; `carga_j2.py` pasa las dos primeras con `--hub` y
`--ranuras N`):

- `reloj-hub`: el núcleo a **800 MHz** (`usb::configuracion_hub`: PLL1 desde el HSE de
  48 MHz, `48 / 3 × 50`, y `IC1` como reloj de la CPU). El periodo pasa a ser el del
  instrumento, 125 µs; a 64 MHz es de 1 ms, porque a 125 µs el giro llega siempre
  tarde y se mide un lazo saturado. La cabecera imprime el reloj pedido y el medido
  con el `DWT`, y `carga_j2.py` se niega si se apartan más de un 2 %. Hay una tercera
  pasada con la D-cache, **sin la región MPU de los búferes del DMA** (R-MJ7): sale
  como `icache+dcache-sin-mpu`, es de exploración y no se anota en el CSV.
- `ranuras-2` y `ranuras-3`: giran además una y dos ranuras de relleno, **SPI1 y SPI2
  sin módulo detrás** (la 2 y la 3 de `SPI_DE_RANURA`), que clocan al aire; la subida
  sale mala y da igual, porque se mide el transporte. Sirve para ver qué parte del
  coste es de cada ranura y cuál se reparte entre ellas (la ISR del reloj, la entrada
  del ejecutor): el coste por giro es el total entre todos los giros. Los pines salen a
  conectores sin otra función en la placa (UM3417 Rev 3, Tabla 13) y no llevan nada
  cableado:

  | Ranura | SPI | SCK | MOSI | MISO | NSS | DMA |
  |---|---|---|---|---|---|---|
  | 2 | SPI1 | PB9 (CN15-16) | PC3 (CN3-25) | PB8 (CN15-14) | PC5 (CN3-15) | CH4, CH5 |
  | 3 | SPI2 | PF2 (CN2-4) | PD7 (CN15-19) | PD6 (CN15-6) | PC1 (CN15-5) | CH6, CH7 |

- `muestreo` y `perfil_pc.py`: el **reparto por función** de lo que gasta la CPU. `TIM6`
  a la prioridad más alta anota el PC a 21 kHz en un histograma (`src/muestreo.rs`) y
  el guion lo lee por `probe-rs read` y lo cruza con los símbolos del ELF:

  ```bash
  cargo build --release --features muestreo --bin perfil_pc    # (y reloj-hub, ranuras-N)
  python perfil_pc.py target/thumbv8m.main-none-eabihf/release/perfil_pc
  ```

  Da **cómo se reparten** los ciclos, no cuántos son: la ISR del muestreo perturba (~5 %
  de la CPU a 64 MHz) y los ciclos por giro salen de `carga_j2`. Existe porque
  `probe-rs profile` 0.32 no arranca y `DWT_PCSR` lee `0xFFFFFFFF` en el M55.
  Solo las muestras que caen en una ISR (`IPSR != 0`, el J2 entero) van al histograma;
  las del hilo se cuentan aparte, porque el medidor del hilo es otro ejecutor de
  embassy con las mismas funciones y se mezclaba con las tareas del J2. La feature
  `caches` enciende la I-cache y la D-cache (sin MPU) para perfilar el régimen de 800 MHz.

- `costes_bus`: **cuánto cuesta un acceso a un registro de periférico**, en ciclos de CPU
  (`cargo run --release --features perfil[,reloj-hub] --bin costes_bus`). A 800 MHz el
  núcleo lleva el bus de periférico a una fracción de su velocidad y cada lectura espera:
  un giro hace cerca de un centenar de accesos (SPI, GPDMA, el reloj de embassy), así que
  lo que decide si caben en 2 500 ciclos puede ser el número de accesos y no el código.
  Imprime `costes_bus,f_cpu=,cache=,destino=,lee_x100=,escribe_x100=`, en centésimas de
  ciclo por acceso, para la SRAM (referencia), el SPI5, el canal 15 del GPDMA1 y el
  reloj de embassy.

- `costes_dma` y `mpu::region_no_cacheable`: **cuánto cuesta leer y escribir un búfer de
  DMA** de 32 y de 128 bytes según la forma de R-MJ7: una región de la MPU *Normal, no
  cacheable*, o el búfer cacheable con `clean` e `invalidate` por dirección
  (`cargo run --release --features perfil[,reloj-hub] --bin costes_dma`). Imprime
  `costes_dma,f_cpu=,cache=,operacion=,ciclos_x100=`, en centésimas de ciclo por
  operación entera.

**Medido el 2026-10-17 a 800 MHz** (`--hub`, núcleo medido a 800,1 MHz, periodo 125 µs).
**Es exploración, no una fila de `carga_j2.csv`**: la pasada con D-cache va sin la región
MPU de los búferes del DMA (R-MJ7) y no se anota, y `recuperacion_j2_budget.py` sigue
sin medida a 800 MHz con las cachés del hub. Ciclos por giro, J2 entero (límite 2 500):

| transporte | ranuras | sin caché | I-cache | I-cache + D-cache, sin MPU |
|---|---|---|---|---|
| ejecutor (el de D5.1) | 1 | 77 773 | 57 437 | **8 000** (3,2×) |
| ejecutor | 3 | 70 944 | 49 202 | **8 167** (3,3×) |
| ISR sin ejecutor (`j2_isr`, una cota) | 1 | 14 400 | 7 700 | **1 500** (0,6×) |

Firmware `a3fd211`. La columna sin caché cambia de una compilación a otra (arriba); la de
D-cache, no. **La cota por ISR completó un giro por tic** en las tres pasadas —`ciclo_us` 125,
40 000 giros en 5 s— **sin un solo giro sin cerrar ni un error del DMA**, en tres corridas
seguidas.

- **La D-cache lo decide casi todo.** Sin ella, una lectura de la SRAM cuesta 80 ciclos a
  800 MHz (26 a 64 MHz); con ella, 1,1. Una lectura de registro de periférico cuesta 32 a
  48 ciclos (12 a 16 a 64 MHz) y no se cachea (tabla de `costes_bus` abajo).
- **Con tres ranuras no baja:** 8 167 por giro contra 8 000 con una. El coste del giro no
  se reparte entre ranuras (cada una espera en su propio `Timer`); las seis ranuras a 8 kHz
  serían cerca de la mitad de un núcleo (48 %), contra el 15 % firmado.
- **De los 8 000 (una ranura, con cachés)**, `ejecutor` son 5 810, de los cuales solo 2 706
  son código de la tarea (previo 333, armado 1 479, cierre 549, posterior 345) y 3 104 la
  maquinaria de futuros y el despacho; `isr_spi` son 244 y el resto, unos 1 950, es lo que
  no cae en esos dos manejadores (las ISR del DMA y del reloj de embassy, y lo que el hilo
  pierde al volver). La maquinaria de futuros y el despacho (3 104) son 1,24 veces el límite
  por sí solos; la ISR del SPI (244) la paga cualquier transporte, y la cota paga 185; y los
  ~1 950 restantes no están atribuidos.
- **El perfil por función (`perfil_pc`, 800 MHz con cachés)** da 6 278 ciclos por giro en
  ISR: `TaskStorage::poll` 2 065 (el cuerpo de las tareas), `_embassy_time_schedule_wake`
  1 457, el driver del DMA (`is_running`, `drop`, `configure`, `on_irq`, `start`) 1 281, el
  waker, `Timer::poll`, `poll` de `&mut F` y la entrada del ejecutor 971, `SPI5` 195. Los
  1 700 que faltan hasta los 8 000 no caen en ninguna función; lo más probable es el hilo
  al volver (cachés frías, entrada y salida de cada excepción), pero no está medido.
  Quitando por completo el reloj de embassy y la maquinaria de wakers y ejecutor (2 428
  ciclos) quedarían unos 3 850 en la base del perfil (5 572 en la del J2 entero, que es la
  del límite). Eso supone esa maquinaria por ranura: con un solo `Timer` y una entrada de
  ejecutor repartidos entre las seis bajaría, y no se ha medido ninguna configuración así.
- **`j2_isr` es una cota, no el transporte del instrumento:** el mismo giro por ISR, sin
  ejecutor ni futuros (un `TIM7` de tic cierra el giro anterior y arma el siguiente; los
  canales del GPDMA preprogramados, sin `TCIE`), con la política de `core` detrás. No tiene
  plazo, ni D4, ni calendario, ni EOT tardío, y no se ha corrido contra el esclavo. Mide
  1 121 en la ISR del tic más 185 en la del SPI, y 1 500 por el medidor del hilo.
- **Un `info!` de `defmt` mantiene las interrupciones apagadas más de un periodo del J2
  sin cachés.** Medido sobre las líneas de resultados de `carga_j2`, a 800 MHz: 139 000 y
  119 000 ciclos (174 y 149 µs) sin cachés, 69 000 y 61 000 con la I-cache, 9 000 y 7 600 con
  las dos. Imprimir los resultados de la primera pasada retrasó ~110 µs el tic de `j2_isr` y
  dejó un giro sin cerrar (`SR` con 23 de 25 bytes por clocar, a 14 µs del armado, sin ningún
  error del DMA). `carga_j2` guarda lo medido y lo imprime al final. **Para el instrumento:**
  `defmt` con el J2 girando retrasa el tic y los `EOT` lo que tarde la llamada (~10 µs con
  las dos cachés, más de un periodo sin ellas).

`costes_bus` (ciclos por acceso, de la lectura y de la escritura, en bucle desenrollado:
las escrituras seguidas llenan el búfer de escritura y miden su caudal; una lectura espera
siempre al periférico):

| destino | 64 MHz, lee | 64 MHz, escribe | 800 MHz, lee | 800 MHz, escribe (I-cache) |
|---|---|---|---|---|
| SRAM, sin D-cache | 26,0 | 1,1 | 80,0 | 1,1 |
| SRAM, con D-cache | 1,1 | 1,1 | 1,1 | 1,1 |
| SPI5 (`SR`, `CRCPOLY`) | 16,0 | 4,0 | 48,0 | 16,0 |
| GPDMA1 (canal 15) | 12,0 | 2,0 | 32,0 | 8,0 |
| reloj de embassy (`TIM12.CNT`) | 16,0 | — | 48,0 | — |

`costes_dma` a 800 MHz, con la D-cache y la región MPU puestas (ciclos por operación; la
I-cache, siempre encendida):

| operación | 32 bytes (una línea) | 128 bytes (cuatro) |
|---|---|---|
| región no cacheable, leer con `ldm` en ráfaga | **96** | **372** |
| región no cacheable, leer palabra a palabra | 676 | 2 692 |
| región no cacheable, leer byte a byte | 2 696 | 10 756 |
| región no cacheable, escribir palabras | 51 | 195 |
| cacheable: `invalidate` y leer palabras | 160 | 580 |
| cacheable: `invalidate` y leer bytes | — | 1 028 |
| cacheable: escribir palabras y `clean` | 176 | 388 |
| cacheable, ya en la caché y sin mantenimiento (cota inferior): leer palabras | — | 164 |

- **En la región no cacheable un acceso suelto cuesta 84 ciclos, sea byte o palabra**, y una
  ráfaga `ldm` de ocho palabras cuesta 96. Un CRC o una comparación que lea el búfer de
  subida directamente, a byte, cuesta unos 10 000 ciclos por 128 bytes: la subida se copia
  con `ldm` a un búfer local y se trabaja sobre la copia. Que el compilador genere `ldm`
  para un `copy_from_slice` hay que mirarlo en el desensamblado: aquí está hecho con `asm!`.
- **Con mantenimiento por dirección**, un `invalidate` o un `clean` de una línea cuestan unos
  30 ciclos, y traer de nuevo una línea invalidada, unos 85.
- **Una trama de 25 bytes (la normal), bajada y subida:** región no cacheable con `ldm`,
  unos 150 ciclos (51 + 96); cacheable con mantenimiento, unos 340 (176 + 160). **Una de 103
  bytes (el `SET` de dieciséis):** unos 570 contra unos 970. La región no cacheable sale más
  barata en los dos tamaños, con la condición de arriba.

Qué falta para una fila: el transporte con sus búferes dentro de la región (los de hoy son
locales de las tareas y de la ISR) y la D-cache encendida con ella (R-MJ7, #380), y que el
transporte que se mida sea el del instrumento.

### El transporte por tic (prototipo de banco, 2026-10-17)

`j2_tic` (feature `transporte-tic`) es el diseño de `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v2.md` §2 puesto en la Nucleo, y **no es el transporte firmado de D5.1** (acta del 17-10, ficha 3; no cambia nada firmado ni nada del instrumento). Una interrupción periódica (`TIM7`, P1) lee `SR` del SPI y de los dos canales del GPDMA de cada ranura armada, se lo da a la máquina de `core::transporte_j2` y hace lo que ella diga. El planificador (`DMA2D`, P3) es el único que llama a la política: vacía el anillo de eventos, copia la subida con `ldm`, la juzga y compone la trama siguiente en un buzón de **tres** casillas. La recuperación (`JPEG`, P4) hace D4 con `CxCR.RESET`, el reset del SPI por RCC y, si un canal no para en 25 µs, el del GPDMA1 entero. No hay `EOTIE`, ni ISR de SPI ni de DMA (sus líneas, enmascaradas); los búferes del DMA van en una región no cacheable (R-MJ7) que `lanzar` pone en la MPU, y las dos cachés, encendidas. Las piezas puras (la máquina, el anillo, el buzón, la subida, los marcos numerados) viven en `core` con sus pruebas: `transporte_j2`, `buzones_j2` y `marcos_j2`. `Vencida` y `Reiniciando` dan la ranura por muerta a los **100 tics** (12,5 ms) cada una, no a los 2 y 4 del papel v2 (ver «La cota de espera contra una retención de P2»). Los hallazgos de la revisión del código y lo que se hizo con cada uno están en `docs/superpowers/juntas/2026-10-17-j2-transporte/junta_halberg_codigo.md`; los comentarios del código los citan por su número.

```bash
cargo run --release --features transporte-tic,reloj-hub[,perfil][,ranuras-3][,sin-componer][,contaminador][,largo-71] --bin carga_j2
cargo run --release --features transporte-tic,reloj-hub[,verifica-bajada][,mil-hz][,corta][,acapara] --bin tic_banco
cargo run --release --features inyeccion,reloj-hub[,verifica-bajada] --bin tic_recupera
cargo run --release --features inyeccion,reloj-hub,ranuras-3,sin-esclavo,escalada --bin tic_recupera
cargo run --release --features inyeccion,secuencia,reloj-hub,pines-medio[,corta|,larga] --bin tic_estres
cargo run --release --features inyeccion,reloj-hub[,cotas-v2] --bin tic_cota
cargo run --release --features transporte-tic,tabla,reloj-hub,corta[,pines-medio][,subida-quieta] --bin tic_contenidos
```

Hasta el 20-10, `carga_j2.py` no lo anotaba (se negaba con cualquier transporte que no fuera el `ejecutor`) y `carga_j2.csv` no tenía filas suyas: la puerta tomaba el mínimo de las filas a 800 MHz sin mirar el transporte, y una fila del tic habría tapado los 8 000 del ejecutor firmado (papel v2 §5). Desde entonces el CSV lleva el transporte y el régimen de caché (ver «Las filas del tic en `carga_j2.csv`»). Qué hace cada binario:

- **`carga_j2 --features transporte-tic`**: el mismo medidor del hilo de arriba, con una base por estado de caché. `sin-componer` hace que la trama sea siempre la misma (el enlace solo); sin él, `bajada_del_banco` la rehace en un lazo cada giro (un compositor de mentira, que cuesta unos 170 ciclos a 25 bytes). `contaminador` añade una tarea de hilo que recorre 64 KB entre vuelta y vuelta, y cada tic y cada pasada del planificador empiezan con la D-cache desalojada. `largo-41` y `largo-71` cambian el mensaje. Con `perfil` imprime además los ciclos por giro de cada nivel (tic, planificador, recuperación, componer) y el detalle del tic (leer, cerrar, armar).
- **`tic_banco`**: el maestro de `j2_tic` en SPI5 contra el esclavo del banco en SPI4, a 8 kHz y con las cachés y la región, 600 s; publica una sola vez al final. `verifica-bajada` hace que el esclavo compare cada bajada con el patrón (`PATRON_BAJADA`) y cuente las buenas y las malas.
- **`tic_recupera`** (feature `inyeccion`): A, un SPI envenenado (el canal de transmisión cuenta un byte menos que el `TSIZE`: el maestro se queda sin dato a mitad de trama con el `CS` abajo); B, mil incidentes seguidos; C, diez escaladas **forzadas** del GPDMA1 con las vecinas en vuelo (sin esclavo: el esclavo comparte el GPDMA1), una cada 400 ms para caber en el presupuesto de escaladas; E (con `escalada`), cuatro escaladas seguidas en la ranura 3 con la ventana del presupuesto vacía, para que la cuarta se deniegue; F, un error de ajuste de usuario del DMA (`USEF`: el canal de recepción con el ancho de origen de una palabra y un bloque de 25 bytes, RM0486 sec. 19.4.17), que lleva a la rama `error_dma` del tic; D, la recuperación inhibida hasta que la ranura pasa a `Muerta`. Cada fase termina con sus comprobaciones.
- **`tic_estres`** (features `inyeccion`, `secuencia` y `pines-medio`): cuatro fases de `FASE_S` segundos (60; 5 con `corta`; 150 con `larga`, diez minutos en total) con marcos numerados en los dos sentidos (`core::marcos_j2`: el valor al principio y al final del marco y, en medio, bytes que dependen del valor, de la posición y del sentido). El cerebro numera cada bajada; el esclavo del banco la clasifica (rota, repetida, atrasada, o buena con los números que se saltó) y devuelve en la subida el último número que aceptó; el juez del cerebro clasifica la subida (rota, atrasada, futura, repetida). Las fases: sin nada; golpes de P3 de 10 a 280 µs, uno tras otro con 0,5 a 4,5 ms de hueco (xorshift de semilla fija), que le quitan al planificador y a la recuperación el sitio detrás del tic y hacen que el tic los interrumpa en puntos al azar (`compone`, `Subida::leer`, `recupera`); incidentes al azar (por turno, un cuelgue con probabilidad 1/4 y un error del DMA con 1/16); y las dos cosas. Pasa si en las cuatro fases las bajadas rotas, repetidas y atrasadas y las subidas rotas, atrasadas y futuras son cero, ninguna ranura muere y cada plazo vencido acaba en una recuperación.
- **`tic_cota`** (feature `inyeccion`; `cotas-v2` para las del papel v2): para cada retención `D` de una lista creciente (100 µs a 60 ms), envenena la ranura 0 y, **en el instante en que el tic la da por vencida**, una interrupción de P2 retiene la CPU `D` microsegundos, de modo que el planificador no puede pedir la recuperación hasta que acabe. Mira si la ranura sigue viva; el primer `D` que la mata es el umbral.
- **`tic_contenidos`** (features `tabla` y `transporte-tic`; `pines-medio` y `subida-quieta` cambian el enlace): la bajada recorre una tabla de 16 contenidos de prueba de 25 bytes (el byte 0 es el número del contenido) y el esclavo cuenta, de cada uno, cuántas tramas llegan enteras y cuántas no, con los bytes de la primera que no.

**Ciclos por giro y por ranura a 800 MHz** (medidor del hilo, sin `perfil`; mensaje de 25 bytes salvo que se diga; límite provisional 2 500; el ejecutor de D5.1 da 8 000 con las mismas cachés, arriba). Cada columna con las dos cachés y la región MPU salvo las dos últimas filas:

| | 1 ranura | 3 ranuras |
|---|---|---|
| el enlace solo (`sin-componer`) | 2 200 | **1 967** |
| con el compositor de mentira | 2 400 | 2 100 |
| el enlace solo, D-cache desalojada entre tic y tic (`contaminador`) | — | **2 778** |
| solo la I-cache (sin D-cache), el enlace solo | 17 900 | 15 773 |
| sin cachés, el enlace solo | 27 600 | 22 849 |

| el enlace solo, 3 ranuras, con cachés | 25 bytes | 41 bytes | 71 bytes |
|---|---|---|---|
| ciclos por giro y ranura | 1 967 | 2 100 | 2 200 |

El `SET` de dieciséis (103 bytes) no está medido: a los ~6 ciclos por byte de la tabla saldrían unos 2 400, pero a 6,25 MHz (el kernel del SPI a `pclk2`, #380) ocupa 131,8 µs y no cabe en un periodo de 125 (R-H5).

- **El desglose del `DWT`** (3 ranuras, con `perfil`, ciclos por giro y ranura, cachés calientes, enlace solo): el tic **1 175** (leer los tres `SR` 139; cerrar 10 —las escrituras van al búfer de escritura y su coste aparece en la lectura siguiente—; armar 617, de los cuales 128 son la espera de un `T_SCK` de D2; el resto, unos 410, es el estado, las banderas, el buzón y el anillo) y el planificador **823** (de los cuales 285 son entregar la trama al buzón). Suman 1 998 con la instrumentación puesta; el medidor con `perfil` da 2 050 contra los 1 967 sin ella, o sea que la instrumentación cuesta del orden de 100 ciclos. Con la D-cache desalojada: tic 1 528 (leer 268, cerrar 31, armar 605) y planificador 1 064.
- **La caché fría, por cuánto se desaloja** (3 ranuras, enlace solo, ciclos propios del J2 por giro y ranura según el `DWT`; `contaminador-8k`, `-16k`, `-32k` y el de 64 KB recorren esa cantidad entre vuelta y vuelta, y la D-cache es de 32 KB):

  | barrido | tic | planificador | total |
  |---|---|---|---|
  | ninguno (calientes) | 1 175 | 823 | 1 998 |
  | 8 KB | 1 175 | 822 | 1 997 |
  | 16 KB | 1 175 | 822 | 1 997 |
  | 32 KB | 1 596 | 1 103 | 2 699 |
  | 64 KB | 1 528 | 1 064 | 2 592 |

  El J2 conserva sus líneas mientras quien le comparte la D-cache no la recorra entera entre dos tics: con la mitad no paga nada medible, y desalojada entera paga unos 600 a 700 ciclos más. **El medidor del hilo no sirve para el barrido de 32 KB** (19 500): un recorrido cíclico del tamaño exacto de la caché falla en cada acceso en cuanto el J2 le quita una sola línea, y lo que mide es ese hilo hundiéndose, no el J2. Con 64 KB el hilo falla siempre, con J2 o sin él, y el medidor da 2 778 contra los 2 592 del `DWT`.
- **El tic no depende del largo del mensaje** (1 175, 1 174 y 1 174 a 25, 41 y 71 bytes); el planificador sí: 823, 954 y 1 068 (las copias con `ldm` de la bajada y de la subida y la comparación del juez).
- **El juez del banco es una comparación de 25 bytes.** El de verdad valida el sobre y su CRC, que es trabajo del enlace (ficha 1 del acta) y no está medido ni escrito (#267); un CRC por tabla a unos 5 ciclos por byte suma del orden de 125 a 350 ciclos según el mensaje. **El compositor de mentira tampoco es el real:** la ficha 1 no cuenta componer la trama.
- **De uno a tres ranuras** el coste por ranura baja unos 230 ciclos (se reparten la entrada y la salida de las dos excepciones y el trabajo fijo del tic; la espera de un `T_SCK` de D2, no). Con las seis, algo menos de lo medido con tres.
- **La estimación del papel v2 (§3) se quedó corta:** 1 060 el enlace solo y 1 560 componiendo, a 25 bytes, contra 1 967 y 2 100 medidos.
- **La D-cache lo decide casi todo, como antes** (R-H4): sin ella, 16 000 a 18 000; sin ninguna caché, más de 22 000 (la columna sin cachés cambia de una compilación a otra).

**La caché fría del todo y el J2 en TCM** (2026-10-19, 800 MHz, 3 ranuras, enlace solo con `sin-componer`, mensaje de 25 bytes, cachés y región MPU; todas las cifras son **M**, de `carga_j2` en la Nucleo, medidas con el árbol de este cambio sin commitear; las corridas en frío, repetidas sobre el firmware a436012, dan las mismas cifras). Las dos preguntas eran cuánto cuesta el tic con las dos cachés frías y cuánto de eso quita llevar el J2 a la TCM. Tres features nuevas, solo de banco:

- **`contaminador-icache`** (implica `contaminador`): además de recorrer los 64 KB, el hilo **invalida la I-cache entera** (`ICIALLU` + `DSB` + `ISB`, `perfil::invalida_icache`) entre vuelta y vuelta, y el planificador (`DMA2D`) la invalida al entrar, antes de tomar su primera marca. Se escogió invalidar y no recorrer un código mayor que la I-cache porque es determinista (no depende de la política de reemplazo ni de dónde caiga el texto), cuesta pocos ciclos y deja la I-cache vacía de verdad, que es la cota. Efecto lateral: el propio medidor del hilo también arranca frío tras cada invalidación, y esa pérdida la lee como J2 (ver más abajo).
- **`j2-tcm`**: el texto del tic (`TIM7`), del planificador (`DMA2D`) y de la recuperación (`JPEG`, `recupera`, `escala`), lo que llaman en `core` (`maestro_j2::Ranura::paso`, `buzones_j2::Anillo::empujar`), `j2_spi`, `j2_banco`, `embassy_stm32::rcc` y `memcmp`, `memclr4`, `memmove8` y `uldivmod`, a la **ITCM** (`0x10000000`); y los statics de `j2_tic` y de `j2_ejecutor` (`SELLOS`, `CUENTAS`) a la **DTCM** (`0x30000000`). Lo hace `j2_tcm.x`, que `build.rs` pasa **antes** de `link.x` para que sus sentencias de `SECTIONS` se lleven las secciones de entrada antes que `.text`; el texto de `core` no se toca (`transporte_j2.rs` queda como estaba): se elige por el nombre del símbolo. El depurador no escribe en las TCM (`probe-rs read` en `0x10000000` o `0x30000000` da `SwdApFault`), así que la imagen se enlaza en `0x34100000` (AXISRAM2, por debajo de `FLASH`) y `__pre_init` (ensamblador, sin pila) la copia antes de inicializar `.data` y `.bss`: hay texto en la ITCM que corre desde `Config::new` (`memclr4`), y copiar desde `main` dio un `BusFault` de captación. Los vectores de `TIM7`, `DMA2D` y `JPEG` apuntan a `0x100006a1`, `0x10000001` y `0x10000301` (leídos del ELF con `rust-objdump -s -j .vector_table`) y `rust-nm` sitúa los tres en `0x1000xxxx`. `j2_tcm::comprueba` asevera al arrancar que `ITCMCR` y `DTCMCR` tienen `EN` y que la ITCM coincide con su imagen.
- **`j2-tcm-pila`** (implica `j2-tcm`): además, la pila principal (la de las excepciones) en el tope de la DTCM (`j2_tcm_pila.x`: `_stack_start = 0x30020000`, `_stack_end = 0x30002000`).

```bash
cargo run --release --features transporte-tic,reloj-hub,sin-componer,ranuras-3 --bin carga_j2                       # caliente
cargo run --release --features transporte-tic,reloj-hub,sin-componer,ranuras-3,contaminador --bin carga_j2         # D fría
cargo run --release --features transporte-tic,reloj-hub,sin-componer,ranuras-3,contaminador-icache --bin carga_j2  # I y D frías
# lo mismo con ,j2-tcm o ,j2-tcm-pila; con ,perfil sale el desglose del DWT y la duración del tic
```

Cada cifra de ciclos es por giro y por ranura. El **DWT** es con `perfil` (tic y planificador; la recuperación no corre, no hay fallos); el **medidor del hilo** es de otra compilación, sin `perfil`, con su base por estado de caché. La duración del tic es la de **una entrada** (las tres ranuras juntas), por `DWT_CYCCNT` desde la primera instrucción del manejador hasta antes de salir; **no incluye** el apilado ni el desapilado de la excepción (no medidos). Media y máximo son de la segunda muestra de 5 s de la pasada con las dos cachés (40 000 entradas).

| | tic (DWT) | planificador (DWT) | total DWT | medidor del hilo | tic: media (µs) | tic: máximo (µs) |
|---|---|---|---|---|---|---|
| sin TCM, caliente | 1 174 | 825 | 1 999 | **1 967** | 4,40 | 4,71 |
| sin TCM, D fría (`contaminador`) | 1 513 | 1 058 | 2 571 | **2 778** | 5,68 | 6,18 |
| sin TCM, I y D frías (`contaminador-icache`) | 2 672 | 2 468 | **5 140** | **5 522** | 10,02 | 11,28 |
| `j2-tcm`, caliente | 1 147 | 820 | 1 967 | 1 900 | 4,30 | 4,60 |
| `j2-tcm`, D fría | 1 147 | 839 | 1 986 | 1 984 | 4,30 | 4,61 |
| `j2-tcm`, I y D frías | 1 148 | 989 | 2 137 | 2 447 | 4,31 | 5,28 |
| `j2-tcm-pila`, caliente | 1 137 | 799 | 1 936 | 1 867 | 4,27 | 4,56 |
| `j2-tcm-pila`, D fría | 1 138 | 821 | 1 959 | 1 918 | 4,27 | 4,57 |
| `j2-tcm-pila`, I y D frías | 1 136 | 966 | **2 102** | **2 381** | 4,26 | 5,18 |

Ninguna pasada tuvo atrasos, plazos vencidos, tics tardíos ni fundidos; el retraso máximo del tic al entrar fue de 0 a 3 µs. Las dos primeras filas reproducen lo de arriba: 1 967 caliente, y 2 778 con la D fría (2 745 en la primera corrida y con `perfil`, a un 1,2 %).

- **Con las dos cachés frías el J2 cuesta 5 140 ciclos por giro y ranura según el DWT (5 522 el medidor): 2,6 veces el caliente y casi el doble de lo que se tenía como cota (2 778).** El tic pasa de 1 174 a 2 672 y el planificador de 825 a 2 468: casi todo es captar el texto desde la AXISRAM sin I-cache. A 6 ranuras y 8 kHz serían, **por extrapolación (E)** de la cifra por ranura de tres (`ciclos × 6 × 8 000 / 800 MHz`), el 33 % de un núcleo con el medidor y el 31 % con el DWT, contra 11,8 % caliente y 16,7 % con la D fría, antes de sumar el CRC del sobre (de 125 a 350 ciclos por giro y ranura, de 0,8 a 2,1 %).
- **Con el J2 en TCM la caché fría casi deja de costar.** El tic no se mueve (1 147 caliente, 1 147 con la D fría, 1 148 con las dos frías: las TCM no pasan por caché) y el planificador pasa de 820 a 989 con las dos frías. El total DWT con las dos frías baja de 5 140 a 2 137 (2 102 con la pila): **+8,6 % sobre el caliente de la misma compilación** en los dos casos, contra +157 % sin TCM. A 6 ranuras y 8 kHz (E): 14,7 % con `j2-tcm` y 14,3 % con la pila por el medidor, 12,8 % y 12,6 % por el DWT.
- **Lo que no desaparece:** unos 150 ciclos del planificador con las dos cachés frías (820 a 989), que la pila en la DTCM apenas mueve (966). **No está diagnosticado.** Lo que queda fuera de la TCM son las constantes de `.rodata`, los caminos de pánico y las rutinas de `defmt`; y la invalidación al entrar al planificador deja fría también la captación de sus primeras instrucciones.
- **Caliente, la TCM casi no gana** (1 999 a 1 967 el DWT con `j2-tcm`, a 1 936 con la pila; 1 967 a 1 900 y 1 867 el medidor): lo que da es la cota fría, no el caso típico.
- **El medidor del hilo sobrestima la fila de las dos frías con TCM** (2 447 contra 2 137 del DWT): la invalidación también vacía la I-cache del hilo medidor y del ejecutor, y esa pérdida la lee como J2. Con la D fría los dos coinciden (1 984 y 1 986). Como cota de diseño vale el DWT más lo que cueste apilar y desapilar la excepción (no medido); el medidor es el techo.
- **Lo que el J2 le impone al resto del hub: el tic bloquea todo lo que esté por debajo del nivel 1.** Con tres ranuras dura de media 4,4 µs caliente y 10,0 µs con las dos cachés frías, y su máximo medido es de 4,7 y 11,3 µs (sin apilar ni desapilar); con la TCM, 4,3 y 4,3 µs de media y 4,6 y 5,3 µs de máximo. Con **una** ranura (misma medida, con `perfil`): 1,60 µs caliente y 6,87 µs con las dos frías sin TCM (máximo 1,91 y 7,96), y 1,56 µs y 1,56 µs con TCM (máximo 1,86 y 2,49). De una a tres ranuras el tic crece unos 1 120 ciclos por ranura caliente (1 260 con las dos frías sin TCM, 1 100 con TCM) sobre un fijo de unos 160 (4 240 sin TCM y frío: ahí está captar el texto fijo del tic). **Extrapolado a seis ranuras (E): 8,6 µs de media caliente, 14,7 µs sin TCM y frío, 8,4 µs con TCM**, o sea del 6,9 % al 11,8 % de cada periodo de 125 µs ocupado por una interrupción que nada de P2 o inferior puede cortar. El máximo es el de una ventana de 5 s: no es una cota de peor caso.
- **Coste de la TCM:** con `j2-tcm`, 13 a 13,4 KB de ITCM (de 64 KB) y 4 336 B de DTCM (de 128 KB), más la imagen de unos 17,5 KB en la AXISRAM2 (`0x34100000`), que tras la copia queda sin uso; con la pila, unos 120 KB de la DTCM son pila (`0x30002000` a `0x30020000`). La ITCM lleva más de lo necesario porque el patrón de `embassy_stm32::rcc` arrastra todas sus funciones; se puede afinar. **Esfuerzo:** un guion del enlazador, 35 líneas de ensamblador, unas líneas en `build.rs` y una por static; una sesión.
- **Dos trampas, resueltas:** (1) la copia desde `main` llega tarde, porque hay texto de la ITCM (`memclr4`) que corre antes; va en `__pre_init`. (2) La **DTCM sale del reset sin escribir**: la primera escritura de un byte sobre una palabra nunca escrita (un `AtomicBool`, la pila) dio un `BusFault` preciso en `0x3001f497`; se escribe la DTCM entera por palabras antes de copiar. Se sospecha ECC (el store de un byte lee antes la palabra), pero no está verificado con el manual; lo que sí consta es que el fallo desaparece con solo escribir la DTCM entera.
- **Direcciones y tamaños: de dónde salen.** No se pudo bajar el RM0486 (`st.com` no contesta a `curl` y el PDF no está en `docs/reference`), así que **no hay página del manual que citar**. Las direcciones salen de `stm32n657xx.h` de `cmsis-device-n6` (`ITCM_BASE_S` `0x10000000`, `DTCM_BASE_S` `0x30000000`; 64 KB y 128 KB de base, extensibles con FLEXRAM por `RAMCFG_CR.ITCMCFG` y `DTCMCFG`, que **no se tocan**), y el estado, de la placa en development boot leído con `probe-rs read`: `ITCMCR` `0x39` (`EN`, tamaño 7 = 64 KB), `DTCMCR` `0x41` (`EN`, tamaño 8 = 128 KB) y `SYSCFG_CM55TCMCR` (`0x56008008`) `0x87`. Las TCM no hay que encenderlas: las deja encendidas la ROM. Falta cotejar con el RM0486 la secuencia de FLEXRAM y el ECC de las TCM.
- **No cubre:** la recuperación (`recuperacion` sale 0, no hay fallos en estas corridas; su texto está en la ITCM pero no se midió frío), seis ranuras reales, el CRC del sobre, un hub con USB y pantalla compartiendo la I-cache (la invalidación entera es la cota, no un caso) y el arranque desde XSPI. La tabla de vectores sigue en la AXISRAM2; llevarla a la DTCM con `VTOR` no se probó.

**Lo mismo con K1 a K5, y la división de 64 bits en la ITCM** (2026-10-19, firmware `a1f6623`: lo de arriba más el tic con el reloj de K2, el presupuesto de escaladas, la marca de la escalada, el incidente y las guardas de `Muerta`; mismas compilaciones y mismo método). Con las K, el tic llama en cada entrada a `__aeabi_ldivmod` (la división con signo de 64 bits del reloj de K2), `compone` a `__aeabi_uldivmod` y `Ranura::paso` a `__aeabi_memmove8`; las tres puertas estaban en la ITCM, pero sus cuerpos (`__divmoddi4`, `__udivmoddi4`, `u64_div_rem` y `memmove`) se quedaban en la AXISRAM2. `j2_tcm.x` los lleva ahora a la ITCM, y del patrón de `embassy_stm32::rcc` deja solo `RccInfo`, que es lo que llama la recuperación (`init` y las PLL, unos 8 KB, salen). Lo que el texto de la ITCM llama fuera de ella, leído del desensamblado de `.itcm` (todo salto a una dirección fuera de `0x1000xxxx`): los pánicos, `defmt` y el contaminador del banco (`perfil::invalida_icache`), nada más.

| | tic (DWT) | planificador (DWT) | total DWT | medidor del hilo | 6 ranuras, DWT / medidor (E) | tic: media / máximo (µs) |
|---|---|---|---|---|---|---|
| sin TCM, caliente | 1 237 | 846 | 2 083 | 2 067 | 12,5 / 12,4 % | 4,64 / 4,95 |
| sin TCM, D fría | 1 648 | 1 093 | 2 741 | 2 900 | 16,4 / 17,4 % | 6,18 / 6,68 |
| sin TCM, I y D frías | 3 360 | 2 500 | **5 860** | **6 233** | 35,2 / 37,4 % | 12,60 / 14,13 |
| `j2-tcm`, caliente | 1 212 | 834 | 2 046 | 2 000 | 12,3 / 12,0 % | 4,55 / 4,86 |
| `j2-tcm`, D fría | 1 212 | 853 | 2 065 | 2 067 | 12,4 / 12,4 % | 4,54 / 4,86 |
| `j2-tcm`, I y D frías | 1 213 | 850 | **2 063** | **2 400** | 12,4 / 14,4 % | 4,55 / 5,64 |
| `j2-tcm-pila`, caliente | 1 208 | 816 | 2 024 | 1 967 | 12,1 / 11,8 % | 4,53 / 4,85 |
| `j2-tcm-pila`, D fría | 1 207 | 835 | 2 042 | 2 000 | 12,3 / 12,0 % | 4,53 / 4,82 |
| `j2-tcm-pila`, I y D frías | 1 206 | 836 | **2 042** | **2 300** | 12,3 / 13,8 % | 4,52 / 5,64 |

Ninguna pasada tuvo atrasos, plazos vencidos, tics tardíos ni periodos saltados; el retraso máximo del tic al entrar fue de 0 a 2 µs.

- **Las K le cuestan al tic unos 60 ciclos por giro y ranura en caliente** (1 174 a 1 237 sin TCM) y al planificador unos 20 (825 a 846); con TCM y las dos frías, el tic sube 65 (1 148 a 1 213).
- **Los ~150 ciclos del planificador que no estaban diagnosticados eran la división de 64 bits de `compone`**, que se iba a la AXISRAM2: con su cuerpo en la ITCM, el planificador con las dos frías baja de 989 a 850, a 16 ciclos del caliente de la misma compilación. El total DWT con TCM y las dos frías queda en 2 063 (+0,8 % sobre su caliente; antes +8,6 %), y 2 042 con la pila (+0,9 %). El medidor, que con las dos frías lee también la I-cache vaciada del hilo, da 2 400 y 2 300: es el techo, y el DWT la cota de diseño, como arriba.
- **Sin TCM y con las dos frías el J2 cuesta más que antes** (5 140 a 5 860 el DWT): la división de K2 se capta desde la AXISRAM2 en cada entrada del tic.
- **`reloj_anomalo` salió 1 y 2 veces en dos corridas sin TCM, las dos en la primera pasada, la de las cachés apagadas** (el tic dura ahí unos 45 µs por entrada; los testigos son acumulados y no crecen en las pasadas con caché), y 0 en todas las demás: K2 contó un periodo en vez de reconstruirlo. Ningún régimen del instrumento corre sin cachés; la causa no está diagnosticada.
- **Huella, con seis ranuras** (`RANURAS_SPI` = 6 dimensiona todos los estáticos, aunque giren tres), sin `perfil` ni contaminador, de `rust-size`: **ITCM 8 120 B** (de 64 KB) y **DTCM 4 616 B** (de 128 KB); igual con `j2-tcm-pila` y con `sin-componer` (8 128). Dentro, el juez del banco (`juez_del_banco`, 38 B, y `memcmp`, 116 B), que hace las veces de la comprobación de la subida y no es el CRC real. Los búferes del DMA (`REGION`, 3 840 B) siguen en la AXISRAM2, en la región no cacheable de R-MJ7. La pila del anidamiento de las tres rutinas, por el desensamblado (E: los marcos más hondos de `TIM7`, `DMA2D` y `JPEG`, 204, 240 y 80 B, más tres marcos de excepción de hasta 104 B; no sigue llamadas indirectas): unos 0,85 KB.
- **El tic con seis ranuras, extrapolado (E)** con el fijo de unos 160 ciclos de la medida con una ranura: con TCM y las dos frías, ~8,9 µs de media y ~11,1 µs de máximo; sin TCM y frío (con su fijo de unos 4 240), ~20 µs de media.

**El CRC del sobre de la subida, medido** (2026-10-19; el árbol de este cambio sin commitear, sobre `52f0521`; `j2-tcm`, tres ranuras, `sin-componer`, mensaje de 25 bytes salvo donde se dice). Con `crc-bits`, `crc-tabla` o `crc-unidad`, el juez de `carga_j2` calcula además el CRC-16/CCITT-FALSE de la cabecera del J2 (D1: de todos los bytes de la subida menos los dos últimos) y lo compara con esos dos; el veredicto sigue siendo el de `juez_del_banco`, así que la política recorre el mismo camino y la diferencia con la fila sin CRC es lo que cuesta el CRC. Por bits es `descubrimiento::crc16`, el que la cabecera dice reutilizar; por tabla, `descubrimiento::crc16_con` con la tabla de 256 entradas copiada a la DTCM (512 B); con la unidad, la unidad CRC del N657 (v3, `0x46024C00`) con el polinomio `0x1021` de 16 bits, inicial `0xFFFF` y sin reflejar, por palabras con los bytes dados la vuelta (`REV`: la unidad mete primero el bit 31 y la v3 no invierte por bytes) y la cola por media palabra y byte. **La unidad da el CRC de `crc16` en la placa:** el vector canónico (`"123456789"` → `0x29B1`) y todos los largos de 0 a 71 de un contenido pseudoaleatorio, comprobados al arrancar (`prepara_crc_unidad`).

| | caliente: planificador / total DWT / medidor | I y D frías: planificador / total DWT / medidor | el CRC con las dos frías (DWT) | 6 ranuras, I y D frías, DWT / medidor (E) |
|---|---|---|---|---|
| sin CRC | 834 / 2 046 / 2 000 | 852 / 2 065 / 2 400 | — | 12,4 / 14,4 % |
| por bits | 2 393 / 3 605 / 3 567 | 2 417 / 3 630 / 3 933 | +1 565 | 21,8 / 23,6 % |
| **por tabla, en la DTCM** | 1 071 / 2 282 / 2 233 | 1 090 / **2 303** / **2 600** | **+238** | **13,8 / 15,6 %** |
| con la unidad | 1 195 / 2 407 / 2 333 | 1 210 / 2 423 / 2 766 | +358 | 14,5 / 16,6 % |

Con 71 bytes y las dos frías (DWT): el planificador sin CRC hace 1 089; por bits, 5 749 (+4 660); por tabla, 1 737 (+648); con la unidad, 1 903 (+814). Totales: 2 302, 6 962, 2 950 y 3 115 ciclos, el 13,8, 41,8, 17,7 y 18,7 % de un núcleo con seis ranuras (E). El tic no se mueve en ninguna (1 211 a 1 213).

- **La tabla es la más barata: unos 10 ciclos por byte** (238 con 23 bytes, 648 con 69), y con la tabla en la DTCM no depende de la caché (caliente, 237). Pide 512 B más de DTCM: 5 128 B.
- **La unidad CRC cuesta un 50 % más que la tabla con 23 bytes y un 25 % más con 69:** cada escritura en el periférico se paga, y la lectura del resultado espera a todas. La cabecera (§10, riesgo 5) ponía la unidad por debajo de la tabla; en el cerebro es al revés. Sus cifras (82 a 92 ciclos con la unidad, 101 con tabla) son **por muestra y del lado del módulo**, el receptor, con su coste fijo de 47: no se comparan con estas, que son por trama y del lado del cerebro.
- **Por bits, 68 ciclos por byte:** con 25 bytes el J2 pasa al 21,8 % de un núcleo.
- **La estimación del papel v3** (§3: de 125 a 350 ciclos, 5 por byte, sin fuente) acierta con la tabla y 25 bytes (238) y se queda en la mitad con 71 (648).
- En las 60 pasadas no hubo atrasos ni plazos vencidos; `reloj_anomalo` salió una vez, en la pasada con las cachés apagadas de una corrida con TCM.

**Lo mismo sobre el guion de enlazado final** (2026-10-19, firmware `13ecefa`: de `core` solo los módulos del J2 y las dos funciones del CRC nombradas en `j2_tcm.x`; `tcm_cierre.py --raices TIM7,DMA2D,JPEG` en verde con las tres variantes). Las dos cachés frías, 25 bytes, DWT / medidor: sin CRC, 2 063 / 2 400; por tabla, **2 299 / 2 633** (+236 en el planificador), el 13,8 y el 15,8 % de un núcleo con seis ranuras (E); con la unidad, 2 424 / 2 767 (+361); por bits, 3 629 por el DWT (+1 567). Con 71 bytes, por tabla, +650 sobre su fila sin CRC (1 087 a 1 737). Las primeras corridas metían todo `core` en la ITCM; con el guion estrecho las cifras se mueven unos pocos ciclos, y la tabla sigue por debajo de la unidad. Huella con el CRC por tabla, sin `perfil`: ITCM 8 224 B y DTCM 5 128 B. Ningún testigo con novedad en las nueve corridas.

**La entrada de la excepción del tic, medida** (2026-10-19, firmware `7fec6a2`, `tic-fino`: `TIM7` sin preescalar, así que el retraso de entrada sale en cuentas de `f_timer`; con `perfil`, `entrada_ciclos` da en ciclos lo que va del suceso de actualización a que el manejador lee `TIM7.CNT`: el apilado, la captación del vector y el prólogo, que el DWT del tic no ve). Tres ranuras, `sin-componer`, CRC por tabla; media / máximo por entrada del tic (una entrada sirve a las tres ranuras):

| | caliente | I y D frías |
|---|---|---|
| sin TCM | 61 / 68 | 319 / 860 |
| `j2-tcm` | 62 / 68 | 143 / 844 |
| `j2-tcm-pila` | 60 / 60 | 136 / 716 |

- **Con TCM, la caché fría le añade a la entrada unos 80 ciclos por tic** (de 62 a 143), unos 27 por ranura y giro con tres ranuras; la pila en la DTCM apenas la mueve (136). Sin TCM, unos 260 (de 61 a 319).
- **No está medido:** la salida (el desapilado) ni la entrada del planificador, que se encadena al tic (`DMA2D` queda pendiente al final del tic; en el M55 la cadena se ahorra apilar, no captar el vector). Si cada una costara lo que la entrada del tic (E), las tres juntas sumarían unos 50 a 110 ciclos por ranura y giro con las dos frías y TCM: el J2 con el CRC por tabla quedaría en unos 2 350 a 2 410 ciclos, del 14,1 al 14,5 % de un núcleo con seis ranuras (E), entre el DWT (13,8 %) y el medidor (15,8 %), y más cerca del primero.
- El reloj de K2 con la cuenta fina no dio `reloj_anomalo` en ninguna pasada con caché; salió 2 veces en la corrida sin TCM, que cuenta también la pasada con las cachés apagadas.

**La salida de la excepción y la entrada encadenada del planificador, medidas** (2026-10-19, firmware `50d43c3`; acta del 19-10, tercera firma, nota de la ficha J). Con `tic-fino` y `perfil`, el tic anota el ciclo en que acaba y `DMA2D` mide desde su primera instrucción cuánto tardó en entrar: **la cadena**, que son el epílogo del tic, el encadenado y el prólogo del planificador. Para **la salida**, una pasada final de `carga_j2` deja el hilo girando sobre el contador de ciclos sin esperar nada, y en cada hueco mide desde el final de `DMA2D` hasta la primera lectura del hilo, y el hueco entero. La pasada corre dos veces: una sin tocar las cachés y otra invalidando las dos tras cada hueco, así que el tic siguiente entra con las dos frías. Tres ranuras, `sin-componer`, CRC por tabla, 8 000 huecos por pasada, I y D encendidas con la región. Medias por tic:

| | entrada | cadena | salida | cuerpos del tic y del planificador, por giro y ranura (DWT) |
|---|---|---|---|---|
| `j2-tcm`, caliente | 62 | 44 | 34 | 2 305 |
| `j2-tcm`, I y D frías | 143 | 121 | 37 | 2 329 |
| `j2-tcm-pila`, I y D frías | 136 | 119 | 35 | 2 303 |

- **Las partes cuadran con el hueco que ve el hilo.** Entrada, tic, cadena, planificador y salida suman entre 62 y 67 ciclos menos que el hueco medido: la propia instrumentación y el paso del bucle del hilo (4 a 13 ciclos). Con `contaminador-icache` faltan unos 780 más, que son la invalidación de la I-cache que el banco hace dentro de `DMA2D`, no trabajo del J2.
- **Cuando el banco vacía la I-cache, la salida sube a una media de 213 a 256 ciclos (109 de mínimo).** Al volver, el hilo tiene que traer otra vez su propio código. Es el coste que la ficha J deja fuera de la cifra del J2 («el medidor cuenta como J2 la I-cache vaciada de su propio hilo y sobrestima»). Con el código del hilo en la I-cache y la D-cache fría, la salida es de 31 a 37 ciclos: el marco se apiló al entrar y sigue en la caché al salir.
- **La cifra de la ficha J, medida.** Con TCM, las dos frías y el CRC por tabla, entrada, cadena y salida suman 301 ciclos por tic, unos 100 por giro y ranura con tres ranuras. Con los cuerpos de esta corrida (2 329), el J2 cuesta **2 429 ciclos por giro y ranura: el 14,6 % de un núcleo con seis ranuras** (las partes son M, la suma es A y la columna de seis ranuras, E). Con los cuerpos de `13ecefa` (2 299), 2 399, el 14,4 %. **Por debajo del 15,0 %: la pasada de optimización sigue aparcada.** Si al J2 se le cargara también lo que el hilo tarda en traer su código, serían de 2 488 a 2 502 ciclos, del 14,9 al 15,0 %.
- **La columna de seis ranuras cuenta dos veces la entrada, la cadena y la salida:** pasan una vez por tic, y aquí se reparten entre tres ranuras y se multiplican por seis. Con seis ranuras de verdad serían unos 50 ciclos por giro y ranura, no 100 (E).
- **Máximos.** La entrada llega a 684 ciclos. La salida, en la pasada con las dos frías y `contaminador-icache`, llegó una vez a 8 817. No se ha buscado de dónde salen.
- **Sin TCM, con las dos frías:** entrada 320, cadena 251, salida 320 y cuerpos 6 726. En la pasada con las cachés apagadas de esa corrida, 20 060 tramas salieron sin bajada fresca; con las cachés encendidas, ninguna. El testigo es acumulado, y por eso la línea de la última pasada dice 20 062.

**Lo que el resto del hub le impone al tic: los testigos** (2026-10-19, `carga_j2` con `transporte-tic`, `reloj-hub`, `sin-componer` y `ranuras-3`, sin TCM y con las cachés calientes; el árbol de este cambio). `tics_fuera_de_presupuesto` cuenta las entradas del tic con más de 60 µs de retraso (R-H2) y `latencia_plan_max_us` es la mayor espera del planificador desde que se pide hasta que arranca (R-H1). Son máximos y cuentas de toda la corrida, con sus tres pasadas.

| | retraso de entrada máximo | tics fuera de presupuesto | espera máxima del planificador |
|---|---|---|---|
| el J2 solo | 1 µs | 0 | 3 µs (4 con las dos cachés frías) |
| con el USB del instrumento (`con-usb`), sin cable | **9 µs** | 0 | 4 µs |

Con `con-usb`, `carga_j2` arranca el USB del instrumento con el mismo `atender` de `main.rs` (su lazo de 1 ms y el servidor MIDI) junto al J2. En esta corrida Windows no enumeró el dispositivo (el puerto USB de usuario de la Nucleo no estaba conectado al PC), así que es el USB sin tráfico: aun así el retraso de entrada máximo pasa de 1 a 9 µs, dentro de los 60 de R-H2. Qué lo causa (la interrupción del temporizador de `embassy-time` o la del OTG, que hoy van por encima del tic, o una sección crítica) no lo dicen los testigos. La medida con el puerto conectado y con tráfico está en el bloque siguiente.

**El USB con tráfico, medido** (2026-10-19, firmware `66b2b15`; `carga_j2` en la configuración de la ficha J, con `transporte-tic`, `reloj-hub`, `sin-componer`, `ranuras-3`, `j2-tcm` y `crc-tabla`, más `con-usb`). El puerto USB de usuario (CN8) va al PC, que enumera la placa como «SAM17 nucleo». `trafico_midi.py` manda notas encendidas y apagadas por la API MIDI de Windows desde que el firmware dice que el PC lo configuró hasta que acaba la medida, y la línea de esa conexión sale antes de que arranque el J2. Son máximos y cuentas de toda la corrida, unas 240 000 entradas del tic. `latencia_plan_max_us` cuenta ahora de pendiente a terminado (#456): no se compara con la tabla de arriba.

| | retraso de entrada máximo | tics de más de 10 µs | fuera de presupuesto (60 µs) | reloj anómalo | planificador, de pendiente a terminado | hilo libre con las dos cachés |
|---|---|---|---|---|---|---|
| el J2 solo | 1 µs | 0 | 0 | 0 | 29 µs | 931 ‰ |
| con el USB, sin tráfico | 1 µs | 0 | 0 | 0 | 35 µs | 924 ‰ |
| 1 000 mensajes MIDI/s | 9 µs | 0 | 0 | 0 | 39 µs | 921 ‰ |
| 5 000 mensajes MIDI/s | **15 µs** | 1 | 0 | **4** | 40 µs | 910 ‰ |

- **Ninguna entrada del tic pasa de los 60 µs de R-H2**, ni con 5 000 mensajes por segundo, unas cinco veces lo que cabe en un cable MIDI DIN. En ninguna corrida hay una trama atrasada, un plazo vencido ni una ranura muerta.
- **El reloj anómalo es una interrupción por encima del tic.** Al entrar, el tic lee seguidos el contador libre y el de TIM7. Si algo se cuela entre las dos lecturas, el instante de la actualización sale corrido y el reloj cuenta un periodo (§2.7), que es lo correcto cuando no se saltó ninguno (`periodos_saltados` 0). Al tic, en el nivel 1, solo lo interrumpe el nivel 0, donde hoy están el OTG y el temporizador de `embassy-time` (#443, punto 4). Como solo pasa con tráfico, lo más probable es el OTG; cuál de los dos no está medido.
- **Lo que el USB cuesta de CPU.** Con las dos cachés encendidas, el hilo libre baja de 931 a 924 ‰ sin tráfico (el lazo de 1 ms de `atender`), a 921 ‰ con 1 000 mensajes/s y a 910 ‰ con 5 000: del 0,7 al 2,1 % de un núcleo, con 1 ‰ de resolución. Con las cachés apagadas baja mucho más (de 684 a 538, 507 y 385 ‰), pero el instrumento no corre así.
- **Los 9 µs del USB sin cable de arriba no salen aquí sin tráfico (1 µs).** Cambiaron dos cosas a la vez: el J2 está en la TCM, y arranca 5 s después que el USB, cuando el PC ya lo enumeró. Cuál de las dos los quitó no está separado.
- **Lo que no dice.** Cuántos paquetes USB llegaron: Windows puede juntar varios mensajes en un paquete y la placa no cuenta lo que recibe, así que `trafico_midi.py` solo sabe que el driver aceptó todos los mensajes sin un fallo (150 000 en los primeros 30 s de la corrida de 5 000). Los máximos salen de unas 240 000 entradas del tic: algo más raro que eso no se ha visto.

**Los niveles de R-H1, en `fw`** (2026-10-19, el árbol de este cambio sobre `3c81a1f`; las mismas cuatro corridas que el bloque de arriba). embassy deja en P0, por encima del tic, todo lo que enciende sin que se le diga la prioridad: los canales del GPDMA1 y del HPDMA1 (en `init`), el temporizador de `embassy-time` (TIM12, también en `init`) y el USB (al arrancar el dispositivo). Ninguno aparece como un `set_priority` en el código. `usb::iniciar`, por donde arrancan `main` y todos los binarios del banco, los baja ahora al nivel 2, el del hub, y `j2_tic::lanzar` lee el NVIC y no arranca el tic si queda alguna interrupción habilitada por encima. Antes del arreglo, `carga_j2` con `con-usb` se paraba ahí: «la interrupción 68 está en 0x0», `HPDMA1_CHANNEL0`.

| | retraso de entrada máximo | tics de más de 10 µs | reloj anómalo | planificador, de pendiente a terminado | hilo libre con las dos cachés |
|---|---|---|---|---|---|
| el J2 solo | 0 µs | 0 | 0 | 32 µs | 931 ‰ |
| con el USB, sin tráfico | 3 µs | 0 | 0 | 32 µs | 925 ‰ |
| 1 000 mensajes MIDI/s | 6 µs (antes 9) | 0 | 0 | 34 µs | 922 ‰ |
| 5 000 mensajes MIDI/s | **4 µs (antes 15)** | 0 (antes 1) | **0 (antes 4)** | 34 µs | 910 ‰ |

- **Con 5 000 mensajes/s, ya no se cuela nada al entrar el tic**: el reloj anómalo pasa de 4 a 0. Ninguna entrada pasa de 10 µs, y en ninguna corrida hay una trama atrasada, un plazo vencido ni una ranura muerta.
- **Lo que cuesta el USB no cambia** (910 a 925 ‰, como antes). El planificador, que ahora queda por debajo del USB, se queda en 34 µs, contra los 12 ms de R-H1.
- **Queda un retraso de 3 a 6 µs con el USB, y sin él 0.** Con el USB por debajo del tic, eso es, lo más probable, una sección crítica del camino del USB, que enmascara todo. Encaja con los 5 µs por sección de R-H2, pero R-H2 no está medido directamente: ni cuál es la sección ni cuánto dura.
- **El muestreo de `perfil_pc` sigue en P0, y tiene que estar ahí:** muestrea dentro de las ISR. Usa el transporte del ejecutor, no `j2_tic::lanzar`, así que el aserto no lo ve.

**Las secciones críticas con el USB, medidas (R-H2)** (2026-10-20, el árbol de este cambio sobre `639cd86`; `carga_j2` en la configuración de la ficha J con `con-usb`, el mismo tráfico que arriba, y `secciones`). Con la feature `secciones`, la sección crítica de `critical-section` es la de `cortex-m` con un reloj: al abrir la más externa apunta el `DWT` y la dirección de vuelta de quien la abre, y al cerrarla anota cuánto duró en una tabla por sitio (`fw/src/secciones.rs`). La dirección se traduce a una línea de fuente con `rust-objdump -l` sobre el mismo binario. En cada pasada, la tabla cubre la segunda muestra de 5 s, la que vale, y se imprime al acabar la corrida. La sección más larga de cada pasada y quién la abre:

| | cachés apagadas | solo la I-cache | las dos cachés | las dos, frías (`contaminador-icache`) |
|---|---|---|---|---|
| con el USB, sin tráfico | 7,7 µs (TIM12) | 5,1 µs (TIM12) | 0,76 µs (TIM12) | |
| 1 000 mensajes MIDI/s | 7,7 µs (TIM12) | 5,1 µs (TIM12) | 0,77 µs (TIM12) | **3,4 µs** (TIM12) |
| 5 000 mensajes MIDI/s | **9,9 µs** (`schedule_wake`) | 4,7 µs (`schedule_wake`) | 0,76 µs (TIM12) | 3,0 µs (TIM12) |

Los sitios que salen, con lo que se repiten en 5 s a 1 000 mensajes/s:

- `_embassy_time_schedule_wake`, de `embassy-stm32` (`time_driver/gp16.rs`): `embassy-time` lo llama cada vez que una tarea espera un `Timer`. 10 000 veces: una por milisegundo del lazo de `atender` y otra por mensaje (30 000 con 5 000 mensajes/s, 5 000 sin tráfico).
- `TIM12`, la interrupción del temporizador de `embassy-time` (`on_interrupt`): unas 5 160 veces.
- La lectura de un endpoint OUT en `embassy-usb-synopsys-otg` (`lib.rs:1717`, que rearma el endpoint para el paquete siguiente): 5 000 veces, una por paquete. Como mucho 1,4 µs con las cachés apagadas y 0,47 µs con las dos.
- De `fw`, solo la de `secciones::reinicia`, una vez.

- **Los 3 a 6 µs del bloque de arriba son del temporizador de `embassy`, no del USB.** Las dos secciones largas son de `embassy-time` y de su driver de TIM12 en `embassy-stm32`. Dentro, recorren la cola de tareas que esperan, despiertan las vencidas y leen y escriben TIM12 varias veces: `now()` lee `CNT`, y `set_alarm` escribe `CCR`, reescribe `DIER` y vuelve a leer `CNT`. El USB solo las dispara más a menudo. La sección del OTG mismo es corta, y en `fw` no hay ninguna.
- **Con las dos cachés, R-H2 se cumple:** como mucho 0,77 µs, con tráfico y sin él, y 3,4 µs con las dos cachés desalojadas sin parar. Solo pasan de 5 µs con las cachés apagadas o con la I-cache sola, y el instrumento no corre así. Los 3 a 6 µs de entrada del bloque de arriba salen de la primera de esas pasadas: los testigos acumulan las tres y el máximo queda fijado en la primera.
- **Sin las dos cachés, el máximo cambia de un binario a otro.** Las corridas de la tabla guardaban PRIMASK en un `bool`. La versión final guarda el `u32` entero, como la de `cortex-m`. Con ella, la corrida de 1 000 mensajes/s repite con las dos cachés (0,78 µs, TIM12) y se mueve en las otras dos pasadas: 7,4 µs con las cachés apagadas y 6,2 µs con la I-cache sola, las dos en `schedule_wake`.
- **El margen con las cachés frías es de 1,6 µs, medido desde la RAM.** El banco corre desde la AXISRAM. El instrumento arranca de XSPI, donde un fallo de la I-cache cuesta más, y el código del temporizador no está en la TCM: `j2-tcm` solo lleva el tic, el planificador y la recuperación. En el instrumento, con la caché fría, estas dos secciones pueden pasar de 5 µs. No está medido; es lo mismo que queda abierto para el tic (R-H4).
- **Cada mensaje llega en su propio paquete.** La lectura del OTG corre una vez por mensaje, a 1 000 y a 5 000 mensajes/s: Windows no los junta. Con el contaminador y las cachés apagadas la placa no da abasto, y el PC solo logra mandar unos 3 600 a 4 300 por segundo, sin un fallo.
- **El reloj alarga lo que mide.** La tabla se lleva con las interrupciones enmascaradas: buscar la fila no entra en la cifra, pero retrasa al tic. Con `secciones`, la entrada del tic llega a 10 µs con 5 000 mensajes/s (4 sin la feature, arriba). Con las dos cachés frías llega a 21 µs, con 60 tics de más de 10 µs; la misma corrida sin `secciones` da 6 µs y ninguno. Para la cláusula de entrada de R-H2 valen las corridas sin `secciones`.
- **Lo que no ve.** `cortex_m::interrupt::free` no pasa por `critical-section`. En `fw` hay cuatro, todas de la recuperación (`escala`, `pide_escalada`, el reset del SPI y la lectura de la cuenta de 64 bits del tic), y en `carga_j2` la recuperación no corre (`latencia_rec_max_us` 0). La sección de la escalada está medida aparte (671 ns, más abajo). Los crates de `embassy` que usa el firmware no tienen otro `interrupt::free` ni `cpsid` (los de `flash` son de otras familias, y el del ejecutor, de AVR). Y son 5 s por pasada: lo que pase menos que eso no se ha visto.

**Las filas del tic en `carga_j2.csv` (§5.2 a)** (2026-10-20, firmware `1d62576`; `carga_j2.py --tic`, que corre `carga_j2` en la configuración de la ficha J, con `transporte-tic`, `reloj-hub`, `sin-componer`, `ranuras-3`, `j2-tcm` y `crc-tabla`, más `perfil` y `tic-fino` para la pasada de la salida). El CSV lleva dos columnas nuevas, `transporte` y `regimen_cache`, y las tres filas del ejecutor a 64 MHz quedan como `ejecutor` y `caliente`. Las filas del tic salen de la pasada de la salida, una por régimen: `caliente` sin tocar las cachés, y `fria` con las dos invalidadas tras cada hueco, así que cada tic entra con las dos frías. La cifra es la de la ficha J: la entrada, el cuerpo del tic, la cadena, el cuerpo del planificador y la salida, en medias por tic y repartidas entre las tres ranuras. El medidor del hilo no entra, y su columna queda vacía. Ciclos:

| | entrada | tic | cadena | planificador | salida | por tic | por giro y ranura | un núcleo, con seis ranuras |
|---|---|---|---|---|---|---|---|---|
| caliente | 60 | 3 695 | 44 | 3 227 | 35 | 7 061 | 2 354 | 14,1 % |
| fría | 140 | 3 742 | 121 | 3 317 | 35 | 7 355 | **2 452** | **14,7 %** |

- **La que cuenta es la fría: 2 452 ciclos por giro, por debajo de los 2 500 del límite.** `recuperacion_j2_budget.py` y `carga_hub_budget.py` toman, de las filas del tic con las cachés del hub a 800 MHz y 8 kHz, las de más ranuras; de cada régimen, la última; y la peor de las dos. La fila del J2 en el censo sale de ahí y deja de llevar la cifra fija de la ficha J. Sigue como ESTIMADO, porque la columna de seis ranuras es aritmética sobre la medida con tres. La pasada de optimización sigue aparcada: no pasa del 15,0 %.
- **Son 23 ciclos más que los 2 429 del 19-10.** Aquella cifra juntaba dos corridas: los cuerpos, la entrada y la cadena venían de la de `contaminador-icache`, y la salida, de la pasada fría de la otra, porque con el contaminador la salida carga además lo que el hilo tarda en traer su propio código. Aquí todo sale de una pasada, y en ella las dos cachés están vacías al entrar cada tic. El contaminador recorre 64 KB por vuelta del hilo, y entre dos tics no siempre la termina.
- **Por el DWT, los cuerpos fríos cuestan un 2 % más que los calientes** (7 059 contra 6 922 ciclos por tic, un 1,98 %; en la pasada fría del 19-10, un 2,05 %). Es justo el tope de la ficha H para los datos de solo lectura que quedan en la AXISRAM2: «la fila con las dos cachés frías no pasa de la caliente en más de un 2 %». Con el contaminador era un 1,0 %. El mismo día ese 2 % pasó a la DTCM y a una puerta (el bloque siguiente).
- **Dos corridas con el mismo código** (`8f41065` sin anotar, y `1d62576` la anotada): 2 353 y 2 452, y 2 354 y 2 452.

**El patrón del juez en la DTCM, y la ficha H como puerta** (2026-10-20, firmware `646a97a`, la misma configuración). Lo que el código de la ITCM nombra en `.rodata` de la AXISRAM2, leído del desensamblado: las ubicaciones de los pánicos, que solo se leen si el pánico ocurre; los `RccInfo` de `resetear_por_rcc`, que solo corren en el reset de una ranura; y el patrón de 25 bytes con el que el juez del banco compara cada subida (`juez_del_banco`, por `memcmp`). Solo el último está en el camino de cada tic. Como `const` vivía en el `.rodata`; ahora el juez lo lee de `PATRON_JUEZ`, un static en la DTCM (+28 B de DTCM, la ITCM igual, y `tcm_cierre.py` sin llamadas fuera). Ciclos por tic:

| | entrada | tic | cadena | planificador | salida | por giro y ranura | cuerpos por giro y ranura | un núcleo, con seis ranuras |
|---|---|---|---|---|---|---|---|---|
| caliente | 60 | 3 695 | 44 | 3 227 | 35 | 2 354 | 2 307 | 14,1 % |
| fría | 140 | 3 742 | 120 | 3 222 | 33 | **2 419** | 2 321 | **14,5 %** |

- **El planificador frío baja 95 ciclos por tic, hasta lo mismo que el caliente.** Toda su diferencia en frío era la línea de caché del patrón. El cuerpo del tic, con el patrón fuera, sigue 47 ciclos por encima en frío; qué lo causa no está medido (la pila de las excepciones sigue en la AXISRAM2, y dónde va la declara el hub, ficha H).
- **Por el DWT, los cuerpos fríos pasan de los calientes un 0,61 %**, contra el 1,98 % de `1d62576`. La fila fría del censo baja de 2 452 a 2 419 ciclos por giro, del 14,7 al 14,5 % de un núcleo.
- **`carga_j2.csv` guarda los cuerpos** en la columna `cuerpos_por_giro`: el tic más el planificador por giro y ranura. Las filas de `1d62576` la llevan de su misma corrida (2 307 y 2 353).
- **`recuperacion_j2_budget.py` comprueba la ficha H:** de las últimas filas del hub, los cuerpos de la fría no pasan de los de la caliente en más de un 2 %. Si pasan, sale en rojo; sin los dos regímenes, con firmwares distintos o sin la columna, es HUECO.
- **El patrón es del banco.** El juez del hub comparará otra cosa, y lo que lea en cada tic tiene que estar también en la DTCM. Esta puerta lo verá cuando haya filas del hub.

**Las fichas B y C en `fw`** (2026-10-19, firmware `0186c68`; acta del 19-10, tercera firma; #455). `Vencida` 200 y `Reiniciando` 112 periodos. El presupuesto concede 6 escaladas por segundo con 1 ms entre dos, y la que llega antes se aplaza: la recuperación lee la cuenta de 64 bits del tic, pide al presupuesto y publica el tic en que vence en una sola sección crítica, y el tic la deja pendiente al llegar. `lanzar` asevera las dos condiciones de la ficha C.

- **`tic_recupera` con la escalada** (`inyeccion,reloj-hub,ranuras-3,sin-esclavo,escalada`): todas las fases en verde. **G, la escalada aplazada:** dos escaladas forzadas a la vez, en las ranuras 2 y 3. Se concede una y la otra se aplaza; el tic despierta a la recuperación una vez, y la ranura 3 sale sin morir y sigue sellando (`escaladas=1`, `aplazadas=1`, `despertadas=1`, `denegadas=0`, ninguna muerta). **E** pasa a siete escaladas en la ranura 3, una cada 30 ms: seis concedidas y la séptima denegada, y la ranura muere por su cota. **C:** diez escaladas, ninguna denegada.
- **`tic_recupera` con el esclavo real** (`inyeccion,reloj-hub`): 20 de 20 comprobaciones. La ranura de D tarda ahora unos 25 ms en morir (`Vencida` 200), y la fase espera 40 ms en vez de 30.
- **`tic_estres`** (`inyeccion,secuencia,reloj-hub,pines-medio`), las cuatro fases en verde: ninguna bajada ni subida rota, repetida ni atrasada, ninguna ranura muerta, y 14 533 plazos vencidos con 14 533 recuperaciones.
- **Los testigos de R-H1 cuentan ahora de pendiente a terminado**, en el planificador y en la recuperación (`latencia_rec_max_us` es nuevo). En `tic_estres`, con los golpes de P3 al azar, el planificador llega a 280 µs y la recuperación a 9 µs. En `carga_j2`, el del planificador pasa de 3 µs (hasta que arrancaba) a 28 µs: cuenta también su pasada, que con las cachés apagadas dura de media unos 25 µs.
- **Lo que cuesta.** En la configuración de la ficha J (TCM, las dos frías, CRC por tabla, tres ranuras), tic y planificador suman 2 330 ciclos por giro y ranura, contra 2 338 de `main` medido en la misma sesión: dentro del ruido. La cifra de la ficha J (14,6 %) no cambia. En la TCM, `carga_j2` con `ranuras-3` y sin la tabla ocupa 8 928 B de ITCM y 4 784 B de DTCM, 476 y 136 B más que `main`, y `tcm_cierre.py` no encuentra llamadas fuera de la ITCM.
- **No se ejerce en placa:** una aplazada cuyo instante cae en la vuelta del contador de 32 bits (eso lo prueba el modelo, `la_vuelta_del_contador_del_tic_no_cambia_nada`), ni un canal que de verdad no pare: las escaladas siguen siendo forzadas.

**Resistencia** (`tic_banco`, 8 kHz, 800 MHz, cachés y región; esclavo real en SPI4, `verifica-bajada`; pines del J2 a `VeryHigh` y el patrón regular de siempre). 600 s, firmware `7bda894`: **4 799 999 giros, 4 799 999 subidas buenas, 4 799 999 tramas vistas por el esclavo y 4 799 999 bajadas con el contenido correcto, ninguna mala**, con cero plazos vencidos, subidas malas, tramas cortas, tics tardíos o fundidos, eventos o subidas perdidos, recuperaciones y ninguna trama sin bajada fresca; el retardo máximo del tic al entrar fue de 0 µs. Dos corridas anteriores de 600 s (`0ae706a` con el árbol sucio y `13d8d6b`) dieron lo mismo. A 1 kHz (`mil-hz`), 20 s (`13d8d6b`): 19 999 giros, subidas, tramas y bajadas buenas, todo lo demás a cero. `verifica-bajada` tiene su control negativo: con el patrón de la bajada corrompido a propósito, el esclavo cuenta 0 buenas y 159 999 malas en 20 s (`13d8d6b`). **Esta comprobación de contenido vale para el patrón regular y para nada más** (ver «Qué contenidos maltrata el enlace del banco»); la integridad con contenido arbitrario es la de «Integridad bajo preempción».

**Recuperación** (`tic_recupera`, esclavo real, una ranura, firmware `7bda894`). Un SPI envenenado, en microsegundos desde el `CSTART` de la transferencia envenenada: el tic la da por vencida a los **123**, la recuperación entra a los 125, resetea el SPI a los 126 y lo deja configurado a los 127, publica `ReinicioHecho` a los 131, y la primera trama buena sale a los **249**. El `CS` queda sin manejar por el reset **1,2 µs** con una ranura y 1,5 µs con tres (de `rcc::disable` a la reescritura de `CFG1`), y hasta que vence el módulo vio el `CS` abajo unos 95 µs sin reloj (por cuenta, no medido: el maestro se queda sin dato tras 24 bytes a 6,25 MHz, o sea a los 31 µs). El hueco con el `CS` arriba antes de la siguiente trama es de 122 µs. El techo de recuperación del papel v2 para un `NADA` era 395 µs. Mil incidentes seguidos, uno cada 4 ms: 1 000 plazos, 1 000 recuperaciones, ninguna ranura muerta, ninguna subida mala, **el esclavo vio exactamente 1 000 tramas cortas y 30 558 bajadas buenas y ninguna mala**. Un error del DMA (`USEF`, fase F; la rama `error_dma` del tic): 1 error, 1 plazo vencido, 1 recuperación, ninguna ranura muerta, los giros siguen. Diez escaladas **forzadas** del GPDMA1 (`fuerza_escalada`) con las vecinas en vuelo (tres ranuras, sin esclavo): 10 escaladas, **10 plazos vencidos en cada una de las tres ranuras**, 30 recuperaciones, ninguna muerta, las tres siguen girando; la sección crítica de la escalada dura **650 ns** y la escalada entera, 2 µs. La rama que escala porque un canal no para en 25 µs no ha corrido: en el banco no hay forma de atascar un canal de verdad. Con la recuperación inhibida, la ranura pasa a `Muerta` y deja de sellar (el sello del IWDG se queda quieto) mientras las vecinas siguen sellando.

**Recuperación con el presupuesto de escaladas y el incidente** (2026-10-19, `tic_recupera`, firmware `5963841`; papel v3, K1 y K4: 3 escaladas por segundo, y el plazo que vence por la escalada de otra ranura no puntúa). Con las escaladas de la fase C a 30 ms, como el 17-10, el presupuesto concede tres, deniega la cuarta y la ranura 0 muere: la fase F corre entonces contra una ranura muerta y falla entera; por eso la fase C va a 400 ms. Tres ranuras, sin esclavo: **10 escaladas, ninguna denegada**, 10 plazos propios en la ranura 0 y, en cada vecina, **10 plazos ajenos y ningún plazo propio** (el 17-10 eran 10 plazos vencidos que puntuaban en cada una), 30 recuperaciones, ninguna muerta, las tres siguen girando; sección crítica 671 ns, escalada entera 2 µs. **La escalada denegada, en placa** (fase E, ranura 3, con la ventana vacía): 3 escaladas concedidas y **1 denegada**; la denegada resetea los dos canales sin publicar `ReinicioHecho`, la ranura 3 pasa a `Muerta` por su cota, y la ranura 2 sigue sellando con 3 plazos ajenos y ninguno propio. A, B, D y F pasan como el 17-10, con esclavo real y sin él (47 comprobaciones, ninguna falla); los instantes de A se mueven a lo sumo 1 µs (vence a los 123, primera trama buena a los 249). Sigue sin correr la rama que escala porque un canal no para en 25 µs.

**Estrés: una interrupción de P2 que acapara la CPU** (`tic_banco --features acapara,sin-esclavo`). Cada fase son 300 golpes de `D` µs, uno cada unos 10 ms y con la fase respecto al tic repartida; el planificador está en P3 (por debajo del golpe) y el tic en P1 (por encima). Va sin esclavo: el del banco es una tarea de P2 y los golpes le pegan a él también. Lo que se pierde en 300 golpes:

| `D` (µs) | tramas sin bajada fresca | giros perdidos por golpe | subidas perdidas |
|---|---|---|---|
| 0, 50, 100 | 0 | 0 | 0 |
| 150 | 65 | 0,22 | 61 |
| 200 | 179 | 0,60 | 176 |
| 300 | 424 | 1,4 | 300 |
| 500 | 904 | 3,0 | 300 |
| 1 000 | 2 102 | 7,0 | 300 |
| 3 000 | 6 904 | 23 | 300 |

El tic no se entera (cero tics tardíos hasta con 3 ms), no se pierde ningún evento, no vence ningún plazo y no muere ninguna ranura: el planificador se queda atrás y la ranura espera una trama que no llega. Cada golpe cuesta unos (`D` − 120) / 125 giros en cada ranura y una subida; **hasta ~100 µs de retención de P2 no cuesta nada**. El cruce con un fallo es otra cosa: una ranura que vence mientras el planificador está retenido más de lo que dejan sus cotas muere (la cota de espera, abajo).

**La cota de espera contra una retención de P2** (`tic_cota`, una ranura, esclavo real, firmware `7bda894`). `Vencida` y `Reiniciando` dan la ranura por muerta si pasan sus cotas sin que la recuperación arranque o acabe, y una ranura muerta deja de sellar al IWDG del hub. El planificador y la recuperación van por debajo de USB y pantalla (P2): una retención de P2 que coincida con un cuelgue puede matar la ranura. Con las cotas del papel v2 (2 y 4 tics) la ranura **sobrevive a 300 µs de retención y muere con 400**. Con las de hoy, **100 tics (12,5 ms) en `Vencida` y otros 100 en `Reiniciando`**, sobrevive a 12 ms y muere con 14 ms; las dos suman 25 ms, la mitad de lo que el módulo aguanta sin tramas. El requisito que sale para el hub: una ISR de P2 que retenga al planificador más de ~12 ms justo cuando una ranura vence, la mata.

**Integridad bajo preempción** (`tic_estres`, 8 kHz, una ranura con esclavo real, 25 bytes por marco, cachés y región, `pines-medio`, firmware `7bda894`). Cuatro fases de 60 s, 1 894 419 marcos numerados en total, 11 570 cuelgues y 2 963 errores del DMA provocados, 14 533 recuperaciones. **Ninguna bajada rota, repetida ni atrasada y ninguna subida rota, atrasada ni futura, en ninguna fase**, y ninguna ranura muerta:

| fase | giros | plazos (= recuperaciones) | errores del DMA | sin bajada fresca | subidas perdidas | tramas cortas del esclavo |
|---|---|---|---|---|---|---|
| 0, sin nada | 480 412 | 0 | 0 | 0 | 0 | 0 |
| 1, golpes de P3 | 472 106 | 0 | 0 | 8 300 | 7 842 | 0 |
| 2, cuelgues y errores del DMA | 465 414 | 7 500 | 1 530 | 0 | 0 | 5 970 |
| 3, golpes, cuelgues y errores | 457 952 | 7 033 | 1 433 | 8 403 | 7 993 | 5 600 |

Todo cuadra con lo provocado: cada cuelgue es una trama corta que el esclavo cuenta, cada cuelgue o error del DMA es un plazo con su recuperación, y cada plazo y cada subida que el planificador no llega a leer es un número que el juez ve saltado. Los golpes de P3 no matan ninguna ranura: solo cuestan tramas sin bajada fresca (el tic no arma sin ella) y subidas perdidas. La corrida larga (`larga`, 4 × 150 s, firmware `7bda894`): 4 727 452 marcos compuestos, 4 686 899 giros, 36 551 recuperaciones, y otra vez cero bajadas rotas, repetidas o atrasadas, cero subidas rotas, atrasadas o futuras y ninguna ranura muerta. Límites: los golpes van a P3 y no a P2 porque a P2 también le pegarían al esclavo del banco (que es una tarea de P2); el cruce de un golpe de P2 con un fallo es `tic_cota`; hay una sola ranura con esclavo, así que la concurrencia de tres ranuras solo la ejerce `tic_recupera`, sin contenido que comprobar.

**Qué contenidos maltrata el enlace del banco** (`tic_contenidos`, 2 500 tramas de cada contenido, firmware `7bda894`). Con los pines del J2 a `VeryHigh` (lo que se ha usado siempre), el cableado de puentes de la Nucleo rompe los marcos de apariencia aleatoria, siempre los mismos. La tabla es de la bajada; la subida con marcos numerados (`tic_estres` a `VeryHigh`, antes de ponerle la guarda) llegaba rota igual:

| pines del J2 | MISO del esclavo | contenidos que llegan enteros |
|---|---|---|
| `VeryHigh` | `PATRON_SUBIDA` (conmuta, `0xA5 ^ i`) | **4 de 16**: ceros, unos (el byte 0 es el número del contenido), `0x00`/`0xFF` alternados y un `0x5A` en el byte 12 sobre ceros |
| `VeryHigh` | ceros (`subida-quieta`) | **16 de 16** |
| `Medium` | `PATRON_SUBIDA` | **16 de 16** |
| `Medium` | ceros (`subida-quieta`) | **16 de 16** |

(Los contenidos 4 y 5 llegan con el byte 0 cambiado —el 4 pasa a 6 y el 5 a 7— y el contador los apunta en el 6 y el 7.) No cambió con la D-cache apagada ni con el SCK a la mitad (3,125 MHz): corridas de banco con features que ya no están en el repo. Lo que hay detrás no se midió con osciloscopio. Lo que encaja: la rotura necesita actividad a la vez en MOSI y en MISO con bordes rápidos; con los patrones regulares de antes (`0x5A ^ i` abajo, `0xA5 ^ i` arriba, complementarios bit a bit) los dos conmutan en oposición y el efecto no aparecía, y con uno de los dos quieto desaparece. La hipótesis es acople entre hilos adyacentes que mete flancos de reloj de más en el esclavo.

Consecuencias: (1) **las comprobaciones de contenido de antes solo valían para el patrón regular**: las corridas de 600 s y la de 1 kHz comparaban `PATRON_BAJADA`, y lo hacían bien, pero no probaban nada sobre contenido arbitrario; la integridad con contenido arbitrario es la de `tic_estres`. (2) `tic_estres` va con `pines-medio` y no compila sin él (ni sin `pines-bajo`). (3) Para el instrumento: el paso 2 del J2 (34,5 MHz) necesita `VeryHigh`, y con el cableado de puentes ese ajuste rompe el enlace; el arnés real (terminación en serie, retornos de masa) es un requisito, y las pruebas de enlace usan contenido que no sea un patrón regular.

**Lo que no está medido**: seis ranuras reales (SPI3 y SPI6 piden otra función alterna que `Ranura::nueva` no soporta; el banco tiene tres físicas); una escalada real (la rama que escala porque un canal no para en 25 µs no ha corrido, no hay forma de atascar un canal en el banco, y `programa()` no reescribe el estado global del GPDMA: `SECCFGR`, `PRIVCFGR`, `RCFGLOCKR`); un tic tarde (el banco corre desde la RAM; el instrumento arranca de XSPI y una I-cache fría añade tiempo al texto de las ISR, R-H4); el `DWT` sin sonda (tres plazos de seguridad lo leen y solo se han ejercido bajo `probe-rs`); el juez real, el compositor real y la cabecera; el hub (USB, pantalla y MIDI, y los niveles de NVIC, R-H1 a R-H6); la subida con un periodo más de latencia contra `latencia_mano_budget.py`; el `CS` visto con un analizador lógico (los tiempos de arriba son marcas del `DWT`, y se supone que el `CS` sube en cuanto el SPI suelta el pin); el cable del banco con un osciloscopio; y ninguna cifra de un módulo de verdad.

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
