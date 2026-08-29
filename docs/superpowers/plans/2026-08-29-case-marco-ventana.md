# Plan — el marco de la ventana y la banda estructural

> **Para quien lo ejecute:** cada tarea sigue el patrón TDD-de-hardware del repo:
> la puerta primero (en `clearance_budget.py` o `check_dxf.py`), correrla y verla
> en ROJO **por su razón** contra el modelo o el DXF viejo, después el modelo,
> VERDE, y romper la puerta a propósito una vez. Se ejecuta en el worktree
> `.claude/worktrees/marco` (rama `feat/case-marco-ventana`). Cada tarea visible
> termina con `cad/export.ps1` y los dos renders.

**Objetivo:** doce piezas de tope y anclaje (6 placas, 4 clips, 2 escuadras) pasan
a dos marcos de ventana; los dos marcos de la trasera desaparecen porque la banda
vista pasa a ser el alma del miembro alto y del talón; la trasera va dentro del
canal; el chasis se atornilla a la tabla.

**Spec:** [`../specs/2026-08-29-marco-ventana-banda-estructural-design.md`](../specs/2026-08-29-marco-ventana-banda-estructural-design.md)

**Restricciones globales** (de la spec, valen en todas las tareas):

- `marco_fondo` = 26 (hereda `placa_fondo`); canto exterior retirado
  `t_costilla + hol_piel` = 1.65 bajo cada chapa, a 0 en las tres filas; pata
  trasera con canto exterior en `x_trasera_int − hol_piel`.
- `banda_trasera` = 24; filas de M3 de la trasera a 12 de cada canto libre.
- `brida_largo` = 40, escalón `brida_escalon` = 14 que sube `t_placa`; M4 a
  `brida_escalon + (2t + r + d/2)` y +10.5, ambos a `dist_rosca_ciega` de la
  silueta.
- `talon_pie` = 20; tres M4 a 1.5 D del canto libre del pie; P6 = `radio_chapa`.
- `prof_sup` = `marco_remate` = 50.
- Nada fijo en `[x_trasera_int − (tol + 0.5), x_trasera_int)` dentro de la huella
  de la trasera.
- Sin adhesivo en ninguna junta. Ningún tornillo en cara vista.
- Números sin fuente inline no se escriben (memoria: haiku fabrica números).

---

### Tarea 1 — el marco de la ventana

**Ficheros:** `case/cad/params.scad`, `case/cad/sam17_case.scad`,
`case/clearance_budget.py`, `case/check_dxf.py`, `case/cad/export.ps1`,
`case/cad/piezas.scad`, `case/renders/piezas.py`.

**Puertas primero (ROJO esperado contra los DXF de `main`):**

1. `guarda_marco_ventana(p)` en el budget: para cada una de las siete patas de
   `_marco_ventana(p)` (quads `A + u·s + n·b`, `b ∈ [retiro, marco_fondo]`):
   - `retiro` = 0 en `cara_inf`/`valle`/`cara_sup` y `t_costilla + hol_piel` en
     `frente`/`suelo`/`meseta`/los 10 de `cara_sup` bajo el retorno; la pata
     `trasera` con canto exterior en `x_trasera_int − hol_piel`;
   - `marco_fondo − cara_anillo ≥ 6` (la sombra sobre el acrílico);
   - pata trasera: viga 16.35 × 6 empotrada, `carga_mano` al centro de su largo
     libre → flecha ≤ 1.0;
   - cada rosca del marco (`_roscas_marco`) y cada cajeado a ≥ 1.5 D del canto de
     su pata; cada paso de brida a ≥ 1.5 D del canto retirado.
   ROJO esperado: `_marco_ventana` no existe → `AttributeError`; se escribe la
   función con el contorno y la puerta pasa a medir.
2. `taladros_marco_ventana()` en check_dxf (sustituye a `taladros_placas`): relee
   `marco_ventana_2d.dxf`: 10 M4 ciegos + 6 pasos de riel + 1 M3 pestaña + 2 pasos
   de brida, en las posiciones del modelo, a ≥ `BORDE_MIN_D × D` del contorno
   releído; el contorno releído dista ≥ 6 de la línea de la ventana en 7 puntos
   de muestreo (uno por tramo). ROJO esperado: `FALTA el DXF`.
3. `guarda_costado()`: `apoyos = [quad por pata de _marco_ventana]`; el mensaje
   deja de hablar de clips. `cuerpos_dentro_del_anillo()`: el marco pasa sus
   siete quads; fuera placas, clips, escuadra.
4. `guarda_anclajes()`: `_centros_rosca_ciega` = 10 del marco + 2 de brida (la
   brida se termina en la Tarea 2: hasta entonces se deja la de hoy). Muere el
   bloque del clip.

**Modelo:**

- `params.scad`: `placa_fondo` → `marco_fondo`; mueren `t_clip`, `clip_fondo`,
  `clip_largo`, `escuadra_ala`, `escuadra_m3`, `escuadra_retiro`,
  `placa_chaflan`, `reparto_rincon`. `retiro_placa_inf`/`_sup` se quedan (son las
  posiciones del escalón del canto exterior).
- `sam17_case.scad`: `function patas_marco()` (siete tuplas `[nombre, i0, i1,
  retiro, rieles]`), `function marco_ventana_pts(pata)`, `module
  marco_ventana_2d()` = `difference(){ contorno exterior; offset(delta =
  -marco_fondo) perfil_lateral(); taladros }`, `module marcos_ventana()` (×2,
  espejo en z, 6 cajeados por el lado del anillo). `roscas_marco()` = por cada
  riel 3U y el primer 1U, eje ± `sep_rosca_riel` a `dist_rosca_ciega`. Mueren
  `placas()`, `placa_2d`, `placa_riel`, `placas_riel`, `clips*`, `escuadra*`,
  `corte_placa`, `esquinas_placa`, `limite_rosca`, `centro_par_rosca`.
  `assembly_aluminio()` llama a `marcos_ventana()`. `PART`: `marco_ventana_2d`.
- `export.ps1`: entra `marco_ventana_2d`; salen `placa_*_2d`, `clip_2d`,
  `escuadra_trasera_2d`. `_sobres()`: `dims["marco_ventana_2d"]` = bbox de las
  siete patas. `piezas.scad`/`piezas.py`: `marcos_ventana` en aluminio; fuera
  `placas_riel`, `clips_costado`, `escuadras_trasera`.

**VERDE:** `python case/clearance_budget.py` (HUECO 2 por la banda del valle,
cero ROJO), `cad/export.ps1`, `python case/check_dxf.py` VERDE. Romper: subir
`marco_fondo` a 40 → la rosca de brida cae fuera del marco / el cajeado del
riel-eje se acerca al canto; volver.

**Commit:** «El marco de la ventana: seis placas, cuatro clips y dos escuadras en
una pletina por costado».

---

### Tarea 2 — la banda es el miembro: `miembro_alto`, `talon`, la trasera dentro

**Ficheros:** los mismos cuatro más nada.

**Puertas primero:**

1. `guarda_miembro_alto(p)`: la L (meseta `prof_sup` × banda `banda_trasera` en
   `t_costilla`) con `carga_mano` en el centro de `ancho_util` → `σ =
   M·c/I ≤ RP02_ALUMINIO` (assert) y flecha (print); fila de M3 a ≥ raíz
   (`radio_doblez_costilla + 3t + d_M3/2`) del doblez de arriba y ≥ 1.5 D del
   canto libre; pestañas: `brida_escalon = t_placa` de subida, M4 a ≥ `2t + r +
   d/2` de la tangente del escalón y ≥ 1.5 D del canto libre, ambos a
   `dist_rosca_ciega` de la silueta y dentro de la franja. ROJO esperado: con
   `banda_trasera` = 20 (el valor de `marco_trasera_ancho` heredado en el primer
   intento) σ = 158 > 130.
2. `guarda_talon(p)`: banda a ras (`x1 == P6.x`), pie sobre la tabla (`y0 == 0`),
   M4 del pie a 1.5 D del canto libre y con la cabeza (Ø7.6) fuera de la huella
   de la trasera; fila de M3 a ≥ raíz del doblez; `radios_perfil()[6] ==
   radio_chapa`. ROJO esperado: P6 = 0.
3. `guarda_trasera_dentro(p)`: recorre `_cajas_solidas` y exige que ningún cuerpo
   fijo ocupe `x ∈ [x_tr − (tol + 0.5), x_tr)` dentro de `y ∈ [t, P5.y − t]`,
   `z ∈ huella`; la meseta cubre el canto de arriba (`x` de la meseta llega a
   `P6.x`), el pie cubre el de abajo; las muescas de esquina (5.5 × 20.5) libran
   el escalón con 0.5. ROJO esperado contra el modelo de hoy: el alma del
   miembro alto a 8.00 justos → «nada a distancia fija».
4. `taladros_talon()` en check_dxf: `talon_2d` trae la fila de 5 M3 y nada más;
   sus tres M4 aparecen en `bandeja_base_2d` (como `taladros_nariz`).
5. `guarda_remate`: `prof_sup == marco_remate`. `taladros_reticula`: `MIEMBROS_DXF
   = {"miembro_alto_2d": "trasero alto", "talon_2d": "talon"}`. `agujeros_donde_toca`,
   `alineacion`, `apoyo`, `guarda_agarre`: las filas en las bandas. `_sobres`:
   `miembro_alto_2d` = retorno + meseta + banda − BD(45) − BD(90) por 
   `ancho_util + 2·(brida_largo − BD)`; `talon_2d` = `banda + pie − BD` por
   `trasera_au`.

**Modelo:** `params.scad`: `banda_trasera = 24`, `talon_pie = 20`, `brida_escalon
= 14`, `brida_largo = 40`, `prof_sup = 50`; mueren `canal_ancho`, `canal_fondo`,
`marco_trasera_ancho`, `radio_trasero` (`radios_perfil()[6] = radio_chapa`).
`sam17_case.scad`: `miembro_alto_2d/miembro_alto` (L + pestañas con escalón),
`talon_2d/talon`, `piel_trasera_2d` (alto, filas, muescas, sin escuadra),
`piel_trasera()` (y0 = t), `anclaje_piel_base/remate` en las bandas,
`bridas_anillo()` solo arriba, `centro_talon()`; mueren `miembro_bajo*`,
`marcos_trasera*`, `marco_trasera_*`, `escuadra_m3_*`, `centro_miembro_bajo`,
`centro_miembro_alto`, `miembro_x_trasera` → `x_trasera_int`. Budget: `_miembro_alto`,
`_talon`, `_cajas_miembro` → las dos L, `_bridas` (solo arriba, con escalón),
`bbox_desarrollo_miembro`/`_talon`, `_cajas_solidas`, `_caras_miembro`,
`_anclajes_miembro`, `guarda_retorno_meseta` y `guarda_tapa` (obstáculos).

**VERDE + romper:** bajar `banda_trasera` a 20 → ROJO por σ; poner
`brida_escalon` = 8 → ROJO por el M4 en el escalón; volver.

**Commit:** «La banda es el miembro: el techo sin costura, la trasera dentro del
canal y el talón sobre la tabla».

---

### Tarea 3 — el chasis a la tabla

**Puertas primero:** `guarda_chasis`: cuatro M4 del suelo en las orillas libres
(`chasis_tornillo_x` = 6.5 y `chasis_int_x − 6.5`, `chasis_tornillo_y` = 20 y
`chasis_int_y − 20`), a ≥ 1.5 D de la ranura de salida, del refuerzo y de las
paredes; `chasis_pie` = 0; mueren los M5 de pared. `chasis_agujeros()` y
`guarda_zocalo()` (check_dxf): los cuatro en `chasis_cuerpo_2d` y en
`bandeja_base_2d` (censo: 4 pies + 3 nariz + 3 talón + 4 chasis). Paticas
traseras en `centro_talon().x`.

**Modelo:** `chasis_cuerpo_2d` (fuera los M5 de pared, dentro los 4 del suelo),
`bandeja_base_2d` (+7 taladros), `x_chasis_frente()` desde el pie del talón,
`ch_pos`, `paticas()`. Params: `chasis_anclajes` muere; `chasis_tornillo_x/y`;
`chasis_pie = 0`; `chasis_holgura_larguero` se queda (la holgura al pie).

**Commit:** «El chasis se atornilla a la tabla: sus dos M5 apuntaban a la ranura
de un 2020 que murió el 27-08».

---

### Tarea 4 — export, BOM, piezas y renders

`cad/export.ps1` completo; `bom()` reescrito (piezas, tornillería 73 → 64,
roscas 12 por anillo, orden de montaje); `piezas.scad`/`piezas.py` (entran
`marcos_ventana`, `talon`; salen cinco); `render.py` y `piezas.py` corridos; los
dos PNG mirados — lo que se ve va a la spec §6 si difiere.

---

### Tarea 5 — los papeles y el cierre

README (piezas, BOM, orden de montaje corregido), PLIEGO rev. 25, RFQ rev. 24,
spec del case rev. 25, enmiendas de la spec §10; memoria; commit; PR; merge;
árbol principal al día; `.blend` de piezas regenerado en el árbol principal;
issues: el chasis (fijación muerta) y lo que quede abierto de la spec §9.
