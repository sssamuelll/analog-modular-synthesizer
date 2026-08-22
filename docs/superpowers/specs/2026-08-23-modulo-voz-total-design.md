# El módulo de Voz total: dieciséis canales completos, y la constitución que faltaba

> Diseño validado en sesión con Samuel el 2026-08-23, con crítica ontológica
> de la junta (Voronov) absorbida sección a sección. **Es papel, no cobre.**
>
> Este spec REABRE parcialmente el de los dieciséis osciladores
> (`2026-08-22-modulo-3-vco-dieciseis-design.md`, PR #164) y SUSTITUYE la
> arquitectura de módulos 5/6/7 de `docs/architecture-poly.md`. Lo que
> sustituye queda marcado en §10; nada se borra.

---

## 0. El acta constitucional

La junta encontró que cada tensión de este diseño venía de legislar con dos
constituciones a la vez: los principios de la era de 4 voces seguían vigentes
mientras las decisiones nuevas obedecían una regla que nadie había escrito.
Esta sección la escribe. **Es anterior a cualquier decisión de cobre.**

### 0.1 La regla de la frontera

> **La modularidad es una sola propiedad con dos regímenes: programática en
> el interior, física en la frontera.**

Por dentro, todo punto de ruteo es reconfigurable a través del modelo — la
matriz de modulación, los selectores, el crosspoint de la bahía, los roles y
la dormancia **son** el patch, y un preset es un patch completo. Por fuera,
la modularidad es cobre y cable.

La frase corta: **por dentro el patch es un preset, por fuera es un cable.**

Dos derogaciones formales de `architecture-poly.md`:

- *«El cable siempre gana»* queda **restringido a los jacks de la bahía**
  (§5). Allí sigue intacto: meter un cable rompe el normalizado de esa
  conexión y el sensado de ocupación se lo cuenta al modelo.
- *«En el patch bay vive la modularidad»* (§5 de architecture-poly) se
  sustituye por la regla de los dos regímenes.

Y dos normas para disputas futuras, que es lo que una constitución debe dar:

1. **Toda capacidad de ruteo interior debe ser expresable en el modelo.**
   Ruteo que solo existe en soldadura sin declarar no es modular: es un
   normalizado declarado (§0.4).
2. **Todo lo que cruza la frontera debe ser físico.** Jacks, perillas, audio.

### 0.2 La representación del patch: la interfaz es la vista, no el motor

El patch interior se representa mediante la interfaz gráfica, en cualquiera
de sus carcasas: **app standalone, VST, MCP o web app vía wifi**. El agente
de IA no es un caso aparte: **MCP es una carcasa más** de la misma interfaz.

La distinción que evita contradecir «el instrumento toca sin computadora»
(architecture-compute): **la interfaz representa el patch; no lo ejecuta.**
El patch vive y corre en el cerebro y los módulos siempre; todas las carcasas
son vistas y editores del mismo modelo, y se renderizan **desde los
descriptores** — no desde tablas mantenidas a mano, que es exactamente lo que
la memoria de 32 KB del módulo vino a matar (#164). El bit de dormancia
(§6) tiene ahí su cara visible: el parámetro durmiente se pinta atenuado.

El panel físico queda como la superficie de **interpretación**: perillas-
sensor, LEDs, bahía. Tocar es físico, editar es programático, y ambos
escriben el mismo modelo.

### 0.3 Los cinco términos, definidos

La junta encontró cinco términos cargando todo el peso del diseño sin
definición vigente. Aquí están:

| Término | Definición |
|---|---|
| **Oscilador** | La unidad física de generación: SSI2130 + convertidor exponencial + tap a la matriz. El máximo común divisor de todos los roles. R-M6 de la orquestación sigue intacta |
| **Canal** | La unidad física de replicación: oscilador + filtro + VCA de resonancia + VCA de voz, soldados en la misma placa. El canal **ofrece** roles; no **es** ninguno |
| **Voz** | Rol computado del estado, nunca cobre: un canal cuenta como voz si su oscilador no es fuente de modulación de otro, no está en modo lento, y su VCA de voz participa de la salida |
| **Módulo** | Tres clases, declaradas en el descriptor (cambio 15 al núcleo, §7): **poseedor** (posee instancias de parámetro: la Voz, el mixer), **referente** (posee vínculos a parámetros ajenos: el panel de mandos), **relator** (posee aristas: la bahía) |
| **Carácter** | Criterio ejecutable, no gusto: es carácter **lo que procesa audio de forma no lineal** (el MS-20, los LEDs del lazo, un drive futuro) → analógico soberano. Lo que genera **control** (envolventes, CV) → del modelo. Lo que aplica **ganancia lineal** (los SSI2164) → indiferente, decide la ingeniería |

La fila de *carácter* disuelve el doble estándar que la junta señaló: la
exponencial de una RC es control, no audio — la disolución del ADSR en
firmware queda **legislada**, no colada. Y el 2164 dentro del lazo de
resonancia es ganancia lineal; la no-linealidad que define el carácter (los
LEDs) sigue siendo cobre soberano.

### 0.4 El normalizado declarado

La cadena soldada oscilador → filtro → VCA de voz es una **decisión, no un
accidente**: el tramo donde la modularidad programática eligió no tener
puntos. Sus dos puntos de ruptura son el **nodo de suma pre-filtro** y la
**salida post-filtro** — y son los únicos, por la regla de §5.2.

---

## 1. Qué es el módulo de Voz

El módulo 3 deja de ser «el VCO» y pasa a ser **la Voz**: dieciséis canales
completos, cada uno oscilador → filtro → VCA, soldado de punta a punta en la
misma placa. Los módulos 5 (VCF) y 7 (VCA) **desaparecen como hardware
separado**: su cobre se muda aquí. El módulo 6 (ADSR) desaparece como
circuito y se ejecuta **en los micros de este módulo** (§3), con sus perillas
en el panel de mandos (§8).

El módulo suelda canales y se llama Voz: el preset computa cuáles canales
son voces en cada instante (§0.3). En FM 8×2 hay 16 canales y 8 voces; los
filtros y VCAs de las moduladoras están **durmientes** (§6), no ociosos por
error.

**De #164 se conserva** (sin tocar): los dieciséis SSI2130 y sus tres
correcciones de exactitud, la matriz de modulación analógica de 16 líneas y
la digital de sync, la partición en dos columnas con dos micros RP2350B
(límite de PIO), la referencia única distribuida y bufferizada, el
convertidor de tono pegado a cada oscilador, los juguetes (§10 de aquel
spec), el camino de silencio, la telemetría y el J2.

**De #164 se reabre**: la partición física de placas (§8), el panel de 32
jacks (muere: §5), y el censo de parámetros y memoria (§7). #164 se mergea
tal cual — es el acta de su junta — y este spec declara la supersesión.

## 2. El canal analógico

```
            nodo de suma
SSI2130 ──────►(+)──► filtro MS-20 ──► VCA de voz ──► bus del mixer
   │            ▲     LM13700 + TL074      ▲          (¼ SSI2164)
   │            │     LP 24 dB/oct         │
   │      bahía: audio  LEDs en el lazo    │ CV de envolvente
   │      externo (§5)  res. por VCA       │ (generador local, §3)
   │                    (¼ SSI2164)        │
   └──► matriz de modulación FM (16 líneas), SIN filtrar
```

- **El tap de la matriz sale ANTES del filtro.** La moduladora de FM es la
  señal cruda del oscilador; filtrarla acoplaría el índice de modulación al
  corte.
- **El filtro es el MS-20 de la tesis** — LM13700 en dos celdas, pasa-bajo
  24 dB/oct, LEDs en el lazo de resonancia — elegido por carácter (§0.3) y
  estabilizado digitalmente (§4). **LP solo**: las variantes multimode/12 dB
  del doc funcional quedan fuera; la placa no reserva lo que nadie pidió.
- **La resonancia se controla por VCA** (¼ SSI2164 en el lazo), nunca
  digipot — herencia directa de architecture-poly §7, caso 2.
- **El VCA de voz es ¼ de SSI2164**: ganancia limpia; el carácter ya salió
  del filtro. 16 canales de voz + 16 de resonancia = 32 VCAs = **8× SSI2164**.
- **El nodo de suma pre-filtro** es donde entra el audio de la bahía y donde
  sobrevive la semántica D9 de la orquestación: lo externo **se suma**, no
  sustituye.
- **CVs nuevos por canal: 3** — corte, resonancia, envolvente. La velocity y
  el escalado son multiplicaciones en el micro del módulo, no canales de DAC.

## 3. Ejecución: las envolventes son generadores del módulo

El golpe más duro de la junta: al disolver el ADSR desaparecían las líneas
físicas `GATE`, y un ataque por trama J2 a 1 kHz queda cuantizado a 1 ms —
con R-M1 vigente («el módulo no interpola»), un ataque sub-milisegundo no
podía existir. La solución estaba dentro del módulo: **ya hay dos RP2350B**.

- **Las envolventes se ejecutan en los micros del módulo.** El cerebro manda
  el evento de nota y los parámetros (A, D, S, R, formas); el micro renderiza
  la curva localmente contra los DACs de envolvente por su SPI privado, a
  decenas de kHz. La *forma* del ataque no tiene límite de trama.
- **Enmienda a R-M1** (cambio 17 al núcleo): «el módulo no interpola
  parámetros» se mantiene, y se añade: «el módulo ejecuta **generadores**
  declarados en su descriptor». La envolvente es un generador, no una
  interpolación.
- **El evento de nota va en la trama** — resuelve el riesgo 2 de la
  orquestación (gates-en-trama) en la dirección que ya apuntaba.
- **Presupuesto nuevo y bloqueante: `ataque_budget.py`** — cota del camino
  completo nota-a-VCA. Estimación de diseño: USB-MIDI 1 ms + trama 1 ms +
  arranque del generador ≈ **2 ms peor caso**, el estándar de la categoría
  (USB-MIDI solo ya cuantiza a 1 ms). El script lo asevera con los números
  reales del protocolo, no con esta estimación.

## 4. Calibración: dos regímenes con nombre

La doctrina «el camino de afinación va antes del filtro, siempre»
(architecture-poly §5) era de una era con un solo régimen. Ahora hay dos:

**Afinación** (osciladores). Permanente, paralela, pre-filtro, invisible,
digital. Intacta de #164: conteo recíproco, 0,5 cents, TUNE_OUT por
oscilador.

**Caracterización** (filtros). Bajo demanda, **muxeada** (calibrar no tiene
la prisa que tenía afinar), y atraviesa el camino de sonido **en estado de
no-uso**: el filtro se mide convertido en oscilador. La premisa del README
del VCF — «no hay nada que escuche un filtro» — era **falsa para este
filtro en concreto**: auto-oscila por diseño, y un filtro auto-oscilando es
un oscilador senoidal que el Schmitt recorta y el conteo recíproco mide.

Tres lazos, con el VCA de voz cerrado (en silencio, como el autoafinado):

1. **Curva corte-vs-CV por canal**: resonancia al máximo, barrido del CV de
   corte, medida de la auto-oscilación → curva a la EEPROM de calibración.
   «Corte a 800 Hz» corta en 800 Hz en los dieciséis canales, cada uno
   corregido por su propia curva. La lotería del LM13700 deja de sonar
   despareja: se vuelve dieciséis offsets que el software se come.
2. **Compensación térmica**: el sensor de la telemetría interpola la curva
   con la temperatura — y con la fusión, ese sensor ve **la misma**
   temperatura que el expo del oscilador. Ganancia directa de soldar el
   canal entero en una placa.
3. **Ancla de resonancia**: el umbral de CV donde arranca la auto-oscilación
   de cada canal define «resonancia 100 %» de ese canal. La resonancia se
   siente igual en las dieciséis voces aunque los chips difieran.

La tesis que la junta pidió escribir, escrita: **se conserva el filtro por
lo inmedible (los LEDs, el carácter) y se estabiliza midiendo todo lo demás
(corte, tracking, umbral).** La dispersión del carácter entre canales no se
calibra: es lo que en un poly analógico siempre se llamó encanto.

## 5. La bahía asignable

### 5.1 Qué es

La frontera física del patch: **8 entradas + 8 salidas** en jacks
Thonkiconn (TN conectado, sensado de ocupación, LED por jack), ruteadas por
**dos AD75019** (crosspoint 16×16, ±12 V, carga serie): uno de entradas
(8 jacks → 16 destinos), uno de salidas (16 fuentes → 8 jacks). El jack deja
de ser un punto del circuito y pasa a ser **un nombre que le da el preset**;
su LED dice en color qué es. El recall del patch interior deja de ser
LED-guiado-manual (el arte previo de Lafayette anotado en el núcleo §6.3):
**se recuerda solo**. Solo los cables hacia el mundo siguen siendo físicos,
porque físico es el mundo al que van.

Es un módulo clase **relator** (§0.3): sus parámetros son aristas. Su
esquema de descriptor es el **cambio 15 al núcleo** (§7). Vive como módulo
propio con su bajada de J2, panel en la fila A junto a la Voz (§8).

### 5.2 La derogación, en voz alta

#164 (decisión 12) elevó a ley: «si el enrutado se acota, la matriz completa
que justifica un solo módulo deja de existir». La bahía es un enrutado
acotado, y la contradicción se resuelve **derogando el principio para el
dominio del patch, no esquivándolo**: la matriz FM es topología
**generadora** — la identidad del instrumento, sigue sin acotarse — y la
bahía es topología **de frontera**.

Y los 16 puntos internos no son una lista (una lista tiene punto 17): son
una **regla** — *la bahía rutea fronteras de canal, nunca interiores*:

- **Destinos** (entradas): los 16 nodos de suma pre-filtro (§2).
- **Fuentes** (salidas): las 16 salidas post-filtro.

El punto 17 no existe por partida doble: la regla no enumera puntos, y el
régimen programático (§0.1) dice que añadir puntos interiores es
legislación del modelo sobre cobre ya previsto, no cobre nuevo.

### 5.3 Límites declarados, con motivo

1. **La bahía v1 no inyecta en la matriz FM.** Las 16 líneas de la matriz
   son buses siempre conducidos (salidas de op-amp); inyectar exige un
   desconectador por línea. El cobre **reserva la huella** para esa
   expansión sin prometer la función. Es un hueco declarado, no un olvido.
2. **Ley de conmutación**: el crosspoint conmuta bajo la ley de retención
   existente — los cambios de topología aplican **al silencio de nota del
   canal afectado**, espejo de R-M5. Cargar un preset no replomea audio a
   medio acorde.
3. **El camino patcheado ve el bus**: siguen mandando los 1,21 cents y
   todas las reglas de `ground_budget.py`. La bahía no promete el suelo del
   pitch; promete el del patch, que siempre fue otro.

## 6. El parámetro durmiente

El dual del hueco, legislado. La junta lo llamó «escritura muda»: en FM 8×2,
~90 parámetros de canales-moduladora (corte, resonancia, envolvente) se
aceptan y no significan nada — y el modelo tenía doctrina para lecturas
vacías (R-F1: «nunca un valor que parezca una medida») y ninguna para esto.

**Cambio 16 al núcleo**: un parámetro cuyo rol lo silencia **no es nulo —
está durmiente**. Se acepta, se guarda y se aplica (es estado real: editar
un preset en modo FM debe persistir y despertar cuando el rol cambie), y
toda lectura lo devuelve con su **bit de dormancia**, computado del mapa de
roles que R-M6 ya calcula. Consecuencias:

- El agente (carcasa MCP, §0.2) no modula a ciegas: el modelo le dice «esto
  hoy no suena, y despertará cuando el rol cambie».
- La interfaz pinta el parámetro atenuado en todas las carcasas.
- La dormancia es **derivada**, nunca almacenada: no puede desincronizarse
  del rol.

## 7. El re-censo: los números de #164 ya no son los suyos

La lista «esto no cambia de #164» de la primera versión de esta propuesta
era aritméticamente falsa, y la junta lo demostró. Números re-estimados —
`censo_voz.py` los asevera en el plan, **bloqueante**:

| | #164 | Voz total |
|---|---|---|
| Parámetros escribibles | 226 | **~520**: +9/canal (corte, res, A, D, S, R, forma×2, nivel) ×16, + aristas de la bahía, + vínculos del panel de mandos |
| Descriptor | ~18,3 KB de 32 | **~24 KB** + 16 curvas de calibración (~1,6 KB) + umbrales → **la EEPROM pasa a 64 KB** |
| Cotas de `MAX_RESPUESTAS` / lotes | derivadas de 226 | se re-derivan de ~520 |
| Clases de módulo en el descriptor | 1 (poseedor implícito) | **3** (cambio 15) |
| Cambios al núcleo | 14 | **17** |

Los tres cambios nuevos al núcleo, con nombre:

- **Cambio 15**: clases de módulo en el descriptor (poseedor / referente /
  relator), y con ellas el esquema de aristas de la bahía y el de vínculos
  del panel de mandos (la integridad referencial inter-módulo del
  soft-takeover, que el descriptor por-ranura no expresaba).
- **Cambio 16**: el bit de dormancia (§6).
- **Cambio 17**: generadores declarados del módulo — la enmienda a R-M1
  (§3).

## 8. Geometría y placas

Presupuesto ejecutable: `voz_total_budget.py` (**VERDE**, se adopta al repo
como puerta). Datos: `case/clearance_budget.py` (ancho útil 528,32/fila,
reserva 40/fila), #164 §4 (fondo 50,0 disponible), issue #152 (placa v1
114×124).

**Las placas** siguen el patrón de #164 — dos columnas, dos diseños:

- **Placa de voces** (×4): pasa de 4 osciladores a **4 canales completos**.
  La fusión añade ~33 % de área (LM13700 + TL074 + ½ 2164 ×2 + ~50 pasivos
  + 3 canales de DAC por canal, factor de ruteo ×2,2 estimado). Como a lo
  alto no queda nada (124 de 128,5), el crecimiento va a lo ancho: columna
  de 114,3 → **~153 mm**.
- **Placa de panel** (×2): pierde los 32 jacks (bahía, §5) y no gana
  perillas (mandos-sensor, abajo). Queda: LEDs y ventana, sensado muerto.

| | mm |
|---|---|
| Módulo de Voz | 228,6 → **~305** (dos columnas de ~153) |
| Máximo estirable en su fila | 388 — **27 % de holgura**; el ruteo tendría que salir ×4,6 (contra ×2,2 estimado) para agotarla |
| Fila A: Voz 305 + bahía 100 + reserva 40 | **445 de 528** ✓ |
| Fila B: cerebro 150 + mandos 120 + mixer 100 + reserva 40 | **410 de 528** ✓ |
| Fondo: pila sin jacks (frente 5 + panel 1,6 + 2×10,6 + 2×h) | **37,8 de 50** con h=5 — era 45,8; h máx sube de 7,1 a **11,1** |

El primer reparto de filas (Voz+bahía+mixer juntas) salió **ROJO por 17 mm**
y el guion lo registra: el mixer se mudó a la fila del cerebro, que sobraba.

**El panel de mandos** (corte, resonancia, A-D-S-R, nivel, macros) vive en
la fila B con el cerebro, no encima de los filtros: como las perillas son
sensores (architecture-poly §7), separarlas del cobre no cuesta un hilo de
audio — y es lo que libera el frente y el fondo del módulo de Voz. Es la
sección de control única de los polys clásicos. Módulo clase **referente**.

Marcado **ESTIMADO** en el guion (se mide al dibujar): áreas de componente,
factor ×2,2, anchos de bahía/cerebro/mandos, frente de 5 mm.

## 9. Verificación

- **Presupuestos ejecutables nuevos**: `ataque_budget.py` (§3, bloqueante),
  `censo_voz.py` (§7, bloqueante), `cal_filtro_budget.py` (tiempo de
  caracterización de 16 canales — que el arranque no cueste minutos),
  `voz_total_budget.py` (§8, adoptado), consumo re-sumado (~+90 mA/riel
  estimado por filtros y VCAs, contra 650 — holgado, se asevera).
- **Prototipo primero**: se fabrica **UNA placa de voz**, y su bring-up
  completo — afinación, caracterización, y la convivencia del dominio de
  0,58 cents del oscilador con los meneos de audio del filtro en el mismo
  cobre — es **bloqueante** antes de pedir las otras tres.
- Cada arreglo con su mutación corrida (Principio VIII), y el veredicto del
  oído sobre el carácter del MS-20 estabilizado es una puerta (Principio
  IX), no una esperanza.

## 10. Supersesiones y papeles

| Documento | Qué le pasa |
|---|---|
| Spec #164 (dieciséis) | Se mergea tal cual como acta. Este spec sustituye su §3 (partición física), su §4 (geometría y panel) y deroga su decisión 12 para el dominio del patch (§5.2). Todo lo demás sigue vigente |
| Spec orquestación (#164) | Vigente; gana los cambios 15-17 (§7) y la resolución del riesgo 2 (§3). Sus números de censo se re-derivan (§7) |
| `docs/architecture-poly.md` | Se reescribe: 16 canales, dos regímenes de calibración (§4), constitución de §0, y cae su §11.3 («no hay nada que escuche un filtro») |
| `docs/modules/05-vcf.md`, `06-adsr.md`, `07-vca.md` | Se reescriben apuntando aquí; el README de `hardware/05-vcf/` corrige la premisa falsa de calibración |
| Censo del case (#152) | Se actualiza con los anchos de §8 |
| Issue #41 (carcasas de la app) | Gana la carcasa MCP y la web-via-wifi como pares (§0.2) |

**Issues a abrir**: cambios 15, 16 y 17 al núcleo; EEPROM a 64 KB; la
expansión de inyección FM de la bahía (huella reservada); los cuatro
presupuestos nuevos; la reescritura de architecture-poly.

## 11. Lo que NO está confirmado

1. Las áreas y factores de §8 marcados ESTIMADO — se miden al dibujar.
2. El AD75019 en el camino patcheado: distorsión y diafonía reales del
   crosspoint, contra datasheet. Si no da la talla, la bahía pide relés o
   switches discretos y su presupuesto de placa cambia.
3. El tiempo de caracterización de 16 filtros (asentamiento de la
   auto-oscilación por punto de la curva) — `cal_filtro_budget.py`.
4. Los ~520 parámetros del censo son estimación hasta `censo_voz.py`.
5. La convivencia térmica y de ruido del canal completo en una placa: es
   exactamente lo que el prototipo-primero (§9) va a medir.
6. El carácter del MS-20 con la resonancia anclada digitalmente **se decide
   con el oído** en el bring-up. Si el ancla lo mata, el ancla es
   configurable por preset, no obligatoria.
7. **La entrada de CV externo por voz de #164 muere con su panel**, y este
   spec no la repone: la bahía v1 rutea audio a los nodos de suma, no CV a
   los sumadores de tono. Si el caso de uso vuelve (CV de otro modular al
   tono de una voz), es una expansión de la bahía — destinos de clase CV —
   que hay que decidir en revisión, no un olvido.
8. Nada de esto está medido. Son cálculos, datasheets y una junta.
