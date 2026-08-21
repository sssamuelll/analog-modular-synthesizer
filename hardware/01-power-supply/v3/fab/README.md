# Ficheros de fabricación — Módulo 1, versión 3 (fuente)

Generados con `kicad-cli` desde `../kicad/sam17-power-v3.kicad_pcb`. Para
regenerarlos, ver el final de este fichero.

## Estado: ruteada y con DRC en cero. **Todavía no pedible.**

```
DRC (kicad-cli, --severity-all)   0 infracciones   0 elementos sin conectar
ERC                               11 lib_symbol_mismatch, preexistentes
ruteo                             1033 segmentos, 176 vías, 2 capas
placa                             200 × 150 mm, FR-4 1,6 mm, 1 oz
barrera de red                    10,63 mm medidos sobre un mínimo de 6
```

Lo que **falta** antes de mandar nada está abajo, en «Las tres puertas que
quedan». Una placa con DRC 0 y sin bring-up no está terminada: está dibujada.

## ⚠ El relleno de zona NO lo hace `build_pcb.py`

**`ZONE_FILLER.Fill()` hace SEGFAULT** desde el Python de KiCad 10.0 con esta
placa ya ruteada — medido el 2026-08-21: exit 139, sin traceback, con 1042
segmentos (con 995 todavía pasaba). No es la zona ni su geometría: se probó
con el polígono ya arreglado y se sigue cayendo, y sin la zona la placa
entera sale en verde.

Por eso el paso de relleno va **fuera del proceso**, con `kicad-cli`, y es
parte del pipeline y no un detalle de estilo:

```
kicad-cli pcb drc --refill-zones --save-board  ...
```

**Si se exportan gerbers sin ese paso, la isla de referencia sale vacía en el
F.Cu.** Una zona sin rellenar en un gerber es cobre que no existe, y el DRC no
lo dice porque para él la zona está bien: simplemente no tiene relleno.

El comando de regenerar de abajo ya lo lleva primero, en ese orden.

## Y la netclass se escapa por dos sitios

`build_pcb.py` escribe el clearance en el **objeto placa**, no solo en el
`.kicad_pro`. La razón está medida: `kicad-cli --save-board` devuelve la
netclass al 0,2 mm de fábrica, porque guarda lo que la placa lleva en memoria
y no lo que hubiera en el fichero de proyecto. La primera versión lo escribía
solo en el `.kicad_pro` y salieron 101 infracciones de margen de golpe.

El valor es **0,127 mm** (5 mil), la capability estándar de JLCPCB en 2 capas
sin recargo. Si se sube, se sube en `CLEARANCE_MM` y se regenera: es la única
fuente.

## Qué se sube a JLC (tres ficheros, no dos)

| fichero | dónde va | se genera con |
|---|---|---|
| `sam17-power-v3-jlcpcb.zip` | «Add gerber file» | bloque de zip al final |
| `sam17-power-v3-bom-jlc.csv` | «Add BOM File» | `python bom_jlc.py` (14 líneas) |
| `sam17-power-v3-cpl-jlc.csv` | «Add CPL File» | `python cpl_jlc.py` (42 designadores) |

**El `sam17-power-v3-pos.csv` NO se sube.** Es la salida cruda de `kicad-cli
pcb export pos`, con las cabeceras de KiCad (`Ref,Val,Package,PosX,PosY,Rot,
Side`); JLC espera las suyas (`Designator,Mid X,Mid Y,Layer,Rotation`) y
devuelve «Failed processing the CPL file» — comprobado en el pedido real de
la v2 el 2026-08-17, con el BOM aceptado en la misma pantalla. `cpl_jlc.py`
traduce cabeceras, capitaliza `Top`/`Bottom`, recorta decimales y filtra a los
designadores del BOM de ensamblaje.

**Lo que NO viene de JLC**: todo el THT (toroide Talema, `BR1`, los 4×4700 µF,
`U1`/`U2` en TO-220, portafusible, conectores, trimmers, el MOV) va por
Reichelt/DigiKey — está en `bom.csv` con proveedor por fila.

## El fusible NO está en esta placa

La spec del case §7 pone un **IEC C14 con portafusible** en la pared del
recinto. Tener además `F1` en la PCB eran **dos fusibles en serie en el mismo
primario** — el mismo fallo los ve a los dos y no hay forma de saber cuál
miró. Se queda el del IEC, que es el accesible sin abrir un recinto de acero
cerrado.

**El requisito no se fue con la pieza.** El fusible del chasis tiene que ser:

| | |
|---|---|
| valor | **1,6 A lento (T)** — por el inrush del toroide de 120 VA más los 0,2 A de la SMPS IRM-15-5 |
| portafusible | **cerrado**, no de clips abiertos: es lo que pide haber elegido aislamiento reforzado |

Si el IEC que se compre no cumple las dos, **no vale**: la placa ya no tiene
red de seguridad detrás.

## Las dos puertas que quedan

1. **La referencia del IEC C14 sigue sin elegir** (#130). Sin ella no hay
   recorte en la chapa, y **el recorte se decide antes de cortar**: después
   de doblada no hay dónde ponerlo. Ya no cambia los gerbers de la PCB — eso
   se cerró al sacar `F1` — pero sí bloquea el chasis.
2. **Stock LCSC el día de mandar** (#57), incluidos `U8`–`U12`. La v2 dejó
   escrito cuál es el más ajustado de su lado; esta versión añade cinco chips
   que no estaban.
3. **Rotaciones de los DFN en la miniatura de JLC**, para `U4`–`U7` (DFN-10 y
   DFN-12) y los MSOP `U8`–`U10`. El cero de rotación de JLC no siempre
   coincide con el de KiCad. Si la miniatura muestra el pin 1 girado, **se
   corrige en el editor de JLC — no se re-exporta el `pos.csv`**.

   Nota de esta versión: `cpl_jlc.py` reporta **«con rotación != 0: ninguno»**,
   o sea que los 42 van a 0°. Eso hace la revisión de miniaturas más fácil, no
   innecesaria.

## Y una que no es de fabricación

**Un `TR1` sin fusible térmico embebido no se compra.** Los 642 W de cualquier
corto del secundario son la cuenta que ni `F1` ni un crowbar cubren, y esto
pasa dentro de un recinto cerrado de acero.

## Regenerar

El orden importa: primero el generador, después el relleno de zona, y solo
entonces los gerbers.

```bash
cd ../kicad
"C:\Program Files\KiCad\10.0\bin\python.exe" build_pcb.py

# el relleno de la zona GNDREF -- ver arriba por que no lo hace build_pcb.py
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --refill-zones --save-board \
  --format json --output ../fab/drc.json --severity-all sam17-power-v3.kicad_pcb

"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export gerbers --output ../fab/ \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,Edge.Cuts --no-x2 sam17-power-v3.kicad_pcb
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export drill --output ../fab/ \
  --format excellon --excellon-units mm sam17-power-v3.kicad_pcb
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export pos --format csv --units mm \
  --side front --output ../fab/sam17-power-v3-pos.csv sam17-power-v3.kicad_pcb
"C:\Program Files\KiCad\10.0\bin\python.exe" bom_jlc.py
"C:\Program Files\KiCad\10.0\bin\python.exe" cpl_jlc.py
```

El zip para JLCPCB (no versionado, se regenera aquí mismo):

```bash
cd ../fab
python -c "import zipfile; z=zipfile.ZipFile('sam17-power-v3-jlcpcb.zip','w',zipfile.ZIP_DEFLATED); [z.write(f) for f in ['sam17-power-v3-F_Cu.gtl','sam17-power-v3-B_Cu.gbl','sam17-power-v3-F_Mask.gts','sam17-power-v3-B_Mask.gbs','sam17-power-v3-F_Silkscreen.gto','sam17-power-v3-Edge_Cuts.gm1','sam17-power-v3.drl','sam17-power-v3-job.gbrjob']]; z.close()"
```
