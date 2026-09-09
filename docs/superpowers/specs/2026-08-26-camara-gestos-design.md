# La cámara de gestos — las manos como fuente de modulación

**Fecha:** 2026-08-26 (noche)
**Estado:** declarada a v1 por acta de Samuel; este papel fija arquitectura,
frontera musical y pendientes. No nombra piezas (R-M3) ni corre presupuestos
(mandados en §5).
**Sujeto:** una cámara mirando las manos sobre el instrumento, con la
inferencia en la NPU del N657, para usar gestos como fuente de expresión —
«como en TouchDesigner», pero embebido y autónomo.

---

## 0. El acta

Samuel: «tambien quiero que usemos una camara para poder usar el
sintetizador con las manos como en touch designer es eso posible?» — y con
el análisis en la mano: «si, la declaras». En la misma conversación preguntó
por la variante inalámbrica; la respuesta está en §4 y es parte de este
papel: **v1 es cableada al case; el satélite inalámbrico queda declarado
como crecimiento**, con su física explicada.

---

## 1. Por qué el chip ya lo trae (cero sorpresas de pines)

- **MIPI CSI-2 de 2 carriles** (2,5 Gbps/carril, sensores hasta 5 Mpx a
  30 fps — DS14791 Rev 2, §3.25-3.26). Sus pines (`CSI_D0P/D0N`,
  `CSI_D1P/D1N`, `CSI_CKP/CKN`, `CSI_REXT` — este último pide su
  resistencia externa de referencia en placa, como el TXRTUNE del USB)
  son **balls dedicados**, como los del USB: no compiten en el censo de
  GPIO. Los 54 libres del censo con pantalla siguen libres.
- **DCMIPP**: la tubería de cámara en hardware — recorte, reescalado y
  conversión de formato, de cámara a memoria sin gastar CPU (DS §3.25).
- **Neural-ART, 600 GOPS a 1 GHz** (DS p1; benchmark §«La NPU, en su
  sitio»). El dato que lo cambia todo: el benchmark eligió el chip con la
  NPU como *«potencial declarado, no argumento»* — el motor de audio no
  cuenta con ella para nada. **Está ociosa por diseño: ciclos de CPU no le
  quita a nadie. Ancho de memoria, sí** — el mismo párrafo del benchmark
  que la declara potencial advierte que *«comparte la memoria del sistema
  (DS p29)»*, y la junta cobró citarlo a medias: los pesos del modelo
  viven en XSPI2 (el mismo bus que streamea la biblioteca de tablas al
  cambiar preset) y las activaciones en la SRAM que ya comparten LTDC y
  granos. Ese costo tiene fila en §5. Los modelos de la clase (landmarks
  de mano / clasificadores de postura, cuantizados) son el caso de uso que
  ST publica para este chip (su model zoo para STM32N6 — referencia por
  nombre, sin documento en el árbol; se trae con la pieza).

Lo que sí pide la cámara, y es barato: su configuración por I2C (el mismo
bus lento que comparten códec y táctil — una dirección más), y 2 GPIO
varios de reset/powerdown (ESTIMADO hasta pieza). **Y el reloj maestro ya
tiene su cuenta corrida** (la junta cobró aplazar una fila que el modelo
contesta hoy): el chip trae exactamente dos MCO en la Tabla 16 — MCO1 solo
en PA8 y MCO2 solo en PC9. **MCO1 está muerto**: PA8 es el único pin de
`LCD_B6` del censo. **MCO2/PC9 cierra**: corrido contra el censo completo,
VERDE en VFBGA264 mudando `LCD_B3` a PG6 (53 libres). Consecuencia para la
mesa R-M3: el módulo sensor **trae oscilador propio, o usa MCO2/PC9 —
única vía** — y esa restricción filtra piezas antes de enamorarse de
ninguna.

---

## 2. La frontera musical: modulación sí, disparo no

Los gestos son **una fuente de expresión continua**, no un teclado:

- Altura, posición, apertura y pinza de las manos → CVs, morphs de macros,
  densidad y posición de la nube de granos, barridos de filtro. Un campo
  tipo theremin sobre el panel.
- La cadena de visión (exposición del sensor + inferencia + suavizado)
  vive en la clase de **decenas de milisegundos** — perfecta para
  modulación, **inadecuada para disparar notas con precisión percusiva**.
  El número real no se promete: **se mide en bring-up** y se escribe en su
  fila de presupuesto. Disparar sigue siendo de teclas, pads y secuenciador.
- **La categoría, escrita de frente** (hallazgo ALTA de la junta: sin
  esto, la frontera confundía fuente de señal con edición del modelo):
  los gestos son **fuente de señal local del motor, tipo LFO** — el VALOR
  instantáneo del gesto es señal continua a 30-60 Hz, no estado, y **no
  pasa por el J2** por la misma razón que la fase instantánea de un LFO
  no vive en el modelo: señal no es estado, y meterla a la trama sería
  inundarla con lo que no le toca. Lo que SÍ es estado del modelo es su
  **mapeo**: qué gesto mueve qué destino, con qué profundidad, y si está
  activo. Esos parámetros son del cerebro, entran por la vía de siempre
  (núcleo §2.1, «ningún camino privado») y **tienen fila mandada en el
  censo de parámetros del motor (#172)** — la cámara no estrena atajos.
  Distinto del táctil de la pantalla, que sí EDITA estado y por eso
  hereda entera la cláusula J2 de pantalla §4 (solo-lectura hasta que su
  fila corra).
- **La misma frontera de autoridad que el táctil** (pantalla §4): la
  cámara **propone, nunca autoriza**. Ninguna operación retenida se
  confirma con un gesto; la llave física sigue siendo el encoder del
  cerebro (cerebro §7, núcleo §5.2).
- Sinergia declarada: la pantalla del motor es el sitio natural del
  feedback visual del campo de gestos (qué ve la cámara, qué mano manda
  sobre qué destino).

---

## 3. La física que decide dónde vive: el flex del CSI

MIPI CSI-2 D-PHY es una interfaz de **flex corto** — centímetros, no
metros (conocimiento de oficio, **sin cita en el árbol**: el DS solo
referencia el estándar D-PHY v1.2 sin cifra de alcance; si algún diseño
quisiera estirar el flex, la cifra de canal se trae del estándar antes).
No es un cable de cámara de seguridad: es el mismo tipo de enlace
que une el sensor de un teléfono con su procesador. Consecuencia de
diseño, no de gusto: **la cámara v1 vive en el case**, en un flex corto
hasta la placa del motor, mirando el campo donde se tocan las manos
(ángulo y hueco: censo del case, junto al sitio de la pantalla — es la
única parte de esta declaración con reloj corriendo, porque el case se
está dibujando ahora).

---

## 4. ¿Y la inalámbrica? La respuesta honesta, en tres caminos

| Camino | Latencia (clase, ESTIMADO) | Veredicto |
|---|---|---|
| **A. Cableada al case (CSI)** | cuadro (17-33 ms a 60/30 fps) + inferencia NPU + suavizado → **~30-80 ms** | **v1.** La única que aprovecha DCMIPP y la NPU tal cual |
| **B. Video inalámbrico** (WiFi/IP-cam: comprimir → radio → descomprimir) | **~100-300 ms** extremo a extremo | **Muerta para expresión.** El lag se siente como tocar por videollamada; además el N657 tendría que descomprimir video, trabajo que nadie presupuestó |
| **C. Satélite con inferencia local** (una cámara-computadora chica que corre el modelo ALLÁ y radia solo los **landmarks**: decenas de floats a 30-60 Hz, kilobits/s) | cuadro + inferencia local (más lenta que la NPU del N657) + radio corta → **~50-100 ms** | **Viable como crecimiento.** No es una cámara: es un periférico inteligente |

El truco del camino C es que **lo inalámbrico no debe ser el video sino el
resultado**: mover kilobits de landmarks por radio es trivial; mover
megabits de video comprimido es lo que mata la latencia. Pero el satélite
cuesta lo que cuesta: otro micro con NPU chica, su batería, su radio — y
la advertencia de certificación del puente RF aplica entera (cerebro §6.6:
la certificación de un módulo pre-certificado está atada a sus antenas).
Y una honestidad más que la junta cobró: el «~50-100 ms» de la tabla es
**el tramo hasta la radio** — dónde aterrizan los landmarks en el
instrumento (¿el puente del cerebro? ¿un receptor propio del motor?) y por
qué ruta entran, es cuenta del papel de crecimiento, no de este. Por eso
es **crecimiento declarado, no v1**: el campo de gestos sobre el panel
(camino A) da el instrumento completo; el satélite añade libertad de
colocación (vista cenital, cámara en un mástil) cuando el instrumento ya
toque.

---

## 5. Presupuestos mandados (no hechos)

| Fila | Dónde | Qué mide |
|---|---|---|
| Frames + activaciones del modelo | censo de SRAM (`sram_hub_budget.py`) | ✅ **sentados**: cuadros del DCMIPP con doble buffer (150-600 kB, ESTIMADO) y activaciones (200-800 kB, ESTIMADO). La inferencia corre sobre entradas reducidas — el DCMIPP reescala en hardware. La primera versión del censo no tenía la fila de cuadros; la cazó la junta de la tanda 2 |
| Caudal de cámara **+ inferencia NPU** por AXI y XSPI2 | `carga_motor` / cola del §8.8 | la cadena entera, no solo el DMA de la cámara: frames por AXI, **pesos desde XSPI2 — el mismo bus que streamea la biblioteca al cambiar preset** (el choque se mide, no se supone), activaciones en la SRAM de todos |
| Ciclos de CPU de la cadena de gestos (pre/post-proceso, suavizado) | el libro bilateral de `carga_motor` (R-M2) | la NPU no le quita ciclos al motor; el pegamento alrededor sí, y se cuenta |
| Latencia de la cadena de gestos | bring-up (Nucleo primero, motor §11) | cuadro→landmark→señal medido, **con puerta** (la junta cobró la fila sin criterio): aprobado en la clase del camino A (~30-80 ms); **suspenso desde ~100 ms**, la frontera que §4 declara muerta para expresión. Umbral de clase ESTIMADO — se afina con el modelo elegido, pero la fila nace con dientes |
| Parámetros de mapeo de gestos (destino, profundidad, enable) | censo de parámetros del motor (#172) | son estado del modelo (§2) y entran al censo como todos |
| Consumo del sensor + iluminación | presupuesto de la fuente | con la hoja de la pieza (R-M3) |

---

## 6. El riesgo real: la luz

La visión en un escenario vive entre luces cambiantes, contraluces y
oscuridad teatral. La salida robusta de la industria es el **infrarrojo**
(así funcionaba el Leap Motion): sensor sensible a IR + iluminación IR
propia = el campo de gestos deja de depender de la luz de la sala. Es
decisión de pieza, no de arquitectura — va a la mesa R-M3 con dos opciones
mínimas (sensor RGB de la clase demo de ST vs sensor+emisores IR) y sus
hojas en el árbol antes de dibujar nada.

---

## 7. Piezas por nombrar (R-M3: hoja en árbol antes de dibujar)

| Pieza | Clase | Restricciones ya conocidas |
|---|---|---|
| Sensor de cámara | módulo MIPI CSI-2, 1-2 carriles | flex corto (§3); ¿oscilador propio o pide MCO? (§1); ¿global shutter ayuda al tracking? — lo dice su hoja |
| Iluminación IR (si §6 la elige) | emisores IR + filtro | consumo a la fila de la fuente; **+1-2 GPIO** (enable/strobe, ESTIMADO) — y si el strobe se sincroniza con la exposición, pide **canal de timer**, que no es «cualquier GPIO» (la lección del PWM del backlight) |

---

## 8. Lo que este papel NO decide

- **La pieza** (sensor, IR, lente) — R-M3.
- **El modelo concreto de manos** (landmarks vs postura, tamaño, fps): se
  elige contra la NPU real en bring-up, con su fila de latencia medida.
- **El mapeo musical** (qué gesto mueve qué): diseño de instrumento, con
  Samuel en la mesa — el papel solo fija la frontera de §2.
- **El satélite inalámbrico** (camino C): crecimiento declarado, sin fecha.
