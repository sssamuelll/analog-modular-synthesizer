# Módulo 3 v2 — VCO ×8 en tres placas, con todos los juguetes

> Sustituye a [`2026-08-16-modulo-3-vco-design.md`](2026-08-16-modulo-3-vco-design.md).
> Origen: #158 — el instrumento se diseña para ocho voces.
> Contrato que produce: [`2026-08-22-contrato-modulo-voz-design.md`](2026-08-22-contrato-modulo-voz-design.md).

## 0. Qué cambia, y por qué sale barato cambiarlo ahora

La v1 —cuatro voces en una placa de 114 × 124 mm— **nunca se fabricó**. Su
`notes/medidas.csv` tiene 65 filas y **cero medidas**: el trabajo llegó hasta el
check de gerbers, que el repositorio describe como «el último paso antes del
dinero», y ahí paró. Ninguna placa de este proyecto se ha fabricado todavía.

Eso convierte este rediseño en una decisión de papel contra papel. Lo que se
conserva de la v1 no es una placa: es un **layout validado** (reparto 2×2 de
voces, plano de masa medido, escapes del QFN, DRC en 0) y **cuatro presupuestos
ejecutables**. Los dos se reutilizan.

## 1. Objetivo

Ocho voces analógicas gobernadas por números, en tres placas que caben en un
panel de 3U sin comerse medio instrumento, con el módulo midiéndose a sí mismo
y con todo lo que el SSI2130 trae latente puesto a trabajar.

Objetivo medible, heredado y ampliado: **las 7 octavas de cada una de las ocho
voces dentro del rango del convertidor, sin trimmers**, y **la escala del jack
de CV externo dentro de 3 cents por octava**.

## 2. Decisiones fijadas (con Samuel, 2026-08-22)

1. **Ocho voces**, y el módulo las mide a sí mismo. Las cuatro líneas
   `TUNE_OUT` de los pines 9-12 del J2 quedan sin usar; los números vuelven por
   `MISO`. **El contrato del J2 no cambia ni un pin** (núcleo §5.3).
2. **Un micro en el módulo.** Cronometra los ocho osciladores con PIO —el mismo
   conteo recíproco que el cerebro hace hoy—, lee las entradas de control,
   sensa los jacks, lleva la cadena de LED y gobierna el enrutado de sync.
3. **Del J2 cuelga el micro, no los chips** (regla 2 del contrato). El cerebro
   le habla al micro; el micro habla con sus conversores por un SPI **privado**,
   dentro del módulo. Esto **cierra un hueco que el spec del cerebro daba por
   perdido**: su §4.1 dice que el requisito de soltar el `MISO` con `CS` alto
   *«vive en placas que todavía no se han dibujado — salvo una, que ya está en
   gerbers y nunca leyó este documento»*. Esa placa es la v1 de este módulo, y
   aquí se rehace. Consecuencias: se acaba la pelea por el `MISO` en vez de
   hacerse sobrevivible, la trama de 72 bits deja de estar clavada en el
   contrato del J2 —era el tamaño de la cadena de tres conversores de la v1,
   un número de una placa metido en una interfaz común— y **cuántos
   conversores lleva el módulo deja de ser asunto de nadie de fuera**.
4. **Tres placas paralelas al panel, todas de 4 capas**, y **un solo módulo**:
   una identidad, un `CS`, un micro, una referencia.
5. **16 jacks**: entrada de control y salida por cada voz.
6. **Las entradas de control van encadenadas.** El pin de normalizado de cada
   jack alimenta al siguiente en vez de ir a masa. Un cable manda sobre todas
   las de abajo; dos cables hacen dos bancos; ocho dan control individual.
   Sustituye a la v1, donde ese pin existía atado a masa —el mecanismo puesto y
   sin usar—, y aplica al módulo 3 la doctrina que `architecture-poly.md` §6 ya
   había escrito para el instrumento.
7. **El cable siempre gana.** Cualquier ruta que el cerebro decida se rompe al
   meter un cable en el jack, y el cerebro **se entera** porque el jack está
   sensado. No es lógica nueva: es el muelle del conector haciendo lo suyo.
8. **El patrón completo del núcleo §10**: sensado de ocupación en los 16 jacks,
   lectura por ADC de las 8 entradas de control, un LED por jack, EEPROM de
   identidad, y telemetría térmica ampliada.
9. **Exactitud, tres correcciones** (§5): la resistencia de escala, la
   compensación de agudos y la histéresis del comparador de PWM.
10. **Los juguetes** (§7), todo lo que el chip trae y la v1 dejó dormido: sync
   entre voces enrutable, FM que cruza el cero, **modulación de fase**,
   modulación en anillo, **los dos caracteres de PWM**, **la sierra
   reversible**, y **voces que pueden bajar a frecuencia de modulación**.
11. **La imperfección se controla, no se elimina** (§7.7). Desafinado, deriva y
   carácter de placa entran como parámetros `por-voz`. Un instrumento que deriva
   de verdad no puede ofrecer esto, porque en él no se elige.
12. **Todo entra como parámetro con descriptor y ámbito declarado**
    (`por-voz` / `compartido`). Sin jumpers, sin modos escondidos. Es la
    condición para que el agente y las tres pieles lo alcancen sin escribirles
    una línea (núcleo §2.1, §3.5, §4.5).
13. **Montaje escalonado**: se fabrican las tres placas, se monta primero una de
    voces más la de panel —un instrumento de cuatro voces completo— y la segunda
    entra cuando la primera responde. Su bring-up es gratis: es la misma placa.

## 3. Las tres placas, y qué lleva cada una

```
   panel                                        fondo del case
     │
     ├── PLACA DE PANEL ── 16 jacks, 16 LED, sensado de ocupación
     │        │ conector de apilar
     ├── PLACA A (madre) ── 4 voces + su convertidor, micro, REFERENCIA
     │        │              única, telemetría, J1 (potencia) y J2 (datos)
     │        │ conector de apilar
     └── PLACA B ────────── 4 voces + su convertidor
```

**Por qué el convertidor va en las dos placas y no solo en la madre.** Un LSB son
38,15 µV y valen 0,139 cents, así que **un milivoltio de caída o de ruido en un
contacto son 3,6 cents** metidos directos en la afinación. Es el mismo efecto que
`dac_local_budget.py` ya midió al comparar el convertidor en el módulo (0,58
cents de suelo) contra el convertidor en el cerebro (1,71). **El tono se genera
siempre pegado a su oscilador y no cruza ninguna unión.**

Qué cruza el conector, y por qué aguanta:

| Señal | Por qué tolera cruzar |
|---|---|
| Alimentación ±12 V, masas | Es lo que ya cruza hoy por el J1 |
| `VREF` 2,5 V | Continua. Se filtra y bufferiza al llegar a B, y sigue siendo **una sola referencia**: los errores de las ocho voces escalan juntos, que es lo que sostiene el diseño |
| El SPI **privado** del micro hacia el convertidor de B, e I²C | Digitales. Ojo: no es el SPI del instrumento — ese muere en el micro (decisión 3) |
| Pulsos de afinación de B hacia el micro | Digitales, 3,3 V, ya limpiados por el Schmitt |
| CV de mezcla y de PWM (compartidos) | Un 1 % de desparejo entre voces es amplitud, no tono — igual que en la v1 |
| Sync entre voces de placas distintas | Digital |
| Audio de las voces de B hacia el panel | Baja impedancia, salida de op-amp |

**Lo que NO cruza:** el CV de tono de cada voz.

### Lo que gana partir así

| | piezas del layout más difícil |
|---|---|
| Una placa de ocho voces | ≈415, todas en un ruteo nuevo |
| Tres placas | **≈215**, sobre un layout que ya está ruteado y con DRC en 0 |

El total de piezas sube un poco; **la placa difícil baja a la mitad**, y esa es
la que decide si esto avanza o se atasca.

### Y si hace falta un segundo banco: otro módulo, no más placas

Para **FM de ocho voces** hacen falta dieciséis osciladores, porque en FM la
moduladora tiene que seguir a su portadora en frecuencia: una moduladora
compartida entre ocho notas distintas no da FM tonal, da campanas disonantes.

Dieciséis **dentro de este módulo no caben**: serían cuatro placas apiladas, o
sea 65 mm de fondo con los conectores más bajos que existen, contra los 50 que da
el 68 % del panel. La salida no es apretar la placa —el chip es solo el 3 % del
área de una voz, así que encogerlo no compra nada— sino:

> **El segundo banco es otro módulo, no otra placa dentro de este.**

| | fondo | ancho |
|---|---|---|
| 16 osciladores en un módulo (4 placas) | 65 mm — **no cabe** | 114 mm |
| **Dos módulos de ocho, uno al lado del otro** | **39,8 mm cada uno** | 228 mm de los 528 de la fila |

El instrumento entero —dos VCO, cerebro, filtro, envolvente, VCA y mezclador—
sale en 798 mm de los 1056, con 258 de sobra. Y **el diseño nuevo que hace falta
es ninguno: es esta misma placa fabricada dos veces más.**

Como los dos módulos son idénticos, lo que sea cada uno lo decide el preset:

- **Ocho voces de FM**, cada portadora con su moduladora siguiéndola.
- **Dieciséis osciladores parafónicos** sobre ocho filtros — unísonos enormes.
- **Ocho voces limpias más ocho moduladores** libres para sync, anillo o
  frecuencia baja.

Nada de esto se construye en este ciclo. Se escribe aquí porque **es gratis
dejarlo posible y caro descubrirlo después**: el conteo de voces ya sale del
descubrimiento (núcleo §3.6) y el direccionamiento aguanta dieciséis por módulo,
así que el instrumento contaría el segundo banco solo.

## 4. La cota que manda: el fondo

El panel es 3U de Eurorack: **128,5 mm de alto**, y la fila da **528 mm útiles**
(`case/cad/params.scad`, `case/clearance_budget.py`). La placa de la v1 mide
124 mm de alto, o sea que **a lo alto ya no queda nada**: el módulo crece a lo
ancho o se apila. Por eso se apila.

Estimación del apilado, **con dos supuestos sin medir**:

| | mm | |
|---|---|---|
| Jack por detrás del panel | 13,0 | **SUPUESTO — hay que medirlo** |
| Placa de panel | 1,6 | |
| Conector de apilar | 10,0 | **SUPUESTO — los hay de 5 a 15** |
| Placa A + sus piezas | 7,6 | el IDC 2×6 es la más alta, ~9 mm |
| Conector de apilar | 10,0 | |
| Placa B + sus piezas | 7,6 | |
| **Total** | **49,8** | contra **50,0** disponibles en el 68 % del panel |

Cabe por dos décimas de milímetro. **Eso no es un margen, es una plegaria.** Con
conectores de 5 mm baja a ≈40 mm y ahí sí hay aire. Por tanto:

> **La altura del conector de apilar es una decisión de diseño con presupuesto
> propio, no un detalle de montaje.** Y el fondo del jack se mide antes de cerrar
> la geometría, no después. Riesgo 1 de §11.

## 5. Exactitud: dos correcciones al núcleo heredado

Las dos salen de leer el datasheet del SSI2130 (rev. 2.4, dic. 2020) como fuente
primaria. **Ese PDF no estaba en el repositorio** —se citaba como origen de las
decisiones de la v1 y vivía en una carpeta temporal del sistema. Se versiona con
este spec.

### 5.1 La resistencia de escala va corta un 0,75 %

El datasheet da la relación exacta (pág. 14): **I_SCALE = 4,717 × I_octava**.
Para los 20 µA/octava de diseño son 94,34 µA, o sea **26,5 kΩ** desde la
referencia. El BOM de la v1 lleva **26,7 kΩ** —el valor de catálogo más cercano,
porque 26,5 no existe en E96—, lo que deja la sensibilidad en **19,850 µA/octava**.

Al convertidor no le afecta: el autoafinado mide la frecuencia real y lo absorbe
en la tabla de 84 notas. **Al jack de CV externo sí**, porque ahí no hay tabla:

| | error de escala del jack |
|---|---|
| 26,7 kΩ (v1) | **+11,5 cents por octava**, acumulativo — 57 cents a cinco octavas |
| **26,1 kΩ + 402 Ω en serie** | **+2,50 cents por octava** |

No es tolerancia que se promedie entre placas: es un **sesgo sistemático**, igual
en todas y siempre en la misma dirección. Se corrige con una resistencia más por
voz. De paso, el span nominal sube de 7,576 a **7,63 octavas**.

Esto **cierra el primer punto de «lo NO confirmado»** de `pitch_budget.py`, que
decía justo que la proporcionalidad entre I_octava e I_escala no estaba
verificada contra datasheet.

> Trampa del propio datasheet, anotada para quien venga: su sección de «trim
> fijo» (pág. 11) recomienda 24,3 kΩ para lo mismo, y eso da un 9 % de más. La
> v1 no la siguió, y acertó.

### 5.2 La compensación de agudos existe sin trimmer, y no se estaba usando

Del datasheet (pág. 11): la resistencia parásita de los transistores del
conversor hace que **en el extremo agudo el oscilador corra más lento de lo
debido**. El chip trae una salida para corregirlo, y **hay versión sin trimmer**:

> «un 4,32 kΩ de HF TRACK a masa y un 267 kΩ de HF TRACK a EXPO FREQ dan
> compensación de alta frecuencia adecuada para 20 µA por octava»

La v1 dejó ese pin sin conectar y lo justificó con «trimless». Pero trimless no
es «sin compensación»: la versión de resistencias fijas encaja entera en la
filosofía del módulo. Sin ella, el error de agudos lo acaba pagando la tabla de
84 notas **gastando span justo en el extremo donde menos hay** — y el margen es
lo único que sostiene la apuesta.

**Entran las dos resistencias por voz.** Es exactitud, no una función.

### 5.3 Al comparador de PWM le falta histéresis

El datasheet lo dice en una línea suelta al pie de su figura 12, y por eso es
fácil de perder:

> «un poco de histéresis ayuda mucho a que el PWM suene bien»

La v1 no la tiene: ata `PWM−` al triángulo y `PWM+` al CV del convertidor, sin
realimentación (`build_schematic.py:571-572`). Sin histéresis, un comparador
cerca del punto de cruce puede conmutar sucio cuando le llega ruido, y eso en el
ancho de pulso se oye. **Entra una resistencia de realimentación por voz**, con
su valor presupuestado contra la amplitud de la triangular. Como las otras dos
de §5: es calidad, no una función.

*(De propina, del mismo párrafo: llevando la entrada del comparador un poco por
encima de la referencia o por debajo de masa, la salida se fuerza a alto o a bajo
**sin chasquidos**. Es una forma limpia de silenciar el pulso que no cuesta nada
declarar.)*

## 6. El bloque digital: el micro

Un micro en la placa A, candidato **RP2350B**, con dos razones de encaje que
**hay que confirmar contra su datasheet antes de fijarlo** (riesgo 4):

- **PIO** suficiente para cronometrar ocho canales en paralelo, con el mismo
  conteo recíproco que el núcleo §5.1 ya presupuestó. Eso permite **mudar
  `autotune_budget.py` al módulo casi tal cual**, en vez de rehacerlo: los
  6,67 ns de sellado derivados del reloj y los **131 ns de jitter máximo del
  74HC14** siguen valiendo, porque la arquitectura de medida no cambia de forma.
- **Ocho entradas analógicas**, justo las ocho del patch bay.

Qué hace, todo reportando por `MISO`:

| Tarea | Detalle |
|---|---|
| Cronometrar los ocho osciladores | En paralelo. El barrido no se alarga por tener más voces |
| Leer las ocho entradas de control | Y hacer posible el barrido por inyección del núcleo §7.6 |
| Sensar los 16 jacks | Es lo que permite que «el cable gane» sin que el cerebro se quede mintiendo |
| Llevar la cadena de LED | 16, uno por jack: guía de patcheo y estado de ruta |
| Gobernar el enrutado de sync | Qué voz sincroniza a cuál (§7.1) |
| **Escribir los conversores de las dos placas** | Por su SPI privado. El cerebro le manda la nota; el micro la pone en el canal que toca (decisión 3) |
| Telemetría | §8 |

Y una obligación que no es suya sino del bus, pero se cumple aquí: **el micro
deja el `MISO` en alta impedancia siempre que su `CS` esté alto**, sin
excepciones de modo. Es la regla 1 del contrato y se mide en el bring-up:
`CS` alto, `MISO` sondado, aprobado o suspenso.

**Lo que el micro NO hace: sonido.** No hay camino de audio que pase por él. Es
la misma regla que el núcleo §5.0 le impone al cerebro, aplicada aquí.

## 7. Los juguetes

Los tres salen de capacidades que el chip ya trae y la v1 dejó latentes «por
alcance, no por capacidad». Su §12 condicionaba abrirlas a «un respin de panel
futuro con dato de uso real». **Este es ese respin**, y el otro argumento de la
v1 —«el sync sin pareja por voz no aporta»— se cae con ocho voces: ahí hay cuatro
parejas, y quién modula a quién lo decide el preset.

### 7.1 Sync entre voces, enrutable

Hard sync (pin 17, umbrales 1,0 / 1,55 V) y soft sync (pin 19, 5 kΩ interna, con
acoplo capacitivo). La salida cuadrada de cualquier voz puede atacar la entrada
de sync de cualquier otra, y **el reparto lo decide el micro**. Es el mismo
principio de enrutado por cerebro que gobierna el instrumento, en pequeño y
dentro del módulo.

### 7.2 FM que cruza el cero

`TIME REVERSE` (pin 18) + `LIN FREQ` (pin 21), según la figura 18 del datasheet
—«un puñado de pasivos hace de la TZFM y la TZPM una realidad de bajo recuento
de piezas»—: medio amplificador operacional y pasivas por voz. Cruzar el cero es
lo que evita que la FM desafine la nota, que es el defecto de la FM analógica
corriente.

Con ocho osciladores y el enrutado del micro, esto da desde ocho voces limpias
hasta **cuatro voces de FM de dos operadores**, y lo cambia un preset.

### 7.3 Modulación en anillo

Figura 19 del datasheet: un operacional por voz y los **dos canales auxiliares
del mezclador interno** —el AUX 2 está libre en la v1— dan un multiplicador de
cuatro cuadrantes. Sonidos metálicos y campanas sin tocar el camino de tono.

### 7.4 Modulación de fase, por el precio de un condensador

El mismo circuito de la figura 18 tiene **dos entradas**: una hace FM y la otra
hace modulación de fase. La diferencia es un condensador que deriva la señal
moduladora.

Y no es un adorno, porque el datasheet dice cuál es mejor y por qué:

> «como la señal moduladora va acoplada en continua, cualquier offset deja el
> oscilador desafinado metiendo un desplazamiento constante de frecuencia. La PM
> quita el offset y **mantiene el oscilador afinado**»

O sea: **la FM te desafina la nota y la PM no.** Si ya se paga el circuito de la
FM, dejar fuera la PM sería dejar fuera la mitad buena. Entra.

### 7.5 Dos sabores de PWM, y la sierra al revés

Dos capacidades que salen del mismo sitio donde ya vamos a poner las manos:

**El PWM tiene dos caracteres** según de qué onda se alimente el comparador
(datasheet pág. 7). Con triangular mantiene constante el tiempo entre los centros
de los pulsos. Con sierra, un flanco queda clavado al corte de la sierra y solo
se mueve el otro, y eso **añade un vibrato suave** como parte del propio efecto.
Son dos sonidos distintos y elegir cuesta **un conmutador analógico por voz**.
Es el único de este grupo con coste real.

**La sierra se puede invertir.** El pin `TIME REVERSE` no solo sirve para cruzar
el cero: quieto en alto da sierra ascendente y en bajo da sierra descendente. Si
ya se cablea para la FM, esto es gratis.

> **Restricción que hay que escribir, porque es el mismo pin:** una voz no puede
> tener la sierra fija en una dirección **mientras** hace FM que cruza el cero.
> Son usos excluyentes del mismo pin y el modelo tiene que decirlo en voz alta,
> no dejar que el usuario descubra que un parámetro le pisa el otro.

### 7.6 Una voz puede ser un oscilador lento

El chip cubre **1000:1 —diez octavas— con menos de un cent de error**
(especificaciones, pág. 2), y el diseño usa siete. El propio datasheet contempla
usarlo de oscilador de baja frecuencia.

Eso significa que **una voz configurada abajo del todo es un modulador**, y no
cuesta ni una pieza: es rango de código del convertidor. Con ocho voces y el
enrutado del micro, dedicar una o dos a modular a las demás es un preset, no un
respin. Lo que sí hay que hacer es **declararlo como parámetro** —el modo de la
voz— y comprobar en el bring-up hasta dónde baja de verdad antes de prometerlo.

### 7.7 La imperfección no se elimina: se controla

Este módulo se afina solo, no deriva y sus ocho voces son iguales por diseño
—referencia única, tabla de 84 notas, autoafinado—. Eso es una virtud técnica y,
dicho sin rodeos, un riesgo musical: lo que hace que un analógico suene vivo son
sus imperfecciones, y aquí están eliminadas por construcción.

La respuesta no es empeorar el circuito. Es que **la imperfección sea un
parámetro**, que es algo que un instrumento con deriva de verdad no puede
ofrecer, porque en él no se elige. Tres, y ninguna cuesta una pieza:

| | Qué es | Ámbito |
|---|---|---|
| **Desafinado** | Un desplazamiento fijo por voz. Lo que engorda un unísono | `por-voz` |
| **Deriva** | Que cada voz vague despacio unos cents, con la amplitud y la velocidad como parámetros | `por-voz` |
| **Carácter de placa** | Un error pequeño y fijo por voz, guardado en la EEPROM de identidad. Hace que **este** instrumento suene distinto de otro igual, y viaja con la placa | `por-voz`, en la calibración |

**La resolución alcanza de sobra**, y por un motivo estructural que ya está
decidido: como las ocho voces cuelgan de **la misma referencia**, el error común
se cancela al restar, así que **desafinar dos voces entre sí es más fino que
afinarlas en absoluto**. El suelo absoluto es 0,58 cents; el paso relativo es
1 LSB = **0,139 cents**.

Traducido a lo que se oye, a 440 Hz:

| Se pide | Se oye |
|---|---|
| 1 paso (0,139 cents) | batido de 0,035 Hz — un ciclo cada 28 s |
| El batido más lento que se nota (~0,1 Hz) | 2,8 pasos |
| Unísono gordo (10 cents) | 72 pasos dentro del efecto |

Y el corolario que hay que escribir para que nadie lo rompa después: **el
autoafinado corrige la afinación, no el desafinado pedido.** Son dos capas
distintas —una quita el error que nadie quiso, la otra añade el que sí— y el
firmware tiene que sumarlas en ese orden, nunca dejar que la primera se coma a la
segunda.

### 7.8 Lo que esto le hace a los canales del convertidor

Es el cuello nuevo y hay que verlo con números. El AD5686R da 4 canales.

| | canales | chips |
|---|---|---|
| v1 (4 voces, sin juguetes) | 9 | 3, con 3 de reserva |
| **8 voces, índice de FM y de anillo por voz** | **30** | **8**, con 2 de reserva |
| 8 voces, FM y anillo compartidos | 16 | 4, con **0 de reserva** |

Ninguna de las dos últimas es cómoda: la primera son ocho chips, la segunda deja
la reserva en cero, contra la doctrina de la v1 («un parámetro futuro cuesta cero
hilos»). **Decisión abierta 3 de §11**, con su criterio escrito.

## 8. Telemetría

El patrón de la v1, ampliado por dos motivos: hay ocho osciladores repartidos en
dos placas, y hay un micro que puede registrar mucho más que antes.

- **Un sensor de temperatura por placa de voces**, pegado a su racimo de
  osciladores. Uno solo dejó de representar a los ocho en cuanto se repartieron.
- **EEPROM de identidad única (24AA02E48) en la placa A**: tipo, revisión, serial
  y calibración. **Riesgo 5**: el blob de la v1 presupuestaba 250 B y la tabla de
  84 notas × 4 voces × 16 bits ya eran 672 B que no cabían. Con ocho son 1344 B.
  Hay que resolver el formato o la pieza.
- **Test points rotulados en serigrafía** — la v1 los dejó sin rótulo y su propia
  lista de mejoras para la rev B lo pedía. Con ocho voces son más, y quince pads
  anónimos con el multímetro en la mano es un tropiezo garantizado.

## 9. Verificación

Se heredan los gates de la v1 y se añaden los que las decisiones nuevas exigen.
El runner los descubre por patrón; **ninguno se añade a una lista**.

| Gate | Qué mide | Estado |
|---|---|---|
| `check_footprints`, `check_netlist`, `check_bom` | Lo de siempre, antes de escribir nada | heredado |
| `pitch_budget.py` | Ahora con `VOCES` parametrizado, no con un 4 escrito | **modificar** |
| `dac_local_budget.py` | Añadir la referencia cruzando el conector | **modificar** |
| `autotune_budget.py` | Se muda al módulo; declarar qué queda en el cerebro | **mudar** |
| `depth_budget.py` | El fondo del apilado contra el del case, con aserción | **nuevo** |
| `cvscale_budget.py` | La escala del jack externo dentro de 3 cents/octava | **nuevo** |
| `dac_channels.py` | Que los canales pedidos caben, con reserva declarada | **nuevo** |
| Render 2D y 3D de las tres placas | Lo mira una persona y lo aprueba | heredado |

**El Monte Carlo ya se corrió a ocho voces** y el diseño aguanta: a 3 % de
dispersión de chip pasan **96,58 %** de las placas contra 98,33 % con cuatro, y
los bodges por 100 placas suben de 1,7 a **3,5**. La aserción de «95 de cada 100
sin tocar una resistencia» sigue en pie. *(Detalle a arreglar al parametrizar: el
rótulo de la tabla dice «placas 4/4 OK» escrito a mano y no sigue a `VOCES`.)*

## 10. Consumo

Del datasheet: cada SSI2130 pide **+3,75 mA / −2,90 mA** típicos y **100 µA de la
referencia**. Ocho chips son ~30 mA, ~23 mA y **800 µA de carga en la ADR4525**,
contra los 400 µA de la v1. Más el micro, la cadena de LED —que tiene su propio
árbitro de brillo abierto en el #104— y los operacionales de los juguetes.

**El recuento se hace con la placa de ocho delante**, no extrapolando de la línea
de la v1. Es el punto 6 del #158 y sale como tarea del plan, no como número de
este spec.

## 11. Riesgos y decisiones abiertas

Cada uno con cómo se cierra, que es la puerta de esta fase.

1. **El fondo del apilado cabe por 0,2 mm sobre dos supuestos sin medir.**
   Cierra: medir cuánto sobresale el jack por detrás del panel, elegir la altura
   del conector de apilar, y escribir `depth_budget.py` con su aserción contra el
   fondo del case. **Antes de fijar la geometría.**
2. **La referencia cruza un conector.** Cierra: extender `dac_local_budget.py`
   con el término del contacto y el filtrado local en B, y aserir que el suelo de
   afinación de las voces de B no empeora respecto a las de A más de lo
   presupuestado. Si no se cumple, la salida conocida es una referencia por placa
   — a costa de que los errores dejen de escalar juntos entre bancos.
3. **Cuántos canales de convertidor, y si el índice de FM y el de anillo van por
   voz.** Cierra: `dac_channels.py` con el conteo, y la decisión tomada contra
   área y coste. Criterio: por voz es lo que hace expresivas esas funciones (una
   nota con más FM que las otras); compartido las convierte en un ajuste global.
   Anotado para evaluarlo: la familia de 8 canales del mismo fabricante reduce
   chips y área, y hay que verificar pinout, referencia interna apagable y cadena
   DCEN antes de proponerla.
4. **El micro candidato no está confirmado contra su datasheet**: máquinas de
   estado de PIO disponibles, entradas analógicas, pines totales y consumo.
   Cierra: leer el datasheet y escribir el presupuesto de pines.
5. **El blob de calibración no cabe en la EEPROM** y con ocho voces cabe menos.
   Cierra: definir el formato del blob (lo decide el firmware) o cambiar la pieza.
6. **Ocho encapsulados de 4×4 mm soldados a mano.** El SSI2130 es de proveedor
   único y la fábrica no lo monta: probado contra el pedido real, sale «8
   shortfall» y el flujo de ensamblaje no acepta piezas sin stock. Cierra:
   comprar ocho más repuestos al arrancar, y que el bring-up empiece por una sola
   placa de voces.
7. **Nada de este proyecto se ha fabricado nunca.** Cierra: el montaje escalonado
   de la decisión 13 — una placa de voces y la de panel primero.
8. **La dispersión chip a chip del conversor exponencial** sigue sin garantizarla
   ningún datasheet. Se hereda de la v1 y se cierra igual: midiendo los chips
   reales en el bring-up.

## 12. Fuera de alcance

- **El enrutado del instrumento** —matriz en el módulo 4, topología en estrella,
  el audio yendo y volviendo de un módulo central— se decidió abrirlo como su
  propio ciclo de diseño. Toca `architecture-poly.md` §5 y §6, define el módulo 4
  y condiciona el 5, 6, 7 y 8. **No bloquea este spec**: el VCO produce y no
  consume, así que saca ocho voces por dieciséis jacks vaya donde vaya el cable.
- **Reordenar la cadena** (VCA antes del filtro) — sigue necesitando un cable.
- **El firmware del cerebro.** Este módulo define su contrato, no su código.
- **Ondas crudas al patch bay** — descartado en la v1 y no se reabre sin dato
  nuevo.
- **Los módulos 5, 6 y 7.** Se especifican para ocho voces con destino de timbre
  por voz, pero no se dibujan en este ciclo.

## 13. Issues que hay que abrir o actualizar

Este spec **excede el #158**, que pedía duplicar voces. Al escribir el plan:

- **#158** — actualizar con el alcance real: exactitud, juguetes, patch bay de
  dieciséis, micro en el módulo y tres placas.
- **#152** (censo de anchos del case) — el ancho real de este módulo sale de
  aquí, y ya no es el de la v1.
- **Nuevo** — el datasheet del SSI2130 no estaba versionado; queda versionado con
  este spec, y hay que revisar si otros módulos citan fuentes que tampoco están.
- **Nuevo** — la escala del jack de CV externo (§5.1): sesgo sistemático de
  +11,5 cents por octava en la v1.
- **Nuevo** — el enrutado del instrumento, para abrir su ciclo (§12).
