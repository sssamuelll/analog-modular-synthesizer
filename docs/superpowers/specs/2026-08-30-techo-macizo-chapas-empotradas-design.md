# El techo macizo, con la salida de aire por el alero, y las tres chapas empotradas en el anillo

> **Enmienda 2026-10-11:** la mejilla de acrílico coplanar que este papel describe la sustituyó la persiana ([`2026-10-11-case-persiana-design.md`](2026-10-11-case-persiana-design.md)); el rebaje del anillo se queda vacío.

> **Enmienda 2026-10-11 (ficha 6):** la nariz sube hasta pisar 1 mm de la cara del riel de abajo (`retiro_placa_inf` 9 → 11.9, blank 545.62 × 53.10) y el retorno de la meseta baja de 4 a 9 hasta pisar la del riel de arriba (blank 593.02 × 78.85): las dos rendijas se cierran. Los blanks de este papel (593.02 × 73.85 y 545.62 × 50.20) son los de antes. Lo mide `guarda_labio_chapas()` ([`2026-10-11-case-persiana-design.md`](2026-10-11-case-persiana-design.md) §7.3).

**Fecha:** 2026-08-30 · **Estado:** aprobado por Samuel en conversación («dale»)
sobre la propuesta de esta mañana, con sus cuatro números (chapa rehundida 1,
rebaje en las tres chapas; y para la tanda B, panel 1U de 55 y paneles 1.5
abajo); **corregido contra dos rondas de crítica adversarial de codex**
(Serrano, Halberg, Rune): ronda 1 — la ranura del rebaje a 3.5 (la fresa es Ø3),
la rendija a 3.0 y el labio del techo a 20 (capilaridad), el tramo trasero a 22,
las chapas a 545.62, el rebaje al DXF del dorso; ronda 2 — **los pies no se
rehunden** (apoyan en la tabla), el tramo trasero por bandas de altura, el
cajeado de la brida a 28 × 15.5, **la tabla entra con el anillo B** con nariz y
talón ya atornillados en el banco, y una mutación por aserto que de verdad
salta ahí; ronda 3 — la muesca de los pies a 2.65 hasta la línea de doblez del
desarrollo, el chasis entra al final por el frente, los umbrales contra
constantes y los derivados sin doble fuente; ronda 4 — **el pie del talón a
21.5** (la boca del M4 quedaba a 1.27 de la trasera retrocedida), la fórmula de
la muesca, el #242 citado, y los dos ensayos con su línea que faltaba; ronda 5
(2026-08-30) — **las dos puertas usan la luz comprimida**, la rendija sube a
4.0, la trasera retrocede otro milímetro y los dos pies recuperan margen ·
**Tanda A de dos**: la B (la fila 1U más alta con sus rieles, los
paneles empotrados y el apoyo de la banda del valle) tiene su propia spec ·
**Supersede** en el techo, en la unión chapa-anillo, en la junta de los labios,
en la ventilación y en el orden de montaje a la spec del 29-08 (trasera
capturada) y a la del 27-08 (esqueleto visible) en lo que dicen de eso.

## 1. De dónde sale

Samuel, con el `.blend` de piezas abierto (cada pieza con el nombre de su módulo),
el 30-08 por la mañana:

> «en la pieza miembro alto no me gustan los huecos. es una decisión errática del
> diseño ya que esa parte es sensible a que le entren líquidos. lo otro es que el
> acabado debe sentirse perfecto con respecto a la esquina. perfectamente
> alineado con el del marco o si no se ve feo. tiene que ser una pieza que se
> sienta empotrada.»

Y, preguntado por la esquina de arriba-atrás, dos cosas y no una: **el borde de la
chapa contra el anillo** (termina a tope contra la cara interior y se le ve la
costura; empotrada = que entre en un rebaje del anillo, como el acrílico en su
bolsillo) y **el chaflán de la chapa no sigue el del anillo** (los dos dobleces a
45° con radio no se leen como el mismo plano que el chaflán de 6 mecanizado).
Sobre el acabado, su vara: «a pesar de que estoy haciendo el instrumento de forma
artesanal, tenga un acabado de instrumento profesional serio, así nivel Moog».

Tres hechos del repo que mandan aquí (trazados el 30-08):

1. Las 16 ranuras de la meseta son la **salida** del circuito de convección
   natural, no un adorno: entrada por la rejilla baja de la trasera (46 ranuras,
   7 193 mm² a y = 47), salida por la meseta (852 mm² a y = 255) y por las dos
   ondas abiertas de la trasera (2 289 mm² a y = 98). `guarda_aire()` exige salto
   térmico ≤ 15 K, no paridad de áreas; hoy da **10.8 K** con 6.33 W. Solo
   borrarlas: **15.9 K**, rojo (`params.scad` ~1612-1654; `clearance_budget.py`
   `guarda_aire`, `_rejilla_valle`, `_ondas_trasera`).
2. La chapa va **a ras** del contorno del anillo: el `.scad` usa los puntos del
   perfil como cara exterior y pone el espesor hacia dentro (`tramo_chapa()`),
   y termina **a tope** contra la cara interior (`z0 = t_anillo`; el techo mide
   `ancho_util` = 540.62 desde z = 14, nariz y talón 540.32 desde 14.15). El único
   rebaje del anillo es para el acrílico (`rebaje_anillo` 6, `rehundido_acrilico`
   3). Ninguna puerta mide asiento, luz ni escalón de la chapa contra el anillo,
   y el sólido de la chapa se dibuja sin los arcos del plegado: la coincidencia
   de los dos chaflanes es coplanar sobre el papel y depende del taller en la
   pieza.
3. El presupuesto térmico cuenta **6.33 W** (solo los reguladores del PSU) y la
   spec de la fuente calcula **9.22 W** de peor caso para su chasis (a media
   carga, con el LED al tope del #104; `2026-08-18-fuente-chasis-telemetria.md`
   §3.1). No hay enlace ejecutable entre los dos. Con 9.22 W el diseño de hoy
   queda en **13.9 K** con el C_D de 0.65 que la puerta asume, y en **15.5 K**
   si el C_D real es 0.55: por un pelo, y pasar por un pelo no es pasar.

## 2. La cuenta

Fórmula de `guarda_aire()`, tal cual (tiro de chimenea laminar, entrada y salida
en serie, C_D 0.65, 20 °C), **con el labio del techo ya a 20** (§3.2): la rejilla
de entrada y las ondas se anclan a lo que se ve de la trasera, así que bajan 2
mm y la entrada queda en **7 065 mm² a y = 46** (hoy 7 193 a 47). La última
columna repite la de 9.22 W con C_D 0.55, la sensibilidad que la crítica pidió.

| escenario | salida (mm²) | tiro (mm) | 6.33 W | 9.22 W | 9.22 W, C_D 0.55 |
|---|---|---|---|---|---|
| hoy: meseta 852 + ondas 2 289 | 3 141 | 94 | 10.8 K | 13.9 K | 15.5 K |
| techo macizo, nada más | 2 289 | 51 | **15.9 K** | 20.5 K | — |
| techo macizo + rendija a 2.5, ocho tacos de 15 | 3 341 | 95 | 10.4 K | 13.4 K | 14.9 K |
| **techo macizo + rendija a 4.0, seis tacos de 15** | 3 731 | 105 | **9.5 K** | **12.2 K** | **13.6 K** |
| ídem, rendija a 3.5 | 3 866 | 108 | 9.2 K | 11.8 K | 13.2 K |

Se adopta la fila en negrita. La rendija del alero (§3.2) está más alta que el
centro de las ondas y aporta más área que la meseta que sustituye: el aparato
respira **mejor** que hoy en los tres supuestos, y con un C_D pesimista sigue
bajo 15 donde el diseño de hoy no.

**Corrección adversarial del 2026-08-30.** La primera cuenta adoptaba 3.0 por
capilaridad, pero calculaba el área con la luz nominal mientras la puerta
capilar ya usaba la comprimida. Al usar la luz comprimida en las dos puertas,
3.0 da **14.8 K** con `C_D = 0.55`: quedan **0.2 K** contra el techo de 15, que
no es margen. Con 4.0 quedan **1.4 K**. El motivo capilar anterior no se borra:
también mejora, porque la subida va con `1/d`.

Las dos filas de exploración que flanquean la adoptada quedan como historia:
todavía calculaban el área con la luz sin comprimir. No son cotas ni resultados
operativos.

## 3. El techo macizo, y la salida de aire por el alero

### 3.1 Lo que se quita

Las 16 ranuras de la meseta (`meseta_paso_hp`, `meseta_largo_ranura`, el bucle de
`miembro_alto_2d()` y `ranura_meseta_3d()`). La meseta queda **maciza**: un
líquido sobre el techo no tiene por dónde entrar. `_rejilla_valle()` deja de
existir como término de salida y `guarda_puentes_ventilacion()` pierde su caso
«meseta».

### 3.2 La rendija: lo que el labio ya tapa

Hoy el labio trasero del techo (18, de y = 250.18 a 232.18) tapa **6.5 mm** del
canto de arriba de la trasera (y1 = 238.68), y la trasera va **4 mm detrás del
plano trasero** (labio del bolsillo 3 + junta de asiento 1). Entre la cara
interior del labio y la cara vista de la plancha hay **2.5 mm de aire**
(`aire_labios`), que la spec del 29-08 dejaba para una tira continua de EPDM.
Por dentro, sobre el canto de la trasera, quedan **13.4 mm** hasta la cara
interior del chaflán.

Eso es una salida de aire hecha: el aire de la caja pasa por encima del canto de
la trasera y sale hacia **abajo** por la rendija, tapada por el alero del techo.
Un derrame sobre la meseta baja por el chaflán, por el labio, y gotea por el
canto del labio por delante de la plancha. Lo que hay que cerrar es que **no
suba por capilaridad**: entre dos planos a d, el agua (γ = 0.073 N/m, mojado
total como peor caso) sube 2γ/(ρ g d) = **5.9 mm a d = 2.5**, contra 6.5 de
solape — 0.6 de margen, y a 1.5 de luz local (una plancha alabeada) 9.8, por
encima del canto. Por eso dos números cambian:

- **`aire_labios` = 4.0**, que es también el grosor de los tacos (§3.3);
- **`techo_labio` = 20** (era 18): el labio baja a y = 230.18 y tapa **8.5** del
  canto. La regla (§6, `guarda_rendija`): la subida con los tacos **comprimidos
  un 20 %** (luz 3.20: subida de 4.7 mm) queda por debajo del solape menos 2
  (6.5). El techo
  gana sección (el labio de 18 ya era el mínimo por rigidez, §5 de la spec del
  29-08), y lo que se ve de la trasera pierde 2.

Área de la rendija con la luz comprimida: **1 442 mm²** a y ≈ 238.

Con la chapa rehundida 1 (§4) la cara interior del labio pasa de 1.5 a 2.5 del
plano trasero; para que la rendija mida 4.0 **la trasera retrocede**: su labio
de bolsillo pasa de 3 a **`rehundido_trasera` = `rehundido_chapa` + `t_costilla`
+ `aire_labios` − `t_junta_asiento` = 5.5** (cara vista a 6.5 del plano). Es un
valor **derivado**, no un parámetro: la única cota de la trasera que deja de
ser «la del costado, girada»; la junta de 1 y el hondo de 6 siguen iguales.

### 3.3 La junta a tacos, en los dos labios

La tira continua de 2.5 tras los labios (spec 29-08 §9, «con la primera pieza»)
se decide aquí: **tacos de EPDM de 4.0 × 15**, seis por labio (uno cada ~90 mm,
pegados a la cara interior del labio), en el labio del techo **y** en el del
talón. Una sola regla para las dos juntas; sujetan la plancha sin que suene,
fijan la luz (la plancha no puede pegarse al labio y cerrar la salida: el taco
es la luz, y la puerta la cuenta comprimida un 20 %) y dejan la rendija libre
entre ellos. Solo la de arriba se cuenta como salida. La de abajo (a y ≈ 6-19,
bajo el labio del talón, mirando al suelo) es una entrada que no se cuenta: si
entra aire por ahí mejora el tiro y no aparece en el número.

### 3.4 Los vatios

`potencia_disipada` pasa de 6.33 a **9.22 W**, con la cita: es el peor caso de la
spec de la fuente para su chasis (a media carga, no a 650 mA). Los módulos
siguen fuera: el repo declara que la bahía de arriba está **sellada** del camino
del PSU (`params.scad` ~1515: «el salto térmico describe el camino del PSU, no
la bahía de arriba, que es justo lo que se sella»), así que sus vatios no van a
esta fórmula — pero tampoco tienen presupuesto propio. Orden de magnitud, por
el mismo método de superficie de la spec de la fuente (9 W/m²K): 2 raíles × 12 V
× 174 mA del censo ≈ **4.2 W** sobre ~0.3 m² de paneles y pieles ≈ **1.5 K**.
Es un ESTIMADO y no cierra nada: queda en §8.

El techo se queda en 15 K y no pegado al número: 12.2 K pasa, y 13.6 con
C_D 0.55 deja 1.4. C_D, la altura efectiva y las pérdidas siguen sin medir, como
el propio `guarda_aire()` declara: por eso §8 pide el ensayo con la primera
unidad.

### 3.5 El gotero

Con la luz a 4.0 y el solape a 8.5 la cuenta capilar cierra sin él. Si la primera
pieza gotea hacia dentro, el remedio es un **dobladillo hacia FUERA** (180°, 3
mm) en el canto de los dos labios — hacia dentro estrangularía la rendija a 1.5
justo en la línea del canto y subiría la capilaridad a 9.8 —, y es visible: se
decide mirando (§8).

## 4. Las tres chapas empotradas en el anillo

### 4.1 El rebaje de chapa

En la cara interior de cada anillo, a lo largo del contorno **solo en los tramos
que se ven** — nariz: chaflán y frente hasta P1; techo: del retorno de P4 por la
meseta, el chaflán de P5 y el labio hasta y = 230.18; talón: labio de y = 19 a 6
y chaflán —, un **rebaje de `rebaje_chapa` = 3 de fondo** (z, 2 t, desde la cara
interior: z = 11..14 contando desde la cara vista) y de u = `rehundido_chapa` a
  u = `rehundido_trasera` (de **1 a 5.5**: 4.5 de ancho, la fresa de Ø3 del pliego
entra; a 2 de ancho no entraba). La chapa entra en él:

- su cara exterior queda a **`rehundido_chapa` = 1** por dentro del contorno del
  anillo, y su cara interior a 2.5; al suelo del rebaje le sobran 2: el suelo
  no posiciona, posicionan las bridas y los M4 de los pies;
- su canto queda **debajo del anillo** con `hol_chapa` = 0.5 a la pared del
  rebaje (no los 0.15 de `hol_piel`: una chapa cortada a ±0.3 tiene que entrar
  aunque venga larga, y aun larga queda 2.2 tapada): **lo que entra en rebaje
  mide 546.62 − 2 × 0.5 = 545.62** entre paredes (el techo crece 5.0 sobre sus
  540.62; el chaflán y el frente de la nariz, y el labio y el chaflán del talón,
  5.3 sobre sus 540.32);
- el borde del anillo es un **reborde de 1 × 3** (u = 0..1, z = 11..14) que
  recorre el contorno donde hay chapa: es lo que se ve como marco, y lo que
  tapa el canto. Una pared de 1 con 3 de alto se fresa (3:1) pero es la cota más
  delicada de la pieza: va al RFQ como pregunta con respuesta ya diseñada — si
  el taller pide 1.5, `rehundido_chapa` = 1.5 y todo lo derivado se mueve solo
  (§6, puerta «reborde»).

**Los pies NO se rehunden.** El pie de la nariz y el del talón apoyan en la tabla
con su cara de abajo en y = 0, a ras de la cara de abajo del anillo, y sus
puntas mueren a `hol_piel` de la cara interior del anillo (z = 14.15) como hoy:
rehundir un tramo horizontal es levantarlo 1 mm de la tabla, y ahí no hay nada
que ver ni que empotrar (la tabla lo tapa). Así que el desarrollo de la nariz y
el del talón lleva en cada punta una **muesca de (545.62 − 540.32)/2 = 2.65**
de hondo (derivada: `rebaje_chapa` − `hol_chapa` + `hol_piel`: la pared del
rebaje está 3 dentro de la cara, lo rehundido se queda 0.5 antes y el pie 0.15
después) desde el canto
libre del pie hasta **la línea de doblez pie-chaflán del desarrollo**, que no
  está a «largo del pie» del canto sino a largo − BD/2 (el talón: 22.5 − 0.44 =
  22.06; la nariz: 20.5 − 0.44 = 20.06 — las líneas que cotaba el PLIEGO antes
  de esta tanda, 19.56 y 17.56, se mueven con los pies de §4.6), con
un **alivio de Ø2** centrado en la esquina, a caballo de esa línea, como el de
las pestañas (`alivio_pestana`), para que el doblez no la rasgue. La pestaña
más cercana del talón arranca a 20 mm de ahí y el primer M4 del pie conserva
sus 1.5 D al canto libre: no chocan. Nada cambia en la tabla ni en los M4 de
los pies.

El acabado que Samuel pide sale de que ninguna de las dos cotas que se ven
depende del taller de chapa: la junta de sombra de 1 mm la fresa el anillo, y el
canto de la chapa no se ve. Un desvío de ±0.3 en el desarrollo o en el doblez se
esconde bajo el reborde, donde antes era un escalón sobre la superficie.

### 4.2 Las esquinas: el reborde sigue al pliegue

Hoy el anillo lleva `radio_chapa` = 4.5 (radio interior 3 + t) en las esquinas
que llevan chapa a 90° y en los dos vértices de cada chaflán: la esquina viva
asomaría 1.9 mm bajo un doblez de 90° y 0.4 bajo uno de 45°. Con la chapa
rehundida 1, el contorno del anillo es la cara exterior de la chapa desplazada
1 hacia fuera: **`radio_borde` = `radio_chapa` + `rehundido_chapa` = 5.5**
(derivado), concéntrico con el arco exterior del pliegue. En P5 (B), el chaflán
de 6 del anillo y el de la chapa quedan a 1 mm uno de otro y paralelos, con los
vértices redondeados sobre el mismo centro que el doblez: se leen como el mismo
plano aunque el taller doble a 2.9 o a 3.1, porque la diferencia cae dentro de
la junta de sombra y no sobre una arista compartida. Donde la chapa sale del
rebaje hacia el pie (los vértices de abajo de los chaflanes de P0 y P6), el
reborde muere en la cara de abajo del anillo y el radio del vértice vuelve a
ser el de hoy.

El sólido de la chapa se dibuja igual que hoy (cubos y polígonos, sin arcos); lo
que cambia es que el anillo ya no pretende coincidir con un arco que el modelo
no tiene.

### 4.3 El tramo trasero, por bandas de altura

En la cara vertical P5-P6 (x = 307.41, de y = 6 a 250.18) el anillo lleva el
  bolsillo de la trasera (z = 8..14 desde la cara vista; cerrado de y = 1 a
  239.18), el del costado (u = 19.5..23, z = 3..14, el PMMA en z = 3..11), y donde
  hay labio de chapa, el rebaje (u = 1..5.5, z = 11..14). Con `rehundido_trasera`
  = 5.5 el bolsillo de la trasera va en **u = 5.5..16.5**, su pared en 16.5..19.5
  (`pared_rebaje_trasera` = 3) y el costado entra 3.5 en 19.5..23: **la franja del
  tramo trasero pasa de 20 a 23** (`cara_anillo_trasera` = 5.5 + 11 + 3 + 3.5). Lo
que hay en cada banda de altura, de fuera a dentro:

| y | z = 11..14 | z = 8..11 | z = 3..8 |
|---|---|---|---|
| **6..19** (labio del talón) y **230.18..239.18** (labio del techo sobre el bolsillo) | reborde en u = 0..1; **un solo vaciado de u = 1 a 16.5** (rebaje + bolsillo: la chapa en 1..2.5, aire, la trasera en 6.5..14.5); pared; costado | labio del bolsillo en u = 0..5.5 (**3 de hondo**), bolsillo 5.5..16.5, pared, costado | macizo hasta 19.5; costado |
| **19..230.18** (sin chapa) | labio del bolsillo en u = 0..5.5 (6 de hondo, como hoy), bolsillo, pared, costado | ídem | macizo; costado |
| **239.18..240.18** (fin del bolsillo, bajo la brida) | reborde; rebaje en u = 1..5.5; macizo hasta 19.5; costado | macizo; costado | macizo; costado |
| **240.18..250.18** (la brida, hasta el chaflán) | reborde; **rebaje y cajeado de la brida en un solo vaciado**, de u = 1 hasta el fondo del cajeado (~30); luego macizo hasta 19.5 si el cajeado no llega; costado | macizo; costado | macizo; costado |

De la tabla salen tres cosas: **bajo los dos labios de chapa el labio del
bolsillo queda con 3 de hondo** (z = 8..11; en z = 11..14 lo sustituyen el
reborde y el propio labio de la chapa, que a 4.0 de aire con los tacos sigue
parando la plancha hacia fuera); **no queda ninguna aleta**, porque el suelo
  del rebaje es la pared exterior del bolsillo por construcción (u = 5.5,
derivado, §3.2); y **el bolsillo sigue cerrado en y = 239.18**: por encima solo
hay rebaje y, desde 240.18, el cajeado de la brida, cuyas roscas quedan 8.5 por
encima del cierre como hoy. La alternativa que la spec del 29-08 ya dejaba a
  Samuel — el costado a 6 en los cuatro tramos — vale 25.5 aquí y se ve 4.5 más
ancha desde el lado; no se toma en esta tanda.

### 4.4 Las bridas del techo

El repo fija la brida **en la cara del anillo** (z = 14) y lo llama no
negociable porque a z ≥ t_anillo + t_placa está el barrido del panel de arriba.
Aquí la brida cambia de plano **en la dirección segura**: como el labio entra 3
en el rebaje, dobla en z = 11 y apoya en un **cajeado de `rebaje_chapa` = 3 de
fondo** en la cara interior — queda de z = 11 a 12.5, **1.5 por debajo** de la
cara, más lejos del barrido, no más cerca. En y no se mueve: dobla del extremo
del labio, que sigue muriendo en 230.18, y queda de 240.18 a 254.68 como hoy; su
cajeado va de 239.68 a 255.18 — hasta u = 1, donde muere el reborde, que queda
entero sobre él. El cajeado es la huella de la brida
(27 × 14.5, con su esquina de arriba cortada a 45°) más 0.5 por lado: **28 ×
15.5**, con esquinas interiores de R1.5 (la fresa); **la brida lleva sus
esquinas redondeadas a R2** para asentar entera. Los dos M4 ciegos se roscan
desde el suelo del cajeado (quedan **11 de pletina**; hoy 14). La muesca del
marco de la ventana sobre la huella se queda: las cabezas siguen asomando por
encima de la cara.

### 4.5 El marco de la ventana

Su canto exterior se retira bajo las chapas `t_costilla` + `hol_piel` = 1.65
hoy (`_retiro_marco_chapa`); pasa a **`rehundido_chapa` + `t_costilla` +
`hol_piel` = 2.65** en frente, meseta y cola bajo el retorno (en el suelo, bajo
los pies, sigue en 1.65: los pies no se rehunden). En el tramo trasero la pata
del marco arranca 0.5 más allá de la pared del bolsillo de la trasera
(`_retiro_marco_trasera` = `t_anillo` + 0.5 = 14.5 hoy); con el bolsillo en u =
5.5..16.5 arranca en **17**, 1.5 más adentro, y la pata de `marco_fondo_trasera`
= 28 perdería ese ancho. **Pasa a 30**: con el retiro en 17 la fórmula vigente
de `guarda_marco_ventana()` da **1.54 mm y 114 MPa** (techos 2 mm y 130); con 28
quedaría roja (**135 MPa**, y a 26 también se pone roja). Corregido el 30-08 al
correr la puerta: este párrafo decía 1.45 mm y 106 MPa, que son los de un
retiro de 14.5 — el viejo. La decisión (30, no 28) no cambia; el número con que
se justificaba, sí.

### 4.6 Nariz y talón

Mismo rebaje, mismo reborde, mismos radios en chaflanes y frentes; los pies a
ras sobre la tabla con su muesca (§4.1). Sus pestañas siguen la cara interior
de la trasera (`pestana_x` se deriva de ella) y sus avellanados no cambian de
regla — pero **el pie del talón crece lo mismo que retrocede la trasera: 20 →
21.5 → 22.5** (`talon_pie`). La razón es la misma que lo puso en 20 y no en 18:
la boca
del avellanado del M4 es un cuerpo fijo detrás de la cara interior del
acrílico y necesita `tol_pmma` + 0.5 = 1.70 de aire; con la trasera 1.5 más
adentro y el pie en 20 quedaban **1.27** (`guarda_talon()` en rojo sin tocar
nada), con 21.5 volvieron los 2.77 de entonces. **Corrección del 2026-08-30:**
al retroceder la trasera otro milímetro, 21.5 deja **1.77**, verde por **0.07**;
con 22.5 vuelven los **2.77**. Y **el pie de la nariz lo sigue: 18 → 19.5 →
20.5** (`nariz_pie`), porque la misma `guarda_talon()` exige que los dos pies
difieran 2 o menos («mismo estilo», el punto 7 de su docstring) y con 18 y 21.5
se pone roja sin tocar nada más; va bajo la tabla, no se ve, y sus M4, su muesca
y sus taladros en la tabla se derivan igual. El desarrollo del talón pasa de
39.73 a **41.23** y ahora a **42.23**; el de la nariz queda en **50.20**. El
chasis del PSU, que se arrima
al canto libre del pie del talón con 3 de aire, se adelanta 2.5 con él. El chaflán de la arista de abajo-fuera de la trasera
(5.5) se recalcula con la plancha 2.5 más adentro y el labio del bolsillo a 5.5
(`chaflan_trasera_bajo()` y su gemela): es una cuenta, no una decisión.

## 5. Montaje: la tabla entra con el anillo B

Las tres chapas quedan capturadas por los rebajes de los dos anillos en lo que
entra en rebaje, y miden más que el vano entre caras: **entran con el anillo B,
como la trasera y los costados**. Para que nada quede de pie sin sujeción y
para que los seis M4 de los pies se sigan apretando en el banco, **la tabla se
une al anillo A antes de que baje el B**. El orden del README, pasos 4 a 7:

4. Con el anillo A tumbado (cara vista abajo), su costado, los rieles y el marco
   A como hoy. **La trasera** en el bolsillo de A, de lado, apoyada en el fin de
   abajo del bolsillo. **La tabla, preparada en el banco** con la nariz y el
   talón (sus 3 + 3 M4 avellanados desde arriba, como hoy) — **sin el chasis**,
   que entra al final (paso 6): con él puesto, el M4 del suelo del marco B más
   cercano queda a 4 mm de su pared y no hay por dónde apretarlo —, **se pone de
   canto sobre el tramo de abajo de A**: el labio
   del talón por fuera de la trasera y sus ocho pestañas por dentro, la nariz y
   el talón con sus puntas en los rebajes de A, y **sus 3 M5 al canto de A desde
   fuera de la tabla** (el redondo del medio primero). La trasera queda sujeta
   entre el bolsillo y el pie del talón. **El techo**, con sus tacos pegados,
   con la punta en el rebaje de A y **su brida A roscada** a los dos M4 del
   cajeado de A (el interior está abierto). El marco B en las puntas de los
   rieles; el costado B en el anillo B, sujeto con cinta hasta que el marco B lo
   pise (como hoy).
5. **El anillo B baja** sobre cinco puntas a la vez — marco B, trasera, techo,
   nariz y talón — y sobre el canto de la tabla, todas en z, como hoy baja
   sobre dos. Los doce M4 del marco B y los dos de la brida B **desde dentro por
   el frente abierto**; los 3 M5 de la tabla al canto de B **desde fuera**. De
   pie.
6. **El chasis del PSU entra por el frente**, por la ventana de la fila de abajo
   (su sección de 176 × 64 cabe en los 528 × 128.5 abiertos), se arrima al pie
   del talón (3 mm de aire) y sus **4 M4 se aprietan desde debajo de la tabla**,
   que es donde siempre estuvieron sus tuercas remachables.

Lo demás (tapa del valle, electricidad, paticas, paneles, el film al final) no
cambia. Ningún tornillo nuevo: los seis M4 de los pies siguen en el banco, y el
chasis es el único que cambia de momento, no de tornillos. **La deuda #242 sigue
igual**: seis de los diez M4 de las filas del marco B caen bajo la huella de los
rieles ya puestos y no hay cómo apretarlos; esta tanda no la crea ni la cierra,
y el orden se escribe con ese hueco a la vista, como el README de hoy.

## 6. Puertas (la puerta primero, ROJA; el modelo; VERDE; romperla)

Una puerta por cosa y una mutación por aserto, que salte por SU texto: como
`canario_trasera()`, `canario_techo()` **llama a la puerta objetivo con el dict
mutado y comprueba el texto del error** — no pasa por `main()`, así que lo que
otra puerta diga de la misma mutación no importa; lo que se exige es que ESTA
salte y por eso. Los derivados (`rehundido_trasera`, `radio_borde`,
`cara_anillo_trasera`, los anchos y la muesca, la profundidad del cajeado =
`rebaje_chapa`) no son parámetros: son funciones gemelas en el `.scad` y el
budget, y `check_dxf` las cruza contra el DXF; los umbrales de pared son
constantes (`PARED_MIN_ANILLO` = 3), no el propio parámetro. Orden en `main()`:
las de hoy como están, y las nuevas entre la trasera capturada y `guarda_aire`:
`guarda_rebaje_chapa` → `guarda_tramo_trasero` → `guarda_rendija`. Los casos
heredados de `canario_trasera()` se recalibran (el chaflán de la plancha se
recalcula con u0 = 5.5 y `t_piel` = 7 deja 4.5 de canto plano: el caso baja a
`t_piel` = 4, que sí dispara «canto plano»; los dos de `guarda_talon` vuelven a
saltar por lo suyo en cuanto el pie está en 22.5, §4.6). Las filas de
`check_dxf` no son casos de canario: son **tests de rotura a mano** en el plan,
como siempre con los DXF (params contra un DXF que no cuadra), y cada fila dice
cuál.

| puerta | asevera | mutación que la pone roja, por su texto |
|---|---|---|
| `guarda_aire()` (reescrita) | salida = rendija (`(ancho_util − n·largo_taco) × aire_labios × (1 − compresion_taco)`) + ondas; `potencia_disipada` = 9.22; ΔT ≤ 15; imprime ΔT con C_D 0.55 como aviso | `taco_largo` = 90 (tira continua: 20.5 K); `potencia_disipada` = 14 (16.4 K) |
| **nueva** `guarda_rendija()` | subida capilar 2γ/(ρ g d) con d = `aire_labios` × (1 − `compresion_taco`), `compresion_taco` = 0.2, ≤ solape − 2; solape = `techo_labio` + `chaflan_nariz` − (P5.y − y1) | `techo_labio` = 18 (solape 6.5: 6.2 > 4.5; el «≥ 6» de siempre sigue verde); `compresion_taco` = 0.4 (luz 1.8: 8.3 > 6.5) |
| **nueva** `guarda_rebaje_chapa()` | `rebaje_chapa` ≥ 2 t; ancho `rehundido_trasera` − `rehundido_chapa` = t + `aire_labios` − `t_junta_asiento` ≥ `fresa_d`; `rehundido_chapa` ≥ 1; `hol_chapa` ≥ 0.3; lo que entra en rebaje = luz − 2·`hol_chapa`; `radio_borde` = `radio_chapa` + `rehundido_chapa`; muesca de los pies = `rebaje_chapa` − `hol_chapa` + `hol_piel` (2.65) con su alivio | `rebaje_chapa` = 2 («menos de 2 t»); `aire_labios` = 2.4 (ancho 2.9: «la fresa no entra»; comprimida un 20 % la rendija también saltaría, 7.8 > 6.5, pero esta puerta se llama sola); `rehundido_chapa` = 0.5 («reborde más fino que 1»); `hol_chapa` = 0.2 |
| **nueva** `guarda_tramo_trasero()` | la tabla de §4.3: labio del bolsillo ≥ 3 de hondo bajo los labios de chapa y 6 en el resto; `pared_rebaje_trasera` ≥ `PARED_MIN_ANILLO` = 3 (**el aserto de la pared se muda aquí** desde la capturada, y contra una constante, no contra sí mismo); `entrada_costado_trasero` ≥ 3 (parámetro, 3.5); `cara_anillo_trasera` = `rehundido_trasera` + 11 + pared + entrada (derivado, 23); el bolsillo cerrado en y = 239.18 y el cajeado desde 240.18 | `entrada_costado_trasero` = 2.5 («el costado entra 2.5»); `pared_rebaje_trasera` = 2 («pared de 2 contra 3») |
| `guarda_trasera_capturada()` | como hoy menos la pared; con u0 = 5.5 derivado; el chaflán de la plancha recalculado | las de `canario_trasera()` de hoy (`t_piel` = 7, …) |
| `guarda_miembro_alto()` | como hoy (200 N sola; con el labio de 20) con la brida en su cajeado: pletina bajo las roscas = `t_anillo` − `rebaje_chapa` ≥ 8; cajeado = huella + 0.5 por lado; R2 de la brida ≥ R1.5 del cajeado | `rebaje_chapa` = 6.5 («quedan 7.5 de pletina bajo la brida»; corre antes que `guarda_tramo_trasero`, que también saltaría) |
| `guarda_marco_ventana()` | la pata trasera a 30 con el retiro en 17 | `marco_fondo_trasera` = 26 |
| `check_dxf.techo_macizo()` (nueva) | `miembro_alto_2d.dxf`: ningún contorno cerrado dentro del blank salvo los cuatro M4 de las bridas; esquinas de brida a R2 | el DXF de hoy, con sus 16 ranuras |
| `check_dxf.anillo_dorso_tiene_rebaje()` (nueva) | en `costilla_dorso_2d.dxf` (la cara mecanizada, no `costilla_2d`): el rebaje de 1..5.5 por el contorno de las chapas, fundido con el bolsillo de la trasera bajo los labios y con los cajeados de brida de 28 × 15.5; **las profundidades no se leen de una planta**: van al PLIEGO y al cupón (§7) | `rehundido_chapa` = 1.5 en params con el DXF a 1 |
| `check_dxf.anillo_tiene_ventana()` (reescrita) | la cara mide `cara_anillo` en seis tramos y `cara_anillo_trasera` (derivado) en el trasero (hoy exige 20 uniforme y pondría rojo el anillo correcto) | `entrada_costado_trasero` = 2.5 en params (cara 22) con el DXF a 23 |
| `check_dxf` sobres y radios | los desarrollos con lo que entra a 545.62, la muesca de los pies y su alivio; `costilla_2d` con radios de 5.5 donde hay chapa y 4.5 donde no | `hol_chapa` = 0.3 en params con el DXF a 0.5 |

Renders: las dos vistas de siempre y **los dos primeros planos de la esquina de
arriba-atrás** (tres cuartos y perfil, los del 30-08 en `build/`) pasan a ser
renders del repo, porque lo que se juzga aquí es una esquina.

## 7. Lo que cambia para el taller

- **Mecanizado (anillos):** en la cara interior de cada anillo, el rebaje de
  chapa de 4.5 × 3 por el contorno de lo que se ve de las tres chapas (fundido
  con el bolsillo de la trasera bajo los dos labios), dos cajeados de brida de
  28 × 15.5 × 3, radios de 5.5 (no 4.5) en las esquinas con chapa, y el tramo
  trasero a 23 de franja; el reborde de 1 × 3 es la cota delicada. Todo con la
  fresa de Ø3 y los DXF a cota final, como hoy; las profundidades en el PLIEGO y
  en el **cupón** (§"El cupón" del PLIEGO), que gana el rebaje y su reborde.
- **Chapa:** el techo **sin ranuras**, labio de 20 y esquinas de brida a R2
  (blank **593.02** × 73.85, era 588.00 × 71.85; el 593.00 de la quinta versión
  redondeaba el bend deduction, y el pliego va a cota); talón y nariz con lo que entra a
  545.62, los pies a 540.32, la muesca de 2.65 en cada punta hasta la línea de
  doblez y su alivio de Ø2; el talón con el pie a 22.5 (blank 545.62 × 42.23),
  y la nariz con el pie a 20.5 (blank 545.62 × 50.20).
  Nada nuevo que plegar.
- **Acrílico:** la trasera igual (552.32 × 237.18), con la cara vista a 6.5 y
  el bolsillo en u = 5.5..16.5; la rejilla de entrada 2 mm más baja
  (7 065 mm²).
- **Juntas:** 12 tacos de EPDM de 4.0 × 15 (adhesivo), en vez de dos tiras de 2.5.
- **RFQ:** al mecanizado, el rebaje, los cajeados y **la pregunta del reborde**
  («¿un reborde de 1 × 3 a lo largo del contorno, con **+0.3 / −0**? si no,
  1.5» — la tolerancia es asimétrica desde la revisión del 30-08: ±0.1 aceptaba
  un 0.9 que la propia puerta rechaza); a la
  chapa, nada nuevo que preguntar.

## 8. Lo que este documento NO cierra

- **El gotero** (§3.5): con la primera pieza, y hacia fuera si entra. Y el
  **ensayo de derrame** que decide si hace falta: 100 ml de agua vertidos **a lo
  largo de toda la meseta**, de punta a punta, con el aparato encendido y
  horizontal, comprobando que el agua moje las dos juntas en **todos los vanos
  entre tacos**; se acepta si a los diez minutos ninguna superficie interior
  (la cara interior de la trasera, el suelo, el chasis) está mojada.

  **Y no se hace sin esto** (el revisor del 30-08 lo pidió, y tiene razón: el
  protocolo mandaba echar agua sobre un aparato encendido y no decía una
  palabra de cómo). El ensayo se monta así, y si algo de esto falta, no se
  hace:
  - **Alimentación por diferencial de 30 mA** dedicado, y **PE verificado
    antes** con medida de continuidad chasis-a-tierra **< 0.1 Ω** — es el
    mismo punto de bonding enmascarado del anodizado.
  - **Corriente de fuga medida antes de mojar** y de nuevo a los diez minutos:
    límite **0.5 mA**. Si sube de ahí en cualquier momento, se aborta.
  - **El operador no toca el aparato mojado.** El vertido se hace desde una
    jarra, con guante aislante, sin apoyar la otra mano en el chasis, y el
    interruptor de corte está fuera del alcance del agua.
  - **Criterio de aborto**, en el acto y desenergizando: cualquier gota en una
    superficie interior antes de los diez minutos, el diferencial saltando, la
    fuga pasando de 0.5 mA, o **cualquier cosa que huela, chisporrotee o
    cambie de sonido**.
  - **Si hay penetración**, el ensayo termina: se desenergiza, se seca **24 h**
    con la caja abierta, y **la fuente NO se vuelve a energizar** hasta
    revisarla módulo a módulo. Una placa que se secó no es una placa que está
    bien.
  - El resultado se anota pase o no pase, con la corriente de fuga de las dos
    medidas.
- **El ensayo térmico** con la primera unidad: C_D, altura efectiva y pérdidas
  no están medidos, y la puerta es de órdenes de magnitud. Protocolo: ambiente
  entre 20 y 25 °C medido; la fuente en **su peor caso, que es a media carga**
  (raíles ±12 V a I ≈ 0.50 A, el prerregulador en su máximo, y el LED del #104
  al tope), no a plena; **ΔT = T_aire a la salida de la rendija − T_ambiente**,
  medidos a la vez (es lo que la fórmula calcula, y lo que recalibra C_D); la
  pared del chasis del PSU se registra aparte; lectura cada 10 min hasta que
  dos seguidas no cambien más de 0.2 K; se acepta si ΔT ≤ 15 K (la puerta), y
  se anota contra los 12.2 K del papel.
- **La compresión de los tacos** (20 %) es un SUPUESTO sin puerta sobre el
  espesor real ni el alabeo de la plancha; el ensayo de derrame es lo que lo
  cubre.
- **La rendija de abajo** como entrada: no se cuenta.
- **Los vatios de la bahía**: ~4.2 W sin presupuesto en un recinto que el repo
  declara sellado; ~1.5 K por superficie, ESTIMADO. Es un presupuesto que falta,
  y no es de esta tanda.
- **El costado a 6 en el tramo trasero** (franja 25.5): decisión de mirada de
  Samuel; aquí 23 con el costado a 3.5.
- **La banda alta de la trasera** (75 mm bajo el labio a más de 10 MPa, spec
  29-08 §9): igual, 2 mm más corta.
- **La banda del valle, los paneles y la fila 1U**: tanda B, su spec.

## 9. Enmiendas que manda

| papel | qué |
|---|---|
| `2026-08-15-case-design.md` | rev. 27 en el historial; §5: techo macizo, chapas empotradas 1 en rebaje de 4.5 × 3 (los pies a ras), salida por el alero a 4.0, labio 20, 9.22 W, la tabla entra con el anillo B |
| `2026-08-29-trasera-capturada-talon-nariz-design.md` | §3.1: el bolsillo de la trasera a u = 5.5..16.5 con labio de 3 de hondo bajo los labios de chapa; §3.4: cara vista a 6.5; §3.5 y §9: la junta es a tacos de 4.0 y la rendija es la salida; §3.6: el montaje; §5: el techo B sin ranuras y el labio a 20; §7: `guarda_aire`, la pared a `guarda_tramo_trasero` |
| `2026-08-29-marco-ventana-banda-estructural-design.md` | §3.2: el retiro bajo las chapas 1.65 → 2.65 (salvo el suelo), la pata trasera a 30; §4: `guarda_aire` nunca leyó ranuras del DXF |
| `2026-08-27-case-esqueleto-visible-design.md` | «Lo que NO se toca: la ventilación» — superado: la salida cambió el 28-08 y aquí otra vez, con su puerta |
| `2026-08-28-costilla-pletina-design.md` | §4: el anillo lleva el rebaje de chapa, los cajeados de brida, radios 5.5 y el tramo trasero a 23; el cupón gana el reborde |
| `case/README.md` | piezas y BOM (techo sin ranuras, labio 20, blanks, muescas, tacos), térmico (9.22 W, 9.5/12.2 K, entrada 46 ranuras/7 065 mm² — hoy dice 44 y 6 781), **orden de ensamblaje** (pasos 4-7 → 4-5) |
| `case/PLIEGO.md` | rev. 27: anillo (rebaje, cajeados, radios, franja trasera 23, cupón), techo macizo, desarrollos con muesca y alivio, el talón con el pie a 22.5, juntas, esquinas de brida |
| `case/RFQ.md` | rev. 26: al mecanizado el rebaje, los cajeados y la pregunta del reborde; a la chapa el techo sin ranuras |
