# SAM17 — El esqueleto de aluminio: el acrílico deja de cargar

Fecha: 2026-08-26
Estado: **diseño aprobado en conversación, sin implementar**
Spec que modifica: [`2026-08-15-case-design.md`](2026-08-15-case-design.md) — §2
(Decisiones), §5 (Estructura), §6 (Raíles), §9 (BOM), §10 (Verificación), §11.
Entra como **rev. 21** de esa spec cuando se implemente.

Referencia visual: fotografía aportada por Samuel el 2026-08-26 (display case
con marco perimetral de aluminio, transparentes de relleno, zócalo de madera).
**Manda sobre lenguaje, no sobre cotas** — la misma regla que el board de
intención de 2026-08-16.

---

## 1. Qué cambia, en una frase

El costado de acrílico deja de ser la pieza portante y pasa a ser piel; la
estructura la toman **dos costillas de aluminio fresado** que le recorren el
contorno, y los cuatro largueros 2020 salen del interior para convertirse en
las transversales de ese marco.

Lo dijo Samuel así: «quiero que le quitemos las barras, y en cambio toda la
estructura sea un esqueleto de aluminio».

## 2. Las ocho decisiones

| # | Decisión | Alternativas descartadas y por qué |
|---|---|---|
| 1 | **El costado sobrevive** con su perfil escalonado de acrílico de 8 mm, pero deja de cargar | Que el costado pasara a ser un relleno plano dentro de un marco —lo que literalmente muestra la foto— mataba `costado_2d.dxf`, `guarda_costado()` y la silueta entera |
| 2 | **El marco es un perfil en L**: un ala agarra la cara interior del costado, la otra le tapa el canto | Ranura en U (canto dentro del marco): es **exactamente la geometría que falló en el intento anterior** — ver §3. Pletina plana sin ala: no tapa el canto y, medido, no aguanta (§4) |
| 3 | **Las cuatro barras internas se van** al canto | Dejar `base delantera` dentro era mi recomendación por lo que cuesta (§4.2); Samuel decidió que se fueran las cuatro. **La decisión se sostiene, pero su coste subió el 2026-08-27**: la transversal que iba a heredar su trabajo no cabe — §4.2.1 |
| 4 | **Los Z-Rails atornillan a la costilla**, no al acrílico | Dejarlos en el costado significaba llamar «relleno» a una pieza que sigue sosteniendo paneles, tapas y ejes de giro. Jubilar los Z-Rails y meter la ranura de panel en el marco tiraba 4 rieles comprados (2026-08-18) y sacaba el case del estándar Eurorack de la rev. 4 |
| 5 | ~~Fresado a medida~~ → **CHAPA PLEGADA** (corregido el 2026-08-26, ver §2.1) | Perfil de catálogo: la sección la mandaría el catálogo. Extrusión con matriz propia: no se amortiza en una unidad. **Fresado: se cayó al descubrirse que la L no se podía atornillar** |
| 6 | ~~Costilla plana + tiras de canto~~ → **una sola pieza plegada** (§2.1) | Barras rectas con escuadras: 14 barras y 12 esquinas solo en los laterales. L continuo fresado de bloque: lo más caro con diferencia. **Tiras atornilladas: imposible, ver §2.1** |
| 7 | ~~Bandeja de base en aluminio de 5 mm~~ → **aluminio de 10** (corregido el 2026-08-27, §4.2.1) | Acrílico de 12: pasa, pero resucita una segunda línea de espesor justo después de que la rev. 20 matara la de 5 mm. Los 5 mm salían de un vano biapoyado que ya no existe: sin apoyo delantero el suelo va **en voladizo** y a 5 mm cede 3.509 mm |
| 8 | **Los ejes de giro se quedan escondidos** dentro del Z-Rail | Bisagra vista sobre la costilla —el detalle de la foto— movía el eje fuera del riel, y con él el radio de giro: las 180° de apertura son lo primero que se pierde, y costaron 16 mm de fondo |

### 2.1 CORRECCIÓN del 2026-08-26 — la costilla es chapa plegada

Las decisiones 5 y 6 se cayeron al ir a dibujar los taladros de la tira, y el
motivo es de una línea: **para formar una L, la tira tiene que ser
perpendicular a la costilla, así que el tornillo cruza la junta por el CANTO —
y el agujero de paso de un M3 mide 3.4 mm contra un canto de 3.0.** No quedaba
justo: el agujero era más ancho que la pieza. Roscar tampoco: deja 0.25 mm de
pared por lado, y con 1.5 D de agarre harían falta 4.5 mm de canto.

Se midieron tres salidas. **Costilla más gruesa** (5 mm, para que el M3 rosque
con 1.67 D): cuesta 4 mm más de ancho de case y deja los 78 M3 en pie.
**Tira de chapa plegada** atornillada a la cara: la costilla se queda en 3, pero
la tira vuelve a no ser plana. **La costilla misma plegada**: el ala sale del
propio material y no hay junta.

**Gana la tercera, y no por gusto: hace desaparecer el problema en vez de
pagarlo.** Se lleva por delante `paso_tira`, `paso_junta_L`, los 78 M3 y §8.1
entera. Y devuelve un proceso: la costilla va al taller de CHAPA con el chasis,
no a uno de fresado nuevo.

**Lo que había que verificar, y es lo único que hacía peligroso el plegado:**
las esquinas. Plegar un ala a lo largo de un contorno cerrado necesita corte de
alivio en cada esquina convexa —práctica normal de chapa, se dibuja en el
desarrollo— pero una esquina **cóncava** hace que las dos alas vecinas diverjan
y deje hueco: eso no se pliega. Medido sobre el perfil real:

**Seis convexas y una cóncava** — P3, el fin del valle. Y sale bien, porque el
ala **no va en los siete tramos**: va solo donde hace falta, y eso se deriva de
si el tramo pasa como pletina plana:

| tramo | largo | sin ala | ¿la necesita? |
|---|---|---|---|
| frente bajo | 19.00 | 0.002 | no |
| cara inferior 35° | 155.75 | 1.268 | **sí** |
| **el valle** | 60.00 | **0.072** | **no — y es el cóncavo** |
| cara superior 45° | 155.00 | 1.249 | **sí** |
| meseta de remate | 50.00 | 0.042 | no |
| la trasera | 256.18 | 5.641 | **sí** |
| el suelo | 308.94 | 9.892 | **sí** |

El ala se interrumpe en el valle porque ese tramo no la necesita, así que en la
única esquina cóncava no hay dos alas que diverjan. **Eso es una coincidencia
afortunada del cálculo, no una garantía**, y por eso `guarda_costilla()` lo
exige explícitamente: si el valle se alargara hasta necesitar ala, la puerta
canta aquí y no en el taller de plegado. Probado subiendo `paso_horizontal` a
140.

Su DXF pasa a ser el **desarrollo plano** con los cortes de alivio, no el
contorno — el mismo caso del chasis, cuyo corte no dice de dónde doblar. Hasta
que se dibuje, la pieza **no se exporta**: está declarada en `SIN_DXF` con su
motivo, porque cortar el contorno daría una pieza que al plegarse no llega a la
cota.

## 3. Por qué el perfil en L, y no la ranura

Esta es la decisión que más pesa, y la razón está en la spec del case, §3.

El primer intento del SAM17 (adaptación del diseño de todbot) **falló porque
los dientes no cuadraron**, y la causa raíz fue la tolerancia de espesor del
acrílico. La arquitectura de sándwich que lo sustituyó «no mitiga el problema:
**lo elimina**», y lo elimina por una razón concreta: la geometría crítica pasó
a ser **posiciones de agujero**, que no dependen del espesor de la plancha.

El PLIEGO acepta hoy **±(0.4 + 0.1 × espesor)**, o sea **±1.2 mm en 8 mm**,
confirmado por escrito por Schaeffer AG el 2026-08-18.

Un marco con **ranura en U** tiene ancho fijo y el acrílico no. Eso resucita el
fallo histórico del proyecto. Solo cerraría mecanizando la ranura *después* de
medir el lote, o metiendo una junta elástica que se coma el ±1.2.

El **perfil en L** no tiene ese problema: el ala interior se atornilla a la
cara del costado, así que la cota que manda vuelve a ser posición de agujero.
La tolerancia de espesor solo decide cuánto sobra del ala exterior, y se
absorbe haciéndola más ancha que el peor caso.

**Consecuencia que conviene escribir aparte porque es una ganancia y no se ve
sola:** con el acrílico fuera del camino de carga, **la tolerancia de ±1.2 mm
deja de mover una sola cota funcional**. Hoy `ancho_util` cuelga de `t_cheek`;
después lo fija la costilla de aluminio, que llega con tolerancia de
mecanizado. El **issue #98 baja de bloqueante a cosmético**: el espesor real
sigue importando para que la junta se vea pareja, ya no para que el
instrumento quepa.

## 4. Los números

Todos calculados sobre los parámetros reales del modelo el 2026-08-26, no
estimados. Constantes tomadas de `clearance_budget.py`: `E_ALUMINIO` = 69 000
MPa, `RP02_ALUMINIO` = 130 MPa (Rp0.2 de un 5754 H22), E del PMMA = 3 000 MPa,
`SIGMA_PMMA` = 10 MPa (#106), `carga_mano` = 200 N, `flecha_costado_max` =
0.60 mm.

### 4.1 La costilla: la tira de canto es estructura, no adorno

El contorno del costado mide **1004.87 mm** de perímetro en 7 tramos:

| tramo | largo |
|---|---|
| P[0]→P[1] frente bajo | 19.00 mm |
| P[1]→P[2] cara inferior 35° | 155.75 mm |
| P[2]→P[3] el valle | 60.00 mm |
| P[3]→P[4] cara superior 45° | 155.00 mm |
| P[4]→P[5] meseta de remate | 50.00 mm |
| P[5]→P[6] la trasera | 256.18 mm |
| P[6]→P[0] el suelo | 308.94 mm |

Modo de carga: empujar el case de lado. La costilla flexa **fuera de su
plano**, que es su dirección floja. Viga biempotrada (las esquinas de un marco
continuo son rígidas), 200 N al centro del tramo, sección en L de ala interior
`b` y tira de canto `c`, espesor `t`.

Con `b` = 20 mm (**SUPUESTO DECLARADO**: es lo que mide el 2020 que ya está en
el BOM; no cambia ninguna conclusión de abajo):

| costilla | la trasera (256.18) | el suelo (308.94) |
|---|---|---|
| t = 3, **sin tira** | 5.640 mm · 213.5 MPa | 9.892 mm · **257.4 MPa — fluye** |
| t = 6, **sin tira** | 0.705 mm · 53.4 MPa | 1.237 mm · 64.4 MPa |
| **t = 3, tira de 12** | **0.146 mm** · 39.3 MPa | **0.255 mm** · 47.4 MPa |
| t = 3, tira de 20 | 0.042 mm · 16.8 MPa | 0.074 mm · 20.2 MPa |

**Sin tira de canto no pasa ningún espesor, ni el de 6 mm.** Una pletina plana
de aluminio es floja fuera de su plano, y a 3 mm además fluye. Doblada en L
con un ala de 12, la de 3 pasa con **2.4× de margen** sobre el techo de 0.60 y
trabaja a 47 MPa contra un Rp0.2 de 130.

De aquí sale que **la tira de canto no es un embellecedor que tapa el canto
del acrílico: es el ala que convierte la plancha en viga.** Quien la quite
después «porque es estética» tumba la estructura, y por eso queda escrito
aquí.

Referencia para comparar: el costado de PMMA de hoy da 0.38 mm bajo la misma
carga (`guarda_costado()`).

### 4.2 La bandeja de base

`base delantera` era lo único que sostenía la fila delantera de tornillos de
la bandeja. El README ya lo tenía cerrado: «**No se retira.** Sostiene la fila
delantera de tornillos de la bandeja; sin él la plancha queda en voladizo de
280 mm bajo el chasis.» Medido:

| | vano | flecha con 200 N | tensión |
|---|---|---|---|
| hoy, entre las dos filas de M3 | 202.60 mm | 0.512 mm | 1.80 MPa |
| sin `base delantera`, sin nada nuevo | 271.45 mm en voladizo | **19.717 mm** | 9.63 MPa (fluencia 10) |
| ~~con la transversal del marco en P[0]~~ | ~~280.94 mm biapoyado~~ | ~~1.366 mm~~ | **esa barra NO CABE — §4.2.1** |

La transversal que **aparece sola** en la esquina inferior delantera —arista
P[0], que hoy no tiene barra ninguna— se come el 93 % del problema: de 19.7 mm
a 1.37. Pero no llega al techo de 0.60. Barrido de materiales sobre ese vano
de 280.94 mm:

| bandeja | flecha con 200 N | tensión |
|---|---|---|
| acrílico 8 (hoy) | 1.366 mm | 2.49 MPa |
| acrílico 12 | 0.405 mm | 1.11 MPa |
| **aluminio 5** | **0.243 mm** | 6.38 MPa (Rp0.2 130) |
| aluminio 4 | 0.475 mm | 9.97 MPa |

**Todo este barrido murió el 2026-08-27**: mide un vano biapoyado que necesita
la barra de P[0], y esa barra no cabe. El barrido vivo es el de §4.2.1, sobre
el voladizo.

**SUPUESTO HEREDADO, y hay que decirlo:** los 200 N vienen de `carga_mano`,
que modela a alguien apoyándose. Para el costado y para la tapa del valle eso
es correcto — son superficies que se tocan. Para el **suelo**, que va por
dentro, el modo real es el peso del chasis del PSU y el de la propia plancha
al levantar el case, **y ese peso no está en ningún documento del repo**. Se
usa el conservador que ya existe. Cuando el peso del PSU se mida, este número
se revisa: puede que sobre bandeja.

### 4.2.1 CORRECCIÓN del 2026-08-27 — la transversal de P[0] no cabe

Al escribirla, `solapes()` la cantó contra dos cuerpos. **La esquina inferior
delantera ya está ocupada**, y por algo que costó caro: el riel de panel del
frente bajó ahí a propósito el 2026-08-21 y se llevó 8.46 mm de alto de
aparato para que la bandeja le pasara por debajo. Medido contra su AABB real:

| hueco libre en la arista P[0] | |
|---|---|
| hasta el morro del riel, en X | **10.45 mm** |
| bajo su panza, en Y | 5.29 mm |

Cabe una barra de 10×10 y no cabe nada mayor. Pero una barra de 10×10 cruzando
los 528.62 mm **no es una viga**:

| barra a lo ancho, 100 N (media carga) | flecha |
|---|---|
| 10×10 maciza — la que cabe | **5.352 mm** |
| 20×20 maciza — la que serviría | 0.335 mm, y no cabe |

Y el 2020 del BOM es **hueco**, así que su inercia real es menor todavía que la
de ese macizo. La fila «con la transversal del marco en P[0]» de la tabla de
§4.2 **es falsa**: esa barra no existe.

**Lo que queda, y lo que se decidió.** Sin apoyo delantero el suelo vuela desde
la única línea trasera que sobrevive a §5.1 —hoy `base trasera`, mañana la
transversal de P[6]—, o sea 271.45 mm ahora y 279.45 después. Mismo modelo de
§4.2 (`P L³/3EI`, `b = ancho_util`, 200 N):

| bandeja de aluminio | flecha (271.45) | tensión | masa |
|---|---|---|---|
| 5 — lo que decía §4.2 | 3.509 mm | 24.65 MPa | 2.08 kg |
| 8 | 0.857 mm | 9.63 MPa | 3.33 kg |
| **10** | **0.439 mm** | **6.16 MPa** | **4.16 kg** |
| 12 | 0.254 mm | 4.28 MPa | 4.99 kg |

**Samuel eligió que la bandeja aguante sola** frente a resucitar `base
delantera` en x=88.34, que es donde sí cabe una 2020 y era mi recomendación.
El suelo pasa a **aluminio de 10**, y eso son **+2.7 kg** contra el acrílico de
8 de hoy: el espesor no lo pide la resistencia (6.16 MPa contra 130 de Rp0.2,
factor 21) sino el techo de flecha de 0.60 mm.

Con 10 mm la pieza deja de ser chapa y pasa a ser **plancha**: sale de corte,
no de plegado, y eso cambia la línea del pliego (§8).

### 4.3 El ancho del case crece 6 mm

La holgura entre el Z-Rail y las caras internas de los costados es **0.00 mm
exactos**: el riel de 104 HP mide 528.32 y `ancho_util` mide 528.32.

Como el ala interior de la costilla se mete en ese hueco, el case tiene que
crecer 2× su espesor:

| costilla | `ancho_total` |
|---|---|
| hoy | 544.32 mm |
| 3 mm | **550.32 mm** (+6) |
| 4 mm | 552.32 mm (+8) |

No hay salida elegante: embutir el ala rebajando el acrílico es fresar una
plancha frágil. **Que la costilla pueda ser de 3 mm (§4.1) es lo que deja el
crecimiento en 6 mm y no en 8 o 12.**

## 5. Anatomía

| pieza | papel | material y proceso | cantidad |
|---|---|---|---|
| **Costilla** | La estructura. Todo atornilla aquí | **chapa de aluminio de 3 mm PLEGADA** (§2.1), contorno del costado con el centro vaciado y ala de 12 doblada a 90° en 4 de los 7 tramos | 2 |
| ~~Tira de canto~~ | **Ya no es una pieza** (§2.1): el ala sale del propio material al plegar la costilla. Sigue siendo lo que da la rigidez fuera de plano (§4.1) | — | 0 |
| **Costado** | Piel. No sostiene nada | acrílico 8 mm — el `costado_2d` de hoy, con otra taladrería | 2 |
| **Transversales** | Atan las dos costillas y reciben las filas de M3 de las planchas | aluminio | ver §5.1 |
| **Z-Rails** | Paneles, tapas y ejes de giro | Tiptop 104 HP, los ya comprados, ahora atornillados a la costilla | 4 |
| **Bandeja de base** | El suelo portante, **en voladizo** desde la transversal trasera | aluminio 10 mm (§4.2.1) | 1 |
| **Zócalo** | Se ve y eleva. No carga | madera — ver §9 | 1 |

### 5.1 Cuántas transversales, y el hallazgo que ahorra la mitad del marco

Cruzando los centros de riel contra los vértices del perfil, **los 4 Z-Rails
ya están arrimados a una arista cada uno**:

| arista | qué hay hoy |
|---|---|
| P[0] esquina inferior delantera | **nada** |
| P[1] | riel `cara_inf frente` |
| P[2] | riel `cara_inf valle` |
| P[3] | riel `cara_sup valle` + larguero `valle` |
| P[4] | riel `cara_sup remate` |
| P[5] | larguero `remate trasero`, a 25.46 mm del vértice |
| P[6] | larguero `base trasera`, a 25.46 mm del vértice |

En 4 de las 7 aristas **el Z-Rail ya es la barra transversal**. El case tenía
medio esqueleto perimetral montado sin que estuviera dicho en ningún sitio.

Las transversales propias del marco son por tanto **tres**, y a cada uno de
los cuatro largueros de hoy le pasa una cosa distinta — decirlo en bloque
(«se van al canto») sería impreciso:

| larguero de hoy | qué le pasa |
|---|---|
| ~~`base trasera`~~ | ~~**se muda** a la arista P[6], 25.46 mm hacia atrás~~ — **no se muda: ya está, §5.2** |
| ~~`remate trasero`~~ | ~~**se muda** a la arista P[5], 25.46 mm hacia atrás~~ — **no se muda: ya está, §5.2** |
| ~~`valle`~~ | ~~**desaparece**: la arista P[3] ya tiene el riel `cara_sup valle`~~ — **ese riel no llega a la tapa, §5.2** |
| `base delantera` | **desaparece sin heredero**. Iba a heredarla una transversal nueva en P[0], pero esa arista está ocupada por el riel de panel del frente y solo admite 10×10, que no es viga (§4.2.1). El suelo se salva subiendo a 10 mm, no con una barra |

**SALVEDAD, y sale del propio README:** la cara del Z-Rail es **pared de 1.2
mm**, y esa es la razón por la que la tapa de remate estuvo pegada hasta el
2026-08-21. Un Z-Rail sirve de transversal donde trabaja a tracción entre
costillas, pero no es una viga a la que se le pueda pedir todo. **Eso hay que
acotarlo con una puerta, no suponerlo** (§7).

### 5.2 CORRECCIÓN del 2026-08-27 — de las cuatro barras se va UNA

§5.1 repartía los cuatro largueros en dos mudanzas y dos muertes. Medido contra
el modelo, **tres de las cuatro filas eran falsas**, y las tres por el mismo
motivo: una arista del marco solo admite una transversal si sus dos caras están
libres, y aquí ninguna lo está.

**Las dos traseras no se mudan porque ya están.** La posición tangente a P[6] es
(298.94, 10), o sea una caja de x 288.94..308.94. La `piel_trasera` ocupa
300.94..308.94: la barra entraría **8 mm por detrás del panel trasero**. Lo
mismo en P[5] contra la trasera y contra `remate_sup`. Y donde están hoy:

| larguero | su caja | contra qué está a tope |
|---|---|---|
| `base trasera` | x 280.94..300.94, y 8..28 | cara interior de la trasera (300.94) **y** techo del suelo (8.00) |
| `remate trasero` | x 280.94..300.94, y 228.18..248.18 | la trasera (300.94) **y** el canto bajo de `remate_sup` (248.18) |

Están **tangentes a dos caras cada una, arrinconadas contra la esquina hasta
donde las piezas dejan**. Eso ya es una transversal de marco. Los 25.46 mm que
§5.1 les quería mover son exactamente `t_piel + rail/2 − rail/2`: la pared
trasera tiene espesor, y una barra tangente al plano exterior está fuera de la
caja. Un marco con pared se retira el espesor de la pared; no es una concesión,
es lo que es.

**El del valle no desaparece: nada llega a sustituirlo.** §5.1 decía que P[3] ya
tiene el riel `cara_sup valle`. Medido:

| | x | y |
|---|---|---|
| tapa del valle | 91.94..158.42 | 143.58..146.58 |
| riel `cara_sup valle` | 162.42..186.32 | 137.18..161.08 |
| riel `cara_inf valle` | 80.71..105.94 | 113.64..135.48 |
| larguero `valle` | 115.18..135.18 | 123.58..143.58 |

El riel de arriba empieza **4.00 mm más allá** del canto de la tapa y el de
abajo muere **8.10 mm por debajo** de su plano: ninguno la toca. Y la costilla
tampoco le da repisa — el tramo del valle es **el único de los siete sin ala**,
que es justo la coincidencia afortunada que hace plegable la única esquina
cóncava (§4.1). Sin su larguero la tapa pasa a volar los 528.62 mm entre
costillas y cede decenas de milímetros. Un canto doblado hacia abajo la salvaría
(25 mm de ala dan 0.360 mm) pero no cabe: a x=91.94 se mete dentro del riel
`cara_inf valle`.

**La que sí se va es `base delantera`**, y es la única que de verdad flotaba —
x=88.34, en mitad del suelo, colocada por el chasis del PSU y no por ninguna
cara del case. Es también la única que se ve al abrir.

### 5.3 Y al irse arrastra las Tareas 9 y 10

Quitar `base delantera` pone **roja** a `guarda_costado()`:

| anclas M5 del costado | vano libre | flecha con 200 N |
|---|---|---|
| 4, hoy | 119.0 mm | 0.38 mm |
| 3, sin `base delantera` | **178.9 mm** en (4, 2) | **0.86 mm** contra un techo de 0.60 |
| 3, sin `valle` | 154.6 mm | 0.64 mm |

Pero esa puerta modela el **acrílico como pieza portante**, y deja de serlo en
la Tarea 9. El rojo no dice que el case se hunda: dice que el modelo estaría
midiendo un estado a medias — el larguero fuera y el costado todavía cargando.
**Las Tareas 7, 9 y 10 son un solo paso**: los largueros, la taladrería
estructural del costado y las tres puertas se mueven juntos o no se mueven.

## 6. Lo que NO se hace, y por qué — para que nadie lo reintente

- **Mudar `base trasera` y `remate trasero` a P[5] y P[6]**: entran 8 mm por detrás del panel trasero. Ya están arrinconadas hasta donde la pared deja (§5.2).
- **Quitar el larguero del valle**: ningún riel llega a la tapa (el de arriba se queda 4 mm corto, el de abajo 8.1 mm bajo) y el tramo del valle de la costilla es el único sin ala, así que tampoco hay repisa (§5.2).
- **Transversal en la arista P[0]**: no cabe. El riel de panel del frente deja 10.45 mm y una barra de 10×10 cede 5.35 mm a lo ancho (§4.2.1). Si vuelve a hacer falta apoyo delantero, el sitio es x=88.34 —donde estaba `base delantera`—, no el canto.
- **Ranura en U**: resucita el fallo del postmortem (§3).
- **Costilla sin tira de canto**: no pasa a ningún espesor, y a 3 mm fluye
  (§4.1).
- **Bandeja de acrílico**: solo cierra a partir de 12 mm, y eso resucita una
  segunda línea de espesor tres días después de que la rev. 20 matara la de
  5 mm (§4.2).
- **Bisagra vista**: mueve el eje fuera del riel y con él el radio de giro.
  Las 180° de apertura de las dos filas son lo primero que se pierde, y
  costaron 16 mm de fondo.
- **Jubilar los Z-Rails**: tira 4 rieles comprados y saca al case del estándar
  Eurorack que la rev. 4 eligió a propósito.
- **Embutir el ala rebajando el acrílico** para no crecer 6 mm: es fresar un
  rebaje en una plancha frágil, y el canto rebajado es donde el PMMA rompe.

## 7. Verificación

### 7.1 Puertas que se reescriben

| puerta | qué le pasa |
|---|---|
| `guarda_costado()` | mide el costado de PMMA como placa empotrada en 4 M5 de larguero. No hay largueros y el costado no carga. **Se reescribe apuntando a la costilla**, con el modelo de §4.1 |
| `railes_dentro_del_costado()` | los rieles van a la costilla; cambia la pieza contra la que mide |
| `taladros_con_material()` | el costado pierde sus 8 taladros estructurales; el chequeo se muda a la costilla |
| `guarda_chaflan()` | el chaflán de 0.5 existe porque el canto de PMMA queda a la vista. En el perímetro que la tira tapa, deja de aplicar. Sigue aplicando en remate y trasera |
| `guarda_piso()` | la bandeja cambia de material y de apoyos |
| `alineacion()`, `apoyo()`, `solapes()` | siguen valiendo; cambian de fuente de centros |
| `guarda_apriete()` | **ojo, que la arandela d16 hace DOS trabajos y es fácil contar solo uno.** Uno es no aplastar el acrílico, que fluye a 10 MPa; ese desaparece en la bandeja y en el valle, ya de aluminio. El otro es **subir el par utilizable de 0.33 a 1.15 N·m**, porque por debajo de 1 N·m no hay llave dinamométrica de 1/4" que lo dé — y ese sigue vivo contra aluminio si se quiere seguir apretando a 1.0. La conclusión honesta es que la d16 **no se puede quitar sin decidir antes a qué par se aprieta contra aluminio**, no que sobre |

### 7.2 Puertas nuevas

1. **`guarda_costilla()`** — la sección en L contra `flecha_costado_max` y
   contra `RP02_ALUMINIO`, sobre el tramo más largo. Tiene que **morder por
   los dos lados**: quitar la tira de canto la pone en rojo.
2. **`guarda_riel_cabe()`** — que `ancho_util` ≥ `largo_riel`. **Hoy esa
   holgura es 0.00 mm exactos y no la verifica nadie**: es el patrón que este
   repo persigue, una cota clavada al límite sin puerta que la mire. Con el
   marco metiéndose en ese hueco pasa de deseable a obligatoria.
3. **`guarda_transversal_riel()`** — que a un Z-Rail usado de transversal no
   se le pida más de lo que da su pared de 1.2 mm (§5.1).
4. La puerta de la bandeja, dentro de `guarda_piso()` reescrita, contra el
   vano de §4.2.

### 7.3 Regeneración

Los DXF que cambian: `costado_2d` (pierde taladrería), `bandeja_base_2d`
(cambia de material), y nacen los de costilla y tiras. `lienzo_2d` es la
preview de **acrílico**: la costilla y las tiras **no van en él**, por el
mismo motivo por el que no van las tres piezas de acero ni la tapa del valle.

## 8. El pliego pasa de tres proveedores a cuatro

| material | proceso | piezas |
|---|---|---|
| PMMA colado GS naranja, 8 mm | fresado CNC | costados ×2, tapa de remate, trasera |
| Aluminio | **chapa**: tapa del valle (3 mm) | 1 |
| Aluminio | **plancha, corte**: bandeja de base (10 mm) — ya no es chapa (§4.2.1) | 1 |
| Aluminio | **chapa plegada**: costillas ×2 — al taller del chasis, no a uno nuevo (§2.1) | 2 |
| Acero | corte + plegado | chasis ×3 |
| Madera | ver §9 | zócalo |

### 8.1 La tira de canto es la primera pieza NO PLANA del proyecto

Hasta hoy **todo lo que este repo manda al taller es un DXF plano**: el
acrílico, la chapa de aluminio, y hasta las tres piezas de acero, cuyo DXF es
su desarrollo plano y viaja con un plano de plegado aparte porque «un DXF de
corte no dice de dónde doblar».

La **costilla sigue siendo plana** — contorno más vaciado, un DXF perfecto.
La **tira de canto no**: tiene sección en L, y un DXF 2D no la describe. Y el
modelo no puede rescatarla por el otro lado, porque **OpenSCAD exporta malla
(STL), no sólido**: para pedir mecanizado hace falta un STEP o un plano
cotado, y una triangulación no es ninguna de las dos cosas.

Las dos salidas, y no están decididas:

1. **La tira como perfil de sección constante.** Un DXF de la SECCIÓN más un
   largo y una posición de taladros la describen entera. Es el mismo patrón
   que ya usa el chasis de acero: el DXF dice lo que sabe decir, y un
   documento aparte dice el resto. Encaja con el flujo del repo sin añadir
   formato nuevo.
2. **La L como dos piezas planas atornilladas** — costilla y pletina de canto,
   ambas DXF, unidas en ángulo. Todo el flujo sigue exactamente igual y no
   aparece ninguna pieza rara. **Pero degrada el cálculo de §4.1**, que supone
   sección monolítica: en una L atornillada las dos alas solo trabajan juntas
   si la junta transmite el cortante, y eso depende del paso de tornillos. Con
   paso largo cada ala trabaja sola, que es exactamente la fila «sin tira» de
   §4.1 — la que no pasa a ningún espesor.

### CERRADO y luego SUPERADO el mismo día — la pregunta dejó de existir

> **La sección de abajo ya no manda.** Se cerró eligiendo la L atornillada, y
> horas después esa salida resultó **imposible de fabricar**: el tornillo
> cruzaría la junta por el canto de la costilla, y el agujero de paso de un M3
> mide 3.4 mm contra un canto de 3.0 (§2.1). Al pasar la costilla a chapa
> plegada el ala sale del propio material, así que **no hay junta, no hay paso
> de tornillo y no hay 78 M3**. Se conserva entera porque el hallazgo sigue
> siendo bueno el día que vuelva una junta atornillada a este case: **una junta
> se dimensiona por deslizamiento, no por resistencia**, y a 109 mm de paso
> deja de trabajar como sección sin romperse ni avisar.

### Lo que se decidió (superado por §2.1) — la L atornillada

Calculado con `paso_junta_L()`, con el criterio de corte escrito **antes** de
mirar el resultado: si el paso salía por debajo de 20 mm, la L atornillada se
caía y había que volver al perfil de sección constante.

| criterio | paso máximo |
|---|---|
| resistencia del M3 a cortante | 109 mm |
| **que la junta no deslice** | **34 mm** |

**Manda el segundo, y ahí está toda la trampa.** Quien dimensione por
resistencia pone tornillos cada 109 mm; a ese paso la junta desliza en la
holgura del agujero antes de que el tornillo llegue a trabajar, las dos alas
flexan por separado y la costilla deja de ser una L. El error no da una
costilla un poco peor: da la fila «sin tira» de §4.1, la que no pasa a ningún
espesor y a 3 mm fluye a 257 MPa. **Y no avisa** — una junta que desliza no se
rompe.

Se adopta **`paso_tira` = 30 mm**, por debajo del límite de 34.

**Lo que cuesta, y no estaba contado en ningún sitio:**

| tramo | largo | M3 |
|---|---|---|
| frente bajo | 19.00 | 2 |
| cara inferior 35° | 155.75 | 6 |
| el valle | 60.00 | 3 |
| cara superior 45° | 155.00 | 6 |
| meseta de remate | 50.00 | 2 |
| la trasera | 256.18 | 9 |
| el suelo | 308.94 | 11 |
| | **por costado** | **39** |
| | **los dos** | **78** |

**78 M3 solo para coser las tiras**, contra los 30 de plancha que lista el BOM
hoy: casi triplica la tornillería del case. Encaja con el lenguaje declarado
—§5 de la spec del case dice que «la retícula visible y regular de puntos de
unión es el ornamento permitido»— pero **tiene que entrar en el BOM y en el
tiempo de montaje**, no aparecer como sorpresa el día del ensamblaje.

La palanca que subiría el paso es el par o el `mu`, y `MU_ALU_SECO` = 0.2 está
deliberadamente por debajo del rango de literatura (0.3-0.6). **Eso se cierra
midiendo la junta real, no eligiendo otro número de otra tabla.** Con mu = 0.3
el paso sube a 52 mm y los tornillos bajan a unos 50.

Y con esta salida **la tira deja de ser una pieza no plana**: es una pletina, y
sale en DXF como todo lo demás. Lo que no puede quedar implícito es su
taladrería — **la posición de esos agujeros es lo que hace que la L funcione**,
así que va acotada en el plano y no «a ojo del taller».

Lo que **sale** del pliego de acrílico: el costado pierde «canto visible
completo, diamantado» en el perímetro que la tira tapa — el acabado más caro
y el de más riesgo de rechazo en un traslúcido — y pierde sus 8 taladros
estructurales. El **recocido se queda**: ese es por tensión interna, no por
estética.

## 9. El zócalo de madera — SEPARABLE

Esta sección se puede sacar sin tocar nada de lo anterior. No carga, no
sostiene y no bloquea ninguna cota.

Una plancha de madera bajo el cuerpo, que sobresale de él y sobre la que se
atornillan las cuatro paticas. El case crece en alto lo que mida la tabla.

**El problema real, y no es opcional resolverlo:** la madera maciza se mueve
con la estación, y a lo ancho de 528 mm a contraveta eso son **milímetros, no
décimas**. Atornillada rígida a un marco de aluminio, o se raja la tabla o se
sueltan los tornillos. Las tres salidas conocidas:

1. **Agujeros alargados** en la dirección del movimiento — la solución de
   ebanistería de toda la vida.
2. **Botones de expansión** — más limpio, más pieza.
3. **Un laminado** (contrachapado o listonado chapado), que es estable por
   construcción y hace el problema desaparecer, a cambio de que el canto
   enseñe las capas.

Ni la especie ni el espesor ni la fijación están elegidos. Va como decisión
aparte.

## 10. Lo que NO está confirmado

Convención del repo (Principio I): lo no verificado no se suaviza.

- **El ala interior de 20 mm** es supuesto de este documento, tomado de que es
  lo que mide el 2020 del BOM. No cambia ninguna conclusión de §4.1 —con tira
  todo pasa, sin tira nada pasa— pero la cota definitiva sale de qué le cabe
  al tornillo del Z-Rail y de cuánto puede robarle al vaciado.
- **El modo de carga del suelo** (§4.2): 200 N de mano es un supuesto heredado
  del costado. El modo real es el peso del chasis del PSU, que no está
  itemizado en el repo. Se cierra pesándolo.
- **El racking del cajón (#203)**: sigue abierto y este diseño **no lo cierra
  con número**. Dos costillas en L de aluminio atadas por transversales son
  cualitativamente mucho más rígidas a torsión que dos placas de PMMA atadas
  por cuatro barras, pero eso es una frase, no una medición. Se cierra
  cargando el prototipo, que es justo lo que #203 pide.
- **La aleación del aluminio fresado**: las cuentas van contra Rp0.2 = 130
  MPa, que es un 5754 H22. Un 6082-T6 da ~250 y sobra. Pedir la aleación
  exacta es cosa del pliego.
- ~~**El alabeo de las tiras**~~ — **se cayó solo el 2026-08-26** al cerrar
  §8.1: con la L atornillada la tira es una **pletina plana** cortada de
  plancha, no una barra fresada, así que no tiene el alabeo de un perfil largo.
  Sigue habiendo que exigir planitud de plancha, que es otra cosa y más barata.
- **Especie, espesor y fijación del zócalo** (§9).
- ~~**Cómo se describe la tira de canto**~~ — **la pregunta dejó de existir**
  el 2026-08-26 (§2.1): no hay tira. Con ella se fue `MU_ALU_SECO`, que era el
  supuesto del que colgaban 78 tornillos.
- **Los tres supuestos del plegado de la costilla**: `t_costilla` = 3 de
  aluminio, `radio_doblez_costilla` = 3 (regla r = t, la misma que usa el
  chasis) y el `k_factor` = 0.42 que ya arrastraba el chasis. **El desarrollo
  plano depende de los tres** y los fija el taller de plegado, no nosotros — es
  exactamente el mismo pendiente que el chasis de acero ya tenía, ahora con una
  segunda pieza colgando de él.
- **El desarrollo plano de la costilla no está dibujado**, y hasta que lo esté
  la pieza no se exporta (`SIN_DXF`). Necesita los cortes de alivio de las seis
  esquinas convexas y su plano de plegado, como el chasis.

## 11. Fuera de alcance

- Iluminación de la banda del valle. La foto la lleva; §12 de la spec del case
  ya tiene la WS2812 como fuera de alcance y esto no lo cambia.
- Placa grabada de marca sobre el zócalo. El `kondor_cajeado_2d` ya resuelve
  la marca en la trasera; una segunda es decisión de identidad, no de
  estructura.
- Cerrar el racking (#203).
- El re-dibujo de los paneles de módulo: no los toca nada de aquí.
