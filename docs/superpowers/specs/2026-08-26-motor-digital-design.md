# El motor digital de la Voz: el N657, los cuatro ciudadanos y el puente

**Fecha:** 2026-08-26
**Estado:** v2, post-junta de cuatro lentes (acta en §13). La v1 fue juzgada
antes del PR, como manda la lección del día: dos bloqueantes, tres réplicas
del patrón #206 y una tabla de garantías que el silicio desmentía — todo
incorporado aquí.
**Premisa:** el estudio de benchmark del mismo día
(`2026-08-26-motor-digital-benchmark.md`, v2 post-junta de cinco lentes), que
selló el chip y cruzó la primera puerta de papel.

---

## 0. El sujeto, las actas y la propiedad

**Sujeto: el zócalo del micro del módulo de Voz.** La pantalla y el USB del
cerebro son de otro zócalo (#209 sitio 2); la partición cerebro/Voz no se
funde (acta E-1).

**Propiedad, declarada:** este papel es el **sucesor de la mitad digital** del
voz-total — §3.3 (presupuesto de cómputo), §3.4 (reparto de núcleos) y §9.2
(camino de silencio de los micros) quedan aquí, reescritos para un solo chip.
El voz-total conserva la cadena analógica (§2), la bahía (§5) y todo lo demás.
Cada enmienda del mapa (§9) nombra su sucesor: mientras no aterricen, la
fuente de verdad de la mitad digital es este papel.

**Actas de Samuel (2026-08-26), que este papel ejecuta:**

- **A-1 — El chip de la Voz es el STM32N657.**
- **A-2 — Todo el trabajo de audio va en la v1.** Dicho honesto (la junta lo
  exigió): *todo* es toda la **carga de cómputo**; la apertura física
  digital→analógica nace por un ojo de cerradura estéreo y crece por censo
  (§4). La resta entre la v1 y el sueño pleno está confesada, no escondida.
- **A-3 — El motor se dimensiona por presupuesto, no por algoritmo.**
- **A-4 — El CV va a velocidad de audio con enlace ≥50 MHz nominal, sin
  truco.** El acta exige el reloj y la ausencia de truco; los márgenes los
  declara este papel con la aritmética completa (§5), no con el mejor caso.
- **A-5 — Las fronteras de ruteo se borran; las de garantía se quedan** (§2).

Lo que **no** se reabre: la cadena analógica del canal (voz-total §2), E-1, los
dieciséis y su FM analógica, el J2 punto a punto (#210), el evento (#207), la
percusión (#160), el veredicto del benchmark.

---

## 1. El corazón

Un solo micro en la placa de Voz: **STM32N657** — Cortex-M55 a 800 MHz con
Helium, 4,2 MB de SRAM contigua + 192 KB de TCM, 16 canales de captura
(TIM2-5, reloj eléctrico 200 MHz → 5 ns), 2 SAI, 6 SPI, GMAC, 2 USB
HS con PHY integrado, NPU (potencial declarado, no argumento). Reemplaza a
los dos RP2350B (voz-total §1, partición de #164) y retira al H750 como clase.

> **Nota 2026-08-26 (acta camino A):** desde la pantalla, las 16 capturas
> son **14 de 32 bits en TIM2-5 + 2 de 16 bits en TIM1** (`tim1_cc2` y
> `tim1_cc4`, con cuenta de desbordes en firmware — spec pantalla-motor §2).

**Condiciones del sello — cláusulas, no notas:**

1. ~~Tabla de peticiones de DMA~~ — **cruzada** (RM0486 Rev 4, Tablas 86 y
   98: las 16 líneas `tim2_cc1…tim5_cc4` en ambos controladores; ~26 flujos
   contra 32 canales, sobran 6). **Reabierta en dos líneas por el acta de
   la pantalla** (hallazgo de su junta): `tim1_cc2`/`tim1_cc4` NO están
   entre las verificadas — su fila de DMA se cruza contra las mismas
   Tablas 86/98 antes del esquemático, junto al reloj kernel de TIM1.
2. **El censo de pines del encapsulado** — 16 capturas + subbloques SAI +
   RGMII + XSPI + J2 + USB + **los 3 buses de CV (§5)**, contra las AF del DS
   pp87-99. Vive en el guion (§8.1). **No se compra silicio hasta su verde.**
3. El RM0486 (98 MB) queda fuera del árbol por peso, citado por revisión y
   tabla, con copia en el Desktop de Samuel. Las hojas del N657 y del RA8M1
   entran a `docs/reference/datasheets/`.

La **puerta de un solo sentido** (benchmark §6) queda aceptada con los ojos
abiertos; el retorno, si hiciera falta, es al RA8M1.

---

## 2. Los cuatro ciudadanos y la ley de garantías

**Ruteo sin fronteras, garantías sin mezcla.** Cualquier ciudadano se rutea a
cualquier parte por el puente (§4) y el crosspoint; lo que no se mezcla es
**qué promete cada clase, medido en qué**:

| Ciudadano | Qué promete | Qué se mide |
|---|---|---|
| **Voz analógica** | su cadena responde en µs; la articulación la comanda el micro (evento → envolvente → VCA) con el objetivo de tecla-a-sonido del instrumento: **≤3 ms** (voz-total §3.3) | latencia evento→VCA abierto, en bring-up |
| **Voz del motor** | cadencia de render de **una muestra** (48 kHz); su latencia hasta la cadena analógica es **la del códec** (retardo de grupo del DAC sigma-delta: ~0,2-1 ms, ESTIMADO) | el retardo del códec, medido en bring-up y escrito aquí |
| **Audio invitado** | milisegundos, **sin garantía de presencia** (R-M1) | detección + rampa cronometradas |
| **CV rápido** | el **lazo de muestra**: 20,8 µs de cadencia — un **cuarto lazo** que se añade por enmienda a los tres del núcleo §7.1 | jitter del escritor, en el guion |
| **CV lento** | el lazo automático de siempre (10 kHz, §5) | `spi_privado_budget.py` |

- **R-M1 — La ausencia del invitado se degrada con elegancia.** Ejecutor: el
  **mezclador digital pre-códec** (mitad heredada, §7). Detección: **timeout
  de datos del endpoint** (~1 ms desde el último paquete válido — no el
  evento de desconexión: una DAW colgada sigue mandando SOFs). Rampa: ≥336
  muestras (7 ms). El cronómetro arranca en el último dato válido; el total
  cierra en ≤10 ms con margen. *Cierra: riesgo 7.*
- **R-M4 — Composición de garantías.** La garantía de una cadena es **la de
  su peor eslabón**. Y ningún destino garantizado queda congelado por la
  muerte de una fuente sin garantía: si el invitado muere mientras escribe un
  destino (p. ej. invitado → oídos → corte), el destino **rampa a su valor de
  preset** en el mismo plazo de R-M1 — el audio se desvanece y el CV vuelve a
  casa; nada queda pegado. *Cierra: riesgo 7, mismo cronómetro.*

---

## 3. El motor de voces

El acta A-3 como contrato:

- **Presupuesto: 50 % del núcleo = ~8 300 ciclos por muestra** a 48 kHz. Es
  **techo con válvula**: lo que no quepa lo toca el cómputo invitado (§6) —
  el motor cede, las garantías jamás (§7, regla de cesión).
- **16 voces digitales**, tipos intercambiables por preset:
  - FM de 6 operadores (clase DX7): 96 operadores **y sus 96 EG de
    operador** — este bucket es del motor — ≈ 1 200-2 800 ciclos (ESTIMADO).
  - Wavetable con unísono (clase Serum): hasta 256 osciladores ≈ 2 000-4 600
    ciclos (ESTIMADO).
  - Espectral (FFT/iFFT amortizada): ≈ 400 ciclos las 16 voces (ESTIMADO).
  - **Granular** (acta 2026-08-26, tarde): granos = lecturas interpoladas
    con ventana, la misma clase de trabajo por muestra que el wavetable —
    **sin cifra hasta que su fila corra en `carga_motor`** (§8.1). No se
    publica número de granos sin correr el modelo.
  - **Sampler** (misma acta): voces de reproducción desde SRAM y **PSRAM
    en XSPI1** — la RAM externa deja de ser crecimiento y pasa a **pieza
    v1** (pieza concreta por nombrar, hoja en árbol antes de dibujar,
    R-M3). Streaming y latencia de grano contra la PSRAM: fila nueva del
    guion (§8.7).
- **Memoria:** una tabla clase Serum ≈ 1 MB en f16. Cuántas caben residentes
  lo dice el **censo de SRAM con el binario adentro** (§8.5 — sin flash
  interna, el firmware entero comparte los 4,2 MB con tablas, colas y
  retardos): entre 1 y 3, no se promete más hasta censar. La biblioteca vive
  en XSPI y se streamea al cambiar preset. Código de callback y tablas
  calientes anclados a TCM/SRAM por linker.
- **Los parámetros del motor entran al modelo o no existen** (núcleo §2.1):
  decenas de parámetros direccionables contra un techo **ya reventado**
  (`MAX_PARAMS = 512` contra 536 censados, voz-total E-6 / #172). El censo de
  parámetros del motor es fila obligada del mapa (§9) — el motor que no se
  puede tocar desde las carcasas y el agente no es el instrumento del sueño.
- **R-M2 — El presupuesto es ejecutable y bilateral.** `carga_motor` (§8.1)
  asevera **las dos mitades**: motor ≤ 50 % **y** mitad heredada ≤ 50 % (con
  su libro en §7); los ESTIMADO parametrizados, el bring-up los reemplaza por
  medidos y las aserciones siguen mandando. *Cierra: riesgo 2.*

---

## 4. El puente digital⇄analógico

La mezcla del instrumento es analógica y fija (16:1, actas E-5/E-6). El audio
digital necesita camino de entrada, y este papel lo decide — con sus costos
contados:

- **D-P1 — La boca del códec entra como fuente de la bahía.** Las salidas del
  códec (estéreo en v1) se conectan como fuentes del crosspoint (los dos
  AD75019, voz-total §5.1). El audio digital se patchea como cualquier señal:
  al nodo de suma de un canal — a través del MS-20 y el VCA de una voz real —,
  en retroalimentación, a donde el preset diga.
  - **Contrato eléctrico (nuevo):** entre boca y crosspoint hay una **etapa
    de acople y ganancia** que lleva el nivel de línea del códec al nivel
    nominal de señal de la bahía (mundo ±12 V). El número exacto se fija en
    el esquemático **con el códec nombrado** — fila del guion, hoja en árbol.
  - **Fallback declarado:** si el censo del crosspoint da rojo (no caben
    fuentes sin quitarle un jack a nadie), la boca entra directo al bus del
    mixer — se pierde el patcheo del audio digital, no el audio digital.
- **D-P2 — Un solo puente, dos clientes.** Motor e invitado comparten la boca
  y se mezclan digitalmente antes del códec.
- **El ojo de la cerradura, confesado:** con boca estéreo, **las 16 voces del
  motor entran al mundo analógico como un par mezclado** — el motor es
  polifónico en lo digital y *parafónico* en lo analógico. La articulación
  analógica por voz digital **no existe en v1**. Ensancharla (códec/DAC
  multicanal TDM, más fuentes de crosspoint) es el camino de crecimiento, con
  su censo y su costo — y es exactamente la resta entre la v1 y el
  Prophet+DX7 pleno del sueño.
- **D-P3 — El contrato del canal conducto.** Un canal que presta su cuerpo al
  audio digital (señal externa en su suma, oscilador callado) es rol
  *conducto* (voz-total §0.3): sale del reparto de notas — **cada canal
  prestado es una voz analógica menos, y se cuenta**. Su VCA lo articula el
  micro (único escritor) con una envolvente disparada por el **evento de
  ruteo del preset**, no por nota. Sin este contrato, el audio digital llega
  a un VCA cerrado.
- **D-P4 — El patch «señal → oídos».** Para que «oscilador → corte» exista,
  los oídos ganan una **entrada ruteable desde el crosspoint** (destino
  nuevo; censo en §8.4). Dos vías al corte, que el guion compara:
  - **vía códec** (audio fiel): lleva el retardo de grupo del códec (~ms,
    ESTIMADO) — modulación a velocidad de audio con latencia de códec;
  - **vía ADC rápido del micro** (12 bits, 5 Msps): µs de lazo para la FM de
    corte apretada, con menos bits.
- **La subida ya existe:** los oídos de E-5. El puente queda bidireccional.

---

## 5. El CV a velocidad de audio

El acta A-4 ejecutada con la aritmética completa — la v1 de este papel
escribió aquí un «margen ≥2×» que su propio rango desmentía (la junta lo cazó
como #206); esta versión escribe la cuenta entera:

- **La ley de dos tasas** (enmienda a voz-total §3.1, no derogación): los
  **destinos rápidos** rinden a **48 kHz**; los demás siguen a **10 kHz** con
  su presupuesto vigente. En v1, los destinos rápidos son **los 16 CV de
  corte** (S-9). **Promover un destino a rápido es acta de Samuel + guion
  recorrido** — ni criterio implícito ni censo fantasma.
- **La palabra, con bandera:** el dato del CV es de **16 bits** (la premisa
  de #210 D9 y del benchmark se conserva); en el cable viaja dentro de la
  **trama del DAC** — 24 bits clase AD5686R como referencia de modelo. La
  demanda se modela con la trama real y la **eficiencia 0,60** que la casa ya
  declara (`spi_privado_budget.py`), no con bits desnudos.
- **La topología: 3 buses SPI maestros** punto a punto, a **50 MHz
  nominales** (techo del chip: 105, Tabla 99 — manda el DAC), **un DAC
  multicanal por bus con NSS por hardware**. La cláusula que lo exige: en DMA
  puro (lista enlazada, cero CPU), el CS solo es gratis si es una línea de
  hardware por bus — 64 tramas × 48 kHz por ISR serían >3 M interrupciones/s,
  y eso mata. Candidatos a receptor: AD5686R (el titular del repo, 4 canales
  — censo de CS feo a 64) y **LTC2668-16** (16 canales, 16 bits, ±10 V, SPI
  50 MHz — la topología limpia). **R-M3 manda: hoja en árbol antes de
  dibujar.** *Cierra: riesgo 3.*
- **La cuenta honesta (eficiencia 0,60):**

  | Escenario | Demanda cruda | Capacidad útil (3×50 MHz×0,60 = 90 Mb/s) | Margen |
  |---|---|---|---|
  | **v1**: 16 rápidos ×24 b×48 kHz + 48 lentos ×24 b×10 kHz | 18,4 + 11,5 = **29,9 Mb/s** | 90 Mb/s | **3,0×** |
  | Techo aspiracional: 64 rápidos ×24 b×48 kHz | 73,7 Mb/s | 90 Mb/s | 1,2× — **no se promete**: se paga con SCLK mayor (manda el DAC) o trama de 16 b, cuenta del guion |

- **El S-9 se conserva y se potencia:** el micro sigue siendo el único
  escritor del corte — ahora a velocidad de audio.

> **Enmienda del 2026-09-02 — la cláusula del suavizado (papel del generador
> de envolvente, §5 y §14).** La ley de dos tasas gana una frase que le
> faltaba: **una fuente lenta puede alimentar un destino rápido a través de
> un polo de un tick (100 µs) en el escritor; el polo es del escritor, que ya
> es rápido, y la fuente sigue lenta.** Es la envolvente del filtro (10 kHz)
> entrando al escritor de corte (48 kHz): retén de orden cero más un polo, el
> gemelo digital de la RC que el DAC del VCA lleva en cobre. No es promover
> la fuente —sigue rindiendo a 10 kHz— y por eso no pide acta por destino; la
> junta cazó que sin esta frase la v1 de aquel papel creaba la categoría en
> una subordinada, que es lo que esta sección prohíbe. El polo es causal y
> no depende de que la razón de relojes sea entera.

---

## 6. El invitado

- **D-P5 — El reloj tiene amo, y es el instrumento.** La interfaz de audio
  USB es **UAC2 asíncrona con endpoint de feedback**: el host se adapta al
  48 kHz del instrumento. El reloj del SAI/códec **jamás** se deriva del USB
  — es la condición que hace ejecutable a R-M1 (si el reloj muriera con el
  cable, el fade sería imposible).
- **En v1 el puerto invitado transporta AUDIO.** El MIDI sigue entrando por
  la puerta del cerebro (su USB de siempre): el asignador de voces es del
  cerebro (architecture-poly §2) y **no se le crea una segunda boca** sin
  árbitro. Unificar ambos en un dispositivo compuesto que reenvíe MIDI al
  cerebro por J2 es evolución declarada — con su presupuesto de trama — no v1.
- **D-P6 — La doctrina de masa como puerta.** «La puerta sucia no vive en el
  cuarto limpio; esta placa es donde 1 mV son 3,6 cents» (voz-total E-1). La
  v1 de este papel aterrizaba el USB de la laptop —su fuente conmutada, su
  masa— en la placa de la Voz: la junta lo marcó como el #206 a escala de
  acta. Se corrige de raíz: **ningún conector del mundo toca la placa de la
  Voz.** El conector del invitado vive en la **tarjeta de E/S trasera**
  (#183), y cruza hacia adentro **aislado galvánicamente**: USB HS con
  aislador clase ISOUSB211 (480 Mb/s; hoja en árbol antes de dibujar),
  Ethernet con sus magnetics de estándar. *Cierra: riesgo 8.*
- **Cómputo diferido:** la computadora renderiza wavetables y timbres y los
  sube a la biblioteca XSPI; el N657 los toca solo.
- Bajada y subida de audio por el puente (§4); ausencia bajo R-M1/R-M4. **El
  instrumento completo funciona sin el invitado.**
- Por Ethernet, el mismo contrato cuando la autopista D9 se decida (#210 —
  en cuarentena; decisión de Samuel).

---

## 7. La mitad heredada — con libro propio

La v1 aseveraba solo la mitad del motor; la junta lo llamó coartada. Libro de
la mitad heredada (~8 333 ciclos/muestra disponibles), método del benchmark:

| Trabajo | Ciclos/muestra (ESTIMADO) |
|---|---|
| 16+ ADSR de canal (tasa: 10 kHz, lazo automático — la clase de envolvente y su tasa quedan así asignadas; promoverlas a rápidas es acta) | ~150 |
| Escritor de CV: cómputo 64 valores + empaquetado + feed de DMA | ~500-800 |
| FFT de oídos amortizada | ~190 |
| Mezcla digital + fade R-M1 + ISR/scheduler | ~650 |
| USB invitado (UAC2 asíncrono, feedback) | ~100-300 |
| Oyente J2 amortizado | ~20-50 |
| **UI de la pantalla, amortizada** (acta camino A — ESTIMADO, sin fuente) | ~25-150 |
| **Mapeo de gestos, amortizado** (acta de la cámara — ESTIMADO, sin fuente) | ~6-50 |
| **Central** | **~1 641-2 340 ≈ 20-28 %** (las seis primeras: ~1 610-2 140) |

> **Enmienda 2026-08-26 (noche), del guion y su junta:** las dos filas
> nuevas entran como **filas**, no como «pegamento». El motivo es un número:
> la UI amortizada llega a 150 ciclos — el triple de la fila entera del
> oyente J2 e igual a la de los 16 ADSR. Llamarla pegamento y aseverarla
> contra un umbral inventado era un verde disfrazado (hallazgo de la junta
> de la tanda 2). Ni el LTDC ni la NPU gastan CPU: esto es solo el trabajo
> de componer la UI y de convertir landmarks en señal.

Con error de 3× en todo: **~59-84 % — cabe**, y las dos filas nuevas se
comieron siete puntos de holgura (antes ~58-77 %). La aserción vive en
`carga_motor_budget.py` (R-M2 bilateral) y es la dura del guion. **Regla de cesión:** al desbordar cualquiera de las dos
mitades, **cede el motor** (su válvula es el invitado); la mitad heredada —
que carga todas las garantías de §2 — no cede jamás.

**Los trabajos, con sus números corregidos:**

| Trabajo | Cómo |
|---|---|
| 16 cronómetros | 14 en TIM2-5 (32 bits) + 2 en TIM1 (16 bits, desbordes contados — acta camino A) a 200 MHz (5 ns); capturas repartidas entre GPDMA1/HPDMA1 (RM0486 Tablas 86/98; `tim1_cc2`/`tim1_cc4` pendientes de cruzar); sellado ≤ ~13 ns (assert de `autotune_budget.py`) |
| Autoafinado autónomo | el guion se recorre con `N_VOCES = 16` y **architecture-poly adopta el número que el guion dé** — no se propaga cifra sin correr el modelo |
| Oyente J2 | esclavo full-duplex; D8 real 34,5 MHz (Tabla 99, nota 2); el gap mínimo entre tramas pasa a cláusula del contrato del enlace (hallazgo de la junta de **este** spec) |
| Oídos + FFT | códec de E-5; el micro entrega espectros — la atribución es del cerebro |

**La arquitectura de tiempo real, declarada** (la v1 no le dedicaba una
oración; es el sucesor de voz-total §3.4): prioridades NVIC en orden —
**capturas y J2 > DMA de audio (SAI/CV) > USB/Ethernet > resto**; vectores e
ISR críticas en ITCM; el presupuesto de latencia de interrupción entra al
libro bilateral y el bring-up lo mide bajo carga plena.

> **Enmienda del 2026-09-02 (papel del generador de envolvente, §3.5, §9 y
> §14).** El **tick de 10 kHz de los generadores de envolvente** entra al
> orden, que no lo nombraba: va **en el escalón del DMA de audio y CV** —debajo
> de capturas y J2, encima de USB y Ethernet—, porque es quien alimenta ese
> DMA. Y es el **único dueño del estado** de los generadores: la ISR del J2
> no muta nada, encola (evento, reafirmación, `SET`, `soltar todo`) en una cola
> SPSC que el tick drena entera y en orden antes de avanzar. La latencia real
> de esa ISR es un hueco de `ataque_budget.py` hasta el bring-up.

- **R-M5 — El silencio no depende del software.** El N657 es el único
  escritor de 48 VCAs: colgado, dieciséis voces quedarían gobernadas por un
  muerto — la enfermedad del #201, tercera función. Sucesor del camino de
  silencio de voz-total §9.2: **watchdog independiente + estado seguro por
  hardware** — los VCAs y el crosspoint caen a silencio **sin CPU** (inhibición
  a reset, el patrón H-OF4). *Cierra: riesgo 9.*

---

## 8. Los guiones (mandados, no hechos; sus criterios de cierre viven en §11)

1. **`micro_budget.py` se expande** (declarado en #210 §7): vara v2 del
   benchmark y **censo de pines** (puerta 2 — bloqueante de compra, ahora
   con los 3 buses de CV, la PSRAM y la pantalla adentro) — ✅ hecho. El
   `carga_motor` **bilateral** (R-M2) salió a guion propio: ✅ **existe,
   `hardware/02-midi-cv/carga_motor_budget.py`** — VERDE, con las dos
   mitades aseveradas y las filas de granular y sampler que el acta de la
   tarde mandó, derivadas del ancla publicada del wavetable.
2. **`spi_privado_budget.py` se recorre** con la ley de dos tasas, la trama
   del DAC real y la eficiencia 0,60 (R-M3).
3. **`autotune_budget.py`**: `N_VOCES = 16`; architecture-poly adopta su
   salida.
4. **Censo del crosspoint** (D-P1/D-P4): fuentes nuevas (la boca) **y el
   destino hacia los oídos**, sin quitarle jack a nadie — enmienda a
   voz-total §5.
5. **Censo de SRAM** con el binario adentro (§3): cuántas tablas residentes
   caben de verdad — **y ahora también los buffers de sample y granos**
   (acta 2026-08-26, tarde). ✅ **Existe: `hardware/03-vco/sram_voz_budget.py`**
   — y sale **HUECO**: con la cara en el hub (D2) y la cámara en el mago
   (D3'), lo fijo de la Voz en el peor caso ESTIMADO son 2,4 de los 4,2 MB
   (binario 2 000 000 + colas 400 000), quedan 1 800 000 B y el mínimo —una
   tabla residente más el buffer de sample— pide 1 256 000. No es verde
   porque **el tamaño del binario sigue siendo el mayor desconocido del
   motor**: el único medido es la parte compartida del hub (82 280 B,
   `sram_hub_budget.py`) y no trae motores de audio. Se mide en escritorio,
   secciones ALLOC del ELF, en cuanto haya motores que enlazar; las otras
   dos salidas de antes (framebuffer a PSRAM, camino B) eran del motor
   integrado y ya no le tocan a este censo.
6. **Censo de parámetros del motor** contra `MAX_PARAMS` (#172): el motor
   entra al modelo o no existe.
7. **Presupuesto de la PSRAM** (nace con el acta 2026-08-26, tarde): caudal
   y latencia del XSPI1 contra la demanda de granos/sampler (techo
   eléctrico: DS Tablas 75-76, 140 MHz a 3,3 V / 180 MHz a 1,8 V en DTR),
   y las filas de ciclos de granular y sampler en `carga_motor`.
   ✅ **Existe: `hardware/02-midi-cv/psram_budget.py`** — caudal cerrado.
   **Corrección de fuente que su junta obligó:** las Tablas 75-76 que este
   punto citaba son la fuente **incompleta** para este diseño. El censo de
   pines sienta `XSPIM_P1_DQS0`, así que la tabla aplicable es la **77**
   (p182, «DTR mode with DQS or HyperBus»): **200 MHz a cualquier voltaje
   entre 1,65 y 3,6 V** — o sea que en el modo del diseño **el voltaje no
   decide el techo**. Con ella el bus compra 2 500 granos a velocidad ×1 y
   625 a ×4 (granos transpuestos leen proporcional), contra los 129-289 que
   compra la CPU: **manda la CPU, no el bus, en todo el rango modelado**.
   La vara del EP-133 queda **medio cerrada, y así lo dice el guion**: la
   mesa de trabajo está aseverada contra la mitad de la vara (criterio
   propio del guion, y hoy pasa por igualdad exacta — margen cero); el
   catálogo del XSPI2, que cubre la otra mitad, **no tiene pieza ni cifra
   ni aserción** (R-M3). **La latencia sigue fuera** y está declarada en el
   cierre del guion: sale de la hoja de la pieza, no del ancho de banda.
8. **Presupuesto de la pantalla** (nace con el acta 2026-08-26, noche —
   spec pantalla-motor; **desde D2 la pantalla es del hub, no del motor**):
   el framebuffer entra al censo de SRAM **del hub** (`sram_hub_budget.py`,
   hub §10 fila 2), no al de la Voz ni junto a los buffers de sample; y su
   caudal de refresco (23,04 Mpx/s sostenidos por AXI: 46-92 MB/s según
   formato) se cobra en el hub. **Dónde vive cada mitad, corregido por la
   junta de la tanda 2 y por D2** (la redacción anterior decía «entra a
   `carga_motor`» de algo que `carga_motor` declara fuera): el **pegamento
   de CPU** (componer la UI) era fila del libro bilateral, ~25-150 ciclos,
   §7, y `carga_motor` la conserva solo como escenario heredado — el hub no
   tiene censo de CPU todavía; el **caudal en PSRAM** lo mide
   `psram_budget.py` en su escenario de framebuffer mudado (46 MB/s en
   RGB565, 69 en RGB888), y en el hub esa PSRAM no comparte bus con el
   sampler; y la **contención en SRAM**, que es el costo real del camino A,
   **no tiene modelo de escritorio a propósito**: se mide en bring-up con el
   refresco LTDC activo, en el hub (#231). Hasta que el censo del hub cierre
   y ese soak corra, **el conector del panel no se dibuja** (puerta del
   repliegue, spec pantalla §1).

---

## 9. El mapa de enmiendas (mandadas, no hechas)

| Papel | Qué |
|---|---|
| ~~voz-total §1/§3~~ | ✅ **APLICADA 2026-08-26.** §1: muere la particion en dos columnas, y con ella la base de tiempo compartida, el arranque en dos mitades y la recuperacion entre columnas (muerto el motivo —doce PIO para dieciseis cronometros—, muere la particion). §3.3: pierde la etapa maestro→esclavo, el jitter entre micros y el «uniforme entre columnas»; **sobrevive el ≤3 ms**. §3.4: sucedida entera, con el texto viejo conservado en `<details>`; se rescata su regla de la ventana de MISO |
| ~~voz-total §3.1~~ | ✅ **APLICADA 2026-08-26.** Escrita como enmienda y no derogacion: los 10 kHz siguen gobernando la clase lenta (envolventes incluidas) y los 16 CV de corte suben a 48 kHz. Copiada tambien la cerradura: promover un destino es acta + guion recorrido |
| ~~voz-total §5~~ | ✅ **APLICADA 2026-08-26.** Fuente nueva (boca, con su etapa de acople pendiente de numero) y destino nuevo (oidos ruteables, con las dos vias y su compromiso bits-contra-latencia). **El censo sigue mandado y sin hacer** (§8.4): hasta que corra, nadie sabe si las dos vias caben en las 16×16 |
| ~~voz-total §9.2~~ | ✅ **APLICADA 2026-08-26.** Dos de sus cuatro failsafes eran micros vigilandose entre si y mueren; escrito de frente que **la red de seguridad empeoro** al perder la vigilancia mutua, que por eso el sustituto es hardware y no mas software, y que el watchdog de trama sobrevive entero |
| ~~voz-total E-5~~ | ✅ **APLICADA 2026-08-26.** El codec deja de ser un sentido y pasa a puente bidireccional; donde el acta dice «los oidos» hoy se lee «el codec» |
| ~~núcleo §7.1~~ | ✅ **APLICADA 2026-08-26.** El cuarto lazo entra arriba de la tabla, y con el argumento de por que no rompe la doctrina: **lo que separa los lazos no es la velocidad, es la autoridad** — el de muestra ejecuta lo que otro decidio, no mide ni razona. La frase «el agente jamas esta en el camino de audio» queda intacta |
| ~~#210 §0.1 / §4~~ | ✅ **APLICADA el 2026-08-26.** «clase H750» → clase N657; D8 **34,5 MHz** (verificado contra DS14791 Rev 2 Tabla 99 + su nota 2, no transcrito); peldaño 1 **22,9 MHz** al peor mazo — **no ~23-26**: recalculado con la disciplina de máx-gobierna que el propio #210 §4.1 declara, el rango de esta fila resultó optimista por arriba y queda señalado allá. Se enmendaron además cinco sitios que este mandato no nombraba pero que la enmienda arrastra: D8, la tabla de peldaños de §3, las tres lecturas de §4.2, la tabla de tráfico y el riesgo 2 de §8 |
| ~~#209~~ | ✅ **APLICADA 2026-08-26** (comentario en el PR, que esta mergeado). Su veredicto sobrevive como historia; la correccion queda escrita con su leccion: el «cabe (73 %)» era contra RAM TOTAL y un framebuffer vive en una region CONTIGUA (la AXI de 512 KB). No llego a hacer dano —el cerebro se quedo con la 2,8" por SPI— pero **el mismo error volvio en grande tres dias despues**: es el hueco del censo de SRAM del N657 |
| ~~architecture-poly §5~~ | ✅ **APLICADA 2026-08-26.** Y descubrio DOS derivas, no una: el numero a mano (3,5 s) ya estaba mal con las 4 voces viejas (el guion daba 2,7 s y nadie lo re-corrio), ademas de que el instrumento tiene 16. **Hubo que enmendar el guion antes**: `autotune_budget.py` modelaba el PIO del RP2350 a 150 MHz — ahora captura de TIM a 200 MHz y `N_VOCES = 16`. Resultado: el barrido **no se alarga** (2,7 s, las 16 en paralelo; 44 s de una en una) y el presupuesto del 74HC14 sube de 131 a **133 ns** de regalo |
| ~~architecture-compute §5~~ | ✅ **APLICADA 2026-08-26.** El cuarto rol escrito con la objecion contestada de frente (¿no contradice el §1?): no, porque el instrumento **no depende** del invitado — suena entero sin computadora, su ausencia esta cronometrada (R-M1, timeout de datos y no evento de desconexion) y nada queda pegado (R-M4). Copiada tambien la regla de cesion y el precio fisico: conector aislado en la tarjeta trasera (D-P6/#183) |
| ~~#183~~ | ✅ **APLICADA 2026-08-26** (comentario en el issue). Deja de ser «una tarjeta que nadie ha documentado» y gana su primer requisito dibujable: conector de invitado **aislado**, con lo que el aislamiento cueste en espacio y piezas, mas su fila en el presupuesto de masa, que hoy no existe |
| ~~#172 / `check_censo_voz`~~ | ✅ **APLICADA 2026-08-26.** Sin inventar la cifra: «decenas» no es un numero, asi que el guion los cuenta como **ausentes y visibles** (fila `SIN CENSAR`, motor + mapeo de gestos). Y desactiva una trampa: los 232 que «sobran» del techo son ANTES de meterlos — no son margen, son la habitacion de dos inquilinos que no han llegado |
| ~~dieciséis~~ / **#205 pendiente de acta** | ✅ **dieciséis §3 APLICADA 2026-08-26**: la tabla perdio su sujeto (no hay RP2350B en esa placa), y se escribe por que se cayo tan limpio — la spec decia «lo que sostiene los dos micros es SOLO el PIO», y un diseno con un unico apoyo se cae entero cuando aparece un chip que da ese recurso de sobra. Sobrevive su primera columna: 16 osciladores piden 16 cronometros. ⚠️ **El «cerrar o reescribir» del #205 NO lo decide este barrido**: evidencia y recomendacion (cerrar) en su issue |

---

## 10. Lo que este papel NO decide

- La pantalla y el USB del **cerebro** (#209 sitio 2).
- La forma de la autopista (D9 del #210 — decisión de Samuel, en cuarentena).
- El contrato de percusión (#160) y el formato del evento (#207).
- La variante (N647/N657) y la compra — bloqueadas por la puerta 2.
- **La PSRAM concreta** (fabricante, densidad, SDR/DTR): pieza v1 por acta,
  parte por nombrar con su hoja en árbol (R-M3).
- **El ancho de la boca multicanal** (el crecimiento del ojo de la cerradura)
  y el número exacto de la etapa de acople — filas del censo y el esquemático.
- El firmware (Rust + núcleos C): la profundidad del PAC/Embassy se audita al
  arrancar el plan de implementación.

---

## 11. Riesgos, con criterio de cierre

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | El censo de pines no cabe (capturas + SAI + RGMII + XSPI + J2 + USB + 3 buses CV + **los 28 pines de la pantalla**, acta camino A) | guion §8.1 verde contra las AF del DS pp87-99 — **antes de comprar** (cerrado: VERDE en VFBGA264 con todo sentado) |
| 2 | Los ESTIMADO mienten >3× (cualquiera de las dos mitades) | bring-up: ciclos medidos desde TCM **con DMA de fondo corriendo** reemplazan estimados en `carga_motor` bilateral |
| 3 | No existe receptor digno (SPI ≥50 MHz, multicanal, NSS hardware, asentamiento a 48 kHz) | hoja del DAC en árbol + `spi_privado_budget.py` recorrido verde |
| 4 | El gap entre tramas del J2 no alcanza para el giro D8 | cláusula escrita en el contrato del enlace + medición |
| 5 | Contención de banco SRAM/AXI — **y desde el acta de la noche el framebuffer ES el contendiente mayor**: el LTDC lo lee sin pausa (46-92 MB/s, §8.8) mientras granular lee grains, contra colas de audio, DMA y código (el paréntesis «framebuffer no» murió con el acta — hallazgo de la junta de la pantalla) | colocación por linker + soak concurrente medido **con el refresco LTDC activo**; cierra también el §8.8 |
| 6 | Errata joven / boot firmado / Rust vivo | FSBL + binario Rust corriendo en Nucleo-N657 **antes del respin de placa** |
| 7 | R-M1/R-M4 no cierran en ≤10 ms | bring-up en vivo: cable fuera a mitad de nota, detección+rampa (audio y CV) cronometradas |
| 8 | El lazo de tierra del invitado ensucia el cuarto limpio | hoja del aislador USB-HS en árbol + medición de ruido en los 16 expos con la laptop enchufada |
| 9 | El N657 colgado deja 48 VCAs sin gobierno | R-M5 en esquemático: silencio por hardware demostrado matando la CPU en bring-up |
| 10 | La térmica del ganador (la vara que mató a los MPU se aplica también en casa) | disipación del N657 medida en el case cerrado contra los −0,33 %/°C del expo |
| 11 | Los 3 buses de 50 MHz cruzan la zona analógica | regla de zonas en el layout + medición de EMI en bring-up |
| 12 | El retardo del códec desmiente la tabla de §2 | retardo de grupo medido y escrito en la fila de la voz del motor |

**El orden del bring-up** (de la junta, y es ley): 1 boot+Rust vivo → 2 linker
y costo de miss XSPI → 3 `carga_motor` medida con DMA de fondo **y el
refresco LTDC activo** → 4 las 16 capturas bajo carga con sello ≤13 ns —
**también con el LTDC refrescando** (acta camino A: la pantalla no puede
costarle jitter a las capturas sin que se sepa) → 5 SPI 50 MHz contra el DAC
nombrado → 6 SAI full-duplex + retardo del códec → 7 UAC2 + R-M1 en vivo →
8 J2 con el par real (gap) → 9 soak total con las aserciones contra medidos.

---

## 12. El sueño, medido contra esta v1

Para que nadie confunda el papel con el instrumento final: esta v1 entrega el
motor completo en cómputo (A-2), el CV de corte a velocidad de audio, el
invitado aislado y el puente — y **no** entrega articulación analógica por
voz digital (el ojo de la cerradura es estéreo), ni más destinos rápidos que
los 16 cortes, ni el MIDI unificado en un solo cable. Cada una de esas tres
restas tiene su camino de crecimiento declarado (§4, §5, §6). El sueño no se
recorta; se entrega por etapas con las cuentas a la vista.

---

## 13. Acta

**Adenda del 2026-08-26 (tarde), acta de Samuel:** «van a v1 de una vez…
escoger el motor es el fundamento… lo que sea necesario pero debemos
resolver esto a lo mega pro». Consecuencias, todas ya ejecutadas o
mandadas: **granular y sampler entran a la lista v1 de motores** (§3, sin
cifras hasta correr el modelo); **la PSRAM en XSPI1 pasa de crecimiento a
pieza v1** (§8.7, R-M3); el censo de pines la sienta a la mesa (11 pines,
puerto XSPI1 — y con ella el piso del encapsulado sin RGMII subió entonces a
VFBGA198; el acta de la noche lo subiría después a VFBGA223,
`micro_budget.py`); el censo de SRAM (§8.5) suma los buffers de
sample. La revalidación del chip bajo el alcance nuevo: el N657 se
**fortalece** (4,2 MB de SRAM + dos XSPI independientes: arranque+biblioteca
en PN, PSRAM en PO/PP); «dos motores» queda descartado — es la enfermedad
del #201, y la válvula del diseño ya es el invitado (§6).

**Adenda del 2026-08-26 (noche), acta de Samuel — la pantalla:** preguntó
por una táctil de 7" en el módulo, pidió la propuesta completa («vamos con
todo») y eligió con los números en la mano: **«Vamos con A»** — la pantalla
directa al LTDC del N657, aceptando la mudanza de dos capturas a TIM1 con
su cuenta de desbordes declarada. El censo re-corrió **VERDE en VFBGA264**
(92 pines repartidos, 54 libres, 20/20 tercetos; el piso sin RGMII sube a
VFBGA223 y ahora lo pone la pantalla, no la PSRAM). La compra decidida no
se mueve. El diseño completo, su precio y sus pendientes viven en
`2026-08-26-pantalla-motor-design.md`; los presupuestos de memoria y caudal
quedan mandados en §8.5/§8.7/§8.8.

**Misma noche, segunda acta — la cámara de gestos:** «si, la declaras». Las
manos como fuente de modulación (categoría: señal local tipo LFO, no
edición del modelo), con el sensor en el CSI-2 (balls dedicados — cero
GPIO del censo) y la inferencia en la NPU que este papel dejó como
«potencial declarado, no argumento»: los gestos la estrenan. Sus filas de
presupuesto apuntan a §8.5, §8.8, el libro bilateral (R-M2) y el censo de
parámetros (#172). El diseño, la respuesta a la variante inalámbrica y
sus pendientes viven en `2026-08-26-camara-gestos-design.md`.

Diseño aprobado por Samuel en conversación (siete secciones); la v1 escrita
pasó su junta de cuatro lentes **antes del PR** y salió reescrita:

- **Consistencia**: toda cita de datasheet/guion/acta CONFIRMADA salvo tres
  vicios — todos en §5 y su eco: el «margen ≥2×» (falso en la mitad de su
  propio rango), los 24 bits sin bandera, una atribución de hallazgo. Los
  tres, corregidos aquí.
- **Clínica** (1 BLOCKER, 11 HIGH): la frontera de «destinos rápidos» sin
  criterio ni dueño → la ley de dos tasas con promoción por acta (§5); el
  50 % sin libro → el libro bilateral (§7); el canal conducto, el acople, el
  embudo estéreo, el reloj USB, los parámetros del motor — todos con cláusula.
- **Ejecución**: corre (~25 % la mitad del motor, ~20-26 % la heredada); las
  dos heridas — la garantía «una muestra» contra el retardo del códec, y la
  aritmética del CV — reescritas; el orden del bring-up adoptado como ley.
- **Estructura** (1 BLOQUEANTE): el USB del invitado aterrizaba en el cuarto
  limpio citando E-1 como intocable — el #206 a escala de acta, la quinta
  réplica del día. Corregido de raíz con D-P6. Más: el libro que solo
  vigilaba una mitad, los huérfanos de §9.2 (→ R-M5), la térmica que solo
  apuntaba hacia afuera (→ riesgo 10), y la confesión del ojo de la cerradura
  (→ §12).

La v1 de este papel repitió el patrón que su propio benchmark acababa de
purgar. La junta existe porque el patrón asciende de capa; el papel que
firmas es el que sobrevivió a ella.
