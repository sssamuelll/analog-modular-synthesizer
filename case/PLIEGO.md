# Pliego de fabricación — cuerpo del SAM17

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
la plancha de 8 mm.

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
| `piel_trasera_2d` | 8 | 1 | **+ `kondor_cajeado_2d` a 4 mm en la cara exterior** (§4, §5). **10 taladros M3** (eran 16 con las escuadras) y **dos muescas de esquina** arriba, de 2 × 15 con radio 2 en el rincón: por ahí le pasa por debajo la brida del miembro alto. Va DENTRO de las dos bandas, sobre el pie del talón |
| `coupon.dxf` | 8 | 1 | pieza de calibración — **sin acabado, sin recocer** |

**`remate_sup_2d` NO EXISTE.** Hasta el 2026-08-27 era la tapa de remate en
acrílico, atornillada de canto al larguero de remate trasero; ese día la
meseta del techo pasó a ser el ala del propio miembro trasero alto (doblada
de su blank, `marco_sup`), no una plancha aparte. `remate_sup()` y
`remate_sup_2d()` se borraron del `.scad` en el fix round 1 de esta tarea
(2026-08-28, sin llamador confirmado por grep). No es un pendiente de
`export.ps1`: la pieza no está en el diseño.

**`bandeja_base_2d` SALIÓ de este pliego el 2026-08-27.** Era el suelo, de
acrílico de 8. Ahora es una **tabla de madera maciza de 18 mm** que va bajo el
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
| `miembro_alto_2d` | aluminio 6082-T6, 1.5 mm | chapa | corte + **plegado**: una L — banda de 24 a 90°, meseta de 50, **retorno a 45°** de 4 en el pico — con dos **bridas** dobladas a 90° de las puntas de la banda — **1 ud** |
| `talon_2d` | aluminio 6082-T6, 1.5 mm | chapa | corte + **plegado**: UN doblez a 90° (banda de 24 + pie de 22) — **1 ud** |
| `nariz_2d` | aluminio 6082-T6, 1.5 mm | chapa | corte + **plegado**: TRES dobleces (45°, 45° y 35°) — **1 ud**. Ver las líneas de plegado abajo |
| `tapa_valle_2d` | aluminio, 3 mm | chapa | corte + **plegado** |
| `costilla_2d`, `costilla_dorso_2d` | **aluminio, pletina de 14 mm** | **mecanizado** (§6.1) | **fresado CNC**, sin plegar, sin soldar |
| `bandeja_base_2d` | madera maciza, 18 mm | carpintería | corte + ranuras alargadas |
| `marco_ventana_2d` | aluminio, `t_placa` = 6 mm, **láser** | chapa | corte + **6 cajeados** Ø8 × `prof_cajeado_riel` = 2.5 **por el lado del anillo** (bolsillos ciegos en UNA cara: dejan 3.5 mm bajo la cabeza del M4 del riel). Nota de mecanizado, no va en el DXF — ver abajo — **2 uds, PAR ESPEJADO**: mismo contorno, cajeado por caras opuestas. **Planitud ≤ 0.5 mm en 300** en el blank cortado: apoya en la cara mecanizada del anillo y doce M4 lo conforman contra ella (una pletina de 6 × 24 se aplana 0.5 con 200 N), pero con más de eso el acrílico lo nota |
| `cupon_anillo_2d` | **aluminio, pletina de 14 mm** | **mecanizado** (§6.1) | **NO ES UNA PIEZA DEL CASE**: es la SECCIÓN del perfil del anillo, y de ella sale el **cupón de 100 mm** que hay que aprobar antes de cortar los dos anillos — ver el punto de parada en §6.1 |

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
- **`costilla_dorso_2d` — LA CARA INTERIOR.** Trae el **contorno del REBAJE**, a
  `cara_anillo − rebaje_anillo` = 20 − 6 = **14 mm** de la silueta, más los **14
  círculos** de rosca ciega a diámetro de broca. La silueta NO se repite aquí a
  propósito: dibujarla sería mandar cortar el contorno dos veces.

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

**Su canto exterior no va a la silueta en todos los tramos**, y no es un
error de corte: en las tres filas sí (es el borde de aluminio de la fila);
en el frente, el suelo y la meseta va retirado **1.65** (encima va chapa a
ras de la silueta: la nariz y su pie, el pie del talón, la meseta y su
retorno); en la trasera va retirado **11.20** (la banda, la trasera más
gruesa del lote y medio milímetro: delante de un acrílico de ±1.2 no puede
haber nada fijo). El canto interior va a 26 de las aristas del perfil,
recto, en los siete tramos. `taladros_marco_ventana()` en `check_dxf.py`
relee todo esto del fichero.

**LA BRIDA DEL MIEMBRO ALTO Y LA MUESCA DE LA TRASERA.** Las dos bridas
salen de las puntas de la BANDA del miembro alto, dobladas a 90° sobre una
línea perpendicular a la silueta, y apoyan **en la cara del anillo** — no
sobre el marco: se probó subirlas con un escalón y la tapa de arriba pasaba
de abrir 121.5° a 52° (`guarda_tapa()`). Miden **27 × 14.5**, con sus dos M4
a 9.75 y 20.25 del doblez, a 8.5 de la silueta. La trasera, que apoya su
esquina en esa misma franja, lleva una **muesca de esquina de 2 (ancho) ×
15 (alto) con radio 2** en cada esquina de arriba: la brida le pasa por
debajo. Son las únicas dos operaciones del acrílico que no son contorno,
taladro ni cajeado, y el radio no se negocia — el PMMA raja desde una
esquina viva.

**EL TALÓN (`talon_2d`) ES UN ÁNGULO**: banda de **24** a ras del plano
trasero por abajo y pie de **20** sobre la tabla, un doblez a 90° con r = 3.
Blank **540.32 × 42.70**, con la fila de 5 M3 de la trasera a 12 del canto
libre de la banda y tres M4 en el pie a 6.75 de su canto libre (a la tabla,
desde dentro, como la nariz). Sustituye a `miembro_bajo_2d`: sin bridas ni
rosca en el anillo. No se voltea.

**LA NARIZ (`nariz_2d`) LLEVA TRES DOBLECES, y ninguno es a 90°.** Blank
**540.32 × 47.38** con el **canto libre del pie en y = 0** (los tres M4 van a
6.75 de ese canto, que no se mueve al plegar). De abajo hacia arriba, con la
línea en la mitad de cada zona de doblez y el mismo r = 3, k = 0.42: **doblez a
45°** a **17.56** (pie de 18 → chaflán), **doblez a 45°** a **25.17** (chaflán →
frente vertical), **doblez a 35°** a **37.42** (frente → cara de abajo, que se
inclina `angulo_inferior` = 35° desde la vertical). Los BD son **0.88** para
cada 45° y **0.62** para el de 35°; salen de `doblez_bd()` en el `.scad` y de
`_bd_angulo()` en el budget, no de una tabla. Los tres dobleces van **hacia
dentro** del case, y la pieza no se voltea: el pie queda sobre la tabla y el
chaflán mira al suelo.

**Y `miembro_alto_2d` ES UNA L desde el 2026-08-29 por la noche**: la banda
de **24** (con su canto libre en y = 0 del blank y la fila de 5 M3 de la
trasera a 12 de él), la meseta de **50** (del pico al plano trasero, con las
16 ranuras de salida) y el retorno de **4 a 45°** en el pico. Blank **588.00 ×
73.83**: dos dobleces a 90° (banda → meseta, y cada brida) y uno a 45°. La
línea del retorno va a **3.56** del canto libre de la meseta (4 − 0.88/2); la
de la banda a la meseta, a 24 − 3.30/2 = **22.35** del canto libre de la
banda. Las dos bridas sobresalen **23.70** por cada punta de la banda (27 −
BD), de 1.5 bajo la meseta hacia abajo, 14.5 de alto. Sale el retorno de 24
del canal de la mañana: la trasera vive donde él iba.

**LAS SEIS ESQUINAS DEL ANILLO MIDEN `radio_chapa` = 4.5**: el radio
exterior de un doblez de r = 3 en chapa de 1.5, porque en todas dobla chapa
encima — las dos del chaflán de la nariz y el arranque de la cara de abajo,
el pico del techo (el retorno), la trasera-alta (la banda del miembro alto)
y, desde el 29-08 por la noche, la trasera-baja (la banda del talón, que
dobla ahí sobre la tabla; `radio_trasero` murió). No es gusto: una esquina
viva del anillo bajo un doblez a 90° asoma 1.9 mm por fuera de la chapa. La
esquina de abajo-delante es un **chaflán de 6 a 45°** (`chaflan_nariz`). Lo
relee `anillo_tiene_chaflan()` del DXF.

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
superficie horizontal entre las dos filas de módulos. Cambió de material
porque el 70 % de su fondo está en voladizo —vuela 23.24 mm a cada lado de
su larguero— y en PMMA de 5 fluía a 90 N, con lo que era la pieza más floja
del case y a la vez donde se apoya quien se levanta.

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
satinado, §6.1) y tampoco lleva recocido ni diamantado.

### 6.1 Taller de mecanizado: el anillo

**Taller nuevo desde el 2026-08-28.** Hasta esa fecha la costilla era chapa
de aluminio plegada y entraba en el pliego de chapa; el render de esa pieza
se leía «como un sándwich de aluminio envolviendo el acrílico» y Samuel lo
rechazó. El anillo que la sustituye no se pliega ni se suelda: es una pletina
maciza, vaciada por el centro con fresadora CNC.

- **Material y blank.** Pletina de aluminio de **14 mm** de espesor
  (`t_anillo`). Blank aproximado **330 × 270 mm** (spec de diseño §9; el
  contorno real mide 307.4 × 256.2 mm, `costilla_2d`, con margen de sujeción
  y desbaste).
- **SON DOS PIEZAS ESPEJADAS, uno derecho y uno izquierdo.** Mismo contorno y
  misma ventana; el **rebaje, el chaflán de la ventana y las 14 roscas ciegas
  van en la cara OPUESTA de cada anillo**, porque la cara vista de cada uno
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

  **Qué se mira cuando vuelve, y qué pasa si falla:**

  | # | Qué se comprueba | Criterio | Si falla |
  |---|---|---|---|
  | 1 | El chaflán se lee como en la foto de referencia | 1.5 ± 0.2 a 45°, continuo y sin escalones de faceta, mirado con la misma luz y al lado de la referencia impresa | Se cambia `chaflan_anillo` (rango ESTIMADO 1–3), se reexporta la sección y se pide otro cupón |
  | 2 | El rebaje asienta el PMMA del lote | Con el recorte **más grueso** del lote (8 + 1.2 = 9.2) más la junta de 1 tiene que entrar en los 11 de fondo y **sobrar 0.3**; con el **más fino** (6.8) la junta todavía tiene que precargar | Se sube `t_anillo` — la puerta `guarda_rebaje()` ya dice que con 12 el rebaje quedaba a −0.2, o sea que no cabía |
  | 3 | El anodizado no interrumpe el PE | **≤ 0.1 Ω** medido a cuatro hilos entre el punto enmascarado y un tornillo M4 apretado en la rosca ciega (spec 2026-08-27 §3.4) | El enmascarado no valió: se rehace el punto y se vuelve a medir antes de anodizar los anillos |

  Las cotas **en el plano** (cara vista y ancho del rebaje) no hacen falta
  medirlas aquí: las cruzan `anillo_tiene_ventana()` y `anillo_tiene_rebaje()`
  contra los ficheros que se cortan, en cada corrida. Lo que el cupón cierra
  son las **tres profundidades** y el **acabado**, que ningún DXF de planta
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

`bandeja_base_2d`, **madera maciza de 18 mm, 588.62 × 327.41** (creció desde
570.62 × 328.94 el 2026-08-28: el anillo es más grueso que la vieja costilla
de chapa y la tabla vuela `vuelo_zocalo` = 10 mm más allá de él por los cuatro
lados). Es el suelo interior del case **y** el zócalo que sobresale: una sola
pieza. El cuerpo se le apoya encima y las cuatro paticas van atornilladas por
debajo.

**La veta corre a lo largo** (los 588 mm). No es decoración: fija en qué
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
- **Apriete de los 20 M3 sobre acrílico: 1.0 N·m, con arandela ancha d16 y ROSCA SECA.**
  Engrasar la rosca baja el coeficiente par-precarga de 0.2 a ~0.15, o sea
  que el mismo par mete un 30 % más de precarga — y sobre acrílico eso
  fisura. Destornillador dinamométrico, no muñeca.
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
| tapa del valle, aluminio 3 mm | `t_valle` | `guarda_valle()` |
| anillo: espesor 14, cara 20, rebaje 6, rehundido 3, chaflán 1.5 × 45° | `t_anillo`, `cara_anillo`, `rebaje_anillo`, `rehundido_acrilico`, `chaflan_anillo` | `guarda_anillo()`, `guarda_rebaje()` |
| roscas ciegas del anillo, broca M4 3.3 / M5 4.2 | `d_M4_rosca`, `d_M5_rosca` | `guarda_anclajes()`, `taladros_anillo()` |
| junta de asiento EPDM 1 mm | `t_junta_asiento` | `guarda_rebaje()` |
