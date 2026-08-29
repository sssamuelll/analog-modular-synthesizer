# Case SAM17 — consola de dos pisos, esqueleto de aluminio

> **2026-08-29 por la noche: cinco piezas en cuestión, cuatro que quedan.**
> Samuel puso en cuestión `clips_costado`, `escuadras_trasera`,
> `marcos_trasera`, `miembro_alto` y `miembro_bajo` «al mejor estilo japonés»:
> una pieza se queda solo si hace un trabajo que ninguna vecina puede hacer.
> Con esa vara: **las tres placas de anclaje, los dos clips y la escuadra de
> cada costado son UN marco de la ventana** (`marco_ventana`, pletina de 6
> con el contorno de la ventana, corrida por los siete tramos: ata los seis
> rieles y retiene el acrílico hacia dentro por todo el perímetro); **los dos
> marcos de la trasera desaparecen** porque la meseta llega al plano trasero
> y dobla 24 hacia abajo — la banda vista ES el alma del miembro alto, el
> techo es una chapa del pico al canto sin costura —; **el miembro bajo es el
> `talon`**, un ángulo sobre la tabla como la nariz, sin bridas; la trasera
> va **dentro** de las dos bandas y sale por abajo; y el chasis del PSU se
> atornilla **a la tabla** (sus dos M5 apuntaban a la ranura de un 2020
> muerto el 27-08). 16 piezas → 4, 73 tornillos → 64, 16 cabezas atrás → 10
> sobre metal, 12 roscas por anillo (eran 16). Lo que cuesta: 0.35 kg, la
> trasera ya no sale por atrás, la banda mide 24 y no 20 para que la L se
> sostenga sola. Todo en
> [`../docs/superpowers/specs/2026-08-29-marco-ventana-banda-estructural-design.md`](../docs/superpowers/specs/2026-08-29-marco-ventana-banda-estructural-design.md).
> **Y una regla que el marco de la mañana rompía**: nada fijo a distancia
> fija delante de un acrílico de ±1.2 (`guarda_trasera_dentro()`).

> **2026-08-29, tres notas de Samuel sobre el aluminio, mirando el case en
> Blender.** (1) **La bahía se va**: en el valle solo van los dos Z-Rails 1U,
> arrimados al frente de su ventana; el interior queda abierto para los tiles.
> (2) **La nariz es recta**: chaflán a 45° de 6 mm abajo, frente vertical de
> 13, y una banda nueva de chapa de 1.5 — la **`nariz`** — que cierra el frente
> de la tabla al panel, atornillada a la tabla desde dentro. (3) **La meseta
> llega al pico** (`prof_sup` 27.5 → 40.5, muere `inset_remate_frente`) y dobla
> 4 mm sobre la cara de arriba: el riel-eje deja de asomar. Y una regla nueva
> para las esquinas del anillo que llevan chapa encima: `radio_chapa` = 4.5, el
> radio exterior del doblez. Todo en
> [`../docs/superpowers/specs/2026-08-29-nariz-recta-valle-limpio-design.md`](../docs/superpowers/specs/2026-08-29-nariz-recta-valle-limpio-design.md).
> Lo que quedó abierto y declarado: la **banda del valle no tiene apoyo**
> (`guarda_valle()` lo imprime como HUECO: fluye a 27 N) — lo tenía la spec del
> 28-08 como párrafo y ahora es puerta.
>
> Para señalar una pieza sin adivinar: `renders/piezas.py` arma
> `build/sam17-piezas.blend` con **cada pieza como objeto con el nombre del
> repo** (`nariz`, `miembro_alto`, `tapa_valle`...). Clic en la pieza, nombre en
> el Outliner.

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

Spec: [`docs/superpowers/specs/2026-08-15-case-design.md`](../docs/superpowers/specs/2026-08-15-case-design.md) (rev. 25)
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
| ancho útil entre anillos | **540.62 mm** = `largo_riel` + `hol_riel` + 2 × `t_placa` (donde van rieles y miembros; era 528.32 antes del marco de la ventana, que hereda `t_placa`) |

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

**Y desde el 2026-08-29 la punta ya no es redonda.** Lo de arriba sobre «la
punta redondeada se come `alto_frontal/2`» es historia: `radio_punta` murió y la
esquina de abajo-delante lleva un **chaflán a 45° de `chaflan_nariz` = 6** y un
frente vertical de 13, con las esquinas al radio de la chapa (`radio_chapa` =
4.5). Encima va la **`nariz`**: chapa de 1.5 doblada sobre esa esquina — pie de
18 sobre la tabla, chaflán, frente y 10.27 mm subiendo por la cara de abajo
hasta justo debajo de la placa de anclaje, que se retira 9 mm para dejarle
sitio (`retiro_placa_inf`) — y atornillada a la **tabla** desde dentro con tres
M4. Se para debajo de la cara del riel porque la fila de abajo es tapa y al
abrir la esquina del riel del frente sale por la cara en s = 12.8: quedan 2.2
mm de aire más los 2 del labio del riel bajo el panel. Lo mide `guarda_nariz()`.

**La punta de arriba es cuadrada** (2026-08-21). El techo lleva una meseta de
`marco_remate` = **50 mm** rematada por dos quiebres de 2 mm, en vez de la
cúpula que salía antes. Fue 34 unas horas: subió a 42 cuando la meseta tuvo
que alojar el larguero del remate trasero (abajo). Son **dos** parámetros y no uno: los vértices 4 y 5
dejaron de compartir `radio_punta` —que va sobredimensionado a propósito y se
recorta a lo que quepa en la arista, o sea a `marco_remate/2`— y estrenan
`radio_remate` = 2. Subir solo el marco **engorda** el round en vez de
cuadrarlo: de 9 mm de tangente a 17.

**`radio_remate` murió el 2026-08-29.** Las dos esquinas del techo llevan
`radio_chapa` = 4.5, el radio exterior del doblez de la chapa que las cubre —
el retorno de la meseta delante, el marco de la trasera detrás. Una esquina
viva del anillo bajo un doblez a 90° asomaba 1.9 mm por fuera de la chapa.

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

Lo que se pagó entonces: `prof_sup` bajó de 29 a 27.5 para no tocar el inset,
«cuyo acantilado está en 12.8». **Superado el mismo día por la tarde:** ese
acantilado era de cuando la meseta era acrílico de 8 apoyado en el riel. Con la
chapa de 1.5 la cara de abajo de la meseta queda a 18.9 del eje y nada de lo
que gira pasa de 16.2 — se corrió `guarda_tapa()` con la meseta en el pico y la
tapa de arriba siguió abriendo 121.5°. Así que **la meseta llega al pico**
(`prof_sup` = **40.5**), `inset_remate_frente` muere y el riel-eje que asomaba
en esos 13 mm queda tapado. Y en el pico la chapa **dobla 4 mm hacia abajo**
por la cara de arriba (`retorno_meseta`): el canto libre de 528 mm deja de
ondular y de leerse como repisa. No puede bajar más: el canto alto del panel
gira con 16.18 de radio y con 4 quedan 0.80 mm radiales de margen
(`guarda_retorno_meseta()`). Línea de sombra sobre el panel: 6 mm (2 de labio
+ 4 de aire).

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

**HISTÓRICO — superado el 2026-08-29** (la meseta llega al pico, ver arriba):
la tapa **no llegaba hasta el pico**: se retiraba `inset_remate_frente` = 13 mm.
Eso no era estética — era lo único que la dejaba abrir **cuando la meseta era
acrílico de 8 apoyado en el riel**. Hasta entonces esta pieza
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
| **ANILLO** (costilla) — pletina de aluminio **FRESADA** t=14, cara vista 20 | **2** | **la pieza portante del case, mecanizada, no plegada** desde el 2026-08-28. Rebaje 6 × 11 por detrás donde asienta el costado, chaflán 1.5 × 45° en las dos aristas de la cara vista, las **seis esquinas a `radio_chapa` = 4.5** (en todas dobla chapa encima desde el 29-08 por la noche). **12 roscas ciegas M4 por anillo** en la cara interior (`taladros_anillo`: 10 del marco de la ventana + 2 de la brida del miembro alto; eran 16 con clips y miembro bajo) + 3 M5 por anillo en el canto inferior para la tabla. Anodizado satinado, punto de bonding enmascarado. Ni casquillo ni junta de 4 mm: el costado asienta en el rebaje sobre una junta de EPDM de 1 mm |
| **MARCO DE LA VENTANA** — pletina t=6, láser | **2** | **una por costado, espejadas** (mismo DXF, cajeado por caras opuestas). El contorno de la ventana del anillo corrido por los **siete tramos**, 26 hacia dentro desde la silueta: sobre las tres filas es exactamente la placa de anclaje de ayer (canto visto de 6, 6 cajeados Ø8 × 2.5 por el lado del anillo, 10 M4 ciegos); en el frente, el suelo, la meseta y la trasera es el tope del acrílico que daban los clips y la escuadra, unificado — pisa 6 mm de acrílico volado por todo el perímetro. Canto exterior retirado 1.65 bajo cada chapa y 11.2 en la trasera (nada fijo delante de un PMMA de ±1.2). Lleva la rosca M3 de la pestaña de la banda y una **muesca** en la esquina trasera-alta sobre la brida del miembro alto. **Orden obligado: el costado en el rebaje ANTES, después los rieles al marco (cabeza en el cajeado), después el marco al anillo desde dentro** |
| Tornillo M4 botón (marco al anillo) | **20** | 10 por costado, a rosca ciega en la franja de 14. Eran los «20 de placa al anillo» que este README llevaba sin itemizar |
| **MIEMBRO ALTO** — chapa 6082-T6 t=1.5 | **1** | **una L**: la **meseta** del techo (50, del pico al plano trasero, con su **retorno** de 4 en el pico) y la **banda vista** de 24 que baja a ras del plano trasero — el techo es una chapa del pico al canto, sin costura. Dos **bridas** de 27 × 14.5 dobladas de la banda, en la cara del anillo, con 2 M4 ciegos cada una. Fue canal de 20 × 24 con un marco de la trasera atornillado encima (mañana del 29-08). Sola, sin la trasera, cede 2.0 mm con 20 kg en el centro de la meseta a 110 MPa (`guarda_miembro_alto()`: por eso la banda mide 24 y no 20); atornillada a la trasera cada 100, décimas |
| **TALÓN** — chapa 6082-T6 t=1.5 | **1** | la banda vista de 24 a ras del plano trasero por **abajo** y un pie de 20 sobre la tabla, con tres M4 a la tabla desde dentro: hace atrás lo que la nariz hace delante. Sustituye al miembro trasero bajo: sin bridas ni rosca en el anillo — su fijación es la tabla, que ya está atada a los dos anillos con seis M5. Desarrollo 540.32 × 40.70 |
| Tornillo M4 avellanado (talón) | **3** | el pie del talón a la **tabla**, desde dentro — mismo herraje que las paticas y la nariz |
| **NARIZ** — chapa 6082-T6 t=1.5 | **1** | la banda del frente: pie de 18 sobre la tabla, chaflán a 45°, frente vertical y 10.27 subiendo por la cara de abajo. Desarrollo **540.32 × 47.38**, tres dobleces (45°, 45°, 35°). Cierra el frente que enseñaba el riel desnudo (2026-08-29) |
| Tornillo M4 avellanado (nariz) | **3** | el pie de la nariz a la **tabla**, desde dentro — mismo herraje que las paticas. Ninguno en la cara vista |
| Z-Rail de Tiptop | **6** | 104 HP (528.32 mm), sección 23.8 × 10. Cuatro forman las dos filas 3U y dos la fila Intellijel 1U. Atornillan al **marco de la ventana**, no directo al anillo |
| Tornillo **M4** para los rieles | **12** | roscan en el propio Z-Rail (M4 taladrado a 3.3 de fábrica). Sin tuerca, sin inserto. 4 de hombro (ejes de giro) + 4 moleteados (cierres) + 4 fijos (fila 1U, no giran) |
| Tornillo M4 botón (brida del miembro alto) | **4** | por la punta del miembro alto, a rosca ciega en el anillo. Eran 8 con la brida del miembro bajo, que hoy es talón y va a la tabla. Eran M5 hasta el 2026-08-28: bajan a M4 porque la franja de 14 mm no admite las dos brocas (paso M5 + broca M5) a la vez |
| **JUNTA DE ASIENTO EPDM** t=1 mm | **2** | una por anillo, perfil continuo en el rebaje entre el labio y el costado. Nunca aluminio contra acrílico — no es la junta de 4 mm del apilado viejo, muerta el 2026-08-28 |
| Tornillo M4 + **tuerca remachable** (clinch, PEM S-M4) | **4** | el chasis del PSU a la **tabla**, por el suelo, desde abajo: cabezas bajo la tabla, nada visto por dentro. Colgaba de dos M5 de pared «a la ranura interior de `base trasera`», un 2020 muerto el 27-08 que el modelo siguió dibujando dos días |
| Tornillo **M3 botón** + tuerca + **arandela de nylon** (y d16 del lado del PMMA) | **12** | la trasera a las **dos bandas** (5 a la del miembro alto + 5 a la del talón: cabeza fuera **sobre metal**, tuerca dentro contra el acrílico) + **2 de las pestañas** de la banda del valle **al marco de la ventana** (no al anillo, ruling R3). Son las **diez cabezas que se ven atrás**, ninguna sobre acrílico (los 6 M3 de las escuadras murieron con ellas). **Apriete 1.0 N·m con rosca SECA**. Ver `par_m3` |
| Arandela ANCHA d16 | **14** | 10 bajo las tuercas de la trasera, del lado que muerde acrílico (8.7 MPa, techo 10) + 4 en los ejes de giro. Eran 24 cuando las diez cabezas iban también sobre el PMMA; hoy van sobre la banda. **Los 2 M3 de pestaña no la necesitan**: aprietan aluminio contra aluminio |
| Belleville M4 | 4 | precarga de los ejes: ~800 N dan 3.84 N·m de fricción, 1.5× el par de la tapa |
| **Chapa de aluminio t=3 mm** — banda delantera del valle | **1** | vuelo delantero liso, desarrollo 572.00 × 18.30, con pestaña de 21 mm doblada en cada punta, atornillada al **marco de la ventana** con un M3 (no al anillo desde el 2026-08-28). Aleación recomendada, no obligatoria: 5754 H22 pasa a 130 MPa con margen (48.8 MPa real, `guarda_valle()`). Va al taller de CHAPA — sin recocido, sin diamantado, sin chaflán: eso es del PMMA |
| **TABLA de madera maciza t=18 mm** | **1** | el suelo interior y el zócalo, una sola pieza, **588.62 × 327.41**. 2 filas de 3 M5 a **rosca ciega en el canto inferior del anillo** (una fila por anillo), uno redondo por fila (punto fijo) y dos en ranura de 10.5. Y **catorce taladros pasantes de 4.5**: 4 de las paticas, 3 de la nariz, 3 del talón y 4 del chasis (`guarda_zocalo()` los censa) |
| Plancha acrílico t=8 mm | **3** | 2 costados + **trasera** (540.32 × 253.03, con las ondas, la rejilla de entrada de aire y KONDOR). Los **costados sin un solo taladro**: asientan en el rebaje del anillo, retenidos por el labio hacia fuera y por el marco de la ventana hacia dentro, por los siete tramos. La **trasera lleva 10 taladros M3** (eran 16 con las escuadras) **y dos muescas de esquina** de 2 × 15 arriba, por donde le pasa la brida del miembro alto; va DENTRO de las dos bandas y sale por abajo |
| Patica de goma con casquillo roscado | 4 | EPDM o NBR, Shore 45–55 A, **d20 × 10**. Se atornillan **a la tabla**, no al acrílico. **Se exige la curva carga-deformación: ≥ 0.25 mm de flecha con 22.8 N** — por debajo la pata AMPLIFICA los 100 Hz del toroide en vez de aislarlos (`flecha_pie`). Casquillo roscado moldeado: se atornilla, **no se pega** |

**Total de tornillos del case: 64** — 12 M4 de raíl + 20 M4 de marco al
anillo + 4 M4 de brida + 3 M4 de la nariz + 3 M4 del talón + 4 M4 del chasis
+ 12 M3 de plancha + 6 M5 de la tabla. Eran 73 la mañana del 2026-08-29: −4
de brida (el miembro bajo), −6 M3 de escuadra, −4 M4 de clip, −2 M5 del
chasis, +3 del talón y +4 del chasis; y los 20 M4 de placa al anillo, que
este README llevaba «sin itemizar», son ahora los del marco de la ventana y
están en la tabla.

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
atornillan **a una banda del esqueleto**, nunca a los 6 raíles de panel: la
trasera a la banda del miembro alto y a la del talón (5 M3 cada una, a media
banda, desde el 2026-08-29 por la noche; antes a la retícula de los dos
miembros), y la banda del valle **solo** con sus dos pestañas al marco de la
ventana (2 M3, ruling R3) — hasta el 2026-08-29 este párrafo le contaba 5 M3
«a la bahía» que no tenía, y la bahía ya no existe; por eso `guarda_valle()`
la declara HUECO hasta que apoye en algo. La tapa de remate está en esta lista
hasta el 2026-08-27; no existe desde entonces (la meseta pasó a ser el ala del
miembro trasero alto). Los miembros dejaron de ser perfil 2020 comprado el
2026-08-27; el alto es una L con brida de extremo y el bajo es el talón, que
va a la tabla. **La tabla no
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

**EL ORDEN CAMBIÓ OTRA VEZ EL 2026-08-29 POR LA NOCHE, y esta vez arregla
uno que estaba mal escrito.** Hasta hoy este README metía los costados
DESPUÉS de las placas y los clips, y así no entra un costado en su rebaje:
las placas ya pisaban 6 mm de acrílico. Con el marco de la ventana el orden
es el único posible: **el costado en el rebaje ANTES que el marco**, porque
el marco lo pisa. Y la trasera **entra por abajo** antes que la tabla y el
talón, porque la banda que la tapa es estructura y no se quita.

1. **Los dos anillos, tumbados con la cara vista abajo, cada uno con su
   costado asentado en el rebaje** sobre la junta de EPDM. El costado sigue
   siendo la pieza que se raya: entra con el film puesto y no se le quita
   hasta el final. **No hay tornillo en este paso**: el labio lo sostiene.
2. **Los seis Z-Rails al marco A, por su cara de anillo** — el M4 rosca en el
   propio riel (viene taladrado a 3.3 de fábrica) y su cabeza queda alojada
   en el cajeado del marco, del lado que después mira al anillo. **Es el
   primer paso de R1**: sin el riel puesto, después no hay cómo apretar el
   marco contra el anillo — la cabeza tiene que quedar tapada primero.
3. **El marco A al anillo A, desde dentro** — con el costado ya en su rebaje,
   el marco baja sobre la cara interior con sus diez M4 a rosca ciega y pisa
   6 mm de acrílico por los siete tramos. **Segundo paso de R1: al revés no
   se puede apretar, y con el marco puesto el costado no entra.**
4. **El marco B a las otras puntas de los rieles** (seis M4 por su cara de
   anillo, con el marco todavía suelto), **el costado B en el anillo B**, y
   el anillo B sobre el marco B: sus diez M4 se aprietan desde dentro por el
   frente abierto. Los dos anillos quedan de pie, atados por los seis
   rieles.
5. **El miembro alto** — la meseta del pico al plano trasero y la banda
   bajando a ras: sus dos bridas a las roscas ciegas de la franja de la
   meseta (2 M4 cada una), bajo la muesca del marco.
6. **La trasera, DESDE ABAJO** — sube contra la cara interior de la banda del
   miembro alto hasta hol_piel bajo la meseta, con sus dos muescas de
   esquina librando las bridas, y se atornilla a la banda con sus **5 M3 de
   arriba**: cabeza fuera, sobre metal; tuerca dentro con **arandela de nylon
   y d16 contra el PMMA, a 1.0 N·m y rosca SECA**. **ATENCIÓN A LA CARA**:
   el cajeado de KONDOR va en la cara EXTERIOR. Montada al revés, la palabra
   se lee invertida.
7. **El talón, desde abajo** — el pie bajo el canto de la trasera, la banda
   detrás de sus 24 mm de abajo, y los **5 M3 de abajo** a la trasera igual
   que arriba. Todavía no va a la tabla: no hay tabla.
8. **La tabla** — el conjunto boca abajo sobre ella: 2 filas de 3 M5 a rosca
   ciega en el canto inferior de cada anillo. **Empezar por el REDONDO del
   medio de cada fila** y apretarlo a tope; los dos de ranura se aprietan
   después y **no se pasan de apriete**: tienen que poder deslizar cuando la
   madera se mueva. Después los **3 M4 del pie del talón**, desde dentro.
9. **La nariz** — entra por el frente entre los dos anillos, el pie sobre la
   tabla, y sus **3 M4 desde dentro**. Ningún tornillo en la cara vista.
10. **Chasis del PSU** — sobre la tabla, arrimado al pie del talón (3 mm de
    aire), y con el conjunto boca abajo sus **4 M4 desde debajo de la tabla**
    a las tuercas remachables de su suelo. Va aquí y no más tarde porque
    después el valle y los paneles cierran el piso por arriba.
11. **Tapa del valle** — las dos pestañas al marco de la ventana (2 M3,
    ruling R3). Es de **aluminio de 3 mm**: no lleva film ni las precauciones
    del PMMA.
12. **Electricidad y bonding** — bloque IEC fijo (su pieza va al pie del
    talón o a la tabla, #130), espárrago junto al PSU.
13. **Paticas y paneles** — las 4 paticas **a la tabla, por debajo** (las dos
    traseras bajo el centro del pie del talón), y paneles ciegos en todo
    hueco de las dos filas, que con una tapa abierta son lo único que ata sus
    dos raíles.
14. **Quitar el film protector** — al final, no al recibir. El acrílico llega
    con las dos caras protegidas de fábrica, y es durante el MONTAJE cuando se
    raya: al deslizarlo por la mesa, al apoyar una herramienta, al girar una
    pieza sobre otra. El film es lo único que lo evita, y solo sirve si sigue
    puesto.

**Ya no hay «Tapa de remate», ni placas, ni clips, ni escuadras, ni marcos
de la trasera.** Las placas, los clips y las escuadras son el marco de la
ventana (paso 3); los marcos de la trasera son la banda del miembro alto y
la del talón (pasos 5 y 7); la tapa de remate (`remate_sup`) no existe desde
el 2026-08-27 — la meseta es el ala del propio miembro alto.

El orden importa en **cinco** sitios: **el costado va antes que el marco**
(el marco lo pisa — es el que este README tenía al revés); **el riel va al
marco antes que el marco al anillo (R1)**, porque la cabeza del M4 se tapa
desde fuera y después no hay acceso; **la trasera va antes que el talón y
que la tabla**, porque entra y sale por abajo; **el tornillo redondo del
medio de la tabla va antes que los de ranura**, o el marco queda referido a
una punta; y **el chasis va a la tabla con el conjunto boca abajo**, porque
sus tornillos entran por debajo. Todo el case se desmonta: la trasera, por
abajo (tabla, talón, cinco M3) — es el precio de que la banda que la tapa sea
estructura y no un embellecedor.

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
      solo taladro**, retenido por el labio del rebaje y, desde el 29-08 por
      la noche, por el **marco de la ventana** en los siete tramos. Vano libre
      del costado: de **119.0 mm** (acrílico portante, sin esqueleto) a 65.2 mm
      con la costilla de chapa plegada (rev. 21) a 95.5 mm al pasar a pletina
      sola (rev. 22) a 65.0 mm con la escuadra de la trasera y a **62.9 mm**
      con el marco de la ventana. Flecha con 200 N: 0.38 → 0.11 → 0.24 → 0.11
      → **0.11 mm**
- [x] **El marco de la ventana y la banda estructural** (2026-08-29, noche):
      placas, clips y escuadras → un marco por costado; marcos de la trasera →
      la banda del miembro alto y el talón; la trasera dentro de las bandas;
      el chasis a la tabla. Puertas nuevas: `guarda_marco_ventana()`,
      `guarda_miembro_alto()`, `guarda_talon()`, `guarda_trasera_dentro()`,
      `taladros_marco_ventana()`, `taladros_talon()`. La tapa de arriba pasa
      de abrir 121.5° a **180°**: el canal que la paraba ya no existe
- [x] Plantilla de panel KiCad
- [x] **Vistas de la BAHIA INFERIOR** (`renders/render_bahia.py`, 2026-08-27):
      la tabla con el chasis del PSU encima, en planta, tres cuartos y rasante.
      Es el único sitio del case cuyo interior es una **decisión** y no una
      consecuencia, y no se ve en ninguna vista del conjunto: los paneles y la
      tapa del valle lo tapan entero. Importa tres ensamblados —madera,
      aluminio y acero— porque pintarlos igual pierde lo que la vista enseña
- [x] **Render del conjunto**, regenerado por última vez el 2026-08-29 por
      la noche con el marco de la ventana, el miembro alto en L y el talón.
      Los anteriores están en `renders/viejos/`, ordenados por fecha. Dos
      vistas: frontal ([`renders/sam17-case.png`](renders/sam17-case.png)) y
      trasera ([`renders/sam17-case-trasera.png`](renders/sam17-case-trasera.png)).
      La trasera muestra las dos bandas de 24 a ras del plano trasero con sus
      diez cabezas sobre metal, el acrílico rehundido con las ondas y la
      rejilla, y ninguna cabeza sobre el PMMA. A través del costado se lee
      una sombra uniforme de 6 alrededor de la ventana: es el marco
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
