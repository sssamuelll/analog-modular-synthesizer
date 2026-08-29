# El benchmark del motor digital: la vara nueva, sus dos habitantes, y la puerta de un solo sentido

**Estado: v2, post-junta de cinco lentes (2026-08-26). SELLADO POR SAMUEL
(2026-08-26): el chip es el STM32N657. Sello condicionado a las dos puertas de
papel de §7 (RM0486 y censo de pines) antes de comprar.** Actas del mismo día:
el CV va a velocidad de audio con enlace de **≥50 MHz nominal, sin truco, por
capacidad de spec** (§7.4b resuelta: se reabre voz-total §3.1 y se recorre
`spi_privado_budget.py`); la dimensión del motor (§7.4a) queda propuesta como
presupuesto de capacidad, pendiente del dale. La v1 de este estudio fue juzgada por una junta
adversarial que encontró 3 bloqueantes y varias réplicas del patrón #206; esta v2
los incorpora todos. El acta de la junta está en §9.

---

## 0. El sujeto, y qué no se reabre

**Sujeto del benchmark: el zócalo del micro del módulo de Voz.** La v1 mezclaba
cargas de dos placas que el acta E-1 del voz-total prohíbe fundir: la pantalla y
el USB host son del **cerebro** (cerebro-v2 §5.2, núcleo digital §5.3) y salen
de la carga. El cerebro tiene su propia comparación abierta (#209, sitio 2); no
es este papel.

**Decisiones vigentes** (no se relitigan): un solo micro en la Voz; 16
cronómetros simultáneos sin multiplexar; autoafinado autónomo; todo el trabajo
de audio en v1; el precio no vota; nada se mergea sin Samuel.

**Definición operativa de «truco»** (la junta la exigió; sin ella V1 no corta):

- Multiplexar los 16: **prohibido** por decisión de Samuel.
- Extensión de desborde por software (contador de 16 bits + conteo de vueltas
  en ISR): **truco**. Es la maraña que la directiva veta.
- Cascada de contadores **por hardware**: no es truco en sí — pero la captura
  tiene que latchear los 32 bits **atómicamente en el flanco**. Una costura de
  dos lecturas con ambigüedad de ±1 vuelta es el equivalente funcional del
  truco.

**Consecuencia, confesada de frente:** bajo esta vara **el H750 también
reprueba V1** (8 canales limpios; los demás, de 16 bits con extensión =
truco). El veredicto del #209 sobrevive como historia — H750 > RP2350B con la
vara vieja — pero la premisa *«un micro clase H750»* de #210 §0.1 queda
apuntando a una clase que esta vara retira. Va al mapa de enmiendas del #210
cuando este papel selle (§8).

---

## 1. La carga del zócalo de la Voz (corregida por la junta)

| # | Trabajo | Número que gobierna | Fuente |
|---|---------|--------------------|--------|
| 1 | 16 cronómetros simultáneos | ventana 61,2 ms; **el sellado del micro debe ser despreciable: ≤ ~13 ns** (el assert de `autotune_budget.py` exige ≤10 % de los 131 ns, que son la holgura del **comparador**, no la vara del micro — la v1 de este papel la infló 10×) | `autotune_budget.py` |
| 2 | Oyente J2 + respuesta D8 | esclavo full-duplex; el techo real lo pone tv(SO)+tsu del maestro, no el titular de la hoja | #210 D8 |
| 3 | Autoafinado autónomo | barrido 2,75 s con 16 en paralelo (el guion aún modela 4 voces — deuda §8) | `autotune_budget.py` |
| 4 | Generadores de envolvente ×16+ | el ADSR corre en el micro | voz-total §3.1 |
| 5 | Escritor de CV | **PENDIENTE DE ACTA**: la ley vigente es render a 10 kHz (voz-total §3.1, con `spi_privado_budget.py` VERDE a esa tasa). «Control a velocidad de audio» (48 kHz = 16×4×48k×16 b ≈ 49 Mb/s, #210 D9) lo multiplica ~5×: si Samuel lo decreta, **se reabre §3.1 y se recorre ese guion** — no se sube en silencio | voz-total §3.1 / #210 D9 |
| 6 | El motor FM digital | **dimensión PROPUESTA, pendiente de acta**: 16 voces × 6 operadores = 96 op @ 48 kHz (la ficha del DX7 como clase de referencia; ningún papel del repo la dimensiona — el FM del repo es el analógico 8×2 del dieciséis) | decisión de hoy + acta pendiente |
| 7 | Oídos | códec 24 b (vive en la Voz por E-5) + FFT local; **la atribución es del cerebro** (architecture-poly §2) — el micro entrega espectros, no veredictos | acta E-5 |
| 8 | El audio digital hacia la cadena | la mezcla del instrumento es **analógica y fija** (16:1, E-5/E-6 — la v1 decía «mezcla digital» citando actas que dicen lo contrario: #206 cazado). El camino por el que las voces digitales entran a esa cadena **no existe en ningún papel**: es decisión del spec de la Voz (¿DAC propio al nodo de suma? ¿a la bahía?) | actas E-5/E-6 |
| 9 | Autopista | **en cuarentena por su propio papel**: #210 D9 es «camino declarado con cobre reservado — no un número del que dependa ningún otro papel». Se anota como capacidad del endpoint; **no puntúa en la vara** | #210 D9 |

Los ESTIMADO van parametrizados al guion y se miden en bring-up.

---

## 2. La vara v2

- **V1 — Los 16 cronómetros de 32 bits, sin truco, con captura por DMA** — y el
  sello exige demostrar en papel (manual de referencia) que las **16 rutas de
  DMA concurrentes existen**, no solo los canales de timer.
- **V2 — Memoria para la carga de audio.** Tablas de onda, líneas de retardo,
  colas, y — donde no hay flash interna — el código mismo. (El framebuffer se
  fue con la pantalla al cerebro; la vara v1 ejecutó a un candidato con esa
  fila fantasma y esta v2 lo repara, §4.)
- **V3 — El enlace**: SPI esclavo full-duplex con los términos que gobiernan;
  USART. (El TSN es propiedad de **sistema**, no del chip: con el maestro de
  hoy sin TSN, no hay TSN de punta a punta — no puntúa.)
- **V4 — Músculo de audio, ahora con umbral**: el presupuesto grueso de ciclos
  (§4-V4). Un candidato reprueba V4 si su presupuesto central no cabe.
- **V5 — Un solo cerebro.** Doble núcleo en un die con SRAM compartida y un
  solo arranque **no** son dos cerebros (la enfermedad del #201 era
  coordinación entre chips con arranques y firmwares separados). Un MPU con
  dominio Linux + dominio M coordinándose por RPMsg, con el arranque del M
  subordinado a U-Boot, **sí** lo es — dentro del encapsulado.
- **V6 — Cadena de herramientas de la casa** (Rust): pondera, no corta.
- **V7 — El precio no vota** (directiva).

---

## 3. Los candidatos y sus papeles

| Chip | Papel | Estado |
|------|-------|--------|
| RP2350B | hoja 2024-08 (en árbol) | muerto en #209 (12 máquinas PIO) |
| STM32H750 | DS12556 Rev 8 (en árbol) | el titular saliente |
| STM32H743/753 | familia RM0433 | dominado: mismos timers que el H750 |
| STM32H7S7 | ficha ST/RS (620 KB RAM) | **reclasificado por la junta**: la v1 lo mató por un framebuffer que era del cerebro. Muerte probable real: V1 (familia H7RS: TIM2/TIM5). **Sin papel en mano — quien lo reviva trae el datasheet** |
| i.MX RT1170 | RM Rev 3 11/2024 (bajado, 35 MB) | muerto en V1, dos veces (§4) |
| **STM32N657** | **DS14791 Rev 2 12/2024 (bajado, 244 pp; verificado carácter por carácter por la junta)** | habitante confirmado de V1 |
| **Renesas RA8M1** | **R01DS0417 Rev 1.10 (bajado hoy, 188 pp)** — censado por exigencia de la junta (H15) | **probable segundo habitante** (§4) |
| SHARC ADSP-2156x | no traído | muere V1+V5+V6: DSP sin banco de captura clase MCU → chip compañero (dos cerebros otra vez), cadena propietaria sin Rust |
| MPU (i.MX 8M Plus, STM32MP2x) | quinto lente de la junta, con fuentes | **muertos**: V1 (12 y ~8 canales), V5 dos veces (dominio A + dominio M por RPMsg; arranque del M subordinado a la cadena Linux — wiki de ST), y el físico: 2-5 W de calor contra los −0,33 %/°C del conversor exponencial, DDR+PMIC irradiando junto a 16 voces analógicas, segundos de arranque contra la doctrina de milisegundos. La NPU real de esta clase es 1,35-2,3 TOPS — no «miles» |

---

## 4. El corte, con cita

### V1 — los 16 cronómetros

| Chip | Canales de captura de 32 bits | Veredicto |
|------|------------------------------|-----------|
| STM32H750 | 8 (TIM2/TIM5) | **reprueba** — completar con 16 bits + software es truco por definición §0 |
| i.MX RT1170 | 12 (6 GPT × «two input capture channels», RM p5823) — y **segunda muerte**: la captura del GPT genera solo interrupción, sin petición de DMA (RM §74.2.1) | **reprueba dos veces**. La cascada de QTimers (16 bits × 2) no lo salva: el latcheo del par no es atómico en el flanco (semántica HOLD del TMR — por confirmar en su RM, pero la carga de la prueba es de quien lo reviva) |
| **STM32N657** | **16** — «4x 32-bit timers with up to four IC» (DS p2), «32-bit counter (TIM2 **to** TIM5)» (Tabla 97 p204), y el pinout pp87-99 expone los 16 pines TIM2_CH1…TIM5_CH4. La junta lo verificó carácter por carácter — el N6 sí rompe el patrón de 20 años de la familia | **pasa en papel de datasheet**; el sello exige la tabla de peticiones de DMA del RM0486 (§7.1) |
| **Renesas RA8M1** | **probable 16** — GPT32 × 8 canales (DS p1, Tabla 1.7 p4), cada uno con entradas GTIOCxA/GTIOCxB (x=0-7; electricals p85) y captura (tGTICW, Figura 2.45 p87). 8 contadores × 2 registros de captura = 16 sellos de 32 bits | **pendiente de dos páginas del manual de hardware**: captura simultánea A+B por canal, y el reloj PCLKD máximo (la resolución debe dar ≤ ~13 ns) |

**Resolución del N657, corregida por la junta:** la portada dice timers «up to
240 MHz», pero la **Tabla 97 de la p204 — característica eléctrica — dice
fTIMxCLK máx 200 MHz → 5 ns**, no 4,17. Gobierna la tabla eléctrica. 5 ns pasa
la vara de ≤13 ns igual; el número corregido es el que entra al guion.

### V2 — memoria para la carga de audio

| Chip | Memoria | Para «todo el audio» |
|------|---------|---------------------|
| STM32N657 | **4,2 MB SRAM contigua** + 128 KB DTCM + 64 KB ITCM (p1); sin flash interna — el código crítico vive en SRAM/TCM por disciplina de linker | holgado: tablas, retardos, colas y código adentro |
| RA8M1 | 1 MB SRAM (896 KB usuario + 128 KB TCM) — pero **2 MB de flash interna** (código fuera de la RAM) | justo: los 896 KB son solo datos; para retardos largos + tablas del motor FM es la diferencia real con el N657 |

### V3 — el enlace

- **N657 esclavo full-duplex**: titular 50 MHz (Tabla 99 p205) — **pero la nota
  (2) de esa misma tabla lo condiciona a un maestro con tsu(MI)=0, que no
  existe**. Con maestro real clase STM32 (tsu 4,5 ns): techo eléctrico
  **1/(2×(10+4,5)) ≈ 34,5 MHz**. La v1 decía «el D8 sube a 50» — patrón #206,
  cazado por la junta y corregido: **el D8 sube de 31 a ~34,5 MHz.** El
  peldaño 1 (~23-26 MHz a 738 mm) no tenía el vicio: su modelo ya sumaba
  tv(SO)máx + tsu + vuelo.
- RA8M1: SPI ×2 «up to 60 Mbps» + SCI síncrono ×6 (p1) — timing de esclavo
  pendiente de su tabla eléctrica antes de puntuarlo.
- USART: N657 12,5 Mb/s (p2).

### La letra que faltaba: la salida física del CV (la casilla más débil del ganador)

La v1 afirmaba «con TDM alcanza» citando el MCLK de 50 MHz. **La fila que
gobierna es otra de la misma Tabla 104: fCK controller transmitter = 38 MHz.**
Con eso: 64 flujos × 16 b × 48 kHz = 49,152 Mb/s **no caben en un subbloque**
(máx ~49 slots de 16 b… a 38 MHz: no); se necesitan **dos subbloques a 32
slots de 16 b (24,576 MHz cada uno)** — y el censo queda 4/4 subbloques
ocupados (códec boca + oídos + 2 de CV), **margen cero**, solo con slots de
16 bits, y **sin un DAC receptor de TDM 32×16 identificado en ningún papel**.
Alternativa: abanico de SPI (2-3 buses, DACs octales). **Estado: ESTIMADO con
receptor pendiente — y condicionado al acta de la fila 5 (si el render queda
en 10 kHz, todo esto sobra).** Es la única casilla donde el titular H750 (4
SAI) era más fuerte que el ganador, y queda escrita como tal.

### V4 — músculo, ahora con presupuesto

Presupuesto grueso del lente de ejecución (todo ESTIMADO, a medir en bring-up;
800 MHz / 48 kHz = **16 666 ciclos por muestra**):

| Trabajo | Ciclos/muestra |
|---|---|
| 96 operadores FM (Helium, 10-25 cyc/op) | 960-2 400 |
| 96 EG de operador + 16 ADSR | ~670 |
| 64 valores de CV | ~380 |
| FFT 1024 f32 amortizada ×16 | ~190 |
| Mezcla digital interna + ISR/scheduler | ~600 |
| **Total central** | **~4 200 ≈ 25 %** |

Con error de **3× en todo a la vez: ~76 %** — apretado pero corre. El riesgo
real no es la ALU: es que el código/tablas críticos caigan fuera de TCM/SRAM
(sin flash interna, un miss de XSPI cuesta cientos de ciclos). Disciplina de
linker, verificada en bring-up. Nota de honestidad: el RT1170 dobla el
CoreMark escalar del N657 (6468 vs 3360) — muere en V1, no en V4. El
multiplicador Helium exacto queda ESTIMADO hasta medirlo.

**La NPU, en su sitio:** 600 Gops @ 1 GHz (p1) — la misma NPU que el
STM32MP23 de clase MPU, sin pagar el peaje del MPU. Pero **comparte la
memoria del sistema** (DS p29) y no hay camino demostrado de su runtime (C,
int8) a inferencia a tasa de audio. **No puntúa en la vara; es potencial
declarado, no argumento.**

---

## 5. El veredicto v2 — no una coronación

La junta desnudó la puesta en escena de la v1: comparar V2-V4 contra
candidatos ya muertos en V1 era teatro. Dicho como es:

**El espacio de restricciones vigente {16×32 sin truco + DMA, un cerebro, la
carga de audio} tiene UN habitante confirmado — el STM32N657 — y un segundo
probable — el RA8M1 — pendiente de dos páginas de su manual.**

Entre los dos, para ESTA carga:

| | STM32N657 | RA8M1 |
|---|---|---|
| Músculo | 800 MHz M55 + Helium, 3360 CoreMark | 480 MHz M85 + Helium (FPU doble incluida) |
| Memoria de audio | 4,2 MB | 1 MB (+2 MB flash interna) |
| Enlace | 34,5 MHz D8; GMAC gigabit | 60 Mbps titular (esclavo pendiente); MAC 10/100 |
| Simplicidad de nacimiento | boot externo firmado, BGA, silicio 12/2024 | **flash interna, LQFP disponible**, silicio 10/2023 |
| Rust | PAC `stm32n6` en crates.io + Embassy con las n657 listadas (verificado hoy; profundidad por auditar) | ecosistema Rust débil (FSP es C) |

**Recomendación: STM32N657** — para la carga que Samuel decretó («todo el
audio, y todo es todo»), la memoria 4,2× y los 800 MHz dominan; el RA8M1 queda
censado con papel como el contrapeso conservador, no ignorado.

---

## 6. La puerta de un solo sentido (léela antes de sellar)

Elegir el N657 es una puerta con bisagra cara, y se declara:

- **Riesgo compuesto, no seis viñetas**: primera placa BGA/HDI del proyecto ×
  silicio con errata joven (12/2024) × boot firmado con herramienta de ST ×
  fuente única sin segunda fuente × cero retrabajo casero. Cada uno es
  «precio»; multiplicados son el perfil de riesgo del proyecto concentrado en
  un footprint.
- **Costo de retorno si en 6 meses resulta error**: respin de placa (BGA→LQFP),
  recálculo de #210 §4, pérdida del inner loop vectorial, y relitigar dos
  decisiones (los 16 sin truco no los cumple ningún otro STM32 de hoy; el
  RA8M1 sería el destino del retorno, no el H750).
- **Mitigación honesta**: las dos puertas de papel de §7 se cruzan ANTES de
  comprar; el bring-up valida los ESTIMADO antes del respin de la placa de Voz.

---

## 7. El sello: condicionado a

1. **RM0486 (N6): la tabla de peticiones GPDMA/HPDMA** — **CRUZADA
   (2026-08-26, RM0486 Rev 4, traído por Samuel).** Las 16 líneas de captura
   (`tim2_cc1_dma`…`tim5_cc4_dma`) existen en **las dos** tablas de peticiones:
   GPDMA1 (Tabla 98, REQSEL 21-24/27-30/33-36/39-42, pp932-933) **y** HPDMA1
   (Tabla 86, mismos números, pp836-837) — cualquier canal atiende cualquier
   petición vía REQSEL, así que las 16 capturas se reparten libres entre los
   dos controladores (p. ej. 8+8). El resto del censo también tiene línea en
   la Tabla 98: los 12 flujos de SPI1-6 (79-90), los 4 subbloques de SAI
   (91-94), USART/UART (107-128), ADC (7-8), ADF/MDF (131-137). Censo total:
   ~26 flujos contra 32 canales con mux libre — **cabe con 6 de sobra**, y
   LTDC/GMAC/USB traen DMA propio (DS §3.28/3.55/3.52). El peor caso de la
   junta («el GPDMA entero consumido») no ocurre.
2. **Censo de pines del encapsulado** — 16 capturas + 4 subbloques SAI + RGMII
   + XSPI + J2 + USB a la vez, con las AF de las pp87-99 del DS.
3. **RA8M1, manual de hardware**: captura A+B simultánea y PCLKD máx — cierra
   si el espacio tiene uno o dos habitantes.
4. **Actas de Samuel** — las dos primeras SELLADAS 2026-08-26:
   (a) **el motor se dimensiona por presupuesto, no por algoritmo**: 50 % del
   núcleo (~8.300 ciclos/muestra a 48 kHz), tipos de oscilador intercambiables
   por preset (FM 6-op clase DX7, wavetable con unísono clase Serum,
   espectral), 16 voces; lo que no quepa lo toca el cómputo invitado;
   (b) **el CV va a velocidad de audio** (48 kHz), con enlace de **≥50 MHz
   nominal sin truco** (SPI maestro, techo del chip 105 MHz, Tabla 99) —
   reabre voz-total §3.1 y recorre `spi_privado_budget.py` por enmienda;
   (c) el receptor físico del CV (DACs con SPI ≥50 MHz): por nombrar con
   datasheet en el guion.
5. **Guion**: `micro_budget.py` se expande (declarado en #210 §7) con esta
   vara y estos números tras el merge de #209.

---

## 8. Ecos a los papeles abiertos

- **#210**: §0.1 «clase H750» → clase nueva (enmienda); §4 el peldaño 1 queda
  ~~~23-26 MHz (consistente)~~ **22,9 MHz — ver la corrección de abajo**, el
  D8 pasa a **34,5 MHz** (no 50); D9 sigue en cuarentena; TSN de punta a punta
  no existe con el maestro de hoy — anotado.

  > **Corrección del 2026-08-26 (sesión de merges), contra mi propio número.**
  > Al aplicar esta enmienda en el #210 hubo que correr la cadena de §4.2 en
  > vez de darla por «consistente», y el rango de arriba **no se reproduce**.
  > Con las filas de la Tabla 99 (`tv(SO)` máx **10 ns**, `tsu(MI)` **4,5 ns**)
  > y la propagación de 5 ns/m que el #210 ya usaba:
  >
  > ```
  > 738 mm:  10 + 7,38 + 4,5 = 21,88 ns  ->  22,9 MHz
  > ```
  >
  > El borde bajo del rango se sostiene raspando; **el 26 no sale ni con el
  > típico** de 8,5 ns, que da 24,5. Escribí «~23-26 (consistente)» sin correr
  > la cuenta — es el mismo patrón #206 que este documento cazó dos veces en
  > otros, cometido aquí. **La cifra que gobierna es 22,9 MHz**, y vive en el
  > #210 §4.2 con su aritmética a la vista.
  >
  > No mueve ninguna conclusión de este benchmark: el peldaño 1 seguía y sigue
  > holgado contra el tráfico declarado, y D8 lo jubila igual. Se corrige
  > porque un número sin correr no se hereda como medido.
- **#209**: sobrevive como historia. Corrección al sitio-cerebro: el «framebuffer
  cabe (73 %)» del H750 era contra RAM total — la región contigua mayor es la
  AXI de 512 KB; con la pantalla sellada del cerebro (2,8" SPI, framebuffer en
  el controlador — cerebro-v2 §5.2) la fila muere entera.
- **voz-total §3.1 / E-6**: sus VERDES quedan condicionados al acta de tasa de
  render (fila 5).
- **`autotune_budget.py`**: modela 4 voces (`N_VOCES = 4`) y architecture-poly
  §5 publica 3,5 s — desfasados de la decisión de 16; deuda de guion.
- **El cerebro (futuro papel)**: hallazgo del quinto lente — si algún día entra
  una computadora, la forma correcta es **módulo opcional colgado de la
  autopista Ethernet**, fuera del camino del sonido; nunca sustituto del
  cerebro. La doctrina («la computadora queda fuera», architecture-compute §1)
  se mantiene.

---

## 9. Acta de la junta (2026-08-26)

Cinco lentes: verificación de citas (todas las citas contra los dos PDF),
clínica (14 hallazgos, 3 BLOCKERS), ejecución (presupuesto de ciclos y los dos
mata-desde-papel), estructura (15 hallazgos; «amañaron un juicio que podían
ganar limpio»), y MPU (veredicto NO con fuentes). Lo que la junta cazó y esta
v2 repara:

- **Sujeto indefinido** (pantalla/USB del cerebro en la carga de la Voz) → §0.
- **La viga maestra sin contraverificar** → verificada carácter por carácter +
  pinout (los 16 pines existen).
- **El framebuffer fantasma que ejecutó al H7S7** → retirado; H7S7 reclasificado.
- **#206 × 4**: «D8 a 50» (nota 2 de la Tabla 99); «con TDM alcanza» (38 MHz
  gobierna, no 50); «240 MHz = 4,17 ns» (Tabla 97: 200 → 5 ns); «mezcla
  digital» citando actas de mezcla analógica.
- **131 ns como vara del micro** → es del comparador; la del micro es ≤ ~13 ns.
- **La doble mano de V1** (H750 «pasa con maraña») → el H750 reprueba, y la
  consecuencia sobre #210 §0.1 queda escrita.
- **El RA8 sin censar** → censado con papel en mano, probable segundo habitante.
- **La vara sin letra para la salida de CV** → escrita, con la casilla débil
  del ganador a la vista.
- **La puerta sin bisagra** → §6.

La v1 de este papel se declaró «verificado página por página» y la junta
demostró que no lo estaba entero. Esta v2 no se declara nada: lista lo que
está verificado, lo que está ESTIMADO, y lo que le falta — que es la única
declaración que un papel de este proyecto tiene derecho a hacer.
