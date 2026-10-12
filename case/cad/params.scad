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
// --- EL MIEMBRO ALTO Y EL TALON: la banda es el miembro (2026-08-29) ---
// Fueron TRES canales de chapa (bahia, trasero bajo, trasero alto) hasta el
// 2026-08-29 por la manana y dos por la tarde. Desde esa noche el miembro alto
// es una L -- la meseta, del pico al plano trasero, y la BANDA que baja por el
// plano trasero -- y el bajo es el TALON: la misma banda con un pie sobre la
// tabla, como la nariz por delante. La trasera va DENTRO de las dos bandas y
// los marcos de la trasera de la manana desaparecen: la banda vista ES el
// alma. Spec 2026-08-29-marco-ventana-banda-estructural.
//
// LA BANDA VISTA, a ras del plano trasero, arriba y abajo. 24 y no 20: 20 era
// el ancho del marco de la manana y lo ponia su fila de M3 (1.5 D a los dos
// cantos); hoy lo pone la flexion de la L SOLA, sin la trasera, con carga_mano
// en el centro de la meseta -- con 20 el canto libre de la banda trabaja a 158
// MPa contra los 130 de RP02_ALUMINIO, con 22 a 131 y con 24 a 110. Lo mide
// guarda_miembro_alto(). Con 20 pasaria solo obligando 6082-T6 (Rp0.2 240,
// EN 485-2 para chapa hasta 3 mm) y la regla del repo es "aleacion
// recomendada, no obligatoria". Se ve: 4 mm mas de metal arriba y abajo. Es
// un parametro y se juzga en render.
banda_trasera   = 24;
// EL TECHO POR DETRAS, dos variantes que se escogieron mirando (spec
// 2026-08-29-trasera-capturada §5): SAMUEL ESCOGIO B (1) EL 2026-08-30, "el
// angulo de 45 mas pronunciado"; la A queda hasta que se retire en una tanda
// propia. 0 = la BANDA plana de banda_trasera con
// P5 a radio_chapa (la de #241); 1 = el CHAFLAN: P5 a chaflan_nariz como P0 y
// P6, la meseta dobla 45 al chaflan y otros 45 al labio vertical de
// talon_labio -- atras se lee un marco simetrico, dos labios iguales arriba y
// abajo, y las bridas suben junto a la tira del chaflan con un relieve. Las
// puertas corren sobre las dos; el render de cada una lleva su nombre. Ninguna
// lleva canal: en una sola chapa el labio no puede tapar el canto del acrilico
// Y tener un retorno detras (es lo que la rev. 22 perdio al fundir la meseta),
// y el bolsillo de los anillos ya retiene la plancha en las dos direcciones
// por los lados. La tapa de arriba conserva sus 180.
remate_trasero_chaflan = 1;
// LA PARED ENTRE LOS DOS BOLSILLOS DEL TRAMO TRASERO (spec s3.2). El anillo
// tiene 20 de franja atras; el bolsillo del costado ocupaba 6 (u = 14..20) y
// el de la trasera ocupa 11 (u = 3..14): se tocaban sin pared. En el tramo
// trasero, y solo ahi, el costado entra 3 en vez de 6 -- su canto vive detras
// del labio y el marco lo sigue pisando -- y entre los dos bolsillos queda
// esta pared, de toda la altura. 3 como el labio: lo que el costado tiene
// delante lo tiene la trasera a los lados.
pared_rebaje_trasera = 3;
// Cuanto entra el costado de PMMA en el tramo trasero (2026-08-30). Era un 3
// implicito dentro de cara_anillo_trasera = 20; se saca a parametro porque
// cara_anillo_trasera pasa a ser DERIVADO -- bolsillo + pared + esto -- y una
// cota no puede tener dos fuentes. 3.5 y no 3: el bolsillo de la trasera se
// mueve 1.5 hacia dentro con la rendija, y de los 2 que gana la franja, medio
// se lo queda el costado para no perder agarre.
entrada_costado_trasero = 3.5;
// EL TALON ES LA NARIZ DE ATRAS (2026-08-29, noche, 2). Samuel: "el talon
// preferiria que tuviera el mismo estilo y acabado que la nariz". La esquina
// de abajo-atras del anillo (P6) va a chaflan_nariz como la de delante, y el
// talon la envuelve igual que la nariz: pie sobre la tabla, chaflan a 45 y un
// LABIO vertical a ras del plano trasero que tapa el canto de abajo de la
// trasera. Sin bridas: tres M4 avellanados por el pie, desde dentro, como la
// nariz. GEMELO de _talon() en clearance_budget.py; lo mide guarda_talon().
//
// El pie, hacia delante desde el PIE DEL CHAFLAN. 20 y no 18 como la nariz:
// la boca del avellanado (d_cabeza_M4_avell) es un cuerpo fijo detras de la
// cara interior del acrilico -- que puede venir 1.2 mas gruesa -- y vale para
// ella la regla de la trasera, tol_pmma + 0.5 = 1.70 de aire; con 20 quedan
// 2.77, con 18 quedaban 0.77.
// 22.5 DESDE EL TECHO MACIZO (2026-08-30): la trasera retrocede 2.5 en total
// al crecer la rendija del alero (rehundido_trasera pasa de 3 a 5.5), y el pie
// la sigue milimetro a milimetro para conservar el aire del avellanado. Fue
// 21.5 con la rendija en 3.0; al subirla a 4.0 tras la revision, esos 2.77
// caian a 1.77 -- verde por 0.07 mm, que no es margen -- y el pie sube otro
// milimetro. La regla no cambia: el pie del talon acompana a la plancha.
talon_pie       = 22.5;
// El labio vertical, desde la coronacion del chaflan hacia arriba. 13 es el
// frente de la nariz (alto_frontal - chaflan_nariz): las chapas del canto
// cierran igual, chaflan de 6 y 13 de plomo. Tapa 12.5 del canto de abajo de
// la trasera, que apoya en el pie (el bolsillo del anillo tapa 6 a los lados).
talon_labio     = 13;
// EL LABIO DEL TECHO (variante B), del canto de abajo de su chaflan hacia
// abajo. 18 y no los 13 del talon: la trasera ya no se atornilla al techo,
// asi que el techo tiene que aguantar SOLO la mano de carga_mano en el centro
// de la meseta, y con 13 trabaja a 176 MPa contra los 130 de la puerta
// (guarda_miembro_alto). Con 18 la caida total es 24, la misma que la banda
// plana de #241, y da 110. Si Samuel lo quiere a 13, es obligar 6082-T6 en el
// pliego (Rp0.2 240), no bajar el numero aqui.
// 20 DESDE EL TECHO MACIZO (2026-08-30): el labio ya no solo aguanta la mano,
// TAPA la rendija por la que sale el aire, y lo que tiene que tapar lo manda
// la capilaridad. Con el solape de 6.5 que daba 18, el agua subia 6.2 por la
// rendija comprimida un 20 % -- 0.3 de margen. Con 20 el solape es 8.5 y
// sobran 3.8 (guarda_rendija) desde que la rendija subio a 4.0: la subida va
// con 1/d, asi que ensanchar la luz por lo termico mejoro tambien esto. El de
// rigidez sigue verde y con mas seccion: 18 era el minimo por ahi, y este
// numero solo sube.
techo_labio     = 20;
// LA RENDIJA DEL ALERO (2026-08-30). El aire de la caja sale por aqui: entre
// la cara interior del labio del techo y la cara vista de la trasera, mirando
// al SUELO, tapada por el vuelo del techo. Sustituye a las 16 ranuras de la
// meseta, que eran un agujero mirando al cielo en la cara que se moja.
// 3.0 y no 2.5 (lo que dejaba la spec del 29-08 para una tira de EPDM) porque
// la subida capilar va con 1/d: a 2.5 el agua sube 5.9 contra 6.5 de solape, y
// a 1.5 de luz local -- una plancha alabeada -- sube 9.8 y se mete dentro.
// Es tambien el grosor de los tacos: el taco ES la luz.
// 4.0 DESDE LA REVISION DEL 30-08. Con 3.0 la cuenta capilar cerraba, pero la
// TERMICA no: el area de salida se calculaba con la luz nominal mientras la
// puerta capilar ya usaba la comprimida -- dos puertas sobre la misma junta,
// cada una con su estado. Con la comprimida en las dos (2.4 de 3.0) el case
// sube 14.8 K contra un techo de 15 con el C_D pesimista: 0.2 K, que no es
// margen. Con 4.0 la luz comprimida es 3.2, el area sube de 1081 a 1442 mm2 y
// quedan 13.6 K -- 1.4 de margen. Y la capilaridad MEJORA de paso, porque la
// subida va con 1/d: baja de 6.2 a 4.7 mm contra 8.5 de solape.
// Lo que cuesta: el rebaje se ensancha a 4.5 (la fresa de Ø3 sigue entrando),
// la trasera retrocede 1 mas y la franja del tramo trasero pasa de 22 a 23 --
// un milimetro mas de aluminio visto desde el lado.
aire_labios     = 4.0;
// LAS PESTANAS del pie: lanzadas de la chapa (cortadas por tres lados y
// dobladas 90 hacia arriba con radio_doblez_pestana) detras del canto de
// abajo de la trasera: su tope hacia dentro entre los anillos, que a los
// lados dan las paredes de los bolsillos. Lejos de los tres M4 (a 1/4, 1/2 y
// 3/4). alto = lo que suben sobre el pie; ancho = a lo largo del talon; aire
// = de su cara a la cara interior nominal de la trasera (>= tol_pmma + 0.5 =
// 1.70; 3.5 deja ademas 2 t de plano entre el doblez del chaflan y el de la
// pestana con el radio a 2 t: 3.14 por la cuenta de guarda_talon, que toma la
// tangente EXTERIOR (r + t) de los dos dobleces; la pestana dobla con el radio
// interior hacia la plancha, asi que el plano real es 1.5 mas (4.64). Con 4 de
// aire el plano sube a 3.64 pero la mano baja entre pestanas pasa de 8.9 a 9.4
// MPa: el aire manda mas en la placa que en el plano. Y el radio queda fuera
// de donde apoya una plancha gruesa. ancho = 25 por la lengueta: su raiz mide
// 23.5 (el alivio muerde 0.75 por lado en la linea del doblez) y con la
// reaccion en su punta trabaja a unos 200 MPa contra los 240 del 6082-T6
// (con 20, raiz de 18.5: unos 250, fluye).
talon_pestana_alto  = 8;
talon_pestana_ancho = 25;
talon_pestana_aire  = 3.5;
// Cuantas pestanas, repartidas a (2i+1)/2n del hueco entre anillos. Solo las
// potencias de dos esquivan los tres M4 (n = 4: 1/8..7/8; n = 8: 1/16..15/16).
// SON ESTRUCTURA, no adorno: la trasera capturada solo por los dos bolsillos
// se comba 20 mm con carga_mano al centro y trabaja a 14 MPa en el contacto,
// sobre el techo de 10 del PMMA. Y son un TOPE, no un apoyo: estan a
// talon_pestana_aire de la plancha, que cede eso antes de tocarlas. Con ese
// aire y la mano barrida por todo lo visible, cuatro dejan la mano baja entre
// dos pestanas a 9.8 MPa (pasar por un pelo no es pasar: la regla de la pata
// del marco); OCHO la dejan en 8.9 (guarda_trasera_flexion: placa por Levy).
talon_pestana_n     = 8;
// Radio interior del doblez de una pestana lanzada: 2 t, el mismo que los
// demas dobleces de la chapa (radio_doblez_costilla) y el que el taller pliega
// sin preguntar. Se probo 1 t la noche del talon: el RFQ lo dejaba como
// pregunta abierta, y si el taller contestaba 2 t la lengueta se quedaba a
// 234 MPa contra 240 y el plano tras el chaflan en 2.64 contra 3 -- un diseno
// colgado de una respuesta. Con 2 t, 25 de ancho y 3.5 de aire no hay
// pregunta. Y ALIVIO en las dos esquinas del corte en U, donde el corte
// muere en la linea del doblez: un taladro de alivio_pestana a caballo de la
// linea, para que el doblez no rasgue la esquina viva (a 200 MPa nominales,
// con Kt ~2 en una esquina viva la chapa plastifica ahi y la pestana toma
// deformacion permanente: el aire de 3.5 dejaria de ser 3.5).
radio_doblez_pestana = 3;
alivio_pestana = 2;
// Ancho del CORTE en U que suelta una pestana lanzada por tres lados (y del
// relieve de la brida del techo junto al chaflan). No es el kerf: un DXF de
// contorno no sabe dibujar una linea suelta, y una pestana necesita aire a
// los lados para doblar sin rozar. Medio milimetro.
corte_pestana = 0.5;
// Vale lo mismo que ya repartian las filas de las planchas de acrilico para
// que sus tornillos caigan en la reticula por construccion, no por coincidencia.
// Una sola cota gobierna ambos lados: repetir 100 los desincronizaria al cambiarla.
reticula_paso = 100;
// LA PESTANA DE LA BANDA DEL VALLE. La banda lisa del vuelo delantero se
// dobla 90 grados en cada punta y se atornilla a la costilla: asi no queda
// sujeta solo por una linea longitudinal incapaz de inmovilizar su alabeo.
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
// es el minimo que conserva 1.5D a ambos lados del M3. Los paneles son fijos;
// no existe alivio ni cota de apertura que gobierne esta pieza.
pestana_valle      = 21;
// Alivio local de la esquina que comparte plano con el Z-Rail 3U fijo. No es
// una holgura de giro: elimina la penetracion estatica sin acercarse al M3.
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
// -0.2.
// DESDE EL 2026-10-11 ESE ACRILICO ES LA TRASERA. La cuenta la puso la mejilla
// del costado, que se fue con la persiana, y la trasera es el mismo PMMA de 8
// en un bolsillo con los mismos tres numeros (labio 3, 11 de ancho, 6 de
// hondo): la vigila guarda_trasera_capturada(). Los bolsillos de la persiana,
// 6.9 de hondo con el iman, dejan 7.1 detras (guarda_tacos_persiana()).
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
// EL REBAJE DE CHAPA (2026-08-30). Samuel, mirando la esquina en Blender: "el
// acabado debe sentirse perfecto con respecto a la esquina, perfectamente
// alineado con el del marco o si no se ve feo -- tiene que ser una pieza que
// se sienta empotrada". Hasta hoy la chapa se apoyaba EN la cara interior del
// anillo, asi que la tolerancia del taller de chapa (+-0.3 en el desarrollo,
// +-0.5 en el doblez) salia a la superficie como un escalon que se toca con
// el dedo. Ahora el anillo lleva un rebaje fresado por dentro, la chapa se
// mete en el, y las dos cotas que se ven las corta la FRESADORA, no la
// plegadora: la junta de sombra de 1 y el reborde que tapa el canto.
// Hermano del bolsillo del acrilico (rebaje_anillo / rehundido_acrilico), que
// ya captura las mejillas y la trasera con el mismo truco.
//
// El fondo, en z desde la cara interior. 3 = 2 t de la chapa: menos y la
// chapa no queda presa, y el suelo del rebaje es ademas la pared exterior del
// bolsillo de la trasera por construccion.
rebaje_chapa       = 3;
// Cuanto queda la cara exterior de la chapa por dentro del contorno del
// anillo: la JUNTA DE SOMBRA que se ve. 1 es lo minimo que deja un reborde
// fresable (1 de pared por 3 de alto es 3:1) y es la cota mas delicada de la
// pieza: va al RFQ como pregunta con respuesta ya disenada -- si el taller
// pide 1.5, se cambia aqui y todo lo derivado se mueve solo.
rehundido_chapa    = 1;
// Holgura del canto de la chapa contra la pared del rebaje. 0.5 y no los 0.15
// de hol_piel: una chapa cortada a +-0.3 tiene que entrar aunque venga larga,
// y aun larga le quedan 2.2 tapados bajo el reborde. Nadie la ve.
hol_chapa          = 0.5;
// Chaflan de las dos aristas de la cara vista, silueta y ventana. Rango
// ESTIMADO 1-3 de la foto. Es lo que hace que la arista brille.
chaflan_anillo     = 1.5;
// --- LA PERSIANA (2026-10-11) ----------------------------------------------
// docs/superpowers/specs/2026-10-11-case-persiana-design.md. La placa de cada
// costado, por fuera del anillo y tapandolo. El ritmo de las varillas y los
// tacos los calcula case/cad/persiana.py y los escribe en
// persiana_generada.scad; aqui van las cotas que los gobiernan.
t_persiana           = 6;     // el fondo de la varilla: lo que la sostiene de frente
borde_persiana       = 4;     // el borde macizo que sigue la silueta
varilla_persiana     = 2.0;   // 6 / 2.0 = 3:1, ESBELTEZ_MAX_PARED de clearance_budget
paso_persiana        = 7.0;   // paso medio; con 6.2 el pesimista daba 20.1 K
ola_persiana         = 0.16;  // la ola lenta del paso (+-16 %)
azar_persiana        = 0.06;  // y un azar determinista (+-6 %): sin numpy.random
hondo_ciego_persiana = 4;     // la ranura ciega (banda y atados) deja un puente de 2
alto_atado           = 4;     // los dos atados, a 1/3 y 2/3 del alto
suelo_persiana       = 0.3;   // sobre la tabla
// los tacos y sus bolsillos (Elke Brandt, junta del 11-10)
u_taco               = 6.5;   // centro, desde la silueta: deja 3.0 al rebaje (u = 14)
d_taco               = 8;     // y localizador a 8 H7
alto_taco            = 3.5;
d_bolsillo_taco      = 9;     // los de retencion, con holgura
hondo_bolsillo_taco  = 3.8;   // 0.3 de aire bajo el taco: la persiana apoya en el anillo
colisa_taco          = 10;    // el segundo localizador, alargado en x
d_iman               = 6;     // neodimio N42
alto_iman_anillo     = 3;
alto_iman_taco       = 2;
alto_iman_fino       = 1;     // en el tramo de atras: detras esta el bolsillo de la trasera
// EL CUPON: un tramo recto del perfil del anillo que se corta, se chaflana, se
// anodiza y se mira ANTES de mandar cortar los dos anillos enteros (#237). 100
// mm es lo que pide la spec 2026-08-28 §9 y lo que ya prometia el PLIEGO: largo
// suficiente para leer el chaflan a lo largo (no en una esquina), para meter el
// PMMA de 8 +-1.2 con su junta en el rebaje y ver si asienta -- desde el
// 2026-10-11 es el de la trasera, que va en un bolsillo con la misma seccion;
// el rebaje del costado se queda vacio --, y para dejar un
// punto de bonding enmascarado con sitio de sobra alrededor. Vive aqui y no
// suelto en el pliego para que la puerta lo imprima con las cotas de la seccion
// del mismo sitio: el cupon no es una pieza del case y no entra en el BOM.
cupon_largo = 100;
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
// Broca del M3 con el que la PESTANA de la banda del valle se atornilla. Esa
// rosca NO va en el anillo -- no cabe, la cuenta esta en guarda_anclajes() --
// sino en los 6 mm de la PLACA DEL VALLE, igual que las de la bahia (R3).
// 2.5 de ISO 262: aqui no hay hoja de fabricante que consultar.
d_M3_rosca         = 2.5;
// LOS CLIPS DE RETENCION (t_clip 4, clip_fondo 24, clip_largo 20) Y LA ESCUADRA
// DE LA TRASERA (escuadra_ala 16, escuadra_m3 3, escuadra_retiro 10) MURIERON
// EL 2026-08-29 por la noche. Hacian un solo trabajo -- el tope hacia dentro
// del costado en el suelo y en el canto trasero, los dos tramos sin placa de
// anclaje -- y ese trabajo lo hace ahora el MARCO DE LA VENTANA (marco_fondo,
// mas abajo), que corre los siete tramos. Con ellos se van dos roscas ciegas
// por anillo y seis M3 sobre el acrilico de la trasera.

// --- LOS ANCLAJES DE LA CARA INTERIOR (2026-08-28) ---------------------
// TODA rosca ciega del anillo es M4 y cae a esta distancia de la silueta. Un
// solo tornillo y una sola cota, y las dos las manda la franja de 14:
//
//   por dentro  la pared del rebaje pide 1.5 D de la BROCA: 8.5 deja 5.5 y el
//               M4 pide 4.95. Un M5 pediria 6.3 y no cabe -- por eso los
//               miembros bajan de M5 a M4 (ver la nota de bom()).
//   por fuera   la placa y la brida apoyan con su canto EN la silueta, asi
//               que su propio agujero de paso (4.5) necesita 1.5 D = 6.75 de
//               ese canto. Con 7 la brida del miembro alto se quedaba en 5.5,
//               porque acaba t_costilla por debajo del canto (la meseta ocupa
//               ese milimetro y medio). 8.5 da 7.0 a la peor de todas.
//
// Entre 6.75 y 9.05 hay sitio; 8.5 es el punto donde las dos reglas tienen el
// mismo margen. Lo comprueba guarda_anclajes() rosca a rosca.
dist_rosca_ciega   = 8.5;
// EL MARCO DE LA VENTANA (2026-08-29, noche). Samuel dijo el 28 mirando el
// render que "la placa es el marco de la fila"; esta cota lo lleva hasta el
// final: las tres placas de anclaje, los dos clips y la escuadra de cada
// costado son UNA pletina de t_placa cortada a laser con el contorno de la
// ventana del anillo, corrida por los siete tramos. Sobre las tres filas es
// EXACTAMENTE la placa de ayer -- mismo canto visto de 6, mismos cajeados,
// mismas roscas --; en el frente, el suelo, la meseta y la trasera es el tope
// del acrilico que daban los clips y la escuadra, unificado: pisa 6 mm de
// acrilico volado por todo el perimetro y a traves del PMMA se lee una sombra
// uniforme de 6, no retazos.
//
// Cuanto entra desde la silueta, en los siete tramos. Fue placa_fondo. El
// cajeado del riel cae a 15.90 y su borde a 19.90, o sea 6.1 de pletina por
// detras; sobre la ventana (cara_anillo = 20) sobran 6, que hasta el
// 2026-10-11 pisaban el acrilico del costado.
marco_fondo        = 26;
// LA PATA TRASERA ENTRA 2 MAS (2026-08-29, noche, 2). Con la trasera capturada
// esa pata arranca en t_anillo + 0.5 = 14.5 (sobre la pared entre bolsillos)
// y con 26 se quedaba en 11.5 de ancho: sin tornillo -- en la franja trasera
// no cabe --, como viga empotrada-apoyada bajo carga_mano trabajaba a 129 MPa
// contra 130. A 28 son 13.5 de pata y 110 MPa. El tramo trasero ya es la
// excepcion de la ventana (el costado entra 3 ahi): pisa 8 de acrilico en vez
// de 6, detras de la plancha.
// 30 DESDE EL TECHO MACIZO (2026-08-30): el bolsillo de la trasera se mueve a
// u = 5.5..16.5 y su pared con el, asi que la pata arranca 2.5 mas adentro
// (en 17) y con 28 perdia ese ancho justo donde no hay tornillo. Con 30 y el
// retiro en 17 la formula de guarda_marco_ventana() da 1.54 mm y 114 MPa
// (techos 2 mm y 130); con 28 quedaba por un pelo. Los numeros son los de
// despues de subir la rendija a 4.0 (revision del 30-08); con la rendija en
// 3.0 eran retiro 16, 1.70 mm y 112 MPa.
// SE QUEDA EN 30 SIN EL CASO QUE LO PUSO (2026-10-11). El techo de 2 mm era el
// del acrilico saliendose del rebaje, y se fue con la mejilla; la tension (114
// contra 130) se sigue mirando con la persiana quitada, que es cuando la mano
// llega al marco. Bajarlo no compra nada que se vea.
marco_fondo_trasera = 30;
// Distancia MINIMA a lo largo del tramo entre el eje del riel y la rosca del
// marco mas cercana. 9.5 saca la cabeza boton M4 Ø7.6 de la huella de 10 del
// Z-Rail y deja 0.7 de aire. Si el extremo de una pata no permite abrazar el
// riel a +-9.5, las dos roscas pasan al lado interior, separadas 2 D de paso
// M4, sin acercar ninguna al riel. guarda_anclajes() comprueba tanto ese acceso
// como 1.5 D desde cada paso M4 hasta el borde del cajeado Ø8 (#242).
sep_rosca_riel     = 9.5;
// LAS DOS ROSCAS DE LA PATA DEL SUELO. El marco sustituyo a los clips y los
// clips llevaban tornillo: sin el, la pata del suelo (288 x 24.35 en pletina
// de 6, la mas larga del marco) cedia 3.31 mm bajo carga_mano como viga
// apoyada, y el acrilico se sale del rebaje con 3. Dos roscas ciegas M4 a
// esta distancia de cada extremo de la pata (del retiro de 11.2 tras P6 y del
// retiro del chaflan): dejan 168 entre ellas (0.16 mm) y 71 desde P6, que es
// lo que EMPOTRA la pata trasera, la unica que no puede llevar tornillo.
// Lejos de los tres M5 de la tabla, que entran por el canto inferior a 53.3,
// 159.9 y 266.5 (guarda_marco_ventana lo mide). El techo de flecha que puso
// las dos roscas (el acrilico se salia con 3) se fue con la mejilla el
// 2026-10-11; las roscas se quedan atando la pata del suelo.
rosca_suelo_retiro = 60;
// DONDE ARRANCA LA PATA DE LA CARA DE ARRIBA, medido desde P3. P3 es concavo
// y su redondeo de 54 curva la franja: el fondo util pasa de 8.51 en x = 128 a
// 12.45 en x = 148, o sea que una rosca a 8.5 de la silueta puesta en los
// sale por la pared del rebaje (taladros_anillo la cazo a 4.72
// contra 4.95). Las roscas de esa pata no pasan de aqui; cuando el par no cabe
// alrededor del riel, ss_roscas_riel() pone las dos hacia el interior sin
// acercarlas a su huella. La pata del valle cubre el rincon. Fue el retiro de
// la placa de la cara superior, con el mismo numero y por la misma razon.
retiro_placa_sup   = 12;
// DONDE EL CANTO EXTERIOR DEL MARCO SALE A LA SILUETA en la cara de abajo,
// medido desde la tangente del redondeo de P1. Antes de ese punto el marco va
// retirado t_costilla + hol_piel (retiro_marco() en el .scad) porque encima
// sube la NARIZ por la cara de abajo, y en las puntas las dos viven en la
// misma rebanada de z. El tope lo pone el cajeado del riel del frente, que
// tiene que quedarse a 1.5 D del escalon del canto (guarda_anclajes): con 9
// se queda en 7.08 contra los 6.75 que pide. Fue el retiro de la placa de la
// cara de abajo, con el mismo numero y por la misma razon.
// 11.9 desde el 2026-10-11 (persiana, D-S9): la nariz sube hasta pisar 0.98 de
// la cara del riel del frente y deja 1.02 al canto del panel, que cierra la
// rendija de la ficha 6. Era 9: la regla del barrido pedia 1 mm de aire BAJO
// el riel, y desde la tanda B los paneles son fijos. Lo vigila
// guarda_labio_chapas(); la pata del marco que arranca aqui la sigue
// guarda_anclajes().
retiro_placa_inf   = 11.9;
// Cajeado de la cabeza del M4 del riel, por el lado del anillo. Boton ISO
// 7380 M4: cabeza de 7.6 de diametro y 2.2 de alto.
d_cajeado_riel     = 8;
prof_cajeado_riel  = 2.5;
// LA BRIDA DE EXTREMO del miembro alto. Sale del mismo blank, doblada 90 del
// EXTREMO DE LA BANDA en cada punta -- sobre una linea PERPENDICULAR a la
// silueta, que es lo que hace legal su agujero: la distancia al doblez y la
// distancia a la silueta son cotas de ejes distintos --, con relieve en las
// dos esquinas, y apoya plana sobre la franja de la MESETA del anillo. 27 =
// 6 x d_M4_paso es lo minimo que reparte sus dos M4: el de dentro a SB + 2t +
// d/2 = 9.75 del propio doblez (regla de chapa), el de fuera a 1.5 D del
// canto libre, y 10.5 entre ellos.
//   OJO AL EJE: con el doblez paralelo al canto la distancia al doblez y la
//   distancia a la silueta serian la misma cota, 9.75 contra 9.05, y no hay
//   agujero legal. Es el mismo choque que tiene la pestana de la banda del
//   valle, y por eso ella no rosca en el anillo sino en el marco.
//
// El marco lleva una muesca de brida_ancho + t_costilla + 0.5 de honda,
// abierta a su canto exterior, sobre la huella de la brida. La trasera lleva
// una muesca de esquina porque la brida pasa bajo su esquina.
// DESDE EL TECHO MACIZO (2026-08-30) VIVE EN UN CAJEADO, y la prohibicion se
// respeta igual porque el cambio va en la DIRECCION SEGURA: como el labio
// entra 3 en el rebaje, la brida dobla en z = 11 y apoya en un cajeado de
// rebaje_chapa de fondo, quedando de z = 11 a 12.5 -- 1.5 POR DEBAJO de la
// cara. La muesca del marco se queda:
// las cabezas siguen asomando por encima de la cara.
// Se probo 34 la noche de la trasera capturada, cuando el bolsillo salia por
// el canto de arriba y pasaba por debajo de la brida: el M4 de dentro tenia
// que huir de su pared. El bolsillo esta CERRADO por los dos extremos y se
// cierra 0.5 sobre el canto de la trasera, 8.5 por debajo de las roscas de la
// brida y 1.0 por debajo de su canto (guarda_miembro_alto lo mide), y la
// brida se queda en 27.
brida_largo        = 27;
// Lo que la brida mide a lo ancho, contado desde t_costilla por debajo de la
// meseta (ahi va el otro ala, como siempre) hacia abajo. NO es toda la banda
// (24): en la franja de la meseta el marco tiene 26 de ancho y la muesca se
// come lo que la brida ocupa, asi que cuanto mas estrecha, mas marco queda
// entero en la esquina trasera-alta -- con 14.5 quedan 9.5 de pata, y el M4
// a 7.5 de su canto de abajo (a 7.0 del de arriba, el de siempre).
brida_ancho        = 14.5;
// La brida redondeada entra sin competir con el radio de la fresa.
radio_brida        = 2;
// LO QUE ESTE BLOQUE SUSTITUYE, y va escrito porque cada cota tenia su cuenta:
// fueron ala_costilla = 27 (la banda de chapa, derivada del M4 de la fila
// auxiliar a
// 1.5 D del canto de la ventana), ala_doblez = 16 (el ala que tapaba el canto
// del PMMA sobre un apilado de 13.5), cierre_p3_gap = 0.5 (la luz de raiz del
// rip soldado de P3), L_casquillo = 9.5 y t_junta = 4 (el casquillo que
// cruzaba el acrilico y la junta que se comia su juego), todas hasta el
// 2026-08-28. Se las llevo la pletina: no hay ala que doblar, ni esquina que
// soldar, ni acrilico que atravesar.
// Radio interior del plegado. Conserva el nombre pero desde el 2026-08-28 es
// el de LAS PIEZAS DE CHAPA (miembro alto, talon, nariz) y no el de la costilla: la costilla es pletina
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
// largo_riel, t_placa y t_anillo, que se declaran mas abajo. Aqui
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
// El de arriba sale mas CORTO aunque lleve el mismo estandar dentro: entre el
// canto del panel fijo y el vertice hay una PESTANA (marco_sup), no un perfil,
// y por eso caben 11 mm donde antes hacian falta 23.
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
// FILA AUXILIAR KONDOR. `alto_panel_1u` conserva el nombre legado porque lo
// consumen las interfaces de exportacion, pero ya no describe un formato 1U.
// Con 55.00 e inset_er = 3.0, sus dos Z-Rails quedan a 49.00 entre centros.
// guarda_fila_1u() exige la altura y la separacion propias, sin declarar
// compatibilidad vertical con formatos externos.
alto_panel_1u   = 55.00;
// Angulos de cara. El fichero los guarda DESDE LA VERTICAL (convencion del
// board), pero Samuel los especifica DESDE LA HORIZONTAL, que es como se
// miran en el alzado. La traduccion es a = 90 - horizontal:
//   cara de arriba  45 desde la horizontal  ->  45 desde la vertical
//   cara de abajo   55 desde la horizontal  ->  35 desde la vertical
// (los 45 coinciden en las dos convenciones; los 55 NO -- ojo con eso.)
//
// Historia, sobre renders sucesivos del 2026-08-17. Al variar el angulo fijo
// de una cara, el perfil gana FONDO y pierde ALTO: avanza sen(a) y sube cos(a).
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
// LO DE LA CURVA DE ARRIBA ES HISTORIA desde el 2026-08-29: la punta es RECTA
// (chaflan_nariz + radio_chapa), asi que alto_frontal ya no paga tangente.
//
// chaflan_nariz = el corte a 45 de la esquina de abajo-delante (vertice 0 del
// perfil), medido sobre cada arista: el contorno pasa de (0,0) a (c,0)-(0,c).
// Es la esquina de la referencia de Samuel: marcos laterales con la punta de
// abajo cortada a 45 y la banda de aluminio del frente siguiendo el corte.
// Debajo no hay modulos que se coma, y lo midio el modelo antes de elegirlo:
// la esquina mas baja del riel del frente esta a 13.3 del suelo y su esquina
// mas cercana a la nariz a x+y = 37.4; el panel de abajo arranca a x+y = 39.2.
// Con 6 quedan 13 mm de frente vertical. guarda_nariz() exige que quede frente
// (>= 5) y que el corte libre el riel por 5 mm.
chaflan_nariz   = 6;
// --- LA NARIZ: la banda del frente (2026-08-29) ---
// Chapa de t_costilla -- la misma de los marcos de la trasera -- doblada sobre
// la nariz del anillo: pie sobre la tabla, chaflan, frente vertical y un tramo
// subiendo por la cara de abajo hasta justo debajo de la placa de anclaje. Se
// atornilla a la TABLA por el pie, desde dentro, con tres M4: en la cara vista
// no hay tornillo, como en todo lo demas. El pie: 18 es lo minimo que reparte
// un M4 entre la zona del doblez (SB + 2t + d/2 = 9.75 desde la linea del
// chaflan) y 1.5 D del canto libre (6.75). 20.5 desde el techo macizo
// (2026-08-30): sigue al pie del talon, que crecio a 22.5 con la trasera
// retrocedida, porque guarda_talon() pide que los dos pies difieran 2 o
// menos -- mismo estilo -- y con 18 se ponia roja. Va bajo la tabla: no se ve.
nariz_pie       = 20.5;
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
// Era el 8 de la mejilla (t_cheek), que se fue con la persiana el 2026-10-11;
// desde entonces es un valor propio. Cambiarlo mueve el fondo del case, que se
// deriva de el.
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
// El valor vigente, 50, da el fondo de la meseta maciza y deja pasar la trasera
// capturada por delante del miembro alto. Los paneles y rieles son fijos: esta
// cota se valida sólo contra sus envolventes cerradas.
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
// Volvio a subir 1.47 mm porque el valle paso a alojar la fila auxiliar
// anterior: su boca tenia que medir 33.65 entre centros + 10.00 de cada Z-Rail = 43.65 mm
// libres entre sus caras, o 49.65 mm entre las caras exteriores de las dos alas
// de chapa. Esa boca sale directamente de paso_horizontal, que ahora gobierna
// guarda_fila_1u(); cada mm que entra aqui suma tambien uno al fondo del aparato.
//
// BAJA 3 mm el 2026-08-28, exactamente lo que las dos alas pierden al pasar de
// t_costilla 3 a 1.5: la boca es paso_horizontal - 2*t_costilla. Sin devolver
// esos 3 mm quedaria en 46.65; con 58.47 conservaba los 43.65 de aquella fila. El
// aparato gana esos mismos 3 mm de fondo por la chapa mas fina.
//
// SUBE 12.35 mm el 2026-08-31 para la fila auxiliar KONDOR de 55.00: la
// ventana crece de 46.653 a 59.003, aloja 49.00 entre centros + 10.00 de riel
// y conserva los 0.003 mm de margen util anteriores (los otros 3.00 eran las
// dos alas de t_costilla de la bahia). Cada mm anadido aqui suma un mm al
// fondo; el fondo nominal resultante es 319.76, siempre derivado.
//
// Lo vigila guarda_escalon(), que ya guardaba la otra holgura de este valle.
paso_horizontal = 70.82;
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
// radio_chapa = el radio EXTERIOR del doblez de la chapa de 1.5 mm
// (radio_doblez_costilla + t_costilla = 4.5), y es el radio de TODA esquina del
// anillo que lleva chapa doblada encima: las dos del chaflan de la nariz y el
// arranque de la cara de abajo (la nariz), el pico del techo (el retorno de la
// meseta), la esquina trasera-alta (la banda del miembro alto) y, desde la
// noche del 29, la trasera-baja (la banda del talon, que dobla ahi sobre la
// tabla). Es decir: las SEIS esquinas del anillo, porque la chapa las
// recorre todas; radio_trasero (0) murio con eso. Anillo y chapa
// tienen que compartir esquina: la chapa dobla con SU radio, no con el del
// anillo, y una esquina viva del anillo bajo un doblez a 90 asoma 1.9 mm
// (4.5 x (raiz(2) - 1)); bajo uno a 45, 0.4. Lo exige guarda_nariz().
//
// SUSTITUYE A DOS PARAMETROS el 2026-08-29:
//   radio_punta (400)  iba sobredimensionado a proposito para que la nariz
//                      saliera REDONDA -- _r_util lo recortaba al maximo de la
//                      arista corta, 30.1 en el arranque de la cara y 9.5 en
//                      la esquina de abajo. Samuel pidio lo contrario mirando
//                      el .blend: "en vez de una nariz curva, una nariz recta",
//                      como el marco lateral de su referencia. La nariz recta
//                      es chaflan_nariz abajo y esta esquina arriba.
//   radio_remate (2)   el radio de esquina de panel del #45, para que case y
//                      paneles remataran igual. Con la meseta llegando al pico
//                      y el marco de la trasera doblando en la otra esquina,
//                      lo que remata ahi es chapa, y manda su doblez.
// Desde la trasera capturada (2026-08-29, noche, 2) P6 va a CHAFLAN como P0,
// y P5 tambien con remate_trasero_chaflan = 1: este radio queda en P1 y P4 (y
// en P5 con la banda plana).
radio_chapa     = 4.5;
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
// POR QUE ALUMINIO Y NO ACRILICO MAS GRUESO: el aluminio de 3 resuelve la
// rigidez sin engordar el apilado estático sobre el Z-Rail. Ensanchar el
// larguero tampoco: un perfil de 30 entra por 0.24 mm
// (por debajo de la tolerancia de la propia extrusion) y uno de 40 no entra,
// se pasa 4.76.
//
// Y NO ROMPE EL LENGUAJE: los paneles de modulo ya son PCB de ALUMINIO a los
// dos lados de esta banda. Una tapa de aluminio entre dos filas de aluminio se
// lee como que la banda central pertenece a los paneles, no como un parche.
//
// Lo que se lleva por delante, y es ganancia: la unica linea de BOM de 5 mm.
// El cuerpo de acrilico queda con UN solo espesor, 8.
t_valle    = 3;    // ALUMINIO. Ver guarda_valle(); el material va en el PLIEGO
// LA TIRA NEGRA DEL VALLE (ficha 6, 2026-10-10): chapa de aluminio que tapa por
// dentro la rendija de la esquina de P3. Su pie va sobre el ala libre del riel
// de atras de la fila KONDOR, que mide 2, y su cara de fuera tiene que quedar
// fuera del camino del modulo KONDOR, que sale hacia arriba. Por eso es de 1:
// con 1.5 queda en el limite y con 2 lo roza. Lo vigila guarda_tira_valle().
// hol_tira_valle: lo que el pie se retira del canto del ala; hol_tira_valle_z:
// el juego contra cada marco.
t_tira_valle     = 1.0;
hol_tira_valle   = 0.1;
hol_tira_valle_z = 0.5;
// El borde trasero de la banda se prolonga a ESPESOR COMPLETO sobre el primer
// Z-Rail KONDOR. El rehundido de panel deja 0.10 de gap bajo los 3 mm de chapa;
// una tira oculta anti-ruido de 0.20 nominal cede 0.10 y entrega la carga.
apoyo_valle = 2.00;
tira_valle_nominal = 0.20;
compresion_tira_valle = 0.10;
// Ancho conservador de una mano apoyada de canto. Compartido por la puerta y
// el BOM para que la tension publicada no sea un literal envejecido.
b_mano_valle = 50.0;
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
// Era el 8 de la mejilla (t_cheek), que se fue con la persiana el 2026-10-11;
// desde entonces es un valor propio.
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
//
// 30 DESDE LA FICHA 12 (acta del 09-10, firmada «hazlo»): «una losa ... mas
// gruesa a la vista». La flecha ya no la decide: a 30 cede un quinto que a 18.
// Lo que cuesta es peso -- unos 5 kg la tabla entera a 0.65 g/cm3 (nogal,
// supuesto como E_madera), contra 2,3 --
// y 12 mm mas de aparato por debajo; el perfil y el interior no cambian.
t_base     = 30;

// El canto de ARRIBA de la tabla, redondeado (ficha 12): fresa de redondeo de
// carpintero. Solo el de arriba, el que se ve; el de abajo queda vivo.
r_canto_tabla = 8;

// Modulo de elasticidad de la madera A FAVOR DE VETA. 11000 MPa es nogal o arce
// -- el rango de manual para frondosas de densidad media va de 10000 a 12000.
// SUPUESTO DECLARADO hasta que la especie este elegida en el pliego: roble da
// 12000 (mejor) y el contrachapado 8000 (peor, pediria 20 mm).
E_madera   = 11000;

// Lo que la tabla sobresale del cuerpo por los cuatro lados. Es cota de MIRAR,
// no de calcular. Fue 10, de la foto de referencia del 26-08, donde el zocalo
// asomaba poco. DESDE LA FICHA 12 (acta del 09-10) son 40: con la piel encima,
// la losa asoma 28 por los costados y 34 por delante y por detras, dentro de los
// 25 a 40 que firmo Samuel (la vigilaba la regla 3 de piel_choques.py, que
// murio con la piel el 2026-10-11; la tabla esta en espera, D-S4).
//
// Y DESDE EL 10-10 DE VERDAD NADA CUELGA DE ELLA. Hasta ese dia los M5 con que
// la tabla se rosca al anillo se repartian en el fondo de la TABLA: un vuelo de
// 40 los subia de 3 a 4 por anillo y movia sus roscas ciegas, sin que nadie lo
// pidiera. Ahora se reparten en el fondo del CUERPO (n_agujeros()).
vuelo_zocalo = 40;

// Carrera del agujero alargado, por lado, en Z. La tabla mide ancho_total +
// 2*vuelo_zocalo a contraveta; una frondosa se mueve del orden del 0.25 % de su
// ancho entre invierno y verano en interior, o sea ~1.4 mm sobre 570. Se dan 2.5
// por lado (5 de carrera total) para cubrir un ambiente peor que el supuesto.
// El tornillo del medio de cada costilla va REDONDO: la tabla tiene que crecer
// hacia los dos lados desde un punto fijo, no arrastrarse hacia uno.
holgura_veta = 2.5;
// EL CAMPO DE AGUJEROS DE LA BASE (papel del suelo, 2026-10-12, sec.3.2 y 5).
// Ø5 al tresbolillo cada 8, el patron Rv 5-8: un 35,4 % abierto, y el puente
// entre agujeros mide 3, una vez el espesor. La regla de 0,8 veces es la del
// PMMA; para aluminio cortado a laser se pide 1 vez (Elke). El campo es una L
// que esquiva la huella del chasis y deja base_orilla libre junto al canto de
// los anillos, los pies de nariz y talon y el chasis. GEMELAS: campo_base()
// aqui y _campo_base() en el budget; check_dxf las cruza.
base_agujero = 5;
base_paso    = 8;
base_orilla  = 10;
// LOS INSERTOS DE PRESION (papel del suelo, sec.3.4). Van de acero o de
// inoxidable, nunca de la serie de aluminio: esa pide chapa de HB <= 89 y el
// 6082-T6 ronda 95. Se prensan despues de anodizar, y sus agujeros se cortan
// a cota de catalogo sobre la pieza anodizada. SUPUESTOS DE MEMORIA hasta la
// hoja de PEM (HUECO H4 del papel).
pem_cls_m4   = 5.4;   // tuerca CLS-M4, en los pies de nariz y talon (D-T2)
pem_fh_m4    = 4.0;   // esparrago FH-M4, en la base, para las patas
pem_borde    = 7.0;   // del centro de un inserto al canto o al borde de otro agujero
// El paso del M5 de los anillos en la base: medio milimetro de juego por lado
// para casar dos anillos mecanizados por separado. Los seis van redondos: la
// veta de la tabla se fue con ella.
d_M5_base    = 6.0;
t_panel    = 1.6;  // PCB de aluminio, espesor estandar JLCPCB
rehundido_panel = 1.50; // las tres filas: panel, riel, ejes y cajeados juntos
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
// ESTA LINEA LLEVA RIEL. El panel y sus dos rieles permanecen fijos al marco;
// la junta de 5 es una junta de sombra, no una holgura de movimiento.
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
// (*) El del valle NO lo pone su curva: por la curva bastarian 10, y lo que
// manda es LA BANDA DEL VALLE. Esa plancha va a ras del
// plano del valle, o sea con su cara de abajo a t_valle por debajo, y justo
// ahi asoma la esquina de arriba del riel del valle de la cara de ABAJO.
//
// 15.75 conserva holgura entre la banda y la envolvente CERRADA del Z-Rail.
// Ningun radio de giro ni estado de apertura gobierna esta cota.
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
n_bulkheads      = 2;    // anillos (3 si el vano flexa, spec §11)
// RIGIDEZ DEL COSTADO. Entran el 2026-08-25 con el retiro del entrepiso
// delantero: el case baja de cinco largueros a cuatro y el costado se queda
// con cuatro M5 en vez de cinco, asi que el vano sin apoyo crece y eso deja de
// poder darse por bueno a ojo.
//
// La puerta fue guarda_costado() en check_dxf.py hasta el 2026-10-11, cuando
// la mejilla se fue con la persiana -- y vivia ahi, y no en clearance_budget,
// porque media sobre el CONTORNO Y LOS TALADROS REALES de costado_2d.dxf, no
// sobre una copia de la geometria en Python. Los dos techos de abajo se quedan:
// carga_mano la leen el marco y la trasera, y flecha_costado_max el valle, el
// anillo y la tabla.
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
// Boca del avellanado de un M4 (ISO 10642, dk maximo). No es un agujero: es
// el CUERPO FIJO que la cabeza a ras deja en el pie del talon, y guarda_talon
// lo mide contra la cara de la trasera con la tolerancia del PMMA.
d_cabeza_M4_avell = 8.96;
d_M3_paso   = 3.4;  // agujero paso M3 (ISO holgura media)
d_M4_paso   = 4.5;  // agujero paso M4: standoffs de las pieles Y los seis
                    // rieles EUROrack, cuyo taladro de punta viene roscado M4
                    // de fabrica (hoja Tiptop: "M4 Tapping To (/)3.3")
d_M5_paso   = 5.5;  // agujero paso M5: SOLO el esqueleto 2020, roscado en el alma
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
// EL TORNILLO CON QUE LA PATICA SE ATORNILLA A LA TABLA (Tarea 6). El BOM
// de arriba dice "casquillo roscado" sin metrica -- no hay hoja de la
// patica citada con un diametro de rosca, y sin hoja no hay cota que leer.
// SUPUESTO = d_M4_paso: mismo herraje que ya usa el resto del case (12 M4
// de riel, 8 de brida, 4 de clip, 4 de lengueta de bahia), asi que no anade
// una talla nueva al pedido. Si el catalogo real trae otra metrica, este es
// el unico numero que hay que tocar.
d_pie_tornillo = 4.5;  // SUPUESTO M4 paso (=d_M4_paso), sin hoja de la patica
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
// Es una pieza fijada al mismo conjunto estático que el panel. gap_sombra es
// sólo una junta visual; no hay movimiento relativo.
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
// LA MESETA: el ala de arriba del miembro alto, medida del pico hacia atras.
// Fue 37 (acrilico apoyado en el riel), 29 el 2026-08-27 (ala del miembro,
// medida desde su doblez), 27.5 el 29-08 por la manana (#234: el marco de la
// trasera se comia 1.5) y 40.5 por la tarde: la meseta de chapa LLEGA AL PICO
// y elimina el inset heredado de la antigua pieza de acrilico.
//
// 50 DESDE EL 2026-08-29 POR LA NOCHE: LA MESETA LLEGA AL PLANO TRASERO y
// dobla ahi hacia abajo como banda_trasera. Ya no muere en el doblez de un
// alma 9.5 mm antes del canto, con el marco de la trasera tapando esos 9.5 y
// dejando una costura en el techo: el techo es una chapa del pico al canto.
//   = marco_remate; guarda_remate() lo exige (era marco_remate - t_piel -
//   t_costilla con el marco de la manana).
prof_sup    = 50;
// El RETORNO de la meseta: en el pico la chapa dobla hacia abajo por la cara
// de arriba este tramo, medido por la cara exterior desde el pico. Es lo que
// cierra el frente de la meseta sobre el Z-Rail fijo -- y de paso mata la ola del
// canto libre de 528 mm y el canto vivo que lo hacia leerse como REPISA.
// 9 desde el 2026-10-11 (persiana, D-S9): el retorno baja hasta pisar 1.0 de
// la cara del riel del remate y deja 1.0 al canto del panel. Era 4 por
// holgura_rail sobre el riel, una regla del barrido de cuando las filas
// giraban, y dejaba una linea de sombra de 6 mm por la que se veia el ambar de
// dentro (la rendija de la ficha 6). Lo vigila guarda_labio_chapas().
retorno_meseta  = 9;

// --- ventilacion con firma (spec §7) ---
// Diametro de la fresa estandar del taller. NO es decoracion del BOM: manda
// sobre toda la geometria interior, porque una fresa no puede entrar en un
// hueco mas estrecho que ella ni dejar una esquina interior mas cerrada que su
// radio. Schaeffer: fresa minima 1 mm (radio interior 0.5), y la de 3 mm es la
// estandar -- pedir un radio mas cerrado obliga a cambio de util y se paga.
// guarda_fresado() en clearance_budget.py lo comprueba contra la geometria.
fresa_d           = 3;
// 3.75 DESDE EL 2026-08-28, y no es una cota de gusto: es una RESTA. El puente
// que queda entre dos columnas de la rejilla trasera vale
// valle_paso_hp*hp - vent_ancho_ranura = 10.16 - ancho, y sobre PMMA de
// t_piel = 8 ese puente tiene que llegar a 0.8*8 = 6.40 (la regla de plancha
// perforada de siempre; la asevera guarda_puentes_ventilacion). Despejando,
// el ancho maximo es 10.16 - 6.40 = 3.76, y se redondea hacia ABAJO al cuarto
// de milimetro para no dejar la cota clavada en el limite: 3.75 deja 6.41.
//
// CON 4 EL ACRILICO ESTABA POR DEBAJO DEL MINIMO -- 6.16 de puente contra 6.40
// -- y ninguna puerta lo cantaba, porque la que existia comparaba vent_puente_min
// contra t_valle, el espesor de la banda del valle, que desde el 2026-08-28 no
// lleva NI UNA ranura. La regla estaba bien y apuntaba a la pieza equivocada.
//
// Sigue por encima de fresa_d (3.75 >= 3), que es la otra condicion que este
// numero tiene que cumplir y la que vigila guarda_fresado().
vent_ancho_ranura = 3.75; // 10.16 - 0.8*t_piel = 3.76, al cuarto por abajo
// 6.5 DESDE EL 2026-08-28, por la MISMA regla y contra la MISMA pieza. Este no
// es el puente entre columnas (ese sale de la resta de arriba y no tiene
// parametro): es el aire que la rejilla le deja a cualquier OTRO hueco de su
// plancha, y hoy ese otro hueco es la ventana de la entrada de red. Si no
// aguanta 0.8*t_piel = 6.40, los dos recortes se comen el acrilico que queda
// entre ellos. 6.5 y no 6.40 porque una cota redonda al medio milimetro se lee
// en el plano y deja 0.1 de margen sobre el minimo.
//
// LO QUE CUESTA, que no es cero: sube el borde de abajo de la banda libre de la
// trasera (_banda_libre_trasera lo forma con valle_espina/2 + vent_puente_min),
// o sea que la rejilla de entrada se acorta y guarda_aire() lo cobra en salto
// termico. Es el precio de que el puente aguante, y va escrito aqui para que
// nadie lo devuelva a 4 buscando area.
vent_puente_min   = 6.5;  // 0.8*t_piel = 6.40, subido al medio milimetro
vent_periodo      = 40;  // periodo horizontal de cada onda
// Separacion entre el CAMPO DE RANURAS de la trasera y la banda de ondas que
// tiene encima. NO es vent_puente_min, y esa confusion es justo lo que se
// arregla aqui: el puente minimo es una cota de FRAGILIDAD -- lo que hace falta
// para que dos huecos no se coman el acrilico que queda entre ellos -- y con 4
// mm los dos campos se leian como uno solo. Esto es una cota de DIBUJO: lo que
// hace falta para que la rejilla y las ondas se lean como DOS cosas.
//
// SIGUEN SIENDO DOS COTAS DISTINTAS aunque el puente subiera a 6.5 el
// 2026-08-28: 14 > 6.5, asi que quien manda aqui sigue siendo el dibujo. El dia
// que el puente de fragilidad pase de la separacion de dibujo, este 14 dejaria
// de decidir nada y habria que subirlo -- pero eso mueve la onda con el, por lo
// que dice el parrafo de abajo.
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
// (vent_ancho_ranura 3.75 >= fresa_d 3). Va desde la cara EXTERIOR: hoy no hay
// iluminacion interior (spec §12 deja la WS2812 fuera de alcance), asi que un
// cajeado por dentro seria casi invisible. Si algun dia entra esa luz, voltear
// la cara es una linea en piel_trasera().
//
// LO QUE COSTO EL 2026-08-24: 0.5 K. La salida bajo de 12609 a 9943 mm2 y el
// salto termico subio de 6.6 a 7.1 K contra un techo de 15 -- eso midio el A/B
// de ese dia, no la corrida de hoy. HOY, con la rejilla y el puente de
// fragilidad movidos el 2026-08-28, guarda_aire() imprime 3141 mm2 de salida
// y 10.8 K en cada corrida. LOS DOS SON DE CUANDO potencia_disipada eran 9.22:
// desde el 2026-09-03 son los 147.83 W del cajon entero y el salto termico que
// imprime esa puerta es otro (77 K, publicado como HUECO). Lo que sigue siendo
// verdad de estas dos ondas es POR DONDE sacan el aire: por debajo del
// entrepiso, o sea el camino del valle y no la bahia de arriba, que es justo
// lo que este cajeado sella.
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
// vent_periodo*0.35 + vent_ancho_ranura/2 = 15.88 con el ancho de 3.75 que fijo
// el puente de fragilidad el 2026-08-28, o sea 31.75 de banda; con el 4 de antes
// eran 16 y 32 clavados), asi que la
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

// --- banda delantera del valle; la meseta queda maciza ---
// De la antigua tapa solo queda la banda LISA del vuelo delantero. Es la
// cara horizontal visible de pie delante del aparato. Samuel la pidio
// "modernista pero seria, como si fuera de Darmstadt": nada figurativo. Las
// ondas de las pieles DIBUJAN una senal; esto es un campo de ranuras y punto.
//
// Y no es un campo cualquiera: va REGISTRADO AL RACK. Una ranura en cada linea
// HP par, o sea que cada una cae en un canto de modulo. El paso no es una
// eleccion de dibujo, es la medida del instrumento; el adorno ES la regla.
//
// Las ranuras salieron tambien de la meseta: el alero toma ahora la salida.
valle_paso_hp   = 2;   // nombre historico: malla de la ENTRADA trasera
// RETIRADOS EL 2026-08-30, y quedan escritos para que no vuelvan por descuido.
// Nacieron el 28-08 cuando las ranuras salieron del valle y subieron a la
// meseta, donde mas altura da mas tiro: paso 6 HP -> 16 ranuras registradas al
// rack, largo 15, 852 mm2. Samuel las mato mirando el .blend: "en la pieza
// miembro alto no me gustan los huecos, es una decision erratica del diseno ya
// que esa parte es sensible a que le entren liquidos". Y tenia razon: era la
// unica cara horizontal de arriba, con un agujero mirando al cielo. La salida
// equivalente es ahora la rendija del alero (aire_labios), que mira al suelo.
// Siguen aqui porque guarda_puentes_ventilacion() y el test de rotura de
// check_dxf.techo_macizo() los usan para reconstruir el techo viejo.
meseta_paso_hp  = 6;
meseta_largo_ranura = 15;
// LOS TACOS DE LA JUNTA (2026-08-30). La spec del 29-08 dejaba "una tira
// continua de EPDM con la primera pieza"; una tira cierra la rendija y mata la
// salida de aire. Son tacos: sujetan la plancha sin que suene, FIJAN LA LUZ
// (el taco es la luz) y dejan la rendija libre entre ellos. Misma regla en el
// labio del techo y en el del talon; solo la de arriba cuenta como salida.
taco_largo      = 15;    // mm, adhesivo, uno cada ~90 a lo largo del labio
taco_n          = 6;     // por labio
// Lo que cede el EPDM apretado. SUPUESTO sin puerta sobre el espesor real ni
// el alabeo: lo cubre el ensayo de derrame (§8 de la spec). Manda porque la
// capilaridad va con 1/d y el peor caso es la luz COMPRIMIDA, no la nominal.
compresion_taco = 0.2;
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
// Fue 6.33 W: la spec de la fuente v2, §4, sumando los reguladores (LM2941
// ~2.7 + LM2991 ~2.9 + LT3045x2 ~0.4 + LT3094x2 ~0.33), SIN las perdidas del
// transformador, que no estan itemizadas -- por eso el techo de salto termico
// va holgado y no pegado al numero.
// 9.22 DESDE EL TECHO MACIZO (2026-08-30): el peor caso del chasis del PSU
// segun su propia spec, que NO es a plena carga sino a MEDIA -- el
// prerregulador disipa su maximo con el rail a I ~ 0.50 A, no a 650 mA --, con
// el LED del #104 al tope. Los modulos seguian fuera de la formula: el repo
// declaraba que la bahia de arriba esta sellada del camino del PSU, y sus
// vatios eran "un presupuesto que falta".
//
// 151.55 DESDE LA FUENTE v4 (2026-09-04), que es ese presupuesto ya hecho.
// Deja de ser el chasis del PSU y pasa a ser TODO lo que se enciende dentro
// del cajon, con su desglose (papel de la fuente v4 sec.6, hardware/
// 01-power-supply/v4/calor_budget.py):
//
//    31.25 W  el recinto de la fuente, todo a placa y ya con D-F7 (PS5 es
//             una IRM-45-5, no una IRM-20-5: 3.95 W en vez de 5.32).
//             Eran 27.53 hasta el 2026-09-04: a la tabla del papel sec.6
//             le faltaba la FRANJA DE RED, que tambien vive dentro del
//             recinto -- la NTC de arranque disipa 2.75 W a los 3.25 A rms
//             del liston y el choke otros 0.95 (ESTIMADO). Lo destapo
//             v4/fusible_budget.py, que asevera la cifra de la NTC contra
//             la constante de v4/calor_budget.py
//   118.08 W  la fila de invitados a placa (95.6), el digital (14.475) y la
//             VOZ (8.00): los +-12 V ultra que la cascada le entrega y que
//             ella disipa aqui dentro. Eran 110.08 hasta el 2026-09-05: la
//             carga ultra no estaba en ninguna celda, ni en el cajon ni en
//             el recinto. Lo encontro el papel de la fila B (04-09, sec.7.1)
//
// El liston de la PSU3 (D-F1) puso el numero y D-F3 = A --ventilar por
// conveccion natural, sin ventilador, firmada el 03-09-- dice que hay que
// dejarlo salir. Esta geometria evacua 12.6 W al techo de 15 K, asi que
// guarda_aire() ya NO asevera ese techo: publica el deficit como HUECO con
// el area que hace falta. La obra que lo cierra es del papel del case (#289).
// La cerro la persiana con la fuente v5: ver el parrafo del 2026-10-12, abajo.
//
// DE 151.55 A 147.31 EL 2026-09-05, EN DOS CORRECCIONES DE SIGNO CONTRARIO, y
// ninguna para que una puerta pase. Las dos son la misma regla mal aplicada:
// todo lo que baja por un riel acaba en calor donde vive la carga.
//
//   -12.24  el digital cobraba 24.7 W = 4.935 A x 5 V, y esos 4.935 son
//           2.895 de cargas duras MAS 2.04 de la cadena de LED que D1 retiro
//           entera el 03-09 (instrumento-entero l.106). La enmienda E16 de
//           aquel papel lo mandaba y nadie la aplico. Los otros 2.02 son PS6,
//           que sigue al digital y arrastraba la misma cifra. Calor de una
//           pieza que no se monta.
//    +8.00  la VOZ no estaba. Los +-12 V ultra que la cascada le entrega
//           --12 V x (340 + 327) mA, el censo de 03-vco/consumo_total_budget--
//           se disipan en la Voz, dentro del cajon, y no los contaba ni el
//           cajon ni el recinto. El recinto si contaba la perdida de
//           FABRICARLOS. Lo encontro el papel de la fila B (04-09, sec.7.1) y
//           tambien quedo sin aplicar.
//
// Las dos se arreglaron en el origen --v4/calor_budget.py, y la de la Voz
// derivada del censo, no transcrita-- que es lo que esta misma guarda pide.
// 64.22 DESDE EL PLAN DEL AIRE (2026-10-12): la fuente v5 (D-V4) saca la
// etapa AC-DC de la caja, y el calor del cajon es lo que baja por el cordon
// del ladrillo (hardware/01-power-supply/v5/ladrillo_budget.py,
// calor_del_cajon_w(): 56.23 W entregados a las cargas + 7.99 perdidos
// convirtiendo dentro). La v5 lo mando el 05-09 en su sec.7 y quedo sin
// aplicar hasta aqui. El desglose de arriba es el de la v4, que no se monta.
// ES COTA DE ABAJO: la enmienda M1 de la v5 aisla el +5 V digital y deja su
// perdida sin valor hasta que haya pieza (H-CENSO-ETA-DIGITAL).
potencia_disipada = 64.22; // W, TODO el cajon: lo que baja por el cordon (fuente v5)
// Techo de salto sobre ambiente. 15 K era el criterio de siempre para caja de
// electronica lineal con electroliticos dentro: a partir de ahi la vida del
// condensador se parte por dos cada 10 K y deja de ser un detalle.
//
// SUBE A 20 EL 2026-09-04, y NO para que una puerta pase: para dejar de
// contradecir al resto del instrumento. tuning_budget.py l.73 lleva semanas
// calculando la deriva de afinacion con
//
//     DELTA_T = 20.0   # C de excursion desde la calibracion. Un cajon
//                      # cerrado con tres reguladores dentro sube facil
//                      # 15-20 C sobre ambiente en una hora.
//
// y PASA con 1.68 cents contra un objetivo de 5.0 -- 3x de margen. O sea que
// el sitio donde la temperatura de verdad importa (el tono) ya estaba
// dimensionado a 20 K mientras el case prometia 15 sin argumentarlo. De los
// dos numeros el que tiene fuente es el de la afinacion; este era SUPUESTO.
//
// LO QUE ESTE CAMBIO NO HACE: no cierra el #289. Con el modelo termico de la
// fuente v4 (35e1bb2) el instrumento solo ya pide 50.3 W y sube 37.7 K por la
// chimenea, asi que el deficit sigue ahi y guarda_aire() lo sigue publicando
// como HUECO. Solo deja de haber dos techos distintos en el mismo aparato.
// Lo cerro el 2026-10-12 el plan del aire: la fuente v5 afuera y las persianas.
salto_termico_max = 20;  // K sobre ambiente; fuente: tuning_budget.py l.73

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
// CERO DESDE EL 2026-08-29 POR LA NOCHE: el suelo del chasis APOYA en la tabla
// y se atornilla a ella por debajo. Los 2 mm de aire eran para no apoyar el
// toroide en una bandeja de ACRILICO que resonaba (#106); esa bandeja murio el
// 27-08 y lo que hay debajo es la tabla de 18 de madera maciza, que se pidio
// justamente para eso. El M5 de pared que ataba este numero por arriba
// apuntaba a la ranura de un 2020 que murio el mismo 27-08.
chasis_pie      = 0;

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
// mas; por eso el hueco existe y no se cierra a cero.
//
// DESDE EL 2026-08-29 POR LA NOCHE ES LA HOLGURA AL PIE DEL TALON: la pared
// trasera del chasis se arrima al canto libre del pie (x_talon_pie), que es
// lo que hay detras, y de ahi hacia delante no hay nada. Los 4 M5 de pared
// que la nota de arriba describe apuntaban a la ranura interior de un 2020
// muerto el 27-08 -- el modelo los siguio dibujando dos dias --; el chasis
// se atornilla ahora a la TABLA por el suelo (chasis_tornillo_x/y).
chasis_holgura_larguero = 3;
// LOS CUATRO M4 DEL SUELO A LA TABLA, en coordenadas INTERIORES del chasis.
// Desde abajo de la tabla, a tuerca remachable (clinch, PEM S-M4) en el suelo
// de acero: cabezas bajo la tabla -- el case va sobre sus paticas de 10 -- y
// nada visto por dentro. Van en las dos orillas libres de 10 mm que la PCB
// (x = 10..210) y el toroide dejan a cada lado: x = 8.5 deja la cabeza de
// 7.6 a 2.7 de la pared, fuera de la curva del doblez (r + t = 3), y y = 20
// deja al de la derecha 2.75 de aire hasta el refuerzo del toroide (que
// arranca en y = 25) y al de la izquierda 8.2 mm hasta el separador de la
// esquina de la PCB. Lo comprueba guarda_chasis(); las posiciones en la tabla
// las cruza guarda_zocalo() en check_dxf.
chasis_tornillo_x = 8.5;
chasis_tornillo_y = 20;
chasis_tornillo_baja  = 8;   // cuanto por debajo del techo va la fila de M3
chasis_tornillos_largo = 3;  // por faldon largo
chasis_tornillos_corto = 2;  // por faldon corto
salida_holgura = 6;   // orilla del agujero del acrilico alrededor de la ranura
salida_radio   = 8;   // esquinas redondeadas: el acrilico raja desde una viva
