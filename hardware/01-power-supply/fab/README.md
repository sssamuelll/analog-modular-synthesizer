# Ficheros de fabricación — Módulo 1 (fuente)

Generados con `kicad-cli` desde `../kicad/sam17-power.kicad_pcb`. Para
regenerarlos, ver el final de este fichero.

## Estado: listo para pedir

La puerta del orden de patillas de `BR1` (issue #11) está **cerrada**: la pieza
queda fijada en **DB207** (2 A / 1000 V, case DB-1 — el único puente de 2 A en
DIP-4; el KBP206 del BOM original era SIP y no encajaba en la huella). Su
datasheet primario (HY Electronic, DB201–DB207 Rev. 11) confirma que el pinout
cae exactamente como está ruteado con el símbolo `D_Bridge_+-AA`
([§14.6](../notes/design-notes.md)). Los gerbers no cambiaron: el pinout ya era
el correcto.

## ⚠ Al montar

**Dos cosas, y las dos destruyen piezas si se pasan por alto.**

**1. La orientación de `BR1`**: la esquina `+` moldeada en el cuerpo va a la
cruz `+` del silk (pad 1). Girado 180° encaja físicamente igual y pone el bulk
en cortocircuito a través de dos diodos en el primer semiciclo. Si compras la
serie DB20x de otro fabricante que no sea HY, re-verifica su datasheet antes de
soldar ([§14.6](../notes/design-notes.md)).

**2. El tab de `U2` (LM2990T-12) NO está a masa: está a VRAW−**, hasta −20 V. Va
con **mica y casquillo aislante**, obligatorios. Atornillarlo desnudo al mismo
disipador que `U1` es un cortocircuito franco al encender
([§16.7](../notes/design-notes.md)).

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

## Regenerar

```
cd ../kicad
"C:\Program Files\KiCad\10.0\bin\python.exe" build_pcb.py
kicad-cli pcb export gerbers --output ../fab/ \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,Edge.Cuts --no-x2 sam17-power.kicad_pcb
kicad-cli pcb export drill --output ../fab/ --format excellon --excellon-units mm sam17-power.kicad_pcb
```

El zip para JLCPCB (no versionado, se regenera aquí mismo):

```
cd ../fab
python -c "import zipfile; z=zipfile.ZipFile('sam17-power-jlcpcb.zip','w',zipfile.ZIP_DEFLATED); [z.write(f) for f in ['sam17-power-F_Cu.gtl','sam17-power-B_Cu.gbl','sam17-power-F_Mask.gts','sam17-power-B_Mask.gbs','sam17-power-F_Silkscreen.gto','sam17-power-Edge_Cuts.gm1','sam17-power.drl','sam17-power-job.gbrjob']]; z.close()"
```

`build_pcb.py` aborta solo si algo no cuadra: cruces entre pistas, pistas sobre
pads ajenos, bucles en la masa, piezas solapadas o sobre la ranura, o barrera de
red por debajo de 6 mm. Estado actual: todo en cero, y DRC de KiCad sin
infracciones ni pads sin conectar.
