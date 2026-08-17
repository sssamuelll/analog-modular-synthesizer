# Ficheros de fabricación — Módulo 3 (VCO ×4)

Generados con `kicad-cli` desde `../kicad/sam17-vco.kicad_pcb` (commit del board
con DRC en 0; la misma historia está contada en el docstring de
`../kicad/build_pcb.py`).
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
| `sam17-vco-drl_map.pdf` | Mapa de taladros (tamaño/símbolo por herramienta), para revisar visualmente antes de pedir |
| `sam17-vco-pos.csv` | Posiciones SMD para ensamblaje (CSV, mm, ambas caras aunque todo cae en `top`) — **solo las 111 huellas SMD**; los conectores (`J1`, `J2`, `J_CV1-4`, `J_OUT1-4`) y los test points son through-hole/pads y se sueldan aparte |
| `sam17-vco-bom.csv` | BOM de ensamblaje **con los códigos LCSC resueltos** (`Designator,Value,Footprint,Quantity,LCSC Part#,Notes`) — 26 líneas cubriendo las 111 huellas SMD. Cada nota lleva el MPN, el stock y la fecha en que se verificó. Es la fuente, no el fichero que se sube |
| `sam17-vco-bom-jlc.csv` | El BOM **que se sube a JLCPCB** (`Comment,Designator,Footprint,LCSC Part #`) — lo genera `../kicad/bom_jlc.py` fusionando las filas que comparten código LCSC, porque JLC marca como duplicado el mismo part number en dos renglones |
| `sam17-vco-cpl-jlc.csv` | El CPL (pick&place) **que se sube a JLCPCB** — lo genera `../kicad/cpl_jlc.py`. **El `pos.csv` crudo NO sirve**: falla con «Failed processing the CPL file» porque kicad-cli escribe las cabeceras de KiCad y JLC espera `Designator,Mid X,Mid Y,Layer,Rotation`, con Layer capitalizado y 2 decimales |
| `sam17-vco-3d-top.png` | Render 3D cenital (kicad-cli pcb render, raytracing) — cómo se verá la placa montada, vista desde arriba |
| `sam17-vco-3d-iso.png` | Render 3D isométrico — la placa en perspectiva |
| `sam17-vco-top.svg` | Vista 2D de la cara superior (F.Cu + serigrafía + contorno) |
| `sam17-vco-bottom.svg` | Vista 2D de la cara inferior, espejada (B.Cu + serigrafía + contorno) |
| `sam17-vco.pdf` | Las 4 capas de cobre + serigrafía + contorno, una página por capa |

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

Todo lo demás **SMD** (los otros 107 refs) lo monta la fábrica por su flujo
normal, con `sam17-vco-pos.csv`/`sam17-vco-bom.csv` como entrada.

**Los conectores through-hole llegan sin montar — no los monta la fábrica.**
`sam17-vco-pos.csv` se generó con `--smd-only` y **no trae sus posiciones**, así
que la fábrica no tiene cómo colocarlos aunque quisiera. Pero **no todos esperan
al panel, y confundirlos bloquea el bring-up**:

- **`J1` (KK-254) y `J2` (IDC 2×6) se sueldan ANTES del bring-up.** No son de
  panel: son conectores de **cable**, en el borde inferior de la placa (`J1` en
  (94, 114), `J2` en (16, 115)). Sin `J1` no hay alimentación y sin `J2` no
  entra `GNDD` — con el mazo fuera, el 74HC14, el sensor y la EEPROM tienen
  alimentación pero ningún retorno. Ver el §0 de
  [`../notes/bring-up.md`](../notes/bring-up.md).
- **Los 8 jacks Thonkiconn (`J_CV1-4`, `J_OUT1-4`) sí son de panel**: se alinean
  mecánicamente contra el chasis antes de soldar, así que un ensamblaje
  automático los desalinearía. Los cuatro de CV-IN hay que soldarlos o puentear
  su punta al manguito antes del paso del span (su normal ata `CVIN_n` a masa;
  sin eso el nodo del expo capta zumbido y la afinación baila).

Todos ellos van en la misma tanda de soldadura a mano que los SSI2130 si se
elige la opción "en casa" de arriba, o en una pasada aparte si el SSI2130 fue
consignado.

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
  --format excellon --excellon-units mm \
  --generate-map --map-format pdf sam17-vco.kicad_pcb

kicad-cli pcb export pos --output ../pcb/sam17-vco-pos.csv \
  --format csv --units mm --side both --smd-only sam17-vco.kicad_pcb

python bom_jlc.py     # sam17-vco-bom.csv  -> sam17-vco-bom-jlc.csv
python cpl_jlc.py     # sam17-vco-pos.csv  -> sam17-vco-cpl-jlc.csv
```

`bom_jlc.py` falla en vez de escribir si alguna línea del BOM se quedó sin
código LCSC válido, y `cpl_jlc.py` cruza BOM y posiciones **en los dos
sentidos**: una pieza del BOM sin posición no se puede colocar, y una huella
SMD con posición pero sin línea de BOM es un pad que la máquina deja vacío
sin avisar. Los dos fallos los descubre la fábrica tarde y caro.

`--no-x2` en los gerbers: genera RS-274X plano en vez del formato extendido
X2 (que mete atributos de red/aperture como comentarios estructurados en
cada gerber, incluyendo nombres de red). Compatibilidad más conservadora con
el CAM de JLCPCB y no filtra nombres de red en los ficheros que se suben. La
extensión de fichero por capa (`.gtl`/`.gbl`/`.gts`/...) es aparte: es el
default de `kicad-cli` (nombres estilo Protel) sin tocar ningún flag, y es lo
que JLCPCB usa para identificar cada capa al subir el zip.

El BOM de ensamblaje (`sam17-vco-bom.csv`) no sale de kicad-cli: se genera
cruzando `../bom.csv` (que agrupa referencias por rango, p. ej. `R_MIX*`)
contra los designadores reales de `sam17-vco-pos.csv`, para quedarse solo con
lo que la fábrica va a colocar.
