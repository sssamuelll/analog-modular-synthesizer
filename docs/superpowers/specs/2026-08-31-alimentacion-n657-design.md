# La alimentación de los N657: un riel de 1,8 V, cuatro lazos y una decisión por chip — propuesta

**Fecha**: 2026-08-31 · **Estado**: **propuesto, pendiente de Samuel** ·
**Cierra**: #252 · **Reabre**: el módulo 1 (rieles), §18 (colocación con veto)

---

## 0. Por qué existe este papel

Al correr el consumo del N657 contra su hoja para el papel de la interfaz
(#251 §4.1) salió un hueco que no era de ese papel: **ningún documento del repo
dice cómo se alimenta este chip**. Verificado por grep sobre `docs/`: cero
apariciones de `0.81`, cero de `VDDCORE`.

Y no es deuda de una propuesta sin firmar. **Tres de los cuatro N657 son
decisiones ya tomadas** —el hub (D1), la Voz (sellada el 26-08) y el mago
(D3')— y las tres necesitan lo mismo. La interfaz solo lo hizo visible.

> **Corrección propia (Principio VII).** #252 se abrió afirmando que hacían
> falta «cuatro reguladores de punto de carga». **Era falso**, e inferido de la
> nota «SMPS external» de las tablas de consumo — que describe cómo ST hizo la
> medición, no lo que el chip exige. La corrección está publicada en el propio
> issue. Este papel parte de la hoja leída, no de aquella inferencia.

---

## 1. Lo que el chip pide, contra la hoja

Todo de **DS14791 Rev 10**, que es la vigente. El Rev 2 con el que se empezó
esta tanda está superado y **renumeró tablas**: ver §3.1.

### 1.1 El conmutado ya viene dentro (§3.4.4, p. 26)

> *«The devices embed an SMPS to provide the VCORE supply. The SMPS generates
> this voltage on `VLXSMPS`, with a total external capacitor of **60 (4× 15) μF**
> (typical). The SMPS requires an **external coil of 0.9 μH** (typical).»*
>
> — DS14791 **Rev 10**, §3.4.4, p. 26.

> **Aviso de revisión.** El Rev 2 con el que se empezó este papel decía **1 µH y
> 88 µF (4× 22)**. **Son cifras muertas**: las de arriba, de Rev 10, son las
> vigentes. El riesgo 7 que este papel declaró ayer —«no se compra ninguna pieza
> hasta cotejarlo»— **se cumplió**, y por eso no hay nada comprado.

Y arranca solo (§3.4.3): al resetear, el conmutado se habilita a 0,81 V, *«hence
the system can start up in any supply configuration»*.

**Lo externo por chip son una bobina y unos cerámicos.** No hay convertidor que
diseñar.

### 1.2 Todo el chip vive a 1,8 V (Tabla 22, pp. 136-137)

| Símbolo | Qué alimenta | Mín | Típ | Máx |
|---|---|---|---|---|
| `VDD18SMPS` | la entrada del conmutado interno | 1,62 | **1,8** | 1,89 |
| `VVDD18PMU` | el analógico del conmutado | 1,62 | **1,8** | 1,89 |
| `VDD18USB` | el PHY de USB | 1,746 | **1,8** | 1,935 |
| `VDD18ADCx` | los ADC (x = 1, 2) | 1,62 | **1,8** | 1,98 |

**No hay riel de 3,3 V en este chip.** Es 1,8 V para todo, y de ahí él se
fabrica su 0,81 V.

### 1.3 Dos configuraciones, y esto es una decisión (§3.4.4)

> *«Two configurations exist, namely SMPS step-down converter supply **on** and
> **off (bypass mode)**. In the latter the step-down converter supply is
> disabled.»*

En bypass, `VDDCORE` se alimenta **desde fuera**. O sea que se puede elegir,
**chip por chip**, entre el conmutado interno y una alimentación externa
silenciosa.

---

## 2. Lo que esto cambia respecto a lo que creíamos ayer

| Creíamos | Es |
|---|---|
| Cuatro convertidores de punto de carga que diseñar | Una bobina de **0,9 µH** y **60 µF** por chip |
| Cuatro conmutadas nuevas y sueltas en el cajón | Cuatro lazos **pequeños y pegados al chip** |
| El problema es el consumo | El consumo sobra (#251 §4.1); el problema es el **riel que falta** y el **ruido** |
| Un subsistema por chip | **Un** riel de 1,8 V para todo el instrumento |

El hueco sigue siendo real —el módulo 1 da +5 V y ±12 V, y **1,8 V no existe**—
pero es mucho más pequeño de lo que #252 decía.

---

## 3. El riel de 1,8 V (D-R1, PROPUESTA)

### 3.1 Cuánta corriente pide — CERRADO contra DS14791 Rev 10

**El hueco está cerrado, y con un número medido por ST en vez de una eficiencia
estimada por mí.**

Con el conmutado **interno** —que es lo que este papel propone— ST publica
`IDDSMPS`: la corriente que el chip pide **en el riel de 1,8 V**, y **ya incluye
el núcleo**. No hay que estimar ningún rendimiento ni sumar `IDDCORE` aparte.

Rev 10 trae las tablas **pareadas**, una versión «SMPS external» y otra «SMPS
internal». **Las que valen aquí son las internas**, condición ITCM/HSI, todos los
periféricos habilitados, VOS high a 800 MHz:

| Símbolo | Qué es | Tabla | Pág. | Típ | Máx (125 °C) |
|---|---|---|---|---|---|
| `IDDSMPS` | entrada del conmutado — **incluye el núcleo** | **39** | 154 | **99,93 mA** | **757,3 mA** |
| `IDDA1V8` | analógico de 1,8 V | **36** | 151 | 2,67 mA | 3,12 mA |
| `IDDA1V8AON` | dominio siempre encendido | **38** | 153 | 0,45 mA | 0,56 mA |
| `IDD` | `VDD`/`VDDIO` | **32** | 147 | 0,27 mA | 0,40 mA |
| | **Total por chip, del riel de 1,8 V** | | | **103,3 mA** | **761,4 mA** |

**Los cuatro chips: 413 mA en típico.** La cota que este papel dio ayer sin el
dato —«≥ 372 mA por conservación de energía»— **era correcta y estaba ajustada**:
el real la supera en un 11 %. La eficiencia implícita del conmutado sale del 93 %.

> **HUECO nuevo (Principio V).** Las cuatro tablas de «SMPS internal» dan **solo
> `Típ` y `Máx` a 125 °C**. **No hay máximo a 85 °C**, que es la temperatura a la
> que este instrumento vive. El salto entre los dos es de 7,4× —de 103 mA a
> 761 mA por chip— así que **interpolar sería inventar**. El riel se dimensiona
> con los dos extremos a la vista y la banda declarada, no con un punto medio
> imaginado.

> **Corrección propia (Principio VII): leí mal las columnas.** La versión
> anterior de esta sección decía «206,7 mA típico a 85 °C» y de ahí sacaba
> 167,4 mW. **Falso.** Las tablas son `Típ` seguido de **varios `Máx`** (a
> 25/85/105/125 °C), no típicos por temperatura: aquel 206,7 era el **máximo a
> 25 °C** de Rev 2. Se ve claro al comparar con la Tabla 39, que tiene `Típ` más
> **un solo** `Máx` etiquetado 125 °C.
>
> El error está propagado a `power_budget.py`, a #251 §4.1 y a la versión previa
> de este papel; los tres se corrigen en esta tanda. Para dejar la referencia:
> la tabla «SMPS external» de `IDDCORE` (**Tabla 33, p. 148**) da **típico
> 172 mA** y máximos de **211 / 423 / 586 / 855 mA** a 25/85/105/125 °C.

### 3.2 Cómo se fabrica, y el precio de cada camino

El instrumento tiene +5 V (de la SMPS de red) y un 3,3 V derivado por buck
(`power_budget.py`, `BUCK_EFICIENCIA = 0.90`).

| Camino | A favor | En contra |
|---|---|---|
| **LDO desde 3,3 V** | **cero conmutación nueva**; §18 no tiene nada que vetar | disipa (3,3−1,8) × 0,413 = **620 mW** en típico |
| LDO desde 5 V | igual de silencioso | disipa **1,32 W** en típico: demasiado calor para el recinto de §3.1 de la fuente |
| Buck a 1,8 V | eficiente | **una conmutada más en el cajón**, y §18 tiene veto |

**Propuesta: LDO desde el 3,3 V que ya existe.** El instrumento acaba de gastar
un papel entero (`fuente-chasis-telemetria`) razonando sobre el calor del
recinto y otro (§18) sobre no meter conmutación; pagar medio vatio de calor por
no añadir un cuarto conmutado es el intercambio que este instrumento ya ha
elegido dos veces.

**Esto reabre el módulo 1**, y con él el lazo de calor de la fuente
(`fuente-chasis-telemetria` §3.1): **620 mW** más dentro del recinto entran en
ese presupuesto térmico, que hoy no los conoce. Y eso es **en típico**: el HUECO
de §3.1 —que no hay máximo a 85 °C— cae entero encima de esta cifra.

---

## 4. Conmutado interno o bypass, chip por chip (D-R2, PROPUESTA)

Aquí está la decisión fina, y §3.4.4 la permite por chip.

| Chip | Propuesta | Por qué |
|---|---|---|
| Hub | **interno** | Ya convive con las ráfagas de DMA del framebuffer; nada suyo es analógico sensible |
| Mago | **interno** | Cámara y NPU; su vecindario es digital |
| Voz | **a decidir** | Es la placa donde **1 mV son 3,6 cents** (voz-total E-1) |
| Interfaz | **a decidir, si D-A1 se firma** | Preamplificadores de micrófono, aún más sensibles que el expo |

**El precio del bypass**, recalculado contra Rev 10: alimentar `VCORE` desde
1,8 V con un LDO disipa (1,8 − 0,81) × 0,172 = **170 mW por chip** — **más que
los 139 mW que el núcleo usa** (`IDDCORE` típico 172 mA × 0,81 V, Tabla 33).
Se paga más calor del que el chip consume, a cambio de quitar un lazo de
conmutación de la placa sensible.

Que ese intercambio valga la pena **no se decide en papel**: depende de cuánto
acopla de verdad un lazo de 1 µH pegado al chip, y eso se mide (§6.3).

---

## 5. Los cuatro lazos y el veto de §18

`psu-v2-goat-design.md` §11.5 dejó el veto escrito para la única conmutada que
hoy existe: *«contenida por diseño, pero §18 tiene veto sobre su colocación»*. Y
`design-notes` §18.1 dice por qué:

> *«El emisor no es el núcleo, es el lazo de carga (…) lo que se acopla a un
> lazo vecino no va con I, va con dI/dt.»*

Aplicado aquí, y es una **buena** noticia: §18 modela el acoplo como un dipolo
magnético con **V ∝ A · dI/dt**, donde `A` es el área del lazo. El lazo de este
conmutado es `VLXSMPS` → bobina → los 88 µF → `VSSSMPS`, todo **pegado al
chip**: `A` es minúscula y, sobre todo, **la fija nuestro layout**. Un
convertidor discreto habría traído su propia geometría; esto no.

El `dI/dt` sí es órdenes de magnitud peor que los 100 Hz para los que §18 se
escribió. **La regla que sale de ahí es de layout, no de topología:** cerrar
cada lazo con el área mínima, sobre su propio plano, y que ninguno de los cuatro
comparta retorno con el analógico.

Los cuatro lazos existen **decida lo que se decida en D-R2**, salvo en los chips
que vayan a bypass.

---

## 6. Verificaciones antes de sellar

1. ~~Bajar DS14791 Rev 4 y leer su Tabla 39~~ — ✅ **HECHO 2026-08-31.** Samuel
   bajó el **Rev 10** (en el árbol como `stm32n657-ds14791-rev10.pdf`). §3.1
   queda cerrada con `IDDSMPS` medido: **103,3 mA por chip, 413 mA los cuatro**.
2. **Cotejar la Tabla 4 de AN5967** («Getting started with hardware development
   for STM32N6»), que trae los componentes externos recomendados del SMPS.
   Rev 10 ya da los valores (0,9 µH y 60 µF), pero **la AN da la pieza y sus
   tolerancias**, que es lo que hace falta para comprar. **Los enlaces que probé
   dan 404: hay que encontrar el bueno.**
3. **El máximo de `IDDSMPS` a 85 °C**, que Rev 10 **no da** (HUECO de §3.1):
   solo publica típico y máximo a 125 °C, y entre ambos hay 7,4×. Es lo que
   decide con cuánto margen se dimensiona el riel, y sale de ST o de medirlo.
3. **El acoplo real del lazo de 1 µH** a una entrada analógica sensible, medido
   en la Discovery. Es lo que decide D-R2 y no se puede razonar en papel.
4. **La pieza del LDO de 1,8 V**, con hoja en el árbol antes de nombrarla (R-M3),
   y su disipación contra el presupuesto térmico de `fuente-chasis-telemetria`
   §3.1.
5. **La bobina de 1 µH y los 88 µF**: pieza, corriente de saturación y sitio, por
   chip.
6. **`power_budget.py`**: hoy refleja el consumo al +5 V con un
   `RENDIMIENTO_DCDC = 0.85` **ESTIMADO** que este papel vuelve obsoleto — el
   camino real es 5 V → buck → 3,3 V → LDO → 1,8 V → SMPS interno → 0,81 V.
   Se reescribe cuando D-R1 se firme.

---

## 7. Lo que este papel NO decide

- **El módulo 1 en sí.** Dice que le hace falta un riel de 1,8 V y cuánto calor
  trae; el rediseño es suyo.
- **Ninguna pieza por nombre** (R-M3).
- **El arranque y el FSBL.** §3.4.3 dice que el chip arranca en cualquier
  configuración; el orden de rieles y el arranque desde XSPI son del papel del
  firmware (#250).
- **Si D-A1 se firma.** Este papel vale con tres chips y con cuatro.

---

## 8. Riesgos

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | El riel de 1,8 V se dimensiona sobre una cota, no sobre la eficiencia real | §6.1 |
| 2 | 558 mW más de calor en un recinto cuyo presupuesto térmico ya era fino | §6.4 contra `fuente-chasis-telemetria` §3.1 |
| 3 | El lazo del conmutado acopla en la Voz o en la interfaz | §6.3 medido; suplente: bypass (D-R2), pagando 205 mW por chip |
| 4 | Cuatro lazos mal cerrados en el layout | Regla de §5 aplicada y verificada en el dibujo, con el veto de §18 |
| 5 | El módulo 1 se reabre con la fuente ya dibujada | Es real; el papel lo declara en vez de descubrirlo en el taller |
| 6 | ~~Trabajamos sobre una revisión superada del datasheet~~ | **CERRADO 2026-08-31**: Rev 10 en el árbol y citado. Confirmó la renumeración (`IDDCORE` era 28, es **33**) y que `IDDSMPS` (39) no existía en Rev 2 |
| 7 | ~~Los valores del SMPS pueden haber cambiado de revisión~~ | **CERRADO 2026-08-31, y habían cambiado**: Rev 10 §3.4.4 dice **0,9 µH y 60 µF (4× 15)**, no los 1 µH y 88 µF de Rev 2. La regla «no se compra nada hasta cotejarlo» **evitó comprar la pieza equivocada** |
| 8 | **El riel se dimensiona sin máximo a temperatura de trabajo** | §6.3. Entre el típico (103 mA/chip) y el máximo a 125 °C (761 mA/chip) hay 7,4×, y el punto de 85 °C no está publicado |
