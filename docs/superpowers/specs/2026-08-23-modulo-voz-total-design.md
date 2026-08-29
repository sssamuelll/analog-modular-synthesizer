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

> ## ⚠️ Enmienda del 2026-08-26: **el micro de este módulo cambió**
>
> **Los dos RP2350B mueren. El N657 hereda el módulo entero.** Lo selló el
> benchmark del motor digital (`2026-08-26-motor-digital-benchmark.md`) y lo
> desarrolla `2026-08-26-motor-digital-design.md`. Este bloque aplica las
> **cinco filas** que ese papel mandó sobre este (su §9), y que llevaban un
> día escritas sin ejecutar.
>
> Léelo antes que nada de abajo: **cinco secciones de este spec están
> enmendadas o sucedidas**, y cada una lleva su marca en su sitio.
>
> | Sección | Qué le pasa | Sucesor |
> |---|---|---|
> | **§1** | muere «la partición en dos columnas con dos micros RP2350B» | motor-digital §1 |
> | **§3.1** | la tasa única de 10 kHz gana una **ley de dos tasas** | motor-digital §5 (acta A-4) |
> | **§3.3** | sus cotas pierden la etapa maestro→esclavo, que ya no existe | motor-digital §7 |
> | **§3.4** | **sucedida entera**: no hay dos núcleos que repartir | motor-digital §7 |
> | **§5** | la bahía gana **fuente nueva** (la boca) y **destino nuevo** (los oídos) | motor-digital D-P1/D-P4 |
> | **§9.2** | el camino de silencio deja de depender del software | motor-digital R-M5 |
>
> **Lo que NO toca esta enmienda, y conviene decirlo:** la cadena analógica
> del canal (§2) queda intacta — el motor-digital la declara expresamente
> fuera de lo que reabre. La doctrina de §0, la bahía como concepto, el
> parámetro durmiente y las siete actas E siguen en pie. **Cambió quién
> ejecuta, no qué instrumento es.**

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
sync, ~~la partición en dos columnas con dos micros RP2350B~~ **(muere —
enmienda del 2026-08-26)**, la referencia única distribuida y bufferizada, el
convertidor de tono pegado a cada oscilador, los juguetes, la telemetría y el
J2.

> **Enmienda del 2026-08-26 — el micro del módulo.** La partición en dos
> columnas con dos RP2350B era la última pieza de #164 que gobernaba
> arquitectura, y **se cae entera**: el módulo pasa a **un solo STM32N657**
> (motor-digital §1, *«los dos RP2350B mueren; el N657 hereda»*).
>
> Lo que se cae con ella, y hay que decirlo porque eran cimientos de otras
> secciones: la **base de tiempo compartida** entre columnas, el **arranque
> en dos mitades**, y **la historia entera de recuperación entre columnas**.
> Ninguna de las tres tiene sentido con un micro: no hay dos relojes que
> alinear, ni dos arranques que ordenar, ni una columna que rescate a la otra.
>
> La razón por la que #164 quiso dos micros era **una sola**: dieciséis
> osciladores pedían dieciséis cronómetros y el RP2350 daba doce máquinas de
> PIO. El N657 trae los dieciséis en sus timers de hardware (motor-digital §7:
> 14 en TIM2-5 de 32 bits + 2 en TIM1 de 16 con desbordes contados). **Muerto
> el motivo, muere la partición.**

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

> **Enmienda del 2026-08-26 — la ley de dos tasas (acta A-4).** La tasa única
> de arriba gana un segundo escalón. **No es derogación**: los 10 kHz siguen
> siendo la tasa de la casa, con su presupuesto vigente intacto.
>
> - Los **destinos rápidos** rinden a **48 kHz**. En v1 son exactamente
>   **los 16 CV de corte** (S-9) — el acta de Samuel pedía CV a velocidad de
>   audio, y esa es la lista de hoy.
> - **Todos los demás siguen a 10 kHz**, envolventes incluidas. Esta sección
>   sigue gobernando la clase lenta.
> - **Promover un destino a rápido es acta de Samuel + guion recorrido.** Ni
>   criterio implícito ni censo fantasma: si mañana alguien quiere el índice
>   FM a 48 kHz, hay que decidirlo y correrlo, no deducirlo.
>
> La aritmética entera —los 3 buses SPI a 50 MHz nominales, la palabra de
> 16 bits viajando en trama de DAC, la eficiencia 0,60— vive en
> motor-digital §5, no aquí. Y el aviso que la acompaña: **la v1 de aquel
> papel escribió un «margen ≥2×» que su propio rango desmentía**, y la junta
> lo cazó como patrón #206. La cuenta buena es la de allá.

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

> **Enmienda del 2026-08-26 — dos tercios de esta cota se evaporaron.** Con
> un solo N657 ya **no hay etapa maestro→esclavo** ni **columnas** entre las
> que uniformar. Mueren, por dejar de tener referente:
>
> - el término *«incluyendo la etapa maestro→esclavo»* (no hay reenvío);
> - el *«jitter maestro-vs-esclavo, sistemático y asimétrico»* (no hay dos);
> - el *«uniforme entre columnas dentro de ±0,5 ms»* (hay una sola).
>
> **Lo que sobrevive intacto es lo que importa: el objetivo de ≤ 3 ms de
> nota a VCA**, y la cláusula de que `ataque_budget.py` no asevera nada hasta
> que el mensaje exista. El camino se acortó; la vara no se relaja.
>
> La arquitectura de tiempo real que ocupa el sitio de la vieja está en
> motor-digital §7 (prioridades NVIC: capturas y J2 > DMA de audio > USB y
> Ethernet > resto; ISR críticas en ITCM), y **el presupuesto de latencia de
> interrupción se mide en bring-up bajo carga plena** — no se declara.
>
> **El formato del mensaje sigue sin estar en `main`.** Lo diseña el papel
> del evento de nota (PR #207), que hoy está frenado — ver el comentario de
> ese PR. Así que este prerrequisito **sigue bloqueante**: cambió su
> aritmética, no su estado.

### 3.4 El reparto del micro, declarado

> ### ⚠️ Sección SUCEDIDA ENTERA — enmienda del 2026-08-26
>
> **Su sucesor es motor-digital §7** («La arquitectura de tiempo real,
> declarada», que se nombra a sí misma *«el sucesor de voz-total §3.4»*).
>
> Lo de abajo repartía trabajo entre **dos núcleos de un RP2350B**. El N657
> es de **un solo núcleo** (Cortex-M55): no hay núcleo 0 ni núcleo 1 que
> repartir, y el reparto de abajo no se «adapta» — desaparece.
>
> Lo que ocupa su sitio no es otro reparto entre núcleos, sino **un orden de
> prioridades y una delegación en hardware**: capturas y J2 por encima del
> DMA de audio, ese por encima de USB y Ethernet, y el resto detrás; ISR
> críticas en ITCM; los dieciséis cronómetros en timers de hardware en vez de
> PIO. El trabajo no se reparte entre manos: **se delega a periféricos que
> corren solos**, y lo que queda de CPU vive en el libro bilateral
> (`carga_motor_budget.py`).
>
> **Una regla de abajo sobrevive y hay que rescatarla, porque su motivo no
> murió con el chip:** *«el esclavo J2 nunca pierde su ventana de MISO»*.
> Sigue siendo cierta y sigue mandando — en motor-digital §7 vive como la
> prioridad más alta junto a las capturas. Que cambie el micro no le quita
> la razón.

<details>
<summary><b>Texto original de §3.4</b> (histórico — repartía dos núcleos que ya no existen)</summary>

El micro del módulo es tiempo real duro por tres frentes (esclavo J2,
render de envolventes, PIO de afinación) y la v1 no asignaba nada
(H-CF1). Se declara el reparto — el plan lo detalla, este spec lo fija:

- **Núcleo 0**: esclavo J2 + eventos + telemetría (latencia manda).
- **Núcleo 1**: render de envolventes + escritura DAC + drenaje de PIO
  (caudal manda).
- Prioridades NVIC y canales DMA: documento del plan, **bloqueante**, con
  la regla de que el esclavo J2 nunca pierde su ventana de MISO.

</details>

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

> **Enmienda del 2026-08-26 — la bahía gana una fuente y un destino que no
> vienen de ningún jack.** El crosspoint dejó de ser solo la frontera con el
> mundo físico: el códec entra por los dos lados (motor-digital D-P1 y D-P4).
>
> **Fuente nueva — la boca del códec (D-P1).** Las salidas del códec (estéreo
> en v1) se conectan como **fuentes del crosspoint**. Consecuencia musical, y
> es grande: el audio digital se patchea como cualquier señal — al nodo de
> suma de un canal, **a través del MS-20 y el VCA de una voz real**, en
> retroalimentación, a donde el preset diga. Un sample o un motor digital
> pueden entrar por el filtro analógico.
> - **Contrato eléctrico nuevo:** entre boca y crosspoint hace falta una
>   **etapa de acople y ganancia** que lleve el nivel de línea del códec al
>   nominal de la bahía (mundo ±12 V). El número exacto no lo fija este
>   papel.
>
> **Destino nuevo — los oídos ruteables (D-P4).** Para que exista el patch
> «señal → corte», los oídos ganan **entrada desde el crosspoint**. Dos vías,
> y el guion las compara en vez de elegir a ciegas:
> - **vía códec** — audio fiel, pero carga el retardo de grupo del códec
>   (~ms, ESTIMADO): modulación a velocidad de audio con latencia de códec;
> - **vía ADC rápido del micro** — 12 bits a 5 Msps: µs de lazo para la FM de
>   corte apretada, con menos bits.
>
> La subida ya existía (los oídos de E-5). **Con esto el puente queda
> bidireccional**, y por eso la fila lo dice completo: la bahía necesita
> **censo** — fuentes nuevas y destinos nuevos contra las 16×16 de los dos
> AD75019, que no son infinitas. El censo está mandado en motor-digital §8.4;
> **no está hecho**, y hasta que corra nadie sabe si las dos vías caben a la
> vez.

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

`check_censo_voz.py` asevera; **bloqueante**. Estimaciones:

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
> **PARCIALMENTE DESBLOQUEADO el 2026-08-27** — rescatado del PR #201 al
> cerrarlo. El **cambio 2 (ranuras lógicas)** tenía su decisión abierta en
> `2026-08-22-vco-orquestacion-design.md` §«Decisiones abiertas», punto 1, y
> **ya está cerrada: DOS ranuras**, por espacio de direcciones — `MAX_INSTANCIAS
> = 16` lo consumen exacto los dieciséis osciladores y las 72 entradas del censo
> que no son voces necesitan la suya. Lo que queda del cambio 2 es escribirlo,
> no decidirlo.
>
> **Corregido el mismo 2026-08-27, unas horas después.** Esta enmienda nació
> diciendo «UNA ranura, funcional y nunca por micro» y era leer mal la pregunta:
> la regla de Samuel —una ranura jamás refleja anatomía de hardware— prohíbe una
> tercera opción (una por micro), no elige entre una y dos. Las dos que estaban
> sobre la mesa eran funcionales las dos. El texto corregido y su razonamiento
> completo viven en `2026-08-22-vco-orquestacion-design.md` §«Decisiones
> abiertas», punto 1.
>
> **El cambio 12 (lotes) sigue bloqueante y sin tocar**, así que la frase de
> abajo sigue siendo cierta por su segunda mitad: el modelo de la Voz total
> todavía no es direccionable, pero ya no por falta de una decisión.

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
| ~~Fila A: Voz 305 + bahía 100 + reserva 40~~ | ~~**445 de 528**~~ **ENMENDADA 2026-08-27** |
| ~~Fila B: cerebro 150 + mandos 120 + mixer 100 + reserva 40~~ | ~~**410 de 528**~~ **ENMENDADA 2026-08-27** |
| Fondo Voz: 5 + 1,6 + 2×10,6 + 2×h | **37,8 de 50** (h ≤ 11,1) |

El primer reparto salió ROJO por 17 mm y el guion lo registra.

> **ENMIENDA 2026-08-27** — `2026-08-27-panel-pantalla-al-centro-design.md`.
> **El reparto por filas deja de ser una lista de módulos.** La fila A pasa a
> ser **un solo módulo de 104 HP (528,32 mm)** con la pantalla de 7" en su
> centro y los mandos en los dos flancos de 181,66 mm; la **bahía sale del
> panel** (al valle, a resultas de un estudio). En la fila B **muere la cabeza
> local de 2,8"** —la 7" es la única cabeza desde esa fecha— y se liberan sus
> 30 HP.
>
> **Lo que NO cambia y conviene no perder en la mudanza:** el PCB de la Voz
> sigue cerrando en 421,5 mm y **no crece**. Las perillas son sensores del
> panel, así que el panel puede volar sobre el borde de la placa sin tocar el
> factor de ruteo — que sigue siendo «el número menos medido de todo el
> diseño» y por eso se deja quieto a propósito.
>
> `voz_total_budget.py` sigue presupuestando **PCB, no panel**: le falta
> `ANCHO_PANEL_A`, que ahora vale 104 HP y no 83.

**El consumo se re-suma entero, no en delta** (S-8: la v1 comparaba +90 mA
contra los 650 totales como si fueran holgura libre). `consumo_total_budget.py`,
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
- ~~**Heartbeat del esclavo dentro del SPI privado**~~ **(muere: no hay
  esclavo)**: el maestro lo vigila; esclavo muerto → `RESET_ESCLAVO` (los
  DACs vuelven a cero-escala, §9.1).
- ~~**El esclavo vigila al maestro**~~ **(muere: no hay maestro)**: SPI
  privado mudo en N ms → release local. Maestro muerto ≠ ocho voces
  congeladas sonando.
- Mutaciones: matar cada micro a mitad de nota y medir que el silencio
  llega solo.

> **Enmienda del 2026-08-26 — sucedida por R-M5, y el problema se puso PEOR,
> no mejor.** Sucesor: motor-digital **R-M5**, *«el silencio no depende del
> software»*.
>
> **Dos de los cuatro failsafes de arriba se caen solos**, porque eran micros
> vigilándose entre sí y ahora hay uno. Y ahí está el punto que hay que decir
> sin adornos: **la vigilancia mutua era la red de seguridad, y desapareció**.
> Con dos micros, uno colgado dejaba al otro vivo para afirmar silencio. Con
> uno solo, **el N657 es el único escritor de 48 VCAs**: colgado, dieciséis
> voces quedan gobernadas por un muerto. Motor-digital lo llama *«la
> enfermedad del #201, tercera función»* — y es el **riesgo 9** de aquel papel.
>
> Por eso el sustituto no es otro watchdog de software, que sería más de lo
> mismo: es **watchdog independiente + estado seguro por hardware**. Los VCAs
> y el crosspoint caen a silencio **sin CPU** — inhibición atada a reset, el
> patrón H-OF4. *Cierre del riesgo 9:* R-M5 dibujado en el esquemático y
> **demostrado matando la CPU en bring-up**, no argumentado.
>
> **El watchdog de trama (el primero de la lista) sobrevive entero** — no
> dependía de haber dos micros — y la mutación de abajo también, con una
> palabra menos: matar **el** micro a mitad de nota y medir que el silencio
> llega solo.

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
| `check_censo_voz.py` | parámetros, memoria, cotas | bloqueante |
| `cal_filtro_budget.py` | tiempos de caracterización | bloqueante |
| `consumo_total_budget.py` | instrumento entero por riel | bloqueante |
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
6. Los ~520 parámetros y los ~24 KB son estimación hasta `check_censo_voz.py`.
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
| S-8 | Consumo en delta contra el total | §8: `consumo_total_budget.py` bloqueante |
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
- **Reserva de invitados por riel.** `consumo_total_budget.py` (§9.4) deja de sumar
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

> **Enmienda del 2026-08-26 — el códec gana boca, no solo oídos.** Esta acta
> trajo el códec a la placa como **oídos**: cómo el instrumento se escucha a
> sí mismo. La enmienda le añade la otra mitad: **el códec también habla**.
>
> Sus salidas entran como **fuentes del crosspoint** (D-P1, enmendado en §5),
> así que el códec deja de ser un sentido y pasa a ser **un puente
> bidireccional** entre el dominio digital y el analógico. Lo que sube por
> los oídos puede bajar por la boca, pasar por un MS-20 y un VCA de verdad, y
> volver a subir.
>
> Consecuencia para el papel: donde E-5 dice «los oídos», hoy hay que leer
> **«el códec»** — con sus dos direcciones. La derogación de §0.4 punto 2 y
> todo lo demás de esta acta siguen intactos.

### E-6. La salida es ESTÉREO, con sitio por voz

Decidido: el instrumento reparte sus voces en el campo estéreo. Es la mitad de
por qué un poli suena grande, y decidirlo después del layout cuesta el layout.

Eran dos caminos, y esta primera versión del acta dejó la elección para el
pase de diseño **suponiendo** que el caudal la decidía. `spi_privado_budget.py`
ya está escrito y corrido, y esa suposición era falsa:

| | VCAs de voz | CV por canal | SPI privado por micro | SCLK que pide |
|---|---|---|---|---|
| **A**: dos VCAs por canal (L/R), cada rama con envolvente × paneo | 32 | 4 | 6,05 Mbit/s | **10,1 MHz** |
| **B**: un VCA de envolvente + etapa de paneo detrás | 48 | 5 | 4,16 Mbit/s | **6,9 MHz** |

**A pide 1,45× el caudal de B, no 2×**, y las dos caben con holgura contra un
techo declarado de 20 MHz. El error del razonamiento: el CV de corte **ya** es
un flujo a tasa de render en las dos topologías —§2 hace que el micro le sume
la envolvente de filtro y escriba el DAC— así que A pasa de dos flujos por
canal a tres, no de uno a dos.

**Se elige A.** Menos cobre —ocho chips menos entre VCA y DAC— y el único
argumento que sostenía a B se cayó con el número delante. La holgura de cómputo
también aguanta: 625 ciclos por valor de envolvente a 150 MHz.

> **Y un hallazgo que sale de escribir el guion, que toca al cuerpo del spec:**
> §3.1 cuenta *«8 envolventes × 10 kHz son 80k escrituras/s por micro»* — una
> por canal. Pero §2 hace del CV de corte un segundo flujo a tasa de render, y
> el módulo 6 que desaparece eran **dos** generadores ADSR, no uno. La línea
> base de §3.1 está a la mitad de lo que su propio §2 implica, **antes** de
> meter estéreo. No rompe nada —el caso corregido también cierra, 6,9 MHz— pero
> la cifra del spec está mal y hay que corregirla.

**Lo que E-6 reabrió, y cómo quedó.** Los cuatro presupuestos estaban
declarados en §9.4 y **ninguno existía como guion**. Se escriben, se corren, y
el resultado es este:

| Guion | Veredicto | Cifra |
|---|---|---|
| `spi_privado_budget.py` | **VERDE** | 10,1 MHz de SCLK contra un techo de 20. §3 sobrevive |
| `voz_total_budget.py` | **VERDE, más estrecho** | fila A a 421,5 de 488,3 mm (15,8 %); el factor de ruteo al que rompe baja de ×4,6 a **×3,79** |
| `consumo_total_budget.py` | **VERDE** | 340 mA en el peor riel de 500 útiles; quedan **160 mA/riel** para los invitados de E-4 |
| `check_censo_voz.py` | **ROJO en dos de tres techos** | ver abajo |

**El censo es el que trae malas noticias, y son las que la spec ya esperaba:**

- **`MAX_PARAMS = 512` (`modelo.rs:9`) contra 536 parámetros.** Se pasa por 24.
  Y el techo es del **instrumento entero**, no de este módulo: un solo módulo se
  come el 105 %. Es el cambio 2, y esto es la cifra que lo hace prerrequisito.
- **El descriptor son 25 512 B contra los 238 B que el `u8` de
  `descubrimiento.rs` puede anunciar** — 107×. Es el cambio 18.
- **La memoria sí cabe, al 91 %** de los 32 KB elegidos en #164. La petición de
  64 KB de §7 queda justificada por el margen, no por la necesidad: hoy entra,
  pero el siguiente parámetro por canal cuesta 672 B y solo quedan 2 968.

Y una consecuencia que no es de presupuesto: **§9.1, el camino de silencio** —
ya no son 32 VCAs en estado seguro, son **48**: los dieciséis de resonancia más
treinta y dos de voz. El criterio «encender el instrumento con cables puestos
no suena» no se ablanda por eso, y la mutación de encendido tiene que cubrir
los nuevos.

### E-7. La memoria del módulo pasa a 128 KB

`check_censo_voz.py` dio **29 800 B**. Contra los 32 KB decididos en #164 §19
eso es el **91 %** — y este módulo creció un 21,7 % de área y ganó un parámetro
por canal en **una sola sesión** (E-5 y E-6).

**Pero el tamaño no lo decide cuántos parámetros caben. Lo decide cuántos bytes
ocupa la entrada de cada uno.** Hoy son 42 B (#164 §13). Y el descriptor no es
un dato interno: `architecture-compute` §6 lo dice sin ambigüedad — *«los
nombres y las unidades de cada parámetro no son cosmética: son la documentación
que el modelo va a leer»*. El servidor MCP sale casi gratis por eso. Nombre
legible, unidad, rango, valor por defecto y una línea de qué hace no caben en
42 B: caben en unos **100**.

Con ese objetivo declarado, el guion decide solo:

| | Aguanta hasta | Con 100 B/entrada |
|---|---|---|
| 32 KB | 29 B | NO CABE |
| 64 KB | 72 B | NO CABE |
| **128 KB** | **158 B** | **cabe** ← elegido |
| 256 KB | 329 B | cabe, y sobra |

**Se sube a 128 KB: `24AA1025`.** Es el más pequeño que aguanta la razón por la
que se sube. El censo queda al **23 %**.

**Por qué no 256, para no volver a preguntarlo.** A 329 B por parámetro se
compra un párrafo entero por perilla, que nadie escribe. Y pasado el `24AA1025`
la pregunta deja de ser *«qué EEPROM»* y pasa a ser *«por qué EEPROM»*: una
flash SPI de 4 MB cuesta lo mismo y da dieciséis veces más, **en un bus que este
módulo ya tiene**. Lo que ata a la EEPROM es que se escribe byte a byte y la
flash se borra por sectores de 4 KB — y la tabla de afinación la reescribe el
autoafinado solo. El día que haga falta guardar **sonido** —formas de onda,
bancos grandes— la respuesta es flash, y es otra decisión.

**Lo que cuesta, en dos partes.**

*Un chip.* #164 (pieza 3) había encontrado el `24AA256UID`, que daba los 32 KB
**y** EUI-48, EUI-64 y serial de fábrica — *«es un chip, no dos»*. **Esa pieza
no existe por encima de 32 KB**: la familia UID de Microchip se acaba ahí,
verificado contra catálogo y hojas. Se vuelve al arreglo de dos chips que #164
§13 ya describía, con el `24AA02E48` —que nunca salió del BOM— haciendo la
identidad.

*Una costura.* El `24AA1025` **no es un chip de 128 KB: son dos de 64 con un
interruptor.** Verificado contra su hoja (DS21941H): el byte de control es
`1010 B0 A1 A0`, el bit `B0` hace de A16, y **`A2` no es configurable — va atado
a VCC o el chip no responde**. Tres consecuencias:

1. **Ocupa dos direcciones.** Con `A0` = 1 responde en **0x51** (bloque bajo) y
   **0x55** (alto). Con `A0` = 0 caería en **0x50**, que es donde vive el
   `24AA02E48`: **hay colisión si se cablea a cero.** El 0x51 que #164 §13 ya
   planeaba sigue valiendo; el **0x55 es nuevo y hay que reservarlo**.
2. **El firmware tiene que conocer la costura**: cambiar de dirección al cruzar
   los 64 KB, y partir en dos cualquier escritura que la atraviese. Unas veinte
   líneas y un test que escriba a caballo del borde.
3. Página de **128 B** y **1 000 000 de ciclos** en modo página — misma
   resistencia que las piezas que ya hay. Eso no empeora.

**Deroga** la decisión 19 de #164 y su pieza 3.

> **El camino que haría esto innecesario, declarado y no tomado:** el descriptor
> es el **69 %** de la memoria, y describe dieciséis canales idénticos entrada
> por entrada. Un descriptor que dijera «este bloque, ×16» lo colapsaría a un
> tercio. Es la respuesta buena, y toca el formato congelado y sus 190 tests: no
> se hace hoy por un chip de treinta centavos, y no se olvida.

### Lo que este acta NO decide

El reparto de anchos de panel con los conectores ya mudados, quién shiftea el
crosspoint (E-3), y nada del cajón. Cada uno va en su propio pase. La idea de
que la fila de abajo fuera también un módulo único **muere aquí**, con E-4.
