# Módulo 1 — Notas de diseño: Alimentación

> Nota de diseño viva para el módulo de alimentación del SAM17. Se escribe
> **antes** de capturar el esquemático para que las decisiones queden
> trazadas. Ítem del [epic #2](https://github.com/sssamuelll/analog-modular-synthesizer/issues/2),
> sección 1.

## 1. Contexto y punto de partida (tesis)

La tesis (Capítulo III, *Módulo de Alimentación*, gráficos 22-24) propone:

- Transformador externo **12 VAC 2 A** a 110 VAC 60 Hz.
- Reguladores lineales **LM7805 / LM7812 / LM7912** (pinout TO-220).
- Condensadores electrolíticos **4700 µF / 25 V** en el filtrado.
- Bus interno de distribución (pin header genérico) hacia cada módulo.
- **Transformador independiente** para el Raspberry Pi vía micro-USB, de modo
  que el riel +5 V del módulo no tenga que absorber los picos de hasta 2 A que
  consume el Pi.

El prototipo reportado en la tesis **funciona y entrega las tres tensiones
correctas**. No hay mediciones de rizado ni de deriva bajo carga.

## 2. Presupuesto de corriente por riel (derivado de los datasheets)

> **⚠️ SECCIÓN DE LA ÉPOCA DE LA TESIS — SUPERADA POR §16 Y POR EL CENSO.**
> Las dos filas que dominan esta tabla ya no existen: el **LCD 16×2 murió en la
> rev. 2** de la spec del case y el **Raspberry Pi en la rev. 3**, cuando el
> cerebro pasó a **RP2350** ([architecture-poly §2](../../../docs/architecture-poly.md)).
> El VCO tampoco son 3× CEM3340: es el módulo 3 con **4× SSI2130**, ~35 mA/riel
> medidos contra su BOM real. Se conserva como registro de por dónde empezó el
> cálculo — **no se usa para dimensionar nada**.
>
> **Los números vigentes:** ±12 V → censo cerrado el 2026-08-18 en
> [spec fuente v2 §8](../../../docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md),
> **~116 mA/riel a 4 voces** contra un envelope de 650. +5 V → §16.12, acotado a
> **300 mA como límite de diseño**, no como estimación.

Inventario de chips por módulo en el peor caso (todos los módulos instalados):

| Chip | Dónde | I típica (por chip) | Cantidad | Total |
|------|-------|---------------------|----------|-------|
| CEM3340 | VCO (×3) | ~20 mA @ ±12 V (ver §8) | 3 | **~60 mA en +12, ~60 mA en −12** |
| LM13700 | VCF + VCA | 2.6 mA @ ±15 V (typ) | 2 | ~5 mA cada riel |
| TL074 | Mixer, VCF, VCA, ADSR, MIDI/CV | 2.5 mA @ ±15 V (typ) | ~5 | ~13 mA cada riel |
| LM358 | ADSR | 1 mA | 1 | 1 mA +12 V |
| ICM7555 | ADSR | 60 µA CMOS | 1 | despreciable |
| AD5686R | MIDI/CV | ~1 mA VDD @ 5 V | 1 | 1 mA +5 V |
| LCD 16×2 (HD44780) | MIDI/CV | 1.5 mA lógica + ~100 mA backlight | 1 | ~100 mA +5 V |
| Raspberry Pi 3B+ | MIDI/CV | 400 mA idle / 1.3 A pico | 1 | **1.3 A +5 V** |

### Totales con margen de seguridad (×1.5)

| Riel | Suma cruda | × 1.5 | Mínimo recomendable |
|------|-----------|-------|---------------------|
| +12 V | ~80 mA | 120 mA | **300 mA** (futuros módulos) |
| −12 V | ~80 mA | 120 mA | **300 mA** |
| +5 V (con Pi) | ~1.4 A | 2.1 A | **2.5 A** |
| +5 V (sin Pi, sólo LCD + DAC) | ~100 mA | 150 mA | 300 mA |

**Conclusión de entonces** (ya no aplica): *«el problema está en +5 V por el
Raspberry Pi; mantener el enfoque de la tesis —fuente dedicada para el Pi— es la
decisión más limpia»*. Sin Pi y sin LCD, el +5 V del módulo 1 solo alimenta el
AD5686R: el problema que esta sección identificó **desapareció con las piezas
que lo causaban**. Los ±12 V siguen holgados, y por más margen del que decía.

## 3. Decisión de arquitectura

Tres opciones sobre la mesa:

### Opción A — Tesis (recomendada para reproducción fiel)
- Transformador 12 VAC 2 A para los rieles ±12 V del módulo (y un ±5 V
  auxiliar si se quiere).
- **Wall adapter 5 V 2.5 A USB** independiente para el Raspberry Pi.
- Ventaja: el ruido de conmutación del Pi **nunca contamina** el plano
  analógico.
- Inconveniente: dos cables a la pared.

### Opción B — Todo-en-uno
- Transformador 15 VAC 3 A → rectificación → regulador 5 V de alta corriente
  (ej. LM2596 step-down) para el Pi + 7812/7912 para analógico.
- Inconveniente: la corriente pico del Pi inyecta rizado en el riel común de
  entrada; difícil de filtrar sin comprometer THD del audio.

### Opción C — Estándar Eurorack
- Adoptar el formato de bus Eurorack (IDC 16 pin: ±12 V / +5 V / GND).
- Ventaja: compatibilidad con módulos comerciales y bus boards existentes
  (Doepfer, Befaco Excalibus, 4ms Pod).
- Inconveniente: se aleja de la tesis; mejor hacerlo como *epic* separado.

**Decisión propuesta para este módulo**: **Opción A**. Tracking directo de la
tesis, con mejoras conservadoras de calidad (ver §5).

## 4. Topología detallada propuesta

```
          110 VAC               12 VAC CT        ~17 VDC              +12 V / +300 mA
   Red ──┤├──────────► TR1 ──────────────► BRIDGE ──► C1  ────► 7812 ────────────►
    60Hz F1 (1A fast)       (split sec)     B1      4700uF 25V  TO-220           Cout ·· OUT
                                                     ║           │ HS1            100uF
                                                    GND          │
                                                                 │
                                                               bulk
                                                             (star GND)
                                                                 │               −12 V / −300 mA
                                                                 ├────► C2 ────► 7912 ────────────►
                                                                      4700uF 25V  TO-220           Cout ·· OUT
                                                                       ║          │ HS2            100uF
                                                                      GND         │
                                                                                  │
                                                                                  ├──► 7805 (OPC*) ──► +5 V AUX
                                                                                         (no Pi)
    (Pi alimentado por wall-adapter 5V USB aparte)
```

**Notas clave**:

- F1: fusible 500 mA lento en el primario del transformador (ante corto en
  secundario).
- TR1: 12 VAC center-tapped 2 A. Después del puente rectificador → ~±17 VDC
  pico (suficiente margen para el **dropout de 2 V** del 7812/7912 a corriente
  nominal).
- C1 / C2: **4700 µF / 25 V** bulk, uno por riel.
- Capacitor de entrada del regulador: **0.33 µF cerámico** (según datasheet TI
  LM78xx, punto crítico si la distancia al bulk > 5 cm).
- Capacitor de salida: **0.1 µF + 100 µF** (estabilidad transitoria, necesario
  en el 79xx).
- Disipadores TO-220 obligatorios (§6).
- **Aislar eléctricamente el tab del 7912** del chasis (tab = pin de entrada
  negativo, no GND — gotcha conocido).
- Diodos 1N4001 en **anti-paralelo** desde la salida a la entrada (protección
  contra backfeeding cuando se apaga con carga inductiva aguas abajo).
- LEDs de estado en cada riel con resistencia de 2.2 kΩ a GND.

## 5. Mejoras conservadoras sobre la tesis (no introducen nuevo riesgo)

Ordenadas por valor/esfuerzo:

1. **Fusible primario 500 mA lento** (la tesis no lo menciona).
2. **LEDs indicadores por riel** (sanity check visual en bring-up).
3. **Diodos de protección reversa** en salida de cada regulador.
4. **Condensador cerámico 0.1 µF** en entrada de cada regulador (hoja de
   aplicación del fabricante).
5. **Zócalo TO-220** para los reguladores (swap fácil si uno falla).
6. **Bus board PCB** con pin headers duplicados (2×3 ó 2×5) para facilitar la
   expansión sin soldadura.
7. **Ground star** físico: un único punto donde se unen los GNDs de ambos
   condensadores bulk y el retorno del bus.

## 6. Cálculo térmico

> **⚠️ CÁLCULO DE OTRO CIRCUITO — SUPERADO POR §16.7.**
> Esta cuenta usa **LM78xx** y un disipador genérico de 20 °C/W. La placa real
> no lleva ninguno de los dos: `U1` es un **LM2940CT-12** y `U2` un
> **LM2990T-12** (§16.3), y el disipador es el **Fischer SK 129/38,1** —
> 6.5 K/W vertical, **7.7 K/W acostado**, que es el número que vale.
>
> La diferencia no es cosmética: §16.7 da **Tj ≈ 89 / 101 / 91 °C** a 45 °C de
> ambiente, ~30-40 °C por encima de los 62.5 °C que sale abajo. Y el más
> caliente es `U2`, no `U1`, porque paga el aislante de mica que le exige tener
> el tab a VIN.
>
> Se conserva como registro. **Para dimensionar disipador, caja o ventilación,
> el número es el de §16.7.**

Regulador +12 V caso crítico (todo el sistema encendido, 300 mA):

```
Vin_pk    = 17 V  (tras puente y filtrado)
Vout      = 12 V
Vdrop     = 5 V
Iload     = 0.3 A
P_reg     = Vdrop × Iload = 5 V × 0.3 A = 1.5 W
```

Datasheet TI LM78xx (TO-220): `R_thJA = 65 °C/W` (sin disipador), `R_thJC =
5 °C/W`. Con disipador pequeño de ~20 °C/W:

```
T_rise    = P × (R_thJC + R_thSA)
          = 1.5 W × (5 + 20) °C/W
          = 37.5 °C
T_junction ≈ 25 + 37.5 = 62.5 °C  ✔ (< 125 °C protección térmica)
```

Con un disipador del tamaño estándar **HS TO-220 con aleta** (≈ 15 °C/W) la
temperatura de junction se mantiene incluso por debajo de 60 °C — confortable.

El regulador +5 V (`U3`, 7805) **no se suprime**: es quien alimenta el AD5686R.
La rama condicional que había aquí —*«si el Pi sigue independiente, se puede
suprimir»*— se resolvió sola: no hay Pi. Su disipación real está en §16.7
(Tj ~91 °C) y su riel acotado a 300 mA en §16.12.

## 7. Grounding y distribución

- **Star ground** en el bulk del riel positivo. Desde ahí salen:
  - Retorno de TR1/puente.
  - Retorno del bulk negativo.
  - Retorno del bus de distribución.
  - **Puente al chasis** — ya no es un «sólo si se quiere»: es obligatorio y va
    por `J5`. Resuelto en §13, incluido por qué el bucle de tierra no se puede
    evitar aquí aunque se quiera.
- Distribución por **bus board dedicado** (PCB con pin headers en paralelo),
  no daisy-chain soldado en cada módulo. La tesis reportó justo este problema
  con sus cables jumper.
- Trazas de potencia con sección suficiente para **< 20 mV de caída** entre
  el regulador y el módulo más lejano a 300 mA (estimación a validar durante
  el routing del bus board).
- Separar físicamente los retornos analógico y digital; unirlos **en el punto
  de estrella**, no en los módulos. Resuelto a nivel de interfaz en §10.4: el
  +5 V digital sale por `J6` con su propio retorno, no por el bus de `J2`.

## 8. Zona gris: corriente del CEM3340

El dato de consumo del CEM3340 no aparece con claridad en las copias del
datasheet disponibles en la red (la sección de especificaciones eléctricas
llega distorsionada en los PDFs consultados). Referencias de diseñadores
experimentados:

- La mayoría de clones modernos (Electric Druid, Rosen Sound, AS3340 de
  Alfa-Rpar) reportan consumos típicos **≈ 15–20 mA por rail** cuando se
  usa con ±12 V y las recomendaciones de biasing de Curtis.
- El chip **no tolera > 24 V entre sus supply pins**: obliga a colocar un
  zener de 6.5 V en el pin 3 cuando se usa con +12 V para limitar la
  tensión interna (discusión clásica en la wiki Synth DIY).

**Acción derivada**: al capturar el esquemático del VCO (módulo 3), no
olvidar el **zener de 6.5 V** en el pin 3 del CEM3340. Esto no afecta al
diseño de la fuente en sí, pero es una dependencia crítica.

## 9. Checklist de bring-up

Orden sugerido al recibir la PCB fabricada (antes de conectar ningún otro
módulo):

1. **Continuidad de tierra, con el equipo desenchufado y ANTES de nada más**:
   óhmetro entre la clavija de tierra del enchufe y cada panel, el espárrago y
   el faston de `J5`. Miliohmios (§13.4). Si esto no pasa, no se enchufa.
2. **Inspección visual**: polaridad de los electrolíticos, orientación de
   los reguladores, cortos en el silkscreen. Y **la orientación de `BR1`**:
   la esquina `+` moldeada en el cuerpo del DB207 va a la cruz `+` del silk
   (pad 1); girado 180° encaja igual y cruza el puente (§14.6) — si esto está
   mal no se nota mirando la placa, se nota en el primer semiciclo.
3. Conectar **sólo el transformador** (sin carga), verificar ±17 V tras el
   bridge.
4. Insertar reguladores en sus zócalos, verificar **+12 V ±1 %** y **−12 V
   ±1 %** en las salidas.
5. Conectar carga resistiva (100 Ω, ~120 mA) en cada riel, medir la caída
   de tensión (expectativa: < 50 mV).
6. Medir **rizado pico-pico** con osciloscopio (DC coupling, 1 MHz BW):
   objetivo **< 10 mVpp** a plena carga.
7. **Termograma o termopar** en los reguladores tras 15 min a plena carga
   (expectativa: < 70 °C en el cuerpo del TO-220).
8. Documentar en `hardware/01-power-supply/notes/bring-up.md`.

## 10. Decisiones resueltas

### 10.1 Riel +5 V → **integrado en la PCB del módulo**

Aunque el Raspberry Pi se alimente por su propio adaptador USB, la sección
analógica/digital local **necesita +5 V** para:

- **AD5686R** (DAC del MIDI/CV): VDD 2.7 – 5.5 V, decoupling 10 µF ∥ 0.1 µF.
- **LCD HD44780**: 5 V para lógica + ~80–100 mA del backlight.
- Posibles módulos futuros (digital control, sensores).

Carga estimada del riel +5 V (sin Pi):

| Consumidor | Corriente |
|------------|-----------|
| AD5686R | ~1 mA |
| LCD lógica | ~1.5 mA |
| LCD backlight | ~100 mA (peor caso, sin PWM) |
| Margen ×1.5 | — |
| **Total +5 V** | **~150 mA** |

**Disipación del 7805 alimentado desde el bulk +17 V**:

```
P_5V = (17 − 5) × 0.15 = 1.8 W
```

Con disipador estándar TO-220 (~20 °C/W): `Tj ≈ 25 + 1.8 × (5 + 20) = 70 °C`
— margen amplio sobre los 125 °C de protección térmica.

**Recomendación operativa**: PWM-ear el backlight del LCD para bajar la
corriente media a ~30 mA cuando el menú no se está usando (lo implementa
el firmware en `software/midi-cv/sam17/hardware/lcd.py`).

**Layout crítico**: la corriente del backlight (variable y relativamente
alta) puede crear *ground bounce* que se acople al plano analógico. Mitigar
con:

- Retorno **dedicado** del +5 V hasta el punto de estrella, **separado** del
  retorno analógico hasta el último cm.
- Trazas de potencia gruesas (≥ 1 mm) para el circuito del LCD.

### 10.2 Soft-start con NTC → **incluido**

Justificación: la suma de los electrolíticos (4700 µF en +V + 4700 µF en −V
+ 100 µF tras cada regulador) produce un inrush significativo al encender
en frío. Sin limitación, el puente rectificador y los condensadores quedan
expuestos a picos de cientos de amperios en el primer hemiciclo.

**Selección**: NTC inrush limiter en **serie con el primario AC**:

- Rating recomendado: **5 Ω fríos / 2 A continuos** — p. ej. **Ametherm
  SL10 5R020** o **Vishay NTCS010** equivalente.
- Caliente (régimen): R ≈ 0.2 – 0.5 Ω, caída despreciable a 2 A.
- Posición: entre F1 y el primario del transformador.

**Compromiso**: se sacrifican ~0.4 W en régimen permanente (calor del NTC
caliente), aceptable a cambio de proteger el puente y duplicar la vida útil
de los condensadores.

### 10.3 MOV en el primario → **incluido**

Justificación específica para Venezuela: red eléctrica con transitorios
recurrentes (rayos, conmutación de cargas industriales, baja calidad del
suministro). Coste marginal: < 1 USD.

**Selección**: MOV de 14 mm rated **150 VAC** continuo para red 110 VAC:

- Modelo: **V150LA20A** (Littelfuse), **S14K150** (Epcos) o **14D151K**
  genérico.
- Energía absorbible: ~70 J — suficiente para transitorios de switching
  típicos, no para rayos directos.
- Posición: en paralelo con el primario, **después** del fusible (para que
  un MOV en cortocircuito haga saltar el fusible).
- Vida útil limitada por el número de eventos absorbidos: especificar en
  el manual de mantenimiento que se reemplace si se observa decoloración o
  apertura.

**Mejora opcional futura**: añadir un **GDT** (gas discharge tube) en
paralelo con el MOV para transitorios de mayor energía, o un módulo
SPD (surge protective device) externo. Fuera de alcance de la reproducción
original.

### 10.4 Interfaz del bus → **J2 analógico + J6 feed dedicado de +5 V** (issue #8, opción C)

El cruce esquemático ↔ BOM del issue #8 destapó que el riel de +5 V no salía
de la placa, y resolverlo obligaba a fijar la interfaz del bus de una vez.
Sobre la mesa estaban el header 2×5 con +5 V que pedía el BOM viejo (opción A),
el bus Eurorack de 16 pines (opción B, ya descartada a favor de un epic propio
en §3) y un conector aparte solo para +5 V (opción C). **Se eligió C**:

- **J2 queda como está** — `+12 / GND / GND / −12`, el mismo conector para los
  módulos 2-7. Ningún módulo recibe un +5 V vivo que no usa, y un bus de 4
  posiciones con llave no se puede enchufar corrido una fila (el clásico
  mata-módulos de los IDC 2×N sin llave).
- **J6 es el feed de +5 V**, 2 posiciones, solo hacia el módulo 2 (AD5686R +
  LCD, ~150 mA). Físicamente distinto de J2: imposible cruzarlo con ±12.
- **El retorno de J6 es la razón de fondo.** §10.1 ya exigía retorno dedicado
  del +5 V hasta el punto de estrella «separado del retorno analógico hasta el
  último cm», porque el backlight va conmutado por PWM: ~100 mA de flancos
  sobre unas decenas de mΩ de retorno compartido son milivoltios de rebote en
  la referencia del DAC — y a 1 V/octava, 1 mV ≈ 1.2 cents en el CV. Con un
  header único esa separación quedaba como convención de layout sobre pines
  GND compartidos; con conector propio la separación **es** el conector.
- La fidelidad a la tesis no favorecía al 2×5: la tesis no tenía bus formal
  (distribución con jumpers en daisy-chain, que ella misma reporta como
  problema — §7). El 2×5 era una invención del BOM viejo, no un dato original.

En la hoja, el retorno de J6 es la misma red `GND` que todo lo demás — la
separación es una regla de **layout**, no de netlist — y viaja anotada en el
propio plano al lado de J6, igual que la regla de PE de §13.

### Topología actualizada

```
   110 VAC                                12 VAC CT             ~17 VDC
   Red ──┤├──[MOV]──[NTC 5Ω]──► TR1 ──────────────► BRIDGE ──► C1 ─► 7812 ─► +12V/300mA
    60Hz F1 (500mA slow)            (split sec)     B1       4700µF │
                                                                    │
                                                                    │
                                                                    ├─► (─V) ─► 7912 ─► −12V/300mA
                                                                    │   C2
                                                                    │   4700µF
                                                                    │
                                                                    └─► (+V) ─► 7805 ─► +5V/150mA
                                                                                       (LCD + DAC)
```

## 11. Hitos siguientes

1. Resolver preguntas §10 (puedes responderlas en el PR que abre esta nota).
2. Capturar esquemático en KiCad → `hardware/01-power-supply/kicad/`.
3. Rutear PCB (bus board + fuente en una sola placa, o dos placas separadas).
4. Pedir fabricación.
5. Ejecutar checklist §9 y documentar en `bring-up.md`.
6. Cerrar los checkboxes correspondientes del epic #2.

## 12. Variante Europa (230 VAC / 50 Hz)

El §10 de arriba documenta las decisiones **tal como se resolvieron
originalmente**, para la red eléctrica de Venezuela (110 VAC / 60 Hz) — se
deja intacto como referencia histórica de por qué se eligió cada componente.
Esta sección documenta el cambio de región: la variante que se está
construyendo ahora asume **mains europeo, 230 VAC nominal / 50 Hz**
(estándar IEC 60038, vigente desde la armonización 1983-2003; "220 V" es el
nombre coloquial preexistente en varios países, sigue siendo la misma red).

**Lo que cambia:**

- **RV1 (MOV)**: el `V150LA20A` del §10.3 (150 V nominal, pensado para
  ~110-120 VAC) **no sirve en 230 V** — conduciría de forma continua y
  fallaría, porque su tensión de operación está muy por debajo del pico de
  230 VAC (≈325 V). Reemplazo: **S20K275** (Epcos/TDK) o equivalente
  `V275LA20A` (Littelfuse) / `14D271K`, rated **275 VAC continuo**, con
  margen sobre los 253 V del +10 % de tolerancia de la red europea.
- **F1 (fusible)**: mismo transformador (12 VAC CT / 2 A ≈ 24 VA), pero la
  corriente de primario cae a la mitad al doblar la tensión de línea
  (≈ 24 VA / 230 V ≈ 104 mA, contra ≈ 218 mA a 110 V). Bajado de 500 mA a
  **250 mA lento**, manteniendo el mismo margen (~2.4×) sobre la corriente
  nominal que tenía el original.
- **TR1 (transformador, externo)**: el secundario no cambia (12 VAC CT / 2 A),
  pero el **primario debe pedirse para 230 VAC / 50 Hz**, no 110 VAC / 60 Hz —
  es una pieza distinta a comprar, no una que se pueda usar indistintamente.
  50 Hz (vs. 60 Hz) generalmente exige más vueltas o más núcleo para el mismo
  flujo; queda del lado del fabricante del transformador, no de esta hoja.

**Lo que NO cambia:**

- **NT1 (NTC)**: el `SL10 5R020` del §10.2 se mantiene igual. Verificado
  contra el datasheet real (Vishay/Ametherm, documento 24503,
  `vishay.com/docs/24503/sl10.pdf`): **toda la familia SL10** (2R005 a
  10003, todos los valores de resistencia) está rated **265 VAC máximo**,
  con margen sobre los 253 V del peor caso europeo. No es una suposición por
  familia de producto — está en la tabla de datos rápidos del fabricante.
- Todo lo demás (reguladores, filtrado, protecciones DC, riel +5 V) es
  independiente de la tensión de red: cuelga del lado DC, después del
  puente rectificador.

**Tierra de protección**: al cambiar de región esto pasó de conveniente a
exigible — un equipo Clase I con marcado CE necesita PE por norma. Se resolvió
en **§13**: `J3` ya tiene su tercer pin y el chasis se une a GND en un punto
único. El esquema de puesta a tierra estaba sin decidir, y era eso lo que
bloqueaba dibujar el pin, no el pin en sí.

### Topología actualizada (Europa)

```
   230 VAC                                12 VAC CT             ~17 VDC
   Red ──┤├──[S20K275]──[NTC 5Ω]──► TR1 ──────────────► BRIDGE ──► C1 ─► 7812 ─► +12V/300mA
    50Hz F1 (250mA slow)                (split sec)     B1       4700µF │
                                                                        │
                                                                        │
                                                                        ├─► (─V) ─► 7912 ─► −12V/300mA
                                                                        │   C2
                                                                        │   4700µF
                                                                        │
                                                                        └─► (+V) ─► 7805 ─► +5V/150mA
                                                                                           (LCD + DAC)
```

## 13. Tierra de protección (PE) y puente de chasis

Cierra lo que §7 dejó a medias («retorno de la masa del chasis, sólo si se
quiere blindar EMI; con cuidado ante ground loops») y el pendiente que
arrastraba §12.

### 13.1 Por qué el puente es duro y no una red de *lift*

En audio hay una solución de compromiso muy conocida para la unión chasis ↔ 0 V:
una red de *ground lift* — resistencia de 10-100 Ω en paralelo con un
condensador de clase Y y un par de diodos en antiparalelo — que rompe el bucle
de tierra a frecuencias de audio pero cortocircuita ante una falla. **Aquí no
sirve**, y el motivo es mecánico, no eléctrico:

- Los paneles son **lámina galvanizada de 0.5 mm**
  ([`docs/modules/08-case-panels.md`](../../../docs/modules/08-case-panels.md)):
  metal, no aislante.
- El instrumento lleva **~40 jacks de 3.5 mm** montados a través de esos paneles
  ([`docs/architecture.md`](../../../docs/architecture.md)). El casquillo de un
  jack estándar es metálico y va a GND.

Chasis y GND ya están unidos en ~40 puntos antes de que la fuente opine nada.
Una red de lift quedaría cortocircuitada 40 veces y el esquemático estaría
documentando un aislamiento que no existe. Así que **se une duro, en un punto
definido, y se dice dónde**.

Esta decisión se apoya en una sola premisa: jacks de casquillo metálico. Si
alguna vez se pasa a jacks aislados de plástico, el chasis queda flotando
respecto a GND y hay que rehacer este apartado desde cero.

### 13.2 Qué se dibuja y qué no

| Elemento | Dónde | Qué hace |
|----------|-------|----------|
| `J3` pin 3 | Bornero de entrada AC, 3 posiciones | Recibe el PE del cable de red |
| Símbolo `Earth_Protective` | Colgando de `J3.3` | Declara la red **PE** y ahí se acaba: no sigue hacia la placa |
| `J5` | Faston 6.3 mm sobre la red GND | Sube el 0 V del circuito al mismo espárrago |

En el netlist salen **dos redes distintas**, `PE` y `GND`, y eso es correcto:
se tocan en el metal, fuera de la PCB.

```
   PE del cable de red ──[J3.3]──┐
                                 │
                                 ├──► ESPÁRRAGO M4 DEDICADO ──► un cable por panel
                                 │    (único punto de unión         (§13.3, punto 6)
   0 V del circuito ────[J5]─────┘     PE ↔ GND del instrumento)

   Fuera de la placa. En la PCB no hay ni una pista de PE.
```

**El PE no lleva pista de cobre.** No es un detalle de estilo. Ante un vivo
tocando el chasis, la corriente de falla la corta el magnetotérmico de la
instalación — 16 A típicos en Europa — y una pista de 0.5 mm no sobrevive el
tiempo que tarda en disparar. El camino de seguridad va por cable y por herraje,
nunca por la placa.

### 13.3 Reglas de montaje

1. **Un espárrago M4 dedicado**, soldado o remachado al chasis, con tuerca +
   contratuerca y arandela dentada. Lo usan **solo** dos cosas: el terminal de
   anillo del PE del cable de red y el del puente de `J5`. Ningún otro tornillo
   comparte ese espárrago, y ese espárrago no sujeta nada más.
2. **Sección del PE ≥ la de L y N** (1.0 mm² con este consumo).
3. **El PE del cable de red se corta más largo que L y N**, para que sea el
   último conductor en soltarse si alguien tira del cable.
4. **Verde/amarillo solo para tierra de protección.** No usar esa combinación
   para ninguna otra cosa dentro del cajón.
5. **Rascar la galvanización** bajo cada terminal de anillo hasta ver metal, y
   proteger después. El zinc conduce, pero el óxido de zinc no.
6. **Cada panel se bonda por su cuenta** al mismo espárrago, con su propio cable
   verde/amarillo y su tornillo. El cajón es de madera: los paneles **no** están
   unidos entre sí por la estructura, y los casquillos de los jacks no cuentan
   como unión de seguridad aunque eléctricamente lo estén. Esto es un requisito
   que este módulo le impone a [`case/`](../../../case), no algo que se resuelva
   en la PCB.

### 13.4 Marco normativo y comprobación

La norma aplicable a un equipo de audio de red en Europa es **IEC/EN 62368-1**,
que sustituyó a IEC 60065 (audio/vídeo) y a IEC 60950-1 (informática); la
Comisión Europea fijó el **20 de diciembre de 2020** como fecha de sustitución
para marcado CE. El requisito que aplica aquí es su cláusula **5.6.6,
*Resistance of the protective bonding system***.

El valor límite concreto de esa cláusula **no se ha verificado** contra el texto
de la norma (es de pago y no aparece en fuentes públicas), así que no se
reproduce aquí ningún número presentándolo como normativo. Para bring-up basta
un criterio de banco:

> Con el equipo **desenchufado**, medir con un óhmetro entre la clavija de
> tierra del enchufe y cualquier parte metálica accesible — cada panel, el
> espárrago, el faston de `J5`. Debe dar **unidades de miliohmio**, del orden de
> la resistencia de las propias puntas. Cualquier lectura que se despegue de eso
> es un bonding malo, no una tolerancia.

Si alguna vez se persigue marcado CE de verdad, hay que leer 5.6.6 y hacer el
ensayo con la corriente y el tiempo que indique, no con un óhmetro.

## 14. Placa: decisiones de diseño

### 14.1 Dos placas, no una

El §11 dejaba abierto si la fuente y el *bus board* iban juntos. Van **separados**:

- La fuente es compacta y vive junto al transformador; el bus board es largo y
  estrecho porque tiene que llegar a los módulos 2-7 a lo ancho del cajón. Son
  formas distintas.
- El formato del cajón sigue sin decidirse (`case/README.md`). Con una sola
  placa, la fuente no se podría fabricar hasta cerrar esa decisión. Separadas,
  la fuente se manda a fabricar ya.
- Una placa que cruza el cajón entero es el peor sitio posible para meter la
  red de 230 V.

### 14.2 Separación de la sección de red

Aislamiento **reforzado**: ≥6 mm de línea de fuga y ≥4 mm al aire entre el
primario (`J3 F1 RV1 NT1 J4`) y todo lo demás, con **ranura fresada** en la
barrera.

Lo hace fácil una propiedad del diseño: `TR1` es externo (sale por `J4`, vuelve
por `J1`), así que primario y secundario son **dos islas sin ningún componente
que las puentee**. La barrera puede ser física porque no hay nada que cruzarla.
La ranura no cuesta extra en fabricación.

El portafusible es **cerrado** (tipo Schurter FPG4, IEC 60335-1, 250 VAC/10 A
VDE) y no de clips abiertos. Clips con 230 V a la intemperie dentro de un cajón
de madera no pegan con haber elegido aislamiento reforzado.

### 14.3 Huellas propias

KiCad 10 no trae tres de las piezas, así que van en `kicad/sam17.pretty`:

| Huella | Por qué |
|---|---|
| `RV_Disc_D21mm_W5.5mm_P10.0mm` | `Varistor.pretty` llega a D12; el S20K275 es un disco de 20 mm |
| `NTC_Disc_D11.5mm_W4.5mm_P7.5mm` | No hay librería de termistores THT |
| `Faston_6.3x0.8mm_PCB_2Leg_P5.0mm` | No hay ningún faston de PCB |

El faston lleva **las dos patillas numeradas como el mismo pad 1**. El símbolo
`Conn_01x01_Pin` de `J5` tiene un solo pin, pero esto conduce corriente de falla
(§13) y necesita las dos patillas por resistencia mecánica y sección de cobre.
Es el mismo truco que usa el portafusible de la librería de KiCad.

### 14.4 Geometría de la placa

**100 × 150 mm, dos capas.** El ancho se queda en 100 mm porque es el borde del
tier barato de fabricación; el alto salió de la colocación, no al revés.

```
        x=0        30                              100
   y=0  ┌──────────╥──────────────────────────────┐
        │ H1       ║  J1      BR1              H2 │
        │ J3 ──────╢                              │
        │ F1       ║  C1        C2                │   bulk + estrella
        │          ║      D1                      │
        │ RV1      ║  C3   C7        ┌────────┐   │   ┐
        │  (22 mm) ║    C5           │ U1 +HS │   │   │ +12 V
        │          ║  R1   D3        └────────┘   │   ┘
        │ NT1      ║      D5                      │
        │          ║  C9   C11       ┌────────┐   │   ┐
        │          ║    C10          │ U3 +HS │   │   │ +5 V
        │ J4 ──────╢  R3   D6        └────────┘   │   ┘
        │          ║      D2                      │
        │          ║  C4   C8        ┌────────┐   │   ┐
        │          ║    C6           │ U2 +HS │   │   │ −12 V
        │ H3       ║  R2   D4        └────────┘ H4│   ┘
  y=150 └──────────╨───── J5   J2   J6 ───────────┘
                   ↑
              ranura fresada (y de 12 a 138)
```

Notas de la colocación, todas medidas y no estimadas:

- **La barrera está en x = 30, no en 25.** El cuerpo del `RV1` mide 22 mm y en
  una franja de 21 mm se montaba encima de la ranura. Sus *pads* cumplían la
  distancia; el problema era el encapsulado. Lo vio el render, no la medida.
- **La ranura no llega a los bordes** (va de y=12 a y=138). Si llegara, la placa
  se partiría en dos. Los puentes que quedan son lo que sujeta la franja de red,
  y por eso `H1`/`H3` van justo ahí.
- **Separación real medida: 12.4 mm** entre `J3.2` (neutro) y `H1` — el doble
  del mínimo de 6 mm. El taladro de fijación cuenta como SELV a propósito: un
  separador metálico está a potencial de chasis.
- **Los disipadores no están en la huella.** `TO-220-3_Vertical` mide 10.6 × 5.0
  y no sabe nada del disipador atornillado, así que se reservan 25 × 25 mm por
  regulador, dibujados en F.Fab para que quien monte la placa los vea.

`build_pcb.py` lo comprueba todo antes de guardar y aborta: piezas fuera del
margen, piezas solapadas, piezas montadas sobre la ranura, pads sin red, y la
separación red↔SELV. DRC de KiCad: **0 infracciones**.

### 14.5 Ruteo

Dos capas. **F** lleva los carriles y todo el lado de red; **B** lleva el árbol
de masa y los tres bajantes hacia los conectores. Una sola vía en toda la placa.

**No hay plano de masa, y es a propósito.** Un *pour* une todo con todo por el
camino más corto — justo lo contrario de la estrella de §7 y del retorno
dedicado de §10.1. Aquí GND es un árbol: sale del punto de estrella (`C1.2`, en
el bulk del riel positivo), cada rama muere en su grupo funcional, y no hay ni
un bucle. Eso último **no se puede ver mirando el dibujo** — un bucle de masa se
ve igual que una rama — así que `build_pcb.py` lo comprueba con union-find sobre
los extremos de los tramos y aborta si encuentra uno.

El **retorno dedicado del +5 V** (`J6.2`) sube por el canto derecho, la única
columna libre de ramas, y entra a la estrella por su propia vía. No toca ninguna
otra rama en todo su recorrido, que es lo que §10.1 pide.

Detalles que costaron una vuelta cada uno:

- **Los tres reguladores tienen la salida en el mismo `x`** (89.1), así que un
  bajante vertical corta a los otros dos. Se reparten tres columnas (90/93/97) y
  el que termina más a la izquierda gira más arriba, para que ninguna horizontal
  corte una vertical viva.
- **Los tres LED estaban girados al revés**: el ánodo caía al lado opuesto de su
  resistencia, así que la pista tenía que atravesar el pad del cátodo. Girados
  180°.
- **La espina de masa pasaba por encima de `D5.1` y `D2.1`.** Iba por `x=52.5`
  y esos pads están en `x=52`. Movida a `x=56`, por el pasillo de 2.1 mm que
  queda entre los pads de las resistencias (54.2) y los de los cerámicos (58).
- **`RED_230V` se bajó de 2.5 a 2.0 mm de separación.** No por relajar el
  diseño: es que el propio paso de 5 mm de los borneros deja 2.2 mm entre pad y
  pad, y la regla era más estricta que la pieza. Entre *pistas* de red la
  separación real sigue siendo ≥ 2.5 mm por trazado.

`build_pcb.py` aborta si encuentra cruces entre pistas, pistas sobre pads
ajenos, bucles de masa, piezas solapadas o sobre la ranura, o barrera por debajo
de 6 mm. **DRC de KiCad: 0 infracciones y 0 pads sin conectar.**

### 14.6 Antes de fabricar: verificar el orden de patillas de BR1

**Esto es una puerta, no una nota.** El nombre del símbolo de un puente en KiCad
codifica el **orden físico** de sus patillas, y por eso la librería trae cinco
variantes: `D_Bridge_+-AA`, `+A-A`, `+AA-`, `-A+A`, `-AA+`. El esquemático usa
`+-AA` (pin1 = +, pin2 = −, pin3 = ~, pin4 = ~), que se eligió sin atarlo a una
pieza concreta.

Al buscarlo, las fuentes secundarias se contradicen entre ellas sobre el orden
real del DF06M/KBP206 — así que **aquí no se afirma cuál es**. Lo que hay que
hacer, con el datasheet del puente que se compre delante:

1. Leer el orden de patillas real del encapsulado.
2. Si no es `+ − ~ ~`, cambiar el símbolo de `BR1` en `build_schematic.py` por la
   variante que corresponda y regenerar.
3. Volver a rutear las cuatro pistas de `BR1` (solo esas: la geometría DIP-4 es
   la misma en los cuatro casos, lo que cambia es qué pad cae en qué red).

Un puente cruzado pone el bulk en cortocircuito a través de dos diodos en el
primer semiciclo. Se lleva el puente, y probablemente el fusible no llega a
tiempo de salvar los condensadores.

**RESUELTO (2026-08-15, issue #11).** La pieza queda fijada: **DB207** (2 A /
1000 V, case DB-1; DB206 vale igual) — el único puente de 2 A que existe en
DIP-4 W7.62/P5.08. La duda de variantes era doblemente teórica: el KBP206 que
nombraba el BOM **no encaja en la huella** — su case KBP es SIP de 4 patas en
línea, paso ~3.8 mm (datasheet primario de Diodes Inc, DS21205 Rev. 12,
jul 2025).

El orden de patillas, de dos fuentes primarias independientes que coinciden:

- **HY Electronic**, `DB201 THRU DB207` Rev. 11 (hygroup.com.tw, el fabricante
  que vende RS con la ref. 923-5485): vista superior, fila superior `− +`
  (① −, ② +), fila inferior `~ ~` (③ ④).
- **Taiwan Semiconductor**, serie HDBL101G — case DBL, mismo layout, y es el
  datasheet que referencia la propia huella de KiCad: igual, `− +` arriba,
  `~ ~` abajo.

Montado girado 90° sobre la huella, eso cae `+` en pad 1 (`VRAW+`), `−` en
pad 2 (`VRAW−`) y `~ ~` en pads 3/4 (`SEC_A`/`SEC_B`): exactamente lo que
codifica el símbolo `D_Bridge_+-AA` ya elegido y lo que está ruteado. **No hubo
que tocar ni el símbolo ni las pistas** — solo el valor del BOM y esta nota.

El riesgo restante es insertar el cuerpo girado 180° (encaja físicamente y
cruza el puente): el silk de la huella trae una cruz `+` junto al pad 1 y el
cuerpo trae la polaridad moldeada, así que la inspección visual del checklist
(§9 paso 2) lo cubre. Si se compra la serie DB20x de otro fabricante
(Rectron/MCC), re-verificar su datasheet antes de soldar: la coincidencia
HY↔TSC hace muy improbable una variante divergente, pero gratis no es.

Reichelt no tiene ningún puente de 2 A en DIP-4 — por eso BR1 cambia de
proveedor (RS o TME).

### 14.7 Un error del BOM que salió al asignar huellas

`C1`/`C2` (4700 µF/25 V) pedían footprint `Radial-D10`. No existe: un
electrolítico de 10 mm de diámetro a 25 V ronda los 470 µF, un orden de magnitud
por debajo. El real es **D16 con paso de 7.5 mm**, y ocupa el cuádruple de área
— lo que cambia el presupuesto de la placa, no solo la línea de compra.

## 15. Simulación: el margen de dropout

Simulado en [`simulations/power/`](../../../simulations/power). Es la única
cuenta del módulo que no se cierra a mano: con filtro de entrada capacitiva la
corriente por el secundario circula en picos estrechos de 2-3 veces la continua,
así que la caída en la resistencia del devanado es mucho peor que corriente
media × resistencia.

### 15.1 El resultado

A red nominal el diseño va sobrado (+1.6 a +2.5 V de margen). **A 207 V — la red
al −10 %, que está dentro de la tolerancia europea — y a plena carga de diseño,
hace falta un transformador con regulación ≥ 10.7 %.** Por debajo de eso el 7812
sale de regulación en los valles del rizado.

Con la carga **real** de §2 (~80 mA analógicos por riel en vez de los 300 de
objetivo) pasa incluso con un transformador malo: +0.54 V. Es decir, **el caso
que falla es el objetivo de diseño, no el instrumento tal como lo describe la
tesis.**

### 15.2 Tres cosas que salieron y no eran obvias

- **Subir el bulk casi no sirve.** De 4700 a 10000 µF se ganan 0.22 V. Lo que
  limita no es el rizado sino el nivel medio: más capacidad estrecha el ángulo
  de conducción, sube el pico de corriente y empeora la caída en el devanado.
  Casi todo lo que ganas por un lado lo pierdes por el otro.
- **Un secundario de 15-0-15 arregla el dropout y rompe el térmico.** Da +3.7 V
  de margen, pero la unión del 7812 se va a 104-113 °C con el disipador de
  20 °C/W de §6, contra los < 70 °C que esa misma sección fija. Descartado.
- **Los dos rieles no van igual de cargados.** VRAW+ mueve 450 mA (7812 + 7805)
  y VRAW− solo 300, así que el negativo tiene ~0.5 V más de margen. El que hay
  que vigilar es el positivo.

### 15.3 Lo que sale holgado

- **El rizado de salida nunca fue el riesgo.** Con ~0.7 Vpp de entrada y 60-70 dB
  de rechazo del 7812 salen ~0.2-0.7 mV, dos órdenes de magnitud por debajo del
  objetivo de < 10 mVpp de §9.
- **Rizado en C1: 0.72-0.88 A RMS.** Entra en un 4700 µF/25 V normal (1.4-2 A),
  pero es un dato a mirar al comprar. Anotado en el BOM.

### 15.4 Lo que cambió en el BOM

`12VAC 2A CT` se lee de dos maneras y solo una funciona: **son 12-0-12, 24 V
totales**. Muchos vendedores llaman «12V CT» a un 6-0-6, y con ese cada riel
daría ~7.6 V — el 7812 no regularía jamás. La línea de `TR1` ahora lo dice, y
además pide la tensión de secundario **en vacío** (≥ 13.3 V por semidevanado),
que es el dato del que depende todo esto y que no estaba pedido.

## 16. Subir a 650 mA/riel: piezas verificadas

Objetivo: **650 mA por riel**, la corriente de la Doepfer A-100NT12 (su
generación lineal), con mejor ruido que la PSU3 actual, que es conmutada.

Todo lo de abajo está verificado contra datasheet primario o simulado. Lo que no
se pudo verificar está en §17, y **no se usó como hecho aquí**.

### 16.1 La corrección que casi se cuela

El dropout no es el criterio. **El LM2940-12 especifica `VIN ≥ 13,6 V`
garantizado** sobre temperatura (TI SNVS769J), que no es lo mismo que
`12 V + dropout = 13,0 V`. Diseñar contra 13,0 daba un margen que no existía:
13,5 y 13,6 parecen el mismo número y no lo son.

Y lo que manda no es el promedio sino **el valle del rizado de 100 Hz** con la
red a 207 V y a plena carga.

### 16.2 Por qué LDO y no más tensión

| Opción | Trafo | VRAW+ @207 V | P en el regulador | |
|---|---|---|---|---|
| 78xx tal cual | 48 VA | 13.00 V | 3.37 W | no llega |
| 15-0-15 + 78xx | 60 VA | 16.66 V | **6.34 W** | llega, disipador de 4 °C/W |
| **12-0-12 + LDO** | 120 VA | **14.12 V** | **3.76 W** | **elegida** |

Subir el secundario **casi duplica el calor** y obliga a disipadores mucho
mayores. Bajar el dropout hace lo contrario. El camino no es más tensión, es
menos caída.

### 16.3 Los reguladores: los dos son sustitución directa

| Ref | Pieza | Pinout | ¿Cambia algo? |
|---|---|---|---|
| `U1` | **LM2940CT-12/NOPB** | 1=IN, 2=GND, 3=OUT | Idéntico al 7812. Tab a **GND** |
| `U2` | **LM2990T-12/NOPB** | 1=GND, 2=IN, 3=OUT | Idéntico al 7912. Tab a **IN** |
| `U3` | 7805, se queda | — | Headroom le sobra |

Confirmado contra TI SNVS769J y SNVS093G, cada uno con una segunda fuente
independiente. **El LM2991 queda descartado**: es TO-220-5, exige divisor, carga
mínima de 500 µA y su pin ON/OFF no se puede dejar al aire — todo eso a cambio
de nada existiendo el LM2990-12.

**Comprobación antes de soldar el `U2`**, con la pieza en la mano: continuidad
entre el tab y la pata central = corto; entre el tab y la pata del punto de
pin 1 = abierto. Si sale al revés, no es un LM2990T.

### 16.4 El transformador: gana el que peor regula

Simulado con la tensión en vacío **publicada** de cada Talema 2×12 V:

| Modelo | Vacío | R devanado | Valle @207 V | Margen |
|---|---|---|---|---|
| 50 VA | 13.6 V | 0.77 Ω | 13.04 V | **−0.56 V** |
| 80 VA | 13.8 V | 0.54 Ω | 13.85 V | +0.25 V |
| **120 VA** | 13.4 V | **0.28 Ω** | **14.12 V** | **+0.52 V** |

**El de 120 VA gana teniendo menos tensión en vacío.** Con filtro capacitivo la
corriente circula en picos de 2-3× la continua, así que manda la resistencia del
devanado, no la tensión nominal. Queda además al 34 % de su capacidad, así que
va frío.

Talema es el único de los fabricantes mirados que **publica la tensión en
vacío**, que es exactamente el dato que decide esto. Sin él no se puede calcular
el valle. Si se compra otro, **hay que medir el vacío con el multímetro antes de
dar el diseño por bueno**.

### 16.5 El bulk sube a 9400 µF por riel

Simulado con el Talema de 120 VA a 207 V y plena carga:

| Bulk/riel | Valle | Margen sobre 13.6 V |
|---|---|---|
| 4700 µF | 13.66 V | +0.06 V |
| **9400 µF (2 × 4700)** | **14.12 V** | **+0.52 V** |
| 14100 µF | 14.30 V | +0.70 V |

Dos de 4700 µF/25 V en paralelo salen más baratos y más bajos que buscar un
10000 µF, y reparten la corriente de rizado. Del tercero en adelante hay
rendimientos decrecientes.

**Tensión de los condensadores**: el pico máximo simulado con red a +10 % y casi
en vacío es **20.54 V**, o sea el **82 %** de un condensador de 25 V. Pasa, pero
justo. Los pequeños del riel negativo van a **35 V**, que cuestan céntimos.

### 16.6 Los condensadores dejan de ser filtrado y pasan a ser estabilidad

Es el cambio conceptual del respin. Un 78xx es estable con casi cualquier cosa;
un LDO **oscila fuera de su ventana de ESR**.

| Nodo | Valor | Requisito duro |
|---|---|---|
| Entrada `U1` | 0.47 µF | Valor de la Table 1 del datasheet, no 0.1 µF |
| **Salida `U1`** | **100 µF/25 V aluminio estándar** | ≥22 µF **y ESR entre 100 mΩ y 1 Ω** |
| Entrada `U2` | 10 µF/35 V aluminio | ≥10 µF |
| Salida `U2` | 100 µF/35 V aluminio | ≥10 µF, ESR < 10 Ω |

Reglas que no se negocian:

1. **Nunca un cerámico X7R solo a la salida del LM2940.** Un MLCC tiene 2-20 mΩ,
   entre 5 y 50 veces por debajo del piso de 100 mΩ. TI lo dice literal:
   *oscillations can result*.
2. **No pongas un MLCC gordo en paralelo con el electrolítico**: la ESR
   resultante es el paralelo de las dos, y se va por debajo del piso.
3. **Los 100 nF de desacoplo se mudan al conector de salida**, no al pin del
   regulador. Así el riel sigue desacoplado en alta frecuencia sin comerse el
   margen de fase del LDO.
4. **`C8` (0.1 µF a la salida de `U2`) no se puebla.** Se deja la huella. Si al
   medir hace falta, se pone con **1 Ω en serie**.

### 16.7 Disipación: el más caliente es el negativo

**Fischer SK 129/38,1 220, 6.5 K/W**, uno por regulador. Reserva **42 × 38.1 mm**
y 25 mm de alto. Fischer mide en montaje vertical: **acostado son 7.7 K/W**, y
ese es el número que vale.

| Regulador | Tab a | Montaje | Tj a 45 °C ambiente |
|---|---|---|---|
| `U1` LM2940 | GND | directo, solo grasa | ~89 °C |
| **`U2` LM2990** | **IN (hasta −20 V)** | **mica + casquillo aislante** | **~101 °C** |
| `U3` 7805 | GND | directo | ~91 °C |

**`U2` es el componente más caliente de la placa**, no `U1`, porque paga el
aislante. Y no hay escapatoria: 7912, LM337, LM2990 y LM2991 tienen los cuatro el
tab a Vin. Tampoco puede compartir disipador desnudo con `U1` o `U3` — tab de
`U2` (VRAW−) contra tab de `U1` (GND) es un corto franco al encender.

### 16.8 Sobretensión: sí en +12 V, no en −12 V

Contra los absolute maximum leídos uno a uno:

| Chip | Abs max | Con VRAW+ a 20.54 V | |
|---|---|---|---|
| TL074 | 42 V (TI) | 32.5 V | sobrevive holgado |
| LM13700 | 36 V / ±18 V | 32.5 V | no se destruye |
| **AS3340** | **VCC−GND: +18 V** | **20.54 V** | **se muere** |

El pico de 20.54 V está **simulado**, y supera el abs max del 3340. Si `U1` falla
en corto, el bus ve VRAW+ y se lleva los tres VCO por delante. **Crowbar en el
riel de +12 V**, cuatro componentes y ~1,50 €:

```
+12V ──┬── ánodo BT169D ── cátodo a GND
       └── BZX55C15 ── gate ──┬── 1 kΩ ── GND
                              └── 100 nF ── GND
```

Umbral peor caso 14.6-16.4 V: cabe entre los 12.60 V del riel sano y los 18 V del
3340. **Quien abre el circuito es `F1`, el fusible de primario que ya existe** —
el crowbar cortocircuita VRAW+ a través del regulador ya muerto. **No metas un
fusible en serie en VRAW+ ni en el riel**: te comes otra vez el margen que tanto
costó recuperar.

El riel de −12 V **no lleva crowbar**: el 3340 alimenta su VEE por un zener
interno y a −18 V la corriente sube a 18.4 mA, por debajo de su límite de 40 mA.
Se desafina por autocalentamiento, no se destruye.

### 16.9 Polyfuse: no en esta placa

La razón honesta es que **se come el margen de dropout**. Un MF-R090 cae 0.20 V
nuevo y 0.31 V después de un ciclo de disparo, y en el valle del rizado —que es
donde se decide el dropout— la caída instantánea es 2-3 veces peor. Convierte un
diseño que raspa en uno que no regula.

Y uno por riel **no da lo que se busca**: mata todos los módulos por igual y no
dice cuál falló. **Va uno pequeño por módulo en el bus board**, con un LED de
4.7 kΩ en paralelo que se enciende solo cuando ese fusible dispara. Eso señala el
conector culpable sin un solo componente activo.

Miedo desmontado, para que no vuelva: el polyfuse **no modula el riel a
frecuencias de audio**. Su constante de tiempo es térmica y vale segundos; entre
20 Hz y 20 kHz es una resistencia fija. Con el peor PSRR garantizado del TL074, un
salto de 20 mA sobre 0.27 Ω da 1.7 µV referidos a la entrada — dos órdenes de
magnitud por debajo de la propia Vos del chip.

### 16.10 Puntos de prueba: obligatorios

`TP1..TP6` en VRAW+, VRAW−, +12 V, −12 V, +5 V y GND. Cuestan cero y son la única
forma de cerrar este diseño: **el valle del rizado de VRAW es el número que decide
todo** y hay que engancharle una punta de osciloscopio sin cocodrilos volando.

### 16.11 KiCad: no hay que crear ningún símbolo

| Ref | Símbolo | Nota |
|---|---|---|
| `U1` | `Regulator_Linear:LM7812_TO220` **reutilizado** | El símbolo del LM2940 no existe, pero su pinout es idéntico. `Value = LM2940CT-12` |
| `U2` | `Regulator_Linear:LM2990SX-12` | Existe. El «SX» del nombre es del encapsulado SMD: pon `MPN = LM2990T-12/NOPB` bien visible o alguien pedirá el que no es |
| `TP1..6` | `Connector:TestPoint` | Existe |

### 16.12 El +5 V queda acotado a 300 mA

Si el 7805 colgara de la **salida** del +12 V, `U1` tendría que dar 650 + 300 =
950 mA por un LM2940 de 1 A. **Se queda colgado de VRAW+**, y el riel de +5 V se
acota a **300 mA como límite de diseño**, no como estimación. Con eso el
semidevanado positivo carga 950 mA, que es el número con el que está simulado
todo lo anterior.

Si algún día el +5 V pide más, esto se reabre: transformador aparte o conmutada
para ese riel. No se tapa con «seguro aguanta».

## 17. Lo que NO está confirmado del respin

Esta sección es la que sostiene la credibilidad de §16. Nada de aquí abajo se usó
como hecho allí arriba. Si algún día alguien tiene que decidir rápido, que empiece
leyendo esto.

### 17.1 El LDO cuesta rechazo de rizado, y eso es una regresión

**Es la única pega real de cambiar a LDO, y conviene no taparla.** El LM2990 usa
paso PNP, y su rechazo de fuente es **peor que el del 7912**:

| | Garantizado | Típico |
|---|---|---|
| LM2990-12 | **42 dB mín a 1 kHz, con IOUT = 5 mA** | ~66 dB a 100 Hz |
| 7912 | ~60 dB a 100 Hz | — |

Con 0.68 Vpp de rizado en la entrada (el que da el bulk de 9400 µF) y el peor
caso garantizado de 42 dB, salen **~5.4 mVpp** en el riel de −12 V. El objetivo
de §9 son < 10 mVpp, así que **pasa — pero por poco, y es ocho veces peor que con
el 7912**.

Dos atenuantes reales: no hay mínimo garantizado a 100 Hz (a esa frecuencia
suele ser mejor que a 1 kHz), y subir el bulk a 9400 µF ya redujo el rizado de
entrada a la mitad, lo que compensa parte de la pérdida.

**Hay que medirlo en la placa.** Y si sale mal, la salida está en el bus board,
no aquí: un RC o LC por riel a la entrada de cada módulo.

Dato adicional del mismo datasheet: la impedancia de salida del LM2990 pasa de
~2-3 mΩ a **~30 mΩ si el regulador trabaja cerca del dropout**. Un orden de
magnitud peor. Otra razón para no raspar el piso de VRAW.

### 17.2 Huecos de datasheet

1. **El dropout a 650 mA no existe como dato garantizado.** TI solo especifica a
   100 mA y a 1 A. Hay curvas típicas, pero típico no es garantizado. Todo §16
   usa el máximo a 1 A, que acota 650 mA de forma conservadora. **No interpoles y
   lo llames garantizado.**
2. **Contradicción dentro del datasheet del LM2990 sobre el VIN mínimo.** El
   §7.4.1 dice que la entrada debe estar entre VOUT−5 V y −26 V, que leído literal
   para la versión de −12 V exigiría |VIN| ≥ 17 V — y eso contradice frontalmente
   su propio dropout y su tabla eléctrica (|VIN| ≥ 13 V). **No se pudo resolver en
   fuente primaria.** Se usó el criterio conservador de 13 V. Si al medir el riel
   negativo se comporta raro cerca del piso, **esta es la primera sospechosa**.
3. **El límite inferior de ESR del LM2990 sale de una figura, no de texto**, y
   además cae justo en el borde del eje: por debajo simplemente no está
   caracterizado.
4. **RθJC del LM2990: no leído.** El presupuesto térmico de `U2` usa 5.0 K/W por
   analogía con el MC7900 de onsemi. Es conservador, pero es una analogía.

### 17.3 Números de parte: dos trampas de compra

5. **Contradicción sin resolver en el encapsulado del `LM2940T-12.0/NOPB`.** Una
   lectura del addendum de TI dice TO-220; otra dice que ese código es TO-263
   (SMD) y que el TO-220 es solo el `LM2940CT-12/NOPB`. **Por eso §16 especifica
   el CT**, que sí está confirmado como TO-220 de 3 patas en dos sitios.
6. **Reichelt vende el «LM2940 CT12» con fabricante FREI y enlaza dos datasheets
   distintos**: el LM2940 de National **y el TS2940 de Taiwan Semiconductor. Si
   llega un TS2940, su ventana de ESR puede no coincidir con la del de TI, y no
   está verificada.** Cómpralo en TME o Mouser DE como `LM2940CT-12/NOPB` si
   quieres silicio trazable.
7. **Stock y precio sin verificar** para casi todo: reichelt.de devuelve 503 y
   tme.eu 403 a consulta automatizada. Lo único confirmado leyendo la página del
   distribuidor: LM2990T-12 (5,20 €, stock), condensador RAD KY 4700/25 (0,99 €),
   disipador SK 129/38,1 (2,65 €).

### 17.4 Térmica: la mica es una estimación

8. **La resistencia térmica de la mica (1.0-1.4 K/W) es una estimación por
   escalado de área**, no un dato de datasheet. Lo único medido es la lámina sola
   (0.15 K/W por pulgada cuadrada), y la tabla de Fischer de la que sale está
   **declarada para encapsulado TO-3**, no TO-220.
9. Y un detalle que da que pensar: la página de producto de Fischer para esa mica
   tiene un párrafo **marcado «KI-generiert» (generado por IA)** que dice 0.4 K/W,
   **contradiciendo la tabla de datos de la propia página** (0.15 K/W por in²).
   Varios distribuidores repiten el 0.4. Aquí se usó la tabla.
10. **Los K/W de Fischer son típicos, no garantizados.** El propio fabricante
    advierte de que no existe norma internacional que fije cómo se mide la Rth de
    un disipador.

### 17.5 Los chips que hay que proteger

11. **El CEM3340 original de Curtis no tiene sitio de fabricante vivo que citar.**
    Los absolute maximum usados son del **AS3340 de ALFA RPAR**. Si el chip que
    compras es un **V3340 de Coolaudio, verifica sus abs max** antes de fijar el
    umbral del crowbar — su PDF devuelve 404.
12. **Inconsistencia dentro del propio datasheet del AS3340**: sus abs max dicen
    −6 V entre VEE y GND, pero el texto describe un zener interno de 7.4 V y las
    características se miden con ese zener. No afecta a la conclusión del riel
    positivo, pero ahí está.
13. **Abs max del AD5686R y del LCD no verificados.** La afirmación de que 16-17 V
    destruye lo que cuelga del +5 V se apoya en que ningún CMOS de 5 V tolera eso,
    **no en un datasheet leído**. Verifícalo antes de fijar un crowbar de +5 V.

### 17.6 Lo que sí se cerró en esta pasada

Para que quede claro qué dejó de ser incierto:

- **El valle de VRAW ya está simulado**, no estimado. Con el Talema de 120 VA y
  9400 µF/riel: **14.12 V a 207 V**, o sea +0.52 V sobre los 13.6 V. Y con
  4700 µF sale **13.66 V**, que es +0.06 V: por eso el bulk sube.
- **El pico máximo también**: 20.54 V con red a +10 % y casi en vacío. Eso es lo
  que **justifica el crowbar** (supera los 18 V del 3340) y lo que deja los
  condensadores de 25 V al 82 % de su tensión.

Aun así, las dos cifras salen de un modelo cuyo transformador es una fuente ideal
con una resistencia serie. **Mídelas con osciloscopio en el valle**, a plena carga
y en caliente, antes de dar el diseño por bueno.

## 18. Zumbido: qué radia de verdad, y dónde va el transformador

Frente abierto junto con el bus board. La pregunta de partida era "cómo oriento
el toroide y a qué distancia lo pongo". La respuesta empieza antes: **el
transformador casi nunca es lo que más radia en una fuente lineal.**

### 18.1 El emisor no es el núcleo, es el lazo de carga

Por el lazo transformador → puente → bulk no circula la corriente continua.
Circulan **picos estrechos de 2-3 veces la continua**, a 100 Hz, con flancos de
microsegundos (§16.4 ya lo usaba para elegir transformador). Y lo que se acopla
a un lazo vecino no va con *I*, va con **dI/dt**.

El acoplo entre dos lazos es un dipolo magnético:

```
V = (mu0 / 4pi) * (2 * Av / r^3) * A * dI/dt
```

donde `A` es el área del lazo emisor, `Av` la del lazo víctima y `r` la
distancia. Todo lo que se puede hacer está en esa fórmula: bajar `A`, bajar
`Av`, o subir `r`.

Elegir un toroide en vez de un EI baja el campo del **núcleo**, que es un
término distinto y que aquí resulta no ser el que manda.

### 18.2 Lo que sí se pudo medir: el lazo de la PCB

[`simulations/power/hum_loop.py`](../../../simulations/power/hum_loop.py) lo
mide **sobre la placa ya ruteada**, no sobre una intención:

| | |
|---|---|
| Caja envolvente de `J1`+`BR1`+`C1`+`C12` | 29.6 × 23.0 mm → **6.81 cm²** |
| Separación media VRAW+ ↔ retorno de masa | 5.0 mm |
| Inducido en un lazo víctima de 10 cm² a 150 mm | **5.0 µV** |
| Referencia: −100 dBu | 7.75 µV |

Pasa, con poco margen. El barrido completo:

| Distancia | Inducido |
|---|---|
| 50 mm | 136 µV |
| 100 mm | 17.0 µV |
| **150 mm** | **5.0 µV** |
| 200 mm | 2.1 µV |
| 300 mm | 0.6 µV |

El 1/r³ es brutal: **duplicar la distancia divide por ocho**. Alejar 5 cm más
vale más que cualquier apantallamiento.

Un aviso sobre este número, porque el primer intento estuvo mal: el script
calculaba el área como "largo de la ida × separación media" y daba 7.82 cm²,
**más que su propia caja envolvente de 6.81**, lo cual es imposible para un lazo
cerrado. Contaba los 157 mm enteros de VRAW+, incluidas las bajadas a los
reguladores y a `TP1`, que no forman parte del lazo de carga. Se quedó la caja
envolvente, que es una cota superior de verdad.

### 18.3 El que de verdad manda: el mazo del secundario

Aquí está el hallazgo del frente. El secundario son **tres hilos sueltos**
(12 V / CT / 12 V) desde el toroide hasta `J1`, y llevan exactamente la misma
corriente de pico que el lazo de la placa.

Con 200 mm de recorrido y los hilos separados 20 mm, el lazo son **40 cm²**.
Seis veces el de la PCB. A 150 mm eso son **~29 µV**: cuatro veces por encima
del suelo de −100 dBu, y haría falta irse a ~270 mm para bajar de ahí.

> **El cableado del secundario radia más que la placa y más que el núcleo.**
> Trenzarlo lo lleva a un área neta prácticamente nula, porque cada vuelta
> invierte el signo del área.

Reglas, por orden de lo que más vale:

1. **Los tres hilos del secundario, trenzados** desde el toroide hasta `J1`.
   Gratis y es la mejora más grande de toda esta sección.
2. **El par del primario, también trenzado** (`J4` → toroide). Menos corriente,
   pero está a 230 V y el mismo argumento aplica al acoplo capacitivo.
3. **Lo más cortos que se pueda.** El área crece con el largo.

### 18.4 Orientación del toroide

El campo residual de un toroide sale de que el devanado da una vuelta completa
alrededor del núcleo: se comporta como **una espira en el plano del toroide**,
con el momento dipolar **a lo largo de su eje** (el que atraviesa el agujero).

Para un dipolo `m` en el eje `z`:

| Posición de la víctima | Campo | Dirección |
|---|---|---|
| En el eje, a distancia `d` | `mu0*m / (2*pi*d^3)` | paralelo al eje |
| En el ecuador, a distancia `d` | `mu0*m / (4*pi*d^3)` | antiparalelo al eje |

El ecuador ya es **2× mejor** que el eje solo por magnitud. Pero lo que decide
es la *dirección*: el flujo que ve una PCB es la componente **perpendicular a
su plano**.

- Toroide con el eje **apuntando a las placas** → el campo llega perpendicular a
  ellas. Acoplo máximo. **Este es el caso malo.**
- Toroide con el eje **paralelo al plano de las placas**, con las placas hacia
  su ecuador → el campo en las placas queda contenido *en* su plano y el flujo
  es casi cero. **Este es el bueno.**

En el SAM17 sale gratis: los paneles son verticales y las PCB van montadas
detrás, o sea en planos verticales. **Un toroide atornillado plano al suelo del
cajón tiene el eje vertical, que es paralelo a esos planos.** El montaje
estándar ya es el correcto.

Lo que **no** hay que hacer: montarlo sobre un soporte vertical en la trasera
con el eje apuntando hacia adelante, hacia los módulos. Es el caso malo, y es
una forma perfectamente razonable de montar un transformador si nadie te dice
por qué no.

### 18.5 Dónde va todo en el cajón de 950 mm

- **Toroide**: en una punta, plano contra el suelo (eje vertical), a **≥ 200 mm**
  del módulo de audio más cercano. Con 1/r³, 200 mm en vez de 150 baja el
  acoplo un 58 %.
- **PCB de la fuente**: junto al toroide, para que el mazo del secundario sea
  corto. Lo que se aleja del audio es el conjunto, no cada pieza por separado.
- **VCO y VCF lo más lejos posible del toroide.** Son los que más duelen: un
  error en la referencia de tono no se enmascara, se oye como desafinación.
- **Bus board**: a lo largo del centro, detrás de los paneles, para que los
  cables de bajada bajen ≤ 150 mm (bus-board §4). Que quede lejos del toroide es
  gratis y conveniente: sus cables son el lazo víctima más grande del aparato.

### 18.6 Lo que NO está confirmado de esta sección

1. **`T_FLANCO = 20 µs`** es una estimación del flanco del pico de carga. Es el
   parámetro más flojo de todo §18 y el resultado es proporcional a él: con 5 µs
   los números se multiplican por cuatro y el margen a 150 mm desaparece. Se mide
   con una sonda de corriente en el secundario, o por la caída sobre una
   resistencia serie pequeña.
2. **El área del lazo víctima, 10 cm²**, es una suposición razonable para una
   placa de módulo. No se ha medido en ninguna de las placas 2-7 porque todavía
   no están ruteadas.
3. **El campo residual del toroide no entra en el cálculo.** No hay dato de
   momento dipolar en el datasheet del Talema — casi ningún fabricante lo
   publica. Lo de §18.4 es la *dirección* correcta de montaje, no una cifra.
4. **Nada de esto sustituye a medirlo.** El procedimiento: con el instrumento
   montado y sin señal, mirar el espectro de la salida y buscar la línea de
   100 Hz (rectificación) frente a la de 50 Hz (campo del núcleo). Cuál de las
   dos domine dice cuál de los dos mecanismos manda, y hasta entonces esto es
   una predicción.

## Referencias

- [Modular Synthesizer Power Supplies (Rabid Elephant)](https://rabidelephant.com/blogs/general/modular-synthesizer-power-supplies-and-distribution-a-thorough-introduction) — fundamento de grounding y distribución.
- [butchwarns/Eurorack_PSU](https://github.com/butchwarns/Eurorack_PSU) — referencia de diseño open source con fuses y >1 A por riel.
- [Shmoergh — Eurorack Power Supply](https://www.shmoergh.com/blog/eurorack-power-supply/) — implementación práctica.
- [TI LM78xx / LM79xx datasheet](https://www.ti.com/lit/ds/symlink/lm7800.pdf) — curvas de dropout y disipación.
- [TI LM13700 datasheet](https://www.ti.com/lit/ds/symlink/lm13700.pdf) — consumo 2.6 mA typ @ ±15 V.
- [Analog Devices AD5686R datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ad5686r_5685r_5684r.pdf) — VDD 2.7–5.5 V, decoupling 10 µF ∥ 0.1 µF obligatorio.
- [CEM3340 — Synth DIY Wiki](https://sdiy.info/wiki/CEM3340) — nota sobre el zener de 6.5 V en pin 3 con supply ±12 V.
- [Pi 3B+ power measurements (RasPi.TV)](https://raspi.tv/2018/how-much-power-does-raspberry-pi-3b-use-power-measurements) — confirmación del pico de 1.3 A.
- [Vishay/Ametherm SL10 datasheet](https://www.vishay.com/docs/24503/sl10.pdf) — tabla de datos rápidos: toda la familia SL10 rated 265 VAC máximo, independiente del valor de resistencia (§12).
- [IEC 60038](https://en.wikipedia.org/wiki/IEC_60038) — estándar de tensión nominal 230 V/50 Hz para Europa, vigente desde la armonización 1983-2003 (§12).
- [IEC 62368-1 sustituye a 60065 y 60950-1 (Eurofins/MET Labs)](https://metlabs.com/product-safety/faqs-iec-62368-1-replacing-iec-60950-1-iec-60065/) — norma vigente para equipos de audio de red y fecha de sustitución para marcado CE, 20-dic-2020 (§13.4).
- [IEC 62368-1 ed. 3.0, muestra pública (IEC/iTeh)](https://cdn.standards.iteh.ai/samples/23618/92449acef5b2481da95e6e59387999ad/IEC-62368-1-2018.pdf) — índice donde figura la cláusula 5.6.6 *Resistance of the protective bonding system*. El texto completo de la cláusula es de pago: el límite numérico **no** se reproduce en §13.4 por no haberse podido verificar.
- [Doepfer A-100 Technical Details](https://doepfer.de/a100_man/a100t_e.htm) — bus de 16 pines: juego de senales, franja roja = -12 V abajo, y la prohibicion expresa de headers con caja y codigo en un bus board (bus-board §9).
- [Doepfer A-100 DIY](https://doepfer.de/DIY/a100_diy.htm) — CV y Gate en los dos pares de arriba; los dos pines de cada par van unidos en la placa (bus-board §9).
- [Bel Fuse 0ZRE Series (radial PTC)](https://www.belfuse.com/media/datasheets/products/circuit-protection/ds-cp-0zre-series.pdf) — 0ZRE0025FF: 0.25 A hold, 0.56 A trip, 240 V, 1.3 ohm (bus-board §7).
- [Bourns MF-R Series](https://www.bourns.com/docs/product-datasheets/mf-r.pdf) — MF-R025 como alternativa: 0.25 A hold, 0.50 A trip, Rmin 1.00 / R1max 1.95 ohm (bus-board §7).
