# Pliego de fabricación — cuerpo del SAM17

> **rev. 27 (2026-08-30). Tanda A: techo macizo y tres chapas empotradas.**
> **Al mecanizado:** cada anillo gana el rebaje de chapa de 4.5 de ancho × 3
> de fondo y un cajeado de brida de 28 × 15.5 × 3; son dos al fabricar el par.
> También cambian los radios a 5.5
> donde hay chapa y la franja trasera de 23. El cupón gana el rebaje y su
> reborde de 1 × 3. **A la chapa:** el techo queda sin ranuras, con labio de
> 20 y bridas con esquinas R2; techo, talón y nariz pasan a los blanks
> vigentes y los dos pies llevan muescas hasta su línea de doblez, con alivio.
> **Juntas:** doce tacos adhesivos de EPDM de 4.0 × 15 sustituyen las dos
> tiras continuas. Esta revisión sustituye las cotas operativas de la rev. 26;
> su bloque se conserva debajo como historia.
>
> **Corrección térmica del 2026-08-30.** La primera versión fijó la rendija en
> 3.0 por capilaridad. Después de hacer que las dos puertas usaran la luz
> comprimida, quedaban 0.2 K contra el techo de 15. La luz sube a 4.0 nominal
> y 3.20 comprimida: quedan 1.4 K en el aviso y la subida capilar baja a 4.7.
> Esto mueve 1 mm la trasera, la franja, el marco y los dos pies. El razonamiento
> anterior se conserva en la spec de diseño; esta es la cota de fabricación.
>
> **rev. 26 (2026-08-29, más noche; corregida tras el PR).** La trasera
> capturada como las mejillas y el talón como la nariz. **Al mecanizado**: en la cara interior
> de cada anillo, un **bolsillo de 11 × 6** a lo largo del tramo trasero
> (para las puntas de la trasera: labio de 3 al canto, 6 de hondo),
> **cerrado por los dos extremos** — de 1 mm del canto de abajo a 17 del de
> arriba, con un **escalón** bajo el chaflán de P6 (ahí arranca a 5.5 del
> plano trasero, no a 3) —; y el **contorno del rebaje
> retirado a 17** en ese tramo (la pared de 3 entre los dos bolsillos); **P6
> a chaflán 6** como P0 (y **P5** con el techo en chaflán).
> `costilla_dorso_2d` lleva el bolsillo como polígono aparte; su profundidad
> va aquí (§6.1). **A la chapa**: `talon_2d` es la nariz en espejo (labio 13,
> chaflán, pie 20; dos dobleces a 45°; **ocho ventanas de pestaña en U**) y
> `miembro_alto_2d` baja con chaflán + labio de 18 (variante B) en vez de la
> banda, con un relieve en las bridas. **Al acrílico**: `piel_trasera_2d` de
> 552.32 × 237.18 **sin un taladro**, con un **chaflán de 5.5 × 45° en su arista
> de abajo-fuera** por todo el largo (§6: no está en el DXF); `kondor_cajeado_2d`
> es solo la palabra. Mueren los 10 M3 con sus tuercas, arandelas de nylon y d16.
> **Juntas**: EPDM de 1 en el bolsillo de la trasera (como en el del costado)
> y tiras de 2.5 tras los labios. Spec
> `2026-08-29-trasera-capturada-talon-nariz-design.md`.
>
> **rev. 25 (2026-08-29, noche).** Cinco piezas en cuestión, cuatro que
> quedan. **Entra `marco_ventana_2d`** — la pletina de 6 con el contorno de la
> ventana del anillo, una por costado, espejadas por el cajeado — y **salen
> siete DXF**: las tres placas, `clip_2d`, `escuadra_trasera_2d`,
> `marco_trasera_sup_2d` y `marco_trasera_inf_2d`. **`miembro_alto_2d` cambia
> de desarrollo** (una L: banda de 24, meseta de 50 y retorno, con dos bridas
> de la banda; sale el retorno de 24 del canal) y **entra `talon_2d`** (banda
> de 24 + pie de 22, un doblez) en vez de `miembro_bajo_2d`. La trasera pierde
> seis taladros y gana dos muescas de esquina; la tabla lleva siete taladros
> más; el anillo pasa de 16 a **14 roscas ciegas** y su esquina de abajo-atrás
> a radio 4.5. El chasis de acero pierde los dos M5 de pared y gana cuatro M4
> en el suelo. `costilla_2d` y `costilla_dorso_2d` se regeneran; el cupón
> (§6.1) no cambia.
>
> **rev. 24 (2026-08-29, tarde).** Tres notas de Samuel sobre el aluminio.
> **Entra `nariz_2d`** — la banda del frente, chapa de 1.5 con TRES dobleces
> (45°, 45°, 35°) y tres M4 al pie —, **`miembro_alto_2d` crece** (la meseta
> llega al pico y gana un cuarto doblez, el retorno a 45°), y **sale
> `bahia_2d`** con sus dos roscas de la placa del valle. El anillo cambia de
> contorno en la nariz (chaflán de 6 a 45° + radios 4.5) y en las dos esquinas
> del techo (radio 4.5): `costilla_2d` y `costilla_dorso_2d` se regeneran, el
> cupón (§6.1) no cambia. La tabla lleva tres taladros más.
>
> **rev. 23 (2026-08-29).** La trasera deja de ser la pieza más exterior de
> la cara de atrás: se rehunde `t_costilla` y la enmarcan **dos bandas de
> chapa** (`marco_trasera_sup_2d`, `marco_trasera_inf_2d`). Hasta hoy sus
> cantos superior e inferior corrían 540 mm cada uno sin metal encima, y el
> de arriba eran además los últimos 8 mm del pico del case. Entra también el
> plano que faltaba del anillo: **`cupon_anillo_2d`**, la sección, con el
> cupón convertido en **punto de parada** antes de cortar los dos anillos.
>
> **rev. 22 (2026-08-28).** La costilla deja de ser **chapa de aluminio
> plegada** y pasa a **anillo de pletina mecanizada** (§6.1): una pieza
> sólida por lado, sin soldadura ni ala doblada, con roscas ciegas donde
> antes había tornillo pasante. Son **seis** talleres, no cinco — acrílico,
> chapa de aluminio (miembros con bridas, placas, clips, escuadras, las dos
> bandas del marco trasero y la tapa del valle), **mecanizado de aluminio**
> (el anillo y su cupón, taller nuevo),
> acero, madera y los rieles comprados. Cada sección dice a cuál va.
>
> **rev. 21 (2026-08-27).** Dejó de ser «el pliego de acrílico»: el case
> pasó a estructura de aluminio y el acrílico bajó a piel.

Este documento **acompaña a los DXF y no es opcional**. Un DXF solo es media
pieza: lleva la geometría de corte y no dice material, espesor, acabado,
profundidad de cajeado ni qué cara es la exterior. Sin esto, esos huecos los
rellena el taller con sus supuestos.

Para elegir taller antes de pedir, ver [`RFQ.md`](RFQ.md).

---

## 1. Material

- **PMMA COLADO (GS)**, naranja translúcido. **NO extruido (XT)**: el
  extruido trae tensión interna de fábrica y craquela solo.
- Espesor: **8 mm**, y es el único. Hubo dos hasta el 2026-08-25: los 5 mm
  existían para una sola pieza —la tapa del valle— y esa pieza pasó a
  **chapa de aluminio**, así que no entra en este pliego (§6).
- Tolerancia de espesor conocida y aceptada: **±(0.4 + 0.1 × espesor)**, o
  sea ±1.2 mm en 8. Confirmada por escrito por Schaeffer AG el 2026-08-18.
- **Comunicar el espesor real medido del lote ANTES de cortar.** No es
  cortesía: hay cotas del diseño derivadas del espesor. `marco_sup` **es** el
  espesor de una plancha, y de él cuelga una junta que el modelo exige que
  valga exactamente cero.

## 2. Proceso

- **Fresado CNC.** No láser: deja canto cónico en 8 mm y microfisura en los
  bordes cargados.
- Fresa asumida **⌀3 mm** (radio interior 1.5). **Avisar si se usa otra**:
  hay geometría acotada contra ese número, incluido el relieve de §4.
- Los DXF están **a cota final**: el CAM compensa el radio de herramienta
  como parte normal del trabajo. **No aplicar sobre-medida.**
- Unidades de los DXF: **milímetros** (implícitas en el fichero).
- Tolerancia de posición requerida entre filas de agujeros de una misma
  placa: **±0.05 mm**. El separador de una placa es uno solo, así que dos
  filas que no apoyen a la misma distancia dejan una atornillada al aire.

## 3. Acabados — los tres que hacen el producto

### 3.1 RECOCIDO (annealing) — obligatorio

**Después de mecanizar y de pulir.** El fresado deja tensión atrapada
alrededor de cada agujero y cada canto; sin recocer, el PMMA craquela en
meses — una telaraña de grietas finas que empieza por los taladros y se
acelera donde hay un tornillo apretado o donde tocó un limpiador. No se ve
al desembalar.

**Indicar temperatura y rampa empleadas** en el albarán.

### 3.2 Canto

| dónde | acabado |
|---|---|
| **canto visible** (contorno exterior de las piezas, ~7.5 m) | **PULIDO DIAMANTADO en máquina** |
| **canto interior** (ranuras, ondas, taladros, ~10 m) | tal cual sale de fresa |

**PULIDO A LLAMA PROHIBIDO.** Mete tensión superficial y deshace el
recocido; en colado craquela cerca de los agujeros.

El acrílico es translúcido: la luz viaja por dentro de la plancha y sale por
el canto. Un canto áspero se lee como una línea blanca lechosa rodeando cada
pieza; uno diamantado se enciende del color del cuerpo.

### 3.3 Chaflán

**0.5 × 45° en toda arista vista**, mecanizado (no lijado a mano).

Incluye **las dos esquinas traseras del costado**, que van a **arista viva
por diseño** (radio 0) para que la trasera empotre a ras. Arista viva más
canto pulido se desportilla al primer roce, y la de abajo va a ras del suelo.

## 4. Cajeado ciego — la operación que el DXF no describe

`kondor_cajeado_2d.dxf` **no es un recorte**: es un **vaciado a 4.0 mm de
profundidad** en la **cara exterior** de `piel_trasera_2d`. **No atraviesa**
la plancha de 8 mm. Trae **solo la palabra** (los dos rebajes de esquina que
llevó unas horas el 2026-08-29 murieron con la salida de abajo del bolsillo:
la trasera ya no pasa por ninguna boca, entra con el anillo).

- El fichero está dibujado **tal como debe verse desde fuera**: la palabra se
  lee del derecho.
- La letra es Franklin Gothic Medium; el contorno ya viene convertido a
  curvas en el DXF, no hace falta la fuente.
- Trazo mínimo verificado contra fresa de 3 mm. Si se usa fresa mayor de
  4 mm, **avisar antes de cortar**.

## 5. Orientación — la trasera tiene cara

`piel_trasera_2d` **tiene cara exterior y cara interior** desde que lleva el
cajeado. **La cara exterior es la del vaciado.** Montada al revés, el relieve
queda hacia dentro y la palabra se lee invertida.

Las demás piezas son indiferentes al lado.

## 6. Piezas

| DXF | espesor | uds | notas |
|---|---|---|---|
| `costado_2d` | 8 | **2** | canto visible completo, diamantado. **Sin un solo taladro** desde el 2026-08-27 |
| `piel_trasera_2d` | 8 | 1 | **+ `kondor_cajeado_2d` a 4 mm en la cara exterior** (§4, §5). **Sin un taladro** desde el 2026-08-29 (más noche): va CAPTURADA como el costado, con sus puntas en los bolsillos del tramo trasero de los anillos (5.85 por punta), sobre el pie del talón y bajo el fin del bolsillo. **Un chaflán de 5.5 × 45° en la arista de abajo por la cara exterior**, a lo largo de los 552.32 — cota que el DXF no sabe decir: se pide aquí, como el diamantado. Es lo que libra el escalón del bolsillo bajo el chaflán del anillo con la plancha en el fondo del bolsillo y pegada al labio; deja 2.5 de canto plano sobre el pie y queda escondido detrás del labio del talón. **552.32 × 237.18** |
| `coupon.dxf` | 8 | 1 | pieza de calibración — **sin acabado, sin recocer** |

**`remate_sup_2d` NO EXISTE.** Hasta el 2026-08-27 era la tapa de remate en
acrílico, atornillada de canto al larguero de remate trasero; ese día la
meseta del techo pasó a ser el ala del propio miembro trasero alto (doblada
de su blank, `marco_sup`), no una plancha aparte. `remate_sup()` y
`remate_sup_2d()` se borraron del `.scad` en el fix round 1 de esta tarea
(2026-08-28, sin llamador confirmado por grep). No es un pendiente de
`export.ps1`: la pieza no está en el diseño.

**`bandeja_base_2d` SALIÓ de este pliego el 2026-08-27.** Era el suelo, de
acrílico de 8. Ahora es una **tabla de madera maciza de 30 mm** (18 hasta la ficha 12 del 10-10) que va bajo el
marco y hace de suelo y de zócalo a la vez. Va al carpintero, §6.2.

**Y el costado dejó de llevar taladros.** Tenía cuatro M4 de riel y cuatro M5 de
larguero; los ocho se fueron al anillo de aluminio. La pieza es ahora
**piel**: entra por detrás y asienta en el rebaje del anillo (§6.1), sobre una
junta de EPDM de 1 mm, sin tocarlo con ningún tornillo — la retención hacia
dentro la hace el **marco de la ventana** (una pletina por costado, corrida
por los siete tramos, desde el 2026-08-29 por la noche; antes placas, clips y
escuadra), atornillado al aluminio, nunca al acrílico. Al taller le llega un
contorno y nada más — menos operaciones y menos sitios por donde el PMMA raja.

**`lienzo_2d.dxf` es solo previsualización de nesteado: NO SE CORTA.**

### Lo que NO va a este taller

Diez DXF de `case/plans/` **no son de acrílico** y no entran aquí. Se reparten
entre DOS talleres — chapa y mecanizado (§6.1) — que **no son el mismo** desde
el 2026-08-28:

| DXF | material | taller | proceso |
|---|---|---|---|
| `chasis_cuerpo_2d`, `chasis_tapa_2d`, `chasis_refuerzo_2d` | acero | chapa | corte + **plegado** |
| `miembro_alto_2d` | aluminio 6082-T6, 1.5 mm | chapa | corte + **plegado**: techo **sin ranuras**, blank **593.02 × 73.85**, meseta de 50, retorno de 4, chaflán de 6 y labio de 20. Dos bridas de 27 × 14.5 con esquinas R2. Entran en los cajeados del anillo; no se dejan sobre la cara — **1 ud** |
| `talon_2d` | aluminio 6082-T6, 1.5 mm | chapa | corte + **plegado**: blank **545.62 × 42.23**, labio de 13, chaflán y pie de **22.5**. En cada punta del pie, muesca de 2.65 hasta la línea de doblez a 22.06, con alivio de Ø2 a caballo de la esquina interior. Conserva sus ocho pestañas lanzadas; el 6082-T6 sigue siendo obligatorio — **1 ud** |
| `nariz_2d` | aluminio 6082-T6, 1.5 mm | chapa | corte + **plegado**: blank **545.62 × 50.20**, pie de **20.5** y tres dobleces. En cada punta del pie, muesca de 2.65 hasta la línea de doblez a 20.06, con alivio de Ø2 a caballo de la esquina interior — **1 ud** |
| `tapa_valle_2d` | aluminio, 3 mm | chapa | corte + **plegado**: blank **560.00 × 20.00**, dos pestañas de 21 mm y labio trasero de apoyo de 2.0 mm; sin taladros visibles en la banda |
| `costilla_2d`, `costilla_dorso_2d` | **aluminio, pletina de 14 mm** | **mecanizado** (§6.1) | **fresado CNC**, sin plegar, sin soldar |
| `bandeja_base_2d` | madera maciza, 30 mm | carpintería | corte + ranuras alargadas + canto de arriba redondeado R8 |
| `marco_ventana_2d` | aluminio, `t_placa` = 6 mm, **láser** | chapa | corte + **6 cajeados** Ø8 × `prof_cajeado_riel` = 2.5 **por el lado del anillo** (bolsillos ciegos en UNA cara: dejan 3.5 mm bajo la cabeza del M4 del riel). Nota de mecanizado, no va en el DXF — ver abajo — **2 uds, PAR ESPEJADO**: mismo contorno, cajeado por caras opuestas. **Planitud ≤ 0.5 mm en 300** en el blank cortado: apoya en la cara mecanizada del anillo y doce M4 lo conforman contra ella (una pletina de 6 × 24 se aplana 0.5 con 200 N), pero con más de eso el acrílico lo nota |
| `cupon_anillo_2d` | **aluminio, pletina de 14 mm** | **mecanizado** (§6.1) | **NO ES UNA PIEZA DEL CASE**: es la SECCIÓN del perfil del anillo, y de ella sale el **cupón de 100 mm** que hay que aprobar antes de cortar los dos anillos — ver el punto de parada en §6.1 |

**Juntas de los dos labios:** suministrar y pegar **12 tacos de EPDM de
4.0 × 15**, seis en el labio del techo y seis en el del talón. No sustituirlos
por tiras continuas: el taco fija la luz y el vano entre tacos deja respirar la
rendija.

**`costilla_2d` y `costilla_dorso_2d` son CONTORNOS REALES, no desarrollos** —
al revés de como era hasta el 2026-08-27. La pieza ya no se dobla: lo que corta
la fresa es lo que sale.

**Qué trae cada hoja, exactamente** (es lo que verifica `check_dxf.py`, y la
descripción de antes estaba cambiada — decía que el rebaje iba en la hoja de la
cara):

- **`costilla_2d` — LA CARA VISTA.** Silueta exterior y ventana central, y
  **nada más**: la ventana sale de retirar `cara_anillo` = **20 mm** de la
  silueta, que es el ancho de la cara vista. **NO trae el contorno del rebaje.**
  Es la hoja del corte del blank.
- **`costilla_dorso_2d` — LA CARA INTERIOR.** Trae el contorno del rebaje del
  costado y, desde la rev. 27, el **rebaje de chapa de 4.5 de ancho** a lo
  largo del contorno solo donde se ve techo, nariz o talón. Bajo los dos
  labios, ese contorno se funde con el bolsillo de la trasera. El bolsillo va
  en **u = 5.5..16.5**, con pared de 3 y el costado entrando 3.5; su labio
  queda con 3 de hondo bajo los labios de chapa y conserva 6 en el resto.
  Trae también la planta del cajeado de brida de cada anillo —dos al fabricar
  el par—, de **28 × 15.5**, y los 14 círculos de rosca ciega. La silueta no se repite: dibujarla sería mandar
  cortar el contorno dos veces. **Las profundidades no viven en esta planta**;
  están escritas en §6.1.

**El dorso está dibujado EN LAS MISMAS COORDENADAS que la cara, no espejado.**
Léase como *la cara de atrás de la misma pieza, mirada desde el mismo lado*:
`taladros_anillo()` compara los centros del DXF contra los del modelo **sin
ninguna transformación**, así que si alguien «arregla» el fichero espejándolo,
las roscas se van al otro extremo del anillo y la puerta lo canta. Quien se
voltea es **la PIEZA en la máquina**, no el dibujo.

**`talon_2d`, `miembro_alto_2d`, `nariz_2d` y `tapa_valle_2d` SÍ son
DESARROLLOS PLANOS, no contornos** — igual que las tres
del chasis: el DXF trae el recorte, y la pieza doblada mide menos. Cortar el
contorno de la pieza montada da un fichero válido e inservible.

**LOS DOS ANILLOS SON PIEZAS ESPEJADAS, no dos iguales.** Mismo contorno y
misma ventana, pero **el rebaje, el chaflán de la ventana y las 14 roscas
ciegas van en la cara OPUESTA de cada uno**: la cara vista de cada anillo mira
hacia FUERA del case, así que el dorso de uno es el lado que en el otro queda
por delante (`costillas()` en `sam17_case.scad` monta el segundo con
`mirror([0,0,1])` justo por esto). Cortar los dos con las operaciones del mismo
lado da un case con un anillo del revés: el rebaje del segundo abriría hacia
fuera y el acrílico no tendría dónde entrar. **Un anillo derecho y uno
izquierdo.**

**EL MARCO DE LA VENTANA (`marco_ventana_2d`) SUSTITUYE A PLACAS, CLIPS Y
ESCUADRAS desde el 2026-08-29 por la noche.** Es la pletina de 6 con el
contorno de la ventana del anillo, corrida por los siete tramos: sobre las
tres filas es exactamente la placa de anclaje de la mañana (canto a la
silueta, cajeado por riel, dos roscas por riel), y en el frente, el suelo,
la meseta y la trasera es el tope del acrílico que daban los clips y la
escuadra. Blank **294.56 × 252.88**. **Se cortan DOS con el mismo DXF y son
un PAR ESPEJADO**: el cajeado Ø8 × 2.5 va en la cara OPUESTA en el de un
costado y en el del otro, porque cada cajeado tiene que mirar al anillo de
SU lado. Los seis cajeados van centrados en los seis pasos M4 de riel
(cuatro 3U, dos 1U) por la cara que mira al anillo — ahí aloja la cabeza
del tornillo del riel; sin ellos la cabeza no tiene dónde meterse y el marco
no cierra contra el anillo. **El DXF NO lleva el cajeado**: un DXF 2D no sabe
decir profundidad, el mismo caso que el rebaje de `costilla_dorso_2d` y el
cajeado KONDOR (§4). Trae **19 taladros**: los doce pasos M4 al anillo (diez
en las tres filas y dos en la pata del suelo, a 60 de cada extremo de la pata:
el trabajo que hacían los de los clips), los seis pasos M4 de riel y la rosca
M3 de la pestaña de la banda del valle a
**diámetro de broca** (pasante en la propia pletina). Y una **muesca** en la
esquina trasera-alta, abierta al canto exterior, de 16.5 de honda: ahí apoya
en la cara del anillo la brida del miembro alto, y el marco se aparta.

**Su canto exterior no va a la silueta en todos los tramos.** En las tres
filas sí: es el borde de aluminio de la fila. Bajo las chapas empotradas se
retira **2.65**, porque la cara de la chapa queda 1 por dentro del contorno.
En el **suelo** se retira **1.65**: los pies apoyan a ras y no entran en el
rebaje. En la trasera se retira **17.00**, medio milímetro después de la pared
del bolsillo. El canto interior conserva 26 de fondo salvo en la pata
trasera, donde `marco_fondo_trasera` vale **30**. Así queda una pata de
**13 × 6**; con 200 N cede 1.54 mm y trabaja a 114 MPa, por debajo de los
techos de 2 mm y 130 MPa. `taladros_marco_ventana()` relee el contorno del
fichero.

**LA BRIDA DEL TECHO VA EMPOTRADA.** Cada brida mide **27 × 14.5** y lleva
sus esquinas a **R2**. Asienta entera en un cajeado de **28 × 15.5**, con
esquinas interiores **R1.5** para la fresa de Ø3. El cajeado se hace en la
cara interior del anillo, a **3 mm de profundidad**. Esa profundidad deja
**11 mm de pletina** bajo los dos M4 ciegos: la brida queda más lejos del
barrido de la tapa y la rosca conserva cuerpo. La muesca del marco sobre la
brida se mantiene. La trasera no lleva muesca ni taladro.

**LO QUE ENTRA EN LOS REBAJES MIDE 545.62 ENTRE PAREDES.** Sale de la luz
546.62 menos 0.5 por cada canto. En nariz y talón, el pie no entra: vuelve al
ancho de apoyo mediante una muesca de 2.65 en cada punta. No recortar el pie a
todo el ancho del blank, porque entonces dejaría de apoyar entre los anillos.

**EL TALÓN (`talon_2d`) ES LA NARIZ EN ESPEJO**: labio vertical de 13,
chaflán a 45° sobre P6 y pie de **22.5** sobre la tabla. Blank
**545.62 × 42.23**. En cada punta del pie se corta una **muesca de 2.65** desde
el canto libre hasta la línea de doblez pie-chaflán. Esa línea está a
**22.06** del canto libre (`largo − BD45/2`), no en el largo nominal del pie.
La esquina interior lleva un **alivio de Ø2 a caballo de la línea**: sin él,
el pliegue arrancaría la muesca. Conserva los tres M4 del pie y las ocho
ventanas de pestaña del DXF. Los dos dobleces van hacia dentro. Sin bridas ni
rosca en el anillo.

**LA NARIZ (`nariz_2d`) LLEVA TRES DOBLECES, y ninguno es a 90°.** Blank
**545.62 × 50.20**, con pie de **20.5**. El pie crece para que los dos pies no
difieran más de 2: se mantienen como una familia. En cada punta se corta una
**muesca de 2.65** desde el canto libre hasta la primera línea de doblez, a
**20.06** (`largo − BD45/2`). Lleva un **alivio de Ø2 a caballo de la esquina
interior**. Después siguen los dos dobleces restantes del perfil vigente. Los
tres van hacia dentro; el pie queda sobre la tabla.

**Corrección del 2026-08-30.** La boca del avellanado M4 del talón es un cuerpo
fijo detrás de la cara interior del acrílico y necesita 1.70 de aire. Con la
trasera 1 mm más adentro y el pie en 21.5 quedaban 1.77: verde por 0.07 no es
margen. El pie en 22.5 recupera 2.77. La nariz lo sigue a 20.5 porque los dos
pies no pueden diferir más de 2. Va bajo la tabla y no se ve.

**`miembro_alto_2d` ES EL TECHO MACIZO.** Hay una sola geometría operativa en
esta revisión: blank **593.02 × 73.85**, meseta de 50 **sin ranuras**, retorno
de 4 a 45° en el pico, chaflán de 6 y labio de **20**. Las dos bridas de
27 × 14.5 se doblan de las puntas del labio y llevan las esquinas a **R2** para
entrar enteras en los cajeados R1.5 del anillo. Sin fila de M3 y sin canal: la
trasera no se atornilla al techo.

**LOS RADIOS DEL CONTORNO SIGUEN LA CHAPA.** Donde el anillo bordea una chapa
empotrada, el radio es **5.5**: `radio_chapa` 4.5 más el rehundido de 1. Así el
reborde sigue concéntrico al arco del pliegue. Donde nariz o talón salen del
rebaje hacia el pie, vuelve a **4.5**: el reborde termina y el pie sigue a ras
sobre la tabla. Las tres esquinas con chaflán conservan el chaflán de 6.

(Las notas sobre los DXF de placa y su fix round — el cajeado dibujado en
vez del paso M4 — quedan en el historial: la pieza es hoy el marco de la
ventana, con las mismas dos mitades por agujero de riel, el paso M4 en el
DXF y el cajeado como nota.)

Las tres del chasis llevan su propio plano de plegado
([`renders/chasis-plano-plegado.png`](renders/chasis-plano-plegado.png)),
porque un DXF de corte no dice de dónde doblar. Los cuatro desarrollos de
aluminio (miembro alto, talón, nariz, tapa del valle) no tienen plano de
plegado dedicado — `renders/plano_chasis.py` cubre solo el acero — y siguen
sin necesitarlo si el taller ya trabaja de los mismos DXF que el chasis. Los
que no son a 90° (la nariz, el retorno de la meseta) llevan sus líneas escritas
arriba.

**La tapa del valle** era acrílico de 5 mm hasta el 2026-08-25 y es la
superficie horizontal entre las dos filas de módulos. Cambió a aluminio de
3 mm porque en PMMA fluía a 90 N y era la pieza más floja del case. Desde la
Tanda B ya **no trabaja como viga entre las pestañas**: el canto trasero se
prolonga 2.0 mm sobre la cara del primer Z-Rail KONDOR y transmite ahí la
carga de mano. Entre ambos se monta una tira anti-ruido adhesiva de
**0.20 mm nominal, comprimida a 0.10 mm**; se compra en rollo y no tiene DXF.
Con 200 N sobre una banda conservadora de 50 mm, `guarda_valle()` verifica
flecha y tensión por debajo de sus techos.

Desde el 2026-08-27 **tampoco es plana**: lleva una pestaña de 21 mm doblada a
90° en cada punta. **Desde el 2026-08-28 esa pestaña ya NO se atornilla al
anillo**: se rosca pasante en el MARCO DE LA VENTANA (6 mm de pletina, ruling
R3; hasta el 29-08 por la noche, en la placa del valle), porque su rosca
caería a 13.7 mm del plano del valle y la franja del anillo solo admite
hasta 10.25 antes de salir por la pared del rebaje. Sigue atando la banda a
los dos marcos y convirtiéndola en diafragma a media altura — el ancla
cambió de pieza, no la función.

**Ninguna pieza de aluminio o de acero lleva nada de §3**: ni recocido, ni
diamantado, ni el chaflán de 0.5. Esas tres cosas son del PMMA. Canto
desbarbado y basta — salvo el anillo, que tiene su propio acabado (anodizado
satinado, §6.1) y tampoco lleva recocido ni diamantado, y la tapa del valle,
que va **anodizada en negro** después de plegar (ficha 14 del acta del
09-10), y la **tira negra del valle** (ficha 6, 10-10): chapa de aluminio de 1 mm,
lisa, cortada a las cotas que imprime `guarda_tira_valle()` y anodizada en
negro, sin taladros ni plegados.

### 6.1 Taller de mecanizado: el anillo

**Taller nuevo desde el 2026-08-28.** Hasta esa fecha la costilla era chapa
de aluminio plegada y entraba en el pliego de chapa; el render de esa pieza
se leía «como un sándwich de aluminio envolviendo el acrílico» y Samuel lo
rechazó. El anillo que la sustituye no se pliega ni se suelda: es una pletina
maciza, vaciada por el centro con fresadora CNC.

- **Material y blank.** Pletina de aluminio de **14 mm** de espesor
  (`t_anillo`). Blank aproximado **340 × 270 mm** (spec de diseño §9; el
  contorno real mide 319.8 × 256.2 mm, `costilla_2d`, con margen de sujeción
  y desbaste).
- **SON DOS PIEZAS ESPEJADAS, uno derecho y uno izquierdo.** Mismo contorno y
  misma ventana; los **rebajes, los cajeados, el chaflán de la ventana y las
  14 roscas ciegas van en la cara OPUESTA de cada anillo**, porque la cara vista de cada uno
  mira hacia FUERA del case. Mecanizar los dos por el mismo lado da un anillo
  del revés, con el rebaje abriendo hacia fuera y el acrílico sin sitio donde
  entrar. En el modelo esto es el `mirror([0,0,1])` de `costillas()`.
- **Contorno + ventana.** Corte de la silueta exterior y de la ventana
  central — láser o agua y luego fresa, o todo fresa: lo decide el taller,
  siempre que el acabado final sea el fresado de §6.1.
- **Rebaje**, por detrás de la cara vista, donde asienta el costado: **6 mm**
  de ancho en el plano (`rebaje_anillo`) × **11 mm** de profundidad
  (`t_anillo − rehundido_acrilico`, 14 − 3). Sin él el acrílico no tiene
  dónde entrar y asoma por delante del anillo.
- **Rebaje de chapa**, en la cara interior y solo a lo largo del contorno que
  queda cubierto por techo, nariz o talón: **4.5 mm de ancho × 3 mm de
  profundidad**, desde z = 11 hasta z = 14 contando desde la cara vista. Deja
  un **reborde de 1 × 3**. La chapa queda 1 por dentro del contorno, con 0.5
  de holgura al canto y 2.5 agarrados en z. El reborde tapa el canto; por eso
  no se extiende bajo los pies.
- **Un cajeado de brida por anillo, dos en total**, de **28 × 15.5 × 3 mm**,
  en la cara interior. Esquinas interiores R1.5 para la fresa Ø3. Las bridas
  van a R2. Quedan 11 mm de pletina bajo sus dos M4 ciegos.
- **Tramo trasero de 23 mm de franja.** El bolsillo de la trasera ocupa
  u = 5.5..16.5; después quedan la pared de 3 y los 3.5 que entra el costado.
  Bajo los labios del techo y del talón, el labio del bolsillo tiene 3 de
  hondo porque el rebaje de chapa ocupa los otros 3. En el resto conserva 6.
- **Radios de contorno:** 5.5 donde se ve chapa empotrada; 4.5 donde la chapa
  abandona el rebaje para formar el pie. Así el marco sigue el pliegue sin
  levantar el apoyo de la tabla.

**PROFUNDIDADES QUE NO ESTÁN EN EL DXF:** el rebaje de chapa tiene **3 mm** y
cada cajeado de brida tiene **3 mm**. `costilla_dorso_2d` es una planta: marca
la huella, no el eje Z. No deducir la profundidad del ancho dibujado.
- **Chaflán 1.5 × 45°** (`chaflan_anillo`) en las DOS aristas de la cara
  vista: la exterior (silueta) y la de la ventana. Es lo que lee como
  «perfil» en vez de «banda plana» — la razón entera del cambio de diseño.
- **Radio ≥ 3 mm** en la esquina interior de P3, el único vértice cóncavo
  del contorno — pide una fresa de **⌀6 mm** para ESA esquina puntual, más
  gruesa que la de contorno general (`fresa_d` = ⌀3 mm, §8): dos útiles
  distintos para dos operaciones distintas, no una contradicción. Es
  esquina fresada, no esquina de plegado: no lleva alivio en V ni cierre
  soldado — esas dos cosas mueren con la chapa plegada.
- **Roscas ciegas M4 en la cara interior (el dorso); las M5 NO van ahí, van
  en el CANTO INFERIOR** — a diámetro de broca, las del dorso según
  `costilla_dorso_2d.dxf`: broca **3.3 mm para M4**, broca
  **4.2 mm para M5**, **10 mm de profundidad útil** (14 mm de pletina menos
  el margen que deja la puerta de anclajes). Son **14 roscas M4 por anillo**
  — la cuenta que imprime `taladros_anillo()` sobre este mismo DXF: dos por
  riel 3U, dos sobre el primer riel 1U y dos en la pata del suelo (las doce
  del marco de la ventana; las del suelo caen en x = 67.6 y 236.2, lejos de
  los tres M5 de la tabla que entran por el canto en 44.6, 153.7 y 262.8 —
  `guarda_marco_ventana()` lo mide) y dos de la brida del miembro alto; eran
  16 con los clips y la brida del
  miembro bajo, muertos el 29-08 por la noche — más **3 roscas M5 por anillo (6 en total, 2
  filas de 3) en el CANTO INFERIOR** para la tabla: esas NO salen en el DXF
  del dorso porque entran por el canto, no por la cara, así que van descritas
  aquí y no en el plano: al medio de los 14 mm de espesor, broca 4.2.
- **Acabado: anodizado satinado**, después de mecanizar. El punto de bonding
  de PE va **enmascarado antes de anodizar**, en la cara interior, uno por
  anillo — el anodizado es aislante y ese punto tiene que quedar metal
  desnudo.
- **PUNTO DE PARADA: el cupón, antes de cortar los dos anillos.** Las cotas
  de la cara vista (chaflán, rebaje, rehundido) salieron de escalar una foto
  de referencia y están marcadas ESTIMADO en la spec de diseño. **No se corta
  el material de los dos anillos hasta que este cupón esté aprobado.** Es la
  misma lógica que el cupón de kerf del acrílico (§ «Procedimiento del cupón»
  en el README): medir sobre la pieza real, no sobre el render.

  **Qué se pide:** `plans/cupon_anillo_2d.dxf` es la **sección** — el único
  plano del anillo que lleva las profundidades, porque los otros dos son
  vistas de planta y ninguna sabe decir «14 de pletina» ni «1.5 × 45». Del
  perfil de esa sección, **100 mm de largo**, con **una rosca ciega M4 (broca
  3.3, 10 mm útiles) a media altura de la franja, a media longitud**, y
  **anodizado satinado con un punto de bonding enmascarado** en la cara
  interior. Mismo material, mismo mecanizado y mismo anodizador que van a
  hacer los anillos: un cupón hecho de otra forma no mide nada.

  Desde la rev. 27, el cupón reproduce la **sección completa del anillo con
  doce vértices**: los ocho anteriores más los cuatro de la muesca del
  **rebaje de chapa de 4.5 × 3**. La muesca deja el **reborde de 1 × 3** entre
  ella y el canto. Así el cupón permite medir el reborde sobre metal. Ese
  reborde es la pared más delicada
  del anillo; probarlo en el cupón evita descubrir su límite después de vaciar
  las dos piezas completas. Si el taller no acepta el reborde de 1 con **+0.3 / −0** (asimétrica a
  propósito: 0.9 es rojo para `guarda_rebaje_chapa`, y pedir ±0.1 sería
  aceptar por contrato una pieza que rechazamos por diseño), se
  detiene el cupón y el diseño se regenera a 1.5 antes de cortar.

  **Qué se mira cuando vuelve, y qué pasa si falla:**

  | # | Qué se comprueba | Criterio | Si falla |
  |---|---|---|---|
  | 1 | El chaflán se lee como en la foto de referencia | 1.5 ± 0.2 a 45°, continuo y sin escalones de faceta, mirado con la misma luz y al lado de la referencia impresa | Se cambia `chaflan_anillo` (rango ESTIMADO 1–3), se reexporta la sección y se pide otro cupón |
  | 2 | El rebaje asienta el PMMA del lote | Con el recorte **más grueso** del lote (8 + 1.2 = 9.2) más la junta de 1 tiene que entrar en los 11 de fondo y **sobrar 0.3**; con el **más fino** (6.8) la junta todavía tiene que precargar | Se sube `t_anillo` — la puerta `guarda_rebaje()` ya dice que con 12 el rebaje quedaba a −0.2, o sea que no cabía |
  | 3 | El anodizado no interrumpe el PE | **≤ 0.1 Ω** medido a cuatro hilos entre el punto enmascarado y un tornillo M4 apretado en la rosca ciega (spec 2026-08-27 §3.4) | El enmascarado no valió: se rehace el punto y se vuelve a medir antes de anodizar los anillos |
  | 4 | El rebaje de chapa deja un marco continuo | Rebaje de 4.5 × 3 y reborde de 1 × 3, sin mordidas ni pared abierta | No se cortan los anillos; se aplica la respuesta acordada en el RFQ y se pide otro cupón |

  Las cotas **en el plano** (cara vista y ancho del rebaje) no hacen falta
  medirlas aquí: las cruzan `anillo_tiene_ventana()` y `anillo_tiene_rebaje()`
  contra los ficheros que se cortan, en cada corrida. Lo que el cupón cierra
  son las **profundidades del perfil** y el **acabado**, que ningún DXF de planta
  puede decir y ningún render puede decidir.
- **Aleación: recomendada, no obligatoria.** La puerta (`guarda_anillo()`)
  calcula con **Rp0.2 = 130 MPa**, el conservador de siempre, y con la
  sección de este anillo (I = 3714 mm⁴, 214 mm², contra 1673 mm⁴ de la vieja
  L plegada) el **5754 H22 pasa con margen de sobra**. El taller puede
  ofrecer 6082-T6 o 5083 por planitud de la pletina tras el vaciado del
  centro — el riesgo técnico real de esta pieza, no la resistencia — pero no
  es un requisito de cálculo.

**Pregunta eliminatoria para este taller** (va también al RFQ, §D):
**planitud garantizada después de vaciar el centro de una pletina de 14 mm.**
Vaciar el centro de una placa gruesa libera tensión interna del material y
puede alabearla; si el taller no puede darla plana, no es el taller.

**Muere de este taller** lo que era del pliego de chapa: los seis alivios
convexos de 4.5 mm, el rip bisector de P3 y su soldadura lineal de 14.5 mm
por costilla — el anillo es una pieza, no siete tramos cerrados a soldadura.

### 6.2 La tabla — al carpintero

`bandeja_base_2d`, **madera maciza de 30 mm, 648.62 × 399.76**, con el
**canto de arriba redondeado R8** (fresa de redondeo; el de abajo, vivo).
Creció el 2026-10-10 por la ficha 12 del acta: la tabla vuela `vuelo_zocalo` =
40 mm más allá del cuerpo por los cuatro lados, para que asome de la piel
entre 25 y 40, y es más gruesa a la vista. Hasta entonces, 18 mm y 588.62 ×
339.76. Es el suelo interior del case **y** el zócalo que sobresale: una sola
pieza. El cuerpo se le apoya encima y las cuatro paticas van atornilladas por
debajo.

**La veta corre a lo largo** (los 648 mm). No es decoración: fija en qué
dirección se mueve la tabla, y de ahí salen las ranuras.

**Las ranuras alargadas NO son opcionales y NO se pueden cambiar por agujeros
redondos.** Son la fijación al anillo de aluminio, que no se mueve, y la tabla
sí: a contraveta, del orden de 3 mm sobre los 307 mm de fondo entre un invierno
seco y un verano húmedo. **Van a rosca ciega en el canto inferior del anillo**
(al medio de sus 14 mm, broca 4.2 — §6.1), no a un larguero. El dibujo trae,
en cada una de las dos filas (una por anillo, 3 tornillos cada una):

- **un agujero REDONDO, el del medio** — es el punto fijo,
- **dos RANURAS de 10.5 × 5.5**, alargadas en el fondo.

Con todos redondos, la tabla se raja por la fila o suelta los tornillos. Con
todos alargados, se arrastra hacia un extremo y el vuelo del zócalo deja de ser
simétrico.

**Y catorce taladros pasantes de Ø4.5, redondos**: cuatro de las paticas
(por debajo), tres de la nariz y tres del talón (las dos bandas de chapa que
se atornillan a la tabla por su pie, desde dentro) y, desde el 2026-08-29 por
la noche, **cuatro del chasis del PSU**, que apoya en la tabla y se atornilla
desde abajo a tuercas remachables de su suelo. `guarda_zocalo()` y
`taladros_talon()` los censan por posición.

**Especie sin elegir.** Las cuentas del modelo van contra E = 11 000 MPa a favor
de veta (nogal o arce). Roble da ~12 000 y sobra; un contrachapado da ~8 000 y
pediría 20 mm. **Decir qué especie se suministra antes de cortar.**

**Acabado y sentido de la cara vista**: la cara de arriba es el suelo que se ve
por dentro del case a través del acrílico; el canto es lo que se ve por fuera.
Las dos cuentan.

## 7. Manipulación y limpieza — para nosotros, no para el taller

Esta sección no es del pedido: es de lo que pasa **después**, y es donde se
estropea un acabado que llegó bien.

- **Prohibido alcohol y limpiacristales con amoníaco**: craquelan el PMMA.
  Agua tibia con jabón neutro y paño de microfibra.
- **El film protector se quita al FINAL del montaje**, no al recibir. El
  acrílico llega perfecto y se raya durante el ensamblaje: al deslizarlo por
  la mesa, al apoyar una herramienta, al girar una pieza sobre otra.
- **Ningún tornillo toca acrílico** desde el 29-08 (más noche): los costados
  y la trasera van capturados. Los paneles y sus seis Z-Rails quedan fijos;
  no existen ejes de giro, cierres manuales ni tornillos de fricción.
- **Paticas**: goma con casquillo roscado, **atornilladas, nunca pegadas**.
  El case no lleva ninguna junta irreversible desde el 2026-08-21.

## 8. De dónde salen estos números

Todo lo cotado aquí vive en [`cad/params.scad`](cad/params.scad) con su
puerta en [`clearance_budget.py`](clearance_budget.py) o
[`check_dxf.py`](check_dxf.py). **Si este documento y el modelo se
contradicen, el equivocado es este documento.**

| aquí | parámetro | puerta |
|---|---|---|
| chaflán 0.5 × 45° (PMMA) | `chaflan` | `guarda_chaflan()` |
| cajeado 4.0 mm | `kondor_prof` | `guarda_kondor()` |
| apriete 1.0 N·m / d16 | `par_m3`, `d_arandela` | `guarda_apriete()` |
| flecha de patica 0.25 mm | `flecha_pie` | `guarda_paticas()` |
| fresa ⌀3 mm | `fresa_d` | `guarda_fresado()` |
| tapa del valle, aluminio 3 mm; apoyo 2.0; tira 0.20 comprimida a 0.10 | `t_valle`, `apoyo_valle`, `tira_valle_nominal`, `compresion_tira_valle` | `guarda_valle()` |
| fila auxiliar KONDOR 55 mm / centros 49 mm; paneles y rieles rehundidos 1.50 | `alto_panel_1u`, `inset_er`, `rehundido_panel` | `guarda_fila_1u()`, `guarda_rehundido_panel()` |
| anillo: espesor 14, cara 20, rebaje 6, rehundido 3, chaflán 1.5 × 45° | `t_anillo`, `cara_anillo`, `rebaje_anillo`, `rehundido_acrilico`, `chaflan_anillo` | `guarda_anillo()`, `guarda_rebaje()` |
| roscas ciegas del anillo, broca M4 3.3 / M5 4.2 | `d_M4_rosca`, `d_M5_rosca` | `guarda_anclajes()`, `taladros_anillo()` |
| junta de asiento EPDM 1 mm (costado y trasera) | `t_junta_asiento` | `guarda_rebaje()`, `guarda_trasera_capturada()` |
| rebaje de chapa 4.5 × 3, rehundido 1, holgura 0.5, reborde 1 × 3 | `rebaje_chapa`, `rehundido_chapa`, `hol_chapa` | `guarda_rebaje_chapa()`, `anillo_dorso_tiene_rebaje()` |
| tramo trasero 23; bolsillo u = 5.5..16.5; pared 3; costado 3.5; labio 3 bajo las chapas y 6 en el resto | `cara_anillo_trasera`, `rehundido_trasera`, `pared_rebaje_trasera`, `entrada_costado_trasero` | `guarda_tramo_trasero()`, `anillo_tiene_bolsillo_trasero()` |
| cajeado de brida 28 × 15.5 × 3, R1.5; brida R2; pletina restante 11 | `rebaje_chapa`, `brida_*` | `guarda_miembro_alto()`, `bridas_techo()` |
| marco retirado 2.65 bajo chapa, 1.65 en el suelo y 17.00 atrás; fondo trasero 30 | `rehundido_chapa`, `marco_fondo_trasera` | `guarda_marco_ventana()`, `taladros_marco_ventana()` |
| talón: pie 22.5, blank 545.62 × 42.23, muesca 2.65 hasta 22.06, alivio Ø2 | `talon_pie`, `muesca_pie` | `guarda_talon()`, `pestanas_talon()` |
| nariz: pie 20.5, blank 545.62 × 50.20, muesca 2.65 hasta 20.06, alivio Ø2 | `nariz_pie`, `muesca_pie` | `guarda_talon()`, `check_dxf` |
| techo macizo: labio 20, blank 593.02 × 73.85 | `techo_labio` | `guarda_miembro_alto()`, `techo_macizo()` |
| doce tacos EPDM 4.0 × 15; rendija nominal 4.0, comprimida 3.20 | `aire_labios`, `taco_largo` | `guarda_rendija()`, `guarda_aire()` |
