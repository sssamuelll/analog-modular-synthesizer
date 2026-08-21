# Remate cuadrado y chasis sobre largueros — plan de implementación

**Objetivo:** terminar el cambio a medias del 2026-08-20 partiéndolo en tandas
independientes, cada una con sus dos puertas en verde antes de mergear.

**Spec:** [`2026-08-15-case-design.md`](../specs/2026-08-15-case-design.md) (rev. 5)

**Diff de partida guardado en:** `scratchpad/wip-2026-08-20.patch` (383 KB) — no
se perdió nada al revertir.

## Constantes globales

- Las **puertas son el test**. No hay pytest: hay `clearance_budget.py` (sale
  distinto de 0 si el diseño se sale) y `check_dxf.py` (relee los DXF como los
  verá la fresadora). Constitución, Principio II.
- **Ninguna tanda desactiva un assert para pasar.** Si una puerta estorba, se
  cambia su PREMISA con la razón escrita, en el mismo commit que cambia la
  geometría. Borrar el assert es el fallo que produjo este plan.
- `kerf = 0` — proceso fresado CNC. No se toca.
- Todo número nuevo se deriva de otro, o lleva escrito por qué es libre.
- Una tanda = una rama = un PR mergeado. Lo aplazado se abre como issue.

---

## T0 — Restaurar el suelo ✅ HECHA (2026-08-21)

`git checkout HEAD --` sobre `case/cad`, `check_dxf.py`, `clearance_budget.py`,
`case/plans` y `case/renders`. Resultado: las dos puertas en verde (exit 0), 17
artefactos regenerados, **los 11 DXF byte-idénticos** tras el export, y el board
de intención que enlaza el README de vuelta en su sitio. Los cinco scratch de
`case/` borrados.

**No dejó nada que commitear**: el revert volvió a HEAD exacto y el export
reprodujo los mismos bytes. Ese diff cero ES la verificación.

---

## T1 — La punta de arriba, cuadrada ✅ HECHA (2026-08-21)

**Reemplaza a la cascada.** El plan original doblaba la piel superior a 45° para
matar la tira pegada. Samuel lo descartó el 2026-08-21 — doblar acrílico pide
otro taller y otra tolerancia — y eligió lo contrario: **cuadrar la punta de
arriba y tirar el case un poco hacia atrás**. Con eso no hay que doblar nada.

Lo que se tocó, y por qué son **dos** parámetros y no uno:

- `marco_remate` 18 → **34**. Es el parámetro del que se deriva el fondo del
  case, así que la pared trasera se va 16 mm atrás y la meseta del techo se
  ensancha lo mismo. Sondeado de 18 a 50: verde en todo el rango.
- `radio_remate` = **2**, nuevo. Los vértices 4 y 5 compartían `radio_punta`,
  que va sobredimensionado a propósito (400) y `_r_util` lo recorta a lo que
  quepa en la arista — o sea a `marco_remate/2`. **Subir solo el marco engorda
  el round**: de 9 mm de tangente a 17. Renderizado y verificado antes de
  escribir nada. 2 y no 0 porque una esquina viva en acrílico colado de 8 mm es
  donde arranca una fisura.
- Las dos derivaciones que colgaban del round viejo, corregidas en los **dos**
  modelos: `y_rs` en `sam17_case.scad` y `por_techo` en `clearance_budget.py`
  pasan de `marco_remate/2` a `radio_remate`.

**Tres cotas apretadas se relajaron solas**, y ninguna se buscó:

| | antes | después |
|---|---|---|
| tapa de la fila de arriba | abre 151.2°, topa con el remate | **abre 180°** |
| chasis PSU vs largueros de base | 3.33 mm (*«la cota más justa del montaje»*) | **11.33 mm** |
| fondo libre de la bandeja | 46.7 mm | **62.7 mm** |

Fondo del case: 276.3 → **292.4 mm**. Alto y ancho, sin cambio.

### Lo que la T1 dejó abierto — la tira pegada

Sigue viva y ahora pesa más. El remate es hoy una tira de 16 mm pegada al
Z-Rail (§2 de la spec, la única junta irreversible del case). Con la meseta a 34
esa tira tiene que crecer a ~34 mm, y **una tira de 34 × 528 pegada por un solo
canto es peor que la de 16**. Tampoco puede atornillarse al larguero de remate:
ese larguero está **47.3 mm por debajo del techo**, lo empujó ahí el barrido del
Z-Rail inclinado para que la tapa de arriba pueda abrir.

Salidas posibles, ninguna elegida todavía:

1. Un **larguero nuevo** en la esquina de arriba, y la tapa de remate atornillada
   a él como cualquier otra plancha. Hay que verificar que no entre en el barrido
   del Z-Rail — es justo lo que empujó al de remate 47 mm abajo.
2. La tapa **anclada a los dos costados** por sus puntas, sin larguero.
3. Dejarla pegada y aceptar la junta, subiendo `prof_sup` a 34.

**Decisión pendiente de Samuel.** Mientras tanto `prof_sup` se queda en 16, o sea
que hay una ranura abierta a lo largo del techo — que es también por donde sale
el aire caliente, así que cerrarla toca el issue #46.

---

## T4 — La trasera se empotra y sella  🔸 PASOS 1–3 HECHOS (2026-08-21)

**Decidido el 2026-08-21.** Samuel pidió que el acrílico encaje a la perfección
y selle el case. Eso **mata la junta de sombra**, que la spec §5 nombra como
lenguaje visual («tornillería inox de botón: reservados a las pieles
flotantes»). Se escribe aquí porque es una decisión de forma y no un ajuste: la
trasera deja de leerse como paneles suspendidos y pasa a ser una cara continua.

### Lo que hay hoy, medido

Las pieles **no están empotradas: cuelgan**. Su cara exterior queda 10 mm por
detrás del canto de los costados, sobre 12 separadores de 5 mm, y miden 518.32
en un hueco de 528.32.

| | |
|---|---|
| cara trasera entre costados | 1308.8 cm² |
| lo que tapan las dos pieles | 1100.9 cm² |
| **hueco directo** | **207.9 cm²** |
| — franja de arriba (32.3 × 528) | 170.7 cm² |
| — junta de sombra y canto de abajo | 37.2 cm² |
| ondas de ventilación | 51.1 cm² |

### El número térmico ya existía, y sale a favor

El #46 pide comparar el área de ondas contra la potencia del §4 de la spec de la
fuente, y esa potencia está escrita ahí: LM2941 ~2.7 W, LM2991 ~2.9 W, LT3045×2
~0.4 W, LT3094×2 ~0.33 W = **~6.3 W** en reguladores, más pérdidas del trafo (no
itemizadas).

Sellada la trasera quedan los **51.1 cm² de las tres ondas** como escape contra
~169 cm² de entrada por el suelo delantero. Tiro de chimenea, área efectiva
dominada por la salida (48.9 cm²), h ≈ 0.15 m, C_d = 0.65, aire a 20 °C:

```
P = 0.38 · ΔT^1.5      6.3 W  ->  ΔT ~ 6 °C
                        10 W  ->  ΔT ~ 9 °C
```

**SUPUESTO, no medido**: C_d, la altura efectiva de chimenea y las pérdidas del
transformador. Pero el orden de magnitud dice dos cosas útiles: sellar no es lo
que calienta el case, y **las ondas no hay que agrandarlas**.

### Dos hallazgos que van al #46, no a esta tanda

1. **El #46 cuenta 4 motivos de onda y hay 3.** El cuarto vivía en el suelo
   (`bandeja_base_2d`, «ventilación bajo el PSU») y se convirtió en la salida de
   cables cuando entró el chasis de acero. El inventario del issue está viejo.
2. **El chasis del PSU es una caja de acero cerrada.** Su única abertura es la
   ranura de cables de 88 × 26 = **22.9 cm²**, y está **en el suelo**, que es el
   peor sitio para un escape. Los ~6.3 W se disipan dentro de esa caja y al aire
   del case solo llegan por la chapa: ventilar el case no ventila el chasis.

---

- [x] **Paso 1: la puerta primero — `alineacion()` no mira la profundidad**

`piel_inferior` declara su fila de abajo contra `base trasera`, cuya cara trasera
está en x=277.22, y las otras tres en 291.22. Con la piel a 296.22 esa fila pide
un separador de **19 mm** y el BOM solo lista los de 5. `alineacion()` no lo caza
porque para las pieles solo compara el eje Y.

Antes de mover nada: que la puerta compare **también el eje de apoyo**. Cada fila
declara un larguero; hoy se verifica que coincida en un eje y se ignora el otro.
La piel apoya en la cara del larguero, así que esa distancia es parte del
anclaje, no un detalle.

```bash
python case/clearance_budget.py ; echo "EXIT=$?"
```

Esperado: **ROJO** citando la fila de abajo de `piel_inferior` a 14 mm de donde
apoya. Rojo = la puerta mide. Si sale verde, la puerta nueva está mal escrita.

- [x] **Paso 2: los cuatro largueros traseros al mismo plano**

En `centros_esqueleto()` de `sam17_case.scad` **y** en `_centros_esqueleto()` de
`clearance_budget.py`, a la vez y en el mismo commit:

```
base trasera        fondo - r - radio_perfil   ->  fondo - r - t_acrilico
entrepiso trasero   fondo - r                  ->  fondo - r - t_acrilico
remate superior     fondo - r                  ->  fondo - r - t_acrilico
repisa              fondo - r                  ->  fondo - r - t_acrilico
```

Con eso la cara del larguero queda en `fondo - t_acrilico` y la piel apoyada
encima remata **exactamente en el plano trasero**: enrasada, sin rebaje, sin
fresado 2.5D, sin dejar de ser un DXF plano.

Verificado que el de base cabe: a y=8 la curva del canto trasero está en
x=289.87 y la esquina del riel movido en 286.22. El comentario que hoy justifica
el `- radio_perfil` («adelantarlo solo compra fondo de bandeja y no hace falta»)
se reescribe: sí hacía falta, y por esto.

- [x] **Paso 3: las pieles se empotran**

`gap_sombra` deja de ser junta de sombra. Las pieles pasan a ancho completo menos
una **holgura de ajuste por lado** —parámetro nuevo, y libre: lo pone la
tolerancia de corte del taller (Schaeffer publica 0.05–0.10 mm), no el gusto— y
su X pasa de `P[6].x + gap_sombra + t_acrilico` a `P[6].x - t_acrilico`.

Mueren los 12 separadores M4 y sus 24 tornillos. Las pieles se atornillan con
tuerca T al larguero, como las bandejas.

- [x] **Paso 4: cerrar la franja de arriba — MEDIDO, y mata una opcion**

Los 32.34 mm de arriba son **170.9 cm²**, el hueco mas grande que le queda al
case. La pregunta era si cabe un larguero en la esquina de arriba para
atornillar ahi la tapa de remate. **No cabe, y no es opinion.** Los tres techos
de `_y_remate` para un larguero en `x_tr = 276.22`:

| techo | limite |
|---|---|
| el acrilico del techo (radio_remate = 2) | y ≤ 235.73 |
| el plano del panel de arriba | y ≤ 244.46 |
| **el BARRIDO del Z-Rail al abrir la tapa** | **y ≤ 200.38** ← manda |

Un larguero ahi arriba tendria su cara superior **37.34 mm por debajo del
techo**. La tapa de la fila de arriba gira sobre su propio M4 y barre ese
volumen: cualquier cosa que se meta ahi la deja sin abrir. Es la misma cuenta
que empujo al larguero de remate 47 mm abajo en su dia.

**Muere la salida 1** (larguero nuevo). Quedan, y son de Samuel:

2. La tapa de remate **anclada a los dos costados** por sus puntas. Sin larguero
   y sin pegamento, pero 528 mm apoyados solo en los extremos.
3. **Junta pegada de dos cantos** en vez de uno: con la piel superior subida
   hasta el techo, la tapa pega contra su canto Y contra el remate. Es peor
   que atornillar y mejor que la junta de hoy, que pega por un solo canto
   contra una pared de 1.2 mm.
4. **Subir la piel superior hasta el techo y que la tapa apoye en su canto.**
   Cierra la parte vertical (los 170.9 cm²) sin pieza nueva ni pegamento; deja
   abierta la meseta horizontal, 29 mm × 528 desde el apex hasta la piel.

- [ ] **Paso 5: BOM y documentos**

Fuera 12 standoffs M4 de 5 y 24 M4 de botón; dentro los M3 + tuerca T de las dos
pieles. **Recontar con el eco del modelo**, no a mano — el total de 71 cambia.
README: la sección de dimensiones y el orden de ensamblaje paso 6, que hoy dice
«12 separadores M4 de 5 mm, tres columnas». Spec §5: muere la junta de sombra.

- [ ] **Paso 6: las dos puertas, export, los dos renders**

El render trasero es el que juzga esta tanda — es literalmente la cara que se
cambió. Regenerarlo y mirarlo, no solo leer que la puerta salió verde.

- [ ] **Paso 7: commit, PR, y comentar el #46** con las tres cosas que esta tanda
      le aporta: el área real de ondas (51.1 cm²), que los motivos son 3 y no 4, y
      que el chasis es una caja cerrada con su única salida en el suelo.

---

## T5 — El octavo larguero, y el techo se atornilla  ✅ HECHA (2026-08-21)

**Decidido el 2026-08-21.** De las cuatro salidas de la T4, Samuel eligió la que
la T4 no tenía: un **larguero 2020 más**, en la arista trasera-superior, que le
da a la tapa de remate algo a lo que atornillarse. Con eso muere el pegamento y
con él la «excepción única» de la spec §2: el case pasa a ser enteramente
desatornillable.

Se estudiaron dos versiones renderizadas antes de escribir nada. **A** (elegida):
la plancha del techo va ENCIMA del larguero y lo tapa; la fijación es un tornillo
hacia abajo contra la cara de arriba del perfil, que es la dirección natural.
**B**: el larguero es el canto y la plancha topa contra su cara delantera; se ve
mucho más pero el tornillo entra horizontal por el canto de la plancha. Samuel
eligió A por la fijación.

### El case crece, y no es opcional

El larguero no cabe en el fondo de hoy. El barrido del Z-Rail al abrir la tapa
obliga a que su centro esté como mínimo en x=286.17, y el costado tiene que
cubrirle la cara de punta para llevar su M5 como los otros siete.

| centro del larguero | distancia al pivote | ¿libra? |
|---|---|---|
| 281.22 (fondo de hoy) | 11.95 | **no** — el barrido mide 12.91 + 4 de holgura |
| 286.22 | 16.95 | justo |
| **289.22 (marco_remate 42)** | **19.95** | **sí, 3.04 mm de margen** |

`marco_remate` 34 → **42**, fondo 291.2 → **299.2**. Los 3 mm de margen son la
misma holgura que el presupuesto ya exige entre el chasis y sus largueros: margen
de verdad, no de cuchillo.

### La pieza

- **Larguero nuevo**: 2020 de 528.32, centro en `(fondo − rail/2, P[5].y −
  marco_sup − rail/2)` = (289.22, 233.73). Cara trasera a ras del plano trasero,
  cara de arriba a `marco_sup` del techo. Es el larguero **8**.
- **`remate_sup`** deja de ser tira en L pegada al Z-Rail y pasa a **plancha
  horizontal** sobre la meseta: 42 × 528.32 en acrílico de 8 (`marco_sup` sin
  tocar — mismo espesor que los costados, mismo stock). Se atornilla con 3 M3 a
  la ranura de arriba del larguero nuevo, y su canto delantero remata el canto
  del panel de arriba, que es lo que hacía la tira.
- **`piel_superior`** sube hasta la cara de abajo del larguero nuevo y cierra la
  franja que quedó abierta en la T4.

- [x] **Paso 1: `marco_remate` 34 → 42**, con la razón escrita: la manda el
      barrido, no el gusto. Correr `clearance_budget.py`: verde esperado, el
      cambio es de fondo y ya se sondeó ese rango.

- [x] **Paso 2: el octavo larguero, en los DOS modelos**

`centros_esqueleto()` / `_centros_esqueleto()` pasan de 7 a 8 entradas, y
`NOMBRES_CE` gana «remate trasero». Al final de la lista, para no mover ningún
índice existente.

- [x] **Paso 3: `remate_sup` pasa a plancha horizontal atornillada**

Su DXF pasa de 528.32 × 16 a 528.32 × 42 y gana 3 taladros M3 sobre la
centerline del larguero nuevo. Declara su fila contra ese larguero, así que la
juzgan `alineacion()` y `apoyo()` como a cualquier otra plancha — que es
exactamente lo que no se podía hacer mientras iba pegada.

- [x] **Paso 4: `piel_superior` sube hasta el larguero nuevo**

Su canto de arriba pasa de y=215.4 a la cara de abajo del perfil. Con eso la
trasera queda cerrada del todo.

- [x] **Paso 5: muere el pegamento**

Fuera el adhesivo estructural del BOM y del `echo` del modelo. Spec §2 pierde su
«excepción única»: ya no hay ninguna junta irreversible en el case. README:
orden de ensamblaje paso 6, que hoy dice «la pestaña va PEGADA».

- [x] **Paso 6: las dos puertas, export, los dos renders, README y spec.**

### Lo que la T5 encontró, y no estaba en el plan

Una plancha FIJA encima de una bisagra bloquea la bisagra. La tapa de remate
giraba CON la tapa de la fila de arriba —por eso iba pegada al Z-Rail, que es
parte de esa tapa— y al atornillarla a un larguero fijo pasó a ser obstáculo:
la fila de arriba bajó de 180° a **13.2°**. Lo cazó `guarda_tapa()` sin que
nadie lo buscara.

Se resolvió retirando la tapa `inset_remate_frente` = 13 mm del pico. El
acantilado es abrupto — 9.3 mm dan 61°, 12.8 dan 180° — y por eso el número
lleva su medición escrita en `params.scad`: no es una cota que se pueda
redondear al gusto.

- [ ] **Paso 7: commit y PR.**

---

## T6 — Se va el entrepiso y la trasera pasa a UNA pieza de 8  ✅ HECHA (2026-08-21)

**Pedido el 2026-08-21:** «vamos a evitar la complejidad». Muere la bandeja de
entrepiso, las dos pieles se funden en una sola plancha empotrada de 8 mm, y las
ondas se conservan. La marca KONDOR se descartó para más adelante.

### Por qué el entrepiso se puede ir

Su papel de barrera entre la fuente y los módulos **ya lo hace el chasis de
acero** (#107): la red y el toroide viven dentro de una caja metálica puesta a
tierra. El acrílico no blindaba ni aislaba — era piso y nada más.

Lo que sí se va con él: **los 3 pasacables de 40 × 12** que ordenaban el cable
entre pisos. El volumen pasa a ser uno solo y el cableado deja de tener paso
definido. Toca el **#103**; no bloquea esta tanda.

`alto_interior_inferior` **no cambia de valor**, solo de dueño: se derivaba de
`y_entrepiso - t_acrilico`, que es la cara de abajo de la bandeja — pero la tapa
del valle es COPLANAR y del mismo espesor, así que el número sigue siendo el
mismo y ahora lo pone ella. Queda conservador donde el chasis no está debajo de
la tapa del valle, y conservador es el lado correcto.

### La trasera

| | hoy | T6 |
|---|---|---|
| piezas | 2 (piel inferior + superior) | **1** |
| espesor | 5 mm | **8 mm** |
| tamaño | 135 y 82 de alto | **528.02 × 216.73** |
| filas de tornillo | 2 cada una | **4** — base trasera, entrepiso trasero, repisa, remate superior |

Cuatro filas en vez de dos es lo que de verdad la sujeta: la plancha grande
apoya en todo el ancho y en toda la altura del esqueleto trasero.

Y los cuatro largueros traseros se retiran **8 mm** en vez de 5 para que siga
enrasando — 3 mm más adentro que hoy.

- [x] **Paso 1:** muere `bandeja_entrepiso` en los dos modelos, en `export.ps1`
      y en el lienzo. Los dos largueros de entrepiso se quedan. Reescribir el
      comentario de `alto_interior_inferior`: su techo es ahora la tapa del valle.
- [x] **Paso 2:** `t_piel = 8`, nuevo, y los cuatro largueros traseros pasan de
      `fondo - r - t_acrilico` a `fondo - r - t_piel`.
- [x] **Paso 3:** `piel_inferior` + `piel_superior` → `piel_trasera`, con cuatro
      filas de 5 taladros (`fila_agujeros`, como el resto de las planchas) y las
      tres ondas en su altura de siempre, derivadas de las filas que las rodean.
- [x] **Paso 4:** las dos puertas, export, borrar los tres DXF que sobran, los
      dos renders.
- [x] **Paso 5:** BOM, README, spec. Commit.

### Supuestos anotados

- **La tapa del valle se queda en 5 mm.** No se pidió tocarla y subirla movería
  la Y de dos largueros. Consecuencia: el acrílico de 5 lo compra **una sola
  pieza**. Se cierra en el pliego, no aquí.
- **5 taladros por fila**, como las bandejas, no 3 como las pieles viejas. La
  retícula visible de uniones es el ornamento que autoriza la spec §5, y una
  plancha de 528 × 217 en 8 mm los quiere.

### Lo que la T6 encontró

`check_dxf` salió en ROJO a la primera con «un agujero en x=475.22 se sale de la
rejilla». La trasera va **empotrada**, o sea `2 × hol_piel` más estrecha que el
ancho útil del case, y la rejilla se estaba calculando sobre el ancho del case:
cada columna corrida 0.06 mm y la última 0.27. Es exactamente el fallo contra el
que el comentario de esa puerta advertía por escrito desde su primera versión.

---

## T7 — El acrílico de atrás llega hasta arriba  ✅ HECHA (2026-08-21)

La trasera se frenaba en y=219.73 porque el larguero de remate vivía **a ras del
plano trasero** y le tapaba esa banda. Para que le pase por delante, ese larguero
tiene que retirarse `t_piel` — y ahí vuelve a meterse en el barrido del Z-Rail,
que es exactamente lo que lo mandó al plano trasero en la T5.

| centro del larguero | distancia al pivote | ¿libra? |
|---|---|---|
| 281.22 (retirado 8, fondo sin tocar) | 11.95 | **no** — la tapa deja de abrir |
| 286.17 | 16.91 | mínimo absoluto, margen 0.04 |
| **289.22 (marco_remate 50)** | **19.95** | **sí, 3.04 mm** — los mismos que tenía |

`marco_remate` 42 → **50**, fondo 299.2 → **307.2** (308.4 dibujado).

Resultado:

- La trasera corre de y=3 hasta **239.73**, la cara de abajo de la tapa de
  remate. 528.02 × **236.73** en 8 mm.
- Gana su **quinta fila** de tornillos, en el larguero que se movió.
- **Los cinco largueros traseros comparten X.** Una sola cota para todo el plano
  de apoyo.
- Desaparece la banda de aluminio de la trasera: acrílico de abajo arriba, con
  el canto de 8 mm de la tapa de remate rematando.

### Lo que la T7 encontró

`piel_trasera_2d()` salió con **bbox de 1.0 × 1.0 mm**. El módulo usaba `P[5].y`
para derivar su alto y `P` no estaba definido en ese scope: OpenSCAD lo trata
como `undef`, `alto` sale `undef` y `plancha()` no dibuja nada.

Es el mismo fallo que el del lienzo dos tandas atrás — variable ausente que no
levanta error —, pero **aquí sí lo cazó la puerta**, y a la primera. La
diferencia no es el fallo: es que `check_dxf` relee esta pieza y el lienzo no.

---

## T8 — Junto a la pared trasera quedan dos largueros  ✅ HECHA (2026-08-21)

**Pedido:** «tenemos cinco barras junto a la pared trasera de acrílico, quiero
que solo queden dos (la de abajo y la de arriba)».

### Los cinco nunca se diseñaron como cinco

Fueron creciendo uno por pieza, y cada pieza que los justificaba ya está muerta:

| larguero | y | nació por | esa pieza murió en |
|---|---|---|---|
| base trasera | 18.00 | la bandeja de base | — **se queda** |
| entrepiso trasero | 123.13 | la bandeja de entrepiso | T6 |
| repisa | 153.13 | la piel superior | T6 |
| remate superior | 200.38 | la tira de remate pegada de canto | T5 |
| remate trasero | 229.73 | la tapa del techo atornillada | — **se queda** |

Los tres de en medio sobrevivieron a sus motivos y seguían ahí solo como filas
de tornillo de la trasera. Y esas filas **no compran rigidez**: desde T6 la
trasera es una plancha continua de 8 mm atornillada arriba y abajo, o sea que esa
cara ya tiene alma de cortante — y una plancha entera es mejor alma que cinco
barras sueltas.

### El vano

211.73 mm libres entre las dos filas que quedan, sobre 528 de ancho y 8 de
espesor. Viga ancha biapoyada, `δ = PL³/48EI` con E = 3 GPa e
I = 528·8³/12 = 22 528 mm⁴:

| empuje en el centro | flecha |
|---|---|
| 50 N (un dedo firme) | 0.15 mm |
| 200 N (alguien apoyándose) | 0.59 mm |

### Lo que arrastró

- **`_y_remate()` muere entera** en `clearance_budget.py`, y con ella
  `radio_giro_riel()` en el SCAD. Existían para bajar el larguero de remate
  superior por debajo del barrido del Z-Rail; sin larguero no hay a quién bajar.
  El radio de giro sigue vivo en `_radio_giro_riel()`, que es donde de verdad se
  usa: `guarda_tapa()`.
- **Las ondas de la trasera** se derivaban de las filas que las rodeaban, y tres
  de esas filas ya no existen. Las fracciones se recalcularon contra las dos que
  quedan para dejarlas *donde estaban*: 82.75 y 171.68 contra 83.33 y 171.39.
- **El canario de `alineacion()`** probaba el umbral sobre «remate superior» y
  «repisa». Pasa a probarlo sobre «base trasera» en Y y «remate trasero».

### Balance

8 largueros → **5**. 69 tornillos → **48** (−6 M5 y −15 M3). Dos DXF movidos:
`costado_2d` (tres taladros M5 menos) y `piel_trasera_2d` (tres filas menos).
Los dos gates en VERDE.

---

## T9 — El suelo cierra, y el aire se muda atrás  ✅ HECHA (2026-08-21)

**Pedido:** «la barra que está chocando con el riel inferior… preferiría quitar
la barra y estirar la base para que selle completamente por debajo».

### Lo que se midió antes de tocar

Tres cosas, y las tres cambiaron el pedido:

1. **No chocaban.** Entre la esquina girada del Z-Rail y la cara del 2020 hay
   4.00 mm exactos = `holgura_rail`. Es el mínimo de diseño, clavado.
2. **El hueco era la entrada de aire**, documentado en `params.scad`: «no es un
   descuido: es por donde entra el aire frío, y sale por las ranuras del valle».
3. **La bandeja no podía estirarse.** El Z-Rail girado 35° baja a y = 4.84,
   3.16 mm por debajo del techo de la bandeja (y = 8), en la ventana
   x 23.70…30.44. Ninguna plancha plana le pasa por debajo.

Y quitar la barra habría dejado la bandeja en voladizo de 289 mm bajo el chasis
del PSU, en acrílico que fluye con carga sostenida. Se descartó.

### El lever real: `alto_frontal`

No viaja solo. La punta redondeada se come `alto_frontal/2` de cara, así que
arrastra `inset_inf_frente`, que va dentro de `alto_cara_inf`, que fija el fondo:

| | antes | ahora |
|---|---|---|
| `alto_frontal` | 13 | **19** |
| `inset_inf_frente` | 14.5 | **17.5** |
| `alto_cara_inf` (derivado) | 152.75 | **155.75** |
| esquina baja del raíl | 4.84 | **13.29** (5.29 de aire) |
| alto del case | 247.73 | **256.18** |
| fondo | 307.22 | **308.94** |

Es el precio que el propio `params.scad` tenía anotado de cuando se hizo el
trato al revés: «subir el riel cuesta 8 mm de aparato». Salieron 8.46.

El canto delantero de la bandeja se deriva ahora igual que el de la tapa del
valle: hasta donde **muere la curva** de la esquina (x = 9.49). Un mm más y la
plancha asoma por delante del redondeo; uno menos y queda suelo sin cubrir.

### La entrada de aire, y la puerta que la vigila

45 ranuras iguales a las del valle, abajo del todo en la trasera, por debajo de
la banda de ondas (que subió de 0.32 a 0.35 para hacerle sitio). **Duró unas
horas** — ver «La entrada de aire se mudó otra vez», más abajo en esta misma
tanda: acabó en el suelo y la banda volvió a 0.32.

| | área abierta | ranuras |
|---|---|---|
| entrada (trasera, abajo) | **8 317 mm²** | 45 de 47.1 × 4 |
| salida (valle) | 7 499 mm² | 102 de 19.2 × 4 |

**No cabía en el suelo.** La bandeja solo vuela 30.19 mm por delante del
larguero — con las mismas ranuras salen 3 536 mm², menos de la mitad.

`guarda_aire()` es nueva y compara las dos áreas derivándolas de sus módulos. Es
justo la cota que se pierde sola: no sale en ningún render, no la ve `solapes()`
ni el sobre del DXF, y el aparato arranca igual. Antes no hacía falta vigilarla
porque la entrada eran 20 054 mm² de hueco accidental contra 7 499 de salida.

### La entrada de aire se mudó otra vez, y la puerta cambió de criterio

Samuel miró los renders y pidió quitar la rejilla de la trasera: esa pieza se
queda **solo con sus tres ondas**. Lo que eso destapa es que ya no había dónde
entrara el aire, porque el suelo se acababa de cerrar.

Medido antes de tocar, con el modelo térmico que el propio plan ya tenía:

| entrada | área | altura | ΔT a 6.33 W |
|---|---|---|---|
| rejilla en la trasera | 8 317 mm² | y ≈ 53 | ~7 K |
| **rejilla en el suelo** | **3 535 mm²** | **y = 4** | **8.5 K** |
| sin rejilla ninguna | solo ondas | y ≈ 75 | ~14 K |

La del suelo tiene menos de la mitad de área y sale casi igual: entra 50 mm más
abajo y el tiro va con la raíz de la altura. Y es invisible — vive en el vuelo
de 30 mm que la bandeja gana por delante del larguero, fuera del camino de carga
entre los dos 2020, con el plenum de las paticas de 8 mm (~13 600 mm² de
perímetro) por debajo.

**`guarda_aire()` cambió de criterio el mismo día que nació.** Nació midiendo
«entrada ≥ salida», que valía con la rejilla en la trasera. Al mudarse al suelo
esa desigualdad se rompe a propósito. Mantener el assert habría sido tener una
puerta roja sobre geometría correcta — el vicio que costó la T0 entera. Ahora
mide **salto térmico** (`P = k·ΔT^1.5`, entrada y salida en serie, `h` entre
centroides) contra `salto_termico_max` = 15 K. Da 8.5.

Y el hueco del IEC subió de y=22 a **y=33**, centrado en la banda libre. No era
solo estética: uno de los cinco M3 de la fila de abajo cae dentro de su franja
de X (x=475.2), y a y=22 quedaban 3.5 mm entre la arandela y el recorte.

### `guarda_piso` cambia de signo

Su segundo assert exigía que la bandeja se **apartara** del raíl. Ahora exige
que **llegue** al frente, y lee la caja declarada en `_cajas_solidas` en vez de
rehacer la cuenta — que es de donde salió el bloqueante de 14 mm en T4. El
primero pasa de medir contra el canto del case a medir contra el techo de la
bandeja: es la cuarta vez que esa cota cambia de referencia.

---

## T10 — El espacio de los módulos lo comía el chasis  ✅ HECHA (2026-08-21)

**Pedido:** «aún estoy interesado en quitar la barra del frente que está muy
cerca del riel, preferiría que los módulos tengan máximo espacio».

### Por caja no se ve; hay que recorrer el panel

El primer intento midió cada estorbo por su caja envolvente y dio un número
falso: el mínimo de una caja puede caer en una `s` que el panel ni siquiera
ocupa. La medida buena recorre el panel y pregunta, en cada punto, cuál es el
estorbo más cercano al plano.

Hecho así, el limitante no era el larguero:

| | mínimo | quién lo pone | panel útil a 50 mm | a 60 mm |
|---|---|---|---|---|
| antes | 18.6 mm | **chasis** | 27 % | 11 % |
| solo quitar el larguero | 18.6 mm | chasis | 42 % | 20 % |
| solo mover el chasis | 25.8 mm | el larguero | 53 % | 37 % |
| **los dos atrás** | **34.4 mm** | chasis | **68 %** | 42 % |
| sin larguero + chasis atrás | 34.4 mm | chasis | 68 % | 46 % |

El chasis mide 176.6 × 93 y se sentaba centrado entre los dos largueros de base.
Los módulos de la fila inferior cuelgan del panel hacia dentro y hacia abajo y se
metían en su esquina delantera-alta. **Nadie había decidido que fuera centrado**:
`ch_pos()` simplemente lo centraba.

### La cadena, en un solo sentido

`x_tr → chasis → base delantera`, los dos saltos a `chasis_holgura_larguero`.
Escrito al revés habría dado recursión — `ch_pos()` mira `bandeja_base_fondo()`,
que mira `ce[0]`—, así que el chasis se ancla al larguero **trasero**, que solo
depende de `x_tr`.

El larguero delantero acaba en x = 88.34: **42.7 mm del raíl de panel** en vez de
4.00, que era la otra mitad de lo que molestaba.

### Lo que la tanda encontró

- **La holgura contra el raíl dejó de salir sola.** Estaba garantizada por
  construcción mientras el larguero se *derivaba* del raíl; al pasar a colocarlo
  el chasis se volvió una consecuencia, o sea la clase de cota que se rompe
  callada. `guarda_piso()` la exige ahora como tercer assert.
- **La rejilla de aire creció sola.** El vuelo de la bandeja pasa de 30.19 a
  68.85 mm y la rejilla vive en el vuelo: 3 535 → 11 421 mm², ΔT de 8.5 a 4.6 K.
  Está derivada del vuelo y no de un número a mano, así que no hubo que tocarla.
- **La barra no se retira.** Sostiene la fila delantera de la bandeja; sin ella
  la plancha queda en voladizo de 280 mm bajo el chasis (1.15 MPa, ~1.4 mm de
  flecha más creep) y la T2 pierde uno de los dos largueros donde quiere montar
  el chasis. Los 4 puntos de panel que se ganarían a 60 mm no pagan eso.

---

## T11 — La entrada de aire vuelve a la trasera  ✅ HECHA (2026-08-21)

**Pedido:** «vamos a quitar el respiradero del piso de ahí, mejor colocarlo
atrás (el efecto que hemos movido ya varias veces para la ventilación)».

### Cuatro mudanzas, y cada una cerró una pregunta

| | dónde | por qué se fue |
|---|---|---|
| 1 | hueco de 37.96 mm en el suelo | no era diseño, era lo que sobraba |
| 2 | trasera, abajo | al cerrar el suelo hubo que dibujarla |
| 3 | suelo, en el vuelo de la bandeja | Samuel dejó la trasera con sus ondas |
| **4** | **trasera otra vez** | en el vuelo **se veía** |

La tercera murió por algo que no sale en ninguna cota y que solo se vio en el
render: el acrílico naranja es **traslúcido**, y el campo de ranuras se
transparentaba a lo largo del canto inferior. Había crecido además de 18.2 a
56.8 mm de ranura al correr el larguero delantero, así que se notaba más.

### Lo que queda

45 ranuras de 40.5 × 4 (**7 128 mm²**) en la banda que dejan libre la fila de M3
por abajo y la onda por arriba. El hueco del IEC vive **dentro** de esa banda —
las dos fronteras que lo centran son las mismas que limitan el campo—, así que
queda embebido en la rejilla y no al lado. Se saltan sus columnas enteras, con
6.98 mm de material alrededor: partir una ranura con el recorte dejaría un diente
de acrílico colgando de un lado, que es donde el PMMA rompe.

ΔT pasa de 4.6 a **6.5 K** contra el techo de 15. Esos 1.9 K son lo que cuesta
que no se vea: en el suelo había más área (11 421) y más tiro (137 mm contra 91).

`y_bajas` se queda en 0.32 y no vuelve a 0.35. La banda da 40.46 mm, que es campo
de sobra, y subir la onda solo para engordar la rejilla movería el dibujo por una
razón que no es de dibujo.

---

## T2 — El chasis del PSU se monta sobre los largueros

Hoy el chasis de acero pasa **entre** los dos largueros de base y se apoya en la
bandeja de acrílico. El toroide, que es lo que pesa, cuelga de una plancha de PMMA
— y el issue **#106** dice que esa plancha resuena justo donde el toroide excita.
Esta tanda lo sube **encima** de los dos largueros: metal contra metal, 4 M5 a
tuerca T del 2020.

**Nota tras la T1:** la holgura contra los largueros pasó de 3.33 a 11.33 mm y el
fondo libre de la bandeja de 46.7 a 62.7. Esta tanda arranca con más sitio del que
tenía cuando se planeó.

**Ficheros:** `case/cad/params.scad`, `case/cad/sam17_case.scad`,
`case/clearance_budget.py`, `case/check_dxf.py`, `case/README.md`

- [ ] **Paso 1: declarar las dos filas ANTES de mover nada**

En `_cajas_solidas()` de `clearance_budget.py`, junto a las filas que ya declara la
bandeja (línea 366), el chasis declara las suyas:

```python
filas += [("chasis", "delantera", "x", ce[0][0], "base delantera"),
          ("chasis", "trasera",   "x", ce[1][0], "base trasera")]
```

`alineacion()` ya sabe juzgar esto — es la misma puerta que caza una plancha
atornillada al aire, y la que rechaza declarar un riel de PANEL. **No hay que
escribir puerta nueva: hay que usar la que existe.**

- [ ] **Paso 2: correr y esperar rojo**

```bash
python case/clearance_budget.py ; echo "EXIT=$?"
```

Esperado: `anclaje [chasis] fila delantera` fuera de la centerline por varios mm,
porque `chasis_int_y` todavía vale 170. Rojo = la puerta mide.

- [ ] **Paso 3: derivar `chasis_int_y` de los largueros**

Deja de ser un número escrito a mano. Las patas del chasis caen a 20 mm de cada
punta de la tapa, y esas dos posiciones tienen que ser `ce[0].x` y `ce[1].x`:

```
tapa_y       = (ce[1].x - ce[0].x) + 40
chasis_int_y = tapa_y - 4*t_chapa - chasis_hol_tapa
```

El scratch de anoche daba 216.6 **con el fondo viejo**; con el fondo a 291.2 el
número es otro y manda la derivación, no el scratch.

- [ ] **Paso 4: re-premisar la guarda 6, no borrarla**

`clearance_budget.py:1115` exige hoy que el chasis quepa ENTRE los largueros. Esa
premisa muere con esta tanda. Se sustituye por la que corresponde: que las patas
apoyen sobre el lomo del larguero con material a cada lado, y que el chasis no se
pase del ancho útil. El comentario de la línea 1107 explica la premisa vieja — se
reescribe explicando por qué cambió y en qué fecha, como el resto del repo.

- [ ] **Paso 5: dibujar los 4 M5 que anoche nunca se dibujaron**

`check_dxf.py` ya esperaba `+4` agujeros en `bandeja_base_2d` y `+4` en
`chasis_cuerpo_2d` — **y el modelo no dibujaba ninguno**. Por eso salía en rojo con
«10 agujeros en el DXF y el modelo pone 14». Los agujeros van en el modelo primero;
la expectativa de la puerta se deriva del modelo, nunca al revés.

- [ ] **Paso 6: `chasis_pie` de 10 a 20**

Con el chasis encima del larguero, los pies tienen que salvar los 20 mm del 2020.
El assert de altura interior (`c["alto"] + chasis_pie < alto_interior_inferior`) lo
juzga: si no cabe, esta tanda se cae y hay que decidir otra cosa. **Correrlo antes
de escribir el resto.**

- [ ] **Paso 7: las dos puertas en verde, export, README**

El BOM gana 4 M5 + 4 tuercas T (el total de 71 tornillos cambia — recontar con el
eco del modelo). El orden de ensamblaje gana un paso: el chasis va después de los
largueros y antes de la bandeja.

- [ ] **Paso 8: commit, PR, y comentar el #106 con el número**

---

## T3 — Retoques de las pieles

La más pequeña. `piel_inferior_2d()` gana una onda sierra y sus dos filas de M4
pasan a derivarse de repisa y remate en vez de `[15, alto-15]`. Es un cambio de
anclaje, así que lo juzga `alineacion()`.

- [ ] **Paso 1:** mover las filas en el modelo, correr `clearance_budget.py`, leer
      el desvío que reporta `alineacion()`.
- [ ] **Paso 2:** añadir la onda sierra a `piel_inferior_2d()`.
- [ ] **Paso 3:** `check_dxf.py` cuenta agujeros por rejilla — verificar que
      `REJILLA_PIEL` sigue cuadrando **sin tocarla**. Si no cuadra, es la pieza la
      que está mal.
- [ ] **Paso 4:** las dos puertas, export, commit.

---

## Cotas sueltas — no entran en ninguna tanda hasta que se justifiquen

- **`alto_frontal` 13 → 21.** Aparecía en el diff de anoche sin una sola línea de
  derivación y sin relación visible con nada. Mueve la silueta del costado, o sea
  un DXF ya presupuestado. **Se queda en 13 hasta que alguien escriba de dónde
  sale el 21.**

## Lo que este plan NO toca

Los 8 paneles (#45 incluido), el pliego para el taller, el acabado de canto y las
dos medidas con calibrador (#98, #97). Son el camino al acabado profesional y van
después de que el modelo esté cerrado — no en paralelo, porque todos cotan contra
este modelo.
