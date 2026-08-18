# Fuente v2 «GOAT» — regulación clase instrumentación para el SAM17

**Fecha:** 2026-08-16 · **Estado:** diseño aprobado por secciones, pendiente de
plan de implementación · **Reemplaza a:** la v1 solo cuando la v2 esté medida y
en verde; hasta entonces la v1 es la fuente del sistema **y la mula de medidas**.

## 1. Objetivo

Rieles analógicos **±12.000 V a 650 mA/riel con ruido de salida sub-µV**
(objetivo: 0.8 µVrms, 10 Hz–100 kHz), sobre la misma arquitectura de seguridad
y protección de la v1. La motivación no es audiófila: el autoafinado por
instrumentación ([architecture-poly.md](../../architecture-poly.md)) cronometra
periodos contra referencias que cuelgan de estos rieles, y el conversor
exponencial de cada VCO convierte cualquier deriva del riel en cents. La fuente
es el suelo de referencia del instrumento.

## 2. Decisiones fijadas (con Samuel, 2026-08-15/16)

| Decisión | Elección |
|---|---|
| Arquitectura | **Respin v2 integrado** de la placa de la fuente (no sidecar, no islas por módulo) |
| Montaje SMD | **Ensamblaje JLCPCB** (una sola cara); THT de potencia a mano |
| La v1 | **Se pide igual y hace de mula**: la v2 se congela contra sus medidas |
| Corriente | **650 mA/riel** (paridad Doepfer A-100NT12, y el censo poly §8 la respalda) |
| Silicio ultra | **LT3045 ×2 / LT3094 ×2** en paralelo (variante A′); plan B TPS7A4701/3301 |

## 3. Topología

```
VRAW+ (14.1…20.5 V) ─► LM2941 (TO-220, disipador) ─► +13.1 V ─► LT3045 ×2 ─► +12.000 V
VRAW− (simétrico)   ─► LM2991 (TO-220-5, disipador) ─► −12.9 V ─► LT3094 ×2 ─► −12.000 V
```

- **Pre-reguladores ajustables** LM2941CT (+13.1 V) y LM2991T (−12.9 V): se
  comen el grueso de la caída sobre disipador. Son ajustables **a propósito**:
  si la mula mide un valle mejor que el simulado, el margen se compra girando
  el divisor, no rediseñando. El LM2991 que §16.3 de la v1 descartó entra aquí
  por derecho: su divisor obligatorio es ahora la función, y su carga mínima de
  500 µA la da ese mismo divisor por diseño (anotado en esquemático para que
  nadie lo «optimice» a valores altos).
- **Etapa ultra en paralelo**: 2 chips por riel con ballast de **20 mΩ**,
  ~325 mA por chip (holgura sobre sus 500 mA). Caída ~1.1 V (+) / ~0.9 V (−) →
  ~0.35 W por chip.
- **Asimetría deliberada** (+13.1 / −12.9): el LM2991 tiene peor dropout que el
  LM2941 y ahí se le compra margen de valle; a los LT3094 les basta ~0.3 V.
- **ILIM programado**: el LT3045/LT3094 traen límite de corriente de precisión
  por resistencia — se fija a **~800 mA por riel**. Una capa más fina que el
  límite genérico del silicio.
- Márgenes de valle sobre el simulado (14.12 V @ 207 V): **+0.37 V** (positivo),
  **+0.22 V** (negativo). Finos, clase v1 — la mula decide (§10).

## 4. Térmica

| Elemento | Caída × I | Nominal | Peor caso (red +10 %) | Disipación en |
|---|---|---|---|---|
| LM2941 | 15.7→13.1 V | ~1.7 W | ~2.7 W | TO-220 + SK 129/38,1 (hueco v1) |
| LT3045 ×2 | 13.1→12.0 V | 0.36 W/chip | ~0.4 W | cobre + granja de vías |
| LM2991 | 15.7→12.9 V | ~1.8 W | ~2.9 W | TO-220-5 + SK 129 (sigue el más caliente) |
| LT3094 ×2 | 12.9→12.0 V | 0.29 W/chip | ~0.33 W | cobre |

El calor total del cajón no sube respecto a la v1: los pre-regs disipan ~0.6 W
menos cada uno y ese calor reaparece en cuatro SMD fríos. La isla SMD va en la
diagonal opuesta a los TO-220. **Puertas de datasheet antes de congelar**
(lección §16.1: garantizado ≠ típico): (a) dropout de LM2941/LM2991 a 650 mA
garantizado sobre temperatura; (b) **a qué está conectado el tab de cada uno**
— se lee, se escribe, y si muerde (como el del LM2990) va con mica.

## 5. Protecciones

Heredado sin tocar: fusible 250 mA lento en primario, MOV S20K275, NTC de
inrush, barrera fresada ≥ 6 mm, portafusible cerrado, **crowbar en +12 V**
(§16.8 v1: sí en +12, no en −12 — análisis vigente), puente único GND-chasis
por faston (§13).

Nuevo por la cascada:

1. **TVS por nodo intermedio** (clase SMAJ15A): si un pre-reg falla en corto,
   el LT ve VRAW — pico 20.54 V contra abs max de 20 V. El TVS contiene el
   fallo simple; el crowbar cubre el doble.
2. **Schottky out→in por pareja ultra** (SS14): apagón con 9400 µF detrás no
   polariza los LT al revés.
3. **Soft-start gratis**: el condensador de SET (§6.1) hace que la salida suba a
   la velocidad de carga de la referencia. Sin golpes de arranque a los módulos.

Capa física (ya existente, se conserva y se completa):

- Bus ±12 V por **Molex KK-254 4 pos CON llave**; +5 V por KK-254 **2 pos** —
  imposible cruzarlos entre sí por geometría.
- Peine Eurorack **sin llave a propósito** (Doepfer lo prohíbe); convención
  franja roja = −12 V serigrafiada, verificación issue #15.
- **PTC 0.25 A por riel y por slot** en el bus board + LED delator por riel.
  Jamás en masa (94 cents de desafinación, calculado).
- **Regla nueva para los módulos 2-7**: protección de polaridad inversa en
  la entrada de alimentación de cada módulo + RC de 10 Ω / 10-47 µF por riel.
  Es la única defensa válida contra la cinta IDC invertida, y el RC remata el
  rizado residual en el punto de uso.

## 6. Layout y ruido — donde se gana el µV

1. **Red de SET**: 100 µA × 120 kΩ = 12.000 V. **22 µF sobre R_SET** filtra la
   referencia al suelo de 0.8 µV. Baja fuga obligatoria (cada nA por el
   condensador es error de salida), pegado al pin, retorno limpio. Los dos LT
   de cada riel **comparten una sola red SET** (nota de aplicación ADI): una
   referencia, dos músculos.
2. **Sense Kelvin**: OUTS conectado después de los ballast, en el punto donde
   el riel sale hacia el bus. 12.000 V en el conector, no en el pad.
3. **Dos masas, un solo puente**: la masa de referencia (SET, OUTS, divisores)
   es una isla unida en un único punto a la de potencia. Los 650 mA con pulsos
   de rectificación jamás pisan el cobre de la referencia.
4. **El lazo puente→bulk, compacto y en su esquina**: es el peor radiador de la
   placa (§18). La isla ultra vive en la diagonal opuesta con los TO-220 de
   muralla en medio.
5. **ESR y piezoelectricidad**: los LT son estables con 10 µF cerámicos sin
   ventana de ESR (la pesadilla §17.3 de la v1 desaparece en la salida), pero
   los pre-regs **sí conservan la suya** (≥ 22 µF acotado, contra datasheet).
   Cerámicos de SET/salida: X7R de calidad o polímero, lejos del borde que
   más flexa — un cerámico es un micrófono piezoeléctrico en un cajón que vibra.

Placa: 2 capas, 1 oz. Esto es dominio de 100 Hz; la disciplina de islas basta.

## 7. Dominios de alimentación del instrumento (post-pivote)

La computadora vive **fuera** ([architecture-compute.md](../../architecture-compute.md)):
no hay dominio de máquina, ni SMPS de 60 W, ni DC jack de cómputo.

| Dominio | Fuente | Presupuesto | Masa |
|---|---|---|---|
| ±12 V analógico | lineal GOAT (esta spec) | 650 mA/riel | GNDA |
| +5 V analógico | 7805 de la v1, se hereda | 300 mA (DACs ×5 ≈ decenas de mA) | GNDA |
| **+5 V digital** (nuevo) | **SMPS encapsulada** clase Mean Well IRM-15-5 (5 V/3 A) | RP2350 ~0.2 A + WS2812 con **tope de brillo por firmware**; peor caso bruto 40-100 LEDs × 60 mA = 2.4-6 A → el tope es de diseño, no cosmético | GNDD |
| Gates 10 V | drivers desde +12 V (módulo 3) | mA | GNDA |

- La SMPS digital cuelga de la red **tras el mismo fusible y MOV**, sobre masa
  digital. Su colocación y blindaje dentro del cajón los arbitra el frente de
  zumbido (§18): acabamos de volver a meter un conmutador en la casa del
  sub-µV, y es contenible (módulo encapsulado, lejos, masa propia) pero se
  decide con ese criterio, no por comodidad de layout.
- **GNDD↔GNDA se unen en un solo punto**, donde diga §18.
- **Frontera con la computadora externa**: el USB trae la masa del host (lazo
  de tierra de manual); MIDI DIN va opto por norma. USB para comodidad, DIN
  para grabar, aislador USB como opción. Pendiente de la caja, anotado aquí
  para que no se pierda.

## 8. Censo de corriente (cerrado contra BOM y datasheets, 2026-08-18)

**El censo vive en [`architecture-poly.md` §9](../../architecture-poly.md), no
aquí.** Esta sección lo cita y le añade lo que solo importa del lado de la
fuente. Un número, un dueño: hasta hoy había dos censos en dos documentos y
esta sección llevaba el viejo.

| Bloque | Consumo por riel | De dónde sale |
|---|---|---|
| Módulo 3 (VCO ×4, SSI2130) | ~35 mA | `dac_local_budget.py`, contra el BOM real del respin |
| 4× VCF + 4× VCA (8× LM13700) | ~21 mA | 2.6 mA/encapsulado a I_ABC = 500 µA (TI SNOSBW2F) |
| 4× ADSR (LM358 + ICM7555) | ~4 mA | ~0.6 mA/amplificador a ±12 V, **interpolado** entre los dos puntos que da el datasheet (300 µA a 5 V, 800 µA a 36 V — TI SLOS068AB); el 7555 es µA |
| Op-amps del instrumento (~8× TL074) | ~45 mA | 1.4 mA/amplificador típ (TI SLOS080W) |
| Módulo 2 (DAC + buffers) | ~11 mA | |
| **Total 4 voces** | **~116 mA** | |
| **Con ×1.5 de diseño** | **~174 mA** | |

Contra el envelope de **650 mA/riel** eso es **holgura 3.7×**. A 8 voces
(~176 mA brutos, ~264 mA con margen) siguen sobrando 2.5×.

### Qué cambió respecto de la versión anterior de esta sección

| | decía | dice |
|---|---|---|
| VCO | 4× CEM3340, ~80 mA | 4× SSI2130, ~35 mA — **la tesis, no el diseño** |
| Bruto | 130-150 mA/riel | ~116 mA/riel |
| Con margen | 200-225 mA | ~174 mA |
| Estado | «pendiente de los respins» | cerrado para el módulo 3; estimado para 4-7 |

El error viejo era **conservador**: sobra más holgura de la que se creía, así
que nada de lo dimensionado contra él queda corto. El CEM3340 salió del diseño
el 2026-08-17 (architecture-poly §10) y esta sección no se enteró.

### Lo que este censo NO cierra

- **Los módulos 4, 5, 6 y 7 no están respinados.** Sus `bom.csv` son los
  esqueletos de la tesis del 2026-04-16, sin tocar desde entonces. Las filas de
  arriba salen del recuento de encapsulados que impone
  [architecture-poly §10](../../architecture-poly.md) (4× LM13700 por módulo,
  un juego de mandos), no de un BOM respinado. Se re-verifica al respinarlos.
- **Este censo no dimensiona TR1.** El toroidal de 120 VA **no se eligió por
  corriente** — se eligió porque su resistencia de devanado es la mitad que la
  del de 80 VA, y eso es lo que sostiene los 13.6 V de valle que exige U1 (ver
  nota de TR1 en `hardware/01-power-supply/v2/bom.csv` y §16.5). Un censo bajo **no** autoriza bajar de
  VA: el criterio es la caída bajo el pico de carga del banco de 9400 µF, no
  los mA que pide el instrumento.

### El techo que ya está construido: los PTC de la bus board

La bus board lleva **12 PTC de 0.25 A hold / 0.50 A trip** — seis ranuras × dos
rieles. Eso pone un techo por módulo de **250 mA/riel** que ninguna versión de
este censo había escrito, y que es más estricto que el envelope global en el
único sitio donde importa: un módulo solo no puede llevarse la fuente. Con
~20-40 mA por módulo, el margen contra el hold es de un orden de magnitud.

Si alguna vez el instrumento pide más de 650 mA/riel, el problema es de
módulos, no de esta placa.

## 9. Placa, ensamblaje y repo

- **Formato heredado**: 150×200 mm, 2 capas, mismos NPTH, misma ranura de
  barrera. Entra en el mismo cajón con los mismos separadores.
- **SMD en una sola cara** (el ensamblaje a doble cara duplica coste): LT3045
  ×2, LT3094 ×2, TVS, Schottkys, ballast, redes SET, cerámicos.
- **Puerta dura: el silicio se congela contra stock real de LCSC el día de
  mandar.** LT/ADI suele estar en «extended parts»; si no hay, **plan B
  TPS7A4701/TPS7A3301** (1 A, sin paralelar, 4/15 µVrms — pinout distinto, no
  admite huella dual, por eso el esquemático se construye después del stock).
- Pre-regs LM2941CT/LM2991T: Mouser/TME, silicio trazable (lección §17.3).
- **Repo**: `hardware/01-power-supply/v2/` con sus `build_schematic.py` /
  `build_pcb.py` (esqueleto v1). El pipeline gana `kicad-cli pcb export pos` +
  BOM formato JLC.

## 10. Plan de validación

1. **La mula fija los números**: valle de VRAW a plena carga (dummy resistiva
   650 mA/riel) y en caliente, pico en vacío, rizado real del −12 V, térmica en
   régimen. Con eso se ajustan los divisores de los pre-regs y se congela la v2.
2. **Stock LCSC verificado** → silicio fijado → esquemático.
3. **Bring-up escalonado** (checklist §9 v1 adaptado): tierra → visual → solo
   trafo → nodos intermedios en sus test points → rails con carga dummy →
   módulos.
4. **El GOAT tiene dos niveles de aceptación**: mínimo = rizado bajo el suelo
   medible del osciloscopio con BW limitado (~sub-mV, ya 10× mejor que v1);
   pleno = **LNA delante del osciloscopio** para ver los µV. El LNA es equipo
   que no existe todavía: ítem propio, no bloquea el pedido.

## 11. Riesgos y lo NO confirmado (estilo §17)

1. Dropout garantizado de LM2941/LM2991 a 650 mA: **no leído aún**. Los
   márgenes de §3 viven o mueren ahí.
2. Conexión del tab de ambos pre-regs: **no leída**. Se asume mica hasta leer.
3. Stock LCSC de LT3045/LT3094: **no verificado** — por eso existe el plan B.
4. El margen de valle (+0.22 V el peor) es fino **hasta que la mula mida**.
5. La SMPS digital reintroduce conmutación en el cajón: contenida por diseño,
   pero **§18 tiene veto** sobre su colocación.
6. El censo §8 es estimación: los módulos poly no tienen BOM aún.
7. Los 0.8 µVrms son el dato de datasheet con el layout de la nota de
   aplicación: **nuestro número real se mide con el LNA, y hasta entonces no se
   presume**.

## 12. Fuera de alcance

La computadora externa y su alimentación (no existe dominio de máquina), el bus
board (cerrado, con sus PTC y su verificación #15), el diseño del LNA de
medida, los respins de módulos (heredan las reglas de módulo de §5), y el firmware.
