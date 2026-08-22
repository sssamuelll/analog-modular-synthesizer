# Contrato: módulo de voz que se mide a sí mismo

> Lo consumen los módulos **5 (VCF), 6 (ADSR) y 7 (VCA)**, ninguno dibujado, y
> lo estrena el **módulo 3 v2**
> ([`2026-08-22-modulo-3-vco-ocho-voces-design.md`](2026-08-22-modulo-3-vco-ocho-voces-design.md)).
> Origen: núcleo §5.3 y §10; issue #158.
> Este documento define **una interfaz**, no una placa. Vive aparte a propósito:
> enterrado dentro del spec de un módulo concreto, los otros tres lo copiarían
> mal.

## 1. El problema que resuelve

El J2 lleva **cuatro líneas de afinación** y están cableadas solo en la ranura 1.
Con ocho voces no dan, y ponerle más pines no escala: serían cuatro por cada
ranura capaz de llevar un módulo de voz, o sea 32 pines solo para eso (núcleo
§5.3).

La salida es el movimiento que este diseño ya hizo tres veces —el mux de
perillas, el sensado de jacks, las medidas del módulo 4—: **que el módulo mida y
mande los números**. Coste en pines del cerebro: cero. El contrato del J2 **no
cambia ni un pin**.

## 2. Qué es un módulo de voz que se mide a sí mismo

Un módulo que cumple estas cinco:

1. **Tiene un micro propio** y todo lo que reporta pasa por él.
2. **Se mide**: cronometra o lee lo que en él se desvía, y manda números.
3. **Se declara**: EEPROM `24AA02E48` en 0x50 con tipo, revisión, serial y su
   blob de calibración. La calibración viaja con la placa.
4. **Se deja auditar**: sensa la ocupación de sus jacks y lee por ADC toda
   entrada de CV patcheable, para que el barrido por inyección del núcleo §7.6
   sea posible.
5. **Se deja gobernar**: cada capacidad suya es un parámetro con descriptor y
   ámbito (`por-voz` / `compartido`). Lo que no está en el modelo no existe
   (núcleo §2.1).

## 3. Quién suelta el `MISO` — el hueco que este contrato cierra

`MISO` es un **bus compartido entre ocho ranuras** y el contrato congelado no
decía quién lo suelta. El spec del cerebro (§4.1) puso cuatro defensas y fue
honesto sobre la última:

> «una resistencia de serie no evita la pelea, la hace sobrevivible. Lo que evita
> la pelea es la pieza 4, y esa vive en placas que todavía no se han dibujado —
> salvo una, que ya está en gerbers y nunca leyó este documento.»

Esa placa es el módulo 3 v1, y es la que se está rediseñando. **El contrato se
cierra aquí**, y el micro lo hace posible:

> **Regla 1 — El `MISO` del J2 lo suelta el micro del módulo, y nadie más.**
> En alta impedancia siempre que su `CS` esté alto, sin excepciones de modo. Se
> mide en el bring-up: `CS` alto, `MISO` sondado. Aprobado o suspenso.

Esto es lo que un micro garantiza y un chip de conversión no: los AD5686R de la
v1 arrancan en modo standalone con su salida deshabilitada, o sea que sueltan la
línea **exactamente en el estado en que no sirve para nada**, y su datasheet no
dice qué hacen con la cadena encendida, que es el estado en el que hay control de
tono.

### 3.1 Consecuencia: el SPI de dentro del módulo es privado

Si el micro es el único que habla por el J2, **los chips del módulo dejan de
colgar del bus del instrumento**. El cerebro le habla al micro; el micro le habla
a sus conversores por un SPI suyo, dentro de la placa.

> **Regla 2 — Del J2 cuelga el micro, no los chips del módulo.**

Lo que compra, y es más de lo que parece:

- **La pelea del `MISO` se acaba de raíz**, no se hace sobrevivible.
- **La trama de 72 bits deja de estar clavada en el contrato.** Era el tamaño de
  la cadena de tres conversores de la v1: un número de una placa concreta metido
  en una interfaz común.
- **Cuántos conversores lleva el módulo deja de ser asunto del cerebro.** El
  módulo 3 v2 puede llevar cuatro u ocho sin que nadie fuera se entere, y ese
  conteo es hoy una decisión abierta suya.
- **El módulo puede hacer trabajo local** entre dos tramas: interpolar, suavizar
  un salto, sostener un portamento, sin gastar ancho de banda del bus.

Lo que cuesta, y hay que presupuestarlo: **una etapa más de latencia** entre lo
que el cerebro manda y lo que el chip recibe. Irrelevante para el tono; **no
irrelevante para un disparo**, que es justo lo que el #160 pide acotar. Riesgo 1.

## 4. Qué reporta, y con qué cadencia

Tres clases, y no se mezclan porque no corren al mismo ritmo:

| Clase | Qué | Cuándo |
|---|---|---|
| **Medida de calibración** | La frecuencia real de cada oscilador del módulo | Solo durante un barrido, y lo pide el cerebro |
| **Estado del patch** | Qué jacks tienen cable; el valor de cada entrada de CV | Al cambiar, y en el barrido de arranque |
| **Salud** | Temperatura de cada racimo, tensiones de riel si las mide, identidad | Lento y periódico |

Reglas que las gobiernan:

> **Regla 3 — El módulo nunca habla sin que le pregunten.** El J2 es un bus con
> ocho ranuras; un módulo que hable por su cuenta se pelea con otro. Todo va a
> petición del cerebro.

> **Regla 4 — Las medidas son parámetros de primera clase, no un canal aparte.**
> Núcleo §3.4 ya lo decidió: entran por el mismo camino que cualquier otro
> parámetro, con su descriptor. Así el agente y las tres pieles las ven sin que
> nadie escriba nada para ellos.

> **Regla 5 — El conteo de voces lo dice el descriptor, nunca una constante.**
> Las voces del instrumento son el mínimo de la cadena (núcleo §3.6): con ocho
> osciladores y cuatro filtros, el instrumento tiene cuatro voces **y lo dice**,
> en vez de sonar raro.

> **Regla 6 — Lo que no se pudo medir se reporta como hueco, con su motivo.**
> Nunca un valor por defecto que parezca una medida. Es el `HUECO` de la casa
> aplicado al bus: un cero silencioso consigue no medir *y* que nadie se entere.

## 5. El reparto con el cerebro

Lo que se muda al módulo y lo que se queda, dicho explícitamente porque hoy está
repartido de otra forma:

| Pieza | Antes | Ahora |
|---|---|---|
| Cronometrar los osciladores | El cerebro, con su PIO y las 4 líneas del J2 | **El módulo** |
| `autotune_budget.py` | En `hardware/02-midi-cv/` | **Se muda al módulo que mide** |
| Los 131 ns de jitter del 74HC14 | Requisito del cerebro sobre una pieza que vive en el módulo 3 | **Requisito interno del módulo** |
| Decidir cuándo se afina y con qué tabla | El cerebro | **El cerebro** — no cambia |
| La tabla de 84 notas y la corrección | El cerebro | **El cerebro** — no cambia |
| Las 4 líneas `TUNE_OUT` de la ranura 1 | Único camino de afinado | **Camino heredado.** Un módulo que cumple este contrato no las usa |

El cerebro **conserva el criterio**: cuándo afinar, qué hacer con los números,
cuándo dar una voz por mala. El módulo aporta **la medida**, no el juicio.

### 5.1 Compatibilidad hacia atrás

La ranura 1 sigue teniendo sus cuatro líneas cableadas y rotuladas. Un módulo de
cuatro voces que las use sigue siendo válido: **este contrato no las deroga, las
deja de necesitar.** Y el cerebro ya tiene que decir por el modelo si hay camino
de afinado en la ranura donde está el módulo, así que la diferencia es visible en
vez de silenciosa.

## 6. Lo que este contrato hereda del núcleo §10

Todo módulo que lo cumpla trae además, sin renegociarlo:

- EEPROM `24AA02E48` en 0x50, y `TMP1075` de telemetría.
- **El mux de perillas vive en el módulo**, no en el cerebro.
- Las lecturas vuelven por el `MISO` del J2, sin hilos nuevos.
- Un LED de la cadena WS2812 por perilla y por jack.
- **Al menos un destino de timbre `por-voz`** en los módulos 5, 6 y 7 — corte con
  CV propio por voz en el 5, aunque las perillas del panel sean comunes. Sin eso
  **MPE es imposible** (núcleo §3.6), y `architecture-poly.md` §3 todavía los
  describe con «corte y resonancia comunes a las 4»: hay que corregirlo.
- **Declarar el ámbito de cada parámetro**. Sin la marca, ni la interfaz sabe
  dibujarlo ni el agente sabe qué puede mover por nota.

## 7. Riesgos y decisiones abiertas

1. **La latencia del reenvío** (§3.1). El módulo deja de recibir la trama
   directamente y la recibe reenviada por su micro. Cierra: un presupuesto de
   temporización de evento —que hoy no existe en el repo— con su criterio de
   aprobado y suspenso **declarado antes de medir**, igual que se hizo con los
   131 ns del 74HC14. Es la misma pieza que pide el #160 para el disparo de
   percusión, y **debe diseñarse una sola vez** para los dos.
2. **Los gates dentro de la trama.** El #158 obliga a mudarlos porque cuatro
   cables no dan para ocho voces, y el núcleo §5.3 ya dijo que además sincroniza
   mejor, porque tono y gate salen en el mismo instante. Este contrato **no lo
   resuelve**: define quién habla por el bus, no qué mensajes lleva. Cierra: al
   diseñar el evento con sello de tiempo, junto al riesgo 1.
3. **El formato de los números.** Qué manda el módulo para «la voz 3 mide
   440,12 Hz»: unidad, resolución y si va crudo o ya en cents. Cierra: al
   escribir el plan, con el firmware del cerebro delante, porque quien consume
   decide el formato.
4. **La longitud máxima del mazo por rama** no existe en ningún documento del
   repo, y sin ese número no hay presupuesto de flanco. Lo hereda del spec del
   cerebro y le afecta igual. Cierra: se declara en el plan y entra como
   constante citada en `enlace_budget.py`.

## 8. Fuera de alcance

- **Qué mensajes lleva el protocolo.** Este contrato dice quién habla y cuándo,
  no el catálogo de mensajes — eso es del núcleo §4.1.
- **El enrutado de audio entre módulos.** Se abre como su propio ciclo.
- **El firmware**, del cerebro y del módulo. Aquí está la interfaz.
