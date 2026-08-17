# Design Notes — PSU v2

## §1 Puertas de datasheet

### §1.1 LM2941CT

Fuente: TI, `LM2941, LM2941C`, doc. SNVS770I (June 1999–Revised January 2015),
`https://www.ti.com/lit/ds/symlink/lm2941.pdf`. Descargado con `curl` (WebFetch no
hizo falta, bajó a la primera).

- [x] **Dropout máximo garantizado**: **1.0 V a IOUT = 1 A**, sobre todo el rango
  de temperatura (LM2941CT: 0–125 °C) — tabla §6.6 "Electrical Characteristics:
  LM2941CT, LM2941CS", p.6 (idéntico en §6.5 para T/S/LD, p.5). A 100 mA: MAX
  200 mV (misma tabla). **No existe un dato garantizado a 650 mA** — el DS solo
  da 100 mA y 1 A. Hay una curva típica por temperatura para 1 A/500 mA/100 mA
  (Fig. 2, p.7), pero es típica, no garantizada. Por el lado conservador (el
  dropout crece monótonamente con la corriente, confirmado en esa misma curva):
  **se usa el MAX de 1 A = 1.0 V como cota aplicable a 650 mA.**
- [x] **VREF y fórmula de VOUT**: VREF **MIN 1.211 / TYP 1.275 / MAX 1.339 V**
  (5 mA ≤ IOUT ≤ 1 A, sobre temperatura completa) — tabla §6.6, p.6. Fórmula real
  del DS (§8.2.2.2, p.13): **VOUT = VREF × (R1+R2)/R1 = VREF × (1 + R2/R1)**.
  **Ojo**: la fórmula esperada en el brief tenía R1 y R2 invertidos — es `1+R2/R1`,
  no `1+R1/R2`. R1 es la resistencia inferior (a masa), R2 la superior (a OUT).
- [x] **Tab del TO-220-5 (KC)**: **GND**. El pin-out del TO-263 (KTT), p.3,
  rotula literalmente "TAB IS GND" y la tabla de pines confirma pin 3 = GND en
  ese package. §10.4.1 (p.17): "The TAB... connected to the die substrate...
  and to device pin 3 [GND]... The TAB must not be connected to any potential
  other than ground." El layout example del TO-220 (Fig. 22, p.15) muestra el
  tab cosido al plano de GND. **No hace falta mica** en el LM2941 (a diferencia
  del LM2991, ver §1.2).
- [x] **Ventana de ESR y C_OUT mínimo**: §8.1 (p.12): COUT ≥ 22 µF, ESR entre
  **100 mΩ y 1 Ω**. §8.2.2.1 (p.13), más permisivo con tantalio: ESR 0.01–5 Ω si
  es tantalio; si es cerámico X5R/X7R 22 µF, se necesita **resistencia serie de
  0.1–1 Ω** para simular el ESR. Fig. 13 (p.9) da la ventana gráfica. **Fija
  C17: no puede ser un MLCC solo** (2–20 mΩ típico, por debajo del piso de
  100 mΩ) — o tantalio, o MLCC + serie R.
- [x] **Corriente del pin ADJ**: el DS **no da un número garantizado en tabla**
  — solo texto en §8.2.2.2 (p.13): "Using 1 kΩ for R1 will ensure that the bias
  current error from the adjust pin will be negligible... R1 higher than 10 kΩ
  may cause the output voltage to shift." Con R1 = 1 kΩ y VREF ≈ 1.275 V, la
  corriente del divisor es ≈ 1.275 mA (~1.2 mA, coincide con el brief); el error
  del ADJ se declara "negligible" de forma cualitativa, sin cifra garantizada
  que citar.
- [x] **Pin ON/OFF**: activo-bajo habilita. §7.4.1 (p.11): "the ON/OFF pin
  voltage must fall below the minimum ON/OFF(ON) voltage threshold (0.8 V) to
  enable... If the ON/OFF function is not needed this pin can be connected
  directly to Ground." Tabla §6.6 (p.6): threshold ON, MAX garantizado = 0.8 V;
  threshold OFF, MIN garantizado = 2 V. **Atar a GND = siempre-encendido**,
  garantizado sobre todo el rango (0 V < 0.8 V).

### §1.2 LM2991T

Fuente: TI, `LM2991`, doc. SNVS099I (May 1999–Revised October 2016),
`https://www.ti.com/lit/ds/symlink/lm2991.pdf`. Descargado con `curl`.

- [x] **Dropout máx. garantizado**: **1.0 V a IOUT = 1 A**, sobre todo el rango
  de temperatura (−40 a 125 °C) — tabla §6.5 "Electrical Characteristics", p.5
  (TYP 0.6 V, MAX 0.8 V a 25 °C; MAX 1 V sobre temperatura). A 0.1 A: MAX 0.3 V
  sobre temperatura. **Igual que el LM2941: no hay dato garantizado a 650 mA.**
  Fig. 1 (p.6) confirma la monotonía (curvas típicas a −55/25/125 °C). Por el
  lado conservador: **se usa el MAX de 1 A = 1.0 V para 650 mA.**
- [x] **VREF y fórmula**: VREF **MIN −1.234 / TYP −1.210 / MAX −1.186 V** a
  25 °C (5 mA ≤ IOUT ≤ 1 A); sobre temperatura completa (−40 a 125 °C): **MIN
  −1.27 / MAX −1.15 V** — tabla §6.5, p.5. Fórmula completa (§8.2.2.4, p.13):
  **VOUT = VREF × (1 + R2/R1) − (IADJ × R2)**, con VREF = −1.21 V. La portada
  (p.1) da la versión simplificada sin el término IADJ; §8.2.2.4 aclara que la
  corriente del ADJ es ≈ 60 nA y que con resistores < 100 kΩ el error es
  despreciable (ejemplo del propio DS: R2 = 100 kΩ, VOUT = −5 V → error de
  0.16 % ignorando IADJ).
- [x] **Tab: MUERDE — confirmado.** Pin-out p.3 (TO-220 KC/NDH y TO-263 KTT):
  el tab está rotulado **"Input"**, y la tabla de pines lo deja explícito: "TAB
  — I: Negative Input voltage. Internally connected directly to the device pin
  3 (IN)... Do NOT connect the thermal tab to ground." No es GND, es la entrada
  negativa sin regular. Coincide con lo que hacía el LM2990 en la v1. **Mica
  obligatoria** si el disipador va a masa de chasis; si no, el tab (y todo lo
  que toque) queda al potencial de VIN−.
- [x] **Carga mínima**: **500 µA**, exacto — §8.2.2.3 (p.13): "A minimum load
  current of 500 μA is required for proper operation. The external resistor
  divider can provide the minimum load, with the resistor from the adjust pin
  to ground set to 2.4 kΩ."
- [x] **Ventana ESR / C_OUT**: §8.2.2.1 (p.12), texto: COUT ≥ 10 µF aluminio
  electrolítico o ≥ 1 µF tantalio, ESR < 10 Ω. Fig. 16 (p.12) da la ventana
  exacta: **ESR entre ~25 mΩ y 10 Ω**. Cerámico ≥ 2.2 µF admitido solo con
  1 Ω de serie recomendado; dieléctrico X7R/X5R si el rango de temperatura
  varía más de ±25 °C del ambiente. **Fija C18: mismo patrón que C17** — ni un
  MLCC solo.
- [x] **ON/OFF**: activo-alto deshabilita. §7.3.1 (p.9): "impedance of the
  voltage source driving the ON/OFF pin must be low enough... 100 µA maximum
  at 2.4 V. If the ON/OFF function is not needed, connect the pin to GND. The
  ON/OFF pin should not be left floating." Tabla §6.5 (p.5): threshold ON, MAX
  garantizado sobre temperatura = 0.8 V; threshold OFF, MIN garantizado sobre
  temperatura = 2.4 V. **Atar a GND = siempre-encendido**, garantizado.

### §1.3 LT3045

**Bloqueo de §Task 2 anterior resuelto.** `analog.com` sigue inalcanzable
desde este entorno (mismo patrón: TLS ok, reset a ~19-20 s), y la Wayback
Machine también devolvió **503 persistente** ("No server is available to
handle this request") para *cualquier* PDF servido a través de
`web.archive.org/web/<ts>/...` — se probó con 6 timestamps distintos del
LT3045 y hasta con un PDF de `ti.com` ya confirmado accesible por otras
vías; todos dieron 503 idéntico. No es un bloqueo específico de
analog.com: el servicio de reproducción de binarios de archive.org está
caído para este tráfico. Se usó entonces la ruta alternativa que autorizó
el orquestador (copia verbatim de un distribuidor): **Farnell/element14,
`https://www.farnell.com/datasheets/2163219.pdf`** — 30 páginas, PDF 1.4,
descargado con `curl` (200 OK, 2.9 MB). Pie de página **"3045f"** en las
30 páginas (revisión F de Linear Technology/ADI) — coincide con el
formato de revisión del LT3045 en analog.com. Verificado como PDF nativo
(no reescaneado/OCR): texto seleccionable, diagramas vectoriales, mismo
membrete Linear Technology/ADI de las copias oficiales.

- [x] **R_ILIM — fórmula y valor a 400 mA/chip**: Current Limit =
  **150 mA·kΩ / R_ILIM** (factor de escala TYP, "Externally Programmable
  Current Limit", p.19). Para 400 mA: R_ILIM = 150 000/400 = **375 Ω** →
  **R11/R12 = 374 Ω 1 %** (E96 estándar más cercano; da 150000/374 =
  401 mA con el factor TYP). **Ojo**: el DS **no garantiza el factor de
  150 mA·kΩ en sí** — solo dos puntos MIN/MAX tabulados en la tabla
  eléctrica (p.4): a R_ILIM = 300 Ω, 450–550 mA garantizado (TYP 500); a
  R_ILIM = 1.5 kΩ, 90–110 mA garantizado (TYP 100). Ambos puntos caen
  dentro de ±10 % del TYP. Por el mismo patrón, el valor a 374 Ω (no
  tabulado) se estima en **~360–440 mA garantizado** — es extrapolación,
  no una cifra que el DS cite directamente.
- [x] **ILIM: uno por chip, NO compartible.** Pin Functions, ILIM (p.12):
  "Connecting a resistor between ILIM and GND programs the current
  limit. **For best accuracy, Kelvin connect this resistor directly to
  the LT3045's GND pin**" — GND es el pin propio de cada IC, no un nodo
  común. Confirmado sin ambigüedad en "Paralleling Multiple Devices Using
  ILIM (Current Monitor) to Cancel Ballast Resistor Drop" (p.25): el
  ejemplo de 2 chips en paralelo usa **dos resistencias RILIM
  independientes (287 Ω cada una)**, una por chip, cada una a su propio
  GND — con fórmula explícita `RILIM = 150 mA·kΩ/ILIM − RCDC·N` por
  dispositivo. **R11 y R12 son dos resistencias separadas, no una
  compartida.**
- [x] **Red SET compartida + ballast**: confirmado exactamente como
  esperaba el brief. "Direct Paralleling for Higher Current" (p.20):
  "**Tie all SET pins together and all IN pins together.** Connect the
  OUT pins together using small pieces of PCB trace (used as a ballast
  resistor) to equalize currents in the LT3045s." Es decir: **una sola
  R_SET + un solo C_SET**, con los pines SET de todos los chips unidos al
  mismo nodo. Ballast recomendado: **pista de PCB de 20 mΩ** por salida
  (ejemplo de referencia con 2 chips a 500 mA c/u: 20 mΩ × 2 chips da
  <20 % de error de reparto de corriente, con solo 10 mV de caída de
  regulación a 1 A total). Tabla 2 (p.20) da la resistencia de pista en
  mΩ/pulgada según ancho (10 mil/20 mil) y peso de cobre (1 oz/2 oz) para
  dimensionar el ballast real del layout.
- [x] **Fuga máxima del C_SET**: confirmado el cálculo del brief.
  "Output Voltage" (p.14): "**Leakages of 100nA into or out of the SET
  pin creates a 0.1% error in the reference voltage**." Con R_SET = 120 kΩ
  (valor de diseño del brief; la Table 1, p.14, da 121 kΩ como redondeo E96
  de ADI para VOUT = 12 V — ver §2.4 sobre por qué se rechaza ese
  redondeo): cada nA de fuga × 120 kΩ = **120 µV de error**, igual que el
  brief. Sanity check contra el DS: 100 nA × 120 kΩ = 12.0 mV, y
  12.0 mV/12 V = 0.1 % — cuadra exacto con la cita. **Dieléctrico
  recomendado**: "Set Pin (Bypass) Capacitance" (p.18): "any bypass
  capacitor leakage deteriorates the LT3045's DC regulation... **LTC
  recommends the use of a good quality low leakage ceramic capacitor**."
  Sección de dieléctricos (p.16): descarta Z5U/Y5V (coeficiente de
  voltaje/temperatura fuerte) a favor de **X5R/X7R**; recomienda
  específicamente la serie **Murata GJ8** por su buen coeficiente de
  voltaje en case size pequeño. Nota aparte: si el ambiente tiene
  vibración, un cerámico en el pin SET puede generar ruido piezoeléctrico
  (cientos de µV pico-pico) — ahí el DS sugiere tantalio/film en su lugar
  (p.16-17), a costa de más ESR/ESL (tolerable en SET, no en OUT).
- [x] **Dropout máx. a 350 mA**: el DS **no tabula 350 mA exacto** — los
  puntos garantizados en la tabla eléctrica (p.3) son a 300 mA (MIN 220 /
  TYP 280 / **MAX 350 mV**) y a 500 mA (MIN 260 / TYP 350 / **MAX 450
  mV**). Por el mismo criterio conservador usado en §1.1/§1.2 (cuando no
  hay un punto exacto, se toma el MAX del siguiente bin garantizado hacia
  arriba): **dropout aplicable a 350 mA = 450 mV** (bin de 500 mA). El
  bin de 300 mA (350 mV) es el dato más cercano pero queda *por debajo*
  de 350 mA, así que no cubre el caso conservador. Hay una curva típica
  a 400 mA en Typical Performance Characteristics (Fig. "Dropout
  Voltage", p.6) pero es TYP, no garantizada.
- [x] **V_IN abs max**: **±22 V** en el pin IN respecto a GND (Absolute
  Maximum Ratings, p.2: "IN Pin Voltage ...........................±22V";
  también "IN-to-OUT Differential...........................±22V" e
  "IN-to-OUTS Differential...........................±22V"). **El brief
  esperaba ≈20 V — ese es el rango de entrada de OPERACIÓN, no el abs
  max**: "Input Voltage Range" en la tabla eléctrica (p.3) da MIN 2 V /
  MAX **20 V** como ventana garantizada de funcionamiento regulado.
  El abs max real (22 V) es el número que debe usarse para dimensionar
  el margen de sobretensión del TVS D8, no 20 V — con 22 V de abs max el
  TVS tiene 2 V más de colchón del que el brief asumía.
- [x] **Conexión del EP**: **GND**, confirmado en ambos packages. Pin
  Configuration (p.2): "EXPOSED PAD (PIN 11) IS GND, MUST BE SOLDERED TO
  PCB" (DFN) y "EXPOSED PAD (PIN 13) IS GND, MUST BE SOLDERED TO PCB"
  (MSOP). Pin Functions (p.12): "GND (Pin 8, Exposed Pad Pin 11/Pin 9,
  Exposed Pad Pin 13): Ground. The exposed backside is an electrical
  connection to GND... solder the exposed backside to the PCB ground and
  tie it directly to the GND pin."
- [x] **PG sin usar**: **flotar**. Pin Functions, PG (p.12): "If the
  power good functionality is not needed, **float the PG pin**." (es
  open-collector; no necesita pull-up si no se usa).
- [x] **EN/UV atado a siempre-ON**: **atar a IN**. Pin Functions, EN/UV
  (p.12): "If unused, **tie EN/UV to IN**. Do not float the EN/UV pin."
  Threshold de encendido: MIN 1.18 / TYP 1.24 / MAX 1.32 V con 130 mV de
  histéresis (tabla eléctrica, p.3) — con EN/UV = IN, el pin siempre está
  muy por encima del threshold mientras el chip tenga alimentación.

**Pinera — DFN (DD, 10-lead 3×3 mm), TOP VIEW** (Pin Configuration p.2 +
Pin Functions p.12):

| Pin | Función |
|---|---|
| 1 | IN |
| 2 | IN |
| 3 | EN/UV |
| 4 | PG |
| 5 | ILIM |
| 6 | PGFB |
| 7 | SET |
| 8 | GND |
| 9 | OUTS |
| 10 | OUT |
| 11 (EP) | GND |

**Pinera — MSOP (MSE, 12-lead), TOP VIEW**:

| Pin | Función |
|---|---|
| 1 | IN |
| 2 | IN |
| 3 | IN |
| 4 | EN/UV |
| 5 | PG |
| 6 | ILIM |
| 7 | PGFB |
| 8 | SET |
| 9 | GND |
| 10 | OUTS |
| 11 | OUT |
| 12 | OUT |
| 13 (EP) | GND |

- [ ] **Orientación del Schottky de protección inversa out→in (D10) — GAP,
  inferencia de ingeniería, no hecho citado.** La pregunta es sobre el
  Schottky entre **OUT e IN** (nodos `+12V`→`+13V1` del plan, Task 4 Step
  2), no entre OUTS y SET — son pines distintos. El DS **no da guía
  explícita de orientación para un Schottky externo OUT→IN**: lo que sí
  da, en "Protection Features" (p.22), es que el LT3045 trae protección
  de entrada inversa **integrada en el chip** — "**the IN pin withstands
  reverse voltages of up to ±20V without causing any input current flow
  and without developing negative voltages at the OUT pin**" — y que, en
  escenarios de batería de respaldo (VOUT sostenido mientras VIN cae o
  flota), "**the reverse current protection circuitry prevents current
  flow from output to the input**" (mismo párrafo, p.22). Es decir: el
  propio LT3045 ya bloquea internamente la trayectoria OUT→IN; el DS no
  dice si además hace falta (ni cómo orientar) un Schottky externo entre
  esos dos pines — el plan lo incluye como defensa adicional (mismo
  patrón que D12/D13 del LM2941/LM2991, §1.1/§1.2), no porque el DS del
  LT3045 lo pida.

  **Orientación esperable (inferencia, riel positivo)**: ánodo en OUT
  (+12 V), cátodo en IN (+13V1) — reverso en operación normal
  (V_OUT < V_IN); conduce solo si la entrada cae por debajo de la salida
  (el mismo escenario de batería de respaldo que describe el DS, pero
  para el diodo externo, no para el clamp interno). Antes de fijar D10 en
  el esquemático: verificar contra el manual del demo board del LT3045
  (**DC2491A**, citado en el propio DS — "Refer to the LT3045's DC2491A
  demo board manual for further details", p.20) si el circuito de
  referencia de Analog Devices muestra ese diodo externo.

  Nota aparte — **no confundir con el Schottky OUTS→SET**, que sí cita el
  DS explícito (p.22): "**placing a Schottky diode between OUTS and SET
  pins, with its anode at the OUTS pin**" (ánodo en OUTS, cátodo en SET).
  Es información real del DS, pero protege una trayectoria distinta (fuga
  de hasta 15 mA hacia GND por el clamp OUTS-SET durante "output
  overshoot recovery") — no responde la pregunta de D10. (Aparte hay
  también un 1N4148, no Schottky, entre IN y PGFB — "PGFB Disabled with
  Reverse Input Protection", p.27, ánodo en IN — tampoco es D10.)

### §1.4 LT3094

**Mismo bloqueo de red que §1.3** (analog.com + Wayback ambos
inalcanzables). Copia verbatim vía distribuidor: **DigiKey,
`https://media.digikey.com/pdf/Data%20Sheets/Analog%20Devices%20PDFs/LT3094_Rev0_9-5-18.pdf`**
— 33 páginas, PDF 1.7, descargado con `curl` (200 OK, 2.6 MB). Pie de
página **"Rev 0"** en las 33 páginas y "D17043-0-9/18(0)" en la
contraportada (fecha 9/2018) — coincide exacto con el nombre del archivo
del distribuidor ("Rev0_9-5-18"), confirmando que es la única revisión
publicada del LT3094, verbatim ADI (no reescaneado).

- [x] **R_ILIM — fórmula y valor a 400 mA/chip**: Current Limit =
  **3.75 A·kΩ / R_ILIM** (= 3750 mA·kΩ/R_ILIM; "Externally Programmable
  Current Limit", p.25). Para 400 mA: R_ILIM = 3750/400 = **9.375 kΩ** →
  **R13/R14 = 9.31 kΩ 1 %** (E96 estándar más cercano; da 3750/9.31 =
  403 mA con el factor TYP; la alternativa 9.53 kΩ da 393 mA — cualquiera
  sirve, 9.31 k queda más cerca del blanco). Igual que en el LT3045, el
  factor de 3.75 A·kΩ es **TYP, no garantizado como constante**: la tabla
  eléctrica (p.5) solo da dos puntos MIN/MAX: R_ILIM = 7.5 kΩ → 450–560 mA
  garantizado (TYP 500); R_ILIM = 37.5 kΩ → 90–120 mA garantizado
  (TYP 105). El valor a 9.31 kΩ (no tabulado) se estima por el mismo
  patrón en **~350–460 mA garantizado** — extrapolación, no cifra citada
  directamente por el DS.
- [x] **ILIM: uno por chip, NO compartible.** Pin Functions, ILIM (p.15):
  "Connecting a resistor between ILIM and GND programs the current
  limit. **For best accuracy, Kelvin connect this resistor directly to
  the LT3094's GND pin.**" Mismo patrón que el LT3045: GND es local a
  cada IC. La sección "Direct Paralleling for Higher Current" (p.25) y
  la Fig. 15 "Parallel Devices" muestran cada chip con su propio ILIM
  (atado a su propio GND, sin compartir nodo) — **R13 y R14 son dos
  resistencias separadas.**
- [x] **Red SET compartida + ballast**: idéntico patrón al LT3045.
  "Direct Paralleling for Higher Current" (p.25): "**Tie all SET pins
  together and all IN pins together.** Connect the OUT pins together
  using small pieces of PCB trace (used as a ballast resistor)..." Tabla
  2 de resistencia de pista (p.25) es la misma que en el LT3045 (mΩ/in
  por ancho/peso de cobre). Ejemplo de referencia: 2 chips con 20 mΩ de
  ballast cada uno, <20 % de error de reparto a plena carga, 10 mV de
  caída extra de regulación con 1 A total.
- [x] **Fuga máxima del C_SET**: mismo cálculo que el LT3045, cifra
  idéntica. "SET Pin (Bypass) Capacitance" (p.21): "Capacitor leakage of
  as little as **100nA causes a 0.1% DC error**. ADI recommends the use
  of a good quality low leakage ceramic capacitor." Con R_SET = 120 kΩ
  (valor de diseño del brief; la Table 1, p.17, da 121 kΩ como redondeo E96
  de ADI para VOUT = −12 V, mismo caso que el lado positivo — ver §2.4):
  cada nA de fuga × 120 kΩ = **120 µV de error**, igual que en §1.3.
  Dieléctrico recomendado: **X5R/X7R** (no Z5U/Y5V), serie
  **Murata GJ8** citada explícitamente (p.19) — texto casi calcado del
  LT3045.
- [x] **Dropout máx. a 350 mA**: tampoco hay bin exacto a 350 mA. Tabla
  eléctrica (p.4): a 100 mA (MIN 185 / TYP 230 / **MAX 280 mV**) y a
  500 mA (MIN 235 / TYP 310 / **MAX 410 mV**) — el hueco entre bins es
  más grande que en el LT3045 (100→500 mA vs 300→500 mA). Con el mismo
  criterio conservador: **dropout aplicable a 350 mA = 410 mV** (bin de
  500 mA, el único que cubre 350 mA por arriba).
- [x] **V_IN abs max**: **22 V de magnitud**, asimétrico por ser
  regulador negativo. Absolute Maximum Ratings (p.3): "IN Pin Voltage
  with Respect to GND Pin ...........................**−22V, 0.3V**"
  (puede ir de −22 V hasta apenas +0.3 V respecto a GND). Igual que en
  §1.3, el rango de **operación** garantizada es más angosto: "Input
  Voltage Range" (p.4) da MIN **−20 V** / MAX −2.3 V. Mismo hallazgo que
  el LT3045: el TVS (D9 en este caso) debe dimensionarse contra el abs
  max de 22 V, no contra los 20 V de operación que asumía el brief —
  refuerza que no es un error puntual sino el patrón real de la familia
  LT304x.
- [x] **Conexión del EP**: **IN, NO GND** — a diferencia del LT3045.
  Pin Configuration (p.3): "EXPOSED PAD (PIN 13) IS **IN**, MUST BE
  SOLDERED TO PCB" en ambos packages (DFN y MSOP). Pin Functions (p.15):
  "IN (Pins 1, 2, **Exposed Pad Pin 13**): Input." Esto es una asimetría
  real entre los dos chips que el brief pedía "espejo exacto" pero que
  **no lo es**: en el LT3045 el tab/EP va a masa; en el LT3094 el tab/EP
  va al potencial de entrada negativa (VIN−) del propio regulador — el
  mismo patrón de "tab muerde" que ya se vio en el LM2991 de §1.2 y en
  el LM2990 de la v1. **Si el EP del LT3094 (U6/U7 en el BOM v2) toca un disipador o
  plano de masa de chasis, hace falta aislamiento** (mica o almohadilla
  térmica aislante), igual que con el LM2991.
- [x] **PG sin usar**: **flotar**. Pin Functions, PG (p.15): "If the
  power good functionality is not needed, **float the PG pin**. The PG
  flag status is valid even if the LT3094 is in shutdown."
- [x] **EN/UV atado a siempre-ON**: **atar a IN**. Pin Functions, EN/UV
  (p.15): "The EN/UV pin is bidirectional... If unused, **tie EN/UV to
  IN**. Do not float the EN/UV pin." Threshold: ±1.26 V (positivo o
  negativo respecto a masa, histéresis 200/215 mV) — con IN en, por
  ejemplo, −14 V, EN/UV = IN queda muy por debajo del threshold negativo
  de −1.26 V, encendido garantizado.

**Pinera — DFN (DD, 12-lead 3×3 mm) y MSOP (MSE, 12-lead), TOP VIEW**
(idéntica numeración en ambos packages — a diferencia del LT3045, aquí el
DFN también es de 12 pines; Pin Configuration p.3 + Pin Functions p.15):

| Pin | Función |
|---|---|
| 1 | IN |
| 2 | IN |
| 3 | EN/UV |
| 4 | PG |
| 5 | PGFB |
| 6 | ILIM |
| 7 | VIOC |
| 8 | SET |
| 9 | GND |
| 10 | OUTS |
| 11 | OUT |
| 12 | OUT |
| 13 (EP) | **IN** (no GND — ver arriba) |

Nota: el LT3094 tiene un pin **VIOC** (control de regulador upstream para
minimizar disipación) que el LT3045 no tiene. Si no se usa: **flotar**
("VIOC (Pin 7): ...If unused, float the VIOC pin", p.15).

- [ ] **Orientación del Schottky de protección inversa (D11) — GAP, no
  espejo confirmado.** A diferencia del LT3045, el DS del LT3094 **no
  incluye** una nota de aplicación equivalente al Schottky OUTS→SET. La
  sección "Protection Features" (p.28) del LT3094 solo cubre pull-up del
  OUT por encima de masa y foldback de corriente — no menciona ningún
  diodo Schottky en todo el documento (se revisaron las 33 páginas
  completas, incluida la sección de protección). El brief pedía "espejo
  exacto" del LT3045 para D11, pero **eso no está soportado por fuente
  primaria contra el LT3094 específicamente**. Por simetría de polaridad
  (regulador negativo), la orientación análoga *esperable* sería
  invertida respecto al LT3045 — cátodo en OUTS, ánodo en SET, para
  bloquear la misma trayectoria de corriente en el sentido correspondiente
  a un riel negativo — pero esto es **inferencia de ingeniería, no un
  hecho citado del DS**. Antes de fijar D11 en el esquemático: (a)
  revisar el manual del demo board DC2624A del LT3094 (citado en p.26,
  no descargado en esta tarea), o (b) confirmar por simulación/analogía
  con el LT3090/LT1175 (reguladores negativos relacionados, Related
  Parts p.32) cuál es la convención correcta para esta topología.

### §1.5 Veredicto GO/NO-GO de márgenes

Recomputado con los dropouts **máximos garantizados** leídos en §1.1/§1.2
(no los típicos), y el valle simulado de 14.12 V de la v1 (Talema 120 VA,
9400 µF/riel, red a 207 V, plena carga — `hardware/01-power-supply/notes/design-notes.md`
§16.5).

```
Positivo: 14.12 V − dropout_max(LM2941 @ 650 mA, conservador = MAX@1A) ≥ 13.1 V
          14.12 V − 1.0 V = 13.12 V ≥ 13.1 V  →  margen = +0.02 V  →  GO

Negativo: 14.12 V − dropout_max(LM2991 @ 650 mA, conservador = MAX@1A) ≥ 12.9 V
          14.12 V − 1.0 V = 13.12 V ≥ 12.9 V  →  margen = +0.22 V  →  GO
```

**Riel negativo: GO cómodo (+0.22 V).**

**Riel positivo: GO, pero por el canto de la uña (+0.02 V).** Esto cierra el
riesgo §11.1 de la spec con un número, y el número que sale es peor de lo que
sonaba la nota de la spec ("el margen de valle +0.22 V el peor"): usando el
dropout **garantizado** en vez del típico, el margen del riel positivo cae a
**2 centésimas de voltio**. Cualquiera de estos se lo come entero:

- Tolerancia de R1/R2 del divisor del LM2941 (desplaza el setpoint de 13.1 V).
- Caída extra en conectores/pistas entre el bulk y el LM2941.
- Que el valle real esté por debajo de los 14.12 V simulados (la propia spec,
  §11.4, ya avisa que esa cifra es "fina hasta que la mula mida"). **Sin mula
  (§4), esa medida se hace ya con la v2 en la mesa** — el umbral por debajo del
  cual el trimmer deja de salvarla está calculado en §4.1: **13.46 V**.
- Que el dropout real a 650 mA/caliente esté más cerca del MAX de 1 A que del
  TYP de 0.5 V (el DS no da un punto intermedio garantizado — ver §1.1).

No hace falta bajar el setpoint todavía porque el margen no dio negativo, pero
con 0.02 V de colchón la recomendación para Task 4/5 es dejar el trimmer del
divisor del LM2941 con margen para bajar el setpoint (el brief documenta el
trimmer llegando hasta ~12.3 V) **si la medida real no confirma al menos unas
décimas de margen**. Ese trimmer dejó de ser una precaución al cancelarse la
mula: es el mecanismo que absorbe el valle real, y el bring-up (§5 paso 5)
espera usarlo, no encontrarlo intacto.

#### §1.5.1 Headroom del LT3045/LT3094 contra el suelo bajable del pre-reg (cierra §1.3/§1.4)

Con §1.3/§1.4 ya leídos, se puede cerrar el extremo de la cadena que quedó
pendiente: ¿el suelo bajable del divisor con trimmer (~12.3 V positivo /
−12.2 V negativo, documentado para Task 4/5) sigue dejando entrada
suficiente al LT3045/LT3094 para sacar 12.000 V, sumando dropout garantizado
del LT **más** la caída del ballast de paralelismo (20 mΩ × 0.325 A ≈ 7 mV
por chip, corriente real de operación con 2 chips repartiendo ~650 mA/riel)?

```
V_IN_mínima_requerida_en_LT = V_OUT (12.000 V) + dropout_max(LT) + caída_ballast (7 mV)

Positivo (LT3045), conservador (bin de 500 mA, MAX 450 mV — ver §1.3):
  12.000 + 0.450 + 0.007 = 12.457 V requeridos
  Suelo del pre-reg: 12.3 V
  Margen = 12.3 − 12.457 = −0.157 V  →  NO ALCANZA (déficit de 157 mV)

Positivo (LT3045), con el bin más cercano (300 mA, MAX 350 mV, optimista
porque 325 mA > 300 mA):
  12.000 + 0.350 + 0.007 = 12.357 V requeridos
  Margen = 12.3 − 12.357 = −0.057 V  →  TAMPOCO alcanza, pero por 57 mV

Negativo (LT3094), conservador (bin de 500 mA, MAX 410 mV — ver §1.4):
  12.000 + 0.410 + 0.007 = 12.417 V requeridos (en magnitud)
  Suelo del pre-reg: 12.2 V
  Margen = 12.2 − 12.417 = −0.217 V  →  NO ALCANZA (déficit de 217 mV)
```

**Hallazgo real, no maquillado: en NINGÚN escenario (conservador u
optimista) el suelo documentado del trimmer (~12.3 V / −12.2 V) alcanza para
que el LT saque 12.000 V limpios**, una vez que se usa dropout garantizado
(no típico) y se suma la caída del ballast. El déficit va de ~57 mV (mejor
caso, LT3045 con el bin de 300 mA) hasta ~217 mV (peor caso, LT3094). Esto
**no invalida el GO de §1.5** sobre el margen de valle del pre-reg en sí —
esa cuenta (13.12 V ≥ 13.1 V / ≥ 12.9 V) sigue siendo válida y es un chequeo
independiente — pero sí cierra la pregunta que había quedado abierta sobre
si el trimmer podía bajarse "hasta ~12.3 V" con seguridad: **no puede, sin
que el LT deje de garantizar 12.000 V exactos en el peor caso.**

**Recomendación concreta para Task 4/5**: el suelo práctico y seguro del
trimmer del pre-reg no debe bajar de ~**12.46 V** (positivo) / ~**−12.42 V**
(negativo) si se quiere garantizar 12.000 V a la salida del LT bajo
condiciones garantizadas de dropout — no de los ~12.3 V / −12.2 V que
documentó Task 1. Alternativamente, aceptar que en el extremo bajo del
trimmer el LT puede perder unas pocas decenas/centenas de mV de regulación
(verificar si el presupuesto de tolerancia global de la spec absorbe esto)
o medir en la mula real si el dropout real es más favorable que el
garantizado (como ya se sospecha para el riel positivo del pre-reg en la
sección anterior). Esto **no es un NO-GO del proyecto** — es un ajuste de
rango de trimmer que Task 4/5 debe incorporar con este número en mano.

## §2 Stock

**Herramientas usadas**: se intentó primero `mcp__kicad__search_jlcpcb_parts` /
`get_jlcpcb_part` / `suggest_jlcpcb_alternatives` — la base local de JLCPCB no
está descargada en este entorno (`search_jlcpcb_parts` devuelve "No JLCPCB
parts found" hasta para búsquedas triviales como "10k resistor 0805", y
`get_jlcpcb_part` con un C-code real conocido responde "download the JLCPCB
database first") y no hay credenciales de API en vivo configuradas. Se cambió
entonces a la web de LCSC (`lcsc.com`, vía `WebSearch`/`WebFetch`), como
autorizaba el fallback. **Fecha de consulta de toda esta sección: 2026-08-16.**

### §2.1 Step 1 — Silicio ultra en LCSC

Búsqueda de LT3045 y LT3094 en sus variantes de grado (E/I/H) y package
(DFN/MSOP). Confirmado en LCSC (no en `findchips`/`octopart`, que solo sirven
de puntero — el C-code y el stock se verificaron en `lcsc.com/product-detail`
directamente):

| variante | package | grado | LCSC C-code | stock | precio (1+/100+) | básica/extendida | fecha |
|---|---|---|---|---|---|---|---|
| LT3045EDD#TRPBF | DFN-10-EP(3×3) | E (−40…125 °C) | **C514420** | 3.618 | $7.01 / $5.25 | Extended | 2026-08-16 |
| LT3045EDD#PBF (sin T&R) | DFN-10-EP(3×3) | E | C666574 | 817 | $8.03 / $6.89 (121+) | Extended | 2026-08-16 |
| LT3045HDD#PBF | DFN-10-EP(3×3) | H | C666580 | no verificado | no verificado | Extended | 2026-08-16 |
| LT3045EMSE#PBF | MSOP-12-EP | E | C580012 | 3.020 | $9.20 / $6.86 | Extended | 2026-08-16 |
| LT3094EDD#PBF | WDFN-12-EP(3×3) | E | **C670492** | 1.475 | $7.30 / $6.36 | Extended | 2026-08-16 |
| LT3094EMSE#PBF | MSOP-12-EP | E | C498217 | 1.017 | $6.92 / $5.87 | Extended | 2026-08-16 |

Sanity check contra la cifra orientativa del brief ($3–6/ud en extended):
los precios reales caen en **$4.8–9.2/ud según variante**, todos en el mismo
orden de magnitud (ninguno a $0.10 ni marcado como otra categoría de parte) —
la descripción de cada página coincide con "Voltage Regulators - Linear, Low
Drop Out (LDO) Regulators", fabricante ADI, sin señales de mislabeling.
Como refleja la columna básica/extendida de la tabla, todas caen en
**Extended** (no Basic) — esperable para un LDO ultra-bajo-ruido, no es un
componente de línea básica.

### §2.2 Step 2 — Elección de package

**DFN-10-EP(3×3) para el LT3045 y DFN-12/WDFN-EP(3×3) para el LT3094**, por
la regla del brief (DFN preferido por térmica, es el package de la nota de
aplicación — pinout ya documentado en §1.3/§1.4). **El DFN no necesitó caer al
fallback de MSOP**: ambos DFN tienen stock real y verificado (3.618 u. el
LT3045EDD#TRPBF, 1.475 u. el LT3094EDD#PBF) — el MSOP queda solo como
alternativa de segunda línea, ya cotizada arriba por si el DFN se agota entre
esta puerta y la compra real. Grado **E** elegido sobre I/H: el circuito no
tiene requisito documentado de rango extendido de temperatura (el propio LM2941/LM2991
ya limitan a 0–125 °C/−40–125 °C aguas arriba, §1.1/§1.2), y el grado E es el
que tiene más stock y menor precio de los tres.

### §2.3 Step 3 — Veredicto GO/NO-GO de silicio

**GO.** Tanto el LT3045 (C514420, 3.618 u.) como el LT3094 (C670492, 1.475 u.)
tienen stock real, verificado en vivo en `lcsc.com`, en el package preferido
por la regla del Step 2. No aplica el plan B de re-plan del brief.

### §2.4 Step 4 — Pasivos y protecciones críticos

| parte | código LCSC | stock | básica/extendida | precio (1+/100+) | fecha |
|---|---|---|---|---|---|
| R_SET 120 kΩ 1 % ±100 ppm/°C 0805 (YAGEO RC0805FR-07120KL) | C114524 | 169.800 | Extended | $0.0082 / $0.0054 | 2026-08-16 |
| R_SET 120 kΩ 0,1 % ±25 ppm/°C 0805 (YAGEO RT0805BRD07120KL — a confirmar como SKU manufacturado) | **sin C-code confirmado** — ver nota | — | — | — | 2026-08-16 |
| Shunt 20 mΩ 1 % 1206 (Isabellenhuette VMK-R020-1.0-U, ±20 ppm/°C, 1.5 W) | **C6920584** | 1.000 | Basic | $0.75 / $0.48 | 2026-08-16 |
| Shunt 20 mΩ 1 % 1206, alterno (Bourns CRF1206-FZ-R020ELF, ±50 ppm/°C, 1 W) | C1848840 | 196 | Extended | $0.52 / $0.30 | 2026-08-16 |
| 22 µF X7R 25 V 1210 (HRE CGA1210X7R226K250RT, ±10 %) | **C6120032** | 2.685 | Basic | $0.27 / $0.16 | 2026-08-16 |
| 10 µF X7R 50 V 1206 (Samsung CL31B106KBHNNNE, ±10 %) — ver nota de voltaje | **C89632** | 385.340 | Extended | $0.43 / $0.28 (500+) | 2026-08-16 |
| SMAJ15A TVS (Littelfuse) | **C148216** | 10.030 | Basic | $0.139 / $0.076 (2500+) | 2026-08-16 |
| SS14 Schottky SMA (MDD/Microdiode) | **C2480** | 1.081.100 | Basic | $0.0185 / $0.0085 (50k+) | 2026-08-16 |
| R_ILIM 374 Ω 1 % 0603 (UNI-ROYAL 0603WAF3740T5E) — R11/R12, LT3045 | **C23149** | 9.800 | Extended | $0.0027 / $0.0021 | 2026-08-17 |
| R_ILIM 9.31 kΩ 1 % 0603 (UNI-ROYAL 0603WAF9311T5E) — R13/R14, LT3094 | **C23126** | 2.200 | Extended | $0.0014 / $0.0012 | 2026-08-17 |

**Nota — R_ILIM (fix task review, 2026-08-17)**: R11/R12 (374 Ω) y R13/R14
(9.31 kΩ), calculados en §1.3/§1.4, **nunca pasaron por esta puerta de
stock** — el Step 4 original (2026-08-16) cotizó R_SET, shunts, C_SET,
entrada/salida y protecciones, pero se saltó los R_ILIM. El implementador de
Task 9 rellenó `bom.csv` con C17590/C25709 sin verificarlos contra
`lcsc.com`; el task review los detectó como **inventados** (C17590 es un
270 Ω 0805, C25709 un 75 kΩ 1210 — ninguno de los dos es la pieza real) y
este fix los reemplaza por códigos verificados en vivo en el navegador
contra `lcsc.com/product-detail/`: value + tolerancia + package confirmados
en pantalla para ambos, con stock real (9.800 u. y 2.200 u.).

**Nota — R_SET (120 kΩ, valor de diseño correcto)**: el objetivo es
**12.000 V = 100 µA × 120 kΩ** — el brief pide 120 kΩ y ese es el valor de
diseño correcto. §1.3/§1.4 habían citado la Table 1 del DS del
LT3045/LT3094 (121 kΩ para VOUT = 12 V) como si fuera el valor a usar; esa
lectura **se rechaza**: 121 kΩ es un redondeo a la serie E96 estándar de
ADI, y 100 µA × 121 kΩ = **12.100 V, 100 mV fuera del blanco de 12.000 V**.
La Table 1 solo sirve como referencia de que ADI redondea a su E96 más
cercana — no reemplaza el objetivo exacto del brief.

El part number `YAGEO RT0805BRD07121KL` **existe como parte manufacturada
real** (confirmado en DigiKey, 121 kΩ ±0,1 % ±25 ppm/°C, 0805, thin film) y
sirve como evidencia de que la serie hermana (`RT0805BRD07`/`AT0805BRD07`,
0,1 %/25 ppm, 0805) existe y tiene SKUs confirmados en LCSC alrededor de ese
rango de valores (10 k→C110774/C110775, 100 k→C122537, 182 k→C865233,
301 k→C865388, 560 k→C865557) — pero el valor a buscar es **120 kΩ**, no
121 kΩ. No se pudo confirmar el C-code puntual de 120 kΩ en LCSC con las
herramientas de búsqueda disponibles (`search_jlcpcb_parts` sin base local,
`WebSearch`/`WebFetch` sin poder ejecutar el buscador JS-driven de
`lcsc.com/search`, que exige render en navegador). No es evidencia de que
LCSC no lo tenga — es un techo de la herramienta, no un NO-GO.

**Fallback ya confirmado y en stock real**: `RC0805FR-07120KL` (C114524,
120 kΩ, 1 %, ±100 ppm/°C, 169.800 u.) tiene el **valor exacto correcto** —
no introduce ningún desvío de VOUT, solo relaja tolerancia (1 % vs el 0,1 %
del brief) y tempco (100 ppm/°C vs 25 ppm/°C). Deriva térmica de ese
tempco: 100 ppm/°C × 120 kΩ = 12 Ω/°C de deriva en R_SET; como
V_SET = I_SET × R_SET sin divisor resistivo en el LT3045/3094, eso equivale
a 100 µA × 12 Ω/°C = 1,2 mV/°C, es decir **~100 ppm/°C de VOUT** (4× peor
que los 25 ppm/°C del componente 0,1 % objetivo del brief). **Acción para
Task 4/9**: antes de cerrar el BOM, verificar en `lcsc.com/search` (interfaz
web, requiere JS) si existe C-code de **120 kΩ** 0,1 %/25 ppm 0805 en
stock; si no, decidir entre (a) soldar a mano el 0,1 % comprado en
Mouser/DigiKey (`RT0805BRD07120KL`, a confirmar como SKU manufacturado) o
(b) aceptar el `C114524` con el impacto en deriva térmica calculado arriba.

**Nota — 10 µF X7R 25 V 1206**: las partes con el voltaje exacto de 25 V que
se encontraron (`TDK CGA5L1X7R1E106K160AC` C2168260: solo 3 u. en stock;
`Taiyo Yuden TMK316B7106KL-TD` C92831: agotado; `Murata GRM31CB31E106KA75L`
C86049: agotado) no sirven para producción. Se sustituyó por
`Samsung CL31B106KBHNNNE` (C89632), rating **50 V** en vez de 25 V — un
sobre-margen de voltaje siempre es válido eléctricamente (nunca un
downgrade), y tiene 385.340 u. en stock real. Documentado para que Task 4/9
no lo lea como un error de transcripción.

**Shunt 20 mΩ — se documentan dos candidatos** porque ninguno es "Basic +
stock alto + mejor tempco" a la vez: el Isabellenhuette (Basic, 1.000 u.,
±20 ppm/°C) es la elección primaria por mejor tempco (importa para el
reparto de corriente entre chips en paralelo, §1.3/§1.4); el Bourns queda
como alterno si el Isabellenhuette se agota.

### §2.5 Step 5 — THT (no va por LCSC)

Verificado en DigiKey (Mouser bloqueó el `WebFetch` — timeout repetido en las
tres páginas de producto, aparente bot-detection; DigiKey sirvió como
alternativa equivalente, ambos son distribuidores autorizados TI/Bourns, no
un canal gris):

| parte | distribuidor / código | stock | precio (1 pc) | fecha |
|---|---|---|---|---|
| LM2941CT/NOPB (TI, TO-220-5) | DigiKey 148143 | 164 u. | $2.04 | 2026-08-16 |
| LM2991T/NOPB (TI, TO-220-5) | DigiKey 212657 | 953 u. | $4.05 | 2026-08-16 |
| Trimmer Bourns 3296W-1-102 (1 kΩ, 25 vueltas, ±10 %, ±100 ppm/°C) | DigiKey 84508 | 1.062 u. | $3.64 | 2026-08-16 |

**LM2941CT/NOPB con 164 u. es el número más ajustado de toda la puerta** —
sigue siendo stock real (no 0, no backorder), suficiente para una tanda
chica (la fuente v2 usa 1 LM2941 por unidad), pero si el proyecto escala a
producción de varias unidades convendría re-chequear antes de comprar. Lead
time de fabricante declarado (16 semanas) es el de fabricación nueva de TI,
no aplica mientras haya stock del distribuidor.

## §3 Decisiones y aritmética

### §3.0 Worksheet F1 (Task 5 Step 6): sube de 250 mA a 1.6 A T

**Hallazgo real, no maquillado**: la nota que fijó F1 en 250 mA (v1,
`hardware/01-power-supply/notes/design-notes.md` líneas 379-383, sección "Lo
que cambia" de la migración 110V→230V) calculó la corriente de primario con
**TR1 = 24 VA** ("mismo transformador (12 VAC CT / 2 A ≈ 24 VA)") — pero ese
no es el transformador que hay hoy en el bom.csv (v1 y v2 igual): el BOM real
dice **Talema 0120P1-2-012, 120 VA** (subido en algún punto de la evolución
de v1 para ganarle margen de valle al dropout del LM2940/LM2941, documentado
en los comentarios de `build_schematic.py` sobre §16.5). Esa nota de F1 quedó
**obsoleta sin que nadie la revisara** — es exactamente el tipo de bug que
esta tarea pide cazar (brief Step 6).

**Aritmética con el término nuevo:**

```
Corriente de primario de TR1 a plena carga (VA/V, exacto, no depende del PF):
  120 VA / 230 V = 0.522 A

Corriente de entrada del IRM-15-5 a 230 VAC:
  Fuente primaria: meanwell.com, IRM-15-SPEC.PDF (File Name:IRM-15-SPEC,
  fecha de archivo 2025-11-21), fila "AC CURRENT (Typ.)" de la tabla de
  especificaciones — aplica a toda la familia IRM-15 (mismos ~15 W, la fila
  no se repite por modelo): "0.35A/115Vac  0.2A/230Vac  0.17A/277Vac".
  0.2 A/230Vac Typ. — más alto que el "~0.16A max" que orientaba el brief
  (ese número no viene de esta hoja; el dato real medido por MeanWell es
  0.2 A). Con ~78-83% de eficiencia típica de la propia hoja y 15 W de
  salida, la potencia real de entrada da ~18-19 W — a 0.2 A/230V eso es
  ~46 VA aparentes, factor de potencia ~0.4, normal en una fuente offline
  pequeña sin PFC activo (rectificador de entrada por capacitor, corriente
  en pulsos cerca del pico de la sinusoidal).

Carga total sobre F1 (J7 comparte el mismo fusible que TR1, spec §7):
  0.522 A (TR1) + 0.2 A (IRM-15-5) = 0.722 A
```

**Decisión: F1 sube de 250 mA a 1.6 A T.** Ni 250 mA (v1) ni las alternativas
250/315/400 mA que orientaba el brief alcanzan: **todas quedan por debajo de
la propia carga nominal de operación (0.722 A)** — con cualquiera de esos
valores el fusible se fundiría en uso normal, no solo ante una falla. El
salto real necesario es mucho mayor de lo que el brief anticipaba.

Margen elegido: se replica la misma filosofía de margen que ya usó la nota
de v1 al fijar 250 mA sobre 104 mA (~2.4× la corriente nominal) — un margen
generoso apropiado para un transformador **toroidal** con arranque en frío
más agresivo que un EI-core (mitigado por NT1, pero no eliminado) y para la
tolerancia de red europea (±10%, la corriente sube algo más a 207 V). Con
0.722 A de carga: 0.722 × 2.4 ≈ 1.73 A → el valor estándar de fusible lento
5×20 mm más cercano por debajo de eso (para no sobre-fusionar y perder valor
protector) es **1.6 A T**, dando 1.6/0.722 = 2.22× de margen — prácticamente
el mismo ~2.2-2.4× que ya validó el diseño original, no un número inventado.
A baja red (207 V, -10%): TR1 sube a ≈120/207=0.580 A, el IRM-15-5 sube algo
menos (interpolando 0.35 A@115V / 0.2 A@230V, ronda ~0.22 A a 207 V) → total
≈0.80 A, sigue siendo solo el 50% del rating de 1.6 A — cómodo.

El portafusible **no cambia**: sigue siendo el Schurter FPG4 (cerrado, IEC
60335-1, 250 VAC/**10 A** VDE) — 1.6 A queda muy por debajo de su límite
mecánico/térmico, solo cambia el elemento fusible que se inserta.

**Actualizado**: `bom.csv` v2, fila F1 (valor "1.6A lento" en vez de "250mA
lento", nota con la aritmética completa) y `build_schematic.py` v2 (Value de
F1 = "1.6A T").

### §3.0.1 Worksheet de arranque (I²t) — fix F1 del task review

**Hallazgo del review**: el valor 1.6 A T queda, pero la nota original no
cuantificaba el arranque en frío ni el trade-off de protección que implica
subir 6.4× el fusible respecto a v1. Se cierra aquí con números.

**Supuestos declarados** (modelo simplificado a mano, no una simulación
SPICE):

1. Peor caso de conexión: el interruptor de red cierra en el PICO de la
   sinusoide (325 V), con los bulk caps totalmente descargados — es el
   escenario clásico de peor caso en una fuente offline con rectificador
   de entrada por capacitor.
2. Se ignora la inductancia de fuga de TR1 y el ESR de los bulk caps —
   modelo puramente resistivo (solo NT1 en frío, 5 Ω, limitando). Esto es
   **conservador**: cualquier inductancia real en serie limitaría el di/dt
   y bajaría el pico real, así que el número que sale de aquí es un techo,
   no un piso.
3. Corriente pico: I_pk = V_pk / R_NTC(frío) = 230×√2 / 5 ≈ **65.05 A**
   (mismo orden que orientaba el task review, ~65 A).
4. Forma del primer semiciclo: se aproxima como un semiciclo senoidal
   COMPLETO a esa amplitud (10 ms a 50 Hz) — sobreestima el I²t real,
   porque en la práctica NT1 se autocalienta (su R cae, es NTC) y los
   bulk caps ya tienen algo de carga antes de completar el semiciclo, así
   que el pico real decae antes del final de esos 10 ms.
5. Segundo semiciclo: con NT1 más caliente pero los bulk caps ya con
   carga parcial (menos tensión disponible para forzar corriente), se
   asume conservador una amplitud del 50% del pico (~32.5 A). Semiciclos
   posteriores se desprecian — su aporte marginal al I²t total es chico
   frente a los dos primeros.

**Cálculo:**

```
I_pk = 230 x sqrt(2) / 5 = 65.05 A

I²t(semiciclo 1, senoidal, T=10ms) = I_pk^2 x (T/2)
  = 65.05^2 x 0.005 = 21.2 A²s

I²t(semiciclo 2, ~50% amplitud) = (0.5 x 65.05)^2 x 0.005
  = 32.53^2 x 0.005 = 5.3 A²s

I²t total estimado (primeros ~20 ms) ~= 21.2 + 5.3 ~= 26.5 A²s
```

**Comparación contra el fusible**: un 5×20 T (slow-blow) de 1.6 A tiene un
I²t de fusión (melting I²t, no el "no-fusión" a 10 s de las curvas
tiempo-corriente) que ronda **10-30 A²s según el fabricante** — Bel,
Littelfuse y Schurter no publican el mismo número para la misma corriente
nominal, y esta puerta no tuvo acceso a un datasheet concreto de fusible
para confirmarlo. Con el estimado de arranque de ~26.5 A²s, **el margen es
fino**: si el fusible comprado cae en la parte baja del rango típico
(10-15 A²s) hay riesgo real de que el arranque en frío lo funda
espúreamente; si cae en la parte alta (25-30 A²s) sobrevive, pero con poco
colchón. No se puede cerrar esta pregunta sin el datasheet del fusible
concreto que se compre — **acción documentada en `bom.csv` v2, fila F1**:
verificar I²t ≥ ~27 A²s contra ese datasheet antes de comprar.

Esto NO invalida el dimensionamiento por corriente nominal (0.722 A × 2.2
de margen = 1.6 A, §3.0 arriba) — es un chequeo independiente y adicional,
igual que §1.5.1 fue un chequeo independiente del GO de §1.5.

### §3.0.2 Trade-off de protección: qué deja de cubrir F1 a 1.6 A

**Hallazgo del review**: subir F1 6.4× (250 mA → 1.6 A) no es gratis — hay
una ventana de corriente de fallo que el fusible viejo SÍ abría y el nuevo
YA NO abre en tiempo útil.

Un fusible T (slow-blow) de 1.6 A típicamente NO abre en un tiempo útil
(según su propia curva tiempo-corriente) para una corriente SOSTENIDA entre
aproximadamente **0.4 A y 2 A** — por debajo de ~1.35× su nominal (2.16 A)
puede tardar minutos u horas en abrir, y cerca de 1× (1.6 A) puede no abrir
nunca en régimen permanente. Con el fusible viejo de 250 mA, esa misma
ventana de corriente (0.4-2 A) SÍ habría disparado la protección en
segundos. Ejemplos reales de falla que caen en esa ventana:

- Fallo parcial del bobinado primario de TR1 (cortocircuito entre espiras,
  no total) que sube la corriente de magnetización sin llegar a un
  cortocircuito franco.
- Fuga sostenida de un MOV (RV1) degradado por sobretensiones repetidas —
  un MOV envejecido puede empezar a conducir en fuga sin llegar al corto
  catastrófico que dispara F1 al instante.

**Mitigantes reales** (no elimina el gap, lo acota):

1. RV1 (MOV) sigue ahí para transitorios reales (el escenario que SÍ
   dispara F1 rápido: un corto franco del MOV o un pico de red que lo hace
   conducir duro).
2. El portafusible es CERRADO (Schurter FPG4, no de clips abiertos) —
   contiene un fallo aunque tarde en abrir, no hay arco expuesto dentro
   del cajón.
3. Muchos transformadores toroidales de esta potencia vienen con un
   **fusible térmico embebido en el propio devanado** (protección térmica
   independiente de F1, dispara por temperatura del bobinado, no por
   corriente de línea) — si el TR1 comprado lo trae, cierra buena parte de
   este gap de forma independiente del dimensionamiento de F1. **Acción
   documentada en `bom.csv` v2, fila TR1**: confirmar si el TR1 comprado
   (Talema 0120P1-2-012 u otro fabricante) trae fusible térmico embebido
   antes de dar el diseño por cerrado en este punto.

Este trade-off es inherente a la decisión de subir F1 para que no se funda
en operación normal (§3.0 arriba) — no es un error de esta tarea, es el
costo real de la corrección, y queda documentado explícito en vez de
maquillado.

### §3.1 Task 4 Step 1 — mapa ref→etapa de la v1

Leído con `grep -n -B3` sobre `hardware/01-power-supply/kicad/build_schematic.py`
(líneas exactas citadas abajo). Comentarios inline y posición X/Y del script
son los que asignan cada pasivo a su etapa — el bom.csv v1 no lo dice
explícito (agrupa C7+C11 y D1+D2+D5 en una sola fila por *valor*, no por
etapa, ver más abajo).

| ref(s) v1 | etapa | evidencia (`build_schematic.py`) | v2 |
|---|---|---|---|
| C1,C2,C12,C13 | bulk (rectificación, común a ambos rieles ±12V) | L189/L199, `4700uF/25V` en ambas filas de coordenadas (+12 y −12) | **sobrevive**, tal cual |
| C3 | entrada de U1 (LM2940, riel +12V) | L190 `0.47uF` en la columna X=XU,Y=69.85 (fila +12V) | **muere** con la etapa; reemplazo conceptual: C27 (entrada U1 nuevo/LM2941) |
| U1 (v1) | LM2940CT-12 | L191 `Regulator_Linear:LM7812_TO220` | **muere**; designador U1 se reutiliza en v2 para el pre-reg LM2941CT |
| C5 | salida de U1 (cap. de estabilidad, ESR) | L192 `100uF/25V ESR` | **muere**; reemplazo conceptual: C17 |
| C7 | desacoplo HF de salida de U1 | L193 `0.1uF`, misma fila +12V (69.85) | **muere**; en el bom.csv v1 estaba agrupado con C11 en una sola fila ("C7,C11") — se separan en v2 |
| D1 | anti-backfeed de U1 | L194 `1N4001` en fila +12V | **muere**; reemplazo conceptual: D12 (out→in del U1 nuevo) |
| R1 | limitadora del LED indicador +12V | L195 `2k2`, no depende del regulador que hace el riel | **sobrevive** — el LED indica el riel, no la etapa |
| C13,C4,U2(v1),C6,C8,D2,R2 | etapa completa de U2 (LM2990, riel −12V) | L199-205 (fila Y=163.83/187.96/144.78) | C13 es bulk → **sobrevive**; C4 (entrada), U2(v1), C6 (salida), C8 (DNP), D2 (anti-backfeed) → **mueren**; R2 (LED −12V) → **sobrevive** |
| J2 | bus de salida ±12V/GND hacia módulos | L207 | **sobrevive** |
| C9,U3,C10,C11,D5 | etapa +5V completa (LM7805) | L210-214, fila `Y5_ROW` | **TODOS sobreviven** — U3 sigue vivo en v2 |
| R3 | limitadora del LED indicador +5V | L218 `680` | **sobrevive** |
| D7,Q1,R4,C14 | crowbar del riel +12V | L650-652 | **sobrevive completo** |

**Etapas que mueren por completo**: U1(v1)=LM2940 y todos sus pasivos
directos (C3, C5, C7, D1); U2(v1)=LM2990 y todos sus pasivos directos (C4,
C6, C8, D2). Los designadores U1/U2 se **reutilizan** en v2 para los
pre-reguladores LM2941CT/LM2991T (misma posición en la cascada — entrada de
red regulada — pero ahora alimentan a la pareja LT3045/LT3094 en vez de ser
el regulador final).

**Ojo con la agrupación por valor del bom.csv v1** (no por etapa): la fila
`"C7,C11",0.1uF ceramico,...` mezcla un componente que muere (C7, etapa U1)
con uno que sobrevive (C11, etapa U3) porque ambos tienen el mismo valor de
0.1 µF — igual la fila `"D1,D2,D5",1N4001,...` mezcla dos que mueren (D1,
D2) con uno que sobrevive (D5, etapa U3). El Step 2 de Task 4 separa estas
dos filas: hereda solo C11 y D5, con cantidad 1 cada una.

### §3.2 Asimetría térmica intra-pareja de las granjas EP (review fase C, F5)

**Hallazgo del review**: las granjas de vías térmicas del EP de U4-U7
(ballast LT3045/LT3094, pareja +12V y pareja −12V) no quedaron simétricas
entre los dos chips de cada pareja — restricciones reales de routing
(clearance hole-to-hole, pines vecinos, corredores ya ocupados por otras
redes) forzaron un reparto desigual:

- **U4**: 4 vías (rejilla 2×2, paso 0.6 mm).
- **U5**: 6 vías (rejilla 2×3, paso 0.6×0.7 mm — la huella del EP es
  1.65×2.38 mm, más alta que ancha, y U5 sí tenía sitio limpio para la
  tercera fila).
- **U6**: 4 vías de la granja nueva (2×2) **+ 1 vía vieja de 0.5 mm de
  taladro** que ya existía como transición F/B del tronco `/-12V9` en
  (120, 169) y hace de ancla — 5 puntos de contacto térmico en total.
- **U7**: 4 vías (rejilla 2×2) — sin vía extra: el stub F.Cu del pin 3 al
  EP se alargó 0.5 mm hasta aterrizar exacto en una de las cuatro vías de
  su propia granja, que hace de ancla sin necesitar una vía adicional.

**Por qué se acepta tal cual (no se re-rutea)**: el reparto de corriente
entre los dos chips de una misma pareja lo domina el ballast de 20 mΩ en
serie con cada uno (R15/R16 para +12V, R17/R18 para −12V) — es una
resistencia de balance deliberada, mucho mayor que cualquier diferencia de
resistencia térmica entre 4 y 6 vías de 0.3 mm. El efecto real de la
asimetría es una diferencia de temperatura de juntura leve entre los dos
chips de una pareja (U4 más caliente que U5, o U6 más caliente que U7 —
menos vías = más resistencia térmica del EP a la plancha de cobre), no un
desbalance de corriente. Con ~0.33 W por chip (spec sec.6.1) el margen
térmico de un DFN-10/12 sobra incluso con la granja más pobre (4 vías).

**Acción si la mula lo desmiente**: si las medidas térmicas (§4, con
cámara termográfica o termopar sobre cada chip) muestran **más de 5 °C**
de diferencia entre los dos chips de una misma pareja (U4 vs U5, o U6 vs
U7) en operación sostenida a plena carga, revisar aquí — la vía adicional
de U6 y las dos vías extra de U5 dejarían de ser una curiosidad de layout
y pasarían a ser sospechosas de un desbalance real que el ballast de 20 mΩ
no está absorbiendo del todo.

## §4 Campaña de medidas — sobre la v2 misma

> **Decisión (2026-08-17): la v1 no se construye.** El plan original usaba la v1
> de mula de medidas y congelaba la v2 contra sus números (spec §11.4). Se va
> directo a la v2. La v1 queda como diseño documentado y cerrado, no como
> hardware. Consecuencias, sin maquillar:
>
> - **Lo que se gana:** el front-end (Talema 120 VA, BR1, 4×4700 µF) se compra
>   una vez, no dos, y desaparece la puerta que bloqueaba el pedido. El valle
>   simulado ya no hace falta confirmarlo *antes* de fabricar porque los
>   setpoints son ajustables en sitio con RV2/RV3 — el trimmer **es** el
>   sustituto de la mula, no un adorno.
> - **Lo que se pierde:** si el valle real está muy por debajo del simulado, te
>   enteras con la placa ya fabricada y montada, no antes. El umbral exacto a
>   partir del cual el trimmer ya no salva la placa está en §4.1 — **léelo antes
>   del paso 5 del bring-up.**
> - **Lo que desaparece:** la fila 3 de la tabla (comparativa de rizado v1 vs
>   v2) no se puede medir sin una v1 física.
> - **Lo que sube de riesgo:** la v2 pasa a ser la única fuente del sistema. No
>   hay fuente de respaldo para los módulos 2-7 mientras se depura.

**Orden a seguir tras bring-up exitoso §5:** tierra y continuidad verificadas,
placa sin carga a setpoint nominal (TP7 = +13.1 ± 0.3 V, TP8 = −12.9 ± 0.3 V).
Cada medida cierra un número de **diseño congelado** — los resultados informan
qué setpoints de RV2/RV3 se dejan puestos en la pareja de LM2941/LM2991.
Medir con red a la tensión real del día.

### Tabla de medidas

| # | Medida | Cómo | Resultado |
|---|---|---|---|
| 1 | Valle `VRAW+` y `VRAW−` (piso del rizado, no promedio) | Con carga dummy 18 Ω / 25 W por riel (12 V / 0.65 A) en **frío** y tras **30 min en caliente**. Medir con osciloscopio DC acoplado, 20 MHz BW limitado, punta en J2. Anotar la tensión de red en el momento. | (vacío) |
| 2 | Pico nominal en vacío (sin dummy) | Con red a la tensión medida en paso 1. Valor esperado: ~14 V; documentar para cierre de margen §1.5. | (vacío) |
| 3 | ~~Rizado pico-pico real del riel −12 V de la v1~~ | **ANULADA** — la v1 no se construye (ver cabecera de §4). La comparativa v1/v2 se queda sin lado v1; el rizado de la v2 se mide igual en el paso 6 del bring-up §5. | n/a |
| 4 | Térmica en régimen: T_case y disipador | IR cámara termográfica u 8 termopares (U1/U2, U4-U7, disipadores FK sk129/38.1). Régimen: dummy 18 Ω × 30 min, después medir T cada 5 min hasta T_case estable (frontera). Anotar T_ambiente. Expectativa: < 70 °C en el TO-220 (§10.4.1 del datasheet del LM2941); cerámicos DFN < 90 °C. | (vacío) |

### Fórmula de cierre de márgenes

Por cada riel, después de **todos los pasos anteriores**, calcular:

```
margen = valle_medido − dropout_max(riel) − setpoint_nominal
```

- `valle_medido`: valor pico inferior de VRAW+/VRAW− del paso 1, en frío (es el
  escenario conservador).
- `dropout_max(riel)`: del datasheet respectivo, MAX garantizado sobre temperatura
  (LM2941 @ 650 mA: 1.0 V; LM2991 @ 650 mA: 1.0 V — ver §1.1/§1.2).
- `setpoint_nominal`: TP7 medido (+13.1 V) o TP8 medido (−12.9 V) tras bring-up §5
  con carga dummy.

**Regla de ajuste**: si margen < 0.2 V, bajar el setpoint girando RV2 (positivo) o
RV3 (negativo) hasta recuperar margen ≥ 0.2 V. **Rango útil del trimmer** (suelo
bajable garantizado por headroom del LT3045/LT3094, §1.5.1): **12.46 V** (positivo) /
**−12.42 V** (negativo). No bajar más allá — el margen del LT vs el dropout de la
cascada se agota.

### §4.1 Umbral de aborto: el valle mínimo que la placa aguanta

Sin mula, la primera medida del valle se hace ya con la v2 fabricada. Esta es la
cuenta que dice si el trimmer puede salvarla o no. Encadenando los dos dropouts
garantizados (no típicos) de §1.5 y §1.5.1:

```
valle_mínimo = 12.000 V (V_OUT) + dropout_max(LT) + ballast (0.007 V) + dropout_max(pre-reg, 1.0 V)

Positivo (LT3045, bin 500 mA, MAX 450 mV):
  12.000 + 0.450 + 0.007 + 1.000 = 13.457 V   ← el que manda
Negativo (LT3094, bin 500 mA, MAX 410 mV):
  12.000 + 0.410 + 0.007 + 1.000 = 13.417 V
```

**El umbral es 13.46 V** (lo fija el riel positivo; ambos rieles comparten
front-end, así que el valle es prácticamente el mismo en magnitud).

| | Valor |
|---|---|
| Valle simulado (§16.5 de la v1, red a 207 V, plena carga) | **14.12 V** |
| Valle mínimo viable | **13.46 V** |
| **Colchón contra la simulación** | **0.66 V (4.7 %)** |

Léelo así: **el valle real puede salir hasta 0.66 V por debajo del simulado y la
placa sigue siendo recuperable girando RV2/RV3.** Ese colchón es lo que compra
saltarse la mula. Por debajo de 13.46 V medidos no existe setpoint que funcione —
ningún giro de trimmer arregla eso.

**Lo que se espera realmente que pase en el paso 5 del bring-up:** el setpoint
nominal del riel positivo (13.1 V) tiene solo **+0.02 V** de margen contra el
valle simulado (§1.5). Eso no es margen, es empate. Con el valle en 14.12 V el
techo del pre-reg queda en 13.12 V, así que para cumplir la regla de margen
≥ 0.2 V hay que **bajar RV2 hasta ~12.9 V**. No es un fallo: es el primer
ajuste previsto, y cae cómodamente dentro del rango (suelo 12.46 V). El riel
negativo ya nace con +0.22 V y probablemente no haya que tocarlo.

**Si el valle medido cae por debajo de 13.46 V**, en orden de coste:

1. **Subir el bulk.** El valle lo fijan trafo + BR1 + C1/C2/C12/C13, todos THT.
   Colgar más electrolítico en paralelo sube el valle sin rediseñar la placa —
   es el arreglo barato y no toca el cobre.
2. **Aceptar salida por debajo de 12.000 V.** Si los módulos 2-7 toleran
   ±11.9 V, el umbral entero se relaja ~100 mV. Decisión de sistema, no de
   la fuente.
3. **Revisar la premisa de red.** El valle de 14.12 V está simulado a 207 V
   (red −10 %). Si la red real está en nominal, el valle medido debería salir
   por encima del simulado, no por debajo — un valle bajo con red nominal
   apunta a trafo o bulk, no a margen de diseño.

## §5 Bring-up escalonado

Orden recomendado al recibir la PCB montada (antes de conectar módulos o carga real):

1. **Continuidad de tierra (equipo desenchufado)**. Óhmetro entre la clavija de tierra
   del enchufe, cada panel, el espárrago y el faston de J5. Miliohmios o decenas de
   miliohmios (§13.4). Si falla, no se enchufa.

2. **Inspección visual**. Polaridad de electrolíticos, orientación de reguladores,
   cortos en el silk. **Punto crítico**: esquina `+` moldeada en BR1 contra cruz `+`
   del silk (pad 1); girado 180° cabe igual y cruza el puente en el primer semiciclo.
   Mica y casquillo aislante en U2 (LM2991), tab NO está a masa (§1.2).

3. **Solo trafo sin placa**, sin carga. Medir ±17 V entre fase y neutro tras BR1.
   Desenchufar. Insertar reguladores THT en sus zócalos.

4. **Placa sin carga**: enchufe con corriente — TP7 = +13.1 ± 0.3 V (prerreg +12V),
   TP8 = −12.9 ± 0.3 V (prerreg −12V). Los test points ya están serigrafiados con su
   señal en la placa (TP7=+13V1, TP8=−12V9). Si alguno está fuera de rango, no
   conectar carga; revisar setpoints RV2/RV3 (giro manual, trimmer cerrado, ~10
   vueltas) hasta meterlo en banda.

5. **Conectar dummy 18 Ω / 25 W por riel** a J2 (medir con multímetro para verificar
   ~12 V/0.6 A en ambos rieles). Anotar que esta es la medida con carga nominal de
   diseño (§4, paso 1).

   **Aquí está la puerta que antes cerraba la mula.** Con la dummy puesta, medir el
   valle de `VRAW+`/`VRAW−` con osciloscopio (DC, 20 MHz BW) **antes de dar por buena
   la placa**, y compararlo contra el umbral de **13.46 V** de §4.1:
   - Valle ≥ 13.46 V → bajar RV2 hasta dejar margen ≥ 0.2 V (se espera aterrizar
     en ~12.9 V en el positivo; el negativo suele no necesitar toque). Seguir.
   - Valle < 13.46 V → **parar**. Ningún setpoint funciona; ir a la lista de
     remedios de §4.1 (subir bulk / relajar V_OUT / revisar red y trafo).

6. **Medir rizado pico-pico** en cada riel con osciloscopio (DC coupling, 20 MHz BW
   limitado, punta en J2 — misma condición que §4 filas 1 y 3). Criterio mínimo
   (spec §10.4): rizado bajo el suelo medible del osciloscopio con esa BW
   (~sub-mV, ya 10× mejor que v1) — no es un umbral numérico fijo tipo "< X mVpp".
   Criterio pleno de aceptación: medir con LNA delante (equipo aparte, issue #58 —
   «LNA de medida para el nivel pleno del GOAT»).

7. **Termograma o termopar** en U1/U2 (TO-220, disipadores de 38 mm) y en U4-U7 (DFN)
   tras 30 min a plena carga (dummy activada). Expectativa: < 70 °C en TO-220,
   < 90 °C en DFN. Si T_case de U4 vs U5 o U6 vs U7 difieren > 5 °C, documentar en §3.2.

8. **Llenar la tabla de §4** con los números medidos. Calcular margen de cada riel y
   aceptar (margen ≥ 0.2 V) o reajustar setpoints si es necesario.
