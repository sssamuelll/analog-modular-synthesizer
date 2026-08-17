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
ancho_total     = 544.32;
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
// ese numero sino la SEPARACION ENTRE RIELES. Ya no es un supuesto: StudioRacks
// contesto el 2026-08-17 con los planos de su riel y de su mejilla FLAT-S, y su
// cota es 123.00 mm entre centros -- no los 122.50 de Doepfer. Los rieles
// comerciales varian de marca (Vector 121.46, Tiptop 122.43, Doepfer 122.50) y
// el que cuenta es el que se compra. De ahi salen las caras:
//
//   alto_cara_inf = 123.0 + inset_inf_frente + inset_inf_valle  = 156.5
//   alto_cara_sup = 123.0 + inset_sup_valle  + inset_sup_remate = 158.25
//
// El de arriba sale mas CORTO aunque lleve el mismo estandar dentro, y es por
// la bisagra: su punta de arriba ya no la remata un 2020 sino el eje de giro.
// Lo que hay entre el canto del panel y el vertice es la PESTANA (marco_sup),
// no un perfil, y por eso caben 11 mm donde antes hacian falta 23.
//
// Los 33.5 / 35.25 mm de acrilico que envuelven el estandar son el minimo REAL,
// medido contra las cotas que los limitan. Bajaron 8 y 12 mm respecto a la
// version que suponia perfil 2020 en las caras, y por la razon que se
// anticipaba: el riel real mide 10 mm A LO LARGO DE LA CARA, no 20, asi que su
// media seccion pasa de 10 a 5 en cada punta.
//
// No sale todo a favor. El riel es FINO a lo largo de la cara pero HONDO hacia
// dentro (27.4, con su eje a 13.7 del panel contra los 10 del 2020), y esa
// profundidad tira de la esquina de abajo del riel hacia abajo -- de ahi que
// alto_frontal subiera de 28 a 31 en vez de bajar. El neto es 6.5 mm menos de
// alto y 9 menos de fondo.
//
// Bisel que sobra alrededor de cada panel (inset - inset_er): 20.75 y 7.25 mm
// en la fila de abajo, 16.75 y marco_sup = 8 en la de arriba. Ese ultimo NO es
// bisel de costado: es la pestana, que cruza de lado a lado.
//
// YA NO HAY SUPUESTO AQUI. Se asumia que el riel EUROrack iria atornillado
// SOBRE un 2020; el plano de StudioRacks ensena que no hace falta: el riel se
// fija de punta con un M5 directo al acrilico (taladro de 4.5 en su eje). Los
// 2020 se quedan solo en el esqueleto -- base, entrepiso, remate y repisa --,
// que es donde de verdad hacen estructura.
alto_cara_inf   = 156.5; // DERIVADO: 122.5 + inset_inf_frente + inset_inf_valle
alto_cara_sup   = 158.25; // DERIVADO: 122.5 + inset_sup_valle + inset_sup_remate
alto_panel_inf  = 128.5; // PCB 3U EUROrack
alto_panel_sup  = 128.5; // PCB 3U EUROrack: la fila de arriba tambien
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
// FUE 45 mm, y ese numero era el piso fisico de un apilado de tres cosas
// (rail base + bandeja + rail del zocalo). Ese apilado ya no existe: Samuel
// pidio DOS nodos en la esquina de abajo y no tres -- el de estabilidad y el
// del riel --, asi que el rail del zocalo se retiro, y con el la plancha del
// zocalo, que se habria quedado colgando de una sola fila de tornillos (una
// plancha de 474 mm de ancho sobre una fila pivota como una puerta).
//
// Sin ese rail el minimo lo pone otra cosa: la esquina va REDONDEADA EN PUNTA,
// y esa curva se come alto_frontal/2 de acrilico a lo largo de la cara del
// panel. El rail del panel necesita empezar despues de la curva, o sea
//   inset_tornillo >= alto_frontal/2 + rail/2
// Hay una SEGUNDA condicion, y es la que manda: en esa esquina van los DOS
// nodos que pidio Samuel, y tienen que caber uno encima del otro. El del panel
// va empujado hacia ABAJO por el offset perpendicular (la normal interior de
// una cara empinada apunta adentro y abajo), asi que su centro cae en
// alto_frontal + cos(a)*inset - 6.65 y su canto inferior 13.93 mas abajo.
//
// OJO CON EL TECHO DE ABAJO, que es donde este calculo se hizo mal una vez: no
// es el lomo del rail de base (y = 20) sino el TOPE DE LA BANDEJA que se apoya
// encima de el (y = 20 + t_acrilico = 25). La bandeja es la que carga el PSU y
// va apoyada en el lomo del rail, no colgada. Exigiendo holgura_rail:
//   alto_frontal + cos(35)*inset >= 49.73
// Derivarlo contra el rail y no contra la bandeja sale 5 mm de barato, y
// solapes() lo canta (0.51 mm de solape rail-bandeja). A alto_frontal = 10 el
// riel del panel se montaba 22.3 mm ENCIMA del de la base.
//
// Las dos condiciones se optimizan JUNTAS, y ahi esta el truco: la altura de
// la primera seccion vale alto_frontal + alto_cara_inf*cos(35), y como
// alto_cara_inf lleva el inset dentro, esa altura es exactamente
// (alto_frontal + cos(35)*inset) + una constante. O sea que minimizar el piso
// ES minimizar el lado izquierdo de la condicion de los dos nodos, y su suelo
// es 49.58 -- por debajo no hay nada que rascar sin mover la bandeja.
//
// El par (31, 23.5) se apoya en las dos a la vez: 0.52 mm sobre el suelo de los
// dos nodos y 1.0 de material de sobra contra la curva.
//
// SUBIO de 28 a 31 al entrar el riel real, y es contraintuitivo: el riel es la
// MITAD de alto que el 2020 a lo largo de la cara, pero su eje se va 15.3 mm
// hacia dentro en vez de 11.6 y el perfil tiene 27.4 de fondo, asi que su
// esquina de abajo cuelga mas y hay que subir el vertice para que libre la
// bandeja. Lo fino de la seccion se cobra en los insets (bajan 3 y 5 mm); lo
// hondo se paga aqui.
//
// Ojo con bajar alto_frontal creyendo que siempre ayuda: a 0 la esquina pasa a
// ser un vertice agudo de 55 grados y su redondeo se come 64 mm de cara, cuatro
// veces mas que la punta de dos arcos de ahora.
alto_frontal    = 31;
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
// FUE 22, que era la meseta que daba la punta redondeada gorda de arriba. Hoy
// es el canto del techo, del GROSOR DEL ACRILICO (t_cheek = 8): de seccion
// cuadrada, tan ancho como grueso es el costado que lo forma.
//
// OJO, ESTE NO ES EL BORDE QUE SE VE DE FRENTE. marco_remate pertenece al
// COSTADO, o sea que solo existe en los dos laterales y no cruza el ancho: por
// eso ponerlo a 8 no hizo aparecer ninguna pestana en el render. La pestana que
// tapa el canto del panel es marco_sup, una pieza aparte que si va de lado a
// lado. Los dos valen 8 y juntos envuelven la punta de arriba en L.
//
// No es un valor libre: si cambia t_cheek hay que cambiar este a mano (aqui no
// se pueden escribir expresiones, ver la cabecera del fichero). Y baja el
// fondo del case 14 mm de golpe, porque el fondo se deriva de el.
//
// Efecto secundario buscado: con el marco en 8 la esquina de arriba pasa a
// tangente 4 mm en vez de 11, o sea que las dos puntas del techo se vuelven
// casi vivas. Eso ya no importa como antes -- lo que se ve arriba ahora es el
// canto del panel, no un pico de acrilico.
marco_remate    = 8;
// Entrepiso: la franja horizontal entre el tope de la cara inferior y la base
// de la superior -- el "valle del medio" de la silueta. Ahi va la bandeja
// acrilica intermedia. Fue 25 (minimo tecnico de R7: por debajo, los dos
// railes girados se solapaban 2.52 mm), luego 40 cuando Samuel lo pidio
// ancho, y ahora 80: pidio el valle "al menos el doble" (2026-08-17).
paso_horizontal = 80;
// Acabado modernista: ningun canto del costado es esquina viva. Hay DOS
// radios porque el contorno pide dos cosas opuestas (ver la nota larga en
// sam17_case.scad, funcion redondear).
//
// radio_perfil = las esquinas SUAVES. Manda en el valle, donde hace la curva
// que Samuel describio: sube de la base del panel superior, queda un tramo
// recto en medio ("una pajuela o dos") y se encorva hacia abajo al llegar al
// tope del inferior. Ese tramo recto es paso_horizontal menos lo que se
// comen las dos curvas -- AJUSTAR MIRANDO EL RENDER, no a ciegas.
radio_perfil    = 14;
// radio_pico = el vertice CONVEXO del valle, donde acaba el tope del panel de
// abajo. Corto a proposito: Samuel lo quiere leyendose como PICO, "el round
// mas durito". No bajar a 0 -- una esquina viva en acrilico de 8 mm es donde
// arranca una fisura.
radio_pico      = 5;
// radio_valle = el vertice CONCAVO del valle, donde arranca la cara de arriba.
// Largo: "el round del angulo que se genera en el valle puede ser mas suave".
// Es el opuesto exacto de radio_pico y por eso no pueden ser el mismo numero.
// Techo: la funcion lo recorta a 96.6 mm con el valle en 80.
radio_valle     = 30;
// bombeo = ENTASIS. "Las rectas no son completamente rectas, por poquito, una
// ligera distorsion pero muy ligera". Flecha en MILIMETROS POR CADA 100 MM de
// tramo recto, no absoluta: una flecha fija se ve exagerada en un tramo corto
// y no se ve en uno largo. A 0.5 el canto de abajo (345 mm) se abomba 1.7 mm.
// Se abomba hacia FUERA, asi que crece el bbox -- por eso la tolerancia de
// check_dxf tuvo que pasar de 2 a 4 mm. Poner 0 lo desactiva.
bombeo          = 0.5;
// radio_punta = las esquinas que tienen que leerse como PUNTA redondeada
// (frente-abajo y remate de arriba, 2026-08-17). Va sobredimensionado a
// proposito: la funcion lo recorta al maximo que permite la arista mas corta
// del vertice, y ese maximo es justo la punta. Subirlo mas no cambia nada;
// bajarlo devuelve la cara plana.
radio_punta     = 400;

// --- materiales ---
t_acrilico = 5;    // planchas del cuerpo; MEDIR con calibre (spec §11)
t_cheek    = 8;    // costados portantes
t_panel    = 1.6;  // PCB de aluminio, espesor estandar JLCPCB
// kerf FIRMADO y NEGATIVO por convencion: el modelo dibuja `d + kerf` en
// todo hueco y el laser ensancha, asi que para que el agujero fisico salga
// al nominal, kerf tiene que RESTAR. Un kerf de tabla de servicio (ancho de
// canal, siempre positivo) entra aqui con el signo cambiado.
// Magnitud provisional; SE CALIBRA con el cupon (spec §11, README paso 2).
// ASIMETRIA DELIBERADA: el kerf se aplica a los HUECOS (agujeros, ranuras,
// recortes), no a los CONTORNOS exteriores. Cada plancha sale por tanto ~0.2
// mm mas chica que el nominal: en todas las piezas de este case eso es
// holgura a favor (auditado pieza por pieza en el review final de rama), y
// ninguna lleva encaje macho donde restaria. Si alguna vez se dibuja una
// lengueta que deba entrar apretada, hay que aplicarle kerf a su contorno.
kerf       = -0.2;

// Teselado de circulos. VIVE AQUI, no en sam17_case.scad, porque todo .scad
// que incluya params lo hereda: coupon.scad lo perdio cuando estaba alla y
// sus agujeros salieron PENTAGONOS (5 segmentos, error de forma 0.33-0.48 mm
// contra peldanos de 0.1 mm) -- la pieza de calibracion no podia calibrar, y
// peor, devolvia un kerf errado con evidencia fisica que lo respaldaba.
// clearance_budget.py lo ignora: su regex pide `\w` y `$` no lo es.
$fn = 48;

// --- sistema de paneles (spec §6) ---
rail            = 20;   // perfil 2020, SOLO esqueleto (base, entrepiso, remate, repisa)
// RIEL EUROrack REAL, de los planos que mando StudioRacks el 2026-08-17. Ya no
// es un 2020 asumido ni un supuesto: es la seccion del perfil que se compra.
//
//   rail_er_alto   10.00  a lo largo de la cara. La mitad del 2020, y de aqui
//                         sale casi todo el recorte de los insets.
//   rail_er_fondo  27.40  hacia dentro del case
//   rail_er_eje    13.70  del taladro de 4.5 (el M5 de punta) a la cara que
//                         toca el panel. Con el 2020 esta cota era rail/2 = 10.
//
// El taladro cae centrado en las dos dimensiones (13.70 de 27.40 y 5.00 de
// 10.00), asi que el eje ES el centroide de la seccion. La mejilla FLAT-S del
// mismo fabricante lo confirma por otro lado: sus dos M5 van a 13.80 del canto
// delantero, o sea el mismo 13.7 con la tolerancia del plano.
//
// El riel se fija DE PUNTA, con un M5 que entra por el costado a ese taladro.
// No hay 2020 detras de las caras: eso era el supuesto viejo y el plano lo
// desmiente.
// Largo de catalogo del riel. Es la cota que fija el ancho del case (ver
// ancho_total): 104 HP x 5.08 = 528.32. No se puede "ajustar" -- o se compra
// otro largo o se corta el riel, y cortarlo se lleva la punta por donde se fija.
largo_riel      = 528.32;
rail_er_alto    = 10;
rail_er_fondo   = 27.4;
rail_er_eje     = 13.7;
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
//   inferior / frente   punta redondeada   15.5      + 5 + 3.0   = 23.5
//   inferior / valle    pico (r=5)          2.6      + 5 + 2.4   = 10
//   superior / valle    valle (r=30)       12.4      + 5 + 2.1   = 19.5
//   superior / remate   -- BISAGRA --   marco_sup + gap_sombra + 2.75 = 15.75
//
// La cuarta se sale del patron porque ahi no hay perfil: es el eje de giro, y
// no la fija ninguna curva sino lo que hay por encima. De arriba abajo:
//   8     marco_sup   la pestana de acrilico que tapa el canto del panel
//   5     gap_sombra  la junta que deja pasar el barrido de la tapa (ver abajo)
//   2.75  inset_er    del canto del panel a su fila de taladros = al eje
//
// La junta NO es decorativa. Al abrir, el canto de arriba del panel gira sobre
// un eje que esta 3 mm por debajo y 5.6 detras, o sea a 6.35 mm de radio; en el
// barrido ese canto SUBE hasta 6.35 - 3 = 3.35 mm antes de retirarse. Con la
// pestana pegada al canto, la tapa se traba en el primer grado. Los 5 de
// gap_sombra dan 1.65 de margen y de paso son la misma junta de sombra que
// llevan las pieles flotantes, asi que el detalle es el del resto del case.
//
// Las tangentes NO son parametros: salen del radio y del angulo del vertice.
// Si se mueve un radio hay que rehacer la columna, y el que avisa es
// railes_dentro_del_costado() en check_dxf, que lee el contorno del DXF.
inset_inf_frente = 23.5;
inset_inf_valle  = 10;
inset_sup_valle  = 19.5;
inset_sup_remate = 15.75;
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
inset_er        = 2.75;
inset_er_x      = 7.5;
// Del plano de la mejilla FLAT-S: dos M5 a 5.00 mm de cada punta de una pieza de
// 133.00, o sea 123.00 entre centros. Confirmado por escrito por John el
// 2026-08-17 ("123mm ctr to ctr, 13.8mm in from front edge").
sep_railes_inf  = 123.0;
sep_railes_sup  = 123.0;
holgura_rail    = 4;    // separacion minima entre railes vecinos (fix solapes)

// --- esqueleto y herrajes ---
n_bulkheads      = 2;    // costados exteriores (3 si el vano flexa, spec §11)
d_M3_paso   = 3.4;  // agujero paso M3 (ISO holgura media)
d_M4_paso   = 4.5;  // agujero paso M4
d_M5_paso   = 5.5;  // agujero paso M5 (railes 2020 roscados en el alma)
gap_sombra  = 5;    // junta de sombra de las pieles flotantes
// Paticas: METALICAS, torneadas, pequenas (Samuel, 2026-08-17 -- "metalicas
// y elegantes"). No son de goma: eso cambia el BOM y el acabado. Van bajo los
// COSTADOS, que son las piezas portantes de 8 mm, con su cara exterior a ras
// del costado; el resto del disco vuela hacia dentro, bajo la bandeja. El
// canto de abajo del perfil va RECTO por esto mismo: con paticas en los
// extremos, un canto abombado convierte el apoyo en un balancin.
alto_pie    = 8;    // altura de la patica
d_pie       = 16;   // diametro; pequeno a proposito
// BISAGRA de la tapa superior. Continua, de todo el ancho util, con el nudillo
// corriendo por el vertice del techo: la cara de arriba entera se levanta como
// el capo de un carro. Sustituye al 2020 que remataba esa cara, y por eso el
// panel llega hasta el punto mas alto.
//
// ASUMIDA igual que el riel EUROrack: 8 mm de nudillo es una bisagra continua
// de aluminio corriente, pero el modelo no ha visto la pieza real. Lo que de
// verdad manda es que el EJE quede a inset_er del canto del panel; si la pieza
// pide otro diametro cambia d_visagra, no la geometria de la cara.
d_visagra   = 8;
// PESTANA SUPERIOR: la banda de acrilico que cruza de costado a costado por
// encima del canto del panel de arriba, sobre la propia cara. Samuel la pidio
// porque el panel remataba pelado ("no veo esa pestana ... quiero un top marco
// acrilico"), y no la daba marco_remate: ese pertenece al COSTADO y solo existe
// en los dos laterales, no cruza el ancho. Son piezas distintas y las dos miden
// 8 = t_cheek, asi que juntas envuelven la punta de arriba en L.
//
// Se lleva su ancho de la cara: la cara crece marco_sup y el canto del panel
// baja otro tanto, o sea que el case sube marco_sup*cos(45) = 5.7 mm.
//
// PENDIENTE, igual que las palas de la bisagra: como se fija. Va volada sobre
// el larguero de remate y a 8 mm de ancho no cabe una fila de M4, asi que sale
// standoff lateral, ranura en el costado o pegado. Por eso todavia no tiene DXF
// propio -- una pieza sin sus taladros no se manda a cortar.
marco_sup   = 8;

// --- ventilacion con firma (spec §7) ---
vent_ancho_ranura = 4;   // ancho de la ranura-onda
vent_puente_min   = 4;   // puente minimo entre ranuras (fragilidad)
vent_periodo      = 40;  // periodo horizontal de cada onda

// --- lo que el budget vigila (spec §11: catalogos, no medidos) ---
alto_transformador  = 45;  // CATALOGO, no confirmado; medir pieza real
margen_transformador = 15; // spec §4
fondo_pcb_max       = 60;  // censo estimado de PCB mas honda, no confirmado
