# El esqueleto de aluminio — plan de implementación

> **Para agentes:** SUB-SKILL OBLIGATORIA: usa `superpowers:subagent-driven-development`
> (recomendado) o `superpowers:executing-plans` para ejecutar tarea a tarea. Los
> pasos van en casillas (`- [ ]`).

**Goal:** el costado de acrílico deja de ser portante y la estructura pasa a
dos costillas de aluminio fresado con tiras de canto en L, absorbiendo los
cuatro largueros 2020 del interior.

**Architecture:** modelo paramétrico OpenSCAD (`params.scad` + `sam17_case.scad`)
que exporta DXF planos, con dos presupuestos ejecutables en Python que se
corren antes y después de exportar. **La puerta se escribe SIEMPRE primero y se
ve en ROJO antes de tocar el modelo** — es el patrón del plan de 2026-08-24 y
no se negocia aquí.

**Tech Stack:** OpenSCAD 2021.01, Python 3 + `ezdxf`, PowerShell (`export.ps1`),
Blender 5.0.1 para render.

**Spec:** [`../specs/2026-08-26-case-esqueleto-aluminio-design.md`](../specs/2026-08-26-case-esqueleto-aluminio-design.md)

## Global Constraints

Copiadas literalmente de la spec y del repo. Aplican a **todas** las tareas.

- **Ninguna tarea termina con una puerta en rojo.** `clearance_budget.py` y
  `check_dxf.py` salen en VERDE antes de cada commit. Si una queda roja, la
  tarea no está hecha.
- **La puerta va antes que el cambio, y hay que verla fallar.** Una puerta que
  nace en verde no ha demostrado que mide algo.
- **Toda puerta muerde por los dos lados**: hay un paso explícito que la rompe
  a propósito y comprueba que canta.
- **Ningún número sin fuente inline.** Constante nueva = comentario que dice de
  dónde sale. Lo no verificado se marca `SUPUESTO DECLARADO`, no se suaviza.
- **Añadir antes de quitar.** El orden de tareas está elegido para que el
  modelo nunca quede a medias: primero existen la costilla y las transversales,
  y solo entonces se van los largueros.
- Constantes del repo: `E_ALUMINIO` = 69 000 MPa · `RP02_ALUMINIO` = 130 MPa ·
  E del PMMA = 3 000 MPa · `SIGMA_PMMA` = 10 MPa · `carga_mano` = 200 N ·
  `flecha_costado_max` = 0.60 mm · `B_MANO` = 50 mm.
- **Fuera de este plan:** el zócalo de madera (§9 de la spec). Va en plan
  aparte y no bloquea nada de aquí.

## Estructura de ficheros

| fichero | responsabilidad en este plan |
|---|---|
| `case/cad/params.scad` | los parámetros nuevos, cada uno con su porqué |
| `case/cad/sam17_case.scad` | `costilla_2d()`, `tira_canto_2d()`, transversales, dispatch `PART` |
| `case/clearance_budget.py` | `guarda_riel_cabe()`, `guarda_costilla()`, `guarda_piso()` reescrita |
| `case/check_dxf.py` | `guarda_costado()` → mide la costilla; `railes_dentro_del_costado()` |
| `case/cad/export.ps1` | las piezas nuevas en `$piezas` |
| `case/README.md`, `case/PLIEGO.md`, `case/RFQ.md` | BOM, ensamblaje, cuarto proveedor |
| `docs/superpowers/specs/2026-08-15-case-design.md` | rev. 21 |

---

### Tarea 1: Cerrar §8.1 — el paso de tornillo decide si la L es maciza

La spec deja abierto si la tira de canto es un perfil en L de una pieza o dos
planchas atornilladas. **Esta tarea lo cierra con número y no con gusto**,
porque de ella cuelga que el cálculo de §4.1 siga valiendo: ese cálculo supone
sección monolítica.

**Files:**
- Modify: `case/clearance_budget.py` (función nueva + su autocomprobación)
- Modify: `docs/superpowers/specs/2026-08-26-case-esqueleto-aluminio-design.md` §8.1

**Interfaces:**
- Produces: `_seccion_L(t, b, c) -> (I, ymax, Q_junta)` y
  `paso_junta_L(p, t, b, c) -> (paso_resistencia, paso_friccion)` — mu y el
  par NO son argumentos: salen de `MU_ALU_SECO` y de `p["par_m3"]`, que ya
  existe.
  Las tareas 3 y 4 consumen `_seccion_L`.

- [ ] **Paso 1: escribir la autocomprobación primero, con el número a mano**

En `case/clearance_budget.py`, junto a las demás constantes de material:

```python
# Junta de la costilla con su tira de canto. El area de tension de un M3 es
# 5.03 mm2 (ISO 898-1). Tau admisible de un A2-70: Rm 700 MPa, y se toma
# 0.6*Rm con factor 2 -> 210 MPa. SUPUESTO DECLARADO: mu del aluminio contra
# aluminio en seco. La literatura da 0.3-0.6 y aqui va 0.2, deliberadamente
# por debajo del rango, porque de este numero cuelga la RIGIDEZ y no la
# resistencia -- ver paso_junta_L().
AS_M3, TAU_M3, MU_ALU_SECO = 5.03, 210.0, 0.2


def _seccion_L(t: float, b: float, c: float) -> tuple[float, float, float]:
    """Inercia, fibra mas alejada y momento estatico del ala separada.

    Seccion en L flexionando FUERA del plano de la costilla: el ala 1 es la
    plancha (ancho b en el plano, espesor t fuera) y el ala 2 es la tira de
    canto (ancho c fuera del plano, espesor t). Q es el momento estatico de
    la TIRA respecto al eje neutro, que es lo que la junta tiene que
    transmitir para que las dos alas trabajen como una."""
    A1, y1 = b * t, t / 2.0
    A2, y2 = c * t, t + c / 2.0
    A = A1 + A2
    yc = (A1 * y1 + A2 * y2) / A
    I = (b * t ** 3 / 12 + A1 * (y1 - yc) ** 2) + (t * c ** 3 / 12 + A2 * (y2 - yc) ** 2)
    return I, max(yc, (t + c) - yc), A2 * (y2 - yc)


def autocomprobacion_L() -> None:
    """A mano, para t=3, b=20, c=12:
         A1=60 y1=1.5 ; A2=36 y2=9 ; A=96 ; yc=414/96=4.3125
         I = (45 + 60*2.8125^2) + (432 + 36*4.6875^2) = 45+474.6+432+790.9
         Q = 36*4.6875 = 168.75"""
    I, ymax, Q = _seccion_L(3.0, 20.0, 12.0)
    assert abs(I - 1742.5) < 1.0, I
    assert abs(Q - 168.75) < 0.01, Q
    assert abs(ymax - 10.6875) < 0.001, ymax
```

- [ ] **Paso 2: correrla y verla en ROJO**

Run: `python -c "import case.clearance_budget"` — o directamente
`cd case && python -c "from clearance_budget import autocomprobacion_L; autocomprobacion_L()"`

Esperado antes de escribir `_seccion_L`: `ImportError` / `NameError`. **Si pasa
a la primera, la función ya existía y hay que averiguar por qué.**

- [ ] **Paso 3: escribir `paso_junta_L()` con los DOS criterios**

```python
def paso_junta_L(p: dict[str, float], t: float, b: float, c: float) -> tuple[float, float]:
    """Paso maximo de tornillo en la junta costilla-tira, por dos criterios.

    EL QUE MANDA ES EL SEGUNDO, y es la trampa de este calculo: quien
    dimensione la junta por RESISTENCIA pone tornillos cada 109 mm, y a ese
    paso la junta desliza en la holgura del agujero antes de que el tornillo
    llegue a trabajar. Con la junta deslizando las dos alas flexan por
    separado, que es exactamente la fila "sin tira" de la spec §4.1 -- la que
    no pasa a NINGUN espesor y a 3 mm ademas fluye. O sea que un error aqui
    no da una costilla un poco peor: da una costilla que no es una L.

      q = V*Q/I      flujo de cortante en la junta, N/mm
      V = P/2        cortante de una biempotrada con la carga al centro

    Criterio 1, RESISTENCIA: el M3 a cortante, AS_M3 * TAU_M3.
    Criterio 2, NO DESLIZAMIENTO: friccion mu*N, con N la precarga que da el
    par. N ~ T/(0.2*d) es la relacion par-precarga de manual, con 0.2 de
    factor de apriete para rosca SECA -- y seca es como va, que engrasarla
    mete un 30 % mas de precarga con el mismo par (ver par_m3)."""
    I, _, Q = _seccion_L(t, b, c)
    q = (p["carga_mano"] / 2.0) * Q / I
    paso_resistencia = AS_M3 * TAU_M3 / q
    precarga = p["par_m3"] * 1000.0 / (0.2 * 3.0)      # N*m -> N*mm, d=3
    paso_friccion = MU_ALU_SECO * precarga / q
    return paso_resistencia, paso_friccion
```

- [ ] **Paso 4: correr y anotar los dos números**

```bash
cd case && python -c "
from clearance_budget import leer_params, paso_junta_L, autocomprobacion_L
autocomprobacion_L()
p = leer_params()
r, f = paso_junta_L(p, 3.0, 20.0, 12.0)
print('resistencia: %.0f mm   friccion: %.0f mm' % (r, f))"
```

Esperado, con `par_m3` = 1.0 y `MU_ALU_SECO` = 0.2: resistencia ≈ **109 mm**,
fricción ≈ **34 mm**. El tramo más largo mide 308.94 mm, así que a 34 mm de
paso caben 10 tornillos.

- [ ] **Paso 5: cerrar §8.1 en la spec con el resultado**

Sustituir el bloque «no se elige aquí» de §8.1 por la decisión, con los dos
números, la elección de `MU_ALU_SECO` = 0.2 marcada `SUPUESTO DECLARADO`, y la
frase que impide el error: **el paso lo fija la fricción, no la resistencia.**

Si el paso de fricción sale **por debajo de 20 mm** con el μ elegido, la L
atornillada deja de ser razonable y hay que volver al perfil de sección
constante. Ese es el criterio de corte, escrito antes de mirar el resultado.

- [ ] **Paso 6: commit**

```bash
git add case/clearance_budget.py docs/superpowers/specs/2026-08-26-case-esqueleto-aluminio-design.md
git commit -m "La junta de la L no se dimensiona por resistencia sino por deslizamiento"
```

---

### Tarea 2: El Z-Rail y el hueco — REPLANTEADA el 2026-08-26 al ejecutarla

**Esta tarea estaba mal razonada y se descubrió al correrla.** Se deja escrita
en vez de borrarla, porque el error es instructivo y porque alguien va a
volver a tenerlo.

**Lo que decía:** que la holgura entre el Z-Rail y las caras internas es 0.00
mm y ninguna puerta lo mira, así que hacía falta `hol_riel` y una
`guarda_riel_cabe()`.

**Lo que pasó al escribirla:** salió en rojo, pero por otra puerta. Ya existía
una regla —`clearance_budget.py`, en el bloque de `exige()` de `main()`— que
pide `abs(ancho_util - largo_riel) < 0.01`, o sea la **igualdad exacta**. La
holgura cero no estaba olvidada: estaba decidida.

**Y la regla vieja tiene razón, en el mundo de hoy.** Su argumento escrito es
que los Z-Rails son de catálogo y desincronizar significa o rieles que no
llegan de costado a costado o rieles que hay que cortar por la punta donde se
fijan. Pero el fondo es más fuerte: **hoy `ancho_util` no es un hueco, es una
consecuencia.** Los costados se separan lo que midan las piezas que van de
cara a cara —largueros y rieles—, así que no existe un vano preexistente que
pueda quedarse corto. Pedir «holgura de montaje» ahí es una regla sin sujeto.

**El problema sí existe, pero en el diseño nuevo**, y por eso se muda a la
Tarea 3: la costilla es una pieza rígida cuyo ala interior es un plano, y las
transversales fijan la separación entre las dos. Ahí el riel pasa a tener que
caber en lo que quede, y la igualdad deja de ser cierta por construcción.

**Lo único que sobrevivió, y va commiteado aparte:** `ancho_total` era un
**literal escrito a mano** (544.32) con la fórmula solo en el comentario de al
lado, así que la igualdad con el riel salía por casualidad aritmética. Ahora se
deriva en los dos lados y `leer_params()` se niega a arrancar si alguien lo
devuelve a literal. El valor no cambia; lo que cambia es que ya no puede
desincronizarse en silencio.

**LECCIÓN PARA EL RESTO DEL PLAN:** antes de escribir una puerta nueva, buscar
si el `exige()` de `main()` ya dice algo del mismo tema. Las `guarda_*` son
fáciles de encontrar por nombre; las líneas sueltas de `exige()` no, y ahí es
donde vive media docena de reglas del case.

---

### Tarea 3: La costilla — parámetros, puerta y contorno 2D

**Files:**
- Modify: `case/cad/params.scad` (`t_costilla`, `ala_costilla`, `tira_canto`)
- Modify: `case/clearance_budget.py` (`guarda_costilla()`)
- Modify: `case/cad/sam17_case.scad` (`costilla_2d()`, dispatch `PART`)
- Modify: `case/cad/export.ps1`

**Interfaces:**
- Consumes: `_seccion_L()` de la Tarea 1.
- Produces: `costilla_2d()` en el `.scad`; `t_costilla`, `ala_costilla` y
  `tira_canto` como parámetros. Las tareas 5, 6, 7 y 9 los consumen.

- [ ] **Paso 1: escribir la puerta primero**

```python
def guarda_costilla(p: dict[str, float]) -> None:
    """La costilla aguanta que empujen el case de lado.

    ES LA PIEZA PORTANTE desde el 2026-08-26: el costado de acrilico paso a
    piel y no sostiene nada. El modo critico es fuera del plano de la costilla,
    que es su direccion floja; viga biempotrada porque las esquinas de un marco
    continuo son rigidas, con carga_mano al centro del tramo mas largo.

    LO QUE ESTA PUERTA EXISTE PARA IMPEDIR es que alguien quite la tira de
    canto por estetica. Sin tira, la seccion es una pletina plana y NO PASA A
    NINGUN ESPESOR -- ni la de 6 mm; y la de 3 ademas fluye, a 257 MPa contra
    un Rp0.2 de 130. Con tira de 12 la de 3 pasa con 2.4x. La tira no tapa un
    canto: es el ala que convierte la plancha en viga."""
    P = _vertices(p)
    n = len(P)
    tramo = max(math.hypot(P[(i + 1) % n][0] - P[i][0],
                           P[(i + 1) % n][1] - P[i][1]) for i in range(n))
    I, ymax, _ = _seccion_L(p["t_costilla"], p["ala_costilla"], p["tira_canto"])
    flecha = p["carga_mano"] * tramo ** 3 / (192 * E_ALUMINIO * I)
    sigma = (p["carga_mano"] * tramo / 8) * ymax / I
    assert flecha <= p["flecha_costado_max"], (
        f"la costilla cede {flecha:.3f} mm en su tramo de {tramo:.2f} mm con "
        f"{p['carga_mano']:.0f} N y el techo son {p['flecha_costado_max']:.2f}. "
        f"Si acabas de tocar tira_canto: sin ella NINGUN espesor pasa.")
    assert sigma <= RP02_ALUMINIO, (
        f"la costilla trabaja a {sigma:.1f} MPa y el Rp0.2 del aluminio de "
        f"chapa son {RP02_ALUMINIO:.0f}.")
    print(f"costilla: L de {p['t_costilla']:g} con ala {p['ala_costilla']:g} y "
          f"tira {p['tira_canto']:g}; tramo mayor {tramo:.2f} mm, cede "
          f"{flecha:.3f} mm y trabaja a {sigma:.1f} MPa")
```

- [ ] **Paso 2: correrla y verla en ROJO**

Run: `python case/clearance_budget.py`
Esperado: `KeyError: 't_costilla'` — los parámetros no existen todavía.

- [ ] **Paso 3: añadir los tres parámetros**

```openscad
// --- el esqueleto de aluminio (spec 2026-08-26) ---
// LA COSTILLA ES LA PIEZA PORTANTE. El costado de acrilico paso a piel el
// 2026-08-26 y ya no sostiene nada: no lleva un solo tornillo estructural.
//
// 3 mm y no mas, y el numero importa por una razon que no es la rigidez:
// el ala interior se mete en el hueco donde va el Z-Rail, asi que ancho_total
// crece 2*t_costilla. A 3 el case crece 6 mm; a 4, ocho. Y con la tira de
// canto puesta, 3 pasa con 2.4x de margen -- la rigidez la da la FORMA en L,
// no el espesor.
t_costilla  = 3;
// Ala que agarra la cara interior del costado. SUPUESTO DECLARADO: 20 es lo
// que medía el 2020 que este marco jubila. La cota definitiva sale de que le
// quepa el M4 del Z-Rail y de cuanto puede robarle al vaciado.
ala_costilla = 20;
// LA TIRA DE CANTO NO ES UN EMBELLECEDOR. Tapa el canto del acrilico, si,
// pero su trabajo es ser el ala que convierte la plancha en viga: sin ella la
// costilla es una pletina y no pasa a ningun espesor, ni a 6 mm. Lo vigila
// guarda_costilla(), y esta escrito ahi para que quien la quite se entere.
tira_canto  = 12;
```

- [ ] **Paso 4: hacer que el ancho pague la costilla — SIN esto la Tarea 2 se cae**

El ala interior se mete en el hueco del Z-Rail, así que `ancho_util` tiene que
restarla. Hoy `perfil()` hace `ancho_total - 2*t_cheek`, y `ancho_total` está
**escrito a mano** (544.32), no derivado: el comentario de al lado da la
fórmula pero el valor es literal, así que la igualdad con el riel salía por
casualidad aritmética.

En `clearance_budget.py`, `perfil()`:

```python
        # El ala de la costilla vive DENTRO de este hueco desde el 2026-08-26:
        # es lo que obliga al case a crecer 2*t_costilla. Ver spec §4.3.
        "ancho_util": (p["ancho_total"] - 2 * p["t_cheek"]
                       - 2 * p["t_costilla"]),
```

Y en `params.scad`, `ancho_total` deja de ser literal:

```openscad
// DERIVADO, y desde el 2026-08-26 no es opcional que lo sea: hasta hoy estuvo
// escrito a mano (544.32) y la igualdad con el riel salia por casualidad
// aritmetica. Ahora hay TRES cosas metidas en ese hueco -- el riel, su holgura
// de montaje y las dos alas de costilla -- y a mano se desincroniza al primer
// cambio.
ancho_total = largo_riel + hol_riel + 2*t_costilla + 2*t_cheek;
```

- [ ] **Paso 5: correr y verlas en VERDE las dos**

Run: `python case/clearance_budget.py`
Esperado: VERDE, con `ancho_total` = **550.62**, la línea de `guarda_riel_cabe`
todavía con sus 0.30 mm de holgura, y `costilla: L de 3 con ala 20 y tira 12;
tramo mayor 308.94 mm, cede 0.255 mm y trabaja a 47.4 MPa`.

**Si `guarda_riel_cabe()` se pone en rojo aquí, es que el ancho no creció y el
ala se comió la holgura** — que es exactamente para lo que se escribió esa
puerta en la Tarea 2.

- [ ] **Paso 6: probar que muerde por los dos lados**

Poner `tira_canto = 0` y comprobar que la puerta canta con el mensaje de la
pletina. Poner `t_costilla = 1` y comprobar que canta por tensión. Revertir.

- [ ] **Paso 7: dibujar `costilla_2d()`**

En `sam17_case.scad`, junto a `costado_2d()`. Es el contorno del perfil con el
centro vaciado, o sea un marco de cuadro:

```openscad
// La costilla: el contorno del costado con el centro vaciado. Es una pieza
// PLANA y por eso sale en DXF como todo lo demas -- la que no es plana es la
// tira de canto (ver spec §8.1).
module costilla_2d() {
    difference() {
        costado_2d_contorno();                 // el mismo perfil, sin taladros
        offset(delta = -ala_costilla) costado_2d_contorno();
        taladros_costilla();                   // Tarea 6 los llena
    }
}
```

**Nota para quien lo implemente:** `costado_2d()` hoy trae contorno **y**
taladros en la misma pieza. Hay que separar el contorno en un módulo propio
(`costado_2d_contorno()`) para que la costilla lo reuse sin heredar los
agujeros del acrílico. No es refactor gratuito: sin eso las dos piezas
divergen en cuanto una se toque.

- [ ] **Paso 8: registrar la pieza y exportar**

Añadir `else if (PART == "costilla_2d") costilla_2d();` al dispatch y
`"costilla_2d"` a `$piezas` en `export.ps1`.

Run: `powershell -File case/cad/export.ps1`
Esperado: VERDE, y `case/plans/costilla_2d.dxf` existe.

- [ ] **Paso 9: commit**

```bash
git add case/cad/ case/clearance_budget.py case/plans/
git commit -m "La costilla entra, y su puerta dice que la tira de canto es estructura"
```

---

### Tarea 4: Las tiras de canto

Depende de la decisión que cerró la Tarea 1. **Si salió L atornillada**, son
piezas planas y se dibujan como DXF. **Si salió perfil de sección constante**,
lo que se entrega es el DXF de la sección más un documento de largos, y esta
tarea escribe ese documento en vez de siete DXF.

**Files:**
- Modify: `case/cad/sam17_case.scad` (`tira_canto_2d(tramo)`)
- Modify: `case/cad/export.ps1`
- Modify: `case/clearance_budget.py` (paso de tornillo en `guarda_costilla()`)

**Interfaces:**
- Consumes: `paso_junta_L()` de la Tarea 1, `tira_canto` de la Tarea 3.

- [ ] **Paso 1: extender la puerta para que exija el paso de tornillo**

Añadir a `guarda_costilla()`, después de los dos asserts que ya tiene:

```python
    _, paso_max = paso_junta_L(p, p["t_costilla"], p["ala_costilla"], p["tira_canto"])
    assert p["paso_tira"] <= paso_max, (
        f"los tornillos de la tira van cada {p['paso_tira']:.0f} mm y la junta "
        f"deja de transmitir el cortante por encima de {paso_max:.0f}. Por "
        f"encima de ese paso la junta DESLIZA, las dos alas flexan por "
        f"separado y la costilla deja de ser una L -- que es la fila 'sin "
        f"tira', la que no pasa a ningun espesor. OJO: el criterio de "
        f"RESISTENCIA daria mucho mas paso y seria el numero equivocado.")
```

- [ ] **Paso 2: correrla y verla en ROJO**

Esperado: `KeyError: 'paso_tira'`.

- [ ] **Paso 3: añadir `paso_tira` a `params.scad`**

```openscad
// Paso de los M3 que cosen la tira de canto a la costilla. NO lo fija la
// resistencia del tornillo -- por resistencia cabrian cada 109 mm -- sino que
// la junta NO DESLICE: hasta que no desliza, las dos alas trabajan como una
// sola seccion, y en cuanto desliza la costilla deja de ser una L. Ver
// paso_junta_L(). 30 mm queda por debajo del limite de friccion con el mu
// conservador de 0.2 y el par de 1.0 N*m.
paso_tira = 30;
```

- [ ] **Paso 4: correr y verla en VERDE**

Esperado: VERDE, y una línea nueva con el paso y su límite.

- [ ] **Paso 5: probar que muerde**

`paso_tira = 120` y comprobar que canta citando el deslizamiento. Revertir.

- [ ] **Paso 6: dibujar las tiras y exportarlas**

Una por tramo del perfil (7), con sus taladros a `paso_tira`. El largo de cada
una sale de `pts_perfil()`, no se escribe a mano.

- [ ] **Paso 7: commit**

```bash
git add case/cad/ case/clearance_budget.py case/plans/
git commit -m "Las tiras de canto, cosidas al paso que impide que la junta deslice"
```

---

### Tarea 5: Las transversales del marco (añadir, sin quitar nada)

Tres barras nuevas: P[0] (arista que hoy está vacía), P[5] y P[6]. Los
largueros de hoy **siguen ahí** al terminar esta tarea — se van en la 7.

**Files:**
- Modify: `case/cad/sam17_case.scad` (`centros_transversal()`)
- Modify: `case/clearance_budget.py` (`_centros_transversal()`, `solapes()`)

- [ ] **Paso 1: escribir el canario del solape primero**

Las transversales nuevas caen cerca de rieles y largueros existentes. Antes de
dibujarlas, comprobar que `solapes()` las mira: añadirlas a `_cajas_solidas()`
y correr `canario_solapes()`.

- [ ] **Paso 2: correr y ver ROJO** — `KeyError` de la función que falta.

- [ ] **Paso 3: implementar `centros_transversal()`**

Cada centro sale de su vértice retirado hacia dentro por el radio de la barra,
en la **bisectriz** de las dos aristas que concurren. Nunca una cota a mano:

```python
IDX_TRANSVERSAL = [0, 5, 6]   # P[0] es nueva; P[5] y P[6] heredan remate y base


def _unitario(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _centros_transversal(p: dict[str, float], P: list[tuple[float, float]]
                         ) -> list[tuple[float, float]]:
    """Las tres barras propias del marco: las aristas que NO tienen riel.

    Las otras cuatro ya llevan Z-Rail (spec §5.1) -- el case tenia medio
    esqueleto perimetral montado sin estar dicho en ningun sitio. Cada centro
    se retira del vertice por el radio de la barra en la BISECTRIZ de las dos
    aristas que concurren, y no en x ni en y: retirarlo por un eje da una barra
    que asoma por una de las dos caras, y en P[0] las dos caras son vistas."""
    r, n, out = p["rail"] / 2, len(P), []
    for i in IDX_TRANSVERSAL:
        u = _unitario(P[i], P[(i - 1) % n])
        v = _unitario(P[i], P[(i + 1) % n])
        bx, by = u[0] + v[0], u[1] + v[1]
        m = math.hypot(bx, by)
        assert m > 1e-9, f"aristas colineales en P[{i}]: no hay bisectriz"
        out.append((P[i][0] + r * bx / m, P[i][1] + r * by / m))
    return out
```

Y su gemela en `sam17_case.scad` con la misma derivación. **Las dos tienen que
dar lo mismo**: `check_dxf.py` compara el DXF contra el modelo, y una
divergencia aquí sale como agujero fuera de sitio.

- [ ] **Paso 4: correr y ver VERDE.** `solapes()` sin fallos.

- [ ] **Paso 5: probar que muerde** — mover una transversal 20 mm dentro de un
riel a propósito y ver que `solapes()` canta. Revertir.

- [ ] **Paso 6: commit**

```bash
git commit -am "Las tres transversales del marco, y la de P[0] que no existia"
```

---

### Tarea 6: Los Z-Rails se mudan del acrílico a la costilla

**Files:**
- Modify: `case/cad/sam17_case.scad` (`taladros_costilla()`, `costado_2d()`)
- Modify: `case/check_dxf.py` (`railes_dentro_del_costado()`)

- [ ] **Paso 1: reescribir `railes_dentro_del_costado()` para que mida la costilla**

Hoy lee `costado_2d.dxf`. Pasa a leer `costilla_2d.dxf`, y **además** exige que
los 4 M4 de riel **ya no estén** en `costado_2d.dxf`.

- [ ] **Paso 2: correr `check_dxf.py` y verla en ROJO** — los M4 siguen en el
costado.

- [ ] **Paso 3: mover los taladros**: `taladros_costilla()` recibe los 4 M4,
`costado_2d()` los pierde.

- [ ] **Paso 4: exportar y ver VERDE** — `powershell -File case/cad/export.ps1`.

- [ ] **Paso 5: probar que muerde** — devolver un M4 al costado y ver que canta.

- [ ] **Paso 6: commit**

```bash
git add case/cad/ case/check_dxf.py case/plans/
git commit -m "Los cuatro Z-Rails dejan el acrilico y atornillan a la costilla"
```

---

### Tarea 7: Se van los cuatro largueros

Ahora sí: existen las transversales (5) y los rieles ya no cuelgan del acrílico
(6). **Esta es la tarea que Samuel pidió**, y llega la séptima porque antes el
modelo quedaba a medias.

**Files:**
- Modify: `case/cad/sam17_case.scad` (`centros_esqueleto()`)
- Modify: `case/clearance_budget.py` (`_centros_esqueleto()`, `NOMBRES_CE`,
  `alineacion()`, `apoyo()`)

- [ ] **Paso 1: escribir primero la puerta que exige que no queden largueros**

```python
    assert not _centros_esqueleto(p, P, cr), (
        "quedan largueros 2020 en el interior, y el 2026-08-26 se fueron los "
        "cuatro: base trasera y remate trasero se mudaron a las aristas P[6] "
        "y P[5], valle desaparecio porque P[3] ya tiene riel, y base delantera "
        "desaparecio con su trabajo heredado por la transversal NUEVA de P[0].")
```

- [ ] **Paso 2: correr y ver ROJO** — hay cuatro.

- [ ] **Paso 3: vaciar `centros_esqueleto()`** en el `.scad` y su gemela, y
re-apuntar `alineacion()` y `apoyo()` a `centros_transversal()`.

- [ ] **Paso 4: correr las dos puertas y verlas en VERDE.**

- [ ] **Paso 5: comprobar el BOM** — `openscad -D 'PART="bom"'` tiene que
listar **0 largueros 2020** y las transversales nuevas. Si sigue diciendo
cuatro, el eco quedó desincronizado del modelo, que es el fallo que ya pasó una
vez con las paticas.

- [ ] **Paso 6: commit**

```bash
git commit -am "Se van las cuatro barras del interior: el marco hace su trabajo"
```

---

### Tarea 8: La bandeja de base pasa a aluminio de 5

Sin `base delantera`, el suelo apoya en P[0] y P[6]: vano de 280.94 mm. En
acrílico de 8 cede 1.366 mm contra un techo de 0.60.

**Files:**
- Modify: `case/cad/params.scad` (`t_base` = 5, y deja de ser PMMA)
- Modify: `case/clearance_budget.py` (`guarda_piso()`)

- [ ] **Paso 1: extender `guarda_piso()` con el vano nuevo**

```python
    L = _centros_transversal(p, P)[-1][0] - p["rail"] / 2
    I = perfil(p)["ancho_util"] * p["t_base"] ** 3 / 12
    flecha = p["carga_mano"] * L ** 3 / (48 * E_ALUMINIO * I)
    assert flecha <= p["flecha_costado_max"], (
        f"el suelo cede {flecha:.3f} mm en su vano de {L:.2f} y el techo son "
        f"{p['flecha_costado_max']:.2f}. En acrilico de 8 daba 1.366 y por eso "
        f"paso a aluminio: solo cerraba en PMMA a partir de 12 mm, que "
        f"resucitaba una segunda linea de espesor.")
```

- [ ] **Paso 2: correr y ver ROJO** — con `t_base` = 8 de acrílico, E = 3000.

- [ ] **Paso 3: cambiar `t_base` a 5 y su material a aluminio**, con el
comentario que dice de dónde sale (spec §4.2) y que **la bandeja sale del
`lienzo_2d`**, que es de acrílico y solo de acrílico.

- [ ] **Paso 4: correr y ver VERDE** — flecha 0.243 mm.

- [ ] **Paso 5: probar que muerde** — `t_base = 2` y ver que canta.

- [ ] **Paso 6: sacar la bandeja del lienzo y del `planchas_acrilico()`**, igual
que se hizo con la tapa del valle el 2026-08-25.

- [ ] **Paso 7: commit**

```bash
git commit -am "El suelo pasa a aluminio de 5: en acrilico solo cerraba a 12"
```

---

### Tarea 9: El costado queda sin un solo tornillo estructural

**Files:**
- Modify: `case/check_dxf.py` (`guarda_costado()` → mide la costilla;
  `taladros_con_material()`)

- [ ] **Paso 1: reescribir `guarda_costado()`**

Hoy modela el costado como placa de PMMA empotrada en sus 4 M5 de larguero. Ya
no hay largueros ni carga. **No se borra**: se re-apunta a la costilla, y su
docstring explica por qué cambió de sujeto — un `git blame` sobre una puerta
borrada no cuenta esa historia.

- [ ] **Paso 2: correr y ver ROJO.**

- [ ] **Paso 3: implementar**, midiendo sobre `costilla_2d.dxf`.

- [ ] **Paso 4: correr y ver VERDE.**

- [ ] **Paso 5: comprobar que `costado_2d.dxf` no tiene taladros estructurales**
— solo los del propio marco.

- [ ] **Paso 6: commit**

```bash
git commit -am "guarda_costado() cambia de sujeto: mide la costilla, que es quien carga"
```

---

### Tarea 10: Las tres puertas que quedaron apuntando al sitio equivocado

El cambio de material deja tres puertas midiendo cosas que ya no son lo que
eran. Ninguna falla en rojo por sí sola — **siguen en verde midiendo mal**, que
es peor, y por eso van en tarea propia y no de rebote en otra.

**Files:**
- Modify: `case/clearance_budget.py` (`guarda_chaflan()`, `guarda_apriete()`,
  `guarda_transversal_riel()` nueva, `guarda_tapa()`)

- [ ] **Paso 1: `guarda_transversal_riel()` — el Z-Rail no es una viga**

La spec §5.1 apoya tres de las siete aristas en Z-Rails usados como
transversal, y el README ya advierte que **su cara es pared de 1.2 mm**: es la
razón por la que la tapa de remate estuvo pegada hasta el 2026-08-21.

```python
# Pared del Z-Rail de Tiptop. NO es una viga: es un extruido de pared fina, y
# esta cifra es la razon por la que la tapa de remate estuvo PEGADA hasta el
# 2026-08-21 -- un M3 en esa cara atraviesa pared.
PARED_ZRAIL = 1.2


def guarda_transversal_riel(p: dict[str, float]) -> None:
    """A un Z-Rail usado de transversal no se le pide mas de lo que da.

    Desde el 2026-08-26 el marco se apoya en que cuatro de las siete aristas ya
    llevan riel (spec §5.1), y eso es cierto como GEOMETRIA. Como ESTRUCTURA
    hay que acotarlo: el riel trabaja bien a traccion entre costillas, y mal a
    todo lo demas, porque su pared son 1.2 mm.

    Esta puerta existe para que el ahorro de §5.1 no se lea como que un riel
    sustituye a un larguero en cualquier direccion."""
    area = PARED_ZRAIL * p["rail_er_alto"]           # dos paredes en traccion
    sigma = p["carga_mano"] / (2 * area)
    assert sigma <= RP02_ALUMINIO, (
        f"al Z-Rail se le piden {sigma:.1f} MPa de traccion entre costillas y "
        f"su pared de {PARED_ZRAIL} mm da para {RP02_ALUMINIO:.0f}. Si esta "
        f"arista necesita mas, lleva transversal propia y no riel.")
    print(f"transversal: el Z-Rail trabaja a {sigma:.1f} MPa sobre "
          f"{2*area:.1f} mm2 de pared (Rp0.2 {RP02_ALUMINIO:.0f})")
```

- [ ] **Paso 2: correrla y verla en ROJO** — `NameError` / `KeyError`.
Registrarla en `main()`, implementar, y verla en VERDE.

- [ ] **Paso 3: probar que muerde** — bajar `PARED_ZRAIL` a 0.05 y ver que canta.
Revertir.

- [ ] **Paso 4: `guarda_chaflan()` — el perímetro tapado sale del cómputo**

Hoy toma `t_min = min(t_base, t_cheek, t_piel)` y de ahí saca el techo del
chaflán. Con la tira de canto cubriendo el perímetro del costado, **ese canto
deja de estar a la vista** y el chaflán deja de aplicarle. Es exactamente el
mismo movimiento que ya se hizo con la tapa del valle el 2026-08-25, y el
docstring de la puerta lo explica: dejar dentro una pieza a la que la regla no
aplica «clava el techo por una pieza a la que la regla no le aplica, que es el
vicio de la puerta que grita en falso».

`t_base` además ya no es PMMA desde la Tarea 8, así que también sale.

- [ ] **Paso 5: `guarda_apriete()` — decidir el par contra aluminio**

**Cuidado, que la arandela d16 hace DOS trabajos y es fácil contar solo uno.**
Uno es no aplastar el acrílico, que fluye a 10 MPa; ese desaparece en la
bandeja y en el valle, ya de aluminio. El otro es **subir el par utilizable de
0.33 a 1.15 N·m**, porque por debajo de 1 N·m no hay llave dinamométrica de
1/4" que lo dé — y ese sigue vivo contra aluminio.

Así que la d16 **no sobra**: lo que hay que hacer es que la puerta distinga los
M3 que aprietan contra PMMA (remate, trasera) de los que aprietan contra
aluminio (bandeja, valle), y que cada familia tenga su límite. Hoy los mete a
todos en el mismo saco.

- [ ] **Paso 6: `guarda_tapa()` — re-verificar las 180°**

La decisión 8 de la spec deja los ejes escondidos dentro del Z-Rail, así que el
radio de giro **no se mueve**. Pero el M4 ahora atraviesa la costilla en vez
del acrílico, y `ancho_total` creció. Correr la puerta y **confirmar que sigue
dando 180.0° en las dos filas**. Si bajó, algo del marco entró en el barrido y
es un hallazgo, no un ajuste.

- [ ] **Paso 7: commit**

```bash
git add case/clearance_budget.py
git commit -m "Tres puertas seguian verdes midiendo lo que ya no era"
```

---

### Tarea 11: Los papeles

**Files:**
- Modify: `case/PLIEGO.md`, `case/RFQ.md`, `case/README.md`
- Modify: `docs/superpowers/specs/2026-08-15-case-design.md` (rev. 21)

- [ ] **Paso 1: `PLIEGO.md`** — el cuarto proveedor, y **lo que SALE del pliego
de acrílico**: el costado pierde «canto visible completo, diamantado» en el
perímetro que la tira tapa. El recocido se queda, que es por tensión interna.

- [ ] **Paso 2: `RFQ.md`** — las preguntas eliminatorias del taller de aluminio:
aleación (Rp0.2 ≥ 130), y **rectitud de las tiras**, que son barras y la más
larga mide 308.94 mm.

- [ ] **Paso 3: `README.md`** — BOM recontado **por el eco del modelo**, no a
mano; orden de ensamblaje nuevo (el marco va primero); y el párrafo de por qué
el acrílico dejó de cargar.

- [ ] **Paso 4: spec del case, rev. 21** — §2 (Estructura), §5, §6, §9, §10 y
§11. En §11, bajar el **#98 de bloqueante a cosmético** con su razón: el
espesor real ya no mueve ninguna cota funcional.

- [ ] **Paso 5: verificar que las cotas del pliego coinciden con el modelo** —
`openscad -D 'PART="bom"'` contra lo escrito. Es el paso que ya cazó una vez
que el eco pedía «patica metálica torneada» después de pasar a goma.

- [ ] **Paso 6: commit**

```bash
git commit -am "Los papeles alcanzan al marco: pliego, RFQ, README y rev. 21"
```

---

## Lo que este plan NO hace

- **El zócalo de madera** (spec §9). Plan aparte.
- **Cerrar el racking, #203.** Este diseño no lo cierra con número y la spec lo
  dice. Se cierra cargando el prototipo.
- **Medir el peso del chasis del PSU**, que es lo que convertiría los 200 N
  heredados en el modo de carga real del suelo (spec §4.2). Va como issue.
- **El render.** `render.py` importa los assemblies; cuando la costilla entre en
  `assembly_aluminio()` el render la coge sola. Si no, es un hallazgo.
