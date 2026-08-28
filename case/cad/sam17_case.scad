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

// --- LAS PLACAS DE ANCLAJE Y LAS ROSCAS CIEGAS --------------------------
//
// El eje del M4 de cada riel cae a 15.90 de la silueta, o sea DENTRO del
// rebaje, donde el anillo solo tiene 3 mm de labio: por ahi el tornillo sale
// por la cara vista. Asi que el riel muere contra una PLACA apoyada en la
// franja interior y es la placa la que va al anillo, con dos M4 a rosca
// ciega. Los miembros hacen lo mismo con una BRIDA doblada de su blank.
//
// LA PLACA ES EL MARCO DE LA FILA: una por TRAMO y por costado, corrida de
// esquina a esquina, no una por riel. Lo decidio Samuel el 2026-08-28 mirando
// el render -- con placas sueltas de 28 quedaba una ranura de 6.15 mm abierta
// en cada punta de cada fila y por ahi se veia el interior. El canto de 6 mm
// de la placa corrida la tapa y se lee como el borde de aluminio de la fila.
//
// TODO ESTO ES GEMELO de _placas(), _bridas() y _centros_rosca_ciega() en
// clearance_budget.py, y quien las cruza es taladros_anillo() releyendo el
// DXF del dorso. Si las dos lenguas se separan, el DXF lo canta.

// [nombre, vertice de arranque, vertice de fin, rieles 3U (vacio = la fila
// 1U), modo de corte de cada esquina honda, retiro extra en cada extremo]
function tramos_placa() = [
    ["cara_inf", 1, 2, [0, 1], ["", "bisectriz"], [0, 0]],
    ["valle",    2, 3, [],     ["bisectriz", ""], [0, 0]],
    ["cara_sup", 3, 4, [2, 3], ["", "45"],        [retiro_placa_sup, 0]]];

// Cuanto se retira la placa del vertice i: la TANGENTE de su redondeo si el
// vertice es convexo -- ahi el contorno se mete hacia dentro y una esquina de
// placa apoyada en la recta se saldria de la silueta -- y CERO si es concavo,
// porque ahi el redondeo aparta el contorno y la placa puede pasar de largo.
// El perfil se recorre en sentido HORARIO: convexo es producto vectorial < 0.
function retiro_placa(i) =
    let (P = pts_perfil(), m = len(P),
         A = P[(i + m - 1) % m], V = P[i], B = P[(i + 1) % m],
         cruz = (V.x - A.x)*(B.y - V.y) - (V.y - A.y)*(B.x - V.x))
    cruz < 0 ? tangente(V, A - V, B - V, radios_perfil()[i]) : 0;

function ang_vertice(i) =
    let (P = pts_perfil(), m = len(P))
    _ang(P[(i + m - 1) % m] - P[i], P[(i + 1) % m] - P[i]);

// [ds, db] del corte de una esquina honda. Dos cortes distintos:
//   "bisectriz"  reparte el rincon con la placa VECINA -- las dos quieren la
//                misma cuna de material y hay que partirla. Un chaflan de 45
//                no vale: con el pico a 125 grados y 26 de fondo pediria un
//                corte de 30 sobre una placa de 26 de honda.
//   "45"         libra una pieza concreta, la brida del miembro trasero alto.
// El corte se mide desde el VERTICE y la placa ya arranca retirada de el.
function corte_placa(i, fondo, retiro, modo, fin) =
    modo == "45"        ? [placa_chaflan, placa_chaflan] :
    modo != "bisectriz" ? [0, 0] :
    let (parte = ang_vertice(i) * (fin ? reparto_rincon : 1 - reparto_rincon))
    [max(0, fondo/tan(parte) - retiro), fondo];

// El M4 de la lengueta de la bahia va por DEBAJO del riel 1U: es el unico
// hueco de la boca (ruling R3, ver _y_brida_bahia en el presupuesto).
function y_brida_bahia() =
    centros_rail_1u()[0].y - he_er_y(90) - 1 - 1.5*d_M4_paso;

// La placa del valle es mas honda que las de 3U porque ademas recibe esas dos
// lenguetas: llega 1.5 D por debajo de su M4.
function placa_1u_fondo() =
    pts_perfil()[3].y - (y_brida_bahia() - 1.5*d_M4_paso);

// [nombre, A, u, n, s0, s1, fondo, cortes, ejes]. A es el vertice de arranque
// del tramo; un punto de la placa es A + u*s + n*b. `ejes` lleva, por cada
// riel que recoge, [s del eje, punto, si lleva sus dos roscas ciegas].
function placas() =
    let (P = pts_perfil(), cr = centros_rail(), c1u = centros_rail_1u())
    [for (t = tramos_placa())
        let (A = P[t[1]], B = P[t[2]], L = norm(B - A),
             u = (B - A)/L, n = [u.y, -u.x],
             s0 = retiro_placa(t[1]) + t[5][0],
             s1v = L - retiro_placa(t[2]) - t[5][1],
             tres = len(t[3]) > 0,
             centros = tres ? [for (i = t[3]) cr[i]] : c1u,
             // LA SEGUNDA 1U NO LLEVA ROSCAS y no es un olvido: radio_valle
             // vale 54 y curva la franja del valle -- su fondo util pasa de
             // 8.51 en x=128 a 12.45 en x=148 --, asi que una broca puesta
             // ahi sale por la pared del rebaje.
             ejes = [for (k = [0 : len(centros) - 1])
                        [(centros[k] - A)*u, centros[k], tres || k == 0]],
             // la placa del valle se alarga hasta cubrir el cajeado de su
             // segundo riel, que cae PASADO P3; puede pasarse porque ese
             // vertice es concavo y el redondeo aparta ahi el contorno
             s1 = tres ? s1v
                       : max(s1v, max([for (e = ejes) e[0]]) + 2*d_M4_paso),
             fondo = tres ? placa_fondo : placa_1u_fondo())
        [t[0], A, u, n, s0, s1, fondo,
         [corte_placa(t[1], fondo, s0, t[4][0], false),
          corte_placa(t[2], fondo, L - s1, t[4][1], true)],
         ejes]];

// Las esquinas de la placa con sus dos esquinas hondas ya cortadas. Un corte
// de bisectriz se lleva el fondo entero (db = fondo) y entonces su vertice de
// arriba coincide con el del canto: se omite, que una arista de largo cero
// rompe el SAT del presupuesto y no le gusta a polygon().
function esquinas_placa(pl) =
    let (A = pl[1], u = pl[2], n = pl[3], s0 = pl[4], s1 = pl[5], f = pl[6],
         c0 = pl[7][0], c1 = pl[7][1],
         ab = concat([[s0, 0]],
                     c1[0] <= 0 ? [[s1, 0], [s1, f]] :
                     c1[1] >= f ? [[s1, 0], [s1 - c1[0], f]]
                                : [[s1, 0], [s1, f - c1[1]], [s1 - c1[0], f]],
                     c0[0] <= 0 ? [[s0, f]] :
                     c0[1] >= f ? [[s0 + c0[0], f]]
                                : [[s0 + c0[0], f], [s0, f - c0[1]]]))
    [for (q = ab) A + u*q[0] + n*q[1]];

// La brida de extremo de los dos miembros traseros. Regla de chapa: el
// agujero no entra en la zona del doblez (setback + 2t + radio).
function brida_raiz() = radio_doblez_costilla + 3*t_costilla + d_M4_paso/2;
function brida_xs() = [miembro_x_trasera() - brida_raiz(),
                       miembro_x_trasera() - brida_largo + 1.5*d_M4_paso];
function bridas_anillo() =
    let (P = pts_perfil(), xs = brida_xs())
    concat([for (x = xs) [x, P[0].y + dist_rosca_ciega]],
           [for (x = xs) [x, P[5].y - dist_rosca_ciega]]);

// [centro, diametro de broca] de cada rosca ciega de la cara interior. Las de
// la TABLA no estan: van en el CANTO inferior del anillo, no en el dorso, y
// un DXF de la cara no sabe dibujar un taladro que entra por el canto (van en
// el pliego, Tarea 5). Las de la bahia y la pestana del valle tampoco: esas
// se roscan en los 6 mm de la placa del valle, no en el anillo (ruling R3).
function centros_rosca_ciega() =
    concat([for (pl = placas(), c = roscas_placa(pl)) [c, d_M4_rosca]],
           [for (c = bridas_anillo()) [c, d_M4_rosca]],
           [for (c = roscas_clips()) [c, d_M4_rosca]]);

// Hasta donde llega una rosca a la profundidad de dist_rosca_ciega sin
// acercarse a un extremo de la placa mas de 1.6 D. El margen NO es s1 - s
// cuando ese extremo va cortado: el corte entra en diagonal y se come mas de
// lo que parece -- 3.11 mm en la placa de la cara inferior, a esa altura.
// 1.6 D y no 1.5 porque la puerta exige 1.5, y una cota puesta justo en el
// limite de su propia puerta vive del redondeo de coma flotante.
function limite_rosca(pl, ext, corte, signo) =
    let (f = pl[6], d = dist_rosca_ciega, canto = 1.6*d_M4_paso,
         ds = corte[0], db = corte[1])
    (ds <= 0 || d <= f - db)
        ? ext + signo*canto
        : ext + signo*(ds*(d - (f - db))/db + canto*norm([ds, db])/db);

// EL PAR SE ARRIMA A SU RIEL PERO NO SE SALE DE LA PLACA. La regla en crudo
// -- eje +- sep_rosca_riel -- deja la rosca del riel del frente a 1.01 mm del
// canto, porque ese riel arranca casi pegado al vertice P1.
function centro_par_rosca(pl, e) =
    let (lo = limite_rosca(pl, pl[4], pl[7][0],  1),
         hi = limite_rosca(pl, pl[5], pl[7][1], -1))
    min(max(e[0], lo + sep_rosca_riel), hi - sep_rosca_riel);

function roscas_placa(pl) =
    [for (e = pl[8], q = [-sep_rosca_riel, sep_rosca_riel]) if (e[2])
        pl[1] + pl[2]*(centro_par_rosca(pl, e) + q) + pl[3]*dist_rosca_ciega];

// El M3 con el que la pestana de la banda del valle se atornilla a la placa.
function m3_pestana() = [pv_x(), pts_perfil()[3].y - pv_a()];

// Lo que se rosca EN la placa del valle y no en el anillo (ruling R3): el M3
// de cada pestana de la banda y el M4 de cada lengueta de la bahia. Van a
// diametro de broca y de lado a lado -- 6 mm de pletina dan rosca de sobra
// para un M3 y un M4, y roscar pasante es lo que el taller prefiere.
function roscas_placa_valle() =
    concat([[m3_pestana(), d_M3_rosca]],
           [for (s = [0, 1])
               [[s == 0 ? bahia_x0() + brida_raiz()
                        : bahia_x1() - brida_raiz(), y_brida_bahia()],
                d_M4_rosca]]);

// La placa, en 3D: sobre la cara interior del anillo, con los pasos M4 a sus
// roscas ciegas y, por cada riel que recoge, el paso del M4 del riel con su
// cajeado POR EL LADO DEL ANILLO -- ahi va la cabeza, y por eso la placa mide
// 6: debajo de ella hay acrilico hasta z = 13.2 y una cabeza que asome lo
// pinza. Orden de montaje: primero el riel a la placa, despues la placa al
// anillo. Al reves no se puede apretar.
module placa_riel(pl) {
    translate([0, 0, t_anillo]) difference() {
        linear_extrude(t_placa) polygon(esquinas_placa(pl));
        for (c = roscas_placa(pl))
            translate(concat(c, [-0.1]))
                cylinder(h = t_placa + 0.2, d = d_M4_paso + kerf);
        for (e = pl[8]) {
            translate(concat(e[1], [-0.1]))
                cylinder(h = t_placa + 0.2, d = d_M4_paso + kerf);
            translate(concat(e[1], [-0.1]))
                cylinder(h = prof_cajeado_riel + 0.1, d = d_cajeado_riel);
        }
        if (pl[0] == "valle")
            for (r = roscas_placa_valle())
                translate(concat(r[0], [-0.1]))
                    cylinder(h = t_placa + 0.2, d = r[1]);
    }
}

// Seis placas: tres por costado, espejadas.
module placas_riel() {
    for (pl = placas())
        for (m = [0, 1])
            translate([0, 0, m ? ancho_total : 0])
                mirror([0, 0, m])
                    placa_riel(pl);
}

// --- LOS DXF DE LAS PLACAS (Tarea 6, item del controller) ---------------
//
// EL LADO ESPEJADO NO PIDE UN DXF PROPIO. mirror([0,0,1]) es una reflexion
// en Z: no toca x ni y, y esquinas_placa() vive enteramente en el plano xy
// del perfil. O sea que las placas de los dos costados comparten el MISMO
// contorno -- una placa por TRAMO, no por costado -- y el pedido de corte va
// "x2" en la linea del BOM en vez de duplicar el fichero.
//
// EN COORDENADAS DEL ANILLO, sin transformar a un marco local por placa: las
// mismas x,y que esquinas_placa()/roscas_placa() ya usan. Se elige a
// proposito para que taladros_placas() en check_dxf.py compare centro a
// centro contra _esquinas_placa()/_roscas_placa() de clearance_budget.py sin
// deshacer ningun giro ni desplazamiento -- la MISMA razon por la que
// costilla_2d()/costilla_dorso_2d() tampoco usan un marco local.
//
// EL DXF LLEVA EL AGUJERO QUE FUNCIONA, no el mayor de los dos que
// placa_riel() corta en 3D. FIX ROUND 1 (Tarea 6): la primera version de
// este modulo dibujaba aqui el CAJEADO (d_cajeado_riel = 8, bolsillo de
// prof_cajeado_riel = 2.5 por el lado del anillo) en el eje de cada riel, y
// se dejaba fuera el agujero de PASO M4 que de verdad atraviesa la placa y
// por donde entra el tornillo del riel. Cortada tal cual, la cabeza del
// tornillo cae dentro de un agujero de 8 mm sin nada que la tope y el riel
// no queda atornillado a nada -- pieza inservible, no una pieza distinta.
// Lo caza taladros_placas() en check_dxf.py. PLIEGO.md (S6) documenta las
// DOS mitades del agujero: el paso M4 funcional, que el DXF SI dibuja, y el
// cajeado de Ø8 x 2.5 por el lado del anillo, que el DXF NO dibuja (va como
// NOTA DE MECANIZADO) -- la version anterior de este modulo dibujaba
// exactamente al reves: el cajeado si, el paso M4 no.
//
// EL CAJEADO NO SE DIBUJA AQUI, y no es un descuido: un DXF 2D no sabe
// decir "a 2.5 mm de profundidad" -- el mismo caso que el rebaje de
// costilla_dorso_2d y el cajeado KONDOR (ver esos modulos). Va como NOTA DE
// MECANIZADO en el pliego (Ø8 x prof_cajeado_riel, centrado en cada paso M4
// de riel, por la cara que mira al anillo), no como corte en este fichero.
module placa_2d(pl) {
    difference() {
        polygon(esquinas_placa(pl));
        for (c = roscas_placa(pl))
            translate(c) circle(d = d_M4_paso + kerf);
        for (e = pl[8])
            translate(e[1]) circle(d = d_M4_paso + kerf);
        // SOLO LA PLACA DEL VALLE: el M3 de la pestana de la banda y el M4
        // de cada lengueta de la bahia, los DOS que roscas_placa_valle()
        // rosca PASANTE en la propia placa (ruling R3) y no en el anillo.
        if (pl[0] == "valle")
            for (r = roscas_placa_valle())
                translate(r[0]) circle(d = r[1]);
    }
}

// Busca el tramo por nombre en vez de indexar placas()[i]: si algun dia
// tramos_placa() cambia de orden, un indice fijo exportaria la placa
// equivocada bajo el nombre equivocado sin que nada lo avise.
function _placa(nombre) = [for (pl = placas()) if (pl[0] == nombre) pl][0];

module placa_cara_inf_2d() { placa_2d(_placa("cara_inf")); }
module placa_valle_2d()    { placa_2d(_placa("valle")); }
module placa_cara_sup_2d() { placa_2d(_placa("cara_sup")); }

// --- LOS CLIPS DE RETENCION DEL ACRILICO -------------------------------
//
// EL REBAJE SUJETA UNA SOLA CARA. El labio de 3 mm pisa el acrilico por
// DELANTE: tirar del costado no lo mueve. Empujarlo hacia DENTRO si -- entre
// la cara del PMMA (z = rehundido + t_cheek = 11) y la cara interior del
// anillo (z = t_anillo = 14) hay aire, y por ahi el costado se sale del
// rebaje. Estos clips son el TOPE de ese lado.
//
// SON TOPE Y NO PRECARGA, y la diferencia importa al montarlo: la precarga la
// da la junta de asiento contra el labio, que es lo que quita el traqueteo. El
// clip se queda a 3 mm de la cara del PMMA en nominal y a 0.8 en el peor
// apilado de tolerancias (z = 13.2, la cuenta esta en guarda_anclajes). O sea
// que en reposo NO toca el acrilico: solo aparece cuando alguien empuja.
//
// LOS CUATRO TRAMOS SIN PLACA son el frente bajo, la meseta, la trasera y el
// suelo -- en los otros tres la placa de anclaje corre el tramo entero y ya
// hace de tope --, y de esos cuatro SOLO EL SUELO tiene franja libre donde
// atornillar. El por que de cada uno esta en TRAMOS_CLIP, en
// clearance_budget.py, con los milimetros que quedan en cada sitio.
//
// GEMELO de _clips(), _cajas_clip() y _roscas_clips() en clearance_budget.py;
// los cruza taladros_anillo() releyendo el DXF del dorso.

// [nombre del tramo, vertice de arranque, vertice de fin, s del centro sobre
// el tramo]. Quien decide la lista es guarda_costado() en check_dxf.py.
function tramos_clip() = [["suelo", 6, 0, 50], ["suelo", 6, 0, 150]];

// [nombre, esquinas, centro de la rosca ciega]. Misma convencion que
// placas(): A el vertice de arranque, u a lo largo del tramo y n hacia dentro.
function clips() =
    let (P = pts_perfil())
    [for (t = tramos_clip())
        let (A = P[t[1]], B = P[t[2]], L = norm(B - A),
             u = (B - A)/L, n = [u.y, -u.x],
             s0 = t[3] - clip_largo/2, s1 = t[3] + clip_largo/2)
        [str(t[0], " ", t[3]),
         [A + u*s0, A + u*s1, A + u*s1 + n*clip_fondo, A + u*s0 + n*clip_fondo],
         A + u*t[3] + n*dist_rosca_ciega]];

function roscas_clips() = [for (c = clips()) c[2]];

// El clip, en 3D: sobre la cara interior del anillo, con el paso de su M4. La
// cabeza queda a la vista por dentro y no estorba a nadie -- aqui no hay nada
// apoyado encima, al reves que en la placa del riel.
module clips_costado() {
    for (c = clips())
        for (m = [0, 1])
            translate([0, 0, m ? ancho_total : 0])
                mirror([0, 0, m])
                    translate([0, 0, t_anillo])
                        difference() {
                            linear_extrude(t_clip) polygon(c[1]);
                            translate(concat(c[2], [-0.1]))
                                cylinder(h = t_clip + 0.2, d = d_M4_paso + kerf);
                        }
}

// El DXF del clip (Tarea 6, item del controller): pieza GENERICA, no una
// por tramo ni por s -- clips() coloca CUATRO (dos tramos x dos costados
// espejados) pero los cuatro son el mismo rectangulo de clip_largo x
// clip_fondo con un M4 centrado a dist_rosca_ciega de un canto, asi que un
// solo DXF basta y se corta x4 (BOM). Dibujado en su propio marco local
// (0,0)-(clip_largo, clip_fondo), no en coordenadas del anillo como las
// placas: al reves que ellas, este contorno no depende de en que tramo ni a
// que s vaya el clip, asi que no hay un "clip()" concreto contra el que
// comparar -- check_dxf.py lo verifica contra clip_largo/clip_fondo/
// dist_rosca_ciega sueltos, los mismos parametros con que _clips() arma
// cada instancia.
module clip_2d() {
    difference() {
        square([clip_largo, clip_fondo]);
        translate([clip_largo/2, dist_rosca_ciega]) circle(d = d_M4_paso + kerf);
    }
}

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

// --- LA BRIDA DE EXTREMO, en el desarrollo ------------------------------
// Lo que la lengueta sobresale del recorte una vez descontado su doblez, y
// donde cae en el blank un punto que en la pieza montada esta a profundidad d
// del pliegue. Misma pareja de cuentas que pv_vuelo()/pv_desarrollo() para la
// pestana del valle, con los parametros de ESTA chapa.
function brida_vuelo_dsr() = brida_largo - miembro_bd();
function brida_dsr(d) = miembro_bd() - d;

// La lengueta tumbada: un rectangulo pegado a cada punta del recorte, dentro
// de la banda del alma. Se dobla sobre una linea PERPENDICULAR al canto del
// anillo -- por eso su largo corre a lo largo del canto -- y lleva relieve en
// las dos esquinas, que en el desarrollo es el propio hueco entre bandas.
module brida_2d(y_centro, ancho, vuelo = 0) {
    v = vuelo > 0 ? vuelo : brida_vuelo_dsr();
    for (lado = [0, 1])
        translate([lado ? ancho_util : -v, y_centro - ancho/2])
            square([v, ancho]);
}

// Sus dos M4 de paso: uno a brida_raiz() del pliegue (regla de chapa) y otro
// a 1.5 D del canto libre. dy desplaza la fila respecto al centro de la banda.
module brida_agujeros_2d(y_centro, dy) {
    for (lado = [0, 1], d = [brida_raiz(), brida_largo - 1.5*d_M4_paso])
        translate([lado ? ancho_util - brida_dsr(d) : brida_dsr(d),
                   y_centro + dy])
            circle(d = d_M4_paso + kerf);
}

// El solido de una brida: chapa plana contra la cara que la recibe.
module brida_3d(x0, y0, ancho_x, ancho_y, z0, largo) {
    for (z = [z0, z0 + largo - t_costilla])
        translate([x0, y0, z]) cube([ancho_x, ancho_y, t_costilla]);
}

// --- LA ESCUADRA DE LA TRASERA: el tope del canto trasero del costado ---
//
// El por que entero esta en params.scad, en el bloque de escuadra_ala. En
// corto: el canto TRASERO del acrilico corria 227 mm sin un solo tope hacia
// dentro -- ahi no cabe clip -- y este angular se lo pone. Va atornillado a la
// TRASERA, no al anillo.
//
// LAS DOS ALAS, y cual es cual:
//   ala A  la que se atornilla. Plana contra la cara interior de la trasera
//          (x = miembro_x_trasera()), de escuadra_ala de ancho en z desde la
//          cara interior del anillo hacia dentro, con sus M3 pasantes.
//   ala B  el TOPE. Perpendicular, tumbada sobre el plano de la cara interior
//          del anillo (z = t_anillo .. t_anillo + t_costilla), volando hacia
//          -x hasta la linea de la ventana.
//
// ES TOPE CON CARRERA, como los clips, y por la misma razon: la precarga la
// pone la junta de asiento contra el labio. El ala B se queda a 3 mm de la
// cara del PMMA en nominal y a 0.8 en el peor apilado de tolerancias
// (z = 13.2); en reposo NO toca el acrilico, solo aparece cuando alguien
// empuja el costado hacia dentro. Y no toca el anillo: arranca exactamente en
// su cara interior, con cero solape.
//
// GEMELA de _escuadras_trasera(), _cajas_escuadra() y _centros_m3_escuadra()
// en clearance_budget.py; la puerta es guarda_escuadra_trasera().

// El vuelo del ala B, medido desde la cara interior de la trasera. DERIVADO:
// su punta muere en la linea de la ventana del anillo (silueta - cara_anillo),
// asi que por dentro pisa exactamente el acrilico que el labio pisa por fuera
// y nada de lo que se ve. Con cara_anillo 20 y t_piel 8 son 12 mm, que pasan
// el canto del acrilico en rebaje_anillo - hol_costado = 5.5.
function escuadra_vuelo() = cara_anillo - t_piel;
// Regla de chapa, la misma de brida_raiz() con el diametro del M3: el agujero
// no entra en la zona del doblez. Setback + 2t + radio del agujero.
function escuadra_raiz() = radio_doblez_costilla + 3*t_costilla + d_M3_paso/2;
// Y donde cae ese mismo M3 en el DXF de la TRASERA, medido desde su canto: la
// plancha arranca hol_piel mas adentro que la cara interior del anillo, que es
// el origen desde el que se mide la raiz.
function escuadra_m3_x() = escuadra_raiz() - hol_piel;
// Y HASTA DONDE TAPA ESA ALA, en el plano de la trasera y medido desde su
// canto. Mismo cambio de origen que escuadra_m3_x(): la plancha arranca
// hol_piel mas adentro que la cara interior del anillo. Lo consume
// rejilla_entrada(), que se salta las columnas que caigan aqui debajo -- una
// ranura con 1.5 mm de aluminio encima no ventila, y guarda_aire() no puede
// seguir contandola como area abierta.
function escuadra_tapa() = escuadra_ala - hol_piel;

// El largo corre entre las dos BRIDAS de los miembros traseros, retirado
// escuadra_retiro de cada una: viven en la misma rebanada de z que el ala B.
function escuadra_y0() = canal_ancho + escuadra_retiro;
function escuadra_y1() = miembro_y_meseta() - canal_ancho - escuadra_retiro;
function escuadra_largo() = escuadra_y1() - escuadra_y0();

// LOS M3 NO SE REPARTEN POR TODA EL ALA, y esto es lo unico de esta pieza que
// no sale de una regla de chapa. El ala A ocupa los primeros escuadra_ala mm
// de la trasera contados desde su canto, y ahi CAIA la primera columna de la
// rejilla de entrada (2 HP = 10.16 del canto): dentro de la banda no quedaba x
// legal, porque entre dos columnas hay 6.16 mm de acrilico y dos margenes de
// 1.5 D piden 10.2.
//
// DESDE LA REVISION DE LA TAREA 4b ESA COLUMNA YA NO SE CORTA -- la tapaba el
// ala y guarda_aire() la estaba contando como area abierta --, o sea que hoy
// SI cabria un M3 ahi: la ranura mas cercana pasa a estar a 20.32 del canto y
// deja 9.27 mm de aire. Los tornillos se quedan igual por encima de la banda, y
// no por inercia: la columna solo desaparece MIENTRAS el ala la tape, asi que
// bajar un tornillo a ese hueco ataria la escuadra a su propia sombra -- el dia
// que escuadra_ala baje de 14.3 la columna vuelve y el tornillo queda dentro de
// una ranura sin que nada lo cante. Con tres por encima el voladizo de abajo
// trabaja a 89.8 MPa contra los 130 del aluminio, asi que no hace falta.
// Lo comprueba guarda_escuadra_trasera() tornillo a tornillo, y ademas mide
// ese voladizo como viga.
function escuadra_m3_y() =
    let (y0 = max(escuadra_y0(),
                  banda_libre_trasera()[1] + 1.5*d_M3_paso),
         e  = (escuadra_y1() - y0)/escuadra_m3)
    [for (i = [0 : escuadra_m3 - 1]) y0 + e*(i + 0.5)];

// El desarrollo: las dos alas por su cota EXTERIOR menos un BD, la misma
// cuenta que la brida y que la pestana del valle.
function escuadra_desarrollo() = escuadra_ala + escuadra_vuelo() - miembro_bd();

// El DXF es el DESARROLLO, como el de los tres miembros. La linea de doblez es
// y = 0: por encima queda el ala A con su cota exterior entera, por debajo el
// ala B ya descontado su BD.
module escuadra_trasera_2d() {
    translate([0, -(escuadra_vuelo() - miembro_bd())])
        difference() {
            square([escuadra_largo(), escuadra_desarrollo()]);
            for (y = escuadra_m3_y())
                translate([y - escuadra_y0(),
                           escuadra_vuelo() - miembro_bd() + escuadra_raiz()])
                    circle(d = d_M3_paso + kerf);
        }
}

// Las dos escuadras dobladas y puestas. El ala B se dibuja hasta la cara
// INTERIOR del ala A y no hasta la trasera: el rincon del doblez es material
// del ala A, y contarlo dos veces haria que la pieza se solapara consigo misma
// en el censo de solapes().
module escuadras_trasera() {
    x_int = miembro_x_trasera();
    for (m = [0, 1])
        translate([0, 0, m ? ancho_total : 0])
            mirror([0, 0, m]) {
                difference() {
                    translate([x_int - t_costilla, escuadra_y0(), t_anillo])
                        cube([t_costilla, escuadra_largo(), escuadra_ala]);
                    for (y = escuadra_m3_y())
                        translate([x_int - t_costilla - 0.1, y,
                                   t_anillo + escuadra_raiz()])
                            rotate([0, 90, 0])
                                cylinder(h = t_costilla + 0.2,
                                         d = d_M3_paso + kerf);
                }
                translate([x_int - escuadra_vuelo(), escuadra_y0(), t_anillo])
                    cube([escuadra_vuelo() - t_costilla, escuadra_largo(),
                          t_costilla]);
            }
}

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
        union() {
            square([ancho_util, desarrollo]);
            // la brida sale del ALMA, que es la cara que llega al canto
            // inferior del anillo (y = 0 del perfil)
            brida_2d(y_alma, canal_ancho);
        }
        fila_agujeros(ancho_util, y_alma);
        brida_agujeros_2d(y_alma, dist_rosca_ciega - canal_ancho/2);
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
        union() {
            square([ancho_util, desarrollo]);
            brida_2d(y_alma, canal_ancho);
        }
        fila_agujeros(ancho_util, y_alma);
        // La brida de arriba ancla en la MESETA del perfil (y = P5.y), que
        // pasa marco_sup por encima del canto del alma: de ahi el desfase.
        brida_agujeros_2d(y_alma,
                          marco_sup + canal_ancho/2 - dist_rosca_ciega);
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
// Los centros de las lenguetas de la bahia en el DESARROLLO: una por ala y por
// punta. La banda de cada ala corre del pliegue del suelo hacia fuera, asi que
// la profundidad del M4 dentro del ala se mide desde bahia_y0().
function bahia_ala_dsr() = bahia_alto - miembro_bd();
function bahia_brida_y(desarrollo, banda) =
    let (prof = y_brida_bahia() - bahia_y0())
    banda == 0 ? bahia_ala_dsr() - prof
               : desarrollo - bahia_ala_dsr() + prof;

module bahia_2d() {
    // La cota delantera la manda el BARRIDO del riel inferior, no su esquina
    // quieta. El contrato Python ya usa esta misma resta (48.18 mm).
    suelo = bahia_x1() - bahia_x0();
    desarrollo = suelo + 2*bahia_alto - 2*miembro_bd();
    y_suelo = bahia_alto + suelo/2 - miembro_bd();
    ala = bahia_ala_dsr();
    vuelo = brida_bahia_vuelo - miembro_bd();
    ancho_l = 3*d_M4_paso;                 // 1.5 D a cada lado del M4
    difference() {
        union() {
            // LAS DOS ALAS ACABAN t_placa ANTES DEL ANILLO (ruling R3): en la
            // boca no queda franja libre, la ocupa entera la placa de la fila
            // 1U. El SUELO no se recorta -- corre 62 mm por debajo del valle,
            // lejos de la placa -- y por eso su reticula sigue midiendo
            // ancho_util como la de los otros dos miembros.
            difference() {
                square([ancho_util, desarrollo]);
                for (lado = [0, 1], banda = [0, 1])
                    translate([lado ? ancho_util - t_placa : 0,
                               banda == 0 ? 0 : desarrollo - ala])
                        square([t_placa, ala]);
            }
            for (lado = [0, 1], banda = [0, 1])
                translate([lado ? ancho_util - t_placa
                                : t_placa - vuelo,
                           bahia_brida_y(desarrollo, banda) - ancho_l/2])
                    square([vuelo, ancho_l]);
        }
        fila_agujeros(ancho_util, y_suelo);
        for (lado = [0, 1], banda = [0, 1])
            translate([lado ? ancho_util - t_placa - brida_dsr(brida_raiz())
                            : t_placa + brida_dsr(brida_raiz()),
                       bahia_brida_y(desarrollo, banda)])
                circle(d = d_M4_paso + kerf);
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
    // las dos bridas, planas contra la franja del canto INFERIOR del anillo
    brida_3d(x1 - brida_largo, 0, brida_largo, canal_ancho, z0, ancho_util);
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
    // las dos bridas, planas contra la franja de la MESETA del anillo
    brida_3d(x1 - brida_largo, y0, brida_largo, canal_ancho, z0, ancho_util);
}

module bahia() {
    x0 = bahia_x0();
    x1 = bahia_x1();
    y0 = bahia_y0();
    y1 = bahia_y1();
    z0 = miembros_z0();
    // el SUELO cruza entero; las dos ALAS mueren t_placa antes del anillo
    // contra la placa de la fila 1U (ruling R3) y doblan ahi su lengueta.
    za = z0 + t_placa;
    la = ancho_util - 2*t_placa;
    translate([x0, y0, z0])
        cube([x1 - x0, t_costilla, ancho_util]);
    for (x = [x0, x1 - t_costilla])
        translate([x, y0, za])
            cube([t_costilla, y1 - y0, la]);
    ancho_l = 3*d_M4_paso;
    for (s = [0, 1])
        brida_3d(s == 0 ? x0 : x1 - brida_bahia_vuelo,
                 y_brida_bahia() - ancho_l/2,
                 brida_bahia_vuelo, ancho_l, za, la);
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
        for (wx = [alto_frontal/2 + d_pie/2, centro_miembro_bajo().x])
            for (wz = [d_pie/2, ancho_total - d_pie/2])
                translate([v + wz, v + wx])
                    circle(d = d_pie_tornillo + kerf);
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

// La onda de abajo, que es la frontera de arriba de la banda libre.
function trasera_y_bajas() =
    anclaje_piel_base().y
    + 0.37*(anclaje_piel_remate().y - anclaje_piel_base().y);

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
function banda_libre_trasera() =
    [anclaje_piel_base().y + valle_espina/2 + vent_puente_min,
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
        plancha(au, alto);
        for (y = [f_base, f_tras]) fila_agujeros(au, y);
        // LOS SEIS M3 DE LAS DOS ESCUADRAS, tres por costado. No son de fila:
        // van en columna a escuadra_m3_x() del canto de la plancha, que es la
        // raiz del doblez de la escuadra menos el aire con que esta plancha se
        // empotra. Son PASANTES con tuerca por dentro -- la escuadra no rosca
        // en el anillo -- y por eso salen aqui, en el DXF de la trasera, y no
        // en el del dorso del anillo.
        for (lado = [0, 1], y = escuadra_m3_y())
            translate([lado ? au - escuadra_m3_x() : escuadra_m3_x(), y])
                circle(d = d_M3_paso + kerf);
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
    // Y SE SALTAN TAMBIEN LAS COLUMNAS QUE EL ALA A DE LA ESCUADRA TAPARIA,
    // desde el 2026-08-28. La escuadra ocupa los primeros escuadra_tapa() mm
    // de la plancha contados desde cada canto, y ahi caia la primera columna
    // (2 HP = 10.16, ranura de 8.16 a 12.16): el 82 % de su largo quedaba
    // debajo de 1.5 mm de aluminio. Cortarla era lo peor de las dos cosas --
    // no ventilaba, pero guarda_aire() la contaba como area abierta y ademas
    // dejaba entrar polvo por el sobrante. Se salta ENTERA y no a medias: una
    // ranura tapada en cuatro quintos no es un campo de ventilacion, es un
    // hueco debil en el acrilico. La cuenta sale del ala, no de un indice a
    // mano: el dia que escuadra_ala crezca, la siguiente columna se cae sola.
    tapa = escuadra_tapa();
    for (n = [valle_paso_hp : valle_paso_hp : n_hp - valle_paso_hp])
        if (abs(n*hp - x_iec) >= hueco
            && n*hp - vent_ancho_ranura/2 >= tapa
            && n*hp + vent_ancho_ranura/2 <= au - tapa)
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

// LA BANDA MUERE CONTRA LAS PLACAS DEL VALLE, no contra el anillo, desde el
// 2026-08-28: mide lo mismo que un riel y sus dos pestanas apoyan planas
// sobre la cara interior de esa placa, con un M3 roscado EN ella. Su rosca no
// cabe en la franja del anillo -- el M3 cae a pv_a() = 13.7 por debajo del
// plano del valle y la franja de 14 solo admite hasta 10.25 --, y en la boca
// tampoco hay franja libre: la ocupa la propia placa. Es el mismo ruling R3
// que cuelga la bahia de esa misma pletina.
// Los 6 mm que la banda deja libres en cada punta NO son un hueco: ahi esta el
// canto de la placa, a ras del plano del valle.
function tapa_valle_au() = ancho_util - 2*t_placa;

module tapa_valle_2d() {
    au = tapa_valle_au();
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
else if (PART == "escuadra_trasera_2d")  escuadra_trasera_2d();
else if (PART == "placa_cara_inf_2d")    placa_cara_inf_2d();
else if (PART == "placa_valle_2d")       placa_valle_2d();
else if (PART == "placa_cara_sup_2d")    placa_cara_sup_2d();
else if (PART == "clip_2d")              clip_2d();
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
    // LAS SEIS PLACAS DE ANCLAJE. Entran el 2026-08-28 con el anillo fresado:
    // son lo unico que ata los seis rieles al case, y van por la cara
    // INTERIOR -- en el render apenas se ven asomar por el canto de la
    // ventana, que es exactamente lo que se busca. Si alguna se viera por
    // fuera, el anclaje estaria mal puesto.
    placas_riel();
    // LOS CUATRO CLIPS DE RETENCION, dos por costado sobre el canto de abajo.
    // Van en la cara INTERIOR igual que las placas y por la misma razon:
    // desde fuera no se ve ninguno, y si se viera es que esta mal puesto.
    clips_costado();
    // LAS DOS ESCUADRAS DE LA TRASERA. Entran el 2026-08-28 y son el tope del
    // canto TRASERO del acrilico, que hasta hoy corria 227 mm sin ninguno.
    // Tampoco se ven desde fuera -- van por dentro de la trasera --: lo unico
    // que la vista de atras ensena de ellas son sus tres M3 por costado, en
    // linea vertical cerca del canto.
    escuadras_trasera();
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
             " x 45 grados en las dos aristas de la cara vista."));
    echo(str("     NINGUN TORNILLO ATRAVIESA LA CARA VISTA: ",
             len(centros_rosca_ciega()), " roscas ciegas M4 en la cara",
             " interior (taladros_anillo, broca ", d_M4_rosca,
             ") + 3 M5 por anillo en el CANTO inferior para la tabla (ver",
             " esa linea, no salen en el mismo DXF). CERO casquillos, CERO",
             " junta de 4 mm."));
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
    echo(str("BOM: MIEMBRO de chapa x", len(centros_transversal()),
             " -- trasero bajo, trasero alto y bahia: canal de aluminio",
             " 6082-T6 de ", t_costilla, " mm, ", au,
             " mm de largo, con BRIDA de extremo doblada en cada punta y",
             " roscada al anillo con M4 ciegos."));
    echo("     Fueron perfil 2020 comprado hasta el 2026-08-27; el eco");
    echo("     seguia llamandolos asi de puro heredado, corregido aqui. Son");
    echo("     tres: trasero bajo, trasero alto y bahia (el valle). Fueron");
    echo("     CUATRO hasta esa fecha -- se fue `base delantera`, la unica");
    echo("     que flotaba en mitad del suelo. Los tres que quedan van");
    echo("     arrinconados contra dos caras cada uno, o sostienen una");
    echo("     plancha que nada mas alcanza (el valle).");
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
    echo("     anillo con roscas ciegas M4 (ver esa linea). Largo: no lo");
    echo("     fija el modelo -- lo fija el pliego, contando el cajeado de");
    echo("     la placa y la rosca util del anillo.");
    echo(str("BOM: PLACA DE ANCLAJE x", 2*len(placas()), " -- pletina de ",
             t_placa, ", una por TRAMO y por costado. Es el MARCO DE LA FILA:",
             " corre el tramo entero y su canto de ", t_placa,
             " tapa la ranura que queda entre el riel de 104 HP y el anillo."));
    echo(str("     Fondo ", placa_fondo, " las dos de 3U y ", placa_1u_fondo(),
             " la del valle, que ademas recibe las dos lenguetas de la bahia.",
             " Cajeado de ", d_cajeado_riel, " x ", prof_cajeado_riel,
             " por el lado del anillo, uno por riel."));
    echo("     DXF de corte: placa_cara_inf_2d, placa_valle_2d y");
    echo(str("     placa_cara_sup_2d -- UNO por TRAMO, no por costado: el",
             " lado espejado (z) comparte el mismo contorno xy. Cada",
             " fichero se corta x2 (los ", 2*len(placas()),
             " de la linea de arriba, entre los tres)."));
    echo("     Cortes: en el PICO las dos placas vecinas se reparten el rincon");
    echo("     por una linea comun (no es un chaflan de 45: el angulo es 125);");
    echo(str("     en el remate la de arriba lleva un chaflan de ", placa_chaflan,
             " para librar la brida del miembro trasero alto."));
    echo("     ORDEN DE MONTAJE OBLIGADO: primero el riel a la placa (la");
    echo("     cabeza queda en el cajeado, del lado que despues mira al");
    echo("     anillo) y despues la placa al anillo, desde dentro. Al reves no");
    echo("     se puede apretar.");
    echo(str("BOM: tornillo M4 boton x", 2*len(bridas_anillo()),
             " -- por la PUNTA de los dos miembros traseros, a una BRIDA de",
             " extremo doblada de su propio blank y roscada al anillo. Desde el",
             " 2026-08-27 no atraviesan el acrilico y desde el 28 tampoco la",
             " costilla."));
    echo("     ERAN M5 (spec 5) y bajan a M4 el 2026-08-28. La franja del");
    echo("     anillo mide 14: un M5 pide 1.5 D de su agujero de paso (8.25)");
    echo("     al canto de la brida y 1.5 D de su broca (6.3) a la pared del");
    echo("     rebaje, y las dos no caben a la vez en 14. El M4 si: 6.75 y");
    echo("     4.95. La brida es chapa de 1.5 -- un M5 ahi estaba sobrado.");
    echo(str("BOM: ESCUADRA DE LA TRASERA x2 -- angular de la MISMA chapa que",
             " los miembros (6082-T6 de ", t_costilla, ", radio ",
             radio_doblez_costilla, "), desarrollo ", escuadra_largo(), " x ",
             escuadra_desarrollo(), ". Un ala de ", escuadra_ala,
             " atornillada a la cara interior de la TRASERA y otra de ",
             escuadra_vuelo(), " tumbada sobre la cara interior del anillo,",
             " que asoma sobre el canto trasero del costado y hace de tope."));
    echo("     Es lo que le faltaba a ese canto: 227 mm de acrilico sin nada");
    echo("     que lo parara hacia dentro. Va al taller de CHAPA con los tres");
    echo("     miembros y la banda del valle, no al de acrilico.");
    echo(str("BOM: tornillo M3 x", 2*escuadra_m3, " + tuerca -- las dos",
             " escuadras a la trasera, PASANTES por sus ", t_piel,
             " mm de PMMA, cabeza fuera y tuerca dentro. Mismo herraje que las",
             " dos filas que esa plancha ya lleva a los miembros."));
    echo("     NO HAY ROSCA CIEGA NUEVA EN EL ANILLO. La escuadra ancla en la");
    echo("     trasera a proposito: en la franja de 14 no cabe -- es la misma");
    echo("     cuenta que deja sin clip a ese tramo (ver TRAMOS_CLIP,");
    echo("     linea de abajo).");
    echo(str("BOM: CLIP DE RETENCION x", 2*len(clips()), " -- pletina de ",
             t_clip, " mm x ", clip_largo, " mm, un M4 ciego al anillo.",
             " Solo en el tramo del SUELO (2 por costado): TRAMOS_CLIP es",
             " el unico tramo sin placa de anclaje. Muerde ", clip_fondo,
             " mm de acrilico desde el canto de la ventana -- retiene el",
             " costado hacia DENTRO junto con las 3 placas y la escuadra",
             " de la trasera, por costado."));
    echo(str("     DXF de corte: clip_2d -- UNA pieza generica (", clip_largo,
             " x ", clip_fondo, " mm), se corta x", 2*len(clips()),
             ": el mismo contorno sirve a los dos tramos del suelo y a los",
             " dos costados."));
    echo(str("BOM: JUNTA DE ASIENTO EPDM x2 (una por anillo), ",
             t_junta_asiento, " mm -- perfil continuo en el rebaje, entre",
             " el labio y el costado. Nunca aluminio contra acrilico. No",
             " es la junta de 4 mm del apilado viejo (muerta el",
             " 2026-08-28): esta va EN EL PLANO del rebaje, no atravesada",
             " por ningun tornillo."));
    echo("BOM: tornillo M4 x4 -- las dos lenguetas de la BAHIA a la placa de");
    echo("     la fila 1U, roscados EN LA PLACA (6 mm de pletina). La bahia no");
    echo("     ancla al anillo: en su boca la franja la ocupa esa placa y los");
    echo("     dos Z-Rails 1U calzan a ras de sus alas, sin un milimetro libre.");
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
    // TRES filas de n_fila: dos de la TRASERA (trasero bajo + trasero alto,
    // cada miembro con su propia reticula) y una de la banda del valle, que
    // usa la reticula de la BAHIA (check_dxf: bahia_2d trae reticula de 5 M3
    // a paso 100, igual que los otros dos miembros). Mas 2 pestanas de la
    // misma banda, que van aparte a la placa del valle (ruling R3, no a la
    // bahia). Decia "tapa de remate" hasta el fix round 1 de la Tarea 5
    // (2026-08-28): esa pieza (`remate_sup`/`remate_sup_2d`) murio el
    // 2026-08-27 -- la meseta del techo paso a ser el ala del miembro
    // trasero alto -- y el eco la seguia contando de puro heredado.
    echo(str("BOM: tornillo M3 x", 3*n_fila + 2, " + tuerca T M3 -- las planchas",
             " a la reticula del miembro: trasera ", 2*n_fila, " (trasero bajo + alto), tapa del valle ",
             n_fila, " (a la bahia), + 2 de las PESTANAS de la tapa del valle."));
    echo("     LOS DOS DE LA PESTANA VAN A LA PLACA DEL VALLE, no al anillo:");
    echo("     su rosca tendria que caer a 13.7 mm del plano del valle");
    echo("     (setback 6 + 2t + d/2, y con t_valle = 3 esa cuenta no baja) y");
    echo("     la franja de 14 solo admite hasta 10.25 -- la broca saldria por");
    echo(str("     la pared del rebaje. En la placa hay ", t_placa,
             " mm de pletina y se rosca pasante, igual que las lenguetas de la",
             " bahia (ruling R3)."));
    echo("     Estos entran por la RANURA del miembro, no por su punta. Es donde");
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
    echo("        la PLACA DEL VALLE (la misma que reciben las lenguetas de");
    echo("        la bahia), no a la costilla. No son ejes ni cierres: no");
    echo("        giran, no se quitan a mano.");
    // Decia "x6 fijos: los largueros de esqueleto" bajo un encabezado que
    // habla de M4 DE RIEL, y esos largueros van con M5. Contaba dos herrajes
    // distintos en la misma lista. Los M4 de riel son DOCE: cuatro ejes,
    // cuatro cierres y cuatro fijaciones permanentes de la fila 1U.
    //
    // ESTOS DOCE NO SON TODOS LOS M4 DEL CASE -- fix round 1, Tarea 5: la
    // frase de aqui decia "no hay mas M4" a seis lineas de la brida (x8) y
    // el clip (x4), y se contradecia sola. Los de brida roscan al anillo y
    // ERAN M5 en el plan; bajaron a M4 el 2026-08-28 porque la franja de
    // 14 mm no admite a la vez el paso M5 y la broca M5 (ver esa linea).
    echo("     Estos 12 son los M4 DE RIEL. El case lleva mas M4 en otras");
    echo("     lineas de este BOM: brida de miembro x8, clip x4, lengueta de");
    echo("     bahia x4, placa a anillo x20 (ver README, BOM de herrajes).");
    echo("     Los tornillos de transversal y de la tabla son M5 y van");
    echo("     aparte.");
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
    // La tapa de remate (plancha acrilica horizontal atornillada al larguero
    // de remate trasero) murio el 2026-08-27: `remate_sup`/`remate_sup_2d`
    // sin llamador, borradas del .scad en el fix round 1 de la Tarea 5. La
    // meseta del techo es hoy el ala del miembro trasero alto (marco_sup,
    // ver params.scad), no una plancha aparte -- este echo la vendia sin
    // que existiera.
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
             " atornillada a la PLACA DEL VALLE con un M3 (no al anillo",
             " -- ruling R3, ver la linea del M3 x17)."));
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
    echo(str("BOM: plancha de acrilico t=", t_cheek, ": costados x2 y",
             " TRASERA -- 3 piezas."));
    echo("     UN SOLO ESPESOR en todo el cuerpo. Hubo dos hasta el 2026-08-25:");
    echo("     los 5 mm existian para UNA pieza, y esa pieza es ahora de");
    echo("     aluminio. Media plancha de 5 que ya no hay que comprar.");
    echo("     Y desde el 2026-08-27 el suelo tampoco es acrilico: es la tabla.");
    echo("     Y desde el 2026-08-27 la tapa de remate tampoco existe: la");
    echo("     meseta del techo es el ala del miembro trasero alto (4 piezas");
    echo("     hasta esa fecha, corregido en el fix round 1 de la Tarea 5).");
    echo("     LOS COSTADOS YA NO LLEVAN UN SOLO TALADRO. Son PIEL: asientan");
    echo("     en el rebaje del anillo, sin tornillo -- el labio los sostiene");
    echo("     hacia fuera y las placas/clips/escuadra hacia dentro.");
}
