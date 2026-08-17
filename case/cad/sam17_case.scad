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
// El radio de giro del propio riel sale de su seccion: la esquina mas lejana de
// su centroide esta a hypot(rail_er_fondo, rail_er_alto)/2 = 14.58 mm, y eso es
// lo que tiene que librar el larguero de remate (ver y_rs).
function radio_giro_riel() = norm([rail_er_fondo, rail_er_alto])/2;

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
// base delantera, base trasera, entrepiso delantero, entrepiso trasero,
// remate superior, repisa. Centros [x, y]:
//
// entrepiso delantero reubicado (fix de solape, ronda de revision 1): el
// original P[3].x+r invadia el rail de panel de la cara superior
// (17.6x12.6 mm de solape, verificado). Ahora se apoya holgura_rail detras
// del borde trasero de ESE rail. Y de ambos railes de entrepiso baja a
// P3.y-t_acrilico-r para que la bandeja apoye con el CANTO SUPERIOR a ras
// de P3.y (antes apoyaba con el canto inferior ahi, dejando la tapa 5 mm
// por encima del plano de entrepiso).
//
// repisa (sexto larguero, ronda de revision 2 — R6): ancla piel_superior
// SIN pasar por el rail entrepiso-trasero. Nacio cuando habia DOS planos
// traseros (piso inferior en X=350, superior en X=250) y anclar la piel
// superior al rail de entrepiso invadia la bandeja. Con el fondo unico del
// triangulo los dos planos son el mismo, pero la repisa sigue siendo
// necesaria: separa en ALTURA las dos pieles, que ahora comparten plano y se
// apilan en Y. Centro a P3.y+15: canto inferior del rail en P3.y+5 (5 mm
// por encima del tope de la bandeja, sin tocarla) y la fila de agujero
// inferior de piel_superior (inset 15) cae justo en P3.y, a ras del tope
// de la bandeja.
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
         // semiextension en X del RIEL EUROrack de la cara superior tras su
         // rotacion (ver he_er_x). El larguero que se planta detras de el se
         // separa de esa esquina, no de su centro.
         he_cs = r * (cos(angulo_superior) + sin(angulo_superior)),
         x_ed = cr[2].x + he_er_x(angulo_superior) + holgura_rail + r,
         y_ep = P[3].y - t_acrilico - r,
         // Remate superior. Su Y NO puede ser P[5].y - r: al acortar el marco
         // de arriba para que la esquina se lea como PUNTA, el rincon se
         // cierra y ahi ya no cabe. Tres techos, y manda el mas bajo:
         //   1. el TECHO YA REDONDEADO. La esquina trasera de arriba lleva
         //      tangente marco_remate/2, y como este larguero vive pegado al
         //      plano trasero (x = fondo - r), su esquina de atras cae justo
         //      donde el arco ya bajo esa tangente. P[5].y - r a secas lo
         //      dejaba FUERA del acrilico.
         //   2. el plano del panel de arriba, a distancia PERPENDICULAR con la
         //      normal interior (cos, -sen). La cota es he_cs + t_panel y NO
         //      r + t_panel: lo que se acerca al panel es la ESQUINA del
         //      larguero, no su centro, y en diagonal alcanza he_cs = 14.14 en
         //      vez de 10. Con el marco en 22 este techo nunca mandaba y el
         //      error dormia; con el marco en 8 manda, y con la version vieja
         //      la esquina asomaba 2.54 mm por delante del panel.
         //   3. el RIEL DE ARRIBA DE LA TAPA, que es el que de verdad manda.
         //      Y no basta con su esquina de abajo: ese riel GIRA sobre su
         //      propio M5, asi que lo que hay que librar es su BARRIDO -- el
         //      circulo de radio_giro_riel() alrededor de su centroide. Con
         //      he_er_y(45) = 13.22 en vez de 14.58 el larguero se quedaba
         //      1.36 mm corto y solo se enteraba uno abriendo la tapa.
         y_rs = min(P[5].y - r - marco_remate/2,
                    P[3].y + (cos(angulo_superior)*(fondo() - r - P[3].x)
                              - (he_cs + t_panel)) / sin(angulo_superior),
                    cr[3].y - radio_giro_riel() - holgura_rail - r))
    // Los dos largueros de la base ya NO viven en el canto de abajo. Desde que
    // la bandeja es el suelo (t_base) montan encima de ella, o sea con su centro
    // en t_base + r, y a esa altura el redondeo de las esquinas de abajo deja de
    // afectarles -- ahi ya hay acrilico de sobra.
    //   - Frente: lo que manda ahora es el riel de panel, que le pasa por
    //     delante. Misma cuenta que x_ed: se separa de la ESQUINA del riel
    //     girado, no de su centro. Antes iba en alto_frontal/2 + r + 2, pegado
    //     al vertice, y ahi el riel se le montaba encima.
    //   - Fondo: se queda en fondo - r - radio_perfil. A y = 18 la curva trasera
    //     ya no llega y sobra sitio, pero adelantarlo solo compra fondo de
    //     bandeja y no hace falta.
    [[cr[0].x + he_er_x(angulo_inferior) + holgura_rail + r, t_base + r],
     [fondo() - r - radio_perfil, t_base + r],  // base trasera
     [x_ed,                y_ep],                     // entrepiso delantero
     [fondo() - r,   y_ep],                     // entrepiso trasero
     [fondo() - r,   y_rs],                     // remate superior
     [fondo() - r,   P[3].y + 15],              // repisa (R6)
     // valle: el septimo, y el unico que existe por una plancha y no por una
     // union. Va CENTRADO bajo la tapa del valle para que los dos vuelos sean
     // iguales; a la vez ata los dos costados por la cintura, que es donde el
     // perfil es mas estrecho. Su ventana es corta -- entre las esquinas
     // giradas de los dos railes del valle -- y clearance_budget la vigila.
     [(x_valle()[0] + x_valle()[1])/2, y_ep]];

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
//   4 apex          PUNTA    5 fondo-arriba   PUNTA
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
function radios_perfil() = [radio_punta, radio_punta,
                            radio_pico,  radio_valle,
                            radio_punta, radio_punta,
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
        // Los cuatro railes de panel llevan su M5 de punta al costado; lo que
        // cambia es el papel de cada uno (ver la nota de centros_rail).
        for (c = concat(cr, centros_esqueleto()))
            translate(c) circle(d = d_M5_paso + kerf);
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
        // ventilacion bajo el PSU (tercio derecho): onda cuadrada
        translate([au*0.68, fondo*0.35])
            onda("cuadrada", au*0.25);
    }
}

module bandeja_entrepiso_2d() {
    au = ancho_total - 2*t_cheek;
    ce = centros_esqueleto();
    largo = fondo() - ce[2].x + rail/2;  // canto delantero a ras del rail reubicado
    difference() {
        plancha(au, largo);
        fila_agujeros(au, rail/2);
        fila_agujeros(au, largo - rail/2);
        // pasacables entre pisos: 3 oblongos de 40 x 12
        for (x = [au*0.2, au*0.5, au*0.8])
            translate([x, largo/2]) hull()
                for (dx = [-14, 14]) translate([dx, 0]) circle(d = 12 + kerf);
    }
}

// TRES columnas de standoff, no dos. Con solo las cuatro esquinas el vano es
// de 518 mm y la plancha se descuelga 1.76 mm por su PROPIO PESO, sin que nadie
// la toque -- calculado con acrilico colado a 3 GPa. Partiendo el vano por la
// mitad cae a 0.11 (la flecha va con L^4, asi que partir en dos divide por 16).
// Cuatro tornillos mas en todo el case para que la cara trasera no ondee.
module piel_inferior_2d() {
    au = ancho_total - 2*t_cheek - 2*gap_sombra;
    ce = centros_esqueleto();
    alto = ce[3].y - ce[1].y + 30;   // entrepiso trasero <-> base trasera
    difference() {
        plancha(au, alto);
        for (x = [15, au/2, au-15]) for (y = [15, alto-15])
            translate([x, y]) circle(d = d_M4_paso + kerf);
        translate([au*0.10, alto*0.62]) onda("triangulo", au*0.35);
        translate([au*0.55, alto*0.62]) onda("cuadrada",  au*0.35);
        // recorte IEC C14 con interruptor (bloque snap-in tipico
        // 48 x 27.5; CONFIRMAR contra el datasheet de la pieza comprada).
        // +kerf como todo hueco interior del fichero (ruling T4: la
        // geometria laser no lleva convencion mixta) — era el unico que
        // faltaba, y en un recorte de encaje a presion el que mas duele.
        translate([au - 70, 22]) square([48 + kerf, 27.5 + kerf]);
    }
}

// re-anclada a la repisa (R6, ronda de revision 2) en vez de entrepiso
// trasero: ese rail vive en el plano del piso inferior (X=340), invadia
// la bandeja de entrepiso 5x5x474 mm. La repisa vive en el plano del
// piso superior, 5 mm por encima del tope de la bandeja.
module piel_superior_2d() {
    au = ancho_total - 2*t_cheek - 2*gap_sombra;
    ce = centros_esqueleto();
    alto = ce[4].y - ce[5].y + 30;   // remate superior <-> repisa
    difference() {
        plancha(au, alto);
        for (x = [15, au/2, au-15]) for (y = [15, alto-15])
            translate([x, y]) circle(d = d_M4_paso + kerf);
        translate([au*0.15, alto*0.45]) onda("sierra", au*0.70);
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
    y_esp = ce[6].x - xv[0];                 // linea del larguero, en local
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

if (PART == "costado")             costado();
else if (PART == "costado_2d")     costado_2d();
else if (PART == "assembly")           assembly();
else if (PART == "assembly_acrilico")  assembly_acrilico();
else if (PART == "assembly_aluminio")  assembly_aluminio();
else if (PART == "bandeja_base_2d")      bandeja_base_2d();
else if (PART == "bandeja_entrepiso_2d") bandeja_entrepiso_2d();
else if (PART == "tapa_valle_2d")        tapa_valle_2d();
else if (PART == "remate_sup_2d")        remate_sup_2d();
else if (PART == "piel_inferior_2d")     piel_inferior_2d();
else if (PART == "piel_superior_2d")     piel_superior_2d();
else if (PART == "lienzo_2d")            lienzo_2d();
else if (PART == "bom")                  bom();
else assert(false, str("PART desconocido: ", PART));

// costado_2d vive en el plano XY del perfil (X = fondo, Y = altura);
// costado() lo extruye en +Z por t_cheek, o sea Z pasa a ser el ancho.
// Dos costados en los extremos de Z; 11 largueros 2020 (centros_rail() +
// centros_esqueleto(), en ese orden — 7 de esqueleto desde el rail nuevo
// del zocalo) cruzando entre sus caras internas.
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
module bandeja_entrepiso() {
    ce = centros_esqueleto();
    P = pts_perfil();
    translate([ce[2].x - rail/2, P[3].y, ancho_total - t_cheek])
        rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(t_acrilico) bandeja_entrepiso_2d();
}

// volado: cara interior a X = fondo() + gap_sombra (fuera del
// cuerpo, no ya recortado hacia dentro), engrosa hacia +X. y0 deriva de
// la fila de agujero inferior cayendo en el rail base-trasera (ce[1].y).
module piel_inferior() {
    P = pts_perfil();
    ce = centros_esqueleto();
    translate([P[6].x + gap_sombra + t_acrilico, ce[1].y - 15, t_cheek + gap_sombra])
        rotate([0, -90, 0])
            linear_extrude(t_acrilico) piel_inferior_2d();
}

// volado: cara interior a X = prof_superior + gap_sombra. y0 deriva de la
// fila de agujero inferior cayendo en la repisa (ce[5].y) — R6, ronda de
// revision 2. Con esto el canto inferior de la plancha cae exacto en
// P3.y (tope de bandeja_entrepiso): a ras, cero solape.
module piel_superior() {
    P = pts_perfil();
    ce = centros_esqueleto();
    translate([P[6].x + gap_sombra + t_acrilico, ce[5].y - 15, t_cheek + gap_sombra])
        rotate([0, -90, 0])
            linear_extrude(t_acrilico) piel_superior_2d();
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
    bandeja_entrepiso();
    tapa_valle();
    piel_inferior();
    piel_superior();
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
    d = (P[4] - P[3]) / norm(P[4] - P[3]);
    translate([P[3].x, P[3].y, t_cheek])
        rotate([0, 0, atan2(d.y, d.x)])
            translate([alto_cara_sup - marco_sup, -prof_sup, 0])
                cube([marco_sup, prof_sup, ancho_util]);
}

// La pestana vista de canto: 528.32 x prof_sup en plancha de marco_sup. Los M3
// atraviesan el ESPESOR, o sea que salen por la cara que apoya en el riel.
module remate_sup_2d() {
    au = ancho_total - 2*t_cheek;
    difference() {
        plancha(au, prof_sup);
        fila_agujeros(au, prof_sup/2);
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
    aup = ancho_total - 2*t_cheek - 2*gap_sombra;
    // fila 1: los 2 costados
    costado_2d();
    translate([prof + sep, 0]) costado_2d();
    // fila 2: las 4 planchas del cuerpo (eran 5 con el zocalo)
    y2 = alto + sep;
    x1 = 0;              translate([x1, y2]) bandeja_base_2d();
    x2 = x1 + au + sep;  translate([x2, y2]) bandeja_entrepiso_2d();
    x3 = x2 + au + sep;  translate([x3, y2]) piel_inferior_2d();
    x4 = x3 + aup + sep; translate([x4, y2]) piel_superior_2d();
    x5 = x4 + aup + sep; translate([x5, y2]) tapa_valle_2d();
    x6 = x5 + au + sep;  translate([x6, y2]) remate_sup_2d();
    %square([1000, 600]);
}

module bom() {
    au = ancho_total - 2*t_cheek;
    echo(str("BOM: larguero 2020 x", len(centros_esqueleto()), " de ", au, " mm"));
    echo(str("BOM: riel EUROrack x", len(centros_rail()), " de ", au, " mm (",
             rail_er_fondo, " x ", rail_er_alto, ") -- 2 al case, fijados de ",
             "punta con M5 al costado; 2 A LA TAPA, que gira y no lleva M5"));
    echo(str("BOM: tornillo M5 boton x", 2*(len(centros_rail()) + len(centros_esqueleto())),
             " -- OJO: la longitud del que entra al riel esta SIN CERRAR, John dijo",
             " que el M5x35 de catalogo no sirve para costado de ", t_cheek, " mm"));
    echo("BOM: standoff M4 x12 (las dos pieles, voladas; TRES columnas -- con");
    echo("     dos, el vano de 518 mm se descuelga 1.76 mm de peso propio)");
    echo("BOM: tornillo M4 boton x24 + arandela x24");
    // LAS DOS FILAS SON TAPA. Cada una gira sobre el M5 de su riel de arriba y
    // se cierra con el de su otro extremo. De los 64 tornillos del case, solo
    // CUATRO se tocan para abrirlo: dos por fila.
    echo("BOM: los M5 de riel no son todos iguales --");
    echo("     x4 DE HOMBRO + arandela: los EJES (riel del valle de la fila de");
    echo("        abajo, riel del vertice de la de arriba). No se aprietan.");
    echo("     x4 DE MANO: los CIERRES (riel del frente abajo, riel del valle");
    echo("        arriba). Son los unicos que se quitan para abrir el case.");
    echo(str("     x", 2*len(centros_esqueleto()), " fijos: los largueros de esqueleto"));
    echo("BOM: tuercas T DE INSERCION LATERAL (drop-in), NO de deslizar. Con las");
    echo("     de deslizar hay que enhebrarlas por la punta del larguero antes de");
    echo("     montar, o sea que anadir un tornillo mas tarde obliga a desarmar.");
    echo("BOM: paneles ciegos en TODO hueco de LAS DOS filas -- no son estetica:");
    echo("     con la tapa abierta son lo unico que ata sus dos rieles entre si");
    echo("BOM: SIN CERRAR -- amortiguador que deje cada tapa abierta");
    echo(str("BOM: pestana superior x1, ", au, " x ", prof_sup, " en acrilico ",
             "t=", marco_sup, " -- apoya de canto en la cara de arriba del riel"));
    echo("BOM: tornillo M3 x5 para la pestana, entran por su canto al riel.");
    echo("     CONFIRMAR con el riel en mano que esa cara admite rosca M3;");
    echo("     si no, el mismo apoyo a tope pegado sobra para 60 g de acrilico");
    echo(str("BOM: patica metalica torneada x4, d=", d_pie, " x ", alto_pie, " mm"));
    echo(str("BOM: planchas t=", t_acrilico, ": entrepiso, tapa del valle, ",
             "piel inf, piel sup; suelo t=", t_base, " (la bandeja de base, ",
             "ahora portante); costados t=", t_cheek, " x2"));
}
