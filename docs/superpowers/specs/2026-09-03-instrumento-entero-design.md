# El instrumento entero: se retira la cadena de LED

**Versión:** v2 — pasó la junta, firmada por Samuel. **Dos preguntas salieron del
papel a conversación propia (§6.1), por dirección suya.**
**Fecha:** 2026-09-03
**Dirección de Samuel**, esta sesión, textual:

> «lo de los leds ya no va. ahora que tenemos la pantalla no necesitamos los
> leds»

> «ahora pasamos a construir el sintetizador como un whole entonces no
> necesitamos pachear internamente por eso todo esto puede ser prescindible»

> «si siguen, necesitamos que el instrumento se pueda conectar ampliamente con
> el exterior»

**Cierra:** #42, #104. **Encoge:** #297. **Toca:** #103, #151.
**Cuelga de:** `2026-08-23-modulo-voz-total-design.md` §5.1 ·
`architecture-poly.md` §6 y §7 · `2026-08-17-nucleo-digital-design.md` §6.2 y §10 ·
`2026-08-23-panel-frontal-gramatica.md` §5 y §7

---

## 0. Alcance

1. Escribe la decisión de origen —**el instrumento se toca entero**— y la ata a
   la que el repo ya había tomado el 23-08.
2. Retira la **cadena WS2812** y reparte **todos** sus trabajos, no tres.
3. Deja mandado, con dueño y con rango de líneas, lo que la retirada desarma en
   otros papeles.

**Lo que NO hace:** no diseña la conexión con el exterior (§6), no rediseña el
panel, no toca el J2, no elige el driver de las coronas (§3, D7), **no decide si
el mux de perillas se queda en el módulo** (§7, E7), y **no decide cómo se dice
lo que una cosa física significa ahora mismo** — el nombre del jack y el señalar
del agente salieron a conversación propia (§6.1).

**Lo que la v1 decía y era falso**, para que no se herede: que el patcheo
interno moría hoy (murió el 23-08, §1), que la cadena tenía tres trabajos (tiene
al menos siete, §2), que sobrevivía un LED testigo (su premisa se derogó el
30-08, D5), y que las constantes de LED de `power_budget.py` se retiraban a cero
como `BACKLIGHT_A` (revientan dos asertos, §4).

---

## 1. Quién mató el patcheo interno, y cuándo

**No fue la decisión de hoy. Fue un chip, el 2026-08-23.**
`2026-08-23-modulo-voz-total-design.md` §5.1, líneas 439-444, entero:

> **8 entradas + 8 salidas** en jacks Thonkiconn (TN conectado, sensado de
> ocupación, LED por jack), ruteadas por **dos AD75019** (crosspoint 16×16,
> ±12 V, carga serie): entradas → los 16 nodos de suma; las 16 salidas
> post-VCA → salidas. El jack es un nombre que le da el preset; su LED dice
> en color qué es. El recall del patch interior se recuerda solo; solo los
> cables hacia el mundo siguen siendo físicos.

La última frase es la dirección de Samuel de hoy, escrita once días antes. Y ya
está en el hierro: `hardware/02-midi-cv/micro_budget.py` líneas 293-297 cobra
«los dos AD75019 en cadena por un **SPI PROPIO**» (acta 2026-09-02, issue #171).

**Por qué importa quién lo mató.** Bajo la causa que la v1 daba —«se toca
entero»— el residuo es difuso: los jacks siguen ahí, así que quién sabe. Bajo la
causa real el residuo está nombrado en la propia fuente: **solo los cables hacia
el mundo siguen siendo físicos.** Es exactamente lo que §5 y §6 desarrollan.

La decisión de Samuel del 03-09 **ratifica** eso y cierra lo que quedaba
colgando: si el patch interior se recuerda solo, la maquinaria que existía para
reconstruirlo a mano no tiene trabajo.

**Y el normalizado no se toca.** `architecture-poly.md` §6, líneas 303-305:

> - **Nada enchufado** → es un poly de 4 voces que suena solo, cero cables.
> - **Un cable enchufado** → **rompe el normalizado de esa conexión** y enrutas
>   a tu gusto, incluyendo sacar una voz suelta y meterla por donde quieras.

Eso ya hacía que sonara entero. Lo que cambia es cuál de las dos filas es el
centro del diseño.

---

## 2. Los trabajos de la cadena. Son siete, no tres

La v1 enumeró tres y afirmó «ninguno más». El método estaba mal y conviene
dejarlo escrito, porque se va a repetir: **enumeré a quien le encargó trabajo a
la cadena, no a quien se apoyaba en ella.** Los cuatro que faltaban están en
papeles que nunca la pidieron —y dos, en código con tests verdes.

| # | Trabajo | Fuente | Dónde queda |
|---|---|---|---|
| 1 | **Soft-takeover / `ANULADO` por perilla** | `architecture-poly.md` §7; `tiempo-musical` §2.2 y §6.3 | **Ya mudado dos veces antes de este papel** — D2 |
| 2 | **Guía de patcheo por jack** | `architecture-poly.md` l. 421-435; `nucleo-digital` §6.2 y §10 | **Derogado** — D3 |
| 3 | **Señalar**: el agente enciende el LED de la perilla que le preguntas | `nucleo-digital` §2.1, l. 138-141; `protocolo.rs` `Point`, `servidor.rs:453` | **Aparcado** — §6.1 |
| 4 | **Identidad del jack de la bahía**: «su LED dice en color qué es» | `voz-total` §5.1, l. 442-443 | **Aparcado** — §6.1 |
| 5 | **Acuse de «ruta pendiente»** bajo `diferir` | `voz-total` §5.3; test vivo en `core/tests/bahia.rs:165` | **Al renglón** — D8 |
| 6 | **Color por preset o banco**: «de un vistazo sabes dónde estás» | `architecture-poly.md` l. 423-424 | **A la pantalla** — D2 |
| 7 | **Coronas de LED de los 4 MACROS** (valor del pote) | `panel-frontal-gramatica` l. 114 y 251 | **Sobreviven, familia aparte** — D7 |

**El octavo no existe.** La v1 tenía un trabajo #3 llamado «la cara del
instrumento con el motor muerto». Su premisa está derogada; ver D5.

---

## 3. Decisiones

### D1 — La cadena WS2812 se retira entera

Se retiran: el LED por perilla, el LED por jack, el farol del interior (#42), el
mazo propio de tres hilos, la fila `LED` de las dos tablas de arquitectura, y el
árbitro de brillo (#104) con la función que lo nombra.

| Lo que se va | Cifra y fuente |
|---|---|
| El consumidor atenuable del +5 V digital | `power_budget.py` l. 158-160: `LED_A_BLANCO_PLENO = 9.60`, `LED_A_CASO_REAL = 2.04`, `LED_A_TOPE_104 = 2.50` |
| El árbitro de brillo (#104) | Título del issue: «El farol y la guia de patcheo comparten 2,8 A». **Los dos clientes que se reparten mueren aquí** — pero ver E9: la retroiluminación de la pantalla es un tercer cliente declarado |
| El único problema del N657 sin PIO que quedaba abierto | `pinout.rs` l. 18-23: los cronómetros son capturas de TIM, el host USB va por el OTG nativo |
| 16 WS2812 por placa de panel del VCO-16 | `2026-08-22-modulo-3-vco-dieciseis-design.md` l. 172-174 y 249-252 |
| El requisito de espacio único de direcciones | `2026-08-22-modulo-3-vco-dieciseis-design.md` l. 1038 — **no está en `nucleo-digital`, la v1 lo atribuyó mal** |
| La disciplina `GNDD` del mazo de luz | `architecture-poly.md` l. 439-441 |

### D2 — El soft-takeover **ya estaba mudado**. Esto lo ratifica

No es una decisión nueva. `2026-08-23-panel-frontal-gramatica.md` §5, punto 5,
líneas 205-209:

> El estado `ANULADO` necesita **superficie física**: A3 mató el LED por
> perilla y el spec del tiempo (§6.3) le tenía asignada esa segunda
> función. El renglón lo repone: parámetro anulado que se toca → el
> renglón lo dice. La cuenta agregada (`ID_ANULADOS`) no basta: el
> descriptor debe publicar **cuáles** (cambio de núcleo, §11.1).

Y el renglón lo absorbió la pantalla cuatro días después
(`panel-pantalla-al-centro`, l. 270-272: la 7" «sustituye a la cabeza local de
2,8" del cerebro **y al renglón del panel**»).

**O sea que el camino ya estaba recorrido: LED por perilla → renglón (23-08) →
pantalla (27-08).** Lo que este papel hace es cerrarlo y decir que no vuelve.

**Coste declarado:** la mano está en un sitio y el ojo en otro. Se acepta, y ya
se aceptó dos veces.

### D3 — El patcheo guiado se deroga, en **tres** sitios

| Sitio | Qué dice hoy | Rango |
|---|---|---|
| `nucleo-digital` §6.2 | La sección entera, «la razón de que los presets existan de verdad» | l. 837-885 |
| `nucleo-digital` §10 | **Restricciones globales a los módulos 5, 6 y 7**: sensado de ocupación, toda entrada de CV patcheable legible por ADC, un LED por jack | l. 1276-1299 |
| `2026-08-22-modulo-3-vco-dieciseis-design.md` | Lista de requisitos (l. 100-102), placa de panel (l. 172-174), §6.3 (l. 461-482), l. 1038 | varios |

**§10 es el que importa.** Son requisitos duros sobre placas que **todavía no se
dibujan**: quien dibuje el módulo 5 leyendo solo §10 pondrá LED por jack y
registro de desplazamiento. La v1 derogaba §6.2 y dejaba §10 vivo — el defecto
que ella misma advertía («o el repo se queda con dos arquitecturas vivas»).

### D4 — Señalar sale del papel

`nucleo-digital` §2.1, líneas 138-141:

> **El agente puede señalar.** Como la cadena WS2812 es direccionable y se
> alcanza por el modelo, *«¿dónde está el cutoff?»* enciende el LED de esa
> perilla. **Señalar y el patcheo guiado son el mismo mecanismo — el segundo
> sale gratis del primero.**

De aquí sigue que **señalar es el primitivo y el patcheo guiado el derivado**, y
la v1 los tenía al revés: derogó el derivado y retiró el primitivo de paso.

Está construido, no propuesto: `software/nucleo/core/src/protocolo.rs` líneas
82-87 define `Point { id: ParamId, color: Rgb }` con el comentario que cita esa
sección; `T_POINT = 0x0C` está en el protocolo congelado; `servidor.rs:453`
tiene rama viva devolviendo `NoDisponible` con el comentario «La cadena WS2812
llega con el plan de los perifericos».

**Qué se decide aquí: nada.** Por dirección de Samuel, señalar sale a la
conversación de §6.1, junto con el nombre del jack.

**Consecuencia operativa: `protocolo.rs` y `servidor.rs` no se tocan en esta
tanda.** `Point`, `Rgb` y `T_POINT` se quedan exactamente como están, y la rama
del `NoDisponible` también. Un mensaje congelado no se borra mientras su
decisión esté abierta — y su comentario tampoco se corrige a «nunca», porque
todavía no se sabe.

### D5 — **No hay testigo.** Su premisa se derogó el 2026-08-30

La v1 mandaba un LED en un GPIO para decir «el motor no arrancó». Se retira, por
dos razones independientes y cada una basta.

**Primera: el pasaje que lo justificaba está tachado.**
`2026-08-27-panel-pantalla-al-centro-design.md` líneas 144-156: el texto original
va entre `~~`, y encima lleva:

> **Enmienda del 2026-08-30 (D2, FIRMADA): la cara se queda en el cerebro.**
> El cerebro pasa a STM32N657 (D1), así que la pantalla cuelga de **su**
> LTDC y no hace falta mudarla al motor — que además la quería en la misma
> SRAM que su audio. El requisito que motivaba la mudanza («que el
> instrumento diga algo aunque el motor no haya arrancado») lo cumple
> mejor así: la pantalla vive en el chip que arranca primero. Del tamaño
> decide A-7/A-8 — **5" en la primera placa** (la del kit de pruebas) y
> 7" en las siguientes, sobre el mismo cobre. Fuente: spec del hub N657,
> §3.1.

O sea: ya no hay un motor aparte del que la pantalla cuelgue. El requisito que
la cadena venía a cubrir **lo cumple la arquitectura**, firmado.

**Segunda: con un solo chip, el testigo no puede atestiguar.** Un LED colgado
del GPIO del cerebro no puede declarar que el cerebro no arrancó — muestra
«apagado», que es indistinguible de LED quemado, pista rota, pin en su estado de
reset, o falta de alimentación. Y un cerebro que arranca y **después** se cuelga
deja el LED como estuviera: el modo de fallo más probable es el que menos se ve.

Es el mismo defecto que este repo ya cazó y derogó.
`2026-08-22-vco-orquestacion-design.md` §2.3, derogada el 2026-08-27:

> **Esa vigilancia nunca funcionó** [línea aparte] un módulo con el micro muerto
> publicaba sus capacidades igual: **la ausencia de descriptor no era señal de
> nada**.

De aquí sigue la ley que este repo ya aplica en otros sitios (R-M5, «el silencio
no depende del software»; el pull-down por hardware de los gates): **lo que juzga
un fallo no puede colgar del sujeto del fallo.**

**Lo que sí existe y no se toca:** `panel-pantalla-al-centro` §4 ya manda como
físicos, en tabla, el **BOOTSEL y RUN** del cerebro —«sin eso, recuperar una
placa con firmware malo pide desarmar el instrumento»— y el **acceso de
recuperación del motor**. Ese es el camino de recuperación real, y no necesita
una luz para existir.

### D6 — El nombre del jack sale del papel

Nace de un choque que la v1 no vio: **dos ontologías del jack, las dos vivas.**

| | Hoy (`voz-total` §5.1) | Lo que pide §5 de este papel |
|---|---|---|
| Qué es un jack | «El jack es un nombre que le da el preset; **su LED dice en color qué es**» | Un punto de conexión con el exterior |
| Qué exige | Rótulo dinámico — o sea, la cadena | Identidad fija y serigrafiada |

**Qué se decide aquí: nada, y no hace falta decidirlo para retirar la cadena.**
Dirección de Samuel, textual:

> «es mucho mas complejo que eso, van muchas cosas alli, no solamente los jacks
> de las voces. tambien van otros parametros. esto tenemos que pensarlo bien»

**Y D1 no lo prejuzga**, porque el rótulo dinámico ya tiene otra superficie en el
panel firmado. `2026-08-23-panel-frontal-gramatica.md` línea 118, fila BAHÍA:

> 16 Thonkiconn en **4×4 a paso 17 mm, pegada al canto derecho** + ventana
> propia de 68×16 (nombre de cada jack)

Una ventana dedicada solo a decir cómo se llama cada jack. Las dos salidas
—serigrafía fija o rótulo dinámico— siguen abiertas después de retirar la
cadena, y ninguna depende de ella.

### D7 — Las coronas de los MACROS sobreviven, y son familia aparte

`2026-08-23-panel-frontal-gramatica.md` línea 114: «**MACROS** | 4 potes
gigantes en cuadro 2×2, corona de LEDs por cap (valor); el nombre vive en el
renglón». Y línea 251, la acotación de la junta del panel: «no dieciséis
ventanas — UNA de renglón, una de bahía, y **cuatro coronas de LED**».

No son la cadena: son el valor de cuatro perillas gigantes, **en la perilla**.
Están en el paquete de panel firmado, y nada de la dirección de Samuel las toca.
Sobreviven.

**Pero se quedan sin mecanismo**, porque el mecanismo era la cadena. Eso es
justo lo que #297 pedía decidir, así que **#297 no se cierra: se encoge** — de
«la luz del panel» a «cuatro coronas piden un driver de corriente constante por
bus serie». Con la cadena fuera, ese driver ya no compite con el J2 ni con el
audio por atención de CPU, que era la mitad del argumento del issue.

### D8 — El acuse de «ruta pendiente» va al renglón, y ya estaba mandado

`voz-total` §5.3 dice que bajo `diferir` «la interfaz y el LED del jack muestran
pendiente», y hay un test verde que lo cita: `core/tests/bahia.rs:165`. El estado
**no tiene fondo por diseño** — el test se llama
`diferir_espera_para_siempre_al_canal_que_cambia_y_suena`— y su justificación
(H-OF3) era que la starvation deja de ser un bug **porque es visible**.

No hace falta inventar nada: la junta del panel ya lo había mandado.
`panel-frontal-gramatica` §6, condición 3, líneas 235-239:

> **Acuse local en el renglón**: bajo `diferir` con un drone sonando, el
> gesto produce «ruta pendiente» — indefinidamente y por diseño. Eso se
> muestra donde ocurrió el gesto, no solo en el LED del jack; y los
> commits pendientes sobre el mismo cruce **se fusionan** (el último
> gana), no se encolan en ráfaga.

«No solo en el LED del jack» pasa a ser «no en el LED del jack». El renglón vive
hoy en la pantalla (D2).

### D9 — El sensado de ocupación **sobrevive**, y no por el patcheo guiado

D3 deroga el sensado como requisito del patcheo guiado. Pero tiene dos clientes
más, y ninguno se cae:

1. **La ley de capas.** `voz-total` §0.2, ley 1, líneas 106-111: «Un gesto físico
   (perilla, **cable en la bahía**) captura ese parámetro **o ruta**». Sin
   sensado no hay sensor para uno de los dos gestos que esa ley legisla, y el
   agente seguiría automatizando una ruta que la mano acaba de tomar, en
   silencio.
2. **La atribución.** `nucleo-digital` §7.2 y `core/src/perturbacion.rs` l. 61-66:
   `Veredicto::Ambiguo` «se cae a la ocupacion —que si es un hecho binario y
   fiable—». Está implementado y con tests.

**Se queda**, acotado a los 16 jacks de la bahía (que es donde `voz-total` §0.1
ya lo había restringido), y **sin LED**: el sensado es un hecho que entra al
modelo, no una luz.

### D10 — `PATCH_SCAN` y la lista de conexiones del preset se degradan

El formato de disco de `preset.rs` no cambia y `PATCH_SCAN` se queda en el
protocolo. **Pero la v1 vendía la vuelta más barata de lo que es:** decía
«volver cuesta implementación, no formato», y lo que abarataba la vuelta era la
cadena de requisitos que E2 suelta —entradas de CV legibles por ADC, mux en el
módulo—. Con E2 sin resolver, el coste real de reabrir la topología por
inyección es **hierro**, no software. Queda escrito así y no al revés.

---

## 4. El código y los guiones

| Fichero | Qué se hace | Nota |
|---|---|---|
| `core/src/pinout.rs` l. 18-23 y 95 | Se **retira** el gpio 34; la cabecera deja de prometer que «el mecanismo de la cadena WS2812 lo decide su propio papel» — este es el papel y no hay cadena | El censo baja de 1 pin, no se queda igual |
| `core/src/protocolo.rs` l. 82-87, 189, 433-441 | **No se toca.** `Point`, `Rgb` y `T_POINT` se quedan exactamente como están | D4 · §6.1 |
| `core/src/servidor.rs` l. 453-456 y 1177-1195 | **No se toca.** La rama del `NoDisponible` y su razón esperan a §6.1 | D4 · §6.1 |
| `core/src/perturbacion.rs` l. 1-4 y 61-66 | Re-anclar: el módulo dice servir «la topologia del patch (§6.2)» y la atribución. Se queda **solo** la segunda | D9 |
| `core/tests/bahia.rs` l. 165-168 | El test cita el LED del jack. Se reescribe la cita al renglón | D8 |
| `hardware/02-midi-cv/micro_budget.py` l. 1138, 1146, 1260 | Se retira el término `+1 # WS2812` de `HUB_GPIO_VARIOS` y su comentario | — |
| `hardware/02-midi-cv/power_budget.py` | **Ver abajo. No es lo que la v1 mandaba** | — |
| `hardware/bus-board/ground_budget.py` l. 64-69 | `I_MASA_SAM17 = 0.050` A está justificado como «VCO (~5 mA) + holgura para **una fila de LED de panel**». Sin esa fila, el margen del presupuesto de 2 cents es otro | E10 |

**`power_budget.py`: las constantes no se ponen a cero.** La v1 lo mandaba «igual
que `BACKLIGHT_A`», y la analogía está invertida: `BACKLIGHT_A` tiene una
aserción que exige que valga **cero**; las de LED tienen dos que exigen lo
contrario.

| Línea | Aserto | Qué pasa con la constante a cero |
|---|---|---|
| 462 | `assert cabe_con_host < LED_A_CASO_REAL` | **Falla.** Exige que el conflicto exista |
| 472 | `assert cabe_solo >= LED_A_CASO_REAL` | Pasa trivialmente: la puerta deja de morder sin avisar |
| 488 | `assert LED_A_BLANCO_PLENO > TECHO_W_OPTIMISTA / V_RIEL` | **Falla** (`0.0 > 4.2` es falso) |

Y el aserto de la línea 462 lleva la instrucción que este papel tenía que haber
seguido, textual:

> Si esto es verdad, el #104 se puede cerrar -- pero revisa que numero
> cambio antes de creertelo.

**Lo que se manda entonces:** los tres asertos y la función `arbitro()` se
retiran **junto con su sujeto**, no se dejan verdes sobre un consumidor que ya no
existe. Es la misma regla que el fichero aplica: una puerta cuyo sujeto muere se
retira nombrándolo, no se relaja. El comentario de `arbitro()` avisa de que
«borrar la funcion seria borrar el nombre del arbitro» — y borrar el nombre del
árbitro es exactamente lo que este papel decide, así que la retirada va con la
cita de #104 al lado.

---

## 5. Los jacks se quedan, y cambian de oficio

**Dirección de Samuel:** «si siguen, necesitamos que el instrumento se pueda
conectar ampliamente con el exterior».

| | Antes | Ahora |
|---|---|---|
| Para qué existe un jack | Pachear entre módulos; el exterior era un caso más | **Hablar con lo de afuera** |
| El normalizado | Lo que evitaba 16 cables | Igual, y ahora es el modo normal |
| El pin `TN` | «En un instrumento patcheable **ese pin es la pieza central**» (`architecture-poly.md` l. 316-317) | **Se queda.** Es el mecanismo del normalizado |
| El nombre del jack | Se lo da el preset | **Aparcado** — §6.1 |

**Colisión que hereda §6.1:** `2026-08-22-modulo-3-vco-dieciseis-design.md`
§6.3, líneas 461-482, dice que **`TN` es o el camino del normalizado o el bit de
ocupación, no las dos cosas**, y de ahí cuelga una «decisión abierta 1» sobre qué
jack se compra. D9 mantiene vivo el sensado de ocupación en la bahía; §5 mantiene
vivo el `TN` como normalizado. **En los 16 jacks de la bahía las dos cosas se
piden a la vez**, así que esa decisión abierta pasa a tener que cerrarse — con
un jack de cuatro patillas si existe en el mismo formato mecánico, o eligiendo.
Fila mandada, E11.

---

## 6. Dos HUECOS con dueño

### 6.1 La cosa física cuyo significado cambia

**Es una sola pregunta, y la v2 la tenía partida en dos** (D4 y D6). Las juntó
Samuel al leerlas:

> «es mucho mas complejo que eso, van muchas cosas alli, no solamente los jacks
> de las voces. tambien van otros parametros»

De aquí sigue: si por la bahía no van solo señales de voz sino **parámetros**,
entonces un jack es una posición física cuyo significado cambia — igual que la
perilla que el agente quiere señalar. Las dos son el mismo acto: *una cosa
física del panel significa X ahora mismo, y algo tiene que decir qué.*

Voronov lo nombró en la junta y es el marco que este papel no supo usar:

| | Qué es | Se muda a una pantalla |
|---|---|---|
| **Estado** | Información cuyo significado no depende de dónde se muestre («este parámetro está anulado») | **Sí** |
| **Deixis** | Información cuyo significado **es** el sitio («*ese* pomo», «*ese* jack») | **No.** Una pantalla puede describir una ubicación; no puede estar en ella |

§2 de este papel partió la cadena en trabajos de estado y por eso el reparto
salió limpio: **el criterio no podía ver la otra clase.**

**Lo que esa conversación tiene que contestar:**

1. Qué va por los 16 jacks de la bahía además de las señales de voz, y si eso
   admite un nombre fijo.
2. Si el rótulo vive en la ventana de 68×16 del panel (que ya existe), en
   serigrafía, o en las dos.
3. Qué pasa con **señalar**: si el agente conserva un canal modelo→espacio, y
   con qué, ahora que las únicas luces que quedan son las 4 coronas de MACRO.
4. Si hay más deixis sin nombrar en el instrumento, porque el censo de §2 no
   podía verla.

**Lo que NO hay que decidir ahí:** nada de esto bloquea D1. El rótulo dinámico
tiene superficie (la ventana), señalar tiene su mensaje congelado sin tocar, y
las coronas sobreviven. La conversación decide qué se construye encima, no si la
cadena se va.

**Dueño:** el papel del panel, con el de la bahía.

### 6.2 La conexión amplia con el exterior

Requisito nuevo sin derivación. Este papel no lo diseña; lo acota.

1. **Qué clases de conexión y cuántas.** Hoy hay MIDI DIN in/out, clock/reset
   in/out y USB de doble rol por el cerebro, y 8 in + 8 out en la bahía. Lo que
   no está censado es cuánto CV y audio se quiere exponer **hacia afuera**.
2. **Dónde viven.** El estudio del valle (`panel-pantalla-al-centro` §5.1) sigue
   abierto y ahora tiene un cliente más grande. Cota que ya existe: el valle mide
   528,32 mm y sus ranuras son el 75 % de la salida de aire del case.
3. **Si el exterior devuelve el sensado por otra puerta.** Una entrada de CV
   externa legible por ADC es útil por razones que no son el patcheo guiado.
   D10 deja `PATCH_SCAN` esperándola, con su coste real declarado.

**Dueño:** el papel del panel y el censo de la Voz, conjuntamente.

---

## 7. Enmiendas mandadas, con rango de líneas

| # | Papel · rango | Tipo | Qué |
|---|---|---|---|
| E1 | `architecture-poly.md` l. 29-32 | Rewrite | El banner de vigencia declara vigente «el sistema de LED por jack que guía el patcheo (§7)». Es el índice de autoridad del documento |
| E2 | `architecture-poly.md` l. 160, 384-409, 421-446 | Remove | Fila `LED` de la tabla de señales; §7 soft-takeover con LED; «Los LEDs de panel» entera |
| E3 | `architecture-poly.md` l. 84-86 | Rewrite | «El panel entero, con sus LEDs direccionables, **es la pantalla de verdad**» |
| E4 | `architecture-compute.md` l. 180 y 279 | Rewrite / Remove | El patcheo guiado como **una de las cuatro razones de que exista el plugin VST/CLAP**; y la fila `Cadena WS2812` |
| E5 | **`nucleo-digital` §10, l. 1276-1299** | Rewrite | Las restricciones globales a los módulos 5, 6 y 7. **La más urgente: son placas sin dibujar** |
| E6 | `nucleo-digital` §6.2 (l. 837-885), §2.1 (l. 138-141), §4.1 (l. 409-416), §5 (l. 601), §7.2 (l. 1156-1161), §8 (l. 1195-1199) | Rewrite | El resto del papel. §7.2 **no se deroga**: es el cliente de la ocupación de D9 |
| E7 | **`nucleo-digital` §6.2 último párrafo, l. 882-885** | Rewrite | «el mux de perillas vive **en el módulo** y devuelve por el `MISO` del J2». **Hay que re-argumentarlo, no heredarlo.** Tiene gemelo en `architecture-poly.md` l. 387-393 y nieto en VCO-16 l. 562-566 |
| E8 | `voz-total` §0.1 (l. 71-77), §5.1 (l. 439-444), §5.3 (l. 501-505) | Rewrite | La definición de la bahía, según D6; el acuse, según D8 |
| E9 | `modulo-2-v2-cerebro` §7 criterio 2, §9 y §9.1 (l. 682-737) | Rewrite | **La retroiluminación de la pantalla es cliente del árbitro del #104 y criterio de compra de la pieza.** Cerrar #104 sin tocar esto mata un criterio de BOM en silencio |
| E10 | `ground_budget.py` l. 64-69 y `bus-board/notes/design-notes.md` §2 | Rewrite | `I_MASA_SAM17` y su justificación en prosa |
| E11 | VCO-16 §6.3, l. 461-482 | Rewrite | `TN` normalizado **o** bit de ocupación: la decisión abierta 1 pasa a tener que cerrarse (§5) |
| E12 | VCO-16 l. 93-102, 141-143, 172-174, 249-252, 1038 | Rewrite / Remove | Decisiones 7, 8, 9 y 20; la placa de panel; lo que cruza; el espacio de direcciones |
| E13 | `tiempo-musical` §2.2 (l. 98-101), §6.2 (l. 293-297), §6.3 | Rewrite | §6.2 usa «Un LED por perilla y un botón, no» para descartar cinco modos: **esa comparación se cae** |
| E14 | `panel-frontal-gramatica` §5 punto 5, §6 cond. 3, §7 opciones A/B | Sync | Ratificar D2 y D8; las coronas de D7 sobreviven pero cambian de mecanismo |
| E15 | `case-design` §12 (l. 861-871), `case-esqueleto-aluminio` §11, `case/cad/params.scad` l. 1474-1478 | Remove | El farol como alcance futuro, y el chaflán de las ranuras cuyo argumento era «hoy no hay iluminación interior» — pasa de «todavía no» a «nunca» |
| E16 | `fuente-v4-liston` §1 (l. 57-62), l. 97, 116-119 | Rewrite | «Con la cadena de LEDs al tope del #104 son 4,935 A» es **una de las dos razones de que la v4 exista**. **No se re-abre `PS6`**: el techo que manda es térmico (4,2 A) y D-F7 se firmó hoy |
| E17 | `modulo-2-v2-cerebro` §4.3 (l. 208-212), §6.4 (l. 371-375), §9.2 (l. 747-757) | Patch | Pull-down de arranque del dato, el cuarto canal del buffer, y el corte de masa del retorno de la cadena |
| E18 | `pantalla-motor` l. 274-277 | Rewrite | Hereda el requisito de D5, cuya premisa se derogó el 30-08 |

---

## 8. Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | E12 retira los 16 WS2812 de las placas de panel del VCO-16 antes de que nadie haya probado el soft-takeover en pantalla | **E12 no se ejecuta hasta que el kit de pruebas enseñe el renglón funcionando.** R1 manda sobre E12; la v1 no declaraba prelación y se contradecía |
| R2 | E7 se queda sin ejecutar y el repo hereda la colocación del mux sin razón | Se abre como issue con este papel de fuente. Tiene tres copias vivas (E7) |
| R3 | Cerrar #104 mata el criterio de compra de la retroiluminación | E9 lo mueve antes de cerrar |
| R4 | D6 se firma en «nombre fijo» y alguien lo lee como que el crosspoint se retira | El crosspoint no se toca: renombrar el jack y rutear por dentro son cosas distintas |
| R5 | Los tres asertos de `power_budget.py` se retiran y nadie nota que el riel se quedó sin puerta | La retirada va con la cita de #104 y el número que cambió, dentro del propio fichero |

---

## 9. Lo que este papel deja medido

| Magnitud | Antes | Después | Fuente |
|---|---|---|---|
| LED en la **cadena** | 160 (100 de panel + 60 del farol) | **0** | `power_budget.py` l. 154 |
| LED en el **instrumento** | 160 + coronas | **4 coronas de MACRO**, mecanismo por decidir (#297) | `panel-frontal-gramatica` l. 114, 251 |
| Corriente de la cadena, blanco pleno | 9,60 A | **0** | `power_budget.py` l. 158 |
| Corriente de la cadena, caso real | 2,04 A | **0** | `power_budget.py` l. 159 |
| Pines del cerebro para la cadena | 1 (exige canal de timer o MOSI) | **0** | `micro_budget.py` l. 1138, 1146 |
| Problemas del N657 sin PIO | 1 abierto | **0** | `pinout.rs` l. 18-23 |
| Techo del +5 V digital | **no cambia**: 4,2 A / 21 W, y es térmico | igual | `fuente-v4-liston` l. 97 |

---

## 10. La junta

| # | Quién | Hallazgo | Qué se hizo |
|---|---|---|---|
| S-1 | Serrano | D5 se apoya en un bloque tachado; su enmienda firmada del 30-08 está tres líneas más arriba | **D5 retirado entero** |
| S-2 | Serrano | Elisión `[...]` dentro de una cita, contra la regla del repo | La cita se retiró con su decisión |
| S-3 | Serrano | «un solo espacio de direcciones» atribuido a `nucleo-digital`; está en VCO-16 l. 1038 | Corregido en D1 y E12 |
| S-4 | Serrano | Poner las constantes de LED a cero **rompe** dos asertos | §4 reescrito: se retiran con su sujeto |
| S-5 | Serrano | La derogación llega a §6.2 y no a §10, que reimpone lo mismo a módulos sin dibujar | E5, marcada la más urgente |
| S-6 | Serrano | «Existía solo para» el árbitro es falso: la retroiluminación es cliente y criterio de BOM | E9 y R3 |
| S-7 | Serrano | E5 (v1) re-abría una decisión de fuente firmada el mismo día, con un número que nunca dimensionó nada | E16: el techo es térmico y no se re-abre |
| S-8 | Serrano | R1 y E4 (v1) se mandaban lo contrario sobre la misma pieza | R1 manda sobre E12, declarado |
| V-1 | Voronov | El patcheo interno lo mató el crosspoint el 23-08, no la decisión de hoy | §1 reescrita |
| V-2 | Voronov | Señalar es el primitivo, el patcheo guiado el derivado; la v1 los tenía al revés | D4 → §6.1 |
| V-3 | Voronov | El LED del jack **es el rótulo**; sin él quedan 16 agujeros idénticos | D6 → §6.1 |
| V-4 | Voronov | El testigo no puede atestiguar: lo que juzga un fallo no puede colgar del sujeto | D5, segunda razón |
| V-5 | Voronov | La cadena hacía **deixis**, no solo estado; una pantalla describe un sitio pero no está en él | Es el marco de §6.1 |
| V-6 | Voronov | El método del censo fue «leer a quien la encargó» y no «leer a quien se apoya» | §2 reescrita y el método declarado |
| H-1 | Halcyon | 6 enmiendas contra ~30 artefactos | §7, 18 filas con rango |
| H-2 | Halcyon | La ocupación tiene dos clientes que no son el patcheo guiado | D9 |
| H-3 | Halcyon | `I_MASA_SAM17` cuelga de «una fila de LED de panel» | E10 |
| H-4 | Halcyon | El acuse de `diferir` tiene test verde citando el LED del jack | D8 |
| H-5 | Halcyon | Las coronas de MACRO son otra familia | D7, y #297 encoge |

---

## 11. Lo leído

`voz-total` §0.1, §0.2 ley 1 (l. 106-111), §5.1 (l. 439-444), §5.3 ·
`architecture-poly.md` §6 (l. 292-317), §7, l. 421-446, l. 160 ·
`nucleo-digital` §2.1 (l. 138-141), §6.2 (l. 835-885), §7.2, §10 (l. 1276-1299) ·
`panel-pantalla-al-centro` §4 **completo, l. 138-190, incluida la enmienda del
30-08** · `panel-frontal-gramatica` l. 108-121, l. 200-261 ·
`modulo-2-v2-cerebro` §7 (l. 592-613), §9.1 ·
`vco-orquestacion` §2.3 (derogada el 27-08) · `fuente-v4-liston` l. 97, 158-167 ·
`power_budget.py` l. 144-161 **y l. 445-496** · `micro_budget.py` l. 288-301,
l. 1130-1150 · `protocolo.rs` l. 76-107 · `preset.rs` · `pinout.rs` ·
issues #42, #103, #104, #151, #297

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_015irzUk2ubW8HPRrtKyjLxb
