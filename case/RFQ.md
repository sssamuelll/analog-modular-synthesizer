# RFQ — el SAM17, taller por taller

Documento para pedir presupuesto. Va **antes** que el pliego
([`PLIEGO.md`](PLIEGO.md)): el pliego dice qué hay que hacer, esto sirve
para saber **quién puede hacerlo**.

> **rev. 21 (2026-08-27).** Son **tres** pedidos, no uno. El case dejó de ser
> «un cuerpo de acrílico» cuando la estructura pasó a aluminio: el acrílico
> bajó a piel y **ya no lleva un solo taladro**. Cada bloque de preguntas es
> eliminatorio para SU taller y no dice nada de los otros.
>
> | § | taller | qué se le pide |
> |---|---|---|
> | A | casa de acrílico | costados ×2, trasera, tapa de remate |
> | B | chapa de aluminio plegada | costillas ×2, tapa del valle, chasis ×3 |
> | C | carpintería | la tabla (suelo + zócalo) |

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
fueron a la costilla de aluminio. La pieza es un contorno y nada más. Eso quita
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

## B. Taller de chapa de aluminio — preguntas eliminatorias

Es el taller que ya hace las tres piezas del chasis de acero. **No es un taller
nuevo**: se le añaden tres piezas de aluminio. Y son las que sostienen el case.

1. **¿Pliegan aluminio de 3 mm a 90°, y con qué radio interior mínimo?** El
   modelo asume **r = 3** (1 × t) y de ahí cuelga todo el desarrollo. Si su
   radio mínimo es otro, **decirlo antes de cortar**: el recorte cambia.
2. **¿Qué factor K usan?** El modelo asume **k = 0.42**. Con r = t = 3 eso da
   BA = 6.69 y BD = 5.31 mm por doblez. Si trabajan con otro, los DXF se
   regeneran — pero hay que saberlo, no adivinarlo.
3. **¿Qué aleación suministran, y su `Rp0.2`?** Las puertas del modelo van
   contra **130 MPa**, que es un **5754 H22**. Un 6082-T6 da ~250 y sobra. Una
   aleación más blanda **hay que avisarla antes de cortar**.

**Los DXF que reciben son DESARROLLOS PLANOS, no contornos.** `costilla_2d` y
`tapa_valle_2d` traen el recorte; la pieza doblada mide menos. Cortar el
contorno de la pieza montada da un fichero válido e inservible — es el mismo
error que el modelo vigila con un sobre por pieza.

**La costilla lleva un alivio cuadrado de 6 × 6 mm** donde concurren dos alas
(una sola esquina, entre la trasera y el suelo). No es un error del dibujo: sin
él las dos alas se solapan al doblar y la chapa no cierra.

### Preguntas de cota (aluminio)

4. ¿Qué **tolerancia de posición** garantizan en taladros de chapa? La costilla
   lleva los ocho tornillos estructurales del case y el más justo deja **1.54
   diámetros** de material hasta el canto de la ventana.
5. ¿**Desbarban** el canto? No lleva ni recocido, ni diamantado, ni chaflán:
   esas tres cosas son del PMMA.

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
