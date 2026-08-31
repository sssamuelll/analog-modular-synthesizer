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

Todo de **DS14791 Rev 2**.

### 1.1 El conmutado ya viene dentro (§3.4.4, p. 22)

> *«The devices embed an SMPS to provide the VCORE supply. The SMPS generates
> this voltage on `VLXSMPS`, with a total external capacitor of **88 (4× 22) μF**
> typical. The SMPS requires an **external coil of 1 μH** typical.»*

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
| Cuatro convertidores de punto de carga que diseñar | Una bobina de 1 µH y 88 µF por chip |
| Cuatro conmutadas nuevas y sueltas en el cajón | Cuatro lazos **pequeños y pegados al chip** |
| El problema es el consumo | El consumo sobra (#251 §4.1); el problema es el **riel que falta** y el **ruido** |
| Un subsistema por chip | **Un** riel de 1,8 V para todo el instrumento |

El hueco sigue siendo real —el módulo 1 da +5 V y ±12 V, y **1,8 V no existe**—
pero es mucho más pequeño de lo que #252 decía.

---

## 3. El riel de 1,8 V (D-R1, PROPUESTA)

### 3.1 Cuánta corriente pide, acotada y no inventada

El conmutado interno entrega **167,4 mW** por chip a `VCORE` (#251 §4.1: 206,7 mA
× 0,81 V, típico a 85 °C).

> **HUECO (Principio V), y con dirección exacta.** La eficiencia del conmutado
> interno **no aparece en el DS14791 Rev 2 que tenemos** — y buscando por qué,
> resulta que **la pregunta estaba mal planteada**: no hace falta la eficiencia.
>
> **ST publica `IDDSMPS` directamente**, o sea la corriente de entrada medida en
> `VDDSMPS`. Lo confirmó un ingeniero de ST (RomainR) en el hilo *«Understanding
> Power Consumption using SMPS on STM32N6»* de su comunidad:
>
> > *«In internal SMPS, IDDSMPS therefore depends on the IDDCore including the
> > internal SMPS efficiency, the voltage ratio (VDDSMPS/VDDCore), and the
> > different external losses. If you need to size the external regulator of the
> > VDDSMPS, you should consider IDDSMPS which corresponds to the VDDCore
> > condition of table 34.»*
>
> Y nombra las tablas: **`IDDSMPS` es la Tabla 39 e `IDDCORE` la Tabla 34, en
> DS14791 Rev 4.** En **nuestra Rev 2** `IDDCORE` es la Tabla 28 y **`IDDSMPS`
> no existe: verificado, cero apariciones en las 244 páginas.**
>
> **El hueco se cierra con una descarga, no con un cálculo.** Y hasta que se
> baje, la corriente del riel solo se acota.

Lo que sí se puede afirmar sin suponer nada, por conservación de energía: el
conmutado **no puede consumir menos potencia de la que entrega**. Con
rendimiento del 100 % —imposible, pero es la cota— serían

    167,4 mW / 1,8 V = 93 mA por chip

o sea **≥ 372 mA para los cuatro**, más `VDDA1V8`, `VDD18USB` y `VDD18ADC`. El
número real está por encima, y cuánto depende de un dato que hay que pedir a ST
o medir. **Se dimensiona con margen, no con la cota.**

### 3.2 Cómo se fabrica, y el precio de cada camino

El instrumento tiene +5 V (de la SMPS de red) y un 3,3 V derivado por buck
(`power_budget.py`, `BUCK_EFICIENCIA = 0.90`).

| Camino | A favor | En contra |
|---|---|---|
| **LDO desde 3,3 V** | **cero conmutación nueva**; §18 no tiene nada que vetar | disipa ≥ (3,3−1,8) × 0,372 = **558 mW** |
| LDO desde 5 V | igual de silencioso | disipa ≥ 1,19 W: demasiado calor para el recinto de §3.1 de la fuente |
| Buck a 1,8 V | eficiente | **una conmutada más en el cajón**, y §18 tiene veto |

**Propuesta: LDO desde el 3,3 V que ya existe.** El instrumento acaba de gastar
un papel entero (`fuente-chasis-telemetria`) razonando sobre el calor del
recinto y otro (§18) sobre no meter conmutación; pagar medio vatio de calor por
no añadir un cuarto conmutado es el intercambio que este instrumento ya ha
elegido dos veces.

**Esto reabre el módulo 1**, y con él el lazo de calor de la fuente
(`fuente-chasis-telemetria` §3.1): 558 mW más dentro del recinto entran en ese
presupuesto térmico, que hoy no los conoce.

---

## 4. Conmutado interno o bypass, chip por chip (D-R2, PROPUESTA)

Aquí está la decisión fina, y §3.4.4 la permite por chip.

| Chip | Propuesta | Por qué |
|---|---|---|
| Hub | **interno** | Ya convive con las ráfagas de DMA del framebuffer; nada suyo es analógico sensible |
| Mago | **interno** | Cámara y NPU; su vecindario es digital |
| Voz | **a decidir** | Es la placa donde **1 mV son 3,6 cents** (voz-total E-1) |
| Interfaz | **a decidir, si D-A1 se firma** | Preamplificadores de micrófono, aún más sensibles que el expo |

**El precio del bypass**, calculado: alimentar `VCORE` desde 1,8 V con un LDO
disipa (1,8 − 0,81) × 0,207 = **205 mW por chip** — **más que los 167 mW que el
chip usa**. Se paga más del doble en calor a cambio de quitar un lazo de
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

1. **Bajar DS14791 Rev 4 y leer su Tabla 39 (`IDDSMPS`)** — cierra el HUECO de
   §3.1 con un número medido en vez de una eficiencia estimada. Nuestro Rev 2 no
   la trae. **Prerrequisito de D-R1**: es lo que dimensiona el riel de 1,8 V.
2. **Cotejar la Tabla 4 de AN5967** («Getting started with hardware development
   for STM32N6») — trae los componentes externos recomendados del SMPS, que es
   lo que fija la pieza de la bobina y los cerámicos (§6.5).
3. **La corriente máxima que el conmutado interno puede dar**, tampoco leída en
   Rev 2. Decide si un solo chip puede con su carga en los picos.
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
| 6 | **Trabajamos sobre una revisión superada del datasheet** | §6.1. Nuestro DS14791 es **Rev 2**; ST va por **Rev 4**, con tablas renumeradas (`IDDCORE` pasa de la 28 a la 34) y al menos una tabla nueva (`IDDSMPS`, la 39) |
| 7 | **Los valores del SMPS externo pueden haber cambiado de revisión** | §6.2. Rev 2 dice **1 µH y 88 µF (4× 22)**; una fuente de ST posterior cita **0,9 µH y 60 µF (4× 15)**. Si el segundo es el vigente, §1.1 y §6.5 de este papel llevan cifras muertas. **No se compra ninguna pieza hasta cotejarlo** |
