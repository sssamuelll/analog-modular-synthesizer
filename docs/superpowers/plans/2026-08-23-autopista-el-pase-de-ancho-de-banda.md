# La autopista: el pase de ancho de banda, carril por carril

**Estado: PROPUESTA.** Encargo de Samuel el 2026-08-23:

> *«nosotros somos un ferrari corriendo a todo dar por la autobahn, como ningun
> otro puede y eso es lo que necesito, el mas minimo tiempo de latencia de todo
> el mercado»* — y después: *«vamos a rediseñar todo lo que sea necesario hasta
> que todo sea una gran autopista»*.

Este papel recorre **todos los enlaces del instrumento**, mide cada uno, y dice
qué se rediseña. Donde hay número, va el número; donde no, va POR_CONFIRMAR con
la medición que lo cierra.

---

## 0. La regla que ordena el pase

Salió de medir el primer carril y vale para todos:

> **La latencia de una etapa periódica no es lo que tarda en transmitir: es su
> período.** Una trama de 288 bits sale en 28,8 µs a 10 MHz. Si sale una cada
> 10 ms, la latencia son 10 ms. El cable puede estar vacío al 97 % y el
> instrumento ir lento.

Por eso ningún carril se arregla «ensanchando el cable». Se arreglan en **este
orden**, y la escalera importa porque los tres primeros peldaños son gratis:

1. **No mandes.** El envío más rápido es el que no ocurre.
2. **Agrupa.** Un dato por trama desperdicia la dirección y el comando.
3. **Acelera.** Sube la cadencia — pero solo después de 1 y 2, porque
   acelerar sin agrupar multiplica el desperdicio.

Y el corolario que este pase demuestra dos veces: **cuando arreglas un carril,
el cuello se muda.** Hay que volver a medir, no suponer.

---

## 1. Carril mano → cerebro — **el cuello real, y no era el bus**

**Hoy:** no existe. El contrato J2 congelado es solo escritura hacia los DACs;
el `MISO` está físicamente presente (pin 4 del bus, con resistencia de serie y
pull-down) y en la ranura del VCO lo ocupa la cadena de DACs (`U7.SDO→MISO`).
El módulo de mandos tendría **su propia ranura**, así que ahí el `MISO` es
suyo — y R-J1 ya legisla que lo suelta quien hable en esa ranura.

**Medido** (`hardware/02-midi-cv/latencia_mano_budget.py`, nuevo y bloqueante):

| Lazo | Total peor caso | Bus | Barrido | |
|---|---|---|---|---|
| 2 kHz | 1,154 ms | 10,9 % | 3,03× | lento |
| **4 kHz** | **0,654 ms** | **21,8 %** | **1,52×** | **OK** |
| 8 kHz | 0,404 ms | 43,5 % | 0,76× | **no barre** |

**El hallazgo:** a 8 kHz el bus va sobrado y **el barrido de potes ya no da**.
El cuello no es el cable: es el escaneo analógico.

Desglose del peor caso a 4 kHz — barrido 0,250 · sondeo 0,250 · transmisión
0,054 · render 0,100 ms.

**Rediseño:**

- **Muxes en paralelo, no en fila.** Con 3 muxes sobre 3 entradas de ADC, todos
  reciben la misma dirección y **asientan a la vez**: el asentamiento se paga
  una vez por paso y se reparte. 45 potes = 15 pasos × (5 µs + 3×2 µs) =
  **165 µs**, contra 315 µs secuencial. *(La v1 de este presupuesto modeló el
  barrido secuencial y estaba mal; queda corregido y dicho.)*
- **Bloque de vuelta agrupado**, no un pote por trama: 256 bits de deltas +
  cabecera, en la misma vuelta del lazo que la escritura.
- **Cadencia 4 kHz** como suelo declarado, con la puerta puesta.

**POR_CONFIRMAR, y manda:** el asentamiento real (mux + impedancia del pote
contra el condensador de muestreo) y la tasa del SAR del RP2350B, que **el repo
no documenta**. Con 1,52× de holgura no hay sitio para sorpresas. Si no da:
más muxes en paralelo (hay 8 entradas analógicas), o barrido en mitades
alternas para los potes que nadie está tocando.

## 2. Carril cerebro → módulos — **agrupar, y R-M4 deja de ser una excepción**

**Hoy:** un parámetro por trama de 72 bits. 16 voces × 3 dimensiones × 100 Hz =
4.800 tramas/s = **3,46 %** del bus. La excepción es el tono, que ya se agrupó:
16 × 16 bits + cabecera a 1 kHz = **2,88 %** — *diez veces más rápido y más
barato*, porque agrupa (R-M4).

**Rediseño: R-M4 deja de ser la ley del tono y pasa a ser la ley de la casa.**

> Todo módulo declara sus parámetros en **bloques agrupados con su tasa**. Un
> parámetro por trama queda prohibido salvo para lo que cambia de higos a
> brevas (registros de configuración, selectores).

La cuenta que lo justifica está aseverada: los mismos 16 parámetros sueltos a
4 kHz cuestan **56,3 %** del bus; agrupados, **21,8 %**, contra un techo
declarado del 50 %. **La agrupación compra la velocidad, no el reloj.**

**[corregido 2026-08-24]** Esta línea publicaba **46,1 %**, y era una cifra
sesgada a favor de lo que defiende: el assert de `latencia_mano_budget.py`
cargaba los 256 bits del sondeo del panel al lado **agrupado** y no al suelto,
o sea comparaba payloads distintos. Peor, la cadencia se cancelaba en los dos
lados, así que la desigualdad real era `1152 > 544` — cierta para cualquier
reloj y cualquier lazo, y por tanto **un assert que no podía fallar**. Lo cazó
la junta adversarial (Serrano, hallazgo 8). Con el sondeo cargado a las dos
configuraciones, los sueltos son 1408 bits por giro (56,3 %) y el agrupado 544
(21,8 %). El assert nuevo sí puede fallar, y el guion imprime las tres
condiciones que lo ponen rojo: J2 ≥ 11,26 MHz, lazo por debajo de 3,6 kHz, o
techo de bus por encima del 56,3 %.

**Deuda:** `trama_j2_budget.py` — el árbitro que suma todos los módulos con su
tasa declarada y **falla si un módulo no declara la suya** — está declarado en
el spec de orquestación §10 y **no existe** (issue #180).

**POR_CONFIRMAR:** los 10 MHz son el techo del contrato congelado; el máximo
real del AD5686R **nunca se leyó de la hoja** (tres intentos con timeout, issue
abierto). Si el chip aguanta más, la autopista es más ancha todavía — pero eso
hoy no se sabe y no se usa.

## 3. Carril cerebro ↔ carcasas — **el peor de todos, y el que nadie miró**

**Hoy:** el descriptor sale por SysEx sobre USB-MIDI, un sobre por descriptor.
Dos pérdidas que se multiplican:

- **USB-MIDI son 3 bytes útiles por paquete de 4** (el primero es cabecera de
  cable y CIN).
- **SysEx obliga a 7 bits por byte**: 8 bytes de cable por cada 7 de dato.

Eficiencia combinada: **≈ 65 %**, sin contar el sobre por descriptor. Con 536
descriptores el volcado son **miles de mensajes diminutos**, y cuánto tarda lo
decide **la política de agendado del host, no el firmware** — entre décimas de
segundo y decenas, contra un objetivo declarado de arranque en menos de 3 s
que ningún guion asevera (`arranque_budget.py`, declarado bloqueante, no
existe).

Y encima el volcado **se aborta entero y en silencio** si un descriptor pasa de
256 bytes — issue #182, punto 5. Un enumerado de 16 opciones ya son 248.

**Rediseño, por la escalera del §0:**

1. **No mandes: el descriptor se cachea con su huella.** El instrumento publica
   una **huella corta** (hash del descriptor completo + versión). La carcasa
   guarda el volcado en disco. Si la huella coincide, **no se manda nada**. El
   descriptor solo cambia cuando cambian los módulos, o sea casi nunca. *Este
   es el peldaño que hace irrelevantes a los otros dos, y es el que convierte
   el arranque de segundos en milisegundos.*
2. **Agrupa: cuando sí haya que mandarlo, va por un canal binario crudo** —
   endpoint bulk de 64 bytes, sin codificación de 7 bits y sin un sobre por
   entrada. Recupera el 35 % que la codificación tira, y cambia miles de
   mensajitos por un flujo.
3. Y con eso, **acelerar no hace falta**.

**Y tres arreglos de contrato que van en el mismo pase**, porque sin ellos el
otro lado no puede confiar en lo que recibe: conteo de entradas al principio,
terminador al final, y **largo por entrada** — hoy el cliente no puede
distinguir «terminó» de «se abortó» de «todavía viene».

**Nota cruzada que nadie había sumado:** el acta E-7 dimensionó la memoria a
100 bytes por entrada **precisamente para que el descriptor documente al
agente**. Eso multiplica el volcado por 2,4×. La huella del punto 1 es lo que
permite tener las dos cosas: descriptores ricos **y** arranque instantáneo.

## 4. Carril interno: el buzón — **desborda hoy, en silencio**

`MAX_RESPUESTAS = 4` contra caminos que producen hasta 16, con todos los envíos
descartando el error. Ya está documentado con evidencia en **#182** (puntos 1,
3 y 4): `Reactivar` sin id pierde doce avisos, el tick pierde doce `CHANGED` con
cinco rampas —divergencia permanente de las vistas— y las cinco medidas del
reloj nunca se publican.

**Rediseño:** dimensionar contra el fan-out real (16, no 4), y **prohibir el
descarte silencioso**: un envío que no cabe es un error con nombre, nunca un
`let _`. Es la misma disciplina que el resto del repo aplica a los presupuestos.

## 5. Carril de las pieles: un solo suscriptor — **#145**

`suscrito: bool`, y `atender()` devuelve respuestas **sin destinatario**. Con un
transporte, singular y plural son indistinguibles; con dos, las pieles divergen
y la que habló de último se vuelve la fuente de verdad — justo lo que la
doctrina dice que este mecanismo impide.

**Rediseño:** conjunto de suscriptores con identidad, y encaminamiento de
salida. Y ojo con la trampa que la junta cazó: **un cliente puede escribir sin
suscribirse (el panel) y suscribirse sin escribir (la pantalla)**. La puerta de
entrada y el encaminamiento de salida son **dos ejes distintos**; saber por
dónde entró algo no dice a dónde va la respuesta.

## 6. Carril de arranque — **el que cierra o no cierra el objetivo de 3 s**

Se compone de: barrido I²C de las ocho ranuras + construcción del descriptor +
volcado a las carcasas (§3) + lectura de la política, si la hay.

Con la huella del §3, el volcado sale de la ruta crítica y quedan el barrido y
la construcción. **`arranque_budget.py` sigue sin existir**, y es lo que
convierte los <3 s en puerta.

**Y trae un riesgo que no es de velocidad:** hoy el instrumento se construye
antes de montar el USB, así que la ventana es cero. Cuando el arranque gane el
barrido y la lectura de política, esa ventana pasa a ser de cientos de ms — y
**quién gana la carrera lo decide el host**. Con «tabla vacía = todo
permitido», un CRC malo, un mux trabado o una ranura vacía dan **acceso total y
silencioso, indistinguible del estado de fábrica**. Se resuelve declarando el
estado de arranque en voz alta, no por omisión.

---

## 7. El cuadro, de un vistazo

| Carril | Hoy | Después | Peldaño |
|---|---|---|---|
| Mano → cerebro | no existe | 0,654 ms, 21,8 % del bus | agrupar + acelerar |
| Cerebro → módulos | 1 parámetro/trama | bloques declarados (R-M4 general) | agrupar |
| Cerebro ↔ carcasas | SysEx, ≈65 % útil, miles de mensajes | huella + caché; bulk crudo si toca | **no mandes** |
| Buzón interno | 4, desborda mudo | 16, sin descarte silencioso | — |
| Pieles | una | conjunto con encaminamiento | — |
| Arranque | sin medir | huella lo saca de la ruta crítica | **no mandes** |

## 8. Lo honesto sobre «la latencia más baja del mercado»

- **Aritmética sólida:** un note-on por MIDI DIN son **960 µs solo en entrar
  por la puerta** (3 bytes a 31250 baudios). Es el suelo de cualquier
  instrumento cuyo control externo sea MIDI DIN. Nosotros llegamos al DAC en
  **654 µs**, y el camino del panel no pasa por MIDI.
- **Lo que no se puede prometer:** contra una perilla de un analógico puro no
  gana nadie — esa perilla es una resistencia en el circuito y su latencia es
  cero por física. Lo alcanzable es **ser imperceptible mientras se hace todo
  lo que esa perilla no puede** (recordar, presets, agente).
- **Lo que NO se declara sin medir:** ninguna comparación contra un
  instrumento concreto. Eso se mide con osciloscopio o no se dice. Va a la
  lista de mediciones, no al papel.

## 9. Las decisiones de Samuel

> **TOMADAS el 2026-08-24.** Lo de abajo se queda como el razonamiento. Dos
> de estas cambiaron AL VERIFICARLAS, y las dos por el mismo motivo: nadie
> habia corrido el modelo variando lo que se podia variar.

| # | Decision | |
|---|---|---|
| **B1** | **Barrido 4 kHz, lazo DESACOPLADO** — 8 kHz, el mas rapido que el bus aguanta. **0,529 ms** peor caso contra 0,654 acoplado: 125 us que no cuestan cobre. | **cambio** |
| **B2** | R-M4 se eleva a **ley de la casa**: todo modulo declara bloques con su tasa, y `trama_j2_budget.py` es su puerta. | |
| **B3** | **La huella Y el contrato, juntos**, y recoge N4: conteo de entradas, terminador y largo por entrada. Rompe el formato, asi que N7 va antes. | **EN EL COBRE (a medias)** |
| **B4** | El canal binario crudo **solo si tras medir la huella sigue doliendo**. Sin el contrato de B3 no arreglaria nada de todos modos. | |
| **B5** | Arranque **permisivo, pero DICHO**. Es N6 del papel del nucleo, misma decision. | |

> **B3 aterrizo el 2026-08-24, y aterrizo la mitad que valia.** La huella esta
> en `Modelo::huella()` y viaja **en el saludo**, no en un mensaje propio: asi
> la carcasa la sabe al conectarse y decide si pedir `Describe` sin gastar un
> viaje en preguntarlo. Se calcula sobre la SERIALIZACION de cada descriptor
> —no sobre sus campos— para que cualquier campo nuevo la mueva sin que nadie
> se acuerde, y **no depende del orden de registro**, que importa mas de lo que
> parece: los descriptores de modulo llegan por I2C y el orden del barrido no
> esta garantizado.
>
> Del contrato entraron **dos de tres**: cabecera con la cuenta y cierre con
> los enviados. El **largo por entrada** no entro y no por olvido -- sobre
> SysEx cada descriptor ya viaja en su propio sobre, que lo delimita. Hace
> falta cuando el volcado vaya por el canal crudo, o sea que es de B4.
>
> Y el formato del descriptor **sigue sin tocarse**: un descriptor sigue
> midiendo 250 de 256 en el peor caso declarado, y su test sigue en rojo con
> `ignore`. Lo que cambio es que saltarselo ya no es invisible.

> **Por que B1 cambio.** `cadena(f_barrido, f_lazo)` siempre acepto dos
> frecuencias y `main()` la llamaba con el mismo numero para las dos. Son
> etapas con techos distintos: al barrido lo limita el analogico, al lazo lo
> limita el bus. Separarlas era gratis y nadie lo habia hecho.
>
> **Y dos numeros se cerraron de paso.** La conversion del ADC era
> POR_CONFIRMAR y salio **CITADA** de la hoja del RP2350, p. 1071: 96 ciclos a
> 48 MHz = **2 us exactos**. El valor de trabajo era correcto, no conservador,
> asi que ahi no hay margen que rascar. Y **mas muxes no es la salida**: de 3
> a 8 el barrido solo baja de 165 a 126 us y 8 kHz sigue sin caber, porque las
> conversiones van en fila por un unico convertidor. La unica palanca que
> queda sobre el barrido es el asentamiento del mux, que sigue sin medir.
>
> **El techo del lazo, para que no se vuelva a proponer:** a 9,19 kHz el J2
> llega al 50 % declarado. Proponer 16 kHz —como se hizo en esta misma
> sesion— lo pone al 87 %.


- **B1 — La cadencia del lazo:** 4 kHz (0,654 ms, 22 % del bus, 1,52× de
  barrido) o forzar 8 kHz añadiendo muxes en paralelo para que el barrido dé.
  Recomendado: **4 kHz**, y subir solo si la medición del asentamiento sale
  generosa.
- **B2 — R-M4 general:** ¿se eleva a ley de la casa (todo módulo declara
  bloques con su tasa) en este pase, o módulo por módulo? Recomendado:
  **ley**, con `trama_j2_budget.py` como su puerta.
- **B3 — La huella del descriptor:** es el cambio de mayor rendimiento de todo
  el pase y toca el contrato con las carcasas. ¿Entra ya?

  **Y ahora también carga el contrato del volcado.** El papel del núcleo le
  cedió N4 en su v3: conteo de entradas, terminador y largo por entrada se
  deciden **aquí**, no allá. El razonamiento de la cesión es que decidir el
  formato sin saber si el descriptor se va a mandar casi nunca es decidir a
  ciegas — y eso lo responde la huella, que es esta misma decisión.

  **Esto dejó de ser holgado.** MEDIDO el 2026-08-24: el descriptor compilado
  más grande son 106 B de 256 (41 %), pero el **peor caso que el propio repo
  declara** —el selector de 17 fuentes con nombres y etiquetas realistas—
  mide **250 B de 256, el 98 %**. El test vive en `core/src/descriptor.rs`
  (`el_peor_caso_declarado_cabe_en_el_volcado`), está en rojo de verdad y
  marcado `#[ignore]` esperando esta decisión. Un descriptor que no quepa hoy
  se salta con un `warn!` y el cliente **no puede enterarse**, porque no hay
  conteo ni terminador con que notarlo — que es exactamente lo que B3 y B4
  tienen que resolver juntos.

- **B4 — El canal crudo para el volcado:** ¿se añade el endpoint binario, o se
  vive con SysEx confiando en que la huella haga que casi nunca se use?
  Recomendado: **la huella primero**; el canal crudo solo si tras medirla sigue
  doliendo.

  Ojo con el orden: si la huella (B3) entra y el volcado sigue sin conteo ni
  terminador, el canal crudo no arregla nada — el cliente seguiría sin poder
  distinguir «terminó» de «se abortó». El contrato es prerrequisito del
  canal, no al revés.

- **B5 — El estado de arranque:** ¿permisivo declarado (coherente con «tabla
  vacía = todo abierto») o cerrado hasta que la política cargue? Recomendado:
  **permisivo, pero DICHO** — y con telemetría de por qué, para que un fallo de
  EEPROM no se disfrace de fábrica.

## 10. Lo que este pase deja abierto

El motor de aterrizaje ya tiene domicilio gracias al §2 (agrupar y subir la
tasa de los parámetros que planean, igual que se hizo con el tono) — **no hace
falta enmendar R-M1**. Lo que sigue sin resolver es el jitter del lazo, el
asentamiento del DAC, y la reconstrucción analógica: **el filtro que borra los
escalones es latencia también, y es el suelo duro**. Ninguno de los tres tiene
número, y los tres entran en la lista de mediciones del panel.
