# RFQ — el SAM17, taller por taller

Documento para pedir presupuesto. Va **antes** que el pliego
([`PLIEGO.md`](PLIEGO.md)): el pliego dice qué hay que hacer, esto sirve
para saber **quién puede hacerlo**.

> **rev. 27 (2026-10-11). La persiana.** Las dos mejillas de acrílico se van
> y las sustituye una persiana de aluminio por costado (papel
> `docs/superpowers/specs/2026-10-11-case-persiana-design.md`). **A la casa de
> acrílico (§A)**: queda una pieza, la trasera. **Al mecanizado (§D)**: diez
> bolsillos por la cara de fuera de cada anillo, y **la persiana ×2**, dos
> programas espejados, con una tira de muestra antes que las piezas. **Entra
> §E, el anodizador**: uno solo, un lote y una aleación para todo el aluminio
> que se ve, en negro; el anillo deja de ir «satinado». Esta revisión
> sustituye el alcance operativo de la rev. 26, que se conserva debajo como
> historia. **A la chapa (§B), por la ficha 6 (D-S9)**: la nariz y el techo
> bajan hasta pisar la cara del riel; sus blanks crecen a 545.62 × 53.10 y
> 593.02 × 78.85 (el retorno del techo pasa de 4 a 9).
>
> | § | taller | qué se le pide |
> |---|---|---|
> | A | casa de acrílico | la trasera — **sin taladros** |
> | B | chapa de aluminio (y acero) | **techo macizo** (sin ranuras, labio de 20, bridas R2), **talón** (pie de 22.5 y muescas), **nariz** (pie de 20.5 y muescas), **marco de la ventana ×2**, tapa del valle, chasis ×3 |
> | C | carpintería | la tabla (suelo + zócalo) |
> | D | mecanizado de aluminio | el anillo ×2, con sus diez bolsillos por fuera, y **la persiana ×2** |
> | E | anodizado | todo el aluminio que se ve, en negro y en un lote |
>
> **rev. 26 (2026-08-30).** **Al mecanizado (§D):** en la cara interior de
> cada anillo entra el rebaje de chapa de 4.5 × 3 y un cajeado de brida de
> 28 × 15.5 × 3; son dos cajeados en total. La única pregunta abierta de esta
> tanda es si el taller sostiene el reborde de 1 × 3. **A la chapa (§B):** el
> techo queda macizo, sin sus 16 ranuras. Son menos operaciones; no aparece
> ninguna pregunta nueva. Esta revisión sustituye el alcance operativo de la
> rev. 25, que se conserva debajo como historia.
>
> **rev. 25 (2026-08-29, más noche; corregida tras el PR).** La trasera
> capturada como las mejillas. **Al mecanizado (§D)**: un segundo bolsillo en
> la cara interior de cada anillo (11 × 6, a lo largo del tramo trasero,
> cerrado por los dos extremos, con un escalón bajo el chaflán) y el rebaje
> del costado a 17 en ese tramo; P6 (y P5) a chaflán 6. **Al acrílico (§A)**:
> un chaflán de 5.5 × 45° en la arista de abajo de la trasera, por la cara
> exterior. **A la chapa
> (§B)**: el talón pasa a ser la nariz en espejo (dos dobleces a 45° y ocho
> pestañas lanzadas a r = 2 t con alivio, en 6082-T6 obligatorio: cada lengüeta
> puede llevar 159 N en la punta) y el techo baja con chaflán + labio (dos a
> 45°) en vez de
> banda a 90°. **A la casa de acrílico (§A)**: la trasera **sin un solo
> taladro**, 552.32 × 237.18. §B ya no pregunta por el radio de la pestaña:
> es el mismo r = 3 que el resto de la chapa.
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
> | B | chapa de aluminio (y acero) | **techo macizo** (sin ranuras, labio de 20, bridas R2), **talón** (pie de 22.5 y muescas), **nariz** (pie de 20.5 y muescas), **marco de la ventana ×2**, tapa del valle, chasis ×3 |
> | C | carpintería | la tabla (suelo + zócalo) |
> | D | mecanizado de aluminio | el anillo ×2, con rebaje de chapa y cajeado de brida por la cara interior |

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
   pieza —la tapa del valle— y esa pasó a chapa de aluminio. Y una sola pieza
   desde el 2026-10-11: la trasera. Las dos mejillas las sustituyó la persiana,
   de aluminio, que va a §D.)*

### Por qué estas tres y no otras

El **recocido** es el que decide cómo está la pieza dentro de tres años. El
fresado deja tensión atrapada alrededor de cada agujero y cada canto; sin
recocer, el PMMA craquela —una telaraña de grietas finas— empezando por los
taladros, y se acelera donde hay un tornillo apretado o donde tocó un
limpiador. No se ve al desembalar.

El **diamantado** es el que decide si el aparato parece comprado o cortado a
medida. Eran ~7,5 m de canto visible, y el acrílico es translúcido: la luz
viaja por dentro de la plancha y sale por el canto, así que un canto áspero
se ve como una línea blanca lechosa rodeando cada pieza. **Desde el
2026-10-11 ningún canto de acrílico queda a la vista**: la trasera es la única
pieza, y sus cuatro cantos van dentro de los bolsillos del anillo y tras los
labios del techo y del talón. Si el diamantado sigue siendo eliminatorio lo
decide Samuel (HUECO); hasta entonces se pregunta.

El **colado** ya está decidido en la spec §11 y no es negociable: el
extruido trae tensión interna de fábrica y craquela solo.

**Lo que ESTE taller ya no hace:** taladrar, desde el 2026-08-27 (los ocho
agujeros del costado se fueron al anillo de aluminio), y el costado, desde el
2026-10-11 (es la persiana, de aluminio). La trasera es un contorno con su
cajeado y nada más. Eso quita de un plumazo el sitio por donde el PMMA
craquela primero, pero **no quita el recocido**: la tensión también la deja el
fresado del canto.

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
pieza se mecaniza en un taller aparte (§D). Lo que sí hace: el **techo
macizo** (blank 593.02 × 78.85, sin ranuras, retorno de 9, labio de 20 y una brida R2 en
cada punta), el **talón** (blank 545.62 × 42.23, pie de 22.5 con muescas y
ocho pestañas lanzadas), la
**nariz** (la banda del frente, blank 545.62 × 53.10, tres dobleces), los
dos **marcos de la ventana** (pletina de 6 cortada a láser, con seis cajeados
por el lado del anillo, un par espejado) y la **tapa del valle** (aluminio de
3 mm, blank 560.00 × 20.00, dos pestañas y labio de apoyo de 2.0 mm). Son las piezas
que llevan los rieles y sostienen el marco por dentro del anillo. (La bahía,
tercer miembro hasta el 2026-08-29, y las placas, clips, escuadras y marcos de
la trasera, muertos esa misma noche, ya no existen.)

1. **¿Pliegan aluminio 6082-T6 de 1.5 mm a 90°, y con qué radio interior
   mínimo?** El modelo asume **r = 3** (2 × t) y de ahí cuelga el desarrollo
   del miembro alto, el talón, la nariz y las bridas. Si su radio mínimo es otro,
   **decirlo antes de cortar**: el recorte cambia. **Y a 45° y a 35°, con el
   mismo radio?** La nariz lleva dos dobleces a 45° y uno a 35°, el talón dos
   a 45° y el techo tres a 45°, contando el retorno y el chaflán. Los
   desarrollos están calculados con el mismo radio y factor K. **Y una pestaña lanzada**
   (las ocho del talón: 25 × 8, cortadas en U de 0.5 con un alivio de Ø2 en
   cada esquina del corte y dobladas 90° hacia arriba con el mismo r = 3)?
   Se pensó con r = 1 t y se deshizo: el diseño no puede colgar de una
   respuesta del taller.
2. **¿Qué factor K usan?** El modelo asume **k = 0.42**. Con r = 3 y t = 1.5
   eso da BA = 5.70 y BD = 3.30 mm por doblez. Si trabajan con otro, los DXF se
   regeneran — pero hay que saberlo, no adivinarlo.
3. **¿Qué aleación y temple suministran, y con qué `Rp0.2`?** **Desde la
   rev. 27 es eliminatoria para todas: 6082-T6/T651**, por color: todo el
   aluminio negro que se ve va en una aleación y un lote (§E). Por cálculo, el
   techo y la nariz pasarían con 130 MPa (el techo SOLO trabaja a 95 MPa con
   200 N en el centro de la meseta). **El talón lo pide además por resistencia:
   Rp0.2 ≥ 240**, porque sus ocho lengüetas sujetan el canto de abajo de la trasera
   y la más cargada trabaja a 199 MPa en la raíz (23.5: los 25 menos lo que
   muerde el alivio) con la carga en la punta — con 130 no pasa ninguna
   lengüeta de 1.5 (`guarda_trasera_flexion()`). Una aleación
   distinta **hay que aprobarla antes de cortar**, regenerando las puertas si
   cambia.

   **Y la tapa del valle, 6082-T6 de 3 mm, se dobla a R3 (1 t).** ¿Lo hacen sin
   fisurar? Si su radio mínimo en ese espesor es mayor, díganlo con el
   presupuesto: es un HUECO del diseño (`radio_doblez_valle`), no una cota que
   el taller pueda cambiar por su cuenta.

El techo de esta tanda **no lleva ranuras**. Se eliminan 16 operaciones del
blank y no aparece ningún proceso nuevo de chapa. Por eso no se añade una
pregunta: basta cotizar el desarrollo vigente y sus pliegues.

La tapa del valle apoya sobre el primer Z-Rail de la fila auxiliar KONDOR.
La tira anti-ruido de 0.20 mm nominal (0.10 mm montada) es consumible de
montaje y **no se pide al taller ni tiene DXF**. La fila mide 55 mm, no sigue
el estándar Intellijel 1U, y los tres planos de panel quedan rehundidos
1.50 mm respecto del anillo; no cambiar estas cotas para acomodar otro riel.
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

Un retazo de la especie propuesta, 30 mm, con el canto redondeado R8 acabado como se
entregaría. Se compara contra el naranja del cuerpo — **la tabla y el acrílico
se ven juntos y a la vez**, y eso no lo contesta ningún render.

---

## D. Taller de mecanizado — preguntas eliminatorias

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
   Son 14 M4 en la cara interior y 3 M5 en el canto inferior, por anillo. En
   esa misma cara interior van tres operaciones nuevas de la rev. 26:
   el **rebaje de chapa de 4.5 de ancho × 3 de fondo**, solo por el contorno
   donde se ve chapa; **un cajeado de brida por anillo, 28 × 15.5 × 3**, con
   esquina interior R1.5; y el tramo trasero de 23, con bolsillo en
   u = 5.5..16.5, pared de 3 y 3.5 de rebaje vacío. Bajo los dos labios de
   chapa el labio del bolsillo queda con 3 de hondo; en el resto conserva 6.
   Y desde la rev. 27, por la cara de FUERA, **diez bolsillos por anillo** para
   los tacos de la persiana (`costilla_bolsillos_2d`): Ø9 × 3.8 con un asiento
   de imán de Ø6.1 × 3.1 (× 1.1 en los dos de atrás), y dos de ellos
   localizan: uno a **Ø8 H7** y una **colisa de 8 H7 × 10**.
4. ¿Hacen **chaflán mecanizado de 1.5 × 45°** en dos aristas de la cara
   vista, por pieza?
5. ¿Anodizan en **negro**, con **enmascarado de un punto** antes de
   anodizar (para el bonding de tierra)? Si no lo hacen ellos, el anodizado va
   a §E: uno solo para todo el negro.

**Única pregunta abierta de esta tanda:** «¿Un reborde de **1 mm de ancho por
3 de alto** a lo largo del contorno, con tolerancia **+0.3 / −0**: se puede?
Si no, lo subimos a **1.5**.» No cambiarlo en máquina sin respuesta: esa cota
mueve el rehundido de las tres chapas y sus desarrollos.

**Y la profundidad del rebaje, 3 mm, va con `+0 / −0.4`** — también
asimétrica, y por la razón inversa. Por arriba la limita la esbeltez del
reborde (a 3.1 con un reborde de 1 ya son 3.1:1); por abajo solo gasta captura
de la chapa, y hay de sobra: a 2.6 el canto todavía engancha 2.1 mm, más de un
espesor. **Si su tolerancia normal en fondo de cajeado es mayor que 0.4,
dígalo**: se sube el reborde y la banda se abre por arriba.

**La tolerancia del reborde es asimétrica a propósito, y no es un capricho.** La rev. 26
pedía ±0.1, que es una contradicción: nuestra propia puerta
(`guarda_rebaje_chapa`) rechaza cualquier reborde por debajo de 1 —a 0.9 deja
de ser una junta de sombra fresable y pasa a ser una rebaba—, así que pedir
±0.1 era aceptar por contrato una pieza que rechazamos por diseño. Por arriba
sí hay sitio: el reborde puede engordar hasta 1.3 sin que nada se mueva, porque
lo que la chapa pierde de rehundido lo gana de reborde y la junta sigue
leyéndose. **Si sale por debajo de 1, la pieza no vale**; si sale por encima,
vale hasta 1.3.

**Y una cosa que el taller tiene que saber antes de cotizar:** en la esquina
donde el bolsillo de la trasera pasa bajo el chaflán de abajo-atrás (P6), el
escalón del bolsillo deja **0.5 mm en x de la cara del chaflán — 0.35
perpendiculares — a lo largo de 6 mm de profundidad**. Es un filo. Viene del
diseño de la trasera capturada (2026-08-29), no de esta tanda, y está declarado
como deuda en `check_dxf.anillo_tiene_rebaje()`. **Si a su criterio ese filo no
sobrevive al fresado, el desbarbado o el anodizado, dígalo con el presupuesto:
preferimos moverlo antes de cortar que descubrirlo en la primera pieza.**

### Muestra que se pide con el presupuesto

Un **cupón de 100 mm del perfil del anillo** — mismo espesor, mismo rebaje,
mismo chaflán, mismo acabado, mismo anodizador — **antes de cortar los dos
anillos completos**. Las cotas de la cara vista (chaflán, rebaje, rehundido)
salieron de escalar una foto de referencia y están marcadas ESTIMADO en la
spec de diseño; el cupón es lo que las cierra contra la pieza real, no contra
el render.

Desde la rev. 26, ese mismo cupón reproduce además el **rebaje de chapa de
4.5 × 3 y el reborde de 1 × 3**. Es la pared delicada que se valida antes del
anillo completo.

El plano es **`plans/cupon_anillo_2d.dxf`**: la sección del perfil, a 1:1 y en
mm. Va con una rosca ciega M4 a media longitud y un punto de bonding
enmascarado en la cara interior. El PLIEGO (§ anillo) lleva la tabla de lo que
se mide cuando vuelve y qué se cambia si no pasa. **Es un punto de parada: sin
cupón aprobado no se corta el material de los anillos.**

### Registro

| fecha | proveedor | planitud confirmada | anodizado | cupón aprobado | tira de la persiana aprobada |
|---|---|---|---|---|---|
| (pendiente) | | | | | |

### La persiana (rev. 27)

Dos placas de **6082-T651 laminado y estirado**, pletina de 12 frenteada a
9.5, con 45 ranuras y diez tacos del mismo bloque: el pliego (§6.3) lleva el
orden de operaciones y lo que trae cada uno de sus tres DXF.

6. **¿Garantizan planitud ≤ 0.2 en 320, después de ranurar y de anodizar?**
   Es eliminatoria, como la del anillo: la persiana apoya en la cara del
   anillo por toda su banda, y esa sujeción decide cómo suena.
7. ¿Pueden **ranurar a 4 de fondo por delante con las paredes acabadas** y
   dar después el pasante de los últimos 2 mm **por tramos, sobre placa de
   sacrificio**? Sin ese orden, las varillas de 248 vibran al cortarlas. La
   placa lleva alojamiento para los diez tacos del dorso (Ø8 × 3.5), que van
   espejados en la segunda persiana: la pieza apoya plana, no sobre los tacos.
8. ¿Trabajan con **fresa Ø3 de 3 filos**, **chaflán 0.2 × 45°** en las aristas
   de delante y **0.3 × 45°** en la arista de atrás del contorno?
9. Son **dos programas**: las dos persianas son un par espejado (las ranuras
   ciegas, los atados y los tacos por la cara opuesta en cada una).
10. Los dos localizadores ajustan a **Ø8 H7/g6 después de anodizar**, y el
    anodizado crece en las dos piezas. ¿Mecanizan contando con esa crece, o
    enmascaran los localizadores y sus bolsillos?

**Muestra, antes que las dos persianas (#398):** una **tira de altura
completa**, 60 × 256 mm, cortada de la propia persiana (x ≈ 270–330), con los
dos atados, la banda ciega, el borde de 4 y dos tacos con sus imanes sobre una
placa de 14 con dos bolsillos. Mismo material, mismo taller, mismo anodizador.
El pliego (§6.3) dice qué se mide en ella.

---

## E. Anodizador — uno para todo el negro (rev. 27)

Todo el aluminio que se ve va anodizado en negro **por un solo anodizador y en
un solo lote**: los dos anillos y las dos persianas (de §D) con el techo, la
nariz, el talón, la tapa del valle, la tira negra del valle y el marco de la
ventana (de §B). Puede ser el propio taller de §D si anodiza; si no, es un
pedido aparte. El pliego (§6.4) lleva el detalle.

1. **¿Anodizan en negro 6082-T6/T651, ISO 7599 clase AA15–AA20, sellado**,
   **en un solo lote** para piezas de dos talleres? (La clase está citada de
   memoria: confírmenla.)
2. ¿Ponen los **contactos del bastidor en caras tapadas** — el dorso de la
   banda de la persiana, la cara interior del anillo — y **enmascaran un
   punto** por anillo?
3. ¿Cierran el anodizado en **cantos de 2 mm con arista rota de 0.2** y en el
   **fondo de ranuras ciegas de 3.5 a 6.3 de ancho y 4 de hondo**? Es lo que
   mide la tira de muestra de la persiana (§D).

### Registro

| fecha | proveedor | lote único | negro AA15–AA20 | tira aprobada |
|---|---|---|---|---|
| (pendiente) | | | | |
