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

## 1. Objetivo

**La placa que manda números.** Reparte voces, cronometra los cuatro
osciladores por hardware, habla con el mundo por cuatro puertas —USB device,
USB host, MIDI DIN y el puente inalámbrico—, sincroniza con hardware ajeno por
clock y reset, y es la raíz del árbol I²C por el que se descubre qué módulos
hay conectados.

**Objetivo medible:** que el binario que hoy solo enlaza —`fw` compila y enlaza
para `thumbv8m.main-none-eabihf`— **arranque, enumere y conteste** sobre esta
placa; y que `core/src/pinout.rs` —hoy 39 pines declarados como propuesta, y
que esta placa hará crecer (§12.10)— pase a ser un hecho **verificado contra el
cobre por una puerta automática** (§11).

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
| **WS2812** | Solo el dato. Los amperios de la cadena no pasan por aquí (§9) | `architecture-poly.md` §4, §7; issue #104 |
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
| `SCLK` | `GNDD` | `MOSI` | `MISO` | `CS_n` | `GNDD` |

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
firmware puede **avisarlo** en vez de dejar al usuario con un autoafinado que
no arranca y no dice por qué. Va a la lista del bring-up.

### 4.1 El hueco del contrato: quién suelta el `MISO`

`MISO` es un **bus compartido entre ocho ranuras**, y el contrato congelado no
dice quién lo suelta. No es teórico: por ahí vuelven el mux de perillas, el
sensado de ocupación de los jacks y las medidas del módulo 4
(`architecture-poly.md` §8). Basta un módulo que no ponga su salida en alta
impedancia con su `CS` alto —o uno sin alimentar, cuyos diodos de protección
chupen corriente— para que dos se peleen la línea.

La defensa es de tres piezas y ninguna cara:

1. **Resistencia en serie por ranura** en `MISO`, `SCLK` y `MOSI`. En `MISO`
   limita la corriente de una pelea a un valor que no rompe nada; en `SCLK` y
   `MOSI` es la terminación que pide un flanco de 10 MHz repartido a ocho
   cintas planas con sus ocho stubs. El valor sale del budget del enlace
   (§11), no del catálogo.
2. **Pull-down en el cerebro**, para que un `MISO` sin nadie lea cero y no
   ruido.
3. **El requisito, escrito como contrato de módulo**: *todo módulo deja su
   `MISO` en alta impedancia con su `CS` alto*. Se **mide en el bring-up** con
   el módulo 3 en la mano, que es el único que hoy puede desmentirlo:
   `CS` alto, `MISO` sondado, aprobado o suspenso.

La velocidad queda como perilla y no como apuesta: el contrato dice **≤10 MHz**,
así que si la cinta no aguanta, baja el firmware y la placa no se rehace.

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
  convención y no se mueve con el riel del bus. Los gates no consumen
  prácticamente nada, así que el regulador es pequeño.
- Salen por un **KK-254 de 5 pines con llave** (4 gates + `GNDD`) hacia el
  módulo 6. Con llave porque enchufarlo al revés tiene que ser imposible, y
  KK-254 porque es el conector que esta casa ya usa (bus board, J1 del módulo 3).

Queda anotado que §5.3 del núcleo ya escribió el camino de salida para cuando
haya más voces —mandar los gates **dentro de la trama SPI**, que además
sincroniza mejor porque tono y gate salen en el mismo instante— y que abandonar
este conector el día que toque no cuesta nada.

## 6. El mundo exterior

Todo lo que sale por el panel lleva protección contra descargas y contra que lo
enchufen mal. Se declara aquí una vez y aplica a los once conectores.

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

### 6.2 USB host — USB-A por PIO-USB

Los dos pines del PIO —consecutivos por exigencia de la pila— con sus
resistencias de serie y las pull-down que pide el modo host. Esos valores salen
del circuito de referencia de Pico-PIO-USB y del estándar USB, citados en el
BOM.

Los 5 V hacia el controlador van por un **interruptor de carga con límite de
corriente y bandera de fallo**: un cable pellizcado no puede llevarse por
delante el riel de 5 V del instrumento. La bandera se lee por GPIO (§9 de este
documento y la nota de `pinout.rs` en §12).

### 6.3 MIDI DIN — dos jacks DIN-5

Entrada con **optoacoplador**, que es obligatorio desde 1983 y es la razón por
la que este camino existe. Los valores de las resistencias y el diodo de
protección salen de la **especificación eléctrica de la MIDI Association**
—que tiene variante de 3,3 V, y no es la de 5 V con otra cuenta— citada por
documento y página en el BOM. Ningún valor de oído.

Con el aislador del §6.1 puesto, el instrumento pasa a tener **dos** caminos
limpios en vez de uno: el *«USB para comodidad, DIN para grabar en serio»* de
`architecture-compute.md` §7 deja de ser un compromiso y pasa a ser una
preferencia.

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
| **+5 V** | IRM-15-5, que vive **fuera** de la placa (issue #60) | Lógica de 5 V, VBUS del USB host, lado no aislado del aislador |
| **+12 V** | Bus board, peine Eurorack (650 mA por riel) | **Solo** el riel local de 10 V de los gates |
| **+3V3** | Regulador local desde +5 V | Micro, puente RF, y todo lo digital |
| **+10 V** | Local desde +12 V | Los cuatro gates, y nada más |
| **−12 V** | Llega por el peine | **Sin usar.** Se declara así, no se deja ambiguo |

Con la regla del **issue #59** en la entrada: protección de polaridad inversa y
RC por riel, que es la única defensa válida contra la cinta IDC invertida.

**El +5 V de la cadena WS2812 no pasa por esta placa.** Del cerebro sale
**solo el dato**; los amperios de la cadena se toman en la fuente. El issue
#104 ya cuenta 2,8 A compartidos con el farol: meter eso por la placa que
sostiene el plano del SPI es regalarle ruido a cambio de nada.

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

## 10. Formato, panel y mecánica

**Una placa, cuatro capas**, con plano de masa entero y sin ranuras: 96 pines
de cabecera, SPI a 10 MHz saliendo a ocho cintas y una cadena de LED
conmutando cerca no dejan mucho margen de discusión. Los jacks van soldados a
la placa y el panel de aluminio delante — el patrón del módulo 3.

**El ancho no se estima: se calcula.** `panel_budget.py` suma las huellas
reales de los once conectores de panel más sus guardas, comprueba que el alto
cabe en el panel Eurorack 3U, y —**importando** de `case/clearance_budget.py`,
no copiando— asevera que el ancho resultante cabe en la fila superior del case
respetando el `EXPANSION_MIN` reservado.

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
| `panel_budget.py` | Que los once conectores quepan, y que el ancho quepa en la fila del case |
| `sync_budget.py` | El divisor y los umbrales de clock/reset contra fuentes de 5 V **y** de 10 V |
| `power_budget.py` | Corriente por riel: micro, puente RF en pico, 500 mA del host, driver de dígitos — contra lo que da el IRM-15-5 y contra los 650 mA del +12 |
| `enlace_budget.py` | El flanco de 10 MHz por cinta plana con ocho stubs, y de ahí la resistencia de serie |

Ninguno reescribe `autotune_budget.py`: lo **importa**, para que los 131 ns del
74HC14 se enteren si algo se mueve.

### 11.1 Dos puertas nuevas

**`check_pinout.py` — el cobre contra el firmware.** Lee la netlist real y lee
`core/src/pinout.rs`, y **falla si discrepan**. Hoy la placa y el firmware
pueden divergir en silencio y nadie se entera hasta que el instrumento hace
cosas raras; esto lo convierte en un error del repositorio. Es además lo que
convierte a `pinout.rs` de propuesta en hecho, que es el objetivo medible de §1.
**Mutación:** cambiarle el GPIO a un pin del esquemático y comprobar que se
pone rojo.

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
   que recalcularlo. Se comprueba en el bring-up y el guion lo dice en su salida.
3. **El full-speed del USB nativo del RP2350.** Si es solo full-speed, el
   aislador no cuesta ancho de banda ninguno. Se da por **probable, no por
   sabido**: se cierra contra el datasheet en la fase de BOM.
4. **El mux I²C no está elegido ni verificado contra stock de LCSC.** Issue #81.
5. **El driver de dígitos, el optoacoplador, el aislador y el módulo del puente
   tampoco.** Cada uno tiene su criterio escrito (§6, §7); ninguno tiene número
   de parte hasta que alguien abra su hoja. **Dato inventado nunca: verificado
   contra datasheet, o celda vacía.**
6. **El nivel exacto que espera el ADSR en el gate.** La convención dice 10 V,
   pero el umbral real lo cierra el módulo 6 cuando se dibuje. Hasta entonces el
   riel local de 10 V es la apuesta conservadora, y el bodge si el 6 pide otra
   cosa es cambiar un regulador, no la placa.
7. **La alta impedancia del `MISO` de cada módulo** (§4.1). Hoy solo el módulo 3
   puede desmentirlo, y se mide en su bring-up.
8. **Pico-PIO-USB es C.** Aplica la escalera de §4.4 del núcleo: se resuelve en
   el plan, y el instrumento funciona sin host — es degradación, no fallo.
9. **El pinout del encapsulado exacto del RP2350B.** Se verifica contra la
   figura del datasheet del **QFN-80 que se compra**, no contra un diagrama de
   la familia. Dos pines desfasados entre encapsulados del mismo chip ya costó
   una tarde en este proyecto.
10. **`pinout.rs` va a crecer con esta placa**: la bandera de fallo del
    interruptor del host, y el `EN` y el arranque del puente. Hay GPIO libres
    (38, 39 y del 41 al 47), y el fichero existe para esto — dice de sí mismo
    que es una propuesta y que cuando haya placa **él es el único que cambia**.
    Sus tests de pin repetido y de pin inexistente siguen corriendo, y ahora
    además `check_pinout.py` lo cruza contra el cobre.
11. **Nada de esto está medido en placa.** Son datasheets, contratos y
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
