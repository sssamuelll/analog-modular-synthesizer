# El hub del SAM17: el cerebro pasa a N657, se lleva la cara, y las radios se reparten — propuesta

**Fecha:** 2026-08-30
**Actualización:** 2026-10-01
**Estado:** D1, D2, D7 y D3' FIRMADAS; ubicación de la interfaz de audio
RESUELTA por ENMIENDA (§6.2); cristal HSE en el hub por el acta del 2026-10-01 (§0). Quedan pendientes los cierres de papeles y
censos propios. No toca DXF ni cobre;
trae un guion (el censo de pines del hub, §10 fila 1). Mezcla dos clases de
cosas y las rotula para que no se confundan: las **actas** de Samuel del
2026-08-30 y 2026-09-09 (§0, textuales) y sus decisiones e interpretaciones.
El 2026-08-30, Samuel firmó **D1, D2 y D7** («todas bien») y devolvió **D3**
con una acta nueva (A-9): la cámara y la IA van a un **tercer N657**. D3 queda
sustituida por D3' (§3.2), firmada con su forma de módulo el 2026-09-09.
Ese día queda decidido un **cuarto N657 dedicado a la interfaz de audio**.
**Sujeto:** el zócalo del micro del cerebro (módulo 2 v2), y lo que cuelga de
él: la cara del instrumento, las radios, la interfaz de audio y el asiento del
procesador de aplicaciones.
**Premisas:** J2 punto a punto §0.1 (la premisa 1 lleva cinco días «dirigida,
no sellada»); motor-digital (N657 en la Voz, acta A-1 del 26); pantalla-motor;
cámara-gestos; panel al centro §4.1; Voz total E-1; cerebro §6.6 (el puente).

---

## 0. Las actas del 2026-08-30 y 2026-09-09

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

- **A-7 — La pantalla es de 5", la del kit de prueba.** Primero como
  dirección («creo que la pantalla va a tener que ser de 5 pulgadas porque en
  todo caso creo que reutilizaria la del kit de prueba») y luego como acta,
  con su razón: «este es un instrumento de diseño de luthier, no de
  reproduccion masiva, quizas el proximo sea de 7 pulgadas, este seria de 5
  porque es lo que tenemos ahora a nuestro alcance ya que cuando haga la
  inversion del dev kit podre aprovechar al maximo los recursos con los que
  venga el kit». Va en §3.1 con lo que cambia y lo que no, y deja un
  principio: **lo que el kit traiga y coincida exactamente con la clase que
  un papel pide, se hereda; lo que solo se parezca, no.**
- **A-8 — Dos versiones, un cobre.** «hacemos una version para 5 pulgadas y
  luego una version para 7 pulgadas, porque cuando imprima las placas pedire
  varias placas, entonces la primera esta bien y es normal que tenga las 5
  pulgadas del dev kit pero luego las otras si que las compro de 7 pulgadas».
  El primer instrumento lleva la 5" del kit; los siguientes, una 7" comprada.
  Las condiciones para que eso sea una versión y no dos diseños van en §3.1.
- **A-9 — La IA entra de una, en un tercer N657.** Al firmar D1, D2 y D7
  («todas bien pero en D3 un tema»): «yo quiero meterle ia de una. para eso
  es que queremos la camara entonces tendriamos que usar tres stm32n657 para
  dedicar uno netamente a ia. para poder hacer cosas tipo de mago como que se
  controlen las cosas solo con mis manos (por medio de la camara) o con cada
  dedo o moviendo mi cuerpo». Sustituye a D3; su forma va en §3.2.

### Acta del 2026-09-09 — Reparto por trabajo

«la idea es que tengamos un procesador solamente para la parte analogica,
un procesador solamente para la interface grafica y controladores, un
procesador solo para la IA, un procesador solamente para la interface de
audio, la razon de ese diseño es que queremos tener suficiente headroom
para procesamiento y que el instrumento jamas se cuelgue. que sea el mas
rapido de toda la historia de los sintetizadores y el que tenga el mejor
sonido tambien, estoy pensando por eso en meterle valvulas y todo.»

**Interpretación y cierre del acta, fuera de la cita:** D3' queda
**FIRMADA el 2026-09-09**, incluida su forma de módulo por J2 (§3.2).
§6.2 queda **RESUELTA mediante ENMIENDA**: la interfaz de audio vive en un
**cuarto N657 dedicado**, fuera del hub y de la Voz. El reparto firmado es:

| N657 | Trabajo |
|---|---|
| Voz | Parte analógica |
| Hub | Interfaz gráfica y controladores |
| Tercero, «el mago» por su trabajo, no como bautizo | IA |
| Cuarto, **sin nombre**, referido por su trabajo | Interfaz de audio |

La razón es reservar **headroom y aislar las cargas por silicio** para que
el instrumento no se cuelgue. Es una intención de diseño; el reparto por sí
solo no garantiza ausencia de cuelgues, mayor rapidez ni mejor sonido.
**Válvulas: intención, NO DECIDIDO**; corresponde a otra conversación sobre
sonido, no sobre cómputo.

**Firmado el 2026-08-30:** D1 (la pareja inicial de N657, hub y Voz), D2 (la
cara al hub) y D7 (el asiento del procesador de aplicaciones).
**Cierre de pendientes el 2026-09-09:** D3' (§3.2), incluida la forma del
módulo, FIRMADA; ubicación de la interfaz de audio (§6.2), RESUELTA mediante
ENMIENDA con un cuarto N657 dedicado. El cierre de su papel propio sigue
pendiente.

### Acta del 2026-10-01 — El hub lleva cristal HSE

Tras la medida en la NUCLEO-N657X0-Q de ese día (#150, comentario del
2026-10-01), y ante la pregunta «¿la placa del hub lleva cristal HSE?»:

«metamosle cristal HSE»

**Interpretación y cierre del acta, fuera de la cita:** la placa del hub
**lleva cristal en el HSE** (OSC_IN/OSC_OUT, PH0/PH1, que el censo de pines ya
reservaba: `micro_budget.py`, reservas fijas), y **la referencia de 24 MHz del
PHY de USB HS sale de él**, no de una PLL.

La razón es doble y la segunda es la que manda. La medida: con la referencia
HSI → PLL4 → IC15 el PHY no se presenta en el bus, y con el HSE de 48 MHz ÷ 2
enumera a alta velocidad (una corrida de cada lado, #231 y `EN-PLACA.md`,
«El primer día en placa»). La hoja: el HSI deriva de −5 % a +5 % con voltaje y
temperatura (DS14791 Rev 10, p. 165, `TJ` −40 a 125 °C), y el USB de alta
velocidad pide ±500 ppm. Con esa deriva, el HSI no puede ser la referencia
del PHY aunque una corrida a temperatura de escritorio hubiera salido.

**La frecuencia, el mismo 2026-10-01**, ante las tres que caben (38,4, 40 o
48 MHz) y el aviso de que 48 está en el techo del rango:

«si la nucleo funciona bien con 48 que sea de 48 hombre. sin miedo.»

**Interpretación, fuera de la cita:** el cristal del hub es de **48 MHz**, el
mismo de la NUCLEO-N657X0-Q (X3, UM3417 Rev 3 §7.7.2, p. 24) y el único medido.
Con el selector del PHY en su defecto (`OTGPHY1SEL = hse_div2_ck`) su mitad,
24 MHz, es un `FSEL` legal (RM0486 Rev 4, p. 3929), y ninguno de los diez
selectores de la errata §2.2.22 se mueve. Que 48 sea el techo de la hoja (16 a
48 MHz, DS14791 Rev 10, Tabla 49, p. 161) queda dicho y aceptado: es la
frecuencia con la que ST diseñó su propia placa para este chip.

**Lo que el acta NO decide:**

- **La pieza**: tolerancia, ESR, carga (CL1 y CL2 contra la capacidad de pin y
  pista, DS14791 Rev 10, p. 162) y huella.
- **Que las PLL tomen el cristal.** Hoy el censo de relojes las sigue
  alimentando del HSI. Con el HSE presente es una opción nueva, no una
  decisión.

**Consecuencia:** la PLL4 deja de estar atada al PHY y pasa a ser una PLL
libre más para la pantalla, la cámara del tercer chip o lo que el reparto
pida (`reloj_budget.py`).

---

## 1. Por qué existe este papel: la frontera de la ráfaga

**Contexto histórico del 2026-08-30, previo a este reparto.** El desarrollo
del instrumento avanza por ráfagas, y en la última la Voz llegó
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

## 2. Un cerebro aparte, y de la misma clase — FIRMADA (D1)

### 2.1 Por qué no se funden

Fundir el cerebro en el N657 de la Voz se evaluó y se descarta por tres
razones nuevas, y la tercera es A-2. La segunda se apoyaba en un número que
después se midió; lo que sostiene la decisión son la primera y la tercera:

1. **SPI.** El N657 tiene 6 (SPI1-6, tabla de pines de `micro_budget.py`).
   El motor usa 3 para los 16 cortes de CV (motor-digital §5). Fundido, la
   Voz deja de necesitar su esclavo del J2 y quedan **3 maestros para
   ranuras**. D3 del J2 exige que toda ranura activa vaya en SPI de hardware;
   el censo activo de D3 pide 4 (la Voz, el módulo de mandos #178 y las
   reservas de los módulos 8 y 9) y las ocho se cablean. Con 3 no cuadra.
2. **CPU, y una SRAM que ya no es razón.** El motor está presupuestado al
   50 % (~8 300 ciclos por muestra, `carga_motor_budget.py`): un hub que
   comparte chip con su cliente más grande no tiene sitio para crecer. La
   SRAM iba en esta misma fila el 2026-08-30 —«el censo compartido daba rojo
   en las cuatro configuraciones de pantalla»—, pero ese rojo salía de un
   binario ESTIMADO entre 700 000 y 2 000 000 B que nadie había medido. El
   único binario medido desde entonces, la parte compartida del hub
   (`sram_hub_budget.py`, 82 280 B en `c521302`), queda 8,5× por debajo de
   la punta baja de aquel estimado y no trae motores de audio; el de la Voz
   sigue ESTIMADO (`sram_voz_budget.py`, HUECO). La SRAM no sostiene esta
   decisión ni la tumba: es un hueco declarado, no un argumento.
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

### 2.3 E-1, reescrita (registro del 2026-08-30)

> **E-1 (2026-08-30).** El cerebro y la Voz **no se funden**: el hub necesita
> los 6 SPI del chip para las ocho ranuras de D3 y la Voz gasta 3 en el CV;
> la SRAM de la Voz no cierra ni sin pantalla mientras el binario no se mida;
> y por A-2 el cerebro es el producto, no un inquilino de un módulo. Son dos
> N657, y lo que cambió el 30 no es qué instrumento es sino quién ejecuta
> cada mitad.

Ese registro describe la pareja hub/Voz y su presupuesto anterior a la
separación de censos (PR #357). El reparto vigente es el de cuatro N657 del
acta del 2026-09-09 (§0), y la regla que sale de ahí es una sola, y vale
igual para un quinto chip si llega: **cada trabajo tiene su chip, cada chip
su SRAM interna de 4 200 000 B, y cada SRAM su censo.** Hoy existen dos
censos, `sram_hub_budget.py` y `sram_voz_budget.py`; los del mago y de la
interfaz de audio están mandados en §10 (filas 11 y 13) y no se cargan a
ningún vecino mientras tanto.

Lo que sigue en pie de la E-1 vieja: **la puerta sucia no vive en el cuarto
limpio** sigue siendo ley, solo que ahora se cumple en la tarjeta trasera
(#183) y en los aisladores (D-P6), no en la partición de chips. Con A-6 esa
ley gana un cuarto limpio más: los preamplificadores de micrófono (§6).

---

## 3. La cara se muda al hub — D2 y D3' FIRMADAS

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

Comparación histórica del 2026-08-30, con la tabla que entonces estaba en
`sram_voz_budget.py` (peor caso de lo fijo, todo ESTIMADO y sin medir el
binario; los censos se separaron en PR #357):

| Lo fijo en la Voz | Hoy (todo adentro) | Con la cara al hub y la cámara al mago |
|---|---:|---:|
| Binario del motor | 2 000 000 | 2 000 000 |
| Colas de audio y retardos | 400 000 | 400 000 |
| Activaciones de la NPU (gestos) | 800 000 | 0 (al mago, D3') |
| Cuadros de cámara (DCMIPP, doble) | 600 000 | 0 (al mago, D3') |
| Framebuffer 800×480 | 768 000 a 2 304 000 | 0 (al hub, D2) |
| **Queda para tablas y samples** (4 200 000 − lo fijo) | **−368 000 a −1 904 000** | **1 800 000** |

La puerta de la pantalla pedía 1 256 000 B libres. En el escenario histórico
con todo adentro era rojo en las cuatro configuraciones; con la cara en el
hub cierra en el peor caso de esa comparación, sin haber
medido el binario. Cerrar bajo un ESTIMADO no es verde: el censo vivo de la
Voz (`sram_voz_budget.py`) sale HUECO con esos mismos 1 800 000 B libres
contra los 1 256 000 del mínimo, y seguirá HUECO hasta que haya motores de
audio enlazados que medir. De paso mueren el riesgo 5 del motor (contención
del LTDC con el audio) y el riesgo del 27 («si el motor no arranca no hay
pantalla»).

#### El tamaño: 5", el panel del kit de prueba (A-7, acta)

Samuel reutiliza en el instrumento la pantalla de la placa de prueba del
N657 (#231 la describe: 5", 800×480, táctil, en el LTDC). Es lógica de
luthier: el instrumento se construye con lo que hay en la mesa, y el kit es
la mesa. Dos consecuencias que este papel fija:

- **La geometría del panel se parametriza por el contorno de la pantalla**,
  no se cota a mano. El panel al centro (§2) tiene que leer ancho, alto y
  zona activa de un solo sitio, para que el próximo instrumento de la casa
  con una 7" sea un cambio de número y no un rediseño. Es la misma
  disciplina que el case ya usa con sus presupuestos.
- **Lo que traiga el kit se censa antes de comprar nada más**: pantalla,
  cámara, códec, PSRAM, lo que sea. Lo que coincida exactamente con la clase
  que un papel pide (la pantalla lo hace: 800×480, RGB paralelo, táctil) se
  hereda; lo que solo se parezca, no. El principio de «nada de chips
  baratos» del J2 sigue intacto: se hereda por exactitud, no por ahorro.

**Dos versiones, un cobre (A-8).** El primer instrumento lleva la 5" del
kit; los siguientes, una 7" comprada. Para que eso sea una versión y no dos
diseños, tres condiciones que este papel fija y el papel del panel ejecuta:

1. **Misma resolución y mismo camino.** La 7" se elige de 800×480, RGB
   paralelo de 24 bits y táctil capacitivo por I²C, como la 5" del kit. Así
   el firmware, el framebuffer y el censo de pines son **uno**; lo que
   cambia entre versiones es la pieza y la cara, no el hub.
2. **Un conector de pantalla en el hub que sirva a las dos hojas.** Las dos
   pantallas se compran con su hoja en el árbol y se cotejan pin a pin
   (contorno, FPC, orden de señales, controlador táctil). Si sus FPC no
   coinciden, la diferencia se absorbe en un **flex adaptador** por versión,
   nunca en dos cobres del hub. Elegir la 7" con el mismo controlador táctil
   que la 5" es lo que evita que el firmware se bifurque.
3. **La cara es la que cambia de versión.** El DXF del panel de la fila A
   sale de la misma parametrización con dos juegos de números (contorno de
   la 5" y de la 7"), y el panel al centro corre sus §2 y §8 **para las
   dos**: flancos, franjas y profundidad. El case no cambia.

Lo que
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

La SRAM del **hub** hereda el framebuffer, y **solo** el framebuffer: con
D3' la cámara y su NPU se van al tercer chip. Tiene la misma memoria
(4,2 MB + 192 KB de TCM) y ningún sampler, así que su PSRAM por XSPI queda
libre para el framebuffer sin la contención de caudal que `psram_budget.py`
mide en la Voz contra los granos. Eso **se corre, no se afirma**: es la
fila 2 de §10.

**El censo de pines del hub ya corrió** (§10 fila 1, `micro_budget.py`, con
su mutación): con las **seis ranuras J2 en SPI de hardware**, la pantalla al
LTDC en 24 bits, la PSRAM del framebuffer, el tronco I²C y el pedal, el
VFBGA264 reparte 66 pines y deja **80 GPIO libres tras las reservas** —
+53 después de cobrar los 27 estimados de lo vario (las dos ranuras por
USART, MIDI DIN, el ESP32-S3, la radio ESB, la cadena WS2812, clock/reset,
el táctil y el mux). Los escenarios históricos del 2026-08-30 daban +48
con la interfaz de audio sentada (A-6), +38 con RGMII de D9 y **+33** con
las dos. El acta del 2026-09-09 saca la interfaz del hub; esas cifras con
audio conservan el análisis anterior, no presupuestan el cuarto chip.
El VFBGA223 también cierra en los cuatro escenarios, con menos aire. Los
tres encapsulados chicos son rojo por la PSRAM, y el VFBGA198 por la pantalla, igual que en la Voz. **La puerta de
D1 está en verde**: el hub cabe con todo lo que este papel le cuelga.

### 3.2 La cámara y la IA: un tercer N657, como módulo (D3', sustituye a D3) — FIRMADA 2026-09-09

La primera versión de este papel (D3) mudaba la cámara y su inferencia al
hub. Samuel la devolvió con A-9: la IA entra de una, y para eso se dedica un
**tercer N657 «netamente a IA»**. Este papel le da forma, y la forma es la
que el instrumento ya tiene para todo lo demás: **un módulo**.

**D3' — La cámara y la inferencia viven en un tercer N657 con placa propia,
que cuelga del hub como un módulo más, por una ranura J2.** Se le llama aquí
«el mago» por su trabajo, no como bautizo. Lo que eso significa, punto por
punto:

- **Un chip por cámara.** El N657 tiene un solo MIPI CSI-2 de dos carriles
  (cámara-gestos §1). «Cada dedo» pide una cámara cerca, mirando las manos
  sobre el panel; «moviendo mi cuerpo» pide otra, de frente al que toca.
  Son dos sensores y por tanto dos CSI: el tercer chip no es un lujo, es la
  cuenta. La segunda cámara es el mismo módulo otra vez, cableado o como el
  satélite de camino C sobre la radio de D4 (con la inferencia allá, como
  ese camino ya decía).
- **Su memoria es suya.** Las activaciones de la NPU (200 000 a 800 000 B)
  y los cuadros de cámara (150 000 a 600 000 B, ESTIMADOS históricos
  conservados en `sram_hub_budget.py`) dejan de competir con el framebuffer
  del hub por el mismo AXI: la contención que el motor llamó riesgo 5 no se muda al
  hub, desaparece. Los pesos del modelo viven en su propia XSPI.
- **El tiempo real del hub no ve la cámara.** Los seis maestros del J2, el
  evento de nota (≤100 µs) y el protocolo no comparten DMA ni bus con una
  tubería de vídeo. Y por §4.3, un mago muerto es «un sensor que calla»: el
  instrumento sigue sonando.
- **Habla como cualquier módulo.** EEPROM de identidad y descriptor,
  descubrimiento por I²C, y sus landmarks y gestos entran al modelo como
  fuentes (decenas de floats a 30-60 Hz, cámara-gestos §4: kilobits por
  segundo, nada para un enlace de 34,5 MHz). El mapeo sigue siendo estado
  del modelo (cámara-gestos §3). Ocupa una de las dos reservas del censo
  activo de D3 (el «módulo 8»).
- **Puede fallar, crecer y reprogramarse sin tocar el hub.** «Cosas tipo de
  mago» es trabajo de iterar modelos; un módulo se reflashea y se cambia
  de sensor sin abrir la placa que manda.

**Lo que el tercer chip NO compra, dicho antes de que se herede como si
sí:** la frontera musical de cámara-gestos §2, «modulación sí, disparo no»,
la puso la latencia (30 a 80 ms de cámara a landmark), no el chip. Controlar
parámetros, escenas y gestos con las manos y los dedos es modulación y
mando: sí. Tocar notas con los dedos en el aire es disparo, y a 50 ms se
siente como tocar por videollamada. Si Samuel quiere gestos de clase disparo,
eso reabre esa frontera con un presupuesto de latencia propio; A-9 no la
mueve. Y «IA» aquí es inferencia de visión en la NPU (landmarks de mano,
postura, clasificadores cuantizados: lo que ST publica para este chip); el
agente de lenguaje sigue siendo D7.

Lo que cuesta: un tercer N657 con su XSPI y su arranque, una placa más, y
dos censos propios (pines: trivial, CSI dedicado más J2 esclavo, I²C y
XSPI; SRAM: el que §10 fila 11 manda). Lo que devuelve: la Voz recupera los
350 000 a 1 400 000 B de la tabla de §3.1 **y** el hub no los hereda.

D3' sustituye a D3; D2 no depende de ella. **FIRMADA el 2026-09-09,
incluida esta forma de módulo por J2.** Sus censos y el cierre de su papel
propio siguen pendientes (§10 fila 11).

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

## 5. El asiento del procesador de aplicaciones — FIRMADA (D7)

A-3 pide cómputo superior. El acta del 2026-09-09 reparte el trabajo entre
cuatro N657: Voz, hub, IA en el mago e interfaz de audio en el cuarto chip.
La NPU para gestos es del mago. La rapidez y el sonido son objetivos, sin
garantía por este reparto. Lo que un microcontrolador no da (agente de IA a bordo, red de verdad, sistema de
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

## 6. La interfaz de audio — chip dedicado decidido; diseño pendiente de cierre

A-6 mete un subsistema entero que ningún papel tenía: el SAM17 es también
**la interfaz de audio del estudio**, de la clase Clarett+ 4Pre (Focusrite).
Este papel **no la diseña**: es un subsistema con su propia cadena analógica
(preamplificadores de micrófono, phantom, entradas de línea e instrumento,
salidas de línea y auriculares, conversión a 24 bits), su propio papel y su
propia junta. Conserva el análisis de lo que podía exigir al hub y lo que
reabre; el acta del 2026-09-09 cierra su ubicación en un cuarto N657 dedicado
(§6.2). **Las cifras de la clase** (cuántos preamplificadores, cuántas entradas y salidas, óptico ADAT sí o no, tasa
máxima) **se fijan contra la hoja del producto de referencia** antes de
cerrar el papel propio, no de memoria (Principio I).

### 6.1 Lo que ya existe y con lo que choca

Antecedentes del 2026-08-30. La asignación del chip se resuelve en §6.2;
la reconciliación de estos contratos sigue pendiente en el papel propio.

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

### 6.2 Dónde vive la interfaz — RESUELTA mediante ENMIENDA 2026-09-09

**Análisis histórico del 2026-08-30, preservado íntegro:**

Si la interfaz cuelga del hub (lo natural: el hub es quien habla con la
computadora), el censo de §10.1 suma: SAI (el N657 tiene SAI1 y SAI2 en la
tabla de pines; cuántos canales por bloque, contra la hoja), I²C o SPI para
el control de conversores y preamplificadores, un USB HS como dispositivo
compuesto (audio + MIDI + protocolo), y colas de audio en SRAM que hoy no
están en ningún censo del hub. Si cuelga de la Voz, D-P6 crece hasta
absorberla y la Voz pierde parte de lo que §3.1 le devolvía. **Dónde vive es
decisión de Samuel con el papel propio delante**, y ese papel es el
prerrequisito de la fila 1 de §10.

**ENMIENDA del 2026-09-09 (§0):** la interfaz de audio vive en un
**cuarto N657 dedicado**; ninguna de las dos alternativas anteriores (hub o
Voz) es la decisión vigente. Su ubicación queda **RESUELTA** y sus cargas
pertenecen a su propio censo. El cuarto chip se refiere por su trabajo y
**no tiene nombre**.

**El papel propio sigue siendo un prerrequisito pendiente de cierre y
firma**, ahora con el chip dedicado dentro. Existe como propuesta en
`2026-08-31-interfaz-audio-design.md`; esta acta resuelve la ubicación, sin
firmar el resto de esa propuesta. Allí siguen la reconciliación de D-P6 y
los demás contratos de §6.1 y los censos de pines y SRAM de §10. En este
registro no se diseña la interfaz ni se fijan sus consumos, memoria, pines
o encapsulado.

---

## 7. Lo que este papel NO decide

- **Más de ocho ranuras.** El IDC y el censo son de ocho; crecer por encima es
  pregunta de conector y de autopista (D9), no de chip.
- **La pieza del radio ESB**, la del SoM ni las demás piezas de la interfaz
  de audio: el acta del 2026-09-09 sí decide su N657 dedicado; el encapsulado
  y las otras piezas siguen pendientes, con hoja en el árbol (R-M3).
- **El diseño de la interfaz de audio** (§6): papel propio pendiente de
  cierre y firma, con las cifras de la clase contra su hoja y el cuarto
  N657 dedicado ya decidido.
- **Las válvulas:** intención del acta del 2026-09-09, **NO DECIDIDO**. Se
  trata en otra conversación sobre sonido, no sobre cómputo.
- **Cuánto pesa el binario del motor.** Sigue sin medir y sigue siendo el
  estimado más gordo del censo; lo que cambia es que ya no tumba la puerta de
  la pantalla.
- **El nombre del módulo.** La fila de arriba entera se propuso llamar «la
  cabeza» (con la pantalla como «la cara») el 2026-08-30; Samuel no ha
  contestado. Este papel usa «el hub» para el chip del cerebro y «el mago»
  para el tercero por su trabajo; el cuarto chip se refiere por su trabajo
  de interfaz de audio y **no tiene nombre**. No bautiza nada.
- **La segunda cámara** (de cuerpo entero): D3' dice que es el mismo módulo
  otra vez, cableado o por radio, y no decide cuál ni cuándo.
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

D1 y D2 se firmaron el 2026-08-30; D3' y la ubicación de la interfaz se
cerraron el 2026-09-09 (§0). Las enmiendas conservan su estado de ejecución
individual para que no se manden al aire (patrón conocido: #214).

| Papel o guion | Sección | Qué cambia | Dueño | Estado |
|---|---|---|---|---|
| `2026-08-25-j2-punto-a-punto-design.md` | §0.1 | Premisa 1: «dirigida, no sellada» → sellada en N657 (D1) | este papel al firmarse | pendiente |
| ídem | cabecera | «propuesto, pendiente de Samuel» → decidido y mergeado (#210, 26-ago) | una línea, cualquiera | pendiente |
| `2026-08-23-modulo-voz-total-design.md` | E-1 | Reescrita como en §2.3 | este papel | pendiente |
| `2026-08-26-motor-digital-design.md` | §0, actas de la noche, §10 riesgo 5, D-P6 | La pantalla y la cámara salen del motor (D2, D3'); riesgo 5 muere; «#209 sitio 2» sigue cierto; D-P6 se reconcilia con A-6 y el acta del 2026-09-09 | este papel + papel de la interfaz | pendiente |
| `2026-08-26-pantalla-motor-design.md` | §1, §6 | «Por qué cuelga del motor» → del hub; sitio contestado | este papel | pendiente |
| `2026-08-26-camara-gestos-design.md` | §1, §3, §4 | La cámara y la NPU salen del motor al **tercer N657** (D3'); camino C → radio de D4; §2 («modulación sí, disparo no») **sigue en pie y no la mueve A-9** | este papel, con acta de Samuel | pendiente |
| **Papel nuevo: el mago (tercer N657)** | — | Placa, censo de pines y de SRAM, descriptor, dos cámaras y su reparto, modelos y su XSPI | papel propio | pendiente |
| `2026-08-25-j2-punto-a-punto-design.md` | §1.1 censo | El mago ocupa una de las dos reservas del censo activo (el «módulo 8») | este papel | pendiente |
| `2026-08-27-panel-pantalla-al-centro-design.md` | §4.1 | «La cara se muda del cerebro al motor» → se queda en el cerebro; el requisito «el motor no arrancó, en luz» lo cumple la pantalla | este papel | pendiente |
| `2026-08-21-modulo-2-v2-cerebro-design.md` | §1, §6.6, §7, §12 | RP2350B → N657; lista de trabajos de §4.1; la cabeza local es la 7"; el margen de pines se recalcula | este papel | pendiente |
| `2026-08-21-modulo-2-v2-cerebro.md` (plan) | entero | Reescribir contra el N657 (VFBGA264, no QFN-80; `pinout.rs` nuevo) | plan nuevo | pendiente |
| `2026-08-31-interfaz-audio-design.md` (propuesta) | — | Cuarto N657 dedicado decidido (§0); censos propios de pines y SRAM; cifras de la clase contra hoja; reconciliación con D-P6; trasera, masa y phantom | papel propio | pendiente de cierre y firma |
| `hardware/02-midi-cv/pio_budget.py` | — | Retirar a historia: mide un chip que se va | PR de nivelación | pendiente |
| `hardware/03-vco/sram_voz_budget.py` y `hardware/02-midi-cv/sram_hub_budget.py` | — | Separación de censos: Voz sin cara ni cámara/NPU; hub con cara y su binario medido (82 280 B). La interfaz de audio tiene censo propio pendiente (§6.2) | PR de nivelación | **APLICADA — PR #357** |
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

1. **Censo de pines del hub** — ✅ **CORRIDO Y VERDE** (`micro_budget.py`,
   2026-08-30, con su mutación). Seis ranuras J2 en SPI1-6, pantalla al LTDC
   en 24 bits, PSRAM del framebuffer, tronco I²C y pedal: **VFBGA264, 66
   pines repartidos, 80 GPIO libres, +53 tras lo vario**; escenarios
   históricos: +48 con audio, +38 con RGMII, +33 con los dos. El acta del
   2026-09-09 saca la interfaz del hub; esas cifras no son el censo del
   cuarto chip. El VFBGA223 también cierra. **Queda
   mandado** destilar los USART de la Tabla 16 para sentar las dos ranuras
   restantes de D3 con nombre de pin en vez de cobrarlas como GPIO varios.
2. **Censo de SRAM del hub**: framebuffer en PSRAM propia (sin sampler) y
   demanda propia de UI, protocolo y DMA del J2, pendiente de censar. La
   NPU y la cámara pertenecen al mago (D3'); la interfaz de audio, al cuarto
   chip (§6.2). Con su mutación.
3. **USART síncrono del N657** como maestro, contra la hoja: las dos ranuras
   de repuesto de D3 dependen de ello.
4. **Latencia y jitter del enlace ESB** en bring-up, con cota escrita antes
   de medir.
5. **Coexistencia de dos radios de 2,4 GHz** en el mismo cajón: canales y
   antenas.
6. **Drivers de embassy-stm32 para el N6** (SPI, USB HS, LTDC, SAI, DMA).
7. **El binario de la Voz**, medido en escritorio como se midió el del hub
   (secciones ALLOC del ELF, `cargo build --release`; `sram_hub_budget.py`:
   82 280 B en `c521302`): sigue siendo el ESTIMADO que manda en
   `sram_voz_budget.py` (700 000 a 2 000 000 B) porque no hay motores de
   audio que enlazar todavía, no porque falte placa. La Discovery (#231)
   mide ciclos y contención; los bytes del binario no la esperan.
8. **Las cifras de la clase Clarett+ 4Pre**, contra la hoja del producto,
   antes de cerrar el papel de la interfaz.
9. **La hoja del panel de 5" de la DK** (A-7): pieza separable, contorno,
   FPC y táctil; y que se venda suelta. Con ella, el panel al centro recorre
   sus números de §2 y §8.
10. **La 7" de las versiones siguientes** (A-8): 800×480, RGB paralelo de
    24 bits, táctil capacitivo por I²C, y cotejada pin a pin con la 5" del
    kit para decidir si el conector del hub sirve a las dos o hace falta un
    flex adaptador. El panel al centro corre sus números para las dos.
11. **Los censos del mago** (D3'): pines (CSI dedicado + J2 esclavo + I²C +
    XSPI) y SRAM (activaciones de la NPU, cuadros de cámara y pesos del
    modelo), en su papel propio.
12. **La latencia de cámara a landmark**, medida en bring-up (30-80 ms según
    cámara-gestos §5): es lo que decide si la frontera «modulación sí,
    disparo no» se puede reabrir.
13. **Los censos del cuarto chip, dedicado a la interfaz de audio**: pines
    y SRAM, en su papel propio. **PENDIENTE**.

---

## 11. Riesgos

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | ~~El censo de pines del hub no cabe~~ | **CERRADO 2026-08-30**: §10.1 corrido, VFBGA264 con +33 GPIO en el peor escenario histórico (audio y RGMII sentados); no censa el cuarto chip del acta del 2026-09-09 |
| 2 | La pareja hub/Voz requiere dos arranques desde XSPI y dos binarios firmados | FSBL + Rust vivos en la Discovery (#231, riesgo 6 del motor) |
| 3 | Dos radios de 2,4 GHz se pisan | §10.5 medido; suplente: ESP-NOW sobre el S3 (§4.2) |
| 4 | Se reabren tres papeles con acta (pantalla, cámara, panel al centro) | **D2 firmada**; la cámara la reabre A-9; **D3' firmada con su forma el 2026-09-09**. Sigue pendiente ejecutar las enmiendas de §9 |
| 8 | El mago añade su arranque desde XSPI, binario firmado y flash externa a la pareja hub/Voz | El bring-up del mago sale del mismo #231; su papel propio lo acota |
| 10 | El cuarto N657 dedicado a interfaz de audio tiene pendiente el cierre de su papel y sus censos propios | Cierre y firma de su papel y censos de pines y SRAM de §10.13; el reparto por silicio no prueba ausencia de cuelgues ni superioridad de rapidez o sonido |
| 9 | «Cosas tipo de mago» se lee como tocar notas en el aire, y la latencia no lo permite | §3.2 lo dice de frente; §10.12 lo mide antes de prometerlo |
| 5 | La computadora ve dos dispositivos de audio (D-P6 y A-6) | El papel de la interfaz los reconcilia en uno compuesto |
| 6 | La trasera y el valle recién dibujados no tienen sitio para los conectores de la interfaz | El papel de la interfaz cuenta conectores contra el estudio del valle (panel al centro §5) |
| 7 | No hay plata para la Discovery | Decisión de Samuel; mientras tanto, todo lo de §10.1-10.3, 10.6 y 10.8 es papel y se puede correr |
