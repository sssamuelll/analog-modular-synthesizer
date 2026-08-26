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
| 3 | **Las cuatro barras internas se van** al canto | Dejar `base delantera` dentro era mi recomendación por lo que cuesta (§4.2); Samuel decidió que se fueran las cuatro |
| 4 | **Los Z-Rails atornillan a la costilla**, no al acrílico | Dejarlos en el costado significaba llamar «relleno» a una pieza que sigue sosteniendo paneles, tapas y ejes de giro. Jubilar los Z-Rails y meter la ranura de panel en el marco tiraba 4 rieles comprados (2026-08-18) y sacaba el case del estándar Eurorack de la rev. 4 |
| 5 | **Fresado a medida** | Perfil de catálogo: la sección la mandaría el catálogo. Extrusión con matriz propia: no se amortiza en una unidad |
| 6 | **Costilla plana fresada + tiras de canto** | Barras rectas con escuadras: 14 barras y 12 esquinas solo en los laterales, y cada junta acumula tolerancia. L continuo fresado de bloque: lo más limpio y lo más caro con diferencia |
| 7 | **Bandeja de base en aluminio de 5 mm** | Acrílico de 12: pasa, pero resucita una segunda línea de espesor justo después de que la rev. 20 matara la de 5 mm. Aluminio de 4: pasa con 1.26× en vez de 2.5× |
| 8 | **Los ejes de giro se quedan escondidos** dentro del Z-Rail | Bisagra vista sobre la costilla —el detalle de la foto— movía el eje fuera del riel, y con él el radio de giro: las 180° de apertura son lo primero que se pierde, y costaron 16 mm de fondo |

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
| con la transversal del marco en P[0] | 280.94 mm biapoyado | 1.366 mm | 2.49 MPa |

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

**SUPUESTO HEREDADO, y hay que decirlo:** los 200 N vienen de `carga_mano`,
que modela a alguien apoyándose. Para el costado y para la tapa del valle eso
es correcto — son superficies que se tocan. Para el **suelo**, que va por
dentro, el modo real es el peso del chasis del PSU y el de la propia plancha
al levantar el case, **y ese peso no está en ningún documento del repo**. Se
usa el conservador que ya existe. Cuando el peso del PSU se mida, este número
se revisa: puede que sobre bandeja.

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
| **Costilla** | La estructura. Todo atornilla aquí | aluminio fresado de plancha, contorno del costado con el centro vaciado, cabe en 308.94 × 256.18 | 2 |
| **Tira de canto** | El ala en L. Tapa el canto del acrílico **y da la rigidez fuera de plano** (§4.1) | aluminio fresado, barra recta por tramo | 7 por costado |
| **Costado** | Piel. No sostiene nada | acrílico 8 mm — el `costado_2d` de hoy, con otra taladrería | 2 |
| **Transversales** | Atan las dos costillas y reciben las filas de M3 de las planchas | aluminio | ver §5.1 |
| **Z-Rails** | Paneles, tapas y ejes de giro | Tiptop 104 HP, los ya comprados, ahora atornillados a la costilla | 4 |
| **Bandeja de base** | El suelo portante | aluminio 5 mm (§4.2) | 1 |
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
| `base trasera` | **se muda** a la arista P[6], 25.46 mm hacia atrás |
| `remate trasero` | **se muda** a la arista P[5], 25.46 mm hacia atrás |
| `valle` | **desaparece**: la arista P[3] ya tiene el riel `cara_sup valle` |
| `base delantera` | **desaparece**, y su trabajo lo hereda una transversal NUEVA en P[0] — que no es la misma barra en otro sitio, sino otra barra en una arista que hoy está vacía. Es la que salva la bandeja (§4.2) |

**SALVEDAD, y sale del propio README:** la cara del Z-Rail es **pared de 1.2
mm**, y esa es la razón por la que la tapa de remate estuvo pegada hasta el
2026-08-21. Un Z-Rail sirve de transversal donde trabaja a tracción entre
costillas, pero no es una viga a la que se le pueda pedir todo. **Eso hay que
acotarlo con una puerta, no suponerlo** (§7).

## 6. Lo que NO se hace, y por qué — para que nadie lo reintente

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
| Aluminio | **chapa**: bandeja de base (5 mm), tapa del valle (3 mm) | 2 |
| Aluminio | **fresado**: costillas ×2, tiras de canto | ver §5 |
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

**No se elige aquí**: la salida 2 solo es admisible si se calcula el paso de
tornillo que hace falta para que la junta transmita el cortante, y ese cálculo
es del plan de implementación, no de esta spec. Lo que sí queda decidido es
que **la costilla y la tira no se pueden describir con el mismo tipo de
entregable**, y que el modelo actual no produce el de la tira.

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
- **El alabeo de las tiras de canto**: la costilla plana no se tuerce, pero
  las tiras son barras. La más larga mide 308.94 mm. Hay que exigir rectitud
  por escrito o medirla al recibir.
- **Especie, espesor y fijación del zócalo** (§9).
- **Cómo se describe la tira de canto para el taller** (§8.1), y si la L es
  maciza o atornillada. De esto depende que el cálculo de §4.1 siga valiendo
  tal como está escrito.

## 11. Fuera de alcance

- Iluminación de la banda del valle. La foto la lleva; §12 de la spec del case
  ya tiene la WS2812 como fuera de alcance y esto no lo cambia.
- Placa grabada de marca sobre el zócalo. El `kondor_cajeado_2d` ya resuelve
  la marca en la trasera; una segunda es decisión de identidad, no de
  estructura.
- Cerrar el racking (#203).
- El re-dibujo de los paneles de módulo: no los toca nada de aquí.
