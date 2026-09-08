# Fuente v5 — el ladrillo afuera, la conversión adentro

**Fecha**: 2026-09-05 · **Estado**: **D-V1, D-V2, D-V3 y D-V5 FIRMADAS el
2026-09-08**; D-V2 y D-V5 arrastran **16 HUECOS** a §9.2. **D-V4 sigue sin
firmar** y sigue siendo el atasco (§9) ·
**Decidido por Samuel el 2026-09-05**: sacar la etapa AC-DC de la caja (opción B de
tres), y firmar **D-B2 a 500 mA/riel** para la fila de abajo ·
**Junta**: `2026-09-08-junta-fuente-v5-dv1-dv5.md` — dictaminó D-V1 firmable tal
cual, D-V2/D-V3/D-V5 con condición, y D-V4 **no firmable aún** ·
**Guion**: `hardware/01-power-supply/v5/ladrillo_budget.py` — todas las cifras de
este papel salen de ahí, corriendo ·
**Reabre**: `fuente-v4-liston` §1 (D-F1), §3, §4.1, §4.2, §5 (D-F5), §6, §7 (D-F2);
la spec del chasis §3.2 y §3.3; `calor_budget.py`; `case/cad/params.scad` ·
**No toca**: la cascada de regulación (§4.2 de la v4), que es de donde sale el
0,8 µVrms

---

## 0. Por qué

La v4 mete dentro de una caja de madera: seis módulos AC-DC, la entrada de red,
el fusible, la NTC de arranque, el choke de modo común, los MOV, los Y2 al
chasis, y un recinto de acero de **338,6 × 176,6 × 83 mm** que ocupa el **30 %
del suelo interior**. Con eso, `clearance_budget.py` le encarga al case
**23 666 mm²** de venteo nuevo (#289), que Elke midió como imposibles de sacar
del suelo entero: con la regla de puente del propio repo caben 21 088.

Samuel preguntó por qué un Moog puede ir sellado. La respuesta, con las cifras
de fábrica:

| | potencia | fuente | refrigeración |
|---|---|---|---|
| Moog Subsequent 37 | 13 W | dentro, IEC | ninguna, sellado |
| **SAM17 v4, declarado** | **139,31 W** | dentro | 23 666 mm² de venteo |
| Moog One, 16 voces | 160 W | **fuera**, ladrillo | **ventilador interno** |

Moog sella a 13 W. Al llegar a 160 sacó la fuente **y aun así puso ventilador**.
A la potencia de la v4 la respuesta de Moog no sería «sellado».

Pero los 139,31 W de la v4 son en un 69 % la fila de abajo **a corriente de
placa**: lo que los módulos pueden entregar, no lo que nadie pide. Con la fila
declarada de verdad, el SAM17 no está en la escala del Moog One.

> Fuentes: manual del Subsequent 37 (inMusic, `Subsequent_37_Manual_0.pdf`,
> «13W») y la reseña del Moog One en Sound On Sound (ladrillo de 160 W,
> ventilador interno), leídas el 2026-09-05.

## 1. D-B2, firmada: la fila de abajo declara 500 mA/riel

El 2026-09-04 Samuel corrigió la premisa: *«los otros módulos los vamos a
fabricar nosotros también»*. La fila de abajo no es un censo de invitados de
mercado, es un presupuesto de diseño propio.

El listón «a la altura de la A-100PSU3 o superior» se firmó pensando en módulos
de terceros. **Ese ya no es el supuesto**, y con él cae la razón de declarar
3,8 / 2,5 / 4,0 A.

| | +12 rack | −12 rack | +5 rack |
|---|---|---|---|
| D-F1 (v4, 03-09) | 3,8 A | 2,5 A | 4,0 A |
| **D-B2 (v5, firmada 05-09)** | **0,5 A** | **0,5 A** | **0,5 A** |

Esto no es un recorte de capacidad: es dejar de prometer corriente a módulos que
no existen. La capacidad real la fija la pieza que se elija, y sobra.

## 2. El reparto: qué se va con la fuente y qué no

Lo primero que hay que decir, porque contradice la intuición y decide el resto
del papel:

> **Todo lo que baja por el cordón acaba en calor dentro de la caja.**
>
> El calor lo hacen las CARGAS, y las cargas no se mudan. Lo único que se muda
> es la pérdida de CONVERSIÓN. Así que el calor del cajón es, exactamente, la
> potencia de **salida** del ladrillo.

`ladrillo_budget.py` lo asevera, no lo promete: si algún día entra potencia por
otro sitio, el aserto salta.

De los 139,31 W de la v4, lo que se va con la fuente son **25,02 W** de pérdidas
de conversión y franja de red. Lo demás baja de golpe por otra razón: D-B2.

## 3. El ladrillo (D-V1, D-V2)

**D-V1: la etapa AC-DC es una pieza de catálogo, certificada, fuera de la caja.**
No un cajón nuestro. Un cajón externo multi-riel sería un segundo producto —
chasis, panel, acabado, entrada de red, certificación — y su única ventaja sobre
esta opción es térmica, de **0 W**.

**D-V2: 24 V.** Los 19 V de portátil también bucan bien a los 15,5 de la
cascada, pero a 24 el cordón lleva menos corriente y ~~queda más margen para el
arranque~~ **la reserva de arranque queda por demostrar** (enmienda de D-V2 del
2026-09-08, abajo).

| | |
|---|---|
| tensión | 24,0 V |
| salida, lo que baja por el cordón | **64,22 W** |
| corriente del cordón | 2,68 A |
| lo que le pide a la red | 72,98 W |
| **se disipa fuera de la caja** | **8,76 W** |

> **ENMIENDA (2026-09-08, D-V2 · `2026-09-08-junta-fuente-v5-dv1-dv5.md` §2). Contrato de entrada, fallo y
> arranque por completar.** Se escribe qué hay que acreditar; ~~D-V2 sigue sin
> firmar~~ **D-V2 se firmó en dirección el 08-09 y estos HUECOS viajan con
> ella a §9.2, sin darse por contestados**. Las preguntas siguientes no tienen valores elegidos en el árbol.
>
> **Los nodos no son intercambiables.** Se distingue la salida del ladrillo,
> la entrada del chasis después del cordón, la entrada de los DC-DC después
> de las protecciones que se elijan, y el pin `IN` de `U1` referido a su masa
> local. El nominal de transporte propuesto es **24 V**
> (`hardware/01-power-supply/v5/ladrillo_budget.py:93`); **24 V en el cordón no
> son 24 V en `U1`**. Entre esos nodos está la conversión DC-DC a crudo y la
> cadena de entrada de la cascada, que incluye el filtro LC
> (`ladrillo_budget.py:136`, `:178`). El presupuesto no elige su realización
> ni demuestra una barrera de aislamiento (`ladrillo_budget.py:49`).
>
> **El límite firmado sigue después del DC-DC.** `U1` es el LT1963A de D-F8:
> su entrada tiene máximo absoluto **±20 V**, no un rango de funcionamiento
> ni un objetivo de disparo (`hardware/01-power-supply/v4/check_absmax.py:209`,
> que cita `docs/reference/datasheets/lt1963a-rev-g-2021-02.pdf` p. 2).
> **Si el DC-DC falla con un corto entre entrada y salida**, y no hay una
> barrera o protección independiente que lo impida, puede trasladar la
> tensión de transporte al nodo de `U1` y superar ese máximo. Ni el nominal
> del crudo ni el apagado del convertidor averiado demuestran supervivencia.
> Hay que acotar la tensión que alcanza `IN`, su duración y la energía hasta
> el corte, contra los límites de las piezas que permanecen expuestas.
>
> **Es el cruce con #334:** la v4 ya enfrentaba **20,25 V sostenidos** de OVP
> de `PS1` con los **±20 V** de `U1` (papel
> `2026-09-03-fuente-v4-liston-design.md`, bloque D-F9, «Lo que NO cierra»;
> `check_absmax.py:209`). Cambiar la fuente de ese nodo cambia el origen del
> fallo, pero no cierra el issue. La protección de `U1` ante el DC-DC nuevo
> queda pendiente de decisión y prueba; este contrato no cambia la pieza.
>
> **H-V2-ENTRADA — HUECO: ventana garantizada.** La ventana de entrada del
> DC-DC tiene que contener la que resulte del ladrillo, menos las caídas del
> cordón, contactos y protecciones, en todas las condiciones admitidas. El
> nominal citado no proporciona ninguno de esos extremos. **Pregunta exacta
> al fabricante del ladrillo y de los DC-DC:** «¿Qué mínimos y máximos de
> salida garantiza el ladrillo bajo línea, carga y temperatura, qué ventana
> admiten los DC-DC para arrancar y para seguir regulando, y qué caídas máximas
> de cordón, contactos y protecciones permite compatibilizar ambas?»
>
> **H-V2-SUBTENSION — HUECO: límites de arranque y parada.** Deben quedar
> declarados por separado el encendido, la inhibición por subtensión, la
> histéresis, las tolerancias y el punto donde se miden. **Pregunta exacta:**
> «¿Qué tensión mínima permite arrancar, cuál obliga a inhibir la conversión,
> con qué histéresis, tolerancia y tiempos, en qué nodo se detectan y cómo se
> coordinan esas señales con la habilitación de la cascada de D-F4?»
>
> **H-V2-TRANSITORIOS — HUECO: envolvente admisible.** Se necesitan límites
> de funcionamiento y supervivencia en los nodos anteriores, incluyendo
> cambios de carga y maniobras del cordón de D-V5. **Pregunta exacta:** «¿Qué
> tolerancia del crudo en régimen y qué amplitud, polaridad, duración y
> repetición de transitorios garantiza o admite cada interfaz, bajo qué carga
> y temperatura, y qué elemento limita lo que finalmente alcanza los
> pre-reguladores?»
>
> **H-V2-RESERVA — HUECO: arranque con las cargas conectadas.** El guion
> entrega **64,22 W** y **2,68 A** al nominal propuesto
> (`ladrillo_budget.py:151`, `:169`); son presupuesto estacionario, no reserva
> de arranque ni corriente máxima de fallo. **Pregunta exacta al fabricante:**
> «¿Qué carga capacitiva y perfil de corriente de arranque admite el ladrillo,
> qué corriente y energía exige la cadena completa con sus cargas, qué
> tensión mínima conserva durante ese arranque y qué reserva garantizada
> evita que su limitación y el arranque de los DC-DC se impidan mutuamente?»
>
> **H-V2-RECUPERACION — HUECO: salida de subtensión o protección.** Falta
> elegir la política, además de acreditar que las piezas pueden cumplirla.
> **Pregunta exacta a Samuel y al fabricante:** «¿La cadena debe recuperarse
> automáticamente, reintentar o esperar una intervención, bajo qué condición
> de tensión y tiempo se autoriza, y en qué estado deben quedar sus rieles y
> habilitaciones durante la caída, la espera y el rearranque?»
>
> **H-V2-CORTO-DCDC — HUECO: supervivencia de `U1`, #334.** **Pregunta exacta:**
> «¿Qué recorrido eléctrico deja un corto entre entrada y salida del DC-DC,
> qué tensión, duración y energía alcanzan `IN` de `U1`, y qué elemento
> independiente limita o interrumpe ese recorrido dentro de los límites
> documentados, incluidos sus tiempos y tolerancias?»
>
> **H-V2-AISLAMIENTO — HUECO: evidencia del ladrillo.** La firma de D-V1
> remite aquí clase, aislamiento y fuga; no se eligen por inferencia del
> rendimiento del guion. **Pregunta exacta al fabricante:** «¿Qué clase de
> protección, aislamiento, corriente de fuga, relación entre salida DC y PE,
> y protecciones con su modo de recuperación acredita la referencia propuesta,
> en qué hoja o certificado y bajo qué condiciones?» La carga capacitiva está
> en H-V2-RESERVA y la relación con el chasis en H-V5-PE.
>
> **DECISIONES PENDIENTES:** adoptar la ventana y los límites de entrada;
> elegir las políticas de arranque, inhibición y recuperación; asignar el
> mecanismo que protege `U1` frente al fallo del DC-DC (#334). Para cerrar
> cada HUECO hace falta una respuesta con fuente local, condiciones y criterio
> de aceptación de la cadena completa. No hay todavía piezas ni ensayos que
> permitan dar esas respuestas por satisfechas.

El cordón es de **dos hilos**, no de siete. ~~Su caída no cae encima de ningún
margen: la absorbe el convertidor de dentro.~~ La conversión puede absorberla
**mientras su entrada permanezca dentro de la ventana que garantiza regulación**;
esa ventana es H-V2-ENTRADA (enmienda del 2026-09-08).

| calibre | 1 m | 2 m |
|---|---|---|
| 18 AWG | 112 mV | 225 mV |
| 16 AWG | 71 mV | 141 mV |

Con 16 AWG y 2 m son el **0,6 %** de 24 V. Esta es la diferencia de fondo con
bajar los rieles ya hechos, donde esa misma caída caería justo sobre el margen
de `U1`/`U2` — que es el problema que este papel viene a cerrar, no a empeorar.

> **ENMIENDA (2026-09-08, D-V5 · `2026-09-08-junta-fuente-v5-dv1-dv5.md` §2). Contrato del cordón y relevo de
> retorno/chasis/PE por completar.** ~~D-V5 sigue sin firmar.~~ **D-V5 se firmó
> en dirección el 08-09; estos HUECOS viajan con ella a §9.2.** «Dos hilos» no
> elige conector, protección ni referencia de masa.
>
> **Lo calculado no es todavía un calibre vinculante.** Se conserva el
> resultado del guion: **141 mV con 16 AWG y 2 m**, a **2,68 A**, equivalentes
> al **0,6 %** del nominal de **24 V** (`ladrillo_budget.py:173`, escenario
> `:339`, corriente `:169` y nominal `:93`). No se recalcula ni se convierte
> ese escenario en una elección de cable. La función no incluye resistencia
> de contactos; tampoco demuestra el comportamiento durante arranque o fallo.
>
> **El retorno DC no hereda el PE por llamarse retorno.** La v4 lleva ★ por
> `J5` al espárrago, con anillos separados para `J5` y el PE de red (papel
> `2026-09-03-fuente-v4-liston-design.md` §4.1). D-F5 cerraba el modo común por
> **módulo → Y2 → chasis → PE → primario** (mismo papel §4.2, «EMI»).
> **Dos hilos de alimentación y retorno no transportan ese PE separado.**
> **No hay todavía un heredero identificado de ese camino.** No queda por
> ello decidido que el retorno DC sea PE, que se una al chasis o que el
> chasis quede flotante. El PE del propio ladrillo, si lo tiene, tampoco
> demuestra un camino hasta el chasis a través del cordón.
>
> El relevo debe declarar las relaciones entre retorno DC, ★, `J5`, chasis
> y PE, y acreditar el camino de modo común del conjunto. No puede dar por
> heredado el resultado de D-F5 con las piezas retiradas. Sigue vigente la
> separación de `GNDD`, fuera de ★, y la aceptación **>1 MΩ entre GNDA y
> GNDD** dentro de la fuente (v4 §4.1 y §9.1). Esta obligación limita las
> respuestas posibles; no elige las barreras ni los retornos de D-V4.
>
> **H-V5-CONECTOR — HUECO: pareja y polaridad.** **Pregunta exacta:** «¿Qué
> pareja de conectores se elige para ladrillo y chasis, qué contacto lleva
> alimentación y cuál retorno, cómo se identifica esa polaridad y qué hoja
> local acredita sus límites eléctricos y su resistencia de contacto?»
>
> **H-V5-RETENCION — HUECO: sujeción del conjunto.** **Pregunta exacta:**
> «¿Qué retención y alivio de tracción se exigen al conjunto, bajo qué esfuerzo
> se verifican y qué condición de aceptación debe cumplir?»
>
> **H-V5-CALIBRE — HUECO: cordón vinculante.** **Pregunta exacta:** «¿Qué
> calibre, longitud máxima y resistencia total admisible se adoptan para el
> cordón completo, incluidos conectores y terminaciones, y qué corriente y
> temperatura debe soportar en uso, arranque y hasta el corte por fallo?»
>
> **H-V5-INVERSION — HUECO: polaridad inversa.** **Pregunta exacta:** «¿Qué
> debe ocurrir al aplicar polaridad inversa, qué tensión y duración debe
> soportar el conjunto, qué elemento responde y cómo se recupera al corregirla?»
>
> **H-V5-CALIENTE — HUECO: conexión en caliente.** **Pregunta exacta:** «¿Se
> admite conectar el cordón con el ladrillo energizado y, si se admite, cuáles
> son los límites garantizados de corriente de entrada y transitorio, qué
> carga capacitiva admite el ladrillo y cómo deben comportarse los rieles
> durante la conexión?» La respuesta tiene que coincidir con
> H-V2-TRANSITORIOS y H-V2-RESERVA; no se presume que el conector lo permita.
>
> **H-V5-RECONEXION — HUECO: energía residual y rearranque.** **Pregunta
> exacta:** «¿Qué debe ocurrir al desconectar y reconectar con energía residual
> en la caja o rebote de contactos, qué condiciones habilitan el rearranque
> y qué límites temporales y eléctricos lo verifican?» La política es la de
> H-V2-RECUPERACION, pendiente de elección.
>
> **H-V5-CORTO — HUECO: fallo del cordón.** **Pregunta exacta:** «¿Qué debe
> ocurrir ante un corto entre los conductores o hacia el chasis, qué elemento
> limita o interrumpe, cuáles son sus límites de corriente y duración y cómo
> se recupera después del corto?» La evidencia debe incluir el tramo de cable
> expuesto al fallo; una protección situada después de ese tramo no demuestra
> por sí sola que lo proteja.
>
> **H-V5-INCOMPATIBLE — HUECO: adaptador ajeno al contrato.** **Pregunta
> exacta:** «¿Qué adaptadores incompatibles debe cubrir el contrato y, para
> cada incompatibilidad de tensión, polaridad o capacidad de entrega, qué
> comportamiento y límites de supervivencia se exigen, y quién los garantiza?»
> Que un adaptador pueda enchufarse no demuestra compatibilidad eléctrica.
>
> **H-V5-PE — HUECO: relevo de D-F5.** **Pregunta exacta:** «¿Qué relación
> tendrán el retorno DC del cordón, ★, `J5`, el chasis y PE, quién proporcionará
> el camino de modo común que D-F5 cerraba por chasis → PE → primario, y qué
> evidencia y ensayo del conjunto lo acreditarán preservando la separación
> de GNDD?» H-V2-AISLAMIENTO aporta la evidencia del ladrillo; por sí sola
> no contesta la relación con el chasis.
>
> **DECISIONES PENDIENTES:** elegir conector, polaridad, retención y cordón
> vinculante; decidir qué maniobras y adaptadores quedan admitidos o cubiertos,
> con su comportamiento de fallo y recuperación; definir retorno/chasis/PE y
> asignar el relevo de D-F5. Cada respuesta debe nombrar responsable físico,
> límites con fuente local y prueba de aceptación. Ninguna queda tomada aquí.

## 4. Los rieles de dentro

| riel | V | A | entrega | pierde |
|---|---|---|---|---|
| +12 rack (bus fila B + pantalla) | 12,00 | 1,050 | 12,60 W | 1,40 W |
| −12 rack (bus fila B) | 12,00 | 0,500 | 6,00 W | 1,06 W |
| +5 rack (bus fila B) | 5,00 | 0,500 | 2,50 W | 0,28 W |
| +5 digital (4 × N657 + host USB) | 5,00 | 2,895 | 14,47 W | 1,61 W |
| crudo +cascada (a `U1`) | 15,89 | 0,650 | 10,33 W | 1,82 W |
| crudo −cascada (a `U2`) | 15,89 | 0,650 | 10,33 W | 1,82 W |
| | | | **56,23 W** | **7,99 W** |

El +12 lleva dos cargas por cables distintos: el bus de la fila y la pantalla de
7" con su retorno dedicado, que es lo que pide `pantalla-motor`. Van juntas en
el convertidor y separadas en el cableado.

**Los tres rendimientos son ESTIMADO** y mueven los 7,99 W enteros. Es el único
término de este presupuesto que no está anclado a una hoja, y se cierra
eligiendo las piezas.

## 5. ~~El regalo: la tensión cruda cierra `U2`~~ Holgura para `U1` y D-F4 (D-V3)

> **ENMIENDA (2026-09-07, D-F9 · #335). El regalo llegó por otro lado, y esta
> sección publica cifras que su propio guion ya no produce.**
>
> El 06-09 —un día después de escribirse este papel, y con este papel sin
> firmar— se firmó **D-F9: `U2` pasa de LM2991 a LT3015**. La tabla de abajo la
> genera `ladrillo_budget.py`, que reusa `margen_budget.py` entero; al cambiar
> la pieza, su columna `margen U2` cambió sola:
>
> | crudo | margen `U2` publicado aquí | margen `U2` que da hoy el guion |
> |---|---|---|
> | 15,0 V | −170 mV | **+536 mV** |
> | 15,5 V | +311 mV | **+1017 mV** |
> | 16,0 V | +792 mV | **+1498 mV** |
>
> **Lo que esto le hace a D-V3: le quita el sujeto, no la razón.** `U2` ya no es
> el rojo que hay que cerrar —ya está cerrado a 15,0 V, sin tocar el crudo—, así
> que subirlo a 15,5 deja de comprar un cierre. Lo que sigue comprando es
> holgura en **`U1`**, que a 15,0 V es el peor riel con **+330 mV** sobre una
> incertidumbre de modelo de 127, y a 15,5 se va a +811.
>
> Y eso **cambia la pregunta**, porque este papel entero va de bajar calor: los
> ~~**+0,33 W** de D-V3 se pagaban por necesidad y ahora se pagarían por margen~~
> **+0,33 W publicados sólo contaban `U2`; el coste completo se precisa en la
> continuación del 2026-09-08**.
> Decidir si valen sigue siendo trabajo de la firma de esta v5; lo que ya no se
> puede es justificarlos con `U2`.
>
> **ENMIENDA (2026-09-08, D-V3 · `2026-09-08-junta-fuente-v5-dv1-dv5.md` §2). Continuación de la del 07-09:
> razón vigente y coste completo.** La corrección anterior de D-F9 se mantiene:
> `U2` es LT3015 y ya cerraba a **15,0 V con +536 mV**; a **15,5 V da +1017 mV**
> (`ladrillo_budget.py:178`, salida `:326`). No se necesita elevar el crudo
> para cerrar `U2`, ni se vuelve al LM2991.
>
> **Lo que compra ahora la propuesta:** holgura en `U1`, de **+330 a +811 mV**
> al pasar de **15,0 a 15,5 V** (`ladrillo_budget.py:178`, salida `:325`), y
> holgura para el detector de ventana de D-F4. Este tenía **+40 mV útiles**
> después de histéresis y error de umbral (papel v4, bloque D-F9, «Lo que
> cierra»; `hardware/01-power-supply/v4/secuencia_budget.py:198`). Esa cifra
> describe la v4; no fija ni garantiza un nuevo umbral para la v5. El aumento
> del margen de entrada alivia esa restricción en el modelo; su realización
> sigue necesitando la entrada y los transitorios de D-V2.
>
> **Lo que cuesta dentro de la caja, comparando el mismo extremo alto:**
> **+0,33 W en `U1` y +0,33 W en `U2`** (`ladrillo_budget.py:197`, `:211`),
> más **+0,12 W de conversión** (`:126`, `:136`, `:138`, `:147`) =
> **+0,78 W en total** (`:151`, `:160`). El presupuesto pasa de **63,43 a
> 64,22 W**; la diferencia se calcula antes de redondear, no restando esos
> extremos ya impresos. El coste usa el rendimiento **0,85 ESTIMADO** del
> crudo (`:103`) y la tolerancia **±2,5 % supuesta** (`:108`, `:115`): es el
> resultado del modelo, no una garantía de piezas aún sin elegir.
>
> **DECISIÓN PENDIENTE:** Samuel debe decidir si esa holgura para `U1` y D-F4
> vale el coste completo. ~~D-V3 sigue sin firmar.~~ **Decidido el 08-09: se
> acepta el vatio a cambio del margen; D-V3 queda FIRMADA y sin HUECOS.** Su
> nominal no acota el crudo
> durante un fallo: #334 sigue abierto y su pregunta está en H-V2-CORTO-DCDC.
> Las tachas del título, texto y tabla siguientes retiran la razón caduca y
> conservan su rastro; esta continuación amplía, no reemplaza, la del 07-09.

~~`U2`, el pre-regulador negativo, lleva desde el 2026-09-03 con **−170 mV** de
margen de entrada, y no tiene salida por piezas: ninguno de los candidatos de
D-F8 es una pieza negativa. El problema nunca fue `U2`. Es que un IRM de
catálogo entrega 15,0 V con ±2,5 %, y eso no alcanza.~~ El sujeto cambió con
D-F9; rige la razón de la enmienda anterior (2026-09-08).

Con un DC-DC nuestro, **la tensión cruda deja de ser un dato de catálogo y pasa
a ser una decisión**:

| crudo | le llega a U1/U2 | margen `U1` | margen `U2` | quema `U2` | |
|---|---|---|---|---|---|
| 15,0 V | 14,370 V | +330 mV | ~~**−170 mV**~~ **+536 mV** | 1,61 W | ~~la v4, y su rojo~~ v4 con D-F9 |
| **15,5 V** | 14,851 V | +811 mV | ~~**+311 mV**~~ **+1017 mV** | 1,94 W | **D-V3** |
| 16,0 V | 15,332 V | +1292 mV | ~~+792 mV~~ +1498 mV | 2,27 W | |

Corrección de la tabla, **2026-09-08**, por D-F9: cifras de la ejecución de
`ladrillo_budget.py:319`. «Quema `U2`» conserva su alcance local; no es el
coste térmico total de D-V3, desglosado en la enmienda.

**D-V3: el crudo de la cascada son 15,5 V.** ~~Cuesta **+0,33 W** en `U2`. Un
tercio de vatio por cerrar el único rojo que le queda a la fuente, y **con la
misma pieza**: el LM2991 que el #322 daba por insuficiente.~~ La propuesta
compra la holgura de `U1` y D-F4 descrita arriba, con el coste completo de la
enmienda del 2026-09-08, ~~pendiente de aceptación~~ **aceptada: D-V3 se
firmó el 2026-09-08 y no arrastra ningún HUECO (§9).**

Tres honestidades sobre esta tabla:

- El margen se aprieta en el corner **bajo** y el calor en el **alto**. No son
  el mismo, y el guion los calcula por separado a propósito.
- **La trampa no es esa, es comparar.** Al escribir la primera versión de este
  papel puse «1,94 W contra los 0,96 de hoy», que son **+0,98 W**: el corner
  alto del nuevo contra el bajo del viejo. En el mismo corner son **+0,33**.
  Por eso la columna de la derecha existe y se calcula con la misma función.
- La tolerancia de ±2,5 % es la de un IRM. ~~Un DC-DC nuestro debería hacerlo
  mejor, y entonces sobra margen. Se declara el conservador.~~ Es un supuesto
  de cálculo (`ladrillo_budget.py:108`, `:115`), no una tolerancia garantizada
  del sustituto sin pieza; H-V2-TRANSITORIOS exige acreditar su salida
  (enmienda del 2026-09-08).

## 6. Lo que le pasa a la caja

| escenario | calor del cajón | hay que abrir (chimenea sola) | con la pared contada |
|---|---|---|---|
| v4 declarada | 139,31 W | 21 355 mm² | 15 970 mm² |
| **v5 declarada** | **64,22 W** | **8 066 mm²** | 2 680 mm² |
| v5 a censo | 35,06 W | 2 906 mm² | 0 |

El encargo del #289 baja de **21 355 a 8 066 mm²**: un 62 % menos. Y eso cambia
la naturaleza de la obra, no solo su tamaño.

Con 8 066 mm² **el suelo puede quedarse macizo**. Corriendo la geometría con la
entrada donde está hoy y solo ensanchando la rendija del alero:

| rendija | v5 declarada | v5 a censo |
|---|---|---|
| 4 mm (hoy) | 45,6 K | 30,5 K |
| 20 mm | 27,8 K | 18,6 K |
| 30 mm | 25,6 K | 17,1 K |

Con la trasera agrandada a 20 000 mm², **sin tocar el suelo**:

| rendija | v5 declarada | v5 a censo |
|---|---|---|
| 20 mm | 21,1 K | 14,1 K |
| 25 mm | **19,0 K** | 12,7 K |
| 30 mm | 17,6 / 19,6 pesimista | 11,7 K |

**A 30 mm de rendija y con la trasera agrandada, la v5 declarada pasa el techo
de 20 K incluso con el `C_D` pesimista, y el suelo no se toca.** Esa era la
faena difícil: ranurar 18 mm de madera con puentes de 14,4.

> **Los 20 000 mm² de trasera caben, pero solo lo he comprobado en el plano.**
> El campo útil de la trasera va de y = 19,0 a y = 230,2, y la rejilla de hoy
> ocupa 41,8 mm de esos 211: 46 ranuras de 41,8 × 3,75, 7 065 mm². Llegar a
> 20 000 pide ranuras de ~118 mm de alto, que terminarían en y ≈ 143 y por
> tanto **por debajo del y = 157** donde `guarda_trasera_flexion()` ya declara
> su HUECO. Geométricamente entra. **Lo que NO he verificado es qué le hace a
> la rigidez del PMMA quitarle esa área**, y esa comprobación es del papel del
> case, no de éste. Hasta que se haga, la cifra de 20 000 es una hipótesis de
> trabajo y no un encargo.

Lo que la v5 **no** arregla: la rendija de 25-30 mm sigue arrastrando la franja
del anillo trasero de 23 a ~44 mm, que es el precio estético que Elke identificó
y que choca con «el marco es perfil, no banda». Eso sigue siendo una decisión
del papel del case, no de éste.

Y se va, además de calor:

- **la red entera** de la caja de madera: IEC, fusible, NTC, choke, MOV, Y2 al
  chasis, distancias de aislamiento. Es una clase entera de restricción.
- **el grueso del recinto de acero**, que hoy ocupa el 30 % del suelo. Queda la
  cascada, que es una placa, no un cajón.

## 7. Lo que esto reabre de la v4

| Qué | Por qué |
|---|---|
| **D-F1** | el listón se rehace: D-B2 sustituye 3,8/2,5/4,0 por 0,5/0,5/0,5 |
| **D-F2** (telemetría de rack) | los INA226 medían en los bornes de PS3/PS4; ahora miden a la salida de convertidores nuestros |
| **D-F4** (secuenciador) | usaba los pines ON/OFF de los Mean Well, que ya no están dentro |
| **D-F5** (Y2 al chasis) | **muere**: la red sale de la caja |
| **D-F7** (`PS5` → IRM-45-5) | muere por desaparición del sujeto |
| **§4.1** (fuga a PE) | se rehace: seis fugas menos dentro |
| `calor_budget.py` | su modelo entero es de módulos AC-DC en un recinto |
| `params.scad::potencia_disipada` | 139,31 → 64,22 |

**No se reabre la cascada.** `U1`/`U2`, los LT3045/LT3094 y `U3` se quedan donde
están, con su misma topología, alimentados por un crudo mejor.

### 7.1 Dos issues se quedan sin sujeto

Cruzado contra los issues abiertos, no contra la memoria:

- **#322** — «*hace falta un LDO negativo 300 mV mejor que el LM2991*». Pedía una
  pieza porque `U2` no llegaba con 15,0 V de crudo. **Con D-V3 llega con el
  LM2991 de hoy**: +311 mV. La búsqueda de pieza sobra. Muere por desaparición
  del sujeto, no por haberse resuelto.
  > **ENMIENDA (2026-09-07).** No murió: **se resolvió con pieza** el 06-09
  > (D-F9 · #335, LT3015), mientras este papel seguía sin firmar. La búsqueda no
  > sobró, y la pieza **sigue haciendo falta aunque se firme esta v5**: el §7
  > dice «no se reabre la cascada», así que con el LM2991 el `ON/OFF` seguiría
  > habilitando al revés que el LT1963A de D-F8 y el **#323** quedaría abierto.
  > El LT3015 lo cierra por construcción, y eso D-V3 no lo compra a ningún
  > precio de crudo.
- **#130** — «*la entrada de red del chasis no tiene pieza*». No hay entrada de
  red en el chasis. Muere entero.

Y **el PR #316** («el recinto partido, R cerrada y C a la vista») queda **medio
adoptado**: su mitad R se va del edificio, y su mitad C —la cascada fuera de un
cajón de acero— pasa a ser la respuesta a dónde vive lo que se queda. Conviene
leerlo antes de escribir el plan de esta v5, no después.

Ninguno de los tres se toca aquí: este papel no está firmado.

## 8. HUECOS

1. **Los tres rendimientos de los convertidores son ESTIMADO.** Mueven 7,99 de
   los 64,22 W declarados. Se cierran eligiendo las piezas.
2. **La pantalla de 7" sigue sin pieza.** `pantalla-motor` l.250-256 manda su
   fila «cuando la pieza tenga nombre». Entra con 550 mA de +12 V, que son
   6,6 W: no es un redondeo. Es una cita, no una hoja.
3. **#256 sigue abierto.** El digital entra por su máximo a TJ = 125 °C porque
   el punto de trabajo real (85 °C) no está publicado. Entre ese máximo y el
   típico hay **3,0 veces** de corriente.
4. **El coeficiente de la pared exterior sigue sin medir.** Con él, el venteo
   nuevo baja de 8 066 a 2 680 mm². Sin él, no se puede contar. `U_PARED_W_M2K`
   está fuera del veredicto a propósito y este papel no lo cambia.
5. **La cascada declara el doble de su censo.** D-F1 dice 650 mA/riel; el censo
   son 334. Son **20,65 W declarados contra 10,60 reales**, y con D-B2 firmada
   la cascada pasa a ser la línea más gorda del presupuesto. Merece la misma
   pregunta que se le hizo a la fila de abajo. **No se toca en este papel.**

## 9. Lo que hay que firmar

| | Qué | Dónde | Estado |
|---|---|---|---|
| **D-V1** | la etapa AC-DC es **pieza de catálogo certificada**, fuera de la caja; no un cajón nuestro | §3 | **FIRMADA 2026-09-08** |
| **D-V2** | el ladrillo son **24 V** | §3 | **FIRMADA 2026-09-08** — dirección; **7 HUECOS arrastrados** a §9.2 |
| **D-V3** | el crudo de la cascada son **15,5 V**, ~~y con eso `U2` cierra en +311 mV~~ para ganar holgura en `U1` y D-F4, con el coste completo de §5 | §5 | **FIRMADA 2026-09-08** — sin HUECOS |
| **D-V4** | los rieles se derivan **dentro** con DC-DC; la cascada no se toca | §4 | sin firmar — **no firmable aún**, ver junta §3 |
| **D-V5** | el cordón es de **dos hilos**; no bajan rieles hechos | §3 | **FIRMADA 2026-09-08** — dirección; **9 HUECOS arrastrados** a §9.2 |

> ### D-V1, FIRMADA — 2026-09-08
>
> **La etapa AC-DC es una pieza de catálogo certificada, fuera de la caja.** No
> se diseña, no se acaba y no se certifica un cajón de red propio.
>
> La junta la dictaminó **firmable tal cual**: es el «cómo» mínimo del «qué» que
> Samuel ya había decidido el 05-09, y no compromete ni la tensión del ladrillo
> (D-V2) ni el reparto de dentro (D-V4). Se firma sola, y por eso se firma antes.
>
> **Lo que arrastra:**
>
> - **El #130 pierde sujeto.** «La entrada de red del chasis no tiene pieza» deja
>   de tener pregunta: no hay entrada de red en el chasis. Lo que quedaba vivo de
>   ese issue era el recorte del IEC C14 en la chapa, y ese recorte no existe.
>   **No se cierra aquí**: la lista de defunción es una decisión aparte, como en
>   la v4.
> - **D-F7** (`PS5` = IRM-45-5) pierde sujeto, y **las piezas de D-F5** (el Y2 de
>   modo común por módulo) se van con los IRM. Sus obligaciones **no** se van con
>   ellas: necesitan relevo nombrado en D-V4 y D-V5.
>
> **Lo que esta firma NO compra**, y conviene que quede escrito porque el papel
> lo insinúa: la comparación de «0 W» contra un cajón externo multirriel **no
> está calculada** — el guion solo modela los DC-DC de dentro. La firma se
> sostiene sin ese número; el número sigue siendo HUECO.
>
> **Lo que sigue sin contestar bajo D-V1**: «certificada» no dice clase,
> aislamiento, corriente de fuga, protecciones ni carga capacitiva admisible.
> Eso es el contrato de D-V2 — ~~y por eso D-V2 no se firma todavía~~ y viaja
> como `H-V2-AISLAMIENTO` en §9.2 (D-V2 se firmó el mismo día, en dirección).

> ### D-V2, D-V3 y D-V5, FIRMADAS — 2026-09-08
>
> **Se firma la DIRECCIÓN, no el detalle.** El ladrillo son **24 V**, el crudo
> de la cascada son **15,5 V**, y el cordón es de **dos hilos**. Con eso queda
> fijada la topología de transporte y la tensión de cada nodo nominal.
>
> **Ningún HUECO se da por contestado.** Los **16** que dejaron los contratos
> del 08-09 —7 de D-V2 y 9 de D-V5— **no** se cierran con esta firma: pasan
> enteros a §9.2 como trabajo previo a fabricar, con su dueño. Firmar la
> dirección no es haber medido nada.
>
> **Precedente, y por qué se puede hacer así:** D-V1 se firmó ese mismo día
> dejando abierto su hueco de aislamiento y remitiéndolo a D-V2. Una decisión
> de arquitectura se firma cuando su dirección es correcta y su coste está
> entendido; los números de pieza son trabajo de ingeniería posterior, no
> requisito de la firma. Lo que **sí** sería fabricar sobre un hueco es llevar
> esto a cobre sin cerrar §9.2 antes.
>
> **D-V3 es distinta: no arrastra nada.** No le faltaba ningún dato — le
> faltaba una decisión de criterio. El coste está calculado (**+0,78 W**: 0,33
> en `U1`, 0,33 en `U2`, 0,12 de conversión) y la holgura también (`U1` de
> **+330 a +811 mV**, y aire para el detector de D-F4 que vivía con +40 mV
> útiles). Samuel acepta el vatio a cambio del margen. **Queda cerrada.**
>
> **Lo que estas tres firmas NO tocan:** **D-V4 sigue sin firmar** y sigue
> siendo el atasco — los dos bloqueantes de la junta (protección por riel y
> aislamiento de GNDD) no se resuelven aquí. Y **el #334 sigue abierto**: su
> pregunta viaja como `H-V2-CORTO-DCDC`. Que el nodo de fallo haya cambiado de
> origen no lo cierra.

### 9.2 Los 16 HUECOS que arrastran D-V2 y D-V5

Esta lista es **la condición de fabricación**, no una lista de deseos: ninguna
de las dos firmas autoriza cobre mientras tenga filas abiertas. El «dueño» sale
de cómo el propio contrato del 08-09 formula cada pregunta — *al fabricante*,
*a Samuel*, o sin destinatario, que es trabajo nuestro.

| HUECO | Qué falta | Dueño |
|---|---|---|
| `H-V2-ENTRADA` | ventana garantizada del ladrillo y de los DC-DC, con las caídas del cordón dentro | **fabricante** |
| `H-V2-SUBTENSION` | arranque, inhibición, histéresis y tiempos, y su coordinación con D-F4 | diseño |
| `H-V2-TRANSITORIOS` | envolvente admisible en cada interfaz, y quién limita lo que llega a los pre-reguladores | diseño |
| `H-V2-RESERVA` | carga capacitiva y corriente de arranque admisibles, contra lo que la cadena exige | **fabricante** |
| `H-V2-RECUPERACION` | política de rearranque, y estado de rieles durante la caída y la espera | **Samuel** + fabricante |
| `H-V2-CORTO-DCDC` | qué limita el corto entrada↔salida antes de `IN` de `U1` — **es el #334** | diseño |
| `H-V2-AISLAMIENTO` | clase, aislamiento y fuga de la referencia, con hoja o certificado | **fabricante** |
| `H-V5-CONECTOR` | pareja y polaridad, con hoja que acredite límites y resistencia de contacto | diseño |
| `H-V5-RETENCION` | retención y alivio de tracción, con su ensayo | diseño |
| `H-V5-CALIBRE` | calibre, longitud y resistencia total vinculantes | diseño |
| `H-V5-INVERSION` | qué pasa con polaridad inversa y qué elemento responde | diseño |
| `H-V5-CALIENTE` | si se admite conectar en caliente, y con qué límites | diseño |
| `H-V5-RECONEXION` | rearranque con energía residual o rebote de contactos | diseño |
| `H-V5-CORTO` | corto entre conductores o contra chasis, incluido el tramo de cable expuesto | diseño |
| `H-V5-INCOMPATIBLE` | qué adaptadores cubre el contrato y qué supervivencia se exige | **Samuel** + diseño |
| `H-V5-PE` | **relevo de D-F5**: quién da el camino de modo común, preservando GNDD | diseño + medida |

**Tres de estas filas no son independientes:** `H-V5-CALIENTE` tiene que
coincidir con `H-V2-TRANSITORIOS` y `H-V2-RESERVA`, y `H-V5-RECONEXION` sigue
la política que se elija en `H-V2-RECUPERACION`. Contestarlas por separado es
una forma de contradecirse.

Y una que este papel **no** propone y hay que decidir aparte: si la cascada
sigue declarando 650 mA/riel contra un censo de 334 (HUECO 5).
