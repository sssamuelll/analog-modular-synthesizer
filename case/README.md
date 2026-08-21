# Case SAM17 — consola de dos pisos en acrílico naranja

Spec: [`docs/superpowers/specs/2026-08-15-case-design.md`](../docs/superpowers/specs/2026-08-15-case-design.md) (rev. 5)
Board de intención: [`renders/propuesta-diseno-2026-08-16.png`](renders/propuesta-diseno-2026-08-16.png)
— **manda sobre lenguaje visual, NO sobre cotas**: se dibujó para paneles de
190 mm y un case de 500 × 380 × 350, y el case real mide 544.32 × 256.18 × 308.94.

## Formato: EUROrack 3U, las dos filas

**Este apartado decía lo contrario hasta el 2026-08-17.** Decía que el SAM17
usaba formato propio de 190 mm y que no era intercambiable con Eurorack. Se
revirtió: las dos filas son **3U de EUROrack** — `alto_panel_inf` =
`alto_panel_sup` = **128.5 mm** ([`cad/params.scad`](cad/params.scad)), paso
de 1 HP = 5.08 mm, y `sep_railes` = **122.5 mm** entre centros, que es la
cota del panel (ranuras a 3.0 mm de cada canto), no del riel.

Los raíles son **Z-Rails de Tiptop de 104 HP** (528.3 mm), comprados el
2026-08-18. Llevan pletina roscada M3 continua, así que la separación la
pone el costado al taladrarse, no el riel.

Consecuencia: cualquier jack, perilla, panel ciego y módulo Eurorack
comercial encaja. Lo que se perdió es la proporción del board de intención,
que se dibujó para 190 mm.

**Dimensiones** (salida real de `clearance_budget.py`):

| | |
|---|---|
| ancho total | **544.32 mm** = 528.32 (104 HP) + 2 × `t_cheek` |
| alto total | **256.18 mm** |
| fondo | **308.94 mm** |
| altura de entrepiso | **146.58 mm** |
| ancho útil entre costados | **528.32 mm** |

**El suelo cierra, y cuesta 8.46 mm de alto** (2026-08-21). La bandeja de base
llegaba solo hasta el larguero de base delantera, que a su vez se retira por
detrás del raíl de panel para que ese raíl pueda bajar hasta la esquina. El
resultado eran **37.96 mm de suelo abierto** por delante — que no era un
descuido: era la entrada de aire.

Cerrarlo no era estirar la plancha. El Z-Rail de abajo va girado 35° y su
esquina baja caía en **y = 4.84**, o sea 3.16 mm *por debajo* del techo de la
bandeja (y = 8): ninguna plancha plana le pasa por debajo. Hubo que subir el
raíl, y `alto_frontal` no viaja solo — la punta redondeada se come
`alto_frontal/2` de cara, así que arrastra `inset_inf_frente`, que va dentro de
`alto_cara_inf`, que es quien fija el fondo:

| | antes | ahora |
|---|---|---|
| `alto_frontal` | 13 | **19** |
| `inset_inf_frente` | 14.5 | **17.5** |
| `alto_cara_inf` (derivado) | 152.75 | **155.75** |
| esquina del raíl | y = 4.84 | **y = 13.29** (5.29 de aire) |
| alto del case | 247.73 | **256.18** |
| fondo | 307.22 | **308.94** |

Es exactamente el precio que el propio `params.scad` había anotado cuando se
hizo el trato al revés: «subir el riel cuesta 8 mm de aparato». Se paga entero.

Por debajo ya no queda hueco: la plancha llega hasta donde **muere la curva** de
la esquina inferior delantera (x = 9.49), que es la misma regla que usa
`x_valle()` para el pico. Lo único abierto es el propio redondeo, y eso se lee
como esquina, no como ranura.

**Y la entrada de aire vuelve al suelo, pero dibujada.** Es la mitad del cambio
que no se ve en ningún render. Se probó unas horas abajo en la trasera; Samuel
pidió dejar esa pieza solo con sus tres ondas, así que la entrada acabó donde
siempre estuvo — 51 ranuras iguales a las del valle, en el **vuelo** de la
bandeja, por delante del larguero y fuera del camino de carga.

Donde está es mejor de lo que parece. Tiene menos de la mitad de área que la
versión trasera, pero entra a **y = 4** en vez de a 53, y el tiro de chimenea
gana los 50 mm que pierde de área. No se ve desde ningún ángulo normal: el
plenum lo dan las paticas de 8 mm, que abren ~13 600 mm² de perímetro contra los
3 535 de la rejilla.

| | área abierta | altura | ranuras |
|---|---|---|---|
| entrada (suelo, en el vuelo) | **11 421 mm²** | y = 4 | 51 de 56.8 × 4 |
| salida — valle | 7 499 mm² | y = 144 | 102 de 19.2 × 4 |
| salida — las tres ondas | 5 110 mm² | y ≈ 137 | — |

La rejilla nació con 3 535 mm² en ranuras de 18.2 y **creció sola** a 11 421
cuando el larguero delantero se corrió hacia atrás (abajo): está derivada del
vuelo, no de un número escrito a mano.

**`guarda_aire()` dejó de medir área y pasa a medir salto térmico.** Nació
exigiendo «entrada ≥ salida», que valía mientras la entrada estaba en la
trasera. Al mudarse al suelo esa desigualdad se rompe *a propósito*, y mantener
el assert habría sido tener una puerta roja sobre un diseño correcto — el vicio
que ya costó una tanda entera en este repo. Lo que hay que exigir no es paridad
de áreas: es que el aparato no se caliente.

```
Q = C_D · A_ef · √(2 g h ΔT / T)        caudal
P = ρ · c_p · Q · ΔT                    calor que se lleva
⇒  P = k · ΔT^1.5,  k = ρ·c_p·C_D·A_ef·√(2 g h / T)
```

`A_ef` son entrada y salida **en serie**; `h`, la distancia entre sus
centroides. Con 6.33 W de reguladores (spec PSU v2 §4) salen **4.6 K** sobre
ambiente contra un techo de 15. **SUPUESTO, no medido**: `C_D` = 0.65, y las
pérdidas del transformador no están itemizadas — por eso el techo va holgado.

## El espacio de los módulos lo comía el chasis, no la barra

Samuel quiso retirar el larguero de base delantera: se leía pegado al raíl de
panel (4.00 mm, la holgura clavada) y parecía comerle fondo a los módulos de la
fila de abajo. Medido a lo largo del panel —y no por caja, que es donde se
esconde el error—, el limitante era otro.

El **chasis de acero del PSU** mide 176.6 × 93 mm y se sentaba *centrado* entre
los dos largueros de base. Los módulos de la fila inferior cuelgan del panel
hacia dentro y hacia abajo, y se metían en su esquina delantera-alta: el fondo
libre caía a **18.6 mm** a media altura del panel. Nadie había decidido que el
chasis fuera centrado — `ch_pos()` simplemente lo centraba.

| | mínimo | quién lo pone | panel útil a 50 mm | a 60 mm |
|---|---|---|---|---|
| antes | 18.6 mm | chasis | 27 % | 11 % |
| solo quitar el larguero | 18.6 mm | chasis | 42 % | 20 % |
| solo mover el chasis | 25.8 mm | el larguero | 53 % | 37 % |
| **los dos atrás** | **34.4 mm** | chasis | **68 %** | 42 % |

Así que ahora **el chasis se pega al larguero trasero y el delantero se pega al
chasis**, los dos a `chasis_holgura_larguero`. Una sola cadena y en un solo
sentido: `x_tr → chasis → base delantera`. El larguero acaba en x = 88.34, o sea
a **42.7 mm del raíl de panel** en vez de a 4.00 — que era la otra mitad de lo
que molestaba.

**No se retira.** Sostiene la fila delantera de tornillos de la bandeja; sin él
la plancha queda en voladizo de 280 mm bajo el chasis, y los 4 puntos de panel
que se ganarían a 60 mm de fondo no pagan eso.

Efecto colateral que sale gratis: el vuelo de la bandeja pasa de 30.19 a
**68.85 mm**, la rejilla de entrada crece con él y el salto térmico baja de 8.5 a
**4.6 K**.

Lo que dejó de salir solo: la holgura contra el raíl de panel. Estaba garantizada
por construcción mientras el larguero se *derivaba* del raíl; ahora es una
consecuencia, así que `guarda_piso()` la exige explícitamente.

**La punta de arriba es cuadrada** (2026-08-21). El techo lleva una meseta de
`marco_remate` = **50 mm** rematada por dos quiebres de 2 mm, en vez de la
cúpula que salía antes. Fue 34 unas horas: subió a 42 cuando la meseta tuvo
que alojar el larguero del remate trasero (abajo). Son **dos** parámetros y no uno: los vértices 4 y 5
dejaron de compartir `radio_punta` —que va sobredimensionado a propósito y se
recorta a lo que quepa en la arista, o sea a `marco_remate/2`— y estrenan
`radio_remate` = 2. Subir solo el marco **engorda** el round en vez de
cuadrarlo: de 9 mm de tangente a 17.

Los 16 mm de fondo que costó relajaron las tres cotas más apretadas del
presupuesto, y ninguna se buscó: la tapa de la fila de arriba **abre 180°**
(abría 151.2° y topaba con el remate), el chasis del PSU pasa de 3.33 a
**11.33 mm** contra los largueros de base —era «la cota más justa del
montaje»— y el fondo libre de la bandeja sube de 46.7 a 62.7 mm.

**La trasera es UNA plancha de 8 mm, empotrada y sellada** (2026-08-21). Fueron
**dos pieles de 5 mm flotando**: colgaban de doce separadores, con su cara
exterior 10 mm por detrás del canto de los costados y 5 mm de aire por los
cuatro lados — la junta de sombra. Estaban partidas a la altura del entrepiso
porque cada una se atornillaba a los dos largueros de su piso; al morir esa
bandeja la frontera dejó de existir. Su cara exterior cae exactamente en el
plano trasero, con `hol_piel` = 0.15 mm por lado de holgura de montaje.

Para que enrase, **los largueros traseros comparten X**
(`x_tr = fondo − rail/2 − t_piel`), y la plancha atornillada sobre su cara
remata en el canto. El de base estaba 14 mm más adelante que los otros tres, y
por ahí se había colado un fallo real: la fila de abajo de la piel de abajo pedía
un separador de 19 mm mientras el BOM listaba los de 5. Lo caza ahora `apoyo()`
en `clearance_budget.py`, la puerta nueva que exige que **todas las filas de una
placa apoyen a la misma distancia** de la cara de su larguero — porque el
separador de una placa es uno solo. `alineacion()` solo miraba un eje.

**El larguero del remate, y el fin del pegamento** (2026-08-21). La tapa que cierra
la meseta del techo iba **pegada** al Z-Rail, y era la única junta irreversible
del case: ahí arriba no había larguero al que atornillarla, y esa cara del riel
es pared de 1.2 mm. Ahora hay uno — un 2020 en la arista trasera-superior, a ras
del plano trasero y con su cara de arriba a `marco_sup` del techo. **El case
entero se desatornilla.**

No cabía más adelante: el **barrido del Z-Rail al abrir la tapa** de la fila de
arriba obliga a que su centro esté en x ≥ 286.17, y por eso el fondo creció de
291.2 a 299.2, y luego a **307.2** cuando ese mismo larguero tuvo que retirarse
otros 8 para que la trasera le pasara por delante. Con el centro en 289.22
quedan 3.04 mm de margen — los mismos que tenía antes de moverse.

Y con eso **todos los largueros traseros comparten X**: una sola cota para todo
el plano de apoyo de la trasera.

**Y junto a esa pared quedan DOS, no cinco** (2026-08-21). Llegaron a ser cinco
porque fueron creciendo uno por pieza: *entrepiso trasero* por la bandeja de
entrepiso, *repisa* por la piel superior, *remate superior* por la tira de
remate pegada de canto. Las tres piezas están muertas, y los tres largueros
seguían ahí solo como filas de tornillo de la trasera. Con la trasera hecha una
plancha continua de 8 mm eso no compra rigidez: una plancha atornillada arriba y
abajo **ya es el alma de cortante** de esa cara, y mejor alma que cinco barras
sueltas. Quedan el de abajo (*base trasera*) y el de arriba (*remate trasero*).

El vano libre entre los dos es **211.73 mm**, sobre 528 de ancho y 8 de espesor:
0.15 mm de flecha con 50 N empujando en el centro, 0.6 mm si alguien se apoya
con 200 N. La cuenta es la de una viga ancha biapoyada, `δ = PL³/48EI` con
E = 3 GPa e I = 528·8³/12.

Y la tapa **no llega hasta el pico**: se retira `inset_remate_frente` = 13 mm.
Eso no es estética — es lo único que la deja abrir. Hasta ahora esta pieza
giraba CON la tapa (por eso iba pegada al riel, que es parte de la tapa); al
fijarla pasa a ser obstáculo, y una plancha fija encima de una bisagra bloquea
la bisagra. Medido barriendo el conjunto giratorio contra la banda de la meseta:

| retiro | la tapa abre |
|---|---|
| 0 mm | 13.2° |
| 9.3 mm | 61.0° |
| **13 mm** | **180°** |

Lo que queda descubierto por delante de la tapa no es un agujero: debajo está el
propio Z-Rail, que llega a x=271.22. Es la línea de sombra entre la tapa que se
abre y el marco que no.

**Kerf: 0.** El proceso es **fresado CNC**, no láser (decidido el
2026-08-17). El CAM del taller compensa el radio de herramienta como parte
normal del trabajo, así que la pieza sale a la cota del dibujo. Cero no
significa «sin calibrar»: significa que no hay nada que compensar. Solo
vuelve a ser negativo si se regresa al láser.

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
relee los DXF tal como los verá la fresadora; si cualquiera de los dos está en
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
| **DXF** (`case/plans/*.dxf`) | **SÍ** | Todo — 8/8 archivos con el mismo SHA-256 en las 3 corridas (medido con 8; hoy son 11, las 3 nuevas son de acero) | OpenSCAD 2021.01 emite R12 determinista para geometría 2D |
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

`case/renders/build/vista_chasis_*.png` también: son vistas de viewport de
OpenSCAD, un segundo de regeneración cada una. Existen porque el chasis de acero
es la única pieza cuyo **interior** es el diseño, y no se ve en ningún otro
entregable — el DXF es plano y en el render del case queda detrás de los paneles
(se probó metiéndolo en `render.py`: dos PNG idénticos y minutos de Cycles).

`case/plans/lienzo_2d.dxf` va por el mismo camino: es la preview de las piezas
de acrílico en rejilla, no se manda a ningún sitio, y son otras 97.512 líneas de
diff. **El lienzo no lleva las tres piezas de acero** y es a propósito: van a
otro taller, con otro proceso (corte + plegado) y otro material, así que
nestearlas con el acrílico sería mentir sobre lo que se manda junto.

Lo que sí se versiona son los **nueve DXF sueltos** de `case/plans/` — cinco
piezas de acrílico, tres de acero y el cupón. Son el entregable que va al taller, y su diff es la
prueba de qué se mandó a cortar y cuándo.

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
| Z-Rail de Tiptop | **4** | 104 HP (528.32 mm), sección 23.8 × 10. Se compran en pares: 2 unidades = 4 raíles |
| Larguero perfil 2020 | **5** | de 528.32 mm cada uno: 2 de base, entrepiso delantero, valle y **remate trasero**. Fueron 8 hasta el 2026-08-21 |
| Tornillo **M4** | **8** | entran de punta por el costado y **roscan en el propio Z-Rail** (viene con M4 taladrado a 3.3 de fábrica). Sin tuerca, sin inserto. **No vienen con el raíl.** 4 de hombro (los ejes de giro) + 4 de mano (los cierres) |
| Tornillo M5 botón + tuerca T | **10** | 2 por larguero 2020, por la punta, desde el costado |
| Tornillo M3 + tuerca T M3 | **30** | las planchas a los largueros: base 10, tapa del valle 5, tapa de remate 5, **trasera 10** (2 filas × 5). Entran por la RANURA, no por la punta |
| Arandela ANCHA d16 | 4 | **no opcional**: en los ejes de giro. Con arandela M4 normal (d9) el apoyo sobre el acrílico da 16.3 MPa y el PMMA fluye en semanas; con d16 da 4.3 MPa y aguanta |
| Belleville M4 | 4 | precarga de los ejes: ~800 N dan 3.84 N·m de fricción, 1.5× el par de la tapa. **Sustituye al amortiguador**, que se eliminó |
| Plancha acrílico t=5 mm | **1** | solo la tapa del valle. Un espesor entero para **una** pieza — a resolver en el pliego, no en el modelo |
| Plancha acrílico t=8 mm | **5** | 2 costados + suelo (bandeja de base, portante, 528.32 × 291.4, con la rejilla de entrada de aire en el vuelo) + tapa de remate (528.32 × 37) + **trasera** (528.02 × 245.18) |
| Patica metálica torneada | 4 | d=16 × 8 mm |

**Total de tornillos del case: 48** — 8 M4 de raíl + 10 M5 de esqueleto +
30 M3 de plancha. Eran 71, y el 2026-08-21 perdió 23 de golpe: al empotrarse, la
trasera se llevó por delante 12 separadores M4 y sus 24 tornillos de botón; al
morir la bandeja de entrepiso se fueron 10 M3; volvieron 2 M5 y 5 M3 con el
larguero del remate y su tapa; y al quedarse la pared trasera con dos largueros
en vez de cinco se fueron 6 M5 y 15 M3 más. Lo que no volvió es el adhesivo:
**el case ya no lleva ninguna junta irreversible.**

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

Las planchas de acrílico (bandeja de base, tapa del valle, tapa de remate y trasera) se atornillan
**únicamente a largueros del esqueleto**, nunca a los 4 raíles de panel. Los
raíles de panel van girados al ángulo de su cara (35° / 45° desde la vertical) para quedar a ras
del panel: un tornillo contra esa cara entraría a 12° del eje de su agujero
(≈1.05 mm de descentre en 5 mm de acrílico, contra 0.7–0.9 mm de holgura) y la
arandela asentaría sobre cara inclinada — carga de borde sobre acrílico frágil,
que es justo el modo de fallo que este proyecto ya conoce.

**El zócalo delantero se eliminó** (2026-08-17), y con él su larguero propio y
sus dos standoffs largos de ~33 mm. Este apartado describía esa pieza hasta
esa fecha. `alto_frontal` pasó de 50 a 13 mm y ya no es un zócalo: es el canto
delantero del case. Volvió a **19 mm** el 2026-08-21, y no por estética: es lo
que hace falta para levantar el raíl de panel por encima de la bandeja y poder
cerrar el suelo.

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

1. **Esqueleto** — costados + los 8 largueros 2020, M5 por la punta desde
   fuera. Meter aquí las 42 tuercas T M3 de las planchas: con tuercas de
   inserción lateral se pueden añadir después, con las de deslizar no.
2. **Bandeja de base** — 8 mm, es el suelo, 5 M3 por fila. Era «bandejas» en plural hasta el 2026-08-21: la de entrepiso murió.
3. **Los 4 Z-Rails** — M4 desde fuera, roscan en el propio riel. Comprobar
   antes que la pletina roscada corre por su canal.
4. **Tapa del valle** — 5 M3 al larguero del valle.
5. **Electricidad y bonding** — bloque IEC fijo, espárrago junto al PSU.
6. **Trasera** — UNA plancha de 8 mm, EMPOTRADA, 25 M3 a tuerca T repartidos
   en las cinco filas de los largueros traseros. Va después de los largueros
   porque la tuerca T vive dentro de la ranura.
7. **Tapa de remate** — 5 M3 al larguero de remate trasero. Va ATORNILLADA
   desde el 2026-08-21; hasta entonces iba pegada al Z-Rail y era la única
   pieza irreversible del case.
8. **Paticas y paneles** — y paneles ciegos en todo hueco de las dos filas,
   que con una tapa abierta son lo único que ata sus dos raíles.

El orden importa en dos sitios: las bandejas no se pueden atornillar antes
que sus largueros (la tuerca T vive en la ranura del perfil), y los raíles
quieren estar antes que cualquier panel. Era en TRES: el tercero era que la
pestaña quedaba irreversible una vez pegada, y ese ya no existe — todo el
case se desmonta.

Guía ilustrada con renders del modelo:
https://claude.ai/code/artifact/0ff54175-6449-4e14-93dd-7c614251bf17

## Estado

- [x] Modelo paramétrico + DXF de corte
- [x] Chasis de acero del PSU (#107): cuerpo, tapa y refuerzo, con su
      desarrollo de plegado y su puerta — ver `guarda_chasis()` en
      `clearance_budget.py`
- [x] **Plano de plegado** ([`renders/chasis-plano-plegado.png`](renders/chasis-plano-plegado.png)),
      generado por `renders/plano_chasis.py` releyendo los mismos DXF que se
      mandan a cortar. Un `.dxf` lleva geometría de corte y **no dice de dónde
      doblar**: mandarlo solo es mandar media pieza
- [x] Cupón de calibración
- [x] `clearance_budget.py` en verde
- [x] Plantilla de panel KiCad
- [x] Render del conjunto — dos vistas: frontal
      ([`renders/sam17-case.png`](renders/sam17-case.png)) y trasera
      ([`renders/sam17-case-trasera.png`](renders/sam17-case-trasera.png)).
      La trasera es la que importa: muestra las tres ondas — sierra, triángulo
      y cuadrada, las tres formas del VCO — que son la firma visual del case y
      la única ventilación de esa pieza.
- [ ] Cupón cortado y kerf registrado (bloquea el corte de planchas)
- [ ] Planchas cortadas y ensayo de ensamblaje
