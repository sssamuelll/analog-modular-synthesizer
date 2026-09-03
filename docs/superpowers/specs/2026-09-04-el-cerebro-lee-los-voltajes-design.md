# El mux se muda al cerebro, el CV externo entra por digital, y el jack se nombra en la pantalla: son la misma decisión

**Fecha**: 2026-09-04 · **Estado**: **v2, pasó la junta, a firma** ·
**Sujeto**: quién lee los voltajes del instrumento y quién decide qué significan ·
**Cierra**: #301, #302 · **Contesta el censo mandado en** motor-digital §8.4 punto 4 ·
**Cuelga de**: el retiro de la cadena (2026-09-03, #300), la bahía asignable
(voz-total §5.1), el hub N657 (2026-08-30), la gramática del panel (2026-08-23)

---

## 0. Qué es este papel, y qué no

El 2026-09-03 por la noche Samuel contestó las dos preguntas que #300 dejó
abiertas y abrió una tercera. Este papel las trata **como una sola**, porque lo
son.

Sus palabras, enteras, que son el acta:

> *«el mux de perillas debe vivir en el cerebro. hay perillas de controles fijos
> y hay otras que van a ser configurables entre parametros, incluso podria
> configurar mover varios parametros con una sola perilla pero todo en
> configuracion. todo altamente configurable y las que se quedan fijas serian
> como muy clasicas no?»*

> *«con respecto a la 302 se muda a la pantalla y tiene que ver un poco con 301»*

> *«pero tambien quiero poder conectarle al sinte entradas de CV y salidas
> tambien (podria ser un patch bay configurable? que yo pueda seleccionar por que
> salida sale que y en ese caso el de patch bay, tendria sentido lo de los leds
> para indicar que jack esta activado y el color define que es (la pantalla le
> indicaria al usuario) :D de esa forma puedo mantener (no toda la barbaridad de
> leds pero si algunos cuantos y no necesito tener 32 o 64 jacks de cv in out etc
> que se yo»*

**Lo que NO es:**

- **No diseña la interfaz de audio.** Los «juguetes» que Samuel nombró —USB,
  MIDI, mic in, instrumentos, salidas de master— **ya tienen papel escrito desde
  el 2026-08-31**, `2026-08-31-interfaz-audio-design.md`, y está *propuesto,
  pendiente de Samuel* con su prerrequisito duro sin cerrar (#256). Este papel
  no lo reabre ni lo duplica: lo señala en §5 y sigue.
- **No dibuja el panel del valle.** Da su cota y su costo (§2.8) y deja el dibujo
  a quien lo esté haciendo.
- **No elige la pieza del driver de LED.** Es #297, y sigue suyo.
- **No reabre el retiro de la cadena.** #300 se sostiene entero: lo que vuelve
  no es la cadena, y §2.6 dice por qué no es lo mismo.
- **No decide el reparto de pines del hub.** El censo dice que cabe; el nombre
  de cada pin es de otra tanda (#301 lo hereda).

---

## 1. En qué se parecen las tres preguntas, y en qué NO — corregido por la junta

> **La v1 de este papel decía que las tres preguntas «eran una» y derivaba las
> decisiones de esa tesis. Voronov lo tumbó y tiene razón: D1, D5 y D6 las
> decidió Samuel, y D3 la decide un conteo. La tesis se escribió después,
> encima de habitaciones ya construidas. Una tesis que no carga peso no es una
> tesis; es un título. Esta sección dice lo que sí es verdad y hasta dónde.**

Las tres cosas se parecen **en el sustrato** y **en el mecanismo de
significado**, y no se parecen **en el gobierno**. Los tres niveles hay que
separarlos porque el papel se juega en el tercero.

**Se parecen en el sustrato.** Una perilla es un voltaje que mueve una mano;
una entrada de CV es un voltaje que mueve otra máquina. El ADC no las
distingue. El repo ya las tenía compartiendo encapsulado — VCO-16 §7.1, líneas
558-559:

> *«un multiplexor analógico 16:1 por micro, a una sola entrada de ADC. Ocho
> canales para las entradas de control, ocho reservados para perillas.»*

Y conviene leer esa frase con cuidado, porque la v1 la forzó: **son dos bloques
de ocho compartiendo cápsula, no una población.** Compartir cápsula no es
compartir naturaleza, y D2 —la decisión siguiente— las vuelve a separar.

**Se parecen en que su significado está en una tabla.** Pero esa familia es más
ancha que los voltajes, y tiene un miembro firmado que no es uno: el mago. El
papel del hub §3.2 dice que sus gestos *«entran al modelo como fuentes (decenas
de floats a 30-60 Hz)»* y que *«el mapeo sigue siendo estado del modelo»*. Sin
ADC, sin mux y sin que el cerebro lea nada.

**Y NO se parecen en el gobierno, que es de lo que va este papel.** El salto de
«comparten sustrato» a «comparten dueño» necesita una premisa que el repo niega
tres veces: *quien lee, posee*. La niega D2 doce líneas más abajo (el módulo lee
la ocupación y el hecho gobierna en el cerebro); la niega el mago; y la niega el
propio crosspoint, cuya imagen es del cerebro y cuya ejecución es de la Voz.

**La corrección que manda, y es de la ley fundacional.** `voz-total` §0.2,
primera línea de la legislación:

> ***El patch vive y corre en el cerebro y los módulos, siempre.***

Así que *«el modelo vive en el cerebro»* es falso tal cual, y lo verdadero es
más flojo y más útil:

> **El cerebro posee la INTENCIÓN del significado. El módulo posee si está EN
> VIGOR.**

Y no es matiz: bajo `diferir`, con un drone sonando, existe hoy en el árbol un
estado —*«ruta pendiente»*— que dice qué significa un jack ahora mismo y **que
el cerebro no tiene**, sin cota de tiempo y por diseño, con test verde
(`core/tests/bahia.rs`).

**Lo que sí se sostiene, y es lo que carga las decisiones:** el mapa de un
mando a lo que gobierna es estado del modelo autoritativo, y por tanto no puede
ser propiedad privada de un módulo que no lo conoce. Eso basta para D1 y no
necesita ninguna tesis sobre voltajes.

---

## 2. Las decisiones

### D1. El mux de perillas se muda al cerebro

**Decidido por Samuel el 2026-09-03.** Este papel escribe el argumento, porque
lo que se hereda en este repo es el argumento y no la conclusión.

**Lo que se deroga.** `nucleo-digital` §10, línea 1277:

> *«**El mux de perillas vive en el módulo**, no en el cerebro (esto cierra una
> ambigüedad de `architecture-poly.md` §7)»*

Y su origen, `architecture-poly.md` §7, líneas 383-393:

> *«**Y ese mux vive EN EL MÓDULO, no en el cerebro** (decidido 2026-08-17; antes
> esto quedaba ambiguo aquí). Las lecturas vuelven por el `MISO` que el J2 ya
> lleva, así que no hace falta ni un hilo nuevo.*
>
> *No es una preferencia de reparto: es lo que hace posible el patcheo guiado de
> abajo. Si las entradas de CV son legibles por ADC **en el propio módulo**, el
> cerebro puede mover una fuente y ver **qué entrada se movió** — y de ahí sale la
> topología del patch. Con el mux en el cerebro, esa información no existe.*
>
> *Por eso los jacks de CV patcheables **también** cuelgan del mux, no solo las
> perillas.»*

**Cuatro razones, en orden de peso:**

**1. Una perilla configurable no tiene módulo.** Es el argumento de Samuel y es
el que decide. Si la perilla 7 puede ser el corte del VCF hoy y la velocidad del
LFO mañana —o las dos a la vez— entonces **ningún módulo la posee**, y un mux
que vive en un módulo la está leyendo en nombre de un dueño que no existe. La
perilla pasa a ser superficie del instrumento, no del módulo.

**2. Las perillas no están en los módulos, y no lo han estado nunca.** Las 20
perillas del SAM17 viven en la fila A (`panel-frontal-gramatica.md` §4,
línea 114-115): 4 MACROS en cuadro 2×2 y 16 potes curados en 8×2. El propio
núcleo lo dice de pasada, línea 1285, hablando del módulo 5:

> *«aunque las perillas del panel sigan siendo comunes»*

**Las perillas del panel.** El §10 le mandaba a los módulos 5, 6 y 7 alojar el
mux de unas perillas que están en un panel que ellos no tienen. Y el módulo que
sí llegó a dibujarlo lo dejó vacío — VCO-16 §7.1, tabla de la línea 571: *«Sitio
para perillas: 8 canales por columna»*, **reservados**. Nunca se cableó ninguno.

**3. La razón que lo puso ahí murió el 2026-09-03.** La cadena de §6.2, líneas
856-858:

> *«Para la captura automática de verdad hace falta que el cerebro mueva una
> fuente a un valor único y vea **qué entrada se movió**. Eso exige que cada
> entrada de CV patcheable sea **legible por ADC**, lo que a su vez fija que el
> mux de perillas viva **en el módulo** y devuelva por el `MISO` del J2.»*

Esa inferencia tenía un salto **ya en su día**: de «las entradas de CV tienen que
ser legibles por ADC» no se sigue «el mux **de perillas** vive en el módulo».
Se seguía solo porque un mismo mux servía a las dos poblaciones por economía.
Derogado el patcheo guiado (#300 D3), la premisa se cae y el salto queda a la
vista.

**4. El impedimento que forzaba la alternativa ya no existe.** La gramática del
panel propuso el 2026-08-23 una tercera vía —el panel como módulo propio, con su
micro y su bajada de J2— y dijo por qué, §11.2, líneas 268-274:

> *«el cerebro está cerrado por escrito (2 GPIO libres, dos SPI gastados, «no
> admite un cliente más» en J2 desde su spec §7… pero **E-3 liberó una ranura de
> J2** al fundir la bahía en la Voz). Propuesta: **el panel de mandos se vuelve
> módulo de verdad** — clase referente, su propia bajada de J2 en la ranura
> liberada, su micro, su escaneo de 45 potes (3 muxes 16:1), su renglón, sus
> coronas y su presupuesto de +5 V.»*

**Ese cerebro era el RP2350.** El de hoy es el N657.

> **Corrección propia (Principio VII), cazada por Voronov.** La v1 de este papel
> decía aquí *«80 GPIO libres, +54 tras lo vario — y «mux» ya está contado entre
> lo vario»*. **Era falso.** El único «mux» que `micro_budget.py` contaba es
> este, línea 1150:
>
> ```python
>                    + 1)                    # RESET del mux I2C
> ```
>
> Un pin, para el **RESET de un multiplexor de bus I²C** del árbol de
> descubrimiento. Otro objeto con el mismo nombre. Y la cuenta no era una
> nimiedad: un barrido analógico de 20 potes no cuesta un GPIO, cuesta líneas de
> dirección **más una entrada con ADC**, que es un pool más escaso — cosa que
> este mismo papel concede en su riesgo 3 para el CV y no había aplicado a la
> población que acababa de mudar.

**Se sentó de verdad y se corrió.** `micro_budget.py` ahora cobra el mux de
perillas: **6 GPIO** (4 líneas de dirección compartidas + 2 enables, para dos
CD74HC4067 que cubren los 20 potes de la fila A) y **una entrada de ADC** en la
mesa, junto a las tres que ya había (`ADC:oidos-rapidos`,
`ADC:reserva-issue213`, `ADC:pedal`). Corrido el 2026-09-04:

| Escenario | VFBGA264 | VFBGA223 |
|---|---|---|
| base | VERDE, 80 libres, **+48 tras lo vario** | VERDE, +27 |
| + audio | VERDE, +43 | VERDE, +22 |
| + RGMII | VERDE, +33 | VERDE, +12 |
| + audio + RGMII | VERDE, **+28** | VERDE, **+7** |

**Cabe, y el reparto encontró pin para la entrada de ADC.** El argumento de
escasez que forzaba la propuesta del panel-como-módulo está muerto por cambio
de chip — pero ahora está muerto *con la cuenta hecha*, no por analogía. La cifra
honesta es **+48**, no +54, y el 223 en el peor escenario baja a +7: si alguien
quiere el encapsulado pequeño, el mux de perillas es de lo que hay que hablar.

**Dónde vive el silicio, dicho con precisión.** «El mux vive en el cerebro» es
una decisión de **propiedad**, no de centímetros. El cerebro pone el ADC, las
líneas de dirección y la tabla. No hay micro nuevo, no hay ranura de J2 nueva.

**Los chips de mux deben ir junto a los potes**, para que lo que viaje al
cerebro sean una línea de ADC y cuatro de dirección, y no veinte cursores.

> **HUECO, y Serrano tiene razón en marcarlo.** La v1 daba por escrito que los
> potes son *board-mount* citando `panel-frontal-gramatica` §4. **Esa cita no
> dice eso.** Su frase entera, líneas 135-137:
>
> > *«**Rebaje trasero fresado Ø12×3 mm en cada pote y cada jack**: un
> > Thonkiconn tiene 4,7 mm de casquillo — **en 5 mm no rosca** (−0,3 mm). El
> > proceso ya es CNC; el rebaje es tiempo de máquina, no utillaje.»*
>
> Es una cota de montaje **al panel**, porque el acrílico de 5 mm es más grueso
> que el casquillo roscado. Si acaso apunta a casquillo y tuerca, que es lo
> contrario de board-mount.
>
> **Que los 20 potes de la fila A vayan sobre una placa no está escrito en
> ningún papel**, y de eso depende el tamaño del riesgo 1: con placa, el
> analógico son milímetros; sin ella, hay veinte cables de cursor hasta donde
> esté el mux. **Es prerrequisito de dibujar el panel**, y es del papel del
> panel, no de éste.

**Y rompe un invariante escrito, que hay que enmendar en voz alta.**
`architecture-poly.md` §8, líneas 520-523, dice:

> *«**Por el mismo enlace vuelven las lecturas.** El `MISO` del J2 no es
> decorativo: por ahí regresan el mux de perillas, el sensado de ocupación de
> los jacks y —en el módulo 4— las medidas del análisis de audio. **El cerebro
> nunca recibe voltajes, ni siquiera para oír.**»*

Con D1 esa última frase **deja de ser verdad**, y es una frase con peso: es la
misma doctrina que puso los DAC en los módulos (*«por el cableado viajan
números, no voltajes»*). La enmienda no la borra, la acota:

> **El cerebro no recibe voltajes de SEÑAL. Recibe el barrido de sus propios
> mandos, que es medida de una mano, no camino de audio ni de tono.**

Y la distinción tiene número: en el expo de la Voz **1 mV son 3,6 cents**
(voz-total E-1), y por eso ningún CV de tono cruza el mazo. En una perilla, 1 mV
es menos de un LSB de ruido sobre un mando humano, y el instrumento ya exige un
umbral con histéresis para ese ruido (riesgo 1). **No es la misma clase de
voltaje**, y por eso la excepción es estrecha y no una grieta.

> **Lo que se pierde y hay que decirlo:** el dominio de fallo que §11.2 ofrecía
> —*«pantalla muerta ≠ perillas muertas, y el camino nota→VCA del cerebro ni se
> entera»*— **desaparece**. Con D1, un cerebro colgado se lleva las perillas con
> él. Es un costo real. Se acepta porque el mismo cerebro ya es dueño del J2, y
> un cerebro colgado ya deja el instrumento sin voces a los ~50 ms
> (`2026-09-03-maestro-j2-recuperacion-design.md`): las perillas no eran una
> segunda vida, eran un consuelo.

### D2. Lo que NO se muda: la auditoría de las entradas de control

**Las 8 entradas de control del VCO-16 se quedan en el módulo.** Samuel dijo «el
mux **de perillas**», y la distinción es exactamente la que el VCO-16 ya había
escrito, §7.1 líneas 561-565:

> *«**la lectura por ADC de una entrada de control es auditoría, no camino de
> señal.** El CV del jack llega al oscilador por cobre, a través de `R_CVIN`, en
> hardware. Lo que el ADC hace es enterarse de qué hay ahí, para el barrido por
> inyección y para la ocupación de §6.3. Unos cientos de hercios sobran, que es
> justo lo que `architecture-poly.md` §7 ya dice del mux de perillas.»*

> **Corrección propia (Principio VII), cazada por Serrano.** La v1 decía aquí
> que *«mudar esto al cerebro rompería `perturbacion.rs`»* y salvaba el ADC
> citando **la ocupación**. Las dos cosas están mal:
>
> 1. **`perturbacion.rs` no se rompe.** Es cómputo puro sobre muestras
>    (`heapless::Vec`, cero E/S) y **ya corre en el cerebro**. Mover el ADC no
>    lo toca: cambia quién le entrega las muestras.
> 2. **La ocupación no usa el ADC.** `nucleo-digital` §6.2, líneas 848-849:
>    *«**Ocupación (sensado simple).** Un registro de desplazamiento por módulo
>    lee qué jacks tienen cable.»* Un registro de desplazamiento, no un
>    convertidor.
>
> El cliente vivo del ADC del módulo es **otro**, y está escrito en el propio
> código — `core/src/perturbacion.rs`, líneas 18-19:
>
> > *«Un `Correlador` por **punto de observacion** (cada entrada de CV legible
> > por ADC). Todas las fuentes se perturban a la vez.»*

De los dos clientes que la frase del VCO-16 nombra, **uno murió** (el patcheo
guiado como destino, #300 D3) y **el otro vive**: el correlador de la
atribución (§7.2/§7.6), que sigue necesitando **un punto de observación por
entrada de CV**, y esos puntos están en el módulo.

**Lo que de verdad se rompería al mudarlo** no es el Rust: es el cobre. El
correlador necesita observar cada entrada de CV patcheable; con el ADC en el
cerebro habría que llevarle ocho señales analógicas por módulo, que es
exactamente lo que la doctrina de §8 prohíbe. **Por eso no se muda**, y la razón
es de mazo, no de software.

Con ello se contesta la pregunta que #301 dejó abierta —«la lectura por ADC
pierde su justificación escrita y hay que volver a darle una o retirarla»—:

> **La justificación nueva de que toda entrada de CV patcheable sea legible por
> ADC no es la topología del patch: es que la frontera con el mundo es el único
> sitio del instrumento cuyo estado el cerebro no conoce por haberlo escrito él.**
> Dentro, el cerebro programó el crosspoint y sabe la topología sin medirla.
> Fuera, alguien enchufa un cable y el instrumento se entera o no se entera.

**Consecuencia de reparto, que sale gratis:** el mux del VCO-16 pasa de 8+8 a
**8 canales usados de 16**. Los 8 reservados para perillas quedan libres para lo
que el módulo necesite, o para bajar de pieza. Es el único ahorro material de
esta tanda y conviene no gastarlo sin motivo.

### D3. Una entrada de CV externa es una perilla que no giras tú

**El CV externo que gobierna un parámetro entra por el camino digital, no por el
crosspoint.** ADC en la entrada → mapeo en el cerebro → el DAC que ese parámetro
ya tiene en su módulo.

**Por qué no por el crosspoint: porque no cabe, y el número es cero.** El censo
que motor-digital §8.4 mandó el 2026-08-26 y que nadie corrió en ocho días está
corrido — `hardware/03-vco/bahia_budget.py`:

| Lado | Ocupado | Libre |
|---|---|---|
| A.X — del mundo hacia las voces | 10/16 (8 jacks + boca del códec) | 6 |
| **A.Y — los nodos de suma** | **16/16** | **0** |
| **B.X — las salidas post-VCA** | **16/16** | **0** |
| B.Y — de las voces hacia el mundo | 9/16 (8 jacks + oídos) | 7 |

Un parámetro que quiera recibir CV externo por vía analógica necesita un destino
en **A.Y**, y A.Y son los 16 nodos de suma de los 16 canales. No queda poco:
queda **cero**, y queda cero mientras haya 16 canales y dos chips de 16×16.

**Por qué el camino digital es mejor, y no un consuelo.** El instrumento ya tiene
un DAC por parámetro en cada módulo (`architecture-poly.md` §8: *«cada módulo
lleva los DAC — y digipots — de sus propios parámetros»*). Con eso, una entrada
de CV digitalizada puede hacer lo que un cruce analógico **no sabe hacer**:

- gobernar **varios parámetros a la vez** con escala y offset propios por
  destino — que es literalmente lo que Samuel pidió para las perillas
  (*«podria configurar mover varios parametros con una sola perilla»*);
- llevar **curva** (exponencial, cuantizada a semitonos, con zona muerta);
- ser **guardada en el preset**, porque es una tabla y no un cable;
- y **no gastar ni un cruce** del crosspoint, que se reserva entero para lo que
  solo él puede hacer.

**Y el precio, dicho antes de que alguien lo descubra montando.** La auditoría
del VCO-16 corre a *«unos cientos de hercios»* (§7.1). Eso vale para saber que
hay un cable; **no vale para modular**. Una entrada de CV que gobierne un
parámetro musicalmente necesita su tasa, y el instrumento ya tiene la ley que lo
gobierna — motor-digital §5, la ley de dos tasas: *«los **destinos rápidos**
rinden a **48 kHz**; los demás siguen a **10 kHz**»*.

**Decisión: una entrada de CV declara su clase de tasa, igual que un destino.**
No es concepto nuevo: es la ley que ya existe aplicada a una población nueva.

- **Clase lenta** (cientos de Hz): pedal, expresión, offsets, LFO lento externo,
  seguidor de envolvente. **Barata**: cabe en un mux compartido.
- **Clase rápida** (la de motor-digital §5): FM, audio-rate. **Cara**: pide su
  camino de ADC.

> **HUECO, y es el que decide cuántos jacks se compran.** Cuántas entradas de
> cada clase, con qué ADC y en qué pin, **no lo fija este papel**: sale del censo
> de pines del hub con esta población dentro, que es trabajo de #301. Lo que sí
> queda fijado es la ley: **una entrada sin clase de tasa declarada no se
> dibuja.**

### D3bis. Un CV externo no es una mano — y sin esto, D3 no se puede construir

**Éste es el hallazgo más caro de la junta, y es un bloqueo, no un matiz.**

La ley de capas de `voz-total` §0.2, ley 1, dice:

> *«**La mano gana por parámetro.** Un gesto físico (perilla, cable en la
> bahía) captura ese parámetro o ruta: la automatización del agente sobre él
> queda `ANULADO` (el primitivo del núcleo §4.1, extendido: el agente es una
> fuente de automatización más). Todo lo demás sigue bajo el agente.
> `REACTIVAR` lo devuelve. Es touch/latch de DAW, hecho instrumento.»*

Y la autoría **la estampa el transporte** (`nucleo-autoria-y-politica` §2):
un mensaje que declara su propio origen puede mentir gratis; lo único honesto es
por dónde entró.

**Voronov encontró que D1 y D3, juntos, rompen eso.** Si la perilla y la entrada
de CV comparten mux, ADC y chip, **el transporte deja de poder distinguirlas** —
no «todavía no está implementado», sino que no puede, por construcción. Y si
además *«una entrada de CV es una perilla que no giras tú»*, entonces **enchufar
un cable anula al agente para siempre**, porque un CV no suelta: no hay fin de
gesto contra el que `REACTIVAR` pueda pelear.

**La salida, y está en la propia ley.** La ley nombra dos gestos, y no son la
misma cosa:

| Gesto | Qué captura | Cómo termina |
|---|---|---|
| **perilla** | un **parámetro** | sueltas la mano |
| **cable en la bahía** | una **ruta** | sacas el cable |

Un cable no captura un valor: captura **una ruta**, que es un estado discreto,
no una magnitud continua. Por eso enchufar no anula a nadie sobre un parámetro.
De ahí la decisión:

> **Una entrada de CV externa NO captura bajo la ley de capas. Enchufar declara
> una FUENTE disponible; asignarla a un parámetro es un acto de configuración,
> y ese acto sí tiene autor.**

Con eso, el CV compite con el agente como compite cualquier automatización —
con un autor identificable— y no como una mano que nunca suelta.

**Y las dos cosas que eso exige, que hoy no existen:**

1. **`Puerta` necesita un valor que no sea `Mano`** para el CV externo. Hoy
   `Puerta` **no existe en Rust** (`panel-frontal-gramatica` §5.1, estado del
   prerrequisito, 2026-08-24: *«`Puerta` **no existe en Rust**»*), y son las
   ocho decisiones N1-N8 que esperan a Samuel en **#177**.
2. **La mitad «ruta» de la ley de capas no existe en el modelo.** Lo dijo la
   junta del panel como condición 3 de MATRIZ: *«**`ANULADO` con tipo de
   arista**: la ley de capas promete "ese parámetro o ruta" y la mitad "ruta" no
   existe en el modelo»*.

**Lo que la clase de un canal SÍ resuelve, y es lo que salva «la autoría la
estampa el transporte».** El transporte no es «el ADC»: es **qué canal del
mux**. Y la clase de un canal la fija el cobre, no el preset — un canal cableado
a un pote es `Mano` y uno cableado a un jack es externo, y cambiarlo pide un
soldador. **Esa tabla es constante de placa, nunca configuración**, y así la
promesa de #177 sobrevive a D1.

> **Regla, y es dura:** el mapa canal-de-mux → clase de autor vive junto al
> pinout, con el resto de lo que fija el cobre. Si alguna vez un preset puede
> cambiarlo, la ley de capas deja de ser una ley y pasa a ser un valor por
> defecto que la configuración apaga — que es exactamente la condición que #177
> se abrió para eliminar.

**Estado honesto de D3, entonces:** la dirección es correcta y el camino digital
es el bueno. **Pero un CV externo no se cablea a un parámetro hasta que #177
cierre**, porque hasta entonces el instrumento no sabe decir quién escribió. Es
prerrequisito, no adorno, y ordena la cola: **#177 antes que el dimensionado de
las entradas de CV.**

### D4. El crosspoint es para audio, y ahora la frontera está en números

De D3 sale la frontera, y conviene escribirla como regla porque hasta hoy era
prosa:

> **El crosspoint mueve señal de audio entre el mundo y las voces. Un parámetro
> se gobierna por número.**

`bahia_budget.py` la asevera: si alguien libera un destino en A.Y, el guion
salta y obliga a **re-argumentar la frontera en vez de heredarla**.

**Lo que el censo contestó de paso, y llevaba ocho días mandado:** las dos
enmiendas del 2026-08-26 —la boca del códec como fuente (D-P1) y los oídos
ruteables como destino (D-P4)— **caben las dos, sin quitarle un jack a nadie**,
incluso con los oídos en estéreo. El *fallback* que D-P1 se había declarado
(*«si el censo del crosspoint da rojo... la boca entra directo al bus del
mixer»*) **no hace falta**, y el patcheo del audio digital se queda.

**Y una consecuencia de la topología, que la v1 presentó mal:** una señal que
entra por A.X solo llega a un nodo de suma; para salir al mundo tiene que
atravesar un canal de voz.

> **Corrección propia, cazada por Voronov.** La v1 lo llamaba *«hallazgo»* y
> decía *«la bahía no sabe hacer de puente»*. **Sí sabe, y está firmado**:
> `voz-total` §0.3 legisla el rol **`conducto`** — línea 143:
>
> > *«Su oscilador está silenciado y hay señal externa activa en su nodo de
> > suma: suena **lo externo** por su filtro y su VCA. El caso DJ: mandar una voz
> > a un pedal y devolverla por el canal de otro»*
>
> Es exactamente el puente, **a través de un canal**, con su caso de uso
> nombrado y su costo contado (`conducto` sale del reparto de notas: cada canal
> prestado es una voz analógica menos). Lo que la v1 encontró como limitación
> era una función con acta. Lo único cierto que queda es que **no hay múltiple
> pasivo**: no se puede sacar la misma señal por dos jacks sin gastar un canal.

**Y una honestidad sobre el rango de esta frontera**, que también es de Voronov:
la frontera está enunciada como afirmación de **tipo** («audio contra
parámetro») y su evidencia es un hecho de **cardinalidad** (A.Y tiene 16 nodos y
16 canales). Hoy coinciden; nada garantiza que coincidan con un tercer AD75019 o
con otro cableado. **Se declara así:**

> La frontera **no se sostiene en la ontología, se sostiene en el conteo** — y
> por eso el aserto de `bahia_budget.py` la vigila. Lo que sí es independiente
> del conteo son las cuatro ventajas de D3 (varios destinos por fuente, curva,
> cabe en el preset, no gasta cruces): **ésas sobrevivirían a un tercer chip**, y
> son la razón de mérito. La cardinalidad es la razón de urgencia.

Y el propio `conducto` se sienta en la costura: ahí un parámetro (el corte)
gobierna audio externo dentro de un canal. La línea audio-contra-parámetro no
corta por donde la frase sugiere, y conviene que quede dicho antes de que
alguien la cite como ley.

> **Marcado como lectura, no como hecho.** La topología A/B sale de leer
> `voz-total` §5.1 (*«entradas → los 16 nodos de suma; las 16 salidas post-VCA →
> salidas»*), que es la única lectura que cierra con 16 voces y dos chips de
> 16×16. **No hay esquemático.** Si el cobre los cablea de otro modo, el guion se
> rehace — y su cabecera lo dice.

### D5. El nombre del jack vive en la pantalla

**Decidido por Samuel el 2026-09-03**, cerrando la mitad de #302: *«con respecto
a la 302 se muda a la pantalla»*.

Lo que se deroga es media frase de `voz-total` §5.1, línea 442-443:

> *«El jack es un nombre que le da el preset; su LED dice en color qué es.»*

La primera mitad se sostiene y es lo que hace falta salvar: **el jack es un
nombre que le da el preset.** Lo que cambia es quién lo dice: la pantalla de 7",
no un color.

Y la superficie ya existe sin gastar nada nuevo: `panel-frontal-gramatica.md` §4
línea 118 le da a la bahía *«ventana propia de 68×16 (nombre de cada jack)»*.
Esa ventana no muere — pasa de ser una franja de frente muerto propia a ser lo
que la 7" ya hace por el resto del panel.

### D6. La luz vuelve, acotada, y solo para lo que una pantalla no puede hacer

Samuel lo pidió y tiene razón, con la frase exacta que resuelve #302:

> *«los leds para indicar que jack esta activado y el color define que es (la
> pantalla le indicaria al usuario)»*

Eso es **exactamente** el reparto que la junta de #300 nombró y que aquel papel
dejó aparcado en su §6.1:

| | Qué lleva | Dónde vive |
|---|---|---|
| **Deixis** | *ese* jack, ahí, está activo; de qué clase es | **LED**, porque una pantalla puede *describir* un sitio y no puede *estar* en él |
| **Estado** | qué es exactamente, cómo se llama, a qué está ruteado, cuánto vale | **Pantalla**, que lo hace mejor |

**Esto SÍ enmienda a #300, y hay que decirlo así.** La v1 decía *«no reabre
#300»*; es falso, y Serrano lo cazó. #300 D9, línea 304, sobre estos mismos 16
jacks:

> *«**Se queda**, acotado a los 16 jacks de la bahía —que voz-total §5.1 ya lo
> había restringido—, y **sin LED**: el sensado es un hecho que entra al modelo,
> no una luz.»*

D6 pone luz exactamente donde aquella frase dice «sin LED». **Es una enmienda a
un papel firmado hace un día, decidida por Samuel, y va con su nombre** (§6). Lo
que no puede ser es firmarla diciendo que no toca nada.

La diferencia con la cadena es material, no de grado, y eso sigue en pie:

| | La cadena retirada | Lo que vuelve |
|---|---|---|
| Cuántos | **160 = 100 de panel + 60 del farol del #42** | **16**, los jacks de la bahía |
| Dónde | todos los paneles, más el interior del case | **una fila** |
| Cómo | mazo propio de 3 hilos atravesando cada módulo | driver por bus serie, local (#297) |
| Qué mata | competía con el audio y con el J2 (#297), y con el riel de +5 V (#104) | local a su placa |
| Qué hace | estado *y* deixis, mezclados | **un bit de deixis**, más color (ver abajo) |

**La cuenta, corregida.** La v1 decía *«16 contra ~160: un 10 %»* y describía
los 160 como *«uno por perilla y por jack»*. Los 160 eran **100 de panel + 60
del farol del interior** (`power_budget.py` l. 156, y #300 §9): el farol no está
en ninguna perilla ni en ningún jack. Contra el denominador que corresponde —los
de panel— son **16 de 100, un 16 %**. Sigue siendo *«algunos cuantos»*, pero la
cifra honesta es ésa.

**Y el ancho de la deixis, que es la parte que la ley sí manda.** Voronov lo
acotó: *«ese jack está activo»* es deixis y cabe en **un bit**. *«De qué clase
es»* —el color— es **estado**, y el estado se dice mejor en la pantalla, que es
lo que D5 acaba de hacer con el nombre. Así que se separa:

- **El bit vive en el LED por ley.** Una pantalla no puede estar en un sitio.
- **El color se queda por ergonomía, no por ontología.** Ver tres jacks
  encendidos del mismo color y saber que son un grupo, sin mirar la pantalla, es
  correlación de un vistazo. Es un argumento de comodidad, es de Samuel, y se
  firma como tal: **estado viajando sobre un portador deíctico, a sabiendas.**

#300 D7 ya dejó vivas las 4 coronas de MACRO por el mismo motivo, y estos LED
entran en esa familia: son clientes de #297, no un capítulo nuevo.

> **La cuenta de corriente NO se hereda del cálculo viejo.** #300 retiró
> `LED_A_BLANCO_PLENO`, `LED_A_CASO_REAL` y `LED_A_TOPE_104` **con sus
> aserciones**, y dejó dicho por qué no se reescriben: *«un aserto sin cifra de
> hoja es un comentario con sintaxis»*. Esa regla sigue: los LED de la bahía
> entran al presupuesto **cuando #297 traiga hoja**, no antes.

### D7. Señalar se hace en la pantalla — y solo puede por D1

Ésta es la mitad de #302 que Samuel no nombró explícitamente, y es donde se ve
que #301 y #302 son la misma decisión, como él intuyó.

`nucleo-digital` §2.1, líneas 138-141:

> ***El agente puede señalar.** Como la cadena WS2812 es direccionable y se
> alcanza por el modelo, «¿dónde está el cutoff?» enciende el LED de esa perilla.
> **Señalar y el patcheo guiado son el mismo mecanismo — el segundo sale gratis
> del primero.***

Sin LED por perilla, el mecanismo citado no existe. **La pantalla lo repone, y
peor** — y conviene decirlo así, porque la v1 decía «mejor» y Voronov lo cazó:

> La v1 argumentaba que un mapa del panel con la perilla resaltada *«no es prosa
> describiendo un sitio, es una imagen del sitio, que es otra cosa»*. **No es
> otra cosa.** La ley que este mismo papel invoca en D6 dice que una pantalla
> *«puede describir una ubicación; no puede estar en ella»*, y un mapa es la
> descripción de máxima fidelidad disponible — sigue siendo descripción. Usar la
> ley para retirar el canal deíctico de las perillas y a la vez declararla
> satisfecha con un dibujo es usarla dos veces en direcciones opuestas.

**Lo honesto:** señalar **se degrada**. Pasa de «la perilla se enciende» a «la
pantalla te dice cuál es». El músico tiene que mirar a otro sitio y traducir.
Se acepta porque:

1. **Las perillas no van a tener LED** por lo que dice §2bis, no por ahorro: 16
   de ellas son fijas y su serigrafía ya dice qué son, así que señalar sobre
   ellas es un caso raro.
2. **Las 4 MACROS, que son las que de verdad cambian de significado, SÍ tienen
   corona**, y sobre ellas señalar sigue siendo deixis pura (#297).
3. Un mapa dibujado a escala del panel real es la mejor descripción posible, y
   la 7" está en el centro del panel — no al lado del instrumento.

**Y esto solo es posible por D1.** Para dibujar «esta perilla es tu cutoff ahora
mismo», alguien tiene que saber qué perilla está asignada a qué parámetro en este
instante. Con el mux en el módulo, esa tabla vivía repartida entre módulos que no
tienen pantalla. **Con el mux en el cerebro, el que dibuja es el que sabe.**

**Qué pasa con el mensaje del protocolo.** `Point { id: ParamId, color: Rgb }`
(`protocolo.rs` l. 82-87, `T_POINT = 0x0C` congelado) y su rama viva en
`servidor.rs:453` devolviendo `NoDisponible`: **el mensaje se queda y cambia de
destinatario.** `id` sigue siendo el parámetro a señalar; `color` deja de ser
para un LED de perilla y pasa a ser el resalte que la pantalla usa —el mismo
campo, el mismo ancho, otro dibujante. No se toca el formato: se implementa
contra la pantalla cuando la pantalla tenga UI, y hasta entonces `NoDisponible`
sigue siendo la respuesta honesta.

### D8. Dónde viven los jacks — y lo que cuesta el valle

> **Corrección propia (Principio VII), cazada por Halcyon.** La v1 de este papel
> decía que los 16 jacks de la bahía están *«en Fila A, canto derecho — firmado
> el 2026-08-23, no se toca»*. **Es falso desde el 2026-08-27.** La enmienda de
> «la pantalla al centro» en `panel-frontal-gramatica.md`, línea 92, ya los
> movió:
>
> > | **BAHÍA** | 16 Thonkiconn 4×4 al canto derecho | **sale del panel** — al
> > valle, a resultas de un estudio. **Mata la colisión E-C6** |
>
> Leí la tabla de la Fila A (línea 118) y no leí la enmienda que la corrige,
> veintiséis líneas más arriba. Es **la segunda vez en una semana** que cito un
> bloque sin leer hacia arriba, y el papel del 2026-09-03 nació del mismo error.
> El documento sigue con las dos frases a la vista, y esa contradicción también
> se enmienda (§6).

**Y la corrección cambia la respuesta a mejor:** el valle no es un sitio nuevo
que haya que justificar. **Es donde la bahía ya iba.** El panel que Samuel está
dibujando es el heredero de un estudio que quedó mandado el 2026-08-27 y nunca
se hizo.

Tres sitios, y cada uno tiene dueño distinto:

| Sitio | Qué va | Estado |
|---|---|---|
| **Valle, fila 1U** | los 16 de la bahía **y** los jacks de CV externo que D3 dimensione | **el panel que Samuel está dibujando** — y el estudio que la enmienda del 27-08 mandó y nadie hizo |
| **Fila A** | ya no lleva jacks: los 104 HP son pantalla y los dos flancos de mandos | enmendado el 2026-08-27 |
| **Trasera** | USB, MIDI, mic, instrumentos, master | **#183 + interfaz de audio, ya escritos** — ver §5 |

**Lo que esto le regala al panel del valle:** los jacks de la bahía y los de CV
externo caen en la misma fila, así que **comparten superficie, mazo y familia de
LED**. Un solo driver (#297), un solo criterio de rótulo, un solo estudio de
drapeado. La pregunta de Samuel —*«¿podría ser un patch bay configurable?»*—
tiene por respuesta que **el patch bay configurable ya está especificado y ya
tiene sitio**; lo que falta es el estudio del 27-08 y el dimensionado de D3.

**El valle está libre de estructura y de aire, y las dos cosas hay que decirlas
con su número.**

*Libre de estructura*: la bandeja de la bahía murió el 2026-08-29
(`nariz-recta-valle-limpio` §2.1, *«La bahía se va, sin heredero»*) y en el valle
quedan solo los dos Z-Rails del 1U. El sitio existe.

*Libre de aire, pero con un costo*: el valle **fue** la salida de aire —
`params.scad` l. 630, *«era la entrada de aire frio, y salia por las ranuras del
valle»*, y esas ranuras daban 7499 mm² en 102 ranuras. Hoy no ventila: la salida
se mudó al alero y a las ondas. **Pero el estado térmico es el peor del repo**, y
un panel de jacks en el valle compite por el sitio donde habría que reponer área.
`clearance_budget.py` corrido el 2026-09-04:

```
tiro 105 mm, area efectiva 3299 mm2 -> 77.4 K sobre ambiente con 147.83 W
(techo 15; esta chimenea evacua 12.6 W a ese techo). SUPUESTO: C_D=0.65, sin perdidas de trafo
```

**La línea entera incluye su supuesto, y la v1 la cortó justo antes** — que es
la falta que este repo tiene tipificada. El guion insiste dos veces más: *«Nada
de esto esta medido: C_D, la altura efectiva y las perdidas del trafo son
supuestos»* y *«C_D ES EL NUMERO QUE MAS MANDA Y EL UNICO SIN MEDIR»*. **Los
77,4 K son un supuesto, no una medición**, y así van a §3.

**Y la cuenta del valle estaba mal por completo.** La v1 decía *«los 7499 mm²
del valle son ~25 % del déficit»*: comparaba **mm² geométricos de ranura** con
**mm² de área efectiva**, que no son la misma magnitud. El guion combina entrada
y salida **en serie**:

```python
a_ef = 1.0 / math.sqrt(1 / a_ent ** 2 + 1 / a_sal ** 2)
```

Y en serie `a_ef < min(a_ent, a_sal)` **siempre**. Corrido con las cifras de hoy
(entrada 7065, salida 3731, `a_ef` 3299):

| | `a_sal` | `a_ef` |
|---|---|---|
| hoy | 3 731 | 3 299 |
| reponiendo las 102 ranuras del valle (+7 499) | 11 230 | **5 980** |
| **salida infinita** (el techo que pone la entrada) | ∞ | **7 065** |

**De donde salen dos cosas, y la segunda es más grande que este papel:**

1. **El valle vale mucho de lo poco que la salida puede comprar.** Repuesto da
   +2 681 mm² efectivos, que es el **71 %** de los +3 766 que toda la salida del
   mundo podría comprar. No es despreciable.
2. **Pero el déficit declarado es de 29 395 mm² efectivos, y la entrada pone un
   techo de 7 065.** Aunque la salida fuera infinita, `a_ef` no pasa de ahí.
   **#289 no se puede cerrar por la salida: el cuello es la entrada.**

> **Lo que este papel manda, corregido:** el panel del valle **se dibuja**, y los
> jacks son buen inquilino. La servidumbre que la v1 le ponía —«deja área de
> ranuras o declara que renuncias»— **se retira**: reponer el valle entero no
> acerca al techo de 15 K ni de lejos, así que cobrarle esa carga al panel era
> pedirle un sacrificio por un beneficio que la propia física del guion no puede
> entregar. Lo que sí se manda es al **#289, con cifra nueva: mirar la entrada.**

---

## 2bis. El residuo: por qué las 16 perillas se quedan fijas

**Ésta es la parte que contesta la pregunta que Samuel dejó abierta con un «¿no?»,
y la respuesta es que su instinto era correcto y por una razón dura.**

Sus palabras: *«todo altamente configurable y las que se quedan fijas serian
como muy clasicas no?»*

Voronov nombró una tercera categoría que ni «estado» ni «deixis» capturan, y que
es la que decide esto:

| | Qué es | Ejemplo |
|---|---|---|
| **Estado** | qué dice el instrumento | «este parámetro está anulado» |
| **Deixis** | dónde lo dice | «*ese* jack» |
| **Residuo** | **qué afirma un objeto por el mero hecho de existir** | una perilla a las 3 dice «esto está a las 3» — la mire alguien o no, esté asignada o no, esté el instrumento encendido o no |

Un CV externo **no tiene residuo**: no tiene cuerpo. Una perilla sí, y ahí está
el costo escondido de la configurabilidad:

> **Con perillas fijas hay un problema de posición rancia por perilla, y el repo
> ya tiene su mecanismo: el salto suave (`panel-frontal-gramatica` A3). Con
> perillas configurables, una sola reasignación falsifica veinte posiciones de
> golpe — y la reasignación la puede hacer un preset, sin que la mano toque
> nada.**

El salto suave está diseñado para «cargaste un preset y esta perilla quedó
descolocada». No está diseñado para «las veinte mienten a la vez, y además ahora
significan otra cosa». Eso no es el mismo problema con más instancias: es otro
problema, y **no tiene mecanismo escrito**.

**De ahí la decisión, que es la que el panel ya tenía y este papel ratifica con
su porqué:**

- **16 perillas curadas, fijas, con serigrafía.** Su residuo siempre dice la
  verdad, porque su significado no cambia. Son «las clásicas» de Samuel, y son
  clásicas por una razón de ingeniería, no de gusto.
- **4 MACROS configurables, con corona de LED.** Reasignables *y* con superficie
  propia para decir qué son ahora — que es exactamente el precio del residuo,
  pagado en luz.

> **Lo que este papel recomienda en voz alta:** que la configurabilidad de
> perillas **no crezca más allá de las 4 MACROS hasta que exista mecanismo para
> el residuo**. Hacer las 16 reasignables es barato en software y caro en
> confusión: veinte objetos físicos afirmando cosas falsas a la vez. Si en algún
> momento se quieren más, lo que hay que diseñar primero es qué las desmiente.

---

## 3. Los números

| Qué | Valor | De dónde | Clase |
|---|---|---|---|
| GPIO libres del hub tras lo vario | **48** (VFBGA264, base) · **28** (peor escenario) | `micro_budget.py`, **con el mux sentado**, corrido 2026-09-04 | corrida |
| Coste en pines del mux de perillas | **6 GPIO + 1 entrada de ADC** | ídem; 2× CD74HC4067 para 20 potes | ESTIMADO (pieza sin elegir) |
| Perillas del instrumento | **20** (16 curadas + 4 MACRO) | `panel-frontal-gramatica.md` §4 l. 114-115 | papel |
| Canales de mux del VCO-16 que se liberan | **8 de 16 por micro**, y estaban *reservados*, no cableados | VCO-16 §7.1, tabla l. 571 | papel |
| Destinos internos libres del crosspoint | **0** | `bahia_budget.py`, leyendo `CANALES`/`LINEAS` de `bahia.rs` | corrida |
| Fuentes libres hacia las voces (A.X) | 6 | ídem | corrida |
| Destinos libres hacia el mundo (B.Y) | 7 (6 con oídos en estéreo) | ídem | corrida |
| LED que vuelven | **16** (bahía) + los de CV por dimensionar | D6 | decisión |
| LED de la cadena retirada | **160 = 100 de panel + 60 del farol** | `power_budget.py` l. 156; #300 §9 | papel |
| Fracción que vuelve, contra los de panel | **16 %** | 16 / 100 | aritmética |
| Margen de recuperación del J2 | **102×** | `recuperacion_j2_budget.py` (esta tanda) | corrida |
| Salto térmico del case | **77,4 K** (techo 15) | `clearance_budget.py` | **SUPUESTO** — `C_D = 0.65` es *«EL NUMERO QUE MAS MANDA Y EL UNICO SIN MEDIR»* |
| Lo que toda la salida puede comprar | **+3 766 mm²** efectivos; el valle da +2 681 de ellos | serie `a_ef`, con `a_ent = 7065` | aritmética |
| Déficit declarado de #289 | **29 395 mm²** efectivos | `clearance_budget.py` | **inalcanzable por la salida** (§D8) |

---

## 4. Lo que este papel NO decide, con su dueño

| Pregunta | Dueño | Bloquea a |
|---|---|---|
| **La autoría de un escritor que no es la mano** (`Puerta` en Rust, N1-N8) | **#177** | **D3bis: el CV no se cablea a un parámetro sin esto** |
| **El guion y el acta de la clase rápida de entrada** | nuevo, con la cerradura de motor-digital §5 | El dimensionado de D3 |
| Si los 20 potes de la fila A son board-mount | **El papel del panel** | El tamaño del riesgo 1 |
| Cuántas entradas de CV, de qué clase de tasa, en qué pin | **#301**, con el censo de pines | — |
| El reparto de pines del hub con esta población dentro | **#301** | — |
| La pieza del driver de LED y su corriente | **#297** | La cifra de los 16 LED en el presupuesto |
| **Qué repone el diagnóstico de «el motor no arrancó»** | sin dueño — **hueco heredado de #300** | — |
| Cómo se cierra #289 **por la entrada** | **#289**, con la cifra de D8 | — |
| La cadena analógica de la interfaz de audio | **interfaz-audio**, pendiente de firma (#256) | — |
| Cómo se dibuja el mapa del panel en la 7" | El papel de la pantalla, cuando exista UI | D7 |
| Si los oídos ruteables son mono o estéreo | **motor-digital D-P4** (HUECO acotado: con 2 cabe) | — |
| El estudio que la enmienda del 27-08 mandó para la bahía en el valle | **El panel del valle** — el que Samuel está dibujando | — |

---

## 5. Lo que Samuel pidió y **ya está escrito** (Principio de no duplicar)

Sus palabras: *«espero poder o bien crear otro panel para conectar modulos tipo
las entradas usb, midi, mic in, instrumentos (la parte de la interface de audio),
salidas de master, etc (todos los juguetes)»*.

**Eso tiene papel desde el 2026-08-31** y no hace falta pensarlo de nuevo:
`2026-08-31-interfaz-audio-design.md`, un cuarto N657 dueño del reloj y única
boca del instrumento — 4 pre de micro, 2 Hi-Z de instrumento, 4 salidas
balanceadas, 2 de auriculares, óptico, 24/192. Estado: **propuesto, pendiente de
Samuel**.

**Por qué no está firmado, en una línea:** le falta un número que no publica ST —
el máximo de `IDDSMPS` a 85 °C (#256). Entre el típico y el máximo hay 7,4×, y
con cuatro N657 el presupuesto de la fuente cierra con el típico y **no cierra**
con el máximo. Firmarlo hoy sería firmar contra un dato que no tenemos.

Y la trasera donde todo eso aterriza es **#183**, ya abierta.

**Este papel no toca ninguno de los dos.** Solo evita que se escriban por tercera
vez.

---

## 6. Enmiendas mandadas, con línea exacta

### 6.0 Prelación con #300, que es lo primero que hay que resolver

**Diez de las filas de la v1 re-mandaban trabajo que `2026-09-03-instrumento-entero`
§7 ya mandó, firmado, hace un día, y que nadie ejecutó.** Verificado:
`architecture-poly.md` tiene **una sola** marca de enmienda en todo el archivo
(l. 234, del 26-08) y `nucleo-digital` tiene una (l. 961). Los pasajes siguen
crudos. Es el patrón que este repo ya tiene en memoria —*las specs prometen
enmiendas en una tabla y nadie las ejecuta*— y con este papel iban dos capas.

**Se declara prelación, y en un sitio los dos mandatos decían lo contrario:**

> **Este papel NO sustituye a #300 §7: lo HEREDA.** Las enmiendas de #300 se
> ejecutan tal cual, y donde este papel toca la misma línea, **manda este papel
> por ser posterior**. La tabla de abajo marca cada fila con su origen para que
> quien ejecute sepa si está haciendo trabajo de ayer o de hoy.

**La contradicción, resuelta:** `nucleo-digital` l. 1280-1281 (*«toda entrada de
CV patcheable tiene que ser legible por ADC»*). #300 D3 lo **derogó** (murió su
cliente, el barrido por inyección). D2 de este papel lo **repone con motivo
nuevo** (el correlador de §7.6, que sigue vivo y sigue necesitando un punto de
observación por entrada). **Vigente con el motivo de D2, no con el de §6.2.**

### 6.1 La tabla

`(300)` = ya mandada por #300 y sin ejecutar · `(nueva)` = de esta tanda.

| Papel | Líneas | Tipo | Qué |
|---|---|---|---|
| `nucleo-digital` §10 | 1277-1278 | Rewrite | `(300 E5)` «el mux de perillas vive en el módulo» → al cerebro (D1) |
| ídem | 1279 | Clarify | `(300 E5)` «Sensado de ocupación» se queda; motivo nuevo (D2) |
| ídem | 1280-1281 | Rewrite | `(nueva)` **Vigente con el motivo de D2** — ver §6.0 |
| ídem | **1282** | Rewrite | `(nueva)` *«Las lecturas vuelven por el `MISO` del J2»* — hoy habla de las dos poblaciones; hay que acotarlo a la que sigue volviendo |
| ídem | 1283 | Remove | `(300 E5)` «Un LED de la cadena WS2812 por perilla y por jack» |
| ídem | **1292-1307** | **Rewrite** | `(nueva)` **Todo el bloque «El cerebro» describe un RP2350B**, con su mux I²C, su cadena WS2812 y su PIO-USB. El cerebro es el N657 desde el 2026-08-30 |
| ídem | 1317-1318 | Clarify | `(nueva)` *«el cerebro manda números, no voltajes» — la regla que §5.0 y §7.4 dejan sin excepciones*: D1 le abre una, y estrecha (§D1) |
| `architecture-poly.md` | 29-32, 84-86, 160 | Rewrite/Remove | `(300 E1/E2/E3)` Banner de vigencia, «el panel entero es la pantalla de verdad», fila LED |
| ídem §7 | 383-393 | Rewrite | `(300 E2/E7)` El gemelo del argumento del mux (D1) |
| ídem | 395-409 | Rewrite | `(300 E2)` «El desfase de la perilla: soft takeover con LED» |
| ídem | 421-446 | Remove | `(300 E2)` «Los LEDs de panel», sección entera |
| ídem §8 | **520-523** | Rewrite | `(nueva)` Sacar el mux de perillas de *«por ahí regresan»*, **y acotar el invariante** *«El cerebro nunca recibe voltajes, ni siquiera para oír»*, que D1 falsifica tal cual |
| `nucleo-digital` §6.2 | **855-858** | Rewrite | `(300 E7)` La inferencia del mux, con su salto dicho *(rango corregido: empieza en 855)* |
| VCO-16 §7.1 | **549-573** | Rewrite | `(nueva)` 8 canales de control se quedan; los 8 **reservados** para perillas se liberan (D2) |
| VCO-16 §7 | **557-566** | Clarify | `(300 E7)` «para el barrido por inyección y para la ocupación» → **el correlador de §7.6**, que es el cliente real. **NO «solo ocupación»**: la ocupación es un registro de desplazamiento y no usa el ADC (Serrano) |
| `voz-total` §5.1 | 442-443 | Rewrite | `(300 E8)` «su LED dice en color qué es» → nombre en pantalla, bit + color en LED (D5, D6) |
| ídem §5.1 | **474-476** | Sync | `(nueva)` *«El censo está mandado… no está hecho»*: **está hecho** (`bahia_budget.py`) |
| `motor-digital` §8.4 pt 4 | — | Update | `(nueva)` Censo del crosspoint: **CORRIDO**, verde |
| **`2026-09-03-instrumento-entero` §9** | fila «LED en el instrumento» | Rewrite | `(nueva)` Dice «4 coronas de MACRO»; con D6 son 4 coronas + 16 de bahía |
| **ídem D9** | l. 304 | Rewrite | `(nueva)` *«y **sin LED**»* — D6 lo enmienda, con acta de Samuel |
| ídem §6.1 | — | Update | `(nueva)` La conversación aparcada: **contestada** |
| `panel-frontal-gramatica` §7 | **268-276** | Rewrite | `(nueva)` El panel-como-módulo se retira: su premisa era el RP2350. *(Corrección de cita: estas líneas están en «## 7. El frente» y **remiten** a §11.2; §11 empieza en la l. 393)* |
| ídem §11, punto 2 | **403-405** | Remove | `(nueva)` *«El módulo de mandos, de verdad… Su spec corto es el siguiente papel técnico»* — el ítem de acción de la propuesta retirada |
| ídem | **92 vs 118** | Clarify | `(nueva)` El documento se contradice: l. 92 saca la bahía al valle (27-08), l. 118 la sigue poniendo al canto derecho. **Manda la 92** (D8) |
| ídem | **53** | Sync | `(nueva)` Su copia propia de *«el jack es un nombre que le da el preset»* |
| ídem | **309** | Rewrite | `(nueva)` Cita la cadena WS2812 como mecanismo vivo de *«el motor no arrancó»*. Retirada por #300; **el hueco de diagnóstico de arranque sigue sin dueño** |
| ídem §5.2 pt 2, §11.2 | **45 potes** | Sync | `(nueva)` El censo real son **20** (16 + 4). La cifra vieja tiene cinco ecos en cuatro documentos |
| **`autopista-el-pase-de-ancho-de-banda.md`** | entero | Rewrite | `(nueva)` **Es el presupuesto de ancho de banda del escaneo del mux**, y sus dos premisas mueren: un micro dedicado al panel (D1) y 45 potes. Con D1 el escaneo lo hace el hub compartiendo tiempo con seis maestros de J2, radios y pantalla: **es otro presupuesto de latencia** |
| `architecture-compute.md` | **272** | Rewrite | `(nueva)` *«un J2 por módulo… hacia sus DAC, digipots, **mux de perillas** y sensado de jacks»* |
| `bus-board/ground_budget.py` | **64-69** | Sync | `(300, sin ejecutar)` `I_MASA_SAM17` sigue justificándose con *«holgura para una fila de LED de panel»*. Con D6 los 16 LED son locales a su placa y **no cruzan la masa del bus-board**: la constante sigue sin sujeto |
| `core/src/bahia.rs` | **16-18** | Sync | `(nueva)` *«el censo… no esta hecho»* → hecho |
| `core/tests/bahia.rs` | **9-11**, **165-169** | Sync/Rewrite | `(nueva)` Ídem, y el comentario que #300 escribió ayer (*«El LED del jack se retiro»*) vuelve a ser falso para la bahía |
| `core/src/protocolo.rs` | **82-83** | Clarify | `(nueva)` El comentario dice *«enciende el LED de un parametro o de un jack»*: tras D6/D7 es falso para el parámetro y cierto para el jack. **El formato no se toca; el comentario sí** |

---

## 7. Riesgos

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | **La línea analógica del panel al cerebro recoge ruido** y las 20 perillas tiemblan | El umbral de gesto en LSB con histéresis que `panel-frontal-gramatica` §5.2 punto 2 ya exige. **Ojo con la cifra**: aquel punto habla de *«45 potes»*, censo viejo; hoy son 20, y el umbral hay que recalcularlo, no heredarlo (§6). Se mide en bring-up |
| 2 | **Los 20 potes no son board-mount y entre pote y mux hay cableado analógico** | **Riesgo nuevo, de Serrano.** La v1 daba el board-mount por escrito citando el rebaje Ø12×3 de `panel-frontal-gramatica` §4 — pero ese rebaje existe porque *«un Thonkiconn tiene 4,7 mm de casquillo — en 5 mm no rosca»*, o sea que es una cota de montaje **al panel**, y si acaso apunta a casquillo y tuerca. **Ningún papel dice que los potes de la fila A vayan soldados a una placa.** Es «no especificado», no «ya son», y decide el tamaño del riesgo 1 |
| 3 | **Un cerebro colgado se lleva las perillas** (costo declarado de D1) | **Menos grave de lo que la v1 dijo.** La v1 lo despachó citando *«el módulo suelta a los ~50 ms»* — que es la **premisa** del papel del maestro del J2, no su conclusión: ese papel acota la recuperación a **490 µs con 102× de margen**, y trata el cuelgue del **periférico SPI**, no del chip entero. El costo de D1 sigue sin evaluar contra el cuelgue del chip |
| 4 | **La clase rápida de CV entra sin presupuesto ni acta** | La ley de dos tasas trae cerradura explícita: *«Promover un destino a rápido es acta de Samuel + guion recorrido — ni criterio implícito ni censo fantasma»*. D3 la aplica a **entradas**, que aquella ley no legisla, y su presupuesto (29,9 Mb/s sobre 90) no mide ningún ADC. **Hace falta guion propio y acta**, y así queda mandado en §4 |
| 5 | El panel del valle se dibuja y luego #289 pide ese sitio | **Retirado.** La aritmética de D8 muestra que reponer el valle entero no acerca al techo: el cuello es la entrada. Lo que queda mandado es al #289, con cifra |
| 6 | Los LED de la bahía repiten la historia del #104 (compiten por el +5 V) | La regla de D6: entran al presupuesto cuando #297 traiga hoja. 16 no son 100, pero un aserto sin hoja no vale |
| 7 | La topología A/B del crosspoint es una lectura y el cobre la desmiente | `bahia_budget.py` lo declara en su cabecera. **Corroborada por `core/src/bahia.rs`** (*«El de entrada lleva una linea al nodo de suma de un canal; el de salida lleva la salida post-VCA de un canal a una linea»*), que es más que una lectura de prosa — pero sigue sin esquemático |
| 8 | **La reasignación falsifica veinte posiciones de golpe** | Ver §2bis. Es la razón de que las 16 perillas curadas **se queden fijas** |

---

## 8. Lo leído para escribir esto

`docs/architecture-poly.md` (§7 l. 330-459, §2 l. 100-127, §6, l. 520-523);
`docs/architecture-compute.md` l. 272-279;
`nucleo-digital` §2.1 l. 138-141, §6.2 l. 830-889, §7.2, §10 l. 1270-1310;
`voz-total` §5.1-5.4 l. 420-520;
VCO-16 §7.1 l. 544-573, §6.3;
`panel-frontal-gramatica` §4 l. 95-138, §5.2 l. 177-210, §6, §7, §8, §9, §11.2 l. 268-276;
`motor-digital` §4 D-P1..D-P4 l. 150-190, §5, §8.4;
`interfaz-audio` entero (326 l.);
`nariz-recta-valle-limpio` entero (196 l.);
`2026-09-03-instrumento-entero` §6.1;
`2026-09-03-maestro-j2-recuperacion` §0-§2;
corridos: `micro_budget.py`, `clearance_budget.py`, `bahia_budget.py` (nuevo);
`case/cad/params.scad` l. 620-650, l. 1295-1310; `case/clearance_budget.py` `guarda_aire()`.

---

## 9. La junta del 2026-09-04

La v1 pasó por Serrano (exactitud clínica), Voronov (crítica ontológica) y
Halcyon (mapa de impacto) **antes de pedir la firma**, que es la regla de esta
casa desde el 2026-09-02. Cambiaron siete decisiones y dos guiones. Lo que
encontraron, y dónde quedó:

| ID | Hallazgo | Dónde quedó |
|---|---|---|
| **S-1** BLOCKER | Diez de las 17 enmiendas re-mandaban trabajo de #300, firmado y sin ejecutar; y en `nucleo-digital` l. 1280-1281 los dos mandatos decían lo contrario | **§6.0**: prelación declarada, contradicción resuelta |
| **S-2 / V-5** BLOCKER | *«el mux ya está contado»* citaba el pin de RESET del mux **I²C** | **D1** reescrito; `micro_budget.py` cobra ahora 6 GPIO + 1 ADC; **+48**, no +54 |
| **S-3** BLOCKER | *«~25 % del déficit»* comparaba mm² geométricos con mm² efectivos | **D8** rehecho con la serie corrida; y sale un hallazgo mayor: **el cuello es la entrada**, no la salida |
| **S-5** | *«rompería `perturbacion.rs`»* es falso, y el cliente del ADC no es la ocupación | **D2** reescrito: el cliente es el correlador de §7.6, y lo que se rompería es el mazo, no el Rust |
| **S-6** | La enmienda a VCO-16 dejaba el ADC del módulo sin cliente | **§6**, fila corregida: «el correlador de §7.6», no «solo ocupación» |
| **S-7** | La cita de `clearance_budget.py` cortada justo antes de `SUPUESTO: C_D=0.65` | **D8** y **§3**: los 77,4 K van marcados como supuesto |
| **S-8** | D3 hereda la ley de dos tasas saltándose su cerradura (*«acta + guion recorrido»*) | **Riesgo 4** y **§4**: hace falta guion propio y acta |
| **S-9** | D6 dejaba falsas la tabla §9 y el D9 de #300 sin enmendarlos | **D6** lo dice: enmienda a #300, con su fila en §6 |
| **S-10** | El «10 %» dividía por 160, que incluye 60 del farol | **D6** y **§3**: 16 de 100, **16 %** |
| **S-11** | Dos asertos de `bahia_budget.py` eran tautológicos, y el «no sabe hacer de múltiple» era falso | Guion reescrito: lee `CANALES`/`LINEAS` de `bahia.rs`, **y las dos mutaciones mueren**. El múltiple hacia adentro existe; lo que no existe es el puente sin gastar canal |
| **S-13** | El rebaje Ø12×3 no dice board-mount | **D1**: HUECO declarado, y **riesgo 2** nuevo |
| **S-14** | 20 potes contra 45, sin dimensionar el mux | **§3** con la cifra y el coste; **§6** manda sincronizar los cinco ecos |
| **S-15** | El costo de D1 se despachaba citando la premisa del papel del J2, no su conclusión | **Riesgo 3** reescrito |
| **V-1** | La tesis unificadora no cargaba ninguna decisión: ratificación disfrazada de derivación | **§1** rehecho: dice en qué se parecen y en qué no |
| **V-2** BLOCKER | D1+D3 rompen la autoría: el transporte deja de distinguir mano de máquina, y un CV no suelta | **D3bis** nuevo: un CV no captura, declara fuente; la clase del canal la fija el cobre; **#177 es prerrequisito** |
| **V-3** | La deixis tiene ancho, y es un bit; el color es estado | **D6**: el bit por ley, el color por ergonomía y dicho así |
| **V-4** | Un mapa sigue siendo una descripción: señalar en pantalla no es «otra cosa» | **D7** |
| **V-6** | *«el modelo vive en el cerebro»* es falso: `voz-total` §0.2 dice «y los módulos» | **§1**: intención contra vigencia |
| **V-7** | La frontera del crosspoint es cardinalidad disfrazada de tipo; y `conducto` ya legisla el puente | **D4** y el guion |
| **V-8** | Falta una tercera categoría: el residuo | **§2bis** nuevo, y es lo que sostiene que las 16 se queden fijas |
| **H-1** | `architecture-compute.md` l. 272 nombra el mux de perillas en el J2 | **§6** |
| **H-3** | `autopista-el-pase-de-ancho-de-banda.md` es el presupuesto del escaneo, y D1 mata sus dos premisas | **§6**, y es la fila más grande que la v1 no vio |
| **H-4** | El comentario de `core/tests/bahia.rs` que #300 escribió ayer vuelve a ser falso | **§6** |
| **H-5/6/7** | Tres ecos de *«el censo no está hecho»* | **§6**; el censo está corrido |
| **H-10** | `panel-frontal-gramatica` se contradice: l. 92 saca la bahía al valle, l. 118 la deja en el canto | **D8**: manda la 92 — **y eso corrige el error de la v1** |
| **H-11** | La cadena WS2812 sigue citada como mecanismo de *«el motor no arrancó»* | **§6**; el hueco de diagnóstico de arranque **sigue sin dueño** |

**Lo que la junta no cambió:** D1 en su dirección (el mux al cerebro), D5 (el
nombre a la pantalla), la existencia de los 16 LED, el censo del crosspoint y su
veredicto verde, y que el valle es el sitio de los jacks.

**Y lo que este papel confiesa sin que nadie se lo preguntara:** es la **segunda
vez en una semana** que cito un bloque sin leer hacia arriba y me pierdo su
enmienda —la primera fue el testigo del #300, ésta es la bahía en el valle—. La
memoria de esa lección existe desde el 2026-09-03 y no bastó.
