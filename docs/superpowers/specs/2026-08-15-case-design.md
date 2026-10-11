# SAM17 — Diseño del case (consola de dos pisos, esqueleto de aluminio)

**Fecha:** 2026-08-15
**Estado:** aprobado en diseño (rev. 28), pendiente de plan de implementación
**Sustituye a:** formato de cajón de la tesis (madera 950 × 440 × 100–200 mm,
paneles galvanizados pintados) descrito en
[`docs/modules/08-case-panels.md`](../../modules/08-case-panels.md).
**Diseño de entrada:**
[`docs/architecture-poly.md`](../../architecture-poly.md) (4 voces con mandos
compartidos y circuitos replicados; dos caminos de señal; patch bay
normalizado); pivote de cómputo del PR #30 (el instrumento entero vive en un
RP2350, la computadora es externa y opcional); spec de la fuente v2
([`2026-08-16-psu-v2-goat-design.md`](2026-08-16-psu-v2-goat-design.md)).
**Render de intención aprobado:**
[`case/renders/propuesta-diseno-2026-08-16.png`](../../../case/renders/propuesta-diseno-2026-08-16.png)
(board del departamento de diseño, 2026-08-16 — manda sobre proporciones y
lenguaje visual).
**Gobernada por:** [`.specify/memory/constitution.md`](../../../.specify/memory/constitution.md).

> **Decisión vigente:** las tres caras de panel son fijas y desmontables por
> tornillos. No hay bisagras, ejes de fricción, barridos ni requisitos de
> ángulo de apertura. Esta decisión prevalece sobre las referencias históricas
> a tapas practicables que permanecen en la cronología de revisiones.

> Historial de revisiones — **rev. 1**: consola inclinada de un piso, cheeks
> de madera, finger joints cementados, pantalla táctil de 7". **rev. 2**: todo
> acrílico, dos pisos, sándwich modernista con standoffs; muere la pantalla
> (interfaz = app web servida por el Pi). **rev. 3**: el cerebro pasa de
> Raspberry Pi 3B+ a **RP2350 con la computadora FUERA** — muere la app web
> servida por el Pi y el compañero pasa a ser un **plugin VST/CLAP** en la
> computadora del usuario; la fuente v2 fija los dominios de alimentación (y
> prevé WS2812); los ángulos quedan **medidos desde la vertical**, como los
> interpretó el board de diseño aprobado. **rev. 4** (2026-08-17/18): el
> panel pasa a **3U de EUROrack** (128.5 mm, 1 HP) y se compran Z-Rails de
> Tiptop de 104 HP — muere el formato propio de 190 mm y con él la
> proporción del board; el proceso pasa de **láser a fresado CNC** y `kerf`
> a 0; el zócalo se elimina; la pestaña de remate pasa a **junta pegada**;
> la bandeja de base sube a 8 mm y se vuelve portante. **rev. 5**
> (2026-08-21): la punta de arriba se lee **cuadrada** — `marco_remate` sube
> de 18 a 34 y los dos vértices del techo estrenan `radio_remate` = 2 en vez
> de compartir `radio_punta` —, el fondo crece 16 mm, y con eso la tapa de la
> fila de arriba pasa a abrir 180°. Muere de paso la idea de doblar la piel
> superior en cascada: no hace falta doblar nada. **rev. 6** (2026-08-21): la
> trasera deja de flotar y se **empotra** —mueren la junta de sombra y los 12
> separadores—, y entra el **octavo larguero** en la arista trasera-superior,
> que le da a la tapa de remate a qué atornillarse: se acabó la única junta
> pegada del case. `marco_remate` 34 → 42 y el fondo 291.2 → 299.2, que es lo
> que pide el barrido del Z-Rail para que la tapa siga abriendo 180°.
> **rev. 7** (2026-08-21): «evitar la complejidad» — muere la **bandeja de
> entrepiso** (su papel de barrera ya lo hace el chasis de acero) y las dos
> pieles se funden en **una sola plancha de 8 mm** atornillada a los cuatro
> largueros traseros. El case pierde dos planchas y gana rigidez en la trasera.
> **rev. 8** (2026-08-21): el acrílico de la trasera **llega hasta arriba** — el
> larguero de remate se retira `t_piel` para que le pase por delante, con lo que
> los CINCO largueros traseros comparten X y la trasera gana su quinta fila de
> tornillos. `marco_remate` 42 -> 50 y el fondo 299.2 -> 307.2, que es lo que
> pide el barrido del Z-Rail para conservar los 3.04 mm de margen.
> **rev. 9** (2026-08-21): junto a la pared trasera quedan **DOS largueros, no
> cinco**. *Entrepiso trasero*, *repisa* y *remate superior* nacieron cada uno
> por una pieza —la bandeja de entrepiso, la piel superior, la tira de remate
> pegada de canto— y las tres murieron en rev. 6-7: seguían solo como filas de
> tornillo de la trasera. Una plancha continua de 8 mm atornillada arriba y
> abajo ya es el alma de cortante de esa cara. Vano libre 211.73 mm, flecha
> 0.15 mm con 50 N en el centro. El case baja de 8 a **5 largueros** y de 69 a
> **48 tornillos**.
> **rev. 10** (2026-08-21): **el suelo cierra**. La bandeja de base llegaba solo
> hasta el larguero delantero y dejaba 37.96 mm de suelo abierto — que era la
> entrada de aire. Ahora vuela hasta donde muere la curva de la esquina (x=9.49)
> y lo único abierto por abajo es el propio redondeo. No salió gratis: el Z-Rail
> de abajo se metía 3.16 mm en el plano del suelo, así que `alto_frontal` 13→19
> e `inset_inf_frente` 14.5→17.5 (van emparejados), y el case pasa a
> **256.18 × 308.94**. La ENTRADA DE AIRE se muda a una rejilla baja en la
> trasera: 8 317 mm² contra los 7 499 de salida del valle, con `guarda_aire()`
> comparando las dos.
> **rev. 11** (2026-08-21): la trasera se queda **solo con sus tres ondas** y la
> entrada de aire vuelve al suelo, dibujada: 51 ranuras en el vuelo de la
> bandeja (3 535 mm² a y=4). Menos área que en la trasera, pero entra 50 mm más
> abajo y el tiro compensa. `guarda_aire()` deja de medir paridad de áreas y
> pasa a medir **salto térmico**: 8.5 K sobre ambiente con 6.33 W contra un
> techo de 15 (`potencia_disipada` y `salto_termico_max`, los dos SUPUESTO). El
> hueco del IEC sube de y=22 a y=33, centrado en la banda libre entre la fila de
> M3 y la onda — estaba a 3.5 mm de la arandela de un tornillo.
> **rev. 12** (2026-08-21): **el chasis del PSU deja de ir centrado**. Medido a
> lo largo del panel, lo que le comía fondo a los módulos de la fila de abajo no
> era el larguero delantero sino el chasis: 18.6 mm de fondo libre a media
> altura. Ahora el chasis se pega al larguero trasero y el delantero al chasis,
> los dos a `chasis_holgura_larguero`. Fondo mínimo 18.6 → **34.4 mm**, panel
> útil con módulos de 50 mm de 27 % → **68 %**. El larguero queda a 42.7 mm del
> raíl de panel en vez de a 4.00, y no se retira: sostiene la fila delantera de
> la bandeja. El vuelo crece a 68.85, la rejilla de aire con él, y ΔT baja a
> 4.6 K.
> **rev. 13** (2026-08-21): la entrada de aire **vuelve a la trasera** y se queda.
> En el vuelo de la bandeja se transparentaba: el acrílico naranja es traslúcido
> y el campo de ranuras se veía por el canto inferior. Son 45 ranuras de 40.5 × 4
> (7 128 mm²) en la banda libre entre la fila de M3 y la onda, con el hueco del
> IEC embebido en el campo y 6.98 mm de material alrededor. ΔT 4.6 → **6.5 K**
> contra el techo de 15: eso es lo que cuesta que no se vea. El vuelo del suelo
> queda de plancha maciza.
> **rev. 14** (2026-08-21): la rejilla y las ondas se **separan 14 mm**. Eran 4
> (`vent_puente_min`, el mínimo por fragilidad) y los dos campos se leían como
> uno. Subir la onda sola no servía: el borde de la rejilla estaba derivado de
> ella. Entra `vent_separacion` como cota de dibujo propia y `y_bajas` sube
> 0.32 → 0.37. ΔT 6.5 → 6.6 K.
> **rev. 15** (2026-08-21, **#106**): el chasis del PSU deja de apoyarse en el
> acrílico y **cuelga** de la ranura interior de los dos largueros de base con
> 4 M5 + separador. `chasis_pie` deja de ser separadores (10) y pasa a ser aire
> (2). La caja no cambia de tamaño. El fondo de módulo sube de 34.4 a **38.3 mm**
> —el limitante deja de ser el chasis y pasa a ser la bandeja— y el techo libre
> del piso de abajo de 40.6 a **48.6**. Pide que la chapa de refuerzo y el
> herraje del M6 del toroide vayan POR DENTRO de la caja.
> **rev. 16** (2026-08-24): **los cantos que apoyan contra algo plano dejan de
> abombarse**. La éntasis (`bombeo` = 0.5 mm por cada 100 mm de tramo) curvaba
> hacia fuera todos los tramos rectos del costado, y el canto trasero —el más
> largo que todavía se abombaba, 256.18 mm— **sobresalía 1.197 mm** del plano
> trasero a media altura, enrasando en las puntas. Contra `hol_piel` = 0.15 mm
> de holgura de montaje de la trasera eso es **ocho veces la junta**, y por eso
> la plancha no encajaba a ras. La meseta del techo hacía lo mismo con 0.240 mm
> bajo la tapa de remate. Los dos entran en `sin_bombeo` junto al canto de abajo
> —exento desde el principio por las paticas—, y la regla queda dicha entera:
> **el canto que apoya contra algo plano va recto; el que solo dibuja silueta
> conserva la éntasis**. El costado pasa a medir su envolvente nominal (bbox
> 310.137 × 256.420 → **308.936 × 256.184**, contra 308.94 × 256.18 nominales) y
> de los nueve DXF **solo cambia `costado_2d`**. La mayor flecha que queda son
> 0.779 mm en la cara del panel de abajo, que no apoya contra nada. Se corrigen
> de paso dos comentarios —`params.scad` y `check_dxf.py`— que culpaban al canto
> de abajo («1.7 mm en el canto de abajo») de un abombamiento que no tiene desde
> que está exento: quien se comía la tolerancia era el canto trasero.
> **rev. 17** (2026-08-24): **las dos esquinas del plano trasero pasan a
> esquina viva** (`radio_trasero` = 0). Medido sobre el DXF, el costado se metía
> hacia dentro del plano trasero **14.004 mm en `y` = 0** (vértice fondo-abajo,
> que llevaba `radio_perfil` = 14) y **2.004 mm arriba** (fondo-arriba,
> `radio_remate` = 2). La trasera es un rectángulo de **540.32 × 254.68** (rev. 23; fue
> 528.020 × 248.184) **con
> esquinas vivas** que baja hasta `y` = 0, así que su esquina inferior quedaba
> colgando 14 mm por fuera de la silueta del costado. Ahora el desajuste es
> **0.000 mm** en las dos, y la tapa de remate gana lo mismo arriba. El costado
> baja de 578 a **546 entidades** y el bbox no se mueve.
>
> **Se deroga aquí una regla escrita**, y se deja dicho por qué en vez de
> saltársela: `radio_remate` sostenía «2 y no 0: una esquina viva en acrílico
> colado de 8 mm es donde arranca una fisura». Eso **se mantiene en los vértices
> cóncavos y en las ranuras** —lo sigue vigilando `guarda_fresado()`, cóncavo
> mínimo 54.0 contra fresa de radio 1.5— pero **no se sostenía como regla
> general**, y el propio repo ya lo demostraba: la trasera se corta con sus
> cuatro esquinas vivas en 8 mm desde que se empotró. Lo nuevo no es la
> excepción, es decirla. **Lo que sí se acepta**: una esquina viva convexa en
> PMMA se desportilla si se golpea, y la de fondo-abajo está a ras del suelo. Es
> riesgo de manipulación, no de rotura en carga; si aparece en el prototipo el
> remedio es un chaflán de 0.5 × 45°, no volver al radio.
>
> Muere de paso **`radio_perfil`**: se quedó sin un solo cliente, y su comentario
> llevaba tiempo mintiendo —decía que «manda en el valle» cuando el valle lo
> gobiernan `radio_pico` y `radio_valle`—, así que quien quisiera suavizar el
> valle movía ese número y lo que cambiaba era una esquina trasera.
>
> **rev. 18** (2026-08-24): **el acabado deja de estar implícito**. La revisión
> adversarial destapó que hay nueve DXF y 563 líneas de README y **ningún
> documento que vaya al taller**; entran [`case/PLIEGO.md`](../../../case/PLIEGO.md)
> y [`case/RFQ.md`](../../../case/RFQ.md). Con ellos, tres procesos que no
> aparecían ni una vez en el proyecto: **recocido** (sin él el PMMA fresado
> craquela en meses alrededor de los taladros), **canto diamantado** en los
> ~7.5 m de contorno visible con pulido a llama **prohibido**, y **chaflán
> 0.5 × 45°** en toda arista vista — obligatorio desde que la rev. 17 dejó dos
> esquinas vivas. Los 30 M3 dejan de apretarse «hasta marcar»: **1.0 N·m con
> arandela d16 y rosca seca**, y el número sale de la arandela, no del
> tornillo. Las **paticas pasan a goma**, lo que revierte la nota del
> 2026-08-17 y **devuelve la razón a esta spec**, que nunca dejó de decir
> «pies de goma»; su cota de compra es la flecha (≥0.25 mm bajo 22.8 N),
> porque una goma dura no aisla menos sino que **amplifica** los 100 Hz del
> toroide. Y `kondor_cajeado_2d` entra en `export.ps1`: existía como pieza y
> no se generaba, así que la trasera habría vuelto **sin la marca**. Cuatro
> puertas nuevas — `guarda_chaflan()`, `guarda_apriete()`, `guarda_paticas()`
> y `guarda_kondor()`.
>
> **rev. 19** (2026-08-25): **se retira el larguero de entrepiso delantero** y
> el case baja de 5 largueros a **4** y de 52 tornillos a **50**. Era el único
> del case que no sostenía ninguna plancha —las seis filas de M3 van a base
> delantera, base trasera, valle y remate trasero—, así que ninguna puerta de
> anclaje lo miraba: se podía retirar y quedarse todo en verde. Su trabajo era
> atar los costados a media altura, y a esa **misma altura** (y = 131.58) ya
> está el del valle, 75.14 mm por delante y encima con su tapa. Mismo argumento
> que la rev. 9, aplicado al que quedaba: una barra que no es alma de nada.
> Medido sobre el contorno real de `costado_2d.dxf` como placa circular
> empotrada: el vano libre del costado pasa de 107.9 a **118.9 mm**, la flecha
> con 200 N de 0.31 a **0.38 mm** (techo 0.60, el mismo que la rev. 9 aceptó
> para la trasera) y la tensión bajo la mano de 6.35 a **6.56 MPa** contra los
> 10 de fluencia. **Se acota por flecha y no por tensión**: para agotar los
> 10 MPa el vano tendría que valer 642 mm, más que la pieza entera, porque la
> tensión de una placa empotrada crece con el logaritmo del vano y la flecha
> con el cuadrado — y lo que se nota con la mano es la flecha. Entran
> `carga_mano`, `flecha_costado_max` y la puerta **`guarda_costado()`**, que
> vive en `check_dxf.py` y no en el budget porque mide sobre el contorno y los
> taladros **reales del DXF**. Se corrige de paso un `echo` del BOM que seguía
> pidiendo «patica metálica torneada» ocho meses después de que la rev. 18 las
> pasara a goma. **Lo que NO cubre**: el racking del cajón, que sigue siendo la
> heurística abierta de §11 — y ahora con una barra menos.
>
> **rev. 21** (2026-08-26/27): **el acrílico deja de cargar.** La estructura
> pasa a **dos costillas de chapa de aluminio de 3 mm plegada** y el costado
> baja a piel: se queda **sin un solo taladro**, capturado entre las dos alas de
> la costilla. Todos los tornillos estructurales se mudan al aluminio. Se va
> `base delantera` —la única barra que flotaba en mitad del suelo— y el case
> baja de 4 transversales a 3; las otras tres no se pueden quitar, y por qué
> está medido. El **suelo pasa a ser una tabla de madera maciza de 18 mm bajo el
> marco**, que es a la vez el zócalo: una sola pieza en vez de dos, con
> agujeros alargados porque la madera se mueve y el aluminio no. La tapa del
> valle gana una **pestaña doblada por punta** que la atornilla a las costillas
> y la convierte en diafragma. `ala_costilla` deja de ser supuesto y se fija en
> 24 por lo que le cabe al M4 del Z-Rail. Medido: el vano libre del costado cae
> de 119.0 a **65.2 mm** y su flecha de 0.38 a **0.11**. Diseño completo en
> [`2026-08-26-case-esqueleto-aluminio-design.md`](2026-08-26-case-esqueleto-aluminio-design.md).
> **rev. 20** (2026-08-25): **la tapa del valle pasa de acrílico de 5 mm a
> chapa de ALUMINIO de 3**. Era la plancha más floja del case y a la vez la
> única cara horizontal — donde se apoya quien se levanta, no donde se posa la
> mano al parchear. El número que decide es la proporción en voladizo: mide
> 66.5 mm de fondo y el larguero solo la toca 20, así que **el 70 % de la pieza
> vuela**, 23.24 mm a cada lado. En PMMA de 5, con 200 N repartidos en 50 mm de
> canto de mano, trabajaba a 22.3 MPa contra los 10 de fluencia (#106) y
> **fluía a 90 N**; en aluminio da 62.0 contra un `Rp0.2` de 130 y **fluye a
> 420**. Las otras tres salidas quedan cerradas por medición y no por gusto:
> acrílico de 6 está BLOQUEADO (la tapa invade el barrido y la fila de abajo
> pasa de abrir 180° a 39.5°), un larguero de 30 entra por 0.24 mm —bajo la
> tolerancia de la propia extrusión— y uno de 40 no entra, se pasa 4.76.
> **No rompe el lenguaje visual**, que era la objeción de la rev. 18: los
> paneles ya son PCB de aluminio a los dos lados de esa banda. Entra
> `guarda_valle()`, `t_acrilico` se renombra a **`t_valle`** porque el nombre
> viejo habría mentido sobre el material, y la tapa sale de
> `planchas_acrilico()` para entrar en `assembly_aluminio()`. Muere la única
> línea de BOM de 5 mm: **el cuerpo de acrílico queda con un solo espesor**.
> Y la tapa sale del pliego de acrílico — sin recocido, sin diamantado y sin
> chaflán, que son exigencias del PMMA.
>
> **Aviso sobre el render de intención:** sigue mandando sobre lenguaje
> visual y proporciones *relativas*, pero **sus cotas están superadas**. Se
> dibujó para paneles de 190 mm y un case de 500 × 380 × 350; el case real
> mide **544.32 × 256.18 × 308.94** — superado otra vez en la rev. 22, ver
> abajo.
>
> **rev. 27** (2026-08-30): **techo macizo, salida por el alero y tres chapas
> empotradas**. Techo, nariz y talón quedan rehundidos 1 en un rebaje de
> 4.5 × 3 de la cara interior del anillo; los pies siguen a ras sobre la
> tabla. El techo pierde las 16 ranuras, su labio pasa a 20 y la salida es la
> rendija de 4.0 bajo el alero. El presupuesto térmico usa 9.22 W. La tabla,
> con nariz y talón, entra con el anillo B; el chasis del PSU entra después por
> el frente. Esta revisión sustituye la geometría y el montaje de la rev. 26
> en esos puntos; conserva debajo el razonamiento que llevó a aquella.
>
> **rev. 30** (2026-10-11): **la persiana**. Las dos mejillas de acrílico se
> van y cada costado pasa a ser una placa de aluminio de 6 por fuera del anillo,
> con 47 varillas de 2, sujeta con diez tacos e imanes; todo el aluminio que se
> ve, en negro. La piel orgánica no se hace. El rebaje del anillo se queda
> vacío, y cada anillo gana diez bolsillos por la cara de fuera. Detalle en
> [`2026-10-11-case-persiana-design.md`](2026-10-11-case-persiana-design.md).
>
> **rev. 29** (2026-10-10): **la tabla de la ficha 12** del acta de la piel. Vuela
> 40 por los cuatro lados (`vuelo_zocalo`, era 10) y mide 30 de grueso (`t_base`,
> era 18), con el canto de arriba redondeado R8 (`r_canto_tabla`). Los M5 de la
> tabla se reparten desde ese día en el fondo del cuerpo y no en el de la tabla:
> con el vuelo nuevo habrían pasado solos de 3 a 4 por anillo. Detalle en el
> §13.8 de [`2026-09-05-case-piel-organica-design.md`](2026-09-05-case-piel-organica-design.md).
>
> **rev. 28** (2026-08-31): **Tanda B — fila KONDOR de 55, banda apoyada y
> paneles rehundidos 1.5**. La tercera fila deja de anunciarse como Intellijel:
> mide 55 mm y 49 entre centros; el primer riel queda fijo y el segundo se
> desplaza 15.35. `paso_horizontal` sube 58.47 → 70.82 y el fondo derivado queda
> en **319.76 mm**. La banda se prolonga 2 mm a espesor completo sobre el primer
> KONDOR y apoya mediante una tira anti-ruido de 0.20 nominal comprimida a 0.10;
> `guarda_valle()` deja de publicar el HUECO de 213 mm / 27 N. Los paneles y sus
> rieles se mueven juntos 1.50 hacia dentro; anillo y marco permanecen fijos y
> la tapa inferior abre 63.8° contra 60 mínimos. Diseño completo en
> [`2026-08-31-case-tanda-b-design.md`](2026-08-31-case-tanda-b-design.md).
>
> **rev. 26** (2026-08-29, más noche): **la trasera capturada como las
> mejillas, y el talón como la nariz** — Samuel, mirando el render de la rev.
> 25, en
> [`2026-08-29-trasera-capturada-talon-nariz-design.md`](2026-08-29-trasera-capturada-talon-nariz-design.md).
> **La trasera va DENTRO de un bolsillo fresado en el tramo trasero de cada
> anillo** — labio 3, 6 de hondo, 11 de ancho: los tres números del bolsillo
> del costado, girados — con su cara rehundida 4 sobre junta de EPDM, **sin
> un taladro** (552.32 × 237.18): el bolsillo cerrado por los dos extremos,
> y la plancha entra al montar el segundo anillo, como los costados, con su
> arista de abajo a chaflán de 5.5. Para que quepan los dos bolsillos en la
> franja de 20, en ese tramo el costado entra 3 en vez de 6 y queda una pared
> de 3 entre ambos. **El talón es la nariz de atrás**: P6 a chaflán 6, pie
> de 20, chaflán, labio de 13, tres M4 avellanados y ocho pestañas
> lanzadas que le hacen de tope a la trasera por dentro y son estructura (la
> plancha como placa: 14 MPa sin ellas con la mano al centro, 8.9 con ellas a
> su aire y la mano barrida por lo visible; arriba, 75 mm que pasan de 10,
> declarados). **El techo
> baja con chaflán + labio de 18** (variante
> B, la escogida el 2026-08-30; A era la banda de 24) y sin canal: en una sola chapa el
> labio no puede tapar el canto Y tener retorno, y el bolsillo ya sujeta la
> plancha. 68 tornillos → 58, 10 cabezas atrás → 0, la tapa de arriba sigue
> en 180°. Lo que cuesta: el segundo bolsillo en el mecanizado, la pata
> trasera del marco a 28 (a 26 quedaba a 129 MPa contra 130), y que el
> costado entre 3 atrás.
>
> **rev. 25** (2026-08-29, noche): **el marco de la ventana y la banda
> estructural** — cinco piezas puestas en cuestión por Samuel «al mejor estilo
> japonés», en
> [`2026-08-29-marco-ventana-banda-estructural-design.md`](2026-08-29-marco-ventana-banda-estructural-design.md).
> **Las tres placas de anclaje, los dos clips y la escuadra de cada costado son
> UN marco de la ventana** (`marco_ventana`, pletina de 6 con el contorno de la
> ventana del anillo, corrida por los siete tramos: ata los seis rieles y
> retiene el acrílico hacia dentro por todo el perímetro; canto a la silueta en
> las filas, retirado 1.65 bajo cada chapa y 11.2 en la trasera). **Los dos
> marcos de la trasera desaparecen**: la meseta llega al plano trasero
> (`prof_sup` 40.5 → 50 = `marco_remate`) y dobla 24 hacia abajo
> (`banda_trasera`): la banda vista ES el alma del miembro alto, una L con dos
> bridas de 27 × 14.5 en la cara del anillo, y el techo es una chapa del pico
> al canto sin costura. **El miembro bajo es el `talon`**: la misma banda con
> un pie de 22 sobre la tabla, tres M4 desde dentro, sin bridas. **La trasera
> va DENTRO de las dos bandas** (sobre el pie, bajo la meseta, 10 taladros y
> dos muescas de esquina) y sale por abajo; delante de ella no hay nada a
> distancia fija — la regla del postmortero (§3) que el marco de la rev. 23
> rompía a 8.00 justos contra un PMMA de ±1.2 (`guarda_trasera_dentro()`).
> **El chasis del PSU se atornilla a la tabla** por el suelo con 4 M4 (sus 2
> M5 apuntaban a la ranura de un 2020 muerto el 27-08). La esquina de
> abajo-atrás pasa a `radio_chapa`. 16 piezas → 4, 73 tornillos → 68, 16
> cabezas atrás → 10 sobre metal, 14 roscas por anillo (12 del marco — dos
> de ellas en la pata del suelo, el trabajo de los clips — y 2 de brida); la
> tapa de arriba abre 180°. Lo que cuesta: +0.28 kg, la trasera sale por
> abajo, la banda
> mide 24 y no 20 (con 20 la L sola trabaja a 158 MPa contra 130).
>
> **rev. 24** (2026-08-29, tarde): **nariz recta, meseta al pico, valle limpio**
> — tres notas de Samuel mirando el case en Blender, en
> [`2026-08-29-nariz-recta-valle-limpio-design.md`](2026-08-29-nariz-recta-valle-limpio-design.md).
> **Muere la bahía** (la bandeja de 60 bajo la fila 1U, tercer miembro desde
> el 27-08): en el valle solo van los dos Z-Rails 1U, arrimados al frente de su
> ventana; la placa del valle vuelve a 26 de fondo y pierde sus dos roscas de
> lengüeta; lo que ata los anillos a media altura son los seis rieles por sus
> placas, la tabla y la trasera, y el racking sigue en #203. **La nariz es
> recta**: `radio_punta` muere, la esquina de abajo-delante lleva un chaflán
> de 6 a 45° y un frente vertical de 13, y una banda nueva de chapa de 1.5 —
> la **`nariz`**, con pie sobre la tabla y tres M4 desde dentro — cierra el
> frente que enseñaba el riel desnudo; se para 2.2 mm bajo la cara del riel
> porque la fila de abajo es tapa y ese riel sale por la cara al abrir
> (`guarda_nariz()`). **La meseta llega al pico**: `prof_sup` 27.5 → 40.5 e
> `inset_remate_frente` muere — su «acantilado en 12.8» era de cuando la
> meseta era acrílico de 8 apoyado en el riel; con chapa de 1.5 la tapa de
> arriba sigue abriendo 121.5° —, y dobla un **retorno de 4** sobre la cara de
> arriba con 0.80 mm radiales de margen al barrido (`guarda_retorno_meseta()`).
> **Regla nueva:** toda esquina del anillo con chapa doblada encima mide
> `radio_chapa` = 4.5, el radio exterior del doblez; `radio_remate` muere y
> `placa_chaflan` baja de 12 a 11. Lo que quedó **abierto y declarado**: la
> banda del valle no apoya en nada — nunca apoyó; la bahía la tocaba en una
> arista — y `guarda_valle()` lo imprime como HUECO (fluye a 27 N) con sus
> salidas. Tornillería 59 → 53.
>
> **rev. 23** (2026-08-29): **la trasera se rehunde y la enmarca el metal.**
> Hasta hoy era la pieza más exterior de la cara de atrás y sus dos cantos
> corrían **540 mm cada uno sin metal encima**; el de arriba eran además los
> últimos 8 mm del **pico** del case — `guarda_remate()` repartía esa meseta
> entre `inset_remate_frente` + `prof_sup` + `t_piel`, y ese `t_piel` era el
> canto del acrílico haciendo de superficie vista. Se aplica por detrás la
> misma regla que ya gobierna el costado: el acrílico va **dentro** del metal.
> La plancha se rehunde `t_costilla` y asoman **dos bandas de chapa de 1.5** —
> `marco_trasera_sup_2d` (angular: banda vista de 20 y ala de 9.5 que dobla
> sobre el canto superior y muere en el doblez de la meseta) y
> `marco_trasera_inf_2d` (pletina plana de 20, sin ala: ese canto apoya en la
> tabla). Las dos cuelgan de las filas de M3 que la trasera ya llevaba a sus
> miembros — **cero taladros nuevos en el acrílico** — y las diez cabezas que
> se veían sobre el PMMA pasan a verse sobre metal. Lo paga **`prof_sup`, que
> baja de 29 a 27.5**, no el inset (su acantilado está en 12.8: con 13 la tapa
> de arriba abre 180°, con 12.8 abre 61); la meseta no se mueve por delante y
> el barrido probado sigue intacto. El ala B de la escuadra trasera se acorta
> la misma cantidad, de 12 a **10.5** — su punta sigue muriendo en la línea de
> la ventana del anillo. Puerta: `guarda_marco_trasera()`. Entra también el
> plano que le faltaba al anillo, **`cupon_anillo_2d`** (la sección, único
> plano suyo con profundidades, `seccion_del_cupon()`), y una puerta para el
> censo de la rejilla de entrada, `ranuras_rejilla_entrada()`, que hasta hoy
> era gemela **por lectura** — un humano contando LINEs del DXF.
>
> **rev. 22** (2026-08-28): **la costilla deja de ser chapa plegada y pasa a
> ser un anillo de pletina de aluminio mecanizada** — 14 mm de espesor, cara
> vista de 20, rebaje de 6 × 11 por detrás donde asienta el costado
> COPLANAR sobre una junta de EPDM de asiento de 1 mm, chaflán 1.5 × 45° en
> las dos aristas de la cara vista. Una pieza por lado, sin soldar: mueren
> el alivio convexo de 4.5 mm, el rip de P3 y la soldadura lineal de
> 14.5 mm de la rev. 21. Samuel rechazó el render de la chapa plegada por
> leerse «como un sándwich de aluminio envolviendo el acrílico».
> **Nada atraviesa la cara vista**: 16 roscas ciegas M4 por anillo en la
> cara interior (`taladros_anillo`) más 3 M5 por anillo en el canto
> inferior para la tabla, así que mueren los tornillos que cruzaban la
> costilla, el casquillo de aluminio (`L_casquillo`) y la junta de 4 mm del
> apilado de la rev. 21. El riel ancla ahora a una **placa** (×6, pletina
> de 6, una por tramo y por costado) que aloja la cabeza del M4 del riel;
> el ancho crece a **568.62 mm** (era 544.32) porque la placa y el anillo
> son más gruesos que la chapa que sustituyen. El canto trasero libre del
> costado —227 mm sin apoyo— gana una **escuadra** atornillada a la
> TRASERA (×2, nunca al anillo) y **clips** de retención (×4, dos por
> costado, solo en el tramo del suelo). Vano libre del costado, la misma
> cadena de CUATRO escalones que cuenta la §5 (el resumen se había comido
> uno y etiquetaba el primero como chapa): **119.0** mm con el acrílico
> portante → **65.2** con la chapa plegada de la rev. 21 → **95.5** al pasar
> a pletina sola en esta rev. 22 → **65.0 mm** con la escuadra de la trasera
> puesta; la flecha con 200 N va de **0.38** a **0.11** a **0.24** y otra vez
> a **0.11 mm**. Diseño completo en
> [`2026-08-28-costilla-pletina-design.md`](2026-08-28-costilla-pletina-design.md).

## 1. Objetivo

Diseñar y fabricar el case definitivo del SAM17 como pieza central del
instrumento: una **consola de dos pisos, íntegramente de acrílico naranja
translúcido**, de estilo modernista — placas planas, retícula estricta, cero
ornamento — unida por **separadores (standoffs) de aluminio a la vista** cuyo
ritmo de tornillería es parte del diseño. Los módulos cierran las dos caras
inclinadas con **paneles de PCB de aluminio**. Todo se fabrica por servicio de
**fresado CNC** a partir de archivos generados desde un modelo paramétrico
versionado en este repo. (Fue corte láser hasta el 2026-08-17; ver rev. 4.)

El case se dimensiona **por paneles, no por voces**: la arquitectura
polifónica fija que los mandos se comparten y los circuitos se replican, así
que el frontal no crece al crecer las voces — crece la PCB detrás de cada
panel. Se conservan de la tesis las convenciones de rotulación; **la altura de
panel de 190 mm NO se conservó** — desde el 2026-08-17 las dos filas son 3U
de EUROrack, 128.5 mm (rev. 4). El orden lógico es el de la cadena polifónica,
repartido en dos pisos por función:

- **Piso superior — generación:** MIDI/CV · VCO ×3
- **Piso inferior — procesamiento:** VCF · ADSR · VCA · MIXER

(El mixer va al final: en poly cada voz atraviesa su filtro y su VCA antes de
mezclarse.) El PSU vive dentro del piso inferior, sin panel propio más allá
de su zona de conexión trasera.

## 2. Decisiones de diseño

| Decisión | Elección | Por qué |
|---|---|---|
| Formato | Consola propia de dos pisos, **con paneles 3U de EUROrack** | La silueta es propia; el panel es estándar (128.5 mm, 1 HP = 5.08 mm). **Cambió el 2026-08-17**: antes eran 190 mm y explícitamente «no Eurorack». Se compraron Z-Rails de Tiptop de 104 HP |
| Estilo | Modernista: placas planas, retícula, standoffs vistos | Decisión estética del proyecto; el naranja translúcido hace el trabajo expresivo; el board de diseño aprobado fija el lenguaje |
| Estructura | Sándwich de placas de acrílico + esqueleto de perfiles 2020 + separadores de aluminio | La precisión depende solo de posiciones de agujero; elimina de raíz el problema de encajes |
| Paneles de módulo | PCB de aluminio (KiCad → fabricante tipo JLCPCB) | Serigrafía perfecta, agujeros exactos, acabado uniforme, bajo costo |
| Interfaz del módulo 2 | Instrumento autosuficiente en el RP2350; computadora **externa y opcional** por USB MIDI class-compliant + plugin compañero VST/CLAP. En el panel: **botón AFINAR + LED de estado**; los conectores de enlace (USB, MIDI DIN) los define el módulo 2 (panel o bloque trasero) | Pivote de cómputo del PR #30: si la computadora se cae en pleno concierto, el instrumento sigue sonando; desaparecen pantalla, Pi y sus consumos del frontal |
| Fabricación | **Fresado CNC** por servicio | El taller compensa el radio de herramienta en CAM, así que `kerf = 0`. El láser dejaba canto cónico en 8 mm y microfisuras en los bordes cargados. Cambió el 2026-08-17. Los DXF del repo siguen siendo directamente los archivos de corte |
| CAD | OpenSCAD paramétrico | Diseño-como-código versionable; exporta DXF (corte) y STL (render en Blender) |
| Servicio | **Enteramente desatornillable** + paneles de módulo desmontables | Acceso total al interior, sin una sola junta irreversible. Tuvo una **excepción única** hasta el 2026-08-21: la pestaña de remate iba PEGADA, porque el Z-Rail es extruido de pared fina de 1.2 mm y un M3 en esa cara atraviesa pared. La resolvió el **octavo larguero** — un 2020 en la arista trasera-superior que le da a esa tapa a qué atornillarse |

> **Enmienda del 2026-08-30 (D1):** la fila «Interfaz del módulo 2» decía
> «autosuficiente en el RP2350»; el chip es hoy un **STM32N657** (spec del
> hub N657, D1). La doctrina de la fila no cambia: el instrumento es
> autosuficiente y la computadora sigue siendo externa y opcional.

## 3. Postmortem del intento anterior (y cómo este diseño lo elimina)

El primer intento (adaptación del diseño de todbot, Thingiverse 3941263,
cortado en acrílico) falló porque **los dientes no cuadraron**. Causas raíz:

1. El diseño original está dibujado para plywood de **0.25 in = 6.35 mm**
   (fuente: README del autor en el zip); los dientes de un finger joint miden
   exactamente el espesor del material contrario. El acrílico se vende en
   espesores métricos y además el nominal trae tolerancia de fabricación
   (§11), así que todo diente quedaba corto o pasado.
2. Re-escalar el vector completo para compensar rompe el ancho de los dientes
   junto con las dimensiones generales.
3. El plywood comprime ~0.5 mm y perdona el ajuste a presión; el acrílico es
   rígido y frágil: o queda flojo o revienta.

La rev. 2+ no mitiga el problema: **lo elimina**. La arquitectura de sándwich
con standoffs no tiene encajes — la geometría crítica son posiciones y
diámetros de agujero, que no dependen del espesor de la plancha. Aun así:

- Los espesores (`t_base`, `t_cheek`, `t_piel`) y `kerf` siguen siendo
  parámetros del modelo (afectan agujeros, largos de tornillo y estética de
  cantos). Hubo un `t_acrilico` hasta la rev. 20; hoy es `t_valle`, y ya no
  es acrílico.
- **Cupón de calibración** (`coupon.scad`) — **solo aplica si se vuelve al
  láser; con fresado `kerf = 0` y no hay nada que calibrar.** Pieza con una
  escalera de diámetros de agujero (ajuste deslizante y ajuste justo para
  M3/M4) y una probeta de canto. Se corta primero con el acrílico y la
  máquina reales, se fija el `kerf` medido, y solo entonces se cortan las
  planchas definitivas. Con láser habría que hacerlo **dos veces**, una por
  espesor: la franja no es la misma en 5 que en 8 mm.

## 4. Geometría (defaults; todo parametrizable)

Perfil lateral escalonado de consola de estudio erguida, como lo fijó el
board de diseño: piso inferior casi vertical frente al intérprete, piso
superior reclinado. **Los ángulos se miden desde la vertical** (convención
del board; la rev. 2 era ambigua y el departamento de diseño la resolvió en
esta dirección).

| Parámetro | Default | Nota |
|---|---|---|
| `ancho_total` | **544.32 mm** | DERIVADO del riel: 528.32 (104 HP) + 2 × `t_cheek`. Ya no lo fija la suma de módulos |
| `alto_panel_inf` / `_sup` | **128.5 mm** | 3U de EUROrack, las dos filas. Fue 190 hasta el 2026-08-17 |
| `sep_railes` | **122.5 mm** | Entre centros. Lo fija el PANEL (ranuras a 3.0 de cada canto), no el riel: el Z-Rail lleva pletina roscada continua |
| `angulo_inferior` | **35° desde la vertical** | Cara del piso de procesamiento |
| `angulo_superior` | **45° desde la vertical** | Cara del piso de generación |
| `alto_frontal` | **19 mm** | Canto delantero. **No es un zócalo**: el zócalo se eliminó. Fue 13 hasta rev. 10; subió para que el raíl de panel del frente librara la bandeja |
| `fondo` / `alto_total` | derivados | **319.76 mm / 256.18 mm**. Ya NO cuadra con el board (350 × ~380): el board se dibujó para paneles de 190. El fondo subió 12.35 en la rev. 28 por la fila KONDOR de 55 |
| `t_valle` / `t_piel` | **3** / **8 mm** | `t_valle` es la tapa del valle y desde la rev. 20 es **chapa de ALUMINIO**: no entra en la medición de espesor de §11 ni en el pliego de acrílico. Se llamó `t_acrilico` hasta esa rev., y el nombre mentía sobre el material. La trasera tiene su propio espesor de 8, y ese sí se MIDE con calibre (§11) |
| `t_base` / `t_cheek` | 8 mm | Suelo portante y costados. La bandeja de base subió de 5 a 8 al pasar a ser el propio canto de abajo |
| `kerf` | **0** | Correcto fresando: el CAM compensa el radio de herramienta. Solo vuelve a ser negativo si se regresa al láser |
| `n_bulkheads` | 2 | Costados exteriores; el modelo admite uno central si el vano lo pide |

Los valores derivados los calcula el modelo, no se fijan a mano. Las holguras
que deciden el diseño viven en **`case/clearance_budget.py`** (Principio II:
presupuesto ejecutable con aserciones, no prosa):

- altura interior del piso inferior vs. altura del transformador real del
  módulo 1 (según spec de la fuente v2), margen ≥ 15 mm;
- profundidad libre bajo cada cara vs. la PCB más honda del censo real de
  módulos — tras el pivote de cómputo el cerebro es un RP2350 y ninguna pieza
  domina de antemano, así que el censo se hace, no se supone;
- suma de anchos mínimos de panel + expansión vs. ancho útil, **por piso**;
- largo de standoffs vs. espesores reales de placas apiladas.

El script corre en verde **antes** de mandar nada a cortar (Principio III: la
comprobación va antes del paso destructivo).

## 5. Estructura

> **Enmienda rev. 27 — 2026-08-30.** Sustituye en esta sección los párrafos
> operativos de «el techo y el talón» y «trasera» de la rev. 26. El techo queda
> **macizo**, con labio de 20, y descarga por una rendija de 4.0 bajo el alero;
> `guarda_aire()` cuenta 9.22 W. Las tres chapas —techo, nariz y talón— entran
> rehundidas 1 en el rebaje de 4.5 × 3 del anillo, salvo los pies, que siguen a
> ras sobre la tabla. La tabla se prepara con nariz y talón y **entra con el
> anillo B**; el chasis del PSU se monta al final por el frente. El porqué de
> la arquitectura sustituida se conserva en las viñetas siguientes.

**REESCRITA EN LA REV. 21 (2026-08-27) Y OTRA VEZ EN LA REV. 22 (2026-08-28).**
Hasta la rev. 20 esta sección decía que los costados de acrílico eran *«las
piezas portantes»*. Ya no lo son desde la rev. 21, y desde la rev. 22 la
pieza portante tampoco es la chapa plegada que la rev. 21 puso en su lugar:
es un anillo mecanizado. El diseño completo del cambio está en
[`2026-08-28-costilla-pletina-design.md`](2026-08-28-costilla-pletina-design.md);
aquí va lo que sustituye a lo anterior.

- **Costillas (×2): anillo de PLETINA de aluminio FRESADA, 14 mm.** Son
  **las piezas portantes**, una pieza por lado, sin soldadura. Cara vista
  de 20 mm, ventana vaciada en el centro, rebaje de 6 × 11 mm por detrás
  donde asienta el costado, chaflán 1.5 × 45° en las dos aristas de la
  cara vista. **Ningún tornillo atraviesa la cara vista**: 16 roscas
  ciegas M4 por anillo en la cara interior (`taladros_anillo`), más 3 M5
  por anillo en el canto inferior para la tabla. Su DXF (`costilla_2d`) es
  ahora un **contorno real**, no un desarrollo — al revés que en la
  rev. 21, porque la pieza ya no se dobla.
  **Corrección del 2026-08-30:** el censo de 16 queda como historia y se
  sustituye por **14 roscas ciegas M4 por anillo**: doce para el marco de la
  ventana y dos para la brida del techo. Las 3 M5 del canto no cambian.
- **Costados (×2): acrílico naranja de 8 mm.** Siguen siendo **piel**: no
  sostienen nada y **no llevan un solo taladro** desde el 2026-08-27.
  Desde la rev. 22 entran por detrás y asientan **coplanares** en el
  rebaje del anillo, sobre una junta de EPDM de asiento de 1 mm — ya no
  van «capturados entre dos alas» (eso era la rev. 21): el labio del
  anillo los sostiene hacia fuera por todo el perímetro, y hacia dentro
  los retiene el **marco de la ventana** en los siete tramos (rev. 25;
  placas, clips y escuadra hasta la rev. 24). Su silueta escalonada
  sigue siendo la del aparato.
- **Marco de la ventana (×2): pletina de aluminio de 6 mm** cortada a
  láser con el contorno de la ventana del anillo, una por costado,
  espejadas. Aloja la cabeza del M4 de cada Z-Rail en un cajeado, se
  rosca al anillo con doce M4 ciegos (diez en las filas, dos en
  la pata del suelo) y pisa 6 mm de acrílico volado por
  todo el perímetro: es a la vez el anclaje de los seis rieles y el tope
  del costado hacia dentro. Sustituye (rev. 25) a las tres placas de
  anclaje, los dos clips y la escuadra de la trasera de cada costado — «la
  placa es el marco de la fila» llevado hasta el final. Orden de montaje
  obligado: el costado en el rebaje, después los rieles al marco, después
  el marco al anillo desde dentro.
- **Tabla de madera maciza de 18 mm**: el **suelo interior y el zócalo**,
  una sola pieza de **588.62 × 339.76** (creció desde 570.62 × 328.94
  porque el anillo es más grueso que la chapa que sustituye) bajo el
  marco. Los dos anillos se le apoyan encima y las cuatro paticas van
  atornilladas debajo. **Su fijación va con agujero alargado** — un
  redondo por fila como punto fijo y el resto en ranura —, ahora a
  **rosca ciega en el canto inferior de cada anillo** en vez de a un
  larguero, porque la madera se mueve a contraveta y el aluminio no.
- **El techo y el talón**, las dos piezas de chapa de atrás (rev. 26). El
  **techo** (miembro alto) es la meseta del pico al canto y, por detrás,
  chaflán de 6 + labio de 18 a ras del plano trasero (variante B, escogida el
  2026-08-30; la A era la banda de 24), con dos bridas de extremo en la cara del anillo (2 M4 ciegos
  cada una) — ata los dos anillos arriba y tapa el canto de arriba de la
  trasera. El **talón** es la nariz de atrás: pie de 20 sobre la tabla (tres
  M4 desde dentro), chaflán sobre el de P6 y labio de 13, con ocho pestañas
  lanzadas del pie detrás de la trasera; no ata nada, que para eso está la
  tabla. Fueron perfil 2020 comprado hasta el 2026-08-27, canales de chapa
  hasta la rev. 24, una L y un ángulo con la trasera atornillada durante la
  rev. 25. El reparto exacto lo fija el modelo.
- **Las planchas (trasera; banda del valle) anclan a la retícula de un
  miembro, nunca a los 6 raíles de panel** — regresión corregida en el fix
  round 1 de la Tarea 5: esta viñeta llegó a decir lo contrario, que los
  PANELES DE MÓDULO anclan a los miembros, y eso es falso: los paneles sí
  van a los raíles, es la razón de ser del formato Eurorack. Lo cierto es
  de las PLANCHAS: la trasera a la banda del miembro alto y a la del
  talón (5 M3 cada una, rev. 25) y la banda del valle con sus dos pestañas
  al marco de la ventana (ruling R3). Las planchas no
  comparten anclaje con los paneles porque los raíles van girados al
  ángulo de su cara, y un tornillo de plancha contra una cara inclinada
  entraría descentrado y apoyaría la arandela de canto sobre acrílico
  frágil. Verificado por `alineacion()` en el budget.
- **Trasera: UNA plancha de acrílico de 8 mm**, CAPTURADA como las
  mejillas (rev. 26): sus puntas en un bolsillo fresado en el tramo trasero
  de cada anillo (labio 3, 6 de hondo), rehundida 4 sobre junta de EPDM,
  apoyada en el pie del talón y muriendo bajo el fin del bolsillo, **sin un
  taladro** — el bolsillo está cerrado por los dos extremos y la plancha entra
  con el segundo anillo, como los costados; lleva la ventilación (§7). Fue atornillada a dos bandas con 10 M3 durante una tarde
  (rev. 25), y dos pieles de 5 flotando sobre standoffs con junta de sombra
  hasta el 2026-08-21; flotar y sellar son incompatibles.
- **Tapa del valle: chapa de aluminio de 3 mm.** Se atornilla al **marco
  de la ventana** con una pestaña doblada por punta (desde la rev. 22 a la
  placa del valle, desde la rev. 25 al marco; hasta entonces iba a las
  costillas): deja de ser una plancha sobre una bisagra y pasa a ser
  **diafragma** a media altura.
- **Paneles de módulo: PCB de aluminio** de ancho variable en múltiplos de
  1 HP (5.08 mm), **128.5 mm de alto**, cerrando las dos caras inclinadas.
- **Pies de goma** bajo la tabla.
- **Sin pegamento estructural en ninguna junta.** La pestaña de remate, que era
  la excepción, se atornilla desde el 2026-08-21.

**Lo que cada cambio compró, medido:** el vano libre del costado —el trozo
de acrílico más lejos de cualquier apoyo— cae de **119.0 mm** (acrílico
portante) a **65.2 mm** con la chapa plegada de la rev. 21, sube a
**95.5 mm** al pasar a pletina sola en la rev. 22 (el anillo es más grueso
pero pierde el canto trasero que antes cubría el vano de otra forma),
vuelve a bajar a **65.0 mm** con la escuadra de la trasera puesta y a
**62.9 mm** con el marco de la ventana (rev. 25); la flecha con 200 N va de
0.38 a 0.11 a 0.24 a 0.11 y otra vez a **0.11 mm**, porque el apoyo deja de
ser cuatro tornillos y pasa a ser la ventana del anillo en todo el
perímetro, por las dos caras.

## 6. Raíles y sistema de paneles

- **4 perfiles de aluminio 2020** (dos por piso, arriba y abajo de cada cara
  inclinada), atornillados a los costados.
- **Tuercas T deslizantes M3**: cada panel se atornilla en cualquier posición
  horizontal; los anchos de módulo pueden cambiar libremente durante el
  desarrollo.
- Tornillos de panel a **5 mm del borde** superior e inferior → separación
  entre centros de raíl = **180 mm** por piso. Offsets exactos raíl–panel los
  resuelve el modelo CAD.
- **El patch bay normalizado no pide sitio propio**: vive en los jacks de
  cada módulo (pin de switch del Thonkiconn), no en un módulo aparte — no se
  reserva zona de patch bay en el frontal. Sí infla el ancho de los paneles
  que ganan jacks; eso lo vigila el budget por piso.
- La plantilla KiCad de panel (en `case/panels/`) fija: **alto 128.5 mm**, posición
  de agujeros de tornillo, zona útil de componentes y estilo de serigrafía
  (tipografía y convenciones de `docs/modules/08-case-panels.md`, revisadas
  al lenguaje modernista: retícula, sin adornos).
- Requisitos derivados para el panel del módulo 2: **botón AFINAR + LED de
  estado**; los conectores de enlace con la computadora externa (USB MIDI
  class-compliant, MIDI DIN con opto) los ubica el diseño del módulo 2 — en
  su panel o en el bloque trasero fijo; el case solo garantiza el acceso.

## 7. Eléctrico y seguridad

- **Bloque trasero fijo del piso inferior** (esquina junto al costado
  derecho): entrada IEC C14 con portafusible + interruptor. El cableado de
  230 V vive solo en ese bloque y llega al transformador del módulo 1,
  montado sobre la base junto al costado derecho. **Las pieles removibles
  nunca llevan mains.**
- **Bonding de tierra** (requisito del módulo 1,
  [`design-notes.md` §13](../../../hardware/01-power-supply/notes/design-notes.md)):
  espárrago M4 único junto al PSU + cable verde/amarillo con terminal de ojal
  bajo un tornillo de cada panel de aluminio. Ni los raíles 2020 ni los
  standoffs anodizados cuentan como camino de tierra confiable.
- **Ventilación con firma**: las perforaciones de las pieles traseras y de la
  base (bajo el PSU) dibujan **onda sierra, triangular y cuadrada** — las
  tres formas de onda de los VCOs — trazadas como retícula geométrica
  estricta, coherente con el lenguaje modernista (así aparecen en la vista
  posterior del board). Convección natural para el PSU lineal.
- Requisito derivado hacia los módulos (no es trabajo del case): las PCBs
  llevan **conformal coating**, porque el cuerpo es deliberadamente abierto
  (juntas de sombra y ventilación).

## 8. Archivos y flujo de trabajo

```
case/
├── cad/          sam17_case.scad (modelo paramétrico)
│                 coupon.scad (cupón: escalera de agujeros + probeta de canto)
│                 export.ps1 / Makefile → regenera DXF + STL con un comando
├── plans/        DXF por plancha de acrílico, nesteados — salida directa
│                 al servicio de corte
├── panels/       plantilla KiCad de panel de aluminio
├── renders/      propuesta-diseno-2026-08-16.png (board aprobado, intención)
│                 STL → Blender (acrílico naranja translúcido, aluminio)
│                 → PNG del conjunto
├── clearance_budget.py   holguras del §4, ejecutable con aserciones
└── README.md     BOM de herrajes, orden de ensamblaje, procedimiento del
                  cupón, calibración de kerf
```

- Requiere instalar **OpenSCAD** (~50 MB); Blender e Inkscape ya están.
- **El artefacto es el script** (convención de la constitución): el `.scad` es
  la fuente de verdad y lo que se revisa en el PR; los DXF/STL se regeneran
  con el script de export y se commitean como artefactos de fabricación, igual
  que los gerbers en `hardware/*/fab/`.

## 9. BOM mecánico (categorías; cantidades exactas en el eco)

**Este párrafo quedó revisiones enteras detrás de la implementación real**
(pieles con standoffs, paticas torneadas, transversales 2020 pasantes) y se
corrige aquí contra la salida real del modelo, el 2026-08-28. Categorías
actuales: **anillo de pletina de aluminio mecanizada** (×2, la pieza
portante — §5, 14 mm, sin soldadura); **marco de la ventana** (×2, pletina
de 6 mm a láser, rev. 25 — sustituye a las placas, los clips y las
escuadras de la rev. 22); **miembro alto** (una L de chapa de 1.5 con
brida de extremo, la meseta y la banda de atrás) y **talón** (chapa de
1.5, la banda de abajo con su pie a la tabla) — perfil 2020 comprado hasta
el 2026-08-27, canales de chapa hasta la rev. 24; **6 Z-Rails de Tiptop de 104 HP** (528.32 mm, sección 23.8 × 10 —
4 para las dos filas 3U, 2 para la fila auxiliar KONDOR de 55 mm del valle);
tornillería inox M3/M4/M5 de botón; los 12 M4 de los seis Z-Rails son fijos,
sin tornillos de hombro, cierres manuales, Belleville ni arandelas de fricción;
ningún tornillo muerde acrílico; tuercas T de inserción lateral, no de deslizar;
**junta de asiento EPDM de 1 mm** (×2, una por anillo, nueva de la rev. 22
— sustituye al casquillo de aluminio y a la junta de 4 mm de la rev. 21);
tabla de madera maciza de 18 mm; paticas de **goma** EPDM/NBR con
casquillo roscado (no metálicas desde la rev. 18); entrada IEC C14 con
fusible, espárrago M4 + cable verde/amarillo + terminales de ojal (bonding,
uno por panel de módulo) — más un segundo punto de bonding, enmascarado
antes de anodizar, uno por anillo. **Sin adhesivo en ninguna junta** — la única que lo llevó,
la tapa de remate (pegada hasta el 2026-08-21, atornillada después), no
existe desde el 2026-08-27: la meseta pasó a ser el ala del miembro trasero
alto.

Los Z-Rails van entre las caras interiores de las placas de anclaje, así
que su largo es `largo_riel` (**528.32 mm**), no `ancho_util`
(**540.62 mm**) ni `ancho_total` (**568.62 mm**). Cantidades y largo
exactos: salida real de `openscad -D 'PART=\"bom\"' case/cad/sam17_case.scad`
— el modelo las cuenta desde `centros_rail()`, `roscas_marco()`,
`bridas_anillo()` y `centros_rosca_ciega()`, y quien las recuente después
de tocar `params.scad` toma ese eco, no este párrafo.

## 10. Verificación

1. **Cupón antes que planchas** — el kerf y los diámetros de ajuste medidos
   se registran en `case/README.md` junto con proveedor, material y máquina.
   **Y EN LA REV. 21 BAJA DE BLOQUEANTE A COSMÉTICO.** Medir el espesor sigue
   valiendo la pena, pero ya no bloquea el corte: las cotas funcionales que
   colgaban del espesor del acrílico se fueron con la carga. El costado no
   lleva taladros, no recibe apriete y no sostiene nada — si llega a 7.2 o a
   8.8 mm, lo que cambia es cómo se ve el canto, no si el case cierra. Lo que
   sí sigue acotado contra un espesor es `marco_sup` — que desde el
   2026-08-27 ya NO es una plancha aparte: es el ala del miembro trasero
   alto, doblada de su propio blank. La «tapa de remate» que este punto
   citaba no existe (`remate_sup`/`remate_sup_2d`, sin llamador, borradas
   del `.scad` en el fix round 1 de la Tarea 5).

   El texto original, que sigue siendo cierto sobre el material: el PMMA colado
   llega con tolerancia de hasta ±1.2 mm en 8 mm. Es la
   aplicación de los Principios III y V: la comprobación va antes del paso
   destructivo, y entre cortar a ciegas y no cortar, no se corta.
2. `case/clearance_budget.py` **en verde**, con autocomprobación del cálculo,
   aserciones que fallan si el diseño se sale, y bloque de lo que no cubre.
3. El script de export debe regenerar todos los DXF/STL sin errores desde un
   repo limpio, y **salir con código de error** si algo queda a medias.
4. Checklist de ensamblaje en `case/README.md` con el orden: **tabla → riel
   a la placa → placa al anillo → miembros → marco a la tabla → chasis del
   PSU → tapa del valle → electricidad y bonding → trasera → escuadras de
   la trasera → costados → clips de retención → paticas y paneles.**

   **EL ORDEN SE DIO LA VUELTA EN LA REV. 21**: el acrílico dejó de ser lo
   primero que se monta y pasó a ser lo último que se mete. La estructura se
   levanta entera en aluminio sobre la tabla, y el costado entra casi al
   final porque no sostiene nada y porque es la pieza que se raya.

   **Y GANA TRES PASOS PROPIOS EN LA REV. 22** (alineado con README en el
   fix round 1 de la Tarea 5, que hasta entonces contradecía este punto):
   (a) «riel a la placa» y «placa al anillo» se separan en dos pasos por
   R1 — la cabeza del M4 del riel se tapa desde fuera antes de que la
   placa entre al anillo, y al revés no se puede apretar; (b) las
   **escuadras de la trasera** van justo después de montar la trasera,
   porque se atornillan a ella y no al anillo; (c) los **clips de
   retención** son el único apoyo hacia dentro que va DESPUÉS del costado,
   no antes — muerden el acrílico por delante y sin el costado puesto no
   tienen qué morder.

   Y hay un paso nuevo que no es de orden sino de apriete: **el tornillo
   redondo del medio de cada fila de la tabla va antes que los de ranura, y
   los de ranura no se pasan de apriete.** Un tornillo de ranura apretado a
   tope es un tornillo redondo, y ahí se acabó la ranura.

   Este punto decía «costados → bandejas y standoffs → raíles», y era
   físicamente imposible según el §5 de esta misma spec: las bandejas se
   atornillan con tuercas T al esqueleto, y una tuerca T vive dentro de la
   ranura del perfil. Sin largueros no hay dónde atornillar la bandeja
   (issue #50). Además metía bandejas y pieles en el mismo paso, y no son el
   mismo herraje.

## 11. Lo que NO está confirmado

Convención del repo (Principio I): lo no verificado no se suaviza, se lista
con qué habría que medir para cerrarlo.

- **Espesor real del acrílico naranja**: el nominal miente. Y con PMMA
  **colado** (GS, que es el que pide el diseño por su baja tensión interna)
  la tolerancia llega a **±(0.4 + 0.1 × espesor)**, o sea ±1.2 mm en 8 mm —
  confirmado por escrito por Schaeffer AG el 2026-08-18: *«Die
  Herstellungstoleranzen können wir jedoch nicht beeinflussen»*. Nadie la
  mejora. Se cierra midiendo con calibre la plancha comprada y metiendo ese
  valor en `t_base` / `t_cheek` / `t_piel`, **antes de cortar** — los tres
  espesores de PMMA que quedan, y desde la rev. 20 son **8 mm los tres**.
  `t_valle` NO entra: dejó de ser acrílico. El
  taller debe medir y avisar; es una de las preguntas del RFQ. Issue #98.
- ~~**Kerf**~~ — **CERRADO por cambio de proceso** (2026-08-17). Con fresado
  CNC el CAM compensa el radio de herramienta y la pieza sale a la cota del
  dibujo, así que `kerf = 0` y no hay nada que calibrar. El procedimiento del
  cupón se conserva en `case/README.md` por si se vuelve al láser — y
  entonces hay que hacerlo **dos veces**, una por espesor. Issue #40.

- **Qué cara del Z-Rail mira al panel**: la hoja de Tiptop acota el taladro
  M4 de punta a 9.5 mm de un canto y por tanto a 14.3 del otro; cuál de los
  dos toca el panel no está confirmado. Si fuera el otro, `rail_er_eje` pasa
  de 14.3 a 9.5 y hay que re-derivar. Se cierra con el riel en la mano y un
  calibrador. Issue #97.
- **Transformador y térmica de la fuente v2**: la spec de la fuente
  ([`2026-08-16-psu-v2-goat-design.md`](2026-08-16-psu-v2-goat-design.md))
  define pre-reg + LT3045/LT3094 y trae su propia lista de no confirmado; el
  budget del case toma de ahí la altura del transformador y la necesidad real
  de ventilación cuando esa spec cierre sus números.
- **Censo de fondos de PCB por módulo**: la aserción de profundidad usa
  estimados hasta que cada módulo publique su PCB (tras el pivote de cómputo
  ya no hay una pieza dominante conocida).
- **Suma de anchos de panel por piso vs. `ancho_total`**: solo cierra cuando
  cada panel esté dibujado; el budget la vigila con anchos mínimos estimados
  por módulo y por piso — y el patch bay normalizado añade jacks a varios
  paneles. Si un piso no cabe, `ancho_total` sube — es un parámetro, no una
  promesa.
- **Rigidez del vano a ~500 mm sin costado central**: heurística. Si el
  prototipo flexa, `n_bulkheads` pasa a 3 y se re-exporta; se cierra cargando
  el prototipo real. **Y la rev. 19 le quitó una barra**: al retirarse el
  larguero de entrepiso delantero el cajón pasa a 4 travesaños. Lo que sí está
  acotado es la pieza plana —`guarda_costado()` mide el vano libre del costado
  y su flecha bajo `carga_mano`—, pero eso es UNA placa, no el racking del
  conjunto. Es la misma medición pendiente de antes, con menos margen.
- **Comportamiento del acrílico bajo apriete de standoffs**: el diseño manda
  arandela y agujero con holgura, pero el par máximo antes de fisura no está
  medido; se cierra con la probeta del cupón.
- **Las cotas de la cara vista del anillo son ESTIMADO** (rev. 22): chaflán
  1–3 mm, rehundido 3–7 mm, cara vista 12–24 mm salieron de escalar una
  foto de referencia, no de una medición. Se cierra con un **cupón de
  100 mm del perfil**, mecanizado y anodizado igual que la pieza final,
  comparado contra la referencia **antes de cortar los dos anillos
  completos** (PLIEGO §6.1). Bloquea el corte del anillo, no el resto del
  case.
- ~~**La trasera enseña canto arriba y abajo**~~ — **CERRADO el 2026-08-29**
  (rev. 23, #234): dos bandas de chapa la enmarcan y la plancha se rehunde
  `t_costilla`. **Y superado la misma noche (rev. 25)**: esas dos bandas
  pinzaban la trasera a 8.00 justos contra un PMMA de ±1.2; hoy son la
  banda del miembro alto y la del talón, la trasera va dentro y la puerta
  es `guarda_trasera_dentro()`.
- **Planitud del anillo tras vaciar el centro de una pletina de 14 mm**
  (rev. 22): es la pregunta eliminatoria del RFQ (§B/§D) y el riesgo
  técnico real de esta pieza — la resistencia sobra por 2× (I = 3714 mm⁴
  contra 1673 mm⁴ de la chapa que sustituye, `guarda_anillo()`). Se cierra
  cuando un taller lo garantice por escrito.
- ~~**Las placas de anclaje y los clips no tienen DXF propio**~~ — **CERRADO
  el 2026-08-28** (Tarea 6, rev. 22) con cuatro DXF, **y superado el 29-08
  por la noche (rev. 25)**: placas, clips y escuadras son el marco de la
  ventana, un DXF (`marco_ventana_2d`) que relee `taladros_marco_ventana()`.
- **El racking del conjunto (#203)** sigue sin número, y la rev. 25 cambia
  su camino de carga por abajo: el diafragma trasero (la trasera atornillada
  a las dos bandas) se ata abajo a la tabla por el talón, no a un canal de
  1.5 con dos bridas. Argumento de camino de carga, no de medida.
- **El chasis del PSU colgaba de un 2020 muerto** (rev. 25): sus dos M5 de
  pared apuntaban a la ranura interior de `base trasera`, que murió el
  27-08, y `guarda_chasis()` solo miraba que cayeran en la pared del chasis.
  Cerrado por construcción — cuatro M4 por el suelo a la tabla —; el
  hallazgo queda aquí y en el cuerpo del PR.

## 12. Fuera de alcance (el diseño no los bloquea)

Al cerrar la tanda se abren como issues con evidencia (Principio VI):

- **Plugin compañero VST/CLAP** (nih-plug, Rust) y todo el enlace con la
  computadora externa — software, flujo spec-kit, ya descrito en el pivote de
  cómputo del PR #30.
- Tapa frontal de transporte.
- Patas plegables / soporte de ángulo variable.
- **Iluminación WS2812**: la fuente v2 ya le reserva alimentación
  (+5 V digital con SMPS encapsulada para RP2350 + WS2812); el translúcido
  naranja la difunde. El case no la implementa en esta tanda, pero las
  bandejas dejan paso de cableado.
- Layouts individuales de cada panel de módulo (trabajo por módulo usando la
  plantilla de `case/panels/`).

> **Enmienda del 2026-08-30 (D1):** el destinatario de la SMPS encapsulada
> de la línea de WS2812 es hoy el **STM32N657**, no el RP2350 (spec del hub
> N657, D1). La reserva de alimentación —+5 V digital para el módulo 2 más
> la cadena WS2812— no cambia.
