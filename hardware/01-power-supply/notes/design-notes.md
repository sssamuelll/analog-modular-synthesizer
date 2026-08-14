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

**Conclusión**: los rieles analógicos ±12 V están holgados; el problema está en
+5 V **por el Raspberry Pi**. Mantener el enfoque de la tesis (fuente dedicada
para el Pi) es la decisión más limpia.

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

El regulador +5 V auxiliar casi no disipa (sólo alimenta DAC + LCD si se
decide unificar; si el Pi sigue independiente, se puede suprimir).

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
   los reguladores, cortos en el silkscreen.
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
