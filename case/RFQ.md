# RFQ — el SAM17, taller por taller

Documento para pedir presupuesto. Va **antes** que el pliego
([`PLIEGO.md`](PLIEGO.md)): el pliego dice qué hay que hacer, esto sirve
para saber **quién puede hacerlo**.

> **rev. 25 (2026-08-29, más noche; corregida tras el PR).** La trasera
> capturada como las mejillas. **Al mecanizado (§D)**: un segundo bolsillo en
> la cara interior de cada anillo (11 × 6, a lo largo del tramo trasero,
> cerrado por los dos extremos, con un escalón bajo el chaflán) y el rebaje
> del costado a 17 en ese tramo; P6 (y P5) a chaflán 6. **Al acrílico (§A)**:
> un chaflán de 5.5 × 45° en la arista de abajo de la trasera, por la cara
> exterior. **A la chapa
> (§B)**: el talón pasa a ser la nariz en espejo (dos dobleces a 45° y ocho
> pestañas lanzadas a r = 2 t con alivio, en 6082-T6 obligatorio: cada lengüeta
> puede llevar 154 N en la punta) y el techo baja con chaflán + labio (dos a
> 45°) en vez de
> banda a 90°. **A la casa de acrílico (§A)**: la trasera **sin un solo
> taladro**, 552.32 × 237.18. Pregunta nueva en §B: pestañas lanzadas con
> r = 1 t.
>
> **rev. 24 (2026-08-29, noche).** Al taller de chapa (§B) le entra **el
> marco de la ventana** (pletina de 6 a láser con seis cajeados, ×2
> espejados) y le salen las seis placas, los cuatro clips, las dos escuadras
> y los dos marcos de la trasera; el miembro bajo pasa a ser **el talón** y
> el miembro alto una L. A la casa de acrílico (§A): la trasera con diez
> taladros y dos muescas de esquina con radio. Al carpintero (§C): siete
> taladros más. Al mecanizado (§D): 14 roscas por anillo, no 16, y la esquina
> de abajo-atrás a radio 4.5.
>
> **rev. 23 (2026-08-29).** Al taller de chapa (§B) le entra **la nariz**
> (banda del frente, tres dobleces a 45°, 45° y 35°) y le sale **la bahía**;
> el miembro alto gana un doblez a 45°. Pregunta nueva en §B: si pliegan a
> ángulos que no sean 90° con el mismo radio.
>
> **rev. 22 (2026-08-28).** Son **cuatro** pedidos, no tres. La costilla deja
> de ser chapa plegada y pasa a **anillo de pletina mecanizada** — taller
> nuevo, §D, que no es el de chapa. El acrílico sigue **sin un solo
> taladro**. Cada bloque de preguntas es eliminatorio para SU taller y no
> dice nada de los otros.
>
> | § | taller | qué se le pide |
> |---|---|---|
> | A | casa de acrílico | costados ×2, trasera — **ninguna con taladros** |
> | B | chapa de aluminio (y acero) | **techo** (meseta + chaflán y labio, con bridas), **talón** (la nariz en espejo, con ocho pestañas lanzadas), **nariz**, **marco de la ventana ×2** (pletina de 6, láser + cajeados), tapa del valle, chasis ×3 |
> | C | carpintería | la tabla (suelo + zócalo) |
> | D | mecanizado de aluminio | el anillo ×2 — NUEVO desde el 2026-08-28 |

**Lo que se busca no es «un CNC».** Es una **casa de acrílico** — de las que
hacen vitrinas, expositores y museografía. Un CNC general fresa la forma y
la entrega tal cual sale de la máquina. Una casa de acrílico tiene la
pulidora de diamante y el horno de recocido como equipo estándar. Los dos
presupuestos parecen el mismo trabajo y no lo son.

---

## A. Casa de acrílico — preguntas eliminatorias

Si alguna respuesta es «no», no es el taller. No se negocia por precio.

1. **¿Hacen RECOCIDO (annealing) de las piezas después de mecanizar?**
   ¿A qué temperatura y con qué rampa de enfriamiento?
2. **¿Hacen PULIDO DIAMANTADO de canto en máquina?** (Pulido a llama **no**
   sirve: mete tensión y deshace el recocido.)
3. **¿Trabajan PMMA COLADO (GS)** en 8 mm, en naranja translúcido?
   *(Un solo espesor desde el 2026-08-25: los 5 mm existían para una única
   pieza —la tapa del valle— y esa pasó a chapa de aluminio.)*

### Por qué estas tres y no otras

El **recocido** es el que decide cómo está la pieza dentro de tres años. El
fresado deja tensión atrapada alrededor de cada agujero y cada canto; sin
recocer, el PMMA craquela —una telaraña de grietas finas— empezando por los
taladros, y se acelera donde hay un tornillo apretado o donde tocó un
limpiador. No se ve al desembalar.

El **diamantado** es el que decide si el aparato parece comprado o cortado a
medida. Son ~7,5 m de canto visible, y el acrílico es translúcido: la luz
viaja por dentro de la plancha y sale por el canto, así que un canto áspero
se ve como una línea blanca lechosa rodeando cada pieza.

El **colado** ya está decidido en la spec §11 y no es negociable: el
extruido trae tensión interna de fábrica y craquela solo.

**Lo que ESTE taller ya no hace, desde el 2026-08-27:** taladrar. El costado
tenía ocho agujeros —cuatro M4 de riel y cuatro M5 de larguero— y los ocho se
fueron al anillo de aluminio. La pieza es un contorno y nada más. Eso quita
de un plumazo el sitio por donde el PMMA craquela primero, pero **no quita el
recocido**: la tensión también la deja el fresado del canto.

---

## Preguntas de cota (acrílico)

4. ¿Qué **tolerancia de espesor** tiene el material que suministran, por
   escrito? *(Schaeffer AG confirmó ±(0.4 + 0.1 × espesor) el 2026-08-18, o
   sea ±1,2 mm en 8. No pedimos que la mejoren; pedimos saberla.)*
5. **¿Miden el espesor real del lote y lo comunican ANTES de cortar?**
   Hay cotas del diseño derivadas del espesor: `marco_sup` **es** el espesor
   de una plancha, y de él cuelga una junta que el modelo exige que valga
   exactamente cero.
6. ¿Qué **tolerancia de posición** garantizan en taladros? Necesitamos
   **±0,05 mm entre filas de una misma placa** — lo exige `alineacion()` en
   `clearance_budget.py`, porque el separador de una placa es uno solo.
7. ¿**Diámetro de fresa** estándar? El diseño asume **3 mm** (radio interior
   1,5) y hay geometría acotada contra ese número.

---

## Muestra que se pide con el presupuesto

Un retazo del **naranja real**, 8 mm, mínimo 150 × 100 mm, que lleve:

- un canto **tal cual sale de fresa** y otro **DIAMANTADO**, para comparar
- un **chaflán de 0,5 × 45°** en una arista
- un **cajeado ciego de 4 mm** y otro **de 6 mm** (una letra o un rectángulo)
- dos **taladros M3** pasantes

Y **el mismo retazo en AHUMADO** si lo tienen.

Este retazo no es un capricho: cierra cinco decisiones que hoy están
abiertas y que ningún render puede contestar — el espesor real (#98), cómo
se ve el diamantado en un traslúcido, a qué profundidad se lee el cajeado,
y si el cuerpo va naranja o ahumado.

---

## Criterio de aceptación de la muestra

**Escrito ANTES de mirarla.** Un criterio decidido con la pieza delante no
es un criterio.

| qué | aprueba si |
|---|---|
| **canto diamantado** | transparente, **sin línea blanca visible a 50 cm** bajo luz de techo. Si se ve lechoso, no es diamantado |
| **cajeado ciego** | la letra **se lee a 1 m** en el naranja. Si a 4 mm no se lee y a 6 sí, se sube `kondor_prof` |
| **chaflán** | uniforme a lo largo de la arista, sin escalón donde arranca |
| **espesor** | medido con calibre en **5 puntos**; se anota el rango, no la media |
| **taladros M3** | sin craquelado visible alrededor a contraluz |

## Registro

Se rellena al recibir. Va aquí y no en un correo.

| fecha | proveedor | recocido | diamantado | espesor medido | veredicto |
|---|---|---|---|---|---|
| (pendiente) | | | | | |

---

## B. Taller de chapa de aluminio (y acero) — preguntas eliminatorias

Es el taller que ya hace las tres piezas del chasis de acero. **No es un
taller nuevo**, pero desde el 2026-08-28 **ya no hace la costilla** — esa
pieza se mecaniza en un taller aparte (§D). Lo que sí hace: el **techo**
(la meseta y, por detrás, chaflán y labio — o la banda —, con una brida de
extremo doblada en cada punta), el **talón** (la nariz en espejo: labio,
chaflán y pie sobre la tabla, con ocho pestañas lanzadas del pie), la
**nariz** (la banda del frente, tres dobleces), los
dos **marcos de la ventana** (pletina de 6 cortada a láser, con seis cajeados
por el lado del anillo, un par espejado) y la tapa del valle. Son las piezas
que llevan los rieles y sostienen el marco por dentro del anillo. (La bahía,
tercer miembro hasta el 2026-08-29, y las placas, clips, escuadras y marcos de
la trasera, muertos esa misma noche, ya no existen.)

1. **¿Pliegan aluminio 6082-T6 de 1.5 mm a 90°, y con qué radio interior
   mínimo?** El modelo asume **r = 3** (2 × t) y de ahí cuelga el desarrollo
   del miembro alto, el talón, la nariz y las bridas. Si su radio mínimo es otro,
   **decirlo antes de cortar**: el recorte cambia. **Y a 45° y a 35°, con el
   mismo radio?** La nariz lleva dos dobleces a 45° y uno a 35°, el talón dos
   a 45° y el techo uno a 45° (o tres, con el chaflán): los BD (0.88 y 0.62)
   están calculados con ese mismo r = 3 y k = 0.42. **Y una pestaña lanzada**
   (las ocho del talón: 25 × 8, cortadas en U de 0.5 con un alivio de Ø2 en
   cada esquina del corte y dobladas 90° hacia arriba con el mismo r = 3)?
   Se pensó con r = 1 t y se deshizo: el diseño no puede colgar de una
   respuesta del taller.
2. **¿Qué factor K usan?** El modelo asume **k = 0.42**. Con r = 3 y t = 1.5
   eso da BA = 5.70 y BD = 3.30 mm por doblez. Si trabajan con otro, los DXF se
   regeneran — pero hay que saberlo, no adivinarlo.
3. **¿Qué aleación y temple suministran, y con qué `Rp0.2`?** Para el techo
   y la nariz no es eliminatoria: con 130 MPa pasan (el techo SOLO trabaja a
   111 con 20 kg en el centro de la meseta; y también el anillo de §D, cada
   pieza con su propia puerta). **Para el talón SÍ lo es: 6082-T6 (Rp0.2 ≥
   240)**, porque sus ocho lengüetas sujetan el canto de abajo de la trasera
   y la más cargada trabaja a 181 MPa con la carga en la punta — con 130 no
   pasa ninguna lengüeta de 1.5 (`guarda_trasera_flexion()`). Una aleación
   distinta **hay que aprobarla antes de cortar**, regenerando las puertas si
   cambia.
4. **¿Cortan a láser pletina de 6 mm y le hacen bolsillos ciegos** (el marco
   de la ventana: Ø8 × 2.5 en seis puntos por el lado del anillo, una rosca
   M3 pasante)? No lleva doblez, solo contorno, cajeado y agujero de paso —
   y **planitud**: apoya en una cara mecanizada y se atornilla con doce M4,
   que la conforman si el blank viene a ≤ 0.5 mm en 300 (`PLIEGO.md` §6).

**Los DXF que reciben son DESARROLLOS PLANOS, no contornos** (salvo el
marco de la ventana, que no se dobla). `miembro_alto_2d`, `talon_2d`,
`nariz_2d` y `tapa_valle_2d` traen el recorte; la pieza doblada mide menos. Cortar el
contorno de la pieza montada da un fichero válido e inservible — es el mismo
error que el modelo vigila con un sobre por pieza. **`costilla_2d` YA NO ES
DE ESTE TALLER**: desde el 2026-08-28 es un contorno real (sin plegar, sin
soldar) que se manda a mecanizado, §D.

**El marco de la ventana (`marco_ventana_2d`) sustituye a placas, clips y
escuadras desde el 2026-08-29 por la noche** (ver `PLIEGO.md` §6). El DXF
trae los agujeros FUNCIONALES de paso M4 (doce al anillo, seis de riel) y la
rosca M3 de la pestaña; el cajeado de Ø8 × 2.5 por el lado del anillo va
como nota de mecanizado en el mismo §6 — un DXF 2D no dice profundidad — y
hay que confirmarlo antes de cortar, como cualquier otra cota que no está en
el fichero. **Se cortan dos y se cajean por caras opuestas.**

### Preguntas de cota (aluminio)

5. ¿Qué **tolerancia de posición** garantizan en taladros de chapa? La rosca
   más justa de este taller hoy es la del riel del frente en el marco de la
   ventana, a **6.85 mm** del canto retirado bajo la nariz, y el M4 de la
   brida del miembro alto, a **6.75 mm** de su canto de arriba — el mínimo
   exigido (1.5 diámetros del M4 de paso), sin margen de sobra.
6. ¿**Desbarban** el canto? Ninguna de estas piezas lleva recocido, ni
   diamantado, ni chaflán: esas tres cosas son del PMMA.

---

## C. Carpintería — preguntas eliminatorias

Una sola pieza, pero **carga**: es el suelo del case y el zócalo a la vez, y el
cuerpo entero se le apoya encima.

1. **¿Qué especie y con qué contenido de humedad la entregan?** El modelo
   calcula contra **E = 11 000 MPa** a favor de veta (nogal, arce). Roble da
   ~12 000 y sobra; un contrachapado da ~8 000 y pediría 20 mm en vez de 18.
   **Decir la especie antes de cortar.**
2. **¿Pueden hacer ranuras alargadas de 10.5 × 5.5 mm** (agujero de paso M5 con
   5 mm de carrera) en la posición del dibujo, y **catorce taladros pasantes de
   Ø4.5** (paticas, nariz, talón y chasis)?
3. ¿Qué **acabado** proponen para una pieza cuya cara de arriba se ve por dentro
   del case a través del acrílico y cuyo canto se ve por fuera?

**La cota que no se negocia:** el dibujo trae, en cada una de las dos filas,
**un agujero redondo (el del medio) y dos ranuras**. No es un descuido ni una
mezcla: es lo que deja que la tabla se mueva con la estación sin rajarse contra
un marco de aluminio que no se mueve. **Con todos redondos la tabla se raja; con
todos alargados se arrastra hacia un extremo.** Si el taller propone
«homogeneizarlos», la respuesta es no.

### Muestra que se pide

Un retazo de la especie propuesta, 18 mm, con un canto acabado como se
entregaría. Se compara contra el naranja del cuerpo — **la tabla y el acrílico
se ven juntos y a la vez**, y eso no lo contesta ningún render.

---

## D. Taller de mecanizado — pregunta eliminatoria

**Taller nuevo desde el 2026-08-28.** No es el de chapa (§B): la costilla deja
de plegarse y pasa a ser un **anillo fresado de una pletina de aluminio
maciza de 14 mm**, vaciada por el centro, una pieza por lado.

1. **¿Garantizan la planitud de la pieza después de vaciar el centro de una
   pletina de 14 mm?** Vaciar el centro de una placa gruesa libera tensión
   interna del material y puede alabearla — es el riesgo técnico real de
   esta pieza (la sección sobra: I = 3714 mm⁴ contra 1673 de la vieja L
   plegada, así que la resistencia no es lo que preocupa). Si la respuesta
   es «no» o «no lo garantizamos», no es el taller.

### Preguntas de cota (mecanizado)

2. ¿Trabajan a **fresado CNC** (3 ejes o mejor) sobre pletina de 14 mm de
   aluminio?
3. ¿Pueden dar **roscas ciegas M4/M5** a **10 mm de profundidad útil**, en
   una franja de 14 mm de aluminio, con la tolerancia de posición que exige
   `guarda_anclajes()` (roscas a 1.5 diámetros de broca de cada canto: la
   silueta exterior, la pared del rebaje y la del bolsillo de la trasera)?
   Son 14 M4 en la cara interior y 3 M5 en el canto inferior, por anillo.
   **Y un segundo bolsillo por la misma cara**: 11 de ancho × 6 de hondo a lo
   largo del tramo trasero, cerrado por los dos extremos (de 1 mm del canto de
   abajo a 17 del de arriba, con un escalón bajo el chaflán), con una pared de
   3 mm entre él y el rebaje del costado.
4. ¿Hacen **chaflán mecanizado de 1.5 × 45°** en dos aristas de la cara
   vista, por pieza?
5. ¿Anodizan en **satinado**, con **enmascarado de un punto** antes de
   anodizar (para el bonding de tierra)? Si no lo hacen ellos, ¿trabajan con
   un anodizador que sí?

### Muestra que se pide con el presupuesto

Un **cupón de 100 mm del perfil del anillo** — mismo espesor, mismo rebaje,
mismo chaflán, mismo acabado, mismo anodizador — **antes de cortar los dos
anillos completos**. Las cotas de la cara vista (chaflán, rebaje, rehundido)
salieron de escalar una foto de referencia y están marcadas ESTIMADO en la
spec de diseño; el cupón es lo que las cierra contra la pieza real, no contra
el render.

El plano es **`plans/cupon_anillo_2d.dxf`**: la sección del perfil, a 1:1 y en
mm. Va con una rosca ciega M4 a media longitud y un punto de bonding
enmascarado en la cara interior. El PLIEGO (§ anillo) lleva la tabla de lo que
se mide cuando vuelve y qué se cambia si no pasa. **Es un punto de parada: sin
cupón aprobado no se corta el material de los anillos.**

### Registro

| fecha | proveedor | planitud confirmada | anodizado | cupón aprobado |
|---|---|---|---|---|
| (pendiente) | | | | |
