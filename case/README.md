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
aplicado por defecto: +0.20 mm — lo confirma el cupón (ver abajo).

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

## Procedimiento del cupón — OBLIGATORIO antes de cortar planchas

1. Cortar [`plans/coupon.dxf`](plans/coupon.dxf) en el acrílico REAL con la
   máquina REAL.
2. Probar tornillos M3/M4/M5 en las escaleras; anotar el diámetro que entra
   firme sin forzar. kerf = diámetro_dibujado − diámetro_que_ajusta.
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
| Larguero perfil 2020 | 10 | de 484 mm (`ancho_util`) cada uno |
| Tornillo M5 botón | 20 | 2 por larguero, a rosca en el alma del 2020 |
| Standoff M4 | 12 | pieles + zócalo, volados |
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
