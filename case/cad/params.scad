// params.scad — unica fuente de verdad dimensional del case.
// Unidades: mm y grados. Angulos de cara MEDIDOS DESDE LA VERTICAL
// (convencion del board de diseno, spec §4 rev. 3).
// clearance_budget.py parsea este fichero: solo lineas `nombre = valor;`
// con valores numericos. No usar expresiones en este fichero.

// --- silueta (spec §4 + board 350 x ~380) ---
ancho_total     = 500;   // spec §4
// CARA vs PANEL. Hasta el 2026-08-17 eran el mismo numero y por eso la puerta
// de EUROrack estaba en rojo: con la cara valiendo 128.5 y los railes a 27 de
// cada punta, los railes quedaban a 74.5 y un modulo 3U NO atornilla.
//
//   alto_cara_*  = el TRAMO DEL PERFIL del costado. Es lo que dibuja la
//                  silueta y donde se atornillan los railes.
//   alto_panel_* = la PCB de aluminio que se monta encima. Es lo que
//                  consume build_template.py y lo unico que ve el fabricante.
//
// En el piso de ARRIBA coinciden (el panel cubre la cara entera). En el de
// ABAJO no pueden: el panel 3U mide 128.5 con sus taladros a 3.0 mm de cada
// canto, o sea 122.50 mm entre centros ("ER Screw distance vertical",
// Doepfer). Ese 122.50 es la cota que manda -- no el alto del panel --, y
// alrededor de cada riel hace falta acrilico. De ahi sale la cara:
//
//   alto_cara_inf = sep_railes_inf + inset_tornillo + inset_valle
//                 = 122.5 + 27 + 15 = 164.5
//
// Las dos puntas piden distinto y por eso los insets son asimetricos (ver
// inset_valle abajo). El panel queda centrado en sus railes y sobra bisel:
// 24 mm por delante -- de los que 15 se los come la curva en punta -- y 12
// por el valle, de los que 2.6 se los come el pico. Samuel pidio
// explicitamente apretar el lado del valle ("llevarlo mas cerca del hueco
// del tornillo"), y ese es el lado que se aprieta.
//
// ASUMIDO, pendiente de Tobias (SynthRacks): que el riel EUROrack real se
// atornille sobre el 2020 con su linea roscada EN LA CENTERLINE del 2020. Si
// su perfil pone la rosca descentrada, lo que cambia es inset_valle y con el
// alto_cara_inf -- la silueta se adapta sin tocar nada mas.
alto_cara_inf   = 164.5; // DERIVADO: sep_railes_inf + inset_tornillo + inset_valle
alto_cara_sup   = 190;   // spec §4, altura de panel de la tesis
alto_panel_inf  = 128.5; // PCB 3U EUROrack (build_template.py --piso inf)
alto_panel_sup  = 190;   // PCB del piso de arriba = cara entera
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
// nodos que pidio Samuel, y tienen que caber uno encima del otro. El de la
// base ocupa y = 0..20; el del panel va empujado hacia ABAJO por el offset
// perpendicular (la normal interior de una cara empinada apunta adentro y
// abajo), asi que su centro cae en alto_frontal + cos(a)*inset - 6.65 y su
// canto inferior 13.93 mas abajo. Exigiendo holgura_rail entre los dos:
//   alto_frontal + cos(35)*inset >= 44.58
// A alto_frontal = 10 el riel del panel se montaba 22.3 mm ENCIMA del de la
// base (solapes() lo canto). Las dos condiciones juntas dan un minimo de
// ~26 mm de vertice frontal; 30 con inset 27 deja 7.5 mm de holgura entre
// railes y 2 mm de margen contra la curva.
alto_frontal    = 30;
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
// arriba -- que es EXACTAMENTE la que Samuel dijo que le gustaba como estaba.
// A 6.7 mm de marco el radio en punta se recorta a 3.3 y la esquina queda
// casi viva; a 57 vuelve la meseta. Con el marco fijo, la esquina se
// conserva aunque se muevan las proporciones, que es lo que se quiere.
//
// 22 mm da la punta redondeada que se aprobo (era 21.7 con el fondo en 345 y
// los angulos 35/45). Por delante nunca hay nada que recortar: el riel de
// panel de la cara de abajo llega a x=11.1, y 11 mm es justo el material
// minimo que quiere un M5 al canto.
marco_remate    = 22;
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
rail            = 20;   // perfil 2020
// Tornillo de panel, distancia al borde del panel. FUE 5 y era imposible:
// el rail 2020 va ALINEADO con la cara, asi que se extiende +-rail/2 = +-10 mm
// a lo largo de ella. Centrado a s=5 ocupaba de s=-5 a s=+15, o sea que
// asomaba 5 mm POR DELANTE del arranque de la cara, donde no hay acrilico
// ninguno. Lo destapo `railes_dentro_del_costado()` en check_dxf: tres de los
// cuatro railes de panel se salian de la pieza (2.7 mm por el frente, 2.0 por
// el valle, 1.2 por el remate). Ventana valida: >= 10 para que el rail quepa,
// y <= 13 para que el tornillo siga cayendo dentro de la boca de la ranura
// (~6 mm, o sea +-3 mm del centro de la cara). 10 lo centra exacto.
inset_tornillo  = 27;
// inset_valle = el inset del OTRO extremo de la cara inferior, el que da al
// valle. Es asimetrico a proposito: las dos puntas de esa cara no se comen lo
// mismo. Por delante la curva en punta vacia alto_frontal/2 = 15 mm de cara,
// asi que el riel no puede empezar antes de 15 + rail/2 + 2 = 27. Por el
// valle el vertice lleva radio_pico = 5 y su tangente mide solo 2.60 mm, asi
// que con 2.6 + rail/2 + 2 = 15 basta. Forzar la simetria costaria 12 mm de
// cara -- y ese es justo el sitio que Samuel pidio recortar ("bajar la
// posicion donde esta el acrilico del medio", 2026-08-17).
inset_valle     = 15;
// EUROrack, cotas del PANEL (no de la cara). Verificado el 2026-08-17 contra
// midisoft.de y exploding-shed.com: taladro a 3.0 mm del canto superior e
// inferior (de ahi los 122.50 entre centros) y el primero a 7.5 mm del canto
// izquierdo, con paso horizontal multiplo de 5.08 (1 HP). Los usa
// build_template.py para colocar los taladros del piso inferior; el piso
// superior no es EUROrack y sigue con inset_tornillo en los dos ejes.
inset_er        = 3.0;
inset_er_x      = 7.5;
// EUROrack manda aqui: "ER Screw distance vertical = 122.50 mm" (Doepfer).
// OJO: los rieles comerciales varian -- Vector pide 121.46 y Tiptop 122.43 --,
// asi que este numero se re-fija contra el riel que se compre. Es el ASUMIDO
// principal de la silueta actual.
sep_railes_inf  = 122.5;
sep_railes_sup  = 136;  // centros de rail = alto_cara_sup - 2*inset = 190 - 54
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

// --- ventilacion con firma (spec §7) ---
vent_ancho_ranura = 4;   // ancho de la ranura-onda
vent_puente_min   = 4;   // puente minimo entre ranuras (fragilidad)
vent_periodo      = 40;  // periodo horizontal de cada onda

// --- lo que el budget vigila (spec §11: catalogos, no medidos) ---
alto_transformador  = 45;  // CATALOGO, no confirmado; medir pieza real
margen_transformador = 15; // spec §4
fondo_pcb_max       = 60;  // censo estimado de PCB mas honda, no confirmado
