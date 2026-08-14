# Simulación — Módulo 1: rectificación y filtrado

Responde a una pregunta que no se puede cerrar a mano: con la red al −10 % y el
transformador cargado, **¿la tensión mínima instantánea sobre `C1` se queda por
encima de lo que el 7812 necesita para seguir regulando?**

No se puede a mano porque con filtro de entrada capacitiva la corriente por el
secundario no es senoidal — circula en picos estrechos de 2-3 veces la
continua — así que la caída en la resistencia del devanado es bastante peor que
corriente media × resistencia.

## Cómo correrlo

```
"C:\Program Files\KiCad\10.0\bin\python.exe" run_sim.py
```

Usa `ngspice.dll` (la del simulador interno de KiCad) por `ctypes`, porque KiCad
no trae binario de consola. [`sam17-power.cir`](sam17-power.cir) es el mismo
circuito en formato estándar para repetirlo en LTspice o en un ngspice normal.

`run_sim.py` se autocomprueba antes de dar ningún número: en vacío la salida
tiene que subir al pico menos una caída de diodo, el rizado tiene que escalar
como 1/C, y tiene que quedar por debajo de la cota analítica `I/(f·C)`. Si algo
de eso falla, aborta.

## Resultados

Plena carga de diseño: **450 mA en VRAW+** (300 mA del 7812 **más 150 mA que se
lleva el 7805**, que cuelga del mismo riel) y 300 mA en VRAW−. El 7812 necesita
**≥ 14 V** de entrada instantánea (12 V + 2 V de dropout, peor caso de
datasheet).

| Red | Regulación TR1 | VRAW+ mín | Rizado | Margen | |
|---|---|---|---|---|---|
| 253 V | 8 % | 17.42 V | 0.73 V | +3.42 V | OK |
| 230 V | 8 % | 15.63 V | 0.72 V | +1.63 V | OK |
| **207 V** | **8 %** | **13.85 V** | 0.71 V | **−0.15 V** | **NO REGULA** |
| 253 V | 12 % | 17.75 V | 0.70 V | +3.75 V | OK |
| 230 V | 12 % | 15.91 V | 0.69 V | +1.91 V | OK |
| 207 V | 12 % | 14.08 V | 0.68 V | +0.08 V | OK, pelado |
| 207 V | 20 % | 14.60 V | 0.65 V | +0.60 V | OK |

**Umbral exacto: a 207 V y plena carga de diseño hace falta un transformador con
regulación ≥ 10.7 %.**

### Qué significa "regulación" aquí

Cuánto sube la tensión del secundario en vacío respecto al dato de placa, que
está medido **a plena carga**. Un transformador de 2 A trabajando a 450 mA está
al 22 % de su capacidad, así que da bastante más de 12 V. **El BOM no fija ese
dato**, y de él depende que el diseño pase o no a 207 V — por eso aquí se barre
en vez de suponerlo.

### Con la carga real, no la de diseño

Los 300 mA por riel son el objetivo de diseño de §2, con margen para módulos
futuros. La carga real de la tesis son ~80 mA analógicos por riel:

| Red | Regulación | VRAW+ mín | Margen |
|---|---|---|---|
| 207 V | 8 % | 14.54 V | **+0.54 V** |
| 207 V | 12 % | 14.90 V | +0.90 V |

O sea: **el caso que falla es el objetivo de diseño, no el instrumento tal como
lo describe la tesis.**

## Tres conclusiones que no eran obvias

### 1. Subir el bulk casi no sirve

| C1 = C2 | VRAW+ mín | Rizado | Margen |
|---|---|---|---|
| 4700 µF | 13.85 V | 0.71 V | −0.15 V |
| 6800 µF | 13.98 V | 0.49 V | −0.02 V |
| 10000 µF | 14.07 V | 0.33 V | +0.07 V |

Más del doble de capacidad para ganar 0.22 V. Lo que limita no es el rizado sino
el **nivel medio**: al subir C se estrecha el ángulo de conducción, sube el pico
de corriente por el devanado y empeora la caída en su resistencia. Casi todo lo
que ganas por un lado lo pierdes por el otro.

### 2. Un secundario de 15-0-15 arregla el dropout y crea un problema térmico

| Secundario | VRAW+ mín @207 V | Margen | P 7812 | **Tj 7812** |
|---|---|---|---|---|
| 12-0-12 | 13.85 V | −0.15 V | 1.73 W | 68 °C |
| 15-0-15 | 17.66 V | +3.66 V | 3.14 W | **104 °C** |

Con 15-0-15 sobra margen, pero la unión del 7812 se va a 104-113 °C con el
disipador de 20 °C/W de §6, contra los < 70 °C que esa misma sección fija como
objetivo. **Descartado**: cambia un dropout marginal por un problema térmico.

### 3. Los dos rieles no están igual de cargados

VRAW+ mueve 450 mA y VRAW− solo 300, porque el 7805 cuelga del positivo. El riel
negativo tiene sistemáticamente ~0.5 V más de margen. No estaba dicho en ninguna
nota y afecta a cuál de los dos hay que vigilar.

## Lo que sí sale holgado

- **Rizado en la salida.** Con ~0.7 Vpp de entrada y 60-70 dB de rechazo del
  7812, salen ~0.2-0.7 mV. El objetivo de < 10 mVpp del checklist de bring-up
  (§9) se cumple con dos órdenes de magnitud de sobra. **El riesgo era el
  dropout, nunca el rizado.**
- **Corriente de rizado en C1: 0.72-0.88 A RMS.** Un electrolítico de
  4700 µF/25 V de 16 mm suele estar sobre 1.4-2 A a 105 °C/100 Hz, así que entra
  — pero es un dato que hay que mirar al comprar, no algo que se pueda dar por
  hecho.

## Qué hacer con esto

1. **Desambiguar y acotar el transformador en el BOM** — hecho, ver `bom.csv`.
   `12VAC CT` se lee de dos maneras y solo una funciona.
2. Medir la tensión sobre `C1` en el bring-up con la red baja si se puede, o al
   menos anotar la tensión real en vacío del transformador que se compre.
