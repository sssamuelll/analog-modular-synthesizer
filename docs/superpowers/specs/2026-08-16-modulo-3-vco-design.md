# Módulo 3 «VCO ×4» — cuatro voces state-of-the-art en una placa

> Sustituye al módulo de 3 osciladores independientes de la tesis (Gráficos
> 25-26). Hereda y aplica las decisiones ya mergeadas: mandos fuera del audio
> (architecture-poly §7), DAC en el módulo (§8), patch bay normalizado (§6),
> camino de afinación digital (§5). Cierra el issue #34.

## 1. Objetivo

La placa que genera el sonido crudo de las 4 voces: cuatro canales idénticos
**SSI2130** con un solo juego de mandos (que no viven aquí: son sensores del
panel, §7). Todo lo que la placa necesita del cerebro le llega como números
por el enlace serie; todo lo que da al resto del sinte sale como audio por
voz, ya mezclado, más los cuatro pulsos de afinación.

**Objetivo medible**: las 7 octavas de cada voz dentro del rango del DAC
**sin trimmers** (diseño trimless, §4), y de ahí el autoafinado sostiene el
suelo de 0.58 cents de `dac_local_budget.py`.

## 2. Decisiones fijadas (con Samuel, 2026-08-16)

1. **SSI2130 como núcleo** (Sound Semiconductor, 2020) en vez del CEM3340 de
   la tesis. Datasheet verificado (ssi2130datasheet.pdf): deriva del expo
   **200 ppm/°C típ compensada en chip** (16× mejor que el 3340 crudo, sin
   R tempco), **mezclador VCA de 5 canales dentro del chip**, seno de 0.76 %
   THD, sync y FM through-zero latentes. Se acepta a sabiendas: carácter
   triangle-core distinto del saw-core Prophet-5, y ensamblaje SMD.
2. **Mezcla de ondas con el mezclador interno, mando compartido.** 4 CV de
   nivel (sierra/tri/pulso/seno) desde el DAC, directos por resistencia — el
   control del mezclador es lineal, 0-50 µA. Entra en presets.
3. **Ni FM lineal ni hard sync** en esta versión — aunque el chip los trae,
   los jacks no: la FM exponencial ya la da el CV-IN, y el sync sin pareja
   por voz no aporta. Quedan latentes a coste cero.
4. **Patch bay: 8 jacks.** CV-IN ×4 (suman en el nodo del expo, normalizados
   a 0 V por TN) y salida de mezcla ×4 (normalizadas al VCF). Ondas crudas no
   se exponen: la mezcla da cualquier onda pura desde el preset.
5. **Enlace serie (#34): híbrido.** CS por módulo entre placas; los chips de
   cada placa en cadena soldada (DCEN al arranque). SCLK/MOSI/MISO
   compartidos. Quitar un módulo solo mata su CS.
6. **Telemetría de serie en toda placa** (patrón para 5, 6, 7 y cerebro):
   sensor de temperatura I²C pegado al punto térmicamente crítico, EEPROM de
   identidad/calibración en el mismo I²C, y test points en los nodos clave.
   Sin voltímetro de rieles.
7. **Diseño trimless.** Sin trimmers de escala ni offset: el span nominal se
   diseña con ~5 % de margen (≈7.4 octavas en el fondo de escala del DAC) y
   `tuning.json` + autoafinado absorben todo lo estático — incluida la
   no-conformidad del expo (0.3 %), que un trimmer no arregla y la tabla de
   84 notas sí. Menos piezas que derivan, cero calibración manual.
8. **Ensamblaje SMD de fábrica** (JLCPCB o similar): el QFN-32 de 4×4 mm lo
   exige, y estrena el flujo de manufactura para las placas siguientes.

## 3. Bloques

```
  enlace serie ──┐                          ┌── TUNE_OUT 1-4 (3.3 V)
  (SPI+CS3+I²C)  ▼                          │
     ┌───────────────────────┐         ┌────┴─────┐
     │ 3x AD5686 en cadena   │         │  74HC14  │
     │ ch1-4: PITCH  ch5: PWM│         └────▲─────┘
     │ ch6-9: MIX saw/tri/   │              │ SQUARE OUT (open-collector,
     │        pulso/seno     │              │  pullup a 3.3 V, por voz)
     │ ch10-12: reserva      │              │
     └──┬──────┬─────────────┘              │
 pitch×4 ▼      ▼ pwm, mix×4 (compartidos)  │
  ┌─────────────────────────────────────────┴───┐
  │  POR VOZ (×4):  SSI2130                     │
  │  expo in (nodo de corriente) ← R ← DAC      │
  │                              ← R ← jack CV-IN│
  │  tri/saw/pulso + seno→AUX1 → mixer interno  │
  │  MIX OUT (corriente) → op-amp I/V → jack OUT│
  └─────────────────────────────────────────────┘
  VREF 2.5 V única → DAC y los 4 SSI2130 (los errores escalan juntos)
  telemetría I²C: sensor temp (en el racimo de SSI2130) + EEPROM identidad
  alimentación local: +12 V → reg. 5 V (V+ de los chips y DAC) → LDO 3.3 V
```

## 4. El núcleo, por voz

- **SSI2130**: condensador de tempo **3.9 nF C0G** (valor recomendado del
  datasheet), compensación térmica en chip — **la R_TEMPCO de la tesis
  desaparece**.
- **CV de tono por suma de corrientes**: la entrada del expo es un nodo a
  tierra virtual (20 µA/octava). El canal del DAC entra por su resistencia
  (escalada para ≈7.4 octavas de span en fondo de escala: margen del 5 % que
  hace posible el trimless) y el jack CV-IN entra por 50 kΩ = 1 V/octava.
  **El amplificador ×2.8 y su deriva desaparecen**: la escala la fijan
  resistencias 1 % de película metálica, cuya tolerancia absorbe
  `tuning.json` y cuya deriva (~50 ppm/°C tracking) queda muy por debajo del
  término que el autoafinado ya cubre.
- **Jack CV-IN**: Thonkiconn WQP-PJ398SM; TN a masa → sin cable suma 0 V. Con
  cable, FM exponencial encima del teclado sin perder el control del cerebro.
- **Una sola VREF de 2.5 V para todo**: el SSI2130 exige VREF externa
  (2.49-2.51 V, 100 µA por chip) y su estabilidad manda en la afinación. La
  misma referencia clase ≤5 ppm/°C sirve al DAC y a los 4 osciladores: al
  compartirla, **sus errores escalan juntos y se cancelan** en el lazo
  DAC→expo. Cómo se materializa (ADR4525 dedicada + AD5686 pelado, o la
  interna del AD5686RB con buffer si su pin admite 400 µA) se fija en
  implementación con el datasheet — el contrato es UNA referencia, §11.3.

## 5. La mezcla, por voz — dentro del chip

- El mezclador de 5 canales del SSI2130 recibe tri/sierra/pulso ya escalados
  internamente (el problema de amplitudes desiguales de la tesis muere solo)
  y el **seno entra por AUX 1** desde el shaper del propio chip. AUX 2 queda
  NC (reserva).
- **4 CV de mezcla compartidos** (sierra/tri/pulso/seno): del DAC directo por
  resistencia (0-2.5 V sobre ~50 kΩ = 0-50 µA de control lineal, el máximo
  recomendado). Cada CV alimenta los 4 chips por resistencias 1 %: un 1 % de
  despareje entre voces es amplitud, no tono.
- **MIX OUT es salida de corriente** (500 µA máx recomendado): un op-amp en
  transimpedancia por voz → **jack OUT**, normalizado hacia la entrada del
  VCF (el TN del jack de ENTRADA del módulo 5 hace el normal, convención §6).

## 6. El bloque digital

- **3× AD5686 en cadena soldada** (DCEN, comando 1000; verificado en
  ad5686r_5685r_5684r.pdf p. 21-23): ch 1-4 pitch, ch 5 PWM compartido
  (fanout a los 4, la entrada PWM es de alta impedancia — rango exacto a
  verificar, §11.5), ch 6-9 mezcla, **ch 10-12 de reserva** (un parámetro
  futuro cuesta cero hilos).
- **La referencia clase ≤5 ppm/°C es obligatoria** — grado B si es la interna
  del RB; ADR4525 si es dedicada. El grado A / 20 ppm/°C revienta el
  presupuesto (`dac_local_budget.py` lo asevera).
- **SDO del último chip → MISO**: en cadena, lo que entra por MOSI sale por
  el final tras atravesar los tres chips — el firmware verifica la
  integridad del enlace comparando lo enviado con lo que vuelve.
- **74HC14 alimentado a 3.3 V**: el SQUARE OUT de cada SSI2130 es
  open-collector con pullup a 3.3 V; el Schmitt limpia el flanco RC del
  pullup antes del PIO → TUNE_OUT 1-4. Los dos inversores sobrantes, a masa.

## 7. Enlace serie y mazo digital (cierra #34)

- **IDC 2×6 (12 pines)**: SCLK, MOSI, MISO, CS3, SDA, SCL, TUNE_OUT 1-4,
  GNDD ×2. Niveles 3.3 V. Reloj SPI moderado (≤10 MHz) con terminación serie
  en el extremo del cerebro.
- El pinout de este conector es **el contrato del enlace** para los módulos
  5, 6 y 7: mismo conector, mismas posiciones; cada módulo usa las señales
  que le tocan (sin TUNE_OUT → pines NC) y recibe su propio CS.
- Al cerrar #34 se actualiza la fila `SERIE` de la tabla de convenciones de
  architecture-poly §4 con el conteo real.

## 8. Telemetría (patrón de instrumento, estrena aquí)

- **Sensor de temperatura I²C** clase TMP1075/PCT2075 (direccionable ≥8 por
  straps; parte exacta en §11), **colocado en el racimo de los SSI2130** —
  la compensación en chip deja un residuo de 200 ppm/°C típ, y este sensor es
  el que permite correlacionarlo con las correcciones del autoafinado.
- **EEPROM I²C** clase 24AA02E48 (ID único de fábrica): tipo de placa,
  revisión, serial, y el blob de calibración de sus 4 voces — **la
  calibración viaja con la placa**.
- **El lazo que compra mejoras**: el cerebro registra (temperatura,
  correcciones del autoafinado) por voz y por pasada. Con eso se mide en
  cents/°C reales si un cambio térmico o de layout funcionó — y es también la
  red de seguridad del diseño trimless.
- **Test points etiquetados**: +12, −12, +5 local, 3.3 local, VREF, CV de
  pitch en el nodo de cada voz, MIX OUT de cada voz, GNDA, GNDD.

## 9. Alimentación y masas

- **V+ de los SSI2130 es +5 V regulado (máx absoluto 5.25 V)** — el regulador
  local de §8 de architecture-poly pasa de «lógica» a alimentar también los
  osciladores: 4×3.75 mA + DAC ≈ 20 mA por el reg. de 5 V (78L05 sobra;
  ~180 mW de disipación, TO-92 aguanta). V− va de −12 V directo (el chip
  admite hasta −18 V), 4×2.9 mA. LDO 3.3 V para 74HC14, sensor y EEPROM.
- **Consumo total del módulo: ~35 mA en +12 V y ~15 mA en −12 V** — contra
  los ~120 mA que pedía la versión CEM3340+LM13700. Menos calor en el cajón =
  menos deriva para todos. La tabla de §9 de architecture-poly se actualiza
  al mergear.
- **GNDA/GNDD patrón del módulo 2**: DAC y osciladores con GND en GNDA;
  la lógica cruza dominios sin problema; GNDD del mazo digital retorna al
  cerebro. Se unen solo en la estrella del módulo 1.
- **Regla de layout con aserción** (`dac_local_budget.py`): DAC pegado a los
  osciladores, el retorno del módulo no cruza el camino DAC→VCO. Y las del
  datasheet del SSI2130: 100 nF pegado a cada chip, el land del EP existe en
  la huella pero va **aislado** — sin conexión eléctrica ni de masa
  (datasheet pág. 6, prohibición explícita: unirlo a masa convierte el land
  en una antena de acoplo entre las cuatro voces) —, C0G en el nodo de tempo
  con guard ring.

## 10. Verificación

El patrón completo del repo, sin excepciones:

- `kicad/build_schematic.py` y `build_pcb.py` escriben el s-expr y verifican
  con kicad-cli (mismo motivo que bus board y módulo 2).
- **ERC 0, DRC 0**, `check_netlist.py` y `check_bom.py` cruzados.
- `dac_local_budget.py` ya en verde; sus aserciones vigilan la referencia y
  la regla de layout.
- **Bring-up documentado en `notes/`**: (1) verificar span ≥7 octavas por voz
  dentro del rango del DAC (la apuesta trimless, §11.2), (2) autoafinado
  puebla `tuning.json`, (3) el blob queda en la EEPROM.
- Firmware (cuando toque): self-test del enlace por passthrough de la cadena,
  y registro temperatura↔correcciones desde el primer arranque.

## 11. Riesgos y lo NO confirmado

1. **El SSI2130 es de proveedor único** (Sound Semiconductor; distribución
   limitada — Cabintech, Amplified Parts, ~$6). Comprar los 4+repuestos al
   arrancar la implementación. Si desaparece del mercado, el plan B es el
   respin CEM3340 de la versión anterior de este spec (en el historial git).
2. **La apuesta trimless**: si un chip cae fuera del margen del 5 % de span,
   el bodge es una resistencia (no un re-spin), pero hay que comprobarlo en
   bring-up con los 4 chips reales.
3. **La materialización de la VREF única** (ADR4525 + AD5686 pelado vs
   interna del RB con buffer): se decide leyendo cuánta carga admite el pin
   VREF del AD5686R. Contrato: una sola referencia ≤5 ppm/°C para todo.
4. **Primera placa QFN/SMD del proyecto**: estrena flujo de ensamblaje de
   fábrica. Riesgo de proceso, no de diseño — pero es la primera vez.
5. **Rango exacto de la entrada PWM** del SSI2130 con el DAC directo: a fijar
   con el datasheet en la fase de esquemático.
6. **El carácter sonoro triangle-core** se aceptó por datasheet, no por
   oído. Si al oírlo no convence, el historial git guarda la alternativa.
7. **El DCEN con tres chips reales** sigue sin probar; bloqueante en bring-up.
8. **Diafonía del mazo digital** (SPI/I²C junto a TUNE_OUT): comprobar en
   bring-up; si aparece, bajar reloj y/o intercalar el GNDD del conector.
9. Nada de esto está medido en placa. Son datasheets y presupuestos.

## 12. Fuera de alcance

- Jacks de FM lineal, sync o TZFM — el chip los trae latentes; exponerlos es
  un respin de panel futuro con dato de uso real, no de esta versión.
- Ondas crudas al patch bay (descartado en §2 — no volver a discutir sin
  dato nuevo).
- Voltímetro de rieles por placa (LED del bus board + test points lo cubren).
- El firmware del cerebro (RP2350) — esta placa define su contrato (enlace,
  telemetría, TUNE_OUT), no su código.
- La PCB del panel y la mecánica de los jacks (van con el case, módulo 8).
