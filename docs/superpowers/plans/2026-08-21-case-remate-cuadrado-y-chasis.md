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
