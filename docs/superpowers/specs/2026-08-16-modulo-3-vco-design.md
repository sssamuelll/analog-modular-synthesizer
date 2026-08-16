# Módulo 3 «VCO ×4» — cuatro voces en una placa, con el DAC adentro

> Sustituye al módulo de 3 osciladores independientes de la tesis (Gráficos
> 25-26). Hereda y aplica las decisiones ya mergeadas: mandos fuera del audio
> (architecture-poly §7), DAC en el módulo (§8), patch bay normalizado (§6),
> camino de afinación digital (§5). Cierra el issue #34.

## 1. Objetivo

La placa que genera el sonido crudo de las 4 voces. Cuatro canales idénticos
CEM3340 con un solo juego de mandos (que ya no viven aquí: son sensores del
panel, §7). Todo lo que la placa necesita del cerebro le llega como números
por el enlace serie; todo lo que da al resto del sinte sale como audio por
voz, ya mezclado, más los cuatro pulsos de afinación.

**Objetivo medible**: calibración 1 V/oct dentro del rango de captura del DAC
(0-7 V) en las 4 voces tras ajustar trims, y de ahí el autoafinado sostiene el
suelo de 0.58 cents de `dac_local_budget.py`.

## 2. Decisiones fijadas (con Samuel, 2026-08-16)

1. **Mezcla de ondas por VCA con mando compartido.** 3 OTAs por voz; los 3 CV
   de nivel (sierra/tri/cuadrada) salen del DAC y entran en presets.
2. **Ni FM lineal ni hard sync.** La FM exponencial ya la da el jack CV-IN
   (suma al pitch); el sync no tiene pareja con un VCO por voz.
3. **Patch bay: 8 jacks.** CV-IN ×4 (suman, normalizados a 0 V por TN) y
   salida de mezcla ×4 (normalizadas al VCF). Las ondas crudas no se exponen:
   la mezcla da cualquier onda pura poniendo su CV a tope.
4. **Enlace serie (#34): híbrido.** CS por módulo entre placas; los chips de
   cada placa en cadena soldada (DCEN al arranque). SCLK/MOSI/MISO
   compartidos. Quitar un módulo solo mata su CS.
5. **Telemetría de serie en toda placa** (patrón para 5, 6, 7 y cerebro):
   sensor de temperatura I²C pegado al punto térmicamente crítico, EEPROM de
   identidad/calibración en el mismo I²C, y test points en los nodos clave.
   Sin voltímetro de rieles (los LED del bus board + test points los cubren).
6. **Trims y tempco se quedan** (decisión por defecto, razonada): trim de
   escala y de offset por voz llevan cada VCO al rango de captura — el VCO3
   de la tesis con −18.62 % pediría 8.5 V y se sale del DAC —; el R_TEMPCO
   baja la deriva cruda de ~5.7 cents/°C unas 30× y el autoafinado pule el
   resto.

## 3. Bloques

```
  enlace serie ──┐                              ┌── TUNE_OUT 1-4 (3.3 V)
  (SPI+CS3+I²C)  ▼                              │
        ┌─────────────────────┐           ┌─────┴────┐
        │ 2x AD5686RB cadena  │           │  74HC14  │
        │ ch1-4: PITCH        │           └─────▲────┘
        │ ch5: PWM  ch6-8: MIX│                 │ (onda cuadrada de cada voz)
        └──┬──────┬───────────┘                 │
   pitch×4 ▼      ▼ pwm, mix×3 (compartidos)    │
  ┌─────────────────────────────────────────────┴──┐
  │  POR VOZ (×4):                                 │
  │  CV: amp ×2.8 (TL074H) → sumador ← jack CV-IN  │
  │      → trims escala/offset → CEM3340 + tempco  │
  │  AUDIO: saw/tri/sqr → niveles ecualizados      │
  │      → 3 OTAs (LM13700) ← mix CV compartidos   │
  │      → suma → jack OUT (normal → VCF)          │
  └────────────────────────────────────────────────┘
  telemetría I²C: sensor temp (pegado a los CEM3340) + EEPROM identidad
  alimentación local: +12 V → 78L05 (5 V DAC) → LDO 3.3 V (VLOGIC, 74HC14)
```

## 4. El núcleo, por voz

- **CEM3340** (o AS3340; decidir por sourcing, ver §11), condensador de tempo
  **1 nF NP0/C0G**, **R_TEMPCO 2k 3300 ppm/°C acoplada térmicamente al chip**
  (pegada, misma isla de cobre).
- **Cadena de CV**: canal del DAC (0-2.5 V) → amplificador ×2.8 con **TL074H**
  (el clásico deriva 9× más: `tuning_budget.py`) → nodo sumador donde entra el
  jack CV-IN → red de trims → entrada 1 V/oct. Resistencias 1 % película
  metálica: su error estático lo absorbe `tuning.json`, aquí solo importa la
  deriva.
- **Jack CV-IN**: Thonkiconn WQP-PJ398SM; el pin TN va a masa → sin cable el
  sumador recibe 0 V. Con cable, el CV externo **se suma** al del DAC: FM
  exponencial gratis sin perder el teclado.
- **Trims**: multivuelta 10k, escala y offset, por voz. Meta del ajuste: error
  de escala < ±2 % (que las 7 octavas quepan en 0-7 V con margen). El resto es
  del autoafinado.

## 5. La mezcla, por voz

- Las tres salidas del CEM3340 pasan por **redes de nivel fijas que ecualizan
  amplitudes** (la triangular sale más baja de fábrica — tesis, Tabla 11 — y
  se corrige aquí con resistencias, no con un mando) y atenúan al rango lineal
  del OTA.
- **6× LM13700** (2 OTAs por chip = 12 canales). Los 3 CV de mezcla del DAC se
  convierten a corriente de control; **cada CV alimenta los 4 OTAs de su onda**
  por resistencias 1 % — un 1 % de despareje entre voces es amplitud, no tono,
  e inaudible.
- Las salidas de corriente de los 3 OTAs de cada voz se suman en un op-amp a
  tierra virtual → **jack OUT de la voz**, normalizado hacia la entrada del
  VCF (el TN del jack de ENTRADA del módulo 5 hace el normal, convención §6).

## 6. El bloque digital

- **2× AD5686RB en cadena soldada** (DCEN, comando 1000; verificado en
  ad5686r_5685r_5684r.pdf p. 21-23). Asignación: chip 1 = pitch de las 4
  voces; chip 2 = PWM compartido (un buffer, fanout a los 4 CEM3340) + mezcla
  sierra/tri/cuadrada. **8 canales de 8: sin reserva** — un parámetro nuevo
  pediría un tercer chip en la cadena (cero hilos nuevos, que es el punto
  de §8 de architecture-poly).
- **Grado B obligatorio** (referencia 2 ppm/°C típ, 5 máx; el A con 20 máx
  revienta el presupuesto — `dac_local_budget.py` lo asevera).
- **SDO del último chip → MISO**: en cadena, lo que entra por MOSI sale por
  el final tras atravesar los dos chips — el firmware verifica la integridad
  del enlace comparando lo enviado con lo que vuelve. El readback de registros
  (comando 1001) existe además, pero el self-test básico es el passthrough.
- **74HC14 alimentado a 3.3 V**: 4 de sus 6 inversores recortan la cuadrada de
  cada voz → TUNE_OUT 1-4. Los dos sobrantes, con entrada a masa.
- **VDD del DAC a 5 V, VLOGIC a 3.3 V** — la lección del umbral VIH del
  módulo 2 aplica igual con el RP2350.

## 7. Enlace serie y mazo digital (cierra #34)

- **IDC 2×6 (12 pines)**: SCLK, MOSI, MISO, CS3, SDA, SCL, TUNE_OUT 1-4,
  GNDD ×2. Niveles 3.3 V. Reloj SPI moderado (≤10 MHz) con terminación serie
  en el extremo del cerebro.
- El pinout de este conector es **el contrato del enlace** para los módulos
  5, 6 y 7: mismo conector, mismas posiciones; cada módulo usa las señales
  que le tocan (los que no tienen TUNE_OUT dejan esos pines NC) y recibe su
  propio CS.
- Al cerrar #34 se actualiza la fila `SERIE` de la tabla de convenciones de
  architecture-poly §4 con el conteo real.

## 8. Telemetría (patrón de instrumento, estrena aquí)

- **Sensor de temperatura I²C** clase TMP1075/PCT2075 (direccionable ≥8
  posiciones por straps; parte exacta en §11), **colocado en el racimo de los
  CEM3340** — mide lo que la R_TEMPCO experimenta, que es la temperatura que
  desafina.
- **EEPROM I²C** clase 24AA02E48 (con ID único de fábrica): tipo de placa,
  revisión, serial, y el blob de calibración de sus 4 voces — **la
  calibración viaja con la placa**, no se queda huérfana en el cerebro.
- **El lazo que compra mejoras**: el cerebro registra (temperatura, correcciones
  del autoafinado) por voz y por pasada. Con eso se mide en cents/°C reales si
  un cambio térmico (acople del tempco, ventilación, layout) funcionó.
- **Test points etiquetados**: +12, −12, +5 local, 3.3 local, VREF (pin del
  DAC), CV de pitch de cada voz (post-amp), salida de mezcla de cada voz,
  GNDA, GNDD.

## 9. Alimentación y masas

- **78L05 desde +12 V** para VDD del DAC (~2 mA) → **LDO 3.3 V** para VLOGIC,
  74HC14, sensor y EEPROM (~5 mA). Carga de un solo riel — retorna entera por
  masa — dentro de la holgura de `I_MASA_SAM17` (50 mA).
- **GNDA/GNDD patrón del módulo 2**: el DAC con GND en GNDA (su salida se
  refiere ahí; su mA son 0.02 cents); la lógica cruza dominios sin problema;
  GNDD del mazo digital retorna al cerebro. Se unen solo en la estrella del
  módulo 1.
- **Regla de layout con aserción** (`dac_local_budget.py`): DAC pegado a los
  VCO, el retorno del módulo no cruza el camino DAC→VCO. Cota pesimista 0.08
  cents; bien hecho, 0.008.
- Consumo estimado del módulo: ~120 mA en +12 V (4× CEM3340 = 80, 6× LM13700
  ≈ 16, op-amps ≈ 20, lógica ≈ 7), ~100 mA en −12 V. La tabla de §9 de
  architecture-poly se actualiza al mergear (los LM13700 de mezcla no estaban).

## 10. Verificación

El patrón completo del repo, sin excepciones:

- `kicad/build_schematic.py` y `build_pcb.py` escriben el s-expr y verifican
  con kicad-cli (mismo motivo que bus board y módulo 2).
- **ERC 0, DRC 0**, `check_netlist.py` y `check_bom.py` cruzados.
- `dac_local_budget.py` ya en verde; sus aserciones vigilan grado de
  referencia y regla de layout.
- **Procedimiento de calibración** en `notes/`: (1) trim de offset centra el
  rango, (2) trim de escala a < ±2 % sobre 7 octavas con el afinador, (3) el
  autoafinado hace el resto y `tuning.json` queda en la EEPROM.
- Firmware (cuando toque): self-test del enlace por readback del DAC, y
  registro temperatura↔correcciones desde el primer arranque.

## 11. Riesgos y lo NO confirmado

1. **CEM3340 vs AS3340**: la reedición de OnChip y el clon de Alfa no son
   idénticos (rango de CV de PWM, red de sync). Decidir por sourcing real y
   leer el datasheet del que se compre ANTES de fijar valores.
2. **Parte exacta del sensor** (TMP1075 vs PCT2075 vs LM75B) y de la EEPROM:
   por disponibilidad; el contrato es «I²C direccionable ≥8» e «ID único».
3. **La linealidad de la mezcla por OTA** (distorsión a niveles altos de
   entrada) depende de la atenuación elegida; se fija con el datasheet del
   LM13700 en la mano y se comprueba en el prototipo.
4. **Zipper noise al mover la mezcla o el PWM** — ya listado en
   architecture-poly §11; si se oye, se suaviza por software (rampas).
5. **El DCEN con dos chips reales** sigue sin probar (architecture-poly §11.5);
   ahora es bloqueante y se prueba en el bring-up de esta placa.
6. **Diafonía del mazo digital** (SPI/I²C junto a TUNE_OUT) a comprobar en
   bring-up; si aparece, bajar reloj y/o intercalar el GNDD del conector.
7. Nada de esto está medido en placa. Son datasheets y presupuestos.

## 12. Fuera de alcance

- FM lineal, hard sync, ondas crudas al patch bay (descartados en §2 — no
  volver a discutir sin dato nuevo).
- Voltímetro de rieles por placa (los LED del bus board y los test points lo
  cubren; reabrirlo solo si el bring-up lo pide).
- El firmware del cerebro (RP2350) — esta placa define su contrato (enlace,
  telemetría, TUNE_OUT), no su código.
- La PCB del panel y la mecánica de los jacks (van con el diseño del case,
  módulo 8).
