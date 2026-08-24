# La gramática del panel: la cara es lienzo libre, y se reparte aquí

**Estado: PROPUESTA, versión 2 — reescrita tras la junta del 2026-08-23**
(Serrano, Voronov, Halberg y Elke Brandt; dictámenes condensados en §10).
No toca cobre, no toca cajón, no toca spec. El acta madre dejó dicho: «El
reparto de anchos de panel con los conectores ya mudados […] Cada uno va en
su propio pase». Este papel es ese pase.

**Principios rectores, dictados por Samuel el 2026-08-23, citas exactas:**

1. *«no hay nada precioso en un analogo que sentirlo, tocar potenciometros,
   botones, slides»* — el panel se diseña desde la mano, no desde la placa.
2. *«sobrio y aleman. porque ese es el plan»* — la imagen de KONDOR. La
   referencia de puesta en escena: Soulwax — *«sus sintes parece que tienen
   solo cuatro perillas gigantes y ya eso es todo. y lo que pasa por dentro
   de esos cajones es una locura»*. La cara calla, el cajón ruge. Un
   instrumento *«que no pretenda ser mas que los demas porque simplemente no
   lo necesita, ya lo sabe»*.
3. La tesis del proyecto: *«es el primer sintetizador hecho para que un
   agente lo manipule por completo»*.
4. La premisa de comportamiento: *«todo comportamiento del sintetizador es
   configurable […] viene resuelto por modos de ejecucion, modos de live
   performance, modos de exploracion»*. Qué pasa cuando el agente ejecuta y
   la mano toca no es una ley única: es política del **modo** activo. El
   precedente ya existe en la casa: la política de drones de la bahía
   (`diferir`/`forzar`) es configurable por preset desde el spec madre §5.3.

Y la marca entra aquí: el plan del case del día 21 dejó KONDOR «para más
adelante»; más adelante es este panel. Es el primer instrumento de la casa.

---

## 1. Qué decide y qué NO

**Decide:** la gramática — qué secciones tiene la cara, en qué orden, en qué
fila vive cada cosa, qué controles existen, y qué *requisitos* debe cumplir
el comportamiento (los mecanismos exactos se diseñan donde manda el núcleo).

**NO decide:** la piel (color, tipografía, marca — su pase, con renders), el
cajón y la mudanza de conectores (#167), quién shiftea el crosspoint (#171),
la lista final de perillas (censo), ni los cambios de núcleo que este papel
exige — esos se ACTAN aquí como requisito y se diseñan en su propia mesa
(§11).

## 2. Lo que ya está legislado, y este papel hereda

| Ley | Fuente |
|---|---|
| «El panel físico es la superficie de **interpretación**: perillas-sensor, LEDs, bahía» | voz-total §0.2 |
| «Las perillas son sensores, mandan números, y los números viajan por cable plano sin ensuciarse» | acta E-2 |
| **La mano gana por parámetro** (gesto físico → `ANULADO`), `REACTIVAR` lo devuelve | voz-total §0.2, ley de capas 1 |
| El panel de mandos es módulo clase **referente** (posee vínculos, no parámetros) | voz-total §0.3, cambio 15 |
| La bahía: 8 entradas + 8 salidas Thonkiconn, LED por jack, «el jack es un nombre que le da el preset» | voz-total §5.1 |
| Conmutación de bahía: imagen sombra, barrera de silencio, política de drones por preset | voz-total §5.3 |
| Fila A = UN módulo (Voz + bahía, una cara continua) | acta E-3, E-2 |
| Fila B = rack Eurorack de verdad, con regleta e invitados | acta E-4, #169 |
| El mixer y la salida estéreo viven dentro del módulo de Voz | acta E-5, E-6 |
| Cabeza local del cerebro: pantalla SPI 2,8" + encoder con pulsador | cerebro-v2 §5.2 |
| Los paneles del case son PCB de aluminio y **«cada panel se bonda por su cuenta, sin excepción»** | case/README.md §13 |

La última fila la subió la junta (S-1): cualquier propuesta de material de
cara **colisiona con ley escrita del case** y se resuelve en voz alta, no
por omisión.

## 3. El descubrimiento que libera el diseño — con su corrección

De «las perillas son sensores» se sigue que **la posición de una perilla no
está atada a ninguna placa**: manda un número por cable plano y puede vivir
donde la mano lo pida. La cara es lienzo libre **para los controles**.

La corrección de la junta (S-1, H-2, E-C5): lo que SÍ ancla son (a) los 16
jacks de la bahía (audio ±12 V, tramos cortos sobre su placa), (b) los
conectores del mundo (ya rumbo atrás, #167), y (c) **cualquier pantalla**:
un rectángulo rígido cuyo cuerpo compite por el mismo fondo que los cuerpos
de los potes. El viejo «mandos 120 mm en fila B» de §8 del spec sigue
derogado; la libertad es real, pero no absoluta.

## 4. El reparto propuesto (v2, con los milímetros de Elke Brandt)

Números CITADOS de `params.scad` y `voz_total_budget.py`; el resto ESTIMADO
con su medición nombrada. Detalle completo en el dictamen de Elke (§10.4).

### Fila A — panel de 83 HP = 421,64 × 128,5 mm

El PCB cierra en 421,5 mm; el panel se redondea al múltiplo de HP: **83 HP**.
No se dibuja más ancho a propósito: el factor de ruteo ×2,2 es «el número
menos medido de todo el diseño» y la reserva de fila es suya. Si el censo
pide más perillas, el panel crece hacia la izquierda; la bahía no se mueve.

De izquierda a derecha:

| Zona | Contenido | Números que mandan |
|---|---|---|
| **MACROS** | 4 potes gigantes en cuadro 2×2, corona de LEDs por cap (valor); el nombre vive en el renglón | Cap ≤ Ø38: el 2×2 cabe en 91 mm. **De Ø44 en adelante no hay cuadro**: fila de 4 = 224 mm = cinco columnas de perillas curadas menos. Se decide con dos caps en un tablón (§11.3) |
| **PERILLAS** | 16 potes curados, cap Ø20, 8×2, paso 28×34 mm | 8 mm de aire entre caps (mínimo de pinza); serigrafía fija |
| **RENGLÓN** | UNA ventana de 216×18 mm: nombre+valor del último parámetro tocado (alineado con su perilla), las 16 voces respirando, y los acuses del modo MATRIZ | Sustituye a «una ventana por perilla» (dieciséis alineaciones y dieciséis fugas: The Cut de Elke). No rompe B2: no es una segunda cabeza, es una etiqueta que cambia |
| **FUENTES** | 1 botón MATRIZ + **10** botones de fuente Ø12, paso 18 | 12 no caben sin pisado de yema o +36 mm de panel: el precio quedó dicho |
| **BAHÍA** | 16 Thonkiconn en **4×4 a paso 17 mm, pegada al canto derecho** + ventana propia de 68×16 (nombre de cada jack) | El 2×8 pide 136 mm > los 100 presupuestados (colisión E-C6). El paso 17 es acceso de llave de vaso. Al canto: el mazo de cables se barre al costado y **no tapa el valle de ventilación** (con el valle tapado, el salto térmico pasa de 6,6 a 8,8 K) |

Densidad resultante: 68 % — los separadores hacen de gramática.

### Fila B — 104 HP repartidos

| Zona | HP | Contenido |
|---|---|---|
| **CABEZA** | 30 | pantalla 2,8" (**IPS obligatoria**: a 55° una TN invierte) + encoder + botones de programa (E1) + TUNE (C6) |
| **INVITADOS** | **62** | riel abierto. *El plan v1 decía 66: 4 HP son el precio del drapeado de la bahía, dicho antes del montaje y no el día del montaje* |
| **SOMBRA** | 12 | panel ciego bajo la bahía — donde cae lo que aun así cuelgue |

### La fijación, que no es detalle

- **Acrílico: 5 mm mínimo** (a 3 mm, alguien apoyándose = 18 MPa: fluencia).
- **5 tornillos M3 por riel** (10 en total): flecha de 0,21 mm al tirar un
  cable. Con los 4 de esquina de la plantilla actual: 13,9 mm — una tapa.
- **Rebaje trasero fresado Ø12×3 mm en cada pote y cada jack**: un
  Thonkiconn tiene 4,7 mm de casquillo — **en 5 mm no rosca** (−0,3 mm).
  El proceso ya es CNC; el rebaje es tiempo de máquina, no utillaje.
- Requisito para las muestras de A1: casquillo ≥8,5 mm o rebaje; eje ≥18 mm.

## 5. El comportamiento: los modos, y el salto suave enmendado

### 5.1 La premisa de modos (principio 4)

Qué puede escribir la mano y qué el agente **no es una constante: es el modo
de ejecución activo** — live performance, ejecución, exploración, los que el
censo declare. Cada modo es una **política nombrada de arbitraje sobre
escrituras con autor**. Consecuencia dura, dicha por la junta entera y
asumida: **esto exige que el modelo sepa quién escribe**. Hoy un mensaje
lleva (parámetro, valor) y ningún «quién»; la ley de capas es, en palabras
de Voronov, «una cortesía que el agente puede retirar». La autoría como
objeto de primera clase es un **cambio de núcleo, prerrequisito de este
papel**, y se acta en §11.1 — junto con la regla de quién puede cambiar el
modo mismo (propuesta por defecto: cambiar de modo es gesto físico o
consentido; POR-DECIDIR con el núcleo).

> **Estado del prerrequisito, 2026-08-24** (PR #181). Aterrizó **la mitad**.
> La autoría ya existe: `Puerta` —Mano / Usb / Inalambrica / Interno— y toda
> escritura llega estampada. Y salió más barata de lo que este papel temía:
> **cuesta cero bytes en la trama**, porque la puerta no viaja en el mensaje,
> la estampa el transporte. Un mensaje que declara su propio origen puede
> mentir gratis; lo único honesto es quién lo recibió.
>
> **El modo como objeto NO aterrizó, y no por falta de tiempo.** El mecanismo
> que el núcleo proponía para sostenerlo —«el sello se arrastra», que la
> autoría viajara a las escrituras derivadas— quedó DEROGADO en su v3: si la
> autoría se arrastra, una escritura automática termina cargando la autoridad
> de la mano, y la ley de capas 1 se vuelve inaplicable contra sí misma.
> El modo necesita otro mecanismo. Sigue en #177.

### 5.2 El salto suave, enmendado en voz alta

**Lo que Samuel firmó y se sostiene:** al tocar una perilla el valor
*planea* hasta ella — sin zona muerta de captura, sin accidente — y **cada
parámetro declara su forma de aterrizar**, ahora bajo el principio 4:
la clase de aterrizaje es configurable, por parámetro y por modo.

**Lo que la junta tumbó y se deroga:** la implementación citada. `rampa.rs`
trabaja en **pulsos musicales cuantizados** (el mismo planeo duraría 3× más
a 60 BPM que a 180 y puede arrancar compases tarde), R-M1 prohíbe al módulo
interpolar flujos del cerebro, la entrega J2 de parámetros no-tono va a
100 Hz — tasa que el propio spec declaró «se oyen como escalones» — y
`MAX_RAMPAS = 16` no aguanta ni una automatización de programa (16 voces =
16 ranuras). *Nadie leyó el archivo que citó* (H-1); queda dicho.

**Los requisitos que el mecanismo nuevo debe cumplir** (diseño en la mesa
del núcleo, §11.1):

1. Motor de aterrizaje en **milisegundos de pared**, separado del motor de
   automatización musical.
2. **Umbral de gesto en LSB con histéresis, declarado y aseverado** — «sin
   zona muerta» se refiere a la captura, no al ruido: sin umbral, 1 LSB de
   ruido de ADC en 45 potes le quita el instrumento al agente en silencio
   (S-4, H-1).
3. Política de blanco móvil (la perilla sigue girando), de recall a mitad
   de rampa, y de qué produce `ANULADO` — **por modo** (principio 4).
4. **Cota mano→DAC declarada en ms y aseverada por guion.** Hoy no existe
   ninguna en el repo; «inmediato» sin número no es falsable.
5. El estado `ANULADO` necesita **superficie física**: A3 mató el LED por
   perilla y el spec del tiempo (§6.3) le tenía asignada esa segunda
   función. El renglón lo repone: parámetro anulado que se toca → el
   renglón lo dice. La cuenta agregada (`ID_ANULADOS`) no basta: el
   descriptor debe publicar **cuáles** (cambio de núcleo, §11.1).

## 6. La bahía y el modo MATRIZ

**El gesto se sostiene:** botón MATRIZ (modo visible a gritos — la cara
entera cambia de estado), fuentes en su fila, y el destino y la cantidad
son **la perilla de siempre del destino**. El mismo gesto asigna jacks. La
cabeza queda como camino completo. La sección FM dedicada **muere** (The
Cut de Elke): MATRIZ da el mismo gesto sin gastar un mm².

**Registro honesto de C2:** esta decisión ES la respuesta a C2 («la matriz
FM, la gorda»): la matriz no gana sección propia en la cara; se toca por
MATRIZ y por carcasas. La fila de 10 fuentes **no acota la matriz** (que
sigue ilimitada por dentro, §5.2 del spec): acota qué fuentes tienen botón
directo. El criterio de cuáles, y si la fila es fija o por preset, queda
POR-DECIDIR con el censo (S-13).

**Las condiciones de la junta para que MATRIZ corra** (H-3):

1. **Épocas en las muestras**: cada lote de perilla lleva número de
   generación de modo; un lote rancio (muestreado en un modo, entregado en
   otro) se descarta. Sin esto, salir de MATRIZ con una vuelta en vuelo
   escribe el corte de verdad en 16 voces.
2. **`ANULADO` con tipo de arista**: la ley de capas promete «ese parámetro
   o ruta» y la mitad «ruta» no existe en el modelo (cambio de núcleo,
   §11.1).
3. **Acuse local en el renglón**: bajo `diferir` con un drone sonando, el
   gesto produce «ruta pendiente» — indefinidamente y por diseño. Eso se
   muestra donde ocurrió el gesto, no solo en el LED del jack; y los
   commits pendientes sobre el mismo cruce **se fusionan** (el último
   gana), no se encolan en ráfaga.
4. El estado «pendiente» sobrevive como estado del relator (ya legislado,
   spec §5.3); un reset lo pierde y **lo dice** al volver.

**Sub-decisión abierta:** fuentes con botones físicos vs zonas táctiles
tras el acrílico. La medición de §11.3 la cierra; si el capacitivo no
cruza el espesor real (rebaje a 2,5 mm incluido), son botones físicos.

## 7. El frente: material y frente muerto, las dos opciones

La idea de Samuel («¿y si el panel es una pantalla de la que salen las
perillas?») traducida a lo fabricable sigue viva, **acotada por la junta**:
no dieciséis ventanas — UNA de renglón, una de bahía, y cuatro coronas de
LED. Pero el material de la cara colisiona con ley del case (§2, última
fila) y se decide en voz alta:

| | **Opción A: aluminio con ventanas** | **Opción B: acrílico entero (5 mm)** |
|---|---|---|
| Qué es | Panel PCB de aluminio (como legisla el case) con dos recortes: renglón 216×18 y bahía 68×16, cubiertos con ahumado; coronas de LED por luz pasante | La cara completa en acrílico ahumado; pantallas detrás; impresión negra en segunda superficie como máscara |
| Bonding/EMC | **Cumple la ley del case tal cual**; blindaje sobre 16 voces donde 1 mV = 3,6 cents | Necesita **excepción escrita** a «sin excepción» + camino de blindaje sustituto (plano de masa en placas + bonding de casquillos) — no es firma de este papel |
| Frente muerto | Parcial: las ventanas son frente muerto; el resto, serigrafía fija | Total: apagado, losa muda |
| Riesgos propios | Menos: la ley física de Elke («donde imprimes no iluminas») aplica solo a las ventanas | Guía de onda (la luz viaja por el canto y sale por cada agujero: máscara + chimeneas obligatorias), fuga por 20 taladros |
| Común a ambas | **Acabado mate en la cara frontal, obligatorio**: la fila A está a 45° apuntando a las lámparas del techo; con brillo, el reflejo especular mata la lectura de día sea cual sea la transmitancia | |

Recomendación de este papel: **empezar la medición de §11.3 con las dos**;
la opción A es la que no le pide permiso a nadie. La B es más KONDOR y más
cara de conseguir en ley y en física. Decide Samuel con el retazo en la
mano.

**Quién maneja el frente y el escaneo — la salida arquitectónica (§11.2):**
el cerebro está cerrado por escrito (2 GPIO libres, dos SPI gastados, «no
admite un cliente más» en J2 desde su spec §7… pero **E-3 liberó una
ranura de J2** al fundir la bahía en la Voz). Propuesta: **el panel de
mandos se vuelve módulo de verdad** — clase referente, su propia bajada de
J2 en la ranura liberada, su micro, su escaneo de 45 potes (3 muxes 16:1),
su renglón, sus coronas y su presupuesto de +5 V. Un dominio de fallo
propio: pantalla muerta ≠ perillas muertas, y el camino nota→VCA del
cerebro ni se entera.

## 8. Los números que vigilan — corregidos por la junta

- `voz_total_budget.py` presupuesta **PCB, no panel**: falta la línea
  `ANCHO_PANEL_A` (83 HP) y falta modelar el fondo de los potes — el
  cuerpo (~10 mm ESTIMADO) entra en los 10,6 de hueco con **0,6 mm** de
  margen, y el fondo de fila A está al 100 % (E-C5). Se amplía el guion al
  aprobar la gramática.
- **La línea de LEDs del ±12 V no existe**: el guion dice textual «LED NO
  cargan este presupuesto: cuelgan de otra fuente». Toda la luz nueva
  (coronas, jacks, renglón, botones) carga al **+5 V de la IRM-15-5, cuya
  suma ya no cierra hoy (#151) y no tiene guion**. El presupuesto de +5 V
  es prerrequisito bloqueante de este plan (§11.4). *El plan v1 citó tres
  veces un presupuesto fantasma; queda dicho.*
- La reserva de invitados de E-4 es **230–300 mA/riel a escribir**, no los
  160 sobrantes de hoy. Los 62 HP se publican con esa reserva, no contra
  el sobrante (S-9).
- Tres presupuestos declarados bloqueantes en el spec madre **no existen
  como guion** (`ataque`, `cal_filtro`, `arranque`), ni `trama_j2_budget.py`
  ni `check_pinout.py` — y `pinout.rs` describe una cabeza que ya no existe
  (H-6). Se abren como issues al mergear (§11.4).

## 9. El inventario de decisiones — estado tras la junta

### Firmadas por Samuel

| # | Decisión | Nota de junta |
|---|---|---|
| A1 | Potes con tope, de los mejores; pieza exacta al BOM con muestras | Requisito nuevo: casquillo ≥8,5 mm o rebaje trasero; eje ≥18 mm (§4) |
| A2 | Puras perillas; sin sliders ni motores | — |
| A3 | **Salto suave: la sensación firmada se sostiene; el mecanismo citado se deroga y se re-diseña con los requisitos de §5.2** | Enmienda de junta, en voz alta |
| A4 | Discretos: botón ciclador + LEDs; on/off con botón | — |
| B2 | Una sola cabeza | El renglón no la contradice: es etiqueta, no cabeza. La enmienda se re-firma contra sus TRES motivos (sobriedad ✓ apagado; consumo → al presupuesto de +5 V de §11.4; competencia visual → UNA ventana, no N) (S-14) |
| B4 | Luz sobria | — |
| **Principio 4** | **Todo comportamiento es configurable, por modos de ejecución** | Exige autoría en el núcleo (§5.1, §11.1) |

### El paquete — FIRMADO por Samuel el 2026-08-23 («dale pues»)

Cara curada (16+4) · frente muerto acotado (renglón + ventana bahía +
coronas) · modo MATRIZ con sus 4 condiciones · 83 HP / 62 HP · bahía 4×4
al canto. **Son un paquete porque se sostienen entre sí** (la macro sin
renglón no tiene nombre; MATRIZ sin frente no tiene acuse). La firma es de
dirección, con las dos puertas que este mismo papel legisla intactas:

- Las **mediciones de §11.3 siguen siendo puerta del congelado**: si el
  retazo mata el frente muerto, el paquete vuelve a la mesa y la cara
  curada se re-propone con serigrafía fija y macros no reasignables.
- El **material (opción A aluminio-con-ventanas vs B acrílico entero)
  queda sin firmar**: se decide con el retazo en la mano, porque la B
  además pide la excepción de bonding que no es de esta mesa.

### Aún no tocadas

A5 (shift: **sigue siendo recomendación, no ley** — MATRIZ se defiende
como modo visible, no contra A5; S-8), A6, B1 (de facto favorable), B3
(resuelta de facto: las voces se dibujan en el renglón, cuestan cero), C1
(la firma implícita del reparto va en el paquete), C3, C4, C5 (auriculares:
**fuera de la fila A** — The Cut; su casa la decide #167), C6 (TUNE va en
la cabeza, §4), D1 (en paquete: 4×4 al canto), D2, D3, E1, E2, F1, F2, y
el botón PANEL (aparcado en E).

## 10. La junta del 2026-08-23 — dictámenes condensados

Los cuatro textos completos quedan en la sesión; aquí lo que cambió el
papel. IDs: S=Serrano, V=Voronov, H=Halberg, E-C=colisiones de Elke.

**Voronov (ontología):** el modelo no tiene eje de autoría — `Set(id,
valor)` sin «quién»; la ley de capas es inexpresable; `REACTIVAR` es de
cualquier cliente, así que el agente puede deshacer la captura de la mano
(V-II). La perilla «por programa» no tiene referente (16 instancias; el
gesto mínimo desborda el buzón de reconciliación 8×) (V-IV). MATRIZ cambia
el codominio del vínculo (parámetro↔arista) sin declarar el tipo (V-V). La
macro es un vínculo cuyo destino es dato: tipo reflexivo sin declarar, y
la dormancia muere en la frontera del referente — V2-III un piso más
arriba (V-VI). El frente no puede ser autoridad y vista en el mismo plano
sin un tercer objeto que diga cuál manda: la autoría (V-VIII). *Reencuadre:
este es el primer papel que exige que el modelo distinga quién escribe.*

**Serrano (clínica, 7 BLOCKERS):** cara de acrílico vs aluminio bondado
del case, sin derogación declarada (S-1). Pantallas sin dueño, bus ni
pines (S-2). Presupuesto de LEDs citado al revés; +5 V sin guion y sin
cerrar (#151) (S-3). A3 sin máquina de estados ni umbral — «sin zona
muerta» como virtud es la respuesta más peligrosa posible (S-4). `ANULADO`
sin disparador y `REACTIVAR` sin gesto (S-5). Reasignación (macros/MATRIZ)
deja posiciones heredadas: el salto que descartamos, de vuelta por la
puerta de atrás (S-6 — lo cubren las épocas y la política de blanco de
§5.2/§6). Votación acoplada presentada como independiente (S-7). C2 había
desaparecido del acta (S-8; registrada en §6). 66 HP sobre reserva
insuficiente y ancho de cabeza caduco (S-9). §5/§6 del plan v1
contradecían al §9 (S-15; esta v2 los reescribe).

**Halberg (runtime): NO-CORRE-ASÍ en los cuatro frentes** como estaban
escritos. `rampa.rs` en pulsos cuantizados vs «decenas de ms»; R-M1 cierra
el módulo; 100 Hz de J2 para no-tono «se oyen como escalones»; `MAX_RAMPAS
= 16` vs 45 potes ×16 voces (H-1). Frente muerto sin tercer SPI, con 2
GPIO y sobre un riel que no cierra (H-2). MATRIZ: race de interpretación
sin épocas; `ANULADO` sin tipo para aristas; gesto mudo bajo `diferir`
(H-3). Escaneo sin micro: el sitio legislado murió con los módulos 5-7 y
los tres candidatos están cerrados por escrito (H-4) — de ahí §7/§11.2.
Además: hoy **ninguna carcasa puede renderizar el módulo** (536>512,
descriptor 107×, respuestas 130×) — el frente construye sobre un contrato
roto que #172 ya rastrea; y `pinout.rs` contradice a su spec (H-6). *«El
runtime no discute con las actas. Mide los pulsos, cuenta los pines y suma
los vatios.»*

**Elke Brandt (materia): fabricable con cuatro condiciones** — 5 mm + 10
tornillos; rebaje trasero Ø12×3 (un Thonkiconn NO rosca en 5 mm); bahía
4×4 a paso 17 al canto (2×8 no cabe y tapa la ventilación: ΔT 6,6→8,8 K);
mate obligatorio a 45°. El bonding no es su firma: o excepción escrita o
la cara no es acrílico entero (§7). El cap de las macros decide la cara:
hasta Ø38 hay cuadro 2×2; de Ø44 en adelante, fila de 224 mm y la cara
curada baja a ~6 perillas (§11.3). Diez colisiones E-C1..E-C10 con
presupuestos y ficheros, incluida una preexistente: `params.scad` dice
panel 1,6 mm y `voz_total_budget.py` reserva 5,0 — **dos ficheros del repo
se contradicen hoy, antes de este papel** (E-C1).

## 11. El camino

1. **Acta de autoría y modos, al núcleo.** Autoría en cada escritura; el
   modo como política nombrada de arbitraje; `ANULADO`/`REACTIVAR` por
   autor y con tipo de arista; publicación de CUÁLES parámetros están
   anulados (no solo la cuenta); quién cambia el modo. El motor de
   aterrizaje de §5.2 con sus requisitos. Se abre como issue con la
   evidencia de la junta al mergear este PR; se diseña con #172 (los
   techos del modelo: 536>512, descriptor, buzón — sin eso ninguna carcasa
   ni frente renderiza).
2. **El módulo de mandos, de verdad.** Clase referente con la bajada J2
   que E-3 liberó: micro propio, escaneo, renglón, coronas, +5 V. Su spec
   corto es el siguiente papel técnico de esta serie.
3. **Las tres mediciones de Elke, antes de congelar** (cada una cambia la
   gramática si sale mal): (a) retazo del ahumado real a 45° con luz de
   techo, brillante vs mate, 5 mm y rebajado — criterio de aprobado
   ESCRITO antes de medir; (b) capacitivo tras 5 mm y tras rebaje a
   2,5 mm — si falla, botones físicos; (c) dos caps de macro en un tablón
   a 53 y 60 mm de paso — decide Ø38 vs Ø44+ y con ello cuántas perillas
   curadas existen.
4. **Deudas de guion que este papel deja abiertas** (issues al mergear):
   presupuesto de +5 V (no existe; #151 sigue sin cerrar), `ANCHO_PANEL_A`
   y fondo de potes en `voz_total_budget.py`, reserva de invitados
   230–300 mA escrita en `consumo_total_budget.py`, los tres presupuestos
   bloqueantes fantasma del spec madre, `trama_j2_budget.py`,
   `check_pinout.py`, y la contradicción E-C1 (`t_panel` 1,6 vs 5,0).

Aprobado el paquete: el censo produce la lista de perillas; el pase de
piel viste la cara; #167 muda los conectores con la gramática congelada.
