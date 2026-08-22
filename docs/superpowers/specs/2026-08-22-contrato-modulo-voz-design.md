# Contrato de módulo de voz — DISUELTO

> **Estado: disuelto el 2026-08-22**, el mismo día en que se escribió y antes de
> pasar a plan, por
> [`2026-08-22-junta-vco-hallazgos.md`](2026-08-22-junta-vco-hallazgos.md) §4.10
> y §4.11.
>
> Este documento ya no define nada. Existe para que los enlaces que apuntan aquí
> no se rompan, para dejar constancia de **qué afirmaba y por qué no se sostenía**,
> y para decir **dónde vive ahora cada parte que sí valía**.
>
> Sus dos herederos son:
> [`2026-08-22-modulo-3-vco-dieciseis-design.md`](2026-08-22-modulo-3-vco-dieciseis-design.md)
> (el cobre) y
> [`2026-08-22-vco-orquestacion-design.md`](2026-08-22-vco-orquestacion-design.md)
> (la ejecución).

## 1. Qué pretendía ser

Una interfaz común para los módulos **5 (VCF), 6 (ADSR) y 7 (VCA)** —ninguno
dibujado— estrenada por el módulo 3 v2. Vivía aparte del spec de un módulo
concreto a propósito, con el argumento de que enterrada dentro de uno los otros
tres la copiarían mal.

El problema del que partía era real y sigue siéndolo: el J2 lleva **cuatro líneas
de afinación** cableadas solo en la ranura 1, con más de cuatro osciladores no
dan, y ponerle más pines no escala —serían 32 pines solo para eso (núcleo §5.3)—.
**Ese problema no se disuelve; su solución tampoco.** Lo que se disuelve es la
generalización que se construyó encima.

## 2. Por qué se disuelve

### 2.1 Sus cinco propiedades eran esta placa con otro nombre

El documento definía «módulo de voz que se mide a sí mismo» con cinco
propiedades: micro propio, se mide, se declara, se deja auditar, se deja
gobernar. Puestas una al lado de otra, no describen una categoría de módulos:
**describen el módulo 3 v2**. Una interfaz que solo tiene un implementador
posible no es una interfaz, es una descripción con la etiqueta cambiada.

### 2.2 Dos de las cinco son insatisfacibles por sus propios consumidores

**«Se mide».** `architecture-poly.md` §11.3 ya decía que al filtro **no hay nada
que lo escuche** y que su apareamiento *«no se resuelve con calibración digital
como el tono»*. El VCF, el ADSR y el VCA presentarían «se mide a sí mismo» como
**hueco permanente, para siempre**. Un contrato cuya propiedad central es un
hueco en tres de sus cuatro firmantes no es un contrato.

**«Tiene micro propio».** El núcleo §10, en su sección de lo aplazado a
propósito, reservaba al diseño del módulo 5 decidir si los módulos 5/6/7 llevan
micro propio o se resuelven con registro de desplazamiento y ADC en la cadena
SPI, **y explicaba por qué se podía aplazar sin riesgo: las dos opciones caben en
el J2 ya congelado**. La Regla 2 de este contrato cerraba esa decisión por
decreto, desde el spec de otro módulo, sin el dato que la iba a cerrar.

### 2.3 Y llevaba el nombre de la propiedad más frágil

El título del documento era la propiedad que solo su autor posee. Eso no es un
detalle de redacción: es lo que hacía que la generalización pareciera legítima.

## 3. Dónde vive ahora cada parte

| Del contrato | Qué era | Dónde vive ahora |
|---|---|---|
| §1, el problema del J2 | Cuatro líneas de afinación no escalan | Sigue vigente: núcleo §5.3. Su solución en este módulo: cobre §2, decisión 2 |
| §2, las cinco propiedades | La generalización | **Eliminada.** Lo que describían es cobre §2 y §3 |
| §3, **Regla 1** — quién suelta el `MISO` | Interfaz real y valiosa | Orquestación §7, **R-J1** — reenunciada **sin presuponer un micro**, para que un registro de desplazamiento que suelte bien la línea también cumpla |
| §3.1, **Regla 2** — del J2 cuelga el micro | Decisión de una placa vendida como ley | Orquestación §7, **R-J2** — pasa a ser decisión del módulo 3 v2 (cobre §2, decisión 3), y el núcleo §10 **queda abierto** otra vez |
| §3.1, lo que la Regla 2 compra | Trama desclavada, conteo de conversores privado, pelea del `MISO` resuelta | Orquestación §7, y el trabajo real que eso obliga es el cambio 1 de orquestación §8 |
| §3.1, lo que cuesta: una etapa de latencia | Riesgo 1 del contrato | Orquestación §9, riesgo 1, con el presupuesto `evento_budget.py` nombrado |
| §4, **Regla 3** — no habla sin que le pregunten | Cadencia de bus | Orquestación §7, **R-J3** |
| §4, **Regla 4** — las medidas son parámetros | Ya era del núcleo §3.4 | Orquestación §7, **R-J4** |
| §4, **Regla 5** — el conteo de voces sale del descriptor | Correcta, e insuficiente | Orquestación §7, **R-J5**, refinada por **R-M6**: en este módulo el conteo sale del **estado** y cambia con el preset |
| §4, **Regla 6** — lo que no se pudo medir es hueco | Correcta, y hoy imposible de expresar | Orquestación §4, **R-F1**, y el cambio 5 de orquestación §8, que es lo que la hace representable |
| §4, la tabla de tres clases y sus cadencias | Buena, y sin números | Orquestación §7.1, con las cadencias **declaradas** (50 ms el patch, 1 Hz la salud) |
| §5, el reparto con el cerebro | La medida se muda, el criterio se queda | Orquestación §3.1. La mudanza de `autotune_budget.py`: cobre §15 |
| §5.1, compatibilidad hacia atrás | Las cuatro líneas de la ranura 1 no se derogan | Sigue vigente tal cual: núcleo §5.3, y cobre §2, decisión 2 |
| §6, lo que heredaba del núcleo §10 | Repetía el núcleo §10 sin añadirle nada | **Vuelve al núcleo §10**, que es donde estaba. Las piezas concretas de este módulo: cobre §9, §13 y §14 |
| §7, riesgo 2 — los gates dentro de la trama | Declarado y no resuelto | Orquestación §9, riesgo 2 |
| §7, riesgo 3 — el formato de los números | Abierto | Orquestación §9, riesgo 3, **ahora con criterio**: la resolución tiene que bajar de 0,139 cents |
| §7, riesgo 4 — la longitud del mazo por rama | Heredado del cerebro | Orquestación §9, riesgo 4 |
| §8, fuera de alcance | Correcto | Repartido entre cobre §19 y orquestación §11 |

## 4. Qué queda como enseñanza, para no repetirlo

Tres cosas, escritas porque el error fue barato esta vez y no lo será la
siguiente.

1. **Una interfaz con un solo implementador posible no es una interfaz.** Antes
   de sacar un contrato del spec que lo produce, hay que poder nombrar dos
   implementadores que lo cumplan sin dejar huecos permanentes.
2. **Un contrato no cierra decisiones que otro documento dejó abiertas a
   propósito.** El núcleo §10 explicaba por qué el micro de los módulos 5/6/7 se
   podía aplazar sin riesgo; ese razonamiento seguía siendo válido y el contrato
   lo pisó sin refutarlo.
3. **Enunciar las reglas de bus sin presuponer quién las cumple.** R-J1 dice
   «quien hable en esa ranura», no «el micro del módulo». Enunciada así, la regla
   vale para el módulo 3 v2, para un registro de desplazamiento en el módulo 5, y
   para lo que venga.
