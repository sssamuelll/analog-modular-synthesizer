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

Las versionadas, enteras. (Decía «las veinte» y con D-F9 entraron tres más;
el número se quita en vez de corregirse, porque una cuenta a mano en la
cabecera de una tabla se desincroniza en la siguiente hoja que baje.) Están en
el historial porque los presupuestos
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
| [`reference/datasheets/stm32n6-es0620-rev5.pdf`](reference/datasheets/stm32n6-es0620-rev5.pdf) | **ES0620 Rev 5** (agosto 2026) — errata del STM32N6x5/x7xx, revisiones de silicio Z, B y X | La lista de lo que el silicio NO hace como dice el RM0486. Diecisiete periféricos con limitación y **el SPI no está entre ellos**. §2.2.1: el prescaler de APB no funciona, pclk = hclk siempre (#363). §2.2.22: diez selectores de reloj a su default antes de un reset por software (#364). §2.15.1: los pines OTGx_VBUS no sirven, solo queda el override por GPIO (#350) |
| [`reference/datasheets/stm32n6-nucleo-um3417-rev3.pdf`](reference/datasheets/stm32n6-nucleo-um3417-rev3.pdf) | **UM3417 Rev 3** (agosto 2025) — manual de la NUCLEO-N657X0-Q (MB1940) | La placa que mide el J2 (#231). Tabla 13: el morpho CN3/CN15, lo único soldado de fábrica. Tabla 12: el Arduino. Tabla 16: PC3 y PC4 son del ST-LINK, que es lo que descarta SPI1. De ahí sale el montaje de dos extremos del J2 en una sola placa |
| [`reference/datasheets/stm32n657-ds14791-rev2.pdf`](reference/datasheets/stm32n657-ds14791-rev2.pdf) | STM32N657 — Rev 2 **(superada, no citar)** | Se conserva porque hay citas históricas a sus tablas. **Renumeró**: `IDDCORE` era la 28 y es la 33; y añadió `IDDSMPS` (39), que en Rev 2 no existía |
| [`reference/datasheets/ad5686r-revf-2024-11.pdf`](reference/datasheets/ad5686r-revf-2024-11.pdf) | AD5686R/85R/84R — DAC cuádruple 16 bits | CV de tono; el `RSTSEL` que sostiene el camino de silencio |
| [`reference/datasheets/ssi2164-rev3.4-2023-02.pdf`](reference/datasheets/ssi2164-rev3.4-2023-02.pdf) | **SSI2164 Rev 3.4** — VCA cuádruple exponencial | Los VCA de voz y de resonancia, 12 encapsulados. `consumo_total_budget.py:63` cita su p. 5 (±8,4 mA con 1,0 mA de mode current) y la ley de −33 mV/dB sale de su p. 4, «Control Port» |
| [`reference/datasheets/ad75019-revf-2026-07.pdf`](reference/datasheets/ad75019-revf-2026-07.pdf) | **AD75019 Rev F** — crosspoint analógico 16×16 | Los dos en cadena de la bahía asignable. `core/src/bahia_serie.rs:30` cita su tabla 3 (p. 4) para el sentido del `PCLK` dentro de los 512 bits |
| [`reference/datasheets/24aa1025-ds21941h-2011.pdf`](reference/datasheets/24aa1025-ds21941h-2011.pdf) | **24AA1025 — DS21941H** — EEPROM I²C de 128 KB | La memoria del módulo de Voz. `core/src/memoria.rs` existe por su **costura**: no es un chip de 128 KB, son dos de 64 con dos direcciones I²C |
| [`reference/datasheets/lm2941-snvs770i-2015-01.pdf`](reference/datasheets/lm2941-snvs770i-2015-01.pdf) | LM2941 — SNVS770I **(retirado con D-F8, 2026-09-04; no citar como pieza viva)** | Fue el pre-regulador del +12 V hasta que `margen_budget.py` lo dejó en **−293 mV de margen** por su dropout de 0,8 V a 1 A y su referencia de ±5 % en temperatura (p. 6). Se conserva como historia del hueco |
| [`reference/datasheets/lm2991-snvs099i-2016-10.pdf`](reference/datasheets/lm2991-snvs099i-2016-10.pdf) | LM2991 — SNVS099I **(retirado con D-F9, 2026-09-06; no citar como pieza viva)** | Fue el pre-regulador del −12 V hasta que `margen_budget.py` lo dejó en **−170 mV de margen** y no había forma de arreglarlo sin cambiarlo: su ventana de referencia (0,640 V) más su dropout garantizado (1,00 V a 1 A) suman 1,640 y el presupuesto son 1,470. Se conserva porque la historia del hueco lo cita por página, y porque su Fig. 8 es la que se comparó contra la G41 del LT3015 |
| [`reference/datasheets/lt1963a-rev-g-2021-02.pdf`](reference/datasheets/lt1963a-rev-g-2021-02.pdf) | **LT1963A Rev. G** (02/21) — LDO 1,5 A ajustable positivo | `U1` desde **D-F8**. Lo que decide: `ADJ Pin Voltage` **1,174–1,246 V sobre temperatura** y `Dropout Voltage` **0,55 V máx a 1,5 A** (p. 5), `GND Pin Current` **120 mA máx a 1,5 A en temperatura** (p. 5, #343) y curva `Ripple Rejection` **G31 de la p. 11**. Su `IN Pin Voltage` es **±20 V** (p. 2), protegido en la v5 por el tope `TPS26630` + `SMBJ16A` (M3 / #334) |
| [`reference/datasheets/lt3015-rev-b.pdf`](reference/datasheets/lt3015-rev-b.pdf) | **LT3015 rev B** — LDO 1,5 A ajustable negativo, bajo ruido | `U2` desde **D-F9**. Las cuatro cifras que lo eligieron, todas de tabla: `ADJ Pin Voltage` **−1,196/−1,244 V** en la fila `l` —que en Linear es todo el rango de temperatura, y aquí trae dentro línea y carga—, `Dropout Voltage` **0,68 V máx a 1,5 A en DD-PAK/TO-220** (p. 5), `IN Pin Voltage` **±33 V** (p. 2) y un `SHDN` que **habilita en ALTO** como el del LT1963A (p. 6), con lo que vuelve el hilo único y muere el inversor del #323. Margen **+536 mV**. **Pedir el grado `I`** (`LT3015IT#PBF`): la Nota 9 sólo garantiza al `E` de 0 a 125 °C. Su curva de rechazo es la **G41 de la p. 11**, y la traza que vale exige `COUT` = 47 µF **y** `CFF` = 10 nF |
| [`reference/datasheets/mic29152-ds20005685b-2019.pdf`](reference/datasheets/mic29152-ds20005685b-2019.pdf) | **MIC29152 — DS20005685B** (2016–2019) — LDO 1,5 A ajustable de alta precisión | **No está en la placa**: fue candidato para `U1` en la **#334** porque su `Maximum Operating Input Voltage` de **+26 V** (p. 4) aguantaba el OVP de PS1 en v4; en la v5 M3 protege al `LT1963A` con tope delante |
| [`reference/datasheets/lt3045-rev-d.pdf`](reference/datasheets/lt3045-rev-d.pdf) | **LT3045 Rev D** — LDO ultra-bajo-ruido positivo | La pareja en paralelo que fija el +12,000 V. De aquí sale el 0,8 µVrms de la cascada y el PSRR de **76 dB a 1 MHz** de portada, **condicionado al headroom** de 1,1 V que no puede bajar |
| [`reference/datasheets/lt3094-rev-b.pdf`](reference/datasheets/lt3094-rev-b.pdf) | **LT3094 Rev B** — el espejo negativo | La pareja del −12,000 V. **74 dB a 1 MHz**, con la misma condición de headroom |
| [`reference/datasheets/meanwell-irm-20-spec-2025-11-21.pdf`](reference/datasheets/meanwell-irm-20-spec-2025-11-21.pdf) | Mean Well IRM-20 (spec 2025-11-21) **(retirada en la v5 con D-V1)** | `PS1`, `PS2` y `PS5` en la v4; se conserva porque `v4/` sigue versionada y sus presupuestos citan sus páginas |
| [`reference/datasheets/meanwell-irm-45-spec-2025-11-21.pdf`](reference/datasheets/meanwell-irm-45-spec-2025-11-21.pdf) | Mean Well IRM-45 (spec 2025-11-21) **(retirada en la v5 con D-V1)** | `PS3`, `PS4` y `PS6` en la v4; se conserva como contrato de `v4/` |
| [`reference/datasheets/stm32h750-ds12556-rev8.pdf`](reference/datasheets/stm32h750-ds12556-rev8.pdf) | STM32H750 — DS12556 Rev 8 **(clase retirada, no citar como contrato)** | Historia rotulada de la decisión: `micro_budget.py:49-55` cita su Tabla 4 (pp. 39-40) y su p. 2. Cayó frente al N657 el 2026-08-26 |
| [`reference/datasheets/ra8m1-r01ds0417-rev110.pdf`](reference/datasheets/ra8m1-r01ds0417-rev110.pdf) | Renesas RA8M1 — R01DS0417 Rev 1.10 | **El retorno declarado**, no una pieza del diseño vigente: si el N657 cayera en sus puertas, el motor digital vuelve aquí (`micro_budget.py:271`) |
| [`reference/datasheets/meanwell-irm-15-spec-2025-11-21.pdf`](reference/datasheets/meanwell-irm-15-spec-2025-11-21.pdf) | Mean Well IRM-15 **(pierde su puesto en la v4)** | Era el +5 V digital «montada fuera de esta placa» (spec v2 §7) y la v4 lo pasa a la IRM-45-5. Se queda porque su codo de derating a **+50 °C** es una lectura que la spec del chasis ya citaba desde el 2026-08-19 |
| [`reference/datasheets/meanwell-irm-30-spec-2026-04-03.pdf`](reference/datasheets/meanwell-irm-30-spec-2026-04-03.pdf) | Mean Well IRM-30 **(descartada, historia de la decisión)** | Era `PS4` en el primer borrador de la v4. Cayó por su p. 2: `OVERLOAD` «105 ~ 160 %» la mete en *hiccup* a **2,63 A** contra los 2,5 A declarados —menos que el arranque de un módulo digital— y la IRM-45 aguanta hasta el 115 % |
| [`reference/datasheets/traco_thn30wi.pdf`](reference/datasheets/traco_thn30wi.pdf) | **TRACO Power THN 30WI** (rev. 2025-07-17) — DC-DC aislado 30 W 4:1 | `THN 30-2422WI`: ±12 V de rack (±1,25 A, 89 % típ., 275 kHz típ., 1600 VDC, p. 1–4) en la fuente v5 |
| [`reference/datasheets/traco_thn20wi.pdf`](reference/datasheets/traco_thn20wi.pdf) | **TRACO Power THN 20WI** (rev. 2026-04-13) — DC-DC aislado 20 W 4:1 | `2 × THN 20-2413WI` (15 V, 1,33 A, recortados a 15,5 V, 89 % típ., 330 kHz típ.) para los crudos ±15,5 V de la cascada v5 (D-V3), y candidato `THN 20-2411WI` para +5 V digital (M1) |
| [`reference/datasheets/mornsun_urb_ymd20wr3.pdf`](reference/datasheets/mornsun_urb_ymd20wr3.pdf) | **Mornsun URB2405YMD-20WR3** (rev. 2025.09.30-A/6) — DC-DC aislado 20 W 4:1 | +5 V digital aislado (M1, 4 A, **88 % mín. / 90 % típ.** en p. 1, 300 kHz típ., 1500 VDC en p. 3). Es el único módulo 1"×1" que publica **eficiencia mínima garantizada** en hoja (cierra H-CENSO-ETA-DIGITAL) |
| [`reference/datasheets/recom_rpmb20.pdf`](reference/datasheets/recom_rpmb20.pdf) | **RECOM RPMB5.0-2.0** (rev. 2023-06) — buck DOSA-4 5 V / 2 A | Candidato para +5 V de rack (9–36 V entrada, 88 % típ. a 24 V, 50 mVp-p máx., p. 1–3) |
| [`reference/datasheets/mornsun_k78_t1000r3.pdf`](reference/datasheets/mornsun_k78_t1000r3.pdf) | **Mornsun K7805T-1000R3** (rev. 2025.06.03-A/4) — buck SMD 5 V / 1 A | +5 V de rack en la fuente v5 (8–36 V entrada, 85 % típ. a Vin máx. / 93 % a Vin mín., 520 kHz típ., 75 mVp-p máx., derating 100 % hasta 60 °C para Vin ≤ 26 V, p. 1–3) |
| [`reference/datasheets/ae-TE90-datasheet.pdf`](reference/datasheets/ae-TE90-datasheet.pdf) | **Advanced Energy / SL Power TE90** (rev. 2023) — ladrillo externo 90 W 24 V | Ladrillo 24 V (D-V1): `TE90A2403F01` / opción `49` (4 pines KPP-4P, p. 6), 90 W hasta 40 °C y 82,5 W a 45 °C (p. 3), hiccup auto-recuperable en sobrecarga, corto y OVP, OTP auto-recuperable (p. 2) |
| [`reference/datasheets/ae-TE90-CB-cert.pdf`](reference/datasheets/ae-TE90-CB-cert.pdf) | **CB Test Certificate DK-59985-M1-UL** — TE90 | Certificado CB IEC 60950-1 + A1 + A2 (Tma = 40 °C a carga nominal, p. 11) |
| [`reference/datasheets/ae-TE90-DEMKO-EN62368.pdf`](reference/datasheets/ae-TE90-DEMKO-EN62368.pdf) | **Certificado DEMKO D-08914** — TE90 EN 62368-1 | Certificado EN 62368-1:2014/A11:2017 de la familia TE90 |
| [`reference/datasheets/meanwell-GST120A-spec.pdf`](reference/datasheets/meanwell-GST120A-spec.pdf) | **Mean Well GST120A24-R7B** (rev. 2025-09-09) — ladrillo 120 W 24 V | Ladrillo 24 V / 5 A con conector `R7B` (`KPPX-4P`, pines 1,4 = +V, 2,3 = −V, p. 2), 100 % (120 W) a 45 °C con 230 VAC (p. 3), −V unido a AC FG (p. 3) |
| [`reference/datasheets/meanwell-GSM120A-spec.pdf`](reference/datasheets/meanwell-GSM120A-spec.pdf) | **Mean Well GSM120A24-R7B** (rev. 2025-09-09) — ladrillo médico 120 W 24 V | Ladrillo 24 V / 5 A 2×MOPP con −V flotante respecto a FG (p. 3), 90 % (108 W) a 45 °C (p. 3), fuga < 100 µA (p. 2) |
| [`reference/datasheets/kycon_KPJX-PM-4S.pdf`](reference/datasheets/kycon_KPJX-PM-4S.pdf) | **Kycon KPJX-PM-4S** (Rev. A10) — receptáculo mini-DIN 4 pines de panel | Conector de entrada 24 V en chasis (48 VDC, 7,5 A por pin, 30 mΩ máx. de contacto, escudo a panel) |
| [`reference/datasheets/kycon_KPPX-4P.pdf`](reference/datasheets/kycon_KPPX-4P.pdf) | **Kycon KPPX-4P** (Rev. A12) — clavija mini-DIN 4 pines («R7B») | Clavija aérea del cordón de 24 V (7,5 A, 30 mΩ máx., bloqueo snap-and-lock) |
| [`reference/datasheets/tps2663.pdf`](reference/datasheets/tps2663.pdf) | **TI TPS2663x — SLVSE94G** (julio 2025) — eFuse 4,5–60 V, 6 A | Vigilante de entrada 24 V (`M5`) y tope OVP del crudo positivo delante de `U1` (`M3` / #334). `RON` = **53 mΩ máx.** en −40..125 °C (p. 7), `V(OVPR)` = **1,176–1,224 V** (p. 6), corte por OVP en **8,5–14 µs** (p. 8) |
| [`reference/datasheets/lm74502.pdf`](reference/datasheets/lm74502.pdf) | **TI LM74502 — SNOSDE5A** (mayo 2023) — controlador de interruptor / bloqueo de polaridad | Bloqueo de polaridad inversa de ±65 V (H-V5-INVERSION) en la entrada de 24 V |
| [`reference/datasheets/bourns_smbj.pdf`](reference/datasheets/bourns_smbj.pdf) | **Bourns SMBJ** (rev. 07/24) — TVS 600 W SMB | `SMBJ16A` (`V_WM` = 16,0 V, `V_BR` = 17,8–19,7 V, `V_C` = 26,0 V a 23,1 A, p. 2) en `U1 IN` para amortiguar la cola inductiva del LC tras el corte del `TPS26630` (#334) y `SMBJ26A` en la entrada de 24 V |
| [`reference/datasheets/bourns_sf1206f.pdf`](reference/datasheets/bourns_sf1206f.pdf) | **Bourns SF-1206F** (rev. 10/25) — fusible SMD rápido 1206 | Fusible rápido de respaldo (65 VDC, p. 1–2) |
| [`reference/datasheets/tl431.pdf`](reference/datasheets/tl431.pdf) | **TI TL431BI — SLVS543S** (junio 2025) — referencia ajustable en derivación | Referencia de disparo de los crowbars `D-F6` y del detector de ventana `D-F4`: `V_ref` = **2483–2507 mV** a 25 °C, `V_I(dev)` = **34 mV máx.** en −40..85 °C, `I_ref` = **4 µA máx.** (p. 13) |
| [`reference/datasheets/msp430fr2111.pdf`](reference/datasheets/msp430fr2111.pdf) | **TI MSP430FR2111 — SLASE78E** (mayo 2021) — MCU ultra-bajo-consumo con FRAM | Decisor del vigilante `M5`: **3,75 KB FRAM** no volátil con $10^{15}$ ciclos (p. 7, 35) para conservar cupo de reintentos y bandera de abandono sin energía, SVS en **1,71–1,99 V** (p. 20) |
| [`reference/datasheets/nxp-bt151-500r.pdf`](reference/datasheets/nxp-bt151-500r.pdf) | **NXP BT151-500R** (Rev. 05, marzo 2009) — tiristor SCR 12 A RMS, TO-220AB | SCR de los tres crowbars de rack de **D-F6** (#340): `I_TSM` = **120 A**, $I^2t$ = **72 $\text{A}^2\text{s}$** (p. 3), `I_GT` = **15 mA máx.**, `I_L` = **40 mA máx.**, `I_H` = **20 mA máx.** a 25 °C (~36 mA a −40 °C, Fig. 10 p. 7), `dV_D/dt` = **200 V/µs mín.** con `R_GK` = 100 Ω (p. 6) |
| [`reference/datasheets/ti-lm393b.pdf`](reference/datasheets/ti-lm393b.pdf) | **TI LM393B — SLCS005AH** (noviembre 2025) — doble comparador 3–36 V | Detector analógico de ventana de **D-F4** (`M4`, `secuencia_budget.py`): `V_IO` = **±2,5 mV máx.** a 25 °C (**±4,0 mV máx.** en −40..85 °C), `I_B` = **−50 nA máx.**, salida colector abierto (`V_OL` = 400 mV máx. a 4 mA, p. 6) para el hilo único wired-AND |

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
| `reference/datasheets/mic29152-ds20005685a-2016.pdf` | MIC29152 — DS20005685A (2016) **(superada por la B, que sí está versionada arriba; no citar)** | [microchip.com](https://ww1.microchip.com/downloads/en/devicedoc/20005685a.pdf) | El otro candidato para `U1`. `Reference Voltage` **1,203–1,277 V** (Note 8) y `Dropout Voltage` **600 mV máx a 1,5 A** (220 mV típico a 750 mA, sin máximo publicado ahí). Trae `EN` y un **`FLG`** que avisa de salida fuera de regulación — telemetría gratis que el LT1963A no da |

**Los dos avisos de esta pareja, y los dos están resueltos desde el
2026-09-06** — la **DS20005685B** bajó al árbol con D-F9
([`reference/datasheets/mic29152-ds20005685b-2019.pdf`](reference/datasheets/mic29152-ds20005685b-2019.pdf)),
que es lo que este aviso llevaba pidiendo desde el 04-09:

1. **La B no mueve los números que citamos.** `Reference Voltage` sigue siendo
   **1,203–1,277 V** con la misma Note 8 —que ahora se puede leer entera:
   *«VREF ≤ VOUT ≤ (VIN – 1V), 2.3V ≤ VIN ≤ 26V, 10 mA < IL ≤ IFL,
   TJ ≤ TJMAX»*, o sea que esos 74 mV **incluyen línea, carga y
   temperatura**— y `Maximum Operating Input Voltage` sigue en **+26 V**
   (p. 4). Comprobado contra la A, no supuesto.
2. **La B ya no se contradice sobre el encapsulado.** Donde la A decía sólo
   *«5-pin power D-Pak (TO-252)»* en su p. 1 mientras dibujaba un TO-220 en la
   p. 2, la B dice **«5-pin TO-220 and surface mount TO-263»** y trae los
   diagramas de *5-Lead TO-220 Adjustable Voltage (T)* y *Adjustable with
   Flag (T)*. Mientras el disipador sea la pared del chasis eso importa, y
   sigue cerrándose con el sufijo de pedido.

**Y por qué esta pareja vuelve a estar viva:** el `Maximum Operating Input
Voltage` de **+26 V** del MIC29152 es exactamente lo que el LT1963A no tiene
(±20 V contra los 20,25 del OVP de PS1), así que el otro candidato de aquella
búsqueda es hoy la salida más obvia de la **#334**. La decisión no está tomada.

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
