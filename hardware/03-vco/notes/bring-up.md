# Módulo 3 (VCO ×4, SSI2130) — bring-up

Procedimiento para la **primera placa física**. No es una lista para tachar: es
el orden en que hay que hacer las cosas para que un fallo no se lleve por
delante cuatro chips de proveedor único, más lo que se espera medir en cada
punto y qué significa cuando el número no sale.

Se escribe **antes** de tener la placa. Todo lo que dice de tolerancias sale de
datasheets y de los presupuestos ejecutables del repo
([`dac_local_budget.py`](../dac_local_budget.py),
[`autotune_budget.py`](../../02-midi-cv/autotune_budget.py)). Nada de esto está
medido todavía — [§11](#11-lo-que-este-documento-no-sabe) dice exactamente qué.

**Los pasos 1 a 7 son los que fijó el plan de la tanda.** El Paso 0 (sin
alimentación), el 8 (diafonía del mazo, riesgo §11.8 del spec) y el 5b
(mezclador, PWM y seno) los añade este documento porque sin ellos el
procedimiento no cierra: el 0 protege los SSI2130, el 5b es la mitad del audio
que el Paso 5 no toca, y el 8 es un riesgo abierto del spec que solo se cierra
con placa.

Referencias: [spec del módulo](../../../docs/superpowers/specs/2026-08-16-modulo-3-vco-design.md),
[`kicad/build_schematic.py`](../kicad/build_schematic.py) y
[`kicad/build_pcb.py`](../kicad/build_pcb.py) (los porqués de cada decisión
viven en sus docstrings), [`pcb/README.md`](../pcb/README.md) (fabricación).

---

## Qué hace falta en la mesa

| | |
|---|---|
| Multímetro | **4½ dígitos o mejor**. Un 3½ dígitos lee «2.50 V» en VREF y no te dice nada: la tolerancia que hay que comprobar es ±0.5 mV |
| Fuente de banco | doble, ±12 V, **con límite de corriente ajustable** |
| Frecuencímetro | o el propio cerebro contando `TUNE_OUT`. Entrada lógica 3.3 V |
| Osciloscopio | para el Paso 5b (formas de onda) y el 8 (flancos). No hace falta antes |
| Cerebro (RP2350) o un Pi | con SPI + I²C + 4 entradas de contaje, y el mazo IDC 2×6 |
| Soldador de punta fina | para los bodges de `R_PITCH` (0805) del Paso 5 |

Y **un cuaderno**. El Paso 7 no es una medida de aprobado/suspenso: es el primer
punto de una serie que solo significa algo comparada con la siguiente placa. En
§9 hay una hoja para rellenar.

---

## 0. Antes de nada: el orden de montaje decide qué se puede romper

La placa sale de fábrica con las **111 huellas SMD montadas** (107 si los
SSI2130 no van consignados) y **sin ningún conector through-hole**. Los cuatro
SSI2130 van por uno de dos caminos ([`pcb/README.md`](../pcb/README.md)), y
**el camino cambia el bring-up**:

**Camino A — SSI2130 consignados a la fábrica.** La placa llega entera. Es el
camino mecánicamente seguro: QFN-32 de 0.4 mm de paso con pad térmico pide
horno de reflujo. El precio es que los pasos 1 a 4 se hacen con los cuatro chips
ya encima, y **un riel de +5 V que se vaya a 12 V se lleva a los cuatro de
golpe**. Los dos repuestos no salvan nada: reponer un QFN pide el mismo horno
que no tienes.

**Camino B — SSI2130 a mano, después.** La fábrica monta los otros 107 SMD; tú
sueldas U1-U4 con stencil y placa caliente **después de que los pasos 1 a 4
pasen**. Los chips caros solo se ponen encima de rieles ya medidos.

> **La regla de decisión: camino B si tienes placa caliente y stencil y ya has
> hecho un QFN antes. Camino A si no.** El camino B elimina el riesgo eléctrico
> y el A el mecánico — pero el B solo elimina el suyo si sabes soldar el QFN. Si
> no, se come los chips igual, nada más que con soldador en vez de con tensión.

Con el camino A no hay forma de quitar los chips, así que el sustituto del
«medir antes de ponerlos» es la **fuente limitada y la rampa a mano** del
Paso 1: impedir que el riel llegue nunca a un valor malo, ya que no se puede
comprobar con la placa desierta.

### Los conectores: cuáles hay que soldar YA

`pcb/README.md` los mete a todos en el mismo saco («van con el panel»). Para el
bring-up hay que separarlos:

| Conector | ¿Antes del bring-up? | Por qué |
|---|---|---|
| **J1** (KK-254, +12/G/G/−12) | **Sí** | Sin él no hay alimentación. No es de panel: es un conector de cable en el borde de abajo (94, 114) |
| **J2** (IDC 2×6, mazo digital) | **Sí** | Sin él **no hay GNDD en la placa** — ver el aviso de abajo. Tampoco es de panel (16, 115) |
| **J_CV1-4** (Thonkiconn) | **Sí, o un puente** | Su normal (TN) ata `CVIN_n` a GNDA. Sin jack, `CVIN_n` queda **flotante** colgando de `R_CVIN` (49.9 k) contra el nodo suma del expo: **1 mV de zumbido captado ahí son 1.2 cents de desafinación**. Si no quieres soldar los jacks todavía, **puentea el pad de punta al de manguito** en las cuatro |
| **J_OUT1-4** | No | La salida de voz se pincha en el pad de punta del jack, que es through-hole y se sondea de sobra. Estos sí esperan al panel |

> **GNDD entra por J2 y por ningún otro sitio.** Los pines 2 y 6 del mazo son el
> único camino de la masa digital a esta placa. Con J2 desconectado, U10
> (74HC14), U13 (TMP1075) y U14 (EEPROM) tienen alimentación (+3V3_LOC, que
> cuelga de GNDA) y **no tienen retorno**: nada digital funciona y `TP15` no
> mide nada. No es dañino — se quedan con ~0 V entre patas — pero explica por
> qué el Paso 1 se hace contra `TP14` (GNDA) y no contra `TP15`.

### Los 15 test points NO están rotulados en la serigrafía

Decisión de [`build_pcb.py`](../kicad/build_pcb.py): las referencias de pasivos
y test points se ocultan (`SetVisible(False)`) porque a 3 mm de paso los rótulos
de 1 mm se pisan entre sí. Consecuencia práctica: **en la placa hay 15 pads de
2.0 mm sin nombre**. Esta tabla es la única forma de saber cuál es cuál.

Coordenadas en mm **desde la esquina superior izquierda de la placa** (el origen
de `Edge.Cuts`, con Y creciendo hacia abajo — convención de KiCad; los jacks
quedan arriba, en `y = 7`, y J1/J2 abajo). Son **pads SMD en F.Cu**, no postes:
usa punta de aguja o suelda un cable corto.

| TP | Red | x, y (mm) | Dónde está |
|---|---|---|---|
| TP1 | `+12V` | 70.0, 102.0 | esquina de alimentación, abajo derecha |
| TP2 | `-12V` | 64.0, 102.0 | ídem |
| TP3 | `+5V_LOC` | 78.0, 102.0 | ídem, junto a U11 |
| TP4 | `+3V3_LOC` | 86.0, 106.0 | ídem, junto a U12 |
| TP5 | `VREF_2V5` | 72.0, 65.0 | centro, pegado a U8 (ADR4525) |
| TP6 | `CV_PITCH_1` | 11.8, 25.4 | celda de la voz 1 (U1 en 27, 35) |
| TP7 | `CV_PITCH_2` | 42.2, 90.6 | celda de la voz 2 (U2 en 27, 81) |
| TP8 | `CV_PITCH_3` | 74.8, 25.4 | celda de la voz 3 (U3 en 90, 35) |
| TP9 | `CV_PITCH_4` | 105.2, 90.6 | celda de la voz 4 (U4 en 90, 81) |
| TP10 | `MIXO_1` | 11.8, 44.6 | celda de la voz 1 |
| TP11 | `MIXO_2` | 42.2, 71.4 | celda de la voz 2 |
| TP12 | `MIXO_3` | 74.8, 44.6 | celda de la voz 3 |
| TP13 | `MIXO_4` | 105.2, 71.4 | celda de la voz 4 |
| TP14 | `GNDA` | 68.0, 32.0 | centro arriba, junto a U9 |
| TP15 | `GNDD` | 40.0, 105.5 | isla digital, abajo izquierda |

> **`MIXO_n` (TP10-13) NO es la salida de audio.** El nombre engaña. Es el pin
> 25 del SSI2130 unido a la entrada inversora de su op-amp: **una tierra
> virtual**. Ahí siempre se leen ~0 V, y eso es justo lo que lo hace útil (ver
> Paso 5b). El audio sale por `VOICE_OUT_n`, en el pad de punta de `J_OUT{n}`.

### Las cuatro voces, dónde están

Cuadro 2×2. **Las voces 2 y 4 (fila de abajo) están giradas 180°** — no es
simetría por gusto, es que así los buses del mezclador miran al centro
([`build_pcb.py`](../kicad/build_pcb.py), `ROT_VOZ`). Al buscar un pasivo
concreto, en las voces 2 y 4 el desplazamiento va al revés.

| Voz | SSI2130 | `R_PITCH` (el bodge del Paso 5) | `R_LIN` (el que hace que arranque) |
|---|---|---|---|
| 1 | U1 (27.0, 35.0) | 16.5, 35.0 | 38.5, 32.0 |
| 2 | U2 (27.0, 81.0) — girada | 37.5, 81.0 | 15.5, 84.0 |
| 3 | U3 (90.0, 35.0) | 79.5, 35.0 | 101.5, 32.0 |
| 4 | U4 (90.0, 81.0) — girada | 100.5, 81.0 | 78.5, 84.0 |

U13 (TMP1075) vive en (32.0, 86.0): **a 2.12 mm del cuerpo de U2**, dentro del
área analógica, con un vertido térmico **sin red** (cobre flotante a propósito)
hacia la esquina del QFN. Mide la voz 2 principalmente; las otras tres las ve
por el plano. Eléctricamente sigue en GNDD, por pista.

---

## Paso 0 — Sin alimentación

Nada conectado: J1 fuera, J2 fuera, nada patcheado. Multímetro en resistencia.

| Medida | Esperado | Si no |
|---|---|---|
| `TP1` (+12V) ↔ `TP14` (GNDA) | > 10 kΩ | corto en el riel del bus. Sospechoso: C25 (10 µ) del revés o dañado |
| `TP2` (−12V) ↔ `TP14` | > 10 kΩ | ídem, C26 |
| `TP3` (+5V_LOC) ↔ `TP14` | > 1 kΩ | corto en la salida de U11. Con 4 SSI2130 + 3 DAC + U8 colgando es normal ver decenas de kΩ, no ohmios |
| `TP4` (+3V3_LOC) ↔ `TP14` | > 1 kΩ | ídem, U12 |
| `TP5` (VREF) ↔ `TP14` | **~6 kΩ**, no un corto | Aquí cuelgan en paralelo 4× `R_SCALE` (26.7 k) y 4× `R_LIN` (499 k): **6.3 kΩ es lo esperado**, no infinito. Ohmios = corto en la referencia; megaohmios = las `R_SCALE` no están puestas |
| **`TP14` (GNDA) ↔ `TP15` (GNDD)** | **abierto, > 1 MΩ** | las dos masas se tocan en esta placa, que es exactamente lo que el diseño prohíbe (se unen solo en la estrella del módulo 1) |

> El GNDA↔GNDD hay que medirlo **en modo resistencia, no en modo diodo**. En
> diodo verás una unión de ~0.7 V y no es un fallo: es el camino
> GNDD → diodo de protección de U10 → `SQ_n` → pin 28 de un SSI2130 → GNDA. Las
> estructuras de ESD existen. En resistencia, a la tensión de prueba del
> multímetro, esa unión no conduce y la lectura es correcta.

**Antes de enchufar J1, comprueba su orden.** Con el conector ya soldado y sin
cable: pin 1 → `TP1`, pin 4 → `TP2`, pines 2 y 3 → `TP14`. Un KK-254 de 4 pines
entra al revés sin quejarse y eso pone −12 V donde va +12 V.

Y a ojo, con lupa: **puentes de estaño en los cuatro QFN** (0.4 mm de paso), y
que el **EP (pad térmico) de cada SSI2130 quede aislado** — el land existe en la
huella pero no debe tener red ni vía. Lo prohíbe el datasheet (pág. 6) y
`verificar_ep()` lo comprueba en el fichero; en la placa hay que comprobar que
la pasta no lo haya unido a nada.

---

## Paso 1 — Rieles y VREF

**Fuente de banco, no el bus board.** Límites: **+12 V a 100 mA**, **−12 V a
50 mA** (el consumo previsto es ~35 mA y ~15 mA; el doble deja sitio a la
irrupción de los 10 µF sin permitir que un corto cocine nada).

Sube los dos rieles **a mano, desde 0, en unos segundos**, con el multímetro en
`TP3` (+5V_LOC). Si algo va mal en U11, `TP3` sigue a la entrada en vez de
plancharse en 5 V, y lo ves antes de pasar de 5.25 V — que es el **máximo
absoluto** del SSI2130 y del AD5686R.

| Medida | Esperado | Tolerancia |
|---|---|---|
| Corriente en +12 V | 30 – 40 mA | si pasa de 60 mA, apaga |
| Corriente en −12 V | 12 – 18 mA | si pasa de 30 mA, apaga |
| `TP1` (+12V) vs `TP14` | +12.0 V | lo que dé la fuente |
| `TP2` (−12V) vs `TP14` | −12.0 V | |
| `TP3` (+5V_LOC) vs `TP14` | **5.00 V ±5 %** | 4.75 – 5.25 V |
| `TP4` (+3V3_LOC) vs `TP14` | **3.30 V ±5 %** | 3.14 – 3.47 V |
| `TP5` (VREF) vs `TP14` | **2.5 V, ventana ANCHA todavía** | ver el aviso |
| `TP6`-`TP9` (CV_PITCH 1-4) | **0 V** (< 5 mV) | |
| `TP15` (GNDD) | no mide nada aún | J2 está fuera |

**La ventana ancha de VREF en este paso.** El pin VREF del AD5686R es
**bidireccional**: es salida mientras la referencia interna está encendida, y
entrada cuando se apaga. Al arrancar, las tres referencias internas están
**encendidas de fábrica** y empujan contra la ADR4525 en la misma red. O sea que
en el Paso 1 lo que mides es **cuatro referencias de 2.5 V peleándose**, no la
ADR4525. Criterio aquí: **2.500 V ±10 mV**, nada más. La tolerancia de verdad
(±0.02 % = ±0.5 mV) solo tiene sentido después del Paso 4.

Si en este paso VREF se sale de ±10 mV, **apaga**: no lo dejes peleando. El
sospechoso es U8 o su alimentación, no las internas.

**`TP6`-`TP9` a 0 V es una comprobación de verdad, no un trámite.** `RSTSEL` de
los tres DAC está atado a GNDA a propósito: al arrancar, las salidas caen a
**fondo de escala cero**. Con `RSTSEL` alto arrancarían a media escala y las
cuatro voces sonarían una nota sola al encender. Si `TP6` lee 1.25 V, eso está
mal soldado o mal cableado.

**U11 va a estar caliente y no es un fallo.** (12 − 5) V × ~25 mA = 175 mW en un
SOT-89: unos 20-25 °C por encima del ambiente. Está en (84, 98), en la esquina
de alimentación: 18 mm del QFN más cercano (U4) y **57 mm de U13**, el
termómetro. Su calor no contamina la medida del Paso 7, que es lo que importa.

### Si falla

| Síntoma | Diagnóstico |
|---|---|
| La fuente entra en límite al subir | Corto. Vuelve al Paso 0: casi seguro un 10 µF o un regulador del revés |
| `TP3` sigue a la entrada por encima de 5.5 V | U11 mal orientado o muerto. **Apaga inmediatamente**: los SSI2130 y los DAC están por encima de su máximo absoluto |
| `TP3` bien, `TP4` a 0 | U12 (LD1117S33). Ojo: su patilla de tab es la 2 (salida), no masa |
| `TP4` bien, `TP5` a 0 | U8 (ADR4525) o su C10/C11. Comprueba que le llegan los 5 V al pin 2 |
| `TP5` en ~5 V | U8 en corto entrada-salida, o el símbolo mal cableado. Apaga: 5 V en `R_SCALE` duplica la corriente de escala de los cuatro chips |
| Consumo muy por debajo de lo previsto | Algo no está alimentado. Con el camino B (SSI2130 todavía sin poner) esto es **lo normal**: sin los cuatro osciladores el consumo cae a ~10-15 mA en +12 V y ~2 mA en −12 V |

---

## Paso 2 — I²C: la placa dice quién es y qué temperatura tiene

**Ahora sí hace falta J2 conectado** (es por donde entra GNDD). Conecta el mazo
al cerebro **con los dos aparatos apagados**, y luego enciende: primero el
módulo, después el cerebro.

> **Nunca dejes el cerebro encendido contra el módulo apagado.** El cerebro
> conduce SCLK/MOSI/CS3/SDA/SCL a 3.3 V; contra un módulo sin alimentación, esa
> corriente entra por los diodos de protección de los DAC hacia `+3V3_LOC` y
> alimenta la placa por la puerta de atrás. No es destructivo con las corrientes
> de un GPIO, pero es cómo se provocan latch-ups. En el instrumento montado no
> pasa: todo cuelga del módulo 1 y sube junto.

Bus I²C a 100 kHz para empezar (los pullups son 4.7 k a 3.3 V; a 400 kHz también
debería ir, pero no es el momento de averiguarlo).

**Escaneo del bus.** Esperado: exactamente **dos direcciones**.

| Dispositivo | Dirección | Qué es |
|---|---|---|
| U13, TMP1075 | **0x48** | A2/A1/A0 los tres a GNDD → dirección base, «sensor 0». Los módulos 5/6/7 usarán 1/2/3 con otros straps |
| U14, 24AA02E48 | **0x50** | EEPROM de 256 B |

**Identidad (U14).** Lee 6 bytes desde **0xFA**: es el EUI-48 único de fábrica,
grabado por Microchip y **protegido contra escritura**.

- Criterio: los tres primeros bytes son **`00 04 A3`** — el OUI de Microchip. Si
  salen `FF FF FF`, o no estás leyendo esa dirección o la pieza no es la E48.
- Consecuencia de diseño que hay que tener clara: **el bloque 0xFA-0xFF es de
  solo lectura**, así que el blob de calibración vive en **0x00-0xF9: 250 bytes
  y ni uno más**. La tabla completa de afinación (84 notas × 4 voces × 16 bits =
  672 bytes) **no cabe** y nunca fue el plan: `tuning.json` vive en el cerebro;
  lo que viaja en la EEPROM son **coeficientes** (por voz: span medido, offset,
  cents/°C, y el valor real de `R_PITCH` si hubo bodge) más cabecera y CRC. Ver
  el Paso 6.
- Escritura: páginas de 8 bytes, ~5 ms por página. Escribir los 250 bytes son
  ~160 ms; no lo hagas byte a byte.

**Temperatura (U13).** Registro `0x00`, 16 bits, resultado de 12 bits
justificado a la izquierda: desplaza 4 a la derecha y multiplica por
**0.0625 °C**.

- Criterio 1: la lectura cae dentro de ±3 °C de la temperatura de la sala.
- Criterio 2, el que de verdad importa: **pon el dedo en U13 y la lectura tiene
  que subir 2-5 °C en unos segundos, y bajar al quitarlo.** Esto es lo que
  distingue «el chip responde» de «el chip está midiendo la placa». Sin este
  segundo criterio, el Paso 7 no vale nada.
- Criterio 3, después de 20 minutos encendida: U13 debe leer **por encima** del
  ambiente. Está pegado a un QFN que disipa; si lee exactamente el ambiente, el
  vertido térmico no está haciendo su trabajo.

### Si falla

| Síntoma | Diagnóstico |
|---|---|
| El escaneo no ve nada | Casi siempre GNDD. Mide `TP15` contra `TP14`: si J2 está bien, deben estar al mismo potencial (unidos en la estrella del módulo 1). Si `TP15` flota ~2.6 V, GNDD no llega |
| El escaneo ve 0x50 y no 0x48 | U13 mal soldado, o su C19. Es el único chip digital que vive en el área analógica: los dos hilos de I²C y su retorno cruzan la frontera como pista |
| El escaneo ve 0x48 y no 0x50 | U14 (SOT-23-5). Ojo con el pin 5: en el símbolo está tipado `no_connect` a propósito |
| Nada responde y SDA se queda abajo | Un esclavo colgado a mitad de transacción. Da 9 pulsos de SCL a mano para liberarlo, o cicla la alimentación |
| Lectura de temperatura absurda (−128, 0) | Registro mal leído: comprueba el desplazamiento de 4 bits, no el sensor |

---

## Paso 3 — SPI: el passthrough de la cadena. **BLOQUEANTE**

Este es el paso que el spec marcó como riesgo abierto desde el principio
(§11.7: «el DCEN con tres chips reales sigue sin probar; bloqueante en
bring-up»). Es la primera vez que el proyecto pone tres AD5686R en cadena
soldada. **Si esto no pasa, no se sigue**: sin cadena no hay control de tono, y
el arreglo no es de firmware, es un re-spin del bloque digital.

### El cableado que se está probando

```
  MOSI (J2.3) ──> U5.SDIN
                  U5.SDO ──> U6.SDIN
                             U6.SDO ──> U7.SDIN
                                        U7.SDO ──> MISO (J2.4)

  SCLK (J2.1) y CS3 (J2.5) van a los tres en paralelo.
```

Tres registros de desplazamiento de 24 bits en serie: **la cadena entera retrasa
72 relojes**.

### El contrato del enlace, tal como queda

- **Modo SPI 1** (CPOL=0, CPHA=1: datos a la entrada en el flanco de bajada de
  SCLK), el mismo que ya usa el AD5686R del módulo 2
  ([`02-midi-cv/README.md`](../../02-midi-cv/README.md)).
- **Reloj ≤ 10 MHz**, con terminación serie en el extremo del cerebro (spec §7).
  Para el bring-up, **empieza a 1 MHz**. La velocidad se sube después del
  Paso 8.
- **CS3 abajo durante los 72 relojes completos, y el flanco de SUBIDA es el que
  carga los tres chips.** Si tu driver levanta CS entre bytes, no funciona nada.
  En `spidev`, eso es `xfer2()` (mantiene CS) y no `xfer()`.
- **El primer word que sale por MOSI acaba en U7, y el último se queda en U5**,
  porque los bits que se mandan primero son los que más lejos viajan. Orden de
  transmisión de una trama de 9 bytes: **`[word para U7][word para U6][word para
  U5]`**. Esto es contrato para el firmware, no una curiosidad del bring-up.

### Formato de trama y comandos

24 bits por chip: `[comando 4b][dirección 4b][datos 16b]`.

| Comando | Qué hace | De dónde sale |
|---|---|---|
| `1000` | **DCEN** — habilita cadena (DB0 = 1) | Verificado en el spec §6 y `bom.csv` contra `ad5686r_5685r_5684r.pdf` p. 21-23 |
| `0111` | **Referencia interna** (DB0 = 1 → apagada) | Ídem, `bom.csv` |
| `0011` | Escribir y actualizar canal | Convención de la familia AD568x — **contrástalo contra el datasheet antes de teclearlo** |
| `0110` | Reset por software | Ídem |
| `0000` | NOP | Ídem |

Dirección de canal: **one-hot** de 4 bits (A=`0001`, B=`0010`, C=`0100`,
D=`1000`) — misma advertencia, contrástalo.

**No hay línea de reset por hardware en esta placa.** El contrato del mazo
(J2) no reserva un pin para eso, así que `RESET` de los tres DAC está atado a
`+3V3_LOC` (inactivo permanente). Si la cadena se queda en un estado raro, las
dos salidas son el comando `0110` o **ciclar la alimentación**.

### El huevo y la gallina del DCEN

Los AD5686R **arrancan en modo standalone, con SDO deshabilitado**. Mientras
U5 no esté en cadena, su SDO está en alta impedancia y U6 no recibe nada
(su SDIN flota). O sea que el DCEN **no puede entrar de una sola vez a los
tres**.

Secuencia a probar, en este orden:

1. **Manda la trama DCEN de 24 bits tres veces**, como tres tramas separadas
   (CS3 baja y sube en cada una). Trama 1: la coge U5, que habilita su SDO.
   Trama 2: U5 desplaza hacia fuera lo que tenía y U6 recibe el DCEN. Trama 3:
   llega a U7. Al terminar, los tres están en cadena.
2. **Manda un NOP de 72 bits** para limpiar: mientras U6 y U7 tenían el SDIN
   flotando, pueden haber latcheado 24 bits de basura. Un NOP en cada uno los
   deja quietos. (`0110`, el reset por software, también sirve y es más
   contundente.)

Si después de esto MISO sigue muerto, **prueba la variante**: una sola trama de
72 bits con el DCEN repetido tres veces, CS3 abajo todo el rato. **Escribe aquí
cuál de las dos funcionó** — es el entregable de este paso, y es lo que el
firmware va a hacer en cada arranque.

### La prueba de passthrough

Con la cadena habilitada:

1. Manda una trama de **72 bits** con un patrón reconocible. Sugerido:

   ```
   00 AA 55   00 0F F0   00 C3 3C
   ^^ el primer nibble de cada word es 0000 = NOP
   ```

   **El patrón va en los 16 bits de datos, nunca en el nibble de comando.** Con
   `0000` delante, los tres chips reciben un NOP: el patrón atraviesa la cadena
   entera sin que ninguno haga nada con él. Un patrón puesto al principio del
   word es un comando de verdad, y el `0110` (reset) o el `0100` (power-down)
   caen ahí por accidente.
2. **Ignora lo que devuelva MISO en esta primera trama**: la cadena escupe lo que
   tuviera dentro, que es basura.
3. **Manda exactamente la misma trama otra vez.** Ahora MISO tiene que devolver,
   bit a bit, los 72 bits de la primera.

**Criterio de éxito: los 72 bits vuelven idénticos.** Nada de «casi».

Repítelo 1000 veces con datos aleatorios (y el nibble de comando siempre a
`0000`) y cuenta los fallos. **Cero fallos a 1 MHz** es el listón. A 10 MHz se
vuelve a medir en el Paso 8.

### Si falla

| Síntoma | Diagnóstico |
|---|---|
| MISO siempre en 0 o siempre en 1 | La cadena no está en modo DCEN, o U7.SDO no llega a J2.4. Mide continuidad de U7 pin 8 al pin 4 de J2 |
| **Los 72 bits vuelven desplazados 1 bit** | Es el **modo SPI**, no la cadena. SDO cambia en un flanco y SDIN muestrea en el otro; prueba el modo 0 y el 2 |
| Vuelven desplazados 24 o 48 bits | Uno de los chips **no** entró en DCEN. Mira otra vez la secuencia de arriba |
| Vuelven bien a veces | Integridad de señal. Baja el reloj a 500 kHz: si se arregla, es el mazo (Paso 8) o falta terminación serie |
| Vuelven bien los primeros 24 y basura el resto | U5 sí, U6 no: soldadura de U6 pin 14 (SDIN) o U5 pin 8 (SDO) |
| Nada, ni siquiera actividad | Antes que nada, mira CS3 con el osciloscopio: que baje una vez y suba una vez por trama, no una vez por byte |

---

## Paso 4 — Apagar las referencias internas y fijar VREF

Ahora que la cadena habla, lo primero que hay que mandarle es **el comando
`0111` con DB0 = 1 a los tres DAC**, en una trama de 72 bits.

**Esto no es una rutina de calibración: es parte del arranque.** Cada vez que la
placa se enciende, las tres referencias internas despiertan encendidas y pelean
con la ADR4525 hasta que el firmware las calla. En el orden de arranque del
cerebro, esto va inmediatamente después del DCEN y antes de escribir un solo
código de tono.

| Medida | Esperado |
|---|---|
| `TP5` (VREF) vs `TP14`, después del `0111` | **2.5000 V ±0.0005 V** (±0.02 %, la precisión inicial de la ADR4525B) |
| Cuánto se movió respecto al Paso 1 | unos pocos mV como mucho |

**El problema de este paso, dicho claro: «VREF no se movió» es ambiguo.** Puede
significar que el comando funcionó y las internas estaban muy cerca de 2.5 V (lo
normal), o que el comando no llegó nunca. Dos formas de salir de la duda:

1. **La prueba del interruptor.** Manda `0111` con DB0 = **0** (referencias
   encendidas), anota VREF; manda DB0 = **1** (apagadas), anota VREF. Cualquier
   diferencia medible confirma que el comando aterriza. Déjalo en apagado.
2. **La prueba que de verdad importa.** Escribe media escala (`0x8000`) en el
   canal A de U5 y mide `TP6` (`CV_PITCH_1`). Tiene que dar **VREF/2 = 1.2500 V
   ±1 mV**. Esto no prueba que la interna esté apagada, pero prueba lo único que
   manda: que el número que gobierna el tono es la tensión que estás midiendo en
   `TP5`.

Aprovecha y barre los cuatro: `0x0000`, `0x4000`, `0x8000`, `0xC000`, `0xFFFF` en
`TP6`-`TP9`. Esperado 0 / 0.6250 / 1.2500 / 1.8750 / 2.5000 V, ±1 mV. **1 LSB =
38.15 µV.**

### Si falla

| Síntoma | Diagnóstico |
|---|---|
| VREF fuera de ±0.5 mV después del `0111` | O la referencia interna no se apagó (repite la prueba del interruptor), o la ADR4525 no es grado B. El grado A (20 ppm/°C) **revienta el presupuesto** y `dac_local_budget.py` lo demuestra |
| VREF se cae al escribir fondo de escala en los cuatro canales | La ADR4525 no aguanta la carga. Los cuatro SSI2130 piden 100 µA cada uno por su pin 23 más las tres redes de `R_SCALE`/`R_LIN`: revisa que C11 (1 µF) esté puesto y que sea el de la salida |
| Un canal no responde y los otros tres sí | Soldadura del pin de salida de ese canal. Cruza con la tabla del Paso 3: los canales de U5 son A=voz 1, B=voz 2, C=voz 3, D=voz 4 |
| Todos los canales dan **el doble** de lo esperado (`0x8000` → 2.5 V) | `GAIN` no está abajo. Debe estar en GNDA: ganancia ×1, salida 0-VREF. En ×2 el fondo de escala son 5 V y `R_PITCH` está dimensionada para 2.5 |

---

## Paso 5 — La apuesta trimless: el span de cada voz

**Este es el paso por el que existe el bring-up.** El diseño no tiene un solo
trimmer: la escala de tono la fijan la ADR4525 y resistencias del 1 %, y el
autoafinado absorbe el resto. La apuesta es que **los cuatro chips reales quepan
en el margen**. Spec §11.2. Aquí se cobra o se pierde.

### La cuenta nominal

```
  2.5 V / 16.5 kΩ (R_PITCH)  =  151.5 µA a fondo de escala
  151.5 µA / 20 µA por octava =  7.576 octavas de span
```

- Objetivo del instrumento: **7 octavas** (C1-C8, las 84 notas de la tesis).
- **Margen de diseño: 7.6 %.** Una voz solo suspende si su constante real de
  µA/octava se desvía más de eso. `R_PITCH` es del 1 %, así que **lo que se está
  midiendo de verdad es la dispersión chip a chip del convertidor exponencial
  del SSI2130** — el número que ningún datasheet garantiza y que decidió el
  diseño entero.
- **Resolución: 1 LSB = 0.139 cents** (7.576 × 1200 / 65535). El suelo de medida
  del autoafinado es 0.5 cents, así que el DAC sobra por 3.6×.

### Cómo se mide

Frecuencímetro (o el contador del cerebro) en **`TUNE_OUT_n`, pines 9-12 de
J2**, con la referencia de masa en **el pin 2 o el 6 de J2 (GNDD)**, no en GNDA:
`TUNE_OUT` sale del 74HC14, que vive en el dominio digital.

**Las cuatro voces se pueden medir a la vez** — son cuatro líneas lógicas
independientes, que es la razón de que el camino de afinación sea digital.

Condiciones:
- **Nada patcheado en los jacks CV-IN** (o los puentes del Paso 0 puestos): con
  el TN a GNDA, `CVIN_n` aporta 0 V.
- Espera **≥ 20 ms** después de cambiar el código antes de medir
  (`autotune_budget.ASENTAMIENTO`).

Barrido: 17 puntos, códigos `0x0000` a `0xFFFF` en pasos de 4096. Cada paso
nominal son 0.473 octavas.

Para cada punto: `octavas(k) = log2( f(k) / f(0) )`.

### Los dos números que salen, y por qué son dos

**A. El span usable**: `log2( f(0xFFFF) / f(0x0000) )`. Es lo que el instrumento
realmente tiene.

**B. El span extrapolado**: ajusta una recta a los puntos desde `0x2000` hasta
`0xFFFF` (que son 7/8 del recorrido, ~6.6 octavas nominales) y multiplica la
pendiente por 65535.

**Van a salir distintos, y la diferencia es información, no error.** En el fondo
de la escala, la corriente fija de `R_LIN` (2.5 V / 499 kΩ = **5.01 µA**) se suma
a la del expo y **levanta el suelo**: la nota más grave sale más aguda de lo que
la recta predice, y A sale por debajo de B. Eso está bien — esos 5 µA son
obligatorios, sin ellos el oscilador no arranca (datasheet pág. 5 y 9).

**Criterio de éxito: B ≥ 7.0 octavas en las cuatro voces.** Anota A también: es
el rango con el que el instrumento va a tocar de verdad, y si A cae por debajo
de 7.0 mientras B lo pasa, el problema no es el chip sino la compresión del
fondo — y entonces el arreglo es **subir `R_LIN`** (menos corriente fija, suelo
más bajo), no bajar `R_PITCH`. Son dos bodges distintos y confundirlos empeora
las cosas.

Con `R_LIN` ve con cuidado: los 499 k son el valor que da el datasheet, y si esa
corriente baja de más el oscilador vuelve a pararse. Sube de un paso E96 cada
vez y vuelve a medir.

Comprueba también la **linealidad**: la desviación de cada punto respecto a la
recta ajustada. El datasheet promete 0.3 % de no conformidad del expo, que son
~3.6 cents; la tabla de 84 notas de `tuning.json` se lo come entero. Si ves
desviaciones de decenas de cents, hay algo roto, no un chip normal.

### El bodge previsto: cambiar SU `R_PITCH`

Si una voz da B < 7.0, **no se descarta el chip todavía**: se cambia su propia
`R_PITCH` (0805, ubicación en la tabla del §0). El span es inversamente
proporcional a `R_PITCH`:

```
  R_nueva  =  16.5 kΩ  ×  B_medido / 7.5
```

| B medido | R_PITCH nueva | E96 más cercano |
|---|---|---|
| 7.0 oct | 15.40 kΩ | **15.4 k** |
| 6.8 oct | 14.96 kΩ | **15.0 k** |
| 6.5 oct | 14.30 kΩ | **14.3 k** |
| 6.0 oct | 13.20 kΩ | **13.3 k** |

**Por qué `R_PITCH` y no `R_SCALE`**: las dos mueven el span, pero `R_SCALE`
(26.7 k, pin 22) fija la corriente de escala del propio convertidor exponencial,
que es contra lo que trabaja la compensación térmica en chip. `R_PITCH` solo
escala la ganancia DAC→corriente y deja el chip como está. Se toca la que no
tiene efectos secundarios.

**Si B sale por ENCIMA de 7.576, no hagas nada.** Más span solo cuesta
resolución, y hay de sobra: incluso a 10 octavas, 1 LSB son 0.183 cents, muy por
debajo del suelo de medida de 0.5. No merece la pena un bodge.

**Anota el valor real de cada `R_PITCH` en el blob de la EEPROM** (Paso 6). Una
placa con un bodge tiene que poder decirlo sola.

### Si falla

| Síntoma | Diagnóstico |
|---|---|
| **Una voz no oscila. Nada en su `TUNE_OUT`** | **Mide `R_LIN` de esa voz primero.** 499 kΩ de VREF al pin 21, ~5 µA. El datasheet es explícito (pág. 9): 0 corriente ahí es 0 frecuencia; el oscilador **se para**. Es el fallo número uno de esta placa y el más fácil de diagnosticar mal |
| Ninguna de las cuatro oscila | Mira VREF (`TP5`) y +5V_LOC (`TP3`) otra vez. Si están bien, el sospechoso es global: `R_LIN` alimentadas todas de la misma red |
| Oscila pero `TUNE_OUT` está sucio o falta | El camino `SQ_n` → `R_SQ` (20 k a +3V3_LOC) → 74HC14. El SQUARE OUT del SSI2130 es **colector abierto**: sin pullup no hay flanco de subida. Mira `SQ_n` con el osciloscopio antes que `TUNE_OUT` |
| `TUNE_OUT` va al doble/mitad de lo esperado | No es fallo de la placa: es el frecuencímetro disparando dos veces por ciclo. Sube el umbral o usa el flanco contrario |
| El span sale bien pero la frecuencia absoluta es rara | `C_TCAP` (3.9 nF). Comprueba que es **C0G/NP0** y no un X7R que se coló: un X7R pierde el 15 % de capacidad con la tensión y deriva con la temperatura como para arruinar el Paso 7 |
| Una voz da span correcto pero se desafina con el CV de otra | Diafonía en las `R_MIX` o en `PWM_CV`, que son buses compartidos. Anótalo y sigue: se resuelve en el Paso 8 |
| Tres voces bien, una fuera por mucho (> 20 %) | Antes de bodgear: mide su `R_SCALE` y su `R_PITCH` en la placa. Un 26.7 k que sea en realidad 267 k explica el 90 % de estos casos |

---

## Paso 5b — El resto del audio: mezclador, PWM y seno

El Paso 5 solo mira frecuencia. Esto mira si la placa **suena**. No es
bloqueante para el autoafinado, pero hacerlo antes ahorra desmontar después.

**Dónde se pincha**: el audio de la voz *n* está en `VOICE_OUT_n`, en el **pad de
punta de `J_OUT{n}`**, no en `TP10`-`TP13`.

**La tierra virtual primero.** Mide `TP10`-`TP13` (`MIXO_n`) contra `TP14`:

- Esperado: **|V| < 5 mV** (el offset del TL074H es 1 mV típ, 4 mV máx).
- Si lees decenas de mV o volts: o el op-amp está muerto, o el SSI2130 está
  metiendo más de los 500 µA que el `R_IV` de 10 k puede convertir sin saturar
  (10 kΩ × 500 µA = 5.0 V, el techo del diseño).

**El mezclador, canal por canal.** Los cuatro CV de mezcla son **compartidos por
las cuatro voces** (U6 canales B/C/D y U7 canal A). Pon tres a cero y sube el
cuarto de `0x0000` a `0xFFFF`:

| CV | DAC | Onda | Qué esperar en `VOICE_OUT_n` |
|---|---|---|---|
| `MIX_SAW` | U6 · B | sierra | rampa **ascendente** (`TIME REVERSE` está a +5 V a propósito) |
| `MIX_TRI` | U6 · C | triangular | |
| `MIX_PULSE` | U6 · D | pulso | ancho gobernado por `PWM_CV` |
| `MIX_SINE` | U7 · A | seno | el shaper del propio chip, vía AUX1 |

- **La amplitud tiene que crecer de forma lineal con el código**: el control del
  mezclador del SSI2130 es lineal, 0-50 µA (2.5 V sobre 49.9 k = **50.1 µA**,
  justo el máximo recomendado).
- **Las cuatro voces con el mismo CV deben dar amplitudes dentro de ~2 %** (el
  1 % de dos resistencias). Un desparejo mayor es una `R_MIX` mal soldada. Ojo:
  **eso es amplitud, no tono** — no afecta al Paso 5.
- El seno: el datasheet promete 0.76 % THD. Si sale un triángulo con las puntas
  redondeadas, la red del shaper (`R_SIN402`, `R_SIN475A/B`, los dos `C_AC` de
  10 µF) tiene algo mal. Es la red más enrevesada de la voz.

**PWM** (spec §11.5, el rango exacto era un riesgo abierto). `PWM_CV` es U6
canal A, **compartido por las cuatro voces**: entra al pin 32 (PWM+) mientras el
triángulo bufferizado entra al 31 (PWM−).

Barre `PWM_CV` de `0x0000` a `0xFFFF` y mide el **ciclo de trabajo** del pulso:

- Anota el código en el que cada voz da **50 %**, y el rango de códigos que da
  entre 5 % y 95 %.
- Criterio: el 50 % cae **holgadamente dentro** del recorrido del DAC y el rango
  útil ocupa una fracción razonable de él. Si el 50 % cae en `0xF000`, el PWM
  utilizable está aplastado contra el fondo de escala y hace falta un divisor en
  `PWM_CV` — anótalo como bodge de rev B.
- **`TUNE_OUT` es el INVERSO de `SQUARE OUT`** (un inversor Schmitt por voz). Si
  mides el ciclo ahí, lo que ves es 100 % − ciclo. Para el frecuencímetro da
  igual; para el PWM no.
- Los cuatro códigos de 50 % **van a ser distintos** entre voces: el offset de DC
  del triángulo de cada chip no es idéntico. Anota los cuatro; es un candidato a
  parámetro por voz en el blob.

---

## Paso 6 — Autoafinado: `tuning.json` y el blob a la EEPROM

Con span verificado en las cuatro voces, el lazo de autoafinado se cierra por
primera vez.

Lo que hace ([`autotune_budget.py`](../../02-midi-cv/autotune_budget.py)): pone
las cuatro voces en la misma nota, cronometra los cuatro `TUNE_OUT` **a la vez**
por conteo recíproco, y corrige la tabla.

| | |
|---|---|
| Notas | 84 (C1-C8) |
| Voces | 4, **en paralelo** |
| Tiempo del barrido completo | **~3.5 s** |
| Precisión de la medida | **0.5 cents** peor caso |
| Suelo de afinación resultante | **0.58 cents** ([`dac_local_budget.py`](../dac_local_budget.py)) |

**Criterios:**

1. El barrido completo **termina** y tarda del orden de 3.5 s. Si tarda 14 s,
   está midiendo las voces de una en una — el paralelismo es medio diseño.
2. Después de escribir `tuning.json`, una segunda pasada debe encontrar
   correcciones **por debajo de 1 cent** en las 84 notas × 4 voces. Si la
   segunda pasada sigue corrigiendo decenas de cents, el lazo no converge.
3. **Las cuatro voces tienen que afinar entre sí.** Toca un unísono a cuatro
   voces y escucha: sin batidos audibles. Es la prueba que ninguna medida
   sustituye, y es la razón de ser del módulo entero.

**El blob a la EEPROM.** 250 bytes disponibles (0x00-0xF9; ver Paso 2). Lo que
tiene que caber, y lo que **no**:

- **Sí**: magic + versión de formato, tipo y revisión de placa, y por voz
  → span medido (A y B), código de 50 % de PWM, valor real de `R_PITCH` si hubo
  bodge, cents/°C del Paso 7, temperatura de la calibración. Más un **CRC**.
- **No**: la tabla de 84 notas. Son 672 bytes y no caben. Vive en el cerebro,
  en `tuning.json`.

La idea: **un cerebro que nunca ha visto esta placa la enchufa, lee la EEPROM,
sabe qué es y arranca razonablemente afinada** antes de correr su primer
barrido. El formato exacto lo fija el firmware; lo que este documento fija es el
presupuesto (250 B), lo que tiene que llevar dentro y que lleve CRC.

Verificación: escribe el blob, **cicla la alimentación**, léelo y compara byte a
byte. Una EEPROM que lee bien sin cortar la corriente no ha demostrado nada.

---

## Paso 7 — Primer registro temperatura ↔ correcciones

No es una prueba de aprobado/suspenso. Es **el punto de partida de la serie** que
va a decir, dentro de seis meses y con una placa más, si un cambio térmico o de
layout sirvió de algo. Sin este primer registro, el resto de la telemetría del
instrumento no tiene contra qué comparar.

**Procedimiento**: placa fría (apagada ≥ 1 h). Enciende y, cada 5 minutos durante
una hora, anota:

- la temperatura de U13 (TMP1075, 0x48),
- las correcciones que el autoafinado aplica a cada voz, en cents,
- la hora.

Una fila por pasada, cuatro columnas de corrección.

**Lo que se espera:**

| Término | Valor previsto | Cómo se reconoce |
|---|---|---|
| Residuo del expo del SSI2130 | 200 ppm/°C típ = **0.35 cents/°C** por voz | cada voz deriva **por su cuenta** |
| Deriva de la ADR4525 (2 ppm/°C típ) | **0.018 cents/°C** sobre 7.6 octavas | las cuatro voces derivan **juntas** |
| Calentamiento propio de la placa | +10 a +20 °C sobre ambiente en 30-40 min | U13 sube y se estabiliza |

Total previsto sobre una excursión de 20 °C: **~7 cents por voz**. Eso es
audible, y es exactamente por lo que el autoafinado existe.

**El diagnóstico que sale gratis del diseño de referencia única:** si las cuatro
voces derivan **juntas**, el culpable es común — VREF, o el tempco de las
`R_SCALE`. Si derivan **cada una por su lado**, es el residuo del expo de cada
chip. Son dos arreglos completamente distintos, y esta gráfica los separa sin
ningún instrumento adicional.

**Banderas rojas:**

- Más de **1 cent/°C** por voz: `C_TCAP` no es C0G, o hay una resistencia con
  tempco malo en la red de VREF.
- Deriva **común** de más de 0.1 cents/°C: la ADR4525 no es grado B, o está
  cargada de más.
- La corrección se mueve sin que la temperatura se mueva: no es térmico. Mira el
  Paso 8.

---

## Paso 8 — Diafonía del mazo y velocidad de reloj

Riesgo abierto del spec (§11.8): en el mismo IDC de 12 pines viajan SPI, I²C y
los cuatro `TUNE_OUT`. Si el reloj SPI se acopla a los `TUNE_OUT`, el
autoafinado mide flancos que no existen y **corrige hacia el lado equivocado**.

**La prueba, que es de estadística y no de osciloscopio:**

1. Con el SPI **en silencio**, mide la misma nota 20 veces en las 4 voces.
   Calcula la desviación típica en cents.
2. Con el SPI **martillando** a 10 MHz de forma continua (NOPs a la cadena),
   repite las 20 medidas.
3. **Criterio: la desviación típica no empeora por encima de 0.5 cents**, que es
   el suelo de medida del autoafinado. Si empeora, el mazo está contaminando la
   medida.

**Si empeora**, en este orden:

1. Baja el reloj SPI (10 → 5 → 1 MHz) y repite. Si a 1 MHz está limpio, el
   contrato del enlace se queda en el reloj más alto que pase.
2. Comprueba la terminación serie en el extremo del cerebro (spec §7).
3. Intercala los GNDD del conector: J2 ya lleva GNDD en los pines 2 y 6, entre
   SCLK/MOSI y CS3/SDA.
4. Si nada basta: cable plano con masa alterna, o separar `TUNE_OUT` a su propio
   mazo — eso ya es cambio de contrato y afecta a los módulos 5, 6 y 7.

Con el osciloscopio, además: mira un flanco de `TUNE_OUT` en el pin 9 de J2 con
el SPI activo. **Debe ser un flanco limpio de 3.3 V** — para eso está el 74HC14:
el flanco de subida del pullup de 20 k es lento (~300 ns contra los ~15 pF de
pista y entrada) y sin el Schmitt cualquier acoplo produce disparos dobles.

**Anota el reloj SPI máximo que pasa esta prueba.** Ese número es el contrato,
no el ≤10 MHz del spec.

---

## 9. Hoja de bring-up (para rellenar en la placa)

```
Placa: módulo 3 VCO ×4, rev ____   EUI-48 (EEPROM 0xFA): ____:____:____:____:____:____
Fecha: __________  Camino de montaje: [ ] A consignado  [ ] B a mano
Ambiente: ____ °C

Paso 0  GNDA↔GNDD abierto  [ ]    Sin cortos en rieles  [ ]    EP aislados  [ ]
Paso 1  +12V ____ mA   −12V ____ mA   TP3 ____ V   TP4 ____ V   TP5 ____ V
Paso 2  0x48 [ ]  0x50 [ ]  T inicial ____ °C   sube con el dedo [ ]
Paso 3  Secuencia DCEN que funcionó: [ ] 3 tramas de 24b  [ ] 1 trama de 72b
        Passthrough 1000/1000 a ____ MHz  [ ]
Paso 4  VREF tras 0111: ______ V   TP6 a 0x8000: ______ V
Paso 5           voz 1     voz 2     voz 3     voz 4
        A (usable) ____ oct  ____ oct  ____ oct  ____ oct
        B (extrap) ____ oct  ____ oct  ____ oct  ____ oct
        R_PITCH    ______    ______    ______    ______   (bodge si ≠ 16.5k)
Paso 5b MIXO ~0 V  [ ][ ][ ][ ]   Código de PWM 50 %: ____ ____ ____ ____
Paso 6  Barrido ____ s   2ª pasada < 1 cent [ ]   Unísono sin batidos [ ]
        Blob escrito y releído tras ciclar [ ]
Paso 7  cents/°C por voz: ____ ____ ____ ____   ¿común o independiente? ______
Paso 8  σ con SPI quieto ____ c   con SPI a 10 MHz ____ c   Reloj adoptado ____ MHz
```

---

## 10. Índice de fallos por síntoma

Atajo para cuando ya estás con el multímetro en la mano.

| Lo que ves | Mira esto primero |
|---|---|
| **Una voz no oscila** | **`R_LIN` de esa voz (499 k, VREF → pin 21)**. Sin sus ~5 µA el oscilador se para |
| Ninguna voz oscila | `TP5` (VREF) y `TP3` (+5V_LOC) |
| VREF fuera de ±0.5 mV | ¿Se mandó el `0111`? ¿La ADR4525 es grado B? |
| Nada digital responde | GNDD. J2 es el único camino que la trae a la placa |
| MISO desplazado 1 bit | Modo SPI, no la cadena |
| MISO desplazado 24 o 48 bits | Un chip no entró en DCEN |
| `MIXO` no está a ~0 V | El TL074H, o el SSI2130 metiendo > 500 µA |
| Las 4 voces sonando una nota al encender | `RSTSEL` no está en GNDA |
| Frecuencia absoluta rara, span bien | `C_TCAP` no es C0G |
| Amplitudes desparejas entre voces | Una `R_MIX`. Es amplitud, no tono |
| Todo bien pero la afinación baila | Jacks CV-IN sin soldar ni puentear: `CVIN_n` flotando |
| Las 4 voces derivan juntas | VREF o los tempco de `R_SCALE` |
| Cada voz deriva por su lado | Residuo del expo de cada chip. Es lo normal |

---

## 11. Lo que este documento no sabe

Todo lo de arriba sale de datasheets y de presupuestos ejecutables. **Ni un solo
número está medido en placa.** Lo que de verdad está abierto:

1. **La dispersión chip a chip del expo del SSI2130.** El margen del 7.6 % del
   Paso 5 es la apuesta entera del diseño trimless y ningún datasheet la
   garantiza. Es lo único que este bring-up no puede predecir.
2. **La secuencia exacta del DCEN** con tres AD5686R reales. Este documento da
   la que debería funcionar y una alternativa; la buena se sabe en el banco.
3. **Cuánto comprime `R_LIN` el fondo de escala.** La diferencia entre el span A
   y el B del Paso 5 es una predicción cualitativa; el número solo sale midiendo.
4. **El formato del blob de la EEPROM.** Aquí solo se fija el presupuesto
   (250 bytes) y qué tiene que llevar. Lo cierra el firmware.
5. **El jitter del sellado de tiempos del cerebro.** `autotune_budget.py` supone
   5 µs y lo llama su parámetro más flojo. Todo el Paso 6 es proporcional a él.
6. **Dónde cae el 50 % de PWM.** Spec §11.5. Se resolvió en el papel
   (comparador 0-VREF, DAC directo); en placa se mide en el Paso 5b.
7. **La velocidad real del enlace.** El ≤10 MHz del spec es un techo de diseño;
   el número que vale sale del Paso 8.

## 12. Para la rev B (abrir como issues con lo que salga del bring-up)

- **Rotular los 15 test points en la serigrafía.** Ahora mismo son 15 pads sin
  nombre y esta tabla es la única forma de encontrarlos. Con los rótulos de los
  pasivos ya ocultos, hay sitio de sobra.
- **Renombrar `MIXO_n`.** El nombre dice «salida de mezcla» y es una tierra
  virtual. Algo como `IV_SUM_n`, y un test point de verdad en `VOICE_OUT_n`.
- **Divisor en `PWM_CV`** si el Paso 5b encuentra el 50 % pegado a un extremo.
- Lo que el Paso 5 obligue a bodgear en `R_PITCH`: si más de una voz lo necesita
  en la misma dirección, el valor nominal está mal y se corrige en el BOM.
