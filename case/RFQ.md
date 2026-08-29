# RFQ — el SAM17, taller por taller

Documento para pedir presupuesto. Va **antes** que el pliego
([`PLIEGO.md`](PLIEGO.md)): el pliego dice qué hay que hacer, esto sirve
para saber **quién puede hacerlo**.

> **rev. 22 (2026-08-28).** Son **cuatro** pedidos, no tres. La costilla deja
> de ser chapa plegada y pasa a **anillo de pletina mecanizada** — taller
> nuevo, §D, que no es el de chapa. El acrílico sigue **sin un solo
> taladro**. Cada bloque de preguntas es eliminatorio para SU taller y no
> dice nada de los otros.
>
> | § | taller | qué se le pide |
> |---|---|---|
> | A | casa de acrílico | costados ×2, trasera |
> | B | chapa de aluminio (y acero) | miembros ×3 (con bridas), placas ×6, clips ×4, escuadras ×2, **marco trasero ×2** (uno plegado, uno plano), tapa del valle, chasis ×3 |
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
pieza se mecaniza en un taller aparte (§D). Lo que sí hace: los tres
miembros del esqueleto (trasero bajo, trasero alto, bahía — cada uno con
brida de extremo doblada en cada punta), las dos escuadras de la trasera,
las seis placas de anclaje de riel, los cuatro clips de retención y la tapa
del valle. Son las piezas que llevan los rieles y sostienen el marco por
dentro del anillo.

1. **¿Pliegan aluminio 6082-T6 de 1.5 mm a 90°, y con qué radio interior
   mínimo?** El modelo asume **r = 3** (2 × t) y de ahí cuelga el desarrollo
   de los miembros, la escuadra y sus bridas. Si su radio mínimo es otro,
   **decirlo antes de cortar**: el recorte cambia.
2. **¿Qué factor K usan?** El modelo asume **k = 0.42**. Con r = 3 y t = 1.5
   eso da BA = 5.70 y BD = 3.30 mm por doblez. Si trabajan con otro, los DXF se
   regeneran — pero hay que saberlo, no adivinarlo.
3. **¿Qué aleación y temple suministran, y con qué `Rp0.2`?** No es
   eliminatoria: con 130 MPa el diseño pasa (miembros, escuadra y también el
   anillo de §D, cada pieza con su propia puerta). Lo que sí hace falta es
   que la digan. Una aleación distinta **hay que aprobarla antes de
   cortar**, regenerando las puertas si cambia.
4. **¿Cortan y roscan pletina de 4 y 6 mm sin plegar** (clips y placas de
   anclaje)? No llevan doblez, solo contorno, cajeado y rosca ciega o de
   paso.

**Los DXF que reciben son DESARROLLOS PLANOS, no contornos.**
`miembro_bajo_2d`, `miembro_alto_2d`, `bahia_2d`, `escuadra_trasera_2d`,
`marco_trasera_sup_2d` y
`tapa_valle_2d` traen el recorte; la pieza doblada mide menos. Cortar el
contorno de la pieza montada da un fichero válido e inservible — es el mismo
error que el modelo vigila con un sobre por pieza. **`costilla_2d` YA NO ES
DE ESTE TALLER**: desde el 2026-08-28 es un contorno real (sin plegar, sin
soldar) que se manda a mecanizado, §D.

**Las placas de anclaje y los clips tienen DXF propio desde el 2026-08-28**
(ver `PLIEGO.md` §6, tabla de «Lo que NO va a este taller»): `placa_cara_inf_2d`,
`placa_valle_2d`, `placa_cara_sup_2d`, `clip_2d`. El DXF trae el agujero
FUNCIONAL de paso M4 por riel (no el cajeado); el cajeado de Ø8 × 2.5 por el
lado del anillo va como nota de mecanizado en el mismo §6 — un DXF 2D no
dice profundidad — y hay que confirmarlo antes de cortar, como cualquier
otra cota que no está en el fichero.

### Preguntas de cota (aluminio)

5. ¿Qué **tolerancia de posición** garantizan en taladros de chapa? La rosca
   más justa de este taller hoy es el paso M4 del riel (con su cajeado por
   el lado del anillo) de la placa de `cara_inf`, a **6.88 mm** del canto, y
   el M4 de la brida de miembro más justo, a **6.75 mm** — el mínimo
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
   5 mm de carrera) en la posición del dibujo?
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
   silueta exterior y la pared del rebaje)?
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
