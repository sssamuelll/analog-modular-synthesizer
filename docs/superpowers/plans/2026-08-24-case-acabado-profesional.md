# Acabado profesional del case SAM17 — plan de implementación

> **Para agentes ejecutores:** SUB-SKILL REQUERIDA: usa
> `superpowers:subagent-driven-development` (recomendado) o
> `superpowers:executing-plans` para ejecutar tarea a tarea. Los pasos van
> en casillas (`- [ ]`).

**Meta:** llevar el cajón de «geométricamente correcto» a **fabricable con
acabado de producto, a la primera**, sin cambiar el material ni la silueta.

**Arquitectura:** el acrílico llega a acabado de vitrina cuando se ejecutan
tres procesos que hoy no están en ningún papel — **recocido**, **canto
diamantado** y **apriete controlado**. Este plan (a) mete esos procesos y
sus cotas en `params.scad` como parámetros con puerta, (b) escribe el
documento que hoy no existe y que los lleva al taller (`case/PLIEGO.md`), y
(c) cierra los cuatro huecos de fabricación que la revisión adversarial del
2026-08-24 destapó. **No toca la silueta ni la geometría de las caras.**

**Herramientas:** OpenSCAD 2021.01, Python 3.14 (numpy/scipy/matplotlib/ezdxf),
PowerShell 5.1. Sin dependencias nuevas.

**Spec:** [`2026-08-15-case-design.md`](../specs/2026-08-15-case-design.md)
(rev. 17) · Revisión adversarial de origen: sesión del 2026-08-24.

## Restricciones globales

- **Material: PMMA COLADO (GS), no extruido.** El extruido trae tensión de
  fábrica y craquela solo. Decidido en spec §11.
- **Proceso: fresado CNC, no láser.** `kerf = 0`. Spec §2 rev. 4.
- **Ninguna junta irreversible.** El case se desatornilla entero desde el
  2026-08-21. Nada de pegado, nada de autoadhesivo estructural.
- **`params.scad` es numérico puro**: solo `nombre = valor;` con valor
  numérico. Las cadenas van en `sam17_case.scad`.
- **Toda cota nueva lleva puerta.** Un parámetro sin assert es un parámetro
  que parece que hace algo — es lo que `guarda_parametros_vivos()` existe
  para cazar (#54).
- **Umbral de fluencia del PMMA: 10 MPa** (#106). Es SUPUESTO declarado,
  igual que `salto_termico_max`. **Nadie lo ha medido sobre el acrílico que
  se va a comprar**, y de él cuelgan el par de apriete y el mapa de
  debilidad. Cerrarlo es pregunta del RFQ (Tarea 1), no de este plan.
- Las puertas se corren con `python case/clearance_budget.py` y
  `python case/check_dxf.py`; el export completo con
  `powershell -File case/cad/export.ps1`.

---

## Estructura de ficheros

| Fichero | Responsabilidad | Acción |
|---|---|---|
| `case/PLIEGO.md` | El documento que va al taller: material, procesos, tolerancias, acabados, qué DXF es qué pieza | **Crear** |
| `case/cad/params.scad` | Cotas nuevas: chaflán, apriete, paticas | Modificar |
| `case/clearance_budget.py` | Puertas nuevas: `guarda_apriete()`, `guarda_paticas()`, `guarda_chaflan()` | Modificar |
| `case/check_dxf.py` | Puerta nueva: `guarda_kondor()` (huella de fuente + fresabilidad) | Modificar |
| `case/cad/export.ps1` | Añadir `kondor_cajeado_2d` a la lista de piezas | Modificar |
| `case/README.md` | BOM de herrajes, orden de ensamblaje, protocolo de manipulación | Modificar |

**Orden:** la Tarea 1 arranca el reloj de proveedor y **se lanza primero
aunque el resto no esté**. Las tareas 2–5 son independientes entre sí y no
dependen de la 1: se pueden repartir. La **Tarea 6 va última** porque el
pliego copia las cotas que fijan las anteriores. Las decisiones que
**esperan a la muestra física** están al final y NO son tareas.

---

## Tarea 1: El RFQ y la muestra — lo único con tiempo de calendario

**Ficheros:**
- Crear: `case/RFQ.md`

**Interfaces:**
- Produce: la lista de procesos que la Tarea 6 copia al pliego; el retazo
  físico que cierra `#98`, `#97` y las tres mediciones del `#179`.

Va primera porque es la única que depende de un tercero. Todo lo demás se
puede hacer hoy; esto tarda lo que tarde el proveedor.

**Lo que hay que buscar no es «un CNC»**: es una **casa de acrílico** — de
las que hacen vitrinas, expositores y museografía. Un CNC general fresa la
forma y te la entrega tal cual sale. Una casa de acrílico tiene la pulidora
de diamante y el horno de recocido como equipo estándar. Es la diferencia
entre dos presupuestos que parecen el mismo trabajo.

- [ ] **Paso 1: escribir `case/RFQ.md`** con estas preguntas, textuales:

```markdown
# RFQ — cuerpo de acrílico del SAM17

## Preguntas eliminatorias (si alguna es "no", no es el taller)
1. ¿Hacen RECOCIDO (annealing) de las piezas después de mecanizar?
   ¿A qué temperatura y con qué rampa de enfriamiento?
2. ¿Hacen PULIDO DIAMANTADO de canto en máquina? (No pulido a llama.)
3. ¿Trabajan PMMA COLADO (GS) en 8 mm y 5 mm en naranja translúcido?

## Preguntas de cota
4. ¿Qué tolerancia de espesor tiene el material que suministran, por
   escrito? (Schaeffer confirmó ±(0.4 + 0.1×espesor) el 2026-08-18.)
5. ¿Miden el espesor real del lote y nos lo comunican ANTES de cortar?
6. ¿Qué tolerancia de posición garantizan en taladros? (Necesitamos
   ±0.05 mm entre filas de una misma placa — lo exige alineacion().)
7. ¿Diámetro de fresa estándar? (El diseño asume 3 mm, radio 1.5.)

## Muestra que pedimos con el presupuesto
Un retazo del naranja REAL, 8 mm, mínimo 150 × 100 mm, que lleve:
  - un canto tal cual sale de fresa y otro DIAMANTADO
  - un chaflán de 0.5 × 45 en una arista
  - un cajeado ciego de 4 mm y otro de 6 mm (letra o rectángulo)
  - dos taladros M3 pasantes
Y el mismo retazo en AHUMADO si lo tienen.
```

- [ ] **Paso 2: registrar el criterio de aceptación ANTES de recibir nada**

En `case/RFQ.md`, sección «criterio»:

```markdown
## Criterio de aceptación de la muestra (escrito ANTES de mirarla)
- Canto diamantado: transparente, sin línea blanca visible a 50 cm bajo
  luz de techo. Si se ve lechoso, no es diamantado.
- Cajeado ciego: la letra tiene que leerse a 1 m en el naranja. Si a 4 mm
  no se lee y a 6 sí, se sube kondor_prof.
- Espesor: medido con calibre en 5 puntos; se anota el rango.
```

- [ ] **Paso 3: commit**

```bash
git add case/RFQ.md
git commit -m "El RFQ: tres preguntas eliminatorias y una muestra con criterio escrito"
```

---

## Tarea 2: Chaflán en las aristas vistas

**Ficheros:**
- Modificar: `case/cad/params.scad`
- Modificar: `case/clearance_budget.py`

**Interfaces:**
- Produce: `chaflan` (float, mm) — lo consume el pliego (Tarea 6).

Un canto pulido con arista viva se desportilla al primer roce, y el
2026-08-24 dejamos **vivas** las dos esquinas traseras (`radio_trasero = 0`),
una de ellas a ras del suelo. El chaflán mata el filo sin devolver el hueco
contra la trasera.

**El chaflán NO es geometría del modelo**: el DXF es 2D y no puede
expresarlo, igual que no puede expresar el cajeado. Es cota de pliego. Aquí
va el parámetro y su puerta; al taller lo lleva la Tarea 6.

- [ ] **Paso 1: escribir la puerta primero, en `case/clearance_budget.py`**

Insertar antes de `guarda_fresado`:

```python
def guarda_chaflan(p: dict[str, float]) -> None:
    """El chaflan mata el filo sin comerse la pieza.

    Existe porque el 2026-08-24 las dos esquinas traseras pasaron a vivas
    (radio_trasero = 0) para que la trasera empotre a ras, y una arista viva
    en PMMA con canto pulido se desportilla -- la de fondo-abajo va a ras del
    suelo, que es donde el case roza al arrastrarlo.

    Dos limites, y los dos muerden por razones distintas:
      - por abajo, la fresa: un chaflan menor que el paso de la maquina no
        se ejecuta, se redondea solo.
      - por arriba, la plancha mas FINA: el chaflan se come material de las
        dos caras, y en la tapa del valle (5 mm) un chaflan grande deja el
        canto en filo otra vez, por el otro lado.
    """
    t_min = min(p["t_acrilico"], p["t_base"], p["t_cheek"], p["t_piel"])
    assert p["chaflan"] >= 0.3, (
          f"chaflan = {p['chaflan']} mm: por debajo de 0.3 el taller no lo "
          f"ejecuta como chaflan, lo redondea. Pedir 0 (arista viva) es otra "
          f"cosa y hay que decirlo aparte.")
    assert p["chaflan"] <= t_min / 4, (
          f"chaflan = {p['chaflan']} mm contra la plancha mas fina "
          f"({t_min} mm): se come mas de un cuarto del espesor por cada cara "
          f"y el canto vuelve a quedar en filo. Maximo {t_min/4:.2f}.")
    print(f"chaflan: {p['chaflan']} mm x 45 en toda arista vista "
          f"(limite por la plancha de {t_min:g} mm: {t_min/4:.2f})")
```

Registrar la llamada en `main()`, junto a las demás guardas.

- [ ] **Paso 2: correrla y verla en ROJO**

Run: `python case/clearance_budget.py`
Expected: `KeyError: 'chaflan'` — el parámetro todavía no existe.

- [ ] **Paso 3: añadir el parámetro a `case/cad/params.scad`**

Después del bloque de `radio_trasero`:

```scad
// CHAFLAN de toda arista VISTA. 0.5 x 45 grados.
//
// No es geometria de este modelo y por eso no aparece en ningun DXF: un
// fichero de corte 2D no sabe decir "y ademas matale el filo". Es cota de
// PLIEGO, y vive aqui para que tenga puerta y no se pierda.
//
// Por que existe: el 2026-08-24 las dos esquinas traseras pasaron a VIVAS
// (radio_trasero = 0) para que la trasera empotre a ras, y ese mismo dia se
// decidio canto DIAMANTADO. Arista viva + canto pulido = se desportilla al
// primer roce, y la de fondo-abajo esta a ras del suelo. El chaflan resuelve
// el filo sin devolver el hueco contra la trasera, que es lo que costaba el
// radio.
//
// 0.5 y no menos: por debajo de 0.3 el taller no lo ejecuta como chaflan,
// lo redondea. Y no mas: en la tapa del valle (5 mm) un chaflan grande deja
// el canto en filo otra vez por el otro lado. Lo vigila guarda_chaflan().
chaflan = 0.5;
```

- [ ] **Paso 4: correr la puerta y verla en VERDE**

Run: `python case/clearance_budget.py`
Expected: `chaflan: 0.5 mm x 45 en toda arista vista (limite por la plancha de 5 mm: 1.25)` y `clearance_budget: VERDE`

- [ ] **Paso 5: probar que la puerta muerde por los dos lados**

Run: `sed -i 's/^chaflan = 0.5;/chaflan = 0.1;/' case/cad/params.scad && python case/clearance_budget.py; sed -i 's/^chaflan = 0.1;/chaflan = 2.0;/' case/cad/params.scad && python case/clearance_budget.py; sed -i 's/^chaflan = 2.0;/chaflan = 0.5;/' case/cad/params.scad`
Expected: la primera falla por «no lo ejecuta como chaflan», la segunda por «se come mas de un cuarto del espesor», la tercera vuelve a VERDE.

- [ ] **Paso 6: commit**

```bash
git add case/cad/params.scad case/clearance_budget.py
git commit -m "El filo se mata en el pliego: chaflan de 0.5 con su puerta por los dos lados"
```

---

## Tarea 3: El apriete de los 30 M3 deja de ser «hasta marcar»

**Ficheros:**
- Modificar: `case/cad/params.scad`
- Modificar: `case/clearance_budget.py`
- Modificar: `case/README.md` (BOM de herrajes)

**Interfaces:**
- Consume: nada.
- Produce: `par_m3` (N·m) y `d_arandela` (mm) — los consume el pliego y el
  orden de ensamblaje.

Hoy el README dice *«apretar hasta marcar, NO hasta fisurar»* y la spec §11
admite que *«el par máximo antes de fisura no está medido»*. Son **30
tornillos visibles** apretados a tacto sobre acrílico, y cada uno es un
punto de craquelado.

**El número sale de la arandela**, y por eso las dos cotas van juntas. Con
la arandela apoyando sobre el acrílico, el área de apoyo es
`π(d² − d_M3_paso²)/4`, la precarga que llega a 10 MPa es `σ·A`, y el par
es `T = 0.2·F·d_tornillo`:

| arandela | área | precarga máx | **par máx** |
|---|---|---|---|
| d9 | 54.5 mm² | 545 N | 0.33 N·m |
| d12 | 104.0 mm² | 1040 N | 0.62 N·m |
| **d16** | **191.9 mm²** | **1919 N** | **1.15 N·m** |

**Se elige la d16**, y por dos razones que se refuerzan: es la única que deja
el par por encima de 1 N·m —donde una llave dinamométrica de 1/4" empieza a
existir; por debajo hace falta destornillador dinamométrico de precisión— y
**ya está en el BOM**, porque es la misma arandela ancha de los cuatro ejes
de giro. La familia de herraje pasa de dos arandelas a una.

- [ ] **Paso 1: escribir la puerta primero, en `case/clearance_budget.py`**

```python
# Coeficiente par-precarga de un tornillo de acero seco. 0.2 es el valor de
# manual; con rosca engrasada baja a ~0.15 y el MISMO par da un 30% mas de
# precarga -- o sea que engrasar la rosca hace fisurar el acrilico con el
# par correcto. Va dicho en el pliego y en el orden de ensamblaje.
K_PAR = 0.20

def guarda_apriete(p: dict[str, float]) -> None:
    """El par de los M3 sale de la arandela, no del tornillo.

    Los 30 M3 aprietan planchas de acrilico contra largueros de aluminio. Lo
    que decide si el PMMA craquela no es el tornillo sino cuanta area de
    acrilico reparte su precarga, o sea la ARANDELA. Precedente en el propio
    BOM: con arandela M4 normal (d9) los ejes de giro daban 16.3 MPa y "el
    PMMA fluye en semanas"; con d16 dan 4.3 y aguantan.

    Aqui se hace la cuenta al reves: dada la arandela, cual es el par maximo
    que no pasa de SIGMA_PMMA.
    """
    SIGMA_PMMA = 10.0
    area = math.pi * (p["d_arandela"] ** 2 - p["d_M3_paso"] ** 2) / 4
    precarga = SIGMA_PMMA * area
    par_max = K_PAR * precarga * 0.003
    assert p["par_m3"] <= par_max, (
          f"par_m3 = {p['par_m3']} N*m con arandela d{p['d_arandela']:g}: la "
          f"precarga aplasta el acrilico a mas de {SIGMA_PMMA} MPa. Maximo "
          f"{par_max:.2f} N*m -- o sube la arandela, que es lo que de verdad "
          f"compra par.")
    assert p["par_m3"] >= 1.0, (
          f"par_m3 = {p['par_m3']} N*m: por debajo de 1 N*m no hay llave "
          f"dinamometrica de 1/4\" que lo de, y 'a tacto' es lo que este "
          f"cambio vino a quitar. Sube la arandela hasta que el par quepa "
          f"en una herramienta que existe.")
    print(f"apriete: 30 M3 a {p['par_m3']} N*m con arandela "
          f"d{p['d_arandela']:g} -> {precarga*p['par_m3']/par_max/area:.1f} MPa "
          f"sobre el acrilico (techo {SIGMA_PMMA})")
```

Registrar la llamada en `main()`.

- [ ] **Paso 2: correrla y verla en ROJO**

Run: `python case/clearance_budget.py`
Expected: `KeyError: 'par_m3'`

- [ ] **Paso 3: añadir los dos parámetros a `case/cad/params.scad`**

```scad
// APRIETE DE LOS 30 M3, y la arandela de la que sale.
//
// Hasta el 2026-08-24 la instruccion era "apretar hasta marcar, NO hasta
// fisurar" (README) y la spec §11 admitia que "el par maximo antes de fisura
// no esta medido". Treinta tornillos visibles apretados a tacto sobre
// acrilico son treinta puntos de craquelado.
//
// EL NUMERO LO PONE LA ARANDELA, no el tornillo: lo que decide si el PMMA
// craquela es cuanta area reparte la precarga.
//
//   arandela   area      precarga a 10 MPa   par
//   d9         54.5 mm2      545 N           0.33 N*m
//   d12       104.0 mm2     1040 N           0.62 N*m
//   d16       191.9 mm2     1919 N           1.15 N*m   <- esta
//
// Se elige d16 por dos razones que van juntas: es la unica que deja el par
// por encima de 1 N*m, que es donde una llave dinamometrica de 1/4" empieza
// a existir (por debajo hace falta destornillador de precision); y YA ESTA
// EN EL BOM, porque es la arandela ancha de los cuatro ejes de giro. La
// familia de herraje baja de dos arandelas a una.
//
// OJO CON ENGRASAR: el par se convierte en precarga con un coeficiente de
// 0.2 en seco. Con la rosca engrasada baja a ~0.15, o sea que el MISMO par
// mete un 30% mas de precarga y fisura. Los M3 van SECOS.
d_arandela = 16;
par_m3     = 1.0;   // N*m. Techo por arandela: 1.15
```

- [ ] **Paso 4: correr la puerta y verla en VERDE**

Run: `python case/clearance_budget.py`
Expected: línea `apriete: 30 M3 a 1.0 N*m con arandela d16 ...` y `clearance_budget: VERDE`

- [ ] **Paso 5: probar que muerde por los dos lados**

Run: `sed -i 's/^par_m3     = 1.0;/par_m3     = 1.5;/' case/cad/params.scad && python case/clearance_budget.py; sed -i 's/^d_arandela = 16;/d_arandela = 9;/' case/cad/params.scad && python case/clearance_budget.py`
Expected: la primera falla por «aplasta el acrílico»; la segunda falla porque con d9 el techo baja a 0.33 y 1.5 lo pasa. Restaurar `par_m3 = 1.0` y `d_arandela = 16` y verificar VERDE.

- [ ] **Paso 6: corregir el BOM en `case/README.md`**

Sustituir la fila de los M3 y la de la arandela:

```markdown
| Tornillo **M3** botón + tuerca T M3 + **arandela ancha d16** | **30** | las planchas a los largueros: base 10, tapa del valle 5, tapa de remate 5, trasera 10 (2 filas × 5). Entran por la RANURA, no por la punta. **Apriete 1.0 N·m, rosca SECA** — ver `par_m3` |
| Arandela ANCHA d16 | **34** | 30 de los M3 + 4 en los ejes de giro. **No opcional en ninguno de los dos sitios**: es la que baja el apoyo sobre el acrílico de 16.3 MPa (donde el PMMA fluye en semanas) a menos de 10 |
```

Y en el §"Procedimiento del cupón" paso 3, sustituir *«apretar hasta marcar,
NO hasta fisurar; anotar sensación de tope»* por *«apretar a `par_m3` con
destornillador dinamométrico; la sensación de tope ya no es el criterio»*.

- [ ] **Paso 7: commit**

```bash
git add case/cad/params.scad case/clearance_budget.py case/README.md
git commit -m "El apriete deja de ser a tacto: 1.0 N*m, y lo compra la arandela"
```

---

## Tarea 4: La palabra KONDOR llega al taller y es fresable

**Ficheros:**
- Modificar: `case/cad/export.ps1`
- Modificar: `case/check_dxf.py`

**Interfaces:**
- Consume: `kondor_2d()` y el `PART == "kondor_cajeado_2d"` de
  `sam17_case.scad` (ya existen).
- Produce: `case/plans/kondor_cajeado_2d.dxf`.

Dos agujeros abiertos el 2026-08-24, los dos silenciosos:

1. **El fichero no se genera.** `kondor_cajeado_2d` existe como `PART` pero
   no está en la lista de `export.ps1`. El DXF de la trasera **no lleva** el
   relieve porque es cajeado ciego. Mandar hoy = la trasera vuelve sin marca.
2. **La fuente es una dependencia de compilación sin puerta.** Si Franklin
   Gothic Medium no está instalada, OpenSCAD **no falla**: avisa por consola
   y sustituye. El DXF sale, parece bueno, y la pieza es otra.

Y una tercera que nadie miraba: `guarda_fresado()` vigila las ranuras y los
cóncavos, **no la palabra**. El cajeado obliga a que la fresa entre DENTRO
del trazo de cada letra, así que ningún trazo puede medir menos que
`fresa_d`.

- [ ] **Paso 1: escribir la puerta primero, en `case/check_dxf.py`**

```python
def guarda_kondor() -> list[str]:
    """El relieve KONDOR: que la fuente sea la buena y que la fresa entre.

    DOS FALLOS DISTINTOS, los dos silenciosos:

    1. SUSTITUCION DE FUENTE. Si Franklin Gothic Medium no esta instalada,
       OpenSCAD avisa por consola y pone otra: el DXF sale y parece bueno.
       La huella son 10 contornos (K1 O2 N1 D2 O2 R2) y 216.87 x 32.44 mm.

    2. TRAZO MAS FINO QUE LA FRESA. Es un CAJEADO: la fresa tiene que entrar
       dentro del trazo. Se comprueba erosionando la palabra fresa_d/2 y
       contando componentes -- si un trazo medía menos, desaparece y la
       cuenta cambia. Medido el 2026-08-24: Franklin Medium aguanta hasta
       fresa de 4 mm; Bahnschrift y Arial se rompen ahi.
    """
    import numpy as np
    from scipy import ndimage
    from matplotlib.path import Path as MPath
    fallos: list[str] = []
    p = cb.leer_params()
    doc = ezdxf.readfile(PLANS / "kondor_cajeado_2d.dxf")
    polis = [[(x, y) for x, y, *_ in e.get_points()]
             for e in doc.modelspace() if e.dxftype() == "LWPOLYLINE"]
    if len(polis) != 10:
        fallos.append(f"kondor: {len(polis)} contornos, se esperan 10 "
                      f"(K1 O2 N1 D2 O2 R2). La fuente se sustituyo.")
        return fallos
    xs = [q[0] for c in polis for q in c]; ys = [q[1] for c in polis for q in c]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if abs(w - 216.87) > 0.5 or abs(h - 32.44) > 0.5:
        fallos.append(f"kondor: caja {w:.2f} x {h:.2f}, se espera "
                      f"216.87 x 32.44. La fuente se sustituyo o cambio de version.")
    # fresabilidad: rasterizar a 0.25 mm/px y erosionar el radio de la fresa
    ESC = 4.0
    W, H = int(w * ESC) + 20, int(h * ESC) + 20
    img = np.zeros((H, W), dtype=bool)
    yy, xx = np.mgrid[0:H, 0:W]
    px = xx / ESC + min(xs) - 10 / ESC
    py = yy / ESC + min(ys) - 10 / ESC
    dentro = np.zeros((H, W), dtype=int)
    pts = np.column_stack([px.ravel(), py.ravel()])
    for c in polis:
        dentro += MPath(c).contains_points(pts).reshape(H, W).astype(int)
    img = (dentro % 2) == 1          # regla par-impar: contras restan
    r_px = int(round(p["fresa_d"] / 2 * ESC))
    ero = ndimage.binary_erosion(img, ndimage.generate_binary_structure(2, 1),
                                 iterations=r_px)
    # SE CALIBRA SOLO: se comparan los trozos ANTES y DESPUES de erosionar, en
    # vez de contra un numero fijo. Si la palabra cambia (otra fuente, otro
    # texto, otro tamano) la referencia cambia con ella. Un numero magico aqui
    # se rompe en cuanto alguien toque kondor_size.
    _, antes = ndimage.label(img)
    _, despues = ndimage.label(ero)
    if despues != antes:
        fallos.append(f"kondor: la palabra son {antes} trozos y al erosionar el "
                      f"radio de la fresa ({p['fresa_d']/2} mm) quedan {despues}: "
                      f"algun trazo mide menos que la fresa y no se puede vaciar. "
                      f"Sube el cuerpo o cambia a una fuente de mas peso.")
    else:
        print(f"  kondor: 10 contornos, {w:.2f} x {h:.2f} mm, y los {antes} "
              f"trozos sobreviven a la fresa de {p['fresa_d']:g} -- fuente "
              f"correcta y fresable")
    return fallos
```

Registrar en `main()` de `check_dxf.py`, junto a las demás guardas:

```python
    fallos += guarda_kondor()
```

**NO añadir `kondor_cajeado_2d` a `_sobres()`**: esa tabla es de piezas de
corte con envolvente esperada, y el cajeado no es una pieza — es una
operación sobre otra. `main()` itera sobre `SOBRES`, así que quedarse fuera
es lo correcto; quien lo cubre es esta guarda.

- [ ] **Paso 2: correrla y verla en ROJO**

Run: `python case/check_dxf.py`
Expected: `FileNotFoundError` sobre `case/plans/kondor_cajeado_2d.dxf` — el
fichero no existe todavía porque `export.ps1` no lo genera. **Ése es el
fallo que la puerta viene a hacer visible.**

- [ ] **Paso 3: añadir la pieza a `case/cad/export.ps1`**

Sustituir la lista `$piezas` por:

```powershell
# kondor_cajeado_2d NO es una pieza de corte: es el CAJEADO CIEGO del relieve
# de la trasera, que no se recorta en piel_trasera_2d porque no atraviesa. Va
# en su propio fichero porque un DXF 2D no sabe decir "a 4 mm de profundidad"
# -- el mismo caso del chasis, que necesita su plano de plegado. Se manda CON
# la cota de kondor_prof al lado, y el pliego lo dice.
$piezas = "costado_2d","bandeja_base_2d","tapa_valle_2d",
          "remate_sup_2d","piel_trasera_2d","kondor_cajeado_2d","lienzo_2d",
          "chasis_cuerpo_2d","chasis_tapa_2d","chasis_refuerzo_2d"
```

- [ ] **Paso 4: exportar y ver la puerta en VERDE**

Run: `powershell -File case/cad/export.ps1`
Expected: `kondor_cajeado_2d` aparece en la lista de piezas releídas, la
línea `kondor: 10 contornos, 216.87 x 32.44 mm, y las 6 letras sobreviven...`
y `check_dxf: VERDE`.

- [ ] **Paso 5: probar que la puerta caza la sustitución de fuente**

Run: `sed -i 's/KONDOR_FONT = "Franklin Gothic Medium";/KONDOR_FONT = "Comic Sans MS";/' case/cad/sam17_case.scad && powershell -File case/cad/export.ps1; sed -i 's/KONDOR_FONT = "Comic Sans MS";/KONDOR_FONT = "Franklin Gothic Medium";/' case/cad/sam17_case.scad && powershell -File case/cad/export.ps1`
Expected: con la fuente cambiada, `check_dxf` sale en ROJO por caja o por
número de contornos; al restaurarla vuelve a VERDE.

- [ ] **Paso 6: commit**

```bash
git add case/cad/export.ps1 case/check_dxf.py case/plans/kondor_cajeado_2d.dxf
git commit -m "La marca llega al taller: kondor_cajeado_2d se exporta, y su puerta caza fuente y fresa"
```

---

## Tarea 5: Las paticas de goma, con la cota que las hace funcionar

**Ficheros:**
- Modificar: `case/cad/params.scad`
- Modificar: `case/clearance_budget.py`
- Modificar: `case/README.md` (BOM y la tabla de no-confirmados)

**Interfaces:**
- Produce: `flecha_pie` (mm) — lo consume el pliego como requisito de compra.

Decidido por Samuel el 2026-08-24: **gomas, no metal**. Eso **revierte** la
nota del 2026-08-17 en `params.scad` (*«metálicas... no son de goma»*) y
**deja de contradecir la spec §5**, que nunca dejó de decir «pies de goma».
La contradicción de tres documentos se cierra volviendo al que no se movió.

Y hay una cota que decide si la goma sirve o es peor que nada: **cuánto se
hunde**. El toroide excita a 100 Hz; si la frecuencia propia de la pata cae
cerca de ahí, la pata **amplifica** en vez de aislar.

| se hunde | f propia | transmite |
|---|---|---|
| 0.10 mm | 49.8 Hz | 33 % |
| **0.25 mm** | **31.5 Hz** | **11 %** |
| 0.50 mm | 22.3 Hz | 5 % |
| 1.00 mm | 15.8 Hz | 2.5 % |

Con 22.8 N por pata (9.30 kg / 4).

- [ ] **Paso 1: escribir la puerta primero, en `case/clearance_budget.py`**

```python
def guarda_paticas(p: dict[str, float]) -> None:
    """Una goma dura no aisla menos: AMPLIFICA.

    El toroide excita a 100 Hz (#106, magnetostriccion al doble de la red).
    La pata y la masa del case son un muelle: si su frecuencia propia cae
    cerca de 100 Hz, la transmisibilidad se dispara y la mesa recibe MAS
    zumbido del que recibiria con el acrilico desnudo.

    f_propia = 15.76 / sqrt(flecha_mm) es la formula de manual para un
    sistema de un grado de libertad bajo su propio peso.

    Se exige f_propia <= 100/3, o sea flecha >= 0.22 mm: el factor 3 es el
    minimo habitual para que la transmisibilidad baje del 15 %.
    """
    MASA_CASE, F_TOROIDE = 9.30, 100.0
    carga = MASA_CASE * 9.81 / 4
    f_propia = 15.76 / math.sqrt(p["flecha_pie"])
    transmision = 1 / abs((F_TOROIDE / f_propia) ** 2 - 1)
    assert f_propia <= F_TOROIDE / 3, (
          f"flecha_pie = {p['flecha_pie']} mm da f propia {f_propia:.1f} Hz "
          f"contra los {F_TOROIDE:.0f} Hz del toroide: transmite "
          f"{transmision*100:.0f} %. Una goma que se hunde poco NO aisla "
          f"menos, AMPLIFICA. Hace falta >= {(15.76/(F_TOROIDE/3))**2:.2f} mm.")
    print(f"paticas: {carga:.1f} N por pata, se hunden {p['flecha_pie']} mm "
          f"-> f propia {f_propia:.1f} Hz, transmiten {transmision*100:.0f} % "
          f"de los 100 Hz del toroide")
```

Registrar la llamada en `main()`.

- [ ] **Paso 2: correrla y verla en ROJO**

Run: `python case/clearance_budget.py`
Expected: `KeyError: 'flecha_pie'`

- [ ] **Paso 3: sustituir el bloque de paticas en `case/cad/params.scad`**

Reemplazar el comentario y los dos parámetros existentes por:

```scad
// PATICAS: DE GOMA. Samuel, 2026-08-24 -- "prefiero las gomas solamente,
// pero unas gomas serias".
//
// ESTO REVIERTE LA NOTA DEL 2026-08-17 que decia "METALICAS, torneadas... no
// son de goma: eso cambia el BOM y el acabado". Y al revertirla, la spec §5
// DEJA DE ESTAR EQUIVOCADA: nunca dejo de decir "pies de goma bajo la base".
// La contradiccion de tres documentos se cierra volviendo al que no se movio.
//
// LA COTA QUE DECIDE SI SIRVE ES CUANTO SE HUNDE, no la dureza ni el tamano.
// El toroide excita a 100 Hz y la pata es un muelle: si su frecuencia propia
// cae cerca de ahi, AMPLIFICA en vez de aislar.
//
//   se hunde   f propia   transmite
//   0.10 mm     49.8 Hz     33 %
//   0.25 mm     31.5 Hz     11 %    <- esta
//   1.00 mm     15.8 Hz    2.5 %
//
// 0.25 es el minimo que deja la f propia a un tercio de la excitacion, que
// es el criterio de manual. Mas blanda aisla mejor y se bambolea mas.
//
// ES REQUISITO DE COMPRA, NO DE DIBUJO: se exige la curva carga-deformacion
// del fabricante. Una goma que no publica esa curva no es una goma seria.
flecha_pie = 0.25;  // mm bajo 22.8 N. DE HOJA DE DATOS, no estimado
alto_pie   = 10;    // sube de 8: la flecha necesita material donde ocurrir
d_pie      = 20;    // sube de 16: area para no aplastarse permanentemente
```

- [ ] **Paso 4: correr la puerta y verla en VERDE**

Run: `python case/clearance_budget.py`
Expected: `paticas: 22.8 N por pata, se hunden 0.25 mm -> f propia 31.5 Hz, transmiten 11 %` y `clearance_budget: VERDE`

- [ ] **Paso 5: probar que la puerta caza la goma dura**

Run: `sed -i 's/^flecha_pie = 0.25;/flecha_pie = 0.05;/' case/cad/params.scad && python case/clearance_budget.py; sed -i 's/^flecha_pie = 0.05;/flecha_pie = 0.25;/' case/cad/params.scad`
Expected: falla con «NO aisla menos, AMPLIFICA»; al restaurar vuelve a VERDE.

- [ ] **Paso 6: corregir el BOM en `case/README.md`**

Sustituir la fila `Patica metálica torneada` por:

```markdown
| Patica de goma con casquillo roscado | 4 | EPDM o NBR, Shore 45–55 A, d20 × 10. **Se exige curva carga-deformación: ≥ 0.25 mm de flecha con 22.8 N.** Casquillo roscado moldeado — se atornilla, no se pega (el case no lleva juntas irreversibles) |
```

Y **borrar** la fila `Pies de goma | sin fijar` de la segunda tabla, que era
la mitad viva de la contradicción.

- [ ] **Paso 7: commit**

```bash
git add case/cad/params.scad case/clearance_budget.py case/README.md
git commit -m "Las paticas son de goma y la cota que importa es cuanto se hunden"
```

---

## Tarea 6: `case/PLIEGO.md` — el documento que no existe

**Ficheros:**
- Crear: `case/PLIEGO.md`
- Modificar: `case/README.md` (enlazarlo desde §Regenerar todo)

**Interfaces:**
- Consume: `chaflan`, `par_m3`, `d_arandela`, `flecha_pie`, `kondor_prof`
  (Tareas 2–5), y el RFQ (Tarea 1).

Éste es el hueco grande de la revisión adversarial: hay nueve DXF y 563
líneas de README, y **ningún documento que vaya al taller**. Un DXF no dice
material, ni espesor, ni acabado, ni profundidad de cajeado, ni qué cara es
la de fuera. El taller rellena esos huecos con sus supuestos.

- [ ] **Paso 1: escribir `case/PLIEGO.md`**

```markdown
# Pliego de fabricación — cuerpo de acrílico del SAM17

Este documento acompaña a los DXF. **Un DXF solo es media pieza**: lleva la
geometría de corte y no dice material, espesor, acabado ni profundidad.

## 1. Material
- **PMMA COLADO (GS)**, naranja translúcido. **NO extruido** (XT): el
  extruido trae tensión interna de fábrica y craquela.
- Espesores: **8 mm** y **5 mm**. Ver §6 qué pieza en qué espesor.
- Tolerancia de espesor conocida: ±(0.4 + 0.1 × espesor). **Comunicar el
  espesor real medido del lote ANTES de cortar** — hay cotas del diseño
  derivadas de él.

## 2. Proceso
- **Fresado CNC.** No láser: deja canto cónico y microfisura.
- Fresa asumida ⌀3 mm (radio interior 1.5). Avisar si se usa otra.
- Los DXF están a cota final: **el CAM compensa el radio de herramienta**.
  No aplicar sobre-medida.
- Unidades: **milímetros**.

## 3. Acabados — los tres que hacen el producto
- **RECOCIDO (annealing) obligatorio, después de mecanizar y pulir.** El
  fresado deja tensión atrapada en cada agujero y cada canto; sin recocer,
  el PMMA craquela en meses alrededor de los taladros. Indicar temperatura
  y rampa empleadas.
- **Canto visible: PULIDO DIAMANTADO en máquina.** Son ~7.5 m (el contorno
  exterior de las cinco piezas). **PULIDO A LLAMA PROHIBIDO**: mete tensión
  y deshace el recocido.
- **Canto interior** (ranuras, ondas, taladros, ~10 m): tal cual sale de
  fresa. No se pule.
- **CHAFLÁN 0.5 × 45° en toda arista vista**, mecanizado. Incluidas las dos
  esquinas traseras del costado, que van a arista viva por diseño.

## 4. Cajeado ciego — la pieza que el DXF no describe entera
`kondor_cajeado_2d.dxf` **no es un recorte**: es un **vaciado a 4.0 mm de
profundidad** en la **cara exterior** de `piel_trasera_2d`. No atraviesa.
- La palabra debe leerse **del derecho desde fuera**. El DXF está dibujado
  tal como debe verse en la cara exterior.

## 5. Orientación — la trasera tiene cara
`piel_trasera_2d` tiene una cara exterior y otra interior desde que lleva el
cajeado. **La cara exterior es la que lleva el vaciado.** Montada al revés,
el relieve queda hacia dentro.

## 6. Piezas
| DXF | espesor | uds | notas |
|---|---|---|---|
| `costado_2d` | 8 | 2 | canto visible completo, pulido |
| `bandeja_base_2d` | 8 | 1 | |
| `piel_trasera_2d` | 8 | 1 | + `kondor_cajeado_2d` a 4 mm en cara exterior |
| `tapa_valle_2d` | 5 | 1 | |
| `remate_sup_2d` | 8 | 1 | |
| `coupon.dxf` | 8 | 1 | pieza de calibración, sin acabado |

`lienzo_2d.dxf` es solo previsualización de nesteado — **no se corta**.
Las tres piezas `chasis_*` son de **acero** y van a otro taller.

## 7. Limpieza y manipulación (para nosotros, no para el taller)
- **Prohibido alcohol y limpiacristales con amoníaco**: craquelan el PMMA.
  Agua tibia con jabón neutro y paño de microfibra.
- El film protector **se quita al final del montaje**, no al recibir.
- Apriete de los M3: **1.0 N·m con arandela d16, rosca SECA**. Engrasar la
  rosca mete un 30 % más de precarga con el mismo par y fisura.
```

- [ ] **Paso 2: enlazarlo desde `case/README.md`**

En §"Regenerar todo", después del bloque de comandos:

```markdown
Lo que se manda al taller **no son solo los DXF**: van con
[`PLIEGO.md`](PLIEGO.md), que lleva material, procesos, acabados y qué cara
es la exterior. Un DXF suelto es media pieza.
```

- [ ] **Paso 3: llevar orientación y film al orden de ensamblaje**

El pliego se lo dice al taller; el orden de ensamblaje se lo dice a quien
monta, que eres tú. En `case/README.md`, §"Orden de ensamblaje", sustituir
el paso 7 y añadir un paso 10:

```markdown
7. **Trasera** — UNA plancha de 8 mm, EMPOTRADA, 10 M3 a tuerca T en las dos
   filas de los largueros traseros, **a 1.0 N·m con arandela d16 y rosca
   seca**. Va después de los largueros porque la tuerca T vive dentro de la
   ranura. **ATENCIÓN A LA CARA**: esta plancha ya no es simétrica — el
   cajeado de KONDOR va en la cara EXTERIOR. Montada al revés, el relieve
   queda mirando al interior y la palabra se lee al revés desde fuera.

10. **Quitar el film protector** — al final, no al recibir. El acrílico llega
    con las dos caras protegidas y se raya durante el montaje: al deslizarlo
    por la mesa, al apoyar una herramienta, al girar una pieza sobre otra.
    El film es lo que lo evita, y solo sirve si sigue puesto.
```

- [ ] **Paso 4: verificar que las cotas del pliego coinciden con el modelo**

Run: `python case/clearance_budget.py | grep -E "chaflan|apriete|paticas"`
Expected: los valores impresos (0.5 mm, 1.0 N·m / d16, 0.25 mm) son los
mismos que están escritos en el pliego. Si no, **el pliego está mal, no el
modelo**.

- [ ] **Paso 5: commit**

```bash
git add case/PLIEGO.md case/README.md
git commit -m "El pliego: lo que un DXF no sabe decir, escrito para el taller"
```

---

## Lo que NO es tarea: lo que espera a la muestra física

Estas decisiones están **bloqueadas por material real** y no se cierran
escribiendo. Van como issues al mergear, con la evidencia de esta sesión:

- **#98 — espesor real.** Medir con calibre en 5 puntos y meter el valor en
  `t_acrilico`/`t_base`/`t_cheek`/`t_piel`. **Y re-derivar `hol_piel`**: hoy
  0.15 mm/lado da una junta pareja *si* la plancha mide 8; con ±1.2 puede
  quedar 0.15 de un lado y 1.3 del otro. Es un problema de acabado antes que
  de montaje, y así no está escrito en ningún sitio.
- **#97 — cara del Z-Rail.** Calibre sobre el riel. Los dos valores pasan la
  puerta; la diferencia son 4.8 mm de panel hundido.
- **Canto diamantado en el naranja real.** «Pulido» en un traslúcido no se
  parece a «pulido» en un opaco, y eso no lo decide un render.
- **Profundidad del cajeado.** 4 mm contra 6 mm en el naranja: hoy el
  relieve se lee bien en el ahumado y pálido en el naranja.
- **Los tres supuestos del chasis de acero** (`t_chapa`, `radio_doblez`,
  `k_factor`): el desarrollo del patrón plano depende de los tres y los
  fija el taller de plegado, no nosotros.

## La decisión que sigue abierta y no la cierra este plan

**La tapa del valle.** Es la plancha más débil del case (fluye a ~100 N de
mano contra 155 de la siguiente), es la superficie horizontal donde va la
mano al parchear, y **subirla de espesor está bloqueado**: a 6 mm la fila de
abajo pasa de abrir 180° a 39.5° porque la tapa invade el barrido del riel.

Las tres salidas medidas, para decidir aparte:
1. **Aluminio de 3 mm** en vez de acrílico de 5: fluye a ~450 N, es más fina
   así que *gana* 2 mm de barrido, y mata la única línea de BOM de 5 mm.
   Cuesta el tono: es la única cara horizontal que se ve de pie.
2. **Crecer hacia arriba** en vez de hacia abajo: no toca el barrido, deja
   de ser enrasada.
3. **Aceptarlo y escribirlo**: es una tapa, no un escalón. Hoy no está dicho.
