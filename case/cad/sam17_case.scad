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
ancho_util = ancho_total - 2*t_cheek;

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
// base delantera, base trasera, entrepiso delantero, valle, remate trasero.
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
// entrepiso delantero reubicado (fix de solape, ronda de revision 1): el
// original P[3].x+r invadia el rail de panel de la cara superior
// (17.6x12.6 mm de solape, verificado). Ahora se apoya holgura_rail detras
// del borde trasero de ESE rail. Y de ambos railes de entrepiso baja a
// P3.y-t_acrilico-r para que la bandeja apoye con el CANTO SUPERIOR a ras
// de P3.y (antes apoyaba con el canto inferior ahi, dejando la tapa 5 mm
// por encima del plano de entrepiso).
//
// El SEPTIMO larguero, "zocalo superior", se retiro el 2026-08-17: Samuel
// pidio DOS nodos en la esquina de abajo y no tres -- uno para amarrar la
// estructura lateral con la vertical (base delantera) y otro solo para el
// riel del panel. Con el se fue la plancha del zocalo, que se habria quedado
// colgando de una sola fila de tornillos. El larguero habia nacido para dar
// a esa plancha un anclaje a rail DERECHO en vez de al de panel girado; sin
// plancha, el problema que resolvia deja de existir.
function centros_esqueleto() =
    let (P = pts_perfil(), r = rail/2, cr = centros_rail(),
         // Los DOS largueros traseros comparten X, y por eso esto es UNA
         // cota y no dos copias: la cara donde apoya la trasera tiene que ser
         // un plano, no dos planos parecidos. Se retiran t_piel (y no
         // t_acrilico: la trasera tiene su propio espesor desde el 2026-08-21)
         // para que la plancha atornillada encima remate EXACTAMENTE en el
         // plano trasero -- empotrada y a ras, sin rebaje y sin dejar de ser
         // un DXF plano.
         x_tr = fondo() - r - t_piel,
         x_ed = cr[2].x + he_er_x(angulo_superior) + holgura_rail + r,
         y_ep = P[3].y - t_acrilico - r)
    // Los dos largueros de la base ya NO viven en el canto de abajo. Desde que
    // la bandeja es el suelo (t_base) montan encima de ella, o sea con su centro
    // en t_base + r, y a esa altura el redondeo de las esquinas de abajo deja de
    // afectarles -- ahi ya hay acrilico de sobra.
    //   - Frente: lo que manda ahora es el riel de panel, que le pasa por
    //     delante. Misma cuenta que x_ed: se separa de la ESQUINA del riel
    //     girado, no de su centro. Antes iba en alto_frontal/2 + r + 2, pegado
    //     al vertice, y ahi el riel se le montaba encima.
    //   - Fondo: comparte X con el de arriba (x_tr). Estuvo en
    //     fondo - r - radio_perfil, 14 mm mas adelante que ellos, con la nota
    //     de que "adelantarlo solo compra fondo de bandeja y no hace falta".
    //     Si hacia falta: la trasera apoya en EL y en el de arriba, y con
    //     14 mm de diferencia una de sus dos filas se atornillaba al aire.
    //     Lo canta apoyo() en clearance_budget. Cabe: a y=8 la curva del canto
    //     trasero esta en x=289.87 y la esquina del riel movido en 286.22.
    [[cr[0].x + he_er_x(angulo_inferior) + holgura_rail + r, t_base + r],
     [x_tr,          t_base + r],               // base trasera
     [x_ed,                y_ep],                     // entrepiso delantero
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
function radios_perfil() = [radio_punta,  radio_punta,
                            radio_pico,   radio_valle,
                            radio_remate, radio_remate,
                            radio_perfil];

// Va DENTRO de perfil_lateral y no en costado_2d a proposito: costado_2d
// resta los agujeros DESPUES, de modo que el redondeo no toca los taladros.
// Si se aplicara al resultado de la resta, los M4 saldrian fuera de
// diametro -- el mismo tipo de fallo que el cupon pentagonal.
//
// Ningun otro modulo consume este contorno (las demas piezas usan
// pts_perfil() para coordenadas, no la silueta), asi que el radio no se
// propaga a bandejas ni pieles.
module perfil_lateral() {
    // El tramo que SALE de P[6] es el canto de abajo (P[6] -> P[0]) y va
    // recto de verdad: es la cara de apoyo del case. Abombada, el aparato
    // descansaria sobre el centro de cada costado en vez de sobre sus
    // extremos, y con paticas en las esquinas eso es un balancin.
    polygon(redondear(pts_perfil(), radios_perfil(), [6]));
}

module costado_2d() {
    cr = centros_rail();
    difference() {
        perfil_lateral();
        // DOS DIAMETROS, no uno. El costado los mezcla porque los dos
        // herrajes que atraviesa son distintos:
        //   - los cuatro railes EUROrack traen el taladro de punta ROSCADO M4
        //     de fabrica (hoja Tiptop), asi que aqui va agujero de PASO M4 y el
        //     tornillo muerde el aluminio. Sin tuerca, sin inserto.
        //   - los siete largueros 2020 se atornillan con M5 a tuerca T.
        // Estuvieron todos a M5 mientras la seccion se creia la de StudioRacks.
        for (c = cr) translate(c) circle(d = d_M4_paso + kerf);
        for (c = centros_esqueleto()) translate(c) circle(d = d_M5_paso + kerf);
    }
}

module costado() { linear_extrude(t_cheek) costado_2d(); }

module rail_2020(largo) { cube([rail, largo, rail], center = true); }

// Riel EUROrack. Los ejes locales no son intercambiables como en el 2020: tras
// el rotate([0,0,-a]) rotate([90,0,0]) de rails(), la X local acaba sobre la
// NORMAL INTERIOR de la cara (o sea el fondo del riel) y la Z local sobre la
// direccion de la cara (su alto). Verificado con las dos matrices a mano.
module rail_er(largo) { cube([rail_er_fondo, largo, rail_er_alto], center = true); }

// --- planchas rectangulares del cuerpo (todas t_acrilico) -------------
// Agujeros M3 de tuerca T contra los largueros 2020, repartidos a ~paso.
//
// IBA DESCENTRADA y nadie la miraba: arrancaba en paso/2 y avanzaba de paso en
// paso hasta donde llegara, o sea que sobre 528.32 dejaba 50.00 de orilla a la
// izquierda y 78.32 a la derecha. 28 mm de diferencia en la pieza que carga el
// transformador. El paso ahora se estira para caber un numero entero de veces,
// que es lo que el codigo viejo QUERIA decir con ese paso/2 de arranque:
// orillas iguales y valiendo medio paso.
module fila_agujeros(largo, y, paso = 100, d = d_M3_paso) {
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
    au = ancho_total - 2*t_cheek;
    ce = centros_esqueleto();
    // Canto delantero A RAS del larguero de base delantera, que a su vez esta
    // derivado de la esquina del riel de panel. Esa es justo la cota que hace
    // corto al case: la bandeja se RETIRA por detras del riel en vez de pasarle
    // por debajo, y a cambio el riel baja hasta la esquina (ver alto_frontal).
    // El precio son 32 mm de suelo abierto por delante, que es por donde entra
    // el aire.
    x0 = ce[0].x - rail/2;
    fondo = ce[1].x + rail/2 - x0;          // canto trasero a ras del rail
    difference() {
        plancha(au, fondo);
        fila_agujeros(au, ce[0].x - x0);    // los dos largueros van ENCIMA
        fila_agujeros(au, ce[1].x - x0);
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
module piel_trasera_2d() {
    au = ancho_total - 2*t_cheek - 2*hol_piel;
    ce = centros_esqueleto();
    P  = pts_perfil();
    // UNA sola plancha desde el 2026-08-21: fueron dos (piel_inferior y
    // piel_superior) partidas a la altura del entrepiso, porque cada una se
    // atornillaba a los dos largueros de SU piso. Muerta la bandeja de
    // entrepiso esa frontera dejo de existir. Va en t_piel (8), no en
    // t_acrilico.
    y0   = ce[1].y - 15;                    // canto de abajo
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
    f_base = ce[1].y - y0;
    f_tras = ce[4].y - y0;
    // Las ondas conservan su altura fisica de siempre, pero derivadas de las
    // dos filas que las rodean: asi no se acercan a un tornillo si un larguero
    // se mueve. Las fracciones se recalcularon al pasar de cinco filas a dos
    // para dejar las ondas DONDE YA ESTABAN: 82.75 y 171.68 contra 83.33 y
    // 171.39 de antes, o sea medio milimetro.
    y_bajas  = f_base + 0.32*(f_tras - f_base);
    y_sierra = f_base + 0.74*(f_tras - f_base);
    difference() {
        plancha(au, alto);
        for (y = [f_base, f_tras]) fila_agujeros(au, y);
        translate([au*0.10, y_bajas])  onda("triangulo", au*0.35);
        translate([au*0.55, y_bajas])  onda("cuadrada",  au*0.35);
        translate([au*0.15, y_sierra]) onda("sierra", au*0.70);
        // recorte IEC C14 con interruptor (bloque snap-in tipico
        // 48 x 27.5; CONFIRMAR contra el datasheet de la pieza comprada).
        // +kerf como todo hueco interior del fichero.
        translate([au - 70, 22]) square([48 + kerf, 27.5 + kerf]);
    }
}

// --- tapa del valle ----------------------------------------------------
// Ranura de extremos redondos. Redondos y no cuadrados por lo de siempre en
// acrilico: una esquina viva dentro de un hueco es donde arranca la fisura.
module ranura(largo, ancho) {
    hull() for (s = [-1, 1])
        translate([0, s*(largo - ancho)/2]) circle(d = ancho + kerf);
}

// La plancha del valle. Ver la nota de params.scad: campo de ranuras registrado
// a la malla HP, partido por la espina maciza donde va la fila de M3.
module tapa_valle_2d() {
    au = ancho_total - 2*t_cheek;
    ce = centros_esqueleto();
    xv = x_valle();
    largo = xv[1] - xv[0];
    y_esp = ce[3].x - xv[0];                 // linea del larguero, en local
    campos = [[valle_margen,               y_esp - valle_espina/2],
              [y_esp + valle_espina/2,     largo - valle_margen]];
    n_hp  = round(largo_riel/hp);            // 104
    difference() {
        plancha(au, largo);
        fila_agujeros(au, y_esp);
        for (c = campos)
            for (n = [valle_paso_hp : valle_paso_hp : n_hp - valle_paso_hp])
                translate([n*hp, (c[0] + c[1])/2])
                    ranura(c[1] - c[0], vent_ancho_ranura);
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
function bandeja_base_fondo() =
    let (ce = centros_esqueleto()) ce[1].x + rail/2 - (ce[0].x - rail/2);
function ch_pos() = [ancho_total - 2*t_cheek - chasis_margen_bandeja
                       - ch_tapa_ext().x,
                     (bandeja_base_fondo() - ch_tapa_ext().y)/2];

// Esquina de la salida de cables del chasis, en coordenadas locales de
// bandeja_base_2d(). Una sola definicion: la consume el agujero del acrilico
// y la comprueba el budget.
function salida_cables_xy() =
    let (pc = ch_pos(), d = ch_desfase() + t_chapa)
    [pc.x + d + chasis_salida_x - salida_holgura,
     pc.y + d + chasis_salida_y - salida_holgura];

module chasis() {
    ce = centros_esqueleto();
    p  = ch_pos();
    multmatrix([[0, 1, 0, ce[0].x - rail/2 + p.y],
                [0, 0, 1, t_base + chasis_pie],
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
else if (PART == "assembly")           assembly();
else if (PART == "assembly_acrilico")  assembly_acrilico();
else if (PART == "assembly_aluminio")  assembly_aluminio();
else if (PART == "bandeja_base_2d")      bandeja_base_2d();
else if (PART == "tapa_valle_2d")        tapa_valle_2d();
else if (PART == "remate_sup_2d")        remate_sup_2d();
else if (PART == "piel_trasera_2d")      piel_trasera_2d();
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
// Dos costados en los extremos de Z; 9 largueros 2020 (centros_rail() +
// centros_esqueleto(), en ese orden — 5 de esqueleto desde que los tres
// traseros de en medio se retiraron) cruzando entre sus caras internas.
module costados() {
    costado();
    translate([0, 0, ancho_total - t_cheek]) costado();
}

// railes de panel (centros_rail(), 4) van a ras de su cara: giro extra
// sobre el propio eje largo (R3, ronda de revision) para que la cara del
// rail quede paralela al panel en vez de un canto en diagonal. Centros
// intactos (agujeros M5 del costado y todos los DXF, sin cambios).
// rotate([0,0,-angulo]) alinea el lado +Y local del rail con el vector de
// cara d=(sin,cos) — verificado con la matriz Rz(-angulo) a mano.
module rails() {
    cr = centros_rail();   // [inf frente, inf valle, sup valle, sup remate]
    angs = [angulo_inferior, angulo_inferior,
            angulo_superior, angulo_superior];
    for (i = [0 : len(cr) - 1])
        translate([cr[i].x, cr[i].y, ancho_total/2])
            rotate([0, 0, -angs[i]])
                rotate([90, 0, 0])
                    rail_er(ancho_util);
    for (c = centros_esqueleto())
        translate([c.x, c.y, ancho_total/2])
            rotate([90, 0, 0])
                rail_2020(ancho_util);
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
    // Ya no apoya en el lomo de nadie: ES el canto de abajo del case, de y = 0 a
    // y = t_base, y los largueros montan sobre ella. El grosor crece hacia -Y
    // desde el origen, asi que el origen va en t_base.
    ce = centros_esqueleto();
    translate([ce[0].x - rail/2, t_base, ancho_total - t_cheek])
        rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(t_base) bandeja_base_2d();
}

// tope de bandeja a ras de P3.y (canto SUPERIOR, no inferior — ver
// centros_esqueleto()); canto delantero a ras del rail reubicado.

// EMPOTRADA (2026-08-21): cara exterior EN el plano trasero, x = fondo(), y
// crece hacia dentro. Estuvo volada sobre separadores, con la cara exterior 10
// mm por detras del canto. Apoya en la cara de los DOS largueros traseros, que
// por eso viven los dos en x_tr = fondo - r - t_piel. y0 deriva de la fila de
// agujero inferior cayendo en el rail base-trasera (ce[1].y).
module piel_trasera() {
    P = pts_perfil();
    ce = centros_esqueleto();
    translate([P[6].x, ce[1].y - 15, t_cheek + hol_piel])
        rotate([0, -90, 0])
            linear_extrude(t_piel) piel_trasera_2d();
}

// A ras del plano del valle, igual que la bandeja de entrepiso: el grosor crece
// hacia -Y desde el origen, asi que el origen va en P[3].y.
module tapa_valle() {
    P = pts_perfil();
    xv = x_valle();
    translate([xv[0], P[3].y, ancho_total - t_cheek])
        rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(t_acrilico) tapa_valle_2d();
}

module planchas_acrilico() {
    bandeja_base();
    tapa_valle();
    piel_trasera();
    remate_sup();
}

// panel de modulo (PCB de aluminio, t_panel) sobre una cara del perfil
// A->B: cara externa a ras del perfil, engrosa hacia dentro segun la
// misma normal que centros_rail() ([d.y,-d.x]). s0 = donde ARRANCA el panel
// sobre la cara; el panel ya no tiene por que cubrirla entera.
module panel_cara(A, B, s0, largo) {
    d = (B - A) / norm(B - A);
    translate([A.x, A.y, t_cheek])
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
    translate([P[4].x + inset_remate_frente, P[5].y - marco_sup, t_cheek])
        cube([prof_sup, marco_sup, ancho_util]);
}

// La pestana vista de canto: 528.32 x prof_sup en plancha de marco_sup.
// SIN TALADROS. Llevo cinco M3 mientras el plan era atornillarla al riel; la
// hoja de datos del Z-Rail enseno que esa cara es pared de 1.2 mm, asi que la
// union pasa a ser junta pegada y esos cinco agujeros dejaron de servir a
// nadie. Fresando eso no es cosmetico: son cinco prestaciones que se pagan.
// Si el calibrador encuentra material, volver a meterlos es una linea.
module remate_sup_2d() {
    au = ancho_total - 2*t_cheek;
    P = pts_perfil();
    ce = centros_esqueleto();
    difference() {
        plancha(au, prof_sup);
        // la fila cae en la centerline del larguero nuevo, medida desde el
        // canto DELANTERO de la plancha (el que remata el canto del panel).
        fila_agujeros(au, ce[4].x - P[4].x - inset_remate_frente);
    }
}

// Paticas torneadas bajo los costados. En X caen sobre los dos rieles de
// base, que es donde esta la estructura; en Z su cara exterior queda a ras
// del canto del case (centro a d_pie/2) para que la carga del costado baje
// recta al pie y no de canto.
module paticas() {
    ce = centros_esqueleto();
    // El pie delantero ya no cae sobre un larguero: la base delantera se retiro
    // 39 mm hacia dentro para librar el riel del panel, y un pie ahi dejaria todo
    // el frente en voladizo justo donde se aprietan los mandos de abajo. Va donde
    // acaba el redondeo de la punta, que es lo mas adelante que se puede apoyar
    // con el disco entero sobre acrilico. El trasero sigue sobre su larguero.
    for (x = [alto_frontal/2 + d_pie/2, ce[1].x])
        for (z = [d_pie/2, ancho_total - d_pie/2])
            translate([x, 0, z])
                rotate([90, 0, 0])
                    cylinder(h = alto_pie, d = d_pie);
}

module assembly() {
    costados();
    rails();
    planchas_acrilico();
    chasis();
    paticas();
    %paneles();                        // paneles de modulo: solo referencia
}

module assembly_acrilico() {           // STL separado para Blender (Task 8)
    costados();
    planchas_acrilico();
}

// OJO CON EL WARNING de 2-manifold que suelta este export: es INHERENTE y no un
// defecto que arreglar. Aqui hay cuerpos que se tocan A PROPOSITO -- el dorso
// del panel apoya EXACTAMENTE en la cara del riel (esa distancia ES t_panel) y
// roza tangente el nudillo de la bisagra --, y una union de solidos que comparten
// cara no es un 2-manifold limpio. Que salga o no salga el aviso depende de por
// que lado caiga el redondeo de coma flotante, asi que aparece y desaparece al
// mover el case (aparecio al bajar el suelo 17 mm, 2026-08-17). No afecta a
// ningun DXF -- esto es el STL de referencia para Blender, y Blender lo carga.
module assembly_aluminio() {           // idem, perfiles 2020 + paneles solidos
    rails();
    paneles();
}

// --- lienzo de corte: 7 piezas (2 costados + 5 planchas) en rejilla -----
// Separacion 8 mm; marco de 1000x600 es solo referencia visual de plancha,
// las piezas pueden desbordarlo (nesting real lo hace el servicio de corte).
module lienzo_2d() {
    sep = 8;
    P = pts_perfil();
    prof = max([for (pp = P) pp.x]);   // ancho real de costado_2d (fondo)
    alto = max([for (pp = P) pp.y]);   // alto real de costado_2d
    au  = ancho_total - 2*t_cheek;
    aup = ancho_total - 2*t_cheek - 2*hol_piel;
    // fila 1: los 2 costados
    costado_2d();
    translate([prof + sep, 0]) costado_2d();
    // fila 2: las 4 planchas del cuerpo. Fueron 6 hasta el 2026-08-21 (murio la
    // bandeja de entrepiso y las dos pieles se fundieron en una).
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
    x3 = x2 + aup + sep;  translate([x3, y2]) tapa_valle_2d();
    x4 = x3 + au + sep;   translate([x4, y2]) remate_sup_2d();
    %square([1000, 600]);
}

module bom() {
    au = ancho_total - 2*t_cheek;
    echo(str("BOM: larguero 2020 x", len(centros_esqueleto()), " de ", au, " mm"));
    echo(str("BOM: Z-Rail de Tiptop x", len(centros_rail()), ", largo ", largo_riel,
             " (104 HP) -- seccion ", rail_er_fondo, " x ", rail_er_alto,
             ", hoja de datos oficial. NO es el riel de StudioRacks: ese media",
             " 27.4 de fondo y el case estuvo dibujado contra el hasta el",
             " 2026-08-17."));
    echo(str("BOM: tornillo M4 x8 para los rieles -- entran de punta por el ",
             "costado y ROSCAN EN EL PROPIO RIEL (viene con M4 taladrado a 3.3 ",
             "de fabrica). Sin tuerca, sin inserto. Largo = ", t_cheek,
             " de costado + arandela + 8..10 de rosca dentro del aluminio."));
    echo(str("BOM: tornillo M5 boton x", 2*len(centros_esqueleto()),
             " + tuerca T -- por la PUNTA de los largueros 2020, desde el costado"));
    // Faltaban. Los M5 de arriba atan el larguero al COSTADO; estos atan la
    // PLANCHA al larguero, que es otra union y otro herraje. Salieron al montar
    // la guia de ensamblaje: las planchas tenian los taladros dibujados y el BOM
    // no tenia el tornillo.
    n_fila = max(1, round(au/100));
    // SEIS filas de n_fila: dos de la bandeja de base, una de la tapa del
    // valle, una de la tapa de remate y DOS de la trasera -- una por larguero
    // trasero. Fueron nueve hasta el 2026-08-21, con cinco en la trasera; se
    // fueron con los tres largueros traseros de en medio.
    echo(str("BOM: tornillo M3 x", 6*n_fila, " + tuerca T M3 -- las planchas a",
             " los largueros: base ", 2*n_fila,
             ", tapa del valle ", n_fila, ", tapa de remate ", n_fila,
             ", trasera ", 2*n_fila, "."));
    echo("     Estos entran por la RANURA del 2020, no por su punta. Es donde");
    echo("     la tuerca de insercion lateral se paga sola: con las de deslizar");
    echo("     hay que dejarlas dentro ANTES de cerrar el esqueleto.");
    echo(str("BOM: la TRASERA es UNA plancha empotrada de t=", t_piel, ", no dos:"));
    echo(str("     ", ancho_total - 2*t_cheek - 2*hol_piel, " de ancho,",
             " atornillada arriba y abajo y NADA en medio: 211.73 mm de vano"));
    echo("     libre, que en 8 mm de acrilico son 0.15 de flecha con 50 N en el");
    echo("     centro. Fueron dos pieles de 5 partidas a la altura del");
    echo("     entrepiso, colgadas de 12 separadores M4 y con cinco filas de");
    echo("     tornillo. Separadores, junta de sombra, una plancha entera y");
    echo("     tres largueros murieron por el camino, todos el 2026-08-21.");
    // LAS DOS FILAS SON TAPA. Cada una gira sobre el M5 de su riel de arriba y
    // se cierra con el de su otro extremo. De los 48 tornillos del case (8 M4 de
    // riel + 10 M5 de larguero + 30 M3 de plancha; los 24 M4 de separador se
    // fueron con los separadores), solo CUATRO se tocan para abrirlo: dos por
    // fila.
    echo("BOM: los M4 de riel no son todos iguales --");
    echo("     x4 EJES: tornillo de HOMBRO M4, espiga 4 mm (no M5 -- el riel");
    echo("        cambio de herraje al cambiar de fabricante). Riel del valle");
    echo("        de la fila de abajo, riel del vertice de la de arriba.");
    echo("        Pila: Belleville + ARANDELA ANCHA d16. Ver la nota de abajo.");
    echo("     x4 CIERRES: M4 de cabeza moleteada o palomilla -- se quitan a");
    echo("        mano y son los unicos que se tocan para abrir el case.");
    echo("        Riel del frente abajo, riel del valle arriba.");
    echo(str("     x", 2*len(centros_esqueleto()), " fijos: los largueros de esqueleto"));
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
    echo(str("BOM: patica metalica torneada x4, d=", d_pie, " x ", alto_pie, " mm"));
    echo(str("BOM: plancha t=", t_acrilico, ": SOLO la tapa del valle -- ojo, un",
             " espesor entero para UNA pieza, cosa del pliego"));
    echo(str("BOM: plancha t=", t_cheek, ": costados x2, suelo (bandeja de base,",
             " portante), tapa de remate y TRASERA -- 5 piezas"));
}
