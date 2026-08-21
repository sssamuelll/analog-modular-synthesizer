# Bring-up — PSU v3

Se escribe **antes** de que la placa exista, que es lo que lo hace un test y no
un informe. Cada paso predice un número; `../check_bringup.py` compara lo
medido contra lo predicho y no deja pasar un hueco por un verde.

> Hereda el protocolo de la v2 ([`../../v2/notes/design-notes.md` §4 y §5]) y
> los umbrales de §4.1, que **no cambian**: la topología de regulación es la
> misma. Lo que cambia es todo lo que la rodea, y eso son los pasos 0, 6 y 7.

**Rellena `notes/medidas.csv` en el banco, con el instrumento en la mano.** El
fichero se commitea: la segunda placa se compara con la primera sin discutir de
memoria.

```
python check_bringup.py --plantilla     escribe la hoja de campo vacía
python check_bringup.py                 la juzga
```

Códigos de salida: **0** todo medido y en rango · **1** algo fuera de rango,
la placa no pasa · **2** faltan medidas — ni bien ni mal, no se sabe todavía.

---

## Lo que esta versión estrena, y por qué está arriba del todo

Tres cosas de la v3 no existían en la v2, y dos de ellas son de seguridad:

1. **Los tres TO-220 atornillan su tab contra la pared del chasis**, que es
   acero y está a PE. **Dos de esos tabs están a `VRAW+` y `VRAW−`** — el de
   `U1` y el de `U2`. Si una mica falla, la pared del recinto se pone a ±20 V.
   En la v2 cada regulador tenía su disipador suelto y solo `U2` pedía mica;
   aquí la piden **los tres**, y hay una medida obligatoria antes de enchufar.
2. **El fusible ya no está en la placa.** Vive en el IEC C14 de la pared
   (#130). Antes de nada, comprobar que el que hay puesto es **1,6 A lento** y
   que su portafusible es **cerrado**. Si no lo es, no se enchufa: la placa ya
   no tiene red detrás.
3. **La telemetría se estrena.** Es la primera vez que este instrumento se
   mide a sí mismo, así que el paso 6 no la da por buena: la **contrasta**
   contra el multímetro. Una telemetría que miente es peor que no tenerla.

---

## Paso 0 — Con el equipo desenchufado

**0.1 — Aislamiento de los tres tabs.** Óhmetro en la escala más alta entre
cada tab de TO-220 y la pared del chasis. **> 10 MΩ los tres.** Esta medida es
la que autoriza a enchufar; si alguna sale por debajo, se desmonta y se revisa
mica y pasador antes de seguir.

| | esperado |
|---|---|
| `U1` tab (`VRAW+`) ↔ pared | > 10 MΩ |
| `U2` tab (`VRAW−`) ↔ pared | > 10 MΩ |
| `U3` tab ↔ pared | > 10 MΩ |

**0.2 — Continuidad de tierra.** Óhmetro entre la clavija de tierra del
enchufe, la pared del chasis, el espárrago M4 y el faston `J5`. **Miliohmios o
decenas de miliohmios** (design-notes §13.4). Si falla, no se enchufa.

**0.3 — Inspección visual.** Polaridad de los electrolíticos, orientación de
los reguladores, cortos en la seda.

> **Punto crítico heredado de la v2:** la esquina `+` moldeada de `BR1` contra
> la cruz `+` de la seda (pad 1). Girado 180° cabe igual y cruza el puente en
> el primer semiciclo.

**0.4 — El fusible del IEC.** 1,6 A lento (T), portafusible cerrado. Anotar la
referencia que se puso.

---

## Paso 1 — Solo el transformador, sin la placa

Medir **±17 V** entre cada extremo del secundario y la toma central, tras
`BR1`. Desenchufar antes de seguir.

---

## Paso 2 — Placa sin carga

Con corriente y sin nada colgando de `J2`:

| test point | señal | esperado |
|---|---|---|
| `TP7` | `+13V1` | **+13,1 ± 0,3 V** |
| `TP8` | `−12V9` | **−12,9 ± 0,3 V** |
| `TP3` | `+12V` | +12,00 ± 0,05 V |
| `TP4` | `−12V` | −12,00 ± 0,05 V |
| `TP5` | `+5V` | 5,00 ± 0,25 V |

Si `TP7` o `TP8` están fuera de banda, **no conectar carga**: ajustar `RV2` /
`RV3` (trimmer cerrado, ~10 vueltas) hasta meterlos en rango.

---

## Paso 3 — El rótulo de `J2`, antes de conectar un solo módulo

`J2` tiene **el pin 1 en −12 V y el pin 4 en +12 V**. El rótulo del conector y
el `bom.csv` dijeron lo contrario durante dos versiones (#121), y quien montara
el mazo leyendo esa columna habría metido ±12 V al revés en los seis módulos.

**Medir con el multímetro pin a pin antes de enchufar nada:**

| pin de `J2` | esperado |
|---|---|
| 1 | **−12 V** |
| 2 | GND |
| 3 | GND |
| 4 | **+12 V** |

La seda de la placa ya lleva el rótulo correcto. Esta medida existe para que
nadie se fíe de él sin comprobarlo una vez.

---

## Paso 4 — Carga dummy, y **la puerta que decide la placa**

Colgar **18 Ω / 25 W por riel** de `J2` (≈ 12 V / 0,65 A). Verificar con el
multímetro que ambos rieles dan ~12 V / 0,6 A.

Con la dummy puesta, medir el **valle** de `VRAW+` y `VRAW−` — el piso del
rizado, no el promedio — con osciloscopio DC acoplado y BW limitado a 20 MHz,
punta en `TP1` / `TP2`. En frío y tras 30 min en caliente. Anotar la tensión de
red del momento.

> ### El umbral de aborto son **13,46 V**
>
> Sale de encadenar los dos dropouts **garantizados** (no típicos):
> `12,000 + 0,450 (LT3045) + 0,007 (ballast) + 1,000 (pre-reg) = 13,457 V`.
>
> | | |
> |---|---|
> | valle simulado (red a 207 V, plena carga) | 14,12 V |
> | valle mínimo viable | **13,46 V** |
> | colchón | **0,66 V (4,7 %)** |
>
> - **valle ≥ 13,46 V** → bajar `RV2` hasta dejar margen ≥ 0,2 V. Se espera
>   aterrizar en ~12,9 V en el positivo; el negativo nace con +0,22 V y suele
>   no necesitar toque. **Seguir.**
> - **valle < 13,46 V** → **parar.** Ningún setpoint funciona y ningún giro de
>   trimmer arregla eso. Remedios en `../../v2/notes/design-notes.md` §4.1, por
>   orden de coste: subir el bulk (es THT, no toca el cobre) · aceptar salida
>   por debajo de 12,000 V (decisión de sistema) · revisar la premisa de red.

**Este es el número que compró saltarse la mula.** Hasta aquí solo existía
simulado.

---

## Paso 5 — Rizado

Pico a pico en cada riel, mismas condiciones que el paso 4, punta en `J2`.

Criterio mínimo (spec §10.4): **por debajo del suelo medible del osciloscopio**
con esa BW — no es un umbral numérico fijo. El criterio pleno necesita el LNA
de medida, que es equipo aparte (#58).

---

## Paso 6 — La telemetría, contrastada

**El instrumento se mide a sí mismo por primera vez.** Con la dummy puesta y
todo estable.

**6.1 — Las cuatro direcciones responden.** Barrido I²C desde `J8`:

| dirección | chip | cómo se fija |
|---|---|---|
| `0x40` | `U8` INA226 (+12 V) | A1 y A0 a GND |
| `0x41` | `U9` INA226 (+5 V) | A0 a VDD |
| `0x49` | `U10` ADS1115 | ADDR a VDD |
| `0x48` | `U11` TMP1075 | A2/A1/A0 a GND |

Y **ninguna más**: `0x50` está reservada a la EEPROM de identidad de las otras
placas, y si aparece aquí es que algo está mal atado.

**6.2 — La barrera de masas.** `GNDA` y `GNDD` no comparten ningún nodo (lo
afirma `check_netlist.py` sobre el dibujo; esto lo comprueba en cobre).
Óhmetro entre `J5` y el pin 4 de `J8`: **> 1 MΩ** con el `U12` sin alimentar
por el lado digital.

**6.3 — Contra el multímetro.** Cada lectura de la telemetría contra la medida
directa. **Tolerancia ±1 %**, que es lo que dan los divisores al 0,1 % más el
error del ADC:

| magnitud | quién la lee | contra qué |
|---|---|---|
| `+12V` tensión | `U8` | `TP3` con el multímetro |
| `+12V` corriente | `U8` (shunt de 20 mΩ) | pinza o caída en la dummy |
| `+5V` tensión | `U9` | `TP5` |
| `−12V` tensión | `U10` AIN0 | `TP4` |
| `VRAW+` | `U10` AIN1 | `TP1` |
| `VRAW−` | `U10` AIN2 | `TP2` |
| temperatura del aire | `U11` | termómetro en el recinto |

> **El invariante de los divisores se comprueba aquí, y es la última
> oportunidad.** El 100 k mira siempre al riel y el 20 k a la referencia. Mal
> *dibujado* lo caza `check_netlist.py`; mal *poblado* —un 20 k soldado en la
> huella del 100 k, las dos son 0805 idénticas— **no lo caza nadie hasta esta
> medida**. Si una lectura sale con la escala cambiada, mirar `R21`–`R26`
> contra las dos líneas de seda antes de buscar en otro sitio.

---

## Paso 7 — Térmica, y **con el chasis cerrado**

Aquí es donde la v3 se separa de la v2 y la medida no se puede heredar: allí
cada TO-220 tenía su disipador Fischer al aire; aquí el disipador **es la pared
del recinto**, y el recinto está cerrado.

Dummy a plena carga, **30 min con la caja montada y cerrada**, después medir
cada 5 min hasta que `T_case` se estabilice. Anotar `T_ambiente`.

| punto | esperado | de dónde sale |
|---|---|---|
| `U1` / `U2` / `U3` case | **< 70 °C** | §10.4.1 del datasheet del LM2941 |
| `U4`–`U7` (DFN) | **< 90 °C** | cerámicos de precisión |
| aire del recinto (`U11`) | registro | no hay umbral: es el primer dato |
| pared del chasis junto a los tabs | registro | idem |

La predicción de la spec es **Tj de `U2` = 62 °C** contra los 101 °C que daba
con el disipador individual de la v2. Si `T_case` sale muy por encima, el
sospechoso es el área de ventilación, que **todavía no tiene presupuesto
escrito** (#46).

> Si `T_case` de `U4` vs `U5`, o de `U6` vs `U7`, difieren **más de 5 °C**,
> documentarlo: es la asimetría térmica intra-pareja de las granjas de EP
> (v2 §3.2).

---

## Paso 8 — Cerrar los márgenes

Por cada riel:

```
margen = valle_medido − dropout_max(riel) − setpoint_nominal
```

Aceptar con **margen ≥ 0,2 V**. Si no, bajar el setpoint con `RV2` / `RV3`.
**Suelo bajable garantizado: 12,46 V (positivo) / −12,42 V (negativo)** — más
abajo se agota el margen del LT contra el dropout de la cascada.

---

## Lo que este bring-up NO cubre

- **El número de ruido real.** El criterio pleno del paso 5 necesita el LNA de
  medida, que es un equipo aparte y su propio issue (#58).
- **La resonancia de la bandeja.** El toroide excita a 100 Hz y el primer modo
  de la plancha con él encima cae en 99,6 Hz (#106). Eso se oye, no se mide con
  este protocolo, y no lo arregla la fuente.
- **El comportamiento con los seis módulos reales.** Aquí solo hay dummies
  resistivas: no hay transitorios de carga ni corrientes de retorno de audio.
