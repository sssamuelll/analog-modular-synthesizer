# El J2 punto a punto: la estrella se queda, la juntura muere

**Fecha**: 2026-08-25 · **Estado**: propuesto, corregido por junta de cuatro
lentes, pendiente de Samuel · **Reabre**: el contrato congelado del J2
(dieciséis, núcleo §5, `j2.rs`)

---

## 0. Por qué se reabre un contrato congelado

El encargo de Samuel, con sus palabras: *«que el control sea tan rápido y
violento que se sienta como un Ferrari en una autobahn»*, y del mismo día:
*«mete los 3 peldaños con todo pero nada de chips baratos, quiero puro bólido
ferrari en una autobahn»*. La cuenta que lo convierte en encargo de bus y no
de chip:

```
el contrato del J2      : 10,0 MHz   (congelado el 2026-08-16 por el
                                      módulo 3, para el instrumento de 4 voces)
lo que ya exige hoy     :  8,70 MHz  = 87 % del contrato
lo que la red de hoy da :  8,90 MHz  = +2,3 % de margen (enlace_budget.py,
                                      caso «hoy: 8 ramas, un oyente por rama»)
cada módulo más         : +0,58 MHz  (R-M4: 288 bits × 1 kHz mínimo / techo
                                      del 50 % — orquestación §5.3)
se pasa del contrato con 3 módulos más
```

Dicho sin trampa, porque la primera versión de este papel la hizo: **el bus
de hoy cierra — por un 2,3 %.** (El 8,54 «NO» de la tabla del guion es el
caso de la T interna, que pertenece al mundo del doble micro que la premisa
§0.1 elimina.) Lo que no cierra es el futuro: el instrumento está al 87 % de
su bus **antes de estar terminado**, el plan tiene más de tres módulos, y la
promesa del proyecto es modularidad — hoy **cada módulo que se enchufa le
quita velocidad a los demás**, y tres más lo tumban.

Y el encargo de fondo no es «que quepa»: es control a velocidad de audio
(§2, D9), que ningún techo del bus compartido puede pagar.

### 0.1 Las premisas de las que este papel cuelga

Este papel NO decide solo. Cuelga de dos decisiones dirigidas hoy y sin
sellar, y lo dice en voz alta para que nadie las herede como hechos:

| Premisa | Estado | Dónde se decide |
|---|---|---|
| El cerebro lleva un micro con maestros serie independientes de sobra (candidato STM32H750) | **dirigida, no sellada** | `micro_budget.py` (PR #209) + el guion de pines del cerebro (§7) |
| El módulo de Voz pasa a UN micro clase H750 (decisión de Samuel: los 16 cronómetros a la vez, y «nada de chips baratos») | **dirigida, no sellada** | PR #209 y la spec que reemplace al #201 |

Las dos premisas son **anclas de los números**: todo el techo de la clase
rápida (§4) — el esclavo a 31 MHz, el `tv(SO)`, la cadena del viaje — está
leído de la hoja del H750. Si el chip de la Voz cambiara, §4 se recalcula
contra las filas del chip que sea, y este papel lo dice aquí y no en letra
chica.

Si la primera premisa cae, este papel cae entero: el RP2350 del cerebro
tiene 2 SPI y **2 GPIO libres de 48** (PR #208). No hay versión de este
diseño sobre el chip de hoy.

---

## 1. Lo que se levanta, cita por cita

El contrato vigente vive congelado en cuatro sitios:

- núcleo §5, tabla de bloques (línea 597): *«Trama de **72 bits** con `CS`
  abajo de punta a punta, modo 1, ≤10 MHz; orden `[U7][U6][U5]` — Congelado
  por el módulo 3, no se toca»*.
- `hardware/03-vco/README.md:110`: *«SPI modo 1, ≤10 MHz. **CS3 abajo durante
  los 72 relojes de la trama entera**»*.
- `software/nucleo/core/src/j2.rs:2` y su test `:143`
  (`assert_eq!(BITS_TRAMA, 72)`).
- `hardware/03-vco/notes/bring-up.md:336-346` y el criterio de passthrough
  (`check_bringup.py:127`).

Y la topología que ese contrato presupone vive en:

- **architecture-poly §8, el origen**: *«El mazo es en estrella, un cable por
  módulo. **Tenía que serlo**: el J2 lleva un solo `CS`»*. Ese «tenía que
  serlo» es el razonamiento fundacional que este papel jubila: la estrella se
  queda, pero ya no porque el bus obligue — porque cada rama es un enlace.
- cerebro §4 (línea 119, copia del anterior): *«El mazo es **en estrella, un
  cable por módulo**… un `CS` por rama»* — y línea 147: *«`MISO` es un **bus
  compartido entre ocho ranuras**»*.
- `pinout.rs:41-43`: `d(2, "J2 SCLK"), d(3, "J2 MOSI"), d(4, "J2 MISO")` —
  **un pin del micro por señal para las ocho ranuras**. Ahí, y solo ahí, está
  la juntura.

### 1.1 El censo cambió debajo del contrato

La estrella de 8 se dimensionó para un mundo con módulos 3, 4, 5, 6 y 7
separados. Ese mundo murió por actas:

- E-3 (voz-total :609-618): la bahía se funde en la Voz — *«una sola bajada
  de J2 en vez de dos… y una ranura libre»*.
- E-5 (voz-total :639-644): el módulo 4 desaparece — mezcla, volumen, salida
  y oídos se mudan a la placa de la Voz.
- voz-total :150-162: los módulos 5 y 7 *«desaparecen como hardware
  separado»*; el 6 se ejecuta en los micros de la Voz.

Clientes reales del J2 en el plan escrito hoy: **la Voz total** (una
identidad, una bajada, con casi todo el instrumento dentro) y **el módulo de
mandos** (#178, la ranura que E-3 liberó). Reservadas: dos para los futuros
módulos 8 y 9 — que el núcleo §10 legisla como submódulos clase Daisy
(STM32H750), no como placas tontas. Libres: cuatro.

**Dos clientes activos repartiéndose un bus diseñado para ocho.** El
problema nunca fue cuántos son: es que comparten.

### 1.2 Y la frase que muere con más gusto

Cerebro §7 (citado por el #178): el J2 *«no admite un cliente más»*. Con seis
ranuras físicas huérfanas. Esa frase es la negación literal de la promesa del
instrumento, y este papel existe para matarla.

---

## 2. Las decisiones

### D1. La estrella física se queda; la juntura eléctrica muere

El mazo ya es en estrella: ocho cables independientes cerebro→módulo, cada
IDC 2×6 con **su propio** SCLK, MOSI, MISO y CS (cerebro, tabla de
posiciones :107-115, congelada por el módulo 3). Las señales homónimas se
juntan hoy en un solo pin del micro del cerebro (`pinout.rs:41-43`).

La decisión: **dejar de juntarlas.** Cada ranura pasa a ser un enlace SPI
punto a punto con su propio maestro en el cerebro.

Lo que esto NO toca, y es la mitad del argumento:

- **El conector no cambia ni un pin.** La tabla de posiciones del IDC 2×6
  sobrevive idéntica.
- **El mazo no cambia.** Los mismos ocho cables.
- **Ningún módulo cambia de forma.** Un módulo v1 que hable el dialecto
  legado (72 bits, modo 1) enchufa y funciona: su enlace se cronometra al
  piso legado (D2).

Cambia **una placa** (el cerebro) y el firmware.

### D2. El reloj es por enlace: lo declara el esclavo y lo sanciona la medida

Muere el `≤10 MHz` global. Nace:

> **El reloj de cada enlace es el mínimo de tres términos: lo que da el
> maestro de esa ranura, lo que declara el esclavo, y lo que la sanción de
> esa ranura tenga registrado.**

Los tres términos, cada uno con su casa:

1. **El maestro**: constante del diseño del cerebro, por ranura (D3).
2. **El esclavo lo declara en su EEPROM de identidad**, que el cerebro lee
   por I²C **antes** de la primera palabra de SPI. El orden ya existe: R-A1
   de orquestación obliga al descubrimiento antes de publicar nada, y el
   I²C es por-ranura vía mux (cerebro :122-124), independiente del SPI. La
   declaración **se relee en cada arranque** — el enchufe en caliente no es
   caso de uso del instrumento (los módulos se atornillan con la caja
   apagada), y un módulo que desaparece en sesión es el modo de fallo de
   identidad ya legislado, no un caso de reloj.
3. **La sanción es una propiedad de la ranura, no del módulo** — depende del
   mazo de esa ranura (largo, terminación), no de quién esté enchufado. Vive
   en **la tabla de sanción del firmware del cerebro**, versionada en el
   repositorio: una fila por ranura con (largo de mazo declarado, reloj
   sancionado, fecha y método de la medida). La escribe el bring-up del
   cerebro (§8, riesgo 1) y **se invalida si el mazo de esa ranura cambia**
   — la fila lleva el largo justamente para que un mazo nuevo desminta la
   fila vieja en revisión, no en la placa. Una ranura sin fila corre al piso
   legado (R-P4).

**El piso legado** no son «10 MHz» a secas: es el **menor** entre 10 MHz y
el reloj adoptado en el bring-up del módulo si está registrado — porque el
Paso 8 del bring-up del módulo 3 ya legisla que *«ESTE número es el
contrato, no el ≤10 del spec»* (`check_bringup.py:179`). Cronometrar por
encima de lo que aquel bring-up adoptó sería el fallo silencioso exacto que
R-P2 existe para impedir.

Esto generaliza R-M4: cada módulo ya declaraba su *tasa*; ahora declara
también su *reloj*. La fila nueva del descriptor de identidad es de la misma
especie que las que ya lleva.

### D3. Todas las ranuras activas van en SPI de hardware — nada de chips baratos

Decisión de Samuel, textual: *«nada de chips baratos, quiero puro bólido»*.
Aterrizada:

- **Las ranuras activas del censo (§1.1) — la Voz, el módulo de mandos, y
  las reservas de los módulos 8 y 9 — van todas en maestros SPI de
  hardware** del cerebro. El H750 trae 6 (hoja p2); el censo activo pide 4.
- **Las ocho ranuras se cablean, para que contar cuadre**: los 6 SPI van a
  las 4 activas más 2 de las libres (repuesto rápido); las 2 ranuras
  restantes salen por USART síncrono (12,5 MHz de CK, Tabla 192 — solo los
  USART tienen el modo, Tabla 5; los UART no) y quedan rotuladas como
  repuesto/legado. 6 + 2 = 8 enlaces, 32 pines. Un detalle que el guion de
  pines hereda: el USART síncrono como maestro no trae NSS por hardware
  (la Tabla 192 solo especifica NSS en esclavo), así que **el CS de esas
  dos ranuras sale por GPIO** — compatible con el framing de D5, que solo
  exige CS abajo la trama entera.
- **La clase económica no es un objetivo de diseño.** Si un día un módulo
  hambriento cae en ranura USART, se recablea a un SPI libre — decisión de
  layout, no de contrato.
- **Consecuencia para el #178**: el micro del módulo de mandos **no se elige
  por barato**. Su ranura es rápida; que su chip la aproveche o no lo decide
  su placa (R-J2), pero la ranura no lo limita. (El techo del RP2350 como
  esclavo por su periférico — 12,5 Mb/s, hoja §12.3.4.4 — queda en §4 como
  referencia de lo que un chip barato podría, no como clase del diseño.)

En el H750 la pantalla no compite por un SPI: el chip trae LTDC (controlador
de pantalla por hardware, hoja p2). Los SPI1/2/3 son excluyentes con I²S
(Tabla 1, nota 2) — irrelevante en el cerebro, donde el audio no entra
(núcleo §5.0), pero **vinculante en la Voz**, donde el códec de E-5 se
comerá uno de esa clase; es del presupuesto de pines de la Voz y queda dicho
para que nadie lo descubra ruteando.

Y una consecuencia de encapsulado que ya se puede decir en papel: 8 enlaces
× 4 pines = 32, más LTDC en RGB paralelo (~24-28 pines), dos USB, I²C + mux,
MIDI y gates — **el LQFP100 (82 GPIO) se descarta ya**; el encapsulado
mínimo realista es el LQFP144 (114 GPIO), y lo confirma el guion de pines
del cerebro (§7).

### D4. Full duplex de verdad: el MISO deja de ser un bus

Con MISO privado por enlace:

- **Muere la pelea de drivers** (`enlace_budget.py:264`, el análisis del
  divisor de VIH en :248): eran física del bus compartido.
- **Sobrevive el pull-down de MISO en el cerebro, por su segunda función**:
  *«para que un `MISO` sin nadie lea cero»* (cerebro :173) — es la
  detección de ranura vacía, y es por-enlace. Muere el análisis de pelea;
  la resistencia se queda.
- **Muere la mitad de R-J1** — *«un registro de desplazamiento que suelte
  bien la línea también cumple»* (orquestación :442-443). Ya no hay línea
  que soltar: cada MISO tiene un solo dueño. R-J1 se reescribe: la ranura
  exige identidad I²C y tolerar el reloj que declara; nada más.
- **Nace la vuelta continua.** Hoy la vuelta comparte el bus con la ida.
  Punto a punto, cada trama de bajada puede traer simultáneamente su subida:
  las medidas de R-J4 viajan en el mismo giro, en vez de robarle aire al
  tono. (Qué viaja en esa subida — telemetría, log, TuneProgress — lo
  reparten sus papeles; este solo abre el canal.)

### D5. El framing y el modo sobreviven; los 72 bits pasan a dialecto legado

- **El framing ES el CS**: la trama es lo que cabe entre bajada y subida de
  CS, de largo variable. (Lo articuló el difunto #201 en su D1 y lo hereda
  el cambio 1 de orquestación; este papel lo confirma como contrato
  por-enlace.)
- **Modo 1 se queda** (CPOL=0, CPHA=1, bring-up.md :340).
- **72 bits deja de ser EL contrato y pasa a ser UN dialecto**: el del
  módulo v1 con tres conversores en cadena. `j2.rs` lo conserva como caso
  legado con su test; deja de ser la definición del bus.

### D6. El techo del 50 % muere como árbitro global; nace ocupación por enlace

`TECHO_OCUPACION = 0.50` (latencia_mano :68) racionaba **un** recurso entre
todos. Con enlaces privados, cada uno lleva su presupuesto contra su propio
reloj. **El techo por enlace lo fija `trama_j2_budget.py`** (§7); mientras
no derive uno mejor, hereda el 50 % — por enlace, como piso conservador con
origen citado, no como dogma nuevo.

Consecuencia inmediata y medible: el techo de 9,19 kHz del lazo del panel
(latencia_mano :254-256) era un techo **del bus compartido** — en el enlace
privado de la Voz, el lazo puede subir hasta donde lo dejen los extremos.
Ese número se recalcula en el guion, no aquí.

El árbitro que R-M4 pedía (`trama_j2_budget.py`, nunca escrito) **cambia de
oficio antes de nacer**: ya no reparte un bus común; asevera enlace por
enlace que lo declarado cabe en lo sancionado.

### D7. La simultaneidad entre módulos, dicha sin heredar una promesa

Corrección sobre la primera versión de este papel, en voz alta: hoy los
gates **no** salen «en el mismo instante» que el tono por el bus — salen por
cuatro cables aparte (`pinout.rs:62-65`), y el «tono y gate en el mismo
instante» del núcleo (:809-813) es el **beneficio futuro prometido** de
meterlos en la trama, no una propiedad del bus de hoy (orquestación :676-678
lo declara sin resolver). Este papel no mata una propiedad existente; hereda
una promesa.

Y la cumple mejor de lo que el bus podía, con dos verdades:

1. **Dentro del módulo, la simultaneidad es del enlace**: todo lo que viaja
   junto en una trama del enlace de la Voz llega junto. Las dieciséis voces
   viven en un módulo — el caso musical entero es intra-enlace.
2. **Entre módulos** (los futuros 8/9), la llegada depende del reloj y el
   largo de trama **de cada enlace**: dos enlaces que arrancan juntos
   terminan en instantes distintos si sus relojes difieren. El sesgo
   dominante no es el arranque de los DMA (decenas de ns): es el **fin de
   trama**. Quien necesite simultaneidad inter-módulo la presupuesta contra
   eso — el papel del evento es el dueño de esa cota, y el bring-up la mide
   (§8, riesgo 3).

### D8. Peldaño 2 — la respuesta viaja al ciclo siguiente

El techo del enlace rápido de hoy lo fija el **viaje de ida y vuelta dentro
del mismo medio ciclo** (§4.2): el flanco baja al módulo, el esclavo tarda
`tv(SO)` en soltar su bit, y el bit tiene que volver antes del flanco de
muestreo. Con los máximos de la hoja, eso topa en **≈19,7 MHz** al peor mazo.

La decisión: **el dato de vuelta se registra en el esclavo y sale al ciclo
siguiente; el maestro lee la subida corrida un ciclo.** El viaje deja de
competir con el medio ciclo — solo la ida (reloj→dato del maestro) gobierna
el flanco, y el techo del enlace sube al **límite eléctrico del esclavo:
31 MHz** (fila «slave full-duplex», Tabla 193).

Precio, dicho entero: un ciclo muerto por trama (despreciable — 1 bit sobre
cientos), firmware en los dos extremos, y **el dialecto legado no lo habla**
— los módulos v1 corren al piso legado igual que antes, así que no les
cuesta nada. La regla del protocolo entra al contrato del enlace; su
verificación es el mismo criterio de ojo de §8.

### D9. Peldaño 3 — la autopista diferencial sobre los cuatro pines muertos

El porqué, con el número del sueño: **control a velocidad de audio**. Que
cualquier parámetro se module a tasa de audio convierte el control en
síntesis — FM de lo que sea contra lo que sea, por el cable digital. Eso
pide:

```
16 voces × 4 parámetros × 48 000 Hz × 16 bits ≈ 49 Mb/s
```

Ningún enlace de 3,3 V con flancos contra tierra lleva eso limpio por 74 cm
al lado de audio de 24 bits. La señalización **diferencial** sí: dos hilos
en espejo, señal pequeña, el ruido se cancela en el par — es *más
silenciosa* que lo de hoy, no más ruidosa, y es exactamente cómo conviven
«digital y analógica sin molestarse».

Y el cobre ya existe: **los pines 9-12 del IDC están muertos** — eran
`TUNE_OUT 1-4`, y dieciséis (decisión 2) los dejó sin uso: *«Las cuatro
líneas `TUNE_OUT` de los pines 9-12 del J2 quedan sin usar; los números
vuelven por `MISO`»*. El cerebro hoy solo los cablea en la ranura 1
(cerebro :126-128). Cuatro pines = **dos pares diferenciales**: bajada y
subida, full duplex, clase 100 Mb/s con transceptores de a dólar en cada
punta.

La decisión: **la autopista diferencial es el camino declarado del enlace de
la Voz** (y de cualquier ranura hambrienta futura), sobre los pines 9-12,
sin tocar conector ni mazo.

**Y la forma recomendada de ese camino no es artesanal** — es la pregunta de
Samuel del mismo día (*«¿no hay manera de tener esos 50 de forma relajada,
sin truco, una obra del state of the art de electrónica 2026?»*), y la
respuesta de la industria tiene nombre: **Ethernet de un solo par
(100BASE-T1, el estándar automotriz)**. 100 Mb/s full duplex por UN par
trenzado, diseñado para el infierno eléctrico de un carro; el mismo linaje
que el audio profesional lleva una década usando en escena (Dante, AVB/TSN)
con latencia determinista. Lo que lo vuelve candidato natural y no capricho:

- **El H750 ya trae el MAC de Ethernet con su DMA dedicado** (hoja p2 y
  §3.14, p50: *«Ethernet MAC interface with DMA controller»*). Cada extremo
  solo necesita un PHY.
- **Aislamiento galvánico en el acoplo**: cero cobre de masa compartido
  entre placas por el enlace — «digital y analógica sin molestarse» pasa de
  disciplina a física del conector.
- **Tramas crudas de capa 2, sin pila TCP** — la regla del núcleo §10 («el
  núcleo de tiempo real nunca ve una pila TCP») queda intacta, que es
  exactamente como operan Dante y AVB.
- 100 Mb/s = **2× el objetivo de velocidad de audio** (49 Mb/s), relajado.
- El bus se depura con Wireshark, y cualquiera en el mundo puede construirle
  un módulo al instrumento con piezas de catálogo.

Su precio, sin maquillar: un PHY por extremo, **un chip switch en el
cerebro** (un MAC no maneja ocho PHYs), micro con MAC en cada módulo rápido
— que es la directiva «nada de chips baratos» empujando en la misma
dirección — y más firmware, por el camino más pisado del embedded.

**La elección entre las dos formas (par LVDS artesanal o 100BASE-T1) es
decisión de Samuel y está pendiente**; el cobre reservado es el mismo para
las dos. Lo que la sella, sea cual sea, porque nada de esto se asevera sin
hoja (Principio I):

1. **La parte se elige contra su datasheet** (el PHY de T1 o el transceptor
   LVDS; la parte concreta NO está elegida y este papel no la inventa).
2. **Su presupuesto ejecutable**: caudal, consumo, y el término feo dicho
   ya — un par en cinta plana **sin masa adyacente** (los GNDD del conector
   están en los pines 2 y 6, no junto al 9-12) tiene control de impedancia
   pobre; eso se mide, no se supone. (100BASE-T1 está especificado para
   pares sin blindar en ambiente hostil, que es justo este caso — pero
   «especificado para» no es «medido aquí».)
3. **El criterio de ojo en bring-up**, como todo enlace (R-P4).

Hasta que eso cierre, la autopista es camino declarado con cobre reservado
— no un número del que dependa ningún otro papel.

Los tres peldaños, juntos:

| Peldaño | Techo del enlace de la Voz | Qué lo fija |
|---|---|---|
| 1 — punto a punto | ≈19,7 MHz (peor mazo, máximos de hoja) | el viaje de ida y vuelta (§4.2) |
| 2 — respuesta al ciclo siguiente | **31 MHz** | la fila eléctrica del esclavo |
| 3 — autopista diferencial | **clase 100 Mb/s** → control a velocidad de audio | el transceptor y su medida |

---

## 3. Las reglas

> **R-P1. Ningún número de un enlace gobierna a otro.** Ocupación, reloj y
> largo de trama son por-enlace. Un guion que sume ocupaciones de enlaces
> distintos contra un techo común está reconstruyendo el bus que este papel
> mata. Vigila: `trama_j2_budget.py` (que asevera por-enlace y no publica
> suma global).

> **R-P2. El reloj de un enlace nunca supera el mínimo de D2** (maestro,
> declarado, sancionado). La violación es un módulo que recibe bits que no
> puede leer — el fallo silencioso exacto del Principio V. Vigila:
> `trama_j2_budget.py`, que falla si un módulo no declara reloj o si una
> ranura activa no tiene fila de sanción.

> **R-P3. Para un enlace punto a punto, el modelo concentrado está
> jubilado.** No es que valga hasta una frontera: con una rama sola (~42 pF)
> y el driver de 12 mA, el flanco que el propio modelo predice (~8 ns) ya es
> más rápido que la frontera de vuelo del cable (~22 ns) **a cualquier
> reloj**. La cinta punto a punto es una línea de transmisión, punto: se
> termina en la fuente (como el bring-up del módulo 3 ya hace — *«terminación
> serie en el extremo del cerebro»*, bring-up.md :343) y se mide. Vigila: el
> `enlace_budget.py` reescrito, cuya aserción nueva es exactamente esta —
> que nadie use el modelo viejo para sancionar un enlace.

> **R-P4. Todo enlace se sella con medida, no con modelo — rápido o no.**
> El reloj de operación de cada enlace lo sanciona el osciloscopio en
> bring-up (ojo de datos y flanco monótono en el extremo del módulo), y el
> resultado vive en la tabla de sanción (D2). Sin fila: piso legado. Esto
> aplica también a los 12,5 MHz del USART síncrono — están por encima del
> rango que el modelo viejo validó (8,54-10 MHz) igual que los demás.
> Vigila: `trama_j2_budget.py` — la misma aserción de R-P2 (ranura activa
> sin fila de sanción es fallo) es el diente de esta regla; el criterio de
> ojo vive en el procedimiento de bring-up del cerebro y su resultado, en
> la tabla de sanción.

---

## 4. Los números que gobiernan, con sus fuentes

### 4.1 Los extremos

| Número | Valor | Fuente |
|---|---|---|
| H750 maestro SPI1/2/3 (2,7-3,6 V, **rev V**) | 100 MHz | DS12556 Rev 8, Tabla 193 (p. 291) |
| H750 maestro SPI4/5/6 (rev V) | 50 MHz | ídem |
| H750 **esclavo full-duplex** (2,7-3,6 V, rev V) | **31 MHz** | ídem — la fila que manda en la Voz con D8 |
| H750 esclavo solo-receptor (rev V) | 100 MHz | ídem |
| H750 esclavo, `tv(SO)` | **típ 12,5 / máx 16 ns** | ídem — **gobierna el máx**, no el típico |
| H750 maestro, `tsu(MI)` | mín 2 ns | ídem, misma tabla |
| H750 USART síncrono maestro | 12,5 MHz de CK | DS12556 Tabla 192 (p. 289) |
| RP2350 esclavo por periférico PL022 | 12,5 Mb/s (= clk_peri/12) | hoja RP2350 §12.3.4.4 — **referencia de chip barato, no clase del diseño (D3)** |
| RP2350 esclavo por PIO | sin cifra en la hoja | derivación propia ~37-50 MHz; NO sella nada |

Aviso que va aquí y no en letra chica: los números eléctricos del H750
**dependen de la revisión del silicio** — la rev V (la de 480 MHz) es más
lenta que la rev Y en varias filas. La revisión comprada se confirma contra
su tabla antes de sellar (§8, riesgo 2).

### 4.2 La cadena que fija el techo del peldaño 1

Full duplex en modo 1, respuesta en el mismo ciclo: medio periodo ≥
`tv(SO)máx` + vuelo de SCLK (ida) + vuelo de MISO (vuelta) + `tsu(MI)`:

```
rama (mm)   vuelo i/v      medio periodo    f_max mismo-ciclo
  738        7,38 ns         25,38 ns          19,7 MHz
  400        4,00 ns         22,00 ns          22,7 MHz
  200        2,00 ns         20,00 ns          25,0 MHz
```

(con `tv(SO)` = **16 ns máx** y `tsu(MI)` = 2 ns, los dos de la Tabla 193;
propagación 5 ns/m **POR CONFIRMAR** contra la cinta real. Con el típico de
12,5 ns saldrían 22,9/27,0/30,3 — se anota para que nadie «recupere» ese
margen sin saber qué está comprando.)

Tres lecturas obligatorias:

1. **El techo del peldaño 1 no lo pone ni el maestro (100) ni el esclavo
   (31): lo pone el viaje del dato por el mazo.**
2. **El largo de la rama es una palanca por enlace.** El heredero del #199:
   la ranura de la Voz se elige por longitud de mazo. Acortarla compra
   megahercios con una decisión de layout.
3. **D8 jubila esta cadena entera**: con la respuesta al ciclo siguiente, el
   techo pasa a la fila eléctrica del esclavo (31 MHz) y el largo deja de
   fijar el reloj.

El tráfico declarado de hoy del instrumento entero son **4,35 Mb/s** (544
bits × 8 kHz, latencia_mano). Contra eso, con el mismo criterio de ocupación
del 50 % que usa la cuenta de §0 — y en crudo entre paréntesis:

| Enlace de la Voz a | lleva | (crudo) |
|---|---|---|
| 19,7 MHz (peldaño 1) | **2,3×** el instrumento de hoy, por dirección | (4,5×) |
| 31 MHz (peldaño 2) | **3,6×** | (7,1×) |
| clase 100 Mb/s (peldaño 3) | **11,5×** — control a velocidad de audio (49 Mb/s) incluido | (23×) |

…y los demás módulos ni se enteran.

### 4.3 La física del cable, dicha sin frontera falsa

Vuelo una vía en 738 mm: 3,69 ns. El criterio de vuelo (flanco > 6× vuelo →
22 ns) se aplica **al flanco, no al reloj** — y el flanco de un driver de
12 mA sobre una rama sola (~42 pF) es ~8 ns según el propio modelo viejo. O
sea: **el enlace punto a punto está en régimen de línea de transmisión desde
el primer megahercio** (R-P3). Terminación serie en la fuente, y la medida
manda (R-P4). La constante y la aserción entran al guion reescrito con esta
derivación citada.

---

## 5. Lo que muere, lo que sobrevive, lo que nace

| | Qué | Nota |
|---|---|---|
| **Muere** | El `≤10 MHz` global | D2 |
| **Muere** | El techo de ocupación del 50 % como árbitro común | D6 — renace por-enlace |
| **Muere** | El MISO como bus: la pelea de drivers y el divisor de VIH | D4 |
| **Muere** | La juntura en GPIO 2/3/4 del cerebro y el «no admite un cliente más» | D1, §1.2 |
| **Muere** | El techo de 9,19 kHz del lazo del panel (era del bus) | D6, se recalcula |
| **Muere** | La mitad «suelta bien el MISO» de R-J1 | D4 |
| **Muere** | El «tenía que serlo» de architecture-poly §8 | §1 — la estrella se queda por otra razón |
| **Muere** | El modelo concentrado para enlaces punto a punto | R-P3 |
| **Sobrevive** | El conector IDC 2×6, pin a pin, y el mazo en estrella | D1 — cero cambio de cobre en módulos |
| **Sobrevive** | Modo 1, framing por CS | D5 |
| **Sobrevive** | El pull-down de MISO — por su segunda función (ranura vacía lee cero) | D4 |
| **Sobrevive** | El descubrimiento por I²C antes del SPI (R-A1) — y pasa a cargar el reloj declarado | D2 |
| **Sobrevive** | R-M4 (declarar la tasa) — generalizada con el reloj | D2 |
| **Sobrevive** | R-J2 — reforzada: ni el reloj es ley común | D2/D3 |
| **Nace** | El campo `reloj declarado` en la identidad EEPROM | D2 |
| **Nace** | La tabla de sanción por ranura, en el firmware del cerebro, versionada | D2 |
| **Nace** | Ranuras rápidas para todo el censo activo — nada de chips baratos | D3 |
| **Nace** | La vuelta full-duplex en el mismo giro | D4 |
| **Nace** | La ocupación por-enlace y el `trama_j2_budget.py` con oficio nuevo | D6 |
| **Nace** | La respuesta al ciclo siguiente (peldaño 2) | D8 |
| **Nace** | La autopista diferencial sobre los pines 9-12 (peldaño 3) | D9 |

---

## 6. El mapa de enmiendas

Lección del #201 aplicada dos veces: la primera junta de este papel encontró
tres documentos ausentes del mapa — están ahora.

| Documento | Sección | Tipo | Qué |
|---|---|---|---|
| **architecture-poly** | §8 (*«Tenía que serlo: el J2 lleva un solo CS»*) | Rewrite | El origen de la topología: la estrella se queda, el porqué cambia (D1) |
| **autopista (plan 2026-08-23)** | :21, :91-92, :104, :110, :282-294 | Rewrite | Sus tasas están legisladas contra el bus compartido de 10 MHz y el techo global del 50 % — todas pasan a por-enlace; su POR_CONFIRMAR de :110 lo contesta este papel |
| **issue #158** | *«La placa del cerebro no cambia. Ni un pin»* | Comentar | Contradicho literalmente por la premisa §0.1 — se anota en el issue, no se edita en silencio |
| núcleo §5 | :597 (tabla de bloques) | Rewrite | La fila del J2: de «72 bits… ≤10 MHz, congelado» a por-enlace (D2/D5) |
| núcleo | :218 («estrella con MISO compartido, 8 stubs») | Rewrite | Estrella sí; MISO compartido muere |
| núcleo | :809-813 (tono y gate en la trama, promesa) | Sync | D7 la hereda y la cumple intra-enlace |
| núcleo §10 | :1310-1316 («caben en el J2 ya congelado») | Rewrite | El aplazamiento se reescribe sobre enlaces privados |
| núcleo | :1209 (bring-up: «72 bits, CS abajo entero») | Patch | Pasa a prueba del dialecto legado |
| núcleo | la cuenta de capacidad del bus (3,5 %) y la tabla de módulos del README del núcleo («j2 = trama de 72 bits del contrato congelado») | Patch | Copias del contrato viejo fuera de las filas anteriores |
| orquestación | R-M4, R-J1 (:442-443), cambio 1 | Rewrite/Patch | D2/D4/D5 |
| orquestación §7 | :449-454 («caben en el J2 congelado») | Sync | Segunda copia del argumento |
| orquestación §10 | la ficha de `trama_j2_budget.py` («asevera que la suma queda por debajo de un techo declarado») | Rewrite | El oficio nuevo: por-enlace, sin suma global (D6/R-P1) |
| cerebro §3/§4 | :91 (tabla), :105-128, :119, :147, :171-173 | Rewrite | La pieza del enlace entera: 8 maestros, muere la juntura; el pull-down se queda por D4 |
| cerebro | :699 (segunda copia del «SPI0 se lo lleva el J2») y :794 (riesgo 11) | Patch | Copias fuera de la fila anterior |
| cerebro §7 | «no admite un cliente más» | Remove | §1.2 |
| cerebro | :449-450 (J2 ocupa el SPI0…) | Rewrite | Reparto de maestros del chip nuevo (D3); pantalla a LTDC |
| voz-total §3.4 | la ventana de MISO | Patch | Con MISO privado y D8, la regla se reformula por-enlace |
| dieciséis §2 decisión 2 | «los números vuelven por MISO» | Clarify | Siguen volviendo — ahora sin pelear el bus |
| dieciséis | la copia completa de la regla de alta impedancia del MISO | Patch | La mitad de R-J1 que muere, en su segunda casa |
| dieciséis §3 | tabla del conector | Ninguno | No cambia ni un pin; los 9-12 ganan destino (D9) |
| contrato disuelto | :49-54 y la copia del MISO trece líneas abajo | Patch | Tercera copia del argumento y de la regla |
| tiempo-musical (spec madre de `tiempo_budget.py`) | la derivación «72 bits a ≤10 MHz» | Patch | La constante pasa a por-enlace |
| `j2.rs` | :1-3, :35, :79, :143 | Rewrite | Contrato por-enlace; 72 bits queda como dialecto legado con su test renombrado |
| `pinout.rs` | :40-60 | Rewrite | Muere un-SPI-más-8-CS; nace el reparto de maestros (chip nuevo, con el guion de pines) |
| `hardware/03-vco/README.md` | :97-116 | Patch | El contrato local pasa a «dialecto legado del enlace de la Voz» |
| `docs/modules/03-vco.md` | :156-163 | Patch | ídem |
| bring-up.md | :336-346, :392-426, **y el Paso 8 entero** | Patch | El passthrough vale para el dialecto legado; la doctrina del «reloj adoptado» pasa a alimentar el piso legado por-enlace (D2) |
| `check_bringup.py` | :127, :177-179 | Patch | ídem |
| `micro_budget.py` | la aserción de maestros **y el comentario del oyente en broadcast** (`OYENTE_J2_*`) | Expand/Patch | Gana ≥6 SPI + 4 USART; el broadcast muere con este papel |
| issue #199 | entero | Cerrar con este papel | Su heredero es la palanca de longitud por enlace (§4.2) |
| issue #178 | la cita a «no admite un cliente más» y el micro | Comentar | Ranura rápida; el micro no se elige por barato (D3) |
| issue #205 | el oyente del J2 | Comentar | Sin broadcast no hay oyente que censar; el censo pasa al chip nuevo |
| issue #171 | la bajada del crosspoint | Comentar | La bahía viaja por el enlace de la Voz (E-3) |
| PR #207 (evento) | C6/C8, aritmética de bus | Aviso a su autor | R-E10/R-E11 sobreviven; muere su contabilidad de bus compartido |

## 7. Los guiones

| Guion | Estado | Qué se le pide |
|---|---|---|
| `enlace_budget.py` | reescribir | Modelo **por enlace**. Muere la pelea de MISO. Gana: la aserción de R-P3 (el modelo concentrado no sanciona enlaces punto a punto), la cadena de §4.2 con máximos de hoja, la terminación como parámetro, y la ranura de la Voz por longitud |
| `trama_j2_budget.py` | nace con oficio nuevo | Por enlace: tasa declarada × trama ≤ techo de ocupación del enlace a su reloj **sancionado**. Falla sin reloj declarado o sin fila de sanción en ranura activa (R-P2). Sin suma global (R-P1). Define el techo por-enlace (D6) |
| `latencia_mano_budget.py` | reescribir | El lazo del panel contra el enlace privado de la Voz: el techo de 9,19 kHz se recalcula; `SCLK_J2` deja de ser global |
| `tiempo_budget.py` | patch | `T_TRAMA_J2` por el enlace que la lleve |
| guion de pines del cerebro | nace | H750: 8×4 de enlaces + LTDC + USB ×2 + I²C/mux + MIDI + gates contra el encapsulado — con el LQFP100 ya descartado en papel (D3) |
| `micro_budget.py` | expand | Aserción: el candidato a cerebro da ≥ 6 SPI + 4 USART síncronos con DMA — se asevera lo que el chip trae (Tabla 5), no lo que el diseño cablea (2), porque los 2 USART de sobra son el margen de recableo de D3 |

Los seis entran solos a `gates.py` por patrón; ninguno necesita alta. La
tabla de sanción de D2 es un artefacto nuevo del firmware del cerebro y su
guion la lee, no la duplica.

## 8. Riesgos, cada uno con su criterio de cierre

1. **El mazo por encima de 10 MHz nunca se ha medido — en ninguna clase.**
   *Cierre:* ojo de datos y flanco monótono en el extremo del módulo, con la
   terminación elegida, al reloj propuesto, por cada ranura activa — en el
   bring-up del cerebro nuevo. El resultado puebla la tabla de sanción (D2).
   Hasta entonces, piso legado (R-P4).
2. **Los números eléctricos del H750 son de la rev V.** *Cierre:* releer
   Tabla 193/94 contra el marcado del chip comprado.
3. **La hoja no garantiza N DMAs serie sin contención** (da los 16 canales
   del MDMA y la frase del router; el desglose 8+8 de DMA1/DMA2 es del
   manual de referencia, no de la hoja). *Cierre:* medir el sesgo de fin de
   trama entre enlaces (D7) en bring-up, contra la cota de simultaneidad que
   fije el papel del evento.
4. **El micro del módulo de mandos no está elegido** (#178). Con D3 su
   ranura es rápida y no lo limita. *Cierre:* su placa declara reloj (D2).
5. **Los módulos 8/9 tras las actas E nadie los ha reconfirmado.** *Cierre:*
   decisión de Samuel al llegar; las ranuras no expiran — punto a punto las
   mantiene gratis.
6. **La premisa del chip del cerebro está dirigida, no sellada** (§0.1).
   *Cierre:* el guion de pines del cerebro en verde sobre el LQFP144+, y la
   decisión de Samuel sobre el PR #209.
7. **La autopista (D9) tiene tres incógnitas propias**: la parte
   transceptora sin elegir, el par diferencial en cinta sin masa adyacente,
   y el consumo. *Cierre:* hoja de la parte + su presupuesto ejecutable +
   ojo medido. Hasta entonces es cobre reservado, no un número del que nada
   dependa.

## 9. Fuera de alcance, a propósito

- **El chip de la Voz y la muerte del broadcast interno** (la T, los dos
  oyentes, la recuperación): del papel que reemplace al #201. Este papel
  asume su premisa (§0.1) y le entrega un enlace privado.
- **El formato del evento de nota** (#207): R-E10/R-E11 sobreviven; su
  aritmética de bus se rehace contra el enlace privado cuando este papel
  entre. La cota de simultaneidad inter-módulo (D7) es suya.
- **La expresividad del modelo** (velocidad en `nota_on`): más grande que
  este papel; se abre aparte.
- **El log de telemetría**: su transporte natural es la subida full-duplex
  del enlace de la Voz (D4), pero su diseño — formato, retención, sello —
  es de otro papel y este no lo decide.

## 10. Acta del día

- Samuel, 2026-08-25, en orden: reabrir el contrato del J2; dirección punto
  a punto; *«dale con todo»*; y sobre los peldaños: *«mete los 3 peldaños
  con todo pero nada de chips baratos, quiero puro bólido ferrari en una
  autobahn»* — que es D3, D8 y D9.
- La cuenta que lo dispara: 87 % del contrato con el instrumento a medio
  construir y +2,3 % de margen real; tres módulos más lo tumban.
- El hallazgo del reconocimiento que puso los números honestos: el techo lo
  ponen los extremos y el viaje, no el cable ni el reloj — RP2350/PL022 =
  12,5 Mb/s (hoja §12.3.4.4), H750 full-duplex = 31 MHz (Tabla 193), y en
  el peldaño 1 manda el viaje de ida y vuelta (≈19,7 MHz al peor mazo con
  máximos de hoja).
- Este papel pasó su junta **antes** de abrir PR — cuatro lentes, un
  BLOQUEANTE (el término de sanción sin casa: hoy es D2.3) y tres réplicas
  del patrón del #206 (la cuenta de apertura contra el veredicto del guion,
  la promesa del núcleo citada como propiedad, el típico presentado como
  máximo), todas corregidas aquí y dichas aquí. El 51× de la primera
  conversación murió por R-P3; el 4,6× de la primera versión murió por
  mezclar convenciones de ocupación (§4.2 lleva las dos, rotuladas).
