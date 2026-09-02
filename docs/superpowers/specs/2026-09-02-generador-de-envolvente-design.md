# El generador de envolvente: la fuerza encuentra a quién multiplicar

**Fecha:** 2026-09-02
**Estado:** v2, tras la junta de tres lentes (clínica, runtime, ontológica —
registro completo en §12). Las once decisiones que Samuel firmó en sesión
sobre la v1 (§13) se conservan en su intención; **seis cambian de mecanismo
por la junta y se marcan para que se vuelvan a firmar en el PR**, y nacen
cuatro más. Pendiente de PR y de esa firma. **Es papel, no código.**
**Sale de:** el issue #269 («La fuerza no tiene a quién multiplicar»).

---

## 0. El sujeto, las actas y la propiedad

**Sujeto: los generadores de envolvente del módulo de Voz** — la pieza que el
módulo 6 de la tesis hacía con un ICM7555 y que el papel de la Voz total
convirtió en software sin escribir el software: *«El módulo 6 (ADSR)
desaparece como circuito y se ejecuta en los micros de este módulo (§3), con
sus perillas en el panel de mandos»* (voz-total §1).

**Lo que este papel hereda y no reabre**, cada cosa con su sitio:

| Ya decidido | Dónde |
|---|---|
| Las envolventes son **generadores del módulo**, renderizadas localmente a **10 kHz** contra los DAC, con RC de reconstrucción en la salida | voz-total §3.1 |
| El **test de membresía** de «generador»: se dispara por un evento de la trama, entre eventos solo consume parámetros constantes, y su dominio excluye el tono. Los parámetros se **capturan al evento**; el sustain aplica **en vivo** (S-12) | voz-total §3.2 |
| **≤ 3 ms de nota a VCA**, y `ataque_budget.py` asevera el camino cuando el mensaje exista | voz-total §3.3, evento §5 |
| *«Velocity y escalados son multiplicaciones en el micro»*; el CV de corte tiene **un solo escritor**, el micro, que suma base + calibración + envolvente de filtro + modulación en digital | voz-total §2, S-9 |
| **Dos generadores por canal**: el módulo 6 eran dos ADSR, no uno | voz-total E-6 (hallazgo del guion) |
| **Topología A del estéreo**: dos VCA por canal (L/R), *«cada rama con envolvente × paneo»*; un parámetro de paneo por canal | voz-total E-6 |
| La **ley de dos tasas**: los 16 CV de corte rinden a 48 kHz; *«todos los demás siguen a 10 kHz, envolventes incluidas»*; promover un destino es acta + guion | motor-digital §5 (A-4) |
| El costo ya presupuestado: *«16+ ADSR de canal (tasa: 10 kHz, lazo automático) ~150 ciclos/muestra»* | motor-digital §7, `carga_motor_budget.py` |
| El evento lleva **destino, borde (`abre`/`cierra`/`dispara`), fuerza y tono de arranque**, y **no** lleva tiempos de envolvente: viajan como parámetros | evento §3 |
| **R-E10**: el flujo periódico reafirma el estado de compuerta de los dieciséis canales; **R-E12**: lo que solo viaja en el evento no tiene red, y la fuerza es su caso vivo | evento D6, D7 |
| **R-M1**: el módulo no interpola ni suaviza lo que recibe; **R-M2**: el tono lo genera solo el cerebro | orquestación §5 |
| **El watchdog de trama sobrevive**: sin trama válida en N ms, *«todos los generadores van a release»* | voz-total §9.2, R-M5 |
| La **fuerza** existe en el modelo: 16 bits, escalado MIDI 2.0, y el repartidor guarda la de `note on` y la de `note off` | `core/src/fuerza.rs`, `partes.rs`, #229 |
| La **barrera** de la bahía espera una máscara de canales en silencio | `core/src/bahia.rs`, PR #265 |

**Acta previa del mismo día, y por qué se registra:** Samuel preguntó si el
ADSR podía vivir en **un N657 aparte**. Se descarta con cuatro números que ya
estaban en el repo, y se escribe para que no se vuelva a proponer sin ellos
delante:

1. **No es lo que aprieta.** `carga_motor_budget.py` tiene los ADSR en 150
   ciclos por muestra de los 8 333 de la mitad heredada: menos del 2 %. Esa
   mitad va al 20-28 %, y al 59-84 % si todos los estimados mienten por tres.
   Lo rojo de la Voz es la SRAM (`sram_budget.py`), y una envolvente cuesta
   bytes, no megas.
2. **La envolvente del filtro no puede salir de la Voz** (S-9: un solo
   escritor del corte). Con la del VCA en otro chip habría dos generadores para
   la misma nota en dos relojes: el jitter maestro-esclavo que la enmienda del
   26-08 mató.
3. **Los DAC de los VCA cuelgan de los tres buses de CV de la Voz**, DMA puro
   con NSS por hardware (motor-digital §5). Un chip aparte pide buses propios
   en la zona analógica (riesgo 11) o un enlace de 32 valores a 10 kHz: más
   tráfico que el evento mismo, y un salto más en el camino de la nota.
4. **Otro N657 es otro módulo entero**: ranura del J2 (el hub tiene 6 maestros,
   4 activas + 2 de repuesto, y el mago ya se lleva una), identidad,
   descriptor, bring-up. Motor-digital §13 ya descartó «dos motores» como la
   enfermedad del #201.

Y si la preocupación es que un N657 colgado deje 48 VCA sin gobierno, la
respuesta ya existe y no es un segundo cerebro: **R-M5**, silencio por
hardware sin CPU. Un segundo micro no sustituye a una inhibición atada a
reset; es una segunda cosa que se puede morir.

Lo que sí se rescata de la pregunta: que las envolventes **no compitan con el
motor de audio**. Se consigue dentro del chip: el tick va en el escalón del
DMA de audio y CV del orden de NVIC (§9, enmienda mandada a motor-digital
§7), y el firmware puede servirlas por DMA con tramos precalculados si el
bring-up lo pide.

**Lo que hay que decir antes que nada, porque la junta lo puso delante:** el
runtime de esto **no existe**. `software/nucleo/fw` es el cerebro sobre
RP2350 (#250); no hay una línea para el N657. Este papel diseña **el modelo
en `core`**, probado en el host, y declara lo que el firmware tendrá que
hacer. Cada cifra de tiempo real de aquí es una obligación para ese firmware,
no una medida.

---

## 1. Qué es, y dónde corre

**La restricción que ningún papel nombraba, y este sí:** la ley de los
generadores (voz-total §3.2) y la frontera del evento (*«el evento lleva el
valor inicial; el flujo lleva la evolución y la verdad»*, evento D2/D6) son la
misma ley vista desde dos lados: **la nota es un objeto cerrado entre dos
bordes.** Lo que entra, entra por el borde; lo que pasa dentro lo decide la
copia que se tomó en el borde. La v1 de este papel trataba esa clausura como
un valor por defecto con excepciones argumentadas una a una; la junta cazó
que, sumadas, dejaban de describir un generador. La v2 la trata como
definición, y separa **dos objetos** que la v1 mezclaba:

| Objeto | Qué es | Qué consume | Quién lo gobierna |
|---|---|---|---|
| **El generador** | Una máquina de estados de cuatro etapas sobre un nivel `y ∈ [0, 1]`, dos por canal (VCA y filtro) | **Solo su copia capturada al borde** (los tiempos y la fuerza) y el sostenido, que S-12 hizo vivo | El test de membresía de §3.2, sin excepciones nuevas |
| **El escritor** | La etapa que convierte niveles en palabras de DAC: para el VCA, `y · fuerza · paneo`; para el corte, la suma de S-9 | Parámetros **vivos** del modelo (paneo, cantidad, base del corte) y los niveles de los generadores | S-9: *«el micro es el único escritor»*. Un escritor no es un generador: no se dispara y no tiene etapas |

Con esa partición ninguna de las «excepciones» de la v1 lo es: el paneo y la
cantidad viven en el escritor, que por S-9 ya consume parámetros vivos; el
sostenido es la excepción que S-12 legisló y no una nueva; y la fuerza es
captura, no memoria (§3.4).

**Treinta y dos generadores y dos escritores** en el N657 de la Voz,
avanzados por un **tick de 10 kHz** (`F_RENDER = 10 000 Hz`, `dt = 100 µs`,
voz-total §3.1). Tres formas se pusieron sobre la mesa, y se eligió la
primera:

| | Forma | Veredicto |
|---|---|---|
| **A** | **Exponencial de un polo por etapa**: el carácter del circuito de la tesis —un condensador que carga y descarga— hecho número | **Elegida.** Cero parámetros de forma, suena a lo que la tesis ya sonaba, y cuesta una multiplicación por tick |
| B | Segmentos lineales con perilla de curva por etapa, como `rampa.rs` | Cuatro parámetros más por envolvente, y suena a máquina si la curva no se toca |
| C | Tramos precalculados servidos por DMA sin CPU | No es un modelo: es una forma de renderizar A en el firmware. Queda anotada en §9 |

**Reparto de propiedad, en una línea:** generadores y escritores viven en
`core`, `no_std`, probados en el host; el firmware de la Voz solo llama al
tick desde su temporizador, encola lo que llega por el J2 (§3.5) y mueve las
palabras al DAC por DMA. Cada línea de lógica que se quedara en `fw` sería
una línea sin puerta.

**Cumplimiento del test de §3.2, fila por fila, para el generador:** (a) se
dispara por un borde —del evento, de la reafirmación o del watchdog; las tres
fuentes se declaran en §3.4 y son una enmienda a (a), no un contrabando—;
(b) entre bordes solo lee su copia capturada y el sostenido, que es un
parámetro constante hasta que alguien lo escribe; (c) no toca el tono.

---

## 2. Las etapas

Todas las etapas son la misma ecuación con distinto destino y distinta
constante de tiempo:

```
y ← y + k · (destino − y)        k = 1 − exp(−dt / τ)
```

`k` se calcula **una vez, al capturar** (una `exp` por borde y por etapa, en
el tick, §3.5); el tick es una multiplicación y una suma.

**Cómo termina cada etapa, y por qué por cuenta y no por umbral.** La v1
terminaba el decaimiento cuando `|y − S| ≤ 10⁻³·|1 − S|`. La lente de
runtime lo corrió en `f32` sobre el barrido de tests firmado: **11 de 36
casillas no terminan nunca**, incluido el `def` (T_D = 10 s, S = 700 ‰): el
punto fijo de la recurrencia en `f32` queda a `ulp(S)/(2k)` del destino, y
con `k ≈ 6,9·10⁻⁵` eso es más lejos que el umbral. Un umbral relativo a
`1 − S` contra una resolución absoluta cerca de 1 no puede cerrar. Así que
las etapas de duración conocida **terminan por cuenta de ticks**, y al
terminar el nivel se **ajusta exacto** al valor que la curva alcanza por
construcción. La forma es la misma; el fin es aritmética entera.

### 2.1 El ataque: una carga RC truncada (decisión 1)

El circuito de la tesis (`docs/modules/06-adsr.md`: *«El pin OUTPUT del 7555
sube → corriente carga el cap a través del pot ATTACK. Al alcanzar el
THRESHOLD, OUTPUT baja»*) carga el condensador hacia la alimentación y corta
la etapa cuando el nivel llega al umbral del 555, a **2/3** de la
alimentación. Eso es una exponencial que apunta más arriba del pico y se
trunca al llegar: convexa suave, y con **tiempo finito**, que una exponencial
pura no tiene.

```
destino = 1,5                  (= 1 / (2/3): el pico es 2/3 del destino)
τ_A = T_A / ln 3               (1,5·(1 − e^(−t/τ)) = 1  ⇔  t = τ·ln 3)
N_A = round(T_A / dt)          ticks; al tick N_A:  y := 1, pasa a decaimiento
```

`T_A` es exactamente **el tiempo de cero al pico**. Un re-disparo desde un
nivel `y₀ > 0` (§3.2) llega antes —`τ_A · ln((1,5 − y₀) / 0,5)`, y N_A se
recalcula con ese valor— que es lo que el circuito hace.

El diseño no depende del número 2/3: cualquier truncado entre la mitad y tres
cuartos da la misma familia de curvas. Se adopta el del 555 porque es el que
da el carácter de la tesis; la hoja del ICM7555 no está en el árbol y no hace
falta para esto.

### 2.2 Decaimiento y relajación: hasta −60 dB (decisión 2)

Las dos son exponenciales asintóticas. Como no llegan nunca, hay que decir
qué mide el «tiempo» de la perilla, y se elige la convención del RT60: **el
tiempo en que el recorrido cae a la milésima**, que es lo que el oído llama
«largo del release».

```
decaimiento:  destino = S (vivo, §2.3);   τ_D = T_D / ln 1000
              N_D = round(T_D / dt);  al tick N_D:  y := S, pasa a sostenido
              (si al entrar S = 1 no hay decaimiento: pasa directo)
relajación:   destino = 0;   τ_R = T_R / ln 1000
              termina cuando y < NIVEL_OCIOSO  →  y := 0, ocioso (§6)
```

La relajación sí termina por umbral: con destino cero la recurrencia es
`y ← y·(1 − k)`, geométrica, sin punto fijo por encima de cero, y la lente de
runtime la vio cerrar en todo el barrido. Su duración depende del nivel de
partida `y₀`, y hay que decirlo porque la v1 lo escondía:

```
t_silencio = τ_R · ln(y₀ / NIVEL_OCIOSO)
             desde 1:     1,61 · T_R        desde 700 ‰:  1,55 · T_R
             desde 300 ‰: 1,43 · T_R        desde 100 ‰:  1,27 · T_R
```

Una relajación normal arranca desde el sostenido, no desde el pico; el test
de §8 barre `y₀`.

### 2.3 El sostenido, en vivo y sin filtro (S-12, y R-M1)

En la etapa de sostenido **`y = S` en cada tick**: el nivel es el parámetro.
S-12 dice *«el sustain aplica en vivo»* y nada más. La v1 lo hacía seguir al
parámetro con la constante del decaimiento, y la lente ontológica cazó lo que
eso era: **un suavizado dentro del módulo**, que R-M1 prohíbe con todas sus
letras (*«todo suavizado vive en el cerebro y en un solo sitio»*): una rampa
de duración cero —salto deliberado por definición del núcleo §4.1— se habría
convertido en un deslizamiento de un segundo y medio con `T_D = 10 s`. El
módulo aplica lo que recibe cuando lo recibe. Si una perilla de sustain tiene
que deslizar, lo hace el cerebro con una rampa, como con cualquier parámetro.

Consecuencia limpia: **el sostenido no se captura**. El decaimiento apunta al
`S` vivo y el sostenido lo es. Lo que se captura al borde es la forma de la
nota —los tres tiempos— y su fuerza (§3.3).

---

## 3. El evento

### 3.1 Los tres bordes

| Borde (evento §3) | Qué hace el generador |
|---|---|
| `abre` | Captura (§3.3), levanta su compuerta propia, arranca el **ataque desde el nivel actual** (§3.2) |
| `cierra` | Baja su compuerta propia y pasa a **relajación desde el nivel actual**, esté en la etapa que esté |
| `dispara` | Captura, **sin levantar la compuerta**: ataque → decaimiento → **relajación al llegar al sostenido**, sin sostener (decisión 3). Así las dos perillas cuentan en un tambor: con S = 0 el decaimiento es la caída, con S > 0 el release arranca desde S |

Un `cierra` sobre un canal ocioso no hace nada. Un `abre` o un `dispara`
sobre un canal en cualquier etapa es un **re-disparo**. Los dos generadores
del canal (VCA y filtro) reciben el mismo borde y capturan a la vez; **el
estado del canal** —su compuerta propia, su silencio— **lo define el
generador del VCA**.

**El canal conducto** (motor-digital D-P3: un canal que presta su cuerpo al
audio digital, *«su VCA lo articula el micro con una envolvente disparada por
el evento de ruteo del preset, no por nota»*) no es un caso del generador: es
un canal cuyo `abre` y `cierra` **los emite el cerebro por el ruteo** en vez
de por una tecla. Y el orden para deshacer una ruta que pase por un conducto
es el mismo que para cualquier canal: el cerebro emite `cierra`, el canal
llega al silencio, y entonces la barrera commitea. No hay circularidad: el
`cierra` precede a la propuesta, no la espera.

### 3.2 El re-disparo, sin clic, medido en la salida (decisión 4)

`abre` sobre una voz que suena o se libera —el caso normal del robo de voz:
`Asignacion.robada` en `partes.rs`— **no reinicia a cero**. Pero la lente de
runtime midió la v1 en la palabra del DAC y no en `y`, y el clic estaba ahí:
la ganancia de fuerza `g_v` (§4.1) se captura al borde, y una voz robada a
`y = 0,8` que pasa de fuerza plena a 0,1 caía un 36 % de la escala en un
tick. La continuidad se define **sobre lo que se oye**, no sobre el nivel
interno:

```
a₀ = y_vieja · g_v,vieja                  (la amplitud que sonaba)
y₀ = min(1, a₀ / g_v,nueva)               (el nivel interno que la conserva)
```

Con `y₀` el ataque arranca desde la misma amplitud, y llega antes (§2.1). Si
`a₀ > g_v,nueva` —la nota nueva es **más suave** que lo que ya sonaba— la
amplitud baja al techo nuevo en un tick: `y₀ = 1` y la nota entra directo en
decaimiento. Ese escalón hacia abajo **se declara y se acepta**: es el mismo
que da un poli analógico al robar una voz con menos velocity, y suavizarlo
sería un suavizado del módulo (R-M1). El test de §8 mide la palabra, no `y`,
y asevera las dos mitades: continuidad hacia arriba, escalón de un tick hacia
abajo.

### 3.3 La captura al borde (voz-total §3.2)

Al `abre` y al `dispara` el generador **copia** los tres tiempos de cada
envolvente (`T_A`, `T_D`, `T_R`) y la fuerza del borde; el escritor del VCA
copia con ella la ganancia `g_v`. La nota corre con esa copia hasta que
termina; la siguiente nota usa los valores nuevos. **Lo que no se captura,
porque no es forma de la nota sino lectura viva del escritor**: el sostenido
(§2.3, S-12), el paneo (§4.2) y la cantidad de envolvente del filtro (§5).
La v1 capturaba la cantidad y nadie consumía la copia; la junta lo llamó por
su nombre.

### 3.4 Las tres fuentes de borde, y la red de R-E10 (decisión 9, refirmada)

El generador se dispara por **tres** fuentes, y decirlo es una enmienda a la
letra (a) de voz-total §3.2 (mapa en §14):

1. **El evento de nota** (evento §3), el camino rápido.
2. **La reafirmación de compuerta** (R-E10): el flujo periódico trae el
   estado de compuerta de los dieciséis canales, y de él se reconstruye el
   borde que se perdió. Es un evento reconstruido, no un flujo.
3. **El watchdog de trama** (voz-total §9.2): sin trama válida en N ms, el
   firmware llama `soltar_todo()` y **todos** los generadores van a
   relajación y bajan su compuerta propia.

**La compuerta de R-E10 es una compuerta, no un disparo.** Cada generador
lleva su **compuerta propia**: la levanta `abre`, la baja `cierra`, y
`dispara` **no la toca**. El bit del flujo se compara solo contra ella:

| Bit del flujo | Compuerta propia | Acción |
|---|---|---|
| 1 | baja | `abre` con la **fuerza de reparación** (abajo). Cubre el `abre` perdido, **incluido el caso normal**: una voz que estaba en relajación y volvió a sonar |
| 0 | alta | `cierra` |
| igual | igual | nada. Una compuerta abierta sobre una nota que ya suena no re-dispara |

Con eso `dispara` es **invisible** para la red: un tambor en decaimiento
tiene la compuerta propia baja y el bit bajo, y ni se trunca ni resucita.
El precio, dicho: **un `dispara` perdido es un golpe perdido**. Un disparo no
tiene nivel que reafirmar (evento §0.1 ya lo admitía), así que cae en la clase
de R-E12 —lo que solo viaja en el evento no tiene red— y se declara
irreparable. Es la primera vez que un borde se declara así, y la lente
ontológica lo pidió como ley: *todo borde tiene un nivel que lo repara o se
declara irreparable*.

**La fuerza de reparación no es una memoria.** La v1 abría la nota reparada
con «la última fuerza que ese canal tuvo»; las tres lentes cazaron lo mismo:
un estado por canal que el modelo no publica (núcleo §2.1), que discrepa de
la memoria que `partes.rs` ya guarda (allí `nota_off` sobrescribe la fuerza
con la de soltar), y que podía ser la de un `cierra` a cero. R-E12 dice *«un
valor por defecto»* y eso es lo que hay: una **constante declarada**,
`FUERZA_REPARACION`, **propuesta a plena (`u16::MAX`)**: una nota reparada
tiene que oírse, y un valor que se oye como error es preferible a uno que se
confunde con una nota tocada. Es la decisión 12 de §13, a firmar. La nota
reparada tampoco lleva tono de arranque: arranca en el último tono que trajo
el flujo, que R-M4 refresca a 1 kHz. Las dos son la degradación que R-E12
anuncia, escrita.

**La reafirmación necesita saber si es vieja.** El bloque de compuerta se
arma en el cerebro con su estado de ese instante y viaja en la cadencia; un
evento emitido después (D1) puede llegar antes. Sin más, un `abre` seguido de
un bloque armado antes lo cerraría, y un `cierra` seguido de un bloque viejo
resucitaría la nota. La regla: **el bloque de compuerta lleva el contador de
eventos emitidos** por el cerebro para ese módulo; el módulo lleva su cuenta
de eventos recibidos; un bloque con contador **menor** que la cuenta del
módulo es viejo y se ignora; igual o mayor, se aplica. Es un requisito para
la cabecera del J2 (#267), y se manda en §14. Tras `soltar_todo()` el módulo
adopta el contador del primer bloque válido que llegue y lo aplica: las notas
que el cerebro sostenía vuelven, con la fuerza de reparación. Es la
recuperación del watchdog, y es la que R-E10 prometía.

### 3.5 Un solo dueño del estado

La lente de runtime lo encontró en la primera lectura: el evento llega por
la ISR del esclavo J2, el tick corre en la ISR del temporizador, y los dos
tocarían el mismo generador. Un `cierra` que entre entre «leo `y`» y
«escribo la etapa» **se pierde**, y con él la nota hasta la red. `core` no
tiene secciones críticas y no las va a tener. La regla:

- **El tick es el único dueño del estado.** Solo él muta generadores y
  escritores.
- **Todo lo demás encola**: eventos, reafirmaciones, escrituras de
  parámetros, `soltar_todo()`. La ISR del J2 deja el mensaje en una **cola
  FIFO** sin cerrojo (un productor, un consumidor) y vuelve.
- **El tick drena la cola entera, en orden, antes de avanzar.** Dos eventos
  sobre el mismo canal en un tick se aplican en orden: `abre` y `cierra`
  seguidos abren y liberan desde el primer paso del ataque, que es lo que
  pasó. Nada se coalesce.
- Las transcendentales —`exp` al capturar, `cos`/`sin` al escribir el
  paneo— corren **en el tick**, al aplicar lo drenado, no en la ISR del J2.
- **Los parámetros se empujan, no se buscan**: la escritura de un parámetro
  del generador o del escritor termina en la ranura del canal (un índice), y
  el tick jamás consulta el modelo por búsqueda. La lente de runtime contó lo
  otro: 32 búsquedas binarias por tick se comen la fila entera del
  presupuesto.

La cola tiene **64 entradas** —un acorde de dieciséis voces abriéndose y
cerrándose dos veces dentro de un tick— y un desborde **cuenta y sube por
salud**, no se calla. Y el orden en el enlace se acepta como es: el J2 es
FIFO, así que un `SET` que el cerebro tenga en cola detrás del bloque
periódico puede ser adelantado por un evento (D1). La nota usa el valor de
hace 100 µs. *«La siguiente nota usa los valores nuevos»* vale a la
granularidad del enlace, y se dice.

---

## 4. El escritor del VCA

### 4.1 La fuerza multiplica la amplitud (decisión 5)

```
v = fuerza / 65 535                 (Fuerza de core/src/fuerza.rs, 16 bits)
s = sensibilidad / 1 000            (parámetro por voz, milésimas)
g_v = (1 − s) + s · v               capturado al borde (§3.3)
```

Con `s = 0` la fuerza no hace nada; con `s = 1` una nota a fuerza cero no
suena. Lineal a propósito: la curva ya la puso MIDI 2.0 al escalar los 7 bits
(`fuerza.rs`), y una segunda curva aquí sería aplicarla dos veces. **La fuerza
de `note off`** el repartidor la guarda y este papel **no la usa en v1**: si
un día el release debe depender de cómo se suelta la tecla, es un parámetro
nuevo y una decisión, no un olvido.

### 4.2 El paneo, a potencia constante y vivo (decisión 6)

E-6 eligió dos VCA por canal, uno por rama, *«cada rama con envolvente ×
paneo»*. El parámetro de paneo por canal ya está censado
(`check_censo_voz.py`, `PANEO_POR_CANAL = 1`):

```
p = paneo / 1 000                   (0 = izquierda, 500 = centro, 1000 = derecha)
L = cos(p · π/2)     R = sin(p · π/2)        L² + R² = 1
```

A potencia constante el centro está a −3 dB en cada rama y una voz que
cruza el campo no sube ni baja de sonoridad. Los factores se recalculan
**cuando el parámetro llega** (en el tick, §3.5), no por tick, y aplican en
vivo porque el paneo es del escritor, no del generador (§1). Un `SET` de
paneo es un escalón en L y R, **y así tiene que ser**: R-M1 le prohíbe al
módulo suavizarlo; el cerebro, que sabe si el paneo se mueve a mano o por el
agente, lo rampa como a cualquier parámetro (núcleo §5). La v1 prohibía el
escalón para el re-disparo y lo ordenaba para el paneo sin decir por qué; el
porqué es este: uno es un borde del módulo y el otro es un parámetro del
cerebro.

### 4.3 Lo que sale por el DAC, y la ley que nadie había escrito

Por canal y por tick, el escritor calcula dos **amplitudes**:

```
a_L = y_vca · g_v · L          a_R = y_vca · g_v · R          a ∈ [0, 1]
```

y de cada una **una palabra de 16 bits** (motor-digital §5: *«el dato del CV
es de 16 bits»*; la trama concreta es del DAC que R-M3 nombre; la referencia
de modelo es la palabra clase AD5686R que `core/src/j2.rs` ya compone).

**Y aquí la lente clínica encontró un supuesto de toda la v1:** que la
palabra fuera **lineal en amplitud**. El VCA de voz es ¼ de SSI2164 (voz-total
§2), y ningún papel declaraba la ley palabra → ganancia. Si la palabra fuera
lineal en dB, el RT60 de la decisión 2, la sensibilidad de la 5 y el −3 dB de
la 6 significarían otra cosa en cobre.

Se resuelve **separando el modelo del cobre**: el generador y las decisiones
firmadas hablan de **amplitud**, que es lo que el oído y la tesis miden; la
conversión de amplitud a palabra de control es **del escritor**, con la ley
del VCA delante. **Y la hoja ya está en el árbol**
(`docs/reference/datasheets/ssi2164-rev3.4-2023-02.pdf`, Rev. 3.4, febrero
2023), y la ley es esta, verbatim (p. 4, «Control Port»):

> *«The SSI2164 provides exponential control with gain constant of −33mV/dB;
> to realize the full gain range of +20dB to −100dB, control voltage should
> span from −660mV to 3.3V, respectively. If only attenuation is desired, the
> control port can be driven directly from a low impedance voltage-output
> DAC.»* Y p. 6: *«a positive VC attenuates the input and a negative VC
> amplifies the input. The VCA has unity gain for a control voltage of
> 0.0V».*

O sea, **control exponencial, referido a masa, −33 mV por dB**; unidad a
0 V; +3,3 V son −100 dB; y para solo atenuar —que es el caso del VCA de
voz— el puerto se puede colgar **directamente de un DAC de voltaje**. La ley
del escritor, en amplitud:

```
V_C(a) = −0,033 V/dB · 20·log10(a)  =  −0,66 V · log10(a)      (a ≤ 1)
V_C(1) = 0 V        V_C(2⁻¹⁶) = 3,18 V (−96 dB)        V_C(0) → tope: +3,3 V (−100 dB)
```

Es un logaritmo por rama y por tick (32 × 10 kHz = 320 000 por segundo): una
**tabla de mil entradas con interpolación** lo cubre en el escritor, y cabe en
la fila del escritor de CV. **Lo que no se negocia**: `ley_vca(0)` es **la
palabra que cierra el VCA** —el tope de +3,3 V, o más—, porque voz-total §9.1
ya legisló que cero-escala es VCA cerrado y se verifica en bring-up. Y como
el sentido del puerto es «más voltaje, menos ganancia», **la palabra cero del
DAC no puede ir directa al puerto**: cero-escala tiene que ser el tope de
atenuación, por escala y desplazamiento en cobre o por el mapa de la tabla.

**Lo que sigue siendo HUECO, con la hoja delante:** (1) la **escala y el
desplazamiento** entre la palabra del DAC y `V_C` —del esquemático, con el
DAC que R-M3 nombre—; y (2) si el puerto se **compensa en temperatura**: la
hoja dice que los −33 mV/dB son *«proportional to absolute temperature, or
approximately 0.33%/°C»*, y su Figura 2 muestra un puerto compensado con NTC
que sale a **−50 mV/dB**. La constante de la tabla depende de esa decisión
de cobre; la forma de la ley, no.

---

## 5. La envolvente del filtro (decisión 7, refirmada)

El segundo generador de cada canal tiene sus propios tres tiempos y su
sostenido, y se dispara con el **mismo borde** que el del VCA. Entrega
`y_f ∈ [0, 1]` como `u16` por tick, y **no escribe ningún DAC**: se lo da al
escritor del corte, que por S-9 es el único que suma. El escritor lo aplica
**en octavas** con la **cantidad viva** del modelo:

```
f = f_base · 2^(cantidad · y_f / 1 200)      cantidad en cents, bipolar, viva
```

y lo convierte a CV por la curva de calibración de §4 de la Voz total. Los
±4 800 cents firmados son cuatro octavas hacia cada lado.

**El suavizado, dicho de frente esta vez.** El corte se escribe a 48 kHz (ley
de dos tasas) y `y_f` cambia a 10 kHz. La v1 decía que el escritor
«interpolaba linealmente entre dos ticks consecutivos» y lo llamaba
«reconstrucción»; las tres lentes lo desmontaron: interpolar entre dos ticks
exige conocer el siguiente (un tick de retardo que la v1 no contaba),
48 000 / 10 000 = 4,8 no es entero y el patrón de muestras deriva si los
relojes no cuelgan del mismo PLL, y «reconstruir» una señal con esquinas es
una metáfora. Lo que hay en la v2 es **un polo**:

```
en el escritor, a 48 kHz:   z ← z + k₄₈ · (y_f − z)        τ = un tick (100 µs)
```

Causal (no mira el tick siguiente), indiferente a la razón de relojes (sirve
con 4, 5 o 6 muestras por tick), y **exactamente el gemelo de la RC que el
DAC del VCA lleva en cobre** (§9): retén de orden cero más un polo. Su retardo
de grupo es de un tick: la envolvente del filtro va **100 µs detrás** de la
del VCA de la misma nota, igual que la RC retrasa la del VCA respecto a la
palabra. Se declara; no está en el camino nota → VCA de §9.

**Es una enmienda a motor-digital §5, y se manda como tal (§14):** *una fuente
lenta puede alimentar un destino rápido a través de un polo de un tick en el
escritor; el polo es del escritor, que ya es rápido, y la fuente sigue
lenta.* La v1 lo afirmaba en una subordinada («esto no es promover»); la lente
ontológica lo llamó criterio implícito, que es lo que §5 prohíbe. Con la
enmienda escrita, deja de serlo.

**El costo, sin el «nada» de la v1:** la exponencial y la curva de calibración
del corte corren a 48 kHz × 16 **de todas formas** —el corte es destino
rápido y su escritor ya está en la fila *«Escritor de CV: cómputo 64 valores
+ empaquetado + feed de DMA, ~500-800 ciclos»* de motor-digital §7—. Lo que
este papel añade a esa fila es el polo (una multiplicación y una suma por
canal y por muestra) y el producto por la cantidad. El suavizado se aplica a
`y_f` **antes** de la suma de S-9, sobre un flujo que el módulo genera él
mismo: R-M1 intacto, sin la lectura estrecha que la v1 necesitaba.

**La fuerza no toca la envolvente del filtro en v1.** Es la lectura estricta
de la decisión 5 (*«la fuerza multiplica la amplitud»*). Un «fuerza → cantidad
de filtro» es un parámetro más por voz y una decisión aparte (§10).

**Dónde vive:** en `core`, como una función del escritor del corte que este
papel define por contrato (la ley de octavas, el polo) y que el papel del
escritor de corte hereda. Legislar su contrato de entrada no es diseñar el
escritor; lo segundo sigue siendo suyo (§10).

---

## 6. El silencio y la bahía (decisión 8, refirmada)

Un canal está **en silencio** cuando **su generador de VCA está ocioso**: la
relajación terminó. Es un hecho del canal, definido en el modelo, y es lo que
la ley de conmutación de la Voz total §5.3 quiere decir con «canales en
silencio». La v1 lo definía como «cuando el DAC escribiría cero», y las tres
lentes lo desmontaron: la palabra es `ley_vca(y · g_v · L)`, que es cero
antes de que `y` lo sea en cuanto la fuerza o el paneo no valen uno, y es
cero toda la nota si `s = 1` y `v = 0`; y atar un predicado de topología al
ancho de una palabra de DAC es una fuga de capa. El silencio es del
generador, no del formato.

```
NIVEL_OCIOSO = 2⁻¹⁶          constante del MODELO: el nivel por debajo del
                             cual una envolvente se declara terminada. Hoy
                             coincide con el LSB de 16 bits; si el DAC cambia
                             de ancho, esta constante no lo sigue.
```

Los generadores exponen `en_silencio() -> u16`, la máscara de dieciséis bits
que `Barrera::tick(canales_en_silencio, ahora_ms)` de `bahia.rs` recibe. Un
canal con una nota a fuerza cero **no está en silencio** aunque no se oiga:
su envolvente corre y su cuerpo está en uso; la barrera espera, que es lo
conservador. Bajo `diferir` un drone a fuerza cero bloquea como cualquier
drone: es la elección del intérprete que H-OF3 hizo visible.

**La barrera y un `abre` en vuelo.** La barrera decide con la máscara de un
tick; el firmware shiftea 512 bits y latchea, y a los 5 MHz máximos de la
hoja del AD75019 eso son **102 µs: más de un tick**. Un `abre` que entre en
esa ventana abriría un canal a medio conmutar, que es lo que la barrera
existe para impedir. La regla: `Commit` gana el campo `cambian` (los canales
cuyos cruces cambian); mientras el firmware no llame `conmutado()`, esos
canales están **en conmutación** y un `abre` sobre ellos **espera en la cola**
(§3.5) hasta el tick siguiente al latch. Dos ticks de retención como máximo,
solo sobre los canales que cambian, solo mientras se latchea.

**`forzar` no es ejecutable en v1.** Su «mute breve» (`Commit::mutear`,
HUECO declarado en `bahia.rs`) tiene aquí su sitio natural —una ganancia de
canal aparte de las etapas, en el escritor: baja en N ticks, sostiene el
latch, sube— y sigue sin número: N depende de cuánto dura el glitch del
AD75019, que su hoja no dice (voz-total §11.2, bring-up). Hasta que tenga
número, la política de un preset **solo puede ser `diferir`**, y `bahia.rs`
lo dirá en su doc.

---

## 7. Los parámetros y el censo (decisiones 10 y 11, refirmadas)

Los parámetros del generador y del escritor son **del módulo de Voz**
(poseedor), **por voz** (`Ambito::PorVoz`, dieciséis instancias), escribibles,
sin medida. En el modelo **existen solo por voz**: no hay «los valores de la
parte» como objeto aparte —`Parte` en `partes.rs` es un tramo del pool con un
número de preset, no un juego de parámetros—. Lo que la v1 llamaba «el cerebro
escribe los valores de la parte en sus canales» es, con su nombre de verdad,
**la carga del preset de la parte**: un preset es *«de una parte»*
(`preset.rs`) y guarda, para un parámetro por voz, *«N»* valores (`descriptor.rs`,
§3.6), uno por cada voz del tramo. La carga escribe esos N. La puerta por la
que escribe y lo que la ley de capas hace con un parámetro que la mano
capturó es de `Politica` (N1/N2) y del cambio 12, **no de este papel**.

| Parámetro (por voz) | Unidad (`descriptor::Unidad`) | Rango firmado | Captura | `def` propuesto |
|---|---|---|---|---|
| `vca_ataque` | Milisegundos | 1 – 10 000 | al borde | 5 |
| `vca_decaimiento` | Milisegundos | 1 – 10 000 | al borde | 200 |
| `vca_sostenido` | Milesimas | 0 – 1 000 | **vivo** (S-12) | 700 |
| `vca_relajacion` | Milisegundos | 1 – 20 000 | al borde | 300 |
| `filtro_ataque` | Milisegundos | 1 – 10 000 | al borde | 5 |
| `filtro_decaimiento` | Milisegundos | 1 – 10 000 | al borde | 300 |
| `filtro_sostenido` | Milesimas | 0 – 1 000 | **vivo** (S-12) | 300 |
| `filtro_relajacion` | Milisegundos | 1 – 20 000 | al borde | 300 |
| `sensibilidad_fuerza` | Milesimas | 0 – 1 000 | al borde (en `g_v`) | 500 |
| `filtro_cantidad` | Cents | −4 800 – +4 800 | **vivo** (escritor) | 0 |

Los rangos son **decisión firmada, no cita**: ningún papel los fijaba. Los
`def` son **propuesta para el campo `def` del descriptor** y se firman en el
PR de código, no aquí. El paneo no está en la tabla porque ya está censado
(E-6).

**El censo, corrido con las cifras de `check_censo_voz.py` — y esta vez con
su reserva, que la v1 olvidó:** 10 parámetros × 16 voces = **160 entradas
nuevas**. El guion suma la base v2 (226), los 9 por canal de voz-total §7, el
paneo y las aristas y vínculos derivados (150), y **aparta 256** como
habitación del motor y de los gestos, *«ausentes y visibles»* (#172):

| | Entradas | Con la reserva de 256 | De `MAX_PARAMS = 1024` |
|---|---|---|---|
| Hoy (guion) | 536 | 792 | quedan 232 |
| Con el generador | **696** | **952** | **quedan 72** |

Cabe, y la v1 decía «cabe» con 696 contra 1024 como si los 232 fueran
holgura. No lo son: son la habitación de dos inquilinos que nadie ha censado,
y este papel les deja **72**. Es el riesgo 3 de §11, y `MAX_PARAMS` es una
capacidad de `heapless::Vec` en `modelo.rs`, no una ley: si el censo del
motor pide más, crece y se paga en RAM del cerebro. En memoria: 696 entradas
a 100 B (E-7) son 69,6 KB, más 1,6 KB de curvas, 2,7 KB de calibración y
3 KB de etiquetas: **76,9 KB, el 58,7 % de los 128 KB**, con el 30 % de
margen que el guion exige. (A los 42 B por entrada que el descriptor ocupa
hoy son 36,5 KB, el 28 %: el `TOTAL` que el guion imprime es ese; el 58,7 %
está en su tabla de candidatas, a los 100 B del objetivo de E-7.) **La fila `ENVOLVENTE_POR_CANAL = 10` entra al
guion en el PR de código** (§9).

**Dos cosas que el censo no puede verificar, dichas:** los «+9/canal» de
voz-total §7 **no están desglosados en ningún papel**; si ya contenían las
perillas del ADSR que se mudó al micro ese mismo día, las 160 duplican. Y
**ninguna de las 160 es direccionable hoy**: voz-total §7 dice que el modelo
de la Voz total no lo es hasta los cambios 2 y 12. Este papel declara los
parámetros para cuando lo sea; mientras, los tests construyen el generador
con ellos a mano.

---

## 8. Numérica y tests

- **`f32`** para el nivel y las constantes; el N657 tiene FPU y `core` ya
  depende de `libm`. Las `exp` se hacen al capturar; el tick no tiene
  transcendentales. Las etapas de duración conocida terminan **por cuenta**
  (§2) y la relajación por umbral hacia cero, que es geométrica: nada se
  atasca.
- **Determinismo**: el mismo borde con los mismos parámetros da la misma
  secuencia de amplitudes en el host y en el chip (IEEE-754, sin `fast-math`),
  **porque todo se aplica en el tick** (§3.5). Con dos ISR mutando el estado
  no sería cierto, y por eso no las hay.
- **La salida del modelo es amplitud** `a ∈ [0, 1]`; la palabra la hace
  `ley_vca` (§4.3), que se prueba aparte cuando tenga hoja.

Los tests, en `core`, **barren en vez de elegir dos puntos**:

1. **Ataque**: para T_A en {1, 3, 10, 100, 1 000, 10 000} ms, desde cero, el
   nivel es monótono, vale exactamente 1 en el tick `N_A`, y a mitad de camino
   vale `1,5·(1 − 3^(−1/2)) = 0,634` ± 1 LSB: la forma, no solo el fin.
2. **Decaimiento**: para S en {0, 100, 500, 700, 900, 999, 1 000} ‰ y T_D
   barrido, cae monótono, vale exactamente S en el tick `N_D`, y a mitad de
   camino la distancia a S es `1000^(−1/2) = 3,2 %` de `1 − S` ± 1 LSB; con
   S = 1 000 no hay decaimiento.
3. **Relajación**: para T_R barrido **y `y₀` en {1, 700, 300, 100} ‰**, llega
   a `NIVEL_OCIOSO` en `τ_R·ln(y₀/NIVEL_OCIOSO) ± 1 tick` y la amplitud final
   es cero.
4. **`dispara`**: recorre ataque → decaimiento → relajación sin sostener, con
   la compuerta propia baja todo el tiempo; con S = 0 la relajación arranca
   en cero.
5. **Re-disparo, medido en la amplitud**: un `abre` en mitad de cada etapa con
   fuerza mayor o igual no salta más que un paso del ataque más corto; con
   fuerza menor baja al techo nuevo en exactamente un tick y entra en
   decaimiento.
6. **Captura**: cambiar un tiempo con la nota abierta no cambia esa nota;
   cambiar el sostenido sí, **en el mismo tick**, sin filtro.
7. **Fuerza**: con s barrida y v barrida, la amplitud es lineal en v, y
   `s = 0` la anula.
8. **Paneo**: para p barrido, `L² + R² = 1` con error < 1 LSB, y p = 500 da
   −3 dB en cada rama; un cambio de paneo aplica en el tick siguiente, sin
   rampa.
9. **Silencio**: la máscara sube exactamente en el tick en que la relajación
   termina, y no antes; con dieciséis canales en etapas distintas es correcta
   bit a bit; una nota a fuerza cero **no** está en silencio.
10. **Reafirmar**: bit alto sobre compuerta baja abre —también desde la
    relajación—; bit bajo sobre compuerta alta cierra; `dispara` es invisible
    en las dos direcciones; un bloque con contador viejo no hace nada; la
    fuerza de reparación es la constante.
11. **La cola**: `abre` y `cierra` en el mismo tick se aplican en orden; un
    desborde cuenta; un `abre` sobre un canal en conmutación espera al
    `conmutado()` y no antes.
12. **Watchdog**: `soltar_todo()` lleva todo a relajación y baja todas las
    compuertas; el primer bloque válido después reabre lo que el cerebro
    sostiene, con la fuerza de reparación.
13. **Filtro**: `y_f` recorre sus etapas con sus propios tiempos; el polo del
    escritor responde a un escalón de `y_f` como `1 − e^(−n/4,8)` por muestra,
    sin mirar el tick siguiente, y con 4, 5 o 6 muestras por tick.
14. **Costo**: un test que cuente operaciones por tick no prueba ciclos; el
    costo real se mide en el bring-up (`carga_motor`, R-M2). Se dice para no
    fingir.

---

## 9. Presupuestos y guiones

**`ataque_budget.py` nace** (el evento §5 lo manda y no existe). Sus filas,
con los huecos dichos y sin rellenar; la cifra «hoy 28,8 µs» de la v1 se
retira porque era del bus compartido que el J2 punto a punto mató:

| Término | Cuánto | De dónde |
|---|---|---|
| Reacción del cerebro | **HUECO** | evento §5: depende de dónde viva el host USB (C2) |
| Turno del J2 | ≤ 100 µs | R-E1 (la cota viva; la cifra vieja no) |
| Parse del evento y encolado en el N657 | **HUECO** | bring-up, ISR del esclavo SPI (motor-digital §7) |
| Latencia de la ISR del tick bajo las capturas y el J2 | **HUECO** | bring-up bajo carga plena (motor-digital §7) |
| **Primer tick del generador** | ≤ 100 µs | este papel: el evento se drena al principio del tick siguiente |
| Latencia de bloque del DMA de CV lento | **HUECO** | motor-digital §5 no declara el tamaño de bloque |
| Escritura y asentamiento del DAC | **HUECO** | hoja del DAC que R-M3 nombre |
| RC de reconstrucción | ≤ 100 µs | cota de abajo |

Lo conocido suma **≤ 300 µs** contra los 3 000 del objetivo: los cinco
huecos tienen 2,7 ms para repartirse, y el guion lo asevera así, con `assert`
sobre lo conocido y `HUECO` impreso sobre lo demás (código 2 de `gates.py`).
El desfase de un tick de la envolvente del filtro (§5) no entra: no es el
camino nota → VCA.

**La cota de la RC**, para el esquemático: el ataque más corto son 1 ms (§7)
y la RC no puede comérselo, así que **RC ≤ 100 µs** (un décimo del ataque
mínimo), o sea un polo a **≥ 1,6 kHz**. Ese polo deja −16 dB al escalón de
10 kHz; si el bring-up lo oye, el remedio es subir la tasa de render por
acta o un segundo polo, **nunca** bajar la RC por debajo de la cota.

**`carga_motor_budget.py` no cambia, y la cuenta se dice completa:** la fila
de 150 ciclos por muestra a 48 kHz son **720 ciclos por tick** de 10 kHz
para 32 generadores y dos escritores —**22 por generador todo incluido**:
entrada y salida de la ISR, drenar la cola, el polo, los productos, la
máscara y alimentar el DMA—. La v1 contaba solo la multiplicación y decía
«un millón de ciclos por segundo»; la fila sobrevive por el ×3 del guion, no
por esa aritmética. El bring-up la sustituye por medida (R-M2).

**El tick en el orden de NVIC** (enmienda mandada a motor-digital §7, que no
lo nombraba): va **en el escalón del DMA de audio y CV** —debajo de capturas
y J2, encima de USB y Ethernet—, porque es quien alimenta ese DMA. La fila
«primer tick ≤ 100 µs» de arriba supone que ahí no se pierde; la latencia
real de la ISR es un hueco de la tabla.

**`check_censo_voz.py` gana la fila** `ENVOLVENTE_POR_CANAL = 10` con su
cita a §7, y se corre: 696 entradas, 952 con la reserva, 58,7 % de la
memoria.

**`trama_j2_budget.py` y el #267:** los flujos de bajada declarados hacia la
Voz son tono, compuerta, evento y crosspoint. **No hay flujo de escritura de
parámetros**: nada de lo que este papel declara por voz puede llegar hoy al
N657. Es la segunda mitad del #267 (la cabecera del J2), que gana dos
clientes más: el `SET` de parámetros y el contador de eventos del bloque de
compuerta (§3.4). Hasta que exista, el generador es una biblioteca de host.

**La forma C** (tramos por DMA): si el bring-up encontrara que el tick de
10 kHz molesta a las capturas o al audio, el mismo modelo se puede servir
precalculando tramos por borde y dejando que el DMA los lleve al DAC. No es
v1 y no cambia una línea del modelo.

---

## 10. Lo que este papel NO decide

- **La escala palabra → `V_C` del VCA** (§4.3): la ley ya está (exponencial,
  −33 mV/dB, hoja en el árbol); la escala y el desplazamiento del DAC al
  puerto, y si el puerto se compensa en temperatura, son del esquemático.
  `ley_vca` se escribe cuando eso exista.
- **El DAC concreto** de los VCA (AD5686R o LTC2668-16): R-M3, hoja en árbol
  antes de dibujar.
- **El escritor de corte a 48 kHz** —el que suma base + calibración +
  envolvente + modulación y lo lleva por DMA— es su propia pieza; este papel
  le entrega `y_f` y le fija su contrato de entrada (§5).
- **La cabecera del J2** por la que llegan el evento, el bloque de compuerta
  con su contador y el `SET` de parámetros (#267). El generador se prueba con
  el borde ya decodificado.
- **Fuerza → cantidad del filtro**, y **la fuerza de `note off`**: parámetros
  nuevos, decisiones aparte.
- **Envolventes multietapa, en bucle, o invertidas** (las «mejoras» de
  `06-adsr.md`): no son v1. El modelo no las impide.
- **El valor de la RC**: solo su cota (§9).
- **El mute breve de `forzar`**: su sitio (§6), no su número. `forzar` queda
  declarada y no ejecutable.
- **La puerta y la ley de capas de la carga de un preset** sobre parámetros
  que la mano capturó: `Politica` y el cambio 12.
- **El bloque de tono y el portamento**: R-M2, del cerebro. Un generador de
  tono sigue prohibido (voz-total §3.2).

---

## 11. Riesgos, con criterio de cierre

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | El escalón de 10 kHz se oye en el VCA (RC corta) o en el corte (un polo insuficiente) | bring-up con el oído y un analizador: si se oye, acta para subir la tasa o segundo polo |
| 2 | La ley del VCA **es** exponencial (hoja en el árbol): `ley_vca` es un logaritmo por rama y por tick, y su tabla tiene que dar la resolución que el RT60 pide en −60 dB con la escala del DAC que el esquemático fije; y la constante se mueve un 0,33 %/°C si el puerto no se compensa | escala y desplazamiento del DAC al puerto en el esquemático; `ley_vca` escrita y contada en `carga_motor`; la palabra a −60 dB medida en bring-up, en frío y en caliente |
| 3 | Los 160 parámetros dejan al motor y a los gestos con 72 ranuras, o duplican perillas que los «+9/canal» ya contaban | `check_censo_voz.py` con la fila; el desglose de los 9 cuando el cambio 15 exista; si no cabe, `MAX_PARAMS` crece por acta |
| 4 | La nota reparada a fuerza plena, o sin tono de arranque, se oye como error | es degradación declarada (R-E12); se documenta en el descriptor y el manual; si molesta, la constante cambia por acta |
| 5 | Un `dispara` perdido no se repara | declarado irreparable; la cadencia de R-E11 y la fiabilidad del enlace medidas en bring-up dicen cuántos se pierden |
| 6 | El tick de 10 kHz roba a las capturas o al DMA de audio | prioridad NVIC (§9) y `carga_motor` medido; la forma C como salida |
| 7 | El contador de eventos del bloque de compuerta no cabe en la cabecera del J2, o la cadencia de R-E11 nunca se elige | #267 y R-E11; hasta entonces la red de R-E10 no tiene ancho conocido |
| 8 | La convención de −60 dB hace que las perillas «se sientan» distintas del ADSR analógico de la tesis | el oído (Principio IX); cambiar la convención es cambiar un factor, no el modelo |

---

## 12. El registro de la junta

Tres lentes sobre la v1: clínica (S, 15 hallazgos, 1 bloqueante), runtime
(H, con simulación en `f32` del barrido de tests y los guiones corridos) y
ontológica (V, con cuatro leyes). Cada hallazgo con su resolución o su
confesión. Donde los tres cazaron lo mismo, se agrupa.

| Hallazgo | Qué era | Resolución |
|---|---|---|
| **S-1 (BLOCKER), H-C2, V-5** | `dispara` contra `reafirmar`: con el bit de compuerta bajo, la red truncaba todos los tambores; con el bit alto, los resucitaba como drones. La v1 no definía el bit de un canal disparado | §3.4: la compuerta de R-E10 es una compuerta, `dispara` no la toca; cada generador lleva su compuerta propia y la red compara solo contra ella; un `dispara` perdido se declara irreparable (R-E12) |
| **S-3, H-B3, H-B4** | El fin del decaimiento por umbral relativo no termina en `f32` (11/36 casillas, incluido el `def`); con el sostenido vivo hacia 1,0, `dispara` no liberaba nunca | §2: las etapas de duración conocida terminan por cuenta de ticks con ajuste exacto; la relajación por umbral hacia cero, que es geométrica |
| **S-4, H-B5** | El re-disparo «sin clic» dejaba un escalón en la palabra: `g_v` saltaba al capturar (−36 % de escala en un tick en el ejemplo corrido) | §3.2: la continuidad se define sobre la amplitud; hacia arriba se conserva, hacia abajo baja al techo nuevo en un tick y se declara |
| **V-2** | El sostenido «en vivo» con τ_D era un suavizado dentro del módulo: R-M1 prohibido, y convertía un salto deliberado en un deslizamiento de 1,5 s | §2.3: `y = S` en el tick; el sostenido no se captura; las rampas son del cerebro |
| **S-6, V-4, H-C1** | La «última fuerza que el canal tuvo» era un estado escondido que el modelo no publica, discrepaba de la memoria de `partes.rs` (que guarda la de soltar) y podía ser la de un `cierra` a cero | §3.4: no hay memoria; una constante declarada `FUERZA_REPARACION` (decisión 12, a firmar) |
| **S-5** | Un `abre` perdido sobre un canal en relajación no se reparaba hasta que la relajación terminara (32 s con T_R = 20 s), y era el caso normal de reutilización de voz | §3.4: la red compara contra la compuerta propia, no contra la etapa; en relajación la compuerta está baja y el bit alto abre |
| **H-I2, H-I1** | El bloque de compuerta armado antes de un evento y recibido después lo contradecía en las dos direcciones: notas apagadas por un bloque viejo y notas zombi; y un `SET` puede ser adelantado por el evento en el enlace | §3.4: contador de eventos en el bloque, y se ignora el bloque viejo (requisito al #267); §3.5: el orden del enlace se acepta a la granularidad del tick y se dice |
| **H-R1, H-R2, H-R3, S-11** | Dos ISR mutando el mismo generador sin dueño: `cierra` perdido en carrera, captura con parámetros mezclados, coalescencia no declarada; la prioridad del tick no estaba en el orden de motor-digital §7; el tick leía parámetros por búsqueda binaria (la fila entera en lookups) | §3.5: el tick es el único dueño, todo lo demás encola (FIFO de 64, drenada en orden), los parámetros se empujan; §9: el tick en el escalón del DMA de audio/CV, enmienda mandada a §7 |
| **H-R4** | La barrera commitea con la máscara de un tick y el latch tarda 102 µs a 5 MHz: un `abre` en la ventana abre un canal a medio conmutar; `forzar` corre sin que nadie mutee | §6: `Commit.cambian` y retención de los `abre` sobre esos canales hasta `conmutado()`; `forzar` declarada no ejecutable en v1 |
| **V-1, S-14, H-B6, V-8b** | La «interpolación lineal» del escritor de corte exigía el tick siguiente (100 µs sin contar), dependía de una razón de relojes no entera, no era «reconstrucción», creaba la categoría implícita que motor-digital §5 prohíbe, y su costo «una suma» olvidaba la exponencial | §5: un polo de un tick en el escritor, causal, indiferente a la razón; declarado como enmienda a §5 (§14); el costo dentro de la fila del escritor de CV, que ya corre a 48 kHz |
| **S-2** | Toda la aritmética de la v1 suponía la palabra del DAC lineal en amplitud; el SSI2164 es de control exponencial y su ley no está escrita en ningún papel | §4.3: el modelo habla de amplitud; `ley_vca` es del escritor y es un hueco con contrato hasta que la hoja entre; `ley_vca(0)` cierra el VCA (§9.1) |
| **S-10, V-6** | «Silencio = palabra cero» era falso en cuanto `g_v·L ≠ 1` (y en las dos ramas), ataba un predicado de topología al ancho del DAC, y el test lo probaba por decreto | §6: silencio es «el generador de VCA está ocioso», hecho del canal; `NIVEL_OCIOSO` constante del modelo |
| **V-3, V-0** | Paneo «en vivo» por la partición nueva «forma contra sitio», sin acta, y con un escalón que la v1 prohibía para el re-disparo; sumadas las excepciones, el objeto ya no era un generador | §1: dos objetos, generador (cerrado) y escritor (vivo, por S-9); el escalón del paneo es del cerebro (R-M1); las enmiendas a §3.2 se mandan en §14 |
| **V-8a** | Se capturaba `cantidad` y nadie consumía la copia | §3.3: `cantidad` es viva, del escritor; se captura solo lo que se consume |
| **V-4b, S-8** | `reafirmar` producía un `abre` y decía no ser un evento; el watchdog de trama no tenía entrada | §3.4: tres fuentes de borde declaradas como enmienda a §3.2 (a); `soltar_todo()` y la recuperación tras la trama |
| **S-7** | El canal conducto (D-P3) tenía una envolvente que el generador no podía disparar y un silencio que la barrera esperaba en círculo | §3.1: sus bordes los emite el cerebro por el ruteo; el orden es `cierra` → silencio → commit |
| **S-9, H-C4, V-4c** | El censo omitía la reserva de 256 (952/1024, quedan 72) y los «+9/canal» no están desglosados: las 160 pueden duplicar | §7: la cuenta con reserva, la duplicación declarada indecidible hasta el cambio 15, riesgo 3 |
| **S-12, V-7c** | «Cabe» no es «direccionable»: los cambios 2 y 12 siguen bloqueantes | §7: declarado; los tests construyen el generador a mano |
| **V-7a, V-7b** | «Los valores de la parte» no existen en el modelo y su escritura no tenía puerta ni ley de capas | §7: es la carga del preset de la parte (N valores por voz); puerta y capas son de `Politica` y del cambio 12 |
| **S-13** | «1,6 × T_R» solo vale desde el pico | §2.2: la fórmula con `y₀`, y el test barre el nivel de partida |
| **S-15** | «Hoy 28,8 µs» era una cifra del bus compartido muerto | §9: retirada; solo la cota viva |
| **H-B2** | No existe flujo del J2 que lleve parámetros a la Voz | §9: declarado; segunda mitad del #267 |
| **H-B1** | El runtime del N657 no existe | §0: dicho de frente; este papel es el modelo |
| **H-C3** | «≈ 1 M ciclos/s» contaba solo la multiplicación | §9: 720 ciclos por tick, 22 por generador todo incluido; la fila sobrevive por el ×3 |
| **H-latencia** | Faltaban filas: ISR del tick, bloque del DMA lento, el desfase del filtro | §9: dos huecos nuevos en la tabla; el desfase declarado fuera del camino nota → VCA |
| **V-9** | Cuatro leyes: todo borde tiene nivel o se declara irreparable; lo capturado se consume; el silencio se define en la capa que commitea; ningún estado por canal que el modelo no lea | Las cuatro cumplidas en §3.4, §3.3, §6 y §3.4 respectivamente |

**Lo que la junta no cambió:** la forma A, la carga RC truncada, el RT60, la
fuerza lineal, el paneo a potencia constante, los rangos, la cota de la RC y
el reparto `core`/`fw`.

---

## 13. Acta del 2026-09-02: las once decisiones, y lo que la junta cambió

Firmadas por Samuel en sesión, sobre la propuesta en cristiano, con una
palabra: *«firmo»*. La columna de la derecha dice qué queda igual y qué
cambió de mecanismo por la junta; **lo marcado con ⚠ se vuelve a firmar en el
PR**.

| # | Decisión | Firmado (v1) | Tras la junta (v2) |
|---|---|---|---|
| 1 | Forma del ataque | Carga RC truncada al pico, como el 7555 de la tesis | Igual; termina por cuenta de ticks (§2.1) |
| 2 | Qué mide «tiempo» en decaimiento y relajación | Tiempo hasta −60 dB del recorrido | ⚠ Igual convención; el **fin del decaimiento es por cuenta de ticks**, no por umbral (§2.2) |
| 3 | `dispara` | Ataque → decaimiento → relajación al llegar al sostenido | Igual; y **no levanta la compuerta** (§3.1) |
| 4 | Re-disparo | Desde el nivel actual, nunca desde cero | ⚠ La continuidad se define **sobre la amplitud**; hacia abajo baja al techo nuevo en un tick, declarado (§3.2) |
| 5 | La fuerza | `(1 − s) + s·v`; la de `note off` no se usa | Igual (§4.1) |
| 6 | El paneo | Potencia constante, en vivo | Igual; vive en el **escritor**, y su escalón es del cerebro (§4.2) |
| 7 | La envolvente del filtro | Octavas; reconstrucción lineal al escribir a 48 kHz | ⚠ Octavas; **un polo de un tick en el escritor**, declarado como enmienda a motor-digital §5 (§5, §14) |
| 8 | Silencio | Cuando la envolvente baja de 1 LSB de 16 bits | ⚠ **Cuando el generador de VCA está ocioso**, con `NIVEL_OCIOSO` como constante del modelo (§6) |
| 9 | La red de R-E10 | Abierta y ocioso → abre con la última fuerza; cerrada y sonando → cierra | ⚠ Compara contra la **compuerta propia**; `dispara` invisible e irreparable; **fuerza de reparación constante**; contador de eventos en el bloque (§3.4) |
| 10 | Dónde viven los parámetros | Por voz, 160 entradas; cabe en 1024 | ⚠ Por voz, 160 entradas; **952 de 1024 con la reserva, quedan 72** para motor y gestos (§7) |
| 11 | Rangos | A y D 1–10 000 ms, R 1–20 000 ms, S 0–1 000 ‰, sensibilidad 0–1 000 ‰, cantidad ±4 800 cents | Igual (§7) |

**Las que nacen con la v2, a firmar:**

| # | Decisión | Propuesta |
|---|---|---|
| 12 | La fuerza de una nota reparada | `FUERZA_REPARACION = u16::MAX` (plena): una nota reparada tiene que oírse (§3.4) |
| 13 | `dispara` y la red | Un `dispara` perdido es un golpe perdido: irreparable, declarado (§3.4) |
| 14 | Un solo dueño del estado | El tick muta; todo lo demás encola en una FIFO de 64 drenada en orden (§3.5) |
| 15 | La ley del VCA | El modelo habla de amplitud; `ley_vca` es del escritor; la hoja del SSI2164 entró el mismo día y fija la ley (exponencial, −33 mV/dB, unidad a 0 V, −100 dB a +3,3 V); lo que espera al esquemático es la escala del DAC al puerto; `ley_vca(0)` cierra el VCA (§4.3) |

Y la decisión previa que las precede: **el generador vive en el N657 de la
Voz**, no en un chip aparte (§0).

---

## 14. El mapa de enmiendas (mandadas, no hechas)

La v1 enmendaba tres papeles sin decirlo; la lente ontológica lo llamó
«enmiendas ni siquiera mandadas». Aquí están, con dueño:

| Papel o guion | Sección | Qué cambia | Dueño | Estado |
|---|---|---|---|---|
| `2026-08-23-modulo-voz-total-design.md` | §3.2 (a) | El generador se dispara por tres fuentes: evento, reafirmación de compuerta y watchdog de trama | el PR de este papel | **aplicada** 2026-09-02, mismo PR que el plan |
| ídem | §3.2 | Nace la categoría **escritor** al lado del generador: consume parámetros vivos por S-9 y no es un generador | el PR de este papel | **aplicada** 2026-09-02, mismo PR que el plan |
| `2026-08-26-motor-digital-design.md` | §5 | Cláusula del suavizado: una fuente lenta puede alimentar un destino rápido a través de un polo de un tick en el escritor; la fuente sigue lenta | el PR de este papel | **aplicada** 2026-09-02, mismo PR que el plan |
| ídem | §7 | El tick de envolventes entra al orden de NVIC en el escalón del DMA de audio y CV | el PR de este papel | **aplicada** 2026-09-02, mismo PR que el plan |
| `2026-08-25-evento-de-nota-design.md` | D6 / R-E10 | La máscara de compuerta es de compuertas (`abre`/`cierra`), nunca de disparos; lleva el contador de eventos emitidos; `dispara` queda sin red (R-E12) | el PR de este papel | **aplicada** 2026-09-02, mismo PR que el plan |
| ídem | D7 / R-E12 | La nota reparada entra con `FUERZA_REPARACION`, constante, y sin tono de arranque | el PR de este papel | **aplicada** 2026-09-02, mismo PR que el plan |
| `software/nucleo/core/src/bahia.rs` | `Commit`, `PoliticaDrones` | `Commit` gana `cambian`; `forzar` se documenta como no ejecutable en v1 | el PR de código | pendiente |
| `hardware/03-vco/check_censo_voz.py` | censo | Fila `ENVOLVENTE_POR_CANAL = 10` | el PR de código | pendiente |
| `hardware/02-midi-cv/trama_j2_budget.py` | flujos de bajada | Falta el flujo de `SET` de parámetros hacia la Voz | #267 | pendiente |
| Issue #267 | — | La cabecera del J2 gana dos clientes: el `SET` de parámetros y el contador de eventos en el bloque de compuerta | comentario en el issue | **aplicada** (comentario del 2026-09-02) |
| `ataque_budget.py` | — | Nace con las filas de §9 | el PR de código | pendiente |
