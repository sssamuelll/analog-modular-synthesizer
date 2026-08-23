# La gramática del panel: la cara es lienzo libre, y se reparte aquí

**Estado: PROPUESTA.** No toca cobre, no toca cajón, no toca spec. El acta del
2026-08-23 dejó dicho: «El reparto de anchos de panel con los conectores ya
mudados […] Cada uno va en su propio pase». Este papel es ese pase. Se revisa
de a una, como todo lo que toca la caja.

**Principio rector, dictado por Samuel el 2026-08-23:** *no hay nada precioso
en un análogo como sentirlo — tocar potenciómetros, botones, sliders.* El
panel se diseña desde la mano, no desde la placa. Y la marca entra aquí: el
plan del case del día 21 dejó KONDOR «para más adelante»; más adelante es
este panel. Es el primer instrumento de la casa.

---

## 1. Qué decide y qué NO

**Decide:** la gramática — qué secciones tiene la cara, en qué orden, en qué
fila vive cada cosa, y cómo se comporta una perilla cuando el preset y la
mano no coinciden.

**NO decide:** la piel (color, tipografía, posición exacta de la marca — su
propio pase, con renders sobre el case real), el cajón y la mudanza de
conectores (#167), quién shiftea el crosspoint (#171), ni la lista final de
perillas (sale del censo, §6).

## 2. Lo que ya está legislado, y este papel hereda

Nada de esto se rediscute aquí; se cita:

| Ley | Fuente |
|---|---|
| «El panel físico es la superficie de **interpretación**: perillas-sensor, LEDs, bahía» | voz-total §0.2 |
| «Las perillas son sensores, mandan números, y los números viajan por cable plano sin ensuciarse» | acta E-2 |
| **La mano gana por parámetro** (gesto físico → `ANULADO` para el agente, en ese parámetro) | voz-total §0.2, ley de capas 1 |
| El panel de mandos es módulo clase **referente** (posee vínculos, no parámetros) | voz-total §0.3, cambio 15 |
| La bahía: 8 entradas + 8 salidas Thonkiconn, LED por jack, «el jack es un nombre que le da el preset» | voz-total §5.1 |
| Fila A = UN módulo (Voz + bahía, una cara continua) | acta E-3, E-2 |
| Fila B = rack Eurorack de verdad, con regleta e invitados | acta E-4, #169 |
| El mixer y la salida estéreo viven dentro del módulo de Voz | acta E-5, E-6 |
| Cabeza local del cerebro: pantalla SPI 2,8" + encoder con pulsador | cerebro-v2 §5.2 |

## 3. El descubrimiento que libera el diseño

De «las perillas son sensores» se sigue algo que la v1 no explotó: **la
posición física de una perilla no está atada a ninguna placa.** Una perilla
manda un número por cable plano al escáner del panel de mandos; puede vivir
en cualquier punto de cualquier fila sin costar un hilo de audio. La cara es
lienzo libre.

Las únicas piezas **ancladas** son las analógicas: los 16 jacks de la bahía
(audio a ±12 V — viven encima de su placa, tramos cortos) y los conectores
del mundo (que ya se van atrás, #167). Todo lo demás — perillas, botones,
LEDs, pantalla — se coloca donde la mano lo pida.

Consecuencia directa: el viejo reparto de §8 («mandos 120 mm en fila B»)
era una restricción imaginaria. Se propone derogarlo.

## 4. El reparto propuesto

### Fila A — la cara del instrumento

Una cara continua (E-2). De izquierda a derecha, **el orden del flujo de
señal** — la gramática que Prophet hizo canon y que sigue siendo la correcta
porque enseña el instrumento al que lo mira:

```
[ OSC ]  [ FILTRO ]  [ ENVOLVENTES ]  [ VCA · PAN · MEZCLA ]  [ BAHÍA ]
   la marca KONDOR / SAM17 en esta cara: posición exacta en el pase de piel
```

- Las perillas son **por programa**: una perilla CUTOFF habla con las 16
  voces a la vez, como en todo polifónico. Cómo se toca la matriz FM —
  identidad del instrumento — es la decisión C2 del inventario (§7).
- La **bahía cierra la fila a la derecha**: los cables hacia el mundo
  cuelgan del extremo, lejos de las perillas. El patch interno no ocupa
  cara — lo recuerda el preset (§5.1).
- Ancho disponible: **488,32 mm** (fuente: `voz_total_budget.py`, VERDE con
  Voz+bahía en 421,5). Quitando ~100 de bahía quedan ~388 mm de secciones:
  a paso de ~25 mm son **~45 perillas máximo** en tres alturas. ESTIMADO —
  la lista real la fija el censo (§6).

### Fila B — la cabeza y el rack abierto

- **Izquierda, ~150 mm: la cabeza del cerebro.** Pantalla 2,8" + encoder
  con pulsador (ya especificados), más los botones de programa (E1). Abajo
  y a la izquierda: donde la mano descansa, donde se cambia de preset sin
  taparse la cara del instrumento.
- **Resto, ~338 mm ≈ 66 HP: rieles abiertos para invitados.** La muerte del
  mixer separado (E-5) y la mudanza de los mandos a la fila A convierten a
  E-4 en un rack **generoso**, no simbólico. La regleta y la reserva de
  corriente ya están legisladas (#169: 160 mA/riel).

### Por qué así y no al revés

Arriba se **toca**, abajo se **configura y se expande**. Las perillas a la
altura de los ojos y de la mano alzada; los cables de los invitados y de la
bahía sin cruzar jamás la superficie de interpretación. Un solo gesto — girar
una perilla de la fila A — es un cambio de sonido, sin menú, sin página, sin
shift. La pantalla existe para **leer** (presets, calibración, diagnóstico),
no para tocar.

## 5. El recall: cuando la perilla y el preset no coinciden

El problema que perillas-sensor crea y la v1 no legisló: cargas un preset y
las 45 perillas físicas quedan apuntando a valores viejos. Tres opciones:

| Opción | Qué hace | Costo |
|---|---|---|
| **Salto** | Tocar la perilla impone su posición de inmediato | Brutal tras un recall: un roce = un salto de octava |
| **Captura al cruce** (pickup) | El parámetro espera a que la perilla cruce el valor guardado; ahí engancha | Un LED tenue por perilla que dice «aún no me capturas» |
| **Relativo** | Los giros suman en delta | La posición física miente siempre; anti-táctil |

**Recomendación: captura al cruce, con LED por perilla.** Y la costura con la
ley de capas se dice en voz alta: el `ANULADO` del agente ocurre **al primer
cambio efectivo** (al cruce), no al roce — tocar sin cruzar no captura nada.
Los LEDs entran en la línea de LEDs de `consumo_total_budget.py`.

## 6. Los números que vigilan esta propuesta

- `voz_total_budget.py` — la fila A con bahía ya cierra en VERDE; las
  perillas no lo mueven (sensores, §3). Los 16 jacks sí: ya presupuestados
  (§5.4 del spec, pila ≤ 50 de fondo).
- `consumo_total_budget.py` — suma ~45 LEDs de perilla + 16 de jack a su
  línea de LEDs cuando la lista exista.
- `check_censo_voz.py` — el censo dice qué parámetros existen; de ahí sale
  **la lista de los que ganan perilla dedicada** (los demás quedan en
  carcasas y agente). Esa lista es el siguiente papel de esta serie.
- El escáner de perillas (muxes analógicos → ADC del micro del panel de
  mandos) es diseño del módulo referente, no de este papel. Cota sana:
  3 muxes 16:1 leen 48 perillas con 3 entradas ADC y 4 líneas de selección.

## 7. Las decisiones de Samuel: el inventario completo

La primera versión de este papel listaba cuatro. Samuel cazó que eran más, y
tenía razón: contadas honestas son **veintitrés**, en seis familias. Cada una
con recomendación cuando la hay honesta; se recorren de a una, y lo que no se
decida aquí queda POR-DECIDIR en voz alta, no supuesto.

### A. La mano — qué se toca

| # | Decisión | Opciones, y recomendación si la hay |
|---|---|---|
| A1 | ¿Perillas con tope o encoders sin fin? | **Potes con tope** (recomendado): el feel analógico manda, y el precio — el recall — se paga en A3. Los encoders siempre «aciertan» tras un recall, pero se sienten a máquina |
| A2 | ¿Sliders, y dónde? | Samuel los nombró. Candidato natural: **envolventes ADSR deslizables** (la tradición Juno/Jupiter) — el gesto se lee de lejos y se agarra con cuatro dedos. Cuestan altura de cara y fondo de placa: si se aprueba, entra a `voz_total_budget.py` |
| A3 | El recall (§5) | **Captura al cruce con LED por perilla** (recomendada) vs salto vs relativo |
| A4 | Los parámetros discretos (formas de onda, modo del filtro, on/off) | **Botón ciclador + fila de LEDs** (recomendado: barato, táctil) vs selector rotativo (más analógico, más área) vs perilla con muescas |
| A5 | ¿Shift/alt en la superficie de interpretación? | **Prohibido** (recomendado): un gesto = un cambio de sonido. Lo que no gana control físico vive en carcasas y agente, no debajo de una tecla escondida |
| A6 | Paso y tamaño de perillas | ~25 mm ESTIMADO; se congela cuando el censo diga cuántas son |

### B. La vista — qué se ve

| # | Decisión | Opciones, y recomendación si la hay |
|---|---|---|
| B1 | ¿La cabeza lee el último parámetro tocado? | **Sí** (recomendado): giras CUTOFF y la pantalla dice nombre y valor. El número ya viaja por el cable plano; es gratis |
| B2 | ¿Pantallitas por sección? | **No** (recomendado): una sola cabeza. Sobriedad, consumo, y la cara no compite consigo misma |
| B3 | ¿La vida de las 16 voces en la cara? | **Sí** (recomendado): 16 LEDs respirando con sus envolventes — el alma del polifónico, visible. Entra en la línea de LEDs del consumo |
| B4 | La política de luz | Sobria vs exuberante. El QUÉ se enciende se decide aquí; el color y la intensidad, en el pase de piel |

### C. El motor en la cara

| # | Decisión | Opciones, y recomendación si la hay |
|---|---|---|
| C1 | El reparto de filas (§4) | **Mandos arriba + rack de 66 HP abajo** (recomendado) vs el viejo §8 (mandos abajo, cara A solo máquina) |
| C2 | **La matriz FM — la gorda** | Es «identidad del instrumento» (voz-total §5.2) y no cabe entera en perillas. (a) Sección propia: selección origen→destino + una perilla de cantidad; (b) perillas fijas para las rutas canónicas y el resto en carcasas; (c) todo en carcasas en v1. **Sin recomendación**: depende de cuántas rutas FM se tuercen EN VIVO, y eso lo sabe el intérprete, no el papel |
| C3 | Envolventes dedicadas | ¿Cuántas en cara, con su ADSR completo cada una? Cruza con A2 (sliders) y con el censo |
| C4 | El estéreo en cara | Qué perillas lo representan: PAN global, SPREAD/WIDTH, ¿algo por voz? La lista fina la da el censo, la categoría se decide aquí |
| C5 | Volumen maestro y auriculares | Perilla maestra dedicada + **jack de auriculares al frente** (recomendado — un sinte sin auriculares al frente no es un instrumento serio); la salida principal se va atrás con #167 |
| C6 | ¿Botón TUNE físico? | **Sí** (recomendado): la calibración de §4 del spec con su gesto de tradición, no enterrada en un menú |

### D. La bahía

| # | Decisión | Opciones, y recomendación si la hay |
|---|---|---|
| D1 | Posición | **Cerrando la fila A a la derecha** (recomendado): los cables cuelgan del extremo, lejos de las perillas. Alternativa: franja superior |
| D2 | Asignación en v1 | **Desde la cabeza/carcasas** (recomendado); el gesto físico en panel cabe después sin romper nada — los jacks ya tienen sensado y LED |
| D3 | Pares estéreo | ¿El preset puede declarar dos salidas como par L/R? (E-6 lo sugiere; costo cero en hardware — es semántica del relator) |

### E. La cabeza

| # | Decisión | Opciones, y recomendación si la hay |
|---|---|---|
| E1 | La botonera de programa | ¿Cuántos botones físicos de preset? ¿Banco×programa al estilo clásico, o solo pantalla + encoder? |
| E2 | ¿Transporte físico? | ¿Play/stop/tap-tempo en la cara, o el tiempo vive solo en el clock trasero y MIDI? |

### F. Identidad (la frontera con la piel)

| # | Decisión | Opciones, y recomendación si la hay |
|---|---|---|
| F1 | El idioma de la serigrafía | **¿CUTOFF o CORTE?** Primer instrumento de la casa: la decide la casa, no la ingeniería. Lo único recomendado: una sola lengua — bilingüe es ruido |
| F2 | Marca y tipografía | Pase de piel, ya declarado. Aquí solo se reserva el sitio |

## 8. Lo que sigue

Aprobada la gramática: (1) el censo produce la lista de perillas con nombre
y sección; (2) el pase de piel — color, tipografía, marca, renders sobre el
case; (3) #167 muda los conectores y el cajón se retoca una sola vez, con
la gramática ya congelada.
