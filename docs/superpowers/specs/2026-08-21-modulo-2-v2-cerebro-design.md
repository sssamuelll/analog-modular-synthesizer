# Módulo 2 v2 «El cerebro» — la placa del núcleo digital

> Sucede al módulo 2 v1 (Raspberry Pi 3B+ + AD5686R + LCD 16×2), marcado
> **SUPERADO** en su propio README el 2026-08-17. Materializa en cobre el
> contrato que ya está escrito y en verde en [`software/nucleo/`](../../../software/nucleo)
> —183 tests, sin haber tocado una placa— y ejecuta la lista que
> [`2026-08-17-nucleo-digital-design.md`](2026-08-17-nucleo-digital-design.md)
> §10 dejó explícitamente para *«la spec siguiente»*.
>
> Disuelve el issue **#22** (la congestión que dejó 17 redes al aire eran las
> seis líneas del LCD, los cuatro botones y la cabecera del Pi). Cierra el
> hueco del issue **#111**. Consume **#59**, **#60**, **#81**, y le entrega el
> **#86** al bring-up.
>
> **Revisión del 2026-08-21**, tras auditoría independiente. Lo que cambió y
> por qué está marcado en el texto, no borrado: el dueño del +5 V (§9.1), la
> tabla de estado de arranque (§4.3), la protección contra back-drive en las
> líneas que el cerebro maneja (§4.1), los conectores de panel —que son nueve,
> no once, y a los que les faltaba la cabeza local (§10)—, el margen de caída
> del riel de 10 V (§5), los cuatro cuadrantes del USB (§6.1), el `EN` del
> interruptor del host (§6.2), el `RESET` del mux (§8), y la puerta
> `check_pinout.py`, que estaba definida de una forma que la volvía una
> tautología (§11). Abrió los issues **#143** a **#152**.

## 1. Objetivo

**La placa que manda números.** Reparte voces, cronometra los cuatro
osciladores por hardware, habla con el mundo por cuatro puertas —USB device,
USB host, MIDI DIN y el puente inalámbrico—, sincroniza con hardware ajeno por
clock y reset, y es la raíz del árbol I²C por el que se descubre qué módulos
hay conectados.

**Objetivo medible:** que el binario que hoy solo enlaza —`fw` compila y enlaza
para `thumbv8m.main-none-eabihf`— **arranque, enumere y conteste** sobre esta
placa; y que `core/src/pinout.rs` —hoy 39 pines declarados como propuesta, y
que esta placa hará crecer (§12.14)— deje de ser una propuesta. Con una
precisión que §11 desarrolla y que conviene no perder: **una puerta automática
puede impedir que la propuesta sea imposible, pero solo el bring-up la
convierte en hecho.**

**Lo que esta placa no hace, y es a propósito:** no tiene entrada de audio, no
lleva DAC y no saca CV. §5.0 y §7.4 de la spec del núcleo no dejan excepción —
la medida del sonido la hace el módulo 4 y llega convertida en números por el
J2. El cerebro no ve un voltaje ni para oír.

## 2. Decisiones fijadas (con Samuel, 2026-08-21)

1. **El cerebro entero de §10 en un solo spin.** Ocho ranuras J2, mux I²C, USB
   de doble rol, DIN aislado, clock y reset con entrada y salida, pedal
   analógico, cabeza local, cadena WS2812 y puente inalámbrico. Se acepta a
   sabiendas que la mitad no se puede probar hasta que existan los módulos 4-7:
   lo caro es el segundo ciclo de fabricación, no los pads de más.
2. **Conectores de tamaño completo, y el ancho el que pida.** DIN-5, pedal de
   6,35 mm, USB-A para el host, USB-B para el device. Se enchufa lo que haya
   sin adaptador. El ancho sale de `panel_budget.py` (§10), no de una
   estimación.
3. **Aislador USB en la placa.** El instrumento es Clase I con tierra, así que
   el lazo con la masa de la computadora existe de verdad. Se corta aquí.
   Cierra la mitad del issue #60 que decía *«se decide con la caja»*.
4. **El puente inalámbrico lleva conector U.FL, no antena en la PCB.** Lo que
   se compra no es cobertura: es que el módulo **deje de exigir un canto de
   placa con keepout** y se pueda colocar donde quepa. La antena sale del metal
   por un pigtail; por defecto **adhesiva por dentro del acrílico trasero**
   —cero agujeros, cero pieza que se parta en una mudanza— y el SMA de mamparo
   en el panel queda como variante que no toca la placa.
5. **Una sola placa, con los jacks soldados a ella**, y panel de aluminio
   delante. Es el patrón del módulo 3, verificado ahí. La PCB de panel y la
   mecánica de los jacks siguen fuera de alcance, igual que allá.
6. **Los `TUNE_OUT` van cableados en una sola ranura.** Esto no es una decisión
   nueva: §5.3 de la spec del núcleo ya vio la trampa —*«serían cuatro líneas
   de afinado por cada ranura capaz de llevar un VCO: con 8 ranuras, 32 pines
   solo para eso»*— y la resolvió mandando a los módulos de más voces a medir
   sus propios osciladores y reportar por `MISO`. La placa solo obedece.

## 3. Bloques

| Bloque | Qué es | De dónde sale la obligación |
|---|---|---|
| **Micro** | RP2350B, QFN-80, 10×10 mm. Flash QSPI externa, cristal, BOOTSEL y RUN | Núcleo §5.3: ~37 GPIO contra los 30 del A |
| **Enlace J2 ×8** | Ocho IDC 2×6, 3,3 V. SPI compartido + `CS` propio + canal propio de I²C + 2× `GNDD` | Núcleo §10; contrato congelado por el módulo 3 |
| **Mux I²C** | 8 canales, uno por ranura | Núcleo §3.5: todas las EEPROM contestan en 0x50 |
| **Afinado** | 4 entradas al PIO, ya recortadas por el 74HC14 **del módulo 3** | Núcleo §5.1 |
| **Gates ×4** | 0/10 V activo alto, cable propio al ADSR | `architecture-poly.md` §4 |
| **WS2812** | El dato, y el +5 V de la cadena **con su medida de corriente** (§9.1) | `architecture-poly.md` §4, §7; issues #104, #151 |
| **Cabeza local** | 4 dígitos + encoder con pulsador + LEDs de estado | Núcleo §5.2 |
| **USB device** | USB-B, **aislado** | Núcleo §4.2; issue #60 |
| **USB host** | USB-A por PIO-USB, con interruptor de carga limitado | Núcleo §5.3 |
| **MIDI DIN** | In y out, DIN-5, con optoacoplador en la entrada | Núcleo §5.3 |
| **Clock / reset** | Cuatro Thonkiconn de 3,5 mm, in y out | Núcleo §5.3 |
| **Pedal** | Jack de 6,35 mm a entrada analógica | Núcleo §2.2 y §5.3 |
| **Puente** | Módulo pre-certificado con U.FL, por UART | Núcleo §4.2, §10 |
| **Telemetría** | EEPROM de identidad, TMP1075, test points rotulados | Patrón de instrumento (módulo 3 §8) |

## 4. El enlace J2 — ocho ranuras y un bus compartido

El conector y sus posiciones están **congelados** por el módulo 3 y no se tocan:

| 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| `SCLK` | `GNDD` | `MOSI` | `MISO` | `CS` de la ranura | `GNDD` |

| 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|
| `SDA` | `SCL` | `TUNE_OUT_1` | `TUNE_OUT_2` | `TUNE_OUT_3` | `TUNE_OUT_4` |

SPI modo 1, ≤10 MHz, `CS` abajo durante los 72 relojes de la trama entera.
Ocho ranuras: módulos 3, 4, 5, 6, 7, los futuros 8 y 9, y una de repuesto.
El mazo es **en estrella, un cable por módulo** (`architecture-poly.md` §8): un
`CS` por rama, y un canal de mux por rama porque todas las EEPROM viven en 0x50.

**`SDA`/`SCL` de cada ranura salen de su propio canal del mux**, no del bus
troncal. Cada canal lleva sus propias pull-ups en el cerebro, dimensionadas
contra la capacidad de la cinta — no copiadas de un ejemplo de aplicación.

**Los pines 9-12 solo se cablean en la ranura 1**, rotulada `VCO / TUNE` en la
serigrafía. Las otras siete los dejan sin conectar. Un módulo de más voces no
los usa y reporta por `MISO`, y **el contrato del J2 no cambia ni un pin**
(núcleo §5.3).

Eso hace de la ranura 1 la única con camino de afinado, y hay que decir qué
pasa si alguien enchufa el VCO en otra: **nada se rompe** —el módulo funciona
entero por SPI e I²C— pero el autoafinado se queda sin sus cuatro líneas. El
descubrimiento ya sabe qué hay en cada ranura (núcleo §3.5), así que el
firmware **tiene que decirlo**.

Y «tiene que decirlo» no vale como intención: por §2.1 del núcleo, una
capacidad que no está en el modelo no existe. Así que el aviso sale por un
mensaje del protocolo —un parámetro de medida «afinado disponible: sí/no» con
su razón, o un `ERROR` al intentar arrancar el barrido— y eso hay que
**elegirlo y escribirlo en la tabla de §4.1 del núcleo**, no dejarlo como una
línea del bring-up. Una versión anterior de este documento decía «puede
avisarlo», que es exactamente la clase de frase que no obliga a nadie.

### 4.1 El hueco del contrato: quién suelta el `MISO`

`MISO` es un **bus compartido entre ocho ranuras**, y el contrato congelado no
dice quién lo suelta. No es teórico: por ahí vuelven el mux de perillas, el
sensado de ocupación de los jacks y las medidas del módulo 4
(`architecture-poly.md` §8). Basta un módulo que no ponga su salida en alta
impedancia con su `CS` alto —o uno sin alimentar, cuyos diodos de protección
chupen corriente— para que dos se peleen la línea.

Y hay que decir de dónde parte la defensa, porque el otro lado ya está
fabricado: la netlist congelada del módulo 3 declara `SPI_MISO: J2-4 U7-8` —
una red directa, **sin resistencia de serie del lado del módulo**. Y su
bring-up documenta que *«los AD5686R arrancan en modo standalone, con SDO
deshabilitado»*, o sea que garantiza soltar el `MISO` **exactamente en el
estado en que no sirve para nada**, y no dice nada del estado con `DCEN`
encendido, que es el que hace falta para que haya control de tono. **Toda la
defensa tiene que vivir en el cerebro.**

Son cuatro piezas y ninguna cara:

1. **Resistencia en serie por ranura** en `MISO`, `SCLK` y `MOSI`. Ojo con
   esta: tiene **dos restricciones opuestas**. En `MISO` limita la corriente de
   una pelea y eso la empuja hacia arriba; en `SCLK` y `MOSI` termina un flanco
   de 10 MHz repartido a ocho cintas con sus ocho stubs, y eso la empuja hacia
   abajo. `enlace_budget.py` las asevera **por separado**, no como una sola
   cuenta, y añade una tercera: que el divisor que forman la serie de `MISO` y
   el pull-down de la pieza 2 deje el `V_IH` del pin dentro de lo que el
   datasheet garantiza.
2. **Pull-down en el cerebro**, para que un `MISO` sin nadie lea cero y no
   ruido.
3. **Protección en serie también en `CS`, `SDA` y `SCL`.** Son las líneas que
   el cerebro **maneja** contra módulos que pueden estar sin alimentar (§4.3),
   y una versión anterior de esta spec las dejó fuera: sin ellas, la salida del
   micro alimenta al módulo por sus diodos de protección.
4. **El requisito, escrito como contrato de módulo**: *todo módulo deja su
   `MISO` en alta impedancia con su `CS` alto, **también con `DCEN`
   encendido***. Se **mide en el bring-up** con el módulo 3 en la mano, que es
   el único que hoy puede desmentirlo: `CS` alto, `DCEN` encendido, `MISO`
   sondado. Aprobado o suspenso.

Con una honestidad sobre la pieza 1: una resistencia de serie **no evita la
pelea**, la hace sobrevivible. Lo que evita la pelea es la pieza 4, y esa vive
en placas que todavía no se han dibujado — salvo una, que ya está en gerbers y
nunca leyó este documento.

La velocidad queda como perilla y no como apuesta: el contrato dice **≤10 MHz**,
así que si la cinta no aguanta, baja el firmware y la placa no se rehace. Lo
que sí hace falta y hoy no existe en ningún documento del repo es **la longitud
máxima del mazo por rama**: sin ese número no hay presupuesto de flanco ni
dimensionado de las pull-ups de I²C. Se declara en el plan y entra como
constante citada en `enlace_budget.py`.

### 4.3 Estado de arranque, y quién maneja a quién sin alimentación

Esta spec tenía un hueco que el propio documento demostraba conocer: aplica la
lógica del estado de reposo a los gates (§5) y no la aplicaba a las ocho líneas
de selección. Se cierra aquí.

**Tabla de estado obligado**, entre la aplicación de alimentación y la primera
instrucción del firmware:

| Línea | Estado obligado en el arranque | Quién lo garantiza |
|---|---|---|
| `CS` ×8 | **Desasertado** (alto: son activo bajo) | Pull-up en el cerebro, no el pad del micro |
| `GATE` ×4 | Bajo | Pull-down en la puerta del primer MOSFET (§5) |
| `WS2812 dato` | Bajo | Pull-down antes del buffer |
| `EN` del interruptor del host | Apagado | Pull-down |
| `CLOCK out`, `RESET out` | Bajo | Pull-down antes del buffer |

El de `CS` no es cosmético: **`CS` asertado en el arranque es la pelea de
`MISO` de §4.1 en cada encendido**, y en el módulo 3 mete relojes espurios en
tres AD5686R en cadena soldada — CV de tono indeterminados en las cuatro voces
antes de que exista firmware que los corrija. El estado de los pads del RP2350B
tras reset **no se supone**: se lee del datasheet en la fase de BOM, y el
pull-up existe precisamente para no depender de esa lectura.

**Y la asimetría de alimentación.** La lógica del cerebro cuelga de la
IRM-15-5 (`J6`) y la de los módulos de un regulador local desde el +12 del
peine. **Son dos fuentes distintas y esta spec no puede imponerles una
secuencia**: hay una ventana en cada encendido, y un estado permanente si salta
un PTC de la bus board, en que el cerebro maneja `SCLK`, `MOSI`, `CS`, `SDA` y
`SCL` contra entradas sin alimentar.

La defensa elegida es **protección contra back-drive en toda línea que el
cerebro maneje** (la pieza 3 de §4.1), no una regla de secuenciación — porque
una regla de secuenciación depende de que el usuario no apague solo una cosa, y
eso no es una defensa. Lo que la spec sí declara es el requisito de medida: en
el bring-up, con el módulo 3 enchufado y **sin** su +12, medir la corriente que
entra por cada línea del J2. Criterio de cierre: por debajo de lo que el
datasheet del receptor admite en sus diodos de protección.

### 4.2 Los cuatro `TUNE_OUT`

Llegan ya recortados a nivel lógico por el 74HC14 **que vive en el módulo 3**;
esta placa no lleva ninguno. Entran directos a cuatro pines del PIO, con
resistencia en serie y **nada más**.

Nada de filtro RC en esas cuatro líneas. Todo el margen que tiene el
presupuesto de afinado son los **131 ns** de temblor que
`autotune_budget.py` le concede al 74HC14, y un filtro que redondee el flanco
se los come. Es una prohibición, no una preferencia, y va en el código que
genera el esquemático.

## 5. Los cuatro gates

El GPIO da 3,3 V y la convención pide **0/10 V activo alto**
(`architecture-poly.md` §4). Entre medias:

- **Cadena de dos MOSFET por gate** — dos inversiones, o sea no inversora — con
  **pull-down en la puerta de entrada**. Es la lección que sobrevive de la v1 y
  no se re-deriva: con una sola inversión, un GPIO flotante o bajo en el
  arranque deja el gate **alto**, y eso abre las cuatro envolventes de golpe al
  encender.
- **Riel local de 10 V desde +12**, no el +12 pelado: así el nivel es el de la
  convención y no se mueve con el riel del bus. Y **la magnitud que decide si
  ese regulador existe no es la corriente, es el margen de caída**: los gates no
  consumen casi nada, pero la entrada real es el +12 del peine con su
  tolerancia, menos el PTC de la bus board, menos el elemento de protección de
  polaridad inversa del issue #59 — cuya topología (serie o derivación) cambia
  la respuesta por medio voltio. `power_budget.py` asevera la **tensión mínima
  garantizada** en la entrada de ese regulador, no solo la corriente que pasa
  por él. Sin esa aserción, la salida de emergencia de §12.10 —«el bodge es
  cambiar un regulador, no la placa»— puede no existir.
- Salen por un **KK-254 de 5 pines con llave** (4 gates + `GNDD`) hacia el
  módulo 6. Con llave porque enchufarlo al revés tiene que ser imposible, y
  KK-254 porque es el conector que esta casa ya usa (bus board, J1 del módulo 3).

Queda anotado que §5.3 del núcleo ya escribió el camino de salida para cuando
haya más voces —mandar los gates **dentro de la trama SPI**, que además
sincroniza mejor porque tono y gate salen en el mismo instante— y que abandonar
este conector el día que toque no cuesta nada.

## 6. El mundo exterior

Todo lo que sale por el panel lleva protección contra descargas y contra que lo
enchufen mal. Se declara aquí una vez y aplica a los **nueve conectores**
enumerados en §10.

Y se declara con criterio, porque es una **pieza que hay que comprar** y no una
buena intención: la capacidad parásita de la protección se elige contra el
flanco que protege. La del USB y la del clock no pueden ser la misma pieza — un
supresor cómodo para un jack de 3,5 mm redondea un flanco de USB full-speed.

### 6.1 USB device — USB-B, aislado

**USB-B** porque es el conector que trae el cable que ya existe en cualquier
estudio, y porque aguanta que lo atornillen a un panel y lo pisen.

El aislador va con dos consecuencias que se declaran ahora, no en el bring-up:

- **El lado de arriba se alimenta del VBUS del host y el de abajo del
  instrumento.** Si los dos lados comparten alimentación no aisló nada, y eso
  es exactamente el error que hace que el aislador parezca puesto.
- **El instrumento deja de alimentarse por USB.** Grabar firmware por UF2 exige
  tenerlo encendido. Es un cambio de costumbre respecto a una Pico pelada, y va
  escrito en el bring-up para que no parezca una avería.

Y como el cable se va a quedar puesto, **el comportamiento va declarado en los
cuatro cuadrantes**, no descubierto por el usuario:

| Host | Instrumento | Qué tiene que pasar |
|---|---|---|
| on | on | Enumera y trabaja |
| on | **off** | **El host no ve nada.** No un dispositivo defectuoso |
| off | on | Nada. El lado de arriba sin VBUS, el de abajo vivo y ocioso |
| off | off | Nada |

El segundo es el que decide un detalle de diseño: **la pull-up de `D+` que
declara la velocidad tiene que vivir del lado del instrumento**, no del lado
del host. Si vive arriba, el sistema operativo ve un dispositivo que no
enumera cada vez que el instrumento está apagado con el cable puesto — y
reporta un aparato roto. §6.1 se preocupa de que el cambio de costumbre «no
parezca una avería»; este es justo el que sí lo parecería.

De ahí sale un criterio de compra que va al BOM: la pieza elegida tiene que
permitir esa colocación de la pull-up, y hay que reservarle los straps o pines
de control que necesite — **hoy esta spec no le reserva ninguno**.

### 6.2 USB host — USB-A por PIO-USB

Los dos pines del PIO —consecutivos por exigencia de la pila— con sus
resistencias de serie y las pull-down que pide el modo host. Esos valores salen
del circuito de referencia de Pico-PIO-USB y del estándar USB, citados en el
BOM.

Los 5 V hacia el controlador van por un **interruptor de carga con límite de
corriente y bandera de fallo**: un cable pellizcado no puede llevarse por
delante el riel de 5 V del instrumento.

**Y su `EN` va a un GPIO, no atado a alto.** Las piezas de esta clase se
enclavan en fallo y piden un ciclo de `EN` para rearmarse: con `EN` fijo, un
cable pellizcado deja el puerto host muerto hasta que el usuario apague el
instrumento entero — la mitad del fallo que la pieza se puso para evitar. Con
`EN` por GPIO, el firmware lo rearma, lo publica como parámetro de medida, y
además puede **apagar VBUS cuando no hace falta**, que es lo que ata este pin
al presupuesto de +5 V de §9.1.

Son dos pines: la bandera y el `EN`. Los dos entran en el crecimiento de
`pinout.rs` (§12).

### 6.3 MIDI DIN — dos jacks DIN-5

Entrada con **optoacoplador**, que es obligatorio desde 1983 y es la razón por
la que este camino existe. Los valores de las resistencias y el diodo de
protección salen de la **especificación eléctrica de la MIDI Association**
—que tiene variante de 3,3 V, y no es la de 5 V con otra cuenta— citada por
documento y página en el BOM. Ningún valor de oído.

Con el aislador del §6.1 puesto, el instrumento pasa a tener **dos** caminos
limpios en vez de uno: el *«USB para comodidad, DIN para grabar en serio»* de
`architecture-compute.md` **§4** deja de ser un compromiso y pasa a ser una
preferencia. *(Esa frase vive en §4, no en §7 como decía una versión anterior
de este documento y como dice la spec del núcleo — el desplazamiento se heredó
de ahí.)*

### 6.4 Clock y reset — cuatro Thonkiconn de 3,5 mm

Aquí «tamaño completo» ya es 3,5 mm: es lo que usa el formato, y es **la misma
pieza que el módulo 3** (WQP-PJ398SM).

- **Entradas.** Las fuentes de ahí fuera dan pulsos de hasta 10 V y esta
  entrada es de 3,3: divisor, recorte a los rieles, y Schmitt. Los valores no
  se ponen a ojo — salen de `sync_budget.py`, que evalúa **los dos casos** (la
  fuente de 5 V y la de 10) y asevera qué umbral queda en cada uno. Si un
  divisor que salva los 10 V deja la fuente de 5 por debajo del umbral, el
  guion se pone rojo aquí y no con un módulo prestado enchufado.
- **Salidas.** 0/5 V, o sea traducción desde 3,3 V. **La misma pieza traduce
  clock out, reset out y el dato del WS2812**, que pedían exactamente lo mismo:
  tres canales de un buffer de cuatro. Si el driver de dígitos (§7) resulta
  necesitar traducción, este buffer pasa a ser de seis canales en vez de
  añadirse otro integrado.

### 6.5 Pedal — jack de 6,35 mm a entrada analógica

Es **la función de seguridad del diseño** —§2.2 del núcleo hace que la
confirmación del agente sea física— así que se diseña como tal:

- **Falla en seguro.** Sin pedal enchufado, la entrada lee «no pulsado». Un
  pedal desconectado no puede parecerse a una confirmación, ni por ruido ni por
  una entrada flotando. Es una aserción del `check_netlist.py`, no una
  esperanza.
- **El ADC distingue solo qué le enchufaron**: un interruptor da dos extremos,
  un pedal de expresión da una rampa. Es firmware sobre el modelo de §3 del
  núcleo y no cuesta hardware.
- **La polaridad se aprende, no se supone.** Los pedales de sostenido vienen
  normalmente abierto y normalmente cerrado según fabricante, y los de
  expresión traen dos cableados incompatibles según sea Roland o Yamaha. Eso es
  un parámetro de calibración en el modelo, no una suposición cableada en cobre.

### 6.6 El puente inalámbrico

Módulo pre-certificado con **U.FL**, alimentado a 3V3, por UART. Su pico de
corriente al transmitir entra en `power_budget.py` tomado de su hoja, no
estimado.

Se le exponen `EN` y el pin de arranque para poder resetearlo y reprogramarlo
sin sacarlo (§12, nota de `pinout.rs`).

**Advertencia que va a la spec y al README:** la certificación de un módulo
pre-certificado **está atada a las antenas de su certificado**. Cambiar la
antena la invalida formalmente. Para un instrumento propio es irrelevante; el
día que salga de casa, no.

## 7. La cabeza local

Cuatro dígitos, un encoder con pulsador, y LEDs de estado. Cubre lo único que
no puede esperar a que aparezca un teléfono: número de preset, canal MIDI, y si
el autoafinado corre o si una voz se salió de rango (núcleo §5.2). No lleva
menús a propósito.

`pinout.rs` reserva tres pines para los dígitos —**datos, reloj, latch**— y eso
ya dice qué clase de pieza va: un **driver serie que refresque por hardware**.
El criterio de elección va escrito y se verifica en la fase de BOM:

1. Refresco y brillo por hardware. El núcleo de tiempo real no puede estar
   multiplexando dígitos mientras cronometra cuatro osciladores.
2. Umbrales de entrada que acepten 3,3 V. Si no los aceptan, se suma al buffer
   de 5 V de §6.4 en vez de añadir un integrado.

**Los LEDs de estado cuelgan del mismo driver.** `pinout.rs` no reserva ni un
pin para ellos, y no es un olvido: a un driver de ocho dígitos le sobran cuatro
cuando solo se usan cuatro. Cero pines, cero piezas.

**El pulsador del encoder es la confirmación física de respaldo** (núcleo §5.2
y §2.2). Con antirrebote, y con el mismo criterio de fallo seguro que el pedal.

## 8. Telemetría

Patrón de instrumento, estrenado en el módulo 3 y aplicado aquí sin excepción.

- **EEPROM de identidad** y **TMP1075**, los dos **aguas arriba del mux**,
  porque los ocho canales están gastados por las ocho ranuras.
- **La consecuencia se declara en vez de descubrirse:** la EEPROM del cerebro
  solo se puede hablar **con todos los canales del mux cerrados**, o choca con
  la de cualquier módulo abierto (todas viven en 0x50). Va escrita como regla
  de firmware y se verifica en el bring-up.
- **Al TMP1075 no le pasa:** su dirección va por straps, y el del cerebro se
  pone en una distinta de la que usan los módulos.
- **El `RESET` del mux va a un GPIO.** Es el caso degradado que la regla de
  arriba no cubre: un módulo que sostenga `SDA` bajo con su canal abierto se
  lleva por delante el descubrimiento, la telemetría **y** la identidad del
  propio cerebro, porque los tres cuelgan del mismo tronco. Sin ese pin, el
  único camino de recuperación es apagar el instrumento. Con él, el firmware
  cierra todos los canales, suelta el tronco y vuelve a abrir de uno en uno
  hasta encontrar al culpable — que además es exactamente lo que hace falta
  para **decir cuál módulo lo trabó** en vez de fallar en silencio.
- El TMP1075 va pegado al **regulador de 3V3**, que es lo que calienta aquí. No
  es un ritual: la temperatura de esta placa es la del aire de la caja, que es
  justo lo que decide cuándo el autoafinado tiene que volver a correr. El
  sensor mide algo que alguien usa.
- **Test points con su rótulo en la serigrafía**: los tres rieles, el de 10 V
  de los gates, `SCLK`/`MOSI`/`MISO`, los cuatro `TUNE_OUT`, el UART del puente
  y **las dos caras del aislador**. Quince pads anónimos y una tabla en otro
  archivo es tropezar con el polímetro en la mano.

## 9. Alimentación y masas

| Riel | De dónde | Para qué |
|---|---|---|
| **+5 V** | IRM-15-5 (vive fuera), por el conector dedicado **`J6`**, KK-254 | Lógica de 5 V, la cadena WS2812, VBUS del USB host, lado no aislado del aislador |
| **+12 V** | Bus board, peine Eurorack (650 mA por riel) | **Solo** el riel local de 10 V de los gates |
| **+3V3** | Regulador local desde +5 V | Micro, puente RF, y todo lo digital |
| **+10 V** | Local desde +12 V | Los cuatro gates, y nada más |
| **−12 V** | Llega por el peine | **Sin usar.** Se declara así, no se deja ambiguo |

El +5 V **no llega por el peine**: el bus SAM17 es de cuatro hilos
(+12/GND/GND/−12) y no lleva 5 V. Llega por `J6`, que la spec de la fuente
declara dedicado a este módulo. Con la regla del **issue #59** en la entrada de
cada riel: protección de polaridad inversa y RC, que es la única defensa válida
contra la cinta IDC invertida.

### 9.1 El +5 V pasa por aquí, y esta placa lo mide

Una versión anterior de esta spec decía que los amperios de la cadena WS2812 no
pasaban por la placa. **Era incompatible con la spec de la fuente**, que le
asigna la medida a este módulo por escrito —§4.1: *«medir sus 2.80 A es trabajo
del módulo 2, no de aquí»*— y sin la cual el árbitro de brillo del issue #104
no existe en ninguna placa del instrumento. Se corrige aquí.

El +5 V entra por `J6` y sale hacia la cadena por su propio conector, con un
**sensor de corriente en ese camino**: es lo que convierte el tope del #104 de
una constante de firmware en un árbitro con realimentación.

Y entra con una **regla de trazado que es una puerta, no una intención**: la
corriente de la cadena vive en una **isla de potencia en el canto de la placa**
y no cruza el plano que sostiene el SPI. Se comprueba sobre la placa ruteada
midiendo el camino real de cobre, no sobre la línea de código que pretendía
aislarlo.

> **El tope del #104 son 2,50 A, no 2,80.** Bajó el 2026-08-19 al leerse la
> curva de derating. `power_budget.py` **lo importa** de la spec de la fuente en
> vez de transcribirlo — la misma disciplina que §11 exige para
> `autotune_budget.py`. Y a ese tope, el margen de la IRM-15-5 es de **+1,58 a
> +2,01 W** contra los **2,50 W** que pide el host USB en su límite: **la suma
> no cierra hoy.** Es un bloqueante del plan, no de la spec, y lo lleva el
> issue #151.

**Masas.** Esta placa es digital entera, así que la masa principal es `GNDD`
—que se une a `GNDA` solo en la estrella del módulo 1, como todas—. Hay tres
fronteras que la generación de la placa tiene que respetar y que se comprueban
sobre el artefacto terminado (§11):

1. **La barrera del aislador**, que no es una masa sino un hueco: sin pista,
   sin plano y sin vía cruzándola en **ninguna** capa.
2. **El retorno de los gates**, que conmutan 10 V hacia otro módulo por un
   cable, y no tienen por qué compartir camino de vuelta con el SPI.
3. **La entrada analógica del pedal**, que es la única señal de esta placa que
   se lee con un ADC.
4. **El retorno de la cadena WS2812.** Ahora que el +5 V de la cadena sale de
   aquí (§9.1), su `GNDD` **vuelve aquí**, y esa es la referencia contra la que
   el primer LED mide el nivel del dato. El mazo es de tres hilos por eso.
   Sacar el dato de una placa y los amperios de otra —que es lo que decía la
   versión anterior de esta spec— dejaba esa referencia sin declarar, que es el
   modo de fallo clásico de las cadenas WS2812 largas.

## 10. Formato, panel y mecánica

**Una placa, cuatro capas**, con plano de masa entero y sin ranuras: 96 pines
de cabecera, SPI a 10 MHz saliendo a ocho cintas y una cadena de LED
conmutando cerca no dejan mucho margen de discusión. Los jacks van soldados a
la placa y el panel de aluminio delante — el patrón del módulo 3.

**El ancho no se estima: se calcula.** Y la lista de entradas del cálculo va
cerrada aquí, porque un presupuesto con una lista abierta es una estimación con
otro nombre:

| # | Elemento de panel | Pieza |
|---|---|---|
| 1 | USB device | USB-B |
| 2 | USB host | USB-A |
| 3, 4 | MIDI DIN in / out | DIN-5 ×2 |
| 5, 6, 7, 8 | Clock in / out, reset in / out | Thonkiconn 3,5 mm ×4 |
| 9 | Pedal | Jack 6,35 mm |
| 10 | **La cabeza local** | 4 dígitos + encoder con pulsador + LEDs de estado |
| 11 | **Los botones** | BOOTSEL y RUN |

**Son nueve conectores, no once**, y una versión anterior de este documento los
contó mal y además dejó la cabeza local fuera de las entradas del cálculo — o
sea que el ancho «calculado» habría salido corto por un bloque entero. La
declaración de §6 sobre protección contra descargas aplica a los **nueve
conectores**; los dos botones no la necesitan.

`panel_budget.py` suma las huellas reales de esos once elementos más sus
guardas, comprueba que el alto cabe en el panel Eurorack 3U, y —**importando**
de `case/clearance_budget.py`, no copiando— asevera que el ancho resultante
cabe en la fila superior del case respetando el `EXPANSION_MIN` reservado.
**Sustituye** la clave `"MIDI/CV"` del censo por su ancho calculado; si sumara,
contaría el módulo 2 dos veces.

Dato de contexto para ese budget, y desfase que hay que arreglar aparte: el
censo del case (`ANCHOS_PISO_SUP`) es de la arquitectura anterior. Lista
**VCO×3** —tres osciladores independientes de la tesis— cuando hoy el módulo 3
es una sola placa de cuatro voces que mide **114 mm**, no los 90 que el censo le
asigna; y le da al módulo 2 **80 mm**, que eran los de cuando era un Raspberry
Pi. El censo está marcado *«estimado, no cerrado»* en el propio README del
case, así que no es un error escondido — pero se abre issue antes de que
`panel_budget.py` lo importe.

**Botón de BOOTSEL accesible desde el panel, más el de RUN.** Sin eso,
recuperar una placa con firmware malo pide desarmar el instrumento.

## 11. Verificación

Las puertas de siempre, en especificidad creciente: huellas en disco **antes**
de escribir nada, vértices exactos en cada pin, ERC, netlist real contra el
diseño declarado a mano (`check_netlist.py`), cruce con el BOM
(`check_bom.py`), render **mirado por un humano** y commiteado, y DRC 0 con 0
sin conectar como juez independiente.

**Budgets ejecutables** (constantes con unidad y fuente citada, autocomprobación
contra un caso hecho a mano, aserciones que fallan, y un bloque de lo que el
cálculo NO cubre):

| Budget | Qué decide |
|---|---|
| `panel_budget.py` | Que los once elementos de panel de §10 quepan, y que el ancho quepa en la fila del case |
| `sync_budget.py` | El divisor y los umbrales de clock/reset contra fuentes de 5 V **y** de 10 V |
| `power_budget.py` | Corriente **y margen de caída** por riel: micro, puente RF en pico, host USB en su límite, driver de dígitos **y la cadena WS2812 entera** — contra lo que da la IRM-15-5 con el tope del #104 **importado** de la spec de la fuente, y contra los 650 mA del +12 |
| `enlace_budget.py` | El flanco de 10 MHz por cinta plana con ocho stubs, la resistencia de serie con sus **dos** restricciones opuestas, el `V_IH` resultante, y el tiempo de subida de las ocho ramas de I²C contra la longitud declarada del mazo |
| `pio_budget.py` | Máquinas de estado, memoria de instrucciones, canales de DMA y reparto de núcleos — y el conflicto de `clk_sys` entre el host USB y el afinado (issue #150) |

Ninguno reescribe `autotune_budget.py`: lo **importa**, para que los 131 ns del
74HC14 se enteren si algo se mueve. Y `power_budget.py` importa el tope del
#104 de la spec de la fuente por la misma razón: una versión anterior de este
documento lo transcribió de un issue y lo transcribió caduco.

### 11.1 Dos puertas nuevas

**`check_pinout.py` — que cada pin pueda hacer lo que se le pide.**

Una versión anterior de este documento definía esta puerta como *«lee la
netlist real y lee `pinout.rs`, y falla si discrepan»*. **Eso no es una
puerta.** En esta casa el esquemático lo genera un guion; si ese guion toma los
números de `pinout.rs` —que es lo correcto, porque debe haber una sola fuente—
entonces comparar la netlist con `pinout.rs` **compara la propuesta consigo
misma**. Es exactamente la lección del golden de netlist que este proyecto ya
aprendió: un verde vacío. La identidad queda garantizada por construcción y no
necesita puerta.

Lo que sí puede fallar, y por tanto lo que la puerta mide, es la **capacidad**:

1. **Que cada función caiga en un pin que la sepa hacer**, contra el datasheet
   del RP2350B: el pedal en una entrada de ADC de las que existen, `SDA`/`SCL`
   en pines con función I²C, y ninguna función encima de los pines que la placa
   necesita para el arranque por QSPI.
2. **Que los pines de un mismo programa de PIO caigan en la misma ventana.**
   Cada bloque PIO ve 32 pines (base 0 o base 16 — a confirmar contra el
   datasheet, issue #150). Con el mapa propuesto, `TUNE_OUT` en 13-16 exige
   base 0 y el PIO-USB en 36-37 exige base 16: cabe porque hay tres bloques,
   pero **nada lo prueba hoy** y `pinout.rs` tiene tests para cosas menores.
3. **Que el par del PIO-USB siga adyacente**, que ya lo prueba `pinout.rs` y
   aquí se cruza contra el cobre.

**Mutación:** mover un `TUNE_OUT` por encima del pin 31 y comprobar que se pone
rojo. Esa modificación pasa hoy todos los tests de `pinout.rs`.

Y la parte honesta, que va escrita en el bring-up y no en un guion: **el único
juez que puede decir que el cobre hace lo que el firmware cree tiene un
polímetro en la mano.** Ningún script convierte una propuesta en un hecho; lo
más que puede hacer es impedir que la propuesta sea imposible.

**`check_aislamiento.py` — que la barrera exista en el cobre.** Un aislador USB
con una pista, un plano o una vía cruzándole por debajo **no aisló nada**, y el
DRC no ve eso: es geometría, no electricidad. El guion mide el hueco real en
cada capa a lo largo de toda la barrera, sobre la placa ya ruteada.
**Mutación:** acercar el plano al otro lado y comprobar que falla. Sin esta
puerta, la decisión del §6.1 es decorativa y no hay forma de saberlo hasta que
zumbe.

Las dos nacen con su mutación corrida, y las dos miden **el artefacto
terminado**, no la línea de código que pretendía lograrlo.

## 12. Riesgos y lo NO confirmado

1. **El jitter real del 74HC14 en placa.** Ya no es una incógnita abierta —hay
   **131 ns** contra los que contrastarlo— pero sigue sin medirse. Issue #80.
2. **`F_PIO` = 150 MHz supone el reloj de sistema sin dividir.** Si el firmware
   lo divide, el sellado sube en la misma proporción y `autotune_budget.py` hay
   que recalcularlo. Se comprueba en el bring-up y el guion lo dice en su
   salida. *(Este riesgo estaba mal formulado: la amenaza no es que el firmware
   decida dividir, sino la del punto 4 — que otro subsistema le imponga el
   reloj.)*
3. **El full-speed del USB nativo del RP2350.** Si es solo full-speed, el
   aislador no cuesta ancho de banda ninguno. Se da por **probable, no por
   sabido**: se cierra contra el datasheet en la fase de BOM. Y hay que decirlo
   en voz alta porque §2.3 lista el aislador entre las **decisiones fijadas**:
   esa decisión descansa sobre una precondición que esta misma sección declara
   sin verificar. **Se verifica antes de dibujar**, no después — es la misma
   disciplina que §12.13 aplica al encapsulado.
4. **El conflicto de `clk_sys` entre el host USB y el afinado.** `Pico-PIO-USB`
   puede **imponer** el reloj de sistema para cumplir su temporizado, y
   `autotune_budget.py` supone 150 MHz. Si el host lo baja, el sellado del PIO
   sube en la misma proporción y los 131 ns del 74HC14 se mueven **sin que
   nadie haya tocado el afinado**. Es el riesgo con más alcance de esta lista
   porque invalida en silencio el presupuesto del que cuelga la afinación
   entera. Issue #150.
5. **El +5 V no cierra hoy.** Al tope de 2,50 A del #104, la IRM-15-5 deja
   +1,58 a +2,01 W, y el host USB en su límite pide 2,50 W. O baja el límite
   del interruptor de carga, o el árbitro le quita brillo a los LED cuando hay
   un controlador enchufado, o cambia la fuente. **Es un bloqueante del plan.**
   Issue #151.
6. **El censo de anchos del case es de la arquitectura anterior**, y
   `panel_budget.py` lo importa. Hay que arreglarlo antes de que el guion se
   escriba, o el guion sale verde porque tres VCO que ya no existen le prestan
   su sitio al cerebro. Issue #152.
7. **El contrato de software no estaba tan cerrado como parecía.** La auditoría
   del 2026-08-21 abrió siete issues sobre `software/nucleo/` —la confirmación
   física sin cablear, su semántica LIFO, el suscriptor único, los presets
   ciegos a la ranura, el conteo de voces todavía constante, los descriptores
   `'static` contra los parámetros por voz, y la polaridad del pedal como
   parámetro que el agente puede escribir (#143 a #149)—. Ninguno es de esta
   placa, pero **el bring-up de §1 depende de varios**: sin la confirmación
   cableada no hay nada que probar del pedal.
8. **El mux I²C no está elegido ni verificado contra stock de LCSC.** Issue #81.
9. **El driver de dígitos, el optoacoplador, el aislador y el módulo del puente
   tampoco.** Cada uno tiene su criterio escrito (§6, §7); ninguno tiene número
   de parte hasta que alguien abra su hoja. **Dato inventado nunca: verificado
   contra datasheet, o celda vacía.**
10. **El nivel exacto que espera el ADSR en el gate.** La convención dice 10 V,
   pero el umbral real lo cierra el módulo 6 cuando se dibuje. Hasta entonces el
   riel local de 10 V es la apuesta conservadora, y el bodge si el 6 pide otra
   cosa es cambiar un regulador, no la placa.
11. **La alta impedancia del `MISO` de cada módulo** (§4.1). Hoy solo el módulo 3
   puede desmentirlo, y se mide en su bring-up.
12. **Pico-PIO-USB es C.** Aplica la escalera de §4.4 del núcleo: se resuelve en
   el plan, y el instrumento funciona sin host — es degradación, no fallo.
13. **El pinout del encapsulado exacto del RP2350B.** Se verifica contra la
   figura del datasheet del **QFN-80 que se compra**, no contra un diagrama de
   la familia. Dos pines desfasados entre encapsulados del mismo chip ya costó
   una tarde en este proyecto.
14. **`pinout.rs` va a crecer con esta placa**, y son cinco pines nuevos: la
    bandera de fallo **y el `EN`** del interruptor del host (§6.2), el `EN` y el
    arranque del puente (§6.6), y el **`RESET` del mux I²C** (§8). Hay GPIO
    libres —38, 39 y del 41 al 47, o sea nueve— y el fichero existe para esto:
    dice de sí mismo que es una propuesta y que cuando haya placa **él es el
    único que cambia**. Sus tests de pin repetido y de pin inexistente siguen
    corriendo, y `check_pinout.py` le añade los de capacidad y ventana de PIO.
15. **Nada de esto está medido en placa.** Son datasheets, contratos y
    presupuestos.

## 13. Fuera de alcance

- **La PCB del panel y la mecánica de los jacks** — van con el case, igual que
  en el módulo 3.
- **El firmware de aplicación.** Esta placa hace arrancar y contestar al
  contrato que ya existe; el secuenciador, las escenas y el patch bay son las
  specs 2, 3 y 4 (issues #94, #95, #91).
- **La placita del puente inalámbrico**, si al final la antena adhesiva no
  bastara. La placa sale con su zócalo y su UART; mover el módulo a una placita
  propia no la toca.
- **El aislador de la salida DIN.** El DIN se aísla en la entrada, que es donde
  lo pide el estándar; aislar también la salida es un problema de otra placa.
- **Módulo 8 (efectos) y módulo 9 (sampler).** §10 del núcleo ya explicó por qué
  no viven aquí, y no se vuelve a discutir sin dato nuevo: el cerebro **no tiene
  camino de audio a propósito**.
- **El firmware del Pi de la v1** (`software/midi-cv/`), que muere con el Pi
  (issue #18).
