# El hub del SAM17: el cerebro pasa a N657, se lleva la cara, y las radios se reparten — propuesta

**Fecha:** 2026-08-30
**Estado:** PROPUESTA. No toca código, DXF ni cobre. Mezcla dos clases de
cosas y las rotula para que no se confundan: las **actas** de Samuel del
2026-08-30 (§0, textuales) y las **decisiones que este papel recomienda y él no
ha firmado** (marcadas PENDIENTE DE FIRMA). Nada de lo segundo entra hasta que
lo firme o lo devuelva.
**Sujeto:** el zócalo del micro del cerebro (módulo 2 v2), y lo que cuelga de
él: la cara del instrumento, las radios, la interfaz de audio y el asiento del
procesador de aplicaciones.
**Premisas:** J2 punto a punto §0.1 (la premisa 1 lleva cinco días «dirigida,
no sellada»); motor-digital (N657 en la Voz, acta A-1 del 26); pantalla-motor;
cámara-gestos; panel al centro §4.1; Voz total E-1; cerebro §6.6 (el puente).

---

## 0. Las actas del 2026-08-30

Textuales, en el orden en que salieron:

- **A-1 — El cerebro no se queda en el RP2350.** «no vamos a tener un cerebro
  rp 2350 y una voz n657 … si vamos a usar otro micro de cerebro tiene que ser
  del mismo nivel o si no superior. lo primero es preguntarnos si es necesario».
- **A-2 — El SAM17 es un hub.** «el sam17 no solo sera un sintetizador, sera
  una interface, a el podre conectar otros modulos y controlarlos desde el
  sam17».
- **A-3 — La vara.** «este instrumento sera superior en computo y superior
  como instrumento a cualquier cosa que jamas haya sido construida».
- **A-4 — Las radios.** Para los satélites, radio propietaria de 2,4 GHz con
  reparto de tiempo (clase Nordic ESB): «bueno entonces ya sabemos que vamos a
  usar no?», señalando esa fila de la tabla. Y Wi-Fi además: «vamos a meterle
  tambien wifi de una vez pero para esas otras tareas».
- **A-5 — Los tres usos de la radio** («me parece muy bien»): salida OSC hacia
  las visuales, sincronía de tempo con la sala sin cable, y satélites como
  fuentes de modulación.
- **A-6 — El SAM17 es también una interfaz de audio.** «la placa (osea el
  sintetizador) ahora tambien debe incorporar una interface de audio tipo
  claret++ 4pre» (Focusrite Clarett+ 4Pre: la clase, no la pieza).

- **A-7 — La pantalla, dirigida y no sellada.** «creo que la pantalla va a
  tener que ser de 5 pulgadas porque en todo caso creo que reutilizaria la del
  kit de prueba». Es dirección («creo que»), no acta: va en §3.1 con lo que
  cambia y lo que no.

Lo que **no** es acta y este papel trata como pendiente: cuántos chips, de
qué placa cuelga la pantalla, el tamaño de la pantalla, dónde vive la cámara,
dónde vive la interfaz de audio, y el asiento del procesador de aplicaciones
(§2, §3, §5, §6).

---

## 1. Por qué existe este papel: la frontera de la ráfaga

El desarrollo del instrumento avanza por ráfagas, y en la última la Voz llegó
al N657 (26 de agosto) mientras el cerebro se quedó en el chip que su propio
contrato ya declaraba inservible. El J2 punto a punto, mergeado el 26 (#210),
cuelga de dos premisas; la segunda (el chip de la Voz) cayó y se reemplazó por
el N657; la primera dice, textual:

> «El cerebro lleva un micro con maestros serie independientes de sobra» —
> **dirigida, no sellada** … «Si la primera premisa cae, este papel cae
> entero: el RP2350 del cerebro tiene 2 SPI y 2 GPIO libres de 48. No hay
> versión de este diseño sobre el chip de hoy.»

O sea: cambiar el micro del cerebro no está en discusión; está mandado. Lo
que está abierto es **cuál** y **si hace falta uno aparte**. Eso último lo
contestó Voz total E-1 el 23 con tres razones «que ya estaban en el repo y
ninguna es de opinión». Las tres eran del RP2350:

| Razón de E-1 | Qué decía | Hoy |
|---|---|---|
| Pines | El cerebro deja 2 GPIO de 48; el maestro de la Voz gasta 8 en cronómetros de PIO | **Muerta.** La 2,8" murió el 27 (quedan 7); el censo del N657 con la pantalla sentada deja 54 libres (`micro_budget.py`, #213); los cronómetros son capturas de timer, no PIO |
| Reloj | `F_PIO = 150 MHz` contra el reloj que impone Pico-PIO-USB (#150) | **Muerta.** El N657 trae USB nativo (OTG1/OTG2); no hay PIO; el afinado se mudó al N657 el 26 |
| Masa | «La puerta sucia no vive en el cuarto limpio» | **Se mudó, no murió.** #183 puso los nueve conectores del mundo en una tarjeta trasera con cable plano, y D-P6 ya mete en la Voz un USB HS aislado (clase ISOUSB211) para el invitado. La Voz ya carga USB HS, LTDC de 28 pines, PSRAM por XSPI y la cámara |

E-1 queda sin sujeto tal como se escribió. Este papel la reescribe en §2.3 con
razones que sí son de hoy.

---

## 2. Un cerebro aparte, y de la misma clase — PENDIENTE DE FIRMA

### 2.1 Por qué no se funden, con los números de hoy

Fundir el cerebro en el N657 de la Voz se evaluó y se descarta por tres
razones nuevas, y la tercera es A-2:

1. **SPI.** El N657 tiene 6 (SPI1-6, tabla de pines de `micro_budget.py`).
   El motor usa 3 para los 16 cortes de CV (motor-digital §5). Fundido, la
   Voz deja de necesitar su esclavo del J2 y quedan **3 maestros para
   ranuras**. D3 del J2 exige que toda ranura activa vaya en SPI de hardware;
   el censo activo de D3 pide 4 (la Voz, el módulo de mandos #178 y las
   reservas de los módulos 8 y 9) y las ocho se cablean. Con 3 no cuadra.
2. **SRAM y CPU.** `sram_budget.py` da rojo en las cuatro configuraciones de
   pantalla, en el peor caso de lo fijo, y el motor está presupuestado al 50 %
   (~8 300 ciclos por muestra). Un hub que comparte chip con su cliente más
   grande no tiene sitio para crecer.
3. **A-2.** Si el SAM17 controla otros módulos, el cerebro es el producto y la
   Voz es su primer cliente. El hub no vive de las sobras de un cliente.

### 2.2 El chip: STM32N657, el mismo de la Voz

**D1 — El cerebro lleva un STM32N657.** Razones:

- **A-1 pide mismo nivel o superior.** El N657 es el mismo nivel, y es el
  chip que el J2 punto a punto ya usó para recalcular D8 (34,5 MHz) contra su
  Tabla 99: con los dos extremos de la misma clase, C5 del evento se sostiene
  sin medir sesgos entre chips distintos.
- **Trae lo que D3 pidió.** D3 repartió ocho ranuras sobre la clase H750 así:
  6 maestros SPI de hardware (4 activas + 2 de repuesto rápido) y 2 por USART
  síncrono a 12,5 MHz. El N657 trae 6 SPI. Que sus USART tengan el modo
  síncrono como maestro **queda por verificar en la hoja** (§10).
- **«Superior» no es un MPU con Linux.** Un sistema operativo en el camino de
  la nota cobra dos cosas que los papeles ya declararon innegociables: el
  arranque («arranca en milisegundos», `architecture-compute.md` §1) y la
  nota (R-E1: ningún mensaje del J2 dura más de 100 µs; el evento «sale en el
  instante en que existe»). El cómputo superior de A-3 tiene su sitio en §5,
  fuera del camino de la nota.

### 2.3 E-1, reescrita

> **E-1 (2026-08-30).** El cerebro y la Voz **no se funden**: el hub necesita
> los 6 SPI del chip para las ocho ranuras de D3 y la Voz gasta 3 en el CV;
> la SRAM de la Voz no cierra ni sin pantalla mientras el binario no se mida;
> y por A-2 el cerebro es el producto, no un inquilino de un módulo. Son dos
> N657, y lo que cambió el 30 no es qué instrumento es sino quién ejecuta
> cada mitad.

Lo que sigue en pie de la E-1 vieja: **la puerta sucia no vive en el cuarto
limpio** sigue siendo ley, solo que ahora se cumple en la tarjeta trasera
(#183) y en los aisladores (D-P6), no en la partición de chips. Con A-6 esa
ley gana un cuarto limpio más: los preamplificadores de micrófono (§6).

---

## 3. La cara se muda al hub — PENDIENTE DE FIRMA

### 3.1 La pantalla (D2)

La pantalla de 7" se colgó del motor el 26 por una sola razón, textual de
pantalla-motor §1: «esa respuesta se escribió cuando ningún chip de la casa
podía manejar 800×480. Hoy sí hay uno». Si el cerebro es un N657, esa razón
desaparece, y hay dos más para traerla:

- **El J2 del 25 ya la contaba en el cerebro.** D3, al descartar el LQFP100:
  «8 enlaces × 4 pines = 32, más LTDC en RGB paralelo (~24-28 pines), dos
  USB, I²C + mux, MIDI y gates». La pantalla fue del cerebro hasta que el
  chip del cerebro no estuvo sellado.
- **La pantalla de una interfaz muestra el sistema**, no un módulo. Y el hub
  es quien puede decir «el motor no arrancó», que era el requisito nuevo que
  el 27 le pedía a la cadena de LED.

**D2 — La pantalla de 7" cuelga del LTDC del N657 del hub.** El camino sigue
siendo el A de pantalla-motor (LTDC, RGB paralelo de 24 bits, táctil
capacitivo por I²C); cambia el chip. Su alimentación propia desde +12 V con
retorno dedicado (pantalla-motor §6) no cambia.

Lo que esto le hace a la SRAM de la Voz, con la tabla de `sram_budget.py`
(peor caso de lo fijo, todo ESTIMADO y sin medir el binario):

| Lo fijo en la Voz | Hoy (todo adentro) | Con cara y cámara en el hub |
|---|---:|---:|
| Binario del motor | 2 000 000 | 2 000 000 |
| Colas de audio y retardos | 400 000 | 400 000 |
| Activaciones de la NPU (gestos) | 800 000 | 0 |
| Cuadros de cámara (DCMIPP, doble) | 600 000 | 0 |
| Framebuffer 800×480 | 768 000 a 2 304 000 | 0 |
| **Queda para tablas y samples** (4 200 000 − lo fijo) | **−368 000 a −1 904 000** | **1 800 000** |

La puerta de la pantalla pedía 1 256 000 B libres. Hoy es rojo en las cuatro
configuraciones; con la cara en el hub cierra en el peor caso, sin haber
medido el binario. De paso mueren el riesgo 5 del motor (contención del LTDC
con el audio) y el riesgo del 27 («si el motor no arranca no hay pantalla»).

#### El tamaño: 5" si se reutiliza el panel del kit de prueba (A-7, dirigida)

Samuel apunta a reutilizar en el instrumento la pantalla de la placa de
prueba del N657 (#231 la describe: 5", 800×480, táctil, en el LTDC). Lo que
eso **no** cambia: D2 entero, porque el camino A es el mismo (LTDC, RGB
paralelo, táctil por I²C); la tabla de SRAM de arriba, porque el framebuffer
depende de la resolución y no de las pulgadas; y la cuenta de pines. Lo que
**sí** cambia: el papel del panel al centro corrió sus números para 165 mm
de ancho (flancos de 181,66 mm, franjas de 13,25 mm; su §2); con 5" los
flancos crecen y el problema de profundidad que ese papel llamaba «el
bloqueante de verdad» (§8, 0,6 mm de margen al fondo de la fila A) se alivia
con un panel más chico. Las cotas nuevas **salen de la hoja del panel**, no
de la pulgada: hay que verificar que la pantalla de la DK sea una pieza
separable con hoja propia (fabricante, contorno, conector FPC y su cuenta de
pines, controlador táctil), y que se compre suelta y no solo pegada al kit.
Es la fila 9 de §10. Y hace que la compra de #231 pague dos veces: el
bring-up mide la pantalla exacta del instrumento, no una parecida.

La SRAM del **hub** hereda el framebuffer y la cámara. Tiene la misma
memoria (4,2 MB + 192 KB de TCM) y ningún sampler, así que su PSRAM por XSPI
queda libre para el framebuffer sin la contención de caudal que
`psram_budget.py` mide en la Voz contra los granos. Eso **se corre, no se
afirma**: es la fila 2 de §10.

### 3.2 La cámara (D3)

El papel de gestos sentó la cámara en el motor para que el valor «no cruce
el J2» (§3 de cámara-gestos: fuente local tipo LFO). Con el enlace a 34,5 MHz
(D8) y una latencia de cámara de 30 a 80 ms, un flujo de gestos a 100 Hz
ocupa una fracción despreciable del enlace; el argumento de no cruzar era
bueno para un bus compartido al 87 % y deja de pesar en un enlace propio.

**D3 — La cámara cuelga del CSI-2 del hub y la inferencia corre en la NPU
del hub.** La NPU está ociosa por diseño en los dos chips (benchmark:
«potencial declarado, no argumento»); lo que cambia es de quién es la SRAM
que pagan las activaciones y los cuadros: 350 000 a 1 400 000 B que la Voz
recupera (tabla de §3.1). El mapeo de gestos sigue siendo estado del modelo
(cámara-gestos §3) y el valor instantáneo viaja por el J2 como cualquier
sensor.

Este papel **reabre** un papel con acta de Samuel («sí, la declaras»). Si
Samuel prefiere que la cámara se quede en el motor, D3 se devuelve y la Voz
paga esos bytes; D2 no depende de D3.

### 3.3 Los mandos

Los potenciómetros alrededor de la pantalla «parametrizables por el cerebro»
(panel al centro §0, textual de Samuel) cuelgan del mismo chip que la
pantalla. No cambia nada del plan del panel: ya eran del cerebro.

---

## 4. Las radios — ACTA A-4, con un dato que Samuel no tenía

### 4.1 Lo que ya estaba decidido y este papel no reabre

El Wi-Fi **ya tiene pieza**: la spec del cerebro §6.6 (2026-08-25) reunió
los siete trabajos de #162, resolvió la licencia de Link (GPL, firmware del
puente publicado) y eligió el **ESP32-S3-WROOM-1U-N16R2** (U.FL, `EN` y pin
de arranque expuestos, por UART). Este papel no toca la pieza; el issue #162
sigue abierto y debería cerrarse contra §6.6. Lo que este papel sí hace es
**recortar la lista de trabajos**, porque la pantalla de 7" cambia para qué
sirve la radio:

| # | Trabajo (cerebro §6.6) | Qué le pasa el 30 |
|---|---|---|
| 1 | Servir la UI web al teléfono | **Deja de ser requisito** (Samuel: «si vamos a tener una pantalla ya no necesitamos esa funcionalidad»). Se queda como crecimiento: el teléfono sigue siendo un cliente válido del protocolo |
| 2 | Expandir el descriptor a JSON | Sigue, al servicio de 4 y 8 |
| 3 | Hablar el protocolo por UART con el cerebro | Sigue; el cerebro es ahora el N657 del hub |
| 4 | Ableton Link, y la fase del instrumento | **Confirmado por A-5** («sincronía con la sala») |
| 5 | Portal de configuración en modo punto de acceso | Sigue |
| 6 | Ser su propia red en escenario | Sigue |
| 7 | HID inalámbrico | Sigue opcional |
| **8** | **Salida OSC hacia visuales** (TouchDesigner, Resolume): notas, gestos y perillas salen como estado del modelo por UDP | **Nuevo, por A-5.** Es la cámara al revés: las manos entran, la luz sale |

### 4.2 Los satélites: radio propietaria con reparto de tiempo (D4, ACTA)

**D4 — Los satélites hablan por una radio propietaria de 2,4 GHz con un TDMA
nuestro, clase Nordic ESB.** El hub reparte ranuras de tiempo; cada satélite
habla en la suya; la latencia tiene cota y el jitter lo fija el diseño, no el
vecino con su router. Es un coprocesador de radio al lado del N657 (SPI o
UART), y la **misma familia en cada satélite** (una segunda cámara en un pie,
un pedal, un sensor de muñeca: el camino C de cámara-gestos §4, que radiaba
landmarks a 30-60 Hz en kilobits por segundo). Trae BLE, así que teléfonos y
controladores comerciales entran por el mismo chip si algún día hace falta el
trabajo 7.

**El dato que Samuel no tenía al firmar A-4:** el ESP32-S3 ya elegido en §6.6
trae **ESP-NOW** de serie: un enlace sin asociación ni TCP/IP sobre la misma
capa física de Wi-Fi, con latencia del orden de 1 a 2 ms (ESTIMADO, sin
medir) pero **sin cota**, porque sigue siendo 802.11 y comparte el canal por
turno educado. Las dos opciones, para que la decisión se tome con el dato:

| | ESB + TDMA propio (D4) | ESP-NOW sobre el S3 ya elegido |
|---|---|---|
| Pieza nueva | sí, un radio Nordic en el hub y en cada satélite | ninguna |
| Latencia | sub-milisegundo con cota (ESTIMADO; a medir) | ~1-2 ms medios, picos con vecinos (ESTIMADO; a medir) |
| Determinismo | el que fije nuestro TDMA | ninguno garantizado |
| Coexistencia | dos radios de 2,4 GHz en el cajón: plan de canales y dos antenas | una sola radio, pero ESP-NOW y Wi-Fi comparten canal |
| Para 100-500 Hz de gestos | sobra | alcanza, sin garantía |

D4 se mantiene como acta; si Samuel, con este dato, prefiere no sumar una
segunda radio, se devuelve aquí y ESP-NOW pasa a v1 con ESB como camino
declarado.

**UWB (clase DW3000): declarado como crecimiento, no v1.** Su gracia para
este instrumento no es mover datos sino **saber dónde está el satélite**: la
posición del que toca en la sala como fuente de modulación.

### 4.3 Lo que ninguna radio toca

El núcleo §10 pide que «el núcleo de tiempo real nunca vea una pila TCP».
Este papel lo extiende: **ninguna radio está en el camino de la nota ni del
audio**. Lo inalámbrico entra al modelo como sensores y sale como estado; la
nota, el audio y el CV a tasa de audio van por J2, por cobre y por USB. Una
radio caída es un sensor que calla, no un instrumento que deja de sonar.

---

## 5. El asiento del procesador de aplicaciones — PENDIENTE DE FIRMA

A-3 pide cómputo superior. Los dos N657 dan el camino de nota más rápido que
el silicio de hoy permite en bare-metal, y la NPU del hub para gestos. Lo que
un microcontrolador no da (agente de IA a bordo, red de verdad, sistema de
archivos, pantalla compuesta) **ya tiene sitio en el diseño**:
`architecture-compute.md` §1 lo llama «cualquier computadora» y D-P6 le da
un conector aislado. Es un cliente del protocolo, con el mismo contrato que
la app y el agente.

**D7 — Se reserva un asiento para un procesador de aplicaciones a bordo,
como cliente del hub.** Sin pieza, sin fecha. Condiciones que nacen aquí:

- Va en un **SoM** (módulo con su DDR ya ruteada): la placa del hub no paga
  el layout de memoria.
- Habla con el hub por un **enlace aislado** ya reservado en papel: USB
  (D-P6) o la autopista de D9. No comparte nada con el camino de la nota.
- **Su arranque no bloquea**: el instrumento suena en milisegundos y la
  pantalla grande puede tardar segundos en llegar si la compone él.
- Si entra, **absorbe el Wi-Fi** (trabajos 4, 5, 6 y 8 de §4.1) y
  `architecture-compute.md` §1 («la computadora se queda FUERA») **se
  re-firma**, no se contradice en silencio.

---

## 6. La interfaz de audio — ACTA A-6, sin diseñar aquí

A-6 mete un subsistema entero que ningún papel tenía: el SAM17 es también
**la interfaz de audio del estudio**, de la clase Clarett+ 4Pre (Focusrite).
Este papel **no la diseña**: es un subsistema con su propia cadena analógica
(preamplificadores de micrófono, phantom, entradas de línea e instrumento,
salidas de línea y auriculares, conversión a 24 bits), su propio papel y su
propia junta. Lo que sí hace es decir qué le exige al hub y qué reabre, para
que el censo de §10 no la descubra tarde. **Las cifras de la clase** (cuántos
preamplificadores, cuántas entradas y salidas, óptico ADAT sí o no, tasa
máxima) **se fijan contra la hoja del producto de referencia** antes de
escribir el papel propio, no de memoria (Principio I).

### 6.1 Lo que ya existe y con lo que choca

- **D-P6 ya es «USB audio hacia la computadora»**: un invitado UAC2 asíncrono
  con endpoint de feedback, aislado, en el N657 de la Voz, con la boca y los
  oídos como ojo de cerradura estéreo (motor-digital D-P1/D-P4). Una interfaz
  de clase Clarett es **el mismo concepto con muchos canales y con
  preamplificadores**. La computadora no puede ver **dos** dispositivos de
  audio del SAM17: una interfaz es **un solo dispositivo compuesto** (audio
  multicanal + MIDI) por **un solo cable**. Eso es una tensión real entre
  D-P6 (en la Voz) y A-6, y este papel la deja escrita, no resuelta.
- **El USB device al computador es del cerebro** (cerebro §1: «habla con el
  mundo por cuatro puertas»), y con A-6 ese puerto pasa a llevar audio
  multicanal isócrono a alta velocidad, además de MIDI y el protocolo. El
  aislador de D-P6 (clase ISOUSB211, 480 Mb/s) es el que lo cruza.
- **La trasera hoy es solo aire** (#167) y #183 la convirtió en una tarjeta
  con nueve conectores. Una interfaz de audio trae combos XLR/TRS, salidas
  balanceadas, auriculares y quizá óptico: la tarjeta trasera **crece**, y
  con ella el estudio del valle y la trasera capturada que se acaban de
  dibujar.
- **La doctrina de masa** (Voz total §0.2, E-1 vieja) gana un segundo cuarto
  limpio: un preamplificador de micrófono es más sensible que un expo de
  3,6 cents por milivoltio. El aislamiento del USB deja de ser un detalle del
  invitado y pasa a ser la frontera de la interfaz.
- **La fuente**: phantom de 48 V es un riel que el módulo 1 no tiene y que el
  presupuesto de potencia no conoce.

### 6.2 Lo que le exige al hub, para el censo

Si la interfaz cuelga del hub (lo natural: el hub es quien habla con la
computadora), el censo de §10.1 suma: SAI (el N657 tiene SAI1 y SAI2 en la
tabla de pines; cuántos canales por bloque, contra la hoja), I²C o SPI para
el control de conversores y preamplificadores, un USB HS como dispositivo
compuesto (audio + MIDI + protocolo), y colas de audio en SRAM que hoy no
están en ningún censo del hub. Si cuelga de la Voz, D-P6 crece hasta
absorberla y la Voz pierde parte de lo que §3.1 le devolvía. **Dónde vive es
decisión de Samuel con el papel propio delante**, y ese papel es el
prerrequisito de la fila 1 de §10.

---

## 7. Lo que este papel NO decide

- **Más de ocho ranuras.** El IDC y el censo son de ocho; crecer por encima es
  pregunta de conector y de autopista (D9), no de chip.
- **La pieza del radio ESB**, la del SoM, ni ninguna de la interfaz de audio:
  sin hoja en el árbol no hay nombre (R-M3).
- **El diseño de la interfaz de audio** (§6): papel propio, con las cifras de
  la clase contra su hoja.
- **Cuánto pesa el binario del motor.** Sigue sin medir y sigue siendo el
  estimado más gordo del censo; lo que cambia es que ya no tumba la puerta de
  la pantalla.
- **El nombre del módulo.** La fila de arriba entera se propuso llamar «la
  cabeza» (con la pantalla como «la cara») el 2026-08-30; Samuel no ha
  contestado. Este papel usa «el hub» para el chip del cerebro y no bautiza
  nada.
- **El estudio del valle** (panel al centro §5): no cambia, pero §6.1 le
  añade conectores por contar.

---

## 8. Lo que cambia en el firmware

- `software/nucleo/core`: **nada**. Es `no_std` y no sabe de chips; sus 232
  tests sobreviven enteros.
- `software/nucleo/fw`: el target. Hoy `embassy-rp` con `rp235xb`; pasa a
  `embassy-stm32` con la feature `stm32n657x0`, que existe en la versión 0.6
  (verificado en su `Cargo.toml` el 30). Son `main.rs`, `usb.rs` y
  `pinout.rs`. **Qué drivers del N6 tiene escritos embassy** (SPI, USB HS,
  LTDC, SAI, DMA) queda por verificar: fila 6 de §10.
- **Un solo bring-up.** La Discovery que #231 aplazó por presupuesto trae una
  800×480 en el LTDC: sirve para el camino de la pantalla del hub y para los
  riesgos de audio del motor con la misma placa. #231 sube de prioridad sin
  gastar más.

---

## 9. Enmiendas mandadas, con dueño

Ninguna se ejecuta hasta que D1 y D2 se firmen. Se listan para que no se
manden al aire (patrón conocido: #214).

| Papel o guion | Sección | Qué cambia | Dueño | Estado |
|---|---|---|---|---|
| `2026-08-25-j2-punto-a-punto-design.md` | §0.1 | Premisa 1: «dirigida, no sellada» → sellada en N657 (D1) | este papel al firmarse | pendiente |
| ídem | cabecera | «propuesto, pendiente de Samuel» → decidido y mergeado (#210, 26-ago) | una línea, cualquiera | pendiente |
| `2026-08-23-modulo-voz-total-design.md` | E-1 | Reescrita como en §2.3 | este papel | pendiente |
| `2026-08-26-motor-digital-design.md` | §0, actas de la noche, §10 riesgo 5, D-P6 | La pantalla y la cámara salen del motor (D2, D3); riesgo 5 muere; «#209 sitio 2» sigue cierto; D-P6 se reconcilia con A-6 | este papel + papel de la interfaz | pendiente |
| `2026-08-26-pantalla-motor-design.md` | §1, §6 | «Por qué cuelga del motor» → del hub; sitio contestado | este papel | pendiente |
| `2026-08-26-camara-gestos-design.md` | §1, §3, §4 | NPU y CSI del hub; camino C → radio de D4 | este papel, con acta de Samuel | pendiente |
| `2026-08-27-panel-pantalla-al-centro-design.md` | §4.1 | «La cara se muda del cerebro al motor» → se queda en el cerebro; el requisito «el motor no arrancó, en luz» lo cumple la pantalla | este papel | pendiente |
| `2026-08-21-modulo-2-v2-cerebro-design.md` | §1, §6.6, §7, §12 | RP2350B → N657; lista de trabajos de §4.1; la cabeza local es la 7"; el margen de pines se recalcula | este papel | pendiente |
| `2026-08-21-modulo-2-v2-cerebro.md` (plan) | entero | Reescribir contra el N657 (VFBGA264, no QFN-80; `pinout.rs` nuevo) | plan nuevo | pendiente |
| **Papel nuevo: la interfaz de audio** | — | Cifras de la clase contra hoja; dónde vive; reconciliación con D-P6; trasera, masa y phantom | papel propio | pendiente |
| `hardware/02-midi-cv/pio_budget.py` | — | Retirar a historia: mide un chip que se va | PR de nivelación | pendiente |
| `hardware/02-midi-cv/sram_budget.py` | — | Partir en dos censos: Voz sin cara, hub con cara (y con colas de audio si §6.2) | PR de nivelación | pendiente |
| `hardware/02-midi-cv/micro_budget.py` | censo N657 | Segundo censo de pines: el hub (§10 fila 1) | PR de nivelación | pendiente |
| `hardware/02-midi-cv/power_budget.py` | — | Riel de phantom y consumo de la interfaz (§6.1) | papel de la interfaz | pendiente |
| `hardware/03-vco/spi_privado_budget.py` | — | «Sigue modelando los dos RP2350B viejos» y da verde: sujeto muerto | PR de nivelación | pendiente |
| `README.md` l.44, `docs/architecture-compute.md` §1, `docs/architecture-poly.md`, `hardware/03-vco/README.md`, `docs/modules/03-vco.md` | — | «2× RP2350B» y «RP2350» → N657 | PR de nivelación | pendiente |
| #162 | — | Cerrar contra cerebro §6.6 más la tabla de §4.1 | issue | pendiente |
| #178 | — | El módulo de mandos cuelga de un SPI del hub | issue | pendiente |
| #183 | — | La tarjeta trasera gana los conectores de la interfaz de audio | issue + papel de la interfaz | pendiente |
| #231 | — | Una placa, dos bring-ups | issue | pendiente |

---

## 10. Lo que hay que correr o verificar antes de sellar

1. **Censo de pines del hub** en `micro_budget.py`: 8 ranuras (32 pines) +
   LTDC (24-28) + dos USB + I²C con mux + MIDI + cadena WS2812 + clock/reset
   + pedal + dos UART (ESP32-S3 y radio ESB) + CSI + XSPI + lo que §6.2
   sume (SAI y control de conversores). **Verde antes de firmar D1.**
2. **Censo de SRAM del hub**: framebuffer en PSRAM propia (sin sampler),
   activaciones de la NPU, cuadros de cámara y colas de audio de §6.2. Con su
   mutación.
3. **USART síncrono del N657** como maestro, contra la hoja: las dos ranuras
   de repuesto de D3 dependen de ello.
4. **Latencia y jitter del enlace ESB** en bring-up, con cota escrita antes
   de medir.
5. **Coexistencia de dos radios de 2,4 GHz** en el mismo cajón: canales y
   antenas.
6. **Drivers de embassy-stm32 para el N6** (SPI, USB HS, LTDC, SAI, DMA).
7. **El binario del motor**, medido en la Discovery (#231): sigue siendo el
   número que manda en ambos censos de SRAM.
8. **Las cifras de la clase Clarett+ 4Pre**, contra la hoja del producto,
   antes del papel de la interfaz.
9. **La hoja del panel de 5" de la DK** (A-7): pieza separable, contorno,
   FPC y táctil; y que se venda suelta. Con ella, el panel al centro recorre
   sus números de §2 y §8.

---

## 11. Riesgos

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | El censo de pines del hub no cabe con las ocho ranuras, la cara y la interfaz de audio | §10.1 en verde, o D3 devuelta (la cámara se queda en el motor), o la interfaz cuelga de la Voz |
| 2 | Dos N657 con dos arranques desde XSPI y dos binarios firmados | FSBL + Rust vivos en la Discovery (#231, riesgo 6 del motor) |
| 3 | Dos radios de 2,4 GHz se pisan | §10.5 medido; suplente: ESP-NOW sobre el S3 (§4.2) |
| 4 | Se reabren tres papeles con acta (pantalla, cámara, panel al centro) | Samuel firma o devuelve D2 y D3 |
| 5 | La computadora ve dos dispositivos de audio (D-P6 y A-6) | El papel de la interfaz los reconcilia en uno compuesto |
| 6 | La trasera y el valle recién dibujados no tienen sitio para los conectores de la interfaz | El papel de la interfaz cuenta conectores contra el estudio del valle (panel al centro §5) |
| 7 | No hay plata para la Discovery | Decisión de Samuel; mientras tanto, todo lo de §10.1-10.3, 10.6 y 10.8 es papel y se puede correr |
