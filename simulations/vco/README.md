# Simulaciones del VCO — qué se simula y qué no

> **Actualización 2026-08-21.** Esta carpeta ya no está vacía: tiene
> [`iv_stage.py`](iv_stage.py). El argumento de abajo **no cambia** — el
> SSI2130 sigue sin simularse y por la misma razón. Lo que se simula es la
> etapa que va DESPUÉS del chip, y de ella sí hay números publicados. Ver la
> sección 5 al final.

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

---

## 5. La etapa I/V sí se simula — y encontró algo

[`iv_stage.py`](iv_stage.py), añadido el 2026-08-21.

**Por qué esta sí y el chip no.** Lo único que hace falta del SSI2130 es lo que
su datasheet **declara** del pin 25: que MIX OUT es una salida de **corriente**.
Una fuente de corriente no es un invento del chip, es la interfaz publicada.
Todo lo demás del lazo —`R_IV` de 10 k, el TL074H, el cable de patcheo— tiene
números de fuente primaria. La frontera es esa: **se modela la interfaz que el
fabricante publica, nunca el interior que no publica.**

**El macromodelo del TL074H** es de dos polos, construido con GBW 5.25 MHz,
AOL 125 dB y Zo 125 Ω del datasheet, y **calibrado** resolviendo sus dos
parámetros libres contra dos anclas publicadas a la vez: el cruce por 0 dB en
5.25 MHz y el margen de fase en 56° (G=+1, RL=10 k, CL=20 pF). No es el modelo
de TI; uno del fabricante sería mejor y es la mejora natural.

**La capacidad del nodo `MIXO_n` no está publicada** —ni la de entrada del
TL074H ni la de salida del pin 25 del SSI2130— así que se **barre** de 5 a
100 pF, igual que `run_sim.py` barre la regulación del transformador que el BOM
no fija.

**Lo que encontró:** la transimpedancia **no lleva condensador de
realimentación** sobre `R_IV`, y la salida del operacional va **directa a la
punta del jack** sin resistencia serie. Las 20 combinaciones del barrido salen
fuera de criterio y 15 de ellas oscilan. Con 33 pF de realimentación y 220 Ω en
serie, las 20 quedan limpias y el polo del I/V se va a 482 kHz — muy por encima
de la banda de audio, así que no cuesta nada musicalmente.

Es exactamente la clase de fallo que ningún gate del repo veía: no lo caza el
ERC, no lo caza el DRC, no lo caza el netlist. Se oye.

**Su mutación** (`python iv_stage.py --mutar`, Principio VIII) corre el barrido
con el circuito corregido y exige que el veredicto se dé la vuelta: 20 de 20
fuera de criterio sin compensar, 0 de 20 con el arreglo. Si no distingue, el
gate no vigila lo que dice vigilar.
