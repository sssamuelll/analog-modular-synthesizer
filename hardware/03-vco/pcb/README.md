# Ficheros de fabricación — Módulo 3 (VCO ×4)

Generados con `kicad-cli` desde `../kicad/sam17-vco.kicad_pcb` (commit del board
con DRC en 0, ver [Tarea 6](../../../.superpowers/sdd/2026-08-16-modulo-3-vco/task-6-report.md)).
Para regenerarlos, ver el final de este fichero.

## Qué hay

| Fichero | Contenido |
|---|---|
| `sam17-vco-F_Cu.gtl` | Cobre cara de componentes |
| `sam17-vco-In1_Cu.g1` | Cobre interna 1 — **plano GNDA** |
| `sam17-vco-In2_Cu.g2` | Cobre interna 2 |
| `sam17-vco-B_Cu.gbl` | Cobre cara de soldadura |
| `sam17-vco-F_Mask.gts` / `-B_Mask.gbs` | Máscara antisoldante |
| `sam17-vco-F_Silkscreen.gto` / `-B_Silkscreen.gbo` | Serigrafía |
| `sam17-vco-Edge_Cuts.gm1` | Contorno de la placa (114×124 mm) |
| `sam17-vco-job.gbrjob` | Job file (metadatos del set de gerbers) |
| `sam17-vco.drl` | Taladros, Excellon, mm — vías (0.20 mm) y through-hole (conectores) en un solo fichero |
| `sam17-vco-pos.csv` | Posiciones SMD para ensamblaje (CSV, mm, ambas caras aunque todo cae en `top`) — **solo las 111 huellas SMD**; los conectores (`J1`, `J2`, `J_CV1-4`, `J_OUT1-4`) y los test points son through-hole/pads y se sueldan aparte |
| `sam17-vco-bom.csv` | BOM de ensamblaje, columnas al estilo JLC (`Designator,Value,Footprint,Quantity,LCSC Part#,Notes`) — generado cruzando `../bom.csv` contra `sam17-vco-pos.csv`, 25 líneas cubriendo las 111 huellas SMD |

## El SSI2130 va consignado

**Proveedor único — JLCPCB no lo stockea.** El SSI2130 (Sound Semiconductor)
solo se consigue en Cabintech o Amplified Parts (~$6/u). Dos caminos, cualquiera
de los dos funciona con el resto del ensamblaje SMD normal de la fábrica:

1. **Consignado**: comprarlo y enviarlo a JLCPCB junto con el pedido, para que
   lo suelden ellos con el resto del SMD (U1-U4, QFN-32 4×4 mm con EP térmico —
   difícil a mano sin horno de reflow).
2. **En casa**: soldar solo los 4 SSI2130 con stencil + placa caliente después
   de que la fábrica monte todo lo demás.

**Comprar 6, no 4** (4 + 2 de repuesto) en la misma orden — es proveedor único
y el margen de span del oscilador es trimless (spec, [§11](../../../docs/superpowers/specs/2026-08-16-modulo-3-vco-design.md#11-riesgos-y-lo-no-confirmado)),
así que un chip fuera de rango en bring-up se descarta, no se repara.

Todo lo demás del BOM (los otros 107 refs SMD + los conectores through-hole)
lo monta/suministra la fábrica por su flujo normal.

**Números de parte LCSC**: la columna queda vacía a propósito en
`sam17-vco-bom.csv` — no hay ninguno confirmado todavía. Se rellenan al pedir
cotización con JLCPCB (su buscador de BOM hace el match por valor/footprint).

## Reglas del fab: ya en capacidad estándar, nada que negociar

El DRC de la Tarea 6 ya afinó las reglas a la capacidad real de JLCPCB para 4
capas — **vía 0.45 mm / taladro 0.20 mm** es el punto exacto sin recargo (por
debajo de 0.45 con taladro 0.20 JLCPCB cobra extra). No hace falta relajar ni
apretar nada al cotizar: pedir el proceso estándar de 4 capas.

## Regenerar

```
cd ../kicad
kicad-cli pcb export gerbers --output ../pcb/ \
  --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts \
  --no-x2 sam17-vco.kicad_pcb

kicad-cli pcb export drill --output ../pcb/ \
  --format excellon --excellon-units mm sam17-vco.kicad_pcb

kicad-cli pcb export pos --output ../pcb/sam17-vco-pos.csv \
  --format csv --units mm --side both --smd-only sam17-vco.kicad_pcb
```

El BOM de ensamblaje (`sam17-vco-bom.csv`) no sale de kicad-cli: se genera
cruzando `../bom.csv` (que agrupa referencias por rango, p. ej. `R_MIX*`)
contra los designadores reales de `sam17-vco-pos.csv`, para quedarse solo con
lo que la fábrica va a colocar.
