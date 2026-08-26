# Módulo 3 v2 — VCO ×16 en seis placas: el cobre

> Sustituye a [`2026-08-16-modulo-3-vco-design.md`](2026-08-16-modulo-3-vco-design.md).
> Origen: #158 — el instrumento se diseña para ocho voces. **Este spec va más
> lejos: dieciséis osciladores en un solo módulo**, decidido con Samuel el
> 2026-08-22.
>
> **Este documento es solo cobre.** Piezas, geometría, presupuestos ejecutables y
> bring-up. Todo lo que sea protocolo, mensajes, ciclo de vida, arranque,
> cadencias o modelo de parámetros vive en
> [`2026-08-22-vco-orquestacion-design.md`](2026-08-22-vco-orquestacion-design.md)
> y aquí solo se referencia.
>
> La partición en dos documentos, y las correcciones que este incorpora, salen de
> [`2026-08-22-junta-vco-hallazgos.md`](2026-08-22-junta-vco-hallazgos.md) §2 y §3.
> El contrato que este spec producía se disolvió en esa misma junta: ver
> [`2026-08-22-contrato-modulo-voz-design.md`](2026-08-22-contrato-modulo-voz-design.md).

## 0. Qué cambia, y por qué sale barato cambiarlo ahora

La v1 —cuatro voces en una placa de 114 × 124 mm— **nunca se fabricó**. Su
`notes/medidas.csv` tiene 65 filas y **cero medidas**: el trabajo llegó hasta el
check de gerbers, que el repositorio describe como «el último paso antes del
dinero», y ahí paró. Ninguna placa de este proyecto se ha fabricado todavía.

Eso convierte este rediseño en una decisión de papel contra papel. Lo que se
conserva de la v1 no es una placa: es un **layout validado** (reparto 2×2 de
voces, plano de masa medido, escapes del QFN, DRC en 0) y **cuatro presupuestos
ejecutables**. Los dos se reutilizan.

Y una segunda razón, que la junta añadió: **el cobre no se itera y el software
sí.** Por eso este documento avanza solo y el de orquestación se resuelve contra
el núcleo digital, que es firmware y por tanto barato de cambiar.

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
solo, los micros enrutan los dieciséis contra los dieciséis por dentro.

Dos objetivos medibles, y los dos son aserciones de guion, no prosa:

| Objetivo | Dónde se asevera |
|---|---|
| Las 7 octavas de cada uno de los dieciséis osciladores dentro del rango del convertidor, **sin trimmers** | `pitch_budget.py`, evaluado **por placa de cuatro** |
| La escala del jack de CV externo dentro de **3 cents por octava**, medida desde una fuente de impedancia despreciable | `cvscale_budget.py` (§6) |

El segundo objetivo era inalcanzable tal como estaba escrito y ahora no lo es:
con resistencias al 1 % cada una vale ±12 cents por octava y hay dos en el
camino. El paso a **0,1 %** (§2, decisión 14) las baja a ±1,2 cents cada una y
deja el peor caso en 2,84 — con 5 % de margen y ni una resistencia más de sobra.
La cuenta entera está en §6.

## 2. Decisiones fijadas (con Samuel, 2026-08-22)

1. **Dieciséis osciladores en un solo módulo**, para FM de ocho voces con la
   matriz de modulación entera (§1). Decidido a sabiendas del coste: dieciséis
   encapsulados de 4×4 mm soldados a mano en un proyecto que nunca ha fabricado
   nada (riesgo 8).
2. **El módulo se mide a sí mismo.** Las cuatro líneas `TUNE_OUT` de los pines
   9-12 del J2 quedan sin usar; los números vuelven por `MISO`. **El contrato del
   J2 no cambia ni un pin** (núcleo §5.3). Cuándo se miden esos números está en
   orquestación §3; con qué cadencia se reportan, en orquestación §7.1.
3. **Del J2 cuelga un micro, no los chips.** El cerebro le habla al micro
   maestro; los conversores cuelgan de un SPI **privado**, dentro del módulo.
   Esto cierra un hueco que el spec del cerebro daba por perdido: su §4.1 dice
   que el requisito de soltar el `MISO` con `CS` alto *«vive en placas que
   todavía no se han dibujado — salvo una, que ya está en gerbers y nunca leyó
   este documento»*. Esa placa es la v1 de este módulo, y aquí se rehace.
   **Esto es una decisión de este módulo, no una ley para los demás**: el núcleo
   §10 sigue teniendo abierto si los módulos 5/6/7 llevan micro propio, y este
   spec no lo cierra (orquestación §7).
4. **Dos diseños de placa, seis unidades**, todas de 4 capas, y **un solo
   módulo**: una identidad, un `CS`, una referencia (§3).
5. **32 jacks en dos filas**: entrada de control y salida por cada oscilador.
6. **Las entradas de control van encadenadas, y la cadena va bufferizada.** El
   pin de normalizado de cada jack alimenta al siguiente en vez de ir a masa, y
   entre etapa y etapa hay un seguidor de tensión. Sin el seguidor, dieciséis
   entradas en paralelo son 3,1 kΩ contra la impedancia de salida del módulo que
   ataque, y **la escala cambia cada vez que se mete o se saca un cable**. El
   detalle y sus números están en §6.
7. **La cabeza de la cadena la alimenta el módulo**, no masa: un seguidor cuya
   entrada es `GNDA` a través de un divisor que el micro puede agitar. Eso deja
   el reposo en 0 V —que es lo musicalmente correcto, porque el tono lo pone el
   convertidor— y de paso da el mecanismo de detección de ocupación de §6.3.
8. **El cable siempre gana.** Cualquier ruta que el cerebro decida se rompe al
   meter un cable en el jack. Que el cerebro **se entere** depende del jack
   elegido (decisión abierta 1) y de su alternativa por correlación (§6.3).
9. **El patrón completo del núcleo §10**: sensado de ocupación en los jacks,
   lectura por ADC de las 16 entradas de control, un LED por jack, EEPROM de
   identidad, y telemetría térmica ampliada.
10. **Exactitud, tres correcciones** (§5): la resistencia de escala, la
    compensación de agudos y la histéresis del comparador de PWM.
11. **Los juguetes** (§10), todo lo que el chip trae y la v1 dejó dormido: sync
    entre osciladores enrutable, FM que cruza el cero, modulación de fase,
    modulación en anillo, los dos caracteres de PWM, la sierra reversible, y
    osciladores que pueden bajar a frecuencia de modulación.
12. **Matriz de enrutado libre: cada oscilador elige de cuál de los dieciséis
    come**, para sync y para modulación. **No es un crosspoint de 256 cruces**:
    es un selector por destino, que ya permite que varios coman de la misma
    fuente. Son **dos matrices distintas** —el sync es digital, la modulación es
    analógica— y salen **32 selectores** repartidos entre las cuatro placas de
    voces (§8). Acotarlo se descartó a propósito: si el enrutado se acota, la
    matriz completa que justifica un solo módulo deja de existir y podrían haber
    sido dos módulos de ocho.
13. **La onda moduladora del anillo sale de otro oscilador**, por el mismo
    selector analógico que la FM. Un concepto de fuente para las dos. El canal
    de convertidor que la v2 le asignaba es el **índice**, no la onda: un
    convertidor da un voltaje de control, no una forma de onda (§10.3).
14. **`R_SCALE` y `R_CVIN` pasan a tolerancia del 0,1 %** en el camino de escala:
    1,2 cents por octava y por resistencia en vez de 12. Es lo que hace
    alcanzable el objetivo de 3 cents/octava del jack (§6).
15. **Camino de silencio por oscilador**, con estado de reposo garantizado por
    hardware —pull, no firmware— como condición de arranque hasta que el
    esclavo confirme (§9). Con dieciséis salidas siempre vivas y sin VCA en la
    placa, un esclavo que no arranca son ocho osciladores sonando.
16. **Un búfer de referencia por placa de voces** (§12). La carga real de la
    ADR4525 no son 1,6 mA sino ~3,2 mA, y además cruza contactos de conector.
    Con el búfer, la referencia no entrega corriente a través de ningún contacto.
17. **Una sola base de tiempo para los dos micros** (§7.2). Dos cristales
    independientes al 50 ppm meten **0,087 cents de sesgo sistemático entre
    columnas**, del mismo orden que la resolución de desafinado prometida, y la
    tabla de calibración lo absorbe como si fuera afinación real.
18. **Un multiplexor analógico por micro**, no ocho entradas analógicas directas
    (§7.1). Descongela el reparto de entradas del micro, que cerraba justo, y
    deja sitio reservado para las perillas.
19. **La memoria pasa a 32 KB**, en un segundo chip I²C, sin tocar el
    24AA02E48 de identidad (§13). Resuelve el blob de calibración **y** deja que
    el módulo cargue su propio descriptor.
20. **La cadena de LED es del instrumento y el módulo solo la atraviesa**
    (§14). El núcleo la declara un mazo del cerebro que encadena todos los
    paneles; este módulo no la gobierna.
21. **Las perillas quedan aplazadas** hasta tener la planta del panel dibujada.
    El riesgo que eso traía —que para entonces el reparto de entradas analógicas
    del micro estuviera congelado— lo cierra la decisión 18, que reserva sitio
    por adelantado.
22. **Todo entra como parámetro con descriptor y ámbito declarado**
    (`por-voz` / `compartido`). Sin jumpers, sin modos escondidos. El modelo de
    parámetros, sus exclusiones y sus cadencias viven en orquestación §5 y §6.
23. **Montaje escalonado por columnas.** Se fabrican las seis placas de una vez y
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
   228,6 mm de ancho (45 HP) · 2 placas de fondo · 4 capas cada una
```

- **Placa de panel** (×2): 16 jacks en dos filas de ocho, 16 LED de la cadena del
  instrumento, sensado de ocupación, y los **ocho seguidores de la cadena de
  entradas de control** (§6).
- **Placa de voces** (×4): 4 osciladores con **su propio convertidor al lado**,
  su búfer de referencia, su sensor de temperatura, sus ocho selectores de matriz
  y el sitio del micro y su entorno. En dos de las cuatro ese sitio se puebla; en
  las otras dos se deja vacío.

**Por qué el convertidor va en todas y no en una central.** Un LSB son 38,15 µV
(2,5 V / 65 535) y valen 0,139 cents (7,576 octavas × 1200 / 65 535), así que
**un milivoltio de caída o de ruido en un contacto son 3,6 cents** metidos
directos en la afinación. Es el mismo efecto que `dac_local_budget.py` ya midió
al comparar el convertidor en el módulo (0,58 cents de suelo) contra el
convertidor en el cerebro (1,71). **El tono se genera siempre pegado a su
oscilador y no cruza ninguna unión.**

**Por qué dos micros.** El argumento se estrechó, y conviene decir en qué. La v2
lo justificaba con dos recursos —máquinas de estado de PIO y entradas
analógicas— y la decisión 18 elimina el segundo: con un multiplexor por micro
sobra entrada analógica. **Lo que sostiene los dos micros es solo el PIO**:

| Recurso | Piden 16 osciladores | Da un RP2350B | Con dos |
|---|---|---|---|
| Cronómetros de PIO | 16 | 12 *(a confirmar — riesgo 4)* | 16 de 24 |
| Entradas analógicas | 2 (una por mux de 16:1) | 8 | 2 de 16 |

Ocho osciladores por micro es lo que hace que la cuenta del PIO cierre, y es la
razón de que el módulo se parta en columnas y no de otra forma. **Uno es el
maestro** —el único que habla por el `MISO` del J2— y el otro cuelga de su SPI
privado como un periférico más.

> ### ⚠️ Enmienda del 2026-08-26: **esta tabla dejó de tener sujeto**
>
> Fila mandada del mapa de motor-digital §9 (*«las máquinas PIO libres del
> RP2350B dejan de existir como recurso»*).
>
> El módulo de Voz pasa a **un solo STM32N657** (motor-digital, acta A-1). No
> hay RP2350B en esta placa, así que **la columna «Da un RP2350B» y la columna
> «Con dos» no describen nada** — y con ellas se cae la partición en columnas
> que esta sección justifica.
>
> **Lo notable es que el argumento de arriba era correcto, y por eso resultó
> letal.** La v2 tenía dos razones para dos micros; la decisión 18 mató una, y
> esta sección dejó la otra al desnudo con una honestidad que se paga sola:
> *«lo que sostiene los dos micros es solo el PIO»*. Un diseño que se apoya en
> un solo recurso se cae entero el día que aparece un chip que da ese recurso
> de sobra. **Apareció**: el N657 trae los dieciséis cronómetros en timers de
> hardware, no doce máquinas de PIO. Muerta la escasez, muere la partición.
>
> Lo que hay que leer de esta tabla hoy es **solo su primera columna** — «16
> osciladores piden 16 cronómetros» —, que sigue siendo verdad y sigue siendo
> el requisito que eligió el chip nuevo.
>
> **Consecuencia para el #205**, que censaba las tres máquinas de PIO libres
> de este micro: su sujeto ya no existe. La decisión de cerrarlo o reescribirlo
> está mandada y **no la toma este papel**.
>
> Lo que **no** toca esta enmienda: la decisión 18 y su multiplexor, el
> convertidor pegado a cada oscilador, la tabla del conector, y todo lo
> analógico. Cambió quién cuenta los flancos, no cómo se generan.

**Una sola referencia para los dieciséis**, en la placa maestra, distribuida y
**bufferizada en cada placa** (§12). Es lo que hace que los errores escalen
juntos y, sobre todo, lo que hace que **desafinar dos osciladores entre sí sea
más fino que afinarlos en absoluto** (§10.7).

Qué cruza los conectores, y por qué aguanta:

| Señal | Por qué tolera cruzar |
|---|---|
| Alimentación ±12 V, masas | Es lo que ya cruza hoy por el J1 |
| `VREF` 2,5 V | Continua, y **sin corriente**: cada placa la bufferiza al llegar (§12). El contacto no cae porque no circula nada por él |
| El SPI **privado** del maestro, e I²C | Digitales. Ojo: no es el SPI del instrumento — ese muere en el maestro (decisión 3) |
| Pulsos de afinación hacia su micro | Digitales, 3,3 V, ya limpiados por el Schmitt. **Se quedan dentro de su columna** |
| CV de mezcla y de PWM (compartidos) | Un 1 % de desparejo entre osciladores es amplitud, no tono — igual que en la v1 |
| **16 líneas de sync** (bus de la matriz digital) | Digitales, 3,3 V |
| **16 líneas de modulación** (bus de la matriz analógica) | Audio de baja impedancia, salida de op-amp |
| CV externo ya bufferizado, del panel a las voces | Baja impedancia. Lo que sí cruza y **cuenta** es la diferencia de masa entre las dos placas: presupuestada en `cadena_cv_budget.py` (§6.4) |
| Audio hacia el panel | Baja impedancia, salida de op-amp |
| `RESET_ESCLAVO` y `OK_ESCLAVO` | Digitales, con pull al estado seguro (§9) |
| Cadena WS2812, de paso | Mazo propio, `GNDD` (§14) |

**Lo que NO cruza:** el CV de tono que sale del convertidor de cada oscilador.

### 3.1 Lo que gana partir así

| | piezas del layout más difícil |
|---|---|
| Un módulo de dieciséis en un solo layout | ≈960, todas nuevas |
| **Dos diseños repetidos** | **≈215**, sobre un layout que ya está ruteado y con DRC en 0 |

Y el reparto paga una segunda vez donde no se esperaba: **la unidad que se
retoca es la placa de cuatro, no el módulo.** Si un oscilador cae fuera del
margen se cambia una resistencia en su placa. A 3 % de dispersión, el 98,33 % de
las placas de cuatro salen limpias, así que **el 6,5 % de los módulos pedirá un
retoque en una sola de sus cuatro placas** — muy distinto del 93,42 % de módulos
limpios que sale de mirarlo como un bloque indivisible de dieciséis (§15).

## 4. La cota que manda: el fondo, y por eso se estira a lo ancho

El panel es 3U de Eurorack: **128,5 mm de alto**, y la fila da **528 mm útiles**
(`case/cad/params.scad`, `case/clearance_budget.py`). La placa de la v1 mide
124 mm de alto, o sea que **a lo alto no queda nada**.

Y apilar tampoco escala: cuatro placas de voces en una sola columna piden más
fondo del que da el 68 % del panel. Por eso el módulo **se estira a lo ancho**:
dos columnas de dos.

**La fila del fondo estaba mal sumada en la v2** y se corrige aquí: 1,6 mm de
placa más una pieza de ~9 mm son 10,6 mm, no 7,6.

| | mm | fuente |
|---|---|---|
| Jack por detrás del panel | 13,0 | **SUPUESTO — hay que medirlo** (riesgo 1) |
| Placa de panel | 1,6 | espesor estándar de 4 capas |
| Conector de apilar | *h* | **decisión abierta 3** |
| Placa de voces + su pieza más alta | 10,6 | 1,6 de placa + 9,0 del IDC 2×6 |
| Conector de apilar | *h* | |
| Placa de voces + su pieza más alta | 10,6 | |
| **Total** | **35,8 + 2·*h*** | contra **50,0** disponibles en el 68 % del panel |

De ahí sale el número que manda:

> ***h* ≤ 7,1 mm.** Y por cada milímetro que el jack sobresalga más de los 13,0
> supuestos, *h* baja medio milímetro.

Con conectores de 5 mm el total son 45,8 y sobran 4,2. **Con conectores de 10 mm
son 55,8 y no cabe** — la v2 decía que cabía por dos décimas, y eso salía de la
fila mal sumada.

> **La altura del conector de apilar es una decisión de diseño con presupuesto
> propio, no un detalle de montaje.** Y el fondo del jack se mide antes de cerrar
> la geometría, no después. `depth_budget.py` lo asevera.

**El ancho:** 228,6 mm (45 HP) de los 528 de una fila. Los 32 jacks piden 191 mm
repartidos en dos filas de dieciséis —12 mm de paso por jack, ocho por fila y por
placa de panel—, que caben de sobra, y las dos filas se llevan unos 40 mm de los
128,5 de alto del panel. El instrumento entero —este módulo, cerebro, filtro,
envolvente, VCA y mezclador— sale en **≈799 mm de los 1056** que dan las dos
filas, con 257 de sobra. Eso hay que meterlo en el censo del case, que es el
#152.

## 5. Exactitud: tres correcciones al núcleo heredado

Las tres salen de leer el datasheet del SSI2130 (rev. 2.4, dic. 2020) como fuente
primaria. **Ese PDF no estaba en el repositorio** —se citaba como origen de las
decisiones de la v1 y vivía en una carpeta temporal del sistema. Se versiona con
este spec.

### 5.1 La resistencia de escala va corta un 0,75 %, y corregirla GASTA margen

El datasheet da la relación exacta (pág. 14): **I_SCALE = 4,717 × I_octava**.
Para los 20 µA/octava de diseño son 94,34 µA, o sea **26 499,9 Ω** desde la
referencia. El BOM de la v1 lleva **26,7 kΩ** —el valor de catálogo más cercano,
porque 26,5 no existe en E96—, lo que deja la sensibilidad real en
**19,850 µA/octava** en vez de 20,000.

La v2 escribió el sentido al revés. Con la relación del datasheet aplicada, el
balance es este:

| | I_octava | span extrapolado B | margen sobre 7,0 oct | error de escala del jack |
|---|---|---|---|---|
| v1: `R_SCALE` = 26,7 kΩ | 19,850 µA | **7,633** | 8,29 % | **+11,5 cents/octava**, acumulativo — 57 cents a cinco octavas |
| 26,5 kΩ, el valor que da el datasheet | 19,998 µA | 7,576 | 7,60 % | +2,41 cents/octava |
| **corregido: 26,1 kΩ + 348 Ω = 26 448 Ω** | 20,038 µA | **7,561** | 7,44 % | **+0,05 cents/octava** |

O sea: **la v1 tenía más margen del que creía y la corrección lo gasta**, de
8,29 % a 7,60 %. Sigue valiendo la pena, y por una razón que no es el span: el
error del jack no es tolerancia que se promedie entre placas, es un **sesgo
sistemático**, igual en todas y siempre en la misma dirección, y ahí no hay tabla
de 84 notas que lo absorba. Al convertidor no le afecta —el autoafinado mide la
frecuencia real y lo mete en la tabla—; al jack sí.

Y un efecto lateral que hay que decir en voz alta: **el 7,60 % que la v1 tenía
escrito en prosa era el número correcto para el diseño corregido, por
coincidencia.** Todos los rendimientos de Monte Carlo de §15 se calcularon
suponiendo 20,000 µA/octava exactos, que es justo lo que el diseño corregido
entrega. **La tabla de rendimiento no se mueve.** Lo que se mueve es de dónde
sale: deja de ser una suposición y pasa a ser el resultado de poner la
resistencia correcta.

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
lo único que sostiene la apuesta, ahora que §5.1 le quitó siete décimas.

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
**sin chasquidos**. Es una forma limpia de silenciar el pulso, y §9 la usa.)*

## 6. Las entradas de control: la cadena, la escala y la ocupación

Es el bloque que la v2 dejó sin piezas y con tres huecos a la vez: la cadena
rompía la escala, el pin del jack no puede hacer dos trabajos, y no estaba
declarado qué alimenta la cabeza de la cadena. Los tres se cierran aquí.

### 6.1 Por qué la cadena cruda rompe la escala

La entrada de cada oscilador es una resistencia al nodo de suma:

> `R_CVIN` = 1 V / I_octava = 1 V / 20 µA = 50 kΩ → **49,9 kΩ** (E96, 0,1 %)

Encadenar los normalizados sin bufferizar pone **todas** las `R_CVIN` de aguas
abajo en paralelo contra la fuente externa. Dieciséis en paralelo son
49,9 kΩ / 16 = **3,12 kΩ**, y contra una salida de módulo de 1 kΩ eso es un
divisor que se come el 24 % de la señal: **291 cents por octava**. Peor todavía,
**el número de entradas en paralelo cambia cada vez que se mete o se saca un
cable**, así que ninguna calibración lo puede absorber: cambia en tiempo de
patcheo.

### 6.2 La cadena bufferizada, y qué cuesta

Un seguidor de tensión por entrada, **en la placa de panel, pegado a su jack**:

```
  jack n ──┬──[R_prot]── (+) seguidor n ──┬── R_CVIN ── nodo de suma del osc. n
           │                              │
        [R_bias]                          └── TN del jack n+1  (normalizado)
           │
       nodo n-1 (etapa anterior)
```

Qué compra, término a término:

| | Sin seguidor | **Con seguidor** |
|---|---|---|
| Carga que ve la fuente externa | 49,9 kΩ / N, con N variable | **Una entrada de op-amp con su `R_bias`, constante** |
| Error de escala por impedancia de fuente | 291 cents/oct con 16 entradas y 1 kΩ | 1200 · R_out / R_bias — **1,2 cents/oct** con 1 kΩ y `R_bias` = 1 MΩ |
| ¿Cambia al patchear? | **Sí** | No |
| Piezas | ninguna | 16 seguidores = **4 cuádruples**, más `R_bias` y protección |

Dos cosas que hay que decir para que nadie las descubra tarde:

**El desplazamiento acumulado de dieciséis etapas no importa, y se puede
demostrar.** Los desplazamientos se suman a lo largo de la cascada, pero **son
los mismos con cable y sin cable**: enchufar sustituye lo que entra por la
cabeza, no cambia los seguidores de aguas abajo. Un error de continua invariante
frente al patcheo lo **mide y lo corrige la tabla de 84 notas**. Lo que sí
importaría es un error de ganancia, y un seguidor de ganancia unidad tiene
menos de 1 ppm a continua. Por eso el requisito sobre el op-amp de la cadena es
**corriente de polarización baja** (entrada FET, ≤100 pA, para que `R_bias` de
1 MΩ no meta más de 100 µV), no desplazamiento de precisión.

**La `R_bias` existe por el cable colgando.** Un cable enchufado con el otro
extremo al aire deja la entrada del seguidor flotando, y una entrada FET flotante
se va a un riel. `R_bias` va **al nodo de la etapa anterior**, no a masa: así,
mientras no hay cable, no cae tensión sobre ella y no carga la cadena.

**La impedancia de entrada se declara, no se esconde.** El módulo presenta
≥1 MΩ, constante e independiente del patch. Una fuente de impedancia `R_out`
añade `1200 · R_out / 1 MΩ` cents por octava, y eso es del que ataca, no del
módulo. El objetivo de 3 cents/octava de §1 se mide **desde una fuente de
impedancia despreciable**, y así lo asevera el guion.

### 6.3 El pin del jack no puede hacer dos trabajos

El Thonkiconn `WQP-PJ398SM` tiene tres patillas: punta, masa y `TN`, el contacto
que se abre al meter un cable. **`TN` es o el camino del normalizado o el bit de
ocupación, no las dos cosas.** Y el reparto no es simétrico:

| | Jacks | `TN` | Ocupación |
|---|---|---|---|
| **Salidas de audio** | 16 | libre, no hay nada que normalizar | **Directa**: `TN` a un pull-up y a un registro de entrada serie |
| **Entradas de control** | 16 | ocupado por la cadena | Ver abajo |

Para las dieciséis entradas de control hay dos caminos y el orden entre ellos
está decidido:

**Camino A, preferido — un jack con contacto de conmutación independiente.**
Cuatro patillas: punta, masa, normalizado y un interruptor aparte. Si existe en
el mismo formato mecánico, hay normalizado en cascada **y** sensado directo.
Decisión abierta 1.

**Camino B, si el jack no existe — ocupación por correlación, y no cuesta una
pieza.** Las dieciséis entradas ya son legibles por ADC a través del mux de §7.1,
porque el núcleo §10 lo exige para el barrido por inyección. Y la cabeza de la
cadena la alimenta el módulo (decisión 7), o sea que es un nodo que el micro
puede **agitar**. Entonces:

> Se mueve la cabeza de la cadena con un código ortogonal de amplitud pequeña y
> se correlaciona en cada entrada. **Donde aparece el código, no hay cable**
> (la cadena llega). **Donde no aparece, hay un cable** que la rompió.

Es exactamente el motor de perturbación que el núcleo §7.6 ya especifica y que
`software/nucleo/core/src/perturbacion.rs` ya implementa y valida en simulación,
aplicado dentro del módulo. Ni una pieza nueva, y una regla de degradación que ya
está escrita: cuando la correlación no es concluyente **no adivina**, reporta
hueco (orquestación §4).

La amplitud del código y su audibilidad se acotan en `cadena_cv_budget.py`: con
una excursión de ±2 LSB del camino del jack —±76 µV, o sea ±0,09 cents— el
código está 20 dB por debajo del paso de desafinado más fino que el módulo
promete, y aun así la ganancia de correlación lo saca del ruido.

### 6.4 El presupuesto de la escala del jack

Lo que hace alcanzable el objetivo es la decisión 14: `R_SCALE` y `R_CVIN` al
0,1 %.

| Término | Fuente | cents/octava |
|---|---|---|
| `R_SCALE` nominal: 26,1 kΩ + 348 Ω = 26 448 Ω contra el ideal **26 447 Ω** | ver nota de abajo | **+0,05** sistemático |
| `R_SCALE`, tolerancia 0,1 % | decisión 14 | ±1,20 |
| `R_CVIN` = 49,9 kΩ, tolerancia 0,1 % | decisión 14 | ±1,20 |
| `VREF`, precisión inicial ±0,02 % | ADR4525BRZ (`pitch_budget.py`, `TOL_VREF`) | ±0,24 |
| `VREF`, deriva 2 ppm/°C sobre 20 °C = 40 ppm | ADR4525BRZ (`architecture-poly.md` §8) | ±0,05 |
| Desplazamiento del búfer de referencia por placa, ≤100 µV = 40 ppm | requisito de §12 | ±0,05 |
| **Peor caso, suma lineal** | | **2,79** |
| *Suma en cuadratura de los aleatorios, más el sistemático* | *(referencia, no es el criterio)* | *1,75* |

> **De dónde sale el ideal de 26 447 Ω, y por qué no son los 26 500 del
> datasheet.** El datasheet da 26,5 kΩ para 20 µA/octava **suponiendo entradas de
> 50 kΩ exactos**, y el BOM lleva 49,9 kΩ, que es el valor de catálogo más
> cercano. Lo que tiene que salir clavado no es la corriente de escala: es **la
> razón** entre la corriente que entra por el jack y la corriente por octava. Con
> `R_CVIN` = 49,9 kΩ eso pide `R_SCALE` = VREF · R_CVIN / 4,717 = **26 447 Ω**.
> Perseguir el número del datasheet en vez de la razón deja **2,41 cents/octava**
> sobre la mesa, casi la mitad del presupuesto entero. `cvscale_budget.py` deriva
> el nominal, no lo copia.

**2,84 contra 3,00: 5 % de margen.** El criterio se cumple en peor caso, que es
como se asevera, y la conclusión operativa es dura y hay que escribirla:

> **Ninguna resistencia más entra en el camino de escala del jack sin volver a
> correr `cvscale_budget.py`.** No hay sitio.

Y una segunda, del mismo cálculo: **el desplazamiento del jack es otra cosa que
la escala.** Sin cable, la cadena está en 0 V y el autoafinado se come cualquier
desplazamiento. Con cable, un desplazamiento de la fuente o de la cadena aparece
como corrimiento fijo de tono, `1200 · V_off / 1 V` cents. Se declara, no se
presupuesta contra el objetivo de escala, que es un criterio de pendiente.

`VREF` sí entra en la escala del jack, y conviene ver por qué no contradice a
`pitch_budget.py`: en el span del convertidor, `VREF` está en el numerador y en
el denominador y **se cancela**. En el jack no, porque la corriente que inyecta
el cable no depende de `VREF`. Son dos caminos distintos y la referencia les
hace cosas distintas.

## 7. El bloque digital: dos micros, un multiplexor y una sola base de tiempo

**Dos** micros, uno por columna, candidato **RP2350B**, con el encaje que hay que
**confirmar contra su datasheet antes de fijarlo** (riesgo 4).

### 7.1 Un multiplexor por micro, no ocho entradas directas

La v2 gastaba las ocho entradas analógicas de cada micro en las ocho entradas de
control de su columna. Cerraba justo —16 de 16— y cualquier error rompía el
reparto en columnas. Además dejaba cero sitio para las perillas, que es el riesgo
que la decisión 21 aplazaba.

Se cambia por lo que el propio instrumento ya hace en todas partes
(`architecture-poly.md` §7, núcleo §10): **un multiplexor analógico 16:1 por
micro, a una sola entrada de ADC**. Ocho canales para las entradas de control,
ocho reservados para perillas.

Y hay una razón por la que no cuesta nada, que conviene dejar clara: **la lectura
por ADC de una entrada de control es auditoría, no camino de señal.** El CV del
jack llega al oscilador por cobre, a través de `R_CVIN`, en hardware. Lo que el
ADC hace es enterarse de qué hay ahí, para el barrido por inyección y para la
ocupación de §6.3. Unos cientos de hercios sobran, que es justo lo que
`architecture-poly.md` §7 ya dice del mux de perillas.

| | v2 | **Ahora** |
|---|---|---|
| Entradas analógicas usadas por micro | 8 de 8 | **1 de 8** |
| Sitio para perillas | ninguno | 8 canales por columna |
| Piezas | ninguna | 1 mux 16:1 + 4 GPIO de dirección por micro |

Con esto, la cuenta de recursos deja de cerrar justo por dos sitios y cierra
justo por uno solo: el PIO (§3).

### 7.2 Dos micros son dos cristales, y eso se ve en la afinación

El presupuesto de afinado tiene un solo `F_PIO`, y aquí hay dos relojes. Un
desajuste de **50 ppm** entre los dos cristales —tolerancia corriente de un
cristal de catálogo— sesga todas las medidas de una columna respecto a la otra:

> 1200 · log₂(1 + 50·10⁻⁶) = **0,087 cents**

Eso es el 63 % del paso de desafinado más fino que el módulo promete
(1 LSB = 0,139 cents, §10.7), y es **sistemático**: la tabla de calibración lo
absorbe como si fuera afinación real, así que las ocho voces de una columna
quedan corridas respecto a las otras ocho y nadie se entera.

**Decisión: una sola base de tiempo para los dos micros.** El maestro es el dueño
del reloj y el esclavo lo toma de él; la línea cruza el conector como una señal
digital más, que es lo que ya hacen el SPI privado y el I²C. Con una sola base,
el sesgo es cero por construcción.

Si al leer el datasheet resulta que el micro no puede tomar reloj externo ni
sacar el suyo por un pin (riesgo 4), la salida conocida es **medir la razón entre
los dos relojes en el bring-up y publicarla como constante de calibración**,
porque el conteo recíproco escala todas las medidas de una columna por un factor
constante. Lo que esa salida **no** cubre es la deriva térmica diferencial entre
dos cristales distintos, que sí se mueve entre pasadas — y por eso es la
alternativa, no el plan.

`autotune_budget.py`, al mudarse (§15), asevera una de las dos: base única, o
constante de razón medida con su residuo por debajo de 0,035 cents (un cuarto de
LSB).

### 7.3 Qué hacen los micros

El conteo recíproco es el mismo que el núcleo §5.1 ya presupuestó, así que
**`autotune_budget.py` se muda al módulo casi tal cual** en vez de rehacerse: los
6,67 ns de sellado derivados del reloj y los **131 ns de jitter máximo del
74HC14** siguen valiendo, porque la arquitectura de medida no cambia de forma.

| Tarea | Detalle |
|---|---|
| Cronometrar sus ocho osciladores | En paralelo. El barrido no se alarga por haber más |
| Leer sus ocho entradas de control por el mux | Y hacer posible el barrido por inyección del núcleo §7.6 |
| Sensar sus 16 jacks | Directo en las salidas; en las entradas, según §6.3 |
| Gobernar el enrutado de sync y de modulación | Escribiendo los registros de §8 |
| Escribir sus conversores | Por el SPI privado (decisión 3) |
| Gobernar el `OE` de sus registros | Es el camino de silencio de §9 |
| Telemetría | §13 |

**Lo que los micros NO hacen: sonido.** No hay camino de audio que pase por
ellos. Es la misma regla que el núcleo §5.0 le impone al cerebro, aplicada aquí.

**Y lo que tampoco hacen: interpolar.** El glide, el portamento y el suavizado
viven en el cerebro y en un solo sitio. La razón —dos interpoladores en serie
destruyen la rampa de duración cero, que está definida como salto deliberado— y
la tasa de trama que eso obliga están en orquestación §5.3.

**Lo que tampoco gobiernan: la cadena de LED** (§14).

Y una obligación que no es suya sino del bus, y que **solo cumple el maestro**:
deja el `MISO` en alta impedancia siempre que su `CS` esté alto, sin excepciones
de modo. Se mide en el bring-up: `CS` alto, `MISO` sondado, aprobado o suspenso.
**El esclavo no toca el J2 en ningún caso.** La regla, en su forma general y
aplicable a cualquier placa, está en orquestación §7.

## 8. Las dos matrices, y qué piezas cuestan

Es el bloque que la v2 declaraba como la razón entera de que el módulo sea de
dieciséis y al que no le asignó ni una pieza. Aquí las lleva.

**No es un crosspoint.** Un crosspoint de 16×16 son 256 cruces. Esto es un
**selector por destino**: cada oscilador elige de cuál de los dieciséis come, y
que varios coman de la misma fuente sale gratis porque las fuentes son buses.

| | Qué elige | Naturaleza | Selectores | Bus |
|---|---|---|---|---|
| **Matriz de sync** | Qué cuadrada ataca la entrada de sync de este oscilador | Digital, 3,3 V | 16 (uno por oscilador) | 16 líneas |
| **Matriz de modulación** | Qué onda alimenta la FM/PM **y** el anillo de este oscilador | Analógica, audio bipolar | 16 (uno por oscilador) | 16 líneas |

**Un concepto de fuente para las dos** modulaciones: el selector analógico de un
oscilador entrega **una** onda, y de ahí salen dos caminos con **dos índices
independientes** —FM/PM y anillo— cada uno con su canal de convertidor (§11).

Piezas por placa de voces (4 osciladores):

| Pieza | Cantidad | Para qué |
|---|---|---|
| Multiplexor 16:1 digital | 4 | Selector de sync |
| Multiplexor 16:1 analógico, rango bipolar | 4 | Selector de modulación. **Decisión abierta 2** |
| Registro serie con salida latcheada, 8 bits | 7 | Los 56 bits de control de la placa |

Los 56 bits, desglosados, porque de ahí sale el 7:

| Control | Bits por oscilador | Por placa |
|---|---|---|
| Dirección del selector de sync | 4 | 16 |
| Dirección del selector de modulación | 4 | 16 |
| Tipo de sync (duro / suave) | 1 | 4 |
| Modo de modulación (FM / PM) | 1 | 4 |
| Origen de `TIME REVERSE` (comparador de TZ / nivel fijo) y su nivel | 2 | 8 |
| Carácter del PWM (triangular / sierra) | 1 | 4 |
| Silencio | 1 | 4 |
| **Total** | **14** | **56** |

Los registros cuelgan del SPI privado, no del bus del instrumento. Y su `OE` es
la pieza central de §9.

**El coste real de la matriz no son los selectores: es el ancho del bus.** Entre
placas cruzan **32 líneas de señal** solo para esto —16 digitales y 16 de
audio—, y van juntas. Eso obliga a dos cosas:

- **Un conector de apilar dedicado a la matriz**, con masa intercalada entre
  líneas. La alimentación, la referencia y el control van por el otro.
- **Presupuesto de diafonía**, porque son cuadradas de audio corriendo al lado de
  las ondas que hacen FM: `matriz_budget.py` (§15).

Y una consecuencia que no es de cobre pero nace aquí: **cambiar un selector hace
clic**, por inyección de carga del multiplexor. Cuándo se permite cambiar de
ruta lo decide el cerebro, y está en orquestación §5.4.

## 9. El camino de silencio, garantizado por hardware

Dieciséis salidas siempre vivas, sin VCA en la placa y con jacks al panel: **un
esclavo que no arranca son ocho osciladores sonando en cuanto haya un cable**. El
patrón correcto ya existe en el repositorio —el cerebro lo aplicó a los gates con
pull-down por hardware, «con una sola inversión un GPIO flotante abre las cuatro
envolventes de golpe al encender» (núcleo §1)— y este módulo no lo había
aplicado a sus salidas.

**Tres capas, de la más barata a la más cara, y las dos primeras no cuestan una
pieza nueva:**

1. **El `OE` de los registros de §8.** Un registro serie con `OE` en alta
   impedancia deja sus salidas sueltas. Con un **pull-up en `OE`** y un **pull
   por línea al estado seguro**, el reposo al encender es «silencio» sin que
   ningún firmware haya corrido. El micro tiene que bajar `OE` **activamente**
   para que el módulo suene, y el maestro puede volver a subirlo por
   `RESET_ESCLAVO`.
2. **El CV de mezcla del oscilador en su valor de reposo.** El SSI2130 lleva un
   mezclador interno gobernado por CV; con ese CV en el valor «cerrado», la salida
   del oscilador es silencio. Se le pone un **pull de 100 kΩ al valor cerrado**
   en el nodo, para que el estado de reposo no dependa de que el convertidor haya
   arrancado ni de a qué salga. *Que el valor cerrado sea 0 V y no el otro
   extremo está en «lo no confirmado» (§17.1): si el datasheet dice lo
   contrario, el pull va al otro lado y no cambia nada más.*
3. **El silenciador de pulso del propio datasheet.** Llevar la entrada del
   comparador por encima de la referencia o por debajo de masa fuerza la salida
   a un nivel fijo **sin chasquidos** (§5.3). Cubre el camino de pulso, que es el
   que la capa 2 no toca si el mezclador se dejara puenteado.

Y la regla de orden que hace posible el barrido silencioso:

> **El camino de afinación va antes del silenciador.** El `SQUARE OUT` se recorta
> con el 74HC14 aguas arriba del silenciador, igual que `architecture-poly.md` §5
> pone el camino de afinación antes del filtro. Así se puede silenciar el módulo
> entero y seguir midiéndolo.

Eso es lo que devuelve una propiedad que el módulo había perdido: la v1 podía
afinarse en silencio porque el VCA estaba cerrado; con dieciséis salidas a jacks,
cualquier cable patcheado haría audible un barrido de 2,7 s de notas cromáticas.
Con el silenciador, no. Cuándo se usa y con qué política lo dice orquestación
§3.4.

**Las dos señales que el handshake necesita del cobre**, y que hoy no existen —un
esclavo colgado solo se recupera apagando la caja con la mano:

| Señal | Sentido | Reposo garantizado por |
|---|---|---|
| `RESET_ESCLAVO` | maestro → esclavo | Pull al estado **de reset afirmado** |
| `OK_ESCLAVO` | esclavo → maestro | Pull al estado **de no arrancado** |

El protocolo que corre sobre ellas está en orquestación §2.

## 10. Los juguetes

Los juguetes salen de capacidades que el chip ya trae y la v1 dejó latentes «por
alcance, no por capacidad». Su §12 condicionaba abrirlas a «un respin de panel
futuro con dato de uso real». **Este es ese respin**, y el otro argumento de la
v1 —«el sync sin pareja por voz no aporta»— se cae con dieciséis osciladores: ahí
hay ocho parejas, y quién modula a quién lo decide el preset.

### 10.1 Sync entre voces, enrutable

Hard sync (pin 17, umbrales 1,0 / 1,55 V) y soft sync (pin 19, 5 kΩ interna, con
acoplo capacitivo). La salida cuadrada de cualquier oscilador puede atacar la
entrada de sync de cualquier otro, por el selector de §8.

Y una propiedad del chip que hay que tener presente en el cobre porque muerde en
el firmware: **el datasheet dice que si la entrada de sync se mantiene alta el
oscilador se para**. Eso convierte un sync mal puesto en un oscilador mudo, y un
barrido sin timeout en un cuelgue. La consecuencia está en orquestación §3.2.

### 10.2 FM que cruza el cero, y lo que de verdad cuesta

`TIME REVERSE` (pin 18) + `LIN FREQ` (pin 21), según la figura 18 del datasheet:
*«un puñado de pasivos hace de la TZFM y la TZPM una realidad de bajo recuento
de piezas»*.

**La v2 subestimó el coste y aquí se corrige.** No es «medio amplificador
operacional y pasivas por voz»: la figura 18 lleva además **un comparador LM311 y
un MOSFET 2N7000 por oscilador**, y ese LM311 gobierna `TIME REVERSE` **y**
`LIN FREQ` a la vez.

| | v2 decía | **Real, figura 18** |
|---|---|---|
| Por oscilador | ½ op-amp + pasivas | ½ op-amp + **1 LM311** + **1 2N7000** + pasivas |
| En el módulo | 8 op-amps | 8 op-amps + **16 LM311** + **16 2N7000** |
| Por placa de voces | 2 secciones | 2 secciones + **4 LM311** + **4 2N7000** |

Dos consecuencias que no son solo de recuento:

- **El LM311 se apodera de `TIME REVERSE`.** Por eso el control de dirección de
  la sierra de §10.5 no es un bit sino un selector de 2 bits: quién manda en ese
  pin, el comparador o un nivel fijo. Está en el desglose de §8.
- **Dieciséis comparadores son consumo** que la v2 no contaba. Entra en §16 y su
  cifra está en «lo no confirmado» (§17.2) hasta leer el datasheet del LM311.

Cruzar el cero es lo que evita que la FM desafine la nota, que es el defecto de
la FM analógica corriente. Con dieciséis osciladores y el enrutado de §8, esto da
desde dieciséis voces limpias hasta **ocho voces de FM de dos operadores**, y lo
cambia un preset.

### 10.3 Modulación en anillo

Figura 19 del datasheet: un operacional por oscilador y los **dos canales
auxiliares del mezclador interno** —el AUX 2 está libre en la v1— dan un
multiplicador de cuatro cuadrantes. Sonidos metálicos y campanas sin tocar el
camino de tono.

**Corrección de concepto de la v2**: el anillo necesita **una onda moduladora de
audio**, y la v2 le presupuestaba un canal de convertidor. Un convertidor da un
voltaje de control, no una onda. La onda sale del **selector analógico de §8**,
el mismo que alimenta la FM; el canal de convertidor es el **índice**, o sea
cuánto anillo hay.

### 10.4 Modulación de fase, por el precio de un condensador

El mismo circuito de la figura 18 tiene **dos entradas**: una hace FM y la otra
hace modulación de fase. La diferencia es un condensador que deriva la señal
moduladora.

Y no es un adorno, porque el datasheet dice cuál es mejor y por qué:

> «como la señal moduladora va acoplada en continua, cualquier offset deja el
> oscilador desafinado metiendo un desplazamiento constante de frecuencia. La PM
> quita el offset y **mantiene el oscilador afinado**»

O sea: **la FM te desafina la nota y la PM no.** Si ya se paga el circuito de la
FM, dejar fuera la PM sería dejar fuera la mitad buena. Entra, y el bit que elige
entre las dos está en el desglose de §8.

### 10.5 Dos sabores de PWM, y la sierra al revés

**El PWM tiene dos caracteres** según de qué onda se alimente el comparador
(datasheet pág. 7). Con triangular mantiene constante el tiempo entre los centros
de los pulsos. Con sierra, un flanco queda clavado al corte de la sierra y solo
se mueve el otro, y eso **añade un vibrato suave** como parte del propio efecto.
Son dos sonidos distintos y elegir cuesta **un conmutador analógico por
oscilador**. Es el único de este grupo con coste real.

**La sierra se puede invertir.** El pin `TIME REVERSE` no solo sirve para cruzar
el cero: quieto en alto da sierra ascendente y en bajo da sierra descendente. Si
ya se cablea para la FM, esto es gratis — con la salvedad de §10.2: el LM311
también quiere ese pin, así que el control es un selector, no un nivel.

> **Restricción que hay que escribir, porque es el mismo pin:** un oscilador no
> puede tener la sierra fija en una dirección **mientras** hace FM que cruza el
> cero. Son usos excluyentes del mismo pin, y el modelo tiene que decirlo en voz
> alta en vez de dejar que el usuario descubra que un parámetro le pisa el otro.
> Es una de las 26 relaciones que orquestación §6 enumera y que el descriptor
> tiene que poder expresar.

### 10.6 Un oscilador puede ser un oscilador lento

El chip cubre **1000:1 —diez octavas— con menos de un cent de error**
(especificaciones, pág. 2), y el diseño usa siete. El propio datasheet contempla
usarlo de oscilador de baja frecuencia.

Eso significa que **un oscilador configurado abajo del todo es un modulador**, y
no cuesta ni una pieza: es rango de código del convertidor. Con dieciséis y el
enrutado de §8, dedicar uno o dos a modular a los demás es un preset, no un
respin. Lo que sí hay que hacer es **comprobar en el bring-up hasta dónde baja de
verdad antes de prometerlo**; declararlo como parámetro y qué se excluye con qué
está en orquestación §6.

### 10.7 La imperfección no se elimina: se controla

Este módulo se afina solo, no deriva y sus dieciséis osciladores son iguales por
diseño —referencia única, tabla de 84 notas, autoafinado—. Eso es una virtud
técnica y, dicho sin rodeos, un riesgo musical: lo que hace que un analógico
suene vivo son sus imperfecciones, y aquí están eliminadas por construcción.

La respuesta no es empeorar el circuito. Es que **la imperfección sea un
parámetro**, que es algo que un instrumento con deriva de verdad no puede
ofrecer, porque en él no se elige. Tres, y **ninguna cuesta una pieza en esta
placa** — las tres las genera el cerebro y llegan sumadas al tono (orquestación
§5.2):

| | Qué es | Ámbito |
|---|---|---|
| **Desafinado** | Un desplazamiento fijo por oscilador. Lo que engorda un unísono | `por-voz` |
| **Deriva** | Que cada oscilador vague despacio unos cents, con la amplitud y la velocidad como parámetros | `por-voz` |
| **Carácter de placa** | Un error pequeño y fijo por oscilador, guardado en la memoria de calibración. Hace que **este** instrumento suene distinto de otro igual, y viaja con la placa | `por-voz`, en la calibración |

**Lo que el cobre sí aporta es la resolución**, y por un motivo estructural que ya
está decidido: como los dieciséis cuelgan de **la misma referencia**, el error
común se cancela al restar, así que **desafinar dos osciladores entre sí es más
fino que afinarlos en absoluto**. El suelo absoluto es 0,58 cents
(`dac_local_budget.py`); el paso relativo es 1 LSB = **0,139 cents**.

Traducido a lo que se oye, a 440 Hz:

| Se pide | Se oye |
|---|---|
| 1 paso (0,139 cents) | batido de 0,035 Hz — un ciclo cada 28 s |
| El batido más lento que se nota (~0,1 Hz) | 2,8 pasos |
| Unísono gordo (10 cents) | 72 pasos dentro del efecto |

Y por eso §7.2 importa tanto: **0,087 cents de sesgo entre columnas por dos
cristales distintos es el 63 % de ese paso**, y se lo comería la tabla de
calibración sin decir nada.

## 11. Los canales de convertidor: el censo completo

Es el cuello nuevo y hay que verlo con números. La v2 escribió 54 canales y solo
desglosó 48; **aquí está el censo entero, y sale más alto**. El número anterior
no se puede reproducir porque nunca listó sus partidas, así que se sustituye por
este, que sí las lista y que `dac_channels.py` asevera.

| Bloque | Ámbito | Canales | De dónde sale |
|---|---|---|---|
| Tono | `por-voz` | 16 | v1: `pitch`×4 |
| Mezcla de formas de onda | `por-voz` | 16 | v1: `mezcla`×4 (mezclador interno del SSI2130) |
| Índice de FM/PM | `por-voz` | 16 | §10.2, §10.4 |
| Índice de anillo | `por-voz` | 16 | §10.3 |
| Ancho de pulso | `compartido` | 1 | v1: `PWM`×1 |
| **En uso** | | **65** | |

La referencia de la cuenta es la v1, que llevaba 9 canales en uso para 4
osciladores (`pitch`×4, `PWM`, `mezcla`×4) sobre 3× AD5686R
(`architecture-poly.md` §10). Escalado a dieciséis y con los dos índices nuevos,
son 65.

Con **familia de ocho canales**, dos repartos posibles:

| Reparto | Chips | Canales | En uso | Reserva |
|---|---|---|---|---|
| 2 por placa de voces + 1 más en la maestra | **9** | 72 | 65 | 7 (todos en la maestra) |
| **3 por placa de voces** | **12** | 96 | 65 | 31 (8 por placa) |

**El primero no deja ni un canal de reserva en las tres placas no maestras**, así
que cualquier CV nuevo por oscilador sería un respin. El segundo mantiene la
disciplina de la v1 (25 % de reserva). **Cuál gana lo decide el área de la placa
de voces, no la preferencia**: decisión abierta 4.

Catorce chips de cuatro canales sería la otra respuesta y no es una solución:
**la familia de ocho canales del mismo fabricante deja de ser una alternativa y
pasa a ser lo sensato**, con tres cosas que verificar antes de proponerla en
firme: 16 bits con referencia externa, referencia interna apagable por registro,
y comportamiento de la cadena. Riesgo 3.

Repartido por placa son **16 canales por cada cuatro osciladores** (17 en la
maestra), que es lo que hay que hacer caber en el mismo sitio donde la v1 metía
tres chips.

## 12. La referencia: la carga real y el búfer por placa

La v2 contaba **1,6 mA** y contaba solo el pin `VREF` de los chips. Del mismo
nodo cuelgan dos corrientes más por oscilador:

| Término | Por oscilador | ×16 | Fuente |
|---|---|---|---|
| Pin `VREF` del SSI2130 | 100 µA | 1,60 mA | datasheet |
| Corriente de escala del expo, `VREF`/`R_SCALE` | 94,34 µA | 1,51 mA | §5.1 |
| Corriente lineal, `VREF`/`R_LIN` (499 kΩ) | 5,01 µA | 0,08 mA | `bom.csv` de la v1 |
| **Subtotal** | **199,35 µA** | **3,19 mA** | |
| Entradas de referencia de los conversores | — | **sin cifrar** | §17.3 |

O sea **el doble de lo presupuestado**, y creciendo cuando se cierre la familia
del convertidor.

**La decisión que lo resuelve, y de paso resuelve otra cosa:** un **búfer de
ganancia unidad por placa de voces**. Con él:

- La ADR4525 entrega **nanoamperios**: solo alimenta las cuatro entradas de los
  búferes. Su regulación de carga deja de importar.
- **Por los contactos del conector no circula corriente de referencia**, así que
  la caída de contacto —que era el término que asustaba— desaparece en vez de
  presupuestarse.
- El búfer entrega ~0,80 mA por placa (199,35 µA × 4), más lo que pida su
  convertidor, que es una carga trivial para cualquier operacional.

Los dos requisitos sobre ese búfer, derivados y no elegidos a ojo:

> **Desplazamiento ≤100 µV** (40 ppm de 2,5 V), porque entra 1:1 en la escala del
> jack: 40 ppm × 1200 = **0,05 cents/octava**, que es lo presupuestado en §6.4.
>
> **Deriva del desplazamiento ≤1 µV/°C.** Sobre una excursión de 20 °C son
> 20 µV = 8 ppm, o sea **0,073 cents** de diferencia entre placas entre dos
> pasadas de autoafinado. Por debajo del paso de desafinado de 0,139 cents, que
> es lo que hay que proteger (§10.7).

Eso apunta a un operacional de deriva nula, no a un TL07x. La pieza concreta se
elige en el plan con su datasheet delante; el requisito es este y
`dac_local_budget.py` lo asevera al extenderse.

**La salida conocida si aun así no cumple** —una referencia por columna— sigue
disponible y ahora tiene número: dos ADR4525 a 2 ppm/°C máximo, no
correlacionadas, sobre 20 °C dan 40 ppm de diferencia entre columnas, o sea
**0,36 cents**, que el autoafinado mete en la tabla y del que solo queda la
deriva entre pasadas. Es aceptable, y sigue siendo peor que el búfer porque
duplica una pieza de precisión para no ahorrar ninguna.

## 13. Telemetría, identidad y memoria

El patrón de la v1, ampliado por tres motivos: hay dieciséis osciladores
repartidos en cuatro placas, hay micros que pueden registrar mucho más que antes,
y el módulo tiene que poder **describirse a sí mismo**.

- **Un sensor de temperatura por placa de voces** —cuatro en total—, pegado a su
  racimo de osciladores. Uno solo dejó de representar al conjunto en cuanto se
  repartieron, y con cuatro placas en dos columnas el gradiente térmico dentro
  del módulo es real, no teórico.
- **EEPROM de identidad `24AA02E48` en 0x50, en la placa maestra, sin tocar.**
  Tipo, revisión y serial. Es la pieza que el descubrimiento del núcleo §3.5 ya
  sabe leer, y **no se cambia** para no romper un camino que funciona.
- **Memoria de 32 KB, chip aparte, en el mismo bus I²C, en otra dirección.** Ahí
  viven el blob de calibración y el descriptor del módulo.

Por qué 32 KB y no menos, con la cuenta delante:

| Qué | Bytes | De dónde |
|---|---|---|
| Calibración: 84 notas × 16 osciladores × 16 bits | **2 688** | tabla de afinado |
| Descriptor del módulo: ~300 entradas × ~42 B | **≈12 600** | censo de orquestación §5.1 |
| Etiquetas de los parámetros enumerados | ≈3 000 | los selectores de fuente son enumerados de 17 valores |
| **Total** | **≈18 300** | 57 % de 32 KB |

Ocho KB no habrían alcanzado. Y el techo de hoy es mucho más bajo que eso:
`software/nucleo/core/src/descubrimiento.rs:87` lee el largo del blob como un
`u8` —techo absoluto 255 B— y `FIN_ZONA_LIBRE = 0xFA` (`:34`) lo baja a 238. El
cambio que eso obliga en el núcleo está en orquestación §8, cambio 3.

Por qué en un chip aparte y no sustituyendo al de identidad: el `24AA02E48` trae
un **EUI-48 de fábrica** que es lo que da el serial único, y su dirección I²C es
fija en 0x50 porque sus pines A0/A1/A2 no están conectados (núcleo §3.5,
verificado contra datasheet). Un chip de 32 KB de la misma familia sí tiene pines
de dirección, así que **cuelga del mismo canal del mux I²C en 0x51** y no obliga
a cambiar nada del descubrimiento. Que exista una sola pieza con las dos cosas
sería mejor y sería un chip menos; buscarlo es decisión abierta 5, y si no
existe, dos chips es la respuesta y no cuesta nada.

- **Test points rotulados en serigrafía** — la v1 los dejó sin rótulo y su propia
  lista de mejoras para la rev B lo pedía. Con dieciséis osciladores son muchos
  más, y una tapa de pads anónimos con el multímetro en la mano es un tropiezo
  garantizado.

## 14. La cadena de LED: el módulo la atraviesa, no la gobierna

La cadena tenía dos dueños. El núcleo §5.1 y `architecture-poly.md` §4 la
declaran **un mazo del cerebro que encadena todos los paneles**; la v2 se la
asignaba a los micros del módulo. **Gana el núcleo**, por tres razones:

1. El patcheo guiado necesita **un solo espacio de direcciones** de LED en todo
   el instrumento. Si cada módulo regenera, el cerebro deja de poder encender
   «el jack 7 del módulo 3 y el jack 2 del módulo 5» en el mismo color.
2. El mensaje `POINT` ya es del cerebro (núcleo §4.1) y ya alcanza jacks.
3. Regenerar obliga al micro a reproducir la temporización del WS2812 en tiempo
   real, y ese micro está además cronometrando ocho osciladores con PIO.

**Y no hace falta regenerar**, porque cada WS2812 retransmite el flujo: la cadena
que cruza este módulo se regenera 32 veces por los propios LED.

Lo que el cobre pone:

| Pieza | Dónde | Para qué |
|---|---|---|
| Conector de 3 pines de entrada y de salida | Cada placa de panel | +5 V, dato, `GNDD` |
| Búfer de nivel 3,3 → 5 V | Solo en la entrada del módulo | El dato llega en 3,3 V del cerebro |
| Resistencia de serie en el dato | Entrada | Terminación |
| 16 WS2812 en serie | Cada placa de panel | Uno por jack |
| Puente de 3 hilos entre los dos paneles | Entre placas de panel | Cerrar la cadena dentro del módulo |

Y la regla, escrita para que nadie la rompa: **el módulo nunca escribe en la
cadena.** Ni el maestro ni el esclavo tienen un pin conectado a ella.

Los LED cuelgan del **+5 V del mazo de la cadena y de `GNDD`**, no de los rieles
del módulo. Su brillo, y por tanto su consumo, es el árbitro abierto del #104.

## 15. Verificación

Se heredan los gates de la v1 y se añaden los que las decisiones nuevas exigen.
El runner los descubre por patrón; **ninguno se añade a una lista**. Cada
presupuesto es un guion con aserciones, no prosa.

| Gate | Qué asevera | Estado |
|---|---|---|
| `check_footprints`, `check_netlist`, `check_bom` | Lo de siempre, antes de escribir nada. **`check_netlist` gana una regla nueva**: toda línea de silencio y todo `OE` de registro tiene su pull al estado seguro (§9) | **modificar** |
| `pitch_budget.py` | Con `VOCES` parametrizado y evaluando **por placa de cuatro** además de por módulo. Y con `R_SCALE` = 26 448 Ω y el modelo `I_octava = VREF / (4,717 · R_SCALE)`, que cierra su primer punto de «lo no confirmado» | **modificar** |
| `dac_local_budget.py` | La referencia cruzando conectores **sin corriente**, el búfer local por placa con su desplazamiento ≤100 µV y su deriva ≤1 µV/°C, y que el suelo de afinación de las placas lejanas no empeore más de lo presupuestado | **modificar** |
| `autotune_budget.py` | Se muda al módulo. Asevera además **una sola base de tiempo o su constante de razón medida**, con residuo por debajo de 0,035 cents (§7.2), y el **timeout del barrido** con su peor caso acotado (orquestación §3.2) | **mudar** |
| `depth_budget.py` | El fondo del apilado contra los 50,0 mm del case: **35,8 + 2·*h* ≤ 50,0**, o sea *h* ≤ 7,1 mm. Falla con conectores de 10 mm y lo dice | **nuevo** |
| `cvscale_budget.py` | La escala del jack externo dentro de **3 cents/octava en peor caso lineal**, con los seis términos de §6.4. Falla si alguien mete una resistencia más en ese camino | **nuevo** |
| `dac_channels.py` | Que los **65 canales** en uso caben, con la reserva **declarada por placa**, y que el reparto elegido deja al menos un canal libre en cada placa de voces | **nuevo** |
| `vref_load_budget.py` | Los **3,19 mA** de carga de la referencia con su desglose, más el término de las entradas de referencia del convertidor, contra la corriente que el búfer por placa puede entregar con 3× de margen | **nuevo** |
| `cadena_cv_budget.py` | La impedancia de entrada declarada (≥1 MΩ, constante frente al patch), la amplitud del código de correlación de §6.3 por debajo de 0,09 cents, y el **error de masa entre placa de panel y placa de voces** convertido a cents del CV del jack | **nuevo** |
| `matriz_budget.py` | Los 32 selectores y los 56 bits de control por placa; el ancho del bus de la matriz contra los pines del conector elegido; y la **diafonía de una línea de sync sobre una línea de modulación adyacente**, convertida a cents por el camino de FM | **nuevo** |
| `pines_budget.py` | El reparto de pines de cada micro contra lo que el RP2350B da de verdad: **16 de 24 máquinas de PIO**, 1 de 8 entradas analógicas por micro, GPIO totales, y que la base de tiempo compartida de §7.2 tiene por dónde salir o entrar. **Se escribe antes que ninguna otra cosa del bloque digital** (riesgo 4) | **nuevo** |
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

Estas cifras **no cambian con la corrección de §5.1**, y la razón está dicha
allí: se calcularon suponiendo 20,000 µA/octava exactos, que es lo que el diseño
corregido entrega y lo que la v1 no entregaba.

*(Detalle a arreglar al parametrizar: el rótulo de la tabla dice «placas 4/4 OK»
escrito a mano y no sigue a `VOCES`.)*

## 16. Consumo

Del datasheet: cada SSI2130 pide **+3,75 mA / −2,90 mA** típicos y **100 µA de la
referencia**. Dieciséis chips son **60 mA**, **46 mA** y **1,60 mA** de la
referencia — que con §12 pasan a salir del búfer de cada placa, no de la
ADR4525.

Lo demás **está identificado pero no cifrado**, y va a §17 con lo que hay que
leer para cerrarlo: dieciséis LM311, dieciséis 2N7000, dieciséis paquetes de
operacionales, dos micros, los multiplexores y los registros. Los 32 LED cuelgan
del mazo de la cadena, no de los rieles del módulo (§14), y su árbitro es el
#104.

**El recuento se hace con las placas delante**, no extrapolando de la línea de la
v1. Es el punto 6 del #158 y sale como tarea del plan, no como número de este
spec. Lo que sí se dice ahora es que **los juguetes son la partida nueva más
grande** —dieciséis comparadores y dieciséis paquetes de operacionales— y que la
holgura de la fuente (650 mA por riel, con ~116 mA de estimación para el
instrumento de cuatro voces según `architecture-poly.md` §9) es donde hay que
comprobarlo primero.

## 17. Lo no confirmado

Números y supuestos que hoy no tienen fuente primaria. Cada uno dice qué hay que
leer o medir para cerrarlo. Ninguno bloquea el layout salvo donde se dice.

1. **En qué extremo el CV de mezcla del SSI2130 cierra la salida.** §9 supone que
   es el extremo bajo y pone el pull ahí. Cerrar: la sección del mezclador
   interno en el datasheet. Si es al revés, el pull cambia de riel y no cambia
   nada más. **Antes de rutear las placas de voces.**
2. **El consumo del LM311 y del 2N7000 en esta topología.** Dieciséis de cada uno
   es la partida nueva más grande de §16. Cerrar: datasheet del LM311 y la
   corriente de puerta real del circuito de la figura 18.
3. **La corriente de la entrada de referencia del convertidor de ocho canales.**
   Es el término que falta en §12. Cerrar: el datasheet de la familia que gane la
   decisión abierta 4, y meterlo en `vref_load_budget.py`.
4. **El fondo del jack por detrás del panel: 13,0 mm es supuesto.** Cerrar:
   medirlo con un jack en la mano. Es riesgo 1 y **bloquea la geometría**.
5. **La amplitud y la impedancia de las ondas del SSI2130 en el conmutador de
   carácter del PWM** (§10.5) y en el bus de la matriz analógica (§8). De ahí
   sale si el multiplexor puede ser de 0-5 V o tiene que ser bipolar. Cerrar:
   las especificaciones de salida del datasheet. Es decisión abierta 2.
6. **El desplazamiento del comparador de PWM con la histéresis puesta** (§5.3).
   El valor de la resistencia de realimentación se presupuesta contra la amplitud
   de la triangular, que es el punto 5. Cerrar: con el punto 5, en el plan.
7. **La dispersión chip a chip del convertidor exponencial.** Ningún datasheet la
   garantiza. Es el mismo hueco que `pitch_budget.py` declara. Cerrar: midiendo
   los dieciséis chips reales en el bring-up (riesgo 9).
8. **Resuelto — el error de escala del jack de la v1 son +11,5 cents/octava**, y
   sí es reproducible: son **dos** términos multiplicativos, no uno. `R_SCALE` a
   26,7 kΩ aporta +9,06 y `R_CVIN` a 49,9 kΩ —en vez de los 50 kΩ exactos que el
   datasheet asume para 1 V/octava— aporta +2,40. Una revisión intermedia contó
   solo el primero. `cvscale_budget.py` los calcula desde las fuentes y los
   asevera por separado, para que el reparto de culpas quede a la vista.

## 18. Riesgos y decisiones abiertas

Cada uno con cómo se cierra, que es la puerta de esta fase.

### Riesgos

1. **El fondo del apilado descansa en un supuesto sin medir.** Con conectores de
   5 mm sobran 4,2 mm; con los de 10 no cabe. Cierra: medir cuánto sobresale el
   jack por detrás del panel, elegir la altura del conector, y que
   `depth_budget.py` asevere 35,8 + 2·*h* ≤ 50,0. **Antes de fijar la
   geometría.**
2. **La referencia alimenta dieciséis osciladores.** Son 3,19 mA más las
   entradas de referencia de los conversores, contra los 400 µA de la v1. Cierra:
   `vref_load_budget.py`, más `dac_local_budget.py` extendido con el búfer por
   placa y sus dos requisitos de §12. Si el búfer no cumple, la salida conocida
   es una referencia por columna, con el coste ya cifrado en §12.
3. **Cuántos canales de convertidor y de qué familia.** Sesenta y cinco canales
   en uso. Cierra: `dac_channels.py` con el censo, y verificar la familia de ocho
   canales contra su datasheet —16 bits con referencia externa, referencia
   interna apagable, comportamiento de la cadena— antes de proponerla en firme.
4. **Parcialmente cerrado — los tres números del micro están confirmados contra
   fuente primaria** (`docs/reference/datasheets/rp2350-product-brief-2024-08.pdf`,
   Raspberry Pi Ltd, agosto 2024). Su tabla de variantes da para el **RP2350B**:
   QFN-80, **48 GPIO y 8 entradas analógicas**; y el texto: *«Three
   high-performance Programmable I/O (PIO) co-processors, with a total of
   **twelve** independent state machines, support software-defined interfacing,
   **with little or no CPU overhead**»*. O sea **12 máquinas por micro, 24 entre
   los dos**, de las que 16 van a los osciladores y quedan 8 — con sitio de sobra
   para la cadena de LED de §14, que es lo que el requisito de latencia exige.
   Esa última frase del datasheet es además la garantía literal de que pintar las
   luces no roba procesador.
   **Lo que sigue abierto de este riesgo:** la entrada o salida de reloj por pin
   —de la que depende la base de tiempo única de §7.2—, los pines totales una vez
   repartidos, y el consumo. Cierra: `pines_budget.py`, que se sigue escribiendo
   **antes que ninguna otra cosa del bloque digital**.
   **Anotado para el plan:** el **RP2354B** es el mismo chip con 2 MB de flash
   apilada dentro. Quita el chip de memoria externa de cada micro y su ruteo
   rápido — dos piezas y dos buses menos en placas donde el área es la cota
   (riesgo 5).
5. **El área de la placa de voces.** Pasa de ~15 chips para 4 osciladores en la
   v1 a ~30: cuatro SSI2130, dos o tres conversores, ocho multiplexores, siete
   registros, cuatro LM311, cuatro MOSFET, tres cuádruples de operacional, el
   Schmitt, el búfer de referencia y el sensor. Cierra: el render 2D y el DRC
   sobre el layout heredado. **Es lo que decide la decisión abierta 4**, porque
   la reserva de convertidor se compra con área.
6. **El ancho del bus de la matriz.** 32 líneas de señal más masas entre placas,
   con cuadradas de audio al lado de las ondas que hacen FM. Cierra:
   `matriz_budget.py` con la diafonía convertida a cents, y elegir el conector
   con su recuento de pines. Si no cabe con masa intercalada, la salida conocida
   es partir en dos conectores por unión, que ya está previsto en §8.
7. **La latencia del maestro al esclavo.** El segundo micro recibe sus órdenes
   reenviadas, no directas. Irrelevante para el tono; **no irrelevante para un
   disparo**. Cierra: el presupuesto de temporización de evento de orquestación
   §9, que es la misma pieza que pide el #160.
8. **Dieciséis encapsulados de 4×4 mm soldados a mano, en un proyecto que nunca
   ha fabricado nada.** El SSI2130 es de proveedor único y la fábrica no lo
   monta: probado contra el pedido real, sale «8 shortfall» y el flujo de
   ensamblaje no acepta piezas sin stock. Son ~96 USD solo en osciladores.
   Cierra: comprar dieciséis más repuestos al arrancar, y **montar una columna
   completa antes de poblar la segunda** (decisión 23).
9. **La dispersión chip a chip del conversor exponencial** sigue sin garantizarla
   ningún datasheet, y con dieciséis chips la probabilidad de tocar la cola sube.
   Se hereda de la v1 y se cierra igual: midiendo los chips reales en el
   bring-up, ahora con dieciséis muestras en vez de cuatro — que es, de paso, la
   mejor medida de esa dispersión que va a tener el proyecto.

### Decisiones cerradas por catálogo (2026-08-22)

Cuatro piezas buscadas y verificadas contra páginas de fabricante y
distribuidor. Lo que solo vivía en un PDF quedó marcado y sigue en §17.

1. **El jack: `PJ366ST` (WQP419GR), estéreo, formato Thonkiconn M6.** ~£0,39 en
   cantidades de 50. **No existe estéreo con contacto de conmutación en este
   formato** — Thonk lo dice literal: la versión estéreo *«sustituye el switch
   por el conector de señal del manguito»*. Sí existe en otro formato
   (`WQP-PJ3410`, bush plástico de 8 mm), y se descartó porque cambia el agujero
   de panel de treinta y dos jacks y suma fondo donde no sobra.
   **Consecuencia, y mejora el diseño:** el anillo hace de detector —con cable
   mono queda a masa— y **la cascada la hace el selector**, no el cobre. Cada
   oscilador elige si su tono entra por su jack o por el de arriba, y lo decide
   el cerebro. La cascada pasa de cable fijo a dato guardable en el preset, y el
   cable sigue mandando porque el anillo lo delata.
   **Lo que esto añade y hay que presupuestar:** un selector 2:1 por oscilador en
   el camino del CV de tono, que es señal de precisión. Entra en
   `matriz_budget.py` con el mismo criterio de inyección de carga del punto 2.

2. **El multiplexor: `ADG1206` en el camino analógico, `CD74HC4067` en el de
   sync.** Son dos matrices distintas (§8) y no hay razón para pagar precisión
   analógica en la que solo lleva flancos lógicos.
   El ADG1206 es el único candidato con **inyección de carga publicada: <1 pC**,
   rail-to-rail y rango bipolar. Ese dato es el que importa aquí y no el `Ron`:
   la inyección de carga de un conmutador **es un desplazamiento de continua**, y
   §10.2 ya declara que el desplazamiento de continua es lo que desafina la FM.
   Sus 120 Ω de `Ron` son irrelevantes contra una entrada de alta impedancia.
   Coste: ~$5,29 la unidad contra ~$0,60 del barato — el reparto deja el gasto
   donde compra algo.

3. **La memoria: `24AA256UID-I/SN`** (SOIC-8) o `-I/ST` (TSSOP-8), ~$1,10.
   Son los 32 KB pedidos **y** trae de fábrica EUI-48, EUI-64 y un identificador
   único de 32 bits, con el mismo esquema de direcciones A0-A2 del chip actual.
   **Es un chip, no dos**: cierra a la vez el blob de calibración y el descriptor
   que el módulo tiene que cargar. La ubicación exacta del identificador en el
   array solo está en su PDF y queda en §17.

### Decisiones abiertas

1. **La altura del conector de apilar, y su paso.** Con el dato en la mano, el
   paso de 2,54 mm **no llega**: el Harwin de 40 pines mide 7,50 mm contra los
   7,1 que da §4, y el Samtec no publica su altura en catálogo HTML. **La salida
   verificada es bajar a paso de 2,00 mm.** Cierra: elegir la familia de 2,00 mm
   y meter su altura real en `depth_budget.py`, junto con el fondo del jack
   (riesgo 1), que sigue sin aparecer en ninguna ficha.
2. **Dos o tres conversores por placa de voces** (§11). Cierra con el riesgo 5:
   si el área de la placa aguanta el tercero, entra, porque la reserva por placa
   es lo que evita un respin por cada CV nuevo. Si no, gana el reparto de nueve
   chips y **se declara por escrito que las tres placas no maestras quedan sin
   reserva**.

## 19. Fuera de alcance

- **La orquestación entera** —protocolo, mensajes, arranque, cadencias, modelo de
  parámetros, exclusiones, y los cambios que el núcleo digital necesita— vive en
  [`2026-08-22-vco-orquestacion-design.md`](2026-08-22-vco-orquestacion-design.md).
  Este documento define el cobre que la hace posible, no cómo se comporta en el
  tiempo.
- **El enrutado de audio del instrumento** —matriz en el módulo 4, topología en
  estrella, el audio yendo y volviendo de un módulo central— sigue aplazado a su
  propio ciclo de diseño. Toca `architecture-poly.md` §5 y §6, define el módulo 4
  y condiciona el 5, 6, 7 y 8. **No bloquea este spec**: el VCO produce y no
  consume, así que saca sus salidas por sus jacks vaya donde vaya el cable.
- **Reordenar la cadena** (VCA antes del filtro) — sigue necesitando un cable.
- **El firmware**, del cerebro y de los dos micros. Este módulo define el cobre;
  orquestación define lo que el firmware tiene que cumplir.
- **Ondas crudas al patch bay** — descartado en la v1 y no se reabre sin dato
  nuevo. Con dieciséis osciladores serían 64 jacks.
- **Las perillas** (decisión 21). Aplazadas hasta tener la planta del panel, con
  el sitio ya reservado por la decisión 18.
- **Los módulos 5, 6 y 7.** Se especifican para ocho voces con destino de timbre
  por voz, pero no se dibujan en este ciclo. Ojo con el conteo: dieciséis
  osciladores en pares de FM dan **ocho voces de salida**, así que aguas abajo el
  instrumento sigue siendo de ocho — y cuántas voces declara el instrumento
  depende del preset, que es orquestación §5.5.

## 20. Issues que hay que abrir o actualizar

Este spec **excede el #158**, que pedía duplicar voces. Al escribir el plan:

- **#158** — actualizar con el alcance real: dieciséis osciladores, no ocho;
  exactitud, juguetes, patch bay de treinta y dos, dos micros y seis placas. Y
  **que el módulo trae una revisión del núcleo digital detrás** (orquestación
  §8), que no estaba contabilizada en ninguna parte.
- **#152** (censo de anchos del case) — el ancho real de este módulo son 228,6 mm
  (45 HP), y el censo todavía lista tres VCO fantasma de la arquitectura vieja.
- **Nuevo** — el datasheet del SSI2130 no estaba versionado; queda versionado con
  este spec, y hay que revisar si otros módulos citan fuentes que tampoco están.
- **Nuevo** — la escala del jack de CV externo (§5.1): sesgo sistemático de
  +11,5 cents por octava en la v1, y el objetivo de 3 cents/octava solo
  alcanzable con resistencias al 0,1 % y con el nominal derivado de la razón, no
  copiado del datasheet.
- **Nuevo** — el enrutado del instrumento, para abrir su ciclo (§19).
- **Nuevo** — dieciséis muestras del SSI2130 son la mejor medida de dispersión
  chip a chip que va a tener el proyecto (riesgo 9): que el bring-up la registre
  como dato, no solo como aprobado o suspenso.
- **Nuevo** — el jack con contacto de conmutación independiente (decisión abierta
  1): buscarlo, y si existe, revisar si conviene a los demás módulos con
  normalizado.
