# La trasera capturada como las mejillas, y el talón como la nariz

**Fecha:** 2026-08-29 (noche, 2) · **Estado:** aprobado por Samuel en conversación
(«Dale con todo») sobre la propuesta de esta misma noche; **implementado** en la
rama `feat/case-trasera-capturada` con sus puertas, y corregido contra lo que las
puertas, el render y el revisor del PR obligaron (§3.5: sin canal; §5: el labio
del techo a 18; §7: la pata trasera del marco a 28; §3.1 y §3.6: el bolsillo
cerrado por los dos extremos y la trasera entra con el anillo B — la primera
versión lo sacaba por arriba, la segunda por abajo, y por abajo la plancha no
pasaba por la boca del chaflán; §4.3 y §7: cuatro pestañas que son estructura y
la trasera como placa) · **Supersede en la trasera y el talón**
a `2026-08-29-marco-ventana-banda-estructural-design.md` §4 (la banda es el
miembro), que se queda en lo demás · **Enmienda** a `2026-08-15-case-design.md`
(rev. 26), a `2026-08-29-nariz-recta-valle-limpio-design.md` §2.3 y a
`2026-08-28-costilla-pletina-design.md` §4.

## 1. De dónde sale

Samuel, mirando el render de la noche: *«no me gusta el talón! preferiría que la
relación del acrílico con el acero en la parte de atrás fuera igual que en las
mejillas (la forma en que se unen), y el talón preferiría que tuviera el mismo
estilo y acabado que la nariz»*.

Son dos cosas y las dos se miden contra piezas que ya existen:

- **Cómo se une el acrílico al metal en las mejillas** (`params.scad`: `cara_anillo`
  20, `rebaje_anillo` 6, `rehundido_acrilico` 3, `t_junta_asiento` 1): la plancha va
  DENTRO de un rebaje del anillo, rehundida 3 tras un labio de 3, con 6 mm de
  acrílico metidos en el bolsillo sobre una junta de EPDM de 1, retenida hacia
  fuera por el labio y hacia dentro por el marco de la ventana. **Ni un taladro.**
  La trasera de esta tarde hace lo contrario: diez M3 a la vista sobre dos bandas
  planas de 24, y sus cantos laterales muriendo contra la cara interior del anillo
  con 0.15 de aire, sin nada que los tape.
- **Cómo es la nariz** (`2026-08-29-nariz-recta-valle-limpio-design.md` §2.2): la
  esquina del anillo cortada a 45° (`chaflan_nariz` 6), y una chapa de 1.5 que la
  envuelve — pie de 18 sobre la tabla, chaflán, frente vertical de 13 — atornillada
  por el pie desde dentro. Nada visto. El talón de esta tarde es una banda plana de
  24 doblada a 90° sobre una esquina de radio 4.5, con cinco cabezas encima.

## 2. La cuenta

| | esta tarde (#241) | ahora |
|---|---|---|
| taladros en la trasera | 10 + 2 muescas | **0** |
| cabezas vistas atrás | 10 (sobre metal) | **0** |
| ancho de la trasera | 540.32 (entre anillos) | **552.32** (sus puntas dentro de los anillos) |
| bolsillos fresados en el anillo | 1 (el del costado) | **2** (el del costado + el de la trasera, en el tramo trasero) |
| esquinas del anillo a chaflán 6 | 1 (P0) | **2 (P0, P6)** o **3 (+ P5)** según la variante del techo |
| tornillos del case | 68 | **58** (−10 M3 de la trasera; el resto igual) |
| roscas ciegas por anillo | 14 | 14 (las mismas) |
| la tapa de arriba abre | 180° | **180°** (no hay canal: §3.5) |

Lo que no cambia de pieza: anillos (cambian de mecanizado), marco de la ventana
(cambia su pata trasera), nariz, tabla (cambian tres taladros), chasis (se corre 2.5
hacia delante), tapa del valle, rieles.

## 3. La trasera se captura como las mejillas

### 3.1 El bolsillo del tramo trasero

En la cara interior de cada anillo, a lo largo del tramo trasero (P5 → P6), se fresa
un **bolsillo de 11 × 6**: 11 hacia dentro desde `u = 3` (u = distancia al plano
trasero), 6 de hondo desde la cara interior (z = 8 … 14). **Cerrado por los dos
extremos**: arranca 0.5 bajo el canto de abajo de la trasera (y = 1.0; la plancha
apoya en el pie del talón, no en el bolsillo) y se cierra 0.5 sobre su canto de
arriba (y = P5.y − 17), 1.0 por debajo de la brida del techo. La primera versión
de este papel lo sacaba por el canto de arriba, y el render lo cantó: un agujero
de 11 × 6 a la vista en el canto superior de cada anillo, al lado del techo — el
techo va ENTRE los anillos, no encima, y no lo tapa nada. La segunda lo sacaba
por el canto de abajo, que tapa la tabla, y el revisor del PR lo cazó con un
booleano: bajo el chaflán la boca mide 8 y la plancha 8 + tolerancia, así que
por ahí no pasa. Cerrado por los dos lados, la plancha entra como los costados
(§3.6) y no hay camino que medir. Bajo la coronación de la pared de u = 3 sobre
el chaflán de P6 (y < 3.5) el bolsillo arranca en `u = 5.5` — un escalón — para no
morder la cara del chaflán; la esquina de abajo-fuera de la plancha va a chaflán y
lo libra (§3.4). Son **los mismos tres números del bolsillo del costado,
girados**:

| | costado (ventana) | trasera (tramo trasero) |
|---|---|---|
| labio que retiene hacia fuera | `rehundido_acrilico` = 3, en la cara vista | **3** (u = 0 … 3), en el canto trasero |
| acrílico dentro del metal | `rebaje_anillo` = 6 | **6** (z = 8 … 14) |
| ancho del bolsillo | `t_anillo − rehundido` = 11 (z) | **11** (u = 3 … 14) |
| junta | EPDM de 1 entre labio y plancha | **EPDM de 1** entre labio y plancha |
| cara vista del acrílico | rehundida 4 (3 + 1) | **rehundida 4** del plano trasero |

Todo derivado de los parámetros que ya existen; no entra ninguna cota nueva para el
bolsillo. La trasera de 8 (+1.2 del lote) más la junta de 1 dejan 0.8 de sobra en
los 11, como en el costado. Su cara interior queda en u = 12 (13.2 con la plancha
gruesa), y la **pared de fondo del bolsillo, en u = 14, es su tope hacia dentro**: a
2.0 de la cara nominal, más que los tol + 0.5 = 1.7 de la regla del postmortem.

Visto desde atrás: el canto del anillo (14 de ancho), la línea de la junta, y el
acrílico 4 mm más adentro arrancando exactamente en la línea de la cara interior del
anillo. Es la lectura de un costado, con el canto de 14 en vez de la cara de 20.

### 3.2 La pared con el bolsillo del costado

Aquí estaba la trampa, y hay que dejarla escrita. El tramo trasero del anillo mide
20 de franja (`cara_anillo`). El bolsillo del costado ocupa u = 14 … 20 (los 6 de
`rebaje_anillo`) por z = 3 … 14, y el de la trasera u = 3 … 14 por z = 8 … 14: **se
tocan en u = 14 sin pared**. Los dos bolsillos serían uno en L, y el tope hacia
dentro de la trasera sería el canto del costado — acrílico contra acrílico.

La salida: **en el tramo trasero, y solo ahí, el costado entra 3 en vez de 6**. El
contorno del rebaje (`costilla_dorso_2d`) corre a 17 de la silueta en ese tramo en
vez de a 14, el canto trasero del costado (`costado_2d`) a 17.15 en vez de a 14.15,
y entre los dos bolsillos queda una **pared de 3** (`pared_rebaje_trasera`, u = 14 …
17) de toda la altura. Nadie lo ve: ese canto del costado vive detrás del labio de 3
de la cara vista, y el marco de la ventana lo sigue pisando por dentro (su pata
trasera va de u = 14.5 a 26: 8.85 sobre el acrílico, más que los 6 de antes). Su
posición en el plano la fijan los otros tres cantos, que siguen con 6.

Lo que queda del tramo trasero, en sección (u de fuera a dentro, z de la cara vista
a la interior): u 0 … 3 macizo en los 14 (el labio de la trasera y el canto); u 3 … 14
solo en z 0 … 8 (encima, el bolsillo de la trasera); u 14 … 17 macizo (la pared); u
17 … 20 solo en z 0 … 3 (el labio del costado); de 20 en adelante, la ventana.

### 3.3 Lo que se le pide al anillo

- Las **roscas de la brida del techo** se quedan donde estaban (9.75 y 20.25 del
  doblez, `brida_largo` 27): el bolsillo se cierra en y = P5.y − 17, **8.5 por
  debajo** de ellas, y `guarda_miembro_alto()` exige ≥ 1.5 D de broca y 1.0 de
  cara entera entre el canto de la brida y el fin del bolsillo. (Con el bolsillo
  saliendo por arriba pasaba por debajo de la brida y la obligaba a 34: se probó
  y se deshizo.)
- Las **esquinas traseras**: P6 a chaflán 6 × 45° como P0 (§4); P5, según la
  variante del techo (§5).
- El bolsillo está **cerrado por los dos extremos**: la trasera entra al montar
  el segundo anillo (§3.6), y en el anillo no se ve nada por ningún canto.

### 3.4 La trasera

Una plancha de 8 de **552.32 × 238.18**, la misma en las dos variantes, sin un
taladro ni una muesca pasante. Sus puntas entran 5.85 en los bolsillos (6 menos
`hol_piel`); su canto de abajo apoya en el pie del talón (y = 1.5), 0.5 sobre el
fin de abajo del bolsillo; su canto de arriba muere **0.5 bajo el fin del
bolsillo** (y = P5.y − 17.5), que a su vez queda 1.0 bajo la brida del techo: la
brida se tumba en la cara del anillo de `t_costilla + brida_ancho` por debajo del
canto de arriba, y una plancha que subiera más necesitaría las muescas de esquina
de #241. Lleva un **chaflán de 4 × 45° en su arista de abajo-fuera**, por todo el
largo: lo que hace falta para que su esquina libre con 0.5 el escalón del bolsillo
bajo el chaflán del anillo (§3.1) — `chaflan_trasera_bajo()`, gemela en el
budget. No sale en el DXF (una arista no es un contorno): va en el pliego, como el
diamantado. Invisible: detrás del labio del talón. Conserva
la rejilla de entrada, las dos ondas, la ventana del IEC y KONDOR, ahora anclados a
**su campo visible** — de la coronación del labio de abajo (y = 19) a la del labio
de arriba (P5.y − 24 en las dos variantes) — en vez de a las dos filas de M3 que ya
no existen. La rejilla arranca a un puente (6.5) del labio; las ondas apenas se
mueven; KONDOR baja 7.

### 3.5 Arriba y abajo: labio por fuera, y por qué no hay canal

A los lados la retiene el anillo en las dos direcciones (§3.1: el labio hacia
fuera, la pared del bolsillo hacia dentro). Arriba y abajo:

- **Hacia fuera**, el labio de cada chapa (el del talón, §4; el del techo, §5), que
  vive en el plano trasero (u = 0 … 1.5) y tapa el canto — 17.5 abajo, 7.5 arriba;
  el bolsillo tapa 6. Entre la cara interior del labio y la cara del acrílico
  quedan **2.5** (4 − 1.5): los llena una **tira de EPDM de 2.5** pegada a la cara
  interior de cada labio, la misma junta que en el bolsillo pero del grueso que
  toca. No es junta de sombra: no se ve, porque el labio la tapa.
- **Hacia dentro, abajo**, dos **pestañas** lanzadas del pie del talón (§4.3), a 3
  de la cara interior del acrílico.
- **Hacia dentro, arriba, nada** — y va explicado, porque la primera versión de
  este papel llevaba un canal (tira + retorno de 10 detrás del canto de arriba).
  **En una sola chapa el labio no puede tapar el canto del acrílico y tener un
  retorno detrás**: para que el retorno cuelgue de una tira, la tira tiene que
  doblar del canto de abajo del labio, y entonces el labio queda ENCIMA del canto
  de la plancha, no delante — es exactamente lo que la rev. 22 perdió al fundir la
  meseta en el miembro alto. Y no hace falta: el bolsillo ya sujeta la plancha en
  las dos direcciones por los lados, así que una plancha empujada desde fuera no
  se va a ningún sitio, se comba (unos milímetros en el centro con 200 N, en
  8 mm de PMMA sobre 540 de luz) y vuelve; hacia fuera la para el labio. El
  canal costaba dos dobleces y grados de la tapa de arriba (la de la rev. 22, con
  su retorno de 24, la dejaba en 121.5°); sin él, **la tapa sigue abriendo 180°**.

### 3.6 Montaje y servicio

**Entra con el anillo B, como los costados.** Con el anillo A de pie y los rieles
en su marco, la trasera se mete de lado: una punta en el bolsillo del anillo A,
sobre la junta de EPDM, apoyada en el fin de abajo del bolsillo; después el anillo
B baja sobre el marco B y sobre la otra punta. Las tres planchas del case se
montan una vez, con el case, y la trasera no sale sin quitar un anillo (doce M4
del marco, dos de la brida del techo, tres M5 de la tabla). La primera versión de
este papel la metía por arriba con el techo quitado, y era la salida del bolsillo
por el canto de arriba la que se veía; la segunda, por abajo con la tabla fuera,
y por abajo no pasaba (§3.1). El precio es el mismo que el de los costados — y la
trasera no lleva electrónica (la pieza fija del IEC va a la tabla, #130), así que
no es pieza de servicio. Cuando la tabla entra, el pie del talón la levanta 0.5
del fin del bolsillo y la deja apoyada en chapa.

Las bridas del techo no estorban: el bolsillo se cierra 8.5 por debajo de sus
roscas y 1.0 por debajo del canto de la brida, y la plancha nunca llega a su
altura; las muescas de esquina de #241 mueren.

## 4. El talón es la nariz de atrás

### 4.1 La esquina

**P6 pasa de radio 4.5 a chaflán 6 × 45°**, el mismo `chaflan_nariz` de P0. Es la
esquina de la referencia de Samuel, y ahora está en las dos puntas de abajo.
`RADIOS_PERFIL[6]` muere; el chaflán vive en el contorno (`pts_contorno()`) como el
de delante, y `anillo_tiene_chaflan()` lo relee del DXF en las dos esquinas.

### 4.2 El perfil

La nariz en espejo, del pie hacia arriba: **pie de 20** sobre la tabla (u = 6 … 26),
**chaflán** de (u 6, y 0) a (u 0, y 6), **labio vertical de 13** a ras del plano
trasero (y = 6 … 19). Dos dobleces a 45°, chapa 6082-T6 de 1.5, desarrollo
**540.32 × 39.73** (`talon_labio` + c·√2 + `talon_pie` − 2·BD45). El labio mide lo
que el frente de la nariz (`alto_frontal − chaflan_nariz` = 13): nariz y talón
cierran igual, chaflán de 6 y 13 de plomo (el techo, en la variante B, lleva el
mismo chaflán y un labio de 18: §5).

Cubre el canto de abajo de la trasera con 17.5 (chaflán + labio − el pie) — más que
los 6 del bolsillo — y el chaflán le pasa por debajo: en la cara del acrílico
(u = 4) la cara interior del chaflán está a y = −0.12, bajo el apoyo (y = 1.5). Ni
se tocan.

Va entre los anillos con `hol_piel` a cada lado, como la nariz; sus puntas mueren
contra la cara interior del anillo, que ahí lleva el chaflán: chapa y anillo
comparten esquina, como delante.

### 4.3 El pie: tres M4 y cuatro pestañas

**Tres M4 avellanados desde dentro a la tabla** en u = 19.25 (1.5 D del canto libre
del pie), en las mismas z que los de la nariz. La boca del avellanado (Ø8.96) llega a
u = 14.77: **2.77 del canto interior de la trasera**, más que los 1.7 de la regla —
es lo que pone el pie en 20 y no en 18 como la nariz. Y la regla de chapa contra el
doblez del chaflán: 13.25 desde su línea, contra 9.75.

**Cuatro pestañas** lanzadas del pie — cortadas por tres lados y dobladas 90° hacia
arriba (r = 1.5, `radio_doblez_pestana`) — a z = 1/8, 3/8, 5/8 y 7/8 del hueco entre
anillos (`talon_pestana_n`), de 20 de ancho y 8 de alto, con su cara hacia la
trasera en **u = 15**: 3.0 del canto interior del acrílico. Son su tope hacia dentro
en el canto de abajo, **y son estructura**: la trasera sola en sus dos bolsillos es
una placa apoyada en dos cantos, y con `carga_mano` al centro cede 20 mm y trabaja
a 14 MPa en el contacto, sobre el techo de 10 del PMMA; con el canto de abajo
sujeto por las pestañas, 5 mm y 8 MPa (§7, `guarda_trasera_flexion()`). Dos
pestañas a 3/8 y 5/8 aguantan el centro igual que cuatro (las dos del medio se
llevan 74 N cada una); las cuatro son por el empujón bajo y descentrado — 200 N a
1/8 del ancho, junto al pie: 12 MPa con dos, 3 con cuatro. Entre el doblez del
chaflán y el de la pestaña quedan 4.1 de plano (dos tangentes a 7.9 y 12 del plano
trasero); se exigen 2 t, y a la pestaña se le exige subir al menos lo que el
bolsillo embebe (8 ≥ 6), ser más ancha que alta y doblar a ≥ 1 t. Los M4 quedan a
67 mm en z de la pestaña más cercana. Cada pestaña deja en el pie una ventana de
20 × 6.85 (su desarrollo), escondida bajo la trasera.

Por qué no bridas a los anillos, que era lo primero que salía: la brida del talón
apoyaría en la cara del anillo justo en la esquina de abajo-atrás, donde vive la
pata del suelo del marco, y el marco tendría que llevar ahí una muesca como la de
arriba. Con muesca en las dos esquinas, la pata trasera del marco — que no puede
llevar tornillo — queda apoyada-apoyada y cede 3.8 mm con `carga_mano`; el acrílico
se sale del rebaje con 3. Y por qué no un canal doblado del propio pie: con la
trasera a 12 del plano trasero el retorno cae a u = 14 y el pie entre el chaflán y
el retorno mide 8, sin sitio para un M4 fuera de dos zonas de doblez.

## 5. El techo por detrás: dos variantes, se escoge mirando

El miembro alto sigue siendo el techo del pico al canto, con su retorno de 4 en el
pico y sus dos bridas a los anillos. Lo que cambia es cómo baja por detrás y que
lleva canal (§3.5). Las dos variantes se renderean y Samuel escoge; el modelo las
lleva bajo un parámetro (`remate_trasero_chaflan`, 0/1) y las puertas corren sobre
las dos.

- **A — la banda de 24.** P5 con radio 4.5, la meseta dobla 90° y baja 24 a ras del
  plano trasero (la banda de #241). Las bridas doblan del extremo de la banda, como
  hoy. Desarrollo 540.62 + 2 × 30.7 × 74.4.
- **B — el chaflán, recomendada.** P5 pasa también a chaflán 6: la meseta acaba en u
  = 6, dobla 45° (el chaflán) y otra vez 45° a un labio vertical de **18**
  (`techo_labio`, y = P5.y − 6 … −24). Las bridas doblan del extremo del labio;
  como suben hasta P5.y − 1.5 (su M4 tiene que quedar a 8.5 del canto de arriba),
  sus 4.5 de arriba corren junto a la tira del chaflán y llevan un **relieve** (un
  corte en la línea de doblez) para no arrastrarla. Desarrollo 540.62 + 2 × 30.7 ×
  75.9.

  **Por qué 18 y no los 13 del talón:** la trasera ya no se atornilla al techo, así
  que el techo tiene que aguantar SOLO la mano de `carga_mano` en el centro de la
  meseta (la puerta de siempre, que puso la banda en 24). Con chaflán 6 + labio 13
  la sección trabaja a **176 MPa** contra los 130 de `RP02_ALUMINIO`; con 18 la
  caída total es 24, la misma que la banda, y da **111 MPa** (cede 2.04 mm). Si
  Samuel quiere el labio a 13 como el del talón, el camino no es bajar el número:
  es obligar 6082-T6 en el pliego (Rp0.2 240) y decirlo aquí.

  Con B, atrás se lee un marco de dos labios con chaflán de 6 arriba y abajo — 18
  el de arriba, 13 el de abajo —, los cantos de los anillos a los lados, y el
  acrílico 4 mm adentro. Delante, la nariz es exactamente el labio de abajo.
  Cuesta un doblez más en el techo (dos a 45° en vez de uno a 90°).

En las dos variantes la trasera es la misma plancha (su canto de arriba lo fija la
brida, §3.4) y el campo visible es el mismo (P5.y − 24 arriba).

## 6. Lo que se ve

Desde atrás: metal a ras por los cuatro lados (dos cantos de anillo de 14, dos
labios de chapa), y la trasera dentro, rehundida 4, sin una cabeza. Las esquinas de
abajo a chaflán en las dos puntas del case; en B, también las de arriba-atrás.

Desde dentro: cuatro pestañas de 8 detrás del canto de abajo de la trasera; tres
cabezas avellanadas a ras en el pie del talón, bajo la trasera. Los diez M3 con
tuerca y arandela de nylon que se veían a través del acrílico, fuera.

## 7. Puertas

| puerta | qué hace |
|---|---|
| **muere** `guarda_trasera_dentro`, `guarda_agarre` (mordida de los M3 en las bandas), `_anclajes_miembro`, `_muesca_trasera` y las tres cajas de la trasera con muescas; `MIEMBROS_DXF` (las filas de M3 de las bandas) | |
| **nueva** `guarda_trasera_capturada()` (budget) | §3.1: el bolsillo fresado con los tres números del costado (labio = `rehundido_acrilico`, hondo = `rebaje_anillo`, ancho = `t_anillo − rehundido`) y sitio para plancha + tolerancia + junta + 0.5; cerrado por los dos extremos con 0.5 a cada canto de la trasera, el escalón bajo el chaflán sin morderlo y el chaflán de la arista de la plancha librándolo con 0.5 (y dejando ≥ 2 de canto plano); `hol_piel` y junta > 0; §3.2: la pared entre bolsillos ≥ 3 y el costado entrando ≥ 3 en el tramo trasero; las puntas de la trasera ≥ 5 dentro; nada fijo a menos de tol + 0.5 de su cara interior (la pared del bolsillo, la pata del marco, las pestañas); el canto de arriba con ≥ 0.5 bajo lo que el techo tiene encima (el chaflán en B, el doblez de la banda en A) y bajo la brida; el de abajo sobre el pie; los labios tapan ≥ 6 arriba y abajo; cero filas; la junta de los labios publicada |
| **reescrita** `guarda_talon()` (budget) | §4: P6 a chaflán; perfil de la nariz en espejo (labio = `alto_frontal − chaflan_nariz`, pie a ≤ 2 del de la nariz); el chaflán por debajo de la esquina del acrílico; los tres M4 fuera del doblez del chaflán, a 1.5 D del canto libre, y su boca a ≥ tol + 0.5 de la trasera; las pestañas a ≥ tol + 0.5, con ≥ 2 t de plano entre las tangentes de los dos dobleces, su ventana a ≥ 2 t del canto libre, y a ≥ 1.5 D + medio ancho de cada M4; el labio tapa ≥ 6 |
| **reescrita** `guarda_miembro_alto()` (budget) | §5: la sección real (meseta + chaflán y labio, o banda) SOLA bajo `carga_mano`, ≤ RP02 — es lo que puso el labio del techo en 18 —; la brida cabe bajo la meseta, sus M4 a ≥ 2 D entre sí y a ≥ 1.5 D de broca por encima del fin del bolsillo de la trasera; en B, el relieve de la brida publicado |
| **cambia** `guarda_marco_ventana()` | `retiro_marco_trasera` = `t_anillo` + 0.5 (14.5). Con `marco_fondo` = 26 la pata trasera se quedaba en 11.5 y a **129 MPa contra 130** (cede 1.77): pasa por un pelo, y eso no es pasar. Entra `marco_fondo_trasera` = **28**: la pata trasera pisa 8 de acrílico en vez de 6 — el tramo trasero ya es la excepción — y queda en 13.5, 1.50 mm y 110 MPa |
| **cambia** `guarda_anclajes()`, `taladros_anillo()` | las roscas de la brida contra la pared del bolsillo: el DXF del dorso lleva las dos líneas del bolsillo y `taladros_anillo` mide contra ellas sin saber que son nuevas |
| **cambia** `guarda_tapa()` | nada nuevo en el barrido: los labios viven donde vivía la banda, y las dos tapas siguen en 63.8° y 180° |
| **cambia** `anillo_tiene_rebaje()` (check_dxf) | el contorno del rebaje a 14 salvo en el tramo trasero, a 17 |
| **nueva** `anillo_tiene_bolsillo_trasero()` (check_dxf) | relee del dorso el polígono del bolsillo: de u = 3 a 14, de y = 1 a P5.y − 17, cerrado, con el escalón bajo el chaflán (vértice en u = 5.5, y = 3.5) |
| **cambia** `anillo_tiene_chaflan()` (check_dxf) | el chaflán de 6 en P0 y en P6 (y en P5 con la variante B) |
| **cambia** `agujeros_donde_toca()` (check_dxf) | la trasera: cero agujeros, como el costado; el costado con su canto trasero a 17.15 |
| **nueva** `guarda_trasera_flexion()` (budget) | §4.3: la trasera como PLACA por Lévy (exacta en y, 60 modos en x; apoyada en los bolsillos, libre arriba, pestañas como apoyos que solo empujan; la mano en un disco de R = 10): cinco posiciones de la mano bajo `SIGMA_PMMA_MAX` = 10 con las pestañas; combada sin ellas (21 mm) no se sale del bolsillo (acorta 2.2 de los 5.85); la mano junto al canto de arriba (16 MPa) se declara HUECO. Contrastada con el revisor: 20.45 / 5.37 mm contra sus 20.35 / 5.38 |
| **cambia** `guarda_anillo()` (budget) | `_seccion_anillo(tramo=5)`: el tramo trasero con sus dos bolsillos (−15 % de área, −36 % de inercia), no la sección genérica |
| **cambia** `guarda_marco_ventana()` (budget) | `marco_fondo_trasera` ≥ `marco_fondo` (por debajo, el .scad dibujaría a `marco_fondo` y la gemela no) |
| **nueva** `bridas_techo()` (check_dxf) | relee `miembro_alto_2d`: los cuatro M4 de brida donde el modelo los pone y, en B, el relieve de 0.5 y la esquina a 45° de cada brida — era la única chapa de la tanda sin puerta propia |
| **cambia** `taladros_talon()`, **nueva** `pestanas_talon()` (check_dxf) | los tres M4 del pie y las mismas tres en la tabla; las cuatro ventanas de las pestañas donde el modelo las pone |
| **cambia** `cuerpos_dentro_del_anillo()` | los labios en vez de las bandas, sin recorte de radio donde hay chaflán |

El orden de siempre: la puerta primero, en ROJO contra el modelo de esta tarde,
el modelo después, VERDE, y romper cada puerta nueva a propósito.

## 8. Lo que cambia para el taller

- **Mecanizado**: en la cara interior de cada anillo, el bolsillo de 11 × 6 a lo
  largo del tramo trasero, cerrado por los dos extremos (de y = 1 a P5.y − 17,
  con el escalón bajo el chaflán); y el contorno del rebaje del costado a 17
  (no 14) en ese tramo. El chaflán de P6 (y P5 en B). `costilla_dorso_2d` lleva el
  contorno del bolsillo como polígono aparte; la profundidad (6, no los 11 del
  rebaje) va en el pliego como la del rebaje. Las roscas ciegas siguen siendo 14
  por anillo, donde estaban.
- **Chapa**: `talon_2d` cambia de desarrollo (540.32 × 39.73, dos dobleces a 45°,
  tres M4, cuatro ventanas de pestaña en U con su línea de doblez sin cortar);
  `miembro_alto_2d`, en B, cambia el doblez a 90° de la banda por dos a 45° (el
  chaflán) con el relieve de las bridas.
- **Acrílico**: `piel_trasera_2d` de 552.32 × 238.18, sin taladros ni muescas
  pasantes, con un chaflán de 4 × 45° en la arista de abajo-fuera que el pliego
  pide aparte (el DXF no lo sabe decir). El pliego deja de pedir arandelas de
  nylon ni tuercas para la trasera.
- **Carpintería**: los tres taladros del talón se corren 2.5 hacia delante.
- **Juntas**: EPDM de 1 en los dos bolsillos traseros (como en las ventanas) y
  tira de EPDM de 2.5 en la cara interior de los dos labios.
- **Tornillería**: −10 M3, −10 tuercas, −10 arandelas de nylon, −10 arandelas d16.

## 9. Lo que este documento NO cierra

- **A contra B** se decide mirando los dos renders. Lo que cuesta B: un doblez
  más en el techo y el relieve en las bridas.
- **El labio del techo a 18 y el del talón a 13** (§5): si se quieren iguales a
  13, es obligar 6082-T6 en el pliego (176 MPa contra 240); a 18 los dos, es
  mover el talón sin más razón que la simetría. Se juzga en el render de B.
- **El costado entra 3 en el tramo trasero** (§3.2). Su posición la fijan los
  otros tres cantos; lo que cambia es que ahí el labio pisa 2.85 de acrílico. Si
  Samuel quiere 6 en los cuatro, el tramo trasero del anillo tiene que medir 23 de
  franja (y verse 3 más ancho desde el lado) — es una decisión de mirada, no de
  cuenta.
- **La tira de EPDM de 2.5** en los labios: alternativa, doblar los labios con un
  resalte hacia dentro. Se deja para cuando se vea la primera pieza.
- **#242** (las cabezas del marco bajo la huella del riel) sigue igual: esta tanda
  no toca las roscas de las filas.
- **#243** (el canto del pico) sigue sin puerta; en B el techo gana rigidez atrás,
  no en el pico.
- **La mano junto al canto de arriba de la trasera.** El labio del techo solo la
  para hacia fuera; hacia dentro, entre los anillos, no la sujeta nada: 200 N a
  12 del borde la comban 18 mm y la ponen a 16 MPa (`guarda_trasera_flexion()`
  lo publica como HUECO, no lo esconde). Un tope lanzado desde la meseta del
  techo dejaría una ventana a la vista en la chapa de arriba; una pestaña del
  labio hacia dentro no cabe en una chapa (§3.5). Queda por decidir si se acepta
  como está — es un empujón raro y transitorio, y 16 MPa están lejos de romper
  — o si se busca el tope.

## 10. Enmiendas que manda

| papel | qué |
|---|---|
| `2026-08-15-case-design.md` | rev. 26 en el historial; §5 (la trasera va capturada, el talón como la nariz) |
| `2026-08-29-marco-ventana-banda-estructural-design.md` | cabecera: §4 superado en la trasera y el talón; §3.2 la pata trasera a 14.5 |
| `2026-08-29-nariz-recta-valle-limpio-design.md` | §2.3: en B la meseta acaba en chaflán, no en doblez a 90° |
| `2026-08-28-costilla-pletina-design.md` | §4: el anillo lleva dos bolsillos en el tramo trasero |
| `case/README.md` | piezas, BOM, tornillería (68 → 58), orden de montaje (la trasera entra con el anillo B, como los costados) |
| `case/PLIEGO.md` | rev. 26: el bolsillo del dorso, el rebaje a 17 atrás, los chaflanes, `talon_2d`, `miembro_alto_2d`, la trasera sin taladros, juntas |
| `case/RFQ.md` | rev. 25: al mecanizado el segundo bolsillo; a la chapa los dobleces nuevos y las pestañas; al acrílico la plancha sin taladros |
