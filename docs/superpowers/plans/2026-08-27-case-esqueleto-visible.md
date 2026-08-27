# El esqueleto visible — plan de implementación

> **Para agentes:** SUB-SKILL OBLIGATORIA: usa `superpowers:subagent-driven-development`
> (recomendado) o `superpowers:executing-plans` para ejecutar tarea a tarea. Los
> pasos van en casillas (`- [ ]`).

**Goal:** el esqueleto de aluminio pasa por fuera y se ve; el acrílico pasa por
dentro; los tres perfiles 2020 comprados se sustituyen por miembros de chapa
doblada; y el hueco del valle se convierte en una bahía perforada estructural.

**Architecture:** modelo paramétrico OpenSCAD (`params.scad` + `sam17_case.scad`)
que exporta DXF planos, con dos presupuestos ejecutables en Python que corren
antes y después de exportar. **La puerta se escribe SIEMPRE primero y se ve en
ROJO antes de tocar el modelo.**

**Tech Stack:** OpenSCAD 2021.01, Python 3 + `ezdxf`, PowerShell (`export.ps1`),
Blender 5.0.1 para render, `codex exec` como motor de implementación.

**Spec:** [`../specs/2026-08-27-case-esqueleto-visible-design.md`](../specs/2026-08-27-case-esqueleto-visible-design.md)

---

## Global Constraints

Copiadas de la spec y del repo. Aplican a **todas** las tareas.

- **Ninguna tarea termina con una puerta en rojo.** `clearance_budget.py` y
  `check_dxf.py` salen en VERDE antes de cada commit.
- **La puerta va antes que el cambio, y hay que verla fallar.** Una puerta que
  nace en verde no ha demostrado que mide algo.
- **Toda puerta muerde por los dos lados**: hay un paso explícito que la rompe
  a propósito y comprueba que canta.
- **Ningún número sin fuente inline.** Lo no verificado se marca
  `SUPUESTO DECLARADO`.
- Cotas nuevas de la spec: `L_casquillo` = **9.5** · `t_junta` = **4** ·
  `ancho_total` pasa a **553.62** · `marco_sup` pasa a **3** ·
  `chasis_int_z` pasa a **61** · canal mínimo **20 × 20** en chapa de 3.
- Constantes del repo: `E_ALUMINIO` = 69 000 MPa · `RP02_ALUMINIO` = 130 MPa ·
  E del PMMA = 3 000 MPa · `SIGMA_PMMA` = 10 MPa · `carga_mano` = 200 N ·
  `flecha_costado_max` = 0.60 mm · `B_MANO` = 50 mm · `BORDE_MIN_D` = 1.5.
- **Fuera de este plan:** el patch bay en sí, la rev. 4 de la placa de la
  fuente, las bisagras vistas.

## El reparto de motores — quién ejecuta cada paso

Samuel pidió delegar a `codex`, que va **fuera de la factura de Claude** y es el
único delegado con sandbox real del sistema operativo. El reparto sale de la
skill `saver` §5 y **no es negociable**:

| paso | quién | por qué |
|---|---|---|
| **escribir la puerta** (el contrato) | **Claude** | «los tests se escriben con el cerebro caro y se revisan como código de producción». En este repo la puerta *es* el test |
| verla en ROJO | Claude | el rojo tiene que ser por la razón correcta, y eso es juicio |
| **tocar el modelo hasta VERDE** | **`codex`** | es la fila «iterar contra tests» de la matriz: el único que puede correr las puertas él mismo con superficie acotada |
| verificar el hash de la puerta | Claude | el sandbox acota la superficie, no el contrato |
| correr las DOS puertas + leer el diff | Claude | verde en una no basta |
| **romperla a propósito** | Claude | |
| review adversarial del resultado | **`codex` invocando a sus agentes** | tiene el mismo roster; panel de lentes disjuntos por cupo de ChatGPT |

**Invocación canónica para los pasos de codex** (el `--` y el `< /dev/null` no
son opcionales):

```bash
cd <worktree>
codex exec --sandbox workspace-write -c model_reasoning_effort=high \
  --json -o out.md -- "<contrato>" < /dev/null > events.jsonl
```

**Y en el prompt siempre**, literal: *«si crees que la puerta está mal, DILO en
vez de darle la vuelta»*. Cuando un delegado dice que un test está mal, suele
tener razón.

**Registrar cada delegación** en `~/.claude/skills/codex/usage.jsonl`: una línea
con `dur_s`, tokens del evento `turn.completed`, y `resultado` ∈ `exito` |
`parcial` | `fallo`.

## Estructura de ficheros

| fichero | responsabilidad en este plan |
|---|---|
| `case/cad/params.scad` | `L_casquillo`, `t_junta`, `marco_sup`, `chasis_int_z`, las cotas de los canales y de la retícula |
| `case/cad/sam17_case.scad` | orden de capas, `miembro_bajo_2d()`, `miembro_alto_2d()`, `bahia_2d()`, la retícula, dispatch `PART` |
| `case/clearance_budget.py` | `guarda_apilado()`, `guarda_casquillo()`, `guarda_reticula()`, `_centros_transversal()` reescrita |
| `case/check_dxf.py` | tres sobres nuevos, `taladros_costilla()` re-apuntada en T4 (pierde `centros_transversal()`), `taladros_costado()` resucitada en T3 |
| `case/cad/export.ps1` | las tres piezas nuevas en `$piezas` |
| `case/README.md`, `case/PLIEGO.md`, `case/RFQ.md` | BOM, bonding, ensamblaje |
| `docs/superpowers/specs/2026-08-15-case-design.md` | rev. 22 |

---

### Tarea 1: El chasis baja a lo que pide el toroide

La más pequeña y la única sin acoplar a nada. Va primera para calibrar el ciclo
de delegación con algo cuyo fallo no cuesta nada.

**Files:**
- Modify: `case/cad/params.scad` (`chasis_int_z`)
- Modify: `case/clearance_budget.py` (`guarda_chasis`, sección 3)

**Interfaces:**
- Consume: nada.
- Produce: `chasis_int_z` = 61, y con él `_chasis(p)["alto"]` = 64.

- [ ] **Paso 1: escribir la puerta primero** — que el interior no sea más alto
que lo que el toroide pide con su margen. Hoy hay un `exige` que comprueba lo
contrario (que quepa); falta el techo. En `guarda_chasis()`, sección 3, justo
después del `exige` del alto del toroide:

```python
    # Y QUE NO SOBRE. El assert de arriba pide que el toroide QUEPA; este pide
    # que la caja no sea mas alta de lo que hace falta. Sin el, 19 mm de aire
    # vivieron dentro del chasis sin que nadie los reclamara, y el volumen de
    # la caja es lo que se ve al abrir el case.
    holgura_alto = p["chasis_int_z"] - (p["alto_transformador"]
                                        + p["margen_transformador"])
    exige(0 <= holgura_alto <= 2,
          f"el interior del chasis mide {p['chasis_int_z']:.0f} de alto y el "
          f"toroide pide {p['alto_transformador'] + p['margen_transformador']:.0f} "
          f"({holgura_alto:+.0f} mm de aire). Es la unica cota del chasis que no "
          f"cuelga de una hoja de datos: la PCB manda en largo y en fondo, pero "
          f"el alto solo lo manda el toroide. Ver spec 8.1")
```

- [ ] **Paso 2: correr y ver ROJO** — `python case/clearance_budget.py`.
Esperado: `chasis_int_z` = 80 contra 61 pedidos, `+19 mm de aire`.

- [ ] **Paso 3 (codex): bajar `chasis_int_z` a 61** y comprobar que las cinco
cotas del reparto interior siguen cerrando. Contrato para el delegado:

```
En case/cad/params.scad, chasis_int_z pasa de 80 a 61. El numero sale de la
hoja del toroide Nuvotem RS0120P1: alto_transformador (46) + margen_transformador
(15). Escribe el comentario que diga de donde sale, en el estilo del fichero.

Luego corre `python case/clearance_budget.py` hasta que salga VERDE. NO toques
ninguna funcion guarda_*: si crees que una puerta esta mal, DILO en vez de darle
la vuelta.

Ojo con lo que cuelga del alto: chasis_pie, la fila de tornillos de la tapa, la
altura libre bajo la tapa del valle y el hueco de la bahia. Si algo de eso se
rompe, reportalo en vez de aflojarlo.
```

- [ ] **Paso 4: Claude verifica** — `git diff` a mano, y que
`clearance_budget.py` no aparezca en el diff salvo por la puerta del paso 1.
Correr las dos puertas.

- [ ] **Paso 5: probar que muerde** — subir `chasis_int_z` a 70 y ver que canta
por sobrar 9. Revertir.

- [ ] **Paso 6: commit**

```bash
git commit -am "El chasis baja 19 mm: el alto solo lo manda el toroide"
```

---

### Tarea 2: La inversión del apilado

El cambio que da la vuelta a la arquitectura. **No toca todavía los 2020** — eso
es la Tarea 4 — para que el modelo nunca quede a medias.

**Files:**
- Modify: `case/cad/params.scad` (`L_casquillo`, `t_junta`)
- Modify: `case/clearance_budget.py` (`leer_params`, `perfil`, `_cajas_solidas`,
  `guarda_apilado` nueva)
- Modify: `case/cad/sam17_case.scad` (`costados()`, `costillas()`)

**Interfaces:**
- Consume: nada.
- Produce: `p["L_casquillo"]` = 9.5 · `p["t_junta"]` = 4 · `p["ancho_total"]` =
  553.62 (derivado) · `perfil(p)["ancho_util"]` = 528.62 (sin cambio) ·
  `guarda_apilado(p) -> None`.

- [ ] **Paso 1: escribir la puerta primero.** Es la que dice qué capa va donde,
y tiene que fallar hoy. En `clearance_budget.py`, función nueva:

```python
def guarda_apilado(p: dict[str, float]) -> None:
    """El aluminio es la capa de FUERA y el acrilico la de dentro.

    NACE EL 2026-08-27 CON LA INVERSION, y es una puerta de ORDEN, no de cota:
    lo que verifica es cual pieza esta mas afuera, que hasta hoy era el acrilico
    y a partir de hoy es la costilla. Sin ella el orden de las capas vive en tres
    translate() del .scad y nadie lo cruza.

    Y verifica una segunda cosa que la primera no implica: que entre el acrilico
    y el marco quepa la JUNTA. El casquillo fija el hueco contra el peor caso del
    lote (spec 3.3), asi que en el caso nominal sobra sitio -- y ese sitio lo
    ocupa la junta, no el aire."""
    z_costilla = (0.0, p["t_costilla"])
    z_acrilico = (p["t_costilla"] + p["t_junta"],
                  p["t_costilla"] + p["L_casquillo"])
    assert z_costilla[1] <= z_acrilico[0], (
        f"el apilado esta al reves o sin junta: la costilla ocupa "
        f"z={z_costilla[0]:.2f}..{z_costilla[1]:.2f} y el acrilico arranca en "
        f"z={z_acrilico[0]:.2f}. Desde el 2026-08-27 el aluminio va POR FUERA "
        f"(spec 2, decision 1)")
    tol = 0.4 + 0.1 * p["t_cheek"]        # Schaeffer AG, 2026-08-18
    t_min, t_max = p["t_cheek"] - tol, p["t_cheek"] + tol
    assert p["L_casquillo"] >= t_max, (
        f"el casquillo mide {p['L_casquillo']:.2f} y el acrilico mas grueso del "
        f"lote mide {t_max:.2f} (tolerancia Schaeffer +-{0.4 + 0.1 * p['t_cheek']:.2f} "
        f"sobre {p['t_cheek']:.0f}). A ese espesor el acrilico quedaria PINZADO "
        f"entre dos caras de aluminio, y el PMMA fluye bajo carga sostenida: la "
        f"precarga que sujeta el riel se relaja sola en semanas. Ver spec 3.3")
    # LA CONDICION ES SOBRE EL JUEGO, no sobre el hueco. La primera version de
    # esta puerta comparaba (L - t_junta) contra t_min y HABRIA FALLADO con los
    # valores correctos: 5.5 contra 6.8. Lo que hay que exigir es que el juego
    # que deja el acrilico MAS DELGADO lo cubra la junta.
    juego = p["L_casquillo"] - t_min
    assert juego <= p["t_junta"], (
        f"el acrilico mas delgado del lote mide {t_min:.2f} y el casquillo "
        f"{p['L_casquillo']:.2f}: deja {juego:.2f} mm de juego y la junta solo "
        f"mide {p['t_junta']:.2f}. No llega a tocarlo, y un panel suelto en un "
        f"instrumento suena")
    print(f"apilado: costilla z 0..{p['t_costilla']:.0f} POR FUERA, junta de "
          f"{p['t_junta']:.0f}, acrilico hasta z={z_acrilico[1]:.2f}")
    print(f"  casquillo de {p['L_casquillo']:.2f} contra un acrilico de "
          f"{t_min:.2f}..{t_max:.2f}: nunca pinza, y la junta se come el juego "
          f"({juego:.2f} mm en el peor caso, sobre {p['t_junta']:.2f} de junta)")
```

Registrarla en `main()` junto a las demás `guarda_*`.

- [ ] **Paso 2: correr y ver ROJO** — `KeyError: 'L_casquillo'`. Ese es el rojo
correcto: la puerta pide parámetros que aún no existen.

- [ ] **Paso 3 (codex): los dos parámetros y la derivación del ancho.** Contrato:

```
En case/cad/params.scad anade dos parametros nuevos, con su comentario en el
estilo del fichero (que diga de DONDE sale el numero, no solo cual es):

  L_casquillo = 9.5;   // largo del casquillo de aluminio que atraviesa el
                       // acrilico en cada M4 de riel. Se dimensiona contra el
                       // acrilico MAS GRUESO del lote (8 + 1.2 = 9.2) mas 0.3
                       // de aire, para que el PMMA no quede nunca pinzado.
  t_junta     = 4;     // junta de EPDM entre el ala de la costilla y la cara
                       // del acrilico. Empuja el acrilico contra las piezas
                       // interiores y se come hasta 2.7 mm de juego.

En case/clearance_budget.py, leer_params() deriva ancho_total. Hoy es:
    largo_riel + hol_riel + 2*t_costilla + 2*t_cheek
Pasa a ser:
    largo_riel + hol_riel + 2*L_casquillo + 2*t_costilla
porque el acrilico deja de fijar el hueco: lo fija el casquillo. Da 553.62.
Actualiza el mensaje del SystemExit para que nombre los terminos nuevos.

En la misma funcion, perfil() calcula ancho_util como
    ancho_total - 2*t_cheek - 2*t_costilla
Pasa a
    ancho_total - 2*L_casquillo - 2*t_costilla
y tiene que seguir dando 528.62 exactos, que es largo_riel + hol_riel.

Corre `python case/clearance_budget.py`. Si crees que una puerta esta mal, DILO
en vez de darle la vuelta.
```

- [ ] **Paso 4: correr y ver VERDE en `guarda_apilado`**, y comprobar a mano que
`ancho_util` sigue en 528.62 y `ancho_total` pasó a 553.62.

- [ ] **Paso 5 (codex): voltear las capas en el `.scad`.** Contrato:

```
En case/cad/sam17_case.scad, dos modulos cambian de Z. HOY:

  module costados() {
      costado();
      translate([0, 0, ancho_total - t_cheek]) costado();
  }
  module costillas() {
      translate([0, 0, t_cheek]) costilla();
      translate([0, 0, ancho_total - t_cheek]) mirror([0, 0, 1]) costilla();
  }

La costilla pasa a ser la capa de FUERA (z 0..t_costilla) y el costado la de
dentro, arrancando en t_costilla + t_junta. Escribe el comentario que diga que
el orden lo verifica guarda_apilado() en clearance_budget.py.

Ojo con el mirror: la costilla del lado lejano tiene que seguir con sus alas
doblando hacia DENTRO del case.

Luego corre `powershell -NoProfile -File case/cad/export.ps1` hasta VERDE.
```

- [ ] **Paso 6: re-apuntar `guarda_costado()`** — spec §9.1. La puerta mide el
vano del acrílico contra la ventana de la costilla, y el 2026-08-27 se reescribió
para hacerlo con el aluminio **por dentro**. Ahora el acrílico está por dentro y
el apoyo le llega **por la otra cara**. La geometría del barrido no cambia —la
ventana está en el mismo sitio en X e Y— pero **el argumento sí**, y el
comentario largo de la función lo dice al revés. Reescribir el docstring y
verificar que el vano sigue dando **65.2 mm** y la flecha **0.11**; si esos dos
números se mueven, algo más cambió y hay que averiguar qué.

- [ ] **Paso 7: probar que muerde**, dos veces:
  - `L_casquillo` a 8 → tiene que cantar «el acrílico quedaría PINZADO».
  - `t_junta` a 2 → tiene que cantar que la junta no llega (2.7 de juego
    contra 2 de junta).

- [ ] **Paso 8: commit**

```bash
git commit -am "El aluminio pasa por fuera: el acrilico deja de ser la piel vista"
```

---

### Tarea 3: Los casquillos, y los cuatro taladros que vuelven al costado

**Files:**
- Modify: `case/cad/sam17_case.scad` (`costado_2d()`)
- Modify: `case/check_dxf.py` (`taladros_costado()` nueva, `taladros_costilla()`)

**Interfaces:**
- Consume: `p["L_casquillo"]` de la Tarea 2.
- Produce: 4 agujeros de d = `d_M4_paso + 2*hol_casquillo` en `costado_2d.dxf`,
  en los centros de `_centros_rail(p, P)`.

- [ ] **Paso 1: escribir la puerta primero.** El costado quedó sin un solo
taladro el 2026-08-27 y `taladros_con_material()` se borró por quedarse sin
sujeto. Vuelve, con criterio nuevo: son **de paso, no de apriete**. En
`check_dxf.py`:

```python
# Holgura del agujero del acrilico ALREDEDOR del casquillo, por lado. No es
# holgura de montaje: es lo que garantiza que el apriete va costilla ->
# casquillo -> riel y NUNCA toca el PMMA. Con 0 el casquillo hace de escariador
# y vuelve el modo de fallo que spec 3.2 evita.
HOL_CASQUILLO = 0.5


def taladros_costado() -> list[str]:
    """Los cuatro agujeros del costado son DE PASO y no de apriete.

    Esta puerta murio el 2026-08-27 -- cuando el costado quedo sin tornillos se
    quedo sin sujeto -- y vuelve el mismo dia con otro criterio. Lo que verifica
    ya no es que haya acrilico para apretar contra el, sino lo contrario: que el
    agujero sea lo bastante GRANDE para que el casquillo pase holgado y el
    tornillo no muerda nunca el PMMA.

    Son exactamente cuatro: uno por Z-Rail. Cualquier otro redondo en esta pieza
    sobra -- el costado es piel."""
    import clearance_budget as cb

    p = cb.leer_params()
    P = cb._vertices(p)
    cr = cb._centros_rail(p, P)
    d_esperado = p["d_M4_paso"] + 2 * HOL_CASQUILLO + p["kerf"]
    leidos = _redondos("costado_2d")
    f: list[str] = []
    if len(leidos) != len(cr):
        f.append(f"costado_2d: {len(leidos)} agujeros redondos y el modelo pone "
                 f"{len(cr)}, uno por Z-Rail. El costado es PIEL: no lleva mas")
        return f
    contorno = _contorno_costado()
    for nm, c in zip(cb.NOMBRES_CR, cr):
        cerca = [q for q in leidos
                 if math.hypot(q[0] - c[0], q[1] - c[1]) <= DESVIO_DXF_MAX]
        if not cerca:
            f.append(f"costado_2d: falta el paso de casquillo de '{nm}' en "
                     f"({c[0]:.2f}, {c[1]:.2f})")
            continue
        if abs(cerca[0][2] - d_esperado) > 0.1:
            f.append(f"costado_2d: el agujero de '{nm}' mide "
                     f"{cerca[0][2]:.2f} y se exige {d_esperado:.2f} (paso M4 + "
                     f"2 x {HOL_CASQUILLO} de holgura de casquillo). Si sale a "
                     f"medida del tornillo, el apriete muerde el PMMA y la "
                     f"precarga del riel se relaja sola")
        dist = _dist_al_contorno(contorno, c)
        if dist < BORDE_MIN_D * d_esperado:
            f.append(f"costado_2d: el agujero de '{nm}' cae a {dist:.2f} mm del "
                     f"canto y se exige {BORDE_MIN_D * d_esperado:.2f}")
    if not f:
        print(f"  costado_2d: los 4 pasos de casquillo miden {d_esperado:.2f} "
              f"(M4 + 2 x {HOL_CASQUILLO}) y tienen acrilico alrededor")
    return f
```

Registrarla en `main()`.

- [ ] **Paso 2: correr y ver ROJO** — `0 agujeros redondos y el modelo pone 4`.

- [ ] **Paso 3 (codex): devolverle los cuatro al costado.** Contrato:

```
En case/cad/sam17_case.scad, costado_2d() es hoy un contorno pelado:

  module costado_2d() { perfil_lateral(); }

Vuelve a llevar CUATRO agujeros, uno por centro de centros_rail(), de diametro
d_M4_paso + 2*0.5 + kerf. NO son agujeros de tornillo: son el PASO del casquillo
de aluminio que atraviesa el acrilico, y por eso van holgados. Escribe el
comentario explicando esa diferencia -- que el apriete va costilla -> casquillo
-> riel y no toca el PMMA nunca -- y que la holgura la fija HOL_CASQUILLO en
check_dxf.py.

Los M5 de transversal NO vuelven: esos siguen en la costilla.

Corre `powershell -NoProfile -File case/cad/export.ps1` hasta VERDE.
```

- [ ] **Paso 4: correr las dos puertas y ver VERDE.**

- [ ] **Paso 5: probar que muerde**, dos veces:
  - poner el agujero a `d_M4_paso` exacto → tiene que cantar por diámetro.
  - añadir un quinto redondo → tiene que cantar por censo.

- [ ] **Paso 6: commit**

```bash
git commit -am "Vuelven cuatro agujeros al costado, y son de paso y no de apriete"
```

---

### Tarea 4: Los tres miembros de chapa — VA ENTERA, y aquí está el porqué

**No se puede partir.** El 2026-08-27, ejecutando el plan anterior, se aprendió
midiendo: quitar un larguero pone roja a `guarda_costado()` mientras el acrílico
siga contando como portante, y las tareas 7, 9 y 10 de aquel plan tuvieron que
fundirse en un solo commit. Aquí pasa lo mismo con las tres barras y sus
herederos: **mueren y nacen juntos o el modelo mide un estado a medias.**

**Files:**
- Modify: `case/cad/params.scad` (cotas de canal, `marco_sup`)
- Modify: `case/cad/sam17_case.scad` (`miembro_bajo_2d()`, `miembro_alto_2d()`,
  `bahia_2d()`, `centros_transversal()` muere, dispatch)
- Modify: `case/clearance_budget.py` (`_seccion_canal()`, `guarda_miembros()`,
  `_cajas_solidas`, `guarda_tapa`)
- Modify: `case/check_dxf.py` (tres sobres nuevos)
- Modify: `case/cad/export.ps1`

**Interfaces:**
- Consume: `p["t_costilla"]` = 3 · `perfil(p)["ancho_util"]` = 528.62 · **y
  `z0`/`z1` de `_cajas_solidas` tal como los deja la Tarea 2** — son las caras
  internas del case y cambiaron de dueño al invertir el apilado: antes salían de
  `t_cheek + t_costilla`, ahora del alma de la costilla que está por fuera. Las
  cajas de los tres miembros van entre esos dos.
- Produce: `_seccion_canal(w, d, t) -> (I, area, ymax)` ·
  `_secciones_miembro(p) -> [(nombre, w, d), ...]` con los nombres exactos
  `"trasero bajo"`, `"trasero alto"` y `"bahia"` ·
  `bbox_desarrollo_miembro(p, cual) -> (w, h)` donde `cual` es uno de esos tres
  nombres · `bbox_desarrollo_bahia(p) -> (w, h)`.

- [ ] **Paso 1: la autocomprobación de la sección, ANTES de la función.** Es el
patrón que salvó la costilla el 2026-08-26: el número a mano primero, la función
después. Con `w = d = 20`, `t = 3`, la convención de spec §4.1 (cotas
exteriores, tres rectángulos: alma `t × w` y dos alas `d × t`):

```python
def autocomprobacion_canal() -> None:
    """La seccion del canal, a mano, ANTES de escribir la funcion.

    Convencion de spec 4.1: canal en U de cotas EXTERIORES w (perpendicular a la
    carga) x d (en la direccion de la carga), chapa de espesor t. Tres
    rectangulos: el alma (t x w) y las dos alas (d x t).

    Con w = d = 20 y t = 3, midiendo x desde la cara exterior del alma:
      alma:  A = 3*20 = 60,   centroide x = 1.5
      alas:  A = 20*3 = 60 cada una, centroide x = 10
      A total = 180
      xb = (60*1.5 + 2*60*10) / 180 = (90 + 1200) / 180 = 7.1667
      I = [20*3^3/12 + 60*(7.1667-1.5)^2] + 2*[3*20^3/12 + 60*(10-7.1667)^2]
        = [45 + 1926.7] + 2*[2000 + 481.6]
        = 1971.7 + 4963.2 = 6934.9
    """
    I, A, _ = _seccion_canal(20.0, 20.0, 3.0)
    assert abs(A - 180.0) < 1e-6, f"area {A:.4f}, a mano 180"
    assert abs(I - 6934.9) < 0.5, f"I = {I:.1f}, a mano 6934.9"
```

- [ ] **Paso 2: escribir `guarda_miembros()`, la puerta.** Cada miembro tiene
que ganarle al 2020 que sustituye, con su propia carga:

```python
# Inercia de un 2020 ranurado de catalogo. SUPUESTO DECLARADO: cifra de oficio,
# no de hoja. Va aqui y no en params.scad porque es la pieza que se JUBILA -- es
# el listón contra el que se mide su sustituto, no una cota del case.
I_2020 = 5600.0


def guarda_miembros(p: dict[str, float]) -> None:
    """Cada miembro de chapa le gana al 2020 que sustituye.

    La comparacion es a IGUAL ENVOLVENTE, que es la unica honesta: un canal mas
    profundo gana siempre y eso no dice nada. Si un miembro necesita mas fondo
    que 20, el que sube es su parametro y esta puerta lo sigue midiendo contra
    el mismo 2020."""
    for nombre, w, d in _secciones_miembro(p):
        I, A, _ = _seccion_canal(w, d, p["t_costilla"])
        assert I >= I_2020, (
            f"el miembro '{nombre}' es un canal {w:g}x{d:g} en chapa de "
            f"{p['t_costilla']:g} y da {I:.0f} mm4 contra los {I_2020:.0f} del "
            f"2020 que sustituye. Un canal de 20x20 ya da 6935: si este no "
            f"llega, la seccion esta mal puesta")
        print(f"  miembro '{nombre}': canal {w:g}x{d:g} -> I={I:.0f} mm4 "
              f"({I/I_2020:.2f}x el 2020), {A*perfil(p)['ancho_util']*2.70e-6:.3f} kg")
```

- [ ] **Paso 3: correr y ver ROJO** — `NameError: _seccion_canal`.

- [ ] **Paso 4 (codex): las dos funciones de sección.** Contrato:

```
En case/clearance_budget.py escribe DOS funciones, y nada mas:

  _seccion_canal(w, d, t) -> (I, area, ymax)
      Perfil en U de cotas EXTERIORES w x d en chapa de espesor t. Tres
      rectangulos: el alma (t de ancho en la direccion de la carga, w de largo)
      y las dos alas (d en la direccion de la carga, t de espesor). Devuelve la
      inercia respecto del eje neutro de la seccion completa contra flexion en
      la direccion d, el area, y la distancia del centroide a la fibra mas
      alejada.

  _secciones_miembro(p) -> [(nombre, w, d), ...]
      Los tres miembros con su seccion: "trasero bajo", "trasero alto" y
      "bahia". Arranca los tres en 20 x 20 leyendo de params.scad
      (canal_ancho / canal_fondo), que hay que anadir alli con su comentario.

La funcion autocomprobacion_canal() que ya esta escrita en el fichero tiene que
pasar SIN TOCARLA: con w=d=20 y t=3 pide area 180 y I 6934.9. Si tu formula no
da eso, la formula esta mal -- no la autocomprobacion.

Registra autocomprobacion_canal() y guarda_miembros() en main().
Corre `python case/clearance_budget.py`. Si crees que una puerta esta mal, DILO.
```

- [ ] **Paso 5: Claude verifica el hash** de `autocomprobacion_canal` — es el
contrato y no lo puede haber tocado:

```bash
git diff case/clearance_budget.py | grep -A2 "autocomprobacion_canal"
```

Si aparece modificada, la tarea la hace Claude.

- [ ] **Paso 6 (codex): los tres desarrollos y la muerte de los 2020.** Es el
paso grande y va con `--sandbox workspace-write` en worktree. Contrato:

```
En case/cad/sam17_case.scad:

1. Escribe miembro_bajo_2d(), miembro_alto_2d() y bahia_2d(). Los tres son
   DESARROLLOS PLANOS de chapa de 3 mm doblada, no contornos de la pieza
   montada. Usa las mismas funciones de plegado que ya existen para la costilla
   (cost_sb, cost_ba, cost_bd) pero con su propio radio si hace falta -- mira
   como lo hace pv_sb()/pv_ba() para la pestana del valle.

   - miembro_bajo_2d: canal en U de canal_ancho x canal_fondo, largo ancho_util.
   - miembro_alto_2d: LO MISMO mas la meseta -- una cara horizontal de
     prof_sup mm (hoy 37) en el ala de arriba. Es una sola pieza doblada: la
     barra y la tapa de remate se funden, y remate_sup_2d MUERE como pieza
     aparte.
   - bahia_2d: bandeja de fondo perforado con las dos alas largas dobladas hacia
     ARRIBA. Las alas son los cantos donde apoya la tapa del valle.

2. centros_transversal() y sus tres accesores (ct_base, ct_valle, ct_remate)
   MUEREN. Lo que colgaba de ellos pasa a colgar de los miembros. Deja tumba con
   comentario, como se hizo con paso_tira.

3. Anade los tres PART al dispatch y las tres piezas a case/cad/export.ps1.

NO inventes cotas. Todo lo que no este en params.scad, anadelo alli con un
comentario que diga de donde sale. Si una cota no la puedes derivar de nada,
NO la inventes: dila en tu respuesta y para.

Corre `powershell -NoProfile -File case/cad/export.ps1`. Si una puerta esta mal,
DILO en vez de darle la vuelta.
```

- [ ] **Paso 6b (codex): `marco_sup` de 8 a 3, y la trasera crece.** Va en esta
tarea y no aparte porque la meseta ES el miembro alto. Contrato:

```
En case/cad/params.scad, marco_sup pasa de 8 a 3: la meseta de remate deja de
ser acrilico y pasa a ser la cara horizontal del miembro trasero alto, que es
chapa de 3.

Se comprobo que es limpio: marco_sup llego a sostener una puerta de "junta
cero" contra el riel, pero esa puerta MURIO el 2026-08-21 cuando la tapa de
remate paso de pegada a atornillada. Hoy marco_sup solo fija tres cosas:
  - el espesor de la meseta,
  - la Y del miembro trasero alto (P[5].y - marco_sup - r),
  - el canto alto de la trasera (P[5].y - marco_sup).

Consecuencia esperada, y si no sale asi PARA y dilo: el miembro sube 5 mm y la
trasera crece 5 mm de alto. guarda_remate() -- que exige que la tapa cubra la
meseta entera -- tiene que seguir en verde.

Corre las dos puertas. Si una esta mal, DILO en vez de darle la vuelta.
```

- [ ] **Paso 6c (Claude): re-apuntar `guarda_tapa()`** — spec §5.2. La tapa del
valle deja de apoyar en el larguero `valle` y pasa a apoyar en **las dos alas de
la bahía**. Lo que cambia en la puerta es de dónde sale el vuelo:

```python
    # EL APOYO CAMBIO DE DUENO el 2026-08-27. Era el larguero del valle -- una
    # barra de 20 centrada bajo la tapa, con la tapa volando 23.24 a cada lado.
    # Ahora son las DOS ALAS de la bahia, que estan mas separadas, asi que la
    # tapa vuela menos: 14.00. Y la tapa deja de ser tapa -- es la PUERTA de la
    # bahia, el frente desmontable que se quita para entrar (spec 5.2).
    x0_b, x1_b = _cantos_bahia(p)
    vol = max(x0_b - x0, x1 - x1_b)
```

Y el `assert` de flecha no cambia de forma: cambia el número que le entra.
**Tiene que bajar de 0.10 a algo menor**; si sube, el apoyo se puso peor y hay
que averiguar por qué antes de seguir.

- [ ] **Paso 6d (codex): lo que la muerte de `centros_transversal()` rompe.**
Sale del escaneo previo: dos consumidores se quedan sin función y ninguna tarea
los reclamaba. Contrato:

```
Al borrar centros_transversal() se rompen DOS cosas que hay que arreglar en el
mismo commit, porque el modelo no puede quedar a medias:

1. taladros_costilla() en case/check_dxf.py saca de ahi el censo de los M5 de
   transversal. Ese censo pasa a ser el de los TORNILLOS DE MIEMBRO: los que
   atornillan cada miembro de chapa a la costilla por su punta. Sigue siendo el
   mismo criterio -- material alrededor, BORDE_MIN_D x D -- solo que la lista
   viene de _secciones_miembro() en vez de centros_transversal().

2. El modulo bom() de case/cad/sam17_case.scad llama a centros_transversal() en
   cinco sitios: el conteo de transversales, los M5 de punta, los M4 de riel y
   dos lineas de texto. Actualizalo para que hable de MIEMBROS DE CHAPA y no de
   perfiles 2020, y para que el conteo salga de los tres desarrollos nuevos.

El eco del BOM es un papel: si dice algo que ya no es cierto, el README lo copia
y el error viaja al taller. Ya paso el 2026-08-27.

Corre las dos puertas y `openscad -D 'PART="bom"'` para leer el eco.
```

- [ ] **Paso 7 (Claude): los tres sobres.** Los escribe Claude porque son el
contrato de lo que va al taller. En `check_dxf.py`, `_sobres()`, después del
bucle sobre `planchas`:

```python
    # Los tres miembros de chapa: sus DXF son DESARROLLOS y salen mas grandes
    # que la pieza doblada, igual que la costilla y la tapa del valle. Derivados,
    # no escritos a mano.
    dims["miembro_bajo_2d"] = cb.bbox_desarrollo_miembro(p, "trasero bajo")
    dims["miembro_alto_2d"] = cb.bbox_desarrollo_miembro(p, "trasero alto")
    dims["bahia_2d"] = cb.bbox_desarrollo_bahia(p)
```

- [ ] **Paso 8: correr las dos puertas y el export.** VERDE las dos.

- [ ] **Paso 9: Claude lee el diff entero a mano.** Obligatorio: es el commit
más grande del plan y el que puede dejar un hueco silencioso.

- [ ] **Paso 10: probar que muerde**, cuatro veces:
  - `canal_fondo` a 8 → `guarda_miembros` canta por no llegar al 2020.
  - borrar un ala de `bahia_2d` → el sobre canta por bbox.
  - mover un miembro 20 mm → `solapes()` canta.
  - `marco_sup` de vuelta a 8 → `guarda_remate()` o el sobre del miembro alto
    tiene que cantar; si ninguna canta, la meseta no está atada a nada.

- [ ] **Paso 11: commit**

```bash
git commit -am "Se van los tres 2020: el marco es el esqueleto entero"
```

---

### Tarea 5: La retícula, que es lo que devuelve la ranura en T

**Files:**
- Modify: `case/cad/params.scad` (`reticula_paso`)
- Modify: `case/cad/sam17_case.scad` (los tres `*_2d` de la Tarea 4)
- Modify: `case/clearance_budget.py` (`guarda_reticula()`)

**Interfaces:**
- Consume: `_secciones_miembro(p)` de la Tarea 4.
- Produce: `guarda_reticula(p) -> None`.

- [ ] **Paso 1: escribir la puerta primero.** Sin ella se pierde en silencio la
propiedad que la ranura en T daba gratis:

```python
def guarda_reticula(p: dict[str, float]) -> None:
    """Todo tornillo de plancha cae en un agujero de la reticula de su miembro.

    ES LA PIEZA QUE SUSTITUYE A LA RANURA EN T, y por eso hay puerta. El 2020
    traia una ranura corrida y tuercas de insercion lateral, o sea que un
    tornillo se podia anadir DESPUES sin desarmar el case. Con canales de chapa
    eso se acaba: cada agujero se decide en el DXF.

    Lo que se pierde en libertad se devuelve en reticula -- una fila de agujeros
    a paso regular a lo largo de cada canal --, y lo que esta puerta impide es
    que una fila de plancha caiga ENTRE dos agujeros de la reticula, que es un
    fallo que no se ve hasta el dia del montaje.

    Encaja con lo declarado: la spec del case dice desde la rev. 1 que la
    reticula visible y regular de puntos de union es el ornamento permitido."""
    _, _, filas = _cajas_solidas(p)
    paso = p["reticula_paso"]
    au = perfil(p)["ancho_util"]
    n = max(1, round(au / paso))
    rejilla = [au * (i + 0.5) / n for i in range(n)]
    for placa, fila, eje, coord, miembro in filas:
        d = min(abs(coord - r) for r in rejilla)
        assert d <= TOL_ALINEACION, (
            f"la fila '{fila}' de {placa} cae a {d:.3f} mm del agujero mas "
            f"cercano de la reticula de '{miembro}' (paso {paso:.0f}, "
            f"{n} agujeros sobre {au:.2f}). El 2020 tenia ranura corrida y esto "
            f"daba igual; un canal de chapa no la tiene")
    print(f"reticula: paso {paso:.0f} mm, {n} agujeros por miembro sobre "
          f"{au:.2f}; las {len(filas)} filas de plancha caen todas en uno")
```

- [ ] **Paso 2: correr y ver ROJO** — `KeyError: 'reticula_paso'`.

- [ ] **Paso 3 (codex): la retícula.** Contrato:

```
Anade reticula_paso = 100 a case/cad/params.scad con su comentario: es el paso
nominal de la fila de agujeros de cada miembro de chapa, y sustituye a la ranura
en T del 2020 que se jubilo. 100 es el mismo paso que ya usa fila_agujeros()
para las planchas, asi que las filas existentes caen en la reticula por
construccion -- ese es el motivo del numero, no una preferencia.

Luego dibuja la reticula en los tres desarrollos (miembro_bajo_2d,
miembro_alto_2d, bahia_2d): una fila de agujeros de d_M3_paso a lo largo del
alma de cada canal, con el mismo reparto que hace fila_agujeros() -- n =
round(largo/paso) agujeros con margenes iguales de medio paso.

Corre `python case/clearance_budget.py` y luego el export. Si una puerta esta
mal, DILO.
```

- [ ] **Paso 4: correr y ver VERDE.**

- [ ] **Paso 5: probar que muerde** — `reticula_paso` a 137 (un número que no
divide bien) y ver que alguna fila de plancha se sale. Revertir.

- [ ] **Paso 6: commit**

```bash
git commit -am "La reticula devuelve lo que la ranura en T daba gratis"
```

---

### Tarea 6: Los papeles, el bonding y la rev. 22

**Files:**
- Modify: `case/README.md`, `case/PLIEGO.md`, `case/RFQ.md`
- Modify: `case/cad/sam17_case.scad` (el eco del BOM)
- Modify: `docs/superpowers/specs/2026-08-15-case-design.md` (rev. 22)

- [ ] **Paso 1: el eco del BOM PRIMERO.** El 2026-08-27 se aprendió que el eco
es un papel tan atrasado como los otros, y que recontar desde él propaga el
error. Antes de tocar el README, `openscad -D 'PART="bom"'` tiene que decir la
verdad: los tres miembros, la bahía, los casquillos, la junta, y **cero 2020**.

- [ ] **Paso 2: `PLIEGO.md`** — el proveedor de perfil se va; la chapa de
aluminio pasa de tres piezas a seis; el acrílico pierde la meseta. Y entra la
sección de **bonding** de spec §3.4: arandela de diente o enmascarado antes de
anodizar, decidido **en el pliego** y no al montar.

- [ ] **Paso 3: `RFQ.md`** — al taller de chapa se le añaden tres piezas y una
pregunta eliminatoria nueva: *«¿pueden enmascarar zonas antes de anodizar, o
suministran sin anodizar para que anodicemos después?»*. Es la pregunta que
decide si la continuidad de PE se puede garantizar.

- [ ] **Paso 4: `README.md`** — BOM recontado contra el eco del paso 1, el orden
de ensamblaje con los casquillos y la junta, y el **procedimiento de
verificación de PE con miliohmímetro (≤ 0.1 Ω)**, que bloquea el primer
encendido y no el corte.

- [ ] **Paso 5: spec del case, rev. 22** — §5 (Estructura) otra vez, §9 (BOM) y
§11 con lo que este plan deja abierto.

- [ ] **Paso 6 (codex, review adversarial): que lo revisen sus agentes.**

```bash
codex exec --sandbox read-only -o audit.md -- "Revisa el diff de esta rama contra main invocando a los agentes que tengas: adrian-serrano para incertidumbre peligrosa y contradicciones, marcus-halberg para viabilidad, vex-rune para complejidad accidental. Consolida sus hallazgos; no los resumas por tu cuenta." < /dev/null
```

- [ ] **Paso 7: commit**

```bash
git commit -am "Los papeles alcanzan al esqueleto visible, y entra el bonding"
```

---

## Lo que este plan NO hace

- **El patch bay.** Este plan le hace sitio y superficie; no lo diseña.
- **La rev. 4 de la placa de la fuente**, que es lo que libera el largo del
  chasis. El modelo ya lo deriva de `chasis_pcb_ancho`: cuando exista la placa,
  el chasis se ajusta solo.
- **Cerrar el racking (#203).** Deuda heredada; se cierra cargando el prototipo.
- **La especie y la humedad de la tabla.** Heredado, bloquea el pedido de
  carpintería y no este plan.
- **El render.** `render.py` importa los assemblies; cuando los miembros entren
  en `assembly_esqueleto()` el render los coge solo. Si no, es un hallazgo.
