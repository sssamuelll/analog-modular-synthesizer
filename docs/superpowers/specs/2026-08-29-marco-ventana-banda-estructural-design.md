# SAM17 — El marco de la ventana y la banda estructural: cinco piezas a cuatro

**Fecha:** 2026-08-29 (noche) · **Estado:** aprobado por Samuel en conversación
(«dale vamos con furia»), con dos supuestos que él dejó abiertos y aquí se cierran
(§1); **implementado** en la rama `feat/case-marco-ventana` con sus puertas — y
corregido contra lo que las puertas obligaron (§4.2: la brida no sube; §3.2: la
pata trasera se retira 11.2; §5: los tornillos del chasis) ·
**Enmienda:** [`2026-08-15-case-design.md`](2026-08-15-case-design.md) (rev. 25),
[`2026-08-28-costilla-pletina-design.md`](2026-08-28-costilla-pletina-design.md) §4, §5
y §10, [`2026-08-27-case-esqueleto-visible-design.md`](2026-08-27-case-esqueleto-visible-design.md)
§4.2 (los miembros) y [`2026-08-29-nariz-recta-valle-limpio-design.md`](2026-08-29-nariz-recta-valle-limpio-design.md)
§2.3 (la meseta). **No toca** la silueta salvo la esquina de abajo-atrás, los
ángulos, las tres filas, los rieles, la tabla ni la nariz.

## 1. De dónde sale

Samuel, mirando el `.blend` con cada pieza nombrada, puso cinco piezas en cuestión
«por un solo objetivo: simplificar el diseño, al mejor estilo japonés»:
`clips_costado`, `escuadras_trasera`, `marcos_trasera`, `miembro_alto` y
`miembro_bajo`. No que sobren por decreto: que si el diseño puede ser más sencillo
y más eficiente **sin comprometer el acabado, por fuera y por dentro**, lo sea.
«Calidad 100 % japo-alemana.»

La vara que se aplicó, y que este papel usa en cada decisión: **una pieza se queda
solo si hace un trabajo que ninguna vecina puede hacer**. Con ella se leyeron las
cinco en el `.scad` y en sus puertas antes de opinar:

| pieza | qué hace hoy | veredicto |
|---|---|---|
| `clips_costado` ×4 | tope hacia dentro del costado en el tramo del suelo — el único de los siete tramos sin placa de anclaje | **sobra**: lo hace el marco de la ventana (§3) |
| `escuadras_trasera` ×2 | el mismo tope en el canto trasero, atornillada a la trasera porque en la franja trasera del anillo no cabe una rosca | **sobra**: lo hace la pata trasera del marco (§3) |
| `marcos_trasera` ×2 | dos bandas para que el PMMA no asome al plano trasero (#234) — un embellecedor atornillado encima de la estructura | **sobra**: la banda ES el alma del miembro (§4) |
| `miembro_alto` ×1 | ata los anillos arriba-atrás, recibe la trasera y ES la meseta | **se queda, simplificado**: pierde el retorno de 24 y gana la banda vista (§4) |
| `miembro_bajo` ×1 | ata los anillos abajo-atrás, recibe la trasera y cuelga el chasis del PSU | **se queda como `talon`**: un ángulo sobre la tabla, sin bridas; el chasis pasa a la tabla (§4, §5) |

Y con ellas caen las seis **placas de anclaje**, que nadie puso en cuestión: no
porque sobren sino porque son el 60 % del marco de la ventana y se funden en él.

Dos supuestos que Samuel dejó abiertos y aquí se deciden, con su motivo:

1. **La banda es estructura** (y no un embellecedor aparte): la trasera va DENTRO
   del canal y sale por abajo, no por atrás. Es el precio de que el techo sea una
   chapa del pico al canto sin costura y de que la tolerancia del PMMA deje de
   mover una cota vista (§4.3). Si un día se quiere la trasera desmontable por
   atrás, el marco vuelve como pieza aparte y sobra menos.
2. **El miembro bajo no necesita bridas**: se atornilla a la tabla por su pie,
   como la nariz. Así no depende de #203 (el racking) para irse: el diafragma
   trasero queda atado abajo a la tabla, que es más rígida que el canal que
   sustituye (§4.4).

Lo que NO se hace, por el propio papel de Samuel: **cinta VHB en el rebaje** en
vez de topes (cero piezas) — la spec del case dice «sin adhesivo en ninguna junta»
y el README «todo el case se desmonta». Se respeta y no se discute.

## 2. La cuenta, antes que nada

| | hoy | mañana |
|---|---|---|
| piezas (las cinco + las placas) | 16 | **4** (`marco_ventana` ×2, `miembro_alto`, `talon`) |
| DXF de corte de esas piezas | 9 | **3** |
| tornillos del case | 73 (53 del eco + 20 de placa sin itemizar) | **68** |
| cabezas vistas atrás | 16 (10 sobre metal + 6 sobre PMMA) | **10, todas sobre metal** |
| taladros en la trasera | 16 | **10** + 2 muescas de esquina |
| roscas ciegas por anillo (cara interior) | 16 | **14** (10 en las filas, 2 en la pata del suelo, 2 de brida) |
| costuras en el techo | 1 (a 9.5 del canto) | **0** |
| bridas de miembro | 4 (8 M4) | 2 (4 M4) |
| masa | — | **+0.28 kg** (cada marco pesa 320 g — 19 764 mm² de DXF a 6 mm y 2.70 g/cm³ — contra 182 g de placas + clips + escuadra por lado) |

Todo lo que no está en esta tabla — rieles, nariz, tabla, paticas, tapa del valle,
costados — no cambia de pieza. El chasis cambia de fijación (§5).

## 3. El marco de la ventana: `marco_ventana` ×2

### 3.1 Qué es

Samuel dijo el 28-08, mirando el render, que **«la placa es el marco de la fila»**
(`params.scad`, `placa_fondo`). Esta spec lo lleva hasta el final: **las tres
placas, los dos clips y la escuadra de cada costado pasan a ser UNA pletina de 6
mm cortada a láser con el contorno de la ventana del anillo**, corrida por los
siete tramos, 26 mm hacia dentro desde la silueta (`marco_fondo`, la misma cota
que `placa_fondo`). Se atornilla en las **mismas diez roscas ciegas** que hoy usan
las placas, lleva los **seis cajeados** de los rieles (cuatro 3U + dos 1U, Ø8 ×
2.5 por el lado del anillo, como hoy), la rosca M3 de la pestaña de la banda del
valle y, en la pata del suelo, **dos pasos M4 más** para sus dos roscas ciegas
al anillo — el trabajo que hacían las de los clips (§3.2). **Nada más**: las
bridas del miembro alto no lo atraviesan (§4.2, la muesca).

Lo que compra, y es lo que se pidió:

- **El tope del acrílico es continuo.** Hoy es «placas aquí, clips allá, escuadra
  atrás y nada en el frente ni en la meseta»; mañana el marco pisa 6 mm de
  acrílico volado por todo el perímetro de la ventana. A través del PMMA
  traslúcido se ve **una sombra uniforme de 6** alrededor de la ventana, en vez de
  retazos.
- **Un solo DXF** (`marco_ventana_2d`) en vez de `placa_cara_inf_2d`,
  `placa_valle_2d`, `placa_cara_sup_2d`, `clip_2d` y `escuadra_trasera_2d`. El
  lado espejado comparte contorno, como las placas: se cortan dos, se cajean uno
  por cada cara (PLIEGO).
- **Mueren** los cuatro clips y sus dos roscas ciegas por anillo, las dos escuadras
  y sus seis M3 sobre el acrílico, `TRAMOS_CLIP`, `placa_chaflan` (el chaflán de
  la placa de arriba existía para librar la brida, y el marco pasa por debajo de
  ella entera) y el reparto de rincón entre placas vecinas (`reparto_rincon`: ya no
  hay vecinas).

### 3.2 La geometría, tramo por tramo

El canto exterior del marco NO va a la silueta en todos los tramos, y la razón es
lo que hay encima de cada uno:

| tramo | canto exterior del marco | por qué |
|---|---|---|
| cara de abajo, valle, cara de arriba (las tres filas) | **a la silueta**, con los mismos retiros de hoy (`retiro_placa_inf` = 9 desde P1, `retiro_placa_sup` = 12 desde P3, tangentes de los radios) | es el marco de la fila que Samuel aprobó: el canto de 6 se lee como el borde de aluminio de la fila |
| frente (el chaflán y los 13 verticales), suelo, meseta y los 10 mm de la cara de arriba bajo el retorno | **retirado `retiro_marco` = `t_costilla` + `hol_piel` = 1.65** | encima va chapa de 1.5 a ras de la silueta (nariz, pie de la nariz y del talón, meseta, retorno) y el marco pasa por debajo con 0.15 de aire; desde fuera no se ve |
| trasera | canto exterior en **x = 296.21**: retirado `t_piel` + `t_costilla` + tol + 0.5 = **11.20** del plano trasero | la trasera y la banda ocupan los 9.5 mm exteriores de la franja, y delante de un PMMA de ±1.2 no puede haber nada fijo (§4.3): la pata queda de 14.8 de ancho, apoya 2.8 en la franja y pisa 11.5 mm de acrílico |

El canto **interior** va a `marco_fondo` = 26 de las **aristas** del perfil en los
siete tramos — recto, no el offset de la silueta redondeada: en P3, el rincón
cóncavo de radio 54, ese offset subía en arco y dejaba el paso del segundo riel 1U
a 6.26 del canto (`check_dxf` lo cazó). Sobre las filas es exactamente la placa de
hoy (mismo cajeado, mismas roscas, mismo canto visto); en el frente, el suelo, la
meseta y la trasera es el tope que hoy dan los clips (24) y la escuadra (25.5),
unificado. Y las roscas de cada riel se arriman a él sin salirse de su pata: las
de la cara de arriba no caben en los primeros 12 tras P3 (`retiro_placa_sup`
vuelve, con la misma cota y por la misma razón que tenía la placa: ahí el
redondeo cóncavo estrecha la franja y la broca sale por el rebaje, 4.72 contra
4.95).

**Las transiciones son escalones de 1.65 en el canto exterior**, y caen donde ya
hay una pieza que los tapa: en la cara de abajo a `retiro_placa_inf` = 9 de P1,
justo donde muere la nariz (`nariz_s_top` = s0 − `hol_piel`); en la cara de
arriba a 5 del pico (`retorno_meseta` + 1), bajo el retorno de la meseta.

**Cada tramo aguanta el empujón del acrílico con lo que tiene**, y la puerta lo
mide tramo a tramo (`guarda_marco_ventana()`): `carga_mano` = 200 N al centro,
flexión en z, menos de 2 mm — el acrílico necesita 3 para salirse del rebaje —
y por debajo de RP02.

- **La pata del suelo lleva dos roscas**, a `rosca_suelo_retiro` = 60 de cada
  extremo. No estaban en la primera versión de este papel y el revisor del PR
  las hizo aparecer: es la pata más larga del marco (288.6 × 24.35) y sin
  tornillo cedía **3.31 mm** — era el tramo que sustituyó a los clips, y los
  clips llevaban tornillo. Con las dos, su vano mayor es 168.6 y cede 0.16.
  Caen en x = 67.6 y 236.2, lejos de los tres M5 con que la tabla entra por el
  canto inferior del anillo (44.6, 153.7, 262.8) — la puerta también lo mide,
  porque un DXF de la cara no ve un taladro que entra por el canto.
- **La pata trasera no lleva tornillo** — en la franja trasera no cabe uno,
  como sabía la escuadra — y no le hace falta: es una viga de 14.8 × 6 de
  **235.18** mm, **empotrada abajo** en la esquina de P6, porque la rosca del
  suelo está a 71 por el contorno (`EMPOTRE_MAX` = 100: el momento entra en la
  vecina como torsión de un tramo corto de pletina y no gira), y **apoyada
  arriba**, donde la muesca de la brida (§4.2) deja un cuello de 9.5 que
  sostiene pero no empotra. Cede **1.32 mm** y trabaja a 99 MPa; apoyada en
  las dos puntas cedería 2.95, y eso es lo que las roscas del suelo compran.
- Las tres filas, por su vano mayor entre dos roscas (≤ 108), ceden ≤ 0.05;
  el chaflán, el frente y la meseta son cortos.

### 3.3 Montaje

Es el mismo orden de hoy, con una pieza en vez de seis: **primero los seis rieles
al marco** (la cabeza queda en el cajeado, del lado que después mira al anillo),
**después el marco al anillo desde dentro** con sus doce M4 — con el costado YA
asentado en el rebaje, porque el marco lo pisa. El README traía los costados
DESPUÉS de las placas y los clips, y eso no se puede montar (§9); aquí se corrige.

## 4. La banda es el miembro

### 4.1 Por qué existe el marco de la trasera, y por qué deja de hacer falta

El marco (#234, ayer) existe porque la meseta muere 9.5 mm antes del canto trasero
y la trasera va POR FUERA del alma del miembro: para que el PMMA no asome al plano
trasero hubo que ponerle una banda encima. Si **la meseta corre hasta el plano
trasero y dobla 20 hacia abajo, esa banda es el alma del miembro alto**: el marco
de arriba desaparece, y con él la costura que hoy cruza el techo a 9.5 del canto.
El techo pasa a ser **una chapa del pico al canto**, con el radio de 4.5 en la
esquina P5 que la regla de ayer ya le había puesto al anillo (`radio_chapa`).

Abajo lo mismo: el miembro bajo se queda como un ángulo — la banda en el plano
trasero y un pie sobre la tabla — y se llama **`talon`**, porque hace atrás lo que
la `nariz` hace delante.

### 4.2 Las dos piezas

**`miembro_alto`** (una L con pestañas): del pico al canto trasero y hacia abajo.

| tramo | cota | nota |
|---|---|---|
| retorno | `retorno_meseta` = 4, a 45° (90 − `angulo_superior`) | como ayer; lo manda el barrido del panel (`guarda_retorno_meseta`) |
| meseta | `prof_sup` = **50** (= `marco_remate`), del pico al plano trasero | era 40.5 y moría en el doblez del alma; sube al canto. `guarda_remate()` pasa a exigir `prof_sup == marco_remate`: dos sumandos mueren |
| banda | `banda_trasera` = **24**, hacia abajo a ras del plano trasero | ver §4.5 por qué 24 y no 20 |
| pestañas (2) | `brida_largo` = **27** desde la cara interior de la banda, hacia delante sobre la franja de la meseta, `brida_ancho` = **14.5** de alto desde `t_costilla` bajo la meseta, **en la cara del anillo** (z = `t_anillo`) | los dos M4 a 9.75 y 20.25 del doblez (regla de chapa y 1.5 D del canto libre), a `dist_rosca_ciega` = 8.5 de la silueta: x = **296.16 y 285.66**, y = 247.68, a rosca ciega en el anillo. **No atraviesan el marco**: en la franja de la meseta el marco lleva una **muesca** abierta a su canto exterior sobre la huella de la brida (16.5 de honda, hasta la punta de la brida menos `hol_piel`), y la brida se tumba en la cara del anillo como siempre |
| ranuras de aire | las 16 de ayer, centradas en la meseta plana | `guarda_aire` sigue leyéndolas del DXF |
| fila de M3 de la trasera | 5 a paso 100, a **12** del canto libre de la banda (y = 244.18) | 12 ≥ 9.2 de la regla de chapa contra el doblez de arriba, 12 ≥ 5.1 contra el canto libre |

La pestaña ya no dobla del alma (que no existe) sino **del extremo de la banda**,
y sigue doblando sobre una línea PERPENDICULAR a la silueta — es lo que hace legal
su agujero (la nota de `brida_largo` en `params.scad` vale entera). Acaba
`t_costilla` por debajo de la meseta, como hoy.

**Lo que se probó y NO vale, para que nadie lo reintente:** subir la pestaña
`t_placa` con un escalón y tumbarla ENCIMA del marco. `guarda_tapa()` lo cantó
en la primera corrida: todo lo que vive a z ≥ `t_anillo` + `t_placa` está en el
barrido del panel de arriba, y la tapa pasaba de abrir 121.5° a **52°**. La
pestaña tiene que quedarse en la cara del anillo, fuera de esa rebanada, y por
eso es el marco el que se aparta con la muesca. Tampoco vale meterla por DEBAJO
del marco con un cajeado y dos agujeros Ø8: dejaba la esquina trasera-alta del
marco con 2.5 mm de pared. Y `brida_ancho` baja de 16 a 14.5 para que bajo la
muesca queden 9.5 de pata entera (`guarda_marco_ventana()` exige 8).

**`talon`** (una L sin pestañas): la banda en el plano trasero y el pie sobre la
tabla.

| tramo | cota | nota |
|---|---|---|
| banda | `banda_trasera` = 24, de y = 0 al canto libre | el doblez de abajo va en la esquina P6, que pasa de radio 0 a `radio_chapa` = 4.5 por la misma regla que las otras cuatro esquinas con chapa encima |
| pie | `talon_pie` = 22 hacia delante, sobre la tabla | la trasera se asienta encima (1.5 sobre la tabla); tres M4 desde dentro a 1.5 D del canto libre (x = 292.66), a z = ¼, ½ y ¾ del hueco entre anillos, mismo herraje que las paticas y la nariz (`d_pie_tornillo`) |
| fila de M3 de la trasera | 5 a paso 100, a **12** de la tabla | 12 ≥ 9.2 contra el doblez de abajo |

No lleva bridas ni rosca en el anillo: **su fijación es la tabla**, que ya está
atada a los dos anillos con seis M5 en 18 mm de madera maciza. Su sección no carga
nada en vertical — está apoyada en la tabla en toda su longitud — y en horizontal
(el empujón por detrás) la tiene la trasera, atornillada a él cada 100.

**`piel_trasera`** cambia sin cambiar de material: sigue siendo la plancha de 8 con
el relieve KONDOR, las ondas, la rejilla y la ventana de red. Ahora va **dentro**
de las dos bandas: su cara trasera contra la cara interior de las bandas (rehundida
`t_costilla` como ayer), su canto de arriba bajo la meseta con `hol_piel` de aire,
su canto de abajo sobre el pie del talón. Mide **540.32 × 253.03** (era 254.68).
Sus dos filas de M3 pasan a y = 12 y 244.18 (eran 10 y 243.18); las ondas y la
rejilla, que se derivan de ellas, se mueven con ellas. **Pierde los seis M3 de las
escuadras** y gana **dos muescas de esquina arriba**, de 2 (z) × 15 (y) con radio
2 en el rincón — por donde le pasa por debajo la pestaña del miembro alto,
escondidas detrás de la banda. Y su 2D se dibuja en y del mundo (arranca en 1.5,
no en 0) para que ondas, rejilla, ventana de red y KONDOR no se muevan.

### 4.3 La regla que el marco de ayer rompía: nada a distancia fija delante del acrílico

Schaeffer manda el PMMA de 8 a **±1.2**. El marco de ayer pinza la trasera entre
dos chapas a 8.00 justos — la banda por fuera, el alma por dentro —: con una
plancha de 9.2 la banda asoma 1.2 del plano trasero, y con una de 6.8 el M3 la
hunde 1.2 y el ala B se despega de la meseta. Es **la ranura de ancho fijo que el
postmortem del case prohíbe** (spec 26-08 §3: «un marco con ranura en U tiene
ancho fijo y el acrílico no»), y la puerta de ayer no la miraba porque medía
nominales.

Con la banda estructural la trasera se atornilla a la banda y **delante de ella no
hay nada a distancia fija**: la tolerancia se va hacia dentro, exactamente como en
el costado (spec 28-08 §4: «la tolerancia del espesor la absorbe la profundidad
del rebaje»). Lo vigila una puerta nueva, `guarda_trasera_dentro()` (§7): ningún
cuerpo fijo en la franja de `tol` + 0.5 delante de la cara interior de la trasera,
salvo sus propias tuercas.

### 4.4 Lo que aguanta cada una, con número

**El miembro alto solo** — sin la trasera puesta — con 200 N en el centro de la
meseta (`carga_mano`, el mismo que carga la trasera, el costado y la banda del
valle), viga biapoyada de 540.62:

| banda | I (mm⁴) | flecha | tensión en el canto libre | contra 130 MPa |
|---|---|---|---|---|
| 20 | 2 848 | 3.35 | 158 | **no pasa** (pasa contra los 240 del 6082-T6 de chapa, EN 485-2) |
| 22 | 3 753 | 2.54 | 131 | al límite |
| **24** | **4 821** | **1.98** | **110** | **pasa** |
| 26 | 6 061 | 1.57 | 94 | pasa (es la flecha del canal de hoy, 1.63) |
| canal de hoy 20 × 24 | 5 844 | 1.63 | — | — |

**Con la trasera atornillada** cada 100 la cuenta cambia de pieza: en ese sentido
la trasera es una viga de canto de 253 × 8 con EI **165 veces** la de la L, y el
M3 que la une trabaja a 1.7 MPa de aplastamiento. La meseta no baja de una
décima. No es «el acrílico carga»: es el mismo principio del sándwich —
posiciones de agujero, no espesores — y el miembro se sostiene solo aunque la
trasera no esté.

**Horizontal** (el empujón de 200 N en la trasera): la L tiene 28 227 mm⁴ contra
los 5 838 del canal de hoy, porque la meseta de 50 es su ala en ese sentido.
Mejor que hoy por cinco.

**El canto del pico bajo una mano puntual**: no cambia. El voladizo de la meseta
sigue siendo 40.5 porque **la meseta apoya en el canto de arriba de la trasera** a
0.15 mm (x = 297.91), no en la banda a 50. Hoy tampoco tiene puerta; se declara en
§9.

**La tapa de arriba abre 180°.** Con el canal fuera no queda nada en su barrido:
`guarda_tapa()` pasa de 121.5° (topaba con el retorno de 24 del canal) a 180° sin
topar. La de abajo sigue en 63.8°.

**El racking (#203)**: el diafragma trasero — la trasera atornillada arriba al
miembro alto y abajo al talón — queda atado arriba a los anillos por las pestañas
(como hoy) y abajo a la **tabla** por los tres M4 del talón. La tabla va a los
anillos con seis M5 en cortante. Es un camino más rígido que las dos pestañas de
1.5 mm con dos M4 que tenía el miembro bajo, no menos; #203 sigue abierto porque
nunca tuvo número, no porque este cambio lo abra más.

### 4.5 Por qué 24 y no 20

La banda de ayer medía 20 y ese piso lo ponía su fila de M3 (1.5 D a los dos
cantos). Hoy el piso lo pone la flexión de la L sola: con 20 trabaja a 158 MPa,
por encima del Rp0.2 de 130 con el que calculan todas las puertas del case. Se
podía dejar en 20 obligando la aleación (6082-T6, 240 MPa) — y el papel lo
apunta —, pero la regla del repo es «aleación recomendada, no obligatoria» y una
banda de 24 la cumple sin excepciones. **Se ve** (4 mm más de metal arriba y
abajo, 205 mm de acrílico entre bandas en vez de 213): es un parámetro y se juzga
en render.

### 4.6 Servicio

La trasera **ya no sale por atrás**: la banda que la tapa es la estructura. Sale
por **abajo**: tabla fuera (6 M5 + 4 paticas), talón fuera (3 M4, sueltos con la
tabla), los 5 M3 de arriba, y la plancha baja de debajo de la meseta y sale por el
suelo. Reversible entero y sin adhesivo — no es lo mismo que «quitar dos bandas y
tirar», y se dice.

## 5. El chasis del PSU pasa a la tabla

El chasis colgaba de la pared trasera por **dos M5 con separador «a la ranura
interior de `base trasera`»** — un 2020 que murió el 27-08. El modelo seguía
dibujando esos dos M5 a la altura de la ranura de un perfil que ya no existe y
`guarda_chasis()` solo comprobaba que cayeran en la pared del chasis con material
alrededor, no en qué mordían. Muerto el miembro bajo, no queda nada ahí.

Se fija **a la tabla, por el suelo, con cuatro M4 desde abajo** a tuerca
remachable (clinch, PEM S-M4) en el suelo del chasis: cabezas bajo la tabla — el
case va sobre sus paticas de 10 —, nada visto por dentro. Van en las dos orillas
libres de 10 mm que la PCB y el toroide dejan a cada lado del interior (x = 8.5 y
323.5 interiores, y = 20 y 150: a 6.75 de la curva del doblez, 2.75 fuera del
refuerzo del toroide y 8.2 del separador de la esquina de la PCB), lejos de la
ranura de salida de cables; `guarda_chasis()` lo comprueba y `taladros_talon()`
los cruza con la tabla. El suelo del chasis apoya
en la tabla (`chasis_pie` pasa de 2 a 0: el «aire para no resonar» era contra una
bandeja de acrílico que ya no existe; la tabla de 18 es la que se pidió
justamente para eso). La pared trasera se arrima al canto del pie del talón con
`chasis_holgura_larguero` = 3: el chasis retrocede **12 mm** (su cara trasera de
270.91 a 282.91), que son 12 mm más de fondo de módulo para la fila de abajo.

La **pieza fija del IEC** (#130, no dibujada) que iba a atornillarse «al larguero
de base trasera» pasa a atornillarse al pie del talón o a la tabla; el papel lo
apunta, no lo dibuja.

## 6. Lo que se ve

- **Atrás:** dos bandas de 24 a ras del plano trasero, el acrílico 1.5 por detrás,
  **diez cabezas M3 sobre metal** y ninguna sobre el acrílico (eran 16). Las
  bandas mueren en la cara interior del anillo, sin escalón.
- **Arriba:** una chapa del pico al canto, sin costura. En P5 el mismo radio de
  4.5 que el anillo.
- **Abajo-atrás:** la esquina P6 del anillo redondea a 4.5 como las otras; el
  talón dobla ahí sobre la tabla, igual que la nariz dobla delante sobre ella.
- **Por los costados, a través del PMMA:** una sombra continua de 6 alrededor de
  la ventana. Ninguna pieza nueva asoma por fuera; si asomara, estaría mal puesta.
- **Por dentro:** un marco liso por costado con sus diez cabezas y seis cajeados;
  en el techo, dos pestañas con escalón; en la trasera, diez tuercas con arandela
  de nylon (nunca acero contra acrílico) — cinco en la meseta, cinco detrás del
  chasis. Nada de clips, escuadras ni canales.

## 7. Las puertas — escritas antes que el modelo, vistas en rojo

| puerta | qué hace |
|---|---|
| **muere** `guarda_escuadra_trasera`, `guarda_marco_trasera`, `TRAMOS_CLIP`/`_clips`/`_cajas_clip`/`_roscas_clips`, `_escuadras_trasera`/`_cajas_escuadra`/`bbox_desarrollo_escuadra`, `_marcos_trasera`/`_cajas_marco_trasera`/`bbox_desarrollo_marco`, `_secciones_miembro`/`guarda_miembros` (la comparación con el 2020), `PLACAS_DXF`/`taladros_placas` (las tres placas y el clip) | |
| **nueva** `guarda_marco_ventana()` (budget) | el contorno es exactamente las tres placas de hoy en las filas (mismas esquinas, mismos cajeados, mismas roscas) más las cuatro patas; canto exterior retirado `retiro_marco` bajo cada chapa y a 0 en las filas; cada pata bajo `carga_mano` ≤ 2 mm y ≤ RP02 — las que llevan rosca por su vano mayor, las que no (la trasera) enteras y empotradas solo por las esquinas con rosca vecina a ≤ `EMPOTRE_MAX` y sin cuello de muesca —; las dos roscas del suelo lejos de los M5 de la tabla; la muesca deja ≥ 8 de pata; sombra de 6 sobre el acrílico en los siete tramos. Los agujeros contra el canto de su pata (las del suelo a 6.85, piden 6.75) en `guarda_anclajes()` |
| **nueva** `taladros_marco_ventana()` (check_dxf) | relee `marco_ventana_2d`: los doce M4 ciegos (diez de las filas, dos del suelo), los seis pasos de riel y la rosca M3 de la pestaña donde el modelo los pone, todos a 1.5 D del canto — sin pasos de brida: ahí va la muesca —; el contorno releído pasa por las ocho patas |
| **nueva** `guarda_miembro_alto()` (budget) | sustituye a `guarda_miembros`: la L sola, con `carga_mano` en el centro, tensión ≤ `RP02_ALUMINIO` y flecha publicada; la fila de M3 a ≥ raíz del doblez y ≥ 1.5 D del canto libre; las pestañas: caben en la banda bajo la meseta, sus M4 a 2 D uno de otro y a 1.5 D del canto de arriba |
| **nueva** `guarda_talon()` (budget) | banda a ras del plano trasero, pie sobre la tabla, sus tres M4 avellanados a 1.5 D del canto libre y **la boca del avellanado a ≥ tol + 0.5 = 1.70 de la cara de la trasera** (la regla de §4.3 vale para ella: con el pie de 20 quedaba a 0.77, por eso 22), la fila de M3 a ≥ raíz del doblez de abajo; P6 = `radio_chapa` |
| **nueva** `guarda_trasera_dentro()` (budget) | §4.3: ningún cuerpo fijo en x ∈ [x_trasera_int − (tol + 0.5), x_trasera_int) dentro de la huella de la trasera — es la que retiró la pata trasera del marco a 11.2 —; la trasera cubierta arriba por la meseta y abajo por el pie; las muescas de esquina libran la pestaña con 0.5 |
| **nueva** `taladros_talon()` (check_dxf) | relee `talon_2d` (fila de M3 + nada más) y cruza sus tres M4 con `bandeja_base_2d`, como `taladros_nariz` |
| **cambia** `guarda_anclajes` | las roscas ciegas son 14 por anillo (12 del marco + 2 de brida); cada agujero del marco contra los cantos REALES de su pata (los extremos en las esquinas son ficticios: el marco sigue de largo); la brida contra su propio canto y contra la raíz del doblez; muere el bloque del clip y el del chaflán de placa |
| **cambia** `guarda_costado` (check_dxf) | el apoyo hacia dentro deja de ser una lista de placas + clips + escuadra y pasa a ser el contorno interior del marco: el vano interior se mide a un canto continuo, como el exterior |
| **cambia** `cuerpos_dentro_del_anillo`, `solapes`, `_cajas_solidas` | el marco, las dos pestañas, el talón y la trasera nueva como cuerpos; fuera clips, escuadras, marcos, miembro bajo y sus bridas |
| **cambia** `guarda_remate` | `prof_sup == marco_remate` (un sumando); la meseta llega al plano trasero |
| **cambia** `guarda_retorno_meseta`, `guarda_tapa` | el retorno como ayer; los obstáculos son la banda, la meseta y el retorno; la tapa de arriba abre 180°. Es la puerta que tumbó el escalón de la pestaña |
| **cambia** `taladros_reticula` | `MIEMBROS_DXF` = {`miembro_alto_2d`, `talon_2d`}; la fila del alto en la banda, la del talón en su banda |
| **cambia** `agujeros_donde_toca`, `alineacion`, `apoyo`, `guarda_agarre` | las filas de la trasera caen en las bandas (24 de material, no en un canto) |
| **cambia** `guarda_chasis` | los cuatro M4 del suelo: en las orillas libres, fuera de la ranura y del refuerzo, cruzados con `bandeja_base_2d`; mueren los dos M5 de pared |
| **cambia** `guarda_zocalo` (check_dxf) | el censo de la tabla: 4 pies + 3 nariz + 3 talón + 4 chasis, cada uno por su posición |
| **cambia** `guarda_paticas`/`bandeja_base_2d` | las dos paticas traseras bajo el centro del pie del talón (x = 295.91; estaban en 285.91) |
| **cambia** `_sobres`, `todo_dxf_tiene_quien_lo_mire`, `export.ps1` | entran `marco_ventana_2d` y `talon_2d`; salen los siete DXF muertos |

El orden es el de siempre: la puerta primero, en ROJO por su razón contra el DXF
viejo, el modelo después, VERDE, y romperla a propósito una vez.

## 8. Lo que cambia para el taller

- **Chapa (láser), no mecanizado**: `marco_ventana` ×2, pletina de 6 cortada a
  láser, seis cajeados Ø8 × 2.5 por el lado del anillo — tres por una cara y tres
  por la otra, como las placas de hoy —, sin más operaciones. Va al lote B del
  RFQ, como las placas de ayer, con una tolerancia que las placas no
  necesitaban: **planitud ≤ 0.5 mm en 300** en el blank cortado (`PLIEGO.md`
  §6). Apoya en la cara mecanizada del anillo y sus doce M4 la conforman
  contra ella — aplanar 0.5 una pletina de 6 × 24 sobre 150 cuesta 200 N —,
  pero un anillo de 294 × 253 con alma de 14.8 cortado a láser puede venir con
  más, y con más el acrílico lo nota. (La primera versión de este papel lo
  mandaba al mecanizado «con planitud como los anillos»; el pliego lo tenía en
  chapa sin pedirle nada. Queda en chapa con la planitud escrita.)
- **Chapa**: `miembro_alto_2d` cambia de desarrollo (banda + meseta + retorno,
  un doblez de 90°, uno de 45° y dos pestañas de la banda a 90°: blank 588.00 ×
  73.83); entra `talon_2d` (un doblez de 90° a r = 3, blank 540.32 × 42.70);
  salen `miembro_bajo_2d`, `escuadra_trasera_2d`, `marco_trasera_sup_2d` y
  `marco_trasera_inf_2d`.
- **Acrílico**: `piel_trasera_2d` con diez taladros (no dieciséis) y dos muescas
  de esquina de 2 × 15, con radio 2 en el rincón (el PMMA raja desde una esquina
  viva).
- **Carpintería**: la tabla gana **siete taladros pasantes Ø4.5**: tres del talón
  (como los de la nariz) y cuatro del chasis.
- **Tornillería**: M4 avellanado × 3 para el talón (avellanado conformado en
  la chapa de 1.5; la cabeza a ras del pie, bajo la trasera no hay nada que
  asome); M4 × 4 para el chasis (a tuerca remachable); los M3 de la trasera,
  10 con tuerca y **arandela de nylon** del lado del acrílico. Los cuatro M4
  de las pestañas, como ayer, y **cuatro M4 más de marco** (las dos roscas del
  suelo por costado): 24 en vez de 20.

## 9. Lo que este documento NO cierra

- **La banda de 24 contra 20** se juzga en render (§4.5). Con 20 hace falta
  obligar 6082-T6 en el pliego; el papel deja las dos cuentas.
- **El marco de la ventana pisa 9 de acrílico en el rincón del valle** (P3) en
  vez de 6, porque su canto interior es recto y el del anillo curva a 54. Se ve
  a través del PMMA como una sombra un poco más ancha ahí; se juzga en render.
- **El canto del pico bajo una mano puntual** no tiene puerta, hoy tampoco: una
  chapa de 1.5 en voladizo de 40.5 con un labio de 4. No empeora (§4.4), y una
  puerta honesta pide un modelo de placa que no se inventa aquí.
- **#203, el racking**, sigue sin número. Este cambio ata el diafragma trasero a
  la tabla en vez de a un canal de 1.5; el argumento es de camino de carga, no de
  medida.
- **#130, la pieza fija del IEC**: su anclaje era el miembro bajo; pasa al talón o
  a la tabla cuando se dibuje.
- **La fijación del chasis de hoy estaba muerta**: apuntaba a la ranura de un 2020
  que murió el 27-08 y la puerta no lo veía. Se cierra aquí (§5); el hallazgo
  queda en el cuerpo del PR y en el §11 de la spec del 15-08.
- **El orden de montaje del README** ponía los costados después de las placas y
  los clips, y así no entra un costado en su rebaje. Se corrige en el README con
  esta tanda.
- **El cupón (#237)** sigue sin cortarse. El marco de la ventana es otra pieza que
  se atornilla sobre la cara mecanizada: su planitud entra en la misma pregunta.
- **Seis de las diez cabezas del marco caen bajo la huella del riel (#242)**, y
  el orden de montaje que el cajeado obliga — riel al marco, después el marco
  al anillo — no se puede apretar para esas seis. Está igual en `main` (las
  placas tenían las mismas roscas) y no lo trae este cambio; lo cazó el revisor
  del PR. Arrastra dos cotas de `params.scad` sin puerta: las 14 entre las dos
  roscas del par y los 10.19 al cajeado, que con el par arrimado son 7.40. Va
  aparte: puerta roja sobre `main`, después el reparto de las roscas.

## 10. Enmiendas a otros papeles — ejecutadas en esta misma tanda

| papel | qué cambia |
|---|---|
| `2026-08-15-case-design.md` | rev. 25 en el historial; §5 y §9 (piezas y BOM) |
| `2026-08-28-costilla-pletina-design.md` | §4 (los clips → el marco), §5 (las placas → el marco; las bridas del miembro alto con escalón; el miembro bajo → talón), §10 (la escuadra: superada) |
| `2026-08-27-case-esqueleto-visible-design.md` | enmienda en cabecera: de tres miembros a uno más el talón; el chasis a la tabla |
| `2026-08-29-nariz-recta-valle-limpio-design.md` | §2.3: la meseta llega al plano trasero, no al doblez del alma |
| `case/README.md` | piezas, BOM, tornillería (73 → 68), orden de montaje corregido (con la deuda de #242 escrita), roscas por anillo |
| `case/PLIEGO.md` | rev. 25: `marco_ventana_2d` (cajeados por cara, planitud), `talon_2d`, `miembro_alto_2d` con sus pestañas, muescas de la trasera, taladros de la tabla; fuera siete DXF |
| `case/RFQ.md` | rev. 24: a la chapa le entran el marco (láser, con planitud) y el talón; al acrílico las muescas; al carpintero siete taladros; al mecanizado 14 roscas por anillo |
