// params.scad — unica fuente de verdad dimensional del case.
// Unidades: mm y grados. Angulos de cara MEDIDOS DESDE LA VERTICAL
// (convencion del board de diseno, spec §4 rev. 3).
// clearance_budget.py parsea este fichero: solo lineas `nombre = valor;`
// con valores numericos. No usar expresiones en este fichero.

// --- silueta (spec §4 + board 350 x ~380) ---
// Ancho del case. FUE 500 por spec §4, y era una eleccion; ahora lo fija el
// riel que se compra, igual que sep_railes. Los Z-Rails vienen en largos de
// catalogo, no a medida:
//
//   84 HP  = 426.72 mm    se queda 57 corto
//   104 HP = 528.32 mm    <- este
//
// Con 484 de ancho util habia que cortarle 44 mm a cada riel, y cortar un
// extremo se lleva por delante justo la punta por donde se fija. Samuel eligio
// el 2026-08-17 alargar el case en vez de cortar el riel, asi que el ancho util
// ES el largo del riel y el total se deriva:
//
//   ancho_total = 528.32 + 2*t_cheek = 544.32
//
// De paso los modulos ocupan 104 HP exactos de canto a canto, que es lo que el
// riel promete. Contra el censo de anchos (360 arriba, 390 abajo) sobran 168 y
// 138 mm de crecimiento por fila en vez de 124 y 94.
//
// OJO CON LA FLECHA: el vano entre costados pasa de 484 a 528, un 9 % mas, y la
// flecha de una placa apoyada en sus extremos va con L^3 -- o sea un 30 % mas
// de pandeo con el mismo espesor. n_bulkheads sigue en 2; si la bandeja del PSU
// cede al cargarla, el remedio es el tercer costado interior que ya contempla
// la spec §11, no engordar el acrilico.
// DERIVADO desde el 2026-08-26, y que lo sea NO es cosmetico. Estuvo escrito a
// mano (544.32) mientras el comentario de arriba daba la formula, asi que la
// igualdad con el riel salia por CASUALIDAD ARITMETICA y no por derivacion --
// justo la clase de cota que parece verificada y nunca se comprobo. Ahora hay
// mas de una cosa metida en ese hueco y a mano se desincroniza al primer
// cambio. clearance_budget.py calcula esta MISMA formula y se niega a arrancar
// si alguien la devuelve a literal.
// --- EL ESQUELETO DE ALUMINIO (spec 2026-08-26) ---
// ESTE ESPESOR ES EL DE LA CHAPA DE LOS TRES MIEMBROS TRANSVERSALES desde el
// 2026-08-28, y ya no el de la costilla. La costilla dejo de ser chapa ese
// mismo dia: pasa a ser un anillo FRESADO de pletina (ver t_anillo, abajo).
// De esta chapa se siguen plegando los tres miembros -- el canal trasero bajo,
// el canal trasero alto (cuya ala de arriba es marco_sup, la meseta) y la
// bandeja de la bahia --; su seccion la deriva guarda_miembros() con
// _seccion_canal(w, d, t_costilla). La banda del valle NO sale de aqui: va en
// t_valle, que es otro espesor y otro aluminio.
//
// LA COSTILLA SIGUE SIENDO LA PIEZA PORTANTE, solo que ahora de pletina. El
// costado de acrilico paso a piel y ya no sostiene nada: no lleva un solo
// tornillo estructural.
//
// LA HISTORIA DEL NUMERO ES LA DE LA COSTILLA CUANDO ERA CHAPA, y se conserva
// porque es la que explica por que hoy vale 1.5 y no otra cosa:
//
//   FUE CHAPA PLEGADA y no plancha fresada desde el 2026-08-26. La L iba a
//   formarse atornillando una tira al CANTO de la costilla, y ese canto tenia
//   3 mm mientras el agujero de paso de un M3 mide 3.4 -- el agujero era mas
//   ancho que la pieza. No quedaba justo: no cabia. Plegando, el ala salia del
//   propio material y no habia junta que atornillar, ni paso de tornillo que
//   calcular, ni 78 M3 que comprar.
//
//   FUE 3 mm, y el numero no lo fijaba la rigidez sino el ancho del case: el
//   ala se metia en el hueco donde va el Z-Rail, asi que ancho_total crecia
//   2*t_costilla. A 3 el case crecia 6 mm; a 4, ocho. Con el ala doblada, 3
//   pasaba con 2.4x -- la rigidez la daba la FORMA en L, no el espesor.
//
//   BAJO A 1.5 el 2026-08-28: 50 % menos chapa y 3 mm menos de ancho exterior.
//   A ese espesor la costilla llegaba a 144.4 MPa, asi que ya no valia el 5754
//   H22 de 130 MPa: la pieza pasaba obligatoriamente a 6082-T6 (Rp0.2 250
//   MPa), como declara el pliego. La peor flecha quedaba en 0.397 mm contra el
//   techo de 0.60.
//
// El 1.5 se queda tal cual al irse la costilla a pletina: es el espesor con el
// que ya estan calculados los tres miembros, y ninguno de ellos cambio.
t_costilla      = 1.5;
// Los tres miembros arrancan en 20 x 20: es la envolvente del 2020 que jubilan
// ALTO DE LAS ALAS DE LA BAHIA, y con el su fondo util.
//
// La bahia es una BANDEJA: suelo perforado y dos alas dobladas hacia arriba.
// Las alas hacen tres cosas a la vez -- son la pared de la bahia, son el canto
// donde apoya la tapa del valle, y son lo que le da inercia a la pieza.
//
// 60 SALE DE DOS TOPES, uno por arriba y otro por abajo:
//   - por arriba, el canto del ala tiene que llegar al plano de la tapa del
//     valle (y = 143.58), que es donde apoya.
//   - por abajo, el suelo de la bahia queda en 143.58 - 60 = 83.58, y el techo
//     del chasis del PSU esta en 66.00: quedan 17.58 mm de aire para el
//     cableado que baje de la bahia a la fuente.
// Un jack de 6.35 pide unos 30 mm detras del panel y un minijack 20: los dos
// entran en 60 con sitio de sobra.
bahia_alto  = 60;
// y la minima que ya le gana en inercia (6935 mm4 contra ~5600). La seccion
// definitiva de cada uno sale de su carga.
canal_ancho = 20;   // cota exterior perpendicular a la carga
// FUE 20, la envolvente del 2020 que estos miembros jubilan, y con chapa de
// 3 mm daba I=6279 mm4: 1.12x el perfil. Al bajar la chapa a 1.5 pierde esa
// ventaja; 24 mm es el fondo minimo que vuelve a ganarle al 2020. Lo deriva
// guarda_miembros(), no una equivalencia nominal de cajas.
canal_fondo = 24;   // cota exterior en la direccion de la carga
// Vale lo mismo que ya repartian las filas de las planchas de acrilico para
// que sus tornillos caigan en la reticula por construccion, no por coincidencia.
// Una sola cota gobierna ambos lados: repetir 100 los desincronizaria al cambiarla.
reticula_paso = 100;
// LA PESTANA DE LA BANDA DEL VALLE. La banda lisa del vuelo delantero se
// dobla 90 grados en cada punta y se atornilla a la costilla: asi no queda
// sujeta SOLO por una linea longitudinal de tornillos, que seria una bisagra.
// Las pestanas fijan la banda; no se les atribuye funcion de diafragma.
//
// La plancha central y sus diez M3 al canto ya no existen. guarda_valle() mide
// la banda como voladizo hacia abajo y publica aparte el levantamiento entre
// los dos M3 laterales, que es su caso estructural critico.
//
// 21 SALE DEL TORNILLO, y va apretado: el M3 tiene que caer 2t+r por debajo de
// la tangente del doblez (13.70 mm bajo la cara de arriba) y aun asi dejar 1.5*D
// hasta el canto libre. 13.70 + 1.7 + 5.1 = 20.5 -> 21.
//
// Y SOLO HAY UNA PESTANA POR PUNTA. Ocupa los ultimos 3D del vuelo delantero:
// es el minimo que conserva 1.5D a ambos lados del M3 y permite abrir mas de 60
// grados. El alivio siguiente libra la esquina que alcanza el Z-Rail 3U.
pestana_valle      = 21;
// Alivio en la esquina libre DELANTERA de cada pestana. El Z-Rail 3U invade
// 0.57 mm del rectangulo sin recortar; 1 mm lo libra y queda lejos del M3.
// solapes() usa esta misma cota para refinar el falso positivo de su AABB.
muesca_riel_valle  = 1;
// Radio interior del doblez de la tapa. Sigue en aluminio de 3 mm aunque la
// costilla haya bajado a 1.5, asi que r=3 conserva su relacion 1xt.
radio_doblez_valle = 3;

// EL ANILLO DE PLETINA. La costilla dejo de ser chapa plegada el 2026-08-28:
// Samuel vio el render de la banda de 27 y lo llamo "sandwich", y la
// referencia que quiere es un perfil estrecho y profundo con canto. Eso no
// sale de un pliegue de 1.5 -- no hay arista que chaflanar ni esquina sin
// alivio. Sale de un anillo fresado de pletina. Spec 2026-08-28.
//
// 14 LO MANDA EL ACRILICO, no el gusto. El PMMA de 8 viene +-1.2 (Schaeffer),
// asi que el peor caso mide 9.2; tras el labio de 3 tienen que caber 9.2 mas
// 1 de junta de asiento mas 0.5 de aire = 10.7. Con 12 el rebaje quedaba a
// -0.2. Lo vigila guarda_rebaje().
t_anillo           = 14;
// Cara vista. La foto de referencia da 12-24 ESTIMADO; el minimo lo pone la
// franja interior donde asientan las placas de anclaje: cara - rebaje >= 3 D
// del M4 = 13.5, o sea cara >= 19.5.
cara_anillo        = 20;
// Cuanto solapa el acrilico bajo el labio (en el plano). Con menos de 5 el
// labio no lo retiene.
rebaje_anillo      = 6;
// Cuanto queda atras la cara del PMMA respecto a la cara vista. Rango
// ESTIMADO 3-7 de la foto; el minimo, para que el labio tenga cuerpo.
rehundido_acrilico = 3;
// Chaflan de las dos aristas de la cara vista, silueta y ventana. Rango
// ESTIMADO 1-3 de la foto. Es lo que hace que la arista brille.
chaflan_anillo     = 1.5;
// LA PLACA DE ANCLAJE DEL RIEL. El eje del M4 de cada riel cae a 15.90 de la
// silueta (medido), en la zona del rebaje donde el anillo solo tiene 3 mm de
// labio: el tornillo no puede atravesar la cara vista. Va a una placa sobre
// la franja interior, con dos M4 a rosca ciega en el anillo. Mide 6 y no 4
// porque la cabeza del M4 del riel (boton ISO 7380, 2.2 de alto) tiene que
// quedar DENTRO de la placa: debajo hay acrilico hasta z = 13.2. Cajeado
// de 8 x 2.5 y quedan 3.5 de placa bajo la cabeza. Ruling R1 del plan.
t_placa            = 6;
// Junta de asiento entre el labio y la cara del PMMA: nunca aluminio contra
// acrilico. NO absorbe la tolerancia del espesor -- eso lo hace la
// profundidad del rebaje --, solo evita el contacto y precarga.
t_junta_asiento    = 1;
// Holgura del acrilico dentro de su rebaje, por lado.
hol_costado        = 0.5;
// Diametros de BROCA de las roscas ciegas. El M4 sale de la hoja de Tiptop
// que ya citaba d_M4_paso ("M4 Tapping To 3.3"); el M5 es el de ISO 262.
// Las roscas se dibujan a este diametro en costilla_dorso_2d y la
// profundidad va en el pliego: un DXF no sabe decir "a 10 mm".
d_M4_rosca         = 3.3;
d_M5_rosca         = 4.2;
// Clips de retencion del acrilico hacia dentro: pletina de 4 sobre la franja.
t_clip             = 4;
// LO QUE ESTE BLOQUE SUSTITUYE, y va escrito porque cada cota tenia su cuenta:
// fueron ala_costilla = 27 (la banda de chapa, derivada del M4 de la fila 1U a
// 1.5 D del canto de la ventana), ala_doblez = 16 (el ala que tapaba el canto
// del PMMA sobre un apilado de 13.5), cierre_p3_gap = 0.5 (la luz de raiz del
// rip soldado de P3), L_casquillo = 9.5 y t_junta = 4 (el casquillo que
// cruzaba el acrilico y la junta que se comia su juego), todas hasta el
// 2026-08-28. Se las llevo la pletina: no hay ala que doblar, ni esquina que
// soldar, ni acrilico que atravesar.
// Radio interior del plegado. Conserva el nombre pero desde el 2026-08-28 es
// el de LOS TRES MIEMBROS y no el de la costilla: la costilla es pletina
// fresada y ya no se pliega. Misma regla que el chasis de acero -- r = t,
// plegado al aire -- pero con SU espesor, que es otro: la costilla fue
// aluminio de 3 y esta chapa es 6082-T6 de 1.5; el chasis sigue siendo acero
// de 1.5. El radio 3 queda en 2t para no agrietar el T6. SUPUESTO, lo confirma
// el taller de plegado igual que los tres del chasis.
radio_doblez_costilla = 3;
// paso_tira MURIO el 2026-08-26, el mismo dia que nacio. Era el paso de los
// M3 que cosian la tira a la costilla, calculado contra el deslizamiento de la
// junta (34 mm) y no contra la resistencia del tornillo (109). Todo ese
// calculo se lo llevo el plegado: no hay junta, asi que no hay cortante que
// transmitir ni 78 M3 que comprar. La cuenta se conserva en la spec por si
// alguna vez vuelve una junta atornillada a este case.
// Holgura de montaje del Z-Rail. NACE CON LA COSTILLA y no antes: hasta el
// 2026-08-26 ancho_util no era un hueco sino una CONSECUENCIA -- los costados
// se separaban lo que midieran las piezas que van de cara a cara --, asi que
// "holgura" no tenia sujeto. Con el marco si lo tiene: el ala de la costilla
// es un plano y las transversales fijan la separacion, o sea que el riel tiene
// que caber en lo que quede. 0.15 por lado, la misma cifra que hol_piel.
hol_riel        = 0.30;
// ancho_total NO VIVE AQUI: OpenSCAD evalua en orden textual y esta formula usa
// largo_riel (linea ~604) y t_cheek (~515), que se declaran mas abajo. Aqui
// daba "Ignoring unknown variable" y ancho_total salia undefined -- sin error
// de export, solo geometria vacia. Esta al final del fichero, detras de sus
// dependencias.
// CARA vs PANEL. Hasta el 2026-08-17 eran el mismo numero y por eso la puerta
// de EUROrack estaba en rojo: con la cara valiendo 128.5 y los railes a 27 de
// cada punta, los railes quedaban a 74.5 y un modulo 3U NO atornilla.
//
//   alto_cara_*  = el TRAMO DEL PERFIL del costado. Es lo que dibuja la
//                  silueta y donde se atornillan los railes.
//   alto_panel_* = la PCB de aluminio que se monta encima. Es lo que
//                  consume build_template.py y lo unico que ve el fabricante.
//
// LAS DOS FILAS SON 3U desde el 2026-08-17 (antes la de arriba media 190, la
// "altura de panel de la tesis"). Un panel 3U mide 128.5, y lo que manda no es
// ese numero sino la SEPARACION ENTRE RIELES, y con el Z-Rail esa cota NO LA
// PONE EL RIEL: la ponemos nosotros al taladrar el costado. El Z-Rail es una
// barra lisa con una pletina roscada continua (M3 cada 5.08 a todo lo largo),
// asi que acepta la separacion que se le de. Los 123.00 de antes venian de la
// MEJILLA FLAT-S de StudioRacks -- una mejilla ya taladrada, que aqui no se
// compra porque el costado lo cortamos nosotros.
//
// Manda entonces el PANEL, que es lo unico que no se puede mover: un 3U mide
// 128.5 y sus ranuras van a 3.00 de cada canto, o sea 122.50 entre centros.
// De ahi salen las caras:
//
//   alto_cara_inf = 122.5 + inset_inf_frente + inset_inf_valle  = 155.75
//   alto_cara_sup = 122.5 + inset_sup_valle  + inset_sup_remate = 155.0
//
// El de arriba sale mas CORTO aunque lleve el mismo estandar dentro, y es por
// la bisagra: su punta de arriba ya no la remata un 2020 sino el eje de giro.
// Lo que hay entre el canto del panel y el vertice es la PESTANA (marco_sup),
// no un perfil, y por eso caben 11 mm donde antes hacian falta 23.
//
// Los 30.0 / 35.25 mm de acrilico que envuelven el estandar salen de cotas
// fisicas, no de gusto. La fila de abajo bajo 6 mm el 2026-08-17 al voltearse la
// base (ver t_base y alto_frontal) y luego subio 2.5 por la tapa del valle: lo
// que la limita nunca fue el estandar sino lo que tiene encima y debajo.
//
// El riel es FINO a lo largo de la cara (10, la mitad del 2020) pero HONDO hacia
// dentro (27.4, con su eje a 13.7 del panel contra los 10 del 2020), y esa
// profundidad tira de la esquina de abajo del riel hacia abajo. Por eso el
// vertice frontal no baja tanto como el riel adelgaza.
//
// Bisel que sobra alrededor de cada panel (inset - inset_er)
// (14.75 y 9.75 abajo, 16.75 y 8 arriba). Ese ultimo ya no es marco_sup:
// desde el 2026-08-27 marco_sup es el espesor de la meseta de chapa.
//
// YA NO HAY SUPUESTO AQUI. Se asumia que el riel EUROrack iria atornillado
// SOBRE un 2020; el plano de StudioRacks ensena que no hace falta: el riel se
// fija de punta con un M5 directo al acrilico (taladro de 4.5 en su eje). Los
// 2020 se quedan solo en el esqueleto -- base, entrepiso, remate y repisa --,
// que es donde de verdad hacen estructura.
alto_cara_inf   = 155.75; // DERIVADO: 122.5 + inset_inf_frente + inset_inf_valle
alto_cara_sup   = 155.0; // DERIVADO: 122.5 + inset_sup_valle + inset_sup_remate
alto_panel_inf  = 128.5; // PCB 3U EUROrack
alto_panel_sup  = 128.5; // PCB 3U EUROrack: la fila de arriba tambien
// PANEL 1U DE INTELLIJEL. No es una altura elegida para llenar el valle: 39.65
// es la cota del formato, y con inset_er = 3.0 obliga a que los dos Z-Rails
// queden a 33.65 entre centros. guarda_fila_1u() cruza ambas cifras contra la
// boca derivada de paso_horizontal para que ninguna se ajuste por separado.
alto_panel_1u   = 39.65;
// Angulos de cara. El fichero los guarda DESDE LA VERTICAL (convencion del
// board), pero Samuel los especifica DESDE LA HORIZONTAL, que es como se
// miran en el alzado. La traduccion es a = 90 - horizontal:
//   cara de arriba  45 desde la horizontal  ->  45 desde la vertical
//   cara de abajo   55 desde la horizontal  ->  35 desde la vertical
// (los 45 coinciden en las dos convenciones; los 55 NO -- ojo con eso.)
//
// Historia, sobre renders sucesivos del 2026-08-17. Cada grado que se abre un
// panel lo gana en FONDO y lo pierde en ALTO: avanza sen(a) y sube cos(a).
//   12 / 35   -> 233 x 386  (0.60)  estrecho y empinado, no leia a triangulo
//   26 / 49   -> 309 x 340  (0.91)  casi cuadrado, todavia chato
//   49 / 58.8 -> 430 x 268  (1.60)  demasiado tumbado
//   35 / 45   -> el actual, fijado por Samuel en grados de horizontal
angulo_inferior = 35;    // 55 desde la horizontal, cara de procesamiento
angulo_superior = 45;    // 45 desde la horizontal, cara de generacion
// Altura del vertice frontal: donde arranca la cara del panel de abajo.
//
// FUE 45, luego 28, luego 31, y desde el 2026-08-17 es 19. Los cuatro numeros
// salen del mismo sitio: EL TECHO QUE HAY BAJO EL RIEL DEL PANEL, o sea lo que
// la esquina de abajo de ese riel tiene que librar. Todo lo demas se acomoda.
//
// Lo que cambio no fue el riel sino el techo. La base era un SANDWICH -- el
// larguero 2020 (20) con la bandeja del PSU apoyada encima (5) -- y esos 25 mm
// caian justo debajo del riel. Samuel lo llamo por su nombre ("la base esta
// bastante gruesa") y pidio bajarla al grosor del resto de la estructura. Hoy la
// bandeja ES el suelo, una plancha de t_base = 8 a ras del canto de abajo, y los
// dos largueros montan ENCIMA de ella (ver t_base). El techo pasa de 25 a 8.
//
// Y mas tarde ese mismo dia cambio OTRA VEZ, por una idea de Samuel que vale
// 8.45 mm: "el tornillo del riel puede estar literalmente en toda la esquina y
// ser tornillo base tambien". O sea: si la bandeja se RETIRA por detras del riel
// en vez de pasarle por debajo, el riel deja de tener nada que librar y baja
// hasta la propia esquina del case.
//
// OJO: ese M5 acabo siendo el CIERRE de la fila de abajo, no una fijacion fija
// (las dos filas se abren, ver d_visagra). O sea que el nodo de la esquina es
// intermitente. Con la tapa abierta, los costados los ata ahi la bandeja de base
// y sus dos largueros, que sobran para eso.
//
// Las dos condiciones quedan asi:
//
//   1. SUELO. Volvio a ponerlo LA BANDEJA el 2026-08-21, y por eso los 8 de
//      t_base vuelven a la cuenta. La esquina de abajo del riel tiene que
//      quedar por encima del techo de la plancha, con material:
//        alto_frontal + cos(35)*inset_inf_frente
//          >= t_base + holgura_rail + he_er_y(35) + off*sen(35)
//           = 8 + 4 + 11.95 + 8.78 = 32.73
//      Este numero ha ido y venido dos veces. Fue 32.73 mientras la bandeja
//      pasaba por debajo; bajo a 24.73 cuando Samuel la retiro por detras del
//      riel (y esos 8 mm eran 8 mm de aparato); y vuelve a 32.73 ahora que la
//      bandeja LLEGA AL FRENTE y sella el suelo. Se paga lo mismo que se gano
//      entonces, a cambio de que el case cierre por abajo.
//   2. CURVA. La esquina va REDONDEADA EN PUNTA y esa curva se come
//      alto_frontal/2 de cara, asi que el riel no puede arrancar antes:
//        inset_inf_frente >= alto_frontal/2 + rail_er_alto/2 + 3
//
// Se optimizan JUNTAS y ahi esta el truco: la altura del primer piso vale
// alto_frontal + alto_cara_inf*cos(35), y como alto_cara_inf lleva el inset
// dentro, esa altura es (alto_frontal + cos(35)*inset) + una constante. O sea
// que minimizar el piso ES minimizar el lado izquierdo de la condicion 1.
//
// El par (19, 17.5) se apoya en las dos a la vez: la curva justa con sus 3 mm de
// material y 5.29 mm de aire entre la esquina del riel y el techo de la bandeja.
//
// Fue (13, 14.5) hasta el 2026-08-21 y eso dejaba el suelo del case con 37.96 mm
// abiertos por delante -- la bandeja arrancaba a ras del larguero de base
// delantera, que a su vez se retira por detras del riel. Aquel hueco NO era un
// descuido: era la entrada de aire frio, y salia por las ranuras del valle.
//
// Samuel pidio cerrarlo ("estirar la base para que selle completamente por
// debajo"). Cerrarlo obliga a subir el riel, porque su esquina girada bajaba a
// y=4.84 y el techo de la bandeja esta en y=8: el riel se metia 3.16 mm dentro
// del plano del suelo y ninguna plancha plana le pasaba por debajo. Subirlo
// cuesta 8.46 mm de aparato (247.73 -> 256.18) y 1.72 de fondo, porque
// inset_inf_frente va dentro de alto_cara_inf.
//
// Y LA ENTRADA DE AIRE SE MUDA A LA TRASERA, que es lo que de verdad hay que
// mirar aqui: la salida del valle son 7499 mm2 en 102 ranuras, o sea que la
// entrada nueva tiene que dar al menos eso o el aparato respira peor que antes.
// Se mudo CUATRO veces en el mismo dia y acabo abajo del todo en la TRASERA.
// El paseo, por si alguien lo repite: hueco del suelo (no era diseno, era lo que
// sobraba) -> trasera -> suelo otra vez, dibujada en el vuelo de la bandeja ->
// trasera. La tercera murio por una razon que no sale en ningun numero: en el
// vuelo SE VEIA. El acrilico naranja es traslucido y el campo de ranuras se
// transparentaba a lo largo del canto de abajo.
//
// Por eso guarda_aire() no compara areas sino SALTO TERMICO. La entrada llego a
// quedar mas estrecha que la salida a proposito, y lo que hay que exigir no es
// paridad de areas: es que el aparato no se caliente.
//
// Ojo con bajar alto_frontal creyendo que siempre ayuda: la curva se come la
// mitad, asi que cada mm que baja el vertice sube medio el inset y solo se gana
// medio. A 0 la esquina pasa a ser un vertice agudo de 55 grados y su redondeo
// se come 64 mm de cara, cuatro veces mas que la punta de dos arcos de ahora.
//
// Y ojo tambien al reves: cada mm que SUBE el vertice engorda el radio efectivo
// de la esquina de abajo, porque radio_punta va sobredimensionado (400) y lo
// recorta la arista corta, que es alto_frontal. A 13 la curva moria en x=6.49;
// a 19 muere en 9.49. Ahi es donde arranca la bandeja, asi que la curva se paga
// dos veces: en inset y en cuanto suelo queda sin cubrir por delante.
//
// Y esto ya no lo vigila un comentario: guarda_piso() en clearance_budget mide
// la esquina de abajo del riel contra el tope de la bandeja. Derivarlo contra lo
// que no toca costo 0.51 mm de solape en su dia -- se midio contra el lomo del
// larguero y no contra la bandeja que iba encima.
// SUBIO A 20 Y VOLVIO A 19 el mismo dia, y conviene que quede escrito por que.
// Con la bandeja DENTRO del case (plancha de 10 a ras del canto de abajo) el
// riel de panel del frente dejaba de librarla por 0.71 mm y habia que subir el
// aparato. Al pasar el suelo a TABLA DE MADERA BAJO EL MARCO (spec 9.1) el
// suelo interior es y=0: el riel solo tiene que librar holgura_rail y le sobran
// 9.29 mm. Esta cota deja de estar atada al espesor del suelo.
alto_frontal    = 19;
// Fondo del case. UN SOLO plano trasero: el costado es un triangulo
// rectangulo con el angulo recto atras y la hipotenusa quebrada en dos
// tramos (35 arriba, 12 abajo) con el entrepiso en medio (Samuel eligio esta
// silueta el 2026-08-17 sobre el render `costado-VARIANTE-triangulo.png`).
// Antes eran DOS cotas -- prof_inferior 350 y prof_superior 250, con una
// repisa trasera escalonada entre ellas. Esa repisa es justo lo que hacia
// que la silueta se leyera como una bota y no como un triangulo, asi que
// prof_superior se elimino: ya no hay dos fondos que puedan desincronizarse.
//
// MARCO DE REMATE: lo que sobra del fondo detras de la cara de arriba. Este
// es el parametro, y el FONDO del case se deriva de el:
//   fondo = alto_cara_inf*sen(a1) + paso_horizontal
//           + alto_cara_sup*sen(a2) + marco_remate
//
// Va al reves de lo obvio a proposito. El fondo era el parametro y el marco
// salia de la resta, y eso se rompio dos veces: cada vez que se movia un
// angulo o un alto de panel, el marco cambiaba solo y con el la esquina de
// arriba. Con el marco fijo, esa esquina se conserva aunque se muevan las
// proporciones, que es lo que se quiere.
//
// FUE 22 (la meseta de la punta gorda), luego 8 (el canto del techo, tan ancho
// como grueso el costado) y desde el 2026-08-17 es 16. Lo subio una cota fisica,
// no el gusto: EL RIEL DE ARRIBA NO CABIA.
//
// La cara superior necesita DOS rieles como cualquier fila EUROrack, y el de
// arriba va en la linea de tornillo del vertice. Un Z-Rail mide 27.4 de fondo y
// ahi el techo se estrechaba a 8, asi que el riel sobresalia 4.90 mm por detras
// del plano trasero y ademas se comia el larguero de remate. La condicion es
//
//   0.7071*(inset_sup_remate - 34) + marco_remate >= 3
//
// y con (15.75, 8) daba -4.90. Habia tres salidas -- engordar el techo, bajar el
// panel por la cara, o buscar un riel mas plano -- y Samuel eligio la primera:
// es la unica que no mueve la altura y deja el panel rematando en el vertice con
// su pestana de 8. Con 16 la holgura sale +3.10.
//
// Lo que cuesta: el fondo crece 8 mm y el techo, VISTO DE LADO, pasa de canto a
// repisa. De frente no cambia nada -- lo que se ve sigue siendo marco_sup.
//
// OJO, ESTE NO ES EL BORDE QUE SE VE DE FRENTE. marco_remate pertenece al
// COSTADO, o sea que solo existe en los dos laterales y no cruza el ancho. La
// pieza que tapa la meseta va de lado a lado, pero desde el 2026-08-27 es la
// cara horizontal del miembro trasero alto y no una pieza de acrilico.
//
// No es un valor libre: si cambia t_cheek hay que cambiar este a mano (aqui no
// se pueden escribir expresiones, ver la cabecera del fichero). Y baja el
// fondo del case 14 mm de golpe, porque el fondo se deriva de el.
//
// Efecto secundario buscado: con el marco en 8 la esquina de arriba pasa a
// tangente 4 mm en vez de 11, o sea que las dos puntas del techo se vuelven
// casi vivas. Eso ya no importa como antes -- lo que se ve arriba ahora es el
// canto del panel, no un pico de acrilico.
//
// SUBIO A 34 el 2026-08-21, y esta vez lo pide la FORMA y no una cota fisica:
// Samuel quiere la punta de arriba CUADRADA y el case tirado un poco hacia
// atras. Cuesta 16 mm de fondo (275.2 -> 291.2) y no cuesta ni un milimetro de
// alto. Sondeado de 18 a 50 contra clearance_budget: verde en todo el rango, o
// sea que dentro de esa ventana el numero es libre.
//
// (El parrafo de arriba decia 16 y el valor era 18 desde 2507d46, que subio la
// cota sin tocar el texto. Corregido de paso.)
//
// OJO -- ESTE PARAMETRO SOLO NO CUADRA LA PUNTA: LA ENGORDA. Los vertices 4 y 5
// usaban radio_punta, que va sobredimensionado y se recorta a lo que quepa en la
// arista mas corta, o sea a marco_remate/2. Subir el marco sin tocar nada mas
// convierte el techo en una cupula de 17 mm de tangente en vez de 9. Lo que
// cuadra la punta es radio_remate. Los dos van juntos o no van.
// SUBIO OTRA VEZ, a 42, el 2026-08-21, y esta vez NO lo pide la forma: lo pide
// una pieza. La tapa de remate pasa a atornillarse a un larguero 2020 nuevo en
// la arista trasera-superior (el octavo), y ese larguero no cabe en el fondo de
// 34: el BARRIDO del Z-Rail al abrir la tapa de la fila de arriba obliga a que
// su centro este en x >= 286.17. Con marco_remate = 42 el centro cae en 289.22 y
// quedan 3.04 mm de margen -- la misma holgura que el presupuesto ya exige entre
// el chasis y sus largueros. A 40 quedaria 1 mm contra una pieza EN MOVIMIENTO,
// y a 39 cero.
// Y SUBIO A 50 el mismo dia. La razon otra vez es una pieza, no la forma: el
// acrilico de la trasera se frenaba en y=219.73 porque el larguero de remate
// vivia A RAS del plano trasero y le tapaba la banda. Para que la trasera le
// pase por delante, ese larguero tiene que retirarse t_piel -- y ahi vuelve a
// meterse en el barrido del Z-Rail, que es lo que lo mando al plano trasero en
// primer lugar. La unica salida es fondo.
//
// A 50 el larguero cae en x_tr = 289.22 y conserva los mismos 3.04 mm de
// margen contra el barrido. El minimo absoluto son 47 (fondo 304.17) y ahi el
// margen es 0.04 mm contra una pieza EN MOVIMIENTO.
marco_remate    = 50;
// Entrepiso: la franja horizontal entre el tope de la cara inferior y la base
// de la superior -- el "valle del medio" de la silueta. Fue 25 (minimo tecnico
// de R7: por debajo, los dos railes girados se solapaban 2.52 mm), luego 40,
// luego 80 cuando Samuel lo pidio ancho, luego 61.47 y ahora 58.47.
//
// Baja porque era el UNICO sitio del case con holgura de verdad. Auditadas todas
// las cotas derivadas, alto_frontal, inset_inf_frente, inset_sup_remate y
// marco_remate estan a cero o a decimas de su limite; el case ya esta apretado
// contra el riel por todos lados. Aqui no: sobraban 23 mm.
//
// Y ojo con cual es el limite, porque el obvio no es. El hueco SAT entre los dos
// railes del valle tiene 72 mm de margen sobre su minimo -- no manda. Lo que
// manda es que EL LARGUERO DEL VALLE quepa en su ventana: va centrado bajo la
// tapa, y al acortar el valle su centro avanza mas rapido que el borde de la
// ventana. Se tocan en paso_horizontal = 57. A 60 quedan 1.54 mm, que es margen
// de verdad; a 57 quedan 0.04, que es una cota de cuchillo.
//
// Volvio a subir 1.47 mm porque el valle paso a alojar una fila Intellijel 1U:
// su boca tiene que medir 33.65 entre centros + 10.00 de cada Z-Rail = 43.65 mm
// libres entre sus caras, o 49.65 mm entre las caras exteriores de las dos alas
// de chapa. Esa boca sale directamente de paso_horizontal, que ahora gobierna
// guarda_fila_1u(); cada mm que entra aqui suma tambien uno al fondo del aparato.
//
// BAJA 3 mm el 2026-08-28, exactamente lo que las dos alas pierden al pasar de
// t_costilla 3 a 1.5: la boca es paso_horizontal - 2*t_costilla. Sin devolver
// esos 3 mm quedaria en 46.65; con 58.47 conserva los 43.65 de la fila 1U. El
// aparato gana esos mismos 3 mm de fondo por la chapa mas fina.
//
// Lo vigila guarda_escalon(), que ya guardaba la otra holgura de este valle.
paso_horizontal = 58.47;
// Acabado modernista. ESTE ENCABEZADO DECIA "ningun canto del costado es
// esquina viva" Y DEJO DE SER CIERTO EL 2026-08-24: las dos esquinas
// TRASERAS son vivas a peticion de Samuel, para que la trasera y la tapa de
// remate empotren a ras. Ver radio_trasero.
//
// AQUI VIVIA radio_perfil = 14, y se BORRA el 2026-08-24 por dos razones que
// conviene dejar escritas, porque la segunda es la peligrosa:
//
//   1. Se queda sin un solo uso. Su unico cliente era el vertice 6
//      (trasera-abajo), que pasa a radio_trasero.
//   2. SU COMENTARIO MENTIA, y llevaba tiempo haciendolo. Decia "manda en el
//      valle, donde hace la curva que Samuel describio", y el valle no lo
//      gobierna: lo gobiernan radio_pico (vertice 2) y radio_valle (3).
//      Quien quisiera suavizar el valle tocaba este numero y lo que se movia
//      era una esquina trasera. Es justo el parametro que PARECE que hace
//      algo, que es lo que guarda_parametros_vivos() existe para cazar.
// radio_pico = el vertice CONVEXO del valle, donde acaba el tope del panel de
// abajo. Corto a proposito: Samuel lo quiere leyendose como PICO, "el round
// mas durito". No bajar a 0 -- una esquina viva en acrilico de 8 mm es donde
// arranca una fisura.
radio_pico      = 5;
// radio_valle = el vertice CONCAVO del valle, donde arranca la cara de arriba.
// Es el opuesto exacto de radio_pico y por eso no pueden ser el mismo numero.
//
// FUE 30, y con 30 la cara de arriba bajaba recta y METIA EN EL VALLE DE UN
// CORTE: la curva solo se comia 12.43 mm de cara antes de resolver. Samuel pidio
// lo contrario -- "que cuando termine el panel de arriba no corte de una vez al
// valle, sino que haya un poquito mas de caida y que el acrilico haga la curva
// suavemente... le rinde tributo al modernismo de los anos 1880".
//
// La tangente vale radio_valle / tan(67.5), o sea r/2.4142 con la cara de arriba
// a 45. Para alargarla 10 mm hacen falta 54:
//
//   r = 30 -> tangente 12.43, valle plano 64.97
//   r = 54 -> tangente 22.37, valle plano 55.03
//
// Y ahi esta lo bueno: el valle se acorta SOLO, 9.94 mm, que es justo el "a
// cambio el valle se hace mas corto" que pidio. Alto, fondo y ancho no se mueven
// ni una micra -- esta curva no toca ningun vertice, solo la manera de llegar a
// el. La tangente arranca ahora POR ENCIMA del canto de abajo del panel (22.37
// contra 16.75), asi que el acrilico del costado sube barriendo por delante del
// plano de la cara y el panel remata dentro de la curva en vez de contra una
// esquina.
//
// El riel del valle no estorba, y eso hay que decirlo porque parece que si: esta
// esquina es CONCAVA, o sea que el redondeo ANADE material al rincon en vez de
// quitarlo. Verificado subiendo r hasta 80 contra railes_dentro_del_costado.
// Techo real: la funcion lo recorta a min(paso_horizontal, alto_cara_sup)/2 *
// tan(67.5) = 96.6 con el valle en 80.
radio_valle     = 54;
// bombeo = ENTASIS. "Las rectas no son completamente rectas, por poquito, una
// ligera distorsion pero muy ligera". Flecha en MILIMETROS POR CADA 100 MM de
// tramo recto, no absoluta: una flecha fija se ve exagerada en un tramo corto
// y no se ve en uno largo. Se abomba hacia FUERA, asi que crece el bbox --
// por eso la tolerancia de check_dxf tuvo que pasar de 2 a 4 mm. Poner 0 lo
// desactiva.
//
// ESTE COMENTARIO CITABA EL CANTO DE ABAJO ("345 mm, se abomba 1.7") Y ERA
// FALSO POR PARTIDA DOBLE (corregido el 2026-08-24): el canto de abajo esta
// EXENTO -- va en sin_bombeo de perfil_lateral() por las paticas --, o sea que
// es justo el que NO se abomba; y ya no mide 345 sino 308.94. La flecha que de
// verdad se comia la tolerancia era la del CANTO TRASERO, 1.197 mm medidos
// sobre el DXF.
//
// NO SE ABOMBA TODO EL CONTORNO. La regla la aplica sin_bombeo en
// perfil_lateral(): el canto que APOYA CONTRA ALGO PLANO va recto (suelo,
// trasera y meseta del techo), y solo se abomba lo que dibuja silueta. Tras
// eximir los tres, la flecha mayor que queda son 0.779 mm en la cara del panel
// de abajo.
bombeo          = 0.5;
// radio_punta = las esquinas que tienen que leerse como PUNTA redondeada
// (frente-abajo y remate de arriba, 2026-08-17). Va sobredimensionado a
// proposito: la funcion lo recorta al maximo que permite la arista mas corta
// del vertice, y ese maximo es justo la punta. Subirlo mas no cambia nada;
// bajarlo devuelve la cara plana.
//
// Desde el 2026-08-21 ya NO gobierna los dos vertices de arriba: esos pasaron a
// radio_remate. Aqui quedan los dos de abajo -- frente-abajo y arranque de cara
// --, que siguen leyendose como punta redondeada.
radio_punta     = 400;
// radio_remate = el vertice del APEX, el pico de arriba donde la cara superior
// se encuentra con la meseta del techo. Desde el 2026-08-21 se lee CUADRADO y
// no como punta. Es un radio de verdad y no un sobredimensionado: aqui lo que
// se pide es lo que sale.
//
// GOBERNABA DOS VERTICES (apex y fondo-arriba) hasta el 2026-08-24. El de
// fondo-arriba se fue a radio_trasero, asi que aqui queda uno solo.
//
// 2 y no 0 a proposito, y esta razon SI se sostiene para este vertice: es el
// radio que el issue #45 pide para las esquinas de panel, asi que case y
// paneles rematan con el mismo canto. Queda ademas por encima del minimo de la
// fresa (radio 1.5 con la de 3), o sea que el taller lo saca sin cambiar util.
radio_remate    = 2;
// radio_trasero = los DOS vertices del plano trasero -- fondo-arriba (5) y
// fondo-abajo (6). CERO: esquina viva.
//
// Lo pidio Samuel el 2026-08-24: "quiero que sean cuadradas tambien para que
// empotre perfectamente entre las piezas". Y era un desajuste medido, no una
// impresion. Sobre el DXF que va al taller, el costado se metia hacia adentro
// del plano trasero:
//
//   fondo-abajo (radio_perfil 14)  ->  14.004 mm en y = 0
//   fondo-arriba (radio_remate 2)  ->   2.004 mm en y = 256.18
//
// La trasera es un rectangulo de 528.020 x 248.184 que baja hasta y = 0 y con
// ESQUINAS VIVAS (medido: 2 puntos por esquina en el DXF). O sea que su esquina
// de abajo quedaba colgando 14 mm por fuera de la silueta del costado. Con 0
// el desajuste es 0.000 en las dos.
//
// SE DEROGA AQUI UNA REGLA ESCRITA, y por eso va con su porque en vez de
// saltarsela en silencio. radio_remate decia "2 y no 0: una esquina viva en
// acrilico colado de 8 mm es donde arranca una fisura". Lo que se sostiene de
// esa regla y lo que no:
//
//   SE SOSTIENE en los vertices CONCAVOS y en las ranuras. Es donde el
//   material tiene que rodear un rincon y donde el PMMA es notch-sensitive.
//   Eso lo sigue vigilando guarda_fresado() (concavo minimo 54.0 contra la
//   fresa de radio 1.5) y no lo toca este cambio.
//
//   NO SE SOSTENIA COMO REGLA GENERAL, y el propio repo ya lo demostraba: la
//   TRASERA se corta con las cuatro esquinas vivas en acrilico de 8 mm desde
//   que se empotro. La regla ya no se aplicaba pareja; lo unico nuevo es
//   decirlo.
//
// LO QUE SI SE ACEPTA, dicho para que no sorprenda al desembalar: una esquina
// viva CONVEXA en PMMA de 8 mm se DESPORTILLA si se golpea, y la de
// fondo-abajo esta a ras del suelo, que es justo donde el case roza al
// arrastrarlo por una mesa. Es riesgo de manipulacion, no de rotura en carga.
// Si aparece en el prototipo, el remedio NO es volver al radio -- es un chaflan
// de 0.5 x 45, que mata el filo sin devolver el hueco contra la trasera.
radio_trasero   = 0;
// CHAFLAN de toda arista VISTA. 0.5 x 45 grados.
//
// NO ES GEOMETRIA DE ESTE MODELO y por eso no aparece en ningun DXF: un
// fichero de corte 2D no sabe decir "y ademas matale el filo". Es cota de
// PLIEGO, y vive aqui para que tenga puerta y no se pierda en un correo.
//
// POR QUE EXISTE. El 2026-08-24 las dos esquinas traseras pasaron a VIVAS
// (radio_trasero, arriba) para que la trasera empotre a ras, y ese mismo dia
// se decidio canto DIAMANTADO. Arista viva mas canto pulido = se desportilla
// al primer roce, y la de fondo-abajo esta a ras del suelo, justo donde el
// case roza al arrastrarlo por una mesa. El chaflan resuelve el filo SIN
// devolver el hueco contra la trasera, que es lo que costaba el radio.
//
// 0.5 y no menos: por debajo de 0.3 el taller no lo ejecuta como chaflan, lo
// redondea. Y no mas: en la tapa del valle (3 mm) un chaflan grande deja el
// canto en filo otra vez por el otro lado, porque se come las DOS caras.
// Lo vigila guarda_chaflan() por los dos extremos.
chaflan         = 0.5;

// --- materiales ---
// LA TAPA DEL VALLE ES DE ALUMINIO, Y ESTE PARAMETRO SE LLAMABA t_valle.
// Cambio el 2026-08-25 y el nombre viejo mentia: era el espesor de UNA sola
// pieza -- la tapa del valle -- y el README ya lo decia con incomodidad ("un
// espesor entero para UNA pieza, cosa del pliego").
//
// POR QUE CAMBIA. Medido: la tapa apoya sobre una banda de rail (20 mm) y mide
// 66.5 de fondo, o sea que el 70 % de la pieza vuela -- 23.24 mm a cada lado.
// En acrilico de 5 eso da, con 200 N repartidos en 100 mm de mano, 11.2 MPa
// contra los 10 de fluencia del PMMA (#106); y si la mano reparte solo 50 mm
// (el canto, no la palma) fluye a 90 N. Era la pieza mas floja del case con
// diferencia, y es la unica superficie HORIZONTAL, o sea donde se apoya quien
// se levanta.
//
// POR QUE ALUMINIO Y NO ACRILICO MAS GRUESO: subir a 6 esta BLOQUEADO -- la
// tapa invade el barrido del riel y la fila de abajo pasa de abrir 180 a 39.5
// grados. Ensanchar el larguero tampoco: un perfil de 30 entra por 0.24 mm
// (por debajo de la tolerancia de la propia extrusion) y uno de 40 no entra,
// se pasa 4.76. El aluminio de 3 resuelve por rigidez especifica en vez de por
// espesor, y ADEMAS devuelve 2 mm de barrido en vez de comerselo.
//
// Y NO ROMPE EL LENGUAJE: los paneles de modulo ya son PCB de ALUMINIO a los
// dos lados de esta banda. Una tapa de aluminio entre dos filas de aluminio se
// lee como que la banda central pertenece a los paneles, no como un parche.
//
// Lo que se lleva por delante, y es ganancia: la unica linea de BOM de 5 mm.
// El cuerpo de acrilico queda con UN solo espesor, 8.
t_valle    = 3;    // ALUMINIO. Ver guarda_valle(); el material va en el PLIEGO
t_cheek    = 8;    // costados portantes
// SUELO del case. La bandeja de base dejo de ser una plancha del cuerpo el
// 2026-08-17: ya no se apoya ENCIMA de los dos largueros -- 20 + 5 = 25 mm de
// sandwich justo debajo del riel del panel -- sino que pasa a ser el propio
// canto de abajo, con los largueros montados sobre ella.
//
// LA ESTRUCTURA NO PIERDE NADA y conviene decirlo claro: son los mismos dos 2020
// cruzando el mismo vano de 528, y la bandeja sigue atornillada a ellos cada
// 100 mm; lo unico que cambia es por que cara. Pero el techo que el riel tiene
// que librar baja de 25 a 8, y con el baja el case entero 17 mm.
//
// Sube de t_valle a t_cheek porque ahora es cara vista y de apoyo: el mismo 8
// del costado, de la pestana y del marco de remate. Es lo que pidio Samuel --
// "el mismo grosor que todo el resto de la estructura".
//
// No es un valor libre: si cambia t_cheek hay que cambiar este a mano (aqui no
// se pueden escribir expresiones, ver la cabecera del fichero).
// LA TABLA. Dejo de ser una plancha DENTRO del case el 2026-08-27 y paso a ser
// una TABLA DE MADERA MACIZA BAJO EL MARCO -- la misma pieza que el zocalo, que
// hasta entonces eran dos (spec 9.1, decidido sobre la foto de referencia).
// Ocupa y = -t_base .. 0: su cara de arriba ES el suelo interior y su canto
// sobresale del cuerpo. Las dos costillas se le apoyan encima y las cuatro
// paticas se le atornillan por debajo, o sea que el peso del case va de costilla
// a pata casi en linea recta.
//
// 18 SALE DE LA FLECHA. Lo que la dobla no es el peso del case sino el chasis
// del PSU sentado en medio del vano entre las dos costillas, que es ancho_util
// y NO una constante: valia 528.62 y desde el 2026-08-28 son 540.62, un 2.3 %
// mas de luz y un 7 % mas de flecha, porque va con L^3.
//
// Con la tabla de 327.41 de ancho, 200 N y E = 11000 MPa: 16 da 0.536, 18 da
// 0.376 y 20 da 0.274, contra un techo de 0.60. Los tres pasan y 18 es ademas
// espesor de tabla de catalogo, asi que se queda: el margen es lo que se
// compra, no el aprobado justo.
//
// ESTA TABLA NO ES EL NUMERO VIVO -- se queda vieja en cuanto se mueva el
// ancho, la especie o el fondo. El vivo lo imprime guarda_piso() en cada
// corrida, con esta misma formula y con el vano de verdad:
//   suelo: TABLA DE MADERA MACIZA t=18 bajo el marco, 327.41 x 588.62 ...
//     con 200 N en medio del vano de 540.62 cede 0.376 mm (techo 0.60, E 11000
//     MPa a favor de veta)
//
// MACIZA, con AGUJEROS ALARGADOS en Z. Es la unica pieza de madera del case que
// CARGA, y una tabla maciza de 540.62 mm a contraveta se mueve milimetros con la
// estacion. El marco de aluminio no se mueve: si la fijacion es rigida, o se
// raja la tabla o se sueltan los tornillos. Lo vigila guarda_zocalo().
t_base     = 18;

// Modulo de elasticidad de la madera A FAVOR DE VETA. 11000 MPa es nogal o arce
// -- el rango de manual para frondosas de densidad media va de 10000 a 12000.
// SUPUESTO DECLARADO hasta que la especie este elegida en el pliego: roble da
// 12000 (mejor) y el contrachapado 8000 (peor, pediria 20 mm).
E_madera   = 11000;

// Lo que la tabla sobresale del cuerpo por los cuatro lados. Es cota de MIRAR,
// no de calcular: nada cuelga de ella. Sale de la foto de referencia, donde el
// zocalo asoma poco -- lo justo para leerse como base y no como bandeja.
vuelo_zocalo = 10;

// Carrera del agujero alargado, por lado, en Z. La tabla mide ancho_total +
// 2*vuelo_zocalo a contraveta; una frondosa se mueve del orden del 0.25 % de su
// ancho entre invierno y verano en interior, o sea ~1.4 mm sobre 570. Se dan 2.5
// por lado (5 de carrera total) para cubrir un ambiente peor que el supuesto.
// El tornillo del medio de cada costilla va REDONDO: la tabla tiene que crecer
// hacia los dos lados desde un punto fijo, no arrastrarse hacia uno.
holgura_veta = 2.5;
t_panel    = 1.6;  // PCB de aluminio, espesor estandar JLCPCB
// EL PROCESO ES FRESADO CNC, NO LASER (decidido el 2026-08-17). Y por eso
// este numero vale CERO, que no es lo mismo que "sin calibrar":
//
//   laser    quema una franja centrada en la linea. El hueco sale mas grande
//            que el dibujo, nadie te dice cuanto, y hay que restarlo a mano.
//            Ahi kerf es NEGATIVO y se mide con el cupon.
//   fresado  el CAM aplica compensacion de radio de herramienta como parte
//            normal del trabajo. La pieza sale a la cota del dibujo, con la
//            tolerancia de produccion del taller (Schaeffer publica 0.05-0.10
//            mm). No hay nada que compensar aqui: kerf = 0.
//
// Si el proceso volviera a laser, esto vuelve a ser negativo Y hay que medirlo
// -- ademas por espesor, porque la franja no es la misma en 5 que en 8 mm.
// El procedimiento del cupon sigue en README §"Procedimiento del cupon".
// ASIMETRIA DELIBERADA: el kerf se aplica a los HUECOS (agujeros, ranuras,
// recortes), no a los CONTORNOS exteriores. Cada plancha sale por tanto ~0.2
// mm mas chica que el nominal: en todas las piezas de este case eso es
// holgura a favor (auditado pieza por pieza en el review final de rama), y
// ninguna lleva encaje macho donde restaria. Si alguna vez se dibuja una
// lengueta que deba entrar apretada, hay que aplicarle kerf a su contorno.
kerf       = 0;

// Teselado de circulos. VIVE AQUI, no en sam17_case.scad, porque todo .scad
// que incluya params lo hereda: coupon.scad lo perdio cuando estaba alla y
// sus agujeros salieron PENTAGONOS (5 segmentos, error de forma 0.33-0.48 mm
// contra peldanos de 0.1 mm) -- la pieza de calibracion no podia calibrar, y
// peor, devolvia un kerf errado con evidencia fisica que lo respaldaba.
// clearance_budget.py lo ignora: su regex pide `\w` y `$` no lo es.
$fn = 48;

// --- sistema de paneles (spec §6) ---
rail            = 20;   // perfil 2020, SOLO esqueleto (base, entrepiso, remate, repisa)
// RIEL EUROrack: Z-Rail de TIPTOP AUDIO. Cotas de su hoja de datos oficial
// (tiptopaudio.com/manuals/z-rails.pdf, seccion A "PROFILE", leida el
// 2026-08-17).
//
// ESTE FICHERO ESTUVO DIBUJADO CONTRA OTRO RIEL. Hasta el 2026-08-17 la seccion
// salia de los planos que mando StudioRacks, y el riel que se compra es el
// Tiptop. No es el mismo perfil: 27.40 de fondo contra 23.80. Un case entero
// dimensionado contra la pieza equivocada -- y con +0.50 mm de margen medido en
// esa cota, o sea que no habia holgura ninguna que lo absorbiera.
//
//   rail_er_alto   10.00  a lo largo de la cara. Es la cota que NO cambio al
//                         pasar de un fabricante al otro: los dos presentan
//                         10 mm de canto al panel, que es lo estandar.
//   rail_er_fondo  23.80  hacia dentro del case. La hoja la acota como la
//                         dimension larga de la seccion.
//   rail_er_eje    14.30  del taladro de punta a la cara que toca el panel.
//                         La hoja lo acota al reves -- 9.50 al canto de
//                         DETRAS --, y 23.80 - 9.50 = 14.30.
//
// El taladro NO esta centrado en el fondo (14.30 de 23.80), pero SI en el alto
// (5.00 de 10.00): la hoja acota 5.0 desde el canto de arriba, y por debajo
// 3.8 + 1.2 = 5.0 hasta el otro. Eso importa porque es lo que permite que el
// M4 de punta y la linea de tornillos del panel caigan a la misma altura.
//
// EL TALADRO DE PUNTA ES M4, NO M5. La hoja lo dice con todas sus letras:
// "M4 Tapping To (/)3.3". O sea que viene ROSCADO en el propio aluminio -- el
// costado solo necesita agujero de PASO (d_M4_paso) y el tornillo muerde el
// riel directamente, sin tuerca ni inserto. Los M5 se quedan para el esqueleto
// 2020, que es otro herraje.
//
// LO QUE SIGUE SIN CONFIRMAR: cual de las dos caras de 10 mm mira al panel.
// Se toma la del canal (el que lleva la pletina roscada), que es la unica que
// puede recibir los M3 del modulo -- se ve en la foto de la hoja que el canal
// abre de costado y no por la cara ancha. Si con el riel en mano resultara ser
// la otra, rail_er_eje pasa de 14.30 a 9.50 y hay que re-derivar.
// Largo de catalogo del riel. Es la cota que fija el ancho del case (ver
// ancho_total): 104 HP x 5.08 = 528.32. No se puede "ajustar" -- o se compra
// otro largo o se corta el riel, y cortarlo se lleva la punta por donde se fija.
largo_riel      = 528.32;

// ANCHO TOTAL, DERIVADO. Va justo detras de largo_riel porque OpenSCAD evalua
// en orden textual y esta formula necesita a los cuatro ya declarados.
//
// Estuvo escrito a mano (544.32) mientras el comentario de arriba daba la
// formula, asi que ancho_util coincidia con el largo del riel por CASUALIDAD
// ARITMETICA y no por derivacion -- la clase de cota que parece verificada y
// nunca se comprobo. Antes de invertir las capas habia tres cosas metidas en
// ese hueco: el riel, su
// holgura de montaje y las dos alas de costilla. clearance_budget.py calcula
// esta misma formula y se niega a arrancar si vuelve a ser literal.
// Con la inversion cambio quien fijaba el hueco: el acrilico dejo de fijarlo y
// paso a fijarlo el casquillo que lo atraviesa, asi que 2*t_cheek salio de la
// derivacion y entro 2*L_casquillo. Duro dos dias.
//
// DESDE EL 2026-08-28 el hueco entre anillos lo fijan las PLACAS de anclaje
// (t_placa por lado, entre el riel y la cara interior del anillo) y el propio
// anillo. El casquillo que cruzaba el acrilico murio con el apilado: el
// acrilico ya no esta en esta cuenta porque va DENTRO de la ventana.
ancho_total     = largo_riel + hol_riel + 2*t_placa + 2*t_anillo;
rail_er_alto    = 10;
rail_er_fondo   = 23.8;
rail_er_eje     = 14.3;
// Tornillo de panel, distancia al borde del panel. FUE 5 y era imposible:
// el rail 2020 va ALINEADO con la cara, asi que se extiende +-rail/2 = +-10 mm
// a lo largo de ella. Centrado a s=5 ocupaba de s=-5 a s=+15, o sea que
// asomaba 5 mm POR DELANTE del arranque de la cara, donde no hay acrilico
// ninguno. Lo destapo `railes_dentro_del_costado()` en check_dxf: tres de los
// cuatro railes de panel se salian de la pieza (2.7 mm por el frente, 2.0 por
// el valle, 1.2 por el remate). Ventana valida: >= 10 para que el rail quepa,
// y <= 13 para que el tornillo siga cayendo dentro de la boca de la ranura
// (~6 mm, o sea +-3 mm del centro de la cara). 10 lo centra exacto.
//
// Hoy no manda esa ventana sino la curva de cada esquina (ver la tabla de los
// cuatro insets, abajo). El del frente ademas va emparejado con alto_frontal:
// mover uno sin el otro sube el case o rompe la holgura sobre la bandeja.
// CUATRO INSETS, uno por punta de cara. Hubo un `inset_tornillo` que servia
// para todo y no daba: cada punta llega a una esquina distinta del contorno, y
// lo que manda en cada una es CUANTO ACRILICO SE COME SU CURVA. El patron es
// siempre el mismo -- tangente de la curva + rail/2 + material -- y lo unico
// que cambia es la tangente:
//
//   punta               curva            tangente  + riel/2 + mat = inset
//   ------------------  ---------------  --------  -------------------------
//   inferior / frente   punta redondeada    6.5      + 5 + 3.0   = 14.5
//   inferior / valle    pico (r=5)          2.6      + 5 + 8.15  = 15.75*
//   superior / valle    valle (r=30)       12.4      + 5 + 2.1   = 19.5
//   superior / remate   -- lo fija la PESTANA ---  8 + 5 = 13
//
// La cuarta se sale del patron: no la fija ninguna curva. La fija que la pestana
// APOYE en el canto de arriba del riel, o sea marco_sup + rail_er_alto/2. Y de
// ella cuelga marco_remate, que tiene que dar para que el riel quepa detras del
// vertice: >= 3 - 0.7071*(13 - 34) = 17.85.
//
// ESTA LINEA LLEVA RIEL, y hasta el 2026-08-17 no lo llevaba: la ocupaba el eje
// de la bisagra. Samuel lo cazo preguntando lo obvio -- "el riel superior del
// segundo row deberia ir en la punta de lo alto del triangulo". Y tenia razon
// dos veces, porque ademas de faltar el riel, el otro extremo de esa cara
// estaba atornillado con M5 a los costados: la tapa estaba empernada y no podia
// abrir. Ver marco_remate y d_visagra.
//
// La junta de 5 era el barrido de la tapa y ya no lo es: la pestana viaja CON el
// panel (las dos son tapa), asi que entre ellas no hay movimiento relativo. Se
// queda de junta de sombra, la misma que llevan las pieles flotantes.
//
// Las tangentes NO son parametros: salen del radio y del angulo del vertice.
// Si se mueve un radio hay que rehacer la columna, y el que avisa es
// cuerpos_dentro_del_anillo() en check_dxf (railes_dentro_del_costado() hasta
// el 2026-08-28), que lee el contorno del DXF -- desde esa fecha el de la
// COSTILLA, que es quien lleva la silueta, y no el del acrilico.
// Subio de 14.5 a 17.5 el 2026-08-21 y NO por su propia condicion: lo arrastro
// alto_frontal. La regla es inset >= alto_frontal/2 + rail_er_alto/2 + 3, y con
// el vertice en 19 eso da 17.5 clavado. Los 3 mm van dentro de alto_cara_inf,
// que es DERIVADO, asi que hay que recontarlo ahi tambien -- por eso el case
// gano 1.72 de fondo ademas de los 6 de alto.
inset_inf_frente = 17.5;
// (*) El del valle NO lo pone su curva desde el 2026-08-17: por la curva
// bastarian 10, y lo que manda es LA TAPA DEL VALLE. Esa plancha va a ras del
// plano del valle, o sea con su cara de abajo a t_valle por debajo, y justo
// ahi asoma la esquina de arriba del riel del valle de la cara de ABAJO.
//
// Fue 10 (0.013 mm de hueco: las dos piezas rozandose por casualidad aritmetica)
// y luego 12.5, que daba 2.06 mm limpios PARADO. Y ahi estaba la trampa: Samuel
// pidio que las DOS filas se abran, y esa cota hay que medirla GIRANDO.
//
//   parado:  hueco = cos(35)*i + sen(35)*(t_panel+rail_er_eje) - t_valle
//                    - he_er_y(35)          he_er_y = 11.95
//   girando: lo mismo pero contra el RADIO DE GIRO del riel = 14.58
//
// El riel gira sobre su propio M5, asi que lo que barre no es su esquina sino su
// circulo. Con 12.5 el hueco parado era +2.06 y el de barrido -0.57: la fila de
// abajo abria 24 grados y se comia la tapa del valle. La holgura estatica mentia
// y solo lo dijo el barrido.
//
// 15.75 deja 2.09 mm de barrido y la fila abre entera. Cuesta 2.66 mm de alto y
// 1.86 de fondo. La alternativa gratis era quitar la tapa del valle (5 tornillos)
// antes de abrir abajo; se pagan los milimetros porque "que se abran las dos" fue
// pedido explicito.
inset_inf_valle  = 15.75;
inset_sup_valle  = 19.5;
inset_sup_remate = 13;
// Cotas del PANEL (no de la cara). El horizontal es de estandar: primer taladro
// a 7.5 mm del canto izquierdo y paso multiplo de 5.08 (1 HP), verificado el
// 2026-08-17 contra midisoft.de y exploding-shed.com.
//
// EL VERTICAL YA NO ES DE ESTANDAR, ES DEL RIEL QUE SE COMPRA. Doepfer pone el
// taladro a 3.0 del canto (122.50 entre centros) pero el riel de StudioRacks
// mide 123.00, asi que aqui van 2.75. Es la resta y no una eleccion:
//   inset_er = (alto_panel_inf - sep_railes_inf)/2 = (128.5 - 123.0)/2
//
// CONSECUENCIA QUE HAY QUE SABER: un modulo de terceros con sus taladros a 3.0
// queda 0.25 mm descentrado por lado contra nuestros rieles. En un taladro de
// 3.2 sobre M3 hay 0.2 mm de juego radial, asi que entra pero justo. Con tuercas
// deslizantes (la opcion de 35 GBP) el juego horizontal es libre y solo aprieta
// en vertical; con insertos roscados (41 GBP) queda fijo en los dos ejes.
inset_er        = 3.0;   // DERIVADO: (128.5 - 122.5)/2, la ranura del panel 3U
inset_er_x      = 7.5;
// 1 HP. Es la unidad del rack y por tanto la del case entero: largo_riel son
// 104 HP y el campo de ranuras de la tapa del valle va registrado a esta malla,
// no a la plancha. Aqui como numero para que no ande suelto en tres sitios.
hp              = 5.08;
// Lo fija el PANEL, no el riel: el Z-Rail lleva pletina roscada continua y
// acepta la separacion que se le de al taladrar el costado. Un panel 3U mide
// 128.5 con las ranuras a 3.00 de cada canto -> 122.50 entre centros (Doepfer).
// FUE 123.00 y era la cota de la mejilla FLAT-S de StudioRacks: una mejilla ya
// taladrada, que no se compra porque el costado lo cortamos nosotros.
sep_railes_inf  = 122.5;
sep_railes_sup  = 122.5;
holgura_rail    = 4;    // separacion minima entre railes vecinos (fix solapes)

// --- esqueleto y herrajes ---
n_bulkheads      = 2;    // costados exteriores (3 si el vano flexa, spec §11)
// RIGIDEZ DEL COSTADO. Entran el 2026-08-25 con el retiro del entrepiso
// delantero: el case baja de cinco largueros a cuatro y el costado se queda
// con cuatro M5 en vez de cinco, asi que el vano sin apoyo crece y eso deja de
// poder darse por bueno a ojo.
//
// La puerta es guarda_costado() en check_dxf.py -- y va ahi, y no en
// clearance_budget, porque mide sobre el CONTORNO Y LOS TALADROS REALES de
// costado_2d.dxf, no sobre una copia de la geometria en Python.
//
// POR QUE FLECHA Y NO TENSION: la tension no es el limitante ni de lejos. Con
// 200 N sobre el vano actual el costado trabaja a 6.56 MPa contra los 10 de
// fluencia (#106), y para llegar al umbral el vano tendria que valer 642 mm --
// mas que la pieza entera, porque la tension de una placa empotrada crece con
// el LOGARITMO del vano. Lo que se nota con la mano es la flecha, que crece
// con el CUADRADO. Un costado que se hunde al empujarlo se siente barato
// aunque no rompa nunca, y este case se mide por acabado.
// Modulo elastico del aluminio. Comun a todas las aleaciones -- el limite
// elastico SI depende de cual, pero el modulo no. Vive AQUI y no solo en
// clearance_budget.py desde el 2026-08-26 porque el .scad tambien lo necesita:
// es quien deriva que tramos de la costilla llevan ala doblada, y esa
// derivacion tiene que dar lo MISMO en los dos lados o el DXF y el modelo se
// separan. clearance_budget lo comprueba al arrancar.
E_aluminio       = 69000;
carga_mano       = 200;  // N. Alguien apoyandose, el mismo caso de carga con
                         // el que ya se acoto la trasera (rev. 9: 0.6 mm)
flecha_costado_max = 0.6;// mm bajo carga_mano. El techo NO es nuevo: es el
                         // mismo que el proyecto ya acepto para la trasera en
                         // su vano de 211.73. Hoy sale 0.38
d_M3_paso   = 3.4;  // agujero paso M3 (ISO holgura media)
d_M4_paso   = 4.5;  // agujero paso M4: standoffs de las pieles Y los seis
                    // rieles EUROrack, cuyo taladro de punta viene roscado M4
                    // de fabrica (hoja Tiptop: "M4 Tapping To (/)3.3")
d_M5_paso   = 5.5;  // agujero paso M5: SOLO el esqueleto 2020, roscado en el alma
// APRIETE DE LOS 20 M3, y la arandela de la que sale.
//
// Hasta el 2026-08-24 la instruccion era "apretar hasta marcar, NO hasta
// fisurar" (README, procedimiento del cupon) y la spec §11 admitia que "el
// par maximo antes de fisura no esta medido". Veinte tornillos VISIBLES
// apretados a tacto sobre acrilico son veinte puntos de craquelado.
//
// EL NUMERO LO PONE LA ARANDELA, no el tornillo: lo que decide si el PMMA
// craquela es cuanta area reparte la precarga. Con el umbral de 10 MPa del
// #106 y T = 0.2*F*d:
//
//   arandela   area apoyo   precarga a 10 MPa   par maximo
//   d9           54.5 mm2       545 N            0.33 N*m
//   d12         104.0 mm2      1040 N            0.62 N*m
//   d16         191.9 mm2      1919 N            1.15 N*m   <- esta
//
// SE ELIGE d16 POR DOS RAZONES QUE VAN JUNTAS. Es la unica que deja el par
// por encima de 1 N*m, que es donde una llave dinamometrica de 1/4" empieza
// a existir -- por debajo hace falta destornillador dinamometrico de
// precision, y "apretar con cuidado" nos devuelve al tacto. Y YA ESTA EN EL
// BOM: es la misma arandela ancha de los cuatro ejes de giro, asi que la
// familia de herraje baja de dos arandelas a una. Consistencia de herraje es
// justo lo que separa un producto de un montaje.
//
// OJO CON ENGRASAR LA ROSCA: el par se convierte en precarga con coeficiente
// 0.2 en seco y ~0.15 engrasado, o sea que el MISMO par mete un 30% mas de
// precarga y fisura. LOS M3 VAN SECOS.
d_arandela  = 16;   // mm, arandela ancha bajo cada M3 visible
par_m3      = 1.0;  // N*m. Techo por arandela: 1.15
// hol_piel = holgura de AJUSTE de las pieles EMPOTRADAS, por lado.
//
// Sustituye a gap_sombra (5 mm), que era otra cosa: la junta de sombra de las
// pieles FLOTANTES. Hasta el 2026-08-21 las dos pieles colgaban de doce
// separadores, con su cara exterior 10 mm POR DETRAS del canto de los costados
// y 5 mm de aire por los cuatro lados. Samuel pidio que la trasera encaje y
// SELLE, asi que dejan de flotar: se empotran a ras del plano trasero y el
// hueco perimetral pasa de junta de diseno a holgura de montaje.
//
// El numero no lo elige el gusto, lo pone la tolerancia de corte del taller
// (Schaeffer publica 0.05-0.10 mm). 0.15 por lado son 0.30 de juego total en
// 528 mm: entra sin forzar y se lee como junta, no como hueco. Si al ensamblar
// aprieta, esto es lo que sube -- no el ancho de la piel.
hol_piel    = 0.15;
// Espesor de la TRASERA, y solo de ella. Samuel la pidio en 8 el 2026-08-21
// -- misma plancha que los costados y el suelo -- cuando el resto del cuerpo
// todavia colgaba de un espesor generico de acrilico. Ese generico ya no
// existe: desde el 2026-08-25 el PMMA del cuerpo es 8 entero (t_base, t_cheek,
// t_piel) y lo unico distinto es t_valle, que ni siquiera es PMMA. Sigue
// siendo parametro aparte porque de este numero cuelga cuanto se retiran los
// cuatro largueros traseros para que la trasera enrase con el canto.
//
// El efecto secundario que este bloque anotaba y NO resolvia -- que el unico
// cliente del acrilico de 5 mm era la tapa del valle, y comprar una plancha
// entera para una pieza es cosa del pliego -- lo cerro la rev. 20 por el otro
// lado: la tapa paso a aluminio y la linea de 5 mm murio.
t_piel      = 8;
// PATICAS: DE GOMA. Samuel, 2026-08-24 -- "prefiero las gomas solamente,
// pero unas gomas serias".
//
// ESTO REVIERTE LA NOTA DEL 2026-08-17 que decia "METALICAS, torneadas,
// pequenas... No son de goma: eso cambia el BOM y el acabado". Y al
// revertirla, LA SPEC §5 DEJA DE ESTAR EQUIVOCADA: nunca dejo de decir "pies
// de goma bajo la base". Habia una contradiccion de TRES documentos -- este
// fichero decia metal, el README listaba las dos cosas a la vez en dos
// tablas distintas, y la spec decia goma -- y se cierra volviendo al unico
// que no se movio.
//
// LA COTA QUE DECIDE SI SIRVE ES CUANTO SE HUNDE, no la dureza ni el
// diametro. El toroide excita a 100 Hz (#106) y la pata es un muelle: si su
// frecuencia propia cae cerca de ahi, AMPLIFICA en vez de aislar, y le pasa
// a la mesa mas zumbido del que le pasaria el acrilico en seco.
//
//   se hunde   f propia   transmite
//   0.10 mm     49.8 Hz     33 %
//   0.25 mm     31.5 Hz     11 %    <- esta
//   0.50 mm     22.3 Hz      5 %
//   1.00 mm     15.8 Hz    2.5 %
//
// 0.25 es el minimo que deja la f propia a un tercio de la excitacion, que
// es el criterio de manual. Mas blanda aisla mejor y se bambolea mas.
//
// ES REQUISITO DE COMPRA, NO DE DIBUJO: se exige la curva carga-deformacion
// del fabricante. Una goma que no publica esa curva no se puede verificar y
// por tanto no sirve, por seria que parezca.
//
// La altura sale gratis: la entrada de aire se mudo a la trasera el
// 2026-08-21, asi que la separacion al suelo ya no ventila nada y alto_pie
// no entra en ninguna derivacion.
flecha_pie  = 0.25; // mm bajo 22.8 N. DE HOJA DE DATOS, no estimado
alto_pie    = 10;   // sube de 8: la flecha necesita material donde ocurrir
d_pie       = 20;   // sube de 16: area para no aplastarse permanentemente   // diametro; pequeno a proposito
// EJE DE LA TAPA: NO HAY BISAGRA. El eje es EL PROPIO M5 con el que el riel de
// arriba se fija de punta al costado. Samuel, viendo el render: "deberia ser el
// mismo tornillo con el que se atornilla la barra del eurorack no? por que tanto
// rollo?".
//
// Pues si. Ese M5 entra por el costado A LO LARGO DEL ANCHO, que es exactamente
// la direccion que necesita un eje de giro; el riel gira sobre su propio taladro
// y con el toda la cara de arriba. La bisagra continua que hubo aqui hasta el
// 2026-08-17 era una pieza ASUMIDA (nunca vimos una), con dos palas sin decidir,
// que ademas pedia un cierre de techo entre costados que no existe y sacaba un
// nudillo de 8 mm fuera del case. Todo eso se cae de golpe.
//
// Por eso no hay ningun parametro aqui: el eje no se elige, ES centros_rail()[3].
//
// QUE ES TAPA Y QUE ES CASE:
//   tapa  = los 2 rieles de la cara de arriba + sus modulos + la pestana
//   case  = todo lo demas
//
// LOS CUATRO RIELES LLEVAN SU M5 AL COSTADO. Hubo un rato en que el del valle de
// arriba no lo llevaba, con el argumento de que con los dos extremos empernados
// la tapa no gira. Es cierto y es media verdad: de ahi no se sigue dejar el riel
// colgando de nada, se sigue que ese tornillo sea QUITABLE. Samuel lo cazo en el
// render -- "donde esta el tornillo del riel de abajo de la row superior?".
// Papeles:
//   cara de abajo   x2  fijacion, y ya
//   riel de arriba  x2  EJE. De hombro, con arandela, sin apretar
//   riel del valle  x2  CIERRE. De mano: se quitan para abrir, se ponen para
//                       cerrar. Misma geometria que un tornillo fijo, distinta
//                       intencion -- y si lo quieres sin herramienta, en ese
//                       mismo taladro entra un pasador de bola con muelle.
//
// OJO CON LOS PANELES CIEGOS de la fila de arriba: con la tapa CERRADA la sujetan
// los 4 tornillos, pero ABIERTA sus dos rieles solo estan atados entre si por lo
// que haya atornillado de uno a otro, o sea los modulos. Un hueco sin tapar es
// una charnela. Los ciegos no son estetica aqui, son estructura.
//
// LO QUE SE PAGA -- y sale mas barato de lo que parecia. La tapa entera cuelga
// de DOS M5 apoyando en acrilico de 8, pero echada la cuenta son 14.7 N por
// tornillo con una fila llena de modulos (3 kg), o sea 0.33 MPa de aplastamiento
// sobre el costado: el 0.3 % de lo que aguanta el acrilico a compresion. La carga
// estatica no es el problema. Lo que hay que cuidar es el DESGASTE del giro, y
// eso lo resuelve una arandela metalica y un tornillo de hombro, no mas seccion.
//
// SIN CERRAR: el cierre del valle (la tapa no tiene nada que la sujete cerrada) y
// el amortiguador que la deje abierta.
// HISTORICO, HASTA 2026-08-21. PESTANA SUPERIOR: la banda de acrilico que cruzaba por
// encima del canto del panel de arriba, sobre la propia cara. Samuel la pidio
// porque el panel remataba pelado ("no veo esa pestana ... quiero un top marco
// acrilico"), y no la daba marco_remate: ese pertenece al COSTADO y solo existe
// en los dos laterales, no cruza el ancho. Son piezas distintas y las dos miden
// 8 = t_cheek, asi que juntas envuelven la punta de arriba en L.
//
// Se lleva su ancho de la cara: la cara crece marco_sup y el canto del panel
// baja otro tanto, o sea que el case sube marco_sup*cos(45) = 5.7 mm.
//
// ES PIEZA DE TAPA, no de case (2026-08-17): viaja con el panel cuando se abre.
// De ahi que gap_sombra dejara de ser holgura de barrido -- entre la pestana y
// el canto del panel ya no hay movimiento relativo.
//
// YA NO ESTA PENDIENTE COMO SE FIJA (2026-08-17). Samuel: "podemos hacer que
// esta conectara al riel? (atornillada al riel)". Si, pero no por donde parece.
//
// Por la cara del riel donde van los modulos NO SE PUEDE, y la cota es dura: el
// panel 3U lleva sus taladros a 2.75 del canto y el riel mide 10 de alto, o sea
// que por encima del panel solo asoman 5 - 2.75 = 2.25 mm de riel. Una cabeza de
// M3 mide 5.5. No cabe, y no hay como hacerla caber sin mover la separacion de
// 123, que no es nuestra.
//
// Lo que si hay es LA OTRA CARA del riel: la de arriba, la que mira al vertice.
// 27.4 mm de fondo por 528 de largo, plana y libre, y la pestana se le apoya de
// canto. Para eso tiene que TOCARLA -- hasta hoy habia 2.75 mm de aire --, y de
// ahi sale el numero:
//
//   inset_sup_remate = marco_sup + rail_er_alto/2 = 8 + 5 = 13
//
// Y VA EN ESTE SENTIDO, no al reves, por una razon tonta y decisiva: marco_sup es
// el ESPESOR DE LA PLANCHA de la que sale la pieza, porque el M3 la atraviesa a
// lo largo de la cara. Derivar marco_sup de inset_sup_remate daba 10.75, que no
// es un espesor que exista. Asi que manda el 8 -- el mismo del costado, comprable
// -- y de el cuelgan inset_sup_remate y, detras, marco_remate.
//
// De paso la junta contra el canto del panel deja de ser aire: pasan a ser los
// 2.25 mm de riel que asoman, o sea una linea de aluminio entre el panel y el
// acrilico. Mejor detalle que el hueco.
//
// YA ESTA CONFIRMADO, y salio que NO (2026-08-17). La hoja de datos del Z-Rail
// da la seccion entera: es un extruido de pared fina, 1.2 mm en casi todo el
// contorno, macizo solo en el nucleo por donde pasa el M4 de punta. Un M3 de 6
// mm en esa cara atraviesa pared y sale al hueco. La union es JUNTA PEGADA, y
// los cinco taladros que llevaba la pestana se quitaron (fresando cada uno se
// paga). Esa pieza y su puerta de junta cero murieron el 2026-08-21. Desde el
// 2026-08-27 marco_sup es la cara horizontal del miembro trasero alto: chapa de
// 3 mm. Solo fija el espesor de la meseta, la Y del miembro y el canto superior
// de la trasera.
// NO ES UN NUMERO LIBRE: vale lo que t_costilla, porque la meseta es un ALA
// doblada del mismo blank del miembro alto. Se quedo en 3 al bajar la chapa a
// 1.5 y el modelo dibujaba una meseta de 3 pegada a un alma de 1.5; lo canto
// codex y ahora lo vigila guarda_meseta_es_chapa(). Este fichero no admite
// expresiones, asi que el valor va a mano y la puerta es lo que los ata.
marco_sup   = 1.5;
// Fondo de la pestana hacia dentro del case.
//
// OJO: ESTE NUMERO YA NO ESTA DERIVADO DE NADA. Fue t_cheek = 8 mientras la
// pestana no llevaba tornillos, subio a 16 cuando los llevo -- para dejar 6.3
// mm de acrilico a cada lado del M3, contra los 2.3 de antes, que en acrilico
// es donde arranca una fisura -- y al quitarse los tornillos esa razon murio.
// Se queda en 16 por FORMA, no por calculo, y podria bajar a 8 sin que ninguna
// puerta se queje. Es de las pocas cotas libres que le quedan al case: si
// alguien la toca, no esta rompiendo una derivacion.
//
// La meseta sale de la misma pieza que el miembro trasero alto. marco_sup sigue
// describiendo sus 3 mm visibles; el alma y el retorno ya bajaron a
// t_costilla=1.5 (ver la incompatibilidad declarada en el cierre del cambio).
// TIENE QUE VALER LO MISMO QUE marco_remate. Desde el 2026-08-21 la pestana no
// es una tira de canto: es la PLANCHA HORIZONTAL que tapa la meseta del techo,
// y esa meseta mide exactamente marco_remate. Aqui no se pueden escribir
// expresiones (ver la cabecera del fichero), asi que la relacion la vigila
// guarda_remate() en clearance_budget.py: si alguien mueve uno y no el otro,
// sale en rojo antes de exportar.
// FONDO de la tapa de remate. Con inset_remate_frente tiene que sumar
// marco_remate, que es lo que mide la meseta: aqui no se pueden escribir
// expresiones (ver la cabecera), asi que la relacion la vigila guarda_remate()
// en clearance_budget.py.
// BAJA DE 37 A 29 el 2026-08-27, y lo decide el BARRIDO de la tapa de arriba.
// Fue 37 mientras la meseta era una plancha de acrilico apoyada ENCIMA del
// larguero y de la trasera: se medía desde el plano trasero (308.94) hacia
// delante, o sea llegaba a 271.94. Ahora la meseta es el ALA del miembro alto,
// y un ala se mide desde su doblez -- que esta en la cara trasera del miembro,
// 300.94 -- no desde el plano del case. Con 37 desde ahi llegaria a 263.94, 8
// mm mas adelante que nunca, y la fila de arriba baja de 180 a 45 grados.
// 29 la deja en 271.94 EXACTO: el mismo sitio donde la plancha de acrilico
// llevaba meses sin estorbar. Geometria probada, no cota nueva.
prof_sup    = 29;
// Cuanto se RETIRA la tapa de remate del pico, y no es estetica: es la unica
// razon por la que la tapa de la fila de arriba sigue abriendo.
//
// Hasta el 2026-08-21 esta pieza iba PEGADA al Z-Rail, o sea que GIRABA CON LA
// TAPA y nunca le estorbaba. Al atornillarla a un larguero fijo pasa a ser
// obstaculo, y una plancha fija encima de una bisagra bloquea la bisagra:
// llegando hasta el pico la tapa abria 13.2 grados. Medido barriendo el
// conjunto giratorio contra la banda de la meseta:
//
//     retiro 0 mm  -> abre  13.2 grados
//     retiro 9.3   -> abre  61.0
//     retiro 12.8  -> abre 180.0
//
// 13 esta al otro lado de ese acantilado. Lo que queda descubierto por delante
// NO es un agujero: debajo esta el propio Z-Rail de la tapa, que llega a
// x=271.22, asi que es una linea de sombra entre la tapa y el marco fijo.
inset_remate_frente = 13;

// --- ventilacion con firma (spec §7) ---
// Diametro de la fresa estandar del taller. NO es decoracion del BOM: manda
// sobre toda la geometria interior, porque una fresa no puede entrar en un
// hueco mas estrecho que ella ni dejar una esquina interior mas cerrada que su
// radio. Schaeffer: fresa minima 1 mm (radio interior 0.5), y la de 3 mm es la
// estandar -- pedir un radio mas cerrado obliga a cambio de util y se paga.
// guarda_fresado() en clearance_budget.py lo comprueba contra la geometria.
fresa_d           = 3;
vent_ancho_ranura = 4;   // ancho de la ranura-onda. >= fresa_d por eso mismo
vent_puente_min   = 4;   // puente minimo entre ranuras (fragilidad)
vent_periodo      = 40;  // periodo horizontal de cada onda
// Separacion entre el CAMPO DE RANURAS de la trasera y la banda de ondas que
// tiene encima. NO es vent_puente_min, y esa confusion es justo lo que se
// arregla aqui: el puente minimo es una cota de FRAGILIDAD -- lo que hace falta
// para que dos huecos no se coman el acrilico que queda entre ellos -- y con 4
// mm los dos campos se leian como uno solo. Esto es una cota de DIBUJO: lo que
// hace falta para que la rejilla y las ondas se lean como DOS cosas.
//
// Y por eso la onda subio a la vez (0.32 -> 0.37 del vano entre filas): con el
// borde de la rejilla derivado de la onda, subir solo la onda arrastraba la
// rejilla con ella y la separacion se quedaba clavada en el minimo. Las dos se
// mueven juntas o no se mueve nada.
// Se mide entre BORDES DE MATERIAL, no entre la polilinea de la onda y el canto
// del campo: la onda es un hull de circulos y asoma medio ancho de ranura por
// debajo de su polilinea. La primera version se olvido ese termino y los 14
// salieron 12.
vent_separacion   = 14;  // rejilla <-> ondas. De dibujo, no de fragilidad
// PROFUNDIDAD DEL CAJEADO DE LA SIERRA. La sierra dejo de ser ranura PASANTE
// el 2026-08-24 y pasa a ser un vaciado ciego en la plancha de 8.
//
// EL PORQUE, que es geometrico y no de gusto. Detras de la trasera, a la
// altura de cada onda, hay esto (medido contra el envolvente de un modulo de
// fondo_pcb_max):
//
//   triangulo y cuadrada   y =  99.47   171 mm de aire: el volumen abierto
//                                       del piso de abajo. Siguen PASANTES.
//   sierra                 y = 180.94    32 mm: el dorso de los modulos de la
//                                       fila de arriba. Esta es la que cambia.
//
// No habia choque -- 32 mm sobran -- pero una ranura de 4 mm a 32 mm de un
// dorso de PCB ensena cable y deja entrar polvo y dedo. Y el propio repo ya
// habia pagado por esto: el 2026-08-21 la rejilla de entrada se fue del suelo
// porque "se transparentaba", y costo 2 K. Aqui es la misma fisica con el
// problema al reves.
//
// EN ACRILICO TRASLUCIDO UN CAJEADO CIEGO SE LEE MEJOR QUE UNA RANURA: atrapa
// luz y brilla contra el espesor, en vez de ser un hueco oscuro que ensena lo
// que hay detras.
//
// 4 = la mitad de t_piel. Deja 4 mm de alma, y la fresa estandar lo saca
// (vent_ancho_ranura 4 >= fresa_d 3). Va desde la cara EXTERIOR: hoy no hay
// iluminacion interior (spec §12 deja la WS2812 fuera de alcance), asi que un
// cajeado por dentro seria casi invisible. Si algun dia entra esa luz, voltear
// la cara es una linea en piel_trasera().
//
// LO QUE CUESTA: 0.5 K. La salida baja de 12609 a 9943 mm2 y el salto termico
// sube de 6.6 a 7.1 K contra un techo de 15 -- lo dice guarda_aire() en cada
// corrida. OJO con leer ese numero de mas: potencia_disipada son SOLO los
// reguladores del PSU, y la disipacion de los modulos no esta en ningun
// presupuesto de este repo. El 7.1 describe el camino del PSU, no la bahia de
// arriba, que es justo lo que se sella.
//
// Y EL CAJEADO YA NO ES UNA SIERRA: es la palabra KONDOR (Samuel, 2026-08-24).
// Eso arregla solo el problema que el render del cajeado habia destapado --
// la sierra ciega se leia floja PORQUE competia con dos ondas abiertas y
// perdia. Un logotipo no compite: se lee distinto a proposito.
//
// LO QUE SE PIERDE, y hay que decirlo: el README describe la trasera como
// "las tres ondas -- sierra, triangulo y cuadrada, las tres formas del VCO --
// que son la firma visual del case". Con la sierra fuera quedan DOS de las
// tres formas mas el nombre de la casa. La idea de "las tres ondas del VCO"
// muere aqui y hay que reescribir ese parrafo.
kondor_prof     = 4;    // cajeado ciego, desde la cara exterior
// Tamano nominal de la fuente. Con Franklin Gothic Medium da una ALTURA DE
// CAJA de 32.44 mm -- caja y no "size", que en tipografia no son lo mismo: el
// size es el cuerpo y lo que se mide en la plancha son las mayusculas.
//
// 32.44 cae casi clavado en la banda que ocupaba la sierra (su semialtura era
// vent_periodo*0.35 + vent_ancho_ranura/2 = 16, o sea 32 de banda), asi que la
// composicion de la trasera no se mueve al cambiar el dibujo por la palabra.
// Con Bahnschrift esto medía 34.22; Franklin tiene la mayuscula mas corta al
// mismo cuerpo.
kondor_size     = 34;
// Tracking, y bajo de 2.32 a 1.3 el 2026-08-24 a peticion de Samuel ("con
// menos intercalado"). 1.0 seria el avance natural de la fuente, asi que 1.3
// sigue siendo letra espaciada -- que es la manera modernista de componer
// mayusculas -- pero deja de ser un cartel estirado.
//
// Medido sobre el DXF con Franklin Gothic Medium a size 34:
//
//   spacing 1.00 -> 172.52 mm      spacing 1.50 -> 246.43
//   spacing 1.15 -> 194.69         spacing 1.80 -> 290.78
//   spacing 1.30 -> 216.87  <- este
//
// POR QUE 1.3 Y NO OTRO: cada bloque de onda de la trasera mide au*0.35 =
// 184.8 mm. Con 216.87 la palabra es el elemento mas ancho de la pieza -- que
// es lo que le toca al nombre -- sin aplastar a las ondas, que es lo que
// pasaba con los 369 de antes (el doble que una onda entera).
kondor_spacing  = 1.3;

// --- la entrada de red ---
// La VENTANA de la trasera por donde asoma la entrada de red. Ojo con la
// palabra: es una ventana de PASO, no el recorte donde se encaja el conector.
//
// Hasta el 2026-08-23 el conector se encajaba a presion en el propio acrilico,
// y eso rompia la regla que la spec del case escribe en su §7 -- "las pieles
// removibles nunca llevan mains" -- porque la trasera se quita con 10 M3. Se
// decidio (Samuel, 2026-08-23) montarlo en una PIEZA FIJA, y el acrilico se
// queda solo con el hueco por donde pasa.
//
// El #107 pedia montarlo en el chasis de acero, y NO LLEGA: su pared trasera
// esta a 23.00 mm de la cara interior del acrilico y 20 de esos 23 son el
// larguero de base trasera, que va en medio. La pieza fija se atornilla al
// larguero, que es la unica estructura que hay detras de esta ventana y que se
// queda puesta cuando la plancha sale.
//
// LA PIEZA SI ESTA ELEGIDA, y este fichero era el ultimo en enterarse. Es la
// Schurter KM00.1105.11 (clase I, portafusibles bipolar, interruptor bipolar,
// sin filtro EMC), listada en hardware/01-power-supply/v3/bom-chasis.csv, y
// hardware/01-power-supply/v3/check_red_chasis.py lleva tiempo diciendo HUECO
// porque su recorte "no esta en case/cad/params.scad". De su hoja typ_KM.pdf:
//
//   p.1  Panel Thickness / Snap-in: 1 / 1.5 / 2 / 2.5 mm
//   p.3  recorte  28 (+0.10/-0.05) x 47 (+0.10/-0.05), esquinas max R 0.3
//        brida    30.5 x 50, sobresale 2.5 del panel
//        detras   26.15 de cuerpo + 3.2 de clips = 29.35
//
// Lo primero de esa lista CIERRA la discusion de donde va: el snap-in agarra
// chapa de 1 a 2.5 mm y esta plancha tiene 8. NUNCA pudo montarse aqui. Va en
// chapa, que es lo que dice el #107 y lo que exige check_red_chasis.py.
//
// LOS DOS NUMEROS DE ABAJO SIGUEN SIN DERIVARSE DE ELLA, y por eso se dejan
// como estan en vez de "corregirse" a 47 x 28. Tres razones:
//
//   1. 48 x 27.5 es el recorte de la hoja GIRADO 90 grados y redondeado a ojo
//      (47 -> 48, 28 -> 27.5). Nadie escribio que fuera girado.
//   2. Esta ventana ya no es un recorte de encaje, asi que su cota no es la del
//      recorte: tiene que dejar pasar el enchufe del cable, y eso depende de
//      donde quede la brida, que depende de la pieza fija que aun no existe.
//   3. Y hay un choque sin resolver: con la brida en el plano del acrilico el
//      cuerpo llega a x=271.59 y la pared trasera del chasis esta en 277.94,
//      o sea 6.35 mm de interferencia. Se decide con Samuel, no aqui.
//
// Ponerles 47 x 28 seria pasar de un numero inventado a un numero PRESTADO de
// otra pieza del ensamblaje -- que es peor, porque parece derivado. Se quedan
// visibles y rotos hasta que la pieza fija se dibuje (Principio V).
iec_ancho      = 48;     // SIN DERIVAR de la KM00.1105.11 -- ver arriba
iec_alto       = 27.5;   // SIN DERIVAR de la KM00.1105.11 -- ver arriba
iec_margen_der = 22;     // acrilico entre la ventana y el canto derecho.
                         // Era "au - 70" al reves, o sea el canto IZQUIERDO
                         // contado desde la derecha: un numero que no queria
                         // decir nada. Esto es una distancia al canto, que es
                         // lo que de verdad importa en una plancha de PMMA.

// --- banda delantera del valle y salida en la meseta ---
// De la antigua tapa solo queda la banda LISA del vuelo delantero. Es la
// cara horizontal visible de pie delante del aparato. Samuel la pidio
// "modernista pero seria, como si fuera de Darmstadt": nada figurativo. Las
// ondas de las pieles DIBUJAN una senal; esto es un campo de ranuras y punto.
//
// Y no es un campo cualquiera: va REGISTRADO AL RACK. Una ranura en cada linea
// HP par, o sea que cada una cae en un canto de modulo. El paso no es una
// eleccion de dibujo, es la medida del instrumento; el adorno ES la regla.
//
// Las ranuras salieron del valle el 2026-08-28: esa cara queda maciza. La salida
// equivalente sube a la meseta del miembro trasero alto, donde mas altura da
// mas tiro. Sigue registrada al HP, pero con paso 6 HP y largo 15 salen unas
// 900 mm2; guarda_aire() decide el numero por salto termico, no por estetica.
valle_paso_hp   = 2;   // nombre historico: malla de la ENTRADA trasera
meseta_paso_hp  = 6;   // una ranura cada 6 HP -> 16, registradas al rack
meseta_largo_ranura = 15; // 905 mm2 nominales con vent_ancho_ranura = 4
// Nombre historico: ya no dimensiona la banda del valle. Sigue gobernando el
// retiro inferior de la rejilla de entrada trasera, cuyo contrato lo comparte
// con el IEC; renombrarlo seria otro cambio independiente.
valle_espina    = 16;
valle_margen    = 6;   // historico; la banda del valle ya no se perfora

// --- tiro de aire ---
// El case se refrigera por CONVECCION NATURAL y nada mas: no hay ventilador y
// no va a haberlo. El aire entra por la rejilla del suelo, sube por el piso de
// la fuente y sale por la rejilla alta de la meseta y las ondas de la trasera.
//
// Estos dos numeros existen porque el 2026-08-21 la entrada de aire cambio de
// sitio DOS VECES en el mismo dia -- del hueco del suelo a la trasera, y de la
// trasera al vuelo de la bandeja -- y en cada mudanza el area y la altura de
// tiro cambian. Mientras la entrada fue un hueco accidental de 20054 mm2 nadie
// tenia que vigilar nada; una rejilla DIBUJADA si se puede quedar corta.
//
// La potencia sale de la spec de la fuente v2, §4, sumando los reguladores:
// LM2941 ~2.7 + LM2991 ~2.9 + LT3045x2 ~0.4 + LT3094x2 ~0.33 = 6.33 W. NO
// incluye las perdidas del transformador, que no estan itemizadas -- por eso el
// techo de salto termico va holgado y no pegado al numero.
potencia_disipada = 6.33; // W, SUPUESTO: spec PSU v2 §4, sin perdidas de trafo
// Techo de salto sobre ambiente. 15 K es el criterio de siempre para caja de
// electronica lineal con electroliticos dentro: a partir de ahi la vida del
// condensador se parte por dos cada 10 K y deja de ser un detalle.
salto_termico_max = 15;  // K sobre ambiente, SUPUESTO de diseno

// --- lo que el budget vigila (spec §11: catalogos, no medidos) ---
// El toroide, con la hoja del FABRICANTE delante (Nuvotem Talema, "120VA Open
// Style, with Leads. 230V Primary, Dual Secondaries", parte RS0120P1-2-012 =
// RS 223-8011): diametro 93 mm, alto 46 mm, peso 1.20 kg.
//
// ESTE PARAMETRO SE HA CORREGIDO DOS VECES EL MISMO DIA, y la segunda vez fue
// para deshacer la primera. Historia, porque la moraleja vale mas que el numero:
//
//   1. Habia 45 mm, heredados sin fuente, marcados como no confirmados (#46).
//   2. Se "corrigieron" a 52.1 con dos LISTADOS DE DISTRIBUIDOR (RS) que dan
//      105 x 52.1 mm y 1.33 kg. Dos fuentes coincidentes, pero las dos
//      secundarias.
//   3. La hoja del fabricante dice 93 x 46 y 1.20 kg. Los 45 originales estaban
//      a 1 mm de la verdad; la "correccion" se habia ido 6 mm en el otro
//      sentido.
//
// La regla de design-notes §16.1 -- fuente primaria, no agregador -- no es solo
// para limites de seguridad. Aqui costo una geometria de chasis entera.
//
// El +4 mm de holgura al diametro SI se mantiene: es la propia hoja la que
// avisa "Measured away from leadout bulge; allow extra 4mm at leads".
alto_transformador  = 46;   // hoja Nuvotem RS0120P1-2-012; medir al recibir
diam_transformador  = 93;   // idem; +4 de holgura por las salidas -> 97 util
peso_transformador  = 1.20; // kg, idem. Cierra la estimacion de masa (#106)
margen_transformador = 15; // spec §4
fondo_pcb_max       = 60;  // censo estimado de PCB mas honda, no confirmado

// =====================================================================
// CHASIS DE ACERO DEL PSU  (#107, spec 2026-08-18 §3.3, plan Task 9)
// =====================================================================
// Es la pieza que §13.3 del design-notes daba por supuesta y no existia: la
// regla decia "un esparrago M4 soldado o remachado AL CHASIS" y el case es
// acrilico. Una caja de acero cerrada que contiene la red (J3 F1 RV1 NT1 J4 y
// TR1) y de la que solo sale secundario de baja tension.
//
// ACERO Y NO ALUMINIO, decidido el 2026-08-18: el aluminio no blinda campo
// magnetico a 100 Hz y el acero si. Casi toda caja de catalogo es de aluminio
// fundido -- seguridad y RF si, zumbido cero.
//
// La caja tiene DOS papeles mas, y los dos mandan sobre su forma:
//   1. Es el disipador. Los tres TO-220 atornillan sus tabs contra la pared
//      larga de y = 0 (spec §3.1: Tj de U2 pasa de 101 a ~61 C). Por eso esa
//      pared no lleva ni un agujero de mas.
//   2. Es la referencia de PE. Todo se bonda a UN esparrago, no en cadena.

// --- el interior, que es lo unico que no se puede negociar ---
// 332 = 10 + 200 (PCB) + 15 (cableado) + 97 (toroide con su holgura) + 10
// 170 = 10 + 150 (PCB) + 10
// El eje largo de la PCB va a lo ANCHO del case: 200 mm de los 528 que hay,
// contra solo 150 de los 223 de fondo. Al reves no cabe.
chasis_int_x = 332;
chasis_int_y = 170;
// Es la unica cota del chasis que NO cuelga de otra pieza. El largo y el fondo
// los manda la PCB, dibujada a 200 x 150; el alto solo lo manda el toroide:
// 46 de la hoja Nuvotem RS0120P1 + 15 de margen = 61.
chasis_int_z = 61;

// --- la chapa, y los tres numeros que NO son nuestros ---
// La spec lo dice en su propia lista de huecos: "1.5 mm es supuesto; lo decide
// el taller de doblado junto con los radios de plegado". El desarrollo del
// patron plano depende de los tres, asi que van como parametros y no como
// cotas dibujadas: cuando el taller conteste se cambian tres lineas y el DXF
// sale solo. Mientras tanto son SUPUESTOS declarados, igual que lo fueron los
// 45 mm del toroide -- y aquel salio caro justamente por no estar marcado.
t_chapa      = 1.5;   // SUPUESTO -- acero dulce; lo confirma el taller
radio_doblez = 1.5;   // SUPUESTO -- r = t, plegado al aire, valor habitual
k_factor     = 0.42;  // SUPUESTO -- fibra neutra; DIN 6935 varia con r/t

// --- la tapa ---
chasis_pestana  = 15;   // faldon de la tapa, por FUERA de la pared del cuerpo
chasis_hol_tapa = 0.6;  // juego total para que la tapa entre sin forzar
// YA NO SON SEPARADORES (2026-08-21, #106). Eran 10 mm de pata porque el
// chasis SE APOYABA en la bandeja y bajo su suelo tenian que pasar la chapa de
// refuerzo (1.5) y la cabeza del M6 del toroide (~5). Desde que el chasis
// CUELGA de los dos largueros, nada suyo toca el acrilico y esos dos herrajes
// se mudan al interior de la caja -- que es cambio del chasis, no del case.
//
// Lo que queda es AIRE: el hueco entre el suelo del chasis y la bandeja, para
// que la plancha no sostenga el toroide y deje de resonar donde el #106 dice
// que resuena. Dos milimetros y no cero: cero seria contacto, que es lo mismo
// que apoyar. La pila de tolerancias (taladro de chapa +-0.5, larguero +-0.3,
// espesor del acrilico +-0.4) se come 1.2 en el peor caso y aun queda hueco.
//
// Y no puede crecer mucho: el M5 que ancla al larguero entra por la RANURA
// INTERIOR del 2020, cuyo eje esta en rail/2 sobre la bandeja. Cuanto mas sube
// el suelo, menos pared queda por debajo de ese eje, y los primeros
// radio_doblez + t_chapa milimetros de pared son curva y no admiten taladro.
// Con 2 el tornillo sube 8 por la pared y sobran 2.25 tras el doblez y el radio
// del taladro. Lo comprueba guarda_chasis.
chasis_pie      = 2;    // AIRE bajo el suelo del chasis, no separadores

// --- lo que la Task 6 tiene que casar, no al reves ---
// Estos tres agujeros los DECLARA el chasis y la PCB se pliega a ellos. Va en
// ese sentido porque la pared existe antes que el ruteo: la Fase C esta
// bloqueada esperando esta geometria, no al contrario. Son numeros elegidos,
// no derivados, y por eso el gate solo puede comprobar que caen en la pared
// con material alrededor -- que casen con los TO-220 lo comprueba la Task 6.
chasis_to220_n     = 3;
chasis_to220_paso  = 20;    // >= 10.16 del cuerpo del TO-220 + aislante + clip
chasis_to220_x     = 110;   // centro de la fila = centro del canto de la PCB
chasis_pcb_standoff = 10;   // separador bajo la PCB. Es tambien la altura por
                            // la que sale el mazo hacia la ranura del suelo
chasis_to220_z     = 28;    // sobre el suelo interior: chasis_pcb_standoff
                            // + 1.6 (PCB) + ~16.4 hasta el taladro del tab
chasis_pcb_x     = 10;    // hueco reservado a la PCB dentro del interior
chasis_pcb_ancho = 200;
chasis_pcb_y     = 10;
chasis_pcb_fondo = 150;

// --- el esparrago de PE (§13.3 regla 1) ---
// Pasante con arandela dentada a los dos lados y la pintura enmascarada, no
// roscado en la chapa: 1.5 mm de acero da metro y medio de rosca M4.
// En la pared corta del lado de la red, que es donde entra J3.
chasis_pe_y = 30;
chasis_pe_z = 40;

// --- la salida de cables ---
// NO es un agujero nuevo: la bandeja de base ya lleva cortado un campo de
// ondas de 104 x 32 bajo el PSU que se dibujo como ventilacion. Con la caja
// encima deja de ventilar nada, asi que pasa a ser por donde bajan los cables
// al interior del case. Esta ranura del suelo del chasis tiene que caer DENTRO
// de aquel recorte, y de eso hay un assert.
// x = 120 y no 178: la puerta caza que a 178 la ranura se metia 41 mm DEBAJO
// del toroide, que vive de x=225 en adelante. Y no puede irse al hueco de
// cableado de 15 mm que hay entre PCB y toroide -- 15 no da para 26 de ranura.
// O sea que la salida va POR DEBAJO DE LA PCB, y eso es una condicion para la
// Task 6: los conectores de salida miran a este canto y el mazo pasa por el
// hueco de los separadores.
chasis_salida_x     = 120;
chasis_salida_ancho = 88;
chasis_salida_y     = 40;
chasis_salida_fondo = 26;

// --- el refuerzo bajo el toroide (#106) ---
// 1.20 kg colgando de UN perno M6 sobre 1.5 mm de chapa es un tambor con la
// excitacion puesta encima. El remedio barato es una chapa doble local: mismo
// material, sin doblar, remachada o soldada bajo el suelo. No sube la altura
// util porque va por FUERA, entre el suelo y los separadores.
chasis_refuerzo_lado = 120;
chasis_toroide_x = 273.5;  // 225 + 97/2, el hueco que le deja el reparto
chasis_toroide_y = 85;     // centrado en el fondo interior
d_M6_paso = 6.5;

// --- colocacion sobre la bandeja, y los tornillos de la tapa ---
chasis_margen_bandeja = 10;  // orilla libre a la derecha de la bandeja
// LA COTA MAS JUSTA DE TODO EL MONTAJE, y por eso es un parametro con nombre y
// no un resultado. Los dos largueros 2020 van ENCIMA de la bandeja de base
// desde el 2026-08-17, asi que el chasis va entre ellos con esto a cada lado.
// Una caja doblada sale con +-1 mm facil, y la soldadura de las esquinas tira
// mas; por eso el hueco existe y no se cierra a cero.
//
// DESDE EL 2026-08-21 ESTE HUECO ES ADEMAS LA LUZ QUE SALVA EL TORNILLO. El
// chasis ya no pasa entre los largueros: cuelga de ellos, con 4 M5 que entran
// por sus paredes largas y muerden la ranura interior del 2020. Cada tornillo
// cruza estos 3 mm de aire, asi que lleva separador -- sin el, apretar
// abollaria la pared de 1.5 hacia dentro.
chasis_holgura_larguero = 3;
// M5 por pared larga. Dos y no uno: con uno solo el cajon pivota sobre el, y
// con tres el reparto deja de casar con ch_tornillos(). Son los mismos que
// llevan la tapa, repartidos con la misma regla.
chasis_anclajes = 2;
chasis_tornillo_baja  = 8;   // cuanto por debajo del techo va la fila de M3
chasis_tornillos_largo = 3;  // por faldon largo
chasis_tornillos_corto = 2;  // por faldon corto
salida_holgura = 6;   // orilla del agujero del acrilico alrededor de la ranura
salida_radio   = 8;   // esquinas redondeadas: el acrilico raja desde una viva
