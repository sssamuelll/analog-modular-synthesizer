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
//   cr[0], cr[1]  fijacion. La cara de abajo no se mueve.
//   cr[3]         EJE. Tornillo de hombro, no se aprieta (ver params.scad).
//   cr[2]         CIERRE. Se quita para abrir la tapa y se pone para cerrarla.
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
// los cuatro 3U y se atornillan por sus puntas al ALMA de cada costilla; no hay
// herraje ni taladros nuevos en las alas de la bahia. La separacion sale del
// panel, y el par completo se centra en la boca de la bahia.
function centros_rail_1u() =
    let (P = pts_perfil(),
         xc = (bahia_x0() + bahia_x1())/2,
         sep = alto_panel_1u - 2*inset_er,
         y = P[3].y - t_panel - rail_er_eje)
    [[xc - sep/2, y], [xc + sep/2, y]];

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
// Accesores POR NOMBRE. El 2026-08-27, al morir `base delantera`, todos los
// ce[i] de este fichero se habrian corrido uno a uno en silencio -- el budget
// se paso a diccionario por lo mismo. Aqui no hay dict, asi que hay tres
// funciones y ni un indice suelto fuera de ellas.
function ct_base()   = centros_transversal()[0];    // base trasera
function ct_valle()  = centros_transversal()[1];
function ct_remate() = centros_transversal()[2];

function centros_transversal() =
    let (P = pts_perfil(), r = rail/2, cr = centros_rail(),
         // Los DOS largueros traseros comparten X, y por eso esto es UNA
         // cota y no dos copias: la cara donde apoya la trasera tiene que ser
         // un plano, no dos planos parecidos. Se retiran t_piel, que es el
         // espesor de la trasera y solo suyo desde el 2026-08-21,
         // para que la plancha atornillada encima remate EXACTAMENTE en el
         // plano trasero -- empotrada y a ras, sin rebaje y sin dejar de ser
         // un DXF plano.
         x_tr = fondo() - r - t_piel,
         // El chasis del PSU se pega al larguero TRASERO, y el larguero
         // delantero se pega al chasis. Una sola cadena y en un solo sentido:
         // x_tr -> chasis -> base delantera. Ver la nota de abajo.
         y_ep = P[3].y - t_valle - r)
    // Los dos largueros de la base ya NO viven en el canto de abajo. Desde que
    // la bandeja es el suelo (t_base) montan encima de ella, o sea con su centro
    // en t_base + r, y a esa altura el redondeo de las esquinas de abajo deja de
    // afectarles -- ahi ya hay acrilico de sobra.
    //   - Frente: LO QUE MANDA ES EL CHASIS DEL PSU, no el riel de panel
    //     (2026-08-21). Estuvo derivado del riel -- se plantaba holgura_rail
    //     detras de su esquina girada, x=49.68 -- y ahi hacia dos cosas malas a
    //     la vez: se leia pegado al riel (4.00 mm, la holgura clavada) y se
    //     metia en el envolvente de los modulos de la fila de abajo, que dejaba
    //     en 25.7 mm de fondo el tramo bajo del panel.
    //
    //     Lo que se midio al ir a retirarlo: el limitante de verdad NO era el,
    //     era el CHASIS. Sus 176.6 x 93 sentados en medio del piso dejaban el
    //     fondo de modulo en 18.6 mm a media altura del panel, y quitar el
    //     larguero solo subia el panel util de 11 % a 20 % con 60 mm de fondo.
    //     Lo que mueve la aguja es correr el chasis contra el larguero trasero
    //     -- nadie decidio que fuera centrado, ch_pos() simplemente lo centraba.
    //
    //     Asi que ahora los dos se apartan: el chasis se pega al trasero y este
    //     se pega al chasis, los dos a chasis_holgura_larguero. El larguero
    //     acaba en x=88.34, o sea a 42.7 mm del riel de panel en vez de a 4.00,
    //     y el fondo de modulo sube de 18.6 a 34.4 mm (68 % del panel util con
    //     50 mm de fondo, contra el 27 % de antes).
    //
    //     No se retira: sostiene la fila delantera de tornillos de la bandeja.
    //     Sin el la plancha queda en voladizo de 280 mm bajo el chasis, y los
    //     4 puntos de panel que se ganarian a 60 mm no pagan eso.
    //   - Fondo: comparte X con el de arriba (x_tr). Estuvo en
    //     fondo - r - radio_perfil, 14 mm mas adelante que ellos, con la nota
    //     de que "adelantarlo solo compra fondo de bandeja y no hace falta".
    //     Si hacia falta: la trasera apoya en EL y en el de arriba, y con
    //     14 mm de diferencia una de sus dos filas se atornillaba al aire.
    //     Lo canta apoyo() en clearance_budget. Cabe: a y=8 la curva del canto
    //     trasero esta en x=289.87 y la esquina del riel movido en 286.22.
    [[x_tr,          r],                        // base trasera
     // valle: el cuarto, y el unico que existe por una plancha y no por una
     // union. Va CENTRADO bajo la tapa del valle para que los dos vuelos sean
     // iguales; a la vez ata los dos costados por la cintura, que es donde el
     // perfil es mas estrecho. Su ventana es corta -- entre las esquinas
     // giradas de los dos railes del valle -- y clearance_budget la vigila.
     [(x_valle()[0] + x_valle()[1])/2, y_ep],
     // remate trasero: el QUINTO, del 2026-08-21. Existe para que la tapa del
     // techo tenga a que atornillarse -- antes iba pegada al Z-Rail porque ahi
     // arriba no habia nada mas, y esa era la unica junta irreversible del case.
     // Va a ras del plano trasero y con su cara de arriba a marco_sup del techo,
     // de modo que la plancha apoye encima y remate a ras. No puede acercarse
     // mas al frente: el barrido del Z-Rail al abrir la tapa se lo come.
     // Comparte X con el de base desde que la trasera le pasa por delante:
     // los DOS largueros traseros son una sola cota, y entre ellos la plancha
     // vuela 211.73 mm sin apoyo intermedio -- a proposito.
     [x_tr,        P[5].y - marco_sup - r]];

// --- referencias de los tres miembros de chapa -------------------------
//
// centros_transversal() conserva por ahora la geometria historica de los tres
// 2020 para el eco del BOM. El modelo y los DXF ya no la consumen: sus herederos
// son estas cotas, gemelas de _cajas_miembro() en clearance_budget.py.
function radio_giro_riel() = norm([rail_er_fondo, rail_er_alto]) / 2;
function miembro_x_trasera() = pts_perfil()[6].x - t_piel;
function miembro_y_meseta() = pts_perfil()[5].y - marco_sup;

// El barrido de la tapa inferior manda el ala delantera; el canto trasero lo
// manda la propia tapa del valle. La resta es el suelo de 48.18 mm que usa el
// contrato bbox_desarrollo_bahia().
function bahia_x0() = centros_rail()[1].x + radio_giro_riel() + holgura_rail;
function bahia_x1() = x_valle()[1];
function bahia_y1() = pts_perfil()[3].y - t_valle;
function bahia_y0() = bahia_y1() - bahia_alto;
function bahia_centro() = [(bahia_x0() + bahia_x1()) / 2,
                           (bahia_y0() + bahia_y1()) / 2];

// Un M5 por miembro, atornillado por su punta al centro de la caja completa.
// En la bahia eso significa su ENVOLVENTE TOTAL, no una de las dos alas.
function centro_miembro_bajo() = [miembro_x_trasera() - canal_fondo/2,
                                  canal_ancho/2];
function centro_miembro_alto() = [miembro_x_trasera() - canal_ancho/2,
                                  miembro_y_meseta() - canal_ancho/2];
// centros_miembro_punta() murio el 2026-08-28. Era la lista de los tres M5 que
// atravesaban la costilla de chapa por la punta de cada miembro; el anillo no
// lleva agujeros pasantes -- los miembros se atornillan a roscas ciegas de la
// franja interior, con una brida de extremo (spec 5) que es cosa de la Tarea 3.
// Los dos centros sueltos se quedan: paticas() usa el bajo.

// Filas de la piel: no coinciden todas con el centro de la envolvente. La de
// arriba vive en el alma vertical, por debajo de la meseta de marco_sup.
function anclaje_piel_base() = centro_miembro_bajo();
function anclaje_piel_remate() = [miembro_x_trasera() - t_costilla/2,
                                  miembro_y_meseta() - marco_sup
                                                     - canal_ancho/2];

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
// el 2026-08-24: esquina viva, para que la trasera y la tapa de remate
// empotren a ras. Antes eran radio_remate (2) y radio_perfil (14), y ese 14 le
// dejaba a la trasera 14 mm de esquina colgando fuera de la silueta del
// costado. radio_perfil se quedo sin clientes y se borro. El porque completo,
// y que parte de la regla anti-fisura se sostiene y cual no, en params.scad.
//
// redondear() ya sabe tratar el 0: R[i] <= 0 devuelve el vertice pelado, sin
// arco. No hace falta tocarla.
function radios_perfil() = [radio_punta,  radio_punta,
                            radio_pico,   radio_valle,
                            radio_remate, radio_trasero,
                            radio_trasero];

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
    polygon(redondear(pts_perfil(), radios_perfil(), [4, 5, 6]));
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
    offset(delta = -(retiro_rebaje() + hol_costado)) perfil_lateral();
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

module anillo_2d() {
    difference() {
        perfil_lateral();
        offset(delta = -cara_anillo) perfil_lateral();
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
    offset(delta = -retiro_rebaje()) perfil_lateral();
    for (c = centros_rosca_ciega())
        translate(c[0]) circle(d = c[1]);
}

// [centro, diametro de broca] de cada rosca ciega de la cara interior. Vacio
// hasta que las placas de anclaje existan (plan, Tarea 3).
function centros_rosca_ciega() = [];

// El solido: cara vista en z=0, cara interior en z=t_anillo. El chaflan se
// construye como laminas de offset() creciente -- seis de 0.25 -- porque un
// chaflan exacto sobre un contorno concavo no sale de hull() ni barato de
// minkowski(); para el render y para solapes() basta y es determinista.
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
                            offset(delta = -cara_anillo + f) perfil_lateral();
                        }
            translate([0, 0, chaflan_anillo])
                linear_extrude(t_anillo - chaflan_anillo) anillo_2d();
        }
        // el rebaje, por detras
        translate([0, 0, rehundido_acrilico])
            linear_extrude(t_anillo)
                offset(delta = -retiro_rebaje()) perfil_lateral();
    }
}

// El plegado de la chapa de LOS TRES MIEMBROS. Se llamo cost_bd() hasta el
// 2026-08-28 y la formula es la MISMA -- setback por dos menos el arco de la
// fibra neutra --, con los mismos parametros: es el mismo material y el mismo
// radio. Cambia el nombre y nada mas, porque la costilla dejo de plegarse y el
// nombre viejo prometia una pieza que ya no se dobla.
function miembro_bd() = 2*(radio_doblez_costilla + t_costilla)
                        - PI/2*(radio_doblez_costilla + k_factor*t_costilla);

// --- LOS TRES MIEMBROS: desarrollos de chapa de aluminio ----------------
//
// El miembro bajo cruza entre las dos costillas en la trasera inferior. Recibe
// el canto bajo de la piel trasera y la fijacion trasera del chasis del PSU.
// Su DXF no es la seccion 20 x 20 ya montada: al tumbar las dos alas del canal
// en U, el blank concatena ala + alma + ala y descuenta el BD de cada doblez.
module miembro_bajo_2d() {
    desarrollo = canal_fondo + canal_ancho + canal_fondo - 2*miembro_bd();
    y_alma = canal_fondo + canal_ancho/2 - miembro_bd();
    difference() {
        square([ancho_util, desarrollo]);
        fila_agujeros(ancho_util, y_alma);
    }
}

// El miembro alto cruza entre las costillas en el remate trasero. Recibe el
// canto alto de la piel trasera y la tapa horizontal del remate. Es un canal
// ASIMETRICO: el ala larga de arriba es la propia MESETA de prof_sup; la de
// abajo es un retorno corto de canal_fondo. Ese retorno no es adorno: un ala
// libre de 528 mm en chapa de 3 ondula y, al ser una pieza vista, dejaria
// ademas un canto vivo. El desarrollo vuelve a tumbar las tres caras en un
// plano y por eso supera la envolvente de la pieza plegada, con dos BD menos.
module miembro_alto_2d() {
    desarrollo = canal_fondo + canal_ancho + prof_sup - 2*miembro_bd();
    // El solido manda el orden: retorno corto inferior, alma, meseta superior.
    y_alma = canal_fondo + canal_ancho/2 - miembro_bd();
    largo_meseta_plana = prof_sup - miembro_bd();
    y_rejilla = desarrollo - largo_meseta_plana/2;
    n_hp = round(largo_riel/hp);
    difference() {
        square([ancho_util, desarrollo]);
        fila_agujeros(ancho_util, y_alma);
        // La salida de aire deja la banda del valle LISA y sube a esta cara.
        // Una fila registrada al HP, misma ranura oblonga que el resto: 16 de
        // 15 x 4 dan ~905 mm2. guarda_aire() usa ademas su altura real.
        for (n = [meseta_paso_hp : meseta_paso_hp : n_hp - meseta_paso_hp])
            translate([n*hp, y_rejilla])
                ranura(meseta_largo_ranura, vent_ancho_ranura);
    }
}

// La bahia cruza el case entre los dos Z-Rails que miran al valle. Su suelo
// ocupa la ventana libre entre las esquinas reales de esos rieles; las dos alas
// forman las paredes de la bahia y reciben la tapa del valle en sus cantos.
// El blank es mayor que ese suelo porque las dos paredes se cortan tumbadas en
// el mismo plano: suelo + dos alas de bahia_alto, menos un BD por doblez.
module bahia_2d() {
    // La cota delantera la manda el BARRIDO del riel inferior, no su esquina
    // quieta. El contrato Python ya usa esta misma resta (48.18 mm).
    suelo = bahia_x1() - bahia_x0();
    desarrollo = suelo + 2*bahia_alto - 2*miembro_bd();
    y_suelo = bahia_alto + suelo/2 - miembro_bd();
    difference() {
        square([ancho_util, desarrollo]);
        fila_agujeros(ancho_util, y_suelo);
    }
}

// Solidos plegados de los tres miembros. Los desarrollos de arriba son para el
// taller; estas caras son para colisiones visuales y para los STL de render.
// Todos cruzan exactamente ancho_util, entre las puntas de los Z-Rails.
function miembros_z0() = (ancho_total - ancho_util) / 2;

module miembro_bajo() {
    x1 = miembro_x_trasera();
    z0 = miembros_z0();
    // alma trasera + dos retornos del canal en U
    translate([x1 - t_costilla, 0, z0])
        cube([t_costilla, canal_ancho, ancho_util]);
    for (y = [0, canal_ancho - t_costilla])
        translate([x1 - canal_fondo, y, z0])
            cube([canal_fondo, t_costilla, ancho_util]);
}

module ranura_meseta_3d(xc, y0, zc) {
    hull() for (s = [-1, 1])
        translate([xc + s*(meseta_largo_ranura - vent_ancho_ranura)/2,
                   y0 - 0.1, zc])
            rotate([-90, 0, 0])
                cylinder(d = vent_ancho_ranura, h = marco_sup + 0.2);
}

module miembro_alto() {
    x1 = miembro_x_trasera();
    y1 = miembro_y_meseta();
    y0 = y1 - canal_ancho;
    z0 = miembros_z0();
    // alma y retorno corto de abajo
    translate([x1 - t_costilla, y0, z0])
        cube([t_costilla, canal_ancho, ancho_util]);
    translate([x1 - canal_fondo, y0, z0])
        cube([canal_fondo, t_costilla, ancho_util]);
    // La meseta de prof_sup ES el ala superior de esta misma pieza: nace en
    // el pliegue del alma y avanza hacia el frente, sin cruzar la propia alma.
    difference() {
        translate([x1 - prof_sup, y1, z0])
            cube([prof_sup, marco_sup, ancho_util]);
        n_hp = round(largo_riel/hp);
        for (n = [meseta_paso_hp : meseta_paso_hp : n_hp - meseta_paso_hp])
            ranura_meseta_3d(x1 - prof_sup/2, y1, z0 + n*hp);
    }
}

module bahia() {
    x0 = bahia_x0();
    x1 = bahia_x1();
    y0 = bahia_y0();
    y1 = bahia_y1();
    z0 = miembros_z0();
    translate([x0, y0, z0])
        cube([x1 - x0, t_costilla, ancho_util]);
    for (x = [x0, x1 - t_costilla])
        translate([x, y0, z0])
            cube([t_costilla, y1 - y0, ancho_util]);
}

module miembros() {
    miembro_bajo();
    miembro_alto();
    bahia();
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
        for (zc = [v + t_cheek + t_costilla/2,
                   v + ancho_total - t_cheek - t_costilla/2])
            for (i = [0 : n_agujeros() - 1])
                let (y = bandeja_base_fondo()*(i + 0.5)/n_agujeros(),
                     medio = (i == floor(n_agujeros()/2)))
                    translate([zc, y])
                        if (medio) circle(d = d_M5_paso + kerf);
                        else hull() for (dy = [-holgura_veta, holgura_veta])
                            translate([0, dy]) circle(d = d_M5_paso + kerf);
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

function trasera_au() = ancho_util - 2*hol_piel;
function trasera_y_relieve() =
    anclaje_piel_base().y
    + 0.74*(anclaje_piel_remate().y - anclaje_piel_base().y);

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
    au = ancho_util - 2*hol_piel;
    P  = pts_perfil();
    // UNA sola plancha desde el 2026-08-21: fueron dos (piel_inferior y
    // piel_superior) partidas a la altura del entrepiso, porque cada una se
    // atornillaba a los dos largueros de SU piso. Muerta la bandeja de
    // entrepiso esa frontera dejo de existir. Va en t_piel (8), que es su
    // propio espesor desde el 2026-08-21.
    // Canto de abajo EN EL PLANO DEL SUELO. Estuvo en ct_base().y - 15 (o sea
    // y=3), que no era una cota del case sino la distancia al canto de la fila
    // de M3 leida al reves: 15 mm por debajo del larguero de base trasera. Ese
    // 15 no sabia donde estaba el suelo, y dejaba un rebaje corrido de
    // 528 x 3 x 8 a lo largo de todo el canto trasero -- una junta de sombra,
    // que es el lenguaje que esta pieza enterro al empotrarse. Ahora la cara
    // trasera es continua desde el piso hasta la tapa de remate.
    //
    // El 0 no es un numero libre: es el plano inferior del case, el mismo
    // datum del que cuelga la bandeja de base (y=0 a t_base) y donde muere el
    // canto de los costados. Lo vigila guarda_piso(), assert 4.
    //
    // La fila de M3 de abajo se aleja del canto al bajarlo: 15 -> 18 mm, o sea
    // MAS material alrededor del tornillo. Y las ondas y la rejilla no se
    // mueven: van derivadas de f_base/f_tras, que son diferencias contra
    // ce[].y y por tanto no dependen de y0.
    y0   = 0;                               // canto de abajo = plano del suelo
    // Hasta la cara de ABAJO DE LA TAPA DE REMATE. Antes se frenaba en el
    // larguero de remate, que vivia a ras del plano trasero y le tapaba la
    // banda; desde que ese larguero se retiro t_piel, la trasera le pasa por
    // delante y llega arriba del todo.
    alto = (P[5].y - marco_sup) - y0;
    // DOS filas, una por larguero trasero, y las dos caen en SU centerline y
    // no a una distancia del canto. Fueron CINCO hasta el 2026-08-21: los tres
    // largueros de en medio no sujetaban ya nada mas que estas filas, y una
    // plancha continua de 8 atornillada arriba y abajo trabaja de alma de
    // cortante en esa cara mejor que cinco barras sueltas.
    f_base = anclaje_piel_base().y - y0;
    f_tras = anclaje_piel_remate().y - y0;
    // Las ondas van derivadas de las dos filas que las rodean: asi no se acercan
    // a un tornillo si un larguero se mueve.
    //
    // La de abajo sube a 0.37 (estuvo en 0.32) para SEPARARSE de la rejilla que
    // tiene debajo. Con la banda derivada de la onda y separada solo por
    // vent_puente_min, los dos campos se leian como uno; subir la onda sola no
    // arreglaba nada, porque la rejilla subia con ella. Lo que separa de verdad
    // es vent_separacion, y la onda sube para que la rejilla no encoja al
    // hacerle sitio: la banda pasa de 40.46 a 41.47 mm.
    y_bajas  = f_base + 0.37*(f_tras - f_base);
    y_sierra = f_base + 0.74*(f_tras - f_base);
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
    lib0 = f_base + valle_espina/2 + vent_puente_min;
    // vent_ancho_ranura/2 y no solo la amplitud: la onda es un hull de circulos,
    // asi que su borde de MATERIAL cae medio ancho de ranura por debajo de la
    // polilinea. Sin ese termino el parametro medía 2 mm menos de lo que decia.
    lib1 = y_bajas - vent_periodo*0.35 - vent_ancho_ranura/2 - vent_separacion;
    difference() {
        plancha(au, alto);
        for (y = [f_base, f_tras]) fila_agujeros(au, y);
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
function pv_x() = bahia_x0() - pv_ancho_x()/2;

module tapa_valle_2d() {
    au = ancho_util;
    xv = x_valle();
    // Solo queda el vuelo DELANTERO: acaba antes del primer Z-Rail 1U. La
    // banda queda maciza: Samuel no quiere ver ranuras en el valle.
    largo = bahia_x0() - xv[0];
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
        // --- los 4 M5 que CUELGAN el chasis de los dos largueros (#106) ---
        // Van en las dos paredes LARGAS, que son las que miran a los largueros:
        // la matriz de chasis() manda su Y local al X del case. La altura sale
        // del case y no del chasis -- es el eje de la ranura interior del 2020,
        // que esta a rail/2 sobre la bandeja, menos lo que el suelo ya subio.
        // Por eso chasis_pie no puede crecer: se come la pared que hay debajo.
        for (x = ch_tornillos(ext.x, chasis_anclajes))
            for (s = [0, 1])
                translate([off + x - ch_sb(),
                           abs(s*b.y - ch_desarrollo(rail/2 - chasis_pie,
                                                     ch_ala(ext.z)))])
                    circle(d = d_M5_paso + kerf);
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
function x_chasis_frente() =
    (centro_miembro_bajo().x - canal_fondo/2)
    - chasis_holgura_larguero - ch_tapa_ext().y;

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

// OJO: EL TERMINO EN Z DE ESTA MATRIZ NO ES UN PLANO, y por eso no se toco al
// mover la cara interior a t_anillo el 2026-08-28. `ancho_total - t_cheek` con
// el -1 deja el chasis en z = 10.50..349.10, mientras ch_pos() y guarda_chasis()
// lo colocan en 206.02..544.62: no es un desfase de espesor, es un ESPEJO de
// lado -- y ademas contradice a salida_cables_xy(), que saca el agujero de la
// tabla del ch_pos() sin espejar. Sustituir t_cheek por t_anillo aqui lo
// empeora (lo mete 6 mm mas dentro del anillo), asi que la cota se queda como
// esta hasta que se decida de que lado vive el PSU. NO LO CAZA NINGUNA PUERTA:
// el chasis no es un cuerpo de _cajas_solidas(), o sea que solapes() no lo mira,
// y en el render queda detras de los paneles. Va al registro de pendientes.
module chasis() {
    p  = ch_pos();
    multmatrix([[0, 1, 0, -vuelo_zocalo + p.y],
                [0, 0, 1, chasis_pie],
                [-1, 0, 0, ancho_total - t_cheek - p.x],
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
else if (PART == "assembly")           assembly();
else if (PART == "assembly_acrilico")  assembly_acrilico();
else if (PART == "assembly_aluminio")  assembly_aluminio();
else if (PART == "assembly_madera")    assembly_madera();
else if (PART == "assembly_esqueleto") assembly_esqueleto();
else if (PART == "assembly_acero")     assembly_acero();
else if (PART == "bandeja_base_2d")      bandeja_base_2d();
else if (PART == "tapa_valle_2d")        tapa_valle_2d();
else if (PART == "miembro_bajo_2d")      miembro_bajo_2d();
else if (PART == "miembro_alto_2d")      miembro_alto_2d();
else if (PART == "bahia_2d")             bahia_2d();
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

// tope de bandeja a ras de P3.y (canto SUPERIOR, no inferior — ver
// centros_transversal()); canto delantero a ras del rail reubicado.

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
    translate([P[6].x, 0, t_anillo + hol_piel])
        rotate([0, -90, 0])
            difference() {
                linear_extrude(t_piel) piel_trasera_2d();
                translate([0, 0, -0.1])
                    linear_extrude(kondor_prof + 0.1) kondor_2d(espejo = true);
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
    translate([xv[0], P[3].y, ancho_total - t_anillo])
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
    // arranca en la cara interior del anillo y cruza ancho_util: era
    // t_cheek cuando la piel de acrilico era esa cara (hasta 2026-08-28)
    translate([A.x, A.y, t_anillo])
        rotate([0, 0, atan2(d.y, d.x)])
            translate([s0, -t_panel, 0])
                cube([largo, t_panel, ancho_util]);
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
}

// Pestana superior: la banda de acrilico que tapa el canto de arriba del panel
// y cruza de costado a costado. Ocupa los ultimos marco_sup mm de la cara, con
// su cara exterior EN EL PLANO DE LA CARA -- igual que el panel, o sea a ras y
// no en resalte. Engorda hacia dentro t_cheek, que es el mismo grosor del
// costado, de modo que por fuera el remate se lee como un canto continuo de
// acrilico que da la vuelta del lateral al techo. Sin ella el panel remataba
// pelado contra el aire, que es lo que Samuel vio en el render.
//
// ES PIEZA DE TAPA (2026-08-17): viaja con el panel al abrir.
//
// YA SE FIJA (ver params.scad): APOYA DE CANTO en la cara de arriba del riel --
// la que mira al vertice, 27.4 x 528 de aluminio plano -- y se atornilla a ella
// con M3 que entran por su canto, a lo largo de la cara. Por delante no habia
// manera: el riel solo asoma 2.25 mm por encima del panel y ahi no cabe una
// cabeza. marco_sup es el ESPESOR de su plancha, prof_sup su fondo.
//
// El solido va con cube() y el DXF con remate_sup_2d(); los dos leen los mismos
// dos parametros, asi que no pueden separarse sin que se note en params.
module remate_sup() {
    P = pts_perfil();
    // misma cara interior que el panel: t_anillo, no t_cheek
    translate([P[4].x + inset_remate_frente, P[5].y - marco_sup, t_anillo])
        cube([prof_sup, marco_sup, ancho_util]);
}

// La pestana vista de canto: 528.32 x prof_sup en plancha de marco_sup.
// SIN TALADROS. Llevo cinco M3 mientras el plan era atornillarla al riel; la
// hoja de datos del Z-Rail enseno que esa cara es pared de 1.2 mm, asi que la
// union pasa a ser junta pegada y esos cinco agujeros dejaron de servir a
// nadie. Fresando eso no es cosmetico: son cinco prestaciones que se pagan.
// Si el calibrador encuentra material, volver a meterlos es una linea.
module remate_sup_2d() {
    au = ancho_util;
    P = pts_perfil();
    ce = centros_transversal();
    difference() {
        plancha(au, prof_sup);
        // la fila cae en la centerline del larguero nuevo, medida desde el
        // canto DELANTERO de la plancha (el que remata el canto del panel).
        fila_agujeros(au, ct_remate().x - P[4].x - inset_remate_frente);
    }
}

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
    for (x = [alto_frontal/2 + d_pie/2, centro_miembro_bajo().x])
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
    echo(str("BOM: COSTILLA x2 -- anillo de PLETINA de ", t_anillo, " fresado. El detalle lo reescribe la Tarea 5."));
    echo(str("BOM: transversal 2020 x", len(centros_transversal()), " de ", au, " mm"));
    echo("     Fueron CUATRO hasta el 2026-08-27. Se fue `base delantera`, la");
    echo("     unica que flotaba en mitad del suelo; las tres que quedan estan");
    echo("     arrinconadas contra dos caras cada una o sostienen una plancha");
    echo("     que nada mas alcanza (el valle).");
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
    echo("     riel se atornilla a una PLACA DE ANCLAJE interior que va al");
    echo("     anillo con roscas ciegas. Largo: lo fija la placa de anclaje,");
    echo("     Tarea 3. El detalle entero lo reescribe la Tarea 5.");
    echo(str("BOM: tornillo M5 boton x", 2*len(centros_transversal()),
             " + tuerca T -- por la PUNTA de las transversales 2020. Desde el",
             " 2026-08-27 no atraviesan el acrilico y desde el 28 tampoco la",
             " costilla: van a una brida de extremo con roscas ciegas en la",
             " franja interior del anillo (Tareas 3 y 5)."));
    echo(str("BOM: tornillo M5 x", chasis_anclajes, " + tuerca T + SEPARADOR de ",
             chasis_holgura_larguero, " -- cuelgan el chasis del PSU de la ranura"));
    echo("     INTERIOR de `base trasera` (#106). El separador no es opcional:");
    echo("     el tornillo cruza ese aire y sin el, apretar abolla la pared de");
    echo("     1.5 de chapa hacia dentro.");
    echo("     FUERON CUATRO, dos por pared larga, hasta el 2026-08-27: la");
    echo("     pared DELANTERA colgaba de `base delantera`, y esa barra ya no");
    echo("     existe. Ahora esa pared APOYA en la tabla, que es un miembro");
    echo("     estructural en cuatro paticas.");
    // Faltaban. Los M5 de arriba atan el larguero al COSTADO; estos atan la
    // PLANCHA al larguero, que es otra union y otro herraje. Salieron al montar
    // la guia de ensamblaje: las planchas tenian los taladros dibujados y el BOM
    // no tenia el tornillo.
    n_fila = max(1, round(au/100));
    // TRES filas de n_fila: una de la tapa de remate y DOS de la trasera. La
    // tapa del valle perdio sus dos filas al canto al quedar reducida a la banda
    // ranurada; conserva solo sus dos pestanas. Fueron nueve hasta el 2026-08-21 (cinco en la
    // trasera, se fueron con los tres largueros traseros de en medio) y seis
    // hasta el 2026-08-27: las DOS de la bandeja de base desaparecieron cuando
    // el suelo dejo de ser una plancha colgada de dos largueros y paso a ser
    // una TABLA bajo el marco, con sus propios M5 y sus agujeros alargados.
    echo(str("BOM: tornillo M3 x", 3*n_fila + 2, " + tuerca T M3 -- las planchas",
             " a las transversales: tapa de remate ", n_fila, ", trasera ", 2*n_fila,
             ", + 2 de las PESTANAS de la tapa del valle a la costilla."));
    echo("     Estos entran por la RANURA del 2020, no por su punta. Es donde");
    echo("     la tuerca de insercion lateral se paga sola: con las de deslizar");
    echo("     hay que dejarlas dentro ANTES de cerrar el esqueleto.");
    echo(str("BOM: la TRASERA es UNA plancha empotrada de t=", t_piel, ", no dos:"));
    echo(str("     ", ancho_util - 2*hol_piel, " de ancho,",
             " atornillada arriba y abajo y NADA en medio: 211.73 mm de vano"));
    echo("     libre, que en 8 mm de acrilico son 0.15 de flecha con 50 N en el");
    echo("     centro. Fueron dos pieles de 5 partidas a la altura del");
    echo("     entrepiso, colgadas de 12 separadores M4 y con cinco filas de");
    echo("     tornillo. Separadores, junta de sombra, una plancha entera y");
    echo("     tres largueros murieron por el camino, todos el 2026-08-21.");
    // LAS DOS FILAS SON TAPA. Cada una gira sobre el M4 de su riel de arriba y
    // se cierra con el de su otro extremo. Del total de tornillos del case
    // (12 M4 de riel + 6 M5 de transversal + 2 M5 del chasis + 6 M5 de la tabla
    // + 17 M3 de plancha; los 24 M4 de separador se fueron con los separadores
    // el 2026-08-21), solo CUATRO se tocan para abrirlo: dos por fila.
    echo("BOM: los M4 de riel no son todos iguales --");
    echo("     x4 EJES: tornillo de HOMBRO M4, espiga 4 mm (no M5 -- el riel");
    echo("        cambio de herraje al cambiar de fabricante). Riel del valle");
    echo("        de la fila de abajo, riel del vertice de la de arriba.");
    echo("        Pila: Belleville + ARANDELA ANCHA d16. Ver la nota de abajo.");
    echo("     x4 CIERRES: M4 de cabeza moleteada o palomilla -- se quitan a");
    echo("        mano y son los unicos que se tocan para abrir el case.");
    echo("        Riel del frente abajo, riel del valle arriba.");
    echo("     x4 FIJOS: los dos Z-Rails 1U, atornillados por ambas puntas a");
    echo("        las costillas. No son ejes ni cierres y no tocan las alas.");
    // Decia "x6 fijos: los largueros de esqueleto" bajo un encabezado que
    // habla de M4 DE RIEL, y esos largueros van con M5. Contaba dos herrajes
    // distintos en la misma lista. Los M4 de riel son DOCE: cuatro ejes,
    // cuatro cierres y cuatro fijaciones permanentes de la fila 1U.
    echo("     Y no hay mas M4: los 12 son estos. Los tornillos de transversal");
    echo("     son M5 y van en su propia linea.");
    echo("BOM: tuercas T DE INSERCION LATERAL (drop-in), NO de deslizar. Con las");
    echo("     de deslizar hay que enhebrarlas por la punta del larguero antes de");
    echo("     montar, o sea que anadir un tornillo mas tarde obliga a desarmar.");
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
    echo(str("BOM: tapa de remate x1, ", au, " x ", prof_sup, " en acrilico ",
             "t=", marco_sup, " -- plancha HORIZONTAL sobre la meseta del techo,"));
    echo(str("     atornillada con ", n_fila, " M3 al larguero de remate trasero."));
    echo("     SIN ADHESIVO. Hasta el 2026-08-21 era una tira de canto PEGADA al");
    echo("     Z-Rail, porque ahi arriba no habia larguero al que atornillarla y");
    echo("     esa cara del riel es pared de 1.2 mm. Con el octavo larguero deja");
    echo("     de hacer falta: el case ya no lleva ninguna junta irreversible.");
    echo(str("     Se retira ", inset_remate_frente, " mm del pico, y eso NO es"));
    echo("     estetica: es lo unico que deja abrir la tapa de la fila de arriba.");
    // Decia "metalica torneada" y se quedo asi cuando las paticas pasaron a
    // GOMA el 2026-08-24 (spec rev. 18): el BOM del README y el PLIEGO ya
    // dicen goma con casquillo roscado, y este echo seguia mandando a comprar
    // otra pieza. La cota de compra no es el material sino la FLECHA -- una
    // goma dura no aisla menos, AMPLIFICA los 100 Hz del toroide.
    echo(str("BOM: patica de GOMA (EPDM/NBR, Shore 45-55 A) con casquillo",
             " roscado x4, d=", d_pie, " x ", alto_pie, " mm -- se atornilla",
             " A LA TABLA, no al acrilico, y NO se pega. Se exige la curva",
             " carga-deformacion: >= ", flecha_pie,
             " mm de flecha con 22.8 N (flecha_pie)"));
    echo(str("BOM: banda delantera del valle: chapa de ALUMINIO t=", t_valle,
             " PLEGADA, desarrollo ", au + 2*pv_vuelo(), " x ",
             bahia_x0() - x_valle()[0], ". Es el vuelo delantero LISO;"));
    echo("     la plancha sobre la boca de la bahia y sus diez M3 ya no existen.");
    echo("     No es acrilico desde el 2026-08-25; lleva una pestana");
    echo(str("     de ", pestana_valle, " doblada a 90 grados en cada punta,",
             " atornillada a la costilla con un M3."));
    echo("     Las pestanas impiden que la banda quede sujeta solo por una linea");
    echo("     de tornillos. No forman un diafragma: guarda_valle() publica por");
    echo("     separado la carga hacia abajo y el caso critico de levantamiento.");
    echo("     Va al taller de CHAPA con las tres piezas del chasis, no al de");
    echo("     acrilico. Sin recocido, sin diamantado, sin chaflan de pliego:");
    echo("     esas tres cosas son del PMMA. Canto desbarbado y basta.");
    echo("     Aleacion obligatoria: 6082-T6. La puerta va contra Rp0.2 = 250");
    echo("     MPa; 5754 H22 ya no pasa con los miembros de 1.5 mm.");
    echo(str("BOM: TABLA de madera MACIZA t=", t_base, " x1, ",
             ancho_total + 2*vuelo_zocalo, " x ", fondo() + 2*vuelo_zocalo,
             " mm -- el suelo interior Y el zocalo, una sola pieza."));
    echo(str("     Ocupa y = -", t_base, " a 0: su cara de arriba es el suelo y su"));
    echo(str("     canto sobresale ", vuelo_zocalo,
             " mm por los cuatro lados. El marco se le APOYA encima y las"));
    echo("     cuatro paticas se le atornillan debajo.");
    echo(str("     FIJACION CON AGUJERO ALARGADO: 2 filas de 3 M5, uno REDONDO"));
    echo("     por fila (el del medio, el punto fijo) y los otros dos en ranura");
    echo(str("     de ", d_M5_paso + 2*holgura_veta,
             ". La madera se mueve ~3 mm a contraveta sobre los ", fondo(), " de"));
    echo("     fondo y el aluminio no. Sin el redondo la tabla se arrastra");
    echo("     hacia un extremo; con dos vuelve a estar clavada y se raja.");
    echo("     Especie sin elegir: las cuentas van contra E = 11000 MPa (nogal");
    echo("     o arce). Roble da 12000; contrachapado 8000 y pediria 20 mm.");
    echo(str("BOM: plancha de acrilico t=", t_cheek, ": costados x2, tapa de remate",
             " y TRASERA -- 4 piezas."));
    echo("     UN SOLO ESPESOR en todo el cuerpo. Hubo dos hasta el 2026-08-25:");
    echo("     los 5 mm existian para UNA pieza, y esa pieza es ahora de");
    echo("     aluminio. Media plancha de 5 que ya no hay que comprar.");
    echo("     Y desde el 2026-08-27 el suelo tampoco es acrilico: es la tabla.");
    echo("     LOS COSTADOS YA NO LLEVAN UN SOLO TALADRO. Son PIEL: quedan");
    echo("     capturados entre las dos alas de la costilla, sin tornillo.");
}
