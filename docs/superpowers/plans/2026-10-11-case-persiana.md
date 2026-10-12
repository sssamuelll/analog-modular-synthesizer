# La persiana en el case — plan de implementación

> **Para quien lo ejecute:** SUB-SKILL OBLIGATORIA: superpowers:subagent-driven-development (recomendada) o superpowers:executing-plans, tarea por tarea. Los pasos usan casillas (`- [ ]`).

**Objetivo:** que el modelo del case, sus puertas, sus DXF de taller, sus renders y su papel de taller sean los de la persiana firmada el 11-10, y que la piel orgánica y la mejilla de acrílico desaparezcan del repo sin dejar puertas mirando piezas muertas.

**Arquitectura:** el `.scad` sigue siendo la fuente de la geometría y los DXF salen de él por `export.ps1`; `check_dxf.py` los relee. Lo que el `.scad` no sabe calcular bien (el ritmo de las varillas y dónde caben los tacos) lo calcula `case/cad/persiana.py` y lo escribe en un fichero generado, `case/cad/persiana_generada.scad`, que una puerta compara con lo que el generador produciría. Las cotas de la persiana viven en `params.scad`, como todas.

**Tecnologías:** OpenSCAD 2021.01 (`C:\Program Files\OpenSCAD\openscad.exe`), Python 3 con `ezdxf`, `shapely` y `numpy`, Blender 5.0 para los renders, PowerShell para `export.ps1`.

**Papel:** `docs/superpowers/specs/2026-10-11-case-persiana-design.md` (firmado el 11-10; D-S4, la tabla, en espera). Se lee junto con este plan.

**Fuera de este plan, y por qué:** el aire con el plano neutro dentro de `clearance_budget._tiro()`, el cambio de la potencia de la v4 a la v5 y la cadena del #289 (§5 del papel) van en **un segundo plan**, `2026-10-11-aire-plano-neutro.md`, que se escribe cuando este esté mergeado: su gemela de la persiana es la que este plan deja hecha. Mientras tanto `guarda_aire()` sigue publicando su HUECO, como hoy. **La tabla no se toca** (D-S4 en espera: Samuel piensa quitarla).

## Restricciones globales

- Rama `docs/case-persiana` en el worktree `.claude/worktrees/persiana`; la Tarea 0 la renombra a `feat/case-persiana`.
- Los commits **no llevan líneas de atribución** (instrucción del 11-10).
- Varilla `varilla_persiana = 2.0` en `t_persiana = 6`: 3:1, `ESBELTEZ_MAX_PARED` de `clearance_budget.py`.
- Paso medio `paso_persiana = 7.0`, ola `ola_persiana = 0.16`, azar `azar_persiana = 0.06` **determinista** (sin `numpy.random`: su flujo puede cambiar entre versiones y la puerta de sincronía se pondría roja sin que nadie tocara el diseño).
- Borde macizo `borde_persiana = 4`; ranuras con radio `fresa_d / 2` (= 1,5) en sus puntas.
- Dos atados a `alto_total / 3` y `2 · alto_total / 3`, de `alto_atado = 4`; en ellos y en la banda sobre el anillo la ranura es ciega a `hondo_ciego_persiana = 4` desde fuera (queda un puente de 2).
- Lo que atraviesa es la ranura dentro de `ventana_anillo_2d()` menos los atados.
- Persiana a `suelo_persiana = 0.3` sobre la tabla.
- Tacos: diez, a `u_taco = 6.5` de la silueta; Ø `d_taco = 8`, alto `alto_taco = 3.5`; bolsillo Ø `d_bolsillo_taco = 9` (el localizador a `d_taco`, H7; la colisa `colisa_taco = 10` en x), hondo `hondo_bolsillo_taco = 3.8`; imanes Ø `d_iman = 6`, de `alto_iman_anillo = 3` y `alto_iman_taco = 2`, y `alto_iman_fino = 1` en el tramo de atrás.
- Pared mínima entre vaciados del anillo: `PARED_MIN_ANILLO = 3.0` (`clearance_budget.py`). Al menos 10 mm en el plano entre un bolsillo y cualquier rosca M4 o M5.
- Rendijas (D-S9): `retiro_placa_inf = 11.9`, `retorno_meseta = 9`; el labio deja `LABIO_AIRE_MIN = 1.0` al canto del panel y pisa al menos 0,5 de la cara del riel.
- Todo el aluminio visto en 6082-T6/T651, anodizado negro AA15–AA20 sellado, arista rota ≥ 0,2 (PLIEGO, Tarea 8). Los Z-Rails se quedan plateados.
- Las puertas del repo son `python hardware/tools/gates.py` (recoge `case/**/check_*.py` y `case/**/*_budget.py`), `ruff check .` y, para los DXF, `case/cad/export.ps1` seguido de `python case/check_dxf.py`. La verificación final es `sh .githooks/pre-push < /dev/null`.

## Lo que más puede morder sin que un test lo vea

1. **Las dos persianas son piezas espejadas.** Si el taller corta dos iguales, una no entra: sus tacos no caen en los bolsillos de su anillo. La Tarea 4 compara los tacos de `persiana_dorso_2d.dxf` con los bolsillos de `costilla_bolsillos_2d.dxf` **en el plano del perfil**, y el PLIEGO dice «izquierda y derecha, dos programas» (Tarea 8).
2. **Un `numpy` nuevo mueve las varillas.** Por eso el ritmo es determinista (Tarea 2), y la puerta de sincronía lo compara.
3. **Un taco que toca fondo antes de que la persiana asiente.** Si `alto_taco + 0,3 > hondo_bolsillo_taco`, la persiana queda colgando de sus tacos y no apoya en el anillo. Lo asevera `guarda_tacos_persiana()` (Tarea 4).
4. **Un panel que ya no sale de frente.** El labio de arriba deja exactamente 1,0 contra `LABIO_AIRE_MIN = 1.0`; un redondeo puede tumbarlo. La puerta compara con 1e-9 de tolerancia y su canario prueba los dos lados (Tarea 1).
5. **Un DXF que ninguna puerta mira.** Los cuatro DXF nuevos entran en `_sobres()`; si no, `todo_dxf_tiene_quien_lo_mire()` los marca huérfanos (Tareas 3 y 4).

---

### Tarea 0: Rama y punto de partida

**Ficheros:** ninguno.

- [ ] **Paso 1: renombrar la rama y comprobar que la base está verde**

```bash
cd D:/Desktop/projects/sam17/.claude/worktrees/persiana
git branch -m docs/case-persiana feat/case-persiana
git fetch -q origin && git log --oneline -1 origin/main
python hardware/tools/gates.py 2>&1 | tail -5
```

Esperado: `GATES EN VERDE` o los HUECOS de hoy (el del #289 entre ellos). Si `origin/main` avanzó desde `820a2eb`, rebasar antes de seguir (`git rebase origin/main`) y volver a correr.

---

### Tarea 1: Las rendijas de la ficha 6 se cierran (D-S9)

La nariz y el techo bajan hasta el riel. Las dos reglas del barrido (`guarda_nariz()` aserto 3 y `guarda_retorno_meseta()`) se sustituyen por la del labio, que hoy es gemela de la piel (`_labio_ventana`) y pasa a ser de las chapas.

**Ficheros:**
- Modificar: `case/cad/params.scad:424-432` (`retiro_placa_inf`) y `:1409-1416` (`retorno_meseta`)
- Modificar: `case/clearance_budget.py:580-637` (el labio), `:5640-5660` (`guarda_retorno_meseta`), `:5715-5770` (`guarda_nariz`), y las llamadas en `main()` (`guarda_labio_ventana`, `canario_labio_ventana`)
- Regenerar: `case/plans/nariz_2d.dxf`, `miembro_alto_2d.dxf`, `marco_ventana_2d.dxf` (por `export.ps1`)

**Interfaces:**
- Produce: `_labio_chapas(p) -> dict[str, tuple[float, float, float]]` con `"abajo"` y `"arriba"`, cada uno `(s_labio, s_riel, s_panel)` en mm a lo largo de su cara; `guarda_labio_chapas(p) -> None`; `canario_labio_chapas(p) -> None`.

- [ ] **Paso 1: escribir la regla nueva y su canario (todavía con los parámetros de hoy, para verla fallar)**

En `case/clearance_budget.py`, sustituir el bloque `LABIO_AIRE_MIN` … `canario_labio_ventana` (líneas 580-637) por:

```python
# El aire entre el labio de la chapa y el canto del panel (ficha 6, persiana
# del 11-10). Por abajo lo pone la nariz; por arriba, el retorno del techo.
# Cada labio tiene que hacer dos cosas a la vez: dejar que el panel salga de
# frente sin rozarlo (LABIO_AIRE_MIN al canto del panel) y pasar del canto del
# riel (LABIO_SOBRE_RIEL_MIN sobre su cara), porque si se queda corto, detras
# del ala del riel vuelve a verse el interior. Las dos reglas del barrido que
# dejaban la rendija abierta (1 mm de aire BAJO el riel, holgura_rail SOBRE el
# riel) eran de cuando las filas giraban; desde la tanda B los paneles son
# fijos (guarda_paneles_fijos()).
LABIO_AIRE_MIN = 1.0
LABIO_SOBRE_RIEL_MIN = 0.5


def _labio_chapas(p: dict[str, float]) -> dict[str, tuple[float, float, float]]:
    """(donde acaba el labio, donde empieza la cara del riel, donde empieza el
    panel), en mm a lo largo de cada cara y medidos desde el canto del panel
    hacia fuera. Abajo, la nariz sube por la cara de abajo hasta s_top (GEMELA
    de nariz_s_top()); arriba, el retorno del techo baja por la cara de arriba
    hasta L - retorno_meseta (GEMELA de miembro_alto())."""
    s_nariz = _nariz(p)["s_top"]
    s_riel_inf = p["inset_inf_frente"] - p["rail_er_alto"] / 2
    s_panel_inf = p["inset_inf_frente"] - p["inset_er"]
    L = p["alto_cara_sup"]
    s_ret = L - p["retorno_meseta"]
    s_riel_sup = L - p["inset_sup_remate"] + p["rail_er_alto"] / 2
    s_panel_sup = p["inset_sup_valle"] - p["inset_er"] + p["alto_panel_sup"]
    # Abajo se mide desde P1 subiendo por la cara; arriba, desde el pico (P4)
    # bajando. Asi, en los dos, riel < labio < panel cuando la rendija esta
    # cerrada y el panel sale de frente.
    return {"abajo": (s_nariz, s_riel_inf, s_panel_inf),
            "arriba": (L - s_ret, L - s_riel_sup, L - s_panel_sup)}


def _guarda_labio(labios: dict[str, tuple[float, float, float]]) -> None:
    for donde, (labio, riel, panel) in labios.items():
        aire = panel - labio
        sobre = labio - riel
        assert aire >= LABIO_AIRE_MIN - 1e-9, (
            f"el labio de la chapa queda a {aire:.2f} mm del panel por {donde}: "
            f"con menos de {LABIO_AIRE_MIN:g} el panel no sale de frente sin "
            f"rozarla")
        assert sobre >= LABIO_SOBRE_RIEL_MIN - 1e-9, (
            f"el labio de la chapa pisa {sobre:.2f} mm de la cara del riel por "
            f"{donde} y se piden {LABIO_SOBRE_RIEL_MIN:g}: detras vuelve a verse "
            f"el interior (la rendija de la ficha 6)")


def guarda_labio_chapas(p: dict[str, float]) -> None:
    """La nariz y el techo acaban sobre el ala del riel, ni dentro de la huella
    del panel ni antes del canto del riel (ficha 6; persiana §7.3)."""
    labios = _labio_chapas(p)
    _guarda_labio(labios)
    print("labio de las chapas (ficha 6): " + ", ".join(
        f"{d} a {panel - labio:.2f} del panel y {labio - riel:.2f} sobre el riel"
        for d, (labio, riel, panel) in labios.items()))


def canario_labio_chapas(p: dict[str, float]) -> None:
    """Los dos lados tienen que saltar: un labio que pisa la huella del panel y
    uno que se queda antes del canto del riel."""
    for cambio, aviso in (({"retorno_meseta": p["retorno_meseta"] + 0.5}, "no sale de frente"),
                          ({"retiro_placa_inf": p["retiro_placa_inf"] - 2.0}, "vuelve a verse")):
        try:
            _guarda_labio(_labio_chapas({**p, **cambio}))
        except AssertionError as e:
            assert aviso in str(e), f"canario del labio salto por '{e}'"
            continue
        raise AssertionError(f"canario del labio NO salto ({aviso})")
```

En `main()`, cambiar `guarda_labio_ventana(p)` por `guarda_labio_chapas(p)` y `canario_labio_ventana(p)` por `canario_labio_chapas(p)`.

> Ojo con la geometría de arriba: el retorno baja **desde** el pico, así que su «borde» está en `L - retorno_meseta` y el riel y el panel quedan **por debajo** de él en s. Medir desde el pico (`L - s`) deja las tres en el mismo sentido que abajo. Comprobar con los números de Elke: con `retorno_meseta = 9`, labio 9,0, riel 8,0 (`L - 147`), panel 10,0 (`L - 145`): aire 1,0 y 1,0 sobre el riel.

- [ ] **Paso 2: correrla con los parámetros de hoy y verla fallar**

Run: `python case/clearance_budget.py 2>&1 | grep -n "labio\|AssertionError" | head`
Esperado: `AssertionError: el labio de la chapa pisa -1.92 mm de la cara del riel por abajo` (la rendija de hoy). Si sale verde, la gemela está mal.

- [ ] **Paso 3: los dos parámetros, con su porqué**

En `case/cad/params.scad`, cambiar `retiro_placa_inf = 9;` por:

```scad
// 11.9 desde el 2026-10-11 (persiana, D-S9): la nariz sube hasta pisar 0.98 de
// la cara del riel del frente y deja 1.02 al canto del panel, que cierra la
// rendija de la ficha 6. Era 9: la regla del barrido pedia 1 mm de aire BAJO
// el riel, y desde la tanda B los paneles son fijos. Lo vigila
// guarda_labio_chapas(); la pata del marco que arranca aqui la sigue
// guarda_anclajes().
retiro_placa_inf   = 11.9;
```

y `retorno_meseta  = 4;` por:

```scad
// 9 desde el 2026-10-11 (persiana, D-S9): el retorno del techo baja hasta
// pisar 1.0 de la cara del riel del remate y deja 1.0 al canto del panel. Era
// 4 por holgura_rail sobre el riel, una regla del barrido de cuando las filas
// giraban. Lo vigila guarda_labio_chapas().
retorno_meseta  = 9;
```

- [ ] **Paso 4: quitar las dos reglas del barrido**

En `guarda_nariz()` (`clearance_budget.py:5715-5770`), quitar el aserto 3 (`aire >= 1.0`) y el punto 3 del docstring, y cambiar la línea del `print` de la sombra por `print(f"  la rendija la cierra el labio: ver guarda_labio_chapas()")`. En `guarda_retorno_meseta()` (`:5640-5660`), quitar el aserto de `margen >= p["holgura_rail"]` y su `print` de margen; dejar el de la línea de sombra.

- [ ] **Paso 5: correr el budget entero**

Run: `python case/clearance_budget.py > /tmp/budget.log 2>&1; echo $?; grep -n "labio\|ROJO\|AssertionError" /tmp/budget.log | head`
Esperado: código 0 o 2 (el HUECO del #289 sigue), `labio de las chapas (ficha 6): abajo a 1.02 del panel y 0.98 sobre el riel, arriba a 1.00 del panel y 1.00 sobre el riel`, y ningún `AssertionError`. Si cae `guarda_anclajes()`, `guarda_marco_ventana()` o `guarda_tramo_trasero()`, parar: Elke las corrió en verde con estos dos valores.

- [ ] **Paso 6: regenerar los DXF y releerlos**

Run (PowerShell): `powershell -NoProfile -File case/cad/export.ps1; echo $LASTEXITCODE`
Esperado: `2` (exporta con el HUECO del #289) y `check_dxf: VERDE`. Cambian `nariz_2d.dxf`, `miembro_alto_2d.dxf` y `marco_ventana_2d.dxf`.

- [ ] **Paso 7: commit**

```bash
git add case/cad/params.scad case/clearance_budget.py case/plans/
git commit -m "Las rendijas de la ficha 6 se cierran: la nariz y el techo bajan hasta el riel, y las reglas del barrido dejan sitio a la del labio"
```

---

### Tarea 2: El generador de la persiana

`case/cad/persiana.py` ya existe como propuesta. Pasa a leer sus cotas de `params.scad`, el contorno de `costilla_2d.dxf` (la silueta real del anillo, que es la suya), a usar un ritmo determinista, a calcular dónde caben los tacos y a escribir `persiana_generada.scad`.

**Ficheros:**
- Modificar: `case/cad/params.scad` (bloque nuevo al final de la sección del anillo)
- Modificar: `case/cad/persiana.py`
- Crear: `case/cad/persiana_generada.scad` (lo escribe el generador)

**Interfaces:**
- Consume: `cb.leer_params()`, `cb._vertices(p)`, `cb._centros_rosca_ciega(p)` → `[(nombre, (x, y), d)]`, `cb._m5_tabla_x(p)` → `[x]`, `cb.CD_TIRO`, `cb.CD_TIRO_PESIMISTA`, `cb._rejilla_entrada`, `cb._rendija`, `cb._ondas_trasera`, `cb._tiro`.
- Produce (los usan las Tareas 3, 4, 7 y el plan del aire):
  - `perfil_real() -> shapely.geometry.Polygon`
  - `varillas_x(p) -> list[float]`
  - `tacos(p) -> list[tuple[float, float, str]]` con tipo en `{"loc", "colisa", "ret", "fino"}`
  - `generado(p) -> str`
  - `geometria(p) -> dict` con claves `contorno, macizo, fondo, ranuras, pasante, abierto, varillas, alto`
  - `franjas`, `plano_neutro`, `salto`, `huecos_case` (sin cambios)

- [ ] **Paso 1: las cotas en `params.scad`**

Añadir después de `chaflan_anillo` (línea ~309):

```scad
// --- LA PERSIANA (2026-10-11) ----------------------------------------------
// docs/superpowers/specs/2026-10-11-case-persiana-design.md. La placa de cada
// costado, por fuera del anillo y tapandolo. El ritmo de las varillas y los
// tacos los calcula case/cad/persiana.py y los escribe en
// persiana_generada.scad; aqui van las cotas que los gobiernan.
t_persiana           = 6;     // el fondo de la varilla: lo que la sostiene de frente
borde_persiana       = 4;     // el borde macizo que sigue la silueta
varilla_persiana     = 2.0;   // 6 / 2.0 = 3:1, ESBELTEZ_MAX_PARED de clearance_budget
paso_persiana        = 7.0;   // paso medio; con 6.2 el pesimista daba 20.1 K
ola_persiana         = 0.16;  // la ola lenta del paso (+-16 %)
azar_persiana        = 0.06;  // y un azar determinista (+-6 %): sin numpy.random
hondo_ciego_persiana = 4;     // la ranura ciega (banda y atados) deja un puente de 2
alto_atado           = 4;     // los dos atados, a 1/3 y 2/3 del alto
suelo_persiana       = 0.3;   // sobre la tabla
// los tacos y sus bolsillos (Elke Brandt, junta del 11-10)
u_taco               = 6.5;   // centro, desde la silueta: deja 3.0 al rebaje (u = 14)
d_taco               = 8;     // y localizador a 8 H7
alto_taco            = 3.5;
d_bolsillo_taco      = 9;     // los de retencion, con holgura
hondo_bolsillo_taco  = 3.8;   // 0.3 de aire bajo el taco: la persiana apoya en el anillo
colisa_taco          = 10;    // el segundo localizador, alargado en x
d_iman               = 6;     // neodimio N42
alto_iman_anillo     = 3;
alto_iman_taco       = 2;
alto_iman_fino       = 1;     // en el tramo de atras: detras esta el bolsillo de la trasera
```

- [ ] **Paso 2: escribir el canario del ritmo determinista (falla con el de numpy)**

Añadir al final de `case/cad/persiana.py`, antes de `if __name__ == "__main__":`:

```python
def autocomprobacion_ritmo(p) -> None:
    """El ritmo no depende de numpy: dos llamadas dan lo mismo, ninguna ranura
    queda mas estrecha que la fresa y el paso no se sale de la ola."""
    a, b = varillas_x(p), varillas_x(p)
    assert a == b, "el ritmo de las varillas no es determinista"
    pasos = [y - x for x, y in zip(a, a[1:])]
    lim = p["paso_persiana"] * (1 + p["ola_persiana"] + p["azar_persiana"])
    assert max(pasos) <= lim + 1e-9, f"un paso de {max(pasos):.2f} se sale de la ola ({lim:.2f})"
    ranura = min(pasos) - p["varilla_persiana"]
    assert ranura >= p["fresa_d"] - 1e-9, (
        f"la ranura mas estrecha mide {ranura:.2f} y la fresa {p['fresa_d']:g}")
```

Run: `python -c "import sys; sys.path[:0]=['case/cad','case']; import persiana as ps, clearance_budget as cb; ps.autocomprobacion_ritmo(cb.leer_params())"`
Esperado: `AttributeError: module 'persiana' has no attribute 'varillas_x'`.

- [ ] **Paso 3: reescribir `persiana.py`**

Sustituir las constantes de módulo por lecturas de `p`, y la geometría por esto (el resto del fichero —`franjas`, `plano_neutro`, `salto`, `huecos_case`, `autocomprobacion`, `capas_json`— se queda):

```python
PHI = 0.6180339887498949            # el azar determinista: k * phi modulo 1
DXF_ANILLO = os.path.join(AQUI, "..", "plans", "costilla_2d.dxf")
GENERADO = os.path.join(AQUI, "persiana_generada.scad")
MARCO, MARCO_ATRAS = "marco_fondo", "marco_fondo_trasera"   # las claves de params


def perfil_real():
    """La silueta del anillo tal como sale al taller: el contorno exterior de
    costilla_2d.dxf (perfil_lateral(), con sus entasis y sus radios). Es la de
    la persiana: su canto cae sobre el del anillo."""
    import ezdxf
    from shapely.geometry import LineString
    from shapely.ops import polygonize
    doc = ezdxf.readfile(DXF_ANILLO)
    lineas = [LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
              for e in doc.modelspace() if e.dxftype() == "LINE"]
    piezas = sorted(polygonize(lineas), key=lambda q: q.area, reverse=True)
    return Polygon(piezas[0].exterior)          # la silueta: la ventana es un agujero


def contorno(p):
    perfil = perfil_real()
    return perfil, perfil.intersection(box(-50, p["suelo_persiana"], 400, 400))


def varillas_x(p) -> list[float]:
    """Los centros de las varillas, de delante atras: paso medio con una ola
    lenta y un azar determinista (k * phi modulo 1). Sin numpy.random: su
    flujo puede cambiar entre versiones."""
    fondo_x = cb._vertices(p)[5][0]
    out, x, k = [], 4.0, 0
    while x < fondo_x + 10:
        out.append(round(x, 3))
        j = 2 * ((k * PHI) % 1.0) - 1
        x += p["paso_persiana"] * (1 + p["ola_persiana"] * math.sin(x / 23.0) + p["azar_persiana"] * j)
        k += 1
    return out


def tacos(p) -> list[tuple[float, float, str]]:
    """Diez tacos a u_taco de la silueta, repartidos por el contorno, a 10 mm o
    mas de toda rosca M4 del dorso y de todo M5 de la tabla. Dos localizan en
    el suelo (el de delante redondo, el de atras en colisa); los del tramo de
    atras llevan iman fino (detras esta el bolsillo de la trasera); el resto
    retiene. Es el reparto de Elke Brandt (junta del 11-10)."""
    perfil = perfil_real()
    linea = perfil.buffer(-p["u_taco"], join_style="mitre").exterior
    L = linea.length
    m4 = [c for _n, c, _d in cb._centros_rosca_ciega(p)]
    m5 = cb._m5_tabla_x(p)
    fondo_x = cb._vertices(p)[5][0]
    validos = []
    for i in range(int(L / 2.0)):
        q = linea.interpolate(i * 2.0)
        lejos_m4 = all(math.dist((q.x, q.y), c) >= 10.0 for c in m4)
        lejos_m5 = all(abs(q.x - x) >= 10.0 for x in m5) or q.y > p["u_taco"] + 1.0
        if lejos_m4 and lejos_m5:
            validos.append((i * 2.0, round(q.x, 3), round(q.y, 3)))
    suelo = [v for v in validos if v[2] <= p["u_taco"] + 1e-6]
    loc = min(suelo, key=lambda v: abs(v[1] - 25.0))
    elegidos = []
    for k in range(10):
        meta = (loc[0] + k * L / 10) % L
        elegidos.append(min(validos, key=lambda v: min(abs(v[0] - meta), L - abs(v[0] - meta))))
    assert len(set(elegidos)) == 10, "dos tacos cayeron en el mismo punto"
    en_suelo = sorted((v for v in elegidos if v[2] <= p["u_taco"] + 1e-6), key=lambda v: v[1])
    assert len(en_suelo) >= 2 and en_suelo[-1][1] - en_suelo[0][1] >= 200.0, (
        "los dos localizadores tienen que caer en el suelo y a 200 mm o mas")
    out = []
    for _s, x, y in elegidos:
        if (x, y) == en_suelo[0][1:]:
            tipo = "loc"
        elif (x, y) == en_suelo[-1][1:]:
            tipo = "colisa"
        elif x > fondo_x - cb._cara_anillo_trasera(p):
            tipo = "fino"
        else:
            tipo = "ret"
        out.append((x, y, tipo))
    return out


def generado(p) -> str:
    v = ", ".join(f"{x:.3f}" for x in varillas_x(p))
    t = ", ".join(f'[{x:.3f}, {y:.3f}, "{tipo}"]' for x, y, tipo in tacos(p))
    return ("// GENERADO por case/cad/persiana.py -- no editar a mano. Lo compara\n"
            "// guarda_persiana_generada() en check_dxf.py.\n"
            f"varillas_persiana = [{v}];\n"
            f"tacos_persiana = [{t}];\n")


def geometria(p):
    perfil, cont = contorno(p)
    V = cb._vertices(p)
    alto, fondo_x = V[5][1], V[5][0]
    v = p["varilla_persiana"]
    xs = varillas_x(p)
    dentro = cont.buffer(-p["borde_persiana"], join_style="mitre")
    franjas_x = unary_union([box(a + v / 2, -10, b - v / 2, 400) for a, b in zip(xs, xs[1:])])
    r = p["fresa_d"] / 2
    ranuras = dentro.intersection(franjas_x).buffer(-r).buffer(r)
    macizo = cont.difference(ranuras)
    atados = unary_union([box(-50, y - p["alto_atado"] / 2, 400, y + p["alto_atado"] / 2)
                          for y in (alto / 3, 2 * alto / 3)])
    ventana_anillo = perfil.buffer(-p["cara_anillo"], join_style="mitre").intersection(
        box(-50, -50, fondo_x - cb._cara_anillo_trasera(p), 400))
    pasante = ranuras.intersection(ventana_anillo).difference(atados)
    fondo = ranuras.difference(pasante)
    ventana_real = perfil.buffer(-p[MARCO], join_style="mitre").intersection(
        box(-50, -50, fondo_x - p[MARCO_ATRAS], 400))
    abierto = pasante.intersection(ventana_real)
    return {"contorno": cont, "macizo": macizo, "fondo": fondo, "ranuras": ranuras,
            "pasante": pasante, "abierto": abierto, "varillas": len(xs), "alto": alto}
```

Y en `__main__`: leer `FONDO`, `PUENTE` de `p` (`p["t_persiana"]`, `p["t_persiana"] - p["hondo_ciego_persiana"]`), llamar a `autocomprobacion_ritmo(p)` al arrancar, y con `--escribir` hacer `open(GENERADO, "w", encoding="utf-8", newline="\n").write(generado(p))`.

> `cb._cara_anillo_trasera(p)` existe (`clearance_budget.py:375`, 23 mm). Si `_vertices`, `_centros_rosca_ciega` o `_m5_tabla_x` cambian de forma, el error sale aquí, no en silencio.

- [ ] **Paso 4: ver pasar el canario y escribir el fichero generado**

Run: `python case/cad/persiana.py --escribir && head -4 case/cad/persiana_generada.scad`
Esperado: la tabla del papel con **47 varillas**, respira ~18 800 mm², pesimista ~18,9 K con 64,2 W, y el fichero con `varillas_persiana = [4.000, ...]` y diez tacos, dos de ellos `"loc"` y `"colisa"` en y = 6,5.

- [ ] **Paso 5: poner en el papel las cifras que imprime el guion**

En `docs/superpowers/specs/2026-10-11-case-persiana-design.md`, cambiar 48 por el número de varillas que imprime, y las cifras de §3.1 (respira, se ve abierto, peso) y de la tabla de §5 por las que imprime. Ninguna a mano: copiar la salida.

- [ ] **Paso 6: commit**

```bash
git add case/cad/params.scad case/cad/persiana.py case/cad/persiana_generada.scad docs/superpowers/specs/2026-10-11-case-persiana-design.md
git commit -m "El generador de la persiana: ritmo determinista, tacos donde caben y el fichero que lee el modelo"
```

---

### Tarea 3: La persiana en el modelo, en sus DXF y en su puerta

**Ficheros:**
- Modificar: `case/cad/sam17_case.scad` (include, módulos nuevos, `PART`s, `assembly()`)
- Modificar: `case/cad/export.ps1` (`$piezas` y los STL)
- Modificar: `case/check_dxf.py` (`_sobres()`, `guarda_persiana()`, `guarda_persiana_generada()`, `main()`)
- Crear (por export): `case/plans/persiana_2d.dxf`, `persiana_pasante_2d.dxf`, `persiana_dorso_2d.dxf`

**Interfaces:**
- Consume: `persiana_generada.scad` (`varillas_persiana`, `tacos_persiana`); de `persiana.py`: `geometria(p)`, `generado(p)`, `tacos(p)`.
- Produce: módulos `persiana_contorno_2d()`, `persiana_ranuras_2d()`, `persiana_atados_2d()`, `persiana_pasante_2d()`, `persiana_2d()`, `persiana_dorso_2d()`, `persiana()`, `persianas()`; función `y_atados()`; `PART`s `"persiana_2d"`, `"persiana_pasante_2d"`, `"persiana_dorso_2d"`, `"assembly_persiana"`.

- [ ] **Paso 1: la puerta primero (falla porque no hay DXF)**

En `case/check_dxf.py`, añadir:

```python
def guarda_persiana_generada() -> list[str]:
    """persiana_generada.scad es lo que sale de persiana.py, byte a byte."""
    import clearance_budget as cb
    sys.path.insert(0, str(Path(__file__).parent / "cad"))
    import persiana
    p = cb.leer_params()
    ruta = Path(persiana.GENERADO)
    if not ruta.exists() or ruta.read_text(encoding="utf-8") != persiana.generado(p):
        return ["persiana_generada.scad no es lo que sale de persiana.py: corre "
                "`python case/cad/persiana.py --escribir` y vuelve a exportar"]
    return []


def guarda_persiana() -> list[str]:
    """Lo que el taller va a fresar de la persiana, releido del DXF:
    las ranuras no son mas estrechas que la fresa, ninguna varilla es mas fina
    que t / ESBELTEZ_MAX_PARED, el borde macizo no baja de borde_persiana, las
    puntas llevan el radio de la fresa, y el numero de ranuras es el del ritmo."""
    import clearance_budget as cb
    from shapely.geometry import LineString
    from shapely.ops import polygonize
    sys.path.insert(0, str(Path(__file__).parent / "cad"))
    import persiana
    p = cb.leer_params()
    f: list[str] = []
    doc = ezdxf.readfile(PLANS / "persiana_2d.dxf")
    lineas = [LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
              for e in doc.modelspace() if e.dxftype() == "LINE"]
    piezas = sorted(polygonize(lineas), key=lambda q: q.area, reverse=True)
    contorno, ranuras = piezas[0], piezas[1:]
    esperadas = len(persiana.varillas_x(p)) - 1
    ranuras = [r for r in ranuras if r.area > 1.0]
    huecos_contorno = len(contorno.interiors)
    if huecos_contorno != len(ranuras):
        f.append(f"persiana_2d: el contorno tiene {huecos_contorno} huecos y se leyeron {len(ranuras)} ranuras")
    if not (esperadas - 8 <= len(ranuras) <= esperadas):
        f.append(f"persiana_2d: {len(ranuras)} ranuras; el ritmo da {esperadas} (las de las puntas pueden no caber)")
    xs = sorted((r.bounds[0], r.bounds[2]) for r in ranuras)
    anchos = [b - a for a, b in xs]
    if min(anchos) < p["fresa_d"] - 0.02:
        f.append(f"persiana_2d: una ranura mide {min(anchos):.2f} y la fresa {p['fresa_d']:g}")
    varillas = [xs[i + 1][0] - xs[i][1] for i in range(len(xs) - 1)]
    minimo = p["t_persiana"] / cb.ESBELTEZ_MAX_PARED
    if min(varillas) < minimo - 0.02:
        f.append(f"persiana_2d: una varilla mide {min(varillas):.2f} y la esbeltez pide {minimo:.2f}")
    borde = min(contorno.exterior.distance(r) for r in ranuras)
    if borde < p["borde_persiana"] - 0.05:
        f.append(f"persiana_2d: el borde macizo baja a {borde:.2f} y se piden {p['borde_persiana']:g}")
    r = p["fresa_d"] / 2
    picos = [q for q in ranuras if q.buffer(-r).buffer(r).area < 0.995 * q.area]
    if picos:
        f.append(f"persiana_2d: {len(picos)} ranuras con esquinas mas vivas que la fresa (R{r:g})")
    if not f:
        print(f"  persiana_2d: {len(ranuras)} ranuras de {min(anchos):.2f} a {max(anchos):.2f}, "
              f"varillas de {min(varillas):.2f} o mas, borde de {borde:.2f}")
    return f
```

Y en `main()`, añadir `fallos += guarda_persiana_generada()` y `fallos += guarda_persiana()` antes de `todo_dxf_tiene_quien_lo_mire()`.

Run: `python case/check_dxf.py 2>&1 | tail -3`
Esperado: falla con `FileNotFoundError ... persiana_2d.dxf` (todavía no se exporta).

- [ ] **Paso 2: los módulos de la persiana en `sam17_case.scad`**

Después de `include <params.scad>` (línea 8), añadir `include <persiana_generada.scad>`. Después de `costillas()` (línea ~2401), añadir:

```scad
// --- LA PERSIANA (2026-10-11) ------------------------------------------------
// docs/superpowers/specs/2026-10-11-case-persiana-design.md. Una placa por
// costado, por fuera del anillo y tapandolo, en el plano del perfil (x = fondo,
// y = alto); el grueso en z, con la cara que apoya en el anillo en z = 0.
// El ritmo y los tacos vienen de persiana_generada.scad (persiana.py).
module persiana_contorno_2d()
    intersection() {
        perfil_lateral();
        translate([-50, suelo_persiana]) square([500, 500]);
    }

// El hueco entre cada dos varillas, dentro del borde macizo, con el radio de la
// fresa en las puntas: encoger y volver a crecer redondea las esquinas.
module persiana_ranuras_2d() {
    r = fresa_d / 2;
    v = varilla_persiana;
    xs = varillas_persiana;
    offset(r = r) offset(delta = -r)
        intersection() {
            offset(delta = -borde_persiana) persiana_contorno_2d();
            union()
                for (k = [0 : len(xs) - 2])
                    translate([xs[k] + v/2, -10]) square([xs[k+1] - xs[k] - v, 400]);
        }
}

function y_atados() = let (H = pts_perfil()[5].y) [H/3, 2*H/3];

module persiana_atados_2d()
    for (y = y_atados()) translate([-50, y - alto_atado/2]) square([500, alto_atado]);

// Lo que atraviesa: la ranura dentro de la ventana del anillo, menos los atados.
// Lo demas (la banda sobre el anillo y los atados) se queda a
// hondo_ciego_persiana desde fuera.
module persiana_pasante_2d()
    difference() {
        intersection() { persiana_ranuras_2d(); ventana_anillo_2d(); }
        persiana_atados_2d();
    }

// LA CARA (DXF): el contorno con todas las ranuras, que se fresan a
// hondo_ciego_persiana desde fuera. Lo pasante va en persiana_pasante_2d, y los
// tacos del dorso en persiana_dorso_2d: un DXF 2D no sabe decir profundidades.
module persiana_2d() difference() { persiana_contorno_2d(); persiana_ranuras_2d(); }

module persiana_dorso_2d()
    for (t = tacos_persiana)
        translate([t[0], t[1]]) difference() {
            circle(d = d_taco, $fn = 48);
            circle(d = d_iman + 0.1, $fn = 32);
        }

function alto_iman_taco_de(tipo) = tipo == "fino" ? alto_iman_fino : alto_iman_taco;

module persiana() {
    translate([0, 0, -t_persiana]) linear_extrude(t_persiana) persiana_2d();
    translate([0, 0, -(t_persiana - hondo_ciego_persiana)])
        linear_extrude(t_persiana - hondo_ciego_persiana)
            difference() { persiana_ranuras_2d(); persiana_pasante_2d(); }
    for (t = tacos_persiana)
        translate([t[0], t[1], 0]) difference() {
            cylinder(d = d_taco, h = alto_taco, $fn = 48);
            translate([0, 0, alto_taco - alto_iman_taco_de(t[2]) - 0.1])
                cylinder(d = d_iman + 0.1, h = alto_iman_taco_de(t[2]) + 0.2, $fn = 32);
        }
}

// Las dos, espejadas como los anillos: la de la izquierda apoya en z = 0 y
// sale hacia -z; la de la derecha apoya en ancho_total y sale hacia +z.
module persianas() {
    persiana();
    translate([0, 0, ancho_total]) mirror([0, 0, 1]) persiana();
}
```

En el despacho de `PART` (líneas ~2338-2373), añadir:

```scad
else if (PART == "persiana_2d")          persiana_2d();
else if (PART == "persiana_pasante_2d")  persiana_pasante_2d();
else if (PART == "persiana_dorso_2d")    persiana_dorso_2d();
else if (PART == "assembly_persiana")    persianas();
```

- [ ] **Paso 3: exportarlos**

En `case/cad/export.ps1`, añadir `"persiana_2d","persiana_pasante_2d","persiana_dorso_2d"` a `$piezas` y `"assembly_persiana"` a la lista de STL; en la línea final, `$($piezas.Count + 7)`.

- [ ] **Paso 4: los sobres**

En `_sobres()` de `case/check_dxf.py`, antes de `return`, añadir:

```python
    # LA PERSIANA (2026-10-11): sus tres DXF, con la envolvente que da su gemela
    # en shapely (persiana.py). Es la unica forma de cruzar dos gemelas que
    # viven en lenguajes distintos.
    sys.path.insert(0, str(Path(__file__).parent / "cad"))
    import persiana
    pg = persiana.geometria(p)

    def lados(geom):
        x0, y0, x1, y1 = geom.bounds
        return x1 - x0, y1 - y0
    dims["persiana_2d"] = lados(pg["contorno"])
    dims["persiana_pasante_2d"] = lados(pg["pasante"])
    tx = [t[0] for t in persiana.tacos(p)]
    ty = [t[1] for t in persiana.tacos(p)]
    dims["persiana_dorso_2d"] = (max(tx) - min(tx) + p["d_taco"], max(ty) - min(ty) + p["d_taco"])
```

- [ ] **Paso 5: exportar y releer**

Run: `powershell -NoProfile -File case/cad/export.ps1; echo $LASTEXITCODE`
Esperado: `2` y `check_dxf: VERDE`, con la línea `persiana_2d: 45 ranuras de 3.5x a 6.3x, varillas de 2.00 o mas, borde de 4.0x` (el número exacto, el que salga). Si `guarda_persiana()` canta esquinas vivas, el `offset(r) offset(delta)` del Paso 2 está al revés.

- [ ] **Paso 6: commit**

```bash
git add case/cad/sam17_case.scad case/cad/export.ps1 case/check_dxf.py case/plans/
git commit -m "La persiana en el modelo: su cara, lo que atraviesa y sus tacos, en tres DXF que relee su puerta"
```

---

### Tarea 4: Los bolsillos del anillo, y que las dos piezas casen

**Ficheros:**
- Modificar: `case/cad/sam17_case.scad` (`bolsillo_taco()`, `costilla()`, `costilla_bolsillos_2d()`, `PART`)
- Modificar: `case/cad/export.ps1` (`costilla_bolsillos_2d`)
- Modificar: `case/clearance_budget.py` (`guarda_tacos_persiana()`, su canario, `main()`)
- Modificar: `case/check_dxf.py` (`_sobres()`, `anillo_tiene_bolsillos()`, `main()`)
- Crear (por export): `case/plans/costilla_bolsillos_2d.dxf`; cambia `costilla_dorso_2d.dxf` solo si se mueve algo (no debería)

**Interfaces:**
- Consume: `tacos_persiana` (SCAD); `persiana.tacos(p)`; `cb._centros_rosca_ciega(p)`, `cb._m5_tabla_x(p)`, `cb.PARED_MIN_ANILLO`.
- Produce: módulos `bolsillo_taco(tipo)`, `bolsillo_taco_2d(tipo)`, `costilla_bolsillos_2d()`; `PART "costilla_bolsillos_2d"`; `guarda_tacos_persiana(p)`, `canario_tacos_persiana(p)`, `anillo_tiene_bolsillos()`.

- [ ] **Paso 1: la puerta de cotas (budget), y verla fallar con un canario**

En `case/clearance_budget.py`, junto a `guarda_anillo()`:

```python
def _tacos_persiana_cotas(p: dict[str, float]) -> list[tuple[str, float, float]]:
    """(que, tiene, pide) de cada relacion de cotas entre tacos y bolsillos."""
    fondo_trasera = p["t_anillo"] - p["rebaje_anillo"]           # el bolsillo de la trasera empieza ahi
    return [
        ("aire bajo el taco", p["hondo_bolsillo_taco"] - p["alto_taco"], 0.3),
        ("holgura del taco en su bolsillo", p["d_bolsillo_taco"] - p["d_taco"], 0.5),
        ("pared hasta el rebaje del acrilico", (p["cara_anillo"] - p["rebaje_anillo"])
         - (p["u_taco"] + p["d_bolsillo_taco"] / 2), PARED_MIN_ANILLO),
        ("canto hasta el chaflan de la silueta", p["u_taco"] - p["d_bolsillo_taco"] / 2,
         p["chaflan_anillo"] + 0.5),
        ("pared hasta el bolsillo de la trasera (iman fino)", fondo_trasera
         - (p["hondo_bolsillo_taco"] + p["alto_iman_fino"] + 0.1), PARED_MIN_ANILLO),
        ("el iman del anillo cabe en el anillo", p["t_anillo"]
         - (p["hondo_bolsillo_taco"] + p["alto_iman_anillo"] + 0.1), PARED_MIN_ANILLO),
        ("el iman del taco cabe en el taco", p["alto_taco"] - (p["alto_iman_taco"] + 0.1), 1.0),
    ]


def guarda_tacos_persiana(p: dict[str, float]) -> None:
    """La persiana apoya en el anillo y no en sus tacos, y los bolsillos no
    rompen hacia el rebaje, el chaflan ni el bolsillo de la trasera (persiana
    §4). Lo que el DXF no puede decir: profundidades y holguras."""
    for que, tiene, pide in _tacos_persiana_cotas(p):
        assert tiene >= pide - 1e-9, f"{que}: {tiene:.2f} mm y se piden {pide:.2f}"
    print("tacos de la persiana: " + ", ".join(
        f"{que} {tiene:.2f}" for que, tiene, _ in _tacos_persiana_cotas(p)))


def canario_tacos_persiana(p: dict[str, float]) -> None:
    for cambio, aviso in (({"alto_taco": p["hondo_bolsillo_taco"]}, "aire bajo el taco"),
                          ({"u_taco": p["u_taco"] + 1.0}, "rebaje del acrilico"),
                          ({"alto_iman_fino": 3.0}, "bolsillo de la trasera")):
        try:
            guarda_tacos_persiana({**p, **cambio})
        except AssertionError as e:
            assert aviso in str(e), f"canario de los tacos salto por '{e}'"
            continue
        raise AssertionError(f"canario de los tacos NO salto ({aviso})")
```

En `main()`, después de `guarda_anillo(p)`: `guarda_tacos_persiana(p)` y `canario_tacos_persiana(p)`.

Run: `python case/clearance_budget.py 2>&1 | grep -n "tacos de la persiana\|canario de los tacos"`
Esperado: `tacos de la persiana: aire bajo el taco 0.30, holgura ... 0.50, pared hasta el rebaje del acrilico 3.00, canto ... 2.00, pared hasta el bolsillo de la trasera ... 3.10, ...`. (Con los parámetros de la Tarea 2 pasa; el canario prueba que salta. Para verla fallar, poner `u_taco = 7` en `params.scad`, correr —`pared hasta el rebaje del acrilico: 2.50 mm y se piden 3.00`— y volver a 6.5.)

- [ ] **Paso 2: los bolsillos en el anillo**

En `case/cad/sam17_case.scad`, antes de `module costilla()`:

```scad
// LOS BOLSILLOS DE LA PERSIANA (2026-10-11): por la cara de FUERA del anillo,
// que ahora tapa la persiana, uno por taco. El localizador a d_taco (H7, en el
// pliego); la colisa, alargada en x; los demas con holgura. Debajo, el asiento
// del iman (fino en el tramo de atras: detras esta el bolsillo de la trasera).
// Lo vigilan guarda_tacos_persiana() (cotas) y anillo_tiene_bolsillos() (DXF).
function alto_iman_anillo_de(tipo) = tipo == "fino" ? alto_iman_fino : alto_iman_anillo;
module bolsillo_taco_2d(tipo)
    if (tipo == "colisa")
        hull() for (dx = [-(colisa_taco - d_taco)/2, (colisa_taco - d_taco)/2])
            translate([dx, 0]) circle(d = d_taco, $fn = 48);
    else circle(d = tipo == "loc" ? d_taco : d_bolsillo_taco, $fn = 48);
module bolsillo_taco(tipo) {
    translate([0, 0, -0.1]) linear_extrude(hondo_bolsillo_taco + 0.1) bolsillo_taco_2d(tipo);
    translate([0, 0, hondo_bolsillo_taco - 0.01])
        cylinder(d = d_iman + 0.1, h = alto_iman_anillo_de(tipo) + 0.11, $fn = 32);
}
// El DXF de la CARA DE FUERA: lo que se fresa por delante. Cada bolsillo con
// el asiento del iman dibujado dentro (como agujero, para que su circunferencia
// salga en el fichero); las profundidades van en el pliego.
module costilla_bolsillos_2d()
    for (t = tacos_persiana) translate([t[0], t[1]]) difference() {
        bolsillo_taco_2d(t[2]);
        circle(d = d_iman + 0.1, $fn = 32);
    }
```

Dentro de `costilla()`, en el `difference()`, después del cajeado de la brida:

```scad
        // los bolsillos de la persiana, por la cara de fuera (z = 0)
        for (t = tacos_persiana) translate([t[0], t[1], 0]) bolsillo_taco(t[2]);
```

En el despacho de `PART`: `else if (PART == "costilla_bolsillos_2d") costilla_bolsillos_2d();`. En `export.ps1`, añadir `"costilla_bolsillos_2d"` a `$piezas` y subir la cuenta final a `+ 8`.

- [ ] **Paso 3: la puerta del DXF (las dos piezas casan)**

En `case/check_dxf.py`, en `_sobres()`, junto a la persiana:

```python
    dims["costilla_bolsillos_2d"] = (max(tx) - min(tx) + p["colisa_taco"], max(ty) - min(ty) + p["d_bolsillo_taco"])
```

Y:

```python
def anillo_tiene_bolsillos() -> list[str]:
    """Los bolsillos de la cara del anillo caen donde los tacos del dorso de la
    persiana (las dos piezas casan, en el plano del perfil), y cada uno queda a
    PARED_MIN_ANILLO de toda rosca M4 del dorso y a 10 mm en x de todo M5 de la
    tabla. Las profundidades las mira guarda_tacos_persiana() en el budget."""
    import clearance_budget as cb
    p = cb.leer_params()
    f: list[str] = []

    def centros(nombre):
        aristas, comps = _componentes(nombre)
        out = []
        for comp in comps:
            px = [q[0] for j in comp for q in aristas[j]]
            py = [q[1] for j in comp for q in aristas[j]]
            if max(px) - min(px) > p["d_iman"] + 0.5:          # el de fuera, no el asiento
                out.append(((min(px) + max(px)) / 2, (min(py) + max(py)) / 2, max(px) - min(px)))
        return sorted(out)
    bolsillos, tacos_ = centros("costilla_bolsillos_2d"), centros("persiana_dorso_2d")
    if len(bolsillos) != len(tacos_) or len(bolsillos) != 10:
        f.append(f"costilla_bolsillos_2d: {len(bolsillos)} bolsillos y persiana_dorso_2d "
                 f"{len(tacos_)} tacos; se esperan 10 y 10")
        return f
    for (bx, by, bw), (tx, ty, _tw) in zip(bolsillos, tacos_):
        if math.dist((bx, by), (tx, ty)) > 0.05:
            f.append(f"el bolsillo en ({bx:.2f}, {by:.2f}) no casa con el taco en ({tx:.2f}, {ty:.2f})")
    for bx, by, bw in bolsillos:
        for nombre, c, d in cb._centros_rosca_ciega(p):
            pared = math.dist((bx, by), c) - min(bw, p["d_bolsillo_taco"]) / 2 - d / 2
            if pared < cb.PARED_MIN_ANILLO - 0.02:
                f.append(f"el bolsillo en ({bx:.2f}, {by:.2f}) deja {pared:.2f} contra la rosca {nombre}")
        if by <= p["u_taco"] + 1.0:
            for x in cb._m5_tabla_x(p):
                if abs(bx - x) < 10.0 - 0.02:
                    f.append(f"el bolsillo en x={bx:.2f} cae a {abs(bx - x):.2f} del M5 de la tabla en x={x:.2f}")
    if not f:
        print(f"  costilla_bolsillos_2d: 10 bolsillos que casan con los tacos de la persiana")
    return f
```

En `main()`: `fallos += anillo_tiene_bolsillos()`.

- [ ] **Paso 4: exportar, releer y correr el budget**

Run: `powershell -NoProfile -File case/cad/export.ps1; echo $LASTEXITCODE`
Esperado: `2` y `check_dxf: VERDE` con `10 bolsillos que casan`. Run: `python case/clearance_budget.py > /tmp/b.log 2>&1; echo $?` → `2`, sin `AssertionError`.

- [ ] **Paso 5: commit**

```bash
git add case/cad/sam17_case.scad case/cad/export.ps1 case/clearance_budget.py case/check_dxf.py case/plans/
git commit -m "Los bolsillos de la persiana en la cara del anillo, y la puerta que comprueba que las dos piezas casan"
```

---

### Tarea 5: La mejilla de acrílico se va

**Ficheros:**
- Modificar: `case/cad/sam17_case.scad` (`costado()`, `costado_2d()`, `costados()`, `tol_pmma()`, `PART "costado"/"costado_2d"`, `assembly()`, `assembly_acrilico()`, `lienzo_2d()`, ecos del BOM)
- Modificar: `case/cad/export.ps1` (`costado_2d` fuera de `$piezas`)
- Borrar: `case/plans/costado_2d.dxf`
- Modificar: `case/check_dxf.py` (`_retiro_costado`, `SOBRES["costado_2d"]`, `_contorno_costado`, el bloque del costado en `agujeros_donde_toca`, `PASO_BARRIDO` y `guarda_costado`, `main()`)
- Modificar: `case/clearance_budget.py` (`guarda_parametros_vivos`, `guarda_tramo_trasero`, `guarda_marco_ventana`, `guarda_rebaje`, `_cajas_solidas`, `_tol_pmma`)
- Modificar: `case/cad/params.scad` (las razones de `t_anillo`, `marco_fondo_trasera`, `t_cheek`, `n_bulkheads`, `cupon_largo`)

**Interfaces:**
- Consume: `persianas()` (Tarea 3).
- Produce: `_cajas_solidas()` con dos cajas nuevas, `"persiana izquierda"` y `"persiana derecha"`.

- [ ] **Paso 1: la caja de la persiana en `_cajas_solidas()`, y verla chocar**

En `_cajas_solidas()` (`clearance_budget.py:1537-1703`), donde se arman las cajas de las planchas, añadir:

```python
    # LAS DOS PERSIANAS (2026-10-11): por fuera de los anillos, de la tabla
    # (suelo_persiana por encima) a la silueta. Los tacos no van en caja: viven
    # en sus bolsillos y los mira guarda_tacos_persiana().
    fondo_x, alto = _vertices(p)[5]
    for nombre, z0, z1 in (("persiana izquierda", -p["t_persiana"], 0.0),
                           ("persiana derecha", p["ancho_total"], p["ancho_total"] + p["t_persiana"])):
        cajas.append((nombre, 0.0, fondo_x, p["suelo_persiana"], alto, z0, z1))
```

(usar el nombre de la lista que la función ya usa para las planchas; leerlo antes de pegar). Run: `python case/clearance_budget.py 2>&1 | grep -n "persiana\|solape" | head`. Esperado: o verde, o un solape contra la tabla si su caja llega a z < 0 (la tabla vuela 40 por fuera del anillo: su caja va de `-vuelo_zocalo` a `ancho_total + vuelo_zocalo` **por debajo** de y = 0, así que no debe tocar: la persiana empieza en y = 0,3). Si `solapes()` canta la persiana contra la tabla, revisar que la caja de la tabla tiene `y1 = 0`.

- [ ] **Paso 2: quitar el costado del modelo**

En `sam17_case.scad`: borrar `module costado()`, `module costado_2d()` (con su comentario de cabecera, líneas ~521-561), `module costados()` (líneas ~2376-2391) y las dos líneas `PART == "costado"` / `"costado_2d"` del despacho. Borrar `function tol_pmma()` (sin llamadores; usa `t_cheek`). En `assembly()`, cambiar `costados();` por `persianas();`. En `assembly_acrilico()`, dejar solo `planchas_acrilico();` y cambiar su comentario a «la trasera, sola: las mejillas de acrílico las sustituyó la persiana el 2026-10-11». En `lienzo_2d()`, quitar la fila de los dos costados (la fila 1) y dejar las planchas. En los ecos del BOM (líneas ~2779-3078), quitar las líneas de los costados y de su junta EPDM, y cambiar «plancha de acrílico: costados x2 y TRASERA — 3 piezas» por «plancha de acrílico: la TRASERA — 1 pieza», y añadir el eco de las dos persianas y de sus 20 pares de imanes.

> Antes de borrar `costado_2d()`, `grep -n "costado_2d\|costados()\|costado()" case/cad/*.scad case/*.py case/renders/*.py`: todo lo que salga, o se borra en este paso o tiene su sitio en esta tarea.

- [ ] **Paso 3: quitarlo de las puertas**

En `check_dxf.py`: borrar `_retiro_costado()`, la entrada `"costado_2d"` de `dims` en `_sobres()`, `_contorno_costado()`, el bloque del costado en `agujeros_donde_toca()` (líneas ~551-557), `PASO_BARRIDO` y su alias del PMMA (~767-777), `guarda_costado()` entera (~780-975) y su llamada en `main()`. En `export.ps1`, quitar `"costado_2d"` de `$piezas` y bajar la cuenta en 1. `git rm case/plans/costado_2d.dxf`.

En `clearance_budget.py`:
- `guarda_parametros_vivos()`: su sujeto era «`costados()` solo sabe dibujar 2»; pasa a ser «`persianas()` solo sabe dibujar 2»: mismo aserto contra `n_bulkheads`, con el mensaje y el docstring cambiados.
- `guarda_tramo_trasero()`: quitar el aserto «el costado entra ≥ 3» (líneas ~4570-4584) y su línea del docstring; **se queda** el de la pared entre los dos bolsillos (`>= PARED_MIN_ANILLO`), que sigue siendo verdad con el rebaje vacío.
- `guarda_marco_ventana()`: su caso de carga «el acrílico empujado desde fuera contra el marco» (líneas ~4680-4687, 4719-4722, 4771-4775) pierde el sujeto. Quitar los dos asertos que dependen del acrílico (la sombra ≥ 6 de acrílico y la flecha ≤ 2 «el acrílico se sale») y dejar escrito en el docstring: «`marco_fondo_trasera` = 30 se queda: lo puso este caso de carga, que murió con la mejilla el 2026-10-11, y bajarlo no compra nada que se vea».
- `guarda_rebaje()`: leerla entera; las condiciones que miden el acrílico en su rebaje (1, 3 y 4 según la junta) se quitan, y la que mide el rebaje como hueco del anillo (pared y labio) se queda. Si después de quitarlas no queda ninguna, la función se borra con su llamada.
- `_tol_pmma()`: la tolerancia de la trasera se calculaba con `t_cheek`; pasa a `t_piel` (el espesor de la trasera).

En `params.scad`: `t_cheek` se borra si tras lo anterior no lo lee nadie (`grep -n "t_cheek" case/`); `t_anillo` cambia su razón a «14: el bolsillo de la trasera (labio 3 + 11 de ancho) y los bolsillos de la persiana (6,9 de hondo) con PARED_MIN_ANILLO»; `marco_fondo_trasera`, `cupon_largo` y `n_bulkheads` cambian el comentario que nombra el acrílico.

- [ ] **Paso 4: correr todo**

Run: `python case/clearance_budget.py > /tmp/b.log 2>&1; echo $?` → `2` sin `AssertionError`. Run (PowerShell): `powershell -NoProfile -File case/cad/export.ps1; echo $LASTEXITCODE` → `2` y `check_dxf: VERDE`, sin `costado_2d` en la lista. Run: `grep -rn "costado_2d\|guarda_costado\|costados()" case/ docs/superpowers/plans/2026-10-11-case-persiana.md` → solo este plan.

- [ ] **Paso 5: commit**

```bash
git add -A case/ && git commit -m "La mejilla de acrílico se va: la persiana ocupa su sitio en el modelo, y las puertas que la miraban se retiran o cambian de sujeto"
```

---

### Tarea 6: La piel se va (D-S7)

**Ficheros:**
- Borrar: `case/cad/piel_organica.scad`, `case/cad/piel_borde.py`, `case/cad/piel_borde.json`, `case/cad/piel_termica.py`, `case/cad/celosia.py`, `celosia_ala.py`, `celosia_calco.py`, `celosia_kondor.py`, `celosia_placa.py` y los `celosia_*.json`, `case/cad/kondor_lattice.png`, `kondor_lattice.svg`, `case/renders/imprimir_piel.py`, `piel_choques.py`, `check_piel.py`, `render_piel.py`, y los `case/renders/sam17-piel*.png`
- Modificar: `.gitignore` (líneas ~110-121), `case/renders/cara_panel.py` (docstring), `params.scad:1034-1044` (el comentario de la regla 3 de `piel_choques.py`)

- [ ] **Paso 1: buscar quién se apoya en cada fichero**

Run: `grep -rln "piel_organica\|piel_borde\|piel_termica\|celosia\|kondor_lattice\|imprimir_piel\|piel_choques\|check_piel\|render_piel" --include=*.py --include=*.scad --include=*.ps1 --include=.gitignore . | grep -v "^./docs/"`
Esperado: solo los propios ficheros de la piel, `cara_panel.py` (docstring), `params.scad` (comentario) y `.gitignore`. **Si sale cualquier otro, parar**: la persiana no puede depender de la piel (la Tarea 2 ya leyó el contorno de `costilla_2d.dxf`).

- [ ] **Paso 2: borrar y limpiar**

```bash
git rm case/cad/piel_organica.scad case/cad/piel_borde.py case/cad/piel_borde.json case/cad/piel_termica.py \
       case/cad/celosia*.py case/cad/celosia*.json case/cad/kondor_lattice.png case/cad/kondor_lattice.svg \
       case/renders/imprimir_piel.py case/renders/piel_choques.py case/renders/check_piel.py \
       case/renders/render_piel.py case/renders/sam17-piel*.png
```

En `.gitignore`, borrar la lista blanca de `sam17-piel*.png` y las líneas de `print/piel`. En `cara_panel.py`, cambiar «Lo llama render_piel.py» por «Lo llama render_persiana.py». En `params.scad`, el comentario de `vuelo_zocalo` que cita «la regla 3 de piel_choques.py» pasa a «la vigilaba la regla 3 de piel_choques.py, que murió con la piel el 2026-10-11; la tabla está en espera (D-S4)».

- [ ] **Paso 3: puertas**

Run: `python hardware/tools/gates.py 2>&1 | tail -6` → verde o con los HUECOS de siempre, **sin** `check_piel` en la lista. Run: `ruff check case/` → limpio.

- [ ] **Paso 4: commit**

```bash
git commit -m "La piel se va del repo (D-S7): cubierta, cachetes, corteza, su puerta y sus renders; queda en el historial"
```

---

### Tarea 7: Los renders del repo

**Ficheros:**
- Modificar: `case/cad/sam17_case.scad` (`PART`s de render: `"render_rieles"`, `"render_negro"`, `"render_paneles"`)
- Modificar: `case/cad/export.ps1` (los tres STL)
- Modificar: `case/renders/cara_panel.py` (`fila_valle()` y su llamada en `vestir()`)
- Crear: `case/renders/render_persiana.py`
- Modificar: `.gitignore` (lista blanca `sam17-persiana*.png`)
- Crear: `case/renders/sam17-persiana.png`, `sam17-persiana-lado.png`, `sam17-persiana-noche.png`, `sam17-persiana-costado.png`, `sam17-persiana-trasera.png`

**Interfaces:**
- Consume: los STL de `export.ps1` en `case/renders/build/` (`assembly_persiana`, `assembly_acrilico`, `assembly_madera`, y los tres nuevos); `cara_panel.vestir(ns, paneles)`.
- Produce: `cara_panel.fila_valle(cara, M, alto, ancho)`.

- [ ] **Paso 1: las partes por material**

En el despacho de `PART` de `sam17_case.scad`:

```scad
// Para render_persiana.py: lo que se pinta de cada color. Plateado solo los
// Z-Rails (comprados); negro todo lo demas del aluminio; los paneles, grafito.
else if (PART == "render_rieles")   rails();
else if (PART == "render_negro")    { costillas(); marcos_ventana(); nariz(); miembros(); tapa_valle(); tira_valle(); }
else if (PART == "render_paneles")  paneles();
```

En `export.ps1`, añadir `"render_rieles","render_negro","render_paneles"` a la lista de STL.

- [ ] **Paso 2: el valle con paneles en `cara_panel.py`**

Llevar `vestir_valle()` del guion del acta (`C:\Users\simon\AppData\Local\Temp\claude\D--Desktop-projects-sam17\dddcb8e5-6871-4320-b7ee-40c834cee6aa\scratchpad\monje\escena.py`) a `cara_panel.py` como `fila_valle(cara, M, alto, ancho)`, con el mismo reparto PROVISIONAL (cascos 14 HP, ocho entradas y salidas 44 HP, MIDI y reloj 30 HP, USB y un nivel 16 HP) y su docstring: «PROVISIONAL: nadie ha decidido qué va en el valle; es la conexión con el exterior que el papel del instrumento le pone (instrumento-entero §6.2), firmada como punto de partida (D-S6)». En `marcos()`, añadir la fila `"valle"` con la matriz de la cara horizontal: `M = Matrix(((0, 1, 0, x0), (0, 0, 1, y_top), (1, 0, 0, t_anillo + t_placa), (0, 0, 0, 1)))`, con `x0` y `y_top` de `cb._centros_rail_1u(p, P, cr)[0]` (`x0 = c.x - inset_er`, `y_top = P[3].y - rehundido_panel`) y alto `alto_panel_1u`; y en `comprobar()` la fila del valle entra como las otras. En `vestir()`, rellenar `"valle"` con `fila_valle`.

- [ ] **Paso 3: `render_persiana.py`**

Copiar la escena del acta (la misma `escena.py` del scratchpad) como `case/renders/render_persiana.py`, con estos cambios: las partes salen de `case/renders/build/` (los STL de `export.ps1`) y se re-exportan si el `.scad`, `params.scad` o `persiana_generada.scad` son más nuevos (como `render.py`, `importar()`); las persianas son `assembly_persiana.stl` en `anodizado_negro`; las vistas `frente` (az 32, el 25), `trasera` (az 222, el 19), `lado` (az 68, el 14), `noche` (como `lado`, a oscuras y con la luz de dentro) y `costado` (ortográfica de lado puro, fondo transparente), con salida `sam17-persiana*.png`; y `PERSIANA_MOTOR=eevee` para iterar. Los umbrales de `medir()` de `render.py` se calibraron con naranja y plata: `render_persiana.py` lleva los suyos (cobertura mínima 0,05 y brillo mínimo 0,08, medidos sobre la primera corrida y escritos con la fecha).

- [ ] **Paso 4: correrlo**

Run: `"/c/Program Files/Blender Foundation/Blender 5.0/blender.exe" -b --factory-startup -P case/renders/render_persiana.py > /tmp/r.log 2>&1; grep -n "OUT\|Traceback" /tmp/r.log`
Esperado: cinco `OUT` y los cinco PNG en `case/renders/`. Mirarlos ampliados (esquinas y juntas a ×3: la regla de los renders del repo).

- [ ] **Paso 5: commit**

En `.gitignore`, la lista blanca `!case/renders/sam17-persiana*.png` (junto a la del 195).

```bash
git add case/cad/sam17_case.scad case/cad/export.ps1 case/renders/cara_panel.py case/renders/render_persiana.py case/renders/sam17-persiana*.png .gitignore
git commit -m "Los renders del repo con la persiana, y la fila del valle con sus paneles (provisional)"
```

---

### Tarea 8: El papel de taller y los papeles de antes

**Ficheros:**
- Modificar: `case/PLIEGO.md`, `case/RFQ.md`, `case/README.md`
- Modificar: `docs/superpowers/specs/2026-08-15-case-design.md` (rev. 30)
- Modificar: `docs/superpowers/specs/2026-09-05-case-piel-organica-design.md` (enmienda de cierre arriba)
- Modificar: las cuatro specs de agosto que describen la mejilla coplanar: `2026-08-28-costilla-pletina-design.md`, `2026-08-29-marco-ventana-banda-estructural-design.md`, `2026-08-29-trasera-capturada-talon-nariz-design.md`, `2026-08-30-techo-macizo-chapas-empotradas-design.md` (una enmienda arriba en cada una)
- Modificar: `docs/superpowers/specs/2026-10-11-case-persiana-design.md` (estado: implementado, con los commits)

- [ ] **Paso 1: el PLIEGO**

Bitácora, rev. 28: «2026-10-11: la persiana sustituye a las mejillas de acrílico (papel `2026-10-11-case-persiana-design.md`)». En §1, el PMMA naranja deja de ser material de las mejillas: queda la trasera. **Pieza nueva, la persiana** (dos, espejadas: dos programas): 6082-T651 laminada y estirada (no placa colada: se anodiza manchada), de 12 frenteada a 9,5 con los tacos; orden de operaciones (frentear las dos caras; todas las ranuras a 4 de fondo por delante con las paredes acabadas mientras el alma de 2 las sostiene; el pasante de los últimos 2 mm solo en `persiana_pasante_2d`, por tramos entre atados, sobre placa de sacrificio; el contorno al final); fresa Ø3 de 3 filos; chaflán 0,2 × 45° en las aristas de delante y repaso por detrás; planitud ≤ 0,2 sobre 320 tras ranurar y anodizar (pregunta eliminatoria, como el anillo); los tres DXF y qué dice cada uno. **El anillo**: gana los diez bolsillos de `costilla_bolsillos_2d` por la cara de fuera (hondos: 3,8 el del taco más el asiento del imán, 3,1 o 1,1 en el tramo de atrás); el localizador a 8 H7 y la colisa; el rebaje se queda (vacío). **El anodizado**: todo el aluminio visto en 6082-T6/T651, negro, ISO 7599 AA15–AA20 sellado, un anodizador y un lote, contactos del bastidor en caras tapadas (el dorso de la banda de la persiana, la cara interior del anillo), arista rota ≥ 0,2 en todo canto visto; el «anodizado satinado» del anillo se cambia. **Los imanes**: 20 pares N42 Ø6 entre los dos costados: 16 pares de un Ø6 × 3 en el anillo con un Ø6 × 2 en el taco, y 4 pares de Ø6 × 1 + Ø6 × 1 en el tramo de atrás (contarlos contra `tacos_persiana`), con la polaridad fija y marcada. **La muestra** (#398): la tira de altura completa de §3.4 del papel, y lo que mide. Las roscas del suelo: corregir las cotas atrasadas (M5 de la tabla en 53,3 / 159,9 / 266,5 y M4 del suelo en 242,76, las que da hoy el budget). Quitar todo lo que nombra el costado de acrílico (la junta EPDM del costado, «el acrílico lo nota», el criterio 2 del cupón —pasa a «la persiana asienta plana en la cara del anillo y sus tacos entran en sus bolsillos», con la tira de muestra—).

- [ ] **Paso 2: el RFQ y el README**

RFQ: el bloque de taller de la persiana (las preguntas de la tira, la planitud, el orden de operaciones, los dos programas), el anillo con sus bolsillos, el anodizador único, y fuera el PMMA de las mejillas. README: un bloque arriba «2026-10-11: la persiana» con lo que es, el render `renders/sam17-persiana.png` enlazado, la línea de BOM de la persiana, sus imanes y sus tacos, y el estado.

- [ ] **Paso 3: las specs**

`2026-08-15-case-design.md`: rev. 30 en la bitácora (rev. 29 ya existe). En el papel de la persiana, §8: «`ancho_exterior` entra cuando se decida la tabla (D-S4): hoy no lo lee nadie y no se crea un parámetro sin lector». La piel: enmienda de cierre arriba — «**Sucedida el 2026-10-11** por `2026-10-11-case-persiana-design.md`. D-P1 nunca se firmó; D-P2 la retiró D-S2 de la persiana. Sus guiones salieron del repo con la persiana; quedan en el historial». Las cuatro de agosto: una línea arriba — «**Enmienda 2026-10-11:** la mejilla de acrílico coplanar que este papel describe la sustituyó la persiana (`2026-10-11-case-persiana-design.md`); el rebaje del anillo se queda vacío». La de la persiana: estado «implementado» con los hashes de esta tanda.

- [ ] **Paso 4: commit**

```bash
git add case/PLIEGO.md case/RFQ.md case/README.md docs/superpowers/specs/
git commit -m "El pliego, el RFQ y el README de la persiana, y las enmiendas a los papeles que la mejilla y la piel dejan atrás"
```

---

### Tarea 9: Issues, puertas completas, PR y merge

- [ ] **Paso 1: las puertas enteras**

Run: `sh .githooks/pre-push < /dev/null 2>&1 | tail -15`
Esperado: todas en OK o con sus HUECOS declarados (el del #289 entre ellos), y ningún ROJO.

- [ ] **Paso 2: push y PR**

```bash
git push -u origin feat/case-persiana
gh pr create --title "La persiana: el case sin piel, y el costado que respira" --body-file /tmp/pr.md
```

El cuerpo (`/tmp/pr.md`) dice en llano qué cambia (las tres cosas que se ven: el costado, el negro, las rendijas), qué se fue (la piel, la mejilla), qué queda en espera (la tabla, D-S4) y qué viene después (el plan del aire y el #289), con los renders enlazados. Sin líneas de atribución.

- [ ] **Paso 3: merge y comprobación sobre el resultado**

```bash
gh pr merge --merge --delete-branch
git fetch -q origin && git checkout --detach origin/main && sh .githooks/pre-push < /dev/null 2>&1 | tail -5
```

- [ ] **Paso 4: los issues, a mano y con previsto contra encontrado**

- #392 y #397: cerrar («murió con la piel el 11-10; ver el papel de la persiana §10»).
- #393: retitular a «La persiana se sujeta con tacos e imanes: medir el tirón en la tira de muestra» y comentar lo hecho (los diez bolsillos) y lo que falta (el tirón medido).
- #398: retitular a «La tira de muestra de la persiana: 60 × 256, dos atados, dos tacos con imanes» y poner en el cuerpo lo que mide (§3.4 del papel).
- #289: comentar que la persiana ya está en el modelo y que se cierra con el plan del aire (cifra v4 → v5, `_tiro()` con el plano neutro).
- Abrir, con el hito 6: «El ensayo de derrame, también en los costados (D-S10)» y «Los costados libres: la holgura que hace falta, medida al encender, al manual y al pliego (D-S11)».

---

## Autorrevisión

- **Cobertura del papel:** §3 (la persiana) → Tareas 2-3; §3.3-3.4 (atados, sonido, muestra) → Tareas 2-3 (geometría), 8 (PLIEGO, muestra) y 9 (#398); §4 (sujeción) → Tarea 4; §5 (el aire) → el plan del aire (fuera, declarado arriba), y `persiana.py` imprime sus cifras; §6 (líquidos) → Tarea 9 (issue); §7.1 (el negro) → Tareas 7 y 8; §7.2 (el anillo, lo que muere con el acrílico) → Tareas 4 y 5; §7.3 (rendijas) → Tarea 1; §8 (ancho y tabla) → la tabla en espera; `ancho_exterior` entra con la decisión de la tabla, y la Tarea 8 lo deja escrito en el papel; §9 (luz) → no (D-S5 «no por ahora»); §10 (retirar) → Tareas 5, 6 y 9; §11 (renders) → Tarea 7.
- **Huecos sin tarea:** ninguno de los once HUECOS del papel se resuelve en código; los que piden medir (sonido, tirón, holgura, derrame) quedan en issues (Tarea 9).
- **Nombres:** `persiana.tacos(p)`, `persiana.varillas_x(p)`, `persiana.geometria(p)`, `persiana.generado(p)`, `persiana.GENERADO`, `guarda_tacos_persiana`, `canario_tacos_persiana`, `anillo_tiene_bolsillos`, `guarda_persiana`, `guarda_persiana_generada`, `guarda_labio_chapas`, `canario_labio_chapas`, `_labio_chapas`, `fila_valle` — usados igual en todas las tareas.
