# La lista del bring-up

Esto se escribió **sin placa**. Todo lo que hay en `core` está probado con
`cargo test`, y el binario compila y enlaza para `thumbv8m.main-none-eabihf`
—el target del Cortex-M55 del N657, el mismo que traía el RP2350— pero eso no
demuestra que arranque, ni que enumere, ni que conteste.

Esta es la lista del día que llegue la placa, **en orden**: cada línea supone
que la anterior salió bien.

## Antes de enchufar nada

**Cuál placa.** La **NUCLEO-N657X0-Q**, firmada en el acta del J2 del
2026-09-11 (#231): el mismo STM32N657X0H3Q en VFBGA264 que eligió el censo,
a un tercio del precio de la Discovery, y con los dos extremos del J2 en un
solo conector (§«El J2 en la Nucleo», abajo). La STM32N6570-DK entra el día
que haya fecha de pedido de PCB con N657 a menos de ocho semanas, por la
pantalla de 800×480 en el LTDC, la PSRAM y la cámara.

**Comprobar `memory.x` contra la placa.** El N657 **no tiene flash interna**:
`FLASH` y `RAM` son dos tramos de la misma AXISRAM2 y el binario lo carga ahí
el depurador, con la placa en *development boot* (BOOT1 arriba). El arranque
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
cargo run --release          # probe-rs con el STLINK-V3EC de la placa
```

**BOOT1 arriba antes de nada.** Con BOOT1 abajo la ROM se va a serial boot
y `probe-rs` no encuentra a nadie escuchando: el LED rojo de PG10 parpadea
rápido. En development boot se queda fijo (AN5967 §11.2). `ARRANQUE.md`
tiene los tres caminos con su página.

**`--release` no es una preferencia: es la unica que enlaza.** Con
`defmt` y embassy, el binario de depuracion se pasa **48 KB** de los 256 K que
`memory.x` reserva para el codigo, y `rust-lld` lo dice con tres secciones que
se solapan. Si hace falta depurar sin optimizar, se sube `FLASH` en
`memory.x` — pero entonces los 768 KB de abajo dejan de ser contiguos y el
framebuffer de 800x480 pierde su banco.

Por `defmt` tiene que salir:

```
SAM17: el cerebro arranco, protocolo v1
39 pines en el mapa
sin descubrimiento todavia: 27 parametros, todos de medida
```

**Si no sale nada**, en orden: la configuración de alimentación (arriba), y
después el reloj de referencia del PHY de USB, que tiene que ser 24 MHz
exactos y sale de PLL4 → IC15 (`usb::configuracion()`, con la cuenta y su
página). Enlazar no es arrancar.

## 2. Enumera

El sistema operativo lo ve como dispositivo MIDI con nombre **SAM17 nucleo**,
VID `0x1209` y PID `0x0017`.

## 3. `HELLO` da la vuelta

**Este es el momento en que el instrumento contesta de verdad por primera vez.**
Manda el SysEx de `HELLO` y espera `HOLA { version: 1 }`.

El sobre es `F0 7D <datos empaquetados a 7 bits> F7`, y el mensaje son la
etiqueta `0x01` más la versión en `u16` little-endian. El troceo en paquetes
de 4 bytes lo hace el driver MIDI del sistema.

## 4. `DESCRIBE` vuelve entero

Tienen que llegar **27 sobres**, uno por parámetro: las 24 bandas de Bark, el
pico, su exceso y la sonoridad. Con sus nombres y sus unidades.

Si llegan menos, sospecha del troceo largo antes que del servidor: 27 sobres
seguidos es lo primero que ejercita el buffer de verdad.

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
- **(1) es el repro de jake-taf tal cual**: embassy sin driver propio, 100 kHz,
  modo 0, `CS` por GPIO en PA3, `TSIZE = 0` y `blocking_read` de 8 bytes en
  bucle. Una hora da 98 % de potencia contra el extremo suave del hilo (un
  cuelgue cada ~900 s).
- **Pero el `f_sck` no van a ser 100 kHz, y la tercera línea lo dice.** El
  `compute_baud_rate` de embassy reparte por tramos y con el kernel en HSI 64 la
  razón 640 cae en el último, `/256` → **250 kHz**, que es el divisor más grande
  que hay. No invalida el repro —la condición de la errata es «system clock much
  faster than SCK» y 250 kHz sigue tres órdenes por debajo del núcleo— pero la
  tasa que se mida **no es comparable byte a byte** con la de jake-taf. Anótalo
  con la medida.
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
T_SCK, **15 min cada uno** (el acta: 15 min contestan p < 4,2e-7 al 95 % para la
tasa por armado). Tramas de 25 bytes a 8 kHz, al piso de 10 MHz, con el esclavo
activo. Por punto:

```
barrido,retardo_cuartos=R,giros=G,plazos_vencidos=P,eot_tardios=E,subidas_malas=S,escaladas=X,tramas_cortas=C
```

`escaladas` y `tramas_cortas` son **deltas del punto**, no totales, para que los
seis se comparen entre sí. Al terminar los seis se queda en 4 —el de
producción— para siempre, publicando un punto más cada 15 min.

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
no el pedido: con 10 MHz pedidos y el kernel en HSI 64 son **8**. La segunda
tanda, al peldaño 2 (34,5 MHz), cambia `F_SCK_HZ` en el binario y se dice sola en
esa columna.

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
`DefaultHandler`. Medido el 2026-09-18 en los cuatro: sale propia, y la entrada
del vector apunta ahí (`rust-objdump -s -j .vector_table`). Lo mismo vale para
`SPI5`, `EXTI11` y `GPDMA1_CHANNEL0..3` en los binarios que los atan: los que no
los atan los dejan en `DefaultHandler`, y eso también es correcto —
`control_positivo` no usa ninguna ISR del SPI.

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
implementado**: son dos constantes de `src/j2_esclavo.rs` y el `bind_interrupts!`
del binario.

### Tres cosas que embassy no decide por nosotros

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
