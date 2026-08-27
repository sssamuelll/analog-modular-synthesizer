# SAM17 — El esqueleto visible

**Fecha:** 2026-08-27
**Estado:** aprobado en diseño, pendiente de plan de implementación
**Sucede a:** [`2026-08-26-case-esqueleto-aluminio-design.md`](2026-08-26-case-esqueleto-aluminio-design.md),
que hizo portante el aluminio pero lo dejó **escondido detrás del acrílico**.
**Referencia visual:** foto de vitrina con marco perimetral de aluminio a la
vista, paneles retranqueados por dentro, tira ranurada iluminada en el medio y
zócalo de madera. Aportada por Samuel el 2026-08-27.
**Gobernada por:** [`.specify/memory/constitution.md`](../../../.specify/memory/constitution.md).

---

## 1. Qué cambia, en una frase

El esqueleto de aluminio pasa **por fuera** y se ve; el acrílico pasa por dentro
y deja de ser la cara exterior del case —aunque **conserva su contorno**, §2
decisión 2—; los tres perfiles 2020 comprados se sustituyen por
**miembros de chapa doblada** de la misma familia que la costilla; y el hueco del
valle se convierte en una **bahía perforada** que es estructura y sitio de
montaje a la vez.

## 2. Las cinco decisiones

| # | Decisión | Alternativas descartadas y por qué |
|---|---|---|
| 1 | **El esqueleto va por fuera, el acrílico por dentro** | Es lo que pidió Samuel y lo que muestra la referencia. Dejarlo como está mantenía un aparato cuya pieza portante no se ve |
| 2 | **El acrílico conserva su silueta escalonada entera** | Encogerlo a llenar la ventana del marco —lo que literalmente muestra la foto— se descartó: Samuel prefiere que las dos piezas compartan contorno. Cambio más pequeño y el canto del acrílico sigue leyéndose por la ventana |
| 3 | **Todo el esqueleto en chapa plegada; se van los tres 2020** | Extrusión propia: matriz de miles de euros que no se amortiza en una unidad (ya descartada en la spec anterior, §2). Fresado de placa: lo más caro. **Mixto** (§5.3): deja dos familias de unión conviviendo y no simplifica el pliego |
| 4 | **La bahía del valle es ESTRUCTURA**, no solo superficie de montaje | Bandeja no portante: el marco tendría que cerrar los 528 mm de vano solo. Una chapa en cortante ata las dos costillas mucho mejor que una barra, y de paso es donde se atornilla el patch bay: **una pieza, dos trabajos** |
| 5 | **La meseta de remate se funde con el miembro trasero alto** | Dos piezas separadas (tapa de aluminio + miembro) es una junta más y un DXF más para nada: la tapa horizontal y el ala que recibe la trasera son los dos lados del mismo doblez |

### 2.1 Lo que Samuel decidió NO hacer, y conviene tenerlo escrito

- **Las bisagras siguen escondidas** dentro del Z-Rail. En la referencia son el
  detalle más llamativo del aparato, y sacarlas fuera mueve el eje de giro y con
  él el radio: las 180° de apertura de las dos filas son lo primero que se
  pierde, y costaron 16 mm de fondo.
- **La fila superior de módulos se queda.** «Tapa de aluminio arriba» significa
  la meseta más el marco visto por el borde, no convertir la cara de arriba en
  una tapa ciega.

## 3. La inversión, y la junta que aparece

### 3.1 El apilado se voltea

| | hoy | después |
|---|---|---|
| z 0 .. 3 | — | **alma de la costilla** |
| z 0 .. 8 | costado de acrílico | — |
| z 3 .. 12.5 | — | junta 4 mm (comprimida) + costado de acrílico |
| z 8 .. 11 | alma de la costilla | — |
| z 11 .. 539.62 | interior | interior |

`ancho_util` (528.62) **no se mueve**: es la punta a punta del Z-Rail y el orden
de las capas no lo toca.

`ancho_total` **sí crece 3.0 mm**, de 550.62 a **553.62**, y no por la inversión
en sí —el orden de las capas es indiferente— sino por el casquillo de §3.3, que
se dimensiona contra el acrílico más grueso del lote.

### 3.2 El tornillo del riel deja de morder donde muerde

Hoy el M4 atraviesa la costilla (3 mm) y rosca en la punta del Z-Rail. Volteado
tiene que cruzar **11 mm** —3 de aluminio y 8 de acrílico— antes de morder, y al
apretarlo deja el PMMA **pinzado entre dos caras de aluminio**.

Eso es carga sostenida sobre PMMA, que es la cuenta de la arandela d16 del
README: por encima de ~10 MPa mantenidos la precarga se relaja sola en semanas.
Aquí lo que se relajaría es lo que sujeta el riel.

**La solución ya está en el repo y ya tiene nombre.** El chasis del PSU cuelga
con un `separador` de 3 mm por exactamente este motivo — *«el tornillo cruza ese
aire y sin él, apretar abolla la pared»* (#106). Aquí igual:

- **8 casquillos de aluminio** (uno por M4 de riel), largo **`L` = 9.5 mm** —
  NO `t_cheek`: se dimensionan contra el acrílico más grueso del lote, ver §3.3 —
  que atraviesan el acrílico.
- El agujero del acrílico es **de paso holgado** alrededor del casquillo.
- El apriete va costilla → casquillo → riel. **El acrílico no se comprime nunca.**

### 3.3 Y entonces la tolerancia reaparece en un sitio nuevo

**La primera versión de esta sección se contradecía y el audit lo cazó.** Decía
que el casquillo fija el hueco en 8 mm exactos, que a 9.2 el acrílico no entra, y
que una junta de 2 mm «absorbe el ±1.2». Las tres cosas juntas no pueden ser: si
el hueco son 8 y el acrílico puede medir 9.2, añadir junta lo empeora.

**La cuenta, hecha bien.** Llamemos `L` al largo del casquillo (que ES el hueco
entre la cara interior del marco y la punta del riel) y `t` al espesor real del
acrílico, que llega entre **6.8 y 9.2** (±(0.4 + 0.1 × t) = ±1.2 sobre 8,
confirmado por Schaeffer AG el 2026-08-18).

Si la junta va **en el mismo apilado que el tornillo**, tiene que cumplir
`L − t ∈ [g_min, g_0]` para todo `t`, y eso deja una sola solución sin margen: con
EPDM de 4 mm comprimible al 60 %, `L = 10.8` exacto. Cero holgura de diseño para
una cota que depende de un lote que aún no se ha medido. **Se descarta.**

**La junta NO va en el apilado del tornillo: va en el perímetro.**

- El casquillo se dimensiona contra el **peor caso**: `L = 9.5` (9.2 del acrílico
  más grueso, más 0.3 de aire). El acrílico **nunca queda pinzado**, mida lo que
  mida.
- La junta de EPDM vive **entre el ala de la costilla y la cara del acrílico**,
  alrededor del perímetro, y es la que empuja el acrílico contra las piezas
  interiores. Se come el juego que quede, que en el peor caso son 2.7 mm.
- Espesor de junta: **4 mm**, para tener recorrido de sobra sobre esos 2.7.

**Lo que eso cuesta, y hay que decirlo porque §3.1 dice que el ancho no cambia:**
`L` pasa de 8 a 9.5, así que el marco se separa 1.5 mm más por lado.
**`ancho_total` crece 3.0 mm**, de 550.62 a **553.62**. `ancho_util` **no se
mueve** — sigue siendo la punta a punta del Z-Rail.

Con eso el acrílico queda **fuera del camino de carga y fuera de la cadena de
tolerancias a la vez**, que es lo que la spec anterior §3 perseguía. El **#98 se
queda cosmético**.

**La alternativa que NO se toma, y por qué:** cortar los casquillos al espesor
medido del lote. El pliego ya exige medir antes de cortar, así que el dato
existiría. Pero eso vuelve a colgar una cota funcional del espesor real del
acrílico, que es exactamente lo que este rediseño lleva dos specs desmontando.
Tres milímetros de ancho es más barato que reabrir el #98.

### 3.4 El esqueleto pasa a ser superficie tocable, y eso es eléctrico

**Este hueco lo encontró el audit adversarial, no el diseño.** Va aquí y no en
«lo que no está confirmado» porque no es una incógnita: es un requisito que el
cambio crea.

El SAM17 es **aparato Clase I**: entrada IEC con fusible, 230 V dentro, y la
protección depende de que **toda parte metálica accesible esté unida a PE**. El
README lo tiene como «Bonding de tierra — no negociable», con un espárrago único
y cable verde/amarillo con terminal de ojal por pieza.

Hasta hoy eso era manejable porque **la cara exterior del case era acrílico**: un
aislante. El aluminio vivía dentro. Con la inversión, **el esqueleto es lo que la
mano toca**, y con él las costillas, los dos miembros, la bahía y la meseta.

Dos consecuencias, y la segunda es la que muerde:

1. **Cada pieza del esqueleto entra en el censo de bonding.** Son seis piezas de
   aluminio donde antes había cuatro barras y dos costillas escondidas.
2. **El acabado y el bonding se pelean.** El anodizado es un **aislante**, y un
   marco visto se anodiza — es lo que le da el aspecto de la referencia. Una
   junta atornillada entre dos piezas anodizadas no garantiza continuidad. Se
   resuelve con **arandela de diente que perfora el anodizado** en el punto de
   bonding, o **enmascarando** ese punto antes de anodizar. Las dos son
   decisiones de pliego, y ninguna se puede tomar «al montar».

**Lo que hay que verificar, y no lo cubre ninguna puerta de hoy:** continuidad de
PE a cada pieza accesible, medida con **miliohmímetro**, no con la escala de
ohmios de un multímetro. La cifra de referencia habitual para Clase I es
**≤ 0.1 Ω** entre el pin de tierra del IEC y cualquier metal accesible.

Eso es un procedimiento de ensamblaje, no una cota del modelo: va al README y al
pliego, y **bloquea el primer encendido**, no el corte de piezas.

## 4. La familia de chapa

### 4.1 Un canal doblado le gana al 2020

**Convención, para que el número sea reproducible** (el audit señaló que sin esto
no lo era): «canal `w × d` en chapa de `t`» es un perfil en U de cotas
**exteriores** `w` (perpendicular a la carga) por `d` (en la dirección de la
carga), doblado de chapa de espesor `t`. La inercia es la del **eje neutro de la
sección completa**, contra flexión en la dirección `d`, calculada por
paralelas-a-ejes sobre tres rectángulos: el alma (`t × w`) y las dos alas
(`d × t`). Con `w = d = 20` y `t = 3`: área 180 mm², centroide a 7.167 mm de la
cara del alma, **I = 6 935 mm⁴**.

| | inercia | sección | peso por miembro de 528.62 |
|---|---|---|---|
| 2020 de catálogo | ~5 600 mm⁴ *(SUPUESTO: cifra de oficio para un 20×20 ranurado; el catálogo del proveedor manda)* | ~460 mm² | 0.657 kg |
| **canal doblado 20 × 20** | **6 935 mm⁴** | 180 mm² | **0.257 kg** |
| canal 20 × 25 *(envolvente MAYOR: 5 mm más de fondo)* | 13 043 mm⁴ | 210 mm² | 0.300 kg |

A **igual envolvente** (20 × 20), el canal da 24 % más de inercia con el 39 % de
la sección y menos de la mitad de peso. La fila de 20 × 25 no es comparable en
envolvente y está solo para enseñar cuánto compra profundizar 5 mm donde carga.

**El perfil comprado no estaba ahí por rigidez: estaba ahí porque era lo que se
compra.**

La sección definitiva de cada miembro sale de su carga, **en el plan**. 20 × 20
es el mínimo que ya gana al 2020, y es lo que el pliego (§10) cotiza mientras
tanto — si un miembro pide más fondo, cambia su desarrollo, no el proveedor.

### 4.2 Son TRES miembros, no cinco

| miembro | qué recibe | forma |
|---|---|---|
| **trasero bajo** | fila baja de la trasera; la pared trasera del chasis del PSU | canal |
| **trasero alto** | fila alta de la trasera **y ES la meseta**: cara horizontal de 37 mm arriba, ala hacia abajo | un solo doblez |
| **la bahía** | la tapa del valle / el patch bay, y ata las dos costillas en cortante | bandeja: fondo perforado y **dos alas dobladas hacia arriba** que son los cantos de apoyo |

El larguero `valle` no desaparece sin heredero: lo hereda la bahía, que es mejor
apoyo que él.

### 4.3 Por qué la trasera no puede vivir sin miembros

Medido antes de elegir enfoque, porque decidía entre ellos. La trasera es
acrílico de 8, 528.02 × 248.18. Sujeta **solo por sus dos cantos verticales**
cruza 528.02 mm y cede **19.3 mm** con 200 N.

La cuenta, para que se pueda rehacer: viga biapoyada, `δ = P·L³/(48·E·I)` con
`I = b·t³/12`, `b` = 248.18 (el alto de la plancha), `t` = 8, `E` = 3 000 MPa
(PMMA colado, el mismo módulo con que está acotada la trasera hoy),
`L` = 528.02, `P` = 200 N (`carga_mano`).

Eso mata el enfoque de monocasco —«las planchas son la estructura»— para esta
cara: para ser estructura la trasera tendría que pasar a aluminio, y se perdería
la trasera vista con el relieve KONDOR y la ventilación.

## 5. La bahía

### 5.1 Le cabe la mano

| | |
|---|---|
| ventana libre entre los dos rieles del valle | **56.47 mm** (X) × 528.62 (Z) |
| profundidad libre hasta el techo del chasis del PSU | **58.58 mm** |
| profundidad donde el chasis no llega | 143.58 mm |

Un jack de 6.35 pide unos 30 mm detrás del panel; un minijack, 20. Entran los dos
con sitio para el cableado. Son **104 HP de frente en una sola tira**.

### 5.2 La tapa del valle deja de ser tapa: es la puerta

Hoy es una chapa ranurada atornillada a una barra. Pasa a ser el **frente
desmontable de la bahía**: cinco M3 y entras. El día que se monte el patch bay,
esa chapa se sustituye por el panel del patch bay y no se toca nada más.

Es lo que Samuel pidió con «fácil de preparar para abrir e instalar algo allí».

De regalo, la tapa mejora: hoy vuela **23.24 mm** a cada lado de su barra;
apoyada en los dos cantos de la bahía vuela **14.00**.

**Los «dos cantos» son las alas de la bandeja.** La bahía no es una chapa plana:
es una bandeja con el fondo perforado y las dos alas largas dobladas hacia
arriba, y esas alas son a la vez el canto donde apoya la tapa, la pared de la
bahía y lo que le da inercia a la pieza. La altura del ala sale del plan.

### 5.3 Lo que la bahía NO cierra

Que ate las dos costillas en cortante mejor que una barra es cualitativamente
cierto y **no está medido**. Es la misma frase que la spec anterior dejó abierta
sobre el racking del cajón (#203), y se cierra igual: **cargando el prototipo**.

## 6. Lo que se pierde con el 2020: la ranura en T

**Esto no estaba en la recomendación cuando se hizo, y es la pérdida más grande
del cambio.** El perfil comprado no solo traía sección: traía una ranura en T
corrida, y el repo la eligió a propósito — usa tuercas de **inserción lateral**
(drop-in) y no de deslizar, con esta razón escrita en el BOM:

> *«con las de deslizar hay que enhebrarlas por la punta del larguero antes de
> montar, o sea que añadir un tornillo más tarde obliga a desarmar»*

Hoy **24 tornillos** viven en esa ranura: 2 del chasis y 22 de plancha. Con
canales de chapa no hay ranura: cada agujero se decide en el DXF, y añadir uno
después es taladrar el case montado.

**Cómo se devuelve:** los miembros llevan la **misma retícula perforada que la
bahía** — una fila de agujeros a paso regular a lo largo de cada canal, como los
raíles de una bahía de PC. No es la libertad continua de la ranura, pero es
«atornilla donde quieras al paso de la retícula» sin desarmar. Y encaja con lo
declarado: la spec del case dice desde la rev. 1 que **la retícula visible y
regular de puntos de unión es el ornamento permitido**.

El paso de la retícula es cota de plan, no de aquí.

## 7. El techo

`marco_sup` pasa de **8 a 3**: la meseta deja de ser acrílico y pasa a ser la
cara horizontal del miembro trasero alto.

**Se comprobó que eso es limpio.** `marco_sup` llegó a sostener una junta que el
modelo exigía que valiera exactamente cero, pero esa puerta **murió** cuando la
tapa de remate pasó de pegada al Z-Rail a atornillada al larguero (2026-08-21).
Hoy `marco_sup` solo fija tres cosas:

- el espesor de la meseta,
- la Y del miembro trasero alto (`P[5].y − marco_sup − r`),
- el canto alto de la trasera (`P[5].y − marco_sup`).

Consecuencia: el miembro sube 5 mm y **la trasera crece 5 mm de alto**.
`guarda_remate()` —que exige que la tapa cubra la meseta entera— sigue siendo la
puerta que lo vigila.

Y «marco de la fila superior en aluminio» sale **gratis** con la inversión: el
ala de la costilla pasa a ser el canto visto de esa cara, y los paneles de módulo
ya son PCB de aluminio.

## 8. La fuente

### 8.1 No es grande por descuido

| cota | de dónde sale | margen |
|---|---|---|
| largo 332 | 10 + **PCB 200** + toroide 97 + 10 = 317 | 15 mm |
| fondo 170 | la PCB (150) manda; el toroide pide 97 | justo |
| **alto 80** | el toroide pide **61** (46 + 15 de margen) | **19 mm sin usar** |

Exterior de hoy: **338.6 × 176.6 × 83**, o sea el **64 % del ancho útil** y el
57 % del fondo. Por eso domina la bahía inferior en el render.

### 8.2 La placa está dibujada, y eso cierra dos de las tres palancas

`chasis_pcb_ancho` = 200 y `chasis_pcb_fondo` = 150 **no son una reserva**: son
el `Edge.Cuts` real de la placa, en las tres revisiones que hay en el repo.

```
sam17-power.kicad_pcb        150.0 x 200.0 mm
sam17-power-v2.kicad_pcb     150.0 x 200.0 mm
sam17-power-v3.kicad_pcb     200.0 x 150.0 mm
```

O sea que **el largo del chasis no se puede apretar desde el case**. Se apretó al
revés en la conversación —se dijo que la reserva era blanda— y no lo es.

### 8.3 Lo que se hace, y lo que queda bloqueado

- **`chasis_int_z` pasa de 80 a 61.** Gratis, y el número sale de la hoja del
  toroide (Nuvotem RS0120P1: 46 mm + 15 de margen). El exterior baja de 83 a 64,
  o sea **23 % más baja** ((83 − 64)/83 = 22.9 %).
- **El largo queda BLOQUEADO por hardware.** Samuel decidió rehacer la placa más
  pequeña, y eso es una rev. 4 de la fuente. El case **no se bloquea**: el modelo
  ya deriva el chasis de `chasis_pcb_ancho`, así que cuando exista la placa nueva
  el chasis se ajusta solo y las puertas lo verifican.

Se midió y se descartó **apilar el toroide y la PCB en profundidad**: bajaría el
chasis al 43 % del ancho pero pediría 283.6 mm de fondo sobre los 308.94 del
case, dejando 25 mm. Se come el suelo entero.

## 9. Verificación

### 9.1 Puertas que se reescriben

| puerta | por qué |
|---|---|
| `guarda_costado()` | el acrílico pasa a estar por dentro; su apoyo sigue siendo la ventana de la costilla, pero desde la otra cara |
| **`costado_2d` vuelve a llevar taladros** | 4 agujeros de paso holgado por costado, para los casquillos de §3.2. Se le quitaron TODOS el 2026-08-27 y vuelven cuatro — **de paso, no de apriete**, que es la diferencia que importa. Las puertas que se re-apuntaron ese día (`taladros_con_material()` murió, la rama del costado de `agujeros_donde_toca()` murió) hay que **resucitarlas con el criterio nuevo** |
| `taladros_costilla()` | cambia el censo entero: entran los casquillos, la bahía y la retícula |
| `guarda_tapa()` | la tapa del valle deja de volar 23.24 y pasa a 14.00 sobre los cantos de la bahía |
| `guarda_chasis()` | alto de 80 a 61, y la pared trasera cuelga de un canal **sin ranura en T** |
| `alineacion()` y `apoyo()` | las filas cambian de dueño |
| `guarda_remate()` | `marco_sup` de 8 a 3 |

### 9.2 Puertas nuevas que hacen falta

1. **La junta del casquillo.** Que el largo del casquillo, el espesor nominal del
   acrílico y la compresión de la junta cierren, y que el acrílico **no** quede
   pinzado. Es la puerta que evita repetir el modo de fallo del PMMA.
2. **La retícula.** Que todo tornillo de plancha caiga en un agujero de la
   retícula de su miembro. Sin ella se pierde la propiedad que la ranura en T
   daba gratis y nadie se entera hasta el montaje.
3. **Los tres sobres nuevos** de DXF —`miembro_bajo_2d`, `miembro_alto_2d` y
   `bahia_2d`— los tres **desarrollos planos derivados** y no escritos a mano,
   como `bbox_desarrollo_costilla()` y `bbox_desarrollo_tapa()` ya lo hacen. Van
   en `_sobres()` de `check_dxf.py`, y el generador es `sam17_case.scad` con su
   gemela en `clearance_budget.py`.
4. **La continuidad de PE** (§3.4). No es puerta de modelo: es paso de
   ensamblaje verificado con miliohmímetro, y va al README.

### 9.3 Lo que NO se toca

La tabla y su fijación de ranura alargada. Los 4 Z-Rails. La geometría del panel,
el paso de 1 HP y **las 180° de apertura**. El perfil escalonado. El relieve
KONDOR. La ventilación. Todo lo que costó milímetros de aparato sigue donde está.

## 10. El pliego

Pierde un proveedor —se va el de perfil de aluminio— y el acrílico pierde una
pieza, la meseta.

| material | piezas |
|---|---|
| PMMA colado GS naranja, 8 mm | costados ×2, trasera |
| Aluminio, chapa plegada 3 mm | costillas ×2, miembro trasero bajo, miembro trasero alto (con meseta), bahía, tapa del valle |
| Acero, corte + plegado | chasis ×3 |
| Madera maciza 18 mm | la tabla |
| Comprado | 4 Z-Rails; 8 casquillos de aluminio de `L` = 9.5; junta de EPDM de 4 mm; **la tornillería entera** |

**La tornillería no se hereda: se recuenta.** Los 24 tornillos que hoy viven en
la ranura en T del 2020 cambian de anclaje (§6), y con ellos su herraje: donde
había tuerca T de inserción lateral ahora hay agujero de la retícula, y eso
decide entre roscar el canal, poner tuerca remachable o tuerca ciega. **Es cota
de plan**, y hasta que se decida el pliego no puede cotizar la tornillería —
solo las piezas.

Lo que sí está cerrado: **8 M4 de riel** (los mismos, con casquillo nuevo) y
**los 6 M5 de la tabla**, que no tocan el esqueleto.

## 11. Lo que NO está confirmado

- **La sección de cada miembro.** 20 × 20 es el mínimo que ya gana al 2020; la
  definitiva sale de la carga de cada uno, en el plan.
- **El paso de la retícula**, y con él cuántos agujeros lleva cada miembro.
- **Que la bahía cierre el racking (#203).** Cualitativamente sí; sin número.
  Se cierra cargando el prototipo. **Es deuda HEREDADA, no nueva**: la spec
  anterior ya dejaba el racking sin cerrar con número, y este diseño le añade una
  chapa en cortante donde antes había una barra. No empeora nada; tampoco lo
  cierra.
- **La placa de la fuente rev. 4**, que es lo que libera el largo del chasis.
- **La especie y la humedad de la tabla**, heredado de la spec anterior.
- **El peso del chasis del PSU**, heredado y sin medir: de él cuelgan los 18 mm
  de tabla y la pregunta de si resuena bajo los 100 Hz del toroide.
- **La dureza de la junta de EPDM.** El espesor ya está: 4 mm, contra los 2.7 de
  juego del peor caso (§3.3). La dureza decide cuánto hay que apretar para que
  el acrílico no baile, y sale de la curva del proveedor.
- **Cómo se garantiza la continuidad de PE con el marco anodizado** (§3.4):
  arandela de diente o enmascarado antes de anodizar. Decisión de pliego.

### 11.1 Lo que este documento decide y lo que deja al plan

El audit señaló, con razón, que varias cotas se declaran «de plan» mientras el
pliego ya lista las piezas. La frontera, explícita:

| decide esta spec | decide el plan |
|---|---|
| que hay tres miembros y cuál recibe qué | la **sección** de cada uno (20 × 20 es el piso) |
| que la bahía es bandeja con dos alas | la **altura del ala** |
| que los miembros llevan retícula perforada | el **paso** de la retícula y cuántos agujeros |
| `L` = 9.5 y junta de 4 mm | la **dureza** de la junta |
| `chasis_int_z` = 61 | el largo, que espera a la placa rev. 4 |

El pliego (§10) cotiza **piezas**, no tornillería, hasta que el plan cierre la
columna derecha.

## 12. Fuera de alcance

- El patch bay en sí. Esta spec le hace **sitio y superficie**, no lo diseña.
- La rev. 4 de la placa de la fuente.
- Las bisagras vistas de la referencia (§2.1).
- El zócalo: ya resuelto en la spec anterior, §9.
