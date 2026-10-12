# La piel orgánica: un árbol sobre el hueso — el tronco y las dos ramas

> **Sucedida el 2026-10-11** por [`2026-10-11-case-persiana-design.md`](2026-10-11-case-persiana-design.md). D-P1 nunca se firmó; D-P2 la retiró D-S2 de la persiana. Sus guiones salieron del repo con la persiana; quedan en el historial.

**Fecha**: 2026-09-05 · **Estado**: **propuesta**; **D-P2 firmada en conversación el 05-09** (*«todo el acabado se hace con impresión 3D»*); **la filosofía dicha por Samuel la misma noche**, mirando la tercera celosía ya impresa en STL: *«toda esta pieza simula un árbol. los cachetes son como ramas (las ramas deberían tener una estructura natural de rama) [...] se interpreta como una rama con extensiones, todo lo que envuelve al aluminio se comporta como un tronco. hasta que no entiendas esto no lograremos el acabado que queremos para la piel 3d»*; y el origen de la rama: *«quiero que el punto del que salen todas las ramificaciones sea la punta inferior delantera»*. D-P1, D-P3, D-P4, D-P5, D-P6 y D-P7 sin firmar (§12) ·
**Sucede a**: nada; **se apoya en** `2026-08-28-costilla-pletina` (el anillo), `2026-08-29-trasera-capturada-talon-nariz` (la trasera, que se queda), `2026-08-30-techo-macizo-chapas-empotradas` (el techo, que se va), `2026-08-31-case-tanda-b` (las tres filas, que no se tocan) y `2026-09-05-fuente-v5-ladrillo` (la fuente afuera, que este papel reabre en §7.1) ·
**No toca**: la silueta, los ángulos, las tres filas, los Z-Rails, el marco de la ventana, los paneles rehundidos, la tabla, el ámbar ·
**Referencia visual**: seis imágenes generadas por Samuel el 05-09, en `docs/images/case-piel-organica/`. **Mandan sobre lenguaje, no sobre cotas** — la misma regla que el board del 16-08 y la foto del 26-08. Samuel, sobre las tres primeras: *«lo que está en los paneles es conceptual pero se entiende que va con el diseño que estamos haciendo, lo del valle seguimos trabajándolo como veníamos [...] son módulos de la fila B»*; sobre la sexta: *«ahí tienes más o menos la idea de las formas de las ramificaciones en los cachetes»* ·
**Modelo**: `case/cad/celosia.py` → `celosia_rama.json` (la rama), `case/renders/imprimir_piel.py` (las piezas en 3D, listas para imprimir, en `case/print/piel/`), `case/cad/piel_organica.scad` (la lámina base de la cubierta y lo que sigue igual), `case/cad/piel_termica.py` (la chimenea), `case/renders/render_piel.py` → `sam17-piel*.png`.

> **ENMIENDA (2026-10-09, acta «SAM17 de cerca»).** Este papel describe la rama del 05-09, y desde entonces pasaron dos cosas. **La celosía cambió** el 07-09: el cachete es la PLACA PERFORADA del concepto (`celosia_placa.py` → `celosia_placa.json`, §4.1). Y **el 09-10 Samuel firmó las 16 fichas de una revisión del modelo** (el acta está publicada en https://claude.ai/artifact/JBqb4yagaAuZyBmBdgriin, con su imagen y su decisión por ficha). Las tres consecuencias que cambian este papel:
> 1. **La piel es una sola masa** (ficha 7, A). El marco del cachete desaparece: el borde de la cubierta se enrolla sobre el costado y la celosía sale de debajo. Abajo, donde la cubierta no puede llegar porque se pone bajando, el borde lo pone una base del cachete, a inglete con la cubierta (§13.2).
> 2. **La piel impresa tiene dos reglas que la revisan** (ficha 16): una isla por pieza y ninguna pieza dentro de otra. Con ellas se vio que el cachete del 09-09 salía en siete piezas sueltas, se metía 5,9 mm en la tabla y pisaba la cubierta en todo el borde (§13.1).
> 3. **D-P4 está cerrada** por D-V1, firmada en el papel de la fuente v5 el 2026-09-08: la fuente va afuera (§7.1).
>
> Modelo desde el 09-10: `celosia_placa.json` (la celosía), `case/cad/piel_borde.py` → `piel_borde.json` (el borde), `imprimir_piel.py` (las piezas), `case/renders/piel_choques.py` y `check_piel.py` (las dos reglas; esta última es una puerta de `gates.py`). Lo que cada ficha decide y en qué estado está, en §13. Las secciones que esto deroga llevan su enmienda encima.

---

## 0. En una línea

El case de hoy es **dos anillos de aluminio fresado** —el hueso— con **seis pieles** encima: el techo de chapa, la nariz, el talón, las dos mejillas de acrílico en bolsillo, y la trasera de PMMA. Esto cambia **cinco de esas seis pieles por un árbol impreso**: la **cubierta es el tronco** —una masa con corteza, de una pieza, que envuelve el canto— y **cada cachete es una rama** que sale de él por la punta inferior delantera y abre sus extensiones sobre el costado. El hueso y la trasera se quedan donde están.

Lo que compra no es estética: **la ventilación deja de ser un agujero que esconder y pasa a ser la identidad del aparato.** Con los cachetes abiertos, el case pasa el techo de 20 K con el `C_D` de la puerta y la fuente afuera; **con el pesimista se queda a 0,9 K**, y ese margen es un parámetro de la rama, no una pared (§4.3).

---

## 1. El concepto, leído como plano

Seis imágenes. Lo que en ellas es decisión y lo que es ruido del generador lo dijo Samuel, y se transcribe arriba.

| imagen | lo que enseña | lo que de ahí se toma |
|---|---|---|
| `concepto-1-ambar.jpg` | piel blanca orgánica, mejillas en celosía abierta, dos caras de acrílico ámbar, base de madera, una barra entre los dos pisos | la piel, la celosía, la madera. El ámbar en las caras **no**: la imagen 2 lo mueve |
| `concepto-2-paneles.jpg` | las caras pasan a **paneles de aluminio oscuro** con los controles reales; el ámbar queda **dentro**, como luz por la celosía; tres bloques separados en el panel de abajo | los paneles de aluminio; el ámbar como interior; **los tres bloques son módulos de la fila B** (Samuel). La barra: es el valle, y el valle sigue como venía |
| `concepto-3-trasera.jpg` | atrás: acrílico ámbar con el KONDOR en relieve y las ondas; debajo, una franja de metal con los conectores; debajo, la rejilla de ranuras; un IEC a la derecha. **La cubierta con pliegues, como una manta gruesa** | **la trasera se queda** —es la del 29-08, en ámbar—; la franja de conectores en metal (§5); las ranuras se quedan (§7.3). **El IEC es una decisión, no un detalle** (§7.1). Y la cubierta es masa, no lámina |
| `concepto-4-despiece.jpg` | el despiece: **el cachete lateral esquelético** como pieza suelta con orificios de montaje y puntos de enganche; **la cubierta superior envolvente** drapeada, aparte; el hueso en dorado | el cachete como pieza atornillada al anillo (§9.1); la cubierta como pieza aparte (§8). Samuel: *«esto es lo que necesitamos [...] queremos tener las piezas listas para mandarlas a imprimir en 3D»* |
| `concepto-5-cachete-2d.jpg` | **el perfil 2D del cachete**, vista interior y exterior: un nudo del que sale todo, una vena principal en diagonal, extensiones largas hacia la cumbre y cortas hacia el suelo, marco grueso y redondo, **cuatro fijaciones en las esquinas**, todo de sección redonda con unas pasando sobre otras | **la estructura de la rama** (§4.1), el marco de almohada, las cuatro fijaciones (§9.1). El nudo lo movió Samuel a la nariz al ver el primer render 3D |
| `concepto-6-celosia-2d.jpg` | **la geometría de la celosía**: «variable core thickness», «filament bifurcation point», «integrated nodal point», «irregular void shape», «interwoven flow path», y el cruce entretejido | **el lenguaje de cada fibra**: grosor variable a lo largo, haces que se juntan y se separan, lentes con punta, cruces con una fibra por encima (§4.1). Su escala daría filamentos de 2 mm: no manda sobre cotas |

**Lo que las seis dicen juntas es una sola cosa, y hasta la cuarta celosía no la entendí**: la piel es un **organismo**, no un patrón. El tronco es masa con corteza y de una pieza; la rama entra gruesa por un punto, se parte y se afina hacia las puntas, y tiene relieve. Tres celosías en un día —celdas, ramas dibujadas, fibras— eran tres dibujos planos del mismo sitio.

---

## 2. Lo que cambia en el case firmado

| | pieza | papel | qué le pasa |
|---|---|---|---|
| **se va** | techo de chapa + rendija del alero | 30-08 | la cubierta es el techo. La salida de aire son los cachetes |
| | nariz y talón | 29-08 | la cubierta es la nariz y el talón |
| | mejillas de acrílico en bolsillo | 28/29-08 | la rama es la mejilla, y respira |
| | **todo el venteo del #289** | 03/04-09 | lo pagan las ramas (§4.3) |
| **se queda** | la silueta de dos pisos, las tres filas, el valle de 55 | 31-08 | igual |
| | Z-Rails, marco de la ventana, paneles rehundidos 1,5 | 29/31-08 | igual |
| | **la trasera**: PMMA, KONDOR, ondas, ranuras, capturada en bolsillo | 29-08 | igual, con la franja de conectores debajo (§5) |
| | la tabla del carpintero, con su vuelo de 10 | 27-08 | igual; **los cachetes asoman ahora 6 mm por fuera de ella**. *Desde la ficha 12 (10-10): una losa de 30 que vuela 40, y es ella la que asoma de la piel (§13.8)* |
| | el ámbar | 27-08 | se queda, pero **dentro**: es la trasera y lo que se ve por la rama |
| **cambia** | los dos anillos | 28-08 | siguen siendo el hueso. Bajo la piel no se ven, y pasan a **pletina cortada y listo** (§6) |
| | el chasis del PSU | 18-08 | con la fuente afuera (v5) no hay chasis. Si se queda dentro, entra como hoy, por el frente |

El case crece **32 mm de ancho** (16 de rama por lado: 568,62 → ~601) y la cubierta con su corteza es 590 de ancho por 341 de fondo; en alto, los pliegues (hasta +7) y nada más.

---

## 3. La piel

### 3.1 Geometría (lo que está en el modelo)

**La cubierta, el tronco** (`piel_organica.scad` → `imprimir_piel.py`):

- **Lámina de 6 mm** (`piel_e`) que sigue el contorno del anillo (`perfil_lateral()`) 6 mm por fuera, de nariz a talón pasando por el techo, **de una pieza**. Por debajo no hay piel: ahí está la tabla (`piel_aire` = 0,3 sobre y = 0). Es una **C abierta por abajo**: se pone y se quita cayendo desde arriba (§8).
- **Los labios de los extremos** pisan cada panel hasta la placa de anclaje y **no más** (`piel_solape` = `t_placa` = 6): 20 mm sobre cada extremo de cada fila. Entre los labios la banda se abre entera sobre las tres filas; entre filas están la tapa del valle y los rieles. **La ventana de la trasera**: el campo visible de hoy (`trasera_campo()`).
- **La corteza**, puesta en Blender solo sobre la cara exterior (la interior sigue lisa contra el hueso): tres capas de ruido desplazando la malla — **pliegues** anchos como una manta (escala 58 mm, de −3 a +7), **vetas** largas a lo largo del perfil (estiradas ×4 en el plano del perfil) y **grano** fino. Es lo que hace que lea a tronco y no a lámina; ±3 (el primer intento) era piel de naranja.
- Los paneles quedan **7,5 mm** dentro del plano de la lámina (6 de piel + 1,5 de rehundido).

> **ENMIENDA (2026-10-09, fichas 1 a 5, 7 y 11).** Lo que sigue describe la rama del 05-09 y su marco de almohada, y ya no es el modelo. Hoy el cachete es la placa de `celosia_placa.json` (3 mm, apoyada en la cara del anillo, los 34 huecos del concepto) más la BASE de abajo; no tiene marco ni tornillos por fuera, y la cubierta lo tapa con su borde enrollado (§13.2). Los cuatro M4 de las esquinas se van: las fijaciones van por dentro (ficha 11).

**El cachete, la rama** (`celosia.py` → `celosia_rama.json` → `imprimir_piel.py`):

- **El marco**: sección de **almohada** —plana contra el anillo, abombada hacia fuera— de 28 de ancho por 11 de alto, barrida por el contorno: **6 mm por fuera del perfil**, pisando el canto de la cubierta como en el despiece, y **22 por dentro**, tapando la cara del anillo (20) y casi el marco de la ventana (26). Las fibras nacen del marco, sin franja de aluminio entre medias.
- **Cuatro pasantes Ø4,5 para M4** en las esquinas, a 12 mm de los dos cantos (la imagen 5), sobre la cara del anillo.
- **Las fibras**: tubos de sección redonda y **diámetro variable** — 8 junto al nudo, 3,6 en las puntas, la vena ×1,5 —, ondulando **en profundidad** (±1,8, la vena +2,6 por encima) para que en cada cruce una pase por encima de la otra. Todo fundido con el marco por remallado (vóxel 0,6): las uniones salen con garganta.
- **Dos piezas espejo** (`cachete_der`, `cachete_izq`): la cara plana va contra el anillo y la abombada fuera, así que la otra mano es la pieza reflejada, no la misma.

### 3.2 Material: la única pregunta de estructura (D-P2 — firmada)

> **Firmada el 05-09, en conversación:** *«eso toca decidirlo, todo el acabado se hace con impresión 3D»*. Es **A**. La piel se imprime, y **la pieza impresa es el acabado**: no hay fundición, no hay mecanizado de la piel, y lo que salga de la máquina es lo que se ve. Eso convierte el material en el siguiente parámetro —blanco de impresión (PA12 W) o teñido, resina o nylon— y hace de las preguntas de §8 ingeniería con proceso conocido en vez de opciones. B se queda escrita abajo como lo que se descartó y por qué, no como alternativa viva.

**A. La piel es piel.** Nylon impreso (SLS/MJF PA12, o resina) sobre los anillos de hoy, que se esconden. La estructura no cambia: los anillos cargan, el marco de la ventana ata los rieles, la piel se cuelga de ellos. Riesgo cero en lo que ya está calculado. Los paneles de aluminio hacen de disipador (§4.4).

**B. La piel es aluminio fundido** y hace de hueso y de disipador a la vez. Más pesada, molde, más cara — y la versión de serie si algún día hay serie.

**Recomendación: A**, para la pieza de concepto y como base. B se decide con una unidad vendida, no antes. Y con A hay una cosa que no se puede olvidar: **a 45 °C de sala más 15–20 K dentro, un nylon impreso aguanta como piel y no como estructura**. Por eso A exige que el hueso siga.

---

## 4. La rama

### 4.1 Cuatro versiones en un día, y por qué la cuarta es otra cosa

> **ENMIENDA (2026-10-09).** Después de la cuarta hubo cuatro más, el 06 y el 07-09: la lámina KONDOR regenerada por estadística (`celosia_kondor.py`, *«caótica»*), el calco del cachete del concepto (`celosia_calco.py`: la organización sí, pero *«costillas»*), el ala de cinta fina (`celosia_ala.py`) y la **placa perforada** (`celosia_placa.py`): la máscara de material del cachete del concepto llevada tal cual a nuestro perfil, 34 huecos deformados con el mismo campo que el calco, relieve B (cada banda baja de 3 mm en su centro a 1 mm en el borde del hueco) y los huecos crecidos 0,3 mm por lado para la térmica. **Es la que aprobó Samuel el 07-09 y la que se imprime.** Dos cosas a saber de ella: las trazas del vectorizer de las que sale (`D:/Desktop/cachete_placa.json` y compañía) ya no están en el Desktop, así que `celosia_placa.json` es la única copia; y dos de sus huecos (el 5 y el 32) se solapan 0,5 mm² desde que crecieron, lo que obliga a cortarlos con el booleano que admite cortadores cruzados (`imprimir_piel.placa()`).

Del dibujo orgánico importan tres números —cuánto abre, cuánto nervio le queda, cuánto borde macizo la enmarca— y los tres tienen que ser **parámetros**, porque el primero lo lee el modelo térmico y los otros dos los leerá la rigidez. Un dibujo no tiene parámetros.

1. **Celdas de Voronoi** (`2bce743`): parametrizable, medible, y **leía a panal**.
2. **Ramas por colonización de espacio** (`d78c592`): un árbol dibujado, ramas sueltas que se cruzan. *«No está ni cerca.»*
3. **Fibras de un campo de flujo** (`73a9bf1`): el tejido bueno —nervios largos que se abanican, se parten y se juntan en lentes— pero **fibras todas iguales, planas, sin nudo y sin tronco**. Samuel, con el STL delante: *«le hace falta mucho detalle de relieve tanto a los cachetes como a las bandas y el problema más grave empieza por una falta de conexión con la filosofía»*.
4. **La rama** — ésta. El mismo motor de líneas de flujo (Jobard & Lefer, 1997) pero con lo que un organismo tiene y un patrón no:

- **Un nudo en la nariz, tres ramas de él, y el resto brota más arriba.** El campo es **radial desde la punta inferior delantera** (`NUDO` = (56, 38), a ~10 mm del marco en la esquina de la nariz), ligeramente torcido y ondulado. Del nudo salen **tres primarias** (`PRIMARIAS`: el suelo a 2°, la vena a la cumbre a 39°, la cara baja a 54°), gruesas (×1,3; la vena ×1,5), fundidas en el nudo y el nudo con la esquina del marco: por ahí la rama sale del tronco. **Las demás nacen de una rama que ya pasa por la banda de la fila de abajo** (`BROTE_Y` = 28–150 mm de alto): hacia atrás, una fibra nueva muere al acercarse a su madre (`MUERE_ATRAS` = 0,6 del espaciado) y la punta se funde en ella con una Y tendida a lo largo de la madre (`SOLDADURA_L` = 2,5 huecos). Samuel, al ver el primer render con todo saliendo del nudo: *«mejor que salgan varias de ese nodo, unas tres, y luego otras nazcan de algún punto más arriba, cada una en donde va el primer row del rack»*.
- **Jerarquía de grosor**: el diámetro cae con la distancia al nudo (8 → 3,6 mm, `LAMBDA` = 95) y sube y baja a lo largo de cada fibra (`GROSOR_ONDA` = 0,18: gruesa a media carrera, fina donde se parte — «variable core thickness»). La **vena** —la diagonal larga, de la nariz a la cumbre trasera, `VENA_ANG` = 39°— va ×1,5 y por encima del plano.
- **Haces y bifurcaciones**: las fibras **no mueren por acercarse a otra** (`MUERE` = 0). Se funden en un haz y, cuando la modulación las separa, se abren: eso es la bifurcación de la imagen 6, y hacia el nudo hace que todas se junten en pocos brazos gordos sin dibujarlos. La densidad la gobierna solo el sembrado: una semilla vale si no hay fibra a menos de `NACE` = 0,62 del espaciado local (`SEPARACION` = 12 junto al nudo, creciendo un 25 % a 250 mm).
- **Lentes por pellizcos**: dos fibras que corren vecinas se acercan hasta tocarse cada `LENTE` (95 mm, local) y se vuelven a abrir, con ventana coseno y sin tocar las puntas. Deja huecos con las dos puntas tangentes. Antes eran puentes en S entre fibras, y salían como rayos en zigzag.
- **La pared**: cerca del marco el flujo se hace tangente (`PARED_D` = 40, `PARED_K` = 0,9), y las fibras corren pegadas al marco antes de fundirse en él **de refilón**, con una curva tangente que termina medio marco dentro. Sin esto, las que salen del nudo hacia el hombro chocaban de frente a 20 mm y morían cortas.
- **Relieve en Z**: cada fibra ondula ±1,8 mm en profundidad (`Z_L` = 90), así que en cada cruce una pasa por encima de la otra — el «interweave intersection» de la imagen 6.

Salen **19 fibras —3 primarias y 16 brotes—, 13 uniones en Y y 16 pellizcos**. Todo esto se itera en un **preview 2D de segundos** (`celosia.py --preview`) y en 3D con EEVEE en un minuto (`PIEL_MOTOR=eevee`); Cycles solo para el render que se mira para decidir. Lo que se afina mirando, con Samuel delante: `NACE` y `SEPARACION` (cuántas fibras), `NERVIO_NUDO`/`NERVIO_PUNTA` (cuánta carne), `LENTE` (cuánto miden las lentes), `Z_AMP` (cuánto relieve).

### 4.2 Dos áreas, y por qué no son la misma

La rama abre desde 28 mm del perfil hacia dentro: eso es **lo que se ve**. Detrás del cachete está el anillo (20 de cara) y el marco de la ventana (hasta `marco_fondo` = 26 del perfil); con el marco de la rama a 22 por dentro del perfil, lo que se ve y lo que respira es casi lo mismo.

| por cachete | mm² | del perfil (52 658) |
|---|---|---|
| **abierto, lo que se ve** (marco y fibras descontados) | **12 654** | **24,0 %** |
| **abierto sobre la ventana y fuera del marco, lo que respira** | **12 654** | **24,0 %** |

Medido por muestreo (120 000 puntos), con cada tramo como cápsula de su diámetro. Las fibras del 73a9bf1 respiraban 19 367: **la rama es un tejido mucho más cerrado**, y eso se paga abajo. (Una versión de este guion contaba como aire la franja entre 26 y 28 del perfil, que la tapa el marco: corregido con `max(ventana, marco)`.)

### 4.3 Lo que le pasa al calor

> **ENMIENDA (2026-10-09).** Con la placa (13 727 mm² respirando por cachete, medidos a 28 mm o más del perfil), `piel_termica.py` imprime hoy:
>
> | escenario | W | salto | pesimista | sin la rejilla trasera |
> |---|---|---|---|---|
> | v5 declarada, fuente afuera | 64,2 | 17,9 K | **20,0 K** | 20,2 K |
> | v5 a censo | 35,1 | 11,9 K | 13,3 K | 13,5 K |
> | fuente adentro | 89,2 | 22,2 K | 24,9 K | 25,2 K |
>
> **Pasa el pesimista con cero margen** (bastan 13 678 y respira 13 727). Los 64,22 W se comprobaron contra `ladrillo_budget.py` de main el 09-10 y siguen vigentes. El borde enrollado del 09-10 tapa el costado hasta W (de 21 a 28 mm según la altura) y el marco de la ventana del anillo llega a 26: la cuenta, hecha a 28, no baja con él. Lo que sí la movería es la ficha 9 (más fondo en la celosía) y la 10 (una placa ámbar detrás), y por eso las dos se deciden con la chimenea delante.

`case/cad/piel_termica.py` — la misma física que `clearance_budget._tiro()`, con las dos mejillas como chimenea: la mitad baja de cada una entra, la mitad alta sale, centroides a un cuarto y tres cuartos del alto; más la rejilla baja de la trasera. Techo, 20 K sobre una sala de 45 °C. `C_D` = 0,65 el de la puerta, 0,55 el pesimista. **La tabla la imprime el guion; no se copia a mano** (el 05-09 la misma resta de dos columnas se hizo mal tres veces).

| escenario | W | salto | pesimista | sin la rejilla trasera |
|---|---|---|---|---|
| **v5 declarada, fuente afuera** | 64,2 | **18,7 K** | **20,9 K** | 21,4 K |
| v5 a censo | 35,1 | 12,5 K | 14,0 K | 14,3 K |
| **fuente ADENTRO** (v5 + los 25,02 que se irían) | 89,2 | **23,3 K** | **26,1 K** | 26,6 K |

Área efectiva **10 650 mm²**, tiro **134 mm**. Para pasar el pesimista con la fuente afuera hacen falta **13 678 mm² respirando por cachete**: un 8 % más que ahora.

Tres lecturas:

1. **Pasa con el `C_D` de la puerta y no con el pesimista**, por 0,9 K. Las fibras del 73a9bf1 pasaban las dos (14,6 / 16,3 con este mismo guion): la rama cambió margen térmico por leer a rama. **Es un parámetro, no una pared**: con `NACE` = 0,62 en vez de 0,55 salen 12 fibras, respiran 15 557 y da 16,6 / 18,5 K — pasa las dos con un 14 % de margen. Se decide mirando, porque también cambia cómo se ve: 12 fibras es más rama y menos tejido.
2. **La rejilla baja de la trasera vale 2,7 K** (18,7 con ella, 21,4 sin ella, mismo `C_D`). Se queda o se va por identidad (§7.3), sabiendo lo que cuesta.
3. **Con la fuente adentro no pasa ni con el `C_D` de la puerta** (23,3 K). Ver §7.1: con esta rama, la fuente afuera deja de ser una opción y pasa a ser condición.

Lo que el modelo NO cuenta y se declara: la pared exterior (`U_PARED` = 3, sin medir, fuera del veredicto); el `C_D` de un hueco entre tubos redondos de nylon (no es el de una ranura en PMMA; probablemente **mejor**, porque la celda es ancha respecto a su profundidad — pero sin medir); y la resistencia de un camino de aire que entra por un extremo, cruza 540 mm de módulos y sale por el otro. Es una aproximación de orden de magnitud. **Se mide en el paso 7 del bring-up, como todo lo demás.**

### 4.4 Y los paneles de aluminio, de regalo

De los 64,2 W declarados, **27,5 están concentrados** en dos o tres placas —los convertidores DC-DC (8,0), la quema de la cascada (5,1) y los cuatro N657 (14,5)— y **36,7 repartidos** en dieciséis placas de voz, la fila de abajo y la pantalla. Lo repartido va por aire. Lo concentrado se puede **atornillar a metal**, y con los paneles de aluminio del concepto el metal ya está: del orden de 0,2 m² a la vista *(ESTIMADO)*, suficiente para sacar esos 27,5 W por conducción a 30 K sobre la sala con h = 6. Los dos caminos a la vez, ninguno forzado. **No está en el modelo** y no se cuenta en §4.3: es margen.

---

## 5. La trasera

Se queda tal cual está firmada el 29-08: PMMA capturado en los bolsillos de los anillos, KONDOR en relieve, las dos ondas, las 46 ranuras. En el concepto aparece en ámbar y no en PMMA claro o ahumado: color de mirar, no cota; el `.scad` no lo fija.

Lo que el concepto añade y tiene sentido: **una franja de metal con los conectores, debajo del acrílico.** Es lo que pedían los hallazgos del 23-08 —los conectores en metal, no en el PMMA— y parte la trasera en dos materiales con dos trabajos: arriba lo que se enseña, abajo lo que se enchufa. No está modelada: es una enmienda al papel de la trasera cuando esto se firme, no un dibujo de este.

**El IEC del render no está decidido.** Con la fuente afuera (v5) ahí va un jack de DC. Con la fuente adentro, un IEC. Es D-V1, y §7.1 dice lo que este case le hace.

---

## 6. El hueso

**Sigue.** Los dos anillos cargan; el marco de la ventana ata los seis rieles y retiene hacia dentro; los Z-Rails llevan los paneles. Nada de eso lo toca la piel.

Lo que sí cambia es **lo que el anillo tiene que ser**. Hoy es pletina de 14 fresada —cara vista de 20, rebaje de 6 donde asienta el acrílico coplanar, chaflán de 1,5 × 45° en las dos aristas, bolsillos cerrados para las tres planchas— porque **se ve** y porque **sujeta piel de acrílico**. Bajo la piel no se ve, y el acrílico de las mejillas ya no existe. Se queda con dos trabajos: cargar, y sujetar la trasera en su bolsillo. Para eso basta **pletina cortada** —láser o agua— con el bolsillo trasero y **las cuatro roscas M4 por esquina** para el cachete; sin chaflán, sin rebaje perimetral, sin cara vista. El hueso se abarata justo cuando la piel se encarece, y el taller de mecanizado del §6.1 del PLIEGO pasa a ser un corte.

---

## 7. Lo que esto reabre

### 7.1 D-V1: la fuente afuera, con este case

> **ENMIENDA (2026-10-09).** D-V1 se firmó el 2026-09-08 en `2026-09-05-fuente-v5-ladrillo-design.md`: la etapa AC-DC es pieza de catálogo certificada, fuera de la caja. Con eso **D-P4 queda cerrada: la fuente va afuera**, y lo de abajo se queda como la razón térmica que la apoyaba.

La v5 sacó la fuente por cuatro razones, y esta piel **toca una**:

| razón | con la rama |
|---|---|
| térmica: la caja no evacuaba | **con la fuente adentro no pasa**: 23,3 K con el `C_D` de la puerta, 26,1 con el pesimista, contra 20. Abriendo la rama un 8 % pasa el pesimista **con la fuente afuera**; para pasarlo con la fuente adentro haría falta respirar del orden del doble, y eso ya no es la misma rama |
| el recinto de acero ocupa el 30 % del suelo | entera |
| la red de 230 V fuera de una caja de madera **y ahora de nylon** | entera, y más |
| el margen de U2 que se regala solo con el crudo a 15,5 | entera |
| un ladrillo de catálogo es lo práctico de fabricar | entera |

Así que el IEC del render **es una decisión que Samuel toma sabiendo el número**: con esta rama, la fuente afuera (jack de DC) es lo único que pasa el techo. Es D-P4, y no la decide este papel.

### 7.2 Tres papeles del case pierden su sujeto

- **30-08, el techo macizo con la salida por el alero**: el techo, la rendija, el labio de 18, los tacos, `guarda_rendija()` y la capilaridad — todo era de una chapa que ya no está. Mueren por desaparición del sujeto. El *criterio* sobrevive: el techo sigue macizo y sigue sin ranuras, porque la cubierta lo es.
- **28-08, la costilla de pletina**: el anillo sigue, el acabado no (§6).
- **29-08, las mejillas coplanares en el rebaje**: no hay mejillas de acrílico. `guarda_costado()`, el vano libre bajo el labio, `hol_costado` — sin sujeto.

### 7.3 El #289 muere, y las ranuras de la trasera cambian de razón

El encargo del #289 —22 244 mm² de venteo nuevo, o 7 610 con la v5— lo paga la rama sola con 10 650 efectivos, y con el `C_D` de la puerta. **Se cierra por desaparición del sujeto** cuando esto se firme. Y las 46 ranuras de la trasera, que eran *la entrada*, valen 2,7 K: se quedan si Samuel las quiere como lenguaje —el concepto las conserva— y se van si no, sabiendo que cuestan eso. Es D-P5.

### 7.4 Los papeles del case, hacia atrás

La spec del chasis (`2026-08-15`) lleva 25 revisiones y este papel sería la 26. `case/README.md`, `PLIEGO.md` y `RFQ.md` cambian de fabricante (§9). Se enmiendan **cuando se firme**, cada uno con su issue e hito, como manda el CONTRIBUTING — y esta vez se ejecutan, porque el repo ya pagó dos veces una tabla de enmiendas sin ejecutar (#331).

---

## 8. Montaje y apertura

> **ENMIENDA (2026-10-09, fichas 7 y 11).** Se queda el punto 1 (la cubierta es una C abierta por abajo y se pone bajando) y el 4 (la máquina, D-P6). **El 2 se invierte**: ya no son los cachetes los que capturan la cubierta, sino la cubierta la que tapa los cachetes. Su borde enrollado cubre la pestaña de cada cachete con 0,6 mm de juego, y al bajar solo barre su propia huella sobre el costado, así que no toca la celosía. **El 3 cambia**: nada de M4 por fuera; las fijaciones van por dentro (ficha 11, a): insertos roscados y tornillos desde el interior, a través del anillo. Sin dibujar: cuántos, dónde, y si el destornillador llega con los módulos puestos (HUECO 9).

Samuel, el 05-09: *«no estoy convencido de partir la banda por la mitad. me gustaría que sea fácil de poner y quitar toda la piel»*. Las dos cosas se contestan con la misma geometría:

1. **La cubierta es una C abierta por abajo y cae desde arriba.** El perfil no tiene voladizo: la cara baja se echa atrás al subir (x₂ = 89 en el entrepiso), el hombro sigue atrás (x₃ = 160), la cara alta más (x₄ = 270) y la trasera es un plomo. Una C rígida que copia ese contorno 6 mm por fuera baja en vertical sin tocar nada hasta asentar, y sube igual. No hay que abrirla, ni flexarla, ni deslizarla por el ancho.
2. **La cubierta no lleva tornillos: la sujetan los cachetes.** El marco de cada rama pisa 6 mm el canto de la cubierta (`SOLAPE_CUBIERTA`), así que con los dos cachetes puestos la cubierta queda **capturada** entre ellos. Quitar la piel entera son los ocho M4 de los cachetes y levantar. Poner: cubierta, cachetes, ocho tornillos.
3. **Los cachetes van al anillo con cuatro M4 en las esquinas**, como la imagen 5. Con tornillos de cabeza moleteada no hace falta herramienta: es D-P7.
4. **De una pieza no entra en una MJF de serie.** 590 × 341 × 268 no cabe en 380 × 284 × 380 (HP 5200); cabe en una SLS de gran formato —EOS P 770, 700 × 380 × 580— y sobra en estereolitografía de gran formato (Materialise Mammoth, 2 100 × 700 × 800). Cifras de catálogo, sin hoja en el repo. **Es D-P6**: qué máquina, o si al final se parte y dónde (en un pliegue de la corteza, no en el medio de una cara).
5. ¿Por dónde se abre para llegar a la fila de abajo? Hoy por los paneles; sigue igual — la piel no los tapa.

Lo que no está dibujado: los **puntos de enganche** cubierta–cachete del despiece (bossas en la cara interior del marco que entren en la cubierta y la centren), y el **cuello** de la cubierta en el canto donde asienta el marco. Son la siguiente pasada, con los STL de esta en la mano (HUECO 1).

---

## 9. Fabricación: cada pieza con quien le toca

| pieza | quién | proceso |
|---|---|---|
| **los dos cachetes** | servicio de impresión (**D-P2, firmada**) | MJF o SLS PA12 W: la pieza impresa **es** el acabado |
| **la cubierta**, de una pieza | servicio de impresión de gran formato (**D-P6**) | SLS PA12 en P 770 o Mammoth SLA |
| **paneles de aluminio** | taller de mecanizado | como siempre se ha querido: tolerancia y canto |
| **anillos** | corte | láser o agua, pletina de 14, con bolsillo trasero y las cuatro roscas M4 por cara. **Ya no fresados** |
| **trasera** | corte láser de PMMA | como hoy |
| **tabla** | el carpintero | como hoy |
| rieles, marco de ventana, tapa del valle | como hoy | |

Hace unas horas se preguntó qué era práctico para un luthier, y la respuesta fue el ladrillo. Esto es la respuesta contraria en la piel y la misma en todo lo demás — y es legítima: **una pieza de concepto para Superbooth se hace justo así**, una piel impresa sobre un hueso de corte y una base de madera.

### 9.1 Las piezas para imprimir

> **ENMIENDA (2026-10-09).** Con el borde de una sola masa (§13.2), `imprimir_piel.py` saca hoy:
>
> | pieza | mm | g en PA12 | cerrada, una isla | cabe en |
> |---|---|---|---|---|
> | `cachete_der.stl` | 319 × 255 × 12 | ~178 | sí | MJF 5200, SLS P 770 |
> | `cachete_izq.stl` (espejo) | 319 × 255 × 12 | ~178 | sí | MJF 5200, SLS P 770 |
> | `cubierta.stl`, con los dos rollos | 593 × 332 × 262 | ~886 | sí | **solo SLS P 770** (D-P6) |
>
> Y `piel_choques.py` las da en verde: ninguna entra en otra más de 0,29 mm (contacto, con la tolerancia de 0,5). Lo que sigue describe el cachete del 05-09.

Samuel: *«queremos tener las piezas listas para mandarlas a imprimir en 3D»*. `case/renders/imprimir_piel.py` las levanta en Blender y las deja en `case/print/piel/`:

1. **La rama**: cada fibra del JSON es un tubo (curva con bisel y radio por punto); el marco es la almohada barrida por su eje con los cuatro pasantes restados (solver *manifold*: el *exact* devolvía un disco con esta barrida); todo se **funde** con un remallado por vóxeles de 0,6 y se suaviza. Y la mano izquierda es la pieza reflejada.
2. **El tronco**: la lámina de OpenSCAD, remallada fina, con las tres capas de corteza sobre la cara exterior, remallada a 0,8 y suavizada.
3. **Comprobado como lo mira un servicio**: cero aristas no-manifold, tamaño contra dos bandejas, volumen → gramos en PA12 (1,01 g/cm³).

| pieza | mm | g en PA12 | cerrada | cabe en |
|---|---|---|---|---|
| `cachete_der.stl` | 331 × 268 × 17 | ~322 | sí | MJF 5200, SLS P 770 |
| `cachete_izq.stl` (espejo) | 331 × 268 × 17 | ~322 | sí | MJF 5200, SLS P 770 |
| `cubierta.stl` | 590 × 341 × 268 | ~876 | sí | **solo SLS P 770** (D-P6) |

**No llevan todavía**: los puntos de enganche cubierta–cachete, el cuello de la cubierta, ni tolerancias de ajuste marco–cubierta. Los tres son de la siguiente pasada, con los cachetes en la mano (HUECO 1).

Los STL **no se versionan hasta la firma** (pesan 8–15 MB cada uno y cambian con cada pasada de la rama): los regenera el guion en unos minutos, y cuando D-P1 se firme el juego que se manda entra con su commit, como los DXF del láser.

---

## 10. Los renders

> **ENMIENDA (2026-10-10, ficha 14).** Los paneles ya no son placas lisas: `case/renders/cara_panel.py` les pone la cara, y la tapa del valle va en negro (los rieles se quedan plateados, §13.6). Hay una vista más, de frente puro, para juzgar el reparto: `PIEL_VISTAS=cara` → `sam17-piel-cara.png`. No se versiona (la regla de la #195 en `.gitignore`); está en el acta. Lo que eso pinta y lo que es provisional, en §13.6.

`case/renders/render_piel.py` reutiliza la escena de `render.py` entera y hace cuatro vistas: las dos de siempre, una **casi de lado** (`sam17-piel-lado.png`) y una **de lado puro** (`sam17-piel-cachete.png`), en la que el cachete llena el cuadro y se juzga la rama. Importa **la piel tal como se imprime** (`case/print/piel/`), no un extruido: lo que se ve es lo que sale de la máquina. `PIEL_MOTOR=eevee` para iterar en un minuto; `PIEL_BLEND=1` guarda `build/sam17-piel.blend` con cada pieza nombrada para girarla en Blender.

Lo que enseñan: la cubierta blanca con su corteza sobre el hueso, la rama saliendo de la nariz con el anillo asomando detrás en la orilla y el interior en el centro, los paneles oscuros de las tres filas 7,5 dentro de la piel, la trasera en ámbar en su ventana, la tabla asomando.

Lo que **no** enseñan, a propósito: la franja de conectores (§5, no modelada), la fuente (fuera), los puntos de enganche (HUECO 1), y ningún control en los paneles — los paneles son placas lisas, como en `render.py`.

---

## 11. HUECOS

> **ENMIENDA (2026-10-09).** El 1 cambia de forma. El cuello de la cubierta es ahora el hueco bajo su borde enrollado, donde entra la pestaña del cachete, y está dibujado y comprobado (§13.2). Los enganches pasan a ser las fijaciones por dentro, sin dibujar (el 9). El 2 sigue: la rigidez de una placa de nylon de 3 mm y 330 mm de largo está sin calcular. Y entran tres:
>
> 9. **Las fijaciones por dentro** (ficha 11, a): cuántos insertos, dónde, y si el destornillador llega desde dentro con los módulos montados. Sin medir.
> 10. **La holgura bajo el borde** (#398) es de 0,6 mm de dibujo. Después del remallado, la regla de choques mide como mucho 0,12 mm de contacto entre las piezas. Es el juego del modelo, no el de la pieza impresa, que en MJF anda en ±0,3: se comprueba con una pieza.
> 11. **Las dos juntas a inglete** (#398) de abajo son las únicas que se ven. Una arista viva impresa no sale perfecta, y la muestra dirá si la junta necesita un chaflán o un rehundido para leerse como algo hecho a propósito.

1. **Los puntos de enganche y el cuello.** Cómo la cubierta se centra en los cachetes y cómo el marco asienta en su canto: no dibujado (§8).
2. **La rigidez de la rama.** Tubos de 3,6 a 12 mm en nylon, lentes de 15 a 60 mm, un marco de 28 × 11: sin calcular. Es lo que fija `NERVIO_PUNTA`, `NERVIO_NUDO` y el marco de verdad, y hoy son números de mirar. Y un cachete de 322 g colgado de cuatro M4 en un anillo de pletina: sin calcular el arranque.
3. **El `C_D` de un hueco entre tubos redondos** de nylon: sin medir, como todo el `C_D`. Los huecos son lentes, no ranuras.
4. **El polvo.** Dos cachetes abiertos al 24 % dejan entrar más que 46 ranuras. Ya se aceptó para la trasera; aquí es más, y se dice.
5. **El camino del aire por dentro**: el modelo es una chimenea y esto son dos. Orden de magnitud.
6. **La temperatura de la piel**: nylon a 45 + 20 = 65 °C como estructura secundaria (A). El PA12 de SLS/MJF tiene el HDT muy por encima de eso en las hojas, pero **la cifra no está citada aquí a propósito**: va con página cuando la hoja esté en `docs/reference/datasheets/`, no de memoria. Y un HDT no es fluencia: lo que hay que mirar es el creep a 65 °C sostenidos con la piel colgada del hueso, que es carga baja y continua.
7. **La franja de conectores** de la trasera: sin modelar; enmienda al papel del 29-08.
8. **El peso de la corteza.** 876 g de cubierta salen de una lámina de 6 con hasta +7 de pliegue; si la corteza se hace más honda, la cubierta engorda. Es una cuenta del guion, no una cota firmada.

---

## 12. Lo que Samuel decide

> **ENMIENDA (2026-10-09).** D-P4 queda cerrada por D-V1 (§7.1). D-P3 pasa a la ficha 10 del acta: Samuel la quiere ver primero, con la chimenea delante. D-P7 la sustituyen la ficha 7 (una sola masa) y la 11 (fijaciones por dentro). **D-P1 sigue sin firmar**: las 16 fichas la dan por hecha, pero este papel no firma por inferencia.

| | decisión | estado |
|---|---|---|
| **D-P1** | **la piel sustituye a techo, nariz, talón y las dos mejillas** (cinco pieles a un árbol); la trasera se queda | pendiente |
| **D-P2** | material: **A**, piel impresa sobre el hueso de hoy; la pieza impresa es el acabado | **firmada 05-09** — *«todo el acabado se hace con impresión 3D»* |
| **D-P3** | la rama abre sobre la ventana del anillo, interior a la vista (lo modelado) — o lleva el ámbar detrás como panel flotante con paso de aire arriba y abajo | **por ahora, lo modelado**: «sin nada detrás» en la ficha 10 (10-10), y la ficha en «después» |
| **D-P4** | la fuente: afuera (v5, D-V1) o adentro con esta piel — §7.1: **adentro no pasa el techo con esta rama** | pendiente |
| **D-P5** | las 46 ranuras de la trasera: se quedan por lenguaje, o se van (valen 2,7 K) | pendiente |
| **D-P6** | la cubierta de una pieza: **qué máquina** (SLS P 770, Mammoth SLA) — o partirla, y dónde | pendiente |
| **D-P7** | cómo se pone y se quita: cubierta capturada por los cachetes, cuatro M4 moleteados por cachete (§8) — o enganches sin tornillo | pendiente |

Orden: mirar los renders y girar el `.blend` → afinar la rama mirando (cuántos brotes, carne, relieve; y el 8 % que le falta al pesimista) → junta (Serrano sobre lo no verificado; Halberg sobre el nylon a 65 °C; Elke sobre el marco, el labio y cómo se cuelga) → firma → enmiendas de §7.4 en su orden, cada una con su issue.

---

## 13. El acta del 9 de octubre

### 13.1 Lo que encontró la revisión

El 09-10 se miró el modelo en Blender desde 19 ángulos y se midió lo que los renders de presentación no enseñan: en cuántas piezas sueltas sale cada STL y cuánto se mete cada pieza en las demás. Las tres comprobaciones que `imprimir_piel.py` tenía (pieza cerrada, cabe en la bandeja, gramos) daban todo por bueno, y el cachete del 09-09:

- salía en **siete islas**: el marco, la celosía y cinco migas. La celosía empezaba a 28 mm del perfil y el marco acababa a 22 (se había corrido 6 hacia fuera para pisar la cubierta), así que **flotaba** a 6 mm del marco sin tocarlo;
- **se metía 5,9 mm en la tabla** por todo su canto de abajo;
- **ocupaba el mismo sitio que la cubierta**, unos 6 mm, en todo el borde (el «cuello» del HUECO 1, sin dibujar);
- tenía una **costura con escalón** en la nariz, donde empezaba y acababa el barrido del marco;
- y el relieve dejaba **las paredes de los huecos picadas**: empujaba cada vértice por su normal, también los de las paredes.

Además se comparó con las imágenes del concepto, y salieron nueve diferencias de acabado (fichas 7 a 15). Todo está en el acta, cada ficha con su imagen.

### 13.2 El borde de una sola masa (ficha 7, A)

`case/cad/piel_borde.py` → `piel_borde.json`, que levanta `imprimir_piel.py`.

**Qué es.** El marco del cachete deja de existir. El borde de la cubierta se **enrolla** sobre el costado: la lámina de 6 mm llega a la cara del anillo, dobla con una esquina redonda y sigue por el costado hacia dentro como un **labio** que acaba en una **nariz** redonda. Debajo del labio va la **pestaña** del cachete, que es la propia placa (3 mm), con 0,6 mm de juego. La celosía sale de debajo de la nariz: los huecos empiezan a 14 mm del perfil y el labio llega a W, así que las hebras se ven entrar bajo el borde.

**Abajo, la base.** La cubierta se pone bajando (§8), y un rollo por el canto de abajo barrería la celosía al bajar. Así que abajo el borde lo pone el cachete: una **base** con la misma sección que el rollo, apoyada en la tabla. El rollo baja hasta la tabla por delante y por detrás (sus dos patas) y la base va entre ellas, **a inglete**, como las esquinas de un marco de cuadro: detrás a 45 grados, delante más tendido, porque la nariz mide 19 mm y enseguida empieza la pendiente. Son las dos únicas juntas que se ven.

**Las cotas** (constantes de `piel_borde.py`):

| | valor | por qué |
|---|---|---|
| grueso sobre la cara del anillo, T | 12 mm | 11 era el marco que sustituye. Constante: variando de 13 a 9,5 la cara del costado salía inclinada y el remallado la hacía escalera (rayas finas en todo el borde) |
| cuánto entra el labio, W | 28 mm junto a la tabla, 21 en la cumbre | lo que engorda abajo, como un tronco. Siempre tapa la cara vista del anillo (20) |
| esquina de fuera | radio 0,55 T | |
| pestaña | 3 mm, sigue 4 más allá de W | = el fondo de la placa |
| juego labio-pestaña y en los ingletes | 0,6 mm | con 0,3 el remallado lo cerraba (salía −0,47) |

**Tres cosas aprendidas al hacerlo.** *El anillo no tiene los cantos rectos*: `perfil_lateral()` lleva éntasis en las pendientes (hasta 0,76 mm) y radios en las esquinas (4,1 mm en el escalón). La lámina de la cubierta ya lo seguía; el borde nuevo, hecho primero sobre el polígono recto, se metía en el aluminio hasta 4,1 mm. Ahora `piel_borde.py` exporta el contorno real (`PART="perfil_2d"` de `piel_organica.scad`) y trabaja sobre él. *El booleano EXACT devolvía la placa vacía sin error* cuando dos huecos se solapaban; ahora corta con `use_self` y una guarda compara el volumen con el que debería salir. *El espejo del cachete izquierdo* se hacía respecto al origen de la placa (z = 1,5) y lo dejaba 3 mm dentro del anillo; ahora se refleja respecto a z = 0 del mundo.

### 13.3 Las dos reglas (ficha 16)

`case/renders/piel_choques.py` (Blender) y `case/renders/check_piel.py` (la puerta, que recoge `gates.py` por su nombre):

1. **Una isla por pieza.**
2. **Ninguna pieza dentro de otra**: cada pieza de la piel contra las otras y contra la tabla, los anillos y rieles, los paneles y la trasera. Se mide la profundidad, con una tolerancia de 0,5 mm para el contacto cara contra cara (el remallado mueve cada cara hasta medio vóxel). Que un punto esté dentro se decide con la paridad de dos rayos: la prueba rápida, la de la cara más cercana, daba falsos 27 mm junto a las aristas vivas de las ventanas.

Con las piezas del 09-09 sale en rojo con todo lo de §13.1. Con las de hoy, en verde. Sin STL o sin Blender sale HUECO (código 2), no verde: los STL no se versionan hasta la firma.

### 13.4 Las dieciséis fichas

Las fichas 1 a 6 no quedaron guardadas en el acta: un fallo de la página perdía lo que se marcaba antes de que conectara (ya corregido). Samuel dijo *«firmadas todas»* y las seis estaban recomendadas en «hazlo», así que se tomaron así. Si alguna la marcó distinto, se corrige aquí. **El 10-10 las volvió a marcar: las seis, «hazlo».**

| ficha | qué | decisión | estado |
|---|---|---|---|
| 1 | la celosía estaba suelta | hazlo | **hecho**: una isla |
| 2 | el marco se metía en la tabla | hazlo | **hecho**: la base apoya en la tabla |
| 3 | cachete y cubierta en el mismo sitio | hazlo | **hecho** con la 7: 0,6 mm de juego, regla en verde |
| 4 | la costura de la nariz | hazlo | **hecho**: el marco ya no existe; la esquina es un inglete |
| 5 | las paredes de los huecos picadas | hazlo | **hecho**: el relieve solo mueve en Z |
| 6 | rendijas por las que se ve el suelo | hazlo | **hecho** (§13.9): abajo y arriba el borde de la piel cae sobre el riel, y en el valle una tira negra la tapa por dentro |
| 7 | dos tubos donde debería haber uno | una sola masa (A) | **hecho, primera vuelta**: se enseña en render |
| 8 | la corteza parece nieve | enséñamelo primero → veta honda, y luego **«más marcada todavía», en toda la estructura blanca** (10-10) | **hecho** (§13.10): la corteza del concepto, cordones por toda la masa blanca |
| 9 | la celosía no tiene cuerpo | enséñamelo primero → hondo, y luego **«más hondo todavía»** (10-10) | **hecho** (§13.10): `mas_hondo`, 231 g cada cachete; la chimenea no cambia |
| 10 | por la celosía se ve la máquina (D-P3) | enséñamelo primero → **sin nada detrás**, y la ficha «después» (10-10) | no se hace ahora: #392 queda aparcada (§13.7) |
| 11 | los tornillos se veían | por dentro (a) | pendiente de dibujar, #393 (HUECO 9). Los de fuera ya no están |
| 12 | la tabla se quedó corta | hazlo | **hecho** (§13.8): losa de 30, vuelo de 40, canto de arriba redondeado; asoma 28 a 34 de la piel, y una tercera regla lo vigila |
| 13 | la trasera en dos materiales | hazlo | pendiente, #395: depende de la lista de conectores (#183) |
| 14 | rieles negros y paneles vestidos | hazlo | **hecho** (§13.6): la cara en el render y la tapa del valle anodizada en negro. Los rieles se quedan plateados: ya estaban comprados (Samuel, 10-10) |
| 15 | acabado satinado | enséñamelo primero → **después, sin muestra** (10-10) | aparcada: el render sigue mate (§13.10), #397 |
| 16 | una pieza por archivo y ningún choque | hazlo | **hecho**: `check_piel.py` |

### 13.5 Las cuatro de «enséñamelo primero», en render (09-10, noche)

Las variantes se fabrican con `imprimir_piel.py` sin tocar las piezas de `case/print/piel/`: `PIEL_RELIEVE` y `PIEL_CORTEZA` escogen la variante y `PIEL_SALIDA` la manda a otra carpeta, que leen también `piel_choques.py` y `render_piel.py`. La puerta (`check_piel.py`) quita `PIEL_SALIDA` del entorno: mira siempre las piezas de verdad. Todas las variantes pasan las dos reglas, con el mismo peor contacto de hoy (0,29 mm, cubierta contra aluminio). Los renders y la elección están en el acta, en «Para escoger mirando». Sin las variables, las piezas salían como hasta entonces: cubierta lisa y relieve B. **Desde el 10-10 salen las escogidas** (§13.7).

**Ficha 9, el lomo** (`imprimir_piel.lomo()`). Cada banda sube desde 2 mm junto al hueco, en cuarto de círculo de radio `rho`, hasta `t_max`. Una banda de menos de 2 `rho` de ancho no llega arriba, así que las finas quedan por debajo de las anchas sin decírselo a nadie. La media banda típica mide 2,8 mm (mediana de la cresta, medida sobre la placa). Solo crece hacia fuera: la cara que apoya en el anillo se queda en z = 0, y bajo el labio la placa no pasa de `PESTANA_T`.

| grado | `rho` | `t_max` | banda típica | cada cachete |
|---|---|---|---|---|
| hoy (relieve B) | | 3 | 3 mm, plana | 178 g |
| suave | 3,5 | 4,0 | 4,0 mm | 189 g |
| medio | 4,5 | 5,5 | 5,2 mm | 202 g |
| hondo | 5,5 | 7,0 | 6,4 mm | 215 g |

Dos vueltas que no sirvieron. La primera escalaba la malla en sus coordenadas locales, con el origen en el plano medio de la placa: la engordaba hacia los dos lados, hasta 2,5 mm dentro de la ventana del anillo. Las reglas no lo vieron porque la ventana es hueca; lo delató la cota z del STL. La segunda subía cada banda según la distancia a sus **dos** huecos más cercanos, y salía con aristas donde cambiaba el segundo (cera con pliegues). La de ahora usa la distancia a uno solo y alisa la cresta.

**La ventilación no cambia**: el área abierta es la misma, y la chimenea da 20,0 K pesimista con los cuatro. La ficha 9 del acta decía que «un hueco más hondo deja pasar algo menos de aire», y es al revés. El borde del hueco pasa de 1 a 2 mm y el lomo lo redondea, y un borde redondeado descarga igual o mejor que uno vivo. Si el modelo se equivoca, se equivoca a favor.

**Ficha 8, la veta** (`imprimir_piel.veta()`). Son surcos que siguen cada franja de la lámina: las curvas de nivel de la distancia al canto más cercano, con un meandro lento y huecos a lo largo, de modo que rodean las esquinas de las ventanas y doblan sobre las franjas de los costados. Dos hondos: 0,5 mm por surco (`veta`) y 0,9 (`veta_honda`), que llegan a 0,6 y 1,3 donde se juntan dos. Se apagan a 1,5–3,5 mm de cada canto. Donde doblan la esquina de una ventana se leen como una moldura: si se escoge veta, eso se afina. La primera vuelta corría de anillo a anillo, como surcos paralelos al largo del aparato, y en las franjas angostas de los costados quedaba en rayitas sueltas. La cubierta pesa 875 g con la fina y 863 con la honda, contra 886 la lisa (aquí decía 881, que era la primera veta, la que se descartó: corregido el 10-10).

**Ficha 10, la placa ámbar.** `piel_termica.py` la cuenta ahora. La placa va dentro de la pletina del anillo, contra su cara de dentro (entre el anillo y el primer riel quedan 6 mm, y el interior es de los módulos), con una rendija alrededor. El aire del cachete cruza en serie la celosía, el canal de 11 mm entre la placa y el cachete, y la rendija:

| K sobre la sala (puerta / pesimista), techo 20 | v5 declarada, 64,2 W | censo, 35,1 W |
|---|---|---|
| sin placa | 17,9 / 20,0 | 11,9 / 13,3 |
| rendija 8 mm | 32,7 / 36,5 | 21,8 / 24,4 |
| rendija 12 mm | 29,8 / 33,3 | 19,9 / 22,3 |
| rendija 16 mm | 28,9 / 32,3 | 19,3 / 21,6 |

Es un orden de magnitud: el mismo `C_D` para todo y sin el roce del canal, que solo empeoraría la cifra. Con la luz, cada vatio dentro suma 0,34 K (declarada) o 0,42 K (censo), en el caso pesimista y con la rendija de 12. **La placa entera no cabe**: con la carga declarada no pasa de ninguna forma, y con el censo no pasa en el caso pesimista. Lo que se puede buscar es algo que tape la vista sin cerrarle el paso al aire (lamas ámbar inclinadas, como una persiana), y eso cuelga del HUECO 5 del papel de la v5: si el venteo se encarga contra la carga declarada o contra el censo. Con la declarada no cabe ni un vatio más.

**Ficha 15, satinado**: solo el material del render, rugosidad 0,22 con una capa de barniz. Aproxima el PA12 alisado por vapor; lo que decide es una muestra.

### 13.6 La cara puesta (ficha 14, 10-10)

`case/renders/cara_panel.py`, que llama `render_piel.py`. Solo pinta: no fabrica nada.

**Arriba**, el reparto que está en papel (plan del panel §4, con la enmienda del 27-08): la pantalla de 7" al centro y, en los dos flancos de 181,66 mm, las 4 macros de 38 en cuadro con su corona de LED, las 16 perillas de 20 a paso 28 × 34 y los 11 botones de 12 a paso 18. **Cómo se reparten entre los dos flancos no está escrito.** El render pone el orden del paquete del 23-08 (macros, perillas, fuentes) y parte las perillas 3 y 5 alrededor de la pantalla. Cabe con 6,8 mm entre las tapas y el canto, y entre las tapas y la pantalla, por la izquierda; por la derecha, 5,8. Es una elección del render, no del panel.

**Abajo, provisional**: los tres bloques del plan (30, 62 y 12 HP) con caras genéricas, perillas arriba y jacks abajo. Son módulos KONDOR que nadie ha dibujado. La fila del valle se queda lisa, porque tampoco tiene reparto.

**El negro.** La tapa del valle sale en un STL propio (`PART="negro"`; el resto del aluminio, rieles incluidos, es `PART="plateado"`). `aluminio` sigue siendo los dos, que es contra lo que mide `piel_choques.py`. En el pliego, la tapa del valle va anodizada en negro después de plegar. **Los rieles se quedan plateados.** La ficha los pedía negros (existen tal cual: *Tiptop Audio Z-Rails 104HP Black*, Thomann 511616), pero Samuel ya los había comprado plateados: *«yo ya compré los rieles plateados, así que serán plateados»* (10-10). Pintado como metal, el negro reflejaba la banda clara del entorno y salía gris; el material va sin `Metallic`, porque la capa anódica es un dieléctrico teñido.

**Lo que no es de fiar.** La zona activa de la pantalla (152,5 × 91,5) está estimada como 7" de diagonal a 5:3, sin hoja de la pieza. Lo que enseña la pantalla es una muestra (una onda y las 16 voces), no un diseño de interfaz.

**Una guarda.** El marco de cada panel sale de las gemelas de `clearance_budget.py`, y `vestir()` comprueba que sus cuatro esquinas caen sobre vértices del STL de los paneles. Si la gemela se separa del `.scad`, el render sale en rojo antes de pintar, en vez de dejar los mandos flotando.

### 13.7 Lo que escogió Samuel (10-10)

Marcó el acta la noche del 10-10. Desde entonces, `imprimir_piel.py` sin variables saca lo escogido:

| ficha | escogió | qué cambia |
|---|---|---|
| 9, el fondo de la celosía | **hondo** | el lomo `hondo` (radio 5,5, hasta 7 mm) es el que sale por defecto; `PIEL_RELIEVE=hoy` da el relieve B. Cada cachete pesa 215 g (178 con el B). La chimenea no cambia: la misma área abierta, 20,0 K pesimista |
| 8, la veta | **veta honda** | la cubierta sale con la veta honda: 871 g, surcos de hasta 1,3 mm. En las esquinas cambió la regla (abajo) |
| 10, la luz detrás | **sin nada detrás**; la ficha, «después» | no se hace ahora. D-P3 se queda como está modelado y #392, aparcada |
| 15, satinado | **por confirmar** | marcó «pide la muestra» en la elección y «no» en la ficha, con cuatro minutos de diferencia. Se le pregunta |

Las fichas 1 a 6, que se habían perdido, las volvió a marcar: las seis, «hazlo», como se habían tomado.

**La veta ya no dobla en las esquinas.** El §13.5 dejó dicho que, si se escogía veta, las esquinas se afinaban: donde los surcos doblaban la esquina de una ventana se leían como una moldura. La causa era la regla. Cada surco seguía la distancia al canto más cercano, así que en cada esquina doblaban todos a la vez, en paralelo, como el marco de un cuadro. Ahora el sitio de cada surco se mide **a lo largo del perfil**, desde el borde de su franja. Los surcos corren rectos a lo largo de la pieza en la nariz, el techo y el talón, y se apagan al llegar al rollo. Las franjas de los lados de cada ventana, donde a media anchura no hay lámina, quedan lisas, como el rollo al que llegan. `veta()` encuentra las ventanas sola: hoy van de 19 a 401 y de 476 a 688 mm de perfil.

**La nota de Samuel, y una más marcada para verla.** Con la elección escribió: *«la veta del concept es super marcada parece el tronco de un arbol digital y al mismo tiempo es lo que la hace tan hermosa, con toques de modernismo del de verdad»*. La honda son surcos de 1,4 mm de ancho y hasta 1,3 de hondo. El concepto tiene lomos anchos y redondos. `PIEL_CORTEZA=veta_marcada` va hacia eso: surcos de 2,6 mm de ancho y 1,8 de hondo (hasta 2,6 donde se juntan), tan juntos que entre ellos quedan lomos. Pasa las dos reglas (peor contacto, 0,30 mm). La cubierta pesa 845 g, y bajo el surco más hondo quedan 3,4 mm de los 6 de la lámina. Se enseña en el acta al lado de la honda. **No está escogida.**

**El peor contacto** pasa de 0,29 a 0,35 mm (cubierta contra aluminio), dentro de la tolerancia de 0,5: es el remallado de otra cubierta, no una pieza que entre en otra.

### 13.8 La tabla de la ficha 12 (10-10)

**Qué es.** La tabla del carpintero, la misma pieza de siempre (`bandeja_base()`), con tres cotas nuevas en `params.scad`:

| | antes | ahora | por qué |
|---|---|---|---|
| `vuelo_zocalo`, lo que vuela del cuerpo por los cuatro lados | 10 | **40** | con la piel encima, la losa asoma **28 mm por los costados y 34 por delante y por detrás**, dentro de los 25 a 40 que firmó Samuel |
| `t_base`, el grueso | 18 | **30** | «más gruesa a la vista». La flecha ya no la decide: con 200 N cede 0,067 mm, contra 0,376 con 18 |
| `r_canto_tabla`, el canto de arriba | vivo | **R8** | fresa de redondeo; el de abajo queda vivo |

Mide 648,62 × 399,76 y pesa unos 5 kg de nogal (a 0,65 g/cm³, densidad supuesta como `E_madera`), contra 2,3. Al aparato le suma 12 mm por debajo; el perfil y el interior no cambian. Las patas no se movieron: con 40 de vuelo quedan escondidas bajo la losa, que era lo que pedía la ficha. La placa grabada, opcional, no está.

**Lo que colgaba del vuelo sin decirlo.** El comentario de `vuelo_zocalo` decía «cota de MIRAR, nada cuelga de ella», y no era verdad. Los M5 con que la tabla se rosca al canto del anillo se repartían en el fondo de la **tabla**. Con 40 de vuelo, la fila pasaba sola de 3 a 4 tornillos por anillo y movía las roscas ciegas del anillo, una pieza mecanizada. Desde hoy se reparten en el fondo del **cuerpo** (`n_agujeros()` en el `.scad`, `_m5_tabla_x()` y `check_dxf.py`, las tres gemelas): siguen siendo 3 por anillo, en x = 53,3, 159,9 y 266,5. Los de las puntas se metieron 6,7 mm hacia dentro, y las puertas que cruzan esas roscas con las del marco siguen en verde.

**La tercera regla.** `piel_choques.py` mide ahora cuánto asoma la tabla de la piel por cada lado y sale en rojo fuera de 25 a 40 (`VUELO_PIEL`). La recoge la misma puerta, `check_piel.py`.

**Papeles.** `bandeja_base_2d.dxf` regenerado; la compra (README), el pliego (§6.2) y la muestra del RFQ dicen 30 mm, 648,62 × 399,76 y R8; el papel del case suma la rev. 29.

### 13.9 Las rendijas de la ficha 6 (10-10)

**Abajo y arriba, hechas.** La ventana de la cubierta se abría entera de P1 a P4, y entre la piel y el panel quedaban 14,5 mm abajo y 10 arriba: por ahí se veían la tabla y el ámbar de dentro. Ahora la lámina sube por la cara de abajo hasta el canto del riel del frente (`borde_ventana_inf()`, a 12,5 mm de P1) y baja por la de arriba hasta el canto del riel del remate (`borde_ventana_sup()`, a 147 de P3). Entre la piel y el panel queda el ala del riel, una línea de 2 mm, recta en todo el largo. Como los rieles se quedan plateados, la línea es de aluminio, no negra. La cubierta gana dos franjas y pesa 933 g.

**Una guarda nueva.** El issue nombraba una `guarda_tapa()` que no existe: los paneles no giran, salen de frente desatornillados (`guarda_paneles_fijos()`). La regla de choques mira la piel quieta y no habría visto un labio sobre la huella de un panel. Por eso `guarda_labio_ventana()`, en `clearance_budget.py` y gemela de las dos funciones del `.scad`, exige dos cosas. Que el labio quede al menos a 1 mm de la huella del panel, para que el panel salga sin rozar. Y que no deje más aire que el ala del riel, para que no vuelva la rendija. Su canario prueba los dos lados.

**El valle, no.** Entre el canto de atrás del panel KONDOR y el panel alto queda una rendija de unos 11 mm en la esquina de P3, y por ahí se ve el ámbar. Con piel no se puede cerrar. El panel KONDOR se mete 6,7 mm bajo el arranque de la cara de arriba, y su módulo sale hacia arriba por esa esquina: entre su camino y el riel del panel alto quedan 2,2 mm. Para esto la ficha pedía «tapar por dentro la línea de vista hacia el suelo». Se propuso una tira negra en el hueco, fuera del camino de los dos módulos, y Samuel la autorizó en el chat el 10-10 («te autorizo que crees el pr pues»).

**La tira del valle.** Es chapa de aluminio de 1 mm, anodizada en negro, lisa y sin taladros (`tira_valle()` en el `.scad`; en el render va en la parte `negro`). Su pie se apoya en el ala libre del riel de atrás de la fila KONDOR, los 2 mm entre el canto del panel y el del riel. Se recuesta en la arista de abajo del riel bajo de la fila alta, como una escalera contra la pared, y dos tacos de VHB en las puntas la sujetan. Va de riel a riel, así que tapa toda la línea de vista. No toca el marco ni pide taladros nuevos. `guarda_tira_valle()` es gemela de la geometría (comprobada contra el `echo` del `.scad`), vigila que el pie apoye en el ala y que la cara de fuera quede a 0,95 mm del camino del módulo KONDOR, e imprime las cotas de corte: 527,62 × 11,78. Su canario prueba los dos lados. El grueso no da para más: con 1,5 quedaría en el límite (0,52 mm de aire) y con 2 roza el módulo.

### 13.10 La corteza del concepto y un fondo más hondo (10-10, segunda vuelta)

Samuel volvió a marcar el acta. Junto a la veta honda le enseñé una más marcada, y escogió «más marcada todavía», con esta nota: *«tambien tiene que estar marcada la de los lados, basicamente toda la estructura blanca sin contar la celocia y las formas son extremadamente coherentes en el concepto me gustaria repetir eso tal cual»*. Al fondo de la celosía le puso «más hondo todavía». Y el satinado quedó en «después», sin muestra.

**La corteza** (`PIEL_CORTEZA=corteza`, la de por defecto; `FIBRAS` y `corteza_fibra()` en `imprimir_piel.py`). En el concepto la masa blanca es fibrosa: muchos cordones juntos que siguen el marco, doblan las esquinas en curva y bajan por los lados. No son surcos en franjas. Por eso la corteza va ahora sobre **toda** la masa blanca: la lámina, los rollos de los costados con sus patas, y la base del cachete. La celosía queda fuera.

Cómo se hace:
- **Dónde va cada cordón.** Lo marca la distancia de cada punto de la cara de fuera al canto más cercano (ventanas, apoyos en la tabla, la nariz del labio), alisada 800 pasadas sobre la malla. Sin alisar, donde se encuentran dos familias de líneas (el eje medio de cada franja) salía un inglete, y eso era lo que hacía la moldura.
- **El relieve.** Surcos de hasta 1,8 mm y lomos de hasta 1,3 entre ellos, cada 4,2 mm de media, con el paso irregular. Un ruido 3D lento los hace serpentear y los corta a trozos.
- **El orden.** Se pone entre el remallado y el decimado, porque una malla decimada no sostiene un surco de 1 mm: salía rayado. En la base del cachete, los cordones corren a lo largo y se apagan en los ingletes.

**Un fallo cazado por la regla 2.** La primera vuelta se metió 0,81 mm en el aluminio. La cara de fuera se decidía con la dirección punto-perfil. En la cara de dentro, pegada al anillo, esa dirección es ruido: el contorno real tiene radios y cae dentro del polígono, y daba la cara de dentro por cara de fuera. Ahora la decide la normal del tramo del perfil (`_lado_perfil()`), y en la lámina solo cuenta la cara que está a más de 2 mm por fuera.

**El fondo más hondo** (`mas_hondo`, el de por defecto): las bandas suben en cuarto de círculo de radio 7 hasta 9,5 mm, por debajo del rollo (12), así que la celosía no asoma del borde. La chimenea no cambia, porque el área abierta es la misma.

**Cifras.** Cada cachete pesa 231 g y la cubierta 949. Las tres reglas pasan en verde: peor contacto 0,40 mm (cubierta contra aluminio), y la tabla asoma 33 mm por delante y por detrás y 27 por los costados.

**Lo que no es el concepto todavía.** En las zonas anchas, donde la distancia al canto tiene una cima, los cordones se cierran en óvalos. Se leen como nudos de madera; en el concepto, en cambio, las fibras corren largas sin cerrarse. Si hace falta, el paso siguiente es medir cada punto entre los **dos** cantos de su franja, no solo contra el más cercano. Así las fibras se juntan donde la franja se estrecha y se abren donde se ensancha, sin cerrarse nunca.
