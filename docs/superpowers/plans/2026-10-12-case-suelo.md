# El suelo: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sustituir la tabla de nogal por una base de chapa 6082-T6 de 3 mm bajo los anillos. La base amarra los anillos, recibe la nariz, el talón, las patas y el chasis, y es entrada de aire. Las puertas del case pasan a medirla.

**Architecture:** La pieza conserva sus nombres de código (`bandeja_base`, `bandeja_base_2d`, `t_base`), y cambian su geometría y su material. Lo nuevo vive en las gemelas de siempre: `clearance_budget.py` decide y `sam17_case.scad` dibuja. `check_dxf.py` cruza el DXF contra el budget:
- el campo de agujeros: `_campo_base()` en el budget y `campo_base()` en el `.scad`;
- el aire: `_tiro()` resuelve la chimenea con la base como camino en serie;
- la flexión de la base: un emparrillado en `numpy`.

**Tech Stack:** OpenSCAD (geometría y DXF), Python 3 (budget, `check_dxf`, `numpy` con import diferido como el de `persiana.py`, `ezdxf`), Blender 5.0 (renders), PowerShell (`export.ps1`).

**Spec:** `docs/superpowers/specs/2026-10-12-case-suelo-design.md`, firmado el 12-10 en el acta 4: D-T1 patas de 10, D-T2 tornillos del suelo desde abajo. El censo de la junta (212 entradas) está en el scratchpad de la sesión del 12-10 (`tool-results/toolu_01PovtAfFcze7pBZVkuK6yAC.txt`). Se hizo sobre la versión 1, que sacaba el chasis: todas sus entradas «Remove» del chasis quedan **fuera** de este plan.

## Global Constraints

- **Nombres.** La pieza conserva `bandeja_base`, `bandeja_base_2d` y `t_base`. «Suelo» ya nombra cinco cosas en el código (censo a.19: el plano y = 0, el tramo de abajo del anillo, los localizadores de la persiana, `suelo_persiana` y filtros por cadena). Los textos para Samuel la llaman «la base» o «el suelo».
- **La chapa.** 6082-T6 (`RP02_6082_T6` = 240), anodizada en negro, `t_base` = 3. En mundo va de x = `chaflan_nariz` a `fondo − chaflan_nariz`, de z = 0 a `ancho_total` y de y = −`t_base` a 0. Sin vuelo.
- **Coordenadas locales de `bandeja_base_2d`.** x local = z del mundo, y local = x del mundo, sin desplazamiento. La transformación 3D es una rotación (determinante +1): `multmatrix([[0,1,0,0],[0,0,1,-t_base],[1,0,0,0],[0,0,0,1]])`.
- **El chasis no se toca.** Se quedan su bloque de `params.scad`, sus módulos, `guarda_chasis()`, `chasis_agujeros()`, sus tres DXF, `plano_chasis.py`, `assembly_acero()` y la v3 de la fuente. Lo único que cambia es a qué se atornilla: de la tabla a la base, en las mismas cuatro posiciones.
- **D-T1:** patas de 10 (`alto_pie` = 10, `d_pie` = 20), en las mismas posiciones.
- **D-T2:** los M4 de la nariz y del talón entran desde abajo, por agujeros de paso de la base (`d_M4_paso`), a tuercas CLS-M4 (`pem_cls_m4`) prensadas en sus pies. El M4 queda a `max(1.5·d_M4_paso, pem_borde)` del canto libre del pie. **Los pies no crecen** (Task 3, ruling sobre el §3.4 del papel).
- **Supuestos declarados, con su HUECO:**
  - `pem_borde` = 7,0 y los agujeros de PEM (H4);
  - el canal bajo la base, 60 estimado y 120 pesimista (H2);
  - la hoja de la pata (H3).
- **Las cifras del aire** las calcula `_tiro()`. `case/cad/suelo.py` solo las imprime.
- **Puertas.**
  - Antes de cada commit que toque `case/`: `sh .githooks/pre-push < /dev/null` en verde.
  - Tarda unos 2,5 min, más que el timeout de la herramienta: se corre en segundo plano y se lee su salida.
  - Cada guarda nueva entra en `main()`: las puertas viven en dos sitios (memoria «Puertas en dos sitios»).
- **Texto de commits, PR e issues.** En español, describe el cambio y su porqué técnico. Ninguna línea de atribución de IA, y nada de proceso ni de audiencia.
- **Edición.** Si el texto lleva barra invertida, se usa la herramienta de edición: en un heredoc del Bash, `\\` llega simple.

## Review Focus

1. **Un agujero del campo bajo el chasis o pegado a un inserto.**
   - La L se deriva de la huella del chasis y de los pies.
   - Si alguien mueve el chasis (`chasis_margen_bandeja`) o una tuerca (`pem_borde`), el campo tiene que seguirlo, y `guarda_campo_base()` tiene que poner rojo lo que no quepa.
   - Lo pinza el canario de la Task 1.
2. **Las gemelas del campo se separan.**
   - Si `campo_base()` del `.scad` y `_campo_base()` del budget dejan de coincidir, el DXF tiene otros agujeros que los que cuenta el aire.
   - `guarda_bandeja_base()` compara la cuenta y las posiciones (Task 3).
3. **El aire.**
   - Sin la base, el aire tiene que dar exacto lo de hoy.
   - El HUECO de los costados tiene que seguir publicándose con el pesimista.
   - Lo pinzan `autocomprobacion_base()` y el canario del aire (Task 2).
4. **Una base más fina.** Con `t_base` = 2 la flexión tiene que ponerse roja: Elke da fluencia en el puente del campo. Canario de la Task 4.
5. **El M4 desde abajo.** Si `pem_borde` no cabe entre el doblez y el canto libre del pie, `guarda_talon()` tiene que ponerse rojo. Canario de la Task 5.

---

### Task 1: El campo de agujeros de la base

**Files:**
- Modify: `case/cad/params.scad` (bloque nuevo tras `t_base`, hacia la l.1070)
- Modify: `case/clearance_budget.py`:
  - helpers nuevos tras `_m5_tabla_x()`, hacia la l.4833;
  - una guarda y su canario;
  - las llamadas en `main()`, hacia las l.6430-6500.

**Interfaces:**
- Produces:
  - `_zonas_campo_base(p) -> list[tuple[float, float, float, float]]`: (x0, x1, z0, z1) en mundo, la L.
  - `_campo_base(p) -> list[tuple[float, float]]`: centros (x, z) en mundo.
  - `_m4_pie_borde(p) -> float`: distancia del M4 al canto libre del pie de nariz y talón.
  - `_taladros_base(p) -> list[tuple[float, float, float, str]]`: (x, z, d, tipo) en mundo, con `tipo` en {"M5", "M4 nariz", "M4 talon", "FH pata", "M4 chasis"}.
  - `guarda_campo_base(p) -> None`.
  - `canario_campo_base(p) -> None`.

- [ ] **Step 1: Escribir el canario (rojo)**

En `clearance_budget.py`, después de `_m5_tabla_x()`:

```python
def canario_campo_base(p: dict[str, float]) -> None:
    """Autocomprobacion ROJA de guarda_campo_base(): con el puente mas fino que
    la chapa, o con la distancia de un inserto mayor que la orilla que lo
    separa del campo, la puerta tiene que saltar y por SU razon; y con los
    parametros de verdad, callar."""
    for cambios, clave in (({"base_paso": p["base_agujero"] + p["t_base"] - 0.5}, "puente"),
                           ({"pem_borde": 25.0}, "inserto")):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                guarda_campo_base({**p, **cambios})
        except AssertionError as e:
            assert clave in str(e), (
                f"canario del campo: con {cambios} guarda_campo_base() salto, "
                f"pero por otra razon ('{str(e)[:80]}...')")
            continue
        raise AssertionError(
            f"canario del campo NO disparo con {cambios}: guarda_campo_base() "
            f"lo deja pasar -- no confiar en su VERDE")
    with contextlib.redirect_stdout(io.StringIO()):
        guarda_campo_base(dict(p))
```

- [ ] **Step 2: Correrlo y verlo fallar**

Run: `cd case && python -c "import clearance_budget as cb; cb.canario_campo_base(cb.leer_params())"`
Expected: FAIL, primero con `KeyError: 'base_agujero'` (el parámetro no existe) o `NameError: guarda_campo_base`.

- [ ] **Step 3: Los parámetros**

En `case/cad/params.scad`, justo después de la línea `t_base     = 30;` y su bloque (hacia la l.1066; el valor de `t_base` cambia en la Task 3, no aquí), se añade:

```
// EL CAMPO DE AGUJEROS DE LA BASE (papel del suelo, 2026-10-12, sec.3.2 y 5).
// Ø5 al tresbolillo cada 8, el patron Rv 5-8: un 35,4 % abierto, y el puente
// entre agujeros mide 3, una vez el espesor. La regla de 0,8 veces es la del
// PMMA; para aluminio cortado a laser se pide 1 vez (Elke). El campo es una L
// que esquiva la huella del chasis y deja base_orilla libre junto al canto de
// los anillos, los pies de nariz y talon y el chasis. GEMELAS: campo_base()
// aqui y _campo_base() en el budget; check_dxf las cruza.
base_agujero = 5;
base_paso    = 8;
base_orilla  = 10;
// LOS INSERTOS DE PRESION (papel del suelo, sec.3.4). Van de acero o de
// inoxidable, nunca de la serie de aluminio: esa pide chapa de HB <= 89 y el
// 6082-T6 ronda 95. Se prensan despues de anodizar, y sus agujeros se cortan
// a cota de catalogo sobre la pieza anodizada. SUPUESTOS DE MEMORIA hasta la
// hoja de PEM (HUECO H4 del papel).
pem_cls_m4   = 5.4;   // tuerca CLS-M4, en los pies de nariz y talon (D-T2)
pem_fh_m4    = 4.0;   // esparrago FH-M4, en la base, para las patas
pem_borde    = 7.0;   // del centro de un inserto al canto o al borde de otro agujero
// El paso del M5 de los anillos en la base: medio milimetro de juego por lado
// para casar dos anillos mecanizados por separado. Los seis van redondos: la
// veta de la tabla se fue con ella.
d_M5_base    = 6.0;
```

- [ ] **Step 4: Las funciones**

En `clearance_budget.py`, tras `_m5_tabla_x()` y antes del canario:

```python
def _m4_pie_borde(p: dict[str, float]) -> float:
    """Del canto libre del pie de nariz y talon al centro de su M4. Era 1.5 D;
    con D-T2 el M4 rosca en una tuerca de presion prensada en el pie, y la
    tuerca pide pem_borde al canto (papel del suelo, sec.3.4)."""
    return max(1.5 * p["d_M4_paso"], p["pem_borde"])


def _zonas_campo_base(p: dict[str, float]) -> list[tuple[float, float, float, float]]:
    """La L donde pueden ir los agujeros de la base, en mundo: (x0, x1, z0, z1).
    A va a la izquierda del chasis, de delante a atras; B, delante del chasis.
    Fuera quedan el canto de los anillos, los pies de nariz y talon y la huella
    del chasis, cada uno con base_orilla de margen. GEMELA de
    zonas_campo_base() en el .scad."""
    o = p["base_orilla"]
    c = _chasis(p)
    x0 = p["chaflan_nariz"] + p["nariz_pie"] + o
    x1 = _talon(p)["x_pie"] - o
    z0 = p["t_anillo"] + o
    z1 = p["ancho_total"] - p["t_anillo"] - o
    z_ch = (p["t_anillo"] + perfil(p)["ancho_util"] - p["chasis_margen_bandeja"]
            - c["tapa_x"])
    x_ch = _x_chasis_frente(p)
    return [(x0, x1, z0, z_ch - o), (x0, x_ch - o, z_ch - o, z1)]


def _campo_base(p: dict[str, float]) -> list[tuple[float, float]]:
    """Los centros (x, z) de los agujeros del campo, en mundo. Una sola red al
    tresbolillo anclada en la esquina de la L, que se queda con los agujeros
    que caben enteros en alguna de las dos zonas. Dos redes, cada una con su
    origen, dejarian en la costura un puente mas fino que el resto. GEMELA de
    campo_base() en el .scad: misma red, mismo filtro."""
    zonas = _zonas_campo_base(p)
    d, s = p["base_agujero"], p["base_paso"]
    r, fila = d / 2, s * math.sqrt(3) / 2
    x0, x1 = min(q[0] for q in zonas), max(q[1] for q in zonas)
    z0, z1 = min(q[2] for q in zonas), max(q[3] for q in zonas)
    ni = math.floor((x1 - x0 - d) / fila + 1e-9)
    nj = math.floor((z1 - z0 - d) / s + 1e-9)
    return [(x, z) for i in range(ni + 1) for j in range(nj + 1)
            for x, z in [(x0 + r + i * fila, z0 + r + (i % 2) * s / 2 + j * s)]
            if any(a + r - 1e-9 <= x <= b - r + 1e-9
                   and c + r - 1e-9 <= z <= e - r + 1e-9
                   for a, b, c, e in zonas)]


def _taladros_base(p: dict[str, float]) -> list[tuple[float, float, float, str]]:
    """Todo taladro de fijacion de la base, en mundo: (x, z, d, tipo). Los 6 M5
    de los anillos, los 3 + 3 M4 de nariz y talon (de paso: D-T2 los mete desde
    abajo a la tuerca de su pie), las 4 FH de las patas y los 4 M4 del chasis.
    Lo leen guarda_campo_base() y guarda_bandeja_base() en check_dxf."""
    nz, tl = _nariz(p), _talon(p)
    out = [(x, z, p["d_M5_base"], "M5") for x in _m5_tabla_x(p)
           for z in (p["t_anillo"] / 2, p["ancho_total"] - p["t_anillo"] / 2)]
    out += [(nz["m4_x"], z, p["d_M4_paso"], "M4 nariz") for z in nz["m4_z"]]
    out += [(tl["m4_x"], z, p["d_M4_paso"], "M4 talon") for z in tl["m4_z"]]
    out += [(x, z, p["pem_fh_m4"], "FH pata")
            for x in (p["alto_frontal"] / 2 + p["d_pie"] / 2,
                      tl["x_chaflan"] - p["talon_pie"] / 2)
            for z in (p["d_pie"] / 2, p["ancho_total"] - p["d_pie"] / 2)]
    out += [(yl, xl, p["d_M4_paso"], "M4 chasis") for xl, yl in _chasis_tornillos_tabla(p)]
    return out


def guarda_campo_base(p: dict[str, float]) -> None:
    """El campo de agujeros de la base: que respire lo que el aire cuenta sin
    debilitar la chapa ni pisar un inserto (papel del suelo, sec.3.2 y 5).

      1. El puente entre agujeros vecinos (la red es de paso base_paso en las
         tres direcciones) mide al menos el espesor: con menos, la mano apoyada
         plastifica el borde del agujero (Elke).
      2. Ningun agujero del campo queda a menos de pem_borde de un taladro de
         fijacion, de centro de taladro a canto de agujero.

    La huella del chasis no se asevera: la L se deriva de ella, y un aserto
    sobre lo que la propia construccion garantiza no puede fallar."""
    puente = p["base_paso"] - p["base_agujero"]
    assert puente >= p["t_base"] - 1e-9, (
        f"el puente del campo de la base mide {puente:.2f} mm (paso "
        f"{p['base_paso']:g} - agujero {p['base_agujero']:g}) y la chapa "
        f"{p['t_base']:g}: con la mano apoyada el borde del agujero plastifica. "
        f"Se pide un puente de una vez el espesor")
    campo = _campo_base(p)
    r = p["base_agujero"] / 2
    peor = min((math.hypot(x - tx, z - tz) - r, tipo)
               for x, z in campo for tx, tz, _d, tipo in _taladros_base(p))
    assert peor[0] >= p["pem_borde"] - 1e-9, (
        f"un agujero del campo queda a {peor[0]:.2f} mm de un taladro de "
        f"{peor[1]} y el inserto pide {p['pem_borde']:g} (pem_borde): sube "
        f"base_orilla o aparta el campo")
    abierto = len(campo) * math.pi * r * r
    print(f"base: {len(campo)} agujeros de {p['base_agujero']:g} cada "
          f"{p['base_paso']:g}, {abierto:.0f} mm2 abiertos; puente {puente:.1f} "
          f"contra {p['t_base']:g} de chapa; el mas cercano a un inserto, a "
          f"{peor[0]:.1f} mm ({peor[1]})")
```

En `main()`, junto a las demás guardas de geometría y antes de `guarda_aire(p)`:

```python
    guarda_campo_base(p)
```

Y junto a los demás canarios (donde corre `canario_techo(p)`):

```python
    canario_campo_base(p)
```

- [ ] **Step 5: Correrlo y verlo pasar**

Run: `cd case && python -c "import clearance_budget as cb; p = cb.leer_params(); cb.canario_campo_base(p); cb.guarda_campo_base(p)"`

Expected: PASS. Imprime `base: N agujeros de 5 cada 8, A mm2 abiertos`, con N entre 1 000 y 1 200 y A entre 20 000 y 23 500. La L sale algo más grande que en `suelo.py`, porque ya no lleva el margen de 8,5 que sumaba aquel guion. Con los pies de hoy, el más cercano a un inserto queda a ≥ 15 mm.

Nota: hasta la Task 3, `_chasis_tornillos_tabla()` todavía suma el vuelo de la tabla. Los M4 del chasis salen desplazados 40 mm y la distancia mínima puede venir de ellos. Es correcto: la Task 3 los coloca.

- [ ] **Step 6: Commit**

```bash
git add case/cad/params.scad case/clearance_budget.py
git commit -m "El campo de agujeros de la base y su puerta: Ø5 cada 8 en una L que esquiva el chasis" -m "_campo_base() reparte una sola red al tresbolillo en la L que dejan los anillos, los pies de nariz y talón y la huella del chasis. guarda_campo_base() exige un puente de al menos el espesor y pem_borde hasta cada taladro de fijación, y su canario la rompe por las dos razones."
```

---

### Task 2: El aire con la base

**Files:**
- Modify: `case/clearance_budget.py`:
  - `_huecos`/`_tiro`, hacia las l.2650-2710: constantes nuevas y solver;
  - `_envolvente_m2`, hacia la l.2554;
  - `guarda_aire`, hacia las l.2730-2850;
  - `canario_techo`, el bloque del aire, hacia las l.3485-3546;
  - `main()`: la autocomprobación.
- Modify: `case/cad/persiana.py:290-306` (los escenarios del aire).
- Rewrite: `case/cad/suelo.py`, que pasa a imprimir lo que calcula el budget.

**Interfaces:**
- Consumes: `_campo_base(p)` (Task 1).
- Produces:
  - `CANAL_BASE = 60.0`, `CANAL_BASE_PESIMISTA = 120.0` y `MU_AIRE = 1.8e-5`.
  - `_camino_base(p, costados=2, canal=CANAL_BASE) -> dict`, con las claves `a_base`, `w`, `largo` y `h`.
  - `_tiro(p, cd=CD_TIRO, costados=2, trasera=True, base=True, canal=CANAL_BASE) -> dict`, con las claves `huecos`, `yn`, `a_entra`, `a_sale`, `a_base`, `q_base`, `p_evacuada`, `p_pared`, `dt` y `falta`. **Ya no devuelve `S` ni `k`.**
  - `_tiro_pesimista(p, **kw) -> dict`, que es `_tiro` con `CD_TIRO_PESIMISTA` y `CANAL_BASE_PESIMISTA`.
  - `_potencia_a(p, dt, cd=CD_TIRO, costados=2, trasera=True, base=True, canal=CANAL_BASE) -> float`: los W que la chimenea evacúa con un salto `dt`.
  - `autocomprobacion_base() -> None`.

- [ ] **Step 1: La autocomprobación (rojo)**

En `clearance_budget.py`, después de `autocomprobacion_plano_neutro()`:

```python
def autocomprobacion_base() -> None:
    """La chimenea con el camino de la base tiene que caer en las dos cuentas
    que ya se conocen. Sin base, la forma cerrada de toda la vida: P = k dT^1.5,
    con S de _plano_neutro(). Y con el canal sin roce, la rendija y los
    agujeros en serie, que son un orificio equivalente a_ef = (a1^-2 +
    a2^-2)^-1/2 metido como un hueco mas a y = 0 (papel del suelo, sec.5)."""
    p = leer_params()

    def cerrada(hs, cd):
        _yn, s = _plano_neutro(hs)
        k = (RHO_AIRE * CP_AIRE * cd * math.sqrt(2 * G / T_AMB)
             * s * 1e-6 * math.sqrt(1e-3))
        return (p["potencia_disipada"] / k) ** (2 / 3)

    for cd in (CD_TIRO, CD_TIRO_PESIMISTA):
        for costados in (2, 1):
            a = _tiro(p, cd, costados, base=False)["dt"]
            b = cerrada(_huecos(p, costados), cd)
            assert abs(a - b) < 1e-6 * b, (
                f"autocomprobacion de la base: sin base el solver da {a:.6f} K "
                f"y la forma cerrada {b:.6f} (C_D {cd}, {costados} costados)")
    cam = _camino_base(p, canal=0.0)
    a_ef = 1 / math.sqrt(1 / (cam["w"] * cam["h"]) ** 2 + 1 / cam["a_base"] ** 2)
    a = _tiro(p, canal=0.0)["dt"]
    b = cerrada(_huecos(p) + [(0.0, a_ef)], CD_TIRO)
    assert abs(a - b) < 1e-6 * b, (
        f"autocomprobacion de la base: con el canal sin roce el solver da "
        f"{a:.6f} K y el orificio equivalente {b:.6f}")
```

En `main()`, junto a `autocomprobacion_plano_neutro()`:

```python
    autocomprobacion_base()
```

- [ ] **Step 2: Verla fallar**

Run: `cd case && python -c "import clearance_budget as cb; cb.autocomprobacion_base()"`
Expected: FAIL con `TypeError: _tiro() got an unexpected keyword argument 'base'`.

- [ ] **Step 3: El solver**

En `clearance_budget.py`, justo antes de `def _tiro`, se añaden las constantes y cinco funciones:

```python
# EL CANAL BAJO LA BASE (papel del suelo, sec.5). Es lo que el aire corre por
# el hueco de alto_pie entre la chapa y la mesa hasta el campo de agujeros. El
# flujo de verdad es 2D y converge; aqui es un canal solo, de ancho la rendija
# libre y de este largo. 60 es la estimacion: casi todo el perimetro queda a
# 25-30 mm de un agujero, y el tramo de atras a la derecha a unos 200, debajo
# del chasis. 120 es la pesimista, que va con CD_TIRO_PESIMISTA. SUPUESTO: se
# mide en la primera unidad (HUECO H2 del papel).
CANAL_BASE = 60.0
CANAL_BASE_PESIMISTA = 120.0
MU_AIRE = 1.8e-5          # Pa s, aire a ~30 C


def _camino_base(p: dict[str, float], costados: int = 2,
                 canal: float = CANAL_BASE) -> dict:
    """La entrada por la base, en serie: la rendija que dejan las patas en el
    perimetro de la chapa, el canal laminar de alto_pie y los agujeros del
    campo. Cada pata tapa su diametro de rendija, y una pared contra un costado
    tapa tambien el tramo de ese costado."""
    largo = fondo(p) - 2 * p["chaflan_nariz"]
    libre = (2 * (p["ancho_total"] + largo) - 4 * p["d_pie"]
             - (2 - costados) * (largo - 2 * p["d_pie"]))
    return {"a_base": len(_campo_base(p)) * math.pi * p["base_agujero"] ** 2 / 4,
            "w": libre, "largo": canal, "h": p["alto_pie"]}


def _caudal_base(dp: float, cd: float, a_base: float, w: float, largo: float,
                 h: float) -> float:
    """m3/s que suben por la base con dp Pa de tiro a y = 0:
        dp = rho/2 (Q / (C_D A_r))^2 + 12 mu L Q / (W h^3) + rho/2 (Q / (C_D A_b))^2
    La rendija y los agujeros son orificios; el canal, Poiseuille entre placas."""
    if dp <= 0 or a_base <= 0:
        return 0.0
    a = RHO_AIRE / 2 * (1 / (cd * w * h * 1e-6) ** 2 + 1 / (cd * a_base * 1e-6) ** 2)
    b = 12 * MU_AIRE * largo * 1e-3 / (w * 1e-3 * (h * 1e-3) ** 3)
    return (-b + math.sqrt(b * b + 4 * a * dp)) / (2 * a)


def _caudales(hs, cd: float, camino: dict | None, yn: float,
              dt: float) -> tuple[float, float]:
    """(entra, sale) en m3/s con el plano neutro en yn mm y el salto dt K."""
    g = RHO_AIRE * G * dt / T_AMB * 1e-3          # Pa por mm de altura
    entra = sale = 0.0
    for y, a in hs:
        q = cd * a * 1e-6 * math.sqrt(2 * g * abs(y - yn) / RHO_AIRE)
        if y < yn:
            entra += q
        else:
            sale += q
    if camino:
        entra += _caudal_base(g * yn, cd, **camino)
    return entra, sale


def _neutro(hs, cd: float, camino: dict | None, dt: float) -> float:
    """El plano neutro por balance de masa. Con la base deja de ser independiente
    de dT, porque el canal es lineal y los orificios no."""
    lo, hi = min(0.0, min(y for y, _ in hs)), max(y for y, _ in hs)
    for _ in range(50):
        yn = (lo + hi) / 2
        entra, sale = _caudales(hs, cd, camino, yn, dt)
        lo, hi = (lo, yn) if entra > sale else (yn, hi)
    return (lo + hi) / 2


def _potencia_con(hs, cd: float, camino: dict | None, dt: float) -> float:
    """W que la chimenea evacua con un salto de dt K."""
    yn = _neutro(hs, cd, camino, dt)
    return RHO_AIRE * CP_AIRE * _caudales(hs, cd, camino, yn, dt)[1] * dt
```

Y se reescribe `_tiro()` entero. Se conserva su docstring con un párrafo nuevo arriba, y se le quitan las frases sobre `k` y `S`:

```python
def _tiro(p: dict[str, float], cd: float = CD_TIRO, costados: int = 2,
          trasera: bool = True, base: bool = True,
          canal: float = CANAL_BASE) -> dict:
    """La chimenea del case: el plano neutro, lo que entra y lo que sale, el
    salto termico y lo que evacua al techo.

    DESDE EL PAPEL DEL SUELO (2026-10-12) LA BASE ES UN CAMINO DE ENTRADA EN
    SERIE (_camino_base()): rendija de las patas, canal laminar y agujeros. Con
    un termino lineal la chimenea deja de ser P = k dT^1.5 y se resuelve con
    dos bisecciones: el plano neutro por masa a cada dT (_neutro()) y dT por
    energia. Sin base (base=False) da la forma cerrada de antes al millonesimo
    (autocomprobacion_base()).

    [aqui sigue el docstring de hoy, desde «FUE EN SERIE HASTA EL 2026-10-12»,
    sin las frases que hablan de S y de k como salida]"""
    hs = _huecos(p, costados, trasera)
    camino = _camino_base(p, costados, canal) if base else None
    techo = p["salto_termico_max"]
    lo, hi = 1e-3, 500.0
    for _ in range(50):
        dt = (lo + hi) / 2
        lo, hi = (dt, hi) if _potencia_con(hs, cd, camino, dt) < p["potencia_disipada"] else (lo, dt)
    dt = (lo + hi) / 2
    yn = _neutro(hs, cd, camino, dt)
    g = RHO_AIRE * G * dt / T_AMB * 1e-3
    p_evacuada = _potencia_con(hs, cd, camino, techo)
    return {"huecos": hs, "yn": yn,
            "a_entra": sum(a for y, a in hs if y < yn),
            "a_sale": sum(a for y, a in hs if y > yn),
            "a_base": camino["a_base"] if camino else 0.0,
            "q_base": _caudal_base(g * yn, cd, **camino) if camino else 0.0,
            "p_evacuada": p_evacuada,
            "p_pared": U_PARED_W_M2K * _envolvente_m2(p) * techo,
            "dt": dt,
            "falta": p["potencia_disipada"] / p_evacuada}


def _tiro_pesimista(p: dict[str, float], **kw) -> dict:
    """El pesimista junta los dos supuestos pesimistas: C_D 0.55 y el canal de
    120 bajo la base."""
    return _tiro(p, CD_TIRO_PESIMISTA, canal=CANAL_BASE_PESIMISTA, **kw)


def _potencia_a(p: dict[str, float], dt: float, cd: float = CD_TIRO,
                costados: int = 2, trasera: bool = True, base: bool = True,
                canal: float = CANAL_BASE) -> float:
    """W que la chimenea evacua con un salto de dt K: la inversa de _tiro().
    Con la base ya no hay k que elevar a 1.5, asi que los canarios que derivan
    una carga del techo pasan por aqui."""
    hs = _huecos(p, costados, trasera)
    camino = _camino_base(p, costados, canal) if base else None
    return _potencia_con(hs, cd, camino, dt)
```

`_envolvente_m2()` (hacia la l.2554): el aparato va sobre patas, así que se deja de restar el suelo. El docstring y la última línea quedan así:

```python
def _envolvente_m2(p: dict[str, float]) -> float:
    """Envolvente exterior del case, con el suelo. Hasta el papel del suelo
    (2026-10-12) restaba el suelo porque la tabla apoyaba en la mesa y no
    convectaba; la base de chapa va sobre patas, con aire debajo. DERIVADA del
    perfil (perimetro x ancho + las dos mejillas), no parametro."""
    V = _vertices(p)
    n = len(V)
    per = sum(math.dist(V[i], V[(i + 1) % n]) for i in range(n))
    mejilla = abs(sum(V[i][0] * V[(i + 1) % n][1] - V[(i + 1) % n][0] * V[i][1]
                      for i in range(n))) / 2.0
    return (per * p["ancho_total"] + 2 * mejilla) * 1e-6
```

- [ ] **Step 4: Ver pasar la autocomprobación**

Run: `cd case && python -c "import clearance_budget as cb; cb.autocomprobacion_base(); import time; p = cb.leer_params(); t0 = time.time(); t = cb._tiro(p); print(round(t['dt'], 2), round(cb._tiro_pesimista(p)['dt'], 2), round(time.time() - t0, 1), 's')"`

Expected: PASS.
- Imprime un salto entre 13,8 y 14,6 K y un pesimista entre 15,4 y 16,4. Son del orden del papel: 14,33 y 16,26, con 20 000 mm². Aquí el campo abre algo más (Task 1).
- Las dos llamadas tardan menos de 3 s en total.
- Si pasa de 5 s, se bajan las iteraciones de 50 a 40: 500·2^-40 sigue siendo 5·10^-10 K.

- [ ] **Step 5: `guarda_aire()`, con los HUECOS en el pesimista**

En `guarda_aire()`:
1. Al docstring se le añade al final:
   ```
       Y DESDE EL PAPEL DEL SUELO (2026-10-12) LA BASE RESPIRA. El aire entra
       tambien por la base, en serie con la rendija de las patas y el canal de
       debajo (_camino_base()). Los dos HUECOS se juzgan con el pesimista, que
       es C_D 0.55 con el canal de 120: con la base, el nominal de un costado
       tapado pasa y el pesimista no, y juzgarlo con el nominal lo callaba en
       silencio (papel del suelo, sec.5).
   ```
2. El primer `print` gana la base:
   ```python
       print(f"aire: plano neutro a {t['yn']:.0f} mm; por debajo entran "
             f"{t['a_entra']:.0f} mm2 de huecos y los {t['a_base']:.0f} de la "
             f"base, y por encima salen {t['a_sale']:.0f}, en {len(t['huecos'])} "
             f"huecos: las franjas de las dos persianas, la rejilla baja de la "
             f"trasera, la rendija del alero y las ondas")
   ```
3. El mensaje del aserto deja de prometer área en proporción, porque con el canal no escala así:
   ```python
       assert t["dt"] <= techo + 1e-9, (
           f"el case sube {t['dt']:.1f} K sobre ambiente con "
           f"{p['potencia_disipada']:.2f} W y el techo es {techo:g}: esta chimenea "
           f"evacua {t['p_evacuada']:.1f} W a ese techo. Hace falta mas area, "
           f"salidas mas altas o mas pata bajo la base: el tiro va con la RAIZ de "
           f"la altura")
   ```
4. `t_p = _tiro(p, CD_TIRO_PESIMISTA)` pasa a `t_p = _tiro_pesimista(p)`, y su aviso dice `con C_D={CD_TIRO_PESIMISTA} y el canal de {CANAL_BASE_PESIMISTA:g} bajo la base`.
5. El bloque del costado:
   ```python
       t_1 = _tiro_pesimista(p, costados=1)
       print(f"  con un costado tapado (contra una pared), pesimista: {t_1['dt']:.1f} K")
       if t_1["dt"] > techo + 1e-9:
           _HUECOS.append(
               f"la holgura de los costados sin medir: con un costado tapado el "
               f"case sube {t_1['dt']:.1f} K con el pesimista y "
               f"{p['potencia_disipada']:.2f} W, y el techo es {techo:.0f}. Los dos "
               f"tienen que quedar libres (PLIEGO sec.7); cuanta holgura hace falta "
               f"a cada lado se mide en el arranque (papel de la persiana, HUECO 4)")
   ```
6. Detrás, un aviso del apoyo, sin HUECO, porque es condición de uso del pliego:
   ```python
       t_0 = _tiro_pesimista(p, base=False)
       print(f"  aviso: sobre un pano o una alfombrilla la base no respira y el "
             f"pesimista sube a {t_0['dt']:.1f} K (PLIEGO sec.7: mesa dura, con "
             f"los {p['alto_pie']:g} mm de pata libres debajo)")
   ```

- [ ] **Step 6: `canario_techo()`, con la carga derivada por `_potencia_a`**

En el bloque del aire de `canario_techo()`:
1. Se sustituyen `w_sala` y `w_costado`:
   ```python
       w_sala = _potencia_a(p, techo * T_AMB / T_SALA_DISENO_K, CD_TIRO_PESIMISTA,
                            canal=CANAL_BASE_PESIMISTA)
       w_costado = _potencia_a(p, techo, CD_TIRO_PESIMISTA, costados=1,
                               canal=CANAL_BASE_PESIMISTA)
   ```
   El comentario de encima pasa a decir «la carga sale de la chimenea con el pesimista, que es como la puerta juzga los dos huecos».
2. Antes de `del _HUECOS[n_huecos:]` se añade el sujeto nuevo, que la base respire:
   ```python
       sin_base = _tiro({**p, "alto_pie": 0.5})
       assert sin_base["dt"] > t["dt"] + 1.0, (
           f"canario del aire: con las patas aplastadas a 0.5 mm el salto da "
           f"{sin_base['dt']:.2f} K contra {t['dt']:.2f} -- _tiro() no esta "
           f"mirando la base")
   ```
3. **Los tres márgenes escritos a mano** (+1,0 con un costado, +0,5 con el paso, +0,1 con los tacos) se miden de nuevo:
   ```bash
   cd case && python -c "
   import clearance_budget as cb; p = cb.leer_params(); t = cb._tiro(p)['dt']
   print('costado', cb._tiro(p, costados=1)['dt'] - t)
   print('paso', cb._tiro({**p, 'paso_persiana': p['paso_persiana'] - 1.0})['dt'] - t)
   print('tacos', cb._tiro({**p, 'taco_largo': 89.0})['dt'] - t)
   print('sin base', cb._tiro({**p, 'alto_pie': 0.5})['dt'] - t)"
   ```
   - Cada margen del canario tiene que quedar **por debajo de la mitad** de lo medido.
   - Si alguno no queda, se baja a la mitad de lo medido, redondeado a una décima hacia abajo, y se deja en el ledger como `Ruling`, con la cifra medida.
   - Si un sujeto sube menos de 0,1 K, el canario ya no lo distingue del ruido: se apunta como hallazgo, no se toca, y se lleva a Samuel.

- [ ] **Step 7: `persiana.py` y `suelo.py`**

En `case/cad/persiana.py`, bloque `__main__` (l.290-306):
1. El título del bloque del aire nombra la base: `«EL AIRE (clearance_budget._tiro(): plano neutro; las persianas, la base, la rejilla, la rendija y las ondas)»`.
2. Las llamadas pesimistas pasan de `cb._tiro(q, cb.CD_TIRO_PESIMISTA)` a `cb._tiro_pesimista(q)`, y de `cb._tiro(p, cb.CD_TIRO_PESIMISTA, **kw)` a `cb._tiro_pesimista(p, **kw)`.
3. Entre los parciales se añade `("sin la base (sobre un pano)", {"base": False})`.

`case/cad/suelo.py` se reescribe como impresor, con el solver ya en el budget:

```python
"""El suelo del case sin tabla: las cifras del aire del papel
docs/superpowers/specs/2026-10-12-case-suelo-design.md (sec.5).

Las calcula clearance_budget._tiro(), que desde el papel del suelo resuelve la
chimenea con la base como camino en serie. Este guion solo las imprime.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import clearance_budget as cb  # noqa: E402

if __name__ == "__main__":
    p = cb.leer_params()
    f_sala = cb.T_SALA_DISENO_K / cb.T_AMB
    t = cb._tiro(p)
    print(f"base: {len(cb._campo_base(p))} agujeros, {t['a_base']:.0f} mm2; "
          f"{p['potencia_disipada']} W, techo {p['salto_termico_max']:g} K")
    print("caso | salto pesim | 1 costado (pesim) | sala 45 (pesim)")
    filas = [("hoy, con la tabla", p, {"base": False})]
    for alto in (10.0, 20.0):
        for canal in (cb.CANAL_BASE, cb.CANAL_BASE_PESIMISTA):
            filas.append((f"patas de {alto:g}, canal de {canal:g}",
                          {**p, "alto_pie": alto}, {"canal": canal}))
    for nombre, q, kw in filas:
        n = cb._tiro(q, **kw)["dt"]
        pe = cb._tiro(q, cb.CD_TIRO_PESIMISTA, **kw)["dt"]
        c1 = cb._tiro(q, cb.CD_TIRO_PESIMISTA, costados=1, **kw)["dt"]
        print(f"{nombre:28s} | {n:5.2f} {pe:5.2f} | {c1:17.2f} | {pe * f_sala:15.2f}")
```

Run: `cd case && python cad/suelo.py && python cad/persiana.py > /dev/null && python -m ruff check clearance_budget.py cad/suelo.py cad/persiana.py`
Expected: la tabla del §5 con el campo real, y ruff limpio.

- [ ] **Step 8: Las puertas, y commit**

Run (en segundo plano, leyendo la salida): `sh .githooks/pre-push < /dev/null`

Expected: verde. El budget sale con exit 2, por los HUECOS declarados, igual que antes. Se imprimen el salto de la base, el aviso del apoyo y el HUECO de los costados con el pesimista. Con patas de 10 sigue publicándose el HUECO de los costados, y el de la sala ya no.

```bash
git add case/clearance_budget.py case/cad/persiana.py case/cad/suelo.py
git commit -m "El aire cuenta la base como camino en serie, y los HUECOS del aire se juzgan con el pesimista" -m "_tiro() resuelve la chimenea con dos bisecciones: el plano neutro por masa y el salto por energía. La base entra por la rendija de las patas y un canal laminar bajo la chapa. Sin base da la forma cerrada de antes, y con el canal sin roce da el orificio equivalente: autocomprobacion_base() fija las dos cosas. El HUECO de los costados se juzga con C_D 0,55 y el canal de 120, como el de la sala; con el nominal se callaba."
```

---

### Task 3: La base de chapa en el modelo y en su DXF

**Files:**
- Modify: `case/cad/params.scad`. Hacia las l.1015-1097 se reescribe el bloque de la tabla:
  - `t_base` = 3;
  - fuera `r_canto_tabla`, `E_madera`, `vuelo_zocalo` y `holgura_veta`.
  
  Y en las l.1382-1389 sale `d_pie_tornillo`.
- Modify: `case/cad/sam17_case.scad`:
  - `nariz_m4_x()` (l.999) y `talon_m4_x()` (l.278);
  - los agujeros del pie en `nariz_2d()` (l.1085-1087) y `talon_2d()` (l.1330-1332);
  - `bandeja_base_2d()` (l.1486-1586);
  - `bandeja_base_fondo()` y `bandeja_base_ancho()` (l.2171-2181);
  - `ch_pos()` (l.2226) y `chasis()` (l.2263-2270);
  - `bandeja_base()` (l.2501-2514) y `canto_redondeado()` (l.2516-2523);
  - `lienzo_2d()` (l.2804-2826);
  - funciones nuevas `zonas_campo_base()` y `campo_base()`.
- Modify: `case/clearance_budget.py`:
  - `_nariz()["m4_x"]` (l.~5864) y `_talon()["m4_x"]` (l.~3766);
  - la caja de `bandeja_base` en `_cajas_solidas()` (l.1679-1683);
  - `_chasis_tornillos_tabla()` (l.266-277);
  - `_fondo_bandeja()` (l.6408-6417);
  - `guarda_chasis()`: las coordenadas con `vuelo_zocalo`, l.6296-6311 y 6341.
- Modify: `case/check_dxf.py`:
  - `guarda_zocalo()` (l.2241-2382) pasa a `guarda_bandeja_base()`;
  - en `taladros_nariz()` y `taladros_talon()` cambia la mitad que mira la tabla (l.1173-1185 y 1565-1583);
  - la llamada en el `main` (l.2536).
- Regenerate: `case/plans/bandeja_base_2d.dxf`, `nariz_2d.dxf` y `talon_2d.dxf`, con `case/cad/export.ps1`.

**Interfaces:**
- Consumes: `_zonas_campo_base`, `_campo_base`, `_taladros_base` y `_m4_pie_borde` (Task 1).
- Produces:
  - `guarda_bandeja_base() -> list[str]` en `check_dxf`.
  - Las gemelas del `.scad`: `zonas_campo_base()`, `campo_base()` y `m4_pie_borde()`.

- [ ] **Step 1: La puerta del DXF (roja contra el DXF de hoy)**

En `check_dxf.py` se borra `guarda_zocalo()` entero y en su lugar va:

```python
def guarda_bandeja_base() -> list[str]:
    """La base de chapa, leida de su DXF (papel del suelo, 2026-10-12).

    Va al taller de chapa lo que diga el DXF, y por eso se lee el DXF:
      1. el contorno es la huella del cuerpo, sin vuelo;
      2. cada taladro de fijacion de _taladros_base() esta, con su diametro;
      3. el campo de agujeros es EL MISMO que cuenta el aire: misma cuenta y
         mismos centros que _campo_base(). Si las gemelas del .scad y del budget
         se separan, el aire cuenta unos agujeros y el taller corta otros.

    Coordenadas locales del DXF: x = z del mundo, y = x del mundo."""
    import clearance_budget as cb

    p = cb.leer_params()
    f: list[str] = []
    aristas, comps = _componentes("bandeja_base_2d")
    if not aristas:
        return ["bandeja_base_2d: sin LINEs, no se puede verificar la base"]
    xs = [q[0] for a in aristas for q in a]
    ys = [q[1] for a in aristas for q in a]
    largo = cb.fondo(p) - 2 * p["chaflan_nariz"]
    caja = (min(xs), max(xs), min(ys), max(ys))
    esperada = (0.0, p["ancho_total"], p["chaflan_nariz"], cb.fondo(p) - p["chaflan_nariz"])
    if any(abs(a - b) > DESVIO_DXF_MAX for a, b in zip(caja, esperada)):
        f.append(f"bandeja_base_2d: el contorno va de {caja} y la huella del "
                 f"cuerpo es {esperada}: la base no lleva vuelo")
    redondos = _redondos("bandeja_base_2d")
    k = p["kerf"]

    def faltan(puntos, d):
        return [(x, y) for x, y in puntos
                if not any(abs(q[2] - (d + k)) < 0.1
                           and math.hypot(q[0] - x, q[1] - y) <= DESVIO_DXF_MAX
                           for q in redondos)]

    for tipo in ("M5", "M4 nariz", "M4 talon", "FH pata", "M4 chasis"):
        puntos = [(z, x) for x, z, _d, t in cb._taladros_base(p) if t == tipo]
        d = next(dd for _x, _z, dd, t in cb._taladros_base(p) if t == tipo)
        mal = faltan(puntos, d)
        if mal:
            f.append(f"bandeja_base_2d: el taladro de {tipo} (d={d:g}) en "
                     f"{mal[0]} no esta en el DXF")
    campo = [(z, x) for x, z in cb._campo_base(p)]
    del_dxf = [q for q in redondos if abs(q[2] - (p["base_agujero"] + k)) < 0.1]
    if len(del_dxf) != len(campo):
        f.append(f"bandeja_base_2d: el DXF trae {len(del_dxf)} agujeros de "
                 f"{p['base_agujero']:g} y el aire cuenta {len(campo)} "
                 f"(_campo_base): las gemelas se separaron")
    else:
        mal = faltan(campo, p["base_agujero"])
        if mal:
            f.append(f"bandeja_base_2d: el agujero del campo en {mal[0]} no "
                     f"esta donde lo pone _campo_base()")
    if not f:
        print(f"  bandeja_base_2d: {largo:.2f} x {p['ancho_total']:.2f}, "
              f"{len(cb._taladros_base(p))} taladros de fijacion y "
              f"{len(campo)} agujeros del campo, los mismos que cuenta el aire")
    return f
```

En el `main` de `check_dxf.py`, `fallos += guarda_zocalo()` pasa a `fallos += guarda_bandeja_base()`.

Run: `cd case && python check_dxf.py 2>&1 | grep -i "bandeja_base"`
Expected: FAIL. El DXF versionado es la tabla: lleva el contorno con vuelo, las ranuras y ningún agujero de 5.

- [ ] **Step 2: Los parámetros de la tabla salen**

En `params.scad`:
1. El bloque de la tabla se reescribe, desde el comentario «LA TABLA. Dejo de ser una plancha DENTRO del case» (l.~1015) hasta `holgura_veta = 2.5;` (l.~1097). Queda solo esto:
   ```
   // LA BASE, desde el papel del suelo (2026-10-12): una chapa de 6082-T6 de 3 mm,
   // anodizada en negro, bajo los anillos y a ras de su huella, de y = -t_base a
   // 0. Sustituye a la tabla de nogal de 30 (D-S4 «quitar», acta 3), que fue el
   // suelo desde el 2026-08-27. Amarra los anillos con los mismos seis M5 a su
   // canto inferior, recibe la nariz, el talon, las patas y el chasis, y es la
   // entrada de aire (sec.5). 3 mm los pide la mano, no el peso: con 200 N
   // (carga_mano) en el campo, 2 mm plastifican el borde de los agujeros y 3 no
   // (guarda_piso(), papel sec.3.2). El plano del suelo interior sigue en y = 0:
   // nada de lo que hay encima se mueve. CONSERVA SUS NOMBRES (bandeja_base,
   // t_base): "suelo" ya nombra cinco cosas en el codigo.
   t_base     = 3;
   ```
2. Se borra el bloque de `d_pie_tornillo`, de «EL TORNILLO CON QUE LA PATICA SE ATORNILLA A LA TABLA» a `d_pie_tornillo = 4.5;`. Ahora la pata va en una FH-M4 (`pem_fh_m4`), y la nariz y el talón pasan por `d_M4_paso` (Task 1 y D-T2).

Run: `cd case && grep -rn "vuelo_zocalo\|holgura_veta\|r_canto_tabla\|E_madera\|d_pie_tornillo" cad/*.scad *.py cad/*.py renders/*.py`
Expected: la lista de los lectores que quedan. Cada uno se trata en los Steps 3 a 5.

- [ ] **Step 3: El `.scad`**

1. Funciones nuevas, junto a `nariz_m4_x()` (l.~999). `talon_m4_x()` se cambia en su sitio (l.278):
   ```
   function m4_pie_borde() = max(1.5*d_M4_paso, pem_borde);   // GEMELA de _m4_pie_borde()
   function nariz_m4_x() = chaflan_nariz + nariz_pie - m4_pie_borde();
   function talon_m4_x()      = talon_x_pie() + m4_pie_borde();
   ```
2. En `nariz_2d()` (l.1086-1087), `translate([z - chapa_z0(), 1.5*d_M4_paso]) circle(d = d_M4_paso + kerf);` pasa a:
   ```
               translate([z - chapa_z0(), m4_pie_borde()])
                   circle(d = pem_cls_m4 + kerf);
   ```
   En `talon_2d()` (l.1331-1332), lo mismo con `d - m4_pie_borde()`.

   Un comentario de una línea encima de cada uno: `// D-T2 (papel del suelo): tuerca CLS-M4 prensada en el pie; el M4 entra desde abajo.`
3. Las gemelas del campo, junto a `bandeja_base_fondo()`:
   ```
   // LA L DEL CAMPO DE LA BASE y su red. GEMELAS de _zonas_campo_base() y
   // _campo_base() del budget: check_dxf compara la cuenta y los centros.
   function zonas_campo_base() =
       let (o = base_orilla,
            x0 = chaflan_nariz + nariz_pie + o, x1 = talon_x_pie() - o,
            z0 = t_anillo + o, z1 = ancho_total - t_anillo - o,
            z_ch = t_anillo + ancho_util - chasis_margen_bandeja - ch_tapa_ext().x,
            x_ch = x_chasis_frente())
       [[x0, x1, z0, z_ch - o], [x0, x_ch - o, z_ch - o, z1]];
   function campo_base() =
       let (zs = zonas_campo_base(), d = base_agujero, s = base_paso,
            r = d/2, f = s*sqrt(3)/2,
            x0 = min([for (q = zs) q[0]]), x1 = max([for (q = zs) q[1]]),
            z0 = min([for (q = zs) q[2]]), z1 = max([for (q = zs) q[3]]),
            ni = floor((x1 - x0 - d)/f + 1e-9), nj = floor((z1 - z0 - d)/s + 1e-9))
       [for (i = [0 : ni]) for (j = [0 : nj])
           let (x = x0 + r + i*f, z = z0 + r + (i % 2)*s/2 + j*s)
           if (len([for (q = zs)
                       if (x >= q[0] + r - 1e-9 && x <= q[1] - r + 1e-9
                           && z >= q[2] + r - 1e-9 && z <= q[3] - r + 1e-9) 1]) > 0)
               [x, z]];
   ```
4. Las cotas de la pieza, sin vuelo:
   ```
   function bandeja_base_fondo() = fondo() - 2*chaflan_nariz;
   function bandeja_base_ancho() = ancho_total;
   ```
   Sus notas de «el VANO ENTRE LARGUEROS» (l.2163-2180) se cambian por una línea: `// La base: la huella del canto inferior del anillo, de chaflan a chaflan.`
5. `ch_pos()`:
   ```
   function ch_pos() = [t_anillo + ancho_util - chasis_margen_bandeja - ch_tapa_ext().x,
                        x_chasis_frente()];
   ```
   `chasis()`:
   ```
   module chasis() {
       p  = ch_pos();
       multmatrix([[0, 1, 0, p.y],
                   [0, 0, 1, chasis_pie],
                   [1, 0, 0, p.x],
                   [0, 0, 0, 1]])
           chasis_3d();
   }
   ```
   Y en el comentario largo de encima, «local x = vuelo_zocalo + z del mundo» pasa a «local x = z del mundo, local y = x del mundo».
6. `bandeja_base_2d()` se reescribe entero. Se conservan dos comentarios: el de la salida de cables y el de los M5 en el canto del anillo.
   ```
   module bandeja_base_2d() {
       // LA BASE (papel del suelo, 2026-10-12): chapa de 3, a ras de la huella del
       // cuerpo. Local x = z del mundo, local y = x del mundo, sin desplazamiento.
       difference() {
           translate([0, chaflan_nariz]) plancha(bandeja_base_ancho(), bandeja_base_fondo());
           // LOS SEIS M5 DE LOS ANILLOS, al medio de su canto inferior (rosca
           // ciega). Redondos los seis: aluminio contra aluminio se dilata igual,
           // y la veta se fue con la tabla. d_M5_base deja medio mm de juego.
           for (zc = [t_anillo/2, ancho_total - t_anillo/2])
               for (i = [0 : n_agujeros() - 1])
                   translate([zc, fondo()*(i + 0.5)/n_agujeros()])
                       circle(d = d_M5_base + kerf);
           // LAS CUATRO FH-M4 DE LAS PATAS, en las posiciones de paticas().
           for (wx = [alto_frontal/2 + d_pie/2, centro_talon().x])
               for (wz = [d_pie/2, ancho_total - d_pie/2])
                   translate([wz, wx]) circle(d = pem_fh_m4 + kerf);
           // LOS 3 + 3 M4 DE NARIZ Y TALON, de paso: entran desde abajo a la
           // tuerca de su pie (D-T2).
           for (wz = nariz_m4_z()) {
               translate([wz, nariz_m4_x()]) circle(d = d_M4_paso + kerf);
               translate([wz, talon_m4_x()]) circle(d = d_M4_paso + kerf);
           }
           // LOS CUATRO M4 DEL CHASIS, desde abajo a su tuerca remachable.
           for (q = chasis_tornillos_tabla())
               translate(q) circle(d = d_M4_paso + kerf);
           // [el comentario de LA SALIDA DE CABLES DEL CHASIS, tal cual]
           translate(salida_cables_xy()) {
               w = chasis_salida_ancho + 2*salida_holgura;
               h = chasis_salida_fondo + 2*salida_holgura;
               r = salida_radio;
               hull() for (dx = [r, w - r], dy = [r, h - r])
                   translate([dx, dy]) circle(r = r + kerf/2);
           }
           // EL CAMPO: la L de campo_base(). 16 lados: el error de cuerda es de
           // 0.05 mm en un agujero de aire, y el DXF no pasa de unos MB.
           for (c = campo_base())
               translate([c[1], c[0]]) circle(d = base_agujero + kerf, $fn = 16);
       }
   }
   ```
   El comentario largo del principio («EL SUELO CIERRA (2026-08-21)…») se borra. Era la historia de una plancha que ya no existe, y describía como cerrado un suelo que ahora respira.
7. `bandeja_base()`, sin vuelo, sin canto redondeado y sin espejo:
   ```
   module bandeja_base() {
       // LA BASE: de y = -t_base a 0, bajo los anillos. La transformacion es una
       // ROTACION (determinante +1): local x = z, local y = x, como ch_pos() y el
       // budget. La de la tabla espejaba z, y solo no se veia porque sus agujeros
       // eran simetricos.
       multmatrix([[0, 1, 0, 0], [0, 0, 1, -t_base], [1, 0, 0, 0], [0, 0, 0, 1]])
           linear_extrude(t_base) bandeja_base_2d();
   }
   ```
   Se borra `canto_redondeado()` entero.
8. `lienzo_2d()`: es de acrílico, así que sale la base.
   ```
   module lienzo_2d() {
       piel_trasera_2d();
       %square([1000, 600]);
   }
   ```

- [ ] **Step 4: El budget**

1. `_nariz()`: `"m4_x": c + p["nariz_pie"] - _m4_pie_borde(p),`. `_talon()`: `"m4_x": x_pie + _m4_pie_borde(p),`.
2. En `_cajas_solidas()`, la caja de `bandeja_base` (l.1679-1683). El comentario largo de encima se reduce a dos líneas (`# bandeja_base: LA BASE de chapa (papel del suelo, 2026-10-12), bajo los anillos y a ras de su huella.`) y la caja queda:
   ```python
       planchas.append(("bandeja_base",
                        p["chaflan_nariz"], fondo(p) - p["chaflan_nariz"],
                        -p["t_base"], 0.0,
                        0.0, p["ancho_total"]))
   ```
3. `_chasis_tornillos_tabla()`: se borra la línea `v = p["vuelo_zocalo"]`, y `pos_x`/`pos_y` quedan:
   ```python
       pos_x = p["t_anillo"] + au - p["chasis_margen_bandeja"] - c["tapa_x"]
       pos_y = _x_chasis_frente(p)
   ```
   En el docstring, «x local = vuelo + z del mundo, y local = vuelo + x del mundo» pasa a «x local = z del mundo, y local = x del mundo».
4. `_fondo_bandeja()`:
   ```python
   def _fondo_bandeja(p: dict[str, float]) -> float:
       """Largo de la BASE en x, de chaflan a chaflan (papel del suelo, 2026-10-12)."""
       return fondo(p) - 2 * p["chaflan_nariz"]
   ```
5. `guarda_chasis()`: solo se quitan los términos de vuelo, y su marco de referencia no se toca.
   - l.~6304: `pos_y = _x_chasis_frente(p) + p["vuelo_zocalo"]` pasa a `pos_y = _x_chasis_frente(p)`.
   - l.~6308: el rango en y pasa a `and p["chaflan_nariz"] <= ay and ay + h <= fondo(p) - p["chaflan_nariz"],`. La base ya no empieza en 0 sino en el chaflán.
   - l.~6341: `libre_1 = _talon(p)["x_pie"] + p["vuelo_zocalo"] - hol` pasa a `libre_1 = _talon(p)["x_pie"] - hol`.
   - `pos_x` (l.~6297) **no lleva vuelo y se queda**: su origen es la cara interior del anillo, y el rango en x que comprueba es `ancho_util`.

- [ ] **Step 5: `check_dxf`, las mitades de nariz y talón**

En `taladros_nariz()` (l.~1173-1185) y `taladros_talon()` (l.~1565-1583):
- `v = p["vuelo_zocalo"]` pasa a `v = 0.0`;
- el diámetro esperado en la base (`d_pie_tornillo`) pasa a `p["d_M4_paso"]`;
- en `nariz_2d`/`talon_2d`, el diámetro de su pie pasa de `d_M4_paso` a `p["pem_cls_m4"]`.

Los comentarios que dicen «mismo herraje a la misma madera» pasan a decir que la tuerca va en el pie y el paso en la base.

Y la posición que se espera en el pie: en `taladros_nariz()`, `esperados = [(_x_blank(p, z), 1.5 * p["d_M4_paso"]) ...]` (l.~1157) y su mensaje (l.~1184) pasan a `cb._m4_pie_borde(p)`. En `taladros_talon()` se hace lo mismo con su gemela (`d - 1.5 * p["d_M4_paso"]` pasa a `d - cb._m4_pie_borde(p)`). La regla `BORDE_MIN_D` (l.~1167) se queda como está: con 7,0 sigue por encima de 1,5 D.

Run: `cd case && grep -n "vuelo_zocalo\|d_pie_tornillo\|holgura_veta" check_dxf.py clearance_budget.py cad/sam17_case.scad`
Expected: ninguna línea de código. Si queda alguna en comentarios de historia, se deja.

- [ ] **Step 6: Exportar y ver la puerta en verde**

Run: `cd case/cad && powershell -File export.ps1` (es el export de siempre: regenera los DXF y los STL de `case/plans/` y `case/cad/build/`)
Expected: exit 0, y `bandeja_base_2d.dxf` pesa unos MB, no decenas.

Run: `cd case && python check_dxf.py 2>&1 | tail -30`
Expected:
- VERDE;
- `bandeja_base_2d: 307.76 x 568.62, 20 taladros de fijacion y N agujeros del campo, los mismos que cuenta el aire`;
- `taladros_nariz()` y `taladros_talon()` verdes, con la CLS en el pie;
- tiempo total de `check_dxf` < 60 s. Si pasa, se mide `_componentes("bandeja_base_2d")` aparte.

- [ ] **Step 7: Las puertas, y commit**

Run (en segundo plano): `sh .githooks/pre-push < /dev/null`
Expected: verde.
- `guarda_chasis()` verde con el chasis en las mismas cuatro posiciones.
- `guarda_talon()` verde: la boca del avellanado se aleja 0,25 hacia la trasera, y el aire pasa de 2,77 a ~2,52. Si queda por debajo de 1,70, está mal, y se para.
- `solapes()` verde.
- `canario_persiana_tabla()` **rojo**: la base ya no pasa bajo la persiana. Se deja rojo y se arregla en la Task 5, sin commit intermedio. Si se prefiere un commit por tarea, se adelanta a esta tarea el Step 4 de la Task 5.

```bash
git add case/cad/params.scad case/cad/sam17_case.scad case/clearance_budget.py case/check_dxf.py case/plans/bandeja_base_2d.dxf case/plans/nariz_2d.dxf case/plans/talon_2d.dxf
git commit -m "La tabla de nogal pasa a ser una base de chapa de 3 mm, a ras de la huella y con su campo de agujeros" -m "bandeja_base conserva el nombre. Pierde el vuelo, la veta y el canto redondeado, y gana el campo en L de campo_base(), gemela de _campo_base(). Los M4 de la nariz y del talón entran desde abajo, a tuercas CLS en sus pies, a pem_borde de su canto libre. La transformación 3D de la base es una rotación: la de la tabla espejaba z. guarda_bandeja_base() lee el DXF y exige el contorno sin vuelo, los 20 taladros de fijación y el mismo campo que cuenta el aire."
```

---

### Task 4: La flexión de la base

**Files:**
- Modify: `case/clearance_budget.py`:
  - en `guarda_piso()` (l.5720-5757), el aserto 2 se sustituye;
  - helpers nuevos: `_seccion_chapa()`, `_flecha_base()` y `autocomprobacion_emparrillado()`;
  - un canario.

**Interfaces:**
- Consumes: `_zonas_campo_base(p)` (Task 1), `_nariz(p)`, `_talon(p)`, `E_ALUMINIO`, `RP02_6082_T6`.
- Produces:
  - `_flecha_base(p, cargas) -> tuple[float, float]`: la flecha máxima en mm y el momento máximo por unidad de ancho en N·mm/mm.
  - `autocomprobacion_emparrillado() -> None`.

- [ ] **Step 1: La autocomprobación del emparrillado (roja)**

```python
def autocomprobacion_emparrillado() -> None:
    """El emparrillado contra Timoshenko: placa cuadrada de 300, apoyada en los
    cuatro bordes, 100 N al centro: w = 0.01160 P a^2 / D. Elke lo valido a
    n = 20 dentro del 1.3 %; aqui se exige el 3 % con la malla de la puerta."""
    t, a = 3.0, 300.0
    nu = 0.33
    d = E_ALUMINIO * t ** 3 / (12 * (1 - nu ** 2))
    w = _emparrillado(a, a, t, 16, 16, apoyos="cuatro bordes",
                      cargas=[(a / 2, a / 2, 100.0)])[0]
    w_t = 0.01160 * 100.0 * a * a / d
    assert abs(w - w_t) < 0.03 * w_t, (
        f"el emparrillado da {w:.3f} mm y Timoshenko {w_t:.3f} en la placa "
        f"cuadrada: la malla o el ensamblado estan mal")
```

Run: `cd case && python -c "import clearance_budget as cb; cb.autocomprobacion_emparrillado()"`
Expected: FAIL con `NameError: _emparrillado`.

- [ ] **Step 2: El emparrillado**

Es el modelo de Elke (analogía de Hambly) en `numpy` denso, con `numpy` importado dentro de la función, como en `persiana.py`. La malla es de 16 × 28, unos 1 600 grados de libertad, y se resuelve en menos de un segundo.

```python
def _seccion_chapa(poly: list[tuple[float, float]], t: float) -> float:
    """Inercia (mm4) de una chapa de espesor t por su linea media, para flexion
    vertical: la seccion de la nariz o del talon tumbada (secciones.py de Elke)."""
    segs = list(zip(poly[:-1], poly[1:]))
    area = sum(t * math.dist(a, b) for a, b in segs)
    yc = sum(t * math.dist(a, b) * (a[1] + b[1]) / 2 for a, b in segs) / area
    inercia = 0.0
    for a, b in segs:
        largo = math.dist(a, b)
        s = abs(b[1] - a[1]) / largo if largo else 0.0
        ym = (a[1] + b[1]) / 2
        inercia += (t * largo * (ym - yc) ** 2 + t * largo ** 3 * s ** 2 / 12
                    + largo * t ** 3 * (1 - s ** 2) / 12)
    return inercia


def _emparrillado(lx: float, lz: float, t: float, nx: int, nz: int, apoyos: str,
                  cargas: list[tuple[float, float, float]],
                  blando: list[tuple[float, float, float, float]] = (),
                  f_blando: float = 1.0, bordes: dict | None = None,
                  lineas_z: tuple[float, ...] = ()) -> tuple[float, float]:
    """Emparrillado de una placa de lx por lz y espesor t (analogia de Hambly):
    vigas en x y en z con la rigidez D de su franja y torsion, tres grados por
    nudo (w, giro en x, giro en z). Devuelve (flecha maxima en mm, momento
    maximo por unidad de ancho en N mm/mm).

    apoyos: "cuatro bordes" (la validacion), o "lineas" (w = 0 a lo largo de
    las z de lineas_z: el canto de los anillos). blando: rectangulos (x0, x1,
    z0, z1) con la rigidez por f_blando (el campo perforado). bordes: vigas de
    borde atadas en puntos, {"x": ..., "EI": ..., "z_atados": [...],
    "z_apoyos": (z0, z1)}. cargas: (x, z, N) en el nudo mas cercano."""
    import numpy as np

    nu = 0.33
    xs, zs = np.linspace(0.0, lx, nx + 1), np.linspace(0.0, lz, nz + 1)
    d0 = E_ALUMINIO * t ** 3 / (12 * (1 - nu ** 2))
    nn = (nx + 1) * (nz + 1)
    bordes = bordes or []
    nb = nz + 1
    ndof = 3 * nn + 2 * nb * len(bordes)
    K = np.zeros((ndof, ndof))

    def idx(i, j):
        return i * (nz + 1) + j

    def kb(ei, L):
        c = ei / L ** 3
        return np.array([[12 * c, 6 * L * c, -12 * c, 6 * L * c],
                         [6 * L * c, 4 * L * L * c, -6 * L * c, 2 * L * L * c],
                         [-12 * c, -6 * L * c, 12 * c, -6 * L * c],
                         [6 * L * c, 2 * L * L * c, -6 * L * c, 4 * L * L * c]])

    def add(dofs, k):
        K[np.ix_(dofs, dofs)] += k

    def rig(x, z):
        return d0 * (f_blando if any(a <= x <= b and c <= z <= e
                                     for a, b, c, e in blando) else 1.0)

    dx, dz = np.diff(xs), np.diff(zs)
    for i in range(nx + 1):
        for j in range(nz + 1):
            if i < nx:
                s = (dz[j - 1] / 2 if j > 0 else 0) + (dz[j] / 2 if j < nz else 0)
                dl = rig((xs[i] + xs[i + 1]) / 2, zs[j]) * s
                n1, n2 = idx(i, j), idx(i + 1, j)
                add([3 * n1, 3 * n1 + 1, 3 * n2, 3 * n2 + 1], kb(dl, dx[i]))
                add([3 * n1 + 2, 3 * n2 + 2], np.array([[1, -1], [-1, 1]]) * dl / dx[i])
            if j < nz:
                s = (dx[i - 1] / 2 if i > 0 else 0) + (dx[i] / 2 if i < nx else 0)
                dl = rig(xs[i], (zs[j] + zs[j + 1]) / 2) * s
                n1, n2 = idx(i, j), idx(i, j + 1)
                add([3 * n1, 3 * n1 + 2, 3 * n2, 3 * n2 + 2], kb(dl, dz[j]))
                add([3 * n1 + 1, 3 * n2 + 1], np.array([[1, -1], [-1, 1]]) * dl / dz[j])

    def ni(x):
        return int(np.argmin(abs(xs - x)))

    def nj(z):
        return int(np.argmin(abs(zs - z)))

    fijos = set()
    kpen = 1e7                         # N/mm, como Elke: tres ordenes sobre la malla
    for bi, bd in enumerate(bordes):
        b0 = 3 * nn + 2 * nb * bi
        for j in range(nz):
            add([b0 + 2 * j, b0 + 2 * j + 1, b0 + 2 * (j + 1), b0 + 2 * (j + 1) + 1],
                kb(bd["EI"], dz[j]))
        for z in bd["z_atados"]:
            a, b = 3 * idx(ni(bd["x"]), nj(z)), b0 + 2 * nj(z)
            add([a, b], np.array([[kpen, -kpen], [-kpen, kpen]]))
        for z in bd["z_apoyos"]:
            fijos.add(b0 + 2 * nj(z))
    if apoyos == "cuatro bordes":
        fijos |= {3 * idx(i, j) for i in range(nx + 1) for j in range(nz + 1)
                  if i in (0, nx) or j in (0, nz)}
    else:
        fijos |= {3 * idx(i, nj(z)) for z in lineas_z for i in range(nx + 1)}
    F = np.zeros(ndof)
    for x, z, n in cargas:
        F[3 * idx(ni(x), nj(z))] -= n
    lib = np.array(sorted(set(range(ndof)) - fijos))
    u = np.zeros(ndof)
    u[lib] = np.linalg.solve(K[np.ix_(lib, lib)], F[lib])
    w = u[0:3 * nn:3]
    # momento por unidad de ancho en las vigas en x: m = D * curvatura
    m_max = 0.0
    for i in range(1, nx):
        for j in range(nz + 1):
            curv = (w[idx(i - 1, j)] - 2 * w[idx(i, j)] + w[idx(i + 1, j)]) / dx[i] ** 2
            m_max = max(m_max, abs(rig(xs[i], zs[j]) * curv))
    for i in range(nx + 1):
        for j in range(1, nz):
            curv = (w[idx(i, j - 1)] - 2 * w[idx(i, j)] + w[idx(i, j + 1)]) / dz[j] ** 2
            m_max = max(m_max, abs(rig(xs[i], zs[j]) * curv))
    return float(-w.min()), float(m_max)


def _flecha_base(p: dict[str, float], cargas: list[tuple[float, float, float]]
                 ) -> tuple[float, float]:
    """La base con sus apoyos de verdad: el canto de los dos anillos (lineas en
    z = t_anillo/2 y ancho - t_anillo/2), y la nariz y el talon como vigas de
    borde atadas en sus tres M4 y apoyadas en el rebaje del anillo. El campo
    perforado, con el 30 % de la rigidez (Elke, O'Donnell-Langer, ligamento
    0.375; ESTIMADO). Coordenadas de la placa: x desde el chaflan delantero."""
    x0 = p["chaflan_nariz"]
    lx = fondo(p) - 2 * x0
    nz_, tl = _nariz(p), _talon(p)
    t = p["t_costilla"]
    bordes = [{"x": nz_["m4_x"] - x0, "EI": E_ALUMINIO * _seccion_chapa(nz_["contorno"], t),
               "z_atados": nz_["m4_z"], "z_apoyos": (p["t_anillo"], p["ancho_total"] - p["t_anillo"])},
              {"x": tl["m4_x"] - x0, "EI": E_ALUMINIO * _seccion_chapa(tl["contorno"], t),
               "z_atados": tl["m4_z"], "z_apoyos": (p["t_anillo"], p["ancho_total"] - p["t_anillo"])}]
    blando = [(a - x0, b - x0, c, e) for a, b, c, e in _zonas_campo_base(p)]
    return _emparrillado(lx, p["ancho_total"], p["t_base"], 16, 28, "lineas",
                         [(x - x0, z, n) for x, z, n in cargas], blando, 0.30,
                         bordes, (p["t_anillo"] / 2, p["ancho_total"] - p["t_anillo"] / 2))
```

Run: `cd case && python -c "import clearance_budget as cb; cb.autocomprobacion_emparrillado()"`
Expected: PASS.

- [ ] **Step 3: El criterio nuevo en `guarda_piso()` y su canario**

En `guarda_piso()` se borra entero el bloque «# 2. LA TABLA NO SE HUNDE BAJO EL CHASIS DEL PSU.» (l.5720-5757), con su aserto y sus dos `print`. En su lugar va:

```python
    # 2. LA BASE AGUANTA UNA MANO (papel del suelo, 2026-10-12, sec.3.2). Lo que
    #    la carga de verdad es poco (ella misma, el chasis en sus cuatro M4 y la
    #    trasera en el pie del talon: Elke, 0.31 a 0.41 mm). Lo que la decide es
    #    una mano de carga_mano apoyada en el campo, que es lo unico de la base
    #    que se alcanza: en el centro de cada brazo de la L. Dos condiciones: no
    #    toca la mesa (flecha <= alto_pie - 1) y el puente del campo no
    #    plastifica: el momento del campo, por la concentracion del ligamento
    #    paso / (paso - agujero), contra RP02_6082_T6 / 1.5.
    peor = (0.0, 0.0, "")
    for n_brazo, (a, b, c, e) in zip("AB", _zonas_campo_base(p)):
        xc, zc = (a + b) / 2, (c + e) / 2
        mano = [(xc + dxm, zc + dzm, p["carga_mano"] / 9)
                for dxm in (-20.0, 0.0, 20.0) for dzm in (-30.0, 0.0, 30.0)]
        w, m = _flecha_base(p, mano)
        if w > peor[0]:
            peor = (w, m, n_brazo)
    w, m, brazo = peor
    sigma = 6 * m / p["t_base"] ** 2 * p["base_paso"] / (p["base_paso"] - p["base_agujero"])
    assert w <= p["alto_pie"] - 1.0 + 1e-9, (
        f"la base cede {w:.2f} mm con una mano de {p['carga_mano']:.0f} N en el "
        f"brazo {brazo} del campo y las patas dejan {p['alto_pie']:g}: toca la "
        f"mesa. Sube t_base")
    assert sigma <= RP02_6082_T6 / 1.5 + 1e-9, (
        f"el puente del campo trabaja a {sigma:.0f} MPa con una mano de "
        f"{p['carga_mano']:.0f} N en el brazo {brazo}, contra {RP02_6082_T6 / 1.5:.0f} "
        f"(Rp0.2 / 1.5): el borde del agujero se deforma para siempre. Sube "
        f"t_base o cierra el campo")
    print(f"suelo: BASE de chapa t={p['t_base']:g}; con {p['carga_mano']:.0f} N "
          f"en el brazo {brazo} del campo cede {w:.2f} mm (techo "
          f"{p['alto_pie'] - 1:.0f}) y el puente trabaja a {sigma:.0f} MPa (techo "
          f"{RP02_6082_T6 / 1.5:.0f})")
```

El canario va junto a `canario_campo_base`:

```python
def canario_base_fina(p: dict[str, float]) -> None:
    """Con t_base = 2 Elke da el borde de los agujeros en fluencia con la mano:
    guarda_piso() tiene que saltar, y por la flexion de la base."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            guarda_piso({**p, "t_base": 2.0})
    except AssertionError as e:
        assert "base" in str(e) or "puente" in str(e), (
            f"canario de la base: con t_base = 2 guarda_piso() salto, pero por "
            f"otra razon ('{str(e)[:80]}...')")
        return
    raise AssertionError("canario de la base NO disparo: con 2 mm de chapa "
                         "guarda_piso() deja pasar la mano -- no confiar en su VERDE")
```

En `main()`: `autocomprobacion_emparrillado()` junto a las demás autocomprobaciones, y `canario_base_fina(p)` junto a los canarios.

Run: `cd case && python -c "import clearance_budget as cb; p = cb.leer_params(); cb.guarda_piso(p); cb.canario_base_fina(p)"`

Expected: PASS. Imprime una flecha del orden de 1 a 3 mm y un puente de 30 a 80 MPa. El canario rojo con 2 mm cae por la tensión o por la flecha.

Si con 3 mm el puente no pasa de 160 MPa, el modelo contradice a Elke (53 MPa): se para y se revisa el momento. Es la curvatura por diferencias centrales en la malla de 16 × 28.

- [ ] **Step 4: Las puertas, y commit**

Run (en segundo plano): `sh .githooks/pre-push < /dev/null`. Expected: verde, con la salvedad del canario de la persiana si la Task 5 no ha entrado.

```bash
git add case/clearance_budget.py
git commit -m "La flexión de la base sale de un emparrillado: una mano en el campo no toca la mesa ni plastifica el puente" -m "_emparrillado() es la analogía de Hambly de Elke en numpy denso, comprobada contra Timoshenko en la placa cuadrada (autocomprobacion_emparrillado). La base se apoya en el canto de los anillos, con la nariz y el talón como vigas de borde atadas en sus M4 y el campo al 30 % de rigidez. Sustituye al aserto 2 de guarda_piso(), que medía la tabla de nogal con el chasis en medio del vano."
```

---

### Task 5: Las patas, el talón, la persiana y el BOM

**Files:**
- Modify: `case/cad/params.scad:1356-1381`, el bloque de la pata.
- Modify: `case/clearance_budget.py`:
  - `guarda_paticas()` (l.2851-2884);
  - `guarda_talon()` (l.4348-4354, la boca);
  - `canario_persiana_tabla()` (l.2156-2163) y su llamada (l.6438);
  - un canario del M4 desde abajo.
- Modify: `case/cad/sam17_case.scad`:
  - `paticas()` (l.2690-2701);
  - `bom()`: la TABLA (l.3099-3121), la nariz y el talón (l.2933-2997), las patas (l.3060-3070) y la cuenta de tornillos (l.3043-3057);
  - el PART `render_negro` (l.2370).

**Interfaces:**
- Consumes: `_m4_pie_borde(p)` (Task 1) y `_tiro(p)` (Task 2).
- Produces: `canario_m4_desde_abajo(p) -> None`.

- [ ] **Step 1: El canario del M4 desde abajo (rojo)**

```python
def canario_m4_desde_abajo(p: dict[str, float]) -> None:
    """D-T2: el M4 del pie de nariz y talon rosca en una tuerca prensada a
    pem_borde del canto libre. Si pem_borde no cabe entre el canto libre y el
    doblez, guarda_talon() tiene que saltar por la regla de chapa."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            guarda_talon({**p, "pem_borde": p["talon_pie"]})
    except AssertionError as e:
        assert "regla de chapa" in str(e), (
            f"canario del M4 desde abajo: guarda_talon() salto, pero por otra "
            f"razon ('{str(e)[:80]}...')")
        return
    raise AssertionError("canario del M4 desde abajo NO disparo: con la tuerca "
                         "a talon_pie del canto, el M4 cae en el doblez y "
                         "guarda_talon() lo deja pasar")
```

Run: `cd case && python -c "import clearance_budget as cb; cb.canario_m4_desde_abajo(cb.leer_params())"`

Expected: con la Task 3 hecha, PASS directo. Ya muerde, porque el aserto `raiz` de `guarda_talon()` lee `m4_x` y `m4_x` sale de `pem_borde`. **Que pase a la primera no es un fallo del test**: el sujeto lo trajo la Task 3. Se deja escrito en el ledger, y se comprueba que muerde con `pem_borde` = 7 y no muerde con el de verdad, que es lo que hace el canario.

- [ ] **Step 2: `guarda_talon()` mide la tuerca, no el avellanado**

En `params.scad`, junto a `pem_cls_m4`:

```
pem_cls_m4_cuerpo = 7.9;   // diametro del cuerpo de la CLS-M4 sobre el pie, por dentro (SUPUESTO, H4)
```

En `guarda_talon()` (l.~4348), la boca del avellanado pasa a ser el cuerpo de la tuerca:

```python
    boca = tl["m4_x"] + p["pem_cls_m4_cuerpo"] / 2
    franja = _tol_pmma(p) + 0.5
    aire = tr["x0"] - boca
    assert aire >= franja - 1e-9, (
        f"la tuerca del M4 del talon (D-T2: el tornillo entra desde abajo) llega "
        f"a x={boca:.2f} y la cara interior de la trasera esta en "
        f"{tr['x0']:.2f}: {aire:.2f} de aire, y detras de un PMMA de "
        f"+-{_tol_pmma(p):.1f} se piden {franja:.2f}. Sube talon_pie")
```

En el docstring de `guarda_talon()`, «tres M4 en el pie con la boca lejos del acrilico» pasa a «tres M4 desde abajo, con la tuerca de su pie lejos del acrilico».

En `params.scad`, el comentario del talón (l.~129-142) que razona la boca del avellanado gana una línea al final: `// DESDE EL PAPEL DEL SUELO (2026-10-12, D-T2) el M4 entra desde abajo y lo que asoma dentro es el cuerpo de la tuerca CLS (pem_cls_m4_cuerpo), no la boca del avellanado: guarda_talon() mide eso.`

`d_cabeza_M4_avell` se queda si tiene otros lectores (`grep -n d_cabeza_M4_avell case/*.py case/cad/*.scad`). Si no tiene ninguno, se borra.

- [ ] **Step 3: La pata, con el criterio nuevo**

En `params.scad` se reescribe el bloque de la pata, de «LA COTA QUE DECIDE SI SIRVE ES CUANTO SE HUNDE» hasta `d_pie = 20;`:

```
// LA PATA, desde el papel del suelo (2026-10-12, D-T1: las de 10). El criterio de
// compra se invierte. Era una goma BLANDA (>= 0.25 mm de flecha con 22.8 N) para
// aislar los 100 Hz de un toroide que se fue con la v4; ahora la pata es parte de
// la entrada de aire (la rendija de alto_pie bajo la base, sec.5) y se quiere
// FIRME: <= 0.3 mm con 50 N (Shore 60-70 A), alto nominal +- 0.2 (cuatro patas
// desiguales cojean), compuesto que no manche el barniz, y la profundidad del
// casquillo y su par en la hoja. Se rosca a una FH-M4 de la base (pem_fh_m4).
// ES REQUISITO DE COMPRA: sin la hoja no se verifica (HUECO H3 del papel).
flecha_pie  = 0.3;  // mm con 50 N: el MAXIMO que se compra, no una medida
alto_pie    = 10;   // D-T1: las de hoy; es el alto de la rendija del aire
d_pie       = 20;
```

`guarda_paticas()` se reescribe. La regla del muelle se va, y lo que se puede verificar es la geometría y el aire:

```python
def guarda_paticas(p: dict[str, float]) -> None:
    """La pata, desde el papel del suelo (2026-10-12).

    La regla de antes (una goma blanda contra los 100 Hz del toroide) se fue
    con el toroide. La pata es ahora parte de la entrada de aire: la rendija
    de alto_pie bajo la base. Lo que se asevera es que su disco cabe bajo la
    base, dentro de su contorno, porque sin la tabla no hay vuelo que lo
    tape. Lo que se compra (firme: <= flecha_pie con 50 N) no se puede
    verificar sin la hoja, y se publica como HUECO mientras falte."""
    x0, x1 = p["chaflan_nariz"], fondo(p) - p["chaflan_nariz"]
    for x, z, _d, tipo in _taladros_base(p):
        if tipo != "FH pata":
            continue
        r = p["d_pie"] / 2
        assert x0 <= x - r + 1e-9 and x + r <= x1 + 1e-9, (
            f"la pata de x={x:.2f} asoma por delante o por detras de la base "
            f"({x0:.2f}..{x1:.2f}): sin el vuelo de la tabla nadie la tapa")
        assert r <= z + 1e-9 <= p["ancho_total"] - r + 2e-9, (
            f"la pata de z={z:.2f} asoma por el costado de la base")
    print(f"paticas: {p['alto_pie']:g} mm, Ø{p['d_pie']:g}, bajo el canto de los "
          f"anillos y dentro de la base; su alto es la rendija del aire")
    _HUECOS.append(
        f"la hoja de la pata sin pedir: se compra firme (<= {p['flecha_pie']:g} "
        f"mm con 50 N, alto {p['alto_pie']:g} +- 0.2) y su casquillo tiene que "
        f"casar con la FH-M4 de la base (papel del suelo, HUECO H3)")
```

Antes de cambiarla se comprueba con `grep -n flecha_pie case/*.py case/cad/*.py` que `flecha_pie` no tiene otro lector.

`paticas()` en el `.scad` no cambia de expresión, porque `-t_base` ya vale 3. Su comentario («En X caen sobre los dos rieles de base») pasa a: `// Las cuatro patas bajo el canto de los anillos, roscadas a las FH-M4 de la base.`

- [ ] **Step 4: El canario de la persiana**

Se borra `canario_persiana_tabla()` con su llamada en `main()`. Su sujeto era que la persiana no pisara la tabla, y la base va a ras de los anillos, así que las dos cajas ya no se cruzan nunca. Lo que probaba de paso (que las cajas de la persiana están en `solapes()`) lo dice con un aserto de una línea en `solapes()`, junto a donde se arman las cajas:

```python
    assert {"persiana izquierda", "persiana derecha"} <= {c[0] for c in railes}, (
        "las dos persianas no estan entre las cajas que solapes() cruza")
```

- [ ] **Step 5: El `render_negro` y el BOM**

- PART `render_negro` (l.2370): se añade `bandeja_base();` a la lista, porque la base es aluminio negro.
- En `bom()`:
  - **La TABLA (l.3099-3121)** pasa a ser una línea de la BASE:
    ```
        echo(str("BOM: BASE de chapa 6082-T6 t=", t_base, " anodizada negra x1, ",
                 bandeja_base_ancho(), " x ", bandeja_base_fondo(),
                 " mm: campo de ", len(campo_base()), " agujeros de ", base_agujero,
                 " cada ", base_paso, ", 6 M5 de paso ", d_M5_base, ", 6 M4 de paso (nariz y talon desde abajo), ",
                 "4 FH-M4 (patas) y 4 M4 del chasis. Al taller de CHAPA: laser, desbarbado, anodizado y prensa."));
    ```
  - **Nariz y talón (l.2933-2997):** «tres M4 avellanados desde dentro» pasa a «tres M4 × 8 ISO 7380 de botón desde abajo, a tuercas CLS-M4 prensadas en su pie», en las dos piezas.
  - **Tornillos (l.3043-3057):** la cuenta conserva los 4 M4 del chasis. Los 6 M5 son ahora × 12 ISO 7380 de botón. Se añaden las líneas de PEM:
    ```
        echo("BOM: PEM CLS-M4 x6 (pies de nariz y talon), PEM FH-M4 x4 (base, patas); de acero o inoxidable, prensadas DESPUES de anodizar");
        echo("BOM: M5 x 12 ISO 7380 x6 (anillos a la base, desde abajo); M4 x 8 ISO 7380 x6 (nariz y talon, desde abajo)");
    ```
  - **Patas (l.3060-3070):** la línea dice «firmes: <= flecha_pie mm con 50 N, alto ± 0.2, roscadas a FH-M4 de la base». Fuera «AMPLIFICA los 100 Hz del toroide».

Run:
1. `cd case/cad && openscad -o /dev/null -D 'PART="bom"' sam17_case.scad 2>&1 | grep "BOM:" | head -40`
2. `cd case && python -c "import clearance_budget as cb; p = cb.leer_params(); cb.guarda_paticas(p); cb.guarda_talon(p); cb.canario_m4_desde_abajo(p)"`
3. `sh .githooks/pre-push < /dev/null`, en segundo plano.

Expected: las líneas nuevas del BOM sin `undef`, las guardas verdes, y la puerta verde con el HUECO de la pata entre los declarados.

- [ ] **Step 6: Commit**

```bash
git add case/cad/params.scad case/cad/sam17_case.scad case/clearance_budget.py
git commit -m "La pata se compra firme, el talón mide la tuerca de su pie, y el BOM lleva la base de chapa" -m "La regla del muelle contra los 100 Hz del toroide se va con el toroide. La pata es ahora el alto de la rendija del aire, y su hoja queda como HUECO. guarda_talon() mide el cuerpo de la tuerca CLS que asoma por dentro, y canario_m4_desde_abajo() la rompe con la tuerca en el doblez. Se retira canario_persiana_tabla(): la base va a ras de los anillos y la persiana ya no la pisa."
```

---

### Task 6: Los renders y las piezas

**Files:**
- Modify:
  - `case/renders/render.py`: `mad` (l.145-157) y el bbox (l.246-255);
  - `case/renders/render_persiana.py`: l.32-33, 45 y 60-65;
  - `case/renders/piezas.py`: l.29-39 y 79-87;
  - `case/cad/piezas.scad`: l.42-43;
  - `case/renders/render_bahia.py`: l.56-69 y 94-104;
  - `case/cad/export.ps1`: l.78-79.
- Regenerate: los PNG versionados que enseñan la tabla: `case/renders/sam17-persiana*.png` (cinco) y las vistas de la bahía si están versionadas.

**Interfaces:**
- Consumes: `bandeja_base()` (Task 3) y `paticas()`.

- [ ] **Step 1: Ver el estado de hoy**

Run: `cd case && grep -n "mad\b\|assembly_madera\|nogal\|madera" renders/*.py cad/piezas.scad cad/export.ps1`
Expected: los lectores de la madera que nombra el censo (a.5 y a.6).

- [ ] **Step 2: La base pasa al grupo negro, y las patas a un grupo propio**

- **`sam17_case.scad`:** `assembly_madera()` pasa a llamarse `assembly_patas()` y lleva solo `paticas();`. El PART `"assembly_madera"` pasa a `"assembly_patas"`. La base entra en `render_negro` (Task 5) y en `assembly_esqueleto()`.
- **`render.py`:** `mad = importar("assembly_madera")` pasa a `pat = importar("assembly_patas")`, con un material `goma` (Base Color (0.02, 0.02, 0.022), Roughness 0.85, el de la escena del acta). Se borra el material `nogal`, y el bucle del bbox pasa a `for obj in (acr, alu, pat)`. **El nombre `mad` se conserva como alias** (`mad = pat`) solo si algún guion lo borra por nombre; si no, se renombran los dos sitios (`render_persiana.py:32`, `piezas.py:79`) a `ns["pat"]`.
- **`render_persiana.py`:** se borra `("assembly_madera", "nogal_oscuro")` y la base sale en el negro (`render_negro`). La línea 45 (`mat("nogal_oscuro", …)`) se borra. Los encuadres se recalculan solos con el bbox, porque la tabla era lo más ancho.
- **`piezas.py`:**
  - `"madera": ["tabla", "paticas"]` pasa a `"negro"`, que gana `"base"`, y a un `"goma": ["paticas"]`;
  - `MATERIAL` pierde `nogal` y gana `goma`;
  - el grupo `acero` se queda.
- **`piezas.scad`:** `else if (PIEZA == "tabla") bandeja_base();` pasa a `else if (PIEZA == "base") bandeja_base();`.
- **`render_bahia.py`:** `mad = importar("assembly_madera")` pasa a importar la base sola. Se añade al `.scad` un `else if (PART == "assembly_base") bandeja_base();` y se importa con material negro. `ace = importar("assembly_acero")` se queda: el chasis sigue. En los textos, «la tabla con el chasis del PSU encima» pasa a «la base con el chasis del PSU encima».
- **`export.ps1`:** `"assembly_madera"` pasa a `"assembly_patas"`, y se añade `"assembly_base"`.

- [ ] **Step 3: Exportar y renderizar**

Run:
1. `cd case/cad && powershell -File export.ps1`
2. Los renders, con su invocación de siempre: `& "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" -b -P render_persiana.py` desde `case/renders/`, y lo mismo para `render.py` y `render_bahia.py`.

Expected:
- exit 0 y **ningún `Traceback` en el log**: Blender sale con 0 aunque reviente (memoria «Trampas de Blender en la piel»);
- los cinco `sam17-persiana*.png` regenerados, sin la losa de nogal y con la línea de sombra y las patas.

- [ ] **Step 4: Mirarlos**

Se abre cada PNG con la herramienta de leer (de uno en uno) y se comprueba:
- no queda nogal;
- la base negra se ve como una línea bajo el chaflán de la nariz;
- se ven las patas;
- el encuadre no corta el aparato.

Si un PNG enseña algo raro, se arregla la escena y se vuelve a renderizar ese PNG. No se commitea un render sin mirarlo.

- [ ] **Step 5: Las puertas, y commit**

Run (en segundo plano): `sh .githooks/pre-push < /dev/null`. Expected: verde.

```bash
git add case/renders/ case/cad/piezas.scad case/cad/export.ps1 case/cad/sam17_case.scad
git commit -m "Los renders enseñan la base de chapa negra y las patas, sin la losa de nogal" -m "assembly_madera pasa a assembly_patas y la base entra en el grupo negro. render.py, render_persiana.py, piezas.py y render_bahia.py dejan el material nogal, y los cinco renders de la persiana se regeneran."
```

---

### Task 7: Los papeles

**Files:**
- Modify: `case/PLIEGO.md`, `case/RFQ.md`, `case/README.md`.
- Modify: `docs/superpowers/specs/2026-08-15-case-design.md` (la spec maestra), `docs/superpowers/specs/2026-10-11-case-persiana-design.md` y `docs/superpowers/specs/2026-10-12-case-suelo-design.md`.

**Interfaces:**
- Consumes: las cifras impresas por `case/cad/suelo.py` (Task 2), `guarda_campo_base()` (Task 1), `guarda_piso()` (Task 4) y el BOM (Task 5).

- [ ] **Step 1: Sacar las cifras**

Run: `cd case && python cad/suelo.py && python clearance_budget.py 2>&1 | grep -E "^base:|^suelo:|aire:|costado|alfombrilla|paticas:"`
Expected: el número de agujeros y el área, la tabla del §5 con el campo real, la flexión con la mano y el salto. Se copian tal cual a los papeles (memoria «La cifra sale bien y la copio mal»: copiar del guion, no de memoria).

- [ ] **Step 2: PLIEGO**

- **Cabecera:** revisión nueva («rev. 29: el suelo»), una línea: la tabla se cambia por una base de chapa de 3 mm y se va el carpintero.
- **l.218-220 y 248:** la fila de `bandeja_base_2d` pasa a ser: `| bandeja_base_2d | 6082-T6, 3 mm, anodizado negro | taller de chapa | láser (agujeros salteados), desbarbado a máquina por las dos caras con la arista de arriba matada, planitud ≤ 1 mm suelta antes de anodizar, anodizado, y después la prensa de insertos (6 CLS-M4 van en los pies de nariz y talón; 4 FH-M4 en la base). El canto de abajo, R0,5 |`.
- **l.233-235 (la cuenta de DXF que no son de acrílico):** se actualiza, porque la madera sale.
- **§6.2, «La tabla — al carpintero» (l.585-631):** se borra.
- **§6.1, el anillo (l.523-526 y 560):** el punto de bonding gana el canto. «un círculo de Ø12 sin anodizar en el canto inferior, alrededor de un M5 por anillo, y el mismo en la base; arandela dentada bajo la cabeza; ≤ 0,1 Ω a cuatro hilos».
- **l.707-710 y 723-725 (anodizado y enmascarado):** entran la base y su círculo.
- **§7, condiciones de uso:**
  - «26 K sobre la sala» pasa a la cifra que imprime el Step 1 para el pesimista con un costado tapado;
  - se añade «sobre una superficie dura con los 10 mm de pata libres debajo: sobre un paño la base no respira», con la cifra que imprime el aviso del apoyo.
- **El ensayo de derrame (D-S10):** se añade un criterio: el agua que entra sale por la base y no se encharca en ella.
- **Los cables:** sus bridas pasan por los agujeros del campo, ya desbarbados.
- **l.763-764 (paticas):** «firmes, roscadas a FH-M4 de la base, nunca pegadas».
- **§8:** la fila `flecha de patica 0.25 mm | flecha_pie | guarda_paticas()` pasa a `pata firme <= 0.3 mm con 50 N | flecha_pie | HUECO H3 (hoja)`. Y se añade `base t=3, campo Ø5 cada 8, puente ≥ t | t_base, base_* | guarda_campo_base(), guarda_piso(), guarda_bandeja_base()`.

- [ ] **Step 3: RFQ**

- **Cabecera:** revisión nueva.
- **l.23-24:** la fila B pasa a ser «chapa de aluminio (y acero) | … tapa del valle, **base**, chasis ×3», y la fila C (carpintería) se borra.
- **§B (l.187-201):** la base entra en la lista. Se añaden tres preguntas:
  - «¿Insertan PEM (CLS-M4 en 1,5; FH-M4 en 3) después de anodizar, con agujero a cota sobre la pieza anodizada?»;
  - «¿Cortan unos 1 000 agujeros de Ø5 salteados sin pasar de 1 mm de planitud en 568 × 308 × 3?»;
  - «¿Enmascaran el círculo de Ø12 de la base?».
- **§C, carpintería (l.277-303):** se borra.
- **l.433-437 y 442-444 (anodizado y enmascarado):** entra la base.

- [ ] **Step 4: README**

- **Estado (l.26-34):** se sustituye «La tabla se va … su papel corto va después» por el bloque del suelo, con la fecha, el papel y las cifras del Step 1.
- **Tabla del aire (l.258-262):** fila nueva `| base (abajo) | <el área del Step 1> mm² en serie con la rendija de las patas | y = 0 |`. Las l.302-305 se actualizan con las cifras del Step 1.
- **BOM:**
  - fila del anillo (l.799): «con el punto de bonding enmascarado en su cara interior y en el canto, alrededor de un M5»;
  - l.803-806 (talón y nariz): «pie de 22.5 sobre la base, tres M4 × 8 de botón desde abajo a tuercas CLS-M4 de su pie»;
  - l.813 (tuerca remachable del chasis): se queda, y «a la tabla» pasa a «a la base»;
  - l.820: la fila de la TABLA pasa a la de la BASE (6082-T6, 3 mm, 568,62 × 307,76, campo y taladros);
  - l.822 (patas): el criterio firme;
  - l.831-838: la cuenta de tornillos;
  - las PEM, en su fila.
- **Montaje (l.956-1021):** se reescribe con el orden del §3.6 del papel.
  1. En el banco, la base con la nariz y el talón: sus seis M4 desde abajo, a las tuercas de sus pies.
  2. La base, de canto sobre el tramo de abajo del anillo A.
  3. El anillo B.
  4. El chasis al final por el frente, con sus cuatro M4 desde abajo.
  5. Las patas, a sus FH-M4.

  Y el servicio: se voltea, se sueltan los doce tornillos de la base y la base baja con el chasis.
- **Pendientes (l.1111-1115):** sale «Especie y humedad de la tabla», y entran «las hojas de PEM y de la pata (H3, H4)».
- **l.18 (el render incrustado):** apunta al PNG regenerado (Task 6).

- [ ] **Step 5: Las specs**

- **La spec maestra.** Un bloque de enmienda tras la rev. 29, con la fecha, el papel y una línea por cambio. Se reescriben:
  - l.498 (la fila de `t_base`: «base de chapa, 3 mm»);
  - l.519-526 y 568-584 (la tabla como suelo);
  - l.614 (los pies);
  - l.707 y 715;
  - l.755-779 (el orden).

  La historia se queda.
- **La persiana.**
  - l.275, §12: `**firmada 11-10 («uno»), **en espera**…` pasa a `firmada «uno» y después «quitar» (11-10, 23:00): la ejecuta el papel 2026-10-12-case-suelo-design.md`.
  - l.51: `D-S4 (§8) → quitar, papel del suelo`.
- **El suelo.**
  - El Estado gana una línea «**Implementado el** …», con la fecha del día, la rama `docs/case-suelo` y el número del PR. El PR se abre en el cierre, así que esta línea se añade con `--fixup` justo antes del merge.
  - §3.4 y §9: «los dos pies crecen medio milímetro» pasa a «el M4 se aleja del canto libre del pie a `pem_borde` = 7,0 (SUPUESTO, H4); los pies no cambian: `m4_x` se medía desde el canto libre, así que crecer el pie no lo apartaba (enmienda del plan)».
  - §7: «`t_base` (30) pasa a `t_suelo` (3)» pasa a «`t_base` pasa de 30 a 3 y la pieza conserva sus nombres: «suelo» ya nombra cinco cosas en el código».
  - §5: la tabla, con las cifras del Step 1 (el campo real) en lugar de las de 20 000.

- [ ] **Step 6: La puerta de los papeles, y commit**

Run (en segundo plano): `sh .githooks/pre-push < /dev/null`
Expected: verde. `papel_trae_los_desarrollos()` sigue verde, porque los blanks de nariz y talón no cambian (los pies no crecen).

```bash
git add case/PLIEGO.md case/RFQ.md case/README.md docs/superpowers/specs/
git commit -m "Los papeles del case cuentan la base de chapa: pliego, RFQ, README, la spec maestra y las enmiendas" -m "Sale el carpintero. La base entra en el taller de chapa con sus cuatro cláusulas: láser, desbarbado, anodizado y prensa. El anillo enmascara el canto para la masa de la base. El pliego gana la condición del apoyo sobre superficie dura y la pata firme. El papel del suelo deja escrito que el M4 se aparta del canto libre y que los pies no crecen."
```

---

## Cierre (fuera de las tareas)

1. **Revisión final de toda la rama**, con un revisor nuevo en el modelo más capaz, con este plan, el papel y el ledger.
2. **PR** contra `main`, con el texto en español y el cambio solo. **Merge**, autorizado.
3. **Issues:**
   - un comentario en **#203**: el descuadre se prueba con la base de chapa y sin paneles (H5);
   - **issue nuevo, el relevo de la v5 en el case** (H1):
     - el chasis encogido a la placa C;
     - el PE frente a la M2;
     - el conector del cordón y su retención;
     - la salida de cables del chasis, que desde el 27-08 atraviesa el suelo hacia la mesa;
   - **issue nuevo, las hojas y las medidas del suelo** (H2, H3, H4): el canal medido en la primera unidad, la hoja de la pata y las hojas de PEM;
   - un comentario en **#130**: su pieza ya no va a la tabla.
