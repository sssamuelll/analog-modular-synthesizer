# El módulo de Voz total: dieciséis canales completos, y la doctrina que los gobierna

> Diseño validado en sesión con Samuel el 2026-08-23 y pasado **dos veces**
> por la junta: crítica ontológica (Voronov) sobre la propuesta, y sobre el
> spec escrito una segunda pasada triple — clínica (Serrano), de runtime
> (Halberg, verificada contra el firmware que corre) y ontológica segunda
> (Voronov). **Los tres dictámenes están absorbidos con nombre y resolución
> en §12.** Es papel, no cobre.
>
> Este spec REABRE parcialmente el de los dieciséis osciladores
> (`2026-08-22-modulo-3-vco-dieciseis-design.md`, PR #164) y SUSTITUYE la
> arquitectura de módulos 5/6/7 de `docs/architecture-poly.md`. Lo que
> sustituye queda marcado en §10; nada se borra.

---

## 0. La doctrina

La primera versión de esta sección se llamó «acta constitucional» y se
declaró «anterior a cualquier decisión de cobre». La segunda pasada de la
junta demostró que eso era falso — sus definiciones citaban al diseño que
decían fundar (V2-0, §12). Se corrige la pretensión, no el contenido:

> **Esta sección es doctrina destilada del diseño, no su fundamento.** Es el
> retrato honesto de las reglas con las que este diseño se juzga a sí mismo,
> escrita antes de cortar cobre y **enmendable solo por acta**, nunca por
> accidente. Cuando llegue un caso que estas reglas no imaginaron, el caso
> no se resuelve preguntándole al cobre: se resuelve enmendando aquí, en
> voz alta.

### 0.1 La regla de la frontera

> **La modularidad es una sola propiedad con dos regímenes: programática en
> el interior, física en la frontera.**

Por dentro, todo punto de ruteo es reconfigurable a través del modelo — la
matriz de modulación, los selectores, el crosspoint de la bahía, los roles
y la dormancia **son** el patch, y un preset es un patch completo. Por
fuera, la modularidad es cobre y cable.

La frase corta: **por dentro el patch es un preset, por fuera es un cable.**

Dos derogaciones formales de `architecture-poly.md`:

- *«El cable siempre gana»* queda **restringido a los jacks de la bahía**
  (§5), donde sigue intacto: meter un cable rompe el normalizado de esa
  conexión y el sensado de ocupación se lo cuenta al modelo.
- *«En el patch bay vive la modularidad»* se sustituye por la regla de los
  dos regímenes.

Dos normas para disputas futuras:

1. **Toda capacidad de ruteo interior debe ser expresable en el modelo.**
   Incluida la convergencia fija: lo que no es reconfigurable es un
   **normalizado declarado** (§0.4), nunca un accidente.
2. **Todo lo que cruza la frontera debe ser físico.**

### 0.2 Las carcasas: escritores con ley de capas, no «vistas»

La primera versión decía «la interfaz es la vista, no el motor» y en el
mismo párrafo la hacía escribir. La junta lo cazó (V2-VI): una
representación que escribe es un controlador, y cuatro controladores
concurrentes sin árbitro de intención son un conflicto. Se legisla:

**El patch vive y corre en el cerebro y los módulos, siempre.** El
instrumento toca sin computadora. Las carcasas — **app standalone, VST,
MCP (el agente es una carcasa más) y web app vía wifi** — son **editores
concurrentes** del mismo modelo autoritativo, renderizados desde los
descriptores, y cada una sostiene su estado optimista local hasta que el
`CHANGED` del cerebro reconcilia. No hay «un modelo»: hay **un modelo
autoritativo y N vistas optimistas**, y decirlo es lo que evita mentirse.

**La ley de capas, por parámetro y no por modo** — diseñada para el caso de
uso que manda: un directo donde Samuel colabora con su agente en vivo,
el agente automatizando secuencias completas mientras la mano patchea y
tuerce perillas encima:

1. **La mano gana por parámetro.** Un gesto físico (perilla, cable en la
   bahía) captura ese parámetro o ruta: la automatización del agente sobre
   él queda `ANULADO` (el primitivo del núcleo §4.1, extendido: el agente
   es una fuente de automatización más). Todo lo demás sigue bajo el
   agente. `REACTIVAR` lo devuelve. Es touch/latch de DAW, hecho
   instrumento.
2. **El pairing decide quién, no cuándo.** Las carcasas remotas (wifi,
   MCP) requieren emparejamiento explícito. El agente emparejado escribe
   en vivo sin fricción; un cliente no emparejado no escribe nada.
3. **La asimetría del núcleo §2.2 se restaura, acotada a lo
   irreversible**: borrar bancos, escribir calibración, firmware — piden
   confirmación física. Tocar, secuenciar y rutear en vivo, no.

El panel físico es la superficie de **interpretación**: perillas-sensor,
LEDs, bahía. Tocar es físico, editar es programático, y ambos escriben el
mismo modelo — bajo la ley de capas.

### 0.3 Los términos, y la partición de roles

| Término | Definición |
|---|---|
| **Oscilador** | La unidad física de generación: SSI2130 + convertidor exponencial + tap a la matriz |
| **Canal** | La unidad física de replicación: oscilador + filtro + VCA de resonancia + VCA de voz, soldados en la misma placa. El canal **ofrece** roles; no **es** ninguno |
| **Rol** | El estado computado de un canal. **Partición total**: todo canal tiene exactamente un rol en cada instante (tabla abajo) |
| **Módulo** | Una unidad con bajada de J2 que declara un **conjunto** de clases: **poseedor** (posee instancias de parámetro), **referente** (posee vínculos a parámetros ajenos), **relator** (posee aristas). La Voz es poseedora; el panel de mandos, referente; la bahía, relatora; **el mixer es poseedor y su suma 16:1 es normalizado declarado** (§0.4) — la junta cazó que caía entre las clases (V2-V) |
| **Carácter** | Criterio ejecutable: lo que procesa **audio de forma no lineal** → analógico soberano. Lo que genera **control** → del modelo. Lo que aplica **ganancia lineal** → indiferente, decide la ingeniería |

**La partición de roles** — sustituye la definición de Voz de la v1, que
era oscilador-céntrica y dejaba residuos (V2-I, S-6). El cerebro computa
**exactamente un rol por canal**, con esta precedencia descendente cuando
varias condiciones se dan a la vez:

| Rol | Condición | Reparto de notas |
|---|---|---|
| **medición** | El canal está en caracterización (§4) | excluido |
| **moduladora** | Su salida pre-filtro es consumida por la matriz como fuente de al menos un destino | excluido |
| **lfo** | Su oscilador está en modo lento (lo consuma alguien o no — el residuo «lento sin consumidores» de la junta cae aquí) | excluido |
| **conducto** | Su oscilador está silenciado y hay señal externa activa en su nodo de suma: suena **lo externo** por su filtro y su VCA. El caso DJ: mandar una voz a un pedal y devolverla por el canal de otro | excluido — el cerebro **no asigna notas a un oscilador silenciado** (V2-I caso 2) |
| **voz** | Su oscilador suena hacia su nodo de suma y su VCA de voz es asignable | **elegible** |
| **mudo** | Nada de lo anterior | excluido |

Esto **enmienda R-M6** de la orquestación (era una condición doble; ahora
es esta partición) — anotado como parte del cambio 16 (§7). La dormancia
(§6) se deriva de esta partición.

### 0.4 El normalizado declarado

Lo no-reconfigurable es decisión escrita, no accidente. El normalizado
declarado del instrumento es:

1. **La cadena de canal**: oscilador → nodo de suma → filtro → VCA de voz,
   soldada, con **dos** puntos tocables por la bahía: el nodo de suma
   (entrada) y la salida **post-VCA** (salida — cambiado desde post-filtro,
   V2-II: la bahía exporta **la voz articulada**, no una señal cruda
   siempre viva que contradiga el silencio).
2. **La convergencia**: las dieciséis salidas post-VCA suman al bus del
   mixer, 16:1, fija (V2-V).
3. **El tap de la matriz FM**: pre-filtro, fijo (§2).
4. **El tap de caracterización**: post-filtro, interno, hacia el mux de
   medida (§4) — instrumentación, no audio.

Por qué dos puntos de bahía y no más, dicho sin bucle (V2-II): el nodo de
suma es el único punto donde lo externo puede **sumarse** sin romper la
semántica D9, y la salida post-VCA es el único punto donde el canal ya es
una voz articulada. Cualquier punto intermedio exportaría un objeto que el
modelo no puede nombrar. Si un día hace falta el tercero, es enmienda de
§0, no cobre furtivo.

---

## 1. Qué es el módulo de Voz

El módulo 3 deja de ser «el VCO» y pasa a ser **la Voz**: dieciséis
canales completos, cada uno oscilador → filtro → VCA, soldado de punta a
punta en la misma placa. Los módulos 5 (VCF) y 7 (VCA) **desaparecen como
hardware separado**. El módulo 6 (ADSR) desaparece como circuito y se
ejecuta **en los micros de este módulo** (§3), con sus perillas en el
panel de mandos (§8).

El módulo suelda canales; el preset computa roles (§0.3). En FM 8×2 hay
16 canales, 8 voces y 8 moduladoras con sus filtros durmientes (§6) — no
ociosos por error.

**De #164 se conserva**: los dieciséis SSI2130 y sus tres correcciones de
exactitud, la matriz de modulación analógica de 16 líneas y la digital de
sync, la partición en dos columnas con dos micros RP2350B, la referencia
única distribuida y bufferizada, el convertidor de tono pegado a cada
oscilador, los juguetes, la telemetría y el J2.

**De #164 se reabre**: la partición física de placas (§8), el panel de 32
jacks (muere: §5), el **camino de silencio** (S-1: ya no basta el pull del
oscilador — hay 32 VCAs nuevos; su estado seguro se rediseña en §9), y el
censo de parámetros y memoria (§7). #164 se mergea tal cual — es el acta
de su junta — y este spec declara la supersesión.

## 2. El canal analógico

```
            nodo de suma                                    bus del mixer
SSI2130 ──────►(+)──► filtro MS-20 ──┬──► VCA de voz ──►──── (16:1, fijo)
   │            ▲     LM13700+TL074  │    (¼ SSI2164)
   │            │     LP 24 dB/oct   │        ▲
   │      bahía IN     LEDs, res.    │        │ CV envolvente
   │      (externo,    por VCA       │        │ (generador local, §3)
   │       se suma)    (¼ SSI2164)   │        └──► bahía OUT (post-VCA)
   │                                 │
   │                                 └──► tap de caracterización ──► mux
   │                                      16:1 ──► Schmitt ──► contador
   └──► matriz de modulación FM (16 líneas), SIN filtrar        del micro
```

- **El tap de la matriz sale ANTES del filtro**: la moduladora de FM es la
  señal cruda; filtrarla acoplaría el índice de modulación al corte.
- **El filtro es el MS-20 de la tesis** — LM13700 en dos celdas, LP
  24 dB/oct, LEDs en el lazo — elegido por carácter (§0.3) y estabilizado
  digitalmente (§4). **LP solo.**
- **La resonancia se controla por VCA** (¼ SSI2164 en el lazo), nunca
  digipot.
- **El VCA de voz es ¼ de SSI2164**. 16 + 16 = 32 VCAs = **8× SSI2164**.
- **El tap de caracterización** (S-3, era el BLOCKER 3): la señal
  post-filtro de cada canal, pre-VCA, va a un **mux analógico 16:1 → un
  Schmitt → un contador del micro**. Es la ruta física por la que la
  auto-oscilación llega al conteo recíproco con el VCA de voz cerrado.
  Instrumentación, no audio: no toca el camino de voz.
- **El CV de corte tiene un solo escritor: el micro del módulo** (S-9).
  Todas las fuentes — valor base + curva de calibración + envolvente de
  filtro local + modulación que mande el cerebro por la trama — **se suman
  digitalmente en el micro**, que escribe el DAC. No hay nodo analógico de
  suma de CV que arbitrar.
- **CVs nuevos por canal: 3** — corte, resonancia, envolvente de VCA.
  Velocity y escalados son multiplicaciones en el micro.

## 3. Ejecución: generadores, eventos y la ley que los limita

### 3.1 Las envolventes son generadores del módulo

El cerebro manda el evento de nota y los parámetros; **el micro del módulo
renderiza la curva localmente** contra los DACs por su SPI privado. La
*forma* del ataque no depende de la trama.

**Tasa de render: 10 kHz por canal, con RC de reconstrucción en la salida
del DAC** — no «decenas de kHz» (H-BP1): 8 envolventes × 10 kHz son 80k
escrituras/s por micro, y esa cifra entra en un presupuesto, no en un acto
de fe. **`spi_privado_budget.py` es bloqueante e INVALIDANTE**: suma todos
los flujos del SPI privado (tono 1 kHz, índices, envolventes, eventos) y
si no cierra, esta sección cae — no «se ajusta en el plan».

### 3.2 El test de membresía de «generador» (cambio 17, con cerradura)

La junta cazó que la categoría no tenía límite (V2-IV). Lo tiene:

Un generador es un proceso del módulo que **(a)** se dispara por un evento
de la trama, **(b)** entre eventos solo consume parámetros constantes —
nunca un flujo de valores del cerebro (eso sería interpolar, y R-M1 sigue
prohibiéndolo), y **(c)** su dominio declarado excluye el tono: **R-M2
prevalece con cita cruzada** — el tono lo genera solo el cerebro. Un
«generador de glide» viola (b). Un «generador de pitch-blip» viola (c).

**La envolvente de tono queda prohibida en v1, en voz alta.** La FM
percusiva no queda huérfana: el cerebro ya puede secuenciar tono a 1 kHz
bajo R-M2 — el agente hace pitch-automation hoy. El generador local de
tono es una **enmienda futura declarada**: tocaría R-M2, el autotune (que
corregiría lo que otro mueve) y este test. Huella anotada, no prometida.

Los parámetros de un generador se capturan **al evento**: la próxima nota
usa los valores nuevos; el sustain aplica en vivo (S-12).

### 3.3 El evento de nota: diseño pendiente, dicho sin maquillaje

La v1 de este spec declaró «resuelto» el riesgo 2 de la orquestación. Era
falso (S-2, era el BLOCKER 2): el formato del mensaje, su sello de tiempo
y la entrega al esclavo **no están diseñados**. Este spec no los diseña —
los declara **prerrequisito bloqueante**, a diseñar junto a los riesgos 1
y 2 de la orquestación, con estas cotas como criterio de aceptación:

- Peor caso nota-a-VCA **incluyendo la etapa maestro→esclavo** (S-5,
  H-BP2: la cuenta de 2 ms de la v1 la omitía, y el jitter
  maestro-vs-esclavo es sistemático y asimétrico): objetivo ≤ 3 ms,
  uniforme entre columnas dentro de ±0,5 ms.
- `ataque_budget.py` asevera el camino completo **cuando el mensaje
  exista**, no antes.

### 3.4 El reparto del micro, declarado

El micro del módulo es tiempo real duro por tres frentes (esclavo J2,
render de envolventes, PIO de afinación) y la v1 no asignaba nada
(H-CF1). Se declara el reparto — el plan lo detalla, este spec lo fija:

- **Núcleo 0**: esclavo J2 + eventos + telemetría (latencia manda).
- **Núcleo 1**: render de envolventes + escritura DAC + drenaje de PIO
  (caudal manda).
- Prioridades NVIC y canales DMA: documento del plan, **bloqueante**, con
  la regla de que el esclavo J2 nunca pierde su ventana de MISO.

## 4. Calibración: dos regímenes, y su ley de concurrencia

**Afinación** (osciladores): permanente, paralela, pre-filtro, invisible.
Intacta de #164.

**Caracterización** (filtros): bajo demanda, muxeada (§2), en silencio
(VCA de voz cerrado), por el tap post-filtro → Schmitt → contador. Tres
lazos: curva corte-vs-CV por canal → EEPROM; compensación térmica por el
sensor común (que ve la misma temperatura que el expo del oscilador —
ganancia de la fusión); ancla de resonancia en el umbral de
auto-oscilación. La premisa del README del VCF («no hay nada que escuche
un filtro») era falsa para este filtro: auto-oscila por diseño.

**La ley de concurrencia** (H-CF3, era indefinido):

- Un canal en caracterización tiene rol **medición** (§0.3): el cerebro
  **no le asigna notas**. No hay carrera nota-contra-medida: la partición
  la excluye por construcción.
- La caracterización **nunca se dispara por un recall**: corre a demanda
  explícita o como mantenimiento en silencios, canal a canal, robando como
  máximo un canal a la vez al reparto.
- **`cal_filtro_budget.py` es bloqueante**: asentamiento de la
  auto-oscilación × puntos de curva × 16 canales, con la aserción de que
  el mantenimiento por canal cabe en un silencio musical razonable y el
  barrido completo se reserva a la primera calibración.

La tesis, escrita: **se conserva el filtro por lo inmedible (el carácter)
y se estabiliza midiendo todo lo demás.** La dispersión del carácter entre
canales no se calibra: es lo que siempre se llamó encanto.

## 5. La bahía asignable

### 5.1 Qué es

**8 entradas + 8 salidas** en jacks Thonkiconn (TN conectado, sensado de
ocupación, LED por jack), ruteadas por **dos AD75019** (crosspoint 16×16,
±12 V, carga serie): entradas → los 16 nodos de suma; las 16 salidas
post-VCA → salidas. El jack es un nombre que le da el preset; su LED dice
en color qué es. El recall del patch interior se recuerda solo; solo los
cables hacia el mundo siguen siendo físicos.

Módulo clase **relator**, con su bajada de J2 y su panel en la fila A.

### 5.2 La derogación del anti-acotamiento, en voz alta

#164 (decisión 12) legisló: «si el enrutado se acota, la matriz que
justifica un solo módulo deja de existir». Se deroga **para el dominio del
patch**: la matriz FM es topología **generadora** — identidad del
instrumento, sigue sin acotarse — y la bahía es topología **de frontera**,
gobernada por §0.4 (los dos puntos, con su porqué sin bucle).

### 5.3 La ley de conmutación, contra el chip real

La v1 legisló «conmutar al silencio del canal afectado» sobre un chip de
**commit global** (H-CF2: el AD75019 carga 256 bits y aplica todo a la
vez). Se rediseña:

- **Imagen sombra** (decisión de Samuel): el cerebro mantiene la imagen
  completa de los 256 bits; conmutar es recargar la imagen entera y
  latchear. **Supuesto marcado**: los cruces que no cambian no glitchean
  en el latch — se verifica contra datasheet y en bring-up **con su
  mutación** (un cruce sonando, recarga de otro, se mide el primero). Si
  el supuesto cae, la bahía pasa a switches direccionables y §8 se rehace.
- **Barrera de cambiados-en-silencio**: el commit espera a que **todos los
  canales cuyos cruces cambian** estén en silencio. Los que no cambian no
  votan.
- **Política de drones, configurable por preset** (decisión de Samuel):
  `diferir` (espera al silencio; la interfaz y el LED del jack muestran
  «pendiente») o `forzar` (timeout declarado y mute breve del canal). Un
  drone bajo `diferir` nunca se corta solo (H-OF3: la starvation deja de
  ser un bug y pasa a ser una elección del intérprete, visible).
- **El commit no viaja por la máquina de retención** (H-RC1: el buzón de 4
  ranuras y TTL 30 s no puede ser cerrojo de topología): la conmutación
  pendiente es **estado propio del relator** («ruta activa» / «ruta
  pendiente»), visible en el descriptor, sin TTL — coherente con
  `diferir` indefinido.

### 5.4 Estado seguro y fondo

- **Arranque** (H-OF4): el AD75019 despierta con el registro aleatorio y
  sin reset a abierto. El driver del latch arranca **inhibido por
  hardware** (pull) hasta que el micro shiftea ceros: la bahía nace
  desconectada, con la misma doctrina del §9 de #164.
- **Fondo presupuestado** (S-13): la bahía hereda la fila que la v1 le
  quitó al módulo de Voz — jack 13,0 + placa 1,6 + AD75019 y orilla — pila
  propia ≤ 50, en `voz_total_budget.py` ampliado.

## 6. El parámetro durmiente

Un parámetro cuyo rol lo silencia **no es nulo — está durmiente**: se
acepta, se guarda, se aplica, y toda lectura lo devuelve con su bit de
dormancia, **derivado de la partición de roles (§0.3), nunca almacenado**.

**La dormancia se computa en el cerebro, para todos los módulos** (V2-III:
la v1 la computaba «donde R-M6 vive» y las aristas de la bahía — que tocan
canales de *otro* módulo — resucitaban la escritura muda un piso más
arriba). El cerebro es el único que tiene todos los mapas: deriva la
dormancia de los parámetros del poseedor **y de las aristas del relator**
(una arista hacia el nodo de suma de un canal durmiente está durmiente), y
la publica en los descriptores. El descriptor del relator declara de qué
roles dependen sus aristas. **Cambio 16** (§7), que incluye la enmienda de
R-M6 a la partición.

Consecuencias: el agente no modula a ciegas; las carcasas pintan atenuado;
la coherencia dormancia↔rol no puede desincronizarse porque no existe dos
veces. Y la serialización que faltaba (H-CI1): **el recompute de roles,
dormancia y reparto es una barrera única al final de la aplicación de un
preset** — no muta mientras el lote está en vuelo.

## 7. El re-censo y los cambios al núcleo

`censo_voz.py` asevera; **bloqueante**. Estimaciones:

| | #164 | Voz total |
|---|---|---|
| Parámetros escribibles | 226 | **~520** (+9/canal ×16, + aristas, + vínculos) |
| Descriptor | ~18,3 KB de 32 | **~24 KB** + curvas (~1,6 KB) → **EEPROM 64 KB** |
| Clases de módulo | 1 implícita | conjunto de clases (cambio 15) |
| Cambios al núcleo | 14 | **18** |

Los cambios nuevos, y los viejos que ascienden a prerrequisito:

- **Cambio 15**: clases de módulo como conjunto + esquema de aristas y de
  vínculos (la integridad referencial del panel de mandos).
- **Cambio 16**: dormancia derivada en el cerebro, incluidas aristas +
  enmienda de R-M6 a la partición de roles (§0.3).
- **Cambio 17**: generadores con test de membresía (§3.2).
- **Cambio 18**: el largo del descriptor pasa de u8 a u16 (H-CI2:
  `descubrimiento.rs:87` lee el largo como u8, techo 255 B — la identidad
  del módulo literalmente no cabe hasta este cambio).
- **Los cambios 2 (ranuras lógicas) y 12 (lotes) ascienden a
  PRERREQUISITO BLOQUEANTE** (H-RC2/RC3, verificado en cobre:
  `MAX_INSTANCIAS = 16` está consumido y `MAX_RESPUESTAS = 4` contra ~520
  `CHANGED` es un desbordamiento de 130×). Hasta que aterricen, **el
  modelo de la Voz total no es direccionable** — este spec lo dice en vez
  de fingir que las carcasas ya renderizan lo que el firmware no publica.
- **El cerrojo de retención se rediseña dentro del cambio 12** (H-RC1): la
  carga de preset es un lote con barrera final (§6), no una ocupación del
  buzón de 4 ranuras.

## 8. Geometría, consumo y reparto físico

`voz_total_budget.py` (**VERDE**, se adopta como puerta; se amplía con el
fondo de la bahía, §5.4). Sin cambios sobre la v1:

| | mm |
|---|---|
| Módulo de Voz | 228,6 → **~305** (dos columnas de ~153; máx. 388, 27 % de holgura; el ruteo tendría que salir ×4,6 contra ×2,2 estimado) |
| Fila A: Voz 305 + bahía 100 + reserva 40 | **445 de 528** ✓ |
| Fila B: cerebro 150 + mandos 120 + mixer 100 + reserva 40 | **410 de 528** ✓ |
| Fondo Voz: 5 + 1,6 + 2×10,6 + 2×h | **37,8 de 50** (h ≤ 11,1) |

El primer reparto salió ROJO por 17 mm y el guion lo registra.

**El consumo se re-suma entero, no en delta** (S-8: la v1 comparaba +90 mA
contra los 650 totales como si fueran holgura libre). `consumo_total.py`,
**bloqueante**, suma el instrumento completo por riel: módulo de Voz (16
SSI2130 + 16 LM13700 + 16 TL074 + 8 SSI2164 + DACs), cerebro, mixer,
bahía, LEDs — contra los 650 mA/riel del módulo 1. Estimación de diseño:
~350–420 mA/riel; **si no cierra con un 30 % de margen, se renegocia
antes del cobre**.

**El panel de mandos** vive en la fila B (perillas-sensor: separarlas del
cobre no cuesta un hilo de audio). Módulo clase referente; la semántica
del vínculo es del cambio 15, y la de edición en vivo, de §3.2.

**El arranque se presupuesta** (S-14): `arranque_budget.py` — descriptor
de ~24 KB + curvas por I²C, con el cambio 18 puesto, contra un objetivo de
instrumento listo en < 3 s sin caracterización.

## 9. Silencio, fallos y verificación

### 9.1 El camino de silencio, rehecho para 32 VCAs (S-1, era el BLOCKER 1)

El de #164 protegía osciladores; ahora hay 32 VCAs gobernados por DAC.
Estado de reposo **garantizado por hardware, antes de que corra
firmware**:

- Los DACs de envolvente y resonancia arrancan a **cero-escala por
  RSTSEL** (supuesto contra datasheet AD5686R, **se verifica y se muta en
  bring-up**), y cero = VCA cerrado, resonancia sin auto-oscilar.
- Pull-downs analógicos en los CV de VCA durante reset, para la ventana
  anterior al power-on-reset del DAC.
- Criterio: **encender el instrumento con cables puestos no suena** — ni
  voces ni aullidos de dieciséis filtros. Mutación: arrancar sin firmware
  y medir el bus.

### 9.2 Watchdogs: los failsafes que el ADSR físico se llevó (H-OF1/OF2)

El gate con pull-down era el failsafe y la v1 lo borró sin sustituto:

- **Watchdog de trama en el módulo**: sin trama válida en N ms (N del
  plan, ~50), todos los generadores van a **release** y el módulo afirma
  silencio localmente. Trama perdida ≠ sustain infinito.
- **Heartbeat del esclavo dentro del SPI privado**: el maestro lo vigila;
  esclavo muerto → `RESET_ESCLAVO` (los DACs vuelven a cero-escala, §9.1).
- **El esclavo vigila al maestro**: SPI privado mudo en N ms → release
  local. Maestro muerto ≠ ocho voces congeladas sonando.
- Mutaciones: matar cada micro a mitad de nota y medir que el silencio
  llega solo.

### 9.3 El prototipo, con su alcance dicho (S-11)

Se fabrica **una placa de voces, la maestra (con micro)**. Su bring-up
valida: afinación, caracterización, generadores, watchdog de trama,
convivencia térmica y de ruido del canal completo. **Declarado fuera de su
alcance**: maestro↔esclavo, bus de matriz inter-columna, bahía. Esas
tienen su **segunda puerta**: dos placas + handshake antes de la tanda.

### 9.4 Los presupuestos, todos, con su carácter

| Script | Qué asevera | Carácter |
|---|---|---|
| `voz_total_budget.py` | geometría + fondo bahía | adoptado, VERDE |
| `spi_privado_budget.py` | caudal del SPI con todos los flujos | **bloqueante e invalidante de §3** |
| `ataque_budget.py` | nota-a-VCA completo, ambas columnas | bloqueante, tras §3.3 |
| `censo_voz.py` | parámetros, memoria, cotas | bloqueante |
| `cal_filtro_budget.py` | tiempos de caracterización | bloqueante |
| `consumo_total.py` | instrumento entero por riel | bloqueante |
| `arranque_budget.py` | descriptor + curvas por I²C | bloqueante |

Y las dos leyes de siempre: cada arreglo con su mutación (Principio VIII),
y el carácter del MS-20 estabilizado se decide con el oído (Principio IX).

## 10. Supersesiones y papeles

| Documento | Qué le pasa |
|---|---|
| Spec #164 (dieciséis) | Se mergea como acta. Este spec sustituye su §3, §4, panel y camino de silencio (§9.1), y deroga su decisión 12 para el dominio del patch |
| Spec orquestación | Vigente; gana los cambios 15-18, la enmienda de R-M6, el test de generadores, y sus riesgos 1-2 pasan a prerrequisito de §3.3 |
| Núcleo digital | Su §2.2 (asimetría del agente) se **restaura acotada** (§0.2); `ANULADO`/`REACTIVAR` se extiende al agente como fuente |
| `docs/architecture-poly.md` | Se reescribe: 16 canales, partición de roles, dos regímenes de calibración, ley de capas; cae su §11.3 |
| `docs/modules/05/06/07`, README del VCF | Se reescriben apuntando aquí |
| Censo del case (#152) | Anchos nuevos de §8 |
| Issue #41 | Gana MCP y web-wifi como carcasas pares, bajo la ley de capas |

**Issues a abrir**: cambios 15-18; ascenso de 2 y 12 a prerrequisito;
EEPROM 64 KB; los siete presupuestos; verificación del latch del AD75019;
RSTSEL del AD5686R; la enmienda futura del generador de tono; reescritura
de architecture-poly.

## 11. Lo que NO está confirmado

1. Áreas y factores de §8 marcados ESTIMADO — se miden al dibujar.
2. **El latch del AD75019 no glitchea cruces que no cambian** — supuesto
   que sostiene §5.3; contra datasheet y bring-up, con mutación. Si cae:
   switches direccionables y §8 se rehace.
3. **RSTSEL del AD5686R arranca a cero-escala** — sostiene §9.1; contra
   datasheet y bring-up.
4. Distorsión y diafonía reales del AD75019 en el camino patcheado.
5. Asentamiento de la auto-oscilación por punto de curva
   (`cal_filtro_budget.py`).
6. Los ~520 parámetros y los ~24 KB son estimación hasta `censo_voz.py`.
7. El caudal del SPI privado a 10 kHz de render (`spi_privado_budget.py`).
8. La convivencia térmica y de ruido del canal completo en una placa — el
   prototipo §9.3.
9. El carácter del MS-20 con la resonancia anclada se decide con el oído;
   si el ancla lo mata, es configurable por preset.
10. **La entrada de CV externo por voz de #164 muere con su panel** y este
    spec no la repone: la bahía rutea audio. Si el caso vuelve, es
    expansión declarada (destinos de clase CV), no un olvido.
11. Nada de esto está medido. Son cálculos, datasheets y tres juntas.

## 12. El registro de las juntas

Cada hallazgo, con su resolución o su confesión. S = Serrano (clínico),
H = Halberg (runtime, verificado contra firmware), V2 = Voronov segunda
pasada (ontológico). El primer dictamen de Voronov está absorbido desde la
v1 y re-auditado por V2.

| Hallazgo | Qué era | Resolución |
|---|---|---|
| S-1 / BLOCKER | 32 VCAs sin estado de arranque; 16 filtros pueden aullar sin firmware | §9.1: cero-escala por RSTSEL + pulls + mutación de encendido |
| S-2 / BLOCKER, H-BP2 | «Evento de nota resuelto» era falso; maestro→esclavo fuera de la cuenta | §3.3: prerrequisito bloqueante con cotas de aceptación, sin maquillaje |
| S-3 / BLOCKER | La auto-oscilación no tenía ruta física al contador | §2: tap post-filtro → mux 16:1 → Schmitt → contador |
| S-4, H-BP1 | Caudal SPI de envolventes sin presupuestar; «decenas de kHz» de fe | §3.1: 10 kHz + RC; `spi_privado_budget.py` invalidante |
| S-5 | Ataque prometido uniforme sin contar la columna del esclavo | §3.3: cota de uniformidad ±0,5 ms entre columnas |
| S-6, V2-I | «Voz» divergía de R-M6 y el espacio de roles no particionaba | §0.3: partición total con precedencia; enmienda R-M6 (cambio 16) |
| S-7, V2-VI | Carcasas remotas sin autoridad; §2.2 del núcleo borrado | §0.2: ley de capas + pairing + §2.2 restaurado acotado |
| S-8 | Consumo en delta contra el total | §8: `consumo_total.py` bloqueante |
| S-9 | CV de corte con fuentes sin árbitro | §2: el micro es el único escritor; suma digital |
| S-10, H-CF2, H-OF3 | Ley de conmutación imposible en el chip; drones = starvation | §5.3: imagen sombra + barrera de cambiados + política por preset |
| S-11 | Prototipo único sobre-prometía | §9.3: alcance declarado + segunda puerta |
| S-12 | Vínculo perilla→parámetro y edición en vivo ambiguos | §3.2 (captura al evento) + cambio 15 |
| S-13 | Fondo de la bahía sin presupuestar | §5.4 |
| S-14, H-CI2 | Arranque del descriptor sin presupuesto; largo u8 (255 B) | §8: `arranque_budget.py`; cambio 18 |
| H-RC1 | La retención (4 ranuras, TTL 30 s) usada como cerrojo de topología | §5.3 y §7: estado del relator + lote con barrera, no buzón |
| H-RC2/RC3 | `MAX_RESPUESTAS=4` vs ~520; `MAX_INSTANCIAS=16` consumido | §7: cambios 2 y 12 ascienden a prerrequisito; el modelo no es direccionable hasta entonces, dicho |
| H-CF1 | Prioridades/núcleos del micro sin asignar | §3.4: reparto por núcleos declarado; NVIC/DMA bloqueante en plan |
| H-CF3 | Note-on durante caracterización indefinido | §4: rol medición excluido del reparto; cal nunca por recall |
| H-CI1 | Roles/dormancia mutando con el lote en vuelo | §6: barrera única al final del preset |
| H-OF1/OF2 | Esclavo muerto = notas pegadas; trama perdida = sustain infinito | §9.2: watchdog de trama + heartbeat bidireccional + mutaciones |
| H-OF4 | Crosspoint aleatorio al arrancar | §5.4: driver inhibido por hardware hasta shiftear ceros |
| V2-0 | El acta era un autorretrato que se decía anterior | §0: se declara doctrina destilada, enmendable por acta |
| V2-I | Canal sonando por bahía contaba como voz; lento-sin-consumidores sin rol | §0.3: roles conducto y lfo; partición total |
| V2-II | «Frontera» era una lista con abrigo; fuente post-filtro exportaba señal sin envolvente | §0.4: cardinalidad fundada sin bucle; fuente movida a post-VCA |
| V2-III | La dormancia moría en la frontera del relator | §6: computada en el cerebro para todos los módulos |
| V2-IV | «Generador» sin test; pitch-env legal e ilegal a la vez | §3.2: test (a)(b)(c); pitch prohibido v1 con huella de enmienda |
| V2-V | El mixer rompía la taxonomía que lo ejemplificaba | §0.3/§0.4: conjunto de clases + la suma 16:1 como normalizado |
| V2-VI | «Vista que escribe»; N+1 modelos negados | §0.2: editores concurrentes + modelo autoritativo y vistas optimistas |

---

## 13. Acta del 2026-08-23: seis decisiones tomadas después de la junta

§0 dice que la doctrina se enmienda **por acta y en voz alta, nunca por
accidente**. Estas seis se tomaron en sesión con Samuel el mismo día, después
de cerrar la v2, y cambian cosas que el cuerpo de este spec da por sentadas. Se
registran aquí en vez de reescribirlo, para que el rastro de las tres juntas
quede intacto.

### E-1. El cerebro y las voces NO se funden

Se evaluó fusionar la placa del cerebro con la de voces y se descarta, con tres
razones que ya estaban en el repo y ninguna es de opinión:

- **Pines.** El cerebro deja 2 GPIO libres de 48 tras la pantalla de 2,8"
  (spec del cerebro §12.16). El maestro de la Voz ya gasta ocho en cronómetros
  de PIO. Fusionar no ahorra un chip: deja tres chips en una placa más grande.
- **Reloj.** `autotune_budget.py` fija `F_PIO = 150 MHz` y Pico-PIO-USB impone
  el suyo (#150, abierto). Fusionados, el host USB le dicta la base de tiempo
  al afinado de los dieciséis osciladores.
- **Masa.** El spec del cerebro corta **ahí** el lazo con la masa de la
  computadora. Esta placa es donde **1 mV son 3,6 cents**. La puerta sucia no
  vive en el cuarto limpio.

**Nada de este spec cambia por E-1.** Se registra para que no se vuelva a
proponer sin estos tres números delante.

### E-2. El frente se unifica; los conectores del mundo se van atrás

Una cara continua por fila, tarjetas separadas detrás, y USB / MIDI DIN /
clock / pedal a la trasera del cajón. Lo habilita el mismo argumento que este
spec ya usa para el panel de mandos (§8): **las perillas son sensores, mandan
números, y los números viajan por cable plano sin ensuciarse.** Detalle,
consecuencias y lo que hay que tocar del cajón: **#167**.

### E-3. La fila de arriba es UN módulo

La bahía deja de ser módulo aparte — **deroga §5.1** en «con su bajada de J2 y
su panel en la fila A». Se funde en el de Voz, que pasa a declarar también la
clase **relator**. Legal sin inventar nada: el cambio 15 hizo que un módulo
declare un *conjunto* de clases, y esta es su primera consecuencia real.

Gana una sola bajada de J2 en vez de dos, una sola identidad y una ranura
libre. Queda por resolver: **quién shiftea los 256 bits del AD75019** ahora que
la bahía no tiene bajada propia. Barato en pines, pero los micros de este
módulo son justo los apretados.

### E-4. Los demás módulos SÍ son modulares, y la fila de abajo es rack de verdad

La regla de los dos regímenes (§0.1) se mantiene y ahora tiene frontera física
declarada: **arriba el instrumento, abajo módulos Eurorack intercambiables** —
un mixer de utilidad, un delay analógico, lo que Samuel quiera llevarse a otro
instrumento. La bahía (§5) es el puente, y ya está en el jack correcto
(Thonkiconn, ±12 V).

Dos cosas que esto exige y hoy no existen:

- **Bus board en la fila de abajo**, con el peine de 16 pines estándar. No está
  en ningún plano.
- **Reserva de invitados por riel.** `consumo_total.py` (§9.4) deja de sumar
  «el instrumento» y pasa a sumar el instrumento **más una reserva declarada**.
  Con los 650 mA/riel del módulo 1 y los 350–420 estimados del instrumento, la
  reserva sale del orden de 230–300 mA — que es una cifra que hay que escribir,
  no una holgura que se descubre enchufando el cuarto módulo.

### E-5. El módulo 4 desaparece como hardware separado

El módulo de Voz se basta solo: es un sintetizador completo, no un banco de
osciladores. Se mudan a esta placa la suma de los dieciséis, el volumen
general, la salida principal **y los oídos** — el códec de 24 bits que hoy vive
en el módulo 4 y que es como el cerebro se escucha a sí mismo.

**Deroga §0.4 punto 2.** La convergencia 16:1 sigue siendo normalizado
declarado, pero ya no «suma al bus del mixer»: **termina en la salida de este
módulo**. El mixer que viva en la fila de abajo es un invitado cualquiera y no
tiene relación con esta suma.

El motivo, dicho por Samuel: *un mixer solo tiene sentido si es independiente
de su fuente y de sus salidas.* El de hoy estaba soldado a las voces, así que
no era un módulo — era una parte.

### E-6. La salida es ESTÉREO, con sitio por voz

Decidido: el instrumento reparte sus voces en el campo estéreo. Es la mitad de
por qué un poli suena grande, y decidirlo después del layout cuesta el layout.

**El cómo NO se decide aquí**, porque son dos caminos y los dos mueven
presupuestos (cuentas derivadas de §2 — ¼ SSI2164 por VCA, 3 CV por canal — no
medidas):

| | VCAs de voz | CV por canal | Tráfico del SPI privado |
|---|---|---|---|
| **A**: dos VCAs por canal (L/R), cada rama con envolvente × paneo | 32 | 4 | **×2** — las dos ramas se escriben a 10 kHz |
| **B**: un VCA de envolvente + etapa de paneo detrás | 48 | 5 | **igual que hoy** — el paneo solo cambia al evento de nota |

A es menos cobre y más caudal; B es más cobre y deja el caudal intacto. Y el
caudal es justo lo que `spi_privado_budget.py` puede invalidar (§9.4). Se
resuelve en el pase de diseño, con los dos presupuestos corridos, no aquí.

**Lo que E-6 reabre, sin excepción:**

- `spi_privado_budget.py` — invalidante, y ahora con dos topologías que medir.
- `consumo_total.py` — más VCAs y más DACs por riel, y encima la reserva de
  invitados de E-4.
- `voz_total_budget.py` — hoy VERDE con 27 % de holgura y un factor de ruteo
  **estimado**; con entre 8 y 16 chips más de VCA y DAC, esa holgura hay que
  volver a ganársela.
- `censo_voz.py` — los CV por canal pasan de 3 a 4 o 5, y los ~520 parámetros
  crecen con el paneo por canal.
- **§9.1, el camino de silencio** — ya no son 32 VCAs en estado seguro, son 48
  o 64 según el camino. El criterio «encender el instrumento con cables puestos
  no suena» no se ablanda por eso.

### Lo que este acta NO decide

La topología de paneo (E-6), el reparto de anchos de panel con los conectores
ya mudados, quién shiftea el crosspoint (E-3), y nada del cajón. Cada uno va en
su propio pase. La idea de que la fila de abajo fuera también un módulo único
**muere aquí**, con E-4.
