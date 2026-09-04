# Referencias bibliográficas

Lista de referencias citadas en la tesis original, complementada con recursos
útiles para la reproducción y mejora del proyecto.

## Tesis original (referencias bibliográficas)

1. *Aplicaciones con Microcontroladores* (2010). Microcontrolador. http://marcombo.com
2. Clegg, B. (2017). *A Modular Synthesizer using the Raspberry Pi*. Tesis de
   grado, University of Sheffield.
   https://ben.clegg.tech/files/ben-clegg-dissertation-2017.pdf
3. ElectroBOOM (canal de YouTube). https://www.youtube.com/user/msadaghd
4. Electronica FP (canal de YouTube).
   https://www.youtube.com/channel/UCeidauAIxx_JeNcrleaPDqw
5. Friedman, D. (1985). *Synthesizer Basics* (1.ª ed.). Music Sales Corp.
6. Chamberlin, H. (1983). *Musical Applications of Microprocessors* (2.ª ed.).
   Hayden Book Company.
7. Jenkins, M. (2007). *Analog Synthesizers* (1.ª ed.). Elsevier.
8. *KiCAD tutorial 2019. Learn KiCAD under 25 minutes*.
   https://www.youtube.com/watch?v=-tN14xlWWmA
9. Miles, D. (2007). *The MIDI Manual* (3.ª ed.). Elsevier.
10. Stinchcombe, T. (2006). *A Study of the Korg MS10 and MS20 Filters*.
    http://www.timstinchcombe.co.uk/synth/MS20_study.pdf
11. *Synths'r'us. Third ADSR schematic*. https://www.schmitzbits.de/adsr.html
12. Wiltshire, T. *Design a Eurorack Vintage VCA with the LM13700*.
    https://electricdruid.net/design-a-eurorack-vintage-vca-with-the-lm13700/
13. Wilson, R. (2013). *Make: Analog Synthesizers* (1.ª ed.). Maker Media.
14. Wikipedia. *Sintetizador*. https://es.wikipedia.org/wiki/Sintetizador

## Hojas de datos (Anexo A de la tesis)

- **CEM3340** — VCO clásico, se usa en VCO1/VCO2/VCO3.
- **AD5686R** — DAC cuádruple 16-bit con referencia interna 2.5 V (módulo MIDI/CV).
- **TL074** — cuádruple op-amp JFET (mixer, VCF, ADSR, VCA).
- **LM13700** — doble OTA con buffers (VCF, VCA).
- **ICM7555** — timer CMOS de bajo consumo (núcleo del ADSR).
- **LM358** — doble op-amp.
- **6N137** — optoacoplador (entrada MIDI estándar DIN, opcional).
- **PIC** — microcontrolador citado en el anexo (no usado en el prototipo final).

Esa lista es la del anexo de la tesis. Sus PDFs no se redistribuyen aquí;
descárgalos del fabricante.

## Hojas de datos en el repositorio

Las veinte versionadas, enteras. Están en el historial porque los presupuestos
ejecutables y el código citan sus tablas por número, así que sin ellas una
puerta no se puede rehacer. Algunas son de piezas **retiradas**: se quedan
rotuladas como historia de la decisión, no como contrato vigente.

| Fichero | Pieza | Dónde se usa |
|---|---|---|
| [`reference/datasheets/ssi2130-rev2.4-2020-12.pdf`](reference/datasheets/ssi2130-rev2.4-2020-12.pdf) | SSI2130 — VCO | Los 16 osciladores del módulo de Voz |
| [`reference/datasheets/rp2350-datasheet-2024-08.pdf`](reference/datasheets/rp2350-datasheet-2024-08.pdf) | RP2350 (legado) | Cerebro y micros del módulo de Voz hasta D1 (2026-08-30) |
| [`reference/datasheets/rp2350-product-brief-2024-08.pdf`](reference/datasheets/rp2350-product-brief-2024-08.pdf) | RP2350 (resumen, legado) | — |
| [`reference/datasheets/stm32n657-ds14791-rev10.pdf`](reference/datasheets/stm32n657-ds14791-rev10.pdf) | **STM32N657 — DS14791 Rev 10, la vigente** | Cerebro (D1), micro de la Voz, mago e interfaz. **Es la que se cita** |
| [`reference/datasheets/stm32n6-an5967-rev5.pdf`](reference/datasheets/stm32n6-an5967-rev5.pdf) | **AN5967 Rev 5** — desarrollo hardware STM32N6 | Tabla 6 (p. 13): piezas y desacoplo por pin, con la bobina del SMPS y su snubber. §14.3: reglas de desacoplo en BGA |
| [`reference/datasheets/stm32n657-ds14791-rev2.pdf`](reference/datasheets/stm32n657-ds14791-rev2.pdf) | STM32N657 — Rev 2 **(superada, no citar)** | Se conserva porque hay citas históricas a sus tablas. **Renumeró**: `IDDCORE` era la 28 y es la 33; y añadió `IDDSMPS` (39), que en Rev 2 no existía |
| [`reference/datasheets/ad5686r-revf-2024-11.pdf`](reference/datasheets/ad5686r-revf-2024-11.pdf) | AD5686R/85R/84R — DAC cuádruple 16 bits | CV de tono; el `RSTSEL` que sostiene el camino de silencio |
| [`reference/datasheets/ssi2164-rev3.4-2023-02.pdf`](reference/datasheets/ssi2164-rev3.4-2023-02.pdf) | **SSI2164 Rev 3.4** — VCA cuádruple exponencial | Los VCA de voz y de resonancia, 12 encapsulados. `consumo_total_budget.py:63` cita su p. 5 (±8,4 mA con 1,0 mA de mode current) y la ley de −33 mV/dB sale de su p. 4, «Control Port» |
| [`reference/datasheets/ad75019-revf-2026-07.pdf`](reference/datasheets/ad75019-revf-2026-07.pdf) | **AD75019 Rev F** — crosspoint analógico 16×16 | Los dos en cadena de la bahía asignable. `core/src/bahia_serie.rs:30` cita su tabla 3 (p. 4) para el sentido del `PCLK` dentro de los 512 bits |
| [`reference/datasheets/24aa1025-ds21941h-2011.pdf`](reference/datasheets/24aa1025-ds21941h-2011.pdf) | **24AA1025 — DS21941H** — EEPROM I²C de 128 KB | La memoria del módulo de Voz. `core/src/memoria.rs` existe por su **costura**: no es un chip de 128 KB, son dos de 64 con dos direcciones I²C |
| [`reference/datasheets/lm2941-snvs770i-2015-01.pdf`](reference/datasheets/lm2941-snvs770i-2015-01.pdf) | **LM2941 — SNVS770I** — pre-regulador LDO ajustable positivo | El pre-regulador del +12 V de la cascada (`docs/modules/01-power-supply.md:33`). La v4 le añade trabajo: su `ON/OFF` **activo-bajo** (< 0,8 V habilita, p. 11) es medio secuenciador, sus 26 V de entrada máxima son quien aguanta el clamp de OVP de la SMPS, y su Fig. 9 «Ripple Rejection» es lo único que dice qué hace a 65 kHz |
| [`reference/datasheets/lm2991-snvs099i-2016-10.pdf`](reference/datasheets/lm2991-snvs099i-2016-10.pdf) | **LM2991 — SNVS099I** — el espejo negativo | Pre-regulador del −12 V. Ojo con la asimetría que decide el circuito del secuenciador: su `ON/OFF` es **activo-alto y deshabilita** (> 2,4 V, p. 9), al revés que el LM2941. Su curva de rechazo es la Fig. 8 |
| [`reference/datasheets/lt3045-rev-d.pdf`](reference/datasheets/lt3045-rev-d.pdf) | **LT3045 Rev D** — LDO ultra-bajo-ruido positivo | La pareja en paralelo que fija el +12,000 V. De aquí sale el 0,8 µVrms de la cascada y el PSRR de **76 dB a 1 MHz** de portada, **condicionado al headroom** de 1,1 V que no puede bajar |
| [`reference/datasheets/lt3094-rev-b.pdf`](reference/datasheets/lt3094-rev-b.pdf) | **LT3094 Rev B** — el espejo negativo | La pareja del −12,000 V. **74 dB a 1 MHz**, con la misma condición de headroom |
| [`reference/datasheets/meanwell-irm-20-spec-2025-11-21.pdf`](reference/datasheets/meanwell-irm-20-spec-2025-11-21.pdf) | **Mean Well IRM-20** (spec 2025-11-21) — SMPS encapsulada de 20 W | `PS1` y `PS2` (los ±15 V crudos que entran a la cascada) y `PS5` (+5 V de rack). Su p. 2 da rizado, rendimiento e inrush; su p. 3, la curva de derating —**100 % hasta 50 °C**— que gobierna la térmica del listón |
| [`reference/datasheets/meanwell-irm-45-spec-2025-11-21.pdf`](reference/datasheets/meanwell-irm-45-spec-2025-11-21.pdf) | **Mean Well IRM-45** (spec 2025-11-21) — SMPS encapsulada de 45 W | `PS3`/`PS4` (±12 V de rack) y `PS6` (+5 V digital, 8 A). Es la que **gana** el puesto de `PS4`: entra en *hiccup* al 115 % y no al 105 % |
| [`reference/datasheets/stm32h750-ds12556-rev8.pdf`](reference/datasheets/stm32h750-ds12556-rev8.pdf) | STM32H750 — DS12556 Rev 8 **(clase retirada, no citar como contrato)** | Historia rotulada de la decisión: `micro_budget.py:49-55` cita su Tabla 4 (pp. 39-40) y su p. 2. Cayó frente al N657 el 2026-08-26 |
| [`reference/datasheets/ra8m1-r01ds0417-rev110.pdf`](reference/datasheets/ra8m1-r01ds0417-rev110.pdf) | Renesas RA8M1 — R01DS0417 Rev 1.10 | **El retorno declarado**, no una pieza del diseño vigente: si el N657 cayera en sus puertas, el motor digital vuelve aquí (`micro_budget.py:271`) |
| [`reference/datasheets/meanwell-irm-15-spec-2025-11-21.pdf`](reference/datasheets/meanwell-irm-15-spec-2025-11-21.pdf) | Mean Well IRM-15 **(pierde su puesto en la v4)** | Era el +5 V digital «montada fuera de esta placa» (spec v2 §7) y la v4 lo pasa a la IRM-45-5. Se queda porque su codo de derating a **+50 °C** es una lectura que la spec del chasis ya citaba desde el 2026-08-19 |
| [`reference/datasheets/meanwell-irm-30-spec-2026-04-03.pdf`](reference/datasheets/meanwell-irm-30-spec-2026-04-03.pdf) | Mean Well IRM-30 **(descartada, historia de la decisión)** | Era `PS4` en el primer borrador de la v4. Cayó por su p. 2: `OVERLOAD` «105 ~ 160 %» la mete en *hiccup* a **2,63 A** contra los 2,5 A declarados —menos que el arranque de un módulo digital— y la IRM-45 aguanta hasta el 115 % |

Cinco de esas filas llevaban desde siempre sin entrar al índice aunque los
ficheros sí estaban versionados, y las **ocho** de la fuente v4 entraron al
historial el 2026-09-03, el mismo día que esta regla. Daba igual mientras la
carpeta se clonara entera; deja de dar igual el día que se ignora, que es hoy.

Desde el 2026-09-03 la carpeta está **ignorada por defecto** (`.gitignore`).
Las de arriba siguen versionadas porque están declaradas una a una; cualquier
hoja nueva se queda en disco y se anota abajo. Lo que forzó la regla fue el
RM0486: 94 MB en un solo fichero, el 28 % de lo que pesa el repositorio entero.

### En disco, no versionadas

Se bajan del fabricante, y **la revisión es parte de la cita**: sin ella un
número de tabla no significa nada. Esta tabla es el único registro de cuál es
la buena, así que una entrada sin URL y sin revisión es una entrada rota.

| Fichero | Documento | De dónde sale | Para qué |
|---|---|---|---|
| `reference/datasheets/stm32n6-rm0486-rev4.pdf` | **RM0486 Rev 4** (mayo 2026), 4.669 pp. — manual de referencia del STM32N6x5/x7xx | [st.com](https://www.st.com/resource/en/reference_manual/rm0486-stm32n647657xx-armbased-32bit-mcus-stmicroelectronics.pdf) | Los registros. Es la fuente de los bits de RCC y del PHY del USB del N657 — lo que le falta a `embassy-stm32` para que el cerebro tenga puerto (#250) |
| `reference/datasheets/lt1963a-rev-g-2021-02.pdf` | **LT1963A Rev. G** (02/21, pie de la p. 28) — LDO 1,5 A ajustable, bajo ruido | [analog.com](https://www.analog.com/media/en/technical-documentation/data-sheets/1963aff.pdf) | Candidato a sustituir al **LM2941** en `U1` (opción **b** del §4.2 de la fuente v4). Lo que decide: `ADJ Pin Voltage` **1,174–1,246 V sobre temperatura** y `Dropout Voltage` **0,55 V máx a 1,5 A** — las dos cifras que el LM2941 no puede batir. Su `SHDN` sirve al secuenciador de D-F4 y sus ±20 V de `IN` cubren los 15,67 V del peor caso alto. **5-lead TO-220**, o sea que el tab sigue contra la pared y `chasis_to220_*` no se mueve |
| `reference/datasheets/mic29152-ds20005685a-2016.pdf` | **MIC29152 — DS20005685A** (2016) — LDO 1,5 A ajustable de alta precisión | [microchip.com](https://ww1.microchip.com/downloads/en/devicedoc/20005685a.pdf) | El otro candidato para `U1`. `Reference Voltage` **1,203–1,277 V** (Note 8) y `Dropout Voltage` **600 mV máx a 1,5 A** (220 mV típico a 750 mA, sin máximo publicado ahí). Trae `EN` y un **`FLG`** que avisa de salida fuera de regulación — telemetría gratis que el LT1963A no da |

**Dos avisos sobre estas dos, y los dos son de los que renumeran tablas:**

1. **La DS20005685A no es la última.** Existe una **DS20005685B** (2016–2019),
   y esta tabla existe precisamente porque *«la Rev 2 contra la Rev 10 del
   DS14791 ya nos renumeró una tabla entera»*. Ningún número del MIC29152 debe
   entrar en un papel sin comprobar antes si la B lo mueve.
2. **La DS20005685A se contradice consigo misma sobre el encapsulado.** Su
   p. 1 dice *«The 1.5A, adjustable output MIC29152 is available in a 5-pin
   power D-Pak (TO-252) package»* y el diagrama de la p. 2 dibuja
   *«MIC29152/302/502 5-Lead TO-220 Adjustable Voltage (T)»* con TAB y el
   pinout entero (`1 EN`, `2 IN`, `TAB 3 GND`, `4 OUT`, `5 ADJ`). **Mientras el
   disipador sea la pared del chasis, sin TO-220 con TAB la pieza no sirve**, y
   eso se cierra con el sufijo de pedido, no leyendo la hoja.

Y una que **ninguna de las dos garantiza**: el dropout a los **710 mA** de la
cascada. El LT1963A salta de 500 mA (0,35 V) a 1,5 A (0,55); el MIC29152
publica el típico a 750 mA y el máximo sólo a 1,5 A; el LM2991 da 0,1 A y 1 A y
nada en medio. Quien las use toma la cota de la corriente **mayor**, que es la
única honesta.

Ojo con la diferencia: la **DS14791** dice qué patillas y cuánta corriente; el
**RM0486** dice qué bit de qué registro. Para escribir un driver hace falta el
segundo, y es el que hasta hoy no estaba.

## Recursos complementarios recomendados

- **MIDI Specification** — https://www.midi.org/specifications
- **mido** (Python MIDI) — https://mido.readthedocs.io/
- **KiCad EDA** — https://www.kicad.org/
- **ngspice / LTspice** para simulaciones de los módulos analógicos.
- **Music From Outer Space** (Ray Wilson) — diseños de referencia de
  sintetizadores DIY: http://musicfromouterspace.com/
- **Look Mum No Computer** — recursos prácticos de DIY synth.
- **Modular Grid** — base de datos de módulos Eurorack para inspiración de
  paneles e interconexión: https://www.modulargrid.net/
