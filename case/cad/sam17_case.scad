// sam17_case.scad — consola de dos pisos en acrilico naranja (spec rev. 3).
// Fuente de verdad dimensional: params.scad. Este fichero DIBUJA;
// clearance_budget.py DECIDE. Angulos desde la vertical.
//
//   openscad -o out.stl -D 'PART="costado"'    sam17_case.scad
//   openscad -o out.dxf -D 'PART="costado_2d"' sam17_case.scad

include <params.scad>
PART = "assembly";
// $fn vive en params.scad: asi lo hereda TODO .scad que incluya params.
// Tenerlo aqui fue el bug del cupon pentagonal (ver nota en params.scad).

// ancho interior entre costados; Tasks 4-5 lo consumen como ancho_util.
// EL HUECO ENTRE COSTILLAS, no entre acrilicos, desde el 2026-08-26. Todo lo
// que vive dentro del case -- largueros, rieles, planchas -- va de cara interna
// a cara interna, y esas caras dejaron de ser el acrilico: son el ala de la
// costilla, que se le monta encima. Restar solo t_cheek dejaria 2*t_costilla de
// hueco fantasma y las planchas crecerian 6.3 mm para llenar un sitio ocupado.
//
// Y SE USA ESTA VARIABLE, no la resta a mano. Estuvo repetida en nueve sitios
// de este fichero, y con dos terminos la copia se desincroniza del original al
// primer cambio -- que es como esta cota llego a existir sin que nadie la
// mirara.
// LO QUE SE RESTA CAMBIO TRES VECES: el acrilico y la costilla hasta el
// 2026-08-27; el CASQUILLO y la costilla desde ese dia -- con el marco por
// fuera era el casquillo el que fijaba el hueco entre marco y riel --; y desde
// el 2026-08-28 SOLO EL ANILLO. El acrilico ya no aparece porque va DENTRO de
// la ventana: la pared del anillo es la unica pieza entre este hueco y el
// exterior.
//
// LA PLACA DE ANCLAJE SI ESTA DENTRO de este hueco, y por eso no se resta
// aqui: el riel mide ancho_util - 2*t_placa y muere contra ella.
//
// GEMELA de perfil()['ancho_util'] en clearance_budget.py -- si las dos se
// separan, la rejilla de agujeros del DXF se corre y lo canta
// agujeros_donde_toca().
ancho_util = ancho_total - 2*t_anillo;

// Las cotas visibles cuelgan de primitivas para que el empotramiento se mueva entero.
function rehundido_trasera() =
    rehundido_chapa + t_costilla + aire_labios - t_junta_asiento;
function ancho_bolsillo_trasera() = t_anillo - rehundido_acrilico;
function pared_trasera_u() = rehundido_trasera() + ancho_bolsillo_trasera();
function cara_anillo_trasera() =
    pared_trasera_u() + pared_rebaje_trasera + entrada_costado_trasero;
function radio_borde() = radio_chapa + rehundido_chapa;
function pie_z0() = t_anillo + hol_piel;
function muesca_pie() = rebaje_chapa - hol_chapa + hol_piel;
function chapa_z0() = pie_z0() - muesca_pie();
function chapa_largo_rebaje() = ancho_total - 2*chapa_z0();
function cajeado_brida_largo() = brida_largo + 2*hol_chapa;
function cajeado_brida_ancho() = brida_ancho + 2*hol_chapa;
function radio_cajeado_brida() = fresa_d/2;

// vertices del perfil lateral (X = fondo, Y = arriba) — misma numeracion
// que clearance_budget.perfil(): p0..p8
// Fondo del case. DERIVADO, no parametro: es la proyeccion de la hipotenusa
// mas el marco de remate (ver la nota larga en params.scad). Se calcula sin
// llamar a pts_perfil para no morderse la cola.
function fondo() = alto_cara_inf*sin(angulo_inferior) + paso_horizontal
                 + alto_cara_sup*sin(angulo_superior) + marco_remate;

function pts_perfil() =
    let (si = sin(angulo_inferior), ci = cos(angulo_inferior),
         ss = sin(angulo_superior), cs = cos(angulo_superior),
         ye = alto_frontal + alto_cara_inf*ci,        // y entrepiso
         x2 = alto_cara_inf*si,                       // fin cara inferior
         x3 = x2 + paso_horizontal,
         x4 = x3 + alto_cara_sup*ss,
         yt = ye + alto_cara_sup*cs,                  // alto total
         pf = fondo())
    [[0,0],[0,alto_frontal],[x2,ye],[x3,ye],[x4,yt],
     [pf,yt],[pf,0]];
// 7 puntos, no 9: el canto trasero es UN plano a plomo de toda la altura.
// La version anterior metia p5..p7 en una repisa escalonada entre
// prof_superior=250 y prof_inferior=350, y esa repisa era la que rompia la
// lectura de triangulo. Al colapsarla, p5=(fondo,yt) y p6=(fondo,0), o sea
// que el ANTIGUO P[8] (esquina trasera baja) es ahora P[6] -- ojo al leer
// codigo viejo. x4 = fin de la cara superior; de x4 a fondo() queda el
// marco de remate.

// puntos medios de riel por cara: centros sobre la cara a sus dos insets,
// retirados hacia dentro t_panel + rail_er_eje segun la normal.
//
// Los DOS insets de cada cara son distintos (ver la tabla de insets en
// params.scad): la punta redondeada del frente vacia 15 mm de cara y el pico
// del valle solo 2.6, asi que exigir el mismo inset en los dos extremos
// regalaria 12 mm de altura de piso sin comprar nada.
//
// SON CUATRO: dos por cara, como cualquier fila EUROrack. Estuvieron en TRES
// hasta el 2026-08-17 porque la bisagra ocupaba la linea de tornillo de arriba,
// y un nudillo no es un riel: no tiene ranura ni tuercas, no le atornillas un
// modulo. Samuel lo cazo mirando el render. La bisagra se mudo a la arista del
// techo (ver eje_visagra()).
//
// LOS CUATRO LLEVAN M5 AL COSTADO, pero no todos hacen lo mismo:
//   cr[1]         EJE de la fila de abajo, que TAMBIEN es tapa (guarda_tapa).
//   cr[0]         CIERRE de la fila de abajo: se quita para abrirla.
//   cr[3]         EJE de la fila de arriba. Tornillo de hombro, no se aprieta.
//   cr[2]         CIERRE de la fila de arriba.
// (Decia "cr[0], cr[1] fijacion, la cara de abajo no se mueve" hasta el
// 2026-08-29: llevaba dos dias desmentido por guarda_tapa() y por params.)
// Aqui hubo un rato en que cr[2] no llevaba taladro, con el argumento de que
// con los dos extremos empernados la tapa no gira. Cierto, pero de ahi no se
// sigue dejar el riel sin nada: se sigue que ese tornillo sea QUITABLE. Samuel
// lo cazo en el render preguntando donde estaba el tornillo de ese riel.

// Semiextension del riel EUROrack ya girado con su cara. NO es un cuadrado:
// mide rail_er_alto a lo largo de la cara y rail_er_fondo hacia dentro, asi que
// cada eje del mundo recibe una mezcla distinta. Con el 2020 los dos daban lo
// mismo y bastaba r*(cos+sin) -- con la seccion real hay que separarlos, y ese
// atajo ya costo dos fallos en este case (x_ed en la Tarea 5, el techo del
// remate en el marco de 8).
function he_er_x(a) = rail_er_fondo/2*abs(cos(a)) + rail_er_alto/2*abs(sin(a));
function he_er_y(a) = rail_er_fondo/2*abs(sin(a)) + rail_er_alto/2*abs(cos(a));

function centros_rail() =
    let (P = pts_perfil(),
         // el eje del M5 de punta esta a rail_er_eje del panel, no a rail/2:
         // el riel es hondo y su taladro cae en su centroide
         off = t_panel + rail_er_eje,
         // [origen, fin, los s sobre la cara que llevan riel]
         caras = [[P[1], P[2], [inset_inf_frente,
                                alto_cara_inf - inset_inf_valle]],
                  [P[3], P[4], [inset_sup_valle,
                                alto_cara_sup - inset_sup_remate]]])
    [for (c = caras, s = c[2])
        let (d = (c[1]-c[0])/norm(c[1]-c[0]),      // unitario de la cara
             n = [d.y, -d.x])                       // normal hacia dentro
        c[0] + d*s + n*off];

// Los dos Z-Rails de la fila Intellijel 1U. Cruzan ancho_util exactamente como
// los cuatro 3U y se atornillan por sus puntas a la placa del valle. La
// separacion sale del panel, y el par va ARRIMADO AL FRENTE de la ventana del
// valle (2026-08-29): el primer riel arranca donde acaba la banda, de modo que
// entre la banda y el panel 1U queda el mismo labio de 2 mm que entre dos
// filas cualesquiera, y lo que sobre de ventana queda detras, bajo el vuelo de
// la cara de arriba, donde no se ve. Hasta hoy se centraban en la boca de la
// bahia, y la bahia murio ese dia (nota 1 de Samuel).
function centros_rail_1u() =
    let (P = pts_perfil(),
         xa = ventana_valle()[0] + rail_er_alto/2,
         sep = alto_panel_1u - 2*inset_er,
         y = P[3].y - t_panel - rail_er_eje)
    [[xa, y], [xa + sep, y]];

// El EJE DE LA TAPA no tiene funcion propia porque no es una pieza: es
// centros_rail()[3], o sea el taladro del M5 con el que el riel de arriba se
// fija de punta al costado. Ese tornillo entra a lo largo del ancho, que es la
// direccion de un eje de giro, asi que el riel gira sobre el y arrastra la cara
// entera. Ver la nota de params.scad donde estaba d_visagra.
//
// El radio de giro del riel (hypot(rail_er_fondo, rail_er_alto)/2 = 14.58 mm)
// vivio aqui como funcion mientras el larguero de remate superior tenia que
// librarlo. Ese larguero se retiro el 2026-08-21 y con el la unica llamada; la
// cota sigue viva en _radio_giro_riel() de clearance_budget.py, que es donde de
// verdad se usa: la guarda del barrido de la tapa.

// Tangente de la curva de un vertice: cuanto acrilico se come el redondeo a lo
// largo de cada arista. Es la misma cuenta que _arco hace por dentro, sacada
// aparte porque la tapa del valle necesita saber donde ACABA la curva del pico
// para no asomar por delante de ella.
function tangente(V, a, b, r) = _r_util(V, a, b, r) / tan(_ang(a, b) / 2);

// Extremos de la tapa del valle. DERIVADOS los dos:
//   delante  donde muere el redondeo del pico. Un milimetro mas y la plancha
//            asoma por delante de la curva del costado.
//   detras   holgura_rail por delante del riel del valle de la cara de arriba,
//            contra su ESQUINA girada (he_er_x), no contra su centro.
function x_valle() =
    let (P = pts_perfil(), cr = centros_rail())
    [P[2].x + tangente(P[2], P[1]-P[2], P[3]-P[2], radio_pico),
     cr[2].x - he_er_x(angulo_superior) - holgura_rail];

// largueros del esqueleto (2020) que no son railes de panel:
// base delantera, base trasera, valle, remate trasero.
// Centros [x, y]:
//
// JUNTO AL PLANO TRASERO QUEDAN DOS, no cinco (2026-08-21). Fueron creciendo
// uno por pieza: entrepiso trasero por la bandeja de entrepiso, repisa por la
// piel superior, remate superior por la tira de remate pegada de canto. Las
// tres piezas murieron, y los tres largueros sobrevivieron solo como filas de
// tornillo de la trasera. Con la trasera hecha UNA plancha de 8 esas filas no
// compran rigidez: una plancha continua atornillada arriba y abajo YA es el
// alma de cortante de esa cara, y mejor alma que cinco barras sueltas. Vano
// libre 211.73 mm sobre 8 mm de acrilico y 528 de ancho: 0.15 mm de flecha
// con 50 N en el centro. Quedan el de abajo (base trasera) y el de arriba
// (remate trasero).
//
// Y EL ENTREPISO DELANTERO SE RETIRA (2026-08-25). Era el CUARTO larguero
// -- centro [200.32, 131.58], holgura_rail detras de la esquina girada del
// riel del valle de la cara de arriba -- y el unico del case que no sostenia
// ninguna plancha: las seis filas de M3 van a base delantera, base trasera,
// valle y remate trasero. Su unico trabajo era atar los costados a media
// altura, y a esa MISMA altura (y = 131.58) ya esta el del valle, 75.14 mm
// por delante y encima con su tapa.
//
// Cruzaba el centro del volumen y se veia por el acrilico traslucido desde
// las dos ondas y desde el valle. Es lo mismo que ya tumbo tres largueros el
// 2026-08-21, aplicado al que quedaba: una barra que no es alma de nada.
//
// LO QUE CUESTA, medido sobre el contorno real de costado_2d y no estimado
// (placa circular empotrada de radio a, a = distancia del punto mas
// desasistido a su ancla mas cercana; D = E t^3/12(1-v^2), E = 3 GPa,
// v = 0.37, t = 8):
//
//   vano libre del costado      107.9 -> 119.2 mm  (solo M5; 111.3 contando
//                                                   los 4 M4 de riel)
//   flecha con 200 N             0.31 ->   0.38 mm
//   tension bajo la mano         6.35 ->   6.56 MPa   (fluencia 10, #106)
//   abrir los costados donde
//     estaba, con 200 N                     0.303 mm de separacion total
//
// El punto mas desasistido del costado NO era el suyo ni antes ni despues:
// esta en el canto trasero a media altura, donde ademas apoya la trasera.
// Se llevan 228 g y dos M5. Lo vigila guarda_costado() en clearance_budget.
//
// LO QUE ESTE CALCULO NO CUBRE, y hay que decirlo: el racking del cajon
// entero. La spec §11 ya lista la rigidez del vano de 528 sin bulkhead
// central como HEURISTICA sin cerrar, y esto le quita una barra. Se cierra
// cargando el prototipo, no aqui.
//
// El SEPTIMO larguero, "zocalo superior", se retiro el 2026-08-17: Samuel
// pidio DOS nodos en la esquina de abajo y no tres -- uno para amarrar la
// estructura lateral con la vertical (base delantera) y otro solo para el
// riel del panel. Con el se fue la plancha del zocalo, que se habria quedado
// colgando de una sola fila de tornillos. El larguero habia nacido para dar
// a esa plancha un anclaje a rail DERECHO en vez de al de panel girado; sin
// plancha, el problema que resolvia deja de existir.
// centros_transversal() y sus tres accesores por nombre -- ct_base(),
// ct_valle() y ct_remate() -- MURIERON el 2026-08-28. Eran la lista de los
// TRES CENTROS de los 2020 comprados: un punto por larguero y nada mas. Los
// 2020 se sustituyeron por miembros de chapa el 2026-08-27, y desde ese dia la
// lista no la consumia ni el modelo ni un solo DXF -- solo sobrevivia porque
// bom() contaba sus elementos para decir "x3". Contar los miembros por el largo
// de una lista que ya no los describe es como contar sillas por las facturas
// viejas: el dia que entre o salga un miembro, el eco miente y nadie lo cantaba.
// Ahora los cuenta miembros_lista(), que son ellos mismos.
//
// LO QUE LLEVABA DENTRO Y NO SE PIERDE, porque sigue vivo unas lineas mas
// abajo: los DOS largueros traseros comparten X (miembro_x_trasera(), el plano
// trasero retirado t_piel) para que la trasera atornillada encima apoye en UN
// plano y no en dos parecidos -- si se separan, una de sus dos filas de M3 se
// atornilla al aire, y lo canta apoyo() en clearance_budget. La cadena del
// chasis del PSU (x_tr -> chasis -> lo que venga por delante) vive en
// _x_chasis_frente() del budget, con su propia nota. Y el larguero de `base
// delantera`, que era el cuarto punto de esta lista, se retiro el 2026-08-27.

// --- referencias de los tres miembros de chapa -------------------------
//
// Las cotas de los tres miembros de chapa, gemelas de _cajas_miembro() en
// clearance_budget.py. Sustituyeron a la geometria de los 2020 el 2026-08-27.
//
// Y LA LISTA DE LOS MIEMBROS, que es lo unico que puede contarlos. La consume
// bom() para decir cuantos hay: los nombres son los mismos que usan
// _cajas_miembro() en el budget y miembros() unas lineas mas abajo, o sea que
// anadir un cuarto miembro sin tocar esta lista deja los tres sitios en
// desacuerdo y el eco corto -- que es exactamente lo que pasaba mientras el
// numero salia de centros_transversal().
// DOS desde el 2026-08-29: la bahia -- la bandeja bajo la fila 1U que hacia de
// tercer miembro -- se fue por decision de Samuel ("en el valle solo irian los
// dos Z-rail del 1U"). Lo que ata los anillos a media altura son los seis
// rieles por sus placas, la tabla debajo y la trasera detras; el racking del
// conjunto sigue siendo #203 y se cierra cargando el prototipo.
function miembros_lista() = ["trasero alto", "talon"];
function radio_giro_riel() = norm([rail_er_fondo, rail_er_alto]) / 2;
// LA CARA INTERIOR DE LA TRASERA. La trasera va DENTRO de las dos bandas
// (la del miembro alto arriba, la del talon abajo): su cara trasera contra la
// cara interior de las bandas, rehundida t_costilla del plano trasero -- como
// con el marco de la manana del 29, que es lo que la banda sustituye -- y de
// ahi t_piel hacia dentro. GEMELA de x_tr en clearance_budget.py.
function x_trasera_int() = trasera_x1() - t_piel;
function y_meseta() = pts_perfil()[5].y - marco_sup;

// LA VENTANA DEL VALLE: lo que queda libre entre los dos rieles 3U que miran al
// valle, y es donde vive la fila 1U. Delante la manda el BARRIDO del riel del
// valle de la fila de abajo (que gira sobre su propio M4: radio de giro mas
// holgura), no su esquina quieta; detras, la esquina girada del riel de arriba
// menos holgura_rail, que es donde acaba x_valle(). Era la boca de la bahia
// hasta el 2026-08-29. GEMELA de _ventana_valle() en clearance_budget.py.
function ventana_valle() =
    [centros_rail()[1].x + radio_giro_riel() + holgura_rail, x_valle()[1]];

// EL TALON (2026-08-29, noche): la banda de abajo del plano trasero y su pie
// sobre la tabla. Sustituye al miembro trasero bajo: un angulo de la misma
// chapa, sin bridas ni rosca en el anillo -- se atornilla a la TABLA por el
// pie, como la nariz --, que recibe la trasera en su banda y la asienta en
// su pie. GEMELO de _talon() en clearance_budget.py.
// EL TALON, la nariz de atras (2026-08-29, noche, 2): pie sobre la tabla del
// canto libre al pie del chaflan de P6, chaflan a 45 y labio vertical a ras
// del plano trasero. GEMELAS de _talon() en clearance_budget.py.
function talon_x_band()    = pts_perfil()[6].x - t_costilla;    // cara interior del labio
function talon_x_chaflan() = pts_perfil()[6].x - chaflan_nariz; // pie del chaflan
function talon_x_pie()     = talon_x_chaflan() - talon_pie;     // canto libre del pie
function talon_m4_x()      = talon_x_pie() + 1.5*d_M4_paso;
function centro_talon()    = [talon_x_chaflan() - talon_pie/2, talon_labio/2];
// Las pestanas lanzadas del pie: su cara hacia la trasera, y sus centros en
// z, a (2i+1)/2n del hueco entre anillos (los M4 van a 1/4, 1/2 y 3/4).
function talon_pestana_x() = x_trasera_int() - talon_pestana_aire;
function talon_pestana_z() =
    [for (i = [0 : talon_pestana_n - 1]) t_anillo + ancho_util*(2*i + 1)/(2*talon_pestana_n)];
// Bend deduction del doblez apretado de una pestana, y lo que su ventana
// mide en el desarrollo (alto + t - BD). GEMELAS de _bd_pestana().
function pestana_bd() = 2*(radio_doblez_pestana + t_costilla)
                        - PI/2*(radio_doblez_pestana + k_factor*t_costilla);
function talon_pestana_dev() = talon_pestana_alto + t_costilla - pestana_bd();
// Lo que mide una chapa que va entre las caras interiores de los anillos con
// hol_piel a cada lado: la nariz, el talon, el techo.
function entre_anillos() = ancho_util - 2*hol_piel;

// LA TRASERA CAPTURADA (2026-08-29, noche, 2). Como las mejillas: sus puntas
// dentro de un BOLSILLO fresado en la cara interior de cada anillo a lo largo
// del tramo trasero -- labio derivado de la rendija y bolsillo de 11 --,
// su cara vista rehundida labio + junta, el canto de
// abajo sobre el pie del talon y el de arriba bajo la brida del techo. Sin un
// taladro. GEMELAS de _bolsillo_trasero(), _trasera() y _trasera_campo().
function trasera_x1() = pts_perfil()[6].x - rehundido_trasera() - t_junta_asiento;
function trasera_z0() = t_anillo - rebaje_anillo + hol_piel;
function trasera_au() = ancho_total - 2*trasera_z0();
function trasera_y0() = t_costilla;
// El canto de arriba muere 1.5 bajo la brida del techo: 0.5 de aire al fin
// del bolsillo, y el bolsillo se cierra 1.0 por debajo del canto de la brida
// (dos cosas en la misma cara del anillo no comparten arista).
function trasera_y1() = pts_perfil()[5].y - t_costilla - brida_ancho - 1.5;
function trasera_alto() = trasera_y1() - trasera_y0();
// El canto de abajo del labio (B) o de la banda (A) del techo: la coronacion
// de lo que se ve de la trasera por arriba.
function y_labio_techo() = remate_trasero_chaflan
    ? pts_perfil()[5].y - chaflan_nariz - techo_labio
    : pts_perfil()[5].y - banda_trasera;
// Lo que de la trasera se VE entre los dos labios: a esto se anclan la
// rejilla, las ondas, el IEC y KONDOR desde que no hay filas de M3.
function trasera_campo() = [chaflan_nariz + talon_labio, y_labio_techo()];
// El bolsillo, en x del mundo: [pared del fondo, cara interior del labio].
function bolsillo_trasero_x() =
    [pts_perfil()[6].x - pared_trasera_u(),
     pts_perfil()[6].x - rehundido_trasera()];
// Donde retrocede el rebaje del costado en el tramo trasero: la pared entre
// los dos bolsillos.
function rebaje_costado_trasero() = pared_trasera_u() + pared_rebaje_trasera;

// --- redondeo del contorno, radio POR VERTICE --------------------------
//
// Aqui estuvo un cierre morfologico global (`offset(-r) offset(2r) offset(-r)`)
// y no da la talla: un radio unico no puede a la vez COMERSE los 45 mm de
// cara frontal -- que Samuel quiere que se lean como punta redondeada -- y
// RESPETAR los 80 mm planos del valle. Con radio 14 el frente sigue siendo
// una cara recta; con el radio 31 que hace falta para borrarla, el valle se
// redondea entero y desaparece. Son requisitos opuestos sobre el mismo
// numero, asi que el numero tiene que dejar de ser uno.
//
// Esto emite el arco de cada esquina explicitamente. El radio pedido se
// RECORTA a lo que da de si la arista mas corta que llega al vertice, de
// modo que pedir un radio enorme no rompe nada: da el maximo redondeo
// posible, que es exactamente "punta redondeada".

// Angulo interior en V entre las aristas que van a los vecinos a y b.
function _ang(a, b) = let (u = a/norm(a), v = b/norm(b))
    acos(max(-1, min(1, u*v)));

// Radio efectivo: el pedido, o el que cabe si las dos tangentes no llegan a
// la mitad de su arista (si no, el arco de un vertice se comeria al vecino).
function _r_util(V, a, b, r) =
    let (g = _ang(a, b) / 2, lim = min(norm(a), norm(b)) / 2 * tan(g))
    min(r, lim * 0.999);

function _arco(V, a, b, r, n = 16) =
    let (u = a/norm(a), v = b/norm(b),
         g  = _ang(a, b) / 2,
         re = _r_util(V, a, b, r),
         t  = re / tan(g),                       // distancia tangente
         w  = (u + v) / norm(u + v),              // bisectriz interior
         C  = V + w * (re / sin(g)),              // centro del arco
         PA = V + u * t,
         aA = atan2(PA.y - C.y, PA.x - C.x),
         PB = V + v * t,
         aB = atan2(PB.y - C.y, PB.x - C.x),
         d  = ((aB - aA) + 540) % 360 - 180)      // giro corto, sirve para
    [for (i = [0:n]) C + re * [cos(aA + d*i/n),   // convexos y concavos
                               sin(aA + d*i/n)]];

// --- bombeo de las rectas (entasis) ------------------------------------
//
// "Las rectas no son completamente rectas, por poquito." Cada tramo recto
// entre dos arcos se cambia por una parabola muy plana que se abomba HACIA
// FUERA. La flecha es proporcional al largo del tramo (bombeo mm por cada
// 100 mm), no absoluta: una flecha fija se ve exagerada en un tramo corto y
// no se ve en uno largo.
//
// El "hacia fuera" se decide contra el CENTROIDE y no por el sentido de giro
// del poligono, que es una fuente de errores de signo silenciosos -- ya
// pasamos por uno con la rotacion de los railes.
function _suma(v, i = 0) = i >= len(v) ? [0, 0] : v[i] + _suma(v, i + 1);
function _centro(P) = _suma(P) / len(P);

function _bombear(A, B, C, n = 10) =
    let (d = B - A, L = norm(d))
    (bombeo <= 0 || L < 1) ? []
    : let (u = d / L,
           nl = [-u.y, u.x],
           M = (A + B) / 2,
           fuera = (nl * (M - C)) >= 0 ? nl : -nl,
           s = L / 100 * bombeo)                       // flecha en el centro
      [for (i = [1 : n-1])
          let (t = i / n)
          A + d*t + fuera * (s * 4*t*(1-t))];          // pico en t=0.5

// sin_bombeo = indices de vertice cuyo tramo SALIENTE se deja recto de
// verdad. El canto de abajo va aqui: es la cara de apoyo, y abombarla
// significa que el case descansa sobre el centro de cada costado en vez de
// sobre sus extremos.
function redondear(P, R, sin_bombeo = []) =
    let (n = len(P), C = _centro(P),
         arcos = [for (i = [0:n-1])
             R[i] <= 0 ? [P[i]]
                       : _arco(P[i], P[(i-1+n)%n] - P[i], P[(i+1)%n] - P[i],
                               R[i])])
    [for (i = [0:n-1]) each concat(
        arcos[i],
        search(i, sin_bombeo) != []
            ? []
            : _bombear(arcos[i][len(arcos[i]) - 1], arcos[(i+1)%n][0], C))];

// Radio por vertice del perfil, en el orden de pts_perfil(). Las dos esquinas
// del valle llevan radios DISTINTOS y opuestos a proposito (2026-08-17):
//
//   0 frente-abajo  PUNTA    1 arranque cara  PUNTA
//   2 valle-delante PICO     3 valle-detras   SUAVE
//   4 apex          REMATE   5 fondo-arriba   REMATE
//   6 fondo-abajo   normal
//
// El 2 es el vertice CONVEXO donde el tope del panel de abajo se encuentra
// con el valle: radio corto, para que se lea como pico. El 3 es el CONCAVO
// donde el valle arranca hacia la cara de arriba: radio largo, para que ese
// angulo entre blando. Son los dos extremos de la misma pieza y por eso no
// pueden compartir numero.
//
// radio_punta va deliberadamente sobredimensionado: _r_util lo recorta al
// maximo que permite la arista, y ese maximo ES la punta.
// Los vertices 4 y 5 compartieron radio_punta hasta el 2026-08-21. Ahi el radio
// efectivo no era el pedido sino el que cabia en la meseta (marco_remate/2), asi
// que ensanchar el techo lo volvia MAS redondo. Con radio_remate se pide un
// radio y sale ese: la punta de arriba se lee cuadrada a cualquier marco.
// Los vertices 5 y 6 -- los DOS del plano trasero -- pasan a radio_trasero = 0
// el 2026-08-24: esquina viva, para que la trasera y el remate del techo
// empotren a ras. OJO CON EL NOMBRE: desde el 2026-08-27 no hay tapa de remate
// -- esa plancha se integro como MESETA del miembro trasero alto --, asi que lo
// que empotra a ras contra esta esquina es esa meseta de chapa.
// Antes eran radio_remate (2) y radio_perfil (14), y ese 14 le
// dejaba a la trasera 14 mm de esquina colgando fuera de la silueta del
// costado. radio_perfil se quedo sin clientes y se borro. El porque completo,
// y que parte de la regla anti-fisura se sostiene y cual no, en params.scad.
//
// redondear() ya sabe tratar el 0: R[i] <= 0 devuelve el vertice pelado, sin
// arco. No hace falta tocarla.
// DESDE EL 2026-08-29 (nota 2 de Samuel: "en vez de una nariz curva, una nariz
// recta"): el vertice 0 no lleva radio sino CHAFLAN -- ver pts_contorno() --, y
// los vertices que llevan chapa empotrada usan radio_borde, concentrico con
// radio_chapa. Las salidas de los pies conservan radio_chapa. radio_punta
// y radio_remate murieron con esto; radio_trasero (0) murio la noche del 29,
// cuando el talon paso a doblar en P6 sobre la tabla.
function radios_perfil() = [0,            radio_borde(),
                            radio_pico,   radio_valle,
                            radio_borde(),
                            remate_trasero_chaflan ? 0 : radio_borde(),
                            0];

// EL CONTORNO DEL ANILLO NO ES pts_perfil(): el vertice 0 (frente-abajo) va
// CHAFLANADO a 45 -- chaflan_nariz sobre cada arista -- y un chaflan son dos
// vertices, cada uno con el radio de la chapa que dobla ahi. Se insertan AQUI
// y no en pts_perfil() porque medio fichero indexa P[1]..P[6] y correrlos uno
// es el mismo bug que costo el P[8] -> P[6]. Solo perfil_lateral() lo consume.
// GEMELO del chaflan que anillo_tiene_chaflan() relee del DXF en check_dxf.
// Y DESDE LA TRASERA CAPTURADA (2026-08-29, noche, 2) el vertice 6 (abajo-
// atras) va tambien a chaflan -- el talon es la nariz de atras -- y el 5
// (arriba-atras) con remate_trasero_chaflan. Cada chaflan son dos vertices
// con radio_chapa.
function pts_contorno() =
    let (P = pts_perfil(), c = chaflan_nariz, pf = P[6].x, yt = P[5].y)
    concat([[c, 0], [0, c]], [for (i = [1 : 4]) P[i]],
           remate_trasero_chaflan ? [[pf - c, yt], [pf, yt - c]] : [P[5]],
           [[pf, c], [pf - c, 0]]);
function radios_contorno() =
    concat([radio_chapa, radio_borde()],
           [for (i = [1 : 4]) radios_perfil()[i]],
           remate_trasero_chaflan ? [radio_borde(), radio_borde()] : [radios_perfil()[5]],
           [radio_borde(), radio_chapa]);
// Los tramos del contorno que van RECTOS: todos menos las tres caras de las
// filas ([2], [3], [4]), que conservan la entasis.
function tramos_rectos() = [for (i = [0 : len(pts_contorno()) - 1]) if (i < 2 || i > 4) i];

// Va DENTRO de perfil_lateral y no en costado_2d a proposito: costado_2d
// resta los agujeros DESPUES, de modo que el redondeo no toca los taladros.
// Si se aplicara al resultado de la resta, los M4 saldrian fuera de
// diametro -- el mismo tipo de fallo que el cupon pentagonal.
//
// Ningun otro modulo consume este contorno (las demas piezas usan
// pts_perfil() para coordenadas, no la silueta), asi que el radio no se
// propaga a bandejas ni pieles.
module perfil_lateral() {
    // TRES tramos van rectos de verdad, y la regla es una sola: EL CANTO QUE
    // APOYA CONTRA ALGO PLANO NO SE ABOMBA. Los que solo dibujan silueta
    // conservan la entasis, que es para lo que existe.
    //
    //   [6] canto de abajo   (P[6] -> P[0], 308.94 mm)  la cara de apoyo.
    //       Abombada, el aparato descansaria sobre el centro de cada costado
    //       en vez de sobre sus extremos, y con paticas en las esquinas eso
    //       es un balancin. Exento desde el principio.
    //   [5] canto trasero    (P[5] -> P[6], 256.18 mm)  contra la TRASERA.
    //   [4] meseta del techo (P[4] -> P[5],  50.00 mm)  contra la TAPA DE
    //       REMATE.
    //
    // Los dos ultimos entran el 2026-08-24, a peticion de Samuel: "siento que
    // no esta recta la linea de ese corte y preferiria que fuera recta para
    // que encaje a la perfeccion con la pieza trasera". Y no era percepcion.
    // Medido sobre el DXF que va al taller, el canto trasero SOBRESALIA
    // 1.1970 mm del plano trasero a media altura y enrasaba en las puntas
    // -- contra hol_piel = 0.15 mm de holgura de montaje de la trasera, o sea
    // OCHO VECES la junta. La meseta hacia lo mismo con 0.250 mm bajo la tapa
    // de remate.
    //
    // El canto trasero era ademas EL TRAMO MAS LARGO QUE TODAVIA SE ABOMBABA
    // (256.18 mm; el de abajo es mayor pero ya estaba exento), asi que se
    // llevaba la flecha mas grande del perfil. Lo que queda de entasis tras
    // esto es 0.779 mm en la cara del panel de abajo, que no apoya contra
    // nada.
    //
    // INDICES DEL CONTORNO, no del perfil (2026-08-29): el chaflan mete un
    // vertice antes, asi que los tres de arriba son [5], [6] y [7]. Y entran
    // dos mas: [0] el chaflan y [1] el frente vertical, que llevan encima la
    // NARIZ -- chapa plana, o sea "algo plano".
    polygon(redondear(pts_contorno(), radios_contorno(), tramos_rectos()));
}

// EL COSTADO YA NO LLEVA UN SOLO TORNILLO. Es piel: un contorno de acrilico y
// nada mas. Los cuatro M4 de riel y los M5 de transversal se fueron a la
// costilla el 2026-08-27, y con ellos se fue lo ultimo que hacia de esta pieza
// una pieza portante.
//
// UN AGUJERO QUE NO RECIBE TORNILLO NO ES NEUTRO EN ACRILICO: quita material
// justo donde el radio de la esquina en punta ya andaba corto, y cada uno es un
// concentrador de tension en una plancha que rompe por el canto.
//
// Como se sujeta entonces: estuvo capturada entre las dos alas de la costilla
// de chapa (spec 2) y desde el 2026-08-28 ASIENTA EN EL REBAJE DEL ANILLO --
// el labio la sostiene hacia fuera por todo el perimetro y los clips la
// retienen hacia dentro. Sin tornillo, y por eso guarda_costado() dejo de
// medir vanos entre anclas y pasa a medir contra el canto de la ventana, que
// es apoyo CONTINUO.
//
// LE VOLVIERON CUATRO AGUJEROS EL 2026-08-27 Y SE VAN EL 28. Eran los pasos
// de casquillo: con el marco POR FUERA y el acrilico APILADO detras, el M4 del
// riel tenia que cruzar el PMMA antes de morder, y el casquillo de aluminio se
// comia el apriete para que no lo pinzara. Ese apilado murio con el anillo --
// el acrilico va DENTRO de la ventana, coplanar, y el tornillo del riel ni lo
// roza: entra en una placa de anclaje por la cara interior. Vuelve a cero.
//
// EL 2026-08-28 EL CONTORNO SE RETRANQUEA. Ya no es la silueta del case: es la
// silueta menos retiro_rebaje() (lo que el anillo tapa por delante) menos la
// holgura de montaje, porque la pieza entra POR DETRAS y asienta en el rebaje.
// Los rebaje_anillo - hol_costado que sobresalen bajo el labio son justo lo que
// lo retiene, y lo mide guarda_costado() en check_dxf como vano libre.
module costado_2d() {
    // EL CANTO TRASERO ENTRA 3, NO 6 (2026-08-29, noche, 2): en el tramo
    // trasero el rebaje retrocede a la pared entre su bolsillo y el de la
    // trasera (rebaje_costado_trasero). Nadie lo ve: ese canto vive detras
    // del labio y el marco lo sigue pisando.
    difference() {
        offset(delta = -(retiro_rebaje() + hol_costado)) perfil_lateral();
        translate([pts_perfil()[6].x - rebaje_costado_trasero() - hol_costado, -1])
            square([100, 400]);
    }
}

module costado() { linear_extrude(t_cheek) costado_2d(); }

// --- EL ANILLO DE PLETINA -------------------------------------------------
// La costilla es un anillo FRESADO desde el 2026-08-28: silueta por fuera,
// ventana por dentro, y por detras el rebaje donde asienta el acrilico. No
// tiene desarrollo, no tiene alivios, no tiene P3 que soldar: es una pieza.
//
// LO QUE SE FUE CON LA CHAPA, y conviene que quede escrito porque fueron dos
// dias de trabajo: la banda de ala_costilla (27) con su ventana, el ala de
// ala_doblez (16) doblada a 90 en los siete tramos, los seis alivios en V de
// los vertices convexos, el rip bisector de P3 y su soldadura, y el
// desarrollo plano que el DXF tenia que llevar porque un corte no dice de
// donde doblar. Nada de eso sobrevive a una pieza maciza: la cara vista sale
// del propio espesor y la esquina concava es un radio de fresa.
function retiro_rebaje() = cara_anillo - rebaje_anillo;

// La ventana se estrecha solo atras; la interseccion deja transiciones minimas.
// VISTA PREVIA: la spec no fija los puntos de enlace entre las caras de 20 y 22.
module ventana_anillo_2d(f = 0) {
    P = pts_perfil();
    intersection() {
        offset(delta = -cara_anillo + f) perfil_lateral();
        translate([-cara_anillo, -cara_anillo])
            square([P[6].x - cara_anillo_trasera() + f + cara_anillo,
                    P[5].y + 2*cara_anillo]);
    }
}

// Banda holgada alrededor de un tramo; el anillo redondeado recorta el resultado.
module mascara_tramo_rebaje(A, B, extra_a = -1, extra_b = -1) {
    d = (B - A)/norm(B - A);
    n = [d.y, -d.x];
    e = radio_borde() + rehundido_trasera();
    ea = extra_a < 0 ? e : extra_a;
    eb = extra_b < 0 ? e : extra_b;
    polygon([A - d*ea - n, B + d*eb - n,
             B + d*eb + n*(rehundido_trasera() + 1),
             A - d*ea + n*(rehundido_trasera() + 1)]);
}

// Solo se fresa donde una chapa queda a la vista.
module rebaje_chapa_2d() {
    P = pts_perfil();
    C = pts_contorno();
    d_sup = [sin(angulo_superior), cos(angulo_superior)];
    pf = P[6].x;
    yt = P[5].y;
    c = chaflan_nariz;
    intersection() {
        difference() {
            offset(delta = -rehundido_chapa) perfil_lateral();
            offset(delta = -rehundido_trasera()) perfil_lateral();
        }
        union() {
            mascara_tramo_rebaje(C[0], C[1], 0);                 // nariz, chaflan
            mascara_tramo_rebaje(C[1], P[1], -1, 0);             // nariz, frente
            mascara_tramo_rebaje(P[4] - d_sup*retorno_meseta, P[4], 0);
            mascara_tramo_rebaje(P[4], [pf - c, yt]);            // meseta
            mascara_tramo_rebaje([pf - c, yt], [pf, yt - c]);    // P5
            mascara_tramo_rebaje([pf, yt - c], [pf, y_labio_techo()], -1, 0);
            mascara_tramo_rebaje([pf, c + talon_labio], [pf, c], 0);
            mascara_tramo_rebaje([pf, c], [pf - c, 0], -1, 0);   // talon
        }
    }
}

module rect_redondeado_2d(w, h, r) {
    hull()
        for (x = [r, w - r], y = [r, h - r])
            translate([x, y]) circle(r = r);
}

// El cajeado da hol_chapa alrededor de la brida y usa el radio de la fresa.
module cajeado_brida_2d() {
    // hol_chapa alrededor de la huella: el canto de arriba del cajeado cae
    // en u = rehundido_chapa, justo donde muere el reborde, y el de abajo
    // 0.5 por encima del cierre del bolsillo (bolsillo_y_fin).
    translate([brida_x_dob() - brida_largo - hol_chapa,
               y_meseta() - brida_ancho - hol_chapa])
        rect_redondeado_2d(cajeado_brida_largo(), cajeado_brida_ancho(),
                           radio_cajeado_brida());
}

// EL REBAJE DEL COSTADO, en planta: la silueta retirada cara - rebaje por
// los cuatro lados, salvo en el tramo trasero, donde retrocede a
// rebaje_costado_trasero (la pared con el bolsillo de la trasera). GEMELO de
// anillo_tiene_rebaje() en check_dxf.
module rebaje_2d() {
    P = pts_perfil();
    union() {
        difference() {
            offset(delta = -retiro_rebaje()) perfil_lateral();
            translate([P[6].x - rebaje_costado_trasero(), -1]) square([100, 400]);
        }
        // El offset redondea P5/P6; la entrada del costado debe cubrir toda la banda.
        translate([P[6].x - cara_anillo_trasera(), chaflan_nariz])
            square([entrada_costado_trasero, P[5].y - 2*chaflan_nariz]);
    }
}

// EL BOLSILLO DE LA TRASERA, en planta: CERRADO POR LOS DOS EXTREMOS. Abajo
// se cierra medio milimetro bajo el canto de la trasera (que apoya en el pie)
// y arriba medio milimetro sobre el otro canto, 1.0 por debajo de la brida
// del techo. La trasera entra al montar el segundo anillo, como los costados
// -- son las tres planchas que se montan una vez, con el case --: salir por
// el canto de arriba dejaba un agujero de 11 x 6 a la vista junto al techo, y
// salir por abajo obligaba a que toda la plancha pasara por la boca estrecha
// que deja el chaflan de P6 (el revisor del PR lo cazo con un booleano).
// Bajo bolsillo_y_paso (la coronacion de la pared de u = rehundido sobre el
// chaflan, mas 0.5) el bolsillo arranca en bolsillo_u_paso para no morder la
// cara del chaflan; la esquina de abajo-fuera de la plancha va a chaflan
// (chaflan_trasera_bajo) y libra ese escalon. Se fresa rebaje_anillo hondo
// desde la cara interior (profundidad en el pliego: la mitad de la del
// rebaje). GEMELO de _bolsillo_trasero() y de anillo_tiene_bolsillo_trasero().
function bolsillo_y_bot()  = trasera_y0() - 0.5;
function bolsillo_y_fin()  = trasera_y1() + 0.5;
function bolsillo_y_paso() = chaflan_nariz - rehundido_trasera() + 0.5;
function bolsillo_u_paso() = chaflan_nariz - bolsillo_y_bot() + 0.5;
module bolsillo_trasero_2d() {
    b = bolsillo_trasero_x();
    pf = pts_perfil()[6].x;
    polygon([[b[0], bolsillo_y_bot()], [pf - bolsillo_u_paso(), bolsillo_y_bot()],
             [pf - bolsillo_u_paso(), bolsillo_y_paso()], [b[1], bolsillo_y_paso()],
             [b[1], bolsillo_y_fin()], [b[0], bolsillo_y_fin()]]);
}

// EL CHAFLAN DE LA ARISTA DE ABAJO-FUERA DE LA TRASERA, a 45, por todo su
// largo: lo que hace falta para que su esquina libre el escalon del bolsillo
// con 0.5 (la pared de u = rehundido..bolsillo_u_paso bajo bolsillo_y_paso)
// EN EL PEOR SITIO DONDE LA PLANCHA PUEDE ESTAR: en el fondo del bolsillo
// (bolsillo_y_bot, donde descansa hasta que llega la tabla) y pegada al labio
// (u = rehundido, con la junta aplastada). El revisor del PR #244 cazo que la
// primera cuenta la media en su sitio nominal, donde no esta al montarla.
// No sale en el DXF (es una arista, no un contorno): va en el pliego. Escondido
// detras del labio del talon. GEMELO de la clave "chaflan_bajo" de _trasera().
function chaflan_trasera_bajo() =
    (bolsillo_u_paso() + 0.5 - rehundido_trasera())
    + (bolsillo_y_paso() - bolsillo_y_bot());

module anillo_2d() {
    difference() {
        perfil_lateral();
        ventana_anillo_2d();
    }
}

// El DXF de la CARA: contorno de la pieza y ventana. Va al corte del blank.
module costilla_2d() { anillo_2d(); }

// El DXF del DORSO: lo que se fresa por detras. El contorno del rebaje
// (profundidad t_anillo - rehundido, en el pliego) y los centros de las
// roscas ciegas a diametro de broca (profundidad en el pliego). Otro fichero
// porque un DXF 2D no sabe decir "a 11 mm" -- mismo caso que el cajeado
// KONDOR de la trasera.
module costilla_dorso_2d() {
    rebaje_2d();
    bolsillo_trasero_2d();
    rebaje_chapa_2d();
    cajeado_brida_2d();
    for (c = centros_rosca_ciega())
        translate(c[0]) circle(d = c[1]);
}

// --- EL MARCO DE LA VENTANA Y LAS ROSCAS CIEGAS (2026-08-29, noche) -------
//
// El eje del M4 de cada riel cae a 15.90 de la silueta, o sea DENTRO del
// rebaje, donde el anillo solo tiene 3 mm de labio: por ahi el tornillo sale
// por la cara vista. Asi que el riel muere contra una pletina apoyada en la
// franja interior y es la pletina la que va al anillo, con dos M4 a rosca
// ciega por riel. Fueron TRES PLACAS por costado, una por fila -- "la placa
// es el marco de la fila" (Samuel, 28-08) -- mas dos clips en el suelo y una
// escuadra en la trasera para retener el acrilico hacia dentro donde no
// habia placa. Desde esta noche son UNA pieza: el MARCO DE LA VENTANA, la
// misma pletina de t_placa corrida por los siete tramos del anillo, con el
// contorno de la ventana por dentro (marco_fondo desde la silueta) y el
// canto exterior donde toca en cada tramo:
//
//   las tres filas          a la silueta: el canto visto de 6 que se lee
//                           como el borde de aluminio de la fila
//   frente, meseta y cola   retirados bajo la chapa empotrada
//   suelo                   retirado solo bajo los pies, que siguen a ras
//   trasera                 retirado t_anillo + 0.5: por debajo corre el
//                           bolsillo de la trasera (2026-08-29, noche, 2) y
//                           la pata apoya en la pared entre bolsillos; entra
//                           marco_fondo_trasera, no marco_fondo
//                           (guarda_trasera_capturada, guarda_marco_ventana)
//
// Y UNA MUESCA sobre la brida del miembro alto, en la esquina trasera-alta:
// la brida apoya en la cara del anillo -- fuera del barrido del panel, que
// es lo que decide -- y el marco vive en esa misma franja, asi que se aparta.
//
// TODO ESTO ES GEMELO de _marco_ventana(), _roscas_marco(), _bridas() y
// _centros_rosca_ciega() en clearance_budget.py, y quien las cruza es
// taladros_anillo() y taladros_marco_ventana() en check_dxf releyendo los DXF.

// Tolerancia de espesor del PMMA: +-(0.4 + 0.1 x t), Schaeffer AG (2026-08-18).
function tol_pmma() = 0.4 + 0.1*t_cheek;
function retiro_marco_pie() = t_costilla + hol_piel;
function retiro_marco_chapa() = rehundido_chapa + t_costilla + hol_piel;
function retiro_marco() = retiro_marco_chapa();
// La pata trasera arranca sobre la pared entre bolsillos: t_anillo + 0.5
// (2026-08-29, noche, 2). Fue t_piel + t_costilla + tol + 0.5 con la trasera
// atornillada a la banda.
function retiro_marco_trasera() = pared_trasera_u() + hol_costado;

// Cuanto se retira una pata del vertice i: la TANGENTE de su redondeo si el
// vertice es convexo -- ahi el contorno se mete hacia dentro y una esquina
// apoyada en la recta se saldria de la silueta -- y CERO si es concavo. El
// perfil se recorre en sentido HORARIO: convexo es producto vectorial < 0.
function retiro_vertice(i) =
    let (P = pts_perfil(), m = len(P),
         A = P[(i + m - 1) % m], V = P[i], B = P[(i + 1) % m],
         cruz = (V.x - A.x)*(B.y - V.y) - (V.y - A.y)*(B.x - V.x))
    cruz < 0 ? tangente(V, A - V, B - V, radios_perfil()[i]) : 0;

// LAS TRES PATAS DE LAS FILAS, que son las que recogen rieles: [nombre, A, u,
// n, s0, s1, ejes]. A es el vertice de arranque del tramo; un punto de la
// pata es A + u*s + n*b. `ejes` lleva, por cada riel, [s del eje, punto, si
// lleva sus dos roscas ciegas]. La cara de abajo cede retiro_placa_inf en P1
// (ahi el canto exterior va retirado bajo la nariz y la pata sigue) y el
// valle se alarga hasta cubrir el cajeado de su segundo riel, pasado P3.
function patas_filas() =
    let (P = pts_perfil(), cr = centros_rail(), c1u = centros_rail_1u())
    [for (t = [["cara_inf", 1, 2, [0, 1], retiro_placa_inf],
               ["valle",    2, 3, [],     0],
               ["cara_sup", 3, 4, [2, 3], retiro_placa_sup]])
        let (A = P[t[1]], B = P[t[2]], L = norm(B - A),
             u = (B - A)/L, n = [u.y, -u.x],
             tres = len(t[3]) > 0,
             centros = tres ? [for (i = t[3]) cr[i]] : c1u,
             // LA SEGUNDA 1U NO LLEVA ROSCAS y no es un olvido: radio_valle
             // vale 54 y curva la franja del valle, y una broca puesta ahi
             // sale por la pared del rebaje.
             ejes = [for (k = [0 : len(centros) - 1])
                        [(centros[k] - A)*u, centros[k], tres || k == 0]],
             s0 = retiro_vertice(t[1]) + t[4],
             s1v = L - retiro_vertice(t[2]),
             s1 = tres ? s1v
                       : max(s1v, max([for (e = ejes) e[0]]) + 2*d_M4_paso))
        [t[0], A, u, n, s0, s1, ejes]];
function pata(nombre) = [for (q = patas_filas()) if (q[0] == nombre) q][0];

// La pata del suelo del marco, de P6 al chaflan: [A, u, n, s0, s1]. Arranca
// donde manda la pata trasera (retiro_marco_trasera tras P6) y acaba en el
// retiro del chaflan. Lleva DOS roscas ciegas, a rosca_suelo_retiro de cada
// extremo: el trabajo que hacian las de los clips. GEMELA de la pata "suelo"
// de _marco_ventana() y de las "marco suelo" de _roscas_marco().
function pata_suelo() =
    let (P = pts_perfil(), A = P[6], B = [chaflan_nariz, 0], L = norm(B - A),
         u = (B - A)/L, n = [u.y, -u.x])
    [A, u, n, max(retiro_vertice(6), retiro_marco_trasera()),
     L - retiro_marco_pie()];
function roscas_suelo() =
    let (q = pata_suelo())
    [for (s = [q[3] + rosca_suelo_retiro, q[4] - rosca_suelo_retiro])
        q[0] + q[1]*s + q[2]*dist_rosca_ciega];

// Las dos roscas ciegas de cada riel: eje +- sep_rosca_riel a lo largo del
// tramo, a dist_rosca_ciega de la silueta. Doce por anillo: diez de las filas
// y dos en la pata del suelo (roscas_suelo). EL PAR SE ARRIMA
// AL RIEL PERO NO SE SALE DE SU PATA: se corre lo justo para que las dos
// queden a 1.6 D de los extremos de la pata -- el de la cara de arriba en P3
// esta a retiro_placa_sup del vertice porque ahi el redondeo concavo
// estrecha la franja y la rosca sale por el rebaje. GEMELA de _roscas_marco().
function centro_par_rosca(q, e) =
    let (canto = 1.6*d_M4_paso)
    min(max(e[0], q[4] + canto + sep_rosca_riel),
        q[5] - canto - sep_rosca_riel);
function roscas_marco() =
    concat([for (q = patas_filas(), e = q[6], s = [-sep_rosca_riel, sep_rosca_riel])
                if (e[2]) q[1] + q[2]*(centro_par_rosca(q, e) + s) + q[3]*dist_rosca_ciega],
           roscas_suelo());
// Los seis pasos M4 de riel (con cajeado por el lado del anillo).
function ejes_marco() = [for (q = patas_filas(), e = q[6]) e[1]];

// La brida de extremo del miembro alto: sus dos M4 en el cajeado de la meseta.
// Regla de chapa: el agujero no entra en la zona del doblez (setback + 2t +
// radio). Dobla del EXTREMO DE LA BANDA, en el plano trasero, y apoya en la
// suelo del cajeado: fuera del barrido del panel, con el marco muescado encima.
function brida_raiz() = radio_doblez_costilla + 3*t_costilla + d_M4_paso/2;
// EL M4 DE DENTRO NO CAE SOBRE EL BOLSILLO DE LA TRASERA (2026-08-29, noche,
// 2): el bolsillo corre por la cara interior hasta u = t_anillo y la rosca
// quiere 1.6 D de broca de su pared (1.6 y no 1.5 para no vivir del
// redondeo). Manda la mayor de las dos reglas. GEMELA de _bridas().
// (Se probo max(raiz, t_anillo + 1.6 D - t) cuando el bolsillo pasaba por
// debajo de la brida; con el bolsillo cerrado arriba vuelve a ser la raiz.)
function brida_s_in() = brida_raiz();
function brida_x_dob() = pts_perfil()[6].x - rehundido_chapa - t_costilla;
function brida_xs() = [brida_x_dob() - brida_s_in(),
                       brida_x_dob() - brida_largo + 1.5*d_M4_paso];
function bridas_anillo() =
    let (P = pts_perfil()) [for (x = brida_xs()) [x, P[5].y - dist_rosca_ciega]];

// [centro, diametro de broca] de cada rosca ciega de la cara interior: CATORCE
// por anillo, doce del marco y dos de la brida. Las de la TABLA no estan: van
// en el CANTO inferior del anillo y un DXF de la cara no sabe dibujar un
// taladro que entra por el canto (pliego). La de la pestana del valle
// tampoco: se rosca en los 6 mm del marco (ruling R3).
function centros_rosca_ciega() =
    concat([for (c = roscas_marco()) [c, d_M4_rosca]],
           [for (c = bridas_anillo()) [c, d_M4_rosca]]);

// El M3 con el que la pestana de la banda del valle se atornilla al marco, a
// diametro de broca y de lado a lado -- 6 mm de pletina dan rosca de sobra.
function m3_pestana() = [pv_x(), pts_perfil()[3].y - pv_a()];
function roscas_marco_m3() = [[m3_pestana(), d_M3_rosca]];

// LA MUESCA DE LA BRIDA: [x_min, y_min]; todo lo que quede a x >= x_min e
// y >= y_min se corta del marco. GEMELA de _muesca_brida().
function muesca_brida() =
    [brida_x_dob() - brida_largo - hol_chapa,
     y_meseta() - brida_ancho - hol_chapa];

// Las bandas que retiran el canto exterior del marco de la silueta, una por
// tramo bajo chapa: [A, B, s0, s1, retiro], con s en mm desde A. Pasarse de
// largo por las puntas es a proposito: en una esquina entre dos tramos
// retirados manda el retiro mayor, y la banda que se pasa se lo come.
function bandas_marco() =
    let (P = pts_perfil(), C = pts_contorno(), r = retiro_marco_chapa(),
         rp = retiro_marco_pie(),
         s0_inf = retiro_vertice(1) + retiro_placa_inf,
         L_sup = norm(P[4] - P[3]))
    [[C[0], C[1], -5, norm(C[1] - C[0]) + 5, r],                 // chaflan
     [C[1], P[1], -5, norm(P[1] - C[1]), r],                      // frente
     [P[1], P[2], -5, s0_inf, r],                                 // cara de abajo, bajo la nariz
     [P[3], P[4], L_sup - (retorno_meseta + 1), L_sup + 5, r],    // cola, bajo el retorno
     [P[4], P[5], -5, norm(P[5] - P[4]) + 5, r],                  // meseta
     [P[5], P[6], -5, norm(P[6] - P[5]) + 5, retiro_marco_trasera()],  // trasera
     [P[6], C[0], -5, norm(C[0] - P[6]) + 5, rp]];                // suelo
module banda_marco_2d(b) {
    A = b[0]; B = b[1]; u = (B - A)/norm(B - A); n = [u.y, -u.x];
    polygon([A + u*b[2] - n*5, A + u*b[3] - n*5,
             A + u*b[3] + n*b[4], A + u*b[2] + n*b[4]]);
}

// La pletina sin taladros: la silueta menos las bandas de retiro, menos la
// ventana a marco_fondo, menos la muesca de la brida.
//
// EL CANTO INTERIOR ES RECTO: marco_fondo desde las ARISTAS del perfil
// (pts_perfil, sin redondear), no desde la silueta redondeada. Da lo mismo
// en las esquinas convexas -- el offset hacia dentro de un redondeo convexo
// es una esquina viva igual --, pero en P3, el rincon concavo de radio 54,
// el offset de la silueta sube en arco y dejaba el paso del segundo riel 1U
// a 6.26 del canto (check_dxf lo cazo). Con las aristas rectas el marco es
// mas hondo en ese rincon -- pisa 9 de acrilico en vez de 6, sin
// consecuencia -- y el paso se queda a 10.
module marco_contorno_2d() {
    difference() {
        perfil_lateral();
        for (b = bandas_marco()) banda_marco_2d(b);
        // la ventana del marco: marco_fondo por dentro, salvo la pata trasera,
        // que entra marco_fondo_trasera (sin tornillo y mas estrecha desde el
        // bolsillo, necesita el ancho)
        difference() {
            offset(delta = -marco_fondo) polygon(pts_perfil());
            translate([pts_perfil()[6].x - marco_fondo_trasera, -1]) square([100, 400]);
        }
        translate(muesca_brida()) square([100, 100]);
    }
}

// EL DXF DEL MARCO: contorno y taladros de PASO. Diez M4 al anillo, seis M4
// de riel y la rosca M3 de la pestana. La brida del miembro alto NO lo
// atraviesa: ahi el marco lleva la muesca y la brida va directa al anillo.
// EL CAJEADO NO SE
// DIBUJA: un DXF 2D no sabe decir "a 2.5 mm de profundidad" -- va como NOTA
// DE MECANIZADO en el pliego (Ø8 x prof_cajeado_riel en cada paso M4 de
// riel, por la cara que mira al anillo: el lado espejado comparte contorno y
// se cajea por la otra cara). Lo relee taladros_marco_ventana() en check_dxf.
module marco_ventana_2d() {
    difference() {
        marco_contorno_2d();
        for (c = roscas_marco())  translate(c) circle(d = d_M4_paso + kerf);
        for (c = ejes_marco())    translate(c) circle(d = d_M4_paso + kerf);
        for (r = roscas_marco_m3()) translate(r[0]) circle(d = r[1]);
    }
}

// El marco en 3D, sobre la cara interior del anillo, con el cajeado de cada
// riel por el lado del anillo. ORDEN DE MONTAJE OBLIGADO: primero los seis
// rieles al marco (la cabeza queda en el cajeado, del lado que despues mira
// al anillo), despues el marco al anillo desde dentro -- con el costado YA
// asentado en el rebaje, porque el marco lo pisa. Al reves no se puede.
module marco_ventana() {
    translate([0, 0, t_anillo]) difference() {
        linear_extrude(t_placa) marco_ventana_2d();
        for (c = ejes_marco())
            translate(concat(c, [-0.1]))
                cylinder(h = prof_cajeado_riel + 0.1, d = d_cajeado_riel);
    }
}

// Dos marcos: uno por costado, espejados.
module marcos_ventana() {
    for (m = [0, 1])
        translate([0, 0, m ? ancho_total : 0])
            mirror([0, 0, m])
                marco_ventana();
}

// --- LA NARIZ: la banda del frente (2026-08-29) --------------------------
//
// Lo que se veia desnudo por delante y por abajo era el riel del frente de la
// fila de abajo y el hueco abierto entre anillos, de la tabla al canto del
// panel: 19 mm de frente vertical mas los 12.5 de cara de abajo que quedan por
// debajo de la cara del riel, sin nada que los cierre (nota 2 de Samuel). La
// nariz es una banda de la MISMA chapa que los marcos de la trasera
// (t_costilla), doblada sobre la nariz del anillo -- que desde hoy es RECTA:
// chaflan a 45 abajo y esquina de radio_chapa arriba, como el marco lateral de
// la referencia de Samuel -- y con un pie hacia dentro sobre la tabla, por
// donde se atornilla desde dentro con tres M4. Ningun tornillo en la cara
// vista.
//
// HASTA DONDE SUBE lo manda la placa de anclaje de la cara de abajo: en las
// puntas las dos viven en la misma rebanada de z, asi que la banda acaba
// hol_piel por debajo del arranque de la placa (que a su vez se retira
// retiro_placa_inf para dejarle sitio). Y NO PUEDE TAPAR LA CARA DEL RIEL: la
// fila de abajo es tapa y gira sobre el riel del valle, y al abrir la esquina
// honda del riel del frente sale por la cara en s = 13.0 -- la nariz es fija y
// tiene que quedarse debajo. Queda una linea de sombra de ~2 mm mas los 2 de
// labio del riel bajo el panel, lo mismo que entre dos filas de cualquier
// Eurorack. Lo mide guarda_nariz() en clearance_budget.py.
//
// GEMELA de _nariz(), _cajas_nariz() y bbox_desarrollo_nariz() en
// clearance_budget.py; los taladros los cruza taladros_nariz() en check_dxf.
function nariz_s_top() = pata("cara_inf")[4] - hol_piel;
function nariz_largo() = ancho_util - 2*hol_piel;
// El contorno EXTERIOR en el plano del perfil, del pie hacia arriba: pie sobre
// la tabla, chaflan, frente vertical y el tramo de cara de abajo.
function nariz_contorno() =
    let (c = chaflan_nariz, P = pts_perfil(),
         d = [sin(angulo_inferior), cos(angulo_inferior)])
    [[c + nariz_pie, 0], [c, 0], [0, c], P[1], P[1] + d*nariz_s_top()];
// Desarrollo: cada tramo por su cara exterior menos un BD por doblez -- dos a
// 45 en el chaflan y uno de angulo_inferior en P1.
function nariz_desarrollo() =
    let (c = chaflan_nariz)
    nariz_pie + c*sqrt(2) + (alto_frontal - c) + nariz_s_top()
    - 2*doblez_bd(45) - doblez_bd(angulo_inferior);
// Los tres M4 del pie: a 1.5 D del canto libre del pie (x del perfil) y a un
// cuarto, medio y tres cuartos del hueco entre anillos (z del mundo).
function nariz_m4_x() = chaflan_nariz + nariz_pie - 1.5*d_M4_paso;
function nariz_m4_z() = [for (f = [0.25, 0.5, 0.75]) t_anillo + ancho_util*f];

// Un tramo de chapa entre dos puntos del contorno, con el espesor hacia
// DENTRO: el perfil se recorre en sentido horario y el interior queda a la
// derecha de cada arista.
module tramo_chapa(A, B) {
    d = (B - A)/norm(B - A);
    r = [d.y, -d.x];
    polygon([A, B, B + r*t_costilla, A + r*t_costilla]);
}

function cruz_2d(a, b) = a.x*b.y - a.y*b.x;
function normal_derecha(A, B) =
    let (d = (B - A)/norm(B - A)) [d.y, -d.x];
function cruce_rectas(P, d, Q, e) =
    abs(cruz_2d(d, e)) < 0.000001
    ? (P + Q)/2
    : P + d*(cruz_2d(Q - P, e)/cruz_2d(d, e));
function polilinea_rehundida(C, u) =
    [for (i = [0 : len(C) - 1])
        i == 0
        ? C[i] + normal_derecha(C[i], C[i + 1])*u
        : i == len(C) - 1
          ? C[i] + normal_derecha(C[i - 1], C[i])*u
          : let (d0 = (C[i] - C[i - 1])/norm(C[i] - C[i - 1]),
                 d1 = (C[i + 1] - C[i])/norm(C[i + 1] - C[i]),
                 q0 = C[i] + normal_derecha(C[i - 1], C[i])*u,
                 q1 = C[i] + normal_derecha(C[i], C[i + 1])*u)
            cruce_rectas(q0, d0, q1, d1)];

module chapa_polilinea_3d(C, retiro, z0, largo) {
    R = polilinea_rehundida(C, retiro);
    translate([0, 0, z0])
        linear_extrude(largo)
            for (i = [0 : len(R) - 2]) tramo_chapa(R[i], R[i + 1]);
}

module nariz() {
    C = nariz_contorno();
    difference() {
        union() {
            // El pie queda a ras; la muesca nace del salto axial hasta el rebaje.
            chapa_polilinea_3d([C[0], C[1]], 0, pie_z0(), entre_anillos());
            chapa_polilinea_3d([C[1], C[2], C[3]], rehundido_chapa,
                               chapa_z0(), chapa_largo_rebaje());
            // La cola bajo el panel no se ve ni entra en el rebaje del anillo.
            chapa_polilinea_3d([C[3], C[4]], 0, pie_z0(), entre_anillos());
        }
        for (z = nariz_m4_z())
            translate([nariz_m4_x(), -0.1, z])
                rotate([-90, 0, 0])
                    cylinder(d = d_M4_paso + kerf, h = t_costilla + 0.2);
    }
}

// El DXF: el desarrollo plano, con el CANTO LIBRE DEL PIE en y = 0 -- un canto
// libre no se mueve al plegar, asi que los M4 caen a 1.5 D de el sin que los
// dobleces entren en la cuenta. Las lineas de plegado van en el pliego.
module nariz_2d() {
    // VISTA PREVIA: el DXF conserva el pie actual; la muesca se valida en 3D.
    difference() {
        square([nariz_largo(), nariz_desarrollo()]);
        for (z = nariz_m4_z())
            translate([z - t_anillo - hol_piel, 1.5*d_M4_paso])
                circle(d = d_M4_paso + kerf);
    }
}

// --- LA SECCION DEL ANILLO, y el cupon que se corta de ella --------------
// EL UNICO PLANO QUE DICE LAS PROFUNDIDADES (#237). Los dos ficheros del anillo
// son vistas de planta: costilla_2d lleva la silueta y la ventana, y
// costilla_dorso_2d el contorno del rebaje. Entre los dos cierran las cotas EN
// EL PLANO -- cara_anillo y rebaje_anillo, y las cruzan anillo_tiene_ventana()
// y anillo_tiene_rebaje() releyendo los ficheros --, pero ninguno de los dos
// sabe decir "14 de pletina", "11 de profundidad de rebaje" ni "1.5 x 45": eso
// es justamente lo que un DXF de planta no puede escribir. Hasta hoy esas tres
// cotas solo vivian en params.scad y en la prosa del pliego.
//
// Se dibuja con la CARA VISTA ABAJO (y = 0) y la pletina creciendo hacia y+,
// que es como se lee montada: lo que se ve del case es el canto de abajo.
//
// LAS DOS ARISTAS DE LA CARA VAN CHAFLANADAS, no una: costilla() aplica sus
// seis rodajas con offset(-f) sobre la silueta Y offset(-cara + f) sobre la
// ventana. Dibujar una sola aqui mandaria fresar un cupon que no es el perfil.
module seccion_anillo_2d() {
    c = chaflan_anillo;
    W = cara_anillo;
    T = t_anillo;
    R = rehundido_acrilico;
    B = rebaje_anillo;
    polygon([[c, 0], [W - c, 0], [W, c], [W, R], [W - B, R],
             [W - B, T], [0, T], [0, c]]);
}

module costilla() {
    n = 6;
    difference() {
        union() {
            for (i = [0 : n-1])
                let (f = chaflan_anillo * (1 - (i + 0.5)/n))
                translate([0, 0, i*chaflan_anillo/n])
                    linear_extrude(chaflan_anillo/n + 0.01)
                        difference() {
                            offset(delta = -f) perfil_lateral();
                            ventana_anillo_2d(f);
                        }
            translate([0, 0, chaflan_anillo])
                linear_extrude(t_anillo - chaflan_anillo) anillo_2d();
        }
        // el rebaje, por detras
        translate([0, 0, rehundido_acrilico])
            linear_extrude(t_anillo) rebaje_2d();
        // EL BOLSILLO DE LA TRASERA (2026-08-29, noche, 2), por detras, en el
        // tramo trasero: rebaje_anillo de hondo desde la cara interior,
        // cerrado por los dos extremos.
        translate([0, 0, t_anillo - rebaje_anillo])
            linear_extrude(rebaje_anillo + 0.1)
                bolsillo_trasero_2d();
        // El rebaje de chapa y el cajeado comparten suelo a 3 de la cara interior.
        translate([0, 0, t_anillo - rebaje_chapa])
            linear_extrude(rebaje_chapa + 0.1) {
                rebaje_chapa_2d();
                cajeado_brida_2d();
            }
    }
}

// El plegado de la chapa de LOS TRES MIEMBROS. Se llamo cost_bd() hasta el
// 2026-08-28 y la formula es la MISMA -- setback por dos menos el arco de la
// fibra neutra --, con los mismos parametros: es el mismo material y el mismo
// radio. Cambia el nombre y nada mas, porque la costilla dejo de plegarse y el
// nombre viejo prometia una pieza que ya no se dobla.
function miembro_bd() = 2*(radio_doblez_costilla + t_costilla)
                        - PI/2*(radio_doblez_costilla + k_factor*t_costilla);

// --- LA BRIDA DE EXTREMO, en el desarrollo ------------------------------
// Lo que la lengueta sobresale del recorte una vez descontado su doblez, y
// donde cae en el blank un punto que en la pieza montada esta a profundidad d
// del pliegue. Misma pareja de cuentas que pv_vuelo()/pv_desarrollo() para la
// pestana del valle, con los parametros de ESTA chapa.
// Bend deduction de un doblez a cualquier angulo (grados) en esta chapa. A 90
// da lo mismo que miembro_bd(): SB = (r + t)*tan(a/2), BA = a*(r + k*t).
// GEMELA de _bd_angulo() en clearance_budget.py.
function doblez_bd(a) = 2*(radio_doblez_costilla + t_costilla)*tan(a/2)
                        - a*PI/180*(radio_doblez_costilla + k_factor*t_costilla);
function brida_vuelo_dsr() = brida_largo - miembro_bd();
function brida_dsr(d) = miembro_bd() - d;

// La lengueta tumbada: un rectangulo pegado a cada punta del recorte, dentro
// de la banda del alma. Se dobla sobre una linea PERPENDICULAR al canto del
// anillo -- por eso su largo corre a lo largo del canto -- y lleva relieve en
// las dos esquinas, que en el desarrollo es el propio hueco entre bandas.
module brida_2d(y_centro, ancho, vuelo = 0) {
    v = vuelo > 0 ? vuelo : brida_vuelo_dsr();
    for (lado = [0, 1])
        translate([lado ? chapa_largo_rebaje() : -v, y_centro - ancho/2])
            rect_redondeado_2d(v, ancho, min(radio_brida, v/2));
}

// Sus dos M4 de paso: uno a brida_raiz() del pliegue (regla de chapa) y otro
// a 1.5 D del canto libre. dy desplaza la fila respecto al centro de la banda.
module brida_agujeros_2d(y_centro, dy) {
    for (lado = [0, 1], d = [brida_s_in(), brida_largo - 1.5*d_M4_paso])
        translate([lado ? chapa_largo_rebaje() - brida_dsr(d) : brida_dsr(d),
                   y_centro + dy])
            circle(d = d_M4_paso + kerf);
}

// El solido de una brida: chapa plana contra la cara que la recibe.
module brida_3d(x0, y0, ancho_x, ancho_y, z0, largo) {
    for (z = [z0, z0 + largo - t_costilla])
        translate([x0, y0, z])
            linear_extrude(t_costilla)
                rect_redondeado_2d(ancho_x, ancho_y, radio_brida);
}

// --- EL TECHO Y EL TALON (2026-08-29, noche, 2) -------------------------
//
// El TECHO (miembro alto) es la meseta del pico al canto con su retorno en
// el pico, y por detras baja de dos maneras, que se escogieron mirando --
// B, el 2026-08-30 -- (remate_trasero_chaflan): A, la banda plana de banda_trasera sobre una
// esquina de radio_chapa (la de #241); B, un chaflan de chaflan_nariz sobre
// P6... sobre P5, a chaflan como P0 y P6, y un labio vertical de techo_labio.
// Sin canal: en una sola chapa el labio no puede tapar el canto del
// acrilico Y tener un retorno detras, y el bolsillo de los anillos ya
// retiene la trasera en las dos direcciones por los lados. Sus dos bridas
// doblan del extremo del labio (o de la banda) como siempre; en B suben junto
// a la tira del chaflan y llevan un RELIEVE (un corte en la linea del
// doblez). Lo que aguanta solo lo mide guarda_miembro_alto(): es lo que puso
// techo_labio en 18.
//
// El TALON es la nariz de atras: pie sobre la tabla (tres M4 desde dentro),
// chaflan a 45 sobre P6 y labio vertical de talon_labio a ras del plano
// trasero, que tapa el canto de abajo de la trasera. Y talon_pestana_n
// PESTANAS lanzadas del pie, dobladas hacia arriba detras de la trasera: su
// tope hacia dentro, y estructura (guarda_trasera_flexion).
// Ni bridas ni rosca en el anillo. Lo mide guarda_talon().
//
// Los desarrollos son para el taller; los solidos, para colisiones y render.

// Desarrollo del techo, tumbado y macizo: el labio (o la banda) abajo con su canto
// libre en y = 0, el chaflan (B), la meseta y el retorno arriba, con un BD
// por doblez. Las bridas salen de las puntas del labio, con su relieve. La
// salida de aire queda bajo el alero, no atraviesa la meseta.
function techo_cara_alto() = remate_trasero_chaflan ? techo_labio + chaflan_nariz
                                                    : banda_trasera;
function techo_y_meseta0() = remate_trasero_chaflan
    ? techo_labio + chaflan_nariz*sqrt(2) - 2*doblez_bd(45)
    : banda_trasera - miembro_bd();
function techo_meseta_dev() = remate_trasero_chaflan ? prof_sup - chaflan_nariz : prof_sup;
module miembro_alto_2d() {
    retorno = retorno_meseta - doblez_bd(90 - angulo_superior);
    y_meseta0 = techo_y_meseta0();
    desarrollo = y_meseta0 + techo_meseta_dev() + retorno;
    largo = chapa_largo_rebaje();
    vuelo = brida_vuelo_dsr();
    y_brida = techo_cara_alto() - t_costilla - brida_ancho;
    difference() {
        union() {
            square([largo, desarrollo]);
            for (lado = [0, 1])
                translate([lado ? largo : -vuelo, y_brida])
                    rect_redondeado_2d(vuelo, brida_ancho,
                                       min(radio_brida, vuelo/2));
        }
        brida_agujeros_2d(techo_cara_alto(), -dist_rosca_ciega);
        // EL RELIEVE de la brida (B): la brida sube por encima del labio, junto
        // a la tira del chaflan, y un corte de corte_pestana en la linea del
        // doblez la suelta de ella para que no la arrastre al plegar. Y SU
        // ESQUINA DE ARRIBA VA A CHAFLAN: apoya en la cara del anillo, que en
        // P5 esta cortada a 45 (u + v = chaflan), y lo que quede fuera de esa
        // linea seria brida en el aire. Gemelo del poligono de _bridas().
        if (remate_trasero_chaflan)
            for (lado = [0, 1]) {
                s = lado ? 1 : -1;
                x0 = lado ? largo : 0;
                translate([x0 - (lado ? 0 : corte_pestana), techo_labio])
                    square([corte_pestana, chaflan_nariz - t_costilla + corte_pestana]);
                polygon([[x0, techo_cara_alto() - chaflan_nariz + t_costilla],
                         [x0, techo_cara_alto() - t_costilla + 0.01],
                         [x0 + s*(chaflan_nariz - 2*t_costilla), techo_cara_alto() - t_costilla + 0.01]]);
            }
    }
}

// El contorno exterior del talon en el plano del perfil, del labio hacia el
// pie -- en ese orden el interior queda a la derecha de cada tramo, que es
// lo que tramo_chapa() necesita. GEMELO del contorno de _talon().
function talon_contorno() =
    let (c = chaflan_nariz, pf = pts_perfil()[6].x)
    [[pf, c + talon_labio], [pf, c], [pf - c, 0], [pf - c - talon_pie, 0]];
// Desarrollo: labio + chaflan + pie menos los dos dobleces a 45.
function talon_desarrollo() =
    talon_labio + chaflan_nariz*sqrt(2) + talon_pie - 2*doblez_bd(45);

// Desarrollo del talon: el labio abajo (su canto libre en y = 0), el chaflan,
// el pie arriba con su canto libre en y = desarrollo. Los tres M4 del pie a
// 1.5 D de ese canto, en las mismas z que los de la nariz, y las ventanas de
// las pestanas: un corte en U (tres lados de kerf) que deja la linea del
// doblez sin cortar, hacia el canto libre del pie, con un taladro de alivio
// en cada esquina del corte, a caballo de la linea del doblez.
module talon_2d() {
    // VISTA PREVIA: 19.56 usa el pie retirado de 20, pero talon_pie ahora es 21.5;
    // el DXF queda sin la muesca hasta que se fije esa linea de doblez.
    d = talon_desarrollo();
    difference() {
        square([entre_anillos(), d]);
        for (z = nariz_m4_z())
            translate([z - t_anillo - hol_piel, d - 1.5*d_M4_paso])
                circle(d = d_M4_paso + kerf);
        // el corte en U, de corte_pestana de ancho, POR FUERA de la pestana:
        // la pestana mide talon_pestana_ancho x su desarrollo, y el corte la
        // rodea por los dos lados y por el fondo, dejando el doblez sin cortar
        for (zc = talon_pestana_z()) {
            zb = zc - t_anillo - hol_piel;
            ym = d - (talon_pestana_x() - talon_x_pie());
            dv = talon_pestana_dev();
            w  = talon_pestana_ancho;
            k  = corte_pestana;
            translate([zb - w/2 - k, ym]) square([k, dv + k]);
            translate([zb + w/2, ym]) square([k, dv + k]);
            translate([zb - w/2 - k, ym + dv]) square([w + 2*k, k]);
            // el alivio: un taladro a caballo de la linea del doblez en cada
            // esquina del corte, centrado en el propio corte
            for (s = [-1, 1])
                translate([zb + s*(w/2 + k/2), ym])
                    circle(d = alivio_pestana + kerf, $fn = 24);
        }
    }
}

function miembros_z0() = chapa_z0();
function techo_contorno() =
    let (P = pts_perfil(), d = [sin(angulo_superior), cos(angulo_superior)],
         pf = P[6].x, yt = P[5].y, c = chaflan_nariz)
    remate_trasero_chaflan
    ? [P[4] - d*retorno_meseta, P[4], [pf - c, yt],
       [pf, yt - c], [pf, y_labio_techo()]]
    : [P[4] - d*retorno_meseta, P[4], P[5],
       [pf, yt - banda_trasera]];
function techo_contorno_rehundido() =
    polilinea_rehundida(techo_contorno(), rehundido_chapa);

module miembro_alto() {
    P = pts_perfil();
    y1 = y_meseta();
    z0 = miembros_z0();
    pf = P[6].x;
    yt = P[5].y;
    c = chaflan_nariz;
    // Retorno, meseta, chaflan y labio forman una sola piel, retirada 1 mm.
    chapa_polilinea_3d(techo_contorno(), rehundido_chapa,
                       z0, chapa_largo_rebaje());
    // las dos bridas, planas contra la franja de la MESETA del anillo, de
    // t_costilla bajo la meseta hacia abajo. Con el techo en chaflan (B) su
    // esquina de arriba-atras va cortada a 45 como la del anillo: lo que
    // quedara fuera de u + v = chaflan seria brida en el aire (y asomaba por
    // el chaflan en el render). Gemelo del poligono de _bridas().
    // En y la brida NO se mueve con el rehundido: dobla del extremo del labio,
    // que sigue muriendo en y_labio_techo(), y su canto de arriba queda donde
    // hoy (y_meseta). Subirla hol_chapa metia el cajeado en el reborde.
    difference() {
        brida_3d(brida_x_dob() - brida_largo, y1 - brida_ancho,
                 brida_largo,
                 brida_ancho, t_anillo - rebaje_chapa,
                 ancho_total - 2*(t_anillo - rebaje_chapa));
        if (remate_trasero_chaflan)
            translate([0, 0, -1])
                linear_extrude(ancho_total + 2)
                    polygon([[pf - c, yt], [pf, yt - c], [pf + 2, yt - c],
                             [pf + 2, yt + 2], [pf - c, yt + 2]]);
    }
}

module talon() {
    C = talon_contorno();
    difference() {
        union() {
            chapa_polilinea_3d([C[0], C[1], C[2]], rehundido_chapa,
                               chapa_z0(), chapa_largo_rebaje());
            chapa_polilinea_3d([C[2], C[3]], 0, pie_z0(), entre_anillos());
        }
        for (z = nariz_m4_z())
            translate([talon_m4_x(), -0.1, z])
                rotate([-90, 0, 0])
                    cylinder(h = t_costilla + 0.2, d = d_M4_paso + kerf);
        // las ventanas de las pestanas, en el pie
        for (zc = talon_pestana_z())
            translate([talon_pestana_x() - talon_pestana_dev(), -0.1,
                       zc - talon_pestana_ancho/2])
                cube([talon_pestana_dev(), t_costilla + 0.2, talon_pestana_ancho]);
    }
    // las pestanas, de pie detras de la trasera
    for (zc = talon_pestana_z())
        translate([talon_pestana_x() - t_costilla, t_costilla,
                   zc - talon_pestana_ancho/2])
            cube([t_costilla, talon_pestana_alto, talon_pestana_ancho]);
}

module miembros() {
    miembro_alto();
    talon();
}

module rail_2020(largo) { cube([rail, largo, rail], center = true); }

// Riel EUROrack. Los ejes locales no son intercambiables como en el 2020: tras
// el rotate([0,0,-a]) rotate([90,0,0]) de rails(), la X local acaba sobre la
// NORMAL INTERIOR de la cara (o sea el fondo del riel) y la Z local sobre la
// direccion de la cara (su alto). Verificado con las dos matrices a mano.
module rail_er(largo) { cube([rail_er_fondo, largo, rail_er_alto], center = true); }

// --- planchas rectangulares del cuerpo (cada una con SU espesor) ------
// Agujeros M3 contra la RETICULA de los miembros de chapa, repartidos a ~paso.
// Fueron tuercas T en la ranura de los largueros 2020 hasta el 2026-08-27:
// alli el reparto daba igual porque la ranura era corrida. Ahora no.
//
// IBA DESCENTRADA y nadie la miraba: arrancaba en paso/2 y avanzaba de paso en
// paso hasta donde llegara, o sea que sobre 528.32 dejaba 50.00 de orilla a la
// izquierda y 78.32 a la derecha. 28 mm de diferencia en la pieza que carga el
// transformador. El paso ahora se estira para caber un numero entero de veces,
// que es lo que el codigo viejo QUERIA decir con ese paso/2 de arranque:
// orillas iguales y valiendo medio paso.
// Cuantos tornillos caben en un largo con el paso nominal. Se saca aparte
// porque la tabla la necesita para su propia fila y no puede usar
// fila_agujeros(): sus agujeros van ALARGADOS, no redondos.
function n_agujeros(largo = 0, paso = reticula_paso) =
    max(1, round((largo == 0 ? bandeja_base_fondo() : largo)/paso));

module fila_agujeros(largo, y, paso = reticula_paso, d = d_M3_paso) {
    n = max(1, round(largo/paso));
    e = largo/n;                       // paso real, <= paso pedido + pico
    for (i = [0 : n-1])
        translate([e*(i + 0.5), y]) circle(d = d + kerf);
}

module plancha(l, a) square([l, a]);   // l = ancho_util, a = fondo local

// fondo derivado de sus DOS railes frontera, igual que bandeja_entrepiso
// (ronda final). La formula vieja `prof_inferior - 2*rail - 4` colocada en
// x=rail dejaba las filas a +18 y -24 mm de las centerlines de base
// delantera / base trasera, y el canto trasero a 4 mm de tocar siquiera el
// rail trasero: la bandeja que CARGA EL PSU (spec §5) no apoyaba atras.
// solapes() no lo vio nunca porque una placa flotando es disjunta —
// alineacion() en clearance_budget.py es la puerta que si lo ve.
module bandeja_base_2d() {
    // EL SUELO CIERRA (2026-08-21). El canto delantero estuvo A RAS del larguero
    // de base delantera, y como ese larguero se retira por detras del riel de
    // panel, el suelo del case tenia 37.96 mm abiertos por delante. Ahora la
    // plancha vuela por delante del larguero hasta donde muere la curva del
    // costado: el unico hueco que queda por abajo es el propio redondeo de la
    // esquina, que se lee como esquina y no como ranura.
    //
    // No salio gratis: el riel de panel del frente bajaba a y=4.84 y el techo de
    // la plancha esta en y=8, o sea que se metia 3.16 mm dentro del plano del
    // suelo. Subirlo costo 8.46 mm de alto de aparato (ver alto_frontal). Y la
    // ENTRADA DE AIRE, que era este hueco, se fue a la trasera. Vivio aqui unas
    // horas como rejilla dibujada en el vuelo y se le veia: el acrilico naranja
    // es TRASLUCIDO y el campo de ranuras se transparentaba a lo largo del canto
    // inferior. Ahora el vuelo es plancha maciza y el suelo cierra de verdad.
    v = vuelo_zocalo;
    difference() {
        plancha(bandeja_base_ancho(), bandeja_base_fondo());
        // LAS DOS FILAS DE FIJACION A LAS COSTILLAS. Corren a lo largo de la
        // tabla, una bajo cada costilla, y NO son agujeros redondos: la tabla
        // es maciza y se mueve a contraveta. La veta va a lo LARGO (los 570 mm
        // del ancho del case, como en la foto), asi que lo que crece y encoge
        // es el FONDO -- la direccion en la que corre esta misma fila. De ahi
        // que las ranuras sean alargadas en Y local.
        //
        // El del MEDIO va redondo a proposito: la tabla tiene que crecer hacia
        // los dos lados desde un punto fijo. Si todos fueran ranura, la tabla
        // se arrastra hacia un extremo y el vuelo deja de ser simetrico.
        // AL MEDIO DEL CANTO INFERIOR DEL ANILLO desde el 2026-08-28. Fue
        // t_cheek + t_costilla/2 -- el alma de la costilla de chapa, que se
        // apoyaba detras del acrilico -- y esa cota apuntaba a un sitio donde
        // ya no hay pieza: hoy el anillo ES el canto, 14 mm de pletina de
        // z=0 a z=14, y el M5 de la tabla va a una rosca ciega en el centro
        // de ese canto. Esas seis roscas NO salen en costilla_dorso_2d: van
        // en el canto, no en el dorso, y un DXF de la cara no las sabe
        // dibujar -- se listan en el pliego (Tarea 5).
        for (zc = [v + t_anillo/2, v + ancho_total - t_anillo/2])
            for (i = [0 : n_agujeros() - 1])
                let (y = bandeja_base_fondo()*(i + 0.5)/n_agujeros(),
                     medio = (i == floor(n_agujeros()/2)))
                    translate([zc, y])
                        if (medio) circle(d = d_M5_paso + kerf);
                        else hull() for (dy = [-holgura_veta, holgura_veta])
                            translate([0, dy]) circle(d = d_M5_paso + kerf);
        // LOS CUATRO TALADROS DE PIE (Tarea 6). paticas() atornilla las
        // paticas de goma A LA TABLA, no al acrilico (BOM), asi que la tabla
        // necesita su propio taladro por pata -- REDONDO y no ranura: la
        // patica no la mueve la contraveta, la sostiene.
        //
        // MISMAS CUATRO POSICIONES QUE paticas(), pasadas por la MISMA
        // conversion de coordenadas que las dos filas de arriba: local x =
        // vuelo_zocalo + z del mundo, local y = vuelo_zocalo + x del mundo
        // (ver la nota larga sobre bandeja_base_2d() mas abajo en este
        // fichero, junto a ch_pos()). Repetir aqui la formula de paticas()
        // en vez de llamarla es a proposito: paticas() dibuja un cilindro
        // rotado en 3D y este agujero es 2D puro, asi que no hay una sola
        // funcion que sirva a los dos -- pero las CUATRO coordenadas de
        // mundo son las mismas literales, y por eso el comentario de
        // paticas() vale tambien aqui.
        for (wx = [alto_frontal/2 + d_pie/2, centro_talon().x])
            for (wz = [d_pie/2, ancho_total - d_pie/2])
                translate([v + wz, v + wx])
                    circle(d = d_pie_tornillo + kerf);
        // LOS TRES M4 DE LA NARIZ (2026-08-29): la banda del frente se
        // atornilla a la tabla por su pie, desde dentro. Misma conversion de
        // coordenadas que los pies y mismo diametro (d_pie_tornillo): es el
        // mismo herraje a la misma madera. Los cruza taladros_nariz().
        for (wz = nariz_m4_z())
            translate([v + wz, v + nariz_m4_x()])
                circle(d = d_pie_tornillo + kerf);
        // LOS TRES M4 DEL TALON (2026-08-29, noche): la banda de abajo del
        // plano trasero se atornilla a la tabla por su pie, como la nariz.
        // Los cruza taladros_talon().
        for (wz = nariz_m4_z())
            translate([v + wz, v + talon_m4_x()])
                circle(d = d_pie_tornillo + kerf);
        // LOS CUATRO M4 DEL CHASIS DEL PSU (2026-08-29, noche): el chasis
        // apoya en la tabla y se atornilla a ella por el suelo, desde abajo,
        // a tuerca remachable en el acero. Los cruza taladros_talon() con
        // chasis_cuerpo_2d, que lleva los mismos cuatro.
        for (q = chasis_tornillos_tabla())
            translate(q) circle(d = d_M4_paso + kerf);
        // LA SALIDA DE CABLES DEL CHASIS. Era un campo de ondas de 104 x 32
        // dibujado como VENTILACION, y con la caja de acero encima ya no
        // ventila nada (spec §3.3). El cambio no es solo de nombre: una onda
        // son ranuras de 4 mm con puentes, y por 4 mm no pasa un mazo. Ahora
        // es un agujero de verdad.
        //
        // Y se DERIVA de la ranura del suelo del chasis, no al reves: este
        // hueco existe para dejarla pasar, asi que crece con ella y la
        // contiene por construccion. El assert de clearance_budget lo
        // confirma releyendo las dos, por si alguien toca una sola.
        translate(salida_cables_xy()) {
            w = chasis_salida_ancho + 2*salida_holgura;
            h = chasis_salida_fondo + 2*salida_holgura;
            r = salida_radio;
            hull() for (dx = [r, w - r], dy = [r, h - r])
                translate([dx, dy]) circle(r = r + kerf/2);
        }
    }
}


// TRES columnas de standoff, no dos. Con solo las cuatro esquinas el vano es
// de 518 mm y la plancha se descuelga 1.76 mm por su PROPIO PESO, sin que nadie
// la toque -- calculado con acrilico colado a 3 GPa. Partiendo el vano por la
// mitad cae a 0.11 (la flecha va con L^4, asi que partir en dos divide por 16).
// Cuatro tornillos mas en todo el case para que la cara trasera no ondee.
// EL RELIEVE DE LA TRASERA. Era la onda SIERRA; desde el 2026-08-24 es la
// palabra KONDOR, el nombre de la casa (Samuel). Vive fuera de
// piel_trasera_2d() porque tiene DOS clientes con papeles distintos: NO se
// recorta en el 2D de corte (es cajeado ciego) y la vacia piel_trasera() en 3D
// a kondor_prof. Derivar su sitio dos veces es el patron del `- 15` copiado en
// cinco ficheros que costo la tanda de la trasera, asi que se deriva UNA vez
// aqui y los dos la llaman.
//
// LA FUENTE ES UNA DEPENDENCIA DE COMPILACION, y de las peligrosas: si no esta
// instalada, OpenSCAD NO falla -- avisa por consola y sustituye por otra, o
// sea que el fichero sale, parece bueno y la pieza es otra.
//
// HUELLA PARA CAZAR LA SUSTITUCION: con la fuente correcta y los parametros de
// params.scad, KONDOR sale en 10 CONTORNOS (K1 O2 N1 D2 O2 R2) y la caja mide
// 216.87 x 32.44 mm. Si esos numeros no salen, la fuente se sustituyo.
//
// POR QUE FRANKLIN GOTHIC MEDIUM (2026-08-24, Samuel pidio "brutalismo y
// modernismo berlines"). Los dos berlines apuntan a letras distintas:
//
//   modernismo berlines  = la GROTESCA. En concreto la Akzidenz-Grotesk de
//                          H. Berthold AG, BERLIN, 1896 -- la letra de la
//                          Neue Typographie de Tschichold. No esta instalada
//                          (Berthold, con licencia) y Franklin Gothic es lo
//                          mas cerca que se llega sin comprarla: grotesca de
//                          1902, misma generacion y color parecido.
//   brutalismo berlines  = la DIN 1451 (Bahnschrift), que es lo que se estarce
//                          en una señal y en una placa de maquina.
//
// Se elige la grotesca porque la DIN es MONOLINEAL DE INGENIERIA: como nombre
// se lee a numero de pieza, no a marca. Franklin tiene peso, que es lo que el
// brutalismo pide y la DIN no da.
//
// Y GANA TAMBIEN POR FABRICACION, que aqui no es un desempate menor: el
// relieve es un CAJEADO, o sea que la fresa tiene que entrar DENTRO del trazo
// de cada letra, asi que ningun trazo puede medir menos que fresa_d. Medido
// erosionando la palabra y contando contornos (si al erosionar r se pierde un
// trazo, ese trazo medía menos de 2r):
//
//   fuente                   fresa 3 mm   fresa 4 mm
//   Bahnschrift (DIN)           pasa        ROMPE
//   Bahnschrift SemiBold        pasa        ROMPE
//   Franklin Gothic Book        pasa        ROMPE
//   Franklin Gothic Medium      pasa         pasa     <- este
//   Franklin Gothic Demi        pasa         pasa
//   Arial                       pasa        ROMPE
//
// O sea: con la fresa REAL (3 mm) valen todas, pero Medium y Demi tienen todo
// trazo >= 4 mm y las demas se quedan entre 3 y 4. Si el taller sube de fresa,
// las otras dejan de salir. Demi es el mismo trato con mas masa: cambiar esta
// linea es todo lo que hace falta.
//
// ESTO NO LO VIGILA NINGUNA PUERTA TODAVIA. guarda_fresado() mira las ranuras
// y los concavos, no la palabra. Pendiente.
//
// No vive en params.scad porque ese fichero es NUMERICO PURO (ver su cabecera):
// el regex de leer_params() pide un valor numerico, asi que una cadena ahi se
// ignoraria en silencio -- que es peor que no ponerla.
KONDOR_FONT = "Franklin Gothic Medium";

function trasera_y_relieve() =
    trasera_campo()[0]
    + 0.74*(trasera_campo()[1] - trasera_campo()[0]);

// La onda de abajo, que es la frontera de arriba de la banda libre.
function trasera_y_bajas() =
    trasera_campo()[0]
    + 0.37*(trasera_campo()[1] - trasera_campo()[0]);

// LA BANDA LIBRE entre la fila de M3 de abajo y esa onda. Sale de
// piel_trasera_2d() -- donde vivio como dos locales -- el 2026-08-28, cuando
// la ESCUADRA se convirtio en su cuarto consumidor: la comparten la rejilla de
// entrada, la ventana de la red, el hueco que las centra y ahora el reparto de
// los M3 de la escuadra, que tienen que caer FUERA de ella. Copiarla habria
// sido la cuarta version del mismo numero. Gemela de _banda_libre_trasera().
//
// El termino vent_ancho_ranura/2 no es decorativo: la onda es un hull de
// circulos, asi que su borde de MATERIAL cae medio ancho de ranura por debajo
// de la polilinea. Sin ese termino el parametro medía 2 mm menos de lo que
// decia.
// SIN ESPINA desde la trasera capturada: la fila de M3 que la rejilla tenia
// que librar murio, y la rejilla arranca a un puente de la coronacion del
// labio del talon.
function banda_libre_trasera() =
    [trasera_campo()[0] + vent_puente_min,
     trasera_y_bajas() - vent_periodo*0.35 - vent_ancho_ranura/2
                       - vent_separacion];

// OJO CON EL ESPEJO -- ESTO NO ES UN DESCUIDO, ES LA CORRECCION.
//
// piel_trasera() extruye desde el plano trasero HACIA DENTRO del case, asi que
// la cara que se ve desde fuera es la z=0 de la extrusion: el DXF de la trasera
// esta dibujado TAL COMO SE VE DESDE DENTRO. Mientras cada recorte fue una onda,
// una ranura o un rectangulo eso daba igual -- ninguno es quiral y la plancha se
// voltea. Una PALABRA si lo es, y el primer render salio leyendo "ЯODNOX".
//
// Por eso hay dos versiones y cada una tiene su cliente:
//
//   espejo = false  el fichero de FABRICACION (PART kondor_cajeado_2d). Se lee
//                   KONDOR del derecho, que es lo unico que un taller puede
//                   interpretar sin preguntar: "esto es lo que tiene que verse
//                   en la cara exterior".
//   espejo = true   lo que resta piel_trasera() en 3D, para que al mirar el
//                   case por detras la palabra se lea.
//
// Si algun dia se decide que el DXF de la trasera se dibuje visto desde FUERA
// (que seria mas sano ahora que la pieza tiene una cara con cajeado y otra sin
// el), esto se cae y hay que mover con el la x del recorte del IEC, que HOY
// esta bien: cae junto al costado derecho como pide la spec §7.
module kondor_2d(espejo = false) {
    translate([trasera_au()/2, trasera_y_relieve()])
        scale([espejo ? -1 : 1, 1])
            text("KONDOR", font = KONDOR_FONT, size = kondor_size,
                 spacing = kondor_spacing, halign = "center", valign = "center");
}

module piel_trasera_2d() {
    // CAPTURADA COMO LAS MEJILLAS desde el 2026-08-29 por la noche (2): sus
    // puntas dentro de los bolsillos de los anillos, y NI UN TALADRO. Ni las
    // dos filas de M3 ni las muescas de esquina: el canto de arriba muere bajo
    // la brida del techo. Lo que queda son la rejilla, las ondas, la ventana
    // de la red y KONDOR, anclados al campo visible (trasera_campo).
    au = trasera_au();
    P  = pts_perfil();
    // UNA sola plancha desde el 2026-08-21: fueron dos (piel_inferior y
    // piel_superior) partidas a la altura del entrepiso, porque cada una se
    // atornillaba a los dos largueros de SU piso. Muerta la bandeja de
    // entrepiso esa frontera dejo de existir. Va en t_piel (8), que es su
    // propio espesor desde el 2026-08-21.
    // Canto de abajo EN EL PLANO DEL SUELO. Estuvo 15 mm por debajo del centro
    // del larguero de base trasera, o sea en y=3 -- se escribia ct_base().y - 15,
    // con la lista de los 2020 que murio el 2026-08-28 --, y eso no era una cota
    // del case sino la distancia al canto de la fila de M3 leida al reves. Ese
    // 15 no sabia donde estaba el suelo, y dejaba un rebaje corrido de
    // 528 x 3 x 8 a lo largo de todo el canto trasero -- una junta de sombra,
    // que es el lenguaje que esta pieza enterro al empotrarse. Ahora la cara
    // trasera es continua desde el piso hasta la MESETA del miembro trasero
    // alto (decia "tapa de remate": esa plancha suelta dejo de existir el
    // 2026-08-27, cuando se integro en el miembro como una cara mas).
    //
    // El 0 no es un numero libre: es el plano inferior del case, el mismo
    // datum del que cuelga la bandeja de base (y=0 a t_base) y donde muere el
    // canto de los costados. Lo vigila guarda_piso(), assert 3 (era el 4 hasta
    // el 2026-08-28: esa puerta tiene tres asserts y el ultimo conservaba el
    // numero de una version con cuatro).
    //
    // La fila de M3 de abajo se aleja del canto al bajarlo: 15 -> 18 mm, o sea
    // MAS material alrededor del tornillo. Y las ondas y la rejilla no se
    // mueven: van derivadas de f_base/f_tras, que son diferencias contra
    // ce[].y y por tanto no dependen de y0.
    // SOBRE EL PIE DEL TALON desde el 2026-08-29 por la noche: el canto de
    // abajo ya no esta en el plano del suelo sino t_costilla por encima, sobre
    // el pie. Y OJO CON EL ORIGEN: este 2D se dibuja en y DEL MUNDO -- el
    // canto de abajo cae en y = y0, no en 0 -- para que las ondas, la rejilla,
    // la ventana de red y la palabra KONDOR, que se derivan en coordenadas del
    // case, sigan cayendo donde caen sin restar nada. El DXF sale con su
    // origen 1.5 por debajo de la pieza; al laser le da igual.
    y0   = trasera_y0();
    alto = trasera_alto();
    // Las ondas van derivadas de las dos filas que las rodean: asi no se acercan
    // a un tornillo si un larguero se mueve.
    //
    // La de abajo sube a 0.37 (estuvo en 0.32) para SEPARARSE de la rejilla que
    // tiene debajo. Con la banda derivada de la onda y separada solo por
    // vent_puente_min, los dos campos se leian como uno; subir la onda sola no
    // arreglaba nada, porque la rejilla subia con ella. Lo que separa de verdad
    // es vent_separacion, y la onda sube para que la rejilla no encoja al
    // hacerle sitio: la banda pasa de 40.46 a 41.47 mm.
    y_bajas  = trasera_y_bajas();
    y_sierra = trasera_y_relieve();
    // El IEC va CENTRADO en la banda libre que dejan la fila de tornillos por
    // abajo y la onda por arriba. Estuvo en y=22 fijo, a 7 mm de la fila -- y
    // uno de los cinco M3 cae justo dentro de su franja de X (x=475.2), asi que
    // ahi quedaban 3.5 mm entre la arandela y el recorte. Ahora las dos
    // fronteras son piezas reales y el hueco se reparte solo.
    // La banda libre entre la fila de tornillos y la onda. La comparten la
    // rejilla y el IEC, y por eso se calcula UNA vez aqui y se les pasa: si cada
    // uno la rederivara, un cambio en vent_separacion los moveria por separado y
    // el recorte dejaria de estar centrado en el campo.
    // El canto izquierdo de la ventana se DERIVA del margen al canto derecho.
    // Estuvo como "au - 70" en tres sitios (dos aqui y uno en el budget), o sea
    // el canto izquierdo contado desde la derecha -- un numero que no queria
    // decir nada y que ya no sabia si lo que protegia era el canto o el campo.
    x_iec0 = au - iec_margen_der - iec_ancho;
    // LA BANDA LIBRE vive en banda_libre_trasera() desde el 2026-08-28. Fueron
    // dos locales aqui mientras solo la usaban la rejilla y la ventana de red;
    // la escuadra es el cuarto consumidor y necesita SU frontera de arriba
    // desde fuera de este modulo, asi que la cuenta se mudo a una funcion.
    lib0 = banda_libre_trasera()[0];
    lib1 = banda_libre_trasera()[1];
    difference() {
        translate([0, y0]) plancha(au, alto);
        rejilla_entrada(au, lib0, lib1, x_iec0);
        translate([au*0.10, y_bajas])  onda("triangulo", au*0.35);
        translate([au*0.55, y_bajas])  onda("cuadrada",  au*0.35);
        // AQUI IBA LA SIERRA, y desde el 2026-08-24 no va nada: ese relieve
        // es la palabra KONDOR y es CAJEADO CIEGO. Un DXF de contorno no sabe
        // decir "hasta 4 mm de profundidad", asi que la vacia piel_trasera()
        // en 3D. Ver kondor_2d() arriba. Este fichero de corte YA NO ES la
        // pieza entera, igual que el DXF del chasis no dice de donde doblar.
        // VENTANA de paso de la entrada de red -- no el recorte donde se encaja
        // el conector. El conector lo sostiene una pieza fija atornillada al
        // larguero de base trasera (Samuel, 2026-08-23): la trasera se quita con
        // 10 M3 y la spec §7 dice que las pieles removibles nunca llevan mains.
        // Las tres cotas son PROVISIONALES y viven en params.scad (#130).
        // +kerf como todo hueco interior del fichero.
        translate([x_iec0, lib0 + (lib1 - lib0 - iec_alto)/2])
            square([iec_ancho + kerf, iec_alto + kerf]);
    }
}

// LA ENTRADA DE AIRE DEL CASE. Se mudo CUATRO veces el 2026-08-21 y se queda
// aqui, abajo del todo en la trasera. Vale la pena el recuento porque cada
// mudanza cerro una pregunta:
//
//   1. hueco de 37.96 mm en el suelo   -- no era diseno, era lo que sobraba
//   2. trasera, abajo                  -- al cerrar el suelo hubo que dibujarla
//   3. suelo, en el vuelo              -- Samuel dejo la trasera con sus ondas
//   4. trasera otra vez                -- en el vuelo SE VEIA: el acrilico
//                                         naranja es traslucido y el campo se
//                                         transparentaba por el canto de abajo
//
// Va ABAJO a proposito. El aire frio entra por lo mas bajo del piso de la
// fuente -- que es donde estan el toroide y los reguladores -- y sale por la
// meseta y por las ondas. Es tiro natural, no
// adorno; entrar por arriba lo mataria.
//
// Ranuras IGUALES a las del valle: mismo ancho, mismo paso HP, misma malla. No
// es economia de codigo, es que la malla HP es la medida del instrumento y el
// adorno ES la regla (ver la nota de valle_paso_hp en params.scad).
//
// Lo vigila guarda_aire() en clearance_budget, y no por area sino por SALTO
// TERMICO. "Entrada >= salida" fue el criterio unas horas y se rompio en la
// mudanza 3, a proposito: lo que hay que exigir no es paridad de areas sino que
// el aparato no se caliente, y eso se calcula.
// La banda (y0, y1) llega DADA desde piel_trasera_2d y no se rederiva aqui: es
// la misma que centra el hueco del IEC, y si cada uno la calculara por su cuenta
// bastaria tocar vent_separacion para que el recorte dejara de estar centrado en
// el campo sin que nada lo cantara.
module rejilla_entrada(au, y0, y1, x_iec0) {
    n_hp = round(largo_riel/hp);
    // El IEC se salta por COLUMNAS ENTERAS: una ranura partida por el recorte
    // deja un diente de acrilico colgando de un lado, que es justo donde el
    // PMMA rompe. Se aparta media anchura de recorte + media de ranura + puente.
    //
    // x_iec0 llega DADO por la misma razon que la banda (y0, y1): rederivarlo
    // aqui fue lo que dejo el mismo "au - 70" copiado en tres sitios, y el dia
    // que la pieza de red se elija y cambie iec_ancho, un campo se enteraria y
    // el otro no.
    x_iec = x_iec0 + iec_ancho/2;
    hueco = (iec_ancho + vent_ancho_ranura)/2 + vent_puente_min;
    // Las columnas que tapaba el ala A de la escuadra se saltaron del 28-08 al
    // 29-08 por la noche; la escuadra murio con el marco de la ventana y la
    // rejilla vuelve a cortar todas las que libran la ventana de red.
    for (n = [valle_paso_hp : valle_paso_hp : n_hp - valle_paso_hp])
        if (abs(n*hp - x_iec) >= hueco)
            translate([n*hp, (y0 + y1)/2]) ranura(y1 - y0, vent_ancho_ranura);
}

// --- tapa del valle ----------------------------------------------------
// Ranura de extremos redondos. Redondos y no cuadrados por lo de siempre en
// acrilico: una esquina viva dentro de un hueco es donde arranca la fisura.
module ranura(largo, ancho) {
    hull() for (s = [-1, 1])
        translate([0, s*(largo - ancho)/2]) circle(d = ancho + kerf);
}

// Banda delantera del valle: LISA desde el 2026-08-28. La salida de aire sube a
// la meseta del miembro alto, donde la misma area compra mas tiro.
// --- LA PESTANA DE LA TAPA DEL VALLE ------------------------------------
// Misma cuenta de plegado que la costilla y que el chasis, con los parametros
// de ESTA chapa. Ver el bloque largo de ch_sb() para la derivacion.
function pv_sb() = radio_doblez_valle + t_valle;
function pv_ba() = PI/2 * (radio_doblez_valle + k_factor*t_valle);
function pv_bd() = 2*pv_sb() - pv_ba();
// Lo que la pestana desplegada sobresale del contorno de la tapa.
function pv_vuelo() = pestana_valle - pv_bd();

// Profundidad del M3 bajo la CARA DE ARRIBA de la tapa. La tangente del doblez
// cae a SB de esa cara y desde ahi la regla de chapa pide 2t antes de taladrar;
// sumado el radio del agujero, el centro va a SB + 2t + d/2.
function pv_a() = pv_sb() + 2*t_valle + d_M3_paso/2;

// Un punto a profundidad d bajo la cara de arriba cae, en el DESARROLLO, a
// BD - d del contorno. Sale de que el tramo recto de la pestana empieza a
// SB - BA del contorno y desde ahi se mide d - SB de chapa: BD - d.
function pv_desarrollo(d) = pv_bd() - d;

// Donde va el tornillo, en X del perfil. La pestana ocupa los ultimos 3D del
// vuelo delantero: es el minimo que deja 1.5D de material a cada lado del M3 y
// abre 63.75 grados; con 11 mm se quedaria en 59.5 y guarda_tapa() la rechaza.
function pv_ancho_x() = 3*d_M3_paso;
function pv_x() = ventana_valle()[0] - pv_ancho_x()/2;

// LA BANDA MUERE CONTRA LAS PLACAS DEL VALLE, no contra el anillo, desde el
// 2026-08-28: mide lo mismo que un riel y sus dos pestanas apoyan planas
// sobre la cara interior de esa placa, con un M3 roscado EN ella. Su rosca no
// cabe en la franja del anillo -- el M3 cae a pv_a() = 13.7 por debajo del
// plano del valle y la franja de 14 solo admite hasta 10.25 --, y en la boca
// tampoco hay franja libre: la ocupa la propia placa (ruling R3).
// Los 6 mm que la banda deja libres en cada punta NO son un hueco: ahi esta el
// canto de la placa, a ras del plano del valle.
function tapa_valle_au() = ancho_util - 2*t_placa;

module tapa_valle_2d() {
    au = tapa_valle_au();
    xv = x_valle();
    // Solo queda el vuelo DELANTERO: acaba antes del primer Z-Rail 1U. La
    // banda queda maciza: Samuel no quiere ver ranuras en el valle.
    largo = ventana_valle()[0] - xv[0];
    // El Z-Rail 3U del valle roza 0.57 mm de la esquina libre de la pestana.
    // Una muesca de 1 x 1 lo libra sin acercarse al M3 ni separar la pieza.
    inicio_pestana = largo - pv_ancho_x();
    difference() {
        union() {
            plancha(au, largo);
            // Las dos pestanas ocupan el extremo trasero del vuelo delantero.
            // Al tocar el contorno de la banda, el DXF sigue siendo UNA pieza.
            for (lado = [0, 1])
                translate([lado ? au : -pv_vuelo(), inicio_pestana])
                    square([pv_vuelo(), pv_ancho_x()]);
        }
        // Alivio gemelo en la esquina libre DELANTERA de cada pestana.
        translate([-pv_vuelo(), inicio_pestana])
            square([muesca_riel_valle, muesca_riel_valle]);
        translate([au + pv_vuelo() - muesca_riel_valle, inicio_pestana])
            square([muesca_riel_valle, muesca_riel_valle]);
        // el M3 de cada pestana, en el desarrollo
        for (lado = [0, 1])
            translate([lado ? au - pv_desarrollo(pv_a())
                            : pv_desarrollo(pv_a()),
                       pv_x() - xv[0]])
                circle(d = d_M3_paso + kerf);
    }
}

// --- la firma: ranuras con forma de onda -------------------------------
// Cada onda es una polilinea engordada vent_ancho_ranura, N periodos de
// vent_periodo. Puentes >= vent_puente_min los garantiza el periodo.
module onda(tipo, largo) {
    n = max(2, floor(largo / vent_periodo));
    a = vent_periodo * 0.35;            // amplitud vertical
    pts = tipo == "sierra" ?
            [for (i = [0:n-1], p = [[0,-a],[1,a]])
                [(i + p[0]) * vent_periodo, p[1]]] :
          tipo == "triangulo" ?
            [for (i = [0:n-1], p = [[0,-a],[0.5,a]])
                [(i + p[0]) * vent_periodo, p[1]]] :
            [for (i = [0:n-1], p = [[0,-a],[0.001,a],[0.5,a],[0.501,-a]])
                [(i + p[0]) * vent_periodo, p[1]]];
    for (i = [0 : len(pts) - 2])
        hull() {
            translate(pts[i])   circle(d = vent_ancho_ranura + kerf);
            translate(pts[i+1]) circle(d = vent_ancho_ranura + kerf);
        }
}

// =====================================================================
// CHASIS DE ACERO DEL PSU  (#107, spec §3.3, plan v3 Task 9)
// =====================================================================
// Tres piezas de chapa: cuerpo (una sola pieza doblada en bandeja, esquinas
// soldadas), tapa (plana con faldon) y refuerzo (plano, sin doblar).
//
// EL DESARROLLO NO SE DIBUJA A OJO. Un patron plano no es "la caja abierta":
// la chapa se ESTIRA al doblar, asi que la suma de los lados exteriores no es
// el largo del recorte. La cuenta estandar, con angulo de 90 grados:
//
//   setback  SB = r + t                         (lo que se come cada doblez)
//   bend allowance  BA = (pi/2)(r + k*t)        (longitud del arco neutro)
//   bend deduction  BD = 2*SB - BA              (lo que hay que restar)
//   desarrollo = suma de lados EXTERIORES - BD por doblez
//
// Con r = t = 1.5 y k = 0.42 salen BA = 3.35 y BD = 2.65 mm: 5.3 mm menos de
// chapa por eje. No es cosmetico -- cortar el desarrollo sin restarlos da una
// caja 5 mm mas grande en las dos direcciones, y la tapa deja de casar con el
// cuerpo aunque la caja siga entrando en la bandeja.
//
// Los tres numeros son SUPUESTOS del taller (ver params.scad). Cuando conteste
// se cambian ahi y todo esto se recalcula solo.
function ch_sb() = radio_doblez + t_chapa;
function ch_ba() = PI/2 * (radio_doblez + k_factor*t_chapa);
function ch_bd() = 2*ch_sb() - ch_ba();

function ch_cuerpo_ext() = [chasis_int_x + 2*t_chapa,
                            chasis_int_y + 2*t_chapa,
                            chasis_int_z + t_chapa];
function ch_tapa_int()   = [ch_cuerpo_ext().x + chasis_hol_tapa,
                            ch_cuerpo_ext().y + chasis_hol_tapa];
function ch_tapa_ext()   = [ch_tapa_int().x + 2*t_chapa,
                            ch_tapa_int().y + 2*t_chapa];
function ch_alto()       = 2*t_chapa + chasis_int_z;   // exterior, con tapa
// desfase del cuerpo dentro de la envolvente de la tapa
function ch_desfase()    = t_chapa + chasis_hol_tapa/2;

// --- desarrollo ---
// ala = trozo recto de la pared en el plano, del final del arco al canto
function ch_ala(alto_ext) = alto_ext - ch_sb();
function ch_blank_cuerpo() =
    [ch_cuerpo_ext().x + 2*ch_cuerpo_ext().z - 2*ch_bd(),
     ch_cuerpo_ext().y + 2*ch_cuerpo_ext().z - 2*ch_bd()];
function ch_off_cuerpo() = ch_ala(ch_cuerpo_ext().z) + ch_ba();

function ch_faldon_ext()  = t_chapa + chasis_pestana;
function ch_blank_tapa()  = [ch_tapa_ext().x + 2*ch_faldon_ext() - 2*ch_bd(),
                             ch_tapa_ext().y + 2*ch_faldon_ext() - 2*ch_bd()];
function ch_off_tapa()    = ch_ala(ch_faldon_ext()) + ch_ba();

// Un punto de una pared, a distancia d de la cara EXTERIOR desde la que se
// dobla, cae en el plano a esta coordenada. La linea de plegado va en el
// centro del arco (ala + BA/2) y desde ahi se mide d - SB de chapa recta.
function ch_desarrollo(d, ala) = ala + ch_ba()/2 - (d - ch_sb());

// Un punto del SUELO, en coordenadas interiores, cae aqui.
function ch_suelo(i, off) = off + i - radio_doblez;

// Reparto de los tornillos de la tapa a lo largo de un canto: orillas iguales,
// mismo criterio que fila_agujeros() de las planchas de acrilico.
function ch_tornillos(largo, n) = [for (i = [0:n-1]) largo*(i + 0.5)/n];
function ch_to220_x() = [for (i = [0 : chasis_to220_n - 1])
    chasis_to220_x + chasis_to220_paso*(i - (chasis_to220_n - 1)/2)];

// --- el desarrollo del cuerpo ------------------------------------------
// Bandeja de cuatro paredes desde UNA chapa. Las esquinas quedan abiertas por
// construccion (las cuatro esquinas del blank no existen) y ademas llevan
// alivio: la muesca se mete t_chapa dentro de la raiz del doblez, que es lo que
// evita que la chapa se rasgue justo ahi. Las cuatro juntas van SOLDADAS -- no
// remachadas: la caja tiene que ser continua electricamente para hacer de
// pantalla y de referencia de PE, y una fila de remaches no lo garantiza.
module chasis_cuerpo_2d() {
    b   = ch_blank_cuerpo();
    off = ch_off_cuerpo();
    rel = t_chapa;                      // alivio de esquina
    ext = ch_cuerpo_ext();
    // altura de la fila de tornillos, medida desde la cara exterior del suelo
    d_torn = t_chapa + chasis_int_z - chasis_tornillo_baja;
    difference() {
        square([b.x, b.y]);
        // esquinas: la cruz se forma quitandolas
        for (sx = [0, 1], sy = [0, 1])
            translate([sx*(b.x - off - rel), sy*(b.y - off - rel)])
                square([off + rel, off + rel]);
        // --- suelo ---
        translate([ch_suelo(chasis_toroide_x, off), ch_suelo(chasis_toroide_y, off)])
            circle(d = d_M6_paso + kerf);
        translate([ch_suelo(chasis_salida_x, off), ch_suelo(chasis_salida_y, off)])
            hull() for (dx = [0, chasis_salida_ancho - chasis_salida_fondo])
                translate([dx + chasis_salida_fondo/2, chasis_salida_fondo/2])
                    circle(d = chasis_salida_fondo + kerf);
        // --- pared larga y = 0: los tres TO-220 y nada mas ---
        for (x = ch_to220_x())
            translate([ch_suelo(x, off),
                       ch_desarrollo(chasis_to220_z + t_chapa, ch_ala(ext.z))])
                circle(d = d_M3_paso + kerf);
        // --- pared corta x = 0: el esparrago de PE ---
        translate([ch_desarrollo(chasis_pe_z + t_chapa, ch_ala(ext.z)),
                   ch_suelo(chasis_pe_y, off)])
            circle(d = d_M4_paso + kerf);
        // --- los tornillos de la tapa, en las cuatro paredes ---
        for (x = ch_tornillos(ext.x, chasis_tornillos_largo))
            for (s = [0, 1])
                translate([off + x - ch_sb(),
                           abs(s*b.y - ch_desarrollo(d_torn, ch_ala(ext.z)))])
                    circle(d = d_M3_paso + kerf);
        for (y = ch_tornillos(ext.y, chasis_tornillos_corto))
            for (s = [0, 1])
                translate([abs(s*b.x - ch_desarrollo(d_torn, ch_ala(ext.z))),
                           off + y - ch_sb()])
                    circle(d = d_M3_paso + kerf);
        // --- los cuatro M4 del suelo a la tabla (2026-08-29, noche) ---
        // El chasis apoya en la tabla y se atornilla a ella desde abajo, a
        // tuerca remachable en el suelo. Fueron 2 M5 de pared "a la ranura
        // interior de base trasera", un 2020 muerto el 27-08 que el modelo
        // siguio dibujando dos dias. Lo comprueba guarda_chasis().
        for (q = chasis_tornillos_int())
            translate([ch_suelo(q.x, off), ch_suelo(q.y, off)])
                circle(d = d_M4_paso + kerf);
    }
}

// --- el desarrollo de la tapa ------------------------------------------
// El faldon va por FUERA de la pared del cuerpo, no por dentro: asi la junta
// solapa hacia abajo y la linea de union no es un camino recto hacia adentro.
module chasis_tapa_2d() {
    b   = ch_blank_tapa();
    off = ch_off_tapa();
    rel = t_chapa;
    ext = ch_cuerpo_ext();
    // el tornillo esta a esta distancia por debajo de la cara de arriba
    d_torn = ch_alto() - (t_chapa + chasis_int_z - chasis_tornillo_baja);
    difference() {
        square([b.x, b.y]);
        for (sx = [0, 1], sy = [0, 1])
            translate([sx*(b.x - off - rel), sy*(b.y - off - rel)])
                square([off + rel, off + rel]);
        // Los del faldon casan con los del cuerpo: misma funcion, corridos por
        // el desfase de la tapa sobre el cuerpo. Escribirlos dos veces es
        // garantizar que se desincronicen el dia que cambie el reparto.
        for (x = ch_tornillos(ext.x, chasis_tornillos_largo))
            for (s = [0, 1])
                translate([off + x + ch_desfase() - ch_sb(),
                           abs(s*b.y - ch_desarrollo(d_torn, ch_ala(ch_faldon_ext())))])
                    circle(d = d_M3_paso + kerf);
        for (y = ch_tornillos(ext.y, chasis_tornillos_corto))
            for (s = [0, 1])
                translate([abs(s*b.x - ch_desarrollo(d_torn, ch_ala(ch_faldon_ext()))),
                           off + y + ch_desfase() - ch_sb()])
                    circle(d = d_M3_paso + kerf);
    }
}

// --- el refuerzo bajo el toroide (#106) --------------------------------
// Sin doblar: una chapa cuadrada del mismo material bajo el suelo, remachada o
// soldada, con el M6 pasando por las dos. No es contra el peso -- 1.2 kg sobre
// 1.5 mm de acero los aguanta de sobra -- es contra el MODO PROPIO: el suelo
// libre bajo un peso puntual es un tambor, y el excitador que tiene encima
// vibra a 100 Hz sin parar. Doblar el espesor local sube la frecuencia propia y
// baja la amplitud a la vez.
module chasis_refuerzo_2d() {
    l = chasis_refuerzo_lado;
    difference() {
        translate([-l/2, -l/2]) square([l, l]);
        circle(d = d_M6_paso + kerf);
        // remaches en las cuatro esquinas, retirados del canto
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx*(l/2 - 10), sy*(l/2 - 10)]) circle(d = d_M3_paso + kerf);
    }
}

// --- el chasis en 3D, para el censo de solapes y el render -------------
// Marco local: X a lo largo de la envolvente de la tapa, Y en el fondo, Z
// hacia arriba desde la cara de abajo del suelo.
module chasis_3d() {
    e = ch_cuerpo_ext();
    t = ch_tapa_ext();
    o = ch_desfase();
    translate([o, o, 0]) {
        cube([e.x, e.y, t_chapa]);                              // suelo
        translate([0, 0, t_chapa]) {
            cube([e.x, t_chapa, chasis_int_z]);                 // pared y=0
            translate([0, e.y - t_chapa, 0]) cube([e.x, t_chapa, chasis_int_z]);
            cube([t_chapa, e.y, chasis_int_z]);                 // pared x=0
            translate([e.x - t_chapa, 0, 0]) cube([t_chapa, e.y, chasis_int_z]);
        }
    }
    translate([0, 0, ch_alto() - t_chapa]) cube([t.x, t.y, t_chapa]);   // tapa
    translate([0, 0, ch_alto() - t_chapa - chasis_pestana]) {           // faldon
        cube([t.x, t_chapa, chasis_pestana]);
        translate([0, t.y - t_chapa, 0]) cube([t.x, t_chapa, chasis_pestana]);
        cube([t_chapa, t.y, chasis_pestana]);
        translate([t.x - t_chapa, 0, 0]) cube([t_chapa, t.y, chasis_pestana]);
    }
    // refuerzo, por debajo del suelo (por eso no come altura util)
    translate([o + chasis_toroide_x + t_chapa, o + chasis_toroide_y + t_chapa,
               -t_chapa])
        linear_extrude(t_chapa) chasis_refuerzo_2d();
    // el toroide, tumbado sobre su perno central
    %translate([o + chasis_toroide_x + t_chapa, o + chasis_toroide_y + t_chapa,
                t_chapa])
        cylinder(d = diam_transformador + 4, h = alto_transformador);
}

// Colocacion sobre la bandeja de base. La bandeja vive con su X local a lo
// ANCHO del case y crece hacia -Z del mundo (ver bandeja_base()); el chasis
// necesita ademas que su Z local suba, asi que el giro se escribe entero en
// vez de encadenar rotates y confiar en que salga.
// OJO: esto es el VANO ENTRE LARGUEROS, no el fondo de la plancha. Fueron el
// mismo numero hasta el 2026-08-21, cuando la bandeja paso a volar por delante
// del larguero delantero. Todo lo del chasis se mide contra ESTE, que es lo que
// de verdad lo encierra; el fondo de la plancha es este mas el vuelo.
function bandeja_base_fondo() = fondo() + 2*vuelo_zocalo;

// Lo que la plancha vuela por delante del larguero de base delantera. DERIVADO,
// no parametro: llega hasta donde MUERE LA CURVA de la esquina inferior
// delantera del costado, que es la misma regla que usa x_valle() para el pico.
// Un milimetro mas y la plancha asoma por delante del redondeo; uno menos y
// queda suelo sin cubrir. Con alto_frontal=19 la curva muere en x=9.49; el
// larguero arranca en 78.34 desde que lo coloca el chasis, o sea 68.85 de
// vuelo. Fueron 30.19 mientras el larguero se derivaba del riel de panel, y ese
// crecimiento se lo lleva entero la rejilla de entrada de aire, que vive aqui.
function bandeja_base_ancho() = ancho_total + 2*vuelo_zocalo;

// El chasis YA NO VA CENTRADO entre los largueros (2026-08-21). Se pega al
// TRASERO, a chasis_holgura_larguero, y el larguero delantero se pega a el: una
// sola cadena, x_tr -> chasis -> base delantera. Centrarlo no lo habia decidido
// nadie -- ch_pos() simplemente lo centraba -- y salia caro: sus 176.6 x 93 en
// medio del piso dejaban el fondo de modulo de la fila de abajo en 18.6 mm.
//
// Aqui se expresa en el marco LOCAL de la plancha, cuyo origen esta el vuelo por
// delante del larguero delantero. Como el larguero se planta a
// chasis_holgura_larguero del chasis, la cuenta se cierra sola y no necesita
// mirar donde acabo ce[0]: vuelo + rail + holgura.
// Cara delantera del chasis: cuelga del larguero TRASERO y de ahi hacia
// delante ya no hay nada. Estuvo escrito como vuelo + rail + holgura -- la
// cadena leida al reves desde el canto de la plancha -- y solo daba lo mismo
// porque `base delantera` estaba justo ahi. GEMELA de _x_chasis_frente().
// DESDE EL 2026-08-29 POR LA NOCHE SE ARRIMA AL PIE DEL TALON, que es lo que
// hay detras (12 mm mas atras que el canal del miembro bajo: 12 mm mas de
// fondo de modulo para la fila de abajo). GEMELA de _x_chasis_frente().
function x_chasis_frente() =
    talon_x_pie() - chasis_holgura_larguero - ch_tapa_ext().y;

// Los cuatro M4 del suelo del chasis a la tabla, en coordenadas INTERIORES
// del chasis (x a lo largo, y en el fondo). GEMELA de _chasis_tornillos().
function chasis_tornillos_int() =
    [for (sx = [0, 1], sy = [0, 1])
        [sx ? chasis_int_x - chasis_tornillo_x : chasis_tornillo_x,
         sy ? chasis_int_y - chasis_tornillo_y : chasis_tornillo_y]];
// Los mismos en coordenadas locales de bandeja_base_2d: la cadena de
// salida_cables_xy(). GEMELA de _chasis_tornillos_tabla().
function chasis_tornillos_tabla() =
    let (pc = ch_pos(), d = ch_desfase() + t_chapa)
    [for (q = chasis_tornillos_int()) [pc.x + d + q.x, pc.y + d + q.y]];

// En coordenadas LOCALES de la tabla, cuyo origen esta vuelo_zocalo por delante
// y por fuera del cuerpo. O sea: x local = vuelo_zocalo + z del mundo, la misma
// cadena con que bandeja_base_2d() coloca sus dos filas de tornillo.
//
// LA CARA INTERIOR ES t_anillo desde el 2026-08-28, no t_cheek + t_costilla.
// guarda_chasis() mide este mismo hueco con el origen EN la cara interior
// (`pos_x = au - chasis_margen_bandeja - tapa_x`, 192.02 mm) y un span de
// ancho_util, asi que el termino de aqui es el unico sitio donde el plano se
// nombra: con los 9.5 viejos el agujero de salida de cables se dibujaba 4.5 mm
// corrido respecto a lo que el presupuesto verifica, y no lo cazaba nadie --
// agujeros_donde_toca() relee las filas de tornillo de la tabla, no la ranura.
function ch_pos() = [vuelo_zocalo + t_anillo
                       + ancho_util - chasis_margen_bandeja - ch_tapa_ext().x,
                     x_chasis_frente() + vuelo_zocalo];

// Esquina de la salida de cables del chasis, en coordenadas locales de
// bandeja_base_2d(). Una sola definicion: la consume el agujero del acrilico
// y la comprueba el budget.
function salida_cables_xy() =
    let (pc = ch_pos(), d = ch_desfase() + t_chapa)
    [pc.x + d + chasis_salida_x - salida_holgura,
     pc.y + d + chasis_salida_y - salida_holgura];

// EL TERMINO EN Z ESPEJABA EL CHASIS, y se arregla el 2026-08-28. Decia
// `ancho_total - t_cheek` con un -1 delante, y eso hacia dos cosas malas a la
// vez: dejaba la caja en z = 10.50..349.10 -- casi 200 mm del sitio, o sea al
// OTRO EXTREMO del case -- y, por el signo, la dibujaba como imagen especular
// (el 3x3 tenia determinante -1). Un chasis de chapa no se puede fabricar
// espejado: al voltearlo, la boca de salida y la entrada IEC cambian de pared.
//
// QUIEN MANDA SON LAS DOS GEMELAS QUE YA SE PONIAN DE ACUERDO, y son dos contra
// una: ch_pos() -- lo que guarda_chasis() verifica, pos_x = ancho_util -
// chasis_margen_bandeja - tapa_x desde la cara interior -- y salida_cables_xy(),
// que saca del MISMO ch_pos() la ranura de cables que se recorta en
// bandeja_base_2d, sin espejar. Las dos dicen z = 206.02..544.62, contra el
// canto de arriba del case, que es ademas donde vive la ventana de la IEC en la
// trasera. Con el espejo puesto, la boca del chasis y su agujero en la tabla
// quedaban en lados opuestos del aparato.
//
// La conversion es la de siempre en este fichero: x local de la tabla =
// vuelo_zocalo + z del mundo (la misma con que bandeja_base_2d() coloca sus dos
// filas de tornillo), asi que el termino es p.x - vuelo_zocalo y el signo, +1.
// Con eso el 3x3 vuelve a ser un giro propio.
//
// SIGUE SIN ADJUDICARLO NINGUNA PUERTA: el chasis no es un cuerpo de
// _cajas_solidas(), o sea que solapes() no lo mira. Meterlo ahi esta aplazado a
// proposito -- puede chocar con el miembro del que cuelga, y eso es otra
// decision.
module chasis() {
    p  = ch_pos();
    multmatrix([[0, 1, 0, -vuelo_zocalo + p.y],
                [0, 0, 1, chasis_pie],
                [1, 0, 0, p.x - vuelo_zocalo],
                [0, 0, 0, 1]])
        chasis_3d();
}

// --- vistas de render del chasis (no salen en ningun DXF) ---------------
// El color() y estas dos PART solo existen para mirar. Van aqui y no en un
// fichero aparte por lo mismo que el resto del chasis: una vista que no se
// regenera con el modelo miente en cuanto alguien mueve un parametro, y esta
// es justo la pieza cuyo interior no se puede comprobar de otra forma.

// TO-220 de pie contra la pared, con el tab atornillado. No es un modelo del
// encapsulado -- es su estorbo: cuerpo, tab y la altura a la que cae su
// taladro. Sirve para ver si la fila choca con algo, no para fabricar.
module to220_estorbo() {
    color([0.15, 0.15, 0.17]) translate([-5.08, 0, -12.4]) cube([10.16, 4.6, 16]);
    color([0.7, 0.7, 0.72]) translate([-5.08, -0.5, -12.4]) cube([10.16, 0.5, 19]);
}

// La PCB no existe todavia (Fase C). Esto es su HUECO RESERVADO, que es un
// dato distinto y hay que leerlo como tal: 200 x 150 flotando sobre sus
// separadores, sin un solo componente encima porque no hay ninguno decidido.
module pcb_reservada() {
    color([0.05, 0.35, 0.15])
        translate([chasis_pcb_x, chasis_pcb_y, t_chapa + chasis_pcb_standoff])
            cube([chasis_pcb_ancho, chasis_pcb_fondo, 1.6]);
}

module chasis_contenido() {
    pcb_reservada();
    color([0.55, 0.35, 0.15])                       // toroide
        translate([chasis_toroide_x, chasis_toroide_y, t_chapa])
            difference() {
                cylinder(d = diam_transformador, h = alto_transformador);
                translate([0, 0, -1]) cylinder(d = 30, h = alto_transformador + 2);
            }
    color([0.8, 0.8, 0.82])                          // perno M6 x 60
        translate([chasis_toroide_x, chasis_toroide_y, -8])
            cylinder(d = 6, h = alto_transformador + 16);
    for (x = ch_to220_x())                           // la fila que disipa
        translate([x, t_chapa, t_chapa + chasis_to220_z]) to220_estorbo();
}

// Vista abierta: el cuerpo sin tapa y lo que lleva dentro.
module chasis_abierto() {
    e = ch_cuerpo_ext();
    color([0.62, 0.63, 0.66]) {
        cube([e.x, e.y, t_chapa]);
        translate([0, 0, t_chapa]) {
            cube([e.x, t_chapa, chasis_int_z]);
            translate([0, e.y - t_chapa, 0]) cube([e.x, t_chapa, chasis_int_z]);
            cube([t_chapa, e.y, chasis_int_z]);
            translate([e.x - t_chapa, 0, 0]) cube([t_chapa, e.y, chasis_int_z]);
        }
    }
    color([0.5, 0.51, 0.54])                         // el refuerzo, por debajo
        translate([chasis_toroide_x + t_chapa, chasis_toroide_y + t_chapa, -t_chapa])
            linear_extrude(t_chapa) chasis_refuerzo_2d();
    translate([t_chapa, t_chapa, 0]) chasis_contenido();
}

if (PART == "costado")             costado();
else if (PART == "costado_2d")     costado_2d();
else if (PART == "costilla_2d")    costilla_2d();
// El dorso del anillo va en su propio fichero por lo mismo que el cajeado
// KONDOR: un DXF 2D no sabe decir "a 11 mm de profundidad". Sin el, el anillo
// vuelve del taller SIN REBAJE y el acrilico no entra.
else if (PART == "costilla_dorso_2d") costilla_dorso_2d();
else if (PART == "cupon_anillo_2d") seccion_anillo_2d();
else if (PART == "marco_ventana_2d")     marco_ventana_2d();
else if (PART == "talon_2d")             talon_2d();
else if (PART == "nariz_2d")             nariz_2d();
else if (PART == "assembly")           assembly();
else if (PART == "assembly_acrilico")  assembly_acrilico();
else if (PART == "assembly_aluminio")  assembly_aluminio();
else if (PART == "assembly_madera")    assembly_madera();
else if (PART == "assembly_esqueleto") assembly_esqueleto();
else if (PART == "assembly_acero")     assembly_acero();
else if (PART == "bandeja_base_2d")      bandeja_base_2d();
else if (PART == "tapa_valle_2d")        tapa_valle_2d();
else if (PART == "miembro_alto_2d")      miembro_alto_2d();
else if (PART == "piel_trasera_2d")      piel_trasera_2d();
// El relieve KONDOR en su propio fichero, y no es un extra: es la UNICA forma
// de que llegue al taller. No se recorta en piel_trasera_2d (es ciego), asi que
// el DXF de la trasera SIN esto es media pieza -- el mismo caso del chasis, que
// necesita su plano de plegado porque el corte no dice de donde doblar. Va con
// su cota de profundidad (kondor_prof) escrita al lado, en el pliego.
else if (PART == "kondor_cajeado_2d")    kondor_2d();
else if (PART == "chasis_cuerpo_2d")     chasis_cuerpo_2d();
else if (PART == "chasis_tapa_2d")       chasis_tapa_2d();
else if (PART == "chasis_refuerzo_2d")   chasis_refuerzo_2d();
else if (PART == "chasis")               chasis();
else if (PART == "chasis_abierto")       chasis_abierto();
else if (PART == "chasis_cerrado")       chasis_3d();
else if (PART == "lienzo_2d")            lienzo_2d();
else if (PART == "bom")                  bom();
else assert(false, str("PART desconocido: ", PART));

// costado_2d vive en el plano XY del perfil (X = fondo, Y = altura);
// costado() lo extruye en +Z por t_cheek, o sea Z pasa a ser el ancho.
//
// EL ACRILICO VA DENTRO DE LA VENTANA desde el 2026-08-28, no apilado detras.
// Su cara exterior queda rehundido_acrilico por detras de la cara del anillo
// -- eso es lo que se ve desde fuera: metal, y el PMMA hundido 3 mm -- y su
// cara interior a rehundido + t_cheek, o sea todavia dentro del rebaje, que es
// mas hondo. Entre el labio y el PMMA va la junta de asiento; aqui no se
// dibuja (1 mm de EPDM no cambia ninguna colision) y la mide guarda_rebaje().
//
// El apilado que esto sustituye era t_costilla + t_junta + t_cheek desde
// fuera, con un casquillo cruzando las tres capas.
module costados() {
    translate([0, 0, rehundido_acrilico]) costado();
    translate([0, 0, ancho_total - rehundido_acrilico - t_cheek]) costado();
}

// Los dos anillos son las capas exteriores: ocupan z=0..t_anillo y
// z=ancho_total-t_anillo..ancho_total, y entre sus caras interiores cruza todo
// lo demas. Ya no hay alas que doblar, pero el espejo se queda: el rebaje y el
// chaflan NO son simetricos en Z -- la cara vista mira hacia fuera.
module costillas() {
    costilla();
    translate([0, 0, ancho_total])
        mirror([0, 0, 1]) costilla();
}

// railes de panel (centros_rail(), 4) van a ras de su cara: giro extra
// sobre el propio eje largo (R3, ronda de revision) para que la cara del
// rail quede paralela al panel en vez de un canto en diagonal. Centros
// intactos (agujeros M5 del costado y todos los DXF, sin cambios).
// rotate([0,0,-angulo]) alinea el lado +Y local del rail con el vector de
// cara d=(sin,cos) — verificado con la matriz Rz(-angulo) a mano.
// LOS RIELES NO CRUZAN ancho_util ENTERO desde el 2026-08-28: en cada punta
// hay una placa de anclaje de t_placa entre el riel y la cara interior del
// anillo, asi que miden ancho_util - 2*t_placa. Es el largo de catalogo que se
// compro (528.32 + hol_riel), no un corte.
module rails() {
    cr = centros_rail();   // [inf frente, inf valle, sup valle, sup remate]
    angs = [angulo_inferior, angulo_inferior,
            angulo_superior, angulo_superior];
    for (i = [0 : len(cr) - 1])
        translate([cr[i].x, cr[i].y, ancho_total/2])
            rotate([0, 0, -angs[i]])
                rotate([90, 0, 0])
                    rail_er(ancho_util - 2*t_placa);
    // Fila horizontal 1U: mismo largo y la misma fijacion M4 de punta que los
    // 3U. El giro de 90 deja rail_er_alto sobre X y rail_er_fondo hacia -Y.
    for (c = centros_rail_1u())
        translate([c.x, c.y, ancho_total/2])
            rotate([0, 0, -90])
                rotate([90, 0, 0])
                    rail_er(ancho_util - 2*t_placa);
}

// --- planchas del cuerpo colocadas en 3D --------------------------------
// Cada *_2d() vive en su plano local (u = ancho, v = fondo/alto local);
// rotate([0,90,0]) rotate([90,0,0]) hace el giro compuesto u->Z, v->X,
// grosor->Y (verificado a mano con la matriz de rotacion: local (x,y,z)
// -> mundo (y,-z,-x)). Las bandejas apoyan encima de sus railes (grosor
// crece hacia +Y desde el lomo del rail); el zocalo y las pieles son
// paredes verticales, volados sobre standoffs (grosor crece hacia FUERA
// del cuerpo en X — R1, ronda de revision: antes crecia hacia dentro y
// el canto interior invadia el rail limite; ver piel_inferior_2d() etc.)
// x0 = canto delantero a ras del rail base-delantera, el mismo que usa
// bandeja_base_2d() para derivar su fondo (ronda final: antes iba en
// x=rail, que no es donde esta el rail).
module bandeja_base() {
    // LA TABLA, y desde el 2026-08-27 vive DEBAJO del marco: de y = -t_base a
    // y = 0. Su cara de arriba ES el suelo interior y su canto sobresale
    // vuelo_zocalo por los cuatro lados. Es la misma pieza que el "zocalo" de
    // la spec 9, que hasta hoy eran dos.
    translate([-vuelo_zocalo, 0, ancho_total + vuelo_zocalo])
        rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(t_base) bandeja_base_2d();
}

// tope de bandeja a ras de P3.y (canto SUPERIOR, no inferior — la cota la pone
// hoy bahia_y1(), que es quien heredo el valle de la lista de los 2020);
// canto delantero a ras del rail reubicado.

// EMPOTRADA (2026-08-21): cara exterior EN el plano trasero, x = fondo(), y
// crece hacia dentro. Estuvo volada sobre separadores, con la cara exterior 10
// mm por detras del canto. Apoya en la cara de los DOS largueros traseros, que
// por eso viven los dos en x_tr = fondo - r - t_piel.
//
// Y desde el 2026-08-22 baja hasta el PLANO DEL SUELO (y=0) en vez de quedarse
// en y=3: empotrada por los cuatro costados y no por tres. Ver el comentario
// largo en piel_trasera_2d().
// El cajeado de la sierra se vacia AQUI y no en el 2D. Ojo con el sentido: la
// extrusion arranca en el plano trasero (P[6].x) y crece hacia DENTRO del case
// por el rotate([0,-90,0]), asi que z local 0 es la cara EXTERIOR. Vaciar de 0
// a kondor_prof deja el cajeado por fuera, que es donde se ve sin luz
// interior. Para voltearlo a la cara de dentro seria translate a
// t_piel - kondor_prof.
// EMPOTRADA ENTRE LOS DOS ANILLOS, no entre los dos acrilicos: desde el
// 2026-08-28 arranca en t_anillo + hol_piel y no en t_cheek + hol_piel. Con el
// anillo por fuera la cara interior del case esta en t_anillo, y arrancar en
// t_cheek dejaba la plancha DESCENTRADA -- 8.15 por un lado y 20.15 por el
// otro sobre el mismo ancho_util --, que es una plancha torcida en el render y
// una posicion que no coincide con la caja gemela de _cajas_solidas().
module piel_trasera() {
    P = pts_perfil();
    // REHUNDIDA t_costilla desde el 2026-08-29 (#234): lo que asoma al plano
    // trasero es el marco, no el acrilico.
    // El 2D ya viene en y del mundo (arranca en t_costilla, sobre el pie del
    // talon), asi que aqui no se le suma nada en y.
    // EN SU BOLSILLO desde la trasera capturada: la cara vista en trasera_x1()
    // (rehundida labio + junta), las puntas en trasera_z0().
    c = chaflan_trasera_bajo();
    difference() {
        translate([trasera_x1(), 0, trasera_z0()])
            rotate([0, -90, 0])
                difference() {
                    linear_extrude(t_piel) piel_trasera_2d();
                    translate([0, 0, -0.1])
                        linear_extrude(kondor_prof + 0.1) kondor_2d(espejo = true);
                }
        // el chaflan de la arista de abajo-fuera, por todo el largo
        translate([0, 0, trasera_z0() - 1])
            linear_extrude(trasera_au() + 2)
                polygon([[trasera_x1() + 0.01, trasera_y0() - 0.01],
                         [trasera_x1() + 0.01, trasera_y0() + c],
                         [trasera_x1() - c, trasera_y0() - 0.01]]);
    }
}

// A ras del plano del valle, igual que la bandeja de entrepiso: el grosor crece
// hacia -Y desde el origen, asi que el origen va en P[3].y.
module tapa_valle() {
    P = pts_perfil();
    xv = x_valle();
    // La cara interior del anillo, no la del acrilico: desde el 2026-08-28
    // el hueco entre costillas es ancho_util y arranca en t_anillo. Con
    // t_cheek la banda quedaba 6 mm corrida hacia un lado y no coincidia
    // con su caja gemela de _cajas_solidas(), que ya mide t_anillo..
    translate([xv[0], P[3].y, ancho_total - t_anillo - t_placa])
        rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(t_valle) tapa_valle_2d();
}

// SIN LA TAPA DEL VALLE desde el 2026-08-25: es de ALUMINIO (t_valle) y se
// fue a assembly_aluminio(). Si vuelve aqui, el render la pinta translucida y
// naranja y ensena una pieza que no existe -- que es peor que no renderizarla.
module planchas_acrilico() {
    piel_trasera();
}

// panel de modulo (PCB de aluminio, t_panel) sobre una cara del perfil
// A->B: cara externa a ras del perfil, engrosa hacia dentro segun la
// misma normal que centros_rail() ([d.y,-d.x]). s0 = donde ARRANCA el panel
// sobre la cara; el panel ya no tiene por que cubrirla entera.
module panel_cara(A, B, s0, largo) {
    d = (B - A) / norm(B - A);
    // ARRANCA DONDE ARRANCA SU RIEL, no donde acaba el anillo. Un panel de
    // modulo se atornilla a la pletina roscada del Z-Rail, asi que la fila no
    // puede ser mas larga que el riel: mide ancho_util - 2*t_placa igual que
    // el, desde t_anillo + t_placa. Cruzo ancho_util entero hasta el
    // 2026-08-28 y esos 6 mm de mas por punta se metian DENTRO de la placa de
    // anclaje -- que solapes() no ve, porque los paneles no entran en su lista
    // (un rectangulo largo y fino en diagonal no se deja meter en una AABB).
    // Lo canto el barrido de guarda_tapa(), que si los gira.
    translate([A.x, A.y, t_anillo + t_placa])
        rotate([0, 0, atan2(d.y, d.x)])
            translate([s0, -t_panel, 0])
                cube([largo, t_panel, ancho_util - 2*t_placa]);
}

// NINGUN panel cubre su cara: los dos son PCB 3U de 128.5 mm con los taladros
// a inset_er = 3 de cada canto, colgados de railes que estan a su inset de la
// punta. Cada uno arranca por tanto en s0 = inset - inset_er y sobra bisel de
// acrilico a los dos lados (23.5 y 12 abajo, 21.5 y 20 arriba). Ese bisel es
// parte del alzado, no un descuadre -- si el render pintara el panel cubriendo
// la cara entera estaria mintiendo sobre lo que se va a ver.
module paneles() {
    P = pts_perfil();
    panel_cara(P[1], P[2], inset_inf_frente - inset_er, alto_panel_inf);
    panel_cara(P[3], P[4], inset_sup_valle  - inset_er, alto_panel_sup);
    // Y LA FILA 1U (2026-08-29): con la bahia muerta, sin este panel el render
    // ensena el interior del case por el valle -- la trasera por dentro y su
    // rejilla --, que es exactamente lo que los tiles tapan. Un panel de
    // alto_panel_1u a ras del plano del valle, de canto a canto de sus dos
    // rieles (taladros a inset_er de cada canto), como los dos de 3U.
    c = centros_rail_1u()[0];
    translate([c.x - inset_er, P[3].y - t_panel, t_anillo + t_placa])
        cube([alto_panel_1u, t_panel, ancho_util - 2*t_placa]);
}

// remate_sup()/remate_sup_2d() MURIERON el 2026-08-28 (fix round 1, Tarea 5):
// eran la tapa de remate en acrilico, apoyada de canto en el riel. Desde el
// 2026-08-27 la meseta del techo (marco_sup) es el ALA del miembro trasero
// alto, doblada de su propio blank -- no una plancha aparte -- y estas dos
// funciones se quedaron sin llamador (grep confirmo cero callers antes de
// borrarlas: ni aqui, ni en check_dxf.py, ni en export.ps1 $piezas). El BOM
// y los papeles seguian vendiendo una pieza que no existia; corregido en la
// misma tanda.

// Paticas torneadas bajo los costados. En X caen sobre los dos rieles de
// base, que es donde esta la estructura; en Z su cara exterior queda a ras
// del canto del case (centro a d_pie/2) para que la carga del costado baje
// recta al pie y no de canto.
module paticas() {
    // El pie delantero ya no cae sobre un larguero: la base delantera se retiro
    // 39 mm hacia dentro para librar el riel del panel, y un pie ahi dejaria todo
    // el frente en voladizo justo donde se aprietan los mandos de abajo. Va donde
    // acaba el redondeo de la punta, que es lo mas adelante que se puede apoyar
    // con el disco entero sobre acrilico. El trasero sigue sobre su larguero.
    for (x = [alto_frontal/2 + d_pie/2, centro_talon().x])
        for (z = [d_pie/2, ancho_total - d_pie/2])
            translate([x, -t_base, z])
                rotate([90, 0, 0])
                    cylinder(h = alto_pie, d = d_pie);
}

module assembly() {
    costados();
    rails();
    costillas();
    miembros();
    planchas_acrilico();
    tapa_valle();
    chasis();
    paticas();
    %paneles();                        // paneles de modulo: solo referencia
}

module assembly_acrilico() {           // STL separado para Blender (Task 8)
    costados();
    planchas_acrilico();
}

// LA TABLA, en su propio STL. Sale de assembly_acrilico() el 2026-08-27 porque
// dejo de ser acrilico: es madera, y en el render tiene que verse como madera.
// Meterla en el ensamblado naranja la pintaba de naranja translucido, que es
// justo el tipo de render que miente sobre una decision de material.
module assembly_madera() {
    bandeja_base();
    // LAS CUATRO PATICAS (Tarea 6). Van aqui, con la tabla, y no en
    // assembly_aluminio(): se atornillan A ELLA (BOM: "se atornilla A LA
    // TABLA, no al acrilico"), asi que este STL es el que las tiene que
    // ensenar para que se vean en su sitio. SON DE GOMA y Blender pinta este
    // STL entero de nogal -- una patica de goma con nogal encima es un
    // desvio de color, no de geometria, y se acepta: separar un cuarto STL
    // solo para cuatro cilindros de 20x10 no paga su peso. paticas() TAMBIEN
    // sigue en assembly() (la vista de conjunto sin separar materiales) --
    // esto la ANADE aqui, no la muda.
    paticas();
}

// LA BAHIA DE ABAJO, para mirarla por dentro. Es el unico sitio del case cuyo
// interior es una decision y no una consecuencia -- la tabla, el chasis del PSU
// encima y los tres miembros de chapa -- y no se ve en ninguna de las dos vistas
// del conjunto: los paneles y la tapa del valle lo tapan entero.
//
// Son DOS ensamblados y no uno porque son DOS MATERIALES: el esqueleto va en
// aluminio y el chasis en acero, y pintarlos igual es perder justo lo que la
// vista existe para enseñar.
module assembly_esqueleto() {          // aluminio, SIN paneles ni tapa
    rails();
    costillas();
    miembros();
}

module assembly_acero() {              // el chasis del PSU, cerrado
    chasis();
}

// OJO CON EL WARNING de 2-manifold que suelta este export: es INHERENTE y no un
// defecto que arreglar. Aqui hay cuerpos que se tocan A PROPOSITO -- el dorso
// del panel apoya EXACTAMENTE en la cara del riel (esa distancia ES t_panel) y
// roza tangente el nudillo de la bisagra --, y una union de solidos que comparten
// cara no es un 2-manifold limpio. Que salga o no salga el aviso depende de por
// que lado caiga el redondeo de coma flotante, asi que aparece y desaparece al
// mover el case (aparecio al bajar el suelo 17 mm, 2026-08-17). No afecta a
// ningun DXF -- esto es el STL de referencia para Blender, y Blender lo carga.
module assembly_aluminio() {           // idem, Z-Rails + miembros + paneles solidos
    rails();
    paneles();
    // LOS DOS MARCOS DE LA VENTANA (2026-08-29, noche): una pletina por
    // costado que ata los seis rieles al case y retiene el acrilico hacia
    // dentro por los siete tramos. Sustituyen a las seis placas de anclaje,
    // los cuatro clips y las dos escuadras. Van por la cara INTERIOR: en el
    // render se ven asomar 6 mm por el canto de la ventana -- el marco de
    // cada fila, y a traves del acrilico una sombra uniforme --, y nada mas.
    // Si algo mas se viera por fuera, estaria mal puesto.
    marcos_ventana();
    // LA NARIZ. Entra el 2026-08-29 y se ve entera: es lo que cierra el
    // frente por delante y por abajo, con la fila de abajo apoyada encima.
    nariz();
    // LAS DOS COSTILLAS. Entran aqui el 2026-08-27, y llegaban tarde: son la
    // pieza PORTANTE del case desde el 26 y el render llevaba un dia
    // ensenando un aparato sostenido por su propia piel.
    costillas();
    miembros();
    // La tapa del valle. Entra aqui el 2026-08-25 al dejar de ser acrilico de 5
    // y pasar a aluminio de 3, y su sitio es este por la misma razon por la que
    // el cambio no rompe el lenguaje visual: queda entre los paneles de las dos
    // filas, que ya son PCB de aluminio.
    tapa_valle();
}

// --- lienzo de corte: 5 piezas (2 costados + 3 planchas) en rejilla -----
// Separacion 8 mm; marco de 1000x600 es solo referencia visual de plancha,
// las piezas pueden desbordarlo (nesting real lo hace el servicio de corte).
module lienzo_2d() {
    sep = 8;
    P = pts_perfil();
    prof = max([for (pp = P) pp.x]);   // ancho real de costado_2d (fondo)
    alto = max([for (pp = P) pp.y]);   // alto real de costado_2d
    au  = ancho_util;
    aup = ancho_util - 2*hol_piel;
    // fila 1: los 2 costados
    costado_2d();
    translate([prof + sep, 0]) costado_2d();
    // fila 2: las 2 planchas de acrilico. Fueron 6 hasta el 2026-08-21 (murio
    // la bandeja de entrepiso y las dos pieles se fundieron en una), y 4 hasta
    // el 2026-08-25, cuando la tapa del valle paso a ALUMINIO.
    //
    // ESTE LIENZO ES DE ACRILICO Y SOLO DE ACRILICO, y es el mismo motivo por
    // el que nunca llevo las tres piezas de acero: van a otro taller, y
    // nestear junto lo que no se manda junto es mentir sobre el pedido.
    //
    // La cadena se renumero al quitarlas: antes cada x colgaba de la anterior
    // (x3 = x2 + ...) y al borrar las lineas de las piezas muertas se fueron
    // con ellas las variables intermedias. OpenSCAD no falla con eso -- trata
    // la variable ausente como undef y coloca la pieza en NaN --, y como el
    // lienzo es PREVIEW y no lo relee check_dxf, ninguna puerta lo hubiera
    // cazado. Por eso va encadenado sin huecos y no por indices sueltos.
    y2 = alto + sep;
    x1 = 0;               translate([x1, y2]) bandeja_base_2d();
    x2 = x1 + au + sep;   translate([x2, y2]) piel_trasera_2d();
    %square([1000, 600]);
}

module bom() {
    au = ancho_util;
    echo(str("BOM: COSTILLA x2 -- anillo de PLETINA de aluminio FRESADA, una",
             " pieza por lado (sin soldar, sin doblar). Espesor ", t_anillo,
             ", cara vista ", cara_anillo, ", rebaje de ", rebaje_anillo,
             " x ", t_anillo - rehundido_acrilico, " por detras donde",
             " asienta el costado, chaflan ", chaflan_anillo,
             " x 45 grados en las dos aristas de la cara vista. P1 y P4 a",
             " radio_chapa (", radio_chapa, ", dobla chapa a 90 encima); P0 y P6",
             " a chaflan de ", chaflan_nariz, " (la nariz y el talon), y P5",
             remate_trasero_chaflan ? " tambien (el techo)" : " a radio_chapa",
             ". Y EN EL TRAMO TRASERO, POR LA CARA INTERIOR, EL BOLSILLO DE LA",
             " TRASERA: ", t_anillo - rehundido_acrilico, " x ", rebaje_anillo,
             " cerrado por los dos extremos (y = ", bolsillo_y_bot(), " a ",
             bolsillo_y_fin(), "), con el rebaje del costado retirado a ",
             rebaje_costado_trasero(), " ahi (pared de ", pared_rebaje_trasera,
             " entre los dos)."));
    echo(str("     NINGUN TORNILLO ATRAVIESA LA CARA VISTA: ",
             len(centros_rosca_ciega()), " roscas ciegas M4 en la cara",
             " interior (taladros_anillo, broca ", d_M4_rosca,
             ") -- 12 del marco de la ventana (10 en las filas, 2 en el suelo)",
             " y 2 de la brida del miembro",
             " alto; eran 16 con clips y miembro bajo -- + 3 M5 por anillo",
             " en el CANTO inferior para la tabla (ver esa linea, no salen",
             " en el mismo DXF). CERO casquillos, CERO junta de 4 mm."));
    echo(str("     El costado asienta en el rebaje sobre una junta de EPDM",
             " de ", t_junta_asiento,
             " mm (ver linea propia), nunca aluminio contra acrilico.",
             " Hasta el 2026-08-28 era chapa plegada con casquillo de",
             " aluminio y junta de EPDM de 4 mm entre costilla y acrilico;",
             " ese dia Samuel vio el render y lo rechazo: 'parece que el",
             " acrilico estuviera envuelto en un sandwich de aluminio'."));
    echo("     Anodizado satinado tras mecanizar, con el punto de bonding");
    echo("     de PE ENMASCARADO antes de anodizar -- uno por anillo, en la");
    echo("     cara interior.");
    echo(str("     Aleacion recomendada, no obligatoria: 5754 H22 pasa a 130",
             " MPa (guarda_anillo, I=3714 mm4, 214 mm2); 6082-T6 o 5083 se",
             " piden por planitud tras el vaciado, no por calculo. ~0.58 kg",
             " por costilla."));
    echo(str("BOM: MARCO DE LA VENTANA x2 -- pletina de aluminio de ", t_placa,
             " cortada a laser con el contorno de la ventana del anillo,",
             " corrida por los siete tramos, ", marco_fondo, " hacia dentro",
             " desde la silueta. Una por costado, ESPEJADAS: el mismo",
             " contorno se corta x2 y se cajea por caras opuestas."));
    echo("     ES LO QUE ATA LOS SEIS RIELES AL CASE Y LO QUE RETIENE EL");
    echo("     ACRILICO HACIA DENTRO por todo el perimetro. Sustituye desde el");
    echo("     2026-08-29 por la noche a las tres placas de anclaje, los dos");
    echo("     clips y la escuadra de la trasera de cada costado: 'la placa es");
    echo("     el marco de la fila' (Samuel, 28-08) llevado hasta el final.");
    echo(str("     Sobre las tres filas es EXACTAMENTE la placa de ayer: canto",
             " visto de ", t_placa, " a la silueta, cajeado de ", d_cajeado_riel,
             " x ", prof_cajeado_riel, " por el lado del anillo en cada uno de",
             " sus 6 pasos de riel (cuatro 3U y dos 1U), dos roscas ciegas M4",
             " por riel 3U, dos sobre el primer 1U y dos en la pata del suelo",
             " (el trabajo de los clips). En el frente, el suelo, la",
             " meseta y la trasera el canto exterior va RETIRADO -- ",
             retiro_marco(), " bajo cada chapa (nariz, pies, meseta, retorno) y ",
             retiro_marco_trasera(), " en la trasera, que es t_anillo + 0.5:",
             " la pata apoya sobre la pared entre el bolsillo de la trasera y",
             " el del costado --, y pisa ", marco_fondo - cara_anillo,
             " de acrilico volado por seis tramos y ",
             marco_fondo_trasera - cara_anillo, " por la trasera: a traves del",
             " PMMA se lee una sombra uniforme de 6, no retazos."));
    echo("     Lleva ademas la rosca M3 pasante de la pestana de la banda del");
    echo("     valle, dos pasos M4 para la brida del miembro alto y UNA MUESCA");
    echo("     en la esquina trasera-alta, abierta al canto exterior, sobre la");
    echo("     huella de esa brida (que apoya en la cara del anillo, fuera del");
    echo("     barrido del panel de arriba: se probo subirla encima del marco");
    echo("     y la tapa pasaba de abrir 121.5 grados a 52).");
    echo("     DXF de corte: marco_ventana_2d, UNO para las dos. El cajeado no");
    echo("     se dibuja: un DXF 2D no sabe decir 'a 2.5 de profundidad' y va");
    echo("     como NOTA DE MECANIZADO en el pliego, tres por una cara y tres");
    echo("     por la otra (PLIEGO 6).");
    echo("     ORDEN DE MONTAJE OBLIGADO: el costado asentado en el rebaje,");
    echo("     DESPUES los seis rieles al marco (la cabeza queda en el cajeado,");
    echo("     del lado que despues mira al anillo) y DESPUES el marco al");
    echo("     anillo, desde dentro, con sus diez M4. Al reves no se puede");
    echo("     apretar, y el costado no entra con el marco puesto.");
    echo(str("BOM: tornillo M4 boton x", 2*len(roscas_marco()), " -- el marco",
             " de la ventana al anillo, a rosca ciega en la franja de ",
             cara_anillo - rebaje_anillo, " (", len(roscas_marco()),
             " por costado). Eran los 20 'de placa al anillo' que el README",
             " llevaba sin itemizar."));
    echo(str("BOM: MIEMBRO ALTO x1 -- chapa de aluminio 6082-T6 de ", t_costilla,
             ", ", au, " de largo: una L cuya ala de arriba ES la MESETA del",
             " techo (", prof_sup, ", del pico al plano trasero, con su",
             " RETORNO de ", retorno_meseta, " en el pico) y cuya alma es la",
             " BANDA VISTA de ", banda_trasera, " que baja a ras del plano",
             " trasero. Dos BRIDAS de extremo dobladas de la banda, de ",
             brida_largo, " x ", brida_ancho, ", roscadas al anillo con dos",
             " M4 ciegos cada una."));
    echo("     Fue canal de 20 x 24 con un marco de la trasera atornillado");
    echo("     encima (2026-08-29 por la manana): la meseta moria 9.5 antes del");
    echo("     canto y dejaba una costura en el techo. Desde esa noche la banda");
    echo("     ES el alma y el techo es una chapa del pico al canto. Solo, sin");
    echo(str("     la trasera, cede ", 2, " mm con 20 kg en el centro de la meseta",
             " a 110 MPa (guarda_miembro_alto: es lo que puso la banda en ",
             banda_trasera, " y no en 20); atornillado a la trasera cada 100, decimas."));
    echo(str("BOM: TALON x1 -- la nariz de atras: la misma chapa 6082-T6 de ",
             t_costilla, ", ", entre_anillos(), " de largo, doblada sobre el",
             " chaflan de ", chaflan_nariz, " de P6: pie de ", talon_pie,
             " sobre la tabla (tres M4 avellanados desde dentro), chaflan a 45",
             " y labio vertical de ", talon_labio, " a ras del plano trasero,",
             " que tapa el canto de abajo de la trasera. ", talon_pestana_n,
             " PESTANAS lanzadas del pie, de ", talon_pestana_ancho, " x ",
             talon_pestana_alto, ", a ", talon_pestana_aire, " detras de la",
             " trasera: su tope hacia dentro, y estructura. Desarrollo ",
             entre_anillos(), " x ", talon_desarrollo(), ". Sin bridas ni",
             " rosca en el anillo."));
    echo(str("BOM: tornillo M4 avellanado x", len(nariz_m4_z()), " -- el pie del",
             " talon a la TABLA, desde dentro, mismo herraje que las paticas y",
             " la nariz (d_pie_tornillo). Ninguno en la cara vista."));
    echo(str("BOM: Z-Rail de Tiptop x", len(centros_rail()) + len(centros_rail_1u()),
             ", largo ", largo_riel,
             " (104 HP) -- seccion ", rail_er_fondo, " x ", rail_er_alto,
             ", hoja de datos oficial. NO es el riel de StudioRacks: ese media",
             " 27.4 de fondo y el case estuvo dibujado contra el hasta el",
             " 2026-08-17. Cuatro forman las dos filas 3U y dos forman la fila",
             " Intellijel 1U."));
    echo(str("BOM: tornillo M4 x12 para los rieles -- ROSCAN EN EL PROPIO RIEL ",
             "(viene con M4 taladrado a 3.3 de fabrica). Sin tuerca, sin inserto."));
    echo("     YA NO ATRAVIESAN LA COSTILLA. Cruzaron el acrilico hasta el");
    echo("     2026-08-26 y la chapa de la costilla hasta el 2026-08-28; el");
    echo("     anillo de pletina no lleva un solo agujero pasante, asi que el");
    echo("     riel se atornilla al MARCO DE LA VENTANA, que va al anillo con");
    echo("     roscas ciegas M4 (ver esa linea). Largo: no lo fija el modelo --");
    echo("     lo fija el pliego, contando el cajeado del marco y la rosca");
    echo("     util del riel.");
    echo(str("BOM: tornillo M4 boton x", 2*len(bridas_anillo()),
             " -- por la PUNTA del miembro alto, a una BRIDA de extremo doblada",
             " de su propia banda y roscada al anillo. Eran 8 con la brida del",
             " miembro bajo, que hoy es talon y va a la tabla."));
    echo("     ERAN M5 (spec 5) y bajan a M4 el 2026-08-28. La franja del");
    echo("     anillo mide 14: un M5 pide 1.5 D de su agujero de paso (8.25)");
    echo("     al canto de la brida y 1.5 D de su broca (6.3) a la pared del");
    echo("     rebaje, y las dos no caben a la vez en 14. El M4 si: 6.75 y");
    echo("     4.95. La brida es chapa de 1.5 -- un M5 ahi estaba sobrado.");
    echo(str("BOM: NARIZ x1 -- la banda del frente, de la MISMA chapa que el",
             " miembro alto y el talon (6082-T6 de ", t_costilla, ", radio ",
             radio_doblez_costilla, "). Desarrollo ", nariz_largo(), " x ",
             nariz_desarrollo(), ", tres dobleces (45, 45 y ", angulo_inferior,
             "): pie de ", nariz_pie, " sobre la tabla, chaflan de ",
             chaflan_nariz, ", frente vertical de ", alto_frontal - chaflan_nariz,
             " y ", nariz_s_top(), " subiendo por la cara de abajo hasta el",
             " marco de la ventana."));
    echo("     Tapa el riel del frente y el hueco entre anillos que se veian");
    echo("     desnudos desde delante y desde abajo (2026-08-29). Se para");
    echo("     debajo de la cara del riel porque la fila de abajo es TAPA y ese");
    echo("     riel sale por la cara al abrir; queda la linea de sombra del");
    echo("     labio, como entre dos filas de cualquier Eurorack.");
    echo(str("BOM: tornillo M4 avellanado x", len(nariz_m4_z()), " -- el pie de",
             " la nariz a la TABLA, desde dentro, con el mismo herraje que las",
             " paticas (d_pie_tornillo). Ninguno en la cara vista."));
    echo(str("BOM: JUNTA DE ASIENTO EPDM x2 (una por anillo), ",
             t_junta_asiento, " mm -- perfil continuo en el rebaje, entre",
             " el labio y el costado. Nunca aluminio contra acrilico. No",
             " es la junta de 4 mm del apilado viejo (muerta el",
             " 2026-08-28): esta va EN EL PLANO del rebaje, no atravesada",
             " por ningun tornillo."));
    echo(str("BOM: tornillo M4 x", len(chasis_tornillos_int()), " + TUERCA",
             " REMACHABLE (clinch, PEM S-M4) en el suelo del chasis -- el",
             " chasis del PSU a la TABLA, desde abajo, por su suelo. Cabezas",
             " bajo la tabla (el case va sobre sus paticas de ", alto_pie,
             "), nada visto por dentro."));
    echo("     COLGABA DE DOS M5 DE PARED 'a la ranura interior de base");
    echo("     trasera' hasta el 2026-08-29 por la noche -- un 2020 que murio");
    echo("     el 27-08 y que el modelo siguio dibujando dos dias --; muerto");
    echo("     tambien el miembro bajo, ahi no queda nada. Apoya en la tabla:");
    echo("     el aire de 2 mm era contra una bandeja de ACRILICO que resonaba,");
    echo("     y esa bandeja murio el 27-08. Lo comprueba guarda_chasis().");
    // Faltaban. Los M5 de arriba atan el larguero al COSTADO; estos atan la
    // PLANCHA al larguero, que es otra union y otro herraje. Salieron al montar
    // la guia de ensamblaje: las planchas tenian los taladros dibujados y el BOM
    // no tenia el tornillo.
    n_fila = max(1, round(au/100));
    echo(str("BOM: tornillo M3 x2 -- las dos PESTANAS de la banda del valle al",
             " marco de la ventana. La trasera ya no lleva NINGUNO: va",
             " capturada como las mejillas (2026-08-29, noche, 2); murieron los ",
             2*n_fila, " M3 con sus tuercas y arandelas de nylon, y con ellos",
             " las diez cabezas que se veian atras. Atras no se ve un tornillo."));
    echo("     LOS DOS DE LA PESTANA VAN AL MARCO DE LA VENTANA, no al anillo:");
    echo("     su rosca tendria que caer a 13.7 mm del plano del valle");
    echo("     (setback 6 + 2t + d/2, y con t_valle = 3 esa cuenta no baja) y");
    echo("     la franja de 14 solo admite hasta 10.25 -- la broca saldria por");
    echo(str("     la pared del rebaje. En el marco hay ", t_placa,
             " mm de pletina y se rosca pasante (ruling R3)."));
    echo(str("BOM: la TRASERA es UNA plancha de t=", t_piel, ", CAPTURADA COMO",
             " LAS MEJILLAS (2026-08-29, noche, 2): sus puntas dentro de un",
             " bolsillo fresado en la cara interior de cada anillo a lo largo",
             " del tramo trasero -- labio de ", rehundido_acrilico, ", ",
             rebaje_anillo, " de hondo, ", t_anillo - rehundido_acrilico,
             " de ancho: los numeros del bolsillo del costado --, la cara",
             " vista rehundida ", rehundido_acrilico + t_junta_asiento,
             " sobre junta de EPDM de ", t_junta_asiento, ", el canto de abajo",
             " sobre el pie del talon y el de arriba bajo la brida del techo."));
    echo(str("     ", trasera_au(), " de ancho por ", trasera_alto(), " de alto,",
             " SIN UN TALADRO. Tope hacia fuera: los dos labios del anillo y",
             " los del talon y el techo (tira de EPDM de ",
             rehundido_acrilico + t_junta_asiento - t_costilla,
             " tras cada uno); hacia dentro: las paredes de los bolsillos, la",
             " pata trasera del marco y las ", talon_pestana_n,
             " pestanas del talon (a ", talon_pestana_aire, " de aire: un tope)."));
    echo("     Fueron dos pieles de 5 partidas a la altura del");
    echo("     entrepiso, colgadas de 12 separadores M4 y con cinco filas de");
    echo("     tornillo. Separadores, junta de sombra, una plancha entera y");
    echo("     tres largueros murieron por el camino, todos el 2026-08-21; los");
    echo("     diez M3 y las dos muescas de #241, la misma noche.");
    echo("     ENTRA AL MONTAR EL SEGUNDO ANILLO, como los costados: los bolsillos");
    echo("     estan cerrados por los dos extremos (nada a la vista en ningun canto)");
    echo("     y la plancha se mete de lado en el anillo A antes de que el B entre");
    echo("     sobre los rieles y sobre su otra punta. Las tres planchas del case se");
    echo("     montan una vez; sacar la trasera es sacar un anillo. Su arista de");
    echo(str("     abajo-fuera va a chaflan de ", chaflan_trasera_bajo(), " x 45 (en el"));
    echo("     pliego, no en el DXF) para librar el escalon del bolsillo bajo el chaflan.");
    // LAS DOS FILAS SON TAPA. Cada una gira sobre el M4 de su riel de arriba y
    // se cierra con el de su otro extremo. Del total de tornillos del case
    // (12 M4 de riel + 24 M4 de marco al anillo + 4 M4 de brida + 3 M4 de la
    // nariz + 3 M4 del talon + 4 M4 del chasis + 2 M3 de pestana + 6 M5 de
    // la tabla = 58; eran 68 con los 10 M3 de la trasera hasta que se capturo
    // la noche del 2026-08-29), solo CUATRO se tocan para
    // abrirlo: dos por fila.
    echo("BOM: los M4 de riel no son todos iguales --");
    echo("     x4 EJES: tornillo de HOMBRO M4, espiga 4 mm (no M5 -- el riel");
    echo("        cambio de herraje al cambiar de fabricante). Riel del valle");
    echo("        de la fila de abajo, riel del vertice de la de arriba.");
    echo("        Pila: Belleville + ARANDELA ANCHA d16. Ver la nota de abajo.");
    echo("     x4 CIERRES: M4 de cabeza moleteada o palomilla -- se quitan a");
    echo("        mano y son los unicos que se tocan para abrir el case.");
    echo("        Riel del frente abajo, riel del valle arriba.");
    echo("     x4 FIJOS: los dos Z-Rails 1U, atornillados por ambas puntas al");
    echo("        MARCO DE LA VENTANA, no a la costilla. No son ejes ni");
    echo("        cierres: no giran, no se quitan a mano.");
    echo("     Estos 12 son los M4 DE RIEL. El case lleva mas M4 en otras");
    echo("     lineas de este BOM: marco al anillo x20, brida x4, nariz x3,");
    echo("     talon x3, chasis x4.");
    echo("     Los M5 del case son SOLO los de la TABLA (6, a rosca ciega en el");
    echo("     canto inferior del anillo): los 2 del chasis murieron con el");
    echo("     miembro bajo la noche del 2026-08-29.");
    echo("BOM: paneles ciegos en TODO hueco de LAS DOS filas -- no son estetica:");
    echo("     con la tapa abierta son lo unico que ata sus dos rieles entre si");
    // YA NO ES UN AMORTIGUADOR (2026-08-18). La tapa se queda abierta por
    // FRICCION en su propio eje, que es la solucion que no anade ninguna pieza
    // al case ni ningun taladro al acrilico.
    echo("BOM: la tapa se sostiene abierta por FRICCION en su eje. Sin");
    echo("     amortiguador, sin compas, sin anclaje nuevo.");
    echo("     Par a vencer con la tapa horizontal: 2.5 N.m por fila");
    echo("       (3.3 kg -- 2 rieles mas una fila llena -- a 77 mm de brazo).");
    echo("     Dos ejes por fila con Belleville a ~800 N dan 3.84 N.m: 1.5x.");
    echo("     LA ARANDELA ANCHA NO ES OPCIONAL. La friccion apoya sobre el");
    echo("     costado, y el PMMA FLUYE bajo carga sostenida: por encima de");
    echo("     ~10 MPa mantenidos la precarga se relaja sola en semanas y la");
    echo("     tapa deja de quedarse abierta.");
    echo("       arandela M4 normal (d9)  -> 16.3 MPa   se relaja");
    echo("       arandela ANCHA   (d16)   ->  4.3 MPa   aguanta");
    // Decia "metalica torneada" y se quedo asi cuando las paticas pasaron a
    // GOMA el 2026-08-24 (spec rev. 18): el BOM del README y el PLIEGO ya
    // dicen goma con casquillo roscado, y este echo seguia mandando a comprar
    // otra pieza. La cota de compra no es el material sino la FLECHA -- una
    // goma dura no aisla menos, AMPLIFICA los 100 Hz del toroide.
    echo(str("BOM: patica de GOMA (EPDM/NBR, Shore 45-55 A) con casquillo",
             " roscado x4, d=", d_pie, " x ", alto_pie, " mm -- se atornilla",
             " A LA TABLA, no al acrilico, y NO se pega. Se exige la curva",
             " carga-deformacion: >= ", flecha_pie,
             " mm de flecha con 22.8 N (flecha_pie). Las dos traseras van bajo",
             " el centro del pie del talon (x = ", centro_talon().x, ")."));
    echo(str("BOM: banda delantera del valle: chapa de ALUMINIO t=", t_valle,
             " PLEGADA, desarrollo ", au + 2*pv_vuelo(), " x ",
             ventana_valle()[0] - x_valle()[0], ". Es el vuelo delantero LISO,"));
    echo("     de la punta del pico al primer Z-Rail 1U, sujeto SOLO por sus dos");
    echo("     pestanas: guarda_valle() lo declara HUECO hasta que tenga apoyo.");
    echo("     No es acrilico desde el 2026-08-25; lleva una pestana");
    echo(str("     de ", pestana_valle, " doblada a 90 grados en cada punta,",
             " atornillada al MARCO DE LA VENTANA con un M3 (no al anillo",
             " -- ruling R3, ver la linea del M3 x12)."));
    echo("     Las pestanas impiden que la banda quede sujeta solo por una linea");
    echo("     de tornillos. No forman un diafragma: guarda_valle() publica por");
    echo("     separado la carga hacia abajo y el caso critico de levantamiento.");
    echo("     Va al taller de CHAPA con las tres piezas del chasis, no al de");
    echo("     acrilico. Sin recocido, sin diamantado, sin chaflan de pliego:");
    echo("     esas tres cosas son del PMMA. Canto desbarbado y basta.");
    echo("     Aleacion recomendada, no obligatoria: 6082-T6. guarda_valle()");
    echo("     calcula con Rp0.2 = 130 MPa (RP02_ALUMINIO) y a 48.8 MPa el");
    echo("     5754 H22 pasa con margen -- fluye a 533 N. El eco decia");
    echo("     'obligatoria' y Rp0.2 = 250: no es lo que la puerta exige");
    echo("     hoy, corregido aqui.");
    echo(str("BOM: TABLA de madera MACIZA t=", t_base, " x1, ",
             ancho_total + 2*vuelo_zocalo, " x ", fondo() + 2*vuelo_zocalo,
             " mm -- el suelo interior Y el zocalo, una sola pieza."));
    echo(str("     Ocupa y = -", t_base, " a 0: su cara de arriba es el suelo y su"));
    echo(str("     canto sobresale ", vuelo_zocalo,
             " mm por los cuatro lados. El marco se le APOYA encima y las"));
    echo("     cuatro paticas se le atornillan debajo.");
    echo(str("     FIJACION CON AGUJERO ALARGADO: 2 filas de 3 M5, uno REDONDO"));
    echo(str("     Van a ROSCA CIEGA en el CANTO INFERIOR del anillo, al medio"));
    echo(str("     de sus ", t_anillo, " mm (broca ", d_M5_rosca,
             "). No son del dorso y por eso no salen en costilla_dorso_2d: un"));
    echo("     DXF de la cara no sabe dibujar un taladro que entra por el canto");
    echo("     -- van listadas en el pliego, con su profundidad.");
    echo("     por fila (el del medio, el punto fijo) y los otros dos en ranura");
    echo(str("     de ", d_M5_paso + 2*holgura_veta,
             ". La madera se mueve ~3 mm a contraveta sobre los ", fondo(), " de"));
    echo("     fondo y el aluminio no. Sin el redondo la tabla se arrastra");
    echo("     hacia un extremo; con dos vuelve a estar clavada y se raja.");
    echo("     Especie sin elegir: las cuentas van contra E = 11000 MPa (nogal");
    echo("     o arce). Roble da 12000; contrachapado 8000 y pediria 20 mm.");
    echo(str("     Y catorce taladros pasantes de ", d_pie_tornillo, ": 4 de",
             " las paticas, 3 de la nariz, 3 del talon y 4 del chasis del PSU",
             " (los siete ultimos desde el 2026-08-29). Los censa guarda_zocalo()."));
    echo(str("BOM: plancha de acrilico t=", t_cheek, ": costados x2 y",
             " TRASERA -- 3 piezas."));
    echo("     UN SOLO ESPESOR en todo el cuerpo. Hubo dos hasta el 2026-08-25:");
    echo("     los 5 mm existian para UNA pieza, y esa pieza es ahora de");
    echo("     aluminio. Media plancha de 5 que ya no hay que comprar.");
    echo("     Y desde el 2026-08-27 el suelo tampoco es acrilico: es la tabla.");
    echo("     Y desde el 2026-08-27 la tapa de remate tampoco existe: la");
    echo("     meseta del techo es el ala del miembro alto.");
    echo("     LOS COSTADOS YA NO LLEVAN UN SOLO TALADRO. Son PIEL: asientan");
    echo("     en el rebaje del anillo, sin tornillo -- el labio los sostiene");
    echo("     hacia fuera y el marco de la ventana hacia dentro, por los");
    echo("     siete tramos.");
}
