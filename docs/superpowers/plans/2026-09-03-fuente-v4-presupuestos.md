# La fuente v4, tanda A: los presupuestos que dimensionan — plan de implementación

> **Para quien lo ejecute:** SUB-SKILL REQUERIDA: `superpowers:subagent-driven-development`
> (recomendada) o `superpowers:executing-plans`, tarea por tarea. Los pasos llevan
> casillas (`- [ ]`). **Cada tarea es TDD: primero la aserción en rojo —el canario
> con su mutación, pegado en el informe—, después el número que la pone verde.**

**Objetivo:** que las nueve piezas que la fuente v4 todavía no puede comprar —el
sostenido del rack, el fusible, la NTC, el LC, las ferritas, los umbrales del
detector de ventana, los Y2, el SCR del crowbar y los conectores— salgan de un
guion ejecutable y no de una tabla en prosa. Al final de esta tanda, **la columna
«sostenido» de §1 del papel está rellena y el listón se vuelve a firmar**, y la
placa R se puede dibujar sin inventar un solo valor.

**Arquitectura:** nueve presupuestos nuevos y cinco enmendados, todos en el patrón
del repo —un `.py` con docstring que argumenta, constantes con su fuente inline,
aserciones ejecutables y un canario que las ve morder—. Corren solos por el glob de
`hardware/tools/gates.py` (`hardware/**/*_budget.py`): **añadir un presupuesto es
escribir el fichero, no tocar la lista**. Dos módulos compartidos nacen para que las
entradas no se copien: `hardware/tools/canario.py` (la mutación por bisección, hoy
privada del case) y `hardware/01-power-supply/v4/curvas.py` (lo que las hojas dicen
en sus gráficas, leído una vez).

**Tech stack:** Python 3 pelado (sin dependencias nuevas: `math`, `dataclasses`,
`csv`). Nada de KiCad ni ngspice en esta tanda — ninguna tarea de aquí necesita
`pcbnew`, y eso es a propósito: los números tienen que existir **antes** que la
placa. `pymupdf` solo como herramienta de lectura de las hojas, nunca importada por
un presupuesto.

**Papel:** `docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md` (v3,
firmada). El plan argumenta desde el papel; quien ejecute lee los dos. Las
decisiones firmadas que lo gobiernan son **D-F1** (listón de placa), **D-F2**
(telemetría de rack poblada), **D-F3 = A** (recinto y cajón ventilados por
convección natural, sin ventilador), **D-F4** (secuenciador), **D-F5** (Y2 de modo
común) y **D-F6** (crowbar de rack).

---

## Lo que esta tanda NO hace, y por qué en este orden

| No entra | Por qué espera |
|---|---|
| La placa **R** (KiCad, esquema, PCB, fab) | Lleva el fusible, la NTC, el LC, los umbrales del detector, el SCR y los conectores. **Los nueve valores salen de esta tanda.** Dibujarla antes es dibujar hipótesis. |
| La placa **C** | Es la v3 menos la red (papel §8); su cambio depende de `margen_budget.py` y del cableado del ON/OFF, que es la Tarea 10. |
| El **bus board de invitados** (#169) | Su PTC por slot depende del censo de §4.3 y del sostenido de la Tarea 3. |
| El **case ventilado** (D-F3 = A: techo, trasera, rejillas nuevas) | Es papel propio. Lo que esta tanda le entrega es la **exigencia numérica**: `guarda_aire()` con los 120 W del cajón (Tarea 4). Hoy esa puerta pasa con 9,22 W, y con la carga real no pasa: ese rojo es el encargo del papel del case. |
| El **papel de la bahía** | Recibe dos requisitos de §10; el mecanismo del diferencial es suyo. |
| **D-R1** (el 1,8 V) | §11 del papel. Aquí solo su calor, como carga declarada de `calor_budget.py`. |

**El orden interno no es negociable:** `curvas.py` → `calor_budget.py` → todo lo
demás. Tres presupuestos (`power_budget.py`, `invitados_budget.py` y la re-firma del
listón) importan el sostenido, y sin él nacen verdes por vacíos, que es el Principio
VIII incumplido en su forma más cómoda.

---

## Las entradas que hoy no están en el árbol

Ninguna tarea puede inventar un número. Lo que falta, con quién lo consigue:

| Qué | Para | Estado |
|---|---|---|
| Curvas de derating, p. 3 de las cuatro hojas IRM | `calor_budget.py` | **En el árbol**, sin leer con los ojos → **Tarea 2** |
| Curvas de PSRR: LM2941 Fig. 9, LM2991 Fig. 8, LT3045, LT3094 | `rizado_budget.py`, `margen_budget.py` | **En el árbol**, sin leer con los ojos → **Tarea 2** |
| «EMI testing of component power supplies», Mean Well | `fuga_budget.py`, D-F5 | **Falta.** `meanwell.com/Upload/PDF/EMI_statement_en.pdf` |
| Cifra de fuga de **IEC 62368-1** para Clase I enchufable | `fuga_budget.py` | **Falta.** Es norma de pago: si no se consigue el texto, se declara HUECO con el valor de trabajo y su origen citado, nunca un número redondo sin fuente |
| Hoja del **fusible** elegido, con su curva I²t | `fusible_budget.py` | **Falta.** Depende de la talla que salga; la hoja se baja **después** del cálculo permanente y **antes** de cerrar la tarea |
| Hoja de **Ametherm SL22** (o la talla que salga) | `fusible_budget.py` | **Falta** |

> **Si una hoja no baja a la segunda intentona, se le pide a Samuel** y la tarea se
> queda en rojo declarado, no se completa con un número plausible. Un HUECO honesto
> es del Principio V; un número inventado con cara de hoja ya costó una v2 entera.

---

## Restricciones globales

Copiadas del papel y de la constitución. Valen para **todas** las tareas.

- **Ningún número sin fuente inline.** Cada constante lleva en su línea o encima de
  dónde sale: hoja y página, sección del papel, o `ESTIMADO` / `HUECO` con el motivo.
  Los `ESTIMADO` se imprimen al final del guion, contados.
- **Cada aserción nueva se ve morder, y por bisección, no a mano.** El canario usa
  `borde_rojo()` (Tarea 1): busca el valor que hace saltar la guarda **por el texto
  de su mensaje**. Dos valores frontera elegidos a ojo pasan con y sin la guarda; un
  barrido, no.
- **Puerta por los dos lados.** Todo parámetro nuevo que se asevera lleva **cota
  inferior y superior**, o se dice explícitamente por qué solo tiene una. Un radio
  con solo mínimo deja pasar el infinito.
- **`ESTIMADO` no es `HUECO`.** `ESTIMADO` es un número con razonamiento y sin hoja;
  `HUECO` es la ausencia de número. Los dos se imprimen; solo el segundo bloquea.
- **Sin acentos en identificadores ni en mensajes de aserción**, como el resto de
  `hardware/`: los mensajes salen por consolas que no siempre son UTF-8.
- **Ninguna dependencia nueva.** Python de la biblioteca estándar.
- **Nada que necesite `pcbnew` ni `ngspice`** en esta tanda (`gates.py` los marcaría
  HUECO en una máquina sin KiCad, y estos números tienen que correr en cualquiera).
- **El listón, en todo momento**: ultra 650 mA/riel; rack 3,8 / 2,5 / 4,0 A **de
  placa**; digital 8,0 A de placa. Sostenido es **otra** columna y solo la escribe
  `calor_budget.py`.
- **Ambiente de diseño: 45 °C de sala**, no 25 (spec del chasis §3.1). Cualquier
  guion que escriba 25 está midiendo otro instrumento.
- **El instrumento y los invitados no se prestan corriente** (papel §1). Lo único
  compartido es la masa.
- **Commit por tarea**, con el cuerpo diciendo qué número nuevo existe y de qué hoja
  salió. Mensajes en español, sin acentos en la primera línea.

---

## Mapa de archivos

Todo lo nuevo de la fuente vive en `hardware/01-power-supply/v4/`, que **no existe
todavía**; la v3 se queda intacta salvo el guion que muere (Tarea 12).

| Fichero | Responsabilidad | Tarea |
|---|---|---|
| `hardware/tools/canario.py` | `borde_rojo()`: la mutación por bisección, compartida | 1 |
| `hardware/01-power-supply/v4/curvas.py` | lo que dicen las gráficas de las hojas, leído una vez | 2 |
| `hardware/01-power-supply/v4/calor_budget.py` | la cadena térmica de §6 → **el sostenido** | 3 |
| `case/clearance_budget.py` | `guarda_aire()` con los 120 W del cajón y D-F3 | 4 |
| `hardware/02-midi-cv/power_budget.py` | techo = sostenido de `PS6` | 5 |
| `hardware/03-vco/consumo_total_budget.py` | sin `RESERVA_INVITADOS` | 5 |
| `hardware/01-power-supply/v4/invitados_budget.py` | placa vs. declarado vs. sostenido vs. censo | 6 |
| `hardware/01-power-supply/v4/fusible_budget.py` | permanente, I²t frío, **rearranque caliente** | 7 |
| `hardware/01-power-supply/v4/rizado_budget.py` | LC × PSRR a 65 kHz y a 1–20 MHz | 8 |
| `hardware/01-power-supply/v4/margen_budget.py` | lo que le llega a `U1`/`U2` contra su dropout | 9 |
| `hardware/01-power-supply/v4/secuencia_budget.py` | los umbrales del detector de ventana (D-F4) | 10 |
| `hardware/01-power-supply/v4/fuga_budget.py` | seis fugas + los Y2 de D-F5 contra la norma | 11 |
| `hardware/01-power-supply/v4/check_absmax.py` | OVP de los IRM contra los máximos de lo que alimentan | 12 |
| `hardware/01-power-supply/v3/valle_budget.py` | **se borra** (no hay valle) | 12 |
| `hardware/bus-board/ground_budget.py` | I × R_retorno con N patches | 13 |
| `hardware/01-power-supply/v4/check_bringup.py`, `medidas.csv` | el bring-up de §9.1 | 14 |
| Los papeles de §10 | las enmiendas prometidas | 15 |

---

### Tarea 1: `canario.py` — la mutación deja de ser privada del case

**Por qué primero:** nueve presupuestos nuevos van a necesitar ver morder sus
aserciones. `_borde_rojo()` ya existe, resuelto y bien argumentado, dentro de
`case/clearance_budget.py:2842` — y su propio docstring cuenta que nació porque
**cuatro canarios escritos a mano dejaron de morder en un solo día**. Copiarlo nueve
veces reproduce exactamente ese fallo, multiplicado.

**Files:**
- Create: `hardware/tools/canario.py`
- Modify: `case/clearance_budget.py` (borra `_borde_rojo`, importa `borde_rojo`)

**Interfaces:**
- Produce: `borde_rojo(guarda, p: dict, clave: str, lo: float, hi: float, texto: str, pasos: int = 24) -> float`
  — devuelve el valor de `p[clave]` con el que `guarda(p)` salta por `AssertionError`
  cuyo mensaje contiene `texto`; levanta `AssertionError` si en todo `[lo, hi]` no
  hay ninguno.
- Consume: nada.

- [ ] **Step 1: el test que falla porque el módulo no existe**

Crea `hardware/tools/test_canario.py`:

```python
"""El canario del canario: que borde_rojo() encuentra bordes y avisa si no hay."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from canario import borde_rojo


def _guarda_de_juguete(p):
    assert p["x"] <= 10.0, f"x se pasa de 10: {p['x']:.2f} (texto que muerde)"


def test_encuentra_el_borde():
    v = borde_rojo(_guarda_de_juguete, {"x": 1.0}, "x", 0.0, 100.0, "texto que muerde")
    assert 10.0 <= v <= 10.5, f"el borde esta en 10, no en {v}"


def test_avisa_si_el_aserto_no_muerde():
    try:
        borde_rojo(_guarda_de_juguete, {"x": 1.0}, "x", 0.0, 9.0, "texto que muerde")
    except AssertionError as e:
        assert "no hay ningun valor" in str(e)
    else:
        raise AssertionError("tenia que quejarse: en [0, 9] la guarda nunca salta")


def test_no_confunde_un_aserto_con_otro():
    try:
        borde_rojo(_guarda_de_juguete, {"x": 1.0}, "x", 0.0, 100.0, "otro texto")
    except AssertionError as e:
        assert "no hay ningun valor" in str(e)
    else:
        raise AssertionError(
            "un canario que acepta CUALQUIER AssertionError deja de distinguir "
            "el aserto que vigila del que se rompio de camino")


if __name__ == "__main__":
    test_encuentra_el_borde()
    test_avisa_si_el_aserto_no_muerde()
    test_no_confunde_un_aserto_con_otro()
    print("OK: canario.py")
```

- [ ] **Step 2: correrlo y verlo fallar**

```
python hardware/tools/test_canario.py
```

Esperado: `ModuleNotFoundError: No module named 'canario'`.

- [ ] **Step 3: crear `hardware/tools/canario.py`**

Mueve el cuerpo de `_borde_rojo` de `case/clearance_budget.py:2842` **sin cambiar la
lógica** — solo el nombre (sin guion bajo) y el docstring, que gana una línea diciendo
de dónde viene:

```python
"""La mutacion de una guarda, buscada por biseccion en vez de escrita a mano.

Vivia en case/clearance_budget.py, privada, desde el 2026-08-30. Sale aqui
porque la fuente v4 estrena nueve presupuestos y cada uno necesita ver morder
sus asertos: nueve copias de esta funcion son nueve sitios donde el numero
frontera se queda viejo, que es EXACTAMENTE el fallo del que nacio.
"""
from __future__ import annotations

import contextlib
import io


def borde_rojo(guarda, p: dict[str, float], clave: str, lo: float, hi: float,
               texto: str, pasos: int = 24) -> float:
    """El valor de `clave` con el que `guarda` salta POR `texto`, buscado.

    Un canario dice "este aserto muerde, y por SU texto"; para eso no hace
    falta saber DONDE muerde, solo que hay un sitio. Se busca por biseccion
    entre lo y hi, y si no lo encuentra el canario falla -- que es exactamente
    lo que tiene que pasar si un aserto se quedo sin dientes.

    Devuelve el valor rojo; levanta AssertionError si en todo el rango no hay
    ninguno que salte por ese texto."""
    def salta(v: float) -> bool:
        roto = dict(p)
        roto[clave] = v
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                guarda(roto)
        except AssertionError as e:
            return texto in str(e)
        except Exception:                       # noqa: BLE001
            return False
        return False

    if salta(hi):
        a, b = lo, hi
    elif salta(lo):
        a, b = hi, lo
    else:
        raise AssertionError(
            f"canario: en {clave} entre {lo:g} y {hi:g} no hay ningun valor que "
            f"haga saltar a {guarda.__name__}() por '{texto}'. O el aserto se "
            f"quedo sin dientes, o su texto cambio y nadie actualizo el canario")
    for _ in range(pasos):                      # b salta, a no
        m = (a + b) / 2.0
        if salta(m):
            b = m
        else:
            a = m
    return b
```

> **Copia el cuerpo del fichero real, no éste.** Si `case/clearance_budget.py:2842`
> difiere de lo de arriba (el bucle final, el número de pasos), **manda el fichero**:
> esta tarea mueve código probado, no lo reescribe de memoria.

- [ ] **Step 4: correr el test, verlo verde**

```
python hardware/tools/test_canario.py
```

Esperado: `OK: canario.py`.

- [ ] **Step 5: que el case lo importe y no tenga el suyo**

En `case/clearance_budget.py`: borra la definición de `_borde_rojo` y añade, junto a
los demás imports:

```python
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "hardware", "tools"))
from canario import borde_rojo as _borde_rojo          # noqa: E402
```

El alias `_borde_rojo` conserva las ~10 llamadas de los canarios sin tocarlas. Si
`clearance_budget.py` ya importa `contextlib` o `io` **solo** para esta función,
quítalos y deja que `pyflakes` lo confirme.

- [ ] **Step 6: la puerta del case sigue verde**

```
python case/clearance_budget.py
```

Esperado: pasa entero, con los mismos canarios y los mismos números que antes del
cambio (tarda ~35 s, es el guion más lento del repo). **Pega el resumen final en el
informe:** si un canario cambia de valor, el movimiento no fue neutro y hay que
mirarlo antes de seguir.

- [ ] **Step 7: commit**

```bash
git add hardware/tools/canario.py hardware/tools/test_canario.py case/clearance_budget.py
git commit -m "La mutacion por biseccion sale del case y se vuelve herramienta"
```

---

### Tarea 2: `curvas.py` — lo que las hojas dicen en sus gráficas

**Por qué:** las curvas **no salen por extracción de texto**. La v1 de este papel
declaró HUECO cuatro cosas que estaban dibujadas en la p. 3, y con ellas el listón
pasó de «cabe» a «se sostiene al 17 %». Cada número de este fichero se lee **mirando
la página**, y lleva escrito en su línea de qué hoja y de qué figura sale.

**Files:**
- Create: `hardware/01-power-supply/v4/curvas.py`
- Create: `hardware/01-power-supply/v4/README.md` (dos párrafos: qué es la v4, qué
  vive aquí, y que la v3 no se pide)

**Interfaces:**
- Produce:
  - `derating(t_amb_c: float, familia: str) -> float` — fracción de la potencia de
    placa disponible (0…1) a esa temperatura de aire, para `"generico"` (salidas de
    12/15 V) o `"salida5v"` (las de 5 V, que quiebran antes).
  - `PSRR_DB: dict[tuple[str, float], float]` — clave `(pieza, frecuencia_hz)`,
    valor dB. Piezas: `"LM2941"`, `"LM2991"`, `"LT3045"`, `"LT3094"`.
  - `psrr_db(pieza: str, f_hz: float) -> float` — interpola en log(f) entre los
    puntos leídos, y **levanta `ValueError` fuera del rango leído** en vez de
    extrapolar.
- Consume: `canario.borde_rojo` (para su autocomprobación).

- [ ] **Step 1: renderizar las páginas y leerlas con los ojos**

`pymupdf` está instalado; no hay `pdftoppm`. Saca las páginas a PNG en el
scratchpad (**no** al árbol: son derivados de hojas que ya están versionadas):

```python
# scratchpad/render.py
import fitz, os
D = "docs/reference/datasheets/"
OUT = os.environ["SCRATCH"]          # el scratchpad de la sesion
PAGS = [("meanwell-irm-15-spec-2025-11-21.pdf", 2),
        ("meanwell-irm-20-spec-2025-11-21.pdf", 2),
        ("meanwell-irm-30-spec-2026-04-03.pdf", 2),
        ("meanwell-irm-45-spec-2025-11-21.pdf", 2),
        ("lm2941-snvs770i-2015-01.pdf", None),      # Fig. 9: buscar la pagina
        ("lm2991-snvs099i-2016-10.pdf", None),      # Fig. 8
        ("lt3045-rev-d.pdf", None),
        ("lt3094-rev-b.pdf", None)]
for f, p in PAGS:
    d = fitz.open(D + f)
    paginas = [p] if p is not None else range(min(12, d.page_count))
    for i in paginas:
        d[i].get_pixmap(dpi=200).save(f"{OUT}/{f[:-4]}-p{i+1}.png")
        print(f"{f} p{i+1}")
```

Después **abre cada PNG y léelo**. De las IRM necesitas: la temperatura del codo, la
pendiente en %/°C, la temperatura donde acaba, y si la curva de las salidas de 5 V es
distinta. De los reguladores: PSRR en dB a 65 kHz, y a 1, 5, 10 y 20 MHz.

- [ ] **Step 2: escribir el fichero con lo leído, y el test en rojo**

Empieza por la autocomprobación, que es lo que fija el contrato:

```python
def _autocomprobacion() -> None:
    # el codo: por debajo no se derratea nada
    assert derating(25.0, "generico") == 1.0
    assert derating(T_CODO, "generico") == 1.0
    # la pendiente: a mitad de camino, la mitad del recorte
    medio = (T_CODO + T_FIN) / 2.0
    assert abs(derating(medio, "generico") - (1.0 + FRAC_FIN) / 2.0) < 1e-9, (
        "la recta de derating no pasa por su punto medio: revisa la pendiente")
    # las salidas de 5 V quiebran ANTES, y eso es lo que hunde a PS5 y PS6
    assert derating(50.0, "salida5v") < derating(50.0, "generico"), (
        "si las dos familias dan lo mismo a 50 C, la de 5 V no se leyo: la "
        "hoja las dibuja distintas y esa diferencia es la que decide PS6")
    # por los dos lados: no se extrapola por arriba ni por abajo
    assert derating(200.0, "generico") == FRAC_FIN, (
        "por encima del final de la curva se devuelve el ultimo valor leido, "
        "nunca una recta que siga bajando hasta negativo")
    # PSRR: dentro del rango interpola, fuera se queja
    assert psrr_db("LT3045", 65e3) > psrr_db("LT3045", 10e6), (
        "el PSRR de un LDO CAE con la frecuencia: si sube, los puntos estan "
        "al reves")
    for pieza in ("LM2941", "LM2991", "LT3045", "LT3094"):
        try:
            psrr_db(pieza, 1e9)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"{pieza}: a 1 GHz no hay hoja que leer. Extrapolar el PSRR "
                f"fuera de su grafica es inventarse el numero que decide si el "
                f"riel de 0,8 uV existe")
```

- [ ] **Step 3: correrlo, verlo fallar**

```
python hardware/01-power-supply/v4/curvas.py
```

Esperado: `NameError` / `ModuleNotFoundError` — el fichero aún no tiene las
funciones.

- [ ] **Step 4: escribir las constantes y las dos funciones**

Esqueleto; **los números los pones de la lectura del Step 1**, no de aquí. Los que
van escritos abajo son los que el papel §6 ya cita, y sirven de comparación: si tu
lectura difiere, manda tu lectura y **dilo en el informe** — que el papel y la hoja
no coincidan es un hallazgo, no un detalle.

```python
"""Lo que las hojas dicen en sus GRAFICAS, leido con los ojos una sola vez.

Ninguna de estas cifras sale por extraccion de texto. La v1 del papel de la
fuente v4 declaro HUECO cuatro cosas que estaban dibujadas en la pagina 3, y
con ellas el liston paso de "cabe" a "se sostiene al 17 %". Este fichero
existe para que la proxima lectura no vuelva a hacerse, y para que cualquiera
pueda comprobarla abriendo la pagina que cada linea cita.

    python curvas.py        (imprime las dos curvas y se autocomprueba)
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "tools"))
from canario import borde_rojo                             # noqa: E402

# --- la curva de derating de los IRM -------------------------------------
# Mean Well IRM-15/20/30/45, p. 3 "DERATING CURVE", leida 2026-09-__.
# Las cuatro hojas dibujan la misma forma; lo que cambia entre familias es
# donde empieza a caer la salida de 5 V.
T_CODO = 50.0            # C de aire. Hasta aqui, 100 % de la potencia de placa
T_FIN = 70.0             # C de aire. Aqui acaba la curva publicada
FRAC_FIN = 0.50          # fraccion de placa disponible a T_FIN
T_CODO_5V = 45.0         # las salidas de 5 V quiebran antes (papel sec.6)

def derating(t_amb_c: float, familia: str = "generico") -> float:
    """Fraccion de la potencia de placa disponible a esa temperatura de AIRE.

    El aire es el que rodea al modulo, no el de la sala: la cadena que lleva
    de uno a otro es de calor_budget.py, no de aqui."""
    codo = T_CODO_5V if familia == "salida5v" else T_CODO
    if t_amb_c <= codo:
        return 1.0
    if t_amb_c >= T_FIN:
        return FRAC_FIN                 # no se extrapola por debajo del final
    pend = (1.0 - FRAC_FIN) / (T_FIN - codo)
    return 1.0 - pend * (t_amb_c - codo)

# --- PSRR de la cascada ---------------------------------------------------
# dB de rechazo. Leidos de: LM2941 SNVS770I Fig. 9; LM2991 SNVS099I Fig. 8;
# LT3045 Rev. D y LT3094 Rev. B, sus figuras de PSRR vs frecuencia.
# Los 65 kHz son la conmutacion de los IRM (diagrama de bloques, p. 3); el
# tramo de 1-20 MHz es el de los FLANCOS, que es donde un LDO ya no rechaza
# y por eso hay ferritas.
PSRR_DB = {
    ("LM2941", 65e3): 0.0,      # <-- LEER
    ("LM2941", 1e6): 0.0,
    # ... los cuatro, con al menos 65 kHz, 1 MHz, 10 MHz y el ultimo publicado
}

def psrr_db(pieza: str, f_hz: float) -> float:
    """Interpola en log(f) entre los puntos LEIDOS. Fuera del rango, se queja."""
    pts = sorted((f, db) for (p, f), db in PSRR_DB.items() if p == pieza)
    if not pts:
        raise ValueError(f"{pieza}: no hay puntos de PSRR leidos")
    if f_hz < pts[0][0] or f_hz > pts[-1][0]:
        raise ValueError(
            f"{pieza}: {f_hz:.3g} Hz esta fuera de la grafica leida "
            f"({pts[0][0]:.3g}-{pts[-1][0]:.3g} Hz). Extrapolar el PSRR es "
            f"inventar el numero que decide si el riel ultra existe")
    for (f0, d0), (f1, d1) in zip(pts, pts[1:]):
        if f0 <= f_hz <= f1:
            if f1 == f0:
                return d0
            k = (math.log10(f_hz) - math.log10(f0)) / (math.log10(f1) - math.log10(f0))
            return d0 + k * (d1 - d0)
    return pts[-1][1]
```

- [ ] **Step 5: correr y ver verde**

```
python hardware/01-power-supply/v4/curvas.py
```

Esperado: imprime las dos curvas y `OK`. **Pega la salida en el informe**, y con ella
las cuatro temperaturas de codo que leíste: son la entrada de la Tarea 3.

- [ ] **Step 6: commit**

```bash
git add hardware/01-power-supply/v4/curvas.py hardware/01-power-supply/v4/README.md
git commit -m "Las curvas de las hojas, leidas con los ojos y en un guion"
```

---

### Tarea 3: `calor_budget.py` — la cadena de §6, y el sostenido

**Por qué:** es el guion que este papel debe y el dueño de techo de #151. Devuelve la
columna que hoy está vacía. Todo lo que viene después lo importa.

**Files:**
- Create: `hardware/01-power-supply/v4/calor_budget.py`

**Interfaces:**
- Consume: `curvas.derating`.
- Produce:
  - `aire_recinto_c(p_recinto_w: float, p_cajon_w: float, t_sala_c: float = 45.0) -> float`
  - `sostenido_a(riel: str, t_aire_c: float) -> float` — amperios sostenidos por
    riel: `"rack+12"`, `"rack-12"`, `"rack+5"`, `"digital+5"`.
  - `SOSTENIDO: dict[str, float]` — la tabla ya evaluada en el punto de diseño
    (recinto ventilado, D-F3 = A), que es lo que `power_budget.py` e
    `invitados_budget.py` importan.

- [ ] **Step 1: la aserción en rojo — la cadena entera, con su testigo**

```python
def _autocomprobacion() -> None:
    # 1. La cadena SUBE. Un modelo que devuelve el aire de la sala no modela nada.
    t_cerrado = aire_recinto_c(P_RECINTO_MAX, P_CAJON_MAX, area_venteo_mm2=0.0)
    assert t_cerrado > T_SALA, "el recinto no puede estar mas frio que la sala"

    # 2. El caso que la junta calculo, reproducido: recinto CERRADO con los
    #    120 W de fila y digital en el cajon da ~78 C de aire y hunde el rack
    #    al 17 % de placa. Si este guion no lo reproduce, no modela lo que
    #    decidio D-F3 y su recomendacion se quedo sin apoyo.
    assert 70.0 <= t_cerrado <= 86.0, (
        f"cerrado y con el cajon cargado la junta estimo ~78 C de aire y este "
        f"modelo da {t_cerrado:.1f}. Si difiere tanto, uno de los dos esta mal "
        f"y hay que saber cual ANTES de firmar un sostenido")

    # 3. VENTILADO (D-F3 = A) tiene que dar MAS corriente que cerrado. Es toda
    #    la razon de ser de la decision: si no, se firmo una obra por nada.
    t_vent = aire_recinto_c(P_RECINTO_MAX, P_CAJON_MAX, area_venteo_mm2=AREA_VENTEO)
    assert t_vent < t_cerrado - 5.0, (
        f"ventilar baja el aire de {t_cerrado:.1f} a {t_vent:.1f} C: menos de "
        f"5 K de mejora no justifica reabrir el techo y la trasera del case, y "
        f"D-F3 = A habria que volver a mirarla")

    # 4. Los dos lados de la puerta. Por arriba: el sostenido nunca supera la
    #    placa -- un derating que devuelve mas del 100 % es un signo cambiado.
    for riel, placa in PLACA_A.items():
        s = sostenido_a(riel, t_vent)
        assert 0.0 < s <= placa + 1e-9, (
            f"{riel}: sostenido {s:.2f} A contra {placa:.2f} de placa. Fuera "
            f"de (0, placa] el modelo se rompio")

    # 5. El aserto que de verdad decide, y el que tiene que morder: el rack
    #    ventilado tiene que quedar POR ENCIMA de la PSU3, que es el liston.
    assert sostenido_a("rack+12", t_vent) >= PSU3_A["rack+12"], (
        f"el rack sostenido se queda en {sostenido_a('rack+12', t_vent):.2f} A "
        f"contra los {PSU3_A['rack+12']:.1f} de la A-100PSU3: con D-F3 = A "
        f"firmada, el liston SIGUE sin existir y hay que volver a Samuel")

    # 6. Y el canario: que ese aserto muerde de verdad, buscado por biseccion.
    v = borde_rojo(_guarda_liston, dict(P_BASE), "area_venteo_mm2",
                   0.0, 100000.0, "SIGUE sin existir")
    print(f"  canario: por debajo de {v:.0f} mm2 de venteo el liston no existe")
```

- [ ] **Step 2: correr y ver fallar**

```
python hardware/01-power-supply/v4/calor_budget.py
```

Esperado: `NameError: name 'aire_recinto_c' is not defined`.

- [ ] **Step 3: escribir el modelo**

La cadena, tal como §6 la escribe, en cuatro tramos y **cada uno con su fuente**:

```python
"""La cadena termica de la fuente v4, de la sala al silicio, y lo que sale de
ella: la corriente SOSTENIDA de cada riel. Es la columna que la sec.1 del papel
tiene vacia, y el dueno de techo del #151.

    python calor_budget.py

## Por que existe

Una corriente sostenible no es propiedad de un modulo: lo es de la terna
(modulo, recinto, ambiente). El liston se firmo el 2026-09-03 en corriente DE
PLACA -- 3,8 / 2,5 / 4,0 A de rack-- y la v1 del papel lo llamo "superior a la
A-100PSU3" sin mirar donde iba a vivir. La PSU3 entrega sus 2 A en un case
ABIERTO, al aire de la sala; estos IRM entregan lo que su curva de derating
diga al aire que haya dentro de una caja de acero.

Con el recinto cerrado y los 120 W de fila y digital dentro del cajon, la junta
estimo ~78 C de aire y un rack sostenido de 0,63 A: por debajo de la PSU3, y en
el peor caso por debajo de la propia v3. Samuel firmo D-F3 = A el 2026-09-03
--ventilar recinto y cajon por conveccion natural, sin ventilador-- y este
guion es el que dice cuanto compro esa decision.

## Lo que este modelo NO cubre

  * **El coeficiente de descarga del venteo.** Igual que guarda_aire() del case,
    C_D es un supuesto y no una medida. Por eso el sostenido que sale de aqui es
    una PREDICCION, y el paso 7 del bring-up es lo que la vuelve una cifra.
  * **La conduccion por el encapsulado a la chapa** (papel sec.12.7): si un IRM
    puede tirar calor por su cara, este modelo lo esta ignorando y va a favor de
    seguridad.
  * **El transitorio.** Aqui todo es regimen permanente. Un pico de dos minutos
    no lo ve.
"""
```

Constantes, todas con su origen:

```python
T_SALA = 45.0            # C. spec del chasis sec.3.1: la habitacion para la que
                         # se dimensiono TODO lo demas. NO 25 -- la v1 de este
                         # papel uso 25 y le salieron 49 C donde hay 78.
AREA_RECINTO_M2 = 0.1453     # spec del chasis sec.3.1
H_CONV_W_M2K = 9.0           # ibid., conveccion natural sobre acero

# Las fuentes de calor, del papel sec.6 (rendimientos ya corregidos de sec.3):
P_RECINTO_TIP = 7.2      # W, instrumento a censo, digital a 3,0 A, rack vacio
P_RECINTO_MAX = 28.9     # W, todo a placa a la vez
P_CAJON_MAX = 120.3      # W: 95,6 de la fila de invitados + 24,7 del digital.
                         # guarda_aire() del case NO tiene hoy ni uno de estos.
P_1V8_MAX = 4.57         # W si el 1,8 V vive dentro (D-R1 sin decidir, sec.4.5)

PLACA_A = {"rack+12": 3.8, "rack-12": 2.5, "rack+5": 4.0, "digital+5": 8.0}
PSU3_A = {"rack+12": 2.0, "rack-12": 1.2, "rack+5": 4.0}   # doepfer.de, 03-09
FAMILIA = {"rack+12": "generico", "rack-12": "generico",
           "rack+5": "salida5v", "digital+5": "salida5v"}
```

El tramo de venteo usa **la misma física que `guarda_aire()`** —tiro de chimenea,
`P = k·dT^1.5`— porque es el mismo fenómeno y tenerlo en dos formas es tenerlo mal en
una: importa las constantes de `case/clearance_budget.py` (`RHO_AIRE`, `CP_AIRE`,
`CD_TIRO`, `G`) en vez de recopiarlas, y **usa `T_AMB` = 318 K, no 293**: el término
de flotabilidad va con la temperatura absoluta del aire, y la sala de diseño son
45 °C. Anota esa diferencia en el docstring; es un ~8 % de tiro y es un hallazgo
contra el fichero del case.

- [ ] **Step 4: correr y ver verde — o rojo del bueno**

```
python hardware/01-power-supply/v4/calor_budget.py
```

Dos desenlaces, y **los dos son resultado**:
- **Verde:** el rack ventilado queda por encima de la PSU3. Apunta los cuatro
  números de `SOSTENIDO`: son la columna «sostenido» de §1.
- **Rojo por el aserto 5:** ni ventilando existe el listón. **Eso no se arregla
  bajando el aserto.** Se para, se pega el número en el informe y vuelve a Samuel:
  es una decisión de listón, no un fallo de guion. (Ver la constitución sobre
  arreglar la fuente y no la regla.)

- [ ] **Step 5: rellenar la columna «sostenido» del papel §1**

Con los cuatro números, edita la tabla de §1 del papel y su nota al pie. **La fila
del ultra no cambia** (650 mA es del censo, no del derating).

- [ ] **Step 6: commit**

```bash
git add hardware/01-power-supply/v4/calor_budget.py docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md
git commit -m "El sostenido deja de ser una columna vacia: la cadena de la sala al silicio"
```

---

### Tarea 4: `guarda_aire()` — el cajón tiene 120 W que nadie contó

**Por qué:** el propio docstring de `_ondas_trasera()` lo confiesa: «potencia_disipada
son SOLO los reguladores del PSU. La disipación de los módulos no está en ningún
presupuesto de este repo». El case se cerró (techo macizo, trasera capturada) con
**9,22 W** en esa variable. D-F3 = A dice que respire; esta tarea es la que le pone
el número con el que tiene que respirar.

**Files:**
- Modify: `case/clearance_budget.py` (`guarda_aire()` y su canario en la lista de
  ~línea 3046)
- Modify: `case/params.scad` o donde viva `potencia_disipada` (búscalo: es el
  parámetro que `guarda_aire` lee de `p`)

**Interfaces:**
- Consume: `calor_budget.P_CAJON_MAX` (120,3 W) y `P_RECINTO_MAX` (28,9 W).
- Produce: nada nuevo; **cambia el veredicto** de una puerta existente.

- [ ] **Step 1: ver el rojo antes de tocar nada**

```
python case/clearance_budget.py
```

Anota el `dt` actual y el `potencia_disipada` con el que sale. Después, a mano:

```python
# en un python interactivo, con el modulo importado
p = dict(PARAMS); p["potencia_disipada"] = 149.2   # 28.9 del recinto + 120.3 del cajon
guarda_aire(p)
```

Esperado: **AssertionError**, «el case sube N K sobre ambiente… y el techo son 15».
**Pega ese número.** Es el encargo que esta tanda le entrega al papel del case.

- [ ] **Step 2: escribir la enmienda — el parámetro se parte en dos**

`potencia_disipada` deja de ser un número suelto y pasa a decir de dónde sale. En el
docstring de `guarda_aire()`, sustituye la confesión por la cuenta:

```
    LO QUE ESTE NUMERO CUENTA, desde 2026-09-03: los reguladores de la fuente
    (28,9 W a placa, papel de la fuente v4 sec.6) MAS lo que disipan la fila de
    invitados y el digital dentro del mismo cajon (95,6 + 24,7 = 120,3 W). Hasta
    hoy eran 9,22 W --solo los TO-220 de la v3-- y con eso el case se cerro el
    18-08. El liston de la PSU3 (D-F1) y D-F3 = A cambiaron las dos cosas: hay
    mas calor y hay que dejarlo salir.
```

Y el parámetro, con su desglose visible:

```python
POT_FUENTE_W = 28.9      # papel fuente v4 sec.6, todo a placa
POT_CAJON_W = 120.3      # ibid.: 95,6 de la fila de invitados + 24,7 del digital
```

- [ ] **Step 3: el canario que lo vigila por los dos lados**

En la lista de canarios (~línea 3046) el barrido ya existe con `9.22, 40.0`. Súbelo
al rango real y añade el lado que falta:

```python
(guarda_aire, {"potencia_disipada": _borde_rojo(
    guarda_aire, p, "potencia_disipada", 9.22, 400.0, "sobre ambiente")},
```

- [ ] **Step 4: correr, y dejar el rojo declarado**

```
python case/clearance_budget.py
```

**Esta puerta se queda ROJA a propósito hasta que el papel del case rediseñe el
venteo.** Es el resultado correcto: D-F3 = A es exactamente la obra que la pone
verde. En el informe: el `dt` que sale, el área de venteo que haría falta (despéjala
de `P = k·dT^1.5` con `dt = 15`), y la frase de que el desbloqueo es del papel del
case, no de esta tanda.

> Si dejar `gates.py` en rojo bloquea el merge de la tanda, **no bajes el techo ni
> el número**: marca la guarda con el `HUECO` explícito que `gates.py` sabe contar,
> citando la tarea del papel del case que lo cierra. Un rojo declarado es del
> Principio V; un techo subido para que pase es lo contrario.

- [ ] **Step 5: commit**

```bash
git add case/clearance_budget.py
git commit -m "El cajon tenia 120 W que ninguna puerta contaba"
```

---

### Tarea 5: los dos presupuestos que importan el sostenido

**Por qué:** `power_budget.py` del módulo 2 lleva escrito a mano `TECHO_W_PESIMISTA =
14.1`, derrateado «a 52,3 °C» con la aritmética vieja; y `consumo_total_budget.py`
del módulo 3 asevera una `RESERVA_INVITADOS ≥ 120 mA/riel` que existía **porque la
fila de abajo se alimentaba del riel del instrumento**. Con la v4 tiene rieles
propios: esa reserva ya no protege nada y, peor, gasta margen del instrumento en un
compromiso que otro riel cumple.

**Files:**
- Modify: `hardware/02-midi-cv/power_budget.py:92-93`
- Modify: `hardware/03-vco/consumo_total_budget.py` (la aserción de `reserva >= 120.0`
  y el bloque que la imprime)

- [ ] **Step 1: el rojo — que el techo deje de ser un literal**

En `power_budget.py`, sustituye el literal por la importación y **deja que falle**:

```python
sys.path.insert(0, os.path.join(DIR, "..", "01-power-supply", "v4"))
from calor_budget import SOSTENIDO                         # noqa: E402

TECHO_W_PESIMISTA = SOSTENIDO["digital+5"] * V_RIEL
TECHO_W_OPTIMISTA = TECHO_W_PESIMISTA * (14.5 / 14.1)   # la misma proporcion
                                                        # que tenia la v3
```

```
python hardware/02-midi-cv/power_budget.py
```

Esperado: o pasa con un techo **distinto**, o falla — y si falla, es información: con
8 A de placa el digital debería tener **más** techo que los 14,1 W de la IRM-15-5 de
la v3, no menos. Si sale menos, el sostenido de `PS6` es el hallazgo y va al informe.

- [ ] **Step 2: la aserción que ata el número a su origen**

```python
assert TECHO_W_PESIMISTA > 14.1, (
    f"el techo del +5 V digital sale {TECHO_W_PESIMISTA:.1f} W, y la IRM-15-5 "
    f"de la v3 ya daba 14,1. La v4 compro una IRM-45-5 de 8 A de placa: si "
    f"sostenido da MENOS, o el derating se leyo mal o el recinto no ventila")
assert LED_A_BLANCO_PLENO > TECHO_W_OPTIMISTA / V_RIEL, (
    "los LED a blanco pleno tienen que SEGUIR sin caber: el tope por firmware "
    "es lo que los sujeta y esta puerta es la que dice que hace falta")
```

La segunda ya existe en el fichero (~línea 488): **compruébala, no la dupliques.**

- [ ] **Step 3: `consumo_total_budget.py` — la reserva se retira con su motivo**

Borra la aserción `assert reserva >= 120.0` y el bloque que la imprime, y pon en su
sitio la explicación y la aserción que la sustituye:

```python
    # --- lo que E-4 pedia, y por que ya no se pide -------------------------
    # Hasta la fuente v3, la fila de abajo se alimentaba del riel del
    # instrumento y esta reserva era el unico sitio donde eso estaba escrito.
    # La v4 (D-F1, 2026-09-03) le da rieles PROPIOS -- 3,8 / 2,5 / 4,0 A de
    # placa desde PS3/PS4/PS5 -- y el instrumento deja de prestar un solo
    # miliamperio. Quien vigila la fila de abajo ahora es invitados_budget.py.
    print(f"\nreserva para invitados: NO APLICA desde la fuente v4. La fila de")
    print(f"  abajo tiene rieles propios (#169); ver invitados_budget.py.")
    print(f"  Margen del instrumento sobre su propio techo: {reserva:.0f} mA/riel")
    assert peor <= USABLE_MA, (
        f"el instrumento se pasa: {peor:.1f} contra {USABLE_MA:.0f} mA")
```

- [ ] **Step 4: correr las dos**

```
python hardware/02-midi-cv/power_budget.py
python hardware/03-vco/consumo_total_budget.py
```

Esperado: las dos verdes, con el techo del módulo 2 **citando a `calor_budget.py`** y
el módulo 3 sin reserva. Pega los dos resúmenes.

- [ ] **Step 5: commit**

```bash
git add hardware/02-midi-cv/power_budget.py hardware/03-vco/consumo_total_budget.py
git commit -m "El techo del digital y la reserva de invitados dejan de ser literales"
```

---

### Tarea 6: `invitados_budget.py` — cuatro columnas, y la que manda es la tercera

**Por qué:** el rack tiene ahora cuatro números distintos que se llaman «corriente» y
que **no son el mismo**: lo que la placa da, lo que el papel declara, lo que el calor
sostiene y lo que el censo de módulos pide. Sin un guion que los ponga en fila, el
que se cita en una conversación es el más grande.

**Files:**
- Create: `hardware/01-power-supply/v4/invitados_budget.py`

**Interfaces:**
- Consume: `calor_budget.SOSTENIDO`, `calor_budget.PLACA_A`, `calor_budget.PSU3_A`.
- Produce: `CENSO: tuple[Modulo, ...]` y `fila_peor_caso() -> dict[str, float]`.

- [ ] **Step 1: la aserción en rojo**

```python
def _autocomprobacion() -> None:
    # 1. El orden de las cuatro columnas no es opinable
    for riel in ("rack+12", "rack-12", "rack+5"):
        assert SOSTENIDO[riel] <= PLACA_A[riel], (
            f"{riel}: sostenido no puede superar la placa")

    # 2. El liston, dicho donde se puede comprobar: sostenido >= PSU3.
    #    Es la MISMA pregunta que calor_budget.py, hecha desde el otro lado
    #    -- alli desde el calor, aqui desde lo que se le promete al dueno.
    for riel, psu3 in PSU3_A.items():
        assert SOSTENIDO[riel] >= psu3, (
            f"{riel}: el instrumento promete {SOSTENIDO[riel]:.2f} A y la "
            f"A-100PSU3 da {psu3:.1f}. El liston firmado dice 'o superior'")

    # 3. Una fila de 104 HP del modulo mas glotron del censo tiene que caber
    #    EN PLACA (papel sec.4.3: cabe, y es lo que se compro) y hay que decir
    #    si cabe SOSTENIDA, que es otra cosa.
    peor = fila_peor_caso()
    assert peor["rack+12"] <= PLACA_A["rack+12"], (
        f"una fila entera del modulo mas glotron pide {peor['rack+12']:.2f} A "
        f"y la placa da {PLACA_A['rack+12']:.1f}: el liston se compro mal")

    # 4. Y el canario del que de verdad importa
    v = borde_rojo(_guarda_censo, {"mas_glotron_ma_por_hp": 28.6},
                   "mas_glotron_ma_por_hp", 1.0, 200.0, "no cabe sostenida")
    print(f"  canario: por encima de {v:.1f} mA/HP la fila no cabe sostenida")
```

- [ ] **Step 2: correr, ver fallar** (`ModuleNotFoundError` / `NameError`).

- [ ] **Step 3: el censo, con sus fuentes**

Los cuatro del papel §4.3, cada uno con dónde se leyó:

```python
@dataclass(frozen=True)
class Modulo:
    nombre: str
    hp: int
    ma_12p: float
    ma_12n: float
    ma_5: float
    fuente: str

CENSO = (
    Modulo("Doepfer A-101-1", 16, 30.0, 30.0, 0.0, "doepfer.de, leido 2026-09-03"),
    Modulo("Mutable Clouds", 18, 120.0, 10.0, 0.0, "mutable-instruments.net, ibid."),
    Modulo("Make Noise Morphagene", 20, 165.0, 65.0, 0.0, "makenoisemusic.com, ibid."),
    Modulo("Expert Sleepers Disting EX", 8, 229.0, 40.0, 0.0,
           "expert-sleepers.co.uk, leido 2026-09-03"),
)
FILA_HP = 104           # #169: la fila de abajo
```

**Comprueba los cuatro contra su web antes de cerrar la tarea.** Los de +12 V están
en el papel; los de −12 V y +5 V de arriba son `ESTIMADO` salvo el Disting: si no los
confirmas, márcalos y que el guion los cuente.

- [ ] **Step 4: correr y ver verde.** Pega la tabla de cuatro columnas: es lo que el
instrumento le puede decir a su dueño, y lo que `U13`/`U14` (D-F2) van a medir en
marcha.

- [ ] **Step 5: commit**

```bash
git add hardware/01-power-supply/v4/invitados_budget.py
git commit -m "Cuatro corrientes distintas que se llamaban igual, en cuatro columnas"
```

---

### Tarea 7: `fusible_budget.py` — el que manda es el rearranque en caliente

**Bloqueada por:** la hoja del fusible y la de la NTC (ver «Las entradas que hoy no
están»). **Si no bajan, se le piden a Samuel y la tarea se queda declarada, no se
completa con un valor plausible.**

**Por qué:** la v3 llevaba 1,6 A T calculado sobre 0,72 A rms. La fila «AC CURRENT»
de las hojas da 0,4 / 0,5 / 0,9 A por módulo con factor de potencia 0,25–0,30: los
seis a nominal son **3,9 A rms**. Y el inrush de la IRM-30 son **45 A**, no 4 — el
dígito corrido de una extracción de texto. 4 A T es **hipótesis** hasta que este
guion corra (papel §11).

**Files:**
- Create: `hardware/01-power-supply/v4/fusible_budget.py`

- [ ] **Step 1: las tres aserciones, en rojo**

```python
def _autocomprobacion() -> None:
    # 1. Permanente: el fusible no abre con la carga nominal, con margen.
    assert I_FUSIBLE_A >= 1.5 * I_RED_RMS_A, (
        f"fusible de {I_FUSIBLE_A:.1f} A contra {I_RED_RMS_A:.2f} rms "
        f"permanentes: por debajo de 1,5x se fatiga y abre un martes")

    # 2. Arranque en FRIO: la NTC limita, y el I2t del arranque cabe bajo el
    #    I2t del fusible.
    assert i2t_arranque_frio() < I2T_FUSIBLE, (
        f"el arranque frio mete {i2t_arranque_frio():.2f} A2s y el fusible "
        f"aguanta {I2T_FUSIBLE:.2f}")

    # 3. EL QUE MANDA: rearranque en CALIENTE. La NTC caliente ya no limita, y
    #    es el caso que la v3 no tenia porque su inrush lo ponia el toroide.
    assert i2t_rearranque_caliente() < I2T_FUSIBLE, (
        f"el rearranque en caliente mete {i2t_rearranque_caliente():.2f} A2s "
        f"contra {I2T_FUSIBLE:.2f} del fusible. Es el caso que manda: apagar y "
        f"volver a encender a los 100 ms con la NTC todavia a su resistencia "
        f"caliente. Sube la talla del fusible o pon NTC con rele de bypass")

    # 4. Los dos lados: un fusible demasiado grande no protege nada.
    assert I_FUSIBLE_A <= 6.3, (
        f"{I_FUSIBLE_A:.1f} A en el IEC de un aparato que consume 3,9 rms deja "
        f"de ser proteccion y pasa a ser un trozo de hilo")

    v = borde_rojo(_guarda_rearranque, dict(P_BASE), "t_rearranque_ms",
                   0.0, 60000.0, "es el caso que manda")
    print(f"  canario: por debajo de {v:.0f} ms entre corte y vuelta, no pasa")
```

- [ ] **Step 2: correr, ver fallar.**

- [ ] **Step 3: los números, de las hojas**

```python
# Fila "AC CURRENT" de las hojas Mean Well IRM, p. 2, leidas 2026-09-03.
# NO es vatios/voltios: el factor de potencia de estos modulos es 0,25-0,30
# y esa division daba 0,94 A donde hay 3,9.
I_RED_MODULO_A = {"PS1": 0.4, "PS2": 0.4, "PS3": 0.5, "PS4": 0.5,
                  "PS5": 0.4, "PS6": 0.9}          # <-- CONFIRMAR modulo a modulo
I_RED_RMS_A = sum(I_RED_MODULO_A.values())        # 3,9 A tipicos a nominal

# INRUSH, misma pagina. El de la IRM-30 son 45 A: la extraccion de texto daba
# "4 A/230Vac5 5" y ese 4 suelto costo un fusible mal dimensionado en la v1.
I_INRUSH_A = {"PS1": 0.0, ...}                     # <-- LEER los seis
T_INRUSH_S = 260e-6                                # ancho tipico, hoja
C_TOTAL_UF = 205.0                                 # papel sec.5, contra la NTC
```

- [ ] **Step 4: correr, ver verde, y anotar la talla que sale.** Ese número deja de
ser hipótesis y entra en el BOM de la placa R (tanda B). **Baja la hoja del fusible
de esa talla ahora**, con su curva I²t, y vuelve a correr contra el `I2T_FUSIBLE`
real: hasta entonces el guion está usando un `ESTIMADO` y tiene que decirlo.

- [ ] **Step 5: commit**

```bash
git add hardware/01-power-supply/v4/fusible_budget.py docs/reference/datasheets/
git commit -m "El fusible sale del rearranque en caliente, no del arranque frio"
```

---

### Tarea 8: `rizado_budget.py` — y lo que declara que no cubre

**Por qué:** el 0,8 µVrms del riel ultra es lo que este instrumento vende. Con el
toroide, lo que había que rechazar eran 100 Hz; ahora son 65 kHz **y sus flancos**, y
el papel §13 lo pone de riesgo 2: «la RF de los flancos entra en los op-amps mientras
el LNA da verde en su banda». Un presupuesto que solo mire 65 kHz reproduce ese
riesgo con cara de puerta.

**Files:**
- Create: `hardware/01-power-supply/v4/rizado_budget.py`

**Interfaces:**
- Consume: `curvas.psrr_db`.

- [ ] **Step 1: en rojo — la banda entera, y la declaración de lo que no cubre**

```python
def _autocomprobacion() -> None:
    # 1. A 65 kHz, la cadena entera tiene que dejar el rizado por debajo de la
    #    cota del riel ultra.
    assert v_ruido_riel_v(65e3) < COTA_RUIDO_V, (
        f"a 65 kHz llegan {v_ruido_riel_v(65e3)*1e6:.2f} uV al riel y la cota "
        f"son {COTA_RUIDO_V*1e6:.2f}")

    # 2. Y EN TODA LA BANDA de los flancos, no solo en la fundamental. Es el
    #    riesgo 2 del papel: el LNA (#58) mira su banda y da verde mientras
    #    esto entra por otro lado.
    peor_f, peor_v = max(((f, v_ruido_riel_v(f)) for f in BANDA_HZ),
                         key=lambda x: x[1])
    assert peor_v < COTA_RUIDO_V, (
        f"el peor punto de la banda esta en {peor_f:.3g} Hz con "
        f"{peor_v*1e6:.2f} uV contra {COTA_RUIDO_V*1e6:.2f} de cota. El LNA "
        f"puede seguir dando verde en SU banda: por eso se mira a 20 MHz")

    # 3. Lo que este guion NO cubre, dicho como asercion y no como nota al pie
    assert CUBRE_MODO_COMUN is False, (
        "este presupuesto es de modo DIFERENCIAL. El modo comun no lo rechaza "
        "ningun PSRR (design-notes v1 sec.18.7): vuelve como corriente por la "
        "masa, y quien lo cierra es D-F5 (Y2 por modulo) y su medida con los "
        "seis encendidos. Si algun dia esta constante se pone en True sin que "
        "el modelo cambie, se estara prometiendo lo que no se mide")

    v = borde_rojo(_guarda_banda, dict(P_BASE), "psrr_lt_20mhz_db",
                   0.0, 120.0, "el peor punto de la banda")
    print(f"  canario: por debajo de {v:.0f} dB de PSRR a 20 MHz, no pasa")
```

- [ ] **Step 2: correr, ver fallar.**

- [ ] **Step 3: la cadena, tramo a tramo**

`200 mVp-p` de salida del IRM (hoja, p. 2) → LC amortiguado → PSRR de `U1`/`U2`
(`curvas.psrr_db`) → PSRR del LT3045/LT3094 → riel. `BANDA_HZ` barre en logarítmico
de 65 kHz a 20 MHz; **no dos puntos elegidos a mano**. El LC se dimensiona aquí: su
`f0`, su `Q` amortiguado y su `DCR` salen de este guion y entran en la Tarea 9.

- [ ] **Step 4: correr, ver verde, pegar la curva** (el barrido impreso, no solo el
veredicto).

- [ ] **Step 5: commit**

```bash
git add hardware/01-power-supply/v4/rizado_budget.py
git commit -m "El rizado se mira hasta 20 MHz, y el modo comun se declara fuera"
```

---

### Tarea 9: `margen_budget.py` — el sustituto de `valle_budget.py`

**Por qué:** lo que reemplaza al valle. La pregunta es la misma —¿le llega a `U1`/`U2`
bastante tensión para que regulen?— y el problema ya no tiene 100 Hz que integrar:
es tolerancia + tempco + rizado + caída en el `DCR` del LC, todo en continua.

**Files:**
- Create: `hardware/01-power-supply/v4/margen_budget.py`

- [ ] **Step 1: en rojo, con el peor caso apilado**

```python
def _autocomprobacion() -> None:
    v_min = v_entrada_minima_v()
    assert v_min >= V_NECESARIA_U1, (
        f"a U1 le llegan {v_min:.2f} V en el peor caso y necesita "
        f"{V_NECESARIA_U1:.2f} (dropout garantizado a la corriente real). "
        f"Por debajo, el pre-regulador deja de regular y el ruido del IRM pasa "
        f"entero a la isla LT")
    # los dos lados: por arriba manda el absmax de U1/U2
    assert v_entrada_maxima_v() <= V_ABSMAX_U1, (
        f"en vacio y a tolerancia alta llegan {v_entrada_maxima_v():.2f} V "
        f"contra los {V_ABSMAX_U1:.1f} de maximo absoluto")
    v = borde_rojo(_guarda_margen, dict(P_BASE), "dcr_lc_ohm",
                   0.0, 5.0, "deja de regular")
    print(f"  canario: con mas de {v:.3f} ohm de DCR en el LC, no regula")
```

- [ ] **Step 2: correr, ver fallar.**

- [ ] **Step 3: los términos, apilados en el peor sentido**

`±15 V` nominales; **tolerancia ±2,5 %** y **tempco ±0,03 %/°C** (hoja IRM, p. 2)
evaluado a la temperatura que dé `calor_budget.py`, no a 25 °C; rizado 200 mVp-p
restado por su mitad; `DCR` del LC × 1,4 A. Enfrente, el **dropout garantizado** de
LM2941 y LM2991 a la corriente real (Fig. 1 de cada hoja, ya en el árbol) — y el
papel §4.2 avisa de que a la corriente real el dropout es **menor** que a 1 A, así
que leer la figura en el punto correcto es parte de la tarea.

- [ ] **Step 4: correr, ver verde.**

- [ ] **Step 5: commit**

```bash
git add hardware/01-power-supply/v4/margen_budget.py
git commit -m "Lo que le llega a la cascada, contra lo que necesita para regular"
```

---

### Tarea 10: `secuencia_budget.py` — D-F4, y que ningún estado deje un riel solo

**Por qué:** es el guion de la decisión D-F4. Los IRM tienen setup de **1000 ms
típico y sin máximo publicado**, hold-up de 40 ms y *hiccup* independiente: sin
detector de ventana, cada encendido, cada apagado y cada microcorte abre una ventana
con un riel crudo y el otro no. La v3 no podía tener este fallo porque tenía un
transformador.

**Files:**
- Create: `hardware/01-power-supply/v4/secuencia_budget.py`

- [ ] **Step 1: en rojo — la máquina de estados, enumerada**

```python
def _autocomprobacion() -> None:
    # 1. La ventana de habilitacion cabe entre lo que U1/U2 necesitan y lo que
    #    los IRM garantizan, con tolerancia y tempco a la T de calor_budget.
    assert V_UMBRAL_ALTO > V_NECESARIA_U1, (
        f"el umbral de habilitacion ({V_UMBRAL_ALTO:.2f} V) esta por debajo de "
        f"lo que U1 necesita para regular ({V_NECESARIA_U1:.2f}): el "
        f"secuenciador habilitaria una cascada que no regula")
    assert V_UMBRAL_ALTO < V_MINIMA_IRM_PEOR_CASO, (
        f"el umbral ({V_UMBRAL_ALTO:.2f} V) esta por encima del minimo que el "
        f"IRM garantiza en su peor caso ({V_MINIMA_IRM_PEOR_CASO:.2f}): la "
        f"cascada no arrancaria nunca en una unidad de tolerancia mala")

    # 2. La histeresis: ni oscila ni se queda pegado.
    assert V_UMBRAL_ALTO - V_UMBRAL_BAJO >= HIST_MIN_V, (
        "sin histeresis suficiente el detector castanetea en cada microcorte")

    # 3. LO QUE DECIDE: ningun estado alcanzable deja un riel solo. Se enumeran
    #    TODOS, no se razonan.
    for est in estados_alcanzables():
        assert not est.riel_solo, (
            f"el estado {est.nombre} deja {est.riel_vivo} vivo con "
            f"{est.riel_muerto} muerto durante {est.ms:.0f} ms. Un bus de "
            f"+-12 V con un solo riel deja el otro nodo donde lo pongan los "
            f"clamps de los op-amps")

    v = borde_rojo(_guarda_ventana, dict(P_BASE), "hist_v",
                   0.0, 5.0, "castanetea")
    print(f"  canario: con menos de {v:.3f} V de histeresis, castanetea")
```

`estados_alcanzables()` enumera el producto de {`PS1` viva/muerta} × {`PS2`
viva/muerta} × {detector habilitando/no} y comprueba que la combinación
«uno sí, otro no, detector habilitando» **no existe**. Enumerar es la tarea: un
argumento en prosa sobre por qué no puede pasar es lo que este guion sustituye.

- [ ] **Step 2: correr, ver fallar.**

- [ ] **Step 3: los umbrales, de las hojas**

`LM2941 ON/OFF` activo-bajo, **< 0,8 V habilita** (SNVS770I p. 11); `LM2991 ON/OFF`
activo-alto deshabilita, **> 2,4 V** (SNVS099I p. 9). Los dos ya en el árbol. La
ventana: **+15 por encima de 14,1 V y −15 por debajo de −13,9 V** (papel §4.2). El
mismo detector, replicado, gobierna los interruptores de carga de ±12 V de rack.

- [ ] **Step 4: correr, ver verde.** La salida de este guion son **los valores de los
divisores y la histeresis del detector**: entran en el esquema de R (tanda B).

- [ ] **Step 5: commit**

```bash
git add hardware/01-power-supply/v4/secuencia_budget.py
git commit -m "El secuenciador de D-F4, con sus umbrales y sus estados enumerados"
```

---

### Tarea 11: `fuga_budget.py` — seis fugas y los Y2 de D-F5

**Bloqueada por:** la nota EMI de Mean Well (§12.4) y la cifra de IEC 62368-1
(§12.5). **Si la norma no se consigue, se declara HUECO con el valor de trabajo y su
origen citado.** Un límite de fuga inventado es exactamente el tipo de número que no
se puede publicar.

**Por qué:** seis módulos con su fuga a PE **suman**, y D-F5 añade seis Y2 más que
también fugan. El papel §5 estima ~1,4 mA; el límite de la norma para Clase I
enchufable es lo que dice si eso cabe. Y el mecanismo de D-F5 —que el lazo de modo
común se cierre en centímetros— es de la nota del fabricante, no de una intuición.

**Files:**
- Create: `hardware/01-power-supply/v4/fuga_budget.py`

- [ ] **Step 1: en rojo**

```python
def _autocomprobacion() -> None:
    assert fuga_total_ma() < LIMITE_NORMA_MA, (
        f"la fuga a PE suma {fuga_total_ma():.3f} mA (seis modulos + seis Y2 "
        f"de D-F5) contra {LIMITE_NORMA_MA:.2f} de la norma")
    # los dos lados: un Y2 demasiado pequeno no cierra el lazo de 65 kHz
    assert Z_Y2_A_65KHZ_OHM < Z_MAX_UTIL_OHM, (
        f"con {C_Y2_NF:.0f} nF el Y2 presenta {Z_Y2_A_65KHZ_OHM:.0f} ohm a "
        f"65 kHz: por encima de {Z_MAX_UTIL_OHM:.0f} deja de ser el camino "
        f"corto y la corriente de modo comun se vuelve por los hilos de la "
        f"estrella, que es justo lo que D-F5 existe para evitar")
    v = borde_rojo(_guarda_fuga, dict(P_BASE), "c_y2_nf", 0.1, 100.0,
                   "contra")
    print(f"  canario: por encima de {v:.1f} nF de Y2, la fuga se pasa")
```

Las dos aserciones son la tensión real de D-F5: **el Y2 grande cierra mejor el modo
común y fuga más**. Este guion es donde ese compromiso tiene un número en vez de una
opinión.

- [ ] **Steps 2–4:** correr en rojo, escribir con las fugas por módulo de la hoja
(p. 2) y el límite de la norma, correr en verde. **El valor del Y2 que sale entra en
el BOM de R.**

- [ ] **Step 5: commit**

```bash
git add hardware/01-power-supply/v4/fuga_budget.py
git commit -m "La fuga de seis modulos y sus Y2, contra el limite de la norma"
```

---

### Tarea 12: `check_absmax.py` v4, y `valle_budget.py` se borra

**Por qué:** el sujeto del `check_absmax.py` de la v3 es `VRAW = 20,54 V`, y **VRAW
ya no existe**. La pregunta nueva son dos: el **OVP máximo de `PS1`/`PS2` (20,25 V)**
contra los 26 V de `U1`/`U2`, y el **OVP de `PS3`/`PS4` (16,2 V)** contra lo que el
crowbar de D-F6 deje pasar. Y `valle_budget.py` mide un valle que no se puede medir:
se borra, no se deja verde por vacío.

**Files:**
- Create: `hardware/01-power-supply/v4/check_absmax.py`, `v4/absmax.csv`
- Delete: `hardware/01-power-supply/v3/valle_budget.py`

- [ ] **Step 1: en rojo — las dos preguntas**

```python
def _autocomprobacion() -> None:
    assert OVP_MAX_PS1_V < ABSMAX_U1_V, (
        f"PS1 en OVP clampa a {OVP_MAX_PS1_V:.2f} V y el maximo absoluto de U1 "
        f"son {ABSMAX_U1_V:.1f}: un fallo del IRM se lleva el pre-regulador")
    # D-F6: en el rack el que decide no es el margen, es el crowbar
    assert V_DISPARO_CROWBAR_V < ABSMAX_MODULO_INVITADO_V, (
        f"el crowbar dispara a {V_DISPARO_CROWBAR_V:.1f} V y un modulo ajeno "
        f"aguanta {ABSMAX_MODULO_INVITADO_V:.1f}: llega tarde")
    assert V_DISPARO_CROWBAR_V > V_RIEL_RACK_V * (1 + TOL_RACK), (
        f"el crowbar dispara a {V_DISPARO_CROWBAR_V:.1f} V y el riel normal "
        f"llega a {V_RIEL_RACK_V*(1+TOL_RACK):.2f}: dispararia solo")
    # el lazo de D-F6 se cierra porque el IRM entra en hiccup, no porque abra
    # un fusible. Es la diferencia con #118 y hay que aseverarla.
    assert I_CORTO_IRM_A > I_MANTENIMIENTO_SCR_A, (
        f"el SCR necesita {I_MANTENIMIENTO_SCR_A:.2f} A para quedarse "
        f"enganchado y la IRM en corto da {I_CORTO_IRM_A:.2f}: el crowbar "
        f"dispararia y se soltaria, dejando el riel oscilando")
```

La última es la que separa a D-F6 de lo que #118 rechazó: **ahí el lazo no cerraba;
aquí sí, y esto lo comprueba.**

- [ ] **Step 2–4:** correr en rojo, escribir con `absmax.csv` heredando la forma del
de la v3, correr en verde.

- [ ] **Step 5: borrar el valle, con su motivo en el commit**

```bash
git rm hardware/01-power-supply/v3/valle_budget.py
git add hardware/01-power-supply/v4/check_absmax.py hardware/01-power-supply/v4/absmax.csv
git commit -m "El valle no existe sin rectificador; los maximos absolutos son otros dos"
```

---

### Tarea 13: `ground_budget.py` — el desfase con N patches

**Por qué:** el hallazgo de la junta que más lejos llega. La masa es **un nodo**, no
una rama: con diez patches, 1,4 A de un retorno de 5,3 cruzan el plano del
instrumento. Una regla sobre una rama no gobierna eso. Lo que sí: la bahía como único
cruce, sus jacks en una isla de masa del rack, y **cada CV recibido en diferencial**.

**Files:**
- Modify: `hardware/bus-board/ground_budget.py`

- [ ] **Step 1: en rojo — N deja de ser 1**

```python
def _desfase_rack_instrumento() -> None:
    # N patches en paralelo: el retorno del invitado NO vuelve por una rama,
    # vuelve por TODAS. Con N=1 el numero es cómodo y falso.
    for n in (1, 2, 5, 10, 20):
        mv = desfase_mv(i_rack_a=I_RACK_SOSTENIDO_A, n_patches=n)
        print(f"  {n:2d} patches -> {mv:6.2f} mV = {cents(mv/1000):5.2f} cents")
    peor = desfase_mv(I_RACK_SOSTENIDO_A, N_PATCHES_PEOR)
    # Y LA ASERCION NO ES que el desfase sea pequeno --no lo es-- sino que NO
    # ENTRA en la cadena de tono, porque la bahia lo recibe en diferencial.
    assert BAHIA_RECIBE_EN_DIFERENCIAL, (
        f"con {N_PATCHES_PEOR} patches el desfase son {peor:.2f} mV = "
        f"{cents(peor/1000):.2f} cents, muy por encima de los "
        f"{OBJETIVO_CENTS:.1f} de objetivo. Eso NO se arregla ensanchando "
        f"cobre: se arregla recibiendo cada CV en diferencial en la bahia "
        f"(papel fuente v4 sec.4.1 y sec.10). Si esta constante se pone en "
        f"False, el instrumento se desafina con el rack cargado")
```

- [ ] **Step 2–4:** correr en rojo, implementar `desfase_mv(i_rack_a, n_patches)`
sobre la resistencia de retorno que el fichero ya modela (`r_plano`, `r_cable`),
correr y **pegar la tabla de N**: es el número que el paso nuevo del bring-up mide en
cents.

- [ ] **Step 5: commit**

```bash
git add hardware/bus-board/ground_budget.py
git commit -m "El retorno del invitado vuelve por todas las ramas, y con N patches"
```

---

### Tarea 14: `check_bringup.py` v4 — se escribe antes que la placa

**Por qué:** es la forma de la v3 y no pierde ninguno de sus pasos —los 6, 7 y 8 de
la v3 siguen, y la v1 de este papel los había dejado caer—. Cada paso **predice un
número**, `medidas.csv` lo guarda y este guion lo juzga. Se escribe ahora, con la
placa sin dibujar, porque un bring-up escrito después de medir es un acta, no una
predicción.

**Files:**
- Create: `hardware/01-power-supply/v4/check_bringup.py`, `v4/medidas.csv`

- [ ] **Step 1: los pasos de §9.1, uno por fila, con su predicción**

`medidas.csv` con columnas `paso, magnitud, predicho, tolerancia, medido, fuente`.
`medido` vacío hasta que exista la placa: **el guion tiene que pasar con la columna
vacía** (no hay nada que juzgar) y **fallar en cuanto un `medido` se salga de su
tolerancia**. Los pasos, del papel §9.1: 0 (aislamiento y ★), 1 (cada IRM solo,
rizado a 20 MHz con el método de la nota 2, corriente de red con pinza, inrush frío y
rearranque a 100 ms), 2 (±15 V con carga tras el LC), **2b (el secuenciador: quitar la
red a `PS1` con `PS2` viva → los dos rieles caen juntos)**, 3–5 (la cascada, como la
v3), 6 (telemetría contra multímetro, **más los ±15 V y los dos INA de D-F2**),
7 (térmica con el recinto **ventilado** a la carga sostenida declarada), el desfase
rack↔instrumento en mV **y en cents**, el disparo del crowbar de D-F6, y el riel
ultra mirado con 20 MHz de ancho de banda.

- [ ] **Step 2: la aserción que impide el acta en blanco**

```python
assert PASOS_ESPERADOS <= {f.paso for f in filas}, (
    f"faltan pasos en medidas.csv: {PASOS_ESPERADOS - {f.paso for f in filas}}. "
    f"Un bring-up al que se le cae un paso no falla: pasa, y por eso los pasos "
    f"6, 7 y 8 de la v3 se habian perdido en la v1 de este papel")
assert all(f.predicho is not None for f in filas), (
    "un paso sin numero predicho no es un bring-up, es una lista de tareas")
```

- [ ] **Steps 3–4:** correr en rojo, escribir, correr en verde con la columna `medido`
vacía.

- [ ] **Step 5: commit**

```bash
git add hardware/01-power-supply/v4/check_bringup.py hardware/01-power-supply/v4/medidas.csv
git commit -m "El bring-up de la v4, escrito antes que la placa y con sus predicciones"
```

---

### Tarea 15: las enmiendas de §10 (la hace quien coordina)

**Por qué:** el papel §10 lo dice de sí mismo: «para ejecutarlas en el plan de esta
tanda, **no para que un documento prometa lo que otro no hace**» (#214, #206). Una
tabla de enmiendas que nadie ejecuta deja dos arquitecturas vivas en `main`.

**Files:** los de la tabla de §10 del papel. Las que **sí** son de esta tanda:

- [ ] `hardware/01-power-supply/v3/README.md` y `docs/modules/01-power-supply.md`:
  la v3 no se pide; la v4 es la que se construye; qué sustituye a la regla «nunca con
  una v4».
- [ ] `design-notes.md` §13 (Patch): ★ es un nodo en R; `GNDD` no lo toca; el chasis
  es la masa del rack.
- [ ] `design-notes.md` §18 (**Rewrite**): de 100 Hz a 65 kHz — seis módulos, LC
  amortiguado, ferritas, Y2 de modo común, enlace trenzado, y **el LNA y la mirada a
  20 MHz como puertas**.
- [ ] `psu-v2-goat-design.md` §7 y §11.5 (Patch): la IRM-15-5 «fuera de la placa» →
  `PS6` en R.
- [ ] `alimentacion-n657-design.md` §3.2 (Patch): el calor del LDO a máximo (4,57 W);
  D-R1 sigue abierto con los dos números.
- [ ] Spec del chasis §3.1, §3.2, §3.3, §4: térmica → `calor_budget.py`; «conduce
  calor, nunca corriente» → «conduce la corriente del rack, nunca la del
  instrumento»; geometría sin toroide y **con D-F3 = A**.
- [ ] Issues, con `gh issue comment`: **#151** (dueño de techo: `calor_budget.py`,
  sigue abierto hasta que corra), **#169** (rieles propios, PTC por slot como
  requisito, secuenciador y crowbar aguas arriba), **#118** (el crowbar vuelve
  **solo** en los rieles de rack, y por qué ahí sí cierra el lazo), **#256** (ya no
  bloquea el dimensionado del +5 V; bloquea el calor del 1,8 V), **#58** (puerta del
  riel ultra, y no basta sola).

Las que **no** son de esta tanda, y hay que decirlo en el PR para que no se pierdan:
el papel de la bahía (dos requisitos), el papel del case (D-F3 = A, el venteo y el
rojo de la Tarea 4), y el cierre de #141, #280, #106, #56 y #57, **que se cierran
cuando la v4 se adopte, no cuando se escriba**.

> **«Cierra #N» en español no cierra nada.** GitHub solo autocierra en inglés: tras
> el merge, `gh issue close` a mano, con la comparación previsto/encontrado en el
> comentario.

- [ ] **Commit**

```bash
git add docs/ hardware/01-power-supply/v3/README.md
git commit -m "Las enmiendas que la v4 le debe a los papeles que legisla"
```

---

## Autorrevisión del plan

**Cobertura del papel.** §1 → Tareas 3 y 5. §3 (los seis módulos) → entra como
constantes en 3, 7, 9 y 11. §4.1 (la masa es un nodo) → Tarea 13. §4.2 (cascada y
secuenciador) → 9 y 10. §4.3 (rieles de rack, crowbar) → 6 y 12. §4.4 (+5 V digital)
→ 5. §4.5 (el 1,8 V) → declarado como carga en 3. §5 (la red) → 7 y 11. §6 (térmica)
→ 2, 3 y 4. §7 (telemetría) → **no tiene tarea propia en esta tanda**: `U13`/`U14` son
huella y esquema, o sea placa R, tanda B; lo que sí entra aquí es su paso del bring-up
(Tarea 14). §8 (placas y conectores) → tanda B, salvo los conectores, cuya corriente
sale de la Tarea 3. §9 (puertas) → es el índice de este plan. §9.1 (bring-up) → 14.
§10 (enmiendas) → 15. §12 (verificaciones) → 2 hace §12.1 y §12.2; 7 hace §12.6 y
§12.8; 11 hace §12.4 y §12.5; **§12.3 (las seis huellas), §12.7 (conducción por el
encapsulado) y §12.9 (que ningún módulo expone un jack) son de la tanda B** y quedan
dichas aquí para que no se caigan. §13 (riesgos) → 1 y 2 en la Tarea 8, 3 en la 11,
4 en la 13, 5 en la 10, 6 en la 12, 7 en la 7, 12 en la 3.

**Dependencias.** 2 → 3 → {4, 5, 6}; 2 → {8, 9}; 3 → 9 y 10 (la temperatura a la que
se evalúan tolerancia y tempco); 1 → todas. Las Tareas 7 y 11 están **bloqueadas por
hojas que no están en el árbol** y pueden adelantarse hasta el punto donde el número
de la hoja hace falta, no más.

**Consistencia de nombres.** `borde_rojo` (Tarea 1, con alias `_borde_rojo` en el
case) · `derating(t_amb_c, familia)` y `psrr_db(pieza, f_hz)` (2) · `SOSTENIDO`,
`PLACA_A`, `PSU3_A`, `aire_recinto_c`, `sostenido_a` (3) · `CENSO`, `fila_peor_caso`
(6) · `desfase_mv(i_rack_a, n_patches)` (13). Las claves de riel son las mismas en
todas partes: `"rack+12"`, `"rack-12"`, `"rack+5"`, `"digital+5"`.

**Lo que este plan no puede garantizar, y hay que mirar de frente:** la Tarea 3 puede
salir **roja aun con D-F3 = A**. Si el rack ventilado no llega a la PSU3, el listón
firmado no existe en ningún recinto que este case pueda ser, y eso es una conversación
con Samuel —no un aserto que se baja—. Es el riesgo 1 del papel, y esta tanda es
justamente la que lo contesta.
