# La trasera capturada y el talón como la nariz — plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** la trasera dentro de dos bolsillos fresados en los anillos, sin un
taladro, con el talón en espejo de la nariz y el techo con canal; en dos variantes
(banda / chaflán) para escoger mirando.

**Architecture:** el patrón del repo — cada cota vive en el `.scad` (dibuja) y en
`clearance_budget.py` (verifica), y `check_dxf.py` relee los DXF y cruza las dos.
Puerta primero en ROJO, modelo, VERDE, mutación.

**Tech Stack:** OpenSCAD, Python 3 (ezdxf), Blender 5 para los renders.

**Spec:** `docs/superpowers/specs/2026-08-29-trasera-capturada-talon-nariz-design.md`

## Global Constraints

- `params.scad` numérico puro; nada de expresiones.
- Nada fijo a menos de `tol_pmma + 0.5` = 1.7 de la cara interior de la trasera.
- Ningún tornillo visto; ningún taladro en el acrílico de la trasera.
- Las tres chapas del canto (nariz, talón, techo en B) cierran con chaflán 6 y
  labio de 13.
- Las dos variantes del techo pasan las puertas.

---

### Task 1: parámetros y puertas en rojo
- [ ] `params.scad`: `pared_rebaje_trasera` 3, `talon_labio` 13, `talon_pie` 20,
  `talon_pestana_*`, `radio_doblez_pestana` 1.5, `remate_trasero_chaflan` 1,
  `brida_largo` 34, `canal_trasero_*`.
- [ ] budget: `_bolsillo_trasero()`, `_trasera()`, `_talon()` nuevo, `_miembro_alto()`
  nuevo, `_cajas_solidas` con las cajas nuevas, `guarda_trasera_capturada()`,
  `guarda_talon()`, `guarda_miembro_alto()`, `guarda_marco_ventana` con el retiro
  nuevo; fuera `guarda_trasera_dentro`, `guarda_agarre`, `_anclajes_miembro`.
- [ ] correr: ROJO contra el .scad de #241.

### Task 2: el modelo
- [ ] `pts_contorno()` con chaflanes en P6 (y P5 con la variante), `costilla()` con el
  bolsillo y el rebaje a 17 atrás, `costilla_dorso_2d` con las líneas del bolsillo,
  `costado_2d` con el canto trasero a 17.15.
- [ ] `talon()`/`talon_2d()` en espejo de la nariz, con pestañas; `miembro_alto()`/
  `miembro_alto_2d()` con canal y variante; `piel_trasera_2d()` sin taladros y anclada
  a su campo; `piel_trasera()` en el bolsillo; `bom()`.
- [ ] budget VERDE (HUECO); mutaciones.

### Task 3: check_dxf y export
- [ ] `anillo_tiene_rebaje` (17 atrás), `anillo_tiene_bolsillo_trasero`,
  `anillo_tiene_chaflan` (P6/P5), `agujeros_donde_toca` (trasera cero, costado),
  `taladros_talon`, `pestanas_talon`, `cuerpos_dentro_del_anillo`, `_sobres`.
- [ ] `export.ps1` completo VERDE en las dos variantes.

### Task 4: renders
- [ ] `render.py` en B y en A (`sam17-case-trasera-A.png`), `piezas.py`.

### Task 5: papeles, PR
- [ ] README, PLIEGO, RFQ, enmiendas a las specs; commit, push, PR; revisor final.
