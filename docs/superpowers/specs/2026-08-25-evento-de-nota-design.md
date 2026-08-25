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
> ni un micro.**

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
nuevo»*— y **lo agravan**. Eso tiene su sitio: el **#205**, que este papel no
resuelve y del que depende. Su tabla, con la cuenta corrida:

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

---

## 5. Los guiones

| Guion | Qué asevera | Estado |
|---|---|---|
| `evento_budget.py` | R-E1 contra el largo de **todos** los mensajes declarados del J2, con D3 en su peor caso; y el sesgo residual entre columnas de §4.5 del enlace sin jefe, **aseverado, no compensado** | no existe |
| `ataque_budget.py` | La cadena completa nota→VCA contra los ≤3 ms de Voz total §3.3, con sus huecos declarados | no existe |
| `tiempo_budget.py` | **Arreglo**: su `BITS_TRAMA_J2 = 72` es la trama de tres AD5686R en cadena de la v1 del módulo 3, muerta desde el cambio 1 de orquestación. Puerta viva vigilando un número muerto | existe, con el número caduco |

### La cadena de `ataque_budget.py`, con sus huecos dichos

| Término | Cuánto | De dónde |
|---|---|---|
| Reacción del cerebro | **HUECO** | #150, `censo_cerebro_budget.py`, en curso |
| Espera del turno | 28,8 µs (54,4 si la ronda fuera indivisible) | §1.1 |
| Aire del evento | derivado del formato de §3 | 10 MHz |
| Parse en el micro | **HUECO** | #205 |
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

---

## 8. Lo que este papel NO decide

- **El contrato del módulo de percusión** — parte 1 del #160: si lleva acento
  aparte de la velocidad, cómo se expresa el *choke* entre charles abierto y
  cerrado, y el ámbito de sus parámetros. Este papel le da el mensaje; no le da
  el contrato.
- **El ancho del campo de fuerza** — §3, condición C4.
- **El reparto de núcleos del micro de la Voz** — Voz total §3.4, que el enlace
  sin jefe reescribe y que nadie ha vuelto a fijar.
- **El programa de PIO del receptor** — #205, condición C1.
- **La cabecera concreta del bloque de deltas de D3** — se deriva en el plan con
  el censo delante.
- **Si el secuenciador (#94) trata a los tambores como caso especial.** R-E3 dice
  que no hace falta; confirmarlo es de aquel papel.

---

## 9. Condiciones de cierre

Ninguna de estas está medida. Se escriben como condiciones para que nadie las
lea como hechos.

1. **C1 — El receptor cabe en PIO.** R-E4 y R-E5 en una máquina de estado, o dos
   si el códec cede sitio. Se cierra escribiendo el programa y contando
   instrucciones. **#205.**
2. **C2 — El planificador del cerebro puede emitir fuera de cadencia** sin
   romper la tasa del lazo ni la ventana de `MISO`. **#150.**
3. **C3 — El peor caso de D3 cumple R-E1** con la cabecera real. Lo asevera
   `evento_budget.py`.
4. **C4 — El ancho de la fuerza** no estrangula MIDI 2.0 ni infla el mensaje.
5. **C5 — El sesgo residual entre columnas** es de microsegundos, como predice
   §4.5 del enlace sin jefe. Se mide en el bring-up con analizador lógico.
6. **C6 — Este papel se escribe sobre el PR #201 sin mergear.** Si el #201
   cambia, §1 y R-E3 se releen.

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

Correcciones hechas durante la sesión, anotadas porque el repo lleva seis del
mismo animal en un día:

- La espera **no** es 1 ms: es 125 µs. El 1 ms sale de la tasa **mínima**
  declarada de R-M4, no del punto de operación.
- El bus **no** está vacío: va al 43,5 % de un techo del 50 %.
- La frase de los gates es del **núcleo §5.3**; el cerebro §5 la cita y lo dice.
- La cadena de LED **no** gasta PIO en el micro de la Voz: dieciséis §14 se la
  quitó, y una de sus tres razones fue justamente proteger ese presupuesto.
