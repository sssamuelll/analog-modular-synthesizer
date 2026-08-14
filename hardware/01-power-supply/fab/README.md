# Ficheros de fabricación — Módulo 1 (fuente)

Generados con `kicad-cli` desde `../kicad/sam17-power.kicad_pcb`. Para
regenerarlos, ver el final de este fichero.

## ⚠ Antes de pedir la placa

**Verifica el orden de patillas de `BR1` contra el datasheet del puente que vayas
a comprar** ([`../notes/design-notes.md` §14.6](../notes/design-notes.md)).

El esquemático usa el símbolo `D_Bridge_+-AA`, que codifica `pin1 = +`,
`pin2 = −`, `pin3 = ~`, `pin4 = ~`. KiCad trae cinco variantes de ese símbolo
precisamente porque el orden cambia según el fabricante, y al buscarlo las
fuentes secundarias se contradicen entre sí. **Aquí no se afirma cuál es el
correcto.** Si el tuyo no es `+ − ~ ~`, hay que cambiar el símbolo en
`build_schematic.py`, regenerar y volver a rutear las cuatro pistas de `BR1`.

Un puente cruzado pone el bulk en cortocircuito a través de dos diodos en el
primer semiciclo.

## Qué hay

| Fichero | Capa |
|---|---|
| `sam17-power-F_Cu.gtl` | Cobre cara de componentes |
| `sam17-power-B_Cu.gbl` | Cobre cara de soldadura |
| `sam17-power-F_Mask.gts` / `-B_Mask.gbs` | Máscara antisoldante |
| `sam17-power-F_Silkscreen.gto` | Serigrafía |
| `sam17-power-Edge_Cuts.gm1` | Contorno **y ranura de la barrera de red** |
| `sam17-power.drl` | Taladros (Excellon, mm) |

## Especificación para el fabricante

- **100 × 150 mm**, 2 capas, FR-4 1.6 mm, cobre 1 oz. Acabado y colores, a gusto.
- **La ranura de `Edge_Cuts` no es un error.** Es una fresa de 2 mm que separa
  la zona de 230 V del resto de la placa
  ([§14.2](../notes/design-notes.md)); va de y = 12 a y = 138, con puentes de
  material arriba y abajo para que la placa no se parta. En el gerber se ve como
  un segundo contorno cerrado en x = 29…31.
- 4 taladros M3 sin metalizar (NPTH) en las esquinas. **Sin cobre a propósito**:
  el puente chasis↔masa es uno solo y va por el faston `J5`
  ([§13](../notes/design-notes.md)), así que un separador metálico no debe tocar
  la masa de la placa.

## Regenerar

```
cd ../kicad
"C:\Program Files\KiCad\10.0\bin\python.exe" build_pcb.py
kicad-cli pcb export gerbers --output ../fab/ \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,Edge.Cuts --no-x2 sam17-power.kicad_pcb
kicad-cli pcb export drill --output ../fab/ --format excellon --excellon-units mm sam17-power.kicad_pcb
```

`build_pcb.py` aborta solo si algo no cuadra: cruces entre pistas, pistas sobre
pads ajenos, bucles en la masa, piezas solapadas o sobre la ranura, o barrera de
red por debajo de 6 mm. Estado actual: todo en cero, y DRC de KiCad sin
infracciones ni pads sin conectar.
