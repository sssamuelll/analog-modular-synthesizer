# Case SAM17 — consola de dos pisos, esqueleto de aluminio

> **La costilla dejó de ser chapa plegada el 2026-08-28** y pasa a ser un
> **anillo de pletina de aluminio mecanizada** (14 mm, fresado CNC, una
> pieza por lado, sin soldadura) que sigue cargando todo el case. El
> acrílico sigue siendo **piel** sin un solo taladro, ahora asentado
> COPLANAR en un rebaje detrás de la cara vista del anillo, sobre una junta
> de EPDM de 1 mm — ya no hay casquillo de aluminio ni junta de 4 mm entre
> costilla y costado. El suelo sigue siendo una **tabla de madera** que hace
> de zócalo a la vez. El diseño entero está en
> [`../docs/superpowers/specs/2026-08-28-costilla-pletina-design.md`](../docs/superpowers/specs/2026-08-28-costilla-pletina-design.md).
>
> **Histórico — el acrílico dejó de cargar el 2026-08-26.** Hasta esa fecha
> este README decía «consola en acrílico naranja» y la pieza que sostenía el
> aparato era el costado. La estructura pasó primero a chapa de aluminio
> plegada
> ([`...2026-08-26-case-esqueleto-aluminio-design.md`](../docs/superpowers/specs/2026-08-26-case-esqueleto-aluminio-design.md))
> y de ahí, el 2026-08-28, a la pletina mecanizada de arriba.

Spec: [`docs/superpowers/specs/2026-08-15-case-design.md`](../docs/superpowers/specs/2026-08-15-case-design.md) (rev. 22)
Board de intención: [`renders/propuesta-diseno-2026-08-16.png`](renders/propuesta-diseno-2026-08-16.png)
— **manda sobre lenguaje visual, NO sobre cotas**: se dibujó para paneles de
190 mm y un case de 500 × 380 × 350, y el case real mide 568.62 × 256.18 × 307.41.

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

**Dimensiones** (salida real de `clearance_budget.py`, `perfil()`):

| | |
|---|---|
| ancho total | **568.62 mm** = `ancho_util` + 2 × `t_anillo` (2026-08-28; era 544.32 con la costilla de chapa) |
| alto total | **256.18 mm** |
| fondo | **307.41 mm** (bbox de `costilla_2d`; era 308.94 con el contorno viejo) |
| altura de entrepiso | **146.58 mm** |
| ancho útil entre anillos | **540.62 mm** = `largo_riel` + `hol_riel` + 2 × `t_placa` (donde van rieles y miembros; era 528.32 antes de la placa de anclaje) |

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

**Y la entrada de aire se queda abajo del todo en la trasera.** Se mudó cuatro
veces el mismo día y el paseo vale la pena, porque cada mudanza cerró una
pregunta:

| | dónde | por qué se fue |
|---|---|---|
| 1 | hueco de 37.96 mm en el suelo | no era diseño, era lo que sobraba |
| 2 | trasera, abajo | al cerrar el suelo hubo que dibujarla |
| 3 | suelo, en el vuelo de la bandeja | Samuel dejó la trasera con sus ondas |
| **4** | **trasera otra vez** | en el vuelo **se veía** |

La tercera murió por una razón que no sale en ningún número: el acrílico naranja
es **traslúcido**, y el campo de ranuras se transparentaba a lo largo del canto
inferior. Se ve en el render oficial, no en la geometría.

Eran 45 ranuras del mismo lenguaje —mismo ancho y registradas al HP— en la banda
que dejan libre la fila de tornillos por abajo y la onda por arriba (cifra de
2026-08-21; **hoy son 44**: la escuadra de la trasera, Tarea 4b, tapa la
primera columna con su ala A y la puerta pasó a saltarla entera en vez de
contarla — `clearance_budget.py` imprime «entrada 6781 mm2 en 44 ranuras de
41.9 x 3.75»).

**Y desde el 2026-08-29 ese 44 lo cruza una puerta**, `ranuras_rejilla_entrada()`
en `check_dxf.py` (#236). Hasta entonces era una gemela **por lectura**: el área
la derivaba el presupuesto, el `.scad` rederivaba las columnas por su cuenta, y
`check_dxf` solo censaba círculos — una ranura es obround y el censo la deja
fuera a propósito. El único cruce entre los dos lenguajes fue un humano contando
entidades `LINE` del fichero (3418 → 3368) el día que la escuadra se comió una
columna. Ahora se exige una ranura por columna adjudicada y ninguna de más, el
ancho, y la banda libre entera de alto: los 6 781 mm² dejan de ser un número de
fe y pasan a ser área que **está cortada**.
El hueco del IEC vive **dentro** de esa banda, así que queda embebido en el
campo en vez de al lado: se saltan sus columnas enteras, con 11.25 mm de
material contra la ranura más cercana. Partir una ranura con el recorte
dejaría un diente de acrílico colgando de un lado, que es justo donde el PMMA
rompe.

La rejilla y las ondas se separan **14.00 mm**. Eran 4 —`vent_puente_min`, el
mínimo por fragilidad— y los dos campos se leían como uno. `vent_puente_min`
ya no vale 4: aquel mínimo se medía contra la tapa del valle cuando era
acrílico de 5 mm (0.8 × 5 = 4); desde `b799e8b` la regla mide 0.8·t contra la
trasera de 8 mm de PMMA y subió a **6.5**, con la ranura de la rejilla
bajando a 3.75 para pagar la diferencia. Subir la onda sola no
lo arreglaba: el borde de la rejilla estaba *derivado* de la onda, así que subía
con ella y la separación se quedaba clavada en el mínimo. Se movieron las dos:
`y_bajas` 0.32 → **0.37** del vano entre filas, y la separación pasa a ser un
parámetro de dibujo propio (`vent_separacion`) en vez del mínimo de fragilidad.

Se mide **entre bordes de material**, no contra la polilínea de la onda: la onda
es un hull de círculos y asoma medio ancho de ranura por debajo de su polilínea.
La primera versión se olvidó ese término y los 14 salieron 12.

| | área abierta | altura | ranuras |
|---|---|---|---|
| entrada (trasera, abajo) | **6 781 mm²** | y = 45 | 44 de 41.9 × 3.75 |
| salida — meseta | **852 mm²** | y = 255 | 16 de 15 × 3.75 |
| salida — las dos ondas abiertas | 2 289 mm² | y ≈ 95 | — |

La banda del valle queda **lisa** desde el 2026-08-28. Su antigua salida sube
a la meseta del miembro trasero alto: menos área a mucha más altura mantiene el
tiro y deja esa cara horizontal sin ranuras.

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
centroides. Con 6.33 W de reguladores (spec PSU v2 §4) salen **6.6 K** sobre
ambiente contra un techo de 15. En el suelo salían 4.6 —más área y más tiro—,
y esos 2 K son lo que cuesta que no se vea. **SUPUESTO, no medido**: `C_D` = 0.65, y las
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

Efecto colateral: el vuelo de la bandeja pasa de 30.19 a **68.85 mm**. Mientras
la rejilla de entrada vivió ahí creció con él —está derivada del vuelo, no de un
número a mano— y el salto térmico bajó a 4.6 K. Al volver la rejilla a la
trasera, el vuelo se queda de plancha maciza: 68.85 mm de suelo continuo por
delante del larguero.

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
presupuesto, y ninguna se buscó: la tapa de la fila de arriba **abría 180°**
en 2026-08-21 (venía de 151.2° y topaba con el remate) — **superado el
2026-08-27**: con `APERTURA_MIN` = 60 la fila de arriba abre **123°** y la de
abajo **63.8°** hoy (salida real de `clearance_budget.py`; los dos topan
contra un miembro del esqueleto, no contra el remate). El resto de este
párrafo describe el estado de 2026-08-21 y sigue siendo cierto sobre ESE
punto en el tiempo. El chasis del PSU pasa de 3.33 a
**11.33 mm** contra los largueros de base —era «la cota más justa del
montaje»— y el fondo libre de la bandeja sube de 46.7 a 62.7 mm.

**La trasera es UNA plancha de 8 mm, empotrada y sellada** (2026-08-21). Fueron
**dos pieles de 5 mm flotando**: colgaban de doce separadores, con su cara
exterior 10 mm por detrás del canto de los costados y 5 mm de aire por los
cuatro lados — la junta de sombra. Estaban partidas a la altura del entrepiso
porque cada una se atornillaba a los dos largueros de su piso; al morir esa
bandeja la frontera dejó de existir. Se empotra entre los dos anillos con
`hol_piel` = 0.15 mm por lado de holgura de montaje.

**Y desde el 2026-08-29 ya no es la pieza más exterior de esa cara: se rehunde
`t_costilla` y la enmarca el metal** (#234). Su cara exterior caía exactamente
en el plano trasero, y con ella caían sus dos cantos: el superior y el inferior
corrían **540 mm cada uno sin un milímetro de metal encima**. El de arriba era
además los últimos 8 mm del **pico** del case — `guarda_remate()` repartía esa
meseta entre `inset_remate_frente` + `prof_sup` + `t_piel`, y ese `t_piel` era,
con todas sus letras, el canto del acrílico haciendo de superficie vista.

Lo que asoma ahora al plano trasero son **dos bandas de chapa de 1.5**, las
mismas de los miembros:

- **arriba**, un angular: banda vista de 20 mm y un ala de 9.5 que dobla sobre
  el canto superior del acrílico y **muere en el doblez de la meseta**, con la
  que queda coplanar. El pico pasa a ser metal de punta a punta.
- **abajo**, una pletina plana de 20. Sin ala, y no es un olvido: ese canto
  está en el plano del suelo y debajo tiene la tabla, no aire — un ala ahí
  levantaría el case de su propia base.

Las dos cuelgan de las filas de M3 que la plancha **ya** llevaba a sus dos
miembros: cero taladros nuevos en el acrílico, tornillos 1.5 mm más largos, y
las diez cabezas que se veían sobre el PMMA pasan a verse sobre metal.

Lo que se pagó: `prof_sup` baja de 29 a **27.5**, porque el trozo de atrás del
pico crece de `t_piel` a `t_piel + t_costilla` y los 1.5 no podían salir del
inset — su acantilado está en 12.8 (con 13 la tapa de arriba abre 180°, con
12.8 abre 61). La meseta no se mueve por delante: el miembro se adelantó 1.5 y
el ala se acortó lo mismo, así que el barrido probado de la tapa sigue intacto,
y sus 16 ranuras de salida (852 mm²) tampoco cambian.

Lo vigila `guarda_marco_trasera()`, y lo primero que exige es justo lo del
issue: que el ala de arriba tape el canto **entero** y muera en el doblez, sin
rendija.

**Y baja hasta el suelo** (2026-08-22). Su canto inferior estaba en y = 3 y el
plano del piso es y = 0: quedaba un rebaje corrido de **528 × 3 × 8 mm** a lo
largo de todo el canto trasero. No era fuga —el canto de la bandeja lo cierra
8 mm adentro— pero era una **junta de sombra**, justo el lenguaje que esta pieza
enterró al empotrarse, y por eso la plancha se leía colgada en vez de asentada.

Venía de un `- 15` sin derivar copiado en cinco sitios (dos en el `.scad`, tres
en `clearance_budget.py`): era la distancia al canto de la fila de M3, leída
como si fuera una cota del case. Ese 15 no sabía dónde estaba el suelo. Ahora el
canto es **y = 0**, el mismo datum del que cuelga la bandeja de base, y lo exige
`guarda_piso()` en su cuarto assert — ninguna otra puerta lo miraba: `solapes()`
no canta porque no hay solape, y `alineacion()`/`apoyo()` solo ven filas de
agujeros.

Lo que costó: la plancha pasó de 245.18 a **248.18 mm** de alto — ese número
es de aquel día; hoy mide **540.32 × 254.68**, y lo que lo movió después fue la
meseta integrándose en el miembro (27-08). Lo que NO se
movió, y se verificó con la salida de la puerta byte a byte contra la de antes:
las tres ondas, la rejilla de entrada, el área abierta y los 6.6 K. Van
derivadas de `f_base` y `f_tras`, que son diferencias contra `ce[].y`, así que
no dependen del canto. Y la fila de M3 de abajo se **aleja** del canto, de 15 a
18 mm: más material alrededor del tornillo, no menos.

Para que enrase, **los largueros traseros comparten X**
(`x_tr = fondo − rail/2 − t_piel`), y la plancha atornillada sobre su cara
remata en el canto. El de base estaba 14 mm más adelante que los otros tres, y
por ahí se había colado un fallo real: la fila de abajo de la piel de abajo pedía
un separador de 19 mm mientras el BOM listaba los de 5. Lo caza ahora `apoyo()`
en `clearance_budget.py`, la puerta nueva que exige que **todas las filas de una
placa apoyen a la misma distancia** de la cara de su larguero — porque el
separador de una placa es uno solo. `alineacion()` solo miraba un eje.

**Y la barra del medio se va** (2026-08-25). El larguero de **entrepiso
delantero** cruzaba el centro del volumen —centro en x = 200.32, y = 131.58, o
sea 25.95 mm por detrás y 17.55 por debajo del riel de abajo de la fila de
arriba— y era **el único larguero del case que no sostenía ninguna plancha**:
las seis filas de M3 van a base delantera, base trasera, valle y remate trasero.

Por eso no lo miraba ninguna puerta. `alineacion()` y `apoyo()` solo ven filas
de agujeros; `solapes()` solo verifica que las piezas no se atraviesen. Se podía
retirar y quedarse todo en verde — que es lo que hace peligroso el cambio, no el
cambio.

Su único trabajo era atar los costados a media altura, y a **esa misma altura**
(y = 131.58) ya está el del valle, 75.14 mm por delante y encima con su tapa. Es
el mismo argumento que el 2026-08-21 tumbó tres largueros de la pared trasera,
aplicado al que quedaba: una barra que no es alma de nada.

**Lo que cuesta**, medido sobre el contorno real de `costado_2d.dxf` y no
estimado. El parche de costado que queda sin apoyo se trata como placa circular
empotrada de radio `a` = distancia del punto más desasistido a su ancla más
cercana, con `D = E t³/12(1−ν²)`, E = 3 GPa, ν = 0.37, t = 8:

| | con la barra | sin ella |
|---|---|---|
| vano libre del costado | 107.9 mm | **118.9 mm** |
| flecha con 200 N | 0.31 mm | **0.38 mm** (techo 0.60) |
| tensión bajo la mano | 6.35 MPa | **6.56 MPa** (fluencia 10, #106) |
| abrir los costados donde estaba, 200 N | — | 0.303 mm en total |
| masa | — | **−228 g** |

El punto más desasistido del costado **no era el suyo, ni antes ni después**:
está en el canto trasero a media altura (x = 244, y = 128), donde además apoya
la trasera — que el modelo no cuenta, así que el número va por el lado seguro.
Las anclas son solo los cuatro M5 de larguero: los cuatro M4 de riel no cuentan
porque dos son ejes de giro y dos son tornillos **de mano** que se quitan para
abrir, y un anclaje que el usuario desmonta no es estructura. Contándolos el
vano sale 111.3 en vez de 118.9.

**Se acota por flecha y no por tensión**, y la razón es que la tensión no es el
limitante ni de lejos: para llegar a los 10 MPa el vano tendría que valer
642 mm —más que la pieza entera—, porque en una placa empotrada la tensión crece
con el **logaritmo** del vano y la flecha con el **cuadrado**. Lo que se nota con
la mano es la flecha. Un costado que se hunde al empujarlo se siente barato
aunque no rompa nunca.

Lo vigila `guarda_costado()` en [`check_dxf.py`](check_dxf.py), y vive ahí y no
en el budget porque mide sobre el **contorno y los taladros reales del DXF**, no
sobre una copia de la geometría en Python.

**Lo que este cálculo NO cubre**: el racking del cajón entero. La puerta mira
UNA pieza plana. La rigidez del vano de 528 mm sin costado central sigue siendo
la heurística que la spec §11 no ha cerrado (`n_bulkheads` = 2, «3 si el vano
flexa»), y este cambio le quita una barra. Se cierra cargando el prototipo.

**La tapa del valle pasa a aluminio** (2026-08-25). Era la plancha más floja
del case y a la vez la **única cara horizontal** — o sea donde se apoya quien se
levanta, no donde se posa la mano al parchear.

El número que lo decide es la proporción en voladizo: la tapa mide 66.5 mm de
fondo y el larguero solo la toca **20 mm**, así que **el 70 % de la pieza
vuela** — 23.24 mm a cada lado.

Ojo con el modo de carga, porque la primera cuenta salió mal: el larguero del
valle corre los 528 mm enteros, así que hacia abajo la tapa apoya en una **línea
continua**, no sobre los 5 M3. El vano entre tornillos no existe en ese modo;
los M3 solo trabajan al tirar de la tapa hacia arriba. Lo que flexa es el
voladizo transversal.

| | acrílico 5 mm | **aluminio 3 mm** |
|---|---|---|
| flecha con 200 N en 50 mm | 0.535 mm | **0.108 mm** |
| tensión | 22.3 MPa | **62.0 MPa** |
| contra su límite | 10 (fluencia PMMA) — **lo pasa** | 130 (`Rp0.2` 5754 H22) — factor **2.1** |
| fluye a | **90 N** | **420 N** |

**Las otras tres salidas están cerradas, y conviene que quede escrito para que
nadie las reintente:**

- **Acrílico de 6 mm**: bloqueado. La tapa invade el barrido del riel y la fila
  de abajo pasa de abrir 180° (cifra de 2026-08-25; hoy abre 63.8°, ver
  arriba) a 39.5°.
- **Larguero de 30 mm** en vez de 20: entra por **0.24 mm**, que está por debajo
  de la tolerancia de la propia extrusión. Eso no es holgura, es suerte.
- **Larguero de 40 mm**: no entra. Se pasa **4.76 mm** de su ventana, que la
  fijan las esquinas giradas de los dos raíles del valle.

El aluminio resuelve por rigidez específica en vez de por espesor, y al ser más
fino **devuelve 2 mm de barrido** en vez de comérselos.

**Y no rompe el lenguaje visual**, que era la única objeción seria: los paneles
de módulo ya son **PCB de aluminio** a los dos lados de esta banda. Una tapa de
aluminio entre dos filas de aluminio se lee como que la banda central pertenece
a los paneles. En el modelo también cambió de sitio — sale de
`planchas_acrilico()` y entra en `assembly_aluminio()`, o si no el render la
pintaría translúcida y naranja, que es peor que no dibujarla.

Lo que se lleva por delante, y es ganancia: **la única línea de BOM de 5 mm**.
El cuerpo de acrílico queda con **un solo espesor**. Y `t_acrilico` se llama
ahora `t_valle`, porque el nombre viejo habría mentido sobre el material.

Efecto colateral medido: al adelgazar la tapa, el larguero del valle sube 2 mm
para seguir tocándola, y con él su M5 en el costado — que pasa de estar a 15.03
mm del canto a **13.03 mm**, o sea de 2.73 D a **2.37 D**. Sigue muy por encima
del mínimo de 1.5 D que exige `taladros_con_material()`.

**El larguero del remate, y el fin del pegamento** (2026-08-21, histórico). La tapa que cierra
la meseta del techo iba **pegada** al Z-Rail, y era la única junta irreversible
del case: ahí arriba no había larguero al que atornillarla, y esa cara del riel
es pared de 1.2 mm. Ahora hay uno — un 2020 en la arista trasera-superior, a ras
del plano trasero y con su cara de arriba a `marco_sup` del techo. **El case
entero se desatornilla.** Ese larguero es el mismo que hoy se llama **miembro
trasero alto** (perfil 2020 comprado hasta el 2026-08-27; canal de chapa
propio desde entonces) — y la tapa que ata no existe: la meseta pasó a ser
su propia ala el 2026-08-27, así que la «junta pegada, ahora desatornillable»
de este párrafo describe una pieza que ya no está, aunque el larguero sigue.

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
| **13 mm** | **180°** (2026-08-21; hoy 123°, `APERTURA_MIN` desde el 2026-08-27) |

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

Lo que se manda al taller **no son solo los DXF**: van con
[`PLIEGO.md`](PLIEGO.md), que lleva material, procesos, acabados, profundidad
de cajeado y qué cara es la exterior. Un DXF suelto es media pieza. Para
elegir taller antes de pedir, [`RFQ.md`](RFQ.md).

Corre `clearance_budget.py` ANTES de exportar y `check_dxf.py` DESPUÉS —
relee los DXF tal como los verá la fresadora; si cualquiera de los dos está en
rojo, el script sale con código distinto de cero y no se exporta ni se deja
nada a medias. Los DXF van en mm; decírselo explícito al servicio de corte.

La plantilla KiCad de panel se regenera aparte, con el Python de KiCad (no
el del sistema, porque importa `pcbnew`):

```powershell
"C:/Program Files/KiCad/10.0/bin/python.exe" case/panels/build_template.py --ancho 100
```

### El naranja del render, y por qué no es una cota

`render.py` pinta el acrílico con `Base Color` **(1.0, 0.24, 0.04)**, que en
sRGB es **#FF8638**. El valor se eligió **mirando el render**, no calculándolo:
estuvo en (1.0, 0.35, 0.05) —#FFA03F, ámbar— y pasó unas horas por
(1.0, 0.16, 0.04) —#FF6F38—, que Samuel descartó el 2026-08-26 por rojo.

Se decide mirando y no con una muestra de color porque el material lleva
`Transmission Weight` = 0.85: **el tono que se percibe no es el hex plano**. Un
chip de color al lado de este render no se parecen, y el que manda es el
render.

**Y no es una cota del material.** El PMMA naranja todavía no está comprado y
su tono lo fija el proveedor, no este archivo. El día que llegue la plancha,
lo que se ajusta es el render para parecerse a ella — no al revés. Esto es
intención visual, del mismo tipo que el board de 2026-08-16: manda sobre
lenguaje, no sobre nada que se corte.

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
de acrílico en rejilla, no se manda a ningún sitio, y son otras 58.894 líneas de
diff. **El lienzo no lleva las tres piezas de acero ni la tapa del valle** y es a
propósito: van a otro taller y con otro proceso —las del chasis, corte y
plegado; la del valle, corte de chapa—, así que nestearlas con el acrílico
sería mentir sobre lo que se manda junto. La tapa salió el 2026-08-25, con el
cambio de material: hasta entonces era la tercera plancha de la segunda fila.

Lo que sí se versiona son los **quince DXF que se mandan a cortar** de
`case/plans/` (más `lienzo_2d`, la preview de arriba que no se manda —
dieciséis ficheros en total, contados el 2026-08-28): dos de acrílico
(costado, trasera — **la tapa de remate NO EXISTE**: no es un pendiente de
`export.ps1`, es una pieza que se borró del diseño el 2026-08-27, y
`remate_sup()`/`remate_sup_2d()` se borraron del `.scad` en el fix round 1
de esta tarea por no tener llamador), **dos del anillo mecanizado** (cara
vista y dorso, §6.1 del pliego), cinco de chapa de aluminio (los tres
miembros con brida, la escuadra de la trasera y la tapa del valle), tres de
acero, una de madera, el cajeado de la marca y **el cupón** (calibración de
kerf del acrílico, §"Procedimiento del cupón" abajo). Son el entregable que
va al taller, y su diff es la prueba de qué se mandó a cortar y cuándo.

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
3. Probar la ranura con el perfil 2020 y la lengüeta con arandela+tuerca,
   **apretando a `par_m3` (1.0 N·m) con destornillador dinamométrico**. La
   «sensación de tope» dejó de ser el criterio el 2026-08-24: el par sale de
   la arandela y está calculado, no se estima con la muñeca.
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
| **ANILLO** (costilla) — pletina de aluminio **FRESADA** t=14, cara vista 20 | **2** | **la pieza portante del case, mecanizada, no plegada** desde el 2026-08-28. Rebaje 6 × 11 por detrás donde asienta el costado, chaflán 1.5 × 45° en las dos aristas de la cara vista. **16 roscas ciegas M4 por anillo** en la cara interior (`taladros_anillo`) + 3 M5 por anillo en el canto inferior para la tabla. Anodizado satinado, punto de bonding enmascarado. Ni casquillo ni junta de 4 mm: el costado asienta en el rebaje sobre una junta de EPDM de 1 mm |
| **MIEMBRO** de chapa — trasero bajo, trasero alto, bahía | **3** | aluminio 6082-T6 t=1.5, canal con **BRIDA de extremo** doblada en cada punta, roscada al anillo con M4 ciegos. Fueron perfil 2020 comprado hasta el 2026-08-27 |
| Z-Rail de Tiptop | **6** | 104 HP (528.32 mm), sección 23.8 × 10. Cuatro forman las dos filas 3U y dos la fila Intellijel 1U. Atornillan a una **placa de anclaje** interior, no directo al anillo |
| Tornillo **M4** para los rieles | **12** | roscan en el propio Z-Rail (M4 taladrado a 3.3 de fábrica). Sin tuerca, sin inserto. 4 de hombro (ejes de giro) + 4 moleteados (cierres) + 4 fijos (fila 1U, no giran) |
| **PLACA DE ANCLAJE** — pletina t=6 | **6** | una por tramo y por costado (3U × 2 + valle). Cajeado de 8 × 2.5 por el lado del anillo para la cabeza del M4 del riel. **Orden obligado: primero el riel a la placa (cabeza en el cajeado), después la placa al anillo desde dentro** — al revés no se puede apretar |
| Tornillo M4 botón (brida de miembro) | **8** | por la punta de los dos miembros traseros, a rosca ciega en el anillo. Eran M5 hasta el 2026-08-28: bajan a M4 porque la franja de 14 mm no admite las dos brocas (paso M5 + broca M5) a la vez |
| **ESCUADRA DE LA TRASERA** — chapa 6082-T6 t=1.5 | **2** | angular atornillado a la **TRASERA** (nunca al anillo): tope hacia dentro del canto trasero del costado, que quedaba sin apoyo. Va al taller de chapa con los miembros |
| Tornillo M3 + tuerca (escuadras) | **6** | pasantes por los 8 mm de PMMA de la trasera, cabeza fuera y tuerca dentro. No hay rosca ciega nueva en el anillo |
| **CLIP DE RETENCIÓN** — pletina t=4 | **4** | 2 por costado, solo en el tramo del SUELO (el único de los cuatro sin placa de anclaje). Un M4 ciego al anillo por clip, muerde 24 mm de acrílico desde el canto de la ventana |
| **JUNTA DE ASIENTO EPDM** t=1 mm | **2** | una por anillo, perfil continuo en el rebaje entre el labio y el costado. Nunca aluminio contra acrílico — no es la junta de 4 mm del apilado viejo, muerta el 2026-08-28 |
| Tornillo M4 (lengüetas de bahía) | **4** | las dos lengüetas de la bahía a la placa de la fila 1U, roscadas **en la placa** (6 mm de pletina), no en el anillo |
| Tornillo M5 + tuerca T + separador 3 mm | **2** | cuelgan la pared **trasera** del chasis del PSU de la ranura interior de `base trasera` (#106). La pared delantera **apoya en la tabla** |
| Tornillo **M3 botón** + tuerca T M3 + **arandela ancha d16** | **17** | las planchas a la retícula del miembro: trasera 10 (trasero bajo + trasero alto, 5 cada uno), tapa del valle 5 a la **bahía** (`check_dxf`: `bahia_2d` trae su propia retícula de 5 M3), + **2 de las pestañas** de la tapa del valle **a la placa del valle** (no al anillo, ruling R3). Entran por la RANURA del miembro, no por la punta. **Apriete 1.0 N·m con rosca SECA**. Ver `par_m3` |
| Arandela ANCHA d16 | **24** | 20 bajo los M3 que muerden acrílico (8.7 MPa, techo 10) + 4 en los ejes de giro. **Los 2 M3 de pestaña no la necesitan**: aprietan aluminio contra aluminio |
| Belleville M4 | 4 | precarga de los ejes: ~800 N dan 3.84 N·m de fricción, 1.5× el par de la tapa |
| **Chapa de aluminio t=3 mm** — banda delantera del valle | **1** | vuelo delantero liso, desarrollo 572.00 × 18.30, con pestaña de 21 mm doblada en cada punta, atornillada a la **placa del valle** con un M3 (no al anillo desde el 2026-08-28). Aleación recomendada, no obligatoria: 5754 H22 pasa a 130 MPa con margen (48.8 MPa real, `guarda_valle()`). Va al taller de CHAPA — sin recocido, sin diamantado, sin chaflán: eso es del PMMA |
| **TABLA de madera maciza t=18 mm** | **1** | el suelo interior y el zócalo, una sola pieza, **588.62 × 327.41** (creció desde 570.62 × 328.94: el anillo es más grueso que la vieja costilla de chapa). 2 filas de 3 M5 a **rosca ciega en el canto inferior del anillo** (una fila por anillo), uno redondo por fila (punto fijo) y dos en ranura de 10.5 |
| Plancha acrílico t=8 mm | **3** | 2 costados + **trasera** (540.32 de ancho, con las ondas y la rejilla de entrada de aire). **Sin un solo taladro**: asientan en el rebaje del anillo, retenidas por el labio, las placas, los clips y la escuadra — nunca por un tornillo propio. Eran 4 hasta el 2026-08-27, con la tapa de remate; esa pieza no existe (ver más arriba) |
| Patica de goma con casquillo roscado | 4 | EPDM o NBR, Shore 45–55 A, **d20 × 10**. Se atornillan **a la tabla**, no al acrílico. **Se exige la curva carga-deformación: ≥ 0.25 mm de flecha con 22.8 N** — por debajo la pata AMPLIFICA los 100 Hz del toroide en vez de aislarlos (`flecha_pie`). Casquillo roscado moldeado: se atornilla, **no se pega** |

**Total de tornillos itemizados en el BOM: 59** — 12 M4 de raíl + 8 M4 de
brida + 6 M3 de escuadra + 4 M4 de clip + 4 M4 de lengüeta de bahía + 2 M5
del chasis + 17 M3 de plancha + 6 M5 de la tabla. **No incluye los M4 de la
placa al anillo**: son **10 por anillo** (20 en total), el resto de las 16
roscas ciegas por anillo que imprime `taladros_anillo()` — las otras 6 por
anillo ya están en la cuenta de arriba: 4 de brida (2 bridas × 2) + 2 de
clip (2 clips × 1). Esos 20 M4 de placa no están itemizados como herraje a
comprar en ningún `echo` todavía — es un pendiente real, no un olvido, y
queda anotado para no mandar a montar de memoria.

Eran 44 el 2026-08-27 (antes de esta tanda) y 71 antes del 2026-08-21: el
historial completo de qué entró y qué salió, tornillo a tornillo, vive en
`git log` sobre este mismo README — no se repite aquí para no arrastrar una
tercera copia que se desincronice.

**Y el reparto sigue sin tocar el acrílico:** de los tornillos de arriba,
**ninguno atraviesa el costado**. Todos los estructurales entran en aluminio
— antes en la costilla de chapa, ahora en el anillo o en las placas/miembros
que cuelgan de él. Lo que no volvió es el adhesivo: **el case sigue sin
ninguna junta irreversible.**

No calculados por el modelo (herrajes eléctricos y de panel; la cantidad
depende de la cuenta final de módulos, no de la geometría del cajón):

| Pieza | Cantidad | Nota |
|-------|----------|------|
| IEC C14 con fusible | 1 | entrada de red, aparato Clase I |
| Espárrago M4 (bonding) | 1 | único — ver «Bonding de tierra» |
| Cable verde/amarillo + terminal de ojal | 1 por panel | al espárrago único, sin excepción |
| Tuerca T M3 | 4 por panel | uno por taladro de `panels/build_template.py` |

Censo de paneles, **reescrito el 2026-08-27**. Los 8 que decía antes
(MIDI/CV, VCO×3, VCF, ADSR, VCA, MIXER) eran de la tesis: los tres VCO
colapsaron en un módulo y los módulos 4-7 **desaparecieron como placa**
el 2026-08-23. `ANCHOS_PISO_SUP`/`ANCHOS_PISO_INF` ya no existen.

- **Fila de arriba: UN panel** de 104 HP con la pantalla de 7" en su centro
  y los mandos en los dos flancos de 181,66 mm
  (`2026-08-27-panel-pantalla-al-centro-design.md`). Su reparto interno entre
  PCB y bahía lo lleva `voz_total_budget.py`, no este fichero.
- **Fila de abajo: SIN CERRAR**, y con dos descripciones vivas que no
  coinciden — ver «Lo que este cálculo NO cubre» en `clearance_budget.py`.

**Estimado, no cerrado**: los totales por panel cierran cuando cada panel
esté dibujado.

## Anclaje de las placas — solo a los miembros del esqueleto, nunca a raíles de panel

Las planchas (trasera, de acrílico; tapa del valle, de aluminio) se
atornillan **a la retícula de un miembro del esqueleto**, nunca a los 6
raíles de panel: la trasera a trasero bajo y trasero alto (5 M3 cada uno),
la tapa del valle a la bahía (5 M3 a su propia retícula) **y además** con
sus dos pestañas a la placa del valle (2 M3 más, ruling R3 — la banda no
depende solo de la retícula). La tapa de remate está en esta lista hasta el
2026-08-27; no existe desde entonces (la meseta pasó a ser el ala del
miembro trasero alto). Los miembros dejaron de ser perfil 2020 comprado el
2026-08-27; son canal de chapa propio con brida de extremo. **La tabla no
está en esta lista**: no cuelga de nada — el
marco se le apoya encima y su fijación es otra cosa (ranuras alargadas, ver el
BOM). Los
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
**acrílico** (piel, sin cargar), también aislante: la conclusión no cambia,
aunque la razón de fondo sí — ahora los paneles son PCB de aluminio
atornillados a los raíles de panel (Z-Rails de Tiptop), no piezas sueltas
sobre una estructura sin más.

**Lo que NO se puede asumir sin medir**: los paneles de aluminio se
atornillan a los Z-Rails, que sí son metal — y un raíl corrido *podría*
unir eléctricamente entre sí los paneles de una misma cara, sin necesidad
de cable. Pero el Z-Rail casi siempre viene anodizado de fábrica, y el
anodizado es aislante. **La conductividad de los raíles no está
confirmada** (Principio I de la constitución). Medición pendiente,
nombrada: continuidad panel↔panel con miliohmetro sobre el Z-Rail real,
anodizado incluido — sobre la pieza física, no sobre el catálogo.

**El anillo tiene su propio punto de bonding, y es un requisito aparte.**
Desde el 2026-08-28 el anillo se anodiza satinado, y el anodizado también lo
deja aislante — así que va **enmascarado un punto antes de anodizar**, en la
cara interior, **uno por anillo** (dos en total), para que quede metal
desnudo donde enganchar un cable de tierra si algún día algo estructural lo
necesita. Es una precaución de acabado, no un sustituto del bonding por
panel de arriba: el requisito de §13 sigue siendo uno independiente por
panel, y el punto del anillo no lo reemplaza.

**Prohibido leer esta sección como "los largueros bondan los paneles, el
cable sobra"**. Eso no está confirmado, y aunque se confirmara, el bonding
panel a panel de §13 sigue siendo el requisito: es la posición segura y no
depende de esa medición. El SAM17 lleva entrada IEC C14 — es un aparato
Clase I, así que toda parte metálica que el usuario pueda tocar llega a
tierra de protección por un cable verificable, nunca por suposición. Omitir
un cable asumiendo continuidad por el riel es riesgo de choque eléctrico.

## Orden de ensamblaje

**EL ORDEN CAMBIÓ OTRA VEZ EL 2026-08-28, y el cambio es en los primeros
pasos.** La costilla dejó de ser chapa plegada y pasó a ser un anillo
mecanizado sin un solo agujero pasante: todo lo que antes entraba "a la
costilla" ahora entra a una placa, a una brida o a una rosca ciega del
anillo, y hay un orden obligado entre esas dos piezas (R1) que no existía
antes. El acrílico sigue siendo lo último que se mete, porque sigue sin
sostener nada — pero ahora entra ANTES que los clips, no después de nada.

1. **La tabla** — apoyada plana sobre la mesa, cara buena arriba. Es la base de
   todo lo demás. **No atornillar nada todavía.**
2. **Cada Z-Rail a su placa de anclaje, por fuera** — el M4 rosca en el propio
   riel (viene taladrado a 3.3 de fábrica) y su cabeza queda alojada en el
   cajeado de la placa, del lado que después mira al anillo. **Es el primer
   paso de R1**: sin el riel puesto, después no hay cómo apretar la placa
   contra el anillo — la cabeza tiene que quedar tapada primero.
3. **Las placas al anillo, desde dentro** — los dos anillos de pie sobre la
   tabla, y cada placa (ya con su riel puesto) entra por la cara interior con
   sus roscas ciegas M4. **Segundo paso de R1: al revés no se puede
   apretar.**
4. **Los miembros** — trasero bajo, trasero alto y bahía, con la brida de
   extremo de cada punta a rosca ciega en el anillo (M4). Meter aquí las
   **17 tuercas T M3** de las planchas: con tuercas de inserción lateral se
   pueden añadir después, con las de deslizar no.
5. **El marco a la tabla** — 2 filas de 3 M5 a rosca ciega en el canto
   inferior de cada anillo (una fila por anillo). **Empezar por el REDONDO del
   medio de cada fila** y apretarlo a tope; los dos de ranura se aprietan
   después y **no se pasan de apriete**: tienen que poder deslizar cuando la
   madera se mueva. Un tornillo de ranura apretado a tope es un tornillo
   redondo, y ahí se acabó la ranura.
6. **Chasis del PSU** — su pared trasera **cuelga** de la ranura interior de
   `base trasera`, 2 M5 con separador de 3 mm; la delantera **apoya en la
   tabla**. Entre la chapa del toroide y la madera quedan 2 mm de aire, que es
   de lo que va el #106. Va aquí y no más tarde porque después el valle y los
   paneles cierran el piso por arriba.
7. **Tapa del valle** — 5 M3 a los miembros **y las dos pestañas a la placa
   del valle** (no al anillo: su rosca no cabe en la franja de 14 mm — ruling
   R3). Es de **aluminio de 3 mm**: no lleva film protector ni las
   precauciones del PMMA, y su apriete no está limitado por el craquelado.
8. **Electricidad y bonding** — bloque IEC fijo, espárrago junto al PSU.
9. **Trasera** — UNA plancha de 8 mm, EMPOTRADA, 10 M3 a tuerca T en las dos
   filas de los miembros traseros, **a 1.0 N·m con arandela d16 y rosca
   SECA**. Va después de los miembros porque la tuerca T vive dentro de la
   ranura. **ATENCIÓN A LA CARA**: el cajeado de KONDOR va en la cara
   EXTERIOR. Montada al revés, el relieve queda mirando al interior y la
   palabra se lee invertida.
10. **Las escuadras de la trasera** — recién montada la trasera, un angular
    por costado atornillado a ELLA (nunca al anillo) con 3 M3 pasantes,
    cabeza fuera y tuerca dentro. Van aquí y no antes porque no tienen nada
    a qué atornillarse hasta que la trasera está puesta, y van aquí y no
    después porque su ala tiene que estar lista para topar el costado
    cuando entre.
11. **Los costados** — los dos de acrílico, **sin un solo tornillo**: entran
    por detrás y asientan en el rebaje del anillo, sobre la junta de EPDM de
    asiento. El labio del anillo los sostiene hacia fuera por todo el
    perímetro; hacia dentro, por ahora, quedan sueltos de las placas, los
    miembros y la escuadra — **todavía no hay clip**.
12. **Los clips de retención — AL FINAL, tras el acrílico, nunca antes.** Dos
    por costado, en el tramo del suelo, un M4 ciego al anillo por clip. Es el
    único apoyo hacia dentro que se monta DESPUÉS del costado en vez de
    antes: el clip muerde el acrílico por delante, así que si va antes no
    hay hueco donde meter el costado.
13. **Paticas y paneles** — las 4 paticas **a la tabla, por debajo**, y paneles
    ciegos en todo hueco de las dos filas, que con una tapa abierta son lo
    único que ata sus dos raíles.
14. **Quitar el film protector** — al final, no al recibir. El acrílico llega
    con las dos caras protegidas de fábrica, y es durante el MONTAJE cuando se
    raya: al deslizarlo por la mesa, al apoyar una herramienta, al girar una
    pieza sobre otra. El film es lo único que lo evita, y solo sirve si sigue
    puesto.

**Ya no hay «Tapa de remate».** Hasta el 2026-08-27 era el paso 11: 5 M3 a
la retícula del miembro de remate trasero. Esa pieza (`remate_sup`,
`remate_sup_2d`) no existe desde entonces — la meseta del techo es el ala
del propio miembro trasero alto — y se borró del `.scad` en el fix round 1
de esta tarea.

El orden importa en **seis** sitios, dos de ellos nuevos el 2026-08-28:
**el riel va a la placa antes que la placa al anillo (R1)**, porque la cabeza
del M4 se tapa desde fuera y después no hay acceso; las planchas no se
pueden atornillar antes que sus miembros (la tuerca T vive en la ranura del
canal); **el tornillo redondo del medio de la tabla va antes que los de
ranura**, o el marco queda referido a una punta; **la escuadra va después de
la trasera**, porque se atornilla a ella; **los costados siguen yendo casi
al final** (2026-08-27), porque no sostienen nada y son la pieza que se
raya; y **los clips van después de los costados**, no antes — es el paso
nuevo, porque muerden el acrílico por delante y sin el costado puesto no
tienen qué morder. Hubo un séptimo que ya no existe: la pestaña de remate
quedaba irreversible una vez pegada. Todo el case se desmonta.

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
- [x] **Esqueleto de aluminio** (2026-08-26/27, histórico): las 2 costillas de
      chapa plegada, el costado bajado a piel sin un solo taladro, `base
      delantera` retirada y el suelo pasado a tabla de madera.
- [x] **Costilla de pletina mecanizada** (2026-08-28, sustituye a la de arriba):
      la costilla deja de plegarse y pasa a ser un **anillo fresado de 14 mm**,
      una pieza por lado, con rebaje coplanar para el costado, chaflán 1.5 × 45°
      y roscas ciegas en vez de tornillo pasante. El acrílico sigue **sin un
      solo taladro**, ahora retenido por el labio del rebaje, 3 placas, 2 clips
      y la escuadra de la trasera por costado. Vano libre del costado: de
      **119.0 mm** (acrílico portante, sin esqueleto) a 65.2 mm con la
      costilla de chapa plegada (rev. 21) a 95.5 mm al pasar a pletina sola
      (rev. 22 — el anillo es más grueso pero pierde el canto trasero que
      antes cubría el vano de otra forma) y de vuelta a **65.0 mm** con la
      escuadra de la trasera puesta. Flecha con 200 N: 0.38 → 0.11 → 0.24 →
      **0.11 mm**
- [x] Plantilla de panel KiCad
- [x] **Vistas de la BAHIA INFERIOR** (`renders/render_bahia.py`, 2026-08-27):
      la tabla con el chasis del PSU encima, en planta, tres cuartos y rasante.
      Es el único sitio del case cuyo interior es una **decisión** y no una
      consecuencia, y no se ve en ninguna vista del conjunto: los paneles y la
      tapa del valle lo tapan entero. Importa tres ensamblados —madera,
      aluminio y acero— porque pintarlos igual pierde lo que la vista enseña
- [x] **Render del conjunto**, regenerado por última vez el 2026-08-28 con el
      anillo mecanizado y la escuadra de la trasera puestos (commit `2e46ff8`
      y su ronda de arreglos). Los anteriores están en `renders/viejos/`,
      ordenados por fecha. Dos vistas: frontal
      ([`renders/sam17-case.png`](renders/sam17-case.png)) y trasera
      ([`renders/sam17-case-trasera.png`](renders/sam17-case-trasera.png)).
      La trasera es la que importa: muestra las tres ondas — sierra, triángulo
      y cuadrada, las tres formas del VCO — que son la firma visual del case,
      la rejilla de entrada de aire con el IEC embebido, y las tres cabezas de
      M3 por costado de la escuadra nueva. El acrílico deja verse un poco más
      cálido junto al canto trasero, donde el ala de la escuadra le devuelve
      luz por detrás — es translúcido, así que lo que hay detrás se nota
- [ ] **Especie y humedad de la tabla** — las cuentas van contra E = 11 000
      MPa y es supuesto declarado (bloquea el pedido de carpintería)
- [ ] **Pesar el chasis del PSU** — los 200 N del suelo son `carga_mano`
      heredado del costado, y el modo real es el peso del chasis. De ese
      supuesto cuelgan los 18 mm de tabla
- [ ] Cupón cortado y kerf registrado (bloquea el corte de planchas)
- [ ] **Cupón del anillo** (100 mm del perfil, chaflán y anodizado) cortado y
      comparado contra la foto de referencia — las cotas de la cara vista
      (chaflán, rebaje, rehundido) son ESTIMADO hasta que esto cierre; bloquea
      el corte de los dos anillos completos (PLIEGO §6.1)
- [ ] Planchas cortadas y ensayo de ensamblaje
