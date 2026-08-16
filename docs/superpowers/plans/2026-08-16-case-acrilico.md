# Case SAM17 (dos pisos, acrílico) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir la spec rev. 3 del case y el board de diseño aprobado en
artefactos fabricables: modelo OpenSCAD paramétrico → DXF de corte láser,
cupón de calibración, `clearance_budget.py`, plantilla KiCad de panel de
aluminio, render Blender y documentación de ensamblaje.

**Architecture:** Un solo modelo OpenSCAD (`sam17_case.scad`) con parámetros
en `params.scad` y un despachador `PART` que exporta cada plancha en 2D (DXF)
o el conjunto en 3D (STL). Un budget Python parsea `params.scad` (misma
fuente de verdad) y hace cumplir las holguras ANTES de cortar. El esqueleto
interno es perfil 2020 + tuercas T (mismo sistema que los paneles); los
standoffs M4 quedan para las pieles flotantes con junta de sombra.

**Tech Stack:** OpenSCAD (CLI, a instalar), Python 3.14 (en PATH), KiCad 10
(`kicad-cli` 10.0.3 + su Python con `pcbnew`), Blender 5.0 (headless),
PowerShell 5.1.

**Spec:** `docs/superpowers/specs/2026-08-15-case-design.md` (rev. 3).
Render de intención: `case/renders/propuesta-diseno-2026-08-16.png`.

## Global Constraints

- Constitución del SAM17 (`.specify/memory/constitution.md`) — innegociable:
  todo número con fuente o a «lo que NO está confirmado» (I); presupuestos =
  scripts con aserciones (II); comprobación antes del paso destructivo (III);
  script incompleto sale con código ≠ 0 (III corolario); se comprueba lo que
  importa, no un proxy (IV); fallo invisible peor que hueco visible (V).
- Unidades: **mm** y **grados** en todo el CAD; ángulos de cara **medidos
  desde la vertical** (convención del board, spec §4).
- Defaults de la spec §4: `ancho_total=500`, `alto_panel=190`,
  `angulo_inferior=12`, `angulo_superior=35`, `alto_frontal=50`,
  `t_acrilico=5`, `t_cheek=8`, `kerf=0.2`, `n_bulkheads=2`.
- Del board: `prof_inferior=350`, `prof_superior=250`.
- Separación entre centros de raíl por piso: **180 mm** (tornillos de panel a
  5 mm del borde, spec §6).
- Idioma de código/comentarios/commits: español, sin emoji, estilo de los
  `*_budget.py` existentes (`hardware/02-midi-cv/tuning_budget.py` es la
  referencia de estilo).
- Commits pequeños por task; mensajes en el estilo del repo (primera línea
  descriptiva en minúsculas-sentencia, cuerpo con el porqué).
- Rutas de herramientas: `kicad-cli` en
  `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`; Python de KiCad en
  `C:\Program Files\KiCad\10.0\bin\python.exe`; Blender en
  `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`; OpenSCAD
  (tras Task 1) en `C:\Program Files\OpenSCAD\openscad.exe`.
- Trabajar SIEMPRE en el worktree `.claude/worktrees/case-design` (rama
  `feat/case-design`). El checkout raíz lo usan otras sesiones.

---

### Task 1: Toolchain OpenSCAD + `params.scad` + enmienda §5/§9 de la spec

**Files:**
- Create: `case/cad/params.scad`
- Modify: `docs/superpowers/specs/2026-08-15-case-design.md` (§5, §9)

**Interfaces:**
- Produces: `params.scad` con TODOS los nombres de parámetro que consumen
  Tasks 2–6 (lista exacta abajo). `OPENSCAD` invocable en
  `C:\Program Files\OpenSCAD\openscad.exe`.

- [ ] **Step 1: Instalar OpenSCAD y verificar CLI**

```powershell
winget install --id OpenSCAD.OpenSCAD --silent --accept-package-agreements --accept-source-agreements
& "C:\Program Files\OpenSCAD\openscad.exe" --version
```
Expected: `OpenSCAD version 20xx...` (si winget falla, descargar el
instalador de https://openscad.org/downloads.html y repetir la verificación).

- [ ] **Step 2: Escribir `case/cad/params.scad`**

```openscad
// params.scad — unica fuente de verdad dimensional del case.
// Unidades: mm y grados. Angulos de cara MEDIDOS DESDE LA VERTICAL
// (convencion del board de diseno, spec §4 rev. 3).
// clearance_budget.py parsea este fichero: solo lineas `nombre = valor;`
// con valores numericos. No usar expresiones en este fichero.

// --- silueta (spec §4 + board 350 x ~380) ---
ancho_total     = 500;   // spec §4
alto_panel      = 190;   // spec §4, altura de panel de la tesis
angulo_inferior = 12;    // desde la vertical, cara de procesamiento
angulo_superior = 35;    // desde la vertical, cara de generacion
alto_frontal    = 50;    // zocalo delantero
prof_inferior   = 350;   // board: PROFUNDIDAD TOTAL
prof_superior   = 250;   // board: cota 250 del alzado lateral
paso_horizontal = 20;    // repisa entre cara inferior y superior

// --- materiales ---
t_acrilico = 5;    // planchas del cuerpo; MEDIR con calibre (spec §11)
t_cheek    = 8;    // costados portantes
t_panel    = 1.6;  // PCB de aluminio, espesor estandar JLCPCB
kerf       = 0.2;  // default; SE CALIBRA con el cupon (spec §11)

// --- sistema de paneles (spec §6) ---
rail            = 20;   // perfil 2020
inset_tornillo  = 5;    // tornillo de panel a 5 mm del borde
sep_railes      = 180;  // centros de rail por piso = 190 - 2*5

// --- esqueleto y herrajes ---
n_bulkheads      = 2;    // costados exteriores (3 si el vano flexa, spec §11)
d_M3_paso   = 3.4;  // agujero paso M3 (ISO holgura media)
d_M4_paso   = 4.5;  // agujero paso M4
d_M5_paso   = 5.5;  // agujero paso M5 (railes 2020 roscados en el alma)
gap_sombra  = 5;    // junta de sombra de las pieles flotantes
alto_pie    = 8;    // pie de goma bajo la base

// --- ventilacion con firma (spec §7) ---
vent_ancho_ranura = 4;   // ancho de la ranura-onda
vent_puente_min   = 4;   // puente minimo entre ranuras (fragilidad)
vent_periodo      = 40;  // periodo horizontal de cada onda

// --- lo que el budget vigila (spec §11: catalogos, no medidos) ---
alto_transformador  = 45;  // CATALOGO, no confirmado; medir pieza real
margen_transformador = 15; // spec §4
fondo_pcb_max       = 60;  // censo estimado de PCB mas honda, no confirmado
```

- [ ] **Step 3: Smoke test del CLI con los params**

```powershell
Set-Location case/cad
'include <params.scad>
cube([ancho_total, 10, 10]);' | Out-File -Encoding ascii smoke.scad
& "C:\Program Files\OpenSCAD\openscad.exe" -o smoke.stl smoke.scad
if ((Get-Item smoke.stl).Length -lt 100) { throw "STL vacio" }
Remove-Item smoke.scad, smoke.stl
```
Expected: sin excepción (STL > 100 bytes).

- [ ] **Step 4: Enmienda §5/§9 de la spec (esqueleto 2020, standoffs a pieles)**

En `docs/superpowers/specs/2026-08-15-case-design.md`, §5, sustituir el bullet
de bandejas por:

```markdown
- **Bandejas horizontales de acrílico** (base y entrepiso) atornilladas con
  tuercas T M3 a un **esqueleto de perfiles 2020** (los mismos del sistema de
  paneles: 2 largueros de base, 2 de entrepiso y 1 de remate superior, además
  de los 4 raíles de paneles). Un solo sistema de fijación para todo el
  instrumento; un standoff no puede sujetar una bandeja de 500 mm de vano.
- **Separadores (standoffs) de aluminio M4**: reservados a las pieles
  flotantes (junta de sombra de 5 mm) y a los puntos vista del sándwich — el
  ritmo visible de tornillería sigue siendo el ornamento permitido.
```

y en §9 añadir a la lista: `perfiles 2020 adicionales del esqueleto (5
piezas, largo = ancho útil)` y `tornillos M5 de botón (extremos de los 9
perfiles, alma del 2020 roscada M5)`.

- [ ] **Step 5: Commit**

```powershell
git add case/cad/params.scad docs/superpowers/specs/2026-08-15-case-design.md
git commit -m "params del case como fuente unica y enmienda del esqueleto a 2020"
```

---

### Task 2: `case/clearance_budget.py` — las holguras, ejecutables

**Files:**
- Create: `case/clearance_budget.py`

**Interfaces:**
- Consumes: `case/cad/params.scad` (Task 1), parseado con regex
  `^\s*(\w+)\s*=\s*(-?[0-9.]+)\s*;`.
- Produces: script que sale 0 en verde y ≠ 0 en rojo; función
  `perfil(p) -> dict` con claves `alto_total`, `prof_sup_min`,
  `alto_interior_inferior`, `ancho_util` que Task 6 y el README citan.

- [ ] **Step 1: Escribir el budget con un valor deliberadamente roto (rojo)**

Escribir `case/clearance_budget.py` completo, pero con
`alto_transformador = 45` sustituido temporalmente por `245` EN EL PARSE
(línea `params["alto_transformador"] = 245  # ROJO deliberado`) para ver
fallar la aserción antes de confiar en ella (Principio III):

```python
"""Presupuesto de holguras del case, en mm.

    python case/clearance_budget.py

Hermano de tuning_budget.py y ground_budget.py, pero mecanico: aqui lo que
se agota no son cents sino milimetros. La distincion que organiza esto:

  El modelo OpenSCAD (sam17_case.scad) DIBUJA; este script DECIDE si lo
  dibujado cabe. Los dos leen los mismos numeros (case/cad/params.scad,
  unica fuente de verdad), pero este recalcula la geometria con su propia
  trigonometria — si el .scad y el budget discrepan, uno de los dos miente
  y la autocomprobacion lo delata.

Convencion: angulos de cara medidos DESDE LA VERTICAL (spec §4 rev. 3).
Corre en verde ANTES de mandar nada a cortar (constitucion, Principio III).
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

PARAMS = Path(__file__).parent / "cad" / "params.scad"


def leer_params() -> dict[str, float]:
    texto = PARAMS.read_text(encoding="utf-8")
    pares = re.findall(r"^\s*(\w+)\s*=\s*(-?[0-9.]+)\s*;", texto, re.M)
    if len(pares) < 20:
        raise SystemExit(f"params.scad: solo {len(pares)} parametros parseados")
    return {k: float(v) for k, v in pares}


def perfil(p: dict[str, float]) -> dict[str, float]:
    """Vertices del perfil lateral (X = fondo hacia atras, Y = arriba)."""
    si, ci = math.sin(math.radians(p["angulo_inferior"])), math.cos(
        math.radians(p["angulo_inferior"]))
    ss, cs = math.sin(math.radians(p["angulo_superior"])), math.cos(
        math.radians(p["angulo_superior"]))
    y_entrepiso = p["alto_frontal"] + p["alto_panel"] * ci
    x_cara_inf = p["alto_panel"] * si
    x_cara_sup0 = x_cara_inf + p["paso_horizontal"]
    x_cara_sup1 = x_cara_sup0 + p["alto_panel"] * ss
    alto_total = y_entrepiso + p["alto_panel"] * cs
    return {
        "y_entrepiso": y_entrepiso,
        "alto_total": alto_total,
        "prof_sup_min": x_cara_sup1,
        "alto_interior_inferior": y_entrepiso - p["t_acrilico"],
        "ancho_util": p["ancho_total"] - 2 * p["t_cheek"],
    }


def autocomprobacion(p: dict[str, float]) -> None:
    """Caso hecho a mano (spec §4): 12/35 grados, panel 190, zocalo 50."""
    g = perfil({**p, "angulo_inferior": 12, "angulo_superior": 35,
                "alto_panel": 190, "alto_frontal": 50, "paso_horizontal": 20,
                "t_acrilico": 5, "ancho_total": 500, "t_cheek": 8})
    # A mano: 50 + 190*cos12 = 50 + 185.85 = 235.85
    assert abs(g["y_entrepiso"] - 235.85) < 0.05, g["y_entrepiso"]
    # A mano: 235.85 + 190*cos35 = 235.85 + 155.64 = 391.49
    assert abs(g["alto_total"] - 391.49) < 0.05, g["alto_total"]
    # A mano: 190*sin12 + 20 + 190*sin35 = 39.51 + 20 + 108.99 = 168.50
    assert abs(g["prof_sup_min"] - 168.50) < 0.05, g["prof_sup_min"]


# Censo de anchos minimos de panel por piso, mm. ESTIMADOS (spec §11):
# cierran cuando cada panel este dibujado. Fuente: conteo de mandos/jacks
# de los README de modulo + patch bay normalizado que anade jacks.
ANCHOS_PISO_SUP = {"MIDI/CV": 80, "VCO1": 90, "VCO2": 90, "VCO3": 90}
ANCHOS_PISO_INF = {"VCF": 100, "ADSR": 110, "VCA": 80, "MIXER": 100}
EXPANSION_MIN = 40  # sitio reservado a crecer, por piso


def main() -> int:
    p = leer_params()
    autocomprobacion(p)
    g = perfil(p)
    fallos: list[str] = []

    def exige(cond: bool, msg: str) -> None:
        (fallos.append if not cond else (lambda m: None))(msg)

    exige(g["alto_interior_inferior"]
          >= p["alto_transformador"] + p["margen_transformador"],
          "transformador no cabe en el piso inferior con margen")
    exige(p["prof_superior"] >= g["prof_sup_min"] + 10,
          "prof_superior no cubre la proyeccion de la cara superior + 10")
    exige(p["prof_inferior"] >= p["prof_superior"] + 60,
          "la repisa trasera del piso inferior queda menor de 60 mm")
    exige(p["fondo_pcb_max"] + 10 <= p["prof_superior"] - p["rail"],
          "la PCB mas honda del censo no cabe bajo la cara superior")
    exige(sum(ANCHOS_PISO_SUP.values()) + EXPANSION_MIN <= g["ancho_util"],
          "el piso superior no cabe en el ancho util")
    exige(sum(ANCHOS_PISO_INF.values()) + EXPANSION_MIN <= g["ancho_util"],
          "el piso inferior no cabe en el ancho util")
    exige(p["sep_railes"] == p["alto_panel"] - 2 * p["inset_tornillo"],
          "sep_railes no sale de alto_panel - 2*inset (spec §6)")
    exige(p["vent_puente_min"] >= 0.8 * p["t_acrilico"],
          "puente de ventilacion fragil para el espesor")

    print(f"perfil: alto_total={g['alto_total']:.1f}  "
          f"entrepiso={g['y_entrepiso']:.1f}  ancho_util={g['ancho_util']:.0f}")
    for f in fallos:
        print(f"ROJO: {f}")
    if fallos:
        return 2
    print("clearance_budget: VERDE")
    return 0


# Lo que este calculo NO cubre (y donde se cierra):
#   * rigidez/flexion del vano de 500 mm  -> cargar el prototipo (spec §11)
#   * par de apriete sobre acrilico       -> probeta del cupon (spec §11)
#   * termica de la fuente v2             -> spec PSU v2 y su validacion
#   * nesting de planchas en el stock     -> lienzo del Task 5, a ojo

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Verificar que FALLA con el valor roto**

Run: `python case/clearance_budget.py`
Expected: `ROJO: transformador no cabe...` y exit code 2
(`$LASTEXITCODE` = 2).

- [ ] **Step 3: Quitar la línea de rojo deliberado**

Eliminar `params["alto_transformador"] = 245  # ROJO deliberado`.

- [ ] **Step 4: Verificar VERDE**

Run: `python case/clearance_budget.py; echo $LASTEXITCODE`
Expected: `clearance_budget: VERDE`, exit 0, y el `perfil:` impreso con
`alto_total=391.5` aprox.

- [ ] **Step 5: Commit**

```powershell
git add case/clearance_budget.py
git commit -m "clearance_budget: las holguras del case dejan de ser prosa"
```

---

### Task 3: `sam17_case.scad` — perfil lateral, costados y despachador PART

**Files:**
- Create: `case/cad/sam17_case.scad`

**Interfaces:**
- Consumes: `params.scad` (Task 1).
- Produces: `module perfil_lateral()` (2D), `module costado()` (3D),
  `function pts_perfil()`, despachador `PART` (string) con valores
  `"assembly"` (default), `"costado"`, y los que añaden Tasks 4–5. Todas las
  planchas 2D se exportan con `PART="<pieza>_2d"`.

- [ ] **Step 1: Escribir el esqueleto con perfil y costado**

```openscad
// sam17_case.scad — consola de dos pisos en acrilico naranja (spec rev. 3).
// Fuente de verdad dimensional: params.scad. Este fichero DIBUJA;
// clearance_budget.py DECIDE. Angulos desde la vertical.
//
//   openscad -o out.stl -D 'PART="costado"'    sam17_case.scad
//   openscad -o out.dxf -D 'PART="costado_2d"' sam17_case.scad

include <params.scad>
PART = "assembly";
$fn = 48;

// vertices del perfil lateral (X = fondo, Y = arriba) — misma numeracion
// que clearance_budget.perfil(): p0..p8
function pts_perfil() =
    let (si = sin(angulo_inferior), ci = cos(angulo_inferior),
         ss = sin(angulo_superior), cs = cos(angulo_superior),
         ye = alto_frontal + alto_panel*ci,          // y entrepiso
         x2 = alto_panel*si,                          // fin cara inferior
         x3 = x2 + paso_horizontal,
         x4 = x3 + alto_panel*ss,
         yt = ye + alto_panel*cs)                     // alto total
    [[0,0],[0,alto_frontal],[x2,ye],[x3,ye],[x4,yt],
     [prof_superior,yt],[prof_superior,ye],[prof_inferior,ye],
     [prof_inferior,0]];

// puntos medios de rail por cara: [origen, direccion] de cada cara y
// centros a inset_tornillo y alto_panel-inset_tornillo sobre la cara,
// retirados hacia dentro t_panel + rail/2 segun la normal
function centros_rail() =
    let (P = pts_perfil(),
         caras = [[P[1], P[2]], [P[3], P[4]]],
         off = t_panel + rail/2)
    [for (c = caras, s = [inset_tornillo, alto_panel - inset_tornillo])
        let (d = (c[1]-c[0])/norm(c[1]-c[0]),      // unitario de la cara
             n = [d.y, -d.x])                       // normal hacia dentro
        c[0] + d*s + n*off];

// largueros del esqueleto (2020) que no son railes de panel:
// base delantera, base trasera, entrepiso delantero, entrepiso trasero,
// remate superior trasero. Centros [x, y]:
function centros_esqueleto() =
    let (P = pts_perfil(), r = rail/2)
    [[r + 2,               r],                       // base delantera
     [prof_inferior - r,   r],                       // base trasera
     [P[3].x + r,          P[3].y - r],              // entrepiso delantero
     [prof_inferior - r,   P[6].y - r],              // entrepiso trasero
     [prof_superior - r,   P[5].y - r]];             // remate superior

module perfil_lateral() { polygon(pts_perfil()); }

module costado_2d() {
    difference() {
        perfil_lateral();
        for (c = concat(centros_rail(), centros_esqueleto()))
            translate(c) circle(d = d_M5_paso + kerf);
    }
}

module costado() { linear_extrude(t_cheek) costado_2d(); }

module rail_2020(largo) { cube([rail, largo, rail], center = true); }

if (PART == "costado")         costado();
else if (PART == "costado_2d") costado_2d();
else if (PART == "assembly")   assembly();
else assert(false, str("PART desconocido: ", PART));

module assembly() {                    // crece en Tasks 4-5
    ancho_util = ancho_total - 2*t_cheek;
    costado();
    translate([0, ancho_total - t_cheek, 0]) costado();
    for (c = concat(centros_rail(), centros_esqueleto()))
        translate([c.x, t_cheek + ancho_util/2, c.y])
            rotate([90, 0, 0]) rotate([0, 0, 90])
                rail_2020(ancho_util);
}
```

Nota de orientación: los costados se modelan en el plano XZ del perfil y el
ancho corre en Y; `assembly()` ya lo hace así (el costado se extruye en Y por
defecto en OpenSCAD — `linear_extrude` va en Z, así que en `assembly()`
rota/traslada según haga falta; lo importante verificable es que los DXF 2D
son correctos y que el STL del conjunto se ve coherente en el render).

- [ ] **Step 2: Exportar y verificar costado**

```powershell
$scad = "C:\Program Files\OpenSCAD\openscad.exe"
& $scad -o build_costado.stl -D 'PART="costado"' case/cad/sam17_case.scad
& $scad -o build_costado.dxf -D 'PART="costado_2d"' case/cad/sam17_case.scad
if ((Get-Item build_costado.stl).Length -lt 5000) { throw "STL sospechosamente vacio" }
if ((Get-Content build_costado.dxf -Raw).Length -lt 2000) { throw "DXF sospechosamente vacio" }
Remove-Item build_costado.stl, build_costado.dxf
```
Expected: sin excepción y sin errores/asserts de OpenSCAD en consola.

- [ ] **Step 3: Cruce contra el budget**

Run: `python case/clearance_budget.py`
Expected: VERDE (mismos números que dibuja el scad; si aquí sale rojo, el
scad y el budget discrepan — parar y resolver antes de seguir).

- [ ] **Step 4: Commit**

```powershell
git add case/cad/sam17_case.scad
git commit -m "modelo del case: perfil de dos pisos, costados y esqueleto 2020"
```

---

### Task 4: Bandejas, zócalo y pieles traseras con las ondas

**Files:**
- Modify: `case/cad/sam17_case.scad`

**Interfaces:**
- Consumes: `pts_perfil()`, `centros_esqueleto()`, `ancho_util` (Task 3).
- Produces: `PART` nuevos: `bandeja_base_2d`, `bandeja_entrepiso_2d`,
  `zocalo_2d`, `piel_inferior_2d`, `piel_superior_2d`; módulo 2D
  `onda(tipo, largo)` con `tipo` ∈ `"sierra" | "triangulo" | "cuadrada"`.

- [ ] **Step 1: Añadir las planchas al scad**

```openscad
// --- planchas rectangulares del cuerpo (todas t_acrilico) -------------
// Agujeros M3 de tuerca T cada ~100 mm contra los largueros 2020.
module fila_agujeros(largo, y, paso = 100, d = d_M3_paso)
    for (x = [paso/2 : paso : largo - paso/4])
        translate([x, y]) circle(d = d + kerf);

module plancha(l, a) square([l, a]);   // l = ancho_util, a = fondo local

module bandeja_base_2d() {
    au = ancho_total - 2*t_cheek;
    difference() {
        plancha(au, prof_inferior - 2*rail - 4);
        fila_agujeros(au, rail/2);
        fila_agujeros(au, prof_inferior - 2*rail - 4 - rail/2);
        // ventilacion bajo el PSU (tercio derecho): onda cuadrada
        translate([au*0.68, (prof_inferior-2*rail-4)*0.35])
            onda("cuadrada", au*0.25);
    }
}

module bandeja_entrepiso_2d() {
    au = ancho_total - 2*t_cheek;
    P = pts_perfil();
    fondo = prof_inferior - P[3].x - 2*rail;
    difference() {
        plancha(au, fondo);
        fila_agujeros(au, rail/2);
        fila_agujeros(au, fondo - rail/2);
        // pasacables entre pisos: 3 oblongos de 40 x 12
        for (x = [au*0.2, au*0.5, au*0.8])
            translate([x, fondo/2]) hull()
                for (dx = [-14, 14]) translate([dx, 0]) circle(d = 12);
    }
}

module zocalo_2d() {
    au = ancho_total - 2*t_cheek;
    difference() {
        plancha(au, alto_frontal - alto_pie);
        fila_agujeros(au, rail/2);
    }
}

// --- pieles traseras flotantes (standoffs M4, junta de sombra) --------
module piel_inferior_2d() {
    au = ancho_total - 2*t_cheek - 2*gap_sombra;
    P = pts_perfil();
    alto = P[6].y - 2*gap_sombra;
    difference() {
        plancha(au, alto);
        for (c = [[15,15],[au-15,15],[15,alto-15],[au-15,alto-15]])
            translate(c) circle(d = d_M4_paso + kerf);
        translate([au*0.10, alto*0.62]) onda("triangulo", au*0.35);
        translate([au*0.55, alto*0.62]) onda("cuadrada",  au*0.35);
        // recorte IEC C14 con interruptor (bloque snap-in tipico
        // 48 x 27.5; CONFIRMAR contra el datasheet de la pieza comprada)
        translate([au - 70, 22]) square([48, 27.5]);
    }
}

module piel_superior_2d() {
    au = ancho_total - 2*t_cheek - 2*gap_sombra;
    P = pts_perfil();
    alto = P[4].y - P[6].y - 2*gap_sombra;
    difference() {
        plancha(au, alto);
        for (c = [[15,15],[au-15,15],[15,alto-15],[au-15,alto-15]])
            translate(c) circle(d = d_M4_paso + kerf);
        translate([au*0.15, alto*0.45]) onda("sierra", au*0.70);
    }
}

// --- la firma: ranuras con forma de onda -------------------------------
// Cada onda es una polilinea engordada vent_ancho_ranura, N periodos de
// vent_periodo. Puentes >= vent_puente_min los garantiza el periodo.
module onda(tipo, largo) {
    n = max(2, floor(largo / vent_periodo));
    a = vent_periodo * 0.35;            // amplitud vertical
    pts = tipo == "sierra" ?
            [for (i = [0:n-1], p = [[0,-a],[1,a]])
                [(i + p[0]) * vent_periodo, p[1]]] :
          tipo == "triangulo" ?
            [for (i = [0:n-1], p = [[0,-a],[0.5,a]])
                [(i + p[0]) * vent_periodo, p[1]]] :
            [for (i = [0:n-1], p = [[0,-a],[0.001,a],[0.5,a],[0.501,-a]])
                [(i + p[0]) * vent_periodo, p[1]]];
    for (i = [0 : len(pts) - 2])
        hull() {
            translate(pts[i])   circle(d = vent_ancho_ranura);
            translate(pts[i+1]) circle(d = vent_ancho_ranura);
        }
}
```

Añadir al despachador:

```openscad
else if (PART == "bandeja_base_2d")      bandeja_base_2d();
else if (PART == "bandeja_entrepiso_2d") bandeja_entrepiso_2d();
else if (PART == "zocalo_2d")            zocalo_2d();
else if (PART == "piel_inferior_2d")     piel_inferior_2d();
else if (PART == "piel_superior_2d")     piel_superior_2d();
```

- [ ] **Step 2: Exportar las cinco planchas y verificar**

```powershell
$scad = "C:\Program Files\OpenSCAD\openscad.exe"
foreach ($p in "bandeja_base_2d","bandeja_entrepiso_2d","zocalo_2d","piel_inferior_2d","piel_superior_2d") {
  & $scad -o "chk_$p.dxf" -D ('PART="' + $p + '"') case/cad/sam17_case.scad
  if ((Get-Content "chk_$p.dxf" -Raw).Length -lt 1500) { throw "$p vacio" }
  Remove-Item "chk_$p.dxf"
}
```
Expected: cinco exports sin error ni warnings de geometría degenerada.

- [ ] **Step 3: Commit**

```powershell
git add case/cad/sam17_case.scad
git commit -m "planchas del cuerpo y ranuras de ventilacion con las tres ondas"
```

---

### Task 5: Assembly completo, lienzo nesteado y `coupon.scad`

**Files:**
- Modify: `case/cad/sam17_case.scad`
- Create: `case/cad/coupon.scad`

**Interfaces:**
- Consumes: todos los módulos de Tasks 3–4.
- Produces: `PART="assembly"` (todo el case en 3D, planchas + 9 largueros
  2020 + paneles fantasma), `PART="assembly_acrilico"` y
  `PART="assembly_aluminio"` (STL separados por material para Blender,
  Task 8), `PART="lienzo_2d"` (todas las planchas colocadas en un
  rectángulo de plancha con 8 mm de margen), `PART="bom"` (solo `echo` de
  conteos). `coupon.scad` autónomo.

- [ ] **Step 1: Completar `assembly()` y añadir lienzo + bom**

`assembly()` coloca: 2 costados (extremos), las 5 planchas en su plano según
`pts_perfil()`, los 9 largueros (`centros_rail()` + `centros_esqueleto()`),
las 2 pieles con offset `gap_sombra` hacia dentro de la boca trasera, y
paneles fantasma (`%` modifier) de `t_panel` sobre las dos caras.
`assembly_acrilico()` = solo piezas de acrílico; `assembly_aluminio()` =
largueros + paneles fantasma sólidos. `lienzo_2d()` traslada las cinco
planchas + `costado_2d()` ×2 a una rejilla con separación 8 mm y un marco
`%square([1000, 600])` de referencia de plancha. `PART="bom"` hace:

```openscad
module bom() {
    au = ancho_total - 2*t_cheek;
    echo(str("BOM: larguero 2020 x", len(centros_rail()) + len(centros_esqueleto()),
             " de ", au, " mm"));
    echo(str("BOM: tornillo M5 boton x", 2*(len(centros_rail()) + len(centros_esqueleto()))));
    echo("BOM: standoff M4 x8 (pieles) + tornillo M4 boton x16 + arandela x16");
    echo(str("BOM: planchas t=", t_acrilico, ": base, entrepiso, zocalo, ",
             "piel inf, piel sup; costados t=", t_cheek, " x2"));
}
```

- [ ] **Step 2: Escribir `case/cad/coupon.scad`**

```openscad
// coupon.scad — se corta ANTES que cualquier plancha (spec §3/§10).
// Escaleras de agujero para M3/M4/M5, ranura de tuerca T y probeta de
// canto/apriete. Marcar el kerf ganador en case/README.md.
include <params.scad>
paso = 12;
module escalera(ds, y) for (i = [0 : len(ds)-1])
    translate([8 + i*paso, y]) circle(d = ds[i]);   // sin kerf: se mide crudo
difference() {
    square([100, 62]);
    escalera([2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5], 12);   // M3
    escalera([4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6], 27);   // M4
    escalera([5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6], 42);   // M5
    translate([8, 52]) square([30, 6.2]);  // ranura perfil 2020
    translate([55, 50]) square([40, 8]);   // lengueta de probeta de apriete
}
```

- [ ] **Step 3: Exportar assembly, lienzo, bom y coupon; verificar**

```powershell
$scad = "C:\Program Files\OpenSCAD\openscad.exe"
& $scad -o chk_asm.stl -D 'PART="assembly"' case/cad/sam17_case.scad
& $scad -o chk_lienzo.dxf -D 'PART="lienzo_2d"' case/cad/sam17_case.scad
& $scad -o chk_nul.stl -D 'PART="bom"' case/cad/sam17_case.scad 2>&1 | Select-String "BOM:"
& $scad -o chk_coupon.dxf case/cad/coupon.scad
if ((Get-Item chk_asm.stl).Length -lt 50000) { throw "assembly vacio" }
Remove-Item chk_asm.stl, chk_lienzo.dxf, chk_nul.stl, chk_coupon.dxf
```
Expected: 4 líneas `BOM:` en consola; exports sin errores.

- [ ] **Step 4: Commit**

```powershell
git add case/cad/sam17_case.scad case/cad/coupon.scad
git commit -m "assembly completo, lienzo de corte y cupon de calibracion"
```

---

### Task 6: `case/cad/export.ps1` — regeneración total con puertas de budget y de relectura

**Files:**
- Create: `case/cad/export.ps1`
- Create: `case/check_dxf.py`
- Modify: `case/clearance_budget.py` (eco de kerf + aserción de rango)

**Interfaces:**
- Consumes: despachador PART (Tasks 3–5), `clearance_budget.py` (Task 2).
- Produces: `case/plans/*.dxf` (7 piezas + lienzo + cupón),
  `case/renders/build/assembly_acrilico.stl` y `assembly_aluminio.stl`,
  y `case/check_dxf.py` (gate de relectura que consume el README de Task 9).
  Exit 0 solo si TODO se regeneró Y la relectura pasó; cualquier fallo →
  exit 1 y lo dice.

> Lección incorporada de `projects/vectorizer` (docs/dxf-dialect.md, destilada
> 2026-08-16, ver `.superpowers/sdd/2026-08-16-case-acrilico/lecciones-vectorizer-vina.md`):
> los fallos de unidades, cierre de paths y entidades descartadas son
> SILENCIOSOS — se valida contra el DXF **releído**, jamás contra el objeto
> que lo generó.

- [ ] **Step 0a: Eco de kerf en el budget**

En `case/clearance_budget.py`, dentro de `main()` junto al print de `perfil:`,
añadir:

```python
    print(f"kerf aplicado: {p['kerf']:+.2f} mm (firmado; cupon manda)")
    exige(-0.5 <= p["kerf"] <= 0.5,
          "kerf fuera de rango fisico [-0.5, +0.5] mm")
```

(Lección L9: un override de kerf equivocado corrompe todos los agujeros con
exit 0 si nadie lo imprime.)

- [ ] **Step 0b: Escribir `case/check_dxf.py`**

```python
"""Relee los DXF exportados y verifica lo que el laser va a ver.

    python case/check_dxf.py

Leccion de projects/vectorizer (docs/dxf-dialect.md): unidades, cierre de
paths y entidades descartadas fallan EN SILENCIO. Se valida contra el
archivo RELEIDO con ezdxf, jamas contra el objeto que lo genero. Corre
dentro de export.ps1, despues de exportar y antes de dar el lote por bueno
(Principio III). Requiere: python -m pip install ezdxf
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import ezdxf

PLANS = Path(__file__).parent / "plans"

# sobre esperado por pieza, mm: (w_min, w_max, h_min, h_max) con margen
SOBRES = {
    "costado_2d":          (330, 370, 370, 410),
    "bandeja_base_2d":     (460, 500, 290, 320),
    "bandeja_entrepiso_2d": (460, 500, 235, 265),
    "zocalo_2d":           (460, 500, 30, 55),
    "piel_inferior_2d":    (450, 490, 210, 240),
    "piel_superior_2d":    (450, 490, 130, 160),
    "coupon":              (90, 110, 50, 75),
}


def revisar(nombre: str, sobre) -> list[str]:
    f: list[str] = []
    doc = ezdxf.readfile(PLANS / f"{nombre}.dxf")
    ents = list(doc.modelspace())
    if not ents:
        return [f"{nombre}: DXF sin entidades"]
    grados: Counter = Counter()   # paridad de extremos de LINEs sueltas
    xs: list[float] = []
    ys: list[float] = []

    def punto(x, y):
        xs.append(x); ys.append(y)
        return (round(x, 3), round(y, 3))

    for e in ents:
        t = e.dxftype()
        if t == "LINE":
            grados[punto(e.dxf.start.x, e.dxf.start.y)] += 1
            grados[punto(e.dxf.end.x, e.dxf.end.y)] += 1
        elif t == "LWPOLYLINE":
            pts = e.get_points("xy")
            for x, y in pts:
                punto(x, y)
            cerrado = e.closed or (
                len(pts) > 2
                and abs(pts[0][0] - pts[-1][0]) < 1e-6
                and abs(pts[0][1] - pts[-1][1]) < 1e-6)
            if not cerrado:
                f.append(f"{nombre}: LWPOLYLINE sin cerrar")
        elif t in ("CIRCLE", "ARC"):
            punto(e.dxf.center.x - e.dxf.radius, e.dxf.center.y - e.dxf.radius)
            punto(e.dxf.center.x + e.dxf.radius, e.dxf.center.y + e.dxf.radius)
            if t == "ARC":
                f.append(f"{nombre}: ARC suelto (posible contorno abierto)")
    sueltos = [p for p, n in grados.items() if n % 2]
    if sueltos:
        f.append(f"{nombre}: {len(sueltos)} extremos de LINE sin pareja "
                 f"(contorno abierto), p.ej. {sueltos[:3]}")
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    ancho_ok = sobre[0] <= w <= sobre[1] or sobre[0] <= h <= sobre[1]
    alto_ok = sobre[2] <= h <= sobre[3] or sobre[2] <= w <= sobre[3]
    if not (ancho_ok and alto_ok):
        f.append(f"{nombre}: bbox {w:.1f} x {h:.1f} mm fuera del sobre "
                 f"{sobre} (unidades mal? factor 25.4?)")
    ins = doc.header.get("$INSUNITS", 0)
    if ins not in (0, 4):
        f.append(f"{nombre}: $INSUNITS={ins} (ni ausente ni mm)")
    print(f"  {nombre}: {len(ents)} entidades, bbox {w:.1f} x {h:.1f} mm")
    return f


def main() -> int:
    fallos: list[str] = []
    for nombre, sobre in SOBRES.items():
        ruta = PLANS / f"{nombre}.dxf"
        if not ruta.exists():
            fallos.append(f"{nombre}: FALTA el DXF")
            continue
        fallos += revisar(nombre, sobre)
    for m in fallos:
        print(f"ROJO: {m}")
    if fallos:
        return 2
    print("check_dxf: VERDE (unidades mm implicitas: decirselo al servicio)")
    return 0


# Lo que NO cubre: lienzo_2d (marco de referencia, piezas repetidas),
# self-intersections, orden de corte, y la pieza fisica (eso es el cupon).

if __name__ == "__main__":
    sys.exit(main())
```

Nota de realidad: OpenSCAD 2021.01 exporta DXF como soup de LINEs o
LWPOLYLINEs según versión — el script cubre ambos; el implementador verifica
empíricamente cuál emite y lo dice en su reporte. Si un sobre de SOBRES no
cuadra con la pieza real exportada, el implementador ajusta EL SOBRE (con el
número medido, no a ojo) y lo reporta — los sobres son control de 25.4×/escala,
no cotas de diseño. Requiere `python -m pip install ezdxf` (anotarlo en el
README en Task 9).

- [ ] **Step 1: Escribir el script**

```powershell
# export.ps1 — regenera DXF de corte y STL de render desde el modelo.
# Constitucion, Principio III: el budget corre ANTES y un export a medias
# sale con codigo de error, para que no se confunda con terminado.
$ErrorActionPreference = "Stop"
$repo = Split-Path (Split-Path $PSScriptRoot)
$scad = "C:\Program Files\OpenSCAD\openscad.exe"
if (-not (Test-Path $scad)) { $scad = (Get-Command openscad).Source }

python (Join-Path $repo "case/clearance_budget.py")
if ($LASTEXITCODE -ne 0) { Write-Error "budget en ROJO: no se exporta nada"; exit 1 }

$plans = Join-Path $repo "case/plans"
$build = Join-Path $repo "case/renders/build"
New-Item -ItemType Directory -Force $plans, $build | Out-Null

$piezas = "costado_2d","bandeja_base_2d","bandeja_entrepiso_2d",
          "zocalo_2d","piel_inferior_2d","piel_superior_2d","lienzo_2d"
$fallos = 0
foreach ($p in $piezas) {
  $out = Join-Path $plans "$p.dxf"
  # ojo: comillas escapadas — PowerShell 5.1 despoja las internas sin \ (fallo silencioso, verificado en Task 3)
  & $scad -o $out -D ('PART=\"' + $p + '\"') (Join-Path $PSScriptRoot "sam17_case.scad")
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $out) -or (Get-Item $out).Length -lt 1000) {
    Write-Warning "FALLO: $p"; $fallos++
  }
}
& $scad -o (Join-Path $plans "coupon.dxf") (Join-Path $PSScriptRoot "coupon.scad")
if ($LASTEXITCODE -ne 0) { $fallos++ }
foreach ($m in "assembly_acrilico","assembly_aluminio") {
  $out = Join-Path $build "$m.stl"
  & $scad -o $out -D ('PART=\"' + $m + '\"') (Join-Path $PSScriptRoot "sam17_case.scad")
  if ($LASTEXITCODE -ne 0 -or (Get-Item $out).Length -lt 10000) {
    Write-Warning "FALLO: $m"; $fallos++
  }
}
if ($fallos -gt 0) { Write-Error "$fallos exports fallidos"; exit 1 }

# puerta de relectura: validar lo que el laser va a ver, no lo que dibujamos
python (Join-Path $repo "case/check_dxf.py")
if ($LASTEXITCODE -ne 0) { Write-Error "check_dxf en ROJO: no se manda a cortar"; exit 1 }
Write-Output "export completo: $($piezas.Count + 3) artefactos regenerados y releidos"
```

- [ ] **Step 2: Correr y verificar la ruta feliz**

Primero: `python -m pip install ezdxf` (dependencia de check_dxf.py).
Run: `powershell -File case/cad/export.ps1; echo $LASTEXITCODE`
Expected: `export completo: 10 artefactos regenerados y releidos`, exit 0,
`case/plans/` con 8 DXF + `case/renders/build/` con 2 STL, y las líneas
`  <pieza>: N entidades, bbox W x H mm` + `check_dxf: VERDE` en la salida.

- [ ] **Step 3: Verificar la ruta de fallo (Principio III)**

Renombrar temporalmente `coupon.scad` a `coupon.scad.off`, correr de nuevo,
esperar exit 1 y mensaje de fallo; restaurar el nombre y correr una vez más
hasta exit 0.

- [ ] **Step 4: Commit (incluye los artefactos, como los gerbers)**

```powershell
git add case/cad/export.ps1 case/plans/ case/renders/build/
git commit -m "export reproducible: DXF de corte y STL de render con puerta de budget"
```

---

### Task 7: Plantilla KiCad del panel de aluminio

**Files:**
- Create: `case/panels/build_template.py`
- Create (generado): `case/panels/panel-template.kicad_pcb`

**Interfaces:**
- Consumes: convenciones spec §6 (alto 190, tornillos a 5 mm de borde,
  ancho parametrizable).
- Produces: `build_template.py --ancho 100` genera el `.kicad_pcb`; los
  módulos futuros COPIAN la plantilla. El artefacto es el script
  (constitución).

- [ ] **Step 1: Escribir el generador con pcbnew de KiCad 10**

```python
"""Genera panel-template.kicad_pcb: panel de aluminio de modulo del SAM17.

    "C:/Program Files/KiCad/10.0/bin/python.exe" build_template.py [--ancho 100]

Alto fijo 190 mm (spec §6); agujeros de tornillo M3 a 5 mm de los bordes
superior e inferior (centros de rail a 180 mm); esquinas redondeadas 2 mm
via linea de contorno; capa F.Silkscreen con el rotulo de plantilla.
Fabricacion: PCB de aluminio 1.6 mm, serigrafia blanca (spec §2).
"""
import argparse
import sys

import pcbnew

ALTO = 190.0
INSET = 5.0


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ancho", type=float, default=100.0)
    ancho = ap.parse_args().ancho

    board = pcbnew.CreateEmptyBoard()
    # contorno
    pts = [(0, 0), (ancho, 0), (ancho, ALTO), (0, ALTO)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(mm(pts[i][0]), mm(pts[i][1])))
        seg.SetEnd(pcbnew.VECTOR2I(mm(pts[(i+1) % 4][0]), mm(pts[(i+1) % 4][1])))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.1))
        board.Add(seg)
    # 4 agujeros M3 no plateados (NPTH) en los centros de rail
    for x in (INSET, ancho - INSET):
        for y in (INSET, ALTO - INSET):
            fp = pcbnew.FOOTPRINT(board)
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            pad = pcbnew.PAD(fp)
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
            pad.SetDrillSize(pcbnew.VECTOR2I(mm(3.2), mm(3.2)))
            pad.SetSize(pcbnew.VECTOR2I(mm(3.2), mm(3.2)))
            pad.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.Add(pad)
            board.Add(fp)
    # rotulo de plantilla
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText("SAM17 PANEL TEMPLATE")
    txt.SetPosition(pcbnew.VECTOR2I(mm(ancho / 2), mm(ALTO / 2)))
    txt.SetLayer(pcbnew.F_SilkS)
    board.Add(txt)

    out = "panel-template.kicad_pcb"
    pcbnew.SaveBoard(out, board)
    print(f"escrito {out} ({ancho} x {ALTO} mm)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Nota: la API de pcbnew cambia entre majors; si un nombre no existe en
KiCad 10, buscar el equivalente con
`python -c "import pcbnew; print([n for n in dir(pcbnew) if 'NPTH' in n])"`
y ajustar — el criterio de aceptación es el Step 2, no el nombre exacto.

- [ ] **Step 2: Generar y verificar con kicad-cli**

```powershell
Set-Location case/panels
& "C:\Program Files\KiCad\10.0\bin\python.exe" build_template.py --ancho 100
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export svg --output chk.svg --layers "Edge.Cuts,F.Silkscreen" panel-template.kicad_pcb
if ($LASTEXITCODE -ne 0) { throw "kicad-cli no pudo leer la plantilla" }
Remove-Item chk.svg
Set-Location ../..
```
Expected: `.kicad_pcb` generado y legible por `kicad-cli` (exit 0).

- [ ] **Step 3: Commit**

```powershell
git add case/panels/build_template.py case/panels/panel-template.kicad_pcb
git commit -m "plantilla de panel de aluminio: el artefacto es el script"
```

---

### Task 8: Render Blender del conjunto

**Files:**
- Create: `case/renders/render.py`
- Create (generado): `case/renders/sam17-case.png`

**Interfaces:**
- Consumes: `case/renders/build/assembly_acrilico.stl` y
  `assembly_aluminio.stl` (Task 6).
- Produces: `sam17-case.png` (1600×1200, Cycles) — contraste visual contra
  `propuesta-diseno-2026-08-16.png` (el board manda en lenguaje, el STL en
  geometría).

- [ ] **Step 1: Escribir el script headless**

```python
"""Render del case: acrilico naranja translucido + aluminio.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" -b -P render.py
"""
import os

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)


def importar(nombre):
    ruta = os.path.join(AQUI, "build", nombre + ".stl")
    try:
        bpy.ops.wm.stl_import(filepath=ruta)          # Blender 4/5
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=ruta)        # por si acaso
    return bpy.context.selected_objects[0]


def mat(nombre, **bsdf):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    n = m.node_tree.nodes["Principled BSDF"]
    for k, v in bsdf.items():
        n.inputs[k].default_value = v
    return m


acr = importar("assembly_acrilico")
acr.data.materials.append(mat(
    "acrilico_naranja", **{
        "Base Color": (1.0, 0.35, 0.05, 1.0),
        "Roughness": 0.08,
        "Transmission Weight": 0.85,
    }))
alu = importar("assembly_aluminio")
alu.data.materials.append(mat(
    "aluminio", **{"Base Color": (0.85, 0.86, 0.88, 1.0),
                   "Metallic": 1.0, "Roughness": 0.35}))

esc = bpy.context.scene
esc.render.engine = "CYCLES"
esc.cycles.samples = 256
esc.render.resolution_x, esc.render.resolution_y = 1600, 1200
esc.render.filepath = os.path.join(AQUI, "sam17-case.png")

bpy.ops.object.camera_add(location=(900, -700, 500),
                          rotation=(1.15, 0, 0.9))
esc.camera = bpy.context.object
bpy.ops.object.light_add(type="AREA", location=(400, -600, 800))
bpy.context.object.data.energy = 4e6
bpy.context.object.data.size = 600
bpy.ops.object.light_add(type="AREA", location=(-500, -300, 400))
bpy.context.object.data.energy = 1.5e6
bpy.context.object.data.size = 400
esc.world = bpy.data.worlds.new("fondo")
esc.world.use_nodes = True
esc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.025, 1)

bpy.ops.render.render(write_still=True)
print("render escrito:", esc.render.filepath)
```

Nota: si en Blender 5 el input se llama distinto a `Transmission Weight`,
listar con `print([i.name for i in n.inputs])` y ajustar; el criterio de
aceptación es el Step 2. Encuadre/energías: iterar hasta que el case entre
completo en cuadro — son dos números, no una ciencia.

- [ ] **Step 2: Renderizar y verificar**

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" -b -P case/renders/render.py
if ((Get-Item case/renders/sam17-case.png).Length -lt 100kb) { throw "render vacio o negro" }
```
Expected: exit 0, PNG > 100 KB; abrir el PNG y comprobar A OJO que se ven
dos pisos, naranja translúcido y largueros — contra el board aprobado.

- [ ] **Step 3: Commit**

```powershell
git add case/renders/render.py case/renders/sam17-case.png
git commit -m "render headless del conjunto en Blender"
```

---

### Task 9: Documentación — `case/README.md`, módulo 8 y README raíz

**Files:**
- Modify: `case/README.md` (reescritura completa)
- Modify: `docs/modules/08-case-panels.md` (nota de sustitución al inicio)
- Modify: `README.md` (fila «Cajón y paneles» de la tabla de módulos)

**Interfaces:**
- Consumes: salida `PART="bom"` (Task 5), `perfil:` impreso por el budget
  (Task 2), procedimiento del cupón (Task 5).

- [ ] **Step 1: Reescribir `case/README.md`**

Estructura obligatoria (contenido real, con los números que imprimen
`clearance_budget.py` y `PART="bom"` en el momento de ejecutar):

```markdown
# Case SAM17 — consola de dos pisos en acrílico naranja

Spec: ../docs/superpowers/specs/2026-08-15-case-design.md (rev. 3)
Board de intención: renders/propuesta-diseno-2026-08-16.png

## Regenerar todo
    python -m pip install ezdxf   # una vez; lo usa check_dxf.py
    powershell -File cad/export.ps1
(corre clearance_budget.py ANTES de exportar y check_dxf.py DESPUÉS —
relee los DXF como los verá el láser; si cualquiera está en rojo, exit 1.
Los DXF van en mm; decírselo explícito al servicio de corte.)

## Procedimiento del cupón — OBLIGATORIO antes de cortar planchas
1. Cortar plans/coupon.dxf en el acrílico REAL con la máquina REAL.
2. Probar tornillos M3/M4/M5 en las escaleras; anotar el diámetro que
   entra firme sin forzar. kerf = diámetro_dibujado − diámetro_que_ajusta.
3. Probar la ranura con el perfil 2020 y la lengüeta con arandela+tuerca
   (apretar hasta marcar, NO hasta fisurar; anotar sensación de tope).
3b. **Confirmación anti-circular** (lección de projects/vectorizer): el kerf
   elegido en el paso 2 se confirma con un ajuste INDEPENDIENTE — la ranura
   del 2020 del paso 3 y un tornillo en una escalera DISTINTA de la que lo
   fijó. Medir los mismos agujeros que definieron el kerf siempre "pasa".
4. Registrar aquí: fecha, proveedor, material, espesor MEDIDO con calibre,
   máquina, kerf medido → actualizar params.scad y re-exportar.

| fecha | proveedor | material | espesor medido | máquina | kerf |
|-------|-----------|----------|----------------|---------|------|
| (pendiente) | | | | | |

## BOM de herrajes
(tabla desde la salida de `PART="bom"` + IEC C14 con fusible, espárrago M4
+ cable verde/amarillo + terminales de ojal, pies de goma, tuercas T M3 y
tornillería — cantidades exactas de la salida del modelo)

## Orden de ensamblaje
costados → largueros 2020 (M5) → bandejas y zócalo (tuercas T M3) →
electricidad y bonding (bloque IEC fijo, espárrago junto al PSU) →
pieles traseras (standoffs M4, junta de sombra) → paneles (tuercas T M3).

## Estado
- [x] Modelo paramétrico + DXF de corte
- [x] Cupón de calibración
- [x] clearance_budget.py en verde
- [x] Plantilla de panel KiCad
- [x] Render del conjunto
- [ ] Cupón cortado y kerf registrado (bloquea el corte de planchas)
- [ ] Planchas cortadas y ensayo de ensamblaje
```

- [ ] **Step 2: Nota de sustitución en `docs/modules/08-case-panels.md`**

Añadir tras el título:

```markdown
> **Sustituido**: el diseño vigente del case es la consola de dos pisos en
> acrílico (spec `docs/superpowers/specs/2026-08-15-case-design.md`, rev. 3;
> implementación en `case/`). Este documento queda como referencia de la
> tesis. Las convenciones de rotulación siguen vigentes y las hereda la
> plantilla `case/panels/`.
```

- [ ] **Step 3: Fila del README raíz**

En la tabla de módulos del `README.md`, cambiar la fila «Cajón y paneles»:
`Madera + lámina galv.` → `Acrílico naranja + paneles PCB de aluminio`.

- [ ] **Step 4: Verificar enlaces y commit**

Comprobar que cada ruta citada en los tres ficheros existe (`Test-Path`).

```powershell
git add case/README.md docs/modules/08-case-panels.md README.md
git commit -m "documentacion del case: cupon, BOM, ensamblaje y sustitucion del modulo 8"
```

---

### Task 10: Cierre de tanda — regeneración limpia, PR e issues

**Files:**
- Ninguno nuevo (verificación + GitHub).

- [ ] **Step 1: Regeneración desde cero**

```powershell
Remove-Item case/plans/*.dxf, case/renders/build/*.stl
powershell -File case/cad/export.ps1
git status --short   # solo debe haber regenerados identicos o vacio
```
Expected: exit 0 y `git status` sin diffs inesperados (los DXF/STL
regenerados deben ser idénticos byte a byte o, si OpenSCAD mete timestamps,
documentarlo en case/README.md y excluir la línea del diff esperado).

- [ ] **Step 2: Budget y checklist final**

```powershell
python case/clearance_budget.py
```
Expected: VERDE. Repasar spec §10 punto a punto contra lo hecho.

- [ ] **Step 3: Push y PR**

```powershell
git push -u origin feat/case-design
gh pr create --title "Case de dos pisos en acrilico: modelo, cupon, budget y plantilla de panel" --body-file - <<'EOF'
(resumen: spec rev. 3 implementada; leer .github/PULL_REQUEST_TEMPLATE.md
y rellenar sus secciones; citar: budget en verde, export reproducible,
cupon obligatorio antes de cortar, enmienda §5 esqueleto 2020)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
```
(El template real del repo manda; leerlo antes de crear el PR.)

- [ ] **Step 4: Issues de lo aplazado (Principio VI, con evidencia)**

```powershell
gh issue create --title "Cortar el cupon y registrar el kerf real" --body "Bloquea el corte de planchas. Evidencia: case/README.md tabla de kerf vacia; spec rev.3 §3/§10. Criterio de cierre: tabla con fecha/proveedor/espesor/kerf y params.scad actualizado."
gh issue create --title "Plugin companero VST/CLAP (nih-plug)" --body "Spec rev.3 §12; pivote de computo PR #30. Flujo spec-kit (firmware). Criterio: specify->plan->tasks en .specify/."
gh issue create --title "Iluminacion WS2812 del interior" --body "La fuente v2 ya reserva +5V digital (spec PSU v2). El translucido difunde. Criterio: diseno de tira/controlador y paso de cableado usado."
gh issue create --title "Tapa de transporte y patas de angulo" --body "Spec rev.3 §12, fuera de alcance de esta tanda. Criterio: diseno propio con su budget si toca."
gh issue create --title "Censo real de fondos de PCB por modulo" --body "clearance_budget.py usa fondo_pcb_max=60 estimado (spec §11). Criterio: tabla modulo->fondo medido de cada PCB publicada y assert actualizado."
```

- [ ] **Step 5: Marcar el plan**

Actualizar este fichero con todos los checkboxes en `[x]` y commitear:

```powershell
git add docs/superpowers/plans/2026-08-16-case-acrilico.md
git commit -m "plan del case ejecutado"
git push
```

---

## Self-review del plan (hecho al escribirlo)

- **Cobertura de spec**: §3 cupón → Tasks 5/9/10; §4 budget → Task 2; §5–§6
  geometría/raíles → Tasks 3–5 (+ enmienda 2020 en Task 1); §7 IEC/ondas →
  Task 4; §8 archivos/export → Task 6; plantilla panel → Task 7; render →
  Task 8; §10 verificación → Tasks 6/10; §11 no-confirmados → constantes
  marcadas en params.scad y budget; §12 issues → Task 10.
- **Sin placeholders**: todos los pasos llevan código o comando concreto;
  las dos notas de "ajustar nombre de API" (pcbnew, Blender) dan el comando
  de descubrimiento y el criterio de aceptación — son tolerancia a versión,
  no trabajo sin definir.
- **Consistencia de nombres**: `PART` values idénticos entre Tasks 3–6;
  `perfil()`/`pts_perfil()` con la misma numeración p0–p8; rutas de
  herramientas centralizadas en Global Constraints.
