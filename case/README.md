# Case SAM17 — consola de dos pisos en acrílico naranja

Spec: [`docs/superpowers/specs/2026-08-15-case-design.md`](../docs/superpowers/specs/2026-08-15-case-design.md) (rev. 3)
Board de intención: [`renders/propuesta-diseno-2026-08-16.png`](renders/propuesta-diseno-2026-08-16.png)

## Formato: propio, no Eurorack

Pregunta abierta desde la tesis, ya resuelta: el SAM17 usa un **formato
propio**, no el estándar Eurorack. `alto_panel = 190 mm`
([`cad/params.scad`](cad/params.scad)) frente a los 128.5 mm de un
Eurorack 3U. Consecuencia: los paneles del SAM17 no son intercambiables con
módulos Eurorack comerciales — ni en alto de panel ni en el sistema de
montaje (rieles 2020 a `sep_railes = 180 mm` entre centros, no HP). Quien
busque compatibilidad Eurorack necesita un case aparte.

**Dimensiones** (salida real de `clearance_budget.py` a la fecha de este
documento): alto total 391.5 mm, altura de entrepiso 235.8 mm, ancho útil
entre costados 484 mm (`ancho_total = 500 mm` menos 2×`t_cheek`). Kerf
aplicado por defecto: **−0.20 mm** — negativo a propósito (el láser
ensancha y el dibujo compensa restando; el paso 2 del cupón lo desarrolla
con números). Magnitud provisional: la confirma el cupón.

**Ancho mínimo de panel: 15.40 mm** (= 2×`inset_tornillo` + `d_M3_paso` +
2 mm de puente — guarda de
[`panels/build_template.py`](panels/build_template.py), Task 7). Un panel
más angosto superpone los dos taladros M3 de una misma cara; la plantilla
lo rechaza citando ese mismo número, antes de dibujar nada.

## Regenerar todo

```powershell
python -m pip install ezdxf   # una vez; lo usa check_dxf.py
powershell -File cad/export.ps1
```

Corre `clearance_budget.py` ANTES de exportar y `check_dxf.py` DESPUÉS —
relee los DXF tal como los verá el láser; si cualquiera de los dos está en
rojo, el script sale con código distinto de cero y no se exporta ni se deja
nada a medias. Los DXF van en mm; decírselo explícito al servicio de corte.

La plantilla KiCad de panel se regenera aparte, con el Python de KiCad (no
el del sistema, porque importa `pcbnew`):

```powershell
"C:/Program Files/KiCad/10.0/bin/python.exe" case/panels/build_template.py --ancho 100
```

### Criterio de regeneración limpia — tres clases, no una

`export.ps1` y `build_template.py` **no** producen los mismos bytes en cada
corrida, y eso es esperado, no un fallo — un `git status` que exige
identidad byte a byte da falso rojo en dos de las tres clases de artefacto.
Verificado corriendo cada export 3 veces (el estado commiteado + 2
regeneraciones desde cero, Task 10) y comparando con SHA-256:

| Clase | ¿Byte-idéntico? | Qué SÍ es estable | Mecanismo |
|-------|:---:|---|---|
| **DXF** (`case/plans/*.dxf`) | **SÍ** | Todo — 8/8 archivos con el mismo SHA-256 en las 3 corridas | OpenSCAD 2021.01 emite R12 determinista para geometría 2D |
| **STL** (`case/renders/build/*.stl`) | **NO** | El tamaño en bytes: `assembly_aluminio.stl` midió 25457 B las 3 veces, `assembly_acrilico.stl` 2478678 B las 3 veces | CGAL no garantiza el orden de facetas al triangular. `assembly_aluminio.stl` cambió de SHA-256 en las 2 regeneraciones (3 hashes distintos en 3 corridas); `assembly_acrilico.stl` coincidió por azar en esta muestra — no asumir que un STL se mantiene solo porque coincidió una vez |
| **`.kicad_pcb`** (`case/panels/panel-template.kicad_pcb`) | **NO** | El *conjunto* de bloques top-level (posiciones de footprint, geometría de taladros y contorno) una vez se descartan las líneas `(uuid ...)`: 17/17 bloques idénticos en las 3 corridas, verificado por comparación estructural (no diff lineal) | KiCad reacuña un UUID nuevo por objeto en cada guardado y además **rota cíclicamente** el orden de los bloques `(footprint ...)` — un `diff` de texto sobre dos corridas muestra decenas de líneas cambiadas sin que ninguna posición real se haya movido |

**Criterio de verificación correcto por clase** (el que aplica Task 10, y el
que debe aplicar cualquier regeneración futura):

- **DXF**: `git status --short` tiene que salir vacío tras regenerar.
  Cualquier diff en un `.dxf` es un hallazgo real — algo cambió que no
  debería (`params.scad` o el propio script).
- **STL**: comparar tamaño en bytes, nunca el hash ni un diff. Un STL
  committeado que cambia de *tamaño* tras regenerar sin tocar `params.scad`
  sí es un hallazgo; un hash distinto con el mismo tamaño no lo es.
- **`.kicad_pcb`**: comparar el conjunto de bloques top-level con los
  `uuid` quitados, nunca un diff lineal ni el hash completo del archivo.

Por eso `case/renders/build/*.stl` y `case/panels/panel-template.kicad_pcb`
pueden aparecer como `M` en `git status` después de un `export.ps1` /
`build_template.py` limpios sin que haya ningún hallazgo real detrás. Antes
de investigar un diff en esos dos archivos: regenerar dos veces más y
comparar las regeneraciones *entre sí* con el criterio de su clase, no
contra lo commiteado con un diff de texto.

(Nota aparte, sin relación con lo anterior: `panel-template.kicad_pcb`
mide 7270 B recién escrito por `pcbnew` en Windows —CRLF— y 6905 B leído
del blob de git con `git show` —LF—, por `core.autocrlf=true`. Es la
misma conversión de fin de línea de siempre, no una cuarta clase de
no-determinismo.)

## Artefactos que NO van al repositorio

`case/renders/build/*.stl` se regenera con `cad/export.ps1` y **no se versiona**
(issue #48). Son ~6,6 MB que cambian entera cada vez que se mueve un milímetro,
y no aportan nada que el `.scad` no tenga: quien quiera el STL lo exporta.

`case/plans/lienzo_2d.dxf` va por el mismo camino: es la preview de las 7 piezas
en rejilla, no se manda a ningún sitio, y son otras 97.512 líneas de diff.

Lo que sí se versiona son los **siete DXF sueltos** de `case/plans/` — esos son
el entregable que va al taller, y su diff es la prueba de qué se mandó a cortar
y cuándo.

## Procedimiento del cupón — sólo si se vuelve al láser

**Con el proceso actual (fresado CNC) este procedimiento NO aplica y `kerf`
vale 0.** El CAM del taller compensa el radio de herramienta como parte normal
del trabajo y la pieza sale a la cota del dibujo, con la tolerancia de
producción del taller (Schaeffer publica 0.05–0.10 mm).

Se conserva entero porque el láser sigue siendo una alternativa viable, y
porque el día que se vuelva a él hay que hacer esto **dos veces, una por
espesor**: la franja del láser no es la misma en 5 que en 8 mm, y `params.scad`
tiene un único `kerf`. Ese día hay que partirlo antes de cortar nada.


1. Cortar [`plans/coupon.dxf`](plans/coupon.dxf) en el acrílico REAL con la
   máquina REAL. El cupón se dibuja CRUDO, sin kerf: es la pieza que lo mide.
   Cada escalera tiene 11 peldaños, de 0.5 mm por debajo del diámetro nominal
   del tornillo a 0.5 por encima, en pasos de 0.1 (M3: 2.5 → 3.5 dibujados).
2. **El `kerf` de `params.scad` es NEGATIVO.** Probar los tornillos M3/M4/M5
   en las escaleras y anotar el peldaño —el diámetro DIBUJADO— en el que el
   tornillo entra firme sin forzar. Ese ajuste firme se da cuando el agujero
   FÍSICO mide más o menos el diámetro nominal del tornillo (3.0 / 4.0 / 5.0),
   así que:

   ```
   canal del láser = diámetro nominal del tornillo − peldaño dibujado que ajusta
   kerf            = − canal del láser
   ```

   Ejemplo numérico completo (los números son de ejemplo, el procedimiento
   no): el M3 entra firme en el peldaño **dibujado 2.7 mm**. Un M3 entra firme
   en un agujero físico de ~3.0 mm, así que el láser se comió
   3.0 − 2.7 = **0.30 mm** de canal → `kerf = -0.30`.

   Comprobación de que el signo es el correcto, porque es el error caro: el
   modelo dibuja todo hueco como `d + kerf`. Con `kerf = -0.30`, un agujero de
   paso M3 se dibuja a 3.4 − 0.30 = 3.10 mm y sale físico a 3.10 + 0.30 =
   **3.40 mm**, que es el nominal buscado. Con `kerf = +0.30` saldría a
   **4.00 mm**: 0.6 mm de más, tornillo bailando en cada agujero de tuerca T
   de las bandejas. Si el servicio te da un kerf de tabla (siempre positivo, es
   el ancho del canal), va a `params.scad` **con el signo cambiado**;
   `clearance_budget.py` avisa en AMARILLO si el valor entra positivo.
3. Probar la ranura con el perfil 2020 y la lengüeta con arandela+tuerca
   (apretar hasta marcar, NO hasta fisurar; anotar sensación de tope).
3b. **Confirmación anti-circular** (lección de projects/vectorizer): el kerf
    elegido en el paso 2 se confirma con un ajuste INDEPENDIENTE — la
    ranura del 2020 del paso 3 y un tornillo en una escalera DISTINTA de la
    que lo fijó. Medir los mismos agujeros que definieron el kerf siempre
    "pasa".
4. Registrar aquí: fecha, proveedor, material, espesor MEDIDO con calibre,
   máquina, kerf medido → actualizar `params.scad` y re-exportar.

| fecha | proveedor | material | espesor medido | máquina | kerf |
|-------|-----------|----------|----------------|---------|------|
| (pendiente) | | | | | |

## BOM de herrajes

Salida real de `openscad -D 'PART=\"bom\"' cad/sam17_case.scad` — los 4
`echo` del modelo (recontar tras cualquier cambio a `params.scad`):

| Pieza | Cantidad | Nota |
|-------|----------|------|
| Larguero perfil 2020 | 11 | de 484 mm (`ancho_util`) cada uno |
| Tornillo M5 botón | 22 | 2 por larguero, a rosca en el alma del 2020 |
| Standoff M4 | 12 | pieles + zócalo, volados. **No todos del mismo largo**: 5 mm los 8 de las pieles, 7 mm el par inferior del zócalo, ~33 mm el par superior (su larguero va retirado para librar el raíl de panel, ver abajo) |
| Tornillo M4 botón | 24 | con los standoffs de arriba |
| Arandela M4 | 24 | ídem |
| Plancha acrílico t=5 mm | 5 | base, entrepiso, zócalo, piel inf., piel sup. |
| Costado portante t=8 mm | 2 | — |

No calculados por el modelo (herrajes eléctricos y de panel; la cantidad
depende de la cuenta final de módulos, no de la geometría del cajón):

| Pieza | Cantidad | Nota |
|-------|----------|------|
| IEC C14 con fusible | 1 | entrada de red, aparato Clase I |
| Espárrago M4 (bonding) | 1 | único — ver «Bonding de tierra» |
| Cable verde/amarillo + terminal de ojal | 1 por panel | al espárrago único, sin excepción |
| Tuerca T M3 | 4 por panel | uno por taladro de `panels/build_template.py` |
| Pies de goma | sin fijar | base rectangular; cantidad a definir en el ensayo de ensamblaje |

Censo actual de paneles: 8 (MIDI/CV, VCO×3, VCF, ADSR, VCA, MIXER —
`clearance_budget.py`, `ANCHOS_PISO_SUP`/`ANCHOS_PISO_INF`). **Estimado, no
cerrado**: estos totales por panel cierran cuando cada panel esté dibujado.

## Anclaje de las placas — solo a largueros del esqueleto

Las cinco planchas de acrílico (2 bandejas, zócalo, 2 pieles) se atornillan
**únicamente a largueros del esqueleto**, nunca a los 4 raíles de panel. Los
raíles de panel van girados al ángulo de su cara (12° / 35°) para quedar a ras
del panel: un tornillo contra esa cara entraría a 12° del eje de su agujero
(≈1.05 mm de descentre en 5 mm de acrílico, contra 0.7–0.9 mm de holgura) y la
arandela asentaría sobre cara inclinada — carga de borde sobre acrílico frágil,
que es justo el modo de fallo que este proyecto ya conoce.

Consecuencia práctica: el zócalo delantero lleva un larguero propio («zócalo
superior», el 11.º del BOM), porque a la altura de su fila de arriba solo había
un raíl de panel y entre el tope de la bandeja base y la esquina del raíl girado
quedan 15.6 mm, menos que los 20 del perfil. Ese larguero se retira en X lo justo
para librar esa esquina (`holgura_rail`), y por eso sus dos standoffs miden
~33 mm en vez de 7. A cambio el canto superior del zócalo cae exacto en
`alto_frontal` = 50 mm, en vez de sobrepasarlo 17.5 mm y tapar la fila de
tornillos inferior de los paneles.

Lo verifica `clearance_budget.py` en `alineacion()`: cada fila de agujeros de
cada placa tiene que caer en la centerline del larguero de esqueleto que
**declara**, con 0.05 mm de tolerancia. Una fila que declare un raíl de panel
sale en ROJO aunque la geometría coincida al micrón. Es una puerta distinta de
`solapes()`, que solo verifica que las piezas no se atraviesen — una placa
flotando en el aire es perfectamente disjunta, y así se coló durante toda la
tanda una bandeja base cuyo canto trasero no llegaba a tocar su larguero.

## Bonding de tierra — no negociable

**Requisito** (se mantiene igual que en el diseño anterior del case):
espárrago M4 único + un cable verde/amarillo por panel, cada uno con su
propio terminal de ojal; ningún otro tornillo comparte ese espárrago.
Fuente: módulo 1 —
[`hardware/01-power-supply/notes/design-notes.md`](../hardware/01-power-supply/notes/design-notes.md)
§13, regla de montaje 6 («cada panel se bonda por su cuenta»).

**Por qué se mantiene**: el case anterior tenía un cuerpo aislante y
paneles metálicos sin unión estructural entre sí, así que §13 exigía
bondar cada panel por su cuenta. El cuerpo del case actual es
**acrílico**, también aislante: la conclusión no cambia, aunque la razón de
fondo sí — ahora los paneles son PCB de aluminio atornillados a largueros
de perfil 2020, no piezas sueltas sobre una estructura sin más.

**Lo que NO se puede asumir sin medir**: los paneles de aluminio se
atornillan a largueros de perfil 2020, que sí son metal — y un larguero
corrido *podría* unir eléctricamente entre sí los paneles de una misma
cara, sin necesidad de cable. Pero el 2020 casi siempre viene anodizado de
fábrica, y el anodizado es aislante. **La conductividad de los largueros no
está confirmada** (Principio I de la constitución). Medición pendiente,
nombrada: continuidad panel↔panel con miliohmetro sobre el extruido 2020
real, anodizado incluido — sobre la pieza física, no sobre el catálogo.

**Prohibido leer esta sección como "los largueros bondan los paneles, el
cable sobra"**. Eso no está confirmado, y aunque se confirmara, el bonding
panel a panel de §13 sigue siendo el requisito: es la posición segura y no
depende de esa medición. El SAM17 lleva entrada IEC C14 — es un aparato
Clase I, así que toda parte metálica que el usuario pueda tocar llega a
tierra de protección por un cable verificable, nunca por suposición. Omitir
un cable asumiendo continuidad por el riel es riesgo de choque eléctrico.

## Orden de ensamblaje

costados → largueros 2020 (M5) → bandejas y zócalo (tuercas T M3) →
electricidad y bonding (bloque IEC fijo, espárrago junto al PSU) → pieles
traseras (standoffs M4, junta de sombra) → paneles (tuercas T M3).

## Estado

- [x] Modelo paramétrico + DXF de corte
- [x] Cupón de calibración
- [x] `clearance_budget.py` en verde
- [x] Plantilla de panel KiCad
- [x] Render del conjunto — dos vistas: frontal
      ([`renders/sam17-case.png`](renders/sam17-case.png)) y trasera
      ([`renders/sam17-case-trasera.png`](renders/sam17-case-trasera.png)).
      La trasera es la que importa: muestra las ranuras de ventilación en
      forma de onda — sierra, triángulo y cuadrada, las tres formas del
      VCO — que son la firma visual del case.
- [ ] Cupón cortado y kerf registrado (bloquea el corte de planchas)
- [ ] Planchas cortadas y ensayo de ensamblaje
