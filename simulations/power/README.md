# Simulación — Módulo 1: rectificación, filtrado y pre-regulador

Responde a una pregunta que no se puede cerrar a mano: con la red al −10 % y
el transformador cargado, **¿el valle instantáneo de VRAW se queda por
encima de lo que el pre-regulador necesita para seguir regulando su propia
salida** (13,1 V en `U1` LM2941, −12,9 V en `U2` LM2991 — design-notes.md
§16.8)?

No se puede a mano porque con filtro de entrada capacitiva la corriente por
el secundario no es senoidal — circula en picos estrechos de 2-3 veces la
continua — así que la caída en la resistencia del devanado es bastante peor
que corriente media × resistencia.

> **Hasta el issue #128 este fichero modelaba la v1** (7812, transformador de
> 2 A, dropout de 2 V) — diseño abandonado el 2026-08-17 — y corría como
> puerta en `main` contestando una pregunta que ya nadie hace. El análisis
> histórico de esa versión (barrido de regulación, comparación de
> arquitecturas 78xx vs. LDO, el secundario 15-0-15 descartado por térmica)
> sigue en el historial de git de este archivo y en
> `hardware/01-power-supply/notes/design-notes.md` §16.2-§16.4; no se repite
> aquí para no mantener dos copias de la misma cuenta.

## Cómo correrlo

```
"C:\Program Files\KiCad\10.0\bin\python.exe" run_sim.py
```

Usa `ngspice.dll` (la del simulador interno de KiCad) por `ctypes`, porque
KiCad no trae binario de consola. [`sam17-power.cir`](sam17-power.cir) es el
mismo circuito en formato estándar para repetirlo en LTspice o en un ngspice
normal.

`run_sim.py` se autocomprueba antes de dar ningún número: en vacío la salida
tiene que subir al pico menos una caída de diodo, el rizado tiene que
escalar como 1/C, y tiene que quedar por debajo de la cota analítica
`I/(f·C)`. Si algo de eso falla, aborta.

## El transformador ya no se barre

`12VAC 2A CT` (v1) se leía de dos maneras y el BOM no fijaba su regulación
en vacío — por eso el fichero anterior barría `reg` entre 8, 12 y 20 %. La
v3 usa el **Nuvotem Talema 0120P1-2-012**, y su hoja da los dos extremos de
la recta sin nada que suponer: **13,42 V en vacío, 12 V a 5 A**
(design-notes.md §16.4) → resistencia efectiva de **0,284 Ω** por
semidevanado. Un solo número, no un rango.

## Los pre-reguladores: dropout garantizado, no típico

`U1` (LM2941) y `U2` (LM2991) no entregan 12,000 V — entregan el escalón que
necesita el post-regulador (LT3045×2 / LT3094×2) para tener margen:
**13,1 V** y **−12,9 V** respectivamente (design-notes.md §16.8). El VIN
mínimo de cada uno es esa salida más su dropout garantizado — leído el
2026-08-25 de la hoja primaria, no de un agregador:

| Chip | Dropout MAX a 1 A, temp. completa | Fuente |
|---|---|---|
| LM2941 | 1,0 V | TI SNVS770I, rev. ene-2015, tabla 6.5/6.6 p.5-6 |
| LM2991 | 1,0 V | TI SNVS099I, rev. oct-2016, tabla 6.5 p.5 |

Ninguna hoja garantiza el dropout justo a 650 mA — solo hay fila a 100 mA y
a 1 A — así que se usa la de 1 A como cota conservadora: el dropout crece
con la corriente, y 650 mA < 1 A.

**VIN mínimo real: 14,1 V para `U1`, 13,9 V para `U2`.**

## Resultado

```
carga                              red |  VRAW+ min  margen U1 |  VRAW- min  margen U2 |  Irms C1 |
----------------------------------------------------------------------------------------------------
censo real, con margen (#70)       253 |     19.26V     +5.16V |     19.34V     +5.44V |    0.51A | OK
censo real, con margen (#70)       230 |     17.38V     +3.28V |     17.46V     +3.56V |    0.50A | OK
censo real, con margen (#70)       207 |     15.51V     +1.41V |     15.59V     +1.69V |    0.49A | OK

envolvente de diseno               253 |     17.81V     +3.71V |     18.32V     +4.42V |    1.78A | OK
envolvente de diseno               230 |     15.97V     +1.87V |     16.47V     +2.57V |    1.74A | OK
envolvente de diseno               207 |     14.13V     +0.03V |     14.62V     +0.72V |    1.70A | OK
```

(2026-08-25, salida real del script.)

**Con la carga que el instrumento pide de verdad (censo, 174 mA/riel + 30 mA
de `U3`), el margen es cómodo: +1,41 V en el peor caso.** El problema es
específicamente el "envolvente de diseño" de 650 mA/riel — un techo teórico
que hoy nadie usa: ahí el margen de `U1` cae a **+0,03 V a 207 V**, al filo
del redondeo. La puerta pasa (no hay ningún caso negativo), pero por el
margen más fino posible.

Esto responde el ítem que la spec v2 §7 dejaba abierto: *"Dropout garantizado
de LM2941/LM2991 a 650 mA: no leído aún. Los márgenes de §3 viven o mueren
ahí."* No mueren, pero quedan al borde — si algún módulo futuro empuja algún
riel cerca de los 650 mA de diseño, esta cuenta es la que hay que revisar
primero.

## Lo que este modelo NO cubre

- **La cascada aguas abajo.** Aquí se simula hasta VRAW y el pre-regulador.
  Que `LT3045`/`LT3094` conviertan ese escalón en ±12,000 V lo responde su
  propio margen (design-notes.md §16.8), no este modelo.
- **El valle "crudo" contra el umbral de aborto del bring-up (13,46 V).**
  Esa es una pregunta más abajo en la cadena — antes de cualquier
  regulador — y la responde
  `hardware/01-power-supply/v3/valle_budget.py` **hasta el 2026-09-04**, cuando
  se borró: la fuente v4 no tiene rectificador, así que no hay valle. La
  pregunta equivalente de la v4 la contesta
  [`hardware/01-power-supply/v4/margen_budget.py`](../../hardware/01-power-supply/v4/margen_budget.py),
  sobre una cadena de continua y sin 100 Hz que integrar. La discrepancia con
  design-notes.md §16.5 (issue #141) se cierra con el toroide, no aquí.
- **El arranque, el ruido y la deriva térmica del devanado** — ver el
  docstring de `run_sim.py`.
