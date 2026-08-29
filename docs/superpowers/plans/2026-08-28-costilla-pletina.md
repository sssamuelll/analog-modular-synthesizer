# La costilla de pletina mecanizada — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** La costilla del SAM17 deja de ser chapa plegada de 1.5 y pasa a ser un anillo
fresado de pletina de 14 mm con el acrílico coplanar en su ventana y sin un tornillo en
la cara vista — y el render lo enseña.

**Architecture:** OpenSCAD paramétrico (`case/cad/params.scad` cotas,
`case/cad/sam17_case.scad` modelo + desarrollos 2D → DXF) con dos presupuestos
ejecutables en Python que SON la suite de tests: `case/clearance_budget.py` (geometría,
estructura, aire) y `case/check_dxf.py` (relee los DXF exportados). Cada cota vive en
`params.scad` y tiene una **gemela** en Python; las gemelas se cruzan releyendo el DXF.
El render es `case/renders/render.py` (Blender 5.0, Cycles) sobre los STL que exporta
`case/cad/export.ps1`.

**Tech Stack:** OpenSCAD 2021+, Python 3.13 (stdlib + ezdxf en check_dxf), PowerShell
5.1 para el export, Blender 5.0 para el render. **No hay pytest ni framework de tests:
las puertas son los tests. No se crean ficheros `test_*.py`.**

**Spec:** `docs/superpowers/specs/2026-08-28-costilla-pletina-design.md` (aprobada por
Samuel el 2026-08-28, secciones 3–6). Enmienda que este plan introduce y aplica en la
Tarea 1: `t_placa` pasa de 4 a **6** (ver Ruling R1).

## Global Constraints

- **TDD de hardware, sin excepción:** la puerta se escribe PRIMERO, se corre y se ve en
  ROJO por la razón correcta; luego se toca el modelo; se ve VERDE; y se rompe a propósito
  al menos una vez para probar que muerde. Revertir una rotura **con copia** (`cp`), nunca
  con `git checkout <fichero>` — dos veces ese comando borró trabajo sin commitear.
- **Verde se mide corriendo los dos presupuestos ENTEROS:** `python case/clearance_budget.py`
  y `python case/check_dxf.py` desde la raíz del worktree, y no lanzan. Nunca una puerta
  suelta, nunca `except AssertionError: pass`.
- **El export completo es parte de verde:** `powershell -ExecutionPolicy Bypass -File case/cad/export.ps1`
  corre el budget, exporta DXF + STL, corre check_dxf y termina con `export completo`.
- **Cada tarea visible termina con los dos renders regenerados** (`case/renders/render.py`)
  y **commiteados**: Samuel decide mirando (`renders-son-el-idioma`).
- **Ningún número de memoria.** Cada cota del plan cita la spec o el modelo; si una hay
  que derivarla, se deriva corriendo el modelo y se escribe de dónde salió.
- **`t_costilla = 1.5` y `radio_doblez_costilla = 3` NO se tocan ni se renombran:** son
  el espesor y el radio de la chapa de los TRES MIEMBROS (~140 usos). Solo cambia su
  comentario. El anillo tiene sus propios parámetros (`t_anillo`, …).
- **Nada atraviesa la cara vista del anillo.** Todo tornillo entra por la cara interior a
  rosca ciega, o por el canto inferior (tabla).
- Español de Venezuela en comentarios, mensajes de puerta y commits (tuteo, nunca voseo).
  Los comentarios del repo explican POR QUÉ, no QUÉ, y conservan la historia de la cota.
- Commits en el estilo del repo: título = qué pasó en una frase con verbo; cuerpo = por qué,
  qué se midió, qué queda abierto. Sin prefijos `feat:`.
- Modelos de subagente: Tareas 1–4 y la revisión final en **opus**; Tareas 5–6 en
  **sonnet**. Codex está retirado en este repo.

## El reparto de motores

| paso | quién |
|---|---|
| escribir la puerta (el contrato) y verla en ROJO | el implementador, transcribiendo el código de este plan sin cambiar los asserts |
| tocar el modelo hasta VERDE | el implementador |
| correr las DOS puertas + export + render | el implementador |
| romper la puerta a propósito y revertir con `cp` | el implementador |
| leer el diff entero y verificar que ningún assert se aflojó | el controlador (`git diff -U0 | grep '^-' | grep assert`) |
| revisión de la tarea | task-reviewer en opus |

## Rulings de plan (decisiones que la spec no cerró)

- **R1 — `t_placa` = 6, no 4.** El M4 del riel entra en la placa desde el lado del anillo
  y su cabeza tiene que quedar **dentro** de la placa: a z < 14 hay acrílico hasta
  z = 3 + 9.2 + 1 = 13.2 en el peor caso, y sobre la franja hay anillo macizo. Una placa
  de 4 con cajeado de 2.5 deja 1.5 mm bajo la cabeza; una de 6 deja 3.5. Cabeza de
  botón ISO 7380 (altura 2.2), cajeado Ø8 × 2.5. Coste: +4 mm más de ancho
  (`ancho_total` = 568.62 en vez de 564.62). Se enmienda la spec §3/§5 en la Tarea 1.
- **R2 — La placa de los dos rieles 1U es UNA por lado**, 50 × 26 × 6, con las dos
  roscas ciegas a ±12 del centro de la boca y los dos cajeados en los centros de riel.
  Dos placas de 28 sobre la franja del valle (61.47 de largo) chocan entre sí y con la
  pestaña de la banda; una sola cabe. Coste si sale mal: una placa más larga que
  mecanizar.
- **R3 — La bahía no ancla al anillo: ancla a la placa 1U.** Sus alas acaban 6 mm antes
  de la cara interior del anillo y una lengüeta doblada de cada ala se atornilla a la
  placa con dos M4 a rosca en la placa (6 mm de pletina). El eje del riel 1U cae a ~16
  mm de la silueta — en la zona del rebaje, donde el anillo solo tiene 3 mm de labio — y
  una brida de chapa de 1.5 no puede alojar la cabeza del M4. La placa es el nodo.
- **R4 — `railes_dentro_del_costado()` cambia de sujeto:** con el acrílico retranqueado
  14.5, los rieles (a 4 de la silueta por su cara exterior) ya no están dentro del
  acrílico ni tienen por qué. Lo que los rodea es el ANILLO: la puerta pasa a medir
  contra el contorno exterior de `costilla_2d.dxf` y se llama `cuerpos_dentro_del_anillo()`.
- **R5 — Las roscas ciegas se dibujan a diámetro de broca** (M4 → 3.3, que ya está en
  el repo por la hoja de Tiptop; M5 → 4.2, ISO 262) en un DXF aparte del dorso, y la
  profundidad va en el pliego. Un DXF 2D no sabe decir «a 10 mm de profundidad» — el
  mismo caso del cajeado KONDOR de la trasera.

## Estructura de ficheros

- `case/cad/params.scad` — entran `t_anillo`, `cara_anillo`, `rebaje_anillo`,
  `rehundido_acrilico`, `chaflan_anillo`, `t_placa`, `t_junta_asiento`, `hol_costado`,
  `d_M4_rosca`, `d_M5_rosca`, `t_clip`; mueren `ala_costilla`, `ala_doblez`,
  `L_casquillo`, `t_junta`, `cierre_p3_gap`; `ancho_total` se rederiva.
- `case/cad/sam17_case.scad` — `anillo_2d()`, `costilla_2d()` (contorno real),
  `costilla_dorso_2d()` (rebaje + roscas ciegas), `costilla()` (sólido con rebaje y
  chaflán), `costado_2d()` retranqueado y sin agujeros, `costados()`/`costillas()`,
  `placas_riel()`, `clips_costado()`, bridas de los tres miembros, `centros_rosca_ciega()`,
  `bom()`.
- `case/clearance_budget.py` — `guarda_rebaje()`, `_seccion_anillo()`,
  `autocomprobacion_anillo()`, `guarda_anillo()`, `_cajas_placa()`, `_cajas_brida()`,
  `_cajas_clip()`, `_centros_rosca_ciega()`, `guarda_anclajes()`; muere la familia L,
  `guarda_costilla`, `guarda_apilado`, `guarda_canto_visto`, `paso_junta_L`.
- `case/check_dxf.py` — `_sobres()` (costilla, dorso, costado), `taladros_anillo()`,
  `cuerpos_dentro_del_anillo()`, `guarda_costado()` (apoyos puntuales hacia dentro),
  `agujeros_donde_toca()` (costado CERO); mueren `taladros_costilla`, `taladros_costado`.
- `case/cad/export.ps1` — `costilla_dorso_2d` en `$piezas`; comentario 29–35 reescrito.
- `case/renders/render.py` — material de aluminio cepillado; `paticas()` en el ensamblado.
- Papeles: `case/README.md`, `case/PLIEGO.md`, `case/RFQ.md`,
  `docs/superpowers/specs/2026-08-15-case-design.md` (rev. 22).

---

### Tarea 1: Los parámetros del anillo, el ancho que cambia y `guarda_rebaje()`

**Files:**
- Modify: `case/cad/params.scad` (bloque de la costilla ~118–147; `t_cheek`/`L_casquillo`/`t_junta` ~634–644; `ancho_total` ~784)
- Modify: `case/cad/sam17_case.scad:30` (`ancho_util`), `rails()` ~1622 (largo del riel)
- Modify: `case/clearance_budget.py` (`leer_params()` 29–56, `perfil()["ancho_util"]` 102–103, `main()`)
- Modify: `docs/superpowers/specs/2026-08-28-costilla-pletina-design.md` (§3 y §5: `t_placa` 6, `ancho_total` 568.62)

**Interfaces:**
- Produce: parámetros `t_anillo=14`, `cara_anillo=20`, `rebaje_anillo=6`,
  `rehundido_acrilico=3`, `chaflan_anillo=1.5`, `t_placa=6`, `t_junta_asiento=1`,
  `hol_costado=0.5`, `d_M4_rosca=3.3`, `d_M5_rosca=4.2`, `t_clip=4`;
  `ancho_total = largo_riel + hol_riel + 2*t_placa + 2*t_anillo` (568.62);
  `ancho_util = ancho_total - 2*t_anillo` (540.62) en sus DOS copias;
  `guarda_rebaje(p) -> None`.
- Los parámetros viejos (`ala_costilla`, `ala_doblez`, `L_casquillo`, `t_junta`,
  `cierre_p3_gap`) **siguen vivos en esta tarea**: los consume `guarda_costilla()` hasta
  la Tarea 2. Se matan allí.

- [ ] **Paso 1: escribir la puerta.** En `case/clearance_budget.py`, justo antes de
`def guarda_piso(`, pegar:

```python
def guarda_rebaje(p: dict[str, float]) -> None:
    """El acrilico cabe en el rebaje del anillo, y el anillo lo cubre entero.

    ES LA PUERTA QUE SUSTITUYE A guarda_apilado() Y A guarda_canto_visto() A LA
    VEZ. Con la costilla de chapa el acrilico iba APILADO detras (chapa, junta,
    PMMA) y un casquillo cruzaba las tres capas; con el anillo de pletina va
    COPLANAR dentro de su ventana, asentado en un rebaje por detras. Ya no hay
    orden de capas que verificar ni casquillo que dimensionar: hay un rebaje
    que tiene que ser MAS HONDO que el acrilico mas grueso del lote.

    Cuatro condiciones, y la primera es la que puso el espesor en 14:

      1. la profundidad del rebaje (t_anillo - rehundido) alcanza para el PMMA
         mas grueso del lote -- 8 + 1.2 de tolerancia Schaeffer -- mas la junta
         de asiento y media decima de aire. Con 12 de anillo el rebaje quedaba
         a -0.2: no cabia.
      2. la franja interior (cara_anillo - rebaje_anillo) admite un M4 a rosca
         ciega con 1.5 D a cada lado: 3 x d_M4_paso = 13.5. Es lo que puso la
         cara vista en 20.
      3. el acrilico solapa el labio al menos 5 mm, para que lo retenga.
      4. el labio tiene al menos 3 mm de cuerpo sobre el acrilico.

    El canto del PMMA queda cubierto POR CONSTRUCCION: un anillo con ventana
    rodea al acrilico en todo su perimetro. Por eso esta puerta no recorre
    tramos -- ya no hay 'tramo con ala' que decidir."""
    tol = 0.4 + 0.1 * p["t_cheek"]            # Schaeffer AG, 2026-08-18
    hondo = p["t_anillo"] - p["rehundido_acrilico"]
    pide = p["t_cheek"] + tol + p["t_junta_asiento"] + 0.5
    assert hondo >= pide, (
        f"el rebaje del anillo tiene {hondo:.2f} mm de fondo (t_anillo "
        f"{p['t_anillo']:g} - rehundido {p['rehundido_acrilico']:g}) y el "
        f"acrilico mas grueso del lote pide {pide:.2f} ({p['t_cheek']:g} + "
        f"{tol:.1f} de tolerancia + {p['t_junta_asiento']:g} de junta + 0.5 de "
        f"aire). Con ese anillo el PMMA no entra: sube t_anillo, no bajes la "
        f"junta")
    franja = p["cara_anillo"] - p["rebaje_anillo"]
    assert franja >= 3 * p["d_M4_paso"], (
        f"la franja interior del anillo mide {franja:.2f} (cara {p['cara_anillo']:g} "
        f"- rebaje {p['rebaje_anillo']:g}) y una rosca ciega M4 con 1.5 D a cada "
        f"lado pide {3 * p['d_M4_paso']:.2f}. Ahi asientan las placas de anclaje")
    assert p["rebaje_anillo"] >= 5, (
        f"el acrilico solo solapa el labio {p['rebaje_anillo']:g} mm; con menos de "
        f"5 el labio no lo retiene")
    assert p["rehundido_acrilico"] >= 3, (
        f"el labio tiene {p['rehundido_acrilico']:g} mm de cuerpo sobre el "
        f"acrilico; con menos de 3 el chaflan de {p['chaflan_anillo']:g} se lo come")
    print(f"rebaje: anillo de {p['t_anillo']:g}, acrilico {p['rehundido_acrilico']:g} "
          f"atras en un rebaje de {hondo:.1f} (pide {pide:.1f}); franja de "
          f"{franja:.0f} para las roscas ciegas; cara vista {p['cara_anillo']:g}")
```

y en `main()` añadir `guarda_rebaje(p)` inmediatamente después de `guarda_apilado(p)`.

- [ ] **Paso 2: correr y ver ROJO.** `python case/clearance_budget.py` → termina en
`KeyError: 't_anillo'`. Si el rojo es otro, parar: algo cambió antes.

- [ ] **Paso 3: los parámetros.** En `case/cad/params.scad`, dentro del bloque de la
costilla (antes de `ala_costilla`), añadir con comentarios en el estilo del fichero
(explican por qué; conservan la historia):

```scad
// EL ANILLO DE PLETINA. La costilla dejo de ser chapa plegada el 2026-08-28:
// Samuel vio el render de la banda de 27 y lo llamo "sandwich", y la
// referencia que quiere es un perfil estrecho y profundo con canto. Eso no
// sale de un pliegue de 1.5 -- no hay arista que chaflanar ni esquina sin
// alivio. Sale de un anillo fresado de pletina. Spec 2026-08-28.
//
// 14 LO MANDA EL ACRILICO, no el gusto. El PMMA de 8 viene +-1.2 (Schaeffer),
// asi que el peor caso mide 9.2; tras el labio de 3 tienen que caber 9.2 mas
// 1 de junta de asiento mas 0.5 de aire = 10.7. Con 12 el rebaje quedaba a
// -0.2. Lo vigila guarda_rebaje().
t_anillo           = 14;
// Cara vista. La foto de referencia da 12-24 ESTIMADO; el minimo lo pone la
// franja interior donde asientan las placas de anclaje: cara - rebaje >= 3 D
// del M4 = 13.5, o sea cara >= 19.5.
cara_anillo        = 20;
// Cuanto solapa el acrilico bajo el labio (en el plano). Con menos de 5 el
// labio no lo retiene.
rebaje_anillo      = 6;
// Cuanto queda atras la cara del PMMA respecto a la cara vista. Rango
// ESTIMADO 3-7 de la foto; el minimo, para que el labio tenga cuerpo.
rehundido_acrilico = 3;
// Chaflan de las dos aristas de la cara vista, silueta y ventana. Rango
// ESTIMADO 1-3 de la foto. Es lo que hace que la arista brille.
chaflan_anillo     = 1.5;
// LA PLACA DE ANCLAJE DEL RIEL. El eje del M4 de cada riel cae a 15.90 de la
// silueta (medido), en la zona del rebaje donde el anillo solo tiene 3 mm de
// labio: el tornillo no puede atravesar la cara vista. Va a una placa sobre
// la franja interior, con dos M4 a rosca ciega en el anillo. Mide 6 y no 4
// porque la cabeza del M4 del riel (boton ISO 7380, 2.2 de alto) tiene que
// quedar DENTRO de la placa: debajo hay acrilico hasta z = 13.2. Cajeado
// de 8 x 2.5 y quedan 3.5 de placa bajo la cabeza. Ruling R1 del plan.
t_placa            = 6;
// Junta de asiento entre el labio y la cara del PMMA: nunca aluminio contra
// acrilico. NO absorbe la tolerancia del espesor -- eso lo hace la
// profundidad del rebaje --, solo evita el contacto y precarga.
t_junta_asiento    = 1;
// Holgura del acrilico dentro de su rebaje, por lado.
hol_costado        = 0.5;
// Diametros de BROCA de las roscas ciegas. El M4 sale de la hoja de Tiptop
// que ya citaba d_M4_paso ("M4 Tapping To 3.3"); el M5 es el de ISO 262.
// Las roscas se dibujan a este diametro en costilla_dorso_2d y la
// profundidad va en el pliego: un DXF no sabe decir "a 10 mm".
d_M4_rosca         = 3.3;
d_M5_rosca         = 4.2;
// Clips de retencion del acrilico hacia dentro: pletina de 4 sobre la franja.
t_clip             = 4;
```

Reescribir el comentario de `t_costilla` (línea ~55) para que diga que desde el
2026-08-28 es **el espesor de la chapa de los tres miembros** y que la costilla ya no es
chapa (conservar la historia del 3→1.5). Lo mismo, en una línea, en el comentario de
`radio_doblez_costilla`. Sustituir la derivación de `ancho_total` por:

```scad
// DESDE EL 2026-08-28 el hueco entre anillos lo fijan las PLACAS de anclaje
// (t_placa por lado, entre el riel y la cara interior del anillo) y el propio
// anillo. El casquillo que cruzaba el acrilico murio con el apilado: el
// acrilico ya no esta en esta cuenta porque va DENTRO de la ventana.
ancho_total     = largo_riel + hol_riel + 2*t_placa + 2*t_anillo;
```

En `case/cad/sam17_case.scad:30`:

```scad
ancho_util = ancho_total - 2*t_anillo;
```

y corregir el comentario de encima (ya no se resta el casquillo: se resta el anillo). En
`rails()` (~1622), los rieles miden lo que se compró y acaban en las placas:

```scad
                    rail_er(ancho_util - 2*t_placa);
```

en las DOS llamadas (3U y 1U).

- [ ] **Paso 4: las gemelas en Python.** En `leer_params()` sustituir la derivación y su
mensaje:

```python
    derivado = (p["largo_riel"] + p["hol_riel"]
                + 2 * p["t_placa"] + 2 * p["t_anillo"])
    if "ancho_total" in p:
        raise SystemExit(
            f"params.scad: ancho_total volvio a ser un literal ({p['ancho_total']:.2f}). "
            f"Es DERIVADO desde el 2026-08-26: largo_riel + hol_riel + "
            f"2*t_placa + 2*t_anillo = {derivado:.2f}. Un literal aqui vuelve a "
            f"esconder si el riel cabe o no.")
```

y en `perfil()`:

```python
        "ancho_util": p["ancho_total"] - 2 * p["t_anillo"],
```

con el comentario de encima reescrito (la placa está DENTRO de ancho_util; el riel mide
`ancho_util - 2*t_placa`). En `_cajas_solidas()` los rieles ya no arrancan en `z0`: dejar
`z0`/`z1` como están en esta tarea (los cambia la Tarea 2) pero acortar las cajas de riel:
`railes.append((nm, ..., z0 + p["t_placa"], z1 - p["t_placa"]))` en el bucle de
`NOMBRES_CR` **y** en el de los dos rieles 1U.

- [ ] **Paso 5: correr y ver VERDE.** `python case/clearance_budget.py` y luego
`powershell -ExecutionPolicy Bypass -File case/cad/export.ps1`. Verde las dos puertas y
`export completo`. La salida imprime `rebaje: anillo de 14, acrilico 3 atras en un rebaje
de 11.0 (pide 10.7); franja de 14 ...`. Si `guarda_costilla()` o `agujeros_donde_toca()`
dan rojo por el ancho nuevo (ancho_util 540.62), es la rejilla de las planchas: sus filas
se reparten sobre `ancho_util` y el paso 100 sigue dando 5 → verificar que el rojo sea
otro antes de tocar nada.

- [ ] **Paso 6: romperla.** `cp case/cad/params.scad /tmp/p.bak`; poner `t_anillo = 12`;
correr el budget → ROJO `el rebaje del anillo tiene 9.00 mm de fondo ... pide 10.70`.
`cp /tmp/p.bak case/cad/params.scad`. Segunda: `cara_anillo = 18` → ROJO `la franja
interior del anillo mide 12.00 ... pide 13.50`. Revertir con `cp`.

- [ ] **Paso 7: enmendar la spec.** En §3 tabla y §5: `t_placa` 6 (con la razón de R1),
`ancho_util` 540.62, `ancho_total` 568.62 (+18). Anotar como enmienda del plan, no borrar
el 4.

- [ ] **Paso 8: render y commit.**

```bash
cd case/renders && "/c/Program Files/Blender Foundation/Blender 5.0/blender.exe" -b -P render.py
git add -A
git commit -m "Entran las cotas del anillo y el case se ensancha 18: lo manda el acrilico"
```

(cuerpo del commit: de dónde sale el 14, el 20 y el 6; qué cambia en el ancho; que la
costilla de chapa sigue dibujándose hasta la Tarea 2.)

---

### Tarea 2: El anillo — 2D, 3D, el acrílico dentro, y `guarda_anillo()`

**Files:**
- Modify: `case/cad/sam17_case.scad` (`cost_*` 537–540, `costilla_ala` … `costilla()` 550–702, `costado_2d()` 489, `costados()`/`costillas()` 1600–1613, dispatch `PART ==` ~1510)
- Modify: `case/clearance_budget.py` (`_seccion_L` … `guarda_costilla` 1320–1550, `guarda_apilado` 1853–1901, `guarda_canto_visto` 2194–2242, `_cajas_solidas` 415–416, `main()`)
- Modify: `case/check_dxf.py` (`_sobres` 97–102, `agujeros_donde_toca` 371–380, `taladros_costilla` 886–998, `taladros_costado` 1098–1156, `railes_dentro_del_costado` 738–816, `main()`)
- Modify: `case/cad/export.ps1` (29–37)
- Modify: `case/cad/params.scad` (matar `ala_costilla`, `ala_doblez`, `L_casquillo`, `t_junta`, `cierre_p3_gap`)

**Interfaces:**
- Consume: los parámetros de la Tarea 1.
- Produce: `anillo_2d()`, `costilla_2d()` (contorno real: silueta − ventana),
  `costilla_dorso_2d()` (contorno del rebaje + círculos de `centros_rosca_ciega()`, que
  en esta tarea devuelve `[]`), `costilla()`, `costado_2d()` retranqueado;
  `_seccion_anillo(p) -> (I, A, ymax)`, `guarda_anillo(p)`; `_sobres()` con
  `costilla_2d`, `costilla_dorso_2d`, `costado_2d` nuevos; `cuerpos_dentro_del_anillo()`.

- [ ] **Paso 1: escribir las puertas.** En `case/clearance_budget.py`, **borrar**
`_seccion_L`, `autocomprobacion_L`, `paso_junta_L` (y el comentario 1308–1319 de las
constantes que «se llevó el plegado»), `_tramos_costilla`, `plegado_costilla`,
`bbox_desarrollo_costilla`, `guarda_costilla`, `guarda_apilado`, `guarda_canto_visto`, y
sus llamadas en `main()`. En su lugar, antes de `def guarda_piso(`:

```python
def _seccion_anillo(p: dict[str, float]) -> tuple[float, float, float]:
    """Inercia, area y fibra mas alejada del anillo, flexion FUERA del plano.

    La seccion de un tramo es un rectangulo macizo de (cara - rebaje) x t_anillo
    -- la franja donde asientan las placas -- mas el LABIO de rebaje x rehundido
    que queda delante del acrilico. Eje neutro por el teorema de los ejes
    paralelos, como _seccion_canal(). NO vale para flexion en el plano: ahi el
    anillo es un marco y trabaja a traccion y compresion."""
    W, T = p["cara_anillo"], p["t_anillo"]
    B, R = p["rebaje_anillo"], p["rehundido_acrilico"]
    a1, y1 = (W - B) * T, T / 2.0
    a2, y2 = B * R, R / 2.0
    A = a1 + a2
    yb = (a1 * y1 + a2 * y2) / A
    I = ((W - B) * T ** 3 / 12 + a1 * (y1 - yb) ** 2
         + B * R ** 3 / 12 + a2 * (y2 - yb) ** 2)
    return I, A, max(yb, T - yb)


def autocomprobacion_anillo() -> None:
    """La seccion del anillo, a mano, con fracciones exactas.

    Es el patron que salvo la costilla el 2026-08-26 y el canal el 27: la
    cuenta primero, la funcion despues. Con cara 20, t 14, rebaje 6, rehundido 3:
      franja: A1 = 14*14 = 196, y1 = 7      labio: A2 = 6*3 = 18, y2 = 1.5
      A = 214;  yb = (196*7 + 18*1.5)/214 = 1399/214 = 6.537383
      I = 14*14^3/12 + 196*(7 - yb)^2 + 6*3^3/12 + 18*(1.5 - yb)^2
        = 2384089/642 = 3713.534268
      ymax = 14 - yb = 7.462617"""
    p = {"cara_anillo": 20.0, "t_anillo": 14.0, "rebaje_anillo": 6.0,
         "rehundido_acrilico": 3.0}
    I, A, ymax = _seccion_anillo(p)
    assert abs(A - 214.0) < 1e-9, f"area {A}, a mano 214"
    assert abs(I - 2384089 / 642) < 1e-6, f"I = {I:.6f}, a mano {2384089/642:.6f}"
    assert abs(ymax - (14 - 1399 / 214)) < 1e-9, f"ymax {ymax:.6f}"


def guarda_anillo(p: dict[str, float]) -> None:
    """El anillo aguanta que empujen el case de lado, tramo por tramo.

    SUSTITUYE A guarda_costilla() desde el 2026-08-28. Aquella media una L de
    chapa plegada tramo a tramo y decidia que tramos llevaban ala; este anillo
    es UNA pletina fresada y todos sus tramos tienen la misma seccion. Se queda
    la hipotesis: viga biempotrada -- las esquinas de un marco continuo lo son,
    y aqui ademas son de una pieza -- con carga_mano al centro del tramo, flecha
    contra flecha_costado_max y tension contra RP02_ALUMINIO.

    Lo que ya no hay que impedir: quitar el ala, dejar un tramo sin ella, mandar
    P3 como alivio en V. No hay ala, no hay pliegue, no hay P3 que soldar. Lo
    que SI impide: que alguien adelgace el anillo o le coma la franja por
    estetica y lo deje por debajo de lo que la chapa plegada ya pasaba."""
    I, A, ymax = _seccion_anillo(p)
    P = _vertices(p)
    n = len(P)
    nombres = ["frente bajo", "cara inferior", "el valle", "cara superior",
               "meseta de remate", "la trasera", "el suelo"]
    print(f"anillo: pletina de {p['t_anillo']:g}, cara vista {p['cara_anillo']:g}, "
          f"rebaje {p['rebaje_anillo']:g} x {p['t_anillo'] - p['rehundido_acrilico']:g}, "
          f"chaflan {p['chaflan_anillo']:g} -> I={I:.0f} mm4, {A:.0f} mm2, "
          f"{A * _perimetro(P) * 2.70e-6:.2f} kg por costilla")
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        largo = math.hypot(b[0] - a[0], b[1] - a[1])
        flecha = p["carga_mano"] * largo ** 3 / (192 * E_ALUMINIO * I)
        sigma = (p["carga_mano"] * largo / 8) * ymax / I
        assert flecha <= p["flecha_costado_max"], (
            f"el anillo cede {flecha:.3f} mm en el tramo '{nombres[i]}' de "
            f"{largo:.2f} mm y el techo son {p['flecha_costado_max']:.2f}. La "
            f"chapa plegada de 27 x 16 x 1.5 daba I=1673 y pasaba: si esto no "
            f"pasa, alguien adelgazo el anillo o le comio la franja")
        assert sigma <= RP02_ALUMINIO, (
            f"el anillo trabaja a {sigma:.1f} MPa en '{nombres[i]}' contra "
            f"{RP02_ALUMINIO:.0f}")
        print(f"  {nombres[i]:<18} {largo:7.2f} mm  cede {flecha:.3f}")


def _perimetro(P: list[tuple[float, float]]) -> float:
    return sum(math.hypot(P[(i + 1) % len(P)][0] - P[i][0],
                          P[(i + 1) % len(P)][1] - P[i][1]) for i in range(len(P)))
```

En `main()`: `autocomprobacion_anillo()` donde estaba `autocomprobacion_L()`;
`guarda_anillo(p)` donde estaba `guarda_costilla(p)`. En `_cajas_solidas()`:

```python
    # LAS CARAS INTERNAS DEL CASE son la cara interior del anillo desde el
    # 2026-08-28: el acrilico ya no esta en el apilado -- va dentro de la
    # ventana, a z = rehundido..rehundido + t_cheek -- y todo lo que vive
    # dentro apoya contra el anillo en z = t_anillo. Los rieles, ademas, contra
    # su placa: ver el bucle de abajo.
    z0 = p["t_anillo"]
    z1 = ancho_total - p["t_anillo"]
```

En `case/check_dxf.py`: en `_sobres()` sustituir la entrada de `costilla_2d` y la del
costado por:

```python
        # EL COSTADO VA DENTRO DE LA VENTANA DEL ANILLO desde el 2026-08-28:
        # su contorno es la silueta retranqueada (cara - rebaje + holgura).
        "costado_2d": (cb.fondo(p) - 2 * _retiro_costado(p),
                       g["alto_total"] - 2 * _retiro_costado(p)),
        # LA COSTILLA VUELVE A SER EL CONTORNO DE LA PIEZA: un anillo fresado
        # no tiene desarrollo. Silueta entera, con la ventana dentro.
        "costilla_2d": (cb.fondo(p), g["alto_total"]),
        # El dorso: lo que se fresa POR DETRAS -- el contorno del rebaje y los
        # centros de las roscas ciegas. Es otro DXF porque un 2D no sabe decir
        # "a 11 de profundidad": mismo caso que kondor_cajeado_2d.
        "costilla_dorso_2d": (cb.fondo(p) - 2 * (p["cara_anillo"] - p["rebaje_anillo"]),
                              g["alto_total"] - 2 * (p["cara_anillo"] - p["rebaje_anillo"])),
```

con, a nivel de módulo:

```python
def _retiro_costado(p: dict[str, float]) -> float:
    """Cuanto se retranquea el acrilico del costado respecto a la silueta."""
    return p["cara_anillo"] - p["rebaje_anillo"] + p["hol_costado"]
```

Borrar `taladros_costilla()` y `taladros_costado()` y sus llamadas. Renombrar
`railes_dentro_del_costado()` → `cuerpos_dentro_del_anillo()`: el contorno contra el que
mide pasa a ser el **exterior** de `costilla_2d` (Ruling R4) — sustituir
`contorno = _contorno_costado()` por `contorno = _contorno_exterior("costilla_2d")` donde:

```python
def _contorno_exterior(nombre: str) -> list:
    """El anillo de aristas mas grande de un DXF: la silueta, no la ventana."""
    aristas, comps = _componentes(nombre)
    if not comps:
        return []
    def area(comp):
        px = [q[0] for j in comp for q in aristas[j]]
        py = [q[1] for j in comp for q in aristas[j]]
        return (max(px) - min(px)) * (max(py) - min(py))
    mayor = max(comps, key=area)
    return _anillo(aristas, mayor)
```

(`_anillo()` y `_componentes()` ya existen en el fichero.) En `agujeros_donde_toca()`
devolver la sección «costado: CERO agujeros»:

```python
    # --- costado: CERO agujeros, otra vez ---
    # Los tuvo (once M5), no los tuvo (2026-08-27 por la manana), tuvo cuatro
    # pasos de casquillo (por la tarde) y desde el 2026-08-28 no tiene ninguno:
    # va DENTRO de la ventana del anillo, coplanar, y nada lo atraviesa.
    if _redondos("costado_2d"):
        f.append(f"costado_2d: {len(_redondos('costado_2d'))} agujero(s) redondo(s) "
                 f"en el acrilico. El costado es PIEL dentro del anillo: cero")
```

En `guarda_costado()` dejar la lógica; actualizar el docstring (ya no «capturado entre las
dos alas»: «asentado en el rebaje del anillo, el labio lo sostiene hacia fuera por todo el
perímetro») y el texto del `print`. En `main()` de check_dxf añadir
`fallos += cuerpos_dentro_del_anillo()` donde estaba la llamada vieja.

- [ ] **Paso 2: correr y ver ROJO.** `python case/clearance_budget.py` → VERDE (las
puertas nuevas no dependen del DXF). `python case/check_dxf.py` → ROJO: `costilla_2d`
fuera de sobre (el DXF sigue siendo el desarrollo, más grande) y `costilla_dorso_2d: FALTA
el DXF`. Ese es el rojo correcto.

- [ ] **Paso 3: el anillo en OpenSCAD.** En `case/cad/sam17_case.scad` **borrar**
`cost_sb/ba/bd/vuelo` (los miembros pasan a `miembro_bd()`, ver abajo), `costilla_ala`,
`costilla_rip_p3`, `costilla_apoyo_bahia`, `costilla_alma`, `costilla_ala_huella`,
`costilla_lleva_ala`, `costilla_alivio_vertice`, y sustituir `costilla_2d()` y `costilla()`
por:

```scad
// --- EL ANILLO DE PLETINA -------------------------------------------------
// La costilla es un anillo FRESADO desde el 2026-08-28: silueta por fuera,
// ventana por dentro, y por detras el rebaje donde asienta el acrilico. No
// tiene desarrollo, no tiene alivios, no tiene P3 que soldar: es una pieza.
function retiro_rebaje() = cara_anillo - rebaje_anillo;

module anillo_2d() {
    difference() {
        perfil_lateral();
        offset(delta = -cara_anillo) perfil_lateral();
    }
}

// El DXF de la CARA: contorno de la pieza y ventana. Va al corte del blank.
module costilla_2d() { anillo_2d(); }

// El DXF del DORSO: lo que se fresa por detras. El contorno del rebaje
// (profundidad t_anillo - rehundido, en el pliego) y los centros de las
// roscas ciegas a diametro de broca (profundidad en el pliego). Otro fichero
// porque un DXF 2D no sabe decir "a 11 mm" -- mismo caso que el cajeado
// KONDOR de la trasera.
module costilla_dorso_2d() {
    offset(delta = -retiro_rebaje()) perfil_lateral();
    for (c = centros_rosca_ciega())
        translate(c[0]) circle(d = c[1]);
}

// [centro, diametro de broca] de cada rosca ciega de la cara interior. Vacio
// hasta que las placas de anclaje existan (plan, Tarea 3).
function centros_rosca_ciega() = [];

// El solido: cara vista en z=0, cara interior en z=t_anillo. El chaflan se
// construye como laminas de offset() creciente -- seis de 0.25 -- porque un
// chaflan exacto sobre un contorno concavo no sale de hull() ni barato de
// minkowski(); para el render y para solapes() basta y es determinista.
module costilla() {
    n = 6;
    difference() {
        union() {
            for (i = [0 : n-1])
                let (f = chaflan_anillo * (1 - (i + 0.5)/n))
                translate([0, 0, i*chaflan_anillo/n])
                    linear_extrude(chaflan_anillo/n + 0.01)
                        difference() {
                            offset(delta = -f) perfil_lateral();
                            offset(delta = -cara_anillo + f) perfil_lateral();
                        }
            translate([0, 0, chaflan_anillo])
                linear_extrude(t_anillo - chaflan_anillo) anillo_2d();
        }
        // el rebaje, por detras
        translate([0, 0, rehundido_acrilico])
            linear_extrude(t_anillo)
                offset(delta = -retiro_rebaje()) perfil_lateral();
    }
}
```

`costado_2d()` pasa a:

```scad
// EL COSTADO VA DENTRO DE LA VENTANA desde el 2026-08-28: silueta retranqueada
// retiro_rebaje() + holgura, sin un solo agujero. Es piel, otra vez.
module costado_2d() {
    offset(delta = -(retiro_rebaje() + hol_costado)) perfil_lateral();
}
```

`costados()` y `costillas()`:

```scad
module costados() {
    translate([0, 0, rehundido_acrilico]) costado();
    translate([0, 0, ancho_total - rehundido_acrilico - t_cheek]) costado();
}
module costillas() {
    costilla();
    translate([0, 0, ancho_total]) mirror([0, 0, 1]) costilla();
}
```

Añadir el dispatch `else if (PART == "costilla_dorso_2d") costilla_dorso_2d();` junto a
`costilla_2d`. Los tres miembros: sustituir sus llamadas a `cost_bd()` por
`miembro_bd()` con `function miembro_bd() = 2*(radio_doblez_costilla + t_costilla) - PI/2*(radio_doblez_costilla + k_factor*t_costilla);`
(la misma fórmula: es el plegado de SU chapa, que no cambia). Buscar todo uso restante de
`ala_costilla`, `ala_doblez`, `L_casquillo`, `t_junta`, `cierre_p3_gap`, `pv_x()` con
`t_costilla` de costilla, y `centros_miembro_punta()` (queda sin consumidor: borrar). En
`bom()`, las líneas que citen los parámetros muertos se sustituyen por UNA línea
provisional: `echo("BOM: COSTILLA x2 -- anillo de PLETINA de ", t_anillo, " fresado. El detalle lo reescribe la Tarea 5.");`
En `params.scad` **borrar** `ala_costilla`, `ala_doblez`, `L_casquillo`, `t_junta`,
`cierre_p3_gap` con sus comentarios (dejar una línea de historia en el bloque del anillo:
«fueron … hasta el 2026-08-28»). En `export.ps1`: añadir `"costilla_dorso_2d"` a
`$piezas` tras `"costilla_2d"` y reescribir el comentario 29–35 (el DXF vuelve a ser el
contorno; el dorso va aparte; ya no hay plano de plegado de la costilla).

- [ ] **Paso 4: correr y ver VERDE.** Export completo:
`powershell -ExecutionPolicy Bypass -File case/cad/export.ps1`. Las dos puertas verdes.
`guarda_anillo` imprime `I=3714 mm4, 214 mm2, 0.6x kg por costilla` (el kg sale del
perímetro real). `guarda_costado` imprime un vano nuevo: anotarlo en el reporte.

- [ ] **Paso 5: romperla.** (a) `cp` de params; `t_anillo = 8` → ROJO de `guarda_rebaje`
(la primera que muerde; está bien: el rebaje manda antes que la flecha). (b) Para probar
`guarda_anillo`: `cara_anillo = 20; rebaje_anillo = 14` (franja de 6) → `guarda_rebaje`
también muerde antes. Entonces romper `guarda_anillo` por su propio lado: en
`clearance_budget.py`, `cp` de respaldo, y multiplicar `carga_mano` por 40 dentro de
`guarda_anillo` (`p["carga_mano"] * 40`) → ROJO `el anillo cede ... en el tramo 'el
suelo'`. Revertir con `cp`. (c) En el .scad, quitar la ventana (`anillo_2d()` →
`perfil_lateral()`), exportar solo `costilla_2d` con OpenSCAD y correr check_dxf → ROJO en
`guarda_costado` (vano enorme: no hay canto de ventana) o en `cuerpos_dentro_del_anillo`.
Revertir con `cp`.

- [ ] **Paso 6: render y commit.** Render con `render.py`. Mirar la imagen antes de
commitear: tiene que verse una cara de aluminio **estrecha** siguiendo la silueta, el
acrílico **rehundido** dentro, y ningún filo naranja en el costado. Commit:
`"La costilla es un anillo fresado, y el acrilico va dentro de su ventana"`.

---

### Tarea 3: Los anclajes — placas, bridas, roscas ciegas y `taladros_anillo()`

**Files:**
- Modify: `case/cad/sam17_case.scad` (`centros_rosca_ciega()`, nuevo `placas_riel()`, `miembro_bajo/alto/bahia` 2D y 3D ~703–790, `tapa_valle_2d()` ~1184 y `pv_x()`, `bandeja_base_2d()` ~888, `assembly_aluminio()`)
- Modify: `case/clearance_budget.py` (`_cajas_solidas`, nuevos `_cajas_placa`, `_cajas_brida`, `_centros_rosca_ciega`, `guarda_anclajes`; `guarda_zocalo` gemela en check_dxf ~1027)
- Modify: `case/check_dxf.py` (nuevo `taladros_anillo()`, `guarda_zocalo()` 1027–1029)

**Interfaces:**
- Consume: `costilla_dorso_2d()` y `centros_rosca_ciega()` de la Tarea 2; `t_placa`,
  `d_M4_rosca`, `d_M5_rosca` de la Tarea 1.
- Produce: `centros_rosca_ciega() -> [[[x,y], d], ...]` y su gemela
  `_centros_rosca_ciega(p) -> list[tuple[str, tuple[float,float], float]]`
  (nombre, centro, diámetro de broca); cajas `placa <riel>`, `brida <miembro> <lado>` en
  `_cajas_solidas`; `guarda_anclajes(p)`; `taladros_anillo()`.

- [ ] **Paso 1: escribir las puertas.** En `check_dxf.py`, antes de `def main`:

```python
def taladros_anillo() -> list[str]:
    """Las roscas ciegas del anillo estan en el dorso, donde el modelo dice,
    con material alrededor y dentro de la FRANJA.

    NADA ATRAVIESA LA CARA VISTA desde el 2026-08-28. Rieles, miembros y clips
    se atornillan por la cara interior a roscas ciegas de 10 mm en la pletina
    de 14. Los centros salen en costilla_dorso_2d a diametro de BROCA (M4 3.3,
    M5 4.2); la profundidad va en el pliego.

    Dos cantos mandan y los dos son del dorso: la silueta por fuera y el
    contorno del REBAJE por dentro, porque mas adentro del rebaje solo quedan 3
    mm de labio y una rosca ahi sale por la cara vista. 1.5 D a cada uno."""
    import clearance_budget as cb

    p = cb.leer_params()
    esperados = cb._centros_rosca_ciega(p)
    leidos = _redondos("costilla_dorso_2d")
    cantos = _cantos("costilla_dorso_2d")
    if not cantos:
        return ["costilla_dorso_2d: sin LINEs, no se pueden verificar las roscas"]
    f: list[str] = []
    for nm, c, d in esperados:
        cerca = [q for q in leidos
                 if math.hypot(q[0] - c[0], q[1] - c[1]) <= DESVIO_DXF_MAX
                 and abs(q[2] - d) < 0.1]
        if not cerca:
            f.append(f"costilla_dorso_2d: falta la rosca ciega de '{nm}' "
                     f"(broca {d:.1f}) en ({c[0]:.2f}, {c[1]:.2f})")
            continue
        dist = _dist_al_contorno(cantos, c)
        if dist < BORDE_MIN_D * d:
            f.append(f"costilla_dorso_2d: la rosca de '{nm}' cae a {dist:.2f} mm "
                     f"del canto mas cercano (silueta o rebaje) y se exige "
                     f"{BORDE_MIN_D * d:.2f}. Fuera de la franja solo hay labio "
                     f"de 3: por ahi la rosca sale por la cara vista")
    if len(leidos) != len(esperados):
        f.append(f"costilla_dorso_2d: {len(leidos)} circulos y el modelo pone "
                 f"{len(esperados)} roscas ciegas")
    if not f:
        print(f"  costilla_dorso_2d: {len(esperados)} roscas ciegas en la franja, "
              f"todas con 1.5 D a la silueta y al rebaje")
    return f
```

y `fallos += taladros_anillo()` en `main()`. En `clearance_budget.py`:

```python
def guarda_anclajes(p: dict[str, float]) -> None:
    """Cada anclaje asienta en la franja del anillo, y la cabeza del M4 del riel
    cabe dentro de su placa sin tocar el acrilico.

    La cabeza va del lado del anillo (el tornillo entra en el riel por su eje)
    y debajo de la placa, a z < t_anillo, hay acrilico hasta rehundido +
    t_cheek + tolerancia + junta. Por eso la placa mide 6 y no 4 (plan, R1)."""
    cabeza = 2.2                                   # ISO 7380 boton M4
    tol = 0.4 + 0.1 * p["t_cheek"]
    techo_pmma = p["rehundido_acrilico"] + p["t_cheek"] + tol + p["t_junta_asiento"]
    assert techo_pmma <= p["t_anillo"], (
        f"el acrilico llega a z={techo_pmma:.2f} y la cara interior del anillo "
        f"esta en {p['t_anillo']:g}: el PMMA asoma por detras del anillo")
    assert p["t_placa"] - (cabeza + 0.3) >= 3.0, (
        f"la placa de {p['t_placa']:g} con un cajeado de {cabeza + 0.3:.1f} para "
        f"la cabeza deja {p['t_placa'] - cabeza - 0.3:.1f} mm bajo ella; hacen "
        f"falta 3. Ruling R1: 6 mm")
    P = _vertices(p)
    franja = p["cara_anillo"] - p["rebaje_anillo"]
    for nm, c, d in _centros_rosca_ciega(p):
        dist = _distancia_a_silueta(P, c)
        assert 1.5 * d <= dist <= franja - 1.5 * d, (
            f"la rosca ciega '{nm}' cae a {dist:.2f} de la silueta; la franja va "
            f"de {1.5 * d:.2f} a {franja - 1.5 * d:.2f}")
    print(f"anclajes: {len(_centros_rosca_ciega(p))} roscas ciegas en la franja "
          f"de {franja:g}; placas de {p['t_placa']:g} con la cabeza dentro "
          f"(PMMA hasta z={techo_pmma:.2f})")


def _distancia_a_silueta(P: list[tuple[float, float]],
                          c: tuple[float, float]) -> float:
    def d_seg(a, b):
        ax, ay = a; bx, by = b; px, py = c
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2)) if L2 else 0.0
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    return min(d_seg(P[i], P[(i + 1) % len(P)]) for i in range(len(P)))
```

`guarda_anclajes(p)` en `main()` tras `guarda_rebaje(p)`. Y la gemela de los centros,
que en esta tarea el implementador escribe **a la vez** en las dos lenguas (es el patrón
del repo: `centros_rail()` / `_centros_rail()`):

```python
def _centros_rosca_ciega(p: dict[str, float]
                          ) -> list[tuple[str, tuple[float, float], float]]:
    """(nombre, centro, diametro de broca) de cada rosca ciega de la cara
    interior del anillo. GEMELA de centros_rosca_ciega() en el .scad; las cruza
    taladros_anillo() releyendo costilla_dorso_2d.dxf."""
    out = []
    for nm, (cx, cy), (ux, uy), (nx, ny) in _placas(p):
        for s in (-7.0, 7.0):
            out.append((f"placa {nm} {s:+.0f}",
                        (cx + ux * s + nx * 7.0, cy + uy * s + ny * 7.0),
                        p["d_M4_rosca"]))
    out += _roscas_bridas(p)          # dos M5 por extremo de miembro
    out += _roscas_clips(p)           # un M4 por clip (Tarea 4: [] hasta entonces)
    return out
```

donde `_placas(p)` devuelve, por placa, `(nombre, pie, u, n)`: el **pie** es la
proyección del centro del riel sobre su tramo de silueta, `u` el unitario a lo largo del
tramo y `n` la normal hacia dentro — la misma convención de `_centros_rail()`
(`n = (d.y, -d.x)`):

```python
def _placas(p: dict[str, float]) -> list[tuple[str, tuple[float, float],
                                               tuple[float, float],
                                               tuple[float, float]]]:
    """Una placa por riel 3U sobre su tramo; UNA para los dos 1U sobre el valle
    (plan, R2). El pie es donde la placa toca la silueta; las roscas van a
    +-7 (3U) o +-12 (1U) a lo largo y a 7 hacia dentro."""
    P = _vertices(p)
    cr = _centros_rail(p, P)
    tramo_de = {0: (P[1], P[2]), 1: (P[1], P[2]), 2: (P[3], P[4]), 3: (P[3], P[4])}
    out = []
    for i, (nm, c) in enumerate(zip(NOMBRES_CR, cr)):
        a, b = tramo_de[i]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (u[1], -u[0])
        s = (c[0] - a[0]) * u[0] + (c[1] - a[1]) * u[1]
        out.append((nm, (a[0] + u[0] * s, a[1] + u[1] * s), u, n))
    cajas = _cajas_miembro(p, P, cr, 0.0, 0.0)
    bahia = _envolvente_bahia(cajas)
    xc = (bahia[1] + bahia[2]) / 2
    out.append(("fila 1U", (xc, P[3][1]), (1.0, 0.0), (0.0, -1.0)))
    return out
```

y en `_centros_rosca_ciega()` el paso `s` vale `±7` para las 3U y `±12` para `"fila 1U"`.
Las cajas:

```python
def _cajas_placa(p, z0, z1) -> list[Caja]:
    """Placa de 28 (a lo largo) x 26 (desde la silueta hacia dentro) x t_placa,
    pegada a la cara interior del anillo en cada extremo del riel. La 1U mide
    50. Es la que retiene el acrilico hacia dentro donde hay riel."""
```

(el implementador la escribe como AABB por tramo, igual que `_esquinas_er`; las placas
de las caras inclinadas van giradas con su tramo y su AABB envolvente vale para
`solapes()` porque nada mas vive en esa franja.) Las bridas de los miembros:

```python
def _cajas_brida(p, cajas_miembro, z0, z1) -> list[Caja]:
    """Lengueta de chapa de t_costilla doblada del extremo de cada miembro,
    plana contra la cara interior del anillo (z0..z0 + t_costilla), dentro de
    la franja, con dos M5 a rosca ciega."""
```

Todas entran en la lista `railes` de `_cajas_solidas()` para que `solapes()` las
adjudique contra rieles, miembros, pestaña de la banda y entre sí.

- [ ] **Paso 2: correr y ver ROJO.** `python case/clearance_budget.py` → `NameError:
_centros_rosca_ciega` (o `AttributeError` si se escribe el stub antes). Escribir los stubs
que devuelven `[]` y correr: `guarda_anclajes` imprime `0 roscas`. Entonces check_dxf con
`taladros_anillo` → VERDE trivial (0 = 0). El rojo de verdad llega al escribir la primera
placa en Python sin su gemela .scad: `falta la rosca ciega de 'placa cara_inf frente
-7'`. **Ese es el rojo que hay que ver antes de tocar el .scad.**

- [ ] **Paso 3: el modelo.**
  - `centros_rosca_ciega()` en .scad con la misma geometría que `_placas()`.
  - `module placas_riel()`: por cada riel 3U, un prisma de 28 × 26 × `t_placa` sobre la
    cara interior del anillo (z = `t_anillo`..`t_anillo + t_placa` y su espejo), girado
    con su tramo; la placa 1U de 50 × 26 centrada en la boca. Con los dos cajeados Ø8 ×
    2.5 (visibles en render, es lo de menos) y los pasos M4.
  - Los miembros: `miembro_bajo_2d/alto_2d/bahia_2d` ganan en cada punta una lengüeta
    de 20 × 22 doblada 90° (mismo `miembro_bd()`), y sus sólidos `miembro_bajo()`,
    `miembro_alto()`, `bahia()` la dibujan plana contra el anillo. La bahía (R3) acaba
    `t_placa` antes del anillo y su lengüeta va contra la placa 1U, no contra el anillo:
    sus dos M4 son roscas **en la placa**, no en el anillo (no entran en
    `centros_rosca_ciega()`).
  - `tapa_valle_2d()`: la pestaña de la banda se atornilla a una rosca ciega M3 en la
    franja del valle, dentro del vuelo delantero (x entre `pts_perfil()[2].x + 1.5*d_M3_paso`
    y `bahia_x0() - 1.5*d_M3_paso`); añadir esa rosca a `centros_rosca_ciega()` con
    `d = 2.5` (broca M3, ISO 262) y su gemela.
  - `bandeja_base_2d()` y `guarda_zocalo()`: las dos filas de M5 de la tabla suben al
    **centro del canto inferior del anillo**: offset `t_anillo/2` desde cada cara exterior
    (era `t_cheek + t_costilla/2`). Esas roscas van en el canto y NO en el dorso: no entran
    en `costilla_dorso_2d`; se listan en el pliego (Tarea 5).
  - `assembly_aluminio()`: `placas_riel();`.

- [ ] **Paso 4: correr y ver VERDE.** Export completo. `solapes()` es el juez: si una
placa choca con una brida o con la pestaña, se mueve la placa a lo largo de su tramo (no
la brida) y se anota en el reporte cuánto. `taladros_anillo` imprime el conteo: 4 placas
3U × 2 + 1 placa 1U × 2 + 3 miembros × 2 lados × 2 + 1 pestaña = **23 por anillo**.

- [ ] **Paso 5: romperla.** Mover una rosca de placa de `s=±7` a `s=±3` en la gemela
Python (con `cp` de respaldo) → check_dxf ROJO `falta la rosca ciega`. Revertir. Poner
`t_placa = 4` en params → ROJO de `guarda_anclajes` (`deja 1.5 mm bajo ella; hacen falta
3`). Revertir.

- [ ] **Paso 6: render y commit.** `"Nada atraviesa la cara: rieles y miembros anclan por
dentro a roscas ciegas"`.

---

### Tarea 4: La retención del acrílico y `guarda_costado()` con apoyos puntuales

**Files:**
- Modify: `case/cad/sam17_case.scad` (nuevo `clips_costado()`, `centros_rosca_ciega()`)
- Modify: `case/clearance_budget.py` (`_cajas_clip`, `_roscas_clips`)
- Modify: `case/check_dxf.py` (`guarda_costado()` 625–735)

**Interfaces:**
- Consume: `_cajas_placa` de la Tarea 3 (las placas ya retienen donde hay riel).
- Produce: `clips_costado()`, `_roscas_clips(p)`, `guarda_costado()` con dos modelos.

- [ ] **Paso 1: escribir la puerta.** `guarda_costado()` conserva su modelo hacia FUERA
(placa circular empotrada, vano = distancia al canto de la ventana, apoyo continuo del
labio) y gana el modelo hacia DENTRO: la mano empuja el costado hacia el interior y lo
que lo para son los **apoyos puntuales** en z = `t_anillo` — placas y clips. Vano
interior = máximo, sobre los puntos del acrílico, de la distancia al apoyo más cercano
(footprint de cada placa/clip que asoma sobre la ventana, proyectado al plano). Misma
fórmula de placa circular con ese vano. Añadir tras el barrido existente:

```python
    # HACIA DENTRO el apoyo es PUNTUAL: placas y clips sobre la cara interior
    # del anillo, en los sitios donde asoman sobre la ventana. La mano empuja
    # hacia dentro y ahi el labio no ayuda.
    apoyos = [c for c in cb._cajas_placa(p, 0.0, 0.0) + cb._cajas_clip(p, 0.0, 0.0)]
    vano_in, donde_in = 0.0, (0.0, 0.0)
    y = min(ys)
    while y <= max(ys):
        x = min(xs)
        while x <= max(xs):
            if _dentro(contorno, (x, y)):
                d = min(_dist_a_caja(c, (x, y)) for c in apoyos)
                if d > vano_in:
                    vano_in, donde_in = d, (x, y)
            x += PASO_BARRIDO
        y += PASO_BARRIDO
    flecha_in = P * vano_in ** 2 / (16 * math.pi * D)
    if flecha_in > p["flecha_costado_max"]:
        fallos.append(
            f"costado_2d: empujado hacia DENTRO se hunde {flecha_in:.2f} mm "
            f"(vano {vano_in:.1f} en x={donde_in[0]:.0f}, y={donde_in[1]:.0f}) "
            f"contra {p['flecha_costado_max']:.2f}. Hacia dentro lo paran las "
            f"placas y los clips: falta un clip cerca de ese punto")
```

con `_dist_a_caja(caja, pt)` = distancia del punto al rectángulo `(x0..x1, y0..y1)` de
la caja en el plano (0 si está dentro). Los clips entran en `_cajas_solidas` como cajas
`clip <tramo> <i>`.

- [ ] **Paso 2: correr y ver ROJO.** Con `_cajas_clip` devolviendo `[]`, check_dxf →
ROJO `empujado hacia DENTRO se hunde ... falta un clip cerca de` en la trasera o el suelo
(los tramos sin riel). Anotar el vano.

- [ ] **Paso 3: los clips.** Pletina de `t_clip` = 4, 20 × 30, sobre la franja, asomando
6 mm sobre la ventana, un M4 a rosca ciega a 7 de la silueta. **Seis por costado** (spec
§4): dos en el suelo, dos en la trasera, uno en el frente bajo, uno en la meseta;
`clips_costado()` en .scad, `_cajas_clip` y `_roscas_clips` en Python, y sus roscas en
`centros_rosca_ciega()` (pasan a 29 por anillo). Si la puerta sigue roja con seis, añadir
donde el mensaje diga y reportar la cantidad final: **no** es un número de la spec, es lo
que la puerta pida.

- [ ] **Paso 4: correr y ver VERDE.** Export completo; anotar `vano hacia dentro`.

- [ ] **Paso 5: romperla.** Quitar los dos clips de la trasera (`cp` de respaldo) → ROJO.
Revertir.

- [ ] **Paso 6: render y commit.** `"El acrilico queda retenido por las dos caras: labio
por fuera, seis clips por dentro"`.

---

### Tarea 4b: La escuadra de la trasera — el tope del canto trasero del costado

**Decisión de Samuel (2026-08-28), tras el hallazgo de la revisión de la Tarea 4:** el
canto TRASERO del acrílico del costado corre 227 mm sin tope hacia dentro (los clips
solo caben en el suelo; la franja trasera la ocupa `piel_trasera`), y la fórmula de
parche empotrado de `guarda_costado()` no vale en un canto libre. Se pone una
**escuadra de aluminio de 1.5 fijada a la trasera** cuya ala asoma sobre el canto del
costado y hace de tope continuo.

**Files:**
- Modify: `case/cad/params.scad` (`escuadra_ala`, `escuadra_m3`; el vuelo se DERIVA)
- Modify: `case/cad/sam17_case.scad` (`escuadra_trasera_2d()`, `escuadras_trasera()`, `centros_m3_escuadra()`, `piel_trasera_2d()` con sus M3, `assembly_aluminio()`, dispatch `PART`, `bom()`)
- Modify: `case/clearance_budget.py` (`_escuadras_trasera(p)`, `_cajas_escuadra`, `_centros_m3_escuadra(p)`, `guarda_escuadra_trasera(p)`, `_cajas_solidas`)
- Modify: `case/check_dxf.py` (`_sobres()` con `escuadra_trasera_2d`, `guarda_costado()` apoyos, `cuerpos_dentro_del_anillo()`, censo de M3 de la trasera en `agujeros_donde_toca()`)
- Modify: `case/cad/export.ps1` (`$piezas`)

**Interfaces:**
- Consume: `_clips(p)`, `_placas(p)`/`_esquinas_placa` (los apoyos de la Tarea 4), la caja `piel_trasera` de `_cajas_solidas` (x = P6.x − t_piel .. P6.x, z = t_anillo + hol_piel .. espejo), `costado_2d()` (canto trasero en x = P6.x − 14.5, z = rehundido .. rehundido + t_cheek).
- Produce: `guarda_escuadra_trasera(p)`, el DXF `escuadra_trasera_2d`, y el apoyo continuo del canto trasero en el modelo interior de `guarda_costado()`.

**Geometría (derivada, no a mano):** un angular en L de chapa de aluminio de
`t_costilla` (1.5, la misma chapa de los miembros; mismo `radio_doblez_costilla`),
uno por lado:
- **Ala A** (la que se atornilla): plana contra la cara INTERIOR de la trasera
  (x = P6.x − t_piel), de `escuadra_ala` = 12 de ancho en z (desde z = t_anillo +
  hol_piel hacia dentro) y de largo en y desde el borde superior de la brida del
  miembro bajo + 10 hasta el borde inferior de la brida del miembro alto − 10
  (`solapes()` los adjudica), con `escuadra_m3` = 3 M3 repartidos como
  `fila_agujeros()` a lo largo de y, a 1.5 D del canto de la trasera y de sus dos
  filas existentes.
- **Ala B** (el tope): perpendicular, apuntando a −x desde la cara de la trasera, a
  z = t_anillo .. t_anillo + t_costilla (justo encima de la cara interior del anillo,
  sin tocarla: 0 de solape con el anillo y ≥ 0.8 sobre el acrílico más grueso), de
  vuelo tal que su punta llegue a 4 mm por delante del canto trasero del costado:
  `vuelo = t_piel + retiro_rebaje() + hol_costado + 4` medido desde la cara interior
  de la trasera (con t_piel 8: 8 + 14 + 0.5 + 4 = 26.5, derivado en el código).
- Los M3 atraviesan la trasera (8 de PMMA) y el ala A, con tuerca por dentro — el
  mismo herraje que las dos filas que la trasera ya lleva a los miembros.

- [ ] **Paso 1: escribir las puertas.** En `clearance_budget.py`, antes de `def guarda_piso(`:

```python
def guarda_escuadra_trasera(p: dict[str, float]) -> None:
    """El canto trasero del costado tiene tope hacia dentro en casi todo su largo.

    LO PIDIO LA REVISION DE LA TAREA 4 Y LO DECIDIO SAMUEL el 2026-08-28: el
    punto peor del modelo interior de guarda_costado() caia a menos de 1 mm del
    canto trasero del acrilico, que corria 227 mm sin un solo tope, y la formula
    de parche empotrado no vale en un canto libre. Los clips no llegan: el mas
    cercano legal se queda a 95.7 mm, y en la franja trasera no cabe ninguno
    porque la ocupa piel_trasera. La escuadra va fijada a la TRASERA, no al
    anillo, y su ala asoma sobre el canto como tope continuo.

    Tres cosas, y la tercera es la que la hace tope y no adorno:
      1. el ala B vuela hasta pasar el canto trasero del costado en >= 4 mm;
      2. el ala B vive a z >= t_anillo (no toca el anillo) y a >= 0.8 mm del
         acrilico mas grueso del lote (tope con carrera, como los clips: la
         precarga la pone la junta del labio);
      3. el ala A cubre al menos el 80 % del largo libre del canto trasero
         (entre las bridas de los dos miembros), con sus M3 a 1.5 D de todo
         canto y de las dos filas que la trasera ya lleva."""
    P = _vertices(p)
    x_canto = P[6][0] - (p["cara_anillo"] - p["rebaje_anillo"] + p["hol_costado"])
    tol = 0.4 + 0.1 * p["t_cheek"]
    z_pmma = p["rehundido_acrilico"] + p["t_cheek"] + tol + p["t_junta_asiento"]
    escuadras = _escuadras_trasera(p)
    for lado, esc in enumerate(escuadras):
        assert x_canto - esc["x_punta"] >= 4.0, (
            f"la escuadra {lado} vuela hasta x={esc['x_punta']:.2f} y el canto "
            f"trasero del costado esta en x={x_canto:.2f}: solapa "
            f"{x_canto - esc['x_punta']:.2f} mm y se exigen 4 para que haga de tope")
        assert esc["z_ala_b"] >= p["t_anillo"] - 1e-9, (
            f"el ala B de la escuadra {lado} arranca en z={esc['z_ala_b']:.2f} y la "
            f"cara interior del anillo esta en {p['t_anillo']:g}: se monta encima")
        assert esc["z_ala_b"] - z_pmma >= 0.8, (
            f"el ala B de la escuadra {lado} queda a {esc['z_ala_b'] - z_pmma:.2f} mm "
            f"del acrilico mas grueso (z={z_pmma:.2f}): pinza en vez de topar")
        assert esc["cobertura"] >= 0.80, (
            f"la escuadra {lado} cubre el {esc['cobertura'] * 100:.0f} % del canto "
            f"trasero libre y se exige el 80 %")
    e = escuadras[0]
    print(f"escuadra trasera: ala B a z={e['z_ala_b']:.2f}, pasa el canto del costado "
          f"en {x_canto - e['x_punta']:.2f} mm, cubre el {e['cobertura'] * 100:.0f} % "
          f"del canto libre, {int(p['escuadra_m3'])} M3 a la trasera por lado")
```

`_escuadras_trasera(p)` devuelve por lado un dict con `x_punta`, `z_ala_b`, `y0`, `y1`,
`cobertura` (largo del ala A entre bridas / largo libre del canto) y las cajas de las
dos alas. `guarda_escuadra_trasera(p)` en `main()` tras `guarda_anclajes(p)`. En
`check_dxf.py`: `_sobres()` gana `escuadra_trasera_2d` (desarrollo: ala A + ala B −
BD, por `_bd_miembro`); `guarda_costado()` añade el rectángulo xy del ala B a
`apoyos`; `cuerpos_dentro_del_anillo()` añade las escuadras; en `agujeros_donde_toca()`
el censo de la trasera admite los `escuadra_m3` por lado fuera de sus dos filas
(contarlos aparte con su nombre, no meterlos en las filas). Los taladros nuevos NO
van en el anillo: no tocan `centros_rosca_ciega()`.

- [ ] **Paso 2: ROJO.** `python case/clearance_budget.py` → `NameError: _escuadras_trasera`
(o `KeyError: 'escuadra_ala'`). Escribir el stub que devuelve `[]` → la puerta imprime
sin asertar; entonces el ROJO real: `agujeros_donde_toca` en check_dxf cuando la
trasera traiga los 3 M3 nuevos y el censo no los espere — ver ese rojo ANTES de tocar
el censo.

- [ ] **Paso 3: el modelo.** Parámetros, `escuadra_trasera_2d()` (desarrollo con sus 3
M3; el DXF es el desarrollo, como los miembros), `escuadras_trasera()` 3D (dos alas
plegadas, espejo), los 3 M3 en `piel_trasera_2d()`, `assembly_aluminio()`, dispatch,
`$piezas`, `bom()` (escuadra ×2, M3 ×6 + tuerca). Gemelas en Python. `solapes()`
adjudica escuadra contra bridas, clips, piel_trasera y miembros; si choca, se acorta el
ala A (nunca el vuelo del ala B) y se anota.

- [ ] **Paso 4: VERDE.** Export completo. `guarda_costado` imprime el vano interior nuevo
(anotar el salto desde 95.5) y `guarda_escuadra_trasera` su línea.

- [ ] **Paso 5: romperla.** (a) vuelo derivado −5 (con `cp`) → ROJO `solapa ... se exigen 4`.
(b) ala B en z = t_anillo − 1 → ROJO `se monta encima`. (c) quitar un M3 del DXF de la
trasera (exportar solo `piel_trasera_2d`) → ROJO del censo.

- [ ] **Paso 6: render y commit.** `"El canto trasero del costado gana su tope: una
escuadra a la trasera"`. Mirar `sam17-case-trasera.png`: la escuadra no se ve desde
fuera (va por dentro de la trasera); lo único nuevo visible son tres cabezas de M3 por
lado en la trasera, en línea vertical cerca del canto. Decir en el reporte si se ven y
cómo.

---

### Tarea 5: Los papeles y el eco del BOM (sonnet)

**Files:**
- Modify: `case/cad/sam17_case.scad` (`bom()` 1889–2062)
- Modify: `case/README.md`, `case/PLIEGO.md`, `case/RFQ.md`
- Modify: `docs/superpowers/specs/2026-08-15-case-design.md` (rev. 22)
- Read: `C:\Users\simon\AppData\Local\Temp\claude\D--Desktop-projects-sam17\5ac71cb9-dc36-434f-acdc-249c31e06c7d\scratchpad\inventario_pletina.md` §F (las ~68 citas con línea), y `docs/superpowers/specs/2026-08-28-costilla-pletina-design.md` §9

- [ ] **Paso 1: el eco del BOM primero.** `openscad -o /tmp/b.stl -D 'PART="bom"' case/cad/sam17_case.scad`
tiene que decir la verdad: costilla = anillo de pletina de 14 fresado, 20 de cara, con
rebaje y chaflán, anodizado con enmascarado; placas ×10 (8 de 3U + 2 de 1U) y clips ×12
de pletina; junta de asiento EPDM 1 mm; roscas ciegas por anillo (el conteo que imprime
`taladros_anillo`); **cero** casquillos, cero junta de 4, cero «transversal 2020», cero
«chapa plegada» para la costilla. Los tres miembros siguen siendo chapa de 1.5 con
bridas. Comprobar con `grep -i "2020\|casquillo\|plegad\|ala_costilla"` sobre el eco.
- [ ] **Paso 2: PLIEGO.** Sección nueva «Taller de mecanizado: el anillo» (spec §9):
pletina de 14, blank ~330 × 270, contorno + ventana, rebaje de 6 × 11 por detrás, chaflán
1.5 × 45° en las dos aristas de la cara vista, roscas ciegas M4/M5 (broca 3.3/4.2, 10 de
profundidad) en la cara interior según `costilla_dorso_2d.dxf`, seis M5 en el canto
inferior, radio ≥ 3 en P3; anodizado satinado tras el mecanizado con el punto de bonding
enmascarado; **cupón** de 100 mm del perfil antes de cortar. Mueren del pliego los
casquillos, la junta de 4 y el plegado de la costilla. Corregir cada línea de la §F del
inventario.
- [ ] **Paso 3: RFQ.** Taller nuevo (mecanizado), con la pregunta eliminatoria de la
spec §9: planitud garantizada tras vaciar el centro de una pletina de 14. El de chapa se
queda con los tres miembros (ahora con bridas), las placas y los clips.
- [ ] **Paso 4: README.** BOM recontado contra el eco; **el orden de montaje** con la
regla de R1 (primero el riel a la placa, después la placa al anillo desde dentro; los
clips al final, tras el acrílico); el bonding de PE ahora sobre UN anillo por lado.
Corregir las 28 citas de §F.
- [ ] **Paso 5: spec del case rev. 22**: §5 estructura (anillo), §9 BOM, §11 abiertos.
- [ ] **Paso 6: commit** `"Los papeles alcanzan al anillo: pliego de mecanizado, cupon y
orden de montaje"`.

---

### Tarea 6: El render que enseña metal, y los pies (sonnet)

**Files:**
- Modify: `case/renders/render.py` (material «aluminio» ~80–83)
- Modify: `case/cad/sam17_case.scad` (`assembly_madera()` o `assembly_aluminio()`: `paticas()`; `bandeja_base_2d()`: cuatro taladros de pie)
- Modify: `case/check_dxf.py` (`guarda_zocalo()`: censo de los cuatro taladros de pie)

- [ ] **Paso 1: la puerta.** En `guarda_zocalo()`, además de las dos filas de M5, exigir
cuatro redondos de `d_pie_tornillo` (nuevo parámetro; el implementador lo lee de la hoja
de la patica citada en `bom()` — si no hay hoja, `M4` paso 4.5 y se marca SUPUESTO en el
comentario) en las posiciones de `paticas()`. ROJO: `bandeja_base_2d: faltan los 4
taladros de pie`.
- [ ] **Paso 2: el modelo.** Cuatro círculos en `bandeja_base_2d()` en las posiciones de
`paticas()`; `paticas()` entra en `assembly_madera()` (van bajo la tabla). VERDE.
- [ ] **Paso 3: el material.** En `render.py`, el aluminio pasa a satinado cepillado:
`"Roughness": 0.28`, `"Anisotropic": 0.6`, `"Anisotropic Rotation": 0.0` (nombres de
entrada del Principled BSDF de Blender 5.0: comprobar con
`print([i.name for i in n.inputs])` como manda el docstring del fichero). Base Color
(0.80, 0.81, 0.83). Los umbrales de cobertura/brillo del propio script tienen que seguir
en verde.
- [ ] **Paso 4: render y commit.** `"El aluminio se ve cepillado y el case tiene pies"`.
Abrir los dos PNG con el visor y compararlos con `referencia.png` al mismo ángulo:
la cara vista tiene que leerse estrecha, con arista que brilla, y sin filo naranja.

---

## Al terminar las seis

Revisión final de toda la rama en **opus** (whole-branch review de
`superpowers:requesting-code-review`), con este lente: (1) ningún assert de las dos
puertas se aflojó (`git diff main -U0 -- case/*.py | grep '^-.*assert'` explicado línea a
línea); (2) las dos copias de `ancho_util` y las gemelas .scad/.py de `centros_rosca_ciega`
coinciden releyendo el DXF; (3) el render final contra `referencia.png`. Luego
`superpowers:finishing-a-development-branch`.

## Lo que este plan NO hace

- **La trasera sigue enseñando canto** arriba y abajo (25.6 % del contorno medido el
  28-08). Es otra pieza y otro papel: los dos miembros traseros como marco de la trasera.
- **La meseta como repisa**, **la banda del valle que fluye a 27 N**, **la secuencia
  completa de montaje**, **el racking (#203)**: listados en la spec §10, quedan abiertos.
- El **cupón** físico del perfil: se pide en el pliego, no se dibuja aquí.
