# Fuente v3 «GOAT de verdad» — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Llevar la fuente de «diseñada y pedible» a «GOAT, y demostrado». Cierra las tres cosas que hoy lo impiden —la protección razona sobre un chip que se fue, el número de portada nunca se midió, y el toroide no tiene pantalla frente a la SMPS que metimos— y añade lo decidido el 2026-08-18: chasis de acero que disipa, y telemetría que le deja saberse a sí misma.

**Architecture:** La cascada de regulación de la v2 no se toca (LM2941/LM2991 → LT3045×2/LT3094×2). Lo que cambia es todo lo que la rodea: los tres TO-220 pasan de disipadores Fischer individuales a atornillarse contra la pared de un chasis de acero cerrado —lo que obliga a ponerlos **en fila sobre un canto con los tabs coplanares**, y eso solo ya es otra placa—; entra un crowbar en −12 V que la v2 no tiene; y entra una isla de telemetría (2× INA226 + ADS1115 + TMP1075) tras una barrera ISO1541.

**Tech Stack:** Python 3 + `pcbnew` (KiCad 10), `kicad-cli`, OpenSCAD para el chasis (mismo pipeline que el case), `gh` CLI.

**Spec:** `docs/superpowers/specs/2026-08-18-fuente-chasis-telemetria.md` (chasis y telemetría) sobre `docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md` (topología de regulación, que no se toca). Léelas las dos antes de la primera tarea, junto con `hardware/01-power-supply/notes/design-notes.md` §13–§18.

## Global Constraints

- **La v3 es la que se construye.** v1 y v2 son las dos de papel; esta es el tercer diseño y la primera placa. **Lo que no quede decidido al cerrar la Fase A sale con huella y `DNP`, nunca con una v4.** Si algo se pretende aplazar, se aplaza como componente no poblado, no como versión.
- **Nada se pide hasta cerrar la Fase A.** Todo lo que toca cobre entra en un solo diseño.
- **La v2 no se edita.** Queda intacta como diseño documentado, igual que la v1 (precedente del 2026-08-17). La v3 hereda por copia y declara qué cambia.
- Todo número de datasheet usado para una decisión es el **garantizado (mín/máx), no el típico**, y lleva cita: fabricante, documento, revisión, página (lección v1 §16.1). Solo fuentes primarias — jamás agregadores.
- **El chasis conduce calor, nunca corriente.** Los tres tabs van aislados; lo único que toca el chasis eléctricamente es el espárrago de PE (spec 2026-08-18 §3.2).
- Placa **2 capas, FR-4 1.6 mm, cobre 1 oz, SMD en una sola cara**; barrera de red **≥ 6 mm**. El tamaño **deja de estar congelado en 150×200** — lo fija la Fase C contra el chasis.
- Rieles **±12.000 V**, envelope **650 mA/riel**, objetivo de ruido **0.8 µVrms (10 Hz–100 kHz)** — dato de datasheet, jamás se presume medido hasta la Fase E.
- Docs y comentarios en español, tono directo del repo. **Una rama por fase, PR + merge al cierre**; lo aplazado se abre como issue con evidencia.

---

## FASE A — Lo que decide el cobre (rama `feat/psu-v3-decisiones`)

Bloquea todo lo demás. Son tres decisiones de papel y ninguna necesita una pieza.

### Task 1: `check_absmax.py` — el censo de máximos absolutos, ejecutable

**Files:**
- Create: `hardware/01-power-supply/v3/check_absmax.py`
- Create: `hardware/01-power-supply/v3/absmax.csv`

El #114 salió de leer §16.8 y notar que razona sobre el AS3340. La forma de que no vuelva a pasar no es reescribir el párrafo: es que el análisis sea **un script que falla** cuando el BOM y la protección se desincronizan.

- [ ] **Step 1: Escribir `absmax.csv` — el contrato**

Una fila por familia de chip que cuelgue de los rieles, con su límite **y su cita**. Los cuatro que ya están verificados:

```csv
chip,modulo,vmax_total,vmax_riel,fuente
TL074,todos,42,,TI SLOS080W rev. JUL-2025 tabla 5.1
LM13700,05-vcf 07-vca,36,18,TI SNOSBW2F tabla 6.1
LM358,06-adsr,32,16,TI SLOS068AB rev. OCT-2024 tabla 5.1
SSI2130,03-vco,,18,Sound Semiconductor SSI2130 ABSOLUTE MAXIMUM RATINGS
```

`vmax_riel` vacío = el datasheet solo acota el total. `SSI2130` no lleva
`vmax_total` porque su V+ no cuelga del bus: viene del L78L05 local del módulo 3.

- [ ] **Step 2: Escribir el test que falla hoy**

```python
def test_fallo_de_riel_negativo_no_pasa_ningun_absmax():
    """U2 en corto pone VRAW- en el bus. Hoy no hay crowbar en -12 V."""
    victimas = chips_fuera_de_rango(v_pos=12.0, v_neg=-20.54)
    assert victimas == [], f"fuera de abs max sin proteccion: {victimas}"
```

- [ ] **Step 3: Correrlo y ver que falla por la razón correcta**

```
Run: python hardware/01-power-supply/v3/check_absmax.py
Esperado: FALLA nombrando SSI2130, LM13700 y LM358
```

Si nombra otros o nombra menos, el `absmax.csv` está mal, no el test.

- [ ] **Step 4: Escribir el escrutinio de los dos fallos y el escenario protegido**

Tres casos, no uno: `U1` en corto (+20.54 / −12), `U2` en corto (+12 / −20.54), y
los dos rieles sanos con crowbars actuando a su umbral peor caso (16.4 V). El
tercero es el que dice si la protección **basta**, no solo si existe.

- [ ] **Step 5: Commit**

```bash
git add hardware/01-power-supply/v3/
git commit -m "El censo de maximos absolutos deja de ser un parrafo y pasa a ser una puerta"
```

### Task 2: El crowbar de −12 V y el I²t del lazo

**Files:**
- Modify: `hardware/01-power-supply/notes/design-notes.md` §16.8
- Create: `hardware/01-power-supply/v3/notes/design-notes.md` (§1: protección)

**Interfaces:**
- Consume: el veredicto de `check_absmax.py` (Task 1)
- Produce: las filas de `Q2`, `D8`, `R3`, `C15` para el `bom.csv` de la Task 3

- [ ] **Step 1: Reescribir §16.8 contra el BOM real**

La tabla actual nombra AS3340. La nueva nombra SSI2130, LM13700, LM358 y TL074
con su cita, y dice explícitamente lo que cambió y desde cuándo — misma
disciplina que el resto del §16. Incluye la frase que hoy falta:

> El SSI2130 no cuelga del bus por su V+: viene del L78L05 del propio módulo 3.
> Un fallo de +12 V lo absorbe el regulador local, no el crowbar. El crowbar de
> +12 V sigue haciendo falta, pero por el LM13700 y el LM358.

- [ ] **Step 2: Dibujar el crowbar de −12 V**

Misma topología, espejada. **No es el mismo circuito girado** — el gate del
BT169D se refiere a su cátodo, que en el riel negativo ya no está en masa:

```
GND ──── anodo BT169D ──── catodo a -12V
                  gate ──┬── R3 1k ──── -12V
                         └── C15 100nF ── -12V
         BZX55C15 entre GND y el gate, catodo a GND
```

Verificar el sentido del zener sobre el esquemático antes de congelar: montado
al revés dispara al encender, que es exactamente el fallo que §16.8 documenta
para el `D7` del riel positivo.

- [ ] **Step 3: Verificar el I²t del lazo crowbar → F1**

Esto **aplica también al crowbar que ya existe en +12 V**, así que si el número
no sale, el problema es de hoy y no de la v3.

```
F1 = 1.6 A T   (subio desde 250 mA en la v2, worksheet notes v2 §3.0.1)
Q1/Q2 = BT169D, 0.8 A nominal
```

Buscar el `I_TSM` del BT169D en su datasheet primario (NXP/WeEn) y la curva
tiempo-corriente del fusible concreto. La pregunta es una sola: **¿sobrevive el
SCR el tiempo que tarda F1 en abrir?** Si no, la salida es un SCR mayor, no un
fusible menor — bajar F1 rompe lo que el #61 arregló.

- [ ] **Step 4: Cerrar #114 con el veredicto y correr Task 1 en verde**

- [ ] **Step 5: Commit**

### Task 3: La telemetría — el contrato en `bom.csv`

**Files:**
- Create: `hardware/01-power-supply/v3/bom.csv`

**Interfaces:**
- Produce: las referencias que consumen las Tasks 5, 6 y 7

- [ ] **Step 1: Fijar el reparto de medidas y escribir por qué**

No todos los rieles se miden igual, y la razón es que **la corriente del riel
negativo es la medida menos valiosa de las cuatro y con diferencia la más
difícil** — un INA226 mide un shunt referido cerca de su propia alimentación, y
en −12 V eso obliga a un segundo dominio aislado por una medida que casi no se
usa. El reparto:

| Riel | Qué se mide | Con qué |
|---|---|---|
| +12 V | tensión **y** corriente | INA226 |
| +5 V | tensión **y** corriente | INA226 |
| −12 V | **solo tensión**, por divisor a referencia positiva | canal del ADS1115 |
| VRAW+ | tensión, por divisor | canal del ADS1115 |
| VRAW− | tensión, por divisor | canal del ADS1115 |
| recinto | temperatura | TMP1075 |

El ADS1115 entra por los dos VRAW, no por el −12 V: **el valle de VRAW es el
número contra el que se pelearon todas las decisiones grandes de esta fuente
—los 9400 µF, el toroide de 120 VA, los 13.6 V de `U1`— y hasta hoy solo existe
simulado.** Medirlo en continuo es lo que convierte §16.5 de simulación en
hecho. Esa fila sola justifica el chip.

**Huella de shunt en −12 V, poblada con 0 Ω.** Si el bring-up pide corriente en
ese riel, se cambia por el shunt y se resuelve entonces — no se diseña hoy por
si acaso (constraint de la v4).

- [ ] **Step 2: Escribir las filas nuevas del `bom.csv`**

```csv
U8,INA226AIDGSR — monitor I/V I2C 16 bits,VSSOP-10,1,LCSC,,Riel +12V. A0/A1 a GND -> 0x40
U9,INA226AIDGSR,VSSOP-10,1,LCSC,,Riel +5V. A0 a VDD -> 0x41
U10,ADS1115IDGSR — ADC 16 bits 4 canales I2C,VSSOP-10,1,LCSC,,VRAW+/VRAW-/-12V por divisor. ADDR a GND -> 0x48
U11,TMP1075DSGR,WSON-8,1,LCSC,,Temperatura del recinto. Misma pieza que el modulo 3 -> driver ya escrito
U12,ISO1541D — aislador I2C bidireccional,SOIC-8,1,LCSC,,Barrera GNDA/GNDD. Ver spec 2026-08-18 §4.3
R_SH1,Shunt 20 mohm 1% 1W,R_2512,1,LCSC,,Shunt del +12V para U8. Kelvin obligatorio
R_SH2,Shunt 20 mohm 1% 1W,R_2512,1,LCSC,,Shunt del +5V para U9
R_SH3,0 ohm — HUELLA DE SHUNT SIN USAR,R_2512,1,LCSC,,Riel -12V. Puente hoy; se cambia por shunt si el bring-up pide corriente en ese riel
```

Los divisores del ADS1115 van con **resistencias del 0.1 %**: el error de
división entra directo en la lectura del valle, y el valle es el número que
decide si la fuente regula.

- [ ] **Step 3: Verificar direcciones I²C contra el mux**

`architecture-poly.md` §8 tiene un mux I²C porque todas las EEPROM de identidad
responden en 0x50. La fuente toma **un canal**; dentro de ese canal 0x40, 0x41,
0x48 y la del TMP1075 no colisionan entre sí ni con 0x50. Escribirlo en el
`bom.csv` y en las notas, no dejarlo a la memoria.

- [ ] **Step 4: Confirmar el tope del #104 contra la curva de derating**

Leer la curva de la IRM-15-5 (su rango es −30 a +85 °C «refer to Derating
Curve», y esa curva no se ha leído). Al tope de 2.80 A la SMPS entrega **el
100 % de sus 15 W dentro de un recinto cerrado a +7.5 °C sobre ambiente**. Si
el codo cae por debajo de eso, el tope del #104 baja, y baja hoy.

- [ ] **Step 5: Commit + PR + merge de la Fase A**

---

## FASE B — El esqueleto y el esquemático (rama `feat/psu-v3-schematic`)

### Task 4: Módulo v3 — qué se hereda y qué cambia

**Files:**
- Create: `hardware/01-power-supply/v3/README.md`
- Create: `hardware/01-power-supply/v3/build_schematic.py` (copia de la v2)

- [ ] **Step 1: Copiar la v2 entera y declarar el delta en el README**

El README abre con una tabla de **qué cambia respecto de la v2 y por qué**, no
con una descripción de la arquitectura (que es la misma). Cuatro filas:

| | v2 | v3 | por qué |
|---|---|---|---|
| Disipación | 3 Fischer individuales | tabs contra la pared del chasis | Tj de `U2` 101 → 62 °C |
| Colocación de los TO-220 | diagonal opuesta a la isla SMD | **en fila sobre un canto, tabs coplanares** | lo impone la pared |
| Protección | crowbar solo en +12 V | crowbar en los dos rieles | #114 |
| Instrumentación | 6 test points | test points + isla de telemetría | spec 2026-08-18 §4 |

- [ ] **Step 2: Dejar escrito que la v2 no se toca** y por qué (precedente del 2026-08-17 con la v1)

- [ ] **Step 3: Commit**

### Task 5: Esquemático — crowbar negativo e isla de telemetría

- [ ] **Step 1: Escribir el test de paridad BOM ↔ hoja**

El `check_bom.py` de la v2 ya cruza `bom.csv` contra el esquemático. Correrlo
contra el `bom.csv` de la Task 3 **falla**, nombrando U8–U12 y R_SH1–3. Ese es
el rojo.

- [ ] **Step 2: Añadir el crowbar de −12 V** con la referencia de gate de la Task 2

- [ ] **Step 3: Añadir la isla de telemetría**

Reglas que no son opcionales:

- Los shunts van con **conexión Kelvin**: las pistas de sensado salen de los
  pads del shunt, no del cobre de potencia. Un shunt de 20 mΩ leído por su
  cobre de alimentación mide el cobre, no el shunt.
- El `ISO1541` parte el mundo: **U8–U11 en GNDA, el bus de salida en GNDD.** El
  plano no cruza la barrera.
- Divisores del ADS1115 al **0.1 %**, y su referencia positiva **no** es el
  +12 V del instrumento: es el +5 V local, para que un fallo del riel medido no
  se lleve el medidor.

- [ ] **Step 4: `check_bom.py` en verde + ERC limpio**

- [ ] **Step 5: Commit + PR + merge de la Fase B**

---

## FASE C — La PCB, con la restricción mecánica nueva (rama `feat/psu-v3-pcb`)

### Task 6: Colocación — los tres TO-220 en fila

**Interfaces:**
- Consume: la geometría del chasis de la Fase D (Task 9). **Esta tarea y la
  Task 9 se cierran juntas o ninguna**: el canto de la placa y la pared del
  chasis son la misma cota vista desde dos lados.

- [ ] **Step 1: Escribir la puerta de coplanaridad**

Un check nuevo en el `build_pcb.py` heredado: los tres TO-220 tienen que estar
**en la misma X (o Y), con la misma orientación, y a la misma distancia del
canto**, con tolerancia de 0.2 mm. Si alguien los mueve, sale en rojo antes de
los gerbers, no al ir a atornillar.

```python
def test_to220_coplanares():
    tabs = [pos_tab(r) for r in ("U1","U2","U3")]
    assert max(t.y for t in tabs) - min(t.y for t in tabs) < 0.2
    assert len({t.rot for t in tabs}) == 1
```

- [ ] **Step 2: Colocar los TO-220 en fila y fijar el tamaño de placa**

Los 150×200 de la v2 **dejan de estar congelados**: el ancho lo fija el chasis.
La cota que manda es la distancia del canto de la placa al tab, que tiene que
casar con la pared.

- [ ] **Step 3: La isla de telemetría, en la diagonal opuesta a los TO-220**

Mismo criterio que la isla ultra de la v2 §6: lejos del calor y lejos del lazo
puente→bulk, que es el peor radiador de la placa.

- [ ] **Step 4: Correr las puertas heredadas de la v2** (islas, barrera de red, cortesía de silk)

- [ ] **Step 5: Commit**

### Task 7: Routing, DRC y fabricación

- [ ] **Step 1: Rutear** con la disciplina de islas de la v2 §6
- [ ] **Step 2: DRC limpio + refill de zonas**
- [ ] **Step 3: Gerbers, drill, pos y BOM de ensamblaje JLC** con el pipeline de la v2
- [ ] **Step 4: Re-verificar stock LCSC el día de mandar** (#57) — incluidos U8–U12
- [ ] **Step 5: Commit + PR + merge de la Fase C**

---

## FASE D — El chasis (rama `feat/psu-v3-chasis`, paralela desde la Fase A)

### Task 8: Medir el toroide y decidir la pantalla

- [ ] **Step 1: Decidir toroide apantallado antes de comprar**

Metimos una SMPS conmutada compartiendo red y recinto sellado con una fuente
construida para microvoltios. Su ruido de modo común pasa del primario al
secundario por la capacidad entre devanados **salvo que el toroide lleve
pantalla electrostática**. Talema las hace. Nada está comprado: se decide ahora
o no se decide nunca.

- [ ] **Step 2: Medir la pieza física** — diámetro, alto y **peso**

El peso cierra a la vez la estimación de masa del #106 y el margen del #46. El
alto de catálogo (45 mm) nunca se confirmó.

- [ ] **Step 3: Meter el diámetro en `params.scad`** — hoy solo está el alto

### Task 9: El chasis paramétrico

**Files:**
- Modify: `case/cad/sam17_case.scad` (PART nuevo), `case/cad/params.scad`
- Modify: `case/clearance_budget.py`

El chasis **vive en el modelo del case**, no en un archivo suelto: así hereda
`export.ps1`, el presupuesto de holguras y la puerta de relectura de DXF que ya
existen. Sale como patrón plano para doblar.

- [ ] **Step 1: La holgura, primero**

```python
assert alto_chasis + alto_pie < p["alto_interior_inferior"]      # 125.13
assert ancho_chasis <= fondo_bandeja_base                        # 223.26
assert diam_toroide + 2*pared + holgura <= alto_chasis_interior
```

- [ ] **Step 2: Dibujar el patrón plano** con pestañas de doblado y los tres
      agujeros de los TO-220 casando con la Task 6
- [ ] **Step 3: El paso del espárrago de PE**, y la salida de cables por el
      recorte de 104 × 32 que la bandeja ya lleva cortado
- [ ] **Step 4: `export.ps1` + `check_dxf.py` en verde**
- [ ] **Step 5: Commit + PR + merge de la Fase D**

---

## FASE E — La medida que da el título (rama `feat/psu-v3-validacion`)

Sin esta fase la v3 es una fuente muy buena con una etiqueta que nadie verificó.

### Task 10: El LNA de medida (#58)

- [ ] Construir el amplificador de bajo ruido que hace falta para ver 0.8 µVrms.
      **Es un instrumento aparte y no depende de la fuente**: puede empezar el
      día uno, en paralelo con toda la Fase A.

### Task 11: Bring-up con telemetría

- [ ] **Step 1:** Protocolo heredado de la v2 Task 10, más las filas nuevas de
      la spec 2026-08-18 §7
- [ ] **Step 2: Calibrar el estimador del #104** — dos lecturas del INA del
      +5 V (cadena apagada y cadena a duty conocido) despejan `Iq` y `k`
- [ ] **Step 3: Medir el valle de VRAW** con el ADS1115 a carga real y
      compararlo contra los 14.12 V simulados de §16.5. **Es la primera vez que
      ese número se ve.**
- [ ] **Step 4: Medir los 0.8 µVrms** con el LNA, con el I²C corriendo y en
      silencio. Las dos medidas: la diferencia dice si el ISO1541 valió la pena.
- [ ] **Step 5: Termopar en la pared del chasis** tras 2 h con los LED al tope,
      contra los +7.5 °C calculados
- [ ] **Step 6: Publicar los números medidos** en el README de la v3, al lado
      de los calculados, con la fecha. **Un número medido nunca sustituye al
      calculado en silencio: se ponen los dos.**

---

## Lo que este plan NO cubre

- El firmware de la telemetría (driver, cadencia, qué hace el autoafinado con
  el dato) — es del lado digital, epic #29.
- La política de prioridades del #104, que no cambia: guía de patcheo nunca se
  atenúa, farol cede primero.
- La elección de taller de doblado y su precio.
- El respin de los módulos 4-7, cuyos `bom.csv` siguen siendo los esqueletos de
  la tesis del 2026-04-16 (#78, #79). El `absmax.csv` de la Task 1 se
  re-verifica cuando existan.
