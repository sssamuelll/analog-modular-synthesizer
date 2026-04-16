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
  - Retorno de la masa del chasis (sólo si se quiere blindar EMI; con cuidado
    ante ground loops).
- Distribución por **bus board dedicado** (PCB con pin headers en paralelo),
  no daisy-chain soldado en cada módulo. La tesis reportó justo este problema
  con sus cables jumper.
- Trazas de potencia con sección suficiente para **< 20 mV de caída** entre
  el regulador y el módulo más lejano a 300 mA (estimación a validar durante
  el routing del bus board).
- Separar físicamente los retornos analógico y digital; unirlos **en el punto
  de estrella**, no en los módulos.

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

1. **Inspección visual**: polaridad de los electrolíticos, orientación de
   los reguladores, cortos en el silkscreen.
2. Conectar **sólo el transformador** (sin carga), verificar ±17 V tras el
   bridge.
3. Insertar reguladores en sus zócalos, verificar **+12 V ±1 %** y **−12 V
   ±1 %** en las salidas.
4. Conectar carga resistiva (100 Ω, ~120 mA) en cada riel, medir la caída
   de tensión (expectativa: < 50 mV).
5. Medir **rizado pico-pico** con osciloscopio (DC coupling, 1 MHz BW):
   objetivo **< 10 mVpp** a plena carga.
6. **Termograma o termopar** en los reguladores tras 15 min a plena carga
   (expectativa: < 70 °C en el cuerpo del TO-220).
7. Documentar en `hardware/01-power-supply/notes/bring-up.md`.

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

## Referencias

- [Modular Synthesizer Power Supplies (Rabid Elephant)](https://rabidelephant.com/blogs/general/modular-synthesizer-power-supplies-and-distribution-a-thorough-introduction) — fundamento de grounding y distribución.
- [butchwarns/Eurorack_PSU](https://github.com/butchwarns/Eurorack_PSU) — referencia de diseño open source con fuses y >1 A por riel.
- [Shmoergh — Eurorack Power Supply](https://www.shmoergh.com/blog/eurorack-power-supply/) — implementación práctica.
- [TI LM78xx / LM79xx datasheet](https://www.ti.com/lit/ds/symlink/lm7800.pdf) — curvas de dropout y disipación.
- [TI LM13700 datasheet](https://www.ti.com/lit/ds/symlink/lm13700.pdf) — consumo 2.6 mA typ @ ±15 V.
- [Analog Devices AD5686R datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ad5686r_5685r_5684r.pdf) — VDD 2.7–5.5 V, decoupling 10 µF ∥ 0.1 µF obligatorio.
- [CEM3340 — Synth DIY Wiki](https://sdiy.info/wiki/CEM3340) — nota sobre el zener de 6.5 V en pin 3 con supply ±12 V.
- [Pi 3B+ power measurements (RasPi.TV)](https://raspi.tv/2018/how-much-power-does-raspberry-pi-3b-use-power-measurements) — confirmación del pico de 1.3 A.
