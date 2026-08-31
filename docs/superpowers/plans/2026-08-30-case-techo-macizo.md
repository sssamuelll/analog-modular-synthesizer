# El techo macizo y las tres chapas empotradas — plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** el techo sin ranuras, con la salida de aire escondida bajo el alero, y
las tres chapas del canto (nariz, techo, talón) metidas 1 mm en un rebaje
fresado en la cara interior de los anillos, con su reborde de 1 × 3 alrededor.

**Architecture:** el patrón del repo — cada cota vive en el `.scad` (dibuja) y en
`clearance_budget.py` (verifica), y `check_dxf.py` relee los DXF y cruza las dos.
**El modelo ya está**, como vista previa (`a7dae55`, `54c7e69`), porque Samuel
tenía que verlo antes de aprobarlo; así que aquí el ROJO no viene de correr la
puerta nueva contra el `.scad` viejo, viene del **canario**: cada aserto se
prueba llamando a su puerta con un `dict(p)` mutado a los valores del diseño
viejo, y comprobando **el texto** del error. Es la misma prueba, y más fina: la
hace por aserto en vez de por puerta.

**Tech Stack:** OpenSCAD, Python 3 (ezdxf), Blender 5 para los renders.

**Spec:** `docs/superpowers/specs/2026-08-30-techo-macizo-chapas-empotradas-design.md`

## Global Constraints

- `params.scad` **numérico puro**; nada de expresiones. Los derivados
  (`rehundido_trasera`, `radio_borde`, `cara_anillo_trasera`, la muesca, lo que
  entra en rebaje, el fondo del cajeado) son **funciones gemelas** en el `.scad`
  y en el budget, nunca parámetros.
- **Cada parámetro nuevo lleva puerta por los dos lados.** Un aserto con solo
  cota inferior no cuenta (ya pasó dos veces: el radio y el alivio).
- Los umbrales de pared van contra **constantes** (`PARED_MIN_ANILLO = 3`), no
  contra el propio parámetro que se está midiendo.
- **Un canario por aserto, y salta por SU texto.** `canario_techo()` llama a la
  puerta objetivo directamente con el dict mutado; lo que otra puerta diga de la
  misma mutación no importa.
- **Los testigos no se eligen a mano**: cada guarda nueva se barre en un rango
  alrededor del valor adoptado y se comprueba dónde cambia de veredicto.
- Ningún tornillo visto; ningún taladro en el acrílico de la trasera.
- Los pies de la nariz y el talón **no se rehunden**: apoyan a ras en la tabla.
- La deuda **#242** (seis M4 del marco B bajo los rieles) no se crea ni se cierra
  aquí; el README la sigue nombrando.

---

### Task 1: `params.scad` — los comentarios que se perdieron, y la puerta del rebaje

**Files:**
- Modify: `case/cad/params.scad`
- Modify: `case/clearance_budget.py` (funciones derivadas + `guarda_rebaje_chapa()` + `canario_techo()`)

**Interfaces:**
- Produce: `_rehundido_trasera(p)`, `_radio_borde(p)`, `_muesca_pie(p)`,
  `_chapa_largo_rebaje(p)`, `guarda_rebaje_chapa(p)`, `canario_techo(p)`. Las
  tareas 2-4 las consumen.

- [ ] **Paso 1: restaurar los comentarios históricos.** La vista previa los
  sustituyó por una línea cada uno. Vuelven, con la enmienda al final, en:
  `talon_pie` (por qué 20 y no 18: la boca del avellanado y los 1.70 de aire),
  `techo_labio` (por qué 18 y no 13: 176 MPa contra 130, y que bajarlo es obligar
  6082-T6 en el pliego), `marco_fondo_trasera` (por qué 28 y no 26: 129 MPa
  contra 130), el bloque «**ESO NO ES NEGOCIABLE**» de la brida (el barrido del
  panel a `z >= t_anillo + t_placa`, y que el techo abría 52° en vez de 121.5),
  `potencia_disipada` (la suma itemizada de la fuente v2 §4), `meseta_paso_hp` y
  `meseta_largo_ranura` (por qué salieron del valle el 28-08). Y en
  `sam17_case.scad`, el comentario del bolsillo trasero y el de la brida.
  Cada uno conserva su razonamiento y **añade** la línea del 30-08 que lo
  enmienda. El repo guarda el porqué, no solo el número: un comentario borrado
  es una decisión que hay que volver a tomar dentro de un mes.

- [ ] **Paso 2: los derivados en el budget, gemelos del `.scad`.**

```python
def _rehundido_trasera(p: dict[str, float]) -> float:
    """Cuanto retrocede la cara vista de la trasera respecto al plano trasero,
    menos su junta. GEMELO de rehundido_trasera() en sam17_case.scad. Es
    DERIVADO y no parametro: lo manda la rendija (aire_labios), no el gusto."""
    return (p["rehundido_chapa"] + p["t_costilla"]
            + p["aire_labios"] - p["t_junta_asiento"])


def _radio_borde(p: dict[str, float]) -> float:
    """El radio del contorno del anillo donde hay chapa: concentrico con el
    arco exterior del pliegue, desplazado el rehundido. GEMELO de radio_borde()."""
    return p["radio_chapa"] + p["rehundido_chapa"]


def _muesca_pie(p: dict[str, float]) -> float:
    """Lo que se recorta en cada punta del desarrollo de nariz y talon para que
    el pie pase a ras mientras el resto entra en el rebaje. La pared del rebaje
    esta rebaje_chapa dentro de la cara, lo rehundido se queda hol_chapa antes y
    el pie llega hol_piel despues. GEMELO de muesca_pie()."""
    return p["rebaje_chapa"] - p["hol_chapa"] + p["hol_piel"]


def _chapa_largo_rebaje(p: dict[str, float]) -> float:
    """Lo que mide una chapa entre las paredes de los dos rebajes."""
    return p["ancho_total"] - 2 * (p["t_anillo"] + p["hol_piel"] - _muesca_pie(p))
```

- [ ] **Paso 3: `guarda_rebaje_chapa()`,** con los seis asertos del §6 de la
  spec, **cada uno con su texto propio** (el canario los distingue por él):
  `rebaje_chapa >= 2*t_costilla` («menos de 2 t»); el ancho del rebaje
  `_rehundido_trasera(p) - rehundido_chapa >= fresa_d` («la fresa no entra»);
  `rehundido_chapa >= 1` («reborde más fino que 1»); `hol_chapa >= 0.3`;
  `_chapa_largo_rebaje(p)` contra la luz menos `2*hol_chapa`; y la muesca con su
  alivio. Y **por los dos lados**: `rehundido_chapa` también tiene techo (si
  crece, el reborde se come el vano y la chapa deja de tapar el canto), y
  `hol_chapa` también (si crece, el canto de la chapa asoma por el reborde).

- [ ] **Paso 4: `canario_techo()`,** calcado de `canario_trasera()` (llama a la
  puerta con `dict(p)` mutado, comprueba el texto, y al final corre las puertas
  con los parámetros buenos para que quede verde). Los cuatro casos del §6:
  `rebaje_chapa = 2`, `aire_labios = 2.4`, `rehundido_chapa = 0.5`,
  `hol_chapa = 0.2`.

- [ ] **Paso 5: barrer, no elegir a mano.** Un barrido de cada parámetro nuevo
  en pasos de 0.1 sobre ±50 % del valor adoptado, imprimiendo dónde cambia el
  veredicto, y **comprobar que el borde cae donde la spec dice**. Si un
  parámetro pasa todo el barrido en verde, su aserto no muerde: es un testigo
  que coincide por accidente, y hay que arreglarlo antes de seguir.

- [ ] **Paso 6:** `guarda_rebaje_chapa` a `main()` **entre
  `guarda_trasera_capturada` y `guarda_aire`**, y `canario_techo` junto a
  `canario_trasera`. Correr `python case/clearance_budget.py`.

- [ ] **Paso 7: commit.**

```bash
git add case/cad/params.scad case/clearance_budget.py
git commit -m "La puerta del rebaje de chapa, con su canario y su barrido"
```

---

### Task 2: `guarda_tramo_trasero()` — la tabla del §4.3

**Files:**
- Modify: `case/clearance_budget.py`

**Interfaces:**
- Consume: `_rehundido_trasera(p)` de la Task 1.
- Produce: `_cara_anillo_trasera(p)`, `PARED_MIN_ANILLO`, `guarda_tramo_trasero(p)`.

- [ ] **Paso 1: el derivado y la constante.**

```python
PARED_MIN_ANILLO = 3.0   # lo minimo que se deja de pletina entre dos vaciados


def _cara_anillo_trasera(p: dict[str, float]) -> float:
    """La franja del tramo trasero: bolsillo de la trasera + su pared + lo que
    entra el costado. GEMELO de cara_anillo_trasera(). Fue 20 hasta el 30-08."""
    return (_rehundido_trasera(p) + (p["t_anillo"] - p["rehundido_acrilico"])
            + p["pared_rebaje_trasera"] + p["entrada_costado_trasero"])
```

- [ ] **Paso 2: `guarda_tramo_trasero()`** con la tabla del §4.3 banda por banda:
  bajo los dos labios de chapa (y = 6..19 y 230.18..239.18) el labio del bolsillo
  queda con **3 de hondo**, y **6** en el resto; `pared_rebaje_trasera >=
  PARED_MIN_ANILLO`; `entrada_costado_trasero >= 3`; el bolsillo cerrado en
  y = 239.18 y el cajeado desde 240.18. Cada aserto, su texto.

- [ ] **Paso 3: mudar el aserto de la pared.** Hoy vive en
  `guarda_trasera_capturada()` y se compara **contra sí mismo**. Se va de allí y
  llega aquí contra `PARED_MIN_ANILLO`. Comprobar que
  `guarda_trasera_capturada()` sigue verde sin él.

- [ ] **Paso 4: dos casos más en `canario_techo()`:**
  `entrada_costado_trasero = 2.5` («el costado entra 2.5») y
  `pared_rebaje_trasera = 2` («pared de 2 contra 3»).

- [ ] **Paso 5: barrido** de `entrada_costado_trasero` y `pared_rebaje_trasera`,
  como en la Task 1.

- [ ] **Paso 6:** a `main()` después de `guarda_rebaje_chapa`. Correr.

- [ ] **Paso 7: commit.**

```bash
git add case/clearance_budget.py
git commit -m "La puerta del tramo trasero, y la pared contra una constante"
```

---

### Task 3: `guarda_rendija()` y `guarda_aire()` reescrita — el alero es la salida

**Files:**
- Modify: `case/clearance_budget.py`
- Modify: `case/cad/params.scad` (`compresion_taco`, `taco_largo`, `taco_n`)

**Interfaces:**
- Consume: `_rehundido_trasera(p)` de la Task 1.
- Produce: `guarda_rendija(p)`, `_rendija(p) -> (area, y)`.

- [ ] **Paso 1: los tres parámetros de los tacos** en `params.scad`, numéricos:
  `taco_largo = 15`, `taco_n = 6` (por labio), `compresion_taco = 0.2`. Con su
  comentario: son de EPDM adhesivo, sujetan la plancha y **fijan la luz** — el
  taco es la luz, y la puerta la cuenta comprimida.

- [ ] **Paso 2: `guarda_rendija()`** — la subida capilar contra el solape:

```python
GAMMA_AGUA, RHO_AGUA = 0.073, 1000.0   # N/m y kg/m3 a 20 C, mojado total


def guarda_rendija(p: dict[str, float]) -> None:
    """El agua no puede subir por la rendija del alero hasta el canto de la
    trasera. Entre dos planos separados d el agua sube 2*gamma/(rho*g*d), y el
    peor caso no es la luz nominal sino la COMPRIMIDA: el taco cede un 20 % y
    la luz baja, que es cuando mas sube. Se exige margen de 2 mm sobre el
    solape porque la plancha viene alabeada y la luz local no es la nominal."""
    d = p["aire_labios"] * (1.0 - p["compresion_taco"]) / 1000.0
    subida = 2 * GAMMA_AGUA / (RHO_AGUA * G * d) * 1000.0
    # Lo que el labio tapa del canto de arriba de la trasera: 8.5 con el labio
    # en 20. _y_labio_techo() ya trae el chaflan y el labio; _trasera()["y1"]
    # es el canto de la plancha. La resta ES el solape, sin recomponerlo.
    solape = _trasera(p)["y1"] - _y_labio_techo(p)
    assert subida <= solape - 2.0 + 1e-9, (
        f"el agua sube {subida:.1f} mm por la rendija comprimida "
        f"({d*1000:.2f} mm de luz) y el labio solo tapa {solape:.1f} del canto "
        f"de la trasera: con menos de 2 de margen un alabeo la mete dentro")
```

- [ ] **Paso 3: `guarda_aire()` reescrita.** `_rejilla_valle()` deja de ser un
  término de salida y la salida pasa a ser la rendija:
  `(ancho_util - taco_n * taco_largo) * aire_labios` a la altura del labio.
  `potencia_disipada` a **9.22**. El aviso con `C_D = 0.55` se imprime, no
  asevera. Comprobar que la fila adoptada del §2 de la spec sale exacta:
  **9.7 / 12.4 / 13.9 K**. Si no sale, es que un dato de la spec y el código no
  cuadran — parar y decirlo, no ajustar el número para que salga.

- [ ] **Paso 4: `guarda_puentes_ventilacion()`** pierde su caso «meseta» (ya no
  hay ranuras que puentear ahí). `guarda_meseta_es_chapa()` se queda: sigue
  siendo verdad que la meseta es chapa.

- [ ] **Paso 5: cuatro casos más en `canario_techo()`:** `taco_largo = 90` (tira
  continua, 20.5 K) y `potencia_disipada = 14` (16.4 K) contra `guarda_aire`;
  `techo_labio = 18` (solape 6.5, sube 6.2 > 4.5) y `compresion_taco = 0.4`
  (luz 1.8, sube 8.3 > 6.5) contra `guarda_rendija`.

- [ ] **Paso 6: barrido** de `aire_labios`, `techo_labio` y `compresion_taco`,
  comprobando que el borde cae donde la spec dice.

- [ ] **Paso 7:** `guarda_rendija` a `main()` después de `guarda_tramo_trasero`.
  Correr; el presupuesto tiene que quedar en su **HUECO de siempre** (la fila de
  abajo), no en un rojo nuevo.

- [ ] **Paso 8: commit.**

```bash
git add case/cad/params.scad case/clearance_budget.py
git commit -m "La rendija del alero es la salida de aire, y su puerta capilar"
```

---

### Task 4: las puertas de hoy, recalibradas

**Files:**
- Modify: `case/clearance_budget.py`

- [ ] **Paso 1: `guarda_trasera_capturada()`** con `u0 = _rehundido_trasera(p)`
  (4.5) en vez de `rehundido_acrilico`, el chaflán de la plancha recalculado, y
  sin el aserto de la pared (se fue en la Task 2).

- [ ] **Paso 2: `guarda_talon()`** con el pie en 21.5 y la nariz en 19.5;
  comprobar que la boca del avellanado recupera sus **2.77 mm** de aire y que el
  aserto de «mismo estilo» (≤ 2 de diferencia entre los dos pies) queda verde.

- [ ] **Paso 3: `guarda_miembro_alto()`** con el labio de 20 y la brida en su
  cajeado: pletina bajo las roscas = `t_anillo - rebaje_chapa >= 8`; cajeado =
  huella + 0.5 por lado; R2 de la brida ≥ R1.5 del cajeado.

- [ ] **Paso 4: `guarda_marco_ventana()`** con la pata trasera a 30 y el retiro
  en 16; comprobar que da **1.45 mm y 106 MPa** (techos 2 mm y 130).

- [ ] **Paso 5: los desarrollos y las cajas.** `_talon()` a 41.23, `_nariz()`
  +1.5, `_miembro_alto()` sin ranuras y con el blank de 593.00 × 73.85,
  `_chasis()` adelantado 1.5, `_cajas_solidas` con las cajas movidas.

- [ ] **Paso 6: `canario_trasera()` recalibrado.** Los casos heredados que ya no
  saltan por lo suyo: el de `t_piel = 7` baja a **`t_piel = 4`** (con u0 = 4.5,
  una plancha de 7 sí deja 4.5 de canto plano y el caso dejó de probar nada); los
  dos de `guarda_talon` vuelven a saltar solos con el pie en 21.5 — **verificarlo
  corriendo, no suponerlo**.

- [ ] **Paso 7:** `python case/clearance_budget.py` → verde salvo el HUECO.
  Y una mutación de rotura a mano por cada puerta tocada, para ver que sigue
  mordiendo.

- [ ] **Paso 8: commit.**

```bash
git add case/clearance_budget.py
git commit -m "Las puertas de hoy con el rebaje: pies, labio de 20, pata de 30"
```

---

### Task 5: `check_dxf` y el export

**Files:**
- Modify: `case/check_dxf.py`
- Modify: `case/cad/sam17_case.scad` (la muesca y el alivio en los desarrollos 2D)
- Run: `case/export.ps1`

- [ ] **Paso 1: la muesca en los DXF.** La vista previa dejó la muesca solo en el
  sólido 3D (`// VISTA PREVIA:` en `nariz_2d()` y `talon_2d()`). Ahora va al
  desarrollo: **2.65 de hondo** desde el canto libre del pie hasta la línea de
  doblez, que está a `largo - BD45/2` (talón **21.06**, nariz **19.06** con los
  pies nuevos), con el **alivio de Ø2** centrado en la esquina, a caballo de esa
  línea. Quitar los dos comentarios `// VISTA PREVIA:`.

- [ ] **Paso 2: `techo_macizo()`** (nueva): en `miembro_alto_2d.dxf`, ningún
  contorno cerrado dentro del blank salvo los cuatro M4 de las bridas; esquinas
  de brida a R2.

- [ ] **Paso 3: `anillo_dorso_tiene_rebaje()`** (nueva): en
  **`costilla_dorso_2d.dxf`** (la cara mecanizada, **no** `costilla_2d`), el
  rebaje de 1..4.5 por el contorno de las chapas, fundido con el bolsillo de la
  trasera bajo los labios, y los dos cajeados de brida de 28 × 15.5. Las
  **profundidades no se leen de una planta**: van al PLIEGO y al cupón.

- [ ] **Paso 4: `anillo_tiene_ventana()`** reescrita: la cara mide `cara_anillo`
  en seis tramos y `_cara_anillo_trasera(p)` en el trasero. Hoy exige 20 uniforme
  y **pondría rojo el anillo correcto**.

- [ ] **Paso 5: sobres y radios:** los desarrollos con lo que entra a 545.62, la
  muesca y su alivio; `costilla_2d` con radios de **5.5** donde hay chapa y 4.5
  donde no (las salidas de los pies).

- [ ] **Paso 6: los tests de rotura, a mano** (las filas de `check_dxf` no son
  casos de canario). Uno por función nueva, cada uno params contra un DXF que no
  cuadra: el DXF de hoy con sus 16 ranuras contra `techo_macizo()`;
  `rehundido_chapa = 1.5` en params con el DXF a 1; `entrada_costado_trasero =
  2.5` (cara 21) con el DXF a 22; `hol_chapa = 0.3` con el DXF a 0.5. Cada uno se
  corre, se ve rojo, y se deshace.

- [ ] **Paso 7:** `case/export.ps1` completo y `python case/check_dxf.py` → VERDE.

- [ ] **Paso 8: commit.**

```bash
git add case/check_dxf.py case/cad/sam17_case.scad case/plans
git commit -m "check_dxf mira el rebaje en el dorso, la ventana por tramos y el techo macizo"
```

---

### Task 6: los renders

**Files:**
- Modify: `case/renders/render.py`
- Create: `case/renders/sam17-case-esquina.png`, `case/renders/sam17-case-esquina-perfil.png`

- [ ] **Paso 1:** las dos vistas de siempre, regeneradas.

- [ ] **Paso 2:** los **dos primeros planos de la esquina de arriba-atrás** (tres
  cuartos y perfil, 85 mm, los del 30-08) pasan a ser renders del repo: lo que se
  juzga en esta tanda es una esquina, y sin ese plano no se juzga. El guion de
  cámara está en el scratchpad del 30-08 (`esquina_techo.py`); se integra en
  `render.py` como dos vistas más, no como un guion aparte.

- [ ] **Paso 3: mirarlos.** Que el reborde de 1 mm recorra el contorno sin
  interrupciones, que el chaflán de la chapa vaya paralelo al del anillo, y que
  no asome ninguna pieza interior por el chaflán (fue el fallo del `54c7e69`).

- [ ] **Paso 4: commit.**

```bash
git add case/renders
git commit -m "Los renders, con los dos primeros planos de la esquina"
```

---

### Task 7: los papeles

**Files:**
- Modify: `case/README.md`, `case/PLIEGO.md`, `case/RFQ.md`
- Modify: las cinco specs del §9 de la spec

- [ ] **Paso 1: `case/README.md`** — piezas y BOM (techo sin ranuras, labio 20,
  blanks, muescas, 12 tacos), térmico (9.22 W, 9.7/12.4 K, entrada 46
  ranuras/7 065 mm² — hoy dice 44 y 6 781), y el **orden de ensamblaje**: los
  pasos 4-7 pasan a 4-6, con la tabla entrando con el anillo A y el chasis al
  final por la ventana de abajo. La deuda **#242** se sigue nombrando.

- [ ] **Paso 2: `case/PLIEGO.md` rev. 27** — anillo (rebaje de 3.5 × 3, cajeados
  de 28 × 15.5 × 3, radios 5.5, franja trasera 22, **el cupón gana el rebaje y su
  reborde**), techo macizo, desarrollos con muesca y alivio, el talón con el pie
  a 21.5 y la nariz a 19.5, juntas, esquinas de brida a R2. Las **profundidades**
  van aquí: el DXF es una planta y no las lleva.

- [ ] **Paso 3: `case/RFQ.md` rev. 26** — al mecanizado el rebaje, los cajeados y
  **la pregunta del reborde**: «¿un reborde de 1 × 3 a lo largo del contorno, a
  ±0.1? si no, 1.5». A la chapa, el techo sin ranuras.

- [ ] **Paso 4: las enmiendas del §9,** una por papel, con su fila:
  `2026-08-15-case-design.md` (rev. 27 en el historial),
  `2026-08-29-trasera-capturada-talon-nariz-design.md`,
  `2026-08-29-marco-ventana-banda-estructural-design.md`,
  `2026-08-27-case-esqueleto-visible-design.md` («la ventilación no se toca»,
  superado), `2026-08-28-costilla-pletina-design.md`. **Se aplican, no se
  prometen**: el repo ya arrastra specs que se mandan enmiendas unas a otras y
  nadie las ejecuta, y así main sostiene dos arquitecturas vivas a la vez.

- [ ] **Paso 5: commit.**

```bash
git add case/README.md case/PLIEGO.md case/RFQ.md docs/superpowers/specs
git commit -m "Los papeles del techo macizo, y las cinco enmiendas aplicadas"
```

---

### Task 8: revisor final y PR

- [ ] **Paso 1:** `python case/clearance_budget.py` y `python case/check_dxf.py`
  de nuevo, enteros, y el hook local.

- [ ] **Paso 2: revisor adversarial** sobre el diff completo de la rama
  (`codex exec review --base main`, con los agentes nombrados: `adrian-serrano`
  para contradicciones, `marcus-halberg` para viabilidad, `vex-rune` para
  complejidad). Arreglar todo hallazgo real; los que no lo sean, decir por qué.

- [ ] **Paso 3:** push y PR contra `main`, con el cuerpo diciendo qué cambió de
  forma y qué de número, y **lo que queda abierto** (§8 de la spec: el gotero, el
  ensayo térmico, el de derrame, la compresión del taco, los vatios de la bahía).

- [ ] **Paso 4:** lo aplazado se abre como **issue con evidencia**, no se queda
  en el cuerpo del PR.
