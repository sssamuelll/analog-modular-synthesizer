# El aire del case con el plano neutro — plan de implementación

> **Para quien lo ejecute:** SUB-SKILL OBLIGATORIA: superpowers:subagent-driven-development (recomendada) o superpowers:executing-plans, tarea por tarea. Los pasos usan casillas (`- [ ]`).

**Objetivo:** que `guarda_aire()` vuelva a juzgar el aire del case —con la potencia de la fuente v5 (64,22 W) y la chimenea contada con el plano neutro y las dos persianas— y que el #289 se cierre sin dejar copias viejas detrás.

**Arquitectura:** `potencia_disipada` sigue siendo una copia en `params.scad`, ahora de `ladrillo_budget.calor_del_cajon_w()` de la v5, y `guarda_potencia_vigente()` la cruza contra ese origen. El plano neutro pasa de `case/cad/persiana.py` a `case/clearance_budget.py`, con estas piezas:
- `_plano_neutro()`, con su cuenta a mano;
- `_huecos()`, que junta lo que respira de las dos persianas (lo calcula `persiana.py`, con importación diferida y caché) con la rejilla baja de la trasera, la rendija y las ondas;
- `_tiro()`, que devuelve el salto, lo que la chimenea evacua al techo y cuánto le falta.

`guarda_aire()` vuelve a ser un aserto con `C_D = 0,65`. Tres cosas se imprimen como avisos: el pesimista, la sala de 45 °C y un costado tapado; las dos últimas publican su HUECO mientras no pasen. La cadena de la v4 (`calor_budget.py` y lo que cuelga de él) se queda como la base de la v4 y deja de seguir al case.

**Tecnologías:** Python 3 con `shapely` y `numpy`, los que ya usa `persiana.py`. OpenSCAD no entra: no cambia ninguna cota salvo la potencia, ni se regenera ningún DXF o render.

**Papeles:**
- `docs/superpowers/specs/2026-10-11-case-persiana-design.md`, firmado el 11-10: §5 (el calor), §13 (HUECO 4, la holgura de los costados) y §14 (el orden).
- La tabla del §7 de `docs/superpowers/specs/2026-09-05-fuente-v5-ladrillo-design.md` (`potencia_disipada` 147,31 → 64,22), con la dirección firmada el 08-09 (D-V4).
- Issue #289.

**Lo que este plan decide, y por qué:**

1. **La cadena de la v4 no sigue al case.**
   - `calor_budget.py` modela la v4: seis módulos AC-DC en un recinto de acero dentro del cajón. La v4 no se monta (D-V4).
   - Su `A_EF_BASE_MM2` es «el venteo que el case ya tiene, sin las aberturas de D-F3», y las aberturas de D-F3 son las persianas. Se queda en 3299, con la cuenta en serie de su propio modelo.
   - Su contrato la sigue recalculando desde `params.scad` (rejilla, rendija y ondas), así que si la trasera cambia, se ve.
   - Re-derivarla con el plano neutro la bajaría un 6,7 %. Eso movería las predicciones de un arranque que no va a ocurrir, y `medidas.csv` las compara al 1e-5.
   - El relevo de ese modelo es el plan de la v5, cuyo §7 lo reabre entero. Por eso `TECHO_VENTEO_MM2`, `medidas.csv` y `check_bringup.py` no cambian de número; el plan lo comprueba corriéndolos.
   - Dato para el papel: en los términos de la v4 (en serie, con 105 mm de tiro), la persiana equivale a 10 776 mm² más de venteo, y la v4 pedía 20 907. La v4 no cabía en este case, que es lo que firmó D-V4.
2. **La sala de diseño no cambia.**
   - El case cuenta su aire a 20 °C (`T_AMB = 293`, `RHO_AIRE = 1.2`). El #289 avisaba de que la sala de diseño de la spec del chasis es de 45 °C.
   - A 45 °C, contando la densidad y la temperatura del aire de esa sala, el salto escala con la temperatura absoluta:
     - con la `C_D` de la puerta, de 16,9 a 18,3 K: pasa;
     - con el pesimista, de 18,9 a 20,5 K: **no pasa**. El paso 7,0 de la persiana se eligió para que el pesimista pasara.
   - El plan no cambia la base: imprime las dos cifras y publica un HUECO. La sala del case la decide Samuel.

**Fuera de este plan:**
- la sala de diseño (lo de arriba);
- el relevo de la cadena de la v4, que es del plan de la v5;
- cuánta holgura necesitan los costados (HUECO 4, se mide en el arranque);
- la `C_D` de la ranura (HUECO 6);
- la vista de las rendijas de cerca (#420).

## Restricciones globales

- Rama `feat/aire-plano-neutro` en el worktree `.claude/worktrees/persiana`, sacada de `main` en 7f2877c. El plan va en esa misma rama.
- Los commits, el PR y los issues no llevan líneas de atribución ni narran el proceso (CLAUDE.md, «Repos públicos»).
- Techo: `salto_termico_max = 20` K (de `tuning_budget.py`). La puerta juzga con `CD_TIRO = 0.65`; el pesimista `CD_TIRO_PESIMISTA = 0.55` solo se imprime (papel §5.5).
- `potencia_disipada = 64.22` W. `ladrillo_budget.calor_del_cajon_w()` da 64,2185 y el cruce tolera 0,01.
- El plano neutro es el de `persiana.py` hoy:
  - cada hueco es `(y, a)`, en mm y mm²;
  - el plano `yn` iguala Σ a·√(yn − y) de los huecos de abajo con Σ a·√(y − yn) de los de arriba;
  - `S` es la suma de arriba;
  - `k = ρ·cp·C_D·√(2g/T)·S·1e-6·√1e-3` y `ΔT = (P/k)^(2/3)`.
- Ninguna cota de `params.scad` cambia salvo `potencia_disipada`.
- Las puertas:
  - `python case/clearance_budget.py`, que sale con 2 por sus HUECOS declarados;
  - `python case/check_dxf.py`, en VERDE;
  - `python hardware/01-power-supply/v4/calor_budget.py`, `python hardware/02-midi-cv/power_budget.py` y `python hardware/01-power-supply/v4/check_bringup.py`;
  - al final, `sh .githooks/pre-push < /dev/null`.
- Con `PYTHONIOENCODING=utf-8` en las corridas que imprimen tildes. Las salidas largas van a `$S`, un directorio temporal fuera del repo (en la sesión que ejecuta, su scratchpad); cada llamada a la shell lo vuelve a definir.

## Lo que más puede morder sin que un test lo vea

1. **Un HUECO que se publica siempre.** Los dos nuevos (los costados y la sala) tienen que mirar la carga: con 1 W se callan. El canario lo prueba por los dos lados (Tarea 3).
2. **La caché devolviendo las franjas de otra geometría.** La clave es la tupla entera de `p`. El canario cambia `paso_persiana` y exige que el salto se mueva (Tarea 3).
3. **Un import circular.** `persiana.py` importa `clearance_budget` al cargarse, así que el budget solo puede importarla dentro de una función. Si alguien sube ese import al principio del fichero, revienta la carga. La Tarea 3 lo deja diferido y comentado.
4. **La potencia de la v5 importando la v4.** `ladrillo_budget.py` importa `calor_budget.py` de la v4, que importa `clearance_budget.py`. El import diferido de `_potencia_del_cajon()` ya convivía con ese ciclo (Tarea 1).
5. **La rendija, casi muda con las persianas.** Casi todo el aire sale ahora por los costados, y ahogar la rendija mueve el salto solo 0,8 K. El canario exige que suba más de 0,1, no cuánto.

---

### Tarea 0: Línea base

**Ficheros:** ninguno.

- [ ] **Paso 1: comprobar la rama y guardar las salidas de hoy**

```bash
cd D:/Desktop/projects/sam17/.claude/worktrees/persiana
git branch --show-current            # feat/aire-plano-neutro
mkdir -p "$S"
PYTHONIOENCODING=utf-8 python case/clearance_budget.py > $S/budget_0.txt 2>&1; echo "exit $?"
PYTHONIOENCODING=utf-8 python case/cad/persiana.py > $S/persiana_0.txt 2>&1
for g in hardware/01-power-supply/v4/calor_budget.py hardware/02-midi-cv/power_budget.py hardware/01-power-supply/v4/check_bringup.py; do
  PYTHONIOENCODING=utf-8 python $g > $S/$(basename $g .py)_0.txt 2>&1; echo "$g exit $?"; done
grep -n "de venteo efectivo" $S/budget_0.txt
```

Esperado: el budget con `exit 2` y el HUECO del venteo con 147.31 W («Hacen falta 25025 mm2 de venteo efectivo…»). Los otros tres con el exit de siempre. Anota los tres exit.

---

### Tarea 1: La potencia es la de la fuente v5

**Ficheros:**
- Modificar `case/clearance_budget.py`:
  - `_potencia_del_cajon()`;
  - `_reparto_del_cajon()`, que se borra;
  - el mensaje y el `print` de `guarda_potencia_vigente()`;
  - el HUECO de `guarda_aire()`.
- Modificar `case/cad/params.scad`: `potencia_disipada` y su comentario.

**Interfaces:**
- Produce `_potencia_del_cajon() -> float`, que devuelve 64,2185 W leídos de `ladrillo_budget.calor_del_cajon_w()`, y `potencia_disipada = 64.22`.

- [ ] **Paso 1: leer la v5 y decirlo en el mensaje**

Sustituir `_potencia_del_cajon()` entera:

```python
def _potencia_del_cajon() -> float:
    """Los W que el case tiene que evacuar, LEIDOS DE DONDE SE CALCULAN.

    `potencia_disipada` de params.scad es una COPIA, y el .scad la necesita
    porque es OpenSCAD y no puede importar nada. Desde el 2026-10-12 es la de
    la fuente v5 (D-V4, firmada en direccion el 08-09): todo lo que baja por el
    cordon del ladrillo acaba en calor dentro de la caja, y lo unico que se
    queda fuera es la perdida AC-DC del propio ladrillo. El numero lo calcula
    hardware/01-power-supply/v5/ladrillo_budget.py, calor_del_cajon_w(). Hasta
    ese dia era la suma de la v4, p_cajon_w + p_recinto_w a placa: 147.31 W,
    con el recinto de la fuente dentro del cajon.

    EL 2026-09-04 ESA COPIA LLEVO UN DIA MINTIENDO. Decia 147.83 cuando la
    franja de red (2.75 W de la NTC de arranque y 0.95 del choke) ya la habia
    subido a 151.55, y con ella se le publico al #289 un encargo de 25113 mm2
    de venteo cuando eran 25742. Nadie hizo nada mal: el numero cambio en la
    fuente y aqui no habia nada que lo notara.

    EL IMPORT ES DIFERIDO A PROPOSITO. ladrillo_budget.py importa
    calor_budget.py de la v4, y calor_budget.py importa de este modulo
    (CD_TIRO, CD_TIRO_PESIMISTA, CP_AIRE, G, RHO_AIRE), asi que a nivel de
    modulo esto seria un ciclo. Y el aserto vive en guarda_potencia_vigente()
    y no al importar: un aserto al importar dejaria rojos tambien a
    power_budget, margen_budget, secuencia_budget, fusible_budget,
    invitados_budget y check_bringup, que no tienen la culpa de un numero
    descuadrado aqui."""
    import os
    import sys
    v5 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "hardware", "01-power-supply", "v5")
    if v5 not in sys.path:
        sys.path.insert(0, v5)
    from ladrillo_budget import calor_del_cajon_w
    return calor_del_cajon_w()
```

Borrar `_reparto_del_cajon()` entera: el reparto entre el recinto y el cajón es de la v4, y en la v5 no hay recinto. En `guarda_potencia_vigente()`, sustituir el aserto y el `print`:

```python
    pot = _potencia_del_cajon()
    assert abs(p["potencia_disipada"] - pot) < 0.01, (
        f"potencia_disipada dice {p['potencia_disipada']:.2f} W y "
        f"ladrillo_budget.py de la fuente v5, que es donde se calcula, da "
        f"{pot:.2f}: lo que baja por el cordon del ladrillo, que acaba entero en "
        f"calor dentro de la caja. {abs(p['potencia_disipada'] - pot):.2f} W de "
        f"desfase. Este numero NO se toca aqui para que la puerta calle: si la "
        f"fuente lo cambio, copia el suyo a params.scad y vuelve a correr -- el "
        f"salto y el veredicto del aire se recalculan solos. Si el que esta mal "
        f"es el de la fuente, arreglalo alli y no aqui")
    print(f"potencia del cajon: {pot:.2f} W, y params.scad dice lo mismo "
          f"(la copia se cruza contra ladrillo_budget.py de la fuente v5)")
```

En `guarda_aire()`, el HUECO (dura hasta la Tarea 3) deja de nombrar el reparto. Sustituir el bloque `if t["dt"] > ...:` entero:

```python
    if t["dt"] > p["salto_termico_max"] + 1e-9:
        _HUECOS.append(
            f"esta geometria evacua {t['p_evacuada']:.1f} W al techo de "
            f"{p['salto_termico_max']:.0f} K y el instrumento le mete "
            f"{p['potencia_disipada']:.2f} (lo que baja por el cordon del "
            f"ladrillo, fuente v5): sube {t['dt']:.0f} K. Hacen falta "
            f"{t['a_ef_techo']:.0f} mm2 de venteo efectivo, "
            f"{t['a_ef_techo'] - t['a_ef']:.0f} MAS que los {t['a_ef']:.0f} de "
            f"hoy ({t['a_ef_techo_pared'] - t['a_ef']:.0f} si se cuenta la "
            f"pared exterior); y menos si el venteo nuevo sube el TIRO, que va "
            f"con la RAIZ de la altura y hoy son {t['h']*1000:.0f} mm en un "
            f"case de {perfil(p)['alto_total']:.0f}. Lo cierra el papel del "
            f"case con D-F3 = A (#289), no esta puerta")
```

- [ ] **Paso 2: ver la copia vieja en rojo**

```bash
cd case && python -c "import clearance_budget as cb; cb.guarda_potencia_vigente(cb.leer_params())"; cd ..
```

Esperado: `AssertionError: potencia_disipada dice 147.31 W y ladrillo_budget.py de la fuente v5, que es donde se calcula, da 64.22…`

- [ ] **Paso 3: aplicar la enmienda de la v5 en `params.scad`**

Justo encima de la línea `potencia_disipada = 147.31; ...`, añadir el párrafo, y cambiar la línea:

```
// 64.22 DESDE EL PLAN DEL AIRE (2026-10-12): la fuente v5 (D-V4) saca la
// etapa AC-DC de la caja, y el calor del cajon es lo que baja por el cordon
// del ladrillo (hardware/01-power-supply/v5/ladrillo_budget.py,
// calor_del_cajon_w(): 56.23 W entregados a las cargas + 7.99 perdidos
// convirtiendo dentro). La v5 lo mando el 05-09 en su sec.7 y quedo sin
// aplicar hasta aqui. El desglose de arriba es el de la v4, que no se monta.
potencia_disipada = 64.22; // W, TODO el cajon: lo que baja por el cordon (fuente v5)
```

- [ ] **Paso 4: verde, y el resto de la cadena sin moverse**

```bash
cd case && python -c "import clearance_budget as cb; cb.guarda_potencia_vigente(cb.leer_params())"; cd ..
PYTHONIOENCODING=utf-8 python case/clearance_budget.py > $S/budget_1.txt 2>&1; echo "exit $?"
diff $S/budget_0.txt $S/budget_1.txt
for g in hardware/01-power-supply/v4/calor_budget.py hardware/02-midi-cv/power_budget.py hardware/01-power-supply/v4/check_bringup.py; do
  PYTHONIOENCODING=utf-8 python $g > $S/$(basename $g .py)_1.txt 2>&1; echo "$g exit $?"
  diff -q $S/$(basename $g .py)_0.txt $S/$(basename $g .py)_1.txt; done
python -m ruff check case/clearance_budget.py
```

Esperado:
- `potencia del cajon: 64.22 W, y params.scad dice lo mismo (… fuente v5)`.
- El budget, con `exit 2`. En el diff solo cambian la línea de la potencia y las del aire que dependen de ella: el salto, los dos avisos y el HUECO del venteo, que sigue publicándose con 64.22 W porque la chimenea todavía es la de agosto. `canario_techo()` no salta.
- Los otros tres, con el mismo exit e idénticos.
- `ruff`, limpio.

- [ ] **Paso 5: commit**

```bash
git add case/clearance_budget.py case/cad/params.scad
git commit -F - <<'EOF'
La potencia del case es la de la fuente v5: 64.22 W, lo que baja por el cordón del ladrillo

params.scad::potencia_disipada pasa de 147.31 a 64.22, como mandaba la tabla
del §7 de la v5 (D-V4): con la fuente afuera, el calor del cajón es la salida
del ladrillo, 56.23 W entregados a las cargas más 7.99 perdidos convirtiendo
dentro. guarda_potencia_vigente() cruza la copia contra
ladrillo_budget.calor_del_cajon_w() y no contra la suma de la v4, y sale
_reparto_del_cajon(): el reparto entre recinto y cajón era de la v4, y en la
v5 no hay recinto.
EOF
```

---

### Tarea 2: El plano neutro, en el budget y con su cuenta a mano

**Ficheros:**
- Modificar `case/clearance_budget.py`: se añaden `_plano_neutro()` y `autocomprobacion_plano_neutro()`, y la llamada en `main()`.
- Modificar `case/cad/persiana.py`: se va `plano_neutro()`, y `salto()` usa la del budget.

**Interfaces:**
- Produce `_plano_neutro(huecos: list[tuple[float, float]]) -> tuple[float, float]`, que devuelve `(yn, S)` en mm y mm^2.5. La consumen la Tarea 3 y `persiana.salto()`.

- [ ] **Paso 1: la cuenta a mano primero**

En `clearance_budget.py`, justo después de `autocomprobacion_anillo()`:

```python
def autocomprobacion_plano_neutro() -> None:
    """El plano neutro, a mano. Mismo patron que autocomprobacion_anillo(): la
    cuenta primero, la funcion despues.

    Una entrada de 3 a y = 0 y una salida de 4 a y = 25: el plano iguala
    3 sqrt(yn) = 4 sqrt(25 - yn), o sea 9 yn = 16 (25 - yn), yn = 16, y
    S = 4 sqrt(9) = 12. Es la cuenta en serie con la que el case conto su aire
    hasta el 2026-10-12: a_ef = 3 x 4 / sqrt(3^2 + 4^2) = 2.4, y
    a_ef sqrt(h) = 2.4 x 5 = 12. Con otra salida de 1 a y = 20, por encima
    del plano, sale mas aire: el plano sube y S crece."""
    yn, s = _plano_neutro([(0.0, 3.0), (25.0, 4.0)])
    assert abs(yn - 16.0) < 1e-9, f"plano neutro a {yn}, a mano 16"
    assert abs(s - 12.0) < 1e-9, f"S = {s}, a mano 12"
    yn3, s3 = _plano_neutro([(0.0, 3.0), (25.0, 4.0), (20.0, 1.0)])
    assert 16.0 < yn3 < 20.0 and s3 > 12.0, (
        f"con una salida mas el plano queda en {yn3:.3f} y S en {s3:.3f}: tenia "
        f"que subir de 16 sin pasar la salida nueva, y S que crecer de 12")
```

En `main()`, debajo de `autocomprobacion_anillo()`, añadir `autocomprobacion_plano_neutro()`.

- [ ] **Paso 2: verla fallar**

```bash
cd case && python -c "import clearance_budget as cb; cb.autocomprobacion_plano_neutro()"; cd ..
```

Esperado: `NameError: name '_plano_neutro' is not defined`.

- [ ] **Paso 3: la función**

En `clearance_budget.py`, justo antes de `def _tiro(`:

```python
def _plano_neutro(huecos: list[tuple[float, float]]) -> tuple[float, float]:
    """El plano neutro de una caja con huecos (y, area), en mm y mm2: la altura
    yn donde lo que entra por debajo iguala lo que sale por encima. La presion
    de flotabilidad es lineal en la altura, asi que el caudal de cada hueco va
    con a * sqrt(|y - yn|), y yn es la raiz de

        suma(a sqrt(yn - y), los de abajo) = suma(a sqrt(y - yn), los de arriba)

    Devuelve (yn, S), con S la suma de arriba en mm^2.5. La diferencia crece
    con yn y es continua --cada hueco pasa de salir a entrar por cero--, asi
    que la biseccion no salta. Vivio en case/cad/persiana.py hasta el
    2026-10-12."""
    def sobra(yn: float) -> float:
        return (sum(a * math.sqrt(yn - y) for y, a in huecos if y < yn)
                - sum(a * math.sqrt(y - yn) for y, a in huecos if y > yn))
    lo, hi = min(y for y, _ in huecos), max(y for y, _ in huecos)
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if sobra(mid) > 0 else (mid, hi)
    yn = (lo + hi) / 2
    return yn, sum(a * math.sqrt(y - yn) for y, a in huecos if y > yn)
```

En `case/cad/persiana.py`, borrar `plano_neutro()` y cambiar la primera línea de `salto()` por `yn, S = cb._plano_neutro(huecos)                   # S en mm^2.5`.

- [ ] **Paso 4: verde, y las cifras de la persiana iguales**

```bash
cd case && python -c "import clearance_budget as cb; cb.autocomprobacion_plano_neutro(); print('ok')"; cd ..
PYTHONIOENCODING=utf-8 python case/cad/persiana.py > $S/persiana_2.txt 2>&1; diff $S/persiana_0.txt $S/persiana_2.txt && echo IGUAL
PYTHONIOENCODING=utf-8 python case/clearance_budget.py > $S/budget_2.txt 2>&1; echo "exit $?"; diff $S/budget_1.txt $S/budget_2.txt && echo IGUAL
python -m ruff check case/
```

Esperado: `ok`, los dos `IGUAL`, `exit 2` y `ruff` limpio.

- [ ] **Paso 5: commit**

```bash
git add case/clearance_budget.py case/cad/persiana.py
git commit -F - <<'EOF'
El plano neutro vive en el budget, con su cuenta a mano

_plano_neutro() pasa de persiana.py a clearance_budget.py, que es donde está
la puerta del aire. autocomprobacion_plano_neutro() la fija con una entrada de
3 y una salida de 4 a 25 mm, que dan yn = 16 y S = 12 exactos: la misma cifra
que la cuenta en serie, y con una salida más el plano sube y S crece.
persiana.py la usa en vez de la suya y sus cifras no cambian.
EOF
```

---

### Tarea 3: La chimenea con las persianas, y `guarda_aire()` vuelve a juzgar

**Ficheros:**
- Modificar `case/clearance_budget.py`:
  - nuevas `T_SALA_DISENO_K`, `_respira_persiana()` y `_huecos()`;
  - `_tiro()` y `guarda_aire()` reescritas;
  - el bloque del aire de `canario_techo()`.
- Modificar `case/cad/persiana.py`: se van `salto()`, `huecos_case()`, `autocomprobacion()` y `ESCENARIOS`. Su `__main__` imprime los escenarios con `cb._tiro()`.
- Modificar `hardware/01-power-supply/v4/test_calor_budget.py`: `test_el_area_base_es_la_que_el_case_tiene_hoy()`.

**Interfaces:**
- Consume `_plano_neutro()` (Tarea 2) y `_potencia_del_cajon()` (Tarea 1).
- Produce:
  - `_huecos(p, costados: int = 2, trasera: bool = True) -> list[tuple[float, float]]`;
  - `_tiro(p, cd=CD_TIRO, costados: int = 2, trasera: bool = True) -> dict`, con las claves `huecos`, `yn`, `S`, `k`, `a_entra`, `a_sale`, `p_evacuada`, `p_pared`, `dt` y `falta`. Se van `a_ef`, `a_ef_techo`, `a_ef_techo_pared`, `h`, `a_ent`, `a_sal` y sus parientes.

- [ ] **Paso 1: el canario nuevo primero**

En `canario_techo()`, sustituir desde `    n_huecos = len(_HUECOS)` hasta `    del _HUECOS[n_huecos:]`, ambas incluidas:

```python
    n_huecos = len(_HUECOS)
    with contextlib.redirect_stdout(sordo):
        guarda_rebaje_chapa(dict(p))          # y con los parametros buenos, verde
        guarda_tramo_trasero(dict(p))
        guarda_rendija(dict(p))
        guarda_aire(dict(p))
    # LA PUERTA DEL AIRE VUELVE A JUZGAR (2026-10-12), y tiene que morder por su
    # razon. Un 5 % por encima de lo que la chimenea evacua al techo el salto
    # pasa del techo (va con la potencia a la 2/3): derivado de la chimenea, no
    # escrito a mano.
    t = _tiro(p)
    roja = round(t["p_evacuada"] * 1.05, 2)
    try:
        with contextlib.redirect_stdout(sordo):
            guarda_aire({**p, "potencia_disipada": roja})
    except AssertionError as e:
        assert "sobre ambiente" in str(e), (
            f"canario del aire: con {roja} W guarda_aire() salto, pero por otra "
            f"razon ('{str(e)[:80]}...')")
    else:
        raise AssertionError(
            f"canario del aire NO disparo: con {roja} W dentro y "
            f"{t['p_evacuada']:.1f} evacuables al techo, guarda_aire() lo deja "
            f"pasar -- no confiar en su VERDE")
    # LOS HUECOS DEL AIRE MIRAN LA CARGA, por los dos lados: con la de hoy, un
    # costado tapado no pasa y se publica; con 1 W todo cabe y nada se publica.
    # Un hueco que se publica siempre no avisa de nada y no se apagaria nunca.
    assert any("holgura de los costados" in h for h in _HUECOS[n_huecos:]), (
        f"canario del aire: con {p['potencia_disipada']:.2f} W y un costado "
        f"tapado el case sube {_tiro(p, costados=1)['dt']:.1f} K, y guarda_aire() "
        f"NO publico el hueco de los costados -- su silencio no vale")
    n_verde = len(_HUECOS)
    with contextlib.redirect_stdout(sordo):
        guarda_aire({**p, "potencia_disipada": 1.0})
    assert len(_HUECOS) == n_verde, (
        f"canario del aire: con 1 W guarda_aire() sigue publicando "
        f"'{_HUECOS[-1][:60]}...' -- un hueco que no mira la carga no avisa de "
        f"nada y no se apagaria nunca")
    # Y QUE LA CHIMENEA VEA LO QUE HAY: tapar un costado, acortar el paso de la
    # persiana (si la cache devolviera las franjas de otra geometria, esto no
    # se moveria) y ahogar la rendija con una tira casi continua suben el salto.
    assert _tiro(p, costados=1)["dt"] > t["dt"] + 1.0, (
        f"canario del aire: con un costado tapado el salto no sube de "
        f"{t['dt']:.1f} K -- _tiro() no esta mirando las persianas")
    otro_paso = _tiro({**p, "paso_persiana": p["paso_persiana"] - 1.0})
    assert otro_paso["dt"] > t["dt"] + 0.5, (
        f"canario del aire: con la persiana a paso {p['paso_persiana'] - 1.0:g} "
        f"el salto da {otro_paso['dt']:.2f} K contra {t['dt']:.2f} -- la chimenea "
        f"no ve la geometria de la persiana")
    ahogado = _tiro({**p, "taco_largo": 89.0})
    assert ahogado["dt"] > t["dt"] + 0.1, (
        f"canario del aire: con los tacos vueltos una tira de 89 mm la rendija "
        f"se ahoga y el salto no sube ({ahogado['dt']:.2f} contra "
        f"{t['dt']:.2f} K) -- _tiro() no esta mirando la rendija")
    del _HUECOS[n_huecos:]
```

- [ ] **Paso 2: verlo fallar con la chimenea de agosto**

```bash
cd case && PYTHONIOENCODING=utf-8 python -c "import clearance_budget as cb; cb.canario_techo(cb.leer_params())" 2>&1 | tail -1; cd ..
```

Esperado: `AssertionError: canario del aire NO disparo: con 20.37 W dentro y 19.4 evacuables al techo…`. La puerta de hoy publica un HUECO y no juzga. La cifra exacta sale de la chimenea de agosto: se acepta cualquier «NO disparo» con la `p_evacuada` de entonces.

- [ ] **Paso 3: la chimenea con el plano neutro**

En `clearance_budget.py`, debajo de `U_PARED_W_M2K = 3.0`:

```python
# LA SALA DE DISENO de la spec del chasis (sec.3.1): 45 C. El case cuenta su
# aire con T_AMB = 20 C. Con la densidad y la temperatura del aire de la sala,
# el salto va con la temperatura absoluta: k va con rho / sqrt(T), rho con 1/T,
# y dT con k^(-2/3). Cual de las dos es la sala del case no esta firmado:
# guarda_aire() imprime las dos y publica el HUECO si el pesimista no pasa.
T_SALA_DISENO_K = 318.0
```

Sustituir `_tiro()` entera, y poner delante sus dos ayudantes:

```python
@functools.lru_cache(maxsize=8)
def _respira_persiana(clave: tuple) -> tuple[tuple[float, float], ...]:
    """Las franjas por las que respira UNA persiana, como (y, area) cada 2 mm:
    lo que atraviesa detras de la ventana real del anillo (persiana.py,
    geometria()["abierto"]).

    EN CACHE POR LA TUPLA ENTERA DE LOS PARAMETROS: la geometria de shapely
    tarda medio segundo y canario_techo() pide la chimenea varias veces. La
    clave no se recorta a las cotas de la persiana a proposito: una lista de
    claves escrita a mano se queda vieja el dia que la persiana lea una cota
    nueva.

    EL IMPORT ES DIFERIDO A PROPOSITO: persiana.py importa este modulo al
    cargarse, asi que a nivel de modulo seria un ciclo."""
    import os
    import sys
    cad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad")
    if cad not in sys.path:
        sys.path.insert(0, cad)
    import persiana
    return tuple(persiana.franjas(persiana.geometria(dict(clave))["abierto"]))


def _huecos(p: dict[str, float], costados: int = 2,
            trasera: bool = True) -> list[tuple[float, float]]:
    """Cada hueco por el que respira el case, como (y, area) en mm y mm2: las
    franjas de las persianas por cada costado libre, y las tres aberturas de la
    trasera --la rejilla baja, la rendija del alero y las dos ondas--."""
    hs = ([(y, a * costados) for y, a in _respira_persiana(tuple(sorted(p.items())))]
          if costados else [])
    if trasera:
        _n, _largo, a_ent, y_ent = _rejilla_entrada(p)
        a_ren, y_ren = _rendija(p)
        a_ond, y_ond = _ondas_trasera(p)
        hs += [(y_ent, a_ent), (y_ren, a_ren), (y_ond, a_ond)]
    return hs


def _tiro(p: dict[str, float], cd: float = CD_TIRO, costados: int = 2,
          trasera: bool = True) -> dict:
    """La chimenea del case: el plano neutro, lo que entra y lo que sale, el
    salto termico y lo que evacua al techo.

        P = k dT^1.5,   k = rho cp C_D sqrt(2 g / T) S

    con S la suma de a sqrt(y - yn) de los huecos de arriba (_plano_neutro()).

    FUE EN SERIE HASTA EL 2026-10-12: una entrada y una salida, A_ef^-2 =
    A_in^-2 + A_out^-2, y el tiro entre sus centroides. Con una entrada y una
    salida las dos cuentas son la misma (autocomprobacion_plano_neutro()); con
    las persianas no, porque su ventana es ancha abajo y una cuna arriba y cada
    franja entra o sale segun su altura. El modelo H/4-3H/4 de la piel, que
    ponia la entrada a un cuarto del alto y la salida a tres cuartos, daba un
    tiro mayor que este (papel de la persiana, sec.5).

    SALIO DE guarda_aire() EL 2026-09-03 para que canario_techo() pudiera leer
    los NUMEROS y no el mensaje de la puerta.

    `falta` es el factor por el que hay que multiplicar el area de TODAS las
    aberturas, a las mismas alturas, para quedarse en el techo: escalarlas
    todas no mueve el plano neutro, asi que S y k crecen con ese mismo
    factor."""
    hs = _huecos(p, costados, trasera)
    yn, s = _plano_neutro(hs)
    k = (RHO_AIRE * CP_AIRE * cd * math.sqrt(2 * G / T_AMB)
         * s * 1e-6 * math.sqrt(1e-3))
    techo = p["salto_termico_max"]
    p_evacuada = k * techo ** 1.5
    return {"huecos": hs, "yn": yn, "S": s, "k": k,
            "a_entra": sum(a for y, a in hs if y < yn),
            "a_sale": sum(a for y, a in hs if y > yn),
            "p_evacuada": p_evacuada,
            "p_pared": U_PARED_W_M2K * _envolvente_m2(p) * techo,
            "dt": (p["potencia_disipada"] / k) ** (2.0 / 3.0),
            "falta": p["potencia_disipada"] / p_evacuada}
```

- [ ] **Paso 4: la puerta vuelve a juzgar**

En el docstring de `guarda_aire()`, después del párrafo que acaba en «esta puerta se pone verde sola.», añadir:

```
    Y EL 2026-10-12 VUELVE A SER UN ASERTO. El venteo esta dibujado --las
    dos persianas, papel de la persiana sec.5-- y la potencia es la de la
    fuente v5, con la fuente afuera. Con C_D = 0.65 el case sube 16.9 K
    contra 20, y la puerta juzga con ese C_D (papel sec.5.5): el pesimista es
    la prueba de robustez y se imprime. Un costado contra una pared no pasa,
    y eso es una condicion de uso (PLIEGO sec.7), con su HUECO hasta que el
    arranque mida cuanta holgura hace falta. La sala de 45 C de la spec del
    chasis se imprime tambien, y publica su HUECO mientras no se decida.
```

Sustituir el cuerpo entero de `guarda_aire()` (de `t = _tiro(p)` hasta el final de la función):

```python
    _n, largo_ent, _a, _y = _rejilla_entrada(p)
    assert largo_ent >= 4 * p["vent_ancho_ranura"], (
        f"la rejilla de entrada mide {largo_ent:.1f} mm de largo con "
        f"ranuras de {p['vent_ancho_ranura']:.2f}: deja de leerse como campo y "
        f"pasa a rayitas (es la misma cuenta que recorto la espina del valle)")
    t = _tiro(p)
    techo = p["salto_termico_max"]
    print(f"aire: plano neutro a {t['yn']:.0f} mm; por debajo entran "
          f"{t['a_entra']:.0f} mm2 y por encima salen {t['a_sale']:.0f}, en "
          f"{len(t['huecos'])} huecos: las franjas de las dos persianas, la "
          f"rejilla baja de la trasera, la rendija del alero y las ondas")
    print(f"  {t['dt']:.1f} K sobre ambiente con {p['potencia_disipada']:.2f} W "
          f"(techo {techo:.0f}; esta chimenea evacua {t['p_evacuada']:.1f} W a "
          f"ese techo). SUPUESTO: C_D={CD_TIRO}, aire a {T_AMB - 273.15:.0f} C")
    assert t["dt"] <= techo + 1e-9, (
        f"el case sube {t['dt']:.1f} K sobre ambiente con "
        f"{p['potencia_disipada']:.2f} W y el techo es {techo:g}: esta chimenea "
        f"evacua {t['p_evacuada']:.1f} W a ese techo. Hace falta un "
        f"{100 * (t['falta'] - 1):.0f} % mas de area en todas las aberturas, a "
        f"las mismas alturas, o salidas mas altas: el tiro va con la RAIZ de la "
        f"altura")
    t_p = _tiro(p, CD_TIRO_PESIMISTA)
    print(f"  aviso: con C_D={CD_TIRO_PESIMISTA} (rendija bajo alero, no chapa "
          f"ranurada) serian {t_p['dt']:.1f} K. Sin medir hasta el ensayo")
    f_sala = T_SALA_DISENO_K / T_AMB
    print(f"  aviso: con la sala a {T_SALA_DISENO_K - 273.15:.0f} C de la spec "
          f"del chasis serian {t['dt'] * f_sala:.1f} K, y "
          f"{t_p['dt'] * f_sala:.1f} con el pesimista")
    if t_p["dt"] * f_sala > techo + 1e-9:
        _HUECOS.append(
            f"la sala de diseno del case sin decidir: con la de la spec del "
            f"chasis ({T_SALA_DISENO_K - 273.15:.0f} C) el case sube "
            f"{t['dt'] * f_sala:.1f} K, y {t_p['dt'] * f_sala:.1f} con el C_D "
            f"pesimista contra un techo de {techo:.0f}. La puerta juzga con "
            f"{T_AMB - 273.15:.0f} C; cual es la sala del case lo decide Samuel")
    print(f"  aviso: la envolvente exterior ({_envolvente_m2(p):.3f} m2, sin el "
          f"suelo) se lleva otros {t['p_pared']:.1f} W a ese techo con "
          f"U={U_PARED_W_M2K} W/m2K (SUPUESTO); no entra en el veredicto")
    t_1 = _tiro(p, costados=1)
    print(f"  con un costado tapado (contra una pared): {t_1['dt']:.1f} K")
    if t_1["dt"] > techo + 1e-9:
        _HUECOS.append(
            f"la holgura de los costados sin medir: con un costado tapado el "
            f"case sube {t_1['dt']:.1f} K con {p['potencia_disipada']:.2f} W y "
            f"el techo es {techo:.0f}. Los dos tienen que quedar libres (PLIEGO "
            f"sec.7); cuanta holgura hace falta a cada lado se mide en el "
            f"arranque (papel de la persiana, HUECO 4)")
```

- [ ] **Paso 5: el canario en verde; el contrato de la v4 en rojo**

```bash
cd case && PYTHONIOENCODING=utf-8 python -c "import clearance_budget as cb; p = cb.leer_params(); cb.canario_techo(p); cb.guarda_aire(p); print('VERDE')"; cd ..
PYTHONIOENCODING=utf-8 python hardware/01-power-supply/v4/calor_budget.py 2>&1 | tail -3
```

Esperado:
- El canario y la puerta en verde, y `aire: plano neutro a 85 mm …`, `16.9 K sobre ambiente con 64.22 W (techo 20; esta chimenea evacua 82.9 W …)`, el pesimista en 18.9 y la sala de 45 °C en 18.3 / 20.5.
- `calor_budget.py` en rojo con `KeyError: 'a_ef'` dentro de `test_el_area_base_es_la_que_el_case_tiene_hoy`. Es el rojo que pide el paso siguiente.

- [ ] **Paso 6: la base de la v4 se queda en la v4**

En `hardware/01-power-supply/v4/test_calor_budget.py`, sustituir la función entera:

```python
def test_el_area_base_es_la_que_el_case_tiene_hoy() -> None:
    """A_EF_BASE_MM2 es la base de la v4: el venteo del case SIN las aberturas
    de D-F3, con la cuenta en serie de este modelo --una entrada y una salida,
    a_ef^-2 = a_ent^-2 + a_sal^-2--. Se recalcula aqui desde params.scad con
    las tres aberturas de la trasera, asi que si el case cambia su rejilla, su
    rendija o sus ondas y nadie mueve esta constante, la copia se ve vieja.

    DESDE EL 2026-10-12 el case cuenta su aire con el plano neutro y las dos
    persianas, que SON las aberturas de D-F3 (clearance_budget._tiro()). Esta
    base no lo sigue a proposito: describe la v4, que no se monta (D-V4), y su
    relevo es el de la v5, cuyo sec.7 reabre este modelo entero. Vive en el
    contrato y no en el modulo: un assert a nivel de modulo convertiria un
    cambio de geometria del case en un rojo del import de media tanda."""
    import math  # noqa: PLC0415
    import clearance_budget as cl  # noqa: PLC0415

    p = cl.leer_params()
    _n, _largo, a_ent, _y = cl._rejilla_entrada(p)
    a_sal = cl._rendija(p)[0] + cl._ondas_trasera(p)[0]
    a_ef = 1.0 / math.sqrt(1 / a_ent ** 2 + 1 / a_sal ** 2)
    assert abs(a_ef - cb.A_EF_BASE_MM2) < 1.0, (
        f"el case tiene hoy {a_ef:.1f} mm2 de venteo efectivo sin las "
        f"persianas y calor_budget.A_EF_BASE_MM2 dice {cb.A_EF_BASE_MM2:.1f}. "
        f"Esa base es a la que la fuente le SUMA su area_venteo_mm2: con ella "
        f"vieja, el venteo minimo que publica sale de una geometria que ya no "
        f"existe")
```

- [ ] **Paso 7: `persiana.py` imprime con la puerta**

En `case/cad/persiana.py`:
- Borrar `salto()`, `huecos_case()`, `autocomprobacion()` y la constante `ESCENARIOS`. En `__main__`, borrar la llamada `autocomprobacion(p)`.
- En el docstring del módulo, sustituir el párrafo que empieza por «EL AIRE: plano neutro.» por:

```
EL AIRE lo cuenta desde el 2026-10-12 clearance_budget._tiro(), que es la
puerta, con el plano neutro: cada hueco a su altura, y por debajo del plano
entra y por encima sale. De aqui sale lo que respira cada persiana (franjas()
sobre geometria()["abierto"]); abajo se imprimen los escenarios del papel.
```

- En `__main__`, sustituir desde `    print("\nEL AIRE (plano neutro; …` hasta el bucle de «con 64,2 W, pesimista» incluido:

```python
    print("\nEL AIRE (clearance_budget._tiro(): plano neutro; las persianas, la "
          "rejilla de la trasera, la rendija del alero y las ondas)")
    print(f"  {'escenario':36s} {'W':>7s} {'C_D puerta':>11s} {'pesimista':>10s} {'techo':>6s}")
    w5 = p["potencia_disipada"]
    for nombre, W in (("v5 declarada, fuente afuera", w5),
                      ("fuente adentro (v5 + 25,02)", w5 + 25.02),
                      ("v4, que no se monta", 147.31)):
        q = {**p, "potencia_disipada": W}
        dt, dtp = cb._tiro(q)["dt"], cb._tiro(q, cb.CD_TIRO_PESIMISTA)["dt"]
        print(f"  {nombre:36s} {W:7.2f} {dt:9.1f} K {dtp:8.1f} K {p['salto_termico_max']:4.0f} K"
              f"{'' if dtp <= p['salto_termico_max'] else '   <- NO pasa el pesimista'}")
    print(f"  (plano neutro a {cb._tiro(p)['yn']:.0f} mm)")
    print(f"\n  con {w5:.2f} W, pesimista:")
    for nombre, kw in (("las dos persianas solas", {"trasera": False}),
                       ("un costado tapado (contra una pared)", {"costados": 1}),
                       ("sin persianas: el case de agosto", {"costados": 0})):
        print(f"    {nombre:38s} {cb._tiro(p, cb.CD_TIRO_PESIMISTA, **kw)['dt']:5.1f} K")
```

- [ ] **Paso 8: todo verde, y las cifras del papel**

```bash
PYTHONIOENCODING=utf-8 python hardware/01-power-supply/v4/calor_budget.py > $S/calor_budget_3.txt 2>&1; echo "exit $?"; diff $S/calor_budget_0.txt $S/calor_budget_3.txt && echo IGUAL
PYTHONIOENCODING=utf-8 python case/cad/persiana.py 2>&1 | sed -n '/EL AIRE/,$p'
PYTHONIOENCODING=utf-8 python case/clearance_budget.py > $S/budget_3.txt 2>&1; echo "exit $?"; diff $S/budget_2.txt $S/budget_3.txt
PYTHONIOENCODING=utf-8 python case/check_dxf.py 2>&1 | tail -1
python -m ruff check case/ hardware/01-power-supply/v4/
```

Esperado:
- `calor_budget.py`, con el exit de la Tarea 0 e `IGUAL`.
- `persiana.py`, con las cifras del §5 del papel:

| escenario | `C_D` de la puerta | pesimista |
|---|---|---|
| v5 declarada, fuente afuera | 16,9 K | 18,9 K |
| fuente adentro | 21,0 K | 23,5 K |
| v4 | 29,4 K | 32,8 K |

  y, con el pesimista, 22,7 K las persianas solas, 26,0 K un costado tapado y unos 52 K sin persianas (el papel dice 51,9 porque lo calculó con 64,2 W).
- El budget, con `exit 2`. En el diff:
  - las líneas del aire nuevas;
  - el HUECO del venteo desaparece;
  - aparecen dos HUECOS: el de la holgura de los costados (23,3 K) y el de la sala de diseño (20,5 K pesimista).
- `check_dxf`, en VERDE; `ruff`, limpio.

- [ ] **Paso 9: commit**

```bash
git add case/clearance_budget.py case/cad/persiana.py hardware/01-power-supply/v4/test_calor_budget.py
git commit -F - <<'EOF'
El aire del case se cuenta con el plano neutro y las dos persianas, y guarda_aire() vuelve a juzgar

_tiro() deja la cuenta en serie (una entrada y una salida a sus centroides)
y cuenta cada hueco a su altura: las franjas que respiran de las dos persianas,
que calcula persiana.py, más la rejilla baja de la trasera, la rendija del
alero y las ondas. Con la potencia de la v5 el case sube 16.9 K con C_D 0.65
(18.9 con el pesimista) contra un techo de 20, y guarda_aire() vuelve a ser
un aserto en vez de publicar el déficit como HUECO.

Quedan dos HUECOS que miran la carga. Con un costado contra una pared el case
sube 23.3 K (PLIEGO §7; la holgura se mide en el arranque). Y con la sala de
45 °C de la spec del chasis, que no está decidida para el case, serían 18.3 K
y 20.5 con el pesimista. canario_techo() prueba que la puerta muerde con un 5 %
más de lo que la chimenea evacua, que los dos HUECOS se callan con 1 W, y que
tapar un costado, acortar el paso de la persiana o ahogar la rendija suben el
salto.

La base de calor_budget.py se queda en la de la v4: el case sin las aberturas
de D-F3, con su cuenta en serie. Su contrato la recalcula desde la rejilla,
la rendija y las ondas.
EOF
```

---

### Tarea 4: El papel y los comentarios que hablan del aire

**Ficheros:**
- `docs/superpowers/specs/2026-10-11-case-persiana-design.md`
- `docs/superpowers/specs/2026-09-05-fuente-v5-ladrillo-design.md`
- `case/README.md`
- `case/cad/params.scad`
- `hardware/01-power-supply/v4/calor_budget.py`
- `hardware/02-midi-cv/power_budget.py`

**Interfaces:** ninguna. Solo cambian textos; ninguna cifra que lea una puerta.

- [ ] **Paso 1: las dos specs**

En el papel de la persiana, al final del §5 (antes del `---` que abre el §6):

```
> **Aplicado el 2026-10-12 (plan del aire, `docs/superpowers/plans/2026-10-11-aire-plano-neutro.md`):**
> `potencia_disipada` = 64,22 W de la v5, `_tiro()` cuenta con el plano neutro y
> las dos persianas, y `guarda_aire()` vuelve a juzgar con `C_D` = 0,65: 16,9 K,
> 18,9 con el pesimista. La fila de la v4 de la tabla es la de antes. Con la sala
> de 45 °C de la spec del chasis serían 18,3 y 20,5 K: la puerta lo publica como
> HUECO hasta que se decida la sala del case.
```

En la v5, debajo de la tabla del §7:

```
> **Aplicado el 2026-10-12 (plan del aire, #289):** `params.scad::potencia_disipada`
> = 64,22, y `guarda_potencia_vigente()` la cruza contra
> `ladrillo_budget.calor_del_cajon_w()`. `calor_budget.py` sigue siendo el modelo
> de la v4: lo reabre el relevo de esta v5, no el plan del aire. En sus términos
> (en serie, 105 mm de tiro) la persiana equivale a 10 776 mm² más de venteo, y la
> v4 pedía 20 907.
```

- [ ] **Paso 2: el README del case**

En el bloque de estado de arriba, sustituir «Lo siguiente es la tira de muestra (#398) y el aire contado con el plano neutro (#289).» por «El aire se cuenta con el plano neutro y la potencia de la v5: 16,9 K sobre la sala con las dos persianas, contra un techo de 20 (#289). Lo siguiente es la tira de muestra (#398).» Respeta el ajuste de líneas del bloque `>`.

Al final del párrafo de `guarda_aire()` que acaba en «…y vive en **#289**, no en esta puerta.», añadir:

```
**Desde el 2026-10-12 la puerta vuelve a juzgar**: con la fuente v5 afuera
(64,22 W) y el aire contado con el plano neutro y las dos persianas, el case sube
16,9 K contra 20. Lo que queda abierto son dos HUECOS: la holgura de los
costados y la sala de diseño del case.
```

- [ ] **Paso 3: los comentarios de `params.scad`**

En el párrafo que acaba en «La obra que lo cierra es del papel del case (#289).», añadir debajo `// La cerro la persiana con la fuente v5: ver el parrafo del 2026-10-12, abajo.`.

En el bloque `// LO QUE ESTE CAMBIO NO HACE: no cierra el #289. …`, añadir debajo `// Lo cerro el 2026-10-12 el plan del aire: la fuente v5 afuera y las persianas.`.

- [ ] **Paso 4: los comentarios de la cadena de la v4**

En `hardware/01-power-supply/v4/calor_budget.py`:
- Al final del comentario de `A_EF_BASE_MM2`, que acaba en «…que es un dato y no un defecto.», añadir:

  ```python
  # Las aberturas de D-F3 son las persianas del case (2026-10-11), y esta base
  # no las sigue a proposito: es la v4, que no se monta (D-V4). Ver
  # test_el_area_base_es_la_que_el_case_tiene_hoy().
  ```

- En `ESTIMADOS`, sustituir `"P_BASE area: hipotesis para #289; el papel del case fija la real",` por `"P_BASE area: el venteo nuevo que la v4 pide al case; el case respira por las persianas para la v5 (#289)",`.
- En `P_BASE`, sustituir `# ESTIMADO - hipotesis para #289, el papel del case fija la real.` por `# ESTIMADO - el venteo nuevo que la v4 pide al case. El case dibujo el suyo para la v5 (#289), y en los terminos de este modelo a la v4 no le alcanza.`.

En `hardware/02-midi-cv/power_budget.py`, en el comentario «LO QUE ESTE NUMERO ARRASTRA», sustituir «o sea de una obra que el papel del case todavia no ha dibujado (D-F3 = A, issue #289).» por «o sea de la obra que la v4 le pedia al case (D-F3 = A). El case dibujo la suya para la v5 --las persianas, #289-- y este modelo, que es el de la v4, no la sigue: ver calor_budget.A_EF_BASE_MM2.». Respeta el ajuste de líneas.

- [ ] **Paso 5: comprobar que nada que lea una puerta cambió**

```bash
for g in hardware/01-power-supply/v4/calor_budget.py hardware/02-midi-cv/power_budget.py hardware/01-power-supply/v4/check_bringup.py; do
  PYTHONIOENCODING=utf-8 python $g > $S/$(basename $g .py)_4.txt 2>&1; echo "$g exit $?"
  diff $S/$(basename $g .py)_0.txt $S/$(basename $g .py)_4.txt; done
grep -rn "lo que lee hoy guarda_aire\|hipotesis para #289\|todavia no ha dibujado" case/ hardware/ docs/superpowers/specs/2026-10-11-case-persiana-design.md
python -m ruff check .
```

Esperado:
- Los tres, con el exit de la Tarea 0. El único diff es la línea de `ESTIMADOS` que imprime `calor_budget.py`.
- El `grep`, sin resultados fuera de la fila de la tabla del papel, que se conserva como historia bajo su enmienda.
- `ruff`, limpio.

- [ ] **Paso 6: commit**

```bash
git add docs/superpowers/specs/2026-10-11-case-persiana-design.md docs/superpowers/specs/2026-09-05-fuente-v5-ladrillo-design.md case/README.md case/cad/params.scad hardware/01-power-supply/v4/calor_budget.py hardware/02-midi-cv/power_budget.py
git commit -F - <<'EOF'
El papel dice que el aire ya se juzga: las enmiendas de la persiana y de la v5, el README y los comentarios de la cadena de la v4

El §5 de la persiana y el §7 de la v5 llevan su línea de «aplicado», con las
cifras de la puerta (16.9 K, 18.9 con el pesimista) y la sala de 45 °C como
decisión abierta. El README del case deja de dar el aire por pendiente. En
calor_budget.py y power_budget.py, lo que decía que el case aún no había
dibujado su venteo dice ahora que lo dibujó para la v5 y que el modelo de la
v4 no lo sigue.
EOF
```

---

### Tarea 5: Puertas, revisión, PR, merge y el #289

**Ficheros:** ninguno nuevo.

- [ ] **Paso 1: las puertas enteras**

```bash
sh .githooks/pre-push < /dev/null 2>&1 | tail -12
git log --format=%B origin/main..HEAD | grep -ci "co-authored\|generated with"
```

Esperado: `PUERTAS EN VERDE` y `0`.

- [ ] **Paso 2: revisión de la rama entera** con un revisor de contexto limpio (opus). Le da el rango `origin/main..HEAD`, este plan, el §5 del papel de la persiana y la lista «Lo que más puede morder». Lo Crítico y lo Importante se arregla con TDD en una pasada; lo Menor va a un issue.

- [ ] **Paso 3: PR y merge**

El cuerpo dice en llano qué cambia:
- la potencia de la v5;
- el plano neutro con las persianas;
- la puerta que vuelve a juzgar, con 16,9 K;
- los dos HUECOS que quedan;
- que la cadena de la v4 se queda como base de la v4.

Sin líneas de atribución. Merge con merge commit (`gh pr merge --merge`), como el resto del repo.

- [ ] **Paso 4: cerrar el #289 a mano**, con la comparación entre lo previsto y lo encontrado, casilla por casilla:
  - **El presupuesto de aire nuevo:** lo dio la persiana, no el techo ni la trasera.
  - **`guarda_aire()` en verde:** sí, con la potencia de la v5 (64,22 W) en vez de los 149 W del issue.
  - **La franja de 230 V:** sale de la caja con la v5.
  - **El polvo:** sigue siendo el precio declarado de D-F3 = A, sin filtro.
  - **`chasis_toroide_*` y la segunda placa:** son de la v4; los recoge su relevo.
  - **La spec del chasis:** también es de la v4.
  - **`T_AMB`:** se imprime, y la sala del case queda como HUECO para Samuel.

- [ ] **Paso 5: memoria.** `el-monje-de-shikoku.md` gana una línea con el PR y lo que queda abierto.

---

## Autorrevisión

- **Cobertura del papel:**
  - §5.4: la enmienda y `guarda_potencia_vigente()` → Tarea 1; `_tiro()` con el plano neutro y las persianas → Tareas 2 y 3.
  - La cadena del §5.4:
    - `calor_budget.py` (`A_EF_BASE_MM2` y `P_BASE`) → Tarea 3 (el contrato) y Tarea 4 (los comentarios);
    - `test_calor_budget.py` → Tarea 3;
    - `TECHO_VENTEO_MM2` → Tarea 4 (el comentario) y Tareas 1, 3 y 4 (corrido, sin cambio de número);
    - `medidas.csv` y `check_bringup.py` → Tareas 1 y 4 (corridos, sin cambio: decisión 1);
    - `canario_techo()` → Tarea 3.
  - §5.3, la condición de uso: el PLIEGO §7 ya la lleva; el HUECO 4 se publica → Tarea 3.
  - §5.5, la puerta juzga con 0,65 → Tarea 3.
  - §13.4 → Tarea 3.
  - §14, el orden: el plan va detrás de la persiana mergeada (#412).
  - El detalle de `T_AMB` del #289 → Tarea 3, como aviso y HUECO (decisión 2).
- **Sin marcadores:** cada paso trae su código o su texto. Los dos únicos sitios donde el ejecutor elige son el ajuste de líneas de dos textos (Tarea 4, pasos 2 y 4), y la cifra exacta del rojo de la Tarea 3, paso 2, que depende de la chimenea de agosto.
- **Nombres:**
  - `_plano_neutro` → Tareas 2 y 3.
  - `_huecos`, `_respira_persiana` y `_tiro` (con `costados` y `trasera`) → Tarea 3, y los usa `persiana.py` en el paso 7.
  - Las claves de `_tiro()` que leen `guarda_aire()` y `canario_techo()` son todas del paso 3.
  - El HUECO de la Tarea 1 lee `a_ef`, `a_ef_techo`, `a_ef_techo_pared` y `h` de la `_tiro()` vieja, que sigue viva hasta el paso 3 de la Tarea 3; el paso 4 lo sustituye.
- **Lo que más puede morder:** los cinco puntos tienen su comprobación en la Tarea 3 (canario) o en la Tarea 1 (el import).
