# Ficheros de fabricación — Módulo 1, versión 2 (fuente)

Generados con `kicad-cli` desde `../kicad/sam17-power-v2.kicad_pcb`. Para
regenerarlos, ver el final de este fichero.

## Estado: listo para pedir, con dos comprobaciones dentro del propio pedido

El diseño está completo (silicio verificado GO en §2.3 del design-notes.md, ruteado con
DRC=0). Las dos puertas que quedan **se resuelven en el flujo del pedido**, no antes:

1. **Stock LCSC el día de mandar**: re-verificar disponibilidad de piezas Extended 
   (LT3045EDD, LT3094EDD) y del fallback 120 kΩ ±100 ppm (C114524). Los códigos 
   están anotados en `bom.csv` con fecha de consulta 2026-08-16 — no son garantía 
   de stock en el momento de compra.
2. **Rotaciones de los DFN**: revisar las miniaturas de ensamblaje de JLCPCB para 
   los chips U4–U7 (DFN-10 y DFN-12). Gotcha conocido: el cero de rotación de JLC 
   no siempre coincide con el de KiCad, y los DFN apaisados lo hacen evidente al 
   montaje.

**La tercera puerta se cerró por decisión, no por medida** (2026-08-17): la v1 no
se construye, así que no hay mula que confirme los setpoints antes de fabricar.
Se ajustan sobre la propia v2 con RV2/RV3 durante el bring-up. Lo que esa decisión
mete en la mesa de pruebas, y que **hay que leer antes de encender la placa**: el
valle de VRAW medido con carga tiene que quedar en **13.46 V o más**
([`design-notes.md` §4.1](../notes/design-notes.md)); por debajo de eso ningún
giro de trimmer recupera los 12.000 V. Colchón contra el valle simulado: 0.66 V.

## ⚠ Al pedir

**Vías de las granjas de EP de U4-U7 abiertas en la ventana de pasta.** Las
granjas térmicas del EP (U4=4, U5=6, U6=4+1, U7=4 vías, 0.3 mm de taladro —
detalle en `design-notes.md` §3.2) quedan dentro del área de pasta del EP,
que abre solo el 7-12 % del EP (spec de stencil). Eso es riesgo de junta
pobre por succión de pasta hacia el taladro durante el reflow (la vía actúa
de mecha y drena estaño de la ventana). Dos opciones al pedir:

1. **Pedir "Epoxy Filled & Capped"** para esas vías (tapadas y planas) si el
   presupuesto lo permite — elimina el riesgo de succión sin tocar el
   diseño.
2. **Aceptar el wicking** (opción por defecto, sin coste extra) e
   **inspeccionar las juntas del EP en el bring-up** — ítem añadido a la
   lista "Al montar" de abajo.

## ⚠ Al montar

**Tres cosas crean daño (o una junta fría no detectada) si se pasan por
alto.**

**1. La orientación de `BR1`** (puente rectificador, THT): la esquina `+` moldeada 
en el cuerpo va a la cruz `+` del silk (pad 1). Girado 180° encaja físicamente igual 
y pone el bulk en cortocircuito a través de dos diodos en el primer semiciclo. Si 
compras la serie DB20x de otro fabricante que no sea HY, re-verifica su datasheet 
antes de soldar ([§14.6](../notes/design-notes.md)).

**2. El tab de `U2` (LM2991T, pre-reg negativo, THT)** NO está a masa: está a VRAW−, 
hasta −20 V. Va con **mica y casquillo aislante**, obligatorios. Atornillarlo desnudo 
al mismo disipador que `U1` es un cortocircuito franco al encender 
([§16.7](../notes/design-notes.md)).

**3. Inspeccionar las juntas del EP de U4-U7** tras el reflow (lupa o rayos
X si hay acceso) — consecuencia directa del wicking de la sección "Al
pedir" de arriba si no se pidió "Epoxy Filled & Capped". Una junta pobre en
el EP no es visible a simple vista en los pines periféricos y sube la
resistencia térmica del chip justo donde más importa (el camino del EP a
la plancha de cobre, ver `design-notes.md` §3.2).

## Qué hay

| Fichero | Capa |
|---|---|
| `sam17-power-v2-F_Cu.gtl` | Cobre cara de componentes |
| `sam17-power-v2-B_Cu.gbl` | Cobre cara de soldadura |
| `sam17-power-v2-F_Mask.gts` / `-B_Mask.gbs` | Máscara antisoldante |
| `sam17-power-v2-F_Silkscreen.gto` | Serigrafía |
| `sam17-power-v2-Edge_Cuts.gm1` | Contorno **y ranura de la barrera de red** |
| `sam17-power-v2.drl` | Taladros (Excellon, mm) |
| `sam17-power-v2-bom-jlc.csv` | BOM de ensamblaje para JLCPCB (16 líneas SMD) |
| `sam17-power-v2-pos.csv` | Posiciones de componentes (72 lineas, incluye THT) |

**Nota sobre el POS**: el fichero `sam17-power-v2-pos.csv` incluye todas las huellas 
de F.Cu exportadas por KiCad (SMD y THT). JLCPCB ignora las líneas de designadores 
que no aparezcan en el BOM JLC, así que los 44 componentes THT que vienen en el POS 
pero no en el BOM son ignorados automáticamente por el programa de ensamblaje. 
Es coherencia esperada: no es un error.

## Especificación para el fabricante

- **150 × 200 mm**, 2 capas, FR-4 1.6 mm, cobre 1 oz. Acabado y colores, a gusto.
- **La ranura de `Edge_Cuts` no es un error.** Es una fresa de 2 mm que separa
  la zona de 230 V del resto de la placa
  ([§14.2](../notes/design-notes.md)); es **horizontal**, va de x = 10 a x = 140
  a la altura y = 30…32, con puentes de material a izquierda y derecha para que
  la placa no se parta. En el gerber se ve como un segundo contorno cerrado.
- **Reservar 42 × 38 mm y 25 mm de alto** por regulador para su disipador
  (Fischer SK 129/38,1). Van marcados en la capa F.Fab.
- 4 taladros M3 sin metalizar (NPTH) en las esquinas. **Sin cobre a propósito**:
  el puente chasis↔masa es uno solo y va por el faston `J5`
  ([§13](../notes/design-notes.md)), así que un separador metálico no debe tocar
  la masa de la placa.

## Nota sobre DRC

El archivo `.kicad_pcb` pasa un DRC completo (KiCad 10.0) en **cero
violaciones de cualquier tipo y cero elementos sin conectar**
(`kicad-cli pcb drc --format json`). Hasta la review de fase C esto traía
**10 violaciones `annular_width` aceptadas por ruling** (anillo de 0.0875 mm
en los taladros THT de `U1`/`U2`, agujero 1.1 mm) — ya NO existen: los pads
de `U1`/`U2` se ensancharon en el eje corto a 1.4×1.8 mm (anillo real
0.15 mm, por encima de la capability JLC de 2 capas de 0.13 mm), en vez de
seguir documentándolas como excepción. Si regeneras el DRC con este
`.kicad_pcb` debe salir **0 infracciones, 0 elementos no conectados**; si
aparece algo, es una regresión real, no una configuración conocida de la
placa.

## Regenerar

```bash
cd ../kicad
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export gerbers --output ../fab/ \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,Edge.Cuts --no-x2 sam17-power-v2.kicad_pcb
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export drill --output ../fab/ \
  --format excellon --excellon-units mm sam17-power-v2.kicad_pcb
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export pos --format csv --units mm \
  --side front --output ../fab/sam17-power-v2-pos.csv sam17-power-v2.kicad_pcb
python bom_jlc.py
```

El zip para JLCPCB (no versionado, se regenera aquí mismo):

```bash
cd ../fab
python -c "import zipfile; z=zipfile.ZipFile('sam17-power-v2-jlcpcb.zip','w',zipfile.ZIP_DEFLATED); [z.write(f) for f in ['sam17-power-v2-F_Cu.gtl','sam17-power-v2-B_Cu.gbl','sam17-power-v2-F_Mask.gts','sam17-power-v2-B_Mask.gbs','sam17-power-v2-F_Silkscreen.gto','sam17-power-v2-Edge_Cuts.gm1','sam17-power-v2.drl','sam17-power-v2-job.gbrjob']]; z.close()"
```
