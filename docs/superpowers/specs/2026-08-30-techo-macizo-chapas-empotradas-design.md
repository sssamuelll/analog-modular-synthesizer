# El techo macizo, con la salida de aire por el alero, y las tres chapas empotradas en el anillo

**Fecha:** 2026-08-30 · **Estado:** aprobado por Samuel en conversación («dale»)
sobre la propuesta de esta mañana, con sus cuatro números (chapa rehundida 1,
rebaje en las tres chapas; y para la tanda B, panel 1U de 55 y paneles 1.5
abajo); **corregido contra la crítica adversarial de codex** (Serrano, Halberg,
Rune) de la misma mañana: la ranura del rebaje a 3.5 (la fresa es Ø3), la
rendija a 3.0 y el labio del techo a 20 (capilaridad), el tramo trasero a 22,
las chapas a 545.62, el montaje escrito, y las puertas una por aserto ·
**Tanda A de dos**: la B (la fila 1U más alta con sus rieles, los paneles
empotrados y el apoyo de la banda del valle) tiene su propia spec ·
**Supersede** en el techo, en la unión chapa-anillo, en la junta de los labios
y en la ventilación a la spec del 29-08 (trasera capturada) y a la del 27-08
(esqueleto visible) en lo que dicen de eso.

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
en serie, C_D 0.65, 20 °C); la última columna repite la de 9.22 W con C_D 0.55,
que es la sensibilidad que la crítica pidió ver.

| escenario | salida (mm²) | tiro (mm) | 6.33 W | 9.22 W | 9.22 W, C_D 0.55 |
|---|---|---|---|---|---|
| hoy: meseta 852 + ondas 2 289 | 3 141 | 94 | 10.8 K | 13.9 K | 15.5 K |
| techo macizo, nada más | 2 289 | 51 | **15.9 K** | 20.4 K | — |
| techo macizo + rendija a 2.5, ocho tacos de 15 | 3 341 | 95 | 10.4 K | 13.3 K | 14.9 K |
| **techo macizo + rendija a 3.0, seis tacos de 15** | 3 641 | 103 | **9.6 K** | **12.4 K** | **13.8 K** |
| ídem, rendija a 3.5 | 3 866 | 108 | 9.2 K | 11.8 K | 13.2 K |

Se adopta la fila en negrita. La rendija del alero (§3.2) está más alta que el
centro de las ondas y aporta más área que la meseta que sustituye: el aparato
respira **mejor** que hoy en los tres supuestos, y con un C_D pesimista sigue
bajo 15 donde el diseño de hoy no.

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

- **`aire_labios` = 3.0** (subida capilar **4.95 mm**), que es también el grosor
  de los tacos (§3.3);
- **`techo_labio` = 20** (era 18): el labio baja a y = 230.18 y tapa **8.5** del
  canto; el margen capilar queda en **3.5 mm** con la luz nominal y en 2.5 con
  una luz local de 2.5. El techo gana sección (el labio de 18 ya era el mínimo
  por rigidez, §5 de la spec del 29-08), y lo que se ve de la trasera pierde 2.

Área: (540.62 − 6 × 15) × 3.0 = **1 352 mm²** a y ≈ 238.

Con la chapa rehundida 1 (§4) la cara interior del labio pasa de 1.5 a 2.5 del
plano trasero; para que la rendija mida 3.0 **la trasera retrocede**: su labio
de bolsillo pasa de 3 a **`rehundido_trasera` = `rehundido_chapa` + `t_costilla`
+ `aire_labios` − `t_junta_asiento` = 4.5** (cara vista a 5.5 del plano). Es un
valor **derivado**, no un parámetro: la única cota de la trasera que deja de
ser «la del costado, girada»; la junta de 1 y el hondo de 6 siguen iguales.

### 3.3 La junta a tacos, en los dos labios

La tira continua de 2.5 tras los labios (spec 29-08 §9, «con la primera pieza»)
se decide aquí: **tacos de EPDM de 3.0 × 15**, seis por labio (uno cada ~90 mm,
pegados a la cara interior del labio), en el labio del techo **y** en el del
talón. Una sola regla para las dos juntas; sujetan la plancha sin que suene,
fijan la luz (la plancha no puede pegarse al labio y cerrar la salida: el taco
es la luz) y dejan la rendija libre entre ellos. Solo la de arriba se cuenta
como salida. La de abajo (a y ≈ 6-19, bajo el labio del talón, mirando al suelo)
es una entrada que no se cuenta: si entra aire por ahí mejora el tiro y no
aparece en el número.

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

El techo se queda en 15 K y no pegado al número: 12.4 K deja 2.6 K, y 13.8 con
C_D 0.55 deja 1.2.

### 3.5 El gotero

Con la luz a 3.0 y el solape a 8.5 la cuenta capilar cierra sin él. Si la primera
pieza gotea hacia dentro, el remedio es un **dobladillo hacia FUERA** (180°, 3
mm) en el canto de los dos labios — hacia dentro estrangularía la rendija a 1.5
justo en la línea del canto y subiría la capilaridad a 9.8 —, y es visible: se
decide mirando (§8).

## 4. Las tres chapas empotradas en el anillo

### 4.1 El rebaje de chapa

En la cara interior de cada anillo, a lo largo del contorno **solo donde hay
chapa** (nariz: pie, chaflán y frente hasta P1; techo: del retorno de P4 por la
meseta, el chaflán de P5 y el labio hasta y = 230.18; talón: labio de y = 19 a 6,
chaflán y pie), un **rebaje de `rebaje_chapa` = 3 de fondo** (z, 2 t, desde la
cara interior: z = 11..14 contando desde la cara vista) y de u =
`rehundido_chapa` a u = `rehundido_trasera` (de **1 a 4.5**: 3.5 de ancho, la
fresa de Ø3 del pliego entra; a 2 de ancho no entraba). La chapa entra en él:

- su cara exterior queda a **`rehundido_chapa` = 1** por dentro del contorno del
  anillo, y su cara interior a 2.5; al suelo del rebaje le sobran 2: el suelo
  no posiciona, posicionan las bridas y los M4 de los pies;
- su canto queda **debajo del anillo** con `hol_chapa` = 0.5 a la pared del
  rebaje (no los 0.15 de `hol_piel`: una chapa cortada a ±0.3 tiene que entrar
  aunque venga larga, y aun larga queda 2.2 tapada): **las tres chapas miden
  546.62 − 2 × 0.5 = 545.62** entre paredes (el techo crece 5.0 sobre sus
  540.62, nariz y talón 5.3 sobre sus 540.32);
- el borde del anillo es un **reborde de 1 × 3** (u = 0..1, z = 11..14) que
  recorre el contorno donde hay chapa: es lo que se ve como marco, y lo que
  tapa el canto. Una pared de 1 con 3 de alto se fresa (3:1) pero es la cota más
  delicada de la pieza: va al RFQ como pregunta con respuesta ya diseñada — si
  el taller pide 1.5, `rehundido_chapa` = 1.5 y todo lo derivado se mueve solo
  (§6, puerta «reborde»).

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
la junta de sombra y no sobre una arista compartida.

El sólido de la chapa se dibuja igual que hoy (cubos y polígonos, sin arcos); lo
que cambia es que el anillo ya no pretende coincidir con un arco que el modelo
no tiene.

### 4.3 El tramo trasero: presupuesto de franja

En el tramo P5-P6 el anillo lleva, además, el bolsillo de la trasera (z = 8..14
desde la cara vista, cerrado de y = 1 a 239.18) y el del costado (z = 3..14, el
PMMA en 3..11). El rebaje de chapa se suma **solo en las alturas de los dos
labios** — y = 230.18..250.18 (techo) e y = 6..19 (talón) —; entre 19 y 230.18 no
hay chapa y el bolsillo de la trasera conserva su labio de 6 de hondo. De fuera
a dentro (u desde el plano trasero; z desde la cara vista, cara interior en 14):

| u | z = 11..14 (los 3 del rebaje) | z = 8..11 | z = 3..8 | z < 3 |
|---|---|---|---|---|
| 0..1 | **reborde** (donde hay labio de chapa) / labio del bolsillo (resto) | labio del bolsillo | macizo | macizo |
| 1..4.5 | rebaje de chapa (chapa en 1..2.5, aire 2.5..4.5) / labio del bolsillo | labio del bolsillo | macizo | macizo |
| 4.5..15.5 | **bolsillo de la trasera** (en las alturas de los labios, rebaje y bolsillo son un solo vaciado de u = 1 a 15.5) | bolsillo de la trasera | macizo | macizo |
| 15.5..18.5 | pared (`pared_rebaje_trasera` = 3) | pared | macizo | macizo |
| 18.5..22 | bolsillo del costado (entra 3.5) | ídem | ídem (el PMMA vive en z = 3..11) | labio del costado |

De la tabla salen tres cosas: en las alturas de los labios **el labio del
bolsillo de la trasera queda con 3 de hondo** (z = 8..11; en z = 11..14 lo
sustituyen el reborde y el propio labio de la chapa, que a 3.0 de aire y con los
tacos sigue parando la plancha hacia fuera); **la franja del tramo trasero pasa
de 20 a 22** (`cara_anillo_trasera`: 4.5 + 11 + 3 + 3.5) para que el costado
siga entrando al menos 3 con su pared de 3; y **no queda ninguna aleta**: el
suelo del rebaje es la pared exterior del bolsillo (u = 4.5) por construcción
(§3.2, derivado). La alternativa que la spec del 29-08 ya dejaba a Samuel — el
costado a 6 en los cuatro tramos — vale 24.5 aquí y se ve 4.5 más ancha desde
el lado; no se toma en esta tanda.

### 4.4 Las bridas del techo

El repo fija la brida **en la cara del anillo** (z = 14) y lo llama no
negociable porque a z ≥ t_anillo + t_placa está el barrido del panel de arriba.
Aquí la brida cambia de plano **en la dirección segura**: como el labio entra 3
en el rebaje, dobla en z = 11 y apoya en un **cajeado de 3 de fondo** en la cara
interior — queda de z = 11 a 12.5, **1.5 por debajo** de la cara, más lejos del
barrido, no más cerca. El cajeado mide la huella de la brida más 0.5 por lado
(28 × 15) con esquinas de R1.5 (la fresa), y **la brida lleva sus esquinas
redondeadas a R2** para asentar entera. Los dos M4 ciegos se roscan desde el
suelo del cajeado (quedan 11 de pletina; hoy 14). La muesca del marco de la
ventana sobre la huella se queda: las cabezas siguen asomando por encima de la
cara.

### 4.5 El marco de la ventana

Su canto exterior se retira bajo las chapas `t_costilla` + `hol_piel` = 1.65
hoy (`_retiro_marco_chapa`); pasa a **`rehundido_chapa` + `t_costilla` +
`hol_piel` = 2.65** en frente, suelo, meseta y cola bajo el retorno. En el tramo
trasero la pata del marco arranca 0.5 más allá de la pared del bolsillo de la
trasera (`_retiro_marco_trasera` = `t_anillo` + 0.5 = 14.5 hoy); con el bolsillo
en u = 4.5..15.5 arranca en **16**, 1.5 más adentro, y la pata de
`marco_fondo_trasera` = 28 pierde ese ancho: con 28 quedaría en unos 129 MPa
contra 130 (con 1 menos el modelo da 119; con 1.5 menos, la cuenta del plan).
**Pasa a 30** — 1.5 que se pierden y 0.5 de margen —, y `guarda_marco_ventana()`
lo comprueba con la cuenta, no con la estimación.

### 4.6 Nariz y talón

Mismo rebaje, mismo reborde, mismos radios: sus pies siguen atornillados a la
tabla con sus M4 (nada cambia en la tabla), y sus chaflanes y frentes entran en
el rebaje por los dos lados. Sin bridas: no hay cajeados nuevos por ellas. El
chaflán de la arista de abajo-fuera de la trasera (5.5) se recalcula con la
plancha 1.5 más adentro y el labio del bolsillo a 4.5 (`chaflan_trasera_bajo()`
y su gemela): es una cuenta, no una decisión.

## 5. Montaje

Las tres chapas quedan capturadas por los rebajes de los dos anillos y miden más
que el vano entre caras: **entran con el anillo B, como la trasera y los
costados**, y el orden del README cambia en dos pasos:

4. (como hoy, más) **la nariz y el talón de pie en el rebaje del anillo A**, en
   sus tramos, y **el techo con su brida A ya roscada** a los dos M4 ciegos del
   cajeado de A (con el anillo A tumbado el interior está abierto); la trasera en
   su bolsillo; el marco B en las puntas de los rieles; el costado B en el
   anillo B. **El anillo B baja** sobre cinco puntas a la vez — marco B, trasera,
   techo, nariz, talón —, todas en z, como hoy baja sobre dos. Los doce M4 del
   marco B y los dos de la brida B, desde dentro por el frente abierto.
5. (era 6-7) **La tabla, sola en el banco, con el chasis del PSU** (sus 4 M4
   desde debajo); nariz y talón ya no vienen con ella: **el case boca abajo, la
   tabla encima**, sus M5 a los cantos de los anillos como hoy, y **los 3 + 3 M4
   de los pies de la nariz y del talón se roscan a la tabla desde dentro, por el
   frente abierto** (los del talón a 300 mm, con prolongador). Es el costo real
   de empotrar: seis tornillos que se apretaban en el banco se aprietan en el
   case.

Lo demás (rieles, marco A, tapa del valle, electricidad, paticas, paneles, el
film al final) no cambia. Los tacos de EPDM van pegados a los labios antes del
paso 4.

## 6. Puertas (la puerta primero, ROJA; el modelo; VERDE; romperla)

Una puerta por cosa y una mutación por aserto, que salte por SU texto
(`canario_techo()` lo comprueba como `canario_trasera()`). Los valores derivados
(`rehundido_trasera`, `radio_borde`, los anchos) no son parámetros: son funciones
gemelas en el `.scad` y el budget, y `check_dxf` las cruza contra el DXF.

| puerta | asevera | mutación que la pone roja (y solo a ella) |
|---|---|---|
| `guarda_aire()` (reescrita) | salida = rendija (`(ancho_util − n·largo_taco) × aire_labios`) + ondas; `potencia_disipada` = 9.22; ΔT ≤ 15; imprime ΔT con C_D 0.55 como aviso | `taco_largo` = 90 (tira continua: 20.4 K); `potencia_disipada` = 12 (16.7 K) |
| **nueva** `guarda_rendija()` | subida capilar 2γ/(ρ g `aire_labios`) ≤ solape del labio − 2; el solape = `techo_labio` + `chaflan_nariz` − (P5.y − y1) ≥ 6; los tacos miden `aire_labios` (la plancha no toca el labio) | `techo_labio` = 17 (solape 5.5: 4.95 > 3.5); `aire_labios` = 1.5 (9.8 > 6.5) |
| **nueva** `guarda_rebaje_chapa()` | `rebaje_chapa` ≥ 2 t; ancho (`rehundido_trasera` − `rehundido_chapa`) ≥ `fresa_d`; `rehundido_chapa` ≥ 1; las tres chapas = luz − 2·`hol_chapa` con `hol_chapa` ≥ 0.3; `radio_borde` = `radio_chapa` + `rehundido_chapa` | `rebaje_chapa` = 2 («menos de 2 t»); `rehundido_chapa` = 2.5 (ancho 2 < 3, «la fresa no entra»); `rehundido_chapa` = 0.5 («reborde más fino que 1») |
| **nueva** `guarda_tramo_trasero()` | la tabla de §4.3: labio del bolsillo ≥ 3 de hondo bajo el rebaje; pared ≥ `pared_rebaje_trasera`; el costado entra ≥ 3; `cara_anillo_trasera` = 4.5 + 11 + pared + entrada del costado; rebaje y bolsillo comparten pared (sin aleta) | `cara_anillo_trasera` = 21 («el costado entra 2.5»); `pared_rebaje_trasera` = 2 |
| `guarda_trasera_capturada()` | `aire_labios` = 3.0 con u0 = 4.5 (derivado); el chaflán de la plancha recalculado; y1 y el bolsillo como hoy | `t_junta_asiento` = 2 (aire 2.0 < 3.0: «la junta se come la rendija») |
| `guarda_miembro_alto()` | como hoy (200 N sola; ahora con el labio de 20) con la brida en su cajeado: roscas desde z = 11 con ≥ 8 de pletina; cajeado = huella + 0.5 por lado; esquinas R2 en la brida ≥ R1.5 del cajeado | `rebaje_chapa` = 7 («quedan 7 de pletina bajo la brida») |
| `guarda_marco_ventana()` | la pata trasera a 30 con el retiro en 16 | `marco_fondo_trasera` = 28 (la cuenta, no la estimación) |
| `check_dxf.techo_macizo()` (nueva) | `miembro_alto_2d.dxf`: ningún contorno cerrado dentro del blank salvo los cuatro M4 de las bridas; esquinas de brida a R2 | un DXF con una ranura |
| `check_dxf.anillo_dorso_tiene_rebaje()` (nueva) | en `costilla_dorso_2d.dxf` (la cara mecanizada, no `costilla_2d`): el rebaje de 1..4.5 por el contorno de las chapas, fundido con el bolsillo de la trasera en las alturas de los labios, y los dos cajeados de brida de 28 × 15; **las profundidades no se leen de una planta**: van al PLIEGO y al cupón (§7) | — |
| `check_dxf.anillo_tiene_ventana()` (reescrita) | la cara mide `cara_anillo` en seis tramos y `cara_anillo_trasera` en el trasero (hoy exige 20 uniforme y pondría rojo el anillo correcto) | `cara_anillo_trasera` = 20 en params con el DXF a 22 |
| `check_dxf` sobres y radios | los tres desarrollos a 545.62 (+ lo suyo por brida); `costilla_2d` con radios de 5.5 donde hay chapa y 4.5 donde no | — |

Renders: las dos vistas de siempre y **los dos primeros planos de la esquina de
arriba-atrás** (tres cuartos y perfil, los del 30-08 en `build/`) pasan a ser
renders del repo, porque lo que se juzga aquí es una esquina.

## 7. Lo que cambia para el taller

- **Mecanizado (anillos):** en la cara interior de cada anillo, el rebaje de
  chapa de 3.5 × 3 por el contorno de las tres chapas (fundido con el bolsillo
  de la trasera en las alturas de los labios), dos cajeados de brida de 28 × 15
  × 3, radios de 5.5 (no 4.5) en las esquinas con chapa, y el tramo trasero a 22
  de franja; el reborde de 1 × 3 es la cota delicada. Todo con la fresa de Ø3 y
  los DXF a cota final, como hoy; las profundidades en el PLIEGO y en el
  **cupón** (§"El cupón" del PLIEGO), que gana el rebaje y su reborde.
- **Chapa:** el techo **sin ranuras**, labio de 20 y esquinas de brida a R2
  (blank 593.00 × 73.85, era 588.00 × 71.85); talón 545.62 × 39.73; nariz 5.3 más
  ancha. Nada nuevo que plegar.
- **Acrílico:** la trasera igual (552.32 × 237.18), con el chaflán de abajo
  recalculado.
- **Juntas:** 12 tacos de EPDM de 3.0 × 15 (adhesivo), en vez de dos tiras de 2.5.
- **RFQ:** al mecanizado, el rebaje, los cajeados y **la pregunta del reborde**
  («¿un reborde de 1 × 3 a lo largo del contorno, a ±0.1? si no, 1.5»); a la
  chapa, nada nuevo que preguntar.

## 8. Lo que este documento NO cierra

- **El gotero** (§3.5): con la primera pieza, y hacia fuera si entra.
- **La rendija de abajo** como entrada: no se cuenta.
- **Los vatios de la bahía**: ~4.2 W sin presupuesto en un recinto que el repo
  declara sellado; ~1.5 K por superficie, ESTIMADO. Es un presupuesto que falta,
  y no es de esta tanda.
- **El costado a 6 en el tramo trasero** (franja 24.5): decisión de mirada de
  Samuel; aquí 22 con el costado a 3.5.
- **La banda alta de la trasera** (75 mm bajo el labio a más de 10 MPa, spec
  29-08 §9): igual, 2 mm más corta.
- **La banda del valle, los paneles y la fila 1U**: tanda B, su spec.

## 9. Enmiendas que manda

| papel | qué |
|---|---|
| `2026-08-15-case-design.md` | rev. 27 en el historial; §5: techo macizo, chapas empotradas 1 en rebaje de 3.5 × 3, salida por el alero a 3.0, labio 20, 9.22 W, montaje |
| `2026-08-29-trasera-capturada-talon-nariz-design.md` | §3.1: el bolsillo de la trasera a u = 4.5..15.5 con labio de 3 de hondo bajo los labios de chapa; §3.4: cara vista a 5.5; §3.5 y §9: la junta es a tacos de 3.0 y la rendija es la salida; §3.6: el montaje; §5: el techo B sin ranuras y el labio a 20; §7: `guarda_aire` |
| `2026-08-29-marco-ventana-banda-estructural-design.md` | §3.2: el retiro bajo las chapas 1.65 → 2.65, la pata trasera a 30; §4: `guarda_aire` nunca leyó ranuras del DXF |
| `2026-08-27-case-esqueleto-visible-design.md` | «Lo que NO se toca: la ventilación» — superado: la salida cambió el 28-08 y aquí otra vez, con su puerta |
| `2026-08-28-costilla-pletina-design.md` | §4: el anillo lleva el rebaje de chapa, los cajeados de brida, radios 5.5 y el tramo trasero a 22; el cupón gana el reborde |
| `case/README.md` | piezas y BOM (techo sin ranuras, labio 20, blanks, tacos), térmico (9.22 W, 9.6/12.4 K, entrada 46 ranuras/7 193 mm² — hoy dice 44 y 6 781), **orden de ensamblaje** (pasos 4-7) |
| `case/PLIEGO.md` | rev. 27: anillo (rebaje, cajeados, radios, franja trasera 22, cupón), techo macizo, desarrollos, juntas, esquinas de brida |
| `case/RFQ.md` | rev. 26: al mecanizado el rebaje, los cajeados y la pregunta del reborde; a la chapa el techo sin ranuras |
