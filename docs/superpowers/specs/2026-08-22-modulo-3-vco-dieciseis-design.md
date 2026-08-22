# Módulo 3 v2 — VCO ×16 en seis placas, con todos los juguetes

> Sustituye a [`2026-08-16-modulo-3-vco-design.md`](2026-08-16-modulo-3-vco-design.md).
> Origen: #158 — el instrumento se diseña para ocho voces. **Este spec va más
> lejos: dieciséis osciladores en un solo módulo**, decidido con Samuel el
> 2026-08-22 (§2.1).
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

**Dieciséis osciladores analógicos en un solo módulo**, gobernados por números,
estirados a lo ancho de un panel de 3U, con el módulo midiéndose a sí mismo y
con todo lo que el SSI2130 trae latente puesto a trabajar.

Dieciséis y no ocho por una razón concreta: **en FM cada voz necesita dos
osciladores**, porque la moduladora tiene que seguir a su portadora en
frecuencia — una moduladora compartida entre ocho notas distintas no da FM
tonal, da campanas disonantes. Con dieciséis, el instrumento hace **FM de ocho
voces**, o dieciséis voces limpias, o cualquier mezcla, y lo decide el preset.

Y **en un solo módulo, no en dos de ocho**: si fueran dos, para que un oscilador
del primero modulase a uno del segundo la señal tendría que salir por un jack y
volver a entrar, y **la matriz de modulación se parte por la mitad**. Con uno
solo, el micro enruta los dieciséis contra los dieciséis por dentro.

Objetivo medible, heredado y ampliado: **las 7 octavas de cada uno de los
dieciséis osciladores dentro del rango del convertidor, sin trimmers**, y **la
escala del jack de CV externo dentro de 3 cents por octava**.

## 2. Decisiones fijadas (con Samuel, 2026-08-22)

1. **Dieciséis osciladores en un solo módulo**, para FM de ocho voces con la
   matriz de modulación entera (§1). Decidido a sabiendas del coste: dieciséis
   encapsulados de 4×4 mm soldados a mano en un proyecto que nunca ha fabricado
   nada (riesgo 7).
2. **El módulo se mide a sí mismo.** Las cuatro líneas `TUNE_OUT` de los pines
   9-12 del J2 quedan sin usar; los números vuelven por `MISO`. **El contrato del
   J2 no cambia ni un pin** (núcleo §5.3).
3. **Del J2 cuelga un micro, no los chips** (regla 2 del contrato). El cerebro le
   habla al micro maestro; los conversores cuelgan de un SPI **privado**, dentro
   del módulo. Esto **cierra un hueco que el spec del cerebro daba por perdido**:
   su §4.1 dice que el requisito de soltar el `MISO` con `CS` alto *«vive en
   placas que todavía no se han dibujado — salvo una, que ya está en gerbers y
   nunca leyó este documento»*. Esa placa es la v1 de este módulo, y aquí se
   rehace. Consecuencias: se acaba la pelea por el `MISO` en vez de hacerse
   sobrevivible, la trama de 72 bits deja de estar clavada en el contrato del J2
   —era el tamaño de la cadena de tres conversores de la v1, un número de una
   placa metido en una interfaz común— y **cuántos conversores lleva el módulo
   deja de ser asunto de nadie de fuera**.
4. **Dos diseños de placa, seis unidades**, todas de 4 capas, y **un solo
   módulo**: una identidad, un `CS`, una referencia (§3).
5. **32 jacks en dos filas**: entrada de control y salida por cada oscilador.
6. **Las entradas de control van encadenadas.** El pin de normalizado de cada
   jack alimenta al siguiente en vez de ir a masa. Un cable manda sobre todas las
   de abajo; dos cables hacen dos bancos; dieciséis dan control individual.
   Sustituye a la v1, donde ese pin existía atado a masa —el mecanismo puesto y
   sin usar—, y aplica al módulo 3 la doctrina que `architecture-poly.md` §6 ya
   había escrito para el instrumento.
7. **El cable siempre gana.** Cualquier ruta que el cerebro decida se rompe al
   meter un cable en el jack, y el cerebro **se entera** porque el jack está
   sensado. No es lógica nueva: es el muelle del conector haciendo lo suyo.
8. **El patrón completo del núcleo §10**: sensado de ocupación en los 32 jacks,
   lectura por ADC de las 16 entradas de control, un LED por jack, EEPROM de
   identidad, y telemetría térmica ampliada.
9. **Exactitud, tres correcciones** (§5): la resistencia de escala, la
   compensación de agudos y la histéresis del comparador de PWM.
10. **Los juguetes** (§7), todo lo que el chip trae y la v1 dejó dormido: sync
   entre osciladores enrutable, FM que cruza el cero, **modulación de fase**,
   modulación en anillo, **los dos caracteres de PWM**, **la sierra reversible**,
   y **osciladores que pueden bajar a frecuencia de modulación**.
11. **La imperfección se controla, no se elimina** (§7.7). Desafinado, deriva y
   carácter de placa entran como parámetros `por-voz`. Un instrumento que deriva
   de verdad no puede ofrecer esto, porque en él no se elige.
12. **Todo entra como parámetro con descriptor y ámbito declarado**
    (`por-voz` / `compartido`). Sin jumpers, sin modos escondidos. Es la
    condición para que el agente y las tres pieles lo alcancen sin escribirles
    una línea (núcleo §2.1, §3.5, §4.5).
13. **Montaje escalonado por columnas.** Se fabrican las seis placas de una vez y
    se monta **una columna primero** —ocho osciladores completos, con su micro y
    su panel— antes de poblar la segunda. No es recortar el alcance: el módulo es
    de dieciséis y se fabrica entero. Es que la operación más delicada del
    proyecto no se hace dieciséis veces seguidas sin haberla hecho nunca.

## 3. Las seis placas, y qué lleva cada una

Solo hay **dos diseños**. Todo lo demás son repeticiones, y una de ellas se
puebla de dos formas distintas.

```
             COLUMNA 1                 COLUMNA 2
   panel  ┌── PANEL (16 jacks) ──┬── PANEL (16 jacks) ──┐  <- mismo diseño x2
          │   VOCES + micro      │   VOCES + micro      │  <- mismo diseño,
          │   (maestro)          │   (esclavo)          │     poblado con micro
          └── VOCES              └── VOCES              ┘  <- mismo diseño,
                                                              sin micro
     228 mm de ancho · 2 placas de fondo · 4 capas cada una
```

- **Placa de panel** (×2): 16 jacks en dos filas de ocho, 16 LED, sensado de
  ocupación.
- **Placa de voces** (×4): 4 osciladores con **su propio convertidor al lado**,
  su sensor de temperatura, y el sitio del micro y su entorno. En dos de las
  cuatro ese sitio se puebla; en las otras dos se deja vacío.

**Por qué el convertidor va en todas y no en una central.** Un LSB son 38,15 µV
y valen 0,139 cents, así que **un milivoltio de caída o de ruido en un contacto
son 3,6 cents** metidos directos en la afinación. Es el mismo efecto que
`dac_local_budget.py` ya midió al comparar el convertidor en el módulo (0,58
cents de suelo) contra el convertidor en el cerebro (1,71). **El tono se genera
siempre pegado a su oscilador y no cruza ninguna unión.**

**Por qué dos micros y no uno.** Un RP2350B tiene 12 máquinas de estado de PIO y
8 entradas analógicas *(a confirmar — riesgo 4)*. Dieciséis osciladores piden 16
cronómetros y 16 entradas de control: no caben en uno. Dos, con ocho cada uno,
encajan justo. **Uno es el maestro** —el único que habla por el `MISO` del J2— y
el otro cuelga de su SPI privado como un periférico más, lo que mantiene intacta
la regla 1 del contrato.

**Una sola referencia para los dieciséis**, en la placa maestra, distribuida y
bufferizada localmente. Es lo que hace que los errores escalen juntos y, sobre
todo, lo que hace que **desafinar dos osciladores entre sí sea más fino que
afinarlos en absoluto** (§7.7).

Qué cruza los conectores, y por qué aguanta:

| Señal | Por qué tolera cruzar |
|---|---|
| Alimentación ±12 V, masas | Es lo que ya cruza hoy por el J1 |
| `VREF` 2,5 V | Continua. Se filtra y bufferiza al llegar, y sigue siendo **una sola referencia** para los dieciséis |
| El SPI **privado** del maestro, e I²C | Digitales. Ojo: no es el SPI del instrumento — ese muere en el maestro (decisión 3) |
| Pulsos de afinación hacia su micro | Digitales, 3,3 V, ya limpiados por el Schmitt |
| CV de mezcla y de PWM (compartidos) | Un 1 % de desparejo entre osciladores es amplitud, no tono — igual que en la v1 |
| Sync y modulación entre osciladores de placas distintas | El sync es digital; la señal de FM es audio de baja impedancia |
| Audio hacia el panel | Baja impedancia, salida de op-amp |

**Lo que NO cruza:** el CV de tono de cada oscilador.

### Lo que gana partir así

| | piezas del layout más difícil |
|---|---|
| Un módulo de dieciséis en un solo layout | ≈960, todas nuevas |
| **Dos diseños repetidos** | **≈215**, sobre un layout que ya está ruteado y con DRC en 0 |

Y el reparto paga una segunda vez donde no se esperaba: **la unidad que se
retoca es la placa de cuatro, no el módulo.** Si un oscilador cae fuera del
margen se cambia una resistencia en su placa. A 3 % de dispersión, el 98,33 % de
las placas de cuatro salen limpias, así que **el 6,5 % de los módulos pedirá un
retoque en una sola de sus cuatro placas** — muy distinto del 93,42 % de módulos
limpios que sale de mirarlo como un bloque indivisible de dieciséis.

## 4. La cota que manda: el fondo, y por eso se estira a lo ancho

El panel es 3U de Eurorack: **128,5 mm de alto**, y la fila da **528 mm útiles**
(`case/cad/params.scad`, `case/clearance_budget.py`). La placa de la v1 mide
124 mm de alto, o sea que **a lo alto no queda nada**.

Y apilar tampoco escala: cuatro placas de voces en una sola columna piden **65 mm
de fondo** con los conectores más bajos que existen, contra los 50 que da el 68 %
del panel. Por eso el módulo **se estira a lo ancho**: dos columnas de dos.

| | mm | |
|---|---|---|
| Jack por detrás del panel | 13,0 | **SUPUESTO — hay que medirlo** |
| Placa de panel | 1,6 | |
| Conector de apilar | 5,0 | **SUPUESTO — los hay de 5 a 15** |
| Placa de voces + sus piezas | 7,6 | el IDC 2×6 es la más alta, ~9 mm |
| Conector de apilar | 5,0 | |
| Placa de voces + sus piezas | 7,6 | |
| **Total** | **39,8** | contra **50,0** disponibles en el 68 % del panel |

Con conectores de 10 mm sube a 49,8 y cabe por dos décimas, que **no es un
margen, es una plegaria**. Por tanto:

> **La altura del conector de apilar es una decisión de diseño con presupuesto
> propio, no un detalle de montaje.** Y el fondo del jack se mide antes de cerrar
> la geometría, no después. Riesgo 1 de §11.

**El ancho:** 228 mm de los 528 de una fila. Los 32 jacks piden 191 mm repartidos
en dos filas de dieciséis, que caben de sobra, y las dos filas se llevan unos
40 mm de los 128,5 de alto del panel. El instrumento entero —este módulo,
cerebro, filtro, envolvente, VCA y mezclador— sale en **798 mm de los 1056** que
dan las dos filas, con 258 de sobra. Eso hay que meterlo en el censo del case,
que es el #152.

## 5. Exactitud: tres correcciones al núcleo heredado

Las tres salen de leer el datasheet del SSI2130 (rev. 2.4, dic. 2020) como fuente
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

## 6. El bloque digital: dos micros

**Dos** micros, uno por columna, candidato **RP2350B**, con el encaje que hay que
**confirmar contra su datasheet antes de fijarlo** (riesgo 4):

| Recurso | Piden 16 osciladores | Da un RP2350B | Con dos |
|---|---|---|---|
| Cronómetros de PIO | 16 | 12 | 16 de 24 |
| Entradas analógicas | 16 | 8 | 16 de 16 — justo |

Ocho osciladores por micro es lo que hace que la cuenta cierre, y es la razón de
que el módulo se parta en columnas y no de otra forma.

El conteo recíproco es el mismo que el núcleo §5.1 ya presupuestó, así que
**`autotune_budget.py` se muda al módulo casi tal cual** en vez de rehacerse: los
6,67 ns de sellado derivados del reloj y los **131 ns de jitter máximo del
74HC14** siguen valiendo, porque la arquitectura de medida no cambia de forma.

Qué hacen, todo reportando por `MISO` a través del maestro:

| Tarea | Detalle |
|---|---|
| Cronometrar sus ocho osciladores | En paralelo. El barrido no se alarga por haber más |
| Leer sus ocho entradas de control | Y hacer posible el barrido por inyección del núcleo §7.6 |
| Sensar sus 16 jacks | Es lo que permite que «el cable gane» sin que el cerebro se quede mintiendo |
| Llevar su tramo de la cadena de LED | 16 cada uno, uno por jack |
| Gobernar el enrutado de sync y de modulación | Quién modula a quién entre los dieciséis (§7.1) |
| Escribir sus conversores | Por el SPI privado (decisión 3) |
| Telemetría | §8 |

**Lo que los micros NO hacen: sonido.** No hay camino de audio que pase por
ellos. Es la misma regla que el núcleo §5.0 le impone al cerebro, aplicada aquí.

Y una obligación que no es suya sino del bus, y que **solo cumple el maestro**:
deja el `MISO` en alta impedancia siempre que su `CS` esté alto, sin excepciones
de modo. Es la regla 1 del contrato y se mide en el bring-up: `CS` alto, `MISO`
sondado, aprobado o suspenso. **El esclavo no toca el J2 en ningún caso.**

## 7. Los juguetes

Los tres salen de capacidades que el chip ya trae y la v1 dejó latentes «por
alcance, no por capacidad». Su §12 condicionaba abrirlas a «un respin de panel
futuro con dato de uso real». **Este es ese respin**, y el otro argumento de la
v1 —«el sync sin pareja por voz no aporta»— se cae con dieciséis osciladores: ahí hay ocho
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

Con dieciséis osciladores y el enrutado del micro, esto da desde dieciséis
voces limpias hasta **ocho voces de FM de dos operadores**, y lo cambia un preset.

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
cuesta ni una pieza: es rango de código del convertidor. Con dieciséis osciladores y el
enrutado del micro, dedicar una o dos a modular a las demás es un preset, no un
respin. Lo que sí hay que hacer es **declararlo como parámetro** —el modo de la
voz— y comprobar en el bring-up hasta dónde baja de verdad antes de prometerlo.

### 7.7 La imperfección no se elimina: se controla

Este módulo se afina solo, no deriva y sus dieciséis osciladores son iguales por
diseño
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
decidido: como los dieciséis cuelgan de **la misma referencia**, el error común
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

Es el cuello nuevo y hay que verlo con números. El AD5686R de la v1 da 4 canales.

| | canales | chips de 4 | chips de 8 |
|---|---|---|---|
| v1 (4 osciladores, sin juguetes) | 9 | 3, con 3 de reserva | — |
| **16 osciladores, con tono, índice de FM y de anillo por voz** | **54** | 14 | **7** |

Catorce chips de cuatro canales es una respuesta, no una solución. **La familia
de ocho canales del mismo fabricante deja de ser una alternativa y pasa a ser lo
sensato**, con dos cosas que verificar antes de proponerla en firme: pinout,
referencia interna apagable por registro, y comportamiento de la cadena. Riesgo 3.

Repartido por placa son unos 13 canales por cada cuatro osciladores, que es lo
que hay que hacer caber en el mismo sitio donde la v1 metía tres chips.

## 8. Telemetría

El patrón de la v1, ampliado por dos motivos: hay dieciséis osciladores
repartidos en cuatro placas, y hay micros que pueden registrar mucho más que
antes.

- **Un sensor de temperatura por placa de voces** —cuatro en total—, pegado a su
  racimo de osciladores. Uno solo dejó de representar al conjunto en cuanto se
  repartieron, y con cuatro placas en dos columnas el gradiente térmico dentro
  del módulo es real, no teórico.
- **EEPROM de identidad única (24AA02E48) en la placa maestra**: tipo, revisión,
  serial y calibración. **Riesgo 5**: el blob de la v1 presupuestaba 250 B y la
  tabla de 84 notas × 4 voces × 16 bits ya eran 672 B que no cabían. Con
  dieciséis son **2688 B**. Hay que resolver el formato o la pieza.
- **Test points rotulados en serigrafía** — la v1 los dejó sin rótulo y su propia
  lista de mejoras para la rev B lo pedía. Con dieciséis osciladores son muchos
  más, y una tapa de pads anónimos con el multímetro en la mano es un tropiezo
  garantizado.

## 9. Verificación

Se heredan los gates de la v1 y se añaden los que las decisiones nuevas exigen.
El runner los descubre por patrón; **ninguno se añade a una lista**.

| Gate | Qué mide | Estado |
|---|---|---|
| `check_footprints`, `check_netlist`, `check_bom` | Lo de siempre, antes de escribir nada | heredado |
| `pitch_budget.py` | Con `VOCES` parametrizado, no con un 4 escrito, y evaluando **por placa de cuatro** además de por módulo | **modificar** |
| `dac_local_budget.py` | Añadir la referencia cruzando conectores y su buffer local | **modificar** |
| `autotune_budget.py` | Se muda al módulo; declarar qué queda en el cerebro | **mudar** |
| `depth_budget.py` | El fondo del apilado contra el del case, con aserción | **nuevo** |
| `cvscale_budget.py` | La escala del jack externo dentro de 3 cents/octava | **nuevo** |
| `dac_channels.py` | Que los 54 canales caben, con reserva declarada | **nuevo** |
| `vref_load_budget.py` | Los 1,6 mA de carga de la referencia, con su margen | **nuevo** |
| Render 2D y 3D de las seis placas, y del apilado montado | Lo mira una persona y lo aprueba | heredado |

**El Monte Carlo ya se corrió a dieciséis** y el resultado depende de qué se
considere la unidad, que es justo lo que la partición cambia:

| dispersión del chip | placas de 4 limpias | módulos de 16 limpios como bloque |
|---|---|---|
| 2,0 % | 99,97 % | 99,91 % |
| 3,0 % | **98,33 %** | 93,42 % |
| 4,0 % | 91,63 % | 69,54 % |

La columna de la derecha asusta y **no es la que manda**: cuando un oscilador cae
fuera del margen se cambia una resistencia **en su placa de cuatro**, no se tira
el módulo. A 3 % de dispersión eso son **6,5 % de módulos que piden un retoque en
una sola de sus cuatro placas**. La aserción de «95 de cada 100 sin tocar una
resistencia» sigue en pie sobre la placa, que es la unidad real.

*(Detalle a arreglar al parametrizar: el rótulo de la tabla dice «placas 4/4 OK»
escrito a mano y no sigue a `VOCES`.)*

## 10. Consumo

Del datasheet: cada SSI2130 pide **+3,75 mA / −2,90 mA** típicos y **100 µA de la
referencia**. Dieciséis chips son **60 mA**, **46 mA** y, sobre todo, **1,6 mA de
carga en la ADR4525** — cuatro veces la de la v1, y ese número deja de ser
despreciable: entra en el presupuesto con su margen, y probablemente pide un
buffer por placa en vez de colgar los dieciséis de la referencia desnuda
(riesgo 2).

Más los dos micros, los 32 LED —que tienen su propio árbitro de brillo abierto en
el #104— y los operacionales de los juguetes.

**El recuento se hace con las placas delante**, no extrapolando de la línea de la
v1. Es el punto 6 del #158 y sale como tarea del plan, no como número de este
spec.

## 11. Riesgos y decisiones abiertas

Cada uno con cómo se cierra, que es la puerta de esta fase.

1. **El fondo del apilado descansa en dos supuestos sin medir.** Con conectores
   de 5 mm sobra sitio; con los de 10 cabe por dos décimas de milímetro.
   Cierra: medir cuánto sobresale el jack por detrás del panel, elegir la altura
   del conector de apilar, y escribir `depth_budget.py` con su aserción contra el
   fondo del case. **Antes de fijar la geometría.**
2. **La referencia alimenta dieciséis osciladores y cruza conectores.** Son
   1,6 mA contra los 400 µA de la v1, más la caída de los contactos. Cierra:
   extender `dac_local_budget.py` con el término del contacto y el buffer local
   por placa, escribir `vref_load_budget.py`, y aserir que el suelo de afinación
   de las placas lejanas no empeora más de lo presupuestado. Si no se cumple, la
   salida conocida es una referencia por columna — a costa de que los errores
   dejen de escalar juntos entre columnas, que es justo lo que da la precisión de
   desafinado de §7.7.
3. **Cuántos canales de convertidor y de qué familia.** Cincuenta y cuatro
   canales son catorce chips de cuatro o siete de ocho. Cierra: `dac_channels.py`
   con el conteo, y verificar la familia de ocho canales contra su datasheet —
   pinout, referencia interna apagable y comportamiento de la cadena— antes de
   proponerla en firme.
4. **Los micros candidatos no están confirmados contra su datasheet**: máquinas
   de estado de PIO, entradas analógicas, pines totales y consumo. La cuenta de
   §6 cierra **justo** —16 de 16 entradas analógicas—, así que un error aquí
   rompe el reparto en columnas. Cierra: leer el datasheet y escribir el
   presupuesto de pines **antes que ninguna otra cosa del bloque digital**.
5. **El blob de calibración no cabe en la EEPROM, y ahora por mucho.** 2688 B
   contra 250 presupuestados. Cierra: definir el formato del blob (lo decide el
   firmware) o cambiar la pieza.
6. **La latencia del maestro al esclavo.** El segundo micro recibe sus órdenes
   reenviadas, no directas. Irrelevante para el tono; **no irrelevante para un
   disparo**. Cierra: el presupuesto de temporización de evento del contrato
   (riesgo 1 de ese documento), que es la misma pieza que pide el #160.
7. **Dieciséis encapsulados de 4×4 mm soldados a mano, en un proyecto que nunca
   ha fabricado nada.** El SSI2130 es de proveedor único y la fábrica no lo
   monta: probado contra el pedido real, sale «8 shortfall» y el flujo de
   ensamblaje no acepta piezas sin stock. Son ~96 USD solo en osciladores.
   Cierra: comprar dieciséis más repuestos al arrancar, y **montar una columna
   completa antes de poblar la segunda** (decisión 13).
8. **La dispersión chip a chip del conversor exponencial** sigue sin garantizarla
   ningún datasheet, y con dieciséis chips la probabilidad de tocar la cola sube.
   Se hereda de la v1 y se cierra igual: midiendo los chips reales en el
   bring-up, ahora con dieciséis muestras en vez de cuatro — que es, de paso, la
   mejor medida de esa dispersión que va a tener el proyecto.

## 12. Fuera de alcance

- **El enrutado del instrumento** —matriz en el módulo 4, topología en estrella,
  el audio yendo y volviendo de un módulo central— se decidió abrirlo como su
  propio ciclo de diseño. Toca `architecture-poly.md` §5 y §6, define el módulo 4
  y condiciona el 5, 6, 7 y 8. **No bloquea este spec**: el VCO produce y no
  consume, así que saca sus salidas por sus jacks vaya donde vaya el cable.
- **Reordenar la cadena** (VCA antes del filtro) — sigue necesitando un cable.
- **El firmware**, del cerebro y de los dos micros. Este módulo define su
  contrato, no su código.
- **Ondas crudas al patch bay** — descartado en la v1 y no se reabre sin dato
  nuevo. Con dieciséis osciladores serían 64 jacks.
- **Los módulos 5, 6 y 7.** Se especifican para ocho voces con destino de timbre
  por voz, pero no se dibujan en este ciclo. Ojo con el conteo: dieciséis
  osciladores en pares de FM dan **ocho voces de salida**, así que aguas abajo el
  instrumento sigue siendo de ocho.

## 13. Issues que hay que abrir o actualizar

Este spec **excede el #158**, que pedía duplicar voces. Al escribir el plan:

- **#158** — actualizar con el alcance real: dieciséis osciladores, no ocho;
  exactitud, juguetes, patch bay de treinta y dos, dos micros y seis placas.
- **#152** (censo de anchos del case) — el ancho real de este módulo son 228 mm,
  y el censo todavía lista tres VCO fantasma de la arquitectura vieja.
- **Nuevo** — el datasheet del SSI2130 no estaba versionado; queda versionado con
  este spec, y hay que revisar si otros módulos citan fuentes que tampoco están.
- **Nuevo** — la escala del jack de CV externo (§5.1): sesgo sistemático de
  +11,5 cents por octava en la v1.
- **Nuevo** — el enrutado del instrumento, para abrir su ciclo (§12).
- **Nuevo** — dieciséis muestras del SSI2130 son la mejor medida de dispersión
  chip a chip que va a tener el proyecto (riesgo 8): que el bring-up la registre
  como dato, no solo como aprobado o suspenso.
