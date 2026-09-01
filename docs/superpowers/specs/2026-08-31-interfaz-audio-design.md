# La interfaz de audio: un cuarto N657, dueño del reloj y única boca del instrumento — propuesta

**Fecha**: 2026-08-31 · **Estado**: **propuesto, pendiente de Samuel** ·
**Ejecuta**: A-6 (acta del 2026-08-30, papel del hub §6), que quedó declarada
sin diseñar · **Reabre**: D-P6 y el puerto invitado del motor, la tarjeta
trasera (#183), el presupuesto de potencia del módulo 1

---

## 0. Las actas

**A-6 (2026-08-30)**, la que abrió el subsistema, con las palabras de Samuel:

> *«ojo con esto, que la placa (osea el sintetizador, ahora tambien debe
> incorporar una interface de audio tipo claret++ 4pre»*

**A-10 (2026-08-31)**, la que este papel propone sellar:

> *«que te parece si hacemos que la interface de audio sea su propio n657
> tambien? igual que el mago»*

---

## 1. Por qué existe este papel

El papel del hub metió A-6 y **se negó a diseñarla ahí mismo**, con razón: es
un subsistema con su propia cadena analógica. Pero dejó la pregunta de dónde
vive planteada en dos opciones —«cuelga del hub» o «cuelga de la Voz»
(hub §6.2)— y **A-10 propone una tercera que ese papel no contempló**: ni una
ni otra, su propio chip.

Este papel dice por qué la tercera gana, qué le cuesta al instrumento, y las
cuatro cosas que hay que medir antes de firmarla.

---

## 2. Las cifras de la clase, contra la hoja

El §6 del hub mandó fijarlas **contra la hoja del producto de referencia y no
de memoria** (Principio I). Verificadas el 2026-08-31 en la página de producto
de Focusrite del Clarett+ 4Pre:

| | Clarett+ 4Pre |
|---|---|
| Preamplificadores de micrófono | **4** |
| Entradas / salidas | **8 in / 4 out** |
| Desglose de entradas | 4 mic pre · 2 Hi-Z JFET de instrumento · 4 de línea fija |
| Salidas | 4 balanceadas |
| Óptico | **ADAT, 8 canales de entrada** |
| Conversión | **24 bits / 192 kHz** |
| Auriculares | **2 salidas** |
| Enlace | USB-C |

**Lo que estas cifras dicen del diseño**, y es lo que manda: son **hasta 16
canales de entrada** (8 analógicos + 8 ADAT) y 4 de salida más dos de
auriculares, a 24 bits y 192 kHz. Eso no es «un ojo de cerradura estéreo con
más canales»: es otro orden de magnitud de flujo isócrono, con un reloj que no
puede temblar.

> **HUECO (Principio V).** El comportamiento del ADAT a 192 kHz —S/MUX reduce
> los canales por par óptico— **no está verificado aquí**. El número «16
> entradas simultáneas a 192 kHz» es el techo nominal, no el medido. Se cierra
> en §9.2 antes de dimensionar nada.

---

## 3. La decisión: un cuarto N657 (D-A1, PROPUESTA)

**La interfaz de audio vive en su propio STM32N657, en su propia placa.**

### 3.1 Por qué no es un argumento de cómputo

Hay que decirlo de frente porque es la razón que parece y no es: **por potencia
no hace falta**. El censo de pines del hub, corrido el 2026-08-30 con su
mutación (`hardware/02-midi-cv/micro_budget.py`, #213), cierra **con el audio
sentado encima**: VFBGA264, 71 pines repartidos, 75 libres, +48 tras lo vario.
Si el argumento fuera «no cabe», el argumento sería falso — sí cabe.

Y una interfaz de esta clase, vista solo como transporte, la mueve un chip de
un tercio del precio: SAI multicanal, USB HS, DMA y un reloj limpio.

**Quien firme esto tiene que firmarlo por las otras tres razones, no por ésta.**

### 3.2 El reloj, que ningún censo de pines ve

El hub va a estar tirando **ráfagas de DMA al framebuffer** de una pantalla de
800×480 (D2). El jitter que eso mete en el reloj de conversión no aparece en
ningún conteo de pines y **no se recupera después**: una muestra convertida en
el instante equivocado ya salió mal.

Un preamplificador de micrófono es, además, el sitio más sensible del
instrumento entero — más que el expo de la Voz, donde 1 mV son 3,6 cents
(voz-total E-1). Poner el reloj de audio en el mismo silicio que el vídeo es
pedirle al peor vecino que comparta cuarto con el más delicado.

### 3.3 La boca única, que es la decisión de verdad

Ésta es la razón que manda, y es de **topología, no de potencia**.

El §6.1 del hub dejó escrita la tensión: **la computadora no puede ver dos
dispositivos de audio del SAM17**. Una interfaz es un solo dispositivo
compuesto por un solo cable. Hoy hay dos candidatos —el puerto invitado del
motor y la interfaz nueva— y **añadir un chip no resuelve eso por sí solo: lo
empeora, porque pasa a haber tres**.

Lo que sí lo resuelve es decidir **quién es el único que habla audio al
mundo**, y ahí el chip propio da la respuesta limpia:

- La interfaz **es** la boca de audio del instrumento hacia la computadora.
- El puerto invitado del motor **se retira como dispositivo USB propio** y pasa
  a ser canales dentro del dispositivo compuesto.
- El MIDI y el protocolo siguen siendo del cerebro.

### 3.4 Esto ya estaba declarado, no es un camino nuevo

El motor-digital §6 lo dejó escrito el 2026-08-26, palabra por palabra:

> *«Unificar ambos en un dispositivo compuesto que reenvíe MIDI al cerebro por
> J2 es **evolución declarada** —con su presupuesto de trama— no v1.»*

A-10 **es** esa evolución. El papel del motor la previó, la nombró y la aplazó
por alcance; A-6 la volvió necesaria y A-10 le pone silicio. Lo que aquel papel
pedía para admitirla —**su presupuesto de trama**— sigue siendo el requisito, y
está en §9.3.

### 3.5 La NPU: lo que convierte «sobredimensionado» en la razón

Un N657 de interfaz de audio **no tiene la NPU muerta**. Tiene 600 GOPS al lado
del convertidor, en el único sitio del instrumento donde el audio del mundo
entra limpio y sin comprimir: supresión de ruido de sala, modelado de
preamplificadores, cancelación de realimentación.

Eso no lo hace ninguna interfaz de su clase, y no lo haría un chip «del tamaño
justo». Si el instrumento va a ser superior **como instrumento** y no solo en
cómputo, éste es un sitio donde la diferencia **se oye**.

> **No se promete nada aquí.** Que la NPU pueda correr un modelo de audio
> dentro del presupuesto de latencia de una interfaz es una **hipótesis**, no
> un número medido, y la frontera de la cámara ya nos enseñó la diferencia
> (hub §3.2, «modulación sí, disparo no»). Se mide en §9.4 antes de ponerlo en
> ningún material.

---

## 4. Lo que cuesta, en frío

Ninguna de estas cuatro es motivo para no hacerlo. Las cuatro son motivo para
**no firmarlo hoy**.

1. **Cuatro arranques desde XSPI.** El riesgo 8 del papel del hub ya avisaba
   con tres: el N657 no tiene flash interna, así que son cuatro flashes
   externas, cuatro binarios firmados y cuatro secuencias de FSBL. Esto crece
   lineal y no hay atajo.
2. ~~**El consumo, que no conocemos.**~~ **CORRIDO el 2026-08-31, y el
   resultado invierte el riesgo.** Ver §4.1.
3. **El phantom de 48 V.** Es un riel que el módulo 1 no tiene y que el
   presupuesto de potencia no conoce. Cuatro preamplificadores con phantom
   simultáneo es corriente real, no un detalle de BOM.
4. **La trasera crece otra vez.** #167 la dejó en aire, #183 la convirtió en
   nueve conectores, y esto le suma 4 combos XLR/TRS, 2 Hi-Z, 4 salidas
   balanceadas, 2 de auriculares y el óptico. El estudio del valle y la trasera
   capturada se acaban de dibujar: hay que contarlos contra ese dibujo, no
   contra el aire.

### 4.1 El consumo — rehecho contra DS14791 Rev 10, y el veredicto no cierra

> **Corrección propia (Principio VII).** La primera versión de esta sección
> (2026-08-31, temprano) daba «171,7 mW por chip» y «161,6 mA los cuatro», y
> concluía que el consumo sobraba. **Las dos cifras eran malas**, por dos
> razones que se corrigieron el mismo día:
>
> 1. **Se leyeron mal las columnas.** Las tablas son `Típ` seguido de varios
>    `Máx` (25/85/105/125 °C), no típicos por temperatura. El «206,7 mA típico
>    a 85 °C» era el **máximo a 25 °C**.
> 2. **Se usaron las tablas equivocadas.** Rev 10 las trae pareadas, «SMPS
>    external» y «SMPS internal», y este instrumento va con el **conmutado
>    interno** del chip (papel de la alimentación, D-R1).

Con el conmutado interno, ST publica `IDDSMPS`: lo que el chip pide **en el riel
de 1,8 V**, y **ya incluye el núcleo**. No hay eficiencia que estimar.

| Símbolo | Tabla (Rev 10) | Pág. | Típ | Máx (125 °C) |
|---|---|---|---|---|
| `IDDSMPS` | **39** | 154 | 99,93 mA | 757,3 mA |
| `IDDA1V8` | **36** | 151 | 2,67 mA | 3,12 mA |
| `IDDA1V8AON` | **38** | 153 | 0,45 mA | 0,56 mA |
| `IDD` | **32** | 147 | 0,27 mA | 0,40 mA |
| | **Total por chip** | | **103,3 mA** | **761,4 mA** |

**Y aquí está el problema: entre los dos extremos hay 7,4×**, y el punto que
decide —el **máximo a 85 °C**, que es donde vive el instrumento— **no está
publicado** para la configuración de SMPS interno.

Corrido (`power_budget.py`, camino D-R1: +5 V → buck → 3,3 V → LDO → 1,8 V):

| Caso | Duras + host USB | Techo | |
|---|---|---|---|
| **Típico**, 4 chips | 0,965 A | 2,82 A | cabe, con el árbitro recortando cadena |
| **Máx 125 °C**, 4 chips | 2,895 A | 2,82 A | **no cabe ni apagando todos los LED** |

**El presupuesto de la fuente con cuatro N657 no está cerrado.** El guion no da
verde ni rojo: sale con código 2 (HUECO) e imprime los dos extremos, porque
afirmar «no cabe» con el máximo de 125 °C sería afirmar más de lo que sabemos
—supone los cuatro chips a temperatura de unión máxima a la vez, y ahí el
problema sería térmico antes que eléctrico— y afirmar «cabe» con el típico sería
usar un típico como cota, que es el error que acabamos de corregir.

**Lo que esto le hace a D-A1:** el cuarto chip ya no es gratis. En el típico
entra; en el peor caso publicado, no. **Firmar D-A1 sin el máximo a 85 °C es
firmar contra un dato que no tenemos.**

**El riesgo real es otro, y es el que este papel tenía mal identificado.**

**El N657 no corre a 3,3 V.** Quiere **0,81 V para el núcleo** y 1,8 V para las
I/O y el analógico. El módulo 1 da +5 V y ±12 V, y el RP2350 vivía a 3,3 V:
esos dos rieles **no existen en el instrumento**, y hacen falta **por chip**.
Peor: la hoja da los máximos con la nota **«SMPS external»** — ST espera un
conmutado para el núcleo, y un riel de 0,81 V con 207 mA típicos y picos a
839 mA es un regulador de punto de carga de verdad, con transitorios rápidos.

Ahí es donde esto choca de frente con la doctrina heredada de D-P6 (§5):
**cuatro conmutadas dentro del mismo cajón donde 1 mV son 3,6 cents**, y ahora
además con preamplificadores de micrófono al lado. El problema de D-A1 no es
que la fuente no dé la corriente. Es que **la solución de alimentación del
propio chip mete conmutación en el cuarto limpio**, y eso ningún presupuesto de
potencia lo mide.

> **HUECO (Principio V), y es grande.** Todas esas cifras son **con CoreMark**.
> **No hay una sola cifra de consumo con la NPU trabajando** — ni en Run mode ni
> en ningún sitio de la hoja. El mago vive de la NPU y §3.5 se la quiere dar
> también a la interfaz: el consumo de los dos chips **en el modo en que los
> pensamos usar** sigue sin número. `power_budget.py` lo imprime como HUECO y
> sale con código 2 en vez de dar un verde falso.

---

## 5. Corrección al §6.1 del papel del hub (Principio VII)

El §6.1 dice: *«D-P6 ya es "USB audio hacia la computadora": un invitado UAC2
asíncrono con endpoint de feedback…»*. **Es incorrecto, y el error es mío al
redactarlo el 2026-08-30.**

D-P6 (motor-digital §6) es **la doctrina de masa como puerta**:

> *«ningún conector del mundo toca la placa de la Voz. El conector del invitado
> vive en la tarjeta de E/S trasera (#183), y cruza hacia adentro aislado
> galvánicamente: USB HS con aislador clase ISOUSB211 (480 Mb/s).»*

La diferencia importa para este papel: **D-P6 no se retira con A-10, se
hereda**. La interfaz de audio es precisamente donde esa doctrina más aprieta
—un preamplificador de micrófono es más sensible que el expo de la Voz— así que
el aislamiento galvánico y el «ningún conector del mundo toca la placa
sensible» pasan a ser **la frontera de la interfaz**, no un detalle del
invitado. Lo que sí se retira es el **puerto invitado como dispositivo USB
propio** (§3.3), que es otra cosa y vive unas líneas más arriba en ese mismo §6.

---

## 6. Lo que este papel NO decide

- **La cadena analógica**: preamplificadores, conversores, topología de
  ganancia, phantom. Es su propia junta, con piezas y hoja.
- **La pieza del conversor.** Sin hoja en el árbol no hay nombre (R-M3).
- **Si el ADAT entra en la v1.** Depende de §9.2 y de la trasera.
- **El nombre del módulo.** Aquí es «la interfaz» por su trabajo.
- **Si la NPU entra en la v1** (§3.5): depende de §9.4.

---

## 7. Enmiendas mandadas, con dueño

Ninguna se ejecuta hasta que D-A1 se firme (patrón conocido: #214, #248).

| Papel | Sección | Qué cambia | Estado |
|---|---|---|---|
| `2026-08-30-hub-n657-y-radios-design.md` | §6.1 | La cita de D-P6 es incorrecta: es la doctrina de masa, no el USB audio (§5 de aquí) | pendiente |
| ídem | §6.2 | «Si cuelga del hub / si cuelga de la Voz» → tercera opción, sellada en D-A1 | pendiente |
| ídem | §10 fila 8 | «Cifras del Clarett+ contra la hoja» → **CORRIDA** (§2 de aquí) | pendiente |
| ídem | §11 riesgo 5 | «La computadora ve dos dispositivos» → cerrado por §3.3 | pendiente |
| ídem | §11 riesgo 8 | Tres arranques XSPI → **cuatro** | pendiente |
| `2026-08-26-motor-digital-design.md` | §6 | El puerto invitado deja de ser dispositivo USB propio; la evolución declarada se ejecuta | pendiente |
| `hardware/02-midi-cv/power_budget.py` | — | Riel de phantom de 48 V y consumo de cuatro N657 | bloqueado por #249 |
| #183 | — | La trasera gana los conectores de §4.4 | issue |

---

## 8. Lo que hay que correr o verificar antes de sellar

1. **El máximo de `IDDSMPS` a 85 °C**, que Rev 10 no publica (§4.1). Es el
   único número que cierra el presupuesto de la fuente con cuatro chips: hoy
   entre típico y máximo hay 7,4× y el veredicto queda en HUECO. **Sale de ST o
   de medirlo en la Discovery (#231), y es prerrequisito de firmar D-A1.**
   Además, y en el mismo papel de la alimentación:
   el **convertidor de punto de carga** de 0,81 V y 1,8 V —pieza, hoja,
   rendimiento real— y **dónde se pone su conmutación** para que no entre en
   el cuarto limpio. Ése es el prerrequisito duro de verdad.
1bis. **El consumo con la NPU activa**, que DS14791 no caracteriza (HUECO de
   §4.1). Sin él, ni el mago ni §3.5 tienen presupuesto.
2. **El ADAT a 192 kHz**: cuántos canales sobreviven al S/MUX, contra la
   norma. Cierra el HUECO de §2.
3. **El presupuesto de trama del dispositivo compuesto** — lo que el motor
   §6 exigía para admitir la unificación: MIDI reenviado al cerebro por J2,
   con su latencia y su cota escrita antes de medir.
4. **La NPU dentro del presupuesto de latencia de una interfaz**, medido en
   bring-up. Sin esto, §3.5 no se pone en ningún material.
5. **Cuántos canales por bloque SAI** da el N657 (SAI1 y SAI2 están en la
   tabla de pines), contra la hoja: decide si 16 entradas caben en un chip.
6. **Censo de pines y de SRAM de la interfaz**, con su mutación, como se hizo
   con el hub.
7. **Los conectores contra el estudio del valle** y la trasera capturada.

---

## 9. Riesgos

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | **Cuatro N657 no caben en el presupuesto de la fuente** — sigue ABIERTO | §4.1: en típico caben (0,965 A contra 2,82 A); en el máximo publicado **no** (2,895 A). Falta el máximo a 85 °C, que es el que decide |
| 1b | **Cuatro conmutadas de punto de carga dentro del cuarto limpio** — el riesgo que sustituye al 1, y el que puede tumbar el papel | Pieza y hoja del DC/DC elegidas, y su sitio decidido contra la doctrina de D-P6 (§8.1) |
| 1c | El consumo con la NPU activa no existe en la hoja | §8.1bis; hoy `power_budget.py` sale con código 2 por esto |
| 2 | Cuatro arranques desde XSPI, cuatro binarios firmados | El bring-up sale del mismo #231 |
| 3 | El dispositivo compuesto añade latencia al MIDI, que hoy es del cerebro | §8.3 medido con cota escrita antes |
| 4 | La NPU se promete y la latencia no la permite | §8.4 antes de prometerlo; misma lección que hub §3.2 |
| 5 | 16 entradas no caben en los SAI de un solo N657 | §8.5 contra la hoja |
| 6 | El phantom mete su conmutación en el cuarto limpio | Doctrina de D-P6 heredada (§5), verificada en el dibujo |
| 7 | La trasera no tiene sitio físico para todo esto | §8.7 contra el valle |
