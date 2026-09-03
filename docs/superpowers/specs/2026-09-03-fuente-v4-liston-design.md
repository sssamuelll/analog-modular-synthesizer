# Fuente v4 — el listón de la PSU3, seis módulos encapsulados y la cascada intacta — propuesta

**Fecha**: 2026-09-03 · **Estado**: **propuesto, pendiente de junta y de firma** ·
**Listón firmado**: 2026-09-03 («firmo el listón», Samuel) ·
**Cierra**: #169 (rieles de la fila de abajo), #151 (dueño del +5 V) ·
**Mata por desaparición del sujeto**: #141, #280, #106, #56, #57 ·
**Reabre**: `design-notes` §18 (zumbido, ahora en kHz), la spec del chasis (§3.1
térmica, §3.3 geometría), `consumo_total_budget.py`, `power_budget.py`

---

## 0. Por qué existe este papel

La v3 está dibujada, ruteada y con DRC en cero, y **no se pide**. No porque le
falte una puerta: porque el listón cambió.

El 2026-09-03 salieron tres cosas a la vez, y las tres tienen número:

1. **El instrumento es digital y su +5 V ya está en rojo.** `power_budget.py`
   (módulo 2) da un techo de **2,82 A** para el +5 V digital —la IRM-15-5 de 3 A
   menos margen— y con cuatro N657 a máximo más el host USB las cargas duras
   solas son **2,895 A**. Con la cadena de LEDs al tope del #104 son **4,935 A**.
   Y eso sin la NPU, que no tiene cifra en DS14791.
2. **La fila de abajo es rack de verdad (#169) y no tiene corriente.**
   `consumo_total_budget.py` deja **160 mA por riel** para invitados. Un solo
   Disting EX come 229 mA en +12 V (expert-sleepers.co.uk, leído 2026-09-03).
3. **Samuel fijó el listón: «a la altura de la A-100PSU3 o superior».** La PSU3
   da +12 V/2000 mA, −12 V/1200 mA, +5 V/4000 mA (doepfer.de/a100_man/a100t_e.htm,
   leído 2026-09-03). La v3 da 650/650 en ±12 V —**exactamente lo que daba la
   primera fuente de Doepfer, la A-100NT12, retirada en el año 2000**— y ningún
   +5 V de rack.

La topología lineal de red de la v3 —toroide de 120 VA, puente, 9400 µF— no
puede crecer hasta ahí sin volverse un ladrillo de dos kilos, y el propio §18 de
la v1 midió que **el mayor emisor de zumbido de la caja es el mazo del
secundario del toroide** (~40 cm², ~29 µV inducidos). Este papel cambia la
entrada de red por módulos AC-DC encapsulados y **deja la cascada de regulación
exactamente como está**, porque es de la cascada de donde sale el 0,8 µVrms, no
del toroide.

> **Sobre la regla «nunca con una v4».** La v3 se la impuso a sí misma para que
> lo indeciso saliera con huella y `DNP` en vez de con otra versión de papel.
> Esto no es indecisión: es un listón nuevo firmado por Samuel. La regla se
> levanta con esa firma y **vuelve a regir desde aquí**: lo que este papel no
> decida sale con huella y `DNP`, nunca con una v5.

---

## 1. El listón (D-F1, FIRMADO 2026-09-03)

| Riel | A-100PSU3 | SAM17 v4 | Dominio de masa |
|---|---|---|---|
| **±12 V ultra** — Voz, VCF, VCA, envolventes, bahía | no tiene | **650 mA/riel, 0,8 µVrms**, cascada intacta | `GNDA` |
| **+12 V invitados** — fila de abajo, 104 HP | 2,0 A | **3,8 A** | `GNDA` (retorno propio, §4.1) |
| **−12 V invitados** | 1,2 A | **2,5 A** | ídem |
| **+5 V invitados** | 4,0 A | **4,0 A** | ídem |
| **+5 V digital** — N657 ×4, pantalla, LEDs, host USB | (dentro de los 4 A) | **8,0 A** | `GNDD` |
| **1,8 V** de los N657 | — | del 3,3 V, aguas abajo del +5 V digital; **no se decide aquí** (§4.5) | `GNDD` |

Dos cosas que el listón fija y que no son obvias:

**El instrumento y los invitados no se prestan un miliamperio.** El riel ultra
sigue en 650 mA con su 30 % de margen (`consumo_total_budget.py`: peor riel
340,2 mA → OK), y ya no tiene que reservar nada para la fila de abajo. El rack
tiene lo suyo. Un módulo ajeno con su conmutado no toca el riel de 0,8 µV, y
la NPU del mago no deja sin corriente a un delay de BBD.

**Lo digital del instrumento no carga los ±12 V.** Carga el +5 V digital, y de
ahí baja a 3,3 y a 1,8. Por eso el riel que más crece contra la PSU3 es ese:
**8 A contra 4**, y aun así la cadena de LEDs a blanco pleno (**9,60 A**,
`power_budget.py`) no cabe. El tope por firmware se queda, ahora con cifra: en
el peor caso quedan 8,0 − 2,895 = **5,1 A** para la cadena, el 53 % del bruto.

---

## 2. Qué se va y qué se queda respecto de la v3

| | v3 | v4 | por qué |
|---|---|---|---|
| **Entrada de red** | toroide Talema 120 VA + `BR1` + 9400 µF | **seis módulos Mean Well IRM** (§3) | el listón; y el toroide era el emisor mayor (§0) |
| **Cascada ±12 V** | LM2941/LM2991 → LT3045 ×2 / LT3094 ×2 | **la misma, sin tocar** | el 0,8 µVrms sale de ahí |
| **Lo que ve la cascada** | VRAW ±20,54 V en vacío, ±15,70 V a 650 mA, rizado de 100 Hz | **±15 V DC ±2,5 %, rizado de conmutación ≤ 200 mVp-p** | §4.2 |
| **El valle de VRAW** | el número del que dependía todo (umbral 13,46 V) | **no existe** | no hay rectificador |
| **`TR1` con fusible térmico** | condición de compra (#118) | **no hay `TR1`** | los 642 W de un corto del secundario ya no tienen dónde ocurrir |
| **Crowbar** | ninguno | ninguno | igual que #118; los IRM traen OVP propio (§5) |
| **Fusible de red** | 1,6 A T en el IEC de la pared (#130) | en el IEC; **el valor se recalcula** (§5) | seis arranques en frío en vez de un toroide |
| **Disipación** | tres TO-220 contra la pared | los mismos tres contra la pared, **con la mitad de calor** | entran a 15 V, no a 20 |
| **Chasis** | acero, cerrado, dimensionado para un toroide Ø93 × 46 | acero, cerrado, **sin toroide** | §6 y enmienda al case |
| **Telemetría** | 5 chips, mide el valle | 5 chips (+2 opcionales, §7), mide los ±15 V y los rieles de rack | |
| **+5 V digital** | IRM-15-5 «montada fuera de esta placa» (spec v2 §7), 3 A | **IRM-45-5 en la placa de red, 8 A** | cierra #151: tiene dueño |
| **Fila de abajo** | 160 mA/riel prestados | **3,8 / 2,5 / 4,0 A propios** por un bus board de invitados | #169 |
| **Placas** | una, 200 × 150 | **dos** + el bus board de invitados | §8 |

---

## 3. Los seis módulos, contra la hoja

Las cuatro hojas están en el árbol desde esta tanda:
`docs/reference/datasheets/meanwell-irm-{15,20,30,45}-spec-*.pdf` (las de 15,
20 y 45 W fechadas 2025-11-21; la de 30 W, 2026-04-03). Todo lo de abajo es de
esas tablas de especificación (p. 2 de cada una), salvo donde se marca.

| Ref. | Módulo | Riel | I nominal | Rizado máx. (20 MHz) | Rendimiento | L × W × H | Peso |
|---|---|---|---|---|---|---|---|
| `PS1` | IRM-20-15 | +15 V → `U1` | 1,4 A | 200 mVp-p | 84 % | 52,4 × 27,2 × 24 | 50 g |
| `PS2` | IRM-20-15 | −15 V → `U2` (apilada, §4.2) | 1,4 A | 200 mVp-p | 84 % | 52,4 × 27,2 × 24 | 50 g |
| `PS3` | IRM-45-12 | +12 V invitados | 3,8 A | 150 mVp-p | 87,5 % (†) | 87 × 52 × 29,5 | 195 g |
| `PS4` | IRM-30-12 | −12 V invitados (apilada) | 2,5 A | 150 mVp-p | 88 % | 69,5 × 39 × 24 | 94 g |
| `PS5` | IRM-20-5 | +5 V invitados | 4,0 A | 200 mVp-p | 79 % | 52,4 × 27,2 × 24 | 50 g |
| `PS6` | IRM-45-5 | +5 V digital | 8,0 A | **80 mVp-p** | 83,5 % (†) | 87 × 52 × 29,5 | 195 g |

(†) La extracción de texto de la tabla de la IRM-45 cruza las dos primeras
columnas de rendimiento (aparecen «87.5% 83.5%» para 5 V y 12 V). Se toma el
**menor de los dos para cada uno** hasta leer la tabla con los ojos (§12.1); en
la térmica de §6 se usa 83,5 % para ambos, que es el lado seguro.

Lo que comparten los seis, de las mismas hojas:

- **Clase II sin pin de tierra** («no FG pin»), aislamiento I/P-O/P **4,2 kVac**
  (IRM-30 p. 2). Las salidas son flotantes: por eso se pueden apilar (§4.2).
- **EMI Clase B conducida y radiada «sin componentes adicionales»** (IRM-30 p. 2,
  EN55032). Eso es lo que dice la hoja del módulo solo; la nota 5 de la misma
  hoja avisa de que **el equipo final tiene que re-verificarlo**. Aquí el equipo
  final tiene seis, y un riel de 0,8 µV al lado: §4.2 y §12.3.
- **Corriente de fuga < 0,25 mA a 277 Vac** (IRM-15 e IRM-20 p. 2). Con seis
  módulos y todas las salidas referidas a PE por la estrella (§13 de la v1), la
  suma de máximos es 1,5 mA: §5 y §12.5.
- **Protecciones propias**: corto en *hiccup* con recuperación automática,
  sobrecarga (IRM-30: 105–160 %; IRM-20/45: 115–160 %; IRM-15: 115–190 %),
  sobretensión «shut off, clamping by zener diode».
- **−30 a +85 °C con curva de derating** (p. 3 de cada hoja) — **la curva no
  está leída**; es el HUECO que manda en §6.
- **Arranque en frío**: la IRM-30 declara **4 A a 230 Vac** de inrush típico
  (p. 2). Las otras tres hojas lo tienen en la misma fila y no se extrajo:
  §12.4. Seis arranques a la vez son el trabajo del fusible (§5).
- **Consumo sin carga** < 0,1 W (IRM-15/20) y < 0,15 W (IRM-45), de la
  descripción de p. 1.
- **Lo que ninguna hoja dice: la frecuencia de conmutación.** El rizado está
  medido a 20 MHz de ancho de banda «con un par trenzado de 12" terminado en
  0,1 µF ‖ 47 µF» (nota 2), pero la frecuencia fundamental no se publica. Sin
  ella el filtro LC de §4.2 se diseña **para el peor caso del rango** o se mide
  en el banco: §12.2.

Los seis pesan **634 g**. El toroide de la v3 pesaba 1,20 kg solo, y ninguno de
los seis pasa de **29,5 mm de alto**; el toroide medía 46 más 4 de holgura.

---

## 4. Arquitectura

### 4.1 Tres dominios de masa y un punto

```
             PE (espárrago M4, §13 v1)
              │
          ★ estrella  ── chasis (puente duro, único)
         /    │     \
     GNDA   GNDD    retorno del rack
      │      │         │
  cascada  PS6 →   PS3 / PS4 / PS5 → bus board de invitados
  (PS1/PS2) módulo 2      │
      │                   └── los módulos ajenos, y sus jacks
  J2 → bus board del instrumento
```

- **`GNDA`**: la cascada, el bus board del instrumento, la bahía. Como hoy.
- **`GNDD`**: el +5 V digital de `PS6` hacia el módulo 2. Como hoy la IRM-15-5,
  pero ahora vive en la placa de red y no «fuera de esta placa».
- **El retorno del rack** es `GNDA` eléctricamente —los jacks de la bahía lo
  unen igual— pero **llega a la estrella por su propio conductor**, y ninguna
  otra corriente lo comparte. El motivo es de afinación, no de ruido: el bus
  board del instrumento mide **1,21 cents** de error de masa a 1 V/oct
  (`ground_budget.py`), y un invitado puede devolver 3,8 A. Si esos amperios
  cruzaran el plano del bus board del instrumento por el camino de los jacks,
  cada milivoltio serían 1,2 cents. La regla: el retorno del rack va **grueso y
  directo** a la estrella, para que el camino por los cables de patch —contactos
  de jack en serie, hilos finos— sea el de más impedancia con diferencia.
  **Cuánto** se cuela por los jacks se calcula (enmienda a `ground_budget.py`,
  §10) y se mide (§9, bring-up).
- **Cada salida de IRM vuelve a la estrella por su conductor.** La fuga de
  50 Hz de cada módulo (< 0,25 mA, §3) sale por su borne negativo hacia PE; si
  ese borne va directo a la estrella, la fuga no cruza ningún plano de señal.
  Ésta es la regla de §18 traducida a los IRM: no es el núcleo, es **por dónde
  vuelve la corriente**.

§13 de la v1 **no cambia**: puente duro chasis-GND en un punto, sin *ground
lift*, PE sin pista en la PCB. Que los módulos sean Clase II no lo cambia: el
recinto es de acero, contiene 230 V en pistas, y va a PE.

### 4.2 El riel ultra: ±15 V DC a la misma cascada

`PS1` da +15 V respecto de su negativo; `PS2` da +15 V respecto del suyo. Se
apilan: el negativo de `PS1` y el **positivo** de `PS2` van juntos a la estrella
como `GNDA`; el positivo de `PS1` es +15 V y el negativo de `PS2` es −15 V.
Legítimo porque cada salida es flotante y aislada de red a 4,2 kVac (§3).

**Margen de entrada de los pre-reguladores**, contra las hojas ya leídas en la
v2 (`v2/notes/design-notes.md` §1.1 y §1.2: dropout **máximo garantizado 1,0 V
a 1 A** en los dos):

```
+15 V − 2,5 % (tolerancia de hoja, IRM-20 p. 2)   = 14,625 V
setpoint de U1                                     = 13,1 V
dropout máx. de LM2941 a 1 A                       = 1,0 V     → 14,1 V necesarios
margen a 1 A                                       = +0,53 V
margen a 650 mA                                    > +0,53 V   (el dropout baja con la corriente, misma hoja)

−15 V + 2,5 %                                      = −14,625 V
setpoint de U2                                     = −12,9 V
dropout máx. de LM2991 a 1 A                       = 1,0 V     → −13,9 V necesarios
margen a 1 A                                       = +0,73 V
```

A eso hay que restarle la caída DC del filtro LC (§4.2, `DCR × I`) y **el
rizado**: los 200 mVp-p de hoja son ±0,1 V alrededor del nominal. Con ambos
descontados el margen a 650 mA sigue positivo; **el número exacto lo pone
`margen_budget.py`** (§9), que sustituye a `valle_budget.py` con un problema
mucho más pequeño: ya no hay 100 Hz que integrar, hay una tolerancia y un
rizado.

Los LT3045/LT3094 no ven nada de esto: siguen entrando a ±13,1/−12,9 V desde
los pre-reguladores, muy por debajo de sus ±22 V de máximo absoluto (v2 §1.3 y
§1.4).

**El camino del rizado.** Es el cambio de naturaleza del problema: la v3
atenuaba **voltios a 100 Hz**; la v4 atenúa **200 mV a decenas o cientos de
kHz**. Tres etapas en serie:

1. **Filtro LC a la salida de cada IRM** —el que la v3 ya diseñó para la
   IRM-15-5 (commit `fec315e`: «el filtro de la SMPS entra en la placa») se
   repite en los seis, dimensionado para la frecuencia del peor caso mientras
   la real no esté medida (§12.2).
2. **El PSRR del pre-regulador** a esa frecuencia.
3. **El PSRR del LT3045/LT3094** a esa frecuencia, que es la etapa que decide.

Las tres cifras salen de las curvas de las hojas (LM2941/LM2991 y ADI Rev. D /
Rev. B, ya en `v2/notes`), y **el producto tiene que dejar el rizado residual
por debajo de la cota de ruido del riel**. Ese cálculo es §12.3 y no se presume:
la v2 ya escribió que el 0,8 µVrms «no se presume hasta medir con el LNA», y
esto lo hace más cierto, no menos.

**La distancia sigue siendo el filtro más barato.** La v3 exige ≥ 80 mm entre
el lazo rectificador y la isla ultra y ≥ 30 mm hasta la isla de telemetría
(`revisar_diagonal()`). La v4 hereda las dos reglas con el sujeto cambiado:
**desde el módulo IRM más cercano**, y con seis módulos y una placa de 200 × 150
eso no cabe. Es la razón principal de que sean dos placas (§8).

### 4.3 Los rieles de invitados

`PS3` (+12 V, 3,8 A) y `PS4` (−12 V, 2,5 A) apiladas como en §4.2; `PS5` (+5 V,
4 A) referida al mismo retorno. Los tres pasan por su filtro LC y salen por un
conector propio hacia **el bus board de invitados** (#169), que es una placa
nueva y **no** el bus board del instrumento: aquél tiene el +5 V «NC a
propósito» y **PTC de 0,25 A por riel y slot** (`hardware/bus-board/README.md`),
y un solo Disting EX (229 mA) o un Morphagene (165 mA) más su arranque lo
dispararía.

Por qué 3,8 A y no los 2 A de la PSU3, con la fila medida en HP:

| Fila de 104 HP hecha de… | mA/HP en +12 V | Total |
|---|---|---|
| filtros Doepfer (A-101-1: 30 mA / 16 HP) | 1,9 | ~200 mA |
| Clouds (120 mA / 18 HP) | 6,7 | ~690 mA |
| Morphagene (165 mA / 20 HP) | 8,3 | ~860 mA |
| **Disting EX (229 mA / 8 HP)** | 28,6 | **~3,0 A** |

Una fila entera de Disting EX es absurda, y cabe. Ése es el sentido de
«superior»: el rack no vuelve a ser el que decide qué módulo se compra.

Lo que el bus board de invitados lleva y lo que no **es del papel de #169**, no
de éste: número de peines (Doepfer pone 14 en 84 HP), la convención «franja
roja = −12 V, abajo» que el repo ya adoptó, si lleva PTC y de cuánto, y su
sitio en el chasis. Lo que este papel le entrega son **tres rieles con su
corriente, su rizado y su retorno**.

### 4.4 El +5 V digital: 8 A, y qué cabe

`PS6` (IRM-45-5) sustituye a la IRM-15-5 y **es el riel de menor rizado de la
familia** (80 mVp-p). Va a `GNDD` y al módulo 2 por el mismo conector de
`+5V_IN` que hoy (plan del cerebro, `J6` KK-254).

Contra `power_budget.py`, corrido el 2026-09-03:

| Escenario | Duras | Cadena | Total | Contra 8 A |
|---|---|---|---|---|
| Typ, 4 N657, host USB a tope | 0,965 A | 2,04 A | 3,005 A | cabe, sobran 5,0 A |
| Max TJ = 125 °C, 4 N657, host a tope | 2,895 A | 2,04 A | 4,935 A | **cabe, sobran 3,1 A** |
| Blanco pleno de la cadena | — | 9,60 A | — | **no cabe**: el tope de firmware se queda |

El techo del script (2,82 A) se reescribe a 8 A menos el margen que el propio
script aplica (enmienda, §10). **Y el HUECO #256 deja de bloquear el
dimensionado**: entre el típico (103 mA/chip) y el máximo a 125 °C (761 mA/chip)
hay 7,4×, el punto a 85 °C no está publicado, y con 8 A **se compra para el
máximo** y sobra. Lo que #256 sigue bloqueando es el calor de §4.5.

### 4.5 El 1,8 V: no se decide aquí, pero su calor sí se declara

`alimentacion-n657-design.md` §3.2 propone el 1,8 V como **LDO desde el 3,3 V**
y calcula su calor con el típico: (3,3 − 1,8) × 0,413 = **620 mW**. Con el
listón de §1 se dimensiona a máximo, y a máximo son 4 × 761,4 mA = 3,046 A:

```
(3,3 − 1,8) × 3,046 = 4,57 W
```

Siete veces más, y **más que todo lo que disipa la cascada a 650 mA**. Eso puede
voltear D-R1 hacia un buck contenido, y **es decisión de aquel papel** (D-R1
sigue abierto). Este papel carga con las dos cifras en su presupuesto térmico
(§6) y no elige. Dónde vive físicamente ese regulador —en el módulo 2, o uno
por placa de N657— tampoco es de aquí.

---

## 5. La red

Lo que entra por la pared es lo de #130: **IEC C14 Schurter `KM00.1105.11`** con
portafusible cerrado, y tras él, en la placa de red, la misma cadena de la v3
—`RV1` MOV S20K275, `NT1` NTC SL10 5R002, choke de modo común `L_F` con sus Y2—
alimentando a los seis módulos en paralelo.

**El fusible se recalcula, y con un guion.** La v2 fijó 1,6 A T con dos
worksheets (`v2/notes` §3.0 y §3.0.1): régimen permanente del toroide más la
IRM-15-5, e I²t del arranque del toroide. Los dos términos cambian:

- **Permanente.** Nominal de los seis: 20 + 20 + 45 + 30 + 20 + 45 = **180 W**.
  A red y a 83,5 % de rendimiento mínimo son 0,94 A rms si **todo** está al
  máximo a la vez; el caso típico (§6) son ~30 W de entrada, **0,13 A**. Los
  1,6 A tienen 1,7× de margen en el peor caso imaginable.
- **Arranque.** Ya no hay toroide que magnetizar; hay **seis condensadores de
  entrada cargándose en el mismo semiciclo**. La IRM-30 declara 4 A típicos a
  230 Vac (§3); si los otros cinco están en el mismo orden, la suma es del
  orden de **24 A de pico durante menos de un semiciclo** (ESTIMADO, suma de
  típicos). Lo limita `NT1` (5 Ω fríos) y lo tiene que aguantar el I²t del
  fusible. **`fusible_budget.py`** (§9) hace esa cuenta con los inrush de las
  cuatro hojas (§12.4) y el I²t del fusible elegido; hasta que corra, el valor
  es **1,6 A T como hipótesis heredada**, no como decisión.

**`NT1` se queda** hasta que ese guion diga otra cosa: 2 A nominales contra
0,94 A de peor caso permanente, y es lo único que pone impedancia delante de
seis arranques simultáneos.

**Crowbar: ninguno, como en #118**, y por una razón más: cada IRM lleva OVP
propio («shut off o/p voltage, clamping by zener diode»). Un fallo de un módulo
no pone su entrada de red en su salida; pone cero. Y la cascada sigue
protegiendo el bus contra cualquier fallo simple del pre-regulador (v3 §16.8).

**`TR1` con fusible térmico: ya no existe la pieza.** El criterio de #118 se
cierra por desaparición del transformador. Los IRM llevan protección de corto
en *hiccup* (§3) y su encapsulado es UL 94V-0 (p. 1 de las hojas).

**La fuga a PE se suma.** Seis módulos × < 0,25 mA más las Y2 del filtro: el
límite lo pone la norma del equipo (IEC 62368-1, **cifra a leer en la norma,
no de memoria**), y **`fuga_budget.py`** (§9) lo compara. Es además el mismo
número que §4.1 cuida por ruido: esa corriente vuelve por la estrella.

---

## 6. Térmica: el mismo recinto, otras fuentes

El modelo es el de `fuente-chasis-telemetria` §3.1 y no cambia: caja de acero
cerrada, **0,1453 m²**, **9 W/m²K** de convección natural, ΔT = P / (A · h). Con
9,22 W la v3 daba 7,1 °C. Lo que cambia son los términos.

**Caso típico** — instrumento a censo (340/327 mA), digital a 3,0 A, rack vacío:

| Fuente de calor | Cuenta | W |
|---|---|---|
| `PS1` + `PS2` | (15 × 0,340 + 15 × 0,327) × (1/0,84 − 1) | 1,91 |
| `PS6` | 5 × 3,005 × (1/0,835 − 1) | 2,97 |
| `PS3` + `PS4` + `PS5` en vacío | 0,15 + 0,1 + 0,1 | 0,35 |
| `U1` LM2941 | (15 − 13,1) × 0,340 | 0,65 |
| `U2` LM2991 | (15 − 12,9) × 0,327 | 0,69 |
| LT3045 ×2 + LT3094 ×2 | tabla de la spec del chasis, a censo | 0,35 |
| `U3` 7805 | (15 − 5) × 0,030 (spec del chasis: ~30 mA) | 0,30 |
| **Total** | | **7,2 W → ΔT = 5,5 °C** |

Menos que la v3 (9,22 W): el toroide ponía 1,6 W él solo y los pre-reguladores
caían de 19 V en vez de 15.

**Caso máximo** — todo al nominal a la vez: instrumento a 650/650, digital a
4,935 A, **rack a 3,8 / 2,5 / 4,0 A**:

| Fuente de calor | W |
|---|---|
| `PS1` + `PS2` a 650 mA | 3,71 |
| `PS6` a 4,935 A | 4,88 |
| `PS3` a 3,8 A (83,5 %) | 9,01 |
| `PS4` a 2,5 A (88 %) | 4,09 |
| `PS5` a 4,0 A (79 %) | 5,32 |
| Regulación a 650 mA: `U1`/`U2` recalculados a 15 V de entrada (1,24 + 1,37), LT ×4 de la columna «650 mA» de la spec del chasis (1,30), `U3` (0,30) | 4,20 |
| **Total** | **31,2 W → ΔT = 23,9 °C** |

Y encima de cualquiera de los dos, **el 1,8 V** si su regulador vive dentro del
recinto: +0,62 W típico, **+4,57 W máximo** (§4.5).

Dos lecturas honestas de la tabla de máximos:

1. **Es un caso que no existe**: una fila de 104 HP que coma 3,8 A y 4 A de
   +5 V a la vez, con la cadena de LEDs al tope y los cuatro N657 a 125 °C.
   Pero es **el que el listón compró**, y un recinto que no lo aguante es un
   recinto que limita en silencio, que es lo que el listón prohíbe.
2. **A 25 °C de sala son 49 °C dentro**, y ahí es donde importa la curva de
   derating que **no está leída** (§3). Si la curva empieza a bajar antes de
   50 °C, los 3,8 A de `PS3` no son 3,8 A a esa temperatura.

Lo que decide es **`calor_budget.py`** (§9), con la curva leída, y **el papel
del chasis** el que dice si el recinto cerrado sigue valiendo, si crece, o si
el máximo declarado del rack baja de 3,8 A a lo que el recinto sostenga. Este
papel no elige entre esas tres: declara que hay que elegir, y con qué número.

Los tres TO-220 **siguen contra la pared**. Con 0,65–1,37 W cada uno podrían
vivir sin ella, pero la pared ya existe, ya tiene su fila declarada
(`chasis_to220_*` en `params.scad`) y cuesta cero.

---

## 7. La telemetría

Los cinco chips de la v3 se quedan y **cambian de pregunta**:

| Chip | v3 | v4 |
|---|---|---|
| `U8` INA226 0x40 | +12 V ultra, V e I | igual |
| `U9` INA226 0x41 | +5 V de `U3`, V e I | igual |
| `U10` ADS1115 0x49 | −12 V, VRAW+, VRAW− (V) | −12 V, **+15 V, −15 V**, y el cuarto canal, libre hasta hoy, a **−12 V invitados** |
| `U11` TMP1075 0x48 | aire del recinto | igual, y ahora **es el que vigila la curva de derating de §6** |
| `U12` ISO1541 | barrera GNDA/GNDD | igual |

El divisor de 1/6 (100 k / 20 k al 0,1 %) sirve tal cual: ±15 V → ±2,5 V en el
pin, dentro de los 4,096 V de fondo de escala. Lo que muere es la frase «mide
por primera vez el valle de VRAW»: ya no hay valle. Lo que nace es **medir los
±15 V con carga**, que es donde se ve si un IRM se está saliendo de su curva.

**D-F2 (PROPUESTA, opcional): dos INA226 más, en los rieles del rack.** `U13`
en +12 V invitados y `U14` en +5 V invitados, direcciones 0x44 y 0x45 (libres:
`check_telemetria.py` vigila las colisiones). Cuestan lo que los otros dos y
dan una cosa que ningún case Eurorack da: **el instrumento le dice al dueño
cuánto come su rack, por riel, en la pantalla.** No toca la regulación, y va
en la placa de red porque ahí están los shunts. Samuel decide; si no, salen
con huella y `DNP`.

**El +5 V digital se mide donde nace.** `power_budget.py` dice que la puerta de
#151 la cierra «la corriente real del riel con el sensor de S9.1» en el
cerebro. Ese sensor se queda; la fuente pone **otro INA226 en `GNDD`** a la
salida de `PS6`, colgado del lado `GNDD` del `ISO1541` —no cruza la barrera— y
el bring-up (§9) **contrasta los dos**. Así #151 tiene dueño: la fuente lo da y
lo mide; el cerebro lo reparte y lo mide otra vez.

---

## 8. Las placas

**Dos, más el bus board de invitados**, y la razón es §4.2: seis módulos y una
isla de 0,8 µV no caben a ≥ 80 mm unos de otra en 200 × 150.

| Placa | Lleva | Hereda de |
|---|---|---|
| **R — red** | IEC (en la pared), `RV1`, `NT1`, `L_F` + Y2, la franja de 230 V con su barrera, **`PS1`–`PS6`**, seis filtros LC, `U13`/`U14`/INA de `GNDD` si D-F2, conectores de salida: ±15 V a C, ±12/+5 al bus board de invitados, +5 V digital al módulo 2 | la franja de red de la v3 (`rutear_red`, `NETS_RED`, barrera de fuga de 6 mm) |
| **C — cascada** | `U1`/`U2` en fila contra la pared, la isla LT3045/LT3094 con su `GNDREF`, `U3`, la isla de telemetría, `J2`, `J6`, `J8`; entrada: ±15 V | **la v3 entera menos `TR1`, `BR1`, `C_bulk` y la franja de red**; la isla ruteada y sus puertas se reutilizan |
| **Bus board de invitados** | #169 | el bus board del instrumento, con otro presupuesto de PTC |

Lo que gana la partición además de la distancia: **R es tonta y C es la v3**.
R no tiene un solo nodo de alta impedancia; C no tiene un solo nodo de red. El
DRC, `check_pcb.py`, `check_netlist.py` y la mitad de `check_bringup.py` de la
v3 valen para C con cambios de nombre. Y **R se puede probar sola**, con cargas
ficticias, antes de conectarle nada sensible (§9, bring-up paso 1).

La unión R → C son **cuatro hilos** (+15, `GNDA`, −15, y `GNDA` otra vez para
que el retorno del riel no comparta pin) por un KK-254 con llave, como `J2`.

**Tamaños**: los seis IRM ocupan 160 cm² de huella entre todos; R con su
franja de red y sus filtros anda por **200 × 150 (ESTIMADO)**; C, sin el
rectificador ni el toroide, **por debajo de 200 × 100 (ESTIMADO)**. Los dos
números los pone `build_pcb.py` de cada una, no este papel.

**El chasis** pierde el toroide (Ø93 × 46 en `chasis_toroide_x = 273,5`) y gana
una placa. `chasis_int_x = 332` estaba dimensionado para PCB + toroide en fila;
qué mide ahora es del papel del case (§10). Lo que este papel le exige: **las
dos placas dentro del mismo recinto de acero**, porque R lleva 230 V y C lleva
los tres tabs contra la pared.

---

## 9. Las puertas

La constitución (Principio II) dice que un presupuesto es un guion con
aserciones. Éstas son las de la v4, con su origen:

| Puerta | Estado | Qué pregunta |
|---|---|---|
| `check_absmax.py` | hereda | ¿la cascada existe y protege sola? Sin cambios |
| `check_telemetria.py` | hereda, crece | direcciones, divisores, shunts — más `U13`/`U14` si D-F2, y el INA de `GNDD` |
| `kicad/check_bom.py`, `check_netlist.py`, `check_pcb.py`, `check_fab.py`, `check_huellas.py` | **una por placa** | las mismas preguntas sobre R y sobre C; `check_huellas.py` estrena **seis huellas IRM dibujadas de la p. 3 de cada hoja** (§12.6) |
| `check_red_chasis.py` | hereda, crece | IEC con su recorte (#130, sigue abierto), **un** fusible, y ahora: cada IRM con su LC y su retorno propio a la estrella |
| `check_bringup.py` | **se reescribe** | §9.1 |
| `valle_budget.py` | **muere** | no hay valle |
| `margen_budget.py` | **nuevo** | tolerancia + rizado + DCR del LC contra el dropout de `U1`/`U2` (§4.2) |
| `fusible_budget.py` | **nuevo** | permanente e I²t de seis arranques contra el fusible del IEC (§5) |
| `fuga_budget.py` | **nuevo** | seis fugas + Y2 contra la norma (§5) |
| `calor_budget.py` | **nuevo** | las dos tablas de §6 **con la curva de derating leída**, y el 1,8 V en sus dos valores |
| `rizado_budget.py` | **nuevo** | LC × PSRR(`U1`) × PSRR(LT) a la frecuencia de peor caso, contra la cota de ruido (§4.2, §12.3) |
| `consumo_total_budget.py` (módulo 3) | **enmienda** | `RESERVA_INVITADOS` desaparece; el 650 con 30 % es todo del instrumento |
| `invitados_budget.py` | **nuevo** | 3,8 / 2,5 / 4,0 A contra el censo de §4.3 y contra lo que `calor_budget.py` sostenga |
| `power_budget.py` (módulo 2) | **enmienda** | techo 2,82 A → 8 A menos el margen del script |
| `ground_budget.py` (bus board) | **enmienda** | el término del retorno del rack por los jacks (§4.1) |

Todos los nuevos entran por `hardware/tools/gates.py` sin lista, como los de la
v3, y **cada uno se ve fallar con su mutación antes de mergear** (Principio
VIII, tabla de puertas de la constitución).

### 9.1 El bring-up, reescrito

Se escribe antes de que exista la placa, como el de la v3, y hereda su forma:
cada paso predice un número, `medidas.csv` lo guarda, `check_bringup.py` juzga.
Lo que cambia de sujeto:

- **Paso 0** (desenchufado): aislamiento de los tres tabs contra la pared
  **se queda**: `U2` sigue con el tab a su entrada, que ahora es −15 V y no
  −20, y la pared sigue a PE. Continuidad de tierra, igual. **Nuevo**: cada
  retorno de IRM tiene continuidad con la estrella **y solo con la estrella**
  (óhmetro entre el borne −V de cada módulo y la estrella: miliohmios; entre
  dos bornes −V de módulos distintos **con la estrella desconectada**: abierto).
- **Paso 1** (R sola, C y bus board desconectados): **cada IRM, uno por uno**,
  tensión en vacío y a su nominal con carga ficticia, y **rizado a 20 MHz con
  el método de la nota 2 de la hoja** (par trenzado de 12", 0,1 µF ‖ 47 µF),
  para que el número sea comparable con el de la tabla. Es el paso que la v3
  no podía dar: probar la entrada de red sin arriesgar la cascada.
- **Paso 2**: ±15 V con carga → **rizado después del LC**, que es lo que ve
  `U1`/`U2`. Aquí se descubre la frecuencia de conmutación real (§12.2).
- **Pasos 3–5**: la cascada, iguales a la v3 (setpoints, `J2` medido y no leído,
  ±12 V con carga).
- **El paso 4 de la v3 —el valle— muere.** Su sustituto: **mínimo de +15 V con
  carga contra los 14,1 V que `U1` necesita** (§4.2).
- **Nuevo, el retorno del rack**: 2 A de carga ficticia en +12 V invitados y
  **milivoltios entre la estrella y el `GND` del bus board del instrumento**.
  Cada milivoltio son 1,2 cents; el umbral lo pone `ground_budget.py`.
- **Nuevo, la telemetría del +5 V digital**: la lectura del INA en `GNDD`
  contra la de S9.1 del cerebro contra el multímetro. Tres números que tienen
  que coincidir.
- **El LNA (#58) deja de ser «fase E»: es la puerta del riel ultra.** Sin el
  número de ruido medido con seis conmutadas encendidas, el 0,8 µVrms es una
  cifra de hoja y este papel no se sella.

---

## 10. Enmiendas a otros papeles

Se listan para ejecutarlas en el plan de esta tanda, **no para que un
documento prometa lo que otro no hace** (el repo ya se hizo esa herida:
issues #214 y #206).

| Documento | Tipo | Qué |
|---|---|---|
| `hardware/01-power-supply/v3/README.md`, `docs/modules/01-power-supply.md` | Update | estado: la v3 no se pide; la v4 es la que se construye, y por qué |
| `hardware/01-power-supply/notes/design-notes.md` §18 | **Rewrite** | el veto pasa de 100 Hz a kHz: seis módulos, regla de retorno propio, distancias con sujeto nuevo, y **el LNA como puerta** |
| `docs/superpowers/specs/2026-08-18-fuente-chasis-telemetria.md` §3.1, §3.3, §4 | Update | térmica → `calor_budget.py`; geometría sin toroide; telemetría de §7 |
| `docs/superpowers/specs/2026-08-31-alimentacion-n657-design.md` §3.2 | Patch | el calor del LDO a máximo (4,57 W); D-R1 sigue abierto con los dos números |
| `docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md` §7, §11.5 | Patch | la IRM-15-5 «fuera de la placa» se sustituye por `PS6` en R |
| `hardware/03-vco/consumo_total_budget.py` | Patch | sin `RESERVA_INVITADOS`; aserción nueva: el 650 es del instrumento |
| `hardware/02-midi-cv/power_budget.py` | Patch | techo del +5 V digital → 8 A menos margen |
| `hardware/bus-board/ground_budget.py` | Expand | término del retorno del rack por los jacks |
| `case/cad/params.scad`, papel del case | Sync | `chasis_toroide_*` desaparece; dos placas en el recinto; el IEC (#130) sigue pendiente; el recinto se re-dimensiona con `calor_budget.py` |
| #169 | Update | los rieles del bus board de invitados son los de §4.3; el papel del bus board queda por escribir |
| #151 | Close | el +5 V digital tiene dueño (§7) |
| #141, #280, #106, #56, #57 | Close | el sujeto desapareció con el toroide y el rectificador |
| #256 | Update | ya no bloquea el dimensionado del +5 V; bloquea el calor del 1,8 V (§4.5) |
| #58 | Update | pasa de mejora a puerta del riel ultra (§9.1) |

---

## 11. Lo que este papel NO decide

- **D-R1, el 1,8 V** (LDO o buck, y dónde vive). Aquí solo se declara su calor
  en los dos extremos.
- **El bus board de invitados** (#169): peines, PTC, sitio. Aquí solo sus rieles.
- **El recinto**: si el cerrado aguanta los 31 W del máximo, crece, o el máximo
  del rack baja. Lo dice `calor_budget.py` con la curva leída, y lo elige el
  papel del chasis.
- **El valor del fusible**: 1,6 A T es hipótesis hasta `fusible_budget.py`.
- **Ninguna pieza que no esté en §3 con su hoja** (R-M3): los filtros LC, el
  INA de `GNDD`, los conectores nuevos, se nombran en el plan con hoja en el
  árbol.
- **El tope de brillo de la cadena de LEDs**: se queda por diseño (spec del
  cerebro); el 5,1 A de §1 es lo que le queda, no un permiso.
- **Si D-F2 entra**: Samuel.

---

## 12. Verificaciones antes de sellar

1. **Leer con los ojos la tabla de rendimiento de la IRM-45** (p. 2) y
   deshacer la ambigüedad (†) de §3. Cambia `calor_budget.py` en décimas.
2. **La frecuencia de conmutación de los seis**, que ninguna hoja publica: o
   Mean Well la da, o **se mide en el paso 2 del bring-up** y hasta entonces el
   LC se diseña para el peor caso del rango.
3. **`rizado_budget.py` con las curvas de PSRR** de LM2941, LM2991, LT3045 y
   LT3094 a esa frecuencia, contra la cota de ruido del riel. Es el número que
   dice si la cascada se come 200 mV de conmutación como se comía voltios de
   100 Hz. **Y luego el LNA (#58)**, que es el único que lo confirma.
4. **El inrush de las hojas de 15, 20 y 45 W** (fila «INRUSH CURRENT» de p. 2,
   no extraída), para `fusible_budget.py`.
5. **La cifra de fuga de la norma** (IEC 62368-1, equipo Clase I) para
   `fuga_budget.py`; y la de la IRM-30 y la IRM-45, que la extracción dejó
   ilegibles.
6. **Las seis huellas IRM** dibujadas de la p. 3 de cada hoja (paso de pines,
   diámetro de taladro, courtyard) y pasadas por `check_huellas.py`: la v3
   aprendió que una huella equivocada pasa el ERC, el DRC y la netlist.
7. **La curva de derating** de las cuatro hojas, leída y tabulada, para
   `calor_budget.py`. Es la que decide §6.
8. **Que el retorno del rack por los jacks queda por debajo del umbral** de
   `ground_budget.py` extendido. Cálculo antes del bring-up; medida en él.
9. **Stock real** de las seis referencias el día de mandar (la v2 ya aprendió
   que el stock se consulta en vivo, no de memoria).

---

## 13. Riesgos

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | El rizado de conmutación no se atenúa como los 100 Hz: la cascada fue diseñada para voltios lentos, no para 200 mV rápidos | §12.3 calculado **y** el LNA medido con las seis encendidas |
| 2 | Seis fugas de 50 Hz sumadas se oyen | `fuga_budget.py`; regla de retorno propio de §4.1 verificada en `check_netlist.py` |
| 3 | El recinto cerrado no aguanta el máximo (31 W) y los IRM salen de su curva | `calor_budget.py` con la curva leída; la decisión del chasis (§11) |
| 4 | El retorno de un invitado glotón desafina el instrumento | `ground_budget.py` extendido + medida del bring-up |
| 5 | Seis arranques en frío funden el 1,6 A T, o el fusible que no funde no protege | `fusible_budget.py` |
| 6 | El calor del 1,8 V a máximo (4,57 W) cae dentro del recinto y nadie lo contó | §4.5 declarado; D-R1 decide con los dos números |
| 7 | Una huella IRM equivocada llega a fábrica | §12.6, `check_huellas.py` por placa |
| 8 | El listón compró un máximo que no existe (fila de 104 HP a 3,8 A) y se paga en tamaño y calor por nada | Es el precio del listón, firmado; lo que se puede bajar es el máximo declarado del rack si §6 lo exige, y eso es una decisión, no un descubrimiento |
| 9 | Dos placas y un bus board: tres proyectos KiCad donde había uno, y las puertas se multiplican por tres | Las puertas heredan por placa (§9); lo que se paga es tiempo, no riesgo |
