# La pantalla del motor — 7" táctil al LTDC del N657

**Fecha:** 2026-08-26 (noche)
**Estado:** diseño aprobado por Samuel en conversación (acta: «Vamos con A»);
el censo de pines ya corrió con la pantalla sentada y dio VERDE
(`hardware/02-midi-cv/micro_budget.py`).
**Sujeto:** una pantalla táctil de 7 pulgadas, 800×480, colgada del módulo
del motor digital (STM32N657). Este papel decide la arquitectura y deja
mandados los presupuestos; **no** nombra piezas (R-M3) ni decide qué dibuja
la interfaz.

---

## 0. El acta

Samuel preguntó si el instrumento podía llevar una táctil de 7" (propuso el
*HDMI 7" 800x480 Display Backpack - With Touchscreen* de Adafruit), pidió la
propuesta completa («si por favor, vamos con todo») y, con los tres caminos
y sus números en la mano, decidió: **«Vamos con A»** — la pantalla directa
al LTDC del N657, aceptando la mudanza de dos capturas que se detalla en §2.

**El backpack HDMI queda descartado en cualquier camino.** Ese producto
existe para computadoras con salida HDMI: por dentro es un panel TTL crudo
más un TFP401 cuyo único trabajo es decodificar HDMI **de vuelta** a RGB
paralelo (página del producto Adafruit #2407). El N657 habla RGB paralelo
nativo por su LTDC (DS14791 Rev 2, §3.28-3.29): comprar ese backpack sería
poner un codificador de HDMI en nuestra placa para alimentar un
decodificador que lo deshace a diez centímetros. Además su táctil sale como
mouse USB, que obligaría a un stack de USB host para leer un dedo. La pieza
correcta es el **panel crudo** de la misma clase (7", 800×480, TTL RGB de
24 bits, 40 pines) con **táctil capacitivo por I2C**.

---

## 1. Por qué cuelga del motor y no de un micro propio

El papel del cerebro ya contestó esta petición una vez (spec
2026-08-21-modulo-2-v2-cerebro §7): la 7" no entra en el módulo 2 —
panel, corriente y memoria, tres razones y cada una bastaba — y «si algún
día se quiere una pantalla grande, no va en este módulo. Va en el case como
otro cliente del protocolo, con su propio micro y su propia alimentación».

Esa respuesta se escribió cuando ningún chip de la casa podía manejar
800×480. Hoy sí hay uno, y ya está comprado en papel: el N657 trae **LTDC**
(composición de 2 capas, salida RGB paralela de 24 bits, techo 150 Mpx/s —
DS §3.28) y la GPU **NeoChrom** (GPU2D, DS §3.30), los dos con DMA propio.
Sostener un segundo chip clase-N6 solo para pantalla sería la enfermedad
del #201 («dos motores»), ya descartada por acta en la spec del motor §13.
Así que la prescripción del cerebro se ejecuta a medias, y a propósito:

- **«No va en el módulo 2»** — sigue en pie. La 2,8" SPI del cerebro no
  cambia, y esta pantalla no toca esa placa.
- **«Con su propio micro»** — superada: el micro es el N657 del motor, que
  no existía cuando se escribió el párrafo. La nota fechada en cerebro §7
  lo deja dicho.
- **«Con su propia alimentación»** — sigue en pie, ver §6.

**Por qué A le ganó a B, en números** (la junta cobró que el caso vivía
solo en la conversación): el camino B es un controlador con framebuffer
propio (clase RA8875, 800×480 por SPI, ~6 pines, cero SRAM del motor, cero
caudal AXI, capturas intactas) — el mismo patrón que la casa eligió para la
2,8" del cerebro. Lo que B **no** puede dar: un SPI a ~50 MHz mueve
~6 MB/s crudos, y un cuadro de 800×480 a 16 bits pesa 768 000 B — es decir
**~8 cuadros/s de pantalla completa** (clase; aritmética, no hoja). Sirve
para menús; no para visualizar granos, capas y waveforms en movimiento,
que es exactamente lo que el acta pide. A entrega 24 bits, 2 capas
compuestas en hardware y 60 cuadros/s por DMA. Y el criterio 1 del cerebro
(«el núcleo de tiempo real no puede estar refrescando píxeles mientras
cronometra») — que es el argumento DE B — se rebate aquí de frente: **el
LTDC refresca por DMA, no con la CPU**; su costo real no es ciclos de
procesador sino contención de AXI, y ese costo tiene fila y criterio de
cierre (riesgo 5 del motor §11, soak con el refresco activo).

**El camino B queda de suplente declarado, con puerta y no con retórica**
(la junta cobró que «se cae a B si un presupuesto se pone rojo» era
infalsificable con los presupuestos aún sin correr): **el conector del
panel no se dibuja hasta que el censo de SRAM (`sram_budget.py`) esté
verde y el soak de contención con el refresco LTDC activo (riesgo 5 del
motor §11) haya corrido.** — la junta de la tanda 2 corrigió la redacción
anterior, que apuntaba a «la fila LTDC de `carga_motor`»: esa fila existe
y ya está verde, pero mide el **pegamento de CPU** (componer la UI), no la
contención de AXI que esta misma spec llama el costo real del camino A.
Una puerta tiene que nombrar lo que de verdad la cierra.

> **Estado 2026-08-26 (noche, tanda 2 del #214): la puerta está CERRADA y
> con hallazgo.** Los tres guiones ya existen y corrieron. `carga_motor`
> sale verde y dice que la CPU compra 129-289 granos según el motor base.
> `psram_budget` cierra su caudal y dice que el bus compra 2 500 granos a
> velocidad ×1 y 625 a ×4 — el cuello es la CPU, no el bus, y el
> framebuffer mudado a PSRAM cabría de sobra (46-69 MB/s de 240
> disponibles). **`sram_budget` sale HUECO**, y su
> hallazgo cambia el foco: apilando el peor caso de los ESTIMADO, lo fijo
> se come 3,2 de los 4,2 MB y **no cierra ni sin pantalla** — o sea que el
> dato que decide esta puerta no es el framebuffer sino **el tamaño del
> binario, hoy sin medir**. Las tres salidas (medir en bring-up / mudar el
> framebuffer a la PSRAM / camino B) están en el guion; **ninguna se elige
> sin acta de Samuel**. La referencia que justifica
la puerta: un doble buffer RGB888 son 2 304 000 B — **~55 % de los 4,2 MB**
antes de contar binario, tablas residentes y buffers de sample. El rojo no
es hipótesis remota, y caerse a B después de dibujar es un respin. El
repliegue intermedio (bus de 16 bits, RGB565: 20 pines) está documentado
en `micro_budget.py`.

---

## 2. El precio en pines: la mudanza de dos capturas

El censo con la pantalla sentada demostró que **el RGB paralelo era
imposible con las 16 capturas tal como estaban** — y no por falta de
búsqueda, por aritmética de pin único:

| Choque | La cuenta |
|---|---|
| `LCD_G2` | un solo pin en todo el DS: **PA1** — que era también el único pin de `TIM5_CH2`. Dos demandas, un pin: no existe reparto. |
| `LCD_G6` | un solo pin: **PB11** — adonde la cadena `TIM5_CH4`→PF6 forzaba a `TIM2_CH4`. |

La salida no fue recortarle color al panel (con G2 y G6 muertos, el verde
quedaba en 1 bit): fue **mudar esas dos capturas a TIM1**, que en el N657
existe con canales de sobra y pines que no chocan con nada:

- `TIM5_CH2` → **`TIM1_CH2`** (candidatos PA9/PD7/PE11 — Tabla 16)
- `TIM2_CH4` → **`TIM1_CH4`** (candidatos PA11/PB0/PC12/PE14/PG15)

**El precio, con su fuente.** TIM2..TIM5 son de 32 bits; TIM1 es de 16
(DS Tabla 97). Un contador de 16 bits al techo de reloj kernel (200 MHz,
misma tabla) da la vuelta cada 327,68 µs — **menos que la ventana más
corta del barrido** (C8, 478 µs; la larga de C1, 61,2 ms, da ~187 vueltas
— `autotune_budget.py`). O sea: los dos canales mudados **llevan la cuenta
de desbordes en firmware en las 84 notas**, no solo en las graves (la
junta cazó la causal subdeclarada). Ese análisis no es nuevo: es el de la
sección H750 de `micro_budget.py`, que lo declaró «técnica conocida, pero
trabajo por canal» — y allá eran **ocho** canales así; aquí son dos. La
resolución de sello no se toca (1/200 MHz = 5 ns, contra 131 ns de
presupuesto de jitter): el reloj no se divide, se cuenta.

**El pendiente RM0486, partido en dos** (la junta cobró la etiqueta
«heredado» aplicada a las dos mitades): el **reloj kernel** de TIM1 sí es
cola heredada — la misma de las instancias SPI. El **DMA de captura** de
`tim1_cc2`/`tim1_cc4` es pendiente **nuevo**: reabre en dos líneas la
cláusula 1 del sello del motor, que solo verificó `tim2_cc1…tim5_cc4`
(nota fechada en motor §1). Y el desenlace honesto si el RM0486 negara a
TIM1 **no es re-repartir**: `TIM5_CH2` y `LCD_G2` siguen compartiendo
{PA1} — hasta el repliegue RGB565 pide G2 y G6 — así que la salida real
sería recortar verde al panel o caer al camino B. «El encapsulado no se
mueve» sigue siendo verdad, pero por su razón vieja: el censo sin
pantalla ya elegía VFBGA264.

**Cicatriz declarada:** la primera extracción coló PB14 y PF1 como
candidatos de `TIM1_CH2` — llevan `LPTIM1_CH2`, otro periférico. Lo cazó
la puerta de reproducibilidad (`check_pinout_n657.py`), no un ojo humano:
la extracción de scratchpad no tenía frontera izquierda en la regex. La
tabla quedó corregida y la puerta coteja hoy las 113 señales pin por pin.

---

## 3. Los números del censo (corrido, no opinado)

Con TODO sentado a la vez — 16 capturas (2 mudadas), SAI full-duplex, 3
buses de CV, J2, I2C del códec, RGMII completo, 2 ADC, PSRAM octal y los
**28 pines del panel** (R0-7, G0-7, B0-7, HSYNC, VSYNC, DE, CLK):

| Escenario | Resultado |
|---|---|
| v1 completo + pantalla 24 bits | **VERDE en VFBGA264** — 92 pines repartidos, 54 GPIO libres tras reservas |
| robustez a instancias | **20/20 tercetos de CV cierran** |
| crecimiento (boca TDM, 4 subbloques SAI) + pantalla | **VERDE** — y el códec (con el táctil en su bus) solo puede vivir en **{I2C2, I2C4}**: la junta demostró que I2C1 **e I2C3** entierran la boca TDM, así que el guion barre ahora las cuatro instancias y publica la lista — el esquemático elige de ahí |
| sin RGMII (si D9 eligiera LVDS) | mínimo **VFBGA223** — sube desde el VFBGA198 de la PSRAM, por **dos cadenas independientes**: `LCD_G3` solo sale por PA0 (único pin de `TIM5_CH1`) o por PO3, y `LCD_CLK` solo por PA5 o PB13 — PO3 y PB13 nacen los dos en el 223 |

**La compra decidida no se mueve**: VFBGA264 sigue siendo la variante, y la
pantalla cabe dentro de lo ya aprobado. La cuenta que ata el encapsulado a
D9: con PA1 en manos de `LCD_G2`, `TIM2_CH2` queda entre PC0 (solo existe
en el 264) y PF14 (único RXD0 del RGMII) — Ethernet + pantalla fuerzan el
264. **Bajo una premisa que ahora está declarada** (la junta corrió el
modelo con una tercera mudanza y la cazó implícita): no se muda una
**tercera** captura. Con `TIM2_CH2`→`TIM1_CH3`, el VFBGA223 cerraría hasta
con RGMII completo — al precio de un tercer canal de 16 bits contando
desbordes. La cuenta **informa** la economía de D9; no la decide, y la
compra del 264 está sellada por la aserción inversa del guion.

---

## 4. El táctil y la frontera de filosofía

- **Capacitivo, por I2C**, compartiendo el bus del códec (los dos son
  control lento, con direcciones distintas). INT y RST del táctil más el
  PWM de retroiluminación viven en los GPIO varios del censo
  (`N6_GPIO_VARIOS = 2 + 3`, ESTIMADO hasta nombrar pieza).
- **La llave física no se muda.** El cerebro es «sin táctil, a propósito»
  porque el pulsador del encoder es la confirmación física y debe estar
  fuera de la superficie que propone (cerebro §7, núcleo §5.2). Esa
  doctrina sobrevive intacta: **las operaciones retenidas se siguen
  confirmando en el encoder del cerebro**. El táctil de esta pantalla
  edita lo del motor — granos, capas, samples, wavetables — y propone;
  no autoriza.
- **Sin menús profundos, también aquí.** La interfaz del instrumento sigue
  siendo el panel, los pomos y los cables (cerebro §7). Esta pantalla
  existe porque granular y sampler (acta de la tarde) son materia visual —
  no para mudar el sinte a un árbol de configuración.
- **Por dónde entran las ediciones al modelo — la cláusula que faltaba**
  (la junta cazó que la frontera prometía una ruta que ningún papel
  soporta): el estado es del cerebro y **nada existe fuera del modelo**
  (núcleo §2.1: «ningún camino privado»). Así que las ediciones del táctil
  **suben al cerebro como cliente, por la vía full-duplex del J2** — la
  misma dirección que el reenvío de MIDI, que el motor §5 somete a
  presupuesto de trama. Esa ruta queda **mandada y con la mano vacía**:
  su fila vive en el presupuesto de trama del enlace (`trama_j2_budget`,
  que el papel del J2 declara por nacer) con su latencia de sondeo, y
  **hasta que esa fila corra en verde, el táctil solo LEE** — visualiza
  granos, capas y estado del motor sin escribir nada. La edición se
  habilita cuando la ruta tenga presupuesto, no antes: sin esta cláusula,
  o el táctil editaba estado fuera del modelo (rompiendo la doctrina y
  dejando ciegos al agente y al VST) o la frontera era inejecutable.

---

## 5. Memoria y caudal (mandados, no hechos)

La pantalla reparte pines en el censo; la memoria y el ancho de banda
tienen sus guiones mandados en la spec del motor (§8.5, §8.7, #214
tanda 2):

- **Framebuffer**: 800×480 = 384 000 px → 768 000 B a 2 B/px (RGB565),
  1 152 000 B a 3 B/px (RGB888); el doble con doble buffer. Dónde vive
  dentro de los 4,2 MB — y contra los buffers de sample del acta de la
  tarde — lo dice el **censo de SRAM** (motor §8.5), no este papel.
- **Caudal de refresco**: 800×480×60 Hz = 23,04 Mpx/s sostenidos que el
  LTDC lee por AXI: 46/69/92 MB/s según el formato del framebuffer (la
  salida es RGB888 de 24 bits para este panel — el LTDC también saca
  YUV422-16, que aquí no aplica; el formato de entrada lo elige cada
  capa, con dithering de 2 bits si entra con menos — DS §3.29). Esa
  demanda se reparte en tres sitios distintos, y conviene no confundirlos
  (la junta de la tanda 2 corrigió la frase anterior, que los metía todos
  en `carga_motor`): el **pegamento de CPU** es fila del libro bilateral
  (motor §7); el **caudal**, solo si el framebuffer se muda a la PSRAM, lo
  mide `psram_budget.py` (46 MB/s en RGB565, 69 en RGB888, de los 240
  disponibles); y la **contención en SRAM** — el caso del camino A tal
  como está hoy — no tiene modelo de escritorio: se mide en el soak del
  riesgo 5.
- **Reloj de píxel**: lo fija el datasheet del panel (clase ~33 MHz para
  800×480@60 — ESTIMADO hasta pieza); el techo del LTDC es 150 Mpx/s
  (DS §3.28), así que no es la variable apretada.

---

## 6. Alimentación y sitio físico

- **Alimentación propia desde +12 V con regulador local** — el patrón de
  la casa, **con su condición confesada** (la junta cazó la cita a
  medias): architecture-poly §8 bendice el regulador local porque sus
  cargas «son un par de mA, dentro de la holgura de `I_MASA_SAM17`». La
  pantalla NO es un par de mA. **Del +5 V del módulo 1 no cuelga ninguna
  pantalla**: es ley escrita con su porqué (architecture-poly §9 — límite
  de diseño 300 mA, y un táctil de 7" pide 450-550 mA; el backpack
  completo de Adafruit declara 600 mA a brillo por defecto). La fila
  nueva del presupuesto de la fuente se manda aquí y se corre cuando la
  pieza tenga nombre.
- **La masa, decidida y con fila** (hallazgo ALTA de la junta: 450-550 mA
  son 9-11× el presupuesto ENTERO de masa por módulo,
  `I_MASA_SAM17 = 50 mA` en `ground_budget.py`): **la corriente de la
  pantalla no retorna por la masa del bus SAM17**. Retorno dedicado — su
  propio par de cables al módulo 1, ida y vuelta juntas — la misma clase
  de decisión que `I_MASA_EURO` ya modela para cargas gordas de un riel.
  La fila de `ground_budget.py` que lo asevere queda **mandada aquí**, con
  dueño: se escribe con la hoja de la pieza (R-M3), junto a la fila de la
  fuente.
> **CONTESTADO el 2026-08-27** — `2026-08-27-panel-pantalla-al-centro-design.md`.
> La fila mandada abajo ya tiene respuesta, y no es «dónde cabe» sino **qué
> manda**: la pantalla va **al centro del panel de la fila superior**, que
> pasa a ser un solo módulo de 104 HP, y **el resto del panel se ordena a su
> alrededor**. Dirección de Samuel. Con eso la 7" además **sustituye a la
> cabeza local de 2,8"** del cerebro y al renglón del panel: es la única
> cabeza del instrumento (B2 ratificada, no re-firmada).
>
> Consecuencia que este papel hereda y tiene que presupuestar: **la cara del
> instrumento pasa a depender del motor**, que arranca desde XSPI. Lo que
> sostiene el estado «el motor no arrancó» es la cadena WS2812, que cuelga del
> cerebro y no toca el J2.
>
> Y la cota que manda no es el ancho: son los **13,25 mm** que quedan arriba y
> abajo de la pantalla en un panel 3U, y el **fondo** — el plan del panel
> declara la fila A al 100 % con 0,6 mm de margen (E-C5).

- **Sitio en el case**: la clase de pieza mide ~165×102 mm (Adafruit 7").
  Dónde vive lo decide el censo del case con el layout del panel — fila
  mandada, dueño: el diseño del case. Lo único que este papel fija es lo
  que ya era ley: no va en el módulo 2, y el interior del case es para los
  módulos (no le compite volumen a nadie: va en una cara).

---

## 7. Piezas por nombrar (R-M3: hoja en árbol antes de dibujar)

| Pieza | Clase | Restricciones ya conocidas |
|---|---|---|
| Panel 7" | 800×480 TTL RGB 24 bits, 40 pines | reloj de píxel y consumo de backlight salen de su hoja |
| Táctil | controlador capacitivo I2C (clase FT5x06/GT911) | direcciones I2C compatibles con el códec en el mismo bus; INT + RST |
| Regulador local | desde +12 V, para backlight y lógica del panel | la fila del presupuesto de la fuente se corre con su hoja |

---

## 8. Lo que este papel NO decide

- **Qué dibuja la interfaz** (layouts, jerarquía visual, qué edita el
  táctil pantalla por pantalla): trabajo de diseño aparte, con sus dueños.
- **La pieza concreta** de las tres de §7 (R-M3).
- **D9** (la autopista): sigue en cuarentena; este papel solo actualiza su
  cuenta (el piso sin RGMII ahora es VFBGA223 y lo pone la pantalla).
- **El firmware de UI** (NeoChrom, doble buffer, compositor): entra con el
  plan de implementación del motor, después del bring-up ordenado
  (motor §11).
