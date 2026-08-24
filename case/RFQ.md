# RFQ — cuerpo de acrílico del SAM17

Documento para pedir presupuesto. Va **antes** que el pliego
([`PLIEGO.md`](PLIEGO.md)): el pliego dice qué hay que hacer, esto sirve
para saber **quién puede hacerlo**.

**Lo que se busca no es «un CNC».** Es una **casa de acrílico** — de las que
hacen vitrinas, expositores y museografía. Un CNC general fresa la forma y
la entrega tal cual sale de la máquina. Una casa de acrílico tiene la
pulidora de diamante y el horno de recocido como equipo estándar. Los dos
presupuestos parecen el mismo trabajo y no lo son.

---

## Preguntas eliminatorias

Si alguna respuesta es «no», no es el taller. No se negocia por precio.

1. **¿Hacen RECOCIDO (annealing) de las piezas después de mecanizar?**
   ¿A qué temperatura y con qué rampa de enfriamiento?
2. **¿Hacen PULIDO DIAMANTADO de canto en máquina?** (Pulido a llama **no**
   sirve: mete tensión y deshace el recocido.)
3. **¿Trabajan PMMA COLADO (GS)** en 8 mm y 5 mm, en naranja translúcido?

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

---

## Preguntas de cota

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
