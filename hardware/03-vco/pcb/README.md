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
| `sam17-vco-pos.csv` | Posiciones SMD para ensamblaje (CSV, mm, ambas caras aunque todo cae en `top`) — **solo las 119 huellas SMD**; los conectores (`J1`, `J2`, `J_CV1-4`, `J_OUT1-4`) y los test points son through-hole/pads y se sueldan aparte |
| `sam17-vco-bom.csv` | BOM de ensamblaje **con los códigos LCSC resueltos** (`Designator,Value,Footprint,Quantity,LCSC Part#,Notes`) — 28 líneas cubriendo las 119 huellas SMD. Cada nota lleva el MPN, el stock y la fecha en que se verificó. Es la fuente, no el fichero que se sube |
| `sam17-vco-bom-jlc.csv` | **NO ESTÁ, y es a propósito.** El BOM que se sube a JLCPCB (`Comment,Designator,Footprint,LCSC Part #`) — lo genera `../kicad/bom_jlc.py` fusionando las filas que comparten código LCSC, porque JLC marca como duplicado el mismo part number en dos renglones. Hoy `bom_jlc.py` se niega a escribirlo: `C_IV1-4` y `R_OUT1-4` siguen sin código LCSC verificado. Un fichero viejo con este nombre es peor que ninguno — alguien lo sube |
| `sam17-vco-cpl-jlc.csv` | El CPL (pick&place) **que se sube a JLCPCB** — lo genera `../kicad/cpl_jlc.py`. **El `pos.csv` crudo NO sirve**: falla con «Failed processing the CPL file» porque kicad-cli escribe las cabeceras de KiCad y JLC espera `Designator,Mid X,Mid Y,Layer,Rotation`, con Layer capitalizado y 2 decimales |
| `sam17-vco-3d-top.png` | Render 3D cenital (kicad-cli pcb render, raytracing) — cómo se verá la placa montada, vista desde arriba |
| `sam17-vco-3d-iso.png` | Render 3D isométrico — la placa en perspectiva |
| `sam17-vco-top.svg` | Vista 2D de la cara superior (F.Cu + serigrafía + contorno) |
| `sam17-vco-bottom.svg` | Vista 2D de la cara inferior, espejada (B.Cu + serigrafía + contorno) |
| `sam17-vco.pdf` | Las 4 capas de cobre + serigrafía + contorno, una página por capa |

## El SSI2130 se suelda a mano — DECIDIDO 2026-08-17

**Proveedor único — JLCPCB no lo stockea.** El SSI2130 (Sound Semiconductor)
solo se consigue en Cabintech o Amplified Parts (~$6/u).

**El flujo de ensamblaje de JLC no acepta piezas sin stock, punto.** Probado
contra el pedido real: al llegar a la selección de piezas, la fila del SSI2130
sale como `8 shortfall` y el mensaje es *«Not enough stock available, please
click "search icon" to select another part»*. Quiere una alternativa **en
stock**, y siendo proveedor único no hay ninguna que ofrecer. El `C42420746`
(Sound Semiconductor, mínimo 1 unidad, ~$24.80) sirve para comprarlo suelto,
NO para meterlo en una orden de montaje. La otra entrada del catálogo,
`C2886621`, tiene MOQ 75 y es inservible.

Así que **la fábrica monta 115 de las 119 piezas** y los cuatro sitios de QFN
llegan vacíos.

### Por qué a mano y no consignado

Consignar en JLC **no es meter los chips en un sobre**: es un trámite de
importación previo al pedido — declarar courier, guía, contacto, precio
unitario, fabricante, país de origen, peso y código HS; adjuntar la factura de
compra; esperar dos días hábiles a que verifiquen el precio; y **pagar por
adelantado** arancel + IVA del 13 % + comisión del 2 % con mínimo de US$ 10,
antes de enviar nada a su almacén de Hong Kong. Sobre $36 de chips eso son
$35-55 de sobrecosto y 2-4 semanas. Y sus términos dicen que **no prueban los
componentes consignados ni responden** por fallos de montaje causados por
ellos.

### Y por qué a mano SÍ se puede, con cautín normal

Dos cosas de la propia huella lo hacen viable sin horno ni placa caliente:

1. **El EP no se suelda.** El pad central de 2.65×2.65 mm existe en la huella
   pero va **aislado, sin red** — el datasheet prohíbe conectarlo (pág. 6). Lo
   que normalmente hace imposible un QFN a mano es refluir esa plataforma
   central, y aquí no hay que tocarla: el chip se apoya y ya.
2. **Los pads sobresalen 0.35 mm del cuerpo.** Miden 0.8 mm de largo con el
   centro a 1.95 mm del origen, y el encapsulado llega a 2.00 mm: queda un
   escalón visible donde apoyar la punta. No se suelda a ciegas por debajo.

Sigue siendo paso de 0.40 mm: hace falta flux, estaño fino, malla de desoldar
y aumento. La técnica es arrastre (*drag soldering*), y los puentes que salgan
se chupan con malla — es parte del método, no un fallo.

**Consecuencia para los gerbers:** por este camino **no hace falta F.Paste**
(eso era para cortar un stencil). El punto 2 del issue #66 queda sin urgencia.

**Comprar 6, no 4** (4 + 2 de repuesto) — es proveedor único
y el margen de span del oscilador es trimless (spec, [§11](../../../docs/superpowers/specs/2026-08-16-modulo-3-vco-design.md#11-riesgos-y-lo-no-confirmado)),
así que un chip fuera de rango en bring-up se descarta, no se repara. Con
soldadura a mano el repuesto cubre además el chip que se arruine soldando.

Todo lo demás **SMD** (los otros 107 refs) lo monta la fábrica por su flujo
normal, con `sam17-vco-bom-jlc.csv` y `sam17-vco-cpl-jlc.csv` como entrada
(NO el `pos.csv` crudo — ver la tabla de arriba).

### Lo que se compra para soldar los cuatro

Herramienta, una sola vez y sirve para los módulos 5, 6 y 7:

| | Para qué |
|---|---|
| Cautín con control de temperatura, punta fina | El trabajo |
| **Flux en gel (jeringa), sin limpieza** | Lo que hace posible el arrastre — sin esto no funciona |
| Estaño 0.5 mm o menos, con plomo (63/37) | El sin plomo es bastante más difícil a mano |
| Malla de desoldar de 1.5-2 mm | Chupar los puentes. Se usa siempre, no es plan B |
| Aumento (microscopio USB o lupa de cabeza) | A 0.40 mm de paso no se ve a ojo pelado |
| Alcohol isopropílico + cepillo | Limpiar el flux al terminar |

Orden de trabajo: flux generoso sobre toda la fila, fijar **una** pata de
esquina para alinear el chip, verificar la alineación con aumento antes de
seguir, y recién ahí arrastrar el resto de las filas. El pad central no se
toca.

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
