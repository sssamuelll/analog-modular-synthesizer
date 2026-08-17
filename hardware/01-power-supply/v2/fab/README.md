# Ficheros de fabricación — Módulo 1, versión 2 (fuente)

Generados con `kicad-cli` desde `../kicad/sam17-power-v2.kicad_pcb`. Para
regenerarlos, ver el final de este fichero.

## Estado: NO listo para pedir

El diseño está completo (silicio verificado GO en §2.3 del design-notes.md, ruteado con
DRC=0), pero hay **tres puertas abiertas** antes de solicitar la fabricación:

1. **Medidas en la mula prototipo**: confirmar los setpoints RV2/RV3 con el valle 
   real de la fuente de red y los límites de temperatura. Task 10 abre una issue 
   por esto.
2. **Stock LCSC el día de mandar**: re-verificar disponibilidad de piezas Extended 
   (LT3045EDD, LT3094EDD) y del fallback 120 kΩ ±100 ppm (C114524). Los códigos 
   están anotados en `bom.csv` con fecha de consulta 2026-08-16 — no son garantía 
   de stock en el momento de compra.
3. **Rotaciones de los DFN**: revisar las miniaturas de ensamblaje de JLCPCB para 
   los chips U4–U7 (DFN-10 y DFN-12). Gotcha conocido: el cero de rotación de JLC 
   no siempre coincide con el de KiCad, y los DFN apaisados lo hacen evidente al 
   montaje.

## ⚠ Al montar

**Dos cosas crean daño si se pasan por alto.**

**1. La orientación de `BR1`** (puente rectificador, THT): la esquina `+` moldeada 
en el cuerpo va a la cruz `+` del silk (pad 1). Girado 180° encaja físicamente igual 
y pone el bulk en cortocircuito a través de dos diodos en el primer semiciclo. Si 
compras la serie DB20x de otro fabricante que no sea HY, re-verifica su datasheet 
antes de soldar ([§14.6](../notes/design-notes.md)).

**2. El tab de `U2` (LM2991T, pre-reg negativo, THT)** NO está a masa: está a VRAW−, 
hasta −20 V. Va con **mica y casquillo aislante**, obligatorios. Atornillarlo desnudo 
al mismo disipador que `U1` es un cortocircuito franco al encender 
([§16.7](../notes/design-notes.md)).

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

## Nota sobre DRC y anillos

El archivo `.kicad_pcb` pasó un DRC completo (KiCad 10.0) con **10 violaciones 
aceptadas por ruling**: anillo `annular_width` de 0.0875 mm en los taladros THT 
de `U1` y `U2` (agujero de 1.1 mm, anillo mínimo de 0.075 mm). Esto es documentado 
en Task 8 y es una configuración conocida de la placa — no es corrupción. Si 
regeneras el DRC con este `.kicad_pcb`, ese número de violaciones reaparecerá; es 
normal.

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
