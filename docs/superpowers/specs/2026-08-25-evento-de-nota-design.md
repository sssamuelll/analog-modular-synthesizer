# El evento de nota: sale sin esperar turno, y lleva el tono puesto

> Diseñado con Samuel el 2026-08-25. **Es papel, no cobre ni firmware.**
>
> Cierra el prerrequisito bloqueante de
> [Voz total §3.3](2026-08-23-modulo-voz-total-design.md) —*«el formato del
> mensaje, su sello de tiempo y la entrega al esclavo no están diseñados»*— y el
> riesgo 2 de [orquestación §9](2026-08-22-vco-orquestacion-design.md). El
> riesgo 1 de esa misma sección **ya no existe**: lo disolvió
> [el enlace sin jefe](2026-08-25-enlace-sin-jefe-design.md) —**PR #201, sin
> mergear**, así que este enlace no resuelve hasta que entre— al matar el reenvío
> maestro→esclavo, y este papel se escribe encima de ese estado.

---

> # ⚠️ Enmienda del 2026-08-26: **la premisa que este papel esperaba ya llegó, por otra puerta**
>
> Este papel quedó frenado esperando al PR #201. **Ya no hace falta esperarlo
> para esa premisa.**
>
> Lo que este documento necesitaba de aquel era una sola cosa: **que el reenvío
> maestro→esclavo estuviera muerto.** El #201 lo mataba haciendo que los dos
> micros oyeran el mismo bus. `main` lo mató más fuerte y por otra vía: el
> módulo de Voz pasa a **un solo STM32N657** (motor-digital, acta A-1). **No hay
> reenvío porque no hay a quién reenviar.** La premisa está entregada, y viene
> de un papel que sí está en `main`.
>
> ## Lo que eso disuelve, condición por condición
>
> | | Estado |
> |---|---|
> | **C1** — «el receptor cabe en PIO» | **DISUELTA.** El oyente del J2 es hoy **esclavo SPI de hardware** (motor-digital §7), no un programa de PIO. No hay programa que escribir ni instrucciones que contar. **Y con ella se suelta el #205**, que era su dependencia entera |
> | **C5** — «el sesgo entre columnas se mide» | **DISUELTA.** No hay columnas: hay un micro. Y su otro término —*«un receptor de clase distinta, SPI de hardware contra PIO»*— muere con la misma frase: los dos extremos son ahora de la misma clase |
> | **C2** — el planificador del cerebro | **EN PIE, y con más aire.** Ver abajo |
> | **C3**, **C4** | **En pie, intactas.** No dependían del chip de la Voz |
> | **C6** — el estado del #201 | **En pie**, reducida. Ver abajo |
>
> ## C2 mejora, y conviene saber por qué
>
> C2 se apoyaba en el censo del cerebro: *«7 de 12 máquinas de PIO»*. Ese número
> **sobrecuenta desde hoy**: los cronómetros de afinación se mudaron al N657 de
> la Voz, así que las 4 máquinas que gastaban en el cerebro **quedaron libres**.
> El cerebro va por **3 de 12**, no 7. El miedo que C2 declaraba —*«si
> Pico-PIO-USB pidiera una máquina más, caen a 8 de 12»*— se aleja mucho.
>
> (El censo lo declara como HUECO en `pio_budget.py`; la fila no se quitó
> todavía porque tocarla obliga a tocar `pinout.rs`.)
>
> **Lo que NO mejora, y sigue siendo lo mismo:** *«en qué núcleo vive el host
> USB»* sigue sin decidirse, y este papel sigue escrito condicionado a que viva
> en el núcleo 1. Eso es decisión de Samuel y el cambio de chip no la toca — el
> cerebro es otro zócalo.
>
> ## Lo que este papel SIGUE necesitando, dicho sin maquillaje
>
> 1. **Rehacer su aritmética de bus contra el enlace privado.** No es opcional:
>    lo manda `main` por su nombre. El J2 punto a punto §9 dice de este PR que
>    *«R-E10/R-E11 sobreviven; su aritmética de bus se rehace contra el enlace
>    privado cuando este papel entre»* — **y ese papel ya entró**.
> 2. **`evento_budget.py` no existe.** C3 dice «lo asevera `evento_budget.py`» y
>    ese guion no está escrito. C5 lo citaba también; al disolverse C5, queda
>    C3 sosteniéndolo solo.
> 3. **El #201 sigue sin decidirse** (C6), pero ya **no bloquea la premisa de
>    §1** — solo las deudas que este papel declara heredar de su D1.
>
> **Traducido: este PR deja de estar bloqueado por otro PR y pasa a estar
> bloqueado por trabajo propio identificado.** Es un sitio mucho mejor.
>
> Y cierra la parte 2 del **#160**, que pedía *«diseñar el evento con sello de
> tiempo dentro de la trama SPI una vez, sirviendo a los gates del #158 y a la
> percusión»*. Se diseña una vez. Lo que cambia respecto a lo que el #160
> imaginaba es que **no va dentro de la trama**, y §1 dice por qué.

---

## 0. Qué es este papel, y qué no

Es el **formato del evento** y la **ley de temporización** que lo protege.

No es el contrato del módulo de percusión (parte 1 del #160), no es el reparto
de núcleos del micro de la Voz, y no es el programa de PIO que lo recibe. Los
tres tienen su sitio en §8 y §9.

Nada de lo que hay aquí está medido. Son cuentas, contratos citados y una
decisión de Samuel. Las condiciones están en §9, escritas como condiciones.

---

## 1. El problema, y la cifra que lo ordena

El núcleo §5.3 escribió el camino hace ocho días, y su razón es un requisito
disfrazado de justificación:

> «Lo mismo con los gates: mandarlos **dentro de la trama SPI**, junto al tono,
> no solo escala — **sincroniza mejor**, porque tono y gate salen en el mismo
> instante en vez de por dos caminos distintos.»
> — `2026-08-17-nucleo-digital-design.md:809`, §5.3

*(El spec del cerebro §5 repite esa frase citando a este. El origen es el
núcleo; el cerebro es quien lo hereda.)*

La frase tiene dos mitades y solo una sobrevive. **La simultaneidad de tono y
gate es un requisito y se conserva** (D2). **Que el vehículo sea la trama
periódica es un medio, y sale caro.**

### 1.1 Lo que cuesta el turno

Corrido, no supuesto — `hardware/02-midi-cv/latencia_mano_budget.py`:

| | bits | a 10 MHz |
|---|---|---|
| Sondeo del panel (deltas + cabecera) | 256 | 25,6 µs |
| Bloque de tono agrupado (16 × 16 + cabecera) | 288 | 28,8 µs |
| **Giro del lazo** | **544** | **54,4 µs** |

El lazo corre a **8 kHz** —lo manda la latencia de la mano— y ocupa el
**43,5 %** del J2 contra un `TECHO_OCUPACION` declarado del **50 %**. No puede
subir más: a **9,19 kHz** toca el techo.

De ahí sale la cifra que ordena este papel:

| El evento viaja… | Espera hasta |
|---|---|
| **dentro** de la trama periódica | **125 µs** — un periodo del lazo a 8 kHz |
| dentro, si el lazo cayera a la tasa **mínima** de R-M4 (1 kHz) | 1 ms |
| **fuera** de la trama, tras el mensaje en curso | **28,8 µs** |
| fuera, si la ronda entera fuera indivisible | 54,4 µs |

**Entre 2 y 4 veces mejor**, no treinta y cinco. La cifra de 1 ms es real pero
es el peor caso contra la tasa **mínima declarada** de R-M4, no contra el punto
de operación. Decirla sin esa distinción sería el mismo pecado que H-BP2 cazó
en la v1.

### 1.2 Por qué importan 100 µs

`hardware/02-midi-cv/tiempo_budget.py` ya fijó el objetivo del instrumento, con
fuente en la literatura de percepción: el umbral de asincronía empieza en
**2 ms**, y se diseña a la mitad — **`OBJETIVO_S = 1 ms`**.

Y ese guion ya asevera cuánto de ese objetivo puede llevarse el enlace:

```python
assert T_TRAMA_J2 < 0.1 * OBJETIVO_S
```

**El 10 %. Cien microsegundos.** Esa aserción estaba escrita desde el 17 de
agosto, antes de que nadie hiciera esta pregunta, y es de donde sale la ley de
D4. No se inventa un número: se hereda el que ya estaba vigilado.

### 1.3 Por qué no se arregla acelerando el cable

No se puede. El presupuesto de flanco (#198, `enlace_budget.py`) deja el J2 con
**8,90 MHz de límite contra 8,70 que exige el tráfico: 2,2 % de margen**, y el
umbral de longitud de mazo del caso adoptado es **≈721 mm** (#201), con ~17 mm
de sobra sobre los 738 de hoy.

Y que el AD5686R aguante 25 MHz en cadena *(hoja rev. F, Tablas 4 y 5)* no
cambia nada: dice que **el conversor nunca fue el techo**, no que el bus pueda
correr más. El techo es el flanco.

**La única palanca es acortar mensajes.** De ahí que la ley de D4 sea una cota
de largo y no de reloj.

---

## 2. Las decisiones

### D1. El evento no espera turno *(decisión de Samuel, 2026-08-25)*

El evento de nota **sale en el instante en que existe**, fuera de la cadencia de
la trama periódica. No hay ranura reservada, no hay horario, no hay antelación.

Lo instantáneo manda sobre lo continuo. El flujo periódico —tono, ancho de
pulso, índices de modulación— **cede el paso** y ocupa lo que queda.

Lo que el evento **no** puede hacer es cortar un mensaje ya en vuelo: partirlo
lo entrega roto. Su peor caso es, por tanto, **lo que le quede al mensaje en
curso**, y por eso D4 acota el largo de todos los mensajes en vez de acelerar el
bus.

> Samuel lo pidió así: *«que las notas no viajen en un autobús, que viajen cada
> una en su ferrari»*. El autobús se quita. El convoy que queda (D3) es lo
> contrario de un autobús lento: es lo que hace rápido al flujo continuo.

### D2. El evento lleva el tono de arranque

El mensaje incluye **la nota con la que la voz arranca**. No es un adorno: es lo
que conserva el requisito del núcleo §5.3.

Si el evento sale fuera de la trama y el tono siguiera llegando solo por el
flujo periódico, el borde de apertura puede adelantar al tono nuevo y la voz
arranca en la nota anterior, deslizándose hasta la nueva. Es el *blip* de tono
de los polis analógicos, y §5.3 lo tenía cazado desde el 17 de agosto.

Con el tono dentro, tono y gate no es que salgan en el mismo instante: **son el
mismo mensaje**, indivisible. Cumple el requisito de §5.3 **mejor** que la
propuesta de §5.3, porque además no espera turno.

Y no rompe *«solo lo instantáneo, lo continuo por parámetros»*: el tono **con el
que arranca** una nota es instantáneo. El tono que se mueve después —portamento,
vibrato, deriva, desafinado— es continuo, sigue en el flujo periódico, y sigue
llegando ya sumado por el cerebro como manda R-M2.

> **La frontera, en una línea: el evento lleva el valor inicial; el flujo lleva
> la evolución.**

### D3. El flujo continuo manda solo lo que cambió *(decisión de Samuel, 2026-08-25)*

El bloque de tono deja de mandar los dieciséis valores siempre y manda **solo
los que se movieron**, con su instancia.

No es una idea nueva en esta casa: `BITS_SONDEO_PANEL = 256` ya se describe como
*«bloque de vuelta del panel: deltas + cabecera»*. Se aplica el mismo patrón a
la ida.

**Y hay que decir lo que cuesta, porque no es gratis:**

| | Hoy (todos siempre) | Con deltas |
|---|---|---|
| Un acorde de 4 notas moviéndose | 288 bits | cabecera + 4 × (instancia + valor) |
| **Los dieciséis moviéndose** | **288 bits** | **cabecera + 16 × (instancia + valor)** |

Cada valor pasa a pagar su propia etiqueta, así que **el peor caso empeora
ligeramente** y el caso normal mejora mucho. Como la ley de D4 se asevera contra
el peor caso, el guion tiene que evaluarla contra la versión de deltas, no
contra los 288 de hoy. Está en §5.

Por qué merece la pena aun así: el peor caso de una nota es *«lo que le quede al
mensaje en curso»*, y con deltas **ese mensaje es corto justo cuando estás
tocando poco**, que es donde se vive.

### D4. La ley del largo

> **R-E1. Ningún mensaje del J2 puede durar más de 100 µs — 1000 bits a
> 10 MHz.**
>
> Deriva de `tiempo_budget.py`: `assert T_TRAMA_J2 < 0.1 * OBJETIVO_S`, con
> `OBJETIVO_S = 1 ms`. No es un número nuevo; es el que esa puerta ya vigilaba.

Hoy se cumple con holgura: el giro entero del lazo son 544 bits, el 54 % del
techo. Un mensaje suelto cualquiera está muy por debajo.

**Esta ley obliga a todos los papeles, no solo a éste.** Cualquier diseño futuro
que quiera mandar un bloque grande por el J2 se topa aquí. Es la contrapartida
de D1: si el evento no puede adelantar a lo que va en vuelo, lo que va en vuelo
tiene que ser corto.

> **R-E2. El evento no espera al lazo, y el lazo no espera al evento.** El
> planificador del cerebro puede emitir un evento entre dos tramas de una misma
> ronda. Si no pudiera, el peor caso de R-E1 pasa de *«el mensaje en curso»* a
> *«la ronda en curso»* — de 28,8 a 54,4 µs hoy. Las dos cumplen la ley; la
> intercalación es holgura, no requisito.

### D5. Direccionamiento: el evento no nombra micros

> **R-E3. El destino de un evento es una ruta y una instancia, nunca una columna
> ni un micro.** Acotado **al evento**, que vive en la ranura V y direcciona
> osciladores.

**Ojo con la generalización, que es falsa.** «La instancia jamás nombra una
columna» **no** es propiedad del modelo: la junta del #201 encontró que el censo
publica `estado de columna` con `instancia = columna`, ×2, en la ranura M. R-E3
vale para el evento y no debe citarse como ley general.

Sale de D4 del enlace sin jefe —*«ranuras lógicas funcionales, nunca por
micro»*— y de su reparto de broadcast: los dos micros oyen todo y cada uno actúa
sobre las instancias que le tocan (0–7 la cabecera, 8–15 la columna B). **Desde
fuera nadie sabe que hay dos cerebros**, y el evento no puede ser quien lo
destape.

La forma la da `ParamId` (`software/nucleo/core/src/param.rs`), que ya es una
ruta de tres niveles de 4 bits más instancia de 4. Un evento usa **la ruta y la
instancia, sin índice**: el evento no escribe un parámetro.

Consecuencia gratis: un módulo de percusión es *ruta a su ranura, instancia 0*.
**No es un caso especial** — que es justo lo que el #160 pedía comprobar.

### D6. El borde va en el evento; la verdad va en el flujo

**El problema que D1 crea y que hay que decir en voz alta.** Al morir el
reenvío murió también todo mecanismo capaz de detectar que un evento se perdió
en la columna B: no hay `MISO` desde B (R-S2 del enlace sin jefe), ni acuse, ni
número de secuencia, ni CRC, ni comparación cruzada — y R-S5 prohíbe
inventarlos. Lo cazó la junta adversarial del #201, y la formulación de Halberg
es justa:

> «Se optimizó el jitter de una entrega cuya fiabilidad ya no se puede
> verificar.»

**Y este papel lo empeoraba.** El tono se auto-repara porque es periódico: si
una trama se pierde, la siguiente trae el valor otra vez, 125 µs después. Un
evento sacado de la cadencia (D1) es un **disparo único**, sin repetición y sin
vuelta. Un `note off` perdido en la columna B es **una nota clavada
permanente**, y nadie en el sistema tiene forma de saberlo.

La salida no es inventar un acuse — lo prohíbe R-S5, y además pediría el `MISO`
que la columna B no tiene:

> **R-E10. Todo evento tiene que ser recuperable por el flujo periódico.** El
> evento lleva el **borde**, que es lo que necesita llegar rápido. El flujo
> periódico lleva además el **estado de compuerta de los dieciséis canales**,
> que es la verdad y se reafirma en cada vuelta. Un evento perdido se corrige
> en la siguiente trama, sin acuse, sin retransmisión y sin canal de vuelta.

Cuesta **16 bits por módulo** en un bloque que el cambio 1 ya está reescribiendo
y que D3 ya toca. No es un mensaje nuevo, así que no roza R-S5.

**Pero la cadencia de ese estado NO es la del tono, y esto es media decisión.**
Corrido por el autor del #201 contra sus guiones: 16 bits **a la tasa del lazo**
(8 kHz) son 128 kbit/s, que empujan el reloj exigido de 8,70 a 8,96 MHz y
multiplican por 2,4 el déficit de mazo — de 18 mm a 44.

Y no hacen falta. El estado de compuerta es una **red de reparación**, no un
flujo: su cadencia no la fija la música, la fija **cuánto tiempo se tolera una
nota clavada**. Este instrumento ya tiene cadencias lentas declaradas para
exactamente esta clase de verdad — 50 ms el sondeo de jacks, 1 Hz la salud
(orquestación §7.1).

> **R-E11. La cadencia del estado de compuerta se declara aparte y se deriva de
> la tolerancia a una nota clavada, nunca de la tasa del bloque de tono.**

El orden de magnitud, corrido contra el mismo modelo:

| Cadencia | Caudal | Reloj exigido de más |
|---|---|---|
| 8 kHz — la del tono | 128 000 bit/s | **+0,2560 MHz** |
| 20 Hz — 50 ms, la del sondeo de jacks | 320 bit/s | +0,0006 MHz |
| 100 Hz — 10 ms | 1 600 bit/s | +0,0032 MHz |
| 200 Hz — 5 ms | 3 200 bit/s | **+0,0064 MHz** |

**Y aquí hay una segunda herencia que tampoco hay que aceptar.** Anclar a los
50 ms del sondeo de jacks tiene el mérito de no inventar cadencias, pero **paga
con lo único que dolía**: a 150 BPM, 50 ms es casi una fusa, y un `note on`
reparado con ese retraso entra tarde y **se oye como error**. A 200 Hz —5 ms—
entra tarde y **se oye como la nota**.

Y el coste de esa mejora son 3 200 bit/s: **tres órdenes de magnitud por debajo
de la precisión del modelo**, igual que los 320.

> **Corolario de R-E11: a este precio, el presupuesto ya no elige la cadencia.
> La elige el oído.** No se hereda la del tono ni la de los jacks; se deriva de
> la tolerancia a una nota tardía, que es el caso que manda — el `note off`
> perdido tolera de sobra cualquiera de las tres.

Lo que se paga a cambio, dicho sin adornos: en el caso de fallo la nota tarda
hasta una cadencia de estado en corregirse, no 125 µs. **Para un `note off`
perdido eso es intachable** —50 ms de nota de más no es un fallo, es un
suspiro—. Para un `note on` perdido es una nota que entra tarde y se oye. Las
dos son el caso de fallo de un mensaje perdido, y las dos son incomparablemente
mejores que el permanente.

El número exacto no se fija aquí: se deriva en el plan contra esa tolerancia,
con `evento_budget.py` delante.

Lo que se gana, dicho con precisión: **el camino rápido sigue siendo el evento y
el camino seguro es el flujo.** En el caso normal la nota llega en decenas de
microsegundos. En el caso de fallo llega tarde —hasta una vuelta del lazo— pero
llega, y sobre todo **se cierra**. Una nota clavada permanente deja de ser
posible.

> **La frontera de D2, completada: el evento lleva el valor inicial, el flujo
> lleva la evolución — y también la verdad.**

### D7. Lo que no repite el flujo, no tiene red

> **R-E12. Todo lo que viaje solo en el evento y no lo reafirme un flujo
> periódico queda sin red.** Hoy el evento lleva el borde y R-E10 lo cubre. El
> día que cargue algo más, ese algo **nace sin reparación** y hay que decidirlo
> a propósito, no heredarlo.

Se escribe como invariante y no como hallazgo por una razón concreta: dentro de
seis meses alguien va a añadirle un campo al evento creyendo que la red ya lo
cubre. Es el mismo animal de siempre — una propiedad que era verdad cuando se
escribió.

**Y ya tiene un caso vivo, que es el campo de fuerza de §3.** Si el evento lleva
velocidad y se pierde, R-E10 repara **que la nota esté sonando**, no **con qué
fuerza**. La nota reparada entra a un valor por defecto. Es degradación
elegante y no fallo — pero es degradación, y va escrita en vez de descubierta.

---

## 3. El formato

Cuatro campos y nada más. Los tres primeros son decisión previa de Samuel;
el cuarto lo añade D2.

| Campo | Qué es | Ancho |
|---|---|---|
| **Destino** | Ruta de tres niveles + instancia, como `ParamId` sin índice | 16 bits |
| **Borde** | `abre` / `cierra` / `dispara` | 2 bits, con 1 valor de reserva |
| **Fuerza** | Velocidad o acento | **se fija en el plan** (§9, C4) |
| **Tono de arranque** | Con qué nota abre la voz (D2) | 16 bits, el mismo ancho que un valor del bloque de tono |

`dispara` es el borde de un solo golpe: abre y cierra sin sostenido. Es lo que
un tambor necesita y lo que evita que la percusión invente un camino aparte.

**La fuerza no se fija aquí a propósito.** El núcleo §4.4 adopta MIDI 2.0 como
escalera, y su UMP lleva velocidad de 16 bits mientras MIDI 1.0 lleva 7. Elegir
7 clavaría el instrumento a lo viejo; elegir 16 sin comprobar el resto de la
cadena sería inventar. Se deriva en el plan, con el descriptor delante.

> **Y hay algo más gordo que el ancho: la velocidad NO EXISTE en el modelo.**
> `software/nucleo/core/src/partes.rs:87` es `nota_on(canal, nota)` — sin
> velocidad, y no aparece en ningún sitio del núcleo. Así que este campo **no es
> un ancho por decidir: es una capacidad nueva del instrumento**, y por §2.1 del
> núcleo —*«si no está en el modelo, no existe»*— tiene que aterrizar en el
> modelo antes que en el mensaje. Va como condición C10, no como campo dado.

**Lo que el evento NO lleva**, y es tan parte del formato como lo que lleva:

- **Ni tiempos de envolvente ni corte ni resonancia.** Son continuos y viajan
  como parámetros. Voz total §3.2 ya lo fija: *«los parámetros de un generador
  se capturan al evento»* — o sea que el generador local lee el último valor
  recibido, no uno que venga en el mensaje.
- **Ni sello de hora.** No hace falta: con D1 el evento sale ya, y con D2 no hay
  nada con lo que sincronizarlo. Un sello exigiría base de tiempo compartida en
  los micros y **compraría lo que D1 ya da gratis**.
- **Ni columna, ni micro, ni número de placa** (R-E3).

---

## 4. Lo que esto le exige al receptor

D1 le cambia el trabajo al oyente del J2 de los micros de la Voz, y hay que
decirlo porque no es gratis.

> **R-E4. El receptor está armado permanentemente.** El `CS` de la ranura puede
> caer **en cualquier instante**, entre dos tramas periódicas. Un receptor
> sincronizado a la cadencia se pierde el evento.

> **R-E5. El receptor acepta largo variable.** Un evento y un bloque de tono no
> miden lo mismo, y con D3 dos bloques de tono tampoco. La cabecera dice qué
> viene y cuánto.

Las dos caen sobre el riesgo 5 del enlace sin jefe —*«el oyente de PIO, firmware
nuevo»*— y **lo agravan**.

> ### Enmienda del 2026-08-26: **esta pelea se acabó, y este papel suelta al #205**
>
> Lo de abajo era una pelea por las máquinas de PIO de un RP2350B. **En el
> módulo de Voz no hay RP2350B**: hay un N657 (motor-digital, acta A-1). Los
> tres consumidores de la tabla dejaron de competir, cada uno por su lado:
>
> | Consumidor | Qué le pasó |
> |---|---|
> | **Cronómetros de afinación** (8 máquinas) | pasan a **capturas de TIM en hardware** — 14 en TIM2-5 de 32 bits + 2 en TIM1 de 16 con desbordes contados. Y son **16**, no 8, porque ya no hay que partir el módulo en dos |
> | **Oyente del J2** (1-2 máquinas) | pasa a **esclavo SPI de hardware**, full duplex, D8 real 34,5 MHz |
> | **I²S del códec** (1-2 máquinas) | pasa a **SAI** — el N657 trae dos, y el censo de pines ya le tiene los suyos sentados en verde |
>
> Los dos candidatos que el **#205** decía que nadie había contado **están
> contados** en `micro_budget.py` SITIO 1: 16 cronómetros + oyente (1-2) +
> códec (1-2) = **18 a 20 canales**, contra los 12 que daba el RP2350B. Esa
> cuenta es exactamente la que este papel dejaba pendiente.
>
> **Así que este documento deja de depender del #205**, y su condición C1
> queda disuelta (§9).
>
> **Lo que NO se disuelve, porque no era un problema de PIO:** R-E4 (el
> receptor no está sincronizado a la cadencia) y R-E5 (acepta largo variable)
> **siguen siendo requisitos del receptor**. Un esclavo SPI de hardware los
> cumple sin pelear máquinas, pero el trabajo de firmware sigue ahí, y su
> término nuevo tiene nombre en `main`: **el gap mínimo entre tramas pasa a
> cláusula del contrato del enlace** (motor-digital §7, hallazgo de su junta).
> Cambió la unidad en que se mide, no la exigencia.

<details>
<summary><b>La cuenta original</b> (histórica — sobre el RP2350B que ya no está en esa placa)</summary>

Eso tiene su sitio: el **#205**, que este papel no resuelve y del que depende.
Su tabla, con la cuenta corrida:

| Consumidor del PIO del micro de la Voz | Máquinas |
|---|---|
| Cronómetros de afinación | 8 |
| Oyente del J2 en broadcast | 1 |
| Cadena de LED — dieciséis §14: *«el módulo nunca escribe en la cadena»* | 0 |
| **Usadas de 12** | **9 — quedan 3** |

Y dos candidatos sin contar peleándose esos 3: el I²S del códec de los oídos
(acta E-5, que no dice a qué micro ni cómo, y el RP2350 no trae I²S) y el
receptor de R-E4/R-E5, que puede pedir dos máquinas en vez de una.

**Si pide dos y el códec pide dos, la cabecera cierra en 12 de 12.** Eso no se
despeja con aritmética: se despeja escribiendo el programa de PIO y contando
instrucciones. Condición C1 de §9.

</details>

---

## 5. Los guiones

| Guion | Qué asevera | Estado |
|---|---|---|
| `evento_budget.py` | R-E1 contra el largo de **todos** los mensajes declarados del J2, con D3 en su peor caso **y con los 16 bits de estado de compuerta de R-E10 dentro**; y el sesgo entre columnas **medido**, nunca supuesto (C5) | no existe |
| `ataque_budget.py` | La cadena completa nota→VCA contra los ≤3 ms de Voz total §3.3, con sus huecos declarados | no existe |
| `tiempo_budget.py` | **Arreglo**: su `BITS_TRAMA_J2 = 72` es la trama de tres AD5686R en cadena de la v1 del módulo 3, muerta desde el cambio 1 de orquestación. Puerta viva vigilando un número muerto | existe, con el número caduco |

### La cadena de `ataque_budget.py`, con sus huecos dichos

| Término | Cuánto | De dónde |
|---|---|---|
| Reacción del cerebro | **HUECO**, y no por falta de guion | Ver C2: depende de en qué núcleo viva el host USB, que nadie ha decidido |
| Espera del turno | 28,8 µs (54,4 si la ronda fuera indivisible) | §1.1 |
| Aire del evento | derivado del formato de §3 | 10 MHz |
| Parse en el micro | **HUECO** | ~~#205~~ → bring-up del N657 *(enmienda 2026-08-26: dejó de ser «cuántas instrucciones de PIO» y pasa a ser tiempo de ISR del esclavo SPI, medido bajo carga plena — motor-digital §7)* |
| Escritura y asentamiento del DAC | **HUECO** | hoja del AD5686R + bring-up |
| Render de la envolvente | 100 µs | Voz total §3.1: 10 kHz por canal |

**Se declara hueco lo que no se puede derivar**, con su motivo, según R-F1/R-J6.
Un presupuesto que rellenara esos tres con supuestos daría un total y no diría
nada.

---

## 6. Las prohibiciones

> **R-E6. El evento no viaja por el bus privado entre columnas.** Sale del
> cerebro por el J2 y llega a las dos columnas por el mismo flanco. Si viajara
> por dentro, la asimetría que el enlace sin jefe acaba de matar volvería por la
> puerta de atrás. Es R-S4 aplicada al evento.

> **R-E7. El módulo no genera eventos.** Sigue valiendo R-J3: *«el módulo nunca
> habla sin que le pregunten»*. Un panel que se toca produce **medidas** que
> suben por `MISO`; el evento que resulte lo emite el cerebro.

> **R-E8. El evento no lleva tono continuo.** R-M1 sigue prohibiendo que el
> módulo interpole y R-M2 que genere tono. D2 mete el valor **inicial**, y eso
> es todo: un evento que trajera una rampa sería un interpolador escondido.

> **R-E9. Ningún mensaje nuevo del J2 se declara sin pasar por R-E1.** Añadir un
> mensaje es añadirlo al guion de §5.

---

## 7. Qué muere, qué sobrevive, qué nace

| | |
|---|---|
| **Muere** | La ranura de gate dentro de la trama periódica que el núcleo §5.3 proponía. Sobrevive su requisito, mejor cumplido (D2) |
| **Muere** | La idea de un sello de hora en el evento. D1 la deja sin trabajo |
| **Sobrevive** | El bloque de tono agrupado, y su razón: `latencia_mano_budget.py` asevera que la versión suelta **rebasa** el techo del 50 % — 1408 bits por vuelta contra 544, el 112,6 % del bus |
| **Nace** | R-E1, que acota el largo de todo lo que cruce el J2 |
| **Nace** | El evento como mensaje de primera clase, con la percusión dentro sin caso especial (#160) |
| **Nace** | R-E10: el flujo periódico pasa a llevar el estado de compuerta. Es lo que hace que sacar el evento de la cadencia no cueste fiabilidad |

---

## 8. Lo que este papel NO decide

- **El contrato del módulo de percusión** — parte 1 del #160: si lleva acento
  aparte de la velocidad, cómo se expresa el *choke* entre charles abierto y
  cerrado, y el ámbito de sus parámetros. Este papel le da el mensaje; no le da
  el contrato.
- **El ancho del campo de fuerza** — §3, condición C4.
- **El reparto de núcleos del micro de la Voz** — Voz total §3.4, que el enlace
  sin jefe reescribe y que nadie ha vuelto a fijar.
- ~~**El programa de PIO del receptor** — #205, condición C1.~~ **Ya no existe**
  (enmienda 2026-08-26): el receptor es esclavo SPI de hardware. Lo que ocupa su
  sitio en esta lista es **el gap mínimo entre tramas**, que este papel tampoco
  decide — es cláusula del contrato del enlace (motor-digital §7).
- **La cabecera concreta del bloque de deltas de D3** — se deriva en el plan con
  el censo delante.
- **Si el secuenciador (#94) trata a los tambores como caso especial.** R-E3 dice
  que no hace falta; confirmarlo es de aquel papel.
- **En qué núcleo del cerebro vive el host USB.** Es la condición C2 y es de
  Samuel. Este papel la nombra y se declara dependiente de ella; no la cierra.

---

## 9. Condiciones de cierre

Ninguna de estas está medida. Se escriben como condiciones para que nadie las
lea como hechos.

1. ~~**C1 — El receptor cabe en PIO.**~~ **DISUELTA el 2026-08-26.** El oyente
   del J2 es esclavo SPI de hardware (motor-digital §7), no un programa de PIO:
   no hay programa que escribir ni instrucciones que contar, y **el #205 queda
   suelto**. Lo que no se disuelve es el requisito: R-E4/R-E5 siguen pidiendo un
   receptor asíncrono de largo variable, y su término nuevo es **el gap mínimo
   entre tramas**, cláusula del contrato del enlace. Se cierra fijando ese gap,
   no contando máquinas.

   <details><summary>texto original</summary>

   **C1 — El receptor cabe en PIO.** R-E4 y R-E5 en una máquina de estado, o dos
   si el códec cede sitio. Se cierra escribiendo el programa y contando
   instrucciones. **#205.**

   </details>
2. **C2 — El planificador del cerebro puede emitir fuera de cadencia** sin
   romper la tasa del lazo ni la ventana de `MISO`.

   El censo del cerebro (#150, PR #208) ya despejó la mitad fácil: **7 de 12
   máquinas de PIO y 7 de 16 canales de DMA**, y los cronómetros de afinación
   cuentan por hardware —*«with little or no CPU overhead»*, datasheet del
   RP2350— así que no hay carga por flanco compitiendo con la decisión de
   emitir. *(Cifras con instrucciones **ESTIMADO** hasta que alguien pase
   `pioasm`: el cerebro respira, no le sobra sitio. Si Pico-PIO-USB pidiera una
   máquina más, caen a 8 de 12.)*

   > **Enmienda del 2026-08-26 — esta condición respira mucho mejor.** Ese
   > «7 de 12» **sobrecuenta**: los cronómetros de afinación se mudaron al N657
   > de la Voz, así que **las 4 máquinas que gastaban en el cerebro quedaron
   > libres**. Va por **3 de 12**, y el miedo declarado arriba —«si Pico-PIO-USB
   > pidiera una máquina más, caen a 8 de 12»— se aleja mucho. El propio
   > `pio_budget.py` lo declara como HUECO: la fila no se quitó porque tocarla
   > obliga a tocar `pinout.rs`, así que el censo **sobrecuenta a propósito**,
   > que es el lado conservador.
   >
   > Y va más allá del conteo: con el afinado fuera del cerebro, **ya no hay ni
   > siquiera cronómetros contando flancos ahí**. El argumento de esta condición
   > deja de necesitar la cita del datasheet — no hay carga porque no hay
   > cronómetros.
   >
   > **Lo que no cambia:** en qué núcleo vive el host USB sigue sin decidirse, y
   > este papel sigue condicionado a que viva en el núcleo 1. El cerebro es otro
   > zócalo y el cambio de chip de la Voz no lo toca.

   **Lo que queda abierto no es un cálculo, es una decisión**: en qué núcleo
   vive el host USB. Hoy el núcleo 0 es tiempo real y el 1 atribución, y el host
   no tiene sitio declarado en ninguno.

   > **Este papel se escribe condicionado a que el host USB viva en el
   > núcleo 1.** Con esa condición, la reacción del cerebro queda acotada por el
   > núcleo 0 y es pequeña. **Si se decidiera al revés, esta condición cae y el
   > término empeora**: un host USB bit-bangeado tiene ráfagas duras, y
   > compartirían núcleo con lo que decide emitir el evento.

   Decisión de Samuel, no de este papel ni del #150.
3. **C3 — El peor caso de D3 cumple R-E1** con la cabecera real. Lo asevera
   `evento_budget.py`.
4. **C4 — El ancho de la fuerza** no estrangula MIDI 2.0 ni infla el mensaje.
5. ~~**C5 — El sesgo entre columnas se MIDE.**~~ **DISUELTA el 2026-08-26: no
   hay columnas.** El módulo de Voz es un solo N657, así que no existe el sesgo
   entre dos micros que esta condición mandaba medir. Y su otro término muere
   con la misma frase: hablaba de *«un receptor de clase distinta, SPI de
   hardware contra PIO»* — hoy los dos extremos son de la misma clase.

   **Lo que sí sobrevive, y merece rescatarse porque era la parte buena:** la
   junta del #201 tenía razón en que *«la asimetría es estructural, no
   residual»*, y esa lección se hereda aunque su caso muera. Donde antes se
   comparaban dos micros, hoy se compara **una CPU contra sus propios plazos**,
   y el sitio donde eso se asevera es el libro bilateral de `carga_motor` más
   el presupuesto de latencia de interrupción que motor-digital §7 manda medir
   en bring-up **bajo carga plena**. La regla no cambia: se mide, no se
   argumenta.

   <details><summary>texto original</summary>

   **C5 — El sesgo entre columnas se MIDE, y el argumento que lo daba por
   pequeño no vale.** §4.5 del enlace sin jefe lo justificaba como *«diferencia
   de cómputo local entre dos copias del mismo binario»*. La junta del #201
   demostró que es falso: el núcleo 0 de la cabecera lleva **además** la ventana
   de `MISO` con su regla de no perderla, la consolidación de medidas y el
   sondeo del bus interno — y un receptor de **clase distinta** (SPI de hardware
   contra PIO). **La asimetría es estructural, no residual.** El número puede
   seguir siendo bueno; el argumento no. `evento_budget.py` lo asevera contra
   medida, nunca contra esa frase.

   </details>
6. **C6 — Este papel se escribe sobre el PR #201, que no está mergeado y que
   NO pasó su junta adversarial de cinco agentes** (2026-08-25). Estado
   comprobado con su autor, decisión por decisión:

   | | |
   |---|---|
   | **D1** (los dos micros oyen, muere el reenvío) | **En pie.** Nadie propuso revertirla; es la parte menos frágil del papel. §1 de este documento se sostiene |
   | **D4** (ranuras funcionales) | **Entra con otro argumento de cierre**: el suyo citaba «tres septetos de SysEx» y el núcleo §3.1 dice cinco. R-E3 sobrevive; su justificación no |
   | **D3** (recuperación) | **Enmendada.** Tres de los cuatro agujeros están ahí. No toca a este papel |

   **Deudas de D1 que este papel hereda y no resuelve**: el caso eléctrico
   adoptado **no cierra hoy** —8,54 MHz disponibles contra 8,70 exigidos— y el
   framing variable que R-E5 necesita está declarado **congelado** en núcleo
   §597. Las dos aprietan R-E1, no la aflojan.

7. **C7 — La pérdida de un evento no se detecta, y no se va a detectar.** R-E10
   la hace recuperable, que es otra cosa. Si alguna vez alguien necesita
   *saber* que se perdió, eso pide canal de vuelta desde la columna B y levanta
   R-S2 y R-S5: es rediseño del enlace, no un añadido a este papel.

8. **C8 — El piso contra el que se mide R-E11 es optimista, y hay que decirlo.**
   Los 8,70 MHz exigidos cuentan **un** sondeo de panel y **un** bloque de tono.
   No cuentan los demás módulos, ni la telemetría de 1 Hz, ni el sondeo de
   jacks. Cada módulo que declare su tasa mínima suma ~0,58 MHz, y **tres
   módulos más se pasan del contrato de 10 MHz antes de que este campo exista**.
   El árbitro que sumaría todo eso, `trama_j2_budget.py`, **no existe**.

   > **R-E11 nace con su línea reservada en ese guion.** No se descubre sumando.

9. **C9 — Si R-E11 acabara costando margen de mazo, se paga de un sitio con
   nombre.** `HOLGURA_SERVICIO = 0,150 m` es holgura **declarada, no derivada**,
   y su propio comentario dice dónde recortar. Recortarla es legítimo;
   **consumirla en silencio no**. Si hace falta, entra como decisión escrita con
   su cifra, no como un número que cambió.

10. **C10 — La velocidad no está en el modelo.** `partes.rs:87` es
    `nota_on(canal, nota)`, sin velocidad, y no aparece en ningún sitio del
    núcleo. El campo de fuerza de §3 es una **capacidad nueva**, no un ancho por
    elegir, y por núcleo §2.1 —*«si no está en el modelo, no existe»*— aterriza
    primero en el modelo. Y por R-E12 nace **sin red**: una nota reparada suena,
    pero a un valor por defecto.

---

## 10. El mapa de enmiendas

Mandadas, no hechas.

| Papel | Qué |
|---|---|
| Voz total §3.3 | Sustituir por referencia a este papel; el prerrequisito queda cerrado |
| Voz total §3.2 | Añadir que el tono de arranque viaja en el evento, y que eso no viola el test de generador |
| Orquestación §9, riesgo 2 | Cerrado: los gates viajan en el evento, no en la trama |
| Orquestación §10 | La fila de `evento_budget.py` pasa a aseverar R-E1 |
| Núcleo §5.3 | Anotar que su camino de salida se cumplió por otra vía, y por qué |
| Núcleo §4.1 | El evento **no** entra en la tabla de mensajes: aquella es la superficie cliente↔cerebro; ésta es cerebro↔módulo. Decirlo, para que la ausencia no se lea como olvido |
| `tiempo_budget.py` | El arreglo de §5 |
| El bloque periódico del cerebro | Gana los 16 bits de estado de compuerta de R-E10. No es mensaje nuevo: es campo en un bloque que el cambio 1 ya reescribe |
| #160 | Su parte 2 queda cerrada aquí; la 1, 3 y 4 siguen abiertas |

---

## 11. Acta de la sesión (2026-08-25)

Decisiones de Samuel, en orden:

1. **Destino direccionable, campo de borde abre/cierra/dispara, y solo lo
   instantáneo** — lo continuo por parámetros. *(Previas a esta sesión, citadas
   por el enlace sin jefe §11.)*
2. **El evento no espera turno.** *«Que las notas no viajen en un autobús, que
   viajen cada una en su ferrari.»*
3. **Todo lo demás tampoco, si cabe.** Se comprobó que no cabe: 1408 bits por
   vuelta contra 544, el 112,6 % del bus, y `latencia_mano_budget.py` ya tenía
   una aserción escrita para esa pregunta desde antes de que se hiciera.
4. **El flujo continuo manda solo lo que cambió** (D3), que es lo que sí se
   puede dar de la idea 3.

Y una decisión que salió de la junta adversarial del #201, no de la sesión:

5. **El borde va en el evento; la verdad va en el flujo** (D6/R-E10). La junta
   encontró que matar el reenvío mató también toda forma de saber que un evento
   se perdió, y que este papel lo empeoraba al sacar el evento de la cadencia:
   el tono se auto-repara por periódico, un disparo único no. Se resuelve sin
   acuse y sin canal de vuelta — 16 bits de estado en el bloque que ya se estaba
   reescribiendo.

Correcciones hechas durante la sesión, anotadas porque el repo lleva seis del
mismo animal en un día:

- La espera **no** es 1 ms: es 125 µs. El 1 ms sale de la tasa **mínima**
  declarada de R-M4, no del punto de operación.
- El bus **no** está vacío: va al 43,5 % de un techo del 50 %.
- La frase de los gates es del **núcleo §5.3**; el cerebro §5 la cita y lo dice.
- La cadena de LED **no** gasta PIO en el micro de la Voz: dieciséis §14 se la
  quitó, y una de sus tres razones fue justamente proteger ese presupuesto.
- El sesgo entre columnas **no** es «diferencia entre dos copias del mismo
  binario»: la cabecera lleva más trabajo y un receptor de clase distinta. La
  asimetría es estructural (C5).
- «La instancia jamás nombra una columna» **no** es propiedad del modelo: en la
  ranura M sí la nombra. R-E3 queda acotada al evento.
