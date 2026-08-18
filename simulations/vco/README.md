# Simulaciones del VCO — por qué esta carpeta está vacía

Esta carpeta no tiene un `.cir` y no es un olvido. La tabla de
[`simulations/README.md`](../README.md) le asigna al VCO tres cosas: forma de
las ondas, linealidad 1 V/oct y PWM. Aquí está qué pasó con cada una.

## Lo que no se puede simular: el chip

El módulo 3 se construye alrededor del **SSI2130** (Sound Semiconductor), y
**no existe modelo SPICE público** del integrado. No es un problema de
buscarlo mejor: es un ASIC analógico de proveedor único, y su fabricante
publica datasheet, no netlist.

Sin modelo del chip no hay simulación de:

- la forma de las ondas (sierra, triangular, cuadrada, seno) — las genera el
  núcleo del integrado;
- el PWM;
- el mezclador interno.

Escribir un modelo de comportamiento a partir del datasheet sería *inventarse*
el chip y luego validar el diseño contra el invento. Eso no es una comprobación,
es un espejo: pasaría siempre, y pasaría igual de bien con un diseño roto.

## Lo que sí había que calcular, y no era SPICE

La pregunta que de verdad decide este módulo no es la forma de onda: es **la
apuesta trimless** — si los cuatro chips reales caben en el margen de span sin
un solo trimmer (spec §11.2).

El camino de tono de esta placa es un **nodo de suma de corrientes sin un solo
amplificador**: `R_PITCH` (16.5 k) desde el DAC, `R_CVIN` (49.9 k) desde el
jack y `R_LIN` (499 k) desde VREF, las tres contra la entrada del convertidor
exponencial. SPICE ahí no añade nada por encima de la ley de Ohm.

Lo que decide el resultado es una **tolerancia estadística**, y eso se calcula:

> **[`hardware/03-vco/pitch_budget.py`](../../hardware/03-vco/pitch_budget.py)**

Responde: con las tres resistencias del 1 % en su peor caso, cuánto puede
desviarse el convertidor exponencial de un chip antes de que su voz suspenda, y
con qué probabilidad sale limpia una placa de cuatro voces para una dispersión
dada. Corre en el CI como una puerta más.

## Lo que sigue pendiente, y cuándo se puede hacer

| Qué | Por qué no ahora | Cuándo |
|---|---|---|
| Formas de onda, PWM, mezclador | sin modelo del SSI2130 | cuando haya placa: se **mide** en [`bring-up.md` Paso 5b](../../hardware/03-vco/notes/bring-up.md) |
| Modelo de comportamiento del expo | se construiría desde el datasheet y validaría contra sí mismo | cuando las medidas del Paso 5 den los cuatro chips reales: entonces el modelo se ajusta a **datos**, no a la hoja |
| Diafonía entre voces (`R_MIX`, `PWM_CV`) | depende del layout físico y del mazo | Paso 8 del bring-up |

El orden importa: **primero se mide, luego se modela**. Un modelo ajustado a
cuatro chips medidos sirve para predecir el quinto. Un modelo ajustado al
datasheet solo sirve para repetir el datasheet.

## Lo que sí está simulado en el repo

[`simulations/power/`](../power) — rectificación, filtrado y margen de dropout
del módulo 1, con `ngspice.dll` por `ctypes` y autocomprobación del propio
modelo. Ahí SPICE sí es la herramienta correcta: componentes discretos con
modelos estándar y una pregunta (el valle instantáneo con filtro capacitivo)
que no se cierra a mano.
