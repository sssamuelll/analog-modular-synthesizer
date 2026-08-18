# El instrumento en tiempo musical — reloj, cuantización y rampas

**Fecha:** 2026-08-17
**Estado:** implementada — `software/nucleo/core` (verde), el bring-up en `fw/EN-PLACA.md`
**Consume:** `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md` (el núcleo digital, aprobado e implementado en `software/nucleo/`)

---

## 0. Qué es esto, y sobre todo qué no es

Esta spec hace **una sola cosa**: que el instrumento sepa dónde está en el
compás, y que las cosas puedan pedirle que ocurran ahí.

Es la primera de cuatro. El brainstorming pedía «el secuenciador entero», y
eso no es una spec — son cuatro, y esta es la que las demás necesitan:

| | Spec | Qué entrega | Depende de |
|---|---|---|---|
| **1** | **Ésta** | El reloj, la cuantización, las rampas y el anulado | — |
| 2 | Patrones y el motor de secuencia | El tipo patrón en el modelo, la modulación, y el motor que los toca | 1 |
| 3 | Escenas, arpegiador y memoria de acordes | La capa de interpretación, y las *Follow Actions* | 2 |
| 4 | El patch bay bilingüe | El módulo de matriz y el `TN` de los jacks | **solo 1** |

**La 4 no necesita el secuenciador**, solo la cuantización de ésta — la matriz
tiene que conmutar donde no se oiga el clic. Así que en cuanto la 1 cierre, la
4 puede ir en paralelo con la 2 y la 3.

Lo que **no** cubre esta spec, y tiene spec propia después:

| Fuera de alcance | Dónde va |
|---|---|
| Patrones como valor de parámetro, p-locks | Spec 2 |
| **La modulación** (valor relativo sumado al absoluto) | Spec 2 — ver §11 |
| LFOs, clip envelopes | Spec 2 |
| Escenas, modo canción, *Follow Actions*, arpegiador, memoria de acordes | Spec 3 |
| El módulo de matriz de conmutación | Spec 4 |
| **El modo de toma de control** (Captura / Salto / Escala) | Donde se implementen las perillas — §2.2 explica por qué es un problema distinto |
| La UI de todo esto | La spec de la app |

---

## 1. El problema, y por qué el arreglo no es hacer el agente más rápido

El agente tarda **segundos**. `architecture-compute.md` §5 ya lo marcaba como la
trampa técnica del plugin, y en un instrumento de audio segundos es una
eternidad.

**Pero en música la latencia no se mide en segundos: se mide en compases.**

Un cambio que cae exactamente en el 1 del compás siguiente tiene latencia
percibida **cero** — tiene *anticipación*. A 120 BPM un compás son 2 segundos,
así que el agente ya tiene 2 segundos gratis; y si necesita 8, cae 4 compases
después y **sigue siendo musical**. Así funciona una banda: nadie cambia al
coro a mitad de frase.

> **El agente no necesita ser rápido. Necesita llegar temprano.**

Un agente tonto que cae en el 1 se siente musical. Uno brillante que cae cuando
le da la gana se siente roto. Esta spec es la que hace posible lo primero.

Y encaja sin tocar §7.1 del núcleo: los tres lazos a tres velocidades siguen
igual. Lo único que se añade es que el lazo lento **sabe dónde está en el
compás**.

---

## 2. La decisión de fondo: se adopta el vocabulario de Ableton

Todo lo que hay aquí —cuándo aterriza un cambio, qué pasa si tocas algo
automatizado, cómo se desplaza un valor sin reemplazarlo— **lleva treinta años
resuelto y tiene nombres**. Esta spec no inventa ninguno.

### 2.1 Por qué adoptar y no inventar

Tres razones, y la tercera es de este proyecto:

1. Son décadas de refinamiento sobre el mismo problema.
2. Todo músico ya los conoce. Nadie tiene que aprender nuestro dialecto.
3. **El agente también los conoce.** Un LLM leyó todos los manuales de DAW que
   existen. Un parámetro llamado `cuantización global` con los valores de
   Ableton no necesita explicación ninguna — mientras que un nombre propio no
   lo entiende nadie, ni tú ni el modelo.

La tercera es §2.1 del núcleo —*«el descriptor es la documentación del
agente»*— cobrándose de golpe. **Las etiquetas de los enumerados de esta spec
son las de Ableton, literales, y eso es una decisión de diseño, no una
comodidad.**

### 2.2 Y son dos problemas ortogonales, no uno

| Problema | Qué es | Cómo se llama |
|---|---|---|
| **Toma de control** | La perilla física está en una posición y el valor en otra. ¿Qué pasa al tocarla? | **Captura / Salto / Escala** |
| **Automatización** | Quién es dueño del valor en el tiempo, lo escrito o tú | **Anulado / Reactivar** |

Se componen: puedes estar en *Escala* + *anulado*.

**El primero ya estaba planeado en este proyecto**: `architecture-poly.md` §7
dice que la cadena WS2812 existe para el *soft-takeover de las perillas*. Esta
spec **no lo cambia**; solo lo nombra con el vocabulario de Ableton y añade el
segundo.

---

## 3. El reloj

### 3.1 Las cuatro fuentes, y su precedencia

| | Fuente | Da tempo | Da fase | Notas |
|---|---|---|---|---|
| 1 | **Link** (por el puente inalámbrico) | sí | **sí** | Sin maestro. Necesita red |
| 2 | **MIDI clock** (USB o DIN) | sí | por SPP | El SPP llega al localizar, no continuo |
| 3 | **CLOCK IN** analógico | derivado | **no** | Solo pulsos. Ver §3.3 |
| 4 | **Interno** | sí | sí | Si no lo sacas, nadie lo sigue |

`fuente de sincronía` es un parámetro: **`automática`** (ese orden de
precedencia) o clavada a una fuente concreta.

**El cambio de fuente aterriza en un borde de compás, nunca a mitad.** Cambiar
en medio da un tirón audible, y este instrumento tiene la información para
evitarlo — salvo cuando **no la tiene**: si `tiene fase` es falso (§3.4), el
cambio aterriza en el borde de pulso, que es el más fino que conoce de verdad.

### 3.2 Ableton Link, y por qué sube de valor el puente inalámbrico

Link sincroniza **tempo, pulso y fase** entre dispositivos de la misma red. Esa
tercera palabra es la que importa: **la fase es exactamente lo que el reloj de
Eurorack no puede dar**.

Su concepto de *quantum* —los pulsos por ciclo musical, típicamente el compás—
garantiza que los participantes con el mismo quantum queden alineados en fase.
Así que **el parámetro `compás` de esta spec *es* el quantum de Link**. Mismo
concepto, ningún tipo nuevo.

Y hay precedente exacto de la topología: existe una implementación corriendo
**Link sobre un ESP32 que le pasa la sesión a un RP2350 por SPI**. Eso es
literalmente el zócalo del puente inalámbrico que §10 del núcleo ya pedía. El
puente deja de ser «lo que sirve la UI web al teléfono» y pasa a ser también
**la fuente de fase del instrumento**.

> **Licencia.** Link es GPLv2+ o propietaria; para incorporarlo a software
> propietario hay que hablar con Ableton. Para un instrumento personal la GPL
> sirve. **Esto no es asesoría legal**, y es la misma clase de nota que la
> patente de Lafayette en §6.3 del núcleo: se anota para que la decisión sea
> consciente.

**Link no es requisito de esta spec.** El modelo de reloj tiene que
*acomodarlo* —una fuente que trae fase por red— para que añadirlo después no
sea un rediseño. Es la misma escalera de §4.4 del núcleo con MIDI 2.0: se deja
el escalón puesto, se sube cuando compre algo.

### 3.3 La verdad incómoda del CLOCK IN

Dos cosas que Eurorack no estandarizó, y las dos muerden:

**Los pulsos por negra no son 24 siempre.** Unos módulos dan 24, otros 1, 2, 4
o 48. No hay manera de adivinarlo: va como parámetro.

**No existe el compás.** El `RESET` es lo único que dice dónde está el 1.

Y la consecuencia hay que decirla entera: **sin RESET, el instrumento no sabe
dónde cae el uno.** Solo sabe pulsar. Si la cuantización está en «1 compás» y
el instrumento no sabe dónde empieza el compás, *«aterriza en el 1»* es mentira.

Sigue en pie lo que ya decidió §5.3 del núcleo: **el comportamiento del RESET
va como parámetro**, porque unos módulos miran el estado del reloj al recibirlo
y otros esperan el siguiente flanco.

### 3.4 `tiene fase`: nunca adivinar en silencio, aplicado al tiempo

De §3.3 sale un parámetro de medida (§3.4 del núcleo: solo lectura):

> **`tiene fase`** — si el instrumento sabe de verdad dónde está el downbeat.

El agente lo lee y sabe si «próximo compás» significa algo, o si le toca
cuantizar al pulso y pedirte un RESET.

**Y cuando no hay fase, el instrumento no inventa un compás: aterriza en el
pulso**, que es lo que sí conoce. No se niega a tocar —la música tiene que
seguir— pero tampoco miente. Es §7.6 del núcleo —*«toda inferencia devuelve una
hipótesis con su confianza, nunca una certeza fabricada»*— aplicado al tiempo,
y es la misma disciplina, no una regla nueva.

### 3.5 Pérdida de reloj

Si el reloj externo se cae, el instrumento **rueda libre al último tempo** y lo
reporta con el parámetro de medida **`rodando libre`**. Un cable flojo no puede
matarte un set.

Pero tampoco puede mentirte: mientras rueda libre lo dice, para que el agente
no siga prometiendo que va sincronizado con nada.

### 3.6 El MIDI clock tiembla, y hay que filtrarlo

El tempo del MIDI clock se deriva del espaciado entre ticks. Sin filtrar, la
lectura baila con el jitter del transporte USB o del DIN.

Necesita un lazo de enganche. **Es trabajo real y hay que presupuestarlo**, no
una nota al pie: §9 lo verifica con jitter inyectado.

---

## 4. La cuantización global

Una sola rejilla, con los valores de Ableton:

> **ninguna · 8 compases · 4 · 2 · 1 · ½ · ¼ · ⅛ · 1⁄16**

El agente **no calcula compases**: dispara, y el instrumento lo aterriza en el
siguiente borde. Como piensa un performer, y como funciona el lanzamiento de
clips en Live.

Y la rejilla es un parámetro más, así que *«cuantízame a 4 compases»* es una
escritura como cualquier otra, alcanzable por el agente por §2.1 del núcleo.

**La consecuencia grande:** si lo único agendado es «al próximo borde», la
ventana en la que hay algo pendiente es **como mucho un compás**. No hace falta
una cola de escrituras agendadas a 4 compases vista, ni resolver las colisiones
que esa cola traería. *«Dentro de 4 compases»* es problema del agente: espera 3
y dispara. **Instrumento tonto, agente listo.**

> **Adaptación declarada.** En Ableton la cuantización global es de
> *lanzamiento de clips*. Aquí se estira a «cuándo aterriza un cambio de
> parámetro». Es una extensión, y se dice para no fingir que es idéntico.

---

## 5. Rampas

### 5.1 `SET` es inmediato; `RAMPA` aterriza

La distinción es la de Ableton: **la cuantización es para lanzar cosas, no para
mover perillas.** Un barrido de perilla cuantizado se sentiría espantoso.

| | Cuándo surte efecto | Quién lo usa |
|---|---|---|
| **`SET`** | **Inmediato, siempre** | Perillas, la cabeza local, el VST. Sin un byte de coste |
| **`RAMPA`** | En el borde de la rejilla | El agente, el secuenciador |

`SET` **no gana ningún campo**. Eso mantiene barato el caso de volumen —un
barrido de perilla son cientos de escrituras por segundo— y mantiene el
invariante de que no hay clientes privilegiados: la cabeza local y el VST hacen
exactamente lo mismo.

### 5.2 La curva la decide el descriptor, y nadie la configura

Una rampa de corte lineal en hercios suena a máquina. **El oído oye octavas.**

El descriptor ya lleva la unidad (§3.3 del núcleo), así que la interpolación
sale de ahí sola:

| Unidad | Interpolación |
|---|---|
| `Hz` | **logarítmica** |
| `MilidB` | lineal (el dB ya es logarítmico) |
| `Cents`, `Semitonos` | lineal (ya son logarítmicos) |
| `Milésimas`, `Milivoltios`, `Milisegundos` | lineal |
| `Ninguna` | lineal |

**Nadie decide esto por parámetro.** Sale de un campo que se puso en el
descriptor por otra razón —para que el agente entienda qué hace el parámetro—
y es el segundo pago del mismo campo.

El campo `curva` del mensaje va **encima** de eso: `0` lineal, negativo cede al
final, positivo arranca lento. Es arrastrar el punto medio de un segmento en
Ableton.

### 5.3 El borde: disparar «justo en el 1» cae en ese 1

Si una `RAMPA` llega exactamente en el borde, esperar un compás entero se
sentiría como fallar. Y «exactamente» nunca ocurre: siempre hay un desfase.

> **Una petición que llega dentro de la ventana de error del sistema alrededor
> de un borde aterriza en ESE borde, no en el siguiente.**

Y la ventana no es un número inventado: **es el error de aterrizaje que despeja
`tiempo_budget.py`** (§9). Si el instrumento no puede colocar nada con más
precisión que X, entonces cualquier cosa que llegue a menos de X de un borde
está, a efectos de todo lo que se puede oír, *en* ese borde.

### 5.4 Duración cero es un salto cuantizado

Una `RAMPA` con duración `0` no es un `SET`: es un **salto que aterriza en la
rejilla**. Un solo mensaje cubre las dos cosas que parecían necesitar dos.

---

## 6. Anulado y reactivar

### 6.1 Un estado y una acción, no cinco modos

Pro Tools y Logic resuelven esto con cinco modos por parámetro —Lectura, Toque,
Enganche, Escritura, Recorte—. Ableton lo resuelve con **un estado y un botón**,
y para este instrumento eso es mejor por una razón concreta:

> **§5.2 del núcleo dice que la cabeza local no lleva menús.** Cinco modos piden
> un menú. Un LED por perilla y un botón, no.

El comportamiento:

1. Tocas un parámetro que tiene automatización corriendo.
2. Queda **anulado**: la automatización deja de escribirlo y tú mandas.
3. **Reactivar** se lo devuelve.

El botón de Ableton hace dos cosas a la vez, y las dos hacen falta: te
**recuerda** que el estado actual difiere del escrito, y te lo **devuelve**.

### 6.2 La cinta sigue corriendo

*«Reactivar»* tiene que volver a algún sitio, y la respuesta correcta no es
obvia. Ableton dice que vuelve al estado escrito *«en la cinta»*, **y la cinta
siguió corriendo**. Así que:

> **La rampa nunca se detiene: deja de escribir.** Sigue siendo una función del
> tiempo, corriendo por dentro. Reactivar es volver a escribir desde donde la
> función esté **ahora**.

Anulas en el compás 2, tonteas un compás, reactivas: caes donde la rampa iba en
el compás 3, no en el 2. Es lo que el oído espera de una automatización, y es
trivial de probar (§9).

### 6.3 Los LED lo muestran, y sale gratis

La cadena WS2812 por perilla ya estaba puesta para el soft-takeover
(`architecture-poly.md` §7). Con esto muestra **las dos cosas a la vez**: dónde
tiene que ir la perilla para retomar el control, y si hay algo automatizado
pendiente en ese parámetro. **Un color más, cero hardware.**

---

## 7. Lo que esto cuesta

### 7.1 Tres mensajes

| Mensaje | Dirección | Para qué |
|---|---|---|
| `RAMPA` | cliente → | `{ id, destino, duración, curva }`. Duración 0 = salto cuantizado |
| `ANULADO` | → cliente | `{ id, anulado }`. Tocaste algo automatizado |
| `REACTIVAR` | cliente → | `{ id opcional }`. Con id, uno; sin id, todos |

La tabla de §4.1 del núcleo pasa de 21 a 24. **Sigue cabiendo de un vistazo**,
que era la defensa que §11 del núcleo puso contra que el invariante se pudra.

### 7.2 Todo lo demás son parámetros

Del reloj y el transporte, en la ranura `0` parte `0`:

| Parámetro | Tipo | Notas |
|---|---|---|
| `fuente de sincronía` | enumerado | automática / link / midi / clock-in / interno |
| `tempo` | continuo | milésimas de BPM |
| `compás: numerador` | continuo | **es el quantum de Link** |
| `compás: denominador` | enumerado | |
| `pulsos por negra` | enumerado | para CLOCK IN: 1 / 2 / 4 / 24 / 48 |
| `comportamiento del reset` | enumerado | ya decidido en §5.3 del núcleo |
| `división de CLOCK OUT` | enumerado | |
| `cuantización global` | enumerado | los valores de §4 |
| `transporte` | booleano | **es un parámetro, no un mensaje** |

**Que el transporte sea un parámetro tiene consecuencia:** por §2.1 del núcleo,
el agente puede arrancarte y pararte el transporte. Lo cual, pensándolo, es lo
que quieres.

De medida (solo lectura, §3.4 del núcleo):

`tiene fase` · `posición en el compás` · `compás actual` · `tempo medido` ·
`rodando libre` · `parámetros anulados`

### 7.3 Un bit en el descriptor, y nada más

El descriptor gana **una marca: «acepta modulación»**. No se usa en esta spec —
la modulación es de la 2 (§11)— pero ponerla ahora cuesta un bit y no ponerla
cuesta reescribir el modelo.

---

## 8. Alcance de la implementación

**Dentro:**

- El seguimiento de las cuatro fuentes y su precedencia, con el cambio de
  fuente en borde de compás
- El filtro del MIDI clock (§3.6)
- `tiene fase` y la degradación a pulso cuando no la hay
- La rueda libre al perder el reloj
- La cuantización global y el cálculo del siguiente borde
- `RAMPA` con su interpolación por unidad y su curva
- `ANULADO` / `REACTIVAR`, con la semántica de §6.2
- Todos los parámetros de §7.2
- `tiempo_budget.py` (§9)

**Fuera, y va en las specs 2, 3 y 4:** patrones, p-locks, modulación, LFOs,
escenas, *Follow Actions*, arpegiador, memoria de acordes, la matriz de
conmutación, y la UI.

**Fuera porque necesita hierro**, y va a `software/nucleo/fw/EN-PLACA.md`:
umbrales reales del CLOCK IN, niveles del CLOCK OUT, MIDI clock por USB de
verdad, y **Link sobre el puente** —que necesita que el puente exista y esté
elegido, cosa que hoy no ocurre—.

---

## 9. Cómo se verifica

Siguiendo la costumbre del repo: guiones ejecutables con aserciones y tests en
host, no prosa.

| Qué | Cómo |
|---|---|
| **La rampa en Hz** | 100 Hz → 1600 Hz en 4 compases. A mitad de tiempo se exige **400 Hz**, no 850. Son 4 octavas; a la mitad van 2. Una rampa lineal en hercios cae aquí |
| La rampa, en general | Aterriza **exactamente** en el destino, no en el 99.7 %. Y ninguna rampa saca un valor fuera del min/max del descriptor |
| Duración cero | Es un salto que cae en la rejilla, no un `SET` disfrazado |
| **La rejilla** | Cada valor. Y el borde exacto: disparar justo *en* el 1 tiene que caer ya, no en el siguiente — decidido y fijado en un test |
| **Seguimiento de tempo** | Pulsos con **±2 ms de jitter inyectado**, contra el techo derivado de `ERROR_TEMPO_MAX_MBPM`. *(Corregido el 2026-08-17 al implementarlo: esta fila pedía ±0.1 BPM, que era una **desviación típica** presentada como techo. El peor caso se lleva un factor de tres, y el techo correcto sale de lo que el error **cuesta** — deriva de fase mientras se rueda libre — no de lo que la ventana casualmente da.)* |
| **Sin RESET no hay compás** | `tiene fase` en falso, y una `RAMPA` con rejilla de 1 compás **aterriza en el pulso**, no en un compás inventado |
| Precedencia | Las cuatro fuentes presentes → gana Link. Se quita → MIDI. Y así hasta interno |
| Cambio de fuente | Cambiar a mitad de compás surte efecto **en el borde** |
| Rueda libre | Se corta el reloj: el tempo se mantiene y `rodando libre` se pone en verdadero |
| **Reactivar** | Anular en el compás 2, reactivar en el 3: el valor cae donde la rampa iba en el **3**. La cinta siguió corriendo |
| `SET` no se cuantiza | Un `SET` con rejilla de 4 compases surte efecto **ya** |
| Presupuestos existentes | Los seis del repo siguen en verde |

### El presupuesto nuevo: `tiempo_budget.py`

Con la forma de `autotune_budget.py`, que es la que ya demostró servir.

**Se deriva lo derivable.** La trama del J2 son 72 bits a ≤10 MHz = **7.2 µs**,
sale del contrato congelado. La latencia de interrupción del RP2350 sale del
reloj.

**Y el término que queda no se supone: se despeja.** Igual que el 74HC14 acabó
siendo *«puede temblar hasta 131 ns»*, aquí el guion despeja **cuánto puede
tardar la detección del flanco de CLOCK IN** sin romper el objetivo musical.

El objetivo se pone contra el caso duro, no contra el cómodo: un cambio de
filtro tolera decenas de milisegundos, pero la simultaneidad percibida de un
gate está en el orden del milisegundo. **El presupuesto se escribe contra el
gate.**

Y como el otro: el guion **asevera**. Si el término del micro dejara de ser
despreciable, falla y dice que el cuello volvió a ser el firmware.

---

## 10. Restricciones que esto impone a lo demás

**Al puente inalámbrico (spec del cerebro, módulo sin elegir):**

- Deja de ser solo el servidor de la UI web: es **la fuente de fase**. Si va a
  correr Link, eso pesa en la elección del módulo — hay implementaciones
  maduras sobre ESP32, y precedente de la topología exacta (Link en el ESP32,
  sesión al RP2350 por enlace serie)
- El instrumento **funciona sin él**: Link es el escalón de arriba, no el
  camino crítico

**A la spec 4 (el patch bay bilingüe):**

- La matriz **conmuta en el borde de la rejilla o con el gate abajo**. Nunca a
  mitad de nota: la inyección de carga hace clic y no hay chip que lo evite.
  Esta spec es lo que se lo permite

**A la spec 2 (patrones):**

- Un patrón es un **valor de parámetro**, así que se escribe con `SET` y se
  agenda con `RAMPA` de duración 0 sin mecanismo nuevo
- El **p-lock de Elektron** —un valor de parámetro por paso— es el modelo a
  seguir, y se anota aquí para que la 2 no lo reinvente peor
- La **modulación** es suya (§11)

**A la spec de la app:**

- La UI tiene que poder mostrar el estado *anulado* por parámetro, que llega
  por `ANULADO`, y ofrecer *Reactivar* global y por parámetro

---

## 11. Lo que se deja fuera a propósito

**La modulación no entra aquí.** Es la distinción de Ableton —la automatización
*define* el valor, la modulación solo lo *influye*— y es genuinamente valiosa:
es lo que permite *«200 Hz más brillante sin parar el barrido»*.

Se aplaza por una razón concreta: implementarla significa que **cada parámetro
tiene dos capas**, valor y modulación, y eso se paga en el modelo entero. Lo
que hace musical al agente es aterrizar en la rejilla y las rampas; la
modulación es lo que hace rico al secuenciador, y ahí vive con los LFO y los
clip envelopes que la necesitan de verdad.

Lo único que hace esta spec es **no cerrarle la puerta**: la marca del
descriptor de §7.3. Un bit hoy contra reescribir el modelo mañana.

*(Anotado de paso: la modulación en el dominio digital es el mismo
comportamiento que el instrumento ya tiene en cobre — la suma de corrientes en
el nodo expo del SSI2130, donde el CV del jack se suma al del DAC en vez de
reemplazarlo. No es un concepto nuevo, es el nombre digital de uno que ya está.)*

---

## 12. Estado de verificación

Verificado el **2026-08-17**.

| | Hallazgo |
|---|---|
| **Modos de toma de control** | Confirmado: Ableton tiene Captura, Salto y Escala. En Captura, mover el control no hace nada hasta que alcanza el valor del destino; a partir de ahí sigue 1:1 |
| **Modos de automatización** | Confirmado: Pro Tools tiene Off, Lectura, Toque, Enganche, Toque/Enganche y Escritura, más Recorte en Ultimate. Logic los mismos. **Toque** escribe solo mientras tocas y al soltar vuelve; **Enganche** no vuelve |
| **Recorte / Trim** | Confirmado: **desplaza** la automatización existente en vez de reemplazarla, y se combina con Toque y Enganche |
| **Ableton: Reactivar automatización** | Confirmado: el botón sirve para **dos cosas** — recuerda que el estado actual difiere del escrito, y al pulsarlo devuelve todo al estado escrito. Se activa al mover un control que ya tiene automatización |
| **Ableton: automatización contra modulación** | Confirmado: la automatización **define** el valor en cada punto del tiempo; la modulación solo puede **influirlo**. La modulación vive únicamente en clip envelopes |
| **Ableton: cuantización global** | Confirmada, y que cada clip tiene la suya con la opción «Global» que difiere a la global |
| **Follow Actions** | Confirmadas, con control de probabilidad. **Se saltan la cuantización global pero no la del clip** — restricción a arrastrar a la spec 3 |
| **Ableton Link** | Confirmado: sincroniza tempo, pulso **y fase**. El *quantum* son los pulsos por ciclo musical, y los participantes con el mismo quantum quedan alineados en fase. **Doble licencia GPLv2+ / propietaria** |
| **Link embebido** | Confirmado: hay implementaciones maduras sobre ESP32, y precedente de la topología exacta — Link corriendo en un ESP32 que pasa la sesión a un **RP2350** por SPI |
| **Elektron p-locks** | El modelo para la spec 2: valor por defecto más overrides por paso |

### Abiertos

1. **El objetivo temporal del presupuesto** no está fijado. Que la
   simultaneidad de un gate se juzga en el orden del milisegundo es la
   referencia de partida, pero **el número exacto contra el que asevera
   `tiempo_budget.py` hay que decidirlo al escribirlo**, y con fuente.
2. **El módulo del puente inalámbrico sigue sin elegir**, así que Link está
   diseñado-para pero no probado en este hardware.
3. **El filtro del MIDI clock** es trabajo de verdad y no está dimensionado:
   qué tipo de lazo, con qué constante de tiempo, y cuánto tarda en enganchar
   tras un cambio de tempo.

---

## Referencias

- `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md` — el núcleo:
  §2.1 el invariante, §3.3 el descriptor y su unidad, §3.4 las medidas, §4.1 la
  tabla de mensajes, §5.2 la cabeza sin menús, §5.3 clock/reset y el
  comportamiento de reset como parámetro, §7.1 los tres lazos, §7.6 nunca
  adivinar en silencio
- `software/nucleo/` — el contrato implementado que esto extiende
- `docs/architecture-compute.md` §5 — la trampa del hilo de audio y el LLM
- `docs/architecture-poly.md` §7 — el soft-takeover de las perillas, que ya
  existía
- [Ableton: Launching Clips](https://www.ableton.com/en/manual/launching-clips/) —
  cuantización global y Follow Actions
- [Ableton: Automation and Editing Envelopes](https://www.ableton.com/en/manual/automation-and-editing-envelopes/) —
  Reactivar automatización
- [Ableton: Clip Envelopes](https://www.ableton.com/en/manual/clip-envelopes/) —
  automatización contra modulación
- [Ableton Link](https://ableton.github.io/link/) — fase, quantum y licencia
